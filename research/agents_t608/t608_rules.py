"""R-T608-1 LIFT LANDING DOOR SCOPE BY TRADE (every villa; research rule, unwired; T-608).

Physical element: the lift landing entrance at one storey = the structural opening in the shaft-front wall (width x
height, jamb to jamb) + the landing-door assembly set in it (frame, sliding leaves, sill: drawn as panel lines across
the gap on the shaft side) + the finishes round it (threshold piece in front, surround on jambs + head) + the wall
around it (masonry, its lintel, the plaster / paint faces on both sides).

Kind (from the opening's OWN drawn evidence; an engine kind label such as PASSAGE is never evidence, ERS s.7 2026-11-07):
  DOOR_LEAF (a leaf block or its swing)            -> DOOR
  PANEL_LINES + SHAFT_CROSS (shaft symbol beside)  -> LIFT_LANDING_DOOR
  PANEL_LINES alone                                -> FRAMED (frame drawn, purpose not established: HELD per family)
  GLAZING                                          -> WINDOW (outside this rule)
  nothing                                          -> PASSAGE (doorless)

Per line family, what a LIFT_LANDING_DOOR takes (governing record in brackets):
  OPENING_COUNT  ARCH.PASSAGE never counts it (it has a frame and leaves) [R-T601-1, LIFT DOOR GAP register]
  DOOR_SUPPLY    one assembly per storey; the count is DRAWING-CONFIRMED from the panel lines; the OWNER TRADE is the
                 lift package ONLY where a printed note or the specification says so, otherwise HELD by name; never in
                 a door-trade supply line (PVC / aluminium / main entrance), never EXCLUDED as 'by others' without the
                 printed note [ELEMENT_REGISTER 'LIFT LANDING DOOR', Lead 2026-11-07]
  THRESHOLD      one piece B6-07 (FIN.MARBLE.LIFT_THRESHOLD); never also a door threshold (B3-04), a porcelain strip or
                 a transition profile [T-413, LIFT ENTRANCE / LIFT LANDING THRESHOLD register]
  SURROUND       B6-06 owns the jamb + head finish and the arrises: no plaster / paint return line, no corner bead
                 [LIFT ENTRANCE register]
  SKIRTING       the whole width is deducted, no jamb skirting [LIFT DOOR GAP register, R-T601-1]
  BLOCKWORK      the host wall deducts the full opening width x opening height (Q-73); the height is the structural
                 opening height of the landing entrance: printed -> used; not printed -> HELD with the bound
                 0 .. width x wall height beside, never 0, never a door-trade fallback (Q-55's 2.20 m is the fallback for
                 doors of the door trade, an internal door; a lift entrance height is fixed by the lift product), never
                 the freelancer's flat 2.40 m
  LINTEL         per the printed lintel schedule (else the owner precast lengths): one at most; count HELD while the head
                 (whether masonry is built above it) is not established; the if-built figure beside, never 0
  WALL_FACES     plaster / paint on each face deduct the same opening (w x h) once; a HELD height holds the face line
                 with the bound beside
  WET_TRADES     wall tile, doorway waterproofing, transition: not applicable when both sides are dry / shaft
Quantities are Decimal; a HELD result carries its bound beside and no value that could be summed.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
RULE_ID = "R-T608-1"
GOVERNING = ["ELEMENT_REGISTER 'LIFT LANDING DOOR' (Lead 2026-11-07 16:17)", "LIFT DOOR GAP IN SKIRTING (T-441)",
             "LIFT LANDING THRESHOLD / LIFT ENTRANCE (T-413)", "R-T601-1", "Q-73 (full deduction)",
             "Q-55 C (door fallback scope)", "owner lintel rule 2026-11-02 + RC LINTEL register ruling",
             "UP-OPEN-SCHED-001 1.4.0", "ERS s.2 / s.3"]
EVIDENCE = ("DOOR_LEAF", "PANEL_LINES", "SHAFT_CROSS", "GLAZING")
FAMILIES = ("OPENING_COUNT", "DOOR_SUPPLY", "THRESHOLD", "SURROUND", "SKIRTING", "BLOCKWORK", "LINTEL", "WALL_FACES",
            "WET_TRADES")
DOOR_TRADE_SUPPLY = ("DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM", "DOOR.MAIN_ENTRANCE")
FALLBACK_HEIGHTS = {"2.20": "Q-55 C internal-door fallback (door trade only)", "2.40": "freelancer flat height"}


class ScopeError(ValueError):
    pass


def kind_of(evidence):
    ev = set(evidence)
    bad = ev - set(EVIDENCE)
    if bad:
        raise ScopeError(f"unknown evidence {sorted(bad)}")
    if "DOOR_LEAF" in ev:
        return "DOOR"
    if "PANEL_LINES" in ev:
        return "LIFT_LANDING_DOOR" if "SHAFT_CROSS" in ev else "FRAMED"
    if "GLAZING" in ev:
        return "WINDOW"
    return "PASSAGE"


def _d(x):
    return None if x in (None, "") else D(str(x))


def expected(op, family):
    """What the family must do with a LIFT_LANDING_DOOR. op: {'evidence', 'width_m', 'height_m' (printed or None),
    'wall_h_m' (face / wall height used by the host line), 'lift_package_note' (bool: a printed note or spec names the
    lift package for the landing door), 'head_established' (bool), 'lintel_if_built_m3' (str or None)}.
    Returns {'takes', 'kind', 'status', 'value', 'bound', 'owner_trade', 'why'}."""
    if family not in FAMILIES:
        raise ScopeError(f"unknown family {family}")
    kind = kind_of(op.get("evidence", ()))
    if kind != "LIFT_LANDING_DOOR":
        raise ScopeError(f"R-T608-1 applies to a lift landing door, not {kind}")
    w = _d(op.get("width_m"))
    if w is None or w <= 0:
        raise ScopeError("the opening width must be established (jamb to jamb)")
    h = _d(op.get("height_m"))
    wh = _d(op.get("wall_h_m"))
    r = {"rule": RULE_ID, "family": family, "kind": kind, "value": None, "bound": None}
    if family == "OPENING_COUNT":
        return dict(r, takes=False, status="EXCLUDED", owner_trade="none (not a passage)",
                    why="a framed landing door with leaves is not a doorless passage")
    if family == "DOOR_SUPPLY":
        if op.get("lift_package_note"):
            return dict(r, takes=True, status="DRAWING-CONFIRMED", value="1", owner_trade="LIFT PACKAGE (printed)",
                        why="one landing-door assembly; the printed note names the lift package")
        return dict(r, takes=True, status="HELD", bound=["1", "1"], owner_trade="HELD (no printed note)",
                    why="one landing-door assembly drawn (count established); its supply trade is printed nowhere: "
                        "HELD by name, never a door-trade line, never 'by others'")
    if family == "THRESHOLD":
        return dict(r, takes=True, status="AS_B6-07", owner_trade="B6-07 lift threshold marble",
                    why="one threshold piece across the clear opening; not a door threshold or porcelain strip")
    if family == "SURROUND":
        return dict(r, takes=True, status="HELD" if h is None else "MEASURABLE", owner_trade="B6-06 lift surround",
                    why="jambs + head finish and arrises belong to the surround: no plaster / paint return, no bead")
    if family == "SKIRTING":
        return dict(r, takes=True, status="DEDUCT_WHOLE", value=str(w), owner_trade="skirting (deduction only)",
                    why="the whole width leaves the skirting run; jamb skirting 0 (framed, leaves)")
    if family in ("BLOCKWORK", "WALL_FACES"):
        trade = "masonry" if family == "BLOCKWORK" else "plaster / paint (each face)"
        if h is not None:
            if wh is not None and h > wh:
                raise ScopeError("opening height above the wall / face height")
            return dict(r, takes=True, status="DEDUCT", value=str(w * h), owner_trade=trade,
                        why=f"full opening {w} x {h} (printed height, Q-73)")
        if wh is None:
            return dict(r, takes=True, status="HELD", bound=None, owner_trade=trade,
                        why="opening height not printed and the wall height not established: HELD, no bound")
        return dict(r, takes=True, status="HELD", bound=["0", str(w * wh)], owner_trade=trade,
                    why="landing-entrance height not printed: deduction HELD 0 .. width x wall height, never 0, never "
                        "a door-trade fallback or the freelancer's height")
    if family == "LINTEL":
        ib = op.get("lintel_if_built_m3")
        if op.get("head_established"):
            if ib is None:
                raise ScopeError("head established but no lintel figure")
            return dict(r, takes=True, status="MEASURABLE", value=ib, owner_trade="structure (lintel schedule)",
                        why="masonry above the head is established: one lintel")
        return dict(r, takes=True, status="HELD", bound=["0", ib] if ib else None,
                    owner_trade="structure (lintel schedule)",
                    why="head not established: whether masonry is built above it is not known; at most one lintel")
    return dict(r, takes=False, status="NOT_APPLICABLE", owner_trade="none",
                why="both sides dry / shaft: no wall tile, doorway waterproofing or transition")


def audit(op, family, line):
    """Compare a candidate line's treatment with expected(). line: {'line_id', 'item_code', 'takes' (bool), 'class'
    (RELEASED / HELD / EXCLUDED / NONE), 'value' (str or None), 'kind_label' (the line's kind text or None),
    'height_used_m' (str or None), 'jamb_lm' (str or None)}. Returns (verdict, fix) where verdict is CORRECT / FIX_ROW
    / OMISSION and fix names the change; refuses the forbidden treatments outright."""
    exp = expected(op, family)
    ic = line.get("item_code") or ""
    if family == "SKIRTING" and _d(line.get("jamb_lm")) not in (None, D("0")):
        raise ScopeError(f"{line.get('line_id')}: a lift landing door is skirted as a doorless opening (jamb lm)")
    if family == "DOOR_SUPPLY":
        if ic in DOOR_TRADE_SUPPLY and line.get("takes"):
            raise ScopeError(f"{line.get('line_id')}: a lift landing door priced in a door-trade line {ic}")
        if line.get("class") == "EXCLUDED" and not op.get("lift_package_note"):
            raise ScopeError(f"{line.get('line_id')}: landing door excluded as out of scope without a printed note")
    if family in ("BLOCKWORK", "WALL_FACES") and op.get("height_m") in (None, ""):
        hu = line.get("height_used_m")
        if hu not in (None, ""):
            src = FALLBACK_HEIGHTS.get(str(D(hu).quantize(D("0.01"))), "an unprinted height")
            raise ScopeError(f"{line.get('line_id')}: deduction uses {hu} m ({src}) where no height is printed")
        if line.get("class") == "RELEASED" and line.get("takes"):
            raise ScopeError(f"{line.get('line_id')}: a face / wall deducting an unprinted height is released")
    if line.get("class") == "HELD" and line.get("value") not in (None, ""):
        raise ScopeError(f"{line.get('line_id')}: a HELD line carries a value")
    if family == "OPENING_COUNT":
        if line.get("takes") and line.get("class") == "RELEASED":
            return "FIX_ROW", "EXCLUDE from the passage count (kind LIFT_LANDING_DOOR); -1 pcs"
        return "CORRECT", None
    if family == "DOOR_SUPPLY":
        if line.get("class") == "NONE":
            return "OMISSION", "ADD a HELD-blank landing-door assembly line (count 1 beside, trade HELD by name)"
        return "CORRECT", None
    if family == "LINTEL" and exp["status"] == "HELD" and line.get("class") == "RELEASED":
        return "FIX_ROW", "HOLD the lintel: head not established"
    if family == "THRESHOLD" and line.get("takes") and not ic.startswith("FIN.MARBLE.LIFT_THRESHOLD"):
        if line.get("class") != "EXCLUDED":
            return "FIX_ROW", "EXCLUDE: the lift threshold is one B6-07 piece"
    if family == "SURROUND" and line.get("takes") and ic in ("FIN.PLASTER", "FIN.PAINT"):
        return "FIX_ROW", "REMOVE the return line: B6-06 owns the jambs + head"
    if family == "WET_TRADES" and line.get("takes"):
        return "FIX_ROW", "REMOVE: not applicable on dry / shaft sides"
    return "CORRECT", None


def tally(rows):
    """rows: [(name, verdict, fix, pcs_delta)]: the count change of the passage family and the names of fixes /
    omissions; refuses a row with an unknown verdict."""
    pcs = D("0")
    names = []
    for name, verdict, fix, delta in rows:
        if verdict not in ("CORRECT", "FIX_ROW", "OMISSION"):
            raise ScopeError(f"{name}: unknown verdict {verdict}")
        if verdict != "CORRECT":
            names.append(name)
        if delta is not None:
            pcs += D(delta)
    return pcs, names
