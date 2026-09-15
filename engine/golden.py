"""Golden regression fixtures — a guardrail, not a museum.

A golden project pins what a real, audited run produced so that later work
cannot quietly degrade it. The hard part is that a good engine change CAN
legitimately change the numbers: BTH-07 moved because a real geometry defect was
fixed, and E31 will move every irregular room when it lands. A fixture that
demanded byte-identical output forever would make the next correct improvement
look like a regression, and the pressure would then be to keep the old bug.

So expectations come in two kinds and they behave differently:

INVARIANTS are safety properties. No benchmark leakage, no geometry mutated by
an agent, no silent default, no quantity released through an unresolved semantic
conflict. These never change. There is no version bump that permits one, and
`check()` reports a violation as a different class of failure from a number that
moved.

EXPECTATIONS are measured values — areas, lengths, accuracy scores, hashes. They
may change, but only deliberately: the fixture's version is bumped and the bump
carries a written root cause, a statement that the change is not specific to this
project, and the list of golden projects whose impact was reviewed. Drift without
that record is a failure, and the failure message says exactly what a legitimate
bump would have to contain.

The asymmetry is the point. Getting a safety property wrong is never acceptable.
Getting a number to move is often progress, and the fixture asks you to say why.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

# What a drift record has to carry before a number is allowed to move.
BUMP_FIELDS = ("root_cause", "not_project_specific", "projects_reviewed", "date")


class GoldenError(RuntimeError):
    """The fixture itself is malformed — not a test failure, a setup failure."""


# Failure classes. These are deliberately not the same word.
INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
EXPECTATION_DRIFT = "EXPECTATION_DRIFT"
INPUT_CHANGED = "INPUT_CHANGED"
MISSING = "MISSING"


@dataclass
class Finding:
    kind: str
    name: str
    expected: object
    actual: object
    note: str = ""

    @property
    def fatal(self) -> bool:
        """An invariant or a changed input can never be waved through."""
        return self.kind in (INVARIANT_VIOLATION, INPUT_CHANGED)

    def __str__(self) -> str:
        base = f"[{self.kind}] {self.name}: expected {self.expected!r}, got {self.actual!r}"
        return f"{base} — {self.note}" if self.note else base


@dataclass
class GoldenReport:
    project: str
    fixture_version: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def violations(self) -> list[Finding]:
        return [f for f in self.findings if f.fatal]

    @property
    def drift(self) -> list[Finding]:
        return [f for f in self.findings if not f.fatal]

    def explain(self) -> str:
        if self.ok:
            return f"{self.project} golden fixture v{self.fixture_version}: clean"
        out = [f"{self.project} golden fixture v{self.fixture_version}:"]
        for f in self.violations:
            out.append(f"  {f}")
        if self.violations:
            out.append("  ^ these are safety properties. There is no version bump "
                       "that permits them.")
        for f in self.drift:
            out.append(f"  {f}")
        if self.drift:
            out.append(
                "  ^ a measured value moved. If that is a correct general "
                "improvement, bump the fixture version and record "
                f"{list(BUMP_FIELDS)} in `drift_log`. If it is not, it is a "
                "regression. Do not edit the expected value on its own.")
        return "\n".join(out)


@dataclass
class GoldenFixture:
    """One audited project, frozen."""

    project: str
    fixture_version: str
    inputs: dict[str, str]                       # path -> sha256
    invariants: dict[str, object]                # safety; never change
    expectations: dict[str, object]              # measured; may move with a bump
    ambiguities: dict[str, object] = field(default_factory=dict)
    drift_log: list[dict] = field(default_factory=list)
    notes: str = ""
    root: Path | None = None

    def __post_init__(self) -> None:
        if not self.invariants:
            raise GoldenError(
                f"{self.project}: a fixture with no invariants pins nothing that "
                "matters. Safety properties are the half that cannot move.")
        for i, entry in enumerate(self.drift_log):
            missing = [f for f in BUMP_FIELDS if not entry.get(f)]
            if missing:
                raise GoldenError(
                    f"{self.project}: drift_log[{i}] is missing {missing}. A version "
                    "bump without a root cause is the same as editing the expected "
                    "value by hand.")

    # ---- checking ---------------------------------------------------------

    def check_inputs(self) -> list[Finding]:
        """The drawing and the space map must be the ones that were audited."""
        out = []
        base = self.root or Path(".")
        for rel, want in sorted(self.inputs.items()):
            p = base / rel
            if not p.exists():
                out.append(Finding(MISSING, rel, want, None,
                                   "the frozen input is not on disk — a fixture that "
                                   "cannot reach its own inputs proves nothing"))
                continue
            got = hashlib.sha256(p.read_bytes()).hexdigest()
            if got != want:
                out.append(Finding(INPUT_CHANGED, rel, want, got,
                                   "the audited input itself changed, so every "
                                   "expectation below is about a different drawing"))
        return out

    def check(self, observed: dict[str, object], *, inputs: bool = True) -> GoldenReport:
        """Compare a fresh run against the fixture."""
        findings: list[Finding] = []
        if inputs:
            findings += self.check_inputs()
        for name, want in sorted(self.invariants.items()):
            if name not in observed:
                findings.append(Finding(MISSING, name, want, None,
                                        "a safety property was not measured at all, "
                                        "which is not the same as it passing"))
            elif observed[name] != want:
                findings.append(Finding(INVARIANT_VIOLATION, name, want, observed[name]))
        for name, want in sorted(self.expectations.items()):
            if name not in observed:
                continue                      # not every run measures everything
            if observed[name] != want:
                findings.append(Finding(EXPECTATION_DRIFT, name, want, observed[name]))
        return GoldenReport(self.project, self.fixture_version, findings)

    # ---- loading ----------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict, root: Path | None = None) -> "GoldenFixture":
        return cls(
            project=data["project"],
            fixture_version=data["fixture_version"],
            inputs=dict(data.get("inputs", {})),
            invariants=dict(data.get("invariants", {})),
            expectations=dict(data.get("expectations", {})),
            ambiguities=dict(data.get("ambiguities", {})),
            drift_log=list(data.get("drift_log", [])),
            notes=data.get("notes", ""),
            root=root,
        )

    @classmethod
    def load(cls, path: str | Path, root: Path | None = None) -> "GoldenFixture":
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")),
                             root=root or p.parent)


def forbidden_strings(benchmark_path: str | Path) -> list[str]:
    """Every value in the sealed site benchmark, as text a leak audit can grep.

    Derived from the benchmark file rather than typed into a list, so a figure
    added to the benchmark is automatically something the audit looks for. A
    hand-maintained list of forbidden numbers goes stale the first time someone
    adds a row and forgets.

    Keys beginning with an underscore are skipped: they hold commentary and the
    engine's OWN figures, which were always in the input package and are not
    answers. The `_allow` list names anything else that is legitimately
    production input — the project id, a space id. Everything remaining in the
    file is a manual answer nobody may see.
    """
    data = json.loads(Path(benchmark_path).read_text(encoding="utf-8"))
    allow = set(data.get("_allow", []))
    out: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if not str(k).startswith("_"):
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float, str)):
            s = str(node).strip()
            # Short tokens match everything; only distinctive values are useful.
            if len(s) >= 4 and s not in allow:
                out.add(s)

    walk(data)
    return sorted(out - allow)
