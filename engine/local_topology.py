"""E31C — what is missing around a room the graph cannot close.

G8 named three bathrooms with no possible enclosing cycle. "BTH-01 cannot be
enclosed" is a result; "BTH-01's north side has no wall pair within 2 m, and
its east side ends at an unresolved terminus 340 mm from a compatible
continuation" is a repair instruction. This module produces the second kind.

THE RULE IT IS WRITTEN UNDER, and it is the whole reason this is a separate
module from anything that builds geometry:

    DO NOT REPAIR A ROOM BECAUSE THE RASTER SAYS IT IS THERE.

The raster region supplies only a place to LOOK. What is found there is
whatever the vector graph actually contains, and when that is nothing, the
answer is that nothing is there. The printed dimension — 1500 x 2400 for the
washroom, 1600 x 3000 for BED-04's bathroom — is used AFTER candidate
generation, to validate, and is never given to the search.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

# What is absent on a side of an expected room boundary.
SIDE_HAS_WALL = "WALL_PRESENT"
SIDE_NO_WALL_PAIR = "NO_WALL_PAIR_FOUND"
SIDE_ENDS_AT_TERMINUS = "WALL_ENDS_AT_AN_UNRESOLVED_TERMINUS"
SIDE_GAP = "GAP_IN_THE_RUN"

# Why the topology is missing. Named so the repair is obvious.
MISSING_OPENING = "OPENING"
MISSING_WALL_END = "WALL_END"
MISSING_WALL_PAIR = "MISSING_WALL_PAIR"
MISSING_VECTOR_REPRESENTATION = "UNRESOLVED_VECTOR_REPRESENTATION"
MISSING_OTHER = "OTHER"

SIDES = ("north", "south", "east", "west")


@dataclass(frozen=True)
class SideReport:
    side: str
    status: str
    nearest_edge_id: str = ""
    distance_mm: float | None = None
    separation_mm: float | None = None
    nearest_cap_id: str = ""
    nearest_stitch_id: str = ""
    likely_cause: str = ""

    def record(self) -> dict:
        return {"side": self.side, "status": self.status,
                "nearest_edge_id": self.nearest_edge_id,
                "distance_mm": (None if self.distance_mm is None
                                else round(self.distance_mm, 1)),
                "separation_mm": (None if self.separation_mm is None
                                  else round(self.separation_mm, 1)),
                "nearest_cap_id": self.nearest_cap_id,
                "nearest_stitch_id": self.nearest_stitch_id,
                "likely_cause": self.likely_cause}


def analyse_space(space_id: str, bbox_mm, *, edges, termini=(), caps=(),
                  stitches=(), search_mm: float = 2000.0) -> dict:
    """Which sides of an expected local cycle are absent, and what is nearby.

    `bbox_mm` says WHERE to look. It never says what should be found there.
    """
    x0, y0, x1, y1 = bbox_mm
    term_by_edge: dict[str, list] = {}
    for t in termini:
        term_by_edge.setdefault(t.edge_id, []).append(t)

    wanted = {
        "north": ("H", y0, x0, x1),
        "south": ("H", y1, x0, x1),
        "west": ("V", x0, y0, y1),
        "east": ("V", x1, y0, y1),
    }
    out: list[SideReport] = []
    for side, (axis, fixed, lo, hi) in wanted.items():
        best = None
        for e in edges:
            if e.axis != axis:
                continue
            d = abs(e.centreline_mm - fixed)
            if d > search_mm:
                continue
            e_lo, e_hi = min(e.start_mm, e.end_mm), max(e.start_mm, e.end_mm)
            overlap = min(hi, e_hi) - max(lo, e_lo)
            if overlap <= 0:
                continue
            score = d - overlap / 100.0
            if best is None or score < best[0]:
                best = (score, e, d, overlap)
        if best is None:
            out.append(SideReport(
                side, SIDE_NO_WALL_PAIR,
                likely_cause=(
                    f"{MISSING_WALL_PAIR}: no wall pair on this axis within "
                    f"{search_mm:.0f} mm that overlaps this side at all. The "
                    "face lines may exist in the drawing without having paired "
                    "into a wall")))
            continue
        _, e, d, overlap = best
        span = hi - lo
        terms = term_by_edge.get(e.edge_id, ())
        unresolved = [t for t in terms if t.kind == "UNRESOLVED"]
        near_cap = next((c.cap_id for c in caps
                         if abs(c.at_mm - fixed) < 400 or
                         abs(c.at_mm - (lo + hi) / 2) < 400), "")
        near_stitch = next((s.stitch_id for s in stitches
                            if s.axis == axis
                            and abs(s.centreline_difference_mm) < 50
                            and s.status == "STITCH_AMBIGUOUS"), "")
        if overlap >= span * 0.9:
            status, cause = SIDE_HAS_WALL, ""
        elif unresolved:
            status = SIDE_ENDS_AT_TERMINUS
            cause = (f"{MISSING_WALL_END}: the run covering this side ends at "
                     f"an unresolved terminus. Nearest continuation "
                     f"{unresolved[0].nearest_id or 'none'} at "
                     f"{unresolved[0].gap_mm} mm")
        else:
            status = SIDE_GAP
            missing = span - overlap
            cause = (f"{MISSING_OPENING if missing < 1200 else MISSING_WALL_PAIR}"
                     f": the wall covers {overlap:.0f} mm of a {span:.0f} mm "
                     f"side, leaving {missing:.0f} mm uncovered")
        out.append(SideReport(
            side, status, nearest_edge_id=e.edge_id, distance_mm=d,
            separation_mm=e.wall_face_separation_mm, nearest_cap_id=near_cap,
            nearest_stitch_id=near_stitch, likely_cause=cause))

    closed = sum(1 for s in out if s.status == SIDE_HAS_WALL)
    return {
        "space_id": space_id,
        "sides_with_a_wall": closed,
        "sides_missing": 4 - closed,
        "can_a_cycle_exist": closed == 4,
        "sides": [s.record() for s in out],
        "summary": (
            f"{closed} of 4 sides have a wall run covering them. "
            + ("A local cycle is geometrically possible."
               if closed == 4 else
               "No local cycle can close: "
               + "; ".join(s.side for s in out
                           if s.status != SIDE_HAS_WALL) + " unaccounted for.")),
        "repaired": False,
        "why_not_repaired": (
            "the raster region says where to look, never what to find. "
            "Nothing here creates geometry, and the printed dimension is used "
            "only afterwards, to validate a candidate the graph produced on "
            "its own"),
    }


def compare_to_printed(space_id: str, *, candidate_area_m2: float | None,
                       candidate_perimeter_m: float | None,
                       printed_w_mm: float, printed_h_mm: float) -> dict:
    """Validate a candidate AFTER generation. Never before.

    If no candidate exists the printed dimension stays unused: it is evidence
    about a room, not an instruction to build one.
    """
    printed_area = printed_w_mm * printed_h_mm / 1_000_000
    printed_per = 2 * (printed_w_mm + printed_h_mm) / 1000
    if candidate_area_m2 is None:
        return {"space_id": space_id, "candidate": None,
                "printed_area_m2": round(printed_area, 3),
                "printed_perimeter_m": round(printed_per, 2),
                "verdict": "NO_CANDIDATE_GENERATED",
                "why": ("the graph produced no face here. The printed "
                        "dimension is NOT used to manufacture one")}
    return {
        "space_id": space_id,
        "candidate_area_m2": round(candidate_area_m2, 3),
        "printed_area_m2": round(printed_area, 3),
        "area_difference_m2": round(candidate_area_m2 - printed_area, 3),
        "candidate_perimeter_m": (None if candidate_perimeter_m is None
                                  else round(candidate_perimeter_m, 2)),
        "printed_perimeter_m": round(printed_per, 2),
        "verdict": ("CONSISTENT_WITH_PRINTED"
                    if abs(candidate_area_m2 - printed_area)
                    <= 0.1 * printed_area else "DIFFERS_FROM_PRINTED"),
        "why": ("compared after generation. A difference is a finding about "
                "the candidate, not a licence to adjust it"),
    }


def positive_controls(faces, regions, space_ids) -> list[dict]:
    """Can the engine reproduce rooms that are already easy?

    Run before attacking the hard cases, because an engine that cannot close a
    plain rectangular bathroom has nothing useful to say about a merged one.
    The comparison is made AFTER generation and nothing is tuned to it.
    """
    by_space = {r["space_id"]: r for r in regions.values() if r.get("space_id")}
    out = []
    for sid in space_ids:
        r = by_space.get(sid)
        if r is None:
            out.append({"space_id": sid, "result": "NO_RASTER_REGION"})
            continue
        cx, cy = r["centroid_mm"]
        hits = [f for f in faces
                if f.bbox_mm[0] <= cx <= f.bbox_mm[2]
                and f.bbox_mm[1] <= cy <= f.bbox_mm[3]]
        hits.sort(key=lambda f: f.area_m2)
        if not hits:
            out.append({
                "space_id": sid, "room_type": r.get("room_type"),
                "raster_area_m2": round(r["area_m2"], 3),
                "vector_face": None, "result": "NOT_REPRODUCED",
                "why": "no vector face covers this region's centroid"})
            continue
        f = hits[0]
        # A face many times the region's size is not that room — it is a face
        # the room happens to sit inside. Reporting it as a match with a
        # 29,676% area difference dresses a total failure as a near miss.
        if f.area_m2 > max(5 * r["area_m2"], r["area_m2"] + 20):
            out.append({
                "space_id": sid, "room_type": r.get("room_type"),
                "raster_area_m2": round(r["area_m2"], 3),
                "vector_face_id": f.face_id,
                "vector_area_m2": round(f.area_m2, 3),
                "result": "NOT_REPRODUCED",
                "why": (f"the smallest vector face containing this room's "
                        f"centroid is {f.area_m2:.0f} m2 — it contains the "
                        "room rather than being it. No face bounds this room")})
            continue
        out.append({
            "space_id": sid, "room_type": r.get("room_type"),
            "vector_face_id": f.face_id,
            "vector_area_m2": round(f.area_m2, 3),
            "raster_area_m2": round(r["area_m2"], 3),
            "area_difference_m2": round(f.area_m2 - r["area_m2"], 3),
            "area_difference_pct": (
                round((f.area_m2 - r["area_m2"]) / r["area_m2"] * 100, 1)
                if r["area_m2"] else None),
            "vector_perimeter_m": round(f.perimeter_m, 2),
            "result": ("REPRODUCED"
                       if abs(f.area_m2 - r["area_m2"]) <= 0.15 * r["area_m2"]
                       else "DIFFERS")})
    return out
