"""T-690 rules (research, unwired; every villa; no project value in this module).

R-T690-1 WET-ROOM WALL BAND ABOVE THE FINISHED CEILING (provenance F-T686-1, Checker 2026-11-10; register ruling Lead
2026-11-11 00:20 'plaster owns the band').
  (a) PHYSICAL ELEMENT: the wall face of a wet room between the wall-tile top H (= the finished ceiling, owner Q-48 A)
      and the plaster top S (the soffit of the structural slab / roof over the room, owner 2026-11-02 / Q-72, height by
      R-T556-1). It is hidden above the closed false ceiling. Owner trade: plaster (FIN.PLASTER) as its OWN component
      line per room; never folded into the tile-backing levelling render line (a different coat, tiler, already
      measured to H), never wall tile (tile stops at H), never paint (no paint above a closed ceiling unless a drawing
      says so).
  (b) QUANTITY at one datum: band = length x (S - H) - openings inside [H, S] - beam end sections inside [H, S].
      An opening with sill and head takes w x max(0, min(head, S) - max(sill, H)) (exact); an opening whose height or
      position is not established takes (0, min(cap, w x (S - H))) where cap is its largest possible hole area; a beam
      crossing the room takes ends x b x min(h - slab, S - H) with ends 2 in a closed room, (0, 2) in an open-sided one.
  (c) DATUMS: S and H that hang on ONE unestablished datum (an annex slab top, an undrawn floor level) are evaluated
      together, point by point over that datum (millimetre grid including every breakpoint): the band bound is the
      min / max over those points, never the difference of independent extremes. Independent segments (a face part
      under a floor slab and a part under a roof) add their own bounds.
  (d) JOINT TOTAL: where the backing / plaster line below H is itself bounded on the same datum, the room's total
      plaster (line + band) is reported as one joint bound (length x S - openings below S); the sum of the two separate
      bounds is never carried as a figure (it pairs a high H with a low H).
  (e) REFUSED / HELD: S below H by more than the tolerance (a tile top above the soffit: data conflict); a level that
      looks like millimetres; a non-positive length; a missing S or H (HELD, never 0); a low bound below 0. S equal to
      H gives a band of 0 that is CALCULATED, not missing.

R-T690-2 CENSUS RESTATEMENT. A census made on one candidate stands on a later candidate only when every line of its
filter is byte-identical in both (same ids, same fields); otherwise it is rebuilt. The restated census keeps the count
by line id (no line missing, none twice).

R-T690-3 WIRING GAP. A candidate HELD line that a merged record settles as EXCLUDED (not applicable) is closed only
when no other candidate line carries the same physical stretch (the neighbouring lines' terms are checked); its beside
figure is removed, never moved into a neighbour.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

TOL = Decimal("0.005")
MAX_LEVEL_M = Decimal(60)
Q6 = Decimal("0.000001")


class RuleError(ValueError):
    pass


class Held(RuleError):
    """a term is not established: the quantity stays HELD by name (never 0)."""


def D(x):
    if x is None:
        raise Held("value not established: HELD, never 0")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def q(x):
    return D(x).quantize(Q6, rounding=ROUND_HALF_UP)


def S6(x):
    return None if x is None else format(q(x).normalize(), "f")


def level(x, name):
    v = D(x) if x is not None else None
    if v is None:
        raise Held(f"{name} not established: the band stays HELD (never 0)")
    if abs(v) > MAX_LEVEL_M:
        raise RuleError(f"{name} {v} looks like millimetres, not metres: refused")
    return v


def opening_in_band(op, S, H):
    """(low, high) m2 of one opening inside [H, S]."""
    w = D(op["width"])
    if w <= 0:
        raise RuleError(f"opening {op.get('id')}: width not positive")
    band = S - H
    if op.get("head") is not None:
        sill = level(op.get("sill", 0), f"{op['id']} sill")
        head = level(op["head"], f"{op['id']} head")
        if head <= sill:
            raise RuleError(f"opening {op['id']}: head {head} not above sill {sill}")
        if head > S + TOL:
            raise RuleError(f"opening {op['id']}: head {head} above the soffit {S}: data conflict, refused")
        v = w * max(Decimal(0), min(head, S) - max(sill, H))
        return v, v
    cap = D(op["cap_m2"]) if op.get("cap_m2") is not None else w * band
    return Decimal(0), min(cap, w * band)


def beam_in_band(bm, S, H):
    b, h, slab = D(bm["b"]), D(bm["h"]), D(bm["slab"])
    if h <= slab:
        raise RuleError(f"beam {bm['id']}: depth {h} not below the slab {slab}")
    e_lo, e_hi = bm["ends"]
    if not (0 <= e_lo <= e_hi <= 2):
        raise RuleError(f"beam {bm['id']}: ends {bm['ends']} refused (0 .. 2)")
    p = b * min(h - slab, S - H)
    return e_lo * p, e_hi * p


def band_at(length, S, H, openings=(), beams=()):
    """R-T690-1 (b) at one datum point -> (low, high, gross)."""
    L = D(length)
    if L <= 0:
        raise RuleError("face length missing or not positive")
    S, H = level(S, "plaster top S"), level(H, "tile top H")
    if S < H - TOL:
        raise RuleError(f"tile top H {H} above the soffit S {S}: data conflict, refused")
    S = max(S, H)
    gross = L * (S - H)
    ded_lo = ded_hi = Decimal(0)
    for op in openings:
        a, b = opening_in_band(op, S, H)
        ded_lo, ded_hi = ded_lo + a, ded_hi + b
    for bm in beams:
        a, b = beam_in_band(bm, S, H)
        ded_lo, ded_hi = ded_lo + a, ded_hi + b
    lo, hi = gross - ded_hi, gross - ded_lo
    if lo < 0:
        raise RuleError(f"band low {lo} < 0: deductions exceed the band, refused")
    return lo, hi, gross


def datum_grid(lo, hi, step="0.001"):
    a, b, s = D(lo), D(hi), D(step)
    if a > b:
        raise RuleError(f"datum bound {a} > {b}: refused")
    out, x = [], a
    while x < b:
        out.append(x)
        x += s
    out.append(b)
    return out


def band_over_points(length, points, openings=(), beams=()):
    """R-T690-1 (c): points = [(S, H)] on one datum -> dict low / high (min / max over the points)."""
    if not points:
        raise Held("no datum point: HELD")
    res = [band_at(length, s, h, openings, beams) for s, h in points]
    return {"low": min(r[0] for r in res), "high": max(r[1] for r in res),
            "gross": (min(r[2] for r in res), max(r[2] for r in res))}


def room_band(segments, openings=(), beams=()):
    """independent segments [(length, points)] add; openings / beams are taken once on the room at the widest and the
    narrowest band height of its segments (bounds, never a split guess)."""
    if not segments:
        raise Held("no face segment")
    lo = hi = Decimal(0)
    pts_all = []
    for length, pts in segments:
        r = band_over_points(length, pts)
        lo, hi = lo + r["low"], hi + r["high"]
        pts_all += [(max(level(s, "S"), level(h, "H")), level(h, "H")) for s, h in pts]
    ded_lo = ded_hi = Decimal(0)
    for item in list(openings) + list(beams):
        f = opening_in_band if "width" in item else beam_in_band
        vals = [f(item, s, h) for s, h in pts_all]
        ded_lo, ded_hi = ded_lo + min(v[0] for v in vals), ded_hi + max(v[1] for v in vals)
    if lo - ded_hi < 0:
        raise RuleError("room band low < 0: refused")
    return {"low": lo - ded_hi, "high": hi - ded_lo, "deducted": (ded_lo, ded_hi)}


def joint_total(length, points, openings_full):
    """R-T690-1 (d): total plaster face to S (line below H + band) per datum point: length x S - openings below S."""
    vals_lo, vals_hi = [], []
    for s, h in points:
        s = level(s, "S")
        ded_lo = ded_hi = Decimal(0)
        for op in openings_full:
            w = D(op["width"])
            if op.get("head") is not None:
                v = w * (min(D(op["head"]), s) - D(op.get("sill", 0)))
                ded_lo, ded_hi = ded_lo + v, ded_hi + v
            else:
                ded_hi += min(D(op["cap_m2"]), w * s) if op.get("cap_m2") is not None else w * s
        g = D(length) * s
        vals_lo.append(g - ded_hi)
        vals_hi.append(g - ded_lo)
    return min(vals_lo), max(vals_hi)


def census_restated(old_lines, new_lines, in_scope):
    """R-T690-2: True when every in-scope line is identical in both candidates; raises otherwise."""
    a = {l["line_id"]: l for l in old_lines if in_scope(l["item_code"])}
    b = {l["line_id"]: l for l in new_lines if in_scope(l["item_code"])}
    if set(a) != set(b):
        raise RuleError(f"filter differs: {len(set(a) ^ set(b))} line ids added / removed: rebuild the census")
    diff = [k for k in a if a[k] != b[k]]
    if diff:
        raise RuleError(f"{len(diff)} in-scope lines changed: rebuild the census")
    return True


def wiring_gap_close(line, settled_class, neighbours):
    """R-T690-3: neighbours = [(line, carries_stretch: bool, why)]; returns the closing record."""
    if settled_class not in ("EXCLUDED",):
        raise RuleError(f"settled class {settled_class!r}: only an EXCLUDED settlement is closed here")
    if line["class"] != "HELD":
        raise RuleError("the candidate line is not HELD: nothing to close")
    carriers = [n for n in neighbours if n[1]]
    if carriers:
        raise RuleError(f"stretch carried by {[n[0]['line_id'] for n in carriers]}: double count, refused")
    return {"line_id": line["line_id"], "before": "HELD blank", "after": "EXCLUDED (NOT_APPLICABLE)",
            "checked": [{"line_id": n[0]["line_id"], "why": n[2]} for n in neighbours]}
