"""CAD_ORACLE_AUTOCAD_READONLY - optional external oracle interface (generic).

An oracle (an AutoCAD MCP route, another extractor, a recorded donor run) is a CROSS-CHECK. Production never depends
on it and an oracle result never overrides a production quantity.

Oracle questions: count tags, inspect ATTRIB, inspect an entity handle, bounding box, line / curve length, parallel
face spacing, insertion point, block scale / rotation.

Safety rules learnt from blind donor runs
  * a result that hit the oracle's entity limit (pagination) is INCOMPLETE - never a count;
  * a failed region / crossing selection is ORACLE_UNAVAILABLE - never zero;
  * an oracle that is not connected answers ORACLE_UNAVAILABLE for every question.
Stdlib only.
"""

from __future__ import annotations

QUESTIONS = ("COUNT_TAGS", "INSPECT_ATTRIB", "INSPECT_HANDLE", "BOUNDING_BOX", "CURVE_LENGTH", "FACE_SPACING",
             "INSERTION_POINT", "BLOCK_SCALE_ROTATION")
OK = "OK"
INCOMPLETE = "INCOMPLETE"
UNAVAILABLE = "ORACLE_UNAVAILABLE"
ANSWER_STATES = (OK, INCOMPLETE, UNAVAILABLE)


def answer(question, value=None, *, refs=(), state=OK, entity_limit=None, returned=None, error=None, oracle=None):
    """Normalised oracle answer. A paginated result (returned >= entity_limit) is INCOMPLETE whatever the caller says;
    an error is UNAVAILABLE; a missing value is never read as zero."""
    if question not in QUESTIONS:
        raise ValueError(f"unknown oracle question {question}")
    if error is not None:
        state, value = UNAVAILABLE, None
    elif entity_limit is not None and returned is not None and returned >= entity_limit:
        state = INCOMPLETE
    elif value is None and state == OK:
        state = UNAVAILABLE
    return {"oracle": oracle, "question": question, "value": value if state == OK else None,
            "raw_value": value, "state": state, "refs": list(refs), "entity_limit": entity_limit,
            "returned": returned, "error": error, "complete": state == OK}


class CadOracleReadOnly:
    """Interface. Concrete oracles implement ask(); none may write to the drawing or to production."""
    name = "ABSTRACT"
    read_only = True

    def ask(self, question, **params):
        raise NotImplementedError

    def available(self):
        return False


class UnavailableOracle(CadOracleReadOnly):
    name = "NONE"

    def ask(self, question, **params):
        return answer(question, None, state=UNAVAILABLE, error="oracle not connected", oracle=self.name)


class RecordedOracle(CadOracleReadOnly):
    """Replays answers recorded from an external run: {(question, key): {value, refs, entity_limit, returned,
    error}}. Unknown questions are UNAVAILABLE."""

    def __init__(self, name, records):
        self.name = name
        self.records = dict(records)

    def available(self):
        return bool(self.records)

    def ask(self, question, key=None, **params):
        r = self.records.get((question, key))
        if r is None:
            return answer(question, None, state=UNAVAILABLE, error="no recorded answer", oracle=self.name)
        return answer(question, r.get("value"), refs=r.get("refs", ()), entity_limit=r.get("entity_limit"),
                      returned=r.get("returned"), error=r.get("error"), oracle=self.name)


def region_select(oracle, region_id, **params):
    """Crossing selection through an oracle: a failure is ORACLE_UNAVAILABLE (never an empty / zero selection)."""
    try:
        res = oracle.ask("COUNT_TAGS", key=region_id, **params)
    except Exception as e:                       # noqa: BLE001 - any oracle failure is 'unavailable', never zero
        return answer("COUNT_TAGS", None, error=f"{type(e).__name__}: {e}", oracle=getattr(oracle, "name", None))
    return res


def schema():
    return {"schema": "CAD_ORACLE_SCHEMA", "questions": list(QUESTIONS), "answer_states": list(ANSWER_STATES),
            "rules": ["oracles are optional and read-only; production never depends on them",
                      "an oracle answer never overrides a production quantity",
                      "a paginated answer (entity limit reached) is INCOMPLETE",
                      "a region / selection failure is ORACLE_UNAVAILABLE, never zero"]}
