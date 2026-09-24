"""Run the generic engine over this project's drawing, and report what changed and why.

This file is the only place the project and the engine meet.  It reads the same DWG the frozen takeoff read,
turns it into the generic engine's inputs, runs the generic pipeline, and then compares the result with the
frozen artifact - as COMPARISON, never as a target.  Nothing here feeds a number back into the engine, and the
engine has no idea which project this is.

The frozen takeoff is opened read-only and is never rewritten.
"""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

from engine.qs_core import geom, identity, invariants, openings as qop, pipeline, spaces as qsp
from engine.qs_core.entities import (GeometryComponent, KIND_FLOOR_REGION, KIND_WALL_BAND, Label, Opening)
from engine.qs_core.spaces import Barrier
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import (final_takeoff as FT, geometry as G, labels as L,
                                                          owner_inputs as OI, quantities as Q, takeoff as TK)

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN = OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json"

# Properties of THIS source, declared here and passed to the engine as arguments.  The engine holds none of them.
TOLERANCE_M = G.SNAP_MM / 1000.0          # the drawing is authored to the millimetre; faces within 5 mm are one
# No usable space in a villa of this kind is narrower than this; anything narrower is structure or drafting
# residue.  It is a statement about buildings and about how this drawing was authored - not a number chosen to
# make a total agree with anything.
SLIVER_MIN_DIMENSION_M = 0.45
MAX_OPENING_SPAN_M = G.MAX_CLOSURE_M      # the widest gap in a wall line an opening can explain
WALL_HEIGHT_M = OI.AR01_WALL_HEIGHT_M     # an owner input (AR-01), carried as evidence, never as a constant here
REVISION = "16-11-2025-R3"


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def _cell_rect(g, i, j):
    return geom.Rect(g["XS"][i], g["YS"][j], g["XS"][i + 1], g["YS"][j + 1])


def extract_floor(ents, floor):
    """Turn one plan window into the generic engine's inputs.  No quantity is computed here."""
    g = G.grid(ents, G.WINDOWS[floor])
    comps = G.rooms(g)
    wall_cells = {(c["I"], c["J"]): c for c in G.wall_cells(g)}
    tr, labs = L.labels_in_drawing(floor, ents)

    # Wall material is wall material wherever it sits: the wall cells come out first, one component each, and
    # what is left of a connected region is floor.  Classifying a whole region by its average width would call a
    # wall that turns a corner "a room", which is how wall material ends up carrying floor finish.
    components = []
    for (i, j), w in sorted(wall_cells.items()):
        components.append(GeometryComponent(
            f"{floor[:2]}-W-{i:03d}-{j:03d}", KIND_WALL_BAND, [_cell_rect(g, i, j)], floor, REVISION,
            thickness=round(w["THICKNESS_M"], 4),
            axis=geom.AXIS_Y if w["AXIS"] == "V" else geom.AXIS_X, layer="WALL"))
    for k, c in enumerate(comps):
        free = sorted(set(c["CELLS"]) - set(wall_cells))
        if not free:
            continue
        for n, group in enumerate(_connected(free)):
            ref = f"{floor[:2]}-{k:03d}" if n == 0 else f"{floor[:2]}-{k:03d}-{n}"
            components.append(GeometryComponent(
                ref, KIND_FLOOR_REGION, [_cell_rect(g, i, j) for i, j in group], floor, REVISION))

    openings = []
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
        openings.append(Opening(o["OPENING_REF"], rect, floor, REVISION, opening_type=o["TYPE"],
                                width=o["WIDTH_M"], height=o["HEIGHT_M"],
                                width_source=o["WIDTH_SOURCE"], height_source=o["HEIGHT_SOURCE"], axis=axis))
    for n, gl in enumerate(FT.glazed_openings(floor, ents)):
        w, d = gl["WIDTH_M"], gl["HOST_WALL_THICKNESS_M"]
        if gl["RUNS"] == "ALONG_X":
            rect = geom.Rect(gl["X"] - w / 2, gl["Y"] - d / 2, gl["X"] + w / 2, gl["Y"] + d / 2)
            axis = geom.AXIS_X
        else:
            rect = geom.Rect(gl["X"] - d / 2, gl["Y"] - w / 2, gl["X"] + d / 2, gl["Y"] + w / 2)
            axis = geom.AXIS_Y
        openings.append(Opening(f"{floor[:2]}-GL-{n:03d}", rect, floor, REVISION, opening_type="WINDOW",
                                width=w, height=None, width_source="MEASURED_FROM_PROJECT_GEOMETRY",
                                height_source="NOT_ESTABLISHED", axis=axis))

    # Everything the source draws between two pieces of floor is carried to the engine as what it is.  A column
    # line is material; a break the extractor spanned in a wall line is a gap whose contents the source does not
    # state.  Leaving either out makes the engine read a boundary as open floor.
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
    window = G.WINDOWS[floor]
    area = (window[1] - window[0]) * (window[3] - window[2])
    return {"COMPONENTS": components, "BARRIERS": barriers, "OPENINGS": openings, "LABELS": labels,
            "REVISION": REVISION, "TOLERANCE_M": TOLERANCE_M,
            "SLIVER_MIN_DIMENSION_M": SLIVER_MIN_DIMENSION_M,
            "PLAN_WINDOW_AREA_M2": sum(c.area for c in components), "GRID": g}


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


