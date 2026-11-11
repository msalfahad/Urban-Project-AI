"""R-T686-1 .. -4: plaster / paint round 3 (every villa; research provenance, proposed; nothing wired or released).

R-T686-1 BOUNDED ROOF DATUM -> FINISH HEIGHTS. Where a room's roof slab top is not printed (a roof mark may be a
  finished level, Q-54 B) but is BOUNDED by the drawings (s_lo from a drawn head under a printed beam on one plane,
  R-T678-2; s_hi = the printed roof mark, a slab top never lies above its finished roof), each finish height is a bound,
  never a chosen point:
    plaster / render to the slab soffit (Q-72, owner 2026-11-02):  S = s - slab - FFL
    paint / wall-tile top at the finished ceiling (Q-43 A / Q-48 A, the owner manual G1: beam 0.60 + ceiling 0.15 below
    the structural top):                                          H = s - beam - ceiling - FFL
  A bound with s_lo > s_hi, a term without a source, a height <= 0, or a value read in mm / cm is refused. The owner
  decision Q-54 B (HOLD the 4.00 m interval) is respected: no point inside the bound is released; the line stays HELD
  with low .. high.

R-T686-2 OPENING PORTION INSIDE A BAND [0, H]. Each opening is deducted only where it physically exists (Q-73) and only
  the part inside the measured band:
    sill and head known           -> exact w x (min(head, H) - max(sill, 0)), clipped at 0
    height h known, sill not      -> the hole lies between the floor and the soffit S:
                                     low w x max(0, h - (S - H)) .. high w x min(h, H)
    height not printed (D-45)     -> 0 .. w x min(cap, H)   (cap = the census cap or H)
  The LOW area uses the HIGH deduction at H_lo and the HIGH area the LOW deduction at H_hi.

R-T686-3 FULLY TILED WET ROOM WITH NO CEILING DATUM. The tile-backing render top (= tile top = finished ceiling,
  Q-48 A) of a wet room whose floor level or ceiling plane is not drawn is bounded below by the highest established
  opening head of the room (a ceiling never lies below a door head) and above by the owner G1 ceiling of the storey
  (an absolute level, independent of the room's own floor); the floor-level alternatives are both carried. A room with
  no established head has no lower bound and stays blank (HELD by name, never 0).

R-T686-4 SOURCE PRECEDENCE FOR AN OPENING HEIGHT (ERS evidence hierarchy). A vector record (DXF / DWF geometry with the
  view's own level ticks and an issue check) governs a raster sheet, which is never scaled; the raster reading is kept
  as a named residual (area impact) only. Two vector records that disagree beyond their tolerance are refused (HELD).

Generic: a painted area is never taken on a tiled face (wet-area rule 2026-11-02: no paint on tiled faces); a bound
low > high or low <= 0 is refused; HELD keeps measured_net None.
"""
from __future__ import annotations

from decimal import Context, Decimal, localcontext

PREC = 40
Q6 = Decimal("0.000001")


class RuleError(Exception):
    pass


def ctx40():
    return localcontext(Context(prec=PREC))


def D(x):
    return None if x is None or x == "" else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


def _term(name, t, lo=Decimal("0"), hi=Decimal("30")):
    """t = (value, source); refused without a source, <= lo, or above hi (mm / cm read as m)."""
    if not isinstance(t, tuple) or len(t) != 2:
        raise RuleError(f"term {name}: (value, source) expected")
    val, src = t
    if not src:
        raise RuleError(f"term {name} has no source: HELD")
    d = D(val)
    if d is None or d <= lo:
        raise RuleError(f"term {name} = {val}: missing or <= {lo} (held is never 0)")
    if d > hi:
        raise RuleError(f"term {name} = {val}: unit slip refused (mm or cm read as m)")
    return d


# ------------------------------------------------------------------ R-T686-1

def finish_heights(s_lo, s_hi, ffl, slab, beam, ceiling):
    """bounded structural top s -> plaster soffit height S and paint / tile top H above the FFL, each (lo, hi)."""
    with ctx40():
        a, b = _term("s_lo", s_lo), _term("s_hi", s_hi)
        if a > b:
            raise RuleError(f"datum bound refused: s_lo {a} > s_hi {b}")
        f = _term("FFL", ffl, lo=Decimal("-10"))
        t = _term("slab", slab, hi=Decimal("1"))
        bm = _term("beam", beam, hi=Decimal("3"))
        c = _term("ceiling", ceiling, hi=Decimal("1"))
        S_lo, S_hi = a - t - f, b - t - f
        H_lo, H_hi = a - bm - c - f, b - bm - c - f
        if H_lo <= 0 or S_lo <= 0:
            raise RuleError(f"finish height <= 0 (H_lo {H_lo}, S_lo {S_lo}): refused")
        return {"S": (q(S_lo), q(S_hi)), "H": (q(H_lo), q(H_hi))}


# ------------------------------------------------------------------ R-T686-2

