"""T-604: WIRING MANIFEST V12 + OVERLAY DRY RUN (R-T604-1).

Synthetic villa K604 (not the training villa; hand values):
  arch A1 (K-1F OP-005) in a 0.20 wall, both ends masonry, both sides dry, deducted by the two room lines K-SK1 (12.000)
          and K-SK2 (4.000): jamb line 2 x 0.20 = 0.400 lm, its own line; room lines unchanged -> released 16.000 ->
          16.400 lm;
  passage P1 (K-GF OP-009): dry | wet -> its HELD-blank jamb line K-SKJ leaves the HELD sum as EXCLUDED (never 0);
  lift L1 (K-GF OP-003, framed) labelled PASSAGE on K-SK3: TEXT_ONLY, nothing moves;
  gate G-09 (no threshold line, gate leaf K-GL): step 3.000 lm x riser 0.20 = 0.600 m2 beside the leaf line; V10 rows
          D-1 1.000 / 0.150 and D-2 0.900 / 0.135 -> family 1.900 lm / 0.285 m2 nr 2 -> 4.900 lm / 0.885 m2 nr 3.
Adverse: a row from an unmerged task (and the T-599 joint citation), a wet side on a FIX_ROW, a jamb lm that is not ends
x depth, a missing wall depth, an existing jamb line, an NA row whose census status is not NOT_APPLICABLE, a gate step
already in V10, a riser m2 that is not payable x riser, a gate step with a threshold line, a family figure that differs
from the source: all refused. Then the training-villa build must be the rebuild and close by hand on the merged
T-601 / T-602 figures."""

import copy
import json
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t604"))
import manifest_v12 as M          # noqa: E402

M9, OV = M.M9, M.OV
MK = {"T-601": {"merge": "k601", "verdict": "K604 jamb verdict"}, "T-602": {"merge": "k602", "verdict": "K604 gate"}}


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


def _idx():
    L = [_line("L-" + "a" * 20, "FIN.SKIRTING", "lm", "K1F-RAAA:skirting", v=12.0),
         _line("L-" + "b" * 20, "FIN.SKIRTING", "lm", "SKIRT-T999:K1F-RBBB", v=4.0),
         _line("K-PA", "ARCH.PASSAGE", "pcs", "K1F-RAAA:OP-005", v=1.0),
         _line("K-SKJ", "FIN.SKIRTING", "lm", "SKIRT-T443:KGF-HALL:OP-009-JAMBS", cls="HELD"),
         _line("L-" + "c" * 20, "FIN.SKIRTING", "lm", "KGF-RCCC:skirting", v=20.0),
         _line("K-GL", "EXT.FENCE.GATE", "pcs", "FENCE:G-09:LEAF", cls="HELD")]
    return {l["line_id"]: l for l in L}


def _arch(**kw):
    c = {"opening": "A1 (engine 1F OP-005)", "kind": "DOORLESS", "status": "FIX_ROW", "sides": ["DRY", "DRY"],
         "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.2", "jamb_lm": "0.40", "fix_lm": "0.40",
         "engine_line": f"L-{'a' * 20} and L-{'b' * 20} (each deducts the arch)", "jamb_face_handles": ["K1", "K2"],
         "side_names": "room | dressing", "his_lm": "0.40", "evidence_ids": {}}
    c.update(kw)
    return c


def _na(**kw):
    c = {"opening": "P1 (engine GF OP-009)", "kind": "DOORLESS", "status": "NOT_APPLICABLE", "sides": ["DRY", "WET"],
         "ends": ["MASONRY_JAMB", "MASONRY_JAMB"], "wall_t_m": "0.2", "jamb_lm": "0", "fix_lm": None,
         "engine_line": "SKIRT-T443:KGF-HALL + HELD SKIRT-T443:KGF-HALL:OP-009-JAMBS", "side_names": "hall | wash",
         "evidence_ids": {}}
    c.update(kw)
    return c


def _lift():
    return {"opening": f"L1 lift landing door (engine 1F OP-003; T-296 kind PASSAGE on L-{'c' * 20})",
            "kind": "FRAMED", "status": "NO_JAMB_SKIRTING", "sides": [None, None], "jamb_lm": "0",
            "evidence_ids": {"panel_lines": ["P1", "P2"]}, "engine_line": None}


def _t601():
    return {"census": [_arch(), _na(), _lift()], "valued_fix_lm": "0.40",
            "fix_rows": [{"id": "FR-T601-1", "effect_lm": "0.40"},
                         {"id": "FR-T601-2", "line": "SKIRT-T443:KGF-HALL:OP-009-JAMBS (HELD)"}]}


def _door_rows():
    out = []
    for o, lm, m2 in (("D-1", "1", "0.15"), ("D-2", "0.9", "0.135")):
        out.append({"line_id": f"K-TH-{o}", "op_id": f"V10|{o}", "package": M.V10_DOOR,
                    "beside": {"opening": o, "step_lm_payable": lm, "riser_m2": m2, "nr": 1}})
    return out


