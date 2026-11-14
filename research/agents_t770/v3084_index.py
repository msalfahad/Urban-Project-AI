"""T-770 r7: ARCH_TAKEOFF_V3.0.84 = the candidate of record V3.0.83 (T-770 r6, merge 35963c4d, line index
research/agents_t770/out/LINE_INDEX_V3_0_83.json) + three Checker-verified family groups, applied by line id under
R-T770-1 .. R-T770-5 (engine.source.arch_v3084):

  1. T-766 stair finishes (merged b0034c54, built on V3.0.81): 66 rows + 2 landing ADDs (MS1-LD, RS-LD); the 18
     sloped-skirting form alternatives (ORR-007) become EXCLUDED_WITH_REASON (R-T770-5 r, Checker F-V766-1: never 0,
     never additive with the zigzag line); the 4 open-side rows EXCLUDED with evidence (R-T770-4 m);
  2. T-768 openings / ceilings / domes (merged eda8232a, built on V3.0.81): 34 figure rows + 9 EXCLUDED rows
     (R-T770-4 m / R-T770-5 r); dome soffit kept at the verified 24.15 (Checker F-V768-1 optional, -0.4 %, below 1 %);
  3. T-771 missing families (merged 88e4b912, built on V3.0.81): 23 added entries: 17 figures, 3 ranges kept HELD
     (R-T770-5 s; mesh strip and sharmat OPTIONAL), the carrier-derived lines recomputed on the wired candidate
     (R-T770-5 t: interior / fence spatter dash = FIN.PLASTER / EXT.FENCE.PLASTER, gypsum board = FIN.CEILING after
     T-768, nosing = FIN.STAIR.STEP_LM after T-766 + the 7.40 lm T-412 landing edges; Checker F-V766-2: nosing wired
     once, here); the exterior spatter line is DEFERRED by name (R-T770-5 u): its carrier FIN.EXT.FINISH is still HELD
     because the merged T-760 set (exterior render / paint) is not wired yet.

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3084_index.py [--check]

Writes V3084_PACKAGE.json (the hub's --v3084-inputs), out/LINE_INDEX_V3_0_84.json, out/V3_0_84_DIFF.csv and
out/V3_0_84_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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
from engine.source import arch_v3084 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_83.json"
BASE_SHA = "f3a81dfe753f81901adeea07d318aae82d20f729e75ead43bbf3b7abac4a78fe"
SETS = {   # file, pinned sha256 (the merged fix-row sets)
    "T-766": (ROOT / "research/agents_t766/out/FIX_ROWS.json",
              "f97c2c91631316fa1ee7ea4a4f18300a32a1519b847a5eccec38cf81cca6234b"),
    "T-768": (ROOT / "research/agents_t768/out/FIX_ROWS.json",
              "1f31fc5bc68bb64afc7069de1ea42cd9524d5cca1807ae732c2275b28b265b3d"),
    "T-771": (ROOT / "research/agents_t771/out/FIX_ROWS.json",
              "5eb803cdd7c6e16424ef2560c6f194c4d631eb6bb84e8e6ac00c623662cd863f"),
}
CARRIERS = {   # R-T770-5 t: the carrier each T-771 line names in its own basis ('recompute at wiring')
    "SPATTER:INTERIOR": {"carrier": ["FIN.PLASTER", "m2"]},
    "SPATTER:FENCE": {"carrier": ["EXT.FENCE.PLASTER", "m2"]},
    "CEILING:GYPSUM_DECOR": {"carrier": ["FIN.CEILING", "m2"]},
    "STAIR:NOSING": {"carrier": ["FIN.STAIR.STEP_LM", "lm"], "plus": 7.40,
                     "plus_source": "T-412 landing / floor arrival nosing edges, DRAWING-CONFIRMED (T-771 basis)"},
}
DEFER_ADDED = {   # R-T770-5 u
    "SPATTER:EXTERIOR": "carrier FIN.EXT.FINISH is HELD in V3.0.83 (17 ranged + 1 blank): the merged T-760 exterior "
                        "render / paint set (Gate A 89be1473) is not wired yet; this line is wired with T-760 in the "
                        "next T-770 round (recomputed from the wired carrier, R-T770-5 t)",
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.81"]
PACKAGE = HERE / "V3084_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("FIN.MARBLE.", "FIN.STAIR.", "ARCH.", "DOOR.", "FIN.CEILING", "FIN.DOME.")


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
            "set_names": list(SETS), "set_sha256": shas, "carriers": CARRIERS, "defer_added": DEFER_ADDED,
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
    new, applied, late, report = A.apply_index(base, pkg)
    v3, _, _, _ = A.prepare(pkg, base["lines"], "index")
    v1, _, _ = A.A83.prepare(v3, base["lines"], "index")
    added = B.check_package(v1, A.A83.EXTENDS)[1]
    nosing = [ln for ln in base["lines"] if ln["item_code"] == "FIN.STAIR.NOSING"]
    if nosing:   # Checker F-V766-2: the B7-05 nosing line is wired once (T-771)
        raise SystemExit(f"base already carries {len(nosing)} FIN.STAIR.NOSING line(s)")
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
    d = A.diff_rows(applied, added, late)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_84.json": idx_text,
            OUT / "V3_0_84_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_84_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.84:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied, added",
          json.dumps(s["added"]), "| blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report", json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in s["report"].items()}))
    print("deferred added", json.dumps(s["report"]["deferred_added"]))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
