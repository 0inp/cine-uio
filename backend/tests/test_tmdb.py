from typing import Any
from unittest.mock import patch

import pytest

from app.tmdb import _best_match, _certification, _title_variants, search_movie


class FakeResponse:
    def __init__(self, payload: dict[str, Any], ok: bool = True, status_code: int = 200) -> None:
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload


def _release_dates(**by_region: str) -> dict[str, Any]:
    """Build a TMDB /release_dates payload: region -> certification."""
    return {
        "results": [
            {"iso_3166_1": region, "release_dates": [{"certification": cert}]} for region, cert in by_region.items()
        ]
    }


@pytest.fixture
def token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TMDB_READ_ACCESS_TOKEN", "fake-token")


class TestTitleVariants:
    def test_original_is_always_first(self) -> None:
        variants = _title_variants("Toy Story 5")
        assert variants[0] == "Toy Story 5"

    def test_no_conjunction_returns_only_original(self) -> None:
        assert _title_variants("Toy Story 5") == ["Toy Story 5"]

    def test_y_replaced_with_ampersand(self) -> None:
        variants = _title_variants("Minions Y Monstruos")
        assert variants == ["Minions Y Monstruos", "Minions & Monstruos"]

    def test_ampersand_replaced_with_y(self) -> None:
        variants = _title_variants("Minions & Monstruos")
        assert variants == ["Minions & Monstruos", "Minions Y Monstruos"]

    def test_y_not_matched_as_substring_of_word(self) -> None:
        # "Toy" contains "y" but " Y " (spaced) should not match inside a word
        assert _title_variants("Toy Story") == ["Toy Story"]

    def test_multiple_y_conjunctions_all_replaced(self) -> None:
        variants = _title_variants("A Y B Y C")
        assert "A & B & C" in variants


class TestCertification:
    def test_prefers_ecuador_over_us_and_gb(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse(_release_dates(US="PG-13", EC="12", GB="15"))):
            assert _certification(1) == "12"

    def test_falls_back_to_us_when_no_ecuador(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse(_release_dates(GB="15", US="PG-13", FR="12"))):
            assert _certification(1) == "PG-13"

    def test_falls_back_to_gb_when_no_ecuador_or_us(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse(_release_dates(FR="12", GB="15"))):
            assert _certification(1) == "15"

    def test_falls_back_to_any_region_when_no_priority_region_present(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse(_release_dates(FR="12"))):
            assert _certification(1) == "12"

    def test_skips_blank_certifications_within_a_region(self) -> None:
        payload = {
            "results": [
                {
                    "iso_3166_1": "EC",
                    "release_dates": [{"certification": "  "}, {"certification": "14"}],
                }
            ]
        }
        with patch("app.tmdb.requests.get", return_value=FakeResponse(payload)):
            assert _certification(1) == "14"

    def test_returns_none_when_no_region_has_a_certification(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse({"results": []})):
            assert _certification(1) is None

    def test_returns_none_on_http_error(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse({}, ok=False, status_code=404)):
            assert _certification(1) is None


class TestBestMatch:
    def test_returns_top_result_when_it_is_popular_enough(self) -> None:
        payload = {"results": [{"id": 862, "popularity": 150.0}, {"id": 999, "popularity": 900.0}]}
        with patch("app.tmdb.requests.get", return_value=FakeResponse(payload)) as mock_get:
            assert _best_match("Toy Story 5") == 862
        # A confident top hit must not cost an alternative-titles round trip.
        assert mock_get.call_count == 1

    def test_promotes_candidate_whose_alternative_title_matches_exactly(self) -> None:
        # Real case: TMDB ranks the obscure "Codigo de venganza" (2002) above "El motin"
        # (2026), which is actually billed as "Codigo: Venganza" in Ecuador.
        search = {"results": [{"id": 188834, "popularity": 1.2}, {"id": 1288445, "popularity": 394.6}]}
        responses = [
            FakeResponse(search),
            FakeResponse({"titles": [{"title": "Hitters"}]}),  # 188834 -> no match
            FakeResponse({"titles": [{"title": "Código: Venganza"}]}),  # 1288445 -> exact match
        ]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert _best_match("Código: Venganza") == 1288445

    def test_alternative_title_match_ignores_case_accents_and_punctuation(self) -> None:
        search = {"results": [{"id": 1, "popularity": 0.5}]}
        responses = [FakeResponse(search), FakeResponse({"titles": [{"title": "codigo venganza"}]})]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert _best_match("Código: Venganza") == 1

    def test_promotes_dramatically_more_popular_recent_release(self) -> None:
        search = {
            "results": [
                {"id": 1, "popularity": 1.2, "release_date": "2002-12-01"},
                {"id": 2, "popularity": 394.6, "release_date": "2026-08-01"},
            ]
        }
        responses = [FakeResponse(search), FakeResponse({"titles": []}), FakeResponse({"titles": []})]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert _best_match("Código: Venganza") == 2

    def test_keeps_top_hit_when_nothing_better_is_found(self) -> None:
        # Never reject: an obscure-but-correct match beats losing the movie entirely.
        # Real case: "La Ultima Entrega" only matches obscure films in TMDB.
        search = {
            "results": [
                {"id": 1, "popularity": 1.3, "release_date": "1993-01-01"},
                {"id": 2, "popularity": 0.7, "release_date": "2001-01-01"},
            ]
        }
        responses = [FakeResponse(search), FakeResponse({"titles": []}), FakeResponse({"titles": []})]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert _best_match("La Última Entrega") == 1

    def test_does_not_promote_an_old_movie_however_popular(self) -> None:
        # Classic re-releases (Terminator 2, Madoka) must keep matching themselves.
        search = {
            "results": [
                {"id": 1, "popularity": 1.0, "release_date": "2026-01-01"},
                {"id": 2, "popularity": 900.0, "release_date": "1994-01-01"},
            ]
        }
        responses = [FakeResponse(search), FakeResponse({"titles": []}), FakeResponse({"titles": []})]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert _best_match("Some 2026 Film") == 1

    def test_returns_none_when_no_results(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse({"results": []})):
            assert _best_match("Mexico Vs Ecuador") is None

    def test_returns_none_on_http_error(self) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse({}, ok=False, status_code=401)):
            assert _best_match("Toy Story 5") is None

    def test_issues_exactly_one_request(self) -> None:
        # Regression: the old implementation retried the same query in es-LA, es-ES and
        # en-US, tripling the cost of every miss without ever finding anything extra.
        with patch("app.tmdb.requests.get", return_value=FakeResponse({"results": []})) as mock_get:
            _best_match("Mexico Vs Ecuador")
        assert mock_get.call_count == 1


