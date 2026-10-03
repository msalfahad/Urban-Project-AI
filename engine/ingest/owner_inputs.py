"""Owner input ingestion (PA05 §13).

Owner answers become versioned project parameters, never drawing facts,
AI memories or hard-coded constants.  Quantities that depend on a
parameter are registered as pure functions of (geometry facts, parameters)
so that changing an input recomputes exactly the dependent lines.
"""

from __future__ import annotations

import hashlib
import json

FIELDS = ("OWNER_INPUT_ID", "PROJECT_ID", "QUESTION_ID", "PARAMETER_OR_RULE", "VALUE", "UNIT", "SCOPE", "SOURCE", "EFFECTIVE_FROM_REVISION",
          "SUPERSEDES", "OWNER_CONFIRMED", "TIMESTAMP", "NOTES")


def owner_input(**f):
    f.setdefault("SOURCE", "OWNER_PROJECT_INPUT")
    f.setdefault("SUPERSEDES", None)
    f.setdefault("NOTES", None)
    missing = [k for k in FIELDS if k not in f]
    if missing:
        raise ValueError(f"owner input missing {missing}")
    if f["SOURCE"] != "OWNER_PROJECT_INPUT":
        raise ValueError("SOURCE must be OWNER_PROJECT_INPUT")
    if not f["OWNER_CONFIRMED"]:
        raise ValueError("an unconfirmed answer is a proposal, not an input")
    return {k: f[k] for k in FIELDS}


class ParameterStore:
    """Versioned parameters per project.  Each set() is a new revision; superseded inputs stay in the ledger."""

    def __init__(self, project_id):
        self.project_id = project_id
        self.ledger = []
        self.revision = 0

    def set(self, inp):
        if inp["PROJECT_ID"] != self.project_id:
            raise ValueError("input belongs to another project")
        self.revision += 1
        inp = dict(inp, EFFECTIVE_FROM_REVISION=self.revision)
        current = self.current(inp["PARAMETER_OR_RULE"], inp["SCOPE"])
        if current:
            inp["SUPERSEDES"] = current["OWNER_INPUT_ID"]
        self.ledger.append(inp)
        return inp

    def current(self, parameter, scope=None):
        cands = [i for i in self.ledger if i["PARAMETER_OR_RULE"] == parameter and (scope is None or i["SCOPE"] == scope)]
        return sorted(cands, key=lambda i: -i["EFFECTIVE_FROM_REVISION"])[0] if cands else None

    def value(self, parameter, scope=None):
        c = self.current(parameter, scope)
        return None if c is None else c["VALUE"]

    def snapshot_hash(self):
        return hashlib.sha256(json.dumps(self.ledger, sort_keys=True, default=str).encode()).hexdigest()[:16]


class Recalculator:
    """Register quantity lines as pure functions f(facts, params) -> value with declared parameter dependencies.
    recompute(changed_parameters) re-evaluates only lines that depend on them; the geometry facts are never re-read."""

    def __init__(self, facts, store):
        self.facts = facts
        self.store = store
        self.lines = {}
        self.values = {}
        self.evaluations = 0

    def register(self, line_id, fn, depends_on):
        self.lines[line_id] = (fn, tuple(depends_on))
        self.values[line_id] = fn(self.facts, self.store)
        self.evaluations += 1

    def recompute(self, changed_parameters):
        touched = []
        for lid, (fn, deps) in self.lines.items():
            if any(p in deps for p in changed_parameters):
                self.values[lid] = fn(self.facts, self.store)
                self.evaluations += 1
                touched.append(lid)
        return touched

    def apply(self, inp):
        """Set a new owner input and recompute dependents deterministically."""
        rec = self.store.set(inp)
        touched = self.recompute([rec["PARAMETER_OR_RULE"]])
        return {"INPUT": rec, "RECOMPUTED": touched, "REVISION": self.store.revision}
