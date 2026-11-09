"""R-T621-1 ROOM-AREA EVIDENCE PER RESIDUAL ROW (every villa; research rule, unwired; T-621).

Physical element: the INSTALLED finished floor of a tiled room (B3), net of what another trade owns and of what is not
floor. A reconciled-quantities row (engine vs reference, one named cause) is DRAWING-CONFIRMED only when the quantity
it carries is rebuilt from the drawing by this rule, never from the engine or the reference:

  1. OWN AREA FROM THE DRAWING ONLY. Every measure names its drawn entities by handle and its source is DRAWING:
     an OUTLINE (ordered chain of drawn edges, R-T606-1 geometry: vertices at the intersections of consecutive edges,
     so a door gap is closed on its own wall face; column polygons cut notches), a GAP (door / arch strip: jamb-to-jamb
     gap x face-to-face depth), a DIM (product of printed DIMENSION measurements) or a SOLID (column polygon, wall
     between two faces). A measure whose source is the ENGINE (its room polygon, its line), the REFERENCE (his row)
     or a cited report without handles is REFUSED as evidence: it cannot confirm itself.
  2. ROW KINDS. ROOM: a room line's own area must equal the engine line within AREA_TOL; the row's delta is then
     reference - engine and its own-area twin reference - own is printed beside. PIECE: a component row (stair arrival,
     strip, lift threshold, band, solid, missing room): its own area must equal |delta| within AREA_TOL. READING: a
     residual row: its delta must equal the stated expression of own areas and his figure within AREA_TOL (it stays
     UNRESOLVED / its class; only its evidence changes). NOT_ESTABLISHED: no own measure this run; the row keeps its
     earlier evidence and names what would close it. A measure that DIFFERS beyond AREA_TOL is a finding (DIFFERS),
     never a confirmation and never silently absorbed.
  3. RULE DEPTHS. A piece whose depth is set by an owner / Urban rule (lift landing threshold certain part 0.300,
     UP-ELEV-005) takes the drawn width x the rule depth; the rule is named; the depth is never read as drawn.
  4. CLASS SANITY. TOLERANCE only for |delta| < 0.01 m2 (his 2-dp working); a ROOM row classed ENGINE_RIGHT needs
     |reference - own| >= 0.005 (otherwise it is TOLERANCE, not a size difference).
  5. RESIDUAL SPLIT. The rows' deltas re-add EXACTLY (Decimal) to the section difference, by class and by evidence
     status; HELD never 0; DRAWING-CONFIRMED is a worker evidence status (not VERIFIED: the Checker re-measures).
AREA_TOL = 0.001 m2: arc flattening (R-T606-1 0.5 deg steps) and CAD noise (e.g. 0.000001 polygons) of the engine lines;
every actual difference is printed per row.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
Z = D("0")
RULE_ID = "R-T621-1"
GOVERNING = ["R-T606-1 (outline geometry)", "R-T612-1 (gross with interior solids)", "R-T553-1 (floor tile scope)",
             "R-T613-1 (statuses)", "UP-ELEV-005 (lift threshold certain part 0.300)", "UP-THR-001", "UP-CER-001",
             "ERS s.2 / s.3"]
AREA_TOL = D("0.001")
KINDS = ("OUTLINE", "GAP", "DIM", "SOLID")
SOURCES_REFUSED = ("ENGINE", "REFERENCE", "REPORT")
ROW_KINDS = ("ROOM", "PIECE", "READING", "NOT_ESTABLISHED")
CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED", "FREELANCER_RIGHT")
EVIDENCE = ("DRAWING_CONFIRMED", "DIFFERS", "NOT_REMEASURED")


class RuleError(ValueError):
    pass


def evidence(meas: dict) -> Decimal:
    """the own area of a measure; refuses a non-drawing source, a measure without handles or an unknown kind."""
    src = meas.get("source")
    if src in SOURCES_REFUSED:
        raise RuleError(f"evidence from the {src} refused: a quantity cannot confirm itself (R-T621-1 (1))")
    if src != "DRAWING":
        raise RuleError(f"evidence source {src!r} unknown")
    if not meas.get("handles"):
        raise RuleError("a drawn measure names its entities by handle")
    if meas.get("kind") not in KINDS:
        raise RuleError(f"measure kind {meas.get('kind')!r} unknown")
    a = D(meas["area"])
    if a <= 0:
        raise RuleError("an own area is positive (missing is never 0)")
    return a


def rule_piece(width: Decimal, rule_depth: Decimal, rule: str) -> Decimal:
    if not rule:
        raise RuleError("a rule depth names its rule")
    return (D(width) * D(rule_depth)).quantize(D("0.000001"))


def check_class(cls: str, delta: Decimal, kind: str, his_minus_own: Decimal | None = None):
    if cls not in CLASSES:
        raise RuleError(f"class {cls} unknown")
    if cls == "TOLERANCE" and D(delta).copy_abs() >= D("0.01"):
        raise RuleError(f"TOLERANCE {delta} is not a 2-dp working difference")
    if kind == "ROOM" and cls == "ENGINE_RIGHT" and his_minus_own is not None and his_minus_own.copy_abs() < D("0.005"):
        raise RuleError("ENGINE_RIGHT on a room his figure reproduces within 0.005: TOLERANCE")


def judge(kind: str, delta: Decimal, own: Decimal | None = None, engine: Decimal | None = None,
          expected: Decimal | None = None) -> tuple[str, Decimal | None]:
    """(evidence status, the measured difference that decided it)."""
    if kind not in ROW_KINDS:
        raise RuleError(f"row kind {kind} unknown")
    if kind == "NOT_ESTABLISHED":
        return "NOT_REMEASURED", None
    if kind == "ROOM":
        if own is None or engine is None:
            raise RuleError("a ROOM row needs the own area and the engine line")
        diff = D(own) - D(engine)
    elif kind == "PIECE":
        diff = D(own) - D(delta).copy_abs()
    else:
        if expected is None:
            raise RuleError("a READING row needs its expression")
        diff = D(expected) - D(delta)
    return ("DRAWING_CONFIRMED" if diff.copy_abs() <= AREA_TOL else "DIFFERS"), diff


def split(rows: list[dict], difference: Decimal) -> dict:
    """deltas by class and by evidence status; re-add exactly to the section difference."""
    tot = sum((D(r["delta"]) for r in rows), Z)
    if tot != D(difference):
        raise RuleError(f"rows re-add to {tot}, section difference {difference}")
    by_cls, by_ev, n_ev = {}, {}, {}
    for r in rows:
        if r["class"] == "HELD" and D(r["delta"]) == 0:
            raise RuleError("a HELD row is never 0")
        by_cls[r["class"]] = by_cls.get(r["class"], Z) + D(r["delta"])
        by_ev[r["evidence_status"]] = by_ev.get(r["evidence_status"], Z) + D(r["delta"])
        n_ev[r["evidence_status"]] = n_ev.get(r["evidence_status"], 0) + 1
    for k in by_ev:
        if k not in EVIDENCE:
            raise RuleError(f"evidence status {k} unknown")
        if k == "VERIFIED":
            raise RuleError("VERIFIED is recorded only by the Checker")
    if sum(by_cls.values(), Z) != tot or sum(by_ev.values(), Z) != tot:
        raise RuleError("split does not re-add")
    return {"total": str(tot), "by_class": {k: str(v) for k, v in sorted(by_cls.items())},
            "by_evidence": {k: str(v) for k, v in sorted(by_ev.items())}, "count_by_evidence": dict(sorted(n_ev.items()))}
