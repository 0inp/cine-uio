# """
# Base Scraper class with registry pattern.
# """
from abc import ABC, abstractmethod
from typing import ClassVar

from playwright.sync_api import Browser, Page, sync_playwright
from sqlalchemy.orm import Session

from app.database import (
    SessionLocal,
    delete_all_screenings,
    get_all_cinema_complexes_from_cinema_company,
)
from app.entities import CinemaCompany, CinemaComplex
from app.logging import logger


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
        self.db: Session = SessionLocal()

    @abstractmethod
    def _scrape_complex_page(self, page: Page, complex: CinemaComplex) -> None:
        pass

    def run_scrape(self) -> None:
        logger.info("Deleting all screenings to start from scratch")
        delete_all_screenings(self.db)
        logger.info(f"Starting to scrape company: {self.company.name}")

        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=False)
            complexes: list[CinemaComplex] = get_all_cinema_complexes_from_cinema_company(self.db, self.company.name)
            for complex in complexes:
                try:
                    page: Page = browser.new_page()
                    self._scrape_complex_page(page, complex)
                finally:
                    page.close()
            browser.close()
