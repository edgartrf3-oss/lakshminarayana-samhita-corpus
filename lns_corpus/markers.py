from __future__ import annotations
import re
from dataclasses import dataclass
from .numerals import devanagari_to_ascii

# Wikisource contains many damaged verse delimiters such as "।।५२।" or
# "। ३६।।".  Accept 1–4 dandas on either side so the boundary is not lost,
# but retain an explicit quality flag; the source string is never emended.
DANDA_RUN = r"(?:॥|(?:।\s*){1,4})"
MARKER_RE = re.compile(rf"(?P<prefix>{DANDA_RUN})\s*(?P<body>[0-9०-९.\s]+?)\s*(?P<suffix>{DANDA_RUN})\s*$")

@dataclass(frozen=True)
class VerseMarker:
    raw: str
    normalized_body: str
    observed_verse_number: int
    full_reference_hint: tuple[int, ...]
    malformed_delimiter: bool = False

def _danda_units(run: str) -> int:
    return 2 if "॥" in run else run.count("।")

def parse_marker_body(body: str):
    compact = re.sub(r"\s+", "", devanagari_to_ascii(body)).strip(".")
    parts = tuple(int(p) for p in compact.split(".") if p)
    if not parts:
        raise ValueError(f"unparseable verse marker: {body!r}")
    return parts[-1], parts

def split_trailing_marker(line: str):
    m = MARKER_RE.search(line)
    if not m:
        return line, None
    try:
        verse_no, parts = parse_marker_body(m.group("body"))
    except ValueError:
        return line, None
    malformed = _danda_units(m.group("prefix")) < 2 or _danda_units(m.group("suffix")) < 2
    return line[:m.start()].rstrip(), VerseMarker(
        m.group(0),
        ".".join(map(str, parts)),
        verse_no,
        parts,
        malformed,
    )
