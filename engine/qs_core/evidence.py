"""The evidence hierarchy, and the lifecycle a claim has before it is allowed into it.

A quantity is only as good as the weakest fact under it, and the weakest fact is usually invisible by the time a
number reaches a bill.  So every established value carries the rank of the evidence that established it, and a
value with no evidence is not a value at all - it is a question.

The order is fixed because it is an order of authority: what the drawing states in writing beats what the
drawing can be measured to imply; measured geometry beats what the owner told us; what the owner told us beats a
general guide; and a guide that does not cover the case leaves a question.

RANK IS NOT ENOUGH.  A claim also has a LIFE: it applies to some things and not others, it starts at a revision,
and it can be superseded or withdrawn.  A superseded owner input still outranks a standard, so a resolver that
looks only at rank will keep choosing it for ever - which is exactly how a value the project had explicitly
retired went on answering seven questions.  Eligibility is therefore decided before authority, and every claim
that was passed over says which of the two rejected it.
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

# ---------------------------------------------------------------- the life of a claim
ACTIVE = "ACTIVE"                 # may answer, where it applies
SUPERSEDED = "SUPERSEDED"         # something later replaced it, within a stated scope
WITHDRAWN = "WITHDRAWN"           # taken back entirely; it may never answer again
CONDITIONAL = "CONDITIONAL"       # may answer only while its condition holds
LIFECYCLE = (ACTIVE, SUPERSEDED, WITHDRAWN, CONDITIONAL)

ESTABLISHED = "ESTABLISHED"
CONFLICTED = "CONFLICTED_AT_EQUAL_AUTHORITY"
NOT_ESTABLISHED = "NOT_ESTABLISHED"

# why a claim was not allowed to answer
INELIGIBLE_STATUS = "STATUS_DOES_NOT_ALLOW_IT_TO_ANSWER"
INELIGIBLE_SCOPE = "OUT_OF_SCOPE_FOR_THIS_SUBJECT"
INELIGIBLE_REVISION = "NOT_YET_EFFECTIVE_AT_THIS_REVISION"
INELIGIBLE_CONDITION = "ITS_CONDITION_DOES_NOT_HOLD"
INELIGIBLE_NO_VALUE = "OFFERS_NO_VALUE"
SUPERSEDED_OUT = "SUPERSEDED_WITHIN_THIS_SCOPE"


def rank_of(source):
    """Where a named source sits in the hierarchy.  An unknown source ranks below every known one."""
    return HIERARCHY.index(source) if source in HIERARCHY else len(HIERARCHY)


@dataclass(frozen=True)
class Claim:
    """One source's answer to one question, where it came from, and whether it may still answer.

    `scope` is a set of key/value pairs the SUBJECT must match for this claim to apply - for example
    {"OBJECT_KIND": "WINDOW", "HAS_SOURCE_HEIGHT": False}.  An empty scope applies to everything, which is the
    right default for a dimension written on one object and the wrong one for a rule about a trade, so a caller
    that means "only windows" has to say so.
    """
    value: float
    source: str                       # one of the hierarchy constants
    reference: str = None             # the dimension, the entity, the owner input id, the guide clause
    detail: dict = field(default_factory=dict)
    status: str = ACTIVE
    scope: dict = field(default_factory=dict)
    effective_from: str = None        # the revision or date this claim starts to apply at
    superseded_by: str = None
    superseded_reason: str = None
    condition: str = None             # for CONDITIONAL: what has to hold, stated in words

    def as_dict(self):
        return {"VALUE": self.value, "SOURCE": self.source, "RANK": rank_of(self.source),
                "REFERENCE": self.reference, "STATUS": self.status, "SCOPE": self.scope,
                "EFFECTIVE_FROM": self.effective_from, "SUPERSEDED_BY": self.superseded_by,
                "SUPERSEDED_REASON": self.superseded_reason, "CONDITION": self.condition,
                "DETAIL": self.detail}


def applies_to(claim, subject):
    """Does this claim's scope cover this subject?  Every stated key must match; unstated keys are not tested."""
    if not claim.scope:
        return True, None
    subject = subject or {}
    for key, want in claim.scope.items():
        if key not in subject:
            return False, f"the subject does not state {key}, which this claim's scope requires"
        if subject[key] != want:
            return False, f"{key} is {subject[key]!r} and this claim applies only where it is {want!r}"
    return True, None


def eligibility(claim, subject=None, revision=None, conditions_met=()):
    """Whether this claim may answer at all, before anything compares authority."""
    if claim.value is None:
        return False, INELIGIBLE_NO_VALUE, "this source names the question and offers no answer"
    if claim.status == WITHDRAWN:
        return False, INELIGIBLE_STATUS, "this claim was withdrawn and may never answer again"
    if claim.status == SUPERSEDED:
        return False, SUPERSEDED_OUT, (claim.superseded_reason or
                                       f"superseded by {claim.superseded_by or 'a later claim'}")
    if claim.status == CONDITIONAL and claim.condition not in (conditions_met or ()):
        return False, INELIGIBLE_CONDITION, (f"this claim answers only while {claim.condition!r} holds, and "
                                             "the caller has not established that it does")
    ok, why = applies_to(claim, subject)
    if not ok:
        return False, INELIGIBLE_SCOPE, why
    if claim.effective_from and revision and str(revision) < str(claim.effective_from):
        return False, INELIGIBLE_REVISION, (f"this claim takes effect at {claim.effective_from} and the "
                                            f"subject is at {revision}")
    return True, None, None


