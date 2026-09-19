"""Run the round-6A drawings and check what the fixture already knows.

Five requirements hold across every case, whatever else it is testing:

    1  no line serves two walls over the same stretch of itself
    2  a room stops at the face of the wall that FACES it
    3  no area is taken to a centreline or to an external face
    4  a missing site boundary never makes outside-the-building interior
    5  no exterior extent is invented where no site ring is drawn

Nothing here compares a measured number to a range. A room this file drew
has an exact clear rectangle, and the check is equality to a millimetre.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import cad_space_role as srole
from engine import interior_exterior as ie
from engine import round6_selftest as r6
from engine import round6a_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import wall_face_ownership as wface

AREA_TOL_M2 = 0.0005      # half a square millimetre: equality, in floats


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


def _clear(rep):
    return [r.clear for r in rep.rows if r.clear is not None]


def _established(rep):
    return [c for c in _clear(rep) if c.basis_established]


def _areas(rep):
    return sorted(round(c.area_m2, 4) for c in _established(rep))


def _has_area(rep, want: float) -> bool:
    return any(abs(a - want) <= AREA_TOL_M2 for a in _areas(rep))


def _face_ids(c) -> set:
    return {f.face_id for f in c.boundary_faces if f.face_id}


def _bands(c) -> set:
    return {f.wall_band_id for f in c.boundary_faces if f.wall_band_id}


def check(case) -> Result:
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    prof = cprofile.build(nd)
    sem = seeds_mod.classify(nd.texts)
    rep = measure.measure(nd, prof, semantic=sem)
    bad = []
    e = case.expect
    dropped = sum(len(o.dropped) for o in rep.ownership)
    obs = {
        "physical_spaces": len(rep.rows),
        "clear_internal_spaces": len(_established(rep)),
        "clear_areas_m2": _areas(rep),
        "lines_standing_inside_a_space": dropped,
        "wall_bands": sum(len(w.walls) for w in rep.walls),
    }

    # ---- 1. one line, one wall (round 6's rule, still held) -----------
    shared = r6._overlapping_shared_lines(rep)
    if shared:
        bad.append(f"{len(shared)} wall pair(s) share a face line over the "
                   f"same stretch, e.g. {shared[0][1]} and {shared[0][2]}")

    # ---- 2. every released polygon names every one of its sides -------
    for c in _clear(rep):
        if not c.basis_established:
            continue
        if c.basis != wface.CLEAR_INTERNAL_FINISH_FACE:
            bad.append(f"{c.space_id} released on basis {c.basis}")
        if any(f.basis != wface.CLEAR_INTERNAL_FINISH_FACE
               for f in c.boundary_faces):
            bad.append(f"{c.space_id} has a side with no established face")

    # ---- 3. no centreline, no external face --------------------------
    if e.get("no_centreline_area") or e.get("no_external_face_used"):
        for c in _established(rep):
            for f in c.boundary_faces:
                if f.basis in (wface.WALL_CENTERLINE, wface.EXTERNAL_FACE):
                    bad.append(f"{c.space_id} measured to {f.basis}")

    # ---- 4/5. the site is a different question from the building -----
    roles = getattr(rep, "space_roles", None)
    if roles is not None:
        obs["by_role"] = dict(Counter(v.role for v in roles.verdicts))
        obs["sites_established"] = sum(
            1 for m in roles.envelopes.values() if m.site is not None)
        obs["envelopes_established"] = sum(
            1 for m in roles.envelopes.values() if m.has_envelope)

    if e.get("site_extent") == ie.SITE_UNKNOWN:
        if obs.get("sites_established"):
            bad.append("a site boundary was established where the fixture "
                       "drew none — an invented exterior extent")
    if e.get("nothing_outside_is_interior") and roles is not None:
        for v in roles.verdicts:
            if v.role == srole.EXTERIOR_EXTENT_UNRESOLVED and v.is_interior:
                bad.append(f"{v.space_id} is outside the building and "
                           "interior at the same time")

    # ---- per case -----------------------------------------------------
    for want in e.get("clear_areas_m2", ()):
        if not _has_area(rep, want):
            bad.append(f"no space measures {round(want, 4)} m2 on the "
                       f"clear-internal basis; measured {_areas(rep)}")

    if "lines_standing_inside_a_space" in e:
        if dropped < e["lines_standing_inside_a_space"]:
            bad.append(f"only {dropped} line(s) were found standing inside "
                       f"a space, expected at least "
                       f"{e['lines_standing_inside_a_space']}")

    if e.get("opposite_faces_of_one_wall"):
        shared_bands = Counter()
        for c in _established(rep):
            for band in _bands(c):
                shared_bands[band] += 1
        pairs = [b for b, n in shared_bands.items() if n >= 2]
        obs["wall_bands_serving_two_spaces"] = len(pairs)
        if not pairs:
            bad.append("no wall band gives a face to two different spaces, "
                       "so nothing was measured from opposite faces")
        # At least one band must give DIFFERENT faces to two spaces. An
        # external wall legitimately gives the same face to two rooms that
        # both sit inside it; a partition between them may not.
        two_faced = 0
        for band in pairs:
            faces = set()
            for c in _established(rep):
                faces |= {f.face_id for f in c.boundary_faces
                          if f.wall_band_id == band}
            if len(faces) >= 2:
                two_faced += 1
        obs["wall_bands_giving_opposite_faces"] = two_faced
        if not two_faced:
            bad.append("no wall band gave its two OPPOSITE faces to two "
                       "different spaces")

    if e.get("clear_bounds_mm"):
        want = [round(v, 1) for v in e["clear_bounds_mm"]]
        from shapely.wkt import loads

        got = []
        for c in _established(rep):
            try:
                got.append([round(v, 1) for v in loads(c.polygon_wkt).bounds])
            except Exception:      # noqa: BLE001
                continue
        obs["clear_bounds_mm"] = got
        if want not in got:
            bad.append(f"no space has bounds {want}; measured {got}")

    if e.get("measurement_basis"):
        if not any(c.basis == e["measurement_basis"]
                   for c in _established(rep)):
            bad.append(f"no space carries basis {e['measurement_basis']}")

    if e.get("no_truncation_at_the_opening"):
        for c in _established(rep):
            for f in c.boundary_faces:
                if f.basis == wface.BASIS_NOT_ESTABLISHED:
                    bad.append(f"{c.space_id} is cut short at a side "
                               "nothing accounts for")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_6A_SYNTHETIC_HASH": freeze_hash(),
        "cases": len(res),
        "passed": len(res) - len(failed),
        "failed": len(failed),
        "requirements_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "a room stops at the face of the wall that faces it, a line "
            "with floor on both sides bounds nothing, and a missing site "
            "boundary never makes outside-the-building interior. There is "
            "no target room count and no tolerance band"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), wface.model_hash(),
             srole.classifier_hash(), ie.model_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-6A requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
