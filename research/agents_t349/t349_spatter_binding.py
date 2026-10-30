"""T-349 rules: binding a spatter-dash (B4-05) population to the candidate's finish lines, one face once (every villa).

Physical element (ERS s.2.1): spatter dash is the cement-slurry bond coat thrown on a wall face BEFORE the coat that
finishes it. It is a separate item on the same geometric population as that finish (owner method record: OD-V3B-4 .. 7,
URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1), whatever the substrate (block or concrete). So a spatter row is never measured
on its own: it is the face population of ONE host, the coat that lies directly on it.

R-T349-1 ONE FACE, ONE CARRIER. Every spatter row names exactly one target: a candidate line id (interior: the
         plaster line of the face; a tiled face: its tile-preparation / backing line) or one exterior face key of the
         merged facade binding. A face id bound twice (twice to one line, or to two lines) is refused. Many faces may
         share one line; one face may never sit under two.
R-T349-2 THE LAYER DIRECTLY ABOVE. Where a tiled face has a tile-preparation line in the candidate, the spatter is
         bound to that line (the coat it lies under) and the tile line is named only as `via`; a tiled face bound to
         its tile line while a backing line carries the same face is refused (one face under two carriers).
R-T349-3 SCOPE FROM THE METHOD RECORD. The finishes that take spatter are those of the project's answered method
         record (a Scope): a row whose finish is outside it is refused (e.g. a villa whose rule puts no spatter under
         tile). With no answered record the item is HELD by name (no quantity).
R-T349-4 STATES. Evidence status per row (WORKFLOW_CONTROLS s.5). A determinate row has a figure; a HELD row has no
         figure (a bound [lo, hi] or BLANK); UNKNOWN has no number; HELD / UNKNOWN never become 0 and are never
         summed into a determinate total.
R-T349-5 EQUAL TO THE HOST. A line-level row equals its host line's figure / range exactly; face-level rows of one
         host close on the host's figure (sum within 0.0005 m2, the 4-dp rounding) or the build stops.
R-T349-6 SUBSTRATE IS INFORMATION. The concrete / block split of a face is reported beside the row and closes on the
         face (concrete + block = face); a split known only for the whole wall side is never pro-rated to a part of it
         (HELD by name).
         A contour closure term of a face ledger (family *_RESIDUAL, e.g. a room's walk-class residual) is signed
         and is the only row that may be negative; it is part of its host's figure, never a face of its own.
R-T349-7 UNITS. Lengths and heights are metres; a height outside 0.05 .. 10 m or a length outside 0.001 .. 200 m is
         refused (mm read as m).
"""

from __future__ import annotations

from dataclasses import dataclass, field

TOL = 0.0005
DET = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "VERIFIED")
NONDET = ("HELD", "UNKNOWN")


class BindError(ValueError):
    pass


@dataclass(frozen=True)
class Scope:
    item: str
    source: str | None                      # answered method record; None = not answered -> HELD by name
    finishes: frozenset = field(default_factory=frozenset)


@dataclass
class Row:
    row_id: str
    family: str                             # INT_DRY_LINE / INT_WET_FACE / EXT_FACE / EXT_ITEM
    face_id: str                            # physical face (or the line itself for a line-level host)
    finish: str                             # PLASTER / TILE / SIGMA / CLADDING / ...
    target: str                             # candidate line id or exterior face key
    carrier_line: str                       # the line the target belongs to (= target for interior)
    state: str
    m2: float | None = None
    lo: float | None = None
    hi: float | None = None
    held: str = ""
    via: str = ""


def check_state(r: Row):
    if r.state in DET:
        if r.m2 is None or r.lo is not None or r.hi is not None:
            raise BindError(f"{r.row_id}: determinate row needs a figure and no range")
        if r.m2 < -TOL and not r.family.endswith("_RESIDUAL"):
            raise BindError(f"{r.row_id}: negative area {r.m2}")
    elif r.state == "HELD":
        if r.m2 is not None:
            raise BindError(f"{r.row_id}: HELD row carries a figure {r.m2} (a held quantity is never a point value)")
        if (r.lo is None) != (r.hi is None):
            raise BindError(f"{r.row_id}: half a range")
        if r.lo is not None and r.lo > r.hi + TOL:
            raise BindError(f"{r.row_id}: range {r.lo} > {r.hi}")
        if not r.held:
            raise BindError(f"{r.row_id}: HELD without its reason")
    elif r.state == "UNKNOWN":
        if r.m2 is not None or r.lo is not None or r.hi is not None:
            raise BindError(f"{r.row_id}: UNKNOWN carries a number")
        if not r.held:
            raise BindError(f"{r.row_id}: UNKNOWN without its reason")
    else:
        raise BindError(f"{r.row_id}: state {r.state!r}")


