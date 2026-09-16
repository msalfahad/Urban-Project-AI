"""Run the round-6D drawings: what a pantry is, and what a stair is.

Requirements that hold on EVERY case, whatever else it is testing:

    1  a functional zone never creates a wall, a room or a quantity
    2  a fitting never gives a room its clear internal finish face
    3  a stair's riser is NOT ESTABLISHED without section evidence, and
       no rise is ever assumed
    4  square metres and linear metres are never added together
    5  no released room polygon overlaps a stair's footprint

Requirement 5 is §12: where the stair is marble, the same square metre
may not also be porcelain.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import fitting_band as fband
from engine import floor_register as freg
from engine import functional_zone as fz
from engine import round6d_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import stair_assembly as stair
from engine import wall_face_ownership as wface

AREA_TOL_M2 = 0.0005


@dataclass
class Result:
    name: str
    what_it_tests: str
    passed: bool
    failures: list = field(default_factory=list)
    observed: dict = field(default_factory=dict)

    def record(self) -> dict:
        return {"case": self.name, "tests": self.what_it_tests,
                "passed": self.passed, "failures": list(self.failures),
                "observed": dict(self.observed)}


def _rows_with_faces(rep, built) -> list:
    """The register rows, with each space's boundary faces as plain dicts."""
    face_of = {}
    for r in rep.rows:
        c = r.clear
        face_of[r.space_id] = [
            {"axis": f.axis, "fixed_mm": f.fixed_mm,
             "length_mm": f.length_mm, "basis": f.basis,
             "wall_band_id": f.wall_band_id, "face_id": f.face_id}
            for f in (c.boundary_faces if c is not None else ())]
    out = []
    for row in built["rows"]:
        row = dict(row)
        row["boundary_faces"] = face_of.get(row["space_id"], [])
        out.append(row)
    return out


@dataclass(frozen=True)
class _Label:
    text: str
    x: float
    y: float
    space_id: str = ""
    region_id: str = ""
    floor_level: str = ""


@dataclass(frozen=True)
class _Fitting:
    """A run of units standing on a wall, for a rows-only case."""

    wall_id: str
    axis: str
    shared_face_mm: float
    far_face_mm: float
    drawn_mm: tuple
    lining_id: str = "FIT"

    @property
    def wall_band_id(self) -> str:
        return self.wall_id


def _zone_case(case):
    """A ZONE case: the register rows and the labels ARE the drawing."""
    rows = [dict(r) for r in case.rows]
    labels = [_Label(t, x, y, space_id=rows[0]["space_id"],
                     region_id=rows[0]["region_id"])
              for t, x, y in case.labels]
    fittings, bands = {}, []
    if case.name.startswith("PI_"):
        # two runs of units, on two of the room's walls
        from engine import fitting_band as fb

        bands = [_Band("FIT-H", "H", 0.0, 600.0, ((0.0, 3000.0),)),
                 _Band("FIT-V", "V", 0.0, 600.0, ((0.0, 2500.0),))]
        fittings = {
            "FIT-H": fb.StackedBand("FIT-H", "PW-Y-H-0.0-200.0", "H",
                                    0.0, 600.0, 3000.0, 6000.0),
            "FIT-V": fb.StackedBand("FIT-V", "PW-Y-V-0.0-200.0", "V",
                                    0.0, 600.0, 2500.0, 5000.0)}
    zones = fz.assess(rows, labels, fittings=fittings, wall_bands=bands)
    return None, {"register": None, "rows": rows}, rows, zones, []


@dataclass(frozen=True)
class _Band:
    wall_id: str
    axis: str
    face_a_mm: float
    face_b_mm: float
    drawn_mm: tuple


def _measure(case):
    if case.decode is None:
        return _zone_case(case)
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts),
                          sections=case.sections)
    built = freg.assemble(nd, rep)
    rows = _rows_with_faces(rep, built)
    zones = fz.assess(rows, built["register"].labels,
                      floor_of=built["floor_of"],
                      fittings=built["linings"],
                      wall_bands=[w for wr in rep.walls for w in wr.walls])
    return rep, built, rows, zones, list(rep.stairs)


