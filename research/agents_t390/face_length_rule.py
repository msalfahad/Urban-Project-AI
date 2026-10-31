"""T-390 face-length rule R-T390-1 (research, stdlib only, any villa; not wired into any method).

Physical element: a room FACE is the drawn wall (or column) surface the room touches, between its drawn ends. An OPEN
SIDE (the walk's VIRTUAL class: no drawn line) is never wall, whatever wall band's face line it happens to cross or
touch. Two merged walks of one contour must therefore give one geometric face per room:

  (a) GEOMETRIC FACE per room = walked contour - its OPEN-SIDE RUNS. An open-side run is a maximal (cyclic) run of
      VIRTUAL samples of at least MIN_OPEN_M (0.10 m, the T-128 r3 merge rule); a VIRTUAL run shorter than that between
      drawn lines is a CORNER piece (drafting / region noise at a drawn corner) and stays face.
  (b) A VIRTUAL sample of an open-side run that a face crosswalk puts on a band face line (perpendicular offset within
      the face tolerance, along-band within the end reach) is a TOLERANCE ARTEFACT, never face length. Its cause is
      named from the run's direction against the band:
        CROSSING        the open side passes through both face lines of the band (a band stretch with no wall built);
        T_JUNCTION      the open side ends perpendicular on the face line (it meets a continuous wall face);
        END_REACH       the open side runs collinear with the face line beyond the band's end (past the drawn wall end);
        ON_FACE_PARALLEL the open side runs on the face line INSIDE the band's span: the band says wall but no drawn
                        line was found: never face, flagged UNRESOLVED for a drawing check.
  (c) A family's face length is checked against (a), and a per-wall face length is the crosswalk's face metres less
      the artefact metres of (b) (= its WALL + COLUMN + WINDOW + DOOR + GAP + CORNER metres).
  (d) Refusals: an open-side (VIRTUAL) piece offered as face; a jamb return (wall-end face at an opening) counted
      twice (in two rooms or twice in one); a face measured past its drawn end into an open side; lengths outside
      0 .. 500 m or sample steps outside 0 .. 0.05 m (units).

Statuses are the board's five (WORKFLOW_CONTROLS s.5). Rule id R-T390-1, proposed (scope: every villa; provenance: T-128
r3 merge rule + T-250 crosswalk tolerances, Checker-merged; this task's reconciliation on the development villa).
"""
from __future__ import annotations

import math

MIN_OPEN_M = 0.10        # T-128 r3: a VIRTUAL run under 0.10 m is corner noise (wall)
TOL_LEN_M = 0.025        # T-388 (d'): five 5 mm samples
PERP_COS = math.cos(math.radians(45.0))
FACE_CLASSES = ("WALL", "COLUMN", "WINDOW", "DOOR", "GAP", "CORNER")
CAUSES = ("CROSSING", "T_JUNCTION", "END_REACH", "ON_FACE_PARALLEL")


class FaceLengthError(ValueError):
    pass


def _check_len(m, what):
    if m is None or not 0 <= float(m) <= 500:
        raise FaceLengthError(f"{what}: length {m} outside 0 .. 500 m (units?)")
    return float(m)


def cyclic_runs(seq):
    """seq: [(cls, seg_m)] of ONE closed ring in walk order. Returns [(cls, length_m, [indices])], cyclic (a run that
    wraps past the ring start is one run), the same convention as the T-128 r3 walk."""
    n = len(seq)
    if n == 0:
        return []
    for c, seg in seq:
        if not 0 < seg < 0.05:
            raise FaceLengthError(f"sample step {seg} m outside 0 .. 0.05 (units?)")
    start = 0
    while start < n - 1 and seq[start][0] == seq[-1][0]:
        start += 1
    runs, cur = [], None
    for k in list(range(start, n)) + list(range(0, start)):
        c, seg = seq[k]
        if cur is None or c != cur[0]:
            cur = [c, 0.0, []]
            runs.append(cur)
        cur[1] += seg
        cur[2].append(k)
    return [(c, ln, ix) for c, ln, ix in runs]


