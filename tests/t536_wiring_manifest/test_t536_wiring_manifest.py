"""T-536: WIRING MANIFEST V2 (research/agents_t536/WIRING_MANIFEST_V2.json) is recomputed from the merged piece outputs
(V1 builder re-run on the T-527 V3 bearings, T-529 exposure V2, T-526 census, FINISH V7) and must equal the committed
file; hand checks of every value that moved V1 -> V2; held stays held by name; the unit of a line comes from its item;
a non-Alsenan synthetic case of two pieces moving one line in order; adverse: stale / unmerged source refused."""

import copy
import json
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import manifest_t536 as M          # noqa: E402

A = pytest.approx
HAVE_DXF = M.M1._dxf() is not None


def _committed():
    return json.loads(M.OUT_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def full():
    if not HAVE_DXF:
        pytest.skip("private drawing not decoded in this checkout")
    m = M.build()
    (Path(tempfile.gettempdir()) / "t536_manifest_built.json").write_text(M.dumps(m), encoding="utf-8")
    return m


@pytest.fixture(scope="module")
def offline():
    return M.build(drawing=False)


def _lin(m, oid):
    return [r for r in m["stream_S"]["lintel_lines"] if r["element_id"] == f"LINTEL:{oid}"][0]


def _f(m, lid):
    return [r for r in m["stream_F"]["lines"] if r["line_id"] == lid][0]


# ---- the committed manifest is the rebuild ---------------------------------------------------------------------------
def test_full_manifest_equals_committed_file(full):
    assert M.dumps(full) == M.OUT_JSON.read_text(encoding="utf-8")


def test_offline_stream_s_equals_committed_and_f_stays_held(offline):
    c = _committed()
    for key in ("stream_S", "finish_v6_v7", "stale_bindings", "pieces", "inputs", "candidate"):
        assert json.loads(M.dumps(offline[key])) == c[key], key
    if not offline["stream_F"]["drawing"]["drawing_read"]:
        for r in offline["stream_F"]["lines"]:                 # absent drawing: HELD, never a number, never 0
            assert r["after"]["state"] == "HELD" and "value" not in r["after"]


# ---- stream S: lintels on the V3 bearings (T-527) ---------------------------------------------------------------------
def test_v1_basis_reproduces_v1_and_only_d_gf_13_moves(offline):
    moved = [r["element_id"] for r in offline["stream_S"]["lintel_lines"] if r["v1_to_v2"]]
    assert moved == ["LINTEL:D-GF-13"]
    d = _lin(offline, "D-GF-13")
    B, D = d["section_B_D_m"]                  # END 1.261 -> 1.260 at the column (V2 area tolerance, F-C-T516-1)
    assert d["after"]["length_m"][1] == A(3.763) and d["after"]["high"] == A(B * D * 3.763, abs=1e-6)
    assert {c["field"]: (c["v1"], c["v2"]) for c in d["v1_to_v2"]} == {"high": (0.11292, 0.11289),
                                                                       "length_m[1]": (3.764, 3.763)}
    assert d["after"]["low"] == d["before"]["value"]           # the lower bound is today's released value
    assert "T-527" in [p["task"] for p in d["source"]] and "R-T527-1" in d["rules"]


def test_held_lintels_stay_held_by_name_with_the_new_ceiling_beside(offline):
    for oid, v1, v3 in (("W18", 0.978, 1.077), ("D-GF-11", 1.869, 1.865)):
        r = _lin(offline, oid)
        assert r["after"]["state"] == "HELD_BY_NAME" and r["after"]["low"] is None and r["after"]["high"] is None
        assert r["t516_length_ceiling_m"]["v1"] == A(v1) and r["t516_length_ceiling_m"]["v3"] == A(v3)
        assert "no quantity" in r["t516_length_ceiling_m"]["carried"] and r["v1_to_v2"] == []
    w18 = _lin(offline, "W18")                 # T-524 deficit volume unchanged by T-527 (a BOUNDED end keeps b_min)
    assert w18["after"]["bound_m3"][0] == A(0.034692)


def test_lintel_code_view_moves_by_the_ceiling_only(offline):
    v = offline["stream_S"]["lintel_code_view"]
    assert v["after"]["at_least_m3"] == A(0.874692)            # lows unchanged
    assert offline["stream_S"]["lintel_code_view_v1_to_v2"] == [
        {"field": "after.upper_known_part_m3", "v1": 1.183992, "v2": 1.183962}]
    assert 1.183992 - 1.183962 == A(0.11292 - 0.11289, abs=1e-9)


def test_host_glue_perimeter_and_groups_unchanged_v1_to_v2(offline):
    c1 = json.loads(M.V1_JSON.read_text(encoding="utf-8"))["stream_S"]
    s = offline["stream_S"]
    for h in s["host_material_lines"]:
        assert h["v1_to_v2"] == []             # W14 / W15 / D-GF-06 faces: no moved bearing on a valued host
    for p in s["perimeter_lines"]:
        assert p["v1_to_v2"] == []
    assert s["glue_group"] == c1["glue_group"] and s["cement_group"] == c1["cement_group"]


def test_t526_moves_no_candidate_line(offline):
    c = offline["stream_S"]["column_end_census"]
    assert c["candidate_lines_moved"] == 0 and c["ends_missed_by_v1"] == 12
    assert c["mas_block"]["d_blockwork_m2"] == 0.0 and c["mas_block"]["d_blocks_nr"] == 0.0
    assert c["ties_and_mesh"]["line_codes_present"] == [] and c["ties_and_mesh"]["d_ties_nr_measured"] == 30.0
    (w09,) = c["perimeter_mortar"]
    p = [x for x in offline["stream_S"]["perimeter_lines"] if "1F-W09" in x["walls"]][0]
    assert w09["perimeter_line_host"] == p["host_line_id"]
    assert p["t526_confirms"][0]["t526_after_m3"] == A(w09["t526_after_m3"]) == A(0.010355)


# ---- stream F: T-529 ledge, the transition unit ------------------------------------------------------------------
def test_ledge_membrane_and_upturn_measured_by_hand(full):
    mem = _f(full, "L-2361d6ec13c952bd2ae3")
    assert mem["after"]["state"] == "MEASURED" and mem["after"]["value"] == A(0.639573)
    assert mem["before"]["class"] == "HELD" and mem["before"]["held_high"] == A(0.639573)
    up = _f(full, "L-d7d1bf8c5991ccf69ea2")
    assert up["after"]["value"] == A(0.250804 + 0.300810, abs=1e-6)      # BCD + BD0, the two solid wall ends
    assert up["after"]["m2_at_0_20"] == A(0.20 * up["after"]["value"], abs=1e-6)
    assert [h for h in (mem, up) if "T-529" not in [p["task"] for p in h["source"]]] == []
    win = _f(full, "L-1954878bb02c91139e1b")
    assert win["v1_to_v2"] == [] and win["after"]["value"] == A(0.500002)


def test_roof_code_totals(full):
    v = full["stream_F"]["code_views"]
    assert v["FIN.WP.ROOF"]["released_before"] == A(209.018867)
    assert v["FIN.WP.ROOF"]["released_after"] == A(209.018867 + 0.639573, abs=1e-6) == A(209.658440)
    assert v["FIN.WP.ROOF"]["held_lines_after"] == 1                     # the 2F block roof (Q-34) stays HELD
    assert v["FIN.WP.ROOF_UPTURN"]["released_after"] == A(186.782544 + 0.500002 + 0.551614, abs=1e-6)
    assert v["FIN.ROOF.FINISH"]["released_after"] == A(202.219760 + 4.519172, abs=1e-6)
    for code in ("FIN.ROOF.SCREED", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.WP.DOORWAY_TRANSITION"):
        assert v[code]["released_after"] is None and "never 0.0" in v[code]["view_after"]


def test_window_transition_is_beside_never_an_m2_line(full):
    assert [a for a in full["stream_F"]["added_lines"] if a["item_code"] == "FIN.WP.DOORWAY_TRANSITION"] == []
    assert full["stream_F"]["code_views"]["FIN.WP.DOORWAY_TRANSITION"]["lines_after"] == \
        full["stream_F"]["code_views"]["FIN.WP.DOORWAY_TRANSITION"]["lines_before"] == 16
    (rm,) = full["stream_F"]["removed_v1_lines"]
    assert rm["measure"] == {"value_lm": A(2.976663), "unit": "lm"} and "UNIT" in rm["refusal"]
    bes = _f(full, "L-2361d6ec13c952bd2ae3")["after"]["held_beside"]
    tr = [b for b in bes if b["what"] == "WINDOW_TRANSITION"]
    assert len(tr) == 1 and tr[0]["unit"] == "lm" and tr[0]["bound"] == A(2.976663) and tr[0]["status"] == "HELD"
    assert {b["what"] for b in bes} >= {"WINDOW_TRANSITION", "VOID_EDGE_TERMINATION", "DRAINAGE_FALLS"}


def test_ledge_build_up_stays_held_with_the_zone_gap_closed(full):
    led = [a for a in full["stream_F"]["added_lines"] if a["element_id"].startswith("1F-POOLCOURT-550-LEDGE:")]
    assert len(led) == 4
    for a in led:
        assert a["after"]["state"] == "HELD" and a["after"]["value"] is None and a["after"]["missing"]
        assert not [x for x in a["after"]["missing"] if x.startswith("ZONE:")] and "T-529" in a["after"]["zone_resolved"]


def test_line_unit_from_the_item():
    idx, t507 = M.M1.line_index(), M.M1._v3058_t507_lines()
    assert M.line_unit("FIN.WP.DOORWAY_TRANSITION", "m2", idx, t507) == "m2"
    assert M.line_unit("FIN.ROOF.SCREED", "m3", idx, t507) == "m3"
    with pytest.raises(M.ManifestError, match="UNIT"):
        M.line_unit("FIN.WP.DOORWAY_TRANSITION", "lm", idx, t507)
    with pytest.raises(M.ManifestError, match="UNIT"):
        M.line_unit("FIN.WP.ROOF_UPTURN", "m2", idx, t507)


# ---- every moved line, V1 -> V2 summary, invariants -------------------------------------------------------------------
def test_line_moves_complete_and_named(full):
    lm = full["line_moves"]
    idx = M.M1.line_index()
    ids = [x["line_id"] for x in lm if not x["line_id"].startswith("NEW")]
    assert len(ids) == len(set(ids)) == 16 + 2 + 3
    for x in lm:
        assert x["pieces"] and x["merges"] and x["owner_trade"]
        if x["item_code"] == "STR.CONC.LINTEL":
            assert idx[x["line_id"]]["class"] == "RELEASED"
    s = {x["element"]: x["cause"] for x in full["v1_to_v2_summary"]}
    assert set(s) == {"LINTEL:D-GF-13", "1F-POOLCOURT-550-LEDGE:wp_upturn", "1F-POOLCOURT-550-LEDGE:wp_membrane",
                      "1F-POOLCOURT-550-LEDGE:falls_screed", "1F-POOLCOURT-550-LEDGE:insulation",
                      "1F-POOLCOURT-550-LEDGE:protection", "1F-POOLCOURT-550-LEDGE:finish",
                      "1F-POOLCOURT-550-LEDGE:wp_window_transition (bay glazing BCE on the slab)"}
    assert all(s.values())


def test_held_never_zero(full):
    def walk(o):
        if isinstance(o, dict):
            st = str(o.get("state", ""))
            if st.startswith("HELD"):                 # a held line carries no value: blank, bound beside, never 0
                assert o.get("value") is None and o.get("low") is None
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(full["line_moves"])
    assert full["released_quantities_changed"] == 0 and full["candidate_files_touched"] == 0


def test_v7_stair_held_by_name_until_t534():
    v = M.finish_v6_v7_v2()["v7_stair_bed"]
    assert "HELD BY NAME" in v["area_state"] and "T-534" in v["area_state"]
    assert "T-534" not in M.PIECES and v["wiring_after"][0].startswith("T-534")


def test_every_piece_is_merged_in_this_tree():
    M.check_sources(M.PIECES)


# ---- synthetic (not Alsenan): two pieces moving one line, in order ---------------------------------------------------
SYN = {"P-1": "a" * 8, "P-2": "b" * 8}


def _syn_moves():
    m1 = {"task": "P-1", "merge": SYN["P-1"], "requires": [], "cause": "wall end pieces measured",
          "after": {"state": "HELD", "held_low": 0.0, "held_high": 2.0}}
    m2 = {"task": "P-2", "merge": SYN["P-2"], "requires": ["P-1"], "cause": "exposure decided",
          "after": {"state": "MEASURED", "value": 1.5}}
    return m1, m2


def test_synthetic_two_pieces_in_order():
    # a 4.00 m parapet run of a terrace: piece 1 bounds the upturn to the two solid ends 0 .. 2.0 lm, piece 2 decides
    # the exposure and measures 1.5 lm (0.75 + 0.75); the line ends at piece 2's value with both steps recorded
    m1, m2 = _syn_moves()
    after, hist = M.apply_moves("L-syn", {"class": "HELD", "value": None}, [m1, m2], merged=lambda c: c in SYN.values())
    assert after == {"state": "MEASURED", "value": 1.5}
    assert [h["task"] for h in hist] == ["P-1", "P-2"] and hist[1]["from"] == m1["after"]
    assert 0.20 * after["value"] == A(0.30)


def test_synthetic_out_of_order_or_twice_refused():
    m1, m2 = _syn_moves()
    ok = lambda c: c in SYN.values()            # noqa: E731
    with pytest.raises(M.ManifestError, match="ORDER"):
        M.apply_moves("L-syn", {}, [m2, m1], merged=ok)
    with pytest.raises(M.ManifestError, match="ORDER"):
        M.apply_moves("L-syn", {}, [m1, m1], merged=ok)


# ---- adverse ---------------------------------------------------------------------------------------------------------
def test_stale_source_commit_refused():
    m1, m2 = _syn_moves()
    with pytest.raises(M.ManifestError, match="STALE_SOURCE"):
        M.apply_moves("L-syn", {}, [m1, m2], merged=lambda c: c == SYN["P-1"])
    bad = copy.deepcopy(M.PIECES)
    bad["T-527"]["merge"] = "0123456789abcdef0123456789abcdef01234567"     # not an object of this tree
    with pytest.raises(M.ManifestError, match="STALE_SOURCE"):
        M.check_sources(bad)


def _git(repo, *a):
    import subprocess
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env).stdout.decode().strip()


def test_unmerged_ready_piece_refused_as_source(monkeypatch, tmp_path):
    # a READY piece lives on its own branch, not merged: naming its commit as a source is refused. F-C-T536-1 (T-538):
    # the case is built on a SYNTHETIC repository (base commit on the working branch + one commit on a side branch, the
    # shape of every READY task branch), never on a live board commit that a later merge turns into an ancestor.
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    (repo / "f").write_text("base\n")
    _git(repo, "add", "f")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "-b", "agents/task-T-999")
    (repo / "f").write_text("piece\n")
    _git(repo, "commit", "-q", "-am", "READY piece")
    ready = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "work")
    monkeypatch.setattr(M, "ROOT", repo)
    assert M.in_tree(base) is True and M.in_tree(ready) is False      # a real object of the tree, not an ancestor
    M.check_sources({"T-998": {"merge": base[:8]}})                   # a merged source passes
    with pytest.raises(M.ManifestError, match="STALE_SOURCE"):
        M.check_sources({"T-999": {"merge": ready[:8]}})
    with pytest.raises(M.ManifestError, match="STALE_SOURCE"):
        M.check_sources({"T-998": {"merge": base[:8]}, "T-999": {"merge": ready}})


def test_edited_v1_manifest_refused(monkeypatch):
    monkeypatch.setitem(M.PINS, M.V1_JSON, "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.v1_manifest()
