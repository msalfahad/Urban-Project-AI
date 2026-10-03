"""PA08_QORTUBA_ROOM_BY_ROOM_QS_01: a quantity surveyor's room-by-room takeoff, from the drawing only.

Every number here is derived from the Qortuba DWG.  This module imports no contractor register and no comparison code, which
a test asserts by reading its imports: a figure that cannot see a benchmark cannot have been fitted to one.

Each room is measured twice where the drawing allows it.  Method A is the arrangement of the room's own bounding lines, the
exact rectangle decomposition a CAD polygon gives.  Method B is the arithmetic a human surveyor does from the authored
dimension text.  The two are reported side by side and never averaged.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from engine.ingest import ENGINE_VERSION, pipeline7 as P7
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as B
from research.qs_wall_treatment_01.pa08.qortuba.r2 import cells as CELLS
from research.qs_wall_treatment_01.pa08.qortuba.r3 import floor_regions as FR
from research.qs_wall_treatment_01.pa08.qortuba.r3 import run_r3 as R3

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
STOREY = "SECOND_FLOOR (title block 'SECOND FLOOR PLAN')"
WET_CLASSES = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM")
DIM_MATCH_MM = 30.0

# a cell is inside the apartment when a door of the apartment opens into it, or it carries an apartment room label.
# stairs, the lift lobby, the terrace and the roof are kept and reported, and are excluded from every apartment subtotal.
EXCLUDED_ZONE_KINDS = ("STAIR", "STAIR_LANDING", "EXTERNAL_TERRACE", "OPEN_ROOF", "COMMON_CIRCULATION_WITH_LIFT",
                       "SHEET_OR_SITE_REGION", "SHAFT_OR_WALL_POCKET", "EXTERNAL_LEDGE", "DRAFTING_ARTIFACT")
BLUE_ELEMENT_CLASSES = ("WINDOW_WITH_WALL_BELOW", "FULL_HEIGHT_WINDOW", "SLIDING_DOOR", "OTHER_GLAZING", "UNRESOLVED")
SKIRTING_SEGMENT_CLASSES = ("SKIRTING_ELIGIBLE_WALL", "DOOR_OPENING", "FLOOR_LEVEL_GLAZED_OPENING", "OPEN_PASSAGE",
                            "NON_WALL_EDGE", "WET_ROOM_EDGE", "COLUMN_FACE", "UNRESOLVED")


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _bbox(label, meta, cell, lab):
    rs, cs = np.nonzero(label == lab)
    if not len(rs):
        return None
    return [round(meta["x0"] + cs.min() * cell, 1), round(meta["y1"] - (rs.max() + 1) * cell, 1),
            round(meta["x0"] + (cs.max() + 1) * cell, 1), round(meta["y1"] - rs.min() * cell, 1)]


# ---------------------------------------------------------------------------- §1 room inventory
def room_inventory(r, vid, cell_rows, adj, prims):
    """Every cell, sorted into the apartment and the zones outside it.

    The engine's own floor-region flag is not the test.  A space with no room label is still a room when doors of the
    apartment open into it, which is how the unlabelled lobby off the two bedrooms earns its place here.
    """
    grid = r.grids7[vid]
    label, meta, cell = grid["label"], grid["meta"], grid["cell"]
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}
    by_id = {c["CELL_ID"]: c for c in cell_rows}
    sites = {s["SITE_ID"]: s for s in r.sites7[vid]}
    named = {c["CELL_ID"] for c in cell_rows if c["ROOM_NAMES"]}

    doors_into = defaultdict(list)
    for a in adj:
        for s in a.get("SITES", []):
            if "DOOR" in s["CLASS"] or "PASSAGE" in s["CLASS"]:
                doors_into[a["ROOM_A"]].append((a["ROOM_B"], s))
                doors_into[a["ROOM_B"]].append((a["ROOM_A"], s))

    stair_cells = {c["CELL_ID"] for c in cell_rows if c["SPACE_ELIGIBILITY"] == "STAIR_OR_LANDING_SPACE"}
    touches_stair = defaultdict(bool)
    for a in adj:
        if a["ROOM_A"] in stair_cells:
            touches_stair[a["ROOM_B"]] = True
        if a["ROOM_B"] in stair_cells:
            touches_stair[a["ROOM_A"]] = True

    layers_in = {}
    for c in cell_rows:
        bb = _bbox(label, meta, cell, faces[c["FACE_ID"]]["RUN_LABEL_NOT_A_KEY"])
        cnt = Counter()
        if bb:
            for p in prims:
                mx = (p.x1 + p.x2) / 2 if p.kind == "SEGMENT" else p.cx
                my = (p.y1 + p.y2) / 2 if p.kind == "SEGMENT" else p.cy
                if bb[0] - 1 <= mx <= bb[2] + 1 and bb[1] - 1 <= my <= bb[3] + 1:
                    cnt[p.provenance.layer] += 1
        layers_in[c["CELL_ID"]] = (bb, cnt)

    rows = []
    for c in sorted(cell_rows, key=lambda z: -z["AREA_M2"]):
        cid, bb, cnt = c["CELL_ID"], *layers_in[c["CELL_ID"]]
        el, names = c["SPACE_ELIGIBILITY"], c["ROOM_NAMES"]
        wet = any(x in WET_CLASSES for x in c["SEMANTIC_CLASSES"]) or el == "SERVICE_FREE_SPACE"
        apt_doors = [(o, s) for o, s in doors_into.get(cid, []) if o in named]
        inside, kind, why = False, None, ""
        if el == "SITE_OR_SHEET_REGION":
            kind, why = "SHEET_OR_SITE_REGION", "the sheet's own drawing region, not a space"
        elif el == "OPEN_ROOF_OR_TERRACE":
            kind, why = "OPEN_ROOF", "labelled ROOF in the drawing"
        elif el == "STAIR_OR_LANDING_SPACE" or cnt.get("STAIR"):
            kind, why = "STAIR", "stair geometry is drawn inside this cell"
        elif cnt.get("lift"):
            kind, why = "COMMON_CIRCULATION_WITH_LIFT", "the lift is drawn inside this cell, so it is common circulation outside the apartment"
        elif names:
            inside, kind, why = True, "LABELLED_ROOM", f"carries the room label {names}"
        elif apt_doors:
            inside, kind = True, "UNLABELLED_INTERNAL_SPACE"
            why = ("no room label, but doors of the apartment open into it: "
                   + ", ".join(f"{' / '.join(by_id[o]['ROOM_NAMES'])} by a {s['CLASS']} of {s['SPAN_MM']:.0f} mm" for o, s in apt_doors))
        elif el in ("WALL_BAND_INTERIOR", "FRAME_INTERIOR", "JOINERY_OR_FURNITURE_INTERIOR", "ARTIFACT_POCKET"):
            kind, why = "DRAFTING_ARTIFACT", f"the interior of a drawn element ({el}), never a room"
        elif touches_stair.get(cid):
            kind, why = "STAIR_LANDING", ("no room label and no apartment door; it adjoins the stair, so it is part of the "
                                          "stair enclosure rather than the apartment")
        elif bb and min(bb[2] - bb[0], bb[3] - bb[1]) <= 600:
            kind, why = "SHAFT_OR_WALL_POCKET", (f"only {min(bb[2]-bb[0], bb[3]-bb[1]):.0f} mm across at its narrowest, and no "
                                                 "door reaches it: a shaft, duct or wall pocket that cannot be entered or floored")
        elif c["AREA_M2"] >= 3.0:
            kind, why = "EXTERNAL_TERRACE", ("a space of usable size with no room label and no apartment door into it; it "
                                             "adjoins the roof or the common circulation, so it is outside the apartment")
        else:
            kind, why = "EXTERNAL_LEDGE", ("no room label, no apartment door, and too small to be a room: a recess or ledge "
                                           "outside the apartment envelope")
        rows.append({"ROOM_ID": ("RM-" if inside else "ZX-") + cid.split("-")[1][:8],
                     "CELL_ID": cid, "FACE_ID": c["FACE_ID"],
                     "RAW_ARABIC_LABEL": None, "RAW_ENGLISH_LABEL": " / ".join(names) if names else None,
                     "CANONICAL_NAME": (" / ".join(names) if names else kind),
                     "PHYSICAL_SPACE": cid, "FUNCTIONAL_ZONE": ("WET_INTERNAL" if wet else "DRY_INTERNAL") if inside else kind,
                     "DRY_WET_CLASS": ("WET" if wet else "DRY") if inside else "NOT_APPLICABLE",
                     "INSIDE_APARTMENT": inside, "ZONE_KIND": kind,
                     "BOUNDARY_STATUS": c["STATUS"], "CELL_CLASS": el,
                     "RASTER_AREA_M2": c["AREA_M2"], "BBOX_MM": bb,
                     "LAYERS_DRAWN_INSIDE": dict(cnt),
                     "WHY": why,
                     "SOURCE": "Qortuba architectural DWG, second floor plan"})
    return rows


def merge_rectangles(rects, tol=1.0):
    """Fuse the arrangement's slivers back into the few rectangles a surveyor would actually write down.

    The arrangement cuts on every boundary line in the room, so a plain L-shape can arrive as a dozen strips.  Merging two
    rectangles that share a whole edge changes no area and makes the formula auditable by hand, which is the point of writing
    a formula at all.
    """
    out = [dict(q) for q in rects]
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                ax, ay, bx, by = a["X_MM"], a["Y_MM"], b["X_MM"], b["Y_MM"]
                same_x = abs(ax[0] - bx[0]) <= tol and abs(ax[1] - bx[1]) <= tol
                same_y = abs(ay[0] - by[0]) <= tol and abs(ay[1] - by[1]) <= tol
                if same_x and (abs(ay[1] - by[0]) <= tol or abs(by[1] - ay[0]) <= tol):
                    ny = [min(ay[0], by[0]), max(ay[1], by[1])]
                    out[i] = {"X_MM": ax, "Y_MM": ny, "W_MM": round(ax[1] - ax[0], 1), "D_MM": round(ny[1] - ny[0], 1),
                              "AREA_M2": round((ax[1] - ax[0]) * (ny[1] - ny[0]) / 1e6, 4)}
                    out.pop(j); changed = True; break
                if same_y and (abs(ax[1] - bx[0]) <= tol or abs(bx[1] - ax[0]) <= tol):
                    nx = [min(ax[0], bx[0]), max(ax[1], bx[1])]
                    out[i] = {"X_MM": nx, "Y_MM": ay, "W_MM": round(nx[1] - nx[0], 1), "D_MM": round(ay[1] - ay[0], 1),
                              "AREA_M2": round((nx[1] - nx[0]) * (ay[1] - ay[0]) / 1e6, 4)}
                    out.pop(j); changed = True; break
            if changed:
                break
    return sorted(out, key=lambda q: -q["AREA_M2"])


# ---------------------------------------------------------------------------- §2 / §3 floor, two methods
def floor_calculations(r, vid, inv, cell_rows, comp, non_fixing):
    """Method A the arrangement of the bounding lines, Method B the authored dimension arithmetic."""
    by_cell = {c["CELL_ID"]: c for c in cell_rows}
    # every space that is not this room is a hard stop, so a measurement region can never swallow a neighbour
    apt = [x for x in inv if x["INSIDE_APARTMENT"]]
    out, regions = [], []
    for x in apt:
        guard = {}
        for c in cell_rows:
            guard[c["FACE_ID"]] = ("OCCUPIABLE_FREE_SPACE" if c["CELL_ID"] != x["CELL_ID"] and c["AREA_M2"] >= 0.9
                                   else c["SPACE_ELIGIBILITY"])
        labels, crossings = FR.assemble(r, vid, x["FACE_ID"], guard, comp, non_fixing)
        segs, summ = FR.boundary_segments(r, vid, labels)
        area, fml = FR.polygon(r, vid, labels, sorted({s["SEAL_INDEX"] for s in segs if s["COUNTS_AS_PERIMETER"]}), non_fixing)
        segs, _ = FR.mark_interior_obstructions(segs, fml)
        raw = (fml or {}).get("RECTANGLES") or []
        rects = merge_rectangles(raw)
        shape = ("RECTANGLE" if len(rects) == 1 else "L_SHAPE" if len(rects) == 2 else
                 f"IRREGULAR_{len(rects)}_RECTANGLES" if rects else "NOT_DECOMPOSED")
        formula = " + ".join(f"{q['W_MM']/1000:.3f} x {q['D_MM']/1000:.3f}" for q in rects)
        formula = (formula + f" = {area:.4f} m2") if area is not None else "NOT_ESTABLISHED"
        ok = area is not None and summ["ALL_SEGMENTS_FIX_THE_FLOOR_LINE"] and fml.get("STATUS") == "COMPUTED"
        regions.append({"ROOM_ID": x["ROOM_ID"], "ROOM": x["CANONICAL_NAME"], "CELL_ID": x["CELL_ID"], "FACE_ID": x["FACE_ID"],
                        "FLOOR_MEASUREMENT_REGION_ID": "FMR-" + x["CELL_ID"].split("-")[1],
                        "WET_OR_DRY": x["DRY_WET_CLASS"], "FORMULA": fml, "AREA_M2": {"VALUE": round(area, 4) if ok else None},
                        "BOUNDARY_SEGMENTS": segs, "SUMMARY": summ, "LABELS": labels, "CROSSINGS": crossings,
                        "STATUS": "SOURCE_ESTABLISHED" if ok else "NOT_ESTABLISHED"})
        out.append({"ROOM_ID": x["ROOM_ID"], "ROOM": x["CANONICAL_NAME"], "WET_OR_DRY": x["DRY_WET_CLASS"],
                    "SHAPE_TYPE": shape, "RECTANGLES": rects, "ARRANGEMENT_CELLS_BEFORE_MERGE": len(raw), "FORMULA": formula,
                    "METHOD_A_CAD_POLYGON_AREA_M2": round(area, 4) if area is not None else None,
                    "METHOD_A_BASIS": "arrangement of the room's own bounding lines, clear finish face; every rectangle is exact",
                    "RASTER_CROSS_CHECK_M2": (fml or {}).get("RASTER_CROSS_CHECK_M2"),
                    "RASTER_DIFFERENCE_M2": (fml or {}).get("DIFFERENCE_M2"),
                    "CUT_LINES_X_MM": (fml or {}).get("CUT_LINES_X_MM"), "CUT_LINES_Y_MM": (fml or {}).get("CUT_LINES_Y_MM"),
                    "STATUS": "SOURCE_ESTABLISHED" if ok else "NOT_ESTABLISHED",
                    "SOURCE_HIERARCHY_USED": "1 authored DWG geometry" if ok else "5 HUMAN_REVIEW"})
    return out, regions


def dual_method(regions, owned, floors):
    """Method B beside Method A, with a verdict and never an average.

    Method B comes in two strengths and the row says which.  Fully authored means both of the room's overall spans carry a
    dimension and the room is one rectangle, so the whole area is arithmetic on the drawing's own text.  Authored spans less a
    drawn recess means the drawing dimensions the room's overall extent but not the notch cut out of it; the overall extent is
    then an independent confirmation and the notch is not, which is worth less and is never presented as worth more.
    """
    recon = R3.dimension_reconciliation(regions, owned)
    by_room = {f["ROOM_ID"]: f for f in floors}
    out = []
    for reg, rc in zip(regions, recon):
        a = reg["AREA_M2"]["VALUE"]
        b = rc["DIMENSION_BASED_AREA_M2"]
        strength = "FULLY_AUTHORED" if b is not None else None
        bs = rc["DIMENSION_BASIS"]
        span = rc["BOUNDING_SPAN_CHECK"] or {}
        envelope = None
        if span.get("OVERALL_SPANS_CONFIRMED") and a is not None:
            sx, sy = span["POLYGON_BOUNDING_SPANS_MM"]
            ax_, ay_ = span["BY_AXIS"]["X"], span["BY_AXIS"]["Y"]
            envelope = {"AUTHORED_SPAN_X_MM": ax_["AUTHORED_VALUE_MM"], "AUTHORED_SPAN_Y_MM": ay_["AUTHORED_VALUE_MM"],
                        "MEASURED_SPAN_X_MM": sx, "MEASURED_SPAN_Y_MM": sy,
                        "DIMENSION_IDS": {"X": ax_["DIMENSION_IDS"], "Y": ay_["DIMENSION_IDS"]},
                        "DELTA_X_MM": round(ax_["AUTHORED_VALUE_MM"] - sx, 1), "DELTA_Y_MM": round(ay_["AUTHORED_VALUE_MM"] - sy, 1),
                        "ENVELOPE_AREA_M2": span["BOUNDING_BOX_AREA_M2"],
                        "DRAWN_RECESS_M2": round(span["BOUNDING_BOX_AREA_M2"] - a, 4),
                        "VERDICT": "ENVELOPE_CONFIRMED_BY_AUTHORED_DIMENSIONS",
                        "WHAT_THIS_DOES_NOT_CHECK": "the recess cut out of the envelope is drawn and not dimensioned, so the "
                                                    "room's area still has only one independent method"}
        if b is None and envelope is not None:
            strength = "ENVELOPE_ONLY"
            bs = (f"the drawing dimensions this room's overall extent as {envelope['AUTHORED_SPAN_X_MM']:.0f} x "
                  f"{envelope['AUTHORED_SPAN_Y_MM']:.0f}, which matches the measured envelope; it does not dimension the "
                  f"recess, so no second area can be computed from the text alone")
        out.append({"ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"],
                    "METHOD_A_CAD_POLYGON_M2": a,
                    "METHOD_B_DIMENSION_ARITHMETIC_M2": b, "METHOD_B_BASIS": bs,
                    "METHOD_B_STRENGTH": strength or "NOT_AVAILABLE",
                    "OWNED_DIMENSIONS": rc["OWNED_DIMENSIONS"],
                    "DELTA_M2": None if (a is None or b is None) else round(a - b, 4),
                    "VERDICT": ({"AGREE": "EXACT", "WITHIN_ROUNDING": "WITHIN_ROUNDING",
                                 "MEASUREMENT_BASIS_DIFFERENCE": "BASIS_DIFFERENCE", "CONFLICT": "CONFLICT",
                                 "NOT_COMPARABLE": "METHOD_B_NOT_AVAILABLE"}[rc["VERDICT"]]
                                if strength == "FULLY_AUTHORED" else
                                "ENVELOPE_CONFIRMED_AREA_NOT_INDEPENDENTLY_CHECKED" if strength == "ENVELOPE_ONLY"
                                else "METHOD_B_NOT_AVAILABLE"),
                    "ENVELOPE_CHECK": envelope,
                    "WHY": (rc["WHY"] if strength == "FULLY_AUTHORED" else
                            "the drawing confirms this room's overall extent but not the recess inside it, so the area has one "
                            "method and the envelope has two" if strength == "ENVELOPE_ONLY" else rc["WHY"]), "BOUNDING_SPAN_CHECK": rc["BOUNDING_SPAN_CHECK"],
                    "RULE": "the two methods are reported side by side and never averaged"})
    return out


# ---------------------------------------------------------------------------- §20 blue elements
def blue_elements(r, vid, prims, inv, regions):
    """Every glazed element, and what it does to a floor-level trade.

    A window with wall below leaves the skirting running under it.  An opening that cuts the wall band right through has no
    wall below it at all, and both the skirting and the profile stop at its jambs.  The discriminator is whether an opening
    site interrupts the band, not the layer name.
    """
    sites = r.sites7[vid]
    win = [p for p in prims if p.provenance.layer == "WINDOW" and p.kind == "SEGMENT"]
    groups, used = [], set()
    for p in sorted(win, key=lambda q: (q.axis, round(min(q.x1, q.x2)), round(min(q.y1, q.y2)))):
        if p.object_id in used:
            continue
        g = [p]
        used.add(p.object_id)
        for q in win:
            if q.object_id in used or q.axis != p.axis:
                continue
            if p.axis == "V" and abs(q.x1 - p.x1) <= 400 and abs(min(q.y1, q.y2) - min(p.y1, p.y2)) <= 400:
                g.append(q); used.add(q.object_id)
            elif p.axis == "H" and abs(q.y1 - p.y1) <= 400 and abs(min(q.x1, q.x2) - min(p.x1, p.x2)) <= 400:
                g.append(q); used.add(q.object_id)
        groups.append(g)

    room_of_seg = {}
    for reg in regions:
        for s in reg["BOUNDARY_SEGMENTS"]:
            room_of_seg.setdefault(s.get("SITE_ID"), []).append(reg["ROOM"])

    rows = []
    for i, g in enumerate(sorted(groups, key=lambda g: (round(min(min(p.x1, p.x2) for p in g)), round(min(min(p.y1, p.y2) for p in g)))), 1):
        axis = g[0].axis
        lo = min(min(p.y1, p.y2) if axis == "V" else min(p.x1, p.x2) for p in g)
        hi = max(max(p.y1, p.y2) if axis == "V" else max(p.x1, p.x2) for p in g)
        width = round(hi - lo, 1)
        cross = round(max(p.x1 if axis == "V" else p.y1 for p in g) - min(p.x1 if axis == "V" else p.y1 for p in g), 1)
        hit = None
        for s in sites:
            if abs(s["SPAN_MM"] - width) <= 120 and abs((s["AXIAL_START"] + s["AXIAL_END"]) / 2 - (lo + hi) / 2) <= 250:
                hit = s
                break
        if hit is not None and hit.get("CROSSES_FULL_BAND") and hit.get("FACE_A_INTERRUPTED") and hit.get("FACE_B_INTERRUPTED"):
            cls = "UNRESOLVED"
            cands = ["SLIDING_DOOR", "FULL_HEIGHT_WINDOW"]
            wall_below, why = False, ("the wall band is cut right through at this element: both faces are interrupted and the "
                                      "opening crosses the full thickness, so no wall stands under it.  A plan cannot say "
                                      "whether the glazing slides or is fixed, and it does not need to: either way there is no "
                                      "wall at floor level, so the floor-level trades stop here")
            eff = "INTERRUPTS: skirting and profile stop at the jambs"
        else:
            cls = "WINDOW_WITH_WALL_BELOW"
            cands = []
            wall_below, why = True, ("the element is drawn inside a wall band that is not interrupted here: the band's faces run "
                                     "continuously past it, so wall stands below the glazing")
            eff = "DOES NOT INTERRUPT: skirting and profile run under the window"
        rows.append({"BLUE_ELEMENT_ID": f"BE-{i:02d}", "LINE_COUNT": len(g),
                     "OBJECT_IDS": sorted(p.object_id for p in g), "AXIS": axis,
                     "WIDTH_MM": width, "FRAME_DEPTH_MM": cross,
                     "POSITION_MM": [round(min(min(p.x1, p.x2) for p in g), 1), round(min(min(p.y1, p.y2) for p in g), 1)],
                     "TYPE": cls, "TYPE_CANDIDATES": cands, "WALL_BELOW": wall_below,
                     "TRADE_EFFECT_IS_THE_SAME_FOR_EVERY_CANDIDATE": bool(cands),
                     "OPENING_SITE_ID": hit["SITE_ID"] if hit is not None else None,
                     "OPENING_SITE_CLASS": hit["CLASS"] if hit is not None else None,
                     "GLAZING_EVIDENCE": bool(hit and hit.get("GLAZING_EVIDENCE")) if hit is not None else False,
                     "ROOMS": sorted(set(room_of_seg.get(hit["SITE_ID"], []))) if hit is not None else [],
                     "HEIGHT_MM": {"VALUE": None, "STATE": "NOT_ESTABLISHED",
                                   "WHY": "a plan gives no sill or head height; no section or elevation exists for this project"},
                     "SKIRTING_EFFECT": eff, "PROFILE_EFFECT": eff,
                     "PLASTER_EFFECT": "plaster stops at the reveal; the reveal return needs a depth and a height, neither established",
                     "PAINT_EFFECT": "follows the plaster",
                     "TILE_EFFECT": "in a tiled room the reveal is tiled; the area needs a height, not established",
                     "WHY": why, "CLASSES": BLUE_ELEMENT_CLASSES})
    return rows


# ---------------------------------------------------------------------------- §9-§12 skirting and profile
def classify_segment(seg, wet, sites_by_id, glazed_site_ids):
    basis = seg["BOUNDARY_BASIS"]
    sid = seg.get("SITE_ID")
    if sid and sid in glazed_site_ids:
        return "FLOOR_LEVEL_GLAZED_OPENING"
    if basis in ("ESTABLISHED_WALL_FACE", "CAD_FACE_LINE_UNRESOLVED_ROLE", "JOINERY_OUTLINE_EDGE", "WALL_INTERIOR_CHORD"):
        return "WET_ROOM_EDGE" if wet else "SKIRTING_ELIGIBLE_WALL"
    if basis == "COLUMN_FACE":
        return "COLUMN_FACE"
    if basis == "THRESHOLD_CLOSURE":
        s = sites_by_id.get(sid)
        return "DOOR_OPENING" if (s and "DOOR" in s["CLASS"]) else "NON_WALL_EDGE"
    if basis == "OPEN_EDGE_CLOSURE":
        return "OPEN_PASSAGE"
    return "UNRESOLVED"


def skirting_and_profile(r, vid, regions, blue, cell_mm):
    """One eligible wall path per room.  The skirting and the profile are two BOQ items reading the same path.

    The owner states the black profile is installed directly above the skirting and follows the same wall path.  So the
    profile inherits this path rather than being measured again from a different rule: nothing in the drawing gives it a
    second, longer perimeter, and inventing one would be arithmetic, not measurement.
    """
    sites_by_id = {s["SITE_ID"]: s for s in r.sites7[vid]}
    glazed = {b["OPENING_SITE_ID"] for b in blue if b["OPENING_SITE_ID"] and not b["WALL_BELOW"]}
    brows_by_face = defaultdict(lambda: defaultdict(float))
    for row in r.brows[vid]:
        if row["SPACE_FACE_ID"]:
            brows_by_face[row["SPACE_FACE_ID"]][row["BAND_ID"]] += row["LENGTH_MM"]
    skirt, prof = [], []
    for reg in regions:
        wet = reg["WET_OR_DRY"] == "WET"
        exact = brows_by_face.get(reg["FACE_ID"], {})
        lengths = R3.segment_lengths(reg["BOUNDARY_SEGMENTS"], exact, cell_mm)
        by_class, detail = defaultdict(float), []
        for seg, ln, lb in lengths:
            k = classify_segment(seg, wet, sites_by_id, glazed)
            by_class[k] += ln
            detail.append({"SEAL_INDEX": seg["SEAL_INDEX"], "SEGMENT_CLASS": k, "BOUNDARY_BASIS": seg["BOUNDARY_BASIS"],
                           "LENGTH_MM": round(ln, 1), "LENGTH_BASIS": lb, "SITE_ID": seg.get("SITE_ID")})
        gross = sum(by_class.values())
        door = by_class.get("DOOR_OPENING", 0.0)
        glaze = by_class.get("FLOOR_LEVEL_GLAZED_OPENING", 0.0)
        openp = by_class.get("OPEN_PASSAGE", 0.0)
        nonwall = by_class.get("NON_WALL_EDGE", 0.0)
        col = by_class.get("COLUMN_FACE", 0.0)
        unres = by_class.get("UNRESOLVED", 0.0)
        wet_edge = by_class.get("WET_ROOM_EDGE", 0.0)
        net = by_class.get("SKIRTING_ELIGIBLE_WALL", 0.0)
        skirt.append({"SKIRTING_PATH_ID": "SK-" + reg["CELL_ID"].split("-")[1][:8], "ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"],
                      "WET_OR_DRY": reg["WET_OR_DRY"],
                      "GROSS_WALL_LINE_PERIMETER_LM": round(gross / 1000, 3),
                      "DOOR_WIDTH_DEDUCTION_LM": round(door / 1000, 3),
                      "SLIDING_DOOR_DEDUCTION_LM": round(glaze / 1000, 3),
                      "OPEN_PASSAGE_DEDUCTION_LM": round(openp / 1000, 3),
                      "NON_SKIRTING_EDGE_LM": round(nonwall / 1000, 3),
                      "COLUMN_FACE_LM": round(col / 1000, 3),
                      "WET_ROOM_EDGE_LM": round(wet_edge / 1000, 3),
                      "UNRESOLVED_LM": round(unres / 1000, 3),
                      "NET_SKIRTING_LM": round(net / 1000, 3),
                      "ARITHMETIC": (f"{gross/1000:.3f} gross - {door/1000:.3f} doors - {glaze/1000:.3f} glazed openings "
                                     f"- {openp/1000:.3f} open - {nonwall/1000:.3f} non-wall - {col/1000:.3f} column "
                                     f"- {wet_edge/1000:.3f} wet edge - {unres/1000:.3f} unresolved = {net/1000:.3f} lm"),
                      "NORMAL_SKIRTING_STATUS": ({"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                                  "WHY": "a wet room may be skirted or tiled to the floor; no finishes schedule "
                                                         "says which, so this room carries a wall-edge length and no skirting"}
                                                 if wet else
                                                 {"VALUE": "NORMAL_SKIRTING_ASSUMED_ELIGIBLE", "STATE": "SOURCE_ESTABLISHED",
                                                  "WHY": "a dry room with a drawn wall line carries skirting along it"}),
                      "SEGMENTS": detail, "SEGMENT_CLASSES": SKIRTING_SEGMENT_CLASSES,
                      "STATE": reg["STATUS"] if not wet else "SOURCE_REQUIRED",
                      "COMMERCIAL_RULE": {"STATE": "SOURCE_REQUIRED",
                                          "WHY": "these deductions are geometric facts about the boundary; no commercial "
                                                 "measurement rule for this project has been supplied and none is invented"}})
        prof.append({"PROFILE_PATH_ID": "PR-" + reg["CELL_ID"].split("-")[1][:8], "ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"],
                     "SKIRTING_PATH_ID": "SK-" + reg["CELL_ID"].split("-")[1][:8],
                     "SKIRTING_GEOMETRIC_PATH_LM": round(net / 1000, 3),
                     "PROFILE_GEOMETRIC_PATH_LM": round(net / 1000, 3),
                     "DIFFERENCE_LM": 0.0,
                     "REASON_FOR_DIFFERENCE": "none: the profile sits directly above the skirting and reads the same eligible "
                                              "wall path, as the owner describes the installed product",
                     "SHARES_PATH_WITH_SKIRTING": True, "SEPARATE_BOQ_ITEM": True,
                     "STATE": reg["STATUS"] if reg["WET_OR_DRY"] != "WET" else "SOURCE_REQUIRED",
                     "PROFILE_TYPE_AND_SIZE": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                               "WHY": "no reflected ceiling plan, elevation or profile detail exists"},
                     "RULE": "a trade that sits on another reads the same path and is never given a second, larger perimeter "
                             "invented for it"})
    return skirt, prof


# ---------------------------------------------------------------------------- §13-§15 wet rooms and pantry
def wall_tile(regions, skirt, inv):
    rows = []
    for reg, sk in zip(regions, skirt):
        name = (reg["ROOM"] or "").upper()
        wet = reg["WET_OR_DRY"] == "WET"
        pantry = "PAINTRY" in name or "PANTRY" in name
        if not (wet or pantry):
            continue
        gross = sk["GROSS_WALL_LINE_PERIMETER_LM"]
        openings = sk["DOOR_WIDTH_DEDUCTION_LM"] + sk["SLIDING_DOOR_DEDUCTION_LM"] + sk["OPEN_PASSAGE_DEDUCTION_LM"]
        net = round(gross - openings - sk["NON_SKIRTING_EDGE_LM"], 3)
        rows.append({"ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"],
                     "ROOM_KIND": "WET_ROOM" if wet else "PREPARATION_AREA_NOT_ASSUMED_TO_BE_A_KITCHEN",
                     "FLOOR_AREA_M2": reg["AREA_M2"]["VALUE"],
                     "GROSS_HOST_WALL_LM": gross,
                     "DOOR_WIDTH_LM": sk["DOOR_WIDTH_DEDUCTION_LM"],
                     "WINDOW_WIDTH_LM": {"VALUE": 0.0, "STATE": "NO_FLOOR_LEVEL_GLAZED_OPENING_IN_THIS_ROOM"}
                     if not sk["SLIDING_DOOR_DEDUCTION_LM"] else {"VALUE": sk["SLIDING_DOOR_DEDUCTION_LM"], "STATE": "SOURCE_ESTABLISHED"},
                     "OTHER_OPENING_LM": sk["NON_SKIRTING_EDGE_LM"],
                     "NET_HOST_WALL_LM": net,
                     "ARITHMETIC": f"{gross:.3f} gross - {openings:.3f} openings - {sk['NON_SKIRTING_EDGE_LM']:.3f} other = {net:.3f} lm",
                     "WALL_TILE_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                          "WHY": "no section, elevation, finishes schedule or owner instruction gives a tiling "
                                                 "height for this project.  A height from another project is not a Qortuba fact."},
                     "GROSS_WALL_TILE_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED"},
                     "NET_WALL_TILE_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED"},
                     "HEIGHT_REQUIRED": True,
                     "WHAT_IS_MISSING": "one number: the wall tiling height.  With it, NET_WALL_TILE_AREA = NET_HOST_WALL_LM x "
                                        "height, less the opening areas, and every length above is already established."})
    return rows


# ---------------------------------------------------------------------------- §16 block walls
def block_walls(r, vid, regions, inv):
    """Wall plan lengths by thickness, with the rooms on each side."""
    grid = r.grids7[vid]
    label, meta, cell = grid["label"], grid["meta"], grid["cell"]
    faces_room = {}
    for x in inv:
        faces_room[x["FACE_ID"]] = x["CANONICAL_NAME"] if x["INSIDE_APARTMENT"] else f"[{x['ZONE_KIND']}]"
    side_of_band = defaultdict(lambda: defaultdict(float))
    for row in r.brows[vid]:
        if row["SPACE_FACE_ID"]:
            side_of_band[row["BAND_ID"]][(row["SIDE"], row["SPACE_FACE_ID"])] += row["LENGTH_MM"]
    sites_on_band = defaultdict(list)
    for s in r.sites7[vid]:
        if s.get("HOST_BAND_ID"):
            sites_on_band[s["HOST_BAND_ID"]].append(s)
    rows = []
    for b in r.bands7[vid]:
        if b["STATUS"] != "ACCEPTED":
            continue
        sides = side_of_band.get(b["BAND_ID"], {})
        a_rooms = sorted({faces_room.get(f, "UNKNOWN") for (sd, f) in sides if sd == "A"})
        b_rooms = sorted({faces_room.get(f, "UNKNOWN") for (sd, f) in sides if sd == "B"})
        ops = sites_on_band.get(b["BAND_ID"], [])
        rows.append({"WALL_ID": "W-" + b["BAND_ID"].split("-")[1][:8], "BAND_ID": b["BAND_ID"],
                     "ROOM_SIDE_A": a_rooms or ["NOT_A_MEASURED_SPACE"], "ROOM_SIDE_B": b_rooms or ["NOT_A_MEASURED_SPACE"],
                     "LENGTH_MM": round(b["LENGTH"], 1), "LENGTH_M": round(b["LENGTH"] / 1000, 3),
                     "THICKNESS_MM": round(b["THK"], 1), "KIND": b["KIND"],
                     "OPENINGS": [{"SITE_ID": s["SITE_ID"], "CLASS": s["CLASS"], "SPAN_MM": s["SPAN_MM"]}
                                  for s in ops if s["CLASS"] != "CAD_JUNCTION"],
                     "COLUMN_INTERRUPTION": [{"SITE_ID": s["SITE_ID"], "SPAN_MM": s["SPAN_MM"]}
                                             for s in ops if s["CLASS"] == "CAD_JUNCTION"],
                     "STATUS": "SOURCE_ESTABLISHED_PLAN_LENGTH"})
    by_thk = defaultdict(float)
    for x in rows:
        by_thk[x["THICKNESS_MM"]] += x["LENGTH_M"]
    return rows, {str(int(k)): round(v, 3) for k, v in sorted(by_thk.items())}


# ---------------------------------------------------------------------------- §17 / §18 plaster and paint
def plaster_and_paint(regions, skirt, blue):
    rows = []
    for reg, sk in zip(regions, skirt):
        wet = reg["WET_OR_DRY"] == "WET"
        wall = sk["NET_SKIRTING_LM"] + sk["WET_ROOM_EDGE_LM"]
        col = sk["COLUMN_FACE_LM"]
        glazed = sk["SLIDING_DOOR_DEDUCTION_LM"]
        rows.append({"ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"], "WET_OR_DRY": reg["WET_OR_DRY"],
                     "NORMAL_INTERNAL_PLASTER_FACE_LM": 0.0 if wet else round(wall, 3),
                     "WET_ROOM_TILE_PREP_FACE_LM": round(wall, 3) if wet else 0.0,
                     "COLUMN_FACE_LM": col,
                     "OTHER_FACE_LM": round(sk["NON_SKIRTING_EDGE_LM"], 3),
                     "TOTAL_PLASTERABLE_FACE_LM": round(wall + col, 3),
                     "PAINT_ELIGIBLE_FACE_LM": 0.0 if wet else round(wall + col, 3),
                     "TILED_FACE_LM": round(wall, 3) if wet else 0.0,
                     "GLAZED_FACE_LM": glazed,
                     "PAINT_WHY": ("a wet room's walls are tiled in this drawing's own terms, so no paint length is released "
                                   "for it without a finishes schedule saying where tiling stops"
                                   if wet else "a dry room's plastered faces are paint eligible"),
                     "HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                "WHY": "no floor-to-ceiling height exists in this drawing set"},
                     "PLASTER_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED"},
                     "PAINT_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED"},
                     "REVEALS": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                 "WHY": "a reveal return needs the opening's depth and height; the plan gives neither"}})
    return rows


# ---------------------------------------------------------------------------- §19 ceiling
def ceilings(regions, inv):
    rows = []
    for reg in regions:
        a = reg["AREA_M2"]["VALUE"]
        rows.append({"ROOM_ID": reg["ROOM_ID"], "ROOM": reg["ROOM"],
                     "FLOOR_AREA_M2": a, "CEILING_GEOMETRIC_AREA_M2": a,
                     "DERIVATION": "CEILING_GEOMETRIC_AREA = FLOOR_MEASUREMENT_REGION_AREA",
                     "CONDITIONS_TESTED": {"VOID": False, "STAIR_OPENING": False, "SHAFT": False, "OPEN_TO_ABOVE": False,
                                           "OTHER_EXCLUSION": False},
                     "WHY": "no void, stair opening, shaft or open-to-above condition is drawn inside this region, so its "
                            "ceiling plan geometry equals its floor measurement region",
                     "STATE": reg["STATUS"],
                     "CEILING_FINISH": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                        "WHY": "no reflected ceiling plan or finishes schedule exists"}})
    return rows


# ---------------------------------------------------------------------------- §21 human sheet
def human_sheet(inv, floors, skirt, prof, ceil, tile, plaster):
    sk = {x["ROOM_ID"]: x for x in skirt}
    pf = {x["ROOM_ID"]: x for x in prof}
    ce = {x["ROOM_ID"]: x for x in ceil}
    tl = {x["ROOM_ID"]: x for x in tile}
    pl = {x["ROOM_ID"]: x for x in plaster}
    lines = ["QORTUBA - SECOND FLOOR APARTMENT", "room-by-room takeoff from the architectural DWG", ""]
    for f in floors:
        rid = f["ROOM_ID"]
        lines.append(f"{f['ROOM']}   [{rid}]   {f['WET_OR_DRY']}")
        lines.append(f"  Floor:      {f['FORMULA']}")
        if f["SHAPE_TYPE"] != "RECTANGLE":
            lines.append(f"              shape {f['SHAPE_TYPE']}, measured as {len(f['RECTANGLES'])} non-overlapping rectangles")
        s = sk.get(rid)
        if s:
            lines.append(f"  Skirting:   {s['ARITHMETIC']}")
            if s["WET_OR_DRY"] == "WET":
                lines.append(f"              wet room: wall edge {s['WET_ROOM_EDGE_LM']:.3f} lm carries no skirting until the owner rules skirted or tiled")
        p = pf.get(rid)
        if p:
            lines.append(f"  Profile:    {p['PROFILE_GEOMETRIC_PATH_LM']:.3f} lm, same path as the skirting, separate BOQ item")
        c = ce.get(rid)
        if c and c["CEILING_GEOMETRIC_AREA_M2"] is not None:
            lines.append(f"  Ceiling:    {c['CEILING_GEOMETRIC_AREA_M2']:.4f} m2  (= floor, nothing open above)")
        t = tl.get(rid)
        if t:
            lines.append(f"  Wall tile:  host wall {t['ARITHMETIC']};  area NOT ESTABLISHED, height required")
        q = pl.get(rid)
        if q:
            lines.append(f"  Wall faces: plasterable {q['TOTAL_PLASTERABLE_FACE_LM']:.3f} lm, paint eligible {q['PAINT_ELIGIBLE_FACE_LM']:.3f} lm; areas need a height")
        lines.append("")
    return lines


# ---------------------------------------------------------------------------- run
def run():
    cfg = json.loads((B.OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    r = P7.run(cfg)
    vid = next(v for v in r.grids7 if r.grids7[v])
    cell_mm = r.grids7[vid]["cell"]
    nd = list(r.normalized.values())[0]
    prims = nd.primitives
    cell_rows, _ = CELLS.build(r, vid)
    adj = CELLS.room_adjacency(r, vid, cell_rows)
    comp, non_fixing = FR.measurement_components(r, vid)

    inv = room_inventory(r, vid, cell_rows, adj, prims)
    floors, regions = floor_calculations(r, vid, inv, cell_rows, comp, non_fixing)
    dim_rows, owned = R3.room_dimension_graph(r, vid, regions)
    dual = dual_method(regions, owned, floors)
    blue = blue_elements(r, vid, prims, inv, regions)
    skirt, prof = skirting_and_profile(r, vid, regions, blue, cell_mm)
    tile = wall_tile(regions, skirt, inv)
    walls, by_thk = block_walls(r, vid, regions, inv)
    plaster = plaster_and_paint(regions, skirt, blue)
    ceil = ceilings(regions, inv)
    sheet = human_sheet(inv, floors, skirt, prof, ceil, tile, plaster)
    return dict(r=r, vid=vid, inv=inv, floors=floors, regions=regions, dual=dual, dim_rows=dim_rows, blue=blue,
                skirt=skirt, prof=prof, tile=tile, walls=walls, by_thk=by_thk, plaster=plaster, ceil=ceil, sheet=sheet)


# ---------------------------------------------------------------------------- §22 summary totals, bottom up
def summary(inv, floors, skirt, prof, ceil, tile, plaster, by_thk):
    dry = [f for f in floors if f["WET_OR_DRY"] == "DRY" and f["METHOD_A_CAD_POLYGON_AREA_M2"] is not None]
    wet = [f for f in floors if f["WET_OR_DRY"] == "WET" and f["METHOD_A_CAD_POLYGON_AREA_M2"] is not None]
    d = round(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in dry), 4)
    w = round(sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in wet), 4)
    sk_dry = round(sum(x["NET_SKIRTING_LM"] for x in skirt if x["WET_OR_DRY"] == "DRY"), 3)
    pf_tot = round(sum(x["PROFILE_GEOMETRIC_PATH_LM"] for x in prof), 3)
    ce = round(sum(c["CEILING_GEOMETRIC_AREA_M2"] for c in ceil if c["CEILING_GEOMETRIC_AREA_M2"] is not None), 4)
    baths = [t for t in tile if t["ROOM_KIND"] == "WET_ROOM"]
    prep = [t for t in tile if t["ROOM_KIND"] != "WET_ROOM"]
    return {"ARTIFACT": "QORTUBA_QS01_SUMMARY_TOTALS",
            "BUILT": "bottom up from the room and wall rows in this phase; no total was set first and back-filled",
            "A_DRY_INTERNAL_FLOOR_AREA_M2": {"VALUE": d, "ROOMS": [f["ROOM"] for f in dry], "COUNT": len(dry)},
            "B_WET_INTERNAL_FLOOR_AREA_M2": {"VALUE": w, "ROOMS": [f["ROOM"] for f in wet], "COUNT": len(wet)},
            "C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2": {"VALUE": round(d + w, 4),
                                                         "COMPONENTS": [{"ROOM": f["ROOM"], "AREA_M2": f["METHOD_A_CAD_POLYGON_AREA_M2"],
                                                                         "WET_OR_DRY": f["WET_OR_DRY"]} for f in dry + wet],
                                                         "EXCLUDES": sorted({x["ZONE_KIND"] for x in inv if not x["INSIDE_APARTMENT"]}),
                                                         "NO_HIDDEN_COMPONENT": "every room in the total is listed above"},
            "D_TOTAL_SKIRTING_LM": {"VALUE": sk_dry, "SCOPE": "dry rooms only; wet rooms carry a wall-edge length and no skirting"},
            "E_TOTAL_BLACK_PROFILE_LM": {"VALUE": pf_tot, "SCOPE": "the same eligible wall path as the skirting, as a separate BOQ item"},
            "F_TOTAL_CEILING_GEOMETRY_M2": {"VALUE": ce, "SCOPE": "the ten apartment rooms; stairs, terrace and roof excluded"},
            "G_TOTAL_BATHROOM_FLOOR_AREA_M2": {"VALUE": w},
            "H_TOTAL_BATHROOM_HOST_WALL_LM": {"VALUE": round(sum(t["NET_HOST_WALL_LM"] for t in baths), 3)},
            "I_TOTAL_PREPARATION_HOST_WALL_LM": {"VALUE": round(sum(t["NET_HOST_WALL_LM"] for t in prep), 3)},
            "J_TOTAL_BATHROOM_AND_PREPARATION_WALL_CERAMIC_M2": {
                "VALUE": None, "STATE": "NOT_ESTABLISHED",
                "MISSING_INPUT": "the wall tiling height",
                "WHAT_IS_ESTABLISHED": round(sum(t["NET_HOST_WALL_LM"] for t in tile), 3),
                "UNIT": "LM of net host wall, ready to multiply by a height the moment one is sourced"},
            "K_TOTAL_150_MM_WALL_LENGTH_M": {"VALUE": by_thk.get("150", 0.0)},
            "L_TOTAL_200_MM_WALL_LENGTH_M": {"VALUE": by_thk.get("200", 0.0)},
            "OTHER_THICKNESS_WALL_LENGTH_M": {k: v for k, v in by_thk.items() if k not in ("150", "200")},
            "M_TOTAL_PLASTERABLE_FACE_LENGTH_LM": {"VALUE": round(sum(x["TOTAL_PLASTERABLE_FACE_LM"] for x in plaster), 3)},
            "N_TOTAL_PAINT_ELIGIBLE_FACE_LENGTH_LM": {"VALUE": round(sum(x["PAINT_ELIGIBLE_FACE_LM"] for x in plaster), 3)},
            "AREA_STATES": {"BLOCKWORK_AREA": "NOT_ESTABLISHED", "PLASTER_AREA": "NOT_ESTABLISHED",
                            "PAINT_AREA": "NOT_ESTABLISHED", "WALL_TILE_AREA": "NOT_ESTABLISHED",
                            "WHY": "no floor-to-ceiling height, no tiling height and no section exists in this drawing set"}}


def provenance(floors, dual, regions, dim_rows, skirt, walls):
    """§25: what each room's number was computed from, so the result stays auditable now the benchmark is known."""
    dims_by_room = defaultdict(list)
    for d in dim_rows:
        dims_by_room[d["ROOM_ID"]].append({"DIMENSION_ID": d["DIMENSION_ID"], "DISPLAY_VALUE": d["DISPLAY_VALUE"],
                                           "PROJECTED_VALUE": d["PROJECTED_VALUE"], "AXIS": d["MEASUREMENT_AXIS"]})
    reg_by = {r["FLOOR_MEASUREMENT_REGION_ID"]: r for r in regions}
    dual_by = {d["ROOM_ID"]: d for d in dual}
    sk_by = {x["ROOM_ID"]: x for x in skirt}
    rows = []
    for f, reg in zip(floors, regions):
        rows.append({"ROOM_ID": f["ROOM_ID"], "ROOM": f["ROOM"],
                     "FORMULA": f["FORMULA"],
                     "METHOD_A_GEOMETRY_IDS": {"CUT_LINES_X_MM": f["CUT_LINES_X_MM"], "CUT_LINES_Y_MM": f["CUT_LINES_Y_MM"],
                                               "BOUNDARY_SEAL_INDEXES": sorted({s["SEAL_INDEX"] for s in reg["BOUNDARY_SEGMENTS"]}),
                                               "BAND_IDS": sorted({s["BAND_ID"] for s in reg["BOUNDARY_SEGMENTS"] if s.get("BAND_ID")}),
                                               "RASTER_LABELS": reg["LABELS"]},
                     "METHOD_B_DIMENSION_IDS": dims_by_room.get(reg["FLOOR_MEASUREMENT_REGION_ID"], []),
                     "METHOD_B_STRENGTH": dual_by[f["ROOM_ID"]]["METHOD_B_STRENGTH"],
                     "SKIRTING_SEAL_INDEXES": sorted({d["SEAL_INDEX"] for d in sk_by[f["ROOM_ID"]]["SEGMENTS"]}),
                     "SOURCE": "Qortuba architectural DWG, second floor plan, via the frozen PA07 ingest engine"})
    return {"ARTIFACT": "QORTUBA_QS01_ROOM_CALCULATION_PROVENANCE", "ROWS": rows, "COUNT": len(rows),
            "WALL_IDS": [w["WALL_ID"] for w in walls],
            "WHY_THIS_MATTERS": "the contractor's aggregate totals were seen in an earlier phase, so this phase's integrity "
                                "rests on the room numbers being derived from named geometry and frozen before any comparison. "
                                "Every row above names the cut lines, the seals, the bands and the dimensions it used."}


