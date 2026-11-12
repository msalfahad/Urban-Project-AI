"""T-733 rules (research, unwired; every villa): a stair flight is read on ONE line set, and a void over a ceiling
needs a drawn opening in the governing slab.

Physical element (ERS 2.1). A stair step is drawn as a PAIR of parallel lines a nosing projection apart (nosing edge +
riser face, often on two layers). The plan area of a flight is the strip between its first and last line of the SAME
set: reading every flight on the nosing set or every flight on the riser set gives the same goings, only shifted by the
offset. Mixing sets (flight 1 on the nosing set, flight 2 on the riser set) puts one offset strip into both flights at
their junction and drops one offset strip at the far end: the footprints overlap, but nothing is built twice.
A dome drawn 'above' a room is a void in that room's ceiling only when the slab that closes the room is drawn open
there; a slab panel drawn continuous, with beams crossing the dome footprint, is closed.

R-T733-1 ONE LINE SET. Before two flight footprints are summed, unioned or compared, both are read on the same step-line
         set (same layer / same side of every pair). For a junction overlap equal to the pair offset x the flight width,
         the reading decides: if the same flights on one set (either set) have overlap 0 and sum = union, the overlap is a
         SET_MIX (a footprint position defect, area effect 0 on each flight line) and the flight lines are kept; only an
         overlap that survives a one-set reading is a physical overlap for R-T727-1.
R-T733-2 SET FROM THE OUTLINE. Of the two sets, the governing one is the set whose end lines coincide with the drawn stair
         outline (stringer / void edge / arrival edge); with no such coincidence both readings are stated and the
         difference is a named range, never a choice by size.
R-T733-3 CLOSED SLAB, NO VOID. A circle or outline drawn 'above' (hidden, projection layer) deducts from the ceiling below
         only if the governing slab drawing (structural slab plan of that roof, overlaid on checked columns) draws an
         opening there. A slab plan that draws the panel continuous (no opening line, no hatch, no ring, beams crossing
         the footprint) makes the ceiling below CLOSED: deduction 0 by drawing (DRAWING-CONFIRMED), not by default.
         With no slab drawing for that roof the void stays HELD (R-T727-4). A client request to open it without a
         revised structural drawing is an ALTERNATIVE shown apart, never applied to the baseline.
R-T733-4 CENSUS AGAINST THE LIVE RECORD. A line census or wiring list carried from an older candidate is restated on the
         candidate of record only after every carried line is compared entry by entry (stale = any field differs); a
         stale entry is re-derived, never carried.
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

D = Decimal
TOL_M2 = D("0.005")          # as R-T719 / R-T727


class RuleError(ValueError):
    pass


def q6(x):
    return D(str(x)).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


def one_set_reading(pairs):
    """R-T733-1. pairs: {'mixed': (a1, a2, overlap, union), 'set_a': (...), 'set_b': (...)} areas of flight 1, flight 2,
    their overlap and union under the engine's (mixed) reading and the two one-set readings. Returns the verdict dict."""
    for k in ("mixed", "set_a", "set_b"):
        if k not in pairs or any(v is None for v in pairs[k]):
            return {"result": "HELD", "cause": f"reading {k} missing: no verdict (never 0)"}
    m = [q6(v) for v in pairs["mixed"]]
    sets = {k: [q6(v) for v in pairs[k]] for k in ("set_a", "set_b")}
    if m[2] <= TOL_M2:
        return {"result": "NO_OVERLAP", "overlap_m2": m[2]}
    clean = {k: abs(v[0] + v[1] - v[3]) <= TOL_M2 and v[2] <= TOL_M2 for k, v in sets.items()}
    if any(clean.values()):
        # a one-set reading with no overlap exists: the mixed overlap is a set mix, not a built overlap
        return {"result": "SET_MIX", "overlap_m2": m[2], "clean_sets": sorted(k for k, c in clean.items() if c),
                "union_understated_by_m2": q6(m[0] + m[1] - m[3]),
                "flight_lines": "KEEP (each flight's own one-set area)"}
    return {"result": "PHYSICAL_OVERLAP", "overlap_m2": min(v[2] for v in sets.values()),
            "flight_lines": "UNION INCREMENT (R-T727-1)"}


def governing_set(set_end_coincides):
    """R-T733-2. set_end_coincides: {set_name: bool (its end lines lie on the drawn stair outline)}."""
    on = sorted(k for k, v in set_end_coincides.items() if v)
    if len(on) == 1:
        return {"set": on[0], "basis": "end lines on the drawn outline"}
    return {"set": None, "basis": "no single set on the outline: state both readings as a named range"}


def ceiling_void(slab_drawing, opening_drawn, beams_cross=None):
    """R-T733-3. slab_drawing: the governing slab plan exists and is overlaid (bool); opening_drawn: an opening line /
    hatch / ring inside the footprint on that plan (bool or None when unread). Returns the void statement."""
    if not slab_drawing:
        return {"result": "VOID_EXTENT_UNRESOLVED", "status": "HELD", "m2": None,
                "cause": "no slab drawing for that roof (R-T727-4)"}
    if opening_drawn is None:
        raise RuleError("slab drawing present but not read inside the footprint")
    if opening_drawn:
        return {"result": "DRAWN_OPENING", "status": "MEASURE_FROM_OUTLINE", "m2": "outline"}
    return {"result": "NOT_A_VOID", "status": "DRAWING-CONFIRMED", "m2": D("0"),
            "cause": "slab panel drawn continuous" + ("; beams cross the footprint" if beams_cross else "")}


def stale_entries(older, live):
    """R-T733-4. older / live: {line_id: entry}. Returns (stale ids, missing ids)."""
    stale = sorted(k for k in older if k in live and older[k] != live[k])
    missing = sorted(k for k in older if k not in live)
    return stale, missing
