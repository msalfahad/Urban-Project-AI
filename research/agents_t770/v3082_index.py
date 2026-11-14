"""T-770 r5: ARCH_TAKEOFF_V3.0.82 = the candidate of record V3.0.81 (T-770 r4, merge 06302fc6, line index
research/agents_t770/out/LINE_INDEX_V3_0_81.json) + three Checker-verified family groups with the T-776 restatement,
applied by line id under R-T770-1 / R-T770-2 / R-T770-3 (engine.source.arch_v3082):

  1. T-764 earthworks B1 + top-roof waterproofing (merged 61a65c42, built on V3.0.78);
  2. T-767 waterproofing (merged 9de1dcd5, built on V3.0.78);
  3. T-769 fence, gates, pool face, outdoor floor, site (merged f8319feb, built on V3.0.79), its NOT_APPLICABLE
     dewatering entry recorded, never a line or 0;
  + T-776 boundary-wall foundation per run type (merged, built on V3.0.79): its rows restate 5 lines of T-764 /
    T-767 / T-769 (composed, R-T770-3 h1) and 4 lines T-761 / T-762 already put in V3.0.81 (R-T770-3 h2); its row on
    the boundary-wall concrete restates T-757's point, which r6 wires: DEFERRED to r6 by name (stays as V3.0.81 has it).

Named check F-V776-1 (Checker, T-776 Gate A): the building exterior GB blinding cut (T-764 line L-438a4abd, 0.50 wide x
0.10 deep) and the 0.30 band trench under the 25.02 m UNDER_BLDG free length can be the same soil: at most 25.02 x 0.30
x 0.10 m3. Computed here from the merged rows, compared with the materiality rule (DELIVERY_MODE s.3: other units,
nothing below 1 % of the family) and recorded with its outcome; never folded silently.

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3082_index.py [--check]

Writes V3082_PACKAGE.json (the hub's --v3082-inputs), out/LINE_INDEX_V3_0_82.json, out/V3_0_82_DIFF.csv and
out/V3_0_82_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
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
from engine.source import arch_v3082 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_81.json"
BASE_SHA = "3976b262611bc3bdc80e42fd2a45f1bb75dab996bc62b56d3b73987dd930f9c2"
SETS = {   # file, pinned sha256 (the merged fix-row sets)
    "T-764": (ROOT / "research/agents_t764/out/FIX_ROWS.json",
              "2e3b4f2d2c3fec1192881757762973d12d78f2dcb0fc9862f25ca0eb2b967cf5"),
    "T-767": (ROOT / "research/agents_t767/out/FIX_ROWS.json",
              "c5d98dd428637253dfe50796ed1b9b12e98b9bb398c4d26d3c6f4c72698c0b82"),
    "T-769": (ROOT / "research/agents_t769/out/FIX_ROWS.json",
              "c61cefac8024620753c1d5042e689721e634c2c65a2a7e3fa0a905ecf8601741"),
    "T-776": (ROOT / "research/agents_t776/out/FIX_ROWS.json",
              "d6d623505f155c6fe1ff06ef01c35d8c09b31ca19899202b9ff0ab2d387638b3"),
}
DEFER = {
    "L-6290a9f3d93f38cd46d6": "T-776 restates T-757's boundary-wall point 8.4588 m3 (+0.637 above the footing tops = "
                              "9.0958); T-757 is wired in T-770 r6 (Lead hub order 2026-11-14 00:20), where this row "
                              "stacks on it; until then the line stays HELD 5.6392 .. 11.0328 as V3.0.81 has it",
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.78", "ARCH_TAKEOFF_V3.0.79"]
PACKAGE = HERE / "V3082_PACKAGE.json"
OUT = HERE / "out"
GB_BLINDING_CUT = "L-438a4abd3adc0475d0bd"     # T-764: building exterior GB blinding cut 55.99 x 0.50 x 0.10
BAND_TRENCH = "L-313384fed48301ae02d2"         # T-764 -> T-776: boundary band trench
MATERIALITY_SHARE = 0.01                       # DELIVERY_MODE s.3: other units, nothing below 1 %


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package():
    sets, shas = [], {}
    for name, (p, want) in SETS.items():
        got = _sha(p)
        if got != want:
            raise SystemExit(f"{p.name}: sha {got[:8]} is not the pinned {want[:8]}")
        shas[name] = got
        doc = json.loads(p.read_text(encoding="utf-8"))
        if (doc.get("task") or doc.get("set")) != name:
            raise SystemExit(f"{p}: set names {doc.get('task')}, expected {name}")
        sets.append(doc)
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": ROW_BASES,
            "set_sha256": shas, "defer": DEFER, "sets": sets}


def named_check_f_v776_1(pkg, new_lines):
    """F-V776-1 from the merged rows: overlap bound vs the materiality of the B1 excavation family."""
    t776 = next(s for s in pkg["sets"] if s["task"] == "T-776")
    under = t776["run_types"]["UNDER_BLDG"]
    width = 0.30           # T-776 basis: band trench 0.30 (A-A, flush on the plot line, 10 past the inner face)
    depth = 0.10           # T-764 basis of L-438a4abd: blinding cut 0.10
    bound = round(under["free_m"] * width * depth, 6)
    by = {ln["line_id"]: ln for ln in new_lines}
    exc = sum(float(ln["measured_net"]) for ln in new_lines
              if ln["item_code"] == "STR.EARTH.EXCAVATION" and ln["class"] == "RELEASED")
    share = bound / exc
    return {"finding": "F-V776-1", "lines": [GB_BLINDING_CUT, BAND_TRENCH],
            "gb_blinding_cut_m3": by[GB_BLINDING_CUT]["measured_net"], "band_trench_m3": by[BAND_TRENCH]["measured_net"],
            "overlap_bound_m3": bound, "basis": f"UNDER_BLDG free {under['free_m']} m x band trench {width} x GB "
                                                f"blinding cut {depth} (the T-776 band_blinding figure of that run)",
            "b1_excavation_released_m3": round(exc, 6), "share_of_b1_excavation": round(share, 6),
            "share_of_band_trench": round(bound / float(by[BAND_TRENCH]["measured_net"]), 6),
            "outcome": ("BELOW MATERIALITY: named, not deducted; both lines and the disposal balance stay as the "
                        "Checker-verified rows give them (disposal at most this much high)")
            if share < MATERIALITY_SHARE else "MATERIAL: a fix row is needed (not wired here)"}


def build():
    if _sha(BASE) != BASE_SHA:
        raise SystemExit(f"{BASE.name}: sha {_sha(BASE)[:8]} is not the pinned {BASE_SHA[:8]}")
    base = json.loads(BASE.read_text(encoding="utf-8"))
    pkg = package()
    pkg_text = json.dumps(pkg, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    new, applied, report = A.apply_index(base, pkg)
    v1, _ = A.stack_package(pkg, base["lines"], "index")
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
        s = by_set.setdefault(r["set"], {"rows": 0, "labels": {}})
        s["rows"] += 1
        s["labels"][r["label"]] = s["labels"].get(r["label"], 0) + 1

    def blank(lines, prefixes=None):
        return sum(1 for ln in lines if ln["class"] == "HELD" and ln.get("held_low") is None
                   and ln.get("held_high") is None and ln["item_code"] != "STR.REBAR"
                   and (prefixes is None or ln["item_code"].startswith(prefixes)))

    fam = ("STR.EARTH", "FIN.WP", "WP.", "EXT.FENCE", "EXT.POOL", "EXT.FLOOR", "SITE.")
    check = named_check_f_v776_1(pkg, new["lines"])
    new["inputs"] = dict(base.get("inputs") or {}, base_index=BASE_SHA,
                         fix_rows_package=hashlib.sha256(pkg_text.encode()).hexdigest())
    idx_text = json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    summary = {"method": A.METHOD, "extends": A.EXTENDS, "rule": A.RULES,
               "base_index_sha256": BASE_SHA, "set_sha256": pkg["set_sha256"],
               "package_sha256": hashlib.sha256(pkg_text.encode()).hexdigest(),
               "lines_before": len(base["lines"]), "lines": len(new["lines"]), "applied": len(applied),
               "added": {lid: {"item_code": x["item_code"], "unit": x["unit"], "net": x["after"]["net"],
                               "label": x["label"], "set": x["set"]} for lid, x in added.items()},
               "stack_report": report, "by_set": by_set,
               "blank_non_rebar_before": blank(base["lines"]), "blank_non_rebar_after": blank(new["lines"]),
               "blank_in_package_families_before": blank(base["lines"], fam),
               "blank_in_package_families_after": blank(new["lines"], fam),
               "named_check": check, "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = B.diff_rows(applied, added)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_82.json": idx_text,
            OUT / "V3_0_82_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_82_DIFF.csv": buf.getvalue()}, summary


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
    print("V3.0.82:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied, added",
          json.dumps(s["added"]), "| blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| package families", s["blank_in_package_families_before"], "->", s["blank_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("stack", json.dumps({k: len(v) for k, v in s["stack_report"].items()}))
    print("named check", json.dumps(s["named_check"], sort_keys=True))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