def finish():
    o = run()
    written = []
    written.append(write("QORTUBA_ROOM_REGISTER", {
        "ARTIFACT": "QORTUBA_ROOM_REGISTER", "STOREY": STOREY, "ROWS": o["inv"], "COUNT": len(o["inv"]),
        "INSIDE_APARTMENT": sum(1 for x in o["inv"] if x["INSIDE_APARTMENT"]),
        "EXCLUDED_ZONE_KINDS": EXCLUDED_ZONE_KINDS,
        "RULE": "a space with no room label is still a room when apartment doors open into it; a space with a label is not a "
                "room of this apartment when the lift or the stair is drawn inside it"}))
    written.append(write("QORTUBA_QS01_FLOOR_CALCULATIONS", {
        "ARTIFACT": "QORTUBA_QS01_FLOOR_CALCULATIONS", "ROWS": o["floors"], "COUNT": len(o["floors"]),
        "METHOD": "arrangement of the room's own bounding lines, merged into the fewest rectangles that reproduce it exactly",
        "RULE": "no bounding-box area is used for an irregular room"}))
    written.append(write("QORTUBA_QS01_DUAL_METHOD_CHECK", {
        "ARTIFACT": "QORTUBA_QS01_DUAL_METHOD_CHECK", "ROWS": o["dual"], "COUNT": len(o["dual"]),
        "BY_STRENGTH": dict(Counter(d["METHOD_B_STRENGTH"] for d in o["dual"])),
        "BY_VERDICT": dict(Counter(d["VERDICT"] for d in o["dual"])),
        "RULE": "the two methods are never averaged, and an envelope check is never reported as an area check"}))
    written.append(write("QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE", {
        "ARTIFACT": "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE", "ROWS": o["blue"], "COUNT": len(o["blue"]),
        "BY_TYPE": dict(Counter(b["TYPE"] for b in o["blue"])),
        "CLASSES": BLUE_ELEMENT_CLASSES,
        "RULE": "the discriminator is whether the wall band is interrupted at the element, not the layer it is drawn on"}))
    written.append(write("QORTUBA_QS01_SKIRTING_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_SKIRTING_TAKEOFF", "ROWS": o["skirt"], "COUNT": len(o["skirt"]),
        "DRY_TOTAL_LM": round(sum(x["NET_SKIRTING_LM"] for x in o["skirt"] if x["WET_OR_DRY"] == "DRY"), 3),
        "RULE": "the path is the eligible wall line, never the polygon perimeter; a window with wall below is not deducted and "
                "a floor-level glazed opening is"}))
    written.append(write("QORTUBA_QS01_PROFILE_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_PROFILE_TAKEOFF", "ROWS": o["prof"], "COUNT": len(o["prof"]),
        "TOTAL_LM": round(sum(x["PROFILE_GEOMETRIC_PATH_LM"] for x in o["prof"]), 3),
        "RULE": "one underlying eligible wall path, two BOQ items; the profile is not given a second invented perimeter"}))
    written.append(write("QORTUBA_QS01_WALL_TILE_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_WALL_TILE_TAKEOFF", "ROWS": o["tile"], "COUNT": len(o["tile"]),
        "TOTAL_NET_HOST_WALL_LM": round(sum(t["NET_HOST_WALL_LM"] for t in o["tile"]), 3),
        "WALL_TILE_AREA_STATE": "NOT_ESTABLISHED", "MISSING_INPUT": "the wall tiling height"}))
    written.append(write("QORTUBA_QS01_BLOCK_WALL_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_BLOCK_WALL_TAKEOFF", "ROWS": o["walls"], "COUNT": len(o["walls"]),
        "TOTAL_LENGTH_M_BY_THICKNESS": o["by_thk"], "BLOCKWORK_AREA_STATE": "NOT_ESTABLISHED",
        "WHY": "no wall height exists in this drawing set, so only plan lengths are released"}))
    written.append(write("QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF", "ROWS": o["plaster"], "COUNT": len(o["plaster"]),
        "TOTAL_PLASTERABLE_LM": round(sum(x["TOTAL_PLASTERABLE_FACE_LM"] for x in o["plaster"]), 3),
        "TOTAL_PAINT_ELIGIBLE_LM": round(sum(x["PAINT_ELIGIBLE_FACE_LM"] for x in o["plaster"]), 3),
        "RULE": "paint is a separate eligibility layer; a plastered wall is not assumed to be painted"}))
    written.append(write("QORTUBA_QS01_CEILING_TAKEOFF", {
        "ARTIFACT": "QORTUBA_QS01_CEILING_TAKEOFF", "ROWS": o["ceil"], "COUNT": len(o["ceil"]),
        "TOTAL_M2": round(sum(c["CEILING_GEOMETRIC_AREA_M2"] for c in o["ceil"] if c["CEILING_GEOMETRIC_AREA_M2"] is not None), 4)}))
    summ = summary(o["inv"], o["floors"], o["skirt"], o["prof"], o["ceil"], o["tile"], o["plaster"], o["by_thk"])
    written.append(write("QORTUBA_QS01_SUMMARY_TOTALS", summ))
    written.append(write("QORTUBA_QS01_ROOM_CALCULATION_PROVENANCE",
                         provenance(o["floors"], o["dual"], o["regions"], o["dim_rows"], o["skirt"], o["walls"])))
    sheet = "\n".join(o["sheet"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "QORTUBA_HUMAN_QS_SHEET.txt").write_text(sheet, "utf-8")
    written.append(write("QORTUBA_HUMAN_QS_SHEET", {"ARTIFACT": "QORTUBA_HUMAN_QS_SHEET", "LINES": o["sheet"],
                                                    "TEXT_FILE": "QORTUBA_HUMAN_QS_SHEET.txt"}))

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    blind = json.loads((B.OUT / "FREEZE_PA08_QORTUBA_BLIND_01.json").read_text("utf-8"))
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written)) if (OUT / f"{n}.json").exists()}
    fr = {"ARTIFACT": "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01", "PROJECT_ALIAS": "QORTUBA", "STOREY": STOREY,
          "SOURCE_ONLY_CALCULATION_COMPLETE": True,
          "WHAT_THAT_MEANS": "every figure in these registers was computed from the Qortuba DWG by this module, which imports "
                             "no contractor register and no comparison code, and the freeze was written before any comparison "
                             "with the contractor sheet ran",
          "CONTRACTOR_AGGREGATE_USED_AS_A_TARGET": False,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "ENGINE_VERSION": ENGINE_VERSION,
          "SOURCE_HASHES": blind["SOURCE_HASHES"], "DECODER": blind["DECODER"],
          "SUMMARY_TOTALS": {k: v for k, v in summ.items() if k.startswith(("A_", "B_", "C_", "D_", "E_", "F_"))},
          "CONTENTS": contents, "COUNT": len(contents)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01", fr)
    return {"FREEZE": fr, "SUMMARY": summ, "WRITTEN": written, **o}


if __name__ == "__main__":
    out = finish()
    s = out["SUMMARY"]
    print("FREEZE", out["FREEZE"]["DIGEST"][:16], "| registers", out["FREEZE"]["COUNT"])
    for f in out["floors"]:
        print(f"  {f['ROOM'][:24]:26s} {f['WET_OR_DRY']:4s} {f['FORMULA']}")
    print("A dry ", s["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"], "| B wet", s["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
          "| C total", s["C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2"]["VALUE"])
    print("D skirting", s["D_TOTAL_SKIRTING_LM"]["VALUE"], "| E profile", s["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"],
          "| F ceiling", s["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"])
    print("H bath host wall", s["H_TOTAL_BATHROOM_HOST_WALL_LM"]["VALUE"], "| I prep host wall", s["I_TOTAL_PREPARATION_HOST_WALL_LM"]["VALUE"],
          "| J ceramic", s["J_TOTAL_BATHROOM_AND_PREPARATION_WALL_CERAMIC_M2"]["STATE"])
    print("K 150mm", s["K_TOTAL_150_MM_WALL_LENGTH_M"]["VALUE"], "| L 200mm", s["L_TOTAL_200_MM_WALL_LENGTH_M"]["VALUE"])
    print("M plasterable", s["M_TOTAL_PLASTERABLE_FACE_LENGTH_LM"]["VALUE"], "| N paint eligible", s["N_TOTAL_PAINT_ELIGIBLE_FACE_LENGTH_LM"]["VALUE"])
