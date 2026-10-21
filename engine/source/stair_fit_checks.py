"""STAIR FIT CHECKS - whether a riser arrangement fits its plan and section: run ends, clearances to a beam band,
the most risers a plan length admits, the going a length needs, the level at every transition, and headroom (generic).

Nothing here chooses an arrangement. Every function takes the geometry it is given and says what follows; whether a
dimension is drawn, printed or proposed is the caller's record. Lengths and levels in mm.

Plan
    run_end(first_riser, n_risers, going, direction)
        the last riser line of a straight flight: first + direction x (n - 1) x going (direction +1 / -1 along the
        walking axis).
    band_clearance(last_riser, band, direction)
        the clear distance from the last riser line to the near face of a band ahead of it (lo, hi along the axis);
        negative when the riser lies inside or beyond the near face.
    max_risers(length, going)
        the most risers a straight flight holds when its first and last riser lines must lie within `length`.
    going_to_fit(length, n_risers)
        the going that fits n risers exactly into `length` (first to last riser line).

Section
    transition_levels(bottom, top, segments)
        segments [(name, kind, n)] in walking order (kind FLIGHT / WINDERS / LANDING, a landing has no riser); equal
        finished risers between two levels. Returns, for every segment, the level it starts and ends at and its
        risers, and the riser height.
    headroom(beam_top, beam_depth, tread_level)
        the clear height from a tread to the soffit of a member above it.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-9
FLIGHT, WINDERS, LANDING = "FLIGHT", "WINDERS", "LANDING"


class FitCheckError(ValueError):
    pass


def run_end(first_riser, n_risers, going, direction):
    if n_risers < 1 or int(n_risers) != n_risers:
        raise FitCheckError("risers must be a whole number")
    if going <= 0 or direction not in (1, -1):
        raise FitCheckError("going positive, direction +1 or -1")
    return first_riser + direction * (n_risers - 1) * going


def band_clearance(last_riser, band, direction):
    lo, hi = sorted(band)
    near = lo if direction > 0 else hi
    return direction * (near - last_riser)


def max_risers(length, going):
    if length < 0 or going <= 0:
        raise FitCheckError("length not negative, going positive")
    return int(math.floor(length / going + TOL)) + 1


def going_to_fit(length, n_risers):
    if n_risers < 2:
        raise FitCheckError("a flight needs at least two risers to have a going")
    if length <= 0:
        raise FitCheckError("length must be positive")
    return length / (n_risers - 1)


def transition_levels(bottom, top, segments):
    segs = list(segments)
    for name, kind, n in segs:
        if kind not in (FLIGHT, WINDERS, LANDING):
            raise FitCheckError(f"unknown segment kind {kind!r}")
        if int(n) != n or n < 0 or (kind == LANDING) != (n == 0):
            raise FitCheckError(f"{name}: a landing has no riser, a flight or a turn at least one")
    total = sum(n for _, _, n in segs)
    if total < 1 or top <= bottom:
        raise FitCheckError("risers and a positive rise are required")
    h = (top - bottom) / total
    out, k = [], 0
    for name, kind, n in segs:
        start = bottom + k * h
        k += n
        end = bottom + k * h if k < total else top
        out.append({"segment": name, "kind": kind, "risers": n, "first_riser": k - n + 1 if n else None,
                    "last_riser": k if n else None, "start_level": start, "end_level": end})
    return {"riser": h, "risers": total, "segments": out}


def headroom(beam_top, beam_depth, tread_level):
    if beam_depth <= 0:
        raise FitCheckError("beam depth must be positive")
    return beam_top - beam_depth - tread_level
