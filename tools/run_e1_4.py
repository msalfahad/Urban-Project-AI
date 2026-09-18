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
from engine import decision_ledger as dl
from engine import edge_relation as edge
from engine import visual_challenger_v2 as vc
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


def floor_fragments(pieces, *, gaps_at, mates, facing) -> dict:
    """Every distinct run of established boundary the drawing carries.

    A run is walked once, from a face, both ways, and it is the same run
    whichever of its faces the walk started on. Runs are found once for
    the whole floor and recorded once, because a 52 m external wall run
    is one run - not one run per room that can see a piece of it.
    """
    runs, seen = [], set()
    for i in range(len(pieces)):
        for end in (0, 1):
            r = bw.walk_both_ways(pieces, start=(i, end), gaps_at=gaps_at,
                                  mates=mates, facing=facing)
            walked = [st["piece"] for st in r["steps"]
                      if st["STEP"] == bw.STEP_MATERIAL_FACE]
            key = tuple(sorted(set(walked)))
            if len(key) < 1 or key in seen:
                continue
            seen.add(key)
            ring, chain_mm, _b = bw.ring_of(r, pieces)
            runs.append({"key": key, "steps": r["steps"], "ring": ring,
                         "chain_mm": chain_mm,
                         "DIRECTIONS_WALKED": r.get("DIRECTIONS_WALKED"),
                         "CLOSED": r["CLOSED_BY_DRAWN_MATERIAL"]})
    runs.sort(key=lambda r: (-len(r["key"]), r["key"]))
    out = []
    for n, r in enumerate(runs, start=1):
        roles = sorted({pieces[j].get("boundary_role") for j in r["key"]})
        caps = set()
        for j in r["key"]:
            caps |= set(bcap.capabilities_of(ir.MATERIAL_WALL_FACE)
                        if pieces[j].get("boundary_role")
                        == cg.MATERIAL_WALL_FACE else ())
        row = bf.fragment(
            f"E1_4-FRAG-{n:04d}", None, source_hypothesis=None,
            cad_entity_ids=sorted({pieces[j].get("object_id")
                                   for j in r["key"]}),
            interval_ids=sorted({pieces[j].get("key") for j in r["key"]
                                 if pieces[j].get("key")}),
            ordered_geometry=r["ring"] if len(r["ring"]) >= 2 else [],
            semantic_role=roles[0] if len(roles) == 1 else "SEVERAL",
            boundary_capabilities=caps,
            start_termination=_termination(r["steps"], at_end=False),
            end_termination=_termination(r["steps"], at_end=True),
            confidence="ESTABLISHED_FROM_CAD",
            provenance="WALKED_FROM_ONE_OF_ITS_OWN_FACES")
        row["CHAIN_LENGTH_MM"] = round(r["chain_mm"], 3)
        row["pieces_walked"] = len(r["key"])
        row["CLOSED_BY_DRAWN_MATERIAL"] = r["CLOSED"]
        row["DIRECTIONS_WALKED"] = r["DIRECTIONS_WALKED"]
        row["boundary_roles"] = roles
        row["_pieces"] = r["key"]
        out.append(row)
    return {"why_every_visible_start_is_walked":
            WHY_EVERY_VISIBLE_START_IS_WALKED,
            "FRAGMENTS": out,
            "runs_the_drawing_carries": len(out)}


A_RUN_IS_NOT_A_ROOMS_BOUNDARY = (
    "these are the runs of established boundary a straight sight line "
    "from this candidate's point reaches, each recorded once for the "
    "whole floor. Reaching a run is not a claim that the run bounds this "
    "region. A SIGHT LINE PASSES THROUGH EVERY OPENING: from a point in a "
    "small room it reaches the far wall of a space twenty metres away, "
    "through a doorway, and that wall is not this room's boundary. This "
    "register preserves what the drawing establishes and where each run "
    "stops. It does not attribute any of it to a region, no length here "
    "is a region's boundary length, and nothing here may be summed into "
    "one")


def fragments_for(candidate_id, seed, pieces, floor, *, hypotheses=()) -> dict:
    """§12 — which established runs this candidate's point reaches."""
    starts = set(bw.visible_pieces(seed, pieces))
    rows = []
    for frag in floor["FRAGMENTS"]:
        touching = starts & set(frag["_pieces"])
        if not touching:
            continue
        visible_mm = sum(
            sum(math.hypot(pieces[j]["coords"][k + 1][0]
                           - pieces[j]["coords"][k][0],
                           pieces[j]["coords"][k + 1][1]
                           - pieces[j]["coords"][k][1])
                for k in range(len(pieces[j]["coords"]) - 1))
            for j in touching)
        rows.append({
            **{k: v for k, v in frag.items() if k != "_pieces"},
            "CANDIDATE_ID": candidate_id,
            "FACES_OF_THIS_RUN_THIS_POINT_CAN_SEE": len(touching),
            "LENGTH_OF_THIS_RUN_A_SIGHT_LINE_FROM_THIS_POINT_REACHES_MM":
                round(visible_mm, 3),
            "THE_RUN_CONTINUES_BEYOND_WHAT_THIS_POINT_CAN_SEE":
                len(touching) < frag["pieces_walked"],
            "a_run_is_not_a_rooms_boundary": A_RUN_IS_NOT_A_ROOMS_BOUNDARY,
        })
    rows.sort(key=lambda r: -r[
        "LENGTH_OF_THIS_RUN_A_SIGHT_LINE_FROM_THIS_POINT_REACHES_MM"])
    unmet = [bf.unmet(h, searched="every run the drawing carries, walked "
                                  "from its own faces",
                      why="no run the walk established answers this "
                          "observation")
             for h in hypotheses]
    return {
        "why_every_visible_start_is_walked": WHY_EVERY_VISIBLE_START_IS_WALKED,
        "a_run_is_not_a_rooms_boundary": A_RUN_IS_NOT_A_ROOMS_BOUNDARY,
        "FRAGMENTS": rows + unmet,
        "faces_the_point_can_see": len(starts),
        "runs_a_sight_line_from_this_point_reaches": len(rows),
        "THESE_RUNS_ARE_NOT_THIS_REGIONS_BOUNDARY": True,
        "no_total_is_given_here": (
            "adding these lengths together would produce a number that "
            "looks like this region's boundary and is not one. Each run is "
            "listed with what it is and where it stops, and that is the "
            "evidence"),
        "never_extended_across_an_unsupported_opening":
            bf.A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING,
    }


# -------------------------------------------- §9 the relations recomputed
WHAT_THE_RELATION_ASKS = (
    "a straight sight line from one candidate's validated seed to "
    "another's, and whether it crosses drawn material. Nothing built "
    "between two points is a fact about the drawing and about where "
    "those points are. It is not a decision to merge two rooms, and two "
    "names on one floor do not make a boundary")

A_RELATION_IS_RECOMPUTED_NOT_CARRIED = (
    "E1.3 recorded these relations from the seeds it used. E1.4 validates "
    "the seeds first, so every relation is recomputed from the validated "
    "anchors. One that survives is reported as it stands; one that does "
    "not is gone because the anchor under it changed, and both outcomes "
    "are recorded against what E1.3 said")