def run_floor(ents, floor):
    plan = extract_floor(ents, floor)
    result = pipeline.run(plan, max_opening_span=MAX_OPENING_SPAN_M, wall_height=WALL_HEIGHT_M,
                          plan_window_area=plan["PLAN_WINDOW_AREA_M2"], closure_tolerance=1e-6,
                          # this extractor stops the wall at each jamb, so the wall over a door is added back
                          # before the door is deducted
                          wall_geometry_includes_openings=False)
    result["FLOOR"] = floor
    result["PLAN"] = plan
    return result


# ------------------------------------------------------------------ comparison with the frozen artifact
def frozen_record():
    return json.loads(FROZEN.read_text("utf-8"))


def compare(results, frozen):
    """What the general algorithms changed, quantity by quantity, with a trace for each."""
    old_rooms = {r["ROOM_REF"]: r for f in frozen["FLOORS"] for r in f["ROOMS"]}
    old_block = frozen["BLOCKWORK"]

    new_by_thickness, new_by_floor_thickness = collections.Counter(), collections.Counter()
    blocked = []
    for res in results:
        for row in res["WALL_ROWS"]:
            t = None if row["THICKNESS_M"] is None else round(row["THICKNESS_M"] * 1000)
            new_by_thickness[t] += row["NET_AREA_M2"]
            new_by_floor_thickness[(res["FLOOR"], t)] += row["NET_AREA_M2"]
            if row["STATUS"] != "FINAL_QUANTITY_AVAILABLE":
                blocked.append({"FLOOR": res["FLOOR"], "WALL_LINE": row["COMPONENT_REF"],
                                "THICKNESS_MM": t, "WHY": row["BLOCKED_NOTE"]})
    old_by_thickness = collections.Counter()
    for b in old_block:
        old_by_thickness[b["THICKNESS_MM"]] += b["NET_AREA_M2"]

    deltas = []
    for t in sorted(set(list(old_by_thickness) + [k for k in new_by_thickness if k])):
        o, n = old_by_thickness.get(t, 0.0), new_by_thickness.get(t, 0.0)
        deltas.append({"QUANTITY": f"BLOCKWORK_{t}", "UNIT": "m2",
                       "FROZEN_M2": round(o, 3), "NEW_M2": round(n, 3), "DELTA_M2": round(n - o, 3),
                       "WHY": "the frozen figure shared each floor's openings across thicknesses in proportion "
                              "to wall length; the new figure deducts every opening from the wall line that "
                              "hosts it, and blocks any line on a floor where a host is unproved",
                       "TRACE": "OPENING_REGISTER -> HOST_COMPONENT_REF -> WALL_LINE -> THICKNESS"})

    merges, old_area_in_spaces = [], 0.0
    for res in results:
        for s in res["SPACES"]:
            old_refs = s["COMPONENT_REFS"]
            old_area_in_spaces += s["AREA_M2"]
            if len(old_refs) < 2:
                continue
            named = [r for r in old_refs if old_rooms.get(r, {}).get("NAME")]
            unnamed = [r for r in old_refs if not old_rooms.get(r, {}).get("NAME")]
            merges.append({"ROOM_ID": s["ROOM_ID"], "FLOOR": s["FLOOR"], "LABEL": s["LABEL"],
                           "COMPONENTS": old_refs, "AREA_M2": s["AREA_M2"],
                           "PREVIOUSLY_NAMED": named, "PREVIOUSLY_UNNAMED": unnamed,
                           "FROZEN_AREAS": {r: old_rooms[r]["AREA_M2"] for r in old_refs if r in old_rooms},
                           "WHY": "these components continue into one another with no wall, no column and no "
                                  "opening between them, so they are one space",
                           "TRACE": "SEAM_REGISTER -> RELATION=CONTINUOUS_FLOOR -> MEMBERSHIP_REGISTER"})

    old_roles = collections.Counter(r["ROLE"] for r in old_rooms.values())
    new_kinds = collections.Counter(m["KIND"] for res in results for m in res["MEMBERSHIP_REGISTER"])
    return {
        "BLOCKWORK_DELTAS": deltas,
        "BLOCKED_WALL_LINES": blocked,
        "SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS": sorted(merges, key=lambda m: -m["AREA_M2"]),
        "COMPONENT_CENSUS": {
            "FROZEN_COMPONENTS": len(old_rooms),
            "FROZEN_ROLE_COUNTS": dict(old_roles),
            "NEW_COMPONENTS": sum(len(res["MEMBERSHIP_REGISTER"]) for res in results),
            "NEW_KIND_COUNTS": dict(new_kinds),
            "NEW_SPACE_COUNT": sum(len(res["SPACES"]) for res in results),
            "NOTE": "the frozen run classified a component as wall material by its width; this run classifies "
                    "it by whether its cells are wall cells, which is evidence rather than a threshold",
        },
        "FLOOR_AREA_IN_SPACES_M2": round(old_area_in_spaces, 3),
        "RULE": "these are differences, not corrections to the frozen artifact, which is unchanged; each one is "
                "accepted or rejected on the drawing evidence in its TRACE and on nothing else",
    }


