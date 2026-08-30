from __future__ import annotations
import re
from dataclasses import dataclass,asdict
from .markers import split_trailing_marker

COLOPHON_START=re.compile(r"^\s*इति\s*श्री(?:लक्ष्मी|लक्ष्मीनारायण)")

@dataclass
class VerseRecord:
    id:str; khanda:int; chapter:int; verse:int; text_devanagari:str; marker_raw:str; marker_normalized:str; marker_observed_verse:int|None; marker_reference_hint:list[int]; anomaly_flags:list[str]
    def as_dict(self): return asdict(self)

def segment_chapter(text,khanda,chapter):
    records=[]; anomalies=[]; buffer=[]; canonical=0
    for lineno,raw in enumerate(text.splitlines(),1):
        line=raw.strip()
        if not line: continue
        if COLOPHON_START.match(line): break
        lexical,marker=split_trailing_marker(line)
        if lexical: buffer.append(lexical)
        if marker is None: continue
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
        # verse boundary.  Never fabricate an observed number.
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
    if buffer:
        tail="\n".join(buffer).strip()
        if tail: anomalies.append({"type":"unsegmented_tail","khanda":khanda,"chapter":chapter,"text_preview":tail[:200]})
    return records,anomalies
