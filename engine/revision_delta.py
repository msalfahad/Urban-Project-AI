"""E11 — Revision Delta.

A new drawing revision produces a change report — what moved, what it costs —
instead of a silent re-price. Compares two BOQ snapshots keyed by item id and
reports added / removed / changed lines with the cost impact.
Deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BoqSnapshotLine:
    id: str
    description: str
    quantity: float
    unit: str
    amount: float


@dataclass
class LineChange:
    id: str
    description: str
    field: str          # "quantity" | "amount" | ...
    from_value: float
    to_value: float


@dataclass
class RevisionReport:
    added: list[BoqSnapshotLine] = field(default_factory=list)
    removed: list[BoqSnapshotLine] = field(default_factory=list)
    changed: list[LineChange] = field(default_factory=list)
    cost_delta: float = 0.0

    def is_material(self, tol: float = 0.01) -> bool:
        return bool(self.added or self.removed or self.changed) and abs(self.cost_delta) > tol


def diff(old: list[BoqSnapshotLine], new: list[BoqSnapshotLine],
         qty_tol: float = 1e-6) -> RevisionReport:
    old_by = {l.id: l for l in old}
    new_by = {l.id: l for l in new}
    rep = RevisionReport()

    for lid, nl in new_by.items():
        if lid not in old_by:
            rep.added.append(nl)
            rep.cost_delta += nl.amount
        else:
            ol = old_by[lid]
            if abs(ol.quantity - nl.quantity) > qty_tol:
                rep.changed.append(LineChange(lid, nl.description, "quantity",
                                              ol.quantity, nl.quantity))
            if abs(ol.amount - nl.amount) > 0.01:
                rep.changed.append(LineChange(lid, nl.description, "amount",
                                              ol.amount, nl.amount))
                rep.cost_delta += nl.amount - ol.amount

    for lid, ol in old_by.items():
        if lid not in new_by:
            rep.removed.append(ol)
            rep.cost_delta -= ol.amount

    return rep
