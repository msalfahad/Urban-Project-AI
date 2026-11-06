"""T-549: WIRING MANIFEST V4 (research/agents_t549/WIRING_MANIFEST_V4.json) is recomputed from the merged piece outputs
(T-533, T-534, T-537 r2, T-539, T-541, T-542, T-543, T-548) on the pinned V3 and must equal the committed file; hand
checks of every figure that moves an expectation; R-T549-1 coverage on a synthetic repository (normal + adverse: a
merged piece missing from the manifest is refused, a later merge is not); 0 candidate lines moved; held never 0."""

import copy
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t549"))
import manifest_v4 as M          # noqa: E402

A = pytest.approx


@pytest.fixture(scope="module")
def man():
    return M.build()


@pytest.fixture(scope="module")
def idx():
    return M.M1.line_index()


def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_merge_since_v3_is_covered_and_merged(man):
    M.M2.check_sources(M.PIECES)
    assert man["coverage"] == {"range": ["9c160d22", "3f3b580c"], "first_parent_merges": 8,
                               "covered": ["T-533", "T-534", "T-537", "T-539", "T-541", "T-542", "T-543", "T-548"]}
    assert set(M.NO_WIRING) <= set(M.NEW_PIECES)
    assert man["candidate_lines_moved_v3_to_v4"] == 0 and man["released_quantities_changed"] == 0
    assert man["candidate_files_touched"] == 0


def test_edited_v3_refused(monkeypatch):
    monkeypatch.setattr(M, "V3_PIN", "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v3_manifest()


# ---- R-T549-1 on a synthetic repository (not Alsenan) ---------------------------------------------------------------
def _git(repo, *a):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env).stdout.decode().strip()


def _piece(repo, task, msg=None):
    _git(repo, "checkout", "-q", "-b", f"agents/task-{task}")
    (repo / task).write_text(task + "\n")
    _git(repo, "add", task)
    _git(repo, "commit", "-q", "-m", f"{task} work")
    _git(repo, "checkout", "-q", "work")
    args = ["merge", "-q", "--no-ff"] + (["-m", msg] if msg else ["--no-edit"]) + [f"agents/task-{task}"]
    _git(repo, *args)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture()
