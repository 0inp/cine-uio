"""
Script to run the scrapers for cinema data.
"""

import sys

from app.database import SessionLocal, delete_all_screenings, get_all_cinema_companies
from app.logging import logger
from app.scrapers.base import Scraper


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

    logger.info("Scraping completed successfully!")


if __name__ == "__main__":
    main()
