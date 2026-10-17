"""RELEASE MODEL V2 (RELEASE_V2) - one quantity, one explicit release state, derived (never asserted) confidence.

V1 (release_model.TWO_LAYER_RELEASE_V1) stays untouched and is carried beside V2 for one migration window:
technical.class, commercial.class and procurement_eligible_v1 are copied, never rewritten.

    release_v2(...)  -> {release_state, population_complete, upstream_complete, procurement_eligible_v2,
                         release_reason, blocking_refs, evidence_grade, weakest_dependency, confidence_reasons,
                         qty_verified, qty_lower_bound, qty_provisional, qty_budget, qty_audit, display, ...}
    evidence(components)            -> weakest-link categorical grade
    cap(state, ceiling)             -> the less certain of two states
    migration_row(code, v1, v2)     -> one V1 -> V2 diff record
    totals(rows)                    -> verified / lower-bound / provisional / budget / blocked sums

States (ordered from most to least certain; NOT_IN_SCOPE is outside the order):
  VERIFIED_COMPLETE             technically valid, upstream complete, population complete -> technical total,
                                procurement eligible
  VERIFIED_PARTIAL_LOWER_BOUND  the measured part is valid, the population is known incomplete -> shown ">= q",
                                LOWER BOUND; never procurement eligible without an explicit owner approval
  PROVISIONAL                   fallback / inference / code method / upstream under review -> commercial view only;
                                procurement only with owner approval
  BUDGET                        allowance; never technical, never procurement eligible by default
  BLOCKED                       source missing / conflicting / unread / semantic conflict -> no final quantity
  NOT_IN_SCOPE                  explicit scope decision

Rules (each is a test):
  1. a quantity is never more certain than its weakest REQUIRED dependency (evidence BLOCKED -> BLOCKED,
     upstream REVIEW -> at most PROVISIONAL, population incomplete -> at most LOWER BOUND);
  2. confidence is derived from named evidence components; no default "H";
  3. procurement_eligible_v2 = VERIFIED_COMPLETE, or an explicit owner approval of a LOWER BOUND / PROVISIONAL;
     BUDGET / BLOCKED / NOT_IN_SCOPE never;
  4. a blocked quantity keeps its number only in qty_audit (never in a total).
Stdlib only, project-agnostic.
"""

from __future__ import annotations

from collections import defaultdict

POLICY_ID = "RELEASE_V2"
VERIFIED_COMPLETE = "VERIFIED_COMPLETE"
LOWER_BOUND = "VERIFIED_PARTIAL_LOWER_BOUND"
PROVISIONAL = "PROVISIONAL"
BUDGET = "BUDGET"
BLOCKED = "BLOCKED"
NOT_IN_SCOPE = "NOT_IN_SCOPE"
STATES = (VERIFIED_COMPLETE, LOWER_BOUND, PROVISIONAL, BUDGET, BLOCKED, NOT_IN_SCOPE)
ORDER = {VERIFIED_COMPLETE: 0, LOWER_BOUND: 1, PROVISIONAL: 2, BUDGET: 3, BLOCKED: 4}

# evidence grades (weakest wins); NOT_APPLICABLE components are ignored
HIGH, MEDIUM, LOW, GRADE_BLOCKED, NA = "HIGH", "MEDIUM", "LOW", "BLOCKED", "NOT_APPLICABLE"
GRADE_ORDER = {HIGH: 0, MEDIUM: 1, LOW: 2, GRADE_BLOCKED: 3}
COMPONENTS = ("source_identity", "unit_frame", "geometry", "semantic_identity", "trade_region", "dimension_height",
              "schedule", "population_completeness", "rule_authority", "upstream_status")

# V1 class families (release_model V1 vocabulary)
V1_TECH_MEASURED = ("MEASURED", "DERIVED", "RASTER_DERIVED", "SOURCE_RULE", "OWNER_PROJECT_FACT")
V1_TECH_RULE = ("URBAN_STANDARD", "CODE_METHOD")
V1_TECH_OUT = ("REVIEW", "BLOCKED", "BLOCKED_SOURCE_CONFLICT", "NOT_IN_SOURCE", "PENDING")
V1_PROVISIONAL = ("PROVISIONAL_SOURCE_DERIVED", "PROVISIONAL_SOURCE_RANGE", "PROVISIONAL_GEOMETRIC_INFERENCE",
                  "PROVISIONAL_CODE_METHOD", "PROVISIONAL_URBAN_FALLBACK", "PROVISIONAL_OWNER_METHOD",
                  "OWNER_APPROVED_PROVISIONAL")

