"""T-770 r11: ARCH_TAKEOFF_V3.0.88 = the candidate of record V3.0.87 (T-770 r10, merge 91072069, line index
research/agents_t770/out/LINE_INDEX_V3_0_87.json) + two Checker-verified family groups, applied by line id under
R-T770-1 .. R-T770-8 (engine.source.arch_v3088 = FILL_WIRE_V7 unchanged, one version step):

  1. CORNICE: T-788 r2 (merged c12c8eb4, built on V3.0.86): FIN.CEILING.CORNICE 302.88 -> 426.31 lm ESTIMATE (closed rooms
     + open zones, R-T788-1 .. -3; T-799 R-T788-4 doors as barriers: cornice does not move);
  2. HELD RANGES TO POINTS: T-795 (merged 26c0b41b, built on V3.0.86): door tile edges 0 .. 73.1 -> 115.2 lm DEFAULT,
     stair-corner floor strip 0 .. 0.23 -> 0.23 m2 DRAWING-READ, two ARCH.SPACE low = high ranges carried as points.

T-791 (stairs) and T-798 (column formwork, F-V770r10-1) were not MERGED at claim: next round.

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3088_index.py [--check]

Writes V3088_PACKAGE.json (the hub's --v3088-inputs), out/LINE_INDEX_V3_0_88.json, out/V3_0_88_DIFF.csv and
out/V3_0_88_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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
from engine.source import arch_v3088 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_87.json"
BASE_SHA = "d92c44544119571cb4a2f4f310b1e3e9019e3b7b75b47f7f7c6c45a61809a75d"
SETS = {   # file, pinned sha256 (the merged fix-row sets; each equals the file at its Gate A merge)
    "T-788": (ROOT / "research/agents_t788/out/FIX_ROWS.json",
              "a490dda0f1c54ca12c4d71302c9c7c70facc1b5c8aed9d57311447cee3f1a84f"),
    "T-795": (ROOT / "research/agents_t795/out/FIX_ROWS.json",
              "86d1f5449149e113d93daa43ca3f55cb7c9c90a3046dbb1d2507a0a3e32b691d"),
}
CHECKER_SETS = {}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.86"]
PACKAGE = HERE / "V3088_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("FIN.CEILING.CORNICE", "FIN.WALL.TILE.EDGE", "FIN.FLOOR.FINISH_HELD", "ARCH.SPACE")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(table):
    docs, shas = {}, {}
    for name, (p, want) in table.items():
        got = _sha(p)
        if got != want:
            raise SystemExit(f"{p.name}: sha {got[:8]} is not the pinned {want[:8]}")
        shas[name] = got
        docs[name] = json.loads(p.read_text(encoding="utf-8"))
    return docs, shas


def package():
    sets, shas = _load(SETS)
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": ROW_BASES,
            "set_names": list(SETS) + list(CHECKER_SETS), "set_sha256": shas,
            "sets": [sets[k] for k in SETS] + [CHECKER_SETS[k] for k in CHECKER_SETS]}


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
    new, applied, late, report = A.apply_index(base, pkg)
    A87 = A.A87
    A86 = A87.A86
    A85 = A86.A85
    v7, _ = A.prepare(pkg, base["lines"])
    v6, _ = A87.prepare(v7, base["lines"])
    v5, _ = A86.prepare(v6, base["lines"], "index")
    v4, _ = A85.prepare(v5, base["lines"], "index")
    v3, _, _, _ = A85.A84.prepare(v4, base["lines"], "index")
    v1, _, _ = A85.A84.A83.prepare(v3, base["lines"], "index")
    added = B.check_package(v1, A85.A84.A83.EXTENDS)[1]
    seen = {}
    for name, doc in zip(pkg["set_names"], pkg["sets"]):   # one owner per line across the package (R-T770-8 ad, restated)
        for r in doc.get("rows") or []:
            if r["line_id"] in seen:
                raise SystemExit(f"{r['line_id']} in {seen[r['line_id']]} and {name}")
            seen[r["line_id"]] = name
    bl = {ln["line_id"]: ln for ln in base["lines"]}
    range_to_point = []   # HELD range -> RELEASED point: where the point lies against the range it replaces
    for r in applied:
        b = bl[r["line_id"]]
        if b["class"] == "HELD" and r["after"].get("class") == "RELEASED":
            lo, hi, net = b.get("held_low"), b.get("held_high"), r["after"]["net"]
            range_to_point.append({"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                                   "low": lo, "high": hi, "point": net, "label": r["label"],
                                   "inside_range": lo is not None and hi is not None and lo <= net <= hi})
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
               "added": dict({lid: {"item_code": x["item_code"], "unit": x["unit"], "net": x["after"]["net"],
                                    "label": x["label"], "set": x["set"]} for lid, x in added.items()},
                             **{x["new_line_id"]: {"item_code": x["item_code"], "unit": x["unit"], "net": x.get("net"),
                                                   "low": x.get("low"), "high": x.get("high"), "label": x["label"],
                                                   "set": x["set"], "kind": x["kind"],
                                                   "set_figure": x.get("set_figure")} for x in late}),
               "report": report, "by_set": by_set, "range_to_point": range_to_point,
               "blank_non_rebar_before": blank(base["lines"]), "blank_non_rebar_after": blank(new["lines"]),
               "ranged_non_rebar_before": ranged(base["lines"]), "ranged_non_rebar_after": ranged(new["lines"]),
               "blank_in_package_families_before": blank(base["lines"], FAMILIES),
               "blank_in_package_families_after": blank(new["lines"], FAMILIES),
               "ranged_in_package_families_before": ranged(base["lines"], FAMILIES),
               "ranged_in_package_families_after": ranged(new["lines"], FAMILIES),
               "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = A.diff_rows(applied, added, late, report)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_88.json": idx_text,
            OUT / "V3_0_88_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_88_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.88:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied,", len(s["added"]),
          "added | blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report", json.dumps({k: (len(s["report"][k]) if isinstance(s["report"][k], list) else s["report"][k]) for k in ("checker_finding_sets", "set_base_read", "no_line_rows", "basis_text_rows", "base_basis_corrections")}))
    for x in s["range_to_point"]:
        print("range -> point", json.dumps(x, sort_keys=True))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
