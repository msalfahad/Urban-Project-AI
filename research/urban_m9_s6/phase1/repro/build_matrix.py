"""S6 Phase 1: the before / after defect matrix from the sweep results (synthetic fixtures + fake-converter DWG cases +
finish cases) and the S6 review register. usage: python3 -I build_matrix.py S6P1_DIR REVIEW_CSV OUT_CSV"""
import csv, json, sys
from pathlib import Path

D, REG, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
J = lambda p: json.loads((D / p).read_text())                                    # noqa: E731
rep = {k: J(f"{k}/S6_REPRO_RESULTS.json") for k in ("rep_before", "rep_v1", "rep_v1strict", "rep_v2")}
dwg = {k: J(f"{k}/S6_REPRO_DWG.json") for k in ("dwg_before", "dwg_v1", "dwg_v1strict", "dwg_v2")}
arch = J("arch_v/S6_REPRO_ARCH_V.json")


def r(kind, case):
    x = rep[kind][case]
    note = x["note"]
    return f"{x['verdict']} (exit {x['exit']}): {note}"[:220]


def d(kind, key, sub=None):
    x = dwg[kind][key]
    if sub:
        x = x[sub]
    b = x.get("blocked")
    s = f"exit {x['exit']}" + (f"; {b['file']} {','.join(b['stopping'])}" if b else "") + \
        ("; earlier outputs -> " + b["superseded"] if b and b.get("superseded") else "") + \
        ("; UNHANDLED TRACEBACK" if x.get("traceback") else "")
    return s


CASES = {
    "S6-ADM-01": ("r30_empty_drawing",), "S6-ADM-02": ("r07_paper_space_frames",), "S6-ADM-03": ("r08_no_frame",),
    "S6-ADM-04": ("r09_frame_exploded",), "S6-ADM-05": ("r10_title_wording",), "S6-ADM-06": ("r24_rotate_all_30",),
    "S6-ADM-07": ("r04_insunits_0", "r05_insunits_absent"), "S6-ADM-08": ("r06_insunits_contradicted",),
    "S6-UNIT-01": ("r01_units_m",), "S6-UNIT-02": ("r02_units_cm", "r03_units_inch"),
    "S6-PLAN-01": ("r11_two_plans_left_titles",), "S6-PLAN-02": ("r12_two_plans_centred_titles",),
    "S6-GEO-01": ("r13_nested_2", "r14_nested_3"), "S6-GEO-02": ("r15_nested_scaled_1000",),
    "S6-GEO-03": ("r17_col_minsert",), "S6-GEO-04": ("r18_col_insert_layer0",),
    "S6-GEO-05": ("r19_col_solid", "r20_col_solid_only"), "S6-GEO-06": ("r22_col_exploded",),
    "S6-GEO-07": ("r21_col_crossed",), "S6-GEO-08": ("r23_col_two_only",), "S6-GEO-09": ("r25_rotate_plans_30",),
    "S6-GEO-10": ("r27_nonuniform_door",), "S6-GEO-11": ("r28_xref_missing",), "S6-GEO-12": ("r31_frozen_old_label",),
    "S6-GEO-13": ("r26_layer_off_partition",), "S6-GEO-14": ("r29_mtext_labels",),
}
DWG = {"S6-ADM-09": ("D1_empty_conversion", None), "S6-ADM-10": ("D2_stale_conversion", "rev2_converter_wrote_nothing"),
       "S6-ADM-11": ("D3_garbage_conversion", None), "S6-ADM-12": ("D4_same_stem", None)}
