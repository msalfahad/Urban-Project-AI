"""E1.4 — the evidence the walk is given, repaired, and run on P7757 GF.

E1.3's mechanism was sound. Five things upstream of it were not, and the
external review named all five:

  the freeze did not bind engine/boundary_walk.py, which is the whole
  mechanism, because the manifest was maintained by hand;

  POOL_CONTOUR was in E1.2's MAY_BOUND_MATERIAL and a curve was given a
  material role for being a curve, so the edge of the water bounded
  rooms;

  a label's seed was one stamp's point with nothing asked about whether
  the label's own anchors agree, so WASH was seeded across the wall it
  is separated from;

  openings were looked for from wall-end gaps only, so a doorway the gap
  search never raised could not reach classification however plainly the
  door is drawn;

  a region whose walk ran out kept one chain, and every other side of it
  the drawing does establish was not recovered.

None of that is repaired by a new region-reconstruction algorithm. The
walk is unchanged: room-side faces chosen by pairing, no nearest face, no
area optimisation, no closure optimisation, exact curves, a ring that is
only its own chain, and an open region that stays open. What changes is
what the walk is given, and how a partial result is written down.

  DO NOT START E2. DO NOT OPEN EXCEL. DO NOT RECONCILE. NO BOQ QUANTITY
  IS CALCULATED HERE, and no known area is consulted anywhere in it.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine import boundary_capability as bcap
from engine import boundary_chain as bc
from engine import boundary_fragment as bf
from engine import boundary_walk as bw
from engine import cad_geometry as cg
from engine import column_ownership as co
from engine import column_validation as cv
from engine import e1_4_inputs as e14
from engine import execution_provenance as ep
from engine import export_provenance as prov
from engine import gap_pass as gp
from engine import interval_role as ir
from engine import label_anchor as la
from engine import label_ontology as lo
from engine import line_semantics as ls
from engine import opening_discovery as od
from engine import ring_qa as rq
from engine import traversal_geometry as tg
from engine import visual_finding as vf
from tools import run_e1_2 as r12
from tools import run_e1_3 as r13

E1_4_MODEL = e14.MODEL
RUN_ID = e14.E1_4Run().run_id


# ---------------------------------------------------------------- helpers
def _write(out, artifacts, name, body) -> dict:
    """One register, with every path relative and its own hash last."""
    body = r13._relative_paths(dict(body), out)
    body["E1_4_MODEL"] = E1_4_MODEL
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


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


# ------------------------------------------------- §7 what a line means
RASTER_STATIONS = 24
RASTER_MIN_LENGTH_MM = 120.0

WHY_EVERY_INTERVAL_IS_CLASSIFIED = (
    "the line-semantics question is asked of every interval the drawing "
    "offers, not of the ones a chain happened to want. A classifier that "
    "runs only where a boundary is being built is a classifier that can "
    "be asked twice and answer differently")


def line_semantics_pass(interp, *, linetypes, sheet, mate_layers=(),
                        stair_ids=()) -> dict:
    """§7 — what each stretch of linework means, before it may bound.

    The sheet probe is run on everything it can be run on, and then
    calibrated against the drawing's own linetype table. It carries
    weight only if it agrees with that table where the table is
    unambiguous. Where it does not, every probe result is still recorded
    and none of them is admitted as evidence.
    """
    probes, rows = {}, []
    for oid, ivs in interp["roles"]["intervals"].items():
        for iv in ivs:
            if sheet is not None and getattr(sheet, "ok", False) \
                    and iv.length_mm >= RASTER_MIN_LENGTH_MM:
                probes[iv.interval_id] = _raster_probe(sheet, iv)
    calibration = ls.calibrate_raster_probe(
        [(ls.layer_linetype_evidence(iv.layer, linetypes),
          probes[iv.interval_id]["EVIDENCE"])
         for ivs in interp["roles"]["intervals"].values() for iv in ivs
         if iv.interval_id in probes])
    probe_is_evidence = calibration["RASTER_STROKE_PROBE_IS_EVIDENCE"]

    rows = []
    for oid, ivs in interp["roles"]["intervals"].items():
        for iv in ivs:
            ev = [ls.layer_linetype_evidence(iv.layer, linetypes)]
            if iv.role == ir.STAIR_GEOMETRY or oid in stair_ids:
                ev.append(ls.RUNS_WITH_A_STAIR)
            if iv.role in (ir.DIMENSION_LINE, ir.DIMENSION_WITNESS):
                ev.append(ls.LAYER_SAYS_DIMENSION)
            if iv.role in (ir.ANNOTATION, ir.LEVEL_OR_GRID_ANNOTATION):
                ev.append(ls.LAYER_SAYS_ANNOTATION)
            if (iv.provenance or {}).get("band_offset_mm"):
                ev.append(ls.PAIRED_AT_A_WALL_THICKNESS)
            probe = probes.get(iv.interval_id)
            if probe is not None:
                probe = dict(probe, USED_AS_EVIDENCE=bool(
                    probe["EVIDENCE"] and probe_is_evidence))
                if probe["USED_AS_EVIDENCE"]:
                    ev.append(probe["EVIDENCE"])
            got = ls.classify(sorted(set(ev)))
            rows.append({
                "INTERVAL_ID": iv.interval_id,
                "PARENT_OBJECT_ID": iv.parent_object_id,
                "LAYER": iv.layer,
                "SEMANTIC_ENTITY_ROLE": iv.role,
                "length_mm": round(iv.length_mm, 3),
                "LAYER_LINETYPE": (linetypes.get(str(iv.layer)) or {}).get(
                    "LINETYPE"),
                "WHAT_THE_SHEET_SHOWS": probe,
                **got,
            })
    counts = {}
    for r in rows:
        counts[r["LINE_SEMANTICS_STATUS"]] = counts.get(
            r["LINE_SEMANTICS_STATUS"], 0) + 1
    return {
        "STATUSES": list(ls.STATUSES),
        "MAY_BE_ASKED_TO_BOUND": list(ls.MAY_BE_ASKED_TO_BOUND),
        "why_every_interval_is_classified": WHY_EVERY_INTERVAL_IS_CLASSIFIED,
        "LAYER_LINETYPES_AS_THE_DRAWING_RECORDS_THEM": linetypes,
        "SHEET_PROBE_CALIBRATION": calibration,
        "a_probe_that_contradicts_the_table_is_not_evidence":
            ls.A_PROBE_THAT_CONTRADICTS_THE_TABLE_IS_NOT_EVIDENCE,
        "ROWS": rows,
        "counts_by_status": counts,
        "intervals_classified": len(rows),
        "intervals_that_may_be_asked_to_bound": sum(
            1 for r in rows if r["MAY_BE_ASKED_TO_BOUND"]),
        "frozen_parameters": ls.frozen_parameters(),
    }


def _raster_probe(sheet, iv) -> dict:
    """What the issued sheet prints along one interval."""
    a, b = _pt(iv.start_mm), _pt(iv.end_mm)
    samples = []
    for k in range(1, RASTER_STATIONS + 1):
        t = k / (RASTER_STATIONS + 1)
        samples.append(sheet._dark(a[0] + (b[0] - a[0]) * t,
                                   a[1] + (b[1] - a[1]) * t))
    return ls.raster_stroke_evidence(samples)


# ------------------------------------------------ §4 role vs capability
def capability_pass(interp) -> dict:
    """§4 — what each semantic role may be asked, answered for every role."""
    bcap.assert_every_role_is_answered()
    seen = {}
    for ivs in interp["roles"]["intervals"].values():
        for iv in ivs:
            seen.setdefault(iv.role, {"intervals": 0, "length_mm": 0.0})
            seen[iv.role]["intervals"] += 1
            seen[iv.role]["length_mm"] += iv.length_mm
    rows = []
    for role in ir.ROLES:
        row = bcap.record(role)
        row["intervals_with_this_role"] = seen.get(role, {}).get(
            "intervals", 0)
        row["length_mm"] = round(seen.get(role, {}).get("length_mm", 0.0), 3)
        row["BOUNDARY_ROLE_WHEN_STRAIGHT"] = bcap.boundary_role_for(
            role, kind=cg.LINE)["BOUNDARY_ROLE"]
        row["BOUNDARY_ROLE_WHEN_CURVED"] = bcap.boundary_role_for(
            role, kind=cg.ARC)["BOUNDARY_ROLE"]
        row["THE_SHAPE_DID_NOT_DECIDE_THE_ROLE"] = (
            row["BOUNDARY_ROLE_WHEN_STRAIGHT"]
            == row["BOUNDARY_ROLE_WHEN_CURVED"])
        rows.append(row)
    e1_2_only = bcap.roles_admitted_by_e1_2_but_not_by_e1_4()
    return {
        "CAPABILITIES": list(bcap.CAPABILITIES),
        "these_are_dimensions_not_answers": bcap.THESE_ARE_DIMENSIONS_NOT_ANSWERS,
        "shape_is_not_a_role": bcap.SHAPE_IS_NOT_A_ROLE,
        "ROWS": rows,
        "ROLES_THAT_MAY_BOUND_A_CLEAR_FLOOR_REGION": list(
            bcap.roles_that_may_bound_a_clear_floor_region()),
        "ROLES_E1_2_ADMITTED_THAT_E1_4_DOES_NOT": list(e1_2_only),
        "why_e1_2_may_bound_material_is_not_used":
            bcap.WHY_E1_2_MAY_BOUND_MATERIAL_IS_NOT_USED,
        "length_e1_2_would_have_admitted_that_e1_4_does_not_mm": round(sum(
            r["length_mm"] for r in rows
            if r["SEMANTIC_ENTITY_ROLE"] in e1_2_only), 3),
        "roles_with_no_capability_row": list(
            bcap.roles_missing_a_capability_row()),
        "frozen_parameters": bcap.frozen_parameters(),
    }


# ------------------------------------------------------- §6 the columns
def column_pass(interp, gf, *, material_segments) -> dict:
    """§6 — every candidate's footprint derived here and cross-checked."""
    base = r13.column_ownership_pass(interp, gf,
                                     material_segments=material_segments)
    by_id = {p.object_id: p for p in gf["primitives"]}
    loops = {lp.get("LOOP_ID"): lp
             for lp in interp["roles"]["columns"].get("loops", ())}
    rows, withdrawn = [], []
    for row in base["rows"]:
        lp = loops.get(row["COLUMN_ID"]) or {}
        members = []
        for oid in row["member_object_ids"]:
            p = by_id.get(oid)
            if p is None:
                continue
            x1, y1 = getattr(p, "x1", None), getattr(p, "y1", None)
            x2, y2 = getattr(p, "x2", None), getattr(p, "y2", None)
            if None in (x1, y1, x2, y2):
                continue
            members.append({"object_id": oid, "a": (float(x1), float(y1)),
                            "b": (float(x2), float(y2))})
        derived = cv.derive_from_members(
            members, expect_centre_mm=tuple(lp["centre_mm"])
            if lp.get("centre_mm") else None,
            max_side_mm=float(ir.COLUMN_MAX_SIDE_MM))
        assessed = cv.assess({
            "loop": derived.get("LOOP_RING"),
            "reported_size_mm": row.get("size_mm"),
            "on_structural_layer": ir.EV_COL_LAYER_IS_STRUCTURAL
            in (row.get("evidence") or ()),
            "repeats_as_a_family": ir.EV_COL_FAMILY
            in (row.get("evidence") or ()),
            "touches_a_wall": ir.EV_COL_WALL_CONNECTIVITY
            in (row.get("evidence") or ()),
            "has_a_block_reference": ir.EV_COL_BLOCK_LINEAGE
            in (row.get("evidence") or ()),
            "sides_are_parts_of_longer_lines": derived.get(
                "SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES"),
        })
        was = row["COLUMN_EXISTENCE_STATUS"]
        now = assessed["COLUMN_EXISTENCE_STATUS"]
        if was == co.STRUCTURAL_COLUMN_CONFIRMED \
                and now != cv.STRUCTURAL_COLUMN_CONFIRMED:
            withdrawn.append(row["COLUMN_ID"])
        merged = dict(row)
        merged.update({
            # E1.3 recorded the bounding box of the whole member ENTITIES
            # under a name that says footprint. Both boxes are here, each
            # under the name of what it actually is.
            "MEMBER_ENTITY_EXTENTS_BOX_MM": derived.get(
                "MEMBER_ENTITY_EXTENTS_BOX_MM"),
            "FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM": derived.get(
                "FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM"),
            "WHAT_E1_3_CALLED_THE_FOOTPRINT_BOX": row.get("footprint_box_mm"),
            "LOOP_RING_ESTABLISHED": derived.get("LOOP_RING_ESTABLISHED"),
            "MEMBERS_REACHING_BEYOND_THE_FOOTPRINT": derived.get(
                "MEMBERS_REACHING_BEYOND_THE_FOOTPRINT"),
            "SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES": derived.get(
                "SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES"),
            "DERIVED_GEOMETRY_SELF_CONSISTENT": assessed[
                "DERIVED_GEOMETRY_SELF_CONSISTENT"],
            "derived_bbox_width_mm": assessed.get("derived_bbox_width_mm"),
            "derived_bbox_height_mm": assessed.get("derived_bbox_height_mm"),
            "derived_perimeter_mm": assessed.get("derived_perimeter_mm"),
            "aspect_ratio": assessed.get("aspect_ratio"),
            "footprint_is_compact": assessed.get("footprint_is_compact"),
            "worst_disagreement_mm": assessed.get("worst_disagreement_mm"),
            "E1_3_COLUMN_EXISTENCE_STATUS": was,
            "COLUMN_EXISTENCE_STATUS": now,
            "why_existence": assessed["why"],
            "self_consistency_why": assessed.get("self_consistency_why"),
        })
        # A candidate no longer established as a column does not own a
        # room's clear face, and it does not deform one either.
        if now != cv.STRUCTURAL_COLUMN_CONFIRMED:
            own = co.clear_face_ownership(
                existence_status=co.COLUMN_CANDIDATE_UNRESOLVED,
                exposure_status=row["EXPOSED_TO_ROOM_STATUS"],
                architectural_face_present=bool(
                    row.get("architectural_face_continues_across")
                    or row.get(
                        "an_architectural_face_terminates_at_the_footprint")))
            merged["CLEAR_FACE_OWNERSHIP_STATUS"] = own[
                "CLEAR_FACE_OWNERSHIP_STATUS"]
            merged["may_deform_the_clear_internal_boundary"] = own[
                "may_deform_the_clear_internal_boundary"]
            merged["why_ownership"] = own["why"]
        rows.append(merged)

    # WHAT IS HELD BACK FROM THE WALK is decided by OWNERSHIP, and
    # ownership only.
    #
    # It was tried the other way round here: hold back only the outlines
    # of columns that are ESTABLISHED, on the reasoning that geometry
    # stands behind a finish face only if it is the structure that face
    # covers. That is wrong, and measuring it showed how wrong. Whether
    # a room's clear face follows a loop's outline does not depend on
    # what the loop IS. Where an architectural face is present and the
    # loop's exposure is not established, the room's clear face is the
    # architectural face - whether the loop is a column, a duct, a
    # planter or something nobody has named. Offering the outline to the
    # walk because its column claim was withheld puts structural linework
    # into rooms on the strength of a claim that failed, and it cost a
    # region its boundary.
    #
    # co.clear_face_ownership answers exactly this, and it can only
    # return COLUMN_FACE_OWNS for an established, exposed column. So the
    # three statuses stay three statuses: existence can let a column face
    # own a boundary, and it can never force an outline into a room.
    hidden, exposed = set(), set()
    for r in rows:
        (exposed if r["may_deform_the_clear_internal_boundary"] else
         hidden).update(r["member_object_ids"])
    return {
        "rows": rows,
        "object_ids_that_do_not_own_the_room_face": sorted(hidden),
        "object_ids_that_own_the_room_face": sorted(exposed),
        "architectural_faces_tested_against": base[
            "architectural_faces_tested_against"],
        "columns_e1_3_confirmed_that_e1_4_does_not": sorted(withdrawn),
        "what_is_held_back_is_decided_by_ownership_alone": (
            "a loop's outline is kept out of a room's boundary when the "
            "room's clear face is established as the architectural face "
            "at that location, or when ownership there is not settled. "
            "That question does not ask what the loop is. An outline is "
            "never offered to a walk because its column claim was "
            "withheld"),
        "nothing_is_deleted": cv.NOTHING_IS_DELETED,
        "layer_evidence_is_evidence_not_truth":
            cv.LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
        "frozen_parameters": cv.frozen_parameters(),
    }


