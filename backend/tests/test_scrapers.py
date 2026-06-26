import re

import pytest

from app.scrapers.multicines import _title_to_slug

# Replicate the sanitizer logic from SupercinesScraper._scrape_complex_page
# so we can test it in isolation without spinning up Playwright.
_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def _sanitize(content: str) -> str:
    return _UNICODE_ESCAPE.sub(
        lambda m: chr(int(m.group(1), 16)), content
    ).replace("\\n", "").replace("\\", "")


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