def opening_portion(op, H, S_):
    """(low, high) m2 of one opening inside the band [0, H]; S_ = plaster soffit height at the same datum."""
    with ctx40():
        if not op.get("exists", True):
            raise RuleError(f"opening {op.get('id')}: not physically built (Q-73): never deducted")
        w = _term(f"{op['id']} width", (op["width"], op["source"]), hi=Decimal("20"))
        H, S_ = D(H), D(S_)
        if S_ < H:
            raise RuleError("soffit below the paint / tile top: refused")
        if op.get("head") is not None:
            sill = D(op.get("sill") or 0)
            head = _term(f"{op['id']} head", (op["head"], op["source"]))
            if head <= sill:
                raise RuleError(f"opening {op['id']}: head {head} <= sill {sill}: refused")
            if head > S_:
                raise RuleError(f"opening {op['id']}: head {head} above the soffit {S_}: data error, refused")
            v = w * max(Decimal(0), min(head, H) - max(sill, Decimal(0)))
            return q(v), q(v)
        if op.get("height") is not None:
            h = _term(f"{op['id']} height", (op["height"], op["source"]))
            if h > S_:
                raise RuleError(f"opening {op['id']}: height {h} > soffit height {S_}: refused")
            return q(w * max(Decimal(0), h - (S_ - H))), q(w * min(h, H))
        cap = D(op.get("cap_h")) if op.get("cap_h") is not None else H
        return Decimal("0").quantize(Q6), q(w * min(cap, H))


def band_bound(length, Hs, Ss, openings, finish, face_finish="PLASTER_OR_PAINT"):
    """(low, high) of length x H - openings, H in Hs = (lo, hi), soffit Ss = (lo, hi) at the same datum ends."""
    if finish == "PAINT" and face_finish == "TILED":
        raise RuleError("paint on a tiled face refused (wet-area rule 2026-11-02: no paint on tiled faces)")
    with ctx40():
        L = _term("length", length, hi=Decimal("500"))
        (H_lo, H_hi), (S_lo, S_hi) = (D(Hs[0]), D(Hs[1])), (D(Ss[0]), D(Ss[1]))
        if H_lo > H_hi:
            raise RuleError("height bound low > high: refused")
        used = sum((D(o["width"]) for o in openings), Decimal(0))
        if used > L:
            raise RuleError(f"openings wider than the faces ({used} > {L}): refused")
        ded_hi_at_lo = sum((opening_portion(o, H_lo, S_lo)[1] for o in openings), Decimal(0))
        ded_lo_at_hi = sum((opening_portion(o, H_hi, S_hi)[0] for o in openings), Decimal(0))
        low, high = L * H_lo - ded_hi_at_lo, L * H_hi - ded_lo_at_hi
        if low <= 0:
            raise RuleError(f"bound low {low} <= 0: refused (held is never 0)")
        if low > high:
            raise RuleError(f"bound {low} > {high}: refused")
        return {"low": S(q(low)), "high": S(q(high)), "gross": [S(q(L * H_lo)), S(q(L * H_hi))],
                "deducted_at_low": S(q(ded_hi_at_lo)), "deducted_at_high": S(q(ded_lo_at_hi))}


# ------------------------------------------------------------------ R-T686-3

def wet_room_tile_top(heads, g1_ceiling_abs, ffl_options):
    """bound of the tile-backing render top above the FFL: low = the highest established head (over every floor
    option), high = G1 ceiling (absolute) - the lowest floor option. heads: [(value, source)]; none -> HELD."""
    if not heads:
        raise RuleError("no established opening head in the room: no lower bound, HELD by name")
    with ctx40():
        hs = [_term("head", h, hi=Decimal("10")) for h in heads]
        g1 = _term("G1 ceiling (absolute)", g1_ceiling_abs)
        ffls = [_term("FFL option", f, lo=Decimal("-10")) for f in ffl_options]
        if not ffls:
            raise RuleError("no floor level option: HELD")
        lo, hi = max(hs), g1 - min(ffls)
        if g1 - max(ffls) < lo:
            raise RuleError(f"G1 ceiling above the highest floor option ({g1 - max(ffls)}) is below the head {lo}: "
                            "refused (a data error, not a bound)")
        return q(lo), q(hi)


# ------------------------------------------------------------------ R-T686-4

def governing_height(records):
    """records: dicts {id, kind VECTOR / RASTER, sill, head, tol}. Returns (governing record, residuals)."""
    vec = [r for r in records if r.get("kind") == "VECTOR"]
    ras = [r for r in records if r.get("kind") == "RASTER"]
    if not vec:
        raise RuleError("no vector record: a raster is never scaled into a quantity; HELD")
    g = vec[0]
    for r in vec[1:]:
        tol = max(D(g.get("tol") or 0), D(r.get("tol") or 0))
        if abs(D(r["head"]) - D(g["head"])) > tol or abs(D(r["sill"]) - D(g["sill"])) > tol:
            raise RuleError("two vector records disagree beyond tolerance: HELD")
    res = []
    for r in ras:
        dv = (D(r["head"]) - D(r["sill"])) - (D(g["head"]) - D(g["sill"]))
        res.append({"id": r.get("id"), "height_difference_m": S(q(dv)), "governs": False})
    return g, res
