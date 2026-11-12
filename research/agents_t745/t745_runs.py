"""T-745: B12-02 DRAINAGE AND WATER SUPPLY RUNS, a census of drawn pipe runs in lm (research only, nothing wired, no
BOQ line produced).

PHYSICAL ELEMENT. A pipe run = one drawn pipe between two fittings / ends (fixture outlet, floor drain, stack, clean-out,
manhole, junction), by system and printed diameter, measured in lm along its drawn centreline. A riser (stack, rain
water pipe) is measured vertically, only between two levels the drawings print; the part beyond a printed level (the
tail below the lowest floor to a drain invert, a vent above the roof, a high-level offset drop) stays HELD.

HOW A RUN IS READ FROM A VECTOR SHEET. A sanitary sheet draws each system in its own pen (colour + width). Segments of
one pen are deduplicated (a CAD export often draws a line twice), joined where their ends meet (JOIN_TOL), and a gap is
bridged ONLY when (a) the two loose ends face each other on one straight line (both end segments within BRIDGE_ANG_DEG
of the gap) and (b) the gap carries at least one dot of the same pen (the dash-dot / dotted line style of a pipe that
passes under something). A plain gap between two pens' ends (a pipe stopping at a floor-drain body) is never bridged.
A component shorter than SYMBOL_MAX_M that touches no other run is a symbol mark (the stub of a stack circle), not a
pipe; it is listed, never counted.

SCALE. Sheet units become metres only through a scale derived from two printed dimensions measured on the same sheet
(e.g. the plot sides); the two must agree within SCALE_AGREE, otherwise the sheet is refused (a wrong-scale or
distorted plot places nothing).

NO DEFAULTS. A run whose diameter is not printed keeps its measured lm with diameter None: its line is HELD
(HELD_DIAMETER_UNPRINTED), never given a default diameter. A run whose system the pen legend does not settle is HELD
too. A riser between two levels of which one is not printed is HELD (or BOUNDED between printed neighbour levels when
the reading names them), never 0. A system the drawings do not draw at all (e.g. water supply on a drainage-only set)
is a HELD row with its cause, never 0.

LENGTH BASIS (V2, T-745 r2; the merged T-380 rule R-T380-1). A plan run has a length only where the drawings STATE it
(a printed dimension: Run.stated_m) or, on a sheet that keeps its printed scale, scaled along the drawn centreline. A
sheet whose notes disclaim its scale ('work with stated dimensions', 'not to scale', 'N.T.S.') is a SCHEMATIC: its
scaled plan length is HELD_SCHEMATIC_NOT_TO_SCALE, carried only as an information figure labelled SCALED_INFO_LABEL,
never MEASURED, never released and never summed with a measured value. A sheet whose notes box was not read gets no
basis at all (refused): the basis is read, never assumed. Risers stay on printed levels at both ends (R-T380-1).

Statuses (ENGINEERING_REASONING_STANDARD): MEASURED = drawn and printed; HELD = needed but a printed value is missing;
BOUNDED = an interval between printed values. Nothing here is VERIFIED; the Checker re-measures.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

METHOD_ID = "DRAIN_RUN_CENSUS_T745_V2"   # V1 (r1, 3e1d0514) rejected, never merged

# systems (the role of a pipe; the pen -> system map is a per-drawing reading, named in the report)
BUILDING_DRAIN = "BUILDING_DRAIN"            # external / underground collector to the manhole
SOIL_WASTE_BRANCH = "SOIL_WASTE_BRANCH"      # branch from WC / floor drain / stack foot to the collector
FIXTURE_WASTE = "FIXTURE_WASTE"              # basin / shower / tray waste to its floor drain (trap)
SOIL_STACK = "SOIL_STACK"                    # vertical soil stack
SOIL_STACK_OFFSET = "SOIL_STACK_OFFSET"      # horizontal high-level offset of a stack
RAINWATER_PIPE = "RAINWATER_PIPE"            # vertical rain water pipe
VENT = "VENT"
COLD_SUPPLY = "COLD_SUPPLY"
HOT_SUPPLY = "HOT_SUPPLY"
SYSTEMS = (BUILDING_DRAIN, SOIL_WASTE_BRANCH, FIXTURE_WASTE, SOIL_STACK, SOIL_STACK_OFFSET, RAINWATER_PIPE, VENT,
           COLD_SUPPLY, HOT_SUPPLY)

MEASURED = "MEASURED"
HELD_DIAMETER = "HELD_DIAMETER_UNPRINTED"
HELD_LEVEL = "HELD_LEVEL_UNPRINTED"
BOUNDED = "BOUNDED"
HELD_NOT_DRAWN = "HELD_NOT_DRAWN"
HELD_SCHEMATIC = "HELD_SCHEMATIC_NOT_TO_SCALE"

# sheet length basis
BASIS_SCALED = "SCALED_DRAWING"            # notes read, no scale disclaimer: the printed scale may be used
BASIS_SCHEMATIC = "SCHEMATIC_NOT_TO_SCALE"  # notes disclaim the scale: no plan length may be scaled
SCALED_INFO_LABEL = "SCALED FROM NOT-TO-SCALE SCHEMATIC, never released"
_NTS = re.compile(r"NOT\s+TO\s+SCALE|(?<![A-Z])N\.?\s?T\.?\s?S\.?(?![A-Z])|WORK\s+(?:ONLY\s+)?(?:WITH|TO)\s+STATED\s+DIMENSIONS|DO\s+NOT\s+SCALE", re.I)

JOIN_TOL = 0.6            # sheet units (pt): two segment ends this close are one point
BRIDGE_ANG_DEG = 2.0      # a bridged gap is straight on with both end segments
BRIDGE_DOT_TOL = 0.8      # a dot of the pen lies this close to the gap line
BRIDGE_MAX_M = 1.60       # a longer gap is never bridged (two separate runs)
SYMBOL_MAX_M = 0.10       # an isolated piece shorter than this is a symbol mark
SCALE_AGREE = 0.005       # two printed dimensions must give the same scale within 0.5 %


class RefusedSheet(ValueError):
    """the sheet's scale cannot be trusted; nothing is measured from it."""


