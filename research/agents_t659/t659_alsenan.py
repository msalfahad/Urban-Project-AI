"""T-659 development villa (Alsenan): the 16 HELD small-B10 lines of trial BOQ r4 (candidate V3.0.61), line by line.

Inputs are committed, sha-pinned files only (no drawing is read here; the drawing reads of this run are recorded as
printed facts with their sheet, below, and were made from Drive 'Alsenan chalet project' / ST7757.pdf (sha256 74da1523),
ST7757 dxf.dxf (9f9d1179), P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55) and p7757_arch_sheet03.pdf, decoded into
.work/private only). No client name, coordinate or drawing content beyond the printed figures cited is tracked.

Run: python -I research/agents_t659/t659_alsenan.py  -> research/agents_t659/out/T659_LEDGER.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t659_rules as R  # noqa: E402

LINE_INDEX = ROOT / "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
T572 = ROOT / "research/agents_t572/out/T572_HELD_BOUNDS.json"
TRIAL_R4 = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654_LINES.csv"
PINS = {LINE_INDEX: "10e5f116d30af67f", T572: "a39e7b4b838e3590", TRIAL_R4: "39e55ea327521a4c"}
OUT = HERE / "out/T659_LEDGER.json"

# Printed facts read this run (own reads; sheet + what is printed). Figures in m.
READS = {
    "ST_P7_POOL": "ST p.7 DETAIL OF SWIMMING POOL (N.I.S.): walls 20, base 40, plan and depths 'AS PER ARCH'; under the "
                  "base '5cm SECREED / 5cm INSULATION MEMBRANE / 10cm PLAIN CONCRETE'; no step drawn",
    "ST_P7_DOME": "ST p.7 DETAIL OF DOME (N.I.S.): chord 442, rise 190, shell 10 (the two 1F-roof domes, Q-27; released)",
    "ST_P14_LIFT": "ST p.14 DETAIL OF LIFT WITH ISOLATED FOOTING: pit walls 20; pit depth 'As Per Lift Manufactures "
                   "recommendations'; footing 'AS PER SCHEDULE'; under the footing '5cm Screed / Water proofing membrane / "
                   "10cm Plain con.'",
    "ST_P14_BW": "ST p.14 TYPICAL BOUNDARY WALL plan (N.I.S.): GROUND BEAM (20x40), pad (130x80x30) at each (20x30) column, "
                 "spacing 'SEE ARCH PLAN'; SECTION A-A: lower G.B 20 wide on an 80 base (G.B soffit = base soffit, the "
                 "base 80 measured from the G.B outer face), plain concrete under it projecting 10 on the inner side, "
                 "depth 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'",
    "ST_P14_PARAPET": "ST p.14 parapets: TYPICAL (P1) RC upstand 30 'MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING', brick "
                      "above, cap 'AS PER ARC.'; P2 RC 130 + 10 cap on a 40 beam; P3 RC 105 tapering 15 / 30; none keyed",
    "ARCH_GF_FENCE": "p7757_arch_sheet03 (GF plan) own read along the neighbour side (31.37) and the street / sea fronts: "
                     "the fence is drawn as two parallel lines; no 20 x 30 boundary-column symbol is drawn (agrees T-065 "
                     "M4: none on either plan)",
}

PARAPET_FLOORS = {  # T-319 (Gate B MERGED): floor = top x 0.30 m RC above the slab top, DRAWING-CONFIRMED; top high m2
    "L-1d419b64e8ca1af30fb4": ("1.799103", "6.03701", "annex roof +4.30"),
    "L-b5ffc172a354375ca107": ("1.677887", "5.67398", "GF terrace +5.50"),
    "L-9a2c81164ec6499cc28c": ("2.949453", "9.84653", "1F roof +9.70"),
    "L-030538dda6a32c601c4c": ("1.6245", "5.415", "2F roof +13.90"),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def check_pins() -> None:
    for p, h in PINS.items():
        got = _sha(p)
        if got != h:
            raise R.Refused(f"input {p.name} changed: {got} != pinned {h}")


def before_lines() -> dict:
    idx = json.loads(LINE_INDEX.read_text())
    t572 = {c["line_id"]: c for c in json.loads(T572.read_text())["components"] if c.get("line_id")}
    keys = ("PARAPET", "BOUNDARY", "BLINDING", "DOME", "POOL", "LIFT")
    out = {}
    for ln in idx["lines"]:
        ic = ln["item_code"]
        if ic.startswith("STR.CONC.") and ln["class"] == "HELD" and any(k in ic for k in keys):
            out[ln["line_id"]] = {"item_code": ic, "element_id": ln["element_id"], "candidate_low": ln["held_low"],
                                  "candidate_high": ln["held_high"], "t572": t572.get(ln["line_id"])}
    return out


def build() -> dict:
    check_pins()
    before = before_lines()
    D, dim = Decimal, R.dim
    rows = []

    # --- B10-12 parapets: 4 blank, the T-319 floor beside, + top m3 per m of b_edge (D-39) -------------------------
    for lid, (floor, top_hi, chain) in PARAPET_FLOORS.items():
        rows.append(R.component(
            lid, "STR.CONC.PARAPET", before[lid]["element_id"], "HELD_BLANK",
            item="Q-65 C (material above the upstand: designer) + D-39 (roof build-up b_edge) + the P1 margin; no P1/P2/P3 "
                 "keyed to a run",
            floor={"m3": floor, "status": "DRAWING-CONFIRMED (T-311 Checker run; T-319 MERGED)",
                   "basis": f"{chain}: drawn top m2 x 0.30 m RC above the slab top, shared by P1 / P2 / P3"},
            coefficients=[{"per": "m of roof build-up depth at the edge (b_edge, D-39)", "m3_per_unit": top_hi,
                           "basis": "drawn top m2 (T-324, high end)"}],
            sources=["ST_P14_PARAPET"]))

    # --- B10-11 boundary pad: count not printed; per-pad coefficient net of the through-running G.B (R-T659-3) -----
    pad = R.pad_net_of_through_beam(dim("1.30", "ST p.14 plan (130x80x30)"), dim("0.80", "ST p.14 plan + A-A '80'"),
                                    dim("0.30", "ST p.14 plan (130x80x30)"), dim("0.20", "ST p.14 A-A G.B '20'"),
                                    dim("0.40", "ST p.14 plan GROUND BEAM (20x40)"))
    rows.append(R.component(
        "L-cda8f41522dc6f42b3d6", "STR.CONC.BOUNDARY_PAD", before["L-cda8f41522dc6f42b3d6"]["element_id"], "HELD_BLANK",
        item="pad count = boundary-column count, 'SEE ARCH PLAN': no boundary column drawn on the architectural or "
             "structural plans (own GF read; T-065 M4); Q-28 A provisional",
        coefficients=[{"per": "pad (net of the G.B running through it on the same soffit, R-T659-3)",
                       "m3_per_unit": pad["net_m3"], "basis": "1.30 x 0.80 x 0.30 - 0.20 x 1.30 x 0.30 (ST p.14 A-A)"},
                      {"per": "pad gross (only if the G.B stops at each pad face)", "m3_per_unit": pad["gross_m3"],
                       "basis": "1.30 x 0.80 x 0.30 (T-400 coefficient)"}],
        sources=["ST_P14_BW", "ARCH_GF_FENCE"]))

    # --- B10-11 boundary wall band: two printed sections give the bound; Q-28 A and the line's point beside ---------
    lo = R.box(dim("70.49", "91.94 closed centreline (plot 31.37 x 15.00 printed, band 0.20) - 21.45 in 9 footings (T-065)"),
               dim("0.20", "ST p.2 band / p.14 G.B"), dim("0.40", "ST p.14 GROUND BEAM (20x40)"))
    hi = R.box(dim("91.94", "2 x 31.17 + 2 x 14.80 (plot 31.37 x 15.00 less the 0.20 band, printed)"),
               dim("0.20", "ST p.10 B.W 20 x 60"), dim("0.60", "ST p.10 B.W 20 x 60"))
    rows.append(R.component(
        "L-6290a9f3d93f38cd46d6", "STR.CONC.BOUNDARY_WALL", before["L-6290a9f3d93f38cd46d6"]["element_id"], "BOUNDED",
        low=lo, high=hi,
        low_basis="typical G.B 0.20 x 0.40 on the 70.49 m free of footings (ST p.14)",
        high_basis="B.W row 0.20 x 0.60 over the whole closed 91.94 m (ST p.10), gross of the 21.45 m inside footings",
        item="section B.W 20x60 vs typical 20x40 (designer RFI, Q-28); band founding level 'AS PER EXCAVATION DEPTH' not "
             "printed, so whether the 21.45 m shares the footings' elevation is open (owner's Q-28 caveat)",
        beside=[{"what": "Q-28 A owner-provisional reading (not released)", "m3": "8.459",
                 "basis": "(91.94 - 21.45) x 0.20 x 0.60"},
                {"what": "candidate V3.0.61 line point (one reading, side 1 lost: T-065 / T-572)", "m3": "7.2204"},
                {"what": "freelancer", "m3": "8.604", "class": "WITHIN"}],
        sources=["ST_P14_BW"]))

    # --- B10-01 blinding: the 5 bounded pieces unchanged (each end drawn), the boundary base blank -----------------
    bl_items = {
        "L-080c97f5f6a92452cd04": ("F10 + F readings A / B (Q-31 C), 0.10 thick 0.10 past each face", False),
        "L-10032bf9a60368473a7b": ("D-14: the 0.10 projection beyond the plot line may not be built", True),
        "L-16b95607fc88cda3844a": ("FF raft projection not dimensioned (ST p.14 draws it, prints 10cm only)", False),
        "L-35382b18e2e362df3ae6": ("D-15: ST p.13 prints no blinding under straps", True),
        "L-7a5214a334ea3559fa2d": ("D-33 / D-35 ground-beam sections; plan-distinct of the pit layer (T-478)", False),
    }
    for lid, (item, ex_open) in bl_items.items():
        c = before[lid]["t572"]
        rows.append(R.component(lid, "STR.CONC.BLINDING", before[lid]["element_id"], "BOUNDED",
                                low=c["low"], high=c["high"], low_basis=c["low_basis"], high_basis=c["high_basis"],
                                item=item, existence_open=ex_open,
                                sources=["ST_P14_LIFT"] if lid == "L-16b95607fc88cda3844a" else []))
    per_pad_blind = R.box(dim("1.30", "ST p.14 pad length"), dim("0.90", "ST p.14 A-A: base 80 + projection 10"),
                          dim("0.10", "ST p.13 / p.14 '10cm Plain con.'"))
    rows.append(R.component(
        "L-d0313e5d204e2758996a", "STR.CONC.BLINDING", before["L-d0313e5d204e2758996a"]["element_id"], "HELD_BLANK",
        item="pad count not printed (as the pad line); under the G.B between pads no blinding is drawn (A-A is cut "
             "through a pad); end projections of the pad blinding not dimensioned",
        coefficients=[{"per": "pad (AT_LEAST: end projections not printed)", "m3_per_unit": per_pad_blind,
                       "basis": "1.30 x 0.90 x 0.10 (ST p.14 A-A)"}],
        sources=["ST_P14_BW"]))

    # --- B10-09 dome 3 (upper roof): no structural detail; thickness not printed --------------------------------
    cap = R.cap_area_per_m(dim("4.41", "arch elevations p.6 / p.8 width '441' at +14.40 (Q-27 text)"),
                           dim("2.15", "arch elevations p.6 / p.8 '215' above +14.40 (Q-27 text)"))
    rows.append(R.component(
        "L-d5401fa8986900c66c37", "STR.CONC.DOME", before["L-d5401fa8986900c66c37"]["element_id"], "HELD_BLANK",
        item="Q-27 A (three domes) with no structural detail for the upper-roof dome: shell thickness, ring and whether "
             "'215' is the shell rise not printed; the 1F-roof detail (442 / 190 / 10) is another element's (no borrowing)",
        coefficients=[{"per": "m of shell thickness (thin-shell outer cap area, architectural envelope reading)",
                       "m3_per_unit": cap, "basis": "pi x (2.205^2 + 2.15^2)"}],
        sources=["ST_P7_DOME"]))

    # --- B10-10 pool steps: not drawn ------------------------------------------------------------------------
    rows.append(R.component(
        "L-b62a7065645589011141", "STR.CONC.POOL", before["L-b62a7065645589011141"]["element_id"], "HELD_BLANK",
        item="steps NOT DRAWN on ST p.7 (own read) nor dimensioned on the architectural plan: consultant item (owner "
             "2026-10-19 16:45, T-183)", sources=["ST_P7_POOL"]))

    # --- B10-10 lift tie beam and pit walls ------------------------------------------------------------------
    rows.append(R.component(
        "L-5ae06fda7d729d54c033", "STR.CONC.LIFT", before["L-5ae06fda7d729d54c033"]["element_id"], "HELD_BLANK",
        item="D-43: tie beam at 3.00 (ST p.8 note 19), section not printed",
        coefficients=[{"per": "m2 of tie-beam section", "m3_per_unit": "5.5",
                       "basis": "drawn length 5.500 m (T-419 DRAWING-CONFIRMED)"}]))
    rows.append(R.component(
        "L-684fcad323adc0c8a267", "STR.CONC.LIFT", before["L-684fcad323adc0c8a267"]["element_id"], "HELD_BLANK",
        item="D-43: pit depth 'As Per Lift Manufactures recommendations' (ST p.14) not printed",
        floor={"m3": "1.903", "status": "FLAGGED NOTE1_ON_LIFT_RAFT (Checker to accept ST p.9 note 1 on the lift raft)",
               "basis": "net ring 1.10 m2 (walls 20, ST p.14; R-T394-6) x h >= 1.73 (T-572)"},
        coefficients=[{"per": "m of pit wall height", "m3_per_unit": "1.1", "basis": "net ring 1.10 m2 (T-322 / R-T394-6)"}],
        beside=[{"what": "freelancer net share", "m3": "1.650", "class": "BELOW_DRAWN_LOWER if note 1 applies"}],
        sources=["ST_P14_LIFT"]))

    # accounting: every HELD small-B10 line of the candidate once
    want = set(before)
    got = {r["line_id"] for r in rows}
    if want != got:
        raise R.Refused(f"line accounting: missing {sorted(want - got)}, extra {sorted(got - want)}")
    for r in rows:
        b = before[r["line_id"]]
        r["before"] = {"candidate_V3_0_61": [b["candidate_low"], b["candidate_high"]]}
    named_missing = [{
        "what": "POOL BLINDING: ST p.7 prints '10cm PLAIN CONCRETE' under the pool base and slope; no STR.CONC.BLINDING "
                "(or any) line carries it in V3.0.61 (T-347 'pool blinding x2 MISSING'; T-183 B >= 1.222 m3)",
        "status": "MISSING (named, never 0)", "action": "Lead: a lane S row to add the line with its drawn bound"}]
    findings = [
        {"id": "F-T659-1", "what": "boundary pad coefficient 0.312 m3 (T-400) is gross of the G.B that runs through the "
                                   "pad on the same soffit (ST p.14 A-A): 0.078 m3 per pad counted twice with the band "
                                   "line; net 0.234 m3 per pad (R-T659-3)", "m3_per_pad": "0.078"},
        {"id": "F-T659-2", "what": "boundary band: candidate line V3.0.61 carries the single reading 7.2204 as a closed "
                                   "range; the drawn bound is 5.6392 .. 11.0328 (overlay F-T628-1 already carries it in "
                                   "trial r4); T-661 must wire the bound, Q-28 A 8.459 beside"},
    ]
    totals_after = R.ledger_totals(rows)
    return {"schema": "T659_LEDGER_V1", "candidate": "ARCH_TAKEOFF_V3.0.61 / trial BOQ r4 (T-654)",
            "pins": {p.name: h for p, h in PINS.items()}, "reads": READS, "rows": rows, "totals_after": totals_after,
            "named_missing": named_missing, "findings": findings}


def main() -> None:
    out = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out["totals_after"]))


if __name__ == "__main__":
    main()