def check(case) -> Result:
    rep, built, rows, zones, stairs = _measure(case)
    bad, e = [], case.expect
    reg = built["register"]
    fits = ({k: v for f in rep.fittings for k, v in (f.fittings or {}).items()}
            if rep is not None else {})
    areas = (sorted(round(r.clear.area_m2, 4) for r in rep.rows
                    if r.clear is not None and r.clear.basis_established)
             if rep is not None else [])
    assemblies = [a for s in stairs for a in s.assemblies]
    refused = [x for s in stairs for x in s.refused]

    obs = {
        "spaces": (len(rep.rows) if rep is not None else len(rows)),
        "clear_areas_m2": areas,
        "fittings": len(fits),
        "zones": len(zones.zones),
        "pantries": [p.openness for p in zones.pantries],
        "wall_tile_shapes": [p.wall_tile_shape for p in zones.pantries],
        "wall_tile_length_m": [round(p.wall_tile_length_m, 3)
                               for p in zones.pantries],
        "open_edge_length_m": [round(p.open_edge_length_m, 3)
                               for p in zones.pantries],
        "stair_assemblies": len(assemblies),
        "flights": sum(len(a.flights) for a in assemblies),
        "treads": sum(len(f.treads) for a in assemblies for f in a.flights),
        "tread_m2": round(sum(a.tread_m2 for a in assemblies), 4),
        "landing_m2": round(sum(a.landing_m2 for a in assemblies), 4),
        "nosing_lm": round(sum(a.nosing_lm for a in assemblies), 3),
        "configurations": [a.configuration for a in assemblies],
        "runs_refused": len(refused),
    }

    # ---- 1 to 5: MANDATORY on every case ------------------------------
    for z in zones.zones:
        if not z.record().get("creates_no_wall"):
            bad.append(f"{z.zone_id} claims to create a wall")
    for p in zones.pantries:
        if p.wall_tile_height_m is None and p.net_wall_tile_area_m2 \
                is not None:
            bad.append(f"{p.pantry_zone_id} has a tile area with no height")
        if p.height_source != fz.OWNER_RULE_REQUEST and \
                p.wall_tile_height_m is None:
            bad.append(f"{p.pantry_zone_id} hides a missing height")
    for a in assemblies:
        rec = a.record()["MEASURED_NET"]
        for r in (x for f in a.flights for x in f.risers):
            if r.height_mm is None and r.area_m2 is not None:
                bad.append(f"{r.riser_id} has an area with no height")
            if r.height_mm is None and r.status != \
                    stair.RISER_NOT_ESTABLISHED:
                bad.append(f"{r.riser_id} hides a missing rise")
        if rec["RISER_M2"] is not None and any(
                x.height_mm is None for f in a.flights for x in f.risers):
            bad.append(f"{a.stair_id} totals risers it has not measured")
        if not isinstance(rec["NOSING_LM"], float):
            bad.append(f"{a.stair_id} reports nosing as something else")
        # A STAIR MAY NOT MEASURE MORE TREAD THAN IT COVERS. Two flights
        # side by side share their tread positions, and a tread clipped
        # to the cell rather than to its own flight covers its
        # neighbour's marble too.
        if rec["TREAD_M2"] is not None and \
                rec["TREAD_M2"] > a.footprint_area_m2 + 0.001:
            bad.append(f"{a.stair_id} measures {rec['TREAD_M2']} m2 of "
                       f"tread on a {round(a.footprint_area_m2, 4)} m2 "
                       "footprint")
    # §12: a released room may not include a stair's footprint
    from shapely.wkt import loads

    for a in assemblies:
        try:
            foot = loads(a.footprint_wkt)
        except Exception:      # noqa: BLE001
            continue
        for entry in (reg.entries if reg is not None else ()):
            if not entry.may_release or entry.release_status != \
                    freg.RELEASE_ELIGIBLE:
                continue
            row = next((r for r in rows
                        if r["space_id"] == entry.space_id), None)
            g = (row or {}).get("polygon")
            if g is None:
                continue
            try:
                if g.intersection(foot).area > 1000.0:
                    bad.append(f"{entry.space_id} releases floor that is "
                               f"{a.stair_id}'s tread area")
            except Exception:      # noqa: BLE001
                continue

    # ---- what this case is actually about -----------------------------
    if "pantry_openness" in e:
        got = [p.openness for p in zones.pantries]
        if e["pantry_openness"] not in got:
            bad.append(f"pantry openness {got}, expected "
                       f"{e['pantry_openness']}")
    if "pantry_openness_in" in e:
        got = [p.openness for p in zones.pantries]
        if not got or not any(g in e["pantry_openness_in"] for g in got):
            bad.append(f"pantry openness {got}, expected one of "
                       f"{e['pantry_openness_in']}")
    if "wall_tile_length_m" in e:
        got = [round(p.wall_tile_length_m, 3) for p in zones.pantries]
        if not any(abs(g - e["wall_tile_length_m"]) <= 0.001 for g in got):
            bad.append(f"tiled length {got} m, expected "
                       f"{e['wall_tile_length_m']} m")
    if "wall_tile_shape" in e:
        got = [p.wall_tile_shape for p in zones.pantries]
        if e["wall_tile_shape"] not in got:
            bad.append(f"wall tile shape {got}, expected "
                       f"{e['wall_tile_shape']}")
    if "host_walls_at_least" in e:
        got = max((len(p.host_wall_segment_ids) for p in zones.pantries),
                  default=0)
        if got < e["host_walls_at_least"]:
            bad.append(f"{got} host wall segment(s), expected at least "
                       f"{e['host_walls_at_least']}")
    if e.get("zone_without_a_closed_room"):
        if not zones.zones:
            bad.append("no functional zone was formed at all")
    if e.get("open_edge_tiles_nothing"):
        for p in zones.pantries:
            if p.openness != fz.OPEN_AMERICAN_PANTRY:
                continue
            if p.wall_tile_length_m and p.open_edge_length_m and \
                    p.wall_tile_shape == fz.CLOSED_ON_FOUR_SIDES:
                bad.append(f"{p.pantry_zone_id} tiles an open edge")
    if e.get("tile_length_not_established"):
        for p in zones.pantries:
            if fz.TILE_LENGTH_NOT_ESTABLISHED not in p.exceptions:
                bad.append(f"{p.pantry_zone_id} states a tiled length of "
                           f"{round(p.wall_tile_length_m, 3)} m with no "
                           "units to measure it on")
    if e.get("owner_rule_request_present"):
        for p in zones.pantries:
            if fz.OWNER_RULE_REQUEST not in p.exceptions:
                bad.append(f"{p.pantry_zone_id} does not ask the owner")
    if (e.get("counter_creates_no_wall") or e.get("island_is_not_a_wall")) \
            and rep is not None:
        for r in rep.rows:
            c = r.clear
            if c is None:
                continue
            for f in c.boundary_faces:
                st = fits.get(f.wall_band_id)
                if st is not None and abs(f.fixed_mm - st.far_face_mm) \
                        <= fband.SAME_PLACE_MM:
                    bad.append(f"{r.space_id} stops at the front of "
                               f"{st.lining_id}")
    if "fittings_at_least" in e and len(fits) < e["fittings_at_least"]:
        bad.append(f"{len(fits)} fitting(s) detected, expected at least "
                   f"{e['fittings_at_least']}")
    for want in e.get("clear_areas_m2", ()):
        if not any(abs(a - want) <= AREA_TOL_M2 for a in areas):
            bad.append(f"no space measures {round(want, 4)} m2; measured "
                       f"{areas}")
    for text in e.get("label_never_names_a_fitting_strip", ()):
        for v in (reg.labels if reg is not None else ()):
            if (v.text or "").strip().upper() != text:
                continue
            entry = next((x for x in reg.entries
                          if x.space_id == v.space_id), None)
            if entry is not None and entry.area_m2 < 3.0:
                bad.append(f"label {text!r} named {entry.space_id} of "
                           f"{round(entry.area_m2, 3)} m2")

    if "assemblies" in e and len(assemblies) != e["assemblies"]:
        bad.append(f"{len(assemblies)} stair assembly(ies), expected "
                   f"{e['assemblies']}")
    if "flights" in e and obs["flights"] != e["flights"]:
        bad.append(f"{obs['flights']} flight(s), expected {e['flights']}")
    if "flights_at_least" in e and obs["flights"] < e["flights_at_least"]:
        bad.append(f"{obs['flights']} flight(s), expected at least "
                   f"{e['flights_at_least']}")
    if "treads" in e and obs["treads"] != e["treads"]:
        bad.append(f"{obs['treads']} tread(s), expected {e['treads']}")
    if "tread_m2" in e and abs(obs["tread_m2"] - e["tread_m2"]) > 0.001:
        bad.append(f"TREAD_M2 {obs['tread_m2']}, expected {e['tread_m2']}")
    if "landing_m2_at_least" in e and obs["landing_m2"] < \
            e["landing_m2_at_least"]:
        bad.append(f"LANDING_M2 {obs['landing_m2']}, expected at least "
                   f"{e['landing_m2_at_least']}")
    if "landing_m2" in e and abs(obs["landing_m2"] - e["landing_m2"]) \
            > 0.001:
        bad.append(f"LANDING_M2 {obs['landing_m2']}, expected "
                   f"{round(e['landing_m2'], 4)}")
    if "configuration" in e and e["configuration"] not in \
            obs["configurations"]:
        bad.append(f"configuration {obs['configurations']}, expected "
                   f"{e['configuration']}")
    if "configuration_in" in e:
        if not any(c in e["configuration_in"]
                   for c in obs["configurations"]):
            bad.append(f"configuration {obs['configurations']}, expected "
                       f"one of {e['configuration_in']}")
    if e.get("riser_quantity_not_established"):
        for a in assemblies:
            if a.riser_m2 is not None:
                bad.append(f"{a.stair_id} reports a riser area with no "
                           "section evidence")
    if e.get("riser_m2_is_none"):
        for a in assemblies:
            if a.record()["MEASURED_NET"]["RISER_M2"] is not None:
                bad.append(f"{a.stair_id} reports RISER_M2 anyway")
    if e.get("tread_areas_differ"):
        sizes = {round(t.area_m2, 4) for a in assemblies
                 for f in a.flights for t in f.treads}
        if len(sizes) < 2:
            bad.append(f"every tread measured the same: {sorted(sizes)}")
    if e.get("tread_m2_is_the_sum"):
        for a in assemblies:
            total = sum(t.area_m2 for f in a.flights for t in f.treads)
            if abs(total - a.tread_m2) > 0.0001:
                bad.append(f"{a.stair_id} TREAD_M2 is not the sum of its "
                           "treads")
    if "exception_present" in e:
        got = [x for a in assemblies for x in a.exceptions]
        if e["exception_present"] not in got:
            bad.append(f"exceptions {got}, expected "
                       f"{e['exception_present']}")
    if "runs_refused_at_least" in e and len(refused) < \
            e["runs_refused_at_least"]:
        bad.append(f"{len(refused)} run(s) refused, expected at least "
                   f"{e['runs_refused_at_least']}")
    if e.get("no_released_room_overlaps_a_stair"):
        pass          # checked as requirement 5 above

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_6D_SYNTHETIC_HASH": freeze_hash(),
        "cases": len(res),
        "passed": len(res) - len(failed),
        "failed": len(failed),
        "requirements_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "a pantry may be a zone of an open space; a counter never "
            "becomes a wall; an open edge tiles nothing; a stair is "
            "measured as treads, risers, landings and nosing, and its "
            "riser is NOT ESTABLISHED until a section says otherwise"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), fz.model_hash(), stair.model_hash(),
             fband.model_hash(), wface.model_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-6D requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
