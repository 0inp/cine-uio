# """
# Base Scraper class with registry pattern.
# """
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import ClassVar

from playwright.sync_api import Browser, Page, sync_playwright

from app.entities import CinemaCompany, CinemaComplex, Screening
from app.logging import logger
from app.scrape import ComplexScrapeResult

# Scraping the whole country walks 49 venues back to back, and the sites drop
# connections under that load: a single run saw 7 of 25 Supercines venues fail with
# "Connection reset by peer". A transient reset should not cost a venue its listings
# for the day, so each complex gets a few attempts with a widening pause.
MAX_COMPLEX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5.0


class Scraper(ABC):
    company_name: ClassVar[str]
    _registry: ClassVar[dict[str, type[Scraper]]] = {}

    def __init_subclass__(cls: type[Scraper], **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "company_name"):
            cls._registry[cls.company_name] = cls

    @classmethod
    def create(cls, company: CinemaCompany) -> Scraper:
        scraper_cls = cls._registry.get(company.name)
        if scraper_cls is None:
            raise ValueError(f"No scraper registered for company: {company.name}")
        return scraper_cls(company)

    def __init__(self, company: CinemaCompany) -> None:
        self.company: CinemaCompany = company

    @abstractmethod
    def _scrape_complex_page(self, page: Page, complex: CinemaComplex) -> list[Screening]:
        """Return the screenings found for one complex. Raise if the page cannot be read."""

    def run_scrape(self, complexes: list[CinemaComplex]) -> Iterator[ComplexScrapeResult]:
        """Yield an outcome per complex, as soon as each one is scraped.

        Scrapers no longer write to the database: they report, and the caller decides
        what to publish. A complex that fails is recorded as a failure rather than
        silently skipped, so a lost venue cannot pass for a successful run.
        """
        logger.info(f"Starting to scrape company: {self.company.name}")

        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=True)
            try:
                for complex in complexes:
                    yield self._scrape_one_complex(browser, complex)
            finally:
                browser.close()

    def _scrape_one_complex(self, browser: Browser, complex: CinemaComplex) -> ComplexScrapeResult:
        """Scrape one complex, retrying a transient failure before giving up on it."""
        label = f"{self.company.name} / {complex.name}"
        last_error = "scrape did not run"

        for attempt in range(1, MAX_COMPLEX_ATTEMPTS + 1):
            page: Page | None = None
            try:
                page = browser.new_page()
                screenings = self._scrape_complex_page(page, complex)
            except Exception as e:
                last_error = str(e) or type(e).__name__
                logger.warning(f"{label}: attempt {attempt}/{MAX_COMPLEX_ATTEMPTS} failed: {last_error}")
                if attempt < MAX_COMPLEX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
            else:
                logger.info(f"{complex.name}: scraped {len(screenings)} screenings")
                return ComplexScrapeResult(
                    company_name=self.company.name,
                    complex_name=complex.name,
                    screenings=screenings,
                )
            finally:
                if page is not None:
                    page.close()

        logger.error(f"{label}: giving up after {MAX_COMPLEX_ATTEMPTS} attempts: {last_error}")
        return ComplexScrapeResult(
            company_name=self.company.name,
            complex_name=complex.name,
            error=last_error,
        )
