"""T-530: the WIRING MANIFEST (research/agents_t530/WIRING_MANIFEST_T530.json) is recomputed from the merged piece
outputs and must equal the committed file; hand checks on the figures, invariants (held never 0, one row per affected
line, no other line named), adverse cases (edited input, line that disagrees, wrong host) and the piece merges."""

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import manifest_t530 as M          # noqa: E402

A = pytest.approx
COMMITTED = M.OUT_JSON


def _committed():
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def offline():
    return M.build(drawing=False)


HAVE_DXF = M._dxf() is not None


@pytest.fixture(scope="module")
def full():
    if not HAVE_DXF:
        pytest.skip("private drawing not decoded in this checkout")
    m = M.build()
    # the rebuild is also left outside the repository, so a reviewer can diff it against the committed file
    (Path(tempfile.gettempdir()) / "t530_manifest_built.json").write_text(M.dumps(m), encoding="utf-8")
    return m


# ---- the committed manifest is the rebuild -------------------------------------------------------------------------
def test_full_manifest_equals_committed_file(full):
    assert M.dumps(full) == COMMITTED.read_text(encoding="utf-8")


def test_offline_sections_equal_committed_file(offline):
    c = _committed()
    for key in ("stream_S", "finish_v6_v7", "stale_bindings", "inputs", "pieces", "candidate"):
        assert json.loads(M.dumps(offline[key])) == c[key], key
    assert c["stream_F"]["drawing"]["drawing_read"] is True       # the committed file was built with the drawing
    assert offline["stream_F"]["drawing"]["drawing_read"] is False or HAVE_DXF
    for r in offline["stream_F"]["lines"]:                           # absent drawing: HELD, never a number, never 0
        if not offline["stream_F"]["drawing"]["drawing_read"]:
            assert r["after"]["state"] == "HELD" and "value" not in r["after"]


# ---- stream S: lintels ---------------------------------------------------------------------------------------------
def _lin(m, oid):
    return [r for r in m["stream_S"]["lintel_lines"] if r["element_id"] == f"LINTEL:{oid}"][0]


def test_sixteen_required_lintel_lines_one_row_each(offline):
    rows = offline["stream_S"]["lintel_lines"]
    assert len(rows) == 16 and len({r["line_id"] for r in rows}) == 16
    idx = M.line_index()
    for r in rows:
        assert idx[r["line_id"]]["item_code"] == "STR.CONC.LINTEL" and idx[r["line_id"]]["class"] == "RELEASED"
    states = [r["after"]["state"] for r in rows]
    assert states.count("BOUNDED_MIN_BEARING") == 6 and states.count("HELD_BY_NAME") == 10


def test_bearing_ok_lintel_by_hand(offline):
    w14 = _lin(offline, "W14")                  # B 0.20 (wall), D 0.30 (L3), L 3.25 .. 2.45 + 0.618 + 1.032 = 4.10
    assert w14["before"]["value"] == A(0.195)
    assert w14["after"]["low"] == A(0.20 * 0.30 * 3.25) and w14["after"]["high"] == A(0.20 * 0.30 * 4.10)
    d201 = _lin(offline, "D-2F-01")             # pier >= 3.0 m, no ceiling: the high stays HELD, never the low
    assert d201["after"]["low"] == A(0.054) and d201["after"]["high"] is None and d201["after"]["high_reason"]


def test_deficit_lintel_by_hand_and_pair_once(offline):
    g6 = _lin(offline, "D-GF-06")               # 0.20 x 0.20 x [1.00 + 0.40 + 0, 1.00 + 0.40 + 0.14] (T-524)
    assert g6["after"]["bound_m3"] == [A(0.04 * 1.40), A(0.04 * 1.54)]
    assert g6["after"]["low"] is None and g6["after"]["high"] is None
    a, b = _lin(offline, "D-GF-11"), _lin(offline, "D-GF-12")
    assert a["after"]["pair"] == b["after"]["pair"] == ["D-GF-11", "D-GF-12"]
    assert a["after"]["pair_carried_on"] == "D-GF-11" and a["after"]["pair_bound_m3"] == [A(0.06), A(0.07914)]
    assert "bound_m3" not in a["after"] and "bound_m3" not in b["after"]          # the pair bound is carried once


def test_lintel_code_view_conserves(offline):
    v = offline["stream_S"]["lintel_code_view"]
    assert v["before_released"] == A(1.016)                      # T-487 16 REQUIRED
    assert v["after"]["valued_lines"] == 0 and v["after"]["at_least_m3"] == A(0.502 + 0.372692)
    assert v["removed_from_b9_02_m3"] == A(0.514 - 0.437542)
    assert sum(v["removed_owner"].values()) == A(v["removed_from_b9_02_m3"])
    assert v["after"]["upper_held_lines"] == ["LINTEL:D-2F-01"]


