"""T-317 (research, unwired): SPATTER DASH (B4-05, m2) and MESH AT BLOCK-TO-CONCRETE JOINTS (B9-03, m.l) as
physical-element ledgers for any villa (rules R-T317-1 .. R-T317-5 below).

PHYSICAL ELEMENTS (ERS s.2.1)
- Spatter dash (طرطشة) is the first, cement-slurry bond coat thrown on a wall face before the coat that finishes it.
  Where it applies is a SCOPE fact of the project method, not a geometric one: on the development villa the owner's
  decisions OD-V3B-4 .. 7 (2026-10-04, research/external_engine_lab/alsenan_v3b_owner_decisions.json) put it on EVERY
  finished wall face (dry plaster: spatter -> rough -> smooth -> paint; tiled: spatter -> tile preparation -> tile;
  external Sigma: spatter -> rough -> smooth -> Sigma; stone: spatter -> cladding), "on the same geometric population"
  as the coat it prepares, whatever the substrate (block or concrete). So the item's quantity is the finish face
  population once, never a concrete-only subset; the concrete share is a SUBSTRATE SPLIT of that population.
- Joint mesh (شبك) is a strip laid over a block-to-concrete JOINT inside a finished face: the line where a block panel
  meets a column face (vertical) or the soffit of the beam / slab over it (horizontal). It exists only where a finished
  coat covers both sides of the joint; a joint above the finished band (behind a false ceiling) or on a side with no
  finish is not inside a finished face. Its unit is m.l: a width is a product property of the specification and is
  never part of the measured quantity (no default width is accepted anywhere).

RULES (every villa; provenance in the T-317 report)
- R-T317-1 SCOPE BEFORE NUMBERS: a spatter / mesh quantity is emitted only under a scope record that cites its source
  (an owner decision, a project rule or a drawing note). Without one, the population is listed with its m2 / m.l and
  the item is HELD by name; a HELD item has no quantity (blank), never 0.
- R-T317-2 SPATTER = THE FINISH POPULATION ONCE: one spatter record per finished face of a host finish line (plaster,
  wall tile, external Sigma / cladding); same quantity, range and evidence state as its host, never more, never a
  second host for one face. The substrate split (block / concrete) is reported beside it and must close to it.
- R-T317-3 FACE OWNERSHIP: a concrete face (column side, in-plane beam band, slab edge) belongs to the ONE side (room or
  exterior) it faces; the same (element, side) claimed twice is refused.
- R-T317-4 JOINTS INSIDE THE FINISHED BAND: per wall side, a horizontal joint (block top under a member) is INSIDE when
  band_bottom < top < band_top, AT_BAND_EDGE when it equals band_top (the finish stops on it: not inside a finished
  face, listed by name), ABOVE_BAND when higher, HELD when its level is not established; a vertical joint at a column
  is clipped to the band (min(block top, band_top) - band_bottom) and is HELD where an opening jamb meets the column
  (the joint length depends on the opening's head / sill). A side with no finish has no joint.
- R-T317-5 TWO METHODS SIDE BY SIDE: the owner's band (Q-43 / Q-48 A heights) and the drawing-derived band (to the
  slab soffit) are computed on the same pieces; neither replaces the other.

Units: metres throughout; `units="mm"` converts every length on entry. A storey outside 2.0 .. 10.0 m after conversion
is refused (a mm drawing read as metres, or the reverse).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

TOL = 1e-6
SCHEMA = "T317_SPATTER_MESH_LEDGER_V1"
FINISHED = {"PLASTER", "TILE", "SIGMA", "CLADDING"}
NOT_FINISHED = {"NONE", "HIDDEN"}
STATES = {"VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN"}


class LedgerError(ValueError):
    pass


def _conv(v, units):
    if v is None:
        return None
    if units == "m":
        return float(v)
    if units == "mm":
        return float(v) / 1000.0
    raise LedgerError(f"unknown units {units!r} (m or mm)")


@dataclass(frozen=True)
class Scope:
    """Where an item applies, with its source. `finishes` = the finishes it applies to."""
    item: str                       # "B4-05" or "B9-03"
    source: str | None              # owner decision / project rule / drawing note id; None = not answered
    finishes: frozenset = frozenset()
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.item not in ("B4-05", "B9-03"):
            raise LedgerError(f"unknown item {self.item}")
        for k in self.extra:
            if "width" in k.lower():
                raise LedgerError("a mesh / spatter width is a specification property, never a measured default "
                                  f"(got {k}={self.extra[k]!r}); the item is measured in its own unit only")
        bad = set(self.finishes) - FINISHED
        if bad:
            raise LedgerError(f"scope names non-finish faces {sorted(bad)}")

    def covers(self, finish):
        return self.source is not None and finish in self.finishes


@dataclass(frozen=True)
class Piece:
    """One piece along a wall run. kind BLOCK (top = block top above the storey's structural floor, None = level not
    established; member = what is over it) or COLUMN (an in-plane column piece; member = column id)."""
    kind: str
    length: float
    top: float | None = None
    member: str = ""
    opening_at: tuple = ()          # for COLUMN: ("start"|"end", ...) where an opening jamb meets this column side
    under: str = ""                 # for BLOCK: what its top meets: "BEAM" (a downstand) or "SLAB" (the slab soffit)


@dataclass(frozen=True)
class Side:
    side_id: str                    # room id or "EXT"
    finish: str                     # PLASTER / TILE / SIGMA / CLADDING / NONE / HIDDEN
    band_bottom: float | None       # finished band, above the structural floor (None = not established)
    band_top: float | None


@dataclass(frozen=True)
class Wall:
    wall_id: str
    storey_h: float                 # slab to slab
    pieces: tuple                   # Piece, in run order
    sides: tuple                    # Side, one per face of the wall


def make_wall(wall_id, storey_h, pieces, sides, units="m"):
    s = _conv(storey_h, units)
    if not (2.0 <= s <= 10.0):
        raise LedgerError(f"{wall_id}: storey height {s} m outside 2.0 .. 10.0 m (units?)")
    ps = []
    for p in pieces:
        if p.kind not in ("BLOCK", "COLUMN"):
            raise LedgerError(f"{wall_id}: piece kind {p.kind}")
        L = _conv(p.length, units)
        t = _conv(p.top, units)
        if L <= 0:
            raise LedgerError(f"{wall_id}: piece length {L}")
        if t is not None and not (0 < t <= s + TOL):
            raise LedgerError(f"{wall_id}: block top {t} outside the storey {s}")
        if p.under not in ("", "BEAM", "SLAB"):
            raise LedgerError(f"{wall_id}: piece under {p.under}")
        ps.append(Piece(p.kind, L, t, p.member, tuple(p.opening_at), p.under))
    sd = []
    for x in sides:
        if x.finish not in FINISHED | NOT_FINISHED:
            raise LedgerError(f"{wall_id}: finish {x.finish}")
        b, t = _conv(x.band_bottom, units), _conv(x.band_top, units)
        if b is not None and t is not None and not (0 <= b < t <= s + TOL):
            raise LedgerError(f"{wall_id}/{x.side_id}: band {b} .. {t} outside the storey")
        sd.append(Side(x.side_id, x.finish, b, t))
    if len({x.side_id for x in sd}) != len(sd):
        raise LedgerError(f"{wall_id}: a side listed twice")
    return Wall(wall_id, s, tuple(ps), tuple(sd))


def mirrored(w: Wall) -> Wall:
    """the same wall read from its other end (mirror / reversed run): every quantity must be unchanged."""
    flip = {"start": "end", "end": "start"}
    ps = tuple(Piece(p.kind, p.length, p.top, p.member, tuple(flip[o] for o in p.opening_at), p.under)
               for p in reversed(w.pieces))
    return Wall(w.wall_id, w.storey_h, ps, w.sides)


# ----------------------------------------------------------------------------------------------- faces (substrate)

def face_split(w: Wall, side: Side, claimed: dict | None = None):
    """area of the finished band of one side, split by substrate: block (below each block top), concrete (column
    pieces over the band, and the in-plane member band above a block top inside the band). Returns a dict with
    m2 figures or state HELD (blank) when the band or a block top inside it is not established."""
    if side.finish in NOT_FINISHED:
        return {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "state": "NOT_FINISHED",
                "block_m2": None, "concrete_m2": None, "face_m2": None, "items": []}
    if side.band_bottom is None or side.band_top is None:
        return {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "state": "HELD",
                "held": "finished band not established", "block_m2": None, "concrete_m2": None, "face_m2": None,
                "items": []}
    b, t = side.band_bottom, side.band_top
    H = t - b
    blk = conc = 0.0
    items, held = [], []
    pos = next(k for k, x in enumerate(w.sides) if x is side or x == side)
    for i, p in enumerate(w.pieces):
        if p.kind == "COLUMN":
            if claimed is not None:
                # one column face = (column, wall plane, face of that plane); a second claim of it, from the same
                # or another room, is a double count (R-T317-3). A corner column's faces on two walls are distinct.
                key = (p.member or f"{w.wall_id}#{i}", w.wall_id, pos)
                if key in claimed:
                    raise LedgerError(f"column face {key[0]} of {w.wall_id} face {pos} claimed twice "
                                      f"(now by {side.side_id}, before by {claimed[key]})")
                claimed[key] = side.side_id
            a = p.length * H
            conc += a
            items.append(("COLUMN", p.member, round(a, 6)))
            continue
        if p.top is None:
            held.append(f"block top over {p.member or i} not established ({p.length:.4f} m)")
            continue
        top_in = min(p.top, t)
        a_blk = p.length * max(0.0, top_in - b)
        a_con = p.length * max(0.0, t - max(p.top, b))
        blk += a_blk
        conc += a_con
        if a_con > TOL:
            items.append(("MEMBER_BAND", p.member, round(a_con, 6)))
    if held:
        return {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "state": "HELD",
                "held": "; ".join(held), "block_m2": None, "concrete_m2": None, "face_m2": None, "items": items,
                "established_part_m2": round(blk + conc, 6)}
    face = sum(p.length for p in w.pieces) * H
    if abs(face - blk - conc) > 1e-6:
        raise LedgerError(f"{w.wall_id}/{side.side_id}: substrate split does not close ({face} vs {blk + conc})")
    return {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "state": "MEASURED",
            "block_m2": round(blk, 6), "concrete_m2": round(conc, 6), "face_m2": round(face, 6), "items": items}


# ----------------------------------------------------------------------------------------------- joints

def _h_class(top, side):
    if top is None or side.band_top is None or side.band_bottom is None:
        return "HELD"
    if top > side.band_top + TOL:
        return "ABOVE_BAND"
    if abs(top - side.band_top) <= TOL:
        return "AT_BAND_EDGE"
    if top <= side.band_bottom + TOL:
        return "BELOW_BAND"
    return "INSIDE"


def joints(w: Wall):
    """every block-to-concrete joint of the wall, per finished side, once. Horizontal: each BLOCK piece's top under
    its member. Vertical: each BLOCK / COLUMN boundary. No record on a side without finish (R-T317-4)."""
    out = []
    ps = w.pieces
    for side in w.sides:
        if side.finish in NOT_FINISHED:
            continue
        for i, p in enumerate(ps):
            if p.kind != "BLOCK":
                continue
            c = _h_class(p.top, side)
            out.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "H",
                        "at": p.member, "length_m": round(p.length, 6), "class": c,
                        "level_m": p.top})
        for i in range(len(ps) - 1):
            a, b = ps[i], ps[i + 1]
            if {a.kind, b.kind} != {"BLOCK", "COLUMN"}:
                continue
            blk, col = (a, b) if a.kind == "BLOCK" else (b, a)
            col_end = "start" if col is b else "end"     # which end of the column piece this joint is on
            if col_end in col.opening_at:
                out.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "V",
                            "at": col.member, "length_m": None, "class": "HELD",
                            "held": "an opening jamb meets the column: joint length depends on the opening head / sill"})
                continue
            if blk.top is None or side.band_top is None or side.band_bottom is None:
                out.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "V",
                            "at": col.member, "length_m": None, "class": "HELD",
                            "held": "block top or finished band not established"})
                continue
            L = min(blk.top, side.band_top) - side.band_bottom
            out.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "V",
                        "at": col.member, "length_m": round(max(0.0, L), 6),
                        "class": "INSIDE" if L > TOL else "BELOW_BAND"})
        out += _steps(w, side, lambda t: None if side.band_top is None else
                      min(max(t, side.band_bottom), side.band_top))
    return out


def _steps(w, side, clip):
    """STEP joints: where the member over two adjacent block pieces changes level (a deeper beam crossing or ending
    over the wall), the block meets the deeper member's vertical face over the level difference, clipped to the band."""
    out = []
    ps = w.pieces
    for i in range(len(ps) - 1):
        a, b = ps[i], ps[i + 1]
        if a.kind != "BLOCK" or b.kind != "BLOCK" or a.member == b.member and a.top == b.top:
            continue
        rec = {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "STEP", "at": f"{a.member}/{b.member}"}
        if a.top is None or b.top is None:
            out.append({**rec, "length_m": None, "class": "HELD", "held": "a block top beside the step not established"})
            continue
        if abs(a.top - b.top) <= 1e-3:
            continue
        ca, cb = clip(a.top), clip(b.top)
        if ca is None:
            out.append({**rec, "length_m": None, "class": "HELD", "held": "finished band not established"})
            continue
        L = abs(ca - cb)
        out.append({**rec, "length_m": round(L, 6), "class": "INSIDE" if L > TOL else "ABOVE_BAND"})
    return out


