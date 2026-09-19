"""E1 — align the frozen A18 reading to exact CAD geometry, then freeze.

    python -m tools.run_e1 --out data/runs/7757/e1 \
        --sandbox <dir> --decode <cad decode>.json

A18 says WHAT to look for. CAD says WHERE, exactly, and owns the
geometry. This runner never decides a functional or trade boundary, never
computes a quantity to compare with anything, and is allowed to come back
with OPEN, PARTIAL, MULTI_FUNCTION, NO_UNIQUE or UNRESOLVED rather than a
polygon. A withheld result is better than a false closed room.

Three geometries stay apart end to end: built material, the topology that
lets two spaces be two spaces, and functional/trade - which is not E1's
business and is not invented here.
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
from engine import cad_geometry as cg
from engine import cad_profile as cprofile
from engine import drawing_region as dreg
from engine import e1_inputs as ei
from engine import e1_region as er
from engine import export_provenance as prov

E1_MODEL = "E1_CAD_PHYSICAL_GEOMETRY_ALIGNMENT_V1"

# Which of this source's layers carry wall-like geometry, and how sure.
# A LAYER DEFAULT IS NOT AN INVARIANT: the profile proposes a role from
# what the layer holds HERE, and the register keeps the default separate
# from anything an entity establishes.
PAIRED_SHARE_WALL_LIKE = 0.45

CONTROLLED_INTEGRATION_REGRESSION = "CONTROLLED_INTEGRATION_REGRESSION"

# Modules written for E1, after the benchmark protection was in force and
# with no benchmark in view.
E1_NEW_MODULES = ("engine/cad_geometry.py", "engine/e1_region.py",
                  "engine/e1_inputs.py", "tools/run_e1.py")
# Modules E1 stands on that were developed while benchmark figures were
# visible (rounds 6 to 6E were explicitly benchmark-informed).
BENCHMARK_INFORMED_LINEAGE = (
    "engine/cad_adapter.py", "engine/cad_profile.py",
    "engine/cad_regions.py", "engine/drawing_region.py")


def _sha(path) -> str:
    return prov.raw_sha256(path)


def _english(label: str) -> str:
    """The English token of a bilingual stamp, for joining on identity."""
    for part in reversed(str(label or "").split("/")):
        tok = re.sub(r"[^A-Za-z. ]", "", part).strip()
        if len(tok) >= 3:
            return tok.upper()
    return ""


def layer_roles(profile) -> dict:
    """LAYER_DEFAULT_ROLE, with evidence and confidence. Not an invariant."""
    out = {}
    for lay in profile.layers:
        paired = lay.paired_share
        wall_like = paired >= PAIRED_SHARE_WALL_LIKE
        if lay.proposed_role == "DIMENSION_BEARING":
            default, conf = cg.DIMENSION_WITNESS, "MEDIUM"
        elif wall_like:
            default, conf = cg.MATERIAL_WALL_FACE, (
                "HIGH" if paired >= 0.6 else "MEDIUM")
        elif lay.total_length_mm < 100.0:
            default, conf = cg.ANNOTATION_ONLY, "LOW"
        else:
            default, conf = cg.ROLE_UNRESOLVED, "LOW"
        out[lay.layer] = {
            "source_layer": lay.layer,
            "LAYER_DEFAULT_ROLE": default,
            "confidence": conf,
            "ENTITY_ESTABLISHED_ROLE": "NOT_ESTABLISHED_PER_ENTITY",
            "evidence": {
                "entities": lay.entities,
                "total_length_m": round(lay.total_length_mm / 1000, 2),
                "paired_share": paired,
                "face_separations_mm": [round(t, 1)
                                        for t in lay.thicknesses_mm[:8]],
                "profile_proposed_role": lay.proposed_role,
                "profile_status": lay.status,
            },
            "scope": ("a DEFAULT proposed from what this layer holds in "
                      "THIS source. Paired-face separation is evidence of "
                      "wall-like geometry, not proof that every pair is a "
                      "physical wall, and no claim is made that a layer of "
                      "this name can never be a wall in another drawing"),
        }
    return out


def prepare(decode_path) -> dict:
    decode = json.loads(Path(decode_path).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    profile = cprofile.build(nd)
    regions = dreg.isolate(nd)
    roles = layer_roles(profile)
    wall_layers = {k for k, v in roles.items()
                   if v["LAYER_DEFAULT_ROLE"] in (cg.MATERIAL_WALL_FACE,
                                                  cg.CURVED_MATERIAL_FACE)}
    return {"nd": nd, "profile": profile, "regions": regions,
            "layer_roles": roles, "wall_layers": wall_layers}


def ground_floor(prep, *, region_id="DR-002") -> dict:
    region = [r for r in prep["regions"].regions
              if r.region_id == region_id][0]
    nd = prep["nd"]
    prims = [p for p in nd.primitives if region.holds(p.object_id)]
    stamps = [t for t in nd.texts if region.contains(t.x, t.y)]
    return {"region": region, "primitives": prims, "stamps": stamps}


def stamp_rows(stamps) -> list:
    """CAD room stamps, with the English token used to join identity."""
    rows = []
    for t in stamps:
        tok = _english(t.value)
        if not tok or tok in ("NEIGHBOUR", "STREET", "SEA VIEW"):
            continue
        if t.value.startswith("%%") or not t.value.isascii():
            continue
        rows.append({"stamp_id": f"STAMP-{len(rows) + 1:03d}",
                     "text": t.value, "english_token": tok,
                     "at_mm": [round(t.x, 2), round(t.y, 2)],
                     "layer": t.provenance.layer,
                     "dwg_handle": t.provenance.handle})
    return rows


def align(gf, prep, a18_candidates) -> dict:
    """Every A18 candidate and every CAD stamp, by the same method.

    Uniformly: no candidate gets extra attention because a later pass
    challenged it, and none is preserved merely because it polygonized.
    """
    prims, region = gf["primitives"], gf["region"]
    wall = prep["wall_layers"]
    role_of = {L: cg.MATERIAL_WALL_FACE for L in wall}
    closure = cg.close_openings(prims, wall_layers=wall,
                               door_layers={"D"})
    barriers = closure["barriers"]
    stamps = stamp_rows(gf["stamps"])
    by_token = {}
    for row in stamps:
        by_token.setdefault(row["english_token"], []).append(row)

    # Every A18 ground-floor hypothesis, by its English identity.
    a18_by_token = {}
    for cand in a18_candidates:
        tok = _english(cand.get("label_as_drawn", ""))
        if tok:
            a18_by_token.setdefault(tok, []).append(cand)

    site_area = None
    regions, alignment = [], []
    released_boundaries = []

    def trace_at(seed):
        return cg.trace(seed, prims, wall_layers=wall,
                        tol_mm=cg.DENSIFY_TOL_MM, role_of=role_of,
                        extra_segments=barriers)

    # --- pass 1: each CAD stamp is traced, once, the same way -----------
    traced = {}
    for row in stamps:
        out = trace_at(tuple(row["at_mm"]))
        traced[row["stamp_id"]] = out
        if out.get("candidates"):
            area = out["candidates"][0]["densified_area_m2_rendering_only"]
            site_area = max(site_area or 0.0, area)

    # --- pass 2: an outcome per stamp, from evidence --------------------
    for row in stamps:
        out = traced[row["stamp_id"]]
        tok = row["english_token"]
        inside = ()
        if out.get("candidates"):
            from shapely.geometry import Polygon, Point
            try:
                poly = Polygon(out["candidates"][0]["boundary"].points())
                inside = tuple(
                    o["english_token"] for o in stamps
                    if poly.is_valid
                    and poly.contains(Point(o["at_mm"][0], o["at_mm"][1])))
            except Exception:
                inside = (tok,)
        a18_hits = a18_by_token.get(tok, [])
        reg = er.assess(
            cad_geometry_id=f"E1-{row['stamp_id']}",
            a18_candidate_id=",".join(c["candidate_id"] for c in a18_hits),
            drawing_id="P7757_ARCHITECTURAL.dwg",
            floor="GROUND", label=tok, trace_result=out,
            labels_in_face=inside, a18_identity=bool(a18_hits))
        reg = er.validate(reg, released_boundaries=released_boundaries,
                          site_area_m2=site_area)
        if reg.released and reg.boundary is not None:
            released_boundaries.append(reg.boundary)
        regions.append(reg)

        if not a18_hits:
            status = "CAD_REGION_WITH_NO_A18_CANDIDATE"
        elif reg.outcome == er.CLOSED_PHYSICAL_REGION:
            status = "CONFIRMED_BY_CAD"
        elif reg.outcome == er.MULTI_FUNCTION_PHYSICAL_REGION:
            status = "MERGED_BY_CAD"
        elif reg.outcome == er.NO_UNIQUE_PHYSICAL_REGION:
            status = "A18_IDENTITY_ONLY_GEOMETRY_INDEPENDENT"
        elif reg.outcome in (er.OPEN_PHYSICAL_REGION,
                             er.PARTIAL_BOUNDARY_CHAIN):
            status = "RESHAPED_BY_CAD"
        else:
            status = "UNRESOLVED"
        alignment.append({
            "CAD_GEOMETRY_ID": reg.cad_geometry_id,
            "A18_CANDIDATE_ID": reg.a18_candidate_id or None,
            "DRAWING_ID": reg.drawing_id,
            "FLOOR": reg.floor,
            "cad_stamp": row,
            "A18_ALIGNMENT_STATUS": status,
            "E1_OUTCOME": reg.outcome,
            "RELEASED": reg.released,
            "corroboration": er.corroboration(
                source_families=["DESIGN_SOURCE_FAMILY",
                                 "DESIGN_SOURCE_FAMILY"]),
            "why": reg.why,
        })

    # --- completeness ---------------------------------------------------
    cad_tokens = set(by_token)
    a18_tokens = set(a18_by_token)
    completeness = {
        "A18_CANDIDATE_WITH_NO_CAD_MATCH": sorted(
            {c["candidate_id"] for tok in (a18_tokens - cad_tokens)
             for c in a18_by_token[tok]}
            | {c["candidate_id"] for c in a18_candidates
               if not _english(c.get("label_as_drawn", ""))}),
        "CAD_REGION_WITH_NO_A18_CANDIDATE": sorted(
            f"{r['stamp_id']}:{r['english_token']}" for r in stamps
            if r["english_token"] not in a18_tokens),
        "MULTIPLE_A18_CANDIDATES_ONE_CAD_REGION": {
            tok: [c["candidate_id"] for c in cands]
            for tok, cands in a18_by_token.items()
            if len(cands) > 1 and len(by_token.get(tok, [])) == 1},
        "ONE_A18_CANDIDATE_MULTIPLE_CAD_REGIONS": {
            tok: [r["stamp_id"] for r in rows]
            for tok, rows in by_token.items()
            if len(rows) > 1 and len(a18_by_token.get(tok, [])) == 1},
    }
    return {"closure": closure, "stamps": stamps, "regions": regions,
            "alignment": alignment, "completeness": completeness,
            "site_area_m2_rendering_only": site_area,
            "traced": traced, "barriers": barriers}


# --------------------------------------------------------------- stairs

TREAD_PITCH_MIN_MM = 220.0
TREAD_PITCH_MAX_MM = 350.0
MIN_TREADS = 3


def stairs(gf, prep) -> dict:
    """Stair assemblies as assemblies, from the treads CAD actually holds.

    A stair is not the rectangle the cut plane draws round it. What can be
    established here is a run of parallel, evenly pitched lines of similar
    length - treads - and the flight they form. Rise, riser and landing
    role need a section, and solid-versus-dashed needs a linetype the
    normalised CAD does not carry, so those are recorded as not
    established rather than guessed.
    """
    prims = [p for p in gf["primitives"] if p.kind == "SEGMENT"]
    by_axis = {"H": [], "V": []}
    for p in prims:
        if p.axis in ("H", "V"):
            by_axis[p.axis].append(p)

    flights = []
    for axis, items in by_axis.items():
        rows = {}
        for p in items:
            fixed = round(p.y1 if axis == "H" else p.x1, 1)
            lo, hi = sorted((p.x1, p.x2) if axis == "H" else (p.y1, p.y2))
            rows.setdefault(round(hi - lo, 0), []).append((fixed, lo, hi, p))
        for width, group in rows.items():
            if width < 600 or len(group) < MIN_TREADS:
                continue
            group.sort(key=lambda r: (r[0], r[1], r[2]))
            run, prev = [], None
            for fixed, lo, hi, p in group:
                if prev is None or TREAD_PITCH_MIN_MM <= abs(
                        fixed - prev) <= TREAD_PITCH_MAX_MM:
                    run.append((fixed, lo, hi, p))
                else:
                    if len(run) >= MIN_TREADS:
                        flights.append((axis, width, list(run)))
                    run = [(fixed, lo, hi, p)]
                prev = fixed
            if len(run) >= MIN_TREADS:
                flights.append((axis, width, list(run)))

    out = []
    for n, (axis, width, run) in enumerate(sorted(
            flights, key=lambda f: -len(f[2]))[:12], start=1):
        pitches = [round(abs(run[i + 1][0] - run[i][0]), 2)
                   for i in range(len(run) - 1)]
        out.append({
            "STAIR_ASSEMBLY": f"E1-STAIR-{n:02d}",
            "STAIR_FLIGHT": [{
                "flight_id": f"E1-STAIR-{n:02d}-F1",
                "axis": axis,
                "TREAD": [{
                    "tread_id": f"E1-STAIR-{n:02d}-T{i + 1:02d}",
                    "entity": p.provenance.record(),
                    "line_mm": [round(p.x1, 3), round(p.y1, 3),
                                round(p.x2, 3), round(p.y2, 3)],
                    "width_mm": round(hi - lo, 2),
                } for i, (fixed, lo, hi, p) in enumerate(run)],
                "tread_count": len(run),
                "pitches_mm": pitches,
                "RISER": "NOT_ESTABLISHED_IN_E1_A_RISER_NEEDS_A_SECTION",
                "LANDING": "NOT_ESTABLISHED_IN_E1",
            }],
            "SOLID_VISIBLE_GEOMETRY": "NOT_DISTINGUISHED",
            "DASHED_BEYOND_CUT_PLANE": "NOT_DISTINGUISHED",
            "CUT_PLANE": "NOT_DISTINGUISHED",
            "why_solid_and_dashed_are_not_distinguished": (
                "the normalised CAD carries handle, entity type, layer and "
                "block lineage, but not linetype, so visible-versus-beyond "
                "cannot be established from it. It is recorded as not "
                "established rather than assumed"),
            "OPENING_OR_VOID": "NOT_ESTABLISHED_IN_E1",
            "not_a_flooring_zone": (
                "a closed stair polygon is not a flooring measurement "
                "zone, and E1 computes no marble"),
        })
    return {"assemblies": out, "count": len(out),
            "rule": {"TREAD_PITCH_MIN_MM": TREAD_PITCH_MIN_MM,
                     "TREAD_PITCH_MAX_MM": TREAD_PITCH_MAX_MM,
                     "MIN_TREADS": MIN_TREADS,
                     "scope": "GENERAL geometry, not a project dimension"}}


# -------------------------------------------------------------- overlays

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


def _project(extent, size, pad=40):
    x0, y0, x1, y1 = extent
    w, h = size
    sx = (w - 2 * pad) / max(1e-9, x1 - x0)
    sy = (h - 2 * pad) / max(1e-9, y1 - y0)
    s = min(sx, sy)

    def to_px(x, y):
        return (pad + (x - x0) * s, h - pad - (y - y0) * s)
    return to_px, s


def _draw_segment(draw, seg, to_px, *, width=None, colour=None):
    col, wid, _name = TREATMENT.get(seg.role, TREATMENT[cg.ROLE_UNRESOLVED])
    col = colour or col
    wid = width or wid
    pts = [to_px(x, y) for x, y in seg.points(tol_mm=cg.DENSIFY_TOL_MM)]
    if len(pts) < 2:
        return
    if seg.role in DASHED_ROLES:
        for i in range(0, len(pts) - 1, 2):
            draw.line([pts[i], pts[i + 1]], fill=col, width=wid)
        if len(pts) == 2:                      # a single dash reads solid
            (ax, ay), (bx, by) = pts
            n = 9
            for i in range(0, n, 2):
                draw.line([(ax + (bx - ax) * i / n, ay + (by - ay) * i / n),
                           (ax + (bx - ax) * (i + 1) / n,
                            ay + (by - ay) * (i + 1) / n)],
                          fill=col, width=wid)
    else:
        draw.line(pts, fill=col, width=wid)


def whole_floor_overlay(gf, prep, result, out_path) -> dict:
    """Every established boundary on the drawing, by role, so artificial
    topology inside an apparently closed polygon is visible at a glance."""
    from PIL import Image, ImageDraw, ImageFont
    region = gf["region"]
    extent = (region.x0, region.y0, region.x1, region.y1)
    size = (4200, 3000)
    img = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    to_px, scale = _project(extent, size)

    # the drawing's own wall-role linework, faint, as context
    for p in gf["primitives"]:
        if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
            continue
        if p.provenance.layer not in prep["wall_layers"]:
            continue
        seg = cg._as_segment(p)
        pts = [to_px(x, y) for x, y in seg.points(tol_mm=cg.DENSIFY_TOL_MM)]
        if len(pts) >= 2:
            draw.line(pts, fill=(205, 205, 205), width=1)

    drawn = {}
    for reg in result["regions"]:
        if reg.boundary is None:
            continue
        for seg in reg.boundary.segments:
            _draw_segment(draw, seg, to_px)
            drawn[seg.role] = drawn.get(seg.role, 0) + 1
    for bar in result["barriers"]:
        _draw_segment(draw, bar, to_px)
        drawn[bar.role] = drawn.get(bar.role, 0) + 1

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    y = 20
    draw.text((20, y), "E1 GROUND FLOOR — CAD PHYSICAL GEOMETRY",
              font=ImageFont.truetype(
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  34), fill=(20, 20, 20))
    y += 52
    for role, (col, wid, name) in TREATMENT.items():
        draw.line([(24, y + 12), (96, y + 12)], fill=col, width=max(3, wid))
        draw.text((110, y), f"{role}  ({name})  n={drawn.get(role, 0)}",
                  font=font, fill=(50, 50, 50))
        y += 34
    draw.text((20, y + 8),
              "dashed = nothing was built along it; a closed-looking "
              "polygon with orange or red in its ring is not closed by "
              "material", font=font, fill=(150, 40, 40))
    img.save(out_path)
    return {"file": Path(out_path).name, "pixels": list(size),
            "mm_per_pixel": round(1.0 / scale, 4),
            "segments_drawn_by_role": drawn,
            "legend": {k: v[2] for k, v in TREATMENT.items()},
            "context_linework": "the wall-role CAD lines, faint grey",
            prov.RAW: _sha(out_path)}


def local_overlays(gf, prep, result, out_dir) -> list:
    """One overlay per region that changed A18's shape or stayed open."""
    from PIL import Image, ImageDraw, ImageFont
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    want = {"RESHAPED_BY_CAD", "MERGED_BY_CAD", "UNRESOLVED",
            "A18_IDENTITY_ONLY_GEOMETRY_INDEPENDENT",
            "CAD_REGION_WITH_NO_A18_CANDIDATE"}
    rows = []
    by_id = {r.cad_geometry_id: r for r in result["regions"]}
    for row in result["alignment"]:
        if row["A18_ALIGNMENT_STATUS"] not in want:
            continue
        reg = by_id[row["CAD_GEOMETRY_ID"]]
        at = row["cad_stamp"]["at_mm"]
        half = 6000.0
        extent = (at[0] - half, at[1] - half, at[0] + half, at[1] + half)
        size = (1600, 1600)
        img = Image.new("RGB", size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        to_px, scale = _project(extent, size)
        for p in gf["primitives"]:
            if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
                continue
            if p.provenance.layer not in prep["wall_layers"]:
                continue
            seg = cg._as_segment(p)
            pts = [to_px(x, y) for x, y in seg.points(
                tol_mm=cg.DENSIFY_TOL_MM)]
            if len(pts) >= 2:
                draw.line(pts, fill=(200, 200, 200), width=2)
        if reg.boundary is not None:
            for seg in reg.boundary.segments:
                _draw_segment(draw, seg, to_px)
        for bar in result["barriers"]:
            mx = (bar.x1 + bar.x2) / 2.0
            my = (bar.y1 + bar.y2) / 2.0
            if abs(mx - at[0]) <= half and abs(my - at[1]) <= half:
                _draw_segment(draw, bar, to_px)
        px, py = to_px(at[0], at[1])
        draw.ellipse([px - 10, py - 10, px + 10, py + 10],
                     outline=(0, 0, 220), width=4)
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
        draw.text((16, 14), f"{row['CAD_GEOMETRY_ID']}  "
                            f"{row['cad_stamp']['english_token']}",
                  font=font, fill=(20, 20, 20))
        draw.text((16, 46), f"{row['A18_ALIGNMENT_STATUS']} / "
                            f"{row['E1_OUTCOME']}", font=font,
                  fill=(150, 40, 40))
        draw.text((16, 78), "blue ring = the CAD stamp this was traced "
                            "from", font=font, fill=(60, 60, 60))
        name = f"E1_LOCAL_{row['CAD_GEOMETRY_ID']}.png"
        img.save(out_dir / name)
        rows.append({"file": name,
                     "CAD_GEOMETRY_ID": row["CAD_GEOMETRY_ID"],
                     "status": row["A18_ALIGNMENT_STATUS"],
                     "outcome": row["E1_OUTCOME"],
                     prov.RAW: _sha(out_dir / name)})
    return rows


# ------------------------------------------------------------- the freeze

def build_sandbox(root, *, decode, a18_dir, rules) -> dict:
    """Admitted inputs only, and the sandbox must equal the manifest."""
    run = ei.E1Run(run_id="E1-P7757-GF-001",
                   subject="E1 CAD physical geometry alignment",
                   floor="GROUND")
    run.notes["why_E1_is_not_blind"] = ei.WHY_E1_IS_NOT_BLIND
    box = sbx.Sandbox(root=Path(root), run=run, working_dirs=())
    a18 = Path(a18_dir)
    plan = [
        (ei.Input(input_id="CAD_DECODE", kind=ei.CAD_GEOMETRY_SOURCE,
                  what_it_is="the authoritative DWG-derived geometry",
                  path=str(decode)), "cad/P7757_ARCHITECTURAL.json"),
        (ei.Input(input_id="PASS_B_REGISTER", kind=ei.FROZEN_PASS_B,
                  what_it_is="frozen A18 Pass B semantic hypotheses",
                  path=str(a18 / "A18_VISUAL_ZONE_REGISTER.json")),
         "a18/A18_VISUAL_ZONE_REGISTER.json"),
        (ei.Input(input_id="PASS_D_CANDIDATES", kind=ei.FROZEN_PASS_D,
                  what_it_is="every frozen A18 ground-floor hypothesis",
                  path=str(a18 / "A18_PASS_D_CANDIDATES.json")),
         "a18/A18_PASS_D_CANDIDATES.json"),
        (ei.Input(input_id="PASS_D_CHALLENGES", kind=ei.FROZEN_PASS_D,
                  what_it_is="frozen Pass D challenge records",
                  path=str(a18 / "A18_PASS_D_FALSE_CONFIDENCE_REGISTER.json")),
         "a18/A18_PASS_D_FALSE_CONFIDENCE_REGISTER.json"),
        (ei.Input(input_id="PASS_C2_RECORD", kind=ei.FROZEN_PASS_C2,
                  what_it_is="frozen Pass C2 challenge record",
                  path=str(a18 / "A18-GF-001_PASS_C2.json")),
         "a18/A18-GF-001_PASS_C2.json"),
        (ei.Input(input_id="SUPERVISED_FLOORS", kind=ei.CAD_SOURCE_METADATA,
                  what_it_is="which drawing region is which floor",
                  path="data/registry/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
         "cad/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
    ]
    if rules:
        plan.append((ei.Input(
            input_id="GENERAL_RULES", kind=ei.GENERAL_GEOMETRY_RULE,
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
    for rel in list(E1_NEW_MODULES) + list(BENCHMARK_INFORMED_LINEAGE) + [
            "engine/blind_input_contract.py", "engine/agent_sandbox.py",
            "engine/benchmark_protection.py"]:
        p = Path(rel)
        if p.exists():
            out[rel] = _sha(p)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode",
                    default="data/runs/cad_convert/P7757_ARCHITECTURAL.json")
    ap.add_argument("--a18-dir",
                    default="data/runs/7757/blind/A18-GF-001")
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
                         rules=rules)
    prep = prepare(a.decode)
    gf = ground_floor(prep)
    cand = json.loads(
        (Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json").read_text(
            encoding="utf-8"))["candidates"]
    result = align(gf, prep, cand)
    st = stairs(gf, prep)

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
        body["E1_MODEL"] = E1_MODEL
        body["RUN_ID"] = "E1-P7757-GF-001"
        body[f"{name.split('.')[0]}_HASH"] = prov.canonical_sha256(body)
        path = out / name
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                                   default=str) + "\n", encoding="utf-8")
        artifacts[name] = _sha(path)
        return body

    released = [r for r in result["regions"] if r.released]
    write("E1_CAD_GEOMETRY_REGISTER.json", {
        "source": source,
        "three_geometries_kept_apart": {
            "MATERIAL_GEOMETRY": "walls, columns, glazing, curved faces",
            "SPACE_TOPOLOGY": ("virtual portal boundaries, which carry no "
                               "material"),
            "FUNCTIONAL_TRADE_BOUNDARY": "NOT_DECIDED_IN_E1"},
        "outcome_counts": {o: sum(1 for r in result["regions"]
                                  if r.outcome == o) for o in er.OUTCOMES},
        "released_regions": len(released),
        "regions": [r.record() for r in result["regions"]],
        "frozen_parameters": {"cad_geometry": cg.frozen_parameters(),
                              "e1_region": er.frozen_parameters()},
        "E1_decides_no_trade_zone": (
            "SAME_TRADE_CATEGORY, SAME_FINISH and SAME_MEASUREMENT_ZONE are "
            "not decided here, and no region was merged because it looked "
            "like the same finish or split because its name differed"),
    })
    write("E1_CAD_ENTITY_PROVENANCE.json", {
        "source": source,
        "layer_roles": prep["layer_roles"],
        "wall_role_layers_used": sorted(prep["wall_layers"]),
        "layer_default_is_not_an_invariant": (
            "LAYER_DEFAULT_ROLE is proposed from what a layer holds in "
            "THIS source. ENTITY_ESTABLISHED_ROLE is separate and is not "
            "claimed here"),
        "entities_by_region": {
            "ground_floor_primitives": len(gf["primitives"]),
            "by_layer": {L: sum(1 for p in gf["primitives"]
                                if p.provenance.layer == L)
                         for L in sorted({p.provenance.layer
                                          for p in gf["primitives"]})}},
        "cad_stamps": result["stamps"],
    })
    write("E1_A18_CAD_ALIGNMENT_REGISTER.json", {
        "source": source,
        "A18_tells_what_CAD_tells_where": (
            "A18 supplies identity. The boundary comes from CAD entities, "
            "and a seed inside a face never establishes ownership"),
        "corroboration_language": er.corroboration(
            source_families=["DESIGN_SOURCE_FAMILY",
                             "DESIGN_SOURCE_FAMILY"]),
        "rows": result["alignment"],
        "status_counts": {s: sum(1 for r in result["alignment"]
                                 if r["A18_ALIGNMENT_STATUS"] == s)
                          for s in sorted({r["A18_ALIGNMENT_STATUS"]
                                           for r in result["alignment"]})},
    })
    write("E1_COMPLETENESS_REGISTER.json", {
        "source": source,
        "method": ("every CAD stamp traced the same way, and every frozen "
                   "A18 ground-floor hypothesis joined by identity. No "
                   "candidate got extra attention for having been "
                   "challenged"),
        "a18_candidates_considered": len(cand),
        "cad_stamps_considered": len(result["stamps"]),
        **result["completeness"],
    })
    write("E1_BOUNDARY_ROLE_REGISTER.json", {
        "roles": list(cg.ROLES),
        "material_roles": list(cg.MATERIAL_ROLES),
        "topology_only_roles": list(cg.TOPOLOGY_ONLY_ROLES),
        "a_virtual_boundary_is_not_wall_material":
            cg.A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL,
        "length_by_role_over_released_regions": {
            role: round(sum(
                s.length_mm for r in released
                for s in r.boundary.segments if s.role == role), 3)
            for role in cg.ROLES},
        "material_length_mm_over_released_regions": round(sum(
            r.boundary.material_length_mm for r in released), 3),
        "topology_only_length_mm_over_released_regions": round(sum(
            r.boundary.topology_only_length_mm for r in released), 3),
    })
    write("E1_PORTAL_AND_OPEN_EDGE_REGISTER.json", {
        "source": source,
        "rule": result["closure"]["rule"],
        "dangling_wall_ends": result["closure"]["dangling_wall_ends"],
        "collinear_candidate_pairs":
            result["closure"]["collinear_candidate_pairs"],
        "pairs_rejected_not_collinear":
            result["closure"]["pairs_rejected_not_collinear"],
        "junction_repairs": result["closure"]["junction_repairs"],
        "portals_or_openings": result["closure"]["openings"],
        "rows": result["closure"]["rows"],
        "open_edges_over_released_regions": [
            {"CAD_GEOMETRY_ID": r.cad_geometry_id,
             "open_edge_mm": round(sum(s.length_mm for s in r.boundary.segments
                                       if s.role == cg.OPEN_EDGE), 3)}
            for r in released],
        "an_open_edge_is_a_result": (
            "where CAD establishes an open connection the edge stays open. "
            "No wall was created, no door was invented, and no virtual "
            "portal was inserted without opening evidence"),
    })
    curved = [(r, s) for r in result["regions"] if r.boundary is not None
              for s in r.boundary.segments if s.kind in (cg.ARC, cg.CIRCLE)]
    write("E1_CURVE_PRESERVATION_REGISTER.json", {
        "source_arcs": source["arcs"],
        "source_circles": source["circles"],
        "why_this_register_exists": (
            "the boundary pipeline this project grew before E1 emitted "
            "only axis-aligned edges, so every arc in this drawing was "
            "dropped before enclosure and every room polygon was "
            "rectilinear by construction"),
        "curved_segments_in_e1_boundaries": len(curved),
        "rows": [{"CAD_GEOMETRY_ID": r.cad_geometry_id,
                  "entity": s.record()["entity"],
                  "centre_mm": [s.cx, s.cy], "radius_mm": s.radius,
                  "start_angle_rad": s.start_angle,
                  "end_angle_rad": s.end_angle,
                  "direction": "CCW" if s.ccw else "CW",
                  "endpoints_mm": [list(p) for p in s.endpoints()],
                  "layer": s.layer,
                  "analytical_geometry": "THE_ORIGINAL_CURVE",
                  "tessellation": cg.RENDERING_ONLY}
                 for r, s in curved],
        "no_chord_became_measurement_geometry": True,
    })
    withheld = [r for r in result["regions"]
                if not r.released]
    write("E1_WITHHELD_GEOMETRY_REGISTER.json", {
        "rule": er.WITHHOLD_RATHER_THAN_REPAIR,
        "withheld": len(withheld),
        "by_outcome": {o: sum(1 for r in withheld if r.outcome == o)
                       for o in er.OUTCOMES},
        "rows": [{"CAD_GEOMETRY_ID": r.cad_geometry_id,
                  "label": r.label_as_drawn, "OUTCOME": r.outcome,
                  "CONFLICTS": list(r.conflicts),
                  "failed_checks": r.validation.get("failed", []),
                  "why": r.why} for r in withheld],
        "success_is_not_closure": (
            "E1 does not need every functional label to have a closed "
            "polygon. An OPEN, PARTIAL or UNRESOLVED result is preferable "
            "to manufactured geometry"),
    })
    write("E1_STAIR_REGISTER.json", {"source": source, **st})

    overlay = whole_floor_overlay(
        gf, prep, result, out / "E1_GROUND_FLOOR_CAD_ALIGNMENT_OVERLAY.png")
    artifacts["E1_GROUND_FLOOR_CAD_ALIGNMENT_OVERLAY.png"] = overlay[prov.RAW]
    locals_ = local_overlays(gf, prep, result, out / "local_overlays")
    for row in locals_:
        artifacts[f"local_overlays/{row['file']}"] = row[prov.RAW]
    write("E1_OVERLAY_INDEX.json", {"whole_floor": overlay,
                                    "local_overlays": locals_})

    man = dict(seal["manifest"])
    (out / "E1_INPUT_MANIFEST.json").write_text(
        json.dumps(man, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")
    artifacts["E1_INPUT_MANIFEST.json"] = _sha(
        out / "E1_INPUT_MANIFEST.json")

    freeze = {
        "E1_MODEL": E1_MODEL,
        "RUN_ID": "E1-P7757-GF-001",
        "E1_RUN_CLASS": CONTROLLED_INTEGRATION_REGRESSION,
        "why_controlled_integration_regression": (
            "E1 stands on geometry modules developed in rounds 6 to 6E, "
            "which were explicitly benchmark-informed. This run opened no "
            "benchmark, but the lineage is not pristine and this register "
            "does not claim blind validation"),
        "E1_CURRENT_RUN_BENCHMARK_INPUTS": "NONE",
        "modules_written_for_E1_with_no_benchmark_in_view":
            list(E1_NEW_MODULES),
        "modules_with_benchmark_informed_lineage":
            list(BENCHMARK_INFORMED_LINEAGE),
        "SOURCE_HASHES": {
            "cad_decode": source["decode_sha256"],
            "NORMALIZATION_HASH": source["NORMALIZATION_HASH"],
            "a18_pass_b_register": _sha(
                Path(a.a18_dir) / "A18_VISUAL_ZONE_REGISTER.json"),
            "a18_pass_d_candidates": _sha(
                Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json"),
        },
        "CODE_VERSION_HASHES": code_hashes(),
        "MODEL_HASHES": {"cad_geometry": cg.model_hash(),
                         "e1_region": er.model_hash(),
                         "e1_inputs": ei.model_hash()},
        "SANDBOX_EQUALITY": seal["report"],
        "ARTIFACTS": artifacts,
        "what_E1_did_not_do": [
            "no benchmark, Excel, reconciliation, manual take-off or "
            "external-review grading was opened",
            "no area was compared with anything",
            "no trade or measurement zone was decided",
            "no region was merged for sharing a finish",
            "no marble or other quantity was computed",
        ],
    }
    freeze["E1_RUN_HASH"] = prov.canonical_sha256(freeze)
    (out / "E1_FREEZE.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False, default=str)
        + "\n", encoding="utf-8")

    print(json.dumps({
        "sandbox": seal["report"]["status"],
        "outcomes": {o: sum(1 for r in result["regions"] if r.outcome == o)
                     for o in er.OUTCOMES},
        "released": len(released),
        "withheld": len(withheld),
        "curved_segments": len(curved),
        "portals": result["closure"]["openings"],
        "junction_repairs": result["closure"]["junction_repairs"],
        "stairs": st["count"],
        "local_overlays": len(locals_),
        "artifacts": len(artifacts) + 1,
        "E1_RUN_HASH": freeze["E1_RUN_HASH"][:16],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
