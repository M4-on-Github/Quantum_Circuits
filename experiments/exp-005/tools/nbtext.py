"""Print a .ipynb's cell sources as plain text (never executes it). Usage: python -I nbtext.py <nb> [out.txt]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
nb = json.load(open(sys.argv[1], encoding="utf-8"))
parts = []
for i, c in enumerate(nb.get("cells", [])):
    src = c.get("source", "")
    parts.append(f"### cell {i} [{c.get('cell_type')}]\n" + ("".join(src) if isinstance(src, list) else src))
text = "\n".join(parts)
if len(sys.argv) > 2:
    open(sys.argv[2], "w", encoding="utf-8").write(text)
else:
    print(text)
