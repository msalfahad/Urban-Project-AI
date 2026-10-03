"""Run the sixteen round-3 cases and enforce both sets of requirements.

Round 2's safety must hold at the same time as round 3's measurement. A
round that unlocked rooms by loosening a gate would undo the previous one,
so every case is checked against BOTH:

    ROUND 2 SAFETY   no site, envelope, super-region or frame may release
    ROUND 3 RESULTS  a site line never closes a room; external walls may;
                     doorways do not leak; zones are not rooms; bilingual
                     labels are not conflicts; unknown identity does not
                     destroy valid geometry
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import architectural_ontology as onto
from engine import boundary_authority as authority
from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import enclosure_role as roles
from engine import identity_reconcile as ident
from engine import round3_fixtures as fixtures
from engine import semantic_seed as seeds_mod

NEVER_RELEASABLE = (roles.SITE_OR_PLOT, roles.BUILDING_ENVELOPE,
                    roles.SUPER_REGION, roles.DETAIL_OR_ANNOTATION)


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


def check(case) -> Result:
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    prof = cprofile.build(nd)
    sem = seeds_mod.classify(nd.texts)
    rep = measure.measure(nd, prof, semantic=sem)

    released = [r for r in rep.rows
                if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]
    obs = {
        "space_candidates": len(rep.rows),
        "released": len(released),
        "by_enclosure_role": dict(Counter(r.enclosure_role
                                          for r in rep.rows)),
        "semantic": sem.counts(),
        "wall_like": rep.all_candidate_lines,
        "room_boundary_eligible": rep.candidate_lines,
        "areas_m2": sorted(round(r.enclosure.area_m2, 2) for r in released
                           if r.enclosure and r.enclosure.area_m2),
    }
    if rep.authority:
        obs["boundary_roles"] = rep.authority.by_role()
        obs["room_depth"] = rep.authority.room_depth
    if rep.identity:
        obs["identity"] = rep.identity.counts()
    bad = []

    # ---- round 2's safety, unchanged -----------------------------------
    for r in released:
        if r.enclosure_role in NEVER_RELEASABLE:
            bad.append(f"{r.space_id} released with role {r.enclosure_role}")
        if r.enclosure_role != roles.PHYSICAL_ROOM:
            bad.append(f"{r.space_id} released with non-room role "
                       f"{r.enclosure_role}")

    e = case.expect

    # ---- §6: a site line may never close a room ------------------------
    if e.get("site_must_not_close_a_room") and rep.authority:
        site_ids = {b.band_id for b in rep.authority.bands
                    if authority.SITE_BOUNDARY in b.roles}
        obs["site_bands"] = len(site_ids)
        for r in released:
            used = {seg["cad_provenance"] for seg in r.boundary_roles}
            if used & site_ids:
                bad.append(f"{r.space_id} was closed using a SITE_BOUNDARY "
                           "band — round 1's flood-to-plot, unchanged")
        if not site_ids:
            bad.append("no band was identified as a site boundary, so the "
                       "case cannot demonstrate what it exists to test")

    # ---- §5: an external building wall MAY close a room ----------------
    if e.get("external_wall_may_close") and rep.authority:
        env = {b.band_id for b in rep.authority.bands
               if authority.BUILDING_ENVELOPE in b.roles}
        obs["envelope_bands"] = len(env)
        used_env = any(seg["cad_provenance"] in env
                       for r in released for seg in r.boundary_roles)
        if not used_env:
            bad.append("no released room used a BUILDING_ENVELOPE band. "
                       "Overcorrecting round 1 by rejecting envelope walls "
                       "makes every corner room unmeasurable")

    if "min_released" in e and len(released) < e["min_released"]:
        bad.append(f"expected at least {e['min_released']} released, "
                   f"got {len(released)}")
    if e.get("releases_nothing") and released:
        bad.append(f"expected no release, got {len(released)}")

    # ---- a doorway must not merge two rooms ----------------------------
    if e.get("no_merged_super_room"):
        for r in released:
            n = sum(1 for g in (rep.identity.groups if rep.identity else ())
                    if r.enclosure and r.enclosure.polygon_wkt
                    and _inside(r.enclosure.polygon_wkt, g.x, g.y))
            if n > 1:
                bad.append(f"{r.space_id} released while containing {n} "
                           "separate identity groups — rooms merged")

    # ---- zones and external spaces are not rooms -----------------------
    if e.get("zones_not_rooms"):
        if any(o.semantic_class == seeds_mod.ROOM_LIKE
               for o in sem.observations):
            bad.append("a zone label was classed ROOM_LIKE")
        if released:
            bad.append("a functional zone was released as a physical room")
    for key, want in (("courtyard_is_external", seeds_mod.EXTERNAL_SPACE_LIKE),
                      ("terrace_is_external", seeds_mod.EXTERNAL_SPACE_LIKE)):
        if e.get(key) and want not in sem.counts():
            bad.append(f"expected an {want} observation; classes were "
                       f"{sem.counts()}")

    # ---- identity -------------------------------------------------------
    if "identity_relationship" in e and rep.identity:
        rels = {g.relationship for g in rep.identity.groups}
        obs["relationships"] = sorted(rels)
        if e["identity_relationship"] not in rels:
            bad.append(f"expected relationship {e['identity_relationship']}, "
                       f"got {sorted(rels)}")
    if "identity_established" in e and rep.identity:
        got = bool(rep.identity.established())
        if got != e["identity_established"]:
            bad.append(f"identity_established: expected "
                       f"{e['identity_established']}, got {got}")
    if "independent_statements" in e and rep.identity:
        best = max((g.supporting_observations
                    for g in rep.identity.groups), default=0)
        obs["independent_statements"] = best
        if best < e["independent_statements"]:
            bad.append(f"expected {e['independent_statements']} independent "
                       f"statements of one identity, got {best}")

    # ---- §10: unknown identity must not destroy valid geometry ---------
    if e.get("geometry_must_be_valid"):
        valid = [r for r in rep.rows
                 if r.physical_space_status == "PHYSICAL_SPACE_VALIDATED"]
        obs["physical_spaces_validated"] = len(valid)
        if not valid:
            bad.append("no physical space validated. An unreadable label "
                       "must not destroy correct geometry")
        if valid and valid[0].identity_status != ident.IDENTITY_UNKNOWN:
            bad.append("expected the identity to be UNKNOWN here")

    if e.get("frame_releases_nothing"):
        for r in released:
            if r.enclosure and r.enclosure.area_m2 and \
                    r.enclosure.area_m2 > 400.0:
                bad.append(f"{r.space_id} released a very large polygon; "
                           "the sheet frame may have been measured")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def _inside(wkt: str, x: float, y: float) -> bool:
    from shapely.geometry import Point
    from shapely.wkt import loads

    try:
        return loads(wkt).contains(Point(x, y))
    except Exception:      # noqa: BLE001
        return False


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_3_SYNTHETIC_HASH": freeze_hash(),
        "ROOM_BOUNDARY_AUTHORITY_HASH": authority.authority_hash(),
        "MULTILINGUAL_IDENTITY_HASH": ident.reconciler_hash(),
        "ONTOLOGY_HASH": onto.ontology_hash(),
        "cases": len(res), "passed": sum(1 for r in res if r.passed),
        "failed": len(failed),
        "required_results_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "locally supported room polygons from authored geometry, with "
            "round 2's safety unchanged. There is NO target room count"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), authority.authority_hash(),
             ident.reconciler_hash(), onto.ontology_hash(),
             seeds_mod.classifier_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-3 requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
