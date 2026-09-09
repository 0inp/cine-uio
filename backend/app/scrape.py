"""Orchestration for a scrape run: gather results, then publish them per complex."""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.database import (
    get_all_cinema_companies,
    get_all_cinema_complexes_from_cinema_company,
    replace_screenings_for_complex,
)
from app.entities import Screening
from app.logging import logger


@dataclass
class ComplexScrapeResult:
    """What one complex's scrape produced, successfully or not.

    Scrapers report an outcome rather than writing to the database themselves, so
    the decision of what to publish belongs to one place.
    """

    company_name: str
    complex_name: str
    screenings: list[Screening] = field(default_factory=list)
    error: str | None = None

    @property
    def label(self) -> str:
        return f"{self.company_name} / {self.complex_name}"


def apply_scrape_results(db: Session, results: list[ComplexScrapeResult]) -> list[str]:
    """Publish every complex that scraped successfully; return a line per failure.

    Each complex is swapped independently, so one venue failing neither erases its
    own listings nor holds back the others. A failure is never raised: the remaining
    complexes still get published, and the caller decides what a failed run means.
    """
    failures: list[str] = []

    for result in results:
        if result.error is not None:
            failures.append(f"{result.label}: {result.error} — kept the previous screenings")
            continue

        if not result.screenings:
            # A venue that legitimately has no showings is indistinguishable from one
            # whose scrape quietly broke, and wiping a venue is the costlier mistake.
            failures.append(f"{result.label}: scraped no screenings — kept the previous screenings")
            continue

        try:
            replace_screenings_for_complex(db, result.company_name, result.complex_name, result.screenings)
        except Exception as e:
            failures.append(f"{result.label}: could not be saved ({e}) — kept the previous screenings")
        else:
            logger.info(f"{result.label}: published {len(result.screenings)} screenings")

    for failure in failures:
        logger.error(failure)

    return failures


def run_all_scrapes(db: Session) -> list[ComplexScrapeResult]:
    """Scrape every complex of every registered company. Does not touch screenings."""
    from app.scrapers.base import Scraper  # local import: scrapers import this module's siblings

    results: list[ComplexScrapeResult] = []
    for company in get_all_cinema_companies(db):
        logger.info(f"Processing company: {company.name}")
        complexes = get_all_cinema_complexes_from_cinema_company(db, company.name)
        results.extend(Scraper.create(company).run_scrape(complexes))
    return results
