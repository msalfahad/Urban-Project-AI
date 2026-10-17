"""Where did Method 1b's floor go? A measurement. NOT A METHOD.

Method 1b does not survive: five of the seven selected cases have no cell
at all, because their label anchor falls in the unbounded exterior. Before
anything is concluded about the arrangement REPRESENTATION, this asks the
same question the four-set diagnostic asked of Method 1A, at the layer
below it:

    is the arrangement starved by the partition-capability model, or by
    how much of the drawing the E1.4 ROLE layer classifies at all?

The census is stark on its own: 1049 of 3287 intervals carry no
established semantic role, 931 of them are continuous linework the line
semantics place squarely IN the cut plane, and together they are 479.8 m -
more drawn length than the whole admitted set. The frozen protocol refuses
them, by a rule written before any face existed and for a good reason:
admitting absence of evidence as a separator lets a stray stroke cut a
room in half. That rule is not being revisited.

What this measures is what those refusals COST, so that the failure is
attributed to the right layer.

CLASSIFICATION: DEVELOPMENT_DIAGNOSTIC_ONLY.
This is not Method 1c. Nothing here is promoted into any method, and no
rule of the frozen Method 1b protocol is changed by it.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine import boundary_capability as bcap
from engine import cad_geometry as cg
from engine import interval_role as ir
from engine import line_semantics as ls
from research.arrangement_experiment_01 import method1b as M
from research.arrangement_experiment_01 import method1b_protocol as R
from research.arrangement_experiment_01 import run_method1b as RUN
from tools import run_e1_2 as r12
from tools import run_e1_4 as r14

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01/method1b")


def main() -> int:
    a = RUN.Args()
    st = r14._core(a)
    interp, gf = st["interp"], st["gf"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    semantics = {r["INTERVAL_ID"]: r for r in st["semantics"]["ROWS"]}
    intervals = [iv for rows_ in interp["roles"]["intervals"].values()
                 for iv in rows_]

    frozen = json.loads(
        (OUT / "EDGE_CAPABILITY_REGISTER.json").read_text("utf-8"))["EDGES"]
    report = json.loads((OUT / "TOPOLOGY_REPORT.json").read_text("utf-8"))
    anchors = [(r["IDENTITY_AS_DRAWN"], r["ANCHOR_MM"])
               for r in report["THE_SEVEN_CASES"] if r.get("ANCHOR_MM")]

    extra = []
    for iv in intervals:
        if iv.role != ir.UNKNOWN or iv.length_mm <= 0:
            continue
        status = (semantics.get(iv.interval_id) or {}).get(
            "LINE_SEMANTICS_STATUS")
        if status != ls.VISIBLE_MATERIAL_FACE:
            continue
        parent = by_id.get(iv.parent_object_id)
        if parent is None:
            continue
        brole = bcap.boundary_role_for(iv.role, kind=iv.kind)["BOUNDARY_ROLE"]
        try:
            pts = cg._as_segment(r12.IntervalPrim(parent, iv),
                                 role=brole).points(
                                     tol_mm=R.ARC_TOPOLOGY_TOLERANCE_MM)
        except Exception:
            continue
        pts = [tuple(float(v) for v in p) for p in pts]
        if len(pts) < 2 or M._length(pts) <= 0:
            continue
        extra.append(M.edge_record(
            pts, capability=R.UNRESOLVED, semantic_role=ir.UNKNOWN,
            entity_ids=[iv.parent_object_id],
            interval_ids=[iv.interval_id], ownership=False))
    extra = M._dedupe(extra)

    from shapely.geometry import Point
    rows = {}
    for name, edges in (("FROZEN_METHOD_1B", frozen),
                        ("PLUS_UNCLASSIFIED_IN_CUT_PLANE_LINEWORK",
                         frozen + extra)):
        faces = M.faces_of(edges)
        big = [f for f in faces if f.area > R.SLIVER_AREA_MM2]
        landed = {}
        for ident, pt in anchors:
            p = Point(*pt)
            hit = next((i for i, f in enumerate(faces) if f.contains(p)), None)
            landed[ident] = (None if hit is None
                             else round(faces[hit].area / 1e6, 2))
        rows[name] = {
            "edges": len(edges),
            "faces": len(faces),
            "faces_larger_than_the_sliver_threshold": len(big),
            "enclosed_area_m2": round(sum(f.area for f in faces) / 1e6, 1),
            "anchors_landing_in_a_bounded_face": sum(
                1 for v in landed.values() if v is not None),
            "anchors": landed,
        }
        print(name, json.dumps(rows[name]["anchors"]))

    body = {
        "EXPERIMENT_ID": "ARRANGEMENT_EXPERIMENT_01",
        "CLASSIFICATION": "DEVELOPMENT_DIAGNOSTIC_ONLY",
        "THIS_IS_NOT_A_METHOD": (
            "it is not Method 1c and nothing in it is promoted into any "
            "method. The frozen Method 1b protocol is unchanged"),
        "WHAT_THIS_MEASURES": (
            "whether Method 1b is starved by the partition-capability "
            "model or by how much of the drawing the E1.4 role layer "
            "classifies at all"),
        "THE_ROLE_CENSUS": {
            "intervals": len(intervals),
            "intervals_with_no_established_role": sum(
                1 for iv in intervals if iv.role == ir.UNKNOWN),
            "of_those_in_the_cut_plane": len(extra),
            "their_length_m": round(
                sum(iv.length_mm for iv in intervals
                    if iv.role == ir.UNKNOWN) / 1000.0, 1),
            "GLAZING_INTERVALS_ON_THIS_FLOOR": sum(
                1 for iv in intervals if iv.role == ir.GLAZING),
            "why_that_matters": (
                "the role layer establishes no glazing anywhere on this "
                "floor, so every window band is unclassified linework. A "
                "room whose fourth side is a window has no fourth side in "
                "the arrangement and leaks into the exterior"),
        },
        "why_unknown_is_not_unresolved": R.WHY_UNKNOWN_IS_NOT_UNRESOLVED,
        "THE_REFUSAL_IS_NOT_BEING_REVISITED": (
            "admitting unclassified linework as a separator is how a "
            "stray stroke cuts a room in half, and no downstream pass "
            "could tell that it had. The rule stands. This measures what "
            "it costs, not whether to keep it"),
        "RESULTS": rows,
    }
    p = OUT / "UNKNOWN_ROLE_DIAGNOSTIC.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({k: {x: y for x, y in v.items() if x != "anchors"}
                      for k, v in rows.items()}, indent=2))
    print(json.dumps(body["THE_ROLE_CENSUS"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
