"""ENGINEERING FLAG MODEL + COMPONENT RELEASE (generic, project-independent).

An ENGINEERING_FLAG records one open engineering question about a source: what is in conflict or missing, how the
engine currently interprets it, which facts it touches, and what that does to quantity release. A flag never deletes
a quantity: it changes the release state of the COMPONENTS that depend on the facts it touches, so independently
known components stay releasable (lower bound / verified) while the uncertain component is blocked.

Status lifecycle (history is append-only; a resolved flag keeps every earlier state):

    OPEN -> PROVISIONAL_INTERPRETATION -> SENT_TO_CONSULTANT -> ANSWERED -> RESOLVED
    any state -> SUPERSEDED

No project data lives here. Stdlib only.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict

POLICY_ID = "ENGINEERING_FLAG_V1"

OPEN = "OPEN"
PROVISIONAL = "PROVISIONAL_INTERPRETATION"
SENT = "SENT_TO_CONSULTANT"
ANSWERED = "ANSWERED"
RESOLVED = "RESOLVED"
SUPERSEDED = "SUPERSEDED"
STATUSES = (OPEN, PROVISIONAL, SENT, ANSWERED, RESOLVED, SUPERSEDED)
TRANSITIONS = {OPEN: {PROVISIONAL, SENT, ANSWERED, RESOLVED, SUPERSEDED},
               PROVISIONAL: {SENT, ANSWERED, RESOLVED, SUPERSEDED, OPEN},
               SENT: {ANSWERED, SUPERSEDED},
               ANSWERED: {RESOLVED, SENT, SUPERSEDED},
               RESOLVED: {SUPERSEDED},
               SUPERSEDED: set()}
OPEN_STATES = frozenset({OPEN, PROVISIONAL, SENT, ANSWERED})

ISSUE_TYPES = ("SOURCE_CONFLICT", "RULE_GAP", "MISSING_DIMENSION", "MISSING_SCHEDULE", "UNBOUND_OCCURRENCE",
               "AMBIGUOUS_APPLICABILITY", "MISSING_DETAIL", "UNIT_CONFLICT", "REVISION_CONFLICT",
               "ENGINEERING_METHOD_REQUIRED")
SEVERITIES = ("HIGH", "MEDIUM", "LOW")
DISCIPLINES = {"STRUCTURAL": "STR", "ARCHITECTURAL": "ARC", "MEP": "MEP"}
TRADES = ("CONCRETE", "REINFORCEMENT", "FORMWORK", "MASONRY", "FINISHES", "OTHER")

# release effect of an OPEN flag on each component that depends on a touched fact (strongest wins)
VERIFIED = "VERIFIED"
PROVISIONAL_VALUE = "PROVISIONAL"        # value taken from the stronger authority; releasable as provisional
LOWER_BOUND = "LOWER_BOUND"              # the proven part is releasable as a lower bound
AUDIT_ONLY = "AUDIT_ONLY"                # shown for audit, never totalled
BLOCKED = "BLOCKED"
NO_QUANTITY_IMPACT = "NO_QUANTITY_IMPACT"
RELEASE_EFFECTS = (VERIFIED, PROVISIONAL_VALUE, LOWER_BOUND, AUDIT_ONLY, BLOCKED, NO_QUANTITY_IMPACT)
_RANK = {NO_QUANTITY_IMPACT: 0, VERIFIED: 0, PROVISIONAL_VALUE: 1, LOWER_BOUND: 2, AUDIT_ONLY: 3, BLOCKED: 4}

FIELDS = ("flag_id", "flag_key", "discipline", "trade", "element_type", "element_id", "element_ids", "floor",
          "source_refs", "issue_type", "issue_summary", "source_a", "source_b", "current_interpretation",
          "interpretation_authority", "affected_facts", "release_effect", "quantity_affected", "unit", "severity",
          "question_for_engineer", "where_to_check", "answer_options", "status", "resolution", "resolved_by",
          "resolution_source", "resolved_at", "project_specific", "generic_rule_candidate", "detector",
          "history", "project_id", "drawing_revision", "context")


def flag_key(project_id, detector, element_type, element_id, subject):
    """Stable content key (claims and later rounds refer to this, not to the display number)."""
    raw = json.dumps([project_id, detector, element_type, element_id, subject], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_flag(*, project_id, drawing_revision, detector, discipline, trade, element_type, element_id, issue_type,
              issue_summary, subject=None, element_ids=None, floor=None, source_refs=(), source_a=None, source_b=None,
              current_interpretation=None, interpretation_authority=None, affected_facts=(), release_effect=BLOCKED,
              quantity_affected=None, unit=None, severity="MEDIUM", question_for_engineer=None, where_to_check=None,
              answer_options=(), status=OPEN, context=None, generic_rule_candidate=None):
    if issue_type not in ISSUE_TYPES:
        raise ValueError(f"issue_type {issue_type}")
    if discipline not in DISCIPLINES:
        raise ValueError(f"discipline {discipline}")
    if severity not in SEVERITIES or status not in (OPEN, PROVISIONAL) or release_effect not in RELEASE_EFFECTS:
        raise ValueError("severity / initial status / release_effect")
    trades = [trade] if isinstance(trade, str) else list(trade)
    if any(t not in TRADES for t in trades):
        raise ValueError(f"trade {trade}")
    return {"flag_id": None, "flag_key": flag_key(project_id, detector, element_type, element_id, subject),
            "discipline": discipline, "trade": trades, "element_type": element_type, "element_id": element_id,
            "element_ids": list(element_ids or [element_id]), "floor": floor, "source_refs": list(source_refs),
            "issue_type": issue_type, "issue_summary": issue_summary, "source_a": source_a, "source_b": source_b,
            "current_interpretation": current_interpretation, "interpretation_authority": interpretation_authority,
            "affected_facts": list(affected_facts), "release_effect": release_effect,
            "quantity_affected": quantity_affected, "unit": unit, "severity": severity,
            "question_for_engineer": question_for_engineer, "where_to_check": where_to_check,
            "answer_options": list(answer_options), "status": status, "resolution": None, "resolved_by": None,
            "resolution_source": None, "resolved_at": None, "project_specific": True,
            "generic_rule_candidate": generic_rule_candidate, "detector": detector,
            "history": [{"to": status, "by": "ENGINE", "at": None, "note": f"raised by {detector}"}],
            "project_id": project_id, "drawing_revision": drawing_revision, "context": context or {}}


def number(flags):
    """Display ids STR-COL-001 ... in a deterministic order (element type, issue, element)."""
    out = sorted(flags, key=lambda f: (f["discipline"], f["element_type"], f["issue_type"], str(f["element_id"]),
                                       f["flag_key"]))
    seq = Counter()
    for f in out:
        k = (DISCIPLINES[f["discipline"]], f["element_type"][:3].upper())
        seq[k] += 1
        f["flag_id"] = f"{k[0]}-{k[1]}-{seq[k]:03d}"
    return out


def transition(flag, to, *, by, at=None, note=None, resolution=None, resolution_source=None):
    """New flag in state `to`; history appended (never rewritten). Illegal transitions raise."""
    if to not in TRANSITIONS[flag["status"]]:
        raise ValueError(f"illegal transition {flag['status']} -> {to}")
    f = copy.deepcopy(flag)
    f["history"].append({"from": flag["status"], "to": to, "by": by, "at": at, "note": note})
    f["status"] = to
    if to in (RESOLVED, ANSWERED):
        f["resolution"], f["resolved_by"], f["resolution_source"] = resolution, by, resolution_source
        f["resolved_at"] = at
    return f


def is_open(flag):
    return flag["status"] in OPEN_STATES


# ------------------------------------------------------------------------------------------------ release
def component_release(components, flags):
    """components: [{element_id, component, trade, quantity, unit, depends_on: [fact]}].
    A component takes the strongest effect of the OPEN flags that touch one of its facts for its element. Components
    whose facts are untouched stay VERIFIED - an element is never zeroed because one component is unknown."""
    by_el = defaultdict(list)
    for f in flags:
        if is_open(f):
            for e in f["element_ids"]:
                by_el[e].append(f)
    out = []
    for c in components:
        hits = [f for f in by_el.get(c["element_id"], []) if set(f["affected_facts"]) & set(c["depends_on"])]
        eff = VERIFIED
        for f in hits:
            if _RANK[f["release_effect"]] > _RANK[eff]:
                eff = f["release_effect"]
        out.append(dict(c, release_state=eff, flags=sorted(f["flag_key"] for f in hits)))
    return out


def release_totals(released):
    """Per trade and unit: released (VERIFIED + PROVISIONAL), lower bound, audit-only and blocked quantities."""
    t = defaultdict(lambda: defaultdict(float))
    for c in released:
        if c.get("quantity") is None:
            continue
        key = f"{c['trade']}|{c['unit']}"
        bucket = {VERIFIED: "released", NO_QUANTITY_IMPACT: "released", PROVISIONAL_VALUE: "released_provisional",
                  LOWER_BOUND: "lower_bound", AUDIT_ONLY: "audit_only", BLOCKED: "blocked"}[c["release_state"]]
        t[key][bucket] += c["quantity"]
    return {k: {b: round(v, 3) for b, v in d.items()} for k, d in sorted(t.items())}


# ------------------------------------------------------------------------------------------------ summary
def summary(flags):
    open_f = [f for f in flags if is_open(f)]

    def eff_bucket(f):
        e = f["release_effect"]
        return {BLOCKED: "BLOCKED_QUANTITY", AUDIT_ONLY: "BLOCKED_QUANTITY", LOWER_BOUND: "LOWER_BOUND_QUANTITY",
                PROVISIONAL_VALUE: "QUANTITY_AFFECTED", NO_QUANTITY_IMPACT: "NO_QUANTITY_IMPACT",
                VERIFIED: "NO_QUANTITY_IMPACT"}[e]
    status_bucket = {OPEN: "OPEN", PROVISIONAL: "PROVISIONAL", SENT: "OPEN", ANSWERED: "OPEN", RESOLVED: "RESOLVED",
                     SUPERSEDED: "RESOLVED"}
    by_disc = {}
    for d in DISCIPLINES:
        fs = [f for f in flags if f["discipline"] == d]
        by_disc[d] = {"total": len(fs), "by_status": dict(Counter(status_bucket[f["status"]] for f in fs)),
                      "open_by_effect": dict(Counter(eff_bucket(f) for f in fs if is_open(f)))}
    trade_open = Counter(t for f in open_f for t in f["trade"])
    affected = defaultdict(float)
    for f in open_f:
        if f["quantity_affected"] is not None and f["release_effect"] != NO_QUANTITY_IMPACT:
            affected[f"{f['unit']}"] += f["quantity_affected"]
    lines = []
    for d, v in by_disc.items():
        n = sum(1 for f in open_f if f["discipline"] == d)
        if v["total"]:
            lines.append(f"{n} {d.lower()} flag{'s' if n != 1 else ''} open")
    for t, n in sorted(trade_open.items()):
        lines.append(f"{n} affect {t.lower()}")
    for u, q in sorted(affected.items()):
        lines.append(f"affected measured quantity = {round(q, 3)} {u} (summed per flag; an element in several "
                     f"flags counts once per flag - use component_release for de-duplicated totals)")
    pending = any(f["release_effect"] in (BLOCKED, AUDIT_ONLY, LOWER_BOUND) for f in open_f)
    lines.append(f"final quantity pending consultant = {'yes' if pending else 'no'}")
    return {"flags": len(flags), "open": len(open_f), "by_discipline": by_disc,
            "open_by_issue_type": dict(Counter(f["issue_type"] for f in open_f)),
            "open_by_severity": dict(Counter(f["severity"] for f in open_f)),
            "open_by_trade": dict(trade_open),
            "affected_measured_quantity_sum_over_flags": {k: round(v, 3) for k, v in affected.items()},
            "final_quantity_pending_consultant": pending, "front_summary_lines": lines, "pricing_integrated": False}


def schema():
    return {"schema": "ENGINEERING_FLAG_SCHEMA", "policy_id": POLICY_ID, "fields": list(FIELDS),
            "statuses": list(STATUSES), "transitions": {k: sorted(v) for k, v in TRANSITIONS.items()},
            "issue_types": list(ISSUE_TYPES), "severities": list(SEVERITIES), "disciplines": DISCIPLINES,
            "trades": list(TRADES), "release_effects": list(RELEASE_EFFECTS),
            "rules": ["flag_key is a content hash (project, detector, element, subject); flag_id is a display number",
                      "history is append-only; resolving keeps every earlier state",
                      "an open flag changes the release state of the components depending on its affected_facts only",
                      "independently known components stay VERIFIED / LOWER_BOUND; nothing is forced to zero",
                      "flags are project_specific; a generic rule only via the rule-promotion workflow"]}
