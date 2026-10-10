"""PA03 - forward source-review / correction layer over PA02 (no historical
freeze is rewritten).  Order (directive §21): A void reconciliation, B
reception vertical faces, C double-height status, D the 10 cm stair
element, E stair face sets, F the D2 column exposed height; plus the NE
elevation eligibility register, the SE opening dimension-ownership audit
and the PA02 supersession ledger.

Every geometric fact below is read from the DWG by entity id and checked
against the stated value (the run fails if the drawing does not say it);
the section / raster reads are labelled as such.

    python3 -m research.qs_wall_treatment_01.pa03_source_review
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pymupdf

from engine import cad_adapter as CA
from engine import source_review as SR
from engine.parapet_assembly import developed_length
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.structural_check import ST_PDF

OUT = Path(P.OUT_DIR)
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
GF2FF = -44852.65
ROOF2GF = 89705.3
LEVELS = {"GF_FFL": 1.00, "FF_SLAB": 5.50, "ROOF_SLAB": 9.70, "TOWER_SLAB": 13.90, "STAIR_FOOT": 0.30}
DATE = "2026-09-20"


# ------------------------------------------------------------------ CAD access
def _norm():
    return CA.normalize(json.loads(Path(DECODE).read_text("utf-8")), source_file="P7757_ARCHITECTURAL.dwg")


def _index(n):
    segs, arcs = {}, {}
    for p in n.primitives:
        if p.kind == "SEGMENT":
            segs[p.object_id] = p
        elif p.kind == "ARC":
            arcs[p.object_id] = p
    return segs, arcs


def _seg(segs, oid, *, x=None, y=None, layer=None, span=None, tol=1.5):
    """Fetch a segment by id and assert what the drawing says about it."""
    s = segs[oid]
    rec = {"ID": oid, "LAYER": s.provenance.layer, "A": [round(s.x1, 1), round(s.y1, 1)], "B": [round(s.x2, 1), round(s.y2, 1)],
           "LENGTH_MM": round(math.hypot(s.x2 - s.x1, s.y2 - s.y1), 1)}
    if layer is not None and s.provenance.layer != layer:
        raise SystemExit(f"{oid}: layer {s.provenance.layer} != {layer}")
    if x is not None and (abs(s.x1 - x) > tol or abs(s.x2 - x) > tol):
        raise SystemExit(f"{oid}: not vertical at x={x}")
    if y is not None and (abs(s.y1 - y) > tol or abs(s.y2 - y) > tol):
        raise SystemExit(f"{oid}: not horizontal at y={y}")
    if span is not None:
        lo, hi = span
        vertical = abs(s.x1 - s.x2) < tol
        got = sorted([s.y1, s.y2] if vertical else [s.x1, s.x2])
        if abs(got[0] - lo) > tol or abs(got[1] - hi) > tol:
            raise SystemExit(f"{oid}: span {got} != {span}")
    return rec


def _dim(n, value, near, tol_mm=400):
    """An authored DWG dimension by display value near a point (its origins)."""
    for d in n.dimensions:
        if abs(d.display_value - value) < 0.05 and (math.hypot(d.x1 - near[0], d.y1 - near[1]) < tol_mm or math.hypot(d.x2 - near[0], d.y2 - near[1]) < tol_mm):
            return {"DISPLAY_VALUE": d.display_value, "GEOMETRY_MM": round(d.geometry_mm, 1), "TEXT_OVERRIDDEN": bool(d.user_text),
                    "FROM": [round(d.x1, 1), round(d.y1, 1)], "TO": [round(d.x2, 1), round(d.y2, 1)], "LAYER": d.provenance.layer,
                    "HANDLE": d.provenance.handle}
    raise SystemExit(f"dimension {value} near {near} not found")


def _struct_p4(box):
    """Structural GF-roof-slab plan (p4) lines inside a CAD box, via the frozen registration."""
    reg = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))["REGISTRATION_p1"]
    S, a, b = reg["SCALE_MM_PER_PT"], reg["A_MM"], reg["B_MM"]
    cad = lambda x, y: (a + S * y, b + S * x)
    doc = pymupdf.open(str(ST_PDF))
    pg = doc[3]
    X0, Y0, X1, Y1 = box
    out = []
    for d in pg.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            c1, c2 = cad(it[1].x, it[1].y), cad(it[2].x, it[2].y)
            if X0 <= min(c1[0], c2[0]) and max(c1[0], c2[0]) <= X1 and Y0 <= min(c1[1], c2[1]) and max(c1[1], c2[1]) <= Y1:
                L = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
                if L > 700:
                    out.append({"FROM": [round(c1[0]), round(c1[1])], "TO": [round(c2[0]), round(c2[1])], "LENGTH_MM": round(L), "WIDTH_PT": round(d.get("width") or 0, 2)})
    return out


# ------------------------------------------------------------------ A. void reconciliation
def void_reconciliation(n, segs, arcs):
    d587 = _dim(n, 587.0, (-186093, -799929))
    d400a = _dim(n, 400.0, (-185623, -799594))
    d400b = _dim(n, 400.0, (-183133, -799594))
    top = _seg(segs, "CAD-2932", y=-799593.5, layer="5", span=(-186092.5, -180222.5))
    top2 = [_seg(segs, "CAD-2935.57d729d2", y=-799643.5, layer="5"), _seg(segs, "CAD-2935.0d614e65", y=-799643.5, layer="5")]
    east = [_seg(segs, "CAD-2933", x=-180222.5, layer="5", span=(-802443.5, -799593.5)), _seg(segs, "CAD-2935.e1df2cee", x=-180272.5, layer="5", span=(-802393.5, -799643.5))]
    south = [_seg(segs, "CAD-2934", y=-802443.5, layer="5"), _seg(segs, "CAD-2935.bb96ea7f", y=-802393.5, layer="5")]
    diag = [_seg(segs, "CAD-2936", layer="5"), _seg(segs, "CAD-2937", layer="5")]
    xs = sorted({v[0] for s in diag for v in (s["A"], s["B"])})
    ys = sorted({v[1] for s in diag for v in (s["A"], s["B"])})
    x_w, x_d = round((xs[-1] - xs[0]) / 1000, 3), round((ys[-1] - ys[0]) / 1000, 3)
    wall = _seg(segs, "CAD-2796", y=-803593.5, layer="1")
    treads = [_seg(segs, f"CAD-{i}", layer="5", span=(-803593.5, -802443.5)) for i in (2883, 2890, 2889, 2888, 2887, 2886, 2885, 2884, 2891, 2892, 2893)]
    tread_x = sorted(t["A"][0] for t in treads)
    outer_arc = arcs["CAD-2977"]
    arc_low_y = outer_arc.cy - outer_arc.radius
    st = _struct_p4((-142000, -804300, -133000, -799000))
    st_diag = [l for l in st if abs(l["FROM"][0] - l["TO"][0]) > 3000 and abs(l["FROM"][1] - l["TO"][1]) > 1500]
    sxs = sorted({v[0] for l in st_diag for v in (l["FROM"], l["TO"])})
    sys_ = sorted({v[1] for l in st_diag for v in (l["FROM"], l["TO"])})
    st_w, st_d = round((sxs[-1] - sxs[0]) / 1000, 2), round((sys_[-1] - sys_[0]) / 1000, 2)
    st_beam = [l for l in st if abs(l["FROM"][1] - l["TO"][1]) < 5 and -803100 < l["FROM"][1] < -802900]
    # printed / authored 587: outer railing line (-180222.5) to the west edge (-186092.5) -> 5.870
    w = SR.reconcile_dimension(
        name="VOID_WIDTH", printed_value=5.87, printed_source="FF sheet printed 587 = DWG dimension entity (authored, geometry 5870, no text override)",
        cad_candidates=[
            {"BASIS": "west edge -186092.5 to the OUTER railing line CAD-2933 (-180222.5)", "VALUE": 5.87, "ENTITY_IDS": ["CAD-2932", "CAD-2933"], "OBJECT": "VOID_STAIR_ZONE / slab opening to the outer railing line"},
            {"BASIS": "west edge to the INNER railing line CAD-2935.e1df2cee (-180272.5) = the X diagonals' extent", "VALUE": x_w, "ENTITY_IDS": ["CAD-2936", "CAD-2937", "CAD-2935.e1df2cee"], "OBJECT": "SLAB_OPENING (X-marked, structural p4 X agrees)"}],
        classification="SAME_OBJECT_DIFFERENT_FACE_BASIS",
        explanation="one opening measured to the two lines of the 50 mm railing pair on its east side: 5.87 to the outer line (the authored dimension), 5.82 to the inner line (the X); neither replaces the other")
    d = SR.reconcile_dimension(
        name="VOID_DEPTH", printed_value=4.00, printed_source="FF sheet printed 400 = two DWG dimension entities (authored, geometry 4000, no text override) from the void's north line -799593.5 to the NE wall inner face -803593.5",
        cad_candidates=[
            {"BASIS": "north line CAD-2932 (-799593.5) to the NE wall inner face CAD-2796 (-803593.5)", "VALUE": 4.00, "ENTITY_IDS": ["CAD-2932", "CAD-2796"], "OBJECT": "VOID_STAIR_ZONE: slab opening + the straight-flight strip along the NE wall"},
            {"BASIS": "X diagonals CAD-2936 / CAD-2937 extent -799643.5 .. -802393.5", "VALUE": x_d, "ENTITY_IDS": ["CAD-2936", "CAD-2937", "CAD-2934", "CAD-2935.bb96ea7f"], "OBJECT": "SLAB_OPENING (Open To Below): the structural p4 X spans the same rectangle"},
            {"BASIS": "flight strip: railing line CAD-2934 (-802443.5) to the wall face (-803593.5), tread lines every 300 mm", "VALUE": 1.15, "ENTITY_IDS": [t["ID"] for t in treads], "OBJECT": "STRAIGHT_FLIGHT_STRIP (inclined flight, not a floor opening and not a slab)"},
            {"BASIS": "outer stair arc CAD-2977 lowest point", "VALUE": round((-799643.5 - arc_low_y) / 1000, 3), "ENTITY_IDS": ["CAD-2977"], "OBJECT": "curved outer railing extreme (reaches the wall face line)"}],
        classification="IDENTITY_MAPPING_DIFFERENCE",
        explanation="the printed 400 is the depth of the VOID_STAIR_ZONE (open well + the 1.15 m straight-flight strip to the NE wall face); the 2.75 PA02 used is the depth of the SLAB_OPENING marked by the X on the architectural FF copy and on the structural p4 slab plan; PA02 mapped the word 'void' to the X only. Both objects are preserved; neither value is substituted or averaged")
    SR.assert_not_substituted(w, [(5.87, 5.82)])
    SR.assert_not_substituted(d, [(4.00, 2.75)])
    objects = {
        "VOID_STAIR_ZONE": {"WIDTH_M": 5.87, "DEPTH_M": 4.00, "AREA_M2": round(5.87 * 4.00, 3), "BASIS": "printed / authored DWG dimensions 587 x 400",
                            "BOUNDS_FF_MM": {"X": [-186092.5, -180222.5], "Y": [-803593.5, -799593.5]}, "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY",
                            "CONTAINS": ["SLAB_OPENING", "STRAIGHT_FLIGHT_STRIP", "railing line pairs"]},
        "SLAB_OPENING": {"WIDTH_M": x_w, "DEPTH_M": x_d, "AREA_M2": round(x_w * x_d, 3), "BASIS": "architectural X (CAD-2936/2937) = structural p4 'Open To Below' X",
                         "BOUNDS_FF_MM": {"X": [xs[0], xs[-1]], "Y": [ys[0], ys[-1]]}, "STRUCTURAL_P4_X_M": [st_w, st_d],
                         "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY (two independent authors agree)"},
        "STRAIGHT_FLIGHT_STRIP": {"WIDTH_M": round((tread_x[-1] - tread_x[0]) / 1000, 3), "DEPTH_M": 1.15, "TREADS": len(treads) - 1, "TREAD_GOING_M": 0.30,
                                  "BASIS": "tread lines CAD-2883..2893 between CAD-2934 and the wall face; structural p4 draws a beam pair at y -802969/-803071 under it",
                                  "STRUCTURAL_BEAM_UNDER_STRIP": st_beam, "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY"},
    }
    return {"ARTIFACT": "VOID_GEOMETRY_RECONCILIATION", "PRINTED_VOID_WIDTH": 5.87, "PRINTED_VOID_DEPTH": 4.00,
            "PRINTED_DIMENSION_ENTITIES": {"587": d587, "400_a": d400a, "400_b": d400b},
            "CAD_VOID_WIDTH": {"OUTER_RAILING_BASIS": 5.87, "INNER_RAILING_BASIS": x_w}, "CAD_VOID_DEPTH": {"WALL_FACE_BASIS": 4.00, "X_BASIS": x_d},
            "CAD_ENTITY_IDS": {"NORTH": [top["ID"]] + [t["ID"] for t in top2], "EAST": [e["ID"] for e in east], "SOUTH_OF_X": [s["ID"] for s in south],
                               "DIAGONALS": [s["ID"] for s in diag], "NE_WALL_FACE": wall["ID"], "TREADS": [t["ID"] for t in treads], "OUTER_ARC": "CAD-2977"},
            "CAD_BOUNDARY_BASIS": "railing line pairs (50 mm) on the north / east / south-of-X sides; the NE wall inner face on the south; the curved stair on the west",
            "RECONCILIATION": {"WIDTH": w, "DEPTH": d},
            "OBJECTS_PRESERVED": objects,
            "PA02_STATEMENT_STATUS": "REOPENED: 'void 5.82 x 2.75' named the SLAB_OPENING only; the printed 587 x 400 names the VOID_STAIR_ZONE; 5.82 x 2.75 is NOT substituted for 5.87 x 4.00",
            "NEVER_AVERAGED": True, "STRUCTURAL_P4_LINES_IN_BOX": st}


# ------------------------------------------------------------------ B/C. reception vertical faces
def reception_faces(segs, void):
    E = []
    ev = lambda *items: list(items)
    # north (+y, SW side of the plan) edge
    _seg(segs, "CAD-1200.f76a5bdb", y=-799643.5, layer="2"); _seg(segs, "CAD-1200.451f96b9", y=-799643.5, layer="2")
    _seg(segs, "CAD-2811", y=-798393.5, layer="1"); _seg(segs, "CAD-2776", y=-798243.5, layer="1")
    E.append(SR.edge_record(EDGE_ID="RV-N", PLAN_AXIS="+y edge of the opening (y -799594 / -799644)", LENGTH_M=5.87,
                            GROUND_FLOOR_PHYSICAL_FACE="NONE: the GF copy draws only the dashed (layer 2) outline CAD-1200.* of the opening above; the reception floor continues",
                            FIRST_FLOOR_PHYSICAL_FACE="RAILING at the slab edge (50 mm pair CAD-2932 / CAD-2935.*); the FF wall CAD-2811 / CAD-2776 (150 thick, layer 1) stands 1.20 m back across the gallery (DWG dim 120 at x -183133)",
                            VOID_FLOOR_OPENING=True, WALL_CONTINUES_VERTICALLY=False, RAILING_AT_FIRST_FLOOR=True, OPEN_EDGE=True, STAIR_EDGE=False, COLUMN=False, GLAZING=False,
                            OTHER="structural p4 draws two 1.8 pt lines at y -799646 / -799447 (a 200 edge element under the gallery: beam, PROPOSED)",
                            EVIDENCE=ev("DWG FF copy CAD-2932/2935 (railing pair)", "DWG GF copy CAD-1200.* dashed", "structural p4 lines at -799646/-799447"), STATUS="ESTABLISHED_FROM_DWG (plan); no section cuts this edge"))
    # east (+x, NW side) edge
    _seg(segs, "CAD-1200.0b7b994b", x=-135419.9, layer="2"); _seg(segs, "CAD-321", x=-135419.9, layer="2")
    _seg(segs, "CAD-2805", x=-179072.5, layer="5", span=(-803593.5, -801193.5)); _seg(segs, "CAD-2806", x=-179022.5, layer="5", span=(-803593.5, -801193.5))
    _seg(segs, "CAD-1199", x=-134169.9, layer="2", span=(-803593.5, -801193.5))
    E.append(SR.edge_record(EDGE_ID="RV-E", PLAN_AXIS="+x edge of the opening (x -180223 / -180273 FF; -135370 / -135420 GF)", LENGTH_M=4.00,
                            GROUND_FLOOR_PHYSICAL_FACE="NONE: dashed outline only (CAD-1200.0b7b994b, CAD-321); the GF reception continues toward the SALOON",
                            FIRST_FLOOR_PHYSICAL_FACE="RAILING (CAD-2933 / CAD-2935.e1df2cee, 2.85 / 2.75 m) over the slab opening; the flight's end lines CAD-2893 / CAD-2904 over the strip; a 1.25 m strip (DWG dim 125) with four 300 mm tread lines (CAD-2905..CAD-3362) then a 50 mm pair CAD-2805 / CAD-2806 (2.40 m) that the GF copy mirrors dashed (CAD-1199) - a railing or a wall stub over a beam (structural p4: 1.8 pt line at x -134226, 2.40 m)",
                            VOID_FLOOR_OPENING=True, WALL_CONTINUES_VERTICALLY=False, RAILING_AT_FIRST_FLOOR=True, OPEN_EDGE=True, STAIR_EDGE=True, COLUMN=False, GLAZING=False,
                            OTHER="the 2.40 m element 1.25 m off the edge: ROLE UNKNOWN (railing vs wall stub); not on the void edge",
                            EVIDENCE=ev("DWG FF copy railing pair", "DWG dims 125 / 120", "structural p4 line at x -134226"), STATUS="ESTABLISHED_FROM_DWG for the edge; UNKNOWN for the 2.40 m element"))
    # south (-y, NE neighbour side): two portions
    _seg(segs, "CAD-168", y=-803593.5, layer="2", span=(-141239.9, -134219.9)); _seg(segs, "CAD-1204", y=-803793.5, layer="2", span=(-141239.9, -138419.9))
    _seg(segs, "CAD-169", y=-803643.5, layer="5", span=(-141239.9, -137419.9))
    _seg(segs, "CAD-822", y=-803593.5, layer="1", span=(-137419.9, -134769.9)); _seg(segs, "CAD-823", y=-803793.5, layer="1", span=(-137419.9, -134169.9))
    _seg(segs, "CAD-2796", y=-803593.5, layer="1"); _seg(segs, "CAD-2787", y=-803793.5, layer="1")
    E.append(SR.edge_record(EDGE_ID="RV-S-A", PLAN_AXIS="-y edge, west portion x -141240 .. -137420 (GF coords)", LENGTH_M=3.82,
                            GROUND_FLOOR_PHYSICAL_FACE="OPENING to the 1.50 m garden strip (DWG dim 150) before the neighbour wall: both wall-face lines are dashed on the GF copy (CAD-168 / CAD-1204, layer 2 = overhead); a solid layer-5 line CAD-169 at -803644 (threshold / step / stair-string line, role UNRESOLVED); no door or glazing line found (layers D / W)",
                            FIRST_FLOOR_PHYSICAL_FACE="WALL (layer 1, CAD-2796 / CAD-2787, 200 thick) over the GF opening; its support (beam / lintel) not read",
                            VOID_FLOOR_OPENING=True, WALL_CONTINUES_VERTICALLY=False, RAILING_AT_FIRST_FLOOR=False, OPEN_EDGE=True, STAIR_EDGE=True, COLUMN=True, GLAZING="UNKNOWN",
                            OTHER="800 x 250 column CAD-12242 / CAD-12300 at x -138220..-137420 in the wall line on both copies; the curved flight's outer arc reaches the -803644 line",
                            EVIDENCE=ev("DWG GF copy dashed faces CAD-168 / CAD-1204", "DWG GF copy CAD-169 solid", "DWG FF copy CAD-2796 / CAD-2787 walls"), STATUS="ESTABLISHED_FROM_DWG (plan); closure of the GF opening UNKNOWN"))
    E.append(SR.edge_record(EDGE_ID="RV-S-B", PLAN_AXIS="-y edge, east portion x -137420 .. -135370 (GF coords; the wall runs on to the 600 column at -134770)", LENGTH_M=2.05,
                            GROUND_FLOOR_PHYSICAL_FACE="WALL (layer 1, CAD-822 / CAD-823, 200 thick) between the 800 column and the 600 column (2.65 m); inner face y -803594",
                            FIRST_FLOOR_PHYSICAL_FACE="WALL (layer 1, CAD-2796 / CAD-2787) in the same plane; the straight flight's tread lines end on this face (CAD-2883..2893)",
                            VOID_FLOOR_OPENING=True, WALL_CONTINUES_VERTICALLY=True, RAILING_AT_FIRST_FLOOR=False, OPEN_EDGE=False, STAIR_EDGE=True, COLUMN=True, GLAZING=False,
                            OTHER="the inclined flight occludes the lower part of this face; the FF slab does not land on it over the flight strip (the strip is a flight, structural p4 marks no slab panel there)",
                            EVIDENCE=ev("same wall plane on the GF copy (CAD-822/823) and the FF copy (CAD-2796/2787)", "flight-strip tread lines terminate on the face", "structural p4: X excludes the strip; beam pair under the strip"),
                            STATUS="PROVISIONAL: plan evidence only; no section cuts the opening (A-A cut at x ~-143109 looks -x with the opening behind it; B-B cut at y ~-799350 looks +y away from it)"))
    # west (-x, SE side) edge
    _seg(segs, "CAD-1201", x=-141239.9, layer="2", span=(-803593.5, -799643.5))
    _seg(segs, "CAD-2807", x=-186092.5, layer="1", span=(-803593.5, -798443.5)); _seg(segs, "CAD-2808", x=-186242.5, layer="1", span=(-803593.5, -798593.5))
    E.append(SR.edge_record(EDGE_ID="RV-W", PLAN_AXIS="-x edge (x -141240 GF / -186093 FF)", LENGTH_M=3.95,
                            GROUND_FLOOR_PHYSICAL_FACE="NONE: dashed CAD-1201 (layer 2) - the GF reception is open to the DINING side; the curved stair (arcs r 1.53-2.78 centred at (-138454, -800863)) occupies this side of the opening",
                            FIRST_FLOOR_PHYSICAL_FACE="WALL (layer 1, CAD-2807 / CAD-2808, 150 thick, 5.15 m) on the opening's west edge, above the GF open edge; its opening-side face runs from its supporting beam's soffit (level NOT_ESTABLISHED) to the FF ceiling",
                            VOID_FLOOR_OPENING=True, WALL_CONTINUES_VERTICALLY=False, RAILING_AT_FIRST_FLOOR=False, OPEN_EDGE=True, STAIR_EDGE=True, COLUMN=False, GLAZING=False,
                            OTHER="OVERHANGING_WALL_FACE_ABOVE_OPEN_GF_EDGE: taller than the FF storey face by the beam depth; bottom level UNKNOWN",
                            EVIDENCE=ev("DWG GF copy CAD-1201 dashed", "DWG FF copy CAD-2807 / CAD-2808 walls"), STATUS="ESTABLISHED_FROM_DWG (plan); face bottom level UNKNOWN"))
    dh = SR.double_height_status(E, section_proof_by_edge={})
    faces = []
    def face(**f):
        faces.append(dict({"LAYER": "PHYSICAL_GEOMETRY"}, **f))
    face(FACE_ID="RVF-S-B", PLAN_EDGE="RV-S-B", GROUND_START_LEVEL=LEVELS["GF_FFL"], TOP_LEVEL="FF ceiling = +9.70 - roof slab T (0.16 PROVISIONAL) = +9.54", CONTINUES_TO_FIRST_FLOOR=True,
         CONTINUES_ABOVE_FIRST_FLOOR=True, FIRST_FLOOR_RAILING=False, OPEN_TO_VOID=True, HOST_STRUCTURE="NE wall between the 800 and 600 columns (200 thick, layer 1 on both copies)",
         LENGTH_M=2.05, HEIGHT={"VALUE_M": round(9.54 - 1.00, 2), "STATE": "PROVISIONAL", "BASIS": "+1.00 to +9.54 if the face is continuous; unproved by section"},
         OCCLUSION="inclined straight flight (1.15 m strip) against the face from GF up; stringer / skirting band not modelled",
         SOURCE="DWG GF + FF copies (plan); structural p4", STATUS="CANDIDATE_DOUBLE_HEIGHT_FACE - NOT_FULLY_ESTABLISHED (no section proof)", QUANTITY_STATE="NOT_ESTABLISHED")
    face(FACE_ID="RVF-W-FF", PLAN_EDGE="RV-W", GROUND_START_LEVEL="beam soffit under the FF wall: NOT_ESTABLISHED", TOP_LEVEL="+9.54 (PROVISIONAL)", CONTINUES_TO_FIRST_FLOOR=False,
         CONTINUES_ABOVE_FIRST_FLOOR=True, FIRST_FLOOR_RAILING=False, OPEN_TO_VOID=True, HOST_STRUCTURE="FF wall CAD-2807 / CAD-2808 over the open GF edge",
         LENGTH_M=3.95, HEIGHT={"VALUE_M": None, "STATE": "NOT_ESTABLISHED", "BASIS": "FF storey face (4.04 = 9.54 - 5.50) plus the beam depth below +5.50, unknown"},
         OCCLUSION="curved flight and its railing in front of the lower part", SOURCE="DWG FF copy", STATUS="UNKNOWN bottom; face exists at FF", QUANTITY_STATE="NOT_ESTABLISHED")
    face(FACE_ID="RVF-N-GALLERY-WALL", PLAN_EDGE="RV-N (1.20 m behind the edge)", GROUND_START_LEVEL=LEVELS["FF_SLAB"], TOP_LEVEL="+9.54 (PROVISIONAL)", CONTINUES_TO_FIRST_FLOOR=None,
         CONTINUES_ABOVE_FIRST_FLOOR=False, FIRST_FLOOR_RAILING=True, OPEN_TO_VOID=False, HOST_STRUCTURE="FF wall CAD-2811 / CAD-2776 (150) behind the gallery", LENGTH_M=None,
         HEIGHT={"VALUE_M": None, "STATE": "NOT_ESTABLISHED", "BASIS": "a normal FF storey face; not a void face"}, OCCLUSION=None, SOURCE="DWG FF copy", STATUS="NORMAL_FF_FACE (not double height)", QUANTITY_STATE="NOT_ESTABLISHED")
    face(FACE_ID="RVF-S-A-FF", PLAN_EDGE="RV-S-A", GROUND_START_LEVEL="support of the FF wall over the GF garden opening: NOT_ESTABLISHED", TOP_LEVEL="+9.54 (PROVISIONAL)", CONTINUES_TO_FIRST_FLOOR=False,
         CONTINUES_ABOVE_FIRST_FLOOR=True, FIRST_FLOOR_RAILING=False, OPEN_TO_VOID=True, HOST_STRUCTURE="FF NE wall over the GF opening (beam / lintel unknown)", LENGTH_M=3.82,
         HEIGHT={"VALUE_M": None, "STATE": "NOT_ESTABLISHED", "BASIS": "FF face + lintel face; GF opening head level unknown"}, OCCLUSION="curved flight", SOURCE="DWG GF + FF copies", STATUS="UNKNOWN bottom", QUANTITY_STATE="NOT_ESTABLISHED")
    return {"ARTIFACT": "RECEPTION_VERTICAL_FACE_REGISTER", "SECTION_CUT_RELATIONSHIP": {
                "A-A": {"CUT_LINE_CAD_GF": "x ~ -143109 (vertical), looking toward -x", "RELATION_TO_OPENING": "the opening (x -141240..-135370) lies BEHIND the viewer; A-A cannot show it", "SOURCE": "PA02 read of the section marks (PROVISIONAL)"},
                "B-B": {"CUT_LINE_CAD_GF": "y ~ -799350 (horizontal), 0.25 m north of the opening's north line", "RELATION_TO_OPENING": "the native B-B main-block bay shows the +5.50 slab continuous across the bay with doors on both floors and no opening: B-B looks +y, away from the opening", "SOURCE": "scratch bb_main_block.png (SOURCE_IMAGE, INFORMATIVE) + section-mark read (PROVISIONAL)"},
                "CONSEQUENCE": "no section in the set cuts or faces the reception opening; the vertical model rests on the two plan copies (solid vs dashed layers) and the structural p4 slab plan"},
            "PLAN_COMPASS": {"-y": "NE neighbour side", "+y": "SW", "-x": "SE facade side", "+x": "NW sea-view side", "BASIS": "roof copy: NE parapet CAD-4735 is the -y line, SE outer face CAD-4804 is the -x line"},
            "EDGES": E, "DOUBLE_HEIGHT": dh, "VERTICAL_FACES": faces,
            "VOID_OBJECTS_USED": {"SLAB_OPENING": void["OBJECTS_PRESERVED"]["SLAB_OPENING"]["BOUNDS_FF_MM"], "VOID_STAIR_ZONE": void["OBJECTS_PRESERVED"]["VOID_STAIR_ZONE"]["BOUNDS_FF_MM"]},
            "L-10_STATUS": "REOPENED_BY_OWNER_SOURCE_REVIEW",
            "PA02_STATEMENT_WITHDRAWN": "'no wall stands on the void boundary at FF, so there is no double-height WALL face' - withdrawn: RV-S-B carries the same wall on both floors with the flight against it; RV-W carries an FF wall over an open GF edge"}


# ------------------------------------------------------------------ D/E. stair register v2
def stair_v2(n, segs, arcs, void):
    # main curved stair (reception)
    arcs_gf = sorted([a for a in arcs.values() if abs(a.cx + 138454) < 5 and abs(a.cy + 800863) < 5], key=lambda a: a.radius)
    outer = developed_length([{"ID": a.object_id, "KIND": "ARC", "radius_mm": a.radius, "sweep_rad": (a.end_angle - a.start_angle) % (2 * math.pi)} for a in arcs_gf if abs(a.radius - 2780.5) < 1])
    inner = developed_length([{"ID": a.object_id, "KIND": "ARC", "radius_mm": a.radius, "sweep_rad": (a.end_angle - a.start_angle) % (2 * math.pi)} for a in arcs_gf if abs(a.radius - 1530.5) < 1])
    east_treads = [_seg(segs, f"CAD-{i}", layer="5", span=(-180222.5, -179072.5)) for i in (2905, 2906, 2907, 2908, 3362)]
    main = {"STAIR_ID": "MAIN-CURVED", "LOCATION": "reception opening", "STOREYS": "+1.00 -> +5.50 (rise 4.50, established levels)",
            "COMPONENTS": [
                {"COMPONENT": "CURVED_FLIGHT", "ARCS_GF": [{"ID": a.object_id, "R_MM": round(a.radius, 1)} for a in arcs_gf], "OUTER_STRING_DEVELOPED": outer, "INNER_STRING_DEVELOPED": inner,
                 "PHYSICAL_FACE": "none plasterable: bounded by railing line pairs (50 mm)", "EXPOSURE": "OPEN", "UNDERSIDE": "NOT_ESTABLISHED (curved soffit; riser count and rise not read)"},
                {"COMPONENT": "STRAIGHT_FLIGHT_NE", "STRIP": void["OBJECTS_PRESERVED"]["STRAIGHT_FLIGHT_STRIP"], "PHYSICAL_FACE": "RVF-S-B behind it (wall), railing CAD-2934 / CAD-2935.bb96ea7f on the opening side",
                 "EXPOSURE": "flight against the NE wall face; underside seen from the GF reception", "STAIR_FLIGHT_OCCLUSION": "occludes the lower part of RVF-S-B", "UNDERSIDE": "NOT_ESTABLISHED (slope from riser count; 10 treads x 0.30 read, rise per riser not read)"},
                {"COMPONENT": "SHORT_RUN_EAST_STRIP", "TREAD_LINES": [t["ID"] for t in east_treads], "TREADS": len(east_treads) - 1, "STRIP_WIDTH_M": 1.25,
                 "ROLE": "PROPOSED: the flight's final run north to the FF gallery (arrives at y -801194)", "STATUS": "PROPOSED_CORRESPONDENCE", "PHYSICAL_FACE": "none on the opening edge"},
                {"COMPONENT": "RAILINGS", "ENTITIES": ["CAD-2932/2935 north", "CAD-2933/2935 east", "CAD-2934/2935 south-of-X", "arcs r 2730.5 / 2780.5 curved"], "PLASTER": 0.0, "ZERO_BY_MATERIAL": True}],
            "WALL_FACES": ["RVF-S-B (candidate double height, NOT_FULLY_ESTABLISHED)", "RVF-W-FF (bottom UNKNOWN)"], "SLAB_LANDING_INTERRUPTION": "none inside the opening; the FF gallery slab meets the north and east railings"}
    # block stair (maid block, A-A)
    d250 = _dim(n, 250.0, (-234745, -792529)); d645 = _dim(n, 645.0, (-232455, -798444))
    d120a = _dim(n, 120.0, (-234745, -794244)); d10 = _dim(n, 10.0, (-233545, -794244)); d120b = _dim(n, 120.0, (-233445, -794207))
    d330 = _dim(n, 330.0, (-233882, -793194)); d120c = _dim(n, 120.0, (-233882, -791994)); d195 = _dim(n, 195.0, (-233882, -796494))
    lines = [s for s in segs.values() if abs(s.x1 - s.x2) < 1 and abs(s.x1 + 233595.2) < 1 or abs(s.x1 - s.x2) < 1 and abs(s.x1 + 233395.2) < 1]
    lines = [{"ID": s.object_id, "LAYER": s.provenance.layer, "X": round(s.x1, 1), "Y": sorted([round(s.y1, 1), round(s.y2, 1)]), "LENGTH_MM": round(abs(s.y2 - s.y1), 1)} for s in lines if abs(s.y2 - s.y1) > 3000]
    element = SR.stair_element(element_id="BLOCK-STAIR-MID-ELEMENT", printed_thickness_cm=10, length_m=round(max(l["LENGTH_MM"] for l in lines) / 1000, 3) if lines else 3.35, role="UNRESOLVED",
                               role_evidence=["DWG dims 120 + 10 + 120 across the well (authored)", "DWG dims 120 / 330 / 195 along the well: the element spans the 3.30 flight length between the two landings",
                                              "A-A native (scratch AA_stair.png, SOURCE_IMAGE, INFORMATIVE): the far flight and its handrail are drawn visible through the well between the two flights, with handrail lines on both flights"],
                               excluded_roles=["STRUCTURAL_SPINE (full height): excluded PROVISIONALLY - a full-height spine would hide the far flight on A-A", "PARTITION (full height): excluded PROVISIONALLY for the same reason"])
    element["CANDIDATE_ROLES_REMAINING"] = ["LOW_UPSTAND", "BALUSTRADE_BASE", "RAILING_SUPPORT", "OTHER (e.g. a 10 cm stringer upstand)"]
    element["HEIGHT"] = "not drawn in plan; A-A does not print it; NOT_ESTABLISHED"
    element["PLASTER_TREATMENT"] = "none until the role is known; if a low upstand, its two faces are a small item (length x upstand height), never storey height"
    element["STRUCTURAL_SOURCE"] = "ST7757 p4 / p5 stair cell 'B3 (With Stair)': beams B2 / B7 / B14 around the cell, no spine wall or beam drawn between the flights (visual read of the vector plot, PROVISIONAL)"
    element["DWG_LINES"] = lines
    element["DWG_DIMS"] = {"ACROSS": [d120a, d10, d120b], "ALONG": [d120c, d330, d195], "WELL": [d250, d645]}
    faces = []
    def bf(fid, storey, side, bottom, top, length, exposure, openings, railing, landing, occl, notes):
        faces.append({"FACE_ID": fid, "STOREY": storey, "SIDE": side, "BOTTOM": bottom, "TOP": top, "HEIGHT_M": round(top - bottom, 2), "LENGTH_M": length,
                      "PHYSICAL_FACE": "block-stair well wall (A-A cut walls; plan cell lines)", "EXPOSURE": exposure, "OPENINGS": openings, "RAILING_RELATION": railing,
                      "SLAB_LANDING_INTERRUPTION": landing, "STAIR_FLIGHT_OCCLUSION": occl, "REFERENCE_GROSS_M2": round((top - bottom) * length, 3),
                      "QUANTITY_STATE": "GEOMETRIC_REFERENCE_ONLY", "NOT_PERIMETER_X_STOREY": True, "NOTES": notes})
    W, L = 2.50, 6.45
    for storey, (b, t) in {"GF": (0.30, 5.50), "FF": (5.50, 9.70), "ROOF": (9.70, 13.90)}.items():
        bf(f"STW2-{storey}-WEST", storey, "long wall (A-A left)", b, t, L, "flight against it for half the storey; landing at mid-storey", ["FF door (A-A)"] if storey == "FF" else [], "handrail on the flight, not on the wall",
           "landing slab at mid-storey (A-A)", "one flight per storey occludes ~half the length", ["face length = printed 645 well length (DWG dim authored)"])
        bf(f"STW2-{storey}-EAST", storey, "long wall (A-A right, continuous +0.30 -> +13.90)", b, t, L, "flight against it for half the storey", ["arched window (A-A)"] if storey == "ROOF" else [], "handrail on the flight",
           "landing slabs attach on this side (A-A)", "one flight per storey", ["continuous on A-A but split per storey: landings interrupt (§136)"])
        bf(f"STW2-{storey}-NORTH", storey, "end wall", b, t, W, "landing end wall", [], "none", "landing slab meets it", "none", ["length = printed 250 (DWG dim authored)"])
        bf(f"STW2-{storey}-SOUTH", storey, "end wall", b, t, W, "landing end wall", [], "none", "landing slab meets it", "none", ["length = printed 250"])
    block = {"STAIR_ID": "BLOCK-STAIR", "LOCATION": "maid block, A-A", "WELL_PRINTED": {"WIDTH_CM": [120, 10, 120], "LENGTH_CM": 645, "SOURCE": "DWG dimension entities (authored; the printed FF-sheet values are these entities)"},
             "MID_ELEMENT": element, "FACES": faces, "STOREY_REFERENCE_GROSS_M2": {s: round(sum(f["REFERENCE_GROSS_M2"] for f in faces if f["STOREY"] == s), 3) for s in ("GF", "FF", "ROOF")},
             "SUBTOTAL_STATUS": "GEOMETRIC_REFERENCE_ONLY: PA02's per-storey gross subtotals (93.08 / 75.18 / 75.18) are demoted - they were four faces x storey height, i.e. a perimeter x storey figure; a quantity needs the interruption, opening and occlusion model per face",
             "UNDERSIDE": "NOT_ESTABLISHED", "LANDINGS": "two per storey (A-A); landing soffits not measured"}
    return {"ARTIFACT": "STAIR_COMPONENT_REGISTER_V2", "STAIRS": [main, block], "PRINTED_KEPT": {"MAIN": "587 x 400 zone", "BLOCK": "120 + 10 + 120 x 645"},
            "SUPERSEDES": "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json STAIR_WELL_FACE_REGISTER (PA02) - faces carried with the new fields; subtotals demoted"}


# ------------------------------------------------------------------ F. column vertical exposure
def column_vertical(segs):
    w1 = _seg(segs, "CAD-822", y=-803593.5, layer="1", span=(-137419.9, -134769.9))
    w2 = _seg(segs, "CAD-823", y=-803793.5, layer="1", span=(-137419.9, -134169.9))
    w3 = _seg(segs, "CAD-783", x=-134219.9, layer="5", span=(-805093.5, -803643.5))
    nb = _seg(segs, "CAD-260", y=-805093.5, layer="1")
    loop = {"X": [-134769.9, -134169.9], "Y": [-803793.5, -803543.5], "SIZE_MM": [600, 250], "SOURCE": "S-COL.BON loop CAD-12230 (architectural); structural 300 x 600 (registered)"}
    faces = [
        {"FACE": "N (y -803544, 0.60 m, toward the reception / saloon)", "EXPOSURE": "EXPOSED", "WHY": "projects 50 mm beyond the wall inner face -803594 (100 mm on the structural 300 depth)", "PLASTERABLE_LM": 0.60, "SIDE": "INTERNAL"},
        {"FACE": "S (y -803794, 0.60 m, toward the 1.30 m garden strip before the neighbour wall CAD-260)", "EXPOSURE": "EXTERNAL_SIDE", "WHY": "in the wall's outer plane (CAD-823 runs along it)", "PLASTERABLE_LM": 0.60, "SIDE": "EXTERNAL (finish system UNKNOWN)"},
        {"FACE": "W (x -134770, 0.25 m)", "EXPOSURE": "BURIED_IN_WALL", "WHY": "the 200 wall CAD-822 / CAD-823 (layer 1 = wall layer; the neighbour wall CAD-260 is on the same layer) ends on this face", "PLASTERABLE_LM": 0.05, "SIDE": "INTERNAL (50 mm reveal sliver; 100 mm on the structural depth)"},
        {"FACE": "E (x -134170, 0.25 m)", "EXPOSURE": "PARTIALLY_COVERED", "WHY": "CAD-783 (layer 5, x -134220) runs south from y -803644: covers the outer 150 mm; the inner 100 mm faces the room", "PLASTERABLE_LM": 0.10, "SIDE": "INTERNAL (sliver)"},
    ]
    internal = round(sum(f["PLASTERABLE_LM"] for f in faces if f["SIDE"].startswith("INTERNAL")), 2)
    rec = SR.column_vertical_exposure(column_id="LOOP-059 (D2)", exposed_girth_lm=internal, girth_state="PROVISIONAL",
                                      exposed_height_m=None, height_state="NOT_ESTABLISHED",
                                      height_evidence=["GF FFL +1.00 (established)", "structural p4: a beam runs north from the column (1.8 pt line at x -134226, 2.40 m); its depth is not read -> the soffit level is unknown",
                                                       "upper bound: FF slab soffit +5.50 - T (T not read) -> < 4.50; lower bound with a 0.60 beam: 3.90"],
                                      parametric_height_m=3.20, parametric_source="NORMAL_INTERNAL_PLASTER_HEIGHT, OWNER_PROJECT_INPUT", faces=faces)
    rec["GIRTH_ALTERNATIVES"] = {"ARCHITECTURAL_LOOP_250_DEEP": internal, "STRUCTURAL_300_DEEP": round(0.60 + 0.10 + 0.15, 2), "PA02_ALL_FOUR_FACES": 1.80,
                                 "NOTE": "PA02's 1.80 (four exposed faces) is SUPERSEDED: walls CAD-822/823 and CAD-783 abut the column; no value is selected between 0.75 and 0.85"}
    rec["EXTERNAL_FACE_LM"] = 0.60
    rec["PA02_5_76_STATUS"] = "SUPERSEDED: 1.80 x 3.20 = 5.76 mixed a superseded girth with a parametric height; the physical area needs the exposed height (NOT_ESTABLISHED); the parametric figure is now 0.75 x 3.20 and labelled OWNER_PARAMETRIC"
    rec["WALL_EVIDENCE"] = [w1, w2, w3, nb]
    rec["LOOP"] = loop
    rec["COLUMN_EXISTS"] = "ESTABLISHED (unchanged)"
    rec["COLUMN_OWNS_CLEAR_FINISH_FACE"] = "NO (unchanged)"
    return {"ARTIFACT": "COLUMN_VERTICAL_EXPOSURE_REGISTER", "COLUMNS": [rec]}


# ------------------------------------------------------------------ NE elevation eligibility
def ne_eligibility():
    rec = SR.elevation_finish_eligibility(
        face_id="F-NE-SOLID-EXT (18.27 m outer face) / F-NE-SOLID-ROOFSIDE (18.87 m)", elevation_source_exists=True,
        elevation_page="P7757_DRAWINGS.pdf page 7 (NORTH EAST ELEVATION, raster); the DWG elevation blob is the NORTH WEST elevation (L-08)",
        finish_system_established=False,
        solid_face_top={"STATUS": "PROVISIONAL", "CANDIDATES": [{"LEVEL": 11.10, "SOURCE": "A-A: hatched masonry 1.40 above +9.70 before the band"}, {"LEVEL": "~11.27 (scale)", "SOURCE": "page 7 wall-top line by the 157.5 px/m chain scale; no printed level at the top"}], "SELECTED": None},
        band_exists={"STATUS": "NOT_ESTABLISHED", "EVIDENCE": ["A-A hatch height 1.62 = 1.40 + 0.20 (PA02 read)", "page 7 draws ONE top line with rounded ends and no separate band line (native crops ne_top_zoomL / ne_top_zoomR: a single line only)"], "NOTE": "the +11.30 line on visual_qa/NE_PARAPET_TOP.png is a DERIVED overlay, not source"},
        band_height={"STATUS": "DERIVED_PROVISIONAL", "VALUE_M": 0.20, "BASIS": "by analogy with the SE band (DIM-20 = 20) and the A-A hatch remainder; not printed on the NE elevation"},
        band_trade_role={"STATUS": "UNKNOWN", "OPTIONS": ["coping / capping band (COPING_CAPPING component)", "plaster band continuous with the face", "none (no band)"]},
        queue_reason="finishes specification SOURCE_NOT_PROVIDED; the NE elevation (page 7) draws no hatch or finish note on the parapet face; sources exhausted for the finish, not for the geometry")
    rec["QA_OVERLAY_NOT_SOURCE"] = "visual_qa/NE_PARAPET_TOP.png: its +11.10 / +11.30 lines are drawn by us; they support a QA check of the read, never the level"
    rec["PA02_QUEUE_WORDING_WITHDRAWN"] = "'no elevation of the neighbour side exists in the set' (NE-PARAPET-EXTERNAL-FINISH, PA02 queue v2) - WITHDRAWN: page 7 is the NE elevation"
    return {"ARTIFACT": "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER", "FACES": [rec]}


# ------------------------------------------------------------------ SE opening dimension ownership audit
def se_ownership():
    D = []
    def d(**k):
        D.append(SR.dimension_ownership(**k))
    tower = "tower strip vertical chain (native page 4, crop se_tower_chain.png, levels axis)"
    d(dim_id="SE-V-185", printed_value=185, chain=tower, owner="SILL_OFFSET", witness_from="+0.15 datum line (level marker printed beside it)", witness_to="W1 sill line", status="PRINTED_OWNED",
      evidence="chain read on the native crop: 185 sits between the +0.15 marker tick and the lowest window's sill tick")
    d(dim_id="SE-V-200a", printed_value=200, chain=tower, owner="OPENING_HEIGHT", witness_from="W1 sill", witness_to="W1 head", status="PRINTED_OWNED", evidence="ticks at the window's sill and head lines")
    d(dim_id="SE-V-250", printed_value=250, chain=tower, owner="SPANDREL", witness_from="W1 head", witness_to="W2 sill zone", status="PRINTED_OWNED", evidence="ticks at W1 head and the next tick below W2")
    d(dim_id="SE-V-8", printed_value=8, chain=tower, owner="FRAME_DETAIL", witness_from="tick below W2", witness_to="tick at W2 sill", status="UNRESOLVED",
      evidence="two small figures (8 and 5) sit between the 250 and the 230 on the native crop", note="sill / frame sub-dimensions: if chain segments, W2's sill is 0.13 higher than 250 alone implies; ownership UNRESOLVED")
    d(dim_id="SE-V-5", printed_value=5, chain=tower, owner="FRAME_DETAIL", witness_from="see SE-V-8", witness_to="see SE-V-8", status="UNRESOLVED", evidence="as SE-V-8")
    d(dim_id="SE-V-230", printed_value=230, chain=tower, owner="OPENING_HEIGHT", witness_from="W2 sill", witness_to="W2 head", status="PRINTED_OWNED", evidence="ticks at W2 sill and head")
    d(dim_id="SE-V-200b", printed_value=200, chain=tower, owner="OPENING_HEIGHT", witness_from="W3 sill", witness_to="W3 head", status="PRINTED_OWNED", evidence="ticks at W3 sill and head (W2 head = W3 sill: no spandrel figure between them on the crop)")
    d(dim_id="SE-V-170", printed_value=170, chain=tower, owner="OPENING_HEIGHT", witness_from="W4 sill", witness_to="W4 arch crown", status="PRINTED_OWNED",
      evidence="ticks at W4 sill and the crown of the semicircular fan-light; the arch spans the full 120 width", note="ARCH_GEOMETRY: rectangle 120 x 110 + semicircle r 60 = 170 total (PA02 arch_area kept)")
    d(dim_id="SE-H-120", printed_value=120, chain="tower strip horizontal (run axis)", owner="OPENING_WIDTH", witness_from="W2 west jamb", witness_to="W2 east jamb", status="PRINTED_OWNED", evidence="120 printed across W2 with jamb ticks; all four tower windows share the strip width")
    d(dim_id="SE-H-72", printed_value=72, chain="tower strip horizontal", owner="PIER_WIDTH", witness_from="W jamb", witness_to="tower edge", status="PROVISIONAL", evidence="72 with a 5 beside it at the strip edge on the crop; termination at the tower outer line not verified", note="the 93 / 72 / 72 / 27 / 123 / 215 / 402 run chain: only 120 (window) and 215 (main-block window) are opening owners; the rest are piers / run segments")
    mb = "main-block window (native page 4 crop se_mb_window.png)"
    d(dim_id="SE-MB-215", printed_value=215, chain=mb, owner="OPENING_WIDTH", witness_from="west frame outer line", witness_to="east frame outer line", status="PRINTED_OWNED",
      evidence="215 printed across the glazed frame with ticks at the frame's outer lines; the louvred shutters lie outside the 215 (a 113-ish figure at the left shutter is cut off)", note="width at the frame outer line; the structural opening may differ by the frame rebate (not printed)")
    d(dim_id="SE-MB-190", printed_value=190, chain=mb, owner="OPENING_HEIGHT", witness_from="sill line", witness_to="head line", status="PRINTED_OWNED", evidence="190 printed inside the window between the sill and head lines")
    d(dim_id="SE-MB-139", printed_value=139, chain=mb, owner="HEAD_OFFSET", witness_from="window head", witness_to="roof-edge base line above", status="PRINTED_OWNED",
      evidence="139 between the head tick and the roof-edge line tick (same 139 as DIM-19 of the SE audit: below_parapet_139_windows)")
    d(dim_id="SE-MB-220", printed_value=220, chain=mb, owner="STOREY_SEGMENT", witness_from="window sill", witness_to="line below (FF level zone)", status="PROVISIONAL",
      evidence="'20' visible at the bottom of the crop (220 cut off); termination below not in the crop", note="sill offset from the FF floor: PROVISIONAL")
    d(dim_id="SE-AN-250", printed_value=250, chain="annex entrance (native page 4)", owner="OPENING_HEIGHT", witness_from="threshold", witness_to="door head", status="PROVISIONAL",
      evidence="PA02 read: 250 printed at the annex door; witness termination not re-cropped in PA03")
    openings = []
    for oid, host, w, hr, arch, total, src, st in (
        ("SE-TW-W1", "F-SE-TOWER-EXT", 1.20, 2.00, None, 2.00, ["SE-H-120", "SE-V-200a"], "PRINTED_OWNED"),
        ("SE-TW-W2", "F-SE-TOWER-EXT", 1.20, 2.30, None, 2.30, ["SE-H-120", "SE-V-230"], "PRINTED_OWNED (sill level +-0.13 from SE-V-8/5)"),
        ("SE-TW-W3", "F-SE-TOWER-EXT", 1.20, 2.00, None, 2.00, ["SE-H-120", "SE-V-200b"], "PRINTED_OWNED"),
        ("SE-TW-W4", "F-SE-TOWER-EXT", 1.20, 1.10, {"KIND": "SEMICIRCLE", "RISE_M": 0.60, "R_M": 0.60}, 1.70, ["SE-H-120", "SE-V-170"], "PRINTED_OWNED (arch split derived from the 120 width)"),
        ("SE-TW-D1", "F-SE-TOWER-EXT", 1.08, 2.00, None, 2.00, [], "PROVISIONAL (raster read, no printed dimension)"),
        ("SE-MB-W1", "F-SE-FACADE-EXT", 2.15, 1.90, None, 1.90, ["SE-MB-215", "SE-MB-190"], "PRINTED_OWNED"),
        ("SE-AN-D1", "F-SE-ANNEX-EXT", 1.00, 2.50, None, 2.50, ["SE-AN-250"], "PROVISIONAL (height printed; width raster)")):
        rect = round(w * hr, 4)
        arch_a = round(math.pi * arch["R_M"] ** 2 / 2, 4) if arch else 0.0
        openings.append({"OPENING_ID": oid, "HOST_FACE": host, "CLEAR_WIDTH": w, "RECTANGULAR_HEIGHT": hr, "ARCH_GEOMETRY": arch, "TOTAL_HEIGHT": total,
                         "TOTAL_AREA": round(rect + arch_a, 4), "SOURCE_DIMENSIONS": src, "STATUS": st, "BOUNDING_BOX_USED": False})
    return {"ARTIFACT": "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT", "SOURCE": "native page 4 crops (se_tower_chain.png, se_mb_window.png, se_base_chain.png) - orchestrator visual reads of the ORIGINAL page, not of PA02 prose",
            "DIMENSIONS": D, "OPENINGS": openings,
            "PA02_OPENING_STATUS": "CONFIRMED for W1 / W2 / W3 / W4 / MB-W1 (printed-owned on both axes); PROVISIONAL kept for TW-D1 and AN-D1 (raster widths)",
            "NOT_A_DIMENSION_SOURCE": "PA02 prose / SE_FACADE_OPENINGS.png overlay"}


# ------------------------------------------------------------------ PA02 supersession ledger
def ledger(void, rv, st, col, ne, se):
    L = []
    def e(i, stmt, art, status, by, ev):
        L.append({"ITEM": i, "PA02_STATEMENT": stmt, "PA02_ARTIFACT": art, "STATUS": status, "REPLACED_OR_QUALIFIED_BY": by, "EVIDENCE": ev, "DATE": DATE, "HISTORY_REWRITTEN": False})
    e("SR-01", "FF void over the reception = 5.82 x 2.75 (X diagonals)", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json VOID", "REOPENED",
      "VOID_GEOMETRY_RECONCILIATION: SLAB_OPENING 5.82 x 2.75 and VOID_STAIR_ZONE 5.87 x 4.00 both preserved; the word 'void' mapped to the X only", "DWG dims 587 / 400 authored; structural p4 X")
    e("SR-02", "no wall stands on the void boundary at FF, so there is no double-height wall face", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json FINDING; ledger L-10", "WITHDRAWN",
      "RECEPTION_VERTICAL_FACE_REGISTER: RV-S-B same wall both floors with the flight against it (candidate); RV-W FF wall over an open GF edge; DOUBLE_HEIGHT_WALL_STATUS = " + rv["DOUBLE_HEIGHT"]["DOUBLE_HEIGHT_WALL_STATUS"],
      "CAD-822/823 (GF) + CAD-2796/2787 (FF); CAD-2807/2808 (FF) over CAD-1201 dashed (GF)")
    e("SR-03", "GF-RECEPTION-DOUBLE-HEIGHT set SUPERSEDED as a category; reception walls are normal-height faces", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json RECEPTION_WALL_HEIGHT_RULE", "WITHDRAWN",
      "the category stays open with RVF-S-B / RVF-W-FF / RVF-S-A-FF as NOT_ESTABLISHED faces", "as SR-02")
    e("SR-04", "CEILING_ABSENCE over 5.82 x 2.75", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json CEILING_ABSENCE", "REOPENED",
      "ceiling exclusion recomputed after the void freeze: SLAB_OPENING (no slab) + STRAIGHT_FLIGHT_STRIP (stair soffit instead of slab soffit)", "VOID_GEOMETRY_RECONCILIATION OBJECTS_PRESERVED")
    e("SR-05", "LOOP-059: all four faces exposed, girth 1.80 lm", "COLUMN_FACE_REGISTER.json; PLASTER_QUANTITY_TRACE D2:COLUMN:LOOP-059:girth", "SUPERSEDED",
      f"COLUMN_VERTICAL_EXPOSURE_REGISTER: internal plasterable girth {col['COLUMNS'][0]['COLUMN_EXPOSED_GIRTH_LM']['VALUE']} lm (arch) / 0.85 (struct), external face 0.60 separate", "walls CAD-822 / CAD-823 (layer 1) end on the W face; CAD-783 covers 150 of the E face")
    e("SR-06", "D2 column area 5.76 m2 = 1.80 x 3.20", "PLASTER_QUANTITY_TRACE D2:COLUMN:LOOP-059 (v4)", "SUPERSEDED",
      "physical area NOT_ESTABLISHED (height unknown); OWNER_PARAMETRIC 0.75 x 3.20 = 2.40 labelled as parametric", "COLUMN_VERTICAL_EXPOSURE_REGISTER")
    e("SR-07", "NE-PARAPET-EXTERNAL-FINISH: 'no elevation of the neighbour side exists in the set'", "OWNER_DECISION_QUEUE.json v2 (PA02)", "WITHDRAWN",
      "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER: ELEVATION_SOURCE_EXISTS = True (page 7); FINISH_SYSTEM_ESTABLISHED = False; queue item rewritten", "P7757_DRAWINGS.pdf page 7")
    e("SR-08", "NE parapet: solid face +9.70 -> +11.10 (1.40) + 0.20 band to +11.30", "ROOF_EDGES_FACADE_FINISH_KERB.json NE; visual_qa/NE_PARAPET_TOP.png", "CONFIRMED_AS_DERIVED_PROVISIONAL",
      "SOLID_FACE_TOP_STATUS PROVISIONAL (two candidates), BAND_EXISTS NOT_ESTABLISHED, BAND_HEIGHT DERIVED, BAND_TRADE_ROLE UNKNOWN; the overlay lines are not source", "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER")
    e("SR-09", "NW sea-view element = X-lattice balustrade on a low curved kerb; zero plaster for the lattice", "ROOF_EDGES_FACADE_FINISH_KERB.json NW_SEA_VIEW", "CONFIRMED",
      "BALUSTRADE_PLASTERABLE_SOLID_FACE = 0; the 0.10 x 1.30 is never a wall area; the kerb is a separate component", "page 6 native (172 / 100 / 10 printed at the element); visual_qa/NW_ROOF_EDGE.png INFORMATIVE")
    e("SR-10", "SE facade openings W1-W4, D1, MB-W1, AN-D1 with printed dimensions (orchestrator read)", "ROOF_EDGES_FACADE_FINISH_KERB.json SE_FACADE_OPENING_REGISTER", "CONFIRMED_IN_PART",
      se["PA02_OPENING_STATUS"], "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT on native page-4 crops")
    e("SR-11", "block stair 10 cm element: ROLE UNRESOLVED (balustrade wall or thin wall)", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json SPINE_WALL_BETWEEN_FLIGHTS", "CONFIRMED_AND_NARROWED",
      "STAIR_COMPONENT_REGISTER_V2: full-height wall roles excluded PROVISIONALLY by A-A (far flight visible); LOW_UPSTAND / BALUSTRADE_BASE / RAILING_SUPPORT / OTHER remain; never a plaster wall without role evidence", "A-A native; DWG dims 120/10/120 and 120/330/195")
    e("SR-12", "block stair walls per storey: 93.08 / 75.18 / 75.18 m2 gross PROVISIONAL", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2; A22-5-STAIR-WELL", "REOPENED",
      "demoted to GEOMETRIC_REFERENCE_ONLY (four faces x storey height = perimeter x storey); v2 faces carry exposure / openings / landing / occlusion fields", "STAIR_COMPONENT_REGISTER_V2")
    e("SR-13", "D1 dual basis (1.22 visible-finish / 1.40 executed), roof build-up information item", "D1_LEVEL_IDENTITY.json", "UNCHANGED", None, None)
    e("SR-14", "SW parapet from the SE elevation's end-on pier (~1.35 above the base line, PROPOSED)", "ROOF_EDGES_FACADE_FINISH_KERB.json SW", "UNCHANGED", None, None)
    e("SR-15", "wet-room lengths, project opening register, trade matrix, profile steel, floor-by-floor, coverage matrix", "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json", "UNCHANGED",
      "not dependent on the reception / void model (the GF reception faces were never in the wet-room or opening registers)", None)
    e("SR-16", "A22-5-COLUMN-FACES engineering 1.80 lm", "A22_RECONCILIATION_REGISTER_v5.json", "SUPERSEDED", "A22 v6 item with 0.75 / 0.85 lm", "COLUMN_VERTICAL_EXPOSURE_REGISTER")
    e("SR-17", "visual_qa/FF_VOID_STAIR.png annotation 'void 5.82 x 2.75'", "VISUAL_QA_PA02.json", "QUALIFIED", "DERIVED_QA_OVERLAY: the annotation is ours; the source page prints 587 x 400", "QA_RENDER_VALIDITY_REGISTER")
    return {"ARTIFACT": "PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER", "ENTRIES": L, "FROZEN_PA02_ARTIFACTS_REWRITTEN": False,
            "COUNTS": {s: sum(1 for x in L if x["STATUS"] == s) for s in sorted({x["STATUS"] for x in L})}}


def run() -> dict:
    n = _norm()
    segs, arcs = _index(n)
    void = void_reconciliation(n, segs, arcs)
    rv = reception_faces(segs, void)
    st = stair_v2(n, segs, arcs, void)
    col = column_vertical(segs)
    ne = ne_eligibility()
    se = se_ownership()
    led = ledger(void, rv, st, col, ne, se)
    shas = {}
    for name, body in (("VOID_GEOMETRY_RECONCILIATION", void), ("RECEPTION_VERTICAL_FACE_REGISTER", rv), ("STAIR_COMPONENT_REGISTER_V2", st),
                       ("COLUMN_VERTICAL_EXPOSURE_REGISTER", col), ("NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER", ne), ("SE_OPENING_DIMENSION_OWNERSHIP_AUDIT", se),
                       ("PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER", led)):
        body = dict({"PHASE_ID": P.PHASE_ID, "NORMALIZATION_HASH": n.normalization_hash(), "LAYER": "PA03_SOURCE_REVIEW_CORRECTION"}, **body)
        p = OUT / f"{name}.json"
        p.write_text(json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8")
        shas[name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return {"VOID": {k: (v["WIDTH_M"], v["DEPTH_M"]) for k, v in void["OBJECTS_PRESERVED"].items()}, "DOUBLE_HEIGHT": rv["DOUBLE_HEIGHT"],
            "COLUMN_GIRTH": col["COLUMNS"][0]["COLUMN_EXPOSED_GIRTH_LM"], "ELEMENT": st["STAIRS"][1]["MID_ELEMENT"]["ROLE"], "LEDGER": led["COUNTS"], "SHA": shas}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
