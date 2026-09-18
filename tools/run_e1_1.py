"""E1.1 — CAD entity role and region ownership correction, then freeze.

    python -m tools.run_e1_1 --out data/runs/7757/e1_1 \
        --sandbox <dir> --decode <cad decode>.json --raster <sheet>.jpeg

E1 v1 is not touched. This is a separate iteration, written because four
released regions were wrong for one family of reasons: a LAYER was
allowed to say what an ENTITY is. A kitchen cabinet front, a pantry
counter, a pool's setting-out lines and a garden's internal edge all sat
on wall-heavy layers, and all four became room walls.

The order of work here is the correction:

    1  read the sheet's typography and group the bilingual stamps, so one
       room labelled twice is ONE functional identity
    2  read the circular geometry as circular geometry, so a line drawn
       from a centre is a setting-out line and not a partition
    3  find the stairs, so treads are treads
    4  ESTABLISH A ROLE FOR EVERY ENTITY, and offer the tracer only the
       entities whose established role may bound material
    5  trace once per functional identity, from where the label is SEEN
    6  compare every candidate with every other one
    7  look at each candidate on the original sheet, and on the drawing's
       own dimensions, before releasing it
    8  release only when all ten conditions hold, and withhold otherwise

No benchmark, Excel, reconciliation, corrected area or target quantity is
opened, and nothing here is tuned to an expected number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from engine import agent_sandbox as sbx
from engine import cad_adapter as adapter
from engine import cad_entity_role as cer
from engine import cad_geometry as cg
from engine import cad_profile as cprofile
from engine import curve_semantics as cs
from engine import drawing_region as dreg
from engine import e1_1_inputs as ei
from engine import e1_region as er
from engine import e1_release as rel
from engine import export_provenance as prov
from engine import label_grouping as lg
from engine import raster_qa as rq
from engine import stair_completeness as stc

E1_1_MODEL = "E1_1_CAD_ENTITY_ROLE_AND_REGION_OWNERSHIP_CORRECTION_V1"
RUN_ID = "E1_1-P7757-GF-001"

# A layer default proposes what is worth testing. Nothing more.
PAIRED_SHARE_WALL_LIKE = 0.45

CONTROLLED_INTEGRATION_REGRESSION = "CONTROLLED_INTEGRATION_REGRESSION"

E1_1_NEW_MODULES = ("engine/cad_entity_role.py", "engine/curve_semantics.py",
                    "engine/label_grouping.py", "engine/raster_qa.py",
                    "engine/e1_release.py", "engine/stair_completeness.py",
                    "engine/e1_1_inputs.py", "tools/run_e1_1.py")
E1_MODULES_CARRIED_FORWARD = ("engine/cad_geometry.py", "engine/e1_region.py",
                              "engine/e1_inputs.py")
BENCHMARK_INFORMED_LINEAGE = (
    "engine/cad_adapter.py", "engine/cad_profile.py",
    "engine/cad_regions.py", "engine/drawing_region.py")

# --- delta reasons (§M) --------------------------------------------------
NO_CHANGE = "NO_CHANGE"
RELEASE_TO_WITHHOLD = "RELEASE_TO_WITHHOLD"
WITHHOLD_TO_RELEASE = "WITHHOLD_TO_RELEASE"
BOUNDARY_RESHAPED = "BOUNDARY_RESHAPED"
IDENTITY_GROUPED = "IDENTITY_GROUPED"
ENTITY_ROLE_CORRECTED = "ENTITY_ROLE_CORRECTED"
OVERLAP_CONFLICT = "OVERLAP_CONFLICT"
VISUAL_QA_VETO = "VISUAL_QA_VETO"
OTHER_EXPLAINED = "OTHER_EXPLAINED"
DELTA_REASONS = (NO_CHANGE, RELEASE_TO_WITHHOLD, WITHHOLD_TO_RELEASE,
                 BOUNDARY_RESHAPED, IDENTITY_GROUPED, ENTITY_ROLE_CORRECTED,
                 OVERLAP_CONFLICT, VISUAL_QA_VETO, OTHER_EXPLAINED)


def _sha(path) -> str:
    return prov.raw_sha256(path)


def _english_token(label) -> str:
    """The ASCII part of a bilingual label, for joining on identity."""
    parts = [p.strip() for p in str(label or "").split("/")]
    for part in reversed(parts):
        tok = re.sub(r"[^A-Za-z. ]", "", part).strip()
        if len(tok) >= 3:
            return " ".join(tok.upper().split())
    return ""


# ------------------------------------------------------------- the source

def layer_roles(profile) -> dict:
    """LAYER_DEFAULT_ROLE only. E1.1 never releases on this alone."""
    out = {}
    for lay in profile.layers:
        paired = lay.paired_share
        if lay.proposed_role == "DIMENSION_BEARING":
            default, conf = cg.DIMENSION_WITNESS, "MEDIUM"
        elif paired >= PAIRED_SHARE_WALL_LIKE:
            default, conf = cg.MATERIAL_WALL_FACE, (
                "HIGH" if paired >= 0.6 else "MEDIUM")
        elif lay.total_length_mm < 100.0:
            default, conf = cg.ANNOTATION_ONLY, "LOW"
        else:
            default, conf = cg.ROLE_UNRESOLVED, "LOW"
        out[lay.layer] = {
            "source_layer": lay.layer,
            "LAYER_DEFAULT_ROLE": default,
            "WHAT_A_LAYER_DEFAULT_IS":
                cer.A_LAYER_IS_CANDIDATE_GENERATION_ONLY,
            "confidence": conf,
            "evidence": {
                "entities": lay.entities,
                "total_length_m": round(lay.total_length_mm / 1000, 2),
                "paired_share": paired,
                "face_separations_mm": [round(t, 1)
                                        for t in lay.thicknesses_mm[:8]],
                "profile_proposed_role": lay.proposed_role,
                "profile_status": lay.status,
            },
        }
    return out


def prepare(decode_path) -> dict:
    decode = json.loads(Path(decode_path).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    profile = cprofile.build(nd)
    regions = dreg.isolate(nd)
    roles = layer_roles(profile)
    return {"decode": decode, "nd": nd, "profile": profile,
            "regions": regions, "layer_roles": roles}


def ground_floor(prep, *, region_id="DR-002") -> dict:
    region = [r for r in prep["regions"].regions
              if r.region_id == region_id][0]
    nd = prep["nd"]
    prims = [p for p in nd.primitives if region.holds(p.object_id)]
    texts = [t for t in nd.texts if region.contains(t.x, t.y)]
    dims = [d for d in nd.dimensions
            if region.contains(d.x1, d.y1) or region.contains(d.x2, d.y2)]
    return {"region": region, "primitives": prims, "texts": texts,
            "dimensions": dims}


# --------------------------------------------------------- the E1.1 pass

def interpret(gf, prep, *, door_layers=("D",)) -> dict:
    """Identity, curves, stairs and an established role for every entity."""
    prims = gf["primitives"]
    defaults = {k: v["LAYER_DEFAULT_ROLE"]
                for k, v in prep["layer_roles"].items()}
    dim_layers = [k for k, v in defaults.items()
                  if v == cg.DIMENSION_WITNESS]
    ann_layers = [k for k, v in defaults.items()
                  if v == cg.ANNOTATION_ONLY]

    # 1 — identity, from typography and placement
    labels = lg.build(gf["texts"], typo=lg.typography(prep["decode"]))

    # 2 — circular geometry read as circular geometry
    label_points = []
    for g in labels["groups"]:
        cx, cy = g.centroid
        if g.english_token:
            label_points.append((cx, cy, g.english_token))
    curves = cs.classify(prims, label_points=label_points)

    # 3 — a first role pass, so annotation and dimensions are out of the
    #     way before the stair pass looks for treads
    phase1 = cer.establish(prims, layer_defaults=defaults,
                           dimension_layers=dim_layers,
                           annotation_layers=ann_layers,
                           door_layers=set(door_layers),
                           curve_roles=curves["curve_roles"])
    not_a_tread = (cer.DIMENSION_LINE, cer.DIMENSION_WITNESS, cer.DOOR,
                   cer.ANNOTATION, cer.CONSTRUCTION_LINE,
                   cer.POOL_INTERNAL_GEOMETRY, cer.POOL_CONTOUR)
    skip = [k for k, v in phase1["roles"].items()
            if v.established_role in not_a_tread]
    centres = [(o.cx, o.cy, max(o.radii_mm))
               for o in curves["round_objects"] if len(o.radii_mm) >= 2]
    stair_labels = [(g.centroid[0], g.centroid[1], g.english_token)
                    for g in labels["groups"] if g.english_token]
    stairs = stc.detect(prims, exclude_object_ids=skip,
                        radial_centres=centres,
                        stair_label_points=stair_labels)

    # 4 — the role pass that counts, with treads known
    roles = cer.establish(prims, layer_defaults=defaults,
                          dimension_layers=dim_layers,
                          annotation_layers=ann_layers,
                          door_layers=set(door_layers),
                          curve_roles=curves["curve_roles"],
                          stair_object_ids=stairs["tread_object_ids"])
    return {"labels": labels, "curves": curves, "stairs": stairs,
            "roles": roles, "layer_defaults": defaults,
            "dimension_layers": dim_layers, "annotation_layers": ann_layers}


def material_segments(gf, interp) -> dict:
    """The only geometry allowed to bound a physical region."""
    roles = interp["roles"]["roles"]
    keep, refused = [], {}
    for p in gf["primitives"]:
        if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
            continue
        r = roles.get(p.object_id)
        if r is None or not r.may_bound_material:
            key = r.established_role if r else "NOT_IN_REGISTER"
            refused[key] = refused.get(key, 0) + 1
            continue
        keep.append(p)
    segs = []
    for p in keep:
        r = roles[p.object_id]
        segs.append(cg._as_segment(p, role=r.boundary_role()))
    return {"primitives": keep, "segments": segs,
            "refused_by_established_role": refused}


def a18_index(candidates) -> dict:
    out = {}
    for c in candidates:
        tok = _english_token(c.get("label_as_drawn", ""))
        if tok:
            out.setdefault(tok, []).append(c)
    return out


def build_candidates(gf, interp, mat, a18_by_token, *, sheet=None) -> dict:
    """One trace per FUNCTIONAL IDENTITY, from where the label is seen."""
    from shapely.geometry import Point, Polygon

    barriers = cg.close_openings(
        mat["primitives"], wall_layers=(), door_layers={"D"},
        tol_mm=cg.DENSIFY_TOL_MM)["barriers"]
    closure = cg.close_openings(mat["primitives"], wall_layers=(),
                                door_layers={"D"})
    extra = tuple(mat["segments"]) + tuple(closure["barriers"])

    groups = [g for g in interp["labels"]["groups"] if g.english_token]
    site_area = None
    rows = []
    for n, g in enumerate(groups, start=1):
        english = [m for m in g.members
                   if m.stamp_class == lg.ENGLISH_ROOM_STAMP]
        anchor = english[0] if english else g.members[0]
        seed = anchor.visible_centroid
        out = cg.trace(seed, [], wall_layers=(), tol_mm=cg.DENSIFY_TOL_MM,
                       role_of=None, extra_segments=extra)
        area = None
        if out.get("candidates"):
            area = out["candidates"][0]["densified_area_m2_rendering_only"]
            site_area = max(site_area or 0.0, area)
        rows.append({"n": n, "group": g, "anchor": anchor, "seed": seed,
                     "trace": out})

    # which OTHER functional identities are seen inside each face
    for row in rows:
        out = row["trace"]
        inside = []
        if out.get("candidates"):
            try:
                poly = Polygon(out["candidates"][0]["boundary"].points())
                if poly.is_valid:
                    for other in rows:
                        cx, cy = other["anchor"].visible_centroid
                        if poly.contains(Point(cx, cy)):
                            inside.append(other["group"].english_token)
            except Exception:
                inside = [row["group"].english_token]
        row["labels_inside"] = tuple(sorted(set(inside)))
    return {"rows": rows, "closure": closure, "barriers": barriers,
            "site_area_m2_rendering_only": site_area, "extra": extra}


def assess_all(built, interp, mat, gf, a18_by_token, *, sheet, reg) -> dict:
    """Assess, then compare globally, then decide release for each."""
    roles = interp["roles"]["roles"]
    site = built["site_area_m2_rendering_only"]
    rows = []
    for row in built["rows"]:
        g = row["group"]
        tok = g.english_token
        hits = a18_by_token.get(tok, [])
        regn = er.assess(
            cad_geometry_id=f"E1_1-{g.group_id}",
            a18_candidate_id=",".join(c["candidate_id"] for c in hits),
            drawing_id="P7757_ARCHITECTURAL.dwg", floor="GROUND",
            label=tok, trace_result=row["trace"],
            labels_in_face=row["labels_inside"], a18_identity=bool(hits))
        regn = er.validate(regn, released_boundaries=[], site_area_m2=site)
        rows.append({**row, "region": regn, "a18": hits})

    # --- §F, before any release -----------------------------------------
    cands = []
    for r in rows:
        b = r["region"].boundary
        if b is None:
            continue
        try:
            pts = b.points()
        except Exception:
            continue
        if len(pts) < 4:
            continue
        cands.append({"id": r["region"].cad_geometry_id, "points": pts,
                      "label_group": r["group"].group_id,
                      "object_kind": _object_kind(r, interp)})
    overlaps = rel.overlap_relations(cands)
    by_id = {}
    for o in overlaps:
        by_id.setdefault(o["a"], []).append(o)
        by_id.setdefault(o["b"], []).append(o)

    # --- §G §K §J -------------------------------------------------------
    for r in rows:
        g, regn = r["group"], r["region"]
        hits = r["a18"]
        statements = []
        for c in hits:
            statements.append(c.get("pass_b_statement", ""))
            statements += list(c.get("pass_b_boundary_statements", ()))
        topo = rel.a18_topology_claim(*statements)
        shape = rel.a18_shape_observations(*statements)
        a18_point_inside = None
        if hits and reg is not None and reg.established:
            a18_point_inside = _a18_point_inside(hits, regn, reg)
        align = rel.alignment_status(
            has_a18_identity=bool(hits), a18_topology=topo, a18_shape=shape,
            a18_geometry_source=(hits[0].get("geometry_source")
                                 if hits else None),
            released=regn.released, outcome=regn.outcome,
            boundary=regn.boundary,
            label_point_inside=True,
            a18_label_point_inside=a18_point_inside)
        dim_rows = rel.dimension_cross_check(regn.boundary,
                                             gf["dimensions"])
        visual = rel.visual_gate(
            boundary=regn.boundary, entity_roles=roles,
            distinct_label_groups=set(r["labels_inside"]),
            dimension_rows=dim_rows, sheet=sheet, registration=reg)
        alias_conflict = _alias_conflict(r, interp)
        decision = rel.release_decision(
            boundary=regn.boundary, outcome=regn.outcome,
            closed_outcome=er.CLOSED_PHYSICAL_REGION, entity_roles=roles,
            label_groups_inside=set(r["labels_inside"]),
            alias_conflict=alias_conflict,
            overlap_relations=by_id.get(regn.cad_geometry_id, []),
            alignment=align, visual=visual)
        r["alignment"] = align
        r["visual"] = visual
        r["decision"] = decision
        r["overlaps"] = by_id.get(regn.cad_geometry_id, [])
        regn.released = bool(decision["released"] and regn.released)
    return {"rows": rows, "overlaps": overlaps,
            "site_area_m2_rendering_only": site}


def _object_kind(row, interp) -> str:
    """Is this candidate a nested architectural object rather than a room?"""
    b = row["region"].boundary
    if b is None:
        return ""
    for s in b.segments:
        info = interp["curves"]["curve_roles"].get(s.object_id)
        if info:
            return "ROUND_OBJECT"
    return ""


def _alias_conflict(row, interp) -> bool:
    """Did an alternate-language stamp create a second function here?

    E1.1 counts a second function only from a READABLE room stamp in a
    DIFFERENT label group, so an Arabic stamp or an unreadable SHX token
    inside the same ring cannot produce one. This function checks that
    outcome rather than assuming it: it finds the non-English stamps
    actually inside the ring and confirms that none of them appears among
    the functions counted against this region.
    """
    from shapely.geometry import Point, Polygon
    b = row["region"].boundary
    if b is None:
        return False
    try:
        poly = Polygon(b.points())
        if not poly.is_valid:
            return False
    except Exception:
        return False
    counted = set(row["labels_inside"])
    for s in interp["labels"]["stamps"]:
        if s.stamp_class == lg.ENGLISH_ROOM_STAMP:
            continue
        cx, cy = s.visible_centroid
        if not poly.contains(Point(cx, cy)):
            continue
        if s.text.upper() in counted:
            return True
    return False


def _a18_point_inside(hits, regn, reg):
    from shapely.geometry import Point, Polygon
    if regn.boundary is None:
        return None
    try:
        poly = Polygon(regn.boundary.points())
        if not poly.is_valid:
            return None
    except Exception:
        return None
    for c in hits:
        box = c.get("box")
        if not box or len(box) != 4:
            continue
        px, py = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
        x, y = reg.to_mm(px, py)
        if poly.contains(Point(x, y)):
            return True
    return False


# --------------------------------------------------------------- overlays

TREATMENT = {
    cg.MATERIAL_WALL_FACE: ((20, 20, 20), 5, "solid black"),
    cg.CURVED_MATERIAL_FACE: ((0, 120, 200), 7, "solid blue, thicker"),
    cg.GLAZING_BOUNDARY: ((0, 170, 170), 5, "solid cyan"),
    cg.COLUMN_FACE: ((120, 60, 160), 5, "solid purple"),
    cg.VIRTUAL_PORTAL_BOUNDARY: ((230, 120, 0), 5, "dashed orange"),
    cg.CAD_JUNCTION_REPAIR: ((160, 160, 60), 3, "dotted olive"),
    cg.OPEN_EDGE: ((220, 30, 30), 5, "dashed red"),
    cg.ROLE_UNRESOLVED: ((140, 140, 140), 3, "grey"),
}
DASHED_ROLES = (cg.VIRTUAL_PORTAL_BOUNDARY, cg.OPEN_EDGE,
                cg.CAD_JUNCTION_REPAIR)
CASEWORK_COLOUR = (200, 0, 200)


def _draw(draw, seg, to_px, *, colour=None, width=None):
    col, wid, _n = TREATMENT.get(seg.role, TREATMENT[cg.ROLE_UNRESOLVED])
    col = colour or col
    wid = width or wid
    pts = [to_px(x, y) for x, y in seg.points(tol_mm=cg.DENSIFY_TOL_MM)]
    if len(pts) < 2:
        return
    if seg.role in DASHED_ROLES:
        if len(pts) == 2:
            (ax, ay), (bx, by) = pts
            n = 9
            for i in range(0, n, 2):
                draw.line([(ax + (bx - ax) * i / n, ay + (by - ay) * i / n),
                           (ax + (bx - ax) * (i + 1) / n,
                            ay + (by - ay) * (i + 1) / n)],
                          fill=col, width=wid)
        else:
            for i in range(0, len(pts) - 1, 2):
                draw.line([pts[i], pts[i + 1]], fill=col, width=wid)
    else:
        draw.line(pts, fill=col, width=wid)


def sheet_overlay(sheet, reg, gf, interp, result, out_path, *,
                  centre_mm=None, half_mm=None, size=(1800, 1800)) -> dict:
    """A candidate drawn ON THE ORIGINAL SHEET, not on pale CAD lines."""
    from PIL import Image, ImageDraw, ImageFont
    if sheet is None or not sheet.ok:
        return {}
    region = gf["region"]
    if centre_mm is None:
        centre_mm = ((region.x0 + region.x1) / 2.0,
                     (region.y0 + region.y1) / 2.0)
        half_mm = max(region.x1 - region.x0, region.y1 - region.y0) / 2.0 + 500
    x0, y0 = centre_mm[0] - half_mm, centre_mm[1] - half_mm
    x1, y1 = centre_mm[0] + half_mm, centre_mm[1] + half_mm
    got = sheet.crop(x0, y0, x1, y1)
    if got is None:
        return {}
    crop, box = got
    img = crop.convert("RGB").resize(size, Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    sx = size[0] / max(1, box[2] - box[0])
    sy = size[1] / max(1, box[3] - box[1])

    def to_px(x, y):
        px, py = reg.to_px(x, y)
        return ((px - box[0]) * sx, (py - box[1]) * sy)
    return {"img": img, "draw": draw, "to_px": to_px, "box": box,
            "path": out_path}


def _finish(bundle, *, title, subtitle, legend_rows) -> dict:
    from PIL import ImageFont
    img, draw = bundle["img"], bundle["draw"]
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    bold = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    draw.rectangle([0, 0, img.size[0], 40 + 26 * (len(legend_rows) + 1)],
                   fill=(255, 255, 255))
    draw.text((14, 6), title, font=bold, fill=(20, 20, 20))
    y = 40
    draw.text((14, y), subtitle, font=font, fill=(150, 40, 40))
    y += 26
    for text, col in legend_rows:
        draw.line([(16, y + 10), (70, y + 10)], fill=col, width=5)
        draw.text((82, y), text, font=font, fill=(50, 50, 50))
        y += 26
    img.save(bundle["path"])
    return {"file": Path(bundle["path"]).name,
            "pixels": list(img.size),
            prov.RAW: _sha(bundle["path"])}


def candidate_overlays(sheet, reg, gf, interp, result, out_dir) -> list:
    """§K: one overlay per candidate, BEFORE release, on the sheet."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    roles = interp["roles"]["roles"]
    rows = []
    for r in result["rows"]:
        regn = r["region"]
        b = regn.boundary
        cx, cy = r["anchor"].visible_centroid
        half = 5000.0
        if b is not None:
            bb = b.bbox_for_indexing_only().get("extent_mm")
            if bb:
                cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
                half = max(bb[2] - bb[0], bb[3] - bb[1]) / 2.0 + 2000.0
        name = f"E1_1_LOCAL_{regn.cad_geometry_id}.png"
        bundle = sheet_overlay(sheet, reg, gf, interp, result,
                               out_dir / name, centre_mm=(cx, cy),
                               half_mm=half, size=(1500, 1500))
        if not bundle:
            continue
        draw, to_px = bundle["draw"], bundle["to_px"]
        # casework and other non-material entities nearby, so what was
        # EXCLUDED from the boundary is visible beside what was kept
        for p in gf["primitives"]:
            if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
                continue
            role = roles.get(p.object_id)
            if role is None or role.established_role not in (
                    cer.CABINET_FRONT, cer.COUNTER_EDGE, cer.CASEWORK,
                    cer.POOL_INTERNAL_GEOMETRY, cer.CONSTRUCTION_LINE):
                continue
            seg = cg._as_segment(p)
            pts = [to_px(x, y) for x, y in seg.points(
                tol_mm=cg.DENSIFY_TOL_MM)]
            if len(pts) >= 2 and all(-200 <= q[0] <= 1700
                                     and -200 <= q[1] <= 1700 for q in pts):
                draw.line(pts, fill=CASEWORK_COLOUR, width=3)
        if b is not None:
            for seg in b.segments:
                _draw(draw, seg, to_px)
        for bar in result.get("barriers", ()):
            _draw(draw, bar, to_px)
        px, py = to_px(*r["anchor"].visible_centroid)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(0, 0, 220),
                     width=4)
        x0, y0, x1, y1 = r["anchor"].render_extent
        draw.rectangle([to_px(x0, y0), to_px(x1, y1)], outline=(0, 0, 220),
                       width=2)
        for d in gf["dimensions"]:
            mid = ((d.x1 + d.x2) / 2.0, (d.y1 + d.y2) / 2.0)
            if abs(mid[0] - cx) > half or abs(mid[1] - cy) > half:
                continue
            draw.line([to_px(d.x1, d.y1), to_px(d.x2, d.y2)],
                      fill=(0, 150, 0), width=2)
        rec = _finish(
            bundle,
            title=f"{regn.cad_geometry_id}  {regn.label_as_drawn}",
            subtitle=(f"{'/'.join(r['visual']['VISUAL_QA_STATE'])}  |  "
                      f"{r['decision']['decision']}  |  {regn.outcome}"),
            legend_rows=[
                ("material boundary", (20, 20, 20)),
                ("curved material face", (0, 120, 200)),
                ("portal / open edge (nothing built)", (230, 120, 0)),
                ("casework, pool internals, setting-out: EXCLUDED",
                 CASEWORK_COLOUR),
                ("the drawing's own dimensions", (0, 150, 0)),
                ("where the label is SEEN, and its render extent",
                 (0, 0, 220)),
            ])
        rec.update({"CAD_GEOMETRY_ID": regn.cad_geometry_id,
                    "VISUAL_QA_STATE": r["visual"]["VISUAL_QA_STATE"],
                    "decision": r["decision"]["decision"],
                    "drawn_before_release": True})
        rows.append(rec)
    return rows