# --------------------------------------------------------------------------------------------------------- scale
def scale_from_dimensions(pairs):
    """pairs = [(printed metres, measured sheet units), ...] (at least two, independent). Returns metres per sheet
    unit. Refused when any two disagree by more than SCALE_AGREE (a distorted or wrongly read sheet)."""
    if len(pairs) < 2:
        raise RefusedSheet("scale needs two printed dimensions")
    ks = []
    for m, u in pairs:
        if not (m and u) or m <= 0 or u <= 0:
            raise RefusedSheet(f"bad dimension pair {m!r} / {u!r}")
        ks.append(m / u)
    lo, hi = min(ks), max(ks)
    if (hi - lo) / lo > SCALE_AGREE:
        raise RefusedSheet(f"printed dimensions disagree: {lo:.6f} .. {hi:.6f} m per unit")
    return sum(ks) / len(ks)


def sheet_basis(notes_text):
    """the length basis of one sheet from the transcription of its notes / title-block text. None (not read) is
    refused: a basis is read from the sheet, never assumed."""
    if notes_text is None:
        raise RefusedSheet("notes box not read: the sheet's length basis is unknown")
    return BASIS_SCHEMATIC if _NTS.search(notes_text) else BASIS_SCALED


# ------------------------------------------------------------------------------------------------------ geometry
def _key(p):
    return (round(p[0], 1), round(p[1], 1))


def dedup(segments):
    """drop zero-length and repeated segments (either direction)."""
    seen, out = set(), []
    for a, b in segments:
        ka, kb = _key(a), _key(b)
        k = tuple(sorted((ka, kb)))
        if ka == kb or k in seen:
            continue
        seen.add(k)
        out.append(((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))))
    return out


def _close(p, q, tol=JOIN_TOL):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol


def _seg_point_dist(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy), t


def _angle(u, v):
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu == 0 or nv == 0:
        return 180.0
    c = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (nu * nv)))
    return math.degrees(math.acos(c))