def held_as_zero(r: Row):
    return r.state in NONDET and (r.m2 == 0 or (r.lo == 0 and r.hi == 0))


def bind(rows, scope: Scope, backing_of_tile: dict | None = None):
    """validate a binding (R-T349-1 .. 4); returns the rows unchanged. backing_of_tile: {tile line id: backing line id}
    of the candidate (a tiled face must sit under the backing, R-T349-2)."""
    if scope.source is None:
        raise BindError(f"{scope.item}: no answered method record: the item is HELD by name, no binding")
    backing_of_tile = backing_of_tile or {}
    seen = {}
    for r in rows:
        check_state(r)
        if held_as_zero(r):
            raise BindError(f"{r.row_id}: a HELD / UNKNOWN row written as 0")
        if r.finish not in scope.finishes:
            raise BindError(f"{r.row_id}: finish {r.finish} takes no {scope.item} under {scope.source}")
        if not r.target:
            raise BindError(f"{r.row_id}: no target")
        if r.face_id in seen:
            raise BindError(f"face {r.face_id} bound twice ({seen[r.face_id]} and {r.target}): one face, one carrier")
        seen[r.face_id] = r.target
        if r.finish == "TILE" and r.target in backing_of_tile:
            raise BindError(f"{r.row_id}: tiled face bound to its tile line {r.target} while the backing line "
                            f"{backing_of_tile[r.target]} carries it (R-T349-2)")
    return rows


def close_on_host(rows, host_line: str, host_m2: float | None, host_lo=None, host_hi=None):
    """R-T349-5: the rows bound to one host close on it."""
    mine = [r for r in rows if r.carrier_line == host_line]
    if not mine:
        raise BindError(f"{host_line}: no row")
    if host_m2 is not None:
        if any(r.state not in DET for r in mine):
            raise BindError(f"{host_line}: determinate host with a held row")
        s = sum(r.m2 for r in mine)
        if abs(s - host_m2) > TOL:
            raise BindError(f"{host_line}: rows {s:.6f} != host {host_m2:.6f}")
        return s, None, None
    if host_lo is not None:
        lo = sum((r.m2 if r.m2 is not None else r.lo) for r in mine)
        hi = sum((r.m2 if r.m2 is not None else r.hi) for r in mine)
        if abs(lo - host_lo) > TOL or abs(hi - host_hi) > TOL:
            raise BindError(f"{host_line}: rows {lo:.6f} .. {hi:.6f} != host {host_lo} .. {host_hi}")
        return None, lo, hi
    if any(r.m2 is not None or r.lo is not None for r in mine):
        raise BindError(f"{host_line}: blank host with a valued row")
    return None, None, None


def face_area(length, height, openings=(), units="m"):
    """gross length x height less fixed openings (m2); mm read as m refused (R-T349-7)."""
    k = {"m": 1.0, "mm": 0.001}[units]
    L, H = length * k, height * k
    if not (0.001 <= L <= 200.0):
        raise BindError(f"length {L} m outside 0.001 .. 200 m (units?)")
    if not (0.05 <= H <= 10.0):
        raise BindError(f"height {H} m outside 0.05 .. 10 m (units?)")
    net = L * H - sum(o * k * k for o in openings)
    if net < -TOL:
        raise BindError(f"openings exceed the face ({net})")
    return round(net, 6)


def substrate(face_m2, concrete_m2, block_m2, whole_side: bool):
    """R-T349-6: the split of one face, or HELD when the split is known only for the whole wall side."""
    if face_m2 is None or concrete_m2 is None or block_m2 is None:
        return {"state": "HELD", "why": "wall side split not established"}
    if abs(concrete_m2 + block_m2 - face_m2) > 1e-6:
        raise BindError(f"split {concrete_m2} + {block_m2} != face {face_m2}")
    if not whole_side:
        return {"state": "HELD", "why": "face is a part of the wall side: no station crosswalk, never pro-rated"}
    return {"state": "ESTABLISHED", "concrete_m2": concrete_m2, "block_m2": block_m2,
            "concrete_share": round(concrete_m2 / face_m2, 6) if face_m2 else None}


def totals(rows):
    """per evidence status: determinate m2, HELD lo / hi, HELD blank count, UNKNOWN count (never summed together)."""
    out = {}
    for r in rows:
        k = r.state
        a = out.setdefault(k, {"n": 0, "m2": 0.0, "lo": 0.0, "hi": 0.0, "blank": 0})
        a["n"] += 1
        if r.m2 is not None:
            a["m2"] += r.m2
        elif r.lo is not None:
            a["lo"] += r.lo
            a["hi"] += r.hi
        else:
            a["blank"] += 1
    return {k: {x: (round(y, 6) if isinstance(y, float) else y) for x, y in v.items()} for k, v in sorted(out.items())}
