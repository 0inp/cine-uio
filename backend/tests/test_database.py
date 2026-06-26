from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.database import (
    delete_all_screenings,
    get_all_cinema_companies,
    get_all_cinema_complexes_from_cinema_company,
    get_all_screenings,
    save_screenings,
)
from app.entities import CinemaCompany, CinemaComplex, Movie, Screening


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
