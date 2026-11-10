"""R-T685-1 / -2 / -3: WATERPROOFING HELD / BLANK / MISSING LINE CENSUS and the MEASURABLE NOW wet-room pieces
(every villa; research provenance, proposed; no new rule value, nothing wired or released).

R-T685-1 CENSUS. Every HELD line of the candidate whose code is a waterproofing code (FIN.WP.*, WP.*) plus every
  MISSING line (a merged, Checker-verified inventory row with no candidate line) gets exactly ONE cause class:
    MEASURABLE_NOW       every term is printed on a sheet / the DXF or owner-fixed: a fix row with its own value or a
                         drawn bound whose only open term is a named designer item
    MEASURED_NOT_WIRED   a merged, Checker-verified piece already carries the value; only the wiring is missing
    OPEN_BOUND           a drawn low .. high (or AT LEAST) bound exists; the open term is named
    DESIGNER_ITEM        a designer item (detail, depth, product, founding level) holds a term
    OWNER_OPEN           an owner item is parked or open (Q-34 2F top roof)
    NO_PHYSICAL_ELEMENT  the line names an element the drawings show does not exist (register only; propose EXCLUDED)
  Generic: one class per line; a freelancer figure is never a cause; HELD keeps measured_net None and is never 0; the
  census count equals the candidate's HELD lines of these codes plus the named MISSING rows (no line twice).

R-T685-2 ELEMENT TOTALS. Lines are grouped by physical element (roof flat, roof upturn, wet-room floor, wet-room wall
  upturn, wet-room membrane edge, floor penetration, door threshold, pool, substructure, planters) and by unit. A flat
  m2 and an upturn lm / m2 are NEVER added together (historical defect B11 L-2), wet rooms are never merged into a dry
  zone (B9 L-17), installed area and procurement (rolls, items) are kept apart (UP-WP-MAT-001). A membrane system that
  no sheet prints stays HELD by name; no default product, thickness, lap or coat count is applied.

R-T685-3 WET-ROOM UPTURN AND EDGE (UP-WP-003 1.7.0 0.20 m; Q-35 C door; Q-37 A open-sided pantry).
  upturn run = sum of the drawn wall-face runs round the wet box - each door width (its crossing is the separate
  transition row, Q-35 C) - each window width whose sill is KNOWN below the upturn height; a window whose sill is
  not printed is excluded in the LOW and included in the HIGH bound (the wall below the sill exists only if the sill
  is at least the upturn height). An open side (no wall drawn) carries no upturn: it is a membrane edge (termination,
  lm) at the box line where an owner rule fixes the box (Q-37 A), otherwise it stays HELD (detail not printed).
  Floor penetrations: every drain body printed on the drainage plan inside the room passes through the membrane, so
  the printed floor-drain count is an AT LEAST value; other pipes stay open until a wet-room detail defines them.
"""
from __future__ import annotations

from decimal import Decimal

Q6 = Decimal("0.000001")
UPTURN_H = Decimal("0.20")          # UP-WP-003 1.7.0 (owner)
MAX_RUN_M = Decimal("100")          # a single wall run above 100 m is a unit error (mm read as m)

CLASSES = ("MEASURABLE_NOW", "MEASURED_NOT_WIRED", "OPEN_BOUND", "DESIGNER_ITEM", "OWNER_OPEN", "NO_PHYSICAL_ELEMENT")
FREELANCER_WORDS = ("freelancer", "his row", "his figure", "his total")

