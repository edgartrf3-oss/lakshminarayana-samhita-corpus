#!/usr/bin/env python3
import argparse,json,re,yaml
from datetime import datetime,timezone
from pathlib import Path
from lns_corpus.mediawiki import MediaWikiClient
TRANS=str.maketrans("०१२३४५६७८९","0123456789")
CHAPTER_RE=re.compile(r"/अध्यायः[_ ]+([०-९0-9 ]+)$")
def chapter_number(title):
    m=CHAPTER_RE.search(title)
    if not m:return None
    s="".join(m.group(1).translate(TRANS).split()); return int(s) if s.isdigit() else None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/corpus.yml"); ap.add_argument("--out",default="source/wikisource"); ap.add_argument("--user-agent",required=True); ap.add_argument("--delay",type=float,default=.5); a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.config).read_text(encoding="utf-8")); client=MediaWikiClient(cfg["work"]["api_endpoint"],a.user_agent,a.delay); root=Path(a.out); root.mkdir(parents=True,exist_ok=True); manifest=[]
    for k in [1,2,3,4]:
        info=cfg["khanda"][k]; prefix=f'{cfg["work"]["root_title"]}/{info["title"]}/अध्यायः'; pages=[]
        for p in client.allpages(prefix):
            n=chapter_number(p["title"])
            if n and 1<=n<=info["expected_chapters"]: pages.append((n,p))
        by_n={}
        for n,p in sorted(pages): by_n.setdefault(n,p)
        expected=set(range(1,info["expected_chapters"]+1)); missing=sorted(expected-set(by_n)); print(f"Khanda {k}: found {len(by_n)}/{len(expected)}; missing={missing[:20]}")
        records=client.revisions_with_content_by_pageid([by_n[n]["id"] for n in sorted(by_n)]); by_id={p["pageid"]:p for p in records}; kdir=root/str(k); kdir.mkdir(exist_ok=True)
        for n in sorted(by_n):
            title=by_n[n]["title"]; page=by_id.get(by_n[n]["id"],{}); revs=page.get("revisions") or []
            if not revs: payload={"title":title,"pageid":page.get("pageid"),"khanda":k,"chapter":n,"error":"no_revision"}
            else:
                rev=revs[0]; content=rev.get("slots",{}).get("main",{}).get("content",""); payload={"title":title,"pageid":page.get("pageid"),"khanda":k,"chapter":n,"revision_id":rev.get("revid"),"parent_id":rev.get("parentid"),"revision_timestamp":rev.get("timestamp"),"revision_sha1":rev.get("sha1"),"revision_size":rev.get("size"),"retrieved_at":datetime.now(timezone.utc).isoformat(),"source_url":"https://sa.wikisource.org/wiki/"+title.replace(" ","_"),"wikitext":content}
            (kdir/f"{n:03d}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); manifest.append({x:y for x,y in payload.items() if x!="wikitext"})
        (kdir/"_audit.json").write_text(json.dumps({"khanda":k,"expected_chapters":info["expected_chapters"],"found_chapters":len(by_n),"missing_chapters":missing},ensure_ascii=False,indent=2),encoding="utf-8")
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
