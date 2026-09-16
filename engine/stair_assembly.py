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
        "why": {
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
                                 MIN_WIDTH_MM)])
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
            "RISER_M2": (None if any(r.area_m2 is None for r in self.risers)
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
        return None if any(v is None for v in vals) else sum(vals)

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
            "footprint_wkt_mm": self.footprint_wkt,
            "MEASURED_NET": {
                "TREAD_M2": round(self.tread_m2, 4),
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

    A run is three or more lines whose spacing is a tread's going and
    repeats, and which span a common interval. That is what a flight of
    treads looks like in plan. It is also what a louvre looks like, which
    is why the caller still has to find stair evidence around it.
    """
    rows = []
    for c in lines:
        if getattr(c, "axis", "") != axis:
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        rows.append((c.fixed_mm, lo, hi, c))
    rows.sort()
    out, cur = [], []
    for row in rows:
        if not cur:
            cur = [row]
            continue
        gap = row[0] - cur[-1][0]
        span = min(cur[-1][2], row[2]) - max(cur[-1][1], row[1])
        same = (len(cur) < 2
                or abs(gap - (cur[-1][0] - cur[-2][0])) <= SAME_PITCH_MM)
        if MIN_GOING_MM <= gap <= MAX_GOING_MM and span > MIN_WIDTH_MM \
                and same:
            cur.append(row)
            continue
        if len(cur) >= MIN_TREADS:
            out.append(cur)
        cur = [row]
    if len(cur) >= MIN_TREADS:
        out.append(cur)
    return out


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
    section evidence: {stair key: {"riser_height_mm": ..., "risers": ...}}
    — a plan alone never produces a riser height, and nothing here
    invents one.
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

    n = 0
    for axis in ("H", "V"):
        for run in _runs(lines, axis):
            n += 1
            ev = [EV_CONSTANT_PITCH, EV_SPAN_TOGETHER]
            f_lo, f_hi = run[0][0], run[-1][0]
            lo = max(r[1] for r in run)
            hi = min(r[2] for r in run)
            width = hi - lo
            foot = _polygon(axis, f_lo, f_hi, lo, hi)

            # which measured space is this run standing in, and does a
            # stair label stand there too?
            space_id, inside = "", None
            for sid, g in poly_of.items():
                try:
                    if g.intersects(foot) and g.intersection(foot).area \
                            > foot.area * 0.5:
                        space_id, inside = sid, g
                        break
                except Exception:      # noqa: BLE001
                    continue
            if inside is not None:
                ev.append(EV_INSIDE_ONE_CELL)
            labelled = any(foot.buffer(0).contains(_pt(x, y))
                           for x, y in stair_points)
            if labelled:
                ev.append(EV_STAIR_LABEL)
            goings = [run[i + 1][0] - run[i][0] for i in range(len(run) - 1)]
            if goings and all(MIN_GOING_MM <= g <= MAX_GOING_MM
                              for g in goings):
                ev.append(EV_GOING_IS_A_STAIR_GOING)

            # A run of parallel lines is a stair when something other
            # than the lines themselves says so: the cell it stands in,
            # or a stair label in it. Decorative lines have neither.
            if EV_INSIDE_ONE_CELL not in ev and not labelled:
                rep.refused.append({
                    "run_id": f"RUN-{region_id}-{n:03d}",
                    "axis": axis, "lines": len(run),
                    "pitch_mm": round(goings[0], 1) if goings else None,
                    "why": NOT_A_STAIR,
                    "what_would_settle_it": (
                        "an enclosure around it, or a stair label in it")})
                continue

            flight = Flight(
                flight_id=f"SF-{region_id}-{n:03d}", axis=axis,
                direction_mm=(f_lo, f_hi), width_mm=width,
                evidence=tuple(ev))
            for i in range(len(run) - 1):
                a, b = run[i], run[i + 1]
                t_lo = max(a[1], b[1])
                t_hi = min(a[2], b[2])
                g = _polygon(axis, a[0], b[0], t_lo, t_hi)
                tread = Tread(
                    tread_id=f"ST-{region_id}-{n:03d}-{i + 1:02d}",
                    index=i + 1, polygon_wkt=g.wkt,
                    area_m2=g.area / 1e6, going_mm=b[0] - a[0],
                    width_mm=t_hi - t_lo,
                    nosing_length_mm=t_hi - t_lo,
                    front_edge_wkt=_edge(axis, a[0], t_lo, t_hi),
                    back_edge_wkt=_edge(axis, b[0], t_lo, t_hi),
                    inner_edge_wkt=_edge("V" if axis == "H" else "H",
                                         t_lo, a[0], b[0]),
                    outer_edge_wkt=_edge("V" if axis == "H" else "H",
                                         t_hi, a[0], b[0]),
                    rectangular=True,
                    cad_provenance=(getattr(a[3], "object_id", ""),
                                    getattr(b[3], "object_id", "")))
                flight.treads.append(tread)

            sec = (sections or {}).get(flight.flight_id) or \
                (sections or {}).get(region_id) or {}
            rise = sec.get("riser_height_mm")
            count = sec.get("risers")
            n_risers = int(count) if count else len(flight.treads)
            for i in range(n_risers):
                w = (flight.treads[min(i, len(flight.treads) - 1)].width_mm
                     if flight.treads else width)
                flight.risers.append(Riser(
                    riser_id=f"SR-{region_id}-{n:03d}-{i + 1:02d}",
                    index=i + 1, width_mm=w,
                    height_mm=(None if rise is None else float(rise)),
                    area_m2=(None if rise is None
                             else w * float(rise) / 1e6),
                    height_source=(RISER_NOT_ESTABLISHED if rise is None
                                   else "SECTION_EVIDENCE"),
                    status=(RISER_NOT_ESTABLISHED if rise is None
                            else "RISER_MEASURED")))

            widths = {round(t.width_mm, 1) for t in flight.treads}
            goings_r = {round(t.going_mm, 1) for t in flight.treads}
            flight.configuration = (
                STRAIGHT if len(widths) == 1 and len(goings_r) == 1
                else WINDER)

            exceptions = []
            if any(r.status == RISER_NOT_ESTABLISHED for r in flight.risers):
                exceptions.append(RISER_NOT_ESTABLISHED)
            if not flight.treads:
                exceptions.append(TREAD_NOT_ESTABLISHED)
            if count and len(flight.treads) and int(count) != \
                    len(flight.treads) and sec.get("treads") and \
                    int(sec["treads"]) != len(flight.treads):
                exceptions.append(PLAN_AND_SECTION_DISAGREE)

            asm = Assembly(
                stair_id=f"SA-{region_id}-{n:03d}", region_id=region_id,
                floor_from=floor_from, floor_to=floor_to,
                space_id=space_id, footprint_wkt=foot.wkt,
                footprint_area_m2=foot.area / 1e6,
                flights=[flight], configuration=flight.configuration,
                finish_rule=finish_rule,
                skirting_lm=(skirting_rule or {}).get("skirting_lm"),
                skirting_status=(
                    SKIRTING_NOT_ESTABLISHED
                    if not (skirting_rule or {}).get("skirting_lm")
                    else "FROM_A_PROJECT_RULE"),
                exceptions=tuple(exceptions), evidence=tuple(ev))

            # Anything inside the same cell that is deeper than a going
            # is a landing rather than a tread.
            if inside is not None:
                asm.landings.extend(_landings(inside, foot, axis,
                                              region_id, n))
                if asm.landings:
                    asm.configuration = (
                        L_SHAPED if len(asm.landings) == 1 else U_SHAPED)
            rep.assemblies.append(asm)

    rep.notes["a_plan_carries_no_height"] = (
        "every riser here is NOT ESTABLISHED unless section evidence was "
        "supplied. No standard rise is assumed")
    rep.notes["no_double_count"] = (
        "a stair's footprint belongs to the stair. Its area may not "
        "appear in any floor-finish quantity as well")
    return rep


def _pt(x: float, y: float):
    from shapely.geometry import Point

    return Point(x, y)


def _landings(cell, foot, axis: str, region_id: str, n: int) -> list:
    """What is left of the stair cell once the flight is taken out."""
    out = []
    try:
        rest = cell.difference(foot)
    except Exception:      # noqa: BLE001
        return out
    if rest.is_empty:
        return out
    parts = list(getattr(rest, "geoms", [rest]))
    for i, g in enumerate(parts, 1):
        if g.is_empty or g.area <= 0:
            continue
        x0, y0, x1, y1 = g.bounds
        depth = (y1 - y0) if axis == "H" else (x1 - x0)
        if depth < LANDING_MIN_MM:
            continue
        out.append(Landing(
            landing_id=f"SL-{region_id}-{n:03d}-{i:02d}",
            polygon_wkt=g.wkt, area_m2=g.area / 1e6,
            length_mm=max(x1 - x0, y1 - y0),
            width_mm=min(x1 - x0, y1 - y0)))
    return out
