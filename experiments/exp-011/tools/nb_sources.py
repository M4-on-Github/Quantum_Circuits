"""List/extract the SOURCES dict of a notebook's code cells WITHOUT executing it (ast.literal_eval only).
Usage: python -I -B nb_sources.py <nb.ipynb> <list|dump> [outdir]"""
import ast, json, sys, hashlib, os
sys.stdout.reconfigure(encoding="utf-8")
nb = json.load(open(sys.argv[1], encoding="utf-8"))
found = {}
for c in nb["cells"]:
    if c.get("cell_type") != "code":
        continue
    src = c["source"] if isinstance(c["source"], str) else "".join(c["source"])
    try:
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("SOURCES", "SOURCE_HASHES", "INPUT_SOURCES", "NOTEBOOK", "COMPETITION_FILES"):
                try:
                    found[name] = ast.literal_eval(node.value)
                except Exception as e:
                    found[name] = f"<not literal: {e}>"
S = found.get("SOURCES", {})
H = found.get("SOURCE_HASHES", {})
print("keys found:", list(found))
print("NOTEBOOK:", found.get("NOTEBOOK"))
if sys.argv[2] == "list":
    for k, v in S.items():
        h = hashlib.sha256(v.encode("utf-8")).hexdigest()
        print(f"{len(v):>8} {h[:12]} {'ok' if H.get(k)==h else 'H?'+str(H.get(k,''))[:12]} {k}")
else:
    out = sys.argv[3]
    for k, v in S.items():
        assert not os.path.isabs(k) and ".." not in k.split("/"), k
        p = os.path.join(out, *k.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="").write(v)
    print("wrote", len(S), "files")