def finish():
    before = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    ents = G.load()
    results = [run_floor(ents, f) for f in TK.FLOORS]
    frozen = frozen_record()
    comparison = compare(results, frozen)

    all_checks = [c for res in results for c in res["INVARIANTS"]["CHECKS"]]
    lineage = []
    for res in results:
        rerun = run_floor(ents, res["FLOOR"])
        lineage += identity.match_revisions(res["PLAN"]["COMPONENTS"], rerun["PLAN"]["COMPONENTS"], 0.05)

    rec = {
        "ARTIFACT": "ALRASHED_GENERIC_ENGINE_REGRESSION",
        "ENGINE": "engine.qs_core",
        "SOURCE_REVISION": REVISION,
        "DECLARED_SOURCE_PARAMETERS": {
            "TOLERANCE_M": TOLERANCE_M, "SLIVER_MIN_DIMENSION_M": SLIVER_MIN_DIMENSION_M,
            "MAX_OPENING_SPAN_M": MAX_OPENING_SPAN_M, "WALL_HEIGHT_M": WALL_HEIGHT_M,
            "WALL_HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-01)",
            "NOTE": "every one of these is an argument to the engine; none of them lives inside it"},
        "FLOORS": [{"FLOOR": r["FLOOR"], "COMPONENTS": len(r["MEMBERSHIP_REGISTER"]),
                    "SPACES": len(r["SPACES"]), "WALL_LINES": len(r["WALL_LINES"]),
                    "OPENINGS": r["OPENING_REGISTER"]["OPENING_COUNT"],
                    "OPENINGS_HOSTED": r["OPENING_REGISTER"]["ASSIGNED_COUNT"],
                    "OPENINGS_UNRESOLVED": r["OPENING_REGISTER"]["UNRESOLVED_COUNT"],
                    "INVARIANTS": f"{r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}"} for r in results],
        "OPENING_REGISTER": {r["FLOOR"]: r["OPENING_REGISTER"] for r in results},
        "MEMBERSHIP_REGISTER": {r["FLOOR"]: r["MEMBERSHIP_REGISTER"] for r in results},
        "SEAM_REGISTER": {r["FLOOR"]: r["SEAM_REGISTER"] for r in results},
        "SPACES": {r["FLOOR"]: r["SPACES"] for r in results},
        "WALL_LINES": {r["FLOOR"]: r["WALL_ROWS"] for r in results},
        "MEASUREMENT_OBJECTS": {r["FLOOR"]: r["MEASUREMENT_OBJECTS"] for r in results},
        "UNRESOLVED": [dict(q, FLOOR=r["FLOOR"]) for r in results for q in r["UNRESOLVED"]],
        "LINEAGE_ON_AN_IDENTICAL_RERUN": identity.lineage_summary(lineage),
        "INVARIANTS": {"PASSED": sum(1 for c in all_checks if c["PASS"]), "OF": len(all_checks),
                       "ALL_PASS": all(c["PASS"] for c in all_checks),
                       "FAILURES": [c for c in all_checks if not c["PASS"]]},
        "COMPARISON_WITH_THE_FROZEN_ARTIFACT": comparison,
        "FROZEN_UNCHANGED": {"SHA256_BEFORE": before,
                             "SHA256_AFTER": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
                             "REWRITTEN": False},
        "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
    }
    assert rec["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == rec["FROZEN_UNCHANGED"]["SHA256_AFTER"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_GENERIC_ENGINE_REGRESSION.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")

    # the three registers the review asked for, each standing on its own
    _write("OPENING_TO_HOST_REGISTER", {
        "WHAT": "every opening, the wall line that hosts it, the evidence, and what is blocked where no host "
                "is proved",
        "ALLOCATION_RULE": "one host or none; no deduction is ever divided",
        "BY_FLOOR": rec["OPENING_REGISTER"],
        "WALL_LINE_QUANTITIES": rec["WALL_LINES"]})
    _write("COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER", {
        "WHAT": "every geometry component, the room it belongs to or the reason it belongs to none, and the "
                "seam evidence behind each decision",
        "STATES": ["ASSIGNED_TO_SPACE", "NON_ROOM_GEOMETRY", "EXTERNAL_OPEN_AREA", "UNRESOLVED"],
        "BY_FLOOR": rec["MEMBERSHIP_REGISTER"], "SEAMS": rec["SEAM_REGISTER"], "SPACES": rec["SPACES"]})
    _write("ENTITY_LINEAGE_REGISTER", {
        "WHAT": "what happened to every entity between two runs of the engine over the same source",
        "COMPARISON": "this run against an identical rerun of this run",
        "SUMMARY": rec["LINEAGE_ON_AN_IDENTICAL_RERUN"],
        "RECORDS": lineage})
    return rec