def joints_to_soffit(w: Wall, ffl: float):
    """R-T317-5, DRAWING-DERIVED band: every finished side runs from the finished floor (ffl above the structural floor)
    to the soffit over it. A block top under a downstand beam is then INSIDE the face (the beam's own face continues
    above it to the slab); a block top under the slab soffit is the wall / ceiling corner (AT_BAND_EDGE); a vertical
    joint is the block height above the finished floor. No slab thickness is needed (none is assumed)."""
    out = []
    ps = w.pieces
    for side in w.sides:
        if side.finish in NOT_FINISHED:
            continue
        for p in ps:
            if p.kind != "BLOCK":
                continue
            c = "HELD" if p.top is None or not p.under else ("INSIDE" if p.under == "BEAM" else "AT_BAND_EDGE")
            out.append({"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "H", "at": p.member,
                        "length_m": round(p.length, 6), "class": c, "level_m": p.top})
        for i in range(len(ps) - 1):
            a, b = ps[i], ps[i + 1]
            if {a.kind, b.kind} != {"BLOCK", "COLUMN"}:
                continue
            blk, col = (a, b) if a.kind == "BLOCK" else (b, a)
            col_end = "start" if col is b else "end"
            rec = {"wall": w.wall_id, "side": side.side_id, "finish": side.finish, "dir": "V", "at": col.member}
            if col_end in col.opening_at:
                out.append({**rec, "length_m": None, "class": "HELD",
                            "held": "an opening jamb meets the column: joint length depends on the opening head / sill"})
            elif blk.top is None:
                out.append({**rec, "length_m": None, "class": "HELD", "held": "block top not established"})
            else:
                out.append({**rec, "length_m": round(blk.top - ffl, 6), "class": "INSIDE"})
        out += _steps(w, side, lambda t: t)
    return out


