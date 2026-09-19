"""Adapter: frozen A21 trace register  ->  measurement-region builder input.

Deterministic. Reads traces, writes nothing back. Every edge it produces
names the trace it came from and the dimension trace that supports its
length, so the drill-down PROJECT -> ROOM -> SEGMENT -> DIMENSION -> SOURCE
is preserved through the arrow.

What it will NOT do:
  * invent a wall to close a ring. If the traced boundary does not meet
    itself, the region builder says so and that is the answer.
  * convert an OPEN_EDGE into a closable site unless the reader traced it
    as a genuine passage with two established terminations. An open edge
    the reader could not bound stays an open edge.
  * take a length from anywhere but a SUPPORTED_BY dimension trace with
    an ESTABLISHED dimension status, or the trace's own LENGTH_M when the
    reader marked its DIMENSION_STATUS ESTABLISHED.

Endpoint matching is in processed-sheet pixels with a tolerance; the
tolerance is recorded in the output, and a match made under tolerance is
labelled SNAPPED so a reviewer can see it.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine import qs_measurement_region as M

REG = Path("data/experiments/A21_TRACE_SUFFICIENCY_01/TRACE_REGISTER.json")

PLAN_SHEETS = ("GROUND_FLOOR_PLAN", "FIRST_FLOOR_PLAN", "SECOND_FLOOR_ROOF_PLAN")

EDGE_KIND = {
    "WALL_SEGMENT": "PHYSICAL_WALL_FACE",
    "COLUMN": "EXPOSED_COLUMN_FACE",
    "GLAZING": "GLAZING_BOUNDARY",
    "PARAPET": "PHYSICAL_WALL_FACE",
    "OPEN_EDGE": "OPEN_PHYSICAL_EDGE",
    "UNRESOLVED_FEATURE": "UNRESOLVED_EDGE",
}
OPENING_TYPES = ("DOOR", "WINDOW", "GLAZING")
SNAP_PX = 12.0


def _ends(t: dict):
    """First and last point of the trace's plan geometry, or None."""
    if t.get("PIXEL_POLYLINE"):
        pl = t["PIXEL_POLYLINE"]
        return tuple(pl[0]), tuple(pl[-1])
    if t.get("PIXEL_BBOX"):
        x0, y0, x1, y1 = t["PIXEL_BBOX"]
        # a bbox edge: use its long axis as the face
        if (x1 - x0) >= (y1 - y0):
            return (x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)
        return ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)
    return None


def _snap(points: list, tol: float) -> dict:
    """Cluster endpoints within tol; return point -> canonical point."""
    canon = {}
    reps = []
    for p in points:
        for r in reps:
            if math.dist(p, r) <= tol:
                canon[p] = r
                break
        else:
            reps.append(p)
            canon[p] = p
    return canon


def _length_from(t: dict, by_id: dict):
    """(length_m, source, supporting_dimension_ids) or (None, None, [])."""
    sup = t.get("SUPPORTED_BY")
    sup = [sup] if isinstance(sup, str) else (sup or [])
    dims = [by_id[s] for s in sup if s in by_id
            and by_id[s]["EFFECTIVE_CLAIM_TYPE"] in ("PRINTED_DIMENSION",
                                                     "HEIGHT_DIMENSION")]
    if t.get("DIMENSION_STATUS") == "ESTABLISHED" and isinstance(
            t.get("LENGTH_M"), (int, float)):
        return t["LENGTH_M"], "DRAWING_PRINTED_DIMENSION", [d["TRACE_ID"] for d in dims]
    return None, None, [d["TRACE_ID"] for d in dims]


