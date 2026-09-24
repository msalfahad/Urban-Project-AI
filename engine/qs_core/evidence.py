"""The evidence hierarchy, made executable.

A quantity is only as good as the weakest fact under it, and the weakest fact is usually invisible by the time a
number reaches a bill.  So every established value carries the rank of the evidence that established it, and a
value with no evidence is not a value at all - it is a question.

The order is fixed because it is an order of authority, not of convenience: what the drawing states in writing
beats what the drawing can be measured to imply; measured geometry beats what the owner told us; what the owner
told us beats a general guide; and a guide that does not cover the case leaves a question.

Nothing here knows any project.  A caller offers claims; this module says which one wins and why, and refuses to
pick when two claims of equal authority disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------- the hierarchy, strongest first
DRAWING_DIMENSION = "DRAWING_DIMENSION"          # a dimension written on the drawing
MEASURED_GEOMETRY = "MEASURED_GEOMETRY"          # taken off the drawing's own geometry
OWNER_PROJECT_INPUT = "OWNER_PROJECT_INPUT"      # the owner stated it for this project
APPROVED_GUIDE = "APPROVED_GUIDE"                # a standing approved rule, applied because it covers this case
UNRESOLVED_QUESTION = "UNRESOLVED_QUESTION"      # nothing above applies: ask

HIERARCHY = (DRAWING_DIMENSION, MEASURED_GEOMETRY, OWNER_PROJECT_INPUT, APPROVED_GUIDE)

ESTABLISHED = "ESTABLISHED"
CONFLICTED = "CONFLICTED_AT_EQUAL_AUTHORITY"
NOT_ESTABLISHED = "NOT_ESTABLISHED"


def rank_of(source):
    """Where a named source sits in the hierarchy.  An unknown source ranks below every known one."""
    return HIERARCHY.index(source) if source in HIERARCHY else len(HIERARCHY)


@dataclass(frozen=True)
class Claim:
    """One source's answer to one question, and where it came from."""
    value: float
    source: str                       # one of the hierarchy constants
    reference: str = None             # the dimension, the entity, the owner input id, the guide clause
    detail: dict = field(default_factory=dict)

    def as_dict(self):
        return {"VALUE": self.value, "SOURCE": self.source, "RANK": rank_of(self.source),
                "REFERENCE": self.reference, "DETAIL": self.detail}


def resolve(what, claims, tolerance):
    """Settle one question from the claims offered, or report that it is not settled.

    Two claims of equal authority that agree within tolerance are one answer.  Two that disagree are a question,
    and the engine does not average them, prefer the first, or prefer the one that suits a total.
    """
    offered = list(claims)
    # a source that names the question but gives no answer has not made a claim; it is recorded and passed over
    claims = [c for c in offered if c.value is not None]
    considered = [c.as_dict() for c in sorted(offered, key=lambda c: (rank_of(c.source), str(c.reference)))]
    if not claims:
        return {"WHAT": what, "VALUE": None, "SOURCE": UNRESOLVED_QUESTION, "RANK": None,
                "REFERENCE": None, "STATUS": NOT_ESTABLISHED, "CONSIDERED": considered,
                "CONFLICTS": [], "WHY": "no source offers a value for this"}
    best_rank = min(rank_of(c.source) for c in claims)
    top = [c for c in claims if rank_of(c.source) == best_rank]
    spread = max(c.value for c in top) - min(c.value for c in top)
    if spread > tolerance:
        return {"WHAT": what, "VALUE": None, "SOURCE": UNRESOLVED_QUESTION, "RANK": best_rank,
                "REFERENCE": None, "STATUS": CONFLICTED, "CONSIDERED": considered,
                "CONFLICTS": [c.as_dict() for c in sorted(top, key=lambda c: c.value)],
                "WHY": f"{len(top)} sources of equal authority disagree by {round(spread, 6)}, which is more "
                       f"than the tolerance {tolerance}; nothing in the hierarchy breaks the tie"}
    chosen = sorted(top, key=lambda c: (c.value, str(c.reference)))[0]
    return {"WHAT": what, "VALUE": chosen.value, "SOURCE": chosen.source, "RANK": best_rank,
            "REFERENCE": chosen.reference, "STATUS": ESTABLISHED, "CONSIDERED": considered, "CONFLICTS": [],
            "WHY": f"the highest authority offering a value for this is {chosen.source}",
            "SUPERSEDED": [c.as_dict() for c in claims if rank_of(c.source) > best_rank]}


def established(record):
    return bool(record) and record.get("STATUS") == ESTABLISHED and record.get("VALUE") is not None


def question(record, subject, blocks):
    """Turn an unsettled evidence record into the question a person has to answer."""
    if established(record):
        return None
    return {"QUESTION": f"What is the {record['WHAT']} of {subject}?",
            "KIND": "EVIDENCE_NOT_ESTABLISHED" if record["STATUS"] == NOT_ESTABLISHED else record["STATUS"],
            "SUBJECT": subject, "WHAT": record["WHAT"], "BLOCKS": blocks,
            "SOURCES_CONSIDERED": record["CONSIDERED"], "CONFLICTS": record["CONFLICTS"],
            "WHY": record["WHY"],
            "HIERARCHY": list(HIERARCHY) + [UNRESOLVED_QUESTION]}
