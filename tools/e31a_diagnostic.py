"""The first diagnostic E31A run — vector faces, then comparison. In that order.

    python3 -m tools.e31a_diagnostic [--json OUT]

WHAT THIS IS. A diagnostic. Every face it produces is a hypothesis that cannot
release a quantity, and the raster region map is not an input to face
generation — only to the comparison that happens afterwards. Seeding a vector
face from a raster boundary would make this an elaborate way of reproducing the
old segmentation.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from engine.connectivity import (classify_termini, components, cycle_capacity,
                                 end_caps)
from engine.face_eligibility import (FACE_BLOCKED, FACE_ELIGIBLE,
                                     assess_components,
                                     engine_development_status,
                                     project_release_status)
from engine.envelope import classify as classify_envelope
from engine.envelope import summary as envelope_summary
from engine.face_qa import (classify_micro_faces, correspond,
                            false_split_control)
from engine.local_topology import (analyse_space, compare_to_printed,
                                   positive_controls)
from engine.planar import (attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.topology import merge_collinear, wall_pairs
from engine.vector_source import read
from engine.wall_graph import build
from engine.wall_noding import node_and_split
from engine.wall_stitching import candidates

PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"
SPACE_MAP = "data/golden/23010/inputs/space_map_23010_2f.json"

# Spaces the raster already handles correctly. A vector face that SPLITS one of
# these is a false split, and false splits are the cost side of recovery.
# Derived from the space map's own topology overlay, never hand-listed.
STABLE_UNLESS_FLAGGED = True


def raster_regions(space_map: str = SPACE_MAP, pdf: str = PDF) -> dict:
    """Region geometry, for COMPARISON ONLY — never an input to face walking."""
    from engine.geometry import VectorPdfSource, calibrate

    sm = json.loads(Path(space_map).read_text(encoding="utf-8"))
    by_space = {s["region"]: s for s in sm["spaces"]}
    src = VectorPdfSource(pdf, calibrate(887.82, 40000, 554.94, 25000))
    px = float(src.px_mm)
    out = {}
    for r in src.regions(0, min_m2=0.3):
        x0, y0, x1, y1 = r.bbox_mm
        sp = by_space.get(r.id, {})
        out[r.id] = {
            # The vector frame is the unrotated page and the raster is the
            # rendered page; on a 270-degree rotation the axes swap. Written
            # out rather than assumed.
            "bbox_mm": (y0, x0, y1, x1),
            "area_m2": float(r.area_m2),
            "centroid_mm": (r.centroid_px[1] * px, r.centroid_px[0] * px),
            "space_id": sp.get("space_id", ""),
            "room_type": sp.get("room_type", ""),
            "scope": sp.get("scope", ""),
        }
    return out


def run(pdf: str = PDF, *, compare: bool = True) -> dict:
    drawing = read(pdf)
    segs = drawing.axis_aligned()
    merged = merge_collinear([s.as_line() for s in segs], tol_mm=2.0,
                             join_mm=25.0)
    pairs = wall_pairs(merged, Decimal(1))
    graph = build(pairs)
    noded = node_and_split(graph)
    noded.assert_length_preserved()

    caps = end_caps(segs)
    comps = components(noded)
    terms = classify_termini(noded)
    cycles = cycle_capacity(noded)
    stitches = candidates(noded.edges, caps=caps,
                          junction_nodes=[n for n in noded.nodes
                                          if n.degree >= 2])

    regions = raster_regions(pdf=pdf) if compare else {}
    region_points = {r["space_id"]: r["centroid_mm"]
                     for r in regions.values() if r["space_id"]}

    elig = assess_components(
        components=comps, cycles=cycles, termini=terms, stitches=stitches,
        length_drift_mm=noded.health()["length_difference_mm"],
        region_points=region_points)
    dev = engine_development_status(elig)

    # --- walk only the components the local gate admits -------------------
    walkable = {e.component_id for e in elig if e.verdict != FACE_BLOCKED}
    comp_of: dict[str, str] = {}
    for c in comps:
        for eid in c.edge_ids:
            comp_of[eid] = c.component_id
    keep = [e for e in noded.edges if comp_of.get(e.edge_id) in walkable]

    class _Sub:
        edges = keep
        nodes = [n for n in noded.nodes
                 if any(comp_of.get(x) in walkable for x in n.edge_ids)]

    hes = build_half_edges(_Sub)
    res = attach_holes(resolve_unbounded(walk_faces(
        hes, component_of=comp_of,
        edge_status={e.edge_id: e.validation_status for e in noded.edges})))

    micro = classify_micro_faces(res.bounded())
    micro_by_face = {m["face_id"]: m["micro_class"] for m in micro}
    from engine.planar import Face
    res.faces = [Face(**{**f.__dict__,
                         "micro_class": micro_by_face.get(f.face_id, "")})
                 for f in res.faces]

    corr, split = [], {}
    if compare:
        corr = correspond(res.bounded(), regions)
        sm = json.loads(Path(SPACE_MAP).read_text(encoding="utf-8"))
        overlay = {}
        ov = Path("data/golden/23010/topology_overlay.json")
        if ov.exists():
            overlay = json.loads(ov.read_text(encoding="utf-8"))["spaces"]
        stable = tuple(s["space_id"] for s in sm["spaces"]
                       if overlay.get(s["space_id"], {}).get(
                           "physical_topology") == "VALIDATED"
                       and overlay.get(s["space_id"], {}).get(
                           "region_identity") == "VALIDATED")
        split = false_split_control(corr, stable_space_ids=stable)

    # --- the hard cases, and what is actually missing around each -------
    hard = {}
    controls = []
    printed = {}
    if compare:
        by_space = {r["space_id"]: r for r in regions.values()
                    if r.get("space_id")}
        for sid in ("BTH-01", "BTH-02", "BTH-03", "WSH-01", "BED-04"):
            r = by_space.get(sid)
            if r is None:
                hard[sid] = {"space_id": sid, "result": "NO_RASTER_REGION"}
                continue
            hard[sid] = analyse_space(
                sid, r["bbox_mm"], edges=noded.edges, termini=terms,
                caps=caps, stitches=stitches)

        # Positive controls: easy rooms first. If the engine cannot close a
        # plain rectangular bathroom it has nothing to say about a merged one.
        controls = positive_controls(
            res.bounded(), regions,
            ["BTH-05", "BED-01", "STR-01", "OPEN-01"])

        # Printed dimensions used ONLY here, after generation.
        wsh = next((f for f in res.bounded()
                    if by_space.get("WSH-01")
                    and f.bbox_mm[0] <= by_space["WSH-01"]["centroid_mm"][0]
                    <= f.bbox_mm[2]), None)
        printed = {
            "WSH-01": compare_to_printed(
                "WSH-01", candidate_area_m2=wsh.area_m2 if wsh else None,
                candidate_perimeter_m=wsh.perimeter_m if wsh else None,
                printed_w_mm=1500, printed_h_mm=2400),
            "BED-04-bathroom": compare_to_printed(
                "BED-04 bathroom", candidate_area_m2=None,
                candidate_perimeter_m=None,
                printed_w_mm=1600, printed_h_mm=3000),
        }

    # --- building envelope, from the faces just produced ----------------
    unbounded_edges = {e for f in res.faces if f.kind == "UNBOUNDED_FACE"
                       for e in f.source_wall_edge_ids}
    bounded_counts: dict = {}
    for f in res.bounded():
        for e in f.source_wall_edge_ids:
            bounded_counts[e] = bounded_counts.get(e, 0) + 1
    env = classify_envelope(noded.edges, unbounded_edge_ids=unbounded_edges,
                            bounded_edge_counts=bounded_counts)

    gate = {"failed": ["G3-TERMINI", "G5-EXPLAINED-DISCONNECTS",
                       "G8-CYCLES-IN-REAL-ROOMS"], "not_measured": []}
    return {
        "status": {**dev, **project_release_status(gate, elig)},
        "graph": noded.health(),
        "eligibility": {
            "by_verdict": dict(Counter(e.verdict for e in elig)),
            "eligible": [e.record() for e in elig
                         if e.verdict == FACE_ELIGIBLE][:10],
            "hypothesis_only": [e.record() for e in elig
                                if e.verdict == "FACE_HYPOTHESIS_ONLY"][:10],
            "blocked_sample": [e.record() for e in elig
                               if e.verdict == FACE_BLOCKED][:5],
        },
        "faces": res.health(),
        "largest_faces": [f.record() for f in sorted(
            res.bounded(), key=lambda f: -f.area_m2)[:15]],
        "micro_faces": {"classified": len(micro),
                        "by_class": dict(Counter(m["micro_class"]
                                                 for m in micro)),
                        "deleted": 0, "detail": micro[:10]},
        "unclosed_walks": res.unclosed_walks[:5],
        "correspondence": [c.record() for c in corr[:25]],
        "false_split_control": split,
        "hard_cases": hard,
        "positive_controls": controls,
        "printed_dimension_comparison": printed,
        "envelope": {**envelope_summary(env),
                     "sample": [c.record() for c in env[:8]]},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default="")
    ap.add_argument("--no-compare", action="store_true")
    a = ap.parse_args()
    rep = run(compare=not a.no_compare)
    text = json.dumps(rep, indent=2, sort_keys=True, default=str)
    print(text)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n")


if __name__ == "__main__":
    main()
