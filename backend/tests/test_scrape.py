from collections.abc import Iterator
from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.database import get_all_screenings, save_screenings
from app.entities import CinemaCompany, CinemaComplex, Movie, Screening
from app.scrape import ComplexScrapeResult, apply_scrape_results, scrape_and_publish


def _screening(title: str, complex_name: str, company_name: str) -> Screening:
    company = CinemaCompany(name=company_name, base_url="https://example.com")
    return Screening(
        datetime=datetime(2026, 9, 9, 14, 30),
        projection="2D",
        audio="dubbed",
        complex=CinemaComplex(name=complex_name, url_part="/", company=company),
        movie=Movie(title=title),
    )


def _ok(title: str, complex_name: str, company_name: str) -> ComplexScrapeResult:
    return ComplexScrapeResult(
        company_name=company_name,
        complex_name=complex_name,
        screenings=[_screening(title, complex_name, company_name)],
    )


def _failed(complex_name: str, company_name: str) -> ComplexScrapeResult:
    return ComplexScrapeResult(company_name=company_name, complex_name=complex_name, screenings=[], error="boom")


class TestApplyScrapeResults:
    def test_publishes_successful_complexes(self, bare_db: Session) -> None:
        failures = apply_scrape_results(bare_db, [_ok("New film", "CCI", "Multicines")])
        assert failures == []
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["New film"]

    def test_a_failed_complex_keeps_its_previous_screenings(self, bare_db: Session) -> None:
        # This is the whole point: losing a scrape must not erase yesterday's data.
        save_screenings(bare_db, [_screening("Yesterday CCI", "CCI", "Multicines")])

        failures = apply_scrape_results(bare_db, [_failed("CCI", "Multicines")])

        assert len(failures) == 1
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["Yesterday CCI"]

    def test_one_failure_does_not_hold_back_the_others(self, bare_db: Session) -> None:
        save_screenings(bare_db, [_screening("Yesterday CCI", "CCI", "Multicines")])
        save_screenings(bare_db, [_screening("Yesterday San Luis", "San Luis", "Supercines")])

        failures = apply_scrape_results(
            bare_db,
            [_failed("CCI", "Multicines"), _ok("Today San Luis", "San Luis", "Supercines")],
        )

        assert len(failures) == 1
        titles = {s.movie.title for s in get_all_screenings(bare_db)}
        assert titles == {"Yesterday CCI", "Today San Luis"}

    def test_a_persistence_failure_is_reported_not_raised(self, bare_db: Session) -> None:
        # An unknown complex must not abort the whole run: the other venues still publish.
        failures = apply_scrape_results(
            bare_db,
            [_ok("Ghost film", "Nowhere", "Multicines"), _ok("Real film", "CCI", "Multicines")],
        )

        assert len(failures) == 1
        assert "Nowhere" in failures[0]
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["Real film"]

    def test_an_empty_scrape_is_a_failure_not_an_empty_cartelera(self, bare_db: Session) -> None:
        # A complex that legitimately returns nothing is indistinguishable from one
        # whose scrape broke, and wiping a venue is the more damaging reading.
        save_screenings(bare_db, [_screening("Yesterday CCI", "CCI", "Multicines")])

        empty = ComplexScrapeResult(company_name="Multicines", complex_name="CCI", screenings=[])
        failures = apply_scrape_results(bare_db, [empty])

        assert len(failures) == 1
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["Yesterday CCI"]


class TestScrapeAndPublish:
    """A country-wide run takes over an hour, so each complex is published the moment
    it is scraped rather than after every venue has been visited."""

    def test_a_complex_is_published_before_the_run_finishes(self, bare_db: Session) -> None:
        def results() -> Iterator[ComplexScrapeResult]:
            yield _ok("Early film", "CCI", "Multicines")
            raise RuntimeError("scraper died halfway")

        with patch("app.scrape.run_all_scrapes", return_value=results()):
            with pytest.raises(RuntimeError):
                scrape_and_publish(bare_db)

        # Work done before the crash survives it.
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["Early film"]

    def test_reports_failures_without_stopping(self, bare_db: Session) -> None:
        def results() -> Iterator[ComplexScrapeResult]:
            yield _failed("CCI", "Multicines")
            yield _ok("Late film", "San Luis", "Supercines")

        with patch("app.scrape.run_all_scrapes", return_value=results()):
            failures = scrape_and_publish(bare_db)

        assert len(failures) == 1
        assert [s.movie.title for s in get_all_screenings(bare_db)] == ["Late film"]

    def test_does_not_hold_every_result_in_memory(self, bare_db: Session) -> None:
        # The generator must be consumed lazily: each result is published as it
        # arrives, so the source is never fully materialised.
        published: list[str] = []

        def results() -> Iterator[ComplexScrapeResult]:
            yield _ok("First", "CCI", "Multicines")
            published.append(str([s.movie.title for s in get_all_screenings(bare_db)]))
            yield _ok("Second", "San Luis", "Supercines")

        with patch("app.scrape.run_all_scrapes", return_value=results()):
            scrape_and_publish(bare_db)

        # Observed from inside the generator, after the first yield was consumed.
        assert published == ["['First']"]
