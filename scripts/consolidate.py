#!/usr/bin/env python3
from pathlib import Path
for script in ("devanagari","iast","slp1"):
    parts=[p.read_text(encoding="utf-8").rstrip() for p in sorted((Path("corpus")/script).glob("LNS_*.txt"))]
    out=Path("consolidated")/f"LNS-{script}.txt"; out.parent.mkdir(exist_ok=True); out.write_text("\n\n".join(parts)+"\n",encoding="utf-8"); print(out)
