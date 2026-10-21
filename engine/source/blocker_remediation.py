"""BLOCKER_REMEDIATION_ENGINE (generic).

Given a blocked fact, try to resolve it automatically along its evidence ladder, record every method tried, and
publish one remediation record that tells the reviewer what is known, what is not, what the quantity is now, what
it would be, why it is blocked, what the engine already tried, what to try next, where to look and - only when the
source genuinely cannot answer - what to ask the consultant. A remediation never writes a source fact: a value found
below the source levels stays PROVISIONAL with its origin. Stdlib only.
"""

from __future__ import annotations

from engine.source import evidence_ladder as EL

BLOCKER_KINDS = {
    "MISSING_DEPTH": "GROUND_BEAM_DEPTH",
    "MISSING_MEMBER_DIMENSION": "MEMBER_DIMENSION",
    "MISSING_SCHEDULE": "MEMBER_DIMENSION",
    "MISSING_HEIGHT": "WALL_HEIGHT",
    "MISSING_THICKNESS": "SLAB_THICKNESS",
    "LABEL_SCOPE": "SLAB_THICKNESS",
    "UNREADABLE_TEXT": "TEXT_READING",
    "UNBOUND_MEMBER": "MEMBER_BINDING",
}
RESOLVED_SOURCE, RESOLVED_PROVISIONAL, STILL_BLOCKED = "RESOLVED_SOURCE", "RESOLVED_PROVISIONAL", "STILL_BLOCKED"
REQUIRED_FIELDS = ("flag_id", "element", "known_facts", "unknown_fact", "current_quantity", "provisional_quantity",
                   "low_scenario", "high_scenario", "quantity_impact", "why_blocked", "attempts",
                   "successful_method", "authority", "next_automated_method", "where_to_look", "search_text",
                   "consultant_question", "result")


class RemediationError(ValueError):
    pass


def remediate(blocker, resolvers, *, quantity_fn=None, context=None):
    """blocker: {flag_id, kind, element, known_facts, unknown_fact, current_quantity, why_blocked, where_to_look,
    search_text, consultant_question}. quantity_fn(value) -> quantity at a resolved value (for best / low / high)."""
    kind = blocker.get("kind")
    if kind not in BLOCKER_KINDS:
        raise RemediationError(f"unknown blocker kind {kind}")
    res = EL.resolve(BLOCKER_KINDS[kind], resolvers, context)
    q_now = blocker.get("current_quantity")
    prov = lo = hi = None
    if res["resolved"] and quantity_fn is not None:
        prov, lo, hi = quantity_fn(res["value"]), quantity_fn(res["low"]), quantity_fn(res["high"])
        lo, hi = min(lo, hi), max(lo, hi)
    if not res["resolved"]:
        result = STILL_BLOCKED
    elif res["fact_origin"] == "SOURCE_FACT" and res["authority"] == "VERIFIED":
        result = RESOLVED_SOURCE
    else:
        result = RESOLVED_PROVISIONAL
    tried = [a["level"] for a in res["attempts"]]
    rest = [lvl for lvl in EL.levels(BLOCKER_KINDS[kind]) if lvl not in tried]
    nxt = next((a["level"] for a in res["attempts"] if a["result"] == "NOT_AVAILABLE"), None) or \
        (rest[0] if rest else None)
    needs_consultant = result != RESOLVED_SOURCE
    rec = {"flag_id": blocker["flag_id"], "kind": kind, "element": blocker.get("element"),
           "known_facts": dict(blocker.get("known_facts") or {}), "unknown_fact": blocker.get("unknown_fact"),
           "current_quantity": q_now, "provisional_quantity": prov, "low_scenario": lo, "high_scenario": hi,
           "quantity_impact": None if prov is None else prov - (q_now or 0.0),
           "why_blocked": blocker.get("why_blocked"), "attempts": res["attempts"],
           "successful_method": res["level"] if res["resolved"] else None,
           "authority": res["authority"], "fact_origin": res["fact_origin"],
           "next_automated_method": None if result == RESOLVED_SOURCE else nxt,
           "where_to_look": blocker.get("where_to_look"), "search_text": blocker.get("search_text"),
           "consultant_question": blocker.get("consultant_question") if needs_consultant else None,
           "needs_consultant": needs_consultant and bool(blocker.get("consultant_question")),
           "result": result}
    missing = [f for f in REQUIRED_FIELDS if f not in rec]
    if missing:
        raise RemediationError(f"remediation record lacks {missing}")
    return rec
