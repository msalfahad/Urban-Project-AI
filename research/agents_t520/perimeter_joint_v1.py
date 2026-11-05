"""PERIMETER_JOINT_V1 (research rule R-T520-1, every villa): the mortar joint where a mortared block wall meets
CONCRETE (an RC column face, the side of a beam drop or lintel end, and the beam / slab soffit over the last course),
measured as the INCREMENT over the panel joint mortar of R-T367-1, so the two are never double counted.

Physical element. A mortared block panel of net area A on a module (W x H) with a unit face (w x h) and joint j holds
A x b x (1 - w h / (W H)) of joint mortar when every module cell carries ONE bed joint (under its unit) and ONE head
joint (beside it): that is the R-T367-1 panel figure. Counting the joints that really exist:
  * horizontally, every course has its bed; the joint over the LAST course exists only where a soffit (beam or slab
    underside) closes the wall: the module never credits it, so a soffit of length Ls adds  kappa b j Ls;
  * vertically, a course SEGMENT (a continuous run of units in one course band between two stops) has (n - 1) joints
    between its units plus one joint at each end that touches concrete or a mortared block face. The module credits
    exactly one per segment, so per band height dz the increment is (ends with a joint - 1) dz;
with kappa = w h / (W H) (the block share of a module cell: the strip that becomes joint was 'kappa block' in the
panel figure). Proof by block count: a panel L x H between two concrete faces under a soffit holds
(L - j)(H - j) / (W H) units instead of L H / (W H): the difference x w h b is kappa b (j L + j H - j^2).
The -kappa b j^2 term is the overlap of an uncredited vertical joint strip and the soffit strip (one per such top
corner) and is applied exactly.

End classes of a segment end (the stop on each side of a course segment, per band):
  C  concrete: column outline, side of a beam drop (the member over a neighbouring piece is lower), lintel end;
  O  a block wall face met at a T / L junction: a joint exists if the junction is butt-jointed, not where it is
     bonded (toothed) in that course; the drawings print no junction detail -> RANGE [0, dz] where it decides;
  F  nothing: a free end, an opening jamb, a glazed stretch: no joint;
  U  unknown: a piece whose top is not drawn, an unresolved lintel end: HELD by name.
Per band and segment (c, o, f, u = counts of the two ends):  u > 0 -> HELD with bound;  c = 0 -> no concrete
junction here (NOT_APPLICABLE: the panel's own free-end / jamb tolerance is a different item, R-T367 / T-176 s.3);
c = 2 -> +dz exact;  c = 1 and f = 1 -> 0 exact;  c = 1 and o = 1 -> RANGE [0, dz].

Units: metres. A missing value is None and stays HELD; it never becomes 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

RULE = "R-T520-1 PERIMETER_JOINT_V1"
EPS = 1e-9
MIN_SEG = 0.005    # m: a block segment shorter than 5 mm cannot be laid (a measuring residue, e.g. a floored bearing)


class PerimeterError(ValueError):
    pass


@dataclass
class Piece:
    """a length of the wall's census run: kind BLOCK (block under a member whose underside is at `top` above the
    structural floor; None = not drawn -> HELD) or COLUMN (an RC column outline crossing the run)."""
    kind: str
    length: float
    top: float | None = None
    name: str = ""
    held: str | None = None


@dataclass
class Opening:
    """a hole in the block from the structural floor (or sill) to `head`, between stations x0 .. x1 along the run.
    Its lintel (concrete) spans head .. head + lintel_d over x0 - bearing .. x1 + bearing; a bearing is a (low, high)
    range in metres per side (the drawn minimum and the masonry available, T-516) or None (HELD)."""
    name: str
    x0: float
    x1: float
    head: float
    sill: float = 0.0
    lintel_d: float | None = None
    bearing_start: tuple | None = None
    bearing_end: tuple | None = None
    held: str | None = None


@dataclass
class Wall:
    wall_id: str
    b: float                         # wall (= unit) thickness, m
    j: float                         # joint thickness, m (owner provisional 10 mm where no drawing prints one)
    module: tuple                    # (unit face w, unit face h, module W, module H), m
    pieces: list
    end_start: str                   # 'C', 'O', 'F' or 'U' for what the run's first stop meets
    end_end: str
    openings: list = field(default_factory=list)
    status: str = ""
    held: str | None = None          # a reason the whole wall is HELD (e.g. a storey datum not printed)


def kappa(module):
    w, h, W, H = module
    if None in (w, h, W, H):
        raise PerimeterError("MODULE: unit face and module both required (HELD, never borrowed)")
    if not (0 < w < W and 0 < h < H):
        raise PerimeterError("MODULE: the unit face must be smaller than its module")
    return (w * h) / (W * H)


def _check(wall):
    if not (0.05 <= wall.b <= 0.5):
        raise PerimeterError(f"UNITS: wall thickness {wall.b} is not metres")
    if not (0.001 <= wall.j <= 0.05):
        raise PerimeterError(f"UNITS: joint {wall.j} is not metres (10 mm = 0.010)")
    for p in wall.pieces:
        if p.kind not in ("BLOCK", "COLUMN"):
            raise PerimeterError(f"PIECE: unknown kind {p.kind}")
        if p.length is None or p.length <= 0 or p.length > 100:
            raise PerimeterError(f"UNITS: piece length {p.length} is not metres")
        if p.kind == "BLOCK" and p.top is not None and not (0.5 <= p.top <= 12):
            raise PerimeterError(f"UNITS: piece top {p.top} is not metres")
        if p.kind == "BLOCK" and p.top is None and not p.held:
            raise PerimeterError("HELD: a piece without a top must name why (never 0)")
    for e in (wall.end_start, wall.end_end):
        if e not in ("C", "O", "F", "U"):
            raise PerimeterError(f"END: unknown end class {e}")


def _stations(wall):
    x, out = 0.0, []
    for p in wall.pieces:
        out.append((x, x + p.length, p))
        x += p.length
    return out, x


def _cells(wall, zm, scenario):
    """material along the run at height zm: list of (x0, x1, cls, id) with cls M (block), C (concrete), U, O (void)."""
    st, Ltot = _stations(wall)
    cells = []
    for x0, x1, p in st:
        if p.kind == "COLUMN":
            cells.append([x0, x1, "C", p.name or "column"])
        elif p.top is None:
            cells.append([x0, x1, "U", p.name])
        elif zm >= p.top:
            cells.append([x0, x1, "C", f"member over {p.name}"])
        else:
            cells.append([x0, x1, "M", p.name])
    for o in wall.openings:
        over = []
        if o.sill <= zm < o.head:
            over.append((o.x0, o.x1, "F", o.name))
        if o.lintel_d is None and o.head <= zm:
            # the lintel depth is not known: everything over the opening up to an unknown level is unknown
            over.append((o.x0, o.x1, "U", f"{o.name} lintel not established"))
        elif o.lintel_d is not None and o.head <= zm < o.head + o.lintel_d:
            if o.bearing_start is None or o.bearing_end is None:
                over.append((o.x0, o.x1, "U", f"{o.name} lintel bearing not established"))
            else:
                bs = o.bearing_start[scenario]
                be = o.bearing_end[scenario]
                over.append((o.x0 - bs, o.x1 + be, "C", f"{o.name} lintel"))
        for a, b, cls, nm in over:
            new = []
            for c in cells:
                if c[1] <= a + EPS or c[0] >= b - EPS or c[2] == "C" and cls != "C":
                    new.append(c)
                    continue
                if c[0] < a:
                    new.append([c[0], a, c[2], c[3]])
                new.append([max(c[0], a), min(c[1], b), cls, nm])
                if c[1] > b:
                    new.append([b, c[1], c[2], c[3]])
            cells = new
    cells.sort(key=lambda c: c[0])
    return cells, Ltot


def _segments(wall, zm, scenario):
    cells, Ltot = _cells(wall, zm, scenario)
    segs, i = [], 0
    while i < len(cells):
        if cells[i][2] != "M":
            i += 1
            continue
        k = i
        while k + 1 < len(cells) and cells[k + 1][2] == "M":
            k += 1
        if cells[k][1] - cells[i][0] < MIN_SEG:
            i = k + 1
            continue
        left = cells[i - 1] if i > 0 else None
        right = cells[k + 1] if k + 1 < len(cells) else None
        def cls(nb, run_end):
            if nb is None:
                return run_end, "run end"
            return {"C": "C", "U": "U", "F": "F"}.get(nb[2], "F"), nb[3]
        lc, lid = cls(left, wall.end_start)
        rc, rid = cls(right, wall.end_end)
        segs.append({"x0": cells[i][0], "x1": cells[k][1], "ends": (lc, rc), "ids": (lid, rid),
                     "tops": [c[3] for c in cells[i:k + 1]]})
        i = k + 1
    return segs


def _levels(wall):
    zs = {0.0}
    for p in wall.pieces:
        if p.kind == "BLOCK" and p.top is not None:
            zs.add(round(p.top, 9))
    for o in wall.openings:
        zs.add(round(o.head, 9))
        zs.add(round(o.sill, 9))
        if o.lintel_d is not None:
            zs.add(round(o.head + o.lintel_d, 9))
    return sorted(zs)


def _classify(ends, dz):
    c = sum(e == "C" for e in ends)
    o = sum(e == "O" for e in ends)
    f = sum(e == "F" for e in ends)
    u = sum(e == "U" for e in ends)
    if u:
        return "HELD", max(0, c - 1) * dz, max(0, c + u + o - 1) * dz
    if c == 0:
        return "NOT_APPLICABLE", 0.0, 0.0
    if c == 2:
        return "EXACT", dz, dz
    if f:
        return "EXACT", 0.0, 0.0
    return "RANGE_BLOCK_END", 0.0, dz


def vertical(wall, scenario=0):
    """per band and course segment: the vertical increment (m of joint height, low / high) and its class."""
    zs = _levels(wall)
    rows = []
    tops = [p.top for p in wall.pieces if p.kind == "BLOCK" and p.top is not None]
    zmax = max(tops) if tops else None
    for z0, z1 in zip(zs, zs[1:]):
        if zmax is None or z0 >= zmax - EPS:
            break
        zm = (z0 + z1) / 2
        for s in _segments(wall, zm, scenario):
            k, lo, hi = _classify(s["ends"], z1 - z0)
            rows.append({"z0": z0, "z1": z1, "x0": s["x0"], "x1": s["x1"], "ends": "".join(s["ends"]),
                         "end_ids": " | ".join(s["ids"]), "class": k, "low_m": lo, "high_m": hi})
    return rows


def _top_corners(wall, rows):
    """exact overlap term: every EXACT c = 2 band whose top is the soffit of the block next to its uncredited end."""
    n = 0
    st, _ = _stations(wall)
    for r in rows:
        if r["class"] != "EXACT" or r["low_m"] <= 0:
            continue
        x = r["x1"] - 1e-6
        p = next((p for a, b, p in st if a <= x < b), None)
        if p is not None and p.kind == "BLOCK" and p.top is not None and abs(p.top - r["z1"]) < 1e-9:
            n += 1
    return n


def soffit(wall):
    """block length under a drawn soffit (m) and the HELD pieces by name. Openings must stop below the soffit."""
    L, held = 0.0, []
    for p in wall.pieces:
        if p.kind != "BLOCK":
            continue
        if p.top is None:
            held.append(f"{p.name} {p.length:.4f} m: {p.held}")
        else:
            L += p.length
    for o in wall.openings:
        tops = [p.top for p in wall.pieces if p.kind == "BLOCK" and p.top is not None]
        top_lintel = o.head + (o.lintel_d or 0.0)
        if tops and top_lintel > min(tops) + EPS:
            raise PerimeterError(f"OPENING: {o.name} reaches a soffit; its length leaves the soffit joint (not "
                                 "modelled here)")
    return L, held


def measure(wall):
    """the perimeter joint increment of one wall: soffit, vertical (exact / range / held) and the totals in m3."""
    _check(wall)
    k = kappa(wall.module)
    f = k * wall.b * wall.j
    if wall.held:
        return {"wall_id": wall.wall_id, "status": "HELD", "held": wall.held, "kappa": k, "m3": None,
                "m3_low": None, "m3_high": None}
    Ls, held_soffit = soffit(wall)
    lo_rows = vertical(wall, 0)
    hi_rows = vertical(wall, 1) if any(o.bearing_start for o in wall.openings) else lo_rows
    def tot(rows, key, cls):
        return sum(r[key] for r in rows if r["class"] in cls)
    exact = tot(lo_rows, "low_m", ("EXACT",))
    exact_hi = tot(hi_rows, "low_m", ("EXACT",))
    rng_hi = tot(lo_rows, "high_m", ("RANGE_BLOCK_END",))
    held_rows = [r for r in lo_rows if r["class"] == "HELD"]
    corners = _top_corners(wall, lo_rows)
    soffit_m3 = f * Ls
    exact_m3 = f * exact - corners * f * wall.j
    out = {
        "wall_id": wall.wall_id, "kappa": k, "factor_m3_per_m": f, "soffit_m": Ls, "soffit_m3": soffit_m3,
        "vertical_exact_m": exact, "vertical_exact_m_other_bearing": exact_hi, "top_corners": corners,
        "vertical_exact_m3": exact_m3, "range_block_end_m": rng_hi, "range_block_end_m3_high": f * rng_hi,
        "held_soffit": held_soffit, "held_bands": len(held_rows),
        "held_band_high_m": sum(r["high_m"] for r in held_rows),
        "rows": lo_rows,
    }
    out["m3"] = soffit_m3 + exact_m3                     # the computed part (exact)
    out["m3_low"] = out["m3"] + f * min(0.0, exact_hi - exact)
    out["m3_high"] = out["m3"] + f * (rng_hi + max(0.0, exact_hi - exact))
    lintel_dep = abs(exact_hi - exact) > 1e-9
    if held_rows or held_soffit:
        out["status"] = "COMPUTED_WITH_HELD_PARTS"
    elif rng_hi or lintel_dep:
        out["status"] = "COMPUTED_WITH_RANGE"
    else:
        out["status"] = "COMPUTED"
    return out


def checker_bound(L_soffit, H, b, j, n_col_faces):
    """the Checker's F-T367-1 bound (L b + n H b) j: every concrete joint counted whole, no module credit."""
    return (L_soffit + n_col_faces * H) * b * j


def materials(m3, cement_bags_per_m3, sand_m3_per_m3, source):
    """cement / sand of the perimeter mortar as its OWN producer key (never inside the panel mortar)."""
    if m3 is None:
        return None
    if not source:
        raise PerimeterError("MIX: cement / sand only from a mix whose source names block laying mortar")
    return {"cement_bags": m3 * cement_bags_per_m3, "sand_m3": m3 * sand_m3_per_m3, "source": source}
