from __future__ import annotations

"""Snapshot-specific structural repairs for damaged Wikisource transcription.

These repairs are deliberately exact-string keyed.  The immutable raw snapshot
is never changed.  A repair affects only the derived segmentation layer and is
reported as an anomaly/provenance event.  If Wikisource later fixes the source
line, the exact match stops firing automatically and the repair can be retired.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ForcedBoundary:
    source_line: str
    marker_raw: str
    observed: int | None = None
    strip_suffix: str = ""
    lexical_override: str | None = None
    note: str = ""


# Lines where the verse boundary is philologically clear but the printed
# number/delimiter is missing or too damaged for a general parser rule.
FORCED_BOUNDARIES: dict[tuple[int, int], tuple[ForcedBoundary, ...]] = {
    (1, 25): (
        ForcedBoundary(
            "आरंभिता द्राक्सुखमुक्तिदात्री भक्तिस्तु माता बहुसम्मता मे ।।",
            "।।",
            None,
            "।।",
            note="verse 7 has no printed numeral; boundary is the end of the second metrical line before printed verse 8",
        ),
    ),
    (1, 67): (
        ForcedBoundary(
            "क्रयविक्रयकौटिल्यकर्ताऽर्षरोगवान्भवेत्।",
            "।",
            None,
            "।",
            note="printed verse 39 numeral is absent; following two-line unit is explicitly verse 40",
        ),
    ),
    (1, 89): (
        ForcedBoundary(
            "समाजे चात्र देवानां भविष्यति महोत्सवः ।।",
            "।।",
            None,
            "।।",
            note="printed verse 13 numeral is absent; next unit is explicitly verse 14",
        ),
    ),
    (1, 103): (
        ForcedBoundary(
            "हनिष्ये त्वां त्रिशूलेन नो चेन्मुञ्चसि मार्गकम् ३४",
            "३४",
            34,
            "३४",
            note="verse 34 numeral survives but both surrounding dandas are absent",
        ),
    ),
    (1, 116): (
        ForcedBoundary(
            "सेवकश्चापि निर्लेपो ब्रह्मशब्दार्थ उच्यते।।।",
            "।।।",
            None,
            "।।।",
            note="verse 24 numeral is absent; next verse is explicitly 25",
        ),
    ),
    (1, 388): (
        ForcedBoundary(
            "रत्नैर्हीरकमण्यादिहारैश्चन्दनकुंकुमैः {{१७{",
            "{{१७{",
            17,
            "{{१७{",
            note="verse 17 marker is corrupted into MediaWiki-like braces",
        ),
    ),
    (1, 421): (
        ForcedBoundary(
            "आतिथ्यं कर्तुमिच्छामि तत्र मे संविधीयताम् ३५",
            "३५",
            35,
            "३५",
            note="verse 35 numeral survives but dandas are absent",
        ),
    ),
    (1, 443): (
        ForcedBoundary(
            "किंकरोऽपि गृहमध्ये रक्ष्यते गृहिणीयुतः ।।",
            "।।",
            None,
            "।।",
            note="verse 45 numeral is absent; adjacent printed verses are 44 and 46",
        ),
    ),
    (2, 32): (
        ForcedBoundary(
            "रोहिण्यास्तु कनिष्ठा सा ज्येष्ठतां तपसेच्छति ।। १४।। तु. स्कन्दपु. [https://sa.wikisource.org/s/ggw १.२.२९.२०९]",
            "।। १४।।",
            14,
            "",
            lexical_override="रोहिण्यास्तु कनिष्ठा सा ज्येष्ठतां तपसेच्छति",
            note="verse 14 marker is followed on the same source line by an editorial Skandapurana cross-reference",
        ),
    ),
    (2, 293): (
        ForcedBoundary(
            "नमामि कान्तं मम कन्यकायाः कान्तं तथा चाऽर्बुदकन्यकानाम् ८५",
            "८५",
            85,
            "८५",
            note="verse 85 numeral survives but dandas are absent",
        ),
    ),
    (3, 107): (
        ForcedBoundary(
            "प्राह श्रीचिह्नयोगी तु पश्यतां रूपमैश्वरम्।।",
            "।।",
            None,
            "।।",
            note="verse 42 numeral is absent; next verse is explicitly 43",
        ),
    ),
}


# These lines contain a stray numeral plus a single danda inside the first
# pada.  The permissive one-sided-marker fallback used to split them as full
# verses; the real verse marker occurs on the following line.
IGNORE_FALSE_BOUNDARIES: dict[tuple[int, int], frozenset[str]] = {
    (1, 46): frozenset({"स्तनयित्नूँश्च भानूँश्च वसूनष्टौ तथैव च । १"}),
    (1, 142): frozenset({"सर्वे शुभाक्षरभाषाः शिवाः शिवकराः सदा । १"}),
    (1, 242): frozenset({"वैकुण्ठे चाथ गोलोके यौवनार्थसुखानि ३ ।"}),
    (1, 256): frozenset({"पुष्पांजलिजलताम्बूलैलालंवगचर्वणैः १९ ।"}),
    (1, 587): frozenset({"राजा सत्कारपूजादि चक्रे स्वागतमाचरत् ।५"}),
    (2, 211): frozenset({"एवं सेवां प्रकुर्वन्तु यान्तु मोक्षपदं परम् ।७"}),
    (3, 194): frozenset({"आततायी यदा नैव हन्यते येन सोऽपि वै ३।"}),
    (3, 221): frozenset({"स्मृद्धयो यास्तु यज्ञार्था देवार्था दानधर्मदा ५ ।"}),
}


# Exact duplicated transcription line: the second copy repeats the same pada
# and the same printed verse number.  It is retained in the immutable source
# snapshot but omitted from the normalized/search layer with an audit flag.
DROP_DUPLICATE_LINES: dict[tuple[int, int], frozenset[str]] = {
    (1, 114): frozenset({"अंकयेच्छंखचक्राभ्यां नाम कुर्याच्च वैष्णवम् ।।५५ ।।"}),
}


# Known printed-number sequence offsets that are not segmentation errors.
# value: (minimum canonical position, expected anchor-minus-canonical offset,
# reason).  Strong anchors matching these offsets are classified separately.
KNOWN_ANCHOR_OFFSETS: dict[tuple[int, int], tuple[tuple[int, int, str], ...]] = {
    (1, 44): ((18, -1, "printed verse 17 is used for two distinct consecutive textual units"),),
    (1, 293): ((3, -2, "chapter has two introductory verses, then printed numbering restarts at 1"),),
    (3, 197): ((87, -1, "printed verse 86 is used for two distinct consecutive textual units"),),
}


def forced_boundary(khanda: int, chapter: int, line: str) -> ForcedBoundary | None:
    for repair in FORCED_BOUNDARIES.get((khanda, chapter), ()):
        if line == repair.source_line:
            return repair
    return None


def ignore_false_boundary(khanda: int, chapter: int, line: str) -> bool:
    return line in IGNORE_FALSE_BOUNDARIES.get((khanda, chapter), ())


def drop_duplicate_line(khanda: int, chapter: int, line: str) -> bool:
    return line in DROP_DUPLICATE_LINES.get((khanda, chapter), ())


def known_anchor_offset(khanda: int, chapter: int, canonical: int, offset: int) -> str | None:
    for start, expected, reason in KNOWN_ANCHOR_OFFSETS.get((khanda, chapter), ()):
        if canonical >= start and offset == expected:
            return reason
    return None
