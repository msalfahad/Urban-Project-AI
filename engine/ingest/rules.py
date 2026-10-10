"""Rule scope and priority (PA05 §14).

PROJECT_DRAWING_SPEC > PROJECT_OWNER_OVERRIDE > URBAN_STANDARD > TEMPORARY_DEFAULT > UNKNOWN.
A project rule never becomes an Urban standard automatically: promotion needs an explicit approval record.
"""

from __future__ import annotations

SCOPES = ("PROJECT_DRAWING_SPEC", "PROJECT_OWNER_OVERRIDE", "URBAN_STANDARD", "TEMPORARY_DEFAULT", "UNKNOWN")
PRIORITY = {s: i for i, s in enumerate(SCOPES)}


def rule(*, rule_id, scope, parameter, value, unit, project_id=None, source, effective_from_revision=1, approval=None, note=None):
    if scope not in SCOPES:
        raise ValueError(f"unknown rule scope {scope}")
    if scope == "URBAN_STANDARD" and not approval:
        raise ValueError("an URBAN_STANDARD rule needs an approval record (who / when / basis); nothing is promoted automatically")
    if scope.startswith("PROJECT") and not project_id:
        raise ValueError("a project-scoped rule needs its project id")
    return {"RULE_ID": rule_id, "SCOPE": scope, "PARAMETER": parameter, "VALUE": value, "UNIT": unit, "PROJECT_ID": project_id, "SOURCE": source,
            "EFFECTIVE_FROM_REVISION": effective_from_revision, "APPROVAL": approval, "NOTE": note}


def resolve(parameter, candidates, project_id=None):
    """Pick the rule that governs `parameter` for `project_id` by scope priority.
    Ties inside one scope are a CONFLICT, never a silent pick."""
    cands = [c for c in candidates if c["PARAMETER"] == parameter and (c["PROJECT_ID"] in (None, project_id))]
    if not cands:
        return {"PARAMETER": parameter, "RESOLVED": None, "SCOPE": "UNKNOWN", "STATUS": "NOT_ESTABLISHED", "CANDIDATES": []}
    best = min(PRIORITY[c["SCOPE"]] for c in cands)
    top = [c for c in cands if PRIORITY[c["SCOPE"]] == best]
    if len(top) > 1 and len({str(c["VALUE"]) for c in top}) > 1:
        return {"PARAMETER": parameter, "RESOLVED": None, "SCOPE": top[0]["SCOPE"], "STATUS": "CONFLICT", "CANDIDATES": top}
    chosen = sorted(top, key=lambda c: -c["EFFECTIVE_FROM_REVISION"])[0]
    st = {"PROJECT_DRAWING_SPEC": "SOURCE_ESTABLISHED", "PROJECT_OWNER_OVERRIDE": "OWNER_ESTABLISHED", "URBAN_STANDARD": "OWNER_ESTABLISHED",
          "TEMPORARY_DEFAULT": "TEMPORARY_DEFAULT", "UNKNOWN": "NOT_ESTABLISHED"}[chosen["SCOPE"]]
    return {"PARAMETER": parameter, "RESOLVED": chosen, "SCOPE": chosen["SCOPE"], "STATUS": st, "CANDIDATES": cands}


def promote_to_standard(project_rule, *, approval):
    """Explicit promotion only.  Returns a NEW rule; the project rule is untouched."""
    if not approval or not all(k in approval for k in ("BY", "DATE", "BASIS")):
        raise ValueError("promotion needs approval {BY, DATE, BASIS}")
    return rule(rule_id=project_rule["RULE_ID"] + ":URBAN", scope="URBAN_STANDARD", parameter=project_rule["PARAMETER"], value=project_rule["VALUE"], unit=project_rule["UNIT"],
                source=f"promoted from {project_rule['RULE_ID']} ({project_rule['PROJECT_ID']})", approval=approval)
