"""Run the round-6B drawings and check the three authorities separately.

Four requirements hold on every case, whatever else it is testing:

    1  no line becomes a partition without POSITIVE architectural evidence
    2  a partition that establishes topology establishes NO material
    3  a partition whose thickness is unknown does not release a clear area
    4  no second wall face is ever invented

Requirement 2 is §6 and it is mandatory: it is checked on every case,
including the ones where no partition is expected at all.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import round6a_selftest as r6a
from engine import round6b_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import single_line_partition as slp
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


def _candidates(rep):
    return [c for pr in rep.partitions for c in pr.candidates]


def _established(rep):
    return [c for c in _candidates(rep) if c.establishes_topology]


def _material_m(rep) -> float:
    """Every metre of wall this run says is MEASURABLE, from a partition."""
    total = 0.0
    for r in rep.rows:
        total += r.quantities.get("SINGLE_LINE_PARTITION_LENGTH_MM", 0.0)
    return round(total / 1000.0, 3)


def _areas(rep):
    return sorted(round(r.clear.area_m2, 4) for r in rep.rows
                  if r.clear is not None and r.clear.basis_established)


def check(case) -> Result:
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    bad, e = [], case.expect
    cands = _candidates(rep)
    est = _established(rep)
    obs = {
        "physical_spaces": len(rep.rows),
        "partition_candidates": len(cands),
        "topology_established": len(est),
        "clear_face_established": sum(1 for c in cands
                                      if c.establishes_clear_face),
        "by_status": dict(Counter(c.status for c in cands).most_common()),
        "clear_areas_m2": _areas(rep),
        "spaces_with_clear_face_not_established": sum(
            1 for r in rep.rows if r.clear is not None
            and r.clear.basis == wface.CLEAR_FACE_NOT_ESTABLISHED),
    }

    # ---- 2 and 4: MANDATORY on every case ----------------------------
    for c in cands:
        if c.material_authority != slp.MATERIAL_NOT_ESTABLISHED:
            bad.append(f"{c.candidate_id} claims {c.material_authority}")
        if c.record()["material_contribution_m"] != 0.0:
            bad.append(f"{c.candidate_id} contributes material")
    partition_material = 0.0
    for r in rep.rows:
        q = r.quantities
        held = q.get("SINGLE_LINE_PARTITION_LENGTH_MM", 0.0)
        est_len = q.get("MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM", 0.0)
        gross = q.get("SPACE_BOUNDARY_LENGTH_MM", 0.0)
        partition_material += held
        if held and est_len > gross - held + 1.0:
            bad.append(f"{r.space_id} counts partition length as material")
    obs["partition_boundary_length_m"] = round(partition_material / 1000, 3)

    # ---- 1 and 3: what this case is actually about -------------------
    if "topology_established_at_least" in e:
        if len(est) < e["topology_established_at_least"]:
            bad.append(f"only {len(est)} partition(s) established, expected "
                       f"at least {e['topology_established_at_least']}")
    if "topology_established_exactly" in e:
        if len(est) != e["topology_established_exactly"]:
            bad.append(f"{len(est)} partition(s) established, expected "
                       f"exactly {e['topology_established_exactly']}: "
                       + ", ".join(f"{c.source_entity_id}{list(c.evidence)}"
                                   for c in est[:3]))
    if "clear_face_established_at_least" in e:
        got = sum(1 for c in cands if c.establishes_clear_face)
        if got < e["clear_face_established_at_least"]:
            bad.append(f"only {got} clear face(s) established, expected at "
                       f"least {e['clear_face_established_at_least']}")
    if "clear_face_established_exactly" in e:
        got = sum(1 for c in cands if c.establishes_clear_face)
        if got != e["clear_face_established_exactly"]:
            bad.append(f"{got} clear face(s) established, expected exactly "
                       f"{e['clear_face_established_exactly']}")
    if "two_spaces_at_least" in e:
        if len(rep.rows) < e["two_spaces_at_least"]:
            bad.append(f"{len(rep.rows)} physical space(s), expected at "
                       f"least {e['two_spaces_at_least']}")
    for want in e.get("clear_areas_m2", ()):
        if not any(abs(a - want) <= AREA_TOL_M2 for a in _areas(rep)):
            bad.append(f"no space measures {round(want, 4)} m2; measured "
                       f"{_areas(rep)}")
    if "spaces_with_clear_face_not_established_at_least" in e:
        got = obs["spaces_with_clear_face_not_established"]
        if got < e["spaces_with_clear_face_not_established_at_least"]:
            bad.append(f"{got} space(s) carry CLEAR_FACE_NOT_ESTABLISHED, "
                       f"expected at least "
                       f"{e['spaces_with_clear_face_not_established_at_least']}")
    if e.get("no_clear_area_released_beside_the_partition"):
        for r in rep.rows:
            c = r.clear
            if c is None or not c.basis_established:
                continue
            if any(f.basis == wface.CLEAR_FACE_NOT_ESTABLISHED
                   for f in c.boundary_faces):
                bad.append(f"{r.space_id} released an area although a "
                           "partition of unknown thickness bounds it")
    if e.get("every_candidate_material_not_established"):
        if any(c.material_authority != slp.MATERIAL_NOT_ESTABLISHED
               for c in cands):
            bad.append("a candidate claims material authority")

    # ---- round 6A must not regress -----------------------------------
    shared = r6a.r6._overlapping_shared_lines(rep)
    if shared:
        bad.append(f"{len(shared)} wall pair(s) share a face line")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_6B_SYNTHETIC_HASH": freeze_hash(),
        "cases": len(res),
        "passed": len(res) - len(failed),
        "failed": len(failed),
        "requirements_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "a line becomes a partition only on positive architectural "
            "evidence; a partition that establishes topology establishes "
            "no material and, without independent face evidence, no clear "
            "area either. No second wall face is ever invented"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), slp.model_hash(), wface.model_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-6B requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
