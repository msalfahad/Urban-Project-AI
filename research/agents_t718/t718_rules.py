"""T-718 rules (project-agnostic; scope: every villa). Research only, unwired: no engine module, method, rule-version or
knowledge file reads this. Built on R-T412-1 (a drawn edge is a PAIR: front edge downhill, riser face 0.050 uphill),
R-T410 / R-T715-4 (skirting pieces per side, zigzag / sloped figures), UP-STAIR-010 / -011, R-T704-2 (stopper to
stopper), R-T711-2 (floor = the smaller reading), R-T715-1 / -2; none edited. Rounding: bound_rounding_v1 (R-T696-1).

R-T718-1 1.0.0  STAIR SKIRTING PIECES ARE CUT ON THE FRONT-EDGE DATUM.
    Physical element: the skirting strip on a wall beside a flight. Seen from above, each tread's visible top runs from
    its own front edge to the next front edge (the part behind the next nosing is covered), so the strip's horizontal
    legs on one wall stretch run from the first front edge to the cut (column face, opening jamb, wall end); the sloped
    form rakes on the nosing line (UP-STAIR-011). A piece's plan length is therefore measured from FRONT-EDGE stations.
    The riser-face datum (the companion line) shifts every station by the drawn nosing projection p: the flight run and
    the risers per piece are datum-invariant (a riser belongs to the piece holding its face), but the first and last
    pieces of a cut flight differ by exactly p. A reading that differs from the pieces by p at a cut is reconciled to the
    datum, never split or averaged. A riser's vertical leg lies on the wall just downhill of its face, so riser k belongs
    to the piece (lo, hi] holding its face (a jamb exactly on a face keeps that riser on the downhill piece). Refused:
    no drawn projection (single line, no pair), stations not monotone, a cut outside the flight.

R-T718-2 1.0.0  UPPER END OF A STAIR FRONT: STOPPER TO STOPPER ON ONE DRAWN GEOMETRY.
    A riser face or front edge of a drawn line cannot be longer than the part of that line between the drawn outline
    edges of the stair (opening / slab edges, the void beyond): for a line at perpendicular offset d from the centre of a
    round flight with outline radii r1 < r2, chord = sqrt(r2^2 - d^2) - sqrt(r1^2 - d^2). A step whose front continues
    along a drawn curtail outline adds that arc (the curtail step's face), once. In a turn (winder) region whose
    subdivision is not drawn, every straight front lies inside the drawn region, so each is at most the region's
    diameter (rectangle a x b: hypot(a, b)). Every input of an AT_MOST must be DRAWN (handle named): a schedule, a
    nominal width, a lane width from a rule or a drawn end combined with a schedule value is refused.

R-T718-3 1.0.0  FLOOR OF A STAIR FRONT = THE DRAWN LINE.
    The physical front / face is at least its drawn line (sum by handle); a floor may rise only to a drawn sum (never to
    a figure from a rule), and a front drawn past the lane (over a band whose role is open) counts only its in-lane part.
"""
from __future__ import annotations

import sys
from decimal import Context, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

X = Decimal
_C = Context(prec=50)
RULES = {"R-T718-1": "1.0.0", "R-T718-2": "1.0.0", "R-T718-3": "1.0.0"}
DRAWN = "DRAWN"


class Refused(ValueError):
    pass


def _d(v, what, positive=True, unit="m"):
    if unit != "m":
        raise Refused(f"{what}: unit {unit!r} refused (metres only)")
    if v is None:
        raise Refused(f"{what}: missing (never 0)")
    try:
        d = BR.D(v)
    except BR.BoundRoundingError as e:
        raise Refused(f"{what}: {e}") from None
    if positive and d <= 0:
        raise Refused(f"{what}: must be positive, got {d}")
    return d


def sqrt(x):
    return _C.sqrt(BR.D(x))


