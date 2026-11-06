"""T-564: WIRING MANIFEST V7 (research/agents_t564/WIRING_MANIFEST_V7.json) is recomputed from the candidate line index
and the merged pieces (T-551, T-553, T-558, T-561, T-562, T-566) and must equal the committed file; the FLOOR-FINISH
COMPLETENESS CENSUS R-T564-1 finds the two T-553 defects by rule (fixture not Alsenan: 3 rooms -> 2 hits), never by
room id; a missing floor is never wired as 0; R-T549-1 coverage on a synthetic repository."""

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t564"))
import manifest_v7 as M          # noqa: E402
import floor_census as F         # noqa: E402

A = pytest.approx
DRESSING, KITCHEN_FLOOR = "1F-RFFE7AF", "L-83609efc5fdb5d38f059"


@pytest.fixture(scope="module")
def bs():
    return M.M5._t523()["bindings"]


@pytest.fixture(scope="module")
def man(bs):
    return M.build(bs=bs)


@pytest.fixture(scope="module")
def idx():
    return M.M1.line_index()


def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_merge_since_v6_is_covered(man):
    M.M2.check_sources(M.PIECES)
    assert man["coverage"] == {"range": ["431ac67f", "33a5833f"], "first_parent_merges": 6,
                               "covered": ["T-551", "T-553", "T-558", "T-561", "T-562", "T-566"]}
    assert set(M.NO_WIRING) | set(M.WIRING_SOURCES) == set(M.NEW_PIECES)
    assert man["candidate_lines_moved_v6_to_v7"] == 0 and man["candidate_files_touched"] == 0


def test_edited_v6_refused(monkeypatch):
    monkeypatch.setattr(M, "V6_PIN", "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v6_manifest()


def test_adverse_t553_as_no_wiring_refused(monkeypatch, bs):
    monkeypatch.setattr(M, "NO_WIRING", dict(M.NO_WIRING, **{"T-553": "moves nothing"}))
    with pytest.raises(M.ManifestError, match="disjoint"):
        M.build(bs=bs)


# ---- R-T549-1 on a synthetic repository (not Alsenan) ---------------------------------------------------------------
def _git(repo, *a):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env).stdout.decode().strip()


def _piece(repo, task, msg):
    _git(repo, "checkout", "-q", "-b", f"agents/task-{task}")
    (repo / task).write_text(task + "\n")
    _git(repo, "add", task)
    _git(repo, "commit", "-q", "-m", f"{task} work")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-ff", "-m", msg, f"agents/task-{task}")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def syn(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    (repo / "a").write_text("0\n")
    _git(repo, "add", "a")
    _git(repo, "commit", "-q", "-m", "base")
    v6 = _piece(repo, "T-930", "Merge agents/task-T-930: previous manifest (verified)")
    m = {"T-931": _piece(repo, "T-931", "Merge agents/task-T-931: first edge (verified)"),
         "T-932": _piece(repo, "T-932", "Merge agents/task-T-932: last edge (verified)")}
    return {"repo": repo, "base": v6, "head": m["T-932"], "m": m}


