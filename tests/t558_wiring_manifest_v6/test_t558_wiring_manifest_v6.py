"""T-558: WIRING MANIFEST V6 (research/agents_t558/WIRING_MANIFEST_V6.json) is recomputed from the merged piece outputs
(T-550, T-555, T-556, T-557, T-559) on the pinned V5 and must equal the committed file; hand checks of the plaster
lines that move; the 132 plaster bindings listed one by one with the T-454 bound rule reproduced; FIN.PAINT after =
before for every line; R-T549-1 coverage on a synthetic repository (normal + a range edge left out); held never 0."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t558"))
import manifest_v6 as M          # noqa: E402

A = pytest.approx
GF15, F104, F203, F101 = ("L-0d93f2209cd9bb827c0a", "L-971f0bdaf68d7fd0966c", "L-4ce74fc37a08d4bdf0d8",
                          "L-af9621f43bc316a871ea")


@pytest.fixture(scope="module")
def bs():
    return M.M5._t523()["bindings"]


@pytest.fixture(scope="module")
def man(bs):
    return M.build(bs=bs)


@pytest.fixture(scope="module")
def idx():
    return M.M1.line_index()


@pytest.fixture(scope="module")
def t556():
    return M._json(M.T556)


def _rows(man):
    return {r["line_id"]: r for r in man["plaster_lines"]["rows"]}


def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_merge_since_v5_is_covered(man):
    M.M2.check_sources(M.PIECES)
    assert man["coverage"] == {"range": ["47d74505", "431ac67f"], "first_parent_merges": 5,
                               "covered": ["T-550", "T-555", "T-556", "T-557", "T-559"]}
    assert set(M.NO_WIRING) == {"T-550", "T-555", "T-557", "T-559"}
    assert man["candidate_lines_moved_v5_to_v6"] == 0 and man["released_quantities_changed"] == 0
    assert man["candidate_files_touched"] == 0


def test_edited_v5_refused(monkeypatch):
    monkeypatch.setattr(M, "V5_PIN", "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v5_manifest()


def test_adverse_t556_as_no_wiring_refused(monkeypatch, bs):
    monkeypatch.setattr(M, "NO_WIRING", dict(M.NO_WIRING, **{"T-556": "moves nothing"}))
    with pytest.raises(M.ManifestError, match="T-556"):
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
    v5 = _piece(repo, "T-920", "Merge agents/task-T-920: previous manifest (verified)")
    m = {"T-921": _piece(repo, "T-921", "Merge agents/task-T-921: first edge (verified)"),
         "T-922": _piece(repo, "T-922", "Merge agents/task-T-922: a method version (verified)"),
         "T-923": _piece(repo, "T-923", "Merge agents/task-T-923: last edge (verified)")}
    later = _piece(repo, "T-924", "Merge agents/task-T-924: after the V6 base")
    return {"repo": repo, "base": v5, "head": m["T-923"], "m": m, "later": later}


def test_synthetic_v6_range_complete(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    assert M.M4.check_coverage(p, syn["base"], syn["head"], syn["repo"])["covered"] == ["T-921", "T-922", "T-923"]


@pytest.mark.parametrize("edge", ["T-921", "T-923"])
def test_adverse_range_edge_left_out_refused(syn, edge):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items() if t != edge}
    with pytest.raises(M.ManifestError, match=f"MISSING_FROM_MANIFEST.*{edge}"):
        M.M4.check_coverage(p, syn["base"], syn["head"], syn["repo"])


def test_adverse_previous_or_later_piece_refused(syn):
    p = {t: {"merge": s[:8]} for t, s in syn["m"].items()}
    with pytest.raises(M.ManifestError, match="OUT_OF_RANGE.*T-920"):
        M.M4.check_coverage(dict(p, **{"T-920": {"merge": syn["base"][:8]}}), syn["base"], syn["head"], syn["repo"])
    with pytest.raises(M.ManifestError, match="MISSING_FROM_MANIFEST.*T-924"):
        M.M4.check_coverage(p, syn["base"], syn["later"], syn["repo"])


# ---- plaster lines (T-556) -------------------------------------------------------------------------------------------
def test_plaster_released_lines_by_hand(man):
    r = _rows(man)
    # GF-15: face 21.537 x 4.29 - (D 1.76 + D 2.20 + W03 5.106 x 4.29, head 4.30 above the 3.65 paint line)
    gf15 = 21.537 * 4.29 - (1.76 + 2.20 + 5.106 * 4.29)
    assert r[GF15]["v6_expected_after"]["held_low"] == A(gf15, abs=1e-6) == A(66.52899, abs=1e-6)
    assert r[F104]["v6_expected_after"]["held_low"] == A(17.40 * 3.99 - 6.285, abs=1e-9)        # 63.141
    assert r[F203]["v6_expected_after"]["held_low"] == A(18.90 * 3.99 - 5.54 - 0.096, abs=1e-9)  # 69.775
    pl = man["plaster_lines"]
    assert pl["released_before_m2"] == A(56.0131 + 51.415 + 52.005 + 57.775, abs=1e-9) == A(217.2081)
    assert pl["equals_released_paint_m2"] == pl["released_before_m2"]
    assert pl["released_after_bound_m2"] == [A(66.52899 + 62.573 + 63.141 + 69.775), A(66.52899 + 62.607 + 63.141
                                                                                         + 69.775)]
    assert pl["code_view"]["FIN.PLASTER_released_after_m2"] == A(580.5819 - 217.2081)
    assert pl["released_lines"] == 4 and pl["held_lines"] == 7


def test_plaster_supersedes_v5_t552_bound(man):
    r = _rows(man)
    assert r[GF15]["v5_expected_after"]["bound_m2"] == [68.71993, 70.87363]
    assert r[GF15]["v5_to_v6_m2"] == [A(66.52899 - 68.71993), A(66.52899 - 70.87363)]
    for x in r.values():
        a = x["v6_expected_after"]
        assert a["class"] == "HELD" and a["value"] is None and 0 < a["held_low"] <= a["held_high"]


def test_adverse_t556_line_class_not_candidate_refused(idx, t556):
    bad = copy.deepcopy(t556)
    next(r for r in bad["rows"] if r["line_id"] == GF15)["candidate_class"] = "HELD"
    with pytest.raises(M.ManifestError, match=GF15):
        M.plaster_lines(idx, M.v5_manifest(), bad)


def test_adverse_t556_range_inverted_refused(idx, t556):
    bad = copy.deepcopy(t556)
    r = next(r for r in bad["rows"] if r["line_id"] == F101)
    r["new_lo"], r["new_hi"] = r["new_hi"], r["new_lo"]
    with pytest.raises(M.ManifestError, match="inverted"):
        M.plaster_lines(idx, M.v5_manifest(), bad)


def test_adverse_t556_total_not_its_rows_refused(idx, t556):
    bad = copy.deepcopy(t556)
    bad["released_4_lines"]["new"][0] = "262.0"
    with pytest.raises(M.ManifestError, match="released_4_lines"):
        M.plaster_lines(idx, M.v5_manifest(), bad)


# ---- bindings --------------------------------------------------------------------------------------------------------
def test_bound_rule_synthetic_fixture_and_adverse():
    assert M._bound_rule(100.0, 120.0) == [2.0, 2.4]                  # 100 .. 120 m2 x 0.020 m
    ok = [{"table": "T-454", "row": "X|WALL_PLASTER", "item_code": "FIN.PLASTER", "material": "WALL_PLASTER",
           "kind": "mortar_m3", "bound": [2.0, 2.4], "read": {"held_read": [100.0, 120.0]}}]
    assert M.reproduce_bound_rule(ok) == 1
    bad = copy.deepcopy(ok)
    bad[0]["bound"] = [2.0, 2.5]
    with pytest.raises(M.ManifestError, match="BOUND_RULE"):
        M.reproduce_bound_rule(bad)
    with pytest.raises(M.ManifestError, match="no printed bound"):
        M.reproduce_bound_rule([])


def test_bindings_listed_one_by_one(man):
    b = man["bindings"]
    assert b["count"] == 132 == len(b["rows"]) == b["v5_stale"] + b["v5_blank_unchanged"]
    assert b["v5_stale"] == 58 and b["figure_changes"] == 22 and b["read_only_changes"] == 110
    assert len({r["key"] for r in b["rows"]}) == 132
    assert sum(1 for r in b["rows"] if r["in_v5_stale_list"]) == 58
    for r in b["rows"]:
        e = r["expected_after"]
        assert e["value"] is None and e["class_read"] == "HELD" and e["net_read"] is None and e["estimate_beside"] is None
        assert (e["bound"] is not None) == (r["material"] == "WALL_PLASTER" and r["kind"] == "mortar_m3")


def test_bindings_gf15_by_hand(man):
    rows = [r for r in man["bindings"]["rows"] if r["line_id"] == GF15]
    assert len(rows) == 12
    m = [r for r in rows if r["change"] == "FIGURE"]
    assert len(m) == 2
    for r in m:
        assert r["before"]["estimate_beside"] == A(56.0131 * 0.02)                         # 1.120262
        assert r["expected_after"]["bound"] == [A(66.52899 * 0.02), A(66.52899 * 0.02)]     # 1.3305798
    s = man["bindings"]["table_sums"]["T-454"]
    assert s["wall_plaster_mortar_m3_estimate_beside_before"] == A(217.2081 * 0.02)
    assert s["wall_plaster_mortar_m3_bound_after"] == [A(840.64581 * 0.02), A(895.89641 * 0.02)]


def test_adverse_binding_with_value_refused(man, bs):
    bad = copy.deepcopy(bs)
    next(b for b in bad if b["line_id"] == GF15)["value"] = 1.0
    with pytest.raises(M.ManifestError, match="released value"):
        M.bindings(man["plaster_lines"], bad, M.v5_manifest())


def test_adverse_v5_stale_binding_missing_refused(man, bs):
    bad = [b for b in bs if not (b["line_id"] == GF15 and b["kind"] == "sand_m3" and b["table"] == "T-454"
                                 and b["material"] == "BOND_COAT")]
    with pytest.raises(M.ManifestError, match="V5 stale"):
        M.bindings(man["plaster_lines"], bad, M.v5_manifest())


# ---- paint (one owner) -----------------------------------------------------------------------------------------------
def test_paint_after_equals_before_every_line(man, idx):
    p = man["paint"]
    assert p["paint_lines_count"] == 45 and p["paint_lines_moved"] == 0
    assert p["paint_released_after_m2"] == p["paint_released_before_m2"] == A(217.2081)
    assert all(x["expected_after"] == "= before" for x in p["paint_lines"])
    assert len(p["pairs"]) == 11
    for x in p["pairs"]:
        assert x["paint_expected_after"] == x["paint_before"]
        assert idx[x["paint_line"]]["item_code"] == "FIN.PAINT"


def test_adverse_paint_not_equal_plaster_refused(man, idx):
    bad = copy.deepcopy(idx)
    pid = next(x["paint_line"] for x in man["paint"]["pairs"] if x["plaster_line"] == GF15)
    bad[pid]["measured_net"] = 50.0
    with pytest.raises(M.ManifestError, match="shared-height"):
        M.paint_unchanged(bad, man["plaster_lines"])


def test_wiring_row_closes_f_t555_3(man):
    w = man["wiring_row"]
    assert w["closes"].startswith("F-T555-3") and w["gate"].startswith("B")
    assert "262.01799" in w["steps"][0] and "217.2081" in w["steps"][0]


def test_held_never_zero(man):
    def walk(o):
        if isinstance(o, dict):
            if str(o.get("state", "")).startswith("HELD") or o.get("class") == "HELD":
                assert o.get("value") is None
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads(M.dumps(man)))
