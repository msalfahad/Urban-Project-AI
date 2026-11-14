"""T-776 (F-14, lane S, DELIVERY MODE): boundary-wall foundation per RUN TYPE + fence block difference.

    python3 -I research/agents_t776/fill_t776.py            # writes research/agents_t776/out/FIX_ROWS.{json,md}
    python3 -I research/agents_t776/fill_t776.py --check    # synthetic self-test (normal + adverse) + rebuild == files

PHYSICAL ELEMENT. The plot-boundary wall rests on a 0.20 band on the plot line (ST p.2, closed, 91.94 m centre line).
Three run types along it, split from the ST DXF (foundation plan band vs the ground-beam plan band, p.3), lengths only:
  FENCE         44.07 m where the p.3 plan draws the boundary band at N.G. and the fence stands above (upper neighbour
                31.17, street 8.20, sea 2.35 + 1.15, lower neighbour 1.20); 1.60 m of it inside footings, 42.47 free.
  UNDER_BLDG    44.37 m where the building stands on the plot line (lower neighbour 29.97, street 6.60, sea 7.80);
                19.35 m inside footings, 25.02 free.
  SEA_GAP       3.50 m on the sea side between the two p.3 band pieces (pool wall / sea gate, no N.G. band drawn);
                0.50 m inside F8, 3.00 free.            free total 42.47 + 25.02 + 3.00 = 70.49 (= T-065 / Q-28).
SECTION (ST p.14 'TYPICAL BOUNDARY WALL', own read at 300 dpi): plan = GROUND BEAM (20x40) between 20x30 columns with a
pad (130x80x30) at each column on the inner side, section mark A-A cut THROUGH a pad; section A-A = lower (G.B) on a base
80 (incl. the G.B) x 30 on '10' plain concrete that is FLUSH with the outer (plot-line) face and runs '10' past the toe.
So the 0.90 cut is a PAD width (1.30 long at each column), not a run width; between pads the base is not drawn and the
member is the band on its own 10 cm plain concrete, flush outside (plot line), 10 past the inner face = 0.30 wide.
Lower-member depth: owner Q-28 A (PROVISIONAL) = schedule B.W 20 x 60 (kept; the A-A drawing scales ~0.40, not printed,
shown beside). Founding: 'AS PER EXCAVATION DEPTH' = the building's founding level, S01 (owner-accepted) underside -1.50;
p.14 A-A prints only the 10 cm plain concrete under the member (no screed / membrane as under the p.13 footings), so the
boundary formation is 1.60 below N.G. (T-764 used the footing build-up 1.67).
CROSSINGS (owner Q-28 answer: deduct only the real overlap): band and footings share the underside -1.50, so inside a
footing only min(H, 0.60) overlaps; the band part above a footing top (0.60 - H) is concrete no line carries.

Only numbers are carried from the drawings (lengths, footing heights by schedule mark); no coordinate or image.
Before-values come from the merged fix-row sets (T-757, T-761, T-762, T-764, T-767, T-769) of the candidate.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
R = lambda p: os.path.join(ROOT, p)
INDEX = "research/agents_t314/out/LINE_INDEX_V3_0_79.json"
FIXSETS = {"T-757": "research/agents_t757/out/FIX_ROWS.json", "T-761": "research/agents_t761/out/FIX_ROWS.json",
           "T-762": "research/agents_t762/out/FIX_ROWS.json", "T-764": "research/agents_t764/out/FIX_ROWS.json",
           "T-767": "research/agents_t767/out/FIX_ROWS.json", "T-769": "research/agents_t769/out/FIX_ROWS.json"}
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")

# ---- printed / owner values -------------------------------------------------------------------------------------------
BAND_B = 0.20             # ST p.2 band width, p.10 B.W 'B 20', p.14 '(20x..)'
BAND_D = 0.60             # p.10 B.W 'D 60' (owner Q-28 A, PROVISIONAL)
BAND_D_AA = 0.40          # p.14 plan label 'GROUND BEAM (20x40)'; A-A lower G.B scales 0.39 (not dimensioned): beside only
PC_T = 0.10               # p.14 A-A '10'
PC_TOE = 0.10             # p.14 A-A '10' past the toe; outer side flush (plot line)
PAD_L, PAD_W, PAD_T = 1.30, 0.80, 0.30   # p.14 plan '(130x80x30)', A-A base '80' incl. the G.B, '30'
FOUND = 1.50              # S01 (owner-accepted): founding / member underside below N.G.
FORMATION = FOUND + PC_T  # 1.60: A-A has no screed / membrane under the boundary member
UPPER_GB = 0.40           # p.14 A-A upper (G.B) '40', top at N.G.
COL_ALONG = 0.30          # 20 x 30 column, 0.30 along the run (T-396 / T-769)
N_PADS = 10               # T-761 SAFETY count (spacing 'SEE ARCH PLAN', none drawn); kept, designer item replaces it

# ---- run types (ST DXF own read this run, lengths in m) ---------------------------------------------------------------
RUNS = {"FENCE": {"centre": 44.07, "in_footings": 1.60}, "UNDER_BLDG": {"centre": 44.37, "in_footings": 19.35},
        "SEA_GAP": {"centre": 3.50, "in_footings": 0.50}}
# crossings: (run type, footing mark, schedule H, centre line inside the outline)
CROSS = [("FENCE", "C/F", 0.30, 0.20), ("FENCE", "F8", 0.50, 1.15), ("FENCE", "C/F", 0.30, 0.25),
         ("SEA_GAP", "F8", 0.50, 0.50),
         ("UNDER_BLDG", "C/F", 0.30, 0.70), ("UNDER_BLDG", "C/F", 0.30, 0.70), ("UNDER_BLDG", "C/F", 0.30, 0.80),
         ("UNDER_BLDG", "C/F", 0.30, 0.65), ("UNDER_BLDG", "F11", 0.50, 3.50), ("UNDER_BLDG", "F14", 0.50, 3.80),
         ("UNDER_BLDG", "F10/F", 0.50, 4.45), ("UNDER_BLDG", "F15", 0.40, 1.80), ("UNDER_BLDG", "F8", 0.50, 1.95),
         ("UNDER_BLDG", "FN", 0.30, 1.00)]
F10F_ALT_H = 0.30         # C5: outline 1B1B holds F10 (0.50) and F (0.30): beside as a range


def r6(x):
    return round(x + 0.0, 6)


# ---- generic method (any villa) ---------------------------------------------------------------------------------------
def boundary_takeoff(runs, cross, n_pads, *, band_b=BAND_B, band_d=BAND_D, pc_t=PC_T, pc_toe=PC_TOE, pad=(PAD_L, PAD_W, PAD_T),
                     formation=FORMATION, upper_gb=UPPER_GB, col_along=COL_ALONG, pad_run="FENCE"):
    """Per run type: trench = free length x (band + inner PC projection; flush on the plot line) x formation; each pad adds
    its extra PC width (base + toe - band strip) x pad length x formation. Concrete: band over the free length + the band
    part above every footing top (min(H, D) overlaps). Missing inputs raise; nothing is defaulted to 0."""
    for k, v in runs.items():
        if v.get("centre") is None or v.get("in_footings") is None:
            raise ValueError(f"run {k}: length missing (HELD, never 0)")
        if not (0 <= v["in_footings"] <= v["centre"] <= 1000.0):
            raise ValueError(f"run {k}: length outside 0 .. 1000 m (units?)")
    if n_pads is None:
        raise ValueError("pad count missing (HELD, never 0)")
    pl, pw, pt = pad
    strip = band_b + pc_toe                      # trench width between pads (outer face on the plot line)
    pad_cut_extra = (pw + pc_toe) - strip        # A-A: base 0.80 + toe 0.10 = 0.90, of which the strip is already dug
    assert pad_cut_extra > 0
    fill_h = formation - pc_t                    # inner strip filled from PC top to N.G.
    out, tot = {}, {}
    for k, v in runs.items():
        free = v["centre"] - v["in_footings"]
        cr = [c for c in cross if c[0] == k]
        assert abs(sum(c[3] for c in cr) - v["in_footings"]) < 1e-9, (k, "crossings must sum to the inside length")
        above = sum(band_b * max(0.0, band_d - h) * L for _, _, h, L in cr)
        above_faces = sum(2 * max(0.0, band_d - h) * L for _, _, h, L in cr)
        np_ = n_pads if k == pad_run else 0
        d = {"centre_m": v["centre"], "in_footings_m": v["in_footings"], "free_m": free, "pads": np_,
             "excavation": free * strip * formation + np_ * pad_cut_extra * pl * formation,
             "band_concrete_free": free * band_b * band_d, "band_concrete_above_footings": above,
             "band_blinding": free * strip * pc_t,
             "pad_concrete": np_ * (pl * pw - pl * band_b) * pt,          # the band runs through the pad (same underside)
             "pad_blinding": np_ * pad_cut_extra * pl * pc_t,
             "band_formwork": 2 * band_d * free - np_ * pl * pt + above_faces,
             "pad_formwork": np_ * (pl + 2 * (pw - band_b)) * pt,       # inner face + two ends; outer face = band's
             "backfill": free * pc_toe * fill_h
             + np_ * (pad_cut_extra * pl * formation - pad_cut_extra * pl * pc_t - (pw - band_b - pc_toe) * pl * pt
                      - pc_toe * pl * pt)}
        out[k] = d
        for q, x in d.items():
            if isinstance(x, float) or isinstance(x, int):
                tot[q] = tot.get(q, 0.0) + x
    return out, tot


# ---- synthetic self-test (not Alsenan) ---------------------------------------------------------------------------------
def selftest():
    # NORMAL: one 10.00 m fence run, 1.00 m of it inside a 0.30 footing, 2 pads. Hand calc (formation 1.60):
    runs = {"FENCE": {"centre": 10.0, "in_footings": 1.0}}
    cross = [("FENCE", "X", 0.30, 1.0)]
    o, t = boundary_takeoff(runs, cross, 2)
    f = o["FENCE"]
    hand_exc = 9.0 * 0.30 * 1.60 + 2 * 0.60 * 1.30 * 1.60          # 4.32 + 2.496 = 6.816
    assert abs(f["excavation"] - hand_exc) < 1e-9 and abs(hand_exc - 6.816) < 1e-9
    assert abs(f["band_concrete_free"] - 9.0 * 0.12) < 1e-9
    assert abs(f["band_concrete_above_footings"] - 0.20 * 0.30 * 1.0) < 1e-9   # 0.06: above a 0.30 footing top
    assert abs(f["pad_concrete"] - 2 * 0.234) < 1e-9                         # 1.30 x 0.60 x 0.30 net of the band
    assert abs(f["pad_formwork"] - 2 * 0.75) < 1e-9                          # (1.30 + 2 x 0.60) x 0.30
    # backfill: strip 9.0 x 0.10 x 1.50 = 1.35; per pad: cut 1.248 - PC 0.078 - pad beyond strip 0.195 - pad in strip 0.039
    assert abs(f["backfill"] - (1.35 + 2 * (1.248 - 0.078 - 0.195 - 0.039))) < 1e-9
    # MIRROR / ORDER: reversing the crossing list or the run order changes nothing
    o2, _ = boundary_takeoff(dict(reversed(list(runs.items()))), list(reversed(cross)), 2)
    assert all(abs(o2["FENCE"][k] - f[k]) < 1e-12 for k in f)
    # UNITS: the same run in mm must be refused by the crossing check, not silently scaled
    try:
        boundary_takeoff({"FENCE": {"centre": 10000.0, "in_footings": 1000.0}}, [("FENCE", "X", 0.30, 1000.0)], 2)
        raise RuntimeError("mm input accepted")
    except ValueError as e:
        assert "units" in str(e)
    # ADVERSE 1: a blanket 0.90 width on every metre is NOT what the method gives (0.90 only at the pads)
    blanket = 9.0 * 0.90 * 1.60
    assert f["excavation"] < blanket - 1.0
    # ADVERSE 2: a missing length or pad count is refused (HELD, never 0)
    for bad in ({"FENCE": {"centre": None, "in_footings": 0.0}},):
        try:
            boundary_takeoff(bad, [], 2); raise RuntimeError("missing length accepted")
        except ValueError:
            pass
    try:
        boundary_takeoff(runs, cross, None); raise RuntimeError("missing pad count accepted")
    except ValueError:
        pass
    return True


# ---- Alsenan fix rows -------------------------------------------------------------------------------------------------
def build():
    idx = json.load(open(R(INDEX)))
    byid = {l["line_id"]: l for l in idx["lines"]}
    prior = {}
    for task, p in FIXSETS.items():
        for r in json.load(open(R(p)))["rows"]:
            prior.setdefault(r["line_id"], (task, r))
    out, tot = boundary_takeoff(RUNS, CROSS, N_PADS)
    assert abs(sum(v["free_m"] for v in out.values()) - 70.49) < 1e-9          # = Q-28 / T-065 free length
    assert abs(sum(v["centre_m"] for v in out.values()) - 91.94) < 1e-9

    rows = []

    def row(lid, code, unit, after, label, basis, expect_before=None):
        assert label in LABELS
        task, pr = prior[lid] if lid in prior else (None, None)
        before = pr["after"]["net"] if pr else None
        if expect_before is not None:
            assert before is not None and abs(before - expect_before) < 1e-6, (lid, before, expect_before)
        l = byid.get(lid)
        assert l is not None and l["item_code"] == code and l["unit"] == unit, lid
        rows.append({"line_id": lid, "item_code": code, "unit": unit, "element_id": l["element_id"],
                     "before": {"index_class": l["class"], "fix_row": task, "net": before,
                                "label": pr["label"] if pr else None},
                     "after": {"class": "RELEASED", "net": r6(after)}, "delta": r6(after - before) if before else None,
                     "label": label, "basis": basis})
        return after

    # 1 excavation (B1-02)
    exc = tot["excavation"]
    row("L-313384fed48301ae02d2", "STR.EARTH.EXCAVATION", "m3", exc, "ESTIMATE",
        "per run type, p.14 A-A section (flush on the plot line, 10 past the inner face) x formation 1.60 (S01 -1.50 + "
        f"10 cm PC; no footing screed / membrane under the boundary member): FENCE 42.47 x 0.30 x 1.60 + 10 pads x 0.60 x "
        f"1.30 x 1.60 = {out['FENCE']['excavation']:.4f}; UNDER_BLDG 25.02 x 0.30 x 1.60 = {out['UNDER_BLDG']['excavation']:.4f}; "
        f"SEA_GAP 3.00 x 0.30 x 1.60 = {out['SEA_GAP']['excavation']:.4f}; = {exc:.4f} m3 (0.90 only at the pads; a blanket "
        "0.90 would be 105.95)", expect_before=47.08732)
    # 2 backfill (B1-03, the OTHER line carries the boundary component of T-764)
    t764 = json.load(open(R(FIXSETS["T-764"])))
    b764 = [r for r in t764["rows"] if r["line_id"] == "L-89b8e6beaea55fc0e4c9"][0]["after"]["net"]
    bnd_old = 70.49 * 2 * 0.10 * (1.67 - 0.10)
    bf_new = b764 - bnd_old + tot["backfill"]
    row("L-89b8e6beaea55fc0e4c9", "STR.EARTH.BACKFILL", "m3", bf_new, "ESTIMATE",
        f"T-764 sum {b764:.4f} with its boundary part {bnd_old:.4f} (two 0.10 strips x 1.57) replaced by {tot['backfill']:.4f}: "
        "inner 0.10 strip x 1.50 (PC top to N.G.) over 70.49 free = 10.5735 + 10 pads x (cut 1.248 - PC 0.078 - pad 0.195 "
        "beyond the strip - pad 0.039 in the strip) = 9.3600; outer face on the plot line: no strip", expect_before=b764)
    # 3 disposal (B1-04) = excavation - backfill, T-764 method
    d764 = [r for r in t764["rows"] if r["line_id"] == "L-78d7c8a989ab34527a1c"][0]["after"]["net"]
    disp = d764 + (exc - 47.08732) - (bf_new - b764)
    row("L-78d7c8a989ab34527a1c", "STR.EARTH.DISPOSAL", "m3", disp, "ESTIMATE",
        f"T-764 {d764:.4f} + excavation change {exc - 47.08732:+.4f} - backfill change {bf_new - b764:+.4f} (in situ, no bulking)",
        expect_before=d764)
    # 4 band concrete (Q-28 A section kept)
    band = tot["band_concrete_free"] + tot["band_concrete_above_footings"]
    row("L-6290a9f3d93f38cd46d6", "STR.CONC.BOUNDARY_WALL", "m3", band, "DEFAULT",
        f"Q-28 A B.W 0.20 x 0.60 over the free 70.49 m = 8.4588 (FENCE {out['FENCE']['band_concrete_free']:.4f}, UNDER_BLDG "
        f"{out['UNDER_BLDG']['band_concrete_free']:.4f}, SEA_GAP {out['SEA_GAP']['band_concrete_free']:.4f}) + the band part "
        f"ABOVE the 14 footing tops it crosses (same underside -1.50, owner: deduct only the real overlap) 0.20 x (0.60 - H) x L "
        f"= {tot['band_concrete_above_footings']:.4f} (C/F, FN 0.30; F15 0.40; F8, F10, F11, F14 0.50) = {band:.4f} m3",
        expect_before=8.4588)
    # 5 pads
    row("L-cda8f41522dc6f42b3d6", "STR.CONC.BOUNDARY_PAD", "m3", tot["pad_concrete"], "SAFETY",
        "10 pads (T-761 SAFETY count) x 1.30 x (0.80 - 0.20 band through the pad, A-A '80' includes the G.B) x 0.30 = "
        f"{tot['pad_concrete']:.4f} m3 (0.078 each was counted twice with the band)", expect_before=3.12)
    # 6 pad blinding
    row("L-d0313e5d204e2758996a", "STR.CONC.BLINDING", "m3", tot["pad_blinding"], "SAFETY",
        "10 pads x A-A PC beyond the band strip (0.80 + 0.10 toe - 0.30 strip = 0.60) x 1.30 x 0.10 = "
        f"{tot['pad_blinding']:.4f} m3; the strip under the band is the new band-blinding line", expect_before=1.04)
    # 8 / 9 formwork
    row("L-16e428b50357188a94d2", "STR.FORMWORK", "m2", tot["pad_formwork"], "ESTIMATE",
        "10 pads x (inner face 1.30 + two ends 0.60) x 0.30 = 0.75 each: the outer face is the band's face and the 0.20 "
        f"under the band is no face = {tot['pad_formwork']:.4f} m2", expect_before=12.6)
    row("L-eb7b7329145b529cc89d", "STR.FORMWORK", "m2", tot["band_formwork"], "ESTIMATE",
        f"hand: band 2 faces x 0.60 x 70.49 free = 84.588 - pad contact 10 x 1.30 x 0.30 = 3.900 + the faces above the "
        f"footing tops 2 x (0.60 - H) x L = {sum(2 * max(0, 0.60 - c[2]) * c[3] for c in CROSS):.4f} = "
        f"{tot['band_formwork']:.4f} m2 (replaces the face-ledger 83.36)", expect_before=83.36)
    # 10 masonry below N.G. (T-769 method, formation 1.60)
    h_below = FORMATION - PC_T - BAND_D - UPPER_GB
    mas = 44.07 * h_below - N_PADS * COL_ALONG * h_below
    row("L-c632bb4647031c37de19", "EXT.FENCE.MASONRY_BELOW_NG", "m2", mas, "ESTIMATE",
        f"T-769 method at formation 1.60: band 44.07 x h {h_below:.2f} (1.60 - 0.10 PC - 0.60 B.W - 0.40 upper G.B) - 10 "
        f"columns x 0.30 x {h_below:.2f} = {mas:.4f} m2", expect_before=23.4099)
    # 11 WP on buried boundary faces (T-767 method, buried 1.50)
    t767 = [r for r in json.load(open(R(FIXSETS["T-767"])))["rows"] if r["line_id"] == "L-4f4e4c930e33ed6dafa3"][0]
    wp = 16.56 + 44.07 * 2 * (FORMATION - PC_T)
    row("L-4f4e4c930e33ed6dafa3", "WP.FOUNDATION.BURIED_LIQUID", "m2", wp, "ESTIMATE",
        f"T-767 method, buried height 1.50 (formation 1.60 - PC 0.10) instead of 1.57: straps 16.56 + 44.07 x 2 x 1.50 = "
        f"{wp:.4f} m2 (T-767's RULE_DIFFERENCE note stands: p.14 prints no coating)", expect_before=t767["after"]["net"])

    new_lines = [{"proposed_id": "NEW:STR.CONC.BLINDING:BOUNDARY_BAND", "item_code": "STR.CONC.BLINDING", "unit": "m3",
                  "net": r6(tot["band_blinding"]), "label": "ESTIMATE",
                  "basis": f"band plain concrete 70.49 free x 0.30 (A-A: flush outside, 10 past the inner face) x 0.10 = "
                           f"{tot['band_blinding']:.4f} m3; carried by no candidate line (T-445 F-T445-4 'under the band "
                           "between pads not drawn'; GB blinding L-7a5214a3 is the building ground beams only)"}]
    t769 = json.load(open(R(FIXSETS["T-769"])))
    blk = t769["summary"]["per_item"]["EXT.FENCE.BLOCK [m2]"]["after"]
    fence = {"engine_m2": blk, "freelancer_m2": 74.40, "freelancer_formula": "1 x 37.20 x 2.00 (row 'fence', T-396 s.6)",
             "steps": [["height 2.00 -> printed 2.65 (p.12 SECTION '265') on his 37.20", r6(37.20 * 0.65), "ENGINE_RIGHT"],
                       ["length 37.20 -> 36.97 (north 31.37 + street plot face 5.60; his corner counted in both runs "
                        "+ 0.03 typed)", r6(-0.23 * 2.65), "ENGINE_RIGHT"],
                       ["street railing dip (p.12 elevation, scaled)", -4.119, "ENGINE_RIGHT"],
                       ["4 columns on his two runs x 0.30 x 2.65 (SAFETY count)", r6(-4 * 0.795), "UNRESOLVED"],
                       ["sea 2.40 + lower 1.20 runs he does not carry, net of their 6 columns", r6(6.36 - 3.18 + 3.18 - 1.59),
                        "RULE_DIFFERENCE"]]}
    fence["residual_m2"] = r6(blk - (74.40 + sum(s[1] for s in fence["steps"])))
    assert abs(fence["residual_m2"]) < 0.01 * blk, fence
    beside = {
        "drawing_method_band_0_40": {"band_free": r6(70.49 * 0.20 * 0.40),
                                     "above_footings": r6(sum(0.20 * max(0, 0.40 - c[2]) * c[3] for c in CROSS)),
                                     "note": "A-A lower G.B scales ~0.40, plan label 20x40; owner Q-28 A keeps B.W 20x60 "
                                             "PROVISIONAL (RFI C1 with the designer)"},
        "f10_f_outline_at_H_0_30": r6(0.20 * (0.60 - F10F_ALT_H) * 4.45 - 0.20 * (0.60 - 0.50) * 4.45),
        "t764_blanket_0_40_x_1_67": 47.08732, "blanket_0_90_x_1_67": r6(70.49 * 0.90 * 1.67),
        "pad_positions_by_run_ends": "8 distinct run-end points (two corners shared), 4 of them inside a footing (C/F, "
                                     "C/F, F8 twice): ends alone justify 4 pads; intermediate columns 'SEE ARCH PLAN' are "
                                     "not drawn -> the T-761 SAFETY count 10 stays until the designer answers",
        "freelancer_band": "8.604 = 71.7 x 0.20 x 0.60 ('perimeter tie beam'): RULE_DIFFERENCE on length (his 71.7 is not "
                           "reproducible: 70.09 inner .. 72.59 outer free), ours 9.0958 adds the band above the footing "
                           "tops he does not carry",
        "possible_overlap_named": "L-438a4abd (building exterior GB blinding cut 0.10) may overlap the 0.30 band trench "
                                  "under the 25.02 m UNDER_BLDG free length by at most 25.02 x 0.30 x 0.10 = 0.75 m3; "
                                  "not changed here (T-764 line, its own cut basis)"}
    res = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-776", "candidate_version": idx["candidate_version"],
           "inputs": {"index": INDEX, "fix_sets": FIXSETS,
                      "drawings": "Drive 'Alsenan chalet project' / ST7757.pdf p.2, p.13, p.14 and ST7757 dxf.dxf (S-BOUN "
                                  "band polylines of the foundation and ground-beam plans, footing outlines), read only in "
                                  ".work/private; only lengths and schedule heights carried"},
           "run_types": {k: {q: r6(x) for q, x in v.items()} for k, v in out.items()},
           "totals": {q: r6(x) for q, x in tot.items()},
           "summary": {"rows": len(rows), "new_lines": len(new_lines),
                       "delta_by_item": {k: r6(sum(r["delta"] for r in rows if f"{r['item_code']} [{r['unit']}]" == k)
                                         + sum(n["net"] for n in new_lines if f"{n['item_code']} [{n['unit']}]" == k))
                                     for k in sorted({f"{r['item_code']} [{r['unit']}]" for r in rows})},
                       "boundary_lines_on_one_blanket_width": 0},
           "fence_block_vs_freelancer": fence, "beside": beside, "rows": rows, "new_lines": new_lines}
    return res


def render_md(res):
    L = [f"# T-776 boundary-wall foundation per run type on {res['candidate_version']} (fix rows, unwired)", "",
         "| run type | centre m | in footings m | free m | pads | excavation m3 | band conc m3 | band above footings m3 | "
         "backfill m3 |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res["run_types"].items():
        L.append(f"| {k} | {v['centre_m']:.2f} | {v['in_footings_m']:.2f} | {v['free_m']:.2f} | {v['pads']} | "
                 f"{v['excavation']:.4f} | {v['band_concrete_free']:.4f} | {v['band_concrete_above_footings']:.4f} | "
                 f"{v['backfill']:.4f} |")
    L += ["", "| line | item | unit | before (set) | after | delta | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        b = r["before"]
        L.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {b['net']} ({b['fix_row']}) | {r['after']['net']} | "
                 f"{r['delta']} | {r['label']} | {r['basis']} |")
    for n in res["new_lines"]:
        L.append(f"| {n['proposed_id']} | {n['item_code']} | {n['unit']} | none | {n['net']} | +{n['net']} | {n['label']} | "
                 f"{n['basis']} |")
    f = res["fence_block_vs_freelancer"]
    L += ["", f"Fence block {f['engine_m2']} m2 vs freelancer {f['freelancer_m2']} m2 ({f['freelancer_formula']}):", ""]
    L += [f"- {s[0]}: {s[1]:+.4f} m2 {s[2]}" for s in f["steps"]]
    L += [f"- residual {f['residual_m2']:+.4f} m2", "", "Beside (not in any line):", ""]
    L += [f"- {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in res["beside"].items()]
    return "\n".join(L) + "\n"


def main(argv):
    assert selftest()
    res = build()
    js = json.dumps(res, indent=1, ensure_ascii=False) + "\n"
    md = render_md(res)
    d = os.path.join(HERE, "out")
    if "--check" in argv:
        ok = open(os.path.join(d, "FIX_ROWS.json")).read() == js and open(os.path.join(d, "FIX_ROWS.md")).read() == md
        print("T-776 check", "PASS" if ok else "FAIL (rebuild differs)")
        return 0 if ok else 1
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "FIX_ROWS.json"), "w").write(js)
    open(os.path.join(d, "FIX_ROWS.md"), "w").write(md)
    print(json.dumps(res["summary"], indent=1)); print(json.dumps(res["totals"], indent=1))
    print(json.dumps(res["fence_block_vs_freelancer"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
