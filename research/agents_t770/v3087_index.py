"""T-770 r10: ARCH_TAKEOFF_V3.0.87 = the candidate of record V3.0.86 (T-770 r9, merge 9be5f69a, line index
research/agents_t770/out/LINE_INDEX_V3_0_86.json) + two Checker-verified family groups and one Checker finding, applied by
line id under R-T770-1 .. R-T770-8 (engine.source.arch_v3087):

  1. CONCRETE: T-786 (merged a2001238, built on V3.0.85): 11 roof-edge projection bands from the 0.60 beam default to the
     0.16 printed slab thickness (UNMARKED_PIECE_DEPTH_V1); Checker F-V786-1 (T-786 Gate A, 2026-11-14T14:05Z): the two
     column-front strips in the same band, 0.16 m2 x 0.16 = 0.0256 m3 each (R-T770-8 ac); T-792 (merged 9ff810ac, built
     on V3.0.85): the two schedule-first column rows (10AE GF 0.31 -> 0.3875, 10E0 1F 0.84 -> 0.672 m3);
  2. ROOF UPTURN: T-794 (merged 8f558cef, built on V3.0.85): door D115 (1.00 lm) and the ledge glazing BCE (2.977 lm)
     out of FIN.WP.ROOF_UPTURN to their own transition / termination lines (3 added).

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3087_index.py [--check]

Writes V3087_PACKAGE.json (the hub's --v3087-inputs), out/LINE_INDEX_V3_0_87.json, out/V3_0_87_DIFF.csv and
out/V3_0_87_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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
from engine.source import arch_v3087 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_86.json"
BASE_SHA = "350770c0a813491f8c6ea3569b55f3fb6d972184b8e1d525a6e547cff7244187"
SETS = {   # file, pinned sha256 (the merged fix-row sets; each equals the file at its Gate A merge)
    "T-786": (ROOT / "research/agents_t786/out/FIX_ROWS.json",
              "1b60dce5293b90c3389b713ca2b7df9c94c0318ecf43e261c9f696124a6071bf"),
    "T-792": (ROOT / "research/agents_t792/out/FIX_ROWS.json",
              "d699fdb6b93ec39dced27aadc455dadc031a7560c83df9748e2b6465fb74d8a1"),
    "T-794": (ROOT / "research/agents_t794/out/FIX_ROWS.json",
              "e2e5859e286597e7765623d95432976026ef4bee4313689de158939e93bf7632"),
}
_FV = ("Checker F-V786-1 (T-786 Gate A light, 2026-11-14T14:05Z): the {f} strip at the column at {b}'s end lies in the "
       "same roof-edge band, between the same outer line, as the T-786 projection bands, so by UNMARKED_PIECE_DEPTH_V1 it "
       "is PROJECTION_BAND: plan 0.16 m2 (T-724 census) x 0.16 printed slab thickness (ST note 18) = 0.0256 m3; was "
       "0.0960 at the 0.60 beam default; D-05 replaces it")
CHECKER_SETS = {   # R-T770-8 ac: the Checker's own fix rows, restated from its verdict (no new measurement)
    "F-V786-1": {
        "schema": "URBAN_FIX_ROWS_V1", "task": "F-V786-1", "kind": "CHECKER_FINDING", "finding": "F-V786-1",
        "verdict": {"task": "T-786", "gate": "A light", "utc": "2026-11-14T14:05Z", "merge": "a2001238"},
        "candidate_version": "ARCH_TAKEOFF_V3.0.86",
        "rows": [
            {"line_id": "L-f113ed57f7875fed9a67", "item_code": "STR.CONC.BEAM", "unit": "m3",
             "element_id": "T729:CHILD:HL:BEAM_LEDGER:GF:BM-GF-058#GF-STRIP-AT-COL",
             "before": {"class": "RELEASED", "net": 0.096, "label": "DEFAULT"},
             "after": {"class": "RELEASED", "net": 0.0256}, "label": "DEFAULT", "hand": [0.16, 0.16],
             "basis": _FV.format(f="GF", b="B20")},
            {"line_id": "L-56c49c3c2596a0869533", "item_code": "STR.CONC.BEAM", "unit": "m3",
             "element_id": "T729:CHILD:HL:BEAM_LEDGER:1F:BM-1F-033#1F-STRIP-AT-COL",
             "before": {"class": "RELEASED", "net": 0.096, "label": "DEFAULT"},
             "after": {"class": "RELEASED", "net": 0.0256}, "label": "DEFAULT", "hand": [0.16, 0.16],
             "basis": _FV.format(f="1F", b="B23")},
        ]},
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.85"]
PACKAGE = HERE / "V3087_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("STR.CONC.BEAM", "STR.CONC.COLUMN", "FIN.WP.ROOF_UPTURN", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP.TERMINATION")


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
    A86 = A.A86
    A85 = A86.A85
    v6, _ = A.prepare(pkg, base["lines"])
    v5, _ = A86.prepare(v6, base["lines"], "index")
    v4, _ = A85.prepare(v5, base["lines"], "index")
    v3, _, _, _ = A85.A84.prepare(v4, base["lines"], "index")
    v1, _, _ = A85.A84.A83.prepare(v3, base["lines"], "index")
    added = B.check_package(v1, A85.A84.A83.EXTENDS)[1]
    tr = [ln for ln in base["lines"] if "D115" in str(ln.get("element_id")) or "glazing BCE" in str(ln.get("element_id"))]
    if tr:   # the T-794 transition / termination lines are wired once
        raise SystemExit(f"base already carries a T-794 line {tr[0]['line_id']}")
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
    d = A.diff_rows(applied, added, late, report)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_87.json": idx_text,
            OUT / "V3_0_87_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_87_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.87:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied,", len(s["added"]),
          "added | blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report", json.dumps({k: (len(s["report"][k]) if isinstance(s["report"][k], list) else s["report"][k]) for k in ("checker_finding_sets", "set_base_read", "no_line_rows", "basis_text_rows", "base_basis_corrections")}))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