# --------------------------------------------- §10, §11 the openings
DOOR_REACH_MM = 1200.0

WHY_BOTH_SEARCHES_RUN = (
    "the gap search starts from a hole in the fabric and asks whether a "
    "door stands in it. The door search starts from the door and asks "
    "which wall it is in. Neither finds everything: a doorway whose jambs "
    "do not reach the pairing as wall ends is invisible to the first, and "
    "an opening with no door drawn is invisible to the second. Both run, "
    "and what each found is reconciled in the open")


def opening_pass(gaps, door_segments, material_segments) -> dict:
    """§10, §11 — the door-first search, and the two searches reconciled."""
    doors, wall_rows = [], []
    for n, s in enumerate(door_segments, start=1):
        a, b = r13._seg_pts(s)
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        kind = getattr(s, "kind", "")
        ev = [od.SWING_ARC] if kind in ("ARC", "CIRCLE") else [od.DOOR_LEAF]
        doors.append({
            "door_id": f"D-{n:03d}",
            "object_id": getattr(s, "object_id", ""),
            "at_mm": _mid(a, b),
            "evidence": ev,
            "ENTITY_KIND": kind,
            "length_mm": round(L, 3),
        })
    # The host walls, each with the interruptions the gap ontology found
    # in it. A wall's own interruption is where an opening's geometry
    # comes from; a door leaf's own extent never is.
    spans_by_wall = {}
    for g in gaps["rows"]:
        for oid in (g.get("host_wall_faces") or ()):
            spans_by_wall.setdefault(oid, []).append(
                {"from_mm": tuple(g["start_mm"]), "to_mm": tuple(g["end_mm"])})
    for s in material_segments:
        a, b = r13._seg_pts(s)
        wall_rows.append({
            "wall_id": getattr(s, "object_id", ""),
            "a": a, "b": b,
            "interrupted_spans": spans_by_wall.get(
                getattr(s, "object_id", ""), []),
        })
    # Every classified gap is an interruption of the fabric, wherever the
    # ontology attributed it; a door is matched against the wall it lies
    # along, so the spans are offered to every wall the search reaches.
    every_span = [{"from_mm": tuple(g["start_mm"]), "to_mm": tuple(g["end_mm"])}
                  for g in gaps["rows"]]
    for w in wall_rows:
        if not w["interrupted_spans"]:
            w["interrupted_spans"] = every_span

    found = od.door_first(doors, wall_rows, reach_mm=DOOR_REACH_MM)
    gap_first = [{"GAP_ID": g["GAP_ID"], "GAP_CLASS": g["GAP_CLASS"],
                  "start_mm": tuple(g["start_mm"]),
                  "end_mm": tuple(g["end_mm"])}
                 for g in gaps["rows"]]
    rec = od.reconcile(gap_first, found)
    return {
        "why_both_searches_run": WHY_BOTH_SEARCHES_RUN,
        "DOOR_ENTITIES": doors,
        "door_entities": len(doors),
        "DOOR_FIRST": found,
        "RECONCILED": rec,
        "HOST_WALL_MATCH_ATTEMPTS": found["HOST_WALL_MATCH_ATTEMPTS"],
        "what_is_kept_includes_what_failed": od.WHAT_IS_KEPT_INCLUDES_WHAT_FAILED,
        "frozen_parameters": od.frozen_parameters(),
    }


