"""T-600 rules (research, unwired): the column / beam PAIR RESIDUAL of a storey reconciled to physical causes by column
mark and by beam mark, for any villa.

Context. Under UP-CONC-JOINT-001 1.0.0 (rules/conventions/URBAN_CONVENTIONS_1.0.0.json, LEAD_ADOPTED) the column line
owns every column-beam joint; a reference that lets the BEAM own it (beam lengths through the supports, columns to the
beam soffit) shows two convention terms per storey: the beam THROUGH_SUPPORT T (his beam volume beyond the engine's
face-to-face runs, per beam mark) and the column JOINT_HEAD J (sum of A x D_ctrl over the compared column set). T-599
matched J inside T; the pair residual R = T - J is not a convention and needs a cause.

R-T600-1 PAIR RESIDUAL BY ZONE. Per storey, exactly (Decimal, 6 dp):
      T = sum over beam marks m of ( Z_m - SHORT_m )
          Z_m      = volume of the drawn support zones his mark can run through: for every support the mark's pieces
                     meet, the strip of the beam (its drawn lateral band) across the support's drawn extent along the
                     beam axis, x his b x D (b x D = the printed section: SECTION agrees on every common mark);
                     carrier-beam crossings at the carrier's drawn width;
          SHORT_m  = Z_m - T_m, his row length NOT carried through every zone (positive: his rows stop inside the
                     support set; which support is not printed, so never apportioned); negative = his length beyond
                     every drawn zone (BEYOND), split off as its own term, never hidden in a zone.
      Per support column k with zones z_i (plan polygon, depth D_i) of the beams that reach it:
          sum_i z_i x D_i = UNION_k + OVERLAP_k + BESIDE_k
          UNION_k   = volume of the union of the zones inside the column outline (layered by depth): what his beam
                      rows bill of the column's head when every row runs through;
          OVERLAP_k = the part two of his rows bill twice inside one column (CROSSING: beams on two axes; REPEAT: two
                      zones on the same axis);
          BESIDE_k  = strip volume outside the column outline (beam wider than the column, or offset).
      For a column of the compared set (in J):  zones - J_k = OVERLAP_k + BESIDE_k - UNCOVERED_k,
          UNCOVERED_k = J_k - UNION_k: the column head (A x D_ctrl) under none of his beam strips, which his column
          rows (stopping at one soffit depth) also leave out.
      For a support outside the compared set (D_ctrl open, held line, no column line, carried member, beam carrier)
      the whole zone volume is its own term (OUTSIDE_SET by kind): the joint is real concrete, billed by a line J
      does not contain (or by the carrier beam); a HELD partner stays HELD, never 0.
      R = sum(OVERLAP + BESIDE - UNCOVERED over the set) + sum(zones outside the set) + carrier crossings
          - sum(SHORT) - sum(BEYOND) (BEYOND already negative SHORT). Every term is printed by column mark / beam mark
      and re-adds exactly to R; a remainder that is not one of these terms is UNRESOLVED by name.
R-T600-2 SUPPORT ZONE FROM THE DRAWING. A zone is read from the drawn outline and the drawn band, never from a
      schedule extent or a 'max(w, d)' guess: the support's extent ALONG the beam axis; a member the beam CARRIES (a
      planted / turned column that starts on the beam) is not a support and the beam line bills under it (T-229): its
      footprint is not a zone; where a piece ends at a carried member only, the support is the first real column
      outline the drawn band reaches beyond it. An oblique band (axis neither X nor Y within 1:5) is measured the same
      way in its own axis frame (strip across the outline's projection on the beam axis), labelled OBLIQUE.
R-T600-3 READINGS OF THE COMPARED SET. Where two comparisons used different column sets (CONFLICT readings, D_ctrl
      open members), their J differ by whole members: each difference is printed per column mark as A x D_ctrl (or
      A x D_low where only the printed lower depth is known, labelled LOWER_BOUND), never chosen by majority and never
      netted; the physical joint does not depend on the set, only the label does.

Provenance: T-600 (2026-11-07), on UP-CONC-JOINT-001 1.0.0 (T-599), R-T395-4 (allowance), T-229 (carried members),
T-551 / T-572 / T-576 (column readings), T-545 (beam marks), F-C-P02-1 (2F footprint vs un-rowed run). Scope: every
villa. Status: PROPOSED (research; no line, rule register or method version changes).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from shapely.geometry import box
from shapely.ops import unary_union

Q6 = Decimal("0.000001")
TOL_M = Decimal("0.01")          # R-T395-4 drawn-edge fit tolerance on a support allowance (m)
TERM_CLASSES = ("OVERLAP_CROSSING", "OVERLAP_REPEAT", "BESIDE", "UNCOVERED", "OUTSIDE_SET_OPEN", "OUTSIDE_SET_HELD",
                "OUTSIDE_SET_NOLINE", "CARRIER_CROSSING", "SHORT", "BEYOND", "UNRESOLVED")


class Refused(ValueError):
    """An input or a split the rule refuses."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("a missing value is HELD, never 0")
    if isinstance(x, str) and x.strip().endswith("%"):
        raise Refused("a percentage is not a quantity")
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_UP)


