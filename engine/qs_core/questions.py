"""One unanswered fact is one question, however many quantities it holds up.

R5 published forty-five "open questions" for thirty-seven unresolved facts, because a door whose host was
unknown was counted once where it was admitted and again where the dependency graph failed to associate it with
a wall.  Counting the same fact twice makes a source look worse than it is, and - worse - it makes the list
useless as a work list, because answering one item silently closes two.

So there are two registers.  ROOT_QUESTIONS holds unique facts nobody has established, each with a stable id
derived from the object and the fact.  DEPENDENCY_IMPACTS holds everything those facts hold up: rows, subtotals,
bill lines.  An impact is never a question; it is what an answer would release.
"""

from __future__ import annotations


def root_id(kind, subject_ref):
    """A stable id for one unanswered fact about one object.  The same fact never earns two ids."""
    return f"RQ::{kind}::{subject_ref}"


class Register:
    """Collects root questions and their impacts, refusing to record the same fact twice."""

    def __init__(self):
        self._roots = {}
        self._impacts = {}

    def ask(self, kind, subject_ref, question, floor=None, subject_kind=None, evidence=None,
            needed_from=None, detail=None):
        """Record an unanswered fact.  Asking the same fact again returns the same id and merges nothing."""
        qid = root_id(kind, subject_ref)
        if qid not in self._roots:
            self._roots[qid] = {
                "ROOT_QUESTION_ID": qid, "KIND": kind, "SUBJECT_REF": subject_ref,
                "SUBJECT_KIND": subject_kind, "FLOOR": floor, "QUESTION": question,
                "NEEDED_FROM": needed_from, "EVIDENCE": evidence or [], "DETAIL": detail or {},
                "ASKED_TIMES": 1}
        else:
            self._roots[qid]["ASKED_TIMES"] += 1
        return qid

    def impact(self, root_question_id, node, node_kind, effect, detail=None):
        """Record that this fact participates in determining this node.

        Impacts are a SET, keyed by the fact, the node and the effect.  R6 appended a row every time a
        construction path reached the same conclusion, and several paths reach most conclusions: 565 rows held
        246 exact duplicates, so the headline number measured how many times the graph was walked rather than
        how much work the answers release.  Recording the same edge twice must change nothing.
        """
        key = (root_question_id, str(node), node_kind, effect)
        if key not in self._impacts:
            self._impacts[key] = {"ROOT_QUESTION_ID": root_question_id, "NODE": node, "NODE_KIND": node_kind,
                                  "EFFECT": effect, "DETAIL": detail or {}, "SEEN_TIMES": 1}
        else:
            self._impacts[key]["SEEN_TIMES"] += 1
        return key

    def blocker_ids_by_node(self):
        """The set of unanswered facts each node is waiting on - the only honest basis for "releases"."""
        out = {}
        for i in self._impacts.values():
            out.setdefault(str(i["NODE"]), set()).add(i["ROOT_QUESTION_ID"])
        return out

    def as_dict(self):
        roots = sorted(self._roots.values(), key=lambda r: (r["KIND"], r["SUBJECT_REF"]))
        impacts = sorted(self._impacts.values(),
                         key=lambda i: (i["ROOT_QUESTION_ID"], i["NODE_KIND"], str(i["NODE"]),
                                        i["EFFECT"]))
        by_kind = {}
        for r in roots:
            by_kind[r["KIND"]] = by_kind.get(r["KIND"], 0) + 1
        per_root = {}
        for i in impacts:
            per_root[i["ROOT_QUESTION_ID"]] = per_root.get(i["ROOT_QUESTION_ID"], 0) + 1
        orphans = sorted({i["ROOT_QUESTION_ID"] for i in impacts} - set(self._roots))
        return {
            "ROOT_QUESTIONS": roots,
            "DEPENDENCY_IMPACTS": impacts,
            "ROOT_QUESTION_COUNT": len(roots),
            "ROOT_QUESTIONS_BY_KIND": dict(sorted(by_kind.items())),
            "DEPENDENCY_IMPACT_COUNT": len(impacts),
            "IMPACTS_PER_ROOT_QUESTION": dict(sorted(per_root.items())),
            "IMPACTS_WITHOUT_A_ROOT_QUESTION": orphans,
            "DUPLICATE_IMPACT_ROWS": 0,
            "IMPACTS_ARE": "a set keyed by (root question, node, node kind, effect).  Recording the same "
                           "edge from a second construction path changes nothing but SEEN_TIMES",
            "REPEATED_INSERTIONS": sum(i["SEEN_TIMES"] - 1 for i in self._impacts.values()),
            "RULE": "a unique unanswered fact is one root question with one stable id; everything it holds up "
                    "is an impact that references that id.  Impacts may be counted; they are never presented "
                    "as additional questions",
            "HOW_TO_READ_THE_COUNTS": ("ROOT_QUESTION_COUNT is the work list.  DEPENDENCY_IMPACT_COUNT is how "
                                       "much of the bill those answers would release, and is always the "
                                       "larger number"),
        }