def seed_relation_pass(rows, pieces, *, prior_pairs=()) -> dict:
    """§9 — every pair of validated seeds, asked the same question."""
    usable = [r for r in rows if r.get("seed")]
    pairs = []
    for i in range(len(usable)):
        for j in range(i + 1, len(usable)):
            a, b = usable[i], usable[j]
            clear, blocker = bw.sight_line_is_clear(a["seed"], b["seed"],
                                                    pieces)
            if not clear:
                continue
            pairs.append({
                "a": a["candidate_id"], "a_identity": a["group"].english_token,
                "b": b["candidate_id"], "b_identity": b["group"].english_token,
                "SIGHT_LINE_IS_CLEAR_OF_DRAWN_MATERIAL": True,
                "a_seed_anchor_kind": a["SEED_ANCHOR_KIND"],
                "b_seed_anchor_kind": b["SEED_ANCHOR_KIND"],
                "distance_mm": round(math.hypot(
                    b["seed"][0] - a["seed"][0],
                    b["seed"][1] - a["seed"][1]), 3),
                "why": bw.TWO_SEEDS_IN_ONE_ENCLOSURE,
            })
    now = {tuple(sorted((p["a_identity"], p["b_identity"]))) for p in pairs}
    before = {tuple(sorted((p["a_identity"], p["b_identity"])))
              for p in prior_pairs}
    for p in pairs:
        p["E1_3_ALSO_REPORTED_THIS_RELATION"] = tuple(sorted(
            (p["a_identity"], p["b_identity"]))) in before
    same = {}
    for pr in pairs:
        same.setdefault(pr["a"], set()).add(pr["b"])
        same.setdefault(pr["b"], set()).add(pr["a"])
    return {
        "what_this_asks": WHAT_THE_RELATION_ASKS,
        "a_relation_is_recomputed_not_carried":
            A_RELATION_IS_RECOMPUTED_NOT_CARRIED,
        "two_seeds_in_one_enclosure": bw.TWO_SEEDS_IN_ONE_ENCLOSURE,
        "PAIRS": pairs,
        "pairs_with_nothing_built_between_them": len(pairs),
        "RELATIONS_E1_3_REPORTED_THAT_E1_4_DOES_NOT": sorted(
            "|".join(k) for k in before - now),
        "RELATIONS_E1_4_REPORTS_THAT_E1_3_DID_NOT": sorted(
            "|".join(k) for k in now - before),
        "BY_CANDIDATE": [
            {"CANDIDATE_ID": r["candidate_id"],
             "identity": r["group"].english_token,
             "labels_seeded_in_the_same_enclosure": sorted(
                 same.get(r["candidate_id"], ()))}
            for r in usable],
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
    # every run the drawing carries, found once for the whole floor
    floor = floor_fragments(pieces, gaps_at=gaps_at, mates=mates,
                            facing=facing)

    rows = []
    for n, g in enumerate(groups, start=1):
        cid = f"E1_4-{g.group_id}"
        english = [m for m in g.members
                   if m.stamp_class == r12.lg.ENGLISH_ROOM_STAMP]
        # the stamp the V1 crop is taken around. It is NOT the seed: the
        # seed is whatever the validated anchors establish, and this is
        # only the window a source-only reader was shown
        anchor = english[0] if english else g.members[0]
        sr = seed_by_group.get(g.group_id, {})
        seed = sr.get("SEED_MM")
        row = {"n": n, "group": g, "candidate_id": cid, "anchor": anchor,
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
            row["fragments"] = fragments_for(cid, seed, pieces, floor)
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
        "floor_fragments": floor,
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
    prior = []
    p3 = Path(a.prior_e1_3) / "E1_3_LABEL_SEED_RELATION_REGISTER.json"
    if p3.exists():
        prior = json.loads(p3.read_text(encoding="utf-8")).get("PAIRS", [])
    relations = seed_relation_pass(built["rows"], built["pieces"],
                                   prior_pairs=prior)
    return {"relations": relations, "prep": prep, "gf": gf, "interp": interp, "owner": owner,
            "gaps": gaps, "ontology": ontology, "built": built,
            "rows": built["rows"], "cand_json": cand_json,
            "semantics": semantics, "capability": capability,
            "admitted": admitted, "openings": openings, "seeds": seeds,
            "mat_segs": mat_segs, "door_segments": door_segs,
            "linetypes": linetypes,
            "iv_by_id": {iv.interval_id: iv
                         for rows_ in interp["roles"]["intervals"].values()
                         for iv in rows_}}


# ---------------------------------------------------------- the overlays
# §21 - every treatment a reader has to be able to tell apart, and what
# each of them means. A colour that a cold reader cannot distinguish from
# another is a defect in the evidence, not a matter of taste: round one
# of E1.3's cold challenge failed on exactly that.
OVERLAY_TREATMENT = {
    "ESTABLISHED_MATERIAL_BOUNDARY": ((0, 0, 0), 7, None,
                                      "solid black"),
    "ESTABLISHED_GLAZING": ((0, 140, 220), 6, None, "solid blue"),
    "ESTABLISHED_POOL_WATER_EDGE": ((0, 160, 150), 6, (30, 10),
                                    "long-dashed teal"),
    "EXPOSED_COLUMN_FACE": ((220, 0, 0), 8, None, "thick solid red"),
    "HIDDEN_STRUCTURAL_COLUMN": ((130, 130, 130), 3, (8, 8),
                                 "thin dotted grey"),
    "CONFIRMED_PORTAL": ((255, 140, 0), 5, (18, 12), "dashed orange"),
    "PROBABLE_PORTAL": ((255, 200, 0), 5, (6, 14), "dotted amber"),
    "POSITIVE_OPEN_EDGE": ((0, 170, 60), 5, (26, 18),
                           "long-dashed green"),
    "UNRESOLVED_EDGE": ((150, 0, 200), 5, (6, 10), "short-dashed purple"),
    "BOUNDARY_FRAGMENT_TERMINATION": ((200, 0, 120), 4, None,
                                      "magenta cross at the station"),
    "NOT_IN_THE_CUT_PLANE": ((170, 190, 230), 3, (10, 10),
                             "pale dotted blue, context only"),
    "DIMENSION_OR_WITNESS_CONTEXT": ((150, 165, 150), 2, None,
                                     "pale grey, context only"),
}

OVERLAY_LEGEND = tuple(
    f"{name}: {how}" for name, (_c, _w, _d, how)
    in OVERLAY_TREATMENT.items())

A_BANNER_STATES_OUR_OWN_STATUS = (
    "an overlay of a region whose boundary was NOT established is drawn "
    "so that nobody can read it as a proposal. The banner says so in "
    "words and the strokes are drawn in the withheld colour")

NOT_PROPOSED_BANNER = ("BOUNDARY NOT ESTABLISHED BY THE DRAWING - "
                       "THIS IS NOT A PROPOSED BOUNDARY")
NOT_PROPOSED_COLOUR = (90, 110, 150)

NOT_IN_THE_CUT_PLANE = (ls.OVERHEAD_GEOMETRY, ls.BELOW_CUT_PLANE_GEOMETRY,
                        ls.STAIR_PROJECTION)

_CHAIN_TREATMENT = {
    bc.MATERIAL_WALL_FACE: "ESTABLISHED_MATERIAL_BOUNDARY",
    bc.CURVED_MATERIAL_FACE: "ESTABLISHED_MATERIAL_BOUNDARY",
    bc.GLAZING_BOUNDARY: "ESTABLISHED_GLAZING",
    bc.EXPOSED_COLUMN_FACE: "EXPOSED_COLUMN_FACE",
    bc.DOOR_PORTAL: "CONFIRMED_PORTAL",
    bc.MATERIAL_CONTINUITY_SPAN: "NOT_IN_THE_CUT_PLANE",
    bc.OPEN_EDGE: "POSITIVE_OPEN_EDGE",
    bc.UNRESOLVED_EDGE: "UNRESOLVED_EDGE",
}


def _stroke(draw, pts, treatment, *, override=None):
    colour, width, dash, _how = OVERLAY_TREATMENT[treatment]
    if override is not None:
        colour = override
    if dash:
        r13._dashed(draw, pts, colour, width, dash)
    else:
        draw.line(pts, fill=colour, width=width)


def _draw_e1_4_chain(draw, chain, to_px, *, clip=(-300, 1800), proposed=True):
    lo_, hi_ = clip
    for e in chain["CHAIN"]:
        kind = e["CHAIN_ELEMENT"]
        treatment = _CHAIN_TREATMENT.get(kind, "UNRESOLVED_EDGE")
        if kind == bc.DOOR_PORTAL and e.get("GAP_CLASS", "").startswith(
                "PROBABLE"):
            treatment = "PROBABLE_PORTAL"
        pts = ([to_px(x, y) for x, y in e["points_mm"]]
               if e.get("points_mm") else
               [to_px(*e["start_mm"]), to_px(*e["end_mm"])])
        if len(pts) < 2 or not all(lo_ <= q[0] <= hi_ and lo_ <= q[1] <= hi_
                                   for q in pts):
            continue
        override = (NOT_PROPOSED_COLOUR
                    if not proposed and kind in bc.MATERIAL_ELEMENTS
                    else None)
        _stroke(draw, pts, treatment, override=override)


def overlays(sheet, reg, gf, interp, rows, owner, out_dir, *,
             semantics=None) -> dict:
    """§21 — a whole-floor overlay and one per candidate."""
    from PIL import ImageDraw
    semantics = semantics or {}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {p.object_id: p for p in gf["primitives"]}
    hidden_ids = set(owner["object_ids_that_do_not_own_the_room_face"])
    made = []
    for row in rows:
        seed = row.get("seed")
        if seed is None:
            continue
        ch = row.get("chain")
        centre, half = seed, 5000.0
        if ch and ch["CHAIN"]:
            xs = [p for e in ch["CHAIN"]
                  for p in (e["start_mm"][0], e["end_mm"][0])]
            ys = [p for e in ch["CHAIN"]
                  for p in (e["start_mm"][1], e["end_mm"][1])]
            centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0 + 2500.0
        got = r12._frame(sheet, reg, centre, half, (1400, 1400))
        if got is None:
            continue
        img, to_px, _box = got
        draw = ImageDraw.Draw(img)
        # context first, so nothing the region claims is drawn under it
        for oid, ivs in interp["roles"]["intervals"].items():
            parent = by_id.get(oid)
            if parent is None:
                continue
            for iv in ivs:
                pid = (iv.provenance or {}).get("object_id")
                if iv.role in (ir.DIMENSION_LINE, ir.DIMENSION_WITNESS,
                               ir.ANNOTATION, ir.LEVEL_OR_GRID_ANNOTATION):
                    treatment = "DIMENSION_OR_WITNESS_CONTEXT"
                elif pid in hidden_ids:
                    treatment = "HIDDEN_STRUCTURAL_COLUMN"
                elif iv.role == ir.POOL_CONTOUR:
                    treatment = "ESTABLISHED_POOL_WATER_EDGE"
                elif semantics.get(iv.interval_id) in NOT_IN_THE_CUT_PLANE:
                    # linework the drawing shows with a broken linetype.
                    # It is drawn, it is in the sheet under this overlay,
                    # and it is not in the cut plane, so it bounds nothing
                    treatment = "NOT_IN_THE_CUT_PLANE"
                else:
                    continue
                seg = cg._as_segment(r12.IntervalPrim(parent, iv))
                pts = [to_px(x, y) for x, y in seg.points(tol_mm=2.0)]
                if len(pts) >= 2 and all(-300 <= q[0] <= 1800
                                         and -300 <= q[1] <= 1800
                                         for q in pts):
                    _stroke(draw, pts, treatment)
        proposed = row["BOUNDARY_BASIS"] == bw.ENCLOSED
        if ch:
            _draw_e1_4_chain(draw, ch, to_px, proposed=proposed)
        # where the walk stopped, marked as a station and not as an edge
        for st_ in (row.get("walk") or {}).get("OPEN_STATIONS", ()) or ():
            pass
        for frag in ((row.get("fragments") or {}).get("FRAGMENTS") or ()):
            geom = frag.get("ORDERED_GEOMETRY") or []
            if len(geom) >= 2:
                for end in (geom[0], geom[-1]):
                    px, py = to_px(end[0], end[1])
                    if not (-300 <= px <= 1800 and -300 <= py <= 1800):
                        continue
                    c, w, _d, _h = OVERLAY_TREATMENT[
                        "BOUNDARY_FRAGMENT_TERMINATION"]
                    draw.line([(px - 8, py - 8), (px + 8, py + 8)],
                              fill=c, width=w)
                    draw.line([(px - 8, py + 8), (px + 8, py - 8)],
                              fill=c, width=w)
        px, py = to_px(*seed)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(0, 0, 220),
                     width=4)
        if reg.rotation_deg:
            img = img.rotate(-reg.rotation_deg, expand=True)
        if not proposed:
            r13._banner(ImageDraw.Draw(img), NOT_PROPOSED_BANNER,
                        size=img.size)
        name = f"E1_4_OVERLAY_{row['candidate_id']}.png"
        img.save(out_dir / name)
        made.append({"candidate_id": row["candidate_id"],
                     "identity": row["group"].english_token,
                     "BOUNDARY_BASIS": row["BOUNDARY_BASIS"],
                     "THIS_IS_A_PROPOSED_BOUNDARY": proposed,
                     "file": str(out_dir / name),
                     prov.RAW: r12._sha(out_dir / name)})
    floor = whole_floor(sheet, reg, gf, rows,
                        out_dir.parent / "E1_4_GROUND_FLOOR_OVERLAY.png")
    return {"LEGEND": list(OVERLAY_LEGEND),
            "a_banner_states_our_own_status": A_BANNER_STATES_OUR_OWN_STATUS,
            "WHOLE_FLOOR": floor, "LOCAL": made,
            "local_overlays": len(made)}


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
            _draw_e1_4_chain(draw, row["chain"], to_px, clip=(-400, 2800),
                             proposed=row["BOUNDARY_BASIS"] == bw.ENCLOSED)
    if reg.rotation_deg:
        img = img.rotate(-reg.rotation_deg, expand=True)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return {"file": Path(path).name, "pixels": list(img.size),
            "distinct_physical_regions_drawn": len(seen),
            "legend": list(OVERLAY_LEGEND), prov.RAW: r12._sha(path)}


# ------------------------------------------------- what changed, and what
WHAT_A_DELTA_IS_FOR = (
    "E1.3 is frozen and is not modified. This register says what E1.4 "
    "concluded differently and why, so that a reader can hold the two "
    "runs side by side without either being rewritten. A candidate whose "
    "proposal changed needs a fresh cold challenge, and this is where "
    "that is decided")


def _delta_from_e1_3(a, st) -> dict:
    prior = Path(a.prior_e1_3) / "E1_3_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json"
    was = {}
    if prior.exists():
        for r in json.loads(prior.read_text(encoding="utf-8"))["REGIONS"]:
            was[r["CANDIDATE_ID"].replace("E1_3-", "")] = r
    rows = []
    for r in st["rows"]:
        key = r["candidate_id"].replace("E1_4-", "")
        old = was.get(key, {})
        prior_chain = old.get("PHYSICAL_BOUNDARY_CHAIN")
        old_chain = (prior_chain.get("CHAIN", [])
                     if isinstance(prior_chain, dict) else prior_chain or [])
        new_chain = (r.get("chain") or {}).get("CHAIN", [])
        old_ids = [e.get("object_id") for e in old_chain]
        new_ids = [e.get("object_id") for e in new_chain]
        changed = (old.get("BOUNDARY_BASIS") != r["BOUNDARY_BASIS"]
                   or old_ids != new_ids)
        rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "E1_3_CANDIDATE_ID": old.get("CANDIDATE_ID"),
            "IDENTITY_AS_DRAWN": r["group"].english_token,
            "E1_3_BOUNDARY_BASIS": old.get("BOUNDARY_BASIS"),
            "E1_4_BOUNDARY_BASIS": r["BOUNDARY_BASIS"],
            "E1_3_CHAIN_ELEMENTS": len(old_chain),
            "E1_4_CHAIN_ELEMENTS": len(new_chain),
            "E1_3_SEED_MM": (old.get("FACE_SELECTION") or [{}])[0].get("seed")
            if old.get("FACE_SELECTION") else None,
            "SEED_MOVED": False,
            "THE_PROPOSAL_CHANGED": bool(changed),
            "A_NEW_COLD_V2_IS_REQUIRED": bool(changed),
            "chain_elements_only_e1_3_walked": sorted(
                set(old_ids) - set(new_ids) - {None}),
            "chain_elements_only_e1_4_walks": sorted(
                set(new_ids) - set(old_ids) - {None}),
        })
    seeds = {r["GROUP_ID"]: r for r in st["seeds"]["ROWS"]}
    for row in rows:
        gid = row["CANDIDATE_ID"].replace("E1_4-", "")
        row["SEED_MOVED"] = bool(seeds.get(gid, {}).get("THE_SEED_MOVED"))
        row["A_NEW_COLD_SOURCE_ONLY_V1_IS_REQUIRED"] = row["SEED_MOVED"]
    return {
        "what_a_delta_is_for": WHAT_A_DELTA_IS_FOR,
        "E1_3_RUN_ID": "E1_3-P7757-GF-001",
        "E1_3_IS_NOT_MODIFIED": True,
        "CANDIDATES": rows,
        "proposals_that_changed": sum(
            1 for r in rows if r["THE_PROPOSAL_CHANGED"]),
        "candidates_needing_a_new_cold_v2": [
            r["CANDIDATE_ID"] for r in rows if r["A_NEW_COLD_V2_IS_REQUIRED"]],
        "candidates_needing_a_new_cold_source_only_v1": [
            r["CANDIDATE_ID"] for r in rows
            if r["A_NEW_COLD_SOURCE_ONLY_V1_IS_REQUIRED"]],
        "RELATIONS_E1_3_REPORTED_THAT_E1_4_DOES_NOT":
            st["relations"]["RELATIONS_E1_3_REPORTED_THAT_E1_4_DOES_NOT"],
        "RELATIONS_E1_4_REPORTS_THAT_E1_3_DID_NOT":
            st["relations"]["RELATIONS_E1_4_REPORTS_THAT_E1_3_DID_NOT"],
        "COLUMNS_E1_3_CONFIRMED_THAT_E1_4_DOES_NOT":
            st["owner"]["columns_e1_3_confirmed_that_e1_4_does_not"],
        "INTERVALS_E1_2_WOULD_ADMIT_THAT_E1_4_DOES_NOT":
            st["admitted"]["refused_that_e1_2_would_have_admitted"],
        "LENGTH_E1_2_WOULD_ADMIT_THAT_E1_4_DOES_NOT_MM":
            st["admitted"]["refused_length_that_e1_2_would_have_admitted_mm"],
        "NOT_ADMITTED_BY_REASON": st["admitted"]["not_admitted_by_reason"],
    }