# upstream (room / occurrence / population) status -> the most certain state it allows downstream
UPSTREAM_CAP = {"COMPLETE": VERIFIED_COMPLETE, "COMPUTED": VERIFIED_COMPLETE, "CERTIFIED": VERIFIED_COMPLETE,
                "PARTIAL": LOWER_BOUND, "REVIEW": PROVISIONAL, "COMPUTED_REVIEW": PROVISIONAL,
                "BLOCKED": BLOCKED, "UNKNOWN": BLOCKED, None: BLOCKED}


def cap(state, ceiling):
    """The less certain of two ordered states (NOT_IN_SCOPE is never capped and never caps)."""
    if state == NOT_IN_SCOPE or ceiling in (None, NOT_IN_SCOPE):
        return state
    return state if ORDER[state] >= ORDER[ceiling] else ceiling


def upstream_cap(status):
    return UPSTREAM_CAP.get(status, BLOCKED)


def evidence(components: dict) -> dict:
    """components: {name: (grade, reason)} -> the weakest grade wins; reasons of every non-HIGH component listed."""
    if not components:
        return {"evidence_grade": GRADE_BLOCKED, "weakest_dependency": None,
                "confidence_reasons": ["no evidence components recorded"]}
    used = {k: v for k, v in components.items() if v[0] != NA}
    if not used:
        return {"evidence_grade": NA, "weakest_dependency": None, "confidence_reasons": []}
    for k, (g, _) in used.items():
        if g not in GRADE_ORDER:
            raise ValueError(f"unknown evidence grade {g!r} for {k}")
    weakest = max(sorted(used), key=lambda k: GRADE_ORDER[used[k][0]])
    return {"evidence_grade": used[weakest][0], "weakest_dependency": weakest,
            "confidence_reasons": [f"{k}: {g} - {r}" for k, (g, r) in sorted(used.items()) if g != HIGH]}


def _f(v):
    return None if v is None else round(float(v), 6)


