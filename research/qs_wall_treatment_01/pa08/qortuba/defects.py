"""Section 24: PA08_BLIND_DEFECTS observed on Qortuba with the frozen engine.  Recorded, not fixed."""

from __future__ import annotations

import json

from research.qs_wall_treatment_01.pa08.qortuba import common as C

DEFECTS = [
    {"DEFECT_ID": "QBD-01", "SOURCE_CONDITION": "Arabic room labels typed through a Latin-glyph keyboard-mapped shape font ('whgm' = صالة, 'plHL' = حمام); no Unicode Arabic in the DWG",
     "ENGINE_BEHAVIOUR": "classify_text sees Latin strings: 10 labels UNDECODABLE_TEXT / UNCLASSIFIED; identity stays UNRESOLVED even where the English partner reads",
     "EXPECTED_SAFE_BEHAVIOUR": "recognise the keyboard-map convention as a deterministic transliteration (AI_INTERPRETED at most) or keep UNRESOLVED", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
     "AFFECTED_TRADES": ["identity of every room", "wet-room detection", "plaster / paint / skirting eligibility by room class"], "SEVERITY": "HIGH_YIELD_LOSS_SAFE"},
    {"DEFECT_ID": "QBD-02", "SOURCE_CONDITION": "door blocks (block '6') draw the leaf and frame pieces only; no swing arc; the frame pieces (59 mm) stand in for jamb returns",
     "ENGINE_BEHAVIOUR": "1 of 8 doors CONFIRMED (leaf + returns); the others fall in UNRESOLVED partitions or read as SINGLE_FACE_GAP", "EXPECTED_SAFE_BEHAVIOUR": "PROBABLE / UNRESOLVED (as happened) or a door evidence rule for leaf-only blocks",
     "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["openings", "plaster deductions", "skirting door deductions", "room topology"], "SEVERITY": "HIGH_YIELD_LOSS_SAFE"},
    {"DEFECT_ID": "QBD-03", "SOURCE_CONDITION": "150 mm partitions whose faces are shared with adjacent thin strips (window frame lines 7 mm apart, door frame pieces, 80-120 mm pairs) and door-frame pairs shorter than thick",
     "ENGINE_BEHAVIOUR": "31 FACE_SIDE_CONFLICT + 44 SHORT_TRANSVERSE_PAIR + 25 ISOLATED_PAIR: most partitions UNRESOLVED; the hall, three bedrooms, dress and two baths merge into ONE BOUNDARY_PROVISIONAL cell (204.66 m2) carrying 14 labels",
     "EXPECTED_SAFE_BEHAVIOUR": "refuse (as happened); a partition should not lose to a frame strip that is itself rejected as THIN_PAIR", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
     "AFFECTED_TRADES": ["floor areas", "plaster", "paint", "skirting", "ceiling", "wet rooms", "blockwork of partitions"], "SEVERITY": "CRITICAL_YIELD_LOSS_SAFE"},
    {"DEFECT_ID": "QBD-04", "SOURCE_CONDITION": "16 of 101 linear dimensions are rotated dimensions whose extension origins are offset perpendicular to the dimension line",
     "ENGINE_BEHAVIOUR": "cad_adapter measures the raw distance between the two extension origins (e.g. 164.9 mm for an authored 150 mm); the register marks them READ_STATUS SOURCE_ESTABLISHED with the wrong measured value",
     "EXPECTED_SAFE_BEHAVIOUR": "project the extension origins onto the dimension direction (LibreDWG's act_measurement equals the author's number for all 16)", "SILENT_WRONG": True, "SAFE_REFUSAL": False,
     "AFFECTED_TRADES": ["number reading; no quantity consumes the measured dimension value in PA07R2 (units come from INSUNITS); the dimension register itself is wrong"], "SEVERITY": "HIGH_SILENT_REGISTER_VALUE_NO_QUANTITY_PATH",
     "CRITICAL_BLIND_DEFECT": False, "QUANTITY_MADE_HUMAN_REVIEW": "the 16 rows carry STATUS HUMAN_REVIEW in PA08_QORTUBA_DIMENSION_REGISTER"},
    {"DEFECT_ID": "QBD-05", "SOURCE_CONDITION": "plot boundary drawn as double lines 150 mm apart (39.5 x 27.2 m) on the FRAME block, and the site region between the boundary and the building",
     "ENGINE_BEHAVIOUR": "the boundary pairs are wall candidates (FACE_SIDE_CONFLICT / ISOLATED_PAIR, UNRESOLVED) whose chords enclose a 636 m2 cell classed INTERIOR (SPACE_CLASS) and BOUNDARY_PROVISIONAL",
     "EXPECTED_SAFE_BEHAVIOUR": "EXTERIOR / SITE classification of a cell bounded by the plot boundary; refusal as happened", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
     "AFFECTED_TRADES": ["floor areas (a site region could be offered as a room if it ever became ESTABLISHED)"], "SEVERITY": "MEDIUM_CLASSIFICATION_SAFE_BY_GATE"},
    {"DEFECT_ID": "QBD-06", "SOURCE_CONDITION": "engine vocabulary gaps: PAINTRY (pantry misspelt), M.B.ROOM, DRESS, تحضير, ملابس; HALL reads CORRIDOR while صالة reads LIVING",
     "ENGINE_BEHAVIOUR": "UNCLASSIFIED_TEXT; a bilingual pair classifies to two classes", "EXPECTED_SAFE_BEHAVIOUR": "UNRESOLVED identity (as happened); vocabulary and a bilingual-conflict rule for PA09", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
     "AFFECTED_TRADES": ["identity", "wet-room class of the pantry"], "SEVERITY": "MEDIUM_SAFE"},
    {"DEFECT_ID": "QBD-07", "SOURCE_CONDITION": "floor words: 'SECOND FLOOR PLAN' (title) with 'Floor 2' (office address) and 'LEVEL R.F = 4.00 m' in one view",
     "ENGINE_BEHAVIOUR": "PA07R2 guard: HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS; STOREY_STATUS blocks every line", "EXPECTED_SAFE_BEHAVIOUR": "HUMAN_REVIEW (correct); an owner storey name releases it", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
     "AFFECTED_TRADES": ["all (gate)"], "SEVERITY": "LOW_OVER_CONSERVATIVE"},
    {"DEFECT_ID": "QBD-08", "SOURCE_CONDITION": "windows drawn as four frame lines (7 mm apart) on the WINDOW layer inside the wall thickness, no GLAZING role configured",
     "ENGINE_BEHAVIOUR": "FRAME_WITHIN_HOST_BAND rejections (33); one CONFIRMED_WINDOW PROVISIONAL (2750 mm) where the host band is accepted; six window groups unseen", "EXPECTED_SAFE_BEHAVIOUR": "PROVISIONAL window (as happened)",
     "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["openings", "plaster window deductions"], "SEVERITY": "MEDIUM_YIELD_LOSS_SAFE"},
    {"DEFECT_ID": "QBD-09", "SOURCE_CONDITION": "ROOF: an open roof terrace east of the apartment, bounded by the 200 mm envelope and the plot boundary lines",
     "ENGINE_BEHAVIOUR": "EXTERIOR_LABELLED cell of 43.31 m2 (a fragment cut by unresolved chords); the rest of the roof falls into unlabelled provisional cells", "EXPECTED_SAFE_BEHAVIOUR": "refusal (as happened)",
     "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["roof / open area"], "SEVERITY": "MEDIUM_YIELD_LOSS_SAFE"},
    {"DEFECT_ID": "QBD-10", "SOURCE_CONDITION": "stair drawn as 24 nosing lines and a well polyline on layer STAIR; lift shaft on layer 'lift' with a hatch",
     "ENGINE_BEHAVIOUR": "nosing lines rejected as walls (REPETITION / ENCLOSES_PARALLEL_FACES); no stair or shaft object; the stair well merges into the hall cell", "EXPECTED_SAFE_BEHAVIOUR": "refusal (as happened); a stair object rule for PA09",
     "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["stair", "ceiling deductions", "floor area of the hall"], "SEVERITY": "MEDIUM_YIELD_LOSS_SAFE"},
]


def main():
    out = {"ARTIFACT": "PA08_BLIND_DEFECTS", "PROJECT": "QORTUBA", "ENGINE": "PA07R2 frozen (FREEZE_PA07R2 1f0c2402dcffc966)", "POLICY": "recorded during the blind test; nothing patched before the freeze",
           "DEFECTS": DEFECTS, "COUNT": len(DEFECTS), "SILENT_WRONG_COUNT": sum(1 for d in DEFECTS if d["SILENT_WRONG"]), "CRITICAL_BLIND_DEFECTS": [d["DEFECT_ID"] for d in DEFECTS if d.get("CRITICAL_BLIND_DEFECT")],
           "QUANTITY_RELEASED_BY_A_DEFECT": 0, "NOTE": "the only silent wrong value (QBD-04) lives in the dimension register and feeds no quantity; every quantity line of the run is blocked"}
    C.write("PA08_BLIND_DEFECTS", out)
    print(json.dumps({k: out[k] for k in ("COUNT", "SILENT_WRONG_COUNT", "CRITICAL_BLIND_DEFECTS")}))


if __name__ == "__main__":
    main()