# ---- stream S: host faces, groups ----------------------------------------------------------------------------------
def _host(m, lid):
    return [h for h in m["stream_S"]["host_material_lines"] if h["host_line_id"] == lid][0]


def test_host_faces_by_hand(offline):
    hs = offline["stream_S"]["host_material_lines"]
    assert {h["host_line_id"] for h in hs} == {"L-2fdc0f971a94348ec855", "L-a3f88ecda2402f67c500"}
    g = _host(offline, "L-a3f88ecda2402f67c500")       # 5.59 m2 - D-GF-06 face 0.20 x [1.40, 1.54], 4.5 kg / m2
    assert g["before"]["kg"] == A(23.535)
    assert g["after"]["material_base_range_m2"] == [A(5.59 - 0.308), A(5.59 - 0.28)]
    assert g["after"]["kg_range"] == [A((5.59 - 0.308) * 4.5), A((5.59 - 0.28) * 4.5)]
    f = _host(offline, "L-2fdc0f971a94348ec855")       # W14 [0.975, 1.23], W15 [0.47, 0.5674], W18 0.2 x 0.8673
    hi = 101.976 - (0.975 + 0.47 + 0.2 * 0.8673)
    lo = 101.976 - (1.23 + 0.2 * 2.837 + 0.2 * 0.8673) - 1.5
    assert f["after"]["material_base_range_m2"] == [A(lo, abs=2e-6), A(hi, abs=2e-6)]
    assert f["before"]["kg_range"] == [A(444.4695), A(451.2195)]
    for h in hs:
        assert h["t498_stage_line"] and h["rule_gap"].startswith("RG-1")


def test_glue_group_moves_only_by_the_two_hosts(offline):
    g = offline["stream_S"]["glue_group"]
    assert g["before"]["at_least"] == [A(35.42625), A(36.19665)]
    d_lo = sum(h["after"]["kg_range"][0] - (h["before"]["kg"] or h["before"]["kg_range"][0])
               for h in offline["stream_S"]["host_material_lines"]) / 25
    d_hi = sum(h["after"]["kg_range"][1] - (h["before"]["kg"] or h["before"]["kg_range"][1])
               for h in offline["stream_S"]["host_material_lines"]) / 25
    assert g["after"]["at_least"] == [A(35.42625 + d_lo, abs=2e-6), A(36.19665 + d_hi, abs=2e-6)]
    assert g["after"]["status"] == "HELD"


def test_perimeter_lines_and_cement_group(offline):
    p = offline["stream_S"]["perimeter_lines"]
    assert len(p) == 2 and {r["host_line_id"] for r in p} == {"L-1c53fadb2f92d1f36d4e", "L-10dd62f66ad05488e63b"}
    gf = [r for r in p if r["host_line_id"] == "L-1c53fadb2f92d1f36d4e"][0]
    assert gf["walls"] == ["GF-W01"] and gf["after"]["value"] == A(0.058854)
    f1 = [r for r in p if r["host_line_id"] == "L-10dd62f66ad05488e63b"][0]
    assert f1["walls"] == ["1F-W02", "1F-W03", "1F-W09"] and f1["after"]["value"] == A(0.008318 + 0.020618 + 0.010355)
    assert sum(r["after"]["value"] for r in p) == A(0.098145)
    assert sum(r["after"]["cement_bags_beside"] for r in p) == A(0.098145 * 8, abs=2e-6)
    assert f1["t526_confirms"][0]["t526_after_m3"] == A(f1["t526_confirms"][0]["t520_wall_m3"])
    c = offline["stream_S"]["cement_group"]
    assert c["before"]["at_least"] == [A(130.816567), A(172.286014)]
    assert c["after"]["at_least"] == [A(130.816567 + 0.78516, abs=2e-6), A(172.286014 + 0.78516, abs=2e-6)]
    assert c["after"]["status"] == "HELD"


def test_stale_bindings(offline):
    s = offline["stale_bindings"]
    assert s["stale_on_v3_0_57_carried"]["count"] == 21 and len(s["stale_on_v3_0_57_carried"]["lines"]) == 7
    assert s["lintel_bindings_without_line"]["count"] == 60 and s["lintel_bindings_without_line"]["unmapped"] == []
    assert len(s["go_stale_by_this_wiring"]) == 16 + 4


