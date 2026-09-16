"""Run the round-6E cases: identity, release, agreement, stairs.

Requirements that hold on EVERY case of a kind, whatever else it tests:

    LINEAGE      a split gives no child the parent's id, and a merge
                 keeps every predecessor
    RELEASE      a released entry never contradicts its own state
    CONSISTENCY  a disagreement is reported with BOTH numbers, unchanged
    STAIR        a landing is part of the stair, and a stair's kind is
                 never read off its width alone
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import floor_register as freg
from engine import report_consistency as rcons
from engine import round6e_fixtures as fixtures
from engine import semantic_seed as seeds_mod
from engine import space_lineage as lineage
from engine import space_register as sreg
from engine import stair_assembly as stair


@dataclass
class Result:
    name: str
    what_it_tests: str
    kind: str
    passed: bool
    failures: list = field(default_factory=list)
    observed: dict = field(default_factory=dict)

    def record(self) -> dict:
        return {"case": self.name, "tests": self.what_it_tests,
                "kind": self.kind, "passed": self.passed,
                "failures": list(self.failures),
                "observed": dict(self.observed)}


@dataclass(frozen=True)
class _Region:
    region_id: str
    x0: float
    y0: float
    x1: float
    y1: float


def _box(b):
    from shapely.geometry import box

    return box(*b)


def _regions(rows):
    xs = [v for r in rows for v in (r["box"][0], r["box"][2])]
    ys = [v for r in rows for v in (r["box"][1], r["box"][3])]
    rid = rows[0]["region_id"]
    return [_Region(rid, min(xs), min(ys), max(xs), max(ys))]


def _lineage_rows(rows) -> list:
    return [{"space_id": r["space_id"], "region_id": r["region_id"],
             "polygon": _box(r["box"]),
             "area_m2": _box(r["box"]).area / 1e6,
             "normalized_identity": r.get("normalized_identity", ""),
             "candidate_role": r.get("candidate_role", ""),
             "wall_band_ids": ()} for r in rows]


def _previous(rows) -> dict:
    out = []
    for r in _lineage_rows(rows):
        out.append({"stable_space_id": r["space_id"],
                    "run_candidate_id": r["space_id"],
                    "drawing_region_id": r["region_id"],
                    "floor": "", "area_m2": r["area_m2"],
                    "normalized_identity": r["normalized_identity"],
                    "candidate_role": r["candidate_role"],
                    "wall_band_ids": [],
                    "polygon_wkt_mm": r["polygon"].wkt})
    return {"model": lineage.MODEL, "run_id": "PREVIOUS", "spaces": out}


def _check_lineage(case) -> Result:
    bad = []
    prev_rows = case.payload["previous"]
    now_rows = case.payload["now"]
    rep = lineage.assign(_lineage_rows(now_rows),
                         _regions(prev_rows + now_rows),
                         previous=_previous(prev_rows), run_id="NOW")
    by_id = {x.run_candidate_id: x for x in rep.links}
    obs = {
        "lineage": {k: v.lineage for k, v in by_id.items()},
        "stable_ids": {k: v.stable_space_id for k, v in by_id.items()},
        "predecessors": {k: list(v.predecessor_ids)
                         for k, v in by_id.items()},
        "removed": [r["stable_space_id"] for r in rep.removed],
        "counts": rep.counts(),
    }

    # MANDATORY, on every lineage case
    for link in rep.links:
        if link.lineage == lineage.SPLIT and \
                link.stable_space_id in link.predecessor_ids:
            bad.append(f"{link.run_candidate_id} inherited its parent's id "
                       "on a split")
        if link.lineage == lineage.MERGED and len(
                link.predecessor_ids) < 2:
            bad.append(f"{link.run_candidate_id} merged and lost a "
                       "predecessor")
        if link.lineage == lineage.UNRESOLVED_LINEAGE and \
                link.stable_space_id in link.predecessor_ids:
            bad.append(f"{link.run_candidate_id} carried an id it could "
                       "not establish")
        if not link.reason or not link.confidence:
            bad.append(f"{link.run_candidate_id} states no reason")

    e = case.expect
    for sid, want in (e.get("lineage") or {}).items():
        got = obs["lineage"].get(sid)
        if got != want:
            bad.append(f"{sid} lineage {got}, expected {want}")
    for sid, want in (e.get("stable_ids") or {}).items():
        got = obs["stable_ids"].get(sid)
        if got != want:
            bad.append(f"{sid} stable id {got}, expected {want}")
    for sid, want in (e.get("predecessors") or {}).items():
        got = obs["predecessors"].get(sid)
        if sorted(got or ()) != sorted(want):
            bad.append(f"{sid} predecessors {got}, expected {want}")
    for old in e.get("no_child_keeps") or ():
        if old in obs["stable_ids"].values():
            bad.append(f"{old} was carried forward and may not be")
    for old in e.get("removed") or ():
        if old not in obs["removed"]:
            bad.append(f"{old} is gone and was not reported REMOVED")
    if e.get("unresolved_is_explicit"):
        if not any(x.lineage == lineage.UNRESOLVED_LINEAGE
                   and x.reason for x in rep.links):
            bad.append("the unresolved case states no explicit exception")
    return Result(case.name, case.what_it_tests, case.kind, not bad, bad,
                  obs)


def _check_release(case) -> Result:
    bad = []
    rows = case.payload["rows"]
    built = [{"space_id": r["space_id"], "region_id": r["region_id"],
              "polygon": _box(r["box"]),
              "area_m2": _box(r["box"]).area / 1e6,
              "basis": r["basis"],
              "candidate_role": r["candidate_role"],
              "raw_label": r.get("raw_label", ""),
              "release_status": r.get("release_status", ""),
              "blockers": list(r.get("blockers", ()))} for r in rows]
    labels = [(r["space_id"], r["raw_label"]) for r in rows
              if r.get("raw_label")]
    # THE MEASUREMENT GATE IS OPEN ON EVERY ROW. That is the point of
    # the failing cases: the geometry is fine and the ROLE still may not
    # release, and one state has to say so.
    register = sreg.build(
        built, _regions(rows),
        floor_of={rows[0]["region_id"]: "GROUND"},
        may_release_in={r["region_id"]: True for r in rows})
    obs = {
        "released": sorted(e.space_id for e in register.entries
                           if e.released),
        "roles": {e.space_id: e.candidate_role
                  for e in register.entries},
        "withheld": {e.space_id: list(e.withheld_because)
                     for e in register.entries if not e.released},
        "labels": len(labels),
    }
    # MANDATORY: one state, and nothing released that contradicts it
    for e in register.entries:
        if not e.released:
            continue
        if not e.is_space:
            bad.append(f"{e.space_id} released and is not a space")
        if not e.may_release:
            bad.append(f"{e.space_id} released and may_release is false")
        if e.candidate_role in sreg.NEVER_A_ROOM_QUANTITY:
            bad.append(f"{e.space_id} released as {e.candidate_role}")
        if e.withheld_because:
            bad.append(f"{e.space_id} released and is withheld")
    exp = case.expect
    if "contradictions" in exp and len(bad) != exp["contradictions"]:
        bad.append(f"{len(bad)} contradictions, expected "
                   f"{exp['contradictions']}")
    for sid in exp.get("never_released") or ():
        if sid in obs["released"]:
            bad.append(f"{sid} was released and never may be")
        entry = next((e for e in register.entries if e.space_id == sid),
                     None)
        if entry is not None and not entry.withheld_because:
            bad.append(f"{sid} was withheld with no reason given")
    for sid, want in (exp.get("roles") or {}).items():
        entry = next((e for e in register.entries if e.space_id == sid),
                     None)
        got = entry.candidate_role if entry is not None else None
        if got != want:
            bad.append(f"{sid} candidate role {got}, expected {want}")
    if "released_at_least" in exp and \
            len(obs["released"]) < exp["released_at_least"]:
        bad.append(f"{len(obs['released'])} released, expected at least "
                   f"{exp['released_at_least']}")
    return Result(case.name, case.what_it_tests, case.kind, not bad, bad,
                  obs)


def _check_consistency(case) -> Result:
    bad = []
    out = rcons.check(case.payload["metrics"], case.payload["tables"])
    obs = {"status": out["status"],
           "checks": [c for c in out["checks"]],
           "disagreements": len(out["disagreements"])}
    e = case.expect
    if out["status"] != e.get("status"):
        bad.append(f"status {out['status']}, expected {e.get('status')}")
    if len(out["disagreements"]) != e.get("disagreements", 0):
        bad.append(f"{len(out['disagreements'])} disagreements, expected "
                   f"{e.get('disagreements')}")
    # MANDATORY: a disagreement carries BOTH numbers, unchanged
    for c in out["disagreements"]:
        if c["report_value"] == c["export_value"]:
            bad.append(f"{c['metric']} was adjusted to agree")
    if "report_value_unchanged" in e:
        got = [c["report_value"] for c in out["disagreements"]]
        if e["report_value_unchanged"] not in got:
            bad.append(f"the report value {e['report_value_unchanged']} "
                       "was not carried through unchanged")
    if "export_value_unchanged" in e:
        got = [c["export_value"] for c in out["disagreements"]]
        if e["export_value_unchanged"] not in got:
            bad.append(f"the export value {e['export_value_unchanged']} "
                       "was not carried through unchanged")
    return Result(case.name, case.what_it_tests, case.kind, not bad, bad,
                  obs)


def _check_stair(case) -> Result:
    bad = []
    nd = adapter.normalize(case.payload["decode"], source_file=case.name,
                           source_hash="FIXTURE")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    built = freg.assemble(nd, rep)
    interior = ({v.space_id: v.interior_exterior
                 for v in rep.space_roles.verdicts}
                if rep.space_roles else {})
    model = stair.reconcile(rep.stairs, regions=rep.regions.regions,
                            floor_of=built["floor_of"],
                            interior_of=interior)
    stairs = model["physical_stairs"]
    assemblies = [a for s in rep.stairs for a in s.assemblies]
    pieces = [x for a in assemblies for x in a.landings]
    obs = {
        "physical_stairs": len(stairs),
        "roles": {x.physical_stair_id: x.stair_role for x in stairs},
        "widths": {x.physical_stair_id: round(x.width_m, 3)
                   for x in stairs},
        "floors": {x.physical_stair_id: list(x.floors) for x in stairs},
        "piece_roles": [x.role for x in pieces],
        "landing_m2": round(sum(a.landing_m2 for a in assemblies), 4),
        "pieces_m2": [round(x.area_m2, 4) for x in pieces],
    }
    # MANDATORY on every stair case
    for x in stairs:
        if x.stair_role == stair.MAIN_INTERIOR_STAIR and not (
                x.floor_from and x.floor_to
                and x.floor_from != x.floor_to):
            bad.append(f"{x.physical_stair_id} is MAIN and carries no "
                       "storey")
        if x.stair_role in (stair.SERVICE_STAIR, stair.LANDSCAPE_STEPS):
            bad.append(f"{x.physical_stair_id} claims {x.stair_role} with "
                       "no rule or label saying so")
    for a in assemblies:
        for x in a.landings:
            if x.role not in stair.BETWEEN_FLIGHT_ROLES:
                bad.append(f"{x.landing_id} has no piece role")
            if x.is_stair_landing and not x.touches_flight_ends:
                bad.append(f"{x.landing_id} is a landing at the end of "
                           "no flight")

    e = case.expect
    if e.get("widest_is_not_main"):
        widest = max(stairs, key=lambda x: x.width_m, default=None)
        if widest is not None and widest.stair_role == \
                stair.MAIN_INTERIOR_STAIR and not (
                    widest.floor_from and widest.floor_to
                    and widest.floor_from != widest.floor_to):
            bad.append("the widest run was called the main stair")
    if e.get("a_stair_on_two_floors_exists") and not any(
            x.floor_from and x.floor_to and x.floor_from != x.floor_to
            for x in stairs):
        bad.append("no staircase was reconciled across two floors")
    if "stair_landings_at_least" in e:
        got = sum(1 for x in pieces if x.is_stair_landing)
        if got < e["stair_landings_at_least"]:
            bad.append(f"{got} stair landings, expected at least "
                       f"{e['stair_landings_at_least']}")
    if "landing_m2_at_most" in e and \
            obs["landing_m2"] > e["landing_m2_at_most"]:
        bad.append(f"LANDING_M2 {obs['landing_m2']}, expected at most "
                   f"{round(e['landing_m2_at_most'], 4)}")
    if "landing_m2" in e and abs(obs["landing_m2"] - e["landing_m2"]) \
            > 0.01:
        bad.append(f"LANDING_M2 {obs['landing_m2']}, expected "
                   f"{round(e['landing_m2'], 4)}")
    if e.get("no_piece_larger_than_the_flights_is_a_landing"):
        for a in assemblies:
            width = max((f.width_mm for f in a.flights), default=0.0)
            for x in a.landings:
                if x.is_stair_landing and x.length_mm > \
                        width * stair.LANDING_MAX_WIDTHS + 1.0:
                    bad.append(f"{x.landing_id} is a landing and is "
                               "larger than the flights it joins")
    return Result(case.name, case.what_it_tests, case.kind, not bad, bad,
                  obs)


CHECKS = {
    fixtures.LINEAGE: _check_lineage,
    fixtures.RELEASE: _check_release,
    fixtures.CONSISTENCY: _check_consistency,
    fixtures.STAIR: _check_stair,
}


def check(case) -> Result:
    return CHECKS[case.kind](case)


def report() -> dict:
    results = [check(c) for c in fixtures.cases()]
    out = {
        "round": "ROUND_6E",
        "cases": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [r.record() for r in results],
        "ROUND_6E_FIXTURE_HASH": fixtures.fixture_hash(),
    }
    out["ROUND_6E_SYNTHETIC_HASH"] = hashlib.sha256(
        "|".join([out["ROUND_6E_FIXTURE_HASH"]]
                 + [f"{r.name}:{r.passed}" for r in results]
                 ).encode("utf-8")).hexdigest()[:24]
    return out


def assert_frozen() -> dict:
    rep = report()
    if rep["failed"]:
        names = [c["case"] for c in rep["results"] if not c["passed"]]
        raise AssertionError(
            f"round-6E requirements broken on {rep['failed']} case(s): "
            f"{names}")
    return rep