def joint_totals(js):
    t = {}
    for j in js:
        k = (j["dir"], j["finish"], j["class"])
        t.setdefault(k, [0.0, 0])
        if j["length_m"] is not None:
            t[k][0] += j["length_m"]
        t[k][1] += 1
    return {f"{d}|{f}|{c}": (round(v[0], 6), v[1]) for (d, f, c), v in sorted(t.items())}


def mesh_records(js, scope: Scope):
    """B9-03 per joint: only joints INSIDE a finished face; a quantity only under a sourced scope (R-T317-1)."""
    if scope.item != "B9-03":
        raise LedgerError("mesh_records needs the B9-03 scope")
    out = []
    for j in js:
        if j["finish"] in NOT_FINISHED:
            raise LedgerError(f"joint on an unfinished side refused: {j['wall']}/{j['side']}")
        if j["class"] != "INSIDE":
            continue
        if scope.covers(j["finish"]) and j["length_m"] is not None:
            out.append({**j, "item": "B9-03", "unit": "m.l", "quantity": j["length_m"], "state": "MEASURED",
                        "scope_source": scope.source})
        else:
            out.append({**j, "item": "B9-03", "unit": "m.l", "quantity": None, "state": "HELD",
                        "held": "scope not answered (no owner rule, drawing note or specification)"
                        if scope.source is None else f"finish {j['finish']} outside the scope {scope.source}",
                        "population_m": j["length_m"]})
    return out


