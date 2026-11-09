"""COLUMN_END_CENSUS_V2 (R-T526-1, research rule, every villa): which RC column a masonry run END abuts.

Physical element (ERS s.2.1): the vertical block-to-concrete joint where the last block of a masonry run meets the face
of an RC column. It exists when the column face stands across the full wall thickness at the run's end face, within one
mortar joint of it, whether the column belongs to the run itself or to the wall the run meets (a column standing in the
met wall of a T or L junction, or drawn as a separate outline beyond a free end).

Census rule V1 (T-274 run pieces -> T-355 R-T355-3 junctions, T-317 joints / joints_to_soffit): a junction is a
boundary between two CONSECUTIVE pieces of one run of kinds BLOCK and COLUMN. A column is a piece only when the run
CROSSES its outline (T-274 cuts the run at every column boundary between its end points), so a column that lies just
BEYOND a run end (the run ends on the column face) is never a piece and its junction is never listed. That is the
systematic omission found by F-T520-1: the rule is blind to the end condition, not to a drawing layer.

Census rule V2 (this module): V1's interior junctions, plus one END junction at every run end classified from the
drawing by what lies beyond the end face (`classify_end`):
  COLUMN_PIECE_IN_RUN  the run's own first / last piece is a column: V1 already lists the junction (never added twice).
  COLUMN               a column outline covers the probe strip [gap, gap + probe] x full thickness (0.5 mm inset each
                       side) with cover >= COVER_FULL and gap == 0: an END junction, the block run length is unchanged.
  COLUMN_WITHIN_JOINT  as COLUMN but 0 < gap <= joint: the drawn gap is inside the mortar joint the owner method lays
                       (10 mm, owner 2026-10-29); the junction exists, gap reported, the run length is unchanged (the
                       joint fills the gap; the block count is a separate rule and is not moved here).
  GAP_HELD             full cover but joint < gap <= search: a drawn void wider than a joint between block and column;
                       no basis to call it a butt joint or a free end: HELD naming the gap (never 0, never a junction).
  PARTIAL_COLUMN       0 < cover < COVER_FULL: the column face meets only part of the thickness (a column at an angle
                       or offset): HELD with the contact width as the bound [0, contact width x height].
  NO_COLUMN            nothing (or a zero-area corner touch) beyond the end: the end class comes from the masonry
                       reading (O / F), unchanged from V1.
Never a default: a missing outline, thickness or joint raises; units are metres (a value in mm is refused).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Polygon

PROBE = 0.02          # m: depth of the end-face strip the cover is read on (T-520 probe)
INSET = 0.0005        # m: lateral inset each side (a drawn face touching the wall face is not counted twice)
COVER_FULL = 0.999    # fraction of the probe strip area: a full-thickness face (float hairlines on drawn outlines)
AREA_EPS = 1e-9       # m2: a corner / edge touch has no area (no joint face)
SEARCH = 0.05         # m: how far beyond the end a column is looked for (L-P9-04 stub convention: 0.05 m)


class EndCensusError(ValueError):
    pass


@dataclass(frozen=True)
class EndResult:
    cls: str                 # see module text
    gap_m: float | None      # distance from the run end face to the column face along the run axis
    cover: float             # column cover of the probe strip at the column face
    contact_m: float | None  # contact width across the wall thickness
    column: int | None       # index of the column in the list passed
    junction: bool | None    # True = a block-to-column joint exists at this end; False = none; None = HELD
    held: str = ""


def _strip(e, u, s0, s1, half):
    """rectangle s0..s1 along the outward unit vector u from the end point e, +- half across."""
    nx, ny = -u[1], u[0]
    p = lambda s, n: (e[0] + u[0] * s + nx * n, e[1] + u[1] * s + ny * n)
    return Polygon([p(s0, -half), p(s1, -half), p(s1, half), p(s0, half)])


def _check(a, b, t, joint):
    if t is None or joint is None:
        raise EndCensusError("wall thickness and mortar joint are required (no default)")
    if not (0.05 <= t <= 0.60):
        raise EndCensusError(f"wall thickness {t} is not in metres (0.05 .. 0.60 m expected)")
    if not (0.0 < joint <= 0.03):
        raise EndCensusError(f"mortar joint {joint} is not in metres (0 .. 0.03 m expected)")
    L = math.dist(a, b)
    if L <= 0:
        raise EndCensusError("run of zero length")
    return L


def classify_end(a, b, t, end, columns, joint, own_piece_is_column=False, probe=PROBE, search=SEARCH):
    """classify one run end (end 0 at a, end 1 at b) against the column outlines (shapely Polygons, metres)."""
    L = _check(a, b, t, joint)
    if columns is None:
        raise EndCensusError("column outlines are required (an empty list means: none drawn on this storey)")
    if own_piece_is_column:
        return EndResult("COLUMN_PIECE_IN_RUN", 0.0, 1.0, t, None, True)
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    e, u = (a, (-d[0], -d[1])) if end == 0 else (b, d)
    half = t / 2 - INSET
    zone = _strip(e, u, 0.0, search, half)
    best = None
    for k, C in enumerate(columns):
        X = C.intersection(zone)
        if X.is_empty or X.area <= AREA_EPS:
            continue
        ss = [(x - e[0]) * u[0] + (y - e[1]) * u[1] for g in getattr(X, "geoms", [X]) for x, y in g.exterior.coords]
        gap = max(0.0, min(ss))
        if gap < 1e-6:
            gap = 0.0
        P = _strip(e, u, gap, gap + probe, half)
        cov = C.intersection(P).area / P.area
        if best is None or (gap, -cov) < (best[1], -best[2]):
            best = (k, gap, cov)
    if best is None:
        return EndResult("NO_COLUMN", None, 0.0, None, None, False)
    k, gap, cov = best
    contact = round(cov * 2 * half, 6)
    if cov < COVER_FULL:
        return EndResult("PARTIAL_COLUMN", round(gap, 6), round(cov, 6), contact, k, None,
                         f"column meets {contact:.4f} m of the {t:.3f} m thickness: joint bound 0 .. contact x height")
    if gap == 0.0:
        return EndResult("COLUMN", 0.0, round(cov, 6), round(t, 6), k, True)
    if gap <= joint + 1e-9:
        return EndResult("COLUMN_WITHIN_JOINT", round(gap, 6), round(cov, 6), round(t, 6), k, True)
    return EndResult("GAP_HELD", round(gap, 6), round(cov, 6), round(t, 6), k, None,
                     f"drawn void {gap * 1000:.1f} mm between the run end and the column face, wider than the "
                     f"{joint * 1000:.0f} mm joint: butt joint or free end not established")


def end_junctions(run_id, pieces_kinds, end_results):
    """V2 junction list for one run: V1 interior junctions (consecutive BLOCK / COLUMN pieces) + one per END class
    COLUMN / COLUMN_WITHIN_JOINT; COLUMN_PIECE_IN_RUN is V1's own (never twice); HELD ends listed as HELD, never 0."""
    out = []
    for i in range(len(pieces_kinds) - 1):
        if {pieces_kinds[i], pieces_kinds[i + 1]} == {"BLOCK", "COLUMN"}:
            out.append({"run": run_id, "at": f"piece {i}/{i + 1}", "source": "V1", "state": "LISTED"})
    for end, r in enumerate(end_results):
        if r.cls in ("COLUMN", "COLUMN_WITHIN_JOINT"):
            inner = pieces_kinds[0] if end == 0 else pieces_kinds[-1]
            if inner != "BLOCK":
                raise EndCensusError(f"{run_id} end {end}: a column beyond the end but the end piece is {inner}")
            out.append({"run": run_id, "at": f"end {end}", "source": "V2_END", "state": "LISTED", "gap_m": r.gap_m})
        elif r.cls in ("GAP_HELD", "PARTIAL_COLUMN"):
            if not r.held:
                raise EndCensusError("a held end needs its reason")
            out.append({"run": run_id, "at": f"end {end}", "source": "V2_END", "state": "HELD", "held": r.held})
    return out

