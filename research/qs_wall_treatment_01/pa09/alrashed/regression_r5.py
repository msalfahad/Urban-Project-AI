"""Run the generic engine over this project's drawing, and report what it can and cannot settle.

This file is the only place the project and the engine meet.  It reads the same DWG the frozen takeoff read,
turns it into the generic engine's inputs, runs the generic pipeline, and compares the result with the frozen
artifact - as COMPARISON, never as a target.  Nothing here feeds a number back into the engine, and the engine
has no idea which project this is.

What the adapter declares, it declares as SOURCE FACTS with their provenance: how finely the drawing is authored,
the widest gap an opening can explain, and which evidence records answer a height.  It declares no thickness,
no total and no expected answer.  The frozen takeoff is opened read-only and is never rewritten.
"""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

from engine.qs_core import (acceptance, admission as AD, dependency as DEP, evidence as EV, geom, identity,
                            masonry as MA, pipeline, quantities as QY, space_validation as SV)
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
        "WHY": "the drawing is authored to the millimetre and its faces are snapped at this distance; two "
               "faces closer together than this are one face"},
    "DRAFTING_RESOLUTION_M": {
        "VALUE": G.SNAP_MM / 1000.0,
        "WHY": "the finest distance this drawing distinguishes.  A gap narrower than this is two lines that "
               "did not meet, not an object; a real opening narrower than this could not have been drawn"},
    "SLIVER_MIN_DIMENSION_M": {
        "VALUE": 0.45,
        "WHY": "no usable space in a villa of this kind is narrower than this; anything narrower is structure "
               "or drafting residue.  A statement about buildings, not a number chosen to make a total agree"},
    "MAX_OPENING_SPAN_M": {
        "VALUE": G.MAX_CLOSURE_M,
        "WHY": "the widest gap in a wall line that an opening in this building could account for.  It can "
               "REJECT a join; continuity still has to be proved by something spanning the gap"},
    "WALL_LAYER": {
        "VALUE": list(G.WALL_LAYERS),
        "WHY": "the layer this drawing puts wall lines on.  It is recorded as evidence and is NOT treated as "
               "proof of masonry: the artefact bands this round excludes are on the same layer, so the layer "
               "cannot tell them apart and nothing pretends it can"},
    "MASONRY_MATERIAL_ANNOTATIONS": {
        "VALUE": [],
        "WHY": "this source annotates no wall with a material.  Identity therefore rests on the thickness "
               "families the drawing itself uses, on shape, and on intersection topology"},
}

TOLERANCE_M = SOURCE_FACTS["TOLERANCE_M"]["VALUE"]
DRAFTING_RESOLUTION_M = SOURCE_FACTS["DRAFTING_RESOLUTION_M"]["VALUE"]
SLIVER_MIN_DIMENSION_M = SOURCE_FACTS["SLIVER_MIN_DIMENSION_M"]["VALUE"]
MAX_OPENING_SPAN_M = SOURCE_FACTS["MAX_OPENING_SPAN_M"]["VALUE"]


def wall_height_evidence():
    """The height of a wall, through the hierarchy.  The drawing states none, so the owner's record answers."""
    rec = OI.PROJECT_INPUTS["AL_RASHED_WALL_HEIGHT"]
    return EV.resolve("wall height",
                      [EV.Claim(rec["VALUE_M"], EV.OWNER_PROJECT_INPUT, rec["FROM"],
                                {"KIND": rec["KIND"], "PRECEDENCE": rec.get("PRECEDENCE")})],
                      TOLERANCE_M)


