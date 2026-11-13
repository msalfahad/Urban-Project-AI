"""R-T662-1 (every villa): REBAR BY OWNER-APPROVED RATIO (owner 2026-11-09 18:30 item (2); AGENT_BRIEF 'Rebar by ratio').
Research rule, unwired: nothing released, no engine / candidate / rule-version / knowledge / registry file changes; the
ratio rows are proposals for a later Gate B wiring row.

Physical element: the reinforcing bars of one structural MEMBER (net installed mass, kg; t at display). The owner rule
applies to a member WITHOUT a detailed bar takeoff: kg = its concrete m3 x the kg/m3 of its element type, + 3 .. 5 %
laps and offcuts. Never both ways on one member.

1. MEMBER DETAIL STATE (from the member's own STR.REBAR lines; EXCLUDED readings are not lines of the member):
     FULL     every bar line RELEASED                                 -> detailed; calibrates
     BOUNDED  RELEASED and / or HELD with BOTH ends (no blank, no open) -> detailed range; calibrates (low and high)
     PARTIAL  some RELEASED / bounded detail AND some blank / open line -> detailed part kept; ratio NOT applied
              (it would be the second way on the same member); its blank groups stay HELD by name
     NONE     every bar line HELD blank                                -> no detailed takeoff: ratio candidate
   An open-high line (low measured, high open) is detail with an unknown part: it makes the member PARTIAL.

2. CONCRETE OF THE MEMBER (bound by a recorded id only, never by geometry guessed here):
     RELEASED (every bound line released) -> m3 point; HELD bounded (no blank) -> low .. high; any bound line HELD
     blank -> BLANK (kg HELD blank by name); no live bound line (none recorded, or only EXCLUDED readings) -> NOT_BOUND.

3. CALIBRATION per element type: the FULL / BOUNDED members whose concrete is RELEASED.
     ratio_low  = sum(detailed kg low)  / sum(m3)       ratio_high = sum(detailed kg high) / sum(m3)
   (counted kg / their concrete m3, as the owner wrote it; a weighted aggregate, not a member picked from the spread).
   The member list, n, per-member ratios and spread are shown; a member outside 0.5 .. 2 x the aggregate low ratio is
   NAMED as an outlier (kept, never removed silently). A type with no calibration member has NO ratio: its NONE
   members stay HELD ('no counted member of the type; no borrowed ratio'); a ratio is never borrowed across types.

4. RATIO KG of a NONE member with a calibrated type and a valued concrete:
     low  = m3_low  x ratio_low  x 1.03        high = m3_high x ratio_high x 1.05
   The 3 .. 5 % laps and offcuts are carried as the range (owner wording), never a picked value. Label
   'ESTIMATE - owner-approved ratio', never VERIFIED. Detailed and ratio subtotals are kept separate.

Missing never becomes 0: a blank concrete, an unbound member, an uncalibrated type each keep the kg HELD with the cause.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

D = Decimal
RULE = "R-T662-1"
LABEL = "ESTIMATE - owner-approved ratio"
LAP_LOW, LAP_HIGH = D("1.03"), D("1.05")
OUTLIER_BAND = (D("0.5"), D("2"))
TYPES = ("FOOTING", "GROUND_BEAM", "NECK", "COLUMN", "BEAM", "SLAB", "STAIR", "POOL_TANK_WALL", "GROUND_SLAB")


class RuleError(ValueError):
    pass


def q(x, places="0.000001"):
    return D(x).quantize(D(places), rounding=ROUND_HALF_UP)


def S(x):
    return None if x is None else str(q(x))


def _num(v, what):
    if v is None:
        raise RuleError(f"MISSING: {what} is None (missing never becomes 0)")
    d = D(str(v))
    if d < 0:
        raise RuleError(f"NEGATIVE: {what} = {v}")
    return d


# ---- 1. member detail state ----------------------------------------------------------------------------------------
def line_state(line, unit=None):
    """line: dict with class (RELEASED / HELD / EXCLUDED), measured_net, held_low, held_high (unit optional; when the
    caller names the unit, a line in another unit is refused: kg bars, m3 concrete)."""
    if unit is not None and line.get("unit", unit) != unit:
        raise RuleError(f"UNIT_REFUSED: {line.get('line_id')} is in {line.get('unit')}, expected {unit}")
    c = line["class"]
    if c == "RELEASED":
        _num(line.get("measured_net"), f"{line.get('line_id')} measured_net")
        return "R"
    if c == "HELD":
        lo, hi = line.get("held_low"), line.get("held_high")
        if lo is not None and hi is not None:
            if D(str(hi)) < D(str(lo)):
                raise RuleError(f"{line.get('line_id')}: high {hi} < low {lo}")
            return "B"
        if lo is not None:
            return "O"
        if hi is not None:
            raise RuleError(f"{line.get('line_id')}: high without low")
        return "H"
    if c == "EXCLUDED":
        return "X"
    raise RuleError(f"{line.get('line_id')}: unknown class {c}")


def member_state(lines):
    st = {line_state(x, "kg") for x in lines} - {"X"}
    if not st:
        raise RuleError("member has no live bar line")
    if st == {"R"}:
        return "FULL"
    if st <= {"R", "B"}:
        return "BOUNDED"
    if st <= {"H"}:
        return "NONE"
    return "PARTIAL"


def detailed_kg(lines):
    """(low, high) of the member's detailed lines; only for FULL / BOUNDED members."""
    lo = hi = D(0)
    for x in lines:
        s = line_state(x, "kg")
        if s == "R":
            v = D(str(x["measured_net"]))
            lo, hi = lo + v, hi + v
        elif s == "B":
            lo, hi = lo + D(str(x["held_low"])), hi + D(str(x["held_high"]))
        elif s != "X":
            raise RuleError(f"detailed_kg on a {s} line: member not FULL / BOUNDED")
    return lo, hi


