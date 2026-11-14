"""T-770 r6: ARCH_TAKEOFF_V3.0.83 = the candidate of record V3.0.82 (T-770 r5, merge 26a82725, line index
research/agents_t770/out/LINE_INDEX_V3_0_82.json) + three Checker-verified family groups and the one T-776 row r5
deferred, applied by line id under R-T770-1 .. R-T770-4 (engine.source.arch_v3083):

  1. T-757 concrete points (merged 951682c5, built on V3.0.79): 114 rows to points by the materiality rule, and the
     ONE safety line restated 1.00 -> 1.1997 m3 (R-T770-4 n: the T-761 ignored pieces 0.4282 + the T-757 unresolved
     widths 0.7715; never a second safety line);
  2. T-763 plaster / paint (merged 2c6a2822, built on V3.0.81): 90 rows (F-04 heights 4.34 / 4.04);
  3. T-765 masonry (merged 3b9f35a6, built on V3.0.81): 78 figure rows + 13 NOT_APPLICABLE rows (R-T770-4 m: the line
     becomes EXCLUDED with its evidence, never 0); Checker F-V765-1 corrects one component's basis text
     (R-T770-4 o; the figure is left as verified);
  + T-776 (merged, built on V3.0.79): only its boundary-wall row L-6290a9f3 (R-T770-4 l: its other 9 rows and its added
    band-blinding line are in V3.0.82 since r5); it restates T-757's point 8.4588 of the same line and composes with it
    (R-T770-3 h1).

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3083_index.py [--check]

Writes V3083_PACKAGE.json (the hub's --v3083-inputs), out/LINE_INDEX_V3_0_83.json, out/V3_0_83_DIFF.csv and
out/V3_0_83_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3083 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_82.json"
BASE_SHA = "e51909257a5d688ff9be64f687560464acac4303f3ebc176d5d1ed820c9656ec"
SETS = {   # file, pinned sha256 (the merged fix-row sets)
    "T-757": (ROOT / "research/agents_t757/out/FIX_ROWS.json",
              "155ed1b3be8eef37d5d8c984e50585f2cf236ed5b5105ec808048db086dcdfd7"),
    "T-763": (ROOT / "research/agents_t763/out/FIX_ROWS.json",
              "419b3f359a24bda1dd6e4173cc176f9b38e92768ca5c2fecd4e5699f602da712"),
    "T-765": (ROOT / "research/agents_t765/out/FIX_ROWS.json",
              "5e2a1ca35b40c6802249edcba28d92629fe51b4330a0557b2b79af137edd54a8"),
    "T-776": (ROOT / "research/agents_t776/out/FIX_ROWS.json",
              "d6d623505f155c6fe1ff06ef01c35d8c09b31ca19899202b9ff0ab2d387638b3"),
}
CARRY = {"T-776": ["L-6290a9f3d93f38cd46d6"]}   # r5 deferred it by name (V3082_PACKAGE.json defer)
BASIS_CORRECTIONS = {
    "L-c22e309433e7b671cf2d": {
        "old": "1F-W14+W15 16.5255 (4.0927 x 4.04",
        "new": "1F-W14+W15 16.5345 (4.0927 x 4.04",
        "source": "Checker F-V765-1 (T-765 Gate A, 2026-11-14): 4.0927 x 4.04 = 16.5345; the line figure 64.8492 is "
                  "left as verified (0.009 m2 under the corrected components, below materiality)"},
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.79", "ARCH_TAKEOFF_V3.0.81"]
PACKAGE = HERE / "V3083_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("STR.CONC", "FIN.PLASTER", "FIN.PAINT", "MAS.")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package():
    sets, shas = [], {}
    for name, (p, want) in SETS.items():
        got = _sha(p)
        if got != want:
            raise SystemExit(f"{p.name}: sha {got[:8]} is not the pinned {want[:8]}")
        shas[name] = got
        sets.append(json.loads(p.read_text(encoding="utf-8")))
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": ROW_BASES,
            "set_names": list(SETS), "set_sha256": shas, "carry": CARRY, "basis_corrections": BASIS_CORRECTIONS,
            "sets": sets}


def blank(lines, prefixes=None):
    return sum(1 for ln in lines if ln["class"] == "HELD" and ln.get("held_low") is None
               and ln.get("held_high") is None and ln["item_code"] != "STR.REBAR"
               and (prefixes is None or ln["item_code"].startswith(prefixes)))


def ranged(lines, prefixes=None):
    return sum(1 for ln in lines if ln["class"] == "HELD" and not (ln.get("held_low") is None
               and ln.get("held_high") is None) and ln["item_code"] != "STR.REBAR"
               and (prefixes is None or ln["item_code"].startswith(prefixes)))


def build():
    if _sha(BASE) != BASE_SHA:
        raise SystemExit(f"{BASE.name}: sha {_sha(BASE)[:8]} is not the pinned {BASE_SHA[:8]}")
    base = json.loads(BASE.read_text(encoding="utf-8"))
    pkg = package()
    pkg_text = json.dumps(pkg, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    new, applied, report = A.apply_index(base, pkg)
    v1, _, _ = A.prepare(pkg, base["lines"], "index")
    added = B.check_package(v1, A.EXTENDS)[1]
    t0, t1 = B.totals_by_code(base["lines"]), B.totals_by_code(new["lines"])
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
        s = by_set.setdefault(r.get("set_doc") or r["set"], {"rows": 0, "labels": {}})
        s["rows"] += 1
        s["labels"][r["label"]] = s["labels"].get(r["label"], 0) + 1
    new["inputs"] = dict(base.get("inputs") or {}, base_index=BASE_SHA,
                         fix_rows_package=hashlib.sha256(pkg_text.encode()).hexdigest())
    idx_text = json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    summary = {"method": A.METHOD, "extends": A.EXTENDS, "rule": A.RULES,
               "base_index_sha256": BASE_SHA, "set_sha256": pkg["set_sha256"],
               "package_sha256": hashlib.sha256(pkg_text.encode()).hexdigest(),
               "lines_before": len(base["lines"]), "lines": len(new["lines"]), "applied": len(applied),
               "added": {lid: {"item_code": x["item_code"], "unit": x["unit"], "net": x["after"]["net"],
                               "label": x["label"], "set": x["set"]} for lid, x in added.items()},
               "report": report, "by_set": by_set,
               "blank_non_rebar_before": blank(base["lines"]), "blank_non_rebar_after": blank(new["lines"]),
               "ranged_non_rebar_before": ranged(base["lines"]), "ranged_non_rebar_after": ranged(new["lines"]),
               "blank_in_package_families_before": blank(base["lines"], FAMILIES),
               "blank_in_package_families_after": blank(new["lines"], FAMILIES),
               "ranged_in_package_families_before": ranged(base["lines"], FAMILIES),
               "ranged_in_package_families_after": ranged(new["lines"], FAMILIES),
               "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = A.diff_rows(applied, added)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_83.json": idx_text,
            OUT / "V3_0_83_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_83_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.83:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied, added",
          json.dumps(s["added"]), "| blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report", json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in s["report"].items()}))
    print("restated safety", json.dumps(s["report"]["restated_safety"]))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
