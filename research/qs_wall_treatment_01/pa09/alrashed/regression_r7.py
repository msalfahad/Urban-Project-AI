"""Run the generic engine over this project's drawing, and report what it can and cannot settle.

This file is the only place the project and the engine meet.  It reads the same DWG the frozen takeoff read,
turns it into the generic engine's inputs, runs the generic pipeline, and compares the result with the frozen
artifact - as COMPARISON, never as a target.  Nothing here feeds a number back into the engine, and the engine
has no idea which project this is.

What changed in R6 is what the adapter HANDS OVER.  A door is now handed over as the features the CAD file
carries - an insertion point, a clear span, an orientation, a block name, a layer and the jamb marks that were
paired to measure it - and not as a rectangle whose depth was taken from whichever grid cell it fell in.  The
project's own retired window height is handed over as a retired claim rather than a live one.  And the window
standard is applied through each window's host room, not through one category chosen for the whole villa.

The frozen takeoff is opened read-only and is never rewritten.
"""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from engine.qs_core import (acceptance, admission as AD, dependency as DEP, evidence as EV,
                            geom, hosting as HO, identity, report_claims as RCL,
                            masonry as MA, pipeline, quantities as QY, room_category as RC,
                            space_validation as SV, transforms as TR)
from engine.qs_core.entities import GeometryComponent, KIND_COLUMN, KIND_FLOOR_REGION, KIND_WALL_BAND, Label
from engine.qs_core.spaces import Barrier
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import (final_takeoff as FT, geometry as G, labels as L,
                                                          owner_inputs as OI, quantities as Q, takeoff as TK,
                                                          window_standard as WS)

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN = OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json"
REVISION = "16-11-2025-R3"

# ---------------------------------------------------------------- source facts, each with its provenance
SOURCE_FACTS = {
    "TOLERANCE_M": {
        "VALUE": G.SNAP_MM / 1000.0,
        "WHY": "the drawing is authored to the millimetre and its faces are snapped at this distance"},
    "DRAFTING_RESOLUTION_M": {
        "VALUE": G.SNAP_MM / 1000.0,
        "WHY": "the finest distance this drawing distinguishes.  A gap narrower than this is two lines that "
               "did not meet; a real opening narrower than this could not have been drawn"},
    "SLIVER_MIN_DIMENSION_M": {
        "VALUE": 0.45,
        "WHY": "no usable space in a villa of this kind is narrower than this; anything narrower is structure "
               "or drafting residue"},
    "MAX_OPENING_SPAN_M": {
        "VALUE": G.MAX_CLOSURE_M,
        "WHY": "the widest gap in a wall line that an opening in this building could account for.  It can "
               "REJECT a join; continuity is still proved by something spanning the gap"},
    "WALL_LAYERS": {
        "VALUE": list(G.WALL_LAYERS),
        "WHY": "the layers this drawing puts wall lines on.  The source drawing a band on a wall layer is "
               "evidence that the band is WALL GEOMETRY.  It is not evidence of what the wall is built from, "
               "and the engine is not given it as such"},
    "DOOR_LAYERS": {"VALUE": list(G.DOOR_LAYERS),
                    "WHY": "the layer this drawing puts door blocks on; a block on it names a door"},
    "WINDOW_LAYERS": {"VALUE": list(G.WINDOW_LAYERS),
                      "WHY": "the layer this drawing puts window blocks on"},
    "MATERIAL_CLAIMS": {
        "VALUE": [],
        "WHY": "THIS SOURCE STATES NO WALL MATERIAL.  No annotation, legend or specification in the received "
               "documents says what any wall is built from, so no material claim is handed over and every "
               "wall's material identity is a question.  Handing over a claim the source does not make is "
               "how shape becomes material"},
}

TOLERANCE_M = SOURCE_FACTS["TOLERANCE_M"]["VALUE"]
DRAFTING_RESOLUTION_M = SOURCE_FACTS["DRAFTING_RESOLUTION_M"]["VALUE"]
SLIVER_MIN_DIMENSION_M = SOURCE_FACTS["SLIVER_MIN_DIMENSION_M"]["VALUE"]
MAX_OPENING_SPAN_M = SOURCE_FACTS["MAX_OPENING_SPAN_M"]["VALUE"]


# ---------------------------------------------------------------- the project's evidence, with its lifecycle
def evidence_claims():
    """Every dimension claim this project makes, with the status the project itself gives it.

    The window height the owner offered early in the project was retired, in writing, for windows with no
    source height - the guide replaced it, by room use.  R5 handed it over as an active claim, and because an
    owner input outranks a standard for ever it answered all seven windows.  Here it is handed over retired,
    within the scope the project retired it in, and it still answers anything outside that scope.
    """
    claims = []
    for key, rec in sorted(OI.PROJECT_INPUTS.items()):
        kind = {"AL_RASHED_WALL_HEIGHT": "WALL_HEIGHT", "AL_RASHED_DOOR_HEIGHT": "DOOR_HEIGHT",
                "AL_RASHED_PROJECT_WINDOW_HEIGHT": "WINDOW_HEIGHT",
                "AL_RASHED_PARAPET_HEIGHT": "PARAPET_HEIGHT"}.get(key)
        if kind is None:
            continue
        scope = {"DOOR_HEIGHT": {"OBJECT_KIND": "DOOR"}, "WINDOW_HEIGHT": {"OBJECT_KIND": "WINDOW"}}.get(kind, {})
        claims.append({"WHAT": kind, "CLAIM": EV.Claim(rec["VALUE_M"], EV.OWNER_PROJECT_INPUT, rec["FROM"],
                                                       {"KIND": rec["KIND"],
                                                        "PRECEDENCE": rec.get("PRECEDENCE")},
                                                       scope=scope)})
    return claims


def height_claims_for(kind):
    """The claims that may answer this opening kind's height, after the project's own supersession."""
    claims = [c["CLAIM"] for c in evidence_claims()
              if c["WHAT"] == {"DOOR": "DOOR_HEIGHT", "WINDOW": "WINDOW_HEIGHT"}.get(kind)]
    if kind == "WINDOW":
        # the project states this in WS.SUPERSEDES: the early 2.00 m was replaced, for windows with no source
        # height, by the approved guide - which answers by room use, not by one number
        claims = EV.supersede(claims, OI.PROJECT_INPUTS["AL_RASHED_PROJECT_WINDOW_HEIGHT"]["FROM"],
                              by=WS.VERSION, reason=WS.SUPERSEDES["WHY"],
                              scope={"HAS_SOURCE_HEIGHT": False})
    return claims


def wall_height_evidence():
    rec = OI.PROJECT_INPUTS["AL_RASHED_WALL_HEIGHT"]
    return EV.resolve("wall height",
                      [EV.Claim(rec["VALUE_M"], EV.OWNER_PROJECT_INPUT, rec["FROM"],
                                {"KIND": rec["KIND"], "PRECEDENCE": rec.get("PRECEDENCE")})],
                      TOLERANCE_M, subject={"OBJECT_KIND": "WALL"})


def category_resolver(label, area_m2):
    """The project's own label-to-category rule, handed to the engine as a function."""
    return WS.category_for(label, area_m2)


def space_role(space):
    """Is this space an occupied room, or is it outside?  This drawing's vocabulary, not the engine's.

    A window separates an occupied room from the open air, and the room-use standard belongs to the occupied
    side.  R6 treated a roof terrace as an equal candidate to the bedroom on the other side of the glass and
    reported three windows ambiguous because the two were a few centimetres apart in distance.  Which of this
    project's words mean "outside" is stated here, in the adapter, because it is a fact about this drawing.
    """
    label = (space.label or "").strip().upper()
    if not label:
        return RC.ROLE_UNKNOWN
    if any(label.startswith(w) or w in label for w in L.EXTERNAL):
        return RC.EXTERNAL_OR_OPEN
    if label in L.ROOM_WORDS or any(label.startswith(w) for w in L.ROOM_WORDS):
        return RC.ENCLOSED_ROOM
    return RC.ROLE_UNKNOWN


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def _cell_rect(g, i, j):
    return geom.Rect(g["XS"][i], g["YS"][j], g["XS"][i + 1], g["YS"][j + 1])


def _column_cells(g):
    """Cells bounded on both axes by lines the source draws on its column layer."""
    xs, ys, tol = g["XS"], g["YS"], TOLERANCE_M
    vert = [(pos, lo, hi) for kind, pos, lo, hi in g["COLUMNS"] if kind == "V"]
    horz = [(pos, lo, hi) for kind, pos, lo, hi in g["COLUMNS"] if kind == "H"]
    out = set()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            v = any(min(abs(p - x0), abs(p - x1)) <= tol and lo - tol <= y0 and hi + tol >= y1
                    for p, lo, hi in vert)
            h = any(min(abs(p - y0), abs(p - y1)) <= tol and lo - tol <= x0 and hi + tol >= x1
                    for p, lo, hi in horz)
            if v and h:
                out.add((i, j))
    return out


def _connected(cells):
    remaining, groups = set(cells), []
    while remaining:
        seed = min(remaining)
        stack, group = [seed], []
        remaining.discard(seed)
        while stack:
            i, j = stack.pop()
            group.append((i, j))
            for nb in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if nb in remaining:
                    remaining.discard(nb)
                    stack.append(nb)
        groups.append(sorted(group))
    return groups


