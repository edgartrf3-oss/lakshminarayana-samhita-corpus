#!/usr/bin/env python3
import csv
import json
import yaml
from collections import Counter
from pathlib import Path

cfg = yaml.safe_load(Path("config/corpus.yml").read_text(encoding="utf-8"))
chapters = list(csv.DictReader(Path("metadata/chapters.csv").open(encoding="utf-8")))
verses = list(csv.DictReader(Path("metadata/verses.csv").open(encoding="utf-8")))
cc = Counter(int(r["khanda"]) for r in chapters)
vc = Counter(int(r["khanda"]) for r in verses)

no_verse_chapters = [
    {"khanda": int(r["khanda"]), "chapter": int(r["chapter"]), "source_url": r.get("source_url")}
    for r in chapters
    if int(r["verses_segmented"]) == 0
]

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
if not page_tree_complete:
    status = "page_tree_incomplete"
elif no_verse_chapters:
    # A page can exist in MediaWiki while containing no chapter text. Keep
    # this distinct from downloader/page-tree completeness and from ordinary
    # marker anomalies so genuine source lacunae are never hidden.
    status = "source_text_gap_or_segmentation_review_required"
else:
    status = "structurally_consistent"

report = {
    "chapter_pages_total": len(chapters),
    "chapters_expected": expected_chapters,
    "page_tree_complete": page_tree_complete,
    "chapters_with_no_verse_records": no_verse_chapters,
    "verse_records_total": len(verses),
    "declared_slokas_total": cfg["checksums"]["declared_slokas_total"],
    "difference_vs_declared_slokas": len(verses) - cfg["checksums"]["declared_slokas_total"],
    "khanda": kr,
    "status": status,
}
Path("reports").mkdir(exist_ok=True)
Path("reports/validation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
