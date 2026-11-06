"""T-560 development-villa build: B11 reinforcement, candidate ARCH_TAKEOFF_V3.0.58 vs the freelancer, by scope group.

Engine: research/agents_t507/out/LINE_INDEX_V3_0_57.json (sha pinned; V3.0.58 = V3.0.57 + 5 FIN.WP.ROOF lines, the
4,994 others byte-identical per T-507 s.6, so every STR.REBAR line is the V3.0.58 line). Benchmark: the committed B1
census tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file RC, summary sheet), re-read this run from the Drive
workbook (sha ae608411, equal to the B1 manifest): only family totals are used, no element row.

Usage: python3 -I research/agents_t560/t560_alsenan.py [--check]
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import t560_rules as R  # noqa: E402

LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
LINE_INDEX_SHA = "fed5141e"   # first 8 of sha256, asserted in build()
CENSUS_SHA = "752c9f4e"
CENSUS = ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
OUT = ROOT / "research/agents_t560/out/T560_REBAR_RECONCILE.json"

# Benchmark families: summary-sheet row -> (family, concrete cell, steel cell); header H13 prints the unit (t).
BENCH_ROWS = {17: "FOOTINGS", 18: "GROUND_BEAMS_AND_SLAB", 19: "WALLS_AND_COLUMNS", 20: "BEAMS", 21: "SLABS",
              22: "STAIRS_AND_DOME", 23: "POOL"}
BENCH_TOTAL_ROW = 25

# R-T560-4 groups (smallest common scope). His footings sheet holds pads, raft, straps AND a perimeter ground beam,
# his ground sheet the ground slab, the ground beams and the fence ground beam: the two cross the engine split
# (footings / ground system / ground slab), so they are compared together.
GROUPS = {
    "G1_SUBSTRUCTURE": {"engine": ["FRP:FTG", "HL:GROUND_SYSTEM_STEEL", "P-S:GROUND_SLAB", "P-S:GROUND_BEAMS"],
                        "bench": ["FOOTINGS", "GROUND_BEAMS_AND_SLAB"]},
    "G2_COLUMNS_NECKS_WALLS": {"engine": ["HL:COLUMN_STEEL", "P-S:NECK", "P-S:COL"], "bench": ["WALLS_AND_COLUMNS"]},
    "G3_BEAMS": {"engine": ["HL:BEAM_STEEL", "LIFT_TIE_BEAM:GF", "P-S:BEAMS", "U-S:BEAMS"], "bench": ["BEAMS"]},
    "G4_SLABS": {"engine": ["HL:SLAB_STEEL", "P-S:SLABS"], "bench": ["SLABS"]},
    "G5_STAIRS_DOME": {"engine": ["STAIR:ST"], "bench": ["STAIRS_AND_DOME"]},
    "G6_POOL": {"engine": ["STAIR:POOL"], "bench": ["POOL"]},
    "G7_TANK": {"engine": ["STAIR:TANK"], "bench": []},
}
# Scope items in one list only (element whose concrete the candidate carries, with no STR.REBAR line), by group.
SCOPE = {
    "G2_COLUMNS_NECKS_WALLS": ["LIFT_PIT:WALLS: concrete line STR.CONC.LIFT HELD in the candidate, no STR.REBAR line "
                               "(his walls-and-columns family includes the lift walls)"],
    "G5_STAIRS_DOME": ["HL:DOME_SHELL / HL:DOME_RING / DG5 dome lines: concrete in the candidate (DOME-A shell 2.540681 "
                       "m3 valued, rings), no STR.REBAR line with a dome element id (his family is stairs + dome)"],
    "G7_TANK": ["TANK: engine rebar line HELD blank; the benchmark has no tank family (NO_ROW)"],
}


def sha8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def engine_family(eid: str) -> str:
    p = eid.split(":")
    if p[0] == "HL" and p[1] == "STAIR_POOL_TANK_STEEL":
        return "STAIR:" + ("ST" if p[2].startswith("ST-") else p[2])
    return ":".join(p[:2])


def bar_group(eid: str) -> str:
    last = eid.split(":")[-1].split("#")[0]
    return re.sub(r"\d+", "#", last)


def read_bench():
    rows = json.load(open(CENSUS, encoding="utf-8"))["rows"]
    summ = {r["row"]: r["cells"] for r in rows if r["file"] == "RC" and r["sheet"] == "ورقة1"}
    header = summ[13]["H13"]["v"]
    if "طن" not in header:
        raise ValueError("benchmark steel header does not print t")
    if summ[BENCH_TOTAL_ROW]["I25"]["v"].strip() != "طن":
        raise ValueError("benchmark total unit not t")
    fams = {}
    for r, fam in BENCH_ROWS.items():
        c = summ[r]
        h = c[f"H{r}"]
        t = R.bench_value(h["v"], "t")
        conc = Decimal(repr(c[f"E{r}"]["v"]))
        fams[fam] = {"t": t, "formula": h["f"], "basis": R.classify_basis(False, h["f"]),
                     "own_concrete_m3": R.d6(conc), "implied_kg_per_m3": R.plausible_t(t, conc),
                     "round_rate_interval_kg_m3": [str(x) for x in R.rate_interval(t, conc)]}
    tot = summ[BENCH_TOTAL_ROW]["H25"]
    total = R.bench_value(tot["v"], "t")
    return fams, total, tot["f"]


def build():
    raw = LINE_INDEX.read_bytes()
    if hashlib.sha256(raw).hexdigest()[:8] != LINE_INDEX_SHA or sha8(CENSUS) != CENSUS_SHA:
        raise ValueError("input changed: re-pin the line index / census after review")
    d = json.loads(raw)
    lines = [ln for ln in d["lines"] if ln["item_code"] == "STR.REBAR"]
    fams = {}
    groups_by_fam = {}
    for ln in lines:
        f = engine_family(ln["element_id"])
        fams.setdefault(f, []).append(ln)
        groups_by_fam.setdefault(f, {}).setdefault(bar_group(ln["element_id"]), []).append(ln)
    bench, bench_total, bench_total_formula = read_bench()
    R.check_groups(GROUPS, fams.keys(), bench.keys())
    fam_parts = {f: R.engine_parts(ls) for f, ls in sorted(fams.items())}
    all_parts = R.add_parts(fam_parts.values())
    table = {}
    for gid, g in GROUPS.items():
        eng = R.add_parts([fam_parts[f] for f in g["engine"]])
        his = R.d6(sum((bench[b]["t"] for b in g["bench"]), Decimal(0))) if g["bench"] else None
        blanks = sorted({f"{f}:{bg}" for f in g["engine"] for bg, ls in groups_by_fam[f].items()
                         if any(x["class"] == "HELD" and x["held_low"] is None for x in ls)})
        c = R.causes(his, eng, "TYPED_LUMP", SCOPE.get(gid, ()), blanks)
        table[gid] = {"engine_families": g["engine"], "bench_families": g["bench"], "engine_kg": eng, **c}
    # closures (acceptance): the group table re-adds to both totals exactly
    his_sum = R.d6(sum((v["his_t"] for v in table.values() if v["his_t"] is not None), Decimal(0)))
    assert his_sum == bench_total, (his_sum, bench_total)
    re_add = R.add_parts([v["engine_kg"] for v in table.values()])
    assert re_add == all_parts, (re_add, all_parts)
    out = {
        "schema": "URBAN_T560_REBAR_TONNAGE_RECONCILE_V1",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (STR.REBAR lines = V3.0.57 line index, byte-identical per T-507 s.6)",
        "inputs": {"line_index": str(LINE_INDEX.relative_to(ROOT)), "line_index_sha256": hashlib.sha256(raw).hexdigest(),
                   "census": str(CENSUS.relative_to(ROOT)), "census_sha256": hashlib.sha256(CENSUS.read_bytes()).hexdigest()},
        "engine_lines": len(lines),
        "engine_totals_kg": all_parts,
        "engine_totals_t": {"valued": R.to_t(all_parts["valued_kg"], "kg"),
                            "held_low": R.to_t(all_parts["held_low_kg"], "kg"),
                            "held_high": R.to_t(all_parts["held_high_kg"], "kg"),
                            "held_blank_lines": all_parts["held_blank"], "excluded_lines": all_parts["excluded"]},
        "engine_families_kg": fam_parts,
        "engine_bar_groups_kg": {f: {bg: R.engine_parts(ls) for bg, ls in sorted(bgs.items())}
                                 for f, bgs in sorted(groups_by_fam.items())},
        "bench": {"families": bench, "total_t": bench_total, "total_formula": bench_total_formula,
                  "total_equals_family_sum": his_sum == bench_total,
                  "bar_rows_in_workbook": 0, "basis": "TYPED_LUMP"},
        "groups": table,
    }
    return out


def dumps(o) -> str:
    return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    o = build()
    s = dumps(o)
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != s:
            print("T560 CHECK FAIL: rebuilt output differs")
            return 1
        print("T560 CHECK PASS")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(s, encoding="utf-8")
    print("written", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