@dataclass
class Run:
    run_id: str
    floor: str
    pen: str
    segments: list                      # [((x, y), (x, y)), ...] drawn, sheet units
    bridges: list = field(default_factory=list)   # gaps bridged, same form
    system: str | None = None
    diameter_in: float | None = None
    symbol_mark: bool = False
    stated_m: float | None = None       # a length the drawing PRINTS for this run (dimension), metres

    def length_units(self):
        return sum(math.dist(a, b) for a, b in self.segments) + sum(math.dist(a, b) for a, b in self.bridges)

    def passes_near(self, p, tol):
        return any(_seg_point_dist(p, a, b)[0] <= tol for a, b in self.segments + self.bridges)

    def touches(self, other, tol=JOIN_TOL):
        ends = [q for s in self.segments for q in s]
        oends = [q for s in other.segments for q in s]
        return (any(other.passes_near(q, tol) for q in ends) or any(self.passes_near(q, tol) for q in oends))


def _components(segs):
    n = len(segs)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(n):
        for j in range(i):
            if any(_close(p, q) for p in segs[i] for q in segs[j]):
                par[f(i)] = f(j)
    groups = {}
    for i in range(n):
        groups.setdefault(f(i), []).append(segs[i])
    return list(groups.values())


def _free_ends(comp):
    """(end point, direction pointing out of the run) for each point used by exactly one segment of the component."""
    pts = [q for s in comp for q in s]
    out = []
    for a, b in comp:
        for p, o in ((a, b), (b, a)):
            if sum(1 for q in pts if _close(p, q)) == 1:
                out.append((p, (p[0] - o[0], p[1] - o[1])))
    return out


def build_runs(segments, dots, *, floor, pen, scale, prefix=None):
    """segments: the pen's drawn segments (sheet units); dots: the pen's dot centres (dotted / dash-dot style);
    scale: metres per sheet unit. Returns the runs (components after dot-bridging), symbol marks flagged."""
    segs = dedup(segments)
    comps = _components(segs)
    bridges = []
    max_gap = BRIDGE_MAX_M / scale
    ends = [(ci, p, d) for ci, c in enumerate(comps) for p, d in _free_ends(c)]
    used = set()
    for i in range(len(ends)):
        for j in range(i + 1, len(ends)):
            ci, p, dp = ends[i]
            cj, q, dq = ends[j]
            if ci == cj or i in used or j in used:
                continue
            gap = (q[0] - p[0], q[1] - p[1])
            g = math.hypot(*gap)
            if g == 0 or g > max_gap:
                continue
            if _angle(dp, gap) > BRIDGE_ANG_DEG or _angle(dq, (-gap[0], -gap[1])) > BRIDGE_ANG_DEG:
                continue
            on = [d for d in dots if (lambda r: r[0] <= BRIDGE_DOT_TOL and 0.0 < r[1] < 1.0)(_seg_point_dist(d, p, q))]
            if not on:
                continue
            bridges.append((ci, cj, (p, q)))
            used.update((i, j))
    # merge bridged components
    par = list(range(len(comps)))

    def f(i):
        while par[i] != i:
            i = par[i]
        return i
    for ci, cj, _ in bridges:
        par[f(ci)] = f(cj)
    merged = {}
    for ci, c in enumerate(comps):
        merged.setdefault(f(ci), {"segs": [], "br": []})["segs"].extend(c)
    for ci, cj, gap in bridges:
        merged[f(ci)]["br"].append(gap)
    runs = []
    keyed = sorted(merged.values(), key=lambda m: (min(min(a[1], b[1]) for a, b in m["segs"]),
                                                   min(min(a[0], b[0]) for a, b in m["segs"])))
    for k, m in enumerate(keyed, 1):
        runs.append(Run(run_id=f"{prefix or floor + '-' + pen}{k:02d}", floor=floor, pen=pen,
                        segments=m["segs"], bridges=m["br"]))
    return runs


def flag_symbol_marks(runs, scale):
    """an isolated piece shorter than SYMBOL_MAX_M that touches no other run (of any pen) is a symbol mark."""
    for r in runs:
        if r.length_units() * scale < SYMBOL_MAX_M and not any(o is not r and r.touches(o) for o in runs):
            r.symbol_mark = True
    return runs


def label_runs(runs, labels, tol):
    """labels: [(point in sheet units, diameter_in)] read from the sheet, each placed ON the run it names. A label
    that lands on no run, or on two runs, is refused (returned)."""
    refused = []
    for p, dia in labels:
        hit = [r for r in runs if not r.symbol_mark and r.passes_near(p, tol)]
        if len(hit) != 1:
            refused.append((p, dia, len(hit)))
            continue
        hit[0].diameter_in = dia
    return refused