def open_side_split(rings):
    """rings: [[(cls, seg_m)]]. Returns {'open_m', 'corner_m', 'open_runs': [m], 'is_open': [[bool per sample]]}."""
    out = {"open_m": 0.0, "corner_m": 0.0, "open_runs": [], "is_open": []}
    for seq in rings:
        flags = [False] * len(seq)
        for c, ln, ix in cyclic_runs(seq):
            if c != "VIRTUAL":
                continue
            if ln >= MIN_OPEN_M - 1e-9:
                out["open_m"] += ln
                out["open_runs"].append(round(ln, 4))
                for k in ix:
                    flags[k] = True
            else:
                out["corner_m"] += ln
        out["is_open"].append(flags)
    out["open_m"] = round(out["open_m"], 4)
    out["corner_m"] = round(out["corner_m"], 4)
    return out


def geometric_face_m(contour_m, open_m):
    """(a): contour less the open-side runs."""
    c = _check_len(contour_m, "contour")
    o = _check_len(open_m, "open side")
    if o > c + 1e-9:
        raise FaceLengthError(f"open side {o} m longer than the contour {c} m")
    return round(c - o, 4)


def artefact_cause(run_dir, band_u, s, band_len, sides_seen):
    """(b): run_dir, band_u: unit vectors (run direction at the sample, band axis); s: along-band position of the
    sample (0 .. band_len inside the span); sides_seen: the set of band sides (+1 / -1) the SAME open-side run touches
    on this band."""
    L = _check_len(band_len, "band")
    cos = abs(run_dir[0] * band_u[0] + run_dir[1] * band_u[1])
    if cos < PERP_COS:                       # the open side runs across the band
        return "CROSSING" if {1, -1} <= set(sides_seen) else "T_JUNCTION"
    if s < 0 or s > L:
        return "END_REACH"
    return "ON_FACE_PARALLEL"


def face_from_pieces(pieces):
    """(c) / (d): pieces [(cls, m, ref)] of one room face (one wall side). Sum of face classes; an open-side piece is
    refused (an open side is never measured as face)."""
    tot = 0.0
    for cls, m, ref in pieces:
        if cls == "VIRTUAL":
            raise FaceLengthError(f"{ref}: open side offered as face length ({m} m) (R-T390-1 d)")
        if cls not in FACE_CLASSES:
            raise FaceLengthError(f"{ref}: unknown face class {cls}")
        tot += _check_len(m, ref)
    return round(tot, 4)


def face_end(drawn_end_s, walked_end_s, beyond_class):
    """(d): a face stops at its drawn end. A walked end past the drawn end is accepted only when the stretch beyond is
    drawn wall / column (a continuation); past it into an open side (VIRTUAL) the face is refused."""
    if walked_end_s > drawn_end_s + 1e-9 and beyond_class == "VIRTUAL":
        raise FaceLengthError(f"face measured {walked_end_s - drawn_end_s:.3f} m past its drawn end into an open side "
                              "(R-T390-1 d)")
    return min(walked_end_s, drawn_end_s) if beyond_class == "VIRTUAL" else walked_end_s


def check_jambs(jambs):
    """(d): jambs [(room, jamb_id, m)]: one wall-end face at an opening belongs to ONE room face, once."""
    seen = {}
    for room, jid, m in jambs:
        _check_len(m, jid)
        if jid in seen:
            raise FaceLengthError(f"jamb return {jid} counted twice ({seen[jid]} and {room}) (R-T390-1 d)")
        seen[jid] = room
    return round(sum(m for _, _, m in jambs), 4)


def closure(family_m, contour_m, open_m, top_m=None, tol=TOL_LEN_M):
    """(c): family face length vs the geometric face; returns {'residual_m', 'm2', 'ok'} (m2 None on a HELD top)."""
    geo = geometric_face_m(contour_m, open_m)
    d = round(_check_len(family_m, "family") - geo, 4)
    if top_m is not None and not 0 < top_m <= 20:
        raise FaceLengthError(f"height {top_m} outside 0 .. 20 m (units?)")
    return {"geometric_m": geo, "residual_m": d, "ok": abs(d) <= tol,
            "m2": (round(d * top_m, 4) if top_m is not None else None)}
