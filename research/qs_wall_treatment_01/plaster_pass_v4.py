"""PLASTER CATEGORY PASS v4 (directive §10, §17, §18): every condition
processed independently on eligible physical face sets; partial
quantities with truthful unresolved scope; one quantity state per line;
totals per unit and per state, never across units.

    python3 -m research.qs_wall_treatment_01.plaster_pass_v4
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.quantity_state import totals_by_unit, weakest
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.owner_parameters import p7757_registry

OUT = Path(P.OUT_DIR)
CATEGORIES = ("NORMAL_INTERNAL_WALL", "WET_ROOM_WALL", "DOUBLE_HEIGHT_WALL", "STAIR_WALL", "EXTERNAL_FACADE",
              "SOLID_PARAPET", "ROOF_SIDE_PARAPET", "COLUMN_BONDING", "DOOR_REVEAL", "WINDOW_REVEAL", "CURVED_WALL")
V3_TRADE_TO_CATEGORY = {"NORMAL_INTERNAL_PLASTER": "NORMAL_INTERNAL_WALL", "COLUMN_BONDING_PLUS_PLASTER": "COLUMN_BONDING",
                        "DOUBLE_HEIGHT_PLASTER": "DOUBLE_HEIGHT_WALL", "STAIR_WELL_PLASTER": "STAIR_WALL",
                        "EXTERNAL_PLASTER": "EXTERNAL_FACADE", "ROOF_PARAPET_PLASTER": "SOLID_PARAPET",
                        "PARAPET_CAPPING": "SOLID_PARAPET"}
FACE_TO_CATEGORY = {"F-SE-SOLID-EXT": "SOLID_PARAPET", "F-SE-SOLID-ROOFSIDE": "ROOF_SIDE_PARAPET",
                    "F-SE-KERB-EXT": "SOLID_PARAPET", "F-SE-KERB-ROOFSIDE": "ROOF_SIDE_PARAPET",
                    "F-SE-PIER-EXT": "SOLID_PARAPET", "F-TOWER-RING-ROOFSIDE": "ROOF_SIDE_PARAPET",
                    "F-TOWER-RING-EXT": "SOLID_PARAPET", "F-NE-SOLID-ROOFSIDE": "ROOF_SIDE_PARAPET",
                    "F-NE-SOLID-EXT": "SOLID_PARAPET", "F-SW-SOLID-ROOFSIDE": "ROOF_SIDE_PARAPET",
                    "F-SE-FACADE-EXT": "EXTERNAL_FACADE"}
COPING_FACES = ("F-SE-CAP-EDGE-EXT", "F-SE-CAP-EDGE-ROOFSIDE", "F-SE-CAP-TOP", "F-NE-CAP-TOP", "F-NE-CAP-EDGE-ROOFSIDE")
ALT_FACES = ("F-SE-SOLID-ROOFSIDE-ALT-BASELINE",)


def _v3_state(bucket, face):
    src = face.get("length_source")
    if bucket == "ESTABLISHED":
        return "OWNER_PARAMETRIC_QUANTITY"       # every v3 established line uses the owner 3.20 height
    if bucket == "PROVISIONAL":
        return "PROVISIONAL_QUANTITY"
    return "NOT_ESTABLISHED"


def run() -> dict:
    v3 = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v3.json").read_text("utf-8"))
    faces = json.loads((OUT / "FACE_MEASUREMENT_REGISTER.json").read_text("utf-8"))["FACES"]
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    asm = json.loads((OUT / "PARAPET_ASSEMBLY_REGISTER.json").read_text("utf-8"))
    curves = json.loads((OUT / "CAD_CURVE_REGISTER.json").read_text("utf-8")) if (OUT / "CAD_CURVE_REGISTER.json").exists() else {}
    reg = p7757_registry()
    h_norm = reg["NORMAL_INTERNAL_PLASTER_HEIGHT"]["VALUE"] if isinstance(reg["NORMAL_INTERNAL_PLASTER_HEIGHT"], dict) else reg["NORMAL_INTERNAL_PLASTER_HEIGHT"]
    lines, unresolved = [], []
    # ---- v3 lines carried forward (frozen v3 untouched) ------------------
    superseded_sets = {"ROOF-SE-PARAPET-CAPPING": "superseded by the assembly coping faces (F-SE-CAP-*): the band runs over the solid portion only"}
    for s in v3["SETS"]:
        plan, fs, res = s["PLAN"], s["FACE_SET"], s.get("RESULT") or s.get("CALCULATION") or {}
        if plan["SET_ID"] in superseded_sets:
            unresolved.append({"CATEGORY": "SOLID_PARAPET", "SET_ID": plan["SET_ID"], "FACE_ID": "*", "WHY": "v3 line SUPERSEDED: " + superseded_sets[plan["SET_ID"]]})
            continue
        cat = V3_TRADE_TO_CATEGORY.get(plan["TRADE"], plan["TRADE"])
        for bucket in ("ESTABLISHED_FACES", "PROVISIONAL_FACES"):
            for f in fs.get(bucket, []):
                L = f.get("length_m")
                if L is None:
                    continue
                area = round(L * h_norm, 4) if plan.get("HEIGHT_PARAMETER") == "NORMAL_INTERNAL_PLASTER_HEIGHT" or cat in ("NORMAL_INTERNAL_WALL", "COLUMN_BONDING") else None
                if f.get("MATERIAL_ROLE") == "CAPPING_BAND":
                    area = round(L * (f.get("width_m") or 0.20), 4)
                    cat = "SOLID_PARAPET"
                if area is None:
                    unresolved.append({"CATEGORY": cat, "SET_ID": plan["SET_ID"], "FACE_ID": f["FACE_ID"], "WHY": "height parameter not applicable / unknown for this category"})
                    continue
                lines.append({"LINE_ID": f"V3:{plan['SET_ID']}:{f['FACE_ID']}", "CATEGORY": cat, "SOURCE_ESTIMATE": "v3",
                              "FLOOR": plan["FLOOR"], "ZONE": plan["ZONE"], "FACE_ID": f["FACE_ID"], "LENGTH_M": L,
                              "HEIGHT_M": (h_norm if area and f.get("MATERIAL_ROLE") != "CAPPING_BAND" else None),
                              "GROSS_AREA_M2": area, "OPENINGS": "per v3 set (full deduction, reveals separate)",
                              "UNIT": "m2", "VALUE": area, "QUANTITY_STATE": _v3_state(bucket.split("_")[0], f),
                              "PROVENANCE": {"length_source": f.get("length_source"), "height": "NORMAL_INTERNAL_PLASTER_HEIGHT (OWNER_PROJECT_INPUT)"}})
        for u in (fs.get("UNRESOLVED_FACES") or []):
            unresolved.append({"CATEGORY": cat, "SET_ID": plan["SET_ID"], "FACE_ID": u.get("FACE_ID"), "WHY": u.get("WHY")})
    # v3 project-level deductions / reveals (kept as the v3 net; see QS_TRACE_v3)
    ag = v3["AGGREGATES"]["PROJECT"]
    # ---- roof-edge faces from the assembly register ------------------------
    for f in faces:
        fid = f["FACE_ID"]
        a = f["AREA"]
        if fid in ALT_FACES:
            continue
        cat = "SOLID_PARAPET" if fid in COPING_FACES else FACE_TO_CATEGORY.get(fid)
        if cat is None:
            continue
        item = {"LINE_ID": f"FACE:{fid}", "CATEGORY": cat, "SOURCE_ESTIMATE": "v4 assembly", "FLOOR": "ROOF", "ZONE": f["COMPONENT_ID"],
                "FACE_ID": fid, "FACE_SIDE": f["FACE_SIDE"], "LENGTH_M": f["FACE_LENGTH_M"], "HEIGHT_M": f["FACE_HEIGHT"],
                "GROSS_AREA_M2": a["GROSS_AREA_M2"], "UNIT": "m2", "VALUE": a["GROSS_AREA_M2"], "QUANTITY_STATE": a["QUANTITY_STATE"],
                "ITEM_KIND": ("COPING" if fid in COPING_FACES else "BALUSTRADE_ZERO" if fid in ("F-SE-BAL", "F-SE-RAIL") else "FACE"),
                "PROVENANCE": {"bottom": f["FACE_BOTTOM_SOURCE"], "top": f["FACE_TOP_SOURCE"], "length": f["FACE_LENGTH_SOURCE"], "notes": f["NOTES"]}}
        if fid == "F-SE-FACADE-EXT":
            item["NET_STATE"] = "NOT_ESTABLISHED"
            item["QUANTITY_STATE"] = "NOT_ESTABLISHED"
            item["VALUE"] = None
            item["WHY"] = "gross face only; the arched windows below the parapet are not traced (openings UNRESOLVED)"
            unresolved.append({"CATEGORY": cat, "FACE_ID": fid, "WHY": item["WHY"], "GROSS_M2_FOR_REFERENCE": a["GROSS_AREA_M2"]})
        if a["GROSS_AREA_M2"] is None:
            unresolved.append({"CATEGORY": cat, "FACE_ID": fid, "WHY": a["WHY"], "REFERENCE_GROSS_M2_IF_ELIGIBLE": a.get("REFERENCE_GROSS_M2_IF_ELIGIBLE")})
            item["VALUE"] = None
            item["QUANTITY_STATE"] = "NOT_ESTABLISHED"
        lines.append(item)
    # ---- D2 column (structural check) ------------------------------------
    d2 = st["D2"]
    girth = d2["COLUMN_EXPOSED_TO_ROOM"]["GIRTH_LM_STRUCTURAL"]
    girth_alt = d2["COLUMN_EXPOSED_TO_ROOM"]["GIRTH_LM_ARCHITECTURAL_LOOP"]
    lines.append({"LINE_ID": "D2:COLUMN:LOOP-059", "CATEGORY": "COLUMN_BONDING", "SOURCE_ESTIMATE": "v4 structural", "FLOOR": "GROUND",
                  "ZONE": "SALOON/RECEPTION open edge", "FACE_ID": "LOOP-059 x 4 faces", "LENGTH_M": girth, "HEIGHT_M": h_norm,
                  "GROSS_AREA_M2": round(girth * h_norm, 4), "UNIT": "m2", "VALUE": round(girth * h_norm, 4),
                  "QUANTITY_STATE": weakest(["PROVISIONAL", "OWNER_PROJECT_INPUT"]),
                  "ALTERNATIVE_GIRTH_LM": girth_alt, "ALTERNATIVE_AREA_M2": round(girth_alt * h_norm, 4),
                  "PROVENANCE": {"exists": d2["COLUMN_EXISTS"]["STATUS"], "exposed": d2["COLUMN_EXPOSED_TO_ROOM"]["STATUS"],
                                 "height": "NORMAL_INTERNAL_PLASTER_HEIGHT to the GF ceiling beam over the column (ST p4)",
                                 "why_provisional": "girth 1.80 (structural 30x60) vs 1.70 (architectural loop 25x60) unresolved; GF storey only"}})
    lines.append({"LINE_ID": "D2:COLUMN:LOOP-059:girth", "CATEGORY": "COLUMN_BONDING", "SOURCE_ESTIMATE": "v4 structural", "FLOOR": "GROUND",
                  "ZONE": "SALOON/RECEPTION open edge", "FACE_ID": "LOOP-059", "UNIT": "lm", "VALUE": girth, "QUANTITY_STATE": "PROVISIONAL_QUANTITY",
                  "PROVENANCE": {"what": "exposed column girth, structural section 30 x 60"}})
    # ---- categories with nothing established ------------------------------
    for cat, why in (("WET_ROOM_WALL", "no wet-room face traced in the frozen register (scope not started)"),
                     ("DOUBLE_HEIGHT_WALL", "GF-RECEPTION-DOUBLE-HEIGHT set exists; DOUBLE_HEIGHT_PLASTER_HEIGHT is UNKNOWN (sections A-A/B-B not yet traced for it)"),
                     ("STAIR_WALL", "stair-wall sets exist; STAIR_WELL_PLASTER_HEIGHT UNKNOWN; 12.90 site record not adopted (§136)"),
                     ("CURVED_WALL", f"{len((curves or {}).get('CURVES', []))} authored curves in the CAD curve register, none semantically linked to a plaster face")):
        unresolved.append({"CATEGORY": cat, "FACE_ID": "*", "WHY": why})
    # reveals: v3 keeps them as separate lines in QS_TRACE_v3; carried by reference
    for cat in ("DOOR_REVEAL", "WINDOW_REVEAL"):
        unresolved.append({"CATEGORY": cat, "FACE_ID": "*", "WHY": "reveal lines live in estimate v3 (REVEALS with actual depth or default); "
                                                                   "no opening height is source-established -> PROVISIONAL_DEFAULT at best"})
    by_cat = {}
    for c in CATEGORIES:
        cl = [l for l in lines if l["CATEGORY"] == c]
        by_cat[c] = {"LINES": [l["LINE_ID"] for l in cl], "TOTALS_BY_UNIT_AND_STATE": totals_by_unit(cl),
                     "UNRESOLVED_SCOPE": [u for u in unresolved if u["CATEGORY"] == c],
                     "COVERAGE_STATUS": ("NONE" if not cl else "PARTIAL"), "COMPLETE_TOTAL_STATUS": "NOT_ESTABLISHED"}
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "PLASTER_QUANTITY_TRACE", "ESTIMATE_VERSION": "v4",
           "RULE": "GROSS = sum(plasterable physical face length x applicable face height); never room perimeter x height",
           "HEIGHT_PARAMETER": {"NORMAL_INTERNAL_PLASTER_HEIGHT": h_norm, "STATUS": "OWNER_PROJECT_INPUT", "SCOPE": "normal rooms only"},
           "LINES": lines, "BY_CATEGORY": by_cat, "UNRESOLVED_SCOPE": unresolved,
           "PROJECT_TOTALS_BY_UNIT_AND_STATE": totals_by_unit(lines),
           "V3_PROJECT_REFERENCE": ag, "D1_ALTERNATIVE_FACE": [f for f in faces if f["FACE_ID"] in ALT_FACES],
           "NOT_A_BOQ": True, "NO_FIREBASE_WRITE": True, "BENCHMARK_USED_IN_GEOMETRY": False,
           "COMPLETE_TOTAL_STATUS": "NOT_ESTABLISHED (traced subset; partial quantities only)"}
    p = OUT / "PLASTER_QUANTITY_TRACE.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    est = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "P7757_WALL_TREATMENT_ESTIMATE", "VERSION": "v4",
           "BUILT_ON": {"v3": "P7757_WALL_TREATMENT_ESTIMATE_v3.json (frozen, carried)", "assembly": "PARAPET_ASSEMBLY_REGISTER.json",
                        "faces": "FACE_MEASUREMENT_REGISTER.json", "structural": "STRUCTURAL_SOURCE_CHECK.json"},
           "BY_CATEGORY": {c: by_cat[c]["TOTALS_BY_UNIT_AND_STATE"] for c in CATEGORIES},
           "PROJECT_TOTALS_BY_UNIT_AND_STATE": out["PROJECT_TOTALS_BY_UNIT_AND_STATE"],
           "COMPLETE_TOTAL_STATUS": "NOT_ESTABLISHED", "NOT_A_BOQ": True, "NO_FIREBASE_WRITE": True,
           "TRACE": "PLASTER_QUANTITY_TRACE.json"}
    q = OUT / "P7757_WALL_TREATMENT_ESTIMATE_v4.json"
    q.write_text(json.dumps(est, indent=2, default=str) + "\n", encoding="utf-8")
    return {"LINES": len(lines), "TOTALS": out["PROJECT_TOTALS_BY_UNIT_AND_STATE"],
            "BY_CATEGORY": {c: by_cat[c]["TOTALS_BY_UNIT_AND_STATE"] for c in CATEGORIES},
            "SHA": {"TRACE": hashlib.sha256(p.read_bytes()).hexdigest()[:16], "EST": hashlib.sha256(q.read_bytes()).hexdigest()[:16]}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