def opening_height_claims(kind, width=None):
    """Every record that could answer this opening's height, at the rank its authority gives it.

    Nothing here copies an area from the frozen takeoff.  These are the project's own evidence records, offered
    to the generic resolver, which picks by authority and reports the ones it passed over.
    """
    claims = []
    key = {"DOOR": "AL_RASHED_DOOR_HEIGHT", "WINDOW": "AL_RASHED_PROJECT_WINDOW_HEIGHT"}.get(kind)
    if key:
        rec = OI.PROJECT_INPUTS[key]
        claims.append(EV.Claim(rec["VALUE_M"], EV.OWNER_PROJECT_INPUT, rec["FROM"],
                               {"KIND": rec["KIND"], "PRECEDENCE": rec.get("PRECEDENCE"),
                                "WHY": "the owner stated this height for this project"}))
    if kind == "WINDOW":
        # the approved guide ranks below the owner's own statement and is offered so the record shows it was
        # considered; where the owner had said nothing it would answer
        band = WS.TABLE.get("LIVING_ROOM")
        if band:
            claims.append(EV.Claim(band["H"], EV.APPROVED_GUIDE, f"{WS.VERSION}::LIVING_ROOM",
                                   {"RULE_ID": WS.RULE_ID,
                                    "WHY": "the approved guide's height for a room of this use"}))
    return claims


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def _cell_rect(g, i, j):
    return geom.Rect(g["XS"][i], g["YS"][j], g["XS"][i + 1], g["YS"][j + 1])


def _column_cells(g):
    """Cells bounded on both axes by lines the source draws on its column layer.

    A column that stands in a wall line is measured as a wall unless the drawing's own layering is read, and a
    column is structure: its quantity is not wall area.
    """
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
    """Split a set of grid cells into the pieces that actually touch each other."""
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


def _local_depth(g, x, y, runs):
    """How deep the drawing makes this opening: the extent of the cell it sits in, across its own run."""
    xs, ys = g["XS"], g["YS"]
    if runs == "ALONG_X":
        for j in range(len(ys) - 1):
            if ys[j] <= y <= ys[j + 1]:
                return ys[j + 1] - ys[j]
        return TOLERANCE_M
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return xs[i + 1] - xs[i]
    return TOLERANCE_M


def extract_floor(ents, floor):
    """Turn one plan window into the generic engine's inputs.  No quantity is computed here."""
    g = G.grid(ents, G.WINDOWS[floor])
    comps = G.rooms(g)
    wall_cells = {(c["I"], c["J"]): c for c in G.wall_cells(g)}
    column_cells = _column_cells(g)
    tr, labs = L.labels_in_drawing(floor, ents)

    components, annotations = [], {}
    for (i, j), w in sorted(wall_cells.items()):
        ref = f"{floor[:2]}-W-{i:03d}-{j:03d}"
        is_column = (i, j) in column_cells
        components.append(GeometryComponent(
            ref, KIND_COLUMN if is_column else KIND_WALL_BAND, [_cell_rect(g, i, j)], floor, REVISION,
            thickness=round(w["THICKNESS_M"], 4),
            axis=geom.AXIS_Y if w["AXIS"] == "V" else geom.AXIS_X,
            layer=G.COLUMN_LAYERS[0] if is_column else G.WALL_LAYERS[0]))
        annotations[ref] = {"LAYER": components[-1].layer,
                            "MATERIAL": None,
                            "WHY": "the source names the layer and states no material"}
    for k, c in enumerate(comps):
        free = sorted(set(c["CELLS"]) - set(wall_cells))
        if not free:
            continue
        for n, group in enumerate(_connected(free)):
            ref = f"{floor[:2]}-{k:03d}" if n == 0 else f"{floor[:2]}-{k:03d}-{n}"
            components.append(GeometryComponent(
                ref, KIND_FLOOR_REGION, [_cell_rect(g, i, j) for i, j in group], floor, REVISION))

    # ---------------------------------------------------------- opening candidates, with their provenance
    candidates = []
    bn = Q._block_names()
    for o in Q.opening_register(ents, floor, g, bn):
        if o["WIDTH_M"] is None:
            continue
        depth = _local_depth(g, o["X"], o["Y"], o["RUNS"])
        w = o["WIDTH_M"]
        if o["RUNS"] == "ALONG_X":
            rect = geom.Rect(o["X"] - w / 2, o["Y"] - depth / 2, o["X"] + w / 2, o["Y"] + depth / 2)
            axis = geom.AXIS_X
        else:
            rect = geom.Rect(o["X"] - depth / 2, o["Y"] - w / 2, o["X"] + depth / 2, o["Y"] + w / 2)
            axis = geom.AXIS_Y
        named = o["TYPE_SOURCE"] == "CAD_SYMBOL_IN_THE_OPENING"
        c = AD.Candidate(o["OPENING_REF"], rect, floor, REVISION, axis=axis, opening_type=o["TYPE"],
                         origin="DRAWING_REGISTER",
                         block_ref=(f"{G.DOOR_LAYERS[0] if o['TYPE'] == 'DOOR' else G.WINDOW_LAYERS[0]}"
                                    f"::{o['OPENING_REF']}") if named else None)
        c.width_claims = [EV.Claim(o["WIDTH_M"], EV.MEASURED_GEOMETRY, f"JAMB_TO_JAMB::{o['OPENING_REF']}",
                                   {"WHY": "the clear width between the jambs the drawing draws"})]
        c.height_claims = opening_height_claims(o["TYPE"], o["WIDTH_M"])
        candidates.append(c)

    for n, gl in enumerate(FT.glazed_openings(floor, ents)):
        w, d = gl["WIDTH_M"], gl["HOST_WALL_THICKNESS_M"]
        if gl["RUNS"] == "ALONG_X":
            rect = geom.Rect(gl["X"] - w / 2, gl["Y"] - d / 2, gl["X"] + w / 2, gl["Y"] + d / 2)
            axis = geom.AXIS_X
        else:
            rect = geom.Rect(gl["X"] - d / 2, gl["Y"] - w / 2, gl["X"] + d / 2, gl["Y"] + w / 2)
            axis = geom.AXIS_Y
        ref = f"{floor[:2]}-GL-{n:03d}"
        c = AD.Candidate(ref, rect, floor, REVISION, axis=axis, opening_type="WINDOW",
                         origin="EXTRACTED_GEOMETRY",
                         symbol="GLAZED_RECTANGLE_PUNCHED_THROUGH_THE_WALL",
                         layer=G.WINDOW_LAYERS[0])
        c.width_claims = [EV.Claim(w, EV.MEASURED_GEOMETRY, f"GLAZED_RECTANGLE::{ref}",
                                   {"WHY": "the plotted rectangle IS the clear opening"})]
        # the height the project's own evidence gives a window, through the hierarchy - never an area copied
        # back from any previous result
        c.height_claims = opening_height_claims("WINDOW", w)
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
            "ANNOTATIONS": annotations, "GRID": g}


