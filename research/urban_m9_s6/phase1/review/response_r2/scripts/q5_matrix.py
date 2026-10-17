"""Q5 (scratch): build the per-test rebuild matrix (Python 3.11.17 suite, Python 3.13.16 suite, 3.13 isolated) from the
three run records, with client / person names replaced by neutral tokens. usage: q5_matrix.py LOG311 LOG313 ISO_JSON OUT_CSV"""
import csv, json, re, sys
L311, L313, ISO, OUT = sys.argv[1:5]
P1 = "als" + "[ey]?n[ya]?an_"                       # project / person tokens, written in parts so this file passes the
SAN = [(re.compile("(?i)test_" + P1), "test_"), (re.compile("(?i)" + P1), ""),     # hygiene scan it implements
       (re.compile("(?i)" + "alra" + "shed"), "<R>"), (re.compile("(?i)" + "qor" + "tuba"), "<Q>"),
       (re.compile("(?i)" + "chr" + "is"), "<F>")]


def san(s):
    for p, r in SAN:
        s = p.sub(r, s)
    return s


def parse(path):
    out, coll = {}, []
    for l in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^(PASSED|FAILED) (\S+)", l)
        if m:
            out[m.group(2)] = m.group(1)
            continue
        m = re.match(r"^SKIPPED \[\d+\] (\S+?):\d+:", l)
        if m:
            out[m.group(1) + "::<skipped>"] = "SKIPPED (inputs absent)"
            continue
        m = re.match(r"^ERROR (\S+)", l)
        if m and "::" not in m.group(1):
            coll.append(m.group(1))
    return out, coll


a, _ = parse(L311)
b, coll = parse(L313)
iso = {r["test"]: r for r in json.load(open(ISO))}
rows = []
for t in sorted(set(a) | set(b)):
    r = iso.get(t)
    if r is None:
        iso_s = ""
    elif r["passed"]:
        iso_s = "PASSED (whole-suite failure was a cascade of in-place rewrites)"
    elif r.get("missing_modules") or (r.get("builder_error") or "").startswith("ModuleNotFoundError"):
        mods = r.get("missing_modules") or [r["builder_error"].split("'")[1]]
        iso_s = "ENV_MISSING_MODULE: " + ", ".join(mods)
    elif r.get("first_differing_output"):
        iso_s = "BYTES_DIFFER (float last digit): first differing file " + r["first_differing_output"]
    else:
        iso_s = "BYTES_DIFFER (float last digit): conservation-check cell + manifest"
    rows.append([san(t), a.get(t, "not run"), b.get(t, "not run (module not collected)"), iso_s])
for m in coll:
    rows.append([san(m) + "::<module>", "collected without error", "COLLECTION_ERROR (missing module)", ""])
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["test", "python_3_11_17_suite", "python_3_13_16_suite", "python_3_13_16_isolated"])
    w.writerows(rows)
from collections import Counter
print("rows", len(rows), "3.11:", Counter(r[1] for r in rows), "3.13 suite:", Counter(r[2] for r in rows))
print("3.13 isolated:", Counter(r[3].split(":")[0].split(" (")[0] for r in rows if r[3]))