# R-T685-2: item code -> physical element; units of one element are never mixed into another's sum
ELEMENT = {
    "FIN.WP.ROOF": "ROOF_FLAT", "FIN.WP.ROOF_UPTURN": "ROOF_UPTURN",
    "FIN.WP.FLOOR": "WET_FLOOR", "FIN.WP.WALL_UPTURN": "WET_WALL_UPTURN", "FIN.WP.TERMINATION": "WET_MEMBRANE_EDGE",
    "FIN.WP.PENETRATION": "WET_FLOOR_PENETRATION", "FIN.WP.DOORWAY": "DOOR_THRESHOLD",
    "FIN.WP.DOORWAY_TRANSITION": "DOOR_THRESHOLD", "FIN.WP.DOORWAY_TRANSITION_NR": "DOOR_THRESHOLD",
    "FIN.WP.MEMBRANE_ROLLS": "PROCUREMENT_ROLLS",
    "WP.POOL.MEMBRANE": "POOL", "WP.POOL.PROTECTION_SCREED": "POOL",
}
ELEMENT_UNITS = {"ROOF_FLAT": {"m2"}, "ROOF_UPTURN": {"lm"}, "WET_FLOOR": {"m2"}, "WET_WALL_UPTURN": {"m2"},
                 "WET_MEMBRANE_EDGE": {"lm"}, "WET_FLOOR_PENETRATION": {"pcs"}, "DOOR_THRESHOLD": {"m2", "pcs"},
                 "PROCUREMENT_ROLLS": {"pcs"}, "POOL": {"m2", "m3"}, "SUBSTRUCTURE": {"m2", "m3", "item"},
                 "PLANTERS": set()}
PROCUREMENT = {"PROCUREMENT_ROLLS"}


class RuleError(Exception):
    pass


def D(x):
    return x if isinstance(x, Decimal) else Decimal(str(x))


def S(x):
    return None if x is None else format(D(x).quantize(Q6), "f")


def element_of(code):
    if code.startswith("WP.FOUNDATION."):
        return "SUBSTRUCTURE"
    if code not in ELEMENT:
        raise RuleError(f"{code}: not a waterproofing code of the census")
    return ELEMENT[code]


def in_scope(code):
    return code.startswith(("FIN.WP.", "WP."))


def _len(x, what):
    v = D(x)
    if v < 0:
        raise RuleError(f"{what}: negative length {v}")
    if v > MAX_RUN_M:
        raise RuleError(f"{what}: {v} m is not a wall run (mm read as m?)")
    return v


def upturn_bound(wall_runs, doors, windows, h=UPTURN_H):
    """R-T685-3. wall_runs: [(name, m)] drawn wall faces round the box (an open side is NOT a wall run);
    doors: [(name, width m)]; windows: [(name, width m, sill m or None)] lying in those runs.
    -> dict(low_lm, high_lm, low_m2, high_m2, status, held_terms)."""
    if not wall_runs:
        raise RuleError("no wall run: an all-open box has no upturn, its sides are membrane edges")
    run = sum((_len(m, n) for n, m in wall_runs), Decimal(0))
    dw = sum((_len(w, n) for n, w in doors), Decimal(0))
    lo = hi = run - dw
    held = []
    for n, w, sill in windows:
        w = _len(w, n)
        if sill is None:
            lo -= w
            held.append(f"{n} sill not printed: {S(w)} m excluded in the low, included in the high")
        elif D(sill) < h:
            lo -= w
            hi -= w
        # sill >= h: the wall below the sill carries the full upturn: nothing deducted
    if lo < 0:
        raise RuleError(f"openings ({S(run - lo)} m) longer than the wall runs ({S(run)} m)")
    status = "MEASURED" if lo == hi else "OPEN_BOUND"
    return {"low_lm": S(lo), "high_lm": S(hi), "low_m2": S(lo * h), "high_m2": S(hi * h), "status": status,
            "held_terms": held, "wall_runs_lm": S(run), "doors_lm": S(dw), "upturn_h": S(h)}


def termination(open_runs, owner_box_rule):
    """R-T685-3: membrane edge on the open sides. Without an owner / printed box rule it stays HELD (never 0)."""
    if not owner_box_rule:
        return {"status": "HELD", "value_lm": None, "why": "edge position on an open side printed on no detail"}
    if not open_runs:
        raise RuleError("an owner box rule with no open side: nothing to terminate")
    v = sum((_len(m, n) for n, m in open_runs), Decimal(0))
    return {"status": "MEASURED", "value_lm": S(v), "owner_ref": owner_box_rule}