def supersede(claims, superseded_reference, by, reason, scope=None):
    """Retire a claim within a scope, generically: the same claim can stay active outside that scope.

    Returns a new list; nothing is deleted, because a reader has to be able to see what was retired and why.
    """
    out = []
    for c in claims:
        if c.reference != superseded_reference:
            out.append(c)
            continue
        out.append(Claim(c.value, c.source, c.reference, c.detail, status=SUPERSEDED,
                         scope=dict(scope or c.scope), effective_from=c.effective_from,
                         superseded_by=by, superseded_reason=reason, condition=c.condition))
        if scope and c.scope != scope:
            # outside the superseded scope the original claim is untouched; the caller states that scope by
            # supplying one, and a claim retired "for windows with no source height" still answers elsewhere
            out.append(Claim(c.value, c.source, f"{c.reference}::OUTSIDE::{_scope_key(scope)}", dict(
                c.detail, OUTSIDE_THE_SUPERSEDED_SCOPE=scope), status=c.status, scope=_negated(scope),
                effective_from=c.effective_from, condition=c.condition))
    return out


def _scope_key(scope):
    return ",".join(f"{k}={v}" for k, v in sorted(scope.items()))


def _negated(scope):
    """A scope that matches subjects the given scope does not, for the single-key case it is used with."""
    if len(scope) != 1:
        return {}
    (k, v), = scope.items()
    return {k: _NOT(v)}


class _NOT:
    """'anything but this'.  A tiny value object so a negated scope stays comparable and printable."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return not (other == self.value)

    def __hash__(self):
        return hash(("NOT", self.value))

    def __repr__(self):
        return f"NOT({self.value!r})"


def resolve(what, claims, tolerance, subject=None, revision=None, conditions_met=()):
    """Settle one question from the claims offered, or report that it is not settled.

    Eligibility first, authority second.  Two claims of equal authority that agree within tolerance are one
    answer; two that disagree are a question, and the engine does not average them, prefer the first, or prefer
    the one that suits a total.
    """
    offered = list(claims)
    eligible, ineligible = [], []
    for c in offered:
        ok, why_kind, why = eligibility(c, subject, revision, conditions_met)
        (eligible if ok else ineligible).append(
            c if ok else dict(c.as_dict(), INELIGIBLE_BECAUSE=why_kind, WHY=why))

    considered = [c.as_dict() for c in sorted(offered, key=lambda c: (rank_of(c.source), str(c.reference)))]
    base = {"WHAT": what, "SUBJECT": subject, "CONSIDERED": considered,
            "INELIGIBLE": sorted(ineligible, key=lambda d: (d["RANK"], str(d["REFERENCE"]))),
            "LIFECYCLE": list(LIFECYCLE), "HIERARCHY": list(HIERARCHY) + [UNRESOLVED_QUESTION]}

    if not eligible:
        return dict(base, VALUE=None, SOURCE=UNRESOLVED_QUESTION, RANK=None, REFERENCE=None,
                    STATUS=NOT_ESTABLISHED, CONFLICTS=[],
                    WHY=("no source that may answer this offers a value" if offered else
                         "no source offers a value for this"))

    best_rank = min(rank_of(c.source) for c in eligible)
    top = [c for c in eligible if rank_of(c.source) == best_rank]
    spread = max(c.value for c in top) - min(c.value for c in top)
    if spread > tolerance:
        return dict(base, VALUE=None, SOURCE=UNRESOLVED_QUESTION, RANK=best_rank, REFERENCE=None,
                    STATUS=CONFLICTED, CONFLICTS=[c.as_dict() for c in sorted(top, key=lambda c: c.value)],
                    WHY=(f"{len(top)} sources of equal authority disagree by {round(spread, 6)}, which is more "
                         f"than the tolerance {tolerance}; nothing in the hierarchy breaks the tie"))

    chosen = sorted(top, key=lambda c: (c.value, str(c.reference)))[0]
    return dict(base, VALUE=chosen.value, SOURCE=chosen.source, RANK=best_rank, REFERENCE=chosen.reference,
                STATUS=ESTABLISHED, CONFLICTS=[],
                WHY=f"the highest authority eligible to answer this is {chosen.source}",
                SUPERSEDED=[c.as_dict() for c in eligible if rank_of(c.source) > best_rank])


def established(record):
    return bool(record) and record.get("STATUS") == ESTABLISHED and record.get("VALUE") is not None


def question(record, subject, blocks):
    """Turn an unsettled evidence record into the question a person has to answer."""
    if established(record):
        return None
    return {"QUESTION": f"What is the {record['WHAT']} of {subject}?",
            "KIND": "EVIDENCE_NOT_ESTABLISHED" if record["STATUS"] == NOT_ESTABLISHED else record["STATUS"],
            "SUBJECT": subject, "WHAT": record["WHAT"], "BLOCKS": blocks,
            "SOURCES_CONSIDERED": record["CONSIDERED"], "INELIGIBLE": record.get("INELIGIBLE", []),
            "CONFLICTS": record["CONFLICTS"], "WHY": record["WHY"],
            "HIERARCHY": record["HIERARCHY"]}
