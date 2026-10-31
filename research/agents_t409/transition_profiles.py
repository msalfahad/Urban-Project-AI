"""B3-07 HIDDEN PROFILE / TRANSITION STRIP census (T-409, research only, read by no method; every villa).

The family code B3-07 ('Hidden profile / transition strips', AR 'بروفايل مخفي', lm) names TWO different physical
elements, which are kept apart here (ERS s.2.1: define the physical element first):

1. HIDDEN PROFILE (Urban standard US-08; URBAN-SKIRTING-OPENING-METHOD v1 'SKIRTING (and the hidden profile on the
   same path, US-08)'): the aluminium profile of the HIDDEN skirting system, a wall-base element. It exists only where
   the project uses the hidden skirting system, and then it runs on the SAME payable path as the skirting, as its own
   BOQ item (never merged with the skirting). No project system -> HELD with the path as its bound; NORMAL system ->
   NOT_APPLICABLE. It is never a doorway item.

2. FLOOR TRANSITION PROFILE at a finish change: a metal / PVC strip where two floor finishes meet at a doorway or an
   open boundary. It is installed only on a boundary where the finish actually changes AND no other element (a marble
   threshold, an external sill, a window / door frame, the lift landing sill) owns the interface. Whether a profile is
   fitted there is decided only by an Urban rule or a printed note (URBAN-FINISH-EXTRAS-SEPARATE-ITEMS v1 makes a
   profile a SEPARATE item wherever source geometry supports one; it does not say that every finish change carries
   one). Classes:

   NO_FINISH_CHANGE      the same finish on both sides (floor continues): nothing to install, NOT_APPLICABLE
   RULE_INTERFACE        a marble threshold owns the strip (the wet doorway rule, or an answered project rule such
                         as Alsenan Q-06 a for basin spaces) and the marble rule defines the interface without a
                         profile: URBAN-WET-SERVICE-MARBLE-THRESHOLD v1
                         'floor_interfaces' (wet tile ends at the wet-side marble edge, dry porcelain at the dry-side
                         edge, marble owns the whole footprint): NOT_APPLICABLE; a strip under or beside it is refused
   OTHER_ELEMENT         a frame (floor-level glazing) or the lift landing sill (lift supplier) owns the interface
   SILL_HELD             an external entrance: the sill material is by specification (HELD), so how many finish
                         changes the opening has (0, 1 or 2 edges) is unknown: HELD, bound 0 .. 2 x width
   INTERFACE_HELD        a doorless wet / dry boundary (or a side whose finish is HELD): no rule or note defines the
                         interface (threshold, continued tile or a profile): HELD, bound 0 .. width
   UNRESOLVED            width or sides unknown: UNKNOWN, no bound

   A HELD / UNKNOWN row carries a blank quantity (never 0) and its bound beside it.

Project-agnostic; stdlib only. Lengths in metres (mm accepted with unit='mm').
"""

from __future__ import annotations

POLICY_ID = "T409_TRANSITION_PROFILE_CENSUS_V1"

NO_CHANGE, RULE_IF, OTHER, SILL_HELD, IF_HELD, UNRES = (
    "NO_FINISH_CHANGE", "RULE_INTERFACE", "OTHER_ELEMENT", "SILL_HELD", "INTERFACE_HELD", "UNRESOLVED")
CLASSES = (NO_CHANGE, RULE_IF, OTHER, SILL_HELD, IF_HELD, UNRES)
NOT_APPLICABLE, HELD, UNKNOWN = "NOT_APPLICABLE", "HELD", "UNKNOWN"
KINDS = ("DOOR", "ARCH", "PASSAGE", "OPEN_EDGE", "FLOOR_GLAZING", "LIFT_LANDING", "GATE")
MARBLE_RULE = "URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 floor_interfaces"
_UNITS = {"m": 1.0, "mm": 0.001}


class CensusError(ValueError):
    pass


def _r(v, n=6):
    return None if v is None else round(float(v) + 0.0, n)


def _width(b):
    unit = b.get("unit", "m")
    if unit not in _UNITS:
        raise CensusError(f"{b.get('id')}: unknown unit {unit!r}")
    w = b.get("width")
    if w is None:
        return None
    if not isinstance(w, (int, float)) or w <= 0:
        raise CensusError(f"{b.get('id')}: width must be a positive length, got {w!r}")
    return w * _UNITS[unit]


