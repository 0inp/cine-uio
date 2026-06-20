# - SupercinesScraper: Scraper for Supercines website.
import json
import re
import sys
from datetime import date, datetime, timedelta

import requests
from playwright.sync_api import ElementHandle, Page

from app.database import save_screenings
from app.entities import CinemaComplex, Movie, Screening
from app.logging import logger
from app.scrapers.base import Scraper


class SupercinesScraper(Scraper):
    company_name = "Supercines"

    def _scrape_complex_page(self, page: Page, complex: CinemaComplex) -> None:
        url = f"{complex.company.base_url}{complex.url_part}"
        logger.info(f"Scraping complex: {url}")
        page.goto(url, wait_until="networkidle")

        scripts: list[ElementHandle] = page.query_selector_all("script")

        script_content = None

        for script in scripts:
            content: str | None = script.text_content()
            if content and "self.__next_f.push" in content and "initialData" in content:
                script_content = content
                break

        if not script_content:
            logger.warning("No script content found containing 'self.__next_f.push' and 'initialData'")
            return

        sanitized_script_content: str = script_content.replace("\\n", "").replace("\\", "")
        try:
            json_match: re.Match | None = re.search(
                r'.*?("initialData".*)\}\]\]"\]\)',
                sanitized_script_content,
            )

            if not json_match:
                logger.debug("No initialData array found in script")
                return

            # Clean and parse the JSON
            json_str: str = "{" + json_match.group(1) + "}"

            movies_data: list[dict[str, str | int | None]] = json.loads(json_str).get("initialData", [])

            today: datetime = datetime.now()
            six_days_later: datetime = today + timedelta(days=6)
            movies: list[Movie] = []
            screenings: list[Screening] = []
            for movie_data in movies_data:
                movie_screenings: list[Screening] = []
                movie_title: str = str(movie_data.get("title", "")).strip()
                logger.info(f"Handling movie {movie_title}...")

                current_date: date = today.date()
                opening_date_str: str = str(movie_data.get("openingDate", ""))
                opening_date: datetime = datetime.strptime(opening_date_str, "%Y-%m-%d")
                if opening_date >= six_days_later:
                    logger.info("jumping this movie")
                    continue

                movie: Movie = Movie(
                    title=movie_title,
                )
                movies.append(movie)

                supercines_movie_id: str = str(movie_data.get("id"))
                base_xhr_url = (
                    f"https://www.supercines.com/api/proxy/movies/tecnologies?Id={supercines_movie_id}&Channel=web"
                )

                while current_date < six_days_later.date():
                    date_query_param: str = current_date.strftime("%Y-%m-%d")
                    xhr_url = f"{base_xhr_url}&Date={date_query_param}"

                    response = requests.get(xhr_url)
                    if not response.status_code == 200:
                        current_date += timedelta(days=1)
                        continue

                    response_data = response.json()
                    response_content = response_data.get("content", {})
                    tecnologies = response_content.get("tecnologies", []) if response_content else []
                    if not tecnologies:
                        current_date += timedelta(days=1)
                        continue

                    for tecnology in tecnologies:
                        screening_format: str = tecnology.get("tecnology", "")
                        screening_language: str = tecnology.get("tecnology", "")
                        tecnology_schedules: list[dict[str, int | str | bool]] = tecnology.get("schedules", [])
                        for tecnology_schedule in tecnology_schedules:
                            tecnology_schedule_time: str = str(tecnology_schedule.get("time", ""))
                            if not tecnology_schedule_time:
                                continue
                            screening_datetime: datetime = datetime.strptime(
                                date_query_param + " " + tecnology_schedule_time,
                                "%Y-%m-%d %H:%M",
                            )
                            screening: Screening = Screening(
                                datetime=screening_datetime,
                                format=screening_format,
                                language=screening_language,
                                complex=complex,
                                movie=movie,
                            )
                            movie_screenings.append(screening)

                    current_date += timedelta(days=1)

                logger.info(f"Movie {movie_title} has {len(movie_screenings)} screenings")
                screenings.extend(movie_screenings)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Failed to parse JSON: {json_str[:200]}...")  # Log first 200 chars for debugging
            return
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            return

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