# ----------------------------------------------------------------------------------------------- spatter from hosts

def spatter_records(host_lines: Iterable[dict], scope: Scope):
    """B4-05 per host finish line (R-T317-2). host: {line_id (or 'NO_LINE:<ref>'), finish, faces (iterable of face
    ids), state, quantity (None = blank), lo, hi, ...}. One record per host, the host's own figures."""
    if scope.item != "B4-05":
        raise LedgerError("spatter_records needs the B4-05 scope")
    seen_face, seen_line, out = {}, set(), []
    for h in host_lines:
        lid = h["line_id"]
        if lid in seen_line:
            raise LedgerError(f"host line {lid} listed twice")
        seen_line.add(lid)
        for f in h.get("faces", ()):
            if f in seen_face:
                raise LedgerError(f"face {f} in two host lines ({seen_face[f]}, {lid})")
            seen_face[f] = lid
        q, lo, hi = h.get("quantity"), h.get("lo"), h.get("hi")
        st = h["state"]
        if st not in STATES:
            raise LedgerError(f"{lid}: state {st}")
        if st == "HELD" and q is not None:
            raise LedgerError(f"{lid}: a HELD host carries no quantity (got {q})")
        if st != "HELD" and q is None:
            raise LedgerError(f"{lid}: state {st} without a quantity")
        rec = {"host_line": lid, "host_item": h.get("item", ""), "finish": h["finish"], "floor": h.get("floor", ""),
               "item": "B4-05", "unit": "m2", "candidate_line": "NO LINE"}
        if not scope.covers(h["finish"]):
            rec.update(quantity=None, state="HELD", lo=None, hi=None,
                       held=("scope not answered" if scope.source is None
                             else f"finish {h['finish']} outside the scope {scope.source}"),
                       population=(q, lo, hi))
        else:
            rec.update(quantity=q, state=st, lo=lo, hi=hi, scope_source=scope.source,
                       held=h.get("held", ""))
        out.append(rec)
    return out


def check_no_zero_held(records):
    """a HELD record with quantity 0 (or any non-blank figure) is refused: held is never carried as 0."""
    for r in records:
        if r.get("state") == "HELD" and r.get("quantity") is not None:
            raise LedgerError(f"HELD record carried with a figure: {r}")
    return True


def spatter_totals(recs):
    t = {}
    for r in recs:
        k = (r["finish"], r["state"])
        a = t.setdefault(k, {"n": 0, "m2": 0.0, "lo": 0.0, "hi": 0.0})
        a["n"] += 1
        if r["quantity"] is not None:
            a["m2"] += r["quantity"]
        if r.get("lo") is not None:
            a["lo"] += r["lo"]
            a["hi"] += r["hi"]
    return {f"{f}|{s}": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in a.items()}
            for (f, s), a in sorted(t.items())}
