"""R-T643-1 (every villa): REBAR NEVER MORE CERTAIN THAN THE INPUTS IT USES; one rule for the reverse case of the T-639
class A principle (a RELEASED bar line whose own concrete element is HELD) and for the concrete binding of bar lines.
Research rule, unwired: no engine, candidate, released (V2.9 + route G), rule / knowledge version or registry file
changes; the DOWNGRADE rows are downgrade-only record PROPOSALS (owner 2026-10-24 23:57: Checker-issued or
Checker-validated, line-bound, may only move a line to HELD, never promote).

Part 1, INHERIT (decide_inherit). A RELEASED bar population n x L x d^2/162 sits on a HELD concrete element. Its inputs
are n and d (the schedule row of the member's printed mark) and L (the record's length basis, e.g. for column main
bars the storey interval between two declared structural levels; bars run through the joint, so the split of the
interval into clear height + controlling depth does not enter L). The concrete hold is reduced to the FACTS it rests on
(the rule and the facts_used / held level of its latest effective register entry). Then:
  DOWNGRADE  a fact of the concrete hold enters n, L or d (e.g. the top level of the storey is not declared: the
             interval, i.e. L, is open). The bar line goes to HELD with that cause; no quantity is computed.
  KEEP       no fact of the concrete hold enters n, L or d, every bar input is printed and L equals the declared
             interval the concrete rule itself used (facts_h). The line stays released; the hold is shown not to touch
             it, cited.
  Anything else (an unknown hold rule, an L that does not reconcile with the declared interval, a missing count /
  diameter / length, a schedule re-read that differs from the record) is REFUSED: the line cannot be kept released.

Part 2, BIND (classify_binding). Every bar line ends BOUND (concrete line id(s), their class, the basis) or
UNRESOLVED (the reason, and a candidate line where one is only inferred). An inferred binding is never written as
BOUND. A bound class only adds a cause; it never computes or releases a quantity.

Laps are never added (OWNER_RULE_REBAR_2026-10-24 s.2 proposal, s.4 item 3)."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

D = Decimal


class RuleError(ValueError):
    pass


def q(x, places="0.000001"):
    return D(x).quantize(D(places), rounding=ROUND_HALF_UP)


def kg_per_m(d_mm):
    d = D(str(d_mm))
    if d < 4 or d > 60:
        raise RuleError(f"UNIT_REFUSED: bar diameter {d_mm} is not a mm diameter (4 .. 60)")
    return d * d / D(162)


def population_kg(count, length_m, d_mm):
    """n x L x d^2 / 162 (kg, unrounded); a missing input raises (HELD, never 0)."""
    for name, v in (("count", count), ("length", length_m), ("diameter", d_mm)):
        if v in (None, ""):
            raise RuleError(f"{name} not printed: the population stays HELD, never 0")
    n, L = D(str(count)), D(str(length_m))
    if n <= 0 or n != n.to_integral():
        raise RuleError(f"bar count {count} is not a positive whole number of bars")
    if L <= 0 or L > 50:
        raise RuleError(f"UNIT_REFUSED: length {length_m} m (an mm figure read as m?)")
    return n * L * kg_per_m(d_mm)


# Which bar input each known concrete hold rule enters, for a column MAIN-BAR population over the storey interval.
#   R-COL-LEVEL-HEIGHT-1      a structural level bounding the storey is not declared -> the interval (L) is open.
#   R-COL-SECTION-CONFLICT-1  printed schedule section vs drawn outline -> only the cross-section; the levels are
#                             declared (facts_h) and n / d are read from the schedule row of the printed mark.
HOLD_ENTERS = {
    "R-COL-LEVEL-HEIGHT-1": ("L",),
    "R-COL-SECTION-CONFLICT-1": (),
}
BAR_POPULATIONS = ("COLUMN_MAIN_BARS_OVER_STOREY_INTERVAL",)


def decide_inherit(bar, hold, schedule=None):
    """bar: {population, count, dia_mm, length_m, released_kg}; hold: {rule, facts_used, held_reason, facts_h,
    declared_levels}; schedule: optional independent re-read {count, dia_mm} of the printed mark. Returns a decision
    dict (DOWNGRADE / KEEP) or raises RuleError (REFUSED)."""
    if bar.get("population") not in BAR_POPULATIONS:
        raise RuleError(f"REFUSED: population {bar.get('population')} has no input map (new rule version needed)")
    rule = hold.get("rule")
    if rule not in HOLD_ENTERS:
        raise RuleError(f"REFUSED: concrete hold rule {rule} is not mapped to the bar inputs it enters")
    kg = population_kg(bar.get("count"), bar.get("length_m"), bar.get("dia_mm"))
    if bar.get("released_kg") is not None and abs(q(kg, "0.001") - D(str(bar["released_kg"]))) > D("0.001"):
        raise RuleError(f"REFUSED: released {bar['released_kg']} kg != n x L x d^2/162 = {q(kg)}")
    if schedule is not None and (D(str(schedule["count"])) != D(str(bar["count"]))
                                 or D(str(schedule["dia_mm"])) != D(str(bar["dia_mm"]))):
        raise RuleError(f"REFUSED: schedule re-read {schedule} differs from the record n {bar['count']} d {bar['dia_mm']}")
    enters = HOLD_ENTERS[rule]
    if enters:
        return {"decision": "DOWNGRADE", "to": "HELD", "inputs_entered": list(enters),
                "cause": f"{rule}: {hold.get('held_reason')} -> enters {'/'.join(enters)} of the bar population "
                         f"(facts {', '.join(hold.get('facts_used') or []) or 'named in the hold'})",
                "kg_withdrawn": q(kg)}
    fh = hold.get("facts_h")
    if fh is None or not hold.get("declared_levels"):
        raise RuleError("REFUSED: the storey interval is not shown declared by the concrete rule (no facts_h / levels): "
                        "a bar length from an unprinted height cannot stay released")
    if D(str(fh)) != D(str(bar["length_m"])):
        raise RuleError(f"REFUSED: bar length {bar['length_m']} != declared interval facts_h {fh}")
    return {"decision": "KEEP", "to": "RELEASED", "inputs_entered": [],
            "cause": f"{rule} rests on the cross-section only (facts_used none); n {bar['count']} and d {bar['dia_mm']} "
                     f"from the schedule row of the printed mark, L {bar['length_m']} = declared interval facts_h {fh} "
                     f"({' -> '.join(hold['declared_levels'])})",
            "kg_kept": q(kg)}


def concrete_state(classes):
    """worst state of the bound concrete line(s): EXCLUDED > HELD > RELEASED."""
    if not classes:
        raise RuleError("no concrete class")
    for k in ("EXCLUDED", "HELD"):
        if k in classes:
            return k
    if set(classes) != {"RELEASED"}:
        raise RuleError(f"unknown concrete class in {classes}")
    return "RELEASED"


def classify_binding(lines, basis, unresolved=None, mixed_is_unresolved=False):
    """lines: [(line_id, class)] found by an EXACT id route; returns BOUND / UNRESOLVED. With mixed_is_unresolved the
    route binds only to a group of pieces (e.g. a band whose span numbering differs between registers): a group with
    mixed states cannot give the piece its state -> UNRESOLVED."""
    if not lines:
        return {"binding": "UNRESOLVED", "reason": unresolved or "no concrete line id is recorded for this element",
                "concrete_lines": [], "concrete_class": None}
    cls = sorted({c for _, c in lines})
    if mixed_is_unresolved and len(cls) > 1:
        return {"binding": "UNRESOLVED", "concrete_lines": sorted(l for l, _ in lines), "concrete_class": None,
                "reason": f"{basis}: the group's pieces are {'/'.join(cls)} and the register does not say which piece "
                          "carries this bar line"}
    return {"binding": "BOUND", "basis": basis, "concrete_lines": sorted(l for l, _ in lines),
            "concrete_class": concrete_state(cls)}