# ------------------------------------------------------- §8 label seeds
def label_seed_pass(groups, pieces) -> dict:
    """§8 — a label's own anchors, and whether they agree about a room."""
    def material_between(a, b):
        clear, blocker = bw.sight_line_is_clear(tuple(a), tuple(b), pieces)
        if clear:
            return False, None
        return True, {"object_id": blocker}

    rows = []
    for g in groups:
        anchors = []
        for m in g.members:
            kind = (la.ENGLISH_TOKEN_ANCHOR
                    if m.stamp_class == r12.lg.ENGLISH_ROOM_STAMP else
                    la.ARABIC_TOKEN_ANCHOR
                    if m.stamp_class == r12.lg.ARABIC_ROOM_STAMP else
                    la.OTHER_SOURCE_ANCHOR)
            anchors.append(la.anchor(kind, m.visible_centroid,
                                     source=m.stamp_id, text=m.text))
            anchors.append(la.anchor(la.CAD_TEXT_INSERTION_POINT,
                                     (m.x, m.y), source=m.stamp_id))
        pts = [tuple(m.visible_centroid) for m in g.members]
        if len(pts) > 1:
            anchors.append(la.anchor(
                la.GROUP_CENTROID,
                (sum(p[0] for p in pts) / len(pts),
                 sum(p[1] for p in pts) / len(pts)),
                source=g.group_id))
        got = la.assess(f"E1_4-{g.group_id}", anchors,
                        material_between=material_between)
        got["IDENTITY_AS_DRAWN"] = g.english_token
        got["GROUP_ID"] = g.group_id
        # what E1.3 used, recorded beside it and never used here
        english = [m for m in g.members
                   if m.stamp_class == r12.lg.ENGLISH_ROOM_STAMP]
        e13 = (english[0] if english else g.members[0]).visible_centroid
        got["WHAT_E1_3_SEEDED_FROM_MM"] = [round(e13[0], 3), round(e13[1], 3)]
        got["THE_SEED_MOVED"] = (
            got["SEED_MM"] is not None
            and (abs(got["SEED_MM"][0] - e13[0]) > 1.0
                 or abs(got["SEED_MM"][1] - e13[1]) > 1.0))
        rows.append(got)
    counts = {}
    for r in rows:
        counts[r["LABEL_SEED_STATUS"]] = counts.get(
            r["LABEL_SEED_STATUS"], 0) + 1
    return {
        "ANCHOR_KINDS": list(la.ANCHOR_KINDS),
        "SEED_STATUSES": list(la.SEED_STATUSES),
        "ROWS": rows,
        "counts_by_status": counts,
        "seeds_that_moved_from_what_e1_3_used": sum(
            1 for r in rows if r["THE_SEED_MOVED"]),
        "anchors_are_not_interchangeable": la.ANCHORS_ARE_NOT_INTERCHANGEABLE,
        "no_area_and_no_expectation": la.NO_AREA_AND_NO_EXPECTATION,
        "frozen_parameters": la.frozen_parameters(),
    }


