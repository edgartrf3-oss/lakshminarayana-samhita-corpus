from __future__ import annotations
import re
from dataclasses import dataclass
from .numerals import devanagari_to_ascii

# The Wikisource transcription contains many damaged verse delimiters:
# missing opening/closing dandas, ASCII pipes/exclamation marks in place of
# dandas, stray punctuation inside or after the marker, etc. These patterns
# are used only to detect a verse boundary. The raw marker is always preserved
# and uncertain printed numbers are never guessed.
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

# Final conservative fallback for residual typographical damage verified in
# the 2026-08-30 snapshot. It permits up to six delimiter glyphs, ASCII !/|
# substitutions, punctuation between delimiter glyphs, and harmless trailing
# punctuation/markup. A numeric body is still mandatory, so ordinary Sanskrit
# punctuation is not promoted to a verse marker.
FLEX_DELIM_UNIT = r"[।॥|lI!]"
FLEX_SEP = r"[\s.,'’\"“”\-)]*"
FLEX_DANDA_RUN = rf"(?:{FLEX_DELIM_UNIT}{FLEX_SEP}){{1,6}}"
TRAILING_MARKER_JUNK = r"[\s.,'’\"“”\-)\]\}]*"
FLEX_BOTH_RE = re.compile(
    rf"(?P<prefix>{FLEX_DANDA_RUN})\s*(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{FLEX_DANDA_RUN}){TRAILING_MARKER_JUNK}$"
)
FLEX_PREFIX_ONLY_RE = re.compile(
    rf"(?P<prefix>{FLEX_DANDA_RUN})\s*(?P<body>{NUMERIC_BODY}){TRAILING_MARKER_JUNK}$"
)
FLEX_SUFFIX_ONLY_RE = re.compile(
    rf"(?<![0-9०-९.])(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{FLEX_DANDA_RUN}){TRAILING_MARKER_JUNK}$"
)

# Strict inline detection is intentionally much narrower than trailing-marker
# detection. It is used only when a clearly bracketed numeric marker is
# followed on the same source line by Sanskrit text containing another danda;
# this recovers the known 1.553.18 -> 1.553.19 line-wrap error without treating
# editorial notes (e.g. the Skandapurana note in 2.32) as verse text.
INLINE_DOUBLE_DANDA = r"(?:॥|(?:।\s*){2,4})"
INLINE_MARKER_RE = re.compile(
    rf"(?P<prefix>{INLINE_DOUBLE_DANDA})\s*(?P<body>{NUMERIC_BODY})\s*(?P<suffix>{INLINE_DOUBLE_DANDA})"
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
    if "॥" in run:
        # A double danda is two units; other damaged glyphs, if present in a
        # flexible fallback, are quality noise rather than extra units.
        return 2
    return run.count("।")

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

def split_first_inline_marker(line: str):
    for m in INLINE_MARKER_RE.finditer(line):
        before = line[:m.start()].rstrip()
        after = line[m.end():].strip()
        if not before or not after:
            continue
        # Editorial references/links after a completed verse are not the next
        # verse. The same-line verse case has Sanskrit text and a danda in the
        # remainder.
        if "http://" in after or "https://" in after or "[" in after:
            continue
        if not re.search(r"[\u0900-\u097F]", after):
            continue
        if not re.search(r"[।॥]", after):
            continue
        lexical, marker = _make_marker(line, m, ["inline_marker_boundary"])
        return lexical, marker, after
    return line, None, None

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

    # Residual, manually audited delimiter damage. These fallbacks are last
    # because they are deliberately more permissive about punctuation, but
    # they still require an explicit numeric body.
    m = FLEX_BOTH_RE.search(line)
    if m:
        return _make_marker(
            line, m, ["nonstandard_marker_delimiter", "residual_marker_damage"]
        )
    m = FLEX_PREFIX_ONLY_RE.search(line)
    if m:
        return _make_marker(
            line, m,
            ["one_sided_marker_delimiter", "nonstandard_marker_delimiter", "residual_marker_damage"],
        )
    m = FLEX_SUFFIX_ONLY_RE.search(line)
    if m:
        return _make_marker(
            line, m,
            ["one_sided_marker_delimiter", "nonstandard_marker_delimiter", "residual_marker_damage"],
        )
    return line, None
