"""The first authoritative full-sheet wall-graph run on the real drawing.

Every earlier graph number came from a synthetic fixture or from an ad-hoc
scratch script. This is the committed version, so the figures it prints can be
re-derived rather than remembered.

WHAT THIS IS NOT. It is a diagnostic, not a quantity. Nothing here releases a
number for a takeoff, and nothing here writes into geometry, semantics or the
benchmark. It reports what the graph looks like and where it is uncertain,
including — deliberately — every separation band, because thickness is evidence
and excluding a band is how a proxy becomes a classification.

Lines are taken in MILLIMETRES from the PDF's own vector geometry and passed to
the topology engine with px_mm = 1, so no raster quantisation sits between the
drawing and the graph.

    python3 -m tools.graph_diagnostic [--pdf PATH] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from decimal import Decimal

from engine.e31a_gate import evaluate
from engine.connectivity import (classify_termini, components,
                                 cycle_capacity, cycles_over_regions,
                                 end_caps, summarise)
from engine.topology import merge_collinear, wall_pairs
from engine.vector_source import read
from engine.wall_graph import build
from engine.wall_noding import (CLUSTER_AMBIGUOUS, CLUSTER_REJECTED,
                                CLUSTER_VALID, node_and_split)
from engine.wall_stitching import candidates
from engine.wall_stitching import summary as stitch_summary

# The audited input, pinned by content hash in data/golden/23010.
DEFAULT_PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"


def length_histogram(lines) -> dict[str, int]:
    def band(mm):
        return ("<50" if mm < 50 else "50-100" if mm < 100 else
                "100-300" if mm < 300 else "300-1000" if mm < 1000 else
                "1000-3000" if mm < 3000 else ">=3000")
    return dict(Counter(band(abs(b - a)) for _, _, a, b in lines))


def region_points(space_map: str = "data/golden/23010/inputs/"
                               "space_map_23010_2f.json",
                  pdf: str = DEFAULT_PDF) -> dict:
    """A point inside each IN_SCOPE mapped region, in the graph's own frame.

    Used only by gate G8, to ask whether a cycle could possibly enclose each
    room the raster found. The centroid is taken from the segmentation, not
    invented, and a region the segmentation did not find contributes nothing.
    """
    import json

    from engine.geometry import VectorPdfSource, calibrate

    sm = json.loads(open(space_map, encoding="utf-8").read())
    src = VectorPdfSource(pdf, calibrate(887.82, 40000, 554.94, 25000))
    px_mm = float(src.px_mm)
    by_region = {r.id: r for r in src.regions(0, min_m2=0.3)}
    out = {}
    for sp in sm["spaces"]:
        if sp.get("scope") != "IN_SCOPE":
            continue
        r = by_region.get(sp.get("region"))
        if r is None:
            continue
        cx, cy = r.centroid_px
        # The vector frame is the unrotated page; the raster is the rendered
        # page. On a 270-degree rotation the axes swap, which is why this is
        # written out rather than assumed.
        out[sp["space_id"]] = (cy * px_mm, cx * px_mm)
    return out


def run(pdf: str = DEFAULT_PDF, *, join_mm: float = 25.0,
        regions: dict | None = None) -> dict:
    """Read, pair, node, then EXPLAIN — in that order.

    The explanation is the point of this round. 115 components and 228 termini
    is not a diagnosis; it is the number that needs one.
    """
    drawing = read(pdf)
    segs = drawing.axis_aligned()
    raw = [s.as_line() for s in segs]
    merged = merge_collinear(raw, tol_mm=2.0, join_mm=join_mm)
    pairs = wall_pairs(merged, Decimal(1))
    graph = build(pairs)
    noded = node_and_split(graph)
    noded.assert_length_preserved()

    caps = end_caps(segs)
    terms = classify_termini(noded)
    comps = components(noded)
    stitches = candidates(noded.edges, caps=caps,
                          junction_nodes=[n for n in noded.nodes
                                          if n.degree >= 2])
    micro = noded.micro_edge_policy()

    report = {
        "input": {"pdf": pdf, "page_rotation": drawing.page_rotation},
        "source": {
            "paths": len(drawing.paths),
            "segments": len(drawing.segments),
            "axis_aligned": len(segs),
            "not_linearised": drawing.skipped,
            "population_bands": drawing.population_bands()[:12],
            "angle_bands": drawing.angle_bands(),
            "path_fragmentation": drawing.path_fragmentation(),
        },
        "end_caps": {
            "found": len(caps),
            "separation_bands_mm": dict(Counter(
                ("<60" if c.separation_mm < 60 else
                 "60-120" if c.separation_mm < 120 else
                 "120-180" if c.separation_mm < 180 else
                 "180-260" if c.separation_mm < 260 else "260-400")
                for c in caps)),
            "pen_weights": dict(Counter(c.stroke_width_pt for c in caps)),
        },
        "extraction": {
            "after_collinear_merge": len(merged),
            "collinear_join_mm": join_mm,
            "raw_length_bands_mm": length_histogram(raw),
            "merged_length_bands_mm": length_histogram(merged),
        },
        "pairing": {
            "wall_pairs": len(pairs),
            "separation_bands_mm": graph.separation_bands(),
        },
        "pre_split_graph": graph.counts(),
        "noded_graph": noded.health(),
        "connectivity": summarise(comps, terms),
        "components": [c.record() for c in comps[:20]],
        "termini_sample": [t.record() for t in terms[:20]],
        "stitching": stitch_summary(stitches),
        "clusters": {
            "valid": sum(1 for n in noded.nodes if n.status == CLUSTER_VALID),
            "ambiguous": sum(1 for n in noded.nodes
                             if n.status == CLUSTER_AMBIGUOUS),
            "rejected": sum(1 for n in noded.nodes
                            if n.status == CLUSTER_REJECTED),
            "subdivided": sum(1 for n in noded.nodes if n.subdivision_depth > 0),
            "merged_by_incidence": len(noded.node_merges),
        },
        "micro_edges": {
            "flagged": len(micro),
            "by_decision": dict(Counter(m["decision"] for m in micro)),
            "deleted": 0,
        },
    }
    # Scored last, on the report just built, so the gate can never be graded
    # against anything but the numbers this run actually produced.
    report["cycle_capacity"] = cycle_capacity(noded)[:10]
    if regions:
        report["cycles_over_regions"] = cycles_over_regions(noded, regions)
    report["e31a_gate"] = evaluate(report)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", default=DEFAULT_PDF)
    ap.add_argument("--json", default="")
    ap.add_argument("--join-mm", type=float, default=25.0)
    ap.add_argument("--no-regions", action="store_true",
                    help="skip the slow raster pass that gate G8 needs")
    a = ap.parse_args()
    rep = run(a.pdf, join_mm=a.join_mm,
              regions=None if a.no_regions else region_points(pdf=a.pdf))
    text = json.dumps(rep, indent=2, sort_keys=True)
    print(text)
    if a.json:
        with open(a.json, "w") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
