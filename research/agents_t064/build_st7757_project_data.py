"""T-064: convert the typed route G profile research/urban_engine_m4_correctness/profile_st7757_m4.json (left untouched)
into the controlled project data file (engine/source/project_data_file.py, owner Q-17 A) beside it:
research/urban_engine_m4_correctness/project_data_st7757_t064.json.

Status of each key from the T-044 r2 audit (research/agents_t044/T-044_PROFILE_AUDIT.md) and the owner answers, and
re-checked by worker 2 on 2026-10-20 against the Drive copies (sha256 below): DXF texts of ST7757 and P7757 with ezdxf,
ST7757.pdf p.13 read visually at 110 dpi.
    PRINTED      -> DRAWING-VERIFIED (sheet text as found)
    DIFFERENT    -> HELD (CB_SUPPORT_BAR_EXTENT_FRAC: '0.3 Ln2' is printed beside '0.22 Ln')
    NOT_PRINTED  -> HELD (CB_SUPPORT_BAR_SPAN_BASIS)
    FOUNDING_DEPTH_M -> HELD (owner Q-21 = C: the note prints the EXCAVATION level, the founding datum is unresolved)
    SLAB_PROJECT_DEFAULT_THICKNESS_M -> DRAWING-VERIFIED from the ST7757 SH12 note (owner Q-14: 16 cm unless a drawing
                 says otherwise)
    NECK_TOP_LEVEL_M -> INFERRED (T-044: the value +1.00 is printed as the GF level; "neck top = GF level" is a reading
                 of the p.13 details, not a printed statement), citing GF_FLOOR_LEVEL_M and GB_EXTERIOR_DETAIL
No client name or personal data is written: drawings are named by drawing number and Drive file title only.

Run: python3 -I research/agents_t064/build_st7757_project_data.py  (stdlib only; rewrites the JSON, then validates it)
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILE = os.path.join(ROOT, "research", "urban_engine_m4_correctness", "profile_st7757_m4.json")
OUT = os.path.join(ROOT, "research", "urban_engine_m4_correctness", "project_data_st7757_t064.json")

PROJECT = "P7757 / ST7757 development villa (route G profile ST7757_M4)"
ST_DXF = "ST7757 dxf.dxf (sha256 9f9d1179...38079)"
ST_PDF = "ST7757.pdf (sha256 74da1523...337e3)"
P_DXF = "P7757.dxf in P7757_DXF_COMPRESSED.zip (sha256 ab54dd55...31cc4)"
REV_ST_DXF = "no revision text in the DXF (2 630 texts searched)"
REV_ST_PDF = "no revision printed (title block: SCALE / DATE May 06, 2026 / FILE NO ST - 7757)"
REV_P_DXF = "no revision text in the DXF (664 texts searched)"
AUDIT = "T-044 r2 audit (worker, 2026-10-19), re-checked by worker 2 T-064 (2026-10-20)"


def rec(key, value, unit, kind, status, drawing_file, number, rev, sheet, reference, applies, source, **extra):
    r = {"key": key, "project": PROJECT, "kind": kind, "unit": unit, "value": value, "status": status,
         "drawing_file": drawing_file, "drawing_number": number, "revision": rev, "sheet": sheet,
         "reference": reference, "applies_to": applies, "reviewer_or_source": source, "entered_by": "TYPED"}
    r.update(extra)
    return r


def build(profile):
    conv = {c["id"]: c for c in profile["conventions"]}
    R = []
    R.append(rec("STOREY_HEIGHT_GF", conv["STOREY_HEIGHT_GF"]["base"], "m", "number", "DRAWING-VERIFIED",
                 P_DXF, "P7757", REV_P_DXF, "GF and 1F plans (LEVEL layer); NW elevation",
                 "level texts '+1.00' (GF plan) and '+5.50' (1F plan): 5.50 - 1.00 = 4.50 m floor to floor; elevation "
                 "dimension '4500' (and '5500' to +5.50 from 0.00); ST7757 SH08 also prints '+1.00'",
                 {"floors": ["GF"], "members": ["COLUMN", "STAIR"]}, AUDIT,
                 notes="profile source 'VE-AA-09' is not a sheet title in either DXF; the value rests on the level texts"))
    R.append(rec("STOREY_HEIGHT_1F", conv["STOREY_HEIGHT_1F"]["base"], "m", "number", "DRAWING-VERIFIED",
                 P_DXF, "P7757", REV_P_DXF, "1F and 2F plans (LEVEL layer); SE / NW elevations",
                 "level texts '+5.50' (1F plan) and '+9.70' (2F plan; ST7757 SH02 '+9.70' twice): 9.70 - 5.50 = 4.20 m; "
                 "elevation chain '8700' = 4500 + 4200",
                 {"floors": ["1F"], "members": ["COLUMN", "STAIR"]}, AUDIT))
    R.append(rec("STOREY_HEIGHT_2F", conv["STOREY_HEIGHT_2F"]["base"], "m", "number", "DRAWING-VERIFIED",
                 P_DXF, "P7757", REV_P_DXF, "SE and NW elevations (vertical dimension chain)",
                 "chain '1000 / 8700 / 4200 / 500' = '14400' overall: 4200 is the top storey under the 500 parapet",
                 {"floors": ["2F"], "members": ["COLUMN", "STAIR"]}, AUDIT,
                 notes="no '+13.90' level text in either DXF; the value rests on the printed elevation chain only"))
    gb = conv["GB_TYPICAL_SECTIONS"]
    R.append(rec("GB_TYPICAL_SECTIONS", gb["classes"], "none", "table", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 (details; not in the DXF)",
                 "titles 'Ground Beams. Less than 2.5m length' 30x30, 'Ground Beams. Less than 5m length without "
                 "concentrated load' 30x40, 'Ground Beams. More than 5m length without concentrated load' 30x60",
                 {"floors": ["GROUND"], "members": ["GROUND_BEAM"]}, AUDIT,
                 conditions=["without concentrated load (printed on the 30x40 and 30x60 titles): a ground beam carrying "
                             "a point load (e.g. a planted column) has no printed typical section",
                             "the exact 2.5 m / 5.0 m band edges are a reading of 'less than' / 'more than'"]))
    R.append(rec("FOUNDING_DEPTH_M", conv["FOUNDING_DEPTH_M"]["base"], "m", "number", "HELD",
                 ST_DXF, "ST7757", REV_ST_DXF, "SH11 schedules sheet (= PDF p.9), boxed note 1 under the soil table",
                 "S-ARAB SHX note decoded (T-044 r2): 'excavation level not less than 1.5 m below the existing plot "
                 "ground level'; TEXT '1.5' on S-TEXT.SCH (re-found 2026-10-20)",
                 {"members": ["FOOTING", "NECK", "EXCAVATION"]}, AUDIT + "; owner answer Q-21 = C (2026-10-19)",
                 hold_reason="owner Q-21 = C: the note prints the EXCAVATION formation level (a minimum), not the "
                             "footing underside; founding datum unresolved until the complete foundation level "
                             "arrangement is verified; the 28 necks are not computed on it",
                 alternatives=[{"value": 2.0, "unit": "m", "status": "NOT_PRINTED",
                                "note": "profile planning upper bound (OQ-13), printed nowhere"}]))
    R.append(rec("GF_FLOOR_LEVEL_M", conv["GF_FLOOR_LEVEL_M"]["base"], "m", "number", "DRAWING-VERIFIED",
                 ST_DXF, "ST7757", REV_ST_DXF, "SH08 ground-beam plan (LEVEL layer); P7757 GF plan",
                 "level text '+1.00' (5 on ST7757 SH08, 4 on the P7757 GF plan, 1 on an elevation)",
                 {"floors": ["GF", "GROUND"], "members": ["ALL"]}, AUDIT))
    R.append(rec("NECK_TOP_LEVEL_M", conv["NECK_TOP_LEVEL_M"]["base"], "m", "number", "INFERRED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 typical footing and exterior ground-beam details",
                 "no neck-top level is printed; the GF level '+1.00' is printed (GF_FLOOR_LEVEL_M)",
                 {"members": ["NECK"]}, AUDIT,
                 logic="the p.13 'Ground Beams. for exterior walls' detail runs its top to 'Ground Floor slab level' and "
                       "the footing details carry the column bars from the footing up through the upper ground beam: "
                       "the neck ends where the GF column starts, at the GF slab level +1.00 (GF_FLOOR_LEVEL_M); a "
                       "reading of the details, not a printed neck level",
                 inferred_from=["GF_FLOOR_LEVEL_M", "GB_EXTERIOR_DETAIL"],
                 notes="every neck stays HELD anyway: it also needs FOUNDING_DEPTH_M (HELD, Q-21 C)"))
    R.append(rec("OUTER_GROUND_LEVEL_M", conv["OUTER_GROUND_LEVEL_M"]["base"], "m", "number", "DRAWING-VERIFIED",
                 ST_DXF, "ST7757", REV_ST_DXF, "SH08 ground-beam plan, levels outside the building",
                 "'%%p0.00' (6 texts, block LEL) and '+0.15' (6 texts)",
                 {"floors": ["GROUND"], "members": ["GROUND_BEAM", "STAIR"]}, AUDIT,
                 alternatives=[{"value": 0.15, "unit": "m", "status": "DRAWING-VERIFIED",
                                "note": "'+0.15' printed at other positions outside the building; which level applies "
                                        "to a member is bound by its position, not decided by this record"},
                               {"value": 0.30, "unit": "m", "status": "PRINTED_ELSEWHERE",
                                "note": "P7757 GF plan prints '+0.30' (annex floor level; not an outer ground level)"}]))
    R.append(rec("GB_EXTERIOR_DETAIL", "P13_EXTERIOR_WALLS", "none", "choice", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 (details; not in the DXF)",
                 "'Ground Beams. for exterior walls': width '30', depth 'FOLLOW ARCH.', from 'Ground Floor slab level' "
                 "to 'Outer Normal ground level'",
                 {"floors": ["GROUND"], "members": ["GROUND_BEAM"]}, AUDIT,
                 conditions=["W = 0.30 m printed; depth follows the architectural levels (GF_FLOOR_LEVEL_M, "
                             "OUTER_GROUND_LEVEL_M)",
                             "ST7757 SH12 SHX note: exterior ground beams on the neighbour side are cast on and under "
                             "black block built up from foundation level (a build-up this single detail does not "
                             "separate)"]))
    R.append(rec("BLINDING_THICKNESS_M", conv["BLINDING_THICKNESS_M"]["base"], "m", "number", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 (details; not in the DXF)",
                 "'10cm Plain con.' under both 'TYP. DETAIL OF ISOLATED FOOTING.' details; '10' dimensioned under all "
                 "four ground-beam sections",
                 {"members": ["FOOTING", "GROUND_BEAM", "BLINDING"]}, AUDIT,
                 notes="the 5 cm screed and the membrane above it are separate works, not blinding"))
    R.append(rec("BLINDING_UNDER", conv["BLINDING_UNDER"]["base"], "none", "choice", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 (details; not in the DXF)",
                 "the plain-concrete layer is drawn and dimensioned under both footing details and all four "
                 "ground-beam sections",
                 {"members": ["BLINDING"]}, AUDIT))
    R.append(rec("CB_SUPPORT_BAR_EXTENT_FRAC", conv["CB_SUPPORT_BAR_EXTENT_FRAC"]["base"], "fraction", "number",
                 "HELD", ST_DXF, "ST7757", REV_ST_DXF, "SH03, SH05, SH07 continuous-beam typical details (S-DIM.SCH)",
                 "dimension overrides '0.22 Ln', '0.22 Ln1', '0.22 Ln2' and '0.3 Ln2' (one per detail)",
                 {"members": ["CONTINUOUS_BEAM_REBAR"]}, AUDIT,
                 hold_reason="T-044 class DIFFERENT: a second extent '0.3 Ln2' is printed beside 0.22; which bars take "
                             "which extent is not settled (rebar only; no concrete line uses it)"))
    R.append(rec("CB_SUPPORT_BAR_SPAN_BASIS", conv["CB_SUPPORT_BAR_SPAN_BASIS"]["base"], "none", "choice", "HELD",
                 ST_DXF, "ST7757", REV_ST_DXF, "SH03, SH05, SH07 continuous-beam typical details",
                 "'Ln' / 'Ln1' / 'Ln2' dimensions carry no axis or face note",
                 {"members": ["CONTINUOUS_BEAM_REBAR"]}, AUDIT,
                 hold_reason="T-044 class NOT_PRINTED: axis-to-axis is a reading of where the dimension lines end "
                             "(rebar only; no concrete line uses it)"))
    R.append(rec("CB_BOTTOM_EXTENSION_M", conv["CB_BOTTOM_EXTENSION_M"]["base"], "m", "number", "DRAWING-VERIFIED",
                 ST_DXF, "ST7757", REV_ST_DXF, "SH03 (2), SH05 (2), SH07 (4) continuous-beam typical details",
                 "dimension override '7.5cm' at the bottom bar ends past the interior support",
                 {"members": ["CONTINUOUS_BEAM_REBAR"]}, AUDIT))
    R.append(rec("SLAB_PROJECT_DEFAULT_THICKNESS_M", conv["SLAB_PROJECT_DEFAULT_THICKNESS_M"]["base"], "m", "number",
                 "DRAWING-VERIFIED", ST_DXF, "ST7757", REV_ST_DXF, "SH12 columns and axes sheet, S-NOTE (SHX Arabic)",
                 "decoded (T-044 r2): 'all slabs to be cast 16 cm thick unless stated otherwise' (text '16' in the "
                 "note, re-found 2026-10-20); also ST7757 PDF p.8 general note 18 and p.1 note",
                 {"floors": ["GF", "1F", "2F"], "members": ["SLAB"]}, AUDIT + "; owner answer Q-14 (2026-10-19)",
                 conditions=["owner Q-14: 0.16 m only where no slab, zone or detail prints its own value (the two 2F "
                             "panels tagged 'T 18' keep 18 cm); never applied to stairs, balconies, depressed slabs, "
                             "landings or special elements without checking their details"]))
    R.append(rec("BLINDING_PROJECTION_M", conv["BLINDING_PROJECTION_M"]["base"], "m", "number", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 (details; not in the DXF)",
                 "'10 | 30 | 10' under each ground-beam section; '10' each side of 'L x W' on the second footing detail",
                 {"members": ["FOOTING", "GROUND_BEAM", "BLINDING"]}, AUDIT))
    R.append(rec("LINTEL_SCHEDULE", conv["LINTEL_SCHEDULE"]["rows"], "none", "table", "DRAWING-VERIFIED",
                 ST_PDF, "ST7757", REV_ST_PDF, "PDF p.13 'LINTEL SCHEDULE' (not in the DXF)",
                 "0-100 B x 20 2Ø12 / 2Ø10; 101-200 B x 20 2Ø14 / 2Ø12; 201-300 B x 30 3Ø16 / 3Ø14; 301-500 B x 40 "
                 "3Ø18 / 3Ø14; 501-750 B x 55 4Ø18 / 3Ø14; stirrups 5Ø8/M; B = width of the block wall",
                 {"members": ["LINTEL"]}, AUDIT,
                 conditions=["bounds inclusive as printed; a width between two bands is a schedule gap, never rounded"]))
    return {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PROJECT,
            "notes": "T-064 conversion of profile_st7757_m4.json (17 keys; the profile itself is unchanged). Every "
                     "value was TYPED by a person or agent from the printed drawings; none is automatic extraction.",
            "records": R}


def main():
    sys.path.insert(0, ROOT)
    from engine.source import project_data_file as PDF
    with open(PROFILE, encoding="utf-8") as fh:
        profile = json.load(fh)
    doc = build(profile)
    keys = {r["key"] for r in doc["records"]}
    missing = {c["id"] for c in profile["conventions"]} - keys
    assert not missing, missing
    PDF.load(doc)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps(PDF.load(doc).summary(), indent=1))


if __name__ == "__main__":
    main()
