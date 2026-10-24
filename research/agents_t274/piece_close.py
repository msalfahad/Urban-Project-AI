"""R-T274-1: a block wall's height pieces close its census length (research rule, any villa; T-274).

Provenance: Checker T-180 slot 15:59 / 16:03 / 16:04 (2026-10-24, own re-measure of 1F-W20 / 1F-W22 / 1F-W08) and
21:05 / 22:03 (1F-W00 W18); ERS s.2-4 lessons rows 'height pieces do not close' and 'opening deducted by schedule width'.
Builds on R-T261-1 (research/agents_t261/piece_split.py: drawn member extents, held pieces never 0) and Q-60 A (block to
the underside of the member above). No engine module is changed; nothing here is applied to the register.

Physical element: the block wall stands under whatever member is drawn above each length of its census run; the height
over a length is the storey less THAT member's depth (beam: schedule depth; slab: thickness). So:

1. CLOSURE: the piece lengths sum to the census length within TOL_M (1 mm). A piece list longer than the wall is refused
   (OVER_CENSUS); a shorter one is NOT_CLOSED: the residual is found on the drawing and assigned to the member drawn over
   it, or carried as its own HELD piece by name (never 0, never spread into a mean, never closed into a neighbour).
2. EXTENT: each piece length is the member's extent ALONG THE WALL CENTRELINE (a band crossing at a skew covers
   width / cos(skew), never its normal width); measured by cutting the run at the member's drawn edges.
3. NO MEAN: the gross is the sum of piece length x piece height; a weighted-mean height over pieces that do not close is
   refused (WEIGHTED_MEAN_NOT_CLOSED).
4. SLIVERS: a piece shorter than TOL_M is a drafting offset between two drawn edges, not a member (R-WP-BURIED-1.1 r2
   tolerance): it joins the neighbour it touches, preferring a beam (the deeper soffit) when one side is a beam.
5. OPENINGS: an opening is deducted by its part inside the counted masonry (gap length inside the run less the part
   inside a column / member outline already excluded from the length), never by its schedule width.
"""
from __future__ import annotations

import math

TOL_M = 0.001
RULE_ID = "R-T274-1"


class PieceError(ValueError):
    """a piece list or a request the rule refuses (the code is the first word of the message)."""


def skew_extent(width_m: float, skew_deg: float) -> float:
    """the length of wall centreline under a straight band of normal width `width_m` crossing at `skew_deg` from the
    wall's normal (0 = square crossing)."""
    if width_m <= 0:
        raise PieceError("BAD_WIDTH: a band width must be positive")
    c = math.cos(math.radians(skew_deg))
    if c <= 0.05:
        raise PieceError("BAD_SKEW: a band nearly parallel to the wall is not a crossing (read it as a run piece)")
    return width_m / c


def join_slivers(pieces: list[dict], tol: float = TOL_M) -> list[dict]:
    """rule 4: every piece shorter than `tol` joins a neighbour (a beam neighbour first, else the longer one)."""
    ps = [dict(p) for p in pieces]
    i = 0
    while i < len(ps):
        p = ps[i]
        if p["length_m"] < tol and len(ps) > 1:
            nb = [j for j in (i - 1, i + 1) if 0 <= j < len(ps)]
            beam = [j for j in nb if ps[j].get("kind") == "BEAM"]
            j = (beam or sorted(nb, key=lambda k: -ps[k]["length_m"]))[0]
            ps[j]["length_m"] += p["length_m"]
            ps[j]["slivers_m"] = round(ps[j].get("slivers_m", 0.0) + p["length_m"], 9)
            del ps[i]
            i = 0
            continue
        i += 1
    return ps


