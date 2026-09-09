"""Concurrent HTTP fetching for scrapers whose APIs only answer one day at a time."""

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

from app.logging import logger

# Deliberately modest. These are someone else's servers, and a country-wide run
# already provoked "Connection reset by peer" at merely sequential load.
MAX_WORKERS = 6
ATTEMPTS_PER_URL = 2
REQUEST_TIMEOUT_SECONDS = 30


def _fetch_one(url: str, headers: dict[str, str]) -> Any:
    """Fetch and parse one URL, retrying once. Returns None for a non-200 answer.

    A refused request is data we do not have, so it raises and lets the complex-level
    retry deal with it; a 200 that simply has nothing is not a failure.
    """
    last_error: Exception | None = None
    for _ in range(ATTEMPTS_PER_URL):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        except Exception as e:  # noqa: BLE001 - re-raised below once attempts run out
            last_error = e
            continue
        if response.status_code != 200:
            return None
        return response.json()

    assert last_error is not None
    raise last_error


def fetch_json_all(urls: list[str], headers: dict[str, str] | None = None) -> list[Any]:
    """Fetch every URL concurrently and return the parsed payloads, in the input order.

    Order is preserved so callers can zip results back onto whatever they asked for.
    An entry is None when the server answered but had nothing; a failure that survives
    its retries propagates, so the complex is reported as failed rather than published
    with a hole in it.
    """
    if not urls:
        return []

    resolved_headers = headers or {}
    workers = min(MAX_WORKERS, len(urls))
    logger.debug(f"fetching {len(urls)} urls over {workers} workers")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda url: _fetch_one(url, resolved_headers), urls))