def whole_floor_overlay(sheet, reg, gf, interp, result, out_path) -> dict:
    bundle = sheet_overlay(sheet, reg, gf, interp, result, out_path,
                           size=(3600, 3600))
    if not bundle:
        return {}
    draw, to_px = bundle["draw"], bundle["to_px"]
    roles = interp["roles"]["roles"]
    for p in gf["primitives"]:
        role = roles.get(p.object_id)
        if role is None or role.established_role not in (
                cer.CABINET_FRONT, cer.COUNTER_EDGE, cer.CASEWORK,
                cer.POOL_INTERNAL_GEOMETRY, cer.CONSTRUCTION_LINE):
            continue
        if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
            continue
        seg = cg._as_segment(p)
        pts = [to_px(x, y) for x, y in seg.points(tol_mm=cg.DENSIFY_TOL_MM)]
        if len(pts) >= 2:
            draw.line(pts, fill=CASEWORK_COLOUR, width=3)
    drawn = {}
    for r in result["rows"]:
        b = r["region"].boundary
        if b is None:
            continue
        for seg in b.segments:
            _draw(draw, seg, to_px)
            drawn[seg.role] = drawn.get(seg.role, 0) + 1
    for a in interp["stairs"]["assemblies"]:
        for t in a.treads:
            draw.line([to_px(t.x1, t.y1), to_px(t.x2, t.y2)],
                      fill=(255, 140, 0), width=3)
    rec = _finish(
        bundle,
        title="E1.1 GROUND FLOOR — ON THE ORIGINAL SHEET",
        subtitle=("boundaries are drawn on the sheet, not on CAD linework, "
                  "so under- and over-capture are visible"),
        legend_rows=[("released or candidate material boundary", (20, 20, 20)),
                     ("curved material face", (0, 120, 200)),
                     ("portal / open edge", (230, 120, 0)),
                     ("casework, pool internals, setting-out: EXCLUDED",
                      CASEWORK_COLOUR),
                     ("stair treads", (255, 140, 0))])
    rec["segments_drawn_by_role"] = drawn
    return rec