# -------------------------------------------------------------------------------------------------------- risers
@dataclass
class Riser:
    riser_id: str
    system: str
    diameter_in: float | None
    top_level: float | None          # printed level (m) where the riser starts, None = not printed
    bottom_level: float | None       # printed level (m) where it ends, None = not printed
    bottom_offset_m: float = 0.0     # a printed offset above the bottom level (e.g. 'free discharge 15 cm above FFL')
    bottom_bounds: tuple | None = None   # (low, high) printed neighbour levels when bottom_level is not printed
    note: str = ""

    def lm(self):
        """(status, low, high) in m. Never 0 for an unresolved riser."""
        if self.top_level is None:
            return (HELD_LEVEL, None, None)
        if self.bottom_level is not None:
            v = self.top_level - (self.bottom_level + self.bottom_offset_m)
            if v <= 0:
                raise ValueError(f"{self.riser_id}: riser top {self.top_level} not above bottom")
            return (MEASURED, round(v, 6), round(v, 6))
        if self.bottom_bounds:
            lo_lv, hi_lv = sorted(self.bottom_bounds)
            return (BOUNDED, round(self.top_level - hi_lv - self.bottom_offset_m, 6),
                    round(self.top_level - lo_lv - self.bottom_offset_m, 6))
        return (HELD_LEVEL, None, None)


# ------------------------------------------------------------------------------------------------------- summary
def run_status(r, basis=BASIS_SCALED):
    """status of one plan run. A printed (stated) length is MEASURED whatever the sheet basis; a scaled length is
    MEASURED only on a SCALED_DRAWING sheet; on a schematic it is HELD_SCHEMATIC_NOT_TO_SCALE. The diameter is then
    checked: a length with no printed diameter is HELD_DIAMETER_UNPRINTED."""
    if r.system is None:
        return "HELD_SYSTEM_UNRESOLVED"
    if r.stated_m is None and basis != BASIS_SCALED:
        if basis != BASIS_SCHEMATIC:
            raise RefusedSheet(f"unknown sheet basis {basis!r}")
        return HELD_SCHEMATIC
    return MEASURED if r.diameter_in is not None else HELD_DIAMETER


def run_record(r, scale, basis=BASIS_SCALED):
    """one plan run as a record: (run_id, floor, system, diameter_in, status, lm, scaled_info_lm, symbol_mark). lm is
    the valued length (stated, or scaled on a SCALED_DRAWING sheet) or None; scaled_info_lm is the scaled length of a
    schematic run, an information figure only."""
    k = scale[r.floor] if isinstance(scale, dict) else scale
    b = basis.get(r.floor) if isinstance(basis, dict) else basis
    scaled = r.length_units() * k
    if r.symbol_mark:
        return {"run_id": r.run_id, "floor": r.floor, "system": r.system, "diameter_in": r.diameter_in,
                "status": "SYMBOL_MARK", "lm": None, "scaled_info_lm": round(scaled, 6), "symbol_mark": True}
    st = run_status(r, b)
    if st == HELD_SCHEMATIC:
        lm, info = None, scaled
    elif r.stated_m is not None:
        lm, info = r.stated_m, None
    else:
        lm, info = scaled, None
    return {"run_id": r.run_id, "floor": r.floor, "system": r.system, "diameter_in": r.diameter_in, "status": st,
            "lm": None if lm is None else round(lm, 6), "scaled_info_lm": None if info is None else round(info, 6),
            "symbol_mark": False}


def riser_record(z):
    st, lo, hi = z.lm()
    return {"riser_id": z.riser_id, "system": z.system, "diameter_in": z.diameter_in, "status": st, "low": lo,
            "high": hi}


def table(runs, risers, scale, not_drawn=(), basis=BASIS_SCALED):
    """rows per floor x system x diameter x status: lm (horizontal, plan) and riser lm, never mixed. Symbol marks are
    listed apart. not_drawn: [(system, cause)] systems the set does not draw -> HELD_NOT_DRAWN rows. scale: metres per
    sheet unit, one number or {floor: number}; basis: one sheet basis or {floor: basis} (sheet_basis)."""
    return table_from_records([run_record(r, scale, basis) for r in runs], [riser_record(z) for z in risers],
                              not_drawn)


