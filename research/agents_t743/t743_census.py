"""T-743: B12-01 SANITARY FIXTURES AND FLOOR DRAINS, a per-room count census from two drawings (research only, nothing
wired, no BOQ line produced).

PHYSICAL ELEMENT. One installed sanitary fixture (WC, wash basin, shower tray, walk-in shower zone, bath tub, bidet,
urinal, kitchen sink) or one floor drain / gully, counted once per physical item, in the room that holds it.

TWO SOURCES, NEVER ADDED. The architectural plan and the sanitary (drainage) plan are two representations of one
building. A symbol on each that is the SAME physical fixture (same kind, within MATCH_TOL_M after the sheet is put on
the plan) is ONE fixture; a fixture drawn on one sheet only is still one fixture, and the reconciliation names why the
other sheet does not show it. A count is never the sum of the two sheets.

WHAT IS NOT A FIXTURE. A room-tag block (a block whose only content is text, e.g. a block called 'WC' that prints
'W.C') names a room; it is not a WC. `is_tag_block` decides that from the block CONTENT, never from its name.

NO DEFAULTS. A symbol whose type the drawing does not show (an unrecognised outline) is counted as HELD_UNTYPED: one
physical item, type unresolved, never given a default type. A room whose function needs a point the drawings do not
draw (a kitchen with no sink symbol, a laundry with no washing-machine point) gets a HELD line with its reason, never a
count of 0 and never a default fixture.

Statuses (ENGINEERING_REASONING_STANDARD): MEASURED = counted from a drawn symbol; HELD = needed, not drawn / not typed.
Nothing here is VERIFIED; the Checker re-counts.
"""
from __future__ import annotations

from dataclasses import dataclass, field

METHOD_ID = "SANITARY_FIXTURE_CENSUS_T743_V1"

# fixture kinds counted in pcs (B12-01)
WC = "WC"
BASIN = "BASIN"
SHOWER_TRAY = "SHOWER_TRAY"
SHOWER_WALKIN = "SHOWER_WALKIN"          # a walk-in shower zone: screen line + mixer, no tray drawn
BATH = "BATH"
BIDET = "BIDET"
URINAL = "URINAL"
KITCHEN_SINK = "KITCHEN_SINK"
WASHING_MACHINE_POINT = "WASHING_MACHINE_POINT"
FLOOR_DRAIN = "FLOOR_DRAIN"
UNTYPED = "HELD_UNTYPED"
KINDS = (WC, BASIN, SHOWER_TRAY, SHOWER_WALKIN, BATH, BIDET, URINAL, KITCHEN_SINK, WASHING_MACHINE_POINT,
         FLOOR_DRAIN, UNTYPED)

ARCH = "ARCH_PLAN"
SANITARY = "SANITARY_PLAN"

# two symbols of one kind, one on each sheet, are the same physical fixture when their centres are this close. A
# fixture is 0.4 - 0.9 m across; two real fixtures of one kind stand at least a fixture apart (two basins of a double
# vanity are about 0.6 m centre to centre in this project's sheets), so 0.30 m cannot merge two real fixtures, and it
# absorbs the sheet-to-plan fit (mean 0.02 m, worst 0.03 m on the development villa, T-743 report).
MATCH_TOL_M = 0.30
# a symbol whose centre is outside every room polygon but within this of one (a WC drawn against the wall face) is that
# room's; farther out it is UNASSIGNED and HELD.
ROOM_TOL_M = 0.10

# cause names of a reconciliation
AGREE = "AGREE"
SANITARY_ONLY = "SANITARY_ONLY"
ARCH_ONLY = "ARCH_ONLY"
CAUSE_ARCH_DRAWS_NO_KIND = "ARCH_PLAN_DRAWS_NO_SYMBOL_OF_THIS_KIND_ON_THIS_FLOOR"
CAUSE_ARCH_MISSING_HERE = "SYMBOL_MISSING_ON_THE_ARCH_PLAN_IN_THIS_ROOM"
CAUSE_SAN_DRAWS_NO_KIND = "SANITARY_PLAN_DRAWS_NO_SYMBOL_OF_THIS_KIND_ON_THIS_FLOOR"
CAUSE_SAN_MISSING_HERE = "SYMBOL_MISSING_ON_THE_SANITARY_PLAN_IN_THIS_ROOM"
CAUSE_SAN_NOT_READ = "SANITARY_PLAN_OF_THIS_FLOOR_NOT_READ"

