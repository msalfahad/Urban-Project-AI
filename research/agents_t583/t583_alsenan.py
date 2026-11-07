"""T-583 development villa build: the T-575 rows restated with every bar component (mains, links, side bars,
anchorage, joints / laps) as a value, a bound or HELD by name, and the lift-wall kg(h) with strict counts.

Inputs: values only. Own reads this run of Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523...):
p.7 dome detail (ring section: shell bar leg drawn down through the ring with a foot along the bottom; side bars
labelled per face at a spacing; links per metre), p.8 notes 9 / 21 / 22 (starter development minimum; side bars in
beams over a printed depth; minimum covers by member class), p.14 lift detail (verticals straight down to the raft
bottom mat, joined in a U over the wall top), p.10 schedule row B4. Geometry and mains from the merged T-575 build.
Run: .work/venv/bin/python -I research/agents_t583/t583_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t575"))
import t583_rebar as M  # noqa: E402
import t575_alsenan as A575  # noqa: E402
import t575_rebar as R575  # noqa: E402

OUT = HERE / "out" / "T583_DOME_LIFT_COMPONENTS.json"
RING_CSV = A575.RING_CSV

COVER_MEMBER_MIN = 0.025   # ST p.8 note 22: columns, beams, slabs (minimum, one-sided: caps highs only)
COVER_SOIL_MIN = 0.07      # ST p.8 note 22: concrete against soil (not used for a high: the smaller cover governs)
NOTE9_D = {"tension": 70, "compression": 40}   # ST p.8 note 9: starter development, minimum (observation only)
SCEN_SRC = "OWNER_RULE_REBAR_2026-10-24 s.2 (proposal: beams / slabs 60 d, columns / ordinary walls 40 d)"


def t(kg):
    return M.to_t(kg)


def tr(lo, hi):
    return [t(lo), None if hi is None else t(hi)]


def segments(dome: str) -> list:
    return [float(r["CENTRELINE_ARC_M"]) for r in csv.DictReader(RING_CSV.open(encoding="utf-8"))
            if r["DOME"] == dome and r["KIND"] == "DRAWN_BAND_SEGMENT"]


# ---- shell -------------------------------------------------------------------------------------------------------
def shell_row(base: dict) -> dict:
    S = A575.SHELL
    sh = R575.dome_shell(S["chord"], S["rise"], S["thickness"], S["d_mm"], S["s"])
    g = sh["groups"]
    m12 = M.kgm(12)
    mains_lo = g["SHELL_HOOP"]["kg"][0] + g["SHELL_MERIDIONAL"]["kg"][0]
    mains_hi = g["SHELL_HOOP"]["kg"][1] + g["SHELL_MERIDIONAL"]["kg"][1]
    n0 = [x["n_springing"] for x in sh["meridional_readings"]]
    ring_layers = A575.RING_DETAIL["layers"]
    leg_floor = sum(max(l["d_mm"] for l in ring_layers if l["role"] == role) for role in ("RING_TOP", "RING_BOTTOM")) / 1000.0
    # hoop joints: every closed hoop >= max(1, ceil(C / 12)); the low is the smallest reading total
    joint_readings = []
    for rho in sh["rho_bounds"]:
        for off in (0.0, S["s"] / 2.0):
            L = R575.hoop_lengths(rho, sh["a"], S["s"], off)
            joint_readings.append({"rho": round(rho, 6), "offset": off, "hoops": len(L),
                                   "joints": sum(M.joints_closed_loop(c) for c in L),
                                   "hoops_over_stock": sum(1 for c in L if c > M.STOCK_M)})
    j_lo = min(x["joints"] for x in joint_readings)
    mer_len_max = max(x["S"] for x in sh["meridional_readings"])
    groups = [
        {"group": "SHELL_MAINS (T-575, unchanged)", "status": "HELD_RANGE", "kg_low": mains_lo, "kg_high": mains_hi,
         "t": tr(mains_lo, mains_hi), "why": "hoops + meridians as merged (R-T575-1 .. 3)"},
        {"group": "SHELL_ANCHORAGE_INTO_RING", "status": "HELD_HIGH", "bars_at_springing": [min(n0), max(n0)],
         "leg_floor_m": leg_floor, "kg_low": min(n0) * leg_floor * m12, "kg_high": None,
         "t": tr(min(n0) * leg_floor * m12, None),
         "why": "p.7 ring section draws each shell bar down through the ring past the top and bottom layers with a "
                "foot along the bottom: floor = the leg crossing the stacked top + bottom bars (d16 + d18), foot >= 0 "
                "(R-T583-5); high = ring depth less cover + foot: ring depth not printed on p.7 (deferred to the architectural set) -> HELD"},
        {"group": "SHELL_MERIDIONAL_JOINTS", "status": "VALUE", "joints": 0, "kg_low": 0.0, "kg_high": 0.0,
         "t": [0.0, 0.0], "why": f"longest meridian {mer_len_max:.4f} m + leg < 12 m stock: no joint certain or "
                                 "needed (R-T583-4); value 0 is computed, not a missing item"},
        M.lap_group("SHELL_HOOP_LAPS", j_lo, 12,
                    "every hoop is a closed loop: >= 1 joint each, >= 2 where longer than 12 m; no lap length printed "
                    "for shell bars (the slab temperature-bar lap detail does not name the dome): length HELD, "
                    "low 0 (coupler or unknown overlap), high HELD", 60, SCEN_SRC),
    ]
    groups[-1]["joint_readings"] = joint_readings
    tot = M.row_total(groups)
    base.update(status="HELD_RANGE_HIGH_OPEN", t_low=t(tot["kg_low"]), t_high_bounded_part=t(tot["kg_high_bounded_part"]),
                high_excluding=tot["high_excluding"], groups=groups,
                t575={"t_low": t(mains_lo), "t_high": t(mains_hi)},
                cover_note=("p.8 note 22 names columns, beams and slabs; a shell is not named: the T-575 bar-sphere "
                            "bounds (cover >= 0) are kept; if the note governed the shell the bar sphere would narrow "
                            "to R_in + 0.031 .. R_out - 0.031 (not applied)"))
    return base


# ---- rings -------------------------------------------------------------------------------------------------------
def ring_reading(name: str, spec: dict, rd: list, segs: list) -> dict:
    mains = R575.ring_mains(spec["layers"], rd)
    s_link = 1.0 / spec["links_per_m"]
    n_lo = sum(M.count_low(L, s_link) for L in segs)
    circle = max(x["circle_m"] for x in mains["readings"])
    n_hi = M.loop_count(circle, s_link)
    m8 = M.kgm(spec["link_d"])
    p_floor = M.link_path_floor(spec["layers"], spec["link_d"])
    groups = [{"group": f"RING_MAINS[{name}] (T-575, unchanged)", "status": "HELD_RANGE",
               "kg_low": mains["kg"][0], "kg_high": mains["kg"][1], "t": tr(*mains["kg"])}]
    if spec["depth"] is not None:
        p_hi = M.link_path_high(0.20, spec["depth"], spec["link_d"], COVER_MEMBER_MIN)
        hi = n_hi * p_hi * m8
        why_hi = (f"{n_hi} links on the closed circle x path {p_hi:.3f} m (0.20 x {spec['depth']:.2f}, printed "
                  "minimum cover 0.025 as the longest admissible path, R-T583-3)")
    else:
        p_hi, hi, why_hi = None, None, "ring depth not printed on p.7 (deferred to the architectural set): link path high HELD"
    groups.append({"group": f"RING_LINKS[{name}]", "status": "HELD_HIGH" if hi is None else "HELD_RANGE",
                   "count": [n_lo, n_hi], "path_m": [round(p_floor, 4), None if p_hi is None else round(p_hi, 4)],
                   "kg_low": n_lo * p_floor * m8, "kg_high": hi, "t": tr(n_lo * p_floor * m8, hi),
                   "why": f"count: drawn in-bay segments {[round(x, 4) for x in segs]} m, each ceil(L/s) - 1 "
                          f"(R-T583-1) .. closed circle {circle:.4f} m ceil(C/s); path floor = link round the "
                          f"widest layer in contact + stacked top / bottom bars; {why_hi}; hooks separate"})
    groups.append({"group": f"RING_LINK_HOOKS[{name}]", "status": "HELD_HIGH", "kg_low": 0.0, "kg_high": None,
                   "t": [0.0, None], "why": "hook extension / bend diameter printed nowhere (G-T371-0): HELD"})
    if spec["side"]:
        inbay = min(x["inbay_m"] for x in mains["readings"])
        m14 = M.kgm(spec["side"]["d_mm"])
        lo = spec["side"]["n_per_face"] * inbay * m14
        groups.append({"group": f"RING_SIDE[{name}]", "status": "HELD_HIGH", "kg_low": lo, "kg_high": None,
                       "t": tr(lo, None),
                       "why": f"at least the {spec['side']['n_per_face']} labelled d{spec['side']['d_mm']} bars over "
                              f"the in-bay length {inbay:.4f} m; further rows at the printed spacing over "
                              "the unprinted ring depth: HELD"})
    else:
        groups.append({"group": f"RING_SIDE[{name}]", "status": "VALUE", "kg_low": 0.0, "kg_high": 0.0, "t": [0.0, 0.0],
                       "why": "B4 schedule row prints no side bars; p.8 note 21 adds side bars only above its printed "
                              "beam depth, which the 0.50 depth does not exceed: 0 by the drawings"})
    # joints of the mains: in-bay segments < 12 m (0 joints) .. closed circle > 12 m (2 per bar)
    jb = sum(l["n"] for l in spec["layers"]) * M.joints_closed_loop(circle)
    scen_kg = sum(l["n"] * M.joints_closed_loop(circle) * 60 * l["d_mm"] / 1000.0 * M.kgm(l["d_mm"])
                  for l in spec["layers"])
    groups.append({"group": f"RING_MAIN_LAPS_AND_ANCHORAGE[{name}]", "status": "HELD_HIGH", "joints_at_least": 0,
                   "joints_closed_circle_reading": jb, "kg_low": 0.0, "kg_high": None, "t": [0.0, None],
                   "scenario": {"label": "OWNER_PROPOSAL_SCENARIO", "source": SCEN_SRC, "d_multiple": 60,
                                "joints": jb, "kg": scen_kg, "t": t(scen_kg), "in_bound": False},
                   "why": "in-bay reading: segments < 12 m, 0 joints certain, ends anchor into the framing members "
                          "(no anchorage drawn: HELD); closed-circle reading: >= 2 joints per bar; no lap printed for "
                          "ring bars: length HELD"})
    tot = M.row_total(groups)
    return {"reading": name, "groups": groups, **tot}


def ring_row(base: dict, west: bool) -> dict:
    dome = "DOME-A" if west else "DOME-B"
    rd = A575.ring_readings(dome)
    segs = segments(dome)
    reads = [ring_reading("DETAIL", A575.RING_DETAIL, rd, segs)]
    if west:
        reads.append(ring_reading("B4", A575.RING_B4, rd, segs))
    lo = min(r["kg_low"] for r in reads)
    excl = sorted({g for r in reads for g in r["high_excluding"]})
    base.update(status="HELD_RANGE_HIGH_OPEN", t_low=t(lo),
                t_high_bounded_part=t(max(r["kg_high_bounded_part"] for r in reads)), high_excluding=excl,
                readings=[{"reading": r["reading"], "t_low": t(r["kg_low"]),
                           "t_high_bounded_part": t(r["kg_high_bounded_part"]), "high_status": r["high_status"],
                           "groups": r["groups"]} for r in reads],
                depth_floor_m=round(M.depth_floor(A575.RING_DETAIL["layers"], 8, COVER_MEMBER_MIN), 4),
                note="row low = the smaller reading low (B4 vs DETAIL are conflicting sources, R-T575-5): strict")
    return base


# ---- lift walls ----------------------------------------------------------------------------------------------------
def lift_row(base: dict) -> dict:
    L = A575.lift_segments()
    segs = [L["segments"][k] for k in ("N", "S", "W", "E")]
    sv = 1.0 / A575.LIFT_BARS["vert"]["per_m"]
    nh = A575.LIFT_BARS["horiz"]["per_m"]
    per_face = {k: M.spacing_readings(L["segments"][k], sv) for k in ("N", "S", "W", "E")}
    nv_lo = 2 * sum(v["low"] for v in per_face.values())
    nv_hi = 2 * sum(v["high"] for v in per_face.values())
    t575_n = 2 * sum(R575.count_by_spacing(x, sv) for x in segs)
    checker_n = 2 * sum(math.floor(x / sv + 1e-9) for x in segs)
    M.assert_strict_low(nv_lo, [t575_n, checker_n, nv_lo, nv_hi])
    mh, mv, mt = M.kgm(12), M.kgm(16), M.kgm(12)
    run_lo, run_hi = 2.0 * sum(segs), L["outer_perimeter"] + L["centre_perimeter"]
    embed_hi = L["raft_H"]                      # raft class not named by note 22 -> cover >= 0 for the high
    w = L["w"]
    ret_hi = (w - 0.016) / 2.0                  # U over the top: one leg per pair, centreline gap with cover >= 0
    A_lo = nh * run_lo * mh + nv_lo * mv
    A_hi = nh * run_hi * mh + nv_hi * mv
    top_lo, top_hi = 2 * sum(segs) * mt, 2 * L["centre_perimeter"] * mt
    B_lo = top_lo - 1.0 * run_lo * mh           # rows >= n h - 1 (R-T583-2); verticals: embed / U leg floor 0
    B_hi = top_hi + nv_hi * (embed_hi + ret_hi) * mv + 2.0 * run_hi * mh
    if B_lo < -1e-9:
        raise M.T583Error("B low negative")
    B_lo = max(B_lo, 0.0)
    h_no_joint = M.STOCK_M - embed_hi - ret_hi
    note9 = {k: v * 16 / 1000.0 for k, v in NOTE9_D.items()}
    base.update(status="HELD_BLANK", t_low=None, t_high=None,
                missing="pit depth / wall height h not printed on p.14: bars only as kg(h)",
                formula={"kg(h)": "A x h + B", "A_t_per_m": [t(A_lo), t(A_hi)], "B_t": [t(B_lo), t(B_hi)],
                         "n_vertical": [nv_lo, nv_hi], "n_vertical_per_face": {k: [v["low"], v["one_end"], v["high"]]
                                                                               for k, v in per_face.items()},
                         "t575": {"A_t_per_m": [0.169284, 0.200217], "B_t": [0.009778, 0.101057], "n_vertical": t575_n},
                         "checker_floor_reading_n": checker_n,
                         "horizontal_run_per_row_m": [round(run_lo, 4), round(run_hi, 4)],
                         "embed_into_raft_m": [0.0, embed_hi], "top_U_leg_per_bar_m": [0.0, round(ret_hi, 4)]},
                groups=[
                    {"group": "WALL_VERTICAL", "d_mm": 16, "count": [nv_lo, nv_hi], "status": "HELD_BLANK",
                     "why": "per face ceil(L/s) - 1 .. ceil(L/s) + 1 (R-T583-1) on N 1.80 / S 1.80 / W 1.20 / E 0.70 m; "
                            "length h + raft leg (drawn to the bottom mat, 0 .. raft depth 0.55) + top U leg"},
                    {"group": "WALL_HORIZONTAL", "d_mm": 12, "status": "HELD_BLANK",
                     "why": "rows ceil(6h) - 1 .. ceil(6h) + 1 (R-T583-2), run per row 11.0 (stop at columns) .. 16.8 m"},
                    {"group": "WALL_TOP_BARS", "d_mm": 12, "n": 2, "status": "HELD_BLANK", "why": "in B"},
                    {"group": "WALL_LAPS", "status": "HELD_HIGH", "joints_at_least": 0,
                     "why": f"verticals: no joint while h <= {h_no_joint:.3f} m (one 12 m bar holds h + leg + U); "
                            "horizontals: stop-at-column reading has 0 joints (segments <= 1.80 m), run-through "
                            "reading 1 closing joint per row per face; no lap printed for wall bars: length HELD"},
                    {"group": "WALL_STARTER_DEVELOPMENT_OBSERVATION", "status": "DESIGNER_ITEM",
                     "why": f"if the verticals are read as starters, p.8 note 9 asks >= {note9['tension']:.2f} m "
                            f"(tension) / {note9['compression']:.2f} m (compression) for d16, more than the 0.55 raft "
                            "the straight drawn leg can occupy; no foot bend is drawn: listed for the designer "
                            "(RFI-B-S21 family), no quantity taken"}],
                strict_low_check={"t575_low_A": 0.169284, "checker_low_A": 0.156642, "restated_low_A": t(A_lo),
                                  "strict": t(A_lo) <= 0.156642 + 1e-9})
    return base


def build() -> dict:
    v8 = json.loads(A575.V8.read_text(encoding="utf-8"))["rebar_omission"]["rows"]
    rows = []
    for r in v8:
        el = r["concrete_element"]
        base = {"row_id": r["expected_after"]["element_id"], "concrete_line": r["concrete_line"], "unit": "t"}
        if el.startswith("HL:DOME_SHELL:"):
            rows.append(shell_row(base))
        elif el.startswith("HL:DOME_RING:"):
            rows.append(ring_row(base, "DOME-1F-W" in el))
        elif el.startswith("DG5:DOME-3"):
            base.update(status="HELD_BLANK", t_low=None, t_high=None,
                        missing="no structural drawing of the third dome (unchanged from T-575)")
            rows.append(base)
        elif el.startswith("LIFT_PIT:WALLS"):
            rows.append(lift_row(base))
        else:
            raise M.T583Error(f"unmapped V8 row {el}")
    rng = [r for r in rows if r.get("t_low") is not None]
    return {"schema": "URBAN_T583_DOME_LIFT_COMPONENTS_V1", "task": "T-583",
            "method": "DOME_LIFT_REBAR_COMPONENTS_V1 (R-T583-1 .. 6) on DOME_LIFT_REBAR_V1 (R-T575-1 .. 6)",
            "candidate": "ARCH_TAKEOFF_V3.0.58 (unchanged)", "rows": rows,
            "totals": {"rows": len(rows), "bounded_low_rows": len(rng),
                       "t_low": round(sum(r["t_low"] for r in rng), 6),
                       "t_high_bounded_part": round(sum(r["t_high_bounded_part"] for r in rng), 6),
                       "t_high": None, "high_status": "HELD_HIGH (laps, hooks, anchorage, ring depth by name)",
                       "t575_t_low": 0.733792, "t575_t_high_mains_only": 1.161932, "valued_t": 0.0},
            "freelancer": "TYPED_LUMP 44.19 t, no bar row (T-560): NOT_COMPARABLE, no %"}


def main():
    res = build()
    txt = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        ok = OUT.read_text(encoding="utf-8") == txt
        print("CHECK", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    for r in res["rows"]:
        print(r["row_id"], r["status"], r.get("t_low"), r.get("t_high_bounded_part"), r.get("formula", {}).get("A_t_per_m"),
              r.get("formula", {}).get("B_t"))
    print(res["totals"])


if __name__ == "__main__":
    main()
