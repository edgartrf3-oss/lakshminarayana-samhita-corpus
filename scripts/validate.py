#!/usr/bin/env python3
import csv,json,yaml
from collections import Counter
from pathlib import Path
cfg=yaml.safe_load(Path("config/corpus.yml").read_text(encoding="utf-8")); chapters=list(csv.DictReader(Path("metadata/chapters.csv").open(encoding="utf-8"))); verses=list(csv.DictReader(Path("metadata/verses.csv").open(encoding="utf-8"))); cc=Counter(int(r["khanda"]) for r in chapters); vc=Counter(int(r["khanda"]) for r in verses); kr={}
for k in [1,2,3,4]:
    info=cfg["khanda"][k]; declared=info["declared_slokas"]+info.get("declared_additional_slokas",0); kr[str(k)]={"chapters_found":cc[k],"chapters_expected":info["expected_chapters"],"chapter_count_ok":cc[k]==info["expected_chapters"],"verses_segmented":vc[k],"slokas_declared_with_additions":declared,"difference_vs_declared_slokas":vc[k]-declared}
report={"chapters_total":len(chapters),"chapters_expected":cfg["checksums"]["expected_chapters_total"],"verse_records_total":len(verses),"declared_slokas_total":cfg["checksums"]["declared_slokas_total"],"khanda":kr,"status":"structurally_consistent" if len(chapters)==cfg["checksums"]["expected_chapters_total"] else "review_required"}; Path("reports").mkdir(exist_ok=True); Path("reports/validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(report,ensure_ascii=False,indent=2))