def project_thickness_families(plans):
    """The thickness families of the WHOLE villa, discovered once and used on every floor.

    Which thicknesses a building uses is a fact about the building.  Asking the question one storey at a time
    makes a partition that appears once in the basement and thirty times upstairs an unknown object down there
    and a wall up here, which is the same answer depending on where you stand.
    """
    import copy

    lines = []
    for plan in plans.values():
        probe = pipeline.run(copy.deepcopy(plan), max_opening_span=MAX_OPENING_SPAN_M,
                             drafting_resolution_m=DRAFTING_RESOLUTION_M,
                             annotations=plan["ANNOTATIONS"], masonry_materials=())
        lines += probe["WALL_LINE_OBJECTS"]
    return MA.thickness_families(lines, TOLERANCE_M)


def run_floor(ents, floor, plan=None, families=None):
    plan = plan if plan is not None else extract_floor(ents, floor)
    result = pipeline.run(plan, max_opening_span=MAX_OPENING_SPAN_M, thickness_families=families,
                          drafting_resolution_m=DRAFTING_RESOLUTION_M,
                          wall_height_evidence=wall_height_evidence(),
                          plan_window_area=plan["PLAN_WINDOW_AREA_M2"], closure_tolerance=1e-6,
                          annotations=plan["ANNOTATIONS"],
                          # this source annotates no wall with a material, so none is declared masonry by name
                          masonry_materials=())
    result["FLOOR"] = floor
    result["PLAN"] = plan
    return result


