"""E10 — Funnel / CRM.

Counts the drop-off: conversations → qualified → drawings received → quoted →
signed. Conversion by source, and why the lost ones were lost. Deterministic
counting over lead records; gives E-nothing-fancy but the baseline the owner
asked for.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

STAGES = ["conversation", "qualified", "drawings", "quoted", "signed"]
_ORDER = {s: i for i, s in enumerate(STAGES)}


@dataclass
class Lead:
    id: str
    source: str = "unknown"     # whatsapp | instagram | referral | ...
    stage: str = "conversation"
    lost: bool = False
    lost_reason: str = ""


@dataclass
class FunnelReport:
    counts: dict[str, int]              # reached-this-stage-or-further
    conversion: dict[str, float]        # stage → % of conversations that reached it
    by_source: dict[str, dict[str, int]]
    lost_reasons: dict[str, int]

    @property
    def signed_rate(self) -> float:
        return self.conversion.get("signed", 0.0)


def analyse(leads: list[Lead]) -> FunnelReport:
    reached = {s: 0 for s in STAGES}
    for ld in leads:
        idx = _ORDER.get(ld.stage, 0)
        for s in STAGES[: idx + 1]:
            reached[s] += 1

    total = reached["conversation"] or 1
    conversion = {s: reached[s] / total * 100 for s in STAGES}

    by_source: dict[str, dict[str, int]] = {}
    for ld in leads:
        d = by_source.setdefault(ld.source, {s: 0 for s in STAGES})
        idx = _ORDER.get(ld.stage, 0)
        for s in STAGES[: idx + 1]:
            d[s] += 1

    lost = Counter(ld.lost_reason or "unspecified" for ld in leads if ld.lost)
    return FunnelReport(counts=reached, conversion=conversion,
                        by_source=by_source, lost_reasons=dict(lost))
