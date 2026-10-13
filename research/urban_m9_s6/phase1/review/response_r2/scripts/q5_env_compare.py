"""Q5 (scratch): compare two output folders byte-wise, then after a canonical form (JSON parsed, floats rounded to
9 decimals, -0.0 -> 0.0, keys sorted; CSV cells that parse as floats rounded the same way), and report the largest
numeric difference. usage: python3 -I q5_env_compare.py DIR_A DIR_B [JSON_OUT]"""
import csv, hashlib, io, json, math, sys
from pathlib import Path
A, B = Path(sys.argv[1]), Path(sys.argv[2])
MAXD = [0.0, None]


def canon(x):
    if isinstance(x, float):
        r = round(x, 9)
        return 0.0 if r == 0 else r
    if isinstance(x, dict):
        return {k: canon(v) for k, v in x.items()}
    if isinstance(x, list):
        return [canon(v) for v in x]
    return x


def walk(a, b, path):
    if isinstance(a, float) and isinstance(b, float):
        d = abs(a - b)
        if d > MAXD[0]:
            MAXD[0], MAXD[1] = d, path
    elif isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() & b.keys():
            walk(a[k], b[k], path + "." + k)
    elif isinstance(a, list) and isinstance(b, list):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]")


def cell(v):
    try:
        f = float(v)
        return repr(canon(f)) if math.isfinite(f) else v
    except ValueError:
        return v


rows = []
for f in sorted(p.name for p in A.iterdir() if p.is_file()):
    ba, bb = (A / f).read_bytes(), (B / f).read_bytes() if (B / f).exists() else None
    same = bb is not None and hashlib.sha256(ba).digest() == hashlib.sha256(bb).digest()
    canon_same = same
    if not same and bb is not None:
        if f.endswith(".json"):
            ja, jb = json.loads(ba), json.loads(bb)
            walk(ja, jb, f)
            canon_same = json.dumps(canon(ja), sort_keys=True) == json.dumps(canon(jb), sort_keys=True)
        elif f.endswith(".csv"):
            ca = [[cell(c) for c in r] for r in csv.reader(io.StringIO(ba.decode("utf-8-sig")))]
            cb = [[cell(c) for c in r] for r in csv.reader(io.StringIO(bb.decode("utf-8-sig")))]
            canon_same = ca == cb
        else:
            canon_same = None
    rows.append({"file": f, "bytes_equal": same, "canonical_equal": canon_same})
for r in rows:
    print(f"{r['file']:44s} bytes_equal={r['bytes_equal']!s:5s} canonical_equal={r['canonical_equal']}")
print("files", len(rows), "byte-different", sum(not r["bytes_equal"] for r in rows),
      "canonical-different", sum(r["canonical_equal"] is False for r in rows), "max |diff|", MAXD)
if len(sys.argv) > 3:
    json.dump({"files": rows, "max_abs_numeric_diff": MAXD[0], "at": MAXD[1]}, open(sys.argv[3], "w"), indent=1)