# ------------------------------------------------------------------ metamorphic evidence on the real drawing
def metamorphic_evidence(ents, floor, families=None):
    """Run the real plan again, described differently, and compare the quantities.

    This is the check that distinguishes measuring from pattern-matching, and it is run against the real
    drawing rather than only against fixtures.
    """
    from engine.qs_core import transforms as TR

    base_plan = extract_floor(ents, floor)

    def measure(plan):
        return TR.quantity_fingerprint(pipeline.run(
            plan, max_opening_span=MAX_OPENING_SPAN_M, drafting_resolution_m=DRAFTING_RESOLUTION_M,
            wall_height_evidence=wall_height_evidence(), annotations=plan["ANNOTATIONS"],
            masonry_materials=(), thickness_families=families))

    base = measure(base_plan)
    moved = measure(TR.transform_plan(extract_floor(ents, floor), dx=1234.5, dy=-987.25, quarter_turns=1))
    cut = measure(TR.resegment_plan(extract_floor(ents, floor), cuts=3))

    def same(a, b, keys):
        return all(a[k] == b[k] for k in keys)

    keys = ("WALLS", "BLOCKED", "SPACES", "OPENINGS")
    return {
        "RIGID_MOTION": {"EQUIVALENT": same(base, moved, keys),
                         "TRANSFORM": "translated by (1234.5, -987.25) m and turned through one right angle",
                         "WHY": "the same building, drawn somewhere else and turned round, is the same "
                                "building; a quantity that moves depends on the drawing's coordinates",
                         "DIFFERENCES": {k: [base[k], moved[k]] for k in keys if base[k] != moved[k]}},
        "SEGMENTATION": {"EQUIVALENT": same(base, cut, keys), "CUTS_PER_WALL_BAND": 3,
                         "WHY": "how finely the extractor chops a wall is a property of the extractor, not "
                                "of the wall",
                         "DIFFERENCES": {k: [base[k], cut[k]] for k in keys if base[k] != cut[k]}},
        "REPRESENTATION": {"EQUIVALENT": same(base, cut, keys) and same(base, moved, keys),
                           "WHY": "on this source the two representations of one wall - drawn through its "
                                  "opening, or stopped at each jamb - are exercised by the per-line basis "
                                  "register, and by the segmentation case above",
                           "BASIS_VALUES_FOUND": None},
    }


# ------------------------------------------------------------------ comparison with the frozen artifact
def frozen_record():
    return json.loads(FROZEN.read_text("utf-8"))


def final_versus_blocked(results):
    """What is finished, what is not, and what each unfinished figure is waiting for.

    No blocked row contributes to any number in this report.  Where a subtotal is not final it is null, and the
    diagnostic arithmetic beside it is named so that it cannot be added to anything.
    """
    rows = [dict(r, FLOOR=res["FLOOR"]) for res in results for r in res["WALL_ROWS"]]
    masonry = [r for r in rows if r["STATUS"] != "EXCLUDED_NOT_MASONRY"]
    project = QY.publish(masonry, lambda r: r["THICKNESS_FAMILY_M"], "NET_AREA_M2", "m2",
                         "masonry wall area by thickness, whole project",
                         blocked_groups={k: {"KIND": "SUBTOTAL_BLOCKED_ON_A_FLOOR", "WHY": v, "DETAIL": k}
                                         for k, v in _blocked_groups(results).items()})
    return {
        "WHOLE_PROJECT": project,
        "BY_FLOOR": {res["FLOOR"]: res["PUBLICATION"] for res in results},
        "FINAL_ROWS": sum(1 for r in rows if r["STATUS"] == QY.FINAL),
        "BLOCKED_ROWS": sum(1 for r in rows if r["STATUS"] == "BLOCKED_PENDING_ANSWERS"),
        "EXCLUDED_ROWS": [{"COMPONENT_REF": r["COMPONENT_REF"], "FLOOR": r["FLOOR"],
                           "THICKNESS_M": r["THICKNESS_M"], "WALL_IDENTITY": r["WALL_IDENTITY"],
                           "WHY": r["EXCLUDED_BECAUSE"]}
                          for r in rows if r["STATUS"] == "EXCLUDED_NOT_MASONRY"],
        "RULE": "a subtotal is a number only when every row behind it is final; otherwise it is null and the "
                "question register says what has to be answered first",
    }


def _blocked_groups(results):
    out = {}
    for res in results:
        graph = res["DEPENDENCY_GRAPH"]
        for node in graph["BLOCKED_SUBTOTALS"]:
            key = node.split("::", 1)[1]
            key = None if key == "None" else float(key)
            out[key] = graph["BLOCKED"][node]["REASONS"][0]["WHY"]
    return out


