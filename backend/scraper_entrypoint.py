"""
Script to run the scrapers for cinema data.
"""

import sys

from dotenv import load_dotenv

# Must run before importing app.*: database.py reads DATABASE_URL and tmdb.py reads
# TMDB_READ_ACCESS_TOKEN, so the .env has to be loaded before those modules are imported.
load_dotenv()

from sqlalchemy import func, select  # noqa: E402

from app.database import SessionLocal, enrich_movies_with_tmdb  # noqa: E402
from app.logging import logger  # noqa: E402
from app.models import CinemaComplex  # noqa: E402
from app.notifications import notify  # noqa: E402
from app.observability import finish_run, last_run, start_run  # noqa: E402
from app.scrape import scrape_and_publish  # noqa: E402


def main() -> None:
    db_session = SessionLocal()

    # Captured before this run overwrites it, so a return to health can be announced
    # rather than passing unnoticed after a string of failure alerts.
    previous = last_run(db_session)
    was_failing = previous is not None and not previous.succeeded

    total_complexes = db_session.execute(select(func.count()).select_from(CinemaComplex)).scalar_one()
    run = start_run(db_session)
    failures: list[str] = []

    try:
        failures = scrape_and_publish(db_session)
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        failures.append(f"the run stopped early: {e}")

    if not failures:
        try:
            enrich_movies_with_tmdb(db_session)
        except Exception as e:
            failures.append(f"TMDB enrichment failed: {e}")
            logger.error(f"TMDB enrichment failed: {e}", exc_info=True)

    finish_run(db_session, run, succeeded=total_complexes - len(failures), failures=failures)
    duration = (run.finished_at - run.started_at).total_seconds() if run.finished_at else 0
    db_session.close()

    if failures:
        summary = "\n".join(f"  - {f}" for f in failures[:10])
        if len(failures) > 10:
            summary += f"\n  … and {len(failures) - 10} more"
        notify(f"cine-uio: scrape finished with {len(failures)} failure(s) in {duration:.0f}s\n{summary}")
        logger.error(f"Scrape run completed with {len(failures)} failure(s) in {duration:.0f}s")
        sys.exit(1)

    if was_failing:
        notify(f"cine-uio: scrape is healthy again — {total_complexes} complexes in {duration:.0f}s")

    logger.info(f"Scraping completed successfully in {duration:.0f}s")


if __name__ == "__main__":
    main()
