"""T-770 round 1: ARCH_TAKEOFF_V3.0.81 = the candidate of record V3.0.78 (T-738 merge 208c5689, line index
research/agents_t738/out/LINE_INDEX_V3_0_78.json) + the owner-session fix-row set MAIN_FILL_ALL (207 rows,
MAIN_FILL_1 + MAIN_FILL_2, pinned here as MAIN_FILL_ALL.json), applied by line id under R-T770-1
(engine.source.arch_v3081). Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3081_index.py [--check]

Writes out/LINE_INDEX_V3_0_81.json, out/V3_0_81_DIFF.csv and out/V3_0_81_SUMMARY.json; --check rebuilds in memory and
fails if a committed output differs. Applying the same set to full BOQ lines of a private chain run is
arch_v3081.apply_boq_lines(lines, rows, "ARCH_TAKEOFF_V3.0.78").
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as A  # noqa: E402

BASE = ROOT / "research/agents_t738/out/LINE_INDEX_V3_0_78.json"
BASE_SHA = "16b0feeaed5ffb3fbb1c1058489d6aa17cafb1338fdae4e841b34227f9069113"
ROWS = HERE / "MAIN_FILL_ALL.json"
ROWS_SHA = "ad9e2c6f5d5ccdf8442d9427e6d438bdce2fd4f8c47fa7af1bf40157b5d8fd5a"
OUT = HERE / "out"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build():
    for p, want in ((BASE, BASE_SHA), (ROWS, ROWS_SHA)):
        if _sha(p) != want:
            raise SystemExit(f"{p.name}: sha {_sha(p)[:8]} is not the pinned {want[:8]}")
    base = json.loads(BASE.read_text(encoding="utf-8"))
    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    new, applied = A.apply_index(base, rows, "ARCH_TAKEOFF_V3.0.78")
    t0, t1 = A.totals_by_code(base["lines"]), A.totals_by_code(new["lines"])
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        a, b = t0.get(k), t1.get(k)
        if a != b:
            moved[f"{k[0]} [{k[1]}]"] = {"before": {f: round(v, 2) if isinstance(v, float) else v for f, v in a.items()},
                                         "after": {f: round(v, 2) if isinstance(v, float) else v for f, v in b.items()}}
    by_set = {}
    for r in applied:
        s = by_set.setdefault(r["set"], {"rows": 0, "labels": {}})
        s["rows"] += 1
        s["labels"][r["label"]] = s["labels"].get(r["label"], 0) + 1
    new["inputs"] = dict(base.get("inputs") or {}, base_index=BASE_SHA, fix_rows=ROWS_SHA)
    idx_text = json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    summary = {"method": A.METHOD, "extends": "ARCH_TAKEOFF_V3.0.78", "rule": A.RULE,
               "base_index_sha256": BASE_SHA, "fix_rows_sha256": ROWS_SHA,
               "lines": len(new["lines"]), "applied": len(applied), "by_set": by_set,
               "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = A.diff_rows(applied)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {"LINE_INDEX_V3_0_81.json": idx_text,
            "V3_0_81_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            "V3_0_81_DIFF.csv": buf.getvalue()}, summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    files, s = build()
    if "--check" in argv:
        bad = [n for n, t in files.items() if not (OUT / n).exists() or (OUT / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for n, t in files.items():
        (OUT / n).write_text(t, encoding="utf-8")
    print("V3.0.81:", s["lines"], "lines,", s["applied"], "applied,", json.dumps(s["by_set"], sort_keys=True))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
