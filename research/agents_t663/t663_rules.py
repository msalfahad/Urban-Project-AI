"""R-T663-1 .. R-T663-4 (every villa): the four WIRING CONDITIONS the Checker set on R-T662-1 (rebar by owner-approved
ratio, owner 2026-11-09 18:30) before any ratio line is wired. Research rules, unwired: nothing released, no engine /
candidate / rule-version / knowledge / registry file changes. R-T662-1 (research/agents_t662/t662_rules.py) is used as
it is and never edited.

R-T663-1 RANGE CHECK (owner: "checked against common ranges and SHOWN"). A reference range is admissible only with its
  printed source: book title, Drive folder, page, low, high, element type. A range with no page, no title or high < low
  is REFUSED (never a remembered figure). No admissible range for a type -> status NOT_CHECKED_NO_CITED_SOURCE (shown
  with every source searched). A calibrated ratio outside a cited range is FLAGGED and never adjusted.

R-T663-2 LAPS NOT COUNTED TWICE. The ratio adds 3 .. 5 % for laps and offcuts, so a calibration member's detailed kg
  must hold no lap / splice kg. Per bar group of a calibration member:
    LAP            the group is a lap / splice / procurement-incl-laps quantity            -> calibration REFUSED
    ANCHORAGE      a bar-end group (development at the member's ends) on a member whose
                   bar population needs no splice (splice_need NOT_REQUIRED, from the lap
                   authority census): bar length inside the support, physically installed -> kept, shown apart
    END_UNRESOLVED a bar-end group on a member whose population needs or draws a splice
                   (REQUIRED / DRAWN_OVERLAP / NOT_ESTABLISHED): lap and anchorage cannot be
                   told apart                                                               -> calibration REFUSED
    BAR            any other group                                                          -> kept
  A calibration member passes only with lap kg = 0 and no END_UNRESOLVED group.

R-T663-3 PARTIAL STAYS PARTIAL. A member whose blank group is a quantity the drawing does not print (e.g. footing top
  end legs drawn closed with no dimension) keeps its detailed part and takes no ratio; it joins the calibration only
  when every group is counted from a printed dimension. A ratio requested for a PARTIAL member is REFUSED.

R-T663-4 BINDING BY A RECORDED ID, CONFIRMED BY TWO MEASURES. A bar member is bound to a concrete line only when
  (a) a committed register names the concrete component id of the member, (b) that id is exactly one live concrete line
  of the candidate, (c) no other bar member names the same concrete id (one owner; a shared band is never split by
  guess), and (d) the register's own m3 for the member agrees with the line (RELEASED: within 0.5 %; HELD bounded:
  inside low .. high). Otherwise the member stays NOT_BOUND with the failed condition named. Never a geometric guess.
"""
from __future__ import annotations

import re
from decimal import Decimal

D = Decimal
RULES = ("R-T663-1", "R-T663-2", "R-T663-3", "R-T663-4")
LABEL = "ESTIMATE - owner-approved ratio"
M3_TOL = D("0.005")
MIN_CAL_N = 3


class RuleError(ValueError):
    pass


def q(x, places="0.000001"):
    return D(str(x)).quantize(D(places))


def S(x):
    return None if x is None else str(q(x))


# ---- R-T663-1 range check --------------------------------------------------------------------------------------------
def admit_range(ref):
    """ref: {type, book, folder, page, low, high}. -> normalised ref, or RuleError (never a remembered figure)."""
    for k in ("type", "book", "folder", "page"):
        if not str(ref.get(k) or "").strip():
            raise RuleError(f"RANGE_REFUSED: no {k} cited (a range without its printed source is never used)")
    if ref.get("low") is None or ref.get("high") is None:
        raise RuleError("RANGE_REFUSED: low / high missing")
    lo, hi = D(str(ref["low"])), D(str(ref["high"]))
    if hi < lo or lo <= 0:
        raise RuleError(f"RANGE_REFUSED: bad range {lo} .. {hi}")
    return dict(ref, low=lo, high=hi)


def range_check(typ, ratio_low, ratio_high, refs, searched=()):
    """-> {status, ...}. refs: admissible references (admit_range is applied here). The ratio is never changed."""
    rs = [admit_range(r) for r in refs if r.get("type") == typ]
    if not rs:
        return {"status": "NOT_CHECKED_NO_CITED_SOURCE", "ratio": [S(ratio_low), S(ratio_high)],
                "sources_searched": list(searched)}
    lo, hi = D(str(ratio_low)), D(str(ratio_high))
    out = []
    for r in rs:
        inside = r["low"] <= lo and hi <= r["high"]
        out.append({"book": r["book"], "page": r["page"], "range": [S(r["low"]), S(r["high"])],
                    "verdict": "INSIDE" if inside else "OUTSIDE_FLAGGED"})
    return {"status": "INSIDE" if all(o["verdict"] == "INSIDE" for o in out) else "OUTSIDE_FLAGGED",
            "ratio": [S(lo), S(hi)], "references": out}


# ---- R-T663-2 lap audit ----------------------------------------------------------------------------------------------
LAP_RE = re.compile(r"LAP|SPLICE|OVERLAP")
END_RE = re.compile(r"ENDS?_|_ENDS|DEVELOPMENT|ANCHORAGE")


def group_class(group, splice_need):
    g = str(group).upper()
    if LAP_RE.search(g):
        return "LAP"
    if END_RE.search(g):
        if splice_need == "NOT_REQUIRED":
            return "ANCHORAGE"
        return "END_UNRESOLVED"
    return "BAR"


