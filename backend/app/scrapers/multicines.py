# - MulticinesScraper: Scraper for Multicines website.
import re
import unicodedata
from datetime import date, datetime, time, timedelta
from typing import TypedDict
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from playwright.sync_api import Page

from app.entities import CinemaComplex, Movie, Screening
from app.logging import logger
from app.scrapers.base import Scraper
from app.scrapers.fetching import fetch_json_all


class ScreeningsResponseDict(TypedDict):
    name: str
    theaterTypes: list[ScreeningTheaterTypeDict]


class ScreeningTheaterTypeDict(TypedDict):
    name: str
    sessions: list[ScreeningSessionDict]


class ScreeningSessionDict(TypedDict):
    showtime: str


def _title_to_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFD", title)
    ascii_str = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")


DAYS_AHEAD = 7


def _day_bounds(first: date, days: int) -> tuple[str, str]:
    """TMDB-style millisecond timestamps spanning `days` from `first`, inclusive."""
    start = datetime.combine(first, time.min)
    end = datetime.combine(first + timedelta(days=days - 1), time(23, 59, 59, 999000))
    fmt = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"  # noqa: E731
    return fmt(start), fmt(end)


def _parse_sessions(payload: list[ScreeningsResponseDict], complex: CinemaComplex, movie: Movie) -> list[Screening]:
    screenings: list[Screening] = []
    for entry in payload:
        language: str = entry["name"]
        for theater_type in entry["theaterTypes"]:
            screening_format: str = theater_type["name"]
            for session in theater_type["sessions"]:
                screenings.append(
                    Screening(
                        datetime=datetime.fromisoformat(session["showtime"]),
                        format=screening_format,
                        language=language,
                        complex=complex,
                        movie=movie,
                    )
                )
    return screenings


class MulticinesScraper(Scraper):
    company_name = "Multicines"

    def _scrape_complex_page(self, page: Page | None, complex: CinemaComplex) -> list[Screening]:
        if page is None:  # pragma: no cover - needs_browser is True for this scraper
            raise RuntimeError("MulticinesScraper needs a browser page")

        url = f"{complex.company.base_url}{complex.url_part}"
        logger.info(f"Scraping complex: {url}")
        page.goto(url)

        movies_response = page.wait_for_event(
            "response",
            lambda response: (
                "multicines.api.x-mart.io/api/multicines-mw/movies" in response.url
                and "sessions/now" not in response.url
            ),
        )
        movies: dict[str, Movie] = {m["externalId"]: Movie(title=m["title"].title()) for m in movies_response.json()}
        logger.info(f"Encountered {len(movies)} movies")
        if not movies:
            return []

        # One navigation, not one per movie. The sessions request only varies by
        # filmId between movies — the auth token and every other parameter are
        # shared — so the rest of the catalogue is fetched over plain HTTP.
        first_id, first_movie = next(iter(movies.items()))
        page.goto(f"{complex.company.base_url}/movie/{_title_to_slug(first_movie.title)}/{first_id}")
        captured = page.wait_for_event(
            "request",
            lambda request: "multicines.api.x-mart.io/api/multicines-mw/sessions" in request.url,
        )

        headers: dict[str, str] = captured.headers
        parsed = urlparse(captured.url)
        base_params: dict[str, list[str]] = parse_qs(parsed.query)
        api_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

        # One request per movie covering the whole window. Asking day by day returned
        # exactly the same sessions for 7x the calls.
        date_from, date_to = _day_bounds(date.today(), DAYS_AHEAD)

        ordered = list(movies.items())
        urls = [
            f"{api_url}?{urlencode({**base_params, 'filmId': [film_id], 'dateFrom': [date_from], 'dateTo': [date_to]}, doseq=True)}"
            for film_id, _ in ordered
        ]
        payloads = fetch_json_all(urls, headers=headers)

        screenings: list[Screening] = []
        for (_, movie), payload in zip(ordered, payloads, strict=True):
            movie_screenings = _parse_sessions(payload or [], complex, movie)
            logger.info(f"Movie {movie.title} has {len(movie_screenings)} screenings")
            screenings.extend(movie_screenings)

        logger.info(
            f"{len(movies)} movies have been processed, with a total of {len(screenings)} screenings for {complex.name}"
        )
        return screenings