# --------------------------------------------- §4, §7 what may bound
NOT_ADMITTED_BY_ROLE = "THE_SEMANTIC_ROLE_BOUNDS_NO_CLEAR_FLOOR_REGION"
NOT_ADMITTED_BY_LINE_SEMANTICS = "THE_LINE_IS_NOT_ESTABLISHED_IN_THE_CUT_PLANE"
NOT_ADMITTED_AS_HIDDEN_STRUCTURE = "IT_DOES_NOT_OWN_THE_ROOMS_CLEAR_FACE"

TWO_GATES_AND_BOTH_MUST_PASS = (
    "a stretch is offered to the walk when its semantic role can bound a "
    "clear floor region AND its linework is established in the cut plane. "
    "The two questions are independent and neither answers the other: the "
    "edge of the water is continuous linework that bounds no room, and a "
    "wall drawn above the cut plane is a wall that is not there")


def admission_pass(interp, gf, *, semantics, hidden_ids) -> dict:
    """Which intervals may be offered to the walk, and why the rest may not."""
    by_id = {p.object_id: p for p in gf["primitives"]}
    sem = {r["INTERVAL_ID"]: r for r in semantics["ROWS"]}
    prims = r12.interval_prims(interp["roles"]["intervals"], by_id,
                               only_material=False)
    kept, refused = [], []
    for m in prims:
        iv = m.interval
        if iv.length_mm <= 0:
            continue
        role_ok = bcap.may_bound_a_clear_floor_region(iv.role)
        line = sem.get(iv.interval_id, {})
        line_ok = bool(line.get("MAY_BE_ASKED_TO_BOUND"))
        oid = (iv.provenance or {}).get("object_id") or iv.parent_object_id
        structural_ok = oid not in hidden_ids
        if role_ok and line_ok and structural_ok:
            kept.append(m)
            continue
        why = []
        if not role_ok:
            why.append(NOT_ADMITTED_BY_ROLE)
        if not line_ok:
            why.append(NOT_ADMITTED_BY_LINE_SEMANTICS)
        if not structural_ok:
            why.append(NOT_ADMITTED_AS_HIDDEN_STRUCTURE)
        refused.append({
            "INTERVAL_ID": iv.interval_id,
            "PARENT_OBJECT_ID": iv.parent_object_id,
            "LAYER": iv.layer,
            "SEMANTIC_ENTITY_ROLE": iv.role,
            "LINE_SEMANTICS_STATUS": line.get("LINE_SEMANTICS_STATUS"),
            "length_mm": round(iv.length_mm, 3),
            "NOT_ADMITTED_BECAUSE": why,
            "E1_2_WOULD_HAVE_ADMITTED_IT": bool(iv.may_bound_material),
        })
    by_reason = {}
    for r in refused:
        for w in r["NOT_ADMITTED_BECAUSE"]:
            d = by_reason.setdefault(w, {"intervals": 0, "length_mm": 0.0})
            d["intervals"] += 1
            d["length_mm"] = round(d["length_mm"] + r["length_mm"], 3)
    return {
        "two_gates_and_both_must_pass": TWO_GATES_AND_BOTH_MUST_PASS,
        "ADMITTED": len(kept),
        "admitted_length_mm": round(sum(m.interval.length_mm for m in kept), 3),
        "NOT_ADMITTED": len(refused),
        "not_admitted_by_reason": by_reason,
        "REFUSED": refused,
        "refused_that_e1_2_would_have_admitted": sum(
            1 for r in refused if r["E1_2_WOULD_HAVE_ADMITTED_IT"]),
        "refused_length_that_e1_2_would_have_admitted_mm": round(sum(
            r["length_mm"] for r in refused
            if r["E1_2_WOULD_HAVE_ADMITTED_IT"]), 3),
        "prims": kept,
    }


# ------------------------------------------------- §12 every fragment
WHY_EVERY_VISIBLE_START_IS_WALKED = (
    "one walk running out is not evidence that nothing else is drawn "
    "around this region. Where the boundary does not close, the walk is "
    "taken from every face the point can see, both ways from each, and "
    "every distinct run that comes back is a fragment the drawing "
    "establishes. None of them is joined to another, and nothing is "
    "drawn between them")


