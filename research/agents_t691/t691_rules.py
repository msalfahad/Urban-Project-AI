"""R-T691-1 / -2 / -3: WATERPROOFING ROUND 2 (every villa; research provenance, proposed; nothing wired or released).

R-T691-1 CIRCULAR OPENING IN A MEMBRANE AREA. A dome, skylight or round shaft drawn as a CIRCLE (or ARC) that the
  membrane stops at (owner Q-24: 'the circle dome ... add 20cm upturn around circle', Q-29) is deducted at its TRUE
  area pi r^2 and its upturn ring is its TRUE circumference 2 pi r. A chord polygon is a drafting / computing device,
  not the physical edge: an INSCRIBED n-chord polygon (area n/2 r^2 sin(2 pi / n)) under-deducts every circle by
  pi r^2 - n/2 r^2 sin(2 pi / n) (about 4/3 pi r s for chord sagitta s), so the net membrane is OVER-stated by that
  much per opening, and the ring is SHORT by 2 pi r - 2 n r sin(pi / n). Where a polygon is kept, the residual is
  added back and named; it is never left inside a released number.

R-T691-2 RELEASED VALUE INSIDE ITS OWN EVIDENCE. A released quantity must lie inside the band its own measurement
  establishes (low .. high, same physical element, same basis); a value outside the band by more than its rounding
  half-step is a defect: the excess is reconciled to named physical / mathematical causes in the line's unit and the
  corrected figure is the same-basis measure. A finish hatch is NOT the membrane outline: the membrane runs to the
  wall / parapet face where it turns up; a hatch drawn on the parapet line adds nothing (it coincides with the face),
  and a hatch larger than the face outline is flagged (it cannot hold more membrane than the face encloses).
  A band term the drawing leaves open (a D-band of unprinted meaning between the wall face and the hatch edge) stays a
  named range: neither end is chosen because it is larger, more conservative or closer to another figure.

R-T691-3 FLOOR PENETRATIONS PER WET ROOM (UP-WP-004 1.1.0 'counted from the drawings'; R-T685-3 refined).
  A floor penetration is a pipe or drain body passing through the waterproofed floor plane inside the room.
    low  = the floor drains printed inside the room on the drainage plan (each body passes the membrane: firm);
    high = low + the W.C. pans drawn inside the room (a pan's soil outlet leaves through the floor unless a wall
           outlet is specified; no wet-room / W.C. detail is printed, so it is the open term);
  a basin or shower waste drawn into the floor drain (waste line to the FD) adds nothing: it enters through the drain
  body already counted; a soil / waste stack drawn inside a wall or at high level is not a floor penetration.
  Twin rooms on one drainage cell pair are mapped by GEOMETRY (cell position from the plan) before per-cell counts are
  assigned; unmapped cells keep AT LEAST 1 each. No drainage plan read -> HELD (never 0); low never below 1 when a
  drain is printed; units are pcs and never mixed with m2 / lm.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

Q6 = Decimal("0.000001")


class RuleError(Exception):
    pass


def _d(x):
    return Decimal(str(x))


def _q(x):
    return _d(x).quantize(Q6, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------- R-T691-1
def chords_for_sagitta(r_m, sag_m):
    """the number of equal chords a 'sagitta <= sag' flattening gives a full circle (the engine EXTERIOR_SPACES_V1
    _arc_pts convention: step = 2 acos(1 - s / r), n = ceil(2 pi / step))."""
    if r_m <= 0 or sag_m <= 0:
        raise RuleError("radius and sagitta must be positive")
    if r_m <= sag_m:
        return 2
    step = 2 * math.acos(1 - sag_m / r_m)
    return max(3, int(math.ceil(2 * math.pi / step)))


def circle_true(r_m):
    if r_m <= 0:
        raise RuleError("radius must be positive")
    if r_m > 50:
        raise RuleError("radius above 50 m: a unit error (mm read as m)")
    return {"area_m2": math.pi * r_m * r_m, "ring_m": 2 * math.pi * r_m}


def circle_inscribed(r_m, n):
    if n < 3:
        raise RuleError("a polygon needs at least 3 chords")
    return {"area_m2": n / 2 * r_m * r_m * math.sin(2 * math.pi / n), "ring_m": 2 * n * r_m * math.sin(math.pi / n)}


def chord_residual(r_m, n):
    """true minus inscribed: what an n-chord hole leaves IN the net area (m2) and OUT of the ring (m)."""
    t, p = circle_true(r_m), circle_inscribed(r_m, n)
    return {"area_m2": t["area_m2"] - p["area_m2"], "ring_m": t["ring_m"] - p["ring_m"], "n": n}


def membrane_net(face_outline_m2, circles_r_m):
    """R-T691-1: membrane net = face outline (to the wall / parapet faces, circles NOT cut) - sum pi r^2."""
    if face_outline_m2 is None:
        raise RuleError("face outline not measured: HELD, never 0")
    holes = sum(circle_true(r)["area_m2"] for r in circles_r_m)
    if holes >= face_outline_m2:
        raise RuleError("openings larger than the face: not a membrane face")
    return face_outline_m2 - holes


# ---------------------------------------------------------------------------------------------------- R-T691-2
def roof_band(face_outline_m2, circles_r_m, open_band_m2=0.0, hatch_m2=None, hatch_on_face_line=False):
    """membrane band of one roof face: high = to the wall / parapet faces; low = high - a drawn band of unprinted
    meaning (open_band_m2). The finish hatch is a check only: it never enters the membrane value."""
    if open_band_m2 < 0:
        raise RuleError("an open band is a width x length, never negative")
    high = membrane_net(face_outline_m2, circles_r_m)
    low = high - open_band_m2
    flags = []
    if hatch_m2 is not None:
        net_hatch_cap = high + 1e-6
        if hatch_m2 > net_hatch_cap:
            flags.append("HATCH_EXCEEDS_FACE: the finish hatch encloses more than the wall-face outline")
        if hatch_on_face_line:
            flags.append("HATCH_ON_FACE_LINE: coincides with the parapet face; adds 0 to the membrane")
    return {"low_m2": _q(low), "high_m2": _q(high), "status": "MEASURED" if open_band_m2 == 0 else "OPEN_BOUND",
            "flags": flags}


def check_inside_band(released, low, high, causes, unit="m2", half_step=Decimal("0.0005")):
    """R-T691-2: is a released value inside its own band? causes: [(name, signed amount)] that explain the excess
    over the nearest band end; the residual left after the named causes is returned (it must be within rounding)."""
    if released is None:
        raise RuleError("a HELD line is not a released value (never 0)")
    rel, lo, hi = _d(released), _d(low), _d(high)
    if lo > hi:
        raise RuleError("band low above high")
    if lo - half_step <= rel <= hi + half_step:
        return {"inside": True, "excess": "0", "residual": "0", "causes": [], "unit": unit}
    end = hi if rel > hi else lo
    excess = rel - end
    named = sum((_d(a) for _n, a in causes), Decimal("0"))
    residual = excess - named
    return {"inside": False, "excess": str(_q(excess)), "named": str(_q(named)), "residual": str(_q(residual)),
            "residual_within_rounding": abs(residual) <= half_step, "causes": [(n, str(_q(a))) for n, a in causes],
            "unit": unit}


# ---------------------------------------------------------------------------------------------------- R-T691-3
def penetration_bound(room):
    """room: {"drainage_read": bool, "fd": int | None, "wc": int, "mapped": bool, "pair_min": int}.
    Returns low / high pcs (low firm) or HELD."""
    if not room.get("drainage_read"):
        return {"status": "HELD", "low": None, "high": None, "why": "drainage plan not read: never 0"}
    fd = room.get("fd")
    wc = int(room.get("wc") or 0)
    if wc < 0 or (fd is not None and fd < 0):
        raise RuleError("a count is never negative")
    if fd is None or fd == 0:
        return {"status": "HELD", "low": None, "high": None,
                "why": "no drain printed in the room: the penetration count is not drawn (never 0)"}
    if not room.get("mapped", True):
        fd = room.get("pair_min", 1)              # unmapped twin cell: AT LEAST 1, high unknown
        return {"status": "OPEN_BOUND", "low": fd, "high": None, "why": "twin cell not mapped: AT LEAST"}
    high = fd + wc
    return {"status": "MEASURED" if high == fd else "OPEN_BOUND", "low": fd, "high": high,
            "why": "" if high == fd else f"{wc} W.C. pan outlet(s): floor or wall outlet not printed"}


def map_twin_cells(cells, disc_overlaps):
    """map two geometrically identical cells to engine room ids by a measured discriminator: cells {cell: overlap
    measured on the drawing (m2)}, disc_overlaps {room_id: overlap printed by an earlier merged ledger (m2)}.
    Each cell takes the room whose overlap is nearest; ambiguity (two rooms within 0.01 m2) raises."""
    if len(cells) != len(disc_overlaps):
        raise RuleError("cell and room counts differ")
    out, used = {}, set()
    for cell, a in sorted(cells.items()):
        ranked = sorted(disc_overlaps.items(), key=lambda kv: abs(kv[1] - a))
        if len(ranked) > 1 and abs(abs(ranked[0][1] - a) - abs(ranked[1][1] - a)) < 0.01:
            raise RuleError(f"{cell}: overlap {a} does not separate the rooms")
        rid = ranked[0][0]
        if rid in used:
            raise RuleError(f"{rid} mapped twice")
        used.add(rid)
        out[cell] = rid
    return out
