#!/usr/bin/env python3
import csv
import json
import yaml
from collections import Counter
from pathlib import Path

cfg = yaml.safe_load(Path("config/corpus.yml").read_text(encoding="utf-8"))
chapters = list(csv.DictReader(Path("metadata/chapters.csv").open(encoding="utf-8")))
verses = list(csv.DictReader(Path("metadata/verses.csv").open(encoding="utf-8")))
anomalies_path = Path("reports/anomalies.json")
anomalies = json.loads(anomalies_path.read_text(encoding="utf-8")) if anomalies_path.exists() else []

cc = Counter(int(r["khanda"]) for r in chapters)
vc = Counter(int(r["khanda"]) for r in verses)
anomaly_counts = Counter(a.get("type", "unknown") for a in anomalies)

no_verse_chapters = [
    {"khanda": int(r["khanda"]), "chapter": int(r["chapter"]), "source_url": r.get("source_url")}
    for r in chapters
    if int(r["verses_segmented"]) == 0
]

unresolved_strong = [a for a in anomalies if a.get("type") == "strong_anchor_position_mismatch"]
known_offsets = [a for a in anomalies if a.get("type") == "known_numbering_offset"]
source_repairs = [a for a in anomalies if a.get("type") == "source_repair_applied"]
prefix_mismatches = [a for a in anomalies if a.get("type") == "marker_prefix_context_mismatch"]

# A bad khaṇḍa/chapter prefix is not a segmentation failure when the printed
# verse component still lands at the canonical position.  This is common in
# the source (e.g. 2.254.30 printed inside Khaṇḍa 1, chapter 254).
prefix_mismatches_positionally_safe = all(
    a.get("hint")
    and int(a["hint"][-1]) == int(a.get("canonical_position", -1))
    for a in prefix_mismatches
)

unsegmented_tails = [a for a in anomalies if a.get("type") == "unsegmented_tail"]
harmless_tail_types = []
for a in unsegmented_tails:
    preview = (a.get("text_preview") or "").strip()
    if preview.startswith("( ५५,५२७)"):
        kind = "editorial_declared_sloka_total"
    elif preview and all(ch in "'’‘\".,;:-–—()[]{} \t\n" for ch in preview):
        kind = "transcription_punctuation_debris"
    elif int(a.get("khanda", 0)) == 2 and int(a.get("chapter", 0)) == 96:
        kind = "known_empty_source_page"
    else:
        kind = "requires_review"
    harmless_tail_types.append({**a, "classification": kind})

unresolved_tails = [a for a in harmless_tail_types if a["classification"] == "requires_review"]

kr = {}
for k in [1, 2, 3, 4]:
    info = cfg["khanda"][k]
    declared = info["declared_slokas"] + info.get("declared_additional_slokas", 0)
    zero_here = [r for r in no_verse_chapters if r["khanda"] == k]
    kr[str(k)] = {
        "chapter_pages_found": cc[k],
        "chapters_expected": info["expected_chapters"],
        "page_tree_complete": cc[k] == info["expected_chapters"],
        "chapters_with_no_verse_records": zero_here,
        "verses_segmented": vc[k],
        "slokas_declared_with_additions": declared,
        "difference_vs_declared_slokas": vc[k] - declared,
    }

expected_chapters = cfg["checksums"]["expected_chapters_total"]
page_tree_complete = len(chapters) == expected_chapters
structural_boundaries_audited = (
    page_tree_complete
    and len(unresolved_strong) == 0
    and len(unresolved_tails) == 0
    and prefix_mismatches_positionally_safe
)

if not page_tree_complete:
    status = "page_tree_incomplete"
elif unresolved_strong or unresolved_tails or not prefix_mismatches_positionally_safe:
    status = "segmentation_review_required"
elif no_verse_chapters:
    status = "structurally_audited_with_known_source_gap"
else:
    status = "structurally_audited"

report = {
    "chapter_pages_total": len(chapters),
    "chapters_expected": expected_chapters,
    "page_tree_complete": page_tree_complete,
    "chapters_with_no_verse_records": no_verse_chapters,
    "verse_records_total": len(verses),
    "declared_slokas_total": cfg["checksums"]["declared_slokas_total"],
    "difference_vs_declared_slokas": len(verses) - cfg["checksums"]["declared_slokas_total"],
    "declared_sloka_total_is_editorial_checksum_not_forced_segmentation_target": True,
    "structural_audit": {
        "structural_boundaries_audited": structural_boundaries_audited,
        "unresolved_strong_anchor_position_mismatches": len(unresolved_strong),
        "known_numbering_offset_events": len(known_offsets),
        "source_specific_repairs_applied": len(source_repairs),
        "printed_reference_prefix_mismatches": len(prefix_mismatches),
        "printed_reference_prefix_mismatches_positionally_safe": prefix_mismatches_positionally_safe,
        "unsegmented_tails_total": len(unsegmented_tails),
        "unresolved_unsegmented_tails": len(unresolved_tails),
        "unsegmented_tail_classifications": harmless_tail_types,
    },
    "anomaly_counts": dict(sorted(anomaly_counts.items())),
    "khanda": kr,
    "status": status,
}
Path("reports").mkdir(exist_ok=True)
Path("reports/validation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