def compare(results, frozen):
    """What the general algorithms changed, and what they now decline to state, each with a trace.

    These are DIFFERENCES, not corrections to the frozen artifact, which is unchanged.  Where the engine no
    longer publishes a figure the frozen one published, that is reported as a withdrawal with its reason - not
    as a new figure, and not as agreement.
    """
    old_rooms = {r["ROOM_REF"]: r for f in frozen["FLOORS"] for r in f["ROOMS"]}
    old_by_thickness = collections.Counter()
    for b in frozen["BLOCKWORK"]:
        old_by_thickness[b["THICKNESS_MM"]] += b["NET_AREA_M2"]

    published = final_versus_blocked(results)["WHOLE_PROJECT"]["SUBTOTALS"]
    lines = []
    for t in sorted(old_by_thickness):
        key = str(round(t / 1000.0, 6))
        sub = published.get(key)
        lines.append({
            "QUANTITY": f"BLOCKWORK_{t}", "UNIT": "m2",
            "FROZEN_M2": round(old_by_thickness[t], 3),
            "ENGINE_FINAL_M2": None if sub is None else sub["FINAL_QUANTITY"],
            "ENGINE_STATUS": "NOT_PRODUCED" if sub is None else sub["STATUS"],
            "WAITING_ON": None if sub is None else sub["WAITING_ON"],
            "COMPARABLE": bool(sub and sub["FINAL_QUANTITY"] is not None),
            "WHY": "the frozen figure shared each floor's openings across thicknesses in proportion to wall "
                   "length, measured every band that had a thickness, and stated one opening basis for the "
                   "whole drawing; this run assigns each opening to one host, establishes what each band is "
                   "before measuring it, and measures the basis line by line",
            "TRACE": "OPENING_ADMISSION -> HOST -> WALL_LINE -> IDENTITY -> BASIS -> DEPENDENCY -> SUBTOTAL"})
    for key, sub in sorted(published.items()):
        if any(l["QUANTITY"] == f"BLOCKWORK_{round(float(key) * 1000)}" for l in lines):
            continue
        lines.append({"QUANTITY": f"BLOCKWORK_{round(float(key) * 1000)}", "UNIT": "m2", "FROZEN_M2": None,
                      "ENGINE_FINAL_M2": sub["FINAL_QUANTITY"], "ENGINE_STATUS": sub["STATUS"],
                      "WAITING_ON": sub["WAITING_ON"], "COMPARABLE": False,
                      "WHY": "a thickness family this run measures that the frozen run did not report",
                      "TRACE": "MASONRY_IDENTITY -> THICKNESS_FAMILY -> SUBTOTAL"})

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

    new_kinds = collections.Counter(m["KIND"] for res in results for m in res["MEMBERSHIP_REGISTER"])
    return {
        "BLOCKWORK_LINES": lines,
        "SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS": sorted(merges, key=lambda m: -m["AREA_M2"]),
        "COMPONENT_CENSUS": {
            "FROZEN_COMPONENTS": len(old_rooms),
            "FROZEN_ROLE_COUNTS": dict(collections.Counter(r["ROLE"] for r in old_rooms.values())),
            "NEW_COMPONENTS": sum(len(res["MEMBERSHIP_REGISTER"]) for res in results),
            "NEW_KIND_COUNTS": dict(new_kinds),
            "NEW_SPACE_COUNT": sum(len(res["SPACES"]) for res in results)},
        "RULE": "these are differences, not corrections to the frozen artifact, which is unchanged; each one "
                "is accepted or rejected on the drawing evidence in its TRACE and on nothing else.  A figure "
                "the engine declines to state is not a figure of zero and is not agreement",
    }


# ------------------------------------------------------------------ provenance
ENGINE_SOURCES = sorted(str(p) for p in Path("engine/qs_core").glob("*.py"))
ADAPTER_SOURCE = "research/qs_wall_treatment_01/pa09/alrashed/regression_r5.py"

FORBIDDEN_IN_THE_ENGINE = [
    "ALRASHED", "AL RASHED", "AL_RASHED", "QORTUBA", "SABAH", "P7757", "7757",
    "963.188", "190.289", "1493.945", "474.693", "155.206", "128.816", "67.563",
    "220.42", "1087.388", "734.638", "931.016",
    "BA-0", "GR-0", "FI-0", "AR-FL", "AR-BL", "AR-W-", "AR-01", "AR-02", "AR-03", "US-18", "US-19",
    "16-11-2025", ".dwg", ".pdf",
]


