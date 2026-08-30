#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "metadata"
SITE = ROOT / "site"
CONSOLIDATED = ROOT / "consolidated"

KHANDA_NAMES = {
    1: ("Kṛtayuga-santāna", "कृतयुगसन्तानः"),
    2: ("Tretāyuga-santāna", "त्रेतायुगसन्तानः"),
    3: ("Dvāparayuga-santāna", "द्वापरयुगसन्तानः"),
    4: ("Tiṣya-santāna", "तिष्यसन्तानः"),
}

STYLE = r"""
:root{--bg:#fbfaf6;--fg:#1d1d1b;--muted:#69665f;--line:#ddd8cb;--card:#fff;--accent:#6b3f1f;--max:1040px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.55}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}.wrap{width:min(var(--max),calc(100% - 2rem));margin:auto}.top{position:sticky;top:0;z-index:5;background:rgba(251,250,246,.96);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}.top .wrap{display:flex;gap:1rem;align-items:center;justify-content:space-between;padding:.7rem 0;flex-wrap:wrap}.brand{font-weight:700}.nav{display:flex;gap:.8rem;flex-wrap:wrap;font-size:.92rem}.hero{padding:2.5rem 0 1.5rem}.hero h1{font-size:clamp(1.8rem,4vw,3rem);margin:.1rem 0}.sub{color:var(--muted);max-width:75ch}.notice{border:1px solid var(--line);background:#fff8e7;border-radius:.65rem;padding:.8rem 1rem;margin:1rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}.card{background:var(--card);border:1px solid var(--line);border-radius:.8rem;padding:1rem}.card h2,.card h3{margin-top:0}.chapter-list{columns:4 8rem;column-gap:1rem}.chapter-list a{display:block;padding:.12rem 0;break-inside:avoid}.toolbar{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin:1rem 0}.toolbar input{min-width:min(420px,100%);padding:.55rem .7rem;border:1px solid var(--line);border-radius:.5rem;background:white}.btn{display:inline-block;border:1px solid var(--line);border-radius:.5rem;padding:.45rem .7rem;background:white;cursor:pointer}.verse{display:grid;grid-template-columns:minmax(8rem,11rem) 1fr;gap:1rem;padding:.72rem 0;border-top:1px solid var(--line);scroll-margin-top:5rem}.ref{font:600 .88rem ui-monospace,SFMono-Regular,Consolas,monospace}.text{font-family:"Noto Serif Devanagari","Noto Serif",Georgia,serif;font-size:1.14rem;white-space:pre-wrap}.iast .text{font-family:Georgia,"Times New Roman",serif;font-size:1.08rem}.source{font-size:.78rem;color:var(--muted)}.pager{display:flex;justify-content:space-between;gap:1rem;margin:1rem 0 2rem}.footer{border-top:1px solid var(--line);color:var(--muted);font-size:.86rem;padding:1.5rem 0 3rem;margin-top:2rem}.hidden{display:none!important}details{margin:.7rem 0}summary{cursor:pointer;font-weight:650}@media(max-width:650px){.chapter-list{columns:2}.verse{grid-template-columns:1fr;gap:.2rem}.ref{position:sticky;top:3.4rem;background:var(--bg);width:max-content;padding-right:.35rem}}
"""

JS = r"""
function filterVerses(){const q=(document.getElementById('verseFilter')?.value||'').toLocaleLowerCase();document.querySelectorAll('.verse').forEach(v=>{v.classList.toggle('hidden',q && !v.innerText.toLocaleLowerCase().includes(q));});}
function copyLink(id){const u=new URL(location.href);u.hash=id;navigator.clipboard?.writeText(u.toString());}
"""


def esc(s: str | None) -> str:
    return html.escape(s or "", quote=True)


