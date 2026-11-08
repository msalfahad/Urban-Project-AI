"""R-T639-1 (every villa): the REBAR HOLD CENSUS. Every HELD-blank or open-high STR.REBAR line of a candidate is given
ONE class and a named cause; nothing is computed except class D. Research rule, unwired: no engine, candidate,
released (V2.9 + route G), rule / knowledge version or registry file changes; the class D rows are fix-row proposals
for the wiring manifest (lane I).

Classes (priority order; the first that applies wins):
  A  CONCRETE_HELD    the line's own concrete element (its concrete line in the same candidate, bound by id) is HELD
                      or EXCLUDED: the bars follow that cause and are never released ahead of their concrete (a bar
                      quantity on a HELD concrete element is REFUSED here, release_refusal()).
  D  COMPUTABLE_NOW   every input is printed and an EXISTING RELEASED method already values the same population on a
                      sibling line: bar count and diameter from the schedule row, length from the record, unit mass by
                      the declared method (R-REBAR-POPULATION-1, REBAR.UNIT_MASS.METHOD = d^2 / 162), the concrete
                      line RELEASED, and the recorded hold is a cause that provably does not enter n, L or d. Only the
                      kinds listed in D_KINDS qualify; a new kind needs a new rule version.
  C  OWNER_GATED      resolving it needs a reinforcement method / convention change the owner has not approved
                      (owner 2026-10-25 10:33: no reinforcement calculation code change until an implementation stage
                      is approved; route G generic profile values, Q-17 A; note-9 lengths outside the starter group,
                      owner 2026-10-29 option B).
  B  INPUT_NOT_GIVEN  the drawings do not give an input: schedule notation unresolved (Q-71 count from a spacing /
                      per-metre notation, diameter not printed, boxed-bar notation) or a detail not drawn /
                      dimensioned (designer item: bar ends, legs, bends, extents, zones, cover printed only as a
                      minimum), incl. the owner-named footing holds of 2026-10-25 13:16.
  Every line must reach a class with a non-empty cause; an unclassifiable line raises RuleError (never dropped).

Laps: never added here (OWNER_RULE_REBAR_2026-10-24 s.2 is a proposal; s.4 item 3: every other lap HELD); a lap / stock
allowance added to a class D row is REFUSED (lap_refusal()).
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

D = Decimal


class RuleError(ValueError):
    pass


def q(x, places="0.000001"):
    return D(x).quantize(D(places), rounding=ROUND_HALF_UP)


def S(x):
    return None if x is None else format(D(x).normalize(), "f") if D(x) == D(x).to_integral() else str(D(x))


# ---- unit mass and the class D formula ------------------------------------------------------------------------------
UNIT_MASS_METHOD = "D2_OVER_162"          # the declared project method of every released STR.REBAR line (T-449)


def kg_per_m(d_mm):
    d = D(str(d_mm))
    if d < 4 or d > 60:
        raise RuleError(f"UNIT_REFUSED: bar diameter {d_mm} is not a mm diameter (4 .. 60)")
    return d * d / D(162)


def population_kg(count, length_m, d_mm, laps_m=None, lap_rule=None):
    """R-REBAR-POPULATION-1: n x L x d^2 / 162 (kg, unrounded Decimal). Count, length and diameter must be printed;
    a missing one raises (the line stays HELD, never 0). A lap added without an owner-approved lap rule is refused."""
    if laps_m not in (None, 0, "0") and not lap_rule:
        raise RuleError("LAP_REFUSED: a lap / stock length is added without an owner-approved lap rule "
                        "(OWNER_RULE_REBAR_2026-10-24 s.2 is a proposal; s.4 item 3)")
    for name, v in (("count", count), ("length", length_m), ("diameter", d_mm)):
        if v in (None, ""):
            raise RuleError(f"{name} not printed: the population stays HELD, never 0")
    n, L = D(str(count)), D(str(length_m))
    if n <= 0 or n != n.to_integral():
        raise RuleError(f"bar count {count} is not a positive whole number of bars")
    if L <= 0 or L > 50:
        raise RuleError(f"UNIT_REFUSED: length {length_m} m (an mm figure read as m?)")
    return n * (L + D(str(laps_m or 0))) * kg_per_m(d_mm)


def release_refusal(concrete_class):
    """a bar quantity on a HELD / EXCLUDED concrete element is never released (class A)."""
    if concrete_class != "RELEASED":
        raise RuleError(f"RELEASE_REFUSED: the concrete element is {concrete_class}: its bars follow that cause")


def lap_refusal(row):
    if row.get("laps_m") not in (None, "0", 0) and not row.get("lap_rule"):
        raise RuleError("LAP_REFUSED: lap on a class D row without an owner-approved lap rule")


# ---- cause kinds by the recorded hold text -------------------------------------------------------------------------
# (kind, class, regex, short meaning). Order matters: the first match names the line.
KINDS = [
    ("C_ROUTE_G_PROFILE", "C", r"PROFILE_VALUE_NOT_USABLE",
     "route G generic profile value not usable (Q-17 A project data): a route G convention / code change, owner-gated"),
    ("C_NOTE9_OUTSIDE_GROUP", "C", r"anchorage into the support, (already )?inside the note-9 range"
                                   r"|ST7757 p\.8 note 9, zone not printed|p\.8 note 9, zone not printed",
     "anchorage length into the end support: note 9 is a starter-bar note; outside its group HELD BLANK (owner "
     "2026-10-29 option B, DGP-T373-LAP)"),
    ("B_FOOTING_COVER", "B", r"UNSUPPORTED BASIS: 38 footing mesh lines",
     "footing mesh straight run = side - 2 x cover with the note-22 7 cm cover, printed only as a MINIMUM: bar "
     "end / cover not established (Checker downgrade, owner 2026-10-25 13:16 / 13:25 footing holds)"),
    ("B_BOXED_NOTATION", "B", r"BOXED bars printed",
     "boxed-bar schedule notation without a diameter: meaning not established"),
    ("B_Q71_NOTATION", "B", r"count Q-71|count from a spacing is owner Q-71|spacing count Q-71|diameter not printed",
     "schedule notation unresolved: per-metre / spacing count (Q-71 needs the drawn zones) or diameter not printed"),
    ("B_SIDE_BARS_KEY", "B", r"width-to-count key not printed",
     "side bars by beam width over 60 cm depth: width-to-count key not printed"),
    ("B_LINK_RULE_GAP", "B", r"link arrangement for L = \d+ cm not printed|candidate links differ or are not printed",
     "link arrangement not printed for this case"),
    ("B_CANDIDATE_SECTION", "B", r"section candidates CONC/|bars of the span not established",
     "ground-beam span section among printed candidates with no project detail (designer D-items)"),
    ("B_POOL_DESIGNER", "B", r"POOL_POPULATION_DESIGNER",
     "pool bar population: two printed zones for a pool ruled flat (designer item)"),
    ("B_NO_BARS_PRINTED", "B", r"NO_BARS_PRINTED|BARS_NOT_PRINTED|TEMPERATURE_ROW_NOT_PRINTED|NOT_PRINTED: the shallow"
                               r"|no schedule row, no section with bars|section prints the outline only, no bars"
                               r"|that no schedule row sizes",
     "no bars printed for this element / group (designer item, never 0)"),
    ("B_NOT_DRAWN", "B", r"NOT_DRAWN_OR_HELD|BAR_DIRECTION_NOT_DRAWN|ZONE_NOT_DELIMITED|OUTLINE_CLIPPED",
     "element / bar direction / zone not drawn (designer item)"),
    ("B_DETAIL_NOT_DIMENSIONED", "B", r"BLOCKED_DETAILING|LENGTH_NOT_DIMENSIONED|LENGTH_NOT_PRINTED|LEG_LENGTH_NOT"
                                      r"|not drawn \| |not drawn$|hook-down legs|held ends|up-turn legs"
                                      r"|no top-bar end valued|bar ends not detailed|bend / hook shape|not dimensioned"
                                      r"|development length|whether the support top bars add",
     "bar ends / legs / bends / extents not detailed or dimensioned (designer item, RFI S21 family)"),
    ("B_JOINT_LINKS_INFO", "B", r"^not printed$",
     "links through the beam-column joint: whether they continue is not printed (information line)"),
    ("B_REGISTER_CONFLICT", "B", r"register CONFLICT|register HELD|carries two marks|TWO_MARKS_ONE_FOOTING"
                                 r"|\(With Stair\)|planted-column extra|T-119 CONFLICT",
     "member register conflict / candidate marks (owner Q-61 C member holds, designer D-items)"),
    ("B_DATUM_HELD", "B", r"GF annex zone|controlling depth changes",
     "storey interval / controlling depth not printed (annex datum Q-54 B; unlabelled framing depth)"),
    ("B_HELD_UNQUANTIFIED", "B", r"^HELD \(unquantified\)$",
     "ground-system group held unquantified at its source ledger (no printed population)"),
    ("B_FRAMING_D_SETTLED_NOT_D", "B", r"D_ctrl settled by calculated members",
     "framing member held, D_ctrl settled, but a D condition is not met (see the row)"),
    ("B_OPEN_HIGH_DETAIL", "B", r"^OPEN_HIGH:",
     "low end measured; the high end stays open by named parts the drawings do not detail"),
]

D_KINDS = {
    "D_COLUMN_MAIN_D_SETTLED": "column MAIN BARS net: the hold was a held framing member that does not change the "
                               "controlling depth (T-119 r2 FRAMING_MEMBER_HELD_D_SETTLED); the bars run the storey "
                               "interval through the joint, so n, L and d are all printed and none depends on the held "
                               "member; the same released method values the sibling columns of the storey",
}


def cause_kind(text):
    t = (text or "").strip()
    for kind, cls, rx, meaning in KINDS:
        if re.search(rx, t):
            return kind, cls, meaning
    raise RuleError(f"unclassifiable hold text: {t[:160]!r}")


def d_column_main(rec, t119_row, concrete_class, sibling):
    """class D test for one column main-bar line. Returns the fix row or raises with the reason it is not D."""
    reasons = rec["reasons"]
    if rec["bar_group"] != "MAIN_BARS_NET":
        raise RuleError("not a main-bar population")
    if len(reasons) != 1 or not re.search(r"controlling depth NOT changed by it \(D_ctrl settled by calculated "
                                          r"members\)$", reasons[0]):
        raise RuleError("hold is not only a D_ctrl-settled framing hold")
    if t119_row["hold_cause"] != "FRAMING_MEMBER_HELD_D_SETTLED":
        raise RuleError(f"T-119 cause {t119_row['hold_cause']}")
    release_refusal(concrete_class)
    m = re.match(r"p\.9 (C\d+) (GF|1F|2F): (\d+) ø (\d+); height ([\d.]+) \+ D_ctrl ([\d.]+) \(bars run through the "
                 r"joint\) = interval ([\d.]+)$", rec["printed"])
    if not m:
        raise RuleError(f"printed text not a full schedule reading: {rec['printed']!r}")
    mark, storey, n, d, h, dc, interval = m.groups()
    if D(h) + D(dc) != D(interval) or D(interval) != D(t119_row["interval"]) or D(dc) != D(t119_row["D_ctrl"]):
        raise RuleError("interval does not reconcile with T-119 (height + D_ctrl = interval)")
    if D(str(rec["count"])) != D(n) or D(str(rec["length_m"])) != D(interval):
        raise RuleError("record count / length differ from the printed schedule reading")
    if sibling["storey"] != storey or D(sibling["interval"]) != D(interval):
        raise RuleError("no released sibling column on the same storey interval")
    kg = population_kg(n, interval, d)
    return {"mark": mark, "storey": storey, "count": int(n), "dia_mm": int(d), "length_m": interval,
            "kg_per_m": S(q(kg_per_m(d))), "kg": S(q(kg)), "t": S(q(kg / 1000, "0.000001")),
            "formula": f"{n} x {interval} m x {d}^2/162 = {n} x {interval} x {q(kg_per_m(d))} = {q(kg)} kg"}
