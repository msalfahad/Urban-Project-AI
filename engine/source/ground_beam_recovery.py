"""GROUND_BEAM_OCCURRENCE_RECOVERY (generic).

A ground beam that exists physically is never dropped because one dimension is missing. Each span keeps its
measured length (straight, curved / arc-following, exterior or unlabelled), its width and its source handles; the
depth comes from the GROUND_BEAM_DEPTH evidence ladder (local dimension -> schedule -> detail -> same mark ->
paired faces / section geometry -> project typical -> bounded candidate -> unknown). The volume is a scenario part
whose state follows the depth authority:

    depth SOURCE_FACT / DERIVED + VERIFIED   -> VERIFIED part,    terminal MEASURED_COMPLETE
    depth PROVISIONAL single value           -> PROVISIONAL part, terminal CANDIDATE_QUANTIFIED
    depth PROVISIONAL range                  -> PROVISIONAL part, terminal BOUNDED_QUANTIFIED
    depth unknown                            -> UNQUANTIFIED part, terminal UNQUANTIFIED (length / width kept)

Region membership uses true segment / region intersection (a beam crossing a sheet / region boundary is kept),
never the start point. Stdlib only.
"""

from __future__ import annotations

import math

from engine.source import cad_guards as CG
from engine.source import evidence_ladder as EL
from engine.source import population_conservation as PC
from engine.source import quantity_scenarios as QS


def span_length_m(geometry):
    """geometry: {'kind': 'LINE', 'p0': (x, y), 'p1': (x, y)} or {'kind': 'ARC', 'radius': r, 'sweep_deg': a}
    or {'kind': 'POLYLINE', 'points': [...]} - lengths in metres."""
    k = geometry["kind"]
    if k == "LINE":
        (x0, y0), (x1, y1) = geometry["p0"], geometry["p1"]
        return math.hypot(x1 - x0, y1 - y0)
    if k == "ARC":
        return abs(geometry["radius"] * math.radians(geometry["sweep_deg"]))
    if k == "POLYLINE":
        pts = geometry["points"]
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    raise ValueError(f"unknown span geometry {k}")


def spans_in_region(spans, region):
    """Spans whose centreline touches the region (true intersection); a LINE crossing the boundary is kept."""
    out = []
    for s in spans:
        g = s["geometry"]
        if g["kind"] == "LINE":
            hit = CG.segment_intersects_region((tuple(g["p0"]), tuple(g["p1"])), region)
        elif g["kind"] == "POLYLINE":
            pts = g["points"]
            hit = any(CG.segment_intersects_region((tuple(a), tuple(b)), region) for a, b in zip(pts, pts[1:]))
        else:
            hit = True                                       # arcs are bound by their owning band, not by a point
        if hit:
            out.append(s)
    return out


def recover_span(span, depth):
    """span: {span_id, geometry | length_m, B_m, kind, source_handles}; depth: an evidence_ladder.resolve result."""
    L = span.get("length_m")
    if L is None:
        L = span_length_m(span["geometry"])
    B = span["B_m"]
    occ = {"occurrence_id": span["span_id"], "source_handles": span.get("source_handles", []),
           "position": span.get("position"), "count": 1,
           "known_geometry": {"length_m": L, "B_m": B, "kind": span.get("kind"),
                              "curved": span.get("geometry", {}).get("kind") == "ARC"},
           "candidate_definitions": span.get("candidate_definitions", [])}
    if not depth["resolved"]:
        part = QS.part(span["span_id"], "UNQUANTIFIED", why="depth unknown")
        return {"span": span["span_id"], "length_m": L, "B_m": B, "depth": depth, "part": part,
                "terminal": PC.terminal(occ, "UNQUANTIFIED", unresolved=["DEPTH"], why="depth unknown")}
    v, lo, hi = L * B * depth["value"], L * B * depth["low"], L * B * depth["high"]
    if depth["authority"] == "VERIFIED":
        part = QS.part(span["span_id"], "VERIFIED", v, origin=depth["fact_origin"])
        state = "MEASURED_COMPLETE"
    else:
        part = QS.part(span["span_id"], "PROVISIONAL", v, min(lo, v), max(hi, v), origin=depth["fact_origin"],
                       why=f"depth from {depth['level']}")
        state = "BOUNDED_QUANTIFIED" if depth["low"] != depth["high"] else "CANDIDATE_QUANTIFIED"
    unresolved = [] if state == "MEASURED_COMPLETE" else ["DEPTH_AUTHORITY"]
    return {"span": span["span_id"], "length_m": L, "B_m": B, "depth": depth, "part": part,
            "terminal": PC.terminal(occ, state, quantity=v, unresolved=unresolved, why=f"depth: {depth['level']}")}


def recover(spans, depth_resolvers):
    """depth_resolvers(span) -> {level_id: callable}; returns per-span records, the scenario roll-up and the
    conservation check (every admitted span terminates)."""
    recs = [recover_span(s, EL.resolve("GROUND_BEAM_DEPTH", depth_resolvers(s), s)) for s in spans]
    occs = [{"occurrence_id": s["span_id"]} for s in spans]
    cons = PC.require_conserved(occs, [r["terminal"] for r in recs])
    return {"spans": recs, "volume": QS.combine([r["part"] for r in recs], unit="m3"), "conservation": cons,
            "length_m": sum(r["length_m"] for r in recs)}
