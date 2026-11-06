"""T-555: WIRING MANIFEST V5 (research/agents_t555/WIRING_MANIFEST_V5.json) is recomputed from the merged piece outputs
(T-544, T-545, T-546, T-547, T-549, T-552, T-554) on the pinned V4 and must equal the committed file; hand checks of
every figure that moves an expectation; R-T549-1 coverage on a synthetic repository (normal + adverse); 0 candidate
lines moved; held never 0."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t555"))
import manifest_v5 as M          # noqa: E402

A = pytest.approx
H1F, HGF2, H1F2, H2F = ("L-2fdc0f971a94348ec855", "L-541cf7210e52db0498bb", "L-b7b4d784fbe7fdbebe84",
                        "L-bbb82de298fecbafa11d")


@pytest.fixture(scope="module")
def t544():
    return M._load(M.T544_APPLY, "t544_for_test_t555").build_all()


@pytest.fixture(scope="module")
def man(t544):
    return M.build(t544=t544)


@pytest.fixture(scope="module")
def idx():
    return M.M1.line_index()


def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_merge_since_v4_is_covered(man):
    M.M2.check_sources(M.PIECES)
    assert man["coverage"] == {"range": ["3f3b580c", "47d74505"], "first_parent_merges": 7,
                               "covered": ["T-544", "T-545", "T-546", "T-547", "T-549", "T-552", "T-554"]}
    assert set(M.NO_WIRING) <= set(M.NEW_PIECES) and "T-544" not in M.NO_WIRING and "T-552" not in M.NO_WIRING
    assert man["candidate_lines_moved_v4_to_v5"] == 0 and man["released_quantities_changed"] == 0
    assert man["candidate_files_touched"] == 0


def test_edited_v4_refused(monkeypatch):
    monkeypatch.setattr(M, "V4_PIN", "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v4_manifest()


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
    v4 = _piece(repo, "T-910", "Merge agents/task-T-910: previous manifest (verified)")
    m = {"T-911": _piece(repo, "T-911", "Merge agents/task-T-911: a bound host (verified)"),
         "T-912": _piece(repo, "T-912", "Merge agents/task-T-912: a reconciliation (verified)")}
    later = _piece(repo, "T-913", "Merge agents/task-T-913: after the V5 base")
    return {"repo": repo, "base": v4, "head": m["T-912"], "m": m, "later": later}


def test_synthetic_v5_range_complete(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    assert M.M4.check_coverage(p, syn["base"], syn["head"], syn["repo"])["covered"] == ["T-911", "T-912"]


def test_adverse_piece_missing_or_previous_manifest_piece_refused(syn):
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-912"):
        M.M4.check_coverage({"T-911": {"merge": syn["m"]["T-911"][:8]}}, syn["base"], syn["head"], syn["repo"])
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    with pytest.raises(M.ManifestError, match="OUT_OF_RANGE.*T-910"):          # belongs to V4, not V5
        M.M4.check_coverage(dict(p, **{"T-910": {"merge": syn["base"][:8]}}), syn["base"], syn["head"], syn["repo"])
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-913"):  # head moved: V6 territory
        M.M4.check_coverage(p, syn["base"], syn["later"], syn["repo"])


def test_adverse_no_wiring_outside_pieces_refused(monkeypatch, t544):
    monkeypatch.setattr(M, "NO_WIRING", dict(M.NO_WIRING, **{"T-999": "not a piece"}))
    with pytest.raises(M.ManifestError, match="NO_WIRING"):
        M.build(t544=t544)


# ---- T-544 glue hosts ------------------------------------------------------------------------------------------------
def test_1f_host_by_hand(man):
    h = {x["host_line_id"]: x for x in man["glue_hosts"]["hosts"]}[H1F]
    hi = 1.23 + 0.20 * 5.627 + 0.20886 + 0.20 * 3.812 + 0.20 * 6.710      # W14, W15+W16, W18, W19+W20, W24
    lo = 0.975 + 0.47 + 0.17346 + 0.0 + 0.0
    assert h["face_sum_m2"] == [A(lo, abs=1e-9), A(hi, abs=1e-9)] == [A(1.61846), A(4.66866)]
    assert h["v5_expected_after"]["glue_kg"]["range"] == [A((101.976 - hi) * 4.5, abs=1e-6),
                                                         A((101.976 - lo) * 4.5, abs=1e-6)]
    assert h["v5_expected_after"]["glue_kg"]["range"] == [A(437.88303), A(451.60893)]
    assert h["v4_expected_after"]["state"] == "HELD" and h["t498_stage_line"] == "L-4b9a29d424ea40e0af8a"
    assert h["stale"] is True


def test_part2_hosts_by_hand(man):
    h = {x["host_line_id"]: x for x in man["glue_hosts"]["hosts"]}
    gf = h[HGF2]["v5_expected_after"]["glue_kg"]["range"]
    assert gf == [A((44.2975 - (0.5002 + 0.694 + 0.670)) * 4.5, abs=1e-6), A(199.33875)]
    f1 = h[H1F2]["v5_expected_after"]["glue_kg"]["range"]
    assert f1 == [A((46.836 - (0.540 + 0.694 + 0.670 + 0.500)) * 4.5, abs=1e-6), A(210.762)]
    assert h[HGF2]["v4_expected_after"]["state"] == "NOT_STATED"
    assert h[HGF2]["v4_expected_after"]["legacy_kg_range"][0] - gf[0] == A(194.02875 - 190.94985, abs=1e-6)
    s2 = h[H2F]["v5_expected_after"]["glue_kg"]
    assert s2["state"] == "HELD" and s2["value"] is None and s2["range"] is None and h[H2F]["stale"] is False


def test_glue_group_and_stale_bindings(man):
    g = man["glue_hosts"]
    assert g["glue_group"]["v4_expected_after"]["at_least"] == [A(17.643906), A(18.16227)]
    assert g["glue_group"]["v5_expected_after"] == {"status": "HELD", "at_least": [A(34.891351), A(36.226627)],
                                                    "to_buy_at_least": [35, 37]}
    assert g["glue_group"]["v5_part1_only"]["at_least"] == [A(35.159227), A(36.226627)]
    assert g["bindings_stale_new_vs_v4"] == sorted(f"T-453|{h}|{k}" for h in (HGF2, H1F2)
                                                   for k in ("glue_bags_25kg_net", "glue_kg"))
    assert g["stage_lines_stale"] == ["L-4b9a29d424ea40e0af8a", "L-6989349aef1cd4fa0940", "L-aa5532bb971eceac1b76"]


def test_adverse_t544_before_not_v4_refused(t544):
    bad = copy.deepcopy(t544)
    bad["part1"]["before_t537_r2"]["glue_kg"] = {"state": "BOUNDED_EXPOSURE", "range": [443.27313, 451.60893]}
    with pytest.raises(M.ManifestError, match="V4 expectation"):
        M.glue_hosts(M.v4_manifest(), bad)


def test_adverse_part2_high_end_moved_refused(t544):
    bad = copy.deepcopy(t544)
    bad["part2"][0]["after"]["glue_kg"]["range"][1] -= 1.0
    with pytest.raises(M.ManifestError, match="HIGH end"):
        M.glue_hosts(M.v4_manifest(), bad)


# fixture (not Alsenan): a staged villa whose glue stage line on one host is another id
def test_stage_ids_check_fixture_and_adverse():
    rows = [{"line_id": s, "source_line_id": h, "item_code": "MAS.GLUE.AAC"} for h, s in M.STAGE_GLUE.items()]
    rows.append({"line_id": "S-UNITS", "source_line_id": H1F, "item_code": "MAS.UNITS.WHITE"})
    assert M.stage_ids_check(rows) == sorted(M.STAGE_GLUE.values())
    rows[0] = dict(rows[0], line_id="L-other")
    with pytest.raises(M.ManifestError, match="STAGE"):
        M.stage_ids_check(rows)


# ---- T-544 lintel ends ----------------------------------------------------------------------------------------------
def test_lintel_lines_stay_held(man, idx):
    le = {x["opening_id"]: x for x in man["lintel_ends"]["part1"]}
    assert le["W16"]["after"]["at_most_beside_m3"] == A(0.20 * 0.20 * (1.5523 + 0.494 + 1.233), abs=1e-4)
    assert le["W24"]["after"]["at_most_beside_m3"] == A(0.20 * 0.20 * 6.710)
    for x in le.values():
        assert idx[x["line_id"]]["class"] == "HELD" and x["after"]["value"] is None
    assert len(man["lintel_ends"]["part2_ceilings"]) == 13


def test_adverse_lintel_released_refused(idx, t544):
    bad = copy.deepcopy(idx)
    bad[M.LINTEL_LINES["W19"]]["class"] = "RELEASED"
    with pytest.raises(M.ManifestError, match="HELD lintel"):
        M.lintel_ends(bad, t544)


# ---- T-552 plaster height --------------------------------------------------------------------------------------------
def test_plaster_height_by_hand(man):
    p = man["plaster_height"]
    r = {x["room"]: x for x in p["rows"]}
    gf15 = r["GF-15"]
    # face 21.537 lm x H (4.50 - 0.16 - b, b 0 .. 0.10) - openings 22.5969 (T-292 ledger)
    assert gf15["after"]["bound_m2"] == [A(21.537 * 4.24 - 22.5969, abs=2e-3), A(21.537 * 4.34 - 22.5969, abs=2e-3)]
    assert gf15["before"] == {"class": "RELEASED", "value": A(56.0131), "basis": "owner G1 3.65 (= paint height)"}
    assert p["released_lines"] == 4 and p["held_lines"] == 7
    assert p["released_before_m2"] == A(56.0131 + 51.415 + 52.005 + 57.775) == p["equals_released_paint_m2"]
    assert p["code_view"]["FIN.PLASTER_released_after_m2"] == A(580.5819 - 217.2081)
    assert len(p["bindings_stale"]) == 58 and p["bindings_held_blank_unchanged"] == 74
    assert p["owning_package"] is None and all(x["after"]["value"] is None for x in p["rows"])


def test_adverse_plaster_line_not_at_paint_height_refused(idx):
    bad = copy.deepcopy(idx)
    bad["L-0d93f2209cd9bb827c0a"]["measured_net"] = 68.72          # already corrected: T-552 'net' no longer matches
    with pytest.raises(M.ManifestError, match="not the candidate line"):
        M.plaster_height(bad, bindings=[])


def test_adverse_plaster_binding_with_value_refused(idx):
    b = [{"table": "T-454", "row": "L-0d93f2209cd9bb827c0a|WALL_PLASTER", "line_id": "L-0d93f2209cd9bb827c0a",
          "kind": "mortar_m3", "value": 1.12, "bound": None, "read": {"net_read": 56.0131}}]
    with pytest.raises(M.ManifestError, match="released value"):
        M.plaster_height(idx, bindings=b)


# ---- reconciliations ------------------------------------------------------------------------------------------------
def test_reconciliations_equal_the_candidate(man):
    c = man["reconciliation_consistency"]
    assert c["T-545"]["engine_m3"] == A(66.321054) and (c["T-545"]["held"], c["T-545"]["excluded"]) == (27, 54)
    assert c["T-546"]["floor_m2"] == A(85.57571) and c["T-546"]["upturn_lm_at_rule_height"] == A(25.214585 / 0.20)
    assert c["T-547"]["engine_m2"] == A(340.3038) and c["T-552"]["engine_m2"] == A(580.5819)
    assert c["T-554"]["stair_engine_wrong_m2"] == A(1.250 * 1.150)
    assert all(v["candidate_lines_moved"] == 0 for v in c.values())


def test_adverse_reconciliation_engine_side_not_candidate_refused(idx):
    bad = copy.deepcopy(idx)
    bad["L-fake"] = {"item_code": "FIN.WALL.TILE", "class": "RELEASED", "measured_net": 1.0, "unit": "m2",
                     "element_id": "X"}
    with pytest.raises(M.ManifestError, match="T-547"):
        M.reconciliation_consistency(bad, M.v4_manifest())


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
    assert json.loads(M.dumps(man))["glue_hosts"]["glue_group"]["v5_expected_after"]["status"] == "HELD"
