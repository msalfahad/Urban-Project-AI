"""TERMINAL_OBJECT_LEDGER - every admitted quantity-bearing object ends in exactly one terminal record.

    led = Ledger()
    led.admit(obj_id, obj_type, source_ref, admission_state="ADMITTED")
    led.terminate(obj_id, terminal_state, quantity_status, blocking_reason=None, downstream_trade=None,
                  release_state=None)
    led.check() -> {"admitted": n, "terminated": n, "unterminated": [...], "unknown_terminations": [...],
                    "double_terminations": [...], "conserved": bool}

UNKNOWN IS ALLOWED, UNACCOUNTED IS NOT: a terminal state may be BLOCKED / AMBIGUOUS / SOURCE_CONFLICT; an object
that is admitted and never terminated is a disappearance and fails the conservation check.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

from collections import Counter

POLICY_ID = "TERMINAL_OBJECT_LEDGER_V1"


class Ledger:
    def __init__(self):
        self._adm, self._term, self._order = {}, {}, []
        self._unknown, self._double = [], []

    def admit(self, obj_id, obj_type, source_ref=None, admission_state="ADMITTED", **extra):
        if obj_id in self._adm:
            raise ValueError(f"object admitted twice: {obj_id}")
        self._adm[obj_id] = {"object_id": obj_id, "object_type": obj_type, "source_ref": source_ref,
                             "admission_state": admission_state, **extra}
        self._order.append(obj_id)

    def terminate(self, obj_id, terminal_state, quantity_status, blocking_reason=None, downstream_trade=None,
                  release_state=None, **extra):
        if not terminal_state:
            raise ValueError(f"empty terminal state for {obj_id}")
        if obj_id not in self._adm:
            self._unknown.append(obj_id)
            return
        if obj_id in self._term:
            self._double.append(obj_id)
            return
        self._term[obj_id] = {"terminal_state": terminal_state, "quantity_status": quantity_status,
                              "blocking_reason": blocking_reason, "downstream_trade": downstream_trade,
                              "release_state": release_state, **extra}

    def rows(self):
        return [dict(self._adm[k], **(self._term.get(k) or {"terminal_state": None})) for k in self._order]

    def check(self) -> dict:
        un = [k for k in self._order if k not in self._term]
        return {"admitted": len(self._adm), "terminated": len(self._term), "unterminated": un,
                "unknown_terminations": list(self._unknown), "double_terminations": list(self._double),
                "conserved": not un and not self._unknown and not self._double,
                "by_type": dict(sorted(Counter(r["object_type"] for r in self._adm.values()).items())),
                "by_terminal_state": dict(sorted(Counter(t["terminal_state"] for t in self._term.values()).items()))}
