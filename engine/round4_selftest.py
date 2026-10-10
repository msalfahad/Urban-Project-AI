"""Run the twenty-two round-4 cases, and rounds 2 and 3 alongside them.

Three sets of requirements have to hold at once now. A round that unlocked
rooms by loosening a gate would undo the previous two, so every case is
checked against all of them:

    ROUND 2 SAFETY   no site, envelope, super-region or frame releases
    ROUND 3 RESULTS  a site line never closes a room; external walls may
    ROUND 4 RESULTS  a wall gap never becomes a portal; a window never
                     becomes a passage; a doorless opening resolves
                     neither relation; transforms and nesting resolve; no
                     relationship crosses a drawing region; an unlabelled
                     room is still a physical space
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_openings as op
from engine import cad_profile as cprofile
from engine import drawing_region as dregion
from engine import enclosure_role as roles
from engine import portal_match as pmatch
from engine import room_partition_graph as rpg
from engine import round4_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import space_topologies as topo

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
    complete = [r for r in rep.rows if r.is_complete]
    oc = rep.openings.counts() if rep.openings else {}
    obs = {
        "drawing_regions": (rep.regions.counts()["drawing_regions"]
                            if rep.regions else 0),
        "space_candidates": len(rep.rows),
        "complete": len(complete),
        "released": len(released),
        "by_enclosure_role": dict(Counter(r.enclosure_role
                                          for r in rep.rows)),
        "openings": oc,
        "matching": (rep.matches.counts() if rep.matches else {}),
        "areas_m2": sorted(round(r.enclosure.area_m2, 2) for r in released
                           if r.enclosure and r.enclosure.area_m2),
    }
    bad = []
    e = case.expect

    # ---- rounds 2 and 3, unchanged -------------------------------------
    for r in released:
        if r.enclosure_role in NEVER_RELEASABLE:
            bad.append(f"{r.space_id} released with role {r.enclosure_role}")
        if r.enclosure_role != roles.PHYSICAL_ROOM:
            bad.append(f"{r.space_id} released with non-room role "
                       f"{r.enclosure_role}")

    # ---- counts --------------------------------------------------------
    if "min_released" in e and len(released) < e["min_released"]:
        bad.append(f"expected at least {e['min_released']} released, got "
                   f"{len(released)}")
    if e.get("releases_nothing") and released:
        bad.append(f"expected no release, got {len(released)}: "
                   f"{[r.space_id for r in released]}")
    if "min_complete" in e and len(complete) < e["min_complete"]:
        bad.append(f"expected at least {e['min_complete']} complete, got "
                   f"{len(complete)}")
    if "min_regions" in e and obs["drawing_regions"] < e["min_regions"]:
        bad.append(f"expected at least {e['min_regions']} drawing regions, "
                   f"got {obs['drawing_regions']}")
    for key, want in (("door_candidates", "door_candidates"),
                      ("window_candidates", "window_candidates")):
        if key in e and oc.get(want, 0) != e[key]:
            bad.append(f"expected {e[key]} {key}, got {oc.get(want, 0)}")

    # ---- §2: the class comes from the evidence -------------------------
    classes = {o.opening_class for o in (rep.openings.openings
                                         if rep.openings else [])}
    if "opening_classes" in e:
        for want in e["opening_classes"]:
            if want not in classes:
                bad.append(f"expected an opening classed {want}; got "
                           f"{sorted(classes) or 'none'}")
    if e.get("no_openings_at_all") and rep.openings and rep.openings.openings:
        bad.append(f"expected no opening hypothesis at all, got "
                   f"{sorted(classes)}")

    # ---- §5: the invariant ---------------------------------------------
    if e.get("no_opening_may_close"):
        closing = [o.opening_id for o in rep.openings.closing()]
        if closing:
            bad.append(f"a wall gap was allowed to close a boundary: "
                       f"{closing}")
    if e.get("grade_d_present"):
        grades = {o.grade for o in rep.openings.openings}
        if op.GRADE_D not in grades:
            bad.append(f"expected a GRADE_D hypothesis, got {sorted(grades)}")
    for o in (rep.openings.openings if rep.openings else []):
        if o.grade == op.GRADE_D and o.may_close_boundary:
            bad.append(f"{o.opening_id} is grade D and may close a boundary")
        if o.opening_class == op.WINDOW_OPENING and o.may_partition_rooms:
            bad.append(f"{o.opening_id} is a window and claims a "
                       "room-to-room partition")

    # ---- §4: widths -----------------------------------------------------
    if "opening_width_mm" in e:
        widths = [round(o.opening_length_mm, 1)
                  for o in rep.openings.openings if o.may_close_boundary]
        if e["opening_width_mm"] not in widths:
            bad.append(f"expected a geometric opening width of "
                       f"{e['opening_width_mm']} mm, got {widths}")

    # ---- §6, §7: the relation -------------------------------------------
    rels = {r.get("ROOM_PARTITION_RELATION")
            for g in rep.graphs for r in g.relations}
    obs["relations"] = sorted(x for x in rels if x)
    if "relation_present" in e and e["relation_present"] not in rels:
        bad.append(f"expected a {e['relation_present']} relation, got "
                   f"{sorted(x for x in rels if x)}")

    # ---- §9: a window is not a passage ----------------------------------
    if e.get("window_is_not_navigable"):
        for o in rep.openings.windows():
            if o.is_navigable:
                bad.append(f"{o.opening_id} is a window and is navigable")

    # ---- §8: zones -------------------------------------------------------
    zone_groups = sum(1 for r in rep.rows if len(r.zones) > 1)
    obs["functional_zone_groups"] = zone_groups
    if "functional_zone_groups" in e and \
            zone_groups < e["functional_zone_groups"]:
        bad.append(f"expected {e['functional_zone_groups']} functional-zone "
                   f"group(s), got {zone_groups}")

    # ---- §11: a room without a name is still a room ----------------------
    unknown_valid = [r for r in rep.rows if r.is_physical_space
                     and not r.zones]
    obs["validated_geometry_unknown_identity"] = len(unknown_valid)
    if "validated_geometry_unknown_identity" in e and \
            len(unknown_valid) < e["validated_geometry_unknown_identity"]:
        bad.append("expected a validated physical space with no readable "
                   f"identity, got {len(unknown_valid)}")

    # ---- §12: ambiguity ---------------------------------------------------
    if "ambiguous_hosts_at_least" in e:
        n = len(rep.matches.ambiguous()) if rep.matches else 0
        if n < e["ambiguous_hosts_at_least"]:
            bad.append(f"expected at least {e['ambiguous_hosts_at_least']} "
                       f"PORTAL_HOST_AMBIGUOUS, got {n}")
    if e.get("no_release_through_an_ambiguous_portal"):
        amb = {m.opening_id for m in (rep.matches.ambiguous()
                                      if rep.matches else [])}
        for r in released:
            used = {o["opening_id"] for o in r.boundary_openings}
            if used & amb:
                bad.append(f"{r.space_id} released through an ambiguous "
                           "portal host")
    if "unmatched_symbols_at_least" in e:
        n = len(rep.openings.unmatched_symbols) if rep.openings else 0
        if n < e["unmatched_symbols_at_least"]:
            bad.append(f"expected at least {e['unmatched_symbols_at_least']} "
                       f"unmatched door symbol(s), got {n}")

    # ---- §1: nothing crosses a drawing region -----------------------------
    if e.get("no_relationship_crosses_a_region") and rep.regions:
        for r in rep.rows:
            for seg in r.boundary_roles:
                pid = seg["cad_provenance"]
                if pid.startswith("PORTAL-"):
                    continue
                owner = rep.regions.of_object(pid)
                if owner is not None and owner.region_id != r.region_id:
                    bad.append(f"{r.space_id} in {r.region_id} was bounded "
                               f"by geometry from {owner.region_id}")
        for m in (rep.matches.matches if rep.matches else []):
            if not m.checks.get("ONE_DRAWING_REGION", True):
                bad.append(f"{m.opening_id} matched across a drawing region")

    # ---- Q: a gate is not an internal separator ---------------------------
    if e.get("gate_not_on_a_released_boundary"):
        gate_ids = {o.opening_id for o in rep.openings.openings
                    if o.host_status != "HOST_ESTABLISHED"}
        obs["openings_with_an_ineligible_host"] = len(gate_ids)
        if not gate_ids:
            bad.append("no opening was refused for sitting in a boundary "
                       "that may not close a room, so the case cannot "
                       "demonstrate what it exists to test")
        for r in released:
            if {o["opening_id"] for o in r.boundary_openings} & gate_ids:
                bad.append(f"{r.space_id} released using a gate in a "
                           "boundary that may not close a room")

    # ---- round 3's two structural requirements ----------------------------
    if e.get("site_must_not_close_a_room") and rep.authority:
        from engine import boundary_authority as authority

        site_ids = {b.band_id for b in rep.authority.bands
                    if authority.SITE_BOUNDARY in b.roles}
        obs["site_bands"] = len(site_ids)
        for r in released:
            if {s["cad_provenance"] for s in r.boundary_roles} & site_ids:
                bad.append(f"{r.space_id} was closed using a SITE_BOUNDARY")
        if not site_ids:
            bad.append("no band was identified as a site boundary")
    if e.get("external_wall_may_close") and rep.authority:
        from engine import boundary_authority as authority

        env = {b.band_id for b in rep.authority.bands
               if authority.BUILDING_ENVELOPE in b.roles}
        if not any(s["cad_provenance"] in env
                   for r in released for s in r.boundary_roles):
            bad.append("no released room used a BUILDING_ENVELOPE band")

    # ---- a door must not merge two rooms ----------------------------------
    if e.get("no_merged_super_room"):
        for r in released:
            if len(r.zones) > 1:
                bad.append(f"{r.space_id} released containing "
                           f"{len(r.zones)} identities — rooms merged")

    # ---- identity ----------------------------------------------------------
    if "identity_relationship" in e and rep.identity:
        got = {g.relationship for g in rep.identity.groups}
        if e["identity_relationship"] not in got:
            bad.append(f"expected relationship {e['identity_relationship']}, "
                       f"got {sorted(got)}")
    if "independent_statements" in e and rep.identity:
        best = max((g.supporting_observations
                    for g in rep.identity.groups), default=0)
        if best < e["independent_statements"]:
            bad.append(f"expected {e['independent_statements']} independent "
                       f"statements of one identity, got {best}")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_4_SYNTHETIC_HASH": freeze_hash(),
        "DRAWING_REGION_HASH": dregion.freeze_hash(),
        "CAD_OPENING_CLASSIFIER_HASH": op.classifier_hash(),
        "PORTAL_MATCHER_HASH": pmatch.matcher_hash(),
        "ROOM_PARTITION_GRAPH_HASH": rpg.graph_hash(),
        "cases": len(res), "passed": sum(1 for r in res if r.passed),
        "failed": len(failed),
        "required_results_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "openings close rooms only on evidence. There is NO target "
            "room count, and a case that requires nothing to happen is as "
            "important as one that requires a room"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), dregion.freeze_hash(),
             op.classifier_hash(), pmatch.matcher_hash(), rpg.graph_hash(),
             topo.ROOM_PARTITION_TOPOLOGY]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-4 requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
