"""V3.0 GATE B v2 (T-168), FIRST COMMIT: the regression baseline only. This module delegates to tools/v30_gate_b.py
(T-156) unchanged, so the ported adversarial probes (tests/t168_gate_b_v2/test_probes_t168.py, strict xfail) fail as
they do on the merged head. The fix commit replaces this file. Nothing imports it (rollback: delete this file).
"""

from __future__ import annotations

from engine.reference_mapping import refuse_if_sealed
from tools import v30_gate_b as G1

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only check tool; it produces no quantity


class Refused(Exception):
    def __init__(self, problems):
        self.problems = list(problems)
        self.codes = sorted({c for c, _ in self.problems})
        super().__init__("; ".join(f"{c}: {t}" for c, t in self.problems))


def diff(before, after, **kw):
    """today's behaviour: the T-156 diff; manifests, verdicts and change logs are not read."""
    return G1.diff(before, after, register=kw.get("register"), ledgers=kw.get("ledgers"))


def guard_inputs(paths, registry=None):
    """today's behaviour: the guard by file name only (engine.reference_mapping)."""
    for p in paths.values():
        refuse_if_sealed(str(p))
    return {}