# ---- stream F (drawing) ---------------------------------------------------------------------------------------------
def test_poolcourt_lines(full):
    f = {r["line_id"]: r for r in full["stream_F"]["lines"]}
    assert f["L-1954878bb02c91139e1b"]["after"] == {"state": "MEASURED", "value": A(0.500002), "m2_at_0_20": A(0.1)}
    assert f["L-d7d1bf8c5991ccf69ea2"]["after"]["held_high"] == A(0.250804 + 0.300810)
    assert f["L-2361d6ec13c952bd2ae3"]["after"]["held_high"] == A(0.639573)
    add = full["stream_F"]["added_lines"]
    assert len(add) == 9
    fin = [a for a in add if a["item_code"] == "FIN.ROOF.FINISH" and a["after"]["value"] is not None]
    assert len(fin) == 1 and fin[0]["after"]["value"] == A(4.519172)
    cv = full["stream_F"]["code_views"]
    assert cv["FIN.WP.ROOF_UPTURN"]["released_before"] == A(186.782544)
    assert cv["FIN.WP.ROOF_UPTURN"]["released_after"] == A(187.282546)
    assert cv["FIN.ROOF.FINISH"]["released_after"] == A(202.21976 + 4.519172)
    for code in ("FIN.ROOF.SCREED", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.WP.DOORWAY_TRANSITION"):
        assert cv[code]["released_after"] is None and cv[code]["view_after"].startswith("HELD")   # never 0.0
    tr = [a for a in add if a["item_code"] == "FIN.WP.DOORWAY_TRANSITION"][0]
    assert tr["unit"] == "m2" and tr["after"]["value"] is None and tr["after"]["length_beside_lm"] == A(2.976663)
    c1 = [c for c in full["conflicts"] if c.get("conflict") == "C-F1"][0]
    assert c1["upstand_lm_after"] == A(5.193544 + 0.500002)


# ---- FINISH V6 / V7 -------------------------------------------------------------------------------------------------
def test_finish_v6_reader_and_v7_conflict(offline):
    v = offline["finish_v6_v7"]
    assert v["candidate_lines_moved"] == 0
    assert v["v6_tile_bed"]["reader_rows"] == 88 and v["v6_tile_bed"]["max_abs_diff"] < 1e-5
    s = v["v7_stair_bed"]
    assert s["keys_computed"] == 11 and s["installed_agrees"]
    assert s["installed_cement_bags"] == A(10.178704) and s["mortar_m3_from_cement"] == A(10.178704 / 9.576)
    assert s["procurement_stair_bed_v1_bags"] != A(s["procurement_v7_q45_bags"])     # two figures: HELD by ruling


# ---- invariants -----------------------------------------------------------------------------------------------------
def _all_rows(m):
    S, F = m["stream_S"], m["stream_F"]
    return S["lintel_lines"] + S["host_material_lines"] + S["perimeter_lines"] + F["lines"] + F["added_lines"]


def test_held_never_zero_and_named(offline):
    for r in _all_rows(offline):
        a = r["after"]
        if "HELD" in a["state"]:
            assert a.get("value") in (None,) and a.get("why") or a.get("missing") or a.get("pair"), r
        for k in ("value", "low", "high"):
            assert a.get(k) != 0.0, r


def test_only_the_affected_codes_are_named(offline):
    codes = {r["item_code"] for r in _all_rows(offline) if "item_code" in r}
    assert codes <= {"STR.CONC.LINTEL", "MAS.MORTAR.BLACK", "FIN.WP.ROOF_UPTURN", "FIN.WP.ROOF",
                     "FIN.WP.DOORWAY_TRANSITION", "FIN.ROOF.SCREED", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION",
                     "FIN.ROOF.FINISH"}
    assert offline["released_quantities_changed"] == 0 and offline["candidate_files_touched"] == 0


def test_every_piece_is_merged_in_this_tree():
    for t, p in M.PIECES.items():
        r = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", p["merge"], "HEAD"],
                           capture_output=True)
        assert r.returncode == 0, f"{t} merge {p['merge']} is not in this tree"


# ---- adverse ---------------------------------------------------------------------------------------------------------
def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(M.PINS, M.T516_OUT, "0" * 64)
    with pytest.raises(M.ManifestError, match="PIN"):
        M.lintel_rows(M.line_index())


def test_candidate_line_that_disagrees_with_the_ledger_refused():
    idx = copy.deepcopy(M.line_index())
    lid = [k for k, l in idx.items() if l["element_id"] == "LINTEL:W14"][0]
    idx[lid]["measured_net"] = 0.200
    with pytest.raises(M.ManifestError, match="not the T-453"):
        M.lintel_rows(idx)


def test_required_lintel_without_valued_line_refused():
    idx = copy.deepcopy(M.line_index())
    lid = [k for k, l in idx.items() if l["element_id"] == "LINTEL:D-GF-13"][0]
    idx[lid]["class"] = "HELD"
    with pytest.raises(M.ManifestError, match="without a valued"):
        M.lintel_rows(idx)


def test_perimeter_on_a_held_host_refused():
    idx = copy.deepcopy(M.line_index())
    idx["L-1c53fadb2f92d1f36d4e"]["class"] = "HELD"
    with pytest.raises(M.ManifestError, match="not a valued MAS.BLOCK"):
        M.perimeter_rows(idx)
