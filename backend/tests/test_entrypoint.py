from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import scraper_entrypoint
from app.models import ScrapeRun


@contextmanager
def _run_with(db: Session, failures: list[str]) -> Iterator[MagicMock]:
    """Run main() against a test session, stubbing out the scrape and enrichment."""
    with (
        patch.object(scraper_entrypoint, "SessionLocal", return_value=db),
        patch.object(scraper_entrypoint, "scrape_and_publish", return_value=failures),
        patch.object(scraper_entrypoint, "enrich_movies_with_tmdb"),
        patch.object(scraper_entrypoint, "notify") as notify,
        patch.object(db, "close"),  # main() closes the session; the fixture owns it
    ):
        yield notify


def _previous_run(db: Session, *, failed: int) -> None:
    db.add(
        ScrapeRun(
            started_at=datetime.now() - timedelta(days=1),
            finished_at=datetime.now() - timedelta(days=1),
            complexes_succeeded=49 - failed,
            complexes_failed=failed,
            failures="something broke" if failed else "",
        )
    )
    db.commit()


class TestEntrypointNotifications:
    """The piece that decides whether a human ever hears about a broken scrape."""

    def test_a_failed_run_notifies_and_exits_non_zero(self, bare_db: Session) -> None:
        with _run_with(bare_db, ["CCI: boom"]) as notify:
            with pytest.raises(SystemExit) as exit_info:
                scraper_entrypoint.main()
        assert exit_info.value.code == 1
        notify.assert_called_once()
        assert "CCI: boom" in notify.call_args.args[0]

    def test_a_clean_run_after_a_clean_run_stays_quiet(self, bare_db: Session) -> None:
        _previous_run(bare_db, failed=0)
        with _run_with(bare_db, []) as notify:
            scraper_entrypoint.main()
        notify.assert_not_called()

    def test_recovery_is_announced(self, bare_db: Session) -> None:
        # Otherwise a return to health is left to guesswork after a failure alert.
        _previous_run(bare_db, failed=7)
        with _run_with(bare_db, []) as notify:
            scraper_entrypoint.main()
        notify.assert_called_once()
        assert "healthy again" in notify.call_args.args[0]

    def test_the_run_is_recorded_either_way(self, bare_db: Session) -> None:
        with _run_with(bare_db, ["CCI: boom"]):
            with pytest.raises(SystemExit):
                scraper_entrypoint.main()
        run = bare_db.execute(select(ScrapeRun).order_by(ScrapeRun.id.desc())).scalars().first()
        assert run is not None
        assert run.complexes_failed == 1
        assert run.finished_at is not None

    def test_a_long_failure_list_is_truncated_in_the_message(self, bare_db: Session) -> None:
        with _run_with(bare_db, [f"venue {i}: boom" for i in range(25)]) as notify:
            with pytest.raises(SystemExit):
                scraper_entrypoint.main()
        message = notify.call_args.args[0]
        assert "and 15 more" in message
