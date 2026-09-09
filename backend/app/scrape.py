"""Orchestration for a scrape run: gather results, then publish them per complex."""

from collections.abc import Iterator
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


def publish_result(db: Session, result: ComplexScrapeResult) -> str | None:
    """Publish one complex's screenings. Returns a failure line, or None on success.

    Never raises: one venue failing must not stop the rest of the run.
    """
    if result.error is not None:
        failure = f"{result.label}: {result.error} — kept the previous screenings"
    elif not result.screenings:
        # A venue that legitimately has no showings is indistinguishable from one
        # whose scrape quietly broke, and wiping a venue is the costlier mistake.
        failure = f"{result.label}: scraped no screenings — kept the previous screenings"
    else:
        try:
            replace_screenings_for_complex(db, result.company_name, result.complex_name, result.screenings)
        except Exception as e:
            failure = f"{result.label}: could not be saved ({e}) — kept the previous screenings"
        else:
            logger.info(f"{result.label}: published {len(result.screenings)} screenings")
            return None

    logger.error(failure)
    return failure


def apply_scrape_results(db: Session, results: list[ComplexScrapeResult]) -> list[str]:
    """Publish a batch of already-collected results; return a line per failure."""
    return [failure for r in results if (failure := publish_result(db, r)) is not None]


def run_all_scrapes(db: Session) -> Iterator[ComplexScrapeResult]:
    """Yield one result per complex, as soon as each is scraped."""
    from app.scrapers.base import Scraper  # local import: scrapers import this module's siblings

    for company in get_all_cinema_companies(db):
        logger.info(f"Processing company: {company.name}")
        complexes = get_all_cinema_complexes_from_cinema_company(db, company.name)
        yield from Scraper.create(company).run_scrape(complexes)


def scrape_and_publish(db: Session) -> list[str]:
    """Scrape every complex and publish each one the moment it is done.

    A country-wide run takes well over an hour. Collecting every result first would
    mean a crash near the end throws away all of it, and would hold tens of thousands
    of screenings in memory for no reason. Publishing as we go keeps each complex's
    swap atomic while making progress durable.
    """
    return [failure for r in run_all_scrapes(db) if (failure := publish_result(db, r)) is not None]
