"""A sandbox holds admitted inputs and nothing else, checked before launch.

The breach this exists to make impossible: a file the input contract
REFUSED was nevertheless supplied to a cold agent, because the sandbox was
assembled by hand with a copy command and the contract was consulted
afterwards. A gate you can walk around is a note, not a gate.

So two things hold here, and the second is what makes the first real:

    THE ONLY WAY IN      bytes reach the sandbox through place(), which
                         screens the input first and WRITES NOTHING when
                         the contract refuses. A refused input cannot be
                         placed: it raises
    THE ONLY WAY OUT     immediately before the agent is launched,
                         verify() walks the sandbox on disk and requires

                             SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST

                         byte for byte. Anything present that was not
                         admitted fails the launch, however it got there —
                         a copy command, an editor, another process

The one exception is declared in advance: directories the agent writes its
own working files into. Those must be EMPTY at verification time, because
"created after execution starts" is a claim that can be checked rather
than trusted — if a working directory already has files in it before
launch, something put them there.

launch_token() is the only thing that says a sandbox is ready, and it is
issued by verify(), not asked for. A caller that launches without one has
not checked.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from engine import blind_input_contract as bic
from engine import export_provenance as prov

MODEL = "A_SANDBOX_HOLDS_ONLY_ADMITTED_INPUTS_V1"

EQUAL = "SANDBOX_CONTENTS_EQUAL_THE_ADMITTED_INPUT_MANIFEST"
MISMATCH = "SANDBOX_CONTENTS_DIFFER_FROM_THE_ADMITTED_INPUT_MANIFEST"

UNADMITTED_PRESENT = "A_FILE_IS_PRESENT_THAT_WAS_NEVER_ADMITTED"
ADMITTED_MISSING = "AN_ADMITTED_INPUT_IS_NOT_ON_DISK"
BYTES_DIFFER = "AN_ADMITTED_INPUT_HAS_DIFFERENT_BYTES_ON_DISK"
WORKING_DIR_NOT_EMPTY = "A_DECLARED_WORKING_DIRECTORY_IS_NOT_EMPTY"

A_GATE_YOU_CAN_WALK_AROUND = (
    "a gate you can walk around is a note, not a gate. The contract "
    "refusing an input means nothing unless the sandbox physically cannot "
    "hold it")


class RefusedInput(RuntimeError):
    """place() was given an input the contract refuses. Nothing written."""


class SandboxMismatch(RuntimeError):
    """The sandbox on disk is not the admitted manifest."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Sandbox:
    """The directory a cold agent will see, and the record of how it got there."""

    root: Path
    run: bic.BlindRun
    working_dirs: tuple = ()
    placed: dict = field(default_factory=dict)   # rel path -> sha256
    refused: list = field(default_factory=list)
    _verified: str = ""

    def __post_init__(self):
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        for name in self.working_dirs:
            (self.root / name).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ placing
    def place(self, item: bic.Input, *, at: str) -> bic.Decision:
        """Screen, then write. A refused input raises and writes nothing."""
        decision = self.run.offer(item)
        if not decision.admitted:
            self.refused.append({"at": at, **decision.record()})
            raise RefusedInput(
                f"{item.input_id} was refused by {decision.refused_by} "
                f"({decision.would_be or 'no category'}) and is NOT in the "
                f"sandbox. {decision.why} — {A_GATE_YOU_CAN_WALK_AROUND}")
        target = self.root / at
        if target.exists():
            raise SandboxMismatch(
                f"{at} is already in the sandbox. A sandbox is assembled "
                "once, so that what is in it has one history")
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.path:
            shutil.copy2(item.path, target)
        else:
            target.write_text(
                json.dumps(item.content, indent=2, ensure_ascii=False,
                           default=str) + "\n", encoding="utf-8")
        self.placed[at] = _sha256_bytes(target.read_bytes())
        self._verified = ""
        return decision

    def place_all(self, pairs) -> list:
        return [self.place(item, at=at) for item, at in pairs]

    # ----------------------------------------------------------- checking
    def _on_disk(self) -> dict:
        out = {}
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(self.root))
                out[rel] = _sha256_bytes(path.read_bytes())
        return out

    def _in_working_dir(self, rel: str) -> bool:
        return any(rel == d or rel.startswith(d.rstrip("/") + "/")
                   for d in self.working_dirs)

    def verify(self) -> dict:
        """SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST, byte for byte."""
        disk = self._on_disk()
        problems = []
        for rel, digest in sorted(disk.items()):
            if self._in_working_dir(rel):
                problems.append({"problem": WORKING_DIR_NOT_EMPTY,
                                 "file": rel,
                                 "why": ("a declared working directory must "
                                         "be empty before launch. 'created "
                                         "after execution starts' is a "
                                         "claim that can be checked")})
                continue
            if rel not in self.placed:
                problems.append({"problem": UNADMITTED_PRESENT, "file": rel,
                                 "sha256": digest,
                                 "why": ("it is on disk in the sandbox and "
                                         "was never admitted. However it "
                                         "got there, the agent would see "
                                         "it")})
            elif self.placed[rel] != digest:
                problems.append({"problem": BYTES_DIFFER, "file": rel,
                                 "admitted_sha256": self.placed[rel],
                                 "on_disk_sha256": digest})
        for rel in sorted(self.placed):
            if rel not in disk:
                problems.append({"problem": ADMITTED_MISSING, "file": rel})

        status = EQUAL if not problems else MISMATCH
        report = {
            "MODEL": MODEL,
            "invariant": "SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST",
            "checked": "IMMEDIATELY_BEFORE_LAUNCH",
            "status": status,
            "admitted_files": len(self.placed),
            "files_on_disk": len(disk),
            "declared_working_dirs": list(self.working_dirs),
            "problems": problems,
            "refused_and_not_placed": list(self.refused),
            "why": A_GATE_YOU_CAN_WALK_AROUND,
            "files": [{"file": k, "sha256": v}
                      for k, v in sorted(self.placed.items())],
        }
        report["SANDBOX_HASH"] = prov.canonical_sha256(
            {"files": report["files"], "status": status})
        self._verified = report["SANDBOX_HASH"] if status == EQUAL else ""
        return report

    def assert_ready(self) -> dict:
        """Verify, and refuse to hand out a token if anything is off."""
        report = self.verify()
        if report["status"] != EQUAL:
            raise SandboxMismatch(
                f"{MISMATCH}: "
                + "; ".join(f"{p['problem']} {p.get('file', '')}"
                            for p in report["problems"][:6])
                + f". {A_GATE_YOU_CAN_WALK_AROUND}")
        return report

    def launch_token(self) -> str:
        """Proof that this sandbox was checked. Issued by verify() only."""
        if not self._verified:
            raise SandboxMismatch(
                "this sandbox has not been verified since it last changed. "
                "A caller that launches without a token has not checked")
        return self._verified

    def manifest(self) -> dict:
        man = self.run.manifest()
        man["sandbox"] = self.verify()
        man["SANDBOX_EQUALS_ADMITTED_INPUTS"] = (
            man["sandbox"]["status"] == EQUAL)
        return man
