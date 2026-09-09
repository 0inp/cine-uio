from typing import Any
from unittest.mock import patch

import pytest

from app.scrapers.fetching import ATTEMPTS_PER_URL, fetch_json_all


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload


class TestFetchJsonAll:
    def test_no_urls_makes_no_requests(self) -> None:
        with patch("app.scrapers.fetching.requests.get") as get:
            assert fetch_json_all([]) == []
        get.assert_not_called()

    def test_preserves_input_order(self) -> None:
        # Results are zipped back onto what was asked for, so order is load-bearing.
        def by_url(url: str, **_: Any) -> FakeResponse:
            return FakeResponse({"n": int(url[-1])})

        with patch("app.scrapers.fetching.requests.get", side_effect=by_url):
            payloads = fetch_json_all([f"https://x/{i}" for i in range(9)])
        assert [p["n"] for p in payloads] == list(range(9))

    def test_a_non_200_is_absence_not_failure(self) -> None:
        # The APIs answer 200-with-nothing for a day a film is not showing.
        with patch("app.scrapers.fetching.requests.get", return_value=FakeResponse(None, status_code=404)):
            assert fetch_json_all(["https://x/1"]) == [None]

    def test_retries_a_transient_error(self) -> None:
        attempts = {"n": 0}

        def flaky(url: str, **_: Any) -> FakeResponse:
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise ConnectionError("Connection reset by peer")
            return FakeResponse({"ok": True})

        with patch("app.scrapers.fetching.requests.get", side_effect=flaky):
            assert fetch_json_all(["https://x/1"]) == [{"ok": True}]
        assert attempts["n"] == 2

    def test_propagates_once_the_retries_run_out(self) -> None:
        # Rather than publish a venue with a hole in it, fail it and let the
        # complex-level retry decide.
        with patch(
            "app.scrapers.fetching.requests.get",
            side_effect=ConnectionError("Connection reset by peer"),
        ) as get:
            with pytest.raises(ConnectionError):
                fetch_json_all(["https://x/1"])
        assert get.call_count == ATTEMPTS_PER_URL

    def test_passes_headers_through(self) -> None:
        with patch("app.scrapers.fetching.requests.get", return_value=FakeResponse({})) as get:
            fetch_json_all(["https://x/1"], headers={"Authorization": "Bearer t"})
        assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer t"}

    def test_uses_several_workers_but_stays_bounded(self) -> None:
        with patch("app.scrapers.fetching.ThreadPoolExecutor") as pool:
            pool.return_value.__enter__.return_value.map.return_value = iter([])
            fetch_json_all([f"https://x/{i}" for i in range(100)])
        assert pool.call_args.kwargs["max_workers"] <= 8

    def test_never_spawns_more_workers_than_urls(self) -> None:
        with patch("app.scrapers.fetching.ThreadPoolExecutor") as pool:
            pool.return_value.__enter__.return_value.map.return_value = iter([])
            fetch_json_all(["https://x/1", "https://x/2"])
        assert pool.call_args.kwargs["max_workers"] == 2
