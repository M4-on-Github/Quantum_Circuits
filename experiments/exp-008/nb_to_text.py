"""Dump a .ipynb as plain text (cell sources, truncated text outputs). Reads JSON only; never executes."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
nb = json.load(open(sys.argv[1], encoding="utf-8"))
maxout = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
for i, c in enumerate(nb.get("cells", [])):
    src = "".join(c.get("source", []))
    print(f"\n######## cell {i} [{c.get('cell_type')}]\n{src}")
    for o in c.get("outputs", []):
        t = o.get("text") or o.get("data", {}).get("text/plain")
        if t:
            t = "".join(t)
            print(f"-------- output ({len(t)} chars)\n{t[:maxout]}")