# Popular enough that _best_match trusts TMDB's own ranking without extra requests.
POPULAR_HIT = {"id": 862, "popularity": 150.0, "release_date": "2026-06-20"}

DETAIL = {
    "title": "Toy Story 5",
    "poster_path": "/poster.jpg",
    "overview": "Woody and Buzz are back.",
    "runtime": 100,
    "release_date": "2026-06-20",
}


def _responses(*, search: dict[str, Any], detail: dict[str, Any], cert: dict[str, Any]) -> list[FakeResponse]:
    return [FakeResponse(search), FakeResponse(detail), FakeResponse(cert)]


class TestSearchMovie:
    def test_returns_none_without_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TMDB_READ_ACCESS_TOKEN", raising=False)
        with patch("app.tmdb.requests.get") as mock_get:
            assert search_movie("Toy Story 5") is None
        mock_get.assert_not_called()

    def test_maps_every_detail_field(self, token: None) -> None:
        responses = _responses(search={"results": [POPULAR_HIT]}, detail=DETAIL, cert=_release_dates(EC="12"))
        with patch("app.tmdb.requests.get", side_effect=responses):
            result = search_movie("Toy Story 5")
        assert result is not None
        assert result.tmdb_id == 862
        assert result.tmdb_title == "Toy Story 5"
        assert result.poster_path == "/poster.jpg"
        assert result.overview == "Woody and Buzz are back."
        assert result.runtime == 100
        assert result.certification == "12"
        assert result.release_date == "2026-06-20"

    def test_returns_none_when_nothing_matches(self, token: None) -> None:
        with patch("app.tmdb.requests.get", return_value=FakeResponse({"results": []})):
            assert search_movie("Mexico Vs Ecuador") is None

    def test_returns_none_when_detail_fetch_fails(self, token: None) -> None:
        responses = [FakeResponse({"results": [POPULAR_HIT]}), FakeResponse({}, ok=False, status_code=500)]
        with patch("app.tmdb.requests.get", side_effect=responses):
            assert search_movie("Toy Story 5") is None

    def test_retries_with_ampersand_variant_when_original_finds_nothing(self, token: None) -> None:
        responses = [
            FakeResponse({"results": []}),  # "Minions Y Monstruos" -> nothing
            FakeResponse({"results": [{"id": 1315772, "popularity": 140.0}]}),  # "Minions & Monstruos" -> hit
            FakeResponse({**DETAIL, "title": "Minions & Monstruos"}),
            FakeResponse(_release_dates(EC="A")),
        ]
        with patch("app.tmdb.requests.get", side_effect=responses):
            result = search_movie("Minions Y Monstruos")
        assert result is not None
        assert result.tmdb_id == 1315772

    def test_falls_back_to_scraped_title_when_detail_has_no_title(self, token: None) -> None:
        detail: dict[str, Any] = {**DETAIL, "title": ""}
        responses = _responses(search={"results": [POPULAR_HIT]}, detail=detail, cert={"results": []})
        with patch("app.tmdb.requests.get", side_effect=responses):
            result = search_movie("Raw Scraped Title")
        assert result is not None
        assert result.tmdb_title == "Raw Scraped Title"

    def test_zero_runtime_is_treated_as_missing(self, token: None) -> None:
        detail: dict[str, Any] = {**DETAIL, "runtime": 0}
        responses = _responses(search={"results": [POPULAR_HIT]}, detail=detail, cert={"results": []})
        with patch("app.tmdb.requests.get", side_effect=responses):
            result = search_movie("Toy Story 5")
        assert result is not None
        assert result.runtime is None

    def test_missing_optional_fields_become_none(self, token: None) -> None:
        responses = _responses(search={"results": [POPULAR_HIT]}, detail={"title": "X"}, cert={"results": []})
        with patch("app.tmdb.requests.get", side_effect=responses):
            result = search_movie("X")
        assert result is not None
        assert result.poster_path is None
        assert result.overview is None
        assert result.runtime is None
        assert result.release_date is None