def build_inputs(case_id: str, *, plan_sheet: str, tol_px: float = SNAP_PX) -> dict:
    reg = json.loads(REG.read_text("utf-8"))
    traces = [t for t in reg["TRACES"] if t["CASE_ID"] == case_id]
    by_id = {t["TRACE_ID"]: t for t in traces}

    boundary = [t for t in traces
                if t["SHEET_ID"] == plan_sheet
                and t["EFFECTIVE_CLAIM_TYPE"] in EDGE_KIND
                and t["TRACE_LOCATABILITY_STATUS"] == "LOCATABLE"
                and _ends(t) is not None]
    # openings hosted in a wall are not boundary edges themselves
    hosted = {t["TRACE_ID"] for t in traces if t.get("HOSTED_IN")}
    boundary = [t for t in boundary if t["TRACE_ID"] not in hosted
                and t["EFFECTIVE_CLAIM_TYPE"] != "GLAZING" or
                (t["EFFECTIVE_CLAIM_TYPE"] == "GLAZING" and not t.get("HOSTED_IN"))]

    pts = []
    for t in boundary:
        a, b = _ends(t)
        pts += [a, b]
    canon = _snap(pts, tol_px)

    edges, snapped = [], []
    for t in boundary:
        a, b = _ends(t)
        ca, cb = canon[a], canon[b]
        if ca != a or cb != b:
            snapped.append({"TRACE_ID": t["TRACE_ID"],
                            "FROM": [list(a), list(b)],
                            "TO": [list(ca), list(cb)]})
        L, src, dims = _length_from(t, by_id)
        edges.append({
            "EDGE_ID": t["TRACE_ID"],
            "KIND": EDGE_KIND[t["EFFECTIVE_CLAIM_TYPE"]],
            "a": [round(ca[0], 1), round(ca[1], 1)],
            "b": [round(cb[0], 1), round(cb[1], 1)],
            "length_m": L,
            "length_source": src,
            "supporting_dimensions": dims,
            "trace_ids": [t["TRACE_ID"]],
            "VISUAL_TRACE_STATUS": t["VISUAL_TRACE_STATUS"],
            "GEOMETRY_STATUS": t["GEOMETRY_STATUS"],
            "DIMENSION_STATUS": t["DIMENSION_STATUS"],
        })

    # sites: only where the reader traced a bounded passage. An OPEN_EDGE
    # becomes a CONFIRMED_OPEN_PASSAGE site only if both its ends land on
    # other boundary endpoints - i.e. the void has two wall terminations.
    degree = {}
    for e in edges:
        for p in (tuple(e["a"]), tuple(e["b"])):
            degree[p] = degree.get(p, 0) + 1
    sites = []
    for e in list(edges):
        if e["KIND"] != "OPEN_PHYSICAL_EDGE":
            continue
        if degree.get(tuple(e["a"]), 0) >= 2 and degree.get(tuple(e["b"]), 0) >= 2:
            sites.append({"SITE_ID": e["EDGE_ID"],
                          "SITE_TYPE": "CONFIRMED_OPEN_PASSAGE",
                          "termination_a": e["a"], "termination_b": e["b"],
                          "span_m": e["length_m"],
                          "evidence": ["traced open edge with two wall "
                                       "terminations"],
                          "trace_ids": e["trace_ids"]})
            edges.remove(e)
    openings = []
    for t in traces:
        if t["EFFECTIVE_CLAIM_TYPE"] in OPENING_TYPES and t.get("HOSTED_IN"):
            L, src, dims = _length_from(t, by_id)
            openings.append({
                "OPENING_ID": t["TRACE_ID"], "TYPE": t["EFFECTIVE_CLAIM_TYPE"],
                "HOSTED_IN": t["HOSTED_IN"],
                "width_m": L, "width_source": src,
                "height_m": None, "height_source": None,
                "trace_ids": [t["TRACE_ID"]] + dims,
                "DIMENSION_STATUS": t["DIMENSION_STATUS"],
            })
    return {"CASE_ID": case_id, "PLAN_SHEET": plan_sheet, "SNAP_TOLERANCE_PX": tol_px,
            "physical_edges": edges, "sites": sites, "openings": openings,
            "SNAPPED_ENDPOINTS": snapped,
            "BOUNDARY_TRACES_CONSIDERED": [t["TRACE_ID"] for t in boundary]}


def run_case(case_id: str, *, plan_sheet: str, trade: str, basis: str) -> dict:
    inp = build_inputs(case_id, plan_sheet=plan_sheet)
    region = M.build_region(region_id=case_id, physical_edges=inp["physical_edges"],
                            sites=inp["sites"], openings=inp["openings"],
                            trade=trade, basis=basis)
    region["ADAPTER"] = {k: inp[k] for k in ("PLAN_SHEET", "SNAP_TOLERANCE_PX",
                                             "SNAPPED_ENDPOINTS",
                                             "BOUNDARY_TRACES_CONSIDERED")}
    return region