def _t602(gate_lm="3.0", riser_m2="0.600"):
    def o(name, lm, r, m2, edge):
        return {"opening": name, "decision": "STEP", "payable_lm": lm, "riser_m": r, "riser_m2": m2, "nr": 1,
                "edge_pair": {"edge": edge, "companion": edge + "c"}, "levels_in": ["+0.20"], "levels_out": ["+0.00"]}
    return {"openings": [o("D-1", "1.0", "0.15", "0.150", "E1"), o("D-2", "0.9", "0.15", "0.135", "E2"),
                         o("G-09", gate_lm, "0.2", riser_m2, "E9")]}


# ---- normal cases (K604, by hand) ------------------------------------------------------------------------------

def test_jamb_line_is_its_own_line_room_lines_unchanged():
    idx = _idx()
    r, rooms = M.jamb_add(_arch(), idx, merged=MK)
    assert r["kind"] == "ADD" and r["line_id"] == "NEW:FIN.SKIRTING:SKIRT-T601:K1F-RAAA:OP-005-JAMBS"
    assert r["after"]["class"] == "RELEASED" and Decimal(str(r["after"]["measured_net"])) == Decimal("0.4")
    assert rooms == ["L-" + "a" * 20, "L-" + "b" * 20]
    after, rep = OV.apply(idx, [(M.P_JAMB, [r])])
    t0, t1 = OV.totals(idx), OV.totals(after)
    assert t0["FIN.SKIRTING|lm"]["released"] == "36" and t1["FIN.SKIRTING|lm"]["released"] == "36.4"
    assert all(after[k] == idx[k] for k in rooms)


def test_na_jamb_leaves_held_sum_as_excluded_never_zero():
    idx = _idx()
    r = M.jamb_na(_na(), idx, "SKIRT-T443:KGF-HALL:OP-009-JAMBS", merged=MK)
    assert r["kind"] == "SET" and r["after"]["class"] == "EXCLUDED" and r["after"]["measured_net"] is None
    after, _ = OV.apply(idx, [(M.P_JAMB, [r])])
    assert after["K-SKJ"]["class"] == "EXCLUDED"
    assert OV.totals(after)["FIN.SKIRTING|lm"]["released"] == OV.totals(idx)["FIN.SKIRTING|lm"]["released"]


def test_label_fix_moves_nothing():
    idx = _idx()
    rows = M.label_rows([_lift()], idx, merged=MK)
    assert [r["kind"] for r in rows] == ["TEXT_ONLY"] and rows[0]["after"] is None
    after, _ = OV.apply(idx, [(M.P_JAMB, rows)])
    assert after == idx


def test_package_order_and_totals():
    idx = _idx()
    (name, rows), _ = M.pkg_jambs(_t601(), idx, merged=MK)
    assert [r["row"] for r in rows] == ["FR-T601-1", "FR-T601-2", "FR-T601-3"]
    after, rep = OV.apply(idx, [(name, rows)])
    assert all(x["status"] == "APPLIED" for x in rep["rows"])
    sk = OV.totals(after)["FIN.SKIRTING|lm"]
    assert (sk["released"], sk["held_n"], sk["excluded_n"]) == ("36.4", 0, 1)


def test_gate_step_beside_leaf_and_family():
    idx = _idx()
    r, claim = M.gate_step(_t602(), idx, _door_rows(), opening="G-09", merged=MK)
    assert r["kind"] == "BESIDE" and r["line_id"] == "K-GL" and r["after"] is None and claim == "G-09:E9"
    assert r["beside"]["step_lm_payable"] == "3" and r["beside"]["riser_m2"] == "0.6"
    assert r["evidence"]["status"] == "DRAWING-CONFIRMED"
    fam = M.step_family(_t602(), _door_rows(), dict(r, package=M.P_GATE))
    assert (fam["lm"], fam["riser_m2"], fam["nr"]) == ("4.9", "0.885", 3)
    after, _ = OV.apply(idx, [(M.P_GATE, [r])])
    assert after == idx


# ---- adverse --------------------------------------------------------------------------------------------------

def test_unmerged_task_refused():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.jamb_add(_arch(), _idx(), merged={"T-602": MK["T-602"]})
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.gate_step(_t602(), _idx(), _door_rows(), opening="G-09", merged={"T-601": MK["T-601"]})


def test_t599_joint_citation_refused_while_unmerged():
    assert "T-599" not in M.MERGED
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.require_merged("T-599")
    j = M.joint_section()
    assert j["manifest_rows"] == 0 and "not MERGED" in j["refusal"]


@pytest.mark.parametrize("kw, msg", [
    ({"sides": ["DRY", "WET"]}, "both sides DRY"),
    ({"jamb_lm": "0.30", "fix_lm": "0.30"}, "!= 2 x"),
    ({"wall_t_m": None}, "HELD, never 0"),
    ({"ends": ["NIB_END", "CONTINUOUS"]}, "HELD, never 0"),
    ({"status": "OUTDOOR_SCOPE"}, "not a doorless FIX_ROW"),
    ({"engine_line": "none"}, "no room line"),
])
def test_jamb_add_adverse(kw, msg):
    with pytest.raises(M.ManifestError, match=msg):
        M.jamb_add(_arch(**kw), _idx(), merged=MK)


