"""T-438 straight-part reading test for a multi-flight stair drawn on several plans (research module; any villa; NOT
wired into any method).

Physical element: a STRAIGHT FLIGHT (or a corner landing followed by a flight) between two finished floors. Each plan
that shows it draws its step EDGES. A drawn edge is a PAIR on the plan whose cut lies above the flight (the visible
nosing and, one nosing projection uphill, the hidden riser face); a plan whose cut lies BELOW the flight draws it as an
OVERHEAD projection, often one line per edge and often incomplete. The structural plan draws the riser faces only.

The question this module answers: when the readings differ, is it a different stair (CONFLICT, quantities HELD) or one
stair read wrongly / drawn partially (one governing reading, the other a check)? It never picks the reading that fits
the storey rise, the riser range or a dimension best.

Rules (research, proposed for the register; every villa):
  R-T438-1  LINE FAMILY. Every drawn edge is registered as (position, family) with family NOSING or FACE; a going is
            measured only between edges of ONE family. A single-line overhead edge is assigned to the family whose
            governing positions it coincides with (tolerance REG_TOL); a going between a NOSING and a FACE line is
            refused (it is going - projection, e.g. 0.300 - 0.050 = 0.250).
  R-T438-2  GOVERNING VIEW. A flight's count and positions govern from the plan whose cut lies above the whole flight
            (the flight drawn VISIBLE) when the structural plan agrees with it edge by edge (owner Q-50 A cond:
            reconstructed from the architectural + structural plans, which must agree; T-425 cause (b): 'the governing
            reading is the plan whose cut the flight lies below'). Visible and structural disagreeing -> CONFLICT, HELD.
            No visible reading -> HELD (never an overhead count).
  R-T438-3  OVERHEAD CHECK. An overhead reading whose every edge coincides with a governing edge is a PARTIAL
            PROJECTION: the governing edges it lacks are recorded (designer list, drawing-correction note), never a
            riser removed. An overhead edge with no governing edge at its position is a DIFFERENT LAYOUT -> CONFLICT,
            HELD (ERS s.6 for the designer list).
  R-T438-4  CHECKS NEVER SELECT. Riser 0.150 - 0.170 and going 0.280 - 0.300 (OWNER_RULE_STAIRS_2026-10-24 s.1),
            the run against a printed dimension and the storey rise are reported for every reading; none of them
            chooses a reading, and a reading passing them does not govern.
  R-T438-5  EFFECTS BESIDE. The quantity effect of a non-governing reading (concrete m3, tread m2, riser pieces,
            nosing lm) is stated beside the governing quantity, never exported, never chosen by fit.

Concrete basis used for the effect (the merged engine construction, T-184 / T-258, cited): a straight flight
V = plan area x (t x sec(alpha) + R / 2), tan(alpha) = R / G; a flat landing plate V = plan area x t.
Units: metres only; a value that looks like millimetres is refused. HELD is None, never 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

RISER_CHECK = (0.150, 0.170)
GOING_CHECK = (0.280, 0.300)
REG_TOL = 0.002          # two drawings of one edge coincide within 2 mm (both are CAD: 0.1 mm is typical)
NOSING, FACE = "NOSING", "FACE"
VISIBLE, OVERHEAD, STRUCTURAL = "VISIBLE", "OVERHEAD", "STRUCTURAL"

GOVERNING = "GOVERNING"
AGREES = "AGREES"
PARTIAL = "PARTIAL_PROJECTION"
CONFLICT = "CONFLICT"
HELD = "HELD"


class ReadingError(ValueError):
    pass


def _m(name, v, hi):
    if v is None:
        raise ReadingError(f"{name}: missing (never defaulted)")
    v = float(v)
    if not (0 < v <= hi):
        raise ReadingError(f"{name}={v}: not a metre value in (0, {hi}] (mm given as m?)")
    return v


@dataclass(frozen=True)
class Edge:
    s: float          # position along the walking axis of the flight, metres (any origin, same on every reading)
    family: str       # NOSING or FACE


@dataclass(frozen=True)
class Reading:
    name: str
    view: str                     # VISIBLE / OVERHEAD / STRUCTURAL
    edges: tuple                  # tuple[Edge]; for one flight in walking order or any order
    arrival_s: float | None = None  # position of the arrival edge (floor nosing) when the reading draws it


def check_reading(r: Reading) -> None:
    if r.view not in (VISIBLE, OVERHEAD, STRUCTURAL):
        raise ReadingError(f"{r.name}: unknown view {r.view}")
    if not r.edges:
        raise ReadingError(f"{r.name}: no edges")
    seen = set()
    for e in r.edges:
        if e.family not in (NOSING, FACE):
            raise ReadingError(f"{r.name}: unknown family {e.family}")
        if abs(e.s) > 100:
            raise ReadingError(f"{r.name}: position {e.s} not in metres (mm given as m?)")
        k = (round(e.s / REG_TOL), e.family)
        if k in seen:
            raise ReadingError(f"{r.name}: edge {e.s} {e.family} given twice")
        seen.add(k)


def edges_of(r: Reading, family: str, projection: float, direction: int) -> list[float]:
    """positions of the reading's edges expressed in one family (R-T438-1). A NOSING lies `projection` DOWNHILL of its
    FACE; `direction` +1 when the flight rises toward +s, -1 otherwise."""
    if projection is None or not (0 <= float(projection) <= 0.2):
        raise ReadingError(f"projection {projection}: not a metre value in [0, 0.2]")
    if direction not in (1, -1):
        raise ReadingError(f"direction {direction} must be +1 or -1")
    out = []
    for e in r.edges:
        if e.family == family:
            out.append(e.s)
        elif family == FACE:          # nosing -> face: uphill by the projection
            out.append(e.s + direction * projection)
        else:                         # face -> nosing: downhill
            out.append(e.s - direction * projection)
    return sorted(out)


def faces_of(r: Reading, projection: float, direction: int) -> list[float]:
    """one position per drawn EDGE (a nosing + face pair is one edge), in the FACE family (R-T438-1)."""
    out = []
    for s in edges_of(r, FACE, projection, direction):
        if out and abs(s - out[-1]) <= REG_TOL:
            continue
        out.append(round(s, 6))
    return out


def goings(positions: list[float]) -> list[float]:
    """goings between consecutive edges of ONE family (R-T438-1)."""
    return [round(b - a, 6) for a, b in zip(positions, positions[1:])]


def mixed_family_goings(r: Reading) -> list[tuple[float, str, str]]:
    """the adverse reading: consecutive drawn lines regardless of family (what a reader who ignores R-T438-1 gets).
    Returned so a report can show where a 'short tread' comes from; never a quantity."""
    es = sorted(r.edges, key=lambda e: e.s)
    return [(round(b.s - a.s, 6), a.family, b.family) for a, b in zip(es, es[1:])]


def register(r: Reading, gov_faces: list[float], projection: float, direction: int):
    """match every edge of r to a governing face position (R-T438-3). Returns (matched, extra, missing)."""
    mine = faces_of(r, projection, direction)
    used, matched, extra = set(), [], []
    for s in mine:
        hit = [i for i, g in enumerate(gov_faces) if abs(g - s) <= REG_TOL]
        if hit:
            used.add(hit[0])
            matched.append(s)
        else:
            extra.append(s)
    missing = [g for i, g in enumerate(gov_faces) if i not in used]
    return matched, extra, missing


def checks(n_risers: int, rise: float, going: float | None, run: float | None = None,
           printed_run: float | None = None) -> dict:
    """R-T438-4: reported, never used to select."""
    if not isinstance(n_risers, int) or n_risers <= 0:
        raise ReadingError(f"riser count {n_risers} must be a positive integer")
    rise = _m("rise", rise, 30.0)
    R = rise / n_risers
    if R > 1.0:
        raise ReadingError(f"riser {R} m: not metres")
    out = {"risers": n_risers, "riser_m": round(R, 6),
           "riser_check": "PASS" if RISER_CHECK[0] - 1e-9 <= R <= RISER_CHECK[1] + 1e-9 else "FAIL"}
    if going is not None:
        g = _m("going", going, 2.0)
        out["going_m"] = round(g, 6)
        out["going_check"] = "PASS" if GOING_CHECK[0] - 1e-9 <= g <= GOING_CHECK[1] + 1e-9 else "FAIL"
    if run is not None and printed_run is not None:
        out["run_m"] = round(run, 6)
        out["printed_run_m"] = printed_run
        out["run_check"] = "PASS" if abs(run - printed_run) <= 0.005 else "FAIL"
    return out


def governing(readings: list[Reading], projection: float, direction: int) -> dict:
    """R-T438-2 / -3. Returns the classification of every reading and the governing face positions (or HELD)."""
    for r in readings:
        check_reading(r)
    names = [r.name for r in readings]
    if len(set(names)) != len(names):
        raise ReadingError("a reading given twice")
    vis = [r for r in readings if r.view == VISIBLE]
    st = [r for r in readings if r.view == STRUCTURAL]
    table = {}
    if not vis:
        for r in readings:
            table[r.name] = {"class": HELD, "why": "no plan draws the flight below its cut (R-T438-2)"}
        return {"status": HELD, "governing": None, "faces": None, "table": table,
                "cause": "NO_VISIBLE_READING"}
    base = vis[0]
    gov = faces_of(base, projection, direction)
    conflict = []
    for r in vis[1:] + st:
        m, extra, missing = register(r, gov, projection, direction)
        if extra or missing:
            conflict.append(r.name)
            table[r.name] = {"class": CONFLICT, "extra_faces": extra, "missing_faces": missing}
        else:
            table[r.name] = {"class": AGREES, "edges": len(m)}
    if not st:
        conflict.append("(no structural reading)")
    if conflict:
        table[base.name] = {"class": CONFLICT, "edges": len(gov)}
        for r in readings:
            table.setdefault(r.name, {"class": HELD})
        return {"status": HELD, "governing": None, "faces": None, "table": table,
                "cause": "VISIBLE_AND_STRUCTURAL_DISAGREE: " + ", ".join(conflict)}
    table[base.name] = {"class": GOVERNING, "edges": len(gov)}
    status = "GOVERNED"
    for r in readings:
        if r.view != OVERHEAD:
            continue
        m, extra, missing = register(r, gov, projection, direction)
        if extra:
            table[r.name] = {"class": CONFLICT, "extra_faces": extra, "missing_faces": missing,
                             "why": "an overhead edge where the governing view has none: a different layout (R-T438-3)"}
            status = HELD
        else:
            table[r.name] = {"class": PARTIAL if missing else AGREES, "edges": len(m), "missing_faces": missing}
    if status == HELD:
        return {"status": HELD, "governing": None, "faces": None, "table": table,
                "cause": "OVERHEAD_DIFFERENT_LAYOUT"}
    return {"status": status, "governing": base.name, "agreeing": [r.name for r in st + vis[1:]],
            "faces": gov, "risers": len(gov), "table": table}


def choose_by_fit(*_a, **_k):
    """The adverse construction named by the task ('riser count taken from the plan that fits the storey rise best
    without a governing reason'): always refused."""
    raise ReadingError("a riser count is never chosen by fit to the storey rise, a range or a dimension (R-T438-4)")


# ---- quantity effect (R-T438-5) --------------------------------------------------------------------------------

def flight_m3(area: float, t: float, R: float, G: float) -> float:
    area, t, R, G = _m("area", area, 1000), _m("t", t, 1.0), _m("R", R, 1.0), _m("G", G, 2.0)
    return area * (t * math.sqrt(1 + (R / G) ** 2) + R / 2)


def plate_m3(area: float, t: float) -> float:
    return _m("area", area, 1000) * _m("t", t, 1.0)


def steps_m3(area: float, R: float) -> float:
    """steps only (triangular prisms on the plan area), as the RS-C curved part (T-415: waist HELD)."""
    return 0.5 * _m("R", R, 1.0) * _m("area", area, 1000)
