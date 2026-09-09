import os
import re
import time
import unicodedata
from dataclasses import dataclass

import requests

from app.logging import logger

_BASE_URL = "https://api.themoviedb.org/3"
_CERT_REGION_PRIORITY = ("EC", "US", "GB")
# Search and detail use different language codes on purpose: es-LA is what TMDB's
# search ranking responds to, while es-419 is the proper locale for translated content.
_SEARCH_LANGUAGE = "es-LA"
_DETAIL_LANGUAGE = "es-419"
_REQUEST_PAUSE_SECONDS = 0.05
# A top hit below this popularity is treated as a weak match worth double-checking.
_LOW_POPULARITY = 5.0
# ...and one above this, released recently, is treated as a likely current release.
_DOMINANT_POPULARITY = 50.0
_RECENT_YEAR = "2025"
_MAX_CANDIDATES = 5


@dataclass
class TMDBMovie:
    tmdb_id: int
    tmdb_title: str
    poster_path: str | None
    overview: str | None
    runtime: int | None
    certification: str | None
    release_date: str | None


def _headers() -> dict[str, str]:
    token = os.environ.get("TMDB_READ_ACCESS_TOKEN", "")
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _optional_str(detail: dict[str, object], key: str) -> str | None:
    value = detail.get(key)
    return str(value) if value else None


def _certification(movie_id: int) -> str | None:
    """Return the age rating, preferring Ecuador, then the US, then the UK."""
    resp = requests.get(f"{_BASE_URL}/movie/{movie_id}/release_dates", headers=_headers(), timeout=10)
    if not resp.ok:
        return None
    by_region: dict[str, str] = {}
    for entry in resp.json().get("results", []):
        region: str = entry.get("iso_3166_1", "")
        for rd in entry.get("release_dates", []):
            cert: str = rd.get("certification", "").strip()
            if cert:
                by_region[region] = cert
                break
    for region in _CERT_REGION_PRIORITY:
        if region in by_region:
            return by_region[region]
    return next(iter(by_region.values()), None)


def _title_variants(title: str) -> list[str]:
    """Return a list of query candidates to try when the original title fails.

    Cinemas sometimes write the Spanish conjunction "Y" where TMDB stores "&"
    (and vice versa), so we swap them as a first fallback.
    """
    variants = [title]
    if " Y " in title:
        variants.append(title.replace(" Y ", " & "))
    elif " & " in title:
        variants.append(title.replace(" & ", " Y "))
    return variants


