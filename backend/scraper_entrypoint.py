"""
Script to run the scrapers for cinema data.
"""

import asyncio
import logging
import sys

from app.database import SessionLocal, get_all_cinema_companies
from app.scraper import Scraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    db_session = SessionLocal()

    try:
        cinema_companies = get_all_cinema_companies(db_session, "Supercines")
    except Exception as e:
        logger.error(f"Error scraping data: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db_session.close()

    logger.info(f"Found {len(cinema_companies)} cinema companies in the database")

    for company in cinema_companies:
        logger.info(f"Processing company: {company.name}")

        scraper = Scraper.create(company)
        await scraper.run_scrape()

    logger.info("Scraping completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