def source_opening_objects(ents, floor, g):
    """Every opening object the SOURCE carries on this floor, as the features it carries them with.

    No depth, no rectangle and no wall geometry: those belong to host resolution.  What is here is what the
    CAD file says - where the object is, how wide it is, which way it runs, what block names it, which layer
    it is on, and the jamb marks that were paired to measure it.
    """
    out = []
    bn = Q._block_names()
    for o in Q.opening_register(ents, floor, g, bn):
        if o["WIDTH_M"] is None:
            continue
        axis = geom.AXIS_X if o["RUNS"] == "ALONG_X" else geom.AXIS_Y
        half = o["WIDTH_M"] / 2.0
        jambs = ([(o["X"] - half, o["Y"]), (o["X"] + half, o["Y"])] if axis == geom.AXIS_X
                 else [(o["X"], o["Y"] - half), (o["X"], o["Y"] + half)])
        named = o["TYPE_SOURCE"] == "CAD_SYMBOL_IN_THE_OPENING"
        layer = (G.DOOR_LAYERS[0] if o["TYPE"] == "DOOR" else
                 G.WINDOW_LAYERS[0] if o["TYPE"] == "WINDOW" else None)
        out.append({"REF": o["OPENING_REF"], "TYPE": o["TYPE"], "TYPE_SOURCE": o["TYPE_SOURCE"],
                    "CENTRE": (o["X"], o["Y"]), "SPAN_M": o["WIDTH_M"], "AXIS": axis,
                    "BLOCK_REF": f"{layer}::{o['OPENING_REF']}" if named else None,
                    "LAYER": layer if named else None,
                    "JAMB_POINTS": jambs, "ORIGIN": "DRAWING_REGISTER",
                    "WIDTH_SOURCE": o["WIDTH_SOURCE"]})
    for n, gl in enumerate(FT.glazed_openings(floor, ents)):
        axis = geom.AXIS_X if gl["RUNS"] == "ALONG_X" else geom.AXIS_Y
        out.append({"REF": f"{floor[:2]}-GL-{n:03d}", "TYPE": "WINDOW",
                    "TYPE_SOURCE": "GLAZED_RECTANGLE_PUNCHED_THROUGH_THE_WALL",
                    "CENTRE": (gl["X"], gl["Y"]), "SPAN_M": gl["WIDTH_M"], "AXIS": axis,
                    "BLOCK_REF": None, "LAYER": G.WINDOW_LAYERS[0], "JAMB_POINTS": None,
                    "ORIGIN": "EXTRACTED_GEOMETRY", "WIDTH_SOURCE": "MEASURED_FROM_PROJECT_GEOMETRY"})
    return out


def extract_floor(ents, floor):
    """Turn one plan window into the generic engine's inputs.  No quantity is computed here."""
    g = G.grid(ents, G.WINDOWS[floor])
    comps = G.rooms(g)
    wall_cells = {(c["I"], c["J"]): c for c in G.wall_cells(g)}
    column_cells = _column_cells(g)
    _tr, labs = L.labels_in_drawing(floor, ents)

    components, annotations = [], {}
    for (i, j), w in sorted(wall_cells.items()):
        ref = f"{floor[:2]}-W-{i:03d}-{j:03d}"
        is_column = (i, j) in column_cells
        layer = G.COLUMN_LAYERS[0] if is_column else G.WALL_LAYERS[0]
        components.append(GeometryComponent(
            ref, KIND_COLUMN if is_column else KIND_WALL_BAND, [_cell_rect(g, i, j)], floor, REVISION,
            thickness=round(w["THICKNESS_M"], 4),
            axis=geom.AXIS_Y if w["AXIS"] == "V" else geom.AXIS_X, layer=layer))
        annotations[ref] = {"LAYER": layer, "MATERIAL": None,
                            "WHY": "the source names the layer and states no material"}
    for k, c in enumerate(comps):
        free = sorted(set(c["CELLS"]) - set(wall_cells))
        if not free:
            continue
        for n, group in enumerate(_connected(free)):
            ref = f"{floor[:2]}-{k:03d}" if n == 0 else f"{floor[:2]}-{k:03d}-{n}"
            components.append(GeometryComponent(
                ref, KIND_FLOOR_REGION, [_cell_rect(g, i, j) for i, j in group], floor, REVISION))

    source_objects = source_opening_objects(ents, floor, g)
    candidates = []
    for s in source_objects:
        c = AD.Candidate(s["REF"], floor, REVISION, centre=s["CENTRE"], span=s["SPAN_M"], axis=s["AXIS"],
                         opening_type=s["TYPE"], origin=s["ORIGIN"], block_ref=s["BLOCK_REF"],
                         layer=s["LAYER"], jamb_points=s["JAMB_POINTS"])
        c.width_claims = [EV.Claim(s["SPAN_M"], EV.MEASURED_GEOMETRY, f"{s['WIDTH_SOURCE']}::{s['REF']}",
                                   {"WHY": "the clear width the drawing draws"})]
        c.height_claims = height_claims_for(s["TYPE"])
        candidates.append(c)

    barriers = [Barrier(geom.AXIS_Y if kind == "V" else geom.AXIS_X, pos, lo, hi,
                        Barrier.BACKED_BY_MATERIAL, floor, component_ref=f"COLUMN::{kind}::{round(pos, 3)}")
                for kind, pos, lo, hi in g["COLUMNS"]]
    barriers += [Barrier(geom.AXIS_Y if kind == "V" else geom.AXIS_X, pos, lo, hi,
                         Barrier.BACKED_BY_MATERIAL, floor, component_ref=f"WALL::{kind}::{round(pos, 3)}")
                 for kind, pos, lo, hi in g["WALLS"]]
    barriers += [Barrier(geom.AXIS_Y if kind == "V" else geom.AXIS_X, pos, lo, hi,
                         Barrier.VIRTUAL_CLOSURE, floor, component_ref=f"CLOSURE::{kind}::{round(pos, 3)}")
                 for kind, pos, lo, hi in g["CLOSURES"]]

    labels = [Label(x["NAME"], x["X"], x["Y"]) for x in labs]
    return {"COMPONENTS": components, "BARRIERS": barriers, "CANDIDATES": candidates, "LABELS": labels,
            "REVISION": REVISION, "TOLERANCE_M": TOLERANCE_M, "FLOOR": floor,
            "SLIVER_MIN_DIMENSION_M": SLIVER_MIN_DIMENSION_M,
            "PLAN_WINDOW_AREA_M2": sum(c.area for c in components),
            "ANNOTATIONS": annotations, "SOURCE_OPENING_OBJECTS": source_objects, "GRID": g}


def run_floor(ents, floor, plan=None, families=None):
    plan = plan if plan is not None else extract_floor(ents, floor)
    result = pipeline.run(
        plan, max_opening_span=MAX_OPENING_SPAN_M, drafting_resolution_m=DRAFTING_RESOLUTION_M,
        thickness_families=families, wall_height_evidence=wall_height_evidence(),
        plan_window_area=plan["PLAN_WINDOW_AREA_M2"], closure_tolerance=1e-6,
        annotations=plan["ANNOTATIONS"],
        # this source states no wall material anywhere, so no material claim is handed over
        material_claims={}, material_map={}, wall_layers=G.WALL_LAYERS,
        room_category_mapping=WS.LABEL_MAP, category_resolver=category_resolver,
        standard_table=WS.TABLE, standard_reference=WS.VERSION,
        # which of THIS drawing's words mean "outside".  The engine holds no such vocabulary; it only knows
        # that a room-use standard belongs to the enclosed side of a window.
        space_role=space_role,
        # this source names no columns among its wall bands, and nothing else in it states that a band is not
        # a wall, so nothing is excluded on anything but a duplicate or a proven junction
        exclusion_evidence={},
        # and it states no material anywhere, at any scope
        material_scopes=[])
    result["FLOOR"] = floor
    result["PLAN"] = plan
    return result


def project_thickness_families(plans):
    """The thickness families of the WHOLE villa, discovered once and used on every floor."""
    import copy

    lines = []
    for plan in plans.values():
        probe = pipeline.run(copy.deepcopy(plan), max_opening_span=MAX_OPENING_SPAN_M,
                             drafting_resolution_m=DRAFTING_RESOLUTION_M,
                             annotations=plan["ANNOTATIONS"], material_claims={}, material_map={},
                             wall_layers=G.WALL_LAYERS)
        lines += probe["WALL_LINE_OBJECTS"]
    return MA.thickness_families(lines, TOLERANCE_M)


# ------------------------------------------------------------------ metamorphic evidence on the real drawing
def metamorphic_evidence(ents, floor, families=None):
    """Run the real plan again, described differently, and compare the quantities."""
    def measure(plan):
        return TR.quantity_fingerprint(run_floor(ents, floor, plan=plan, families=families))

    base = measure(extract_floor(ents, floor))
    moved = measure(TR.transform_plan(extract_floor(ents, floor), dx=1234.5, dy=-987.25, quarter_turns=1))
    cut = measure(TR.resegment_plan(extract_floor(ents, floor), cuts=3))
    keys = ("WALLS", "BLOCKED", "SPACES", "OPENINGS")

    def same(a, b):
        return all(a[k] == b[k] for k in keys)

    return {
        "RIGID_MOTION": {"EQUIVALENT": same(base, moved),
                         "TRANSFORM": "translated by (1234.5, -987.25) m and turned through one right angle",
                         "WHY": "the same building, drawn elsewhere and turned round, is the same building",
                         "DIFFERENCES": {k: [base[k], moved[k]] for k in keys if base[k] != moved[k]}},
        "SEGMENTATION": {"EQUIVALENT": same(base, cut), "CUTS_PER_WALL_BAND": 3,
                         "WHY": "how finely the extractor chops a wall is a property of the extractor",
                         "DIFFERENCES": {k: [base[k], cut[k]] for k in keys if base[k] != cut[k]}},
        "REPRESENTATION": {"EQUIVALENT": same(base, cut) and same(base, moved),
                           "WHY": "the two representations of one wall - drawn through its opening, or "
                                  "stopped at each jamb - are exercised by the per-line basis register and by "
                                  "the segmentation case above"},
    }


# ------------------------------------------------------------------ provenance and the anti-calibration audit
ENGINE_SOURCES = sorted(str(p) for p in Path("engine/qs_core").glob("*.py"))
ADAPTER_SOURCE = "research/qs_wall_treatment_01/pa09/alrashed/regression_r6.py"

