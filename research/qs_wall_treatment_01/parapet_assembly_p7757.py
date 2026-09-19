"""PARAPET ASSEMBLY REGISTER for P7757 (directive §2-§6): what physical
material exists at the roof edges, component by component, face by face,
before any plaster quantity. Reads the frozen A21 traces, the SE native
audit, the DWG roof-edge link register and the structural check. Nothing
here rewrites a frozen output.

    python3 -m research.qs_wall_treatment_01.parapet_assembly_p7757
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shapely.geometry import Polygon

from engine import parapet_assembly as PA
from engine.quantity_state import weakest
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)

# ---- declared correspondences (PROPOSED unless stated) --------------------
DECL = {
    "SE_RUN": {"SW_CORNER_IS_ELEVATION_PIER_END": "the SE elevation's left end (pier SEG-04, x~577) is the "
               "plan's SW rounded corner; the right end (SEG-05, x~1112) is the NE square corner; "
               "supported by the B-B cut (SEC-01 at plan y=750) landing in the lattice zone",
               "LATTICE_PORTION": "CAD line 250 mm inside the outer face (CAD-4808), 3.767 m from the SW corner",
               "SOLID_PORTION": "the rest of the outer face to the NE corner (3.683 m)",
               "STATUS": "PROPOSED_CORRESPONDENCE"},
    "BASE_LINE": {"LEVEL_M": 9.88, "IDENTITY": "drawn level line 0.18 above the +9.70 slab on both the frozen "
                  "raster (UNK-09 at ~+9.90) and the DWG elevation (+9.856/+9.883): ROOF_FINISH_LEVEL_CANDIDATE",
                  "STATUS": "PROPOSED"},
    "SOLID_TOP_M": {"LEVEL_M": 11.10, "SOURCE": "DIM-21 680 from LVL-07 +4.30 (OWNER_ESTABLISHED, termination audit)"},
    "BAND_M": {"THICKNESS": 0.20, "SOURCE": "DIM-20 (OWNER_ESTABLISHED as band thickness)"},
    "SLAB_M": {"LEVEL_M": 9.70, "SOURCE": "LVL-01/LVL-03/LVL-05 + DIM-15 chain (ESTABLISHED)"},
}


def _traces():
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    return {t["TRACE_ID"]: t for t in reg["TRACES"] if t["CASE_ID"] == "CASE-6-ROOF-PARAPET"}


def _poly(t):
    g = t["ORIGINAL_PAGE_GEOMETRY"].get("PIXEL_POLYGON")
    return Polygon(g["COORDINATES"]) if g else None


def _dimline_len(t):
    c = t["ORIGINAL_PAGE_GEOMETRY"]["DIMENSION_LINE_TRACE"]["COORDINATES"]
    return ((c[0][0] - c[1][0]) ** 2 + (c[0][1] - c[1][1]) ** 2) ** 0.5


def _px_per_m(tr, dim_id, value_m):
    return _dimline_len(tr[dim_id]) / value_m


def run() -> dict:
    tr = _traces()
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    se = json.loads((OUT / "SE_ELEVATION_SOURCE_AUDIT.json").read_text("utf-8"))
    # native-scan scales (px per metre) from printed dimension lines, per sheet
    scale = {"SOUTH_EAST_ELEVATION": _px_per_m(tr, "DIM-21", 6.80),
             "SECTION_B_B": _px_per_m(tr, "DIM-09", 4.20),
             "SECTION_A_A": _px_per_m(tr, "DIM-10", 0.50)}
    checks = {"SE_DIM-13_1440": round(_px_per_m(tr, "DIM-13", 14.40), 2), "SE_DIM-15_420": round(_px_per_m(tr, "DIM-15", 4.20), 2)}

    def area_m2(tid):
        p = _poly(tr[tid])
        s = scale[tr[tid]["SHEET_ID"]]
        return (round(p.area / s / s, 4) if p else None)

    def extent_m(tid, axis):
        p = _poly(tr[tid])
        s = scale[tr[tid]["SHEET_ID"]]
        b = p.bounds
        return round(((b[3] - b[1]) if axis == "y" else (b[2] - b[0])) / s, 3)

    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    lat = link["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"]
    corner_arc = lat["CORNER_ARC"][0] if lat["CORNER_ARC"] else None
    kerb_dev = PA.developed_length([{"ID": "CAD-4808", "KIND": "LINE", "length_mm": lat["KERB_ZONE_LINE_LENGTH_M"] * 1000}]
                                   + ([{"ID": corner_arc["ID"], "KIND": "ARC", "radius_mm": corner_arc["RADIUS_MM"],
                                        "sweep_rad": corner_arc["SWEEP_RAD"]}] if corner_arc else []))
    tower = st["TOWER_ROOF_13_90_OUTLINE_p6"]
    ring_thk = {"PAR-08": extent_m("PAR-08", "y"), "PAR-09": extent_m("PAR-09", "y")}
    ring_thk_mean = round(sum(ring_thk.values()) / 2, 3)
    ne_len_outer = 18.27
    ne_len_inner = 18.87
    ne_par_h = extent_m("PAR-07", "x")          # A-A hatched cut: slab top to parapet top
    kerb_h_cut = extent_m("PAR-04", "x")
    SLAB, BASE, TOP, BAND = DECL["SLAB_M"]["LEVEL_M"], DECL["BASE_LINE"]["LEVEL_M"], DECL["SOLID_TOP_M"]["LEVEL_M"], DECL["BAND_M"]["THICKNESS"]
    prov = {"CAD": "ESTABLISHED_FROM_DWG", "CAD_PROPOSED": "PROPOSED_CORRESPONDENCE", "RASTER": "PROVISIONAL",
            "OWNER_EST": "OWNER_ESTABLISHED", "PROV": "PROVISIONAL", "NE": "NOT_ESTABLISHED", "VECTOR": "PROVISIONAL"}
    C = []
    def comp(aid, ctype, **kw):
        base = dict(ASSEMBLY_ID=aid, SHEET_ID=kw.pop("SHEET_ID", "SECOND_FLOOR_ROOF_PLAN"), SOURCE_OBJECT_ID=kw.pop("SOURCE_OBJECT_ID", None),
                    CAD_OBJECT_ID=kw.pop("CAD_OBJECT_ID", None), COMPONENT_TYPE=ctype, GEOMETRY_TYPE=kw.pop("GEOMETRY_TYPE", "LINE"),
                    START_POINT=kw.pop("START_POINT", None), END_POINT=kw.pop("END_POINT", None), LENGTH=kw.pop("LENGTH", None),
                    HEIGHT=kw.pop("HEIGHT", None), THICKNESS=kw.pop("THICKNESS", None), CURVED_OR_STRAIGHT=kw.pop("CURVED_OR_STRAIGHT", "STRAIGHT"),
                    MATERIAL_STATUS=kw.pop("MATERIAL_STATUS", "NOT_ESTABLISHED"),
                    PLASTERABLE_EXTERNAL_FACE_STATUS=kw.pop("EXT", "NOT_ESTABLISHED"), PLASTERABLE_INTERNAL_FACE_STATUS=kw.pop("INT", "NOT_ESTABLISHED"),
                    COPING_STATUS=kw.pop("COPING_STATUS", "NONE"), BALUSTRADE_STATUS=kw.pop("BALUSTRADE_STATUS", "NONE"),
                    HANDRAIL_STATUS=kw.pop("HANDRAIL_STATUS", "NONE"), SOURCE_DIMENSION_IDS=kw.pop("SOURCE_DIMENSION_IDS", []),
                    DIMENSION_OWNER_STATUS=kw.pop("DIMENSION_OWNER_STATUS", {}), SOURCE_CONFIDENCE_STATUS=kw.pop("SOURCE_CONFIDENCE_STATUS", "PROVISIONAL"),
                    OWNER_VERIFICATION_STATUS=kw.pop("OWNER_VERIFICATION_STATUS", "NOT_OWNER_VERIFIED"),
                    QUANTITY_ELIGIBILITY=kw.pop("QUANTITY_ELIGIBILITY", "SEE_FACES"), PROVENANCE=kw.pop("PROVENANCE", {}))
        base.update(kw)
        C.append(PA.component(**base))
        return base

    comp("SE-RE-DATUM", "SLAB_ROOF_DATUM", GEOMETRY_TYPE="LEVEL", SOURCE_OBJECT_ID="LVL-01", HEIGHT=SLAB,
         MATERIAL_STATUS="NOT_A_MATERIAL", EXT="NOT_APPLICABLE", INT="NOT_APPLICABLE",
         SOURCE_DIMENSION_IDS=["LVL-01", "LVL-03", "LVL-05", "DIM-15"], SOURCE_CONFIDENCE_STATUS="ESTABLISHED",
         PROVENANCE={"DWG_LEVEL_CHAIN": "870 from +1.00 -> +9.70 (elevation blob)", "RASTER": "LVL marks"})
    comp("SE-RE-STRUCT", "STRUCTURAL_EDGE", SHEET_ID="ST7757_p5", SOURCE_OBJECT_ID="SECTION B-B (structural)",
         LENGTH=st["SE_ROOF_EDGE_STRUCTURE"]["OUTER_EDGE_LENGTH_M"], HEIGHT=0.20, THICKNESS=0.45,
         MATERIAL_STATUS="SOLID_MASONRY_OR_RC", EXT="NOT_APPLICABLE", INT="NOT_APPLICABLE",
         SOURCE_CONFIDENCE_STATUS="PROPOSED", QUANTITY_ELIGIBILITY="NOT_A_FINISH_ITEM (structure under the parapet)",
         PROVENANCE={"DETAIL": st["SE_ROOF_EDGE_STRUCTURE"]["UPSTAND_DETAIL_SECTION_B_B_p5"],
                     "NOTE": "RC edge beam 45 x 75 with a 20 x 20 upstand; parapet above per architectural detail"})
    comp("SE-RE-SOLID", "SOLID_PARAPET", SOURCE_OBJECT_ID="PAR-12 (elevation) / PAR-01 NE portion (plan)",
         CAD_OBJECT_ID=["CAD-4804", "CAD-4807", "CAD-4741"], START_POINT=[link["SE_ROOF_EDGE_AUTHORED"]["OUTER_FACE"]["X_MM"], sol["Y_FROM_MM"]],
         END_POINT=[link["SE_ROOF_EDGE_AUTHORED"]["OUTER_FACE"]["X_MM"], sol["Y_TO_MM"]],
         LENGTH={"OUTER_FACE_M": sol["OUTER_FACE_LENGTH_M"], "ROOF_SIDE_FACE_M": sol["ROOF_SIDE_FACE_LENGTH_M"],
                 "ELEVATION_RASTER_WIDTH_M": extent_m("PAR-12", "y"), "STATUS": "ESTABLISHED_FROM_DWG length; PROPOSED_CORRESPONDENCE split"},
         HEIGHT={"EXTERNAL_TOP_M": TOP, "EXTERNAL_BOTTOM_PHYSICAL_M": 4.30, "ROOF_SIDE_BOTTOM_PHYSICAL_M": SLAB,
                 "BASE_LINE_M": BASE, "PARAPET_FACE_FROM_SLAB_M": round(TOP - SLAB, 2), "PARAPET_FACE_FROM_BASE_LINE_M": round(TOP - BASE, 2)},
         THICKNESS=0.20, MATERIAL_STATUS="SOLID_PROVISIONAL", EXT="ELIGIBLE_PROVISIONAL", INT="ELIGIBLE_PROVISIONAL",
         COPING_STATUS="CAPPED_BY SE-RE-CAP", SOURCE_DIMENSION_IDS=["DIM-21", "DIM-20", "DIM-01", "LVL-07"],
         DIMENSION_OWNER_STATUS={"DIM-21": "OWNER_ESTABLISHED", "DIM-20": "OWNER_ESTABLISHED", "DIM-01": "OWNER_ESTABLISHED (thickness)"},
         OWNER_VERIFICATION_STATUS="OWNER_VERIFIED_TEXT_EXISTENCE (SE elevation check)",
         PROVENANCE={"PLAN": "DWG roof copy authored lines", "ELEVATION": "frozen A21 PAR-12 + native audit",
                     "STRUCTURE": "RC upstand under it (ST p5); material above per arch. detail (blockwork/RC)"})
    comp("SE-RE-KERB", "SOLID_KERB", SOURCE_OBJECT_ID="PAR-11 (elevation) / PAR-04 (B-B cut) / PAR-01 SW portion",
         CAD_OBJECT_ID=["CAD-4808", "CAD-4804", corner_arc["ID"] if corner_arc else None],
         START_POINT=[link["SE_ROOF_EDGE_AUTHORED"]["OUTER_FACE"]["X_MM"], lat["Y_FROM_MM"]],
         END_POINT=[link["SE_ROOF_EDGE_AUTHORED"]["OUTER_FACE"]["X_MM"], lat["Y_TO_MM"]],
         LENGTH={"KERB_ZONE_LINE_M": lat["KERB_ZONE_LINE_LENGTH_M"], "WITH_SW_CORNER_ARC_DEVELOPED": kerb_dev,
                 "OUTER_FACE_PORTION_M": lat["OUTER_FACE_LENGTH_M"], "ELEVATION_RASTER_WIDTH_M": extent_m("PAR-11", "y")},
         HEIGHT={"AT_B_B_CUT_ABOVE_SLAB_M": kerb_h_cut, "ELEVATION_TOP_PROFILE": "curved (ogee): rises from ~0.19 to ~0.80 above the base line (PAR-11)",
                 "STATUS": "VARIABLE; profile from the frozen trace polygon"},
         THICKNESS={"PLAN_LINES": "outer face, +200, +250 (kerb zone line)", "B_B_CUT_M": extent_m("PAR-04", "y")},
         CURVED_OR_STRAIGHT="STRAIGHT in plan (SW corner arc r=0.23); CURVED top profile in elevation",
         MATERIAL_STATUS="SOLID_MASONRY_OR_RC", EXT="ELIGIBLE_PROVISIONAL", INT="ELIGIBLE_PROVISIONAL",
         BALUSTRADE_STATUS="CARRIES SE-RE-BAL", HANDRAIL_STATUS="CARRIES SE-RE-RAIL",
         SOURCE_DIMENSION_IDS=["DIM-01"], SOURCE_CONFIDENCE_STATUS="PROVISIONAL",
         PROVENANCE={"B_B": "hatched cut masonry PAR-04 0.54 above the slab", "ELEVATION": "PAR-11 polygon", "PLAN": "CAD-4808"})
    comp("SE-RE-BAL", "BALUSTRADE", SOURCE_OBJECT_ID="BAL-03 (elevation) / BAL-02 (B-B)", SHEET_ID="SOUTH_EAST_ELEVATION",
         LENGTH={"PROPOSED_M": lat["KERB_ZONE_LINE_LENGTH_M"], "ELEVATION_RASTER_WIDTH_M": extent_m("BAL-03", "y")},
         HEIGHT={"ASSEMBLY_104_M": 1.04, "NOTE": "DIM-18 rail top -> base line; includes the kerb under it"},
         THICKNESS=0.10, MATERIAL_STATUS="OPEN_METAL", EXT="ZERO_BY_MATERIAL", INT="ZERO_BY_MATERIAL",
         BALUSTRADE_STATUS="OPEN_X_LATTICE", HANDRAIL_STATUS="TOPPED_BY SE-RE-RAIL",
         SOURCE_DIMENSION_IDS=["DIM-18"], DIMENSION_OWNER_STATUS={"DIM-18": "OWNER_ESTABLISHED (assembly, not a face)"},
         QUANTITY_ELIGIBILITY="ZERO_PLASTER (balustrade)", SOURCE_CONFIDENCE_STATUS="ESTABLISHED (material) / PROPOSED (length)")
    comp("SE-RE-RAIL", "HANDRAIL", SOURCE_OBJECT_ID="PAR-13 over the lattice / PAR-05 cap block (B-B)", SHEET_ID="SOUTH_EAST_ELEVATION",
         LENGTH={"PROPOSED_M": lat["KERB_ZONE_LINE_LENGTH_M"]}, HEIGHT=0.16, THICKNESS=0.20,
         MATERIAL_STATUS="NOT_ESTABLISHED", EXT="ZERO_BY_MATERIAL", INT="ZERO_BY_MATERIAL",
         HANDRAIL_STATUS="TOP_RAIL_OVER_LATTICE", QUANTITY_ELIGIBILITY="ZERO_PLASTER (rail)",
         PROVENANCE={"B_B": "PAR-05 20-wide cap block on top of the lattice"})
    comp("SE-RE-CAP", "COPING_CAPPING", SOURCE_OBJECT_ID="PAR-13 over the solid wall", SHEET_ID="SOUTH_EAST_ELEVATION",
         LENGTH={"PROPOSED_M": sol["OUTER_FACE_LENGTH_M"], "ELEVATION_RASTER_WIDTH_M": extent_m("PAR-13", "y")},
         HEIGHT=BAND, THICKNESS=0.20, MATERIAL_STATUS="SOLID_PROVISIONAL",
         EXT="ELIGIBLE_PROVISIONAL", INT="ELIGIBLE_PROVISIONAL", COPING_STATUS="BAND_OVER_SOLID_WALL (separate item, not wall face)",
         SOURCE_DIMENSION_IDS=["DIM-20"], DIMENSION_OWNER_STATUS={"DIM-20": "OWNER_ESTABLISHED"},
         QUANTITY_ELIGIBILITY="COPING item: edge faces 0.20 high + top face 0.20 wide; never added to the wall face height")
    comp("SE-RE-PIER", "SOLID_PARAPET", SOURCE_OBJECT_ID="SEG-04 end pier (SW end)", SHEET_ID="SOUTH_EAST_ELEVATION",
         LENGTH={"ELEVATION_RASTER_WIDTH_M": extent_m("SEG-04", "y")}, HEIGHT={"ELEVATION_RASTER_M": extent_m("SEG-04", "x")},
         MATERIAL_STATUS="SOLID_PROVISIONAL", EXT="ELIGIBLE_PROVISIONAL", INT="NOT_ESTABLISHED",
         QUANTITY_ELIGIBILITY="small; external face polygon only", SOURCE_CONFIDENCE_STATUS="PROVISIONAL")
    comp("SE-RE-FACADE", "FACADE_WALL", SOURCE_OBJECT_ID="SE facade below the roof edge (DIM-21 run)", SHEET_ID="SOUTH_EAST_ELEVATION",
         LENGTH={"SE_RUN_OUTER_M": link["PLAN_RUN_LENGTH"]["OUTER_FACE_M"]}, HEIGHT={"FROM_M": 4.30, "TO_M": SLAB},
         MATERIAL_STATUS="SOLID_PROVISIONAL", EXT="ELIGIBLE_PROVISIONAL", INT="NOT_APPLICABLE",
         SOURCE_DIMENSION_IDS=["DIM-21", "LVL-07"], QUANTITY_ELIGIBILITY="gross only: arched windows below the parapet are not traced (UNRESOLVED openings)",
         PROVENANCE={"NATIVE_EVIDENCE": "decision_cards/se_native/below_parapet_139_windows.png"})
    comp("SE-RE-TOWER", "TOWER_DOME_FEATURE", SOURCE_OBJECT_ID="DIM-16/DIM-17 (155 / 193)", SHEET_ID="SOUTH_EAST_ELEVATION",
         GEOMETRY_TYPE="NONE", MATERIAL_STATUS="NOT_A_MATERIAL", EXT="NOT_APPLICABLE", INT="NOT_APPLICABLE",
         SOURCE_DIMENSION_IDS=["DIM-16", "DIM-17"], DIMENSION_OWNER_STATUS={"DIM-16": "OWNER_ESTABLISHED", "DIM-17": "OWNER_ESTABLISHED"},
         QUANTITY_ELIGIBILITY="NONE (tower top to dome apex, dome apex to rail top: not faces)")
    comp("SE-RE-EXTSKIN", "EXTERNAL_FINISH_FACE", SOURCE_OBJECT_ID="UNK-05 (B-B outer skin)", SHEET_ID="SECTION_B_B",
         GEOMETRY_TYPE="POLYLINE", THICKNESS=0.10, MATERIAL_STATUS="FINISH_LAYER_UNKNOWN", EXT="NOT_ESTABLISHED", INT="NOT_APPLICABLE",
         QUANTITY_ELIGIBILITY="depends on FINISHES_SPECIFICATION (SOURCE_NOT_PROVIDED): plaster vs cladding")
    comp("SE-RE-ROOFSIDE", "INTERNAL_ROOF_SIDE_FACE", SOURCE_OBJECT_ID="roof-side face of SE-RE-SOLID", SHEET_ID="SECOND_FLOOR_ROOF_PLAN",
         CAD_OBJECT_ID=["CAD-4807", "CAD-4741"], LENGTH={"ROOF_SIDE_M": sol["ROOF_SIDE_FACE_LENGTH_M"]},
         HEIGHT={"FROM_SLAB_M": round(TOP - SLAB, 2), "FROM_BASE_LINE_M": round(TOP - BASE, 2)},
         MATERIAL_STATUS="SOLID_PROVISIONAL", EXT="NOT_APPLICABLE", INT="ELIGIBLE_PROVISIONAL",
         QUANTITY_ELIGIBILITY="face-specific; bottom convention queued (D1)")
    comp("TOWER-RING", "SOLID_PARAPET", SOURCE_OBJECT_ID="PAR-08 / PAR-09 (A-A hatched) / PAR-10 (SE) / PAR-06 (B-B)", SHEET_ID="ST7757_p6 + SECTION_A_A",
         GEOMETRY_TYPE="POLYLINE", LENGTH={"SLAB_EDGE_DEVELOPED_M": tower["DEVELOPED_PERIMETER_M"], "RECTANGLE_M": tower["RECTANGLE_PERIMETER_FOR_COMPARISON_M"],
                                            "SOURCE_TIER": "VECTOR_DRAWING_GEOMETRY (ST p6 +13.90 slab outline)", "CORRESPONDENCE": "PROPOSED_CORRESPONDENCE"},
         HEIGHT={"ROOF_SIDE_M": 0.50, "SOURCE": "DIM-10 OWNER_ESTABLISHED (hatched cut)"},
         THICKNESS={"A_A_RASTER_M": ring_thk, "MEAN_M": ring_thk_mean, "STATUS": "PROVISIONAL (raster)"},
         MATERIAL_STATUS="SOLID_MASONRY_OR_RC", EXT="ELIGIBLE_PROVISIONAL", INT="ELIGIBLE_PROVISIONAL",
         SOURCE_DIMENSION_IDS=["DIM-10", "DIM-11", "DIM-14"], DIMENSION_OWNER_STATUS={"DIM-10": "OWNER_ESTABLISHED", "DIM-11": "OWNER_PROVISIONAL", "DIM-14": "OWNER_PROVISIONAL"})
    comp("NE-RE-SOLID", "SOLID_PARAPET", SOURCE_OBJECT_ID="PAR-03 (plan) / PAR-07 (A-A hatched cut)", SHEET_ID="SECOND_FLOOR_ROOF_PLAN",
         CAD_OBJECT_ID=["CAD-4735", "CAD-4741"], LENGTH={"OUTER_M": ne_len_outer, "ROOF_SIDE_M": ne_len_inner, "SOURCE": "DWG authored lines"},
         HEIGHT={"A_A_CUT_ABOVE_SLAB_RASTER_M": ne_par_h, "STATUS": "PROVISIONAL (raster; one cut)"}, THICKNESS=0.20,
         MATERIAL_STATUS="SOLID_MASONRY_OR_RC", EXT="ELIGIBLE_PROVISIONAL", INT="ELIGIBLE_PROVISIONAL",
         SOURCE_DIMENSION_IDS=["DIM-01"], PROVENANCE={"NOTE": "neighbour-side parapet; external face faces the neighbour plot"})
    comp("SW-RE-SOLID", "SOLID_PARAPET", SOURCE_OBJECT_ID="PAR-02 (plan)", SHEET_ID="SECOND_FLOOR_ROOF_PLAN",
         CAD_OBJECT_ID=["CAD-4776", "CAD-4793", "CAD-4805"], LENGTH={"OUTER_M": 4.325, "ROOF_SIDE_M": 4.125, "SOURCE": "DWG authored lines"},
         HEIGHT={"STATUS": "NOT_ESTABLISHED (no section cuts it; no elevation dimension)"}, THICKNESS=0.20,
         MATERIAL_STATUS="SOLID_PROVISIONAL", EXT="NOT_ESTABLISHED", INT="NOT_ESTABLISHED", SOURCE_DIMENSION_IDS=["DIM-05"])
    comp("NW-RE-THIN", "UNKNOWN_COMPONENT", SOURCE_OBJECT_ID="UNK-04 (plan) / DIM-07 130 (B-B)", SHEET_ID="SECOND_FLOOR_ROOF_PLAN",
         THICKNESS=0.10, HEIGHT={"B_B_M": 1.30, "STATUS": "OWNER_PROVISIONAL"}, MATERIAL_STATUS="NOT_ESTABLISHED",
         EXT="NOT_APPLICABLE", INT="NOT_APPLICABLE", SOURCE_DIMENSION_IDS=["DIM-06", "DIM-07"],
         QUANTITY_ELIGIBILITY="NONE until the material of a 10 cm x 1.30 m sea-view edge element is established")

    # ---- faces ------------------------------------------------------------
    F = []
    def face(**kw):
        F.append(PA.face(**kw))
    L_solid_out, L_solid_in = sol["OUTER_FACE_LENGTH_M"], sol["ROOF_SIDE_FACE_LENGTH_M"]
    face(face_id="F-SE-SOLID-EXT", component_id="SE-RE-SOLID", side="EXTERNAL", bottom=SLAB, bottom_source="ESTABLISHED",
         top=TOP, top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_out, length_source="PROPOSED_CORRESPONDENCE",
         notes=["parapet portion of one continuous external face +4.30 -> +11.10; the split at +9.70 is the ENGINEERING measurement convention",
                f"raster polygon PAR-12 (base line -> band underside) = {area_m2('PAR-12')} m2 at {round(scale['SOUTH_EAST_ELEVATION'],1)} px/m"])
    face(face_id="F-SE-SOLID-ROOFSIDE", component_id="SE-RE-ROOFSIDE", side="ROOF_SIDE", bottom=SLAB, bottom_source="ESTABLISHED",
         top=TOP, top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_in, length_source="PROPOSED_CORRESPONDENCE",
         notes=["bottom at the structural slab (physical); alternative bottom at the drawn base line +9.88 (finish level candidate) queued as D1"])
    face(face_id="F-SE-SOLID-ROOFSIDE-ALT-BASELINE", component_id="SE-RE-ROOFSIDE", side="ROOF_SIDE", bottom=BASE, bottom_source="PROVISIONAL",
         top=TOP, top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_in, length_source="PROPOSED_CORRESPONDENCE", notes=["D1 option B (measured from the finish level line)"])
    face(face_id="F-SE-FACADE-EXT", component_id="SE-RE-FACADE", side="EXTERNAL", bottom=4.30, bottom_source="ESTABLISHED",
         top=SLAB, top_source="ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=link["PLAN_RUN_LENGTH"]["OUTER_FACE_M"], length_source="ESTABLISHED_FROM_DWG",
         notes=["gross only; openings below the parapet (arched windows) UNRESOLVED -> net NOT_ESTABLISHED", "NET_STATE: NOT_ESTABLISHED"])
    face(face_id="F-SE-KERB-EXT", component_id="SE-RE-KERB", side="EXTERNAL", bottom=BASE, bottom_source="PROVISIONAL",
         top="CURVED_PROFILE", top_source="PROVISIONAL", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=lat["KERB_ZONE_LINE_LENGTH_M"], length_source="PROPOSED_CORRESPONDENCE",
         area_from_polygon_m2=area_m2("PAR-11"), polygon_source="PROVISIONAL",
         notes=[f"area from the frozen PAR-11 polygon (raster tier); elevation width {extent_m('PAR-11', 'y')} m vs plan kerb line {lat['KERB_ZONE_LINE_LENGTH_M']} m"])
    face(face_id="F-SE-KERB-ROOFSIDE", component_id="SE-RE-KERB", side="ROOF_SIDE", bottom=SLAB, bottom_source="ESTABLISHED",
         top="CURVED_PROFILE", top_source="PROVISIONAL", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=lat["KERB_ZONE_LINE_LENGTH_M"], length_source="PROPOSED_CORRESPONDENCE",
         area_from_polygon_m2=round(area_m2("PAR-11") + (BASE - SLAB) * lat["KERB_ZONE_LINE_LENGTH_M"], 4), polygon_source="PROVISIONAL",
         notes=["external polygon area + (base line - slab) x length: the roof-side face starts at the slab"])
    face(face_id="F-SE-CAP-EDGE-EXT", component_id="SE-RE-CAP", side="EXTERNAL", bottom=TOP, bottom_source="OWNER_ESTABLISHED",
         top=round(TOP + BAND, 2), top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_out, length_source="PROPOSED_CORRESPONDENCE", notes=["coping edge face; separate COPING item"])
    face(face_id="F-SE-CAP-EDGE-ROOFSIDE", component_id="SE-RE-CAP", side="ROOF_SIDE", bottom=TOP, bottom_source="OWNER_ESTABLISHED",
         top=round(TOP + BAND, 2), top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_in, length_source="PROPOSED_CORRESPONDENCE", notes=["coping edge face; separate COPING item"])
    face(face_id="F-SE-CAP-TOP", component_id="SE-RE-CAP", side="TOP", bottom=0.0, bottom_source="OWNER_ESTABLISHED", top=0.20,
         top_source="OWNER_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=L_solid_out, length_source="PROPOSED_CORRESPONDENCE", notes=["top face 0.20 wide (wall thickness DIM-01); 'height' here is the width"])
    face(face_id="F-SE-BAL", component_id="SE-RE-BAL", side="EXTERNAL", bottom=None, bottom_source="NOT_ESTABLISHED", top=None,
         top_source="NOT_ESTABLISHED", material="OPEN_METAL", eligibility="ZERO_BY_MATERIAL",
         length_m=lat["KERB_ZONE_LINE_LENGTH_M"], length_source="PROPOSED_CORRESPONDENCE", notes=["balustrade: zero plaster by construction"])
    face(face_id="F-SE-RAIL", component_id="SE-RE-RAIL", side="TOP", bottom=None, bottom_source="NOT_ESTABLISHED", top=None,
         top_source="NOT_ESTABLISHED", material="NOT_ESTABLISHED", eligibility="ZERO_BY_MATERIAL",
         length_m=lat["KERB_ZONE_LINE_LENGTH_M"], length_source="PROPOSED_CORRESPONDENCE", notes=["handrail: zero plaster by construction"])
    face(face_id="F-SE-PIER-EXT", component_id="SE-RE-PIER", side="EXTERNAL", bottom=BASE, bottom_source="PROVISIONAL", top="ROUNDED",
         top_source="PROVISIONAL", material="SOLID_PROVISIONAL", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=extent_m("SEG-04", "y"), length_source="PROVISIONAL", area_from_polygon_m2=area_m2("SEG-04"), polygon_source="PROVISIONAL",
         notes=["area from the SEG-04 polygon (raster)"])
    face(face_id="F-TOWER-RING-ROOFSIDE", component_id="TOWER-RING", side="ROOF_SIDE", bottom=13.90, bottom_source="ESTABLISHED",
         top=14.40, top_source="OWNER_ESTABLISHED", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=round(tower["DEVELOPED_PERIMETER_M"] - 8 * ring_thk_mean, 3), length_source="PROVISIONAL",
         notes=["slab-edge ring (ST p6 exterior ring) minus 8 x mean raster thickness at the corners; correspondence PROPOSED"])
    face(face_id="F-TOWER-RING-EXT", component_id="TOWER-RING", side="EXTERNAL", bottom=13.90, bottom_source="PROVISIONAL",
         top=14.40, top_source="OWNER_ESTABLISHED", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=tower["DEVELOPED_PERIMETER_M"], length_source="PROVISIONAL",
         notes=["the external face is continuous with the tower wall below; the +13.90 split is the ENGINEERING convention (DIM-14 chain link, OWNER_PROVISIONAL)"])
    face(face_id="F-NE-SOLID-ROOFSIDE", component_id="NE-RE-SOLID", side="ROOF_SIDE", bottom=SLAB, bottom_source="ESTABLISHED",
         top=round(SLAB + ne_par_h, 3), top_source="PROVISIONAL", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE_PROVISIONAL",
         length_m=ne_len_inner, length_source="ESTABLISHED_FROM_DWG", notes=["height from the A-A hatched cut (raster); one cut for an 18.9 m run -> PROVISIONAL"])
    face(face_id="F-NE-SOLID-EXT", component_id="NE-RE-SOLID", side="EXTERNAL", bottom=SLAB, bottom_source="ESTABLISHED",
         top=round(SLAB + ne_par_h, 3), top_source="PROVISIONAL", material="SOLID_MASONRY_OR_RC", eligibility="NOT_ESTABLISHED",
         length_m=ne_len_outer, length_source="ESTABLISHED_FROM_DWG", notes=["neighbour side; whether the external face is finished is NOT_ESTABLISHED (boundary wall condition) -> queued",
                                                                             f"gross for reference: {round(ne_len_outer * ne_par_h, 3)} m2"])
    face(face_id="F-SW-SOLID-ROOFSIDE", component_id="SW-RE-SOLID", side="ROOF_SIDE", bottom=SLAB, bottom_source="ESTABLISHED", top=None,
         top_source="NOT_ESTABLISHED", material="SOLID_PROVISIONAL", eligibility="NOT_ESTABLISHED", length_m=4.125,
         length_source="ESTABLISHED_FROM_DWG", notes=["no section cuts the SW parapet; height NOT_ESTABLISHED"])
    for f in F:
        f["AREA"] = PA.face_area(f)

    # ---- D1 source matrix (first principles) --------------------------------
    matrix = []
    def row(comp_, plan, elev, sec, cad, dim, owner, status):
        matrix.append({"PHYSICAL_COMPONENT": comp_, "PLAN_SOURCE": plan, "ELEVATION_SOURCE": elev, "SECTION_SOURCE": sec,
                       "CAD_SOURCE": cad, "DIMENSION_SOURCE": dim, "OWNER_VERIFIED_SOURCE": owner, "STATUS": status})
    row("slab / roof datum +9.70", "LVL-01/02", "DIM-15 chain", "LVL-03 / LVL-05", "DWG level chain 870", "DIM-15, DIM-09", "-", "ESTABLISHED")
    row("solid parapet (NE portion)", "PAR-01 NE part", "PAR-12", "none cuts it", "CAD-4804/4807 + split line CAD-4808", "DIM-21 (top), DIM-01 (thk)", "SE check: 680/20 text", "LENGTH ESTABLISHED_FROM_DWG; SPLIT PROPOSED; HEIGHT ESTABLISHED")
    row("solid kerb under the lattice", "PAR-01 SW part / UNK-01", "PAR-11", "PAR-04 hatched 0.54", "CAD-4808 (3.767)", "none printed", "-", "PROVISIONAL (variable profile)")
    row("curved upstand (ogee)", "-", "PAR-11 top edge", "PAR-04 rounded outer edge", "-", "none", "-", "PROVISIONAL")
    row("balustrade / lattice", "-", "BAL-03", "BAL-02", "-", "DIM-18 (assembly 104)", "104 established as text", "ESTABLISHED zero plaster")
    row("handrail / cap", "-", "PAR-13 over lattice", "PAR-05", "-", "-", "-", "PROVISIONAL zero plaster")
    row("coping / band over solid", "-", "PAR-13 over solid", "-", "-", "DIM-20 (20)", "20 established", "PROVISIONAL separate item")
    row("tower / dome feature", "-", "DIM-16/17", "-", "DWG dome circles", "155 / 193", "155 established", "NOT A FACE")
    row("facade wall below", "-", "DIM-21 run, windows", "-", "CAD outer 7.50", "DIM-21, LVL-07", "-", "GROSS PROVISIONAL; openings UNRESOLVED")
    row("external finish face", "-", "-", "UNK-05 outer skin", "-", "-", "-", "NOT_ESTABLISHED (finishes spec not provided)")
    row("internal roof-side face", "PAR-01 inner line", "-", "PAR-04 (kerb only)", "CAD-4807 / CAD-4741", "-", "-", "PROVISIONAL; bottom convention D1")
    row("structural edge", "-", "-", "ST p5 SECTION B-B 45x75 + 20 upstand", "ST p5/p6 outline 7.497", "-", "-", "PROPOSED")
    d1 = {
        "D1_STATUS": "REDUCED_TO_A_FACE_BOTTOM_CONVENTION",
        "WHAT_IS_NOW_ESTABLISHED": ["solid portion length from the DWG (3.683 outer / 3.483 roof-side) with a PROPOSED split",
                                    "external face top +11.10 (DIM-21), band 0.20 (DIM-20), slab +9.70",
                                    "the drawn base line is a level line 0.18 above the slab on both the raster and the DWG elevation",
                                    "the structural edge is an RC beam with a 20 cm upstand; the parapet above is per architectural detail"],
        "EXACT_MISSING_RELATIONSHIP": "whether the roof-side plaster face is measured from the structural slab (+9.70, physical face, "
                                      "1.40) or from the finished roof level line (+9.88, 1.22): a measurement convention, not a drawing fact; "
                                      "and the kerb top profile as an authored curve (raster polygon only)",
        "QUANTITY_IMPACT_M2": {"ROOF_SIDE_A_MINUS_B": round((TOP - SLAB - (TOP - BASE)) * L_solid_in, 3),
                               "PER_METRE_RUN": round(BASE - SLAB, 2)},
        "TECHNICAL_DEFAULT": "A: physical face from the slab (+9.70), 1.40 m; plaster precedes roof finishes",
        "OWNER_DECISION_QUEUED": "D1-SE-ROOFSIDE-BOTTOM (small, does not block)",
    }
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "PARAPET_ASSEMBLY_REGISTER", "DECLARED_CORRESPONDENCES": DECL,
           "NATIVE_SCALE_PX_PER_M": {k: round(v, 2) for k, v in scale.items()}, "SCALE_CROSS_CHECKS": checks,
           "COMPONENT_TYPES": PA.COMPONENT_TYPES, "COMPONENTS": C, "D1_SOURCE_MATRIX": matrix, "D1": d1,
           "INPUTS": {"LINK_REGISTER": "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json", "STRUCTURAL": "STRUCTURAL_SOURCE_CHECK.json",
                      "SE_AUDIT": "SE_ELEVATION_SOURCE_AUDIT.json", "TRACES": P.TRACE_REGISTER},
           "FROZEN_OUTPUTS_REWRITTEN": False}
    p = OUT / "PARAPET_ASSEMBLY_REGISTER.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    fm = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "FACE_MEASUREMENT_REGISTER", "FACES": F,
          "RULE": "GROSS = face length x face height per physical face; balustrade / handrail faces are zero; a coping is its own item",
          "LAYER": "PHYSICAL_GEOMETRY -> face areas (gross); deductions and net in the TRADE_QUANTITY layer"}
    q = OUT / "FACE_MEASUREMENT_REGISTER.json"
    q.write_text(json.dumps(fm, indent=2, default=str) + "\n", encoding="utf-8")
    return {"COMPONENTS": len(C), "FACES": len(F), "D1": d1,
            "FACES_SUMMARY": [(f["FACE_ID"], f["FACE_HEIGHT"], f["FACE_LENGTH_M"], f["AREA"]["GROSS_AREA_M2"], f["AREA"]["QUANTITY_STATE"]) for f in F],
            "SHA": {"ASSEMBLY": hashlib.sha256(p.read_bytes()).hexdigest()[:16], "FACES": hashlib.sha256(q.read_bytes()).hexdigest()[:16]}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
