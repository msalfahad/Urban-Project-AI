"""Phase 2B-8 acceptance: BOQ coverage of REVIEW spaces under ARCH_TAKEOFF_V2.7.1.

A space whose type is under review (UP-WET-002: WET_CLASSIFICATION_REVIEW, WC_CANDIDATE_REVIEW) is measured under
each plausible classification (WET_SCOPE: the owner wet scope UP-WET-001, as a W.C.; DRY_SCOPE: a lobby / wash area).
A quantity is released into the main BOQ only when it is identical under every plausible classification - same item,
same quantity, same state, same rule - AND its system does not depend on the classification (plaster: the substrate
behind wall porcelain is its own line, UP-FIN-PAINT-001, so plaster is never released while the wall finish over it
differs). Everything else is a CONDITIONAL scenario quantity, never added to the main BOQ. A space with no fixture
evidence (a plain unlabelled lobby) has no established set of plausible types: nothing is released.

The plan (p2b8_fixtures.wc_plan / tests/m9_p2b7): a W.C. 2.00 x 3.00 m (room word) and an unlabelled lobby
3.40 x 3.00 m = 10.20 m2 behind a 0.80 m door, with a 1.00 m external door. Truth: p2b8_fixtures.LOBBY_TRUTH, derived
by hand from the coordinates and the stated S2 heights."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b8_fixtures as F                                     # noqa: E402
import p2b8_run as R                                          # noqa: E402

T = F.LOBBY_TRUTH
TOL = 1e-6


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_review")


_cache = {}


def _run(work, kind, *, facts=True, method=R.V271, transform=None):
    key = (kind, facts, method, transform)
    if key not in _cache:
        src = F.wc_plan(work / f"WC_{kind}.dxf", kind)
        if transform:
            src = F.variant(src, work / f"WC_{kind}_{transform}.dxf", transform)
        tag = f"{kind}_{'A' if facts else 'U'}_{method[-5:]}_{transform or 'base'}".replace(".", "")
        _cache[key] = R.run(src, work / f"o_{tag}", roles=F.ROLES, facts=facts, method=method)
    return _cache[key]


def _space(out):
    sp = R.review_spaces(out)
    assert len(sp) == 1
    return sp[0]


def _delta(space, scenario, item, room_id=None):
    """the net change of one item under a scenario against the main BOQ (scenario quantity - main quantity)."""
    return round(sum((c["quantity"] or 0.0) - (c["main_quantity"] or 0.0) for c in space["conditional"][scenario]
                     if c["item_code"] == item and (room_id is None or c["room_id"] == room_id)), 6)


def _sq(space, scenario, item, room_id):
    got = [c for c in space["conditional"][scenario] if c["item_code"] == item and c["room_id"] == room_id]
    assert len(got) == 1, (item, scenario, got)
    return got[0]


# --------------------------------------------------------------------------- release of the invariant quantities

def test_basin_space_releases_its_ceiling_and_nothing_else(work):
    """the lobby stays REVIEW (no room type); its main-BOQ lines are its area (ARCH.SPACE 10.20 m2) and its ceiling
    10.20 m2 - identical as a W.C. and as a lobby - and no floor, wall, skirting or waterproofing line."""
    out = _run(work, "BASIN")
    lob = R.lobby(out)
    assert lob["class"] == "UNLABELLED" and not lob["codes"]
    assert lob["issue"].startswith("WET_CLASSIFICATION_REVIEW")
    mine = R.room_lines(out, lob["room_id"])
    assert sorted(ln["item_code"] for ln in mine) == ["ARCH.SPACE", "FIN.CEILING"]
    ceil = next(ln for ln in mine if ln["item_code"] == "FIN.CEILING")
    assert abs(ceil["measured_net"] - T["ceiling_m2"]) < TOL
    assert ceil["evidence_state"] == "PROVISIONAL"                  # as every ceiling (type not in a plan)
    assert "CLASSIFICATION_INVARIANT" in ceil["notes"]
    sp = _space(out)
    assert sp["room_id"] == lob["room_id"] and sp["issue_code"] == "WET_CLASSIFICATION_REVIEW"
    assert sorted(s["scenario"] for s in sp["plausible"]) == ["DRY_SCOPE", "WET_SCOPE"]
    assert [r["item_code"] for r in sp["released"]] == ["FIN.CEILING"]
    assert sp["released"][0]["line_id"] == ceil["line_id"]


def test_v2_7_is_unchanged(work):
    """ARCH_TAKEOFF_V2.7 keeps the lobby without a ceiling line (the behaviour V2.7.1 versions)."""
    out = _run(work, "BASIN", method=R.V27)
    lob = R.lobby(out)
    assert [ln["item_code"] for ln in R.room_lines(out, lob["room_id"])] == ["ARCH.SPACE"]
    assert not (Path(out) / "REVIEW_SPACES.json").exists()


def test_geometry_measured_with_confidence(work):
    """the geometry of the review space is reported whatever its type: area 10.20 m2, perimeter 12.80 m, wall run
    12.80 m, the two doors 0.80 + 1.00 m, ceiling plan 10.20 m2, no double height."""
    sp = _space(_run(work, "BASIN"))
    g = sp["geometry"]
    assert abs(g["area_m2"] - F.LOBBY["area_m2"]) < TOL
    assert abs(g["perimeter_lm"] - F.LOBBY["perimeter_lm"]) < TOL
    assert abs(g["wall_run_lm"] - F.LOBBY["perimeter_lm"]) < TOL
    assert sorted(round(o["width_m"], 4) for o in g["openings"]) == [0.8, 1.0]
    assert abs(g["ceiling_plan_m2"] - T["ceiling_m2"]) < TOL and g["double_height_m2"] == 0


# --------------------------------------------------------------------------- the conditional scenario quantities

def test_wet_scope_quantities(work):
    """as a W.C. (UP-WET-001): wet floor tile 10.20, wall tile 12.80 x 2.40 - 3.78 = 26.94, plaster 34.62, skirting
    11.00 (the stated tile height is below the full height, so the skirting stays), membrane floor 10.20, wall upturn
    11.00 x 0.20 = 2.20, marble at the external door 0.20; the doorway membrane gains only the external door's piece
    1.00 x 0.20 = 0.20 (the W.C. door's 0.16 m2 piece moves to the lobby, counted once)."""
    out = _run(work, "BASIN")
    sp, rid = _space(out), R.lobby(out)["room_id"]
    for item, want in (("FIN.FLOOR.WET_TILE", T["wet_floor_m2"]), ("FIN.WALL.TILE", T["wet_tile_m2"]),
                       ("FIN.PLASTER", T["plaster_m2"]), ("FIN.SKIRTING", T["skirting_lm"]),
                       ("FIN.WP.FLOOR", T["wet_wp_floor_m2"]), ("FIN.WP.WALL_UPTURN", T["wet_wall_upturn_m2"])):
        c = _sq(sp, "WET_SCOPE", item, rid)
        assert abs(c["quantity"] - want) < TOL, (item, c)
        assert c["main_quantity"] is None and c["change"] == "ADDED"
    assert abs(_delta(sp, "WET_SCOPE", "FIN.MARBLE.THRESHOLD") - T["wet_external_threshold_m2"]) < TOL
    assert abs(_delta(sp, "WET_SCOPE", "FIN.WP.DOORWAY") - T["wet_new_doorway_wp_m2"]) < TOL
    assert _delta(sp, "WET_SCOPE", "FIN.FLOOR.PORCELAIN") == 0


def test_dry_scope_quantities(work):
    """as a lobby / wash area: porcelain floor 10.20, plaster 34.62 and paint 34.62, skirting 11.00, the external
    doorway strip as floor porcelain 0.20; no wall tile and no waterproofing."""
    out = _run(work, "BASIN")
    sp, rid = _space(out), R.lobby(out)["room_id"]
    for item, want in (("FIN.FLOOR.PORCELAIN", T["dry_floor_m2"]), ("FIN.PLASTER", T["plaster_m2"]),
                       ("FIN.PAINT", T["dry_paint_m2"]), ("FIN.SKIRTING", T["skirting_lm"])):
        assert abs(_sq(sp, "DRY_SCOPE", item, rid)["quantity"] - want) < TOL, item
    assert abs(_delta(sp, "DRY_SCOPE", "FIN.FLOOR.PORCELAIN") - (T["dry_floor_m2"] + T["dry_external_strip_m2"])) \
        < TOL
    for item in ("FIN.WALL.TILE", "FIN.WP.FLOOR", "FIN.WP.WALL_UPTURN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.THRESHOLD"):
        assert _delta(sp, "DRY_SCOPE", item) == 0, item


def test_equal_quantities_are_not_released_when_the_system_or_rule_differs(work):
    """plaster is 34.62 m2 in both scenarios but its system depends on the wall finish over it (UP-FIN-PAINT-001:
    the substrate behind porcelain is its own line); skirting is 11.00 m in both but under different rules (UP-CER-004
    as a W.C., UP-CER-003 as a lobby): neither is released, and each says why."""
    sp = _space(_run(work, "BASIN"))
    why = {x["item_code"]: x["reason"] for x in sp["not_released"]}
    assert why["FIN.PLASTER"] == "SYSTEM_DEPENDS_ON_WALL_FINISH"
    assert why["FIN.SKIRTING"] == "RULE_DIFFERS"
    assert why["FIN.FLOOR.WET_TILE"] == "ONLY_IN_SOME_SCENARIOS"


def test_scenarios_are_never_added_to_the_main_boq(work):
    """the main BOQ is V2.7's plus the released ceiling, line for line; the release report's confirmed totals are the
    main BOQ's, and no conditional quantity is in them."""
    o27, o271 = _run(work, "BASIN", method=R.V27), _run(work, "BASIN")
    d = R.diff(o27, o271)
    lob_name = R.lobby(o271)["name_en"]
    assert set(d) == {("FIN.CEILING", lob_name)}, d
    assert abs(d[("FIN.CEILING", lob_name)][1][0] - T["ceiling_m2"]) < TOL
    rep = R.release_report(o271)
    conf = {}
    for x in rep["categories"]["CONFIRMED"]["lines"]:
        conf[(x["item_code"], x["unit"])] = conf.get((x["item_code"], x["unit"]), 0.0) + x["quantity"]
    main = {}
    for ln in R.lines(o271):
        if ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL") and ln["measured_net"] is not None:
            main[(ln["item_code"], ln["unit"])] = main.get((ln["item_code"], ln["unit"]), 0.0) + ln["measured_net"]
    assert conf.keys() == main.keys() and all(abs(conf[k] - main[k]) < TOL for k in main)
    assert "never" in rep and any("added" in s for s in rep["never"])
    sets = [s for s in rep["categories"]["CONDITIONAL"]["scenario_sets"] if s["kind"] == "REVIEW_CLASSIFICATION"]
    assert len(sets) == 1 and sorted(sets[0]["scenarios"]) == ["DRY_SCOPE", "WET_SCOPE"]
    assert sets[0]["mutually_exclusive"] is True


def test_every_line_is_reported_exactly_once(work):
    """CONFIRMED / HELD / EXCLUDED partition the main BOQ lines: each line id once; HELD lines carry a reason class;
    a range (BOUNDED_EXPOSURE) keeps its bounds."""
    out = _run(work, "BASIN")
    rep = R.release_report(out)
    seen = [x["line_id"] for c in ("CONFIRMED", "HELD", "EXCLUDED") for x in rep["categories"][c]["lines"]]
    ids = [ln["line_id"] for ln in R.lines(out)]
    assert sorted(seen) == sorted(ids) and len(set(seen)) == len(seen)
    assert rep["conservation"]["every_line_once"] is True
    for x in rep["categories"]["HELD"]["lines"]:
        assert x["reason_class"] in ("REQUIRES_DRAWING_EVIDENCE", "REQUIRES_OWNER_DECISION", "ENGINEERING_REVIEW",
                                     "CANNOT_BE_ESTABLISHED"), x
        if x["evidence_state"] == "BOUNDED_EXPOSURE":
            assert x["low"] is not None and x["high"] is not None
    for x in rep["categories"]["EXCLUDED"]["lines"]:
        assert x["reason"]


# --------------------------------------------------------------------------- Mode U, other review kinds, a plain space

def test_without_heights_the_ceiling_is_still_released(work):
    """Mode U (no facts): the ceiling needs no height - released 10.20; the wall finishes are blocked in both
    scenarios (no height); the skirting is 11.00 as a lobby and not applicable as a W.C. (UP-FIN-WALL-001: the wall
    porcelain of an owner wet area runs full height whatever its height value, UP-CER-004: no skirting): conditional."""
    out = _run(work, "BASIN", facts=False)
    sp, rid = _space(out), R.lobby(out)["room_id"]
    assert [r["item_code"] for r in sp["released"]] == ["FIN.CEILING"]
    assert abs(sp["released"][0]["quantity"] - T["ceiling_m2"]) < TOL
    assert abs(_sq(sp, "DRY_SCOPE", "FIN.SKIRTING", rid)["quantity"] - T["skirting_lm"]) < TOL
    wet_sk = _sq(sp, "WET_SCOPE", "FIN.SKIRTING", rid)
    assert wet_sk["quantity"] is None and wet_sk["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert _sq(sp, "WET_SCOPE", "FIN.PLASTER", rid)["evidence_state"] == "BLOCKED_RFI"


def test_wc_shape_alone_is_a_review_space_with_scenarios(work):
    """a water-closet shape alone (WC_CANDIDATE_REVIEW): the same two scenarios, the ceiling released."""
    out = _run(work, "ALONE")
    sp = _space(out)
    assert sp["issue_code"] == "WC_CANDIDATE_REVIEW"
    assert [r["item_code"] for r in sp["released"]] == ["FIN.CEILING"]
    assert abs(sp["released"][0]["quantity"] - T["ceiling_m2"]) < TOL


def test_a_plain_unlabelled_space_releases_nothing(work):
    """the lobby with nothing drawn inside: no fixture says what it is (a store, a duct, an open court ...) - no
    plausible set is established, nothing is released, its geometry is still reported."""
    out = _run(work, "PLAIN_LOBBY")
    lob = R.lobby(out)
    assert lob["issue"].startswith("UNLABELLED_SPACE")
    assert [ln["item_code"] for ln in R.room_lines(out, lob["room_id"])] == ["ARCH.SPACE"]
    sp = _space(out)
    assert sp["issue_code"] == "UNLABELLED_SPACE" and sp["plausible"] == [] and sp["released"] == []
    assert sp["plausible_basis"].startswith("NOT_ESTABLISHED")
    assert abs(sp["geometry"]["area_m2"] - F.LOBBY["area_m2"]) < TOL


# --------------------------------------------------------------------------- invariance and determinism

@pytest.mark.parametrize("transform", ["rot30", "mirror", "metres"])
def test_release_is_invariant(work, transform):
    """moved, turned 30 degrees, mirrored or drawn in metres: the same release and the same scenario totals."""
    base, moved = _space(_run(work, "BASIN")), _space(_run(work, "BASIN", transform=transform))
    assert [(r["item_code"], round(r["quantity"], 5)) for r in base["released"]] == \
        [(r["item_code"], round(r["quantity"], 5)) for r in moved["released"]]
    for sc in ("WET_SCOPE", "DRY_SCOPE"):
        for item in ("FIN.FLOOR.WET_TILE", "FIN.FLOOR.PORCELAIN", "FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE",
                     "FIN.SKIRTING", "FIN.WP.FLOOR", "FIN.WP.DOORWAY", "FIN.MARBLE.THRESHOLD"):
            assert abs(_delta(base, sc, item) - _delta(moved, sc, item)) < 1e-5, (sc, item)


def test_outputs_are_deterministic(work):
    a = _run(work, "BASIN")
    b = R.run(work / "WC_BASIN.dxf", work / "o_again", roles=F.ROLES, facts=True)
    for name in ("REVIEW_SPACES.json", "BOQ_RELEASE_REPORT.json"):
        ja, jb = R.load(a, name), R.load(b, name)
        ja.pop("run", None), jb.pop("run", None)
        assert ja == jb, name
