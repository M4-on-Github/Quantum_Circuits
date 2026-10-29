"""Summarize SomeJoint's frozen BUILD.json (data only) and compare circuit hashes with a heliosli manifest.
Usage: python -I -B read_build_json.py <BUILD.json> <QCC_RELEASE_MANIFEST.json>"""
import json, sys
b = json.load(open(sys.argv[1], encoding="utf-8"))
m = json.load(open(sys.argv[2], encoding="utf-8"))
hel = {f["file"]: f["sha256"] for f in m["files"]}
print("top keys:", list(b))
print("batch keys:", list(b["batches"][0]))
print("metadata keys:", b["batches"][0]["metadata"])
tot = 0
for r in b["batches"]:
    k = r["batch"]; md = r["metadata"]; tot += md["T"]
    print(k, md.get("T"), md.get("Q"), r["circuit_sha256"][:12], "== v11" if hel.get(f"dfthcsos/angle_k_{k}.kmb") == r["circuit_sha256"] else "")
print("per pass", tot, "both", 2 * tot)
for k in b:
    if k != "batches":
        print(k, str(b[k])[:300])