def _metres(v, what):
    v = Decimal(str(v))
    if v < 0:
        raise Refused(f"negative {what}")
    if v > 50:
        raise Refused(f"{what} {v} looks like mm: give metres")
    return v


# ------------------------------------------------------------------------------------------------- R-T600-2 geometry
def axis_of(pts):
    """'X' / 'Y' / 'OBLIQUE' from the longest edge of a band polygon (1:5 test)."""
    best, n = None, len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        if best is None or L > best[0]:
            best = (L, abs(b[0] - a[0]), abs(b[1] - a[1]))
    _, dx, dy = best
    return "X" if dx > 5 * dy else "Y" if dy > 5 * dx else "OBLIQUE"


def direction_of(pts):
    """Unit vector of the longest edge of a band polygon (the beam axis), sign normalised (x > 0, or y > 0)."""
    import math
    best, n = None, len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.dist(a, b)
        if best is None or L > best[0]:
            best = (L, b[0] - a[0], b[1] - a[1])
    L, dx, dy = best
    if L <= 0:
        raise Refused("degenerate band")
    ux, uy = dx / L, dy / L
    if ux < -1e-12 or (abs(ux) <= 1e-12 and uy < 0):
        ux, uy = -ux, -uy
    return ux, uy


def strip_zone(band_pts, col_rect, u=None, axis=None):
    """The beam strip across a column: the band's lateral range x the column's range along the beam axis u (unit
    vector; 'X' / 'Y' accepted as axis). col_rect = (xmin, ymin, xmax, ymax) in metres.
    Returns (inside polygon, beside polygon, along extent m)."""
    from shapely.geometry import Polygon
    if u is None:
        if axis == "X":
            u = (1.0, 0.0)
        elif axis == "Y":
            u = (0.0, 1.0)
        else:
            raise Refused("give the beam axis")
    x0, y0, x1, y1 = col_rect
    if x1 <= x0 or y1 <= y0:
        raise Refused("empty column outline")
    ux, uy = u
    vx, vy = -uy, ux
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    su = [cx * ux + cy * uy for cx, cy in corners]
    sv = [px * vx + py * vy for px, py in band_pts]
    a0, a1, b0, b1 = min(su), max(su), min(sv), max(sv)
    pts = [(a * ux + b * vx, a * uy + b * vy) for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]
    strip = Polygon(pts)
    col = box(x0, y0, x1, y1)
    return strip.intersection(col), strip.difference(col), a1 - a0


def zone_m3(z):
    """(inside m3, beside m3) of one zone, each rounded to 6 dp once: every total is a sum of these."""
    return (d6(Decimal(repr(z["poly"].area)) * Decimal(str(z["D"]))),
            d6(Decimal(repr(z["beside"].area)) * Decimal(str(z["D"]))))


