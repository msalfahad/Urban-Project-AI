"""E44 — a quantity that can be traced back to the drawing it came from.

The CostX idea worth copying is not a spreadsheet feature. It is that every
number on a report is an OBJECT with an identity and a provenance chain, so
"where did 8.6 m come from" has an answer that does not require rerunning
anything. That is what this module builds.

    Q-23010-2F-BTH03-CERWALL-GROSS-001

The id is structured so a human can read it and a machine can match it across
revisions. It is NOT derived from list position: a quantity that keeps its
identity when a wall moves 100 mm is the whole point of revision intelligence,
and a positional id loses that on the first inserted room.

WHAT A TRACE IS NOT. It is not a calculation. This module stores what an
engine decided, with the inputs it decided from; it never multiplies, deducts
or converts. If a value is absent it stays absent — a trace that fills a gap
is worse than no trace, because it looks authoritative.

    NULL RULE SET MUST NEVER MEAN DEFAULT RULE.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

# Where a quantity is in its life. Not a quality score — a gate.
DRAFT = "DRAFT"
VALIDATED = "VALIDATED"
SUPERSEDED = "SUPERSEDED"
WITHDRAWN = "WITHDRAWN"

# How an entity is matched to its counterpart in another revision. The point of
# persistent ids is that this is answerable at all.
MATCH_EXACT_ID = "EXACT_ID"
MATCH_GEOMETRY = "GEOMETRY_WITHIN_TOLERANCE"
MATCH_SEMANTIC = "SEMANTIC_AND_LOCATION"
MATCH_NONE = "NO_MATCH"

QUANTITY_ID = re.compile(
    r"^Q-(?P<project>[A-Z0-9]+)-(?P<floor>[A-Z0-9]+)-(?P<space>[A-Z0-9]+)"
    r"-(?P<trade>[A-Z0-9]+)-(?P<basis>GROSS|NET|DIRECT)-(?P<seq>\d{3})$")


class TraceError(RuntimeError):
    """A quantity was presented without the provenance it must carry."""


def quantity_id(project: str, floor: str, space_id: str, trade: str,
                basis: str, seq: int = 1) -> str:
    """Build a readable, stable quantity id.

    Stable means: the same physical quantity in the same space for the same
    trade gets the same id next revision. Nothing here uses list order, a row
    number, or a hash of the value — the value is the thing most likely to
    change.
    """
    def clean(v: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", str(v).upper())
    if basis not in ("GROSS", "NET", "DIRECT"):
        raise TraceError(
            f"basis {basis!r} must be GROSS, NET or DIRECT. A quantity whose "
            "basis is unstated gets read as net, and a gross figure read as "
            "net is an under-measure nobody notices")
    qid = (f"Q-{clean(project)}-{clean(floor)}-{clean(space_id)}"
           f"-{clean(trade)}-{basis}-{seq:03d}")
    if not QUANTITY_ID.match(qid):
        raise TraceError(f"{qid!r} is not a well-formed quantity id")
    return qid


@dataclass(frozen=True)
class QuantityTrace:
    """One quantity, and the whole chain behind it.

    Every field that names a source is required to be present in the record
    even when it is empty, because an absent key reads as "not applicable" and
    an empty one reads as "nobody established this". They are different facts.
    """

    quantity_id: str
    space_id: str
    use: str
    unit: str
    value: float | None = None

    drawing_id: str = ""
    revision_id: str = ""

    geometry_source: str = ""
    boundary_edge_ids: tuple[str, ...] = ()

    height_id: str = ""
    height_source: str = ""
    height_truth_domain: str = ""

    opening_ids: tuple[str, ...] = ()

    trade_rule_id: str = ""
    trade_rule_version: str = ""

    assembly_id: str = ""
    assembly_version: str = ""

    calculation_reference: str = ""

    validation_status: str = DRAFT
    release_status: str = ""
    primary_blocker: str = ""

    # Filled in later by the viewer layer; declared now so the schema does not
    # have to change when it is.
    drawing_preview_reference: str = ""
    highlight_geometry_reference: str = ""

    def __post_init__(self):
        if not QUANTITY_ID.match(self.quantity_id):
            raise TraceError(
                f"{self.quantity_id!r} is not a well-formed quantity id; a "
                "quantity without a stable identity cannot be compared across "
                "revisions, which is the only reason the id exists")
        if self.value is not None and not self.release_status:
            raise TraceError(
                f"{self.quantity_id} carries a value with no release status. A "
                "figure printed without the status that governs it gets quoted")

    @property
    def is_released(self) -> bool:
        return self.release_status == "READY" and self.value is not None

    def record(self) -> dict:
        """Every field, including the empty ones. An absent key hides a gap."""
        return {
            "quantity_id": self.quantity_id, "space_id": self.space_id,
            "use": self.use, "value": self.value, "unit": self.unit,
            "drawing_id": self.drawing_id, "revision_id": self.revision_id,
            "geometry_source": self.geometry_source,
            "boundary_edge_ids": list(self.boundary_edge_ids),
            "height_id": self.height_id, "height_source": self.height_source,
            "height_truth_domain": self.height_truth_domain,
            "opening_ids": list(self.opening_ids),
            "trade_rule_id": self.trade_rule_id,
            "trade_rule_version": self.trade_rule_version,
            "assembly_id": self.assembly_id,
            "assembly_version": self.assembly_version,
            "calculation_reference": self.calculation_reference,
            "validation_status": self.validation_status,
            "release_status": self.release_status,
            "primary_blocker": self.primary_blocker,
            "drawing_preview_reference": self.drawing_preview_reference,
            "highlight_geometry_reference": self.highlight_geometry_reference,
        }

    def gaps(self) -> list[str]:
        """What this trace cannot answer. The honest half of provenance."""
        out = []
        if not self.boundary_edge_ids:
            out.append("no boundary geometry is named")
        if not self.height_id and "WALL" in self.use or "PLASTER" in self.use:
            out.append("no height record is named")
        if not self.trade_rule_id:
            out.append("no trade rule is named")
        if not self.opening_ids and self.use.startswith("NET_"):
            out.append("a NET quantity names no openings to have deducted")
        return out


@dataclass
class TraceLedger:
    """Every quantity in a run, addressable by id."""

    project_id: str
    revision_id: str = ""
    traces: list[QuantityTrace] = field(default_factory=list)

    def by_id(self) -> dict[str, QuantityTrace]:
        return {t.quantity_id: t for t in self.traces}

    def add(self, trace: QuantityTrace) -> QuantityTrace:
        if trace.quantity_id in self.by_id():
            raise TraceError(
                f"{trace.quantity_id} already exists in this ledger. Two "
                "quantities sharing an id makes both untraceable")
        self.traces.append(trace)
        return trace

    def summary(self) -> dict:
        return {
            "quantities": len(self.traces),
            "released": sum(1 for t in self.traces if t.is_released),
            "with_a_value": sum(1 for t in self.traces if t.value is not None),
            "by_validation_status": dict(Counter(
                t.validation_status for t in self.traces)),
            "by_use": dict(Counter(t.use for t in self.traces)),
            "traces_with_gaps": sum(1 for t in self.traces if t.gaps()),
            "commonest_gap": (Counter(
                g for t in self.traces for g in t.gaps()).most_common(1) or
                [(None, 0)])[0][0],
        }