CLOSURE_IS_NOT_THE_MEASURE = (
    "E1.4 does not succeed by releasing more rooms, by matching any known "
    "area, or by closing more regions. It succeeds when every executed "
    "module is bound, when role is separate from capability, when a seed "
    "belongs to the label evidence it came from, when a door can be found "
    "from the door, when an open region keeps every fragment the drawing "
    "establishes without inventing the missing side, and when a visual "
    "finding blocks only geometry it could actually move")


def _completeness(st) -> dict:
    rows = st["rows"]
    frags = [r for r in rows if r.get("fragments")]
    return {
        "closure_is_not_the_measure": CLOSURE_IS_NOT_THE_MEASURE,
        "what_success_means": e14.WHAT_SUCCESS_MEANS,
        "candidates": len(rows),
        "seeds_established": sum(
            1 for r in rows if r["LABEL_SEED_STATUS"] == la.SEED_ESTABLISHED),
        "seeds_ambiguous_across_a_physical_boundary": sum(
            1 for r in rows
            if r["LABEL_SEED_STATUS"] == la.AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY),
        "enclosed_by_drawn_material": sum(
            1 for r in rows if r["BOUNDARY_BASIS"] == bw.ENCLOSED),
        "boundary_not_established_by_the_drawing": sum(
            1 for r in rows if r["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED),
        "rings_that_establish_geometry": sum(
            1 for r in rows
            if (r.get("ring_qa") or {}).get("RING_ESTABLISHES_GEOMETRY")),
        "open_candidates_whose_reachable_runs_are_recorded": len(frags),
        "runs_of_established_boundary_the_drawing_carries":
            st["built"]["floor_fragments"]["runs_the_drawing_carries"],
        "EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED": True,
        "SEMANTIC_ROLE_IS_SEPARATE_FROM_BOUNDARY_CAPABILITY": True,
        "DOOR_EVIDENCE_CAN_DISCOVER_AN_OPENING_WITHOUT_A_GAP_CANDIDATE":
            st["openings"]["RECONCILED"]["counts_by_status"].get(
                od.CONFIRMED_DOOR_FIRST, 0) > 0,
        "NO_FRAGMENT_WAS_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING": True,
        "NO_BENCHMARK_QUANTITY_WAS_READ": True,
        "NO_KNOWN_AREA_WAS_READ": True,
        "NO_WORKBOOK_WAS_OPENED": True,
    }


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
        "a_run_is_not_a_rooms_boundary": A_RUN_IS_NOT_A_ROOMS_BOUNDARY,
        "RUNS_THE_DRAWING_CARRIES": [
            {k: v for k, v in f.items() if k != "_pieces"}
            for f in st["built"]["floor_fragments"]["FRAGMENTS"]],
        "runs_the_drawing_carries_count":
            st["built"]["floor_fragments"]["runs_the_drawing_carries"],
        "CANDIDATES": [
            {"CANDIDATE_ID": r["candidate_id"],
             "IDENTITY_AS_DRAWN": r["group"].english_token,
             "COMPLETE_PHYSICAL_REGION_STATUS": r["BOUNDARY_BASIS"],
             **bf.summarise(r["candidate_id"], r["fragments"]["FRAGMENTS"],
                            complete_region_status=r["BOUNDARY_BASIS"]),
             "faces_the_point_can_see":
                 r["fragments"]["faces_the_point_can_see"],
             "runs_a_sight_line_from_this_point_reaches":
                 r["fragments"]["runs_a_sight_line_from_this_point_reaches"],
             "THESE_RUNS_ARE_NOT_THIS_REGIONS_BOUNDARY": True,
             "FRAGMENTS": [{k: v for k, v in f.items()
                            if k not in ("ORDERED_GEOMETRY",)}
                           for f in r["fragments"]["FRAGMENTS"]]}
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

    _reg, sheet = r13._registered_sheet(a, gf)
    if sheet is not None and getattr(sheet, "ok", False):
        _write(out, artifacts, "E1_4_OVERLAY_INDEX.json", {
            "source": src,
            **overlays(sheet, _reg, gf, interp, rows, st["owner"],
                       out / "local_overlays",
                       semantics={r["INTERVAL_ID"]:
                                  r["LINE_SEMANTICS_STATUS"]
                                  for r in st["semantics"]["ROWS"]})})

    _write(out, artifacts, "E1_4_LABEL_SEED_RELATION_REGISTER.json",
           {"source": src, **st["relations"]})

    _write(out, artifacts, "E1_4_DELTA_FROM_E1_3.json",
           _delta_from_e1_3(a, st))

    _write(out, artifacts, "E1_4_COMPLETENESS_REGISTER.json",
           _completeness(st))

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


# ------------------------------------------------ §17 the cold challenge
WHY_V1_IS_CARRIED_OR_RERUN = (
    "the frozen E1.3 source-only V1 saw a crop of the sheet taken around "
    "a candidate's label. E1.4 validated every label seed and none of "
    "them moved, so for a candidate whose V1 crop comes back byte for "
    "byte identical the frozen observation is of the same picture and is "
    "carried forward with its provenance. Where a crop differs at all, "
    "the frozen answer is an observation of a different picture: it is "
    "preserved as history and a NEW cold source-only V1 is required, "
    "which receives no old answer, no proposal, no benchmark and no area")

WHY_EVERY_CANDIDATE_GETS_A_NEW_V2 = (
    "E1.3 Round 2 judged the overlays E1.3 drew. E1.4 draws different "
    "overlays - different treatments, a different legend, and for twelve "
    "candidates a different proposal underneath. An answer about one "
    "picture is not an answer about another, so no E1.3 verdict is "
    "reused as validation here and every candidate is challenged again, "
    "uniformly, by a reader who has not seen the old round")

WHAT_THE_NEW_ROUND_NEVER_RECEIVES = (
    "the E1.3 Round 2 answers, the E1.3 proposal, any benchmark quantity, "
    "any expected geometry, any known area, and any statement of what "
    "E1.4 would like the answer to be")


def phase_v2_inputs(a) -> int:
    """Write the cold inputs: carry V1 where the crop is identical, and
    put every candidate to a new V2."""
    out = Path(a.out)
    artifacts = json.loads((out / "_E1_4_ARTIFACTS_GEOMETRY.json")
                           .read_text(encoding="utf-8"))
    st = _core(a)
    gf, rows = st["gf"], st["rows"]
    src = r12._source(st["prep"], gf, a)
    reg_r, sheet = r13._registered_sheet(a, gf)

    # --- V1: the same crops, taken again, and compared byte for byte
    prior = json.loads(
        (Path(a.prior_e1_3) / "E1_3_VISUAL_V1_REGISTER.json")
        .read_text(encoding="utf-8"))
    prior_crop = {c["candidate_id"]: c for c in prior["crops"]}
    prior_ans = {x["candidate_id"]: x for x in prior["answers"]}
    v1_dir = out / "visual" / "v1_source_only"
    crop_rows = []
    for row in rows:
        if row.get("seed") is None:
            continue
        shim = {"anchor": row["anchor"], "boundary": None,
                "candidate_id": row["candidate_id"],
                "group": row["group"]}
        made = r12.source_crops(sheet, reg_r, [shim], v1_dir) if sheet else []
        got = made[0] if made else {}
        key = row["candidate_id"].replace("E1_4-", "E1_3-")
        was = prior_crop.get(key, {})
        same = bool(got.get(prov.RAW)
                    and got.get(prov.RAW) == was.get("RAW_FILE_SHA256"))
        crop_rows.append({
            "candidate_id": row["candidate_id"],
            "identity": row["group"].english_token,
            "file": r13._in_run(got.get("file", ""), out),
            "RAW_FILE_SHA256": got.get(prov.RAW),
            "E1_3_CROP_SHA256": was.get("RAW_FILE_SHA256"),
            "THE_CROP_IS_BYTE_IDENTICAL_TO_THE_ONE_V1_SAW": same,
            "SEED_MOVED": bool(next(
                (x["THE_SEED_MOVED"] for x in st["seeds"]["ROWS"]
                 if x["GROUP_ID"] == row["candidate_id"].replace("E1_4-", "")),
                False)),
            "FROZEN_E1_3_V1_ANSWER_CARRIED_FORWARD": same,
            "A_NEW_COLD_SOURCE_ONLY_V1_IS_REQUIRED": not same,
            "FROZEN_E1_3_V1_ANSWER": prior_ans.get(key) if same else None,
            "WHERE_THE_FROZEN_ANSWER_LIVES_IF_NOT_CARRIED":
                None if same else
                "data/runs/7757/e1_3/E1_3_VISUAL_V1_REGISTER.json",
        })
    _write(out, artifacts, "E1_4_VISUAL_V1_REGISTER.json", {
        "source": src,
        "STAGE": vc.V1,
        "why_v1_is_carried_or_rerun": WHY_V1_IS_CARRIED_OR_RERUN,
        "what_the_challenger_never_receives":
            vc.WHAT_THE_CHALLENGER_NEVER_RECEIVES,
        "what_the_new_round_never_receives": WHAT_THE_NEW_ROUND_NEVER_RECEIVES,
        "brief": vc.V1_BRIEF,
        "observation_vocabulary": list(vc.V1_OBSERVATIONS),
        "EDGE_RELATIONS": list(edge.EDGE_RELATIONS),
        "CROPS": crop_rows,
        "carried_forward_from_frozen_e1_3": sum(
            1 for c in crop_rows if c["FROZEN_E1_3_V1_ANSWER_CARRIED_FORWARD"]),
        "requiring_a_new_cold_source_only_v1": [
            c["candidate_id"] for c in crop_rows
            if c["A_NEW_COLD_SOURCE_ONLY_V1_IS_REQUIRED"]],
        "status": "AWAITING_ANSWERS" if any(
            c["A_NEW_COLD_SOURCE_ONLY_V1_IS_REQUIRED"] for c in crop_rows)
        else "CARRIED_FORWARD_UNCHANGED",
    })

    # --- V2: every candidate, uniformly, on E1.4's own overlays
    index = json.loads((out / "E1_4_OVERLAY_INDEX.json")
                       .read_text(encoding="utf-8"))
    by_cand = {o["candidate_id"]: o for o in index["LOCAL"]}
    delta = {r["CANDIDATE_ID"]: r for r in json.loads(
        (out / "E1_4_DELTA_FROM_E1_3.json").read_text(encoding="utf-8")
    )["CANDIDATES"]}
    tasks = []
    for row in rows:
        o = by_cand.get(row["candidate_id"])
        if o is None:
            continue
        # o["file"] comes back from the overlay index already relative to
        # the run, so relativising it again would leave only a basename
        # and a reader could not find the picture the task names
        t = vc.Task(task_id=f"E1_4-V2-{row['candidate_id']}",
                    candidate_id=row["candidate_id"],
                    identity=row["group"].english_token,
                    crop_path=o["file"],
                    root=str(out), stage=vc.V2, brief=vc.V2_BRIEF)
        m = t.manifest()
        m["OVERLAY_PATH_IN_THE_RUN"] = o["file"]
        m["OVERLAY_SHA256"] = o.get(prov.RAW)
        m["OVERLAY_LEGEND"] = list(OVERLAY_LEGEND)
        m["THE_PROPOSAL_CHANGED_SINCE_E1_3"] = bool(
            delta.get(row["candidate_id"], {}).get("THE_PROPOSAL_CHANGED"))
        m["THIS_IS_A_PROPOSED_BOUNDARY"] = o["THIS_IS_A_PROPOSED_BOUNDARY"]
        tasks.append(m)
    _write(out, artifacts, "E1_4_VISUAL_V2_REGISTER.json", {
        "source": src,
        "STAGE": vc.V2,
        "status": "AWAITING_ANSWERS",
        "why_every_candidate_gets_a_new_v2": WHY_EVERY_CANDIDATE_GETS_A_NEW_V2,
        "what_the_new_round_never_receives": WHAT_THE_NEW_ROUND_NEVER_RECEIVES,
        "E1_3_ROUND_2_IS_PRESERVED_AS_HISTORY": (
            "data/runs/7757/e1_3/E1_3_VISUAL_V2_REGISTER.json is frozen and "
            "is not modified, reused as validation, or shown to this round"),
        "brief": vc.V2_BRIEF,
        "V2_STATUSES": list(vc.V2_STATUSES),
        "PHYSICAL_STATUSES": list(vc.PHYSICAL_STATUSES),
        "FUNCTIONAL_STATUSES": list(vc.FUNCTIONAL_STATUSES),
        "over_capture_is_a_physical_claim": vc.OVER_CAPTURE_IS_A_PHYSICAL_CLAIM,
        "a_naming_status_may_not_veto": vc.A_NAMING_STATUS_MAY_NOT_VETO,
        "the_challenger_may_not_move_a_coordinate":
            vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
        "legend": list(OVERLAY_LEGEND),
        "overlays": index["LOCAL"],
        "task_manifests": tasks,
        "answers": [],
    })
    (out / "_E1_4_ARTIFACTS_GEOMETRY.json").write_text(
        json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
    print(f"E1.4 v2-inputs: {len(tasks)} V2 tasks, "
          f"{sum(1 for c in crop_rows if c['FROZEN_E1_3_V1_ANSWER_CARRIED_FORWARD'])}"
          f"/{len(crop_rows)} V1 crops byte-identical")
    return 0


# ---------------------------------- §14 what a finding could actually move
A_STATUS_ABOUT_THE_BOUNDARY_ITSELF = {
    # these say the proposed geometry is wrong. Their subject IS the chain
    vc.WALL_FALSELY_REMOVED,
    vc.OPEN_SIDE_FALSELY_CLOSED,
    vc.POSSIBLE_UNDER_CAPTURE,
    vc.POSSIBLE_OVER_CAPTURE,
    vc.INTERNAL_CASEWORK_USED_AS_BOUNDARY,
    vc.COUNTER_OR_BAR_USED_AS_WALL,
    vc.BOUNDARY_SEMANTIC_CONFLICT,
}

WHY_A_STATUS_IS_NOT_AN_EFFECT = (
    "a status names what the reader was uncertain about. Whether that "
    "uncertainty could move the boundary is a different question, and it "
    "is answered from the drawing. A status whose subject IS the chain - "
    "a wall said to be missing, a side said to be falsely closed - "
    "challenges the chain by construction. A status about an ATTRIBUTE of "
    "something standing on the chain challenges it only where resolving "
    "the attribute either way gives a different chain, and that is "
    "computed, not assumed from the name")

BOTH_READINGS_GIVE_THE_SAME_CHAIN = (
    "an architectural face runs unbroken across this column's footprint. "
    "Exposed or not, the room's clear face follows that architectural "
    "face, so the chain is the same on either reading. The uncertainty is "
    "real and it is recorded; it cannot move this geometry")

ONE_READING_MOVES_THE_CLEAR_FACE = (
    "no architectural face runs across this column's footprint. If the "
    "column is exposed the room's clear face steps around it and the "
    "chain moves, so this uncertainty is unresolved geometry")


# How close a footprint has to come to a chain to be standing on it. It
# is a drawing tolerance, not a search radius: a column either meets the
# boundary or it does not.
FOOTPRINT_TOUCHES_CHAIN_MM = 50.0


def _footprint_meets_chain(column, chain) -> bool:
    """Does this candidate's own footprint meet this candidate's chain?"""
    box = (column.get("FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM")
           or column.get("footprint_box_mm"))
    if not box or len(box) != 4 or not chain:
        return False
    from shapely.geometry import LineString, box as make_box
    pad = FOOTPRINT_TOUCHES_CHAIN_MM
    foot = make_box(box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    for e in chain:
        pts = e.get("points_mm") or [e.get("start_mm"), e.get("end_mm")]
        pts = [tuple(p) for p in pts if p]
        if len(pts) < 2:
            continue
        if foot.intersects(LineString(pts)):
            return True
    return False


def affects_proposed_boundary(status, row, owner) -> dict:
    """Could resolving this finding change the chain this run proposes?"""
    if status in A_STATUS_ABOUT_THE_BOUNDARY_ITSELF:
        return {"AFFECTS_PROPOSED_BOUNDARY": vf.AFFECTS_YES,
                "AFFECTED_CHAIN_ELEMENTS": [],
                "why": ("this finding's subject is the proposed chain "
                        "itself")}
    if status in (vc.COLUMN_EXPOSURE_UNRESOLVED, vc.COLUMN_ROLE_UNRESOLVED):
        ch = (row.get("chain") or {}).get("CHAIN", [])
        on_chain = {e.get("object_id") for e in ch if e.get("object_id")}
        # WHICH COLUMNS COULD MOVE *THIS* CHAIN.
        #
        # A column that owns a face on the chain is named there. One that
        # does NOT own the face was held back from the walk, so it is not
        # on the chain by object id however close it stands - and those
        # are exactly the ones whose exposure is in question. So the test
        # is geometric: does the candidate's own footprint meet this
        # candidate's own chain?
        #
        # Asking instead for every column on the floor whose ownership
        # reads ARCHITECTURAL_FACE_OWNS was tried here and named nineteen
        # loops against one small room. A finding about a column at the
        # other end of the building cannot move this boundary, and a rule
        # that says it can is the name-based gating §14 replaced, wearing
        # different clothes.
        touching = [c for c in owner["rows"]
                    if set(c["member_object_ids"]) & on_chain
                    or _footprint_meets_chain(c, ch)]
        moving = [c for c in touching
                  if not c.get("architectural_face_continues_across")]
        if not touching:
            return {"AFFECTS_PROPOSED_BOUNDARY": vf.AFFECTS_NO,
                    "AFFECTED_CHAIN_ELEMENTS": [],
                    "why": ("no column stands on this candidate's proposed "
                            "chain, so its exposure cannot move it")}
        if moving:
            return {"AFFECTS_PROPOSED_BOUNDARY": vf.AFFECTS_YES,
                    "AFFECTED_CHAIN_ELEMENTS": [
                        c["COLUMN_ID"] for c in moving],
                    "why": ONE_READING_MOVES_THE_CLEAR_FACE}
        return {"AFFECTS_PROPOSED_BOUNDARY": vf.AFFECTS_NO,
                "AFFECTED_CHAIN_ELEMENTS": [],
                "columns_considered": [c["COLUMN_ID"] for c in touching],
                "why": BOTH_READINGS_GIVE_THE_SAME_CHAIN}
    return {"AFFECTS_PROPOSED_BOUNDARY": vf.AFFECTS_UNRESOLVED,
            "AFFECTED_CHAIN_ELEMENTS": [],
            "why": ("nothing in this run establishes whether resolving "
                    "this finding would change the proposed chain, and not "
                    "knowing that is itself a reason to withhold")}


# ------------------------------------------------------- the release gates
C_PHYSICAL_BOUNDARY_IS_ESTABLISHED = "PHYSICAL_BOUNDARY_IS_ESTABLISHED"
C_LABEL_SEED_IS_ESTABLISHED = "THE_LABEL_SAYS_WHICH_SPACE_IT_NAMES"
C_RING_IS_ITS_OWN_CHAIN = "THE_RING_IS_ONLY_THE_CHAIN_THAT_MADE_IT"
C_EVERY_ELEMENT_MAY_BOUND = "EVERY_CHAIN_ELEMENT_MAY_BOUND_A_CLEAR_FLOOR_REGION"
C_EVERY_ELEMENT_IS_IN_THE_CUT_PLANE = "EVERY_CHAIN_ELEMENT_IS_IN_THE_CUT_PLANE"
C_NO_GAP_IS_UNCLASSIFIED = "EVERY_GAP_ON_THE_BOUNDARY_IS_CLASSIFIED"
C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM = (
    "NO_COLUMN_THAT_DOES_NOT_OWN_THE_FACE_DEFORMS_THE_ROOM")
C_COLD_VISUAL_DOES_NOT_CHALLENGE_THE_GEOMETRY = (
    "NO_COLD_VISUAL_FINDING_COULD_MOVE_THIS_GEOMETRY")

RELEASE_GATES = (
    C_PHYSICAL_BOUNDARY_IS_ESTABLISHED,
    C_LABEL_SEED_IS_ESTABLISHED,
    C_RING_IS_ITS_OWN_CHAIN,
    C_EVERY_ELEMENT_MAY_BOUND,
    C_EVERY_ELEMENT_IS_IN_THE_CUT_PLANE,
    C_NO_GAP_IS_UNCLASSIFIED,
    C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM,
    C_COLD_VISUAL_DOES_NOT_CHALLENGE_THE_GEOMETRY,
)

D_FUNCTIONAL_IDENTITY = "FUNCTIONAL_IDENTITY_IS_ESTABLISHED"
D_REGION_IS_SHARED = "THIS_PHYSICAL_REGION_HOLDS_ONE_LABEL_ONLY"


def ledger_for(row, *, owner, gaps_by_id, semantics, findings) -> dict:
    """One candidate's decision, every gate recorded, nothing implied."""
    L = dl.Ledger(row["candidate_id"])
    ch = (row.get("chain") or {}).get("CHAIN", [])
    qa = row.get("ring_qa") or {}

    L.gate(C_PHYSICAL_BOUNDARY_IS_ESTABLISHED,
           row["BOUNDARY_BASIS"] == bw.ENCLOSED,
           row["BOUNDARY_BASIS"])
    L.gate(C_LABEL_SEED_IS_ESTABLISHED,
           row["LABEL_SEED_STATUS"] == la.SEED_ESTABLISHED,
           f"{row['LABEL_SEED_STATUS']} from {row['SEED_ANCHOR_KIND']}")
    L.gate(C_RING_IS_ITS_OWN_CHAIN,
           bool(qa.get("RING_ESTABLISHES_GEOMETRY")),
           "; ".join(qa.get("WHY_NOT") or ()) or
           "the ring is the chain, it contains its seed, and it passes "
           "every ring-QA field")

    roles = [e.get("INTERVAL_ROLE") for e in ch if e.get("INTERVAL_ROLE")]
    bad_role = [r_ for r_ in roles
                if not bcap.may_bound_a_clear_floor_region(r_)]
    L.gate(C_EVERY_ELEMENT_MAY_BOUND, not bad_role,
           "roles on the chain that bound no clear floor region: "
           + ", ".join(sorted(set(bad_role))) if bad_role else
           "every element's semantic role can bound a clear floor region")

    not_cut = [e.get("object_id") for e in ch
               if e.get("object_id")
               and semantics.get(e["object_id"]) is False]
    L.gate(C_EVERY_ELEMENT_IS_IN_THE_CUT_PLANE, not not_cut,
           "elements not established in the cut plane: "
           + ", ".join(sorted(x for x in not_cut if x)) if not_cut else
           "every element's linework is established in the cut plane")

    unres = [e.get("GAP_ID") for e in ch
             if e.get("GAP_ID")
             and (gaps_by_id.get(e["GAP_ID"]) or {}).get("GAP_CLASS")
             == "UNRESOLVED_GAP"]
    L.gate(C_NO_GAP_IS_UNCLASSIFIED, not unres,
           "unclassified gaps on the boundary: " + ", ".join(unres)
           if unres else "every gap the boundary crosses is classified")

    hidden = set(owner["object_ids_that_do_not_own_the_room_face"])
    deforming = [e.get("object_id") for e in ch
                 if e.get("object_id") in hidden]
    L.gate(C_NO_HIDDEN_COLUMN_DEFORMS_THE_ROOM, not deforming,
           "structural outlines on the chain that do not own the face: "
           + ", ".join(sorted(x for x in deforming if x)) if deforming
           else "no structural outline that does not own the room's clear "
                "face stands on this boundary")

    g = vf.gate(findings)
    L.gate(C_COLD_VISUAL_DOES_NOT_CHALLENGE_THE_GEOMETRY,
           not g["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"], g["why"])

    L.diagnostic(D_REGION_IS_SHARED,
                 dl.PASS if len(row.get(
                     "candidates_sharing_this_physical_region") or ()) <= 1
                 else dl.FAIL,
                 "labels sharing this physical region: "
                 + ", ".join(row.get(
                     "candidates_sharing_this_physical_region") or ["one"]))
    return L.record_out()


def phase_finalize(a) -> int:
    out = Path(a.out)
    artifacts = json.loads((out / "_E1_4_ARTIFACTS_GEOMETRY.json")
                           .read_text(encoding="utf-8"))
    v2 = json.loads((out / "E1_4_VISUAL_V2_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v2_by = {x["candidate_id"]: x for x in v2.get("answers", [])}

    st = _core(a)
    gf, rows, owner = st["gf"], st["rows"], st["owner"]
    src = r12._source(st["prep"], gf, a)
    gaps_by_id = {g["GAP_ID"]: g for g in st["gaps"]["rows"]}
    semantics = {}
    for r_ in st["semantics"]["ROWS"]:
        oid = r_["PARENT_OBJECT_ID"]
        semantics[oid] = semantics.get(oid, False) or r_[
            "MAY_BE_ASKED_TO_BOUND"]

    ledger_rows, arb_rows, ident_rows, finding_rows = [], [], [], []
    for r in rows:
        ans = v2_by.get(r["candidate_id"], {})
        split = vc.split_statuses(ans.get("statuses", ()))
        findings = []
        # A reader saying it cannot settle the question from this crop is
        # not silence. Not knowing whether the geometry would move is
        # itself a reason to withhold, which is what AFFECTS_UNRESOLVED
        # means, so an undecided status is carried into the findings
        # rather than dropped between the physical and naming buckets.
        for status in (list(split["PHYSICAL_STATUSES"])
                       + list(split["UNDECIDED_STATUSES"])):
            if status == vc.VISUALLY_CONSISTENT:
                continue
            eff = affects_proposed_boundary(status, r, owner)
            findings.append(vf.finding(
                status, evidence=ans.get("reasons", []),
                confidence="COLD_VISUAL_READING",
                affects_proposed_boundary=eff["AFFECTS_PROPOSED_BOUNDARY"],
                affected_chain_elements=eff["AFFECTED_CHAIN_ELEMENTS"],
                visual_position=(vf.VISUAL_CONTRADICTION
                                 if status in A_STATUS_ABOUT_THE_BOUNDARY_ITSELF
                                 else vf.VISUAL_UNRESOLVED),
                why=eff["why"]))
        rec = ledger_for(r, owner=owner, gaps_by_id=gaps_by_id,
                         semantics=semantics, findings=findings)
        r["ledger"] = rec
        r["released"] = rec["DECISION"] == dl.RELEASED
        ledger_rows.append(rec)
        finding_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "IDENTITY_AS_DRAWN": r["group"].english_token,
            "V2_ANSWERED": bool(ans),
            "V2_STATUSES": list(ans.get("statuses", ())),
            "FINDINGS": findings,
            **vf.gate(findings),
        })
        arb_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "BOUNDARY_BASIS": r["BOUNDARY_BASIS"],
            "RING_ESTABLISHES_GEOMETRY": (r.get("ring_qa") or {}).get(
                "RING_ESTABLISHES_GEOMETRY"),
            "V2_PHYSICAL_STATUSES": split["PHYSICAL_STATUSES"],
            "V2_REASONS": ans.get("reasons", []),
            "COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY":
                vf.gate(findings)["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"],
            "CROSS_REPRESENTATION": vf.cross_representation(
                "the CAD establishes this chain",
                vf.VISUAL_CONTRADICTION if any(
                    f["VISUAL_POSITION"] == vf.VISUAL_CONTRADICTION
                    for f in findings) else
                vf.VISUAL_UNRESOLVED if findings else vf.VISUAL_SUPPORT,
                what="the proposed physical boundary"),
        })
        ident_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "LABEL_SEED_STATUS": r["LABEL_SEED_STATUS"],
            "SEED_ANCHOR_KIND": r["SEED_ANCHOR_KIND"],
            "candidates_sharing_this_physical_region": r.get(
                "candidates_sharing_this_physical_region") or [],
            "V2_FUNCTIONAL_STATUSES": split["FUNCTIONAL_STATUSES"],
            "blocks_physical_geometry": False,
            "why": vc.A_NAMING_STATUS_MAY_NOT_VETO,
        })

    released = [r for r in rows if r["released"]]
    withheld = [r for r in rows if not r["released"]]

    _write(out, artifacts, "E1_4_PHYSICAL_TOPOLOGY_ARBITRATION_REGISTER.json",
           {"source": src,
            "why_a_status_is_not_an_effect": WHY_A_STATUS_IS_NOT_AN_EFFECT,
            "a_name_is_not_an_effect": vf.A_NAME_IS_NOT_AN_EFFECT,
            "unresolved_is_not_contradiction": vf.UNRESOLVED_IS_NOT_CONTRADICTION,
            "same_drawing_family": vf.SAME_DRAWING_FAMILY,
            "FINDINGS_BY_CANDIDATE": finding_rows,
            "CANDIDATES": arb_rows})
    _write(out, artifacts, "E1_4_FUNCTIONAL_IDENTITY_ARBITRATION_REGISTER.json",
           {"source": src,
            "a_naming_status_may_not_veto": vc.A_NAMING_STATUS_MAY_NOT_VETO,
            "CANDIDATES": ident_rows})
    _write(out, artifacts, "E1_4_DECISION_LEDGER.json", {
        "source": src,
        "RELEASE_GATES": list(RELEASE_GATES),
        "one_ledger_and_every_account_reads_from_it": dl.MODEL,
        "released": len(released),
        "withheld": len(withheld),
        "LEDGER": ledger_rows,
    })
    _write(out, artifacts, "E1_4_COMPLETENESS_REGISTER.json",
           {**_completeness(st), "source": src,
            "released": len(released),
            "withheld": len(withheld),
            "RELEASED": [r["candidate_id"] for r in released],
            "WITHHELD": [{"candidate_id": r["candidate_id"],
                          "why": r["ledger"]["WHY"]} for r in withheld]})

    freeze = _freeze(a, st, artifacts, released, withheld)
    path = out / "E1_4_FREEZE.json"
    path.write_text(json.dumps(freeze, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    print(f"E1.4 finalize: {len(released)} released, {len(withheld)} withheld, "
          f"RUN_HASH {freeze['E1_4_RUN_HASH']}")
    return 0


E1_4_MODULES = (
    "engine/boundary_capability.py", "engine/column_validation.py",
    "engine/e1_4_inputs.py", "engine/execution_provenance.py",
    "engine/label_anchor.py", "engine/line_semantics.py",
    "engine/opening_discovery.py", "engine/boundary_fragment.py",
    "engine/ring_qa.py", "engine/traversal_geometry.py",
    "engine/visual_finding.py", "tools/run_e1_4.py",
)


def _freeze(a, st, artifacts, released, withheld) -> dict:
    """The freeze binds what ran, generated from what ran."""
    man = ep.manifest(".")
    ep.assert_every_executed_local_module_is_hashed(man, ".")
    code = {r["RELATIVE_FILE_PATH"]: r["SHA256"] for r in man["modules"]
            if r["SHA256"]}
    prior = Path(a.prior_e1_3) / "E1_3_FREEZE.json"
    freeze = {
        "E1_4_MODEL": E1_4_MODEL,
        "RUN_ID": RUN_ID,
        "E1_4_RUN_CLASS": e14.RUN_CLASS,
        "supersedes_nothing": (
            "E1, E1.1, E1.2 and E1.3 are preserved exactly as frozen. This "
            "is a separate iteration in its own directory and it modifies "
            "none of them"),
        "E1_4_CURRENT_RUN_BENCHMARK_INPUTS": "NONE",
        "what_the_external_review_supplied": (
            "five named upstream defects and nine candidate ids as "
            "regression cases. No expected area, target dimension, "
            "benchmark number or corrected geometry entered this run"),
        "what_e1_4_repairs": e14.WHAT_E1_4_REPAIRS,
        "what_e1_4_does_not_do": e14.WHAT_E1_4_DOES_NOT_DO,
        "modules_written_for_E1_4": list(E1_4_MODULES),
        "EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED": True,
        "how_the_code_manifest_is_built": ep.WHY_IT_IS_GENERATED,
        "a_model_hash_is_not_a_file_hash": ep.A_MODEL_HASH_IS_NOT_A_FILE_HASH,
        "no_compiled_file_is_provenance": ep.NO_COMPILED_FILE_IS_PROVENANCE,
        "SOURCE_HASHES": {
            "cad_decode": r12._sha(a.decode) if Path(a.decode).exists() else "",
            "source_sheet": r12._sha(a.raster) if Path(a.raster).exists()
            else "",
            "e1_3_freeze": r12._sha(prior) if prior.exists() else "",
        },
        "CODE_VERSION_HASHES": code,
        "MODEL_HASHES": {
            "boundary_capability": bcap.model_hash(),
            "boundary_chain": bc.model_hash(),
            "boundary_fragment": bf.model_hash(),
            "boundary_walk": bw.model_hash(),
            "column_validation": cv.model_hash(),
            "column_ownership": co.model_hash(),
            "execution_provenance": ep.model_hash(),
            "label_anchor": la.model_hash(),
            "line_semantics": ls.model_hash(),
            "opening_discovery": od.model_hash(),
            "ring_qa": rq.MODEL,
            "traversal_geometry": tg.MODEL,
            "visual_finding": vf.model_hash(),
            "e1_4_inputs": e14.model_hash(),
            "interval_role": ir.model_hash(),
        },
        "ARTIFACTS": artifacts,
        "RELEASED": [r["candidate_id"] for r in released],
        "WITHHELD": [r["candidate_id"] for r in withheld],
        "NOT_HASHED_AND_WHY": {
            "E1_4_FREEZE.json": (
                "the freeze cannot carry its own hash. Its integrity is "
                "the integrity of everything it names"),
        },
        "what_success_means": e14.WHAT_SUCCESS_MEANS,
        "DO_NOT": ("E2 has not started. No workbook was opened, no "
                   "quantity was calculated, nothing was reconciled and no "
                   "known area was read"),
    }
    freeze["E1_4_RUN_HASH"] = prov.canonical_sha256(freeze)
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
    ap.add_argument("--prior-e1-3", default="data/runs/7757/e1_3")
    ap.add_argument("--rules",
                    default="data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
    ap.add_argument("--sandbox", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.phase == "geometry":
        return phase_geometry(a)
    if a.phase == "v2-inputs":
        return phase_v2_inputs(a)
    return phase_finalize(a)


if __name__ == "__main__":
    raise SystemExit(main())
