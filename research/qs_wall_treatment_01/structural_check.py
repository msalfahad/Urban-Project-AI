"""STRUCTURAL SOURCE CHECK (directive §7, §21): ST7757.pdf (vector, 16
sheets, exact 1:100 plots) registered to the architectural DWG by the
column pattern. Answers D2 in three separate statements and records the
SE roof-edge structure. ST7757.dwg itself stays PRESENT_NOT_DECODED (no
LibreDWG in this container; GitHub blocked by the network policy).

    python3 -m research.qs_wall_treatment_01.structural_check
"""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

import pymupdf

from engine import cad_adapter as CA
from engine import structural_registration as SR
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
ST_PDF = UPLOADS / "96ccda3b-ST7757.pdf"
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
GF_WINDOW = ((-166000, -124000), (-806000, -790000))
D2_LOOP = (-134770, -803794, -134170, -803544)          # E1.4 LOOP-059 (architectural S-COL.BON)
SALOON_FACE_Y = -805093.5                                # neighbour-wall inner face (owner-verified 515 run)
STUB_X = -134219.9                                       # CAD-783 line at the open edge


def _gf_loops(n):
    segs = [p for p in n.primitives if p.kind == "SEGMENT" and p.provenance.layer == "S-COL.BON"
            and GF_WINDOW[0][0] < p.x1 < GF_WINDOW[0][1] and GF_WINDOW[1][0] < p.y1 < GF_WINDOW[1][1]]
    key = lambda x, y: (round(x), round(y))
    adj = collections.defaultdict(set)
    for i, s in enumerate(segs):
        adj[key(s.x1, s.y1)].add(i)
        adj[key(s.x2, s.y2)].add(i)
    seen, loops = set(), []
    for i in range(len(segs)):
        if i in seen:
            continue
        stack, comp = [i], []
        while stack:
            j = stack.pop()
            if j in seen:
                continue
            seen.add(j)
            comp.append(j)
            s = segs[j]
            stack.extend(adj[key(s.x1, s.y1)])
            stack.extend(adj[key(s.x2, s.y2)])
        xs = [c for j in comp for c in (segs[j].x1, segs[j].x2)]
        ys = [c for j in comp for c in (segs[j].y1, segs[j].y2)]
        l = (round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))
        if 150 < l[2] - l[0] < 1300 and 150 < l[3] - l[1] < 1300:
            loops.append(l)
    return sorted(loops)


def _items_near(page, px, py, r_pt):
    out = []
    for dr in page.get_drawings():
        rc = dr["rect"]
        if rc.x0 < px + r_pt and rc.x1 > px - r_pt and rc.y0 < py + r_pt and rc.y1 > py - r_pt and rc.width < 150 and rc.height < 150:
            out.append({"RECT_PT": [round(rc.x0, 1), round(rc.y0, 1), round(rc.x1, 1), round(rc.y1, 1)],
                        "WIDTH": dr.get("width"), "FILL": dr.get("fill"),
                        "ITEMS": [(it[0],) + tuple(round(v, 1) for pt in it[1:] if hasattr(pt, "x") for v in (pt.x, pt.y)) for it in dr["items"]][:6]})
    return out


