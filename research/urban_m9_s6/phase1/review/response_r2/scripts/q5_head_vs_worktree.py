"""Q5 (scratch): for every file the 3.13 rebuilds rewrote in the worktree, compare it with the committed bytes (git
HEAD): byte-equal?, canonical-equal (JSON / JSONL / CSV floats rounded to 9 decimals, -0.0 -> 0.0)?, largest numeric
difference, and whether the only difference is a code-digest stamp. usage: WT LIST_FILE JSON_OUT"""
import csv, io, json, math, re, subprocess, sys
WT, LST, OUT = sys.argv[1:4]
STAMP = re.compile(r"[0-9a-f]{7}\+code:[0-9a-f]{8,}|\"(code|code_sha256|engine_code)\": \{[^}]*\}", re.S)


def canon(x):
    if isinstance(x, float):
        r = round(x, 9); return 0.0 if r == 0 else r
    if isinstance(x, dict):
        return {k: canon(v) for k, v in x.items()}
    if isinstance(x, list):
        return [canon(v) for v in x]
    return x


def maxdiff(a, b, acc):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        acc[0] = max(acc[0], abs(a - b))
    elif isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() & b.keys(): maxdiff(a[k], b[k], acc)
    elif isinstance(a, list) and isinstance(b, list):
        for x, y in zip(a, b): maxdiff(x, y, acc)


def num(c):
    try:
        f = float(c); return canon(f) if math.isfinite(f) else c
    except ValueError:
        return c


def load(name, data):
    if name.endswith(".json"):
        return json.loads(data)
    if name.endswith(".jsonl"):
        return [json.loads(l) for l in data.splitlines() if l.strip()]
    if name.endswith(".csv"):
        return [[num(c) for c in r] for r in csv.reader(io.StringIO(data))]
    return None


rows = []
for f in open(LST).read().split():
    old = subprocess.run(["git", "-C", WT, "show", f"HEAD:{f}"], capture_output=True, text=True).stdout
    new = open(f"{WT}/{f}", encoding="utf-8").read()
    r = {"file": f.split("/", 2)[-1], "stage_dir": f.split("/")[1], "byte_equal": old == new}
    r["only_stamp_differs"] = STAMP.sub("<STAMP>", old) == STAMP.sub("<STAMP>", new)
    a, b = load(f, old), load(f, new)
    if a is not None:
        acc = [0.0]; maxdiff(a, b, acc)
        r["max_abs_numeric_diff"] = acc[0]
        r["canonical_equal"] = json.dumps(canon(a), sort_keys=True) == json.dumps(canon(b), sort_keys=True)
    rows.append(r)
json.dump(rows, open(OUT, "w"), indent=1)
for r in rows:
    print(r)
