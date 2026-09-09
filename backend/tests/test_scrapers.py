import re
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest

from app.entities import CinemaCompany, CinemaComplex, Movie, Screening
from app.scrape import ComplexScrapeResult
from app.scrapers.base import MAX_COMPLEX_ATTEMPTS, Scraper
from app.scrapers.multicines import _title_to_slug

# Replicate the sanitizer logic from SupercinesScraper._scrape_complex_page
# so we can test it in isolation without spinning up Playwright.
_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _sanitize(content: str) -> str:
    return _UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), content).replace("\\n", "").replace("\\", "")


def _split_format_language(tecnology: str) -> tuple[str, str]:
    parts = tecnology.rsplit(" ", 1)
    return (parts[0], parts[1]) if len(parts) > 1 else (tecnology, "")


class TestTitleToSlug:
    def test_basic_ascii(self) -> None:
        assert _title_to_slug("Toy Story 5") == "toy-story-5"

    def test_removes_accents(self) -> None:
        assert _title_to_slug("El Día De La Revelación") == "el-dia-de-la-revelacion"

    def test_collapses_punctuation_to_hyphen(self) -> None:
        assert _title_to_slug("Spider-Man: Un Nuevo Día") == "spider-man-un-nuevo-dia"

    def test_no_leading_or_trailing_hyphens(self) -> None:
        slug = _title_to_slug("Test Title")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_lowercases_output(self) -> None:
        assert _title_to_slug("BLEACH") == "bleach"


class TestSupercinesSanitizer:
    def test_decodes_ampersand_escape(self) -> None:
        assert _sanitize("Minions \\u0026 Monstruos") == "Minions & Monstruos"

    def test_decodes_multiple_escapes(self) -> None:
        assert _sanitize("A \\u0026 B \\u003e C") == "A & B > C"

    def test_removes_escaped_newlines(self) -> None:
        assert "\\n" not in _sanitize("line1\\nline2")

    def test_preserves_plain_text(self) -> None:
        assert _sanitize("Toy Story 5") == "Toy Story 5"


class TestSupercinasFormatLanguageSplit:
    @pytest.mark.parametrize(
        "tecnology,expected_format,expected_language",
        [
            ("2D Doblada", "2D", "Doblada"),
            ("2D Subtitulada", "2D", "Subtitulada"),
            ("3D Doblada", "3D", "Doblada"),
            ("IMAX 3D Doblada", "IMAX 3D", "Doblada"),
            ("2D", "2D", ""),
        ],
    )
    def test_split(self, tecnology: str, expected_format: str, expected_language: str) -> None:
        fmt, lang = _split_format_language(tecnology)
        assert fmt == expected_format
        assert lang == expected_language


class _FakePage:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FakeBrowser:
    def __init__(self) -> None:
        self.pages: list[_FakePage] = []

    def new_page(self) -> _FakePage:
        page = _FakePage()
        self.pages.append(page)
        return page


class _FlakyScraper(Scraper):
    company_name = "Flaky"

    def __init__(self, company: CinemaCompany, failures: int) -> None:
        super().__init__(company)
        self.failures = failures
        self.calls = 0

    def _scrape_complex_page(self, page: Any, complex: CinemaComplex) -> list[Screening]:
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectionError("Connection reset by peer")
        return [
            Screening(
                datetime=datetime(2026, 9, 9, 20, 0),
                format="2D",
                language="Doblada",
                complex=complex,
                movie=Movie(title="Some film"),
            )
        ]


@pytest.fixture
def flaky_complex() -> CinemaComplex:
    company = CinemaCompany(name="Flaky", base_url="https://example.com")
    return CinemaComplex(name="Somewhere", city="Quito", url_part="/x", company=company)


class TestComplexRetry:
    """A reset connection cost 7 of 25 Supercines venues their listings in one run,
    so a transient failure gets a few attempts before the venue is given up on."""

    def _run(self, failures: int, complex: CinemaComplex) -> tuple[ComplexScrapeResult, _FlakyScraper]:
        scraper = _FlakyScraper(complex.company, failures)
        browser = _FakeBrowser()
        with patch("app.scrapers.base.time.sleep") as sleep:
            result = scraper._scrape_one_complex(browser, complex)  # type: ignore[arg-type]
        scraper.slept = sleep.call_count  # type: ignore[attr-defined]
        scraper.browser = browser  # type: ignore[attr-defined]
        return result, scraper

    def test_a_first_attempt_success_does_not_retry_or_wait(self, flaky_complex: CinemaComplex) -> None:
        result, scraper = self._run(0, flaky_complex)
        assert result.error is None and len(result.screenings) == 1
        assert scraper.calls == 1
        assert scraper.slept == 0  # type: ignore[attr-defined]

    def test_recovers_from_a_transient_failure(self, flaky_complex: CinemaComplex) -> None:
        result, scraper = self._run(1, flaky_complex)
        assert result.error is None and len(result.screenings) == 1
        assert scraper.calls == 2

    def test_recovers_on_the_last_allowed_attempt(self, flaky_complex: CinemaComplex) -> None:
        result, scraper = self._run(MAX_COMPLEX_ATTEMPTS - 1, flaky_complex)
        assert result.error is None
        assert scraper.calls == MAX_COMPLEX_ATTEMPTS

    def test_gives_up_and_reports_after_the_last_attempt(self, flaky_complex: CinemaComplex) -> None:
        result, scraper = self._run(MAX_COMPLEX_ATTEMPTS, flaky_complex)
        assert result.error == "Connection reset by peer"
        assert result.screenings == []
        assert scraper.calls == MAX_COMPLEX_ATTEMPTS
        # No pause after the final attempt.
        assert scraper.slept == MAX_COMPLEX_ATTEMPTS - 1  # type: ignore[attr-defined]

    def test_every_attempt_closes_its_page(self, flaky_complex: CinemaComplex) -> None:
        _, scraper = self._run(MAX_COMPLEX_ATTEMPTS, flaky_complex)
        pages = scraper.browser.pages  # type: ignore[attr-defined]
        assert len(pages) == MAX_COMPLEX_ATTEMPTS
        assert all(p.closed for p in pages)


class _BrowserlessScraper(Scraper):
    company_name = "Browserless"
    needs_browser = False

    def __init__(self, company: CinemaCompany) -> None:
        super().__init__(company)
        self.pages_received: list[Any] = []

    def _scrape_complex_page(self, page: Any, complex: CinemaComplex) -> list[Screening]:
        self.pages_received.append(page)
        return [
            Screening(
                datetime=datetime(2026, 9, 9, 20, 0),
                format="2D",
                language="Doblada",
                complex=complex,
                movie=Movie(title="Some film"),
            )
        ]


class TestBrowserlessScrapers:
    """Chains whose listings are already in the served HTML must not pay for Chromium."""

    def test_never_launches_a_browser(self, flaky_complex: CinemaComplex) -> None:
        scraper = _BrowserlessScraper(flaky_complex.company)
        with patch("app.scrapers.base.sync_playwright") as playwright:
            results = list(scraper.run_scrape([flaky_complex]))
        playwright.assert_not_called()
        assert len(results) == 1 and results[0].error is None

    def test_receives_no_page(self, flaky_complex: CinemaComplex) -> None:
        scraper = _BrowserlessScraper(flaky_complex.company)
        list(scraper.run_scrape([flaky_complex]))
        assert scraper.pages_received == [None]

    def test_browser_backed_scrapers_still_launch_one(self, flaky_complex: CinemaComplex) -> None:
        assert _FlakyScraper.needs_browser is True