def table_from_records(run_recs, riser_recs, not_drawn=()):
    """the same table from run / riser records (also used to restate a committed census without its coordinates).
    A HELD_SCHEMATIC row carries lm None and its scaled figure apart, labelled SCALED_INFO_LABEL."""
    rows = {}
    marks = []
    for r in run_recs:
        if r["symbol_mark"]:
            marks.append({"run_id": r["run_id"], "floor": r["floor"], "len_m": round(r["scaled_info_lm"], 3)})
            continue
        key = (r["floor"], r["system"], r["diameter_in"], r["status"], "PLAN")
        row = rows.setdefault(key, {"floor": r["floor"], "system": r["system"], "diameter_in": r["diameter_in"],
                                    "diameter_printed": r["diameter_in"] is not None, "status": r["status"],
                                    "kind": "PLAN", "runs": 0, "lm": 0.0, "lm_high": 0.0})
        row["runs"] += 1
        if r["status"] == HELD_SCHEMATIC:
            if r["lm"] is not None:
                raise ValueError(f"{r['run_id']}: a schematic run carries a valued lm")
            row["lm"] = row["lm_high"] = None
            row["scaled_info_lm"] = row.get("scaled_info_lm", 0.0) + r["scaled_info_lm"]
            row["info_label"] = SCALED_INFO_LABEL
        else:
            if r["lm"] is None:
                raise ValueError(f"{r['run_id']}: status {r['status']} without a length")
            row["lm"] += r["lm"]
            row["lm_high"] = row["lm"]
    for z in riser_recs:
        st, lo, hi = z["status"], z["low"], z["high"]
        k = ("ALL", z["system"], z["diameter_in"], st, "RISER")
        row = rows.setdefault(k, {"floor": "ALL", "system": z["system"], "diameter_in": z["diameter_in"],
                                  "status": st, "kind": "RISER", "runs": 0, "lm": 0.0, "lm_high": 0.0,
                                  "held_ids": []})
        row["runs"] += 1
        if lo is None:
            row["lm"] = None
            row["lm_high"] = None
            row.setdefault("held_ids", []).append(z["riser_id"])
        elif row["lm"] is not None:
            row["lm"] += lo
            row["lm_high"] += hi
    for system, cause in not_drawn:
        rows[("ALL", system, None, HELD_NOT_DRAWN, "-")] = {"floor": "ALL", "system": system, "diameter_in": None,
                                                           "status": HELD_NOT_DRAWN, "kind": "-", "runs": 0,
                                                           "lm": None, "lm_high": None, "cause": cause}
    out = []
    for row in rows.values():  # noqa: B007
        if row["lm"] is not None:
            row["lm"] = round(row["lm"], 3)
            row["lm_high"] = round(row["lm_high"], 3)
        if "scaled_info_lm" in row:
            row["scaled_info_lm"] = round(row["scaled_info_lm"], 3)
        out.append(row)
    out.sort(key=lambda r: (r["kind"], r["floor"], r["system"] or "", r["diameter_in"] or 0, r["status"]))
    return out, marks


def totals_by_state(rows):
    """sums per kind x status, never across kinds (plan vs riser) and never a HELD row as 0. A schematic row's scaled
    figure is summed apart (scaled_info_lm, labelled), never into lm."""
    t = {}
    for r in rows:
        k = f"{r['kind']}|{r['status']}"
        c = t.setdefault(k, {"rows": 0, "lm": 0.0, "lm_high": 0.0, "unvalued_rows": 0})
        c["rows"] += 1
        if "scaled_info_lm" in r:
            c["scaled_info_lm"] = round(c.get("scaled_info_lm", 0.0) + r["scaled_info_lm"], 3)
            c["info_label"] = SCALED_INFO_LABEL
        if r["lm"] is None:
            c["unvalued_rows"] += 1
        else:
            c["lm"] = round(c["lm"] + r["lm"], 3)
            c["lm_high"] = round(c["lm_high"] + r["lm_high"], 3)
    for c in t.values():
        if c["unvalued_rows"] == c["rows"]:      # nothing valued: no number at all, never 0
            c["lm"] = c["lm_high"] = None
    return t


def endpoint_coverage(points, runs, tol):
    """for each fitting point (e.g. a floor-drain centre), the run ids that end at / pass within tol of it."""
    out = []
    for p in points:
        out.append([r.run_id for r in runs if not r.symbol_mark and r.passes_near(p, tol)])
    return out