# ----------------------------------------------------------- the sandbox

def build_sandbox(root, *, decode, a18_dir, rules, raster, prior_e1) -> dict:
    run = ei.E1_1Run(run_id=RUN_ID,
                     subject="E1.1 CAD entity role and region ownership",
                     floor="GROUND")
    run.notes["why_E1_is_not_blind"] = ei.ei.WHY_E1_IS_NOT_BLIND
    run.notes["why_the_raster_is_admitted"] = ei.WHY_THE_RASTER_IS_ADMITTED
    run.notes["why_the_prior_run_is_admitted"] = (
        ei.WHY_THE_PRIOR_RUN_IS_ADMITTED)
    box = sbx.Sandbox(root=Path(root), run=run, working_dirs=())
    a18 = Path(a18_dir)
    plan = [
        (ei.Input(input_id="CAD_DECODE", kind=ei.ei.CAD_GEOMETRY_SOURCE,
                  what_it_is="the authoritative DWG-derived geometry",
                  path=str(decode)), "cad/P7757_ARCHITECTURAL.json"),
        (ei.Input(input_id="PASS_B_REGISTER", kind=ei.ei.FROZEN_PASS_B,
                  what_it_is="frozen A18 Pass B semantic hypotheses",
                  path=str(a18 / "A18_VISUAL_ZONE_REGISTER.json")),
         "a18/A18_VISUAL_ZONE_REGISTER.json"),
        (ei.Input(input_id="PASS_D_CANDIDATES", kind=ei.ei.FROZEN_PASS_D,
                  what_it_is="every frozen A18 ground-floor hypothesis",
                  path=str(a18 / "A18_PASS_D_CANDIDATES.json")),
         "a18/A18_PASS_D_CANDIDATES.json"),
        (ei.Input(input_id="PASS_C2_RECORD", kind=ei.ei.FROZEN_PASS_C2,
                  what_it_is="frozen Pass C2 challenge record",
                  path=str(a18 / "A18-GF-001_PASS_C2.json")),
         "a18/A18-GF-001_PASS_C2.json"),
        (ei.Input(input_id="SUPERVISED_FLOORS",
                  kind=ei.ei.CAD_SOURCE_METADATA,
                  what_it_is="which drawing region is which floor",
                  path="data/registry/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
         "cad/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
    ]
    if raster:
        plan.append((ei.Input(
            input_id="SOURCE_SHEET", kind=ei.SOURCE_RASTER_QA,
            what_it_is="the original ground-floor sheet, for QA only",
            path=str(raster)), f"sheet/{Path(raster).name}"))
    for name in ("E1_A18_CAD_ALIGNMENT_REGISTER.json",
                 "E1_CAD_GEOMETRY_REGISTER.json",
                 "E1_STAIR_REGISTER.json", "E1_FREEZE.json"):
        p = Path(prior_e1) / name
        if p.exists():
            plan.append((ei.Input(
                input_id=f"E1_V1_{name.split('.')[0]}",
                kind=ei.PRIOR_E1_ITERATION_REGISTER,
                what_it_is="E1 v1's frozen register, for the delta only",
                path=str(p)), f"e1_v1/{name}"))
    if rules:
        plan.append((ei.Input(
            input_id="GENERAL_RULES", kind=ei.ei.GENERAL_GEOMETRY_RULE,
            what_it_is="approved general Urban geometry rules, projected",
            content=rules), "rules/general_geometry_rules.json"))

    placed, refused = 0, []
    for item, at in plan:
        try:
            box.place(item, at=at)
            placed += 1
        except sbx.RefusedInput as exc:
            refused.append({"at": at, "why": str(exc)})
    report = box.assert_ready()
    man = box.manifest()
    man["plan"] = {"offered": len(plan), "placed": placed,
                   "refused_and_not_placed": refused}
    return {"box": box, "report": report, "manifest": man}


def code_hashes() -> dict:
    out = {}
    for relpath in (list(E1_1_NEW_MODULES) + list(E1_MODULES_CARRIED_FORWARD)
                    + list(BENCHMARK_INFORMED_LINEAGE)
                    + ["engine/agent_sandbox.py",
                       "engine/benchmark_protection.py"]):
        p = Path(relpath)
        if p.exists():
            out[relpath] = _sha(p)
    return out


# ------------------------------------------------------------- the delta

def delta_from_e1_v1(result, interp, gf, prior_dir) -> dict:
    """WHY each region changed. Geometry and outcomes only, no quantity."""
    path = Path(prior_dir) / "E1_A18_CAD_ALIGNMENT_REGISTER.json"
    if not path.exists():
        return {"available": False,
                "why": "E1 v1's alignment register was not admitted"}
    prior = json.loads(path.read_text(encoding="utf-8"))
    old = {}
    for row in prior.get("rows", ()):
        tok = (row.get("cad_stamp") or {}).get("english_token") or ""
        if not tok:
            continue
        old.setdefault(tok.upper(), []).append(row)

    rows, counts = [], {}
    seen = set()
    for r in result["rows"]:
        tok = r["group"].english_token
        seen.add(tok)
        was = old.get(tok, [])
        was_released = any(x.get("RELEASED") for x in was)
        now_released = bool(r["region"].released)
        reasons = []
        if len(was) > 1 and len(r["group"].members) > 1:
            reasons.append(IDENTITY_GROUPED)
        roles_on_ring = _roles_corrected(r, interp, gf)
        if roles_on_ring:
            reasons.append(ENTITY_ROLE_CORRECTED)
        if r["overlaps"] and any(
                o["relation"] not in rel.OVERLAP_PERMITS_RELEASE
                for o in r["overlaps"]):
            reasons.append(OVERLAP_CONFLICT)
        if rel.VISUALLY_CONSISTENT not in r["visual"]["VISUAL_QA_STATE"]:
            reasons.append(VISUAL_QA_VETO)
        if was_released and not now_released:
            reasons.insert(0, RELEASE_TO_WITHHOLD)
        elif now_released and not was_released:
            reasons.insert(0, WITHHOLD_TO_RELEASE)
        elif was_released and now_released:
            reasons.insert(0, BOUNDARY_RESHAPED if roles_on_ring
                           else NO_CHANGE)
        elif not reasons:
            reasons.append(NO_CHANGE)
        if not reasons:
            reasons.append(OTHER_EXPLAINED)
        for x in reasons:
            counts[x] = counts.get(x, 0) + 1
        rows.append({
            "identity": tok,
            "E1_1_CAD_GEOMETRY_ID": r["region"].cad_geometry_id,
            "E1_V1_CAD_GEOMETRY_IDS": [x.get("CAD_GEOMETRY_ID")
                                       for x in was],
            "E1_V1_stamps": len(was),
            "E1_1_label_group_members": len(r["group"].members),
            "E1_V1_RELEASED": was_released,
            "E1_1_RELEASED": now_released,
            "E1_V1_OUTCOME": sorted({x.get("E1_OUTCOME") for x in was}),
            "E1_1_OUTCOME": r["region"].outcome,
            "E1_V1_A18_ALIGNMENT_STATUS": sorted(
                {x.get("A18_ALIGNMENT_STATUS") for x in was}),
            "E1_1_A18_ALIGNMENT_STATUS":
                r["alignment"]["A18_ALIGNMENT_STATUS"],
            "VISUAL_QA_STATE": r["visual"]["VISUAL_QA_STATE"],
            "CHANGE_REASONS": reasons,
            "entity_roles_that_changed_the_ring": roles_on_ring,
            "why": "; ".join(r["decision"]["failed"]) or
                   "all ten release conditions hold",
        })
    dropped = sorted(set(old) - seen)
    return {
        "available": True,
        "prior_register": str(path),
        "prior_register_sha256": _sha(path),
        "DELTA_REASONS": list(DELTA_REASONS),
        "reason_counts": counts,
        "rows": rows,
        "identities_in_E1_v1_not_carried_forward": dropped,
        "no_quantity_is_compared": (
            "this register compares outcomes, roles and topology. No area, "
            "length or quantity of either iteration is compared with the "
            "other or with anything else"),
    }


def _roles_corrected(row, interp, gf=None) -> list:
    """Roles E1.1 kept OFF this ring that a layer default would admit.

    Per region: the entities lying within the candidate's own neighbourhood
    whose LAYER says wall but whose ESTABLISHED role says otherwise. Those
    are the entities E1 v1 would have offered the tracer here.
    """
    roles = interp["roles"]["roles"]
    b = row["region"].boundary
    if b is None or gf is None:
        return []
    bb = b.bbox_for_indexing_only().get("extent_mm")
    if not bb:
        return []
    x0, y0, x1, y1 = bb
    out = {}
    for p in gf["primitives"]:
        r = roles.get(p.object_id)
        if r is None or r.layer_default_role != cg.MATERIAL_WALL_FACE:
            continue
        if r.established_role == cer.MATERIAL_WALL_FACE:
            continue
        mx = (p.x1 + p.x2) / 2.0 if p.kind == "SEGMENT" else p.cx
        my = (p.y1 + p.y2) / 2.0 if p.kind == "SEGMENT" else p.cy
        if x0 <= mx <= x1 and y0 <= my <= y1:
            out[r.established_role] = out.get(r.established_role, 0) + 1
    return [f"{k}={v}" for k, v in sorted(out.items())]


# ------------------------------------------------------------------ main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode",
                    default="data/runs/cad_convert/P7757_ARCHITECTURAL.json")
    ap.add_argument("--a18-dir", default="data/runs/7757/blind/A18-GF-001")
    ap.add_argument("--raster",
                    default="data/runs/7757/blind/A18-GF-001/images/"
                            "page-01.jpeg")
    ap.add_argument("--prior-e1", default="data/runs/7757/e1")
    ap.add_argument("--rules",
                    default="data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
    ap.add_argument("--sandbox", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    rules = None
    if a.rules and Path(a.rules).exists():
        from engine import blind_input_contract as bicm
        lib = json.loads(Path(a.rules).read_text(encoding="utf-8"))
        rules = bicm.general_rules(lib)

    seal = build_sandbox(a.sandbox, decode=a.decode, a18_dir=a.a18_dir,
                         rules=rules, raster=a.raster, prior_e1=a.prior_e1)

    prep = prepare(a.decode)
    gf = ground_floor(prep)
    interp = interpret(gf, prep)
    mat = material_segments(gf, interp)

    reg = sheet = None
    if a.raster and Path(a.raster).exists():
        region = gf["region"]
        reg = rq.register(a.raster, gf["primitives"],
                          extent=(region.x0, region.y0, region.x1, region.y1))
        sheet = rq.Sheet(reg)

    cand = json.loads(
        (Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json").read_text(
            encoding="utf-8"))["candidates"]
    a18_by_token = a18_index(cand)

    built = build_candidates(gf, interp, mat, a18_by_token, sheet=sheet)
    result = assess_all(built, interp, mat, gf, a18_by_token,
                        sheet=sheet, reg=reg)
    result["barriers"] = built["barriers"]
    result["closure"] = built["closure"]

    nd = prep["nd"]
    source = {
        "DRAWING_ID": "P7757_ARCHITECTURAL.dwg",
        "decode_file": str(a.decode),
        "decode_sha256": _sha(a.decode),
        "decoder": nd.notes.get("decoder", "LibreDWG"),
        "NORMALIZATION_HASH": nd.normalization_hash(),
        "drawing_unit": nd.drawing_unit,
        "insunits_code": nd.insunits_code,
        "dimlfac": nd.dimlfac,
        "primitives": len(nd.primitives),
        "arcs": sum(1 for p in nd.primitives if p.kind == "ARC"),
        "circles": sum(1 for p in nd.primitives if p.kind == "CIRCLE"),
        "texts": len(nd.texts),
        "FLOOR": "GROUND",
        "drawing_region": gf["region"].record(),
    }

    artifacts = {}

    def write(name, body):
        body = dict(body)
        body["E1_1_MODEL"] = E1_1_MODEL
        body["RUN_ID"] = RUN_ID
        body[f"{name.split('.')[0]}_HASH"] = prov.canonical_sha256(body)
        path = out / name
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                                   default=str) + "\n", encoding="utf-8")
        artifacts[name] = _sha(path)
        return body

    rows = result["rows"]
    released = [r for r in rows if r["region"].released]
    withheld = [r for r in rows if not r["region"].released]
    roles = interp["roles"]["roles"]

    # --- §A the entity role register ------------------------------------
    write("E1_1_ENTITY_ROLE_REGISTER.json", {
        "source": source,
        "the_correction": {
            "LAYER_DEFAULT_ROLE": "CANDIDATE_GENERATION_EVIDENCE_ONLY",
            "ENTITY_ESTABLISHED_ROLE":
                "REQUIRED_BEFORE_A_SEGMENT_MAY_BOUND_MATERIAL",
            "why": cer.A_LAYER_IS_CANDIDATE_GENERATION_ONLY,
            "unknown_cannot_release_as_material_wall":
                cer.UNKNOWN_CANNOT_RELEASE_AS_MATERIAL_WALL,
        },
        "ENTITY_ROLES": list(cer.ENTITY_ROLES),
        "MAY_BOUND_MATERIAL": list(cer.MAY_BOUND_MATERIAL),
        "counts_by_established_role": interp["roles"]["counts"],
        "entities": interp["roles"]["entities"],
        "entities_that_may_bound_material":
            interp["roles"]["may_bound_material"],
        "refused_from_the_tracer_by_established_role":
            mat["refused_by_established_role"],
        "layer_defaults": prep["layer_roles"],
        "frozen_parameters": cer.frozen_parameters(),
        "rows": [r.record() for r in sorted(
            roles.values(), key=lambda r: (r.established_role,
                                           -r.length_mm))],
    })

    # --- §D §E the bilingual label register ------------------------------
    write("E1_1_BILINGUAL_LABEL_REGISTER.json", {
        "source": source,
        "counts": interp["labels"]["counts"],
        "group_counts": interp["labels"]["group_counts"],
        "dominant_text_style_handle":
            interp["labels"]["dominant_text_style_handle"],
        "no_token_mapping_is_encoded":
            interp["labels"]["no_token_mapping_is_encoded"],
        "insertion_point_is_weak_evidence":
            lg.INSERTION_POINT_IS_WEAK_EVIDENCE,
        "an_unresolved_token_is_not_a_second_function":
            lg.AN_UNRESOLVED_TOKEN_IS_NOT_A_SECOND_FUNCTION,
        "frozen_parameters": lg.frozen_parameters(),
        "LABEL_GROUPS": [g.record() for g in interp["labels"]["groups"]],
        "STAMPS": [s.record() for s in interp["labels"]["stamps"]],
    })

    # --- §F the global overlap register ----------------------------------
    write("E1_1_GLOBAL_OVERLAP_REGISTER.json", {
        "source": source,
        "OVERLAP_RELATIONS": list(rel.OVERLAP_RELATIONS),
        "OVERLAP_PERMITS_RELEASE": list(rel.OVERLAP_PERMITS_RELEASE),
        "two_rooms_may_not_occupy_one_place":
            rel.TWO_ROOMS_MAY_NOT_OCCUPY_ONE_PLACE,
        "candidates_compared": len(rows),
        "relations_found": len(result["overlaps"]),
        "counts": {k: sum(1 for o in result["overlaps"]
                          if o["relation"] == k)
                   for k in rel.OVERLAP_RELATIONS},
        "rows": result["overlaps"],
    })

    # --- §K the visual release QA register -------------------------------
    write("E1_1_VISUAL_RELEASE_QA_REGISTER.json", {
        "source": source,
        "VISUAL_QA_STATES": list(rel.VISUAL_QA_STATES),
        "only_visually_consistent_releases":
            rel.ONLY_VISUALLY_CONSISTENT_RELEASES,
        "raster_registration": reg.record() if reg is not None else {
            "REGISTRATION_ESTABLISHED": False,
            "why": "no source sheet was admitted"},
        "raster_frozen_parameters": rq.frozen_parameters(),
        "what_the_sheet_may_not_do": rq.RASTER_DOES_NOT_CALCULATE_GEOMETRY,
        "counts": {s: sum(1 for r in rows
                          if s in r["visual"]["VISUAL_QA_STATE"])
                   for s in rel.VISUAL_QA_STATES},
        "rows": [{"CAD_GEOMETRY_ID": r["region"].cad_geometry_id,
                  "identity": r["group"].english_token,
                  "VISUAL_QA_STATE": r["visual"]["VISUAL_QA_STATE"],
                  "notes": r["visual"]["notes"],
                  "dimension_cross_check":
                      r["visual"]["dimension_cross_check"],
                  "overlay_drawn_before_release": True}
                 for r in rows],
    })

    # --- §I the stair completeness register ------------------------------
    st = interp["stairs"]
    write("E1_1_STAIR_COMPLETENESS_REGISTER.json", {
        "source": source,
        "STAIR_TYPES": list(stc.STAIR_TYPES),
        "never_silently_absent": st["never_silently_absent"],
        "no_riser_without_a_section": st["no_riser_without_a_section"],
        "by_type": st["by_type"],
        "detected": st["detected"],
        "explicitly_unresolved": st["explicitly_unresolved"],
        "frozen_parameters": stc.frozen_parameters(),
        "assemblies": [x.record() for x in st["assemblies"]],
    })
    write("E1_1_STAIR_REGISTER.json", {
        "source": source,
        "note": ("the same assemblies as the completeness register, kept "
                 "under E1's register name so the two iterations line up"),
        "assemblies": [x.record() for x in st["assemblies"]],
        "count": st["count"],
    })

    # --- the E1 registers, updated ---------------------------------------
    write("E1_1_CAD_GEOMETRY_REGISTER.json", {
        "source": source,
        "three_geometries_kept_apart": {
            "MATERIAL_GEOMETRY": "walls, columns, glazing, curved faces",
            "SPACE_TOPOLOGY": "virtual portal boundaries, carrying no "
                              "material",
            "FUNCTIONAL_TRADE_BOUNDARY": "NOT_DECIDED_IN_E1_1"},
        "unit_of_work": ("ONE TRACE PER FUNCTIONAL IDENTITY, seeded from "
                         "where the label is SEEN, not from a raw text "
                         "insertion point"),
        "outcome_counts": {o: sum(1 for r in rows
                                  if r["region"].outcome == o)
                           for o in er.OUTCOMES},
        "released_regions": len(released),
        "withheld_regions": len(withheld),
        "regions": [{**r["region"].record(),
                     "LABEL_GROUP": r["group"].group_id,
                     "seeded_from": lg.VISIBLE_LABEL_CENTROID,
                     "seed_mm": [round(r["seed"][0], 2),
                                 round(r["seed"][1], 2)],
                     "RELEASE_DECISION": r["decision"],
                     "A18_ALIGNMENT": r["alignment"],
                     "VISUAL_QA": {k: v for k, v in r["visual"].items()
                                   if k != "dimension_cross_check"},
                     "OVERLAP_RELATIONS": r["overlaps"]}
                    for r in rows],
        "frozen_parameters": {"cad_geometry": cg.frozen_parameters(),
                              "e1_region": er.frozen_parameters(),
                              "cad_entity_role": cer.frozen_parameters(),
                              "curve_semantics": cs.frozen_parameters(),
                              "e1_release": rel.frozen_parameters()},
        "E1_1_decides_no_trade_zone": (
            "SAME_TRADE_CATEGORY, SAME_FINISH and SAME_MEASUREMENT_ZONE are "
            "not decided here, and no region was merged for sharing a "
            "finish or split because its name differed"),
    })

    write("E1_1_CAD_ENTITY_PROVENANCE.json", {
        "source": source,
        "layer_roles": prep["layer_roles"],
        "layer_default_is_not_an_invariant":
            cer.A_LAYER_IS_CANDIDATE_GENERATION_ONLY,
        "entity_established_roles_are_in":
            "E1_1_ENTITY_ROLE_REGISTER.json",
        "entities_by_region": {
            "ground_floor_primitives": len(gf["primitives"]),
            "offered_to_the_tracer": len(mat["primitives"]),
            "by_layer": {L: sum(1 for p in gf["primitives"]
                                if p.provenance.layer == L)
                         for L in sorted({p.provenance.layer
                                          for p in gf["primitives"]})}},
        "cad_stamps": [s.record() for s in interp["labels"]["stamps"]],
    })

    write("E1_1_A18_CAD_ALIGNMENT_REGISTER.json", {
        "source": source,
        "confirmed_must_name_its_subject": rel.CONFIRMED_MUST_NAME_ITS_SUBJECT,
        "ALIGNMENT_STATUSES": list(rel.ALIGNMENT_STATUSES),
        "corroboration_language": er.corroboration(
            source_families=["DESIGN_SOURCE_FAMILY",
                             "DESIGN_SOURCE_FAMILY"]),
        "status_counts": {s: sum(1 for r in rows
                                 if s in r["alignment"]
                                 ["A18_ALIGNMENT_STATUS"])
                          for s in rel.ALIGNMENT_STATUSES},
        "rows": [{"CAD_GEOMETRY_ID": r["region"].cad_geometry_id,
                  "LABEL_GROUP": r["group"].group_id,
                  "identity": r["group"].english_token,
                  "A18_CANDIDATE_ID": r["region"].a18_candidate_id or None,
                  "E1_1_OUTCOME": r["region"].outcome,
                  "RELEASED": r["region"].released,
                  **r["alignment"]} for r in rows],
    })

    write("E1_1_COMPLETENESS_REGISTER.json", {
        "source": source,
        "method": ("one trace per functional identity, every identity "
                   "treated the same way, and every frozen A18 ground-floor "
                   "hypothesis joined by its English token"),
        "a18_candidates_considered": len(cand),
        "functional_identities": len(rows),
        "label_groups": len(interp["labels"]["groups"]),
        "A18_CANDIDATE_WITH_NO_CAD_IDENTITY": sorted(
            {c["candidate_id"] for tok, cs_ in a18_by_token.items()
             for c in cs_
             if tok not in {r["group"].english_token for r in rows}}
            | {c["candidate_id"] for c in cand
               if not _english_token(c.get("label_as_drawn", ""))}),
        "CAD_IDENTITY_WITH_NO_A18_CANDIDATE": sorted(
            r["group"].english_token for r in rows if not r["a18"]),
        "ONE_A18_IDENTITY_SEVERAL_CAD_STAMPS": {
            g.english_token: [m.stamp_id for m in g.members]
            for g in interp["labels"]["groups"]
            if g.english_token and len(g.members) > 1},
    })

    write("E1_1_BOUNDARY_ROLE_REGISTER.json", {
        "roles": list(cg.ROLES),
        "material_roles": list(cg.MATERIAL_ROLES),
        "topology_only_roles": list(cg.TOPOLOGY_ONLY_ROLES),
        "entity_roles": list(cer.ENTITY_ROLES),
        "entity_roles_that_may_bound_material": list(cer.MAY_BOUND_MATERIAL),
        "a_virtual_boundary_is_not_wall_material":
            cg.A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL,
        "length_by_role_over_released_regions": {
            role: round(sum(s.length_mm for r in released
                            for s in r["region"].boundary.segments
                            if s.role == role), 3) for role in cg.ROLES},
        "material_length_mm_over_released_regions": round(sum(
            r["region"].boundary.material_length_mm for r in released), 3),
        "topology_only_length_mm_over_released_regions": round(sum(
            r["region"].boundary.topology_only_length_mm
            for r in released), 3),
    })

    write("E1_1_PORTAL_AND_OPEN_EDGE_REGISTER.json", {
        "source": source,
        "rule": result["closure"]["rule"],
        "offered_only_established_material_geometry": True,
        "dangling_wall_ends": result["closure"]["dangling_wall_ends"],
        "collinear_candidate_pairs":
            result["closure"]["collinear_candidate_pairs"],
        "pairs_rejected_not_collinear":
            result["closure"]["pairs_rejected_not_collinear"],
        "junction_repairs": result["closure"]["junction_repairs"],
        "portals_or_openings": result["closure"]["openings"],
        "rows": result["closure"]["rows"],
        "an_open_edge_is_a_result": (
            "where CAD establishes an open connection the edge stays open. "
            "No wall was created and no portal was inserted without "
            "opening evidence"),
    })

    curved = [(r, s) for r in rows if r["region"].boundary is not None
              for s in r["region"].boundary.segments
              if s.kind in (cg.ARC, cg.CIRCLE)]
    write("E1_1_CURVE_PRESERVATION_REGISTER.json", {
        "source_arcs": source["arcs"],
        "source_circles": source["circles"],
        "curve_support_is_unchanged": cs.WHY_CURVE_SUPPORT_IS_NOT_THE_PROBLEM,
        "CURVE_SEMANTICS": list(cs.CURVE_SEMANTICS),
        "curve_semantic_counts": interp["curves"]["counts"],
        "round_objects": [o.record() for o in
                          interp["curves"]["round_objects"]
                          if len(o.radii_mm) >= 2
                          or o.radial_line_ids],
        "curved_segments_in_e1_1_boundaries": len(curved),
        "rows": [{"CAD_GEOMETRY_ID": r["region"].cad_geometry_id,
                  "entity": s.record()["entity"],
                  "centre_mm": [s.cx, s.cy], "radius_mm": s.radius,
                  "start_angle_rad": s.start_angle,
                  "end_angle_rad": s.end_angle,
                  "direction": "CCW" if s.ccw else "CW",
                  "curve_semantic": (interp["curves"]["curve_roles"]
                                     .get(s.object_id, {})
                                     .get("curve_semantic")),
                  "analytical_geometry": "THE_ORIGINAL_CURVE",
                  "tessellation": cg.RENDERING_ONLY}
                 for r, s in curved],
        "no_chord_became_measurement_geometry": True,
    })

    write("E1_1_WITHHELD_GEOMETRY_REGISTER.json", {
        "rule": rel.OTHERWISE_WITHHOLD,
        "withheld": len(withheld),
        "by_outcome": {o: sum(1 for r in withheld
                              if r["region"].outcome == o)
                       for o in er.OUTCOMES},
        "by_failed_condition": {c: sum(1 for r in withheld
                                       if c in r["decision"]["failed"])
                                for c in rel.RELEASE_CONDITIONS},
        "rows": [{"CAD_GEOMETRY_ID": r["region"].cad_geometry_id,
                  "identity": r["group"].english_token,
                  "OUTCOME": r["region"].outcome,
                  "failed_release_conditions": r["decision"]["failed"],
                  "VISUAL_QA_STATE": r["visual"]["VISUAL_QA_STATE"],
                  "A18_ALIGNMENT_STATUS":
                      r["alignment"]["A18_ALIGNMENT_STATUS"],
                  "why": r["region"].why} for r in withheld],
        "success_is_not_closure": (
            "E1.1 does not need every functional label to have a closed "
            "polygon. Withholding is the correct outcome when an entity "
            "role, an overlap, a topology conflict or the sheet itself "
            "contradicts the candidate"),
    })

    # --- §M the delta -----------------------------------------------------
    write("E1_1_DELTA_FROM_E1_V1.json",
          delta_from_e1_v1(result, interp, gf, a.prior_e1))

    # --- overlays ---------------------------------------------------------
    overlay = whole_floor_overlay(
        sheet, reg, gf, interp, result,
        out / "E1_1_GROUND_FLOOR_ON_THE_SOURCE_SHEET.png")
    if overlay:
        artifacts["E1_1_GROUND_FLOOR_ON_THE_SOURCE_SHEET.png"] = \
            overlay[prov.RAW]
    locals_ = candidate_overlays(sheet, reg, gf, interp, result,
                                 out / "local_overlays")
    for row in locals_:
        artifacts[f"local_overlays/{row['file']}"] = row[prov.RAW]
    write("E1_1_OVERLAY_INDEX.json", {
        "whole_floor": overlay,
        "local_overlays": locals_,
        "drawn_on": "THE_ORIGINAL_SOURCE_SHEET",
        "every_candidate_has_an_overlay_before_release": True,
        "corroboration_kind": rq.CROSS_REPRESENTATION_CORROBORATION,
        "never_independent_source_truth": rq.NEVER_INDEPENDENT_SOURCE_TRUTH,
    })

    man = dict(seal["manifest"])
    (out / "E1_1_INPUT_MANIFEST.json").write_text(
        json.dumps(man, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")
    artifacts["E1_1_INPUT_MANIFEST.json"] = _sha(
        out / "E1_1_INPUT_MANIFEST.json")

    freeze = {
        "E1_1_MODEL": E1_1_MODEL,
        "RUN_ID": RUN_ID,
        "E1_1_RUN_CLASS": CONTROLLED_INTEGRATION_REGRESSION,
        "supersedes_nothing": (
            "E1 v1 is preserved exactly as frozen. This is a separate "
            "iteration in its own directory and overwrites none of it"),
        "why_controlled_integration_regression": (
            "E1.1 stands on geometry modules developed in rounds 6 to 6E, "
            "which were explicitly benchmark-informed, and it was written "
            "after an external review named four failures. It opened no "
            "benchmark and was tuned to no expected number, and it does "
            "not claim blind validation"),
        "E1_1_CURRENT_RUN_BENCHMARK_INPUTS": "NONE",
        "what_the_external_review_supplied": (
            "four named geometry and semantic failures, and no quantity. "
            "No expected area, target dimension or benchmark number "
            "entered this run, and no threshold here was chosen to make a "
            "particular number come out"),
        "modules_written_for_E1_1": list(E1_1_NEW_MODULES),
        "modules_carried_forward_from_E1_unchanged":
            list(E1_MODULES_CARRIED_FORWARD),
        "modules_with_benchmark_informed_lineage":
            list(BENCHMARK_INFORMED_LINEAGE),
        "SOURCE_HASHES": {
            "cad_decode": source["decode_sha256"],
            "NORMALIZATION_HASH": source["NORMALIZATION_HASH"],
            "source_sheet": _sha(a.raster) if Path(a.raster).exists() else "",
            "a18_pass_d_candidates": _sha(
                Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json"),
            "e1_v1_alignment_register": _sha(
                Path(a.prior_e1) / "E1_A18_CAD_ALIGNMENT_REGISTER.json"),
        },
        "CODE_VERSION_HASHES": code_hashes(),
        "MODEL_HASHES": {"cad_geometry": cg.model_hash(),
                         "e1_region": er.model_hash(),
                         "cad_entity_role": cer.model_hash(),
                         "curve_semantics": cs.model_hash(),
                         "label_grouping": lg.model_hash(),
                         "raster_qa": rq.model_hash(),
                         "e1_release": rel.model_hash(),
                         "stair_completeness": stc.model_hash(),
                         "e1_1_inputs": ei.model_hash()},
        "SANDBOX_EQUALITY": seal["report"],
        "ARTIFACTS": artifacts,
        "COUNTS": {
            "functional_identities": len(rows),
            "released": len(released),
            "withheld": len(withheld),
            "entities": interp["roles"]["entities"],
            "entities_that_may_bound_material":
                interp["roles"]["may_bound_material"],
            "stairs_detected": st["detected"],
            "stairs_explicitly_unresolved": st["explicitly_unresolved"],
        },
        "what_E1_1_did_not_do": [
            "no benchmark, Excel, reconciliation, manual take-off, "
            "corrected area or external grading was opened",
            "no area was compared with anything, in either direction",
            "no trade or measurement zone was decided",
            "no quantity was computed",
            "no geometry was repaired to make a region close",
            "E1 v1 was not modified, rerun or overwritten",
        ],
    }
    freeze["E1_1_RUN_HASH"] = prov.canonical_sha256(freeze)
    (out / "E1_1_FREEZE.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")

    print(json.dumps({
        "sandbox": seal["report"]["status"],
        "raster_registration": (reg.established if reg else False),
        "label_groups": interp["labels"]["group_counts"],
        "entity_roles": interp["roles"]["counts"],
        "curve_semantics": interp["curves"]["counts"],
        "stairs": st["by_type"],
        "outcomes": {o: sum(1 for r in rows if r["region"].outcome == o)
                     for o in er.OUTCOMES},
        "visual": {s: sum(1 for r in rows
                          if s in r["visual"]["VISUAL_QA_STATE"])
                   for s in rel.VISUAL_QA_STATES},
        "released": len(released),
        "withheld": len(withheld),
        "overlaps": {k: sum(1 for o in result["overlaps"]
                            if o["relation"] == k)
                     for k in rel.OVERLAP_RELATIONS},
        "artifacts": len(artifacts) + 1,
        "E1_1_RUN_HASH": freeze["E1_1_RUN_HASH"][:16],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
