# - MulticinesScraper: Scraper for Multicines website.
import sys
from datetime import date, datetime, time, timedelta
from typing import TypedDict
from urllib.parse import parse_qs, urlparse, urlunparse

import requests
from playwright.sync_api import Page

from app.database import save_screenings
from app.entities import CinemaComplex, Movie, Screening
from app.logging import logger
from app.scrapers.base import Scraper


class ScreeningsResponseDict(TypedDict):
    name: str
    theaterTypes: list[ScreeningTheaterTypeDict]


class ScreeningTheaterTypeDict(TypedDict):
    name: str
    sessions: list[ScreeningSessionDict]


class ScreeningSessionDict(TypedDict):
    showtime: str


class MulticinesScraper(Scraper):
    company_name = "Multicines"

    def _scrape_complex_page(self, page: Page, complex: CinemaComplex) -> None:
        url = f"{complex.company.base_url}{complex.url_part}"
        logger.info(f"Scraping complex: {url}")
        page.goto(url)

        screenings_response = page.wait_for_event(
            "response",
            lambda response: (
                "multicines.api.x-mart.io/api/multicines-mw/movies" in response.url
                and "sessions/now" not in response.url
            ),
        )

        response_json = screenings_response.json()
        movies_by_multicines_ids: dict[str, Movie] = {}

        movies: list[Movie] = []
        for movie_json in response_json:
            movie_multicines_id: str = movie_json["externalId"]
            movie: Movie = Movie(title=movie_json["title"].title())
            movies_by_multicines_ids[movie_multicines_id] = movie
            movies.append(movie)
        logger.info(f"Encountered {len(movies_by_multicines_ids)} movies")

        screenings: list[Screening] = []
        for movie_id, movie in movies_by_multicines_ids.items():
            movie_screenings: list[Screening] = []
            movie_url = f"{complex.company.base_url}/movie/{movie.title.lower().replace(' ', '-')}/{movie_id}"
            logger.info(f"Navigating to movie: {movie_url}")
            page.goto(movie_url)

            captured_request = page.wait_for_event(
                "request",
                lambda request: "multicines.api.x-mart.io/api/multicines-mw/sessions" in request.url,
            )

            request_headers: dict[str, str] = captured_request.headers

            parsed_url = urlparse(captured_request.url)
            request_query_params: dict[str, list[str]] = parse_qs(parsed_url.query)

            # Reconstruct the base API URL WITHOUT the query string
            base_api_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))

            today = date.today()
            for i in range(7):
                current_day = today + timedelta(days=i)

                start_dt = datetime.combine(current_day, time.min)
                end_dt = datetime.combine(current_day, time(23, 59, 59, 999000))

                start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

                request_query_params["dateFrom"] = [start_str]
                request_query_params["dateTo"] = [end_str]

                screenings_response = requests.get(
                    base_api_url,
                    headers=request_headers,
                    params=request_query_params,
                )

                if screenings_response.status_code == 200:
                    screenings_json: list[ScreeningsResponseDict] = screenings_response.json()
                    for screening_json in screenings_json:
                        screening_language: str = screening_json["name"]
                        screening_theater_types: list[ScreeningTheaterTypeDict] = screening_json["theaterTypes"]
                        for screening_theater_type in screening_theater_types:
                            screening_format: str = screening_theater_type["name"]
                            screening_sessions: list[ScreeningSessionDict] = screening_theater_type["sessions"]
                            for screening_session in screening_sessions:
                                screening_datetime = screening_session["showtime"]
                                screening = Screening(
                                    datetime=datetime.fromisoformat(screening_datetime),
                                    format=screening_format,
                                    language=screening_language,
                                    complex=complex,
                                    movie=movie,
                                )
                                movie_screenings.append(screening)
                else:
                    logger.error(f"Error {screenings_response.status_code}: {screenings_response.text}")

            logger.info(f"Movie {movie.title} has {len(movie_screenings)} screenings")

            screenings.extend(movie_screenings)

        try:
            save_screenings(self.db, screenings)
        except Exception as e:
            logger.error(f"Error saving screenings during scraping: {e}", exc_info=True)
            sys.exit(1)
        finally:
            self.db.close()

        logger.info(
            f"{len(movies)} movies have been processed, with a total of {len(screenings)} screenings for {complex.name}"
        )
