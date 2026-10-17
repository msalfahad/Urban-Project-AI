"""E1.2 §11 — one ledger, and every count read off it.

Frozen E1.1's input manifest says, at the top:

    offered = 0
    admitted = 0
    inputs_made_available = []

and lower down, about the same run:

    sandbox.admitted_files = 11
    files_on_disk = 11
    SANDBOX_EQUALS_ADMITTED_INPUTS = true

Both cannot be true. The cause is small and entirely mechanical:
`Sandbox.place()` calls `run.offer()`, gets a decision, uses it to decide
whether to write the bytes - and never appends it to `run.decisions`. The
sandbox knew what it held; the run object it reported through did not.

That is not a leak and nothing untoward reached the run. It is worse in
one way: a manifest that contradicts itself cannot be used as evidence of
anything, including of a clean run.

So E1.2 keeps ONE ledger. Every admission is recorded here as it is made,
and every number a manifest prints - offered, admitted, refused, the
input rows, the sandbox files, their count and the manifest hash - is
derived from this one list. `assert_consistent()` proves they agree, and
it runs before launch, not after.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from engine import agent_sandbox as sbx
from engine import export_provenance as prov

MODEL = "ONE_ADMISSION_LEDGER_AND_EVERY_COUNT_READ_OFF_IT_V1"

ONE_LEDGER = (
    "offered, admitted, refused, the input rows, the sandbox files and "
    "the manifest hash are all derived from ONE list of decisions, "
    "recorded as each admission is made. No number in the manifest is "
    "computed anywhere else")

CONSISTENT = "ADMISSION_LEDGER_IS_SELF_CONSISTENT"
INCONSISTENT = "ADMISSION_LEDGER_CONTRADICTS_ITSELF"


class LedgerInconsistent(RuntimeError):
    """The ledger's own numbers disagree. The run must not launch."""


@dataclass
class Entry:
    input_id: str = ""
    kind: str = ""
    at: str = ""
    admitted: bool = False
    refused_by: str = ""
    would_be: str = ""
    why: str = ""
    identity: dict = field(default_factory=dict)
    sha256: str = ""

    def record(self) -> dict:
        out = {"input_id": self.input_id, "kind": self.kind,
               "placed_at": self.at if self.admitted else None,
               "status": "ADMITTED" if self.admitted
               else "REFUSED_AT_THE_DOOR"}
        out.update(self.identity)
        if self.admitted:
            out["SANDBOX_FILE_SHA256"] = self.sha256
        else:
            out["refused_by"] = self.refused_by
            out["it_would_have_been"] = self.would_be
        out["why"] = self.why
        return out


@dataclass
class Ledger:
    """The one place an admission is recorded."""

    run: object = None
    box: object = None
    entries: list = field(default_factory=list)

    def offer(self, item, *, at: str) -> Entry:
        """Screen and place in one act, and record it here, once."""
        try:
            decision = self.box.place(item, at=at)
            entry = Entry(input_id=getattr(item, "input_id", ""),
                          kind=getattr(item, "kind", ""), at=at,
                          admitted=True, why=decision.why,
                          identity=decision.identity,
                          sha256=self.box.placed.get(at, ""))
        except sbx.RefusedInput as exc:
            dec = self.run.offer(item)
            entry = Entry(input_id=getattr(item, "input_id", ""),
                          kind=getattr(item, "kind", ""), at=at,
                          admitted=False, refused_by=dec.refused_by,
                          would_be=dec.would_be, why=str(exc),
                          identity=dec.identity)
        self.entries.append(entry)
        return entry

    # --- every number below is read off `entries` -------------------
    @property
    def offered(self) -> int:
        return len(self.entries)

    @property
    def admitted(self) -> list:
        return [e for e in self.entries if e.admitted]

    @property
    def refused(self) -> list:
        return [e for e in self.entries if not e.admitted]

    def sandbox_files(self) -> dict:
        return dict(self.box.placed)

    def assert_consistent(self) -> dict:
        """Prove the ledger, the sandbox and the manifest agree."""
        placed = self.sandbox_files()
        report = self.box.verify()
        problems = []
        if len(self.admitted) != len(placed):
            problems.append(
                f"{len(self.admitted)} admitted entries but {len(placed)} "
                "files placed")
        for e in self.admitted:
            if e.at not in placed:
                problems.append(f"{e.input_id} admitted but not placed")
            elif placed[e.at] != e.sha256:
                problems.append(f"{e.at} has different bytes than admitted")
        for at in placed:
            if not any(e.at == at and e.admitted for e in self.entries):
                problems.append(f"{at} is placed but not in the ledger")
        if report["status"] != sbx.EQUAL:
            problems.append(f"sandbox verification says {report['status']}")
        if problems:
            raise LedgerInconsistent(
                INCONSISTENT + ": " + "; ".join(problems) + ". " + ONE_LEDGER)
        return {"status": CONSISTENT,
                "offered": self.offered,
                "admitted": len(self.admitted),
                "refused_at_the_door": len(self.refused),
                "files_in_the_sandbox": len(placed),
                "sandbox_verification": report,
                "every_count_is_read_off_one_ledger": ONE_LEDGER}

    def manifest(self, *, extra=None) -> dict:
        check = self.assert_consistent()
        body = {
            "MODEL": MODEL,
            "ADMISSION_LEDGER": check["status"],
            "counts": {"offered": self.offered,
                       "admitted": len(self.admitted),
                       "refused_at_the_door": len(self.refused),
                       "files_in_the_sandbox": len(self.sandbox_files())},
            "inputs_made_available": [e.record() for e in self.admitted],
            "refused_at_the_door": [e.record() for e in self.refused],
            "sandbox": check["sandbox_verification"],
            "SANDBOX_EQUALS_ADMITTED_INPUTS": True,
            "every_count_is_read_off_one_ledger": ONE_LEDGER,
        }
        if extra:
            body.update(extra)
        body["INPUT_MANIFEST_HASH"] = prov.canonical_sha256(body)
        return body


def model_hash() -> str:
    return hashlib.sha256(f"{MODEL}|{ONE_LEDGER}".encode()).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {"MODEL": MODEL, "why": {"one_ledger": ONE_LEDGER}}