# ---- 2. concrete of the member ---------------------------------------------------------------------------------------
def concrete_state(conc_lines):
    """conc_lines: the bound concrete lines (dicts as above). -> (state, low, high)."""
    live = [x for x in conc_lines if x["class"] != "EXCLUDED"]
    if not live:
        return "NOT_BOUND", None, None
    lo = hi = D(0)
    held = False
    for x in live:
        s = line_state(x, "m3")
        if s == "R":
            v = D(str(x["measured_net"]))
            lo, hi = lo + v, hi + v
        elif s == "B":
            held = True
            lo, hi = lo + D(str(x["held_low"])), hi + D(str(x["held_high"]))
        else:
            return "BLANK", None, None
    if lo == 0 and hi == 0:
        return "BLANK", None, None
    return ("HELD_BOUNDED" if held else "RELEASED"), lo, hi


# ---- 3. calibration ----
def calibration_set(rows, typ):
    """The calibration members of one type: FULL / BOUNDED detail on RELEASED concrete (a HELD concrete never
    calibrates). rows: dicts with type, state, concrete_state, member, m3_low, detailed_kg."""
    return [{"member": r["member"], "m3": D(r["m3_low"]), "kg_low": D(r["detailed_kg"][0]),
             "kg_high": D(r["detailed_kg"][1])}
            for r in rows if r["type"] == typ and r["state"] in ("FULL", "BOUNDED")
            and r["concrete_state"] == "RELEASED"]


# ---- 3b. calibration ----------------------------------------------------------------------------------------------------
def calibrate(members):
    """members: list of dicts {member, kg_low, kg_high, m3} (FULL / BOUNDED, concrete RELEASED). -> dict or None."""
    if not members:
        return None
    m3 = sum((_num(x["m3"], f"{x['member']} m3") for x in members), D(0))
    if m3 <= 0:
        raise RuleError("calibration concrete is 0 m3")
    lo = sum((_num(x["kg_low"], x["member"]) for x in members), D(0))
    hi = sum((_num(x["kg_high"], x["member"]) for x in members), D(0))
    r_lo, r_hi = lo / m3, hi / m3
    per = []
    for x in members:
        r = D(str(x["kg_low"])) / D(str(x["m3"]))
        out = not (OUTLIER_BAND[0] * r_lo <= r <= OUTLIER_BAND[1] * r_lo)
        per.append({"member": x["member"], "m3": S(x["m3"]), "kg_low": S(x["kg_low"]), "kg_high": S(x["kg_high"]),
                    "ratio_low": S(r), "ratio_high": S(D(str(x["kg_high"])) / D(str(x["m3"]))),
                    "outlier": out})
    rs = [D(p["ratio_low"]) for p in per]
    return {"n": len(members), "m3": S(m3), "kg_low": S(lo), "kg_high": S(hi), "ratio_low": S(r_lo),
            "ratio_high": S(r_hi), "spread_low": [S(min(rs)), S(max(rs))], "members": per,
            "outliers": [p["member"] for p in per if p["outlier"]]}


# ---- 4. ratio kg ---------------------------------------------------------------------------------------------------------
def ratio_kg(cal, conc):
    """cal: calibrate() result or None; conc: (state, low, high). -> dict with status and kg or the hold cause."""
    state, lo, hi = conc
    if cal is None:
        return {"status": "HELD", "cause": "no counted member of the type (no calibration); no borrowed ratio"}
    if state == "NOT_BOUND":
        return {"status": "HELD", "cause": "member concrete not bound to a live concrete line by a recorded id"}
    if state == "BLANK":
        return {"status": "HELD", "cause": "member concrete HELD blank: the ratio kg stays HELD blank by name"}
    k_lo = D(lo) * D(cal["ratio_low"]) * LAP_LOW
    k_hi = D(hi) * D(cal["ratio_high"]) * LAP_HIGH
    return {"status": LABEL, "kg_low": S(k_lo), "kg_high": S(k_hi),
            "formula": f"{S(lo)} m3 x {cal['ratio_low']} kg/m3 x 1.03 .. {S(hi)} m3 x {cal['ratio_high']} kg/m3 x 1.05",
            "concrete_state": state}


def assign(member_state_, cal, conc):
    """Route one member: detailed, ratio or held. Never both ways."""
    if member_state_ in ("FULL", "BOUNDED"):
        return {"route": "DETAILED", "status": "detailed takeoff kept (no ratio)"}
    if member_state_ == "PARTIAL":
        return {"route": "PARTIAL_HELD",
                "status": "detailed part kept; ratio NOT applied (second way on one member); blank groups stay HELD"}
    if member_state_ != "NONE":
        raise RuleError(f"unknown member state {member_state_}")
    r = ratio_kg(cal, conc)
    return {"route": "RATIO" if r["status"] == LABEL else "RATIO_HELD", **r}
