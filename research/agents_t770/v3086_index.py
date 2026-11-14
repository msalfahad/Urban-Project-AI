"""T-770 r9: ARCH_TAKEOFF_V3.0.86 = the candidate of record V3.0.85 (T-770 r8, merge c5b79f10, line index
research/agents_t770/out/LINE_INDEX_V3_0_85.json) + three Checker-verified family groups and the Checker's two basis-text
corrections, applied by line id under R-T770-1 .. R-T770-7 (engine.source.arch_v3086):

  1. T-787 dome extrados (merged 21646f39, built on V3.0.84): 7 added lines: FIN.WP.ROOF + FIN.ROOF.PROTECTION on each
     of the 3 dome shells (spherical cap pi (a^2 + h^2), a 2.21, h 1.90 = 26.685 m2 each) + 12 membrane rolls;
  2. T-789 masonry open items (merged 7113111b, built on V3.0.84): the 4 parapet-block NO_LINE rows (0 m2, complement of
     the wired STR.CONC.PARAPET lines: recorded, never written, R-T770-7 z) + the MAIN_S below-ground block basis
     restatement (BASIS_TEXT, figure unchanged, R-T770-7 aa);
  3. T-790 blockwork views (merged 28d6336e, built on V3.0.85): 24 ARCH.WALL_PANEL / ARCH.WALL_VOLUME reference views =
     the MAS.BLOCK line of the same group, 2 GF t=0.40 views NOT_APPLICABLE (R-T770-4 m), mesh strip and sharmat points;
  4. BASE BASIS CORRECTIONS (R-T770-7 ab, Checker F-V770r8-1, no figure moves): the 1F parapet outer render line and the
     four +9.70 roof-layer lines.

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3086_index.py [--check]

Writes V3086_PACKAGE.json (the hub's --v3086-inputs), out/LINE_INDEX_V3_0_86.json, out/V3_0_86_DIFF.csv and
out/V3_0_86_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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
from engine.source import arch_v3086 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_85.json"
BASE_SHA = "878e9a629435932479415d6fb01d15e56edd719851b8c8d0543a0a45000a47fa"
SETS = {   # file, pinned sha256 (the merged fix-row sets; each equals the file at its Gate A merge)
    "T-787": (ROOT / "research/agents_t787/out/FIX_ROWS.json",
              "eabfb415ddc3bf3d8a23cd84a4aad9b0b1fb65df32b9b8dba842788ff3940ff9"),
    "T-789": (ROOT / "research/agents_t789/out/FIX_ROWS.json",
              "7783b7c12108d9ecf620d44c8b25c5d8d64bebc8c9a322f626bddcffeb6dd56d"),
    "T-790": (ROOT / "research/agents_t790/out/FIX_ROWS.json",
              "555a00b8f0049b37aef03841ede50bc6b33a67d8f099ce96be96b2baea2b0c97"),
}
_F1 = "Checker F-V770r8-1 (T-770 r8 Gate B, 2026-11-14T11:49Z): the figure already holds the minimum heights"
_F2 = ("Checker F-V770r8-1 (T-770 r8 Gate B, 2026-11-14T11:49Z): 146.532 - 2 x 15.359 = 115.814 already equals the "
       "line; the drawn band is inside the face")
_ROOF_OLD = "(B4 rings, Q-44 A) + drawn band 0.1575 = membrane line"
_ROOF_NEW = "(B4 rings, Q-44 A) = membrane line"
BASE_BASIS_CORRECTIONS = {   # R-T770-7 ab: text only, no figure moves
    "L-5a04a3ec70ce025ddd95": {"old": "54.651 low + NE-1 / SW-1 0.08 x 1.20 + SW-2 4.40 x 1.20 = 5.280",
                               "new": "54.651 low (minimum heights) + SW-2 4.40 x (1.20 - 0.385) + NE-1 / SW-1 "
                                      "2 x 0.08 x (1.20 - 1.10) = 58.253",
                               "source": _F1},
    "L-122cbab32ca719527de8": {"old": _ROOF_OLD, "new": _ROOF_NEW, "source": _F2},
    "L-e005eb9041acb08d8b87": {"old": _ROOF_OLD, "new": _ROOF_NEW, "source": _F2},
    "L-e0dc4455bc0c6ee4fa9b": {"old": _ROOF_OLD, "new": _ROOF_NEW, "source": _F2},
    "L-f4ae7151a6e2b93dd7ad": {"old": _ROOF_OLD, "new": _ROOF_NEW, "source": _F2},
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.84"]
PACKAGE = HERE / "V3086_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("FIN.WP.ROOF", "FIN.ROOF.", "FIN.WP.MEMBRANE_ROLLS", "MAS.", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME")


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
            "set_names": list(SETS), "set_sha256": shas, "base_basis_corrections": BASE_BASIS_CORRECTIONS,
            "sets": [sets[k] for k in SETS]}


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
    A85 = A.A85
    v5, _ = A.prepare(pkg, base["lines"], "index")
    v4, _ = A85.prepare(v5, base["lines"], "index")
    v3, _, _, _ = A85.A84.prepare(v4, base["lines"], "index")
    v1, _, _ = A85.A84.A83.prepare(v3, base["lines"], "index")
    added = B.check_package(v1, A85.A84.A83.EXTENDS)[1]
    ext = [ln for ln in base["lines"] if "EXTRADOS" in str(ln.get("element_id"))]
    if ext:   # the dome extrados lines are wired once
        raise SystemExit(f"base already carries a dome extrados line {ext[0]['line_id']}")
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
            OUT / "LINE_INDEX_V3_0_86.json": idx_text,
            OUT / "V3_0_86_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_86_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.86:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied,", len(s["added"]),
          "added | blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report", json.dumps({k: (len(s["report"][k]) if isinstance(s["report"][k], list) else s["report"][k]) for k in ("set_base_read", "no_line_rows", "basis_text_rows", "base_basis_corrections")}))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