def syn(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    (repo / "a").write_text("0\n")
    _git(repo, "add", "a")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    m1 = _piece(repo, "T-901", "Merge agents/task-T-901: first piece (verified)")
    m2 = _piece(repo, "T-902")                          # git's default subject: Merge branch 'agents/task-T-902'
    head = m2
    later = _piece(repo, "T-903", "Merge agents/task-T-903: merged after the manifest base")
    return {"repo": repo, "base": base, "head": head, "m": {"T-901": m1, "T-902": m2}, "later": later}


def test_synthetic_coverage_complete(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    c = M.check_coverage(p, syn["base"], syn["head"], syn["repo"])
    assert c["covered"] == ["T-901", "T-902"] and c["first_parent_merges"] == 2


def test_adverse_merged_piece_missing_from_manifest_refused(syn):
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-902"):
        M.check_coverage({"T-901": {"merge": syn["m"]["T-901"][:8]}}, syn["base"], syn["head"], syn["repo"])


def test_adverse_out_of_range_or_wrong_commit_refused(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    with pytest.raises(M.ManifestError, match="OUT_OF_RANGE"):
        M.check_coverage(dict(p, **{"T-903": {"merge": syn["later"][:8]}}), syn["base"], syn["head"], syn["repo"])
    bad = copy.deepcopy(p)
    bad["T-901"]["merge"] = syn["m"]["T-902"][:8]
    with pytest.raises(M.ManifestError, match="OUT_OF_RANGE"):
        M.check_coverage(bad, syn["base"], syn["head"], syn["repo"])


def test_later_merge_does_not_turn_the_pinned_manifest_red(syn):
    # T-903 merged after the pinned head: it belongs to the next manifest (the F-C-T536-1 lesson)
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    assert M.check_coverage(p, syn["base"], syn["head"], syn["repo"])["covered"] == ["T-901", "T-902"]
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-903"):
        M.check_coverage(p, syn["base"], syn["later"], syn["repo"])


# ---- T-534 / T-542 stair bed ----------------------------------------------------------------------------------------
def test_stair_bed_resolves_to_at_least(man, idx):
    s = man["stair_bed"]
    assert s["before_v3"]["state"] == "HELD_BY_NAME" and s["after"] == {"state": "AT_LEAST", "value_m2": A(35.4313),
                                                                       "source": "T-534"}
    assert len(s["lines"]) == 11 and sum(idx[k]["measured_net"] for k in s["lines"]) == A(35.4313, abs=1e-9)
    assert s["held_or_excluded_lines"]["HELD"] == 20 and s["held_or_excluded_lines"]["EXCLUDED"] == 3
    v = s["v7_on_it"]
    assert v["mortar_m3"] == A(35.4313 * 0.03, abs=1e-6) and v["cement_bags_installed"] == A(1.062939 * 9.576, abs=1e-6)
    assert v["sand_m3_installed"] == A(1.062939 * 0.9975, abs=1e-5) and "HELD" in v["procurement"]


def test_stair_beyond_by_hand(man):
    b = man["stair_beyond"]
    risers = 1.571667 + 1.886 + 1.9044 + 1.9044 + 0.667 + 1.653536 + 0.751607     # MS1-L .. RS-A (T-412 counts)
    landings = 1.4375 + 2.9325 + 4.865 + 1.3525                                     # MS1-LD, MS2-LD, 2F-ARR, RS-LD
    assert b["risers"] == 7 and b["landings"] == 4 and b["area_m2"] == A(risers + landings, abs=1e-6) == A(20.92611)
    p = {(x["key"], x["surface"]): x for x in b["parts"]}
    ms1 = p[("MS1-L", "RISER")]
    assert ms1["v7_mortar_m3"] == A(1.571667 * 0.03, abs=1e-6) and ms1["v7_cement_bags"] == A(0.04715 * 9.576, abs=1e-6)
    assert all(x["before"]["value"] is None for x in b["parts"])
    assert b["tolerance_not_wired"]["difference_m2"] == A(0.0012)


def test_adverse_beyond_part_on_a_released_line_refused(idx):
    bad = copy.deepcopy(idx)
    bad["L-ecc450d6cc865617f8f6"]["class"] = "RELEASED"          # the MS1-L riser line released: already on the wire
    with pytest.raises(M.ManifestError, match="not HELD"):
        M.stair_beyond(bad)


def test_floor_bed_mix_by_hand(man):
    f = man["floor_bed_mix"]
    hall, lobby = (r for r in sorted(f["rows"], key=lambda r: r["key"]))
    assert hall["key"] == "GF-HALL" and hall["if_marble_landing_1_3"]["sand_m3"] == A(4.805 * 0.03 * 0.9975, abs=1e-6)
    assert lobby["if_marble_landing_1_3"]["cement_bags"] == A(1.3225 * 0.03 * 9.576, abs=1e-6)
    assert f["sand_below_1_4_low_m3"] == A(0.158565 + 0.043643 - (4.805 + 1.3225) * 0.03 * 0.9975, abs=1e-6)
    assert all(r["state"].startswith("STALE_ON_MIX") for r in f["rows"])


# ---- T-537 r2 host faces ---------------------------------------------------------------------------------------------
def test_host_faces_by_hand(man):
    h = {x["t498_stage_line"]: x for x in man["host_faces"]["hosts"]}
    gf, f1 = h["L-d14c6c9b738045c797ec"], h["L-4b9a29d424ea40e0af8a"]
    # GF: net 5.59, face 0.20 x [1.40, 1.899] = [0.28, 0.3798]; white 0.20 glue 4.5 kg / m2
    assert gf["v4_expected_after"]["glue_kg"]["range"] == [A((5.59 - 0.3798) * 4.5), A((5.59 - 0.28) * 4.5)]
    assert gf["v2_expected_after"]["kg_range"] == [A(23.769), A(23.895)]
    g1 = f1["v4_expected_after"]["glue_kg"]
    assert g1["state"] == "HELD" and g1["value"] is None and g1["at_most_beside"] == A(100.35754 * 4.5, abs=1e-6)
    gg = man["host_faces"]["glue_group"]
    assert gg["v2_expected_after"]["at_least"] == [A(35.387755), A(36.226627)]
    assert gg["v4_expected_after"] == {"status": "HELD", "at_least": [A(17.643906), A(18.16227)],
                                       "to_buy_at_least": [18, 19]}
    assert len(man["host_faces"]["bindings_stale"]) == 4


# ---- T-533 0.15 m module ---------------------------------------------------------------------------------------------
def test_block_module_hosts(man, idx):
    b = man["block_module"]
    assert b["walls"] == 15 and len(b["host_lines"]) == 6 and b["contract_m2"] == A(178.571, abs=1e-6)
    for h in b["host_lines"]:
        assert idx[h["host_line"]]["class"] == "RELEASED" and "t=0.15" in h["element_id"]
    assert b["candidate_lines_moved"] == 0 and b["result"] == "HELD"


def test_adverse_015_wall_with_a_figure_refused(monkeypatch, tmp_path, idx):
    rows = list(csv.DictReader(open(M.T533_WALLS, encoding="utf-8")))
    rows[0]["units_nr"] = str(12.5 * float(rows[0]["contract_m2"]))      # the 0.20 m module borrowed
    p = tmp_path / "w.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    monkeypatch.setattr(M, "T533_WALLS", p)
    with pytest.raises(M.ManifestError, match="figure"):
        M.block_module(idx, M.M3.v2_manifest())


# fixture (not Alsenan): a staged villa with one 0.15 m black host H15 and one 0.20 m host H20
STAGE = [{"line_id": "S1", "source_line_id": "H15", "item_code": "MAS.UNITS.BLACK", "state": "HELD", "value": None},
         {"line_id": "S2", "source_line_id": "H15", "item_code": "MAS.MORTAR.BLACK", "state": "BLOCKED_RFI",
          "value": None},
         {"line_id": "S3", "source_line_id": "H20", "item_code": "MAS.UNITS.BLACK", "state": "SOURCE_DERIVED",
          "value": 125.0},
         {"line_id": "S4", "source_line_id": "H15", "item_code": "MAS.GLUE.AAC", "state": "BLOCKED_RFI", "value": None}]


def test_stage_check_fixture():
    assert M.stage_check(STAGE, {"H15"}) == ["S1", "S2"]        # the 0.20 m host keeps its figure; glue not a black item


def test_adverse_stage_figure_on_015_host_refused():
    bad = copy.deepcopy(STAGE)
    bad[0].update(state="SOURCE_DERIVED", value=12.5 * 10.0)     # 10 m2 x 12.5 / m2 on a 0.15 m host
    with pytest.raises(M.ManifestError, match="R-T533-1"):
        M.stage_check(bad, {"H15"})


# ---- T-539 accessories ------------------------------------------------------------------------------------------------
def test_accessories_reconcile_v3(man):
    a = man["accessories"]
    assert a["v3"]["ties_nr"] == 30.0 and a["v4_end_ties"]["measured_nr"] == 18
    assert a["v4_end_ties"]["measured_nr"] + a["v4_end_ties"]["held_015_s_a_beside_nr"] == 30     # 3 ends x 6 + 12
    assert a["v4_end_ties"]["held_015_by_name"] == ["1F-W23", "2F-W08"]
    assert a["v4_end_vjoint_mesh"]["owner_ml"] == 40.9 and a["v4_end_vjoint_mesh"]["residual_ml"] == A(0.10)
    assert a["v4_end_strip_ml"] == 0.0 and a["candidate_lines_with_these_codes"] == []
    assert [p["code"] for p in a["proposed_lines"]] == ["MAS.TIE.SHARMAT", "MAS.MESH.BED_JOINT", "MAS.MESH.JOINT"]


def test_adverse_existing_accessory_line_refused(idx):
    bad = copy.deepcopy(idx)
    bad["L-fake"] = {"item_code": "MAS.TIE.SHARMAT", "class": "RELEASED", "measured_net": 6.0, "unit": "pcs",
                     "element_id": "X"}
    with pytest.raises(M.ManifestError, match="double count"):
        M.accessories(bad, M.v3_manifest())


# ---- T-541 / T-548 / T-543 consistency --------------------------------------------------------------------------------
def test_roof_rows_hold_only_after_f_steps(man):
    r = man["roof_consistency"]
    assert r["membrane"]["t541_engine"] == A(32.721 + 55.559 + 115.832 + 4.906867 + 0.639573, abs=1e-6)
    assert r["membrane"]["candidate_v3_0_58_released"] == A(32.721 + 55.559 + 115.832 + 4.906867, abs=1e-6)
    assert r["upturn"]["difference"] == A(0.500002 + 0.551614, abs=1e-6)
    assert [x["line_id"] for x in r["membrane"]["lines_valued_only_after_wiring"]] == ["L-2361d6ec13c952bd2ae3"]
    assert set(r["t548_absent_lines"]["T-541/upturn"]) >= {"L-1954878bb02c91139e1b", "L-d7d1bf8c5991ccf69ea2"}


def test_adverse_roof_view_mismatch_refused(monkeypatch):
    v2 = copy.deepcopy(M.M3.v2_manifest())
    v2["stream_F"]["code_views"]["FIN.WP.ROOF"]["released_after"] = 209.0
    with pytest.raises(M.ManifestError, match="expected after"):
        M.roof_consistency(v2)


def test_blockwork_consistency(man, idx):
    b = man["blockwork_consistency"]
    assert b["engine_valued_m2"] == A(467.7925) and b["held_lines"] == 15 and b["gap_m2"] == A(1260.6895 - 467.7925)
    bad = copy.deepcopy(idx)
    bad["L-fake"] = {"item_code": "MAS.BLOCK", "class": "RELEASED", "measured_net": 1.0, "unit": "m2", "element_id": "X"}
    with pytest.raises(M.ManifestError, match="not the candidate"):
        M.blockwork_consistency(bad)


def test_held_never_zero(man):
    def walk(o):
        if isinstance(o, dict):
            if str(o.get("state", "")).startswith("HELD") or o.get("class") == "HELD":
                assert o.get("value") is None and o.get("value_m2") is None
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(man)
    assert json.loads(M.dumps(man))["v3_to_v4"][0]["v4"]["state"] == "AT_LEAST"
