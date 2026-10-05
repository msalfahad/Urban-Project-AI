"""REBAR_MODEL_V1 - a generic, typed reinforcement model: source definition -> occurrence -> bar geometry -> count ->
length parts -> D^2/162 -> net kg -> completeness -> BBS eligibility -> mass conservation.

    bar_count(mode, value, distribution_m)     explicit count modes; a per-metre rate is never read as a bar count
    part(kind, length_m, state, rule, ...)     one length part of a bar (CORE / EXTENSION / HOOK / ANCHORAGE / LEG ...)
    component(...)                             one bar set of one occurrence: verified / provisional / audit kg
    population(...)                            one structural occurrence: release state from its required components
    totals(populations)                        verified-complete / lower-bound / provisional / budget / blocked buckets
    check_* (...)                              invariants: completeness, mass conservation, provenance, duplicates
    bbs(components)                            12 m stock cutting of the components whose geometry is established

Quantity rules (no exceptions):
  * unit weight kg/m = D^2 / 162 (D in mm), no early rounding; pi D^2 / 4 x 7850 is reported for QA only;
  * kg/m3, kg/m2 or kg/element ratios never create a quantity (`ratio_qa` only reports them);
  * a per-metre count gives a VERIFIED lower bound ceil(rate x distribution) and a CONVENTION count (+1 end bar,
    spacing <= 1000 / rate with a bar at both edges); the convention part is PROVISIONAL until the project states it;
  * a population is VERIFIED_COMPLETE only when every required component is COMPLETE or NOT_REQUIRED and its
    occurrence is established; one BLOCKED / PARTIAL / PROVISIONAL required component caps it at LOWER_BOUND;
  * a BLOCKED occurrence keeps every kg in audit only; nothing BLOCKED or PROVISIONAL enters the BBS.
Stdlib + engine.source.bbs_optimiser only; project-agnostic.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import bbs_optimiser as BB

POLICY_ID = "REBAR_MODEL_V1"
KG_FORMULA = "kg/m = D^2 / 162 (D in mm)"
COUNT_MODES = ("ABSOLUTE_COUNT", "BARS_PER_METRE", "SPACING_MM", "ONE_PER_OCCURRENCE", "UNKNOWN")
PART_KINDS = ("CORE", "EXTENSION", "HOOK", "ANCHORAGE", "LEG", "BEND", "LAP")
COMPLETE, PARTIAL, PROVISIONAL, BLOCKED, NOT_REQUIRED = "COMPLETE", "PARTIAL", "PROVISIONAL", "BLOCKED", "NOT_REQUIRED"
COMPONENT_STATES = (COMPLETE, PARTIAL, PROVISIONAL, BLOCKED, NOT_REQUIRED)
VC, LB, PROV, BUDGET, BLK, NIS = ("VERIFIED_COMPLETE", "VERIFIED_PARTIAL_LOWER_BOUND", "PROVISIONAL", "BUDGET",
                                  "BLOCKED", "NOT_IN_SCOPE")
OCC_STATES = ("ESTABLISHED", "PROVISIONAL", "BLOCKED", "NOT_REQUIRED")
PROVENANCE_FIELDS = ("drawing_sha256", "drawing", "locator", "raw", "normalised")
EPS = 1e-9


def kgm(d_mm) -> float:
    return d_mm * d_mm / 162.0


def kgm_density_qa(d_mm) -> float:
    """QA only: steel density 7850 kg/m3 x nominal area. Never a quantity basis."""
    return math.pi * d_mm * d_mm / 4.0 * 7850.0 / 1e6


# ---------------------------------------------------------------------------------------------------- counts
def bar_count(mode, value=None, distribution_m=None, *, basis="") -> dict:
    """Explicit count. Returns verified (lower-bound) and convention counts; never infers one mode from another."""
    if mode not in COUNT_MODES:
        raise ValueError(f"unknown count mode {mode}")
    out = {"mode": mode, "value": value, "distribution_m": distribution_m, "basis": basis}
    if mode == "ABSOLUTE_COUNT":
        if value is None or int(value) != value or value < 0:
            raise ValueError("ABSOLUTE_COUNT needs a non-negative integer")
        return dict(out, verified=int(value), convention=int(value), rule_id="COUNT_ABSOLUTE",
                    formula=f"n = {int(value)} (printed count)")
    if mode == "ONE_PER_OCCURRENCE":
        return dict(out, verified=1, convention=1, rule_id="COUNT_ONE", formula="n = 1")
    if mode in ("BARS_PER_METRE", "SPACING_MM"):
        if value is None or value <= 0 or distribution_m is None:
            return dict(out, verified=None, convention=None, rule_id="COUNT_UNRESOLVED",
                        formula="rate / spacing or distribution length missing")
        rate = value if mode == "BARS_PER_METRE" else 1000.0 / value
        s_mm = 1000.0 / rate
        d = max(distribution_m, 0.0)
        n_lo = math.ceil(rate * d - EPS)
        n_conv = math.ceil(d * 1000.0 / s_mm - EPS) + 1
        return dict(out, rate_per_m=rate, spacing_mm=s_mm, verified=n_lo, convention=n_conv,
                    rule_id="COUNT_PER_METRE_LB_PLUS_END_BAR",
                    formula=f"verified n = ceil({rate:g}/m x {d:.4f} m) = {n_lo}; convention n = ceil({d * 1000:.1f} / "
                            f"{s_mm:.2f}) + 1 = {n_conv} (spacing <= {s_mm:.2f} mm, a bar at both edges)")
    return dict(out, verified=None, convention=None, rule_id="COUNT_UNKNOWN", formula="count mode UNKNOWN")


# ---------------------------------------------------------------------------------------------------- lengths
def part(kind, length_m, state, rule, *, source=None, why=None) -> dict:
    if kind not in PART_KINDS:
        raise ValueError(kind)
    if state not in COMPONENT_STATES:
        raise ValueError(state)
    if length_m is not None and length_m < -EPS:
        raise ValueError("negative length")
    if state in (COMPLETE, PARTIAL, PROVISIONAL) and length_m is None:
        raise ValueError(f"{kind} part in state {state} needs a length")
    return {"kind": kind, "length_m": length_m, "state": state, "rule": rule, "source": source, "why": why}


def lap_parts(run_m, dia_mm, *, stock_m=BB.STOCK_M, lap_factor=None, lap_rule_id=None) -> dict:
    """Procurement laps of one continuous run: NOT_REQUIRED within the stock length, computed when the run exceeds
    it AND a lap authority (factor x D) is given, otherwise BLOCKED_LAP_METHOD. Laps are BBS length, never net."""
    if run_m is None:
        return {"state": BLOCKED, "laps": None, "lap_m": None, "rule": "BLOCKED_RUN_UNKNOWN", "pieces": None}
    if run_m <= stock_m + EPS:
        return {"state": NOT_REQUIRED, "laps": 0, "lap_m": 0.0, "rule": f"run {run_m:.3f} <= stock {stock_m} m",
                "pieces": [run_m]}
    if not lap_factor:
        return {"state": BLOCKED, "laps": None, "lap_m": None, "rule": "BLOCKED_LAP_METHOD", "pieces": None}
    lap = lap_factor * dia_mm / 1000.0
    pcs = BB.split_run(run_m, lap, stock_m)
    return {"state": COMPLETE, "laps": len(pcs) - 1, "lap_m": lap, "rule": f"{lap_rule_id}: {lap_factor} x D",
            "pieces": pcs}


# ---------------------------------------------------------------------------------------------------- component
def component(*, comp_id, population_id, element_type, occurrence_id, level, bar_role, dia_mm, count, parts,
              bar_shape="STRAIGHT", layer=None, direction=None, span=None, cover_rule_id=None, lap_rule_id=None,
              laps=None, source=None, interpretation_state="INTERPRETED", required=True, forced_state=None,
              why=None, formula=None, bbs_addition_m=0.0, bbs_addition_rule=None) -> dict:
    """One bar set. verified_kg = verified count x COMPLETE length parts; provisional_kg = the PROVISIONAL length
    parts plus the convention bars; audit_kg = what a BLOCKED component would weigh if its known parts were accepted."""
    k = kgm(dia_mm) if dia_mm else None
    nv, nc = (count or {}).get("verified"), (count or {}).get("convention")
    L_ok = sum(p["length_m"] for p in parts if p["state"] == COMPLETE)
    L_prov = sum(p["length_m"] for p in parts if p["state"] == PROVISIONAL)
    blocked_parts = [p for p in parts if p["state"] == BLOCKED]
    ver = prov = aud = 0.0
    if k is not None and nv is not None:
        ver = nv * L_ok * k
        prov = nv * L_prov * k + ((nc or nv) - nv) * (L_ok + L_prov) * k
    if forced_state in (BLOCKED, NOT_REQUIRED):
        state = forced_state
        aud, ver, prov = (ver + prov if forced_state == BLOCKED else 0.0), 0.0, 0.0
    elif nv is None or k is None:
        state = BLOCKED
    elif ver > 0 and not blocked_parts and L_prov == 0 and (nc or nv) == nv:
        state = COMPLETE
    elif ver > 0:
        state = PARTIAL
    elif prov > 0:
        state = PROVISIONAL
    else:
        state = BLOCKED
    if forced_state == PROVISIONAL and state in (COMPLETE, PARTIAL):
        prov, ver, state = prov + ver, 0.0, PROVISIONAL
    return {"comp_id": comp_id, "population_id": population_id, "element_type": element_type,
            "occurrence_id": occurrence_id, "level": level, "bar_role": bar_role, "layer": layer,
            "direction": direction, "span": span, "dia_mm": dia_mm, "count_mode": (count or {}).get("mode", "UNKNOWN"),
            "count": count, "rate_per_m": (count or {}).get("rate_per_m"),
            "spacing_mm": (count or {}).get("spacing_mm"), "bar_shape": bar_shape, "parts": parts,
            "verified_length_m": L_ok, "provisional_length_m": L_prov,
            "blocked_parts": [p["kind"] + ":" + (p["why"] or p["rule"]) for p in blocked_parts],
            "total_length_verified_m": (nv or 0) * L_ok if state in (COMPLETE, PARTIAL) else 0.0,
            "unit_weight_kg_m": k, "weight_formula": KG_FORMULA, "verified_kg": ver, "provisional_kg": prov,
            "audit_kg": aud, "net_kg": ver + prov, "cover_rule_id": cover_rule_id, "lap_rule_id": lap_rule_id,
            "laps": laps, "bbs_addition_m": bbs_addition_m, "bbs_addition_rule": bbs_addition_rule,
            "source": source or {}, "interpretation_state": interpretation_state,
            "required": required, "state": state, "why": why, "formula": formula}


def blocked_component(*, comp_id, population_id, element_type, occurrence_id, level, bar_role, why, source=None,
                      required=True, audit_kg=0.0, dia_mm=None, interpretation_state="BLOCKED_INTERPRETATION") -> dict:
    c = component(comp_id=comp_id, population_id=population_id, element_type=element_type,
                  occurrence_id=occurrence_id, level=level, bar_role=bar_role, dia_mm=dia_mm, count=None, parts=[],
                  source=source, interpretation_state=interpretation_state, required=required, forced_state=BLOCKED,
                  why=why)
    c["audit_kg"] = audit_kg or 0.0
    return c


def not_required(*, comp_id, population_id, element_type, occurrence_id, level, bar_role, why, source=None) -> dict:
    return component(comp_id=comp_id, population_id=population_id, element_type=element_type,
                     occurrence_id=occurrence_id, level=level, bar_role=bar_role, dia_mm=None, count=None, parts=[],
                     source=source, required=False, forced_state=NOT_REQUIRED, why=why,
                     interpretation_state="NOT_REQUIRED")


# ---------------------------------------------------------------------------------------------------- population
def population(*, pop_id, element_type, occurrence_id, level, occurrence_state, components, source=None,
               occurrence_why=None, release_override=None) -> dict:
    if occurrence_state not in OCC_STATES:
        raise ValueError(occurrence_state)
    ver = sum(c["verified_kg"] for c in components)
    prov = sum(c["provisional_kg"] for c in components)
    aud = sum(c["audit_kg"] for c in components)
    req = [c for c in components if c["required"]]
    missing = [c["comp_id"] for c in req if c["state"] not in (COMPLETE, NOT_REQUIRED)]
    if occurrence_state == "NOT_REQUIRED":
        state = NIS
        aud, ver, prov = aud + ver + prov, 0.0, 0.0
    elif occurrence_state == "BLOCKED":
        state = BLK
        aud, ver, prov = aud + ver + prov, 0.0, 0.0
    elif occurrence_state == "PROVISIONAL":
        state = PROV if ver + prov > 0 else BLK
        prov, ver = prov + ver, 0.0
    elif not missing and ver > 0:
        state = VC
    elif ver > 0:
        state = LB
    elif prov > 0:
        state = PROV
    else:
        state = BLK
    bud = 0.0
    if release_override == BUDGET:
        state, bud, prov, ver = BUDGET, ver + prov, 0.0, 0.0
    elif release_override:
        state = release_override
    return {"pop_id": pop_id, "element_type": element_type, "occurrence_id": occurrence_id, "level": level,
            "occurrence_state": occurrence_state, "occurrence_why": occurrence_why, "release_state": state,
            "verified_complete_kg": ver if state == VC else 0.0, "lower_bound_kg": ver if state == LB else 0.0,
            "provisional_kg": prov if state in (VC, LB, PROV) else 0.0, "budget_kg": bud,
            "audit_kg": aud, "net_kg": ver + prov + bud,
            "missing_components": missing, "components": [c["comp_id"] for c in components],
            "component_states": dict(Counter(c["state"] for c in components)), "source": source or {}}


def totals(populations) -> dict:
    out = defaultdict(float)
    n = Counter()
    for p in populations:
        for f in ("verified_complete_kg", "lower_bound_kg", "provisional_kg", "budget_kg", "audit_kg"):
            out[f] += p[f]
        n[p["release_state"]] += 1
    res = {k: v for k, v in out.items()}
    res["populations_by_state"] = dict(n)
    res["project_final_rebar_total"] = ("ESTABLISHED" if populations and set(n) <= {VC, NIS} else
                                        "NOT YET ESTABLISHED")
    return res


def ratio_qa(kg, *, volume_m3=None, area_m2=None, n_elements=None) -> dict:
    """Reasonableness diagnostics only - the output never feeds a quantity."""
    return {"use": "QA_ONLY", "kg_per_m3": kg / volume_m3 if volume_m3 else None,
            "kg_per_m2": kg / area_m2 if area_m2 else None, "kg_per_element": kg / n_elements if n_elements else None}


# ---------------------------------------------------------------------------------------------------- invariants
def check_completeness(rc_occurrences, populations, components) -> list:
    """rc_occurrences: ids of reinforced-concrete occurrences admitted. Every one needs a population record; every
    required component a state; a VERIFIED_COMPLETE population no missing required component."""
    v = []
    have = Counter(p["occurrence_id"] for p in populations)
    for o in rc_occurrences:
        if not have.get(o):
            v.append(("OCCURRENCE_WITHOUT_POPULATION", o))
    byp = defaultdict(list)
    for c in components:
        if c["state"] not in COMPONENT_STATES:
            v.append(("COMPONENT_WITHOUT_STATE", c["comp_id"]))
        byp[c["population_id"]].append(c)
    for p in populations:
        cs = byp.get(p["pop_id"], [])
        if not cs:
            v.append(("POPULATION_WITHOUT_COMPONENT", p["pop_id"]))
        for c in cs:
            if c["state"] == COMPLETE and c["verified_kg"] <= EPS:
                v.append(("COMPLETE_WITHOUT_QUANTITY", c["comp_id"]))
        bad = [c["comp_id"] for c in cs if c["required"] and c["state"] not in (COMPLETE, NOT_REQUIRED)]
        if p["release_state"] == VC and (bad or p["occurrence_state"] != "ESTABLISHED"):
            v.append(("INCOMPLETE_POPULATION_MARKED_COMPLETE", p["pop_id"]))
        if p["release_state"] == VC and any(c["provisional_kg"] > EPS for c in cs):
            v.append(("PROVISIONAL_COMPONENT_IN_COMPLETE_POPULATION", p["pop_id"]))
    return v


def check_duplicates(components, populations) -> list:
    v = []
    ids = Counter(c["comp_id"] for c in components)
    v += [("DUPLICATE_COMPONENT_ID", k) for k, n in ids.items() if n > 1]
    sig = defaultdict(set)
    for c in components:
        if c["state"] in (BLOCKED, NOT_REQUIRED):
            continue
        key = (c["occurrence_id"], c["bar_role"], c["layer"], c["direction"], c["span"], c["dia_mm"])
        sig[key].add(c["population_id"])
        if len(sig[key]) > 1:
            v.append(("COMPONENT_IN_TWO_POPULATIONS", str(key)))
    seen = Counter()
    for c in components:
        if c["state"] in (BLOCKED, NOT_REQUIRED):
            continue
        seen[(c["occurrence_id"], c["bar_role"], c["layer"], c["direction"], c["span"], c["dia_mm"])] += 1
    v += [("DUPLICATE_COMPONENT", str(k)) for k, n in seen.items() if n > 1]
    occ = Counter(p["occurrence_id"] for p in populations if p.get("occurrence_id"))
    v += [("DUPLICATE_OCCURRENCE", k) for k, n in occ.items() if n > 1]
    return v


def check_provenance(components) -> list:
    v = []
    for c in components:
        if c["net_kg"] <= EPS and c["state"] != BLOCKED:
            continue
        s = c["source"] or {}
        miss = [f for f in PROVENANCE_FIELDS if not s.get(f)]
        if miss:
            v.append(("MISSING_PROVENANCE", c["comp_id"], miss))
        if c["net_kg"] > EPS and not c.get("formula"):
            v.append(("MISSING_FORMULA", c["comp_id"]))
        if c["net_kg"] > EPS and not c.get("cover_rule_id"):
            v.append(("MISSING_COVER_RULE", c["comp_id"]))
    return v


def check_mass(components, populations, trade=None, bbs_result=None, tol=1e-6) -> list:
    v = []
    byp = defaultdict(lambda: [0.0, 0.0, 0.0])
    for c in components:
        for i, f in enumerate(("verified_kg", "provisional_kg", "audit_kg")):
            if c[f] < -tol:
                v.append(("NEGATIVE_KG", c["comp_id"], f))
            byp[c["population_id"]][i] += c[f]
    for p in populations:
        cv, cp, ca = byp.get(p["pop_id"], (0.0, 0.0, 0.0))
        pv = p["verified_complete_kg"] + p["lower_bound_kg"]
        if p["release_state"] in (BLK, NIS):
            if abs((cv + cp + ca) - p["audit_kg"]) > tol * max(1, ca):
                v.append(("POPULATION_AUDIT_MISMATCH", p["pop_id"]))
        elif p["release_state"] == BUDGET:
            if abs((cv + cp) - p["budget_kg"]) > tol * max(1, cp):
                v.append(("POPULATION_BUDGET_MISMATCH", p["pop_id"]))
        elif p["occurrence_state"] == "PROVISIONAL":
            if abs((cv + cp) - p["provisional_kg"]) > tol * max(1, cp):
                v.append(("POPULATION_PROVISIONAL_MISMATCH", p["pop_id"]))
        elif abs(cv - pv) > tol * max(1.0, cv) or abs(cp - p["provisional_kg"]) > tol * max(1.0, cp):
            v.append(("POPULATION_NET_MISMATCH", p["pop_id"]))
    if trade is not None:
        t = totals(populations)
        for f in ("verified_complete_kg", "lower_bound_kg", "provisional_kg", "audit_kg"):
            if abs(t.get(f, 0.0) - trade.get(f, 0.0)) > tol * max(1.0, t.get(f, 0.0)):
                v.append(("TRADE_TOTAL_MISMATCH", f))
    if bbs_result is not None:
        tot = bbs_result["total"]
        if tot["used_kg"] + tol < tot["net_kg"]:
            v.append(("BBS_USED_BELOW_NET", tot["used_kg"], tot["net_kg"]))
        if tot["purchased_kg"] + tol < tot["used_kg"]:
            v.append(("BBS_PURCHASED_BELOW_USED",))
        if abs(tot["waste_kg"] - (tot["purchased_kg"] - tot["used_kg"])) > 1e-3:
            v.append(("BBS_WASTE_NOT_PURCHASED_MINUS_USED",))
        if bbs_result.get("ineligible_included"):
            v.append(("BBS_INCLUDES_INELIGIBLE", bbs_result["ineligible_included"]))
    return v


def check_source_consistency(components) -> list:
    """The typed component must say what its source says: diameter, printed count and per-metre semantics."""
    v = []
    for c in components:
        if c["state"] in (BLOCKED, NOT_REQUIRED):
            continue
        n = (c["source"] or {}).get("normalised")
        if not isinstance(n, dict):
            continue
        if n.get("dia_mm") is not None and c["dia_mm"] is not None and int(n["dia_mm"]) != int(c["dia_mm"]):
            v.append(("DIAMETER_DIFFERS_FROM_SOURCE", c["comp_id"]))
        per_m = bool(n.get("per_m")) or "PER_METRE" in str(n.get("semantics", ""))
        if per_m and c["count_mode"] not in ("BARS_PER_METRE", "SPACING_MM"):
            v.append(("PER_METRE_READ_AS_COUNT", c["comp_id"]))
        if not per_m and n.get("count") is not None and c["count_mode"] == "ABSOLUTE_COUNT" and \
                int(n["count"]) != (c["count"] or {}).get("verified"):
            v.append(("COUNT_DIFFERS_FROM_SOURCE", c["comp_id"]))
    return v


def check_bbs_eligibility(bbs_result, components, pop_state) -> list:
    byid = {c["comp_id"]: c for c in components}
    return [("BBS_INCLUDES_INELIGIBLE", i) for i in bbs_result["included"]
            if i not in byid or not bbs_eligible(byid[i], pop_state.get(byid[i]["population_id"]))]


def check_conflicts(populations, conflict_keys, key_of) -> list:
    """An occurrence whose schedule key is a SOURCE_CONFLICT must stay BLOCKED (no row selected)."""
    return [("CONFLICT_KEY_RELEASED", p["pop_id"]) for p in populations
            if key_of(p) in conflict_keys and p["release_state"] != BLK]


# ---------------------------------------------------------------------------------------------------- BBS
def bbs_eligible(c, population_state) -> bool:
    return (c["state"] in (COMPLETE, PARTIAL) and population_state in (VC, LB) and c["verified_length_m"] > EPS
            and (c["count"] or {}).get("verified"))


def bbs(components, pop_state, *, stock_m=BB.STOCK_M, lap_factor=None, lap_rule_id=None) -> dict:
    """12 m stock cutting of the verified geometry of eligible components (net = verified kg). Laps for runs longer
    than the stock come from the lap authority; without it those runs are excluded (BLOCKED_LAP_METHOD)."""
    by_d = defaultdict(list)
    net = defaultdict(float)
    excluded, used_ids = [], []
    for c in components:
        ps = pop_state.get(c["population_id"])
        if not bbs_eligible(c, ps):
            if c["net_kg"] > EPS or c["audit_kg"] > EPS:
                excluded.append({"comp_id": c["comp_id"], "state": c["state"], "population_state": ps})
            continue
        L, n, d = c["verified_length_m"], c["count"]["verified"], c["dia_mm"]
        L += c.get("bbs_addition_m") or 0.0                  # procurement-only additions with an authority (splices)
        lp = lap_parts(L, d, stock_m=stock_m, lap_factor=lap_factor, lap_rule_id=lap_rule_id)
        if lp["state"] == BLOCKED:
            excluded.append({"comp_id": c["comp_id"], "state": "BLOCKED_LAP_METHOD", "population_state": ps})
            continue
        used_ids.append(c["comp_id"])
        net[d] += c["verified_kg"]
        for i, p in enumerate(lp["pieces"]):
            by_d[d].append((f"{c['comp_id']}#{i}", p, n))
    res = {}
    for d, pcs in sorted(by_d.items()):
        r = BB.cut(pcs, stock_m)
        k = kgm(d)
        res[d] = dict(r, kg_per_m=k, net_kg=net[d], used_kg=r["used_m"] * k, purchased_kg=r["purchased_m"] * k,
                      waste_kg=(r["purchased_m"] - r["used_m"]) * k)
    tot = {f: sum(v[f] for v in res.values()) for f in ("net_kg", "used_kg", "purchased_kg", "waste_kg")}
    tot["waste_pct"] = 100.0 * tot["waste_kg"] / tot["purchased_kg"] if tot["purchased_kg"] else 0.0
    return {"policy": POLICY_ID, "stock_m": stock_m, "by_dia": res, "total": tot, "included": used_ids,
            "excluded": excluded, "ineligible_included": [],
            "rule": "only COMPLETE / PARTIAL components of VERIFIED_COMPLETE / LOWER_BOUND populations, verified "
                    "length and verified count; laps only where a run exceeds the stock and a lap authority exists"}


# ---------------------------------------------------------------------------------------------------- project gate
PROJECT_STATES = ("FINAL_ESTABLISHED", "LOWER_BOUND_ONLY", "PROVISIONAL", "BLOCKED")


def project_status(populations, components, *, checks_pass, source_conflicts=0) -> dict:
    """PROJECT_REBAR_STATUS. FINAL_ESTABLISHED only when every required population is terminal AND VERIFIED_COMPLETE
    (or NOT_IN_SCOPE), no source conflict, no blocked required component, mass conservation and provenance pass.
    Otherwise LOWER_BOUND_ONLY when a verified lower bound exists, PROVISIONAL when only provisional weight exists,
    BLOCKED when nothing is released. A single 'total rebar' figure may only be shown when FINAL_ESTABLISHED."""
    req = [p for p in populations if p["release_state"] != NIS]
    terminal = all(p["release_state"] in (VC, LB, PROV, BUDGET, BLK) for p in req)
    blocked_req = [c["comp_id"] for c in components if c["required"] and c["state"] == BLOCKED
                   and next((p for p in populations if p["pop_id"] == c["population_id"]), {}).get("release_state") != NIS]
    not_complete = [p["pop_id"] for p in req if p["release_state"] != VC]
    reasons = []
    if not terminal:
        reasons.append("non-terminal population state")
    if not_complete:
        reasons.append(f"{len(not_complete)} of {len(req)} required populations are not VERIFIED_COMPLETE")
    if blocked_req:
        reasons.append(f"{len(blocked_req)} required components BLOCKED")
    if source_conflicts:
        reasons.append(f"{source_conflicts} source conflicts open")
    if not checks_pass:
        reasons.append("an invariant check (mass / provenance / completeness) fails")
    final = bool(req) and not reasons
    ver = sum(p["verified_complete_kg"] + p["lower_bound_kg"] for p in populations)
    prov = sum(p["provisional_kg"] for p in populations)
    state = ("FINAL_ESTABLISHED" if final else "LOWER_BOUND_ONLY" if ver > EPS else "PROVISIONAL" if prov > EPS
             else "BLOCKED")
    return {"PROJECT_REBAR_STATUS": state, "PROJECT_REBAR_FINAL_ESTABLISHED": final,
            "PROJECT_REBAR_PROCUREMENT_READY": final, "required_populations": len(req),
            "verified_complete_populations": len(req) - len(not_complete),
            "population_completeness_pct": 100.0 * (len(req) - len(not_complete)) / len(req) if req else 0.0,
            "blocked_required_components": len(blocked_req), "source_conflicts": source_conflicts,
            "checks_pass": checks_pass, "reasons_not_final": reasons,
            "single_total_allowed": final,
            "rule": "FINAL_ESTABLISHED = 100 % required populations terminal AND VERIFIED_COMPLETE / NOT_REQUIRED AND no "
                    "source conflict AND no blocked required component AND mass + provenance pass"}


def known_components_bbs(bbs_result, status) -> dict:
    """The BBS of the KNOWN (eligible) components, named so that it can never be read as the project's purchase
    quantity while the project gate is not FINAL_ESTABLISHED."""
    t = bbs_result["total"]
    final = status["PROJECT_REBAR_FINAL_ESTABLISHED"]
    return {"KNOWN_COMPONENTS_NET_KG": t["net_kg"], "KNOWN_COMPONENTS_BBS_USED_KG": t["used_kg"],
            "KNOWN_COMPONENTS_BBS_PURCHASED_KG": t["purchased_kg"], "KNOWN_COMPONENTS_BBS_WASTE_KG": t["waste_kg"],
            "KNOWN_COMPONENTS_BBS_WASTE_PCT": t["waste_pct"],
            "PROJECT_REBAR_FINAL_ESTABLISHED": final, "PROJECT_REBAR_PROCUREMENT_READY": final,
            "is_project_procurement_quantity": final,
            "label": ("project procurement quantity" if final else
                      "audit BBS of the known components only - NOT the villa's reinforcement procurement requirement "
                      f"(project status {status['PROJECT_REBAR_STATUS']})")}
