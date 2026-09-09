"""E5 — Approval & Audit Log.

Append-only. Every change records what changed, from what value to what, who
decided, and when — and nothing is ever edited or deleted. This is what makes
the whole system traceable: when a number is wrong you can walk backwards to the
decision and the drawing it came from.

Maps directly to the web app's existing `auditLogs` collection, so entries this
engine records are the same entries Urban Projects Manager shows.

The append-only guarantee is structural: the log exposes `record()` and reads,
never an edit or delete. A frozen `AuditEntry` cannot be mutated after creation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    """One immutable record of a change or a decision."""

    timestamp: str          # ISO 8601, server clock
    actor: str              # who decided (person or agent id)
    action: str             # e.g. "approve", "edit_rate", "override_quantity"
    entity: str             # what it concerns, e.g. "boqItem:abc" / "project:TEST-x"
    field: str = ""         # the field changed, if any
    from_value: Any = None
    to_value: Any = None
    reason: str = ""
    ref: str = ""           # a drawing/sheet/row or source reference

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditLog:
    """An append-only sequence of audit entries.

    Deliberately offers no way to edit or remove an entry. In production the
    same entries are written to Firestore `auditLogs` via a writer; here they
    accumulate in memory (and can be dumped for a test or a report).
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(
        self,
        *,
        actor: str,
        action: str,
        entity: str,
        field: str = "",
        from_value: Any = None,
        to_value: Any = None,
        reason: str = "",
        ref: str = "",
        now: datetime | None = None,
    ) -> AuditEntry:
        """Append one entry and return it. The only way to add to the log."""
        if not actor.strip():
            raise ValueError("an actor is required for every audit entry")
        if not action.strip():
            raise ValueError("an action is required for every audit entry")
        entry = AuditEntry(
            timestamp=(now or datetime.now(timezone.utc)).isoformat(),
            actor=actor,
            action=action,
            entity=entity,
            field=field,
            from_value=from_value,
            to_value=to_value,
            reason=reason,
            ref=ref,
        )
        self._entries.append(entry)
        return entry

    # -- reads only -------------------------------------------------------
    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    @property
    def entries(self) -> tuple[AuditEntry, ...]:
        """A read-only view — the internal list is never handed out."""
        return tuple(self._entries)

    def for_entity(self, entity: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.entity == entity]

    def by_actor(self, actor: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.actor == actor]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries]


def firestore_audit_writer(db: Any):
    """Build a writer that mirrors entries into the app's `auditLogs`.

    Usage (production): pass entries as they are recorded, e.g. in an approval
    gate, so the web app's audit view stays in step. Kept as a factory so
    firebase-admin is only imported when actually writing.
    """

    def _write(entry: AuditEntry) -> str:
        ref = db.collection("auditLogs").document()
        ref.set(entry.to_dict())
        return ref.id

    return _write