def classify(b: dict) -> dict:
    """One boundary (an opening or an open edge where two floor areas meet).
    b: id, kind, floor, width (+ unit), sides: [finish A, finish B] (finish text or None = HELD / unknown),
    wet: [bool, bool] (optional), threshold: None or {'material': 'MARBLE' | 'PORCELAIN' | 'HELD', 'line_id'},
    external (bool), frame (bool, the interface is a door / window frame), lift (bool).
    -> {'id', 'class', 'status', 'qty_ml', 'bound_ml', 'width_m', 'why'}"""
    if b.get("kind") not in KINDS:
        raise CensusError(f"{b.get('id')}: unknown boundary kind {b.get('kind')!r}")
    w = _width(b)
    thr = b.get("threshold") or {}
    sides = list(b.get("sides") or [None, None])
    if len(sides) != 2:
        raise CensusError(f"{b['id']}: a boundary has exactly two sides, got {len(sides)}")
    out = {"id": b["id"], "kind": b["kind"], "floor": b.get("floor"), "width_m": _r(w),
           "finish_a": sides[0], "finish_b": sides[1], "threshold": thr.get("material"),
           "threshold_line": thr.get("line_id"), "qty_ml": None, "bound_ml": None}
    if b.get("lift"):
        return dict(out, **{"class": OTHER, "status": NOT_APPLICABLE, "qty_ml": 0.0,
                            "why": "lift landing sill comes with the lift (supplier item), not a floor profile"})
    if b.get("frame"):
        return dict(out, **{"class": OTHER, "status": NOT_APPLICABLE, "qty_ml": 0.0,
                            "why": "the frame stands on the boundary: the finishes stop against it, no floor profile"})
    if thr.get("material") == "MARBLE":
        src = thr.get("source") or "the wet doorway rule"
        return dict(out, **{"class": RULE_IF, "status": NOT_APPLICABLE, "qty_ml": 0.0,
                            "why": f"marble threshold ({src}); {MARBLE_RULE}: tile / porcelain end at the marble "
                                   "edges, marble owns the strip"})
    if w is None or b.get("unresolved"):
        return dict(out, **{"class": UNRES, "status": UNKNOWN,
                            "why": b.get("unresolved") or "width not established"})
    if b.get("external"):
        return dict(out, **{"class": SILL_HELD, "status": HELD, "bound_ml": [0.0, _r(2 * w)],
                            "why": "external entrance: sill material by specification (none printed); 0, 1 or 2 "
                                   "finish edges depending on it; no rule or note fits a profile"})
    if any(s is None for s in sides):
        return dict(out, **{"class": IF_HELD, "status": HELD, "bound_ml": [0.0, _r(w)],
                            "why": "a side's floor finish is HELD: whether the finish changes is unknown"})
    wet = list(b.get("wet") or [False, False])
    if wet[0] != wet[1] and not thr:
        return dict(out, **{"class": IF_HELD, "status": HELD, "bound_ml": [0.0, _r(w)],
                            "why": "doorless wet / dry boundary: no rule or printed note defines its interface "
                                   "(marble rule names doorways; continued tile or a profile not printed)"})
    if sides[0].strip().upper() == sides[1].strip().upper():
        return dict(out, **{"class": NO_CHANGE, "status": NOT_APPLICABLE, "qty_ml": 0.0,
                            "why": "same floor finish on both sides: the floor continues, nothing to install"})
    return dict(out, **{"class": IF_HELD, "status": HELD, "bound_ml": [0.0, _r(w)],
                        "why": "the finish changes and no Urban rule or printed note says a profile is fitted"})


def census(boundaries) -> list:
    """Classify every boundary once. A doorway counted from both rooms (same id twice, or two ids at one drawn
    location 'at' = (x, y) within 0.01 m on one floor) is refused."""
    seen, at = set(), {}
    rows = []
    for b in boundaries:
        if b["id"] in seen:
            raise CensusError(f"boundary {b['id']} listed twice (one doorway counted from both rooms)")
        seen.add(b["id"])
        if b.get("at") is not None:
            k = (b.get("floor"), round(b["at"][0] / 0.01), round(b["at"][1] / 0.01))
            if k in at:
                raise CensusError(f"{b['id']} and {at[k]} are one drawn opening (counted from both rooms)")
            at[k] = b["id"]
        rows.append(classify(b))
    return rows


