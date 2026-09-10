import pytest

from app.screening_types import (
    AUDIO_DUBBED,
    AUDIO_SUBTITLED,
    DEFAULT_PROJECTION,
    parse_audio,
    parse_projection,
)


class TestParseProjection:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2D ESP", "2D"),
            ("4D ESP", "4D"),
            ("4D SUB", "4D"),
            ("2D", "2D"),
            ("3D SUB", "3D"),  # none in the catalogue today, but the parser must not care
        ],
    )
    def test_reads_the_format_out_of_the_raw_value(self, raw: str, expected: str) -> None:
        assert parse_projection(raw) == expected

    @pytest.mark.parametrize("raw", ["ESP", "SUB", "", "Doblada"])
    def test_defaults_to_2d_when_nothing_says_otherwise(self, raw: str) -> None:
        # Multicines' ICE and ScreenX rooms carry no marker; they are 2D projections
        # in an unusual room, and the room is the dimension we dropped.
        assert parse_projection(raw) == DEFAULT_PROJECTION

    def test_looks_through_several_fields_in_order(self) -> None:
        # The chains disagree about which field holds it.
        assert parse_projection("SALA 4D", "ESP") == "4D"
        assert parse_projection("", "2D ESP") == "2D"

    def test_the_first_field_that_says_something_wins(self) -> None:
        assert parse_projection("4D ESP", "2D") == "4D"

    def test_does_not_match_a_d_inside_a_word(self) -> None:
        assert parse_projection("SALA DBOX VIP") == DEFAULT_PROJECTION


class TestParseAudio:
    @pytest.mark.parametrize("raw", ["Doblada", "2D ESP", "4D ESP", "ESP", "doblado"])
    def test_recognises_dubbed(self, raw: str) -> None:
        assert parse_audio(raw) == AUDIO_DUBBED

    @pytest.mark.parametrize("raw", ["Subtitulada", "2D SUB", "SUB", "subtitulado"])
    def test_recognises_subtitled(self, raw: str) -> None:
        assert parse_audio(raw) == AUDIO_SUBTITLED

    def test_subtitled_wins_over_a_mention_of_spanish(self) -> None:
        # "Subtitulada en español" is not a dubbed showing.
        assert parse_audio("Subtitulada en español") == AUDIO_SUBTITLED

    @pytest.mark.parametrize("raw", ["", "SALA NORMAL", "PANTALLA GIGANTE MCX"])
    def test_says_nothing_rather_than_guessing(self, raw: str) -> None:
        assert parse_audio(raw) is None

    def test_looks_through_several_fields(self) -> None:
        assert parse_audio("SALA NORMAL", "Doblada") == AUDIO_DUBBED

    def test_ignores_a_substring_that_is_not_a_word(self) -> None:
        # "SUB" inside "SUBURBIO" must not read as subtitled.
        assert parse_audio("CINE SUBURBIO") is None