# the Phase 1 disposition of every review entry: FIXED (measured right or blocked with exit 2 and its reason),
# LOUD (still measured differently, but a REVIEW flag names the cause on the BOQ - the reader fix is Phase 2),
# OPEN (unchanged; why), CONTROL (a control / not reproduced), STILL_FIXED
STATUS = {
    "S6-ADM-01": ("FIXED", "exit 2 EMPTY_MODEL_SPACE; no BOQ; DRAWING_DISCOVERY.json + ADMISSION_BLOCKED.json"),
    "S6-ADM-02": ("FIXED", "exit 2 PAPER_SPACE_SHEETS; measured with --region (recorded reviewer input); viewport reading is Phase 3"),
    "S6-ADM-03": ("FIXED", "exit 2 PLAN_TITLES_OUTSIDE_ANY_FRAME (--region measures it)"),
    "S6-ADM-04": ("FIXED", "V2 reads frames drawn as lines (identical quantities, FRAME_DRAWN_AS_LINES review flag); V1 strict exit 2"),
    "S6-ADM-05": ("FIXED", "exit 2 NO_FLOOR_PLAN_TITLE (the title vocabulary is not widened in Phase 1)"),
    "S6-ADM-06": ("FIXED", "exit 2 NO_PLAN_REGION (measuring a rotated sheet is Phase 2/3)"),
    "S6-ADM-07": ("FIXED", "exit 2 UNITS_NOT_DECLARED with the inferred unit in the evidence; --units mm measures identically"),
    "S6-ADM-08": ("FIXED", "exit 2 UNITS_CONTRADICTED"),
    "S6-ADM-09": ("FIXED", "strict conversion: EMPTY_CONVERSION -> exit 2 DWG_CONVERSION_BLOCKED"),
    "S6-ADM-10": ("FIXED", "the stale target is removed before converting; earlier BOQ moved to SUPERSEDED_<n>; exit 2"),
    "S6-ADM-11": ("FIXED", "CONVERTED_FILE_UNREADABLE -> exit 2, no traceback"),
    "S6-ADM-12": ("FIXED", "conversions named <stem>.<sha12>.dxf; the plan read is the plan; SAME_FILE_NAME warning"),
    "S6-UNIT-01": ("FIXED", "V2 unit-relative tolerances: identical quantities in m / cm / in; V1 strict exit 2 LEGACY_TOLERANCE_TOO_COARSE"),
    "S6-PLAN-01": ("FIXED", "V2 splits along empty bands: identical quantities; V1 strict exit 2 REGION_CUT_CROSSES_GEOMETRY"),
    "S6-GEO-01": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED + FILLS_NOT_READ_IN_PLAN on the rooms; reading nested hatches is Phase 2"),
    "S6-GEO-03": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED + FILLS_NOT_READ_IN_PLAN; MINSERT cells in the hatch reader is Phase 2"),
    "S6-GEO-04": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED (layer-0 inheritance in the hatch reader is Phase 2)"),
    "S6-GEO-05": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED + FILLS_NOT_READ_IN_PLAN (SOLID as fill is Phase 2)"),
    "S6-GEO-06": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED (exploded outlines are Phase 2)"),
    "S6-GEO-08": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED (the >= 3 rectangles layer rule is Phase 2)"),
    "S6-GEO-09": ("LOUD", "REVIEW COLUMN_EVIDENCE_NOT_MEASURED (rotated rectangles are Phase 2)"),
    "S6-GEO-10": ("LOUD", "REVIEW DOOR_SYMBOLS_DISTORTED on both plans (reading scaled swings is Phase 2)"),
    "S6-GEO-11": ("FIXED", "exit 2 XREF_NOT_SUPPLIED; --accept-missing-xref measures with a REVIEW flag (recorded)"),
    "S6-GEO-12": ("LOUD", "REVIEW HIDDEN_LAYER_CONTENT on the BOQ (honouring layer state is an owner question: Phase 2)"),
    "S6-GEO-13": ("CONTROL", "identical; now also REVIEW HIDDEN_LAYER_CONTENT (the luck is visible)"),
    "S6-TXT-01": ("OPEN", "route G intake: frozen route, not changed in Phase 1"),
    "S6-TXT-02": ("OPEN", "unchanged in V1 and V2: the room is UNLABELLED with its ARCH.SPACE RFI; diacritic normalisation is Phase 2"),
    "S6-ARC-01": ("FIXED", "V2: FIN.PAINT BLOCKED_RFI for the band above the tile (Q7), NOT_APPLICABLE_WITH_EVIDENCE when the tile is full height"),
    "S6-ARC-02": ("FIXED", "V2: stair-hall FIN.PLASTER / FIN.PAINT / FIN.SKIRTING BLOCKED_RFI (Q-S6-4); no finish assumed"),
    "S6-ARC-03": ("OPEN", "wall_height.derive is an owner-rule input: not changed without approval (assessment A6)"),
    "S6-ARC-04": ("OPEN", "the opening-deduction rule is an owner decision (requirement 10): unchanged, question listed"),
    "S6-ARC-05": ("FIXED", "V2: every strip reviewed; one ARCH.THRESHOLD / ARCH.WINDOW_REVEAL BLOCKED_RFI line per opening; coverage gate PASS"),
    "S6-ARC-06": ("PARTLY", "V2: the strips of the wide opening are UNATTRIBUTED RFIs (failed_checks listed); the opening class itself is Phase 2"),
    "S6-ARC-07": ("FIXED", "V2: reveals are WINDOW_REVEAL RFIs (floor status not established), split out in doorway_strips_by_class_m2; V1 figure kept"),
    "S6-STR-01": ("FIXED", "V2 + --structural requires --conventions (exit 2 STRUCTURAL_CONVENTIONS_REQUIRED); V1 prints a WARNING; route G unchanged"),
    "S6-ENV-01": ("OPEN", "environment: values agree within 1e-9; the V1 snapshot test compares at 1e-6, byte hashes only within one Python"),
    "S6-FIX-01": ("STILL_FIXED", "tests/m9_s5 pass"), "S6-FIX-02": ("STILL_FIXED", "tests/m9_s5 pass"),
    "S6-FIX-03": ("STILL_FIXED", "tests/m9_s5 pass"),
}
NEW = [
    ("S6P1-NEW-01", "real plan, frames drawn as LINEs on the wall layer (V2 frames-from-lines path)", "V2 1F plate = the sheet frame",
     "FIXED", "the frame's own sides are dropped from the region (frame_side_segments_dropped); synthetic test frame_on_wall_layer"),
    ("S6P1-NEW-02", "real plan wrapped in blocks two deep", "a bedroom alcove split off as UNLABELLED (hatches two deep unread)",
     "LOUD", "REVIEW FILLS_NOT_READ_IN_PLAN on the floor and the rooms; reader fix Phase 2"),
    ("S6P1-NEW-03", "V1 --strict-admission on a metre drawing", "admitted, then measured with 1-unit (1 m) tolerances",
     "FIXED", "exit 2 LEGACY_TOLERANCE_TOO_COARSE"),
    ("S6P1-NEW-04", "real plan door / passage strips set back from the wall face or spanning two openings",
     "classed from the boundary only", "LOUD", "UNATTRIBUTED BLOCKED_RFI with failed_checks and extents; never excluded"),
    ("S6P1-NEW-05", "lower length thresholds equal to drafted dimensions (100 mm face piece, 300 mm overlap, 0.4 / 0.5 m gap)",
     "a drafted length 1e-14 below its threshold (metre coordinates, or decimal mm coordinates) is dropped: the real plan in "
     "metres loses two 100 mm face pieces (one 0.20 m wall-run difference)",
     "OPEN", "a relative 1e-9 slack makes metres equal millimetres but changes the millimetre result of the reference plan "
             "(two more openings found on one floor), so it is NOT adopted; strict xfail test records it; Phase 2 with review"),
]
rows = list(csv.DictReader(REG.open(encoding="utf-8")))
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "fixture", "severity", "before_HEAD_V1", "after_V1_default", "after_V1_strict", "after_V2",
                "phase1_status", "phase1_evidence"])
    for x in rows:
        i = x["id"]
        if i in CASES:
            cs = CASES[i]
            cell = lambda k: " | ".join(f"{c}: {r(k, c)}" for c in cs)                    # noqa: E731
            b, v1, st, v2 = cell("rep_before"), cell("rep_v1"), cell("rep_v1strict"), cell("rep_v2")
        elif i in DWG:
            k, sub = DWG[i]
            b, v1, st, v2 = (d(n, k, sub) for n in ("dwg_before", "dwg_v1", "dwg_v1strict", "dwg_v2"))
            if i == "S6-ADM-12":
                b += f"; plan read is the plan: {dwg['dwg_before'][k]['plan_read_is_A']}"
                v2 += f"; plan read is the plan: {dwg['dwg_v2'][k]['plan_read_is_A']}"
                st += f"; plan read is the plan: {dwg['dwg_v1strict'][k]['plan_read_is_A']}"
                v1 += f"; plan read is the plan: {dwg['dwg_v1'][k]['plan_read_is_A']}"
        elif i.startswith("S6-ARC-0") and i in ("S6-ARC-01", "S6-ARC-02", "S6-ARC-05", "S6-ARC-07"):
            key = {"S6-ARC-01": "ARC-D2 finish above partial wet tile", "S6-ARC-02": "ARC-D3 stair-hall walls and skirting",
                   "S6-ARC-05": "ARC-D4/D8 doorway strips (thresholds, window reveals)",
                   "S6-ARC-07": "ARC-D4/D8 doorway strips (thresholds, window reveals)"}[i]
            sv = lambda m: "SILENT" if arch[m][key]["silent"] else "line or RFI for every surface"   # noqa: E731
            b, v1, st, v2 = sv("ARCH_TAKEOFF_V1"), sv("ARCH_TAKEOFF_V1"), sv("ARCH_TAKEOFF_V1") + " (strict adds admission only)", sv("ARCH_TAKEOFF_V2")
        elif i == "S6-TXT-02":
            k = "ARC-D7 diacritics on a room word"
            b = v1 = st = f"rooms changed: {not arch['ARCH_TAKEOFF_V1'][k]['gf_rooms_same']}; space RFI {arch['ARCH_TAKEOFF_V1'][k]['space_rfis']}"
            v2 = f"rooms changed: {not arch['ARCH_TAKEOFF_V2'][k]['gf_rooms_same']}; space RFI {arch['ARCH_TAKEOFF_V2'][k]['space_rfis']}"
        else:
            b, v1, st, v2 = x["result"], "unchanged", "-", "-"
        stt, ev = STATUS.get(i, ("CONTROL", "control / not reproduced"))
        w.writerow([i, x["fixture"], x["severity"], b, v1, st, v2, stt, ev])
    for i, fx, before, stt, ev in NEW:
        w.writerow([i, fx, "HIGH" if i.endswith("01") else "MED", before, "-", "-", ev, stt, ev])
print(OUT)
