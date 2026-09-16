"""Export the FROZEN round-5 result for external benchmarking. Read-only.

    python3 -m tools.export_round5_benchmark \
        data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg \
        --decode-json data/runs/cad_convert/P7757_ARCHITECTURAL.json \
        --out-dir data/runs/7757/round5_export

THIS TOOL CHANGES NOTHING AND DECIDES NOTHING.

It re-derives the round-5 measurement with the engine exactly as frozen,
recomputes `PROJECT_2_CAD_ROUND5_HASH`, and **refuses to write a single
file unless that hash is `8a90def3ac70301a1398aed5`**. The gate is the
whole point: an export that could not prove it describes the frozen state
would be an export of something else.

    NO THRESHOLD IS INTRODUCED. NO NUMBER IS INTERPRETED.

The percentages in §8 are ratios of lengths this run already measured.
They are diagnostics: nothing downstream may gate on them, and nothing
here compares a measured area against what a room "ought" to be.

WHAT IS AND IS NOT IN THESE FILES

Every one of the 57 physical-space polygons is exported, not the four that
released — a benchmark of the four would only measure the gate. No human
quantity, no take-off total, no Excel and no manual measurement is read,
opened or referenced anywhere in this module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_openings as copen
from engine import cad_profile as profile
from engine import face_subdivision as fsub
from engine import junction_recovery as jrec
from engine import partition_continuity as pcont
from engine import portal_match as pmatch
from engine import round5_selftest as round5
from engine import space_topologies as topo
from engine.reference_mapping import refuse_if_sealed
from tools import run_cad_pipeline as pipeline

EXPORT = "P7757_ROUND5_BENCHMARK_EXPORT_V1"

FROZEN_ROUND5_HASH = "8a90def3ac70301a1398aed5"

# Boundary segment kinds. A polygon's SIDES are the OBSERVED rows and they
# sum to its perimeter. RECOVERED and VIRTUAL_PORTAL rows are OVERLAYS that
# say which parts of those sides are not drawn material — they are not
# additional perimeter and must not be summed with it.
OBSERVED = "OBSERVED"
RECOVERED = "RECOVERED"
VIRTUAL_PORTAL = "VIRTUAL_PORTAL"

# Release classes (§7). Five separate questions, never one boolean.
RELEASE_CLASSES = ("AREA_GEOMETRY_RELEASE", "ROOM_TOPOLOGY_RELEASE",
                   "IDENTITY_RELEASE", "MATERIAL_WALL_RELEASE",
                   "OPENING_RELEASE")

YES, NO, NA = "YES", "NO", "NOT_APPLICABLE"


# ----------------------------------------------------------------- helpers

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ends(axis: str, fixed: float, lo: float, hi: float) -> tuple:
    if axis == "H":
        return (lo, fixed, hi, fixed)
    return (fixed, lo, fixed, hi)


def _undecoded(text: str) -> bool:
    """Characters above ASCII that are not Arabic — a failed SHX decode.

    Sixteen of this drawing's identities are Arabic stored in an SHX font
    the decoder returns as mojibake, and mojibake is mostly Latin letters
    with a few stray symbols in it. Without this flag the script column
    would call `M“B¢` Latin text and a benchmark would take it at
    its word.
    """
    return any(ord(ch) > 127 and not ("؀" <= ch <= "ۿ")
               for ch in text)


def _script(text: str) -> str:
    """Which script the characters are in. NOT a claim about language."""
    if _undecoded(text):
        return "TEXT_DECODE_SUSPECT_NOT_A_SCRIPT_READING"
    arabic = any("؀" <= ch <= "ۿ" for ch in text)
    latin = any(("a" <= ch.lower() <= "z") for ch in text)
    if arabic and latin:
        return "MIXED_SCRIPT"
    if arabic:
        return "ARABIC_SCRIPT"
    if latin:
        return "LATIN_SCRIPT"
    return "SCRIPT_NOT_ESTABLISHED"


def _poly(row):
    from shapely.wkt import loads

    wkt = row.enclosure.polygon_wkt if row.enclosure else ""
    if not wkt:
        return None
    try:
        return loads(wkt)
    except Exception:       # noqa: BLE001
        return None


def _line(axis: str, fixed: float, lo: float, hi: float):
    from shapely.geometry import LineString

    x0, y0, x1, y1 = _ends(axis, fixed, lo, hi)
    return LineString([(x0, y0), (x1, y1)])


def _pct(part: float, whole: float) -> float:
    return 0.0 if whole <= 0 else round(100.0 * part / whole, 3)


# --------------------------------------------------------------- the tables

def space_rows(rep, nd, context) -> list:
    """§1 and §7 and §8: one row per physical-space polygon."""
    out = []
    for row in rep.rows:
        ctx = context[row.space_id]
        e = row.enclosure
        poly = _poly(row)
        q = dict(row.quantities)
        boundary = q.get("SPACE_BOUNDARY_LENGTH_MM", 0.0)
        opening = q.get("OPENING_LENGTH_MM", 0.0)
        recovered = q.get("RECOVERED_BOUNDARY_LENGTH_MM", 0.0)
        material = q.get("MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM", 0.0)
        classes = release_classes(row, ctx)
        out.append({
            "space_id": row.space_id,
            "drawing_region_id": row.region_id,
            "polygon_hash": e.geometry_hash if e else "",
            "polygon_wkt_mm": e.polygon_wkt if e else "",
            "polygon_vertex_count": (
                0 if poly is None else len(poly.exterior.coords) - 1),
            "polygon_interior_ring_count": (
                0 if poly is None
                else len(list(getattr(poly, "interiors", ()) or ()))),
            "centroid_x_mm": (None if poly is None
                              else round(poly.centroid.x, 2)),
            "centroid_y_mm": (None if poly is None
                              else round(poly.centroid.y, 2)),
            "seed_x_mm": round(row.seed_mm[0], 2),
            "seed_y_mm": round(row.seed_mm[1], 2),
            "area_m2": (None if not e or e.area_m2 is None
                        else round(e.area_m2, 4)),
            "clear_internal_perimeter_m": (
                None if not e or e.perimeter_m is None
                else round(e.perimeter_m, 4)),
            "principal_dim_x_mm": (row.principal_dims_mm[0]
                                   if row.principal_dims_mm else None),
            "principal_dim_y_mm": (row.principal_dims_mm[1]
                                   if len(row.principal_dims_mm) > 1
                                   else None),
            "principal_dims_established": bool(row.principal_dims_mm),
            "GEOMETRY_STATUS": row.geometry_status,
            "PHYSICAL_SPACE_STATUS": row.physical_space_status,
            "IDENTITY_STATUS": row.identity_status,
            "RELEASE_STATUS": row._release()["status"],
            "release_blocker": row._release()["blocker"],
            "release_blockers_all": "; ".join(ctx["blockers"]),
            "enclosure_role": row.enclosure_role,
            "super_region_flag": row.enclosure_role == "SUPER_REGION",
            "identity_observations": " | ".join(row.label_observations),
            "identity_observation_count": len(row.label_observations),
            "normalized_identity": row.normalized_identity,
            "functional_zone_count": len(row.zones),
            "functional_zone_observations": " | ".join(
                f"{z.zone_id}={'/'.join(z.label_observations)}"
                for z in row.zones),
            "undersegmentation_status": ctx["undersegmentation"],
            "number_of_boundary_segments": len(row.boundary_roles),
            "observed_boundary_length_m": round(material / 1000.0, 4),
            "recovered_boundary_length_m": round(recovered / 1000.0, 4),
            "virtual_portal_length_m": round(opening / 1000.0, 4),
            "material_established_length_m": round(material / 1000.0, 4),
            "space_boundary_length_m": round(boundary / 1000.0, 4),
            "OBSERVED_BOUNDARY_PCT": _pct(material, boundary),
            "RECOVERED_BOUNDARY_PCT": _pct(recovered, boundary),
            "VIRTUAL_BOUNDARY_PCT": _pct(opening, boundary),
            "MATERIAL_ESTABLISHED_PCT": _pct(material, boundary),
            "unresolved_gap_count": ctx["unresolved_gaps"],
            "recovered_span_count": len(row.recovered_boundary),
            "portal_count": ctx["portals"],
            "door_count": ctx["doors"],
            "window_count": ctx["windows"],
            "archway_count": ctx["archways"],
            "TOPOLOGY_AUTHORITY": row.weakest_topology_authority,
            "MATERIAL_AUTHORITY": row.material_authority,
            **classes,
        })
    return out


def release_classes(row, ctx) -> dict:
    """§7: five separate questions, decomposed from the frozen gate.

    Nothing new is decided here. Each class reads fields the frozen run
    already produced, and `AREA_GEOMETRY_RELEASE` is exactly the gate the
    engine applied — the other four say WHY a space is or is not usable for
    a different purpose, which one boolean could never carry.
    """
    complete = row.is_complete
    release = row._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"
    topology_ok = (complete
                   and not row.unresolved_relations
                   and not ctx["ambiguous_portals"]
                   and row.weakest_topology_authority ==
                   pcont.TOPOLOGY_VALIDATED)
    if not ctx["portals"]:
        opening = NA
    elif ctx["ambiguous_portals"] or ctx["grade_d_on_boundary"]:
        opening = NO
    else:
        opening = YES
    return {
        "AREA_GEOMETRY_RELEASE": YES if release else NO,
        "ROOM_TOPOLOGY_RELEASE": YES if topology_ok else NO,
        "IDENTITY_RELEASE": (YES if row.identity_status ==
                             "IDENTITY_ESTABLISHED" else NO),
        "MATERIAL_WALL_RELEASE": (
            YES if (complete and row.material_authority ==
                    pcont.MATERIAL_ESTABLISHED) else NO),
        "OPENING_RELEASE": opening,
    }


def boundary_rows(rep, nd, context) -> list:
    """§2: every boundary segment, and every overlay on it."""
    prov = {p.object_id: p.provenance for p in nd.primitives}
    out = []
    for row in rep.rows:
        ctx = context[row.space_id]
        by_id = {o["opening_id"]: o for o in row.boundary_openings}
        for n, seg in enumerate(row.boundary_roles, 1):
            lo, hi = seg["interval_mm"]
            x0, y0, x1, y1 = _ends(seg["axis"], seg["fixed_mm"], lo, hi)
            oid = seg["cad_provenance"]
            pv = prov.get(oid)
            out.append({
                "space_id": row.space_id,
                "drawing_region_id": row.region_id,
                "segment_id": f"{row.space_id}-SEG-{n:03d}",
                "segment_kind": OBSERVED,
                "is_polygon_side": True,
                "start_x_mm": round(x0, 2), "start_y_mm": round(y0, 2),
                "end_x_mm": round(x1, 2), "end_y_mm": round(y1, 2),
                "length_mm": seg["length_mm"],
                "axis": seg["axis"],
                "boundary_role": "|".join(seg["boundary_roles"]) or
                                 "NOT_CLASSIFIED",
                "material": seg["material"],
                "topology_authority": pcont.TOPOLOGY_VALIDATED,
                "material_authority": pcont.MATERIAL_ESTABLISHED,
                "cad_entity_handles": oid,
                "cad_entity_type": (pv.entity_type if pv else ""),
                "layer_observation": (pv.layer if pv else ""),
                "block_lineage": ("/".join(pv.block_path) if pv else ""),
                "instance_lineage": ("/".join(str(h)
                                              for h in pv.instance_path)
                                     if pv else ""),
                "source_type": seg["source_type"],
                "opening_id": "",
                "portal_evidence_grade": "",
                "attribution_note": (
                    "the frozen enclosure attributes each SIDE to the drawn "
                    "piece covering most of it. Where a side is part drawn "
                    "and part recovered, the overlay rows below say which "
                    "part is which"),
            })
        for n, rec in enumerate(row.recovered_boundary, 1):
            cand = ctx["recovered_by_id"].get(rec["cad_provenance"])
            if cand is None:
                continue
            lo, hi = sorted((cand.start_mm, cand.end_mm))
            x0, y0, x1, y1 = _ends(cand.axis, cand.fixed_mm, lo, hi)
            out.append({
                "space_id": row.space_id,
                "drawing_region_id": row.region_id,
                "segment_id": f"{row.space_id}-REC-{n:03d}",
                "segment_kind": RECOVERED,
                "is_polygon_side": False,
                "start_x_mm": round(x0, 2), "start_y_mm": round(y0, 2),
                "end_x_mm": round(x1, 2), "end_y_mm": round(y1, 2),
                "length_mm": round(abs(hi - lo), 1),
                "axis": cand.axis,
                "boundary_role": rec.get("verdict", ""),
                "material": "INFERRED_NO_MATERIAL_AUTHORITY",
                "topology_authority": rec["TOPOLOGY_AUTHORITY"],
                "material_authority": rec["MATERIAL_AUTHORITY"],
                "cad_entity_handles": "",
                "cad_entity_type": "",
                "layer_observation": "",
                "block_lineage": "",
                "instance_lineage": "",
                "source_type": cand.source_type,
                "opening_id": "",
                "portal_evidence_grade": "",
                "attribution_note": (
                    "a side nobody drew. It closes room topology and it is "
                    "not measurable material"),
            })
        for n, oid in enumerate(sorted(by_id), 1):
            o = by_id[oid]
            lo, hi = o["interval_mm"]
            x0, y0, x1, y1 = _ends(o["axis"], o["fixed_mm"], lo, hi)
            out.append({
                "space_id": row.space_id,
                "drawing_region_id": row.region_id,
                "segment_id": f"{row.space_id}-POR-{n:03d}",
                "segment_kind": VIRTUAL_PORTAL,
                "is_polygon_side": False,
                "start_x_mm": round(x0, 2), "start_y_mm": round(y0, 2),
                "end_x_mm": round(x1, 2), "end_y_mm": round(y1, 2),
                "length_mm": o["OPENING_LENGTH_MM"],
                "axis": o["axis"],
                "boundary_role": o["opening_class"],
                "material": "VIRTUAL_NO_MATERIAL",
                "topology_authority": pcont.TOPOLOGY_PORTAL,
                "material_authority": pcont.MATERIAL_ABSENT,
                "cad_entity_handles": ";".join(o["symbol_provenance"]),
                "cad_entity_type": "",
                "layer_observation": "",
                "block_lineage": ";".join(o["block_names_observed"]),
                "instance_lineage": "",
                "source_type": "",
                "opening_id": oid,
                "portal_evidence_grade": o["evidence_grade"],
                "attribution_note": (
                    "the room boundary runs across the opening with zero "
                    "material"),
            })
    return out


def opening_rows(rep, context) -> list:
    """§3: every opening lying on one of the 57 polygons."""
    spaces_of = defaultdict(list)
    for row in rep.rows:
        for o in row.boundary_openings:
            spaces_of[o["opening_id"]].append(row.space_id)
    status_of = rep.matches.status_of() if rep.matches else {}
    relation_of = {}
    for g in rep.graphs:
        for r in g.relations:
            if r.get("opening_id"):
                relation_of[r["opening_id"]] = r
    out = []
    for o in rep.openings.openings:
        if o.opening_id not in spaces_of:
            continue
        rec = o.record()
        rel = relation_of.get(o.opening_id, {})
        part = rel.get(topo.ROOM_PARTITION_TOPOLOGY, {})
        mat = rel.get(topo.MATERIAL_GEOMETRY, {})
        nav = rel.get(topo.NAVIGABLE_FREE_SPACE, {})
        w = rec["widths"]
        out.append({
            "opening_id": o.opening_id,
            "space_ids": " | ".join(sorted(spaces_of[o.opening_id])),
            "space_count": len(spaces_of[o.opening_id]),
            "drawing_region_id": o.region_id,
            "opening_class": o.opening_class,
            "opening_family": _family(o.opening_class),
            "evidence_grade": o.grade,
            "GEOMETRIC_OPENING_WIDTH_MM": w["GEOMETRIC_OPENING_WIDTH_MM"],
            "BLOCK_NAME_WIDTH_RAW": w["BLOCK_NAME_WIDTH_OBSERVATION"]["raw"],
            "BLOCK_NAME_WIDTH_AGREEMENT": w["BLOCK_NAME_WIDTH_OBSERVATION"][
                "which_reading_agrees_with_geometry"],
            "DIMENSION_WIDTH_NORMALIZED_MM": w[
                "DIMENSION_WIDTH_OBSERVATION"]["normalized_mm"],
            "DIMENSION_WIDTH_VERDICT": w["DIMENSION_WIDTH_OBSERVATION"][
                "verdict"],
            "axis": o.axis,
            "fixed_mm": round(o.fixed_mm, 2),
            "start_mm": round(o.start_mm, 2),
            "end_mm": round(o.end_mm, 2),
            "host_wall_id": " | ".join(o.host_bands),
            "host_status": status_of.get(o.opening_id, o.host_status),
            "host_status_from_classifier": o.host_status,
            "cad_handles": ";".join(o.symbol_ids),
            "block_lineage": ";".join(o.block_names),
            "leaf_length_observation_mm": o.leaf_length_mm,
            "swing_radius_observation_mm": o.swing_radius_mm,
            "evidence": ";".join(o.evidence),
            "MATERIAL_TOPOLOGY": (
                "OPEN_NO_MATERIAL" if mat.get("connected", True)
                else "MATERIAL_PRESENT"),
            "ROOM_PARTITION_TOPOLOGY": rel.get(
                "ROOM_PARTITION_RELATION",
                part.get("ROOM_PARTITION_RELATION", "NOT_EVALUATED")),
            "ROOM_PARTITION_STATUS": part.get("status", ""),
            "NAVIGATION_TOPOLOGY": (
                "PASSABLE" if nav.get("connected") else "NOT_PASSABLE"),
            "may_close_a_room_boundary": o.may_close_boundary,
            "may_assert_two_distinct_rooms": o.may_partition_rooms,
        })
    return out


def _family(klass: str) -> str:
    if klass in (copen.DOOR_WITH_LEAF, copen.DOOR_PORTAL):
        return "DOOR"
    if klass == copen.WINDOW_OPENING:
        return "WINDOW"
    if klass in (copen.DOORLESS_ARCHWAY, copen.OPEN_PLAN_CONNECTION):
        return "ARCHWAY"
    return "UNRESOLVED"


def identity_rows(rep, nd) -> list:
    """§4: every semantic observation, including the unreadable ones."""
    prov = {t.provenance.object_id: t.provenance for t in nd.texts}
    regions = rep.regions
    group_of, space_of = {}, {}
    for g in (rep.identity.groups if rep.identity else ()):
        for o in g.observations:
            group_of[o.observation_id] = g
    for row in rep.rows:
        for oid in row.provenance:
            space_of[oid] = row.space_id
    out = []
    for o in rep.semantic.observations:
        src = o.provenance[0] if o.provenance else ""
        pv = prov.get(src)
        region = regions.of_point(o.x, o.y) if regions else None
        gid = f"OBS-{src}"
        g = group_of.get(gid)
        space = space_of.get(gid, "")
        out.append({
            "observation_id": o.observation_id,
            "drawing_region_id": (region.region_id if region else
                                  "UNASSIGNED"),
            "x_mm": round(o.x, 2),
            "y_mm": round(o.y, 2),
            "raw_decoded_text": o.text,
            "normalized_text": (g.normalized_identity if g else ""),
            "semantic_concept": (g.observations[0].concept if g and
                                 g.observations else ""),
            "semantic_class": o.semantic_class,
            "benchmark_class": _benchmark_class(o.semantic_class),
            "concept_class": (g.concept_class if g else ""),
            "identity_group_id": (g.group_id if g else ""),
            "identity_status": (g.identity_status if g
                                else "NOT_RECONCILED"),
            "identity_relationship": (g.relationship if g else ""),
            "carrier_block": o.carrier_block,
            "block_lineage": ("/".join(pv.block_path) if pv else ""),
            "instance_lineage": ("/".join(str(h) for h in pv.instance_path)
                                 if pv else ""),
            "cad_handle": src,
            "layer_observation": (pv.layer if pv else ""),
            "script_observation": _script(o.text),
            "text_decode_suspect": _undecoded(o.text),
            "classifier_reasons": ";".join(o.reasons),
            "space_id": space,
            "association_status": (
                "ASSOCIATED_WITH_A_PHYSICAL_SPACE" if space
                else "RECONCILED_BUT_NOT_INSIDE_A_MEASURED_POLYGON" if g
                else "NOT_USED_FOR_IDENTITY"),
        })
    return out


def _benchmark_class(semantic_class: str) -> str:
    return {"ROOM_LIKE": "ROOM", "ZONE_LIKE": "ZONE",
            "EXTERNAL_SPACE_LIKE": "EXTERNAL_SPACE",
            "NON_SPACE_ANNOTATION": "ANNOTATION"}.get(semantic_class,
                                                      "UNKNOWN")


def dimension_rows(rep, nd) -> list:
    """§5: every association ATTEMPTED, not only the ones that agreed."""
    prov = {d.provenance.object_id: d for d in nd.dimensions}
    out = []
    for row in rep.rows:
        poly = _poly(row)
        bounds = poly.bounds if poly is not None else (None,) * 4
        for c in row.dimension_checks:
            handle = c.get("dimension_provenance", "")
            d = prov.get(handle)
            if c["axis"] == "X":
                w_lo, w_hi = bounds[0], bounds[2]
                w_at = None if poly is None else (bounds[1] + bounds[3]) / 2
            else:
                w_lo, w_hi = bounds[1], bounds[3]
                w_at = None if poly is None else (bounds[0] + bounds[2]) / 2
            out.append({
                "dimension_id": f"{row.space_id}-DIM-{c['axis']}",
                "cad_handle": handle,
                "drawing_region_id": row.region_id,
                "space_id": row.space_id,
                "geometry_association": f"{c['axis']}_SPAN_OF_POLYGON",
                "axis": c["axis"],
                "display_value": c.get("DIMENSION_DISPLAY_VALUE"),
                "DIMLFAC": c.get("dimlfac_applied", nd.dimlfac),
                "normalized_value_mm": c.get(
                    "DIMENSION_NORMALIZED_VALUE_MM"),
                "geometry_value_mm": c["GEOMETRY_MEASURED_VALUE_MM"],
                "residual_mm": c.get("residual_mm"),
                "status": c["verdict"],
                "witness_lo_mm": (None if w_lo is None else round(w_lo, 2)),
                "witness_hi_mm": (None if w_hi is None else round(w_hi, 2)),
                "witness_offset_mm": (None if w_at is None
                                      else round(w_at, 2)),
                "dimension_x1_mm": (None if d is None else round(d.x1, 2)),
                "dimension_y1_mm": (None if d is None else round(d.y1, 2)),
                "dimension_x2_mm": (None if d is None else round(d.x2, 2)),
                "dimension_y2_mm": (None if d is None else round(d.y2, 2)),
                "why": c.get("why", ""),
            })
    return out


def region_rows(rep, nd) -> list:
    """§6: the nine drawing regions. Floors stay unnamed."""
    spaces = Counter(r.region_id for r in rep.rows)
    walls = {w.region_id: len(w.walls) for w in rep.walls}
    doors, windows = Counter(), Counter()
    for o in rep.openings.openings:
        if _family(o.opening_class) == "DOOR":
            doors[o.region_id] += 1
        elif _family(o.opening_class) == "WINDOW":
            windows[o.region_id] += 1
    obs = Counter()
    for o in rep.semantic.observations:
        region = rep.regions.of_point(o.x, o.y)
        obs[region.region_id if region else "UNASSIGNED"] += 1
    out = []
    for r in rep.regions.regions:
        pop = r.populations
        out.append({
            "drawing_region_id": r.region_id,
            "floor_name": r.floor_name,
            "x0_mm": round(r.x0, 2), "y0_mm": round(r.y0, 2),
            "x1_mm": round(r.x1, 2), "y1_mm": round(r.y1, 2),
            "width_mm": round(r.width_mm, 1),
            "height_mm": round(r.height_mm, 1),
            "is_major": r.is_major,
            "geometry_count": pop.get("geometry_marks", 0),
            "wall_band_count": walls.get(r.region_id, 0),
            "door_count": doors.get(r.region_id, 0),
            "window_count": windows.get(r.region_id, 0),
            "semantic_observation_count": obs.get(r.region_id, 0),
            "dimension_count": pop.get("authored_dimensions", 0),
            "block_instance_count": pop.get("block_instances", 0),
            "arc_and_circle_count": pop.get("arc_and_circle_symbols", 0),
            "layers_present": pop.get("layers_present", 0),
            "physical_polygon_count": spaces.get(r.region_id, 0),
            "assignment_pad_mm": round(r.pad_mm, 1),
            "naming_note": ("floors are not named. Nothing in this run "
                            "established which drawing is which storey"),
        })
    return out


# ------------------------------------------------------------- the context

def build_context(rep) -> dict:
    """Per-space facts that live across several report objects."""
    amb = {m.opening_id for m in (rep.matches.ambiguous()
                                  if rep.matches else [])}
    diag = {}
    for s in rep.subdivisions:
        for d in s.diagnoses:
            diag[d.space_id] = d.outcome
    spans_by_region = defaultdict(list)
    for c in rep.continuity:
        spans_by_region[c.region_id].extend(c.spans)
    recovered_by_id = {}
    for g in rep.graphs:
        for cand in g.recovered:
            recovered_by_id[cand.object_id] = cand

    out = {}
    for row in rep.rows:
        poly = _poly(row)
        gaps = 0
        if poly is not None:
            for s in spans_by_region.get(row.region_id, ()):
                if s.verdict != pcont.UNRESOLVED_GAP:
                    continue
                for f in s.faces_mm:
                    line = _line(s.axis, f, s.lo, s.hi)
                    if poly.distance(line) <= 1.0:
                        gaps += 1
                        break
        families = Counter(_family(o["opening_class"])
                           for o in row.boundary_openings)
        blockers = []
        blocker = row._release()["blocker"]
        if blocker:
            blockers.append(blocker)
        if row.material_authority != pcont.MATERIAL_ESTABLISHED:
            blockers.append("MATERIAL_AUTHORITY_IS_"
                            + row.material_authority)
        if row.identity_status != "IDENTITY_ESTABLISHED":
            blockers.append("IDENTITY_IS_" + row.identity_status)
        out[row.space_id] = {
            "unresolved_gaps": gaps,
            "portals": len(row.boundary_openings),
            "doors": families.get("DOOR", 0),
            "windows": families.get("WINDOW", 0),
            "archways": families.get("ARCHWAY", 0),
            "ambiguous_portals": [o["opening_id"]
                                  for o in row.boundary_openings
                                  if o["opening_id"] in amb],
            "grade_d_on_boundary": [
                o["opening_id"] for o in row.boundary_openings
                if o["evidence_grade"] == copen.GRADE_D],
            "undersegmentation": diag.get(row.space_id, "NOT_FLAGGED"),
            "blockers": blockers,
            "recovered_by_id": recovered_by_id,
        }
    return out


# ------------------------------------------------------------------ writing

def _write(out_dir: Path, name: str, rows: list, notes: dict) -> list:
    """One table, as CSV and as JSON. Both hashed."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    csv_path = out_dir / f"{name}.csv"
    fields = sorted({k for r in rows for k in r}) if rows else []
    order = [f for f in _PREFERRED if f in fields]
    fields = order + [f for f in fields if f not in order]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    written.append(csv_path)
    json_path = out_dir / f"{name}.json"
    json_path.write_text(json.dumps({
        "export": EXPORT,
        "table": name,
        "derived_from": {"PROJECT_2_CAD_ROUND5_HASH": FROZEN_ROUND5_HASH},
        "rows": len(rows),
        "columns": fields,
        "notes": notes,
        "data": rows,
    }, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    written.append(json_path)
    return written


_PREFERRED = ["space_id", "opening_id", "observation_id", "dimension_id",
              "segment_id", "drawing_region_id"]


def export(dwg: str, *, decode_json: str, out_dir: str) -> dict:
    """Re-derive the frozen state, prove it, then write the tables."""
    refuse_if_sealed(dwg)
    path = Path(dwg)
    src_hash = pipeline._hash(path)

    r2, r3, r4, r5 = _freezes()
    decoded = json.loads(Path(decode_json).read_text(errors="replace"))
    nd = adapter.normalize(decoded, source_file=path.name,
                           source_hash=src_hash)
    prof = profile.build(nd)
    rep = measure.measure(nd, prof)

    got = pipeline._round5_hash(nd, prof, rep, src_hash, r5)
    if got != FROZEN_ROUND5_HASH:
        raise SystemExit(
            "REFUSING TO EXPORT. This run computes "
            f"PROJECT_2_CAD_ROUND5_HASH {got}, and the frozen result being "
            f"benchmarked is {FROZEN_ROUND5_HASH}. An export that cannot "
            "prove it describes the frozen state would be an export of "
            "something else.")

    context = build_context(rep)
    tables = {
        "P7757_ROUND5_SPACE_EXPORT": (
            space_rows(rep, nd, context),
            {"scope": "every physical-space polygon, not only the released "
                      "ones",
             "percentages": "diagnostic only. No release threshold is "
                            "derived from them anywhere",
             "observed_vs_material": (
                 "observed_boundary_length_m and "
                 "material_established_length_m are equal BY CONSTRUCTION "
                 "in round 5: material authority is withheld along exactly "
                 "the spans that were recovered rather than drawn. Both "
                 "columns are kept so a later round that separates them "
                 "does not silently change a column's meaning")}),
        "P7757_ROUND5_BOUNDARY_EXPORT": (
            boundary_rows(rep, nd, context),
            {"segment_kinds": {
                OBSERVED: "a SIDE of the polygon. These sum to its "
                          "perimeter",
                RECOVERED: "an OVERLAY marking part of a side that nobody "
                           "drew. NOT additional perimeter",
                VIRTUAL_PORTAL: "an OVERLAY marking part of a side that is "
                                "an opening. NOT additional perimeter"},
             "attribution": "the frozen enclosure names one drawn piece "
                            "per side — the one covering most of it"}),
        "P7757_ROUND5_OPENING_EXPORT": (
            opening_rows(rep, context),
            {"scope": "openings lying on one of the exported polygons",
             "three_topologies": "material, room-partition and navigation "
                                 "are reported separately and never "
                                 "collapsed"}),
        "P7757_ROUND5_IDENTITY_EXPORT": (
            identity_rows(rep, nd),
            {"scope": "every semantic observation on the drawing",
             "unknowns": "UNKNOWN observations are exported, not discarded. "
                         "Sixteen of this drawing's identities are Arabic "
                         "in an SHX font this decoder returns as mojibake, "
                         "and the raw text is given as decoded",
             "script": "script_observation reports CHARACTERS, not a "
                       "claim about language. text_decode_suspect marks "
                       "strings carrying non-Arabic characters above "
                       "ASCII, which is what a failed SHX decode of Arabic "
                       "looks like — read those raw strings as BYTES, not "
                       "as words"}),
        "P7757_ROUND5_DIMENSION_EXPORT": (
            dimension_rows(rep, nd),
            {"scope": "every association ATTEMPTED",
             "warning": "the row count is attempts, not validations. Read "
                        "the status column"}),
        "P7757_ROUND5_REGION_EXPORT": (
            region_rows(rep, nd),
            {"floors": "not named. Nothing established which drawing is "
                       "which storey"}),
    }

    out = Path(out_dir)
    files, written = {}, []
    for name, (rows, notes) in tables.items():
        for p in _write(out, name, rows, notes):
            written.append(p)
            files[p.name] = {"rows": len(rows),
                             "bytes": p.stat().st_size,
                             "sha256": _sha256(p)}

    manifest = {
        "export": EXPORT,
        "derived_from": {
            "PROJECT_2_CAD_ROUND5_HASH": FROZEN_ROUND5_HASH,
            "recomputed_here": got,
            "gate": "the export refuses to write unless these are equal",
        },
        "source": {"file": path.name, "sha256_16": src_hash,
                   "decode_json": decode_json,
                   "decode_sha256_16": pipeline._hash(Path(decode_json))},
        "engine_freezes": {
            "ROUND_5_SYNTHETIC_HASH": r5["ROUND_5_SYNTHETIC_HASH"],
            "PHYSICAL_WALL_BAND_HASH": r5["PHYSICAL_WALL_BAND_HASH"],
            "PARTITION_CONTINUITY_HASH": r5["PARTITION_CONTINUITY_HASH"],
            "JUNCTION_RECOVERY_HASH": r5["JUNCTION_RECOVERY_HASH"],
            "FACE_SUBDIVISION_HASH": r5["FACE_SUBDIVISION_HASH"],
            "FREEZE_MANIFEST_SCHEMA_HASH": r5[
                "FREEZE_MANIFEST_SCHEMA_HASH"],
            "CAD_OPENING_CLASSIFIER_HASH": copen.classifier_hash(),
            "PORTAL_MATCHER_HASH": pmatch.matcher_hash(),
            "JUNCTION_RECOVERY_MODEL": jrec.MODEL,
            "FACE_SUBDIVISION_MODEL": fsub.SUBDIVIDER,
        },
        "release_classes": list(RELEASE_CLASSES),
        "files": files,
        "counts": {
            name: len(rows) for name, (rows, _n) in tables.items()},
        "what_this_export_does_not_do": (
            "it decides nothing, tunes nothing and compares nothing against "
            "an expected answer. No human quantity, take-off total, Excel "
            "or manual measurement is read or referenced"),
    }
    payload = json.dumps(
        {"files": {k: v["sha256"] for k, v in sorted(files.items())},
         "PROJECT_2_CAD_ROUND5_HASH": FROZEN_ROUND5_HASH,
         "export": EXPORT}, sort_keys=True)
    manifest["ROUND5_BENCHMARK_EXPORT_MANIFEST_HASH"] = hashlib.sha256(
        payload.encode("utf-8")).hexdigest()[:24]

    mpath = out / "ROUND5_BENCHMARK_EXPORT_MANIFEST.json"
    mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)
                     + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(mpath)
    return manifest


def _freezes() -> tuple:
    from engine import round2_selftest as r2m
    from engine import round3_selftest as r3m
    from engine import round4_selftest as r4m

    return (r2m.assert_frozen(), r3m.assert_frozen(), r4m.assert_frozen(),
            round5.assert_frozen())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dwg")
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--out-dir", default="data/runs/7757/round5_export")
    a = ap.parse_args(argv)
    m = export(a.dwg, decode_json=a.decode_json, out_dir=a.out_dir)
    print(json.dumps({
        "ROUND5_BENCHMARK_EXPORT_MANIFEST_HASH": m[
            "ROUND5_BENCHMARK_EXPORT_MANIFEST_HASH"],
        "derived_from": m["derived_from"],
        "counts": m["counts"],
        "files": {k: v["sha256"][:16] for k, v in m["files"].items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