def _normalize_title(title: str) -> str:
    """Casefold, strip accents and punctuation so titles compare on words alone."""
    decomposed = unicodedata.normalize("NFKD", title.lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", stripped).split())


def _has_exact_alternative_title(movie_id: int, query: str) -> bool:
    """True if TMDB lists `query` among the movie's registered release titles.

    Cinemas advertise the local release title, which TMDB often stores only as an
    alternative title — "El motin" is billed as "Codigo: Venganza" in Ecuador. An exact
    match here is a far stronger signal than similarity against the display title, which
    routinely differs completely from the local one.
    """
    resp = requests.get(f"{_BASE_URL}/movie/{movie_id}/alternative_titles", headers=_headers(), timeout=10)
    if not resp.ok:
        return False
    wanted = _normalize_title(query)
    return any(_normalize_title(alt.get("title", "")) == wanted for alt in resp.json().get("titles", []))


def _best_match(query: str) -> int | None:
    """Return the best TMDB movie ID for a query, or None if the search found nothing.

    TMDB ranks by textual relevance, which for a *current* cartelera sometimes floats an
    obscure old film above the blockbuster actually showing. We only second-guess that
    ranking when the top hit is unpopular enough to be suspect, and we never reject a
    match outright: worst case we keep TMDB's own pick.
    """
    params: dict[str, str | int] = {"query": query, "language": _SEARCH_LANGUAGE, "page": 1}
    resp = requests.get(f"{_BASE_URL}/search/movie", headers=_headers(), params=params, timeout=10)
    if not resp.ok:
        logger.error(f"TMDB search error for '{query}': {resp.status_code}")
        return None

    results: list[dict[str, object]] = resp.json().get("results", [])[:_MAX_CANDIDATES]
    candidates: list[tuple[int, dict[str, object]]] = []
    for result in results:
        result_id = result.get("id")
        if isinstance(result_id, int):
            candidates.append((result_id, result))
    if not candidates:
        return None

    top_id, top = candidates[0]
    if _popularity(top) >= _LOW_POPULARITY:
        return top_id

    # Weak top hit: prefer any candidate whose local release title matches exactly.
    for candidate_id, _ in candidates:
        if _has_exact_alternative_title(candidate_id, query):
            if candidate_id != top_id:
                logger.info(f"TMDB: '{query}' promoted over the top hit by an exact alternative title")
            return candidate_id

    # Otherwise fall back to a dramatically more popular recent release, if there is one.
    hot = [
        (cid, c) for cid, c in candidates if _release_year(c) >= _RECENT_YEAR and _popularity(c) >= _DOMINANT_POPULARITY
    ]
    if hot:
        best_id, best = max(hot, key=lambda pair: _popularity(pair[1]))
        logger.info(
            f"TMDB: '{query}' promoted over the top hit on popularity "
            f"({_popularity(top):.1f} -> {_popularity(best):.0f})"
        )
        return best_id

    return top_id


def _popularity(result: dict[str, object]) -> float:
    value = result.get("popularity")
    return float(value) if isinstance(value, (int, float)) else 0.0


def _release_year(result: dict[str, object]) -> str:
    value = result.get("release_date")
    return str(value)[:4] if value else ""


def _fetch_detail(movie_id: int) -> dict[str, object] | None:
    resp = requests.get(
        f"{_BASE_URL}/movie/{movie_id}",
        headers=_headers(),
        params={"language": _DETAIL_LANGUAGE},
        timeout=10,
    )
    if not resp.ok:
        logger.error(f"TMDB detail fetch error for id={movie_id}: {resp.status_code}")
        return None
    detail: dict[str, object] = resp.json()
    return detail


def search_movie(scraped_title: str) -> TMDBMovie | None:
    """Look up a scraped cinema title on TMDB.

    Returns None when the token is missing, the title matches nothing, or the
    detail fetch fails — in every case the caller leaves the movie unenriched.
    Details are fetched in Latin American Spanish, so overview and tmdb_title are
    Spanish *when TMDB has a translation* — it falls back to the original title
    otherwise, which is why some tmdb_titles come back in English.
    """
    if not os.environ.get("TMDB_READ_ACCESS_TOKEN", ""):
        logger.warning("TMDB_READ_ACCESS_TOKEN not set — skipping enrichment")
        return None

    movie_id: int | None = None
    matched_variant = scraped_title
    for candidate in _title_variants(scraped_title):
        movie_id = _best_match(candidate)
        if movie_id is not None:
            matched_variant = candidate
            break

    if movie_id is None:
        logger.info(f"TMDB: no result for '{scraped_title}'")
        return None

    if matched_variant != scraped_title:
        logger.info(f"TMDB: found '{scraped_title}' via variant '{matched_variant}'")

    detail = _fetch_detail(movie_id)
    if detail is None:
        return None

    raw_runtime = detail.get("runtime")
    certification = _certification(movie_id)

    time.sleep(_REQUEST_PAUSE_SECONDS)  # space out requests between movies

    return TMDBMovie(
        tmdb_id=movie_id,
        tmdb_title=_optional_str(detail, "title") or scraped_title,
        poster_path=_optional_str(detail, "poster_path"),
        overview=_optional_str(detail, "overview"),
        runtime=raw_runtime if isinstance(raw_runtime, int) and raw_runtime > 0 else None,
        certification=certification,
        release_date=_optional_str(detail, "release_date"),
    )