# ------------------------------------------------------------------ R-T718-1
def pieces(*, fronts, faces, cuts, unit="m"):
    """fronts / faces: stations (m) of the drawn front edges and riser faces along the flight, uphill positive, from any
    origin; faces may hold None where only the front is drawn (the projection is then the drawn pairs' common value).
    cuts: stations of the piece boundaries strictly inside the flight. Returns per datum the piece plans and risers."""
    if unit != "m":
        raise Refused(f"unit {unit!r} refused (metres only)")
    f = [_d(v, "front station", positive=False) for v in fronts]
    if len(f) < 2 or any(b <= a for a, b in zip(f, f[1:])):
        raise Refused("front stations must be at least two and strictly increasing (uphill)")
    if len(faces) != len(f):
        raise Refused("one face entry per front (None where not drawn)")
    pr = {BR.D(c) - a for a, c in zip(f, faces) if c is not None}
    if not pr:
        raise Refused("no drawn pair: the nosing projection is not drawn (R-T412-1)")
    if len(pr) != 1:
        raise Refused(f"drawn projections differ {sorted(pr)}: re-read the pairs")
    p = pr.pop()
    if p <= 0:
        raise Refused(f"projection {p} <= 0: the companion is not uphill")
    face = [a + p for a in f]
    cs = [_d(c, "cut station", positive=False) for c in cuts]
    if any(b <= a for a, b in zip(cs, cs[1:])):
        raise Refused("cuts must be strictly increasing")
    if cs and not (f[0] < cs[0] and cs[-1] < f[-1]):
        raise Refused("a cut outside the flight")
    out = {"projection_m": p, "run_m": f[-1] - f[0]}
    for name, ref in (("front_edge", f), ("riser_face", face)):
        b = [ref[0]] + cs + [ref[-1]]
        plans = [y - x for x, y in zip(b, b[1:])]
        if any(v <= 0 for v in plans):
            raise Refused(f"{name}: a cut lies within the projection of the end edge: re-read")
        out[name] = {"plans_m": plans, "run_m": ref[-1] - ref[0]}
    # risers per piece: the vertical leg of riser k lies on the wall just DOWNHILL of its face (above the lower tread,
    # against the face), so riser k belongs to the piece (lo, hi] that holds its face. Counting by front edge gives the
    # same answer unless a cut falls strictly inside a nosing projection: then the face count governs (flagged).
    def count(ref, closed_right):
        b = [ref[0] - 1] + cs + [ref[-1] + 1]
        if closed_right:
            return [sum(1 for v in ref if lo < v <= hi) for lo, hi in zip(b, b[1:])]
        return [sum(1 for v in ref if lo <= v < hi) for lo, hi in zip(b, b[1:])]
    out["risers"] = count(face, True)
    out["risers_by_front"] = count(f, False)
    out["cut_inside_projection"] = out["risers"] != out["risers_by_front"]
    if sum(out["risers"]) != len(f):
        raise Refused("risers do not sum to the drawn edges")
    out["datum_shift_first_last_m"] = (out["front_edge"]["plans_m"][0] - out["riser_face"]["plans_m"][0],
                                       out["front_edge"]["plans_m"][-1] - out["riser_face"]["plans_m"][-1])
    return out


# ------------------------------------------------------------------ R-T718-2
def _drawn(v, what, positive=True):
    if not isinstance(v, tuple) or len(v) != 2 or v[1] != DRAWN:
        raise Refused(f"{what}: an AT_MOST input must be (value, 'DRAWN') with a drawn source; got {v!r}")
    return _d(v[0], what, positive=positive)


def chord(*, offset, r_in, r_out):
    """part of a straight line at perpendicular offset `offset` from the centre between the circles r_in < r_out
    (the outer half: the side of the line that leaves the inner circle outward)."""
    d = _drawn(offset, "offset", positive=False)
    if d < 0:
        raise Refused("offset < 0")
    a, b = _drawn(r_in, "inner outline radius"), _drawn(r_out, "outer outline radius")
    if not d < a < b:
        raise Refused(f"need offset {d} < r_in {a} < r_out {b}")
    return _C.subtract(sqrt(_C.subtract(b * b, d * d)), sqrt(_C.subtract(a * a, d * d)))


def round_front_at_most(*, offset, r_in, r_out, curtail_arc=None):
    c = chord(offset=offset, r_in=r_in, r_out=r_out)
    if curtail_arc is not None:
        c = BR.add(c, _drawn(curtail_arc, "curtail arc"))
    return c


def curtail_front_at_most(*, start_r, offset, r_out, curtail_arc):
    """a curtail step's front: from the drawn start of its straight part (on the curtail outline) to the outer edge,
    plus the curtail arc."""
    d = _drawn(offset, "offset", positive=False)
    s, b = _drawn(start_r, "start radius"), _drawn(r_out, "outer outline radius")
    if not 0 <= d <= s < b:
        raise Refused("need offset <= start radius < outer radius")
    return BR.add(_C.subtract(sqrt(_C.subtract(b * b, d * d)), sqrt(_C.subtract(s * s, d * d))),
                  _drawn(curtail_arc, "curtail arc"))


def turn_front_at_most(*, side_a, side_b):
    a, b = _drawn(side_a, "turn region side a"), _drawn(side_b, "turn region side b")
    return sqrt(_C.add(a * a, b * b))


# ------------------------------------------------------------------ R-T718-3
def drawn_floor(lengths, *, lane=None):
    """sum of drawn lengths by handle; `lane` (value, 'DRAWN') caps each front at its in-lane part."""
    tot = X(0)
    cap = _drawn(lane, "lane") if lane is not None else None
    for h, v in lengths:
        if not h:
            raise Refused("a floor term names its handle")
        x = _d(v, f"drawn length {h}")
        tot = BR.add(tot, min(x, cap) if cap is not None else x)
    return tot
