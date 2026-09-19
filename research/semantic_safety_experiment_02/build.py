"""Build SEMANTIC_SAFETY_EXPERIMENT_02: features, legible crops, packages.

Order enforced here: the protocol is hashed, then features are grown from
source geometry, then crops are rendered and PROVED legible, then the
sample is admitted, then the blind reference packages are assembled. No
A19 output and no E1.4 semantic classification reaches a reference package.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import time
from pathlib import Path

from engine import cad_geometry as cg
from engine import interval_role as ir
from research.semantic_safety_experiment_02 import features as F
from research.semantic_safety_experiment_02 import protocol as P
from research.semantic_safety_experiment_02 import render as R
from tools import run_e1_2 as r12
from tools import run_e1_3 as r13
from tools import run_e1_4 as r14

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")

CONTEXT_MARGIN_MM, CONTEXT_MIN_HALF_MM = 4000.0, 5000.0
FEATURE_MARGIN_MM, FEATURE_MIN_HALF_MM = 700.0, 1100.0
DETAIL_MARGIN_MM, DETAIL_MIN_HALF_MM = 200.0, 420.0
PIXELS = (1400, 1400)
# A marked crop is re-rendered larger until the SAME placement tests pass.
# Fourteen parallel lines across a wall thickness put their anchors a few
# pixels apart at the base size, and no leader can escape that without
# passing under a neighbour. More pixels per millimetre separates the
# anchors; it relaxes no test.
MARKED_PIXEL_LADDER = ((1400, 1400), (2000, 2000), (2800, 2800),
                       (3600, 3600))

# General CAD layer-naming conventions, not a lookup for this project.
WINDOW_NAMES = ("W", "WIN", "WINDOW", "GL", "GLAZ", "GLAZING")
DOOR_NAMES = ("D", "DR", "DOOR")
COLUMN_NAMES = ("COL", "S-COL", "STRUCT")
HOMOGENEOUS_SHARE = 0.9

# A stratum name says which safety category the selection was AIMING at,
# so in front of a reader it would be a hint at the answer. Every one of
# them is screened out of the blind package along with the rest.
FORBIDDEN_IN_A_BLIND_PACKAGE = (
    "PASS_A", "PASS_B", "A19", "E1_4", "SEMANTIC_ENTITY_ROLE",
    "REFERENCE_ROLE_DISTRIBUTION", "CHECKER_COMPARISON",
    "SAFETY_SAMPLE", "STRATUM", "SELECTED_BECAUSE",
) + tuple(name for name, _, _ in P.STRATA)


class Args:
    decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
    a18_dir = "data/runs/7757/blind/A18-GF-001"
    raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    rules = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"
    prior_e1_3 = "data/runs/7757/e1_3"
    sandbox = ""
    v2_sandbox = ""
    out = "data/runs/7757/e1_4"


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (body if isinstance(body, str)
            else json.dumps(body, indent=2, ensure_ascii=False,
                            default=str) + "\n")
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _layer_kinds(intervals):
    """What each layer is, from its own name and its own homogeneity."""
    by, kinds = {}, {}
    for iv in intervals:
        by.setdefault(str(iv.layer), []).append(iv)
    for lay, rows in by.items():
        up = lay.upper()
        tags = set()
        if any(up == n or up.startswith(n + "-") or up.startswith(n + "_")
               for n in WINDOW_NAMES):
            tags.add("WINDOW_LAYER")
        if any(up == n or up.startswith(n + "-") or up.startswith(n + "_")
               for n in DOOR_NAMES):
            tags.add("DOOR_LAYER")
        if any(n in up for n in COLUMN_NAMES):
            tags.add("STRUCTURAL_LAYER")
        n = len(rows)
        share = {}
        for iv in rows:
            share[iv.role] = share.get(iv.role, 0) + 1
        for role, c in share.items():
            if c / n >= HOMOGENEOUS_SHARE:
                if role == ir.DOOR:
                    tags.add("DOOR_LAYER")
                if role in (ir.DIMENSION_LINE, ir.DIMENSION_WITNESS,
                            ir.ANNOTATION, ir.LEVEL_OR_GRID_ANNOTATION):
                    tags.add("ANNOTATION_LAYER")
        kinds[lay] = sorted(tags)
    return kinds


def _signatures(feat, *, layer_kinds, doors, stairs, material, gaps,
                hull_skin, sem):
    """Mechanical source signatures. No claim about what the feature is."""
    from shapely.geometry import LineString, Point
    ms = feat["_members"]
    box = feat["bounding_box_mm"]
    sig = {}

    pair = False
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            if not F.parallel(a, b):
                continue
            off, ov = F.offset_overlap(a, b)
            if ov >= P.MIN_PARALLEL_OVERLAP_MM and 75.0 <= off <= 400.0:
                pair = True
    sig["A_PAIR_AT_A_WALL_THICKNESS"] = pair

    lays = {str(m.layer) for m in ms}
    sig["LAYERS"] = sorted(lays)
    sig["LAYER_KINDS"] = sorted({k for L in lays
                                 for k in layer_kinds.get(L, ())})
    sig["ON_A_WINDOW_LAYER"] = "WINDOW_LAYER" in sig["LAYER_KINDS"]
    sig["ON_A_DOOR_LAYER"] = "DOOR_LAYER" in sig["LAYER_KINDS"]
    sig["MEMBER_ROLES"] = sorted({m.role for m in ms})
    sig["ON_AN_ANNOTATION_LAYER"] = "ANNOTATION_LAYER" in sig["LAYER_KINDS"]
    sig["ON_A_STRUCTURAL_LAYER"] = "STRUCTURAL_LAYER" in sig["LAYER_KINDS"]

    g = LineString([(box[0], box[1]), (box[2], box[3])]).envelope
    sig["SPANS_A_RECORDED_GAP"] = any(
        g.buffer(P.JOIN_MM).intersects(
            LineString([tuple(x["start_mm"]), tuple(x["end_mm"])]))
        for x in gaps if x.get("start_mm") and x.get("end_mm"))
    sig["SPANS_A_RECORDED_PORTAL"] = any(
        x.get("IS_A_PORTAL") and g.buffer(P.JOIN_MM).intersects(
            LineString([tuple(x["start_mm"]), tuple(x["end_mm"])]))
        for x in gaps if x.get("start_mm") and x.get("end_mm"))

    def _near(ids, reach):
        for m in ms:
            lm = LineString([m.start_mm, m.end_mm])
            for o in ids:
                if lm.distance(LineString([o.start_mm, o.end_mm])) <= reach:
                    return True
        return False

    sig["DOOR_GEOMETRY_IS_NEAR"] = _near(doors, P.DOOR_REACH_MM)
    sig["STAIR_GEOMETRY_IS_NEAR"] = _near(stairs, 1500.0)

    fitted = False
    for m in ms:
        for o in material:
            if o.interval_id in {x.interval_id for x in ms}:
                continue
            if not F.parallel(m, o):
                continue
            off, ov = F.offset_overlap(m, o)
            if ov >= P.MIN_PARALLEL_OVERLAP_MM and 450.0 <= off <= 800.0:
                fitted = True
                break
        if fitted:
            break
    sig["PARALLEL_TO_MATERIAL_AT_FITTED_UNIT_DEPTH"] = fitted

    sig["A_SMALL_CLOSED_LOOP"] = (
        feat["extent_mm"] <= 1200.0 and len(ms) >= 4
        and any(F.endpoints_meet(ms[0], m) for m in ms[1:]))

    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    sig["IN_THE_ENVELOPE_BAND"] = bool(
        hull_skin is not None
        and hull_skin.distance(Point(cx, cy)) <= P.ENVELOPE_BAND_MM)

    statuses = {(sem.get(m.interval_id) or {}).get("LINE_SEMANTICS_STATUS")
                for m in ms}
    sig["LINE_SEMANTICS_STATUSES"] = sorted(s for s in statuses if s)
    sig["NOT_IN_THE_VISIBLE_CUT_PLANE"] = bool(
        statuses & {"OVERHEAD_GEOMETRY", "BELOW_CUT_PLANE_GEOMETRY",
                    "STAIR_PROJECTION"})
    sig["IN_THE_CUT_PLANE"] = "VISIBLE_MATERIAL_FACE" in statuses

    sig["HAS_A_CURVE"] = any(m.kind in ("ARC", "CIRCLE") for m in ms)
    sig["UNSETTLED_BY_THE_DETERMINISTIC_LAYER"] = any(
        m.role in (ir.UNKNOWN, ir.COLUMN_CANDIDATE_UNRESOLVED,
                   ir.AMBIGUOUS_PAIRED_BAND) for m in ms)
    return sig


ANNOTATION_ROLES = (ir.DIMENSION_LINE, ir.DIMENSION_WITNESS,
                    ir.ANNOTATION, ir.LEVEL_OR_GRID_ANNOTATION)
JOINERY_ROLES = (ir.CASEWORK, ir.CABINET_FRONT, ir.COUNTER_EDGE,
                 ir.FIXTURE, ir.FURNITURE)
STRUCTURAL_ROLES = (ir.COLUMN, ir.COLUMN_CANDIDATE_UNRESOLVED)


def _stratum(sig):
    """The first rule that fits, in the declared order.

    Every input below is FROZEN DETERMINISTIC evidence: the semantic role
    E1.4 already established for each interval, the frozen gap and door
    registers, the drawing's own layer names, and line semantics. No A19
    answer, no reference label from any round, no checker answer, no room
    geometry, no benchmark area and no closure result takes any part in
    it. The question asked here is which source signatures are LIKELY to
    produce a category - never which examples will be answered correctly.

    A stratum's NAME says what it is TRYING to produce. It does not say
    what the feature is. The reference is the only thing that may say
    that, and no stratum name ever reaches a reader.
    """
    roles = set(sig["MEMBER_ROLES"])

    # FIRST, and deliberately so: a feature every one of whose members is
    # already established as drawing apparatus may reach no other
    # stratum, whatever its geometry looks like. SAFETY_SAMPLE_01 lacked
    # this rule and came back half annotation
    if roles and roles <= set(ANNOTATION_ROLES):
        return "DIMENSION_OR_ANNOTATION_CANDIDATE"
    if (ir.MATERIAL_WALL_FACE in roles
            and sig["A_PAIR_AT_A_WALL_THICKNESS"]):
        return "SOLID_SEPARATOR_CANDIDATE"
    if sig["ON_A_WINDOW_LAYER"]:
        return "WINDOW_OR_GLAZED_CANDIDATE"
    if (sig["SPANS_A_RECORDED_PORTAL"] or sig["ON_A_DOOR_LAYER"]
            or (sig["DOOR_GEOMETRY_IS_NEAR"]
                and ir.MATERIAL_WALL_FACE in roles)):
        return "DOOR_OR_OPENING_CANDIDATE"
    if roles & set(JOINERY_ROLES):
        return "COUNTER_CABINET_OR_FITTED_UNIT_CANDIDATE"
    if roles & set(STRUCTURAL_ROLES) or sig["ON_A_STRUCTURAL_LAYER"]:
        return "COLUMN_OR_OBSTACLE_CANDIDATE"
    if (ir.STAIR_GEOMETRY in roles
            or sig["NOT_IN_THE_VISIBLE_CUT_PLANE"]):
        return "STAIR_HIDDEN_OR_OVERHEAD_CANDIDATE"
    if roles <= {ir.UNKNOWN} and sig["IN_THE_CUT_PLANE"]:
        return "GENUINELY_AMBIGUOUS_HIGH_IMPACT"
    if ir.MATERIAL_WALL_FACE in roles:
        return "SOLID_SEPARATOR_CANDIDATE"
    return "GENUINELY_AMBIGUOUS_HIGH_IMPACT"


def _crop_plan(feat):
    e = feat["extent_mm"]
    return [
        ("CONTEXT", max(e / 2.0 + CONTEXT_MARGIN_MM, CONTEXT_MIN_HALF_MM),
         False),
        ("FEATURE", max(e / 2.0 + FEATURE_MARGIN_MM, FEATURE_MIN_HALF_MM),
         True),
        ("DETAIL", max(e / 2.0 + DETAIL_MARGIN_MM, DETAIL_MIN_HALF_MM),
         True),
    ]


def _render(sheet, reg, feat, by_id, labels, half, marked, path,
            pixels=PIXELS):
    got = r12._frame(sheet, reg,
                     ((feat["bounding_box_mm"][0]
                       + feat["bounding_box_mm"][2]) / 2.0,
                      (feat["bounding_box_mm"][1]
                       + feat["bounding_box_mm"][3]) / 2.0),
                     half, pixels)
    if got is None:
        return None, {}, {"ALL": "THE_FRAME_COULD_NOT_BE_MADE"}
    img, to_px, box = got
    img = img.convert("RGB")
    if not marked:
        img.save(path)
        return {"path": str(path), "box_mm": [round(v, 3) for v in box],
                "pixels": list(pixels), "MARKED": False,
                "SHA256": None}, {}, {}
    members_px, anchors, missing = {}, {}, {}
    for lab, iv in labels.items():
        parent = by_id.get(iv.parent_object_id)
        if parent is None:
            missing[lab] = "NO_SOURCE_GEOMETRY"
            continue
        try:
            pts = [to_px(x, y) for x, y in cg._as_segment(
                r12.IntervalPrim(parent, iv)).points(tol_mm=2.0)]
        except Exception:
            missing[lab] = "NO_SOURCE_GEOMETRY"
            continue
        inside = [p for p in pts
                  if 0 <= p[0] <= pixels[0] and 0 <= p[1] <= pixels[1]]
        if len(inside) < 2:
            missing[lab] = "A_TAGGED_MEMBER_IS_NOT_INSIDE_THE_CROP"
            continue
        members_px[lab] = pts
        # a leader may start anywhere along the member it names, so every
        # tag is offered feet in a declared order: the middle first, then
        # outward. They are spaced along the member BY LENGTH - v4 spaced
        # them by vertex index, which gave a straight segment only its
        # two ends
        picks = R.anchor_candidates(pts, pixels)
        if not picks:
            missing[lab] = "A_TAGGED_MEMBER_IS_NOT_INSIDE_THE_CROP"
            del members_px[lab]
            continue
        anchors[lab] = picks
    placed, failed = R.place_tags(anchors, pixels)
    failed.update(missing)
    R.draw(img, members_px, placed, failed)
    img.save(path)
    return ({"path": str(path), "box_mm": [round(v, 3) for v in box],
             "pixels": list(pixels), "MARKED": True, "SHA256": sha(path)},
            placed, failed)


def main() -> int:
    t0 = time.time()
    a = Args()
    OUT.mkdir(parents=True, exist_ok=True)
    keep = OUT / "safety_sample_01_apparatus_result"
    if not keep.exists():
        keep.mkdir(parents=True)
        for name in ("00_PROTOCOL.json",
                     "01_CANONICAL_FEATURE_REGISTER.json",
                     "02_RENDER_QA_REGISTER.json",
                     "03_REFERENCE_INPUT_MANIFEST.json",
                     "04_REFERENCE_A.json"):
            if (OUT / name).exists():
                shutil.move(str(OUT / name), str(keep / name))
        for d in ("blind_sandbox", "crops", "reference_raw"):
            if (OUT / d).exists():
                shutil.move(str(OUT / d), str(keep / d))
        (keep / "APPARATUS_RESULT.json").write_text(
            json.dumps({
                "SAMPLE_ID": "SAFETY_SAMPLE_01",
                "RESULT_CLASS": "APPARATUS_AND_SAMPLING_RESULT",
                "THIS_IS_NOT_A_FAILED_DRAFT": (
                    "it was run honestly, start to finish, and it "
                    "measured something true about the sampling "
                    "strategy. It is preserved exactly as run and is not "
                    "overwritten, re-scored or re-read"),
                "THE_FINDING":
                    P.SAFETY_SAMPLE_01_IS_A_RESULT_NOT_A_MISTAKE,
                "SUCCESSOR": {
                    "SAMPLE_ID": P.SAMPLE_ID,
                    "RELATION": "NEW_TARGETED_ROUND_NOT_A_CORRECTION",
                    "safety_sample_02_is_a_new_round":
                        P.SAFETY_SAMPLE_02_IS_A_NEW_ROUND},
                "WHY": P.WHY_V3_WAS_SUPERSEDED,
                "the_reference_is_not_a_sampling_aid":
                    P.THE_REFERENCE_IS_NOT_A_SAMPLING_AID,
                "ITS_ANSWERS_TOOK_NO_PART_IN_SELECTING_SAFETY_SAMPLE_02":
                    True,
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    proto_hash = write(OUT / "00_PROTOCOL.json", P.record())

    st = r14._core(a)
    interp, gf = st["interp"], st["gf"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    sem = {r["INTERVAL_ID"]: r for r in st["semantics"]["ROWS"]}
    intervals = [iv for rows in interp["roles"]["intervals"].values()
                 for iv in rows]
    block_of = {iv.interval_id: (iv.provenance or {}).get("instance_path")
                or (iv.provenance or {}).get("block_path")
                for iv in intervals}
    t_core = time.time() - t0

    feats = F.build(intervals, block_of=block_of)

    from shapely.geometry import MultiPoint
    pts = [p for iv in intervals
           if iv.role in (ir.MATERIAL_WALL_FACE, ir.GLAZING, ir.COLUMN)
           for p in (iv.start_mm, iv.end_mm)]
    hull = MultiPoint(pts).convex_hull if len(pts) >= 3 else None
    skin = hull.boundary if hull is not None else None
    layer_kinds = _layer_kinds(intervals)
    doors = [iv for iv in intervals if iv.role == ir.DOOR]
    stairs = [iv for iv in intervals if iv.role == ir.STAIR_GEOMETRY]
    material = [iv for iv in intervals if iv.role == ir.MATERIAL_WALL_FACE]
    gaps = st["gaps"]["rows"]

    for f in feats:
        f["SIGNATURES"] = _signatures(
            f, layer_kinds=layer_kinds, doors=doors, stairs=stairs,
            material=material, gaps=gaps, hull_skin=skin, sem=sem)
        f["STRATUM"] = _stratum(f["SIGNATURES"])

    reg_ids = set(P.REGRESSION_SOURCE_INTERVALS)
    for f in feats:
        f["IS_THE_REGRESSION_FEATURE"] = bool(
            reg_ids & set(f["SOURCE_INTERVAL_IDS"]))

    # ---- render, prove legible, admit ------------------------------
    reg_sheet, sheet = r13._registered_sheet(a, gf)
    if sheet is None or not getattr(sheet, "ok", False):
        raise SystemExit("the source sheet did not register")

    crops_root = OUT / "crops"
    if crops_root.exists():
        shutil.rmtree(crops_root)

    def try_admit(f):
        if f["members"] > P.MAX_FEATURE_MEMBERS:
            return None, {"ADMITTED": False,
                          "WHY_NOT": "MORE_MEMBERS_THAN_THE_CAP",
                          "members": f["members"]}
        labels = {f"M{n:02d}": iv for n, iv in enumerate(
            sorted(f["_members"], key=lambda x: x.interval_id), start=1)}
        d = crops_root / f["CANONICAL_FEATURE_ID"]
        d.mkdir(parents=True, exist_ok=True)
        rows, qa = [], {}
        for level, half, marked in _crop_plan(f):
            clean, _, _ = _render(sheet, reg_sheet, f, by_id, labels, half,
                                  False, d / f"{level}_CLEAN.png")
            if clean:
                clean["SHA256"] = sha(d / f"{level}_CLEAN.png")
                rows.append({"LEVEL": level, "FILE": f"{level}_CLEAN.png",
                             "half_extent_mm": round(half, 3), **clean})
            if not marked:
                continue
            got = placed = failed = None
            for px in MARKED_PIXEL_LADDER:
                got, placed, failed = _render(
                    sheet, reg_sheet, f, by_id, labels, half, True,
                    d / f"{level}_MARKED.png", pixels=px)
                if got is None or not failed:
                    break
            if got:
                rows.append({"LEVEL": level, "FILE": f"{level}_MARKED.png",
                             "half_extent_mm": round(half, 3), **got})
            qa[level] = {
                "pixels_used": (got or {}).get("pixels"),
                "THE_LADDER_RELAXES_NO_TEST": (
                    "the same placement tests are applied at every size; "
                    "more pixels only give the leaders room"),
                "tags_required": len(labels),
                "tags_placed": len([k for k in placed if k not in failed]),
                "FAILURES": failed,
                "PER_TAG": {k: {"TAG_VISIBLE": k not in failed,
                                "TAG_TO_ENTITY_LINK_UNAMBIGUOUS":
                                    k not in failed,
                                "radius_px": v.get("radius_px"),
                                "direction_deg": v.get("direction_deg")}
                            for k, v in placed.items()},
            }
        gate = qa.get("FEATURE", {})
        clean = bool(gate) and not gate.get("FAILURES")
        # §13 and the render gate collide on one feature only: the doorway
        # holding the prior critical error, whose wall opening the drawing
        # overlays with a door block. It is admitted with the tags that
        # can be proved legible and the rest declared. No other feature
        # may enter this way.
        partial = (not clean) and bool(gate) and f["IS_THE_REGRESSION_FEATURE"]
        ok = clean or partial
        untagged = sorted((gate.get("FAILURES") or {}).keys())
        return ({"labels": labels, "crops": rows, "qa": qa,
                 "UNTAGGED_MEMBERS": untagged if partial else []}
                if ok else None,
                {"ADMITTED": ok,
                 "ADMISSION": ("FULLY_TAGGED" if clean else
                               P.PARTIAL_TAGGING_ADMISSION if partial
                               else None),
                 "WHY_NOT": (None if ok else
                             "A_TAG_COULD_NOT_BE_PLACED_LEGIBLY"),
                 "MEMBERS_SHOWN_WITHOUT_AN_INDIVIDUAL_TAG":
                     untagged if partial else [],
                 "FEATURE_LEVEL_QA": gate,
                 "DETAIL_LEVEL_QA": qa.get("DETAIL")})

    admitted, qa_rows, shortfalls = [], [], {}
    ordered = sorted(feats, key=lambda x: x["SOURCE_INTERVAL_IDS"][0])
    regression = [f for f in ordered if f["IS_THE_REGRESSION_FEATURE"]]

    def admit_one(f, why):
        got, qrow = try_admit(f)
        qa_rows.append({"CANONICAL_FEATURE_ID": f["CANONICAL_FEATURE_ID"],
                        "STRATUM": f["STRATUM"],
                        "SELECTED_BECAUSE": why, **qrow})
        if got is None:
            return False
        f["_render"] = got
        f["SELECTED_BECAUSE"] = why
        admitted.append(f)
        return True

    for f in regression:
        admit_one(f, "REGRESSION_RULE")

    for name, target, _ in P.STRATA:
        have = sum(1 for f in admitted if f["STRATUM"] == name)
        pool = [f for f in ordered if f["STRATUM"] == name
                and f not in admitted]
        for f in pool:
            if have >= target or len(admitted) >= P.SAMPLE_MAX:
                break
            if admit_one(f, "PER_STRATUM_TARGET"):
                have += 1
        if have < target:
            shortfalls[name] = {"admitted": have, "target": target,
                                "features_in_the_stratum": len(
                                    [x for x in ordered
                                     if x["STRATUM"] == name])}

    feat_hash = write(OUT / "01_CANONICAL_FEATURE_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "WHAT_A_CANONICAL_FEATURE_IS": P.WHAT_A_CANONICAL_FEATURE_IS,
        "GROUPING_RELATIONS": list(P.GROUPING_RELATIONS),
        "nothing_semantic_is_used_to_group":
            P.NOTHING_SEMANTIC_IS_USED_TO_GROUP,
        "EVERY_INTERVAL_BELONGS_TO_EXACTLY_ONE_FEATURE": True,
        "intervals_on_the_floor": len(intervals),
        "canonical_features_on_the_floor": len(feats),
        "intervals_accounted_for": sum(f["members"] for f in feats),
        "LAYER_KINDS_AS_THE_DRAWING_NAMES_THEM": layer_kinds,
        "HOW_A_LAYER_KIND_IS_DECIDED": (
            "by the layer's own name against a general CAD naming "
            "convention, or by the layer being homogeneous in one kind of "
            "geometry. It is a fact about the layer, not a claim about "
            "any feature"),
        "STRATUM_COUNTS": {n: sum(1 for f in feats if f["STRATUM"] == n)
                           for n, _, _ in P.STRATA},
        "selected": len(admitted),
        "shortfalls": shortfalls,
        "do_not_fabricate_to_meet_a_quota": P.DO_NOT_FABRICATE_TO_MEET_A_QUOTA,
        "REGRESSION_FEATURES_FOUND": [f["CANONICAL_FEATURE_ID"]
                                      for f in regression],
        "REGRESSION_RULE": P.REGRESSION_RULE,
        "SELECTED": [{k: v for k, v in f.items()
                      if not k.startswith("_")} for f in admitted],
        "ALL_FEATURES": [{"CANONICAL_FEATURE_ID": f["CANONICAL_FEATURE_ID"],
                          "STRATUM": f["STRATUM"],
                          "members": f["members"],
                          "extent_mm": f["extent_mm"],
                          "SOURCE_INTERVAL_IDS": f["SOURCE_INTERVAL_IDS"]}
                         for f in feats],
    })

    qa_hash = write(OUT / "02_RENDER_QA_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "RULES": list(P.RENDER_RULES),
        "ADMISSION_FAILS_WHEN": list(P.ADMISSION_FAILS_WHEN),
        "the_reader_is_not_asked_to_work_around_bad_markup":
            P.THE_READER_IS_NOT_ASKED_TO_WORK_AROUND_BAD_MARKUP,
        "THE_GATE_IS_THE_FEATURE_LEVEL_MARKED_CROP": (
            "the feature crop is where a reader answers about members, so "
            "it is the level that gates admission. The detail crop's QA is "
            "recorded beside it and does not gate"),
        "features_offered_to_the_gate": len(qa_rows),
        "features_admitted": sum(1 for r in qa_rows if r["ADMITTED"]),
        "features_refused": sum(1 for r in qa_rows if not r["ADMITTED"]),
        "PARTIAL_TAGGING_RULE": P.PARTIAL_TAGGING_RULE,
        "features_admitted_with_partial_tagging": sum(
            1 for r in qa_rows
            if r.get("ADMISSION") == P.PARTIAL_TAGGING_ADMISSION),
        "REFUSAL_REASONS": {r["WHY_NOT"]: sum(
            1 for x in qa_rows if x["WHY_NOT"] == r["WHY_NOT"])
            for r in qa_rows if r["WHY_NOT"]},
        "ROWS": qa_rows,
    })

    # ---- applicability + the blind packages ------------------------
    box_dir = OUT / "blind_sandbox"
    if box_dir.exists():
        shutil.rmtree(box_dir)
    ctx = (Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
           / "a19" / "pass_a_sandbox")
    ctx_file = next(ctx.glob("*/FLOOR_CONTEXT.txt"))

    manifest = []
    for f in admitted:
        fid = f["CANONICAL_FEATURE_ID"]
        d = box_dir / fid
        d.mkdir(parents=True)
        for c in f["_render"]["crops"]:
            shutil.copy(c["path"], d / c["FILE"])
        sig = f["SIGNATURES"]
        untagged = set(f["_render"].get("UNTAGGED_MEMBERS") or [])
        members = []
        for lab, iv in f["_render"]["labels"].items():
            if lab in untagged:
                continue
            parent = by_id.get(iv.parent_object_id)
            members.append({
                "MEMBER_LABEL": lab,
                "LAYER": str(iv.layer),
                "ENTITY_TYPE": str(iv.entity_type),
                "GEOMETRY_KIND": str(iv.kind),
                "LINETYPE": str(getattr(parent, "linetype", "") or ""),
                "BLOCK": str(block_of.get(iv.interval_id) or ""),
            })
        applic = {
            "CURVE_FAMILY": {
                "QUESTION_APPLICABILITY": bool(sig["HAS_A_CURVE"]),
                "APPLICABILITY_EVIDENCE":
                    "a tagged member is an ARC or a CIRCLE"
                    if sig["HAS_A_CURVE"] else
                    "no tagged member is a curve, so the question is not "
                    "asked"},
            "FENESTRATION_DETAIL": {
                "QUESTION_APPLICABILITY": bool(
                    sig["ON_A_WINDOW_LAYER"] or sig["ON_A_DOOR_LAYER"]
                    or sig["IN_THE_ENVELOPE_BAND"]),
                "APPLICABILITY_EVIDENCE":
                    f"layer kinds {sig['LAYER_KINDS']}, in the envelope "
                    f"band: {sig['IN_THE_ENVELOPE_BAND']}"},
            "DOOR_RELATION": {
                "QUESTION_APPLICABILITY": bool(sig["DOOR_GEOMETRY_IS_NEAR"]
                                               or sig["SPANS_A_RECORDED_GAP"]),
                "APPLICABILITY_EVIDENCE":
                    f"door geometry near: {sig['DOOR_GEOMETRY_IS_NEAR']}, "
                    f"spans a recorded gap: {sig['SPANS_A_RECORDED_GAP']}"},
        }
        task = {
            "CANONICAL_FEATURE_ID": fid,
            "WHAT_YOU_ARE_LOOKING_AT": (
                "one local architectural feature of a ground floor plan, "
                "marked in red with a lettered tag on a leader line for "
                "each of its members"),
            "CROPS": [c["FILE"] for c in f["_render"]["crops"]],
            "MARKED_MEMBERS": members,
            "MEMBERS_SHOWN_BUT_NOT_INDIVIDUALLY_TAGGED": len(untagged),
            "WHY_SOME_MEMBERS_CARRY_NO_TAG": (
                "these members are drawn on top of one another in the "
                "source, so no tag can point at one of them without "
                "pointing at another. They are drawn in the member colour "
                "so you can see them. Answer the feature's relation as "
                "usual, and do not give a member role for a member you "
                "cannot identify"
                if untagged else None),
            "QUESTIONS_THAT_APPLY_HERE": {
                k: v["QUESTION_APPLICABILITY"] for k, v in applic.items()},
            "APPLICABILITY_EVIDENCE": {
                k: v["APPLICABILITY_EVIDENCE"] for k, v in applic.items()},
            "PRIMARY_PHYSICAL_RELATIONS": list(P.PHYSICAL_RELATIONS),
            "SECONDARY_ASSEMBLY_TYPES": list(P.ASSEMBLY_TYPES),
            "TERTIARY_ENTITY_SUB_ROLES": list(P.ENTITY_SUB_ROLES),
            "CONFIDENCE_CLASSES": list(P.CONFIDENCE_CLASSES),
        }
        write(d / "TASK.json", task)
        shutil.copy(ctx_file, d / "FLOOR_CONTEXT.txt")
        f["_applic"] = applic
        manifest.append({
            "CANONICAL_FEATURE_ID": fid,
            "STRATUM": f["STRATUM"],
            "SELECTED_BECAUSE": f["SELECTED_BECAUSE"],
            "marked_members": len(members),
            "members_shown_without_an_individual_tag": len(untagged),
            "ADMISSION": ("PARTIAL_TAGGING_ADMISSION" if untagged
                          else "FULLY_TAGGED"),
            "crops": len(f["_render"]["crops"]),
            "TASK_SHA256": sha(d / "TASK.json"),
            "FLOOR_CONTEXT_SHA256": sha(d / "FLOOR_CONTEXT.txt"),
            "CROP_SHA256": {c["FILE"]: sha(d / c["FILE"])
                            for c in f["_render"]["crops"]},
            "QUESTIONS_THAT_APPLY_HERE": task["QUESTIONS_THAT_APPLY_HERE"],
        })

    leaks = []
    for p in sorted(box_dir.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".txt"):
            text = p.read_text(encoding="utf-8", errors="replace")
            for bad in FORBIDDEN_IN_A_BLIND_PACKAGE:
                if bad in text:
                    leaks.append({"file": str(p.relative_to(box_dir)),
                                  "carries": bad})
    if leaks:
        raise SystemExit(f"the blind sandbox is not blind: {leaks[:5]}")

    man_hash = write(OUT / "03_REFERENCE_INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SEES": list(P.REFERENCE_SEES),
        "DOES_NOT_SEE": list(P.REFERENCE_DOES_NOT_SEE),
        "THE_SANDBOX_WAS_SEARCHED_FOR_EVERY_FORBIDDEN_TOKEN":
            list(FORBIDDEN_IN_A_BLIND_PACKAGE),
        "NOTHING_FORBIDDEN_WAS_FOUND": True,
        "may_not_guess": P.THE_REFERENCE_MAY_NOT_GUESS,
        "no_irrelevant_question_reaches_the_reader":
            P.NO_IRRELEVANT_QUESTION_REACHES_THE_READER,
        "THE_SAME_SANDBOX_SERVES_THE_REFERENCE_A19_AND_THE_CHECKER": (
            "one set of crops and tags, three different briefs. Nobody "
            "sees anybody's answer"),
        "features": len(manifest),
        "STRATUM_COUNTS": {n: sum(1 for m in manifest if m["STRATUM"] == n)
                           for n, _, _ in P.STRATA},
        "TASKS": manifest,
    })

    print(json.dumps({
        "PROTOCOL_HASH": P.protocol_hash(),
        "00_PROTOCOL_SHA256": proto_hash,
        "01_CANONICAL_FEATURE_REGISTER_SHA256": feat_hash,
        "02_RENDER_QA_REGISTER_SHA256": qa_hash,
        "03_REFERENCE_INPUT_MANIFEST_SHA256": man_hash,
        "intervals_on_the_floor": len(intervals),
        "canonical_features_on_the_floor": len(feats),
        "features_offered_to_the_gate": len(qa_rows),
        "features_admitted": len(admitted),
        "features_refused_by_the_render_gate": sum(
            1 for r in qa_rows if not r["ADMITTED"]),
        "STRATUM_COUNTS_SELECTED": {
            n: sum(1 for f in admitted if f["STRATUM"] == n)
            for n, _, _ in P.STRATA},
        "shortfalls": shortfalls,
        "regression_feature_admitted": any(
            f["IS_THE_REGRESSION_FEATURE"] for f in admitted),
        "seconds_rebuilding_e1_4_evidence": round(t_core, 1),
        "seconds_total": round(time.time() - t0, 1),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
