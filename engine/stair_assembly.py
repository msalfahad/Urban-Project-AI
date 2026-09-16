"""A stair is not a room-floor polygon, and its treads are not tiles.

Round 6C found a stair tread carrying 1.2 m2 of "floor" and refused to
release it. Refusing is not measuring. On P7757 the stair finish is
MARBLE while the floor around it is PORCELAIN — **a project rule, not a
universal one** — and marble is bought by the piece:

    TREAD_M2     every tread, measured from its own polygon
    RISER_M2     every riser, width by height
    LANDING_M2   the landing polygon
    NOSING_LM    the exposed front edges
    SKIRTING_LM  separately again, where the drawing establishes it

Four numbers and a fifth, and none of them is added to another: square
metres and linear metres are different quantities and a stair that
reports one number has already lost the argument.

WHAT A STAIR LOOKS LIKE IN PLAN

A run of parallel lines at a near-constant pitch, spanning a common
interval, inside one enclosure. That is a stair — and it is also a
louvre, a grating and a run of shelving, so this module says STAIR only
where the drawing gives it a stair's own evidence, and NOT_ESTABLISHED
otherwise. Decorative parallel lines are refused.

WHAT A PLAN CANNOT SAY

A plan does not carry a riser height. Without section evidence the riser
quantity is `RISER_QUANTITY_NOT_ESTABLISHED` — never a default, never a
standard rise, never treads-minus-one arithmetic dressed up as geometry.
The same for a tread nobody drew: `TREAD_QUANTITY_NOT_ESTABLISHED`.

    DO NOT ASSUME treads = risers, OR treads = risers - 1

CURVED AND WINDER STAIRS

Every tread is measured from ITS OWN polygon. No constant width times a
constant going times a count: a winder's treads are wedges of different
sizes and the marble is cut to each of them.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import space_enclosure as enc

MODEL = "STAIR_ASSEMBLY_TREADS_RISERS_LANDINGS_V1"

# --- what a stair is made of --------------------------------------------
STAIR_ASSEMBLY = "STAIR_ASSEMBLY"
STAIR_FLIGHT = "STAIR_FLIGHT"
STAIR_TREAD = "STAIR_TREAD"
STAIR_RISER = "STAIR_RISER"
STAIR_LANDING = "STAIR_LANDING"
PARTS = (STAIR_ASSEMBLY, STAIR_FLIGHT, STAIR_TREAD, STAIR_RISER,
         STAIR_LANDING)

# --- how it runs ---------------------------------------------------------
STRAIGHT = "STRAIGHT"
L_SHAPED = "L_SHAPED"
U_SHAPED = "U_SHAPED"
WINDER = "WINDER"
CURVED = "CURVED"
SPIRAL = "SPIRAL"
CONFIGURATION_NOT_ESTABLISHED = "STAIR_CONFIGURATION_NOT_ESTABLISHED"

# --- what a plan cannot answer -------------------------------------------
RISER_NOT_ESTABLISHED = "RISER_QUANTITY_NOT_ESTABLISHED"
TREAD_NOT_ESTABLISHED = "TREAD_QUANTITY_NOT_ESTABLISHED"
FLIGHTS_OVERLAP = "FLIGHTS_OF_ONE_STAIR_OVERLAP_EACH_OTHER"
LANDING_NOT_ESTABLISHED = "LANDING_QUANTITY_NOT_ESTABLISHED"
SKIRTING_NOT_ESTABLISHED = "STAIR_SKIRTING_NOT_ESTABLISHED"
FLOOR_TO_FLOOR_NOT_ESTABLISHED = "FLOOR_TO_FLOOR_HEIGHT_NOT_ESTABLISHED"
PLAN_AND_SECTION_DISAGREE = "PLAN_AND_SECTION_DISAGREE"
NOT_A_STAIR = "PARALLEL_LINES_WITH_NO_STAIR_EVIDENCE"

# --- the evidence a run of lines has to have -----------------------------
EV_CONSTANT_PITCH = "PARALLEL_LINES_AT_A_CONSTANT_PITCH"
EV_SPAN_TOGETHER = "THEY_SPAN_THE_SAME_INTERVAL"
EV_INSIDE_ONE_CELL = "THEY_LIE_INSIDE_ONE_ENCLOSED_CELL"
EV_STAIR_LABEL = "A_STAIR_LABEL_STANDS_IN_THAT_CELL"
EV_GOING_IS_A_STAIR_GOING = "THE_PITCH_IS_A_TREAD_GOING"
EVIDENCE = (EV_CONSTANT_PITCH, EV_SPAN_TOGETHER, EV_INSIDE_ONE_CELL,
            EV_STAIR_LABEL, EV_GOING_IS_A_STAIR_GOING)

# A stair has at least this many treads drawn before a run of lines is a
# flight rather than two lines that happen to be parallel.
MIN_TREADS = 3

# A tread's going, in millimetres. NOT a rule about what a going should
# be — a bound on what a drawn pitch may be and still be read as one.
# Below the first figure the lines are hatching; above the second they
# are not treads of a stair anybody walks up.
MIN_GOING_MM = 150.0
MAX_GOING_MM = 450.0

# Two pitches are the same pitch within this. The enclosure's own join.
SAME_PITCH_MM = enc.COLLINEAR_JOIN_MM * 10.0

# A cell inside the footprint deeper than the largest going is a landing
# rather than a tread.
LANDING_MIN_MM = MAX_GOING_MM

# A stair is at least this wide, or it is a ladder in a shaft. The
# project's own thinnest wall, doubled: nothing new is chosen.
MIN_WIDTH_MM = cprofile.MIN_WALL_THICKNESS_MM * 2.0

# A STAIR FILLS ITS CELL. A run of hatching in the corner of a room is
# parallel, pitched and inside an enclosure too — and it covers a few
# per cent of it. A share, never an area: the cell decides the scale.
STAIR_CELL_SHARE = 0.25
NOT_ENOUGH_OF_THE_CELL = "THE_RUN_COVERS_TOO_LITTLE_OF_THE_CELL_IT_IS_IN"


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "PARTS": list(PARTS),
        "MIN_TREADS": MIN_TREADS,
        "MIN_GOING_MM": MIN_GOING_MM,
        "MAX_GOING_MM": MAX_GOING_MM,
        "SAME_PITCH_MM": SAME_PITCH_MM,
        "LANDING_MIN_MM": LANDING_MIN_MM,
        "MIN_WIDTH_MM": MIN_WIDTH_MM,
        "STAIR_CELL_SHARE": STAIR_CELL_SHARE,
        "why": {
            "a_stair_fills_its_cell": (
                "a run of hatching is parallel, pitched and inside an "
                "enclosure as well. What a stair also does is take up "
                "its cell, and a share says so at any scale"),
            "a_riser_needs_a_section": (
                "a plan carries no height. Without section evidence the "
                "riser quantity is NOT ESTABLISHED, and no standard rise "
                "is borrowed from anywhere"),
            "counts_are_not_arithmetic": (
                "treads = risers and treads = risers - 1 are both true of "
                "some stairs and neither is derived here. Each is counted "
                "from what is drawn"),
            "each_tread_from_its_own_polygon": (
                "a winder's treads are wedges of different sizes. A "
                "constant width times a constant going times a count is "
                "the wrong quantity for every one of them"),
            "m2_and_lm_are_not_added": (
                "TREAD_M2, RISER_M2 and LANDING_M2 are areas; NOSING_LM "
                "and SKIRTING_LM are lengths. They are reported apart"),
            "no_waste_here": (
                "this is the MEASURED NET quantity. A waste factor and a "
                "procurement quantity are separate numbers, applied "
                "later, by an owner-approved rule"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(PARTS) + list(EVIDENCE)
             + [STRAIGHT, L_SHAPED, U_SHAPED, WINDER, CURVED, SPIRAL,
                CONFIGURATION_NOT_ESTABLISHED, RISER_NOT_ESTABLISHED,
                TREAD_NOT_ESTABLISHED, LANDING_NOT_ESTABLISHED,
                SKIRTING_NOT_ESTABLISHED, PLAN_AND_SECTION_DISAGREE,
                NOT_A_STAIR]
             + [str(v) for v in (MIN_TREADS, MIN_GOING_MM, MAX_GOING_MM,
                                 SAME_PITCH_MM, LANDING_MIN_MM,
                                 MIN_WIDTH_MM, STAIR_CELL_SHARE)]
             + [NOT_ENOUGH_OF_THE_CELL, FLIGHTS_OVERLAP])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the objects

@dataclass
class Tread:
    """One tread, measured from its own polygon."""

    tread_id: str = ""
    index: int = 0
    polygon_wkt: str = ""
    area_m2: float = 0.0
    going_mm: float = 0.0          # front edge to back edge
    width_mm: float = 0.0          # the walking width
    nosing_length_mm: float = 0.0  # the exposed front edge
    front_edge_wkt: str = ""
    back_edge_wkt: str = ""
    inner_edge_wkt: str = ""
    outer_edge_wkt: str = ""
    rectangular: bool = True
    cad_provenance: tuple = ()
    status: str = "TREAD_MEASURED"

    def record(self) -> dict:
        return {
            "tread_id": self.tread_id,
            "index": self.index,
            "tread_area_m2": round(self.area_m2, 4),
            "going_mm": round(self.going_mm, 1),
            "width_mm": round(self.width_mm, 1),
            "nosing_length_mm": round(self.nosing_length_mm, 1),
            "rectangular": self.rectangular,
            "front_edge_wkt": self.front_edge_wkt,
            "back_edge_wkt": self.back_edge_wkt,
            "inner_edge_wkt": self.inner_edge_wkt,
            "outer_edge_wkt": self.outer_edge_wkt,
            "polygon_wkt_mm": self.polygon_wkt,
            "cad_provenance": list(self.cad_provenance),
            "status": self.status,
        }


@dataclass
class Riser:
    """One riser. Its face area needs a height a plan does not carry."""

    riser_id: str = ""
    index: int = 0
    width_mm: float = 0.0
    height_mm: float | None = None
    area_m2: float | None = None
    height_source: str = RISER_NOT_ESTABLISHED
    edge_wkt: str = ""
    status: str = RISER_NOT_ESTABLISHED

    def record(self) -> dict:
        return {
            "riser_id": self.riser_id,
            "index": self.index,
            "riser_width_mm": round(self.width_mm, 1),
            "riser_height_mm": (None if self.height_mm is None
                                else round(self.height_mm, 1)),
            "riser_face_area_m2": (None if self.area_m2 is None
                                   else round(self.area_m2, 4)),
            "height_source": self.height_source,
            "edge_wkt": self.edge_wkt,
            "status": self.status,
        }


@dataclass
class Landing:
    landing_id: str = ""
    polygon_wkt: str = ""
    area_m2: float = 0.0
    length_mm: float = 0.0
    width_mm: float = 0.0
    status: str = "LANDING_MEASURED"

    def record(self) -> dict:
        return {
            "landing_id": self.landing_id,
            "landing_area_m2": round(self.area_m2, 4),
            "landing_length_mm": round(self.length_mm, 1),
            "landing_width_mm": round(self.width_mm, 1),
            "polygon_wkt_mm": self.polygon_wkt,
            "status": self.status,
        }


@dataclass
class Flight:
    flight_id: str = ""
    axis: str = ""                 # the axis the treads are drawn on
    direction_mm: tuple = ()       # the interval the flight climbs over
    width_mm: float = 0.0
    treads: list = field(default_factory=list)
    risers: list = field(default_factory=list)
    configuration: str = CONFIGURATION_NOT_ESTABLISHED
    evidence: tuple = ()

    @property
    def tread_area_m2(self) -> float:
        return sum(t.area_m2 for t in self.treads)

    @property
    def nosing_lm(self) -> float:
        return sum(t.nosing_length_mm for t in self.treads) / 1000.0

    def record(self) -> dict:
        return {
            "flight_id": self.flight_id,
            "axis": self.axis,
            "climbs_over_mm": [round(v, 1) for v in self.direction_mm],
            "stair_width_m": round(self.width_mm / 1000.0, 3),
            "number_of_treads": len(self.treads),
            "number_of_risers": len(self.risers),
            "TREAD_M2": round(self.tread_area_m2, 4),
            # NO RISERS IS NOT ZERO RISERS. An empty sum reads as a
            # measured nothing, and nothing here has been measured.
            "RISER_M2": (None if not self.risers
                         or any(r.area_m2 is None for r in self.risers)
                         else round(sum(r.area_m2 or 0.0
                                        for r in self.risers), 4)),
            "NOSING_LM": round(self.nosing_lm, 3),
            "configuration": self.configuration,
            "evidence": list(self.evidence),
            "treads": [t.record() for t in self.treads],
            "risers": [r.record() for r in self.risers],
            "counts_are_not_derived_from_each_other": (
                "treads and risers are each counted from what is drawn. "
                "Neither is the other plus or minus one here"),
        }


@dataclass
class Assembly:
    stair_id: str = ""
    region_id: str = ""
    floor_from: str = ""
    floor_to: str = ""
    space_id: str = ""
    footprint_wkt: str = ""
    footprint_area_m2: float = 0.0
    containing_space_area_m2: float | None = None
    flights: list = field(default_factory=list)
    landings: list = field(default_factory=list)
    configuration: str = CONFIGURATION_NOT_ESTABLISHED
    finish_rule: str = ""
    skirting_lm: float | None = None
    skirting_status: str = SKIRTING_NOT_ESTABLISHED
    exceptions: tuple = ()
    evidence: tuple = ()

    @property
    def tread_m2(self) -> float:
        return sum(f.tread_area_m2 for f in self.flights)

    @property
    def landing_m2(self) -> float:
        return sum(x.area_m2 for x in self.landings)

    @property
    def nosing_lm(self) -> float:
        return sum(f.nosing_lm for f in self.flights)

    @property
    def riser_m2(self):
        vals = [r.area_m2 for f in self.flights for r in f.risers]
        if not vals or any(v is None for v in vals):
            return None          # not established is not zero
        return sum(vals)

    def record(self) -> dict:
        return {
            "stair_id": self.stair_id,
            "drawing_region_id": self.region_id,
            "floor_from": self.floor_from or FLOOR_TO_FLOOR_NOT_ESTABLISHED,
            "floor_to": self.floor_to or FLOOR_TO_FLOOR_NOT_ESTABLISHED,
            "physical_space_id": self.space_id,
            "configuration": self.configuration,
            "flight_count": len(self.flights),
            "footprint_area_m2": round(self.footprint_area_m2, 4),
            "containing_space_area_m2": (
                None if self.containing_space_area_m2 is None
                else round(self.containing_space_area_m2, 4)),
            "footprint_wkt_mm": self.footprint_wkt,
            "MEASURED_NET": {
                # A stair whose flights overlap cannot have both their
                # treads, and neither can be chosen: the quantity is NOT
                # ESTABLISHED rather than the larger of two readings.
                "TREAD_M2": (None if TREAD_NOT_ESTABLISHED
                             in self.exceptions
                             else round(self.tread_m2, 4)),
                "RISER_M2": (None if self.riser_m2 is None
                             else round(self.riser_m2, 4)),
                "LANDING_M2": round(self.landing_m2, 4),
                "NOSING_LM": round(self.nosing_lm, 3),
                "STAIR_SKIRTING_LM": self.skirting_lm,
                "this_is": ("the measured net quantity. No waste factor "
                            "and no procurement quantity are applied "
                            "here, and no price exists"),
            },
            "skirting_status": self.skirting_status,
            "finish_rule": self.finish_rule or "NO_PROJECT_FINISH_RULE",
            "flights": [f.record() for f in self.flights],
            "landings": [x.record() for x in self.landings],
            "exceptions": list(self.exceptions),
            "evidence": list(self.evidence),
            "floor_finish_owner": (
                "this footprint belongs to the stair. Its area may not "
                "appear again in any floor-finish quantity"),
        }


@dataclass
class StairReport:
    region_id: str = ""
    assemblies: list = field(default_factory=list)
    refused: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        return {
            "stair_assemblies": len(self.assemblies),
            "flights": sum(len(a.flights) for a in self.assemblies),
            "treads": sum(len(f.treads) for a in self.assemblies
                          for f in a.flights),
            "risers": sum(len(f.risers) for a in self.assemblies
                          for f in a.flights),
            "landings": sum(len(a.landings) for a in self.assemblies),
            "runs_refused": len(self.refused),
            "riser_quantity_established": sum(
                1 for a in self.assemblies if a.riser_m2 is not None),
        }

    def record(self) -> dict:
        return {
            "model": MODEL,
            "STAIR_ASSEMBLY_HASH": model_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "assemblies": [a.record() for a in self.assemblies],
            "refused": list(self.refused),
            "notes": dict(self.notes),
        }


# ------------------------------------------------------------ the detector

def _runs(lines, axis: str) -> list:
    """Parallel drawn lines on one axis, grouped into pitched runs.

    A run is three or more lines, each a tread's going from the last and
    overlapping it along its length. SEVERAL RUNS MAY BE OPEN AT ONCE:
    two flights side by side share their tread positions, and a walk
    that can only follow one of them finds neither.

    A CONSTANT pitch is not required — a winder's goings differ from
    tread to tread, and requiring one would cut every winder into pieces
    and then measure none of them. Constant pitch is recorded as
    evidence where it is true.

    This is also what a louvre, a grating and a run of shelving look
    like, which is why the caller still has to find stair evidence
    around the run.
    """
    rows = []
    for c in lines:
        if getattr(c, "axis", "") != axis:
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        rows.append((c.fixed_mm, lo, hi, c))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    # TWO LINES LESS THAN A GOING APART ARE ONE STEP'S EDGE. A stair is
    # often drawn with a nosing line just in front of each riser line,
    # and read as two tracks it becomes two overlapping flights that
    # measure the same marble twice.
    merged = []
    for row in rows:
        if merged and row[0] - merged[-1][0] < MIN_GOING_MM \
                and min(merged[-1][2], row[2]) \
                - max(merged[-1][1], row[1]) > MIN_WIDTH_MM:
            prev = merged[-1]
            merged[-1] = (prev[0], min(prev[1], row[1]),
                          max(prev[2], row[2]), prev[3])
            continue
        merged.append(row)
    rows = merged
    open_runs: list = []
    done: list = []
    for row in rows:
        best, best_gap = None, None
        for run in open_runs:
            last = run[-1]
            gap = row[0] - last[0]
            span = min(last[2], row[2]) - max(last[1], row[1])
            if MIN_GOING_MM <= gap <= MAX_GOING_MM and span > MIN_WIDTH_MM:
                if best is None or gap < best_gap:
                    best, best_gap = run, gap
        if best is not None:
            best.append(row)
            continue
        open_runs.append([row])
    for run in open_runs:
        done.extend(_cut(run))
    return done


def _cut(run) -> list:
    """Split a walk where the lines stop being treads of one flight.

    A flight's treads reach nearly as far as each other — a winder's
    shrink from one end to the other, but gradually. A room's own wall
    runs the width of the ROOM and happens to sit a going away from the
    first tread, so it joins the walk; and it gives itself away by
    reaching past its neighbour by more than a tread's going, which is
    the module's own figure and not a new one.
    """
    out, cur = [], []
    for row in run:
        if cur and abs((row[2] - row[1]) - (cur[-1][2] - cur[-1][1])) \
                > MAX_GOING_MM:
            out.append(cur)
            cur = [row]
            continue
        cur.append(row)
    out.append(cur)
    return [r for r in out if len(r) >= MIN_TREADS]


def _polygon(axis: str, f0: float, f1: float, lo: float, hi: float):
    from shapely.geometry import box

    if axis == "H":
        return box(lo, f0, hi, f1)
    return box(f0, lo, f1, hi)


def _edge(axis: str, fixed: float, lo: float, hi: float) -> str:
    from shapely.geometry import LineString

    pts = ([(lo, fixed), (hi, fixed)] if axis == "H"
           else [(fixed, lo), (fixed, hi)])
    return LineString(pts).wkt


def assess(lines, *, region_id: str = "DR-001", spaces=(), labels=(),
           floor_from: str = "", floor_to: str = "", sections=None,
           finish_rule: str = "", skirting_rule=None) -> StairReport:
    """Find the stairs in one region and measure what is drawn.

    `spaces` are the region's measured spaces (each with a polygon and an
    identity), `labels` their authored text. `sections` is optional
    section evidence: {stair or region key: {"riser_height_mm": ...,
    "risers": ..., "treads": ...}} — a plan alone never produces a riser
    height, and nothing here invents one.

    Runs that stand in the SAME cell are flights of ONE stair: two
    flights and a landing are one staircase, not two staircases.
    """
    from shapely.wkt import loads

    rep = StairReport(region_id=region_id)
    poly_of = {}
    for sp in spaces or ():
        wkt = getattr(sp, "polygon_wkt", "") or ""
        if not wkt:
            continue
        try:
            poly_of[getattr(sp, "space_id", "")] = loads(wkt)
        except Exception:      # noqa: BLE001
            continue
    stair_points = [(getattr(o, "x", 0.0), getattr(o, "y", 0.0))
                    for o in (labels or ())
                    if "STAIR" in (getattr(o, "text", "") or "").upper()]

    # ---- every run, with the cell it stands in ------------------------
    found = []
    n = 0
    for axis in ("H", "V"):
        for run in _runs(lines, axis):
            n += 1
            goings = [run[i + 1][0] - run[i][0] for i in range(len(run) - 1)]
            ev = [EV_SPAN_TOGETHER]
            if goings and max(goings) - min(goings) <= SAME_PITCH_MM:
                ev.append(EV_CONSTANT_PITCH)
            if goings and all(MIN_GOING_MM <= g <= MAX_GOING_MM
                              for g in goings):
                ev.append(EV_GOING_IS_A_STAIR_GOING)
            f_lo, f_hi = run[0][0], run[-1][0]
            lo = min(r[1] for r in run)
            hi = max(r[2] for r in run)
            foot = _polygon(axis, f_lo, f_hi, lo, hi)
            space_id, cell = "", None
            for sid, g in sorted(poly_of.items()):
                try:
                    if g.intersection(foot).area > foot.area * 0.5:
                        space_id, cell = sid, g
                        break
                except Exception:      # noqa: BLE001
                    continue
            if cell is not None:
                ev.append(EV_INSIDE_ONE_CELL)
            labelled = any(foot.contains(_pt(x, y)) for x, y in stair_points)
            if labelled:
                ev.append(EV_STAIR_LABEL)
            if cell is None and not labelled:
                rep.refused.append({
                    "run_id": f"RUN-{region_id}-{n:03d}",
                    "axis": axis, "lines": len(run),
                    "pitch_mm": round(goings[0], 1) if goings else None,
                    "why": NOT_A_STAIR,
                    "what_would_settle_it": (
                        "an enclosure around it, or a stair label in it")})
                continue
            found.append({"axis": axis, "run": run, "foot": foot,
                          "space_id": space_id, "cell": cell,
                          "ev": ev, "n": n})

    # ---- runs in one cell are flights of one stair --------------------
    groups: dict = {}
    for item in found:
        groups.setdefault(item["space_id"] or f"RUN-{item['n']}",
                          []).append(item)

    for k, (key, items) in enumerate(sorted(groups.items()), 1):
        cell = next((it["cell"] for it in items if it["cell"] is not None),
                    None)
        foot = items[0]["foot"]
        for it in items[1:]:
            foot = foot.union(it["foot"])
        labelled = any(EV_STAIR_LABEL in it["ev"] for it in items)
        if cell is not None and not labelled and \
                foot.area < cell.area * STAIR_CELL_SHARE:
            rep.refused.append({
                "run_id": f"RUN-{region_id}-{items[0]['n']:03d}",
                "axis": items[0]["axis"],
                "lines": sum(len(it["run"]) for it in items),
                "pitch_mm": None,
                "why": NOT_ENOUGH_OF_THE_CELL,
                "what_would_settle_it": (
                    f"it covers {round(100 * foot.area / cell.area, 1)}% "
                    "of the cell it stands in, and no stair label stands "
                    "there")})
            continue
        asm = Assembly(
            stair_id=f"SA-{region_id}-{k:03d}", region_id=region_id,
            floor_from=floor_from, floor_to=floor_to,
            space_id=items[0]["space_id"],
            # THE STAIR'S OWN FOOTPRINT, not the room it stands in. The
            # cell's area is reported beside it and never as the stair.
            footprint_wkt=foot.wkt,
            footprint_area_m2=foot.area / 1e6,
            containing_space_area_m2=(None if cell is None
                                      else cell.area / 1e6),
            finish_rule=finish_rule,
            skirting_lm=(skirting_rule or {}).get("skirting_lm"),
            skirting_status=(
                SKIRTING_NOT_ESTABLISHED
                if not (skirting_rule or {}).get("skirting_lm")
                else "FROM_A_PROJECT_RULE"),
            evidence=tuple(sorted({e for it in items for e in it["ev"]})))

        exceptions = []
        for j, it in enumerate(items, 1):
            flight = _flight(it, region_id, k, j, cell, sections)
            asm.flights.append(flight)
            if any(r.status == RISER_NOT_ESTABLISHED for r in flight.risers):
                exceptions.append(RISER_NOT_ESTABLISHED)
            if not flight.treads:
                exceptions.append(TREAD_NOT_ESTABLISHED)
            sec = _section_for(sections, flight.flight_id, region_id)
            told = sec.get("treads")
            if told and int(told) != len(flight.treads):
                exceptions.append(PLAN_AND_SECTION_DISAGREE)

        asm.landings.extend(_landings(cell, [it["foot"] for it in items],
                                      region_id, k))
        axes = {it["axis"] for it in items}
        if len(items) >= 2 and len(axes) > 1:
            asm.configuration = L_SHAPED
        elif len(items) >= 2:
            asm.configuration = U_SHAPED
        elif asm.flights:
            asm.configuration = asm.flights[0].configuration
        # Do two flights of this stair cover the same ground? Then their
        # tread polygons cannot both be marble, and nothing here picks.
        feet = [it["foot"] for it in items]
        for i, fa in enumerate(feet):
            for fb in feet[i + 1:]:
                try:
                    if fa.intersection(fb).area > 1000.0:
                        exceptions.extend([FLIGHTS_OVERLAP,
                                           TREAD_NOT_ESTABLISHED])
                except Exception:      # noqa: BLE001
                    continue
        asm.exceptions = tuple(sorted(set(exceptions)))
        if TREAD_NOT_ESTABLISHED in asm.exceptions:
            for f in asm.flights:
                for t in f.treads:
                    t.status = TREAD_NOT_ESTABLISHED
        rep.assemblies.append(asm)

    rep.notes["a_plan_carries_no_height"] = (
        "every riser here is NOT ESTABLISHED unless section evidence was "
        "supplied. No standard rise is assumed")
    rep.notes["no_double_count"] = (
        "a stair's footprint belongs to the stair. Its area may not "
        "appear in any floor-finish quantity as well")
    rep.notes["runs_in_one_cell_are_one_stair"] = (
        "two flights and a landing are one staircase. Counting them as "
        "two would count the landing twice and the stair not at all")
    return rep


def _section_for(sections, flight_id: str, region_id: str) -> dict:
    src = sections or {}
    return dict(src.get(flight_id) or src.get(region_id) or {})


def _flight(item, region_id: str, k: int, j: int, cell, sections) -> Flight:
    """One run of treads, each measured from its own polygon."""
    axis, run = item["axis"], item["run"]
    lo = min(r[1] for r in run)
    hi = max(r[2] for r in run)
    flight = Flight(
        flight_id=f"SF-{region_id}-{k:03d}-{j:02d}", axis=axis,
        direction_mm=(run[0][0], run[-1][0]), width_mm=hi - lo,
        evidence=tuple(item["ev"]))
    for i in range(len(run) - 1):
        a, b = run[i], run[i + 1]
        # A WINDER'S TREAD IS NOT THE OVERLAP OF TWO LINES. Take the
        # stretch both lines reach over, clipped to the cell the stair
        # stands in, so a wedge is measured as the wedge it is.
        g = _polygon(axis, a[0], b[0], min(a[1], b[1]), max(a[2], b[2]))
        # Clipped to THIS FLIGHT's own footprint, and then to the cell.
        # Two flights side by side share their tread positions, and a
        # tread clipped only to the cell would cover its neighbour's
        # treads as well — a stair measuring more marble than it has.
        for clip in (item["foot"], cell):
            if clip is None:
                continue
            try:
                g = g.intersection(clip)
            except Exception:      # noqa: BLE001
                pass
        if g.is_empty or g.area <= 0:
            continue
        x0, y0, x1, y1 = g.bounds
        width = (x1 - x0) if axis == "H" else (y1 - y0)
        flight.treads.append(Tread(
            tread_id=f"ST-{region_id}-{k:03d}-{j:02d}-{i + 1:02d}",
            index=i + 1, polygon_wkt=g.wkt, area_m2=g.area / 1e6,
            going_mm=b[0] - a[0], width_mm=width,
            nosing_length_mm=a[2] - a[1],
            front_edge_wkt=_edge(axis, a[0], a[1], a[2]),
            back_edge_wkt=_edge(axis, b[0], b[1], b[2]),
            inner_edge_wkt=_edge("V" if axis == "H" else "H",
                                 min(a[1], b[1]), a[0], b[0]),
            outer_edge_wkt=_edge("V" if axis == "H" else "H",
                                 max(a[2], b[2]), a[0], b[0]),
            rectangular=abs((a[2] - a[1]) - (b[2] - b[1])) <= SAME_PITCH_MM,
            cad_provenance=(getattr(a[3], "object_id", ""),
                            getattr(b[3], "object_id", ""))))

    sec = _section_for(sections, flight.flight_id, region_id)
    rise = sec.get("riser_height_mm")
    told = sec.get("risers")
    n_risers = int(told) if told else len(flight.treads)
    for i in range(n_risers):
        w = (flight.treads[min(i, len(flight.treads) - 1)].width_mm
             if flight.treads else flight.width_mm)
        flight.risers.append(Riser(
            riser_id=f"SR-{region_id}-{k:03d}-{j:02d}-{i + 1:02d}",
            index=i + 1, width_mm=w,
            height_mm=(None if rise is None else float(rise)),
            area_m2=(None if rise is None else w * float(rise) / 1e6),
            height_source=(RISER_NOT_ESTABLISHED if rise is None
                           else "SECTION_EVIDENCE"),
            status=(RISER_NOT_ESTABLISHED if rise is None
                    else "RISER_MEASURED")))

    widths = {round(t.width_mm, 1) for t in flight.treads}
    goings = {round(t.going_mm, 1) for t in flight.treads}
    flight.configuration = (STRAIGHT if len(widths) == 1 and len(goings) == 1
                            else WINDER)
    return flight


def _pt(x: float, y: float):
    from shapely.geometry import Point

    return Point(x, y)


def _landings(cell, feet, region_id: str, n: int) -> list:
    """What the flights of one stair leave BETWEEN them.

    A landing is the piece a staircase turns on, and it lies between its
    flights — never the rest of the room the stair stands in. Taking the
    flights out of the space around them made a 1,229 m2 "landing" out
    of a floor plate on the first run of this module.
    """
    from shapely.geometry import box

    out = []
    if len(feet) < 2:
        return out
    x0 = min(f.bounds[0] for f in feet)
    y0 = min(f.bounds[1] for f in feet)
    x1 = max(f.bounds[2] for f in feet)
    y1 = max(f.bounds[3] for f in feet)
    rest = box(x0, y0, x1, y1)
    for f in feet:
        rest = rest.difference(f)
    if cell is not None:
        try:
            rest = rest.intersection(cell)
        except Exception:      # noqa: BLE001
            pass
    if rest.is_empty:
        return out
    for i, g in enumerate(getattr(rest, "geoms", [rest]), 1):
        if g.is_empty or g.area <= 0:
            continue
        bx0, by0, bx1, by1 = g.bounds
        out.append(Landing(
            landing_id=f"SL-{region_id}-{n:03d}-{i:02d}",
            polygon_wkt=g.wkt, area_m2=g.area / 1e6,
            length_mm=max(bx1 - bx0, by1 - by0),
            width_mm=min(bx1 - bx0, by1 - by0)))
    return out