def lap_audit(groups, splice_need):
    """groups: list of (group label, kg_low, kg_high) of ONE calibration member; splice_need of its bar population
    (NOT_REQUIRED / REQUIRED / DRAWN_OVERLAP / NOT_ESTABLISHED; None = not in the census). -> audit dict."""
    if splice_need is None:
        raise RuleError("LAP_AUDIT_REFUSED: the member's bar population has no splice-need record")
    acc = {"LAP": [D(0), D(0)], "ANCHORAGE": [D(0), D(0)], "END_UNRESOLVED": [D(0), D(0)], "BAR": [D(0), D(0)]}
    for g, lo, hi in groups:
        c = group_class(g, splice_need)
        acc[c][0] += D(str(lo))
        acc[c][1] += D(str(hi))
    lap = acc["LAP"]
    unres = acc["END_UNRESOLVED"]
    ok = lap == [0, 0] and unres == [0, 0] and not any(group_class(g, splice_need) in ("LAP", "END_UNRESOLVED")
                                                        for g, _, _ in groups)
    return {"splice_need": splice_need, "lap_kg": [S(lap[0]), S(lap[1])],
            "anchorage_kg": [S(acc["ANCHORAGE"][0]), S(acc["ANCHORAGE"][1])],
            "end_unresolved_kg": [S(unres[0]), S(unres[1])], "bar_kg": [S(acc["BAR"][0]), S(acc["BAR"][1])],
            "passes": ok}


def require_lap_free(audit, member):
    if not audit["passes"]:
        raise RuleError(f"LAPS_IN_CALIBRATION: {member} carries lap / unresolved end kg {audit['lap_kg']} / "
                        f"{audit['end_unresolved_kg']}: the +3 .. 5 % would count laps twice")


# ---- R-T663-3 partial stays partial --------------------------------------------------------------------------------
def partial_resolution(blank_groups, printed):
    """blank_groups: labels of the member's blank groups; printed: {label: printed dimension or None}. -> state."""
    miss = [g for g in blank_groups if printed.get(g) is None]
    return ("PARTIAL", miss) if miss else ("COUNTABLE", [])


def wiring_route_guard(route, member):
    if route != "RATIO":
        raise RuleError(f"RATIO_REFUSED: {member} is routed {route}; only a member with no detailed takeoff takes a ratio")


# ---- R-T663-4 binding ------------------------------------------------------------------------------------------------
def bind(member, register_rows, concrete_by_id, owners_of_id):
    """register_rows: the committed register rows naming this member: [{component, m3}]; concrete_by_id: concrete id ->
    list of live concrete line dicts (class, measured_net, held_low, held_high); owners_of_id: concrete id -> set of bar
    members naming it. -> {bound: bool, concrete_id, lines, reason}."""
    comps = {r["component"] for r in register_rows if r.get("component")}
    if not comps:
        return {"bound": False, "reason": "(a) no committed register row names a concrete component of the member"}
    if len(comps) != 1:
        return {"bound": False, "reason": f"(a) register names {len(comps)} components: {sorted(comps)}"}
    cid = next(iter(comps))
    hits = [(pre + cid, concrete_by_id[pre + cid]) for pre in ("P-C:", "U-C:", "") if pre + cid in concrete_by_id]
    if len(hits) != 1 or len(hits[0][1]) != 1:
        return {"bound": False, "reason": f"(b) {cid}: {len(hits)} candidate ids / not exactly one live line"}
    eid, (line,) = hits[0]
    if owners_of_id.get(cid, set()) - {member}:
        return {"bound": False, "concrete_id": eid,
                "reason": f"(c) {cid} is also named by {sorted(owners_of_id[cid] - {member})}: shared band, never split by guess"}
    m3s = {r.get("m3") for r in register_rows}
    if len(m3s) != 1 or None in m3s:
        return {"bound": False, "concrete_id": eid, "reason": "(d) register m3 missing or ambiguous"}
    reg = D(str(next(iter(m3s))))
    if line["class"] == "RELEASED":
        v = D(str(line["measured_net"]))
        ok = v > 0 and abs(reg - v) <= M3_TOL * v
        why = f"register {S(reg)} vs line {S(v)} m3"
    elif line["class"] == "HELD" and line.get("held_low") is not None and line.get("held_high") is not None:
        lo, hi = D(str(line["held_low"])), D(str(line["held_high"]))
        ok = lo - M3_TOL * lo <= reg <= hi + M3_TOL * hi
        why = f"register {S(reg)} vs line {S(lo)} .. {S(hi)} m3"
    else:
        return {"bound": False, "concrete_id": eid, "reason": "(d) concrete line HELD blank: no second measure"}
    if not ok:
        return {"bound": False, "concrete_id": eid, "reason": f"(d) two measures disagree: {why}"}
    return {"bound": True, "concrete_id": eid, "line_id": line["line_id"], "reason": f"(a)-(d) pass: {why}"}


# ---- the Gate-B readiness of one ratio row --------------------------------------------------------------------------
def gate(range_status, cal_n, laps_ok):
    blockers = []
    if range_status != "INSIDE":
        blockers.append(f"(1) range check {range_status}")
    if cal_n < MIN_CAL_N:
        blockers.append(f"(2) calibration n = {cal_n} < {MIN_CAL_N} (WEAK)")
    if not laps_ok:
        blockers.append("(3) laps not proven absent from the calibration kg")
    return {"wiring_ready": not blockers, "blockers": blockers}