def _write(name, payload):
    (OUT / f"ALRASHED_{name}.json").write_text(
        json.dumps({"ARTIFACT": f"ALRASHED_{name}", "SOURCE_REVISION": REVISION,
                    "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    **payload}, indent=1, ensure_ascii=False, default=str), "utf-8")


if __name__ == "__main__":
    r = finish()
    print(f"{r['ARTIFACT']}  invariants {r['INVARIANTS']['PASSED']}/{r['INVARIANTS']['OF']}")
    for f in r["FLOORS"]:
        print(f"  {f['FLOOR']:9s} components {f['COMPONENTS']:3d}  spaces {f['SPACES']:3d}  "
              f"wall lines {f['WALL_LINES']:3d}  openings {f['OPENINGS']:3d} "
              f"(hosted {f['OPENINGS_HOSTED']}, unresolved {f['OPENINGS_UNRESOLVED']})  "
              f"invariants {f['INVARIANTS']}")
    c = r["COMPARISON_WITH_THE_FROZEN_ARTIFACT"]
    print("  blockwork deltas:")
    for d in c["BLOCKWORK_DELTAS"]:
        print(f"    {d['QUANTITY']:16s} frozen {d['FROZEN_M2']:>10}  new {d['NEW_M2']:>10}  "
              f"delta {d['DELTA_M2']:>+9}")
    print(f"  spaces assembled from several components: {len(c['SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS'])}")
    print(f"  unresolved questions: {len(r['UNRESOLVED'])}")
    print(f"  identical rerun lineage: {r['LINEAGE_ON_AN_IDENTICAL_RERUN']}")
    print(f"  frozen unchanged: {not r['FROZEN_UNCHANGED']['REWRITTEN']}")
