"""Every numerical or causal statement a report makes, declared as an object and checked against a register.

A20 was described in R6 as verifying "every statement in the narrative".  It verified five hand-written
assertions.  That is a useful check and an inaccurate description of it, and the gap between the two is
exactly where the round's wrong sentences lived: "four material questions are the whole bottleneck", "those
questions unblock all 127 rows", "565 impacts" - none of them declared, so none of them checked, all of them
published.

So a claim is a first-class object.  It carries an id, the sentence a reader will see, the register path or
query that decides it, the value it asserts, what kind of claim it is, and the result of re-reading the
register.  Prose is then GENERATED from the claims rather than written beside them: a sentence that is not a
claim cannot contain a number, and a claim that does not agree with its register fails the gate.

The gate reports what this actually proves - that every DECLARED claim agrees - and never calls that "all
prose verified".  Those are different statements, and conflating them is the same class of error again.
"""

from __future__ import annotations

COUNT = "COUNT"
CAUSAL = "CAUSAL"
RELEASE = "RELEASE"
COMPARISON = "COMPARISON"
STATUS = "STATUS"
CLAIM_TYPES = (COUNT, CAUSAL, RELEASE, COMPARISON, STATUS)


def at(document, path):
    """Read a dotted path out of a published document.  A missing path is a failed claim, not an exception."""
    node = document
    for part in str(path).split("."):
        if isinstance(node, list):
            try:
                node = node[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


class Register:
    """Collects the claims a report is allowed to make, and checks each one against its register."""

    def __init__(self, document):
        self._doc = document
        self._claims = []

    def claim(self, claim_id, statement, path, value, kind=COUNT, query=None, note=None):
        """Declare one statement.  `value` is what the report says; the path is what decides it."""
        actual = value if path is None else at(self._doc, path)
        if path is None and query is not None:
            actual = query(self._doc)
        verified = actual == value
        self._claims.append({
            "CLAIM_ID": claim_id,
            "STATEMENT": statement,
            "CLAIM_TYPE": kind,
            "REGISTER_PATH": path,
            "QUERY": (None if query is None else
                      (query.__doc__ or "a query over this document, defined where the claim is")),
            "VALUE": value,
            "REGISTER_SAYS": actual,
            "VERIFIED": verified,
            "NOTE": note,
        })
        return self._claims[-1]

    def sentence(self, claim_id):
        """The prose for one claim, generated from the claim rather than written beside it."""
        c = next(x for x in self._claims if x["CLAIM_ID"] == claim_id)
        return c["STATEMENT"].format(value=c["REGISTER_SAYS"])

    def as_dict(self):
        rows = sorted(self._claims, key=lambda c: c["CLAIM_ID"])
        failed = [c for c in rows if not c["VERIFIED"]]
        return {
            "CLAIMS": rows,
            "CLAIM_COUNT": len(rows),
            "CLAIM_TYPES": list(CLAIM_TYPES),
            "ALL_DECLARED_CLAIMS_AGREE": not failed,
            "DISAGREEMENTS": failed,
            "WHAT_THIS_PROVES": "every claim DECLARED here was re-read from the register that decides it and "
                                "agrees with it",
            "WHAT_THIS_CHECK_DOES_NOT_PROVE": "that the prose contains no undeclared claim.  A number that "
                                              "never became a claim object is not verified by this register, "
                                              "and no report may describe this check as 'all prose verified'",
            "RULE": "a sentence carrying a number or a causal assertion is generated from a claim object; "
                    "anything else may not carry one",
        }
