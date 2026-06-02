"""
Script to populate the database with dummy data using the Scraper class.
"""

import sys

from database import SessionLocal
from scraper import Scraper


def main():
    db_session = SessionLocal()
    scraper = Scraper()

    try:
        print("Populating database with dummy data...")
        scraper.dummy_scrape(db_session)
        print("Dummy data populated successfully!")
    except Exception as e:
        print(f"Error populating dummy data: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
