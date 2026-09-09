from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScrapeRun
from app.observability import (
    STALE_AFTER_HOURS,
    current_health,
    finish_run,
    last_run,
    last_successful_run,
    start_run,
)

NOW = datetime(2026, 6, 25, 12, 0)


def _record(db: Session, *, started: datetime, failed: int = 0, finished: bool = True) -> ScrapeRun:
    run = ScrapeRun(
        started_at=started,
        finished_at=started + timedelta(minutes=9) if finished else None,
        complexes_succeeded=49 - failed,
        complexes_failed=failed,
        failures="\n".join(f"venue {i} failed" for i in range(failed)),
    )
    db.add(run)
    db.commit()
    return run


class TestRunRecording:
    def test_start_then_finish_records_the_outcome(self, seeded_db: Session) -> None:
        run = start_run(seeded_db, now=NOW)
        finish_run(seeded_db, run, succeeded=47, failures=["a failed", "b failed"])

        stored = seeded_db.execute(select(ScrapeRun)).scalar_one()
        assert stored.complexes_succeeded == 47
        assert stored.complexes_failed == 2
        assert stored.failures == "a failed\nb failed"
        assert stored.finished_at is not None

    def test_a_clean_run_counts_as_succeeded(self, seeded_db: Session) -> None:
        run = start_run(seeded_db, now=NOW)
        finish_run(seeded_db, run, succeeded=49, failures=[])
        assert run.succeeded is True

    def test_an_unfinished_run_is_not_a_success(self, seeded_db: Session) -> None:
        run = start_run(seeded_db, now=NOW)
        assert run.succeeded is False

    def test_last_run_is_the_most_recent_whatever_its_outcome(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(days=2))
        newest = _record(seeded_db, started=NOW - timedelta(hours=2), failed=3)
        assert last_run(seeded_db) is not None
        assert last_run(seeded_db).id == newest.id  # type: ignore[union-attr]

    def test_last_successful_run_skips_the_failed_ones(self, seeded_db: Session) -> None:
        clean = _record(seeded_db, started=NOW - timedelta(days=2))
        _record(seeded_db, started=NOW - timedelta(hours=2), failed=3)
        assert last_successful_run(seeded_db).id == clean.id  # type: ignore[union-attr]


class TestHealth:
    def test_unknown_before_any_run(self, seeded_db: Session) -> None:
        health = current_health(seeded_db, now=NOW)
        assert health.status == "unknown"
        assert health.last_run_at is None

    def test_failing_when_the_last_run_lost_a_complex(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(hours=1), failed=7)
        health = current_health(seeded_db, now=NOW)
        assert health.status == "failing"
        assert "7" in health.detail

    def test_failing_when_the_last_run_never_finished(self, seeded_db: Session) -> None:
        # A crashed or killed run leaves no finished_at; silence is not success.
        _record(seeded_db, started=NOW - timedelta(hours=1), finished=False)
        assert current_health(seeded_db, now=NOW).status == "failing"

    def test_stale_when_the_last_clean_run_is_too_old(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(hours=STALE_AFTER_HOURS + 2))
        health = current_health(seeded_db, now=NOW)
        assert health.status == "stale"
        assert health.hours_since_success is not None and health.hours_since_success > STALE_AFTER_HOURS

    def test_ok_when_a_recent_run_was_clean(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(hours=6))
        health = current_health(seeded_db, now=NOW)
        assert health.status == "ok"
        assert health.upcoming_screenings == 2

    def test_stale_when_everything_ran_but_nothing_is_showing(self, seeded_db: Session) -> None:
        # The scrape worked and there is still nothing ahead: the listings are past.
        _record(seeded_db, started=NOW - timedelta(hours=6))
        health = current_health(seeded_db, now=NOW + timedelta(days=30))
        assert health.status == "stale"
        assert health.upcoming_screenings == 0

    def test_reports_complex_coverage(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(hours=6))
        health = current_health(seeded_db, now=NOW)
        assert health.complexes_total == 2
        assert health.complexes_with_screenings == 2

    def test_a_failing_run_does_not_erase_the_last_known_good(self, seeded_db: Session) -> None:
        _record(seeded_db, started=NOW - timedelta(hours=8))
        _record(seeded_db, started=NOW - timedelta(hours=1), failed=2)
        health = current_health(seeded_db, now=NOW)
        assert health.status == "failing"
        assert health.last_success_at == NOW - timedelta(hours=8)
