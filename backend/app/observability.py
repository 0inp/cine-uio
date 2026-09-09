"""Whether the data can be trusted, and how we know."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.logging import logger
from app.models import CinemaComplex as CinemaComplexModel
from app.models import ScrapeRun
from app.models import Screening as ScreeningModel

# The scrape runs daily, so a day and a half without a clean one means something
# is wrong — long enough to absorb a laptop that stayed shut, short enough to
# notice before the listings are actually wrong.
STALE_AFTER_HOURS = 36

Status = Literal["ok", "stale", "failing", "unknown"]


@dataclass
class Health:
    status: Status
    detail: str
    last_run_at: datetime | None
    last_success_at: datetime | None
    hours_since_success: float | None
    complexes_total: int
    complexes_with_screenings: int
    upcoming_screenings: int


def start_run(db: Session, now: datetime | None = None) -> ScrapeRun:
    run = ScrapeRun(started_at=now or datetime.now())
    db.add(run)
    db.commit()
    return run


def finish_run(db: Session, run: ScrapeRun, succeeded: int, failures: list[str]) -> None:
    run.finished_at = datetime.now()
    run.complexes_succeeded = succeeded
    run.complexes_failed = len(failures)
    run.failures = "\n".join(failures)
    db.commit()


def last_run(db: Session) -> ScrapeRun | None:
    return db.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(1)).scalar_one_or_none()


def last_successful_run(db: Session) -> ScrapeRun | None:
    return db.execute(
        select(ScrapeRun)
        .where(ScrapeRun.finished_at.is_not(None), ScrapeRun.complexes_failed == 0)
        .order_by(ScrapeRun.started_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def current_health(db: Session, now: datetime | None = None) -> Health:
    """Summarise whether what the site is serving can be trusted right now."""
    now = now or datetime.now()

    complexes_total = db.execute(select(func.count()).select_from(CinemaComplexModel)).scalar_one()
    complexes_with_screenings = db.execute(select(func.count(func.distinct(ScreeningModel.complex_id)))).scalar_one()
    upcoming = db.execute(
        select(func.count()).select_from(ScreeningModel).where(ScreeningModel.datetime >= _start_of(now))
    ).scalar_one()

    latest = last_run(db)
    latest_success = last_successful_run(db)
    hours: float | None = None
    if latest_success is not None:
        hours = (now - latest_success.started_at).total_seconds() / 3600

    status, detail = _classify(latest, latest_success, hours, upcoming)
    return Health(
        status=status,
        detail=detail,
        last_run_at=latest.started_at if latest else None,
        last_success_at=latest_success.started_at if latest_success else None,
        hours_since_success=round(hours, 1) if hours is not None else None,
        complexes_total=complexes_total,
        complexes_with_screenings=complexes_with_screenings,
        upcoming_screenings=upcoming,
    )


def _start_of(moment: datetime) -> datetime:
    return datetime.combine(moment.date(), datetime.min.time())


def _classify(
    latest: ScrapeRun | None,
    latest_success: ScrapeRun | None,
    hours_since_success: float | None,
    upcoming: int,
) -> tuple[Status, str]:
    if latest is None:
        return "unknown", "no scrape has been recorded yet"
    if latest.finished_at is None:
        return "failing", "the last scrape did not finish"
    if latest.complexes_failed:
        return "failing", f"the last scrape lost {latest.complexes_failed} complex(es)"
    if latest_success is None or hours_since_success is None:
        return "stale", "no scrape has ever completed cleanly"
    if hours_since_success > STALE_AFTER_HOURS:
        return "stale", f"the last clean scrape was {hours_since_success:.0f}h ago"
    if upcoming == 0:
        # Everything ran, and there is still nothing to show: the listings are past.
        return "stale", "no screenings are scheduled from today onwards"
    return "ok", f"last clean scrape {hours_since_success:.1f}h ago"


def days_of_listings(db: Session, now: datetime | None = None) -> int:
    """How many distinct future dates the listings cover, as a coverage signal."""
    today: date = (now or datetime.now()).date()
    rows = (
        db.execute(
            select(func.distinct(func.date(ScreeningModel.datetime))).where(
                ScreeningModel.datetime >= _start_of(now or datetime.now())
            )
        )
        .scalars()
        .all()
    )
    logger.debug(f"{len(rows)} distinct dates from {today}")
    return len(rows)
