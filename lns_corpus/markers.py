from __future__ import annotations
import re
from dataclasses import dataclass
from .numerals import devanagari_to_ascii
DANDA_RUN = r"(?:॥|(?:।\s*){2,4})"
MARKER_RE = re.compile(rf"(?P<prefix>{DANDA_RUN})\s*(?P<body>[0-9०-९.\s]+?)\s*(?P<suffix>{DANDA_RUN})\s*$")
@dataclass(frozen=True)
class VerseMarker:
    raw: str
    normalized_body: str
    observed_verse_number: int
    full_reference_hint: tuple[int, ...]
def parse_marker_body(body: str):
    compact = re.sub(r"\s+", "", devanagari_to_ascii(body)).strip(".")
    parts = tuple(int(p) for p in compact.split(".") if p)
    if not parts: raise ValueError(f"unparseable verse marker: {body!r}")
    return parts[-1], parts
def split_trailing_marker(line: str):
    m = MARKER_RE.search(line)
    if not m: return line, None
    try:
        verse_no, parts = parse_marker_body(m.group("body"))
    except ValueError:
        return line, None
    return line[:m.start()].rstrip(), VerseMarker(m.group(0), ".".join(map(str, parts)), verse_no, parts)
