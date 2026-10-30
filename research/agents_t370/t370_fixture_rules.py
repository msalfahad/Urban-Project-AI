"""T-370: sanitary fixtures and floor drains as a COUNT, two sources reconciled fixture by fixture (B12-01).

A fixture is a physical item placed in a room. Each source (the architectural plan, the sanitary / drainage plan) is
read on its own first: what it PRINTS (a symbol, a block, a legend tag such as 'FD', a label). Only then are the two
matched. One physical fixture is counted once, whichever source shows it; where the two sources show the same
position with a different type the item is a CONFLICT and is never counted as agreed; a type that no symbol, legend
or label prints is UNKNOWN and is never guessed. A drain is a drain only where a drain symbol / legend tag is printed:
a floor fall (slope arrow) is not a drain. Supply type, brand or rating is never inferred.

Research module, no engine import, no rule version: it reports, it does not release a quantity.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

ARCH = "ARCH"
SAN = "SAN"

# Physical kinds a drawing can print. ROOF_DRAIN is kept as its own population (rain-water outlet on a roof), never
# merged into FLOOR_DRAIN: different element, different BOQ line.
WC = "WC"
BASIN = "BASIN"
SHOWER_TRAY = "SHOWER_TRAY"          # a drawn tray / enclosure outline
SHOWER_WALKIN = "SHOWER_WALKIN"      # a screen line closing a zone, with a shower valve drawn in it; no tray drawn
BATH_TUB = "BATH_TUB"
SINK = "SINK"
BIDET = "BIDET"
SHATTAF = "SHATTAF"
FLOOR_DRAIN = "FLOOR_DRAIN"
ROOF_DRAIN = "ROOF_DRAIN"
UNKNOWN = "UNKNOWN"
KINDS = (WC, BASIN, SHOWER_TRAY, SHOWER_WALKIN, BATH_TUB, SINK, BIDET, SHATTAF, FLOOR_DRAIN, ROOF_DRAIN, UNKNOWN)
FIXTURE_KINDS = (WC, BASIN, SHOWER_TRAY, SHOWER_WALKIN, BATH_TUB, SINK, BIDET, SHATTAF)

# What may type an item. Anything else (a guess from the room name, a fall arrow, 'usual practice') is refused.
BASIS_SYMBOL = "SYMBOL_DRAWN"        # the fixture's own outline is drawn (block or linework)
BASIS_LEGEND = "LEGEND_TAG"          # a tag the sheet's legend defines (e.g. 'FD' = floor drain, 'RWD' = rain water drain)
BASIS_LABEL = "PRINTED_LABEL"        # a printed word naming the item
BASES = (BASIS_SYMBOL, BASIS_LEGEND, BASIS_LABEL)
REFUSED_BASES = ("ROOM_NAME", "FALL_ARROW", "GUESS", "PRACTICE", "OTHER_SOURCE")

AGREE = "AGREE"
ARCH_ONLY = "ARCH_ONLY"
SAN_ONLY = "SAN_ONLY"
CONFLICT = "CONFLICT"
STATUS_UNKNOWN = "UNKNOWN"


class FixtureRefused(ValueError):
    """An item typed without printed evidence, or a fixture counted twice."""


@dataclass(frozen=True)
class Item:
    source: str           # ARCH or SAN
    ref: str              # source handle (DXF handle) or sheet reference (page / point)
    floor: str
    room: str             # room anchor (the architectural room-tag handle, or a named space)
    kind: str
    basis: str
    note: str = ""

    def __post_init__(self):
        if self.source not in (ARCH, SAN):
            raise FixtureRefused(f"{self.ref}: source {self.source!r} is neither ARCH nor SAN")
        if self.kind not in KINDS:
            raise FixtureRefused(f"{self.ref}: kind {self.kind!r} not a printed kind")
        if self.basis in REFUSED_BASES or self.basis not in BASES:
            raise FixtureRefused(
                f"{self.ref}: a {self.kind} typed from {self.basis!r} is not printed evidence (never guessed)")
        if self.kind == UNKNOWN and self.basis == BASIS_LABEL:
            raise FixtureRefused(f"{self.ref}: a printed label names its item; UNKNOWN cannot carry a label basis")


@dataclass
class Entry:
    floor: str
    room: str
    kind: str
    status: str
    arch: Item | None = None
    san: Item | None = None
    note: str = ""

    def record(self) -> dict:
        return OrderedDict(
            floor=self.floor, room=self.room, kind=self.kind, status=self.status,
            arch_ref=self.arch.ref if self.arch else None, arch_basis=self.arch.basis if self.arch else None,
            san_ref=self.san.ref if self.san else None, san_basis=self.san.basis if self.san else None,
            note=self.note)


def reconcile(arch_items, san_items, links=()):
    """Match the two sources. `links` pairs (arch ref, san ref) that a reader established as the SAME physical item
    (same room, same position). Each item may appear in at most one link, and each ref only once per source."""
    arch = {}
    for it in arch_items:
        if it.source != ARCH:
            raise FixtureRefused(f"{it.ref}: an {it.source} item in the ARCH list")
        if it.ref in arch:
            raise FixtureRefused(f"{it.ref}: the same ARCH item listed twice (double count)")
        arch[it.ref] = it
    san = {}
    for it in san_items:
        if it.source != SAN:
            raise FixtureRefused(f"{it.ref}: an {it.source} item in the SAN list")
        if it.ref in san:
            raise FixtureRefused(f"{it.ref}: the same SAN item listed twice (double count)")
        san[it.ref] = it
    used_a, used_s = set(), set()
    entries = []
    for a_ref, s_ref in links:
        if a_ref not in arch or s_ref not in san:
            raise FixtureRefused(f"link {a_ref} <-> {s_ref}: unknown item")
        if a_ref in used_a or s_ref in used_s:
            raise FixtureRefused(f"link {a_ref} <-> {s_ref}: an item linked twice (one fixture counted twice)")
        used_a.add(a_ref)
        used_s.add(s_ref)
        a, s = arch[a_ref], san[s_ref]
        if (a.floor, a.room) != (s.floor, s.room):
            raise FixtureRefused(f"link {a_ref} <-> {s_ref}: the two items are in different rooms")
        if UNKNOWN in (a.kind, s.kind):
            entries.append(Entry(a.floor, a.room, UNKNOWN, STATUS_UNKNOWN, a, s, "a side prints no type"))
        elif a.kind == s.kind:
            entries.append(Entry(a.floor, a.room, a.kind, AGREE, a, s))
        else:
            entries.append(Entry(a.floor, a.room, f"{a.kind}|{s.kind}", CONFLICT, a, s,
                                 "same position, different printed type: recorded, neither picked"))
    for ref, a in arch.items():
        if ref not in used_a:
            st = STATUS_UNKNOWN if a.kind == UNKNOWN else ARCH_ONLY
            entries.append(Entry(a.floor, a.room, a.kind, st, a, None, a.note))
    for ref, s in san.items():
        if ref not in used_s:
            st = STATUS_UNKNOWN if s.kind == UNKNOWN else SAN_ONLY
            entries.append(Entry(s.floor, s.room, s.kind, st, None, s, s.note))
    return entries


def counts(entries, floors=None):
    """pcs per kind and floor, split by status. 'drawn' = AGREE + ARCH_ONLY + SAN_ONLY (each physical item once);
    CONFLICT and UNKNOWN are reported beside it and never added to it."""
    out = OrderedDict()
    for e in entries:
        if e.status in (CONFLICT, STATUS_UNKNOWN):
            key = (e.status, e.floor)
            out.setdefault(key, 0)
            out[key] += 1
            continue
        row = out.setdefault((e.kind, e.floor), OrderedDict(AGREE=0, ARCH_ONLY=0, SAN_ONLY=0))
        row[e.status] += 1
    table = OrderedDict()
    for (kind, floor), v in out.items():
        if floors and floor not in floors:
            continue
        if isinstance(v, int):
            table.setdefault(kind, OrderedDict())[floor] = OrderedDict(held=v)
        else:
            table.setdefault(kind, OrderedDict())[floor] = OrderedDict(v, drawn=sum(v.values()))
    return table


def totals(entries):
    """pcs per kind over all floors: drawn, and how many of those AGREE; conflict / unknown separately."""
    t = OrderedDict()
    for e in entries:
        if e.status in (CONFLICT, STATUS_UNKNOWN):
            t.setdefault(e.status, 0)
            t[e.status] += 1
            continue
        r = t.setdefault(e.kind, OrderedDict(drawn=0, AGREE=0, ARCH_ONLY=0, SAN_ONLY=0))
        r["drawn"] += 1
        r[e.status] += 1
    return t


def wet_room_check(entries, room_class):
    """Cross-check against the wet / dry class each room carries. Returns (wet rooms with no fixture,
    wet rooms with a drain but no fixture, fixtures in a room classed DRY)."""
    fixtures = {}
    drains = {}
    for e in entries:
        key = (e.floor, e.room)
        if e.kind in FIXTURE_KINDS and e.status in (AGREE, ARCH_ONLY, SAN_ONLY):
            fixtures[key] = fixtures.get(key, 0) + 1
        if e.kind == FLOOR_DRAIN and e.status in (AGREE, ARCH_ONLY, SAN_ONLY):
            drains[key] = drains.get(key, 0) + 1
    no_fixture, drain_only, in_dry = [], [], []
    for key, cls in room_class.items():
        if cls == "WET" and not fixtures.get(key):
            (drain_only if drains.get(key) else no_fixture).append(key)
        if cls == "DRY" and fixtures.get(key):
            in_dry.append(key)
    return no_fixture, drain_only, in_dry