def release_v2(*, technical_class, measured_qty, commercial=None, population_complete=True, upstream_status="COMPLETE",
               components=None, owner_approved_procurement=False, not_in_scope=False, blocking_refs=(),
               quantity_rule_dependency=True, v1=None) -> dict:
    """technical_class: the V1 technical class; measured_qty: the geometric / derived number (kept in qty_audit even
    when blocked); commercial: the V1 commercial record (class, qty, low, high, method ...); components: evidence
    components {name: (grade, reason)}; quantity_rule_dependency: False when the rule authority only sets the
    specification (material) and not the quantity."""
    comps = dict(components or {})
    spec = comps.pop("rule_authority") if not quantity_rule_dependency and "rule_authority" in comps else None
    ev = evidence(comps)
    reasons, refs = [], list(blocking_refs)
    com = commercial or {}
    ccls = com.get("class")

    if not_in_scope:
        state = NOT_IN_SCOPE
        reasons.append("explicit scope decision")
    elif ev["evidence_grade"] == GRADE_BLOCKED:
        state = BLOCKED
        reasons.append(f"required dependency BLOCKED: {ev['weakest_dependency']}")
    elif technical_class in V1_TECH_OUT or measured_qty is None:
        if ccls == "BUDGET_ESTIMATE" and com.get("qty") is not None:
            state = BUDGET
            reasons.append("allowance only (V1 BUDGET_ESTIMATE)")
        elif ccls in V1_PROVISIONAL and com.get("qty") is not None:
            state = PROVISIONAL
            reasons.append(f"V1 technical {technical_class}; commercial {ccls}")
        elif technical_class == "REVIEW" and measured_qty is not None:
            state = PROVISIONAL
            reasons.append("measured, but the upstream object is under review")
        else:
            state = BLOCKED
            reasons.append(f"V1 technical {technical_class}; no labelled provisional basis")
    elif technical_class == "PARTIAL":
        state = LOWER_BOUND
        reasons.append("V1 PARTIAL: the measured part of an incomplete population")
    elif technical_class in V1_TECH_RULE and quantity_rule_dependency:
        state = PROVISIONAL
        reasons.append(f"quantity depends on an Urban / code rule ({technical_class}), not on project source")
    else:
        state = VERIFIED_COMPLETE
    up = upstream_cap(upstream_status)
    if state not in (NOT_IN_SCOPE,) and ORDER.get(up, 4) > ORDER.get(state, 0):
        reasons.append(f"capped by upstream status {upstream_status}")
        state = cap(state, up)
    if population_complete is False and state == VERIFIED_COMPLETE:
        state = LOWER_BOUND
        reasons.append("population incomplete")
    if ev["evidence_grade"] in (MEDIUM, LOW) and state == VERIFIED_COMPLETE and ev["weakest_dependency"] in (
            "semantic_identity", "trade_region", "dimension_height", "rule_authority"):
        state = PROVISIONAL
        reasons.append(f"evidence {ev['evidence_grade']} on {ev['weakest_dependency']}")

    q = _f(measured_qty)
    cq = _f(com.get("qty"))
    out = {"policy": POLICY_ID, "release_state": state,
           "population_complete": population_complete, "upstream_complete": up == VERIFIED_COMPLETE,
           "upstream_status": upstream_status,
           "procurement_eligible_v2": state == VERIFIED_COMPLETE or (
               owner_approved_procurement and state in (LOWER_BOUND, PROVISIONAL)),
           "owner_approved_procurement": bool(owner_approved_procurement),
           "release_reason": "; ".join(reasons) or "all required evidence present; population complete",
           "blocking_refs": refs, **ev,
           "specification_authority": None if spec is None else {"grade": spec[0], "reason": spec[1]},
           "qty_verified": q if state == VERIFIED_COMPLETE else None,
           "qty_lower_bound": q if state == LOWER_BOUND else None,
           "qty_provisional": (q if q is not None else cq) if state == PROVISIONAL else None,
           "qty_budget": cq if state == BUDGET else None,
           "qty_audit": q if state in (BLOCKED, NOT_IN_SCOPE) else None}
    out["display"] = {VERIFIED_COMPLETE: f"{q}", LOWER_BOUND: f">= {q} (LOWER BOUND)",
                      PROVISIONAL: f"{out['qty_provisional']} (PROVISIONAL)", BUDGET: f"{cq} (BUDGET)",
                      BLOCKED: "BLOCKED", NOT_IN_SCOPE: "NOT IN SCOPE"}[state]
    if v1 is not None:
        out["technical_class_v1"] = (v1.get("technical") or {}).get("class")
        out["commercial_class_v1"] = (v1.get("commercial") or {}).get("class")
        out["procurement_eligible_v1"] = (v1.get("commercial") or {}).get("procurement_eligible")
        out["confidence_v1"] = (v1.get("commercial") or {}).get("confidence")
    return out


def migration_row(code, v1, v2, **extra) -> dict:
    t, c = (v1 or {}).get("technical") or {}, (v1 or {}).get("commercial") or {}
    in_tech_v1 = bool(t.get("in_total"))
    proc_v1 = bool(c.get("procurement_eligible"))
    in_ver_v2 = v2["release_state"] == VERIFIED_COMPLETE
    changed = in_tech_v1 != in_ver_v2 or proc_v1 != v2["procurement_eligible_v2"]
    return {"code": code, "v1_technical_class": t.get("class"), "v1_in_technical_total": in_tech_v1,
            "v1_commercial_class": c.get("class"), "v1_procurement_eligible": proc_v1,
            "v1_confidence": c.get("confidence"), "v2_release_state": v2["release_state"],
            "v2_in_verified_total": in_ver_v2, "v2_procurement_eligible": v2["procurement_eligible_v2"],
            "v2_evidence_grade": v2["evidence_grade"], "v2_weakest_dependency": v2["weakest_dependency"],
            "v2_release_reason": v2["release_reason"], "status_changed": changed, **extra}


def totals(rows, key="v2") -> dict:
    acc = defaultdict(lambda: defaultdict(float))
    for r in rows:
        v = r[key] if key else r
        u = r.get("unit", "?")
        for f, name in (("qty_verified", "verified"), ("qty_lower_bound", "lower_bound"),
                        ("qty_provisional", "provisional"), ("qty_budget", "budget"), ("qty_audit", "blocked_audit")):
            if v.get(f) is not None:
                acc[u][name] += v[f]
    return {u: {k: round(x, 3) for k, x in d.items()} for u, d in sorted(acc.items())}
