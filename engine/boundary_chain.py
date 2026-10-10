"""E1.3 §11, §12 — an open room still has boundaries.

E1.2 did the safe thing with a region it could not close: it refused to
invent a polygon. Then it stored, in effect, nothing. A pantry with a
drawn wall on three sides and an opening onto the dining area came out as
"no boundary built", and three established walls were thrown away with
the one that does not exist.

An open physical region has a PHYSICAL_BOUNDARY_CHAIN: the pieces the
drawing does establish, in order, connected where they connect, with the
places where no material exists recorded as what they are. It is not a
polygon and it must never be closed into one. It is a complete, honest
statement of the boundary evidence, which is what E1 owes the stages
after it.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "AN_OPEN_REGION_HAS_AN_ORDERED_BOUNDARY_CHAIN_V1"

# ---------------------------------------------------------- element kinds
MATERIAL_WALL_FACE = "MATERIAL_WALL_FACE"
EXPOSED_COLUMN_FACE = "EXPOSED_COLUMN_FACE"
GLAZING_BOUNDARY = "GLAZING_BOUNDARY"
CURVED_MATERIAL_FACE = "CURVED_MATERIAL_FACE"
DOOR_PORTAL = "DOOR_PORTAL"
MATERIAL_CONTINUITY_SPAN = "MATERIAL_CONTINUITY_SPAN"
OPEN_EDGE = "OPEN_EDGE"
UNRESOLVED_EDGE = "UNRESOLVED_EDGE"

CHAIN_ELEMENTS = (MATERIAL_WALL_FACE, EXPOSED_COLUMN_FACE, GLAZING_BOUNDARY,
                  CURVED_MATERIAL_FACE, DOOR_PORTAL, MATERIAL_CONTINUITY_SPAN,
                  OPEN_EDGE, UNRESOLVED_EDGE)

# Elements along which something was built. Only these contribute wall
# material length, and the register computes that from the kind rather
# than trusting whoever assembled the chain.
MATERIAL_ELEMENTS = (MATERIAL_WALL_FACE, EXPOSED_COLUMN_FACE,
                     GLAZING_BOUNDARY, CURVED_MATERIAL_FACE)

# Elements that exist in the topology and carry no material of their own.
# A portal is a hole in a wall and a continuity span is where a junction
# or a cross wall carries the boundary through: in both cases the region
# is still bounded there, by something that is not this span.
TOPOLOGY_ONLY_ELEMENTS = (DOOR_PORTAL, MATERIAL_CONTINUITY_SPAN, OPEN_EDGE,
                          UNRESOLVED_EDGE)

# An element across which the region is NOT bounded by anything built.
# These, and only these, make a region open.
NO_MATERIAL_EXISTS_HERE = (OPEN_EDGE, UNRESOLVED_EDGE)

# ------------------------------------------------------------------ prose
AN_OPEN_EDGE_IS_A_RESULT = (
    "an open edge is the drawing saying that nothing was built along this "
    "stretch. It belongs in the boundary record with zero material, and "
    "closing it to obtain a polygon would replace a fact with a number "
    "nobody drew")

A_CHAIN_IS_NOT_A_POLYGON = (
    "a chain states the boundary evidence in order. It closes only when "
    "the drawn material closes it. Nothing here joins the two loose ends "
    "of an open chain, however small the remaining distance looks")

ORDER_AND_CONNECTIVITY_ARE_THE_POINT = (
    "which faces run into which, and where the runs stop, is what makes "
    "this a boundary rather than a bag of lines. A later stage can walk it "
    "and see exactly where the room stops being enclosed")


def model_hash() -> str:
    parts = [MODEL] + list(CHAIN_ELEMENTS) + list(MATERIAL_ELEMENTS)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _k(pt, snap):
    return (round(pt[0] / snap), round(pt[1] / snap))


def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def order_into_runs(elements, *, snap_mm=1.0):
    """Walk the material elements into maximal connected runs.

    Each element is a dict with start_mm, end_mm and kind. Elements are
    joined where an endpoint meets an endpoint within snap_mm. An element
    may be traversed in either direction; the run records the direction it
    was walked so the chain reads continuously.
    """
    ends = {}
    for i, e in enumerate(elements):
        for pt in (e["start_mm"], e["end_mm"]):
            ends.setdefault(_k(pt, snap_mm), []).append(i)

    used, runs = set(), []
    for i0 in range(len(elements)):
        if i0 in used:
            continue
        used.add(i0)
        e0 = elements[i0]
        run = [dict(e0, reversed=False)]
        head, tail = e0["start_mm"], e0["end_mm"]

        def extend(at, append):
            nonlocal head, tail
            moved = True
            while moved:
                moved = False
                for j in ends.get(_k(at, snap_mm), ()):
                    if j in used:
                        continue
                    ej = elements[j]
                    # Walking forward off the tail, the next element must
                    # START where we are. Walking backward off the head, it
                    # must END where we are - so the same endpoint match
                    # implies the opposite traversal direction.
                    if _k(ej["start_mm"], snap_mm) == _k(at, snap_mm):
                        nxt, rev = ej["end_mm"], not append
                    elif _k(ej["end_mm"], snap_mm) == _k(at, snap_mm):
                        nxt, rev = ej["start_mm"], append
                    else:
                        continue
                    used.add(j)
                    row = dict(ej, reversed=rev)
                    if append:
                        run.append(row)
                        tail = nxt
                    else:
                        run.insert(0, row)
                        head = nxt
                    at, moved = nxt, True
                    break
            return at

        tail = extend(tail, True)
        head = extend(head, False)
        runs.append({"elements": run, "start_mm": list(head),
                     "end_mm": list(tail),
                     "closed": _k(head, snap_mm) == _k(tail, snap_mm)
                     and len(run) > 2})
    return runs


A_CURVE_IS_NOT_ITS_CHORD = (
    "an element drawn as an arc or a polyline has more than two points, "
    "and the straight line between its ends is not it. Where an element "
    "carries points_mm, the chain keeps every point and its length is the "
    "length along those points. A chord would both draw the wrong line "
    "and measure short")


def _poly_len(points) -> float:
    return sum(_len(points[i], points[i + 1])
               for i in range(len(points) - 1))


def build(elements, *, connectors=None, snap_mm=1.0) -> dict:
    """Assemble an ordered PHYSICAL_BOUNDARY_CHAIN.

    `elements` are the established boundary pieces. `connectors` are the
    already-classified pieces that stand between runs - a DOOR_PORTAL, an
    OPEN_EDGE or an UNRESOLVED_EDGE - supplied by the caller because what
    a gap is, is a question this module does not answer.
    """
    bad = sorted({e.get("kind") for e in elements
                  if e.get("kind") not in CHAIN_ELEMENTS})
    if bad:
        raise ValueError(f"not a chain element kind: {bad}")

    runs = order_into_runs(list(elements), snap_mm=snap_mm)
    ordered, idx = [], 0
    for n, run in enumerate(runs):
        for e in run["elements"]:
            a = e["end_mm"] if e.get("reversed") else e["start_mm"]
            b = e["start_mm"] if e.get("reversed") else e["end_mm"]
            pts = list(e.get("points_mm") or ())
            if len(pts) >= 2 and e.get("reversed"):
                pts = list(reversed(pts))
            span = _poly_len(pts) if len(pts) >= 2 else _len(a, b)
            idx += 1
            row = {
                "SEQ": idx,
                "CHAIN_ELEMENT": e["kind"],
                "run_index": n,
                "start_mm": [round(a[0], 3), round(a[1], 3)],
                "end_mm": [round(b[0], 3), round(b[1], 3)],
                "length_mm": round(span, 3),
                "material_present": e["kind"] in MATERIAL_ELEMENTS,
                "wall_length_contribution_mm": (
                    round(span, 3) if e["kind"] in MATERIAL_ELEMENTS
                    else 0.0),
                **{k: v for k, v in e.items()
                   if k not in ("kind", "start_mm", "end_mm", "reversed",
                                "points_mm")},
            }
            if len(pts) >= 3:
                row["points_mm"] = [[round(q[0], 3), round(q[1], 3)]
                                    for q in pts]
                row["a_curve_is_not_its_chord"] = A_CURVE_IS_NOT_ITS_CHORD
                row["chord_length_mm"] = round(_len(a, b), 3)
            ordered.append(row)
    for c in connectors or ():
        if c.get("kind") not in TOPOLOGY_ONLY_ELEMENTS:
            raise ValueError(
                "a connector between runs carries no material and must be "
                f"one of {TOPOLOGY_ONLY_ELEMENTS}, not {c.get('kind')!r}")
        a, b = c["start_mm"], c["end_mm"]
        idx += 1
        ordered.append({
            "SEQ": idx,
            "CHAIN_ELEMENT": c["kind"],
            "run_index": None,
            "start_mm": [round(a[0], 3), round(a[1], 3)],
            "end_mm": [round(b[0], 3), round(b[1], 3)],
            "length_mm": round(_len(a, b), 3),
            "material_present": False,
            "wall_length_contribution_mm": 0.0,
            **{k: v for k, v in c.items()
               if k not in ("kind", "start_mm", "end_mm")},
        })

    by_kind = {k: 0.0 for k in CHAIN_ELEMENTS}
    for e in ordered:
        by_kind[e["CHAIN_ELEMENT"]] += e["length_mm"]
    material = round(sum(e["wall_length_contribution_mm"] for e in ordered), 3)
    no_material = round(sum(e["length_mm"] for e in ordered
                            if e["CHAIN_ELEMENT"] in NO_MATERIAL_EXISTS_HERE),
                        3)

    # A region is closed when the whole chain - faces, portals and
    # continuity spans together - forms ONE cycle with no open or
    # unresolved edge in it. A doorway does not open a room; an edge with
    # nothing built along it does.
    deg, seen = {}, set()
    for e in ordered:
        for pt in (e["start_mm"], e["end_mm"]):
            k = _k(pt, snap_mm)
            deg[k] = deg.get(k, 0) + 1
            seen.add(k)
    every_end_met = bool(deg) and all(n == 2 for n in deg.values())
    adj = {}
    for e in ordered:
        a, b = _k(e["start_mm"], snap_mm), _k(e["end_mm"], snap_mm)
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    connected = False
    if seen:
        stack, hit = [next(iter(seen))], set()
        while stack:
            n = stack.pop()
            if n in hit:
                continue
            hit.add(n)
            stack += adj.get(n, [])
        connected = hit == seen
    closed = (every_end_met and connected
              and not any(e["CHAIN_ELEMENT"] in NO_MATERIAL_EXISTS_HERE
                          for e in ordered))
    return {
        "MODEL": MODEL,
        "CHAIN": ordered,
        "runs": len(runs),
        "run_endpoints": [{"run_index": n, "start_mm": r["start_mm"],
                           "end_mm": r["end_mm"], "closed": r["closed"]}
                          for n, r in enumerate(runs)],
        "elements": len(ordered),
        "CLOSED_BY_DRAWN_MATERIAL": closed,
        "every_chain_end_meets_another": every_end_met,
        "chain_is_connected": connected,
        "material_length_mm": material,
        "length_with_no_material_mm": no_material,
        "length_by_chain_element": {k: round(v, 3)
                                    for k, v in by_kind.items() if v},
        "an_open_edge_is_a_result": AN_OPEN_EDGE_IS_A_RESULT,
        "a_chain_is_not_a_polygon": A_CHAIN_IS_NOT_A_POLYGON,
        "order_and_connectivity_are_the_point":
            ORDER_AND_CONNECTIVITY_ARE_THE_POINT,
    }


def assert_no_material_on_a_gap(chain: dict) -> None:
    """A gap that acquired material length is a bug, not a result."""
    for e in chain["CHAIN"]:
        if e["CHAIN_ELEMENT"] in TOPOLOGY_ONLY_ELEMENTS:
            if e["material_present"] or e["wall_length_contribution_mm"]:
                raise AssertionError(
                    f"{e['CHAIN_ELEMENT']} at SEQ {e['SEQ']} claims "
                    f"{e['wall_length_contribution_mm']} mm of material. "
                    + AN_OPEN_EDGE_IS_A_RESULT)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "CHAIN_ELEMENTS": list(CHAIN_ELEMENTS),
        "MATERIAL_ELEMENTS": list(MATERIAL_ELEMENTS),
        "TOPOLOGY_ONLY_ELEMENTS": list(TOPOLOGY_ONLY_ELEMENTS),
        "NO_MATERIAL_EXISTS_HERE": list(NO_MATERIAL_EXISTS_HERE),
        "a_curve_is_not_its_chord": A_CURVE_IS_NOT_ITS_CHORD,
        "why": {
            "an_open_edge_is_a_result": AN_OPEN_EDGE_IS_A_RESULT,
            "a_chain_is_not_a_polygon": A_CHAIN_IS_NOT_A_POLYGON,
            "order_and_connectivity_are_the_point":
                ORDER_AND_CONNECTIVITY_ARE_THE_POINT,
        },
    }
