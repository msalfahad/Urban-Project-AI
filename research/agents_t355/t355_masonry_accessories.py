"""T-355 (research, unwired): three OPTIONAL masonry-accessory items of the blocks section, measured apart from the
block area and from each other (owner, Q-77 answer 2026-10-29 21:22 and his four points of 2026-10-29; any villa).

PHYSICAL ELEMENTS (ERS s.2.1)
- BED-JOINT MESH STRIP (m.l): an expanded-metal strip laid in the mortar bed joint on top of every third block course,
  along the wall, where block stands both under and over that joint. Its quantity is the NET INSTALLED length per
  joint level; a lap or roll waste is procurement, never part of it. A width is a product property, never a quantity.
- SHARMAT (شرمات, pcs): a metal tie with one end fixed to a column face and the other laid in the block bed joint, one
  per third course at every physical wall-to-column junction (one block end against one column face). An Urban
  estimating rule, NOT a structural design: material, size, anchorage and fixing stay SPECIFICATION HELD.
- PLASTER-STAGE JOINT MESH (B9-03, m.l): a strip over a block-to-concrete joint inside a finished face, by face class.
  The joint population itself is T-317's; this module only classes it (R-T355-4).

RULES (every villa; provenance in the T-355 report)
- R-T355-1 COURSES: a course module = block height + bed joint, from a CourseSpec that names its source. Course n
  (n >= 1) sits on a starting bed of one joint: its top is at n x module above the wall's own base; the bed joint over
  course n is [n x module, n x module + joint]. A mesh / tie level is the joint over course 3k (k >= 1) and exists
  where block stands above it: level + joint < block top (a partial top course counts; it is reported). No fractional
  course, no level above the block top. No CourseSpec (a thin-bed / adhesive block without its specification, or an
  unknown block height) -> the wall's levels are HELD by name, never 0.
- R-T355-2 NET STRIP: per level, strip = sum of block pieces standing over the level - every opening that occupies the
  joint layer (bottom < level + joint and top > level) - the lintel over an opening where the lintel occupies the joint
  layer (span cut: concrete); the lintel BEARINGS (printed minimum, actual length not drawn) are HELD at that level,
  capped to the block present. An opening whose sill / head / lintel depth is not established holds its own width
  (plus its bearings above the sill) at the levels it may reach; nothing else is held. Columns are never in the strip.
- R-T355-6 (r2, Checker D-T355-1 2026-10-30): at a level ABOVE a known lintel top (head + lintel depth <= level) an
  opening never cuts and never holds the strip, whatever piece it stands under: the masonry is continuous over the
  lintel wherever the level exists. An opening whose lintel depth is unknown still holds (R-T355-2).
- R-T355-7 (r2): the partial top course is judged per block piece, not from the wall's highest top: a level is flagged
  partial_above when any piece standing over it has less than a full block height above the joint (report only; the
  joint and the strip exist).
- R-T355-3 JUNCTIONS ONCE: a junction = one boundary between a block segment and a column piece in a run (consecutive
  block pieces are one segment); keyed (wall, run, station); the same key twice is refused. Ties per junction = the
  levels of R-T355-1 that exist on the block segment beside the column. An unknown block top there -> HELD.
- R-T355-4 PLASTER JOINT MESH BY FACE CLASS: A plastered / painted, B tiled, C exterior Sigma system, D no plaster / no
  render = EXCLUDED. A, B and C are reported separately and never summed into one released figure; a side whose rooms
  are of two classes (no station split) is MIXED: its length is shown, its class split HELD.
- R-T355-5 SEPARATE ITEMS: the three items are never added to the block m2 or to each other; they may coincide at one
  junction (a tie, a strip end and a vertical plaster joint) without a double count because they are different items.

Units: metres; `units="mm"` converts every length on entry (a 0.2 m module given as 200 with units="m" is refused).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TOL = 1e-6
SCHEMA = "T355_MASONRY_ACCESSORIES_V1"
FACE_CLASSES = {"A": "plastered / painted", "B": "tiled", "C": "exterior Sigma system", "D": "no plaster / render"}


class AccessoryError(ValueError):
    pass


def _m(v, units):
    if v is None:
        return None
    if units == "m":
        return float(v)
    if units == "mm":
        return float(v) / 1000.0
    raise AccessoryError(f"unknown units {units!r}")


@dataclass(frozen=True)
class CourseSpec:
    block_h: float
    joint: float
    source: str
    status: str                      # ASSUMED — OWNER-APPROVED / DRAWING-CONFIRMED / ...

    @property
    def module(self):
        return self.block_h + self.joint


def course_spec(block_h, joint, source, status, units="m"):
    h, j = _m(block_h, units), _m(joint, units)
    if not source:
        raise AccessoryError("a course spec needs its source (no default block or joint)")
    if not (0.05 <= h <= 0.40):
        raise AccessoryError(f"block height {h} m outside 0.05 .. 0.40 m (units?)")
    if not (0.0 < j <= 0.03):
        raise AccessoryError(f"bed joint {j} m outside 0 .. 0.03 m (units?)")
    return CourseSpec(h, j, source, status)


@dataclass(frozen=True)
class Piece:
    kind: str                        # BLOCK or COLUMN
    length: float
    top: float | None = None         # BLOCK: block top above the wall base; None = not established
    key: str = ""                    # station / member id


@dataclass(frozen=True)
class Opening:
    oid: str
    width: float
    bottom: float | None             # lowest point of the hole in the masonry above the wall base (door: 0)
    top: float | None                # head of the hole above the wall base
    lintel_d: float | None           # depth of the lintel over it (printed schedule); None = not established
    bearing: float | None            # printed minimum bearing each end; None = not printed
    status: str = ""


@dataclass(frozen=True)
class Panel:
    wall_id: str
    floor: str
    pieces: tuple                    # Piece in run order (several runs: their pieces, runs separated by key prefix)
    openings: tuple
    course: CourseSpec | None
    held: str = ""                   # a cause that leaves every level of the wall unknown
    runs: tuple = ()                 # run keys, for the junction keys


def make_piece(kind, length, top=None, key="", units="m"):
    L, t = _m(length, units), _m(top, units)
    if kind not in ("BLOCK", "COLUMN"):
        raise AccessoryError(f"piece kind {kind}")
    if L <= 0:
        raise AccessoryError(f"piece length {L}")
    if t is not None and not (0.5 <= t <= 10.0):
        raise AccessoryError(f"block top {t} m outside 0.5 .. 10.0 m (units?)")
    return Piece(kind, L, t, key)


def make_opening(oid, width, bottom, top, lintel_d=None, bearing=None, status="", units="m"):
    w, b, t = _m(width, units), _m(bottom, units), _m(top, units)
    if w <= 0:
        raise AccessoryError(f"{oid}: width {w}")
    if b is not None and t is not None and not (0 <= b < t):
        raise AccessoryError(f"{oid}: bottom {b} / top {t}")
    return Opening(oid, w, b, t, _m(lintel_d, units), _m(bearing, units), status)


def levels(course: CourseSpec, top: float):
    """mesh / tie levels (R-T355-1) on a block piece of the given top: k, level, height of the course above it."""
    out = []
    k = 1
    while True:
        z = 3 * k * course.module
        if z + course.joint >= top - TOL:
            break
        out.append((k, round(z, 6), round(min(course.block_h, top - z - course.joint), 6)))
        k += 1
    return out


def level_set(panel: Panel):
    tops = [p.top for p in panel.pieces if p.kind == "BLOCK" and p.top is not None]
    if not tops or panel.course is None:
        return []
    return levels(panel.course, max(tops))


def _gross(panel, z, j):
    g = held = 0.0
    for p in panel.pieces:
        if p.kind != "BLOCK":
            continue
        if p.top is None:
            held += p.length
        elif z + j < p.top - TOL:
            g += p.length
    return g, held


def mesh_levels(panel: Panel):
    """one record per mesh level of the wall: gross block length over it, cuts (openings, lintel spans), held segments
    with causes, net installed strip. Returns (records, state) with state HELD when the wall has no levels."""
    if panel.held:
        return [], f"HELD: {panel.held}"
    if panel.course is None:
        return [], "HELD: course height not established (no course spec for this block type)"
    if not any(p.kind == "BLOCK" and p.top is not None for p in panel.pieces):
        return [], "HELD: no block top established on the wall"
    j = panel.course.joint
    known = [p.top for p in panel.pieces if p.kind == "BLOCK" and p.top is not None]
    tmin, tmax = min(known), max(known)
    recs = []
    for k, z, above in level_set(panel):
        gross, held = _gross(panel, z, j)
        cut_o = cut_l = 0.0
        hold = []
        if held > TOL:
            hold.append(("BLOCK_TOP_UNKNOWN", held, "block top over these pieces not established"))
        for o in panel.openings:
            bear = 2 * o.bearing if o.bearing is not None else 0.0
            if o.bottom is None:
                hold.append(("OPENING_EXTENT_UNKNOWN", o.width + bear, f"{o.oid}: sill / head not established"))
                continue
            if z + j <= o.bottom + TOL:     # the joint layer lies at or under the sill: it runs under the opening
                continue
            if o.top is None:
                hold.append(("OPENING_EXTENT_UNKNOWN", o.width + bear, f"{o.oid}: head not established"))
                continue
            in_open = o.bottom < z + j - TOL and o.top > z + TOL
            # the opening's station is not tied to the pieces: where the wall also has pieces of unknown top, or the
            # level is at / above the lowest block top, the opening may stand in either: its width is HELD, not cut
            ambiguous = held > TOL or z + j >= tmin - TOL
            if in_open:
                if ambiguous:
                    hold.append(("POSITION_UNKNOWN", o.width, f"{o.oid}: opening not tied to a piece of known top"))
                else:
                    cut_o += o.width
                continue
            # above the head
            if o.lintel_d is None:
                if z + j < tmin - TOL:
                    hold.append(("LINTEL_UNKNOWN", o.width + bear, f"{o.oid}: lintel over the head not established"))
                elif z + j < tmax - TOL:
                    hold.append(("POSITION_UNKNOWN", o.width, f"{o.oid}: host block top not tied to the opening"))
                continue
            lt = o.top + o.lintel_d
            if o.top < z + j - TOL and lt > z + TOL:
                if ambiguous:
                    hold.append(("POSITION_UNKNOWN", o.width + bear, f"{o.oid}: lintel not tied to a piece of known top"))
                    continue
                cut_l += o.width
                if bear > TOL:
                    hold.append(("LINTEL_BEARING", bear, f"{o.oid}: lintel bearing (printed minimum, length not drawn)"))
                continue
            # R-T355-6 (r2, D-T355-1): the level is above a KNOWN lintel top (lt <= z): the opening interrupts nothing
            # at this joint. Wherever the level exists (decided by the piece tops, already in gross) the masonry runs
            # continuously over the lintel; the opening's station does not matter: no cut, no hold.
        avail = gross - cut_o - cut_l
        if avail < -1e-6:
            raise AccessoryError(f"{panel.wall_id} level {z}: cuts {cut_o + cut_l} exceed the block {gross}")
        held_in = 0.0
        hold_out = []
        for cause, L, why in hold:
            if cause == "BLOCK_TOP_UNKNOWN":
                hold_out.append((cause, round(L, 6), why))
                continue
            take = max(0.0, min(L, avail - held_in))
            held_in += take
            hold_out.append((cause, round(take, 6), why))
        net = avail - held_in
        # R-T355-7 (r2): the course above the level is judged PER PIECE (a two-top wall can have a full course over
        # its high pieces and a cut one over its low pieces); course_above_h_m = the smallest course above over the
        # pieces standing at this level, partial_above_m = their block length under a partial course (report only).
        bh = panel.course.block_h
        over = [(round(min(bh, p.top - z - j), 6), p.length) for p in panel.pieces
                if p.kind == "BLOCK" and p.top is not None and z + j < p.top - TOL]
        above = min(a for a, _ in over) if over else above
        part_m = sum(L for a, L in over if a < bh - TOL)
        recs.append({"wall_id": panel.wall_id, "floor": panel.floor, "k": k, "course_below": 3 * k, "level_m": z,
                     "course_above_h_m": above, "partial_above": above < bh - TOL,
                     "partial_above_m": round(part_m, 6),
                     "gross_m": round(gross, 6), "cut_opening_m": round(cut_o, 6), "cut_lintel_m": round(cut_l, 6),
                     "held_m": round(held_in + sum(L for c, L, _ in hold_out if c == "BLOCK_TOP_UNKNOWN"), 6),
                     "held": hold_out, "net_m": round(net, 6)})
    return recs, "MEASURED" if recs else "NO LEVEL (wall lower than three courses)"


def segments(panel: Panel):
    """block segments and columns in run order, per run: consecutive BLOCK pieces merge into one segment."""
    out = []
    for p in panel.pieces:
        run = p.key.split("@")[0] if "@" in p.key else ""
        if out and out[-1]["kind"] == p.kind == "BLOCK" and out[-1]["run"] == run:
            s = out[-1]
            s["length"] += p.length
            s["tops"].append(p.top)
            continue
        out.append({"kind": p.kind, "run": run, "length": p.length, "tops": [p.top], "key": p.key})
    return out


def junctions(panel: Panel):
    """R-T355-3: each block-segment / column boundary once, with the block top beside the column."""
    segs = segments(panel)
    out, seen = [], set()
    for i in range(len(segs) - 1):
        a, b = segs[i], segs[i + 1]
        if a["run"] != b["run"] or {a["kind"], b["kind"]} != {"BLOCK", "COLUMN"}:
            continue
        blk, col = (a, b) if a["kind"] == "BLOCK" else (b, a)
        top = blk["tops"][-1] if blk is a else blk["tops"][0]
        face = "column_start" if col is b else "column_end"     # the column face the block segment meets
        key = (panel.wall_id, col["key"], face)
        if key in seen:
            raise AccessoryError(f"junction {key} counted twice")
        seen.add(key)
        out.append({"wall_id": panel.wall_id, "floor": panel.floor, "column_at": col["key"],
                    "face": face, "block_segment_m": round(blk["length"], 6), "top": top})
    return out


def ties(panel: Panel, js=None):
    js = junctions(panel) if js is None else js
    out = []
    for jn in js:
        r = dict(jn)
        if panel.held:
            r.update(state="HELD", ties=None, held=panel.held)
        elif panel.course is None:
            r.update(state="HELD", ties=None, held="course height not established (no course spec)")
        elif jn["top"] is None:
            r.update(state="HELD", ties=None, held="block top beside the column not established")
        else:
            r.update(state="MEASURED", ties=len(levels(panel.course, jn["top"])), held="")
        out.append(r)
    return out


def face_class(finishes: set):
    """R-T355-4: class of one wall side from the finishes of the spaces it faces."""
    m = {"PLASTER": "A", "TILE": "B", "SIGMA": "C", "NONE": "D"}
    cl = {m[f] for f in finishes if f in m}
    if set(finishes) - set(m):
        raise AccessoryError(f"unknown finish {sorted(set(finishes) - set(m))}")
    if not cl:
        return "UNKNOWN"
    return cl.pop() if len(cl) == 1 else "MIXED"


def check_separate(block_m2: float, mesh_ml, ties_pcs, joint_ml):
    """R-T355-5: an accessory quantity is never folded into the block m2 (different unit and item)."""
    for name, v in (("mesh strip m.l", mesh_ml), ("sharmat pcs", ties_pcs), ("joint mesh m.l", joint_ml)):
        if isinstance(v, dict) and v.get("added_to") == "block_m2":
            raise AccessoryError(f"{name} added into the block m2 refused (separate optional item, Q-77)")
    return block_m2


def no_zero_held(records):
    for r in records:
        if r.get("state", "").startswith("HELD") and r.get("ties") == 0:
            raise AccessoryError(f"{r.get('wall_id')}: a HELD record carries 0")


def totals(mesh_recs, tie_recs):
    t = {}
    for r in mesh_recs:
        a = t.setdefault(r["floor"], {"net_m": 0.0, "held_m": 0.0, "levels": 0, "ties": 0, "junctions": 0,
                                      "junctions_held": 0})
        a["net_m"] += r["net_m"]
        a["held_m"] += r["held_m"]
        a["levels"] += 1
    for r in tie_recs:
        a = t.setdefault(r["floor"], {"net_m": 0.0, "held_m": 0.0, "levels": 0, "ties": 0, "junctions": 0,
                                      "junctions_held": 0})
        if r["state"] == "MEASURED":
            a["ties"] += r["ties"]
            a["junctions"] += 1
        else:
            a["junctions_held"] += 1
    return {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(t.items())}


def lintel_depth(width_m, schedule):
    """printed lintel schedule row by opening width (integer cm bands, inclusive; a width between bands has no row)."""
    cm = width_m * 100.0
    for lo, hi, d in schedule:
        if lo - 1e-6 <= cm <= hi + 1e-6:
            return d
    return None


def n_levels(course: CourseSpec, top: float):
    return len(levels(course, top))


def _isclose(a, b):
    return math.isclose(a, b, abs_tol=1e-6)
