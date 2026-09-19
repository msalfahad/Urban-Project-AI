"""A9 / event bus — loop the agents together.

The architecture rule: no agent calls another agent. Each writes a record; a
trigger wakes whatever comes next. This module is that trigger mechanism in one
place — an event bus. In production the same shape is a Firestore onWrite
trigger; here it is an in-process dispatcher so the whole chain is testable
offline.

A handler receives an Event and may return zero or more new Events; the bus
keeps dispatching until the queue drains. Every event is appended to a log, so
the whole run is traceable — you can walk backwards from any record to the one
that produced it. Handlers are agents or engine modules; the orchestrator only
routes and records, it never computes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass
class Event:
    type: str
    payload: dict = field(default_factory=dict)
    source: str = ""                 # who emitted it
    id: str = ""
    caused_by: str | None = None     # the event id that produced this one
    ts: str = ""


Handler = Callable[["Event"], "list[Event] | None"]


@dataclass
class Dispatch:
    """One recorded step: the event and what it produced."""
    event: Event
    handler: str
    produced: list[str] = field(default_factory=list)
    error: str = ""


class Orchestrator:
    """Routes events to handlers and records every handoff."""

    def __init__(self, *, max_steps: int = 1000) -> None:
        self._handlers: dict[str, list[tuple[str, Handler]]] = {}
        self.log: list[Dispatch] = []
        self._seq = 0
        self._max_steps = max_steps

    def on(self, event_type: str, name: str, handler: Handler) -> None:
        """Register a handler for an event type (an agent or engine module)."""
        self._handlers.setdefault(event_type, []).append((name, handler))

    def _next_id(self) -> str:
        self._seq += 1
        return f"e{self._seq}"

    def emit(self, event: Event) -> list[Dispatch]:
        """Dispatch an event and everything it cascades into, in order."""
        if not event.id:
            event.id = self._next_id()
        if not event.ts:
            event.ts = datetime.now(timezone.utc).isoformat()
        queue: list[Event] = [event]
        run: list[Dispatch] = []
        steps = 0

        while queue:
            steps += 1
            if steps > self._max_steps:
                raise RuntimeError("orchestrator exceeded max steps (possible event loop)")
            ev = queue.pop(0)
            handlers = self._handlers.get(ev.type, [])
            if not handlers:
                self.log.append(Dispatch(event=ev, handler="(unhandled)"))
                run.append(self.log[-1])
                continue
            for name, handler in handlers:
                d = Dispatch(event=ev, handler=name)
                try:
                    produced = handler(ev) or []
                except Exception as exc:  # a handler failure is recorded, not swallowed silently
                    d.error = f"{type(exc).__name__}: {exc}"
                    self.log.append(d)
                    run.append(d)
                    raise
                for ne in produced:
                    if not ne.id:
                        ne.id = self._next_id()
                    ne.caused_by = ev.id
                    if not ne.ts:
                        ne.ts = datetime.now(timezone.utc).isoformat()
                    d.produced.append(ne.id)
                    queue.append(ne)
                self.log.append(d)
                run.append(d)
        return run

    def trace(self) -> list[dict]:
        return [
            {"event": d.event.type, "id": d.event.id, "handler": d.handler,
             "caused_by": d.event.caused_by, "produced": d.produced, "error": d.error}
            for d in self.log
        ]
