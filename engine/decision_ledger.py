"""E1.3 §16 — one ledger, and every account of the decision reads from it.

Frozen E1.2 Kitchen says three different things about why it was
withheld. Its VALIDATION block fails NO_SITE_FACE_LEAKAGE. Its
RELEASE_DECISION.failed lists only the visual challenge. Its prose `why`
repeats the validation note, naming a condition that is not in the failed
set at all. Three records, one decision, and a reader cannot tell which
of them is the reason.

The cure is not better prose. It is that the prose has no independent
source: every failure, every withheld reason and every sentence of
explanation is derived from one ledger of checks, and a check that was
never allowed to gate a release cannot appear as the reason for one.
"""

from __future__ import annotations

import hashlib

MODEL = "ONE_LEDGER_AND_EVERY_ACCOUNT_OF_THE_DECISION_READS_FROM_IT_V1"

PASS = "PASS"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
RESULTS = (PASS, FAIL, NOT_APPLICABLE)

RELEASE_GATING = "RELEASE_GATING"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
KINDS = (RELEASE_GATING, DIAGNOSTIC_ONLY)

RELEASED = "RELEASED"
WITHHELD = "WITHHELD"
DECISIONS = (RELEASED, WITHHELD)

A_DIAGNOSTIC_IS_NOT_A_GATE = (
    "a check kept for information tells a reader something about the "
    "drawing. It does not decide anything, and the moment it appears as "
    "the reason a region was withheld the record has two authorities and "
    "no way to choose between them")

EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER = (
    "the failed list, the withheld reason and the prose all come from the "
    "same rows. There is no second place to write a reason, so there is no "
    "way for two reasons to disagree")


class LedgerContradiction(AssertionError):
    """The ledger and the decision it produced do not agree."""


def model_hash() -> str:
    return hashlib.sha256(
        "|".join([MODEL] + list(RESULTS) + list(KINDS)
                 + list(DECISIONS)).encode("utf-8")).hexdigest()[:24]


class Ledger:
    """Every check on one candidate, and the single decision they make."""

    def __init__(self, subject: str):
        self.subject = subject
        self._rows = []

    def record(self, check_id: str, *, result: str, kind: str,
               note: str, dimension: str = "") -> None:
        if result not in RESULTS:
            raise ValueError(f"not a result: {result!r}")
        if kind not in KINDS:
            raise ValueError(f"not a check kind: {kind!r}")
        if any(r["CHECK_ID"] == check_id for r in self._rows):
            raise LedgerContradiction(
                f"{check_id} is recorded twice for {self.subject}. One "
                "check has one result. " + EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER)
        self._rows.append({"CHECK_ID": check_id, "RESULT": result,
                           "KIND": kind, "DIMENSION": dimension,
                           "note": note})

    def gate(self, check_id: str, ok: bool, note: str,
             dimension: str = "") -> None:
        self.record(check_id, result=PASS if ok else FAIL,
                    kind=RELEASE_GATING, note=note, dimension=dimension)

    def diagnostic(self, check_id: str, result: str, note: str,
                   dimension: str = "") -> None:
        self.record(check_id, result=result, kind=DIAGNOSTIC_ONLY,
                    note=note, dimension=dimension)

    # ------------------------------------------------------------ reading
    @property
    def rows(self) -> list:
        return list(self._rows)

    def failed_gates(self) -> list:
        return [r["CHECK_ID"] for r in self._rows
                if r["KIND"] == RELEASE_GATING and r["RESULT"] == FAIL]

    def failed_diagnostics(self) -> list:
        return [r["CHECK_ID"] for r in self._rows
                if r["KIND"] == DIAGNOSTIC_ONLY and r["RESULT"] == FAIL]

    def note_for(self, check_id: str) -> str:
        for r in self._rows:
            if r["CHECK_ID"] == check_id:
                return r["note"]
        raise KeyError(check_id)

    def decision(self) -> str:
        return WITHHELD if self.failed_gates() else RELEASED

    def why(self) -> str:
        """The one sentence, derived - never written independently."""
        failed = self.failed_gates()
        if not failed:
            return (f"{self.subject} is released: every release-gating check "
                    f"passed ({sum(1 for r in self._rows if r['KIND'] == RELEASE_GATING)} "
                    "of them).")
        parts = "; ".join(f"{c} ({self.note_for(c)})" for c in failed)
        return (f"{self.subject} is withheld because these release-gating "
                f"checks failed: {parts}.")

    # -------------------------------------------------------- consistency
    def assert_consistent(self, *, decision=None, failed=None,
                          why=None) -> None:
        """Refuse any record that disagrees with the ledger."""
        mine_d, mine_f, mine_w = self.decision(), self.failed_gates(), self.why()
        if decision is not None and decision != mine_d:
            raise LedgerContradiction(
                f"{self.subject}: the record says {decision} and the ledger "
                f"says {mine_d}. " + EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER)
        if failed is not None and sorted(failed) != sorted(mine_f):
            extra = sorted(set(failed) - set(mine_f))
            missing = sorted(set(mine_f) - set(failed))
            diag = [c for c in extra if c in self.failed_diagnostics()]
            msg = (f"{self.subject}: the failed list does not match the "
                   f"ledger. Not in the ledger as a failed gate: {extra}. "
                   f"Failed in the ledger but absent from the list: "
                   f"{missing}.")
            if diag:
                msg += (f" {diag} are DIAGNOSTIC_ONLY and may never appear "
                        "as a release reason. " + A_DIAGNOSTIC_IS_NOT_A_GATE)
            raise LedgerContradiction(msg)
        if why is not None and why != mine_w:
            raise LedgerContradiction(
                f"{self.subject}: the prose was written independently of "
                f"the ledger.\n  record: {why}\n  ledger: {mine_w}\n"
                + EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER)
        for c in self.failed_diagnostics():
            if c in mine_f:
                raise LedgerContradiction(
                    f"{self.subject}: {c} is recorded both as a diagnostic "
                    "and as a gate. " + A_DIAGNOSTIC_IS_NOT_A_GATE)

    def record_out(self) -> dict:
        """The canonical block every register quotes, and none rewrites."""
        self.assert_consistent()
        return {
            "LEDGER_MODEL": MODEL,
            "SUBJECT": self.subject,
            "CHECKS": self.rows,
            "counts": {
                "release_gating": sum(1 for r in self._rows
                                      if r["KIND"] == RELEASE_GATING),
                "diagnostic_only": sum(1 for r in self._rows
                                       if r["KIND"] == DIAGNOSTIC_ONLY),
            },
            "FAILED_RELEASE_GATES": self.failed_gates(),
            "FAILED_DIAGNOSTICS_WHICH_DECIDE_NOTHING":
                self.failed_diagnostics(),
            "DECISION": self.decision(),
            "WHY": self.why(),
            "a_diagnostic_is_not_a_gate": A_DIAGNOSTIC_IS_NOT_A_GATE,
            "every_account_derives_from_the_ledger":
                EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER,
        }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "RESULTS": list(RESULTS),
        "KINDS": list(KINDS),
        "DECISIONS": list(DECISIONS),
        "why": {
            "a_diagnostic_is_not_a_gate": A_DIAGNOSTIC_IS_NOT_A_GATE,
            "every_account_derives_from_the_ledger":
                EVERY_ACCOUNT_DERIVES_FROM_THE_LEDGER,
        },
    }
