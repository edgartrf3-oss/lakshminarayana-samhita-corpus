from __future__ import annotations
import re
from dataclasses import dataclass
from .numerals import devanagari_to_ascii

# The Wikisource transcription contains many damaged verse delimiters:
# missing opening/closing dandas, ASCII pipes in place of dandas, stray
# punctuation inside the marker, etc. These patterns are used only to detect
# a verse boundary. The raw marker is always preserved and uncertain printed
# numbers are never guessed.
DANDA_RUN = r"(?:॥|(?:।\s*){1,4})"
NUMERIC_BODY = r"(?=[0-9०-९.\s]*[0-9०-९])[0-9०-९.\s]+?"
MARKER_RE = re.compile(
    rf"(?P<prefix>{DANDA_RUN})\s*(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{DANDA_RUN})\s*$"
)
# A very small number of source lines contain an explicit empty number slot,
# e.g. "... ।।  ।।". Requiring two clear double-danda groups separated by
# whitespace makes this conservative: we treat it as a boundary but do not
# manufacture the missing printed number.
EMPTY_MARKER_RE = re.compile(
    r"(?P<prefix>॥|।।)\s+(?P<body>)(?P<suffix>॥|।।)\s*$"
)
PREFIX_ONLY_RE = re.compile(
    rf"(?P<prefix>{DANDA_RUN})\s*(?P<body>{NUMERIC_BODY})\s*[.!]?\s*$"
)
SUFFIX_ONLY_RE = re.compile(
    rf"(?<![0-9०-९.])(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{DANDA_RUN})\s*[.!|]?\s*$"
)
ASCII_DANDA_RUN = r"(?:[।॥|lI]\s*){1,4}"
MIXED_DELIMITER_RE = re.compile(
    rf"(?P<prefix>{ASCII_DANDA_RUN})\s*(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{ASCII_DANDA_RUN})\s*[.!|]?\s*$"
)
NOISY_BODY_RE = re.compile(
    rf"(?P<prefix>{DANDA_RUN})\s*(?P<body>[^।॥\n]{{0,15}}[0-9०-९][^।॥\n]{{0,10}}?)\s*(?P<suffix>{DANDA_RUN})\s*[.!|]?\s*$"
)
MIXED_NOISY_BODY_RE = re.compile(
    rf"(?P<prefix>{ASCII_DANDA_RUN})\s*(?P<body>[^।॥|\n]{{0,15}}[0-9०-९][^।॥|\n]{{0,10}}?)\s*(?P<suffix>{ASCII_DANDA_RUN})\s*[.!|]?\s*$"
)

@dataclass(frozen=True)
class VerseMarker:
    raw: str
    normalized_body: str
    observed_verse_number: int | None
    full_reference_hint: tuple[int, ...]
    anomaly_flags: tuple[str, ...] = ()

def _danda_units(run: str | None) -> int:
    if not run:
        return 0
    return 2 if "॥" in run else run.count("।")

def parse_marker_body(body: str):
    compact = re.sub(r"\s+", "", devanagari_to_ascii(body)).strip(".")
    if not re.fullmatch(r"[0-9.]+", compact):
        raise ValueError(f"unparseable verse marker: {body!r}")
    parts = tuple(int(p) for p in compact.split(".") if p)
    if not parts:
        raise ValueError(f"unparseable verse marker: {body!r}")
    return parts[-1], parts

def _make_marker(line: str, m: re.Match[str], flags: list[str]):
    body = m.group("body")
    if "missing_marker_number" in flags:
        verse_no, parts, normalized = None, (), ""
    else:
        try:
            verse_no, parts = parse_marker_body(body)
            normalized = ".".join(map(str, parts))
        except ValueError:
            verse_no, parts, normalized = None, (), ""
            flags.append("malformed_marker_body")
    prefix = m.groupdict().get("prefix")
    suffix = m.groupdict().get("suffix")
    if prefix and _danda_units(prefix) < 2:
        flags.append("malformed_marker_delimiter")
    if suffix and _danda_units(suffix) < 2:
        flags.append("malformed_marker_delimiter")
    return line[:m.start()].rstrip(), VerseMarker(
        m.group(0), normalized, verse_no, parts, tuple(dict.fromkeys(flags))
    )

def split_trailing_marker(line: str):
    m = MARKER_RE.search(line)
    if m:
        return _make_marker(line, m, [])

    m = EMPTY_MARKER_RE.search(line)
    if m:
        return _make_marker(line, m, ["missing_marker_number"])

    # One-sided delimiters are common OCR/transcription damage. A numeric
    # body plus a surviving danda-run at the line end is still a strong verse
    # boundary signal; we do not infer the missing punctuation.
    m = PREFIX_ONLY_RE.search(line)
    if m:
        return _make_marker(line, m, ["one_sided_marker_delimiter"])
    m = SUFFIX_ONLY_RE.search(line)
    if m:
        return _make_marker(line, m, ["one_sided_marker_delimiter"])

    # Some pages use ASCII |/l/I glyphs where dandas should be. Preserve them
    # verbatim and flag the nonstandard delimiter.
    m = MIXED_DELIMITER_RE.search(line)
    if m:
        return _make_marker(line, m, ["nonstandard_marker_delimiter"])

    # When the marker is clearly bracketed but its body contains stray OCR
    # characters, use it only as a boundary. The observed number remains
    # unknown rather than being silently corrected.
    m = NOISY_BODY_RE.search(line)
    if m:
        return _make_marker(line, m, ["malformed_marker_body"])
    m = MIXED_NOISY_BODY_RE.search(line)
    if m:
        return _make_marker(
            line, m, ["nonstandard_marker_delimiter", "malformed_marker_body"]
        )
    return line, None
