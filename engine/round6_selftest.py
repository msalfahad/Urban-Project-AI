"""Run the round-6 cases. Geometry now; the trade cases wait, and say so.

A case that is not yet implementable is reported NOT_YET_IMPLEMENTED with
its expectation printed. It never counts as a pass, because a suite that
quietly passes what it cannot test is worse than no suite.

Rounds 2 to 5 run beside these and must still hold. Their HASHES may
diverge — round 6 edits `physical_wall`, and `freeze_manifest` predicts
exactly which replays that moves — but a PASS is the score and a pass may
not move.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import partition_continuity as pcont
from engine import physical_wall as pwall
from engine import round6_fixtures as fixtures
from engine import semantic_seed as seeds_mod

NOT_YET = "NOT_YET_IMPLEMENTED"


@dataclass
class Result:
    name: str
    what_it_tests: str
    stage: str
    passed: bool
    failures: list = field(default_factory=list)
    observed: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)

    def record(self) -> dict:
        return {"case": self.name, "tests": self.what_it_tests,
                "stage": self.stage, "passed": self.passed,
                "failures": list(self.failures),
                "observed": dict(self.observed),
                "awaiting_implementation": dict(self.pending)}


def _roles(rep):
    """The space-role report, or None while it does not exist yet."""
    return getattr(rep, "space_roles", None)


def _overlapping_shared_lines(rep) -> list:
    """Pairs of walls that share a face line over the SAME stretch of it.

    §1's rule, stated as a test: one source line may not represent two
    physical wall faces unless the walls occupy disjoint stretches of it.
    """
    by_line = {}
    for wr in rep.walls:
        for w in wr.walls:
            # The stretch this wall USES of each line — not the whole line.
            # One drawn line can legitimately be the face of two walls end
            # to end, and its extent covers both of them.
            lo, hi = (w.overlap_mm if getattr(w, "overlap_mm", None)
                      else w.observed_extent)
            for f in (w.face_a_mm, w.face_b_mm):
                by_line.setdefault((w.region_id, w.axis, round(f, 1)),
                                   []).append((lo, hi, w.wall_id))
    bad = []
    for key, rows in by_line.items():
        rows.sort()
        for i, (lo, hi, wid) in enumerate(rows):
            for lo2, hi2, wid2 in rows[i + 1:]:
                if min(hi, hi2) - max(lo, lo2) > pwall.JOIN_MM:
                    bad.append((key, wid, wid2))
    return bad


def _unsupported_recovering_bands(rep) -> list:
    """Bands that produced recovered geometry on nothing but collinearity.

    This is the round-5 pathology in one line: a band paired out of two
    unrelated parallel lines has an undrawn "second face" everywhere, and
    recovering it draws a partition nobody drew.
    """
    evidence = {}
    for wr in rep.walls:
        for w in wr.walls:
            evidence[w.wall_id] = getattr(w, "evidence", ())
    bad = []
    for c in rep.continuity:
        for s in c.spans:
            if not s.may_subdivide:
                continue
            ev = evidence.get(s.wall_id)
            if ev is None:
                bad.append((s.wall_id, "NO_PAIRING_EVIDENCE_RECORDED"))
            elif not ev:
                bad.append((s.wall_id, "PAIRED_ON_NOTHING"))
    return bad


def check(case) -> Result:
    nd = adapter.normalize(case.decode, source_file=case.name,
                           source_hash="FIXTURE")
    prof = cprofile.build(nd)
    sem = seeds_mod.classify(nd.texts)
    rep = measure.measure(nd, prof, semantic=sem)
    roles = _roles(rep)

    bands = sum(len(wr.walls) for wr in rep.walls)
    obs = {
        "physical_spaces": len(rep.rows),
        "wall_bands": bands,
        "recovered_spans": sum(1 for c in rep.continuity
                               for s in c.spans if s.may_subdivide),
        "functional_zone_groups": sum(1 for r in rep.rows
                                      if len(r.zones) > 1),
        "areas_m2": sorted(round(r.enclosure.area_m2, 3) for r in rep.rows
                           if r.enclosure and r.enclosure.area_m2),
    }
    if roles is not None:
        obs["space_roles"] = dict(Counter(v.role for v in roles.verdicts))
        obs["observed_thickness_modes"] = list(
            getattr(roles, "thickness_modes", ()) or ())
    bad, pending = [], {}
    e = case.expect

    if case.stage == fixtures.TRADE:
        return Result(case.name, case.what_it_tests, case.stage, False,
                      [NOT_YET], obs, dict(case.expect_trade))

    # ---------------- universal, every geometry case --------------------
    shared = _overlapping_shared_lines(rep)
    obs["lines_serving_overlapping_walls"] = len(shared)
    if shared:
        bad.append(f"{len(shared)} wall pair(s) share a face line over the "
                   f"same stretch, e.g. {shared[0][1]} and {shared[0][2]}")

    unsupported = _unsupported_recovering_bands(rep)
    obs["unsupported_recovering_bands"] = len(unsupported)
    if unsupported:
        bad.append(f"{len(unsupported)} recovered span(s) came from a band "
                   f"with no pairing evidence ({unsupported[0][1]})")

    if roles is None:
        bad.append("no space-role classifier: the engine still has no way "
                   "to say a space is interior, exterior, a shaft or "
                   "simply unclassified")
    else:
        for v in roles.verdicts:
            if v.role in (roles.VOID_OR_SHAFT, roles.SHAFT) and \
                    not v.evidence:
                bad.append(f"{v.space_id} was called {v.role} with no "
                           "evidence")

    # ---------------------------- per case -------------------------------
    interior = []
    if roles is not None:
        interior = [v for v in roles.verdicts if v.is_interior]
        obs["interior_spaces"] = len(interior)

    if "min_interior_spaces" in e:
        if roles is None or len(interior) < e["min_interior_spaces"]:
            bad.append(f"expected at least {e['min_interior_spaces']} "
                       f"interior spaces, got "
                       f"{len(interior) if roles else 'no classifier'}")
    if "max_interior_spaces" in e:
        if roles is not None and len(interior) > e["max_interior_spaces"]:
            bad.append(f"expected at most {e['max_interior_spaces']} "
                       f"interior spaces, got {len(interior)}")
    if "functional_zones" in e:
        best = max((len(r.zones) for r in rep.rows), default=0)
        obs["largest_zone_group"] = best
        if best < e["functional_zones"]:
            bad.append(f"expected a face carrying {e['functional_zones']} "
                       f"functional zones, largest was {best}")
    if "wall_bands_at_most" in e and bands > e["wall_bands_at_most"]:
        bad.append(f"expected at most {e['wall_bands_at_most']} wall bands, "
                   f"got {bands}")
    if "shared_line_wall_count" in e:
        counts = Counter()
        for wr in rep.walls:
            for w in wr.walls:
                for f in (w.face_a_mm, w.face_b_mm):
                    counts[(w.axis, round(f, 1))] += 1
        best = max(counts.values(), default=0)
        obs["most_walls_on_one_line"] = best
        if best != e["shared_line_wall_count"]:
            bad.append(f"expected one line to serve exactly "
                       f"{e['shared_line_wall_count']} walls, the busiest "
                       f"served {best}")
    if "an_l_shaped_face_exists" in e:
        ok = any(r.enclosure and r.enclosure.polygon_wkt
                 and len(r.enclosure.polygon_wkt.split(",")) > 5
                 and _is_l(r.enclosure.polygon_wkt) for r in rep.rows)
        obs["l_shaped_face"] = ok
        if not ok:
            bad.append("no L-shaped face was measured")
    if "observed_thickness_mode" in e:
        modes = obs.get("observed_thickness_modes") or []
        if e["observed_thickness_mode"] not in [round(m, 1) for m in modes]:
            bad.append(f"expected {e['observed_thickness_mode']} mm among "
                       f"the observed thickness modes, got {modes}")
    if "unnamed_interior_space_role" in e:
        want = e["unnamed_interior_space_role"]
        got = ([v.role for v in roles.verdicts if not v.has_identity]
               if roles else [])
        obs["unnamed_space_roles"] = sorted(set(got))
        if want not in got:
            bad.append(f"an interior space nobody named should be {want}, "
                       f"got {sorted(set(got)) or 'no classifier'}")
    if e.get("a_shaft_is_identified"):
        got = [v for v in (roles.verdicts if roles else [])
               if v.role == getattr(roles, "SHAFT", "SHAFT")]
        if not got:
            bad.append("no shaft was identified where one is labelled, "
                       "enclosed, doorless and repeated across plans")
    if e.get("a_vertical_penetration_is_identified"):
        got = [v for v in (roles.verdicts if roles else [])
               if v.role in (getattr(roles, "VOID_OR_SHAFT",
                                     "VOID_OR_SHAFT_ON_EVIDENCE"),
                             getattr(roles, "SHAFT", "SHAFT"))]
        if not got:
            bad.append("an enclosed doorless space repeated across plans "
                       "was not identified as a vertical penetration")
    if e.get("an_exterior_space_is_identified"):
        got = [v for v in (roles.verdicts if roles else []) if v.is_exterior]
        obs["exterior_spaces"] = len(got)
        if not got:
            bad.append("no exterior space was identified")
    if e.get("no_exterior_space_called_interior") and roles is not None:
        for v in roles.verdicts:
            if v.is_interior and "GARDEN" in " ".join(v.evidence).upper():
                bad.append(f"{v.space_id} carries garden evidence and was "
                           "called interior")
    if e.get("a_space_with_no_opening_is_flagged"):
        flagged = [v for v in (roles.verdicts if roles else [])
                   if getattr(v, "no_opening_on_any_boundary", False)]
        obs["spaces_with_no_opening"] = len(flagged)
        if not flagged:
            bad.append("a fully enclosed space with no opening anywhere was "
                       "not flagged")

    return Result(case.name, case.what_it_tests, case.stage, not bad, bad,
                  obs, pending)


def _is_l(wkt: str) -> bool:
    from shapely.wkt import loads

    try:
        poly = loads(wkt)
    except Exception:       # noqa: BLE001
        return False
    if len(poly.exterior.coords) - 1 <= 4:
        return False
    x0, y0, x1, y1 = poly.bounds
    return poly.area < (x1 - x0) * (y1 - y0) * 0.95


def run() -> list:
    return [check(c) for c in fixtures.cases()]


def report(results=None) -> dict:
    res = list(results) if results is not None else run()
    geo = [r for r in res if r.stage == fixtures.GEOMETRY]
    trade = [r for r in res if r.stage == fixtures.TRADE]
    failed = [r for r in geo if not r.passed]
    return {
        "ROUND_6_SYNTHETIC_HASH": freeze_hash(),
        "cases": len(res),
        "geometry_cases": len(geo),
        "geometry_passed": sum(1 for r in geo if r.passed),
        "geometry_failed": len(failed),
        "trade_cases_awaiting_implementation": len(trade),
        "geometry_requirements_held": not failed,
        "results": [r.record() for r in res],
        "success_criterion": (
            "one line never serves two overlapping walls, nothing is called "
            "a void without evidence, and no recovered partition comes from "
            "a band paired on nothing. There is no target room count"),
    }


def freeze_hash() -> str:
    parts = [fixtures.freeze_hash(), pwall.wall_band_hash(),
             pcont.continuity_hash()]
    try:
        from engine import cad_space_role

        parts.append(cad_space_role.classifier_hash())
    except Exception:       # noqa: BLE001 - not implemented yet
        parts.append("SPACE_ROLE_NOT_IMPLEMENTED")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def assert_geometry_frozen() -> dict:
    rep = report()
    if rep["geometry_failed"]:
        names = [c["case"] for c in rep["results"]
                 if c["stage"] == fixtures.GEOMETRY and not c["passed"]]
        raise AssertionError(
            f"round-6 geometry requirements broken on "
            f"{rep['geometry_failed']} case(s): {names}")
    return rep
