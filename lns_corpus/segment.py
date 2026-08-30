from __future__ import annotations
import re
from dataclasses import dataclass,asdict
from .markers import split_trailing_marker, split_first_inline_marker

# Every non-empty chapter in the current Wikisource snapshot has a closing
# colophon of this general form, but the transcription contains variants:
# omitted śrī, spelling damage, and hyphenated saṃhi-tā. Restrict detection
# to the latter half of a chapter and choose the last candidate; this avoids
# treating ordinary occurrences of "iti" as a colophon.
COLOPHON_RE = re.compile(r"इति\s*(?:श्री)?[^\n]{0,100}?(?:संहि-?ता|सहिता)")
STRICT_COLOPHON_RE = re.compile(r"इति\s*श्रीलक्ष्मीनारायणीयसंहिता")
# Fallback retained for future snapshots whose colophon is too damaged for
# COLOPHON_RE but still begins in the formerly recognized standard shape.
COLOPHON_START = re.compile(r"^\s*इति\s*श्री(?:लक्ष्मी|लक्ष्मीनारायण)")

@dataclass
class VerseRecord:
    id:str; khanda:int; chapter:int; verse:int; text_devanagari:str; marker_raw:str; marker_normalized:str; marker_observed_verse:int|None; marker_reference_hint:list[int]; anomaly_flags:list[str]
    def as_dict(self): return asdict(self)

def _separate_colophon(text:str,khanda:int,chapter:int):
    anomalies=[]
    candidates=[m for m in COLOPHON_RE.finditer(text) if m.start() >= len(text)*0.5]
    if not candidates:
        return text,anomalies
    m=candidates[-1]
    start=m.start()
    line_start=text.rfind("\n",0,start)+1
    midline=bool(text[line_start:start].strip())
    lineno=text.count("\n",0,start)+1
    raw_preview=text[start:start+220].replace("\n"," ")
    anomalies.append({
        "type":"colophon_detected_midline" if midline else "colophon_detected",
        "khanda":khanda,
        "chapter":chapter,
        "line":lineno,
        "text_preview":raw_preview,
    })
    if not STRICT_COLOPHON_RE.match(text[start:]):
        anomalies.append({
            "type":"colophon_variant_detected",
            "khanda":khanda,
            "chapter":chapter,
            "line":lineno,
            "text_preview":raw_preview,
        })
    return text[:start],anomalies

def segment_chapter(text,khanda,chapter):
    text,colophon_anomalies=_separate_colophon(text,khanda,chapter)
    records=[]; anomalies=list(colophon_anomalies); buffer=[]; canonical=0

    def emit(marker,lineno):
        nonlocal canonical,buffer
        canonical+=1; flags=[]; observed=marker.observed_verse_number

        for marker_flag in marker.anomaly_flags:
            if marker_flag not in flags:
                flags.append(marker_flag)
            anomalies.append({
                "type":marker_flag,
                "khanda":khanda,
                "chapter":chapter,
                "line":lineno,
                "canonical_position":canonical,
                "marker":marker.raw,
            })

        # If the printed number cannot be parsed, the marker is used only as a
        # verse boundary. Never fabricate an observed number.
        if observed is not None and observed!=canonical:
            flags.append("printed_verse_number_mismatch")
            anomalies.append({"type":"printed_verse_number_mismatch","khanda":khanda,"chapter":chapter,"line":lineno,"canonical_position":canonical,"observed":observed,"marker":marker.raw})
        hint=marker.full_reference_hint
        if len(hint)>=3:
            ak,ach,av=hint[-3],hint[-2],hint[-1]
            if ak!=khanda or ach!=chapter:
                flags.append("marker_prefix_context_mismatch")
                anomalies.append({"type":"marker_prefix_context_mismatch","khanda":khanda,"chapter":chapter,"line":lineno,"canonical_position":canonical,"hint":list(hint)})
            elif av!=canonical:
                flags.append("strong_anchor_position_mismatch")
                anomalies.append({"type":"strong_anchor_position_mismatch","khanda":khanda,"chapter":chapter,"line":lineno,"canonical_position":canonical,"anchor_verse":av,"hint":list(hint)})
        verse_text="\n".join(buffer).strip()
        records.append(VerseRecord(f"LNS_{khanda}.{chapter}.{canonical}",khanda,chapter,canonical,verse_text,marker.raw,marker.normalized_body,observed,list(hint),flags)); buffer=[]

    for lineno,raw in enumerate(text.splitlines(),1):
        line=raw.strip()
        if not line: continue
        if COLOPHON_START.match(line):
            anomalies.append({"type":"fallback_colophon_detected","khanda":khanda,"chapter":chapter,"line":lineno,"text_preview":line[:200]})
            break

        # Very rare source line-wrap corruption can place the end marker of
        # one verse and the first pada of the next verse on the same line.
        # Only the strict inline detector handles this; editorial notes after
        # a verse marker are intentionally left untouched.
        while True:
            lexical,inline_marker,remainder=split_first_inline_marker(line)
            if inline_marker is None:
                break
            if lexical:
                buffer.append(lexical)
            emit(inline_marker,lineno)
            line=remainder.strip()
            if not line:
                break
        if not line:
            continue

        lexical,marker=split_trailing_marker(line)
        if lexical: buffer.append(lexical)
        if marker is None: continue
        emit(marker,lineno)

    if buffer:
        tail="\n".join(buffer).strip()
        if tail: anomalies.append({"type":"unsegmented_tail","khanda":khanda,"chapter":chapter,"text_preview":tail[:200]})
    return records,anomalies
