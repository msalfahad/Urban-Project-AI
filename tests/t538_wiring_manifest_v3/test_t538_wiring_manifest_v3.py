"""T-538: WIRING MANIFEST V3 (research/agents_t538/WIRING_MANIFEST_V3.json) is recomputed from the merged piece outputs
(T-531 lintel bars, T-532 END_CENSUS_V3, T-535 / T-540 sand) on the pinned V2 and must equal the committed file; hand
checks of every figure; R-T538-1 sliver head rule on a non-Alsenan fixture (normal + adverse); unmerged source refused
on a synthetic repository; T-534 stated in both branches, never read from live board state."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t538"))
import manifest_v3 as M          # noqa: E402

A = pytest.approx


@pytest.fixture(scope="module")
def man():
    return M.build()


def test_committed_manifest_is_the_rebuild(man):
    assert M.dumps(man) == M.OUT_JSON.read_text(encoding="utf-8")


def test_every_source_merged_and_v2_pinned(man):
    M.M2.check_sources(M.PIECES)
    assert set(M.NEW_PIECES) == {"T-531", "T-532", "T-535", "T-536", "T-540"}
    assert "T-534" not in M.PIECES and "T-534" in man["not_sources"]
    assert man["candidate_lines_moved_v2_to_v3"] == 0 and man["released_quantities_changed"] == 0


def test_edited_v2_refused(monkeypatch):
    monkeypatch.setitem(M.PINS, M.V2_JSON, "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v2_manifest()


# ---- T-531 lintel bars --------------------------------------------------------------------------------------------
def test_lintel_bars_two_held_parts_by_hand(man):
    b = man["lintel_bars"]
    assert b["candidate_lines_carrying_lintel_bars"] == []            # no double count with an existing STR.REBAR line
    p, f = b["added_lines"]
    # PRODUCED: L1 3.90 m x 488/162 + L3 2.45 m x 1356/162 + L2 1.55 m x 680/162 (T-531 s.5 hand check)
    assert p["after"]["held_low"] == A(3.90 * 488 / 162 + 2.45 * 1356 / 162 + 1.55 * 680 / 162, abs=1e-6) == A(38.761728)
    assert f["after"]["held_low"] == A(8.0673 * 488 / 162, abs=1e-6) == A(24.301496)    # FLAGGED: L1 over 8.0673 m
    for x in (p, f):
        assert x["unit"] == "kg" and x["after"]["class"] == "HELD" and x["after"]["value"] is None
        assert x["after"]["held_high"] is None and x["before"] is None
        assert "S1 LINKS" in x["after"]["held_parts"]
    assert len(p["lintels"]) == 6 and len(f["lintels"]) == 10
    assert b["t515_to_t531"]["delta_kg"] == A(-0.0327 * 488 / 162, abs=1e-6)              # W18 strip in C8


def test_lintel_parts_match_v2_line_states(man):
    v2 = M.v2_manifest()
    st = {r["element_id"].split(":")[1]: r["after"]["state"] for r in v2["stream_S"]["lintel_lines"]}
    p, f = man["lintel_bars"]["added_lines"]
    assert {st[o] for o in p["lintels"]} == {"BOUNDED_MIN_BEARING"}
    assert {st[o] for o in f["lintels"]} == {"HELD_BY_NAME"}


def test_existing_lintel_rebar_line_refused():
    idx = M.M1.line_index()
    v2 = M.v2_manifest()
    bad = copy.deepcopy(idx)
    bad["L-fake"] = {"item_code": "STR.REBAR", "unit": "kg", "class": "RELEASED", "element_id": "HL:LINTEL_STEEL:W14",
                     "measured_net": 1.0}
    with pytest.raises(M.ManifestError, match="double"):
        M.lintel_bar_rows(bad, v2)


# ---- T-532 + R-T538-1 ---------------------------------------------------------------------------------------------
def test_end_census_set_equal_and_no_line(man):
    e = man["end_census_v3"]
    assert e["set_equal_to_t526"] == {"listed_n": 12, "held_n": 1} and e["candidate_lines_moved"] == 0
    assert e["perimeter_1F_W09"]["after_m3"] == A(0.003334 + 0.007021, abs=1e-6)
    t = e["ties_and_mesh"]
    assert (t["d_ties_nr"], t["d_mesh_owner_ml"], t["d_mesh_drawing_ml"]) == (30.0, 40.9, 44.1)
    assert t["state"].startswith("NO LINE")


def test_sliver_check_villa(man):
    s = man["sliver_check"]
    assert s["joint_m"] == 0.010 and s["junctions_listed"] == 118 + 12
    assert s["by_state"] == {"OWN": 73, "FROM_ADJACENT_SAME": 53, "FROM_ADJACENT_CHANGED": 4, "HELD": 0}
    by = {(x["run"], x["at"]): x for x in s["sliver_junctions"]}
    g = by[("GF|WB-FL0041-FL0042", "end 1")]                   # F-C-T532-1: the FACE sliver is not the head
    assert g["piece_len_m"] == A(0.001695) and g["state"] == "FROM_ADJACENT_CHANGED"
    assert g["head"]["member_id"] == "BM-GF-046" and g["head"]["depth_m"] == "0.75"
    w09 = [x for x in s["sliver_junctions"] if x["run"] == "1F|WB-FL0024-FL0025"]
    assert [x["state"] for x in w09] == ["FROM_ADJACENT_SAME"] and w09[0]["piece_len_m"] == A(0.000189)
    assert s["checker_5mm_vs_joint"]["classified_differently"] == 0


# fixture (not Alsenan): run of 5 pieces: COLUMN 0.30 | BEAM B9 2.40 | FACE 0.003 | BEAM B9 0.002 | COLUMN 0.25
def _run(kinds_lens):
    out = []
    for i, (k, n, mem, d) in enumerate(kinds_lens):
        out.append({"run_key": "X|R", "seq": str(i), "kind": k, "len_m": str(n), "member_id": mem, "mark": mem and "B9",
                    "depth_m": d, "face_id": "F-1" if k == "FACE" else "", "face_cls": "SLAB" if k == "FACE" else "",
                    "slab_t_m": "0.20" if k == "FACE" else ""})
    return out


ROLE = {"COLUMN": "CONCRETE", "BEAM": "MASONRY", "FACE": "MASONRY", "NONE": "MASONRY"}
FX = [("COLUMN", 0.30, "", ""), ("BEAM", 2.40, "BM-9", "0.50"), ("FACE", 0.003, "", ""), ("BEAM", 0.002, "BM-9", "0.50"),
      ("COLUMN", 0.25, "", "")]


def test_fixture_head_from_adjacent_full_piece():
    p = _run(FX)
    a = M.resolve_head(p, 1, -1, 0.010, ROLE)                 # 2.40 m BEAM at the first column: its own head
    assert a["state"] == "OWN" and a["head"]["depth_m"] == "0.50"
    b = M.resolve_head(p, 3, -1, 0.010, ROLE)                 # 2 mm BEAM sliver at the second column: walk 3 -> 2 -> 1
    assert b["state"] == "FROM_ADJACENT_SAME" and b["piece"] == 1    # same member BM-9: head unchanged
    p2 = _run(FX[:3] + [("COLUMN", 0.25, "", "")])            # FACE 3 mm sliver at the column
    c = M.resolve_head(p2, 2, -1, 0.010, ROLE)
    assert c["state"] == "FROM_ADJACENT_CHANGED" and c["head"]["kind"] == "BEAM" and c["sliver"]["own_fields"]["kind"] \
        == "FACE"


def test_fixture_mirrored_run_same_answer():
    p = list(reversed(_run(FX)))
    b = M.resolve_head(p, 1, +1, 0.010, ROLE)                 # mirrored: sliver now piece 1, walk away = +1
    assert b["state"] == "FROM_ADJACENT_SAME" and b["head"]["member_id"] == "BM-9"


def test_adverse_sliver_head_refused_and_held_when_no_full_piece():
    p = _run(FX)
    with pytest.raises(M.ManifestError, match="SLIVER"):
        M.head_of(p[3], 0.010)
    only = _run([("COLUMN", 0.30, "", ""), ("FACE", 0.004, "", ""), ("COLUMN", 0.30, "", "")])
    h = M.resolve_head(only, 1, +1, 0.010, ROLE)              # column on both sides of a sliver: HELD, never a head
    assert h["state"] == "HELD" and h["head"] is None and "HELD" in h["held"]
    with pytest.raises(M.ManifestError, match="not masonry"):
        M.resolve_head(p, 0, +1, 0.010, ROLE)


def test_adverse_joint_not_metres(monkeypatch, tmp_path):
    bad = tmp_path / "s.json"
    bad.write_text(json.dumps({"joint_m": 10}))
    monkeypatch.setattr(M, "T520_SUM", bad)
    with pytest.raises(M.ManifestError, match="metre"):
        M.joint_m()


# ---- sand ---------------------------------------------------------------------------------------------------------
def test_sand_group_no_line_and_delta(man):
    s = man["sand"]
    assert s["candidate_sand_lines"] == [] and s["candidate_lines_moved"] == 0
    g = s["binding_group"]
    assert g["before_t523_at_least_m3"] == [A(17.588682), A(23.290726)]
    assert g["after_t535_at_least_m3"] == [A(17.746996), A(23.449040)]
    # cause by hand: stair 1.06028 x 1.05 - 1.062939 = +0.050355 ; perimeter key +0.107959 -> +0.158314
    assert 1.06028 * 1.05 - 1.062939 + 0.107959 == A(0.158314, abs=1e-6) and g["delta_m3"] == [A(0.158314)] * 2
    assert "HELD" in s["tonnes"] and "HELD" in s["loads"]


# ---- T-534 stated both ways, never from live state ----------------------------------------------------------------
def test_stair_area_both_branches(man):
    s = man["stair_bed_area"]
    assert s["area_m2"] == A(35.4313) and len(s["lines"]) == 11
    assert s["lines_by_code"] == {"FIN.MARBLE.TREAD": 8, "FIN.MARBLE.RISER": 1, "FIN.MARBLE.LANDING": 2}
    assert s["area_m2"] * 0.03 == A(1.062939, abs=1e-6)
    assert s["once_t534_merges"] == {"state": "AT_LEAST", "value_m2": A(35.4313), "source": "T-534"}
    assert s["until_then"]["state"] == "HELD_BY_NAME" and s["until_then"]["value_m2"] is None


def _git(repo, *a):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env).stdout.decode().strip()


def test_adverse_unmerged_source_on_synthetic_repo(monkeypatch, tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    (repo / "a").write_text("1\n")
    _git(repo, "add", "a")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "-b", "agents/task-T-997")
    (repo / "a").write_text("2\n")
    _git(repo, "commit", "-q", "-am", "ready")
    ready = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "work")
    monkeypatch.setattr(M.M2, "ROOT", repo)
    M.M2.check_sources({"T-996": {"merge": base[:8]}})
    with pytest.raises(M.ManifestError, match="STALE_SOURCE"):
        M.M2.check_sources({"T-997": {"merge": ready[:8]}})
    _git(repo, "merge", "-q", "--no-ff", "-m", "merge", "agents/task-T-997")       # once merged it is a source
    M.M2.check_sources({"T-997": {"merge": ready[:8]}})


def test_held_never_zero(man):
    def walk(o):
        if isinstance(o, dict):
            if str(o.get("state", "")).startswith("HELD") or o.get("class") == "HELD":
                assert o.get("value") in (None,) and o.get("value_m2") is None
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(man)
