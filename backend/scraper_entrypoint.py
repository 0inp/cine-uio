"""
Script to run the scrapers for cinema data.
"""

import sys

from dotenv import load_dotenv

# Must run before importing app.*: database.py reads DATABASE_URL and tmdb.py reads
# TMDB_READ_ACCESS_TOKEN, so the .env has to be loaded before those modules are imported.
load_dotenv()

from app.database import (  # noqa: E402
    SessionLocal,
    delete_all_screenings,
    enrich_movies_with_tmdb,
    get_all_cinema_companies,
)
from app.logging import logger  # noqa: E402
from app.scrapers.base import Scraper  # noqa: E402


def main() -> None:
    db_session = SessionLocal()

    try:
        delete_all_screenings(db_session)
        cinema_companies = get_all_cinema_companies(db_session)
    except Exception as e:
        logger.error(f"Error scraping data: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db_session.close()

    logger.info(f"Found {len(cinema_companies)} cinema companies in the database")

    for company in cinema_companies:
        logger.info(f"Processing company: {company.name}")
        scraper = Scraper.create(company)
        scraper.run_scrape()

    db_session = SessionLocal()
    enrichment_ok = True
    try:
        enrich_movies_with_tmdb(db_session)
    except Exception as e:
        enrichment_ok = False
        logger.error(f"TMDB enrichment failed: {e}", exc_info=True)
    finally:
        db_session.close()

    if enrichment_ok:
        logger.info("Scraping completed successfully!")
    else:
        logger.warning("Scraping completed, but TMDB enrichment failed — movies may lack metadata")


if __name__ == "__main__":
    main()
