"""E1.2 — atomic entity-role intervals and a true visual challenger.

    python -m tools.run_e1_2 --phase geometry  --sandbox <dir> --out <dir>
    python -m tools.run_e1_2 --phase v2-inputs --out <dir>
    python -m tools.run_e1_2 --phase finalize  --out <dir>

E1 and E1.1 are not touched. Three phases, because the visual challenge
has to happen between them and an overlay anchors whoever looks at it:

    geometry    the deterministic work - intervals, roles, columns,
                labels, candidates, deterministic drawing QA - then the
                SOURCE-ONLY crops the cold pass V1 will see
    v2-inputs   after V1 is frozen: the candidate overlays and the V2
                task manifests
    finalize    arbitration between the frozen reading, CAD and the cold
                visual passes, the release invariant, the registers and
                the freeze

Nothing here opens a benchmark, an Excel workbook, a reconciliation, a
corrected geometry or an expected area, and no threshold in it was chosen
to make a number come out.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from engine import admission_ledger as led
from engine import agent_sandbox as sbx
from engine import arbitration as arb
from engine import atomic_interval as ai
from engine import cad_adapter as adapter
from engine import cad_geometry as cg
from engine import cad_profile as cprofile
from engine import curve_semantics as cs
from engine import deterministic_qa as dqa
from engine import drawing_region as dreg
from engine import e1_2_inputs as ei2
from engine import e1_region as er
from engine import e1_release as rel
from engine import export_provenance as prov
from engine import interval_role as ir
from engine import label_grouping as lg
from engine import label_ontology as lo
from engine import raster_qa as rq
from engine import stair_completeness as stc
from engine import visual_challenger as vc

E1_2_MODEL = "E1_2_ATOMIC_ENTITY_ROLE_INTERVALS_AND_TRUE_VISUAL_CHALLENGER_V1"
RUN_ID = "E1_2-P7757-GF-001"
PAIRED_SHARE_WALL_LIKE = 0.45
CONTROLLED_INTEGRATION_REGRESSION = "CONTROLLED_INTEGRATION_REGRESSION"

E1_2_NEW_MODULES = ("engine/atomic_interval.py", "engine/interval_role.py",
                    "engine/label_ontology.py", "engine/deterministic_qa.py",
                    "engine/visual_challenger.py", "engine/arbitration.py",
                    "engine/admission_ledger.py", "engine/e1_2_inputs.py",
                    "tools/run_e1_2.py")
CARRIED_FORWARD = ("engine/cad_geometry.py", "engine/e1_region.py",
                   "engine/curve_semantics.py", "engine/label_grouping.py",
                   "engine/raster_qa.py", "engine/stair_completeness.py",
                   "engine/e1_release.py", "engine/e1_1_inputs.py",
                   "engine/e1_inputs.py", "engine/agent_sandbox.py")
BENCHMARK_INFORMED_LINEAGE = ("engine/cad_adapter.py", "engine/cad_profile.py",
                              "engine/cad_regions.py",
                              "engine/drawing_region.py")

# --- delta reasons -------------------------------------------------------
NO_CHANGE = "NO_CHANGE"
RELEASE_TO_WITHHOLD = "RELEASE_TO_WITHHOLD"
WITHHOLD_TO_RELEASE = "WITHHOLD_TO_RELEASE"
BOUNDARY_RESHAPED = "BOUNDARY_RESHAPED"
INTERVAL_ROLE_SPLIT = "INTERVAL_ROLE_SPLIT"
COLUMN_EVIDENCE_WITHDRAWN = "COLUMN_EVIDENCE_WITHDRAWN"
COLLINEAR_PROPAGATION_WITHDRAWN = "COLLINEAR_PROPAGATION_WITHDRAWN"
AMBIGUOUS_BAND_FOUND = "AMBIGUOUS_BAND_FOUND"
LABEL_RECLASSIFIED = "LABEL_RECLASSIFIED"
VISUAL_CHALLENGE_VETO = "VISUAL_CHALLENGE_VETO"
ARBITRATION_RESOLVED = "ARBITRATION_RESOLVED"
OTHER_EXPLAINED = "OTHER_EXPLAINED"
DELTA_REASONS = (NO_CHANGE, RELEASE_TO_WITHHOLD, WITHHOLD_TO_RELEASE,
                 BOUNDARY_RESHAPED, INTERVAL_ROLE_SPLIT,
                 COLUMN_EVIDENCE_WITHDRAWN,
                 COLLINEAR_PROPAGATION_WITHDRAWN, AMBIGUOUS_BAND_FOUND,
                 LABEL_RECLASSIFIED, VISUAL_CHALLENGE_VETO,
                 ARBITRATION_RESOLVED, OTHER_EXPLAINED)

OVERLAY_LEGEND = (
    "thick black = the proposed material boundary",
    "blue = a curved material face, kept as an arc",
    "dashed orange = a portal or open edge: nothing was built along it",
    "magenta = casework, pool internals and setting-out, EXCLUDED",
    "yellow = a paired band CAD cannot tell from a counter or a bar",
    "green = the drawing's own dimensions",
    "blue ring = where the label is seen",
)


def _sha(path) -> str:
    return prov.raw_sha256(path)


def _english_token(label) -> str:
    for part in reversed(str(label or "").split("/")):
        tok = re.sub(r"[^A-Za-z. ]", "", part).strip()
        if len(tok) >= 3:
            return " ".join(tok.upper().split())
    return ""


# ------------------------------------------------------------ the source

def layer_roles(profile) -> dict:
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
                "CANDIDATE_GENERATION_EVIDENCE_ONLY. In E1.2 it does not "
                "even reach an entity: a role belongs to an interval",
            "confidence": conf,
            "evidence": {"entities": lay.entities,
                         "total_length_m": round(lay.total_length_mm / 1000, 2),
                         "paired_share": paired,
                         "profile_proposed_role": lay.proposed_role,
                         "profile_status": lay.status},
        }
    return out


def prepare(decode_path) -> dict:
    decode = json.loads(Path(decode_path).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    profile = cprofile.build(nd)
    return {"decode": decode, "nd": nd, "profile": profile,
            "regions": dreg.isolate(nd), "layer_roles": layer_roles(profile)}


def ground_floor(prep, *, region_id="DR-002") -> dict:
    region = [r for r in prep["regions"].regions
              if r.region_id == region_id][0]
    nd = prep["nd"]
    return {"region": region,
            "primitives": [p for p in nd.primitives
                           if region.holds(p.object_id)],
            "texts": [t for t in nd.texts if region.contains(t.x, t.y)],
            "dimensions": [d for d in nd.dimensions
                           if region.contains(d.x1, d.y1)
                           or region.contains(d.x2, d.y2)]}


# ------------------------------------------------- intervals as geometry

class IntervalPrim:
    """One atomic interval, shaped like a primitive so the frozen tracer
    and the frozen opening-closure can read it unchanged."""

    def __init__(self, parent, iv):
        self.kind = parent.kind
        self._iv = iv
        self._parent = parent
        self.provenance = parent.provenance
        if parent.kind == "SEGMENT":
            self.x1, self.y1 = iv.start_mm
            self.x2, self.y2 = iv.end_mm
            self.cx = self.cy = self.radius = 0.0
            self.start_angle = self.end_angle = 0.0
        else:
            self.cx, self.cy, self.radius = parent.cx, parent.cy, parent.radius
            sweep = ((parent.end_angle - parent.start_angle) % (2 * math.pi)
                     if parent.kind == "ARC" else 2 * math.pi)
            self.start_angle = parent.start_angle + sweep * iv.t_start
            self.end_angle = parent.start_angle + sweep * iv.t_end
            self.x1, self.y1 = iv.start_mm
            self.x2, self.y2 = iv.end_mm

    @property
    def object_id(self) -> str:
        return self._iv.interval_id

    @property
    def length_mm(self) -> float:
        return self._iv.length_mm

    @property
    def interval(self):
        return self._iv


def interval_prims(intervals, by_id, *, only_material=True) -> list:
    out = []
    for oid, rows in intervals.items():
        parent = by_id.get(oid)
        if parent is None:
            continue
        for iv in rows:
            if only_material and not iv.may_bound_material:
                continue
            if iv.length_mm <= 0:
                continue
            out.append(IntervalPrim(parent, iv))
    return out


def boundary_role_of(iv, *, column_layers=cg.COLUMN_LAYERS_DEFAULT) -> str:
    if iv.role == ir.GLAZING:
        return cg.GLAZING_BOUNDARY
    if iv.role == ir.COLUMN:
        return cg.COLUMN_FACE
    if iv.kind in ("ARC", "CIRCLE"):
        return cg.CURVED_MATERIAL_FACE
    return cg.MATERIAL_WALL_FACE


# ------------------------------------------------------- the geometry pass

def interpret(gf, prep, *, door_layers=("D",)) -> dict:
    prims = gf["primitives"]
    defaults = {k: v["LAYER_DEFAULT_ROLE"]
                for k, v in prep["layer_roles"].items()}
    dim_layers = [k for k, v in defaults.items() if v == cg.DIMENSION_WITNESS]
    ann_layers = [k for k, v in defaults.items() if v == cg.ANNOTATION_ONLY]
    # A LEVEL LAYER IS FOUND, NOT NAMED: a layer whose texts read as levels
    # and whose linework is short leader work is level/grid annotation.
    level_layers = _level_layers(gf, defaults)

    labels = lg.build(gf["texts"], typo=lg.typography(prep["decode"]))
    label_points = [(g.centroid[0], g.centroid[1], g.english_token)
                    for g in labels["groups"] if g.english_token]
    curves = cs.classify(prims, label_points=label_points)

    first = ir.establish(prims, layer_defaults=defaults,
                         dimension_layers=dim_layers,
                         annotation_layers=ann_layers,
                         level_layers=level_layers,
                         door_layers=set(door_layers),
                         curve_roles=curves["curve_roles"])
    not_a_tread = (ir.DIMENSION_LINE, ir.DIMENSION_WITNESS, ir.DOOR,
                   ir.ANNOTATION, ir.LEVEL_OR_GRID_ANNOTATION,
                   ir.CONSTRUCTION_LINE, ir.POOL_INTERNAL_GEOMETRY,
                   ir.POOL_CONTOUR)
    skip = {oid for oid, rows in first["intervals"].items()
            if all(iv.role in not_a_tread for iv in rows)}
    centres = [(o.cx, o.cy, max(o.radii_mm))
               for o in curves["round_objects"] if len(o.radii_mm) >= 2]
    stairs = stc.detect(prims, exclude_object_ids=sorted(skip),
                        radial_centres=centres,
                        stair_label_points=label_points)
    final = ir.establish(prims, layer_defaults=defaults,
                         dimension_layers=dim_layers,
                         annotation_layers=ann_layers,
                         level_layers=level_layers,
                         door_layers=set(door_layers),
                         curve_roles=curves["curve_roles"],
                         stair_object_ids=stairs["tread_object_ids"])
    return {"labels": labels, "curves": curves, "stairs": stairs,
            "roles": final, "layer_defaults": defaults,
            "dimension_layers": dim_layers, "annotation_layers": ann_layers,
            "level_layers": sorted(level_layers)}


def _level_layers(gf, defaults) -> set:
    """Layers whose TEXT reads as levels or grid marks, found from content.

    No layer name is matched. A layer earns this by what its own text says
    and by its linework being short leader work rather than long runs.
    """
    by_layer = {}
    for t in gf["texts"]:
        lay = t.provenance.layer
        row = by_layer.setdefault(lay, {"texts": 0, "level_like": 0})
        row["texts"] += 1
        v = (t.value or "").strip()
        if v.startswith("%%") or lo._LEVEL.match(v):
            row["level_like"] += 1
    out = set()
    for lay, row in by_layer.items():
        if row["texts"] >= 2 and row["level_like"] / row["texts"] >= 0.6:
            out.add(lay)
    return out


def build_candidates(gf, interp, *, ontology) -> dict:
    """One trace per PHYSICAL or FUNCTIONAL label, from established
    material INTERVALS only."""
    from shapely.geometry import Point, Polygon
    roles = interp["roles"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    mat = interval_prims(roles["intervals"], by_id, only_material=True)
    closure = cg.close_openings(mat, wall_layers=(), door_layers={"D"})
    segs = []
    for m in mat:
        segs.append(cg._as_segment(m, role=boundary_role_of(m.interval)))
    extra = tuple(segs) + tuple(closure["barriers"])

    keep = {r.group_id for r in ontology["rows"] if r.in_denominator}
    groups = [g for g in interp["labels"]["groups"]
              if g.group_id in keep and g.english_token]
    rows = []
    for n, g in enumerate(groups, start=1):
        english = [m for m in g.members
                   if m.stamp_class == lg.ENGLISH_ROOM_STAMP]
        anchor = english[0] if english else g.members[0]
        seed = anchor.visible_centroid
        out = cg.trace(seed, [], wall_layers=(), tol_mm=cg.DENSIFY_TOL_MM,
                       role_of=None, extra_segments=extra)
        rows.append({"n": n, "group": g, "anchor": anchor, "seed": seed,
                     "trace": out,
                     "candidate_id": f"E1_2-{g.group_id}"})
    for row in rows:
        inside = []
        out = row["trace"]
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
    return {"rows": rows, "closure": closure, "material_prims": mat,
            "segments": segs, "extra": extra}


# ------------------------------------------------------------- the sandbox

def build_sandbox(root, *, decode, a18_dir, rules, raster, prior_e1,
                  prior_e1_1) -> dict:
    run = ei2.E1_2Run(run_id=RUN_ID,
                      subject="E1.2 atomic entity-role intervals and a "
                              "cold visual challenge",
                      floor="GROUND")
    box = sbx.Sandbox(root=Path(root), run=run, working_dirs=())
    ledger = led.Ledger(run=run, box=box)
    a18 = Path(a18_dir)
    plan = [
        (ei2.Input(input_id="CAD_DECODE",
                   kind=ei2.e11.ei.CAD_GEOMETRY_SOURCE,
                   what_it_is="the authoritative DWG-derived geometry",
                   path=str(decode)), "cad/P7757_ARCHITECTURAL.json"),
        (ei2.Input(input_id="PASS_B_REGISTER",
                   kind=ei2.e11.ei.FROZEN_PASS_B,
                   what_it_is="frozen A18 Pass B semantic hypotheses",
                   path=str(a18 / "A18_VISUAL_ZONE_REGISTER.json")),
         "a18/A18_VISUAL_ZONE_REGISTER.json"),
        (ei2.Input(input_id="PASS_D_CANDIDATES",
                   kind=ei2.e11.ei.FROZEN_PASS_D,
                   what_it_is="every frozen A18 ground-floor hypothesis",
                   path=str(a18 / "A18_PASS_D_CANDIDATES.json")),
         "a18/A18_PASS_D_CANDIDATES.json"),
        (ei2.Input(input_id="PASS_C2_RECORD",
                   kind=ei2.e11.ei.FROZEN_PASS_C2,
                   what_it_is="frozen Pass C2 challenge record",
                   path=str(a18 / "A18-GF-001_PASS_C2.json")),
         "a18/A18-GF-001_PASS_C2.json"),
        (ei2.Input(input_id="SUPERVISED_FLOORS",
                   kind=ei2.e11.ei.CAD_SOURCE_METADATA,
                   what_it_is="which drawing region is which floor",
                   path="data/registry/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
         "cad/P7757_SUPERVISED_FLOOR_ASSIGNMENT.json"),
    ]
    if raster and Path(raster).exists():
        plan.append((ei2.Input(
            input_id="SOURCE_SHEET", kind=ei2.SOURCE_RASTER_QA,
            what_it_is="the original ground-floor sheet, for QA and for "
                       "the cold visual challenge",
            path=str(raster)), f"sheet/{Path(raster).name}"))
    for label, folder, names in (
            ("E1_V1", prior_e1, ("E1_A18_CAD_ALIGNMENT_REGISTER.json",)),
            ("E1_1", prior_e1_1, ("E1_1_CAD_GEOMETRY_REGISTER.json",
                                  "E1_1_ENTITY_ROLE_REGISTER.json",
                                  "E1_1_FREEZE.json"))):
        for name in names:
            p = Path(folder) / name
            if p.exists():
                plan.append((ei2.Input(
                    input_id=f"{label}_{name.split('.')[0]}",
                    kind=ei2.PRIOR_E1_ITERATION_REGISTER,
                    what_it_is="a previous iteration's frozen register, "
                               "for the delta only",
                    path=str(p)), f"prior/{label}/{name}"))
    if rules:
        plan.append((ei2.Input(
            input_id="GENERAL_RULES", kind=ei2.e11.ei.GENERAL_GEOMETRY_RULE,
            what_it_is="approved general Urban geometry rules, projected",
            content=rules), "rules/general_geometry_rules.json"))

    for item, at in plan:
        ledger.offer(item, at=at)
    check = ledger.assert_consistent()
    return {"box": box, "ledger": ledger, "check": check}


def code_hashes() -> dict:
    out = {}
    for relpath in (list(E1_2_NEW_MODULES) + list(CARRIED_FORWARD)
                    + list(BENCHMARK_INFORMED_LINEAGE)):
        p = Path(relpath)
        if p.exists():
            out[relpath] = _sha(p)
    return out


# --------------------------------------------------------------- overlays

TREATMENT = {
    cg.MATERIAL_WALL_FACE: ((20, 20, 20), 5),
    cg.CURVED_MATERIAL_FACE: ((0, 120, 200), 7),
    cg.GLAZING_BOUNDARY: ((0, 170, 170), 5),
    cg.COLUMN_FACE: ((120, 60, 160), 5),
    cg.VIRTUAL_PORTAL_BOUNDARY: ((230, 120, 0), 5),
    cg.CAD_JUNCTION_REPAIR: ((160, 160, 60), 3),
    cg.OPEN_EDGE: ((220, 30, 30), 5),
    cg.ROLE_UNRESOLVED: ((140, 140, 140), 3),
}
DASHED = (cg.VIRTUAL_PORTAL_BOUNDARY, cg.OPEN_EDGE, cg.CAD_JUNCTION_REPAIR)
CASEWORK_COLOUR = (200, 0, 200)
AMBIGUOUS_COLOUR = (220, 190, 0)


def _draw(draw, seg, to_px, *, colour=None, width=None):
    col, wid = TREATMENT.get(seg.role, TREATMENT[cg.ROLE_UNRESOLVED])
    col, wid = colour or col, width or wid
    pts = [to_px(x, y) for x, y in seg.points(tol_mm=cg.DENSIFY_TOL_MM)]
    if len(pts) < 2:
        return
    if seg.role in DASHED:
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


def _frame(sheet, reg, centre_mm, half_mm, size):
    from PIL import Image
    got = sheet.crop(centre_mm[0] - half_mm, centre_mm[1] - half_mm,
                     centre_mm[0] + half_mm, centre_mm[1] + half_mm)
    if got is None:
        return None
    crop, box = got
    img = crop.convert("RGB").resize(size, Image.LANCZOS)
    sx = size[0] / max(1, box[2] - box[0])
    sy = size[1] / max(1, box[3] - box[1])

    def to_px(x, y):
        px, py = reg.to_px(x, y)
        return ((px - box[0]) * sx, (py - box[1]) * sy)
    return img, to_px, box


def _extent_of(row, half_default=5000.0):
    b = row.get("boundary")
    cx, cy = row["anchor"].visible_centroid
    half = half_default
    if b is not None:
        bb = b.bbox_for_indexing_only().get("extent_mm")
        if bb:
            cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0
            half = max(bb[2] - bb[0], bb[3] - bb[1]) / 2.0 + 2500.0
    return (cx, cy), half


def source_crops(sheet, reg, rows, out_dir) -> list:
    """§8 PASS V1 input: the sheet, and nothing anybody proposed."""
    from PIL import ImageDraw, ImageFont
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for row in rows:
        centre, half = _extent_of(row)
        got = _frame(sheet, reg, centre, half, (1400, 1400))
        if got is None:
            continue
        img, _to_px, _box = got
        if reg.rotation_deg:
            img = img.rotate(-reg.rotation_deg, expand=True)
        name = f"V1_SOURCE_{row['candidate_id']}.png"
        img.save(out_dir / name)
        made.append({"candidate_id": row["candidate_id"],
                     "identity": row["group"].english_token,
                     "file": str(out_dir / name),
                     "NO_CANDIDATE_BOUNDARY_IS_DRAWN": True,
                     prov.RAW: _sha(out_dir / name)})
    return made


def candidate_overlays(sheet, reg, gf, interp, rows, out_dir) -> list:
    """§8 PASS V2 input: the same crop with ONE proposal drawn on it."""
    from PIL import ImageDraw, ImageFont
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_id = {p.object_id: p for p in gf["primitives"]}
    made = []
    for row in rows:
        centre, half = _extent_of(row)
        got = _frame(sheet, reg, centre, half, (1500, 1500))
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
                    colour = CASEWORK_COLOUR
                elif iv.role == ir.AMBIGUOUS_PAIRED_BAND:
                    colour = AMBIGUOUS_COLOUR
                else:
                    continue
                seg = cg._as_segment(IntervalPrim(parent, iv))
                pts = [to_px(x, y) for x, y in seg.points(tol_mm=2.0)]
                if len(pts) >= 2 and all(-300 <= q[0] <= 1800
                                         and -300 <= q[1] <= 1800
                                         for q in pts):
                    draw.line(pts, fill=colour, width=4)
        b = row.get("boundary")
        if b is not None:
            for seg in b.segments:
                _draw(draw, seg, to_px)
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
                     prov.RAW: _sha(out_dir / name)})
    return made


# --------------------------------------------------------------- phases

def _write(out, artifacts, name, body) -> dict:
    body = dict(body)
    body["E1_2_MODEL"] = E1_2_MODEL
    body["RUN_ID"] = RUN_ID
    key = f"{name.split('.')[0]}_HASH"
    # A register's own hash is never part of what it hashes. Re-writing a
    # register that already carries one (the two visual registers are read
    # back from disk after a cold pass recorded into them) would otherwise
    # fold the previous hash into the new one and the freeze would not
    # reproduce from the same inputs.
    body.pop(key, None)
    body[key] = prov.canonical_sha256(body)
    path = Path(out) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    artifacts[name] = _sha(path)
    return body


def _a18_index(candidates) -> dict:
    out = {}
    for c in candidates:
        tok = _english_token(c.get("label_as_drawn", ""))
        if tok:
            out.setdefault(tok, []).append(c)
    return out


def phase_geometry(a) -> dict:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {}

    rules = None
    if a.rules and Path(a.rules).exists():
        from engine import blind_input_contract as bicm
        rules = bicm.general_rules(json.loads(
            Path(a.rules).read_text(encoding="utf-8")))
    seal = build_sandbox(a.sandbox, decode=a.decode, a18_dir=a.a18_dir,
                         rules=rules, raster=a.raster, prior_e1=a.prior_e1,
                         prior_e1_1=a.prior_e1_1)

    prep = prepare(a.decode)
    gf = ground_floor(prep)
    interp = interpret(gf, prep)
    by_id = {p.object_id: p for p in gf["primitives"]}
    mat = interval_prims(interp["roles"]["intervals"], by_id)
    mat_segs = [cg._as_segment(m, role=boundary_role_of(m.interval))
                for m in mat]

    cand_json = json.loads((Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json")
                           .read_text(encoding="utf-8"))["candidates"]
    zone_tokens = {_english_token(c.get("label_as_drawn", ""))
                   for c in cand_json
                   if str(c.get("candidate_id", "")).startswith("FZ")}
    ontology = lo.classify(interp["labels"]["groups"], region=gf["region"],
                           a18_zone_tokens=sorted(t for t in zone_tokens if t),
                           material_segments=mat_segs)

    built = build_candidates(gf, interp, ontology=ontology)
    rows = built["rows"]

    a18_by_token = _a18_index(cand_json)
    site_area = max((r["trace"]["candidates"][0]
                     ["densified_area_m2_rendering_only"]
                     for r in rows if r["trace"].get("candidates")),
                    default=None)
    interval_by_id = {iv.interval_id: iv
                      for rows_ in interp["roles"]["intervals"].values()
                      for iv in rows_}
    for r in rows:
        g = r["group"]
        hits = a18_by_token.get(g.english_token, [])
        reg = er.assess(cad_geometry_id=r["candidate_id"],
                        a18_candidate_id=",".join(c["candidate_id"]
                                                  for c in hits),
                        drawing_id="P7757_ARCHITECTURAL.dwg", floor="GROUND",
                        label=g.english_token, trace_result=r["trace"],
                        labels_in_face=r["labels_inside"],
                        a18_identity=bool(hits))
        reg = er.validate(reg, released_boundaries=[], site_area_m2=site_area)
        r["region"] = reg
        r["boundary"] = reg.boundary
        r["a18"] = hits
        r["ambiguous_on_ring"] = tuple(
            iv.interval_id for iv in
            [interval_by_id.get(s.object_id) for s in
             (reg.boundary.segments if reg.boundary is not None else ())]
            if iv is not None and iv.role == ir.AMBIGUOUS_PAIRED_BAND)

    cands = []
    for r in rows:
        b = r["boundary"]
        if b is None:
            continue
        try:
            pts = b.points()
        except Exception:
            continue
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
    for r in rows:
        dims = dqa.dimension_cross_check(r["boundary"], gf["dimensions"])
        r["dqa"] = dqa.check(
            boundary=r["boundary"], interval_roles=iv_lookup,
            distinct_label_groups=set(r["labels_inside"]),
            dimension_rows=dims,
            overlap_relations=by_cand.get(r["candidate_id"], []),
            a18_topology_conflict=False,
            ambiguous_band_on_ring=r["ambiguous_on_ring"])
        r["overlaps"] = by_cand.get(r["candidate_id"], [])

    reg_r = sheet = None
    if a.raster and Path(a.raster).exists():
        rgn = gf["region"]
        reg_r = rq.register(a.raster, gf["primitives"],
                            extent=(rgn.x0, rgn.y0, rgn.x1, rgn.y1))
        sheet = rq.Sheet(reg_r)

    v1_dir = out / "visual" / "v1_source_only"
    crops = source_crops(sheet, reg_r, rows, v1_dir) if sheet else []
    tasks = []
    for c in crops:
        t = vc.Task(task_id=f"V1-{c['candidate_id']}",
                    candidate_id=c["candidate_id"], identity=c["identity"],
                    crop_path=c["file"], stage=vc.V1)
        tasks.append(t.manifest())

    _write(out, artifacts, "E1_2_VISUAL_V1_REGISTER.json", {
        "STAGE": vc.V1,
        "status": "AWAITING_THE_COLD_PASS",
        "an_overlay_anchors_a_reader": vc.AN_OVERLAY_ANCHORS_A_READER,
        "what_the_challenger_never_receives":
            vc.WHAT_THE_CHALLENGER_NEVER_RECEIVES,
        "brief": vc.V1_BRIEF,
        "observation_vocabulary": list(vc.V1_OBSERVATIONS),
        "crops": crops,
        "task_manifests": tasks,
        "answers": [],
    })

    state = {
        "candidates": [{
            "candidate_id": r["candidate_id"],
            "identity": r["group"].english_token,
            "label_group": r["group"].group_id,
            "seed_mm": [round(r["seed"][0], 3), round(r["seed"][1], 3)],
            "outcome": r["region"].outcome,
            "labels_inside": list(r["labels_inside"]),
            "ambiguous_on_ring": list(r["ambiguous_on_ring"]),
            "a18_candidate_ids": [c["candidate_id"] for c in r["a18"]],
            "DETERMINISTIC_QA_STATE": r["dqa"]["DETERMINISTIC_QA_STATE"],
            "dqa_notes": r["dqa"]["notes"],
            "dimension_cross_check": r["dqa"]["dimension_cross_check"],
            "overlaps": r["overlaps"],
        } for r in rows],
        "registration": reg_r.record() if reg_r else {},
        "site_area_m2_rendering_only": site_area,
    }
    (out / "_E1_2_STATE.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")

    _write_geometry_registers(out, artifacts, prep, gf, interp, ontology,
                              built, rows, overlaps, seal, a)
    print(json.dumps({
        "phase": "geometry",
        "ledger": seal["check"],
        "entities": interp["roles"]["entity_count"],
        "intervals": interp["roles"]["interval_count"],
        "entities_with_more_than_one_role":
            interp["roles"]["entities_with_more_than_one_role"],
        "interval_roles": interp["roles"]["counts_by_role"],
        "columns": {k: v for k, v in interp["roles"]["columns"].items()
                    if k != "loops"},
        "labels": ontology["counts"],
        "candidates": len(rows),
        "outcomes": {o: sum(1 for r in rows if r["region"].outcome == o)
                     for o in er.OUTCOMES},
        "deterministic_qa": {s: sum(
            1 for r in rows if s in r["dqa"]["DETERMINISTIC_QA_STATE"])
            for s in dqa.QA_STATES},
        "v1_crops": len(crops),
    }, indent=2))
    return {"rows": rows, "artifacts": artifacts}


def _source(prep, gf, a) -> dict:
    nd = prep["nd"]
    return {
        "DRAWING_ID": "P7757_ARCHITECTURAL.dwg",
        "decode_file": str(a.decode),
        "decode_sha256": _sha(a.decode),
        "NORMALIZATION_HASH": nd.normalization_hash(),
        "drawing_unit": nd.drawing_unit,
        "dimlfac": nd.dimlfac,
        "primitives": len(nd.primitives),
        "arcs": sum(1 for p in nd.primitives if p.kind == "ARC"),
        "circles": sum(1 for p in nd.primitives if p.kind == "CIRCLE"),
        "FLOOR": "GROUND",
        "drawing_region": gf["region"].record(),
    }


def _write_geometry_registers(out, artifacts, prep, gf, interp, ontology,
                              built, rows, overlaps, seal, a):
    src = _source(prep, gf, a)
    roles = interp["roles"]

    _write(out, artifacts, "E1_2_ATOMIC_INTERVAL_ROLE_REGISTER.json", {
        "source": src,
        "the_correction": {
            "UNIT_OF_ROLE": "ATOMIC_ENTITY_INTERVAL",
            "evidence_licenses_only_its_own_interval":
                ai.EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL,
            "whole_entity_promotion_is_banned":
                ai.WHOLE_ENTITY_PROMOTION_IS_BANNED,
        },
        "CUT_REASONS": list(ai.CUT_REASONS),
        "ROLES": list(ir.ROLES),
        "MAY_BOUND_MATERIAL": list(ir.MAY_BOUND_MATERIAL),
        "entities": roles["entity_count"],
        "intervals": roles["interval_count"],
        "entities_carrying_more_than_one_role":
            roles["entities_with_more_than_one_role"],
        "counts_by_role": roles["counts_by_role"],
        "intervals_that_may_bound_material":
            roles["intervals_that_may_bound_material"],
        "material_length_mm": roles["material_length_mm"],
        "frozen_parameters": {"atomic_interval": ai.frozen_parameters(),
                              "interval_role": ir.frozen_parameters()},
        "INTERVALS": [iv.record() for iv in sorted(
            roles["flat"], key=lambda x: (x.role, -x.length_mm))],
    })

    _write(out, artifacts, "E1_2_ENTITY_ROLE_REGISTER.json", {
        "source": src,
        "what_an_entity_row_is": (
            "a SUMMARY of its intervals, never a fact about the entity. "
            "An entity with two roles is listed with both, and no role "
            "here licenses anything - the interval register does"),
        "layer_defaults": prep["layer_roles"],
        "level_layers_found_from_their_own_text": interp["level_layers"],
        "entities": {
            oid: {"roles": sorted({iv.role for iv in rows_}),
                  "intervals": len(rows_),
                  "layer": rows_[0].layer if rows_ else "",
                  "dwg_handle": rows_[0].provenance.get("dwg_handle")
                  if rows_ else None,
                  "length_mm": round(sum(iv.length_mm for iv in rows_), 3),
                  "material_length_mm": round(
                      sum(iv.length_mm for iv in rows_
                          if iv.may_bound_material), 3)}
            for oid, rows_ in roles["intervals"].items()},
        "entities_with_more_than_one_role":
            roles["entities_with_more_than_one_role_rows"],
    })

    _write(out, artifacts, "E1_2_COLUMN_EVIDENCE_REGISTER.json", {
        "source": src,
        "a_small_loop_is_a_question": ir.A_SMALL_LOOP_IS_A_QUESTION,
        "COLUMN_EVIDENCE": list(ir.COLUMN_EVIDENCE),
        "COLUMN_EVIDENCE_REQUIRED": ir.COLUMN_EVIDENCE_REQUIRED,
        "STRUCTURAL_IN_KIND": list(ir.STRUCTURAL_IN_KIND),
        **{k: v for k, v in roles["columns"].items() if k != "loops"},
        "LOOPS": roles["columns"].get("loops", []),
    })

    _write(out, artifacts, "E1_2_LABEL_ONTOLOGY_REGISTER.json", {
        "source": src,
        "LABEL_CLASSES": list(lo.LABEL_CLASSES),
        "IN_THE_COMPLETENESS_DENOMINATOR":
            list(lo.IN_THE_COMPLETENESS_DENOMINATOR),
        "site_context_is_not_a_space": lo.SITE_CONTEXT_IS_NOT_A_SPACE,
        "no_word_list_decides_this": lo.NO_WORD_LIST_DECIDES_THIS,
        "counts": ontology["counts"],
        "PHYSICAL_AND_FUNCTIONAL_CANDIDATES":
            ontology["physical_and_functional_candidates"],
        "SITE_CONTEXT": ontology["site_context"],
        "OTHER_ANNOTATIONS": ontology["other_annotations"],
        "UNRESOLVED": ontology["unresolved"],
        "median_room_stamp_height_mm":
            ontology["median_room_stamp_height_mm"],
        "frozen_parameters": lo.frozen_parameters(),
        "rows": [r.record() for r in ontology["rows"]],
    })

    _write(out, artifacts, "E1_2_DETERMINISTIC_DRAWING_QA_REGISTER.json", {
        "source": src,
        "renamed_from": "E1.1 called this layer visual_gate. It never read "
                        "a pixel",
        "QA_STATES": list(dqa.QA_STATES),
        "never_emits_a_visual_verdict": dqa.NEVER_EMITS_A_VISUAL_VERDICT,
        "banned_state": dqa.BANNED_STATE,
        "frozen_parameters": dqa.frozen_parameters(),
        "counts": {s: sum(1 for r in rows
                          if s in r["dqa"]["DETERMINISTIC_QA_STATE"])
                   for s in dqa.QA_STATES},
        "rows": [{"CANDIDATE_ID": r["candidate_id"],
                  "identity": r["group"].english_token,
                  "DETERMINISTIC_QA_STATE":
                      r["dqa"]["DETERMINISTIC_QA_STATE"],
                  "notes": r["dqa"]["notes"],
                  "dimension_cross_check":
                      r["dqa"]["dimension_cross_check"],
                  "ambiguous_bands_on_the_ring":
                      list(r["ambiguous_on_ring"])}
                 for r in rows],
    })

    _write(out, artifacts, "E1_2_STAIR_COMPLETENESS_REGISTER.json", {
        "source": src,
        "STAIR_TYPES": list(stc.STAIR_TYPES),
        "never_silently_absent": interp["stairs"]["never_silently_absent"],
        "no_riser_without_a_section":
            interp["stairs"]["no_riser_without_a_section"],
        "by_type": interp["stairs"]["by_type"],
        "detected": interp["stairs"]["detected"],
        "explicitly_unresolved": interp["stairs"]["explicitly_unresolved"],
        "frozen_parameters": stc.frozen_parameters(),
        "assemblies": [x.record() for x in interp["stairs"]["assemblies"]],
    })

    man = seal["ledger"].manifest(extra={
        "phase": "E1_2_GEOMETRY",
        "why_E1_is_not_blind": ei2.e11.ei.WHY_E1_IS_NOT_BLIND,
        "why_the_raster_is_admitted": ei2.WHY_THE_RASTER_IS_ADMITTED,
        "why_the_prior_run_is_admitted": ei2.WHY_THE_PRIOR_RUN_IS_ADMITTED,
        "ALLOWED_KINDS": list(ei2.ALLOWED_KINDS),
        "PROHIBITED_KINDS": list(ei2.PROHIBITED_KINDS),
    })
    (Path(out) / "E1_2_INPUT_MANIFEST.json").write_text(
        json.dumps(man, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")
    artifacts["E1_2_INPUT_MANIFEST.json"] = _sha(
        Path(out) / "E1_2_INPUT_MANIFEST.json")
    (Path(out) / "_E1_2_ARTIFACTS_GEOMETRY.json").write_text(
        json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")


def _rebuild(a):
    """The deterministic state, rebuilt identically for a later phase."""
    prep = prepare(a.decode)
    gf = ground_floor(prep)
    interp = interpret(gf, prep)
    by_id = {p.object_id: p for p in gf["primitives"]}
    mat = interval_prims(interp["roles"]["intervals"], by_id)
    mat_segs = [cg._as_segment(m, role=boundary_role_of(m.interval))
                for m in mat]
    cand_json = json.loads((Path(a.a18_dir) / "A18_PASS_D_CANDIDATES.json")
                           .read_text(encoding="utf-8"))["candidates"]
    zone_tokens = {_english_token(c.get("label_as_drawn", ""))
                   for c in cand_json
                   if str(c.get("candidate_id", "")).startswith("FZ")}
    ontology = lo.classify(interp["labels"]["groups"], region=gf["region"],
                           a18_zone_tokens=sorted(t for t in zone_tokens if t),
                           material_segments=mat_segs)
    built = build_candidates(gf, interp, ontology=ontology)
    rows = built["rows"]
    a18_by_token = _a18_index(cand_json)
    site_area = max((r["trace"]["candidates"][0]
                     ["densified_area_m2_rendering_only"]
                     for r in rows if r["trace"].get("candidates")),
                    default=None)
    iv_by_id = {iv.interval_id: iv for iv in interp["roles"]["flat"]}
    for r in rows:
        hits = a18_by_token.get(r["group"].english_token, [])
        reg = er.assess(cad_geometry_id=r["candidate_id"],
                        a18_candidate_id=",".join(c["candidate_id"]
                                                  for c in hits),
                        drawing_id="P7757_ARCHITECTURAL.dwg", floor="GROUND",
                        label=r["group"].english_token,
                        trace_result=r["trace"],
                        labels_in_face=r["labels_inside"],
                        a18_identity=bool(hits))
        r["region"] = er.validate(reg, released_boundaries=[],
                                  site_area_m2=site_area)
        r["boundary"] = r["region"].boundary
        r["a18"] = hits
        r["ambiguous_on_ring"] = tuple(
            iv.interval_id for iv in
            [iv_by_id.get(s.object_id) for s in
             (r["boundary"].segments if r["boundary"] is not None else ())]
            if iv is not None and iv.role == ir.AMBIGUOUS_PAIRED_BAND)
    return {"prep": prep, "gf": gf, "interp": interp, "ontology": ontology,
            "built": built, "rows": rows, "cand_json": cand_json,
            "site_area": site_area, "iv_by_id": iv_by_id}


def phase_v2_inputs(a) -> int:
    out = Path(a.out)
    v1 = json.loads((out / "E1_2_VISUAL_V1_REGISTER.json")
                    .read_text(encoding="utf-8"))
    answers = {x["candidate_id"]: x for x in v1.get("answers", [])}
    if not answers:
        print(json.dumps({"error": "PASS_V1_IS_NOT_FROZEN_YET",
                          "why": "V2 may not be prepared before V1 is "
                                 "answered and frozen. " +
                                 vc.AN_OVERLAY_ANCHORS_A_READER}, indent=2))
        return 1
    st = _rebuild(a)
    rgn = st["gf"]["region"]
    reg_r = rq.register(a.raster, st["gf"]["primitives"],
                        extent=(rgn.x0, rgn.y0, rgn.x1, rgn.y1))
    sheet = rq.Sheet(reg_r)
    made = candidate_overlays(sheet, reg_r, st["gf"], st["interp"],
                              st["rows"], out / "visual" / "v2_overlays")
    tasks = []
    for m in made:
        t = vc.Task(task_id=f"V2-{m['candidate_id']}",
                    candidate_id=m["candidate_id"], identity=m["identity"],
                    crop_path=str(out / "visual" / "v1_source_only" /
                                  f"V1_SOURCE_{m['candidate_id']}.png"),
                    overlay_path=m["file"], legend=OVERLAY_LEGEND,
                    stage=vc.V2)
        row = t.manifest()
        row["frozen_v1_observation"] = answers.get(m["candidate_id"], {})
        tasks.append(row)
    artifacts = {}
    _write(out, artifacts, "E1_2_VISUAL_V2_CHALLENGE_REGISTER.json", {
        "STAGE": vc.V2,
        "status": "AWAITING_THE_CHALLENGE",
        "brief": vc.V2_BRIEF,
        "V2_STATUSES": list(vc.V2_STATUSES),
        "V2_PERMITS_RELEASE": list(vc.V2_PERMITS_RELEASE),
        "the_challenger_may_not_move_a_coordinate":
            vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
        "legend": list(OVERLAY_LEGEND),
        "overlays": made,
        "task_manifests": tasks,
        "answers": [],
    })
    print(json.dumps({"phase": "v2-inputs", "overlays": len(made),
                      "v1_answers_frozen": len(answers)}, indent=2))
    return 0


# ------------------------------------------------- §12 release invariant

C1 = "EXACT_GEOMETRY_IS_COHERENT"
C2 = "EVERY_MATERIAL_BOUNDARY_INTERVAL_HAS_AN_ESTABLISHED_ROLE"
C3 = "WHOLE_ENTITY_ROLE_PROPAGATION_WAS_NOT_USED"
C4 = "NO_AMBIGUOUS_PAIRED_BAND_ACTS_AS_WALL"
C5 = "NO_GENERIC_SMALL_LOOP_ACTS_AS_COLUMN_WITHOUT_STRUCTURAL_EVIDENCE"
C6 = "NO_COLLINEAR_ONLY_PROPAGATION_CREATES_MATERIAL"
C7 = "PORTALS_REMAIN_TOPOLOGY_ONLY"
C8 = "CURVES_REMAIN_ANALYTICAL"
C9 = "LABEL_ONTOLOGY_IS_VALID"
C10 = "OVERLAP_QA_PASSES"
C11 = "DETERMINISTIC_DRAWING_QA_PASSES"
C12 = "COLD_VISUAL_V2_DOES_NOT_CHALLENGE_THE_BOUNDARY"
C13 = "A18_CAD_VISUAL_CONFLICT_IS_RESOLVED"
RELEASE_CONDITIONS = (C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13)

RELEASED, WITHHELD = "RELEASED", "WITHHELD"
CLOSURE_IS_NOT_A_TARGET = (
    "closure rate is not an optimisation target. A stricter evidence rule "
    "that releases fewer regions has done its job; a rule relaxed until "
    "more regions close has not")


def release_decision(*, row, iv_by_id, arbitration) -> dict:
    checks = {}

    def put(name, ok, note):
        checks[name] = {"result": "PASS" if ok else "FAIL", "note": note}

    b = row["boundary"]
    put(C1, bool(b is not None and b.closed and b.segments
                 and row["region"].outcome == er.CLOSED_PHYSICAL_REGION),
        f"outcome is {row['region'].outcome}")
    if b is None:
        for n in RELEASE_CONDITIONS[1:]:
            checks.setdefault(n, {"result": "FAIL",
                                  "note": "no boundary was built"})
        failed = [k for k, v in checks.items() if v["result"] == "FAIL"]
        return {"RELEASE_CONDITIONS": checks, "failed": failed,
                "decision": WITHHELD, "released": False,
                "closure_is_not_a_target": CLOSURE_IS_NOT_A_TARGET}

    ring = [iv_by_id.get(s.object_id) for s in b.segments
            if s.role in cg.MATERIAL_ROLES]
    missing = [s.object_id for s, iv in
               zip([x for x in b.segments if x.role in cg.MATERIAL_ROLES],
                   ring) if iv is None or iv.role == ir.UNKNOWN]
    put(C2, not missing,
        f"{len(missing)} material ring segments have no established "
        f"interval role: {sorted(missing)}" if missing else
        f"all {len(ring)} material ring intervals name an established role")
    put(C3, True,
        "every role on this ring came from an atomic interval; no parent "
        "entity was promoted")
    amb = [iv.interval_id for iv in ring
           if iv is not None and iv.role == ir.AMBIGUOUS_PAIRED_BAND]
    put(C4, not amb,
        f"{len(amb)} ring intervals are bands CAD cannot tell from a "
        f"counter or a bar: {sorted(amb)}" if amb
        else "no ambiguous band on the ring")
    loops = [iv.interval_id for iv in ring
             if iv is not None and iv.role == ir.COLUMN_CANDIDATE_UNRESOLVED]
    put(C5, not loops,
        f"{len(loops)} ring intervals are unresolved column candidates: "
        f"{sorted(loops)}" if loops
        else "no unresolved loop acts as a column here")
    # §5: the ban is on material created BY collinearity, not on material
    # that happens to lie in line with a wall. ir.established_by_
    # collinearity_alone() is the rule; the raw tag is diagnostic.
    collinear_only = [
        iv.interval_id for iv in ring
        if iv is not None and ir.established_by_collinearity_alone(iv)]
    put(C6, not collinear_only,
        f"{len(collinear_only)} ring intervals are material by "
        f"collinearity alone: {sorted(collinear_only)}"
        if collinear_only else
        "no ring interval is material by collinearity alone")
    put(C7, all(s.wall_length_contribution_mm == 0.0 for s in b.segments
                if s.role in cg.TOPOLOGY_ONLY_ROLES),
        "every inserted segment contributes zero wall material")
    curved = [s for s in b.segments if s.kind in (cg.ARC, cg.CIRCLE)]
    put(C8, all(s.radius > 0 for s in curved),
        f"{len(curved)} curved segments keep centre, radius and angles")
    put(C9, row["label_class"] in lo.IN_THE_COMPLETENESS_DENOMINATOR,
        f"label class is {row['label_class']}")
    put(C10, not [o for o in row["overlaps"] if o.get("blocks_release")],
        "no released region overlaps this one impermissibly")
    put(C11, row["dqa"]["DETERMINISTIC_QA_STATE"]
        == [dqa.DETERMINISTICALLY_CONSISTENT],
        "; ".join(row["dqa"]["notes"]))
    v2 = set(row.get("v2_statuses", ()))
    put(C12, bool(v2) and v2 <= set(vc.V2_PERMITS_RELEASE),
        f"the cold visual challenge answered {sorted(v2)}" if v2
        else "the cold visual challenge has not answered for this candidate")
    put(C13, not arbitration.get("blocks_release", True),
        arbitration.get("ARBITRATION_STATE", "UNRESOLVED"))

    failed = [k for k, v in checks.items() if v["result"] == "FAIL"]
    return {"RELEASE_CONDITIONS": checks, "failed": failed,
            "decision": RELEASED if not failed else WITHHELD,
            "released": not failed,
            "closure_is_not_a_target": CLOSURE_IS_NOT_A_TARGET}


# ------------------------------------------------------------- finalize

def phase_finalize(a) -> int:
    out = Path(a.out)
    artifacts = json.loads((out / "_E1_2_ARTIFACTS_GEOMETRY.json")
                           .read_text(encoding="utf-8"))
    v1 = json.loads((out / "E1_2_VISUAL_V1_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v2 = json.loads((out / "E1_2_VISUAL_V2_CHALLENGE_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v1_by = {x["candidate_id"]: x for x in v1.get("answers", [])}
    v2_by = {x["candidate_id"]: x for x in v2.get("answers", [])}

    st = _rebuild(a)
    rows, interp, gf = st["rows"], st["interp"], st["gf"]
    iv_by_id = st["iv_by_id"]
    ontology = st["ontology"]
    label_class = {r.group_id: r.label_class for r in ontology["rows"]}

    # deterministic QA again, from the same inputs
    cands = []
    for r in rows:
        b = r["boundary"]
        if b is None:
            continue
        try:
            pts = b.points()
        except Exception:
            continue
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

    arb_rows = []
    for r in rows:
        r["label_class"] = label_class.get(r["group"].group_id,
                                           lo.UNRESOLVED_TEXT)
        r["overlaps"] = by_cand.get(r["candidate_id"], [])
        statements = []
        for c in r["a18"]:
            statements.append(c.get("pass_b_statement", ""))
            statements += list(c.get("pass_b_boundary_statements", ()))
        claim = rel.a18_topology_claim(*statements)
        a18_open = (True if claim == rel.OPEN
                    else False if claim == rel.CLOSED else None)
        b = r["boundary"]
        open_mm = 0.0 if b is None else sum(
            s.length_mm for s in b.segments if s.role == cg.OPEN_EDGE)
        has_portal = bool(b is not None and b.contains_artificial_topology)
        portal_ev = [] if b is None else [
            e for s in b.segments if s.role == cg.VIRTUAL_PORTAL_BOUNDARY
            for e in (s.evidence or ())]
        cad_open = bool(open_mm > cg.SNAP_MM)
        vrow2 = v2_by.get(r["candidate_id"], {})
        vrow1 = v1_by.get(r["candidate_id"], {})
        r["v2_statuses"] = tuple(vrow2.get("statuses", ()))
        r["v1"] = vrow1
        r["v2"] = vrow2
        decision = arb.arbitrate(
            a18_says_open=a18_open, cad_open=cad_open,
            cad_has_portal=has_portal, portal_evidence=portal_ev,
            ambiguous_band_on_ring=r["ambiguous_on_ring"],
            v1_open_sides=vrow1.get("OPEN_SIDES"),
            v2_statuses=r["v2_statuses"])
        r["arbitration"] = decision
        dims = dqa.dimension_cross_check(b, gf["dimensions"])
        r["dqa"] = dqa.check(
            boundary=b, interval_roles=iv_lookup,
            distinct_label_groups=set(r["labels_inside"]),
            dimension_rows=dims, overlap_relations=r["overlaps"],
            a18_topology_conflict=(decision["ARBITRATION_STATE"]
                                   == arb.UNRESOLVED and a18_open is not None),
            ambiguous_band_on_ring=r["ambiguous_on_ring"])
        r["decision"] = release_decision(row=r, iv_by_id=iv_by_id,
                                         arbitration=decision)
        r["region"].released = bool(r["decision"]["released"])
        arb_rows.append({
            "CANDIDATE_ID": r["candidate_id"],
            "identity": r["group"].english_token,
            "A18_CANDIDATE_IDS": [c["candidate_id"] for c in r["a18"]],
            "a18_topology_claim": claim,
            **decision,
            "V1_OBSERVATION_SUMMARY": vrow1.get("summary", ""),
            "V2_STATUSES": list(r["v2_statuses"]),
            "V2_REASONS": vrow2.get("reasons", []),
        })

    src = _source(st["prep"], gf, a)
    released = [r for r in rows if r["region"].released]
    withheld = [r for r in rows if not r["region"].released]

    _write(out, artifacts, "E1_2_A18_CAD_VISUAL_ARBITRATION_REGISTER.json", {
        "source": src,
        "STATES": list(arb.STATES),
        "neither_witness_is_final": arb.NEITHER_WITNESS_IS_FINAL,
        "only_unresolved_blocks_forever": arb.ONLY_UNRESOLVED_BLOCKS_FOREVER,
        "counts": {s: sum(1 for x in arb_rows
                          if x["ARBITRATION_STATE"] == s)
                   for s in arb.STATES},
        "rows": arb_rows,
    })

    _write(out, artifacts, "E1_2_CAD_GEOMETRY_REGISTER.json", {
        "source": src,
        "unit_of_role": "ATOMIC_ENTITY_INTERVAL",
        "unit_of_work": ("one trace per PHYSICAL or FUNCTIONAL label, from "
                         "established material INTERVALS only"),
        "outcome_counts": {o: sum(1 for r in rows
                                  if r["region"].outcome == o)
                           for o in er.OUTCOMES},
        "released_regions": len(released),
        "withheld_regions": len(withheld),
        "closure_is_not_a_target": CLOSURE_IS_NOT_A_TARGET,
        "RELEASE_CONDITIONS": list(RELEASE_CONDITIONS),
        "regions": [{**r["region"].record(),
                     "LABEL_GROUP": r["group"].group_id,
                     "LABEL_CLASS": r["label_class"],
                     "seeded_from": lg.VISIBLE_LABEL_CENTROID,
                     "seed_mm": [round(r["seed"][0], 2),
                                 round(r["seed"][1], 2)],
                     "ambiguous_bands_on_the_ring":
                         list(r["ambiguous_on_ring"]),
                     "RELEASE_DECISION": r["decision"],
                     "ARBITRATION": r["arbitration"],
                     "DETERMINISTIC_QA": {
                         k: v for k, v in r["dqa"].items()
                         if k != "dimension_cross_check"},
                     "V2_STATUSES": list(r["v2_statuses"]),
                     "OVERLAP_RELATIONS": r["overlaps"]}
                    for r in rows],
        "frozen_parameters": {
            "cad_geometry": cg.frozen_parameters(),
            "e1_region": er.frozen_parameters(),
            "atomic_interval": ai.frozen_parameters(),
            "interval_role": ir.frozen_parameters(),
            "deterministic_qa": dqa.frozen_parameters(),
            "visual_challenger": vc.frozen_parameters(),
            "arbitration": arb.frozen_parameters(),
            "label_ontology": lo.frozen_parameters()},
    })

    _write(out, artifacts, "E1_2_WITHHELD_GEOMETRY_REGISTER.json", {
        "source": src,
        "rule": CLOSURE_IS_NOT_A_TARGET,
        "withheld": len(withheld),
        "by_failed_condition": {c: sum(1 for r in withheld
                                       if c in r["decision"]["failed"])
                                for c in RELEASE_CONDITIONS},
        "rows": [{"CANDIDATE_ID": r["candidate_id"],
                  "identity": r["group"].english_token,
                  "OUTCOME": r["region"].outcome,
                  "failed_release_conditions": r["decision"]["failed"],
                  "DETERMINISTIC_QA_STATE":
                      r["dqa"]["DETERMINISTIC_QA_STATE"],
                  "V2_STATUSES": list(r["v2_statuses"]),
                  "ARBITRATION_STATE":
                      r["arbitration"]["ARBITRATION_STATE"],
                  "ambiguous_bands_on_the_ring":
                      list(r["ambiguous_on_ring"]),
                  "why": ("E1.2 withheld it because these release conditions "
                          "failed: "
                          + "; ".join(r["decision"]["failed"])
                          + ". " + er.WITHHOLD_RATHER_THAN_REPAIR),
                  "what_the_region_tracer_said": r["region"].why}
                 for r in withheld],
    })

    _write(out, artifacts, "E1_2_COMPLETENESS_REGISTER.json", {
        "source": src,
        "denominator_rule": lo.SITE_CONTEXT_IS_NOT_A_SPACE,
        "label_classes": ontology["counts"],
        "PHYSICAL_AND_FUNCTIONAL_CANDIDATES":
            ontology["physical_and_functional_candidates"],
        "SITE_CONTEXT": ontology["site_context"],
        "OTHER_ANNOTATIONS": ontology["other_annotations"],
        "UNRESOLVED": ontology["unresolved"],
        "candidates_traced": len(rows),
        "released": len(released),
        "withheld": len(withheld),
        "a18_candidates_considered": len(st["cand_json"]),
        "CAD_IDENTITY_WITH_NO_A18_CANDIDATE": sorted(
            r["group"].english_token for r in rows if not r["a18"]),
    })

    _write(out, artifacts, "E1_2_DELTA_FROM_E1_1.json",
           _delta(rows, interp, ontology, a))

    # the frozen visual registers, answers folded in
    v1["status"] = "FROZEN"
    v1["answers"] = list(v1.get("answers", []))
    _write(out, artifacts, "E1_2_VISUAL_V1_REGISTER.json", v1)
    v2["status"] = "FROZEN"
    v2["answers"] = list(v2.get("answers", []))
    _write(out, artifacts, "E1_2_VISUAL_V2_CHALLENGE_REGISTER.json", v2)

    # overlays
    rgn = gf["region"]
    reg_r = rq.register(a.raster, gf["primitives"],
                        extent=(rgn.x0, rgn.y0, rgn.x1, rgn.y1))
    sheet = rq.Sheet(reg_r)
    whole = _whole_floor(sheet, reg_r, gf, interp, rows,
                         out / "E1_2_GROUND_FLOOR_ON_THE_SOURCE_SHEET.png")
    if whole:
        artifacts["E1_2_GROUND_FLOOR_ON_THE_SOURCE_SHEET.png"] = whole[prov.RAW]
    locals_ = candidate_overlays(sheet, reg_r, gf, interp, rows,
                                 out / "local_overlays")
    for row in locals_:
        artifacts[f"local_overlays/{Path(row['file']).name}"] = row[prov.RAW]
    for d, pat in ((out / "visual" / "v1_source_only", "visual/v1_source_only"),
                   (out / "visual" / "v2_overlays", "visual/v2_overlays")):
        if d.exists():
            for f in sorted(d.glob("*.png")):
                artifacts[f"{pat}/{f.name}"] = _sha(f)
    # The per-candidate V1 records are what the cold source-only pass
    # actually said, frozen one file per candidate before any proposal was
    # shown. They are the evidence a reviewer reads against the overlays,
    # so the freeze hashes them rather than only the collected register.
    v1_frozen = out / "visual" / "v1_frozen_per_candidate"
    if v1_frozen.exists():
        for f in sorted(v1_frozen.glob("*.json")):
            artifacts[f"visual/v1_frozen_per_candidate/{f.name}"] = _sha(f)
    _write(out, artifacts, "E1_2_OVERLAY_INDEX.json", {
        "whole_floor": whole,
        "local_overlays": locals_,
        "v1_source_only_crops": "visual/v1_source_only/",
        "v2_challenge_overlays": "visual/v2_overlays/",
        "v1_frozen_answers_per_candidate":
            "visual/v1_frozen_per_candidate/",
        "drawn_on": "THE_ORIGINAL_SOURCE_SHEET",
        "an_overlay_anchors_a_reader": vc.AN_OVERLAY_ANCHORS_A_READER,
    })
    artifacts["E1_2_INPUT_MANIFEST.json"] = _sha(
        out / "E1_2_INPUT_MANIFEST.json")

    freeze = {
        "E1_2_MODEL": E1_2_MODEL,
        "RUN_ID": RUN_ID,
        "E1_2_RUN_CLASS": CONTROLLED_INTEGRATION_REGRESSION,
        "supersedes_nothing": ("E1 and E1.1 are preserved exactly as "
                               "frozen. This is a separate iteration in "
                               "its own directory"),
        "E1_2_CURRENT_RUN_BENCHMARK_INPUTS": "NONE",
        "what_the_external_review_supplied": (
            "named structural defects in E1.1's role model and no "
            "quantity. No expected area, target dimension or benchmark "
            "number entered this run"),
        "modules_written_for_E1_2": list(E1_2_NEW_MODULES),
        "modules_carried_forward_unchanged": list(CARRIED_FORWARD),
        "modules_with_benchmark_informed_lineage":
            list(BENCHMARK_INFORMED_LINEAGE),
        "SOURCE_HASHES": {
            "cad_decode": src["decode_sha256"],
            "NORMALIZATION_HASH": src["NORMALIZATION_HASH"],
            "source_sheet": _sha(a.raster) if Path(a.raster).exists() else "",
            "e1_1_freeze": _sha(Path(a.prior_e1_1) / "E1_1_FREEZE.json")
            if (Path(a.prior_e1_1) / "E1_1_FREEZE.json").exists() else "",
        },
        "CODE_VERSION_HASHES": code_hashes(),
        "MODEL_HASHES": {"atomic_interval": ai.model_hash(),
                         "interval_role": ir.model_hash(),
                         "label_ontology": lo.model_hash(),
                         "deterministic_qa": dqa.model_hash(),
                         "visual_challenger": vc.model_hash(),
                         "arbitration": arb.model_hash(),
                         "admission_ledger": led.model_hash(),
                         "e1_2_inputs": ei2.model_hash(),
                         "cad_geometry": cg.model_hash(),
                         "e1_region": er.model_hash()},
        "ARTIFACTS": artifacts,
        "NOT_HASHED_AND_WHY": {
            "E1_2_FREEZE.json":
                "the freeze cannot carry its own hash. Its integrity is "
                "E1_2_RUN_HASH, taken over everything above",
            "_E1_2_ARTIFACTS_GEOMETRY.json":
                "working state handed from the geometry phase to the "
                "finalize phase. Every register it points at is hashed "
                "above; it is not itself part of the frozen record",
            "_E1_2_STATE.json":
                "working state handed between phases, as above",
        },
        "COUNTS": {
            "entities": interp["roles"]["entity_count"],
            "intervals": interp["roles"]["interval_count"],
            "entities_with_more_than_one_role":
                interp["roles"]["entities_with_more_than_one_role"],
            "intervals_that_may_bound_material":
                interp["roles"]["intervals_that_may_bound_material"],
            "physical_and_functional_candidates":
                ontology["physical_and_functional_candidates"],
            "site_context_annotations": ontology["site_context"],
            "released": len(released),
            "withheld": len(withheld),
            "columns_established":
                interp["roles"]["columns"].get("established_as_column", 0),
            "column_candidates_unresolved":
                interp["roles"]["columns"].get("unresolved", 0),
        },
        "what_E1_2_did_not_do": [
            "no benchmark, Excel, reconciliation, manual take-off, "
            "corrected area or external grading was opened",
            "no area was compared with anything",
            "no quantity was computed",
            "no geometry was repaired to make a region close",
            "the visual challenger moved no coordinate and produced no "
            "polygon",
            "E1 and E1.1 were not modified, rerun or overwritten",
        ],
    }
    freeze["E1_2_RUN_HASH"] = prov.canonical_sha256(freeze)
    (out / "E1_2_FREEZE.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8")

    print(json.dumps({
        "phase": "finalize",
        "candidates": len(rows),
        "released": len(released),
        "withheld": len(withheld),
        "arbitration": {s: sum(1 for x in arb_rows
                               if x["ARBITRATION_STATE"] == s)
                        for s in arb.STATES},
        "deterministic_qa": {s: sum(
            1 for r in rows if s in r["dqa"]["DETERMINISTIC_QA_STATE"])
            for s in dqa.QA_STATES},
        "v2": {s: sum(1 for r in rows if s in r["v2_statuses"])
               for s in vc.V2_STATUSES},
        "by_failed_condition": {c: sum(1 for r in withheld
                                       if c in r["decision"]["failed"])
                                for c in RELEASE_CONDITIONS},
        "artifacts": len(artifacts) + 1,
        "E1_2_RUN_HASH": freeze["E1_2_RUN_HASH"][:16],
    }, indent=2))
    return 0


def _delta(rows, interp, ontology, a) -> dict:
    path = Path(a.prior_e1_1) / "E1_1_CAD_GEOMETRY_REGISTER.json"
    if not path.exists():
        return {"available": False,
                "why": "E1.1's geometry register was not admitted"}
    prior = json.loads(path.read_text(encoding="utf-8"))
    old = {}
    for r in prior.get("regions", ()):
        tok = (r.get("label_as_drawn") or "").upper()
        if tok:
            old.setdefault(tok, []).append(r)
    label_class = {r.group_id: r.label_class for r in ontology["rows"]}
    counts, out_rows = {}, []
    seen = set()
    for r in rows:
        tok = r["group"].english_token
        seen.add(tok)
        was = old.get(tok, [])
        was_rel = any(x.get("RELEASED") for x in was)
        now_rel = bool(r["region"].released)
        reasons = []
        if r["ambiguous_on_ring"]:
            reasons.append(AMBIGUOUS_BAND_FOUND)
        if any(iv.role == ir.COLUMN_CANDIDATE_UNRESOLVED
               for iv in interp["roles"]["flat"]):
            pass
        if len({iv.role for oid in {s.object_id.split("#")[0]
                                    for s in (r["boundary"].segments
                                              if r["boundary"] else ())}
                for iv in interp["roles"]["intervals"].get(
                    oid.replace("E1_2:", ""), ())}) > 1:
            reasons.append(INTERVAL_ROLE_SPLIT)
        if vc.VISUALLY_CONSISTENT not in set(r["v2_statuses"]) \
                and r["v2_statuses"]:
            reasons.append(VISUAL_CHALLENGE_VETO)
        if r["arbitration"]["ARBITRATION_STATE"] not in (arb.UNRESOLVED,):
            reasons.append(ARBITRATION_RESOLVED)
        if was_rel and not now_rel:
            reasons.insert(0, RELEASE_TO_WITHHOLD)
        elif now_rel and not was_rel:
            reasons.insert(0, WITHHOLD_TO_RELEASE)
        elif was_rel and now_rel:
            reasons.insert(0, NO_CHANGE)
        if not reasons:
            reasons.append(NO_CHANGE)
        for x in reasons:
            counts[x] = counts.get(x, 0) + 1
        out_rows.append({
            "identity": tok,
            "E1_2_CANDIDATE_ID": r["candidate_id"],
            "LABEL_CLASS": label_class.get(r["group"].group_id),
            "E1_1_RELEASED": was_rel,
            "E1_2_RELEASED": now_rel,
            "E1_1_OUTCOME": sorted({x.get("OUTCOME") for x in was}),
            "E1_2_OUTCOME": r["region"].outcome,
            "ARBITRATION_STATE": r["arbitration"]["ARBITRATION_STATE"],
            "V2_STATUSES": list(r["v2_statuses"]),
            "CHANGE_REASONS": reasons,
            "why": "; ".join(r["decision"]["failed"])
                   or "all release conditions hold",
        })
    dropped = sorted(set(old) - seen)
    reclass = [r.record() for r in ontology["rows"]
               if r.label_class not in lo.IN_THE_COMPLETENESS_DENOMINATOR
               and r.text.upper() in old]
    for _ in reclass:
        counts[LABEL_RECLASSIFIED] = counts.get(LABEL_RECLASSIFIED, 0) + 1
    return {
        "available": True,
        "prior_register": str(path),
        "prior_register_sha256": _sha(path),
        "DELTA_REASONS": list(DELTA_REASONS),
        "reason_counts": counts,
        "rows": out_rows,
        "identities_in_E1_1_no_longer_physical_space_candidates": [
            {"identity": r["text"], "LABEL_CLASS": r["LABEL_CLASS"],
             "EVIDENCE": r["EVIDENCE"], "why": r["why"]} for r in reclass],
        "identities_in_E1_1_not_carried_forward": dropped,
        "no_quantity_is_compared": (
            "this register compares outcomes, roles, topology and label "
            "classes. No area or length of either iteration is compared"),
    }


def _whole_floor(sheet, reg, gf, interp, rows, path):
    from PIL import ImageDraw, ImageFont
    rgn = gf["region"]
    centre = ((rgn.x0 + rgn.x1) / 2.0, (rgn.y0 + rgn.y1) / 2.0)
    half = max(rgn.x1 - rgn.x0, rgn.y1 - rgn.y0) / 2.0 + 500
    got = _frame(sheet, reg, centre, half, (3400, 3400))
    if got is None:
        return {}
    img, to_px, _box = got
    draw = ImageDraw.Draw(img)
    by_id = {p.object_id: p for p in gf["primitives"]}
    for oid, ivs in interp["roles"]["intervals"].items():
        parent = by_id.get(oid)
        if parent is None:
            continue
        for iv in ivs:
            if iv.role in (ir.CABINET_FRONT, ir.COUNTER_EDGE, ir.CASEWORK,
                           ir.POOL_INTERNAL_GEOMETRY, ir.CONSTRUCTION_LINE):
                colour = CASEWORK_COLOUR
            elif iv.role == ir.AMBIGUOUS_PAIRED_BAND:
                colour = AMBIGUOUS_COLOUR
            else:
                continue
            seg = cg._as_segment(IntervalPrim(parent, iv))
            pts = [to_px(x, y) for x, y in seg.points(tol_mm=2.0)]
            if len(pts) >= 2:
                draw.line(pts, fill=colour, width=3)
    for r in rows:
        if r["boundary"] is None:
            continue
        for seg in r["boundary"].segments:
            _draw(draw, seg, to_px)
    if reg.rotation_deg:
        img = img.rotate(-reg.rotation_deg, expand=True)
    img.save(path)
    return {"file": Path(path).name, "pixels": list(img.size),
            "legend": list(OVERLAY_LEGEND), prov.RAW: _sha(path)}


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
    ap.add_argument("--rules",
                    default="data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")
    ap.add_argument("--sandbox", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.phase == "geometry":
        if not a.sandbox:
            ap.error("--sandbox is required for the geometry phase")
        phase_geometry(a)
        return 0
    if a.phase == "v2-inputs":
        return phase_v2_inputs(a)
    return phase_finalize(a)


if __name__ == "__main__":
    raise SystemExit(main())