def _termination(steps, *, at_end) -> str:
    """What stopped this run at one of its ends, in the walk's own words."""
    if not steps:
        return bf.NO_VALID_CONTINUATION
    st = steps[-1] if at_end else steps[0]
    kind = st["STEP"]
    if kind == bw.STEP_STOPS:
        if st.get("an_end_faces_this_one_across_a_gap"):
            return bf.TERMINATES_AT_AN_UNCLASSIFIED_GAP
        if st.get("the_mate_face_carries_on_here"):
            return bf.TERMINATES_WHERE_THE_ROLE_CHANGES
        return bf.TERMINATES_AT_A_WALL_END
    if kind == bw.STEP_ACROSS_A_GAP:
        return bf.TERMINATES_AT_A_CLASSIFIED_PORTAL
    return bf.NO_VALID_CONTINUATION


def fragment_pass(candidate_id, seed, pieces, *, gaps_at, mates, facing,
                  hypotheses=()) -> dict:
    """§12 — every independently established fragment of an open region."""
    starts = bw.visible_pieces(seed, pieces)
    seen, frags = set(), []
    for i in starts:
        end = bw.leave_with_the_space_on_the_left(pieces, i, seed)
        run = bw.walk_both_ways(pieces, start=(i, end), gaps_at=gaps_at,
                                mates=mates, facing=facing)
        walked = [s["piece"] for s in run["steps"]
                  if s["STEP"] == bw.STEP_MATERIAL_FACE]
        key = tuple(sorted(set(walked)))
        if not key or key in seen:
            continue
        seen.add(key)
        ring, chain_mm, _broken = bw.ring_of(run, pieces)
        if len(ring) < 2:
            continue
        roles = sorted({pieces[j].get("boundary_role") for j in key})
        caps = set()
        for j in key:
            caps |= set(bcap.capabilities_of(
                pieces[j].get("semantic_role") or ir.MATERIAL_WALL_FACE))
        frags.append(bf.fragment(
            f"{candidate_id}-FRAG-{len(frags) + 1:02d}", candidate_id,
            source_hypothesis=None,
            cad_entity_ids=sorted({pieces[j].get("object_id") for j in key}),
            interval_ids=sorted({pieces[j].get("key") for j in key
                                 if pieces[j].get("key")}),
            ordered_geometry=ring,
            semantic_role=roles[0] if len(roles) == 1 else "SEVERAL",
            boundary_capabilities=caps,
            start_termination=_termination(run["steps"], at_end=False),
            end_termination=_termination(run["steps"], at_end=True),
            confidence="ESTABLISHED_FROM_CAD",
            provenance="WALKED_FROM_A_FACE_THIS_POINT_CAN_SEE"))
        frags[-1]["CHAIN_LENGTH_MM"] = round(chain_mm, 3)
        frags[-1]["pieces_walked"] = len(key)
        frags[-1]["DIRECTIONS_WALKED"] = run.get("DIRECTIONS_WALKED")
    unmet = [bf.unmet(h, searched="every face this point can see, walked "
                                  "both ways from each",
                      why="no run the walk established answers this "
                          "observation")
             for h in hypotheses]
    return {
        "why_every_visible_start_is_walked": WHY_EVERY_VISIBLE_START_IS_WALKED,
        "FRAGMENTS": frags + unmet,
        "faces_the_point_can_see": len(starts),
        "never_extended_across_an_unsupported_opening":
            bf.A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING,
    }


# -------------------------------------------------------- the candidates
def build_candidates(gf, interp, *, ontology, gaps, seeds, prims,
                     owner) -> dict:
    """Every Ground Floor candidate, walked against one arrangement."""
    exposed = set(owner["object_ids_that_own_the_room_face"])
    interval_by_id = {iv.interval_id: iv
                      for rows_ in interp["roles"]["intervals"].values()
                      for iv in rows_}
    segs = []
    for m in prims:
        role = bcap.boundary_role_for(m.interval.role,
                                      kind=m.interval.kind)["BOUNDARY_ROLE"]
        segs.append(cg._as_segment(m, role=role))
    look = []
    for sg in segs:
        try:
            pts = sg.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) >= 2:
            look.append({"points": pts, "key": sg.object_id,
                         "object_id": sg.object_id,
                         "boundary_role": sg.role, "layer": sg.layer})
    pieces = bw.pieces_from(look, tol_mm=cg.DENSIFY_TOL_MM)
    families = [{"nominal_mm": f["thickness_mm"]}
                for f in gaps["wall_thickness_families_inferred"]]
    mates, mate_pairs = bw.mate_map(pieces, families=families)
    nodes = bw.node_graph(pieces)
    facing = bw.facing_ends(pieces, nodes)
    gaps_at = {}
    for grow in gaps["rows"]:
        for q in (grow["start_mm"], grow["end_mm"]):
            gaps_at.setdefault(bw._nkey(tuple(q)), grow)

    keep = {r.group_id for r in ontology["rows"] if r.in_denominator}
    groups = [g for g in interp["labels"]["groups"]
              if g.group_id in keep and g.english_token]
    seed_by_group = {r["GROUP_ID"]: r for r in seeds["ROWS"]}

    rows = []
    for n, g in enumerate(groups, start=1):
        cid = f"E1_4-{g.group_id}"
        sr = seed_by_group.get(g.group_id, {})
        seed = sr.get("SEED_MM")
        row = {"n": n, "group": g, "candidate_id": cid,
               "LABEL_SEED_STATUS": sr.get("LABEL_SEED_STATUS"),
               "SEED_ANCHOR_KIND": sr.get("SEED_ANCHOR_KIND"),
               "seed": tuple(seed) if seed else None,
               "chain": None, "walk": None, "ring_qa": None,
               "traversal": None, "fragments": None,
               "BOUNDARY_BASIS": None}
        if seed is None:
            row["WITHHELD"] = "THE_LABEL_DOES_NOT_SAY_WHICH_SPACE_IT_NAMES"
            row["why"] = sr.get("why")
            rows.append(row)
            continue
        seed = tuple(seed)
        res = bw.boundary_at(seed, pieces, gaps_at=gaps_at, mates=mates,
                             facing=facing)
        chain = r13.chain_from_walk(res, pieces, gap_rows=gaps["rows"],
                                    exposed_ids=exposed,
                                    interval_by_id=interval_by_id)
        ring, chain_mm, broken = bw.ring_of(res, pieces)
        spans = [{"GAP_ID": st.get("gap"), "start_mm": tuple(st["start_mm"]),
                  "end_mm": tuple(st["end_mm"])}
                 for st in res["steps"]
                 if st["STEP"] == bw.STEP_ACROSS_A_GAP]
        row["ring_qa"] = rq.assess(
            ring=ring, chain_length_mm=chain_mm, seed=seed,
            chain_breaks=[broken] if broken else None, portal_spans=spans)
        row["ring_qa"]["CANDIDATE_ID"] = cid
        row["ring_qa"].update(rq.establishes_geometry(row["ring_qa"]))
        row["traversal"] = tg.traverse(res["steps"], pieces, mates=mates)
        tg.assert_no_stretch_is_counted_twice(row["traversal"])
        row["chain"] = chain
        row["BOUNDARY_BASIS"] = res["BOUNDARY_BASIS"]
        row["walk"] = {k: v for k, v in res.items()
                       if k not in ("steps", "FACE_SELECTION")}
        row["face_selection"] = res.get("FACE_SELECTION")
        row["PHYSICAL_REGION_KEY"] = r13._face_key(chain)
        if res["BOUNDARY_BASIS"] != bw.ENCLOSED:
            row["fragments"] = fragment_pass(cid, seed, pieces,
                                             gaps_at=gaps_at, mates=mates,
                                             facing=facing)
        rows.append(row)

    shared = {}
    for r in rows:
        if r.get("PHYSICAL_REGION_KEY"):
            shared.setdefault(r["PHYSICAL_REGION_KEY"], []).append(r)
    for key, grp in shared.items():
        for r in grp:
            r["candidates_sharing_this_physical_region"] = sorted(
                x["candidate_id"] for x in grp)
    return {
        "rows": rows, "pieces": pieces, "segments": segs, "mates": mates,
        "gaps_at": gaps_at, "facing": facing,
        "wall_bodies_paired": len(mate_pairs),
        "wall_thickness_families_used": families,
        "pieces_of_drawn_material": len(pieces),
        "dangling_ends_with_something_facing_them": len(facing),
        "physical_regions": {k: sorted(x["candidate_id"] for x in v)
                             for k, v in shared.items()},
    }


