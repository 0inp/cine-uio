"""
Playwright scraper for cinema data.
"""

import random
from datetime import datetime, timedelta
from typing import List

from entities import (
    CinemaCompany as EntityCinemaCompany,
)
from entities import (
    CinemaComplex as EntityCinemaComplex,
)
from entities import (
    Movie as EntityMovie,
)
from entities import (
    Screening as EntityScreening,
)
from models import CinemaCompany, CinemaComplex, Movie, Screening
from playwright.async_api import Browser, Page, async_playwright
from sqlalchemy.orm import Session


class Scraper:
    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None

    async def initialize(self) -> None:
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def cleanup(self) -> None:
        """Clean up Playwright resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_company(self, company: CinemaCompany, db_session: Session) -> None:
        """
        Scrape a single cinema company.

        Args:
            company: The CinemaCompany to scrape.
            db_session: SQLAlchemy database session.
        """
        if not self.browser:
            await self.initialize()

        page = await self.browser.new_page()
        await page.goto(company.base_url)

        # Extract CinemaComplex URLs from the company's page.
        complex_urls = await self._extract_complex_urls(page, company)

        for url in complex_urls:
            await self._scrape_complex(page, url, company, db_session)

        await page.close()

    async def _extract_complex_urls(
        self, page: Page, company: CinemaCompany
    ) -> List[str]:
        """
        Extract CinemaComplex URLs from the company's page.

        Args:
            page: Playwright Page object.
            company: The CinemaCompany being scraped.

        Returns:
            List of URLs for CinemaComplex pages.
        """
        # TODO: Implement logic to extract complex URLs (e.g., from a "cartelera" or "showtimes" page).
        return []

    async def _scrape_complex(
        self, page: Page, complex_url: str, company: CinemaCompany, db_session: Session
    ) -> None:
        """
        Scrape a single CinemaComplex and its movies/screenings.

        Args:
            page: Playwright Page object.
            complex_url: URL of the CinemaComplex to scrape.
            company: The CinemaCompany being scraped.
            db_session: SQLAlchemy database session.
        """
        await page.goto(complex_url)

        # Extract CinemaComplex data.
        complex = self._extract_complex_data(page, complex_url, company)
        db_session.add(complex)
        db_session.commit()
        db_session.refresh(complex)

        # Extract Movie and Screening data.
        movies = await self._extract_movies_and_screenings(page, complex)
        for movie in movies:
            db_session.add(movie)
            db_session.commit()
            db_session.refresh(movie)

    def _extract_complex_data(
        self, page: Page, complex_url: str, company: CinemaCompany
    ) -> CinemaComplex:
        """
        Extract CinemaComplex data from the page.

        Args:
            page: Playwright Page object.
            complex_url: URL of the CinemaComplex.
            company: The CinemaCompany being scraped.

        Returns:
            CinemaComplex object.
        """
        # TODO: Implement logic to extract complex name and URL part.
        return CinemaComplex(
            name="",
            url_part="",
            company_id=company.id,
        )

    async def _extract_movies_and_screenings(
        self, page: Page, complex: CinemaComplex
    ) -> List[Movie]:
        """
        Extract Movie and Screening data from the CinemaComplex page.

        Args:
            page: Playwright Page object.
            complex: The CinemaComplex being scraped.

        Returns:
            List of Movie objects with associated Screenings.
        """
        # TODO: Implement logic to extract movies and screenings.
        return []

    def dummy_scrape(self, db_session: Session) -> None:
        """
        Generate dummy data for testing purposes.

        Args:
            db_session: SQLAlchemy database session.
        """
        companies = db_session.query(CinemaCompany).all()
        complexes = db_session.query(CinemaComplex).all()

        dummy_movies = [
            "Dune: Part Two",
            "Godzilla x Kong: The New Empire",
            "Furiosa: A Mad Max Saga",
            "The Fall Guy",
            "Inside Out 2",
        ]

        formats = ["2D", "3D"]
        languages = ["original + subbed in Spanish", "dubbed in Spanish"]

        for complex in complexes:
            # Create 2-3 movies per complex
            for _ in range(random.randint(2, 3)):
                movie_title = random.choice(dummy_movies)
                movie = Movie(title=movie_title)
                db_session.add(movie)
                db_session.commit()
                db_session.refresh(movie)

                # Create 2-3 screenings per movie
                for _ in range(random.randint(2, 3)):
                    screening_time = datetime.now() + timedelta(
                        days=random.randint(1, 3), hours=random.randint(0, 23)
                    )
                    format = random.choice(formats)
                    language = random.choice(languages)
                    screening = Screening(
                        datetime=screening_time,
                        format=format,
                        language=language,
                        movie_id=movie.id,
                        complex_id=complex.id,
                    )
                    db_session.add(screening)
            db_session.commit()