# room functions that need a point the drawings may not draw (HELD when absent, never 0)
NEEDS_POINT = {"KITCHEN": KITCHEN_SINK, "LAUNDRY": WASHING_MACHINE_POINT}


# ------------------------------------------------------------------------------------------------------- geometry
def _pip(x, y, poly):
    ins, n = False, len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def _seg_dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _dist(x, y, poly):
    if _pip(x, y, poly):
        return 0.0
    return min(_seg_dist(x, y, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


@dataclass(frozen=True)
class SheetFit:
    """a sanitary sheet's point (sheet units, y down) -> plan metres: x = a + s*u*mx, y = b - s*v (mirror mx = -1 when
    the sheet is drawn mirrored against the plan)."""
    a: float
    b: float
    s: float
    mirror_x: bool = False

    def to_plan(self, u, v):
        return (self.a + self.s * (-u if self.mirror_x else u), self.b - self.s * v)


def fit_sheet(pairs, mirror_x=False):
    """least-squares SheetFit from >= 2 (sheet point, plan point) pairs of the SAME physical object (e.g. a basin block
    drawn on both sheets). -> (fit, residuals in m). Fewer than 2 pairs, or a degenerate set: ValueError."""
    if len(pairs) < 2:
        raise ValueError("a sheet fit needs at least two shared objects")
    sg = -1.0 if mirror_x else 1.0
    n = len(pairs)
    us = [sg * p[0][0] for p in pairs]
    vs = [p[0][1] for p in pairs]
    xs = [p[1][0] for p in pairs]
    ys = [p[1][1] for p in pairs]
    mu, mv, mx, my = sum(us) / n, sum(vs) / n, sum(xs) / n, sum(ys) / n
    den = sum((u - mu) ** 2 for u in us) + sum((v - mv) ** 2 for v in vs)
    if den <= 0:
        raise ValueError("the shared objects are one point: no scale")
    s = (sum((u - mu) * (x - mx) for u, x in zip(us, xs)) - sum((v - mv) * (y - my) for v, y in zip(vs, ys))) / den
    if s <= 0:
        raise ValueError("negative scale: the sheet is mirrored against the plan (try mirror_x)")
    f = SheetFit(a=mx - s * mu, b=my + s * mv, s=s, mirror_x=mirror_x)
    res = [((f.to_plan(*p[0])[0] - p[1][0]) ** 2 + (f.to_plan(*p[0])[1] - p[1][1]) ** 2) ** 0.5 for p in pairs]
    return f, res


# a fit whose worst shared object lands farther than this from its plan position is no fit: a rotated or wrong-scale
# sheet, or a wrong anchor. Half of ROOM_TOL_M + MATCH_TOL_M is the most a symbol may move before a 1.2 m wide WC
# room could lose it (development villa: worst 0.092 m, from anchors read by hand at 100 dpi).
FIT_MAX_RESIDUAL_M = 0.10


def check_fit(residuals):
    """ValueError when the sheet fit does not hold (a rotated sheet, a wrong scale, a mismatched anchor): no symbol of
    that sheet is placed in a room, so nothing of it is counted (HELD by the caller, never 0)."""
    worst = max(residuals) if residuals else None
    if worst is None or worst > FIT_MAX_RESIDUAL_M:
        raise ValueError(f"sheet fit does not hold: worst anchor residual {worst} m > {FIT_MAX_RESIDUAL_M} m")
    return worst


# ------------------------------------------------------------------------------------------------- what is a tag
def is_tag_block(entity_types):
    """a block whose content is text only (TEXT / MTEXT / ATTDEF / ATTRIB) is a room tag, not a fixture, whatever its
    name. An empty block is not evidence of anything (False: it is no tag and it is no fixture either)."""
    t = [str(x).upper() for x in entity_types]
    return bool(t) and all(x in ("TEXT", "MTEXT", "ATTDEF", "ATTRIB") for x in t)


def fixture_symbols(inserts, *, source=None):
    """plan inserts -> (fixture Symbols, tag counts). inserts: [{"name", "kind" (a KINDS value or None),
    "entity_types" (the block's content types), "at_m", "floor"}]. A block of text only is a room tag and is counted in
    tags, never as a fixture, whatever its name says; an insert with no kind is not sanitary and is skipped."""
    syms, tags = [], {}
    for i in inserts:
        if i.get("kind") is None:
            continue
        if is_tag_block(i.get("entity_types") or ()):
            tags[i["name"]] = tags.get(i["name"], 0) + 1
            continue
        syms.append(Symbol(kind=i["kind"], at_m=tuple(i["at_m"]), source=source or ARCH, floor=i["floor"],
                           ref=i.get("ref") or i["name"]))
    return syms, tags


# ------------------------------------------------------------------------------------------------------ the census
@dataclass
class Symbol:
    kind: str
    at_m: tuple                      # plan metres (after the sheet fit for a sanitary symbol)
    source: str                      # ARCH or SANITARY
    floor: str
    ref: str = ""                    # the symbol's own id on its sheet
    size_in: float | None = None     # a floor drain's printed size (inches), when printed
    note: str = ""


@dataclass
class Room:
    room_id: str
    floor: str
    polygon_m: list
    codes: tuple = ()                # the room's function words (BATHROOM, KITCHEN, LAUNDRY ...)


@dataclass
class Census:
    rooms: dict = field(default_factory=dict)       # room_id -> {"fixtures": [...], "held": [...], "recon": [...]}
    unassigned: list = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    held_totals: dict = field(default_factory=dict)
    drains_by_size: dict = field(default_factory=dict)


def assign(sym, rooms):
    """-> room_id of the room holding the symbol (inside, or within ROOM_TOL_M of one room on its floor), or None."""
    best = None
    for r in rooms:
        if r.floor != sym.floor:
            continue
        d = _dist(sym.at_m[0], sym.at_m[1], r.polygon_m)
        if d <= ROOM_TOL_M and (best is None or d < best[0]):
            best = (d, r.room_id)
    return best[1] if best else None


def census(rooms, arch_symbols, sanitary_symbols, *, sanitary_floors_read):
    """count every fixture once, per room and kind, reconcile the two sheets per room to a named cause.

    rooms: [Room]; arch_symbols / sanitary_symbols: [Symbol] (tags already removed by is_tag_block);
    sanitary_floors_read: the floors whose sanitary sheet was read (a floor not read never makes an arch-only
    fixture look missing on the sanitary sheet)."""
    for s in list(arch_symbols) + list(sanitary_symbols):
        if s.kind not in KINDS:
            raise ValueError(f"unknown fixture kind {s.kind!r}")
    out = Census()
    placed = {}
    for s in list(arch_symbols) + list(sanitary_symbols):
        rid = assign(s, rooms)
        if rid is None:
            out.unassigned.append({"kind": s.kind, "source": s.source, "floor": s.floor, "ref": s.ref,
                                   "state": "HELD", "reason": "outside every room of its floor"})
            continue
        placed.setdefault(rid, {ARCH: [], SANITARY: []})[s.source].append(s)
    arch_kinds_on_floor = {}
    san_kinds_on_floor = {}
    for s in arch_symbols:
        arch_kinds_on_floor.setdefault(s.floor, set()).add(s.kind)
    for s in sanitary_symbols:
        san_kinds_on_floor.setdefault(s.floor, set()).add(s.kind)

    for r in rooms:
        a_syms = list(placed.get(r.room_id, {}).get(ARCH, []))
        s_syms = list(placed.get(r.room_id, {}).get(SANITARY, []))
        fixtures, recon = [], []
        used = set()
        for a in a_syms:                                         # an arch symbol and its sanitary twin = one fixture
            twin = None
            for j, s in enumerate(s_syms):
                if j in used or s.kind != a.kind:
                    continue
                d = ((a.at_m[0] - s.at_m[0]) ** 2 + (a.at_m[1] - s.at_m[1]) ** 2) ** 0.5
                if d <= MATCH_TOL_M and (twin is None or d < twin[0]):
                    twin = (d, j)
            if twin:
                used.add(twin[1])
                s = s_syms[twin[1]]
                fixtures.append({"kind": a.kind, "state": "HELD" if a.kind == UNTYPED else "MEASURED",
                                 "sources": [ARCH, SANITARY], "refs": [a.ref, s.ref],
                                 "size_in": s.size_in if s.size_in is not None else a.size_in})
                recon.append({"kind": a.kind, "status": AGREE, "refs": [a.ref, s.ref],
                              "offset_m": round(twin[0], 3)})
            else:
                if r.floor not in sanitary_floors_read:
                    cause = CAUSE_SAN_NOT_READ
                elif a.kind not in san_kinds_on_floor.get(r.floor, set()):
                    cause = CAUSE_SAN_DRAWS_NO_KIND
                else:
                    cause = CAUSE_SAN_MISSING_HERE
                fixtures.append({"kind": a.kind, "state": "HELD" if a.kind == UNTYPED else "MEASURED",
                                 "sources": [ARCH], "refs": [a.ref], "size_in": a.size_in})
                recon.append({"kind": a.kind, "status": ARCH_ONLY, "cause": cause, "refs": [a.ref]})
        for j, s in enumerate(s_syms):
            if j in used:
                continue
            cause = (CAUSE_ARCH_DRAWS_NO_KIND if s.kind not in arch_kinds_on_floor.get(r.floor, set())
                     else CAUSE_ARCH_MISSING_HERE)
            fixtures.append({"kind": s.kind, "state": "HELD" if s.kind == UNTYPED else "MEASURED",
                             "sources": [SANITARY], "refs": [s.ref], "size_in": s.size_in})
            recon.append({"kind": s.kind, "status": SANITARY_ONLY, "cause": cause, "refs": [s.ref]})
        held = []
        for code, need in NEEDS_POINT.items():
            if code in r.codes and not any(f["kind"] == need for f in fixtures):
                held.append({"kind": need, "state": "HELD", "pcs": None,
                             "reason": f"a {code.lower()} needs a {need.lower().replace('_', ' ')}; neither sheet draws "
                                       "one (designer item, never 0, never a default)"})
        out.rooms[r.room_id] = {"floor": r.floor, "codes": list(r.codes), "fixtures": fixtures, "held": held,
                                "recon": recon}
        for f in fixtures:
            key = f["kind"]
            if f["state"] == "MEASURED":
                out.totals[key] = out.totals.get(key, 0) + 1
            else:
                out.held_totals[key] = out.held_totals.get(key, 0) + 1
            if key == FLOOR_DRAIN:
                sz = "UNPRINTED" if f["size_in"] is None else f'{f["size_in"]:g}in'
                out.drains_by_size[sz] = out.drains_by_size.get(sz, 0) + 1
        for h in held:
            out.held_totals[h["kind"]] = out.held_totals.get(h["kind"], 0) + 1
    for u in out.unassigned:
        out.held_totals["UNASSIGNED_" + u["kind"]] = out.held_totals.get("UNASSIGNED_" + u["kind"], 0) + 1
    return out


def table(c):
    """per room: kind -> pcs (MEASURED), and the reconciliation statuses; for reports and tests."""
    rows = []
    for rid, r in sorted(c.rooms.items()):
        if not r["fixtures"] and not r["held"]:
            continue
        cnt = {}
        for f in r["fixtures"]:
            k = f["kind"] if f["state"] == "MEASURED" else f["kind"] + "(HELD)"
            cnt[k] = cnt.get(k, 0) + 1
        rows.append({"room_id": rid, "floor": r["floor"], "pcs": dict(sorted(cnt.items())),
                     "arch": sum(1 for f in r["fixtures"] if ARCH in f["sources"]),
                     "sanitary": sum(1 for f in r["fixtures"] if SANITARY in f["sources"]),
                     "recon": sorted({x["status"] + ("" if x["status"] == AGREE else ":" + x["cause"])
                                      for x in r["recon"]}),
                     "held": [h["kind"] for h in r["held"]]})
    return rows