# ---------------------------------------------------------------- core
def _core(a) -> dict:
    """Everything the phases need, rebuilt from the same inputs each time."""
    prep = r12.prepare(a.decode)
    gf = r12.ground_floor(prep)
    interp = r12.interpret(gf, prep)
    by_id = {p.object_id: p for p in gf["primitives"]}

    linetypes = ls.linetype_table(
        json.loads(Path(a.decode).read_text(encoding="utf-8"))["OBJECTS"])
    _reg, sheet = r13._registered_sheet(a, gf)
    semantics = line_semantics_pass(interp, linetypes=linetypes, sheet=sheet)
    capability = capability_pass(interp)

    # The column pass needs material segments to test an architectural
    # face against, and it must not be given the column's own geometry.
    e12_material = r12.interval_prims(interp["roles"]["intervals"], by_id)
    mat_segs_all = [cg._as_segment(m, role=bcap.boundary_role_for(
        m.interval.role, kind=m.interval.kind)["BOUNDARY_ROLE"])
        for m in e12_material]
    owner = column_pass(interp, gf, material_segments=mat_segs_all)

    admitted = admission_pass(interp, gf, semantics=semantics,
                              hidden_ids=set(owner[
                                  "object_ids_that_do_not_own_the_room_face"]))
    prims = admitted.pop("prims")
    mat_segs = [cg._as_segment(m, role=bcap.boundary_role_for(
        m.interval.role, kind=m.interval.kind)["BOUNDARY_ROLE"])
        for m in prims]

    band_offsets = []
    for rows_ in interp["roles"]["intervals"].values():
        for iv in rows_:
            b = (iv.provenance or {}).get("band_offset_mm")
            if b:
                band_offsets.append(float(b))
    struct_ids = set(owner["object_ids_that_do_not_own_the_room_face"]) | \
        set(owner["object_ids_that_own_the_room_face"])
    xs = [v for p_ in prims
          for v in (p_.interval.provenance or {}).get("extent_mm", ()) or ()]
    span = max(xs) - min(xs) if xs else 0.0
    reach = max(float(cg.MAX_DOUBLE_LEAF_MM), span)
    raw_closure = cg.close_openings(prims, wall_layers=(), door_layers={"D"},
                                    max_barrier_mm=reach)
    all_prims = r12.interval_prims(interp["roles"]["intervals"], by_id,
                                   only_material=False)
    door_segs = [cg._as_segment(m) for m in all_prims
                 if m.interval.role == ir.DOOR]
    gaps = gp.reclassify(raw_closure, material_segments=mat_segs,
                         structural_ids=struct_ids,
                         band_offsets_mm=band_offsets,
                         door_segments=door_segs)
    openings = opening_pass(gaps, door_segs, mat_segs)

    cand_json = json.loads((Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json")
                           .read_text(encoding="utf-8"))["candidates"]
    zone_tokens = {r12._english_token(c.get("label_as_drawn", ""))
                   for c in cand_json
                   if str(c.get("candidate_id", "")).startswith("FZ")}
    ontology = lo.classify(interp["labels"]["groups"], region=gf["region"],
                           a18_zone_tokens=sorted(t for t in zone_tokens if t),
                           material_segments=mat_segs)

    # The seeds are validated against the SAME arrangement the walk uses,
    # so "a wall stands between these two anchors" means the wall the walk
    # would meet and not some other reading of the drawing.
    look = []
    for sg in mat_segs:
        try:
            pts = sg.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) >= 2:
            look.append({"points": pts, "key": sg.object_id,
                         "object_id": sg.object_id,
                         "boundary_role": sg.role, "layer": sg.layer})
    seed_pieces = bw.pieces_from(look, tol_mm=cg.DENSIFY_TOL_MM)
    keep = {r.group_id for r in ontology["rows"] if r.in_denominator}
    groups = [g for g in interp["labels"]["groups"]
              if g.group_id in keep and g.english_token]
    seeds = label_seed_pass(groups, seed_pieces)

    built = build_candidates(gf, interp, ontology=ontology, gaps=gaps,
                             seeds=seeds, prims=prims, owner=owner)
    return {"prep": prep, "gf": gf, "interp": interp, "owner": owner,
            "gaps": gaps, "ontology": ontology, "built": built,
            "rows": built["rows"], "cand_json": cand_json,
            "semantics": semantics, "capability": capability,
            "admitted": admitted, "openings": openings, "seeds": seeds,
            "mat_segs": mat_segs, "door_segments": door_segs,
            "linetypes": linetypes,
            "iv_by_id": {iv.interval_id: iv
                         for rows_ in interp["roles"]["intervals"].values()
                         for iv in rows_}}


