"""E1.3 — physical boundary basis, gap ontology and open boundary chains.

Three phases, because the visual challenge is genuinely cold and has to
be run between them:

    geometry    admit the inputs, re-decide every gap, decide what each
                column owns, build a boundary CHAIN for every candidate
                whether or not it closes, and cut the V1 source-only crops
    v2-inputs   draw one overlay per candidate for the challenge pass
    finalize    arbitrate in three dimensions, run one decision ledger per
                candidate, write the registers and freeze

E1, E1.1 and E1.2 are read and never written. Every module they froze is
imported unchanged; where E1.3 disagrees with one of them it does so in a
new module, so both runs remain reproducible from their own freezes.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine import admission_ledger as led
from engine import arbitration_dimensions as ad
from engine import atomic_interval as ai
from engine import boundary_chain as bc
from engine import boundary_walk as bw
from engine import cad_geometry as cg
from engine import column_ownership as co
from engine import decision_ledger as dl
from engine import deterministic_qa as dqa
from engine import e1_3_inputs as ei3
from engine import e1_release as rel
from engine import edge_relation as edge
from engine import export_provenance as prov
from engine import gap_ontology as go
from engine import gap_pass as gp
from engine import interval_role as ir
from engine import label_ontology as lo
from engine import space_status as ss
from engine import stair_completeness as stc
from engine import visible_boundary as vb
from engine import visual_challenger_v2 as vc
from tools import run_e1_2 as r12

E1_3_MODEL = "E1_3_PHYSICAL_BOUNDARY_BASIS_GAP_ONTOLOGY_AND_OPEN_CHAINS_V1"
RUN_ID = "E1_3-P7757-GF-001"

CLOSURE_IS_NOT_A_TARGET = (
    "E1.3 does not succeed by closing more rooms. It succeeds when it can "
    "say which boundaries the drawing establishes, where no boundary "
    "exists, which structural objects exist without owning a room face, "
    "and what is still unresolved")

FRAME_ID = "E1_3:DRAWING_REGION_FRAME"

WHY_A_LOCAL_WINDOW = (
    "an open room cannot be ordered by spanning its opening. A doorway is "
    "two wall ends facing each other ALONG ONE LINE; an open side is two "
    "walls that do not face each other at all, so no span is ever proposed "
    "for it and no reach, however large, finds one. Nor can the whole "
    "drawing be used as a frame: an open region's seed then falls in the "
    "one face outside every closed loop, and the answer is the site.\n\n"
    "So the material is cut against a LOCAL WINDOW round the seed, and the "
    "window grows only while the face it produces is still room-scale. "
    "What that yields is the material actually standing round this point, "
    "in order, with the stretches where the window edge had to carry the "
    "figure marked as OPEN_EDGE - the drawing builds nothing along them. "
    "The window is not a wall, carries no material, and its size is "
    "recorded beside every chain it produced")

WHAT_AN_OPEN_EDGE_LENGTH_IS = (
    "OPEN_EDGE is a claim about the drawing: a gap was found between two "
    "wall ends and classified, and nothing is built across it. "
    "UNRESOLVED_EDGE on the local window is not that claim. It says only "
    "that this pass stopped looking there, and the drawing may well build "
    "something just beyond it. Reading a window edge as an open side would "
    "assert an absence nobody established.\n\n"
    "So: material_length_mm is measured from drawn faces and may be used. "
    "The length AND the position of any element carrying "
    "ON_THE_LOCAL_WINDOW_EDGE belong to the window, not to the drawing, "
    "and no later stage may read either as geometry the drawing gives")

WINDOW_LEVELS = 7
WINDOW_MIN_MM = 1500.0
WINDOW_MAX_SHARE_OF_REGION = 0.25
FACE_MAX_SHARE_OF_REGION = 0.20

ONE_FACE_MAY_HOLD_SEVERAL_LABELS = (
    "where no wall, portal or drawn separator lies between two labels, "
    "they are inside one physical region and the same boundary chain is "
    "that region's. It is reported once, as ONE_PHYSICAL_REGION with "
    "several functional zones, rather than handed to each label as if it "
    "were a room of its own")

RUNS_OUT_COLOUR = (200, 0, 0)

OVERLAY_LEGEND = (
    "thick black = an established material face of the boundary chain",
    "blue = a curved material face, kept as an arc",
    "thick red = an EXPOSED column face: it owns the clear internal boundary",
    "thin grey dashed = a structural column BEHIND the finish face: it "
    "exists and does not own the room face",
    "dashed orange = a door portal: a gap with positive opening evidence",
    "fine grey dashed = a continuity span: a junction or cross wall carries "
    "the boundary through, and the span itself is not a drawn face",
    "dashed green = an OPEN EDGE: the drawing builds nothing here",
    "dotted purple = an UNRESOLVED EDGE: what bounds the region here is not "
    "established, including where the drawing region frame was used to make "
    "a face walkable",
    "magenta = casework, counters, pool internals and fixtures, excluded",
    "red cross = the boundary RUNS OUT here: the drawn material ends and "
    "nothing carries the boundary on. Nothing beyond a red cross is "
    "proposed as part of this region",
    "blue ring = the label this candidate was traced from",
)


# ---------------------------------------------------------------- helpers
def _write(out, artifacts, name, body) -> dict:
    body = dict(body)
    body["E1_3_MODEL"] = E1_3_MODEL
    body["RUN_ID"] = RUN_ID
    key = f"{name.split('.')[0]}_HASH"
    body.pop(key, None)
    body[key] = prov.canonical_sha256(body)
    path = Path(out) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    artifacts[name] = r12._sha(path)
    return body


def _pt(p):
    return (float(p[0]), float(p[1]))


def _seg_pts(s):
    return (_pt((s.x1, s.y1)), _pt((s.x2, s.y2)))


def _registered_sheet(a, gf):
    """The source raster, registered to the CAD, for cross-representation
    work only. Never an independent source of truth."""
    from engine import raster_qa as rq
    if not (a.raster and Path(a.raster).exists()):
        return None, None
    rgn = gf["region"]
    reg = rq.register(a.raster, gf["primitives"],
                      extent=(rgn.x0, rgn.y0, rgn.x1, rgn.y1))
    return reg, rq.Sheet(reg)


def window_segments(centre, half):
    """A local window round a seed, as topology-only closing geometry."""
    cx, cy = centre
    x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    out = []
    for i, (a, b) in enumerate(zip(corners, corners[1:]), start=1):
        out.append(cg.BoundarySegment(
            kind=cg.LINE, x1=a[0], y1=a[1], x2=b[0], y2=b[1],
            role=cg.OPEN_EDGE, object_id=f"{FRAME_ID}#{i:02d}",
            entity_type="A_LOCAL_WINDOW_EDGE_NOT_A_DRAWN_ENTITY",
            layer="", evidence=("A_WINDOW_SO_A_FACE_EXISTS_TO_WALK",),
            confidence="LOW"))
    return out


def window_ladder(region):
    """Window half-sizes to try, from small to a capped room scale."""
    span = min(float(region.x1 - region.x0), float(region.y1 - region.y0))
    top = span * WINDOW_MAX_SHARE_OF_REGION
    out, h = [], WINDOW_MIN_MM
    while h <= top and len(out) < WINDOW_LEVELS:
        out.append(round(h, 1))
        h *= 1.8
    return out or [WINDOW_MIN_MM]


# ------------------------------------------------------------- columns
def column_ownership_pass(interp, gf, *, material_segments) -> dict:
    """§7, §8, §10 — three questions per column, and both geometries kept."""
    cols = interp["roles"]["columns"]
    loops = list(cols.get("loops", ()))
    by_id = {p.object_id: p for p in gf["primitives"]}

    # Architectural faces are the ESTABLISHED material faces that are not
    # themselves structural-layer geometry: the thing a column is tested
    # against must not be the column.
    struct_layers = set(cols.get("structural_layers", ()))
    arch = []
    for s in material_segments:
        if getattr(s, "layer", "") in struct_layers:
            continue
        try:
            pts = s.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) >= 2:
            arch.append((_pt(pts[0]), _pt(pts[-1])))

    rows, hidden_ids, exposed_ids = [], set(), set()
    for lp in loops:
        members = list(lp.get("member_object_ids", ()))
        xs, ys = [], []
        for oid in members:
            p = by_id.get(oid)
            if p is None:
                continue
            for ax, ay in (("x1", "y1"), ("x2", "y2")):
                x, y = getattr(p, ax, None), getattr(p, ay, None)
                if x is not None and y is not None:
                    xs.append(float(x))
                    ys.append(float(y))
            if getattr(p, "kind", "") in ("ARC", "CIRCLE"):
                cx, cy, r = float(p.cx), float(p.cy), float(p.radius)
                xs += [cx - r, cx + r]
                ys += [cy - r, cy + r]
        if not xs:
            continue
        box = (min(xs), min(ys), max(xs), max(ys))
        cont = co.architectural_face_continues_across(box, arch)

        # §8 — exposure evidence, taken from the drawing rather than
        # assumed. An architectural face that STOPS at the footprint, with
        # no face carrying on past it, is the finish meeting the column.
        pad = 2.0
        x0, y0, x1, y1 = box
        terminates = any(
            (x0 - pad <= q[0] <= x1 + pad and y0 - pad <= q[1] <= y1 + pad)
            for (pa, pb) in arch for q in (pa, pb))
        exposure = []
        if terminates and not cont["continues_across"]:
            exposure.append(co.EV_ARCH_FACE_TERMINATES_AT_THE_COLUMN)

        a = co.assess(
            column_evidence=lp.get("STRUCTURAL_EVIDENCE", ()),
            structural_in_kind=ir.STRUCTURAL_IN_KIND,
            evidence_required=ir.COLUMN_EVIDENCE_REQUIRED,
            exposure_evidence=sorted(set(exposure)),
            architectural_face_continues=cont["continues_across"],
            architectural_face_present=bool(cont["continues_across"]
                                            or terminates))
        owns = a["CLEAR_FACE_OWNERSHIP"][
            "may_deform_the_clear_internal_boundary"]
        (exposed_ids if owns else hidden_ids).update(members)
        rows.append({
            "COLUMN_ID": lp.get("LOOP_ID"),
            "member_object_ids": members,
            "footprint_box_mm": [round(v, 3) for v in box],
            "size_mm": lp.get("size_mm"),
            "layers": lp.get("layers"),
            "blocks": lp.get("blocks"),
            "COLUMN_EXISTENCE_STATUS":
                a["EXISTENCE"]["COLUMN_EXISTENCE_STATUS"],
            "evidence": a["EXISTENCE"]["evidence"],
            "evidence_that_is_structural_in_kind":
                a["EXISTENCE"]["evidence_that_is_structural_in_kind"],
            "only_structural_in_kind_evidence_is_wall_contact": (
                a["EXISTENCE"]["evidence_that_is_structural_in_kind"]
                == [ir.EV_COL_WALL_CONNECTIVITY]),
            "EXPOSED_TO_ROOM_STATUS": a["EXPOSURE"]["EXPOSED_TO_ROOM_STATUS"],
            "exposure_evidence": a["EXPOSURE"]["exposure_evidence"],
            "architectural_face_continues_across": cont["continues_across"],
            "an_architectural_face_terminates_at_the_footprint": terminates,
            "CLEAR_FACE_OWNERSHIP_STATUS":
                a["CLEAR_FACE_OWNERSHIP"]["CLEAR_FACE_OWNERSHIP_STATUS"],
            "structural_object_relation":
                a["CLEAR_FACE_OWNERSHIP"]["structural_object_relation"],
            "may_deform_the_clear_internal_boundary": owns,
            "why_existence":
                a["EXISTENCE"]["a_touched_wall_is_not_a_structure"],
            "why_exposure": a["EXPOSURE"]["why"],
            "why_ownership": a["CLEAR_FACE_OWNERSHIP"]["why"],
        })
    return {"rows": rows,
            "object_ids_that_do_not_own_the_room_face": sorted(hidden_ids),
            "object_ids_that_own_the_room_face": sorted(exposed_ids),
            "architectural_faces_tested_against": len(arch)}


# ----------------------------------------------------------------- chains
def _class_at(pt_a, pt_b, gap_rows, *, tol_mm=50.0):
    """Which classified gap does this inserted span correspond to?"""
    ma = ((pt_a[0] + pt_b[0]) / 2.0, (pt_a[1] + pt_b[1]) / 2.0)
    best, best_d = None, None
    for g in gap_rows:
        gm = ((g["start_mm"][0] + g["end_mm"][0]) / 2.0,
              (g["start_mm"][1] + g["end_mm"][1]) / 2.0)
        d = math.hypot(ma[0] - gm[0], ma[1] - gm[1])
        if best_d is None or d < best_d:
            best, best_d = g, d
    if best is not None and best_d is not None and best_d <= tol_mm:
        return best
    return None


_ELEMENT_FOR_GAP = {
    go.CONFIRMED_DOOR_PORTAL: bc.DOOR_PORTAL,
    go.PROBABLE_DOOR_PORTAL: bc.DOOR_PORTAL,
    go.CAD_JUNCTION_GAP: bc.MATERIAL_CONTINUITY_SPAN,
    go.MATERIAL_CONTINUITY_GAP: bc.MATERIAL_CONTINUITY_SPAN,
    go.OPEN_PHYSICAL_EDGE: bc.OPEN_EDGE,
    go.UNRESOLVED_GAP: bc.UNRESOLVED_EDGE,
}


def _parent_of(interval_id, interval_by_id):
    iv = interval_by_id.get(interval_id)
    if iv is not None:
        return (iv.provenance or {}).get("object_id") or ""
    # fall back on the id's own shape: "<prefix>:<parent>#<n>"
    head = str(interval_id).split("#", 1)[0]
    return head.split(":", 1)[-1] if ":" in head else head


def chain_for(trace_out, *, gap_rows, exposed_ids, interval_by_id) -> dict:
    """Turn a walked face into a PHYSICAL_BOUNDARY_CHAIN.

    The face exists because the material network was closed against the
    drawing region frame. Nothing that came from the frame is material,
    and nothing that came from an unclassified gap is either.
    """
    cands = trace_out.get("candidates") or []
    if not cands:
        return None
    b = cands[0]["boundary"]
    material, connectors = [], []
    for s in b.segments:
        a, z = _seg_pts(s)
        oid = s.object_id or ""
        iv = interval_by_id.get(oid)
        if oid.startswith(FRAME_ID):
            connectors.append({
                "kind": bc.UNRESOLVED_EDGE, "start_mm": a, "end_mm": z,
                "ON_THE_LOCAL_WINDOW_EDGE": True,
                "LENGTH_AND_POSITION_ARE_THE_WINDOWS_NOT_THE_DRAWINGS": True,
                "why": ("the local window cut the figure here. That is not "
                        "the drawing saying nothing is built along this "
                        "stretch - it is this pass saying it stopped "
                        "looking. What bounds the region here is not "
                        "established, and nothing is closed across it")})
            continue
        if s.role in cg.MATERIAL_ROLES:
            parent = _parent_of(oid, interval_by_id)
            if s.role == cg.COLUMN_FACE and parent not in exposed_ids:
                connectors.append({
                    "kind": bc.UNRESOLVED_EDGE, "start_mm": a, "end_mm": z,
                    "object_id": oid, "parent_object_id": parent,
                    "CLEAR_FACE_OWNERSHIP_STATUS": co.ARCHITECTURAL_FACE_OWNS,
                    "why": ("a structural column face stands here and does "
                            "not own the clear internal boundary. What the "
                            "room's face follows across it is not "
                            "established from this trace")})
                continue
            if s.role == cg.COLUMN_FACE:
                kind = bc.EXPOSED_COLUMN_FACE
            elif s.kind in (cg.ARC, cg.CIRCLE):
                kind = bc.CURVED_MATERIAL_FACE
            elif iv is not None and iv.role == ir.GLAZING:
                kind = bc.GLAZING_BOUNDARY
            else:
                kind = bc.MATERIAL_WALL_FACE
            material.append({
                "kind": kind, "start_mm": a, "end_mm": z,
                "object_id": oid, "layer": s.layer,
                "entity_type": s.entity_type,
                "INTERVAL_ROLE": iv.role if iv is not None else None,
                "boundary_role": s.role,
                **({"centre_mm": [s.cx, s.cy], "radius_mm": s.radius,
                    "start_angle_rad": s.start_angle,
                    "end_angle_rad": s.end_angle,
                    "analytical_geometry": "THE_ORIGINAL_CURVE"}
                   if s.kind in (cg.ARC, cg.CIRCLE) else {}),
            })
            continue
        # an inserted span: what the evidence says it is decides its kind
        g = _class_at(a, z, gap_rows)
        cls = g["GAP_CLASS"] if g else go.UNRESOLVED_GAP
        kind = _ELEMENT_FOR_GAP.get(cls, bc.UNRESOLVED_EDGE)
        row = {"kind": kind, "start_mm": a, "end_mm": z,
               "GAP_CLASS": cls, "GAP_ID": g["GAP_ID"] if g else None,
               "why": "; ".join(g["notes"]) if g else
               "no classified gap corresponds to this inserted span"}
        if kind == bc.MATERIAL_CONTINUITY_SPAN:
            row["MATERIAL_CONTINUES_ACROSS"] = True
        connectors.append(row)
    if not material:
        return None
    return bc.build(material, connectors=connectors)


VISIBILITY_REACH_MM = 12000.0

WHAT_A_VISIBLE_BOUNDARY_IS = (
    "for a region drawn material does not enclose there is no face to "
    "walk, and no window may be used to invent one. So the boundary is "
    "taken by standing at the label point and looking out: in each "
    "direction either drawn material is the first thing met, and that "
    "stretch bounds this point, or nothing is, and the drawing "
    "establishes no boundary that way.\n\n"
    "Read it as what it says. It is the boundary evidence AROUND THIS "
    "POINT, not the outline of a room the drawing never closed. Where "
    "the sightlines run far, that is the region genuinely extending that "
    "far: an open side means the space carries on until something stops "
    "it, and the walls it reaches are the ones that do")


def chain_from_visibility(seed, segments, *, gap_rows, exposed_ids,
                          interval_by_id, reach_mm=VISIBILITY_REACH_MM):
    """§11 for a region no drawn material encloses. No window is used."""
    near = []
    for s in segments:
        pts = s.get("points") or ()
        if len(pts) < 2:
            continue
        if min(math.hypot(p[0] - seed[0], p[1] - seed[1])
               for p in pts) <= reach_mm:
            near.append(s)
    if not near:
        return None, {"why": "no drawn material lies within reach"}

    # A sight line that leaves through an opening lands on the far wall of
    # another space, and that wall does not bound this point. What stops it
    # is the mouth of the opening: the span from one wall end to the wall
    # end facing it. Both ends are drawn material; the span is not.
    mouth_spans = vb.mouths(seed, near, reach_mm=reach_mm)
    look = vb.look_around(seed, near + mouth_spans, reach_mm=reach_mm)
    look["mouths_between_wall_ends"] = len(mouth_spans)
    look["a_mouth_is_not_a_wall"] = vb.A_MOUTH_IS_NOT_A_WALL
    runs = [r for r in look["runs"]]
    if not any(r["KIND"] == "MATERIAL_RUN" and not r.get("IS_A_MOUTH")
               for r in runs):
        return None, look

    material, connectors = [], []
    mats = [r for r in runs if r["KIND"] == "MATERIAL_RUN"]
    for r in mats:
        if r.get("IS_A_MOUTH"):
            a = tuple(r["start_mm"])
            b = tuple(r["end_mm"])
            g = _class_at(tuple(r["mouth_start_mm"]),
                          tuple(r["mouth_end_mm"]), gap_rows)
            if g is not None:
                kind = _ELEMENT_FOR_GAP.get(g["GAP_CLASS"], bc.UNRESOLVED_EDGE)
                why = "; ".join(g["notes"]) or g["GAP_CLASS"]
                gid, cls = g["GAP_ID"], g["GAP_CLASS"]
            else:
                kind, gid, cls = bc.OPEN_EDGE, None, None
                why = ("the sight line ends at the mouth of an opening - the "
                       "span from one wall end to the wall end facing it. No "
                       "gap record classifies this span, so nothing is closed "
                       "across it and the boundary stays open here")
            connectors.append({
                "kind": kind, "start_mm": a, "end_mm": b,
                "GAP_ID": gid, "GAP_CLASS": cls,
                "MOUTH_SPAN_MM": r.get("span_mm"),
                "mouth_between_wall_ends": r.get("wall_end_object_ids"),
                "FIRST_MATERIAL_MET_LOOKING_THIS_WAY": False,
                "why": why})
            continue
        oid = r.get("object_id") or ""
        iv = interval_by_id.get(oid)
        parent = _parent_of(oid, interval_by_id)
        role = r.get("boundary_role")
        if role == cg.COLUMN_FACE and parent not in exposed_ids:
            connectors.append({
                "kind": bc.UNRESOLVED_EDGE,
                "start_mm": tuple(r["start_mm"]), "end_mm": tuple(r["end_mm"]),
                "object_id": oid, "parent_object_id": parent,
                "CLEAR_FACE_OWNERSHIP_STATUS": co.ARCHITECTURAL_FACE_OWNS,
                "why": ("a structural column face is the first thing met in "
                        "this direction and it does not own the clear "
                        "internal boundary")})
            continue
        kind = (bc.EXPOSED_COLUMN_FACE if role == cg.COLUMN_FACE
                else bc.GLAZING_BOUNDARY
                if (iv is not None and iv.role == ir.GLAZING)
                else bc.MATERIAL_WALL_FACE)
        material.append({
            "kind": kind,
            "start_mm": tuple(r["start_mm"]), "end_mm": tuple(r["end_mm"]),
            "object_id": oid, "parent_object_id": parent,
            "layer": r.get("layer"), "boundary_role": role,
            "INTERVAL_ROLE": iv.role if iv is not None else None,
            "FIRST_MATERIAL_MET_LOOKING_THIS_WAY": True,
        })

    # between consecutive material runs, a connector whose two ends are
    # real wall ends. Its class comes from the gap evidence where one
    # exists, and otherwise from whether the look found nothing that way.
    order = [r for r in runs]
    idx = [i for i, r in enumerate(order) if r["KIND"] == "MATERIAL_RUN"]
    for n, i in enumerate(idx):
        j = idx[(n + 1) % len(idx)] if len(idx) > 1 else None
        if j is None:
            break
        a = tuple(order[i]["end_mm"])
        b = tuple(order[j]["start_mm"])
        if math.hypot(b[0] - a[0], b[1] - a[1]) <= cg.SNAP_MM:
            continue
        between = (order[i + 1:j] if i < j
                   else order[i + 1:] + order[:j])
        nothing_met = any(x["KIND"] == "NOTHING_MET" for x in between)
        g = _class_at(a, b, gap_rows)
        if g is not None:
            cls = g["GAP_CLASS"]
            kind = _ELEMENT_FOR_GAP.get(cls, bc.UNRESOLVED_EDGE)
            why = "; ".join(g["notes"])
            gid = g["GAP_ID"]
        elif nothing_met:
            cls, kind, gid = None, bc.OPEN_EDGE, None
            why = ("looking between the end of one run of material and the "
                   "start of the next, nothing was met. The drawing builds "
                   "nothing along this stretch")
        else:
            cls, kind, gid = None, bc.UNRESOLVED_EDGE, None
            why = ("two runs of material do not meet here and no classified "
                   "gap corresponds to the span between them")
        connectors.append({"kind": kind, "start_mm": a, "end_mm": b,
                           "GAP_CLASS": cls, "GAP_ID": gid, "why": why,
                           "BOTH_ENDS_ARE_REAL_WALL_ENDS": True})

    if not material:
        return None, look
    ch = bc.build(material, connectors=connectors)
    ch["BOUNDARY_BASIS"] = "VISIBLE_FROM_THE_LABEL_POINT"
    ch["what_a_visible_boundary_is"] = WHAT_A_VISIBLE_BOUNDARY_IS
    ch["no_window_is_involved"] = vb.NO_WINDOW_IS_INVOLVED
    ch["look"] = {k: v for k, v in look.items() if k != "runs"}
    return ch, look



E1_3_CORRECTED_MECHANISM = (
    "the boundary is WALKED from face to face. Selecting material by "
    "where it is - nearest, or first met in a direction, or enclosed by a "
    "search window - was tried three times and failed three times, and "
    "each failure put material from another space into a region's "
    "boundary. engine.boundary_walk replaces all three")

_STOP_ELEMENT = {
    bw.WHY_THE_WALK_STOPS: bc.UNRESOLVED_EDGE,
    bw.BOUNDARY_OPEN_AT_AN_UNCLASSIFIED_GAP: bc.UNRESOLVED_EDGE,
}


def chain_from_walk(res, pieces, *, gap_rows, exposed_ids, interval_by_id):
    """The walked boundary, written in the chain vocabulary."""
    gap_by_id = {g["GAP_ID"]: g for g in gap_rows}
    material, connectors = [], []
    counted = set()
    for st in res["steps"]:
        kind = st["STEP"]
        if kind == bw.STEP_MATERIAL_FACE:
            pc = pieces[st["piece"]]
            oid = pc.get("object_id") or ""
            iv = interval_by_id.get(oid)
            parent = _parent_of(oid, interval_by_id)
            role = pc.get("boundary_role")
            cs = pc["coords"]
            a, z = ((tuple(cs[0]), tuple(cs[-1])) if st["entered_at_end"] == 0
                    else (tuple(cs[-1]), tuple(cs[0])))
            if role == cg.COLUMN_FACE and parent not in exposed_ids:
                connectors.append({
                    "kind": bc.UNRESOLVED_EDGE, "start_mm": a, "end_mm": z,
                    "object_id": oid, "parent_object_id": parent,
                    "CLEAR_FACE_OWNERSHIP_STATUS": co.ARCHITECTURAL_FACE_OWNS,
                    "why": ("a structural column face lies on this stretch "
                            "and it does not own the clear internal "
                            "boundary")})
                continue
            el = (bc.EXPOSED_COLUMN_FACE if role == cg.COLUMN_FACE
                  else bc.GLAZING_BOUNDARY
                  if (iv is not None and iv.role == ir.GLAZING)
                  else bc.MATERIAL_WALL_FACE)
            first = st["piece"] not in counted
            counted.add(st["piece"])
            material.append({
                "kind": el, "start_mm": a, "end_mm": z,
                "object_id": oid, "parent_object_id": parent,
                "layer": pc.get("layer"), "boundary_role": role,
                "INTERVAL_ROLE": iv.role if iv is not None else None,
                "WALKED_FROM_THE_FACE_BEFORE_IT": True,
                # a face walked from both of its sides is ONE piece of
                # drawn material and is counted once
                "COUNTS_TOWARD_MATERIAL_LENGTH": first,
            })
        elif kind == bw.STEP_WALL_END_RETURN:
            material.append({
                "kind": bc.MATERIAL_WALL_FACE,
                "start_mm": tuple(st["at_mm"]), "end_mm": tuple(st["to_mm"]),
                "object_id": "", "parent_object_id": None,
                "boundary_role": "WALL_END_ACROSS_ITS_OWN_THICKNESS",
                "WALL_THICKNESS_MM": st["thickness_mm"],
                "MATCHED_THICKNESS_FAMILY_MM": st["matched_family_mm"],
                "COUNTS_TOWARD_MATERIAL_LENGTH": True,
                "why": st["why"],
            })
        elif kind == bw.STEP_ACROSS_A_GAP:
            g = gap_by_id.get(st["gap"], {})
            connectors.append({
                "kind": _ELEMENT_FOR_GAP.get(st["GAP_CLASS"],
                                             bc.UNRESOLVED_EDGE),
                "start_mm": tuple(st["start_mm"]),
                "end_mm": tuple(st["end_mm"]),
                "GAP_ID": st["gap"], "GAP_CLASS": st["GAP_CLASS"],
                "why": "; ".join(g.get("notes") or ()) or st["GAP_CLASS"]})
        elif kind == bw.STEP_SINGLE_LINE_END_TURN:
            connectors.append({
                "kind": bc.MATERIAL_CONTINUITY_SPAN,
                "start_mm": tuple(st["at_mm"]), "end_mm": tuple(st["at_mm"]),
                "SINGLE_LINE_WALL_END": True, "why": st["why"]})
        elif kind == bw.STEP_STOPS:
            connectors.append({
                "kind": _STOP_ELEMENT.get(st["why"], bc.UNRESOLVED_EDGE),
                "start_mm": tuple(st["at_mm"]), "end_mm": tuple(st["at_mm"]),
                "THE_BOUNDARY_RUNS_OUT_HERE": True,
                "an_end_faces_this_one_across_a_gap":
                    st.get("an_end_faces_this_one_across_a_gap"),
                "why": st["why"]})
    if not material:
        return None
    ch = bc.build(material, connectors=connectors)
    ch["BOUNDARY_BASIS"] = res["BOUNDARY_BASIS"]
    ch["CLOSED_BY_DRAWN_MATERIAL"] = bool(res.get("RING_ENCLOSES_THE_POINT"))
    ch["RING_ENCLOSES_THE_POINT"] = bool(res.get("RING_ENCLOSES_THE_POINT"))
    ch["FACE_SELECTION"] = res.get("FACE_SELECTION") or []
    ch["faces_the_point_can_see"] = res.get("faces_the_point_can_see")
    ch["rings_that_close_but_not_around_the_point"] = res.get(
        "rings_that_close_but_not_around_the_point")
    ch["islands_standing_in_the_region"] = res.get(
        "islands_standing_in_the_region") or []
    ch["ring_area_mm2"] = res.get("ring_area_mm2")
    ch["the_corrected_mechanism"] = E1_3_CORRECTED_MECHANISM
    if not ch["RING_ENCLOSES_THE_POINT"]:
        ch["THIS_IS_NOT_A_PROPOSED_BOUNDARY"] = res.get(
            "THIS_IS_NOT_A_PROPOSED_BOUNDARY")
        ch["why_nothing_is_proposed"] = bw.WHY_NOTHING_IS_PROPOSED
    else:
        ch["why_this_ring"] = res.get("why_this_ring")
    # material length counts each piece of drawn material once
    once = 0.0
    for e in ch["CHAIN"]:
        if e.get("COUNTS_TOWARD_MATERIAL_LENGTH"):
            once += e["length_mm"]
    ch["material_length_counted_once_mm"] = round(once, 3)
    return ch

def _face_key(chain, *, snap=1.0):
    """Two candidates in the SAME physical region share a face key."""
    if chain is None:
        return None
    pts = sorted({(round(p[0] / snap), round(p[1] / snap))
                  for e in chain["CHAIN"]
                  for p in (e["start_mm"], e["end_mm"])})
    return prov.canonical_sha256(pts)[:24]


# ------------------------------------------------------------- candidates

OPEN_SPAN_CLOSES_NOTHING = (
    "a span from one wall end to the wall end facing it, where the drawing "
    "offers no evidence that anything was built across it. It delimits "
    "where the region stops; it does not close it. It contributes no wall "
    "length, it is never read as a face, and a region that meets one is "
    "ESTABLISHED_OPEN")


def _open_span_barriers(look_segments, gaps):
    """The facing wall-end spans that carry no closing evidence."""
    known = []
    for g in gaps["rows"]:
        a, b = tuple(g["start_mm"]), tuple(g["end_mm"])
        known.append((a, b))

    def already(a, b):
        for (ka, kb) in known:
            if ((math.hypot(a[0] - ka[0], a[1] - ka[1]) <= cg.SNAP_MM
                 and math.hypot(b[0] - kb[0], b[1] - kb[1]) <= cg.SNAP_MM)
                or (math.hypot(a[0] - kb[0], a[1] - kb[1]) <= cg.SNAP_MM
                    and math.hypot(b[0] - ka[0], b[1] - ka[1]) <= cg.SNAP_MM)):
                return True
        return False

    out = []
    for m in vb.mouths(None, look_segments):
        a = tuple(m["mouth_start_mm"])
        b = tuple(m["mouth_end_mm"])
        if already(a, b):
            continue
        out.append(cg.BoundarySegment(
            kind=cg.LINE, x1=a[0], y1=a[1], x2=b[0], y2=b[1],
            role=cg.OPENING, object_id="",
            entity_type="OPEN_SPAN_BETWEEN_TWO_WALL_ENDS_NOTHING_WAS_BUILT_HERE",
            layer="|".join(str(x) for x in (m.get("wall_end_object_ids") or ())
                           if x),
            evidence=(OPEN_SPAN_CLOSES_NOTHING,
                      m.get("TWO_ENDS_FACE_EACH_OTHER_BECAUSE") or "",
                      f"span_mm={m['span_mm']}")))
    return out


def build_e1_3_candidates(gf, interp, *, ontology, gaps, owner) -> dict:
    """Trace every candidate against material, real portals and the frame."""
    from shapely.geometry import Point, Polygon
    roles = interp["roles"]
    by_id = {p.object_id: p for p in gf["primitives"]}

    hidden = set(owner["object_ids_that_do_not_own_the_room_face"])
    exposed = set(owner["object_ids_that_own_the_room_face"])

    mat_all = r12.interval_prims(roles["intervals"], by_id, only_material=True)
    # §8: a structural outline that does not own the clear face is not
    # offered to the trace as a boundary. It stays in its own register.
    mat = [m for m in mat_all
           if m.interval.provenance.get("object_id") not in hidden]
    segs = [cg._as_segment(m, role=r12.boundary_role_of(m.interval))
            for m in mat]
    base = tuple(segs) + tuple(gaps["barriers"])

    keep = {r.group_id for r in ontology["rows"] if r.in_denominator}
    groups = [g for g in interp["labels"]["groups"]
              if g.group_id in keep and g.english_token]
    interval_by_id = {iv.interval_id: iv
                      for rows_ in roles["intervals"].values()
                      for iv in rows_}
    look_segments = []
    for sg in segs:
        try:
            pts = sg.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) >= 2:
            look_segments.append({
                "points": pts, "key": sg.object_id,
                "object_id": sg.object_id, "boundary_role": sg.role,
                "layer": sg.layer})

    # §11 - a region with an open side still has an extent, and the drawing
    # says where it stops: at the span from one wall end to the wall end
    # facing it. The evidenced spans are already barriers; these are the
    # rest, and they close NOTHING. They carry no material, they are never
    # a wall, and a region delimited by one is open, not closed.
    open_span_segments = _open_span_barriers(look_segments, gaps)
    # Offering these to the trace as barriers was tried and did not help:
    # it closed no further region and cost one that had been closed. They
    # are computed and reported, and the trace is not given them.

    # THE CORRECTED MECHANISM. Drawn material is noded into pieces once,
    # the faces that are the two sides of one wall body are paired once,
    # and the wall ends with something facing them are found once. Every
    # candidate is then walked against exactly the same arrangement, so
    # no region is treated differently from any other.
    pieces = bw.pieces_from(look_segments, tol_mm=cg.DENSIFY_TOL_MM)
    families = [{"nominal_mm": f["thickness_mm"]}
                for f in gaps["wall_thickness_families_inferred"]]
    mates, mate_pairs = bw.mate_map(pieces, families=families)
    nodes = bw.node_graph(pieces)
    facing = bw.facing_ends(pieces, nodes)
    gaps_at = {}
    for grow in gaps["rows"]:
        for q in (grow["start_mm"], grow["end_mm"]):
            gaps_at.setdefault(bw._nkey(tuple(q)), grow)

    rows = []
    for n, g in enumerate(groups, start=1):
        english = [m for m in g.members
                   if m.stamp_class == r12.lg.ENGLISH_ROOM_STAMP]
        anchor = english[0] if english else g.members[0]
        seed = anchor.visible_centroid

        res = bw.boundary_at(seed, pieces, gaps_at=gaps_at, mates=mates,
                             facing=facing)
        chain = chain_from_walk(res, pieces, gap_rows=gaps["rows"],
                                exposed_ids=exposed,
                                interval_by_id=interval_by_id)
        basis = res["BOUNDARY_BASIS"]

        rows.append({"n": n, "group": g, "anchor": anchor, "seed": seed,
                     "trace": None, "chain": chain,
                     "BOUNDARY_BASIS": None if chain is None else basis,
                     "walk": {k: v for k, v in res.items()
                              if k not in ("steps", "FACE_SELECTION")},
                     "look": None,
                     "PHYSICAL_REGION_KEY": _face_key(chain),
                     "candidate_id": f"E1_3-{g.group_id}"})

    # §13 — several labels in one face are one physical region
    shared = {}
    for r in rows:
        if r["PHYSICAL_REGION_KEY"]:
            shared.setdefault(r["PHYSICAL_REGION_KEY"], []).append(r)
    for key, group in shared.items():
        toks = sorted({x["group"].english_token for x in group})
        for r in group:
            r["labels_sharing_this_physical_region"] = toks
            r["candidates_sharing_this_physical_region"] = sorted(
                x["candidate_id"] for x in group)

    for row in rows:
        inside = list(row.get("labels_sharing_this_physical_region") or ())
        ch = row["chain"]
        if ch and not inside:
            try:
                poly = Polygon([tuple(e["start_mm"]) for e in ch["CHAIN"]])
                if poly.is_valid:
                    for other in rows:
                        cx, cy = other["anchor"].visible_centroid
                        if poly.contains(Point(cx, cy)):
                            inside.append(other["group"].english_token)
            except Exception:
                pass
        row["labels_inside"] = tuple(sorted(set(inside)))
    return {"rows": rows, "material_prims": mat, "segments": segs,
            "physical_regions": {k: sorted(x["candidate_id"] for x in v)
                                 for k, v in shared.items()},
            "hidden_column_object_ids": sorted(hidden),
            "exposed_column_object_ids": sorted(exposed)}


# ------------------------------------------------------------- overlays
CHAIN_COLOUR = {
    bc.MATERIAL_WALL_FACE: ((0, 0, 0), 7, None),
    bc.CURVED_MATERIAL_FACE: ((0, 70, 220), 7, None),
    bc.GLAZING_BOUNDARY: ((0, 140, 220), 6, None),
    bc.EXPOSED_COLUMN_FACE: ((220, 0, 0), 8, None),
    bc.DOOR_PORTAL: ((255, 140, 0), 5, (18, 12)),
    bc.MATERIAL_CONTINUITY_SPAN: ((90, 90, 90), 5, (4, 4)),
    bc.OPEN_EDGE: ((0, 170, 60), 5, (26, 18)),
    bc.UNRESOLVED_EDGE: ((150, 0, 200), 5, (6, 10)),
}
HIDDEN_COLUMN_COLOUR = ((130, 130, 130), 3, (8, 8))


def _dashed(draw, pts, colour, width, dash):
    on, off = dash
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d = math.hypot(bx - ax, by - ay)
        if d <= 0:
            continue
        t, drawing = 0.0, True
        while t < d:
            u, v = min(t + (on if drawing else off), d), t
            if drawing:
                draw.line([(ax + (bx - ax) * v / d, ay + (by - ay) * v / d),
                           (ax + (bx - ax) * u / d, ay + (by - ay) * u / d)],
                          fill=colour, width=width)
            t, drawing = u, not drawing


def _arc_px(e, to_px):
    cx, cy = e["centre_mm"]
    r = e["radius_mm"]
    a0, a1 = e.get("start_angle_rad", 0.0), e.get("end_angle_rad", 0.0)
    n = 48
    return [to_px(cx + r * math.cos(a0 + (a1 - a0) * i / n),
                  cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _extent_of_chain(row, half_default=5000.0):
    cx, cy = row["anchor"].visible_centroid
    ch = row.get("chain")
    if ch and ch["CHAIN"]:
        xs = [p for e in ch["CHAIN"]
              for p in (e["start_mm"][0], e["end_mm"][0])]
        ys = [p for e in ch["CHAIN"]
              for p in (e["start_mm"][1], e["end_mm"][1])]
        cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
        half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0 + 2500.0
        return (cx, cy), half
    return (cx, cy), half_default


def _draw_chain(draw, chain, to_px, *, clip=(-300, 1800)):
    lo_, hi_ = clip
    for e in chain["CHAIN"]:
        colour, width, dash = CHAIN_COLOUR.get(
            e["CHAIN_ELEMENT"], ((0, 0, 0), 4, None))
        if e["CHAIN_ELEMENT"] == bc.CURVED_MATERIAL_FACE and "centre_mm" in e:
            pts = _arc_px(e, to_px)
        else:
            pts = [to_px(*e["start_mm"]), to_px(*e["end_mm"])]
        if len(pts) < 2 or not all(lo_ <= q[0] <= hi_ and lo_ <= q[1] <= hi_
                                   for q in pts):
            continue
        if dash:
            _dashed(draw, pts, colour, width, dash)
        else:
            draw.line(pts, fill=colour, width=width)
    # Where the walk ran out, the element has no length and would draw as
    # nothing. A reader has to be able to see that the boundary stops
    # there, so it is marked.
    for e in chain["CHAIN"]:
        if not e.get("THE_BOUNDARY_RUNS_OUT_HERE"):
            continue
        qx, qy = to_px(*e["start_mm"])
        if not (lo_ <= qx <= hi_ and lo_ <= qy <= hi_):
            continue
        r = 16
        draw.line([(qx - r, qy - r), (qx + r, qy + r)],
                  fill=RUNS_OUT_COLOUR, width=5)
        draw.line([(qx - r, qy + r), (qx + r, qy - r)],
                  fill=RUNS_OUT_COLOUR, width=5)


def chain_overlays(sheet, reg, gf, interp, rows, owner, out_dir) -> list:
    """§19 — every chain element gets a treatment a reader can tell apart."""
    from PIL import ImageDraw
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {p.object_id: p for p in gf["primitives"]}
    hidden_ids = set(owner["object_ids_that_do_not_own_the_room_face"])
    made = []
    for row in rows:
        centre, half = _extent_of_chain(row)
        got = r12._frame(sheet, reg, centre, half, (1500, 1500))
        if got is None:
            continue
        img, to_px, _box = got
        draw = ImageDraw.Draw(img)
        for oid, ivs in interp["roles"]["intervals"].items():
            parent = by_id.get(oid)
            if parent is None:
                continue
            for iv in ivs:
                if iv.role in (ir.CABINET_FRONT, ir.COUNTER_EDGE,
                               ir.CASEWORK, ir.POOL_INTERNAL_GEOMETRY,
                               ir.CONSTRUCTION_LINE):
                    colour, width, dash = r12.CASEWORK_COLOUR, 4, None
                elif iv.role == ir.AMBIGUOUS_PAIRED_BAND:
                    colour, width, dash = r12.AMBIGUOUS_COLOUR, 4, None
                elif (iv.provenance or {}).get("object_id") in hidden_ids:
                    colour, width, dash = HIDDEN_COLUMN_COLOUR
                else:
                    continue
                seg = cg._as_segment(r12.IntervalPrim(parent, iv))
                pts = [to_px(x, y) for x, y in seg.points(tol_mm=2.0)]
                if len(pts) >= 2 and all(-300 <= q[0] <= 1800
                                         and -300 <= q[1] <= 1800
                                         for q in pts):
                    if dash:
                        _dashed(draw, pts, colour, width, dash)
                    else:
                        draw.line(pts, fill=colour, width=width)
        if row.get("chain"):
            _draw_chain(draw, row["chain"], to_px)
        for d in gf["dimensions"]:
            mid = ((d.x1 + d.x2) / 2.0, (d.y1 + d.y2) / 2.0)
            if abs(mid[0] - centre[0]) > half or abs(mid[1] - centre[1]) > half:
                continue
            draw.line([to_px(d.x1, d.y1), to_px(d.x2, d.y2)],
                      fill=(0, 150, 0), width=2)
        px, py = to_px(*row["anchor"].visible_centroid)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(0, 0, 220),
                     width=4)
        if reg.rotation_deg:
            img = img.rotate(-reg.rotation_deg, expand=True)
        name = f"V2_OVERLAY_{row['candidate_id']}.png"
        img.save(out_dir / name)
        made.append({"candidate_id": row["candidate_id"],
                     "identity": row["group"].english_token,
                     "file": str(out_dir / name),
                     "legend": list(OVERLAY_LEGEND),
                     prov.RAW: r12._sha(out_dir / name)})
    return made


def whole_floor(sheet, reg, gf, rows, path) -> dict:
    from PIL import ImageDraw
    rgn = gf["region"]
    x0, y0 = float(rgn.x0), float(rgn.y0)
    x1, y1 = float(rgn.x1), float(rgn.y1)
    centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    half = max(x1 - x0, y1 - y0) / 2.0 + 2000.0
    got = r12._frame(sheet, reg, centre, half, (2400, 2400))
    if got is None:
        return {"file": None, "why": "the sheet could not be framed"}
    img, to_px, _box = got
    draw = ImageDraw.Draw(img)
    seen = set()
    for row in rows:
        key = row.get("PHYSICAL_REGION_KEY")
        if row.get("chain") and key not in seen:
            seen.add(key)
            _draw_chain(draw, row["chain"], to_px, clip=(-400, 2800))
    if reg.rotation_deg:
        img = img.rotate(-reg.rotation_deg, expand=True)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return {"file": Path(path).name, "pixels": list(img.size),
            "distinct_physical_regions_drawn": len(seen),
            "legend": list(OVERLAY_LEGEND), prov.RAW: r12._sha(path)}


# ---------------------------------------------------- the decision ledger
C_PHYSICAL_BOUNDARY_IS_ESTABLISHED = "PHYSICAL_BOUNDARY_IS_ESTABLISHED"
C_EVERY_CHAIN_ELEMENT_HAS_A_ROLE = "EVERY_CHAIN_ELEMENT_HAS_AN_ESTABLISHED_ROLE"
C_NO_GAP_IS_UNCLASSIFIED = "EVERY_GAP_ON_THE_BOUNDARY_IS_CLASSIFIED"
C_NO_PORTAL_WITHOUT_EVIDENCE = "NO_PORTAL_WITHOUT_POSITIVE_OPENING_EVIDENCE"
C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM = (
    "NO_UNEXPOSED_COLUMN_DEFORMS_THE_CLEAR_INTERNAL_BOUNDARY")
C_NO_AMBIGUOUS_BAND_ACTS_AS_WALL = "NO_AMBIGUOUS_PAIRED_BAND_ACTS_AS_WALL"
C_NO_COLLINEAR_ONLY_MATERIAL = "NO_COLLINEAR_ONLY_PROPAGATION_CREATES_MATERIAL"
C_OPEN_EDGES_CARRY_NO_MATERIAL = "OPEN_EDGES_CARRY_NO_MATERIAL"
C_NO_FRAME_EDGE_ON_THE_BOUNDARY = "NO_DRAWING_REGION_FRAME_EDGE_BOUNDS_IT"
C_CURVES_REMAIN_ANALYTICAL = "CURVES_REMAIN_ANALYTICAL"
C_LABEL_ONTOLOGY_IS_VALID = "LABEL_ONTOLOGY_IS_VALID"
C_OVERLAP_QA_PASSES = "OVERLAP_QA_PASSES"
C_PHYSICAL_TOPOLOGY_ARBITRATION_RESOLVED = (
    "PHYSICAL_TOPOLOGY_ARBITRATION_IS_RESOLVED")
C_BOUNDARY_ROLE_ARBITRATION_RESOLVED = "BOUNDARY_ROLE_ARBITRATION_IS_RESOLVED"
C_COLD_VISUAL_DOES_NOT_CHALLENGE_PHYSICALLY = (
    "COLD_VISUAL_V2_RAISES_NO_PHYSICAL_CHALLENGE")

RELEASE_GATES = (
    C_PHYSICAL_BOUNDARY_IS_ESTABLISHED, C_EVERY_CHAIN_ELEMENT_HAS_A_ROLE,
    C_NO_GAP_IS_UNCLASSIFIED, C_NO_PORTAL_WITHOUT_EVIDENCE,
    C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM, C_NO_AMBIGUOUS_BAND_ACTS_AS_WALL,
    C_NO_COLLINEAR_ONLY_MATERIAL, C_OPEN_EDGES_CARRY_NO_MATERIAL,
    C_NO_FRAME_EDGE_ON_THE_BOUNDARY, C_CURVES_REMAIN_ANALYTICAL,
    C_LABEL_ONTOLOGY_IS_VALID, C_OVERLAP_QA_PASSES,
    C_PHYSICAL_TOPOLOGY_ARBITRATION_RESOLVED,
    C_BOUNDARY_ROLE_ARBITRATION_RESOLVED,
    C_COLD_VISUAL_DOES_NOT_CHALLENGE_PHYSICALLY,
)

# Recorded because a reader wants to know, and structurally unable to
# decide anything. §16.
D_FUNCTIONAL_IDENTITY = "FUNCTIONAL_IDENTITY_IS_ESTABLISHED"
D_DETERMINISTIC_QA = "DETERMINISTIC_DRAWING_QA_STATE"
D_REGION_IS_SHARED = "THIS_PHYSICAL_REGION_HOLDS_ONE_LABEL_ONLY"
DIAGNOSTICS = (D_FUNCTIONAL_IDENTITY, D_DETERMINISTIC_QA, D_REGION_IS_SHARED)


def ledger_for(row, *, iv_by_id, arb, v2_split, label_class, overlaps,
               dqa_state) -> dl.Ledger:
    """One ledger. Every account of this decision derives from it."""
    L = dl.Ledger(row["candidate_id"])
    ch, phys = row["chain"], row["physical"]
    chain = ch["CHAIN"] if ch else []

    L.gate(C_PHYSICAL_BOUNDARY_IS_ESTABLISHED,
           phys["geometry_is_established"],
           f"PHYSICAL_GEOMETRY_STATUS is {phys['PHYSICAL_GEOMETRY_STATUS']}",
           dimension=ss.PHYSICAL_SPACE_GEOMETRY)

    missing = [e["SEQ"] for e in chain
               if e["CHAIN_ELEMENT"] in bc.MATERIAL_ELEMENTS
               and (iv_by_id.get(e.get("object_id")) is None
                    or iv_by_id[e["object_id"]].role == ir.UNKNOWN)]
    L.gate(C_EVERY_CHAIN_ELEMENT_HAS_A_ROLE, not missing,
           f"{len(missing)} material chain element(s) carry no established "
           f"interval role: {missing[:12]}" if missing else
           f"all {len(chain)} chain elements name an established role")

    unresolved = [g for g in row["gaps_on_chain"]
                  if g["GAP_CLASS"] == go.UNRESOLVED_GAP]
    L.gate(C_NO_GAP_IS_UNCLASSIFIED, not unresolved,
           f"{len(unresolved)} gap(s) on this boundary are UNRESOLVED_GAP: "
           f"{[g['GAP_ID'] for g in unresolved]}" if unresolved else
           f"all {len(row['gaps_on_chain'])} gap(s) on this boundary are "
           "classified")

    bad_portals = [
        g for g in row["gaps_on_chain"]
        if g["GAP_CLASS"] in go.IS_A_PORTAL and not g["confirming_evidence"]
        and len(g["probable_evidence"]) < go.PROBABLE_EVIDENCE_REQUIRED]
    L.gate(C_NO_PORTAL_WITHOUT_EVIDENCE, not bad_portals,
           f"{len(bad_portals)} portal(s) rest on neither confirming nor "
           "sufficient circumstantial evidence" if bad_portals else
           "every portal on this boundary carries positive opening evidence")

    hidden = row["hidden_on_chain"]
    L.gate(C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM, not hidden,
           f"{len(hidden)} unexposed structural column face(s) stand on "
           f"this boundary: {hidden[:8]}" if hidden else
           "no column deforms this boundary without established exposure")

    amb = [e.get("object_id") for e in chain
           if (iv_by_id.get(e.get("object_id")) is not None
               and iv_by_id[e["object_id"]].role == ir.AMBIGUOUS_PAIRED_BAND)]
    L.gate(C_NO_AMBIGUOUS_BAND_ACTS_AS_WALL, not amb,
           f"{len(amb)} band(s) CAD cannot tell from a counter or a bar act "
           f"as wall here: {sorted(x for x in amb if x)[:8]}" if amb else
           "no ambiguous band acts as wall on this boundary")

    coll = [e.get("object_id") for e in chain
            if (iv_by_id.get(e.get("object_id")) is not None
                and ir.established_by_collinearity_alone(
                    iv_by_id[e["object_id"]]))]
    L.gate(C_NO_COLLINEAR_ONLY_MATERIAL, not coll,
           f"{len(coll)} element(s) are material by collinearity alone: "
           f"{sorted(x for x in coll if x)[:8]}" if coll else
           "no element is material by collinearity alone")

    leak = [e["SEQ"] for e in chain
            if e["CHAIN_ELEMENT"] in bc.TOPOLOGY_ONLY_ELEMENTS
            and (e["material_present"] or e["wall_length_contribution_mm"])]
    L.gate(C_OPEN_EDGES_CARRY_NO_MATERIAL, not leak,
           f"element(s) {leak} carry material on a gap" if leak else
           "every portal, continuity span, open edge and unresolved edge "
           "contributes zero material")

    onframe = [e["SEQ"] for e in chain
               if e.get("ON_THE_DRAWING_REGION_FRAME")]
    L.gate(C_NO_FRAME_EDGE_ON_THE_BOUNDARY, not onframe,
           f"{len(onframe)} stretch(es) of this boundary fall on the "
           "drawing region outline, which is not a drawn edge: "
           f"{onframe[:8]}" if onframe else
           "no stretch of this boundary rests on the drawing region frame")

    curved = [e for e in chain
              if e["CHAIN_ELEMENT"] == bc.CURVED_MATERIAL_FACE]
    L.gate(C_CURVES_REMAIN_ANALYTICAL,
           all(e.get("radius_mm", 0) > 0 for e in curved),
           f"{len(curved)} curved face(s) keep centre, radius and angles")

    L.gate(C_LABEL_ONTOLOGY_IS_VALID,
           label_class in lo.IN_THE_COMPLETENESS_DENOMINATOR,
           f"label class is {label_class}")

    blocking = [o for o in overlaps if o.get("blocks_release")]
    L.gate(C_OVERLAP_QA_PASSES, not blocking,
           f"{len(blocking)} impermissible overlap(s) with another released "
           "region" if blocking else
           "no released region overlaps this one impermissibly")

    t = arb[ad.PHYSICAL_TOPOLOGY_ARBITRATION]
    L.gate(C_PHYSICAL_TOPOLOGY_ARBITRATION_RESOLVED,
           not t["blocks_physical_release"],
           f"physical topology arbitration is {t['STATE']}",
           dimension=ad.PHYSICAL_TOPOLOGY_ARBITRATION)
    r = arb[ad.BOUNDARY_ROLE_ARBITRATION]
    L.gate(C_BOUNDARY_ROLE_ARBITRATION_RESOLVED,
           not r["blocks_physical_release"],
           f"boundary role arbitration is {r['STATE']}",
           dimension=ad.BOUNDARY_ROLE_ARBITRATION)

    L.gate(C_COLD_VISUAL_DOES_NOT_CHALLENGE_PHYSICALLY,
           not v2_split["vetoes_physical_release"],
           ("the cold challenge raises physical findings: "
            + ", ".join(v2_split["PHYSICAL_STATUSES"]))
           if v2_split["vetoes_physical_release"] else
           ("the cold challenge raises no physical finding"
            + (" (its naming observations are recorded in the identity "
               "dimension and decide nothing here: "
               + ", ".join(v2_split["FUNCTIONAL_STATUSES"]) + ")"
               if v2_split["FUNCTIONAL_STATUSES"] else "")))

    # ---- diagnostics: recorded, and unable to decide anything
    i = arb[ad.FUNCTIONAL_IDENTITY_ARBITRATION]
    L.diagnostic(D_FUNCTIONAL_IDENTITY,
                 dl.PASS if i["STATE"] == ad.IDENTITY_AGREED else dl.FAIL,
                 f"functional identity arbitration is {i['STATE']}. "
                 + ad.IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE,
                 dimension=ad.FUNCTIONAL_IDENTITY_ARBITRATION)
    L.diagnostic(D_DETERMINISTIC_QA,
                 dl.PASS if dqa_state == dqa.DETERMINISTICALLY_CONSISTENT
                 else dl.FAIL,
                 f"deterministic drawing QA is {dqa_state}")
    sharers = row.get("labels_sharing_this_physical_region") or []
    L.diagnostic(D_REGION_IS_SHARED,
                 dl.PASS if len(sharers) <= 1 else dl.FAIL,
                 f"{len(sharers)} labels inhabit this one physical region: "
                 f"{sharers}. " + ONE_FACE_MAY_HOLD_SEVERAL_LABELS
                 if len(sharers) > 1 else
                 "one label inhabits this physical region")
    return L


# ---------------------------------------------------------------- phases
def _core(a):
    """Everything every phase needs, rebuilt from the same inputs."""
    prep = r12.prepare(a.decode)
    gf = r12.ground_floor(prep)
    interp = r12.interpret(gf, prep)
    by_id = {p.object_id: p for p in gf["primitives"]}
    mat_all = r12.interval_prims(interp["roles"]["intervals"], by_id)
    mat_segs = [cg._as_segment(m, role=r12.boundary_role_of(m.interval))
                for m in mat_all]

    owner = column_ownership_pass(interp, gf, material_segments=mat_segs)

    band_offsets = []
    for rows_ in interp["roles"]["intervals"].values():
        for iv in rows_:
            b = (iv.provenance or {}).get("band_offset_mm")
            if b:
                band_offsets.append(float(b))
    struct_ids = set(owner["object_ids_that_do_not_own_the_room_face"]) | \
        set(owner["object_ids_that_own_the_room_face"])
    raw_closure = cg.close_openings(mat_all, wall_layers=(),
                                    door_layers={"D"})
    # The door geometry the drawing actually holds. close_openings is only
    # given material geometry, and a door leaf is not material, so the
    # evidence has to be gathered from the DOOR intervals themselves.
    all_prims = r12.interval_prims(interp["roles"]["intervals"], by_id,
                                   only_material=False)
    door_segs = [cg._as_segment(m) for m in all_prims
                 if m.interval.role == ir.DOOR]
    gaps = gp.reclassify(raw_closure, material_segments=mat_segs,
                         structural_ids=struct_ids,
                         band_offsets_mm=band_offsets,
                         door_segments=door_segs)

    cand_json = json.loads((Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json")
                           .read_text(encoding="utf-8"))["candidates"]
    zone_tokens = {r12._english_token(c.get("label_as_drawn", ""))
                   for c in cand_json
                   if str(c.get("candidate_id", "")).startswith("FZ")}
    ontology = lo.classify(interp["labels"]["groups"], region=gf["region"],
                           a18_zone_tokens=sorted(t for t in zone_tokens if t),
                           material_segments=mat_segs)
    built = build_e1_3_candidates(gf, interp, ontology=ontology, gaps=gaps,
                                  owner=owner)
    return {"prep": prep, "gf": gf, "interp": interp, "owner": owner,
            "gaps": gaps, "raw_closure": raw_closure, "ontology": ontology,
            "built": built, "rows": built["rows"], "cand_json": cand_json,
            "mat_segs": mat_segs, "door_segments": door_segs,
            "iv_by_id": {iv.interval_id: iv
                         for rows_ in interp["roles"]["intervals"].values()
                         for iv in rows_}}


def _statuses(st):
    """Physical and functional status for every candidate."""
    a18_by_token = r12._a18_index(st["cand_json"])
    label_class = {r.group_id: r.label_class for r in st["ontology"]["rows"]}
    gap_by_id = {g["GAP_ID"]: g for g in st["gaps"]["rows"]}
    for r in st["rows"]:
        g = r["group"]
        r["a18"] = a18_by_token.get(g.english_token, [])
        r["label_class"] = label_class.get(g.group_id, lo.UNRESOLVED_TEXT)
        ch = r["chain"]
        # A region is ESTABLISHED_OPEN only where the drawing itself shows
        # an edge with nothing built along it. Stretches the local window
        # cut are not evidence of openness, so they do not count toward it.
        drawn_open = 0.0 if not ch else sum(
            e["length_mm"] for e in ch["CHAIN"]
            if e["CHAIN_ELEMENT"] in bc.NO_MATERIAL_EXISTS_HERE
            and not e.get("ON_THE_LOCAL_WINDOW_EDGE"))
        r["length_open_on_the_drawings_own_evidence_mm"] = round(drawn_open, 3)
        r["physical"] = ss.physical_status(
            chain=dict(ch, length_with_no_material_mm=drawn_open) if ch
            else {"CHAIN": [], "CLOSED_BY_DRAWN_MATERIAL": False,
                  "length_with_no_material_mm": 0.0, "runs": 0},
            any_material_established=bool(ch and ch["CHAIN"]))
        r["gaps_on_chain"] = [] if not ch else [
            gap_by_id[e["GAP_ID"]] for e in ch["CHAIN"]
            if e.get("GAP_ID") in gap_by_id]
        r["hidden_on_chain"] = [] if not ch else sorted({
            e.get("object_id") for e in ch["CHAIN"]
            if e.get("CLEAR_FACE_OWNERSHIP_STATUS")
            == co.ARCHITECTURAL_FACE_OWNS and e.get("object_id")})
    return st


def phase_geometry(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {}

    rules = None
    if a.rules and Path(a.rules).exists():
        from engine import blind_input_contract as bicm
        rules = bicm.general_rules(json.loads(
            Path(a.rules).read_text(encoding="utf-8")))
    seal = r12.build_sandbox(a.sandbox, decode=a.decode, a18_dir=a.a18_dir,
                             rules=rules, raster=a.raster,
                             prior_e1=a.prior_e1, prior_e1_1=a.prior_e1_1)

    st = _statuses(_core(a))
    gf, interp, rows, owner = st["gf"], st["interp"], st["rows"], st["owner"]
    src = r12._source(st["prep"], gf, a)

    _write(out, artifacts, "E1_3_ATOMIC_INTERVAL_ROLE_REGISTER.json", {
        "source": src,
        "carried_forward_unchanged": (
            "engine.atomic_interval and engine.interval_role are the frozen "
            "E1.2 modules, imported and not modified. E1.3 changes what is "
            "concluded about gaps, columns and open regions, not how an "
            "interval is cut or how its role is established"),
        "CUT_REASONS": list(ai.CUT_REASONS),
        "ROLES": list(ir.ROLES),
        "entities": interp["roles"]["entity_count"],
        "intervals": interp["roles"]["interval_count"],
        "entities_carrying_more_than_one_role":
            interp["roles"]["entities_with_more_than_one_role"],
        "counts_by_role": interp["roles"]["counts_by_role"],
        "intervals_that_may_bound_material":
            interp["roles"]["intervals_that_may_bound_material"],
        "material_length_mm": interp["roles"]["material_length_mm"],
        "frozen_parameters": {"atomic_interval": ai.frozen_parameters(),
                              "interval_role": ir.frozen_parameters()},
        "INTERVALS": [iv.record() for iv in interp["roles"]["flat"]],
    })

    _write(out, artifacts, "E1_3_GAP_ONTOLOGY_REGISTER.json", {
        "source": src,
        "the_correction": go.TWO_ENDS_FACING_IS_NOT_A_DOOR,
        "a_junction_and_a_door_are_different_ontologies":
            go.A_JUNCTION_AND_A_DOOR_ARE_DIFFERENT_ONTOLOGIES,
        "width_families_come_from_the_drawing":
            go.WIDTH_FAMILIES_COME_FROM_THE_DRAWING,
        "GAP_CLASSES": list(go.GAP_CLASSES),
        "counts_by_class": st["gaps"]["counts_by_class"],
        "candidate_gaps": st["gaps"]["candidate_gaps"],
        "closed_as_portal": st["gaps"]["closed_as_portal"],
        "closed_as_material_continuity":
            st["gaps"]["closed_as_material_continuity"],
        "left_open_or_unresolved": st["gaps"]["left_open"],
        "E1_2_WOULD_HAVE_CLOSED": st["gaps"]["E1_2_WOULD_HAVE_CLOSED"],
        "wall_thickness_families_inferred":
            st["gaps"]["wall_thickness_families_inferred"],
        "opening_width_families_from_confirmed_doors":
            st["gaps"]["opening_width_families_from_confirmed_doors"],
        "frozen_parameters": gp.frozen_parameters(),
        "GAPS": st["gaps"]["rows"],
    })

    portals = [g for g in st["gaps"]["rows"] if g["IS_A_PORTAL"]]
    _write(out, artifacts, "E1_3_PORTAL_EVIDENCE_REGISTER.json", {
        "source": src,
        "rule": ("a gap becomes a portal on positive evidence that an "
                 "opening was drawn, or on independent circumstantial "
                 "evidences at or above the required count, and never on "
                 "the shape of the gap alone"),
        "CONFIRMING_EVIDENCE": list(go.CONFIRMING_EVIDENCE),
        "PROBABLE_EVIDENCE": list(go.PROBABLE_EVIDENCE),
        "PROBABLE_EVIDENCE_REQUIRED": go.PROBABLE_EVIDENCE_REQUIRED,
        "door_intervals_searched": len(st["door_segments"]),
        "portals": len(portals),
        "confirmed": sum(1 for g in portals
                         if g["GAP_CLASS"] == go.CONFIRMED_DOOR_PORTAL),
        "probable": sum(1 for g in portals
                        if g["GAP_CLASS"] == go.PROBABLE_DOOR_PORTAL),
        "PORTALS": portals,
    })

    _write(out, artifacts, "E1_3_COLUMN_EXISTENCE_REGISTER.json", {
        "source": src,
        "a_touched_wall_is_not_a_structure":
            co.A_TOUCHED_WALL_IS_NOT_A_STRUCTURE,
        "EXISTENCE_STATUSES": list(co.EXISTENCE_STATUSES),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["COLUMN_EXISTENCE_STATUS"] == s)
                   for s in co.EXISTENCE_STATUSES},
        "columns_whose_only_structural_in_kind_evidence_is_wall_contact":
            [r["COLUMN_ID"] for r in owner["rows"]
             if r["only_structural_in_kind_evidence_is_wall_contact"]],
        "COLUMNS": [{k: v for k, v in r.items()
                     if k in ("COLUMN_ID", "member_object_ids", "size_mm",
                              "layers", "blocks", "footprint_box_mm",
                              "COLUMN_EXISTENCE_STATUS", "evidence",
                              "evidence_that_is_structural_in_kind",
                              "only_structural_in_kind_evidence_is_wall_contact",
                              "why_existence")}
                    for r in owner["rows"]],
    })

    _write(out, artifacts, "E1_3_COLUMN_EXPOSURE_REGISTER.json", {
        "source": src,
        "EXPOSURE_STATUSES": list(co.EXPOSURE_STATUSES),
        "EXPOSURE_EVIDENCE": list(co.EXPOSURE_EVIDENCE),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["EXPOSED_TO_ROOM_STATUS"] == s)
                   for s in co.EXPOSURE_STATUSES},
        "architectural_faces_tested_against":
            owner["architectural_faces_tested_against"],
        "how_continuation_is_tested": (
            "against COLLINEAR RUNS. A wall face in CAD is cut at every "
            "intersection, so each piece of it stops at the column it "
            "passes; asking whether one piece spans the footprint would "
            "answer no for every column ever drawn inside a wall"),
        "COLUMNS": [{k: v for k, v in r.items()
                     if k in ("COLUMN_ID", "EXPOSED_TO_ROOM_STATUS",
                              "exposure_evidence",
                              "architectural_face_continues_across",
                              "an_architectural_face_terminates_at_the_footprint",
                              "why_exposure")}
                    for r in owner["rows"]],
    })

    _write(out, artifacts, "E1_3_CLEAR_FACE_OWNERSHIP_REGISTER.json", {
        "source": src,
        "existence_is_not_ownership": co.EXISTENCE_IS_NOT_OWNERSHIP,
        "both_geometries_are_kept": co.BOTH_GEOMETRIES_ARE_KEPT,
        "neither_status_may_deform_a_room_without_exposure":
            co.NEITHER_STATUS_MAY_DEFORM_A_ROOM_WITHOUT_EXPOSURE,
        "OWNERSHIP_STATUSES": list(co.OWNERSHIP_STATUSES),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["CLEAR_FACE_OWNERSHIP_STATUS"] == s)
                   for s in co.OWNERSHIP_STATUSES},
        "object_ids_that_own_the_room_face":
            owner["object_ids_that_own_the_room_face"],
        "object_ids_that_do_not_own_the_room_face":
            owner["object_ids_that_do_not_own_the_room_face"],
        "COLUMNS": [{k: v for k, v in r.items()
                     if k in ("COLUMN_ID", "COLUMN_EXISTENCE_STATUS",
                              "EXPOSED_TO_ROOM_STATUS",
                              "CLEAR_FACE_OWNERSHIP_STATUS",
                              "structural_object_relation",
                              "may_deform_the_clear_internal_boundary",
                              "why_ownership")}
                    for r in owner["rows"]],
    })

    chains = []
    for r in rows:
        ch = r["chain"]
        if ch is not None:
            bc.assert_no_material_on_a_gap(ch)
        chains.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "LABEL_CLASS": r["label_class"],
            "PHYSICAL_REGION_KEY": r["PHYSICAL_REGION_KEY"],
            "labels_sharing_this_physical_region":
                r.get("labels_sharing_this_physical_region") or [],
            "candidates_sharing_this_physical_region":
                r.get("candidates_sharing_this_physical_region") or [],
            "PHYSICAL_GEOMETRY_STATUS":
                r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
            "why_physical": r["physical"]["why"],
            "labels_inside": list(r["labels_inside"]),
            "CLOSED_BY_DRAWN_MATERIAL": bool(
                ch and ch["CLOSED_BY_DRAWN_MATERIAL"]),
            "elements": 0 if ch is None else len(ch["CHAIN"]),
            "runs": 0 if ch is None else ch["runs"],
            "material_length_mm": 0.0 if ch is None
            else ch["material_length_mm"],
            "length_with_no_material_mm": 0.0 if ch is None
            else ch["length_with_no_material_mm"],
            "length_by_chain_element": {} if ch is None
            else ch["length_by_chain_element"],
            "BOUNDARY_BASIS": r.get("BOUNDARY_BASIS"),
            "RING_ENCLOSES_THE_POINT": bool(
                ch and ch.get("RING_ENCLOSES_THE_POINT")),
            "material_length_counted_once_mm": None if ch is None
            else ch.get("material_length_counted_once_mm"),
            "clear_internal_area_mm2": None if ch is None
            else ch.get("ring_area_mm2"),
            "faces_the_point_can_see": None if ch is None
            else ch.get("faces_the_point_can_see"),
            "rings_that_close_but_not_around_the_point": None if ch is None
            else ch.get("rings_that_close_but_not_around_the_point"),
            "islands_standing_in_the_region": [] if ch is None
            else ch.get("islands_standing_in_the_region") or [],
            "FACE_SELECTION": [] if ch is None
            else ch.get("FACE_SELECTION") or [],
            "faces_walked_on_the_opposite_side_of_their_wall_body": 0
            if ch is None else sum(
                1 for f in (ch.get("FACE_SELECTION") or [])
                if f.get("THE_WALK_IS_ON_THE_ROOM_SIDE_FACE") is False),
            "THIS_IS_NOT_A_PROPOSED_BOUNDARY": None if ch is None
            else ch.get("THIS_IS_NOT_A_PROPOSED_BOUNDARY"),
            "PHYSICAL_BOUNDARY_CHAIN": [] if ch is None else ch["CHAIN"],
            "run_endpoints": [] if ch is None else ch["run_endpoints"],
        })
    _write(out, artifacts, "E1_3_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json", {
        "source": src,
        "an_open_edge_is_a_result": bc.AN_OPEN_EDGE_IS_A_RESULT,
        "a_chain_is_not_a_polygon": bc.A_CHAIN_IS_NOT_A_POLYGON,
        "order_and_connectivity_are_the_point":
            bc.ORDER_AND_CONNECTIVITY_ARE_THE_POINT,
        "what_an_open_edge_length_is_and_is_not": WHAT_AN_OPEN_EDGE_LENGTH_IS,
        "one_face_may_hold_several_labels": ONE_FACE_MAY_HOLD_SEVERAL_LABELS,
        "THE_CORRECTED_MECHANISM": E1_3_CORRECTED_MECHANISM,
        "how_a_face_is_selected": bw.WHY_A_FACE_IS_SELECTED,
        "why_a_closed_ring_is_checked_against_the_point":
            bw.WHY_A_CLOSED_RING_IS_CHECKED,
        "why_the_innermost_ring": bw.WHY_THE_INNERMOST_RING,
        "why_nothing_is_proposed_where_nothing_is_established":
            bw.WHY_NOTHING_IS_PROPOSED,
        "why_the_walk_stops": bw.WHY_THE_WALK_STOPS,
        "why_a_wall_end_returns": bw.WHY_A_WALL_END_RETURNS,
        "why_a_single_line_end_turns": bw.WHY_A_SINGLE_LINE_END_TURNS,
        "boundary_open_at_an_unclassified_gap":
            bw.BOUNDARY_OPEN_AT_AN_UNCLASSIFIED_GAP,
        "what_a_disconnected_fragment_is":
            bw.WHAT_A_DISCONNECTED_FRAGMENT_IS,
        "boundary_walk_frozen_parameters": bw.frozen_parameters(),
        "CHAIN_ELEMENTS": list(bc.CHAIN_ELEMENTS),
        "MATERIAL_ELEMENTS": list(bc.MATERIAL_ELEMENTS),
        "distinct_physical_regions": len(st["built"]["physical_regions"]),
        "physical_regions": st["built"]["physical_regions"],
        "counts_by_physical_status": {
            s: sum(1 for c in chains if c["PHYSICAL_GEOMETRY_STATUS"] == s)
            for s in ss.PHYSICAL_GEOMETRY_STATUSES},
        "frozen_parameters": bc.frozen_parameters(),
        "REGIONS": chains,
    })

    stairs = stc.detect(gf["primitives"])
    _write(out, artifacts, "E1_3_STAIR_COMPLETENESS_REGISTER.json", {
        "source": src, **{k: v for k, v in stairs.items() if k != "rows"},
        "ASSEMBLIES": stairs.get("rows", []),
    })

    ledger = led.Ledger()
    for row in seal.get("inputs_made_available", ()):
        ledger.offer(row, at=row.get("placed_at", ""))
    manifest = dict(seal)
    manifest["MODEL"] = ei3.MODEL
    _write(out, artifacts, "E1_3_INPUT_MANIFEST.json", manifest)

    reg_r, sheet = _registered_sheet(a, gf)
    v1_dir = out / "visual" / "v1_source_only"
    crops = r12.source_crops(sheet, reg_r, rows, v1_dir) if sheet else []
    tasks = []
    for row in rows:
        crop = next((c for c in crops
                     if c["candidate_id"] == row["candidate_id"]), None)
        t = vc.Task(task_id=f"V1-{row['candidate_id']}",
                    candidate_id=row["candidate_id"],
                    identity=row["group"].english_token,
                    crop_path=(crop or {}).get("file", ""),
                    stage=vc.V1, brief=vc.V1_BRIEF)
        tasks.append(t.manifest())
    _write(out, artifacts, "E1_3_VISUAL_V1_REGISTER.json", {
        "STAGE": vc.V1, "status": "AWAITING_ANSWERS",
        "an_overlay_anchors_a_reader": vc.AN_OVERLAY_ANCHORS_A_READER,
        "what_the_challenger_never_receives":
            vc.WHAT_THE_CHALLENGER_NEVER_RECEIVES,
        "brief": vc.V1_BRIEF,
        "observation_vocabulary": list(vc.V1_OBSERVATIONS),
        "EDGE_RELATIONS": list(edge.EDGE_RELATIONS),
        "internal_continuity_is_not_openness":
            edge.INTERNAL_CONTINUITY_IS_NOT_OPENNESS,
        "a_subzone_is_not_a_separator": edge.A_SUBZONE_IS_NOT_A_SEPARATOR,
        "crops": crops, "task_manifests": tasks, "answers": [],
    })

    (out / "_E1_3_ARTIFACTS_GEOMETRY.json").write_text(
        json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
    (out / "_E1_3_STATE.json").write_text(json.dumps({
        "candidates": [{
            "candidate_id": r["candidate_id"],
            "identity": r["group"].english_token,
            "PHYSICAL_GEOMETRY_STATUS":
                r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
            "PHYSICAL_REGION_KEY": r["PHYSICAL_REGION_KEY"],
            "labels_inside": list(r["labels_inside"]),
            "chain_elements": 0 if r["chain"] is None
            else len(r["chain"]["CHAIN"]),
        } for r in rows],
    }, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "phase": "geometry",
        "candidates": len(rows),
        "distinct_physical_regions": len(st["built"]["physical_regions"]),
        "gaps": st["gaps"]["counts_by_class"],
        "E1_2_would_have_closed": st["gaps"]["E1_2_WOULD_HAVE_CLOSED"],
        "E1_3_closes_as_portal": st["gaps"]["closed_as_portal"],
        "columns": {s: sum(1 for r in owner["rows"]
                           if r["CLEAR_FACE_OWNERSHIP_STATUS"] == s)
                    for s in co.OWNERSHIP_STATUSES},
        "physical_status": {
            s: sum(1 for c in chains if c["PHYSICAL_GEOMETRY_STATUS"] == s)
            for s in ss.PHYSICAL_GEOMETRY_STATUSES},
        "artifacts": len(artifacts),
    }, indent=2))
    return 0


def phase_v2_inputs(a) -> int:
    out = Path(a.out)
    artifacts = json.loads((out / "_E1_3_ARTIFACTS_GEOMETRY.json")
                           .read_text(encoding="utf-8"))
    v1 = json.loads((out / "E1_3_VISUAL_V1_REGISTER.json")
                    .read_text(encoding="utf-8"))
    if v1.get("status") != "FROZEN":
        raise SystemExit("V2 may not be prepared before V1 is frozen. "
                         + vc.AN_OVERLAY_ANCHORS_A_READER)
    st = _statuses(_core(a))
    reg_r, sheet = _registered_sheet(a, st["gf"])
    overlays = []
    if sheet:
        overlays = chain_overlays(sheet, reg_r, st["gf"], st["interp"],
                                  st["rows"], st["owner"],
                                  out / "visual" / "v2_overlays")
    v1_by = {x["candidate_id"]: x for x in v1.get("answers", [])}
    tasks = []
    for row in st["rows"]:
        ov = next((o for o in overlays
                   if o["candidate_id"] == row["candidate_id"]), None)
        crop = next((c for c in v1.get("crops", [])
                     if c["candidate_id"] == row["candidate_id"]), None)
        t = vc.Task(task_id=f"V2-{row['candidate_id']}",
                    candidate_id=row["candidate_id"],
                    identity=row["group"].english_token,
                    crop_path=(crop or {}).get("file", ""),
                    overlay_path=(ov or {}).get("file", ""),
                    legend=OVERLAY_LEGEND, stage=vc.V2, brief=vc.V2_BRIEF)
        m = t.manifest()
        m["frozen_v1_observation"] = v1_by.get(row["candidate_id"], {})
        tasks.append(m)
    _write(out, artifacts, "E1_3_VISUAL_V2_REGISTER.json", {
        "STAGE": vc.V2, "status": "AWAITING_ANSWERS",
        "brief": vc.V2_BRIEF,
        "V2_STATUSES": list(vc.V2_STATUSES),
        "PHYSICAL_STATUSES": list(vc.PHYSICAL_STATUSES),
        "FUNCTIONAL_STATUSES": list(vc.FUNCTIONAL_STATUSES),
        "over_capture_is_a_physical_claim":
            vc.OVER_CAPTURE_IS_A_PHYSICAL_CLAIM,
        "a_naming_status_may_not_veto": vc.A_NAMING_STATUS_MAY_NOT_VETO,
        "the_challenger_may_not_move_a_coordinate":
            vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
        "legend": list(OVERLAY_LEGEND),
        "overlays": overlays, "task_manifests": tasks, "answers": [],
    })
    (out / "_E1_3_ARTIFACTS_GEOMETRY.json").write_text(
        json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"phase": "v2-inputs", "overlays": len(overlays),
                      "tasks": len(tasks)}, indent=2))
    return 0



DEV_DIAGNOSTIC_DIR = Path("data/runs/7757/e1_3_development_diagnostic")

WHY_THE_CORRECTION_IS_AUDITED = (
    "the mechanism that proposes a boundary was rebuilt after three "
    "constructions failed. A rebuild can look like an improvement simply "
    "because the cases that were vetoed stopped being vetoed, so this "
    "register puts the three things side by side for every candidate "
    "uniformly: what the superseded construction proposed and what the "
    "challenge said about it, what the corrected mechanism proposes, and "
    "what a fresh challenge with no knowledge of any of it says now. "
    "Whether the general fix worked is read off this table, not asserted")

A_VETO_IDENTIFIES_A_FAILURE_CLASS_ONLY = (
    "the earlier challenge answers were used to name WHAT KIND of thing "
    "was wrong. No coordinate, length, area or corrected outline from any "
    "challenge was given to the corrected mechanism, and no threshold was "
    "moved to make a particular candidate pass")


def _correction_audit(a, rows, v2_by) -> dict:
    """§11 of the correction brief - the three states, side by side."""
    pre_v2, pre_props = {}, {}
    f = DEV_DIAGNOSTIC_DIR / "PRE_CORRECTION_V2_ANSWERS.json"
    if f.exists():
        doc = json.loads(f.read_text(encoding="utf-8"))
        pre_v2 = {x["candidate_id"]: x for x in doc.get("ANSWERS", ())}
    f = DEV_DIAGNOSTIC_DIR / "PRE_CORRECTION_PROPOSALS.json"
    if f.exists():
        doc = json.loads(f.read_text(encoding="utf-8"))
        for name, lst in (doc.get("PROPOSALS_BY_SUPERSEDED_CONSTRUCTION")
                          or {}).items():
            if not isinstance(lst, list):
                continue
            for x in lst:
                pre_props.setdefault(x["CANDIDATE_ID"], {})[name] = x

    out_rows = []
    for r in rows:
        cid = r["candidate_id"]
        ch = r["chain"]
        pv = pre_v2.get(cid)
        post = v2_by.get(cid)
        out_rows.append({
            "CANDIDATE_ID": cid,
            "identity": r["group"].english_token,
            "PRE_CORRECTION_V2": ({
                "STATUSES": pv.get("statuses"),
                "summary": pv.get("summary"),
                "reasons": pv.get("reasons"),
            } if pv else "NOT_ANSWERED_THE_ROUND_WAS_STOPPED"),
            "PRE_CORRECTION_PROPOSALS": pre_props.get(cid)
            or "NOT_PRESENT_IN_THE_DEVELOPMENT_DIAGNOSTIC",
            "CORRECTED_PROPOSAL": {
                "BOUNDARY_BASIS": r.get("BOUNDARY_BASIS"),
                "RING_ENCLOSES_THE_POINT": bool(
                    ch and ch.get("RING_ENCLOSES_THE_POINT")),
                "PHYSICAL_GEOMETRY_STATUS":
                    r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
                "elements": 0 if ch is None else len(ch["CHAIN"]),
                "material_length_counted_once_mm": None if ch is None
                else ch.get("material_length_counted_once_mm"),
                "clear_internal_area_mm2": None if ch is None
                else ch.get("ring_area_mm2"),
                "IS_A_PROPOSAL": bool(
                    ch and ch.get("RING_ENCLOSES_THE_POINT")),
                "withheld_because": None if (
                    ch and ch.get("RING_ENCLOSES_THE_POINT"))
                else bw.WHY_NOTHING_IS_PROPOSED,
            },
            "POST_CORRECTION_COLD_V2": ({
                "STATUSES": post.get("statuses"),
                "summary": post.get("summary"),
                "reasons": post.get("reasons"),
            } if post else "NOT_ANSWERED"),
        })
    return {
        "why_the_correction_is_audited": WHY_THE_CORRECTION_IS_AUDITED,
        "a_veto_identifies_a_failure_class_only":
            A_VETO_IDENTIFIES_A_FAILURE_CLASS_ONLY,
        "the_development_diagnostic_is_not_a_result": (
            "data/runs/7757/e1_3_development_diagnostic holds the "
            "superseded attempts. It is DEVELOPMENT_DIAGNOSTIC_ONLY and no "
            "geometry or quantity may be taken from it"),
        "counts": {
            "candidates": len(out_rows),
            "answered_in_the_pre_correction_round": sum(
                1 for x in out_rows
                if isinstance(x["PRE_CORRECTION_V2"], dict)),
            "answered_in_the_post_correction_round": sum(
                1 for x in out_rows
                if isinstance(x["POST_CORRECTION_COLD_V2"], dict)),
            "corrected_proposals_offered": sum(
                1 for x in out_rows
                if x["CORRECTED_PROPOSAL"]["IS_A_PROPOSAL"]),
            "corrected_proposals_withheld": sum(
                1 for x in out_rows
                if not x["CORRECTED_PROPOSAL"]["IS_A_PROPOSAL"]),
        },
        "CANDIDATES": out_rows,
    }


def phase_finalize(a) -> int:
    out = Path(a.out)
    artifacts = json.loads((out / "_E1_3_ARTIFACTS_GEOMETRY.json")
                           .read_text(encoding="utf-8"))
    v1 = json.loads((out / "E1_3_VISUAL_V1_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v2 = json.loads((out / "E1_3_VISUAL_V2_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v1_by = {x["candidate_id"]: x for x in v1.get("answers", [])}
    v2_by = {x["candidate_id"]: x for x in v2.get("answers", [])}

    st = _statuses(_core(a))
    gf, interp, rows, owner = st["gf"], st["interp"], st["rows"], st["owner"]
    iv_by_id = st["iv_by_id"]
    src = r12._source(st["prep"], gf, a)

    cands, seen_key = [], set()
    for r in rows:
        ch = r["chain"]
        if not ch or not ch["CLOSED_BY_DRAWN_MATERIAL"]:
            continue
        if r["PHYSICAL_REGION_KEY"] in seen_key:
            continue
        seen_key.add(r["PHYSICAL_REGION_KEY"])
        pts = [tuple(e["start_mm"]) for e in ch["CHAIN"]]
        if len(pts) >= 4:
            cands.append({"id": r["candidate_id"], "points": pts,
                          "label_group": r["group"].group_id,
                          "object_kind": ""})
    overlaps = rel.overlap_relations(cands)
    for o in overlaps:
        o["blocks_release"] = (o["relation"]
                               not in rel.OVERLAP_PERMITS_RELEASE)
    by_cand = {}
    for o in overlaps:
        by_cand.setdefault(o["a"], []).append(o)
        by_cand.setdefault(o["b"], []).append(o)
    iv_lookup = {iv.interval_id: {"role": iv.role,
                                  "may_bound_material": iv.may_bound_material}
                 for iv in interp["roles"]["flat"]}

    arb_rows, ident_rows, ledger_rows = [], [], []
    for r in rows:
        ch = r["chain"]
        a1 = v1_by.get(r["candidate_id"], {})
        a2 = v2_by.get(r["candidate_id"], {})
        rels = [e.get("EDGE_RELATION") for e in (a1.get("EDGES") or ())
                if isinstance(e, dict)]
        rels = [x for x in rels if edge.relation_is_valid(x)]
        split = vc.split_statuses(a2.get("statuses", ()))

        statements = []
        for c in r["a18"]:
            statements.append(c.get("pass_b_statement", ""))
            statements += list(c.get("pass_b_boundary_statements", ()))
        claim = rel.a18_topology_claim(*statements)
        a18_open = (True if claim == rel.OPEN
                    else False if claim == rel.CLOSED else None)
        cad_open = not bool(ch and ch["CLOSED_BY_DRAWN_MATERIAL"])

        chain = ch["CHAIN"] if ch else []
        unresolved_edges = [e["SEQ"] for e in chain
                            if e["CHAIN_ELEMENT"] == bc.UNRESOLVED_EDGE]
        amb = [e.get("object_id") for e in chain
               if (iv_by_id.get(e.get("object_id")) is not None
                   and iv_by_id[e["object_id"]].role
                   == ir.AMBIGUOUS_PAIRED_BAND)]
        unres_gaps = [g["GAP_ID"] for g in r["gaps_on_chain"]
                      if g["GAP_CLASS"] == go.UNRESOLVED_GAP]

        arb = ad.arbitrate(
            topology_args=dict(
                a18_says_open=a18_open, cad_open=cad_open,
                edge_relations=rels, unresolved_edges=unresolved_edges,
                v2_says_open_side_closed=(
                    vc.OPEN_SIDE_FALSELY_CLOSED in split["PHYSICAL_STATUSES"]),
                v2_says_wall_removed=(
                    vc.WALL_FALSELY_REMOVED in split["PHYSICAL_STATUSES"])),
            role_args=dict(
                ambiguous_bands=[x for x in amb if x],
                unresolved_gaps=unres_gaps,
                v2_role_challenges=[
                    s for s in split["PHYSICAL_STATUSES"]
                    if s in (vc.INTERNAL_CASEWORK_USED_AS_BOUNDARY,
                             vc.COUNTER_OR_BAR_USED_AS_WALL,
                             vc.COLUMN_ROLE_UNRESOLVED,
                             vc.COLUMN_EXPOSURE_UNRESOLVED,
                             vc.BOUNDARY_SEMANTIC_CONFLICT)]),
            identity_args=dict(
                labels_inside=r["labels_inside"],
                a18_identities=[r12._english_token(c.get("label_as_drawn", ""))
                                for c in r["a18"]],
                v2_subzone_suggested=(
                    vc.POSSIBLE_FUNCTIONAL_SUBZONE
                    in split["FUNCTIONAL_STATUSES"]),
                v2_wrong_functional_region=(
                    vc.WRONG_FUNCTIONAL_REGION
                    in split["FUNCTIONAL_STATUSES"])))
        r["arb"], r["v2_split"] = arb, split

        dims = dqa.dimension_cross_check(None, gf["dimensions"])
        dq = dqa.check(boundary=None, interval_roles=iv_lookup,
                       distinct_label_groups=set(r["labels_inside"]),
                       dimension_rows=dims,
                       overlap_relations=by_cand.get(r["candidate_id"], []),
                       a18_topology_conflict=False,
                       ambiguous_band_on_ring=())
        state = dq["DETERMINISTIC_QA_STATE"]
        r["dqa_state"] = state[0] if isinstance(state, list) else state

        L = ledger_for(r, iv_by_id=iv_by_id, arb=arb, v2_split=split,
                       label_class=r["label_class"],
                       overlaps=by_cand.get(r["candidate_id"], []),
                       dqa_state=r["dqa_state"])
        rec = L.record_out()
        vc.assert_no_naming_status_vetoes(rec["FAILED_RELEASE_GATES"])
        r["ledger"] = rec
        r["released"] = rec["DECISION"] == dl.RELEASED
        ledger_rows.append(rec)

        arb_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "A18_CANDIDATE_IDS": [c["candidate_id"] for c in r["a18"]],
            "a18_topology_claim": claim,
            "PHYSICAL_GEOMETRY_STATUS":
                r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
            ad.PHYSICAL_TOPOLOGY_ARBITRATION:
                arb[ad.PHYSICAL_TOPOLOGY_ARBITRATION],
            ad.BOUNDARY_ROLE_ARBITRATION: arb[ad.BOUNDARY_ROLE_ARBITRATION],
            "V1_EDGE_RELATIONS": edge.summarise(rels),
            "V2_PHYSICAL_STATUSES": split["PHYSICAL_STATUSES"],
            "V2_REASONS": a2.get("reasons", []),
        })
        fs = ss.functional_status(
            labels_inside=r["labels_inside"],
            subzone_suggested=(vc.POSSIBLE_FUNCTIONAL_SUBZONE
                               in split["FUNCTIONAL_STATUSES"]),
            separator_between_labels=(
                False if len(r.get("labels_sharing_this_physical_region")
                             or ()) > 1 else None))
        r["functional"] = fs
        ident_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "FUNCTIONAL_IDENTITY_STATUS": fs["FUNCTIONAL_IDENTITY_STATUS"],
            "REGION_RELATION": fs["REGION_RELATION"],
            "labels_sharing_this_physical_region":
                r.get("labels_sharing_this_physical_region") or [],
            ad.FUNCTIONAL_IDENTITY_ARBITRATION:
                arb[ad.FUNCTIONAL_IDENTITY_ARBITRATION],
            "V2_FUNCTIONAL_STATUSES": split["FUNCTIONAL_STATUSES"],
            "blocks_physical_geometry": False,
            "why": fs["why"],
        })

    released = [r for r in rows if r["released"]]
    withheld = [r for r in rows if not r["released"]]

    _write(out, artifacts,
           "E1_3_PHYSICAL_TOPOLOGY_ARBITRATION_REGISTER.json", {
               "source": src,
               "dimensions_may_disagree": (
                   "this register answers one question - is the region "
                   "enclosed, and where is it open. What it is called is "
                   "not here"),
               "TOPOLOGY_STATES": list(ad.TOPOLOGY_STATES),
               "ROLE_STATES": list(ad.ROLE_STATES),
               "EDGE_RELATIONS": list(edge.EDGE_RELATIONS),
               "internal_continuity_is_not_openness":
                   edge.INTERNAL_CONTINUITY_IS_NOT_OPENNESS,
               "counts_topology": {
                   s: sum(1 for x in arb_rows
                          if x[ad.PHYSICAL_TOPOLOGY_ARBITRATION]["STATE"] == s)
                   for s in ad.TOPOLOGY_STATES},
               "counts_boundary_role": {
                   s: sum(1 for x in arb_rows
                          if x[ad.BOUNDARY_ROLE_ARBITRATION]["STATE"] == s)
                   for s in ad.ROLE_STATES},
               "frozen_parameters": ad.frozen_parameters(),
               "rows": arb_rows,
           })

    _write(out, artifacts,
           "E1_3_FUNCTIONAL_IDENTITY_ARBITRATION_REGISTER.json", {
               "source": src,
               "identity_never_blocks_physical_release":
                   ad.IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE,
               "E1_decides_no_trade_zone": ss.E1_DECIDES_NO_TRADE_ZONE,
               "not_by_proximity_and_not_by_difference":
                   ss.NOT_BY_PROXIMITY_AND_NOT_BY_DIFFERENCE,
               "FUNCTIONAL_IDENTITY_STATUSES":
                   list(ss.FUNCTIONAL_IDENTITY_STATUSES),
               "IDENTITY_STATES": list(ad.IDENTITY_STATES),
               "REGION_RELATIONS": list(ss.REGION_RELATIONS),
               "counts": {s: sum(1 for x in ident_rows
                                 if x["FUNCTIONAL_IDENTITY_STATUS"] == s)
                          for s in ss.FUNCTIONAL_IDENTITY_STATUSES},
               "rows": ident_rows,
           })

    _write(out, artifacts, "E1_3_DECISION_LEDGER.json", {
        "source": src,
        "every_account_derives_from_the_ledger":
            dl.EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER,
        "a_diagnostic_is_not_a_gate": dl.A_DIAGNOSTIC_IS_NOT_A_GATE,
        "RELEASE_GATES": list(RELEASE_GATES),
        "DIAGNOSTICS_WHICH_DECIDE_NOTHING": list(DIAGNOSTICS),
        "released": len(released), "withheld": len(withheld),
        "by_failed_gate": {c: sum(1 for x in ledger_rows
                                  if c in x["FAILED_RELEASE_GATES"])
                           for c in RELEASE_GATES},
        "closure_is_not_a_target": CLOSURE_IS_NOT_A_TARGET,
        "frozen_parameters": dl.frozen_parameters(),
        "LEDGERS": ledger_rows,
    })

    geometry_rows = []
    for r in rows:
        ch = r["chain"]
        geometry_rows.append({
            "CAD_GEOMETRY_ID": r["candidate_id"],
            "A18_CANDIDATE_ID": ",".join(c["candidate_id"] for c in r["a18"]),
            "DRAWING_ID": "P7757_ARCHITECTURAL.dwg", "FLOOR": "GROUND",
            "label_as_drawn": r["group"].english_token,
            "LABEL_CLASS": r["label_class"],
            "PHYSICAL_REGION_KEY": r["PHYSICAL_REGION_KEY"],
            "labels_sharing_this_physical_region":
                r.get("labels_sharing_this_physical_region") or [],
            "PHYSICAL_GEOMETRY_STATUS":
                r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
            "FUNCTIONAL_IDENTITY_STATUS":
                r["functional"]["FUNCTIONAL_IDENTITY_STATUS"],
            "REGION_RELATION": r["functional"]["REGION_RELATION"],
            "RELEASED": r["released"],
            "CLOSED_BY_DRAWN_MATERIAL": bool(
                ch and ch["CLOSED_BY_DRAWN_MATERIAL"]),
            "material_length_mm": 0.0 if ch is None
            else ch["material_length_mm"],
            "length_with_no_material_mm": 0.0 if ch is None
            else ch["length_with_no_material_mm"],
            "length_by_chain_element": {} if ch is None
            else ch["length_by_chain_element"],
            "PHYSICAL_BOUNDARY_CHAIN": [] if ch is None else ch["CHAIN"],
            "labels_inside_this_region": list(r["labels_inside"]),
            "DECISION_LEDGER": r["ledger"],
            "ARBITRATION": {
                ad.PHYSICAL_TOPOLOGY_ARBITRATION:
                    r["arb"][ad.PHYSICAL_TOPOLOGY_ARBITRATION]["STATE"],
                ad.BOUNDARY_ROLE_ARBITRATION:
                    r["arb"][ad.BOUNDARY_ROLE_ARBITRATION]["STATE"],
                ad.FUNCTIONAL_IDENTITY_ARBITRATION:
                    r["arb"][ad.FUNCTIONAL_IDENTITY_ARBITRATION]["STATE"],
            },
            "V2_PHYSICAL_STATUSES": r["v2_split"]["PHYSICAL_STATUSES"],
            "V2_FUNCTIONAL_STATUSES": r["v2_split"]["FUNCTIONAL_STATUSES"],
            "WHY": r["ledger"]["WHY"],
        })
    _write(out, artifacts, "E1_3_CAD_GEOMETRY_REGISTER.json", {
        "source": src,
        "unit_of_role": "ATOMIC_ENTITY_INTERVAL",
        "unit_of_boundary": "PHYSICAL_BOUNDARY_CHAIN",
        "closure_is_not_a_target": CLOSURE_IS_NOT_A_TARGET,
        "E1_decides_no_trade_zone": ss.E1_DECIDES_NO_TRADE_ZONE,
        "counts_physical": {
            s: sum(1 for x in geometry_rows
                   if x["PHYSICAL_GEOMETRY_STATUS"] == s)
            for s in ss.PHYSICAL_GEOMETRY_STATUSES},
        "released_regions": len(released),
        "withheld_regions": len(withheld),
        "regions": geometry_rows,
    })

    _write(out, artifacts, "E1_3_COMPLETENESS_REGISTER.json", {
        "source": src,
        "denominator_rule": lo.SITE_CONTEXT_IS_NOT_A_SPACE,
        "label_classes": st["ontology"]["counts"],
        "PHYSICAL_AND_FUNCTIONAL_CANDIDATES":
            st["ontology"]["physical_and_functional_candidates"],
        "SITE_CONTEXT": st["ontology"]["site_context"],
        "candidates_traced": len(rows),
        "distinct_physical_regions": len(st["built"]["physical_regions"]),
        "physical_geometry_established": sum(
            1 for r in rows if r["physical"]["geometry_is_established"]),
        "released": len(released), "withheld": len(withheld),
        "a18_candidates_considered": len(st["cand_json"]),
        "what_success_means": CLOSURE_IS_NOT_A_TARGET,
    })

    _write(out, artifacts, "E1_3_CORRECTION_AUDIT_REGISTER.json",
           _correction_audit(a, rows, v2_by))

    _write(out, artifacts, "E1_3_DELTA_FROM_E1_2.json", _delta(a, rows))

    reg_r, sheet = _registered_sheet(a, gf)
    whole, locals_ = {}, []
    if sheet:
        whole = whole_floor(
            sheet, reg_r, gf, rows,
            out / "E1_3_GROUND_FLOOR_ON_THE_SOURCE_SHEET.png")
        if whole.get("file"):
            artifacts[whole["file"]] = whole[prov.RAW]
        locals_ = chain_overlays(sheet, reg_r, gf, interp, rows, owner,
                                 out / "local_overlays")
        for row in locals_:
            artifacts[f"local_overlays/{Path(row['file']).name}"] = \
                row[prov.RAW]
    for d, pat in ((out / "visual" / "v1_source_only",
                    "visual/v1_source_only"),
                   (out / "visual" / "v2_overlays", "visual/v2_overlays")):
        if d.exists():
            for f in sorted(d.glob("*.png")):
                artifacts[f"{pat}/{f.name}"] = r12._sha(f)
    v1f = out / "visual" / "v1_frozen_per_candidate"
    if v1f.exists():
        for f in sorted(v1f.glob("*.json")):
            artifacts[f"visual/v1_frozen_per_candidate/{f.name}"] = r12._sha(f)
    _write(out, artifacts, "E1_3_OVERLAY_INDEX.json", {
        "whole_floor": whole, "local_overlays": locals_,
        "v1_source_only_crops": "visual/v1_source_only/",
        "v2_challenge_overlays": "visual/v2_overlays/",
        "v1_frozen_answers_per_candidate": "visual/v1_frozen_per_candidate/",
        "drawn_on": "THE_ORIGINAL_SOURCE_SHEET",
        "legend": list(OVERLAY_LEGEND),
        "an_overlay_anchors_a_reader": vc.AN_OVERLAY_ANCHORS_A_READER,
    })
    for n in ("E1_3_VISUAL_V1_REGISTER.json", "E1_3_VISUAL_V2_REGISTER.json",
              "E1_3_INPUT_MANIFEST.json"):
        pth = out / n
        if pth.exists():
            _write(out, artifacts, n,
                   json.loads(pth.read_text(encoding="utf-8")))

    freeze = _freeze(a, st, artifacts, released, withheld)
    (out / "E1_3_FREEZE.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")

    print(json.dumps({
        "phase": "finalize",
        "candidates": len(rows),
        "distinct_physical_regions": len(st["built"]["physical_regions"]),
        "released": len(released), "withheld": len(withheld),
        "physical_status": {
            s: sum(1 for x in geometry_rows
                   if x["PHYSICAL_GEOMETRY_STATUS"] == s)
            for s in ss.PHYSICAL_GEOMETRY_STATUSES},
        "topology_arbitration": {
            s: sum(1 for x in arb_rows
                   if x[ad.PHYSICAL_TOPOLOGY_ARBITRATION]["STATE"] == s)
            for s in ad.TOPOLOGY_STATES},
        "functional_identity": {
            s: sum(1 for x in ident_rows
                   if x["FUNCTIONAL_IDENTITY_STATUS"] == s)
            for s in ss.FUNCTIONAL_IDENTITY_STATUSES},
        "by_failed_gate": {c: n for c, n in
                           ((c, sum(1 for x in ledger_rows
                                    if c in x["FAILED_RELEASE_GATES"]))
                            for c in RELEASE_GATES) if n},
        "artifacts": len(artifacts),
        "E1_3_RUN_HASH": freeze["E1_3_RUN_HASH"][:16],
    }, indent=2))
    return 0


DELTA_REASONS = (
    "NO_CHANGE",
    "GAP_RECLASSIFIED_PORTAL_WITHDRAWN",
    "GAP_RECLASSIFIED_AS_CONFIRMED_DOOR",
    "COLUMN_NO_LONGER_OWNS_THE_CLEAR_FACE",
    "OPEN_REGION_GAINED_A_BOUNDARY_CHAIN",
    "PHYSICAL_AND_FUNCTIONAL_STATUS_SEPARATED",
    "EDGE_RELATION_REPLACED_AN_OPEN_SIDE_COUNT",
    "SEVERAL_LABELS_SHARE_ONE_PHYSICAL_REGION",
    "RELEASE_TO_WITHHOLD",
    "WITHHOLD_TO_RELEASE",
    "OTHER_EXPLAINED",
)


def _delta(a, rows) -> dict:
    prior = Path(a.prior_e1_2) / "E1_2_CAD_GEOMETRY_REGISTER.json"
    if not prior.exists():
        return {"available": False,
                "why": "E1.2's geometry register was not admitted",
                "DELTA_REASONS": list(DELTA_REASONS)}
    body = json.loads(prior.read_text(encoding="utf-8"))
    by_token = {}
    for x in body.get("regions", ()):
        by_token.setdefault(x.get("label_as_drawn", ""), []).append(x)

    out_rows, counts = [], {}
    for r in rows:
        tok = r["group"].english_token
        pool = by_token.get(tok, [])
        prev = pool.pop(0) if pool else None
        ch = r["chain"]
        reasons = ["PHYSICAL_AND_FUNCTIONAL_STATUS_SEPARATED",
                   "EDGE_RELATION_REPLACED_AN_OPEN_SIDE_COUNT"]
        if prev is None:
            reasons.append("OTHER_EXPLAINED")
        else:
            was = bool(prev.get("RELEASED"))
            if was and not r["released"]:
                reasons.append("RELEASE_TO_WITHHOLD")
            elif r["released"] and not was:
                reasons.append("WITHHOLD_TO_RELEASE")
            elif r["released"] == was:
                reasons.append("NO_CHANGE")
            prev_roles = {s.get("boundary_role")
                          for s in (prev.get("BOUNDARY") or {})
                          .get("BOUNDARY_SEGMENTS", ())}
            now = {e["CHAIN_ELEMENT"] for e in (ch["CHAIN"] if ch else ())}
            if "VIRTUAL_PORTAL_BOUNDARY" in prev_roles \
                    and bc.DOOR_PORTAL not in now:
                reasons.append("GAP_RECLASSIFIED_PORTAL_WITHDRAWN")
            if bc.DOOR_PORTAL in now:
                reasons.append("GAP_RECLASSIFIED_AS_CONFIRMED_DOOR")
            if "COLUMN_FACE" in prev_roles and r["hidden_on_chain"]:
                reasons.append("COLUMN_NO_LONGER_OWNS_THE_CLEAR_FACE")
            if not prev.get("BOUNDARY") and ch is not None and ch["CHAIN"]:
                reasons.append("OPEN_REGION_GAINED_A_BOUNDARY_CHAIN")
        if len(r.get("labels_sharing_this_physical_region") or ()) > 1:
            reasons.append("SEVERAL_LABELS_SHARE_ONE_PHYSICAL_REGION")
        reasons = sorted(set(reasons))
        for x in reasons:
            counts[x] = counts.get(x, 0) + 1
        out_rows.append({
            "identity": tok,
            "E1_3_CANDIDATE_ID": r["candidate_id"],
            "E1_2_RELEASED": None if prev is None
            else bool(prev.get("RELEASED")),
            "E1_3_RELEASED": r["released"],
            "E1_2_OUTCOME": None if prev is None else prev.get("OUTCOME"),
            "E1_3_PHYSICAL_GEOMETRY_STATUS":
                r["physical"]["PHYSICAL_GEOMETRY_STATUS"],
            "E1_3_FUNCTIONAL_IDENTITY_STATUS":
                r["functional"]["FUNCTIONAL_IDENTITY_STATUS"],
            "E1_2_had_no_boundary_at_all": prev is not None
            and not prev.get("BOUNDARY"),
            "E1_3_chain_elements": 0 if ch is None else len(ch["CHAIN"]),
            "CHANGE_REASONS": reasons,
            "why": r["ledger"]["WHY"],
        })
    return {
        "available": True,
        "prior_register": str(prior),
        "prior_register_sha256": r12._sha(prior),
        "DELTA_REASONS": list(DELTA_REASONS),
        "reason_counts": counts,
        "no_quantity_is_compared": (
            "this register compares boundary evidence, roles and statuses. "
            "No area, length or quantity of either run is compared with the "
            "other, and no target was consulted"),
        "rows": out_rows,
    }


E1_3_MODULES = (
    "engine/edge_relation.py", "engine/gap_ontology.py",
    "engine/gap_pass.py", "engine/column_ownership.py",
    "engine/boundary_chain.py", "engine/space_status.py",
    "engine/arbitration_dimensions.py", "engine/decision_ledger.py",
    "engine/visual_challenger_v2.py", "engine/e1_3_inputs.py",
    "tools/run_e1_3.py",
)

CARRIED_FORWARD_UNCHANGED = (
    "engine/atomic_interval.py", "engine/interval_role.py",
    "engine/cad_geometry.py", "engine/e1_region.py",
    "engine/curve_semantics.py", "engine/label_grouping.py",
    "engine/label_ontology.py", "engine/raster_qa.py",
    "engine/deterministic_qa.py", "engine/stair_completeness.py",
    "engine/e1_release.py", "engine/visual_challenger.py",
    "engine/admission_ledger.py", "engine/e1_2_inputs.py",
    "engine/e1_1_inputs.py", "engine/e1_inputs.py",
    "engine/agent_sandbox.py", "tools/run_e1_2.py",
)

BENCHMARK_INFORMED_LINEAGE = (
    "engine/cad_adapter.py", "engine/cad_profile.py",
    "engine/cad_regions.py", "engine/drawing_region.py",
)


def _freeze(a, st, artifacts, released, withheld) -> dict:
    code = {}
    for f in (list(E1_3_MODULES) + list(CARRIED_FORWARD_UNCHANGED)
              + list(BENCHMARK_INFORMED_LINEAGE)):
        if Path(f).exists():
            code[f] = r12._sha(f)
    prior = Path(a.prior_e1_2) / "E1_2_FREEZE.json"
    owner = st["owner"]
    freeze = {
        "E1_3_MODEL": E1_3_MODEL,
        "RUN_ID": RUN_ID,
        "E1_3_RUN_CLASS": "CONTROLLED_INTEGRATION_REGRESSION",
        "supersedes_nothing": (
            "E1, E1.1 and E1.2 are preserved exactly as frozen. This is a "
            "separate iteration in its own directory"),
        "E1_3_CURRENT_RUN_BENCHMARK_INPUTS": "NONE",
        "what_the_external_review_supplied": (
            "named structural defects in E1.2's gap, column and QA "
            "ontologies, and no quantity. No expected area, target "
            "dimension or benchmark number entered this run"),
        "modules_written_for_E1_3": list(E1_3_MODULES),
        "modules_carried_forward_unchanged": list(CARRIED_FORWARD_UNCHANGED),
        "modules_with_benchmark_informed_lineage":
            list(BENCHMARK_INFORMED_LINEAGE),
        "SOURCE_HASHES": {
            "cad_decode": r12._sha(a.decode) if Path(a.decode).exists()
            else "",
            "source_sheet": r12._sha(a.raster) if Path(a.raster).exists()
            else "",
            "e1_2_freeze": r12._sha(prior) if prior.exists() else "",
        },
        "CODE_VERSION_HASHES": code,
        "MODEL_HASHES": {
            "edge_relation": edge.model_hash(),
            "gap_ontology": go.model_hash(),
            "column_ownership": co.model_hash(),
            "boundary_chain": bc.model_hash(),
            "boundary_walk": bw.model_hash(),
            "space_status": ss.model_hash(),
            "arbitration_dimensions": ad.model_hash(),
            "decision_ledger": dl.model_hash(),
            "visual_challenger_v2": vc.model_hash(),
            "e1_3_inputs": ei3.model_hash(),
            "interval_role": ir.model_hash(),
            "atomic_interval": ai.model_hash(),
        },
        "ARTIFACTS": artifacts,
        "NOT_HASHED_AND_WHY": {
            "E1_3_FREEZE.json":
                "the freeze cannot carry its own hash. Its integrity is "
                "E1_3_RUN_HASH, taken over everything above",
            "_E1_3_ARTIFACTS_GEOMETRY.json":
                "working state handed from the geometry phase to the "
                "finalize phase. Every register it points at is hashed "
                "above",
            "_E1_3_STATE.json":
                "working state handed between phases, as above",
        },
        "COUNTS": {
            "entities": st["interp"]["roles"]["entity_count"],
            "intervals": st["interp"]["roles"]["interval_count"],
            "candidates": len(st["rows"]),
            "distinct_physical_regions":
                len(st["built"]["physical_regions"]),
            "released": len(released),
            "withheld": len(withheld),
            "candidate_gaps": st["gaps"]["candidate_gaps"],
            "gaps_closed_as_portal": st["gaps"]["closed_as_portal"],
            "gaps_E1_2_would_have_closed":
                st["gaps"]["E1_2_WOULD_HAVE_CLOSED"],
            "columns_assessed": len(owner["rows"]),
            "columns_owning_the_room_face": sum(
                1 for r in owner["rows"]
                if r["may_deform_the_clear_internal_boundary"]),
        },
        "what_E1_3_did_not_do": [
            "no benchmark, Excel, reconciliation, manual take-off, "
            "corrected area or external grading was opened",
            "no area was compared with anything",
            "no quantity was computed and no trade zone was decided",
            "no open edge was closed to obtain a polygon",
            "no structural column was deleted",
            "the visual challenger moved no coordinate and produced no "
            "polygon",
            "E1, E1.1 and E1.2 were not modified, rerun or overwritten",
        ],
        "what_success_means": CLOSURE_IS_NOT_A_TARGET,
    }
    freeze["E1_3_RUN_HASH"] = prov.canonical_sha256(freeze)
    return freeze


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", required=True,
                    choices=("geometry", "v2-inputs", "finalize"))
    ap.add_argument("--decode",
                    default="data/runs/cad_convert/P7757_ARCHITECTURAL.json")
    ap.add_argument("--a18-dir", default="data/runs/7757/blind/A18-GF-001")
    ap.add_argument("--raster",
                    default="data/runs/7757/blind/A18-GF-001/images/"
                            "page-01.jpeg")
    ap.add_argument("--prior-e1", default="data/runs/7757/e1")
    ap.add_argument("--prior-e1-1", default="data/runs/7757/e1_1")
    ap.add_argument("--prior-e1-2", default="data/runs/7757/e1_2")
    ap.add_argument("--rules",
                    default="data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
    ap.add_argument("--sandbox", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.phase == "geometry":
        if not a.sandbox:
            ap.error("--sandbox is required for the geometry phase")
        return phase_geometry(a)
    if a.phase == "v2-inputs":
        return phase_v2_inputs(a)
    return phase_finalize(a)


if __name__ == "__main__":
    raise SystemExit(main())