def column_zone_terms(zones, *, col_rect, joint=None):
    """zones = [{'poly': inside polygon, 'beside': polygon, 'D': m, 'axis': 'X'|'Y'|'OBLIQUE', 'key': str}] at one column.
    joint = A x D_ctrl (m3) for a column of the compared set, else None.
    Returns Decimal terms: ZONES (sum z x D incl. beside), UNION, OVERLAP_CROSSING, OVERLAP_REPEAT, BESIDE,
    UNCOVERED (only with a joint); ZONES = UNION + OVERLAP_* + BESIDE exactly (6 dp, remainder refused)."""
    keys = [z["key"] for z in zones]
    if len(keys) != len(set(keys)):
        raise Refused("one zone entered twice at a column (a cause counted twice)")
    for z in zones:
        _metres(z["D"], "depth")
    col = box(*col_rect)
    tot_in = sum((zone_m3(z)[0] for z in zones), Decimal(0))
    beside = sum((zone_m3(z)[1] for z in zones), Decimal(0))
    depths = sorted({Decimal(str(z["D"])) for z in zones})
    union = Decimal(0)
    prev = Decimal(0)
    for d in depths:                               # layer [prev, d): union of the zones at least d deep
        u = unary_union([z["poly"] for z in zones if Decimal(str(z["D"])) >= d]).intersection(col)
        union += Decimal(repr(u.area)) * (d - prev)
        prev = d
    # same-axis (REPEAT) overlap = union per axis vs sum per axis; the rest of the overlap is CROSSING
    rep = Decimal(0)
    for ax in sorted({z["axis"] for z in zones}):
        zz = [z for z in zones if z["axis"] == ax]
        if len(zz) < 2:
            continue
        s = sum((zone_m3(z)[0] for z in zz), Decimal(0))
        ds = sorted({Decimal(str(z["D"])) for z in zz})
        u_ax, pv = Decimal(0), Decimal(0)
        for d in ds:
            u = unary_union([z["poly"] for z in zz if Decimal(str(z["D"])) >= d])
            u_ax += Decimal(repr(u.area)) * (d - pv)
            pv = d
        rep += s - d6(u_ax)
    union = d6(union)
    out = {"ZONES": tot_in + beside, "UNION": union, "OVERLAP_REPEAT": rep,
           "OVERLAP_CROSSING": tot_in - union - rep, "BESIDE": beside}
    if joint is not None:
        out["JOINT"] = d6(joint)
        out["UNCOVERED"] = d6(joint) - out["UNION"]
    gap = out["ZONES"] - (out["UNION"] + out["OVERLAP_REPEAT"] + out["OVERLAP_CROSSING"] + out["BESIDE"])
    if abs(gap) > Decimal("0.000002"):
        raise Refused(f"column zone terms do not re-add ({gap})")
    if gap:
        out["BESIDE"] += gap                       # 6-dp bookkeeping on the smallest term, |gap| <= 2e-6
    return out


# ------------------------------------------------------------------------------------------------- R-T600-1 closure
def mark_short(zone_m3, through_m3):
    """Per beam mark: T_m (positive m3 of his length beyond the engine) against its zone volume Z_m.
    Returns {'SHORT': >= 0} or {'BEYOND': < 0}; within the 1 cm drawn-edge tolerance x b x D the remainder is
    still printed (EDGE) and never dropped."""
    z, t = d6(zone_m3), d6(through_m3)
    if t < 0:
        raise Refused("give his through-support volume as a positive m3")
    s = z - t
    return {"SHORT": s} if s >= 0 else {"BEYOND": s}


def pair_closure(residual, terms):
    """terms = [(class, key, m3)]; class in TERM_CLASSES; key = column / beam mark. The terms must re-add exactly to
    the storey residual (6 dp); a (class, key) twice is refused; None (missing) is refused, never 0."""
    seen = set()
    tot = Decimal(0)
    by = {}
    for cls, key, v in terms:
        if cls not in TERM_CLASSES:
            raise Refused(f"unknown term class {cls}")
        if (cls, key) in seen:
            raise Refused(f"cause counted twice: {cls} {key}")
        seen.add((cls, key))
        x = d6(v)
        tot += x
        by[cls] = by.get(cls, Decimal(0)) + x
    if tot != d6(residual):
        raise Refused(f"terms {tot} do not re-add to the residual {d6(residual)}")
    return {k: str(v) for k, v in sorted(by.items())}


def held_term(v):
    """A support zone whose column partner is HELD keeps its m3; 0 / None refused."""
    if v is None or d6(v) == 0:
        raise Refused("a HELD partner's zone shown as 0 or missing")
    return d6(v)


# ------------------------------------------------------------------------------------------------- R-T600-3 readings
def reading_differences(record, other):
    """record / other: {column key: joint m3} of two compared sets. Returns per-member signed differences (other -
    record), each member once; the totals must re-add."""
    out = {}
    for k in sorted(set(record) | set(other)):
        a, b = record.get(k), other.get(k)
        if a is not None and b is not None and d6(a) != d6(b):
            raise Refused(f"{k}: one member with two joint values: a geometry difference, not a set difference")
        if (a is None) != (b is None):
            out[k] = d6(b) if a is None else -d6(a)
    diff = sum((d6(v) for v in other.values()), Decimal(0)) - sum((d6(v) for v in record.values()), Decimal(0))
    if sum(out.values(), Decimal(0)) != diff:
        raise Refused("reading differences do not re-add")
    return out