def close(census_m: float, pieces: list[dict], tol: float = TOL_M) -> dict:
    """rule 1: {'status': CLOSED | NOT_CLOSED, 'piece_sum_m', 'residual_m'}; OVER_CENSUS is refused."""
    if census_m is None or census_m <= 0:
        raise PieceError("NO_CENSUS: a wall without a census length cannot be closed (HELD, never 0)")
    for p in pieces:
        if p.get("length_m") is None or p["length_m"] < 0:
            raise PieceError("BAD_PIECE: every piece needs a non-negative length")
    s = sum(p["length_m"] for p in pieces)
    r = census_m - s
    if r < -tol:
        raise PieceError(f"OVER_CENSUS: pieces sum {s:.4f} m on a {census_m:.4f} m wall ({-r:.4f} m too long)")
    return {"status": "CLOSED" if abs(r) <= tol else "NOT_CLOSED", "piece_sum_m": round(s, 6),
            "residual_m": round(r, 6)}


def gross(census_m: float, pieces: list[dict], tol: float = TOL_M) -> dict:
    """rules 1 + 3: the gross of a closed piece list. A piece with height None is HELD by name: the result is the
    established part plus the held pieces listed (never 0). A non-closing list is refused."""
    c = close(census_m, pieces, tol)
    if c["status"] != "CLOSED":
        raise PieceError(f"NOT_CLOSED: residual {c['residual_m']:.4f} m has no member; find the member drawn over it "
                         "or add it as a HELD piece by name")
    est = sum(p["length_m"] * p["height_m"] for p in pieces if p.get("height_m") is not None)
    held = [p for p in pieces if p.get("height_m") is None]
    for p in held:
        if not p.get("held_item"):
            raise PieceError("HELD_UNNAMED: a held piece names the missing item (member, depth, datum)")
    return {"status": "ESTABLISHED" if not held else "ESTABLISHED_PART_PLUS_HELD", "established_m2": round(est, 6),
            "established_length_m": round(sum(p["length_m"] for p in pieces if p.get("height_m") is not None), 6),
            "held": [{"length_m": round(p["length_m"], 6), "held_item": p["held_item"]} for p in held]}


def weighted_mean_gross(census_m: float, pieces: list[dict], tol: float = TOL_M) -> float:
    """the register v2 form (census x weighted mean height): allowed only when the pieces close (then it equals the
    sum of piece areas); refused otherwise (rule 3)."""
    c = close(census_m, pieces, tol)
    if c["status"] != "CLOSED":
        raise PieceError("WEIGHTED_MEAN_NOT_CLOSED: a mean height of pieces that do not close the wall is refused")
    s = sum(p["length_m"] for p in pieces)
    return census_m * sum(p["length_m"] * p["height_m"] for p in pieces) / s


def opening_in_masonry(gap_from: float, gap_to: float, run: tuple, excluded: list[tuple] = ()) -> float:
    """rule 5: metres of an opening's drawn gap [gap_from, gap_to] (stations along the wall) that lie inside the counted
    run [run[0], run[1]] and outside every excluded interval (column / member outlines cut from the length)."""
    if gap_to < gap_from:
        raise PieceError("BAD_GAP: gap end before its start")
    lo, hi = max(gap_from, run[0]), min(gap_to, run[1])
    if hi <= lo:
        return 0.0
    inside = hi - lo
    for a, b in excluded:
        inside -= max(0.0, min(b, hi) - max(a, lo))
    return max(0.0, inside)


def shared_corner_height(storey_m: float, printed_depth_m: float, candidate_depths_m: list) -> float | None:
    """rule 6 (corner square shared by two drawn bands, one of them with no printed depth): the block under the corner
    stops at the lowest underside of the two. The height is established only when the printed member is at least as
    deep as every candidate depth recorded for the unprinted one (then the printed depth governs whatever the designer
    answers); with no candidate recorded, or a candidate deeper than the printed member, it stays HELD (None)."""
    if printed_depth_m is None or printed_depth_m <= 0:
        raise PieceError("BAD_DEPTH: the printed member needs its depth")
    if not candidate_depths_m:
        return None
    if max(candidate_depths_m) > printed_depth_m + 1e-9:
        return None
    return round(storey_m - printed_depth_m, 6)