# ------------------------------------------------------------ the phases
def phase_geometry(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {}

    st = _core(a)
    gf, interp, rows = st["gf"], st["interp"], st["rows"]
    src = r12._source(st["prep"], gf, a)
    from engine import atomic_interval as ai
    from engine import gap_ontology as go

    # §3 - generated from what ran, and the freeze fails without it
    man = ep.manifest(".")
    bound = ep.assert_every_executed_local_module_is_hashed(man, ".")
    _write(out, artifacts, "E1_4_EXECUTION_CODE_MANIFEST.json", {
        "source": src, **man, **bound})

    _write(out, artifacts, "E1_4_ATOMIC_INTERVAL_ROLE_REGISTER.json", {
        "source": src,
        "carried_forward_unchanged": (
            "engine.atomic_interval and engine.interval_role are the frozen "
            "E1.2 modules, imported and not modified. What changed in E1.4 "
            "is which of these intervals may be asked to bound a room, and "
            "that question is answered in the capability and line-semantics "
            "registers rather than here"),
        "CUT_REASONS": list(ai.CUT_REASONS),
        "ROLES": list(ir.ROLES),
        "entities": interp["roles"]["entity_count"],
        "intervals": interp["roles"]["interval_count"],
        "counts_by_role": interp["roles"]["counts_by_role"],
        "INTERVALS_E1_2_WOULD_ADMIT": interp["roles"][
            "intervals_that_may_bound_material"],
        "ADMISSION": st["admitted"],
        "frozen_parameters": {"atomic_interval": ai.frozen_parameters(),
                              "interval_role": ir.frozen_parameters()},
        "INTERVALS": [iv.record() for iv in interp["roles"]["flat"]],
    })

    _write(out, artifacts, "E1_4_BOUNDARY_CAPABILITY_REGISTER.json",
           {"source": src, **st["capability"]})
    _write(out, artifacts, "E1_4_LINE_SEMANTICS_REGISTER.json",
           {"source": src, **st["semantics"]})

    owner = st["owner"]
    _write(out, artifacts, "E1_4_COLUMN_EXISTENCE_REGISTER.json", {
        "source": src,
        "a_touched_wall_is_not_a_structure": co.A_TOUCHED_WALL_IS_NOT_A_STRUCTURE,
        "EXISTENCE_STATUSES": list(cv.EXISTENCE_STATUSES),
        "DERIVED_GEOMETRY_SELF_CONSISTENT_IS_REQUIRED": (
            "no structural classification survives an internal geometry "
            "inconsistency, and the footprint it is checked against is "
            "derived here from the candidate's own ring"),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["COLUMN_EXISTENCE_STATUS"] == s)
                   for s in cv.EXISTENCE_STATUSES},
        "columns_e1_3_confirmed_that_e1_4_does_not":
            owner["columns_e1_3_confirmed_that_e1_4_does_not"],
        "nothing_is_deleted": owner["nothing_is_deleted"],
        "layer_evidence_is_evidence_not_truth":
            owner["layer_evidence_is_evidence_not_truth"],
        "frozen_parameters": owner["frozen_parameters"],
        "COLUMNS": owner["rows"],
    })
    _write(out, artifacts, "E1_4_COLUMN_EXPOSURE_REGISTER.json", {
        "source": src,
        "EXPOSURE_STATUSES": list(co.EXPOSURE_STATUSES),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["EXPOSED_TO_ROOM_STATUS"] == s)
                   for s in co.EXPOSURE_STATUSES},
        "COLUMNS": [{k: r[k] for k in
                     ("COLUMN_ID", "EXPOSED_TO_ROOM_STATUS",
                      "exposure_evidence", "architectural_face_continues_across",
                      "an_architectural_face_terminates_at_the_footprint",
                      "why_exposure")} for r in owner["rows"]],
    })
    _write(out, artifacts, "E1_4_CLEAR_FACE_OWNERSHIP_REGISTER.json", {
        "source": src,
        "OWNERSHIP_STATUSES": list(co.OWNERSHIP_STATUSES),
        "counts": {s: sum(1 for r in owner["rows"]
                          if r["CLEAR_FACE_OWNERSHIP_STATUS"] == s)
                   for s in co.OWNERSHIP_STATUSES},
        "object_ids_that_do_not_own_the_room_face":
            owner["object_ids_that_do_not_own_the_room_face"],
        "object_ids_that_own_the_room_face":
            owner["object_ids_that_own_the_room_face"],
        "COLUMNS": [{k: r[k] for k in
                     ("COLUMN_ID", "CLEAR_FACE_OWNERSHIP_STATUS",
                      "structural_object_relation",
                      "may_deform_the_clear_internal_boundary",
                      "why_ownership")} for r in owner["rows"]],
    })

    _write(out, artifacts, "E1_4_LABEL_ANCHOR_REGISTER.json",
           {"source": src, **st["seeds"]})

    _write(out, artifacts, "E1_4_GAP_ONTOLOGY_REGISTER.json", {
        "source": src,
        "GAP_CLASSES": list(go.GAP_CLASSES),
        "counts_by_class": st["gaps"]["counts_by_class"],
        "candidate_gaps": st["gaps"]["candidate_gaps"],
        "closed_as_portal": st["gaps"]["closed_as_portal"],
        "closed_as_material_continuity":
            st["gaps"]["closed_as_material_continuity"],
        "left_open_or_unresolved": st["gaps"]["left_open"],
        "wall_thickness_families_inferred":
            st["gaps"]["wall_thickness_families_inferred"],
        "frozen_parameters": gp.frozen_parameters(),
        "GAPS": st["gaps"]["rows"],
    })
    portals = [g for g in st["gaps"]["rows"] if g["IS_A_PORTAL"]]
    _write(out, artifacts, "E1_4_PORTAL_EVIDENCE_REGISTER.json", {
        "source": src,
        "CONFIRMING_EVIDENCE": list(go.CONFIRMING_EVIDENCE),
        "PROBABLE_EVIDENCE": list(go.PROBABLE_EVIDENCE),
        "portals": len(portals),
        "PORTALS": portals,
    })
    _write(out, artifacts, "E1_4_DOOR_ENTITY_REGISTER.json", {
        "source": src,
        "a_door_must_not_disappear": od.A_DOOR_MUST_NOT_DISAPPEAR,
        "DOOR_EVIDENCE": list(od.DOOR_EVIDENCE),
        "ESTABLISHES_THAT_AN_OPENING_EXISTS": list(
            od.ESTABLISHES_THAT_AN_OPENING_EXISTS),
        "door_entities": st["openings"]["door_entities"],
        "DOORS": st["openings"]["DOOR_ENTITIES"],
        "HOST_WALL_MATCH_ATTEMPTS": st["openings"]["HOST_WALL_MATCH_ATTEMPTS"],
    })
    _write(out, artifacts, "E1_4_OPENING_DISCOVERY_REGISTER.json", {
        "source": src,
        "why_both_searches_run": st["openings"]["why_both_searches_run"],
        "RECONCILIATION_STATUSES": list(od.RECONCILIATION_STATUSES),
        "counts_by_status": st["openings"]["RECONCILED"]["counts_by_status"],
        "door_first_matched": st["openings"]["DOOR_FIRST"]["matched"],
        "door_first_rejected": st["openings"]["DOOR_FIRST"]["rejected"],
        "OPENINGS": st["openings"]["RECONCILED"]["RECONCILED_OPENINGS"],
        "frozen_parameters": st["openings"]["frozen_parameters"],
    })

    ends = []
    for key, facing in st["built"]["facing"].items():
        ends.append({"at_mm": [round(v, 3) for v in key],
                     "ends_facing_this_one": [[round(v, 3) for v in p]
                                              for p in facing[:4]],
                     "why": bw.BOUNDARY_OPEN_AT_AN_UNCLASSIFIED_GAP})
    _write(out, artifacts, "E1_4_WALL_END_REGISTER.json", {
        "source": src,
        "what_this_is": (
            "every end of drawn material with another end facing it across "
            "an unclassified gap. These are the stations where a walk "
            "stops, and they are kept whether or not anything was made of "
            "them"),
        "pieces_of_drawn_material": st["built"]["pieces_of_drawn_material"],
        "wall_bodies_paired": st["built"]["wall_bodies_paired"],
        "wall_thickness_families_used":
            st["built"]["wall_thickness_families_used"],
        "ends_with_something_facing_them": len(ends),
        "ENDS": ends,
    })

    _write(out, artifacts, "E1_4_RING_QA_REGISTER.json", {
        "source": src,
        "these_are_qa_diagnostics_not_target_quantities":
            rq.THESE_ARE_QA_DIAGNOSTICS_NOT_TARGET_QUANTITIES,
        "a_ring_may_not_be_established_by_its_repair":
            rq.A_RING_MAY_NOT_BE_ESTABLISHED_BY_ITS_REPAIR,
        "REQUIRED_FIELDS": list(rq.REQUIRED_FIELDS),
        "CANDIDATES": [r["ring_qa"] for r in rows if r.get("ring_qa")],
        "rings_that_establish_geometry": sum(
            1 for r in rows if (r.get("ring_qa") or {}).get(
                "RING_ESTABLISHES_GEOMETRY")),
    })

    _write(out, artifacts, "E1_4_BOUNDARY_FRAGMENT_REGISTER.json", {
        "source": src,
        "completeness_is_not_closure": bf.COMPLETENESS_IS_NOT_CLOSURE,
        "a_hypothesis_owns_no_coordinate": bf.A_HYPOTHESIS_OWNS_NO_COORDINATE,
        "never_extended_across_an_unsupported_opening":
            bf.A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING,
        "FRAGMENT_STATUSES": list(bf.FRAGMENT_STATUSES),
        "TERMINATIONS": list(bf.TERMINATIONS),
        "CANDIDATES": [
            {"CANDIDATE_ID": r["candidate_id"],
             "IDENTITY_AS_DRAWN": r["group"].english_token,
             "COMPLETE_PHYSICAL_REGION_STATUS": r["BOUNDARY_BASIS"],
             **bf.summarise(r["candidate_id"], r["fragments"]["FRAGMENTS"],
                            complete_region_status=r["BOUNDARY_BASIS"]),
             "faces_the_point_can_see":
                 r["fragments"]["faces_the_point_can_see"],
             "FRAGMENTS": r["fragments"]["FRAGMENTS"]}
            for r in rows if r.get("fragments")],
    })

    _write(out, artifacts, "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json", {
        "source": src,
        "a_chain_is_not_a_polygon": bc.A_CHAIN_IS_NOT_A_POLYGON,
        "a_curve_is_not_its_chord": bc.A_CURVE_IS_NOT_ITS_CHORD,
        "CHAIN_ELEMENTS": list(bc.CHAIN_ELEMENTS),
        "CANDIDATES": [
            {"CANDIDATE_ID": r["candidate_id"],
             "IDENTITY_AS_DRAWN": r["group"].english_token,
             "LABEL_SEED_STATUS": r["LABEL_SEED_STATUS"],
             "SEED_ANCHOR_KIND": r["SEED_ANCHOR_KIND"],
             "SEED_MM": list(r["seed"]) if r.get("seed") else None,
             "BOUNDARY_BASIS": r["BOUNDARY_BASIS"],
             "WITHHELD": r.get("WITHHELD"),
             "PHYSICAL_REGION_KEY": r.get("PHYSICAL_REGION_KEY"),
             "candidates_sharing_this_physical_region": r.get(
                 "candidates_sharing_this_physical_region"),
             "walk": r.get("walk"),
             "CHAIN": r.get("chain")}
            for r in rows],
    })

    _write(out, artifacts, "E1_4_TRAVERSAL_GEOMETRY_REGISTER.json", {
        "source": src,
        "which_register_answers_which_question":
            dict(tg.WHICH_REGISTER_ANSWERS_WHICH_QUESTION),
        "no_quantity_is_calculated_in_e1_4": tg.NO_QUANTITY_IS_CALCULATED_IN_E1_4,
        "a_traversal_may_never_be_read_as_a_length":
            tg.A_TRAVERSAL_MAY_NEVER_BE_READ_AS_A_LENGTH,
        "CANDIDATES": [
            {"CANDIDATE_ID": r["candidate_id"], **r["traversal"]}
            for r in rows if r.get("traversal")],
    })

    _write(out, artifacts, "E1_4_INPUT_MANIFEST.json", {
        "source": src,
        **e14.E1_4Run().record(),
        "what_e1_4_repairs": e14.WHAT_E1_4_REPAIRS,
        "what_e1_4_does_not_do": e14.WHAT_E1_4_DOES_NOT_DO,
        "what_success_means": e14.WHAT_SUCCESS_MEANS,
        "LAYER_LINETYPES_AS_THE_DRAWING_RECORDS_THEM": st["linetypes"],
    })

    (out / "_E1_4_ARTIFACTS_GEOMETRY.json").write_text(
        json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
    print(f"E1.4 geometry: {len(rows)} candidates, "
          f"{sum(1 for r in rows if r['BOUNDARY_BASIS'] == bw.ENCLOSED)} "
          f"enclosed, {len(artifacts)} registers")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", required=True, choices=("geometry",))
    ap.add_argument("--decode",
                    default="data/runs/cad_convert/P7757_ARCHITECTURAL.json")
    ap.add_argument("--a18-dir", default="data/runs/7757/blind/A18-GF-001")
    ap.add_argument("--raster",
                    default="data/runs/7757/blind/A18-GF-001/images/"
                            "page-01.jpeg")
    ap.add_argument("--prior-e1-3", default="data/runs/7757/e1_3")
    ap.add_argument("--rules",
                    default="data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
    ap.add_argument("--sandbox", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return phase_geometry(a)


if __name__ == "__main__":
    raise SystemExit(main())
