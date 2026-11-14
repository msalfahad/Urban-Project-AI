"""T-771 (F-12, lane I): MISSING FAMILIES PLAN. One entry per BOQ family that has no line in the candidate.

DELIVERY MODE (owner 2026-11-13): every family of the workbook Missing sheet gets either NEW LINES (figure + label
MEASURED / DRAWING-READ / DEFAULT / ESTIMATE / SAFETY + one-line basis) or a DISPOSITION with its evidence
(NOT_APPLICABLE_WITH_EVIDENCE, COVERED_BY_LINE, COVERED_BY_ROW, REGISTER_NO_LINE, PARKED, HELD_MEP_STAGE).
Nothing is wired here: Worker 3 wires the new lines in a T-770 round (item codes + master mapping proposed below).

Inputs: merged repository records only (values; no drawing, no coordinate, no client data):
  candidate   research/agents_t770/out/LINE_INDEX_V3_0_81.json + rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json
  carriers    merged, not yet wired fix-row sets T-760 (external render), T-763 (plaster), T-769 (fence plaster)
  censuses    T-743 sanitary counts (MERGED e9c61254), T-355 / T-362 mesh strip + sharmat (MERGED 21f7b58a / 8bd595ac),
              T-368 exposed tile edges (MERGED r2), T-361 posts (MERGED e8d0bb06), T-147 ceilings (MERGED d54cfac),
              T-351 counters (MERGED f0bd9f3c), T-223 / T-240 joinery boxes (MERGED 48d1d846 / d07af773),
              T-358 temporary works (B1-06b), T-412 nosing edges (MERGED f9c80501), T-766 STEP_LM (READY, not merged)
  freelancer  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json totals quoted by value only

    python3 -I research/agents_t771/fill_t771.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
IDX = ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_81.json"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json"
T743 = ROOT / "research/agents_t743/out/T743_ALSENAN_COUNTS.json"
T355 = ROOT / "research/agents_t355/summary.json"
T362 = ROOT / "research/agents_t362/summary.json"
CARRIER_SETS = {"t760": "FIN.EXT.FINISH", "t763": "FIN.PLASTER", "t769": "EXT.FENCE.PLASTER"}

# merged research values (sources in the docstring and in each basis)
T368_DETERMINATE = 31.65      # exposed tile edges at the old 3.65 tile top (corners 24.35 + pantry 3.65 + 3.65)
T368_OLD_TOP = 3.65
TILE_TOP = 3.00               # owner 2026-11-13: wet-room wall tiles 3.00 m from F.F.L.
T368_GF14_EDGES = 2           # GF-14 wall end + flat stop; no header drawn on the slab plan (T-368 item 2)
T368_DOOR_EDGES_HIGH = 73.10  # door-jamb edges HELD 0 .. 73.10 (T-368)
T361_POSTS = {"RL-02 (NW)": 6, "RL-01 (SE)": 4}
T147_CORNICE_CLOSED_ROOMS = 302.88   # closed-room wall perimeter at the decor ceiling (T-147)
T766_STEP_LM = 89.69          # T-766 READY totals_after FIN.STAIR.STEP_LM (one nosing per step edge)
T412_LANDING_EDGES = 7.40     # T-412 DRAWING-CONFIRMED landing / floor arrival nosing edges
JOINERY_FULL = {"GF lobby box 0.50 x 2.10 (T-223)": 2.10, "1F dressing box 0.50 x 1.80 (T-223 / T-240)": 1.80}
COUNTER_BASE = {"GF kitchen L counter north 2.650 + west 2.500 (T-351)": 5.150,
                "GF pantry wall-backed legs 3.066 + 1.450 + 1.400 (T-351)": 5.916}
COUNTER_WALL = {"GF kitchen west leg (north leg under W08) (T-351)": 2.500,
                "GF pantry wall-backed legs (T-351)": 5.916}
FREELANCER = {"spatter_interior_m2": 504.54, "gypsum_decor_m2": 409.58, "cornice_lm": 427.46}


def r(x, n=2):
    return round(x + 0.0, n)


def load(p):
    return json.loads(Path(p).read_text())


def family_of(master):
    return {c: f["code"] for f in master["families"] for c in f.get("item_codes", [])}


def missing_families(master, lines):
    ic = family_of(master)
    present = {ic.get(l["item_code"], "REF") for l in lines if l["class"] != "EXCLUDED"}
    return [f["code"] for f in master["families"] if f["code"] not in present]


def carrier_total(lines, item_code, unit, overlay):
    """Sum of a carrier item: index figure, replaced by the merged fix-row figure where one exists (no blank left)."""
    tot, blank = 0.0, 0
    for l in lines:
        if l["item_code"] != item_code or l["unit"] != unit or l["class"] == "EXCLUDED":
            continue
        a = overlay.get(l["line_id"])
        if a is not None:
            if a.get("net") is None:
                blank += 1
            else:
                tot += a["net"]
        elif l["class"] == "RELEASED":
            tot += l["measured_net"] or 0.0
        elif l["held_low"] is None and l["held_high"] is None:
            blank += 1
        else:
            tot += (float(l["held_low"] or 0) + float(l["held_high"] if l["held_high"] is not None else l["held_low"])) / 2
    return tot, blank


def build():
    L = load(IDX)
    lines = L["lines"]
    master = load(MASTER)
    overlay = {}
    for t, code in CARRIER_SETS.items():
        for row in load(ROOT / f"research/agents_{t}/out/FIX_ROWS.json")["rows"]:
            if row["item_code"] == code:
                assert row["line_id"] not in overlay, row["line_id"]
                overlay[row["line_id"]] = row["after"]
    new, disp = [], {}

    def add(fam, code, unit, el, label, basis, net=None, low=None, high=None, optional=False, vs=None):
        assert (net is None) != (low is None and high is None), (fam, code)
        d = dict(family=fam, item_code=code, unit=unit, element_id=el, label=label, basis=basis)
        d.update({"net": r(net)} if net is not None else {"low": r(low), "high": r(high)})
        if optional:
            d["optional"] = True
        if vs:
            d["vs_freelancer"] = vs
        new.append(d)

    # B1-06b excavation support (B1-06a dewatering / B1-06c: T-769 NOT_APPLICABLE)
    add("B1-06", "SITE.EXCAVATION_SUPPORT", "item", "SITE:B1-06b", "DRAWING-READ",
        "ST p.8 note 15 puts excavation protection / shoring on the contractor (extent by his specialist study); "
        "faces at the plot line >= 1.50 deep on all 4 sides (T-358 TRIGGERED); 1 lump-sum item, perimeter "
        "2 x (15.00 + 31.37) = 92.74 lm beside", net=1)

    # B4-05 spatter dash: one coat under every finished wall face, once (owner OD-V3B-4..7, mix 1:2 Q-79)
    for code, unit, el, fl in (("FIN.PLASTER", "m2", "SPATTER:INTERIOR", FREELANCER["spatter_interior_m2"]),
                               ("FIN.EXT.FINISH", "m2", "SPATTER:EXTERIOR", None),
                               ("EXT.FENCE.PLASTER", "m2", "SPATTER:FENCE", None)):
        tot, blank = carrier_total(lines, code, unit, overlay)
        assert blank == 0, (code, blank)
        vs = None
        if fl:
            vs = {"freelancer": fl, "diff": r(tot - fl), "pct": r(100 * (tot - fl) / fl, 1), "verdict":
                  "RULE_DIFFERENCE: freelancer = wet rooms + kitchens 433.83 + under soffit 70.71 only; owner OD-V3B-4..7 = every plastered face"}
        add("B4-05", "FIN.SPATTER_DASH", "m2", el, "ESTIMATE",
            f"= carrier {code} {unit} total {tot:.2f} (V3.0.81 index with the merged T-760 / T-763 / T-769 figures; "
            "owner OD-V3B-4..7 coat under every finished face once" + (", wet-room tile backing included" if code == "FIN.PLASTER" else "")
            + "; recompute from the carrier at wiring)",
            net=tot, vs=vs)

    # B4-10 exposed wall-tile edges (45-degree mitre OR steel profile, one finish per edge; choice = designer item)
    scaled = T368_DETERMINATE * TILE_TOP / T368_OLD_TOP
    add("B4-10", "FIN.WALL.TILE.EDGE", "lm", "TILE_EDGE:CORNERS_AND_ENDS", "ESTIMATE",
        f"T-368 determinate {T368_DETERMINATE} lm at the 3.65 tile top x 3.00 / 3.65 (owner tile top 3.00, 13 Nov) "
        f"= {scaled:.2f} + GF-14 wall end and flat stop 2 x 3.00 (no header on the slab plan) = {scaled + 6:.2f}; "
        "finish 45-degree OR steel profile (never both), designer list", net=scaled + T368_GF14_EDGES * TILE_TOP)
    add("B4-10", "FIN.WALL.TILE.EDGE", "lm", "TILE_EDGE:DOOR_JAMBS", "ESTIMATE",
        f"door-jamb tile edges: T-368 range 0 .. {T368_DOOR_EDGES_HIGH} lm (0 when the door frame covers the edge); "
        "frame / architrave detail not printed", low=0.0, high=T368_DOOR_EDGES_HIGH)

    # B5-02 gypsum decor ceiling (owner Q-57 A mod): board area = the decor ceiling area of FIN.CEILING
    ceil, cblank = carrier_total(lines, "FIN.CEILING", "m2", {})
    fl = FREELANCER["gypsum_decor_m2"]
    add("B5-02", "FIN.CEILING.GYPSUM", "m2", "CEILING:GYPSUM_DECOR", "ESTIMATE",
        f"= FIN.CEILING m2 of the candidate {ceil:.2f} ({cblank} lines still blank: T-768 fills them; recompute at "
        "wiring); owner Q-57 A mod + Q-48 A: gypsum decor ceiling in every room, moisture-resistant board type HELD "
        "(not specified); FIN.CEILING stays the physical area (B5-01): wire as the board item, not added to it",
        net=ceil, vs={"freelancer": fl, "diff": r(ceil - fl), "pct": r(100 * (ceil - fl) / fl, 1),
                      "verdict": "AGREE within 1 % before T-768's blanks"})

    # B5-03 cornice at the decor ceiling
    fl = FREELANCER["cornice_lm"]
    add("B5-03", "FIN.CEILING.CORNICE", "lm", "CEILING:CORNICE", "ESTIMATE",
        f"T-147 closed-room wall perimeter at the decor ceiling {T147_CORNICE_CLOSED_ROOMS} lm; no cornice / cove "
        "detail printed (Q-57 A mod: cove only with geometry or a detail, not carried); open zones without a wall edge "
        "not counted", net=T147_CORNICE_CLOSED_ROOMS,
        vs={"freelancer": fl, "diff": r(T147_CORNICE_CLOSED_ROOMS - fl), "pct": r(100 * (T147_CORNICE_CLOSED_ROOMS - fl) / fl, 1),
            "verdict": "UNRESOLVED: freelancer rooms 282.85 + wet rooms 144.61 lm; open-zone and wet-room runs to split by room"})

    # B7-05 nosing (T-424 was folded into T-766, whose fix rows carry no nosing line)
    add("B7-05", "FIN.STAIR.NOSING", "lm", "STAIR:NOSING", "ESTIMATE",
        f"one nosing per step edge = T-766 FIN.STAIR.STEP_LM {T766_STEP_LM} (READY; recompute when merged) + landing / "
        f"floor arrival edges {T412_LANDING_EDGES} (T-412 DRAWING-CONFIRMED) = {T766_STEP_LM + T412_LANDING_EDGES:.2f}; "
        "nosing form not printed (designer list)", net=T766_STEP_LM + T412_LANDING_EDGES)

    # B7-11 posts (glass panels not drawn anywhere: none)
    posts = sum(T361_POSTS.values())
    add("B7-11", "MET.RAILING.POST", "pcs", "RAILING:POSTS", "DRAWING-READ",
        "posts drawn on the roof X railings: " + ", ".join(f"{k} {v}" for k, v in T361_POSTS.items())
        + f" = {posts} (T-361); glass panels drawn nowhere and not specified: no glass line", net=posts)

    # B9-03 masonry accessories, owner Q-77 answer 2026-10-29: separate OPTIONAL items in the blocks section
    s355, s362 = load(T355), load(T362)
    mesh = s362["villa_mesh_conditional_m"]["black restated + white family A"]
    ties = s362["villa_ties_conditional_pcs"]["black + white family A"]
    resolved_junctions = s355["ties_primary_by_floor"]["GF"]["junctions"] + s355["ties_primary_by_floor"]["1F"]["junctions"] \
        + s355["ties_primary_by_floor"]["2F"]["junctions"] + sum(v["junctions"] for v in s362["white_family_A"]["by_floor"].values())
    per_j = ties["ties"] / resolved_junctions
    add("B9-03", "MAS.MESH_STRIP", "lm", "MASONRY:MESH_STRIP", "ESTIMATE",
        f"strip on every 3rd course of every block wall (Q-77): T-355 black restated by T-362 + white family A "
        f"(62.5 x 25 face, as T-765): certain {mesh['net_m']:.2f} .. + held levels {mesh['held_m']:.2f}; 7 walls of "
        "unknown block type not in the range (T-362)", low=mesh["net_m"], high=mesh["net_m"] + mesh["held_m"], optional=True)
    add("B9-03", "MAS.SHARMAT", "pcs", "MASONRY:SHARMAT", "ESTIMATE",
        f"one tie per 3rd course at every wall-to-column junction (Q-77): {ties['ties']} pcs at {resolved_junctions} "
        f"resolved junctions .. + {ties['junctions_held']} held junctions x {per_j:.2f} pcs average",
        low=ties["ties"], high=ties["ties"] + ties["junctions_held"] * per_j, optional=True)

    # B12-01 sanitary fixtures and floor drains (T-743 census from the sanitary sheets)
    s = load(T743)
    t, fd = s["totals_measured"], s["floor_drains_by_size"]
    for code, n, what in (("MEP.SAN.WC", t["WC"], "WC (GF 6, 1F 5, 2F 1)"),
                          ("MEP.SAN.BASIN", t["BASIN"], "wash basin (GF 11, 1F 5, 2F 1; 5 on both sheets)"),
                          ("MEP.SAN.SHOWER_TRAY", t["SHOWER_TRAY"], "shower tray (GF 1, 1F 2)"),
                          ("MEP.SAN.SHOWER_WALKIN", t["SHOWER_WALKIN"], "walk-in shower zone, screen + mixer (1F 2, 2F 1)"),
                          ("MEP.SAN.FLOOR_DRAIN_4IN", fd["4in"], "floor drain 4 in"),
                          ("MEP.SAN.FLOOR_DRAIN_3IN", fd["3in"], "floor drain 3 in")):
        add("B12-01", code, "pcs", "SANITARY:" + code.split(".")[-1], "MEASURED",
            f"{what}: {n} pcs counted on sanitary-7757 p.1-3 fitted to the plan (T-743)", net=n)
    for code, key, what in (("MEP.SAN.KITCHEN_SINK", "KITCHEN_SINK", "GF kitchen sink (kitchen FD4 drawn, sink symbol not)"),
                            ("MEP.SAN.WASHING_MACHINE_POINT", "WASHING_MACHINE_POINT", "1F laundry washing-machine point (FD4 drawn)")):
        add("B12-01", code, "pcs", "SANITARY:" + key, "ESTIMATE",
            f"{what}: 1 per room by function (T-743 HELD the symbol); designer list", net=s["held"][key])

    # B13-06 joinery: owner defaults wardrobe 2.40, kitchen base 0.85 / wall 0.70 (lengths drawn, heights default)
    for code, runs, h, lab, note in (
            ("JOIN.WARDROBE", JOINERY_FULL, 2.40, "DEFAULT", "boxes drawn on layer 5, no wall line (T-223 joinery rule)"),
            ("JOIN.KITCHEN.BASE", COUNTER_BASE, 0.85, "DEFAULT", "counter outlines drawn; pantry peninsula on the open edge not counted"),
            ("JOIN.KITCHEN.WALL", COUNTER_WALL, 0.70, "ESTIMATE", "wall units not drawn: on the wall-backed legs, none under a window")):
        add("B13-06", code, "lm", "JOINERY:" + code.split(".")[-1], lab,
            " + ".join(f"{k} {v:.3f}" for k, v in runs.items()) + f" = {sum(runs.values()):.3f} lm; height {h:.2f} "
            f"company default (owner 13 Nov); no interior drawing; {note}", net=sum(runs.values()))

    def D(fam, kind, evidence, figure=None):
        disp[fam] = dict(disposition=kind, evidence=evidence, **({"figure_beside": figure} if figure else {}))

    for fam in ("B1-01", "B1-05", "B1-07"):
        D(fam, "COVERED_BY_ROW", "T-769 new_lines (MERGED f8319feb), wired by a T-770 round")
    D("B1-06", "COVERED_BY_ROW", "B1-06a dewatering NOT_APPLICABLE by T-769 (water -4.50 vs formation -1.67); "
      "B1-06b support = the new line above; B1-06c none printed (T-358)")
    D("B2-01", "REGISTER_NO_LINE", "a room register, not a quantity: every line carries its room id (arch_measure.room_id); master 1.45.0 N/A")
    D("B2-03", "REGISTER_NO_LINE", "Lead decision F-T730-5 (master 1.76.0): coverage denominator only, no candidate line",
      "gross floor plate MEASURED T-720: GF 278.27, 1F 209.84, 2F 55.08 = 543.19 m2")
    D("B2-04", "REGISTER_NO_LINE", "a functional zone; its floor, wall tile and WP are on B3-02 / B4-01 / B8 lines (T-351)",
      "open pantry 4.50 x 3.00 = 13.50 m2 (T-120)")
    D("B2-05", "REGISTER_NO_LINE", "a void is a deduction, not a payable item: the GF light well is out of the GF ceiling "
      "(T-147), stair shafts on B7 lines", "GF light well 23.24 m2 (ST p.4 face; 1F plan VOID 4.00 x 5.87 = 23.48)")
    D("B3-03", "NOT_APPLICABLE_WITH_EVIDENCE", "no marble floor drawn or noted (T-091, 12 arch pages + DXF); GF entrance / hall "
      "floor is B3-01 (T-418); the freelancer 'entrance marble' rows are the E1 external stair (B7-02 / B7-04, T-471)")
    D("B3-07", "NOT_APPLICABLE_WITH_EVIDENCE", "hidden skirting profile printed nowhere (T-409); doorway boundaries carry "
      "the marble threshold lines (B3-04); no profile / transition strip printed")
    D("B4-02", "COVERED_BY_LINE", "kitchen / laundry / pantry faces are full-height wet-room tile on FIN.WALL.TILE (B4-01) "
      "by owner rule (UP-WET-001, Q-37 A / Q-40 A / Q-48 A); 0 own faces (T-351)")
    D("B4-04", "COVERED_BY_LINE", "external render is FIN.EXT.FINISH (18 lines, T-760 figures), mapped to B4-07 in master "
      "1.81.0: PROPOSAL for the next master: move FIN.EXT.FINISH to B4-04 (render), keep paint / edges in B4-07; no line moves")
    D("B4-11", "NOT_APPLICABLE_WITH_EVIDENCE", "no material legend, 0 of 675 DXF texts name a cladding; render + paint on "
      "every face (T-360 MERGED 5bde82a7); porch arch surround on the designer list")
    D("B5-05", "NOT_APPLICABLE_WITH_EVIDENCE", "no access panel drawn or noted; MEP drawings absent: revisit with B12 at the MEP stage")
    D("B6-08", "COVERED_BY_ROW", "T-768 (worker 2, TODO) fills DOOR.LIFT_LANDING: 3 landings GF / 1F / 2F (T-619), "
      "1.00 x 2.10 default; the lines are absent from V3.0.81, so T-768 adds them", "3 pcs")
    D("B7-10", "NOT_APPLICABLE_WITH_EVIDENCE", "no wall handrail drawn (one FIN.HANDRAIL EXCLUDED_WITH_REASON line, T-199 / UP-STAIR-013)")
    for fam in ("B7-14", "B11-02", "B11-03", "B11-04"):
        D(fam, "PARKED", "rebar parked by the owner 2026-11-11: approximate tons by ratio at the end")
    D("B8-04", "COVERED_BY_LINE", "showers sit inside the wet-room membrane FIN.WP.FLOOR + upturn (B8-01 / B8-03), "
      "no separate tanking (Q-40 A, T-369); 6 showers (T-743)")
    D("B8-07", "NOT_APPLICABLE_WITH_EVIDENCE", "no balcony / terrace label, no slab projecting with a door onto it; the 2F "
      "roof terrace and the pool-court slab are on FIN.WP.ROOF (B8-06) (T-486 MERGED)")
    D("B9-05", "NOT_APPLICABLE_WITH_EVIDENCE", "parapets carried all-RC on STR.CONC.PARAPET (T-761 MERGED: sections A-A / "
      "B-B cut every parapet in RC); ST p.14 typical block-on-upstand alternative noted in T-761's basis")
    D("B12-02", "HELD_MEP_STAGE", "drainage / supply runs: the sanitary sheets are not to scale (plotted 1:108 vs printed "
      "1:100, T-743); runs at the MEP stage (owner default 'drainage runs at MEP')")
    for fam, what in (("B12-03", "electrical"), ("B12-04", "HVAC"), ("B12-05", "low-voltage")):
        D(fam, "HELD_MEP_STAGE", f"no {what} drawing in the Drive set; MEP stage")
    D("B13-03", "NOT_APPLICABLE_WITH_EVIDENCE", "garden labels only, no landscape / irrigation plan (T-427); out of the owner scope freeze")
    D("B13-05", "NOT_APPLICABLE_WITH_EVIDENCE", "no movement joint or sealant printed on ST p.1-16, ARCH p.1-12, SAN p.1-3 (T-365); "
      "owner Q-42 gives a width only; out of the owner scope freeze")
    D("B13-07", "NOT_APPLICABLE_WITH_EVIDENCE", "no canopy or pergola on any sheet (T-199, T-471); railings, gates and "
      "shutters are on B7-09 / B13-08 / B13-04 / B6-05")

    miss = missing_families(master, lines)
    covered = {d["family"] for d in new} | set(disp)
    mapping = {}
    for d in new:
        mapping.setdefault(d["item_code"], d["family"])
    summary = {
        "missing_families_in_candidate": len(miss),
        "with_new_lines": sorted({d["family"] for d in new}),
        "new_lines": len(new),
        "dispositions": {k: sorted(f for f, v in disp.items() if v["disposition"] == k)
                         for k in sorted({v["disposition"] for v in disp.values()})},
        "not_covered": sorted(set(miss) - covered),
        "missing_sheet_after_wiring": sorted(f for f, v in disp.items() if v["disposition"] == "HELD_MEP_STAGE"),
    }
    return {
        "schema": "URBAN_FIX_ROWS_V1",
        "task": "T-771",
        "candidate_version": L["candidate_version"],
        "inputs": [str(p.relative_to(ROOT)) for p in (IDX, MASTER, T743, T355, T362)]
                  + [f"research/agents_{t}/out/FIX_ROWS.json" for t in CARRIER_SETS],
        "summary": summary,
        "rows": [],
        "new_lines": new,
        "dispositions": disp,
        "master_mapping_proposal": {"item_codes_to_family": mapping, "move": {"FIN.EXT.FINISH": "B4-07 -> B4-04"},
                                    "family_field": "disposition (builder Missing sheet skips every disposition but HELD_MEP_STAGE)"},
    }


def md(d):
    out = ["# T-771 missing families: new lines and dispositions (fix-row set, unwired)", "",
           f"Candidate {d['candidate_version']}; {d['summary']['missing_families_in_candidate']} families without a line; "
           f"{d['summary']['new_lines']} new lines in {len(d['summary']['with_new_lines'])} families; not covered: "
           f"{d['summary']['not_covered'] or 'none'}.", "",
           "| Family | Item | Unit | Figure | Label | Basis |", "|---|---|---|---|---|---|"]
    for n in d["new_lines"]:
        fig = n["net"] if "net" in n else f"{n['low']} .. {n['high']}"
        out.append(f"| {n['family']} | {n['item_code']} ({n['element_id']}) | {n['unit']} | {fig} | {n['label']}"
                   f"{' OPTIONAL' if n.get('optional') else ''} | {n['basis']} |")
    out += ["", "| Family | Disposition | Evidence | Figure beside |", "|---|---|---|---|"]
    for f, v in d["dispositions"].items():
        out.append(f"| {f} | {v['disposition']} | {v['evidence']} | {v.get('figure_beside', '')} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
    if a.check:
        ok = (OUT / "FIX_ROWS.json").read_text() == js and (OUT / "FIX_ROWS.md").read_text() == md(d)
        print("T-771 fix rows reproduce:", ok)
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "FIX_ROWS.json").write_text(js)
    (OUT / "FIX_ROWS.md").write_text(md(d))
    print(json.dumps(d["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
