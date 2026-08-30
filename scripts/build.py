#!/usr/bin/env python3
import csv,json
from pathlib import Path
from lns_corpus.clean import conservative_wikitext_cleanup
from lns_corpus.segment import segment_chapter
from lns_corpus.transliterate import devanagari_to_iast,devanagari_to_slp1
def main():
    source=Path("source/wikisource"); metadata=Path("metadata"); metadata.mkdir(exist_ok=True); reports=Path("reports"); reports.mkdir(exist_ok=True); corpus=Path("corpus")
    for s in ("devanagari","iast","slp1"): (corpus/s).mkdir(parents=True,exist_ok=True)
    rows=[]; anomalies=[]; chapters=[]
    for path in sorted(source.glob("[1-4]/[0-9][0-9][0-9].json")):
        p=json.loads(path.read_text(encoding="utf-8"))
        if "wikitext" not in p: anomalies.append({"type":"missing_wikitext","file":str(path)}); continue
        k=int(p["khanda"]); ch=int(p["chapter"]); recs,ans=segment_chapter(conservative_wikitext_cleanup(p["wikitext"]),k,ch); anomalies.extend(ans); chapters.append({"khanda":k,"chapter":ch,"verses_segmented":len(recs),"source_revision_id":p.get("revision_id"),"source_revision_sha1":p.get("revision_sha1"),"source_url":p.get("source_url"),"anomaly_count":len(ans)})
        outs={s:[] for s in ("devanagari","iast","slp1")}
        for r in recs:
            d=r.as_dict(); d["text_iast"]=devanagari_to_iast(r.text_devanagari); d["text_slp1"]=devanagari_to_slp1(r.text_devanagari); d["source_revision_id"]=p.get("revision_id"); d["source_url"]=p.get("source_url"); rows.append(d); outs["devanagari"].append(f"[{r.id}] {r.text_devanagari}"); outs["iast"].append(f"[{r.id}] {d['text_iast']}"); outs["slp1"].append(f"[{r.id}] {d['text_slp1']}")
        for s in outs: (corpus/s/f"LNS_{k}.{ch:03d}.txt").write_text("\n\n".join(outs[s])+"\n",encoding="utf-8")
    fields=["id","khanda","chapter","verse","text_devanagari","text_iast","text_slp1","marker_raw","marker_normalized","marker_observed_verse","marker_reference_hint","anomaly_flags","source_revision_id","source_url"]
    with (metadata/"verses.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:
            r=dict(r); r["marker_reference_hint"]=json.dumps(r["marker_reference_hint"],ensure_ascii=False); r["anomaly_flags"]=json.dumps(r["anomaly_flags"],ensure_ascii=False); w.writerow(r)
    with (metadata/"chapters.csv").open("w",encoding="utf-8",newline="") as f:
        fs=["khanda","chapter","verses_segmented","source_revision_id","source_revision_sha1","source_url","anomaly_count"]; w=csv.DictWriter(f,fieldnames=fs); w.writeheader(); w.writerows(chapters)
    (reports/"anomalies.json").write_text(json.dumps(anomalies,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"Built {len(rows)} verse records from {len(chapters)} chapters; anomalies={len(anomalies)}")
if __name__=="__main__":main()