def bind_profile(row: dict, line: dict):
    """A proposed profile line for a boundary. Refused: any strip / profile line on a marble threshold (the strip
    is the marble's), a figure on a HELD / UNKNOWN row, a line on a NOT_APPLICABLE row, and a 0 on a HELD row."""
    if row["class"] == RULE_IF:
        raise CensusError(f"{row['id']}: a strip under / beside a marble threshold is refused ({MARBLE_RULE})")
    if row["status"] == NOT_APPLICABLE:
        raise CensusError(f"{row['id']}: {row['class']} carries no profile line")
    q = line.get("qty_ml")
    if row["status"] in (HELD, UNKNOWN) and q is not None:
        raise CensusError(f"{row['id']}: a {row['status']} row carries no figure (got {q!r}); blank with its bound")
    return {"id": row["id"], "line_id": line["line_id"], "qty_ml": None, "bound_ml": row["bound_ml"]}


def check(rows) -> None:
    """Ledger invariants: every id once; a HELD / UNKNOWN row never carries a figure (0 included); a marble threshold
    row is never also a strip row; a NOT_APPLICABLE row's figure is exactly 0."""
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise CensusError("a boundary appears twice")
    for r in rows:
        if r["status"] in (HELD, UNKNOWN) and r["qty_ml"] is not None:
            raise CensusError(f"{r['id']}: HELD / UNKNOWN as a figure ({r['qty_ml']!r}) refused (never 0)")
        if r["status"] == HELD and not r.get("bound_ml"):
            raise CensusError(f"{r['id']}: HELD without its bound")
        if r["class"] == RULE_IF and r.get("strip_line"):
            raise CensusError(f"{r['id']}: counted as marble threshold AND as a strip")
        if r["status"] == NOT_APPLICABLE and r["qty_ml"] not in (None, 0.0):
            raise CensusError(f"{r['id']}: NOT_APPLICABLE with a figure {r['qty_ml']!r}")


def totals(rows) -> dict:
    out = {}
    for r in rows:
        a = out.setdefault(r["class"], {"n": 0, "width_ml": 0.0, "bound_hi_ml": 0.0})
        a["n"] += 1
        a["width_ml"] = _r(a["width_ml"] + (r["width_m"] or 0.0))
        if r.get("bound_ml"):
            a["bound_hi_ml"] = _r(a["bound_hi_ml"] + r["bound_ml"][1])
    return out


def hidden_profile(path_ml, system):
    """US-08: the hidden profile runs on the SAME payable path as the hidden skirting, as its own item.
    path_ml: a number (the skirting path) or [lo, hi]; system: 'HIDDEN' | 'NORMAL' | None (not specified)."""
    if system not in ("HIDDEN", "NORMAL", None):
        raise CensusError(f"unknown skirting system {system!r}")
    if path_ml is None:
        return {"item": "HIDDEN_PROFILE", "status": UNKNOWN, "qty_ml": None, "bound_ml": None,
                "why": "skirting path not established"}
    lo, hi = (path_ml, path_ml) if isinstance(path_ml, (int, float)) else tuple(path_ml)
    if lo < 0 or hi < lo:
        raise CensusError(f"bad skirting path {path_ml!r}")
    if system == "NORMAL":
        return {"item": "HIDDEN_PROFILE", "status": NOT_APPLICABLE, "qty_ml": 0.0, "bound_ml": None,
                "why": "normal skirting system: no hidden profile (US-08 applies to the hidden system only)"}
    if system is None:
        return {"item": "HIDDEN_PROFILE", "status": HELD, "qty_ml": None, "bound_ml": [0.0, _r(hi)],
                "path_ml": [_r(lo), _r(hi)],
                "why": "skirting system (hidden / normal) neither printed nor answered: HELD; if HIDDEN it equals "
                       "the skirting path"}
    if lo != hi:
        return {"item": "HIDDEN_PROFILE", "status": HELD, "qty_ml": None, "bound_ml": [_r(lo), _r(hi)],
                "why": "hidden system: the skirting path itself is still a range"}
    return {"item": "HIDDEN_PROFILE", "status": "MEASURED", "qty_ml": _r(lo), "bound_ml": None,
            "why": "US-08: same payable path as the hidden skirting, its own item, never merged"}