FORBIDDEN_IN_THE_ENGINE = [
    "ALRASHED", "AL RASHED", "AL_RASHED", "QORTUBA", "SABAH", "P7757", "7757",
    "963.188", "190.289", "1493.945", "474.693", "155.206", "128.816", "67.563",
    "220.42", "1087.388", "942.479", "204.334", "734.638", "931.016",
    "BA-0", "GR-0", "FI-0", "AR-FL", "AR-BL", "AR-W-", "AR-01", "AR-02", "AR-03", "US-18", "US-19",
    "EWAN", "16-11-2025", ".dwg", ".pdf",
]


def provenance():
    head = _git("rev-parse", "HEAD")
    return {
        "GENERATING_COMMIT": {"SHA": head, "SHORT": head[:7],
                              "WHAT": "the commit of the code that produced these registers",
                              "WORKING_TREE_CLEAN": _git("status", "--porcelain") == ""},
        "SOURCE_ARTIFACT_COMMIT": {
            "SHA": _git("log", "-1", "--format=%H", "--", str(FROZEN)) or None,
            "PATH": str(FROZEN), "TRACKED_IN_GIT": bool(_git("ls-files", "--", str(FROZEN))),
            "WHAT": "the commit that last touched the source artifact this run reads",
            "IF_NULL": "this artifact is produced output and is not tracked in git, so it has no commit; its "
                       "identity is the digest recorded beside it"},
        "FROZEN_ARTIFACT": {"PATH": str(FROZEN), "SHA256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
                            "WHAT": "the digest of the frozen takeoff, opened read-only and never rewritten"},
        "PACKAGING_COMMIT": {"SHA": None,
                             "WHAT": "the commit at which the deliverable zip was assembled; written by the "
                                     "packager, because it cannot be known here"},
        "ENGINE_SOURCES": ENGINE_SOURCES, "ADAPTER_SOURCE": ADAPTER_SOURCE,
    }


def anti_calibration_audit():
    from engine.qs_core import invariants as INV
    import re

    check = INV.no_comparison_input([Path(p) for p in ENGINE_SOURCES], FORBIDDEN_IN_THE_ENGINE)
    branch_hits = []
    for p in ENGINE_SOURCES:
        text = Path(p).read_text("utf-8")
        for pat in (r"if\s+project\b", r"project\s*==", r"PROJECT_ID\s*==", r"if\s+.*\bfloor\s*==\s*[\"']"):
            for m in re.finditer(pat, text):
                branch_hits.append({"FILE": p, "PATTERN": pat, "LINE": text.count("\n", 0, m.start()) + 1})
    return {
        "WHAT": "the generic engine is read and must contain no project name, no previously reported total, "
                "no reference from a real drawing, no project vocabulary and no branch on which project is "
                "running",
        "TOKEN_SCAN": check,
        "PROJECT_BRANCH_SCAN": {"PATTERNS": 4, "HITS": branch_hits},
        "FILES_SCANNED": ENGINE_SOURCES,
        "PASS": check["PASS"] and not branch_hits,
        "WHAT_IT_DOES_NOT_PROVE": "that the engine is correct.  It proves only that it cannot be reproducing "
                                  "an answer it was told",
    }


# ------------------------------------------------------------------ reporting
def frozen_record():
    return json.loads(FROZEN.read_text("utf-8"))


def final_versus_blocked(results):
    rows = [dict(r, FLOOR=res["FLOOR"]) for res in results for r in res["WALL_ROWS"]]
    masonry = [r for r in rows if r["STATUS"] != "EXCLUDED_NOT_MASONRY"]
    blocked_groups = {}
    for res in results:
        graph = res["DEPENDENCY_GRAPH"]
        for node in graph["BLOCKED_SUBTOTALS"]:
            key = node.split("::", 1)[1]
            key = None if key == "None" else float(key)
            blocked_groups[key] = {"KIND": "SUBTOTAL_BLOCKED_ON_A_FLOOR",
                                   "WHY": graph["BLOCKED"][node]["REASONS"][0]["WHY"], "DETAIL": key}
    project = QY.publish(masonry, lambda r: r["THICKNESS_FAMILY_M"], "NET_AREA_M2", "m2",
                         "masonry wall area by thickness, whole project", blocked_groups=blocked_groups)
    categories = {"FINAL": sum(1 for r in rows if r["STATUS"] == QY.FINAL),
                  "BLOCKED": sum(1 for r in rows if r["STATUS"] == "BLOCKED_PENDING_ANSWERS"),
                  "EXCLUDED": sum(1 for r in rows if r["STATUS"] == "EXCLUDED_NOT_MASONRY")}
    categories["OF"] = len(rows)
    excluded_refs = {(r["FLOOR"], r["COMPONENT_REF"]) for r in rows
                     if r["STATUS"] == "EXCLUDED_NOT_MASONRY"}
    blocked_refs = {(res["FLOOR"], ref) for res in results
                    for ref in res["DEPENDENCY_GRAPH"]["BLOCKED_WALL_LINES"]}
    blocked_and_excluded = len(blocked_refs & excluded_refs)
    line_status = {
        "BLOCKED_BY_AN_OPEN_QUESTION": len(blocked_refs),
        "NOT_BLOCKED": sum(len(res["DEPENDENCY_GRAPH"]["NON_BLOCKED_WALL_LINES"]) for res in results),
        "OF": len(rows),
        "MEANS": "blocked is a property of the LINE and its open questions; the three row categories are a "
                 "property of what may be PUBLISHED for it, and the two are reported separately because "
                 "one number cannot carry both",
    }
    return {
        "WHOLE_PROJECT": project,
        "BY_FLOOR": {res["FLOOR"]: res["PUBLICATION"] for res in results},
        "ROW_CATEGORIES": categories,
        "WALL_LINE_STATUS": line_status,
        "HOW_THE_TWO_COUNTS_AGREE": {
            "BLOCKED_LINES_MINUS_BLOCKED_BUT_EXCLUDED": (line_status["BLOCKED_BY_AN_OPEN_QUESTION"]
                                                         - blocked_and_excluded),
            "EQUALS_BLOCKED_ROWS": categories["BLOCKED"],
            "RECONCILES": (line_status["BLOCKED_BY_AN_OPEN_QUESTION"] - blocked_and_excluded
                           == categories["BLOCKED"]),
            "EXCLUDED_ROWS_THAT_ARE_ALSO_BLOCKED": blocked_and_excluded,
            "WHY": "a row's category is settled by identity first: a band the drawing settles is not a wall "
                   "is EXCLUDED even where an open question still touches it, so the blocked rows are the "
                   "blocked lines less the ones that are excluded anyway",
        },
        "NON_BLOCKED_WALL_LINES": line_status["NOT_BLOCKED"],
        "WHY_NON_BLOCKED_IS_NOT_FINAL": ("a line is non-blocked when no open question holds it up.  Not one "
                                         "of them is a released quantity here: every non-blocked line on "
                                         "this source is a band the drawing settles is not a wall"),
        "EXCLUDED_ROWS": [{"COMPONENT_REF": r["COMPONENT_REF"], "FLOOR": r["FLOOR"],
                           "THICKNESS_M": r["THICKNESS_M"],
                           "WALL_GEOMETRY_IDENTITY": r["WALL_GEOMETRY_IDENTITY"],
                           "REASON_KIND": r.get("EXCLUDED_REASON_KIND"), "WHY": r["EXCLUDED_BECAUSE"]}
                          for r in rows if r["STATUS"] == "EXCLUDED_NOT_MASONRY"],
        "RULE": "a subtotal is a number only when every row behind it is final; otherwise it is null and the "
                "root-question register says what has to be answered first",
    }


def compare(results, frozen):
    """What the general algorithms changed, and what they now decline to state, each with a trace."""
    old_rooms = {r["ROOM_REF"]: r for f in frozen["FLOORS"] for r in f["ROOMS"]}
    old_by_thickness = collections.Counter()
    for b in frozen["BLOCKWORK"]:
        old_by_thickness[b["THICKNESS_MM"]] += b["NET_AREA_M2"]
    published = final_versus_blocked(results)["WHOLE_PROJECT"]["SUBTOTALS"]

    lines = []
    for t in sorted(old_by_thickness):
        sub = published.get(str(round(t / 1000.0, 6)))
        lines.append({
            "QUANTITY": f"BLOCKWORK_{t}", "UNIT": "m2", "FROZEN_M2": round(old_by_thickness[t], 3),
            "ENGINE_FINAL_M2": None if sub is None else sub["FINAL_QUANTITY"],
            "ENGINE_STATUS": "NOT_PRODUCED" if sub is None else sub["STATUS"],
            "WAITING_ON": None if sub is None else sub["WAITING_ON"],
            "COMPARABLE": bool(sub and sub["FINAL_QUANTITY"] is not None),
            "WHY": "the frozen figure shared each floor's openings across thicknesses in proportion to wall "
                   "length, measured every band that had a thickness, and read shape as material; this run "
                   "admits openings on what the source names, resolves each host from the material around it, "
                   "and establishes geometry and material on separate evidence",
            "TRACE": "SOURCE_OBJECT -> ADMISSION -> HOST -> WALL_LINE -> GEOMETRY -> MATERIAL -> SUBTOTAL"})
    merges = []
    for res in results:
        for s in res["SPACES"]:
            if len(s["COMPONENT_REFS"]) < 2:
                continue
            merges.append({"ROOM_ID": s["ROOM_ID"], "FLOOR": s["FLOOR"], "LABEL": s["LABEL"],
                           "COMPONENTS": s["COMPONENT_REFS"], "AREA_M2": s["AREA_M2"],
                           "FROZEN_AREAS": {r: old_rooms[r]["AREA_M2"] for r in s["COMPONENT_REFS"]
                                            if r in old_rooms},
                           "TRACE": "SEAM_REGISTER -> RELATION=CONTINUOUS_FLOOR -> MEMBERSHIP_REGISTER"})
    return {
        "BLOCKWORK_LINES": lines,
        "SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS": sorted(merges, key=lambda m: -m["AREA_M2"]),
        "COMPONENT_CENSUS": {
            "FROZEN_COMPONENTS": len(old_rooms),
            "NEW_COMPONENTS": sum(len(res["MEMBERSHIP_REGISTER"]) for res in results),
            "NEW_SPACE_COUNT": sum(len(res["SPACES"]) for res in results)},
        "RULE": "these are differences, not corrections to the frozen artifact, which is unchanged.  A figure "
                "this run declines to state is not a figure of zero and is not agreement",
    }