def provenance():
    """Four different things, kept apart because conflating them is how a package stops being checkable."""
    head = _git("rev-parse", "HEAD")
    return {
        "GENERATING_COMMIT": {"SHA": head, "SHORT": head[:7],
                              "WHAT": "the commit of the code that produced these registers",
                              "WORKING_TREE_CLEAN": _git("status", "--porcelain") == ""},
        "SOURCE_ARTIFACT_COMMIT": {
            "SHA": _git("log", "-1", "--format=%H", "--", str(FROZEN)) or None,
            "PATH": str(FROZEN),
            "WHAT": "the commit that last touched the source artifact this run reads"},
        "FROZEN_ARTIFACT": {
            "PATH": str(FROZEN), "SHA256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
            "WHAT": "the digest of the frozen takeoff, opened read-only and never rewritten"},
        "PACKAGING_COMMIT": {"SHA": None,
                             "WHAT": "the commit at which the deliverable zip was assembled; it is written by "
                                     "the packager, not by this run, because it cannot be known here"},
        "ENGINE_SOURCES": ENGINE_SOURCES,
        "ADAPTER_SOURCE": ADAPTER_SOURCE,
    }


def anti_calibration_audit():
    """The engine may not contain a project name, a known total or a branch on which project is running."""
    from engine.qs_core import invariants as INV

    check = INV.no_comparison_input([Path(p) for p in ENGINE_SOURCES], FORBIDDEN_IN_THE_ENGINE)
    import re
    branch_hits = []
    for p in ENGINE_SOURCES:
        text = Path(p).read_text("utf-8")
        for pat in (r"if\s+project\b", r"project\s*==", r"PROJECT_ID\s*==",
                    r"if\s+.*\bfloor\s*==\s*[\"']"):
            for m in re.finditer(pat, text):
                branch_hits.append({"FILE": p, "PATTERN": pat,
                                    "LINE": text.count("\n", 0, m.start()) + 1})
    return {
        "WHAT": "the generic engine is read and must contain no project name, no previously reported total, "
                "no reference from a real drawing and no branch on which project is running",
        "TOKEN_SCAN": check,
        "PROJECT_BRANCH_SCAN": {"PATTERNS": 4, "HITS": branch_hits},
        "FILES_SCANNED": ENGINE_SOURCES,
        "PASS": check["PASS"] and not branch_hits,
        "WHAT_IT_DOES_NOT_PROVE": "that the engine is correct.  It proves only that it cannot be reproducing "
                                  "an answer it was told",
    }


