"""Run the round-6C drawings and ask what each polygon IS.

Five requirements hold on every case, whatever else it is testing:

    1  nothing the register does not call a SPACE ever releases
    2  a container of spaces never releases alongside its children
    3  no label attaches to sheet content, or to the strip in front of a
       fitting
    4  nothing releases from a region that is not an established plan of
       an established floor
    5  every candidate carries a role from the frozen vocabulary

Requirements 1 to 4 are the whole of round 6C's safety: a register that
breaks any of them produces a number that looks like a floor area and is
not one. They are checked on every case, including the ones where no
release is expected at all.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import drawing_role as drole
from engine import floor_register as freg
from engine import round6c_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import space_register as sreg

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


@dataclass(frozen=True)
class _Region:
    """The smallest thing `build` needs of a region: an id and an origin."""

    region_id: str
    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, x, y) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass(frozen=True)
class _Label:
    text: str
    x: float
    y: float


def _released(reg):
    return [e for e in reg.entries
            if e.released]


def _label_of(reg, text: str):
    for v in reg.labels:
        if (v.text or "").strip().upper() == text.upper():
            return v
    return None


def _build_drawing(case):
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    return freg.assemble(nd, rep)


def _build_rows(case):
    """Case K: the rows ARE the drawing."""
    xs = [p for r in case.rows for p in (r["polygon"].bounds[0],
                                         r["polygon"].bounds[2])]
    ys = [p for r in case.rows for p in (r["polygon"].bounds[1],
                                         r["polygon"].bounds[3])]
    region = _Region(case.rows[0]["region_id"], min(xs), min(ys),
                     max(xs), max(ys))
    rows = [dict(r) for r in case.rows]
    floor_of = {region.region_id: "GROUND"}
    register = sreg.build(rows, [region], floor_of=floor_of)
    labels = []
    if "label_at_mm" in case.expect:
        x, y = case.expect["label_at_mm"]
        labels = [_Label(case.expect["labels_unresolved"][0], x, y)]
    register = sreg.reconcile_labels(register, labels, rows,
                                     floor_of=floor_of)
    roles = drole.classify([region], supervised={
        region.region_id: {"drawing_role": drole.FLOOR_PLAN,
                           "floor_level": "GROUND"}})
    return {"roles": roles, "floor_of": floor_of, "rows": rows,
            "linings": {}, "register": register,
            "release_refused_for_drawing_role": 0}


def check(case) -> Result:
    built = (_build_rows(case) if case.decode is None
             else _build_drawing(case))
    reg = built["register"]
    roles = built["roles"]
    bad, e = [], case.expect
    rel = _released(reg)
    by_id = {x.space_id: x for x in reg.entries}

    obs = {
        "candidates": len(reg.entries),
        "by_candidate_role": dict(Counter(
            x.candidate_role for x in reg.entries).most_common()),
        "released": len(rel),
        "released_area_m2": round(sum(x.area_m2 for x in rel), 4),
        "released_areas_m2": sorted(round(x.area_m2, 4) for x in rel),
        "by_role": dict(Counter(r.drawing_role
                                for r in roles.roles).most_common()),
        "regions_that_may_release": sum(1 for r in roles.roles
                                        if r.may_release_rooms),
        "labels": len(reg.labels),
        "labels_mapped": sum(1 for v in reg.labels
                             if v.status == sreg.LABEL_ONE_SPACE),
    }

    # ---- 1 to 5: MANDATORY on every case ------------------------------
    for x in reg.entries:
        if x.candidate_role not in sreg.CANDIDATE_ROLES:
            bad.append(f"{x.space_id} carries the role {x.candidate_role}")
    for x in rel:
        if not x.is_space:
            bad.append(f"{x.space_id} released and is not a space")
        if x.candidate_role == sreg.SUPER_REGION:
            bad.append(f"{x.space_id} released and is a super-region")
        kids = [by_id[c] for c in x.children if c in by_id]
        for k in kids:
            if k in rel:
                bad.append(f"{x.space_id} released with its child "
                           f"{k.space_id}")
        rr = roles.of(x.region_id)
        if not rr.may_release_rooms:
            bad.append(f"{x.space_id} released from a "
                       f"{rr.drawing_role} whose floor is {rr.floor_level}")
    for v in reg.labels:
        if v.status != sreg.LABEL_ONE_SPACE:
            continue
        target = by_id.get(v.space_id)
        if target is None:
            bad.append(f"label {v.text!r} names a space nobody registered")
            continue
        if target.candidate_role == sreg.DRAWING_ARTIFACT:
            bad.append(f"label {v.text!r} attached to sheet content")
        if sreg.LINING_FACE in target.blockers:
            bad.append(f"label {v.text!r} attached to the strip in front "
                       "of a fitting")

    # ---- what this case is actually about -----------------------------
    for text, want in (e.get("labels_map_to_area_m2") or {}).items():
        v = _label_of(reg, text)
        if v is None or v.status != sreg.LABEL_ONE_SPACE:
            bad.append(f"label {text!r} did not resolve to one space "
                       f"({v.why if v else 'no such label'})")
            continue
        got = by_id[v.space_id].area_m2
        if abs(got - want) > AREA_TOL_M2:
            bad.append(f"label {text!r} names {round(got, 4)} m2, expected "
                       f"{round(want, 4)} m2")
    for text in e.get("labels_unresolved", ()):
        v = _label_of(reg, text)
        if v is None:
            bad.append(f"label {text!r} was never read")
        elif v.status == sreg.LABEL_ONE_SPACE:
            bad.append(f"label {text!r} resolved to {v.space_id} "
                       f"({by_id[v.space_id].area_m2} m2) and should not")
    if "why" in e:
        v = _label_of(reg, e["labels_unresolved"][0])
        if v is not None and v.why != e["why"]:
            bad.append(f"the exception says {v.why}, expected {e['why']}")
    if "floors" in e:
        got = {r.floor_level for r in roles.roles
               if r.floor_level != drole.FLOOR_NOT_ESTABLISHED}
        missing = set(e["floors"]) - got
        if missing:
            bad.append(f"floor(s) {sorted(missing)} not established; "
                       f"got {sorted(got)}")
    if "roles_present" in e:
        got = {r.drawing_role for r in roles.roles}
        missing = set(e["roles_present"]) - got
        if missing:
            bad.append(f"role(s) {sorted(missing)} not found; "
                       f"got {sorted(got)}")
    if "regions_that_may_release_exactly" in e:
        if obs["regions_that_may_release"] != \
                e["regions_that_may_release_exactly"]:
            bad.append(f"{obs['regions_that_may_release']} region(s) may "
                       f"release, expected exactly "
                       f"{e['regions_that_may_release_exactly']}")
    if "regions_that_may_release_at_least" in e:
        if obs["regions_that_may_release"] < \
                e["regions_that_may_release_at_least"]:
            bad.append(f"{obs['regions_that_may_release']} region(s) may "
                       "release, expected at least "
                       f"{e['regions_that_may_release_at_least']}")
    if "no_release_below_m2" in e:
        for x in rel:
            if x.area_m2 < e["no_release_below_m2"]:
                bad.append(f"{x.space_id} released {round(x.area_m2, 4)} "
                           f"m2, below {e['no_release_below_m2']} m2")
    if "released_candidates_at_most" in e:
        if len(rel) > e["released_candidates_at_most"]:
            bad.append(f"{len(rel)} candidate(s) released, expected at "
                       f"most {e['released_candidates_at_most']}: "
                       f"{obs['released_areas_m2']}")
    if "released_area_never_exceeds_m2" in e:
        if obs["released_area_m2"] > e["released_area_never_exceeds_m2"] \
                + AREA_TOL_M2:
            bad.append(f"released {obs['released_area_m2']} m2 in total, "
                       f"more than the {e['released_area_never_exceeds_m2']}"
                       " m2 the drawing encloses")
    if "super_regions_at_least" in e:
        got = sum(1 for x in reg.entries
                  if x.candidate_role == sreg.SUPER_REGION)
        if got < e["super_regions_at_least"]:
            bad.append(f"{got} super-region(s), expected at least "
                       f"{e['super_regions_at_least']}")
    if "unidentified_spaces_at_least" in e:
        got = sum(1 for x in reg.entries if x.is_space and not x.label_raw)
        if got < e["unidentified_spaces_at_least"]:
            bad.append(f"{got} unidentified space(s), expected at least "
                       f"{e['unidentified_spaces_at_least']}")
    if "drawing_artifacts_at_least" in e:
        got = sum(1 for x in reg.entries
                  if x.candidate_role == sreg.DRAWING_ARTIFACT)
        if got < e["drawing_artifacts_at_least"]:
            bad.append(f"{got} candidate(s) called sheet content, expected "
                       f"at least {e['drawing_artifacts_at_least']}")
    if "repeated_geometry_groups_at_least" in e:
        groups = {x.repeated_in for x in reg.entries if x.repeated_in}
        if len(groups) < e["repeated_geometry_groups_at_least"]:
            bad.append(f"{len(groups)} repeated-geometry group(s), expected "
                       f"at least {e['repeated_geometry_groups_at_least']}")
    if e.get("no_release_of_repeated_geometry"):
        for x in rel:
            if x.repeated_in:
                bad.append(f"{x.space_id} released although it repeats in "
                           f"{list(x.repeated_in)}")
    if "one_space_claimed_by_labels_at_least" in e:
        counted = Counter(v.space_id for v in reg.labels
                          if v.status == sreg.LABEL_ONE_SPACE)
        top = max(counted.values(), default=0)
        if top < e["one_space_claimed_by_labels_at_least"]:
            bad.append(f"no space is claimed by "
                       f"{e['one_space_claimed_by_labels_at_least']} "
                       f"labels; the most any space has is {top}")
    if e.get("a_fitting_strip_is_never_a_room"):
        for x in reg.entries:
            if sreg.LINING_FACE in x.blockers and x.is_space:
                bad.append(f"{x.space_id} stops at a fitting and is still "
                           f"a {x.candidate_role}")
    if e.get("no_functional_zone_is_emitted"):
        for x in reg.entries:
            for key in x.record():
                if "zone" in key.lower() or "trade" in key.lower():
                    bad.append(f"the register emits {key!r}, which round "
                               "6C may not")
    if e.get("no_release_of_a_fitting_strip"):
        for x in reg.entries:
            if sreg.LINING_FACE in x.blockers and x.released:
                bad.append(f"{x.space_id} stops at a fitting and released "
                           f"{round(x.area_m2, 4)} m2")
    if e.get("a_stair_releases_no_room_area"):
        stairs = [x for x in reg.entries
                  if x.candidate_role == sreg.STAIR]
        if not stairs:
            bad.append("no candidate was registered as a stair at all")
        for x in stairs:
            if x.may_release:
                bad.append(f"{x.space_id} is a stair and may release "
                           f"{round(x.area_m2, 4)} m2 as a room")
    if e.get("no_release_outside_a_plan"):
        for x in rel:
            if roles.of(x.region_id).drawing_role not in \
                    drole.BOQ_ELIGIBLE_ROLES:
                bad.append(f"{x.space_id} released from a "
                           f"{roles.of(x.region_id).drawing_role}")

    return Result(case.name, case.what_it_tests, not bad, bad, obs)


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    failed = [r for r in res if not r.passed]
    return {
        "ROUND_6C_SYNTHETIC_HASH": freeze_hash(),
        "cases": len(res),
        "passed": len(res) - len(failed),
        "failed": len(failed),
        "requirements_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "a polygon releases an area only when the register calls it a "
            "space, it contains no other space, its region is an "
            "established plan of an established floor, and the label on it "
            "belongs to it"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), sreg.model_hash(), drole.model_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-6C requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
