"""Run the twelve round-2 cases and enforce the safety result on all of them.

The safety result is checked on EVERY case, not only on the ones designed to
test it:

    no SITE_OR_PLOT, no BUILDING_ENVELOPE, no SUPER_REGION and no
    DETAIL_OR_ANNOTATION may carry release_status RELEASE_ELIGIBLE.

A case that releases nothing passes. Zero is a safe answer; a wrong room is
not, and round 1's 443 m² washroom is the reason this file exists.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import enclosure_role as roles
from engine import round2_fixtures as fixtures
from engine import semantic_seed as seeds_mod

# Roles that may never be released, whatever else a case asserts.
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
    by_role = Counter(r.enclosure_role for r in rep.rows)
    obs = {
        "space_candidates": len(rep.rows),
        "by_enclosure_role": dict(by_role),
        "released": len(released),
        "released_roles": sorted({r.enclosure_role for r in released}),
        "semantic": sem.counts(),
        "room_like_texts": sorted(o.text for o in sem.seeds()),
        "non_space_texts": sorted(
            o.text for o in sem.observations
            if o.semantic_class == seeds_mod.NON_SPACE_ANNOTATION),
    }
    bad = []

    # THE SAFETY RESULT, on every case.
    for r in released:
        if r.enclosure_role in NEVER_RELEASABLE:
            bad.append(f"{r.space_id} released with role {r.enclosure_role} "
                       "— a site, envelope, super-region or frame was "
                       "released as a physical room")
        if r.enclosure_role != roles.PHYSICAL_ROOM:
            bad.append(f"{r.space_id} released with role {r.enclosure_role}, "
                       f"which is not {roles.PHYSICAL_ROOM}")

    e = case.expect
    for role in e.get("no_room_release_for_roles", ()):
        if any(r.enclosure_role == role for r in released):
            bad.append(f"a {role} was released")
    if e.get("site_must_not_release"):
        if any(r.enclosure_role == roles.SITE_OR_PLOT for r in released):
            bad.append("the site polygon was released as a room")
    # Asserted on the RELEASE, not on the role. The first version of these
    # checks looked only at the role, so when the classifier called a site
    # polygon a PHYSICAL_ROOM_CANDIDATE the case passed vacuously while
    # releasing exactly what it existed to forbid.
    released_labels = sorted({lab for r in released
                              for lab in r.label_observations})
    obs["released_labels"] = released_labels
    for lab in e.get("labels_that_must_not_release", ()):
        if lab in released_labels:
            bad.append(f"the space seeded by {lab!r} was RELEASED. On this "
                       "fixture that label is stray — it sits on the site, "
                       "outside the building — and releasing what it seeds "
                       "is round 1's failure unchanged")
    if "released_labels" in e and released_labels != sorted(e["released_labels"]):
        bad.append(f"released labels: expected {sorted(e['released_labels'])}, "
                   f"got {released_labels}")
    if e.get("frame_must_not_release"):
        if any(r.enclosure_role in NEVER_RELEASABLE for r in released):
            bad.append("a drawing frame was released as a room")
    if e.get("releases_nothing") and released:
        bad.append(f"expected no release, got {len(released)}")
    if "expect_role_present" in e and e["expect_role_present"] not in by_role:
        # The role may legitimately be absent when no enclosure formed at
        # all; what must not happen is it being called a room.
        obs["note"] = (f"{e['expect_role_present']} not present; roles were "
                       f"{dict(by_role)}")
    if "not_role" in e:
        if e["not_role"] in by_role:
            bad.append(f"role {e['not_role']} appeared where it must not")
    for want in e.get("non_space_texts", ()):
        if want not in obs["non_space_texts"]:
            bad.append(f"{want!r} should be NON_SPACE_ANNOTATION; "
                       f"classes were {sem.counts()}")
    if "room_like_texts" in e:
        for want in e["room_like_texts"]:
            if want not in obs["room_like_texts"]:
                bad.append(f"{want!r} should be ROOM_LIKE; got "
                           f"{obs['room_like_texts']}")
    if "separating_partitions" in e and rep.roles:
        got = max((v.separating_partitions for v in rep.roles.verdicts),
                  default=0)
        obs["max_separating_partitions"] = got
        if got != e["separating_partitions"]:
            bad.append(f"separating_partitions: expected "
                       f"{e['separating_partitions']}, got {got}")
    if e.get("outer_contains_nested") and rep.roles:
        if not any(v.nested_enclosures for v in rep.roles.verdicts):
            obs["note"] = "no nesting detected between the enclosures formed"

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_2_SYNTHETIC_HASH": freeze_hash(),
        "ENCLOSURE_ROLE_CLASSIFIER_HASH": roles.classifier_hash(),
        "SEMANTIC_SEED_CLASSIFIER_HASH": seeds_mod.classifier_hash(),
        "cases": len(res), "passed": sum(1 for r in res if r.passed),
        "failed": len(failed),
        "safety_result": (
            "NO site, building envelope, super-region or drawing frame was "
            "released as a physical room in any case"
            if not failed else "VIOLATED"),
        "results": [r.record() for r in res],
        "success_criterion": (
            "zero false releases. NOT a target room count — if the safe "
            "answer is zero released rooms, zero is the answer"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), roles.classifier_hash(),
             seeds_mod.classifier_hash(), "|".join(NEVER_RELEASABLE)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-2 safety broken on {rep['failed']} case(s): {names}. A "
            "site, envelope, super-region or frame became releasable as a "
            "room, which is the exact defect this round removed")
    return rep