def _write(name, payload, prov):
    path = OUT / f"ALRASHED_{name}.json"
    path.write_text(json.dumps(
        {"ARTIFACT": f"ALRASHED_{name}", "SOURCE_REVISION": REVISION, "PROVENANCE": prov,
         "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         **payload}, indent=1, ensure_ascii=False, default=str), "utf-8")
    return path


def finish():
    before = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    prov = provenance()
    ents = G.load()
    plans = {f: extract_floor(ents, f) for f in TK.FLOORS}
    families = project_thickness_families(plans)
    results = [run_floor(ents, f, plan=plans[f], families=families) for f in TK.FLOORS]
    meta = {f["FLOOR"]: metamorphic_evidence(ents, f["FLOOR"], families) for f in
            [{"FLOOR": r["FLOOR"]} for r in results]}
    project_meta = {key: {"EQUIVALENT": all(meta[f][key]["EQUIVALENT"] for f in meta),
                          "BY_FLOOR": {f: meta[f][key] for f in meta}}
                    for key in ("RIGID_MOTION", "SEGMENTATION", "REPRESENTATION")}

    graded = {res["FLOOR"]: acceptance.grade(pipeline.acceptance_document(res, metamorphic=meta[res["FLOOR"]]))
              for res in results}

    frozen = frozen_record()
    comparison = compare(results, frozen)
    quantities = final_versus_blocked(results)

    all_checks = [c for res in results for c in res["INVARIANTS"]["CHECKS"]]
    lineage = []
    for res in results:
        rerun = run_floor(ents, res["FLOOR"], families=families)
        lineage += identity.match_revisions(res["PLAN"]["COMPONENTS"], rerun["PLAN"]["COMPONENTS"], 0.05)

    rec = {
        "ARTIFACT": "ALRASHED_GENERIC_ENGINE_VALIDATION",
        "ENGINE": "engine.qs_core",
        "SOURCE_REVISION": REVISION,
        "PROVENANCE": prov,
        "DECLARED_SOURCE_FACTS": SOURCE_FACTS,
        "THICKNESS_FAMILIES_OF_THE_WHOLE_SOURCE": families,
        "WALL_HEIGHT_EVIDENCE": wall_height_evidence(),
        "FLOORS": [{"FLOOR": r["FLOOR"], "COMPONENTS": len(r["MEMBERSHIP_REGISTER"]),
                    "SPACES": len(r["SPACES"]),
                    "SPACE_ASSEMBLY_OUTCOME": r["SPACE_VALIDATION"]["OUTCOME"],
                    "WALL_LINES": len(r["WALL_LINES"]),
                    "OPENING_CANDIDATES": r["OPENING_POPULATION"]["CANDIDATES_IN"],
                    "OPENING_CLASSES": r["OPENING_POPULATION"]["COUNTS"],
                    "WALL_IDENTITIES": r["WALL_IDENTITY"]["COUNTS"],
                    "WALL_LINES_RELEASED": len(r["DEPENDENCY_GRAPH"]["RELEASED_WALL_LINES"]),
                    "WALL_LINES_BLOCKED": len(r["DEPENDENCY_GRAPH"]["BLOCKED_WALL_LINES"]),
                    "INVARIANTS": f"{r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}",
                    "ACCEPTANCE": f"{graded[r['FLOOR']]['PASSED']}/{graded[r['FLOOR']]['OF']}"}
                   for r in results],
        "FINAL_VERSUS_BLOCKED": quantities,
        "ACCEPTANCE_GATE": {"BY_FLOOR": graded,
                            "ALL_PASS": all(g["ALL_PASS"] for g in graded.values()),
                            "BLOCKERS": [b for g in graded.values() for b in g["BLOCKERS"]]},
        "METAMORPHIC": project_meta,
        "UNRESOLVED": [dict(q, FLOOR=r["FLOOR"]) for r in results for q in r["UNRESOLVED"]],
        "LINEAGE_ON_AN_IDENTICAL_RERUN": identity.lineage_summary(lineage),
        "INVARIANTS": {"PASSED": sum(1 for c in all_checks if c["PASS"]), "OF": len(all_checks),
                       "ALL_PASS": all(c["PASS"] for c in all_checks),
                       "FAILURES": [c for c in all_checks if not c["PASS"]]},
        "ANTI_CALIBRATION_AUDIT": anti_calibration_audit(),
        "COMPARISON_WITH_THE_FROZEN_ARTIFACT": comparison,
        "FROZEN_UNCHANGED": {"SHA256_BEFORE": before,
                             "SHA256_AFTER": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
                             "REWRITTEN": False},
        "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    assert rec["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == rec["FROZEN_UNCHANGED"]["SHA256_AFTER"]
    OUT.mkdir(parents=True, exist_ok=True)
    written = [_write("GENERIC_ENGINE_VALIDATION", rec, prov)]

    written.append(_write("OPENING_ADMISSION_REGISTER", {
        "WHAT": "every opening candidate the sources offer - extracted geometry, the drawing's own register "
                "and the schedule - normalised to one physical population before anything is hosted",
        "CLASSES": list(AD.CLASSES), "NAMING_PROVENANCE": list(AD.NAMING_PROVENANCE),
        "BY_FLOOR": {r["FLOOR"]: r["OPENING_POPULATION"] for r in results}}, prov))

    written.append(_write("PER_WALL_OPENING_BASIS_REGISTER", {
        "WHAT": "for every wall line: whether its drawn material spans its openings or stops at the jambs, "
                "how that was detected, which openings were tested, and the status that follows",
        "REPLACES": "a single source-wide boolean, which was an assumption about a mixed population",
        "BY_FLOOR": {r["FLOOR"]: r["OPENING_BASIS"] for r in results}}, prov))

    written.append(_write("MASONRY_IDENTITY_REGISTER", {
        "WHAT": "what each measurable band IS, decided before anything measures it",
        "IDENTITIES": list(MA.IDENTITIES), "BILLABLE": list(MA.BILLABLE),
        "BY_FLOOR": {r["FLOOR"]: r["WALL_IDENTITY"] for r in results}}, prov))

    written.append(_write("DEPENDENCY_AND_BLOCKING_REGISTER", {
        "WHAT": "opening -> candidate hosts -> wall lines -> thickness subtotal -> bill line, and the nodes "
                "whose value each open question could change",
        "BY_FLOOR": {r["FLOOR"]: r["DEPENDENCY_GRAPH"] for r in results}}, prov))

    written.append(_write("SPACE_ASSEMBLY_VALIDATION", {
        "WHAT": "whether this drawing exercised multi-component room assembly, with the seam evidence behind "
                "every merge and behind every pair of fragments kept apart",
        "OUTCOMES": [SV.ALGORITHM_RAN, SV.VALIDATED, SV.NO_CASE, SV.CONTRADICTION],
        "BY_FLOOR": {r["FLOOR"]: r["SPACE_VALIDATION"] for r in results}}, prov))

    written.append(_write("FINAL_VERSUS_BLOCKED_QUANTITY_REPORT", {
        "WHAT": "what is finished, what is not, and what each unfinished figure is waiting for",
        **quantities,
        "COMPARISON_WITH_THE_FROZEN_ARTIFACT": comparison["BLOCKWORK_LINES"]}, prov))

    written.append(_write("OPENING_TO_HOST_REGISTER", {
        "WHAT": "every confirmed opening, the wall line that hosts it, the evidence, and what is blocked "
                "where no host is proved",
        "ALLOCATION_RULE": "one host or none; no deduction is ever divided",
        "BY_FLOOR": {r["FLOOR"]: r["OPENING_REGISTER"] for r in results},
        "WALL_LINE_QUANTITIES": {r["FLOOR"]: r["WALL_ROWS"] for r in results}}, prov))

    written.append(_write("COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER", {
        "WHAT": "every geometry component, the room it belongs to or the reason it belongs to none, and the "
                "seam evidence behind each decision",
        "BY_FLOOR": {r["FLOOR"]: r["MEMBERSHIP_REGISTER"] for r in results},
        "SEAMS": {r["FLOOR"]: r["SEAM_REGISTER"] for r in results},
        "SPACES": {r["FLOOR"]: r["SPACES"] for r in results}}, prov))

    written.append(_write("ENTITY_LINEAGE_REGISTER", {
        "WHAT": "what happened to every entity between two runs of the engine over the same source",
        "SUMMARY": rec["LINEAGE_ON_AN_IDENTICAL_RERUN"], "RECORDS": lineage}, prov))

    written.append(_write("ANTI_CALIBRATION_AUDIT", rec["ANTI_CALIBRATION_AUDIT"], prov))

    rec["WRITTEN"] = [str(p) for p in written]
    (OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['ARTIFACT']}  invariants {r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}")
    for f in r["FLOORS"]:
        print(f"  {f['FLOOR']:9s} components {f['COMPONENTS']:4d}  spaces {f['SPACES']:3d} "
              f"({f['SPACE_ASSEMBLY_OUTCOME']})")
        print(f"             wall lines {f['WALL_LINES']:3d} "
              f"(released {f['WALL_LINES_RELEASED']}, blocked {f['WALL_LINES_BLOCKED']})  "
              f"invariants {f['INVARIANTS']}  acceptance {f['ACCEPTANCE']}")
        print(f"             openings {f['OPENING_CANDIDATES']:3d} -> {f['OPENING_CLASSES']}")
        print(f"             identities {f['WALL_IDENTITIES']}")
    print("  final versus blocked:")
    for k, s in sorted(r["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]["SUBTOTALS"].items()):
        print(f"    {k:>8}  {s['STATUS']:<24} final {s['FINAL_QUANTITY']}")
    print(f"  acceptance gate: {'PASS' if r['ACCEPTANCE_GATE']['ALL_PASS'] else 'FAIL'}")
    print(f"  metamorphic: {[(k, v['EQUIVALENT']) for k, v in r['METAMORPHIC'].items()]}")
    print(f"  unresolved questions: {len(r['UNRESOLVED'])}")
    print(f"  anti-calibration audit: {r['ANTI_CALIBRATION_AUDIT']['PASS']}")
    print(f"  frozen unchanged: {not r['FROZEN_UNCHANGED']['REWRITTEN']}")
