"""
Script to run the scrapers for cinema data.
"""

import sys

from dotenv import load_dotenv

# Must run before importing app.*: database.py reads DATABASE_URL and tmdb.py reads
# TMDB_READ_ACCESS_TOKEN, so the .env has to be loaded before those modules are imported.
load_dotenv()

from app.database import SessionLocal, enrich_movies_with_tmdb  # noqa: E402
from app.logging import logger  # noqa: E402
from app.scrape import scrape_and_publish  # noqa: E402


def main() -> None:
    db_session = SessionLocal()
    failures: list[str] = []

    try:
        failures = scrape_and_publish(db_session)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        db_session.close()
        sys.exit(1)

    try:
        enrich_movies_with_tmdb(db_session)
    except Exception as e:
        failures.append(f"TMDB enrichment failed: {e}")
        logger.error(f"TMDB enrichment failed: {e}", exc_info=True)
    finally:
        db_session.close()

    if failures:
        # Exit non-zero so a partial run is visible in the launchd log rather than
        # passing for success, which is how a whole complex was lost unnoticed.
        logger.error(f"Scrape run completed with {len(failures)} failure(s)")
        sys.exit(1)

    logger.info("Scraping completed successfully!")


if __name__ == "__main__":
    main()
