"""T-371 development-villa input: printed SHAPE readings per released-route bar population + the candidate binding.

Readings are by eye from Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523.., 16 pages, no text layer),
re-read this run at 110 / 220 / 400 dpi: p.3 (ground-slab mesh label), p.8 (notes 1 - 24), p.9 (schedules + DETAILS OF
COLUMN REINFORCEMENT), p.10 (simple beams), p.11 / p.12 (continuous beams + typical span diagram), p.13 (TYP. DETAIL OF
ISOLATED FOOTING x 2, ground-beam sections x 4), p.15 (twisted column, beam carrying planted column, TYP. SLAB ON BEAMS
DETAIL, temperature schedule). Positions are cited by sheet and detail (p.13 - p.16 are not in the DXF). Nothing of
the drawings is copied: only the shape attribute states and the label notation needed by the census.

The binding reads the merged T-297 extract of the candidate's reinforcement lines (ARCH_TAKEOFF_V3.0.16 = V3.0.17,
2,505 lines), pinned by sha256; every line goes to exactly one population or to T-359 (special elements).

Repeat: python -I t371_alsenan_input.py            (writes ALSENAN_BAR_SHAPE_INPUT.json + LINE_BINDING_T371.json)
        python -I t371_alsenan_input.py --check    (rebuilds in memory and compares with the committed files)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXTRACT = ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"
EXTRACT_SHA = "2f28367b81fe362d98d8a97080adb62cfd9a3c0a880fc20d201735e6eba39760"
OUT_INPUT = HERE / "ALSENAN_BAR_SHAPE_INPUT.json"
OUT_BINDING = HERE / "LINE_BINDING_T371.json"

# RFI ids used below, as titled in the board's rfi/A_PRIORITY_RFI.md and rfi/B_REMAINING_RFI.md (2026-10-30 12:40)
RFI_REGISTER = ["RFI-S15", "RFI-S18", "RFI-S22", "RFI-B-S09", "RFI-B-S10", "RFI-B-S12", "RFI-B-S19", "RFI-B-S20",
                "RFI-B-S21", "RFI-B-S22"]
ANSWERED_RULES = ["OWNER_OPTION_B_2026-10-29", "Q-71"]
OTHER_CENSUS = ["T-359"]


def A(state, ref="", **kw):
    d = {"state": state}
    if ref:
        d["ref"] = ref
    d.update(kw)
    return d


NA = A("NOT_APPLICABLE")
BEND_GAP = A("NOT_PRINTED", gap="G-T371-0", note="no bend diameter / hook extension printed anywhere (p.8 notes 1-24)")


def bend_if(rfi):
    """Bend diameter of a population whose shape is not printed: needed only if the RFI's answer is a bent shape (then
    G-T371-0 applies); it is asked with the shape, never assumed straight."""
    return A("NOT_PRINTED", rfi=rfi, note="only if the answered shape is bent; then G-T371-0")




def straight(ref, applies=None, typical=False):
    body = A("PRINTED_TYPICAL" if typical else "PRINTED", ref, value="straight", **({"applies_to": applies} if typical else {}))
    e = A(body["state"], ref, value="straight end", **({"applies_to": applies} if typical else {}))
    return {"body": body, "end_1": e, "end_2": dict(e), "leg_length": NA, "hook": NA, "bend_diameter": NA, "crank": NA}


P9COL = "p.9 DETAILS OF COLUMN REINFORCEMENT (3 link arrangements by L: L <= 50, 50 < L < 80, 80 < L < 120 cm)"
P13FT = "p.13 TYP. DETAIL OF ISOLATED FOOTING (left: upper G.B > 2.5 m above; right: < 2.5 m)"
P13GB = "p.13 Ground Beams sections (> 5 m, < 5 m, < 2.5 m, exterior walls)"
P15SL = "p.15 TYP. SLAB ON BEAMS DETAIL"
P1112 = "p.11 / p.12 continuous-beam rows + typical span diagram"


def link(ref, applies, rfi_hook=None, gap_hook=None, nested=None):
    hook = A("DRAWN_UNDIMENSIONED", ref, value="hook drawn at one corner (angled tick), length / angle not dimensioned",
             **({"rfi": rfi_hook} if rfi_hook else {"gap": gap_hook}))
    d = {"body": A("PRINTED_TYPICAL", ref, applies_to=applies, value="closed rectangular link"),
         "end_1": hook, "end_2": dict(hook), "leg_length": A("PRINTED_TYPICAL", ref, applies_to=applies,
         value="link sides = member section less covers (section printed; cover p.8 note 22, a minimum)"),
         "hook": dict(hook), "bend_diameter": BEND_GAP, "crank": NA}
    if nested:
        d["crank"] = A("NOT_PRINTED", nested[0], rfi=nested[1], value="inner link size / legs (symbol only)")
    return d


POPS = [
    # ---------------- footings (isolated, p.9 schedule + p.13 typical) ----------------
    {"pop_id": "FTG-BOT-MESH", "element_class": "ISOLATED_FOOTING",
     "description": "footing bottom mesh, short and long bars (p.9 SHORT / LONG BARS)",
     "attrs": straight(P13FT + ": 'Long bars' / 'Short bars' drawn straight, no end bend", "ISOLATED_FOOTING", True),
     "note": "shape straight; the bar END POSITION vs the boxed-bar legs is a length question (T-299 / T-171), not shape"},
    {"pop_id": "FTG-TOP-MESH", "element_class": "ISOLATED_FOOTING",
     "description": "footing top layer F8 / F12 / F13 / F14 / FF (p.9 TOP rows)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S09", value="no top layer drawn on either p.13 typical"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S09"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S09"),
               "leg_length": A("NOT_PRINTED", rfi="RFI-B-S09"), "hook": A("NOT_PRINTED", rfi="RFI-B-S09"),
               "bend_diameter": bend_if("RFI-B-S09"), "crank": NA}},
    {"pop_id": "FTG-TOP-END-LEGS", "element_class": "ISOLATED_FOOTING",
     "description": "FF / F12 - F14 cage: top-layer end legs (p.9 REMARKS cage symbol)",
     "attrs": {"body": A("DRAWN_UNDIMENSIONED", "p.9 footing schedule REMARKS: closed-rectangle symbol with dots on F12, "
                         "F13, F14, FF", rfi="RFI-B-S09", value="cage symbol, no shape dimension"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S09"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S09"),
               "leg_length": A("NOT_PRINTED", rfi="RFI-B-S09"), "hook": NA, "bend_diameter": BEND_GAP, "crank": NA}},
    {"pop_id": "FTG-BOXED", "element_class": "ISOLATED_FOOTING",
     "description": "footing 'BOXED' bars (p.9 BOXED '3+n')",
     "attrs": {"body": A("PRINTED_TYPICAL", P13FT + ": 'Boxed bars' leader", applies_to="ISOLATED_FOOTING",
                         value="inverted U: top horizontal + a vertical leg down each side to the bottom mesh"),
               "end_1": A("DRAWN_UNDIMENSIONED", P13FT, gap="G-T371-1", value="leg foot at the bottom mesh, no return drawn"),
               "end_2": A("DRAWN_UNDIMENSIONED", P13FT, gap="G-T371-1", value="as end_1"),
               "leg_length": A("DRAWN_UNDIMENSIONED", P13FT, gap="G-T371-1",
                               value="footing H printed (p.9) but the leg's end level is not dimensioned"),
               "hook": A("DRAWN_UNDIMENSIONED", P13FT, gap="G-T371-1",
                         value="angled marks at both upper inner corners: meaning (hook of which bar) not printed"),
               "bend_diameter": BEND_GAP, "crank": NA},
     "count_label": "", "note": "diameter of the boxed bar is printed nowhere (T-171 / T-299); '3+n' meaning open"},
    {"pop_id": "STARTER", "element_class": "ISOLATED_FOOTING",
     "description": "column starter bars in the footing / neck (route G NECK MAIN)",
     "attrs": {"body": A("PRINTED_TYPICAL", P13FT + ": 'Column reinforcement' to an L foot on the bottom mesh",
                         applies_to="ISOLATED_FOOTING", value="L: vertical + horizontal foot, foot end bent up"),
               "end_1": A("PRINTED_TYPICAL", P13FT, applies_to="ISOLATED_FOOTING",
                          value="foot end: short up-bend drawn (undimensioned, see hook)"),
               "end_2": A("PRINTED_TYPICAL", P13FT + " right: '40 ø' above the footing top", applies_to="ISOLATED_FOOTING",
                          value="top: projection 40 ø (right detail); left detail cranks drawn, no dimension (T-366 F-T366-1)"),
               "leg_length": A("PRINTED_MINIMUM", P13FT + ": foot 'Min. 30cm'", gap="G-T371-2", min_m=0.30,
                               value="foot >= 0.30 m (a minimum, not an exact length)"),
               "hook": A("DRAWN_UNDIMENSIONED", P13FT, gap="G-T371-2", value="up-bend at the foot end, no dimension"),
               "bend_diameter": BEND_GAP,
               "crank": A("DRAWN_UNDIMENSIONED", P13FT + " left", gap="G-T371-2",
                          value="splice cranks drawn on the deep detail, no offset / length")},
     "note": "'Max. 10cm' on both details fixes the foot's position above the mesh, not a bar length"},
    # ---------------- columns ----------------
    {"pop_id": "COL-MAIN-BODY", "element_class": "COLUMN",
     "description": "column / neck main bars, body (p.9 REINF; route G COL / NECK MAIN; MAIN BARS net)",
     "attrs": straight("p.13 footing details 'Column reinforcement' + p.15 twisted-column elevations: straight vertical "
                       "lines; p.9 schedule count", "COLUMN", True)},
    {"pop_id": "COL-TOP-END", "element_class": "COLUMN",
     "description": "column bar ends stopping at a roof",
     "attrs": {"body": A("PRINTED", "p.9 schedule (bars stop: '—ø—' storeys)", value="straight"),
               "end_1": A("NOT_PRINTED", gap="G-T371-3", value="no column-head detail: bend into the roof slab or straight not printed"),
               "end_2": NA, "leg_length": A("NOT_PRINTED", gap="G-T371-3"), "hook": A("NOT_PRINTED", gap="G-T371-3"),
               "bend_diameter": BEND_GAP, "crank": NA}},
    {"pop_id": "COL-SECTION-TRANSITION", "element_class": "COLUMN",
     "description": "column bars at a section change (p.9: e.g. 30 x 50 foundation -> 20 x 50 GF; legend C.S)",
     "attrs": {"body": A("PRINTED", "p.9 schedule (size per storey)", value="straight above / below"),
               "end_1": NA, "end_2": NA, "leg_length": NA, "hook": NA, "bend_diameter": BEND_GAP,
               "crank": A("NOT_PRINTED", gap="G-T371-3", value="offset crank or stop-and-new-bar: no detail")}},
    {"pop_id": "COL-STOREY-LAP", "element_class": "COLUMN", "owned_by": "T-366",
     "description": "column storey laps (LAP at storey bottom)",
     "attrs": {"body": A("PRINTED", "p.9 schedule", value="straight overlap of two straight bars"),
               "end_1": NA, "end_2": NA, "leg_length": A("NOT_PRINTED", value="lap length: T-366 (HELD_NO_AUTHORITY)"),
               "hook": NA, "bend_diameter": NA, "crank": NA}},
    {"pop_id": "COL-LINKS", "element_class": "COLUMN",
     "description": "column and neck links 6 ø8/m (p.9 'ST. OF COLUMN- 6ø8/m'; route G TIES; LINKS; joint links)",
     "attrs": link(P9COL, "COLUMN", gap_hook="G-T371-3")},
    {"pop_id": "COL-TWIST-EXTRA", "element_class": "TWISTED_COLUMN",
     "description": "twisted column extra 4 ø16 (p.15)",
     "attrs": straight("p.15 TYP. DETAIL OF TWISTED COLUMN x 2: '4ø16 EXTRA', straight, '1M' + '1M' dimensions",
                       "TWISTED_COLUMN", True)},
    {"pop_id": "COL-TWIST-SPIRAL", "element_class": "TWISTED_COLUMN",
     "description": "twisted column spiral stirrups 6 ø8/m (p.15)",
     "attrs": {"body": A("PRINTED_TYPICAL", "p.15 TYP. DETAIL OF TWISTED COLUMN: 'Spiral Stirrups 6ø8/m', circle in plan",
                         applies_to="TWISTED_COLUMN", value="spiral (helix)"),
               "end_1": A("NOT_PRINTED", gap="G-T371-4", value="end turns / anchorage"),
               "end_2": A("NOT_PRINTED", gap="G-T371-4"),
               "leg_length": A("NOT_PRINTED", gap="G-T371-4", value="spiral diameter not dimensioned"),
               "hook": A("NOT_PRINTED", gap="G-T371-4"), "bend_diameter": BEND_GAP, "crank": NA},
     "count_label": ""},
    # ---------------- simple beams (p.10 schedule only) ----------------
    {"pop_id": "SB-BOTTOM", "element_class": "SIMPLE_BEAM",
     "description": "simple beams B1 - B29, CA, B.W bottom bars (+ route G BEAMS BOT, mark not on the id)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S21",
                         value="p.10 prints count / diameter only; no elevation of any simple beam"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S21"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "leg_length": A("NOT_PRINTED", rfi="RFI-B-S21"), "hook": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "bend_diameter": bend_if("RFI-B-S21"), "crank": NA},
     "note": "the released straight face-to-face net (T-149) is a length under option B, not a printed shape"},
    {"pop_id": "SB-BOTTOM-ENDS", "element_class": "SIMPLE_BEAM", "description": "simple-beam bottom bar ends (note-9 lines)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S21"), "end_1": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "end_2": A("NOT_PRINTED", rfi="RFI-B-S21"), "leg_length": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "hook": A("NOT_PRINTED", rfi="RFI-B-S21"), "bend_diameter": bend_if("RFI-B-S21"), "crank": NA}},
    {"pop_id": "SB-TOP", "element_class": "SIMPLE_BEAM",
     "description": "simple beams top bars (+ route G BEAMS TOP)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S21"), "end_1": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "end_2": A("NOT_PRINTED", rfi="RFI-B-S21"), "leg_length": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "hook": A("NOT_PRINTED", rfi="RFI-B-S21"), "bend_diameter": bend_if("RFI-B-S21"), "crank": NA}},
    {"pop_id": "SB-TOP-ENDS", "element_class": "SIMPLE_BEAM", "description": "simple-beam top bar ends (note-9 lines)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S21"), "end_1": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "end_2": A("NOT_PRINTED", rfi="RFI-B-S21"), "leg_length": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "hook": A("NOT_PRINTED", rfi="RFI-B-S21"), "bend_diameter": bend_if("RFI-B-S21"), "crank": NA}},
    {"pop_id": "BM-UNSCHEDULED", "element_class": "BEAM",
     "description": "projection bands and upstands with no bar print ('all bars' lines)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-S18", value="no schedule row / section with bars"),
               "end_1": A("NOT_PRINTED", rfi="RFI-S18"), "end_2": A("NOT_PRINTED", rfi="RFI-S18"),
               "leg_length": A("NOT_PRINTED", rfi="RFI-S18"), "hook": A("NOT_PRINTED", rfi="RFI-S18"),
               "bend_diameter": bend_if("RFI-S18"), "crank": A("NOT_PRINTED", gap="G-T371-5", value="upstands B20 / B23: no RFI")}},
    {"pop_id": "BEAM-LINKS", "element_class": "BEAM",
     "description": "beam links (simple + continuous; route G STI / CB_STIRRUP; Q-71 count)",
     "attrs": link(P15SL + ": beam section, closed link with corner tick ('BEAM SIZE & REINF. SEE SHEDULE')", "BEAM",
                   rfi_hook="RFI-B-S21", nested=("p.10 REMARKS nested-link symbol B17, B19 - B26", "RFI-B-S20"))},
    {"pop_id": "BEAM-SIDE-BARS", "element_class": "BEAM",
     "description": "beam side bars 2ø12/30cm, 2ø14/20cm, 2ø16/20cm (p.10 REMARKS, p.11 / p.12 MIDDLE REINT.)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S19", value="remark text only; no beam section draws them"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S21"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S21"),
               "leg_length": NA, "hook": A("NOT_PRINTED", rfi="RFI-B-S21"), "bend_diameter": bend_if("RFI-B-S21"), "crank": NA},
     "count_label": "", "note": "'2ø12/30cm' is COUNT_PER_SPACING: never a count (RFI-B-S19)"},
    {"pop_id": "PLANTED-COL-EXTRA", "element_class": "PLANTED_COLUMN_BEAM",
     "description": "beam carrying a planted column: 4 ø16 (p.15)",
     "attrs": {"body": A("PRINTED_TYPICAL", "p.15 BEAM CARRYING PLANTED COL. DETAIL: '4ø16'", applies_to="PLANTED_COLUMN_BEAM",
                         value="horizontal bars in the beam, extent 'DEPTH' beyond the column face each side"),
               "end_1": A("DRAWN_UNDIMENSIONED", "p.15 planted-column detail", rfi="RFI-B-S22", value="hooked ends drawn"),
               "end_2": A("DRAWN_UNDIMENSIONED", "p.15 planted-column detail", rfi="RFI-B-S22"),
               "leg_length": A("DRAWN_UNDIMENSIONED", "p.15 planted-column detail", rfi="RFI-B-S22"),
               "hook": A("DRAWN_UNDIMENSIONED", "p.15 planted-column detail", rfi="RFI-B-S22"),
               "bend_diameter": BEND_GAP, "crank": NA},
     "note": "the column's own bars are drawn cranked with a '100' dimension (RFI-B-S12, no candidate line here)"},
    # ---------------- continuous beams (p.11 / p.12) ----------------
    {"pop_id": "CB-BOTTOM", "element_class": "CONTINUOUS_BEAM",
     "description": "continuous-beam bottom bars (+ route G CB_BOTTOM)",
     "attrs": straight(P1112 + ": bottom bars drawn straight, no leg at the end supports; overlap at the interior "
                       "support drawn ('0.15L', '7.5cm')", "CONTINUOUS_BEAM", False),
     "note": "overlap length at the interior support: T-366 F-T366-3 (a length, not a shape)"},
    {"pop_id": "CB-TOP-CORNER", "element_class": "CONTINUOUS_BEAM",
     "description": "continuous-beam top corner / through bars (+ route G CB_TOP_THROUGH)",
     "attrs": {"body": A("PRINTED", P1112 + ": every row draws the top corner bars with a DOWN leg at each end support",
                         value="L (one end) / U (two-end through bar, e.g. CB8 span 1 5 ø18)"),
               "end_1": A("DRAWN_UNDIMENSIONED", P1112, rfi="RFI-B-S21", value="down leg at the end support"),
               "end_2": A("PRINTED", P1112 + " typical: interior end straight at '0.22 Ln'", value="straight, 0.22 Ln"),
               "leg_length": A("DRAWN_UNDIMENSIONED", P1112, rfi="RFI-B-S21"),
               "hook": NA, "bend_diameter": BEND_GAP, "crank": NA}},
    {"pop_id": "CB-TOP-ENDS", "element_class": "CONTINUOUS_BEAM",
     "description": "continuous-beam top corner / support bar ends on note 9 (40d..70d lines)",
     "attrs": {"body": A("PRINTED", P1112, value="the drawn bar ends at the down leg; no further extension drawn"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S21", value="any anchorage beyond the drawn leg"),
               "end_2": NA, "leg_length": A("NOT_PRINTED", rfi="RFI-B-S21"), "hook": NA, "bend_diameter": bend_if("RFI-B-S21"),
               "crank": NA}},
    {"pop_id": "CB-SUPPORT-TOP", "element_class": "CONTINUOUS_BEAM",
     "description": "continuous-beam support top bars (0.22 Ln / 0.3 Ln2; route G CB_SUPPORT_TOP)",
     "attrs": straight(P1112 + ": support bars drawn straight, extents '0.22 Ln' / '0.22 Ln1' / '0.3 Ln2' printed",
                       "CONTINUOUS_BEAM", False)},
    {"pop_id": "CB-BOTTOM-ENDS", "element_class": "CONTINUOUS_BEAM",
     "description": "continuous-beam bottom bar ends on note 9 (40d..70d lines)",
     "attrs": {"body": A("PRINTED", P1112, value="bottom bar ends drawn straight at the end support"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S21", value="any anchorage beyond the drawn straight end"),
               "end_2": NA, "leg_length": NA, "hook": NA, "bend_diameter": NA, "crank": NA}},
    # ---------------- ground beams and straps ----------------
    {"pop_id": "GB-MAIN", "element_class": "GROUND_BEAM",
     "description": "ground-beam / strap main bars, body (TOP, BOTTOM, rows 1 / 2, LONGITUDINAL, bars over the footings)",
     "attrs": straight(P13FT + ": upper / lower G.B bars drawn as continuous straight lines through the column; "
                       + P13GB + ": bars as dots", "GROUND_BEAM", True)},
    {"pop_id": "GB-BAR-ENDS", "element_class": "GROUND_BEAM",
     "description": "ground-beam bar ends (note-9 lines)",
     "attrs": {"body": A("PRINTED_TYPICAL", P13FT, applies_to="GROUND_BEAM", value="straight; ends shown broken"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S09", value="end at an end column: no elevation"),
               "end_2": A("NOT_PRINTED", rfi="RFI-B-S09"), "leg_length": A("NOT_PRINTED", rfi="RFI-B-S09"),
               "hook": A("NOT_PRINTED", rfi="RFI-B-S09"), "bend_diameter": bend_if("RFI-B-S09"), "crank": NA}},
    {"pop_id": "GB-STIRRUPS", "element_class": "GROUND_BEAM",
     "description": "ground-beam stirrups ø8/15cm and strap links (SB1 - SB3 rows, p.10)",
     "attrs": link(P13GB + ": closed link, corner tick", "GROUND_BEAM", gap_hook="G-T371-3",
                   nested=("p.10 SB1 / SB3 two-link, SB2 three-link symbol", "RFI-B-S20"))},
    {"pop_id": "GB-SIDE", "element_class": "GROUND_BEAM",
     "description": "exterior-wall ground beam side bars 2ø12/30cm (p.13)",
     "attrs": {"body": A("PRINTED_TYPICAL", P13GB + " (exterior walls): side bars as dots", applies_to="GROUND_BEAM",
                         value="straight"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S09"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S09"),
               "leg_length": NA, "hook": NA, "bend_diameter": NA,
               "crank": A("DRAWN_UNDIMENSIONED", P13GB + " (exterior walls): an unlabelled X between the four side bars",
                          gap="G-T371-6", value="X drawn, no label: bar, tie or symbol not printed")}},
    {"pop_id": "GB-BOTTOM-TIES", "element_class": "GROUND_BEAM", "no_line_reason":
     "drawn, unlabelled: no candidate line; never added before G-T371-6 is answered",
     "description": "unlabelled verticals from the second bottom layer down to the bottom bars (all four p.13 G.B sections)",
     "attrs": {"body": A("DRAWN_UNDIMENSIONED", P13GB, gap="G-T371-6", value="short verticals, no label"),
               "end_1": A("NOT_PRINTED", gap="G-T371-6"), "end_2": A("NOT_PRINTED", gap="G-T371-6"),
               "leg_length": A("NOT_PRINTED", gap="G-T371-6"), "hook": A("NOT_PRINTED", gap="G-T371-6"),
               "bend_diameter": BEND_GAP, "crank": NA}},
    {"pop_id": "GB-LAPS", "element_class": "GROUND_BEAM", "owned_by": "T-366",
     "description": "ground-beam procurement laps (laps only)",
     "attrs": {"body": A("PRINTED_TYPICAL", P13FT, applies_to="GROUND_BEAM", value="straight overlap"),
               "end_1": NA, "end_2": NA, "leg_length": A("NOT_PRINTED", value="lap length: T-366 HELD_NO_AUTHORITY"),
               "hook": NA, "bend_diameter": NA, "crank": NA}},
    # ---------------- slabs ----------------
    {"pop_id": "SLAB-BOTTOM", "element_class": "SLAB_ON_BEAMS",
     "description": "suspended-slab bottom mesh (+ route G SLABS MESH)",
     "attrs": {"body": A("PRINTED_TYPICAL", P15SL + ": straight; 'STOP 50% OF BOT. REINF. BALANCE CONTINUOUS' at "
                         "'.125 L'", applies_to="SLAB_ON_BEAMS", value="straight"),
               "end_1": A("PRINTED_TYPICAL", P15SL, applies_to="SLAB_ON_BEAMS", value="continuous support: straight"),
               "end_2": A("DRAWN_UNDIMENSIONED", P15SL + ": non-continuous support, bar turned UP, '40 CL.' from the outer face",
                          gap="G-T371-7", value="up-turn leg"),
               "leg_length": A("DRAWN_UNDIMENSIONED", P15SL, gap="G-T371-7"), "hook": NA, "bend_diameter": BEND_GAP,
               "crank": NA},
     "leg_bound_basis": "up-turn leg drawn inside the slab, from the bottom layer to the top layer: bounded above by D - "
                        "bottom cover ('25 CL' printed in the same detail) - top cover (p.8 note 22, >= 2.5 cm: a "
                        "minimum, so the bound is an upper bound only); D = panel thickness from the plan"},
    {"pop_id": "SLAB-DEVELOPMENT", "element_class": "SLAB_ON_BEAMS",
     "description": "slab bar-end development lines (T-318 re-booked: straight part valued, legs HELD)",
     "attrs": {"body": A("PRINTED_TYPICAL", P15SL, applies_to="SLAB_ON_BEAMS", value="straight to 40 mm of the outer face"),
               "end_1": A("PRINTED_TYPICAL", P15SL, applies_to="SLAB_ON_BEAMS", value="continuous: no development drawn"),
               "end_2": A("DRAWN_UNDIMENSIONED", P15SL, gap="G-T371-7", value="edge beam: up-turn leg"),
               "leg_length": A("DRAWN_UNDIMENSIONED", P15SL, gap="G-T371-7"), "hook": NA, "bend_diameter": BEND_GAP,
               "crank": NA}},
    {"pop_id": "SLAB-TOP", "element_class": "SLAB_ON_BEAMS",
     "description": "slab top bars over supports ('TOP ANCHOR BARS')",
     "attrs": {"body": A("PRINTED_TYPICAL", P15SL + ": '.25 L1' at the edge, '.30 L1 OR .30 L2 WHICHEVER LARGER' over "
                         "continuous supports", applies_to="SLAB_ON_BEAMS", value="straight"),
               "end_1": A("PRINTED_TYPICAL", P15SL, applies_to="SLAB_ON_BEAMS", value="inner end straight"),
               "end_2": A("DRAWN_UNDIMENSIONED", P15SL + ": hook-down leg at the outer face", gap="G-T371-7",
                          value="leg drawn passing BELOW the slab soffit into the edge beam (F-T371-1)"),
               "leg_length": A("DRAWN_UNDIMENSIONED", P15SL, gap="G-T371-7"), "hook": NA, "bend_diameter": BEND_GAP,
               "crank": NA},
     "leg_bound_basis": "F-T371-1: the hook-down leg is drawn past the slab soffit into the edge beam, so 'D less "
                        "note-22 covers' (F-T318-1) does NOT bound it; the drawn bound is the EDGE BEAM depth (p.10 / "
                        "p.11 schedule D of the supporting beam) less its bottom cover and less the beam's own bar "
                        "layers: still undimensioned, HELD"},
    {"pop_id": "SLAB-UNPRINTED-PANELS", "element_class": "SLAB_ON_BEAMS",
     "description": "13 slab panels whose plan prints no bars ('ALL BARS' lines)",
     "attrs": {"body": A("NOT_PRINTED", rfi="RFI-B-S10", value="no bar label on the panel"),
               "end_1": A("NOT_PRINTED", rfi="RFI-B-S10"), "end_2": A("NOT_PRINTED", rfi="RFI-B-S10"),
               "leg_length": A("NOT_PRINTED", rfi="RFI-B-S10"), "hook": A("NOT_PRINTED", rfi="RFI-B-S10"),
               "bend_diameter": bend_if("RFI-B-S10"), "crank": NA}},
    {"pop_id": "SLAB-TEMP", "element_class": "SLAB_ON_BEAMS",
     "description": "slab temperature bars (p.15 TEMPERATURE REINFORCEMENT SCHEDULE)",
     "attrs": straight(P15SL + ": 'TEMP. REINFORCING' drawn as a bar in section; schedule Y10 / Y12 @ 200; NOTE 1 lap",
                       "SLAB_ON_BEAMS", True)},
    {"pop_id": "SLAB-EXTRA", "element_class": "SLAB_ON_BEAMS",
     "description": "slab corner bars / second-bar zone (plan labels, T-152)",
     "attrs": {"body": A("NOT_PRINTED", gap="G-T371-7", value="plan legend 'Corner Reinforcement' / 'Extra Reinforcement' "
                         "hatches (p.3 legend): zone symbols, no bar shape"),
               "end_1": A("NOT_PRINTED", gap="G-T371-7"), "end_2": A("NOT_PRINTED", gap="G-T371-7"),
               "leg_length": A("NOT_PRINTED", gap="G-T371-7"), "hook": A("NOT_PRINTED", gap="G-T371-7"),
               "bend_diameter": BEND_GAP, "crank": NA}},
    {"pop_id": "GROUND-SLAB-MESH", "element_class": "GROUND_SLAB",
     "description": "ground slab on grade mesh (route G GROUND_SLAB MESH D10)",
     "attrs": {"body": A("PRINTED", "p.3 GROUND BEAMS PLAN: '5ø10/m E.W. T=10cm' + 'Normal Slab Reinforcement' "
                         "symbol (x 2)", value="straight mesh, each way"),
               "end_1": A("NOT_PRINTED", gap="G-T371-7", value="edge at ground beams: no detail"),
               "end_2": A("NOT_PRINTED", gap="G-T371-7"), "leg_length": NA, "hook": NA, "bend_diameter": NA,
               "crank": NA},
     "count_label": "", "note": "'5ø10/m' is a RATE (bars per metre), never a count"},
]

GAPS = {
    "G-T371-0": "bend diameter / standard hook extension: printed for no population (p.8 notes 1 - 24; no BBS legend); a "
                "cutting length of any bent bar (leg, hook, crank, link) needs it",
    "G-T371-1": "footing BOXED bars: diameter, leg end level, the marks at the upper corners (T-171 / T-299 designer item; "
                "in no RFI of rfi/A or rfi/B)",
    "G-T371-2": "starter foot: exact length ('Min. 30cm' printed), foot-end up-bend and the deep detail's crank offset",
    "G-T371-3": "column / neck / ground-beam link hook (angle, extension) and column head / section-change bar shapes: "
                "RFI-B-S21 asks beam links only, RFI-B-S09 ground-beam bar ends only",
    "G-T371-4": "twisted-column spiral: diameter and end turns",
    "G-T371-5": "upstands on B20 / B23: no bar print (RFI-S18 covers projection bands only)",
    "G-T371-6": "unlabelled G.B section marks: the X between exterior-G.B side bars and the second-layer verticals",
    "G-T371-7": "slab bar-end legs (bottom up-turn, top hook-down), corner / extra bar shapes, ground-slab edges: RFI-B-S10 "
                "asks the top-bar extent only; held under owner option B meanwhile",
}

FINDINGS = [
    "F-T371-1: p.15 TYP. SLAB ON BEAMS DETAIL draws the top anchor bar's hook-down leg passing below the slab soffit "
    "into the edge beam: the Checker's F-T318-1 bound 'D less note-22 covers' holds for the bottom up-turn leg only.",
    "F-T371-2: p.13 G.B sections draw unlabelled marks (X between exterior side bars; verticals from the second bottom "
    "layer): neither is in the candidate; never added before G-T371-6 is answered.",
    "F-T371-3: no bend diameter / hook extension is printed for any population (G-T371-0): no bent BBS shape is "
    "schedulable now, even where every leg is drawn.",
    "F-T371-4: the footing BOXED-bar request (T-171 / T-299 'designer item') reached neither rfi/A nor rfi/B.",
]


def _binding_target(line: dict) -> str:
    e = line["element_id"]
    i = line.get("inputs") or {}
    comp = str(i.get("component"))
    mark = str(i.get("mark"))
    if e.startswith("HL:STAIR_POOL_TANK_STEEL"):
        return "T-359"
    if e.startswith("FRP:FTG"):
        return {"BOTTOM_LONG": "FTG-BOT-MESH", "BOTTOM_SHORT": "FTG-BOT-MESH", "ALL": "FTG-BOT-MESH",
                "TOP_LONG": "FTG-TOP-MESH", "TOP_SHORT": "FTG-TOP-MESH", "TOP_END_LEGS": "FTG-TOP-END-LEGS",
                "BOXED": "FTG-BOXED"}[comp]
    if e.startswith(("P-S:", "U-S:")):
        p = e.split(":")
        fam, tail = p[1], (p[-2] if p[-1].startswith("D") and p[-1][1:].isdigit() else p[-1])
        if fam == "NECK":
            return {"MAIN": "STARTER", "TIES": "COL-LINKS"}[tail]
        if fam == "COL":
            return {"MAIN": "COL-MAIN-BODY", "TIES": "COL-LINKS"}[tail]
        if fam in ("SLABS",):
            return "SLAB-BOTTOM"
        if fam == "GROUND_SLAB":
            return "GROUND-SLAB-MESH"
        if fam == "GROUND_BEAMS":
            return {"BOT": "GB-MAIN", "TOP": "GB-MAIN", "STI": "GB-STIRRUPS"}[tail]
        if fam == "BEAMS":
            if tail.startswith("CB_SUPPORT_TOP"):
                return "CB-SUPPORT-TOP"
            return {"BOT": "SB-BOTTOM", "TOP": "SB-TOP", "STI": "BEAM-LINKS", "CB_BOTTOM": "CB-BOTTOM",
                    "CB_STIRRUP": "BEAM-LINKS", "CB_TOP_THROUGH": "CB-TOP-CORNER"}[tail]
    if e.startswith("HL:COLUMN_STEEL"):
        if comp.startswith("LINKS"):
            return "COL-LINKS"
        if comp.startswith("TURN EXTRA"):
            return "COL-TWIST-EXTRA"
        if comp.startswith("TURN SPIRAL"):
            return "COL-TWIST-SPIRAL"
        return {"MAIN BARS net": "COL-MAIN-BODY", "BAR ENDS stopping at this roof": "COL-TOP-END",
                "LAP at storey bottom (reading P)": "COL-STOREY-LAP",
                "SECTION TRANSITION at bottom": "COL-SECTION-TRANSITION"}[comp]
    if e.startswith("HL:GROUND_SYSTEM_STEEL"):
        if comp.startswith("STIRRUP"):
            return "GB-STIRRUPS"
        if comp.startswith("BAR ENDS"):
            return "GB-BAR-ENDS"
        if comp.startswith("SIDE"):
            return "GB-SIDE"
        if comp.startswith("PROCUREMENT"):
            return "GB-LAPS"
        return "GB-MAIN"
    if e.startswith("HL:SLAB_STEEL"):
        return {"BOTTOM MESH": "SLAB-BOTTOM", "ALL BARS": "SLAB-UNPRINTED-PANELS", "DEVELOPMENT / ANCHORAGE": "SLAB-DEVELOPMENT",
                "TOP BARS OVER SUPPORTS": "SLAB-TOP", "TEMPERATURE BARS": "SLAB-TEMP"}.get(comp, "SLAB-EXTRA")
    if e.startswith("HL:BEAM_STEEL"):
        cb = mark.startswith("CB")
        if comp == "all bars":
            return "BM-UNSCHEDULED"
        if comp.startswith("links"):
            return "BEAM-LINKS"
        if comp.startswith("side bars"):
            return "BEAM-SIDE-BARS"
        if comp.startswith("planted-column"):
            return "PLANTED-COL-EXTRA"
        if comp.startswith("END-SUPPORT TOP BARS") or comp.startswith("top over support"):
            return "CB-TOP-ENDS" if "note 9" in comp else "CB-SUPPORT-TOP"
        if comp.startswith("top corner"):
            return "CB-TOP-ENDS" if "note 9" in comp else "CB-TOP-CORNER"
        if comp.startswith("bottom"):
            if "note 9" in comp:
                return "CB-BOTTOM-ENDS" if cb else "SB-BOTTOM-ENDS"
            return "CB-BOTTOM" if cb else "SB-BOTTOM"
        if comp.startswith("top"):
            if "note 9" in comp:
                return "CB-TOP-ENDS" if cb else "SB-TOP-ENDS"
            return "SB-TOP"
    raise ValueError(f"unbound candidate line {line['line_id']} {e} {comp}")


def build() -> tuple[dict, dict]:
    raw = EXTRACT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXTRACT_SHA:
        raise SystemExit("T-297 extract changed: re-read the binding before use")
    ext = json.loads(raw)
    lines = {l["line_id"]: _binding_target(l) for l in ext["lines"]}
    data = {"policy": "BAR_SHAPE_SOURCE_CENSUS_V1", "villa": "development villa (Drive 'Alsenan chalet project')",
            "sources": {"ST7757.pdf": "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"},
            "register": {"rfi_register": RFI_REGISTER, "answered_rules": ANSWERED_RULES, "other_census": OTHER_CENSUS},
            "populations": POPS, "gaps": GAPS, "findings": FINDINGS}
    binding = {"candidate": ext["candidate"], "extract": "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json",
               "extract_sha256": EXTRACT_SHA, "candidate_line_ids": sorted(lines), "lines": dict(sorted(lines.items()))}
    return data, binding


def main(argv) -> int:
    data, binding = build()
    if "--check" in argv:
        same = (json.loads(OUT_INPUT.read_text("utf-8")) == json.loads(json.dumps(data))
                and json.loads(OUT_BINDING.read_text("utf-8")) == binding)
        print("committed input matches the builder" if same else "STALE: rebuild")
        return 0 if same else 1
    OUT_INPUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", "utf-8")
    OUT_BINDING.write_text(json.dumps(binding, indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(f"{len(POPS)} populations, {len(binding['lines'])} lines bound")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