def _tower_roof_outline(page, region=(400, 480, 640, 750), heavy=1.5):
    """The +13.90 slab outline on the SECOND FLOOR ROOF SLAB sheet: heavy
    lines lying on the boundary of the heavy-line bbox inside the region;
    developed length is the sum of those authored segments (the small
    step at the top edge included), never 2*(W+H)."""
    S = SR.PT_MM_AT_1_100
    segs = []
    for dr in page.get_drawings():
        if (dr.get("width") or 0) < heavy:
            continue
        for it in dr["items"]:
            if it[0] != "l":
                continue
            a, b = it[1], it[2]
            if all(region[0] <= v.x <= region[2] and region[1] <= v.y <= region[3] for v in (a, b)):
                segs.append((a.x, a.y, b.x, b.y))
    if not segs:
        return {"STATUS": "NOT_FOUND"}
    xs = [v for s in segs for v in (s[0], s[2])]
    ys = [v for s in segs for v in (s[1], s[3])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    on = lambda v, t: abs(v - t) <= 3.0
    outline = []
    for s in segs:
        L = ((s[0] - s[2]) ** 2 + (s[1] - s[3]) ** 2) ** 0.5
        boundary = ((on(s[0], x0) and on(s[2], x0)) or (on(s[0], x1) and on(s[2], x1))
                    or (on(s[1], y0) and on(s[3], y0)) or (on(s[1], y1) and on(s[3], y1)))
        if boundary and L > 1.0:
            outline.append({"PT": [round(v, 1) for v in s], "LENGTH_M": round(L * S / 1000, 3)})
    # dedupe identical segments
    seen, uniq = set(), []
    for o in outline:
        k = tuple(o["PT"])
        if k in seen or tuple(reversed(k)) in seen:
            continue
        seen.add(k)
        uniq.append(o)
    # exterior ring of the polygonized heavy-line set: interior beams cannot
    # change it, overlapping boundary pieces are not double counted
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    lines = unary_union([LineString([(s[0], s[1]), (s[2], s[3])]) for s in segs])
    polys = list(polygonize(lines))
    dev = None
    if polys:
        big = max(polys, key=lambda g: g.area)
        outer = unary_union(polys)
        ring = outer.exterior if outer.geom_type == "Polygon" else max(outer.geoms, key=lambda g: g.area).exterior
        dev = round(ring.length * S / 1000, 3)
    return {"STATUS": "FOUND", "EXTERIOR_RING_METHOD": "shapely polygonize of the heavy lines; exterior ring length", "BBOX_PT": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
            "BBOX_M": [round((x1 - x0) * S / 1000, 3), round((y1 - y0) * S / 1000, 3)],
            "OUTLINE_SEGMENTS": uniq, "DEVELOPED_PERIMETER_M": dev,
            "RECTANGLE_PERIMETER_FOR_COMPARISON_M": round(2 * ((x1 - x0) + (y1 - y0)) * S / 1000, 3),
            "SOURCE_TIER": "VECTOR_DRAWING_GEOMETRY (1:100 plot)", "CORRESPONDENCE": "PROPOSED_CORRESPONDENCE",
            "WHAT": "the +13.90 slab edge on which the tower parapet ring (A-A PAR-08/09, SE PAR-10) stands"}


def run() -> dict:
    d = json.loads(Path(DECODE).read_text("utf-8"))
    n = CA.normalize(d, source_file="P7757_ARCHITECTURAL.dwg")
    loops = _gf_loops(n)
    doc = pymupdf.open(str(ST_PDF))
    sha = hashlib.sha256(ST_PDF.read_bytes()).hexdigest()
    p1 = doc[0]
    reg = SR.register(loops, SR.column_rects(p1))
    d2c = ((D2_LOOP[0] + D2_LOOP[2]) / 2, (D2_LOOP[1] + D2_LOOP[3]) / 2)
    px, py = SR.to_pdf(reg, *d2c)
    st_col = [m for m in reg["MATCHES"] if abs(m["CAD_CENTRE_MM"][0] - d2c[0]) < 200 and abs(m["CAD_CENTRE_MM"][1] - d2c[1]) < 200]
    # beams at the D2 column on the ground-beams sheet (p3) and the GF roof-slab sheet (p4)
    beams = {}
    for pi, name in ((2, "GROUND_BEAMS_PLAN_p3"), (3, "GROUND_FLOOR_ROOF_SLAB_p4")):
        pg = doc[pi]
        heavy = []
        for dr in pg.get_drawings():
            w = dr.get("width") or 0
            if w < 1.0:
                continue
            if dr['rect'].width < 12 and dr['rect'].height < 12:
                continue
            for it in dr["items"]:
                if it[0] == "l":
                    a, b = it[1], it[2]
                    if min(a.x, b.x) < px + 80 and max(a.x, b.x) > px - 80 and min(a.y, b.y) < py + 40 and max(a.y, b.y) > py - 40:
                        ca, cb = SR.to_cad(reg, a.x, a.y), SR.to_cad(reg, b.x, b.y)
                        heavy.append({"PT": [round(a.x, 1), round(a.y, 1), round(b.x, 1), round(b.y, 1)], "WIDTH_PT": w,
                                      "CAD_FROM_MM": [round(ca[0]), round(ca[1])], "CAD_TO_MM": [round(cb[0]), round(cb[1])],
                                      "LENGTH_M": round(((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5 / 1000, 3)})
        beams[name] = heavy
    # SE roof edge on the roof-slab sheets (p5 first-floor roof slab = +9.70; p6 second-floor roof slab)
    edge = {}
    for pi, name in ((4, "FIRST_FLOOR_ROOF_SLAB_p5"), (5, "SECOND_FLOOR_ROOF_SLAB_p6")):
        pg = doc[pi]
        rows = []
        for dr in pg.get_drawings():
            rc = dr["rect"]
            if 268 <= rc.x0 and rc.x1 <= 495 and 360 <= rc.y0 and rc.y1 <= 392:
                rows.append({"RECT_PT": [round(rc.x0, 1), round(rc.y0, 1), round(rc.x1, 1), round(rc.y1, 1)],
                             "WIDTH": dr.get("width"), "FILL": dr.get("fill"),
                             "ITEMS": [(it[0],) + tuple(round(v, 1) for pt in it[1:] if hasattr(pt, "x") for v in (pt.x, pt.y)) for it in dr["items"]][:5]})
        edge[name] = rows
    S = SR.PT_MM_AT_1_100
    tower = _tower_roof_outline(doc[5])
    out = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "STRUCTURAL_SOURCE_CHECK",
        "SOURCE": {"FILE": ST_PDF.name, "SHA256": sha, "PAGES": len(doc), "KIND": "VECTOR_PDF_PLOT_1_100",
                   "SOURCE_TIER": "VECTOR_DRAWING_GEOMETRY (below DWG authored geometry, above printed dimension)",
                   "ST7757_DWG": "PRESENT_NOT_DECODED (no LibreDWG in this container; network policy blocks GitHub)",
                   "SHEETS": {"p1": "COLUMN & AXIS PLAN", "p3": "GROUND BEAMS PLAN", "p4": "GROUND FLOOR ROOF SLAB",
                              "p5": "FIRST FLOOR ROOF SLAB (+9.70 terrace)", "p6": "SECOND FLOOR ROOF SLAB (+13.90)",
                              "p7": "DETAILS (swimming pool, dome)", "p9": "schedules"},
                   "NOTE_ON_SHEETS_p4_p5_p6": "'CHECK ARCHITECTURAL DETAIL OF PARAPET BEFORE CASTING' - the "
                                              "parapet is deferred to the architectural set by the engineer"},
        "REGISTRATION_p1": reg,
        "D2": {
            "LOCATION": {"CAD_LOOP_MM": D2_LOOP, "PDF_PT": [round(px, 2), round(py, 2)]},
            "COLUMN_EXISTS": {"STATUS": "ESTABLISHED", "EVIDENCE": st_col,
                              "SOURCE_INDEPENDENCE": "structural set (different author discipline) + architectural S-COL.BON loop"},
            "COLUMN_EXPOSED_TO_ROOM": {
                "STATUS": "ESTABLISHED_PROVISIONAL",
                "WHY": f"the column stands {round((D2_LOOP[1] - SALOON_FACE_Y) / 1000, 2)} m off the neighbour-wall face; "
                       "no wall is drawn around it on the architectural GF plan (the only lines at it are the "
                       "S-COL.BON loop, the layer-5 stub line and a layer-2 line); the structural sheets show beams "
                       "to it, not walls",
                "FACES_EXPOSED": 4, "GIRTH_LM_STRUCTURAL": round(2 * (0.30 + 0.60), 2),
                "GIRTH_LM_ARCHITECTURAL_LOOP": round(2 * ((D2_LOOP[2] - D2_LOOP[0]) + (D2_LOOP[3] - D2_LOOP[1])) / 1000, 2),
                "RESIDUAL": "structural 30 x 60 vs architectural loop 25 x 60: the plaster girth is 1.80 or 1.70 lm; "
                            "finish thickness and any cladding are NOT_ESTABLISHED"},
            "COLUMN_OWNS_CLEAR_FINISH_FACE": {
                "STATUS": "NO",
                "WHY": "the SALOON clear face (owner-verified 515 run on the neighbour wall) passes 1.3 m from the "
                       "column; the room boundary is not deformed around it (E1.4 finding kept)"},
            "STUB_LINE_CAD_783": {
                "CLASSIFICATION": "E_LEVEL_OR_REFERENCE_LINE: overhead beam line (GF roof-slab beam from the wall "
                                  "to the column, sheet p4), drawn dashed on the raster",
                "STATUS": "PROPOSED", "EVIDENCE": beams},
            "CLASSIFICATION_A_TO_F": {"A_HIDDEN_STRUCTURAL_COLUMN": False, "B_EXPOSED_STRUCTURAL_COLUMN": True,
                                      "C_ARCHITECTURAL_PIER": False, "D_WALL_TERMINATION": False,
                                      "E_FLOOR_LEVEL_REFERENCE_LINE": "the 1.3 m line only",
                                      "F_OTHER": False},
            "D2_STATUS": "RESOLVED_PROVISIONAL_BY_STRUCTURAL_SOURCE",
            "E1_4_STATEMENT_NOT_EXPOSED_TO_ROOM": "SUPERSEDED_IN_PART (forward layer; E1.4 frozen output untouched)",
            "PLASTER_CONSEQUENCE": "COLUMN_BONDING + plaster on 4 exposed faces, girth 1.80 lm (structural) / 1.70 lm "
                                   "(architectural loop), height = SALOON normal height (owner 3.20) -> OWNER_PARAMETRIC; "
                                   "no room boundary change",
        },
        "SE_ROOF_EDGE_STRUCTURE": {
            "SHEET_p5_p6_EDGE_ITEMS": edge,
            "OUTER_EDGE_LENGTH_M": round((485.4 - 272.9) * S / 1000, 3),
            "PARAPET_THICKNESS_M": round((378.1 - 372.3) * S / 1000, 3),
            "TICKS_FROM_NE_CORNER_M": [round((321.3 - 272.9) * S / 1000, 3), round((398.7 - 272.9) * S / 1000, 3)],
            "TICKS_FROM_SW_CORNER_M": [round((489.3 - 398.7) * S / 1000, 3), round((489.3 - 321.3) * S / 1000, 3)],
            "UPSTAND_DETAIL_SECTION_B_B_p5": {"BEAM_WIDTH_CM": 45, "SPLIT_CM": [25, 20], "BEAM_DEPTH_CM": 75,
                                              "UPSTAND_HEIGHT_CM": 20, "BARS": ["3d18 top", "11d18"],
                                              "WHERE_CALLED": "B marker at the SW-edge hatched beam (top-left of the +9.70 slab)",
                                              "RELATION_TO_SE_EDGE": "PROPOSED (same edge-beam family; not cut on the SE edge)"},
            "MATERIAL_CONSEQUENCE": "the roof edge is an RC edge beam with a 20 cm RC upstand; the parapet above is "
                                    "per the architectural detail (blockwork or RC, plasterable either way): "
                                    "SOLID_MASONRY_OR_RC for the solid portions, PROVISIONAL",
        },
        "TOWER_ROOF_13_90_OUTLINE_p6": tower,
        "WHAT_THIS_SOURCE_MAY_NOT_DO": "corroborate geometry only; it is the same design family, not site truth; "
                                       "no benchmark value was used to place, size or select anything here",
    }
    p = OUT / "STRUCTURAL_SOURCE_CHECK.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    out["_SHA256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({"REG": {k: r["REGISTRATION_p1"][k] for k in ("STATUS", "INLIERS", "MAX_RESIDUAL_MM", "A_MM", "B_MM")},
                      "D2": {k: r["D2"][k]["STATUS"] for k in ("COLUMN_EXISTS", "COLUMN_EXPOSED_TO_ROOM", "COLUMN_OWNS_CLEAR_FINISH_FACE")},
                      "EVIDENCE": r["D2"]["COLUMN_EXISTS"]["EVIDENCE"],
                      "BEAMS": {k: len(v) for k, v in r["D2"]["STUB_LINE_CAD_783"]["EVIDENCE"].items()},
                      "EDGE": {k: r["SE_ROOF_EDGE_STRUCTURE"][k] for k in ("OUTER_EDGE_LENGTH_M", "PARAPET_THICKNESS_M", "TICKS_FROM_SW_CORNER_M")},
                      "SHA": r["_SHA256"]}, indent=1))
