"""Input/output contract for the template agent.

Uses dataclasses so it stays dependency-free. Swap for pydantic later if you
want richer validation — the shape is what matters: an agent's output is
checked against this before it is ever saved.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Input:
    """What the runner hands the agent."""

    text: str
    context: dict = field(default_factory=dict)


@dataclass
class Output:
    """What the agent must return. Validated before saving."""

    result: str
    notes: str = ""

    def validate(self) -> None:
        if not isinstance(self.result, str) or not self.result.strip():
            raise ValueError("agent output 'result' must be a non-empty string")