def penetrations_at_least(drains_printed):
    """R-T685-3: printed floor drains in the room -> AT LEAST count; None (plan not read) stays HELD."""
    if drains_printed is None:
        return {"status": "HELD", "at_least": None}
    n = int(drains_printed)
    if n < 0 or n != drains_printed:
        raise RuleError("a drain count is a whole number >= 0")
    if n == 0:
        return {"status": "HELD", "at_least": None, "why": "no drain printed: the count is open, never 0"}
    return {"status": "OPEN_BOUND", "at_least": n, "high": None}


def system_status(printed_text):
    """R-T685-2: membrane system / product. Not printed -> HELD by name, never a default."""
    if not printed_text:
        return {"status": "HELD", "system": None, "why": "membrane system / product printed on no sheet"}
    return {"status": "PRINTED", "system": printed_text}


def element_totals(lines):
    """R-T685-2. lines: dicts with item_code, unit, class, measured_net, held_low, held_high.
    -> {element: {unit: {...}}}; refuses a unit foreign to the element (e.g. an upturn lm into the flat m2)."""
    out = {}
    for l in lines:
        el = element_of(l["item_code"])
        u = l["unit"]
        if u not in ELEMENT_UNITS[el]:
            raise RuleError(f"{l.get('line_id')}: unit {u} cannot join element {el} (flat and upturn kept apart)")
        t = out.setdefault(el, {}).setdefault(u, {"released": Decimal(0), "released_n": 0, "held_low": Decimal(0),
                                                  "held_high": Decimal(0), "held_bounded_n": 0, "held_blank_n": 0,
                                                  "excluded_n": 0, "kind": "PROCUREMENT" if el in PROCUREMENT or
                                                  u == "item" else "INSTALLED"})
        c = l["class"]
        if c == "RELEASED":
            if l["measured_net"] is None:
                raise RuleError(f"{l.get('line_id')}: released with no value")
            t["released"] += D(l["measured_net"])
            t["released_n"] += 1
        elif c == "HELD":
            if l.get("measured_net") not in (None,):
                raise RuleError(f"{l.get('line_id')}: a HELD line carries a value")
            if l.get("held_high") is None:
                t["held_blank_n"] += 1
            else:
                t["held_low"] += D(l["held_low"] or 0)
                t["held_high"] += D(l["held_high"])
                t["held_bounded_n"] += 1
        elif c == "EXCLUDED":
            t["excluded_n"] += 1
        else:
            raise RuleError(f"{l.get('line_id')}: class {c}")
    for el in out.values():
        for t in el.values():
            for k in ("released", "held_low", "held_high"):
                t[k] = S(t[k])
            if not t["held_bounded_n"]:
                t["held_low"] = t["held_high"] = None
    return out


def census(entries, held_ids, missing_keys):
    """R-T685-1: one entry per HELD line and per MISSING row; returns counts by class."""
    ids = [e["key"] for e in entries]
    if len(set(ids)) != len(ids):
        raise RuleError("a line appears twice in the census")
    want = set(held_ids) | set(missing_keys)
    if set(ids) != want:
        raise RuleError(f"census != candidate HELD + MISSING: missing {sorted(want - set(ids))[:3]}, "
                        f"extra {sorted(set(ids) - want)[:3]}")
    by = {}
    for e in entries:
        if e["class"] not in CLASSES:
            raise RuleError(f"{e['key']}: class {e['class']}")
        txt = (e.get("cause") or "") + " " + (e.get("note") or "")
        if any(w in txt.lower() for w in FREELANCER_WORDS):
            raise RuleError(f"{e['key']}: a freelancer figure is never a cause")
        fix = e.get("fix")
        if fix and fix.get("value") is not None and D(fix["value"]) <= 0:
            raise RuleError(f"{e['key']}: a fix value <= 0 (HELD is never 0)")
        by[e["class"]] = by.get(e["class"], 0) + 1
    return dict(sorted(by.items()))