def shell(title: str, body: str, *, root: str = "", cls: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><link rel="stylesheet" href="{root}assets/style.css"></head>
<body class="{esc(cls)}"><header class="top"><div class="wrap"><a class="brand" href="{root}index.html">Lakṣmīnārāyaṇa Saṃhitā Corpus</a><nav class="nav"><a href="{root}index.html">Index</a><a href="{root}devanagari.html">Devanāgarī</a><a href="{root}iast.html">IAST</a></nav></div></header>
<main class="wrap">{body}</main><footer class="footer"><div class="wrap">Derived research interface for the Sanskrit Wikisource corpus. Canonical verse IDs belong to this corpus; the immutable source snapshot and revision metadata remain available in the project artifacts.</div></footer><script src="{root}assets/app.js"></script></body></html>"""


def verse_html(r: dict[str, str], text_field: str) -> str:
    vid = r["id"]
    src = r.get("source_url") or ""
    source_link = f'<a class="source" href="{esc(src)}" rel="noopener">source</a>' if src else ""
    return f'''<article class="verse" id="{esc(vid)}" data-id="{esc(vid)}"><div><a class="ref" href="#{esc(vid)}">{esc(vid.replace("_", " "))}</a><br>{source_link}<br><button class="btn source" onclick="copyLink('{esc(vid)}')">copy link</button></div><div class="text">{esc(r[text_field])}</div></article>'''


def read_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with (META / "verses.csv").open(encoding="utf-8", newline="") as f:
        verses = list(csv.DictReader(f))
    with (META / "chapters.csv").open(encoding="utf-8", newline="") as f:
        chapters = list(csv.DictReader(f))
    verses.sort(key=lambda r: (int(r["khanda"]), int(r["chapter"]), int(r["verse"])))
    chapters.sort(key=lambda r: (int(r["khanda"]), int(r["chapter"])))
    return verses, chapters


def build_index(chapters: list[dict[str, str]]) -> None:
    by_k: dict[int, list[dict[str, str]]] = defaultdict(list)
    for r in chapters:
        by_k[int(r["khanda"])].append(r)
    cards = []
    for k in range(1, 5):
        latin, dev = KHANDA_NAMES[k]
        links = []
        for r in by_k[k]:
            ch = int(r["chapter"])
            n = int(r.get("verses_segmented") or 0)
            label = f"{ch}" + (" — source gap" if n == 0 else "")
            links.append(f'<a href="{k}/{ch:03d}.html">{esc(label)}</a>')
        cards.append(f'''<section class="card"><h2>{k}. {esc(latin)}</h2><div lang="sa">{esc(dev)}</div><p>{len(by_k[k])} chapter pages</p><details><summary>Chapters</summary><div class="chapter-list">{"".join(links)}</div></details></section>''')
    body = f'''<section class="hero"><h1>Lakṣmīnārāyaṇa Saṃhitā</h1><p class="sub">A reproducible, verse-addressable research corpus derived from Sanskrit Wikisource. Browse by chapter or use the consolidated Devanāgarī/IAST pages for GRETIL-style full-text browser search.</p><div class="notice"><strong>Known source gap:</strong> LNS 2.96 has a MediaWiki page but no Sanskrit chapter text in the audited source snapshot. It is intentionally left empty rather than reconstructed.</div></section><section class="grid">{"".join(cards)}</section>'''
    (SITE / "index.html").write_text(shell("Lakṣmīnārāyaṇa Saṃhitā Corpus", body), encoding="utf-8")


def build_chapters(verses: list[dict[str, str]], chapters: list[dict[str, str]]) -> None:
    grouped: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for r in verses:
        grouped[(int(r["khanda"]), int(r["chapter"]))].append(r)
    keys = [(int(r["khanda"]), int(r["chapter"])) for r in chapters]
    for i, (k, ch) in enumerate(keys):
        rows = grouped.get((k, ch), [])
        latin, dev = KHANDA_NAMES[k]
        prev_link = ""
        next_link = ""
        if i:
            pk, pc = keys[i - 1]
            prev_link = f'<a class="btn" href="../{pk}/{pc:03d}.html">← LNS {pk}.{pc}</a>'
        if i + 1 < len(keys):
            nk, nc = keys[i + 1]
            next_link = f'<a class="btn" href="../{nk}/{nc:03d}.html">LNS {nk}.{nc} →</a>'
        if rows:
            content = "".join(verse_html(r, "text_devanagari") + f'<div class="verse iast" id="{esc(r["id"])}-iast"><div><span class="ref">IAST</span></div><div class="text">{esc(r["text_iast"])}</div></div>' for r in rows)
        else:
            content = '<div class="notice"><strong>Source gap.</strong> No Sanskrit verse records are available for this chapter in the audited Wikisource snapshot.</div>'
        body = f'''<section class="hero"><h1>LNS {k}.{ch}</h1><p>{esc(latin)} · <span lang="sa">{esc(dev)}</span></p><p class="sub">{len(rows)} segmented verse records. Each Devanāgarī verse has a stable fragment identifier such as <code>#LNS_{k}.{ch}.1</code>.</p></section><div class="toolbar"><input id="verseFilter" oninput="filterVerses()" placeholder="Filter this chapter…"></div><nav class="pager">{prev_link}<span></span>{next_link}</nav>{content}<nav class="pager">{prev_link}<span></span>{next_link}</nav>'''
        out = SITE / str(k) / f"{ch:03d}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(shell(f"LNS {k}.{ch} — {latin}", body, root="../"), encoding="utf-8")


def build_full(verses: list[dict[str, str]], field: str, filename: str, label: str, cls: str = "") -> None:
    chunks = []
    current = None
    for r in verses:
        key = (int(r["khanda"]), int(r["chapter"]))
        if key != current:
            current = key
            chunks.append(f'<h2 id="LNS_{key[0]}.{key[1]}">LNS {key[0]}.{key[1]}</h2>')
        chunks.append(verse_html(r, field))
    body = f'''<section class="hero"><h1>Lakṣmīnārāyaṇa Saṃhitā — {esc(label)}</h1><p class="sub">Consolidated full-text view. Use the browser’s Find command (Ctrl/Cmd+F) for GRETIL-style searching, or jump directly to a canonical fragment such as <code>#LNS_3.173.52</code>.</p></section>{"".join(chunks)}'''
    rendered = shell(f"LNS — {label}", body, cls=cls)
    (SITE / filename).write_text(rendered, encoding="utf-8")
    CONSOLIDATED.mkdir(exist_ok=True)
    shutil.copyfile(SITE / filename, CONSOLIDATED / f"LNS-{filename}")


def build_machine_manifest(verses: list[dict[str, str]], chapters: list[dict[str, str]]) -> None:
    manifest = {
        "title": "Lakshminarayana Samhita Corpus",
        "verse_records": len(verses),
        "chapter_pages": len(chapters),
        "canonical_id_example": "LNS_3.173.52",
        "known_source_gaps": [
            {"khanda": int(r["khanda"]), "chapter": int(r["chapter"])}
            for r in chapters if int(r.get("verses_segmented") or 0) == 0
        ],
    }
    (SITE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    verses, chapters = read_rows()
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    (SITE / "assets" / "style.css").write_text(STYLE.strip() + "\n", encoding="utf-8")
    (SITE / "assets" / "app.js").write_text(JS.strip() + "\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    build_index(chapters)
    build_chapters(verses, chapters)
    build_full(verses, "text_devanagari", "devanagari.html", "Devanāgarī")
    build_full(verses, "text_iast", "iast.html", "IAST", cls="iast")
    build_machine_manifest(verses, chapters)
    print(f"Built HTML site: {len(chapters)} chapter pages, {len(verses)} verse records")
    print(SITE / "index.html")
    print(CONSOLIDATED / "LNS-devanagari.html")
    print(CONSOLIDATED / "LNS-iast.html")


if __name__ == "__main__":
    main()