def test_existing_jamb_line_refused():
    idx = _idx()
    idx["K-OLD"] = _line("K-OLD", "FIN.SKIRTING", "lm", "SKIRT-T443:K1F-RAAA:OP-005-JAMBS", cls="HELD")
    with pytest.raises(M.ManifestError, match="already exists"):
        M.jamb_add(_arch(), idx, merged=MK)


def test_na_adverse():
    idx = _idx()
    with pytest.raises(M.ManifestError, match="only NOT_APPLICABLE"):
        M.jamb_na(_na(status="HELD"), idx, "SKIRT-T443:KGF-HALL:OP-009-JAMBS", merged=MK)
    with pytest.raises(M.ManifestError, match="without a wet side"):
        M.jamb_na(_na(sides=["DRY", "DRY"]), idx, "SKIRT-T443:KGF-HALL:OP-009-JAMBS", merged=MK)
    idx["K-SKJ"]["class"] = "RELEASED"
    idx["K-SKJ"]["measured_net"] = 0.4
    with pytest.raises(M.ManifestError, match="not HELD"):
        M.jamb_na(_na(), idx, "SKIRT-T443:KGF-HALL:OP-009-JAMBS", merged=MK)


def test_gate_adverse():
    rows = _door_rows()
    with pytest.raises(M.ManifestError, match="double count"):
        M.gate_step(_t602(), _idx(), rows, opening="D-1", merged=MK)
    with pytest.raises(M.ManifestError, match="payable x riser|!= 3"):
        M.gate_step(_t602(riser_m2="0.450"), _idx(), rows, opening="G-09", merged=MK)
    idx = _idx()
    idx["K-TH9"] = _line("K-TH9", "ARCH.THRESHOLD", "m2", "GF-THRESHOLD-G-09:strip", cls="HELD")
    with pytest.raises(M.ManifestError, match="threshold line exists"):
        M.gate_step(_t602(), idx, rows, opening="G-09", merged=MK)
    idx = _idx()
    del idx["K-GL"]
    with pytest.raises(M.ManifestError, match="0 gate leaf"):
        M.gate_step(_t602(), idx, rows, opening="G-09", merged=MK)


def test_family_figure_differs_refused():
    rows = _door_rows()
    rows[1]["beside"]["step_lm_payable"] = "1.0"
    r, _ = M.gate_step(_t602(), _idx(), _door_rows(), opening="G-09", merged=MK)
    with pytest.raises(M.ManifestError, match="D-2"):
        M.step_family(_t602(), rows, r)


# ---- training villa: rebuild + hand closure ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_committed_output_is_the_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_overlay_clean(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v11": 5124, "after_v12": 5125}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v11_overlay"] == []
    assert [f["package"] for f in o["flagged_rows"]] == ["T-498"]          # T-580's own NO_BEFORE, not a V12 row
    assert list(o["v12_vs_v11_totals"]) == ["FIN.SKIRTING|lm"]


def test_skirting_moves_only_by_t601(built):
    sk = built["skirting"]["FIN.SKIRTING|lm"]
    assert (sk["v11"]["released"], sk["v12"]["released"]) == ("209.428592", "209.728592")
    assert Decimal(sk["v12"]["released"]) - Decimal(sk["v11"]["released"]) == Decimal("0.3")     # 2 x 0.15
    assert (sk["v11"]["held_n"], sk["v12"]["held_n"], sk["v12"]["held_low"], sk["v12"]["held_high"]) == (7, 6, "0", "0")


def test_step_family_moves_only_by_g01(built):
    d = built["door_steps"]
    assert (d["v11_family"]["lm"], d["v11_family"]["riser_m2"], d["v11_family"]["nr"]) == ("4.8", "0.720", 5)
    assert (d["v12_family"]["lm"], d["v12_family"]["riser_m2"], d["v12_family"]["nr"]) == ("7.3", "1.095", 6)
    assert d["delta"] == {"lm": "2.5", "riser_m2": "0.375", "nr": 1}                         # 2.500 x 0.15
    assert d["his"]["ours_minus_his_lm"] == "-0.4" and d["edge_census"]["excluded_second_readings"] == []


def test_rows_and_supersessions(built):
    rows = {r["row"]: r for r in built["rows"]}
    assert set(rows) == {"FR-T601-1", "FR-T601-2", "FR-T601-3", "FR-T602-1"}
    assert set(built["sources_merged"]) == {"T-601", "T-602"}
    assert all(built["supersedes"][r["op_id"]] for r in built["rows"])
    assert built["joint"]["manifest_rows"] == 0
    assert built["stair_edge_census_after_v12"] == {"edges": 89, "doubles": 0, "orphans": 0}
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
