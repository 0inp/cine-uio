from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import (
    MAX_TMDB_ATTEMPTS,
    configure_sqlite,
    delete_all_screenings,
    enrich_movies_with_tmdb,
    get_all_cinema_companies,
    get_all_cinema_complexes_from_cinema_company,
    get_all_screenings,
    save_screenings,
)
from app.entities import CinemaCompany, CinemaComplex, Movie, Screening
from app.models import Movie as MovieModel
from app.tmdb import TMDBMovie


def _make_screening(
    title: str,
    complex_name: str,
    company_name: str,
    fmt: str = "2D",
    language: str = "Doblada",
    dt: datetime | None = None,
) -> Screening:
    company = CinemaCompany(name=company_name, base_url="https://example.com")
    return Screening(
        datetime=dt or datetime(2026, 6, 25, 14, 30),
        format=fmt,
        language=language,
        complex=CinemaComplex(name=complex_name, url_part="/", company=company),
        movie=Movie(title=title),
    )


class TestSaveScreenings:
    def test_creates_movie_and_screening(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Inception", "CCI", "Multicines")])
        results = get_all_screenings(bare_db)
        assert len(results) == 1
        assert results[0].movie.title == "Inception"

    def test_reuses_existing_movie_across_screenings(self, bare_db: Session) -> None:
        screenings = [
            _make_screening("Toy Story 5", "CCI", "Multicines", dt=datetime(2026, 6, 25, 10, 0)),
            _make_screening("Toy Story 5", "CCI", "Multicines", dt=datetime(2026, 6, 25, 12, 0)),
        ]
        save_screenings(bare_db, screenings)
        results = get_all_screenings(bare_db)
        assert len(results) == 2
        assert all(r.movie.title == "Toy Story 5" for r in results)

    def test_stores_format_and_language(self, bare_db: Session) -> None:
        save_screenings(
            bare_db,
            [_make_screening("Bleach", "CCI", "Multicines", fmt="IMAX 3D", language="Subtitulada")],
        )
        result = get_all_screenings(bare_db)[0]
        assert result.format == "IMAX 3D"
        assert result.language == "Subtitulada"

    def test_raises_for_unknown_complex(self, bare_db: Session) -> None:
        with pytest.raises(ValueError, match="Complex NotAComplex"):
            save_screenings(bare_db, [_make_screening("Inception", "NotAComplex", "Multicines")])


class TestGetAllScreenings:
    def test_returns_all_screenings(self, seeded_db: Session) -> None:
        assert len(get_all_screenings(seeded_db)) == 2

    def test_results_carry_nested_objects(self, seeded_db: Session) -> None:
        s = get_all_screenings(seeded_db)[0]
        assert s.movie.title
        assert s.complex.name
        assert s.complex.company.name
        assert s.complex.company.base_url

    def test_filter_by_company_name(self, seeded_db: Session) -> None:
        results = get_all_screenings(seeded_db, cinema_company_name="Multicines")
        assert len(results) == 1
        assert results[0].complex.company.name == "Multicines"

    def test_filter_by_complex_name(self, seeded_db: Session) -> None:
        results = get_all_screenings(seeded_db, cinema_complex_name="San Luis")
        assert len(results) == 1
        assert results[0].complex.name == "San Luis"

    def test_ordered_by_datetime(self, seeded_db: Session) -> None:
        results = get_all_screenings(seeded_db)
        datetimes = [r.datetime for r in results]
        assert datetimes == sorted(datetimes)

    def test_unknown_filter_returns_empty(self, seeded_db: Session) -> None:
        assert get_all_screenings(seeded_db, cinema_company_name="Ghost") == []


def _tmdb_result(tmdb_id: int = 862, title: str = "Toy Story 5") -> TMDBMovie:
    return TMDBMovie(
        tmdb_id=tmdb_id,
        tmdb_title=title,
        poster_path="/poster.jpg",
        overview="Woody and Buzz are back.",
        runtime=90,
        certification="G",
        release_date="2026-06-20",
    )


class TestEnrichMoviesWithTmdb:
    def test_populates_tmdb_fields(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=_tmdb_result()):
            enrich_movies_with_tmdb(bare_db)
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        assert movie.tmdb_id == 862
        assert movie.tmdb_title == "Toy Story 5"
        assert movie.poster_path == "/poster.jpg"
        assert movie.runtime == 90
        assert movie.certification == "G"

    def test_merges_duplicate_titles_sharing_tmdb_id(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        save_screenings(bare_db, [_make_screening("Toy Story Five", "San Luis", "Supercines")])

        with patch("app.tmdb.search_movie", return_value=_tmdb_result()):
            enrich_movies_with_tmdb(bare_db)

        movies = list(bare_db.execute(select(MovieModel)).scalars().all())
        assert len(movies) == 1
        screenings = get_all_screenings(bare_db)
        assert len(screenings) == 2

    def test_no_unique_violation_when_multiple_titles_resolve_to_same_tmdb_id_in_same_run(
        self, bare_db: Session
    ) -> None:
        # Regression: without db.flush() after each assignment, the second movie fails
        # with a UNIQUE constraint error on tmdb_id at commit time.
        save_screenings(bare_db, [_make_screening("Jackass", "CCI", "Multicines")])
        save_screenings(bare_db, [_make_screening("Jackass: La Última Y Nos Vamos", "San Luis", "Supercines")])
        save_screenings(
            bare_db, [_make_screening("Jackass: Forever", "CCI", "Multicines", dt=datetime(2026, 6, 25, 16, 0))]
        )

        with patch(
            "app.tmdb.search_movie", return_value=_tmdb_result(tmdb_id=1612018, title="Jackass: Lo mejor para el final")
        ):
            enrich_movies_with_tmdb(bare_db)  # must not raise

        movies = list(bare_db.execute(select(MovieModel)).scalars().all())
        assert len(movies) == 1
        assert movies[0].tmdb_id == 1612018

    def test_skips_already_enriched_movies(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        movie.tmdb_id = 862
        bare_db.commit()

        with patch("app.tmdb.search_movie") as mock_search:
            enrich_movies_with_tmdb(bare_db)
            mock_search.assert_not_called()

    def test_leaves_movie_unenriched_when_no_tmdb_result(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Obscure Local Film", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=None):
            enrich_movies_with_tmdb(bare_db)
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        assert movie.tmdb_id is None

    def test_enriched_fields_visible_via_get_all_screenings(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=_tmdb_result()):
            enrich_movies_with_tmdb(bare_db)
        result = get_all_screenings(bare_db)[0]
        assert result.movie.tmdb_id == 862
        assert result.movie.poster_path == "/poster.jpg"


class TestTmdbAttemptPolicy:
    def test_a_miss_increments_the_attempt_counter(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Mexico Vs Ecuador", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=None):
            enrich_movies_with_tmdb(bare_db)
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        assert movie.tmdb_attempts == 1

    def test_repeated_misses_accumulate_then_stop_being_retried(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Mexico Vs Ecuador", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=None) as mock_search:
            for _ in range(MAX_TMDB_ATTEMPTS + 2):
                enrich_movies_with_tmdb(bare_db)
        # Runs past the cap must not reach TMDB at all.
        assert mock_search.call_count == MAX_TMDB_ATTEMPTS
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        assert movie.tmdb_attempts == MAX_TMDB_ATTEMPTS
        assert movie.tmdb_id is None

    def test_a_successful_lookup_leaves_the_counter_alone(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        with patch("app.tmdb.search_movie", return_value=_tmdb_result()):
            enrich_movies_with_tmdb(bare_db)
        movie = bare_db.execute(select(MovieModel)).scalar_one()
        assert movie.tmdb_attempts == 0

    def test_progress_survives_a_crash_partway_through(self, bare_db: Session) -> None:
        # Each movie is committed as it goes, so API work already done is not lost.
        save_screenings(bare_db, [_make_screening("Toy Story 5", "CCI", "Multicines")])
        save_screenings(bare_db, [_make_screening("Supergirl", "San Luis", "Supercines")])

        def explode_on_second(title: str) -> object:
            if title == "Toy Story 5":
                return _tmdb_result()
            raise RuntimeError("TMDB exploded")

        with patch("app.tmdb.search_movie", side_effect=explode_on_second):
            with pytest.raises(RuntimeError):
                enrich_movies_with_tmdb(bare_db)

        enriched = bare_db.execute(select(MovieModel).where(MovieModel.title == "Toy Story 5")).scalar_one()
        assert enriched.tmdb_id == 862


class TestSqliteConfiguration:
    def test_connections_use_wal_journal_mode(self, tmp_path: Path) -> None:
        # The daily scrape rewrites every screening while the API may be serving
        # reads. In the default `delete` journal mode a writer blocks readers.
        engine = create_engine(f"sqlite:///{tmp_path / 'wal.db'}")
        configure_sqlite(engine)
        with engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "wal"

    def test_connections_wait_instead_of_failing_on_a_locked_database(self, tmp_path: Path) -> None:
        engine = create_engine(f"sqlite:///{tmp_path / 'busy.db'}")
        configure_sqlite(engine)
        with engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA busy_timeout").scalar_one() > 0


class TestDeleteAllScreenings:
    def test_removes_every_screening(self, seeded_db: Session) -> None:
        assert len(get_all_screenings(seeded_db)) > 0
        delete_all_screenings(seeded_db)
        assert get_all_screenings(seeded_db) == []


class TestGetAllCinemaCompanies:
    def test_returns_both_companies(self, bare_db: Session) -> None:
        names = {c.name for c in get_all_cinema_companies(bare_db)}
        assert names == {"Multicines", "Supercines"}

    def test_includes_base_url(self, bare_db: Session) -> None:
        companies = get_all_cinema_companies(bare_db)
        multicines = next(c for c in companies if c.name == "Multicines")
        assert multicines.base_url == "https://www.multicines.com.ec"


class TestGetAllCinemaComplexes:
    def test_returns_complexes_for_company(self, bare_db: Session) -> None:
        results = get_all_cinema_complexes_from_cinema_company(bare_db, "Multicines")
        assert len(results) == 1
        assert results[0].name == "CCI"

    def test_includes_company_on_result(self, bare_db: Session) -> None:
        results = get_all_cinema_complexes_from_cinema_company(bare_db, "Supercines")
        assert results[0].company.name == "Supercines"

    def test_empty_for_unknown_company(self, bare_db: Session) -> None:
        assert get_all_cinema_complexes_from_cinema_company(bare_db, "Unknown") == []
