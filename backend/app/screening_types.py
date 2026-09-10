"""Turning each chain's private vocabulary into two comparable dimensions.

The chains describe a showing in incompatible ways. Multicines puts the room type
in one field ("SALA NORMAL Y VIP") and the projection *and* audio in another
("2D ESP"); Supercines puts the projection in the first ("2D") and the audio in
the second ("Doblada"). Three concepts across two fields, filled differently.

Only two of those three survive here. The room type is Multicines-only and has no
Supercines equivalent, so it cannot be harmonised — and a reader comparing venues
is choosing a time and a language, not a seat class.
"""

import re

from app.logging import logger

DEFAULT_PROJECTION = "2D"

AUDIO_DUBBED = "dubbed"
AUDIO_SUBTITLED = "subtitled"

_PROJECTION_PATTERN = re.compile(r"\b(\d)\s*D\b", re.IGNORECASE)
_DUBBED_WORDS = ("doblada", "doblado", "esp", "español", "espanol")
_SUBTITLED_WORDS = ("subtitulada", "subtitulado", "sub", "vose", "vos")


def parse_projection(*sources: str) -> str:
    """Find the projection format in whichever field the chain hid it in.

    Defaults to 2D rather than to nothing: a showing with no explicit format is a
    normal screening, and the special rooms that carry no marker (ICE, ScreenX)
    are 2D projections in an unusual room, which is the dimension we dropped.
    """
    for source in sources:
        match = _PROJECTION_PATTERN.search(source or "")
        if match:
            return f"{match.group(1)}D".upper()
    return DEFAULT_PROJECTION


def parse_audio(*sources: str) -> str | None:
    """Dubbed or subtitled, or None when the chain did not say.

    Subtitled is tested first: "SUB" appears inside no dubbing word, while a naive
    "esp" search would match "Subtitulada en español".
    """
    for source in sources:
        words = re.findall(r"[a-záéíóúñ]+", (source or "").lower())
        if any(word in _SUBTITLED_WORDS for word in words):
            return AUDIO_SUBTITLED
        if any(word in _DUBBED_WORDS for word in words):
            return AUDIO_DUBBED

    logger.debug(f"no audio recognised in {sources!r}")
    return None
