"""GROUND_SLAB_REGION_RECOVERY (generic).

The ground slab is recovered as physical cells, not only where a thickness label happens to sit:

    founded footprint (outer outline of the connected ground-beam system)
      - ground-beam bands - columns - single structural barrier lines
      = cells

Every cell is a physical region and gets a terminal record:

    LABELLED_OFFICIAL      thickness printed inside the cell, or the cell belongs to an already released zone
    UNLABELLED_CANDIDATE   no thickness inside; thickness from the SLAB_THICKNESS ladder (same-sheet typical label
                           / project rule / fallback) -> PROVISIONAL_ONLY, low scenario 0 (it may not be slab)
    EXCLUDED_SLIVER        narrower than the minimum effective width (2 x area / perimeter) - recorded, not slab
    EXCLUDED_NON_SLAB      the caller marked it a void / pool / shaft (reason kept)

decompose() uses shapely (lazy import); classify() / quantities() are stdlib. No area target is used.
"""

from __future__ import annotations

from engine.source import evidence_ladder as EL
from engine.source import quantity_scenarios as QS

LABELLED_OFFICIAL, UNLABELLED_CANDIDATE, EXCLUDED_SLIVER, EXCLUDED_NON_SLAB = (
    "LABELLED_OFFICIAL", "UNLABELLED_CANDIDATE", "EXCLUDED_SLIVER", "EXCLUDED_NON_SLAB")
DEFAULT_MIN_EFF_WIDTH_MM = 450.0


def decompose(barriers, *, min_footprint_m2=20.0, labels=(), units_per_m=1000.0):
    """barriers: shapely polygons (bands, columns, buffered single lines). labels: [(x, y, text)].
    Returns cells [{cell_id, footprint_id, area_m2, eff_width_mm, labels, wkt}]."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    u2 = units_per_m * units_per_m
    union = unary_union(list(barriers))
    comps = sorted([Polygon(c.exterior) for c in getattr(union, "geoms", [union])], key=lambda p: -p.area)
    fps = [c for c in comps if c.area >= min_footprint_m2 * u2]
    cells = []
    for fi, fp in enumerate(fps, 1):
        rest = fp.difference(union)
        pcs = sorted([q for q in getattr(rest, "geoms", [rest]) if not q.is_empty and q.area > 0],
                     key=lambda q: (round(q.centroid.x), round(q.centroid.y)))
        for q in pcs:
            c = q.centroid
            cells.append({"cell_id": f"FP{fi}-C{round(c.x)}_{round(c.y)}", "footprint_id": f"FP-{fi}",
                          "footprint_area_m2": fp.area / u2, "area_m2": q.area / u2,
                          "eff_width_mm": 2.0 * q.area / q.length * (1000.0 / units_per_m) if q.length else 0.0,
                          "labels": [t for (x, y, t) in labels if q.contains(Point(x, y))],
                          "wkt": q.wkt})
    return cells


def classify(cells, *, is_thickness_label, official_cell_ids=(), non_slab=None,
             min_eff_width_mm=DEFAULT_MIN_EFF_WIDTH_MM):
    """non_slab: {cell_id: reason}. Returns cells with a `role` and `why`."""
    non_slab = non_slab or {}
    out = []
    for c in cells:
        r = dict(c)
        if c["cell_id"] in non_slab:
            r["role"], r["why"] = EXCLUDED_NON_SLAB, non_slab[c["cell_id"]]
        elif c["eff_width_mm"] < min_eff_width_mm:
            r["role"], r["why"] = EXCLUDED_SLIVER, f"effective width {c['eff_width_mm']:.0f} < {min_eff_width_mm:.0f} mm"
        elif c["cell_id"] in official_cell_ids or any(is_thickness_label(t) for t in c.get("labels", [])):
            r["role"], r["why"] = LABELLED_OFFICIAL, "thickness printed in the cell / released zone"
        else:
            r["role"], r["why"] = UNLABELLED_CANDIDATE, "no thickness label inside the cell"
        out.append(r)
    return out


def quantities(classified, thickness, *, labelled_t_m=None):
    """thickness: an evidence_ladder.resolve result (SLAB_THICKNESS) for the unlabelled cells; labelled cells use
    the printed `labelled_t_m` (default: the resolved value). Returns area / volume scenarios + exclusions."""
    if not thickness["resolved"]:
        raise EL.LadderError("ground slab thickness unresolved - candidate cells stay UNQUANTIFIED")
    t, tlo, thi = thickness["value"], thickness["low"], thickness["high"]
    tl = t if labelled_t_m is None else labelled_t_m
    a_parts, v_parts = [], []
    for c in classified:
        if c["role"] == LABELLED_OFFICIAL:
            a_parts.append(QS.part(c["cell_id"], "VERIFIED", c["area_m2"], origin="SOURCE_FACT"))
            v_parts.append(QS.part(c["cell_id"], "VERIFIED", c["area_m2"] * tl, origin="SOURCE_FACT"))
        elif c["role"] == UNLABELLED_CANDIDATE:
            a_parts.append(QS.part(c["cell_id"], "CANDIDATE", c["area_m2"], 0.0, c["area_m2"], origin="CANDIDATE",
                                   why=c["why"]))
            v_parts.append(QS.part(c["cell_id"], "CANDIDATE", c["area_m2"] * t, 0.0, c["area_m2"] * thi,
                                   origin=thickness["fact_origin"], why=f"thickness from {thickness['level']}"))
    return {"area": QS.combine(a_parts, unit="m2"), "volume": QS.combine(v_parts, unit="m3"),
            "excluded": [{"cell_id": c["cell_id"], "role": c["role"], "area_m2": c["area_m2"], "why": c["why"]}
                         for c in classified if c["role"] in (EXCLUDED_SLIVER, EXCLUDED_NON_SLAB)],
            "thickness": {k: thickness[k] for k in ("level", "value", "low", "high", "fact_origin", "authority")},
            "tlo_m": tlo}