def test_synthetic_v7_range_complete_and_edge_left_out_refused(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    assert M.M4.check_coverage(p, syn["base"], syn["head"], syn["repo"])["covered"] == ["T-931", "T-932"]
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-932"):
        M.M4.check_coverage({"T-931": p["T-931"]}, syn["base"], syn["head"], syn["repo"])


# ---- census fixture (not Alsenan): 3 rooms, 2 hits -----------------------------------------------------------------
def _l(lid, code, el, cls="RELEASED", net=None, unit="m2", lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "element_id": el, "class": cls, "measured_net": net, "unit": unit,
            "held_low": lo, "held_high": hi, "binding": None, "unbound_records": []}


def _fixture(a="GF-R0000A1", b="GF-R0000B2", c="1F-R0000C3"):
    return [
        # room A 3.00 x 2.00: space, ceiling and skirting, NO floor line (the dressing defect class)
        _l("L-a1", "ARCH.SPACE", f"{a}:space", net=6.0), _l("L-a2", "FIN.CEILING", f"{a}:ceiling", net=6.0),
        _l("L-a3", "FIN.SKIRTING", f"{a}:skirting", net=9.1, unit="lm"),
        # room B 2.50 x 2.00 wet: WP + wet bed, finish coded dry porcelain (the kitchen defect class)
        _l("L-b1", "FIN.WP.FLOOR", f"{b}:wp_floor", net=5.0), _l("L-b2", "FIN.FLOOR.PORCELAIN", f"{b}:floor", net=5.0),
        _l("L-b3", "FIN.FLOOR.BED.WET", f"{b}:floor:bed", net=5.0),
        _l("L-b4", "FIN.FLOOR.BED.WET", f"{b}:floor:bed", cls="HELD", unit="m3", lo=0.2, hi=0.3),
        _l("L-b5", "FIN.CEILING", f"{b}:ceiling", net=5.0),
        # room C 4.00 x 4.00 dry, correct
        _l("L-c1", "FIN.FLOOR.PORCELAIN", f"{c}:floor", net=16.0), _l("L-c2", "FIN.FLOOR.BED.DRY", f"{c}:floor:bed",
                                                                         net=16.0),
        _l("L-c3", "FIN.FLOOR.BED.DRY", f"{c}:floor:bed", cls="HELD", unit="m3", lo=0.48, hi=0.64),
        _l("L-c4", "FIN.CEILING", f"{c}:ceiling", net=16.0), _l("L-c5", "FIN.SKIRTING", f"{c}:skirting", net=15.1,
                                                                 unit="lm"),
    ]


def test_fixture_three_rooms_two_hits():
    c = F.census(_fixture())
    assert [h["key"] for h in c["C1_missing_floor"]] == ["GF-R0000A1"]
    assert [h["line_id"] for h in c["C2_wet_bed_dry_finish"]] == ["L-b2"]
    assert c["C4_bed_pair"] == []
    k = F.classify(c, _fixture())
    a = k["C1"][0]["expected_after"]["add"]
    assert k["C1"][0]["verdict"] == "ENGINE_WRONG"
    assert [x["item_code"] for x in a] == ["FIN.FLOOR.FINISH_HELD", "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.DRY"]
    assert a[0]["value"] == 6.0 and a[2]["held_low"] == A(6.0 * 0.03) and a[2]["held_high"] == A(6.0 * 0.04)
    assert k["C2"][0]["expected_after"] == {"recode": ["L-b2", "FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"],
                                            "m2_change": 0.0}
    st = c["C3_wp_floor_cover"]["GF"]
    assert st["state"] == "RESIDUAL" and st["residual_m2"] == A(5.0)


def test_adverse_census_keyed_on_room_ids_refused():
    with pytest.raises(F.CensusError, match="KEYED_INPUT"):
        F.census(_fixture(), room_ids=["GF-R0000A1"])
    with pytest.raises(F.CensusError, match="KEYED_INPUT"):
        F.census(["GF-R0000A1", "GF-R0000B2"])


def test_hits_follow_the_rule_not_the_ids():
    c = F.census(_fixture(a="2F-R9F9F9F", b="1F-RABCDEF", c="GF-R123456"))
    assert [h["key"] for h in c["C1_missing_floor"]] == ["2F-R9F9F9F"]
    assert [h["line_id"] for h in c["C2_wet_bed_dry_finish"]] == ["L-b2"]


def test_adverse_missing_floor_wired_as_zero_refused():
    c = F.census(_fixture())
    k = F.classify(c, _fixture())
    row = copy.deepcopy(k["C1"][0])
    row["expected_after"]["add"][0]["value"] = 0.0
    with pytest.raises(F.CensusError, match="ZERO"):
        F.check_after(row)
    row["expected_after"]["add"][0]["value"] = None
    with pytest.raises(F.CensusError, match="ZERO"):
        F.check_after(row)
    lines = [dict(l, measured_net=0.0) if l["line_id"] == "L-a1" else l for l in _fixture()]
    with pytest.raises(F.CensusError, match="not positive"):
        F.classify(F.census(lines), lines)


def test_no_space_area_stays_held_never_zero():
    lines = [l for l in _fixture() if l["line_id"] != "L-a1"]
    k = F.classify(F.census(lines), lines)
    h = k["C1"][0]
    assert h["verdict"] == "HELD" and h["expected_after"]["add"][0]["value"] is None
    assert h["expected_after"]["floor_change_m2"] is None


def test_adverse_owner_on_another_storey_or_not_a_floor_refused():
    lines = _fixture() + [_l("L-m1", "FIN.MARBLE.LANDING", "1F-R0000D4:landings", cls="HELD", lo=0.0, hi=2.0)]
    with pytest.raises(F.CensusError, match="storey"):
        F.classify(F.census(lines), lines, [{"key": "GF-R0000A1", "owner_line": "L-m1", "source": "x"}])
    with pytest.raises(F.CensusError, match="floor-owning"):
        F.classify(F.census(lines), lines, [{"key": "GF-R0000A1", "owner_line": "L-a2", "source": "x"}])


def test_adverse_unscoped_ceiling_refused():
    with pytest.raises(F.CensusError, match="UNSCOPED"):
        F.census(_fixture() + [_l("L-x", "FIN.CEILING", "CANOPY:EAST", net=3.0)])


def test_reverse_wet_tile_on_dry_bed_found():
    lines = [dict(l, item_code="FIN.FLOOR.WET_TILE") if l["line_id"] == "L-c1" else l for l in _fixture()]
    hits = F.census(lines)["C2_wet_bed_dry_finish"]
    assert {(h["line_id"], h["expected_item_code"]) for h in hits} == {("L-b2", "FIN.FLOOR.WET_TILE"),
                                                                       ("L-c1", "FIN.FLOOR.PORCELAIN")}


# ---- the candidate (Alsenan) ---------------------------------------------------------------------------------------
def test_candidate_hits_found_by_rule(man):
    fc = man["floor_census"]
    assert [h["key"] for h in fc["before"]["C1_missing_floor"]] == [DRESSING, "2F-ST-ARRIVAL"]
    assert [h["line_id"] for h in fc["before"]["C2_wet_bed_dry_finish"]] == [KITCHEN_FLOOR]
    assert fc["before"]["C4_bed_pair"] == []
    v = {h["key"]: h["verdict"] for h in fc["classified"]["C1"]}
    assert v == {DRESSING: "ENGINE_WRONG", "2F-ST-ARRIVAL": "ENGINE_RIGHT"}
    assert fc["after_hits"]["C1"] == ["2F-ST-ARRIVAL"] and fc["after_hits"]["C2"] == 0


def test_dressing_by_hand(man):
    a = man["fix_rows"]["rows"][0]["expected_after"]["add"]
    assert a[0]["value"] == A(1.65 * 1.80) == A(2.970) and a[0]["item_code"] == "FIN.FLOOR.FINISH_HELD"
    assert a[2]["held_low"] == A(2.97 * 0.03) and a[2]["held_high"] == A(2.97 * 0.04)


def test_kitchen_recode_and_class_split(man):
    r = man["fix_rows"]["rows"][1]
    assert r["before"]["item_code"] == "FIN.FLOOR.PORCELAIN" and r["expected_after"]["item_code"] == \
        "FIN.FLOOR.WET_TILE" and r["expected_after"]["m2_change"] == 0.0
    t = man["fix_rows"]["t553_restated"]
    assert t["total_before_m2"] == "387.094050" and t["total_after_m2"] == "390.064050"
    assert t["after"] == {"DRY": "295.390972", "WET": "85.575578", "FINISH_HELD": "9.0975"}
    assert t["gap_after_pct"] == "-4.76"


def test_wp_cover_closes_after_recode(man):
    e = man["floor_census"]["c3_explained"]["GF"]
    assert e["residual_before_m2"] == A(9.630133) and e["residual_after_m2"] == A(0.000132)
    assert e["state_after"] == "COVERED"


def test_tile_bindings_code_only_and_bound_rule(man):
    tb = man["tile_bindings"]
    assert tb["reproduced_on"] > 0
    ch = [r["change"] for r in tb["rows"]]
    assert ch == ["CODE_ONLY", "CODE_ONLY", "NEW_HELD_BLANK", "NEW_HELD_BLANK"]
    adh = next(r for r in tb["rows"] if r["kind"] == "adhesive_bags_20kg")
    assert adh["before"]["bound"] == adh["expected_after"]["bound"] == [A(9.630001 / 5), A(9.630001 / 3)]
    s = tb["adhesive_bound_by_code"]
    tot_b = [s["FIN.FLOOR.PORCELAIN"]["before"][i] + s["FIN.FLOOR.WET_TILE"]["before"][i] for i in (0, 1)]
    tot_a = [s["FIN.FLOOR.PORCELAIN"]["after"][i] + s["FIN.FLOOR.WET_TILE"]["after"][i] for i in (0, 1)]
    assert tot_a == A(tot_b)


def test_return_paint_row(man):
    rp = man["return_paint"]
    assert rp["valued_plaster_returns_m2"] == A(23.07) and rp["fin_paint_released_after_m2"] == A(217.2081)
    assert all(r["expected_after"]["class"] == "HELD" and r["expected_after"]["value"] is None for r in rp["rows"])


def test_held_never_zero(man):
    for h in man["floor_census"]["classified"]["C1"]:
        F.check_after(h)
    for r in man["return_paint"]["rows"]:
        assert r["expected_after"]["value"] is None


def test_adverse_census_given_candidate_ids_refused(idx):
    with pytest.raises(F.CensusError, match="KEYED_INPUT"):
        F.census(list(idx.values()), known=[DRESSING])
