"""T-376 DESIGNER_RFI_ROWS_V1 (research code; read-only on every ledger, candidate extract and engine module).

Proposed designer RFI rows for the rebar shape and lap gaps that T-366 (lap authority census, MERGED 51be6eab) and
T-371 (bar-shape source census, MERGED) left open. One row per designer FACT: the question, the sheets / details
where the search ended (each citation resolved against the merged T-366 / T-371 ledgers: a row with no resolvable
citation is refused), the existing RFI it extends or a proposed new id, the bar populations and candidate line ids it
unlocks on ARCH_TAKEOFF_V3.0.27 and the kg range it governs. HELD is BLANK, never 0. Nothing here computes a new
length, a new bar count or a new kg: every figure is read from a merged ledger or the merged candidate extract.

The rows are TEXT for the Lead; the worker never edits docs/agents/rfi/*. Nothing is sent to any designer (owner
2026-10-29 22:05). No owner question: each item is a drawing gap or a conflict between two printed documents of the
same set, i.e. a designer fact (ERS s.2.7 not met for the owner).

V3.0.27 view without private data (same projection T-373 proved equal to the reproduced V3.0.27, test
t373 test_projection_from_committed_extract_equals_the_v3027_record): the merged T-297 extract of V3.0.16 (2,505
reinforcement lines; the line ids are stable across versions) + the merged T-318 slab bar-end inputs read through the
engine's own `arch_v3027.load_inputs` (read only): REBASE lines carry the part range on themselves, PARENT lines become
BLANK and gain one part line (element id `<parent>#SLAB_BAR_ENDS:VALUED`, the engine's `part_element_id`), RESTATE / NA
lines become BLANK. 2,505 + 138 parts = 2,643 lines = T-373's count of V3.0.27. The four DOWNGRADE-ONLY records of
DGP-T373-LAP (Verifier 2026-10-30 21:58, verdicts/V3.0.28/DOWNGRADES.json) are marked per line from the committed
T-373 binding (its 351 'HELD' ids): those lines are HELD / UNSUPPORTED BASIS in the contractual view of V3.0.28; their
range is audit only.

    python3 -I research/agents_t376/t376_rfi_rows.py --out research/agents_t376
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "DESIGNER_RFI_ROWS_V1"

EXTRACT = ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"
T371_INPUT = ROOT / "research/agents_t371/ALSENAN_BAR_SHAPE_INPUT.json"
T371_BIND = ROOT / "research/agents_t371/LINE_BINDING_T371.json"
T366_INPUT = ROOT / "research/agents_t366/ALSENAN_LAP_AUTHORITY_INPUT.json"
T373_CSV = ROOT / "research/agents_t373/T373_LAP_BINDING.csv"
T273_MD = ROOT / "research/agents_t273/T-273_LAPS_AND_TONNES.md"
EXTRACT_SHA = "2f28367b81fe362d98d8a97080adb62cfd9a3c0a880fc20d201735e6eba39760"

# DGP-T373-LAP records (Verifier 2026-10-30 21:58 UTC, board T-373 row): report group of the T-373 binding -> record id
DGP = {"beam ends": "DG-30f59008802b7c52", "column storey laps": "DG-8afa33d54d4dfe7e",
       "GB bar ends": "DG-a941799811602f7c", "GB procurement laps": "DG-aaabf79afb37aa08"}

# existing questions (rfi/A_PRIORITY_RFI.md, rfi/B_REMAINING_RFI.md, as registered in the merged T-371 input)
NEXT_FREE_NOTE = ("new ids proposed as the next free B structural numbers after RFI-B-S22 that do not collide with "
                  "A's RFI-S01 .. S28 (S29 onward); the Lead confirms the final id when applying the row")


Q6 = Decimal("0.000001")


class RowError(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def D(x):
    return Decimal(str(x))


# ------------------------------------------------------------------------------------------- the proposed rows
# cite forms (resolved by resolve_cite against the merged ledgers):
#   {"t371": pop_id, "attr": a, "state": S?, "quote": q?}   T-371 input: population attribute (state / ref / value)
#   {"t371_gap": G}                                          T-371 input: gap register
#   {"t366": pop_id, "field": f, "quote": q?}                T-366 input: population field (finding / need_basis ...)
#   {"t366_checked": key, "handle": h?}                      T-366 input: sheet searched (+ DXF handle in it)
#   {"t366_source": key, "quote": q?}                        T-366 input: printed lap source
#   {"doc": relpath, "quote": q}                             another merged ledger, quoted (kg figures only)
# kg: {"kind": "LINES"} = the unlocked lines' own figures; {"kind": "LEDGER", "low", "high", "cite"} = a merged
#     ledger range the answer settles (not in the candidate); {"kind": "UNQUANTIFIED", "why"} = HELD, no bound exists.
ROWS = [
    dict(row="R01", gap="G-T371-0", fact="BEND_DIAMETER_HOOK_EXTENSION_ALL_MARKS", target="RFI-B-S21", sub="(d)",
         relation="EXTENDS",
         question="Which bend (mandrel) diameter and which hook / bend extension apply to the bent bar marks (links, "
                  "legs, cranks, spirals, starter feet), or which standard and edition governs them?",
         requested="the bend diameter and the hook / bend extension per bar diameter, or the governing standard",
         missing="no bend diameter, hook extension or bar-bending legend is printed on any sheet",
         cites=[{"t371_gap": "G-T371-0"}, {"t371": "BEAM-LINKS", "attr": "bend_diameter", "state": "NOT_PRINTED"},
                {"t371": "COL-LINKS", "attr": "bend_diameter", "state": "NOT_PRINTED"},
                {"t366_checked": "P8"}, {"t366_checked": "DXF", "handle": "1BA9"}],
         pops="BEND_NOT_PRINTED", kg={"kind": "UNQUANTIFIED",
                                     "why": "a bend changes the cutting length of a bar schedule, not the installed "
                                            "net kg; hook tails are drawn without length: no merged ledger bounds them"},
         dup="S21 asks the link hook TYPE and LENGTH of beam links only; this asks the bend diameter / extension of "
             "every bent mark: one new fact, added to S21 so one reply covers both"),
    dict(row="R02", gap="G-T371-3", fact="LINK_CLOSURE_ALL_LINK_CLASSES", target="RFI-B-S21", sub="(e)",
         relation="EXTENDS (absorbs S21's beam-link hook item)",
         question="How is each link closed (hook angle and extension, or overlap) for column links including the "
                  "necks and the beam-column joints, ground-beam stirrups and strap links, as already asked for the "
                  "beam links?",
         requested="the closure detail per link class (beam, column / neck / joint, ground beam, strap)",
         missing="every link section draws a closed link with an undimensioned corner tick",
         cites=[{"t371_gap": "G-T371-3"},
                {"t371": "COL-LINKS", "attr": "hook", "state": "DRAWN_UNDIMENSIONED", "quote": "DETAILS OF COLUMN"},
                {"t371": "GB-STIRRUPS", "attr": "hook", "state": "DRAWN_UNDIMENSIONED", "quote": "corner tick"},
                {"t371": "BEAM-LINKS", "attr": "hook", "state": "DRAWN_UNDIMENSIONED", "quote": "corner tick"},
                {"t366_checked": "P9", "handle": "1BAA"}],
         pops=["COL-LINKS", "GB-STIRRUPS", "BEAM-LINKS"],
         kg={"kind": "UNQUANTIFIED", "why": "the bounded link lines book the closed perimeter only ('hooks not "
                                            "printed'); the hook tails carry no figure in any merged ledger"},
         dup="S21 (c) 'link hook type and length' (beam links): the same fact for beams, so S21's item is WIDENED "
             "to every link class, never asked twice; S20 (nested inner links) and A RFI-S11 (< 2.5 m link size / "
             "spacing) are different facts and stay"),
    dict(row="R03", gap="G-T371-3", fact="COLUMN_TOP_END_AND_SECTION_CHANGE", target="NEW", new_id="RFI-B-S29",
         sub="", relation="NEW",
         question="At the top of each column (roof) and where a column section reduces between storeys, how do the "
                  "main bars end or continue: bent into the slab / beam (with what leg), cranked into the smaller "
                  "section (with what offset), or stopped with new bars lapped?",
         requested="the column-head bar detail and the bar detail at a section change (or the typical detail that "
                   "governs both)",
         missing="the p.9 schedule prints the size and bars per storey but no column-head or section-change detail",
         cites=[{"t371": "COL-TOP-END", "attr": "end_1", "state": "NOT_PRINTED"},
                {"t371": "COL-TOP-END", "attr": "body", "quote": "p.9 schedule"},
                {"t371": "COL-SECTION-TRANSITION", "attr": "crank", "state": "NOT_PRINTED"},
                {"t366_checked": "P9", "handle": "1B3A"}, {"t366_checked": "P15"}],
         pops=["COL-TOP-END", "COL-SECTION-TRANSITION"],
         kg={"kind": "UNQUANTIFIED", "why": "no head leg or crank is drawn, so no merged ledger gives a bound"},
         dup="no A or B question asks a column bar end or a section change (A RFI-S19 / S20 / S21 ask column "
             "concrete sections, RFI-B-S12 the planted columns only)"),
    dict(row="R04", gap="G-T371-1", fact="FOOTING_BOXED_BARS", target="NEW", new_id="RFI-B-S30", sub="",
         relation="NEW (carries F-T371-4: the T-171 / T-299 designer item that never reached rfi/)",
         question="For the footing 'Boxed bars' (p.9 BOXED column, p.13 typical footing details): what is the bar "
                  "diameter, to which level do the legs run, and what are the marks drawn at the upper corners?",
         requested="diameter, leg end level and the corner marks of the boxed bars (or a dimensioned detail)",
         missing="p.13 draws the boxed bar as an inverted U with legs towards the mesh; no diameter, leg level or "
                 "corner detail is printed",
         cites=[{"t371_gap": "G-T371-1"}, {"t371": "FTG-BOXED", "attr": "body", "quote": "Boxed bars"},
                {"t371": "FTG-BOXED", "attr": "leg_length", "state": "DRAWN_UNDIMENSIONED"},
                {"t366": "FTG-BOXED", "field": "finding", "quote": "open U"}, {"t366_checked": "P13"}],
         pops=["FTG-BOXED"],
         kg={"kind": "UNQUANTIFIED", "why": "diameter and leg level not printed: all 20 lines BLOCKED, no bound"},
         dup="RFI-B-S09 asks the top-bar ENDS of F8 / F12 / F13 / F14 / FF (the cage end legs), not the boxed bars: "
             "different bars; no A question touches footing reinforcement"),
    dict(row="R05", gap="G-T371-2", fact="STARTER_FOOT_AND_CRANK", target="NEW", new_id="RFI-B-S31", sub="(a) (b)",
         relation="NEW",
         question="(a) What is the length of the starter-bar foot on the footing mesh (p.13 prints 'Min. 30cm', a "
                  "minimum) and is its end bent up; (b) what are the crank dimensions of the starters and column "
                  "bars drawn in the deeper footing detail (lower G.B more than 2.5 m below)?",
         requested="the foot length (or confirmation that 30 cm is the length), the foot-end bend, the crank offsets",
         missing="foot printed as a minimum only; the up-bend and the deep-detail cranks drawn without dimension",
         cites=[{"t371_gap": "G-T371-2"}, {"t371": "STARTER", "attr": "leg_length", "state": "PRINTED_MINIMUM",
                                          "quote": "Min. 30cm"},
                {"t371": "STARTER", "attr": "crank", "state": "DRAWN_UNDIMENSIONED"},
                {"t366": "NECK-STARTER-DEEP", "field": "finding", "quote": "cranks"}, {"t366_checked": "P13"}],
         pops=["STARTER"],
         kg={"kind": "UNQUANTIFIED", "why": "the printed 30 cm is a minimum (a lower bound of the foot only); no "
                                            "merged ledger bounds the foot from above or values the cranks"},
         dup="A RFI-S01 asks the founding level, which fixes the starter's vertical length, not its foot or "
             "crank: different fact, kept as a joint dependency"),
    dict(row="R06", gap="F-T366-1", fact="STARTER_PROJECTION_40D_VS_NOTE9", target="NEW", new_id="RFI-B-S31",
         sub="(c)", relation="NEW (same RFI as R05, its own question)",
         question="(c) The starter projection above the footing top is dimensioned '40 ø' on the p.13 typical "
                  "footing detail (upper G.B less than 2.5 m above), while p.8 note 9 requires the starter-bar "
                  "development to be not less than 70 x dia in tension zones and 40 x dia in compression zones: "
                  "which governs, and which of the two p.13 details applies to each footing?",
         requested="the governing starter projection per footing (or the zone of each starter splice)",
         missing="two printed documents of the same set disagree in a tension zone; the zone is not printed",
         cites=[{"t366_source": "P13D40", "quote": "40"}, {"t366_source": "N9", "quote": "70"},
                {"t366": "NECK-STARTER-SHALLOW", "field": "finding", "quote": "F-T366-1"},
                {"t371": "STARTER", "attr": "end_2", "quote": "40 ø"}, {"t366_checked": "P8"}],
         pops=["STARTER"],
         kg={"kind": "LEDGER", "low": "278.836", "high": "487.963",
             "basis": "column ledger starter projection 278.836 kg on 31 chains at 40 D (T-273 r2 s.9.2, MERGED); "
                      "+209.127 kg at 70 D (its own scenario figure) = 487.963 kg; a scenario range, NOT in the "
                      "candidate (the 28 starter lines are BLOCKED, BLANK)",
             "cite": [{"doc": "research/agents_t273/T-273_LAPS_AND_TONNES.md", "quote": "278.836 kg on 31 chains"},
                      {"doc": "research/agents_t273/T-273_LAPS_AND_TONNES.md", "quote": "+209.127 kg at 70 D"}]},
         dup="RFI-B-S09 / S21 cite note 9 for ground-beam and beam ends, never for the starters it names; no A or "
             "B question asks the starter projection"),
    dict(row="R07", gap="T-366 item (1) / F-T366-2", fact="LAP_LENGTH_SPLICE_ZONE_COLUMN_GB_SLAB", target="NEW",
         new_id="RFI-B-S32", sub="", relation="NEW",
         question="What lap length and which splice zones apply to (a) column main bars at the storey joints, (b) "
                  "ground-beam main bars where a run exceeds the bar stock, (c) the boundary-wall ground beam, and "
                  "(d) slab bottom / top bars and the ground-slab mesh where they are spliced? (No note or detail "
                  "prints a lap for these bars; p.8 note 9 is written for starter bars.)",
         requested="the lap length (in bar diameters or mm) and the permitted splice zone per member class",
         missing="no lap print for these populations; note 9 names starter bars only",
         cites=[{"t366": "COL-MAIN", "field": "finding", "quote": "F-T366-2"},
                {"t366": "GB-MAIN", "field": "need_basis", "quote": "18.570"},
                {"t366": "BW-GB", "field": "need_basis", "quote": "31.370"},
                {"t366": "GROUND-SLAB-MESH", "field": "finding", "quote": "lap not printed"},
                {"t366_source": "N9", "quote": "STARTER"}, {"t366_checked": "DXF", "handle": "1BA9"}],
         pops=["COL-STOREY-LAP", "GB-LAPS"], kg={"kind": "LINES"},
         dup="RFI-B-S21 asks whether note 9 governs BEAM laps; RFI-B-S12 the planted-column laps: other members, "
             "kept apart; stock length is not asked (owner-approved 12 m, OD-V3-3)"),
    dict(row="R08", gap="F-T366-3", fact="CB_BOTTOM_OVERLAP_INTERIOR_SUPPORT", target="RFI-B-S21", sub="(f)",
         relation="EXTENDS",
         question="On the continuous beams, what is the overlap length of the bottom bars of two adjacent spans "
                  "across an interior support (drawn overlapping on p.11 / p.12, not dimensioned)?",
         requested="the overlap / anchorage length of the bottom bars at interior supports",
         missing="the overlap is drawn on the typical span diagram and every CB row, with no length",
         cites=[{"t366": "CB-BOTTOM", "field": "finding", "quote": "F-T366-3"},
                {"t366_checked": "P1112", "handle": "206B"},
                {"t371": "CB-BOTTOM-ENDS", "attr": "end_1"}],
         pops=["CB-BOTTOM-ENDS"], kg={"kind": "LINES"},
         joint="RFI-B-S21 (a) end shape at end supports: the 29 lines carry both ends, not separable by line",
         dup="S21 asks end supports and the note-9 scope; the interior overlap is a separate drawn item"),
    dict(row="R09", gap="G-T371-4", fact="TWISTED_COLUMN_SPIRAL", target="NEW", new_id="RFI-B-S33", sub="",
         relation="NEW",
         question="For the spiral stirrups of the twisted columns (p.15 'Spiral Stirrups 6ø8/m'): what is the "
                  "spiral diameter (or cover to the spiral), and how many end turns / what anchorage at each end?",
         requested="spiral diameter and end turns / anchorage ('6ø8/m' is read as a rate: 6 turns per metre)",
         missing="the spiral is drawn as a circle in plan; diameter and end turns not printed",
         cites=[{"t371_gap": "G-T371-4"}, {"t371": "COL-TWIST-SPIRAL", "attr": "body", "quote": "Spiral"},
                {"t371": "COL-TWIST-SPIRAL", "attr": "end_1", "state": "NOT_PRINTED"}, {"t366_checked": "P15"}],
         pops=["COL-TWIST-SPIRAL"],
         kg={"kind": "UNQUANTIFIED", "why": "2 lines BLOCKED; no diameter, no bound"},
         dup="RFI-B-S22 covers the planted-column 4ø16 and the stair-beam crank on the same sheets; the spiral is "
             "a different bar"),
    dict(row="R10", gap="G-T371-5", fact="UNSCHEDULED_BANDS_UPSTAND_BARS", target="NEW", new_id="RFI-B-S34",
         sub="", relation="NEW (asked with A RFI-S18, which asks the concrete section)",
         question="What reinforcement do the roof-edge projection bands and the upstands on B20 / B23 carry, once "
                  "their section is given (RFI-S18)?",
         requested="bars (count, diameter, shape) of each projection band / upstand section",
         missing="no schedule row or section prints bars for these members",
         cites=[{"t371_gap": "G-T371-5"}, {"t371": "BM-UNSCHEDULED", "attr": "body", "state": "NOT_PRINTED"},
                {"t371": "BM-UNSCHEDULED", "attr": "crank", "quote": "B20 / B23"}, {"t366_checked": "P10",
                                                                                     "handle": "1E47"}],
         pops=["BM-UNSCHEDULED"],
         kg={"kind": "UNQUANTIFIED", "why": "12 'all bars' lines BLOCKED: no section, no bar print, no bound"},
         joint="A RFI-S18 (section, depth, material of each projection)",
         dup="RFI-S18 asks the concrete section only; the bars are a separate fact"),
    dict(row="R11", gap="G-T371-6", fact="GB_SECTION_UNLABELLED_MARKS", target="RFI-B-S09", sub="(e)",
         relation="EXTENDS (carries F-T371-2)",
         question="In the four p.13 ground-beam sections, what are (i) the unlabelled X drawn between the side bars "
                  "of the exterior-wall ground beam and (ii) the short verticals drawn from the second bottom layer "
                  "down to the bottom bars: bars or not, and if bars, their diameter and spacing?",
         requested="identification, diameter and spacing of both marks (or confirmation they are not bars)",
         missing="drawn without label or dimension",
         cites=[{"t371_gap": "G-T371-6"}, {"t371": "GB-SIDE", "attr": "crank", "quote": "unlabelled X"},
                {"t371": "GB-BOTTOM-TIES", "attr": "body", "state": "DRAWN_UNDIMENSIONED"}, {"t366_checked": "P13"}],
         pops=["GB-SIDE", "GB-BOTTOM-TIES"],
         kg={"kind": "UNQUANTIFIED", "why": "GB-SIDE 30 lines BLOCKED; the verticals have no line and are never "
                                            "added before the answer"},
         dup="S09 asks ground-beam bar ends; RFI-B-S19 the '2ø12/30cm' notation of beams: neither asks these marks"),
    dict(row="R12", gap="G-T371-7", fact="SLAB_BOTTOM_UPTURN_LEG", target="RFI-B-S10", sub="(e)",
         relation="EXTENDS",
         question="At a non-continuous slab support (edge beam), the p.15 TYP. SLAB ON BEAMS DETAIL turns the bottom "
                  "bars up at '40 CL.' from the outer face: what is the length of the up-turned leg (to the top "
                  "layer, or a stated length)?",
         requested="the up-turn leg length (or the level it reaches)",
         missing="the leg is drawn, not dimensioned",
         cites=[{"t371_gap": "G-T371-7"}, {"t371": "SLAB-BOTTOM", "attr": "end_2", "quote": "40 CL."},
                {"t371": "SLAB-DEVELOPMENT", "attr": "leg_length", "state": "DRAWN_UNDIMENSIONED"},
                {"t366_checked": "P15"}],
         pops=["SLAB-DEVELOPMENT"], held_item="UPTURN_LEG",
         kg={"kind": "UNQUANTIFIED", "why": "legs carry no figure (owner option B 2026-10-29); the only bound basis "
                                            "(D less covers, T-371 s.4) is a PROPOSAL, never valued"},
         dup="S10 asks the top-bar EXTENT and the bar-less panels; the bottom leg is a separate fact"),
    dict(row="R13", gap="F-T371-1", fact="SLAB_TOP_HOOKDOWN_LEG_INTO_EDGE_BEAM", target="RFI-B-S10", sub="(f)",
         relation="EXTENDS",
         question="At the outer face the top anchor bars are drawn hooking down past the slab soffit into the edge "
                  "beam: what is the leg length / the level it ends at in the beam?",
         requested="the hook-down leg length or its end level",
         missing="drawn into the edge beam, not dimensioned",
         cites=[{"t371": "SLAB-TOP", "attr": "end_2", "quote": "hook-down"},
                {"t371": "SLAB-TOP", "attr": "leg_length", "state": "DRAWN_UNDIMENSIONED"},
                {"t371_gap": "G-T371-7"}, {"t366_checked": "P15"}],
         pops=["SLAB-TOP"], held_item="HOOK_DOWN_LEG",
         kg={"kind": "UNQUANTIFIED", "why": "legs carry no figure; 'D less covers' is refused for this leg "
                                            "(F-T371-1: the leg enters the beam)"},
         dup="S10's top-bar EXTENT question ('.30 L1' vs note 2) is the horizontal length; this is the leg"),
    dict(row="R14", gap="G-T371-7", fact="SLAB_CORNER_EXTRA_BAR_SHAPE", target="RFI-B-S10", sub="(g)",
         relation="EXTENDS (S10's GF-126 zone-extent item stays as it is)",
         question="What are the shape, length and layer of the slab corner bars ('Corner Reinforcement', e.g. "
                  "1F-084 12 ø14) and of the bars in the second-bar zones ('Extra Reinforcement')?",
         requested="a detail or a stated length / layer for corner and extra bars",
         missing="plan legend hatches only",
         cites=[{"t371": "SLAB-EXTRA", "attr": "body", "state": "NOT_PRINTED", "quote": "Corner Reinforcement"},
                {"t366": "SLAB-EXTRA", "field": "group", "quote": "SLAB_EXTRA"}, {"t371_gap": "G-T371-7"}],
         pops=["SLAB-EXTRA"],
         kg={"kind": "UNQUANTIFIED", "why": "2 lines BLOCKED; no bar drawn on the plan, no bound"},
         dup="S10 asks where the GF-126 zone lies (extent); the bar shape / corner bars are a different fact"),
    dict(row="R15", gap="G-T371-7", fact="GROUND_SLAB_MESH_EDGES", target="RFI-B-S10", sub="(h)",
         relation="EXTENDS",
         question="At the edges of the ground slab ('5ø10/m E.W. T=10cm', p.3), how does the mesh end at the ground "
                  "beams: stopped, turned down, or anchored into the beam (with what length)?",
         requested="the ground-slab edge detail",
         missing="mesh printed as a rate with no edge detail",
         cites=[{"t371": "GROUND-SLAB-MESH", "attr": "body", "quote": "5ø10/m"},
                {"t371": "GROUND-SLAB-MESH", "attr": "end_1", "state": "NOT_PRINTED"}, {"t371_gap": "G-T371-7"}],
         pops=["GROUND-SLAB-MESH"],
         kg={"kind": "UNQUANTIFIED", "why": "the 24 mesh lines are valued as plan area x rate; an edge leg or "
                                            "anchorage would add to them and carries no figure in any ledger"},
         dup="no A or B question asks the ground slab; its lap is in R07 (d), not here"),
    dict(row="R16", gap="T-366 SLAB-TEMPERATURE", fact="TEMPERATURE_BARS_16CM_SLAB", target="RFI-B-S10", sub="(i)",
         relation="EXTENDS",
         question="The p.15 TEMPERATURE REINFORCEMENT SCHEDULE has no row for the 16 cm slabs: which temperature "
                  "bars (diameter, spacing) apply to them? (NOTE 1 already prints their lap, 40 x dia.)",
         requested="the temperature bars of the 16 cm slabs",
         missing="no schedule row for this slab thickness",
         cites=[{"t366": "SLAB-TEMPERATURE", "field": "finding", "quote": "no 160 mm row"},
                {"t366_source": "P15N1", "quote": "40 x DIA"}, {"t371": "SLAB-TEMP", "attr": "body"}],
         pops=["SLAB-TEMP"],
         kg={"kind": "UNQUANTIFIED", "why": "3 lines BLOCKED: diameter not established, no bound"},
         dup="no A or B question asks the temperature bars"),
]

# items left open by T-366 / T-371 that get NO new row, each with its reason
NOT_ASKED = [
    dict(item="T-366 item (4) stock length", reason="owner-approved fallback 12 m (OD-V3-3, URBAN-REBAR-NET-AND-"
         "PROCUREMENT@v1): ASSUMED - OWNER-APPROVED, a procurement fact, not a designer one",
         cite={"t366_checked": "DXF"}),
    dict(item="F-T366-2 beam ends on note 9", reason="already RFI-B-S21 (a) / (b) (note-9 scope, end shape at end "
         "supports); 254 lines HELD under DG-30f59008802b7c52", cite={"t366": "COL-MAIN", "field": "finding"}),
    dict(item="FTG-TOP-END-LEGS / FTG-TOP-MESH", reason="already RFI-B-S09 (top-bar ends of F8 / F12 - F14 / FF)",
         cite={"t371": "FTG-TOP-END-LEGS", "attr": "body"}),
    dict(item="GB-BAR-ENDS", reason="already RFI-B-S09 (ground-beam / strap bar ends)",
         cite={"t371": "GB-BAR-ENDS", "attr": "end_1"}),
    dict(item="SB / CB top and bottom ends, CB top corner leg length",
         reason="already RFI-B-S21 (end shape at end supports); the bend diameter is R01",
         cite={"t371": "CB-TOP-CORNER", "attr": "leg_length"}),
    dict(item="nested links", reason="already RFI-B-S20", cite={"t371": "BEAM-LINKS", "attr": "crank"}),
    dict(item="beam side bars 2ø12/30cm", reason="already RFI-B-S19", cite={"t371": "BEAM-SIDE-BARS", "attr": "body"}),
    dict(item="planted-column 4ø16 ends", reason="already RFI-B-S22", cite={"t371": "PLANTED-COL-EXTRA",
                                                                          "attr": "end_1"}),
    dict(item="slab top-bar extent, bar-less panels", reason="already RFI-B-S10 (a) - (c)",
         cite={"t371": "SLAB-UNPRINTED-PANELS", "attr": "body"}),
    dict(item="pool / stair / tank bars (88 lines)", reason="T-359 census, not this task", cite={"t371_gap": "G-T371-0"}),
]

GAPS_REQUIRED = ("G-T371-0", "G-T371-1", "G-T371-2", "G-T371-3", "G-T371-4", "G-T371-5", "G-T371-6", "G-T371-7",
                 "F-T366-1", "F-T366-3", "F-T371-1", "T-366 item (1) / F-T366-2", "T-366 SLAB-TEMPERATURE")


# ------------------------------------------------------------------------------------------- citations
def _ledgers():
    return {"t371": _load(T371_INPUT), "t366": _load(T366_INPUT)}


def resolve_cite(c, led, root=ROOT):
    """return the ledger text the citation points at; RowError when it does not exist or the quote / state / handle
    is not in it."""
    if "t371" in c:
        pops = {p["pop_id"]: p for p in led["t371"]["populations"]}
        p = pops.get(c["t371"])
        if p is None:
            raise RowError(f"cite {c}: no T-371 population {c['t371']!r}")
        a = (p.get("attrs") or {}).get(c.get("attr"))
        if a is None:
            raise RowError(f"cite {c}: population {c['t371']} has no attribute {c.get('attr')!r}")
        if c.get("state") and a.get("state") != c["state"]:
            raise RowError(f"cite {c}: state is {a.get('state')!r}")
        text = " | ".join(str(a.get(k) or "") for k in ("state", "ref", "value", "gap", "rfi"))
    elif "t371_gap" in c:
        text = (led["t371"].get("gaps") or {}).get(c["t371_gap"])
        if not text:
            raise RowError(f"cite {c}: no T-371 gap {c['t371_gap']!r}")
    elif "t366" in c:
        pops = {p["id"]: p for p in led["t366"]["populations"]}
        p = pops.get(c["t366"])
        if p is None:
            raise RowError(f"cite {c}: no T-366 population {c['t366']!r}")
        text = str(p.get(c.get("field")) or "")
        if not text:
            raise RowError(f"cite {c}: T-366 {c['t366']} field {c.get('field')!r} is empty")
    elif "t366_checked" in c:
        text = (led["t366"].get("checked") or {}).get(c["t366_checked"])
        if not text:
            raise RowError(f"cite {c}: T-366 searched no sheet {c['t366_checked']!r}")
        if c.get("handle") and c["handle"] not in text:
            raise RowError(f"cite {c}: handle {c['handle']} not in the T-366 sheet record")
    elif "t366_source" in c:
        s = (led["t366"].get("sources") or {}).get(c["t366_source"])
        if not s:
            raise RowError(f"cite {c}: no T-366 printed source {c['t366_source']!r}")
        text = json.dumps(s, ensure_ascii=False)
    elif "doc" in c:
        p = root / c["doc"]
        if not p.is_file():
            raise RowError(f"cite {c}: no merged file {c['doc']}")
        text = p.read_text(encoding="utf-8")
    else:
        raise RowError(f"cite {c}: unknown form")
    if c.get("quote") and c["quote"] not in text:
        raise RowError(f"cite {c}: quote {c['quote']!r} not in the ledger text")
    return text


def ledger_cites(row):
    return [c for c in row.get("cites") or () if any(k in c for k in ("t371", "t371_gap", "t366", "t366_checked",
                                                                         "t366_source"))]


def check_rows(rows, led, register, root=ROOT):
    """every row: a T-366 / T-371 citation, every citation resolved, one fact once, a known target, populations that
    exist, a kg kind; HELD never 0."""
    facts = collections.Counter(r.get("fact") for r in rows)
    dup = [f for f, n in facts.items() if n > 1 or not f]
    if dup:
        raise RowError(f"one fact asked twice (or unnamed): {dup}")
    pops = {p["pop_id"] for p in led["t371"]["populations"]}
    for r in rows:
        if not ledger_cites(r):
            raise RowError(f"{r.get('row')}: no citation into the merged T-366 / T-371 ledgers (uncited row refused)")
        for c in r["cites"]:
            resolve_cite(c, led, root)
        if r["target"] != "NEW" and r["target"] not in register:
            raise RowError(f"{r['row']}: extends {r['target']}, which is in no RFI file")
        if r["target"] == "NEW" and not r.get("new_id"):
            raise RowError(f"{r['row']}: a new RFI without a proposed id")
        if r["target"] == "NEW" and r["new_id"] in register:
            raise RowError(f"{r['row']}: proposed id {r['new_id']} already exists")
        if "?" not in (r.get("question") or ""):
            raise RowError(f"{r['row']}: the question asks nothing")
        if r["pops"] != "BEND_NOT_PRINTED":
            bad = [p for p in r["pops"] if p not in pops]
            if bad:
                raise RowError(f"{r['row']}: populations {bad} are not in the T-371 census")
        k = r.get("kg") or {}
        if k.get("kind") not in ("LINES", "LEDGER", "UNQUANTIFIED"):
            raise RowError(f"{r['row']}: kg kind {k.get('kind')!r}")
        if k["kind"] == "LEDGER":
            if D(k["low"]) <= 0 or D(k["high"]) < D(k["low"]):
                raise RowError(f"{r['row']}: a ledger range {k['low']} .. {k['high']} (HELD is BLANK, never 0)")
            for c in k.get("cite") or ():
                resolve_cite(c, led, root)
            if not k.get("cite"):
                raise RowError(f"{r['row']}: a ledger kg range without its ledger citation")
        if k["kind"] == "UNQUANTIFIED" and not k.get("why"):
            raise RowError(f"{r['row']}: unquantified without the reason")
    return True


def check_gap_coverage(rows, not_asked=NOT_ASKED, required=GAPS_REQUIRED):
    have = {r["gap"] for r in rows}
    missing = [g for g in required if g not in have]
    if missing:
        raise RowError(f"open gaps with no proposed row: {missing}")
    return True


# ------------------------------------------------------------------------------------------- V3.0.27 view
def _fig(line):
    net, br = line.get("measured_net"), line.get("bounded_range") or None
    if net is not None:
        return D(net), D(net)
    if br and br.get("low") is not None:
        return D(br["low"]), D(br["high"])
    return None, None


def v3027_view(extract_lines, t318_doc=None):
    """(line_id, element_id, state, low, high, parent) for every reinforcement line of V3.0.27. t318_doc: the
    validated URBAN_V3027_INPUTS_V1 doc (arch_v3027.load_inputs); None = no slab re-booking (synthetic villas)."""
    recs = {r["line_id"]: r for r in (t318_doc or {}).get("lines") or ()}
    out, hit = [], set()
    for l in extract_lines:
        lo, hi = _fig(l)
        r = recs.get(l["line_id"])
        if r is None:
            out.append(dict(line_id=l["line_id"], element_id=l["element_id"], state=l["evidence_state"], low=lo,
                            high=hi, parent=None, held=""))
            continue
        hit.add(l["line_id"])
        b = r["before"]
        if lo is None or abs(lo - D(b["low"])) > D("0.0005") or abs(hi - D(b["high"])) > D("0.0005"):
            raise RowError(f"T-318 'before' of {l['line_id']} differs from the extract: stale input")
        if r["action"] == "REBASE":
            p = r["part"]
            out.append(dict(line_id=l["line_id"], element_id=l["element_id"], state="BOUNDED_EXPOSURE",
                            low=D(p["low"]).quantize(D("0.001")), high=D(p["high"]).quantize(D("0.001")),
                            parent=None, held=r.get("held_items") or ""))
            continue
        st = "NOT_APPLICABLE_WITH_EVIDENCE" if r["action"] == "NA" else "BLOCKED_RFI"
        out.append(dict(line_id=l["line_id"], element_id=l["element_id"], state=st, low=None, high=None, parent=None,
                        held=r.get("held_items") or ""))
        if r["action"] == "PARENT":
            p = r["part"]
            out.append(dict(line_id=l["line_id"] + "#PART", element_id=f"{l['element_id']}#SLAB_BAR_ENDS:VALUED",
                            state="BOUNDED_EXPOSURE", low=D(p["low"]).quantize(D("0.001")),
                            high=D(p["high"]).quantize(D("0.001")), parent=l["line_id"],
                            held=r.get("held_items") or ""))
    missing = set(recs) - hit
    if missing:
        raise RowError(f"T-318 lines not in the extract: {sorted(missing)[:3]}")
    return out


def dgp_of(t373_rows):
    """line id -> DOWNGRADE-ONLY record id (DGP-T373-LAP): the T-373 rows proposed HELD."""
    out = {}
    for r in t373_rows:
        if r["proposed"] == "HELD":
            if r["report_group"] not in DGP:
                raise RowError(f"T-373 HELD row {r['line_id']} in group {r['report_group']!r} has no record")
            out[r["line_id"]] = DGP[r["report_group"]]
    return out


def unlock(row, view, bind, bend_pops, dgp):
    pops = bend_pops if row["pops"] == "BEND_NOT_PRINTED" else row["pops"]
    sel = [v for v in view if bind.get(v["parent"] or v["line_id"]) in pops
           and (not row.get("held_item") or row["held_item"] in v.get("held", ""))]
    if row.get("held_item") and not sel:
        raise RowError(f"{row['row']}: no line holds {row['held_item']!r}")
    valued = [v for v in sel if v["low"] is not None]
    blank = [v for v in sel if v["low"] is None]
    for v in blank:
        if v["high"] is not None:
            raise RowError(f"{v['line_id']}: blank low with a high")
    lo = sum((v["low"] for v in valued), D(0)).quantize(Q6)
    hi = sum((v["high"] for v in valued), D(0)).quantize(Q6)
    dg = [v for v in sel if v["line_id"] in dgp]
    dlo = sum((v["low"] for v in dg if v["low"] is not None), D(0)).quantize(Q6)
    dhi = sum((v["high"] for v in dg if v["high"] is not None), D(0)).quantize(Q6)
    return dict(populations=sorted(pops), lines=sel, n_lines=len(sel), n_valued=len(valued), n_blank=len(blank),
                kg_low=lo if valued else None, kg_high=hi if valued else None, n_dgp=len(dg),
                dgp_records=sorted({dgp[v["line_id"]] for v in dg}), dgp_low=dlo if dg else None,
                dgp_high=dhi if dg else None)


def governed(row, u):
    k = row["kg"]
    if k["kind"] == "LINES":
        if u["kg_low"] is None:
            return None, None, "all unlocked lines BLANK (HELD): no figure"
        b = f"the unlocked lines' own range on V3.0.27 ({u['n_valued']} valued lines)"
        if u["n_dgp"]:
            b += (f"; {u['n_dgp']} of them HELD by {', '.join(u['dgp_records'])} on V3.0.28 (range = audit only, "
                  f"UNSUPPORTED BASIS)")
        return u["kg_low"], u["kg_high"], b
    if k["kind"] == "LEDGER":
        return D(k["low"]), D(k["high"]), k["basis"]
    return None, None, "HELD, unquantified: " + k["why"]


# ------------------------------------------------------------------------------------------- build
def _q(x):
    return "" if x is None else format(x, "f")


def build(rows=ROWS, root=ROOT, t318=True):
    led = _ledgers()
    if _sha(EXTRACT) != EXTRACT_SHA:
        raise RowError("the T-297 extract changed: stale pin")
    register = set(led["t371"]["register"]["rfi_register"])
    check_rows(rows, led, register, root)
    check_gap_coverage(rows)
    for n in NOT_ASKED:
        resolve_cite(n["cite"], led, root)
    ex = _load(EXTRACT)
    bind = _load(T371_BIND)["lines"]
    doc = None
    if t318:
        sys.path.insert(0, str(root))
        sys.path.insert(0, str(root / "research" / "agents_t318"))
        import t318_inputs as L27
        from engine.source import arch_v3027 as A
        pid = ex["project"]["project_id"]
        doc = A.load_inputs(L27.build(pid), pid)
    view = v3027_view(ex["lines"], doc)
    t373 = list(csv.DictReader(T373_CSV.open(encoding="utf-8")))
    dgp = dgp_of(t373)
    bend = sorted(p["pop_id"] for p in led["t371"]["populations"]
                  if (p["attrs"].get("bend_diameter") or {}).get("state") == "NOT_PRINTED")
    out_rows, line_rows = [], []
    for r in rows:
        u = unlock(r, view, bind, bend, dgp)
        glo, ghi, gb = governed(r, u)
        rid = r["new_id"] if r["target"] == "NEW" else r["target"]
        out_rows.append(dict(row=r["row"], rfi=f"{rid} {r['sub']}".strip(), relation=r["relation"], gap=r["gap"],
                             fact=r["fact"], question=r["question"], requested=r["requested"], missing=r["missing"],
                             sheets_searched=" ; ".join(_cite_text(c) for c in r["cites"]),
                             populations=" ".join(u["populations"]), lines=u["n_lines"], valued=u["n_valued"],
                             blank_held=u["n_blank"], kg_low_now=_q(u["kg_low"]), kg_high_now=_q(u["kg_high"]),
                             dgp_lines=u["n_dgp"], dgp_records=" ".join(u["dgp_records"]),
                             kg_low_governed=_q(glo), kg_high_governed=_q(ghi), governed_basis=gb,
                             joint=r.get("joint", ""), duplicates=r["dup"]))
        for v in u["lines"]:
            line_rows.append(dict(row=r["row"], rfi=f"{rid} {r['sub']}".strip(), line_id=v["line_id"],
                                  element_id=v["element_id"], population=bind.get(v["parent"] or v["line_id"]),
                                  state_v3027=v["state"], kg_low=_q(v["low"]), kg_high=_q(v["high"]),
                                  dgp_record=dgp.get(v["line_id"], "")))
    summary = dict(schema=SCHEMA, candidate="ARCH_TAKEOFF_V3.0.27 (projection: T-297 extract V3.0.16 + merged T-318 "
                                            "inputs; equal to the reproduced file per tests/t373_lap_binding)",
                   extract_sha256=EXTRACT_SHA, rebar_lines_v3027=len(view), rows=len(out_rows),
                   new_ids=sorted({r["new_id"] for r in rows if r["target"] == "NEW"}),
                   extended=sorted({r["target"] for r in rows if r["target"] != "NEW"}),
                   bend_not_printed_populations=bend, not_asked=NOT_ASKED, id_note=NEXT_FREE_NOTE,
                   lines_unlocked_distinct=len({x["line_id"] for x in line_rows}),
                   kg_computed=0, candidate_lines_changed=0,
                   by_row={o["row"]: {k: o[k] for k in ("rfi", "lines", "valued", "blank_held", "kg_low_now",
                                                        "kg_high_now", "dgp_lines", "kg_low_governed",
                                                        "kg_high_governed")} for o in out_rows})
    return out_rows, line_rows, summary


def _cite_text(c):
    if "t371" in c:
        return f"T-371 {c['t371']}.{c['attr']}" + (f" [{c['state']}]" if c.get("state") else "") + \
            (f" '{c['quote']}'" if c.get("quote") else "")
    if "t371_gap" in c:
        return f"T-371 {c['t371_gap']}"
    if "t366" in c:
        return f"T-366 {c['t366']}.{c['field']}" + (f" '{c['quote']}'" if c.get("quote") else "")
    if "t366_checked" in c:
        return f"T-366 searched {c['t366_checked']}" + (f" (handle {c['handle']})" if c.get("handle") else "")
    if "t366_source" in c:
        return f"T-366 source {c['t366_source']}" + (f" '{c['quote']}'" if c.get("quote") else "")
    return f"{c['doc']} '{c['quote']}'"


ROW_COLS = ("row", "rfi", "relation", "gap", "fact", "question", "requested", "missing", "sheets_searched",
            "populations", "lines", "valued", "blank_held", "kg_low_now", "kg_high_now", "dgp_lines", "dgp_records",
            "kg_low_governed", "kg_high_governed", "governed_basis", "joint", "duplicates")
LINE_COLS = ("row", "rfi", "line_id", "element_id", "population", "state_v3027", "kg_low", "kg_high", "dgp_record")


def write(out_dir, rows, lines, summary):
    out = Path(out_dir)
    with (out / "T376_RFI_ROWS.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ROW_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with (out / "T376_LINE_UNLOCK.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, LINE_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(lines)
    (out / "T376_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                                           encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "research/agents_t376"))
    a = ap.parse_args(argv)
    rows, lines, summary = build()
    write(a.out, rows, lines, summary)
    for r in rows:
        print(f"{r['row']} {r['rfi']:<22} lines {r['lines']:>4} (valued {r['valued']}, blank {r['blank_held']}) now "
              f"{r['kg_low_now'] or '-'} .. {r['kg_high_now'] or '-'} | governed {r['kg_low_governed'] or 'HELD'} .. "
              f"{r['kg_high_governed'] or 'HELD'} | DGP {r['dgp_lines']}")
    print(f"V3.0.27 rebar lines {summary['rebar_lines_v3027']}, distinct lines unlocked "
          f"{summary['lines_unlocked_distinct']}")


if __name__ == "__main__":
    main()
