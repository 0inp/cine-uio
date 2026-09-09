from datetime import datetime

from sqlalchemy.orm import Session

from app.database import get_all_screenings, save_screenings
from app.entities import CinemaCompany, CinemaComplex, Movie, Screening
from app.scrape import ComplexScrapeResult, apply_scrape_results


def _screening(title: str, complex_name: str, company_name: str) -> Screening:
    company = CinemaCompany(name=company_name, base_url="https://example.com")
    return Screening(
        datetime=datetime(2026, 9, 9, 14, 30),
        format="2D",
        language="Doblada",
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
