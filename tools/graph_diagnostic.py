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

from engine.topology import merge_collinear, wall_pairs
from engine.wall_graph import build
from engine.wall_noding import (CLUSTER_AMBIGUOUS, CLUSTER_REJECTED,
                                CLUSTER_VALID, node_and_split)

# The audited input, pinned by content hash in data/golden/23010.
DEFAULT_PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"

# The sheet's own scale. A plotted 1:100 sheet at 72 pt/inch.
MM_PER_PT = 45.0542

# A segment is axis-aligned when its off-axis extent is below this. Plotted CAD
# output is exact; this catches float noise, not slanted walls.
AXIS_TOL_PT = 0.05


def axis_lines(path: str, page: int = 0, *, mm_per_pt: float = MM_PER_PT):
    """Axis-aligned vector segments, in millimetres, with nothing inferred.

    Rectangles are expanded into their four sides: a wall face drawn as a thin
    filled rectangle is two faces and two ends, and dropping it would lose a
    wall the architect drew.
    """
    import pymupdf

    doc = pymupdf.open(path)
    pg = doc[page]
    out: list[tuple[str, float, float, float]] = []
    skipped = Counter()

    def add(x0, y0, x1, y1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        if dy <= AXIS_TOL_PT and dx > AXIS_TOL_PT:
            out.append(("H", y0 * mm_per_pt,
                        min(x0, x1) * mm_per_pt, max(x0, x1) * mm_per_pt))
        elif dx <= AXIS_TOL_PT and dy > AXIS_TOL_PT:
            out.append(("V", x0 * mm_per_pt,
                        min(y0, y1) * mm_per_pt, max(y0, y1) * mm_per_pt))
        elif dx <= AXIS_TOL_PT and dy <= AXIS_TOL_PT:
            skipped["degenerate_point"] += 1
        else:
            skipped["not_axis_aligned"] += 1

    for d in pg.get_drawings():
        for item in d["items"]:
            kind = item[0]
            if kind == "l":
                (x0, y0), (x1, y1) = item[1], item[2]
                add(x0, y0, x1, y1)
            elif kind == "re":
                r = item[1]
                add(r.x0, r.y0, r.x1, r.y0)
                add(r.x0, r.y1, r.x1, r.y1)
                add(r.x0, r.y0, r.x0, r.y1)
                add(r.x1, r.y0, r.x1, r.y1)
            elif kind == "qu":
                skipped["quad"] += 1
            else:
                skipped[f"curve_{kind}"] += 1
    return out, dict(skipped)


def length_histogram(lines) -> dict[str, int]:
    def band(mm):
        return ("<50" if mm < 50 else "50-100" if mm < 100 else
                "100-300" if mm < 300 else "300-1000" if mm < 1000 else
                "1000-3000" if mm < 3000 else ">=3000")
    return dict(Counter(band(abs(b - a)) for _, _, a, b in lines))


def run(pdf: str = DEFAULT_PDF, *, join_mm: float = 25.0) -> dict:
    raw, skipped = axis_lines(pdf)
    merged = merge_collinear(raw, tol_mm=2.0, join_mm=join_mm)
    pairs = wall_pairs(merged, Decimal(1))
    graph = build(pairs)
    noded = node_and_split(graph)
    noded.assert_length_preserved()

    micro = noded.micro_edge_policy()
    return {
        "input": {"pdf": pdf, "mm_per_pt": MM_PER_PT},
        "extraction": {
            "axis_aligned_segments": len(raw),
            "skipped": skipped,
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
        "clusters": {
            "valid": sum(1 for n in noded.nodes if n.status == CLUSTER_VALID),
            "ambiguous": sum(1 for n in noded.nodes
                             if n.status == CLUSTER_AMBIGUOUS),
            "rejected": sum(1 for n in noded.nodes
                            if n.status == CLUSTER_REJECTED),
            "subdivided": sum(1 for n in noded.nodes if n.subdivision_depth > 0),
            "max_subdivision_depth": max(
                (n.subdivision_depth for n in noded.nodes), default=0),
            "merged_by_incidence": len(noded.node_merges),
        },
        "micro_edges": {
            "flagged": len(micro),
            "by_decision": dict(Counter(m["decision"] for m in micro)),
            "deleted": 0,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", default=DEFAULT_PDF)
    ap.add_argument("--json", default="")
    ap.add_argument("--join-mm", type=float, default=25.0)
    a = ap.parse_args()
    rep = run(a.pdf, join_mm=a.join_mm)
    text = json.dumps(rep, indent=2, sort_keys=True)
    print(text)
    if a.json:
        with open(a.json, "w") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
