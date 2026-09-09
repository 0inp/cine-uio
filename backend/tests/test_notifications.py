from unittest.mock import patch

import pytest

from app.notifications import WEBHOOK_ENV_VAR, notify


class FakeResponse:
    def __init__(self, ok: bool = True, status_code: int = 204) -> None:
        self.ok = ok
        self.status_code = status_code


@pytest.fixture
def webhook(monkeypatch: pytest.MonkeyPatch) -> str:
    url = "https://hooks.example.com/abc"
    monkeypatch.setenv(WEBHOOK_ENV_VAR, url)
    return url


class TestNotify:
    def test_does_nothing_without_a_configured_webhook(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(WEBHOOK_ENV_VAR, raising=False)
        with patch("app.notifications.requests.post") as post:
            assert notify("anything") is False
        post.assert_not_called()

    def test_ignores_a_blank_webhook(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(WEBHOOK_ENV_VAR, "   ")
        with patch("app.notifications.requests.post") as post:
            assert notify("anything") is False
        post.assert_not_called()

    def test_sends_both_slack_and_discord_keys(self, webhook: str) -> None:
        # Slack reads "text", Discord reads "content"; sending both means the same
        # payload works either way without knowing which is configured.
        with patch("app.notifications.requests.post", return_value=FakeResponse()) as post:
            assert notify("scrape failed") is True
        assert post.call_args.args[0] == webhook
        assert post.call_args.kwargs["json"] == {"text": "scrape failed", "content": "scrape failed"}

    def test_a_rejected_message_is_reported_not_raised(self, webhook: str) -> None:
        with patch("app.notifications.requests.post", return_value=FakeResponse(ok=False, status_code=400)):
            assert notify("scrape failed") is False

    def test_an_unreachable_webhook_never_raises(self, webhook: str) -> None:
        # A broken webhook must not turn a failed scrape into a crash, nor a
        # successful one into a failure.
        with patch("app.notifications.requests.post", side_effect=ConnectionError("down")):
            assert notify("scrape failed") is False

    def test_uses_a_timeout(self, webhook: str) -> None:
        with patch("app.notifications.requests.post", return_value=FakeResponse()) as post:
            notify("hi")
        assert post.call_args.kwargs["timeout"] > 0
