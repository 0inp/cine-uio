# - SupercinesScraper: Scraper for Supercines website.
import json
import re
from datetime import date, datetime, timedelta
from typing import Any

import requests
from playwright.sync_api import Page

from app.entities import CinemaComplex, Movie, Screening
from app.logging import logger
from app.scrapers.base import Scraper
from app.scrapers.fetching import fetch_json_all

# Supercines serves a different page to an unidentified client.
_USER_AGENT = "Mozilla/5.0 (compatible; cine-uio/1.0)"


DAYS_AHEAD = 7


def _parse_day(payload: Any, day: date, complex: CinemaComplex, movie: Movie) -> list[Screening]:
    """Turn one day's technologies payload into screenings. Empty payload -> nothing."""
    content = (payload or {}).get("content") or {}
    screenings: list[Screening] = []
    for tecnology in content.get("tecnologies") or []:
        label: str = tecnology.get("tecnology", "")
        parts = label.rsplit(" ", 1)
        screening_format = parts[0] if len(parts) > 1 else label
        screening_language = parts[1] if len(parts) > 1 else ""
        for schedule in tecnology.get("schedules", []):
            start = str(schedule.get("time", ""))
            if not start:
                continue
            screenings.append(
                Screening(
                    datetime=datetime.strptime(f"{day:%Y-%m-%d} {start}", "%Y-%m-%d %H:%M"),
                    format=screening_format,
                    language=screening_language,
                    complex=complex,
                    movie=movie,
                )
            )
    return screenings


class SupercinesScraper(Scraper):
    company_name = "Supercines"
    # The listings are already in the served HTML — rendering the page bought
    # nothing and cost roughly 3.5s a venue.
    needs_browser = False

    def _scrape_complex_page(self, page: Page | None, complex: CinemaComplex) -> list[Screening]:
        url = f"{complex.company.base_url}{complex.url_part}"
        logger.info(f"Scraping complex: {url}")
        response = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=30)
        response.raise_for_status()

        # The whole document is handed to the sanitizer rather than a single <script>
        # element: the payload marker below is unique in the page, and matching script
        # tags by hand is more brittle than letting the marker find itself.
        script_content = response.text
        if "self.__next_f.push" not in script_content or "initialData" not in script_content:
            # Raise rather than return nothing: an unreadable page is a failed scrape,
            # and reporting it keeps this complex's previous screenings published.
            raise ValueError("no script tag containing 'self.__next_f.push' and 'initialData'")

        sanitized_script_content: str = (
            re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), script_content)
            .replace("\\n", "")
            .replace("\\", "")
        )
        try:
            json_match: re.Match | None = re.search(
                r'.*?("initialData".*)\}\]\]"\]\)',
                sanitized_script_content,
            )

            if not json_match:
                raise ValueError("no initialData array found in the page script")

            # Clean and parse the JSON
            json_str: str = "{" + json_match.group(1) + "}"

            movies_data: list[dict[str, str | int | None]] = json.loads(json_str).get("initialData", [])

            today: date = datetime.now().date()
            days = [today + timedelta(days=i) for i in range(DAYS_AHEAD)]
            cutoff = today + timedelta(days=DAYS_AHEAD - 1)

            # Build every (movie, day) request first. The endpoint answers one day at
            # a time — it rejects a missing Date with 422 and knows no range — so the
            # only lever on ~120 calls per venue is to stop making them one at a time.
            wanted: list[tuple[Movie, date, str]] = []
            movies: list[Movie] = []
            for movie_data in movies_data:
                movie_title: str = str(movie_data.get("title", "")).strip()
                opening_date = datetime.strptime(str(movie_data.get("openingDate", "")), "%Y-%m-%d").date()
                if opening_date > cutoff:
                    logger.info(f"{movie_title}: opens after the window, skipping")
                    continue

                movie = Movie(title=movie_title)
                movies.append(movie)
                movie_id = str(movie_data.get("id"))
                base_xhr_url = f"https://www.supercines.com/api/proxy/movies/tecnologies?Id={movie_id}&Channel=web"
                wanted.extend((movie, day, f"{base_xhr_url}&Date={day:%Y-%m-%d}") for day in days)

            payloads = fetch_json_all([url for _, _, url in wanted], headers={"User-Agent": _USER_AGENT})

            screenings: list[Screening] = []
            per_movie: dict[str, int] = {}
            for (movie, day, _), payload in zip(wanted, payloads, strict=True):
                found = _parse_day(payload, day, complex, movie)
                per_movie[movie.title] = per_movie.get(movie.title, 0) + len(found)
                screenings.extend(found)

            for title, count in per_movie.items():
                logger.info(f"Movie {title} has {count} screenings")

        except json.JSONDecodeError as e:
            # Let it propagate: run_scrape records the complex as failed, and its
            # previous screenings stay published rather than being wiped.
            logger.debug(f"Failed to parse JSON: {json_str[:200]}...")  # Log first 200 chars for debugging
            raise ValueError(f"could not parse the embedded Next.js payload: {e}") from e

        logger.info(
            f"{len(movies)} movies have been processed, with a total of {len(screenings)} screenings for {complex.name}"
        )
        return screenings
