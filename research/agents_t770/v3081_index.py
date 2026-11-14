"""T-770 r2: ARCH_TAKEOFF_V3.0.81 = the candidate of record V3.0.79 (T-314 r4 merge 57e4a49f, line index
research/agents_t314/out/LINE_INDEX_V3_0_79.json) + three Checker-verified family groups, applied by line id under
R-T770-1 / R-T770-2 (engine.source.arch_v3081):

  1. MAIN_FILL_ALL (owner session 2026-11-13 16:30, pinned here) WITHOUT its 126 formwork rows (Verifier T-762 Gate A
     2026-11-13T16:59Z: double count CONFIRMED on BM-GF-048, T-762's set is wired instead) and WITHOUT its disposal row
     (the Checker-verified T-764 disposal figure 9.05 m3 replaces the 105.6 .. 115.5 range; it is wired with T-764's set);
  2. T-762 formwork set (merged 43eae30a), the 33 cover deductions netted into their hosts (F-V762-1, R-T770-2 f);
  3. T-761 concrete set (merged 8d3bbf1c): 67 figures, 13 known pieces < 0.05 m3 IGNORED_SMALL under ONE safety line
     (R-T770-2 g).

Every set was built on V3.0.78; V3.0.79 moved none of the lines they name (R-T770-1 a re-checks each). Reads committed
files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3081_index.py [--check]

Writes V3081_PACKAGE.json (the hub's --v3081-inputs), out/LINE_INDEX_V3_0_81.json, out/V3_0_81_DIFF.csv and
out/V3_0_81_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
"""
from __future__ import annotations

import copy
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

BASE = ROOT / "research/agents_t314/out/LINE_INDEX_V3_0_79.json"
BASE_SHA = "0582aac58defff74c13bc23512832b258754dc4cffceff759fcbbda3e71011fb"
SETS = {   # file, pinned sha256
    "MAIN_FILL_ALL": (HERE / "MAIN_FILL_ALL.json",
                      "ad9e2c6f5d5ccdf8442d9427e6d438bdce2fd4f8c47fa7af1bf40157b5d8fd5a"),
    "T-762": (ROOT / "research/agents_t762/out/FIX_ROWS.json",
              "14ce7ca0b50a263e2decd0c4fcf97f2705421842f4a1e87211a7c60675c13db8"),
    "T-761": (ROOT / "research/agents_t761/out/FIX_ROWS.json",
              "db7c98f773f3d069b228863e436cf69bca7f98da28a12b08578e10aadf7c1588"),
}
DROP_MAIN_FILL = {
    "STR.FORMWORK": "superseded by the T-762 formwork set (Verifier T-762 Gate A 2026-11-13T16:59Z: MAIN_FILL put "
                    "the full host ratio on each partial line, double count CONFIRMED on BM-GF-048)",
    "STR.FORMWORK.STAIR": "superseded by the T-762 formwork set (same Verifier finding)",
    "STR.EARTH.DISPOSAL": "superseded by the Checker-verified T-764 disposal figure (Verifier 2026-11-13T18:25Z, "
                          "9.05 m3 AGREE); wired with the T-764 set, never twice",
}
PACKAGE = HERE / "V3081_PACKAGE.json"
OUT = HERE / "out"
V78 = "ARCH_TAKEOFF_V3.0.78"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package():
    sets, dropped, shas = [], [], {}
    for name, (p, want) in SETS.items():
        got = _sha(p)
        if want and got != want:
            raise SystemExit(f"{p.name}: sha {got[:8]} is not the pinned {want[:8]}")
        shas[name] = got
        doc = json.loads(p.read_text(encoding="utf-8"))
        if name == "MAIN_FILL_ALL":
            doc = copy.deepcopy(doc)
            keep = []
            for r in doc["rows"]:
                why = DROP_MAIN_FILL.get(r["item_code"])
                if why:
                    dropped.append({"set": name, "line_id": r["line_id"], "item_code": r["item_code"], "reason": why})
                else:
                    keep.append(r)
            doc["rows"] = keep
            doc["task"] = "MAIN_FILL_ALL"
        sets.append(doc)
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V78],
            "set_sha256": shas, "dropped": dropped, "sets": sets}


def build():
    if _sha(BASE) != BASE_SHA:
        raise SystemExit(f"{BASE.name}: sha {_sha(BASE)[:8]} is not the pinned {BASE_SHA[:8]}")
    base = json.loads(BASE.read_text(encoding="utf-8"))
    pkg = package()
    pkg_text = json.dumps(pkg, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    new, applied = A.apply_index(base, pkg, A.EXTENDS)
    added = A.check_package(pkg, A.EXTENDS)[1]
    t0, t1 = A.totals_by_code(base["lines"]), A.totals_by_code(new["lines"])
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        a, b = t0.get(k), t1.get(k)
        if a != b:
            moved[f"{k[0]} [{k[1]}]"] = {"before": {f: round(v, 2) if isinstance(v, float) else v
                                                    for f, v in (a or {}).items()},
                                         "after": {f: round(v, 2) if isinstance(v, float) else v
                                                   for f, v in (b or {}).items()}}
    by_set = {}
    for r in applied:
        s = by_set.setdefault(r["set"], {"rows": 0, "labels": {}, "after": {}})
        s["rows"] += 1
        s["labels"][r["label"]] = s["labels"].get(r["label"], 0) + 1
        s["after"][r["after"]["class"]] = s["after"].get(r["after"]["class"], 0) + 1

    def blank(lines):
        return sum(1 for ln in lines if ln["class"] == "HELD" and ln.get("held_low") is None
                   and ln.get("held_high") is None and ln["item_code"] != "STR.REBAR")

    new["inputs"] = dict(base.get("inputs") or {}, base_index=BASE_SHA,
                         fix_rows_package=hashlib.sha256(pkg_text.encode()).hexdigest())
    idx_text = json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    summary = {"method": A.METHOD, "extends": A.EXTENDS, "rule": [A.RULE, A.RULE_NET],
               "base_index_sha256": BASE_SHA, "set_sha256": pkg["set_sha256"],
               "package_sha256": hashlib.sha256(pkg_text.encode()).hexdigest(),
               "lines_before": len(base["lines"]), "lines": len(new["lines"]), "applied": len(applied),
               "added": {lid: {"item_code": x["item_code"], "unit": x["unit"], "net": x["after"]["net"],
                               "label": x["label"]} for lid, x in added.items()},
               "dropped": {k: sum(1 for d in pkg["dropped"] if d["item_code"] == k) for k in DROP_MAIN_FILL},
               "by_set": by_set, "blank_non_rebar_before": blank(base["lines"]),
               "blank_non_rebar_after": blank(new["lines"]), "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = A.diff_rows(applied, added)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_81.json": idx_text,
            OUT / "V3_0_81_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_81_DIFF.csv": buf.getvalue()}, summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    files, s = build()
    if "--check" in argv:
        bad = [p.name for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for p, t in files.items():
        p.write_text(t, encoding="utf-8")
    print("V3.0.81:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied, added",
          json.dumps(s["added"]), "| blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True), "| dropped", s["dropped"])
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