R6_PACKAGE = Path("data/reports/ALRASHED_6_GENERIC_ENGINE_VALIDATION.zip")


def r6_snapshot_from_the_delivered_package():
    """R6's own registers, read out of the zip that was delivered, so the BEFORE column can be checked.

    Not off disk: this run overwrites some of those files.  The delivered package is also the only copy a
    reviewer can verify independently, which is the point of publishing it with detached hashes.
    """
    if not R6_PACKAGE.exists():
        return {}
    want = ("ALRASHED_OPENING_ADMISSION_REGISTER.json",
            "ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json",
            "ALRASHED_WINDOW_ROOM_AND_CATEGORY_REGISTER.json",
            "ALRASHED_ROOT_QUESTION_REGISTER.json",
            "ALRASHED_DEPENDENCY_IMPACT_REGISTER.json",
            "ALRASHED_WALL_GEOMETRY_REGISTER.json")
    out = {"FROM": f"{R6_PACKAGE.name}",
           "SHA256_OF_THE_PACKAGE": hashlib.sha256(R6_PACKAGE.read_bytes()).hexdigest()}
    with zipfile.ZipFile(R6_PACKAGE) as z:
        names = set(z.namelist())
        for name in want:
            if name in names:
                out[name] = json.loads(z.read(name))
    admission = out.get("ALRASHED_OPENING_ADMISSION_REGISTER.json")
    out["OPENING_ADMISSION"] = (admission or {}).get("BY_FLOOR", {})
    return out


def _r6_defect_rows(r6, rec, questions, quantities):
    """One row per defect this review found, with what R6 did and what this round does instead.

    The BEFORE column is read from the delivered R6 package wherever that package carries it, and says so
    where it does not.  No expected quantity and no expected question count appears here: every AFTER value
    is read from the register this run produced.
    """
    val = r6.get("ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json") or {}
    windows = r6.get("ALRASHED_WINDOW_ROOM_AND_CATEGORY_REGISTER.json") or {}
    r6_roots = r6.get("ALRASHED_ROOT_QUESTION_REGISTER.json") or {}
    r6_impacts = (r6.get("ALRASHED_DEPENDENCY_IMPACT_REGISTER.json") or {}).get("DEPENDENCY_IMPACTS", [])
    r6_geom = r6.get("ALRASHED_WALL_GEOMETRY_REGISTER.json") or {}

    def r6_window_rows():
        return [row for f in (windows.get("BY_FLOOR") or {}).values() for row in f.get("REGISTER", [])]

    def dupes(rows):
        seen = {}
        for i in rows:
            key = (i.get("ROOT_QUESTION_ID"), str(i.get("NODE")), i.get("NODE_KIND"), i.get("EFFECT"))
            seen[key] = seen.get(key, 0) + 1
        return sum(n - 1 for n in seen.values())

    r6_heights = [q for q in r6_roots.get("ROOT_QUESTIONS", [])
                  if q.get("KIND") == "OPENING_HEIGHT_NOT_ESTABLISHED"]
    r6_established = [w for w in r6_window_rows()
                      if (w.get("HEIGHT_EVIDENCE") or {}).get("STATUS") == "ESTABLISHED"]
    contradicted = sorted({w["OPENING_REF"] for w in r6_established}
                          & {q["SUBJECT_REF"] for q in r6_heights})
    r6_ambiguous = [w for w in r6_window_rows()
                    if (w.get("ROOM") or {}).get("STATUS") == "HOST_ROOM_AMBIGUOUS"]
    r6_excluded = [x for f in (r6_geom.get("BY_FLOOR") or {}).values()
                   for x in f.get("REGISTER", []) if x.get("GEOMETRY_IDENTITY") == "NON_WALL_ARTEFACT"]

    now_windows = [row for res in rec["_RESULTS"]
                   for row in res["ROOM_CATEGORY_REGISTER"]["REGISTER"]]
    now_heights = [q for q in questions["ROOT_QUESTIONS"]
                   if q["KIND"] == "OPENING_HEIGHT_NOT_ESTABLISHED"]
    now_established = [o for res in rec["_RESULTS"] for o in res["FINAL_OPENING_STATE"]["OPENINGS"]
                       if o["HEIGHT_EVIDENCE"]["STATUS"] == "ESTABLISHED"]
    now_excluded = [x for res in rec["_RESULTS"] for x in res["WALL_IDENTITY"]["REGISTER"]
                    if x["GEOMETRY_IDENTITY"] == MA.NON_WALL_ARTEFACT]
    now_material_subjects = sorted({q["SUBJECT_REF"] for q in questions["ROOT_QUESTIONS"]
                                    if q["KIND"] == "WALL_MATERIAL_NOT_ESTABLISHED"})

    def row(ref, defect, before, after, evidence, automatic=True):
        return {"REVIEW_POINT": ref, "DEFECT": defect, "R6_BEFORE": before, "R7_AFTER": after,
                "EVIDENCE_FOR_THE_CHANGE": evidence,
                "AUTOMATIC_OR_QUESTION": "AUTOMATIC" if automatic else "REMAINS_A_ROOT_QUESTION"}

    return [
        row("1", "a dimension resolved after the registers were built left them describing an earlier moment",
            {"HEIGHTS_ESTABLISHED_BUT_STILL_ASKED": contradicted,
             "OPENINGS_WITH_A_NULL_AREA_AND_AN_ESTABLISHED_HEIGHT": len(r6_established)},
            {"EVIDENCE_BARRIER_HOLDS_ON_EVERY_FLOOR":
                all(r["EVIDENCE_BARRIER"]["UNCHANGED"] for r in rec["FLOORS"]),
             "HEIGHTS_ESTABLISHED": len(now_established),
             "HEIGHT_QUESTIONS_STILL_OPEN": len(now_heights)},
            "the pipeline resolves every dimension, freezes the opening state, and derives areas, "
            "deductions, dependencies and questions from that frozen state alone"),
        row("2", "no check compared the registers against each other",
            {"GATE_CHECKS": val.get("ACCEPTANCE_GATE", {}).get("OF")},
            {"GATE_CHECKS": rec["ACCEPTANCE_GATE"]["OF"],
             "NEW_CHECKS": ["A22", "A23", "A24", "A25", "A26", "A27", "A28", "A29", "A30", "A31"]},
            "ten document-level checks, each with a mutation test, and the whole gate still scores 0 on the "
            "committed R4 output"),
        row("3", "a question was asked from a stale AREA_M2 rather than from the evidence",
            {"HEIGHT_QUESTIONS": len(r6_heights), "OF_WHICH_ALREADY_ANSWERED": len(contradicted)},
            {"HEIGHT_QUESTIONS": len(now_heights)},
            "the question register reads the frozen height evidence directly"),
        row("4", "an external roof competed with the room on the other side of the glass",
            {"WINDOWS_AMBIGUOUS": len(r6_ambiguous),
             "REFS": sorted(w["OPENING_REF"] for w in r6_ambiguous)},
            {"WINDOWS_AMBIGUOUS": sum(1 for w in now_windows
                                      if w["ROOM"]["STATUS"] == "HOST_ROOM_AMBIGUOUS"),
             "WINDOWS_RESOLVED": sum(1 for w in now_windows
                                     if w["ROOM"]["STATUS"] == "HOST_ROOM_RESOLVED")},
            "the room is resolved from the two sides of the host wall, and an open area never competes with "
            "an enclosed room for a room-use standard"),
        row("5", "the impact register counted construction paths, not dependencies",
            {"IMPACT_ROWS": len(r6_impacts), "EXACT_DUPLICATES": dupes(r6_impacts)},
            {"IMPACT_ROWS": questions["DEPENDENCY_IMPACT_COUNT"],
             "EXACT_DUPLICATES": questions["DUPLICATE_IMPACT_ROWS"]},
            "impacts are a set keyed by fact, node, node kind and effect, and every node publishes the set "
            "of facts holding it up"),
        row("6", "'unblocks all 127 rows' was asserted, not calculated",
            {"CLAIM": "four material questions are the whole bottleneck and unblock all 127 rows",
             "CALCULATION_BEHIND_IT": None},
            {"MATERIAL_QUESTIONS": len(now_material_subjects),
             "RELEASES": next((x["RELEASES_NODES"] for x in rec["ANSWER_IMPACT_SIMULATION"]["BY_KIND"]
                               if x["SCENARIO"].endswith("WALL_MATERIAL_NOT_ESTABLISHED question")), None),
             "LEAVES_BLOCKED": next((x["STILL_BLOCKED"] for x in
                                     rec["ANSWER_IMPACT_SIMULATION"]["BY_KIND"]
                                     if x["SCENARIO"].endswith("WALL_MATERIAL_NOT_ESTABLISHED question")),
                                    None)},
            "every release statement is generated from the blocker-set simulation"),
        row("7", "a thickness family was used as a wall type",
            {"MATERIAL_QUESTION_SUBJECTS": sorted({q.get("SUBJECT_REF") for q in
                                                   r6_roots.get("ROOT_QUESTIONS", [])
                                                   if q.get("KIND") == "WALL_MATERIAL_NOT_ESTABLISHED"})},
            {"MATERIAL_QUESTION_SUBJECTS": now_material_subjects},
            "a material claim carries an explicit scope and answers only the bands it names; the question "
            "group is every attribute the source states, and is published as a group and not as a type",
            automatic=False),
        row("8", "twenty-three bands left the trade on their shape, at weak confidence",
            {"EXCLUDED": len(r6_excluded),
             "ON_WEAK_CONFIDENCE": sum(1 for x in r6_excluded
                                       if x.get("GEOMETRY_CONFIDENCE") == "WEAK")},
            {"EXCLUDED": len(now_excluded),
             "SHORT_BANDS_NOW_ASKED_ABOUT": sum(1 for q in questions["ROOT_QUESTIONS"]
                                                if q["KIND"] == "WALL_GEOMETRY_NOT_ESTABLISHED")},
            "exclusion needs positive evidence: a source-named column, a proven duplicate, or a junction "
            "already inside the crossing walls.  A short band is a question",
            automatic=False),
        row("9", "A20 was described as verifying every statement in the narrative",
            {"WHAT_IT_CHECKED": "five hand-written assertions"},
            {"DECLARED_CLAIMS": rec["REPORT_CLAIMS"]["CLAIM_COUNT"],
             "ALL_AGREE": rec["REPORT_CLAIMS"]["ALL_DECLARED_CLAIMS_AGREE"],
             "WHAT_IT_DOES_NOT_PROVE": rec["REPORT_CLAIMS"]["WHAT_THIS_CHECK_DOES_NOT_PROVE"]},
            "every number and causal statement is a claim object with a register path, and the prose is "
            "generated from the claims"),
        row("10", "the gate had no check for any of the above",
            {"CHECKS": val.get("ACCEPTANCE_GATE", {}).get("OF")},
            {"CHECKS": rec["ACCEPTANCE_GATE"]["OF"],
             "ALL_PASS": rec["ACCEPTANCE_GATE"]["ALL_PASS"]},
            "ten new checks and ten mutations, run on the real drawing and on the fixtures"),
    ]


