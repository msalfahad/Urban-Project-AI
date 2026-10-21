"""Run the twenty-three round-5 cases, and rounds 2, 3 and 4 alongside them.

Four sets of requirements now hold at once. A round that restored room
topology by loosening a gate would undo the three before it, so every case
is checked against all of them, and the universal invariants below are
applied to EVERY case rather than only to the ones that exist to test them:

    no opening is filled with invented material
    no unsupported gap is bridged
    open plan is not artificially split
    a fragmented but supported partition can restore room topology
    topology authority does not automatically grant material authority
    false room release remains zero
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import enclosure_role as roles
from engine import face_subdivision as fsub
from engine import freeze_manifest as fman
from engine import junction_recovery as jrec
from engine import partition_continuity as pcont
from engine import physical_wall as pwall
from engine import round5_fixtures as fixtures
from engine import semantic_seed as seeds_mod

NEVER_RELEASABLE = (roles.SITE_OR_PLOT, roles.BUILDING_ENVELOPE,
                    roles.SUPER_REGION, roles.DETAIL_OR_ANNOTATION)

VERDICT_ALIASES = {
    "ESTABLISHED": pcont.ESTABLISHED,
    "SUPPORTED": pcont.SUPPORTED,
    "OPENING_INTERRUPTION": pcont.OPENING_INTERRUPTION,
    "UNRESOLVED_GAP": pcont.UNRESOLVED_GAP,
    "NO_CONTINUATION": pcont.NO_CONTINUATION,
}


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
    spans = [s for c in rep.continuity for s in c.spans]
    junctions = [j for r in rep.junctions for j in r.junctions]
    diagnoses = [d for r in rep.subdivisions for d in r.diagnoses]
    cols = [c for r in rep.junctions for c in r.columns]

    obs = {
        "space_candidates": len(rep.rows),
        "complete": sum(1 for r in rep.rows if r.is_complete),
        "released": len(released),
        "by_enclosure_role": dict(Counter(r.enclosure_role
                                          for r in rep.rows)),
        "continuity": dict(Counter(s.verdict for s in spans)),
        "junctions_recovered": sum(1 for j in junctions if j.is_recovered),
        "columns_observed": len(cols),
        "functional_zone_groups": sum(1 for r in rep.rows
                                      if len(r.zones) > 1),
        "undersegmentation": [d.outcome for d in diagnoses],
        "faces_before_after": [
            (r.faces_before, r.faces_after) for r in rep.subdivisions],
        "areas_m2": sorted(round(r.enclosure.area_m2, 2) for r in released
                           if r.enclosure and r.enclosure.area_m2),
        "material_authority": dict(Counter(r.material_authority
                                           for r in rep.rows)),
    }
    bad = []
    e = case.expect

    # ================= universal invariants, every case ==================

    # rounds 2-4: nothing but a physical room may release
    for r in released:
        if r.enclosure_role in NEVER_RELEASABLE:
            bad.append(f"{r.space_id} released with role {r.enclosure_role}")
        if r.enclosure_role != roles.PHYSICAL_ROOM:
            bad.append(f"{r.space_id} released with non-room role "
                       f"{r.enclosure_role}")

    # §7: no material is ever recovered across an opening
    for s in spans:
        if s.verdict == pcont.OPENING_INTERRUPTION and \
                s.material_authority != pcont.MATERIAL_ABSENT:
            bad.append(f"{s.span_id} is an opening and claims "
                       f"{s.material_authority}")
        if s.verdict == pcont.OPENING_INTERRUPTION and s.may_subdivide:
            bad.append(f"{s.span_id} recovered a partition across an "
                       "opening")

    # §8: an unresolved gap recovers nothing
    for s in spans:
        if s.verdict in (pcont.UNRESOLVED_GAP, pcont.NO_CONTINUATION) and \
                s.may_subdivide:
            bad.append(f"{s.span_id} is {s.verdict} and was allowed to "
                       "subdivide")

    # §6: topology authority never grants material authority by itself
    for s in spans:
        if s.topology_authority in (pcont.TOPOLOGY_VALIDATED,
                                    pcont.TOPOLOGY_SUPPORTED) and \
                s.material_authority == pcont.MATERIAL_ESTABLISHED:
            bad.append(f"{s.span_id} recovered topology AND claimed "
                       "established material")

    # §9/§11: a face is never subdivided by its labels
    for d in diagnoses:
        if d.outcome == fsub.MULTIPLE_PHYSICAL_SPACES and \
                not d.supported_internal_partitions:
            bad.append(f"{d.space_id} was subdivided with no supported "
                       "partition inside it")

    # ============================ per case ==============================
    if "min_released" in e and len(released) < e["min_released"]:
        bad.append(f"expected at least {e['min_released']} released, got "
                   f"{len(released)}")
    if e.get("releases_nothing") and released:
        bad.append(f"expected no release, got "
                   f"{[r.space_id for r in released]}")
    if "door_candidates" in e:
        got = rep.openings.counts()["door_candidates"]
        if got != e["door_candidates"]:
            bad.append(f"expected {e['door_candidates']} doors, got {got}")
    if "window_candidates" in e:
        got = rep.openings.counts()["window_candidates"]
        if got != e["window_candidates"]:
            bad.append(f"expected {e['window_candidates']} windows, got "
                       f"{got}")
    for want in e.get("continuity_verdicts", ()):
        target = VERDICT_ALIASES[want]
        if target not in {s.verdict for s in spans}:
            bad.append(f"expected a {target} span; got "
                       f"{sorted({s.verdict for s in spans})}")
    if e.get("no_unresolved_gap") and any(
            s.verdict == pcont.UNRESOLVED_GAP for s in spans):
        bad.append("an unresolved gap appeared where the faces cover the "
                   "wall between them")
    if e.get("no_unsupported_recovery"):
        for s in spans:
            if s.may_subdivide and s.verdict not in (pcont.ESTABLISHED,
                                                     pcont.SUPPORTED):
                bad.append(f"{s.span_id} recovered on {s.verdict}")
    if e.get("no_continuation_or_nothing"):
        if any(j.is_recovered for j in junctions):
            bad.append("a wall that simply ends was extended to meet "
                       "something")
    if "junction_recovered" in e:
        got = bool(obs["junctions_recovered"])
        if got != e["junction_recovered"]:
            bad.append(f"junction_recovered: expected "
                       f"{e['junction_recovered']}, got {got}")
    if "columns_observed_at_least" in e and \
            len(cols) < e["columns_observed_at_least"]:
        bad.append(f"expected at least {e['columns_observed_at_least']} "
                   f"column observation(s), got {len(cols)}")
    if e.get("no_column_released_as_a_room"):
        for r in released:
            for c in cols:
                if r.enclosure and r.enclosure.area_m2 and \
                        _same_box(r, c):
                    bad.append(f"{r.space_id} released a column as a room")
    if "functional_zone_groups" in e and \
            obs["functional_zone_groups"] < e["functional_zone_groups"]:
        bad.append(f"expected {e['functional_zone_groups']} zone group(s), "
                   f"got {obs['functional_zone_groups']}")
    if "undersegmentation_outcome" in e:
        want = e["undersegmentation_outcome"]
        if want not in obs["undersegmentation"]:
            bad.append(f"expected a {want} diagnosis, got "
                       f"{obs['undersegmentation'] or 'none'}")
    if e.get("subdivision_needed_recovery"):
        # The honest measure is not a face COUNT — a room that leaks into
        # its own wall cavity is still one face. It is whether a released
        # space is actually held shut by a recovered span.
        if not any(r.recovered_boundary for r in released):
            bad.append("no released space was closed by a recovered span, "
                       "so the case cannot demonstrate that fragmented "
                       "geometry restores room topology")
    if e.get("material_authority_blocked_somewhere"):
        if pcont.MATERIAL_CANDIDATE not in {s.material_authority
                                            for s in spans}:
            bad.append("no span kept material authority back")
    if e.get("material_release_blocked_on_a_released_space"):
        if not any(r.material_authority != pcont.MATERIAL_ESTABLISHED
                   for r in released):
            bad.append("no released space had its material authority "
                       "withheld, so the case cannot show the two "
                       "authorities coming apart")
    if e.get("no_envelope_released"):
        for r in released:
            if r.enclosure_role == roles.BUILDING_ENVELOPE:
                bad.append(f"{r.space_id} released the envelope")
    if e.get("no_external_space_released"):
        for r in released:
            if any("COURT" in t.upper() for z in r.zones
                   for t in z.label_observations):
                bad.append(f"{r.space_id} released a courtyard as a room")
    if e.get("no_unlabelled_face_released"):
        for r in released:
            if not r.zones:
                bad.append(f"{r.space_id} released with no identity at all")
    if "layer_not_wall_like" in e:
        if e["layer_not_wall_like"] in prof.wall_like_layers():
            bad.append(f"layer {e['layer_not_wall_like']} was proposed "
                       "wall-like")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def _same_box(row, col) -> bool:
    from shapely.wkt import loads

    try:
        x0, y0, x1, y1 = loads(row.enclosure.polygon_wkt).bounds
    except Exception:       # noqa: BLE001
        return False
    return (abs(x0 - col.x0) < 1.0 and abs(y0 - col.y0) < 1.0
            and abs(x1 - col.x1) < 1.0 and abs(y1 - col.y1) < 1.0)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_5_SYNTHETIC_HASH": freeze_hash(),
        "FREEZE_MANIFEST_SCHEMA_HASH": fman.schema_hash(),
        "PHYSICAL_WALL_BAND_HASH": pwall.wall_band_hash(),
        "PARTITION_CONTINUITY_HASH": pcont.continuity_hash(),
        "JUNCTION_RECOVERY_HASH": jrec.junction_hash(),
        "FACE_SUBDIVISION_HASH": fsub.subdivision_hash(),
        "cases": len(res), "passed": sum(1 for r in res if r.passed),
        "failed": len(failed),
        "required_results_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "fragmented but independently supported wall geometry restores "
            "physical-space subdivision, and nothing else does. There is NO "
            "target room count and no target release count"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), pwall.wall_band_hash(),
             pcont.continuity_hash(), jrec.junction_hash(),
             fsub.subdivision_hash(), fman.schema_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-5 requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