def before_after(results, r6_snapshot=None):
    """R6 against R7: one row per defect this review found, and any object whose class changed."""
    rows = []
    r5 = r6_snapshot if r6_snapshot is not None else r6_snapshot_from_the_delivered_package()
    r5_pop = {c["CANDIDATE_REF"]: c for f, v in (r5.get("OPENING_ADMISSION") or {}).items()
              for c in v.get("POPULATION", [])}
    for res in results:
        for c in res["OPENING_POPULATION"]["POPULATION"]:
            was = (r5_pop.get(c["CANDIDATE_REF"]) or {}).get("CLASSIFICATION", "NOT_IN_THE_R6_REGISTER")
            if was == c["CLASSIFICATION"]:
                continue
            named = [p["REFERENCE"] for p in c["PROVENANCE"] if p["KIND"] == AD.PROV_BLOCK]
            rows.append({
                "OBJECT": c["CANDIDATE_REF"], "OBJECT_KIND": "OPENING", "FLOOR": c["FLOOR"],
                "R6_CLASSIFICATION_BEFORE": was, "R7_CLASSIFICATION": c["CLASSIFICATION"],
                "SOURCE_EVIDENCE_FOR_THE_CHANGE": ("the CAD block " + named[0] if named else
                                                   "no naming provenance in the source"),
                "AUTOMATIC_OR_QUESTION": ("AUTOMATIC" if c["CLASSIFICATION"] ==
                                          AD.OPENING_CONFIRMED_HOST_CONFIRMED else
                                          "REMAINS_A_ROOT_QUESTION"),
                "WHY": (c["EVIDENCE"][0]["DETAIL"].get("WHY") if c["EVIDENCE"] else None)})
    identity_rows = []
    for res in results:
        for r in res["WALL_IDENTITY"]["REGISTER"]:
            identity_rows.append({
                "OBJECT": r["COMPONENT_REF"], "OBJECT_KIND": "WALL_LINE", "FLOOR": r["FLOOR"],
                "R6_CLASSIFICATION_BEFORE": "CONFIRMED_MASONRY_WALL (geometry read as material)",
                "R7_CLASSIFICATION": f"{r['GEOMETRY_IDENTITY']} + {r['MATERIAL_IDENTITY']}",
                "SOURCE_EVIDENCE_FOR_THE_CHANGE": ("the source states no material for this band; its layer "
                                                   f"{r.get('LAYER')} establishes wall geometry only"),
                "AUTOMATIC_OR_QUESTION": ("REMAINS_A_ROOT_QUESTION"
                                          if r["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN else "AUTOMATIC"),
                "WHY": r["WHY_MATERIAL"]})
    return {
        "R6_COLUMN_READ_FROM": r5.get("FROM", "no R5 package was available to this run"),
        "R6_PACKAGE_SHA256": r5.get("SHA256_OF_THE_PACKAGE"),
        "OPENINGS": sorted(rows, key=lambda r: r["OBJECT"]),
        "WALL_IDENTITY": sorted(identity_rows, key=lambda r: r["OBJECT"])[:40],
        "WALL_IDENTITY_SUMMARY": collections.Counter(r["R7_CLASSIFICATION"] for r in identity_rows),
        "OPENINGS_NOTE": ("empty is the right answer where R6 already classified every object correctly; "
                          "this review found no defect in the admission classes, and none was invented"),
        "HOW_TO_READ": "AUTOMATIC means the source evidence settled it without anyone being asked.  "
                       "REMAINS_A_ROOT_QUESTION means the change was to stop pretending it was settled",
    }


def _write(name, payload, prov):
    path = OUT / f"ALRASHED_{name}.json"
    path.write_text(json.dumps(
        {"ARTIFACT": f"ALRASHED_{name}", "SOURCE_REVISION": REVISION, "PROVENANCE": prov,
         "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         **payload}, indent=1, ensure_ascii=False, default=str), "utf-8")
    return path


def _merge_questions(results):
    """One project-wide root-question register: the same fact on two floors is still one fact per object.

    The impacts are a SET here too, keyed exactly as the per-floor register keys them.  Merging three floors
    by concatenation would reintroduce the duplicates the per-floor registers were built to avoid.
    """
    roots, impacts = {}, {}
    for res in results:
        qs = res["QUESTIONS"]
        for r in qs["ROOT_QUESTIONS"]:
            key = r["ROOT_QUESTION_ID"]
            if key in roots:
                roots[key]["ASKED_TIMES"] += r["ASKED_TIMES"]
                roots[key].setdefault("FLOORS", []).append(res["FLOOR"])
                continue
            roots[key] = dict(r, FLOORS=[res["FLOOR"]])
        for i in qs["DEPENDENCY_IMPACTS"]:
            key = (i["ROOT_QUESTION_ID"], str(i["NODE"]), i["NODE_KIND"], i["EFFECT"])
            if key not in impacts:
                impacts[key] = dict(i, FLOOR=res["FLOOR"])
    impacts = list(impacts.values())
    ordered = sorted(roots.values(), key=lambda r: (r["KIND"], r["SUBJECT_REF"]))
    by_kind = collections.Counter(r["KIND"] for r in ordered)
    per_root = collections.Counter(i["ROOT_QUESTION_ID"] for i in impacts)
    return {
        "ROOT_QUESTIONS": ordered, "ROOT_QUESTION_COUNT": len(ordered),
        "ROOT_QUESTIONS_BY_KIND": dict(sorted(by_kind.items())),
        "DEPENDENCY_IMPACTS": sorted(impacts, key=lambda i: (i["ROOT_QUESTION_ID"], str(i["NODE"]))),
        "DEPENDENCY_IMPACT_COUNT": len(impacts),
        "IMPACTS_PER_ROOT_QUESTION": dict(sorted(per_root.items())),
        "IMPACTS_WITHOUT_A_ROOT_QUESTION": sorted(set(per_root) - set(roots)),
        "DUPLICATE_IMPACT_ROWS": 0,
        "IMPACTS_ARE": "a set keyed by (root question, node, node kind, effect), across the whole project",
        "RULE": "a unique unanswered fact is one root question with one stable id; everything it holds up is "
                "an impact that references that id and is never counted as another question",
    }


def answer_impact_simulation(blockers, questions):
    """What each answer, and each plausible set of answers, would actually release.

    The R6 report said four material questions were "the whole bottleneck" and would "unblock all 127 rows".
    Neither sentence came from a calculation.  This is the calculation: answer a set of questions, and count
    only the nodes that have nothing left holding them up.
    """
    by_kind = {}
    for q in questions["ROOT_QUESTIONS"]:
        by_kind.setdefault(q["KIND"], []).append(q["ROOT_QUESTION_ID"])

    scenarios = []
    for kind, ids in sorted(by_kind.items()):
        sim = DEP.simulate(blockers, ids)
        scenarios.append({
            "SCENARIO": f"answer every {kind} question",
            "QUESTIONS_ANSWERED": len(ids),
            "RELEASES_NODES": sim["RELEASED_NODE_COUNT"],
            "STILL_BLOCKED": sim["STILL_BLOCKED_COUNT"],
            "WHAT_REMAINS": sorted({b for n in sim["STILL_BLOCKED"] for b in n["REMAINING_BLOCKERS"]}),
        })
    everything = DEP.simulate(blockers, [q["ROOT_QUESTION_ID"] for q in questions["ROOT_QUESTIONS"]])
    single = [{"ROOT_QUESTION_ID": qid,
               "RELEASES_NODES": rec["RELEASES_NODE_COUNT"],
               "AFFECTS_NODES": rec["AFFECTS_NODE_COUNT"],
               "REMOVES_A_BLOCKER_BUT_LEAVES_OTHERS": len(rec["REMOVES_A_BLOCKER_BUT_LEAVES_OTHERS"])}
              for qid, rec in sorted(blockers["BY_ROOT_QUESTION"].items())]
    return {
        "PER_QUESTION": single,
        "BY_KIND": scenarios,
        "ANSWERING_EVERYTHING": {"RELEASES_NODES": everything["RELEASED_NODE_COUNT"],
                                 "STILL_BLOCKED": everything["STILL_BLOCKED_COUNT"]},
        "RULE": "a question RELEASES a node only when it is that node's last blocker.  Everything else "
                "removes one blocker and leaves the rest, and is reported that way",
    }


def report_claims(rec, documents):
    """Every number and every causal statement this round's report is allowed to make.

    Each is declared with the register path that decides it and re-read from the record.  A sentence that is
    not a claim here may not carry a number, and the register says plainly what that does and does not prove.
    """
    reg = RCL.Register(rec)
    q = rec["ROOT_QUESTIONS_AND_IMPACTS"]
    fb = rec["FINAL_VERSUS_BLOCKED"]
    sim = rec["ANSWER_IMPACT_SIMULATION"]

    reg.claim("C-ROOT-QUESTIONS", "{value} unique facts remain unanswered across the villa",
              "ROOT_QUESTIONS_AND_IMPACTS.ROOT_QUESTION_COUNT", q["ROOT_QUESTION_COUNT"])
    reg.claim("C-IMPACTS", "those facts hold up {value} dependent values",
              "ROOT_QUESTIONS_AND_IMPACTS.DEPENDENCY_IMPACT_COUNT", q["DEPENDENCY_IMPACT_COUNT"])
    reg.claim("C-IMPACT-DUPLICATES", "the impact register contains {value} duplicate rows",
              "ROOT_QUESTIONS_AND_IMPACTS.DUPLICATE_IMPACT_ROWS", q["DUPLICATE_IMPACT_ROWS"])
    reg.claim("C-ROWS-FINAL", "{value} wall rows carry a final quantity",
              "FINAL_VERSUS_BLOCKED.ROW_CATEGORIES.FINAL", fb["ROW_CATEGORIES"]["FINAL"])
    reg.claim("C-ROWS-BLOCKED", "{value} wall rows are blocked",
              "FINAL_VERSUS_BLOCKED.ROW_CATEGORIES.BLOCKED", fb["ROW_CATEGORIES"]["BLOCKED"])
    reg.claim("C-ROWS-EXCLUDED", "{value} wall rows are excluded from the trade",
              "FINAL_VERSUS_BLOCKED.ROW_CATEGORIES.EXCLUDED", fb["ROW_CATEGORIES"]["EXCLUDED"])
    reg.claim("C-PUBLISHED", "the published project masonry total is {value}",
              "FINAL_VERSUS_BLOCKED.WHOLE_PROJECT.PUBLISHED_TOTAL",
              fb["WHOLE_PROJECT"]["PUBLISHED_TOTAL"], kind=RCL.STATUS)
    reg.claim("C-MATERIAL-QUESTIONS",
              "{value} material questions are open, one per group of bands the source describes identically",
              None, q["ROOT_QUESTIONS_BY_KIND"].get("WALL_MATERIAL_NOT_ESTABLISHED", 0),
              query=lambda d: d["ROOT_QUESTIONS_AND_IMPACTS"]["ROOT_QUESTIONS_BY_KIND"].get(
                  "WALL_MATERIAL_NOT_ESTABLISHED", 0))
    material = next((x for x in sim["BY_KIND"]
                     if x["SCENARIO"].endswith("WALL_MATERIAL_NOT_ESTABLISHED question")), None)
    if material is not None:
        reg.claim("C-MATERIAL-RELEASES",
                  "answering every material question would release {value} nodes", None,
                  material["RELEASES_NODES"], kind=RCL.RELEASE,
                  query=lambda d: next(x["RELEASES_NODES"] for x in
                                       d["ANSWER_IMPACT_SIMULATION"]["BY_KIND"]
                                       if x["SCENARIO"].endswith(
                                           "WALL_MATERIAL_NOT_ESTABLISHED question")),
                  note="counted as nodes with nothing left holding them up, not as nodes touched")
        reg.claim("C-MATERIAL-LEAVES",
                  "and would leave {value} nodes still blocked by something else", None,
                  material["STILL_BLOCKED"], kind=RCL.RELEASE,
                  query=lambda d: next(x["STILL_BLOCKED"] for x in
                                       d["ANSWER_IMPACT_SIMULATION"]["BY_KIND"]
                                       if x["SCENARIO"].endswith(
                                           "WALL_MATERIAL_NOT_ESTABLISHED question")))
    reg.claim("C-ALL-ANSWERS", "answering every open question would release {value} nodes",
              "ANSWER_IMPACT_SIMULATION.ANSWERING_EVERYTHING.RELEASES_NODES",
              sim["ANSWERING_EVERYTHING"]["RELEASES_NODES"], kind=RCL.RELEASE)
    reg.claim("C-GATE", "the independent gate result is {value}",
              "ACCEPTANCE_GATE.ALL_PASS", rec["ACCEPTANCE_GATE"]["ALL_PASS"], kind=RCL.STATUS)
    reg.claim("C-GATE-CHECKS", "the gate runs {value} document-level checks",
              "ACCEPTANCE_GATE.OF", rec["ACCEPTANCE_GATE"]["OF"])
    reg.claim("C-INVARIANTS", "{value} engine invariants hold on the real drawing",
              "INVARIANTS.PASSED", rec["INVARIANTS"]["PASSED"])
    reg.claim("C-FROZEN", "the frozen takeoff was rewritten: {value}",
              "FROZEN_UNCHANGED.REWRITTEN", rec["FROZEN_UNCHANGED"]["REWRITTEN"], kind=RCL.STATUS)
    reg.claim("C-BARRIER",
              "every derived register on every floor describes the frozen evidence state: {value}",
              None, all(r["EVIDENCE_BARRIER"]["UNCHANGED"] for r in rec["FLOORS"]), kind=RCL.STATUS,
              query=lambda d: all(f["EVIDENCE_BARRIER"]["UNCHANGED"] for f in d["FLOORS"]))
    out = reg.as_dict()
    out["PER_FLOOR_DOCUMENT_CLAIMS"] = {f: doc["REPORT_CLAIMS"] for f, doc in documents.items()}
    return out


def generated_prose(claims):
    """The paragraph a reader sees, built from the claims rather than written beside them."""
    by_id = {c["CLAIM_ID"]: c for c in claims["CLAIMS"]}

    def say(cid):
        c = by_id.get(cid)
        return None if c is None else c["STATEMENT"].format(value=c["REGISTER_SAYS"])

    lines = [say(c) for c in ("C-ROOT-QUESTIONS", "C-IMPACTS", "C-ROWS-FINAL", "C-ROWS-BLOCKED",
                              "C-ROWS-EXCLUDED", "C-PUBLISHED", "C-MATERIAL-QUESTIONS",
                              "C-MATERIAL-RELEASES", "C-MATERIAL-LEAVES", "C-ALL-ANSWERS",
                              "C-GATE-CHECKS", "C-INVARIANTS", "C-BARRIER", "C-FROZEN")]
    return {
        "SENTENCES": [x for x in lines if x],
        "EVERY_SENTENCE_IS": "generated from a declared claim and its register path",
        "WHAT_THIS_DOES_NOT_PROVE": claims["WHAT_THIS_CHECK_DOES_NOT_PROVE"],
    }


def finish(r6_snapshot=None):
    before = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    prov = provenance()
    ents = G.load()
    plans = {f: extract_floor(ents, f) for f in TK.FLOORS}
    families = project_thickness_families(plans)
    results = [run_floor(ents, f, plan=plans[f], families=families) for f in TK.FLOORS]
    meta = {res["FLOOR"]: metamorphic_evidence(ents, res["FLOOR"], families) for res in results}
    project_meta = {key: {"EQUIVALENT": all(meta[f][key]["EQUIVALENT"] for f in meta),
                          "BY_FLOOR": {f: meta[f][key] for f in meta}}
                    for key in ("RIGID_MOTION", "SEGMENTATION", "REPRESENTATION")}

    questions = _merge_questions(results)
    project_blockers = DEP.blocker_sets(
        {"NODES": {k: sorted({n for r in results for n in r["DEPENDENCY_GRAPH"]["NODES"].get(k, [])})
                   for k in ("OPENING", "WALL_LINE", "THICKNESS_SUBTOTAL", "BOQ_LINE")},
         "EDGES": [e for r in results for e in r["DEPENDENCY_GRAPH"]["EDGES"]]},
        questions,
        [row for r in results for row in r["WALL_ROWS"]])
    simulations = answer_impact_simulation(project_blockers, questions)
    quantities = final_versus_blocked(results)
    frozen = frozen_record()
    comparison = compare(results, frozen)

    graded, documents = {}, {}
    for res in results:
        doc = pipeline.acceptance_document(res, metamorphic=meta[res["FLOOR"]])
        doc["QUESTIONS"] = res["QUESTIONS"]
        documents[res["FLOOR"]] = doc
        graded[res["FLOOR"]] = acceptance.grade(doc)

    all_checks = [c for res in results for c in res["INVARIANTS"]["CHECKS"]]
    lineage = []
    for res in results:
        rerun = run_floor(ents, res["FLOOR"], families=families)
        lineage += identity.match_revisions(res["PLAN"]["COMPONENTS"], rerun["PLAN"]["COMPONENTS"], 0.05)

    lifecycle = []
    for kind in ("DOOR", "WINDOW"):
        for c in height_claims_for(kind):
            lifecycle.append(dict(c.as_dict(), APPLIES_TO_OPENING_KIND=kind))
    lifecycle.append(dict(EV.Claim(OI.PROJECT_INPUTS["AL_RASHED_WALL_HEIGHT"]["VALUE_M"],
                                   EV.OWNER_PROJECT_INPUT,
                                   OI.PROJECT_INPUTS["AL_RASHED_WALL_HEIGHT"]["FROM"]).as_dict(),
                          APPLIES_TO_OPENING_KIND="WALL"))

    rec = {
        "ARTIFACT": "ALRASHED_GENERIC_ENGINE_VALIDATION_R7",
        "ENGINE": "engine.qs_core", "SOURCE_REVISION": REVISION, "PROVENANCE": prov,
        "DECLARED_SOURCE_FACTS": SOURCE_FACTS,
        "THICKNESS_FAMILIES_OF_THE_WHOLE_SOURCE": families,
        "WALL_HEIGHT_EVIDENCE": wall_height_evidence(),
        "FLOORS": [{"FLOOR": r["FLOOR"], "COMPONENTS": len(r["MEMBERSHIP_REGISTER"]),
                    "EVIDENCE_VERSION": r["EVIDENCE_VERSION"],
                    "EVIDENCE_BARRIER": r["EVIDENCE_BARRIER"],
                    "HEIGHT_ESTABLISHED": r["FINAL_OPENING_STATE"]["HEIGHT_ESTABLISHED"],
                    "AREA_AVAILABLE": r["FINAL_OPENING_STATE"]["AREA_AVAILABLE"],
                    "SPACES": len(r["SPACES"]),
                    "SPACE_ASSEMBLY_OUTCOME": r["SPACE_VALIDATION"]["OUTCOME"],
                    "WALL_LINES": len(r["WALL_LINES"]),
                    "SOURCE_OPENING_OBJECTS": len(r["PLAN"]["SOURCE_OPENING_OBJECTS"]),
                    "NAMED_BY_THE_SOURCE": r["OPENING_POPULATION"]["NAMED_BY_THE_SOURCE_COUNT"],
                    "PHYSICAL_OPENINGS": r["OPENING_POPULATION"]["PHYSICAL_OPENING_COUNT"],
                    "HOST_CONFIRMED": r["HOST_REGISTER"]["HOST_CONFIRMED"],
                    "HOST_UNRESOLVED": r["HOST_REGISTER"]["HOST_UNRESOLVED"],
                    "OPENING_CLASSES": r["OPENING_POPULATION"]["COUNTS"],
                    "WALL_GEOMETRY": r["WALL_IDENTITY"]["GEOMETRY_COUNTS"],
                    "WALL_MATERIAL": r["WALL_IDENTITY"]["MATERIAL_COUNTS"],
                    "ROW_CATEGORIES": {k: v for k, v in r["PUBLICATION"]["ROW_CATEGORIES"].items()
                                       if k != "WHY_THREE"} if r["PUBLICATION"] else None,
                    "ROOT_QUESTIONS": r["QUESTIONS"]["ROOT_QUESTION_COUNT"],
                    "INVARIANTS": f"{r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}",
                    "ACCEPTANCE": f"{graded[r['FLOOR']]['PASSED']}/{graded[r['FLOOR']]['OF']}"}
                   for r in results],
        "FINAL_VERSUS_BLOCKED": quantities,
        "ROOT_QUESTIONS_AND_IMPACTS": questions,
        "ACCEPTANCE_GATE": {"BY_FLOOR": graded, "ALL_PASS": all(g["ALL_PASS"] for g in graded.values()),
                            "OF": max((g["OF"] for g in graded.values()), default=0),
                            "BLOCKERS": [b for g in graded.values() for b in g["BLOCKERS"]]},
        "METAMORPHIC": project_meta,
        "LINEAGE_ON_AN_IDENTICAL_RERUN": identity.lineage_summary(lineage),
        "INVARIANTS": {"PASSED": sum(1 for c in all_checks if c["PASS"]), "OF": len(all_checks),
                       "ALL_PASS": all(c["PASS"] for c in all_checks),
                       "FAILURES": [c for c in all_checks if not c["PASS"]]},
        "BLOCKER_SETS": project_blockers,
        "ANSWER_IMPACT_SIMULATION": simulations,
        "BEFORE_AND_AFTER": before_after(results, r6_snapshot),
        "ANTI_CALIBRATION_AUDIT": anti_calibration_audit(),
        "COMPARISON_WITH_THE_FROZEN_ARTIFACT": comparison,
        "FROZEN_UNCHANGED": {"SHA256_BEFORE": before,
                             "SHA256_AFTER": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
                             "REWRITTEN": False},
        "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    assert rec["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == rec["FROZEN_UNCHANGED"]["SHA256_AFTER"]
    rec["_RESULTS"] = results
    claims = report_claims(rec, documents)
    rec["REPORT_CLAIMS"] = claims
    rec["GENERATED_PROSE"] = generated_prose(claims)
    # the defect table reads the finished record, including the claim register, so it comes last
    rec["BEFORE_AND_AFTER"]["DEFECTS_THIS_REVIEW_FOUND"] = _r6_defect_rows(
        rec["BEFORE_AND_AFTER"].pop("_SNAPSHOT", {}), rec, questions, quantities)
    OUT.mkdir(parents=True, exist_ok=True)
    _write("GENERIC_ENGINE_VALIDATION_R7", {k: v for k, v in rec.items() if not k.startswith("_")}, prov)

    _write("SOURCE_OPENING_POPULATION_REGISTER", {
        "WHAT": "every opening object the SOURCE carries, as the features it carries them with - insertion "
                "point, span, orientation, block, layer and jamb marks.  No depth and no rectangle: those "
                "belong to the wall that turns out to host it",
        "BY_FLOOR": {r["FLOOR"]: r["PLAN"]["SOURCE_OPENING_OBJECTS"] for r in results},
        "TOTAL": sum(len(r["PLAN"]["SOURCE_OPENING_OBJECTS"]) for r in results)}, prov)

    _write("OPENING_ADMISSION_REGISTER", {
        "WHAT": "what the source says EXISTS, decided before any wall geometry is consulted",
        "CLASSES": list(AD.CLASSES), "NAMING_PROVENANCE": list(AD.NAMING_PROVENANCE),
        "BY_FLOOR": {r["FLOOR"]: r["OPENING_POPULATION"] for r in results}}, prov)

    _write("OPENING_TO_HOST_REGISTER", {
        "WHAT": "which wall each physical opening interrupts, decided from the material AROUND it, with the "
                "competing groups and their scores where the geometry does not settle it",
        "WEIGHTS": HO.WEIGHTS, "DECISIVE_MARGIN": HO.DECISIVE_MARGIN,
        "BY_FLOOR": {r["FLOOR"]: r["HOST_REGISTER"] for r in results},
        "DEDUCTION_REGISTER": {r["FLOOR"]: r["OPENING_REGISTER"] for r in results},
        "WALL_LINE_QUANTITIES": {r["FLOOR"]: r["WALL_ROWS"] for r in results}}, prov)

    _write("EVIDENCE_CLAIM_LIFECYCLE_REGISTER", {
        "WHAT": "every dimension claim this project makes, with the status the project gives it and the scope "
                "any supersession applies to",
        "LIFECYCLE": list(EV.LIFECYCLE), "HIERARCHY": list(EV.HIERARCHY),
        "CLAIMS": lifecycle,
        "SUPERSESSION_RECORDED_BY_THE_PROJECT": WS.SUPERSEDES,
        "WHY_IT_MATTERS": "an owner input outranks a standard for ever, so a resolver that reads rank alone "
                          "keeps choosing a value the project retired"}, prov)

    _write("WINDOW_ROOM_AND_CATEGORY_REGISTER", {
        "WHAT": "each window's host room, the category its label maps to, and whether the standard was the "
                "thing that answered its height",
        "BY_FLOOR": {r["FLOOR"]: r["ROOM_CATEGORY_REGISTER"] for r in results},
        "MAPPING_SOURCE": f"{WS.VERSION} label map, supplied by the adapter",
        "RULE": "no project-wide category.  A window whose room or category is unresolved publishes its "
                "width and leaves its height a question"}, prov)

    _write("WALL_GEOMETRY_REGISTER", {
        "WHAT": "whether each band is wall geometry, on the drawing's shapes, topology and layers",
        "IDENTITIES": list(MA.GEOMETRY_IDENTITIES), "ARTEFACT_REASONS": list(MA.ARTEFACT_REASONS),
        "BY_FLOOR": {r["FLOOR"]: {"COUNTS": r["WALL_IDENTITY"]["GEOMETRY_COUNTS"],
                                  "REGISTER": [{k: v for k, v in row.items()
                                                if not k.startswith("MATERIAL")}
                                               for row in r["WALL_IDENTITY"]["REGISTER"]]}
                     for r in results},
        "THICKNESS_FAMILIES": families}, prov)

    _write("WALL_MATERIAL_REGISTER", {
        "WHAT": "what each band is made of, and by which document - independently of its geometry",
        "IDENTITIES": list(MA.MATERIAL_IDENTITIES),
        "SOURCES_THAT_MAY_STATE_A_MATERIAL": list(MA.MATERIAL_EVIDENCE_SOURCES),
        "THIS_SOURCE_STATES": SOURCE_FACTS["MATERIAL_CLAIMS"]["WHY"],
        "BY_FLOOR": {r["FLOOR"]: {"COUNTS": r["WALL_IDENTITY"]["MATERIAL_COUNTS"],
                                  "REGISTER": [{"COMPONENT_REF": row["COMPONENT_REF"],
                                                "THICKNESS_FAMILY_M": row["THICKNESS_FAMILY_M"],
                                                "MATERIAL_IDENTITY": row["MATERIAL_IDENTITY"],
                                                "MATERIAL_EVIDENCE": row["MATERIAL_EVIDENCE"],
                                                "MATERIAL_INELIGIBLE": row["MATERIAL_INELIGIBLE"],
                                                "THICKNESS_FAMILY_PROVES_MATERIAL": False,
                                                "WHY": row["WHY_MATERIAL"]}
                                               for row in r["WALL_IDENTITY"]["REGISTER"]]}
                     for r in results}}, prov)

    _write("ROOT_QUESTION_REGISTER", {
        "WHAT": "unique unanswered facts, each with a stable id.  This is the work list",
        **{k: v for k, v in questions.items() if k != "DEPENDENCY_IMPACTS"}}, prov)

    _write("DEPENDENCY_IMPACT_REGISTER", {
        "WHAT": "everything the root questions hold up.  These are consequences, never additional questions",
        "DEPENDENCY_IMPACTS": questions["DEPENDENCY_IMPACTS"],
        "DEPENDENCY_IMPACT_COUNT": questions["DEPENDENCY_IMPACT_COUNT"],
        "IMPACTS_PER_ROOT_QUESTION": questions["IMPACTS_PER_ROOT_QUESTION"]}, prov)

    _write("FINAL_VERSUS_BLOCKED_QUANTITY_REPORT", {
        "WHAT": "what is finished, what is not, what is excluded, and what each unfinished figure waits on",
        **quantities, "COMPARISON_WITH_THE_FROZEN_ARTIFACT": comparison["BLOCKWORK_LINES"]}, prov)

    _write("COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER", {
        "WHAT": "every geometry component, the room it belongs to or the reason it belongs to none",
        "BY_FLOOR": {r["FLOOR"]: r["MEMBERSHIP_REGISTER"] for r in results},
        "SEAMS": {r["FLOOR"]: r["SEAM_REGISTER"] for r in results},
        "SPACES": {r["FLOOR"]: r["SPACES"] for r in results},
        "VALIDATION": {r["FLOOR"]: r["SPACE_VALIDATION"] for r in results}}, prov)

    _write("ENTITY_LINEAGE_REGISTER", {
        "WHAT": "what happened to every entity between two runs of the engine over the same source",
        "SUMMARY": rec["LINEAGE_ON_AN_IDENTICAL_RERUN"], "RECORDS": lineage}, prov)

    _write("FINAL_OPENING_STATE_REGISTER", {
        "WHAT": "the state of every opening at the moment the evidence stage closed.  Every register below "
                "was derived from this one and records its version",
        "BY_FLOOR": {r["FLOOR"]: r["FINAL_OPENING_STATE"] for r in results},
        "ORDER": results[0]["FINAL_OPENING_STATE"]["ORDER"],
        "RULE": results[0]["FINAL_OPENING_STATE"]["RULE"]}, prov)

    _write("EVIDENCE_VERSION_AND_DERIVATION_LINEAGE", {
        "WHAT": "which evidence state each derived register was built from, and whether the openings still "
                "say what that state says",
        "BY_FLOOR": {r["FLOOR"]: {
            "EVIDENCE_VERSION": r["EVIDENCE_VERSION"],
            "DERIVED_REGISTERS": {
                "OPENING_REGISTER": r["OPENING_REGISTER"].get("DERIVED_FROM_EVIDENCE_VERSION"),
                "DEPENDENCY_GRAPH": r["DEPENDENCY_GRAPH"].get("DERIVED_FROM_EVIDENCE_VERSION"),
                "QUESTIONS": r["QUESTIONS"].get("DERIVED_FROM_EVIDENCE_VERSION")},
            "BARRIER": r["EVIDENCE_BARRIER"]} for r in results},
        "RULE": "no register may describe an earlier snapshot; a register carrying a different version is "
                "describing a different moment and its numbers may not be read beside the others"}, prov)

    _write("OPENING_AREA_AND_DEDUCTION_REGISTER", {
        "WHAT": "each opening's area, taken from the final state, and the wall line it is deducted from",
        "BY_FLOOR": {r["FLOOR"]: {
            "EVIDENCE_VERSION": r["EVIDENCE_VERSION"],
            "OPENINGS": [{"OPENING_REF": o["OPENING_REF"], "TYPE": o["TYPE"],
                          "WIDTH_M": o["WIDTH_M"], "WIDTH_EVIDENCE": o["WIDTH_EVIDENCE"],
                          "HEIGHT_M": o["HEIGHT_M"], "HEIGHT_EVIDENCE": o["HEIGHT_EVIDENCE"],
                          "AREA_M2": o["AREA_M2"], "AREA_IS": o["AREA_IS"],
                          "DEDUCTED_FROM": o["HOST_COMPONENT_REF"],
                          "HOST_ASSIGNMENT_STATUS": o["HOST_ASSIGNMENT_STATUS"]}
                         for o in r["FINAL_OPENING_STATE"]["OPENINGS"]],
            "DEDUCTION_BY_WALL_LINE_M2": r["OPENING_REGISTER"]["DEDUCTION_BY_WALL_COMPONENT_M2"]}
            for r in results},
        "RULE": "the deduction uses the final area and no earlier snapshot of it"}, prov)

    _write("BLOCKER_SET_AND_ANSWER_IMPACT_REGISTER", {
        "WHAT": "per node, the set of facts holding it up; per fact, what answering it alone would release",
        "DEFINITIONS": results[0]["BLOCKER_SETS"]["DEFINITIONS"],
        "BY_FLOOR": {r["FLOOR"]: r["BLOCKER_SETS"] for r in results},
        "WHOLE_PROJECT": project_blockers,
        "ANSWER_IMPACT_SIMULATION": simulations,
        "RULE": results[0]["BLOCKER_SETS"]["RULE"]}, prov)

    _write("MATERIAL_SCOPE_REGISTER", {
        "WHAT": "the groups a material question is asked about, and how far an answer about one would travel",
        "BY_FLOOR": {r["FLOOR"]: MA.material_scope_register(r["WALL_IDENTITY"]["REGISTER"])
                     for r in results},
        "THIS_SOURCE_STATES": SOURCE_FACTS["MATERIAL_CLAIMS"]["WHY"],
        "SCOPE_ATTRIBUTES": list(MA.SCOPE_ATTRIBUTES)}, prov)

    _write("GEOMETRY_EXCLUSION_EVIDENCE_REGISTER", {
        "WHAT": "every band excluded from the trade, the positive evidence that excluded it, and every band "
                "whose shape alone would once have excluded it",
        "RULE": "exclusion is permanent and silent, so it needs positive evidence: the source naming a "
                "column, the same object drawn twice, or a junction already inside the walls that cross "
                "there.  A short band on its own is a question",
        "BY_FLOOR": {r["FLOOR"]: {
            "EXCLUDED": [{"COMPONENT_REF": x["COMPONENT_REF"], "REASON": x["GEOMETRY_ARTEFACT_REASON"],
                          "CONFIDENCE": x["GEOMETRY_CONFIDENCE"], "WHY": x["WHY_GEOMETRY"],
                          "ON_A_SOURCE_WALL_LAYER": x["ON_A_SOURCE_WALL_LAYER"],
                          "DUPLICATE_OF": x["DUPLICATE_OF"],
                          "COVERED_BY_CROSSING_WALLS": x["COVERED_BY_CROSSING_WALLS"]}
                         for x in r["WALL_IDENTITY"]["REGISTER"]
                         if x["GEOMETRY_IDENTITY"] == MA.NON_WALL_ARTEFACT],
            "SHORT_BUT_NOT_EXCLUDED": [
                {"COMPONENT_REF": x["COMPONENT_REF"],
                 "ASPECT_LENGTH_OVER_THICKNESS": x["ASPECT_LENGTH_OVER_THICKNESS"],
                 "ON_A_SOURCE_WALL_LAYER": x["ON_A_SOURCE_WALL_LAYER"],
                 "MATERIAL_LENGTH_M": x["MATERIAL_LENGTH_M"], "WHY": x["WHY_GEOMETRY"]}
                for x in r["WALL_IDENTITY"]["REGISTER"]
                if x["GEOMETRY_IDENTITY"] == MA.WALL_GEOMETRY_CANDIDATE
                and (x["ASPECT_LENGTH_OVER_THICKNESS"] or 99) < MA.WALL_ASPECT_MIN]}
            for r in results}}, prov)

    _write("REPORT_CLAIM_REGISTER", claims, prov)

    _write("BEFORE_AND_AFTER_R6_TO_R7", rec["BEFORE_AND_AFTER"], prov)
    rec.pop("_RESULTS", None)
    _write("ANTI_CALIBRATION_AUDIT", rec["ANTI_CALIBRATION_AUDIT"], prov)
    _write("ACCEPTANCE_GATE_R7", rec["ACCEPTANCE_GATE"], prov)
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['ARTIFACT']}  invariants {r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}")
    for f in r["FLOORS"]:
        print(f"  {f['FLOOR']:9s} source openings {f['SOURCE_OPENING_OBJECTS']:3d}  named "
              f"{f['NAMED_BY_THE_SOURCE']:3d}  physical {f['PHYSICAL_OPENINGS']:3d}  "
              f"host confirmed {f['HOST_CONFIRMED']:3d}  unresolved {f['HOST_UNRESOLVED']:3d}")
        print(f"             wall lines {f['WALL_LINES']:3d}  geometry {f['WALL_GEOMETRY']}")
        print(f"             material {f['WALL_MATERIAL']}  rows {f['ROW_CATEGORIES']}")
        print(f"             spaces {f['SPACES']:3d} ({f['SPACE_ASSEMBLY_OUTCOME']})  "
              f"root questions {f['ROOT_QUESTIONS']}  invariants {f['INVARIANTS']}  "
              f"acceptance {f['ACCEPTANCE']}")
    q = r["ROOT_QUESTIONS_AND_IMPACTS"]
    print(f"  root questions {q['ROOT_QUESTION_COUNT']} -> {q['ROOT_QUESTIONS_BY_KIND']}")
    print(f"  dependency impacts {q['DEPENDENCY_IMPACT_COUNT']}")
    print(f"  rows {r['FINAL_VERSUS_BLOCKED']['ROW_CATEGORIES']}")
    fb = r["FINAL_VERSUS_BLOCKED"]
    print(f"  wall lines {fb['WALL_LINE_STATUS']}")
    print(f"  row and line counts reconcile {fb['HOW_THE_TWO_COUNTS_AGREE']['RECONCILES']}")
    for k, s in sorted(r["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]["SUBTOTALS"].items()):
        print(f"    {k:>8}  {s['STATUS']:<24} final {s['FINAL_QUANTITY']}")
    print(f"  acceptance gate {'PASS' if r['ACCEPTANCE_GATE']['ALL_PASS'] else 'FAIL'} "
          f"({r['ACCEPTANCE_GATE']['OF']} checks)")
    print(f"  metamorphic {[(k, v['EQUIVALENT']) for k, v in r['METAMORPHIC'].items()]}")
    print(f"  anti-calibration audit {r['ANTI_CALIBRATION_AUDIT']['PASS']}")
    print(f"  frozen unchanged {not r['FROZEN_UNCHANGED']['REWRITTEN']}")
