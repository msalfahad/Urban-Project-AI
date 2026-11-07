"""T-609: reconciled-quantities statement V10 (T-602 door-step split, T-606 room-outline split, T-180 pack evidence,
T-597 B1 plan side beside, F-T606-1 pending beside). Synthetic villa "S609" (not the training villa) by hand for
R-T609-1 with adverse cases (parts not re-adding, an omission not drawing-confirmed, a manifest family that is not V11 +
the omitted step, a pack mark not AGREE, pack marks not re-adding, a pack setting a class, a pack on a row already
verified, a merged class changed, a % beside HELD, a blank plan without HELD), then the merged training-villa sources
(committed research outputs only; no private input): V9 carried byte-equal, the 2.90 -> 2.50 + 0.40 split, the 1F
living -8.66 split, two evidence moves and no class move from the packs, NOT_COMPARABLE kept, nothing applied."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t609"))
import t609_adapters as A  # noqa: E402
import t609_build as B  # noqa: E402

Dd = Decimal
E = A.StatementError


# ------------------------------------------------------------------------------- S609 door steps by hand ----------
# S609: his 3 step pieces 5.0 lm; our V11 family D1 1.0 + D2 1.0 = 2.0 lm (2 nr, riser 0.30 m2). Section: reference
# 12.0, engine 8.0 -> +4.0 = door-step UNRESOLVED +3.0 (5.0 - 2.0) + WET +1.0. The merged report found gate G-9 drawn
# (2.4 lm, riser 0.15 -> 0.36 m2) with no line: +3.0 = 2.4 ENGINE_OMISSION + 0.6 UNRESOLVED; ours 4.4 lm / 3 nr.
def _st9(delta="3.0"):
    rows = [{"name": "EXT: his 3 door-step pieces 5.0 lm vs our 2 step elements 2.0 lm", "delta": delta,
             "class": "UNRESOLVED", "unit": "lm", "evidence_status": A.PV, "kind_of_cause": "SCOPE"},
            {"name": "WET: strips", "delta": "1.0", "class": "ENGINE_RIGHT", "unit": "lm", "evidence_status": A.WP}]
    sec = {"section_id": "S609/marble-lm@V8", "unit": "lm", "reference_total": "12.0", "engine_valued": "8.0",
           "difference": "4.0", "difference_pct_of_reference": None, "rows": rows,
           "beside": {"door_steps_t592": {"element": "stone in the wall gap"}}}
    return {"sections_v8": [sec], "supersedes_v8": {"T-577/marble-lm": "S609/marble-lm@V8"}}


def _d602(om="2.4", res="0.6", status="DRAWING-CONFIRMED"):
    steps = [{"opening": "D1", "lm": "1.0", "riser_m": "0.15", "riser_m2": "0.150"},
             {"opening": "D2", "lm": "1.0", "riser_m": "0.15", "riser_m2": "0.150"},
             {"opening": "G-9", "lm": "2.4", "riser_m": "0.15", "riser_m2": "0.360"}]
    return {"sign": "ours - his", "his": {"lm": "5.0", "nr": 3},
            "fix_rows": [{"id": "FR-S609-1", "row": "external step at the gate G-9: 2.4 lm"}],
            "reconciliation": {"v8_before": {"unresolved_lm": "3.0"}, "residual_lm": "-" + res, "ours_lm": "4.4",
                               "ours_nr": 3, "ours_riser_m2": "0.660", "ours_steps": steps,
                               "v8_unresolved_split": [
                                   {"part": "G-9 gate step (ENGINE_OMISSION: drawn pair)", "lm": om, "status": status},
                                   {"part": "residual", "lm": res, "status": "UNRESOLVED",
                                    "candidate_causes_not_attributed": ["D1 block +0.1"]}]}}


def _d604(dl="2.4", riser="0.360"):
    return {"door_steps": {"v11_family": {"lm": "2.0", "nr": 2, "riser_m2": "0.300"},
                           "delta": {"lm": dl, "nr": 1, "riser_m2": riser},
                           "v12_family": {"by_opening": [{"opening": "D1", "lm": "1.0"}, {"opening": "D2", "lm": "1.0"},
                                                         {"opening": "G-9", "lm": "2.4"}]}}}


def test_s609_door_step_split_by_hand():
    sec, mv = A.t602_marble_lm(_st9(), _d602(), _d604(), "v")
    assert sec["section_id"] == "S609/marble-lm@V10" and sec["restates"] == "S609/marble-lm@V8"
    assert (sec["reference_total"], sec["engine_valued"], sec["difference"]) == ("12.0", "8.0", "4.0")
    parts = [(r["class"], Dd(r["delta"]), r["evidence_status"]) for r in sec["rows"] if r.get("tag") == A.TAG_STEP]
    assert parts == [("ENGINE_WRONG", Dd("2.4"), A.CV), ("UNRESOLVED", Dd("0.6"), A.PV)]
    assert Dd(sec["closure_residual"]) == 0
    assert [(m["from"], m["to"], m["delta"]) for m in mv] == [("UNRESOLVED", "ENGINE_WRONG", "2.4")]
    ds = sec["beside"]["door_steps_t602"]
    assert ds["count"].startswith("his 3 = ours 3") and ds["pct"] is None
    assert ds["manifest_family_v11_to_v12"]["lm"] == ["2.0", "4.4"]
    om = [r for r in sec["rows"] if r.get("kind_of_cause") == "ENGINE_OMISSION"][0]
    assert om["when_wired"].startswith("HELD point bound")        # (e) stone unprinted: HELD when wired, not valued


def test_s609_parts_not_readding_refused():
    with pytest.raises(E, match="re-add"):
        A.t602_marble_lm(_st9(), _d602(res="0.5"), _d604(), "v")


def test_s609_before_not_the_row_refused():
    with pytest.raises(E, match="v8_before"):
        A.t602_marble_lm(_st9(delta="2.9"), _d602(), _d604(), "v")


def test_s609_omission_not_drawing_confirmed_refused():
    with pytest.raises(E, match="DRAWING-CONFIRMED ENGINE_OMISSION"):
        A.t602_marble_lm(_st9(), _d602(status="ASSUMED"), _d604(), "v")


def test_s609_manifest_family_not_v11_plus_step_refused():
    with pytest.raises(E, match="V11 \\+ the omitted step"):
        A.t602_marble_lm(_st9(), _d602(), _d604(riser="0.375"), "v")


# ------------------------------------------------------------------------------- S609 packs by hand ---------------
# S609 beams: RUN -1.5 (ENGINE_RIGHT, WP; marks M1 1.2 + M2 0.3), JOINT 0.3 (UNRESOLVED, WP), COUNT -2.0 (CV).
def _beams():
    rows = [{"name": "GF: RUN", "delta": "-1.5", "class": "ENGINE_RIGHT", "unit": "m3", "evidence_status": A.WP},
            {"name": "GF: JOINT", "delta": "0.3", "class": "UNRESOLVED", "unit": "m3", "evidence_status": A.WP},
            {"name": "GF: COUNT", "delta": "-2.0", "class": "ENGINE_RIGHT", "unit": "m3", "evidence_status": A.CV}]
    return {"section_id": "S609/beams@V9", "unit": "m3", "rows": rows}


def _pack(marks=None, state="FULL", row="GF: RUN", **extra):
    cov = {"state": state, "marks": marks or {"M1": ("1.2", "AGREE"), "M2": ("0.3", "AGREE")}, **extra}
    return [{"pack": "PX", "verdict": "v", "rows": {row: cov}}]


def test_s609_pack_promotes_evidence_only():
    am, mv = A.pack_amends(_beams(), _pack())
    assert list(am) == ["GF: RUN"] and am["GF: RUN"]["evidence"] == A.CV
    assert "class" not in am["GF: RUN"]["set"] and "delta" not in am["GF: RUN"]["set"]
    assert [(m["from"], m["to"], m["class"], m["delta"]) for m in mv] == [(A.WP, A.CV, "ENGINE_RIGHT", "-1.5")]


def test_s609_pack_mark_not_agree_refused():
    with pytest.raises(E, match="not AGREE"):
        A.pack_amends(_beams(), _pack({"M1": ("1.2", "AGREE"), "M2": ("0.3", "+3 %")}))


def test_s609_pack_marks_not_readding_refused():
    with pytest.raises(E, match="re-add"):
        A.pack_amends(_beams(), _pack({"M1": ("1.2", "AGREE"), "M2": ("0.2", "AGREE")}))


def test_s609_pack_may_not_set_a_class():
    with pytest.raises(E, match="may not set"):
        A.pack_amends(_beams(), _pack(**{"class": "ENGINE_WRONG"}))


def test_s609_pack_on_verified_row_refused_and_partial_moves_nothing():
    with pytest.raises(E, match="already CHECKER_VERIFIED"):
        A.pack_amends(_beams(), _pack({"M": ("2.0", "AGREE")}, row="GF: COUNT"))
    for st in ("PARTIAL", "NOT_READ", "ENGINE_WRONG_FINDING"):
        assert A.pack_amends(_beams(), _pack(state=st)) == ({}, [])
    with pytest.raises(E, match="recorded as already verified"):
        A.pack_amends(_beams(), _pack(state="ALREADY_VERIFIED"))


def test_pct_beside_held_refused():
    sec = {"section_id": "S", "difference_pct_of_reference": "3.1", "rows": [{"class": "HELD"}]}
    with pytest.raises(E, match="HELD"):
        A._no_pct_beside_held(sec)


# ------------------------------------------------------------------------------- training villa ------------------
@pytest.fixture(scope="module")
def st():
    return B.build()


@pytest.fixture(scope="module")
def st9():
    return B.v9_statement()


def _sec(st, sid):
    return [c for c in st["sections_v10"] if c["section_id"] == sid][0]


def test_rebuild_identical(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_v9_byte_equal(st, st9):
    B.check_v9_unchanged(st, st9)
    bad = copy.deepcopy(st)
    bad["sections_v9"][0]["rows"][0]["delta"] = "999"
    with pytest.raises(E, match="V9 key sections_v9 changed"):
        B.check_v9_unchanged(bad, st9)


def test_door_steps_290_split(st):
    c = _sec(st, "T-577/marble-lm@V10")
    parts = [(r["class"], r["delta"], r["evidence_status"], r.get("kind_of_cause")) for r in c["rows"]
             if r.get("tag") == A.TAG_STEP]
    assert parts == [("ENGINE_WRONG", "2.5", A.CV, "ENGINE_OMISSION"), ("UNRESOLVED", "0.4", A.PV, "SCOPE")]
    assert Dd(c["closure_residual"]) == 0 and c["engine_valued"] == "56.83" and c["difference"] == "-35.13"
    assert not any(r["class"] == "UNRESOLVED" and Dd(r["delta"]) == Dd("2.9") for r in c["rows"])
    ds = c["beside"]["door_steps_t602"]
    assert (ds["ours_lm"], ds["ours_nr"], ds["his_minus_ours_lm"], ds["pct"]) == ("7.3", 6, "0.4", None)


def test_room_outline_split(st):
    c = _sec(st, "T-574/skirting-room@V10")
    parts = [(r["class"], r["delta"], r["evidence_status"]) for r in c["rows"] if r.get("tag") == A.TAG_ROOM]
    assert parts == [("ENGINE_RIGHT", "-8.40", A.CV), ("ENGINE_WRONG", "-0.20", A.WP), ("UNRESOLVED", "-0.06", A.PV)]
    assert c["by_class"]["UNRESOLVED"] == "18.293234"          # T-606 'unresolved -18.293234' in its own sign
    assert c["engine_valued"] == "197.278592"                   # F-T606-1 not applied (R-T609-1 (c))


def test_merged_class_changed_refused(st9):
    d = A.load(A.T606_JSON)
    d = copy.deepcopy(d)
    d["rooms"][0]["causes"][1]["verdict"] = "ENGINE_RIGHT"       # LIV-VOID promoted beyond its verdict
    with pytest.raises(E, match="merged class"):
        A.t606_skirting_room(st9, d)


def test_packs_move_evidence_not_class(st, st9):
    old = A.section_of_record(st9, "T-545/beams")
    new = _sec(st, "T-545/beams@V10")
    assert [(r["name"], r["class"], r["delta"]) for r in old["rows"]] == \
        [(r["name"], r["class"], r["delta"]) for r in new["rows"]]
    moved = {m["row"]: (m["from"], m["to"], m["pack"]) for m in st["evidence_shift_v10"]}
    assert moved == {"2F: THROUGH_SUPPORT": (A.WP, A.CV, "P02 2F"), "1F: RUN_COUNT": (A.WP, A.CV, "P03 1F")}
    by = {r["name"]: r for r in new["rows"]}
    assert by["2F: THROUGH_SUPPORT"]["class"] == "UNRESOLVED"            # joint pointer: T-599 r2 not merged
    assert by["GF: RUN_COUNT"]["evidence_status"] == A.WP                # F-C-P03-2 finding: not promoted
    assert by["1F: THROUGH_SUPPORT"]["evidence_status"] == A.WP          # P02 1F partial
    assert "T-545/beams@V10" not in json.dumps(st["class_shift_v10"])


def test_class_moves_per_unit(st):
    assert st["class_shift_v10"] == {"lm": {"UNRESOLVED -> ENGINE_RIGHT": {"n": 1, "signed": "-8.40", "gross": "8.40"},
                                            "UNRESOLVED -> ENGINE_WRONG": {"n": 2, "signed": "2.30", "gross": "2.70"}}}


def test_no_pct_and_units_apart(st):
    for c in st["sections_v10"]:
        assert c["difference_pct_of_reference"] is None
        assert all(r["unit"] == c["unit"] for r in c["rows"])
    bad = copy.deepcopy(_sec(st, "T-545/beams@V10")["rows"])
    bad[0]["unit"] = "t"
    with pytest.raises(E, match="summed into a m3 headline"):
        A.A7.by_class_evidence(bad, "m3", lambda r: A.CV)


def test_b1_plan_side_beside(st):
    b = [x for x in st["beside_v10"] if x["block_id"] == "T-597/b1-plan-side@V10"][0]
    assert b["pct"] is None and b["his"] == "NO_ROW" and b["valued"] == "0"
    z = b["pits_zone_m2"]
    assert (z["union"], z["own_in_plot"], z["overlap_drawn_F_C_T597_1"]) == ("129.234375", "124.648614", "0.195625")
    held = [r for r in b["plan_rows"] if r["plan_m2"] is None]
    assert len(held) == 2 and all("HELD" in r["plan_status"] for r in held)
    assert "min_mm" not in json.dumps(st["beside_v10"])                     # no coordinates
    nc = [x for x in st["not_comparable"] if x["block_id"] == "T-565/earthworks"][0]
    assert all(f["class"] == "NOT_COMPARABLE" for f in nc["families"])


def test_blank_plan_without_held_refused(st9):
    d = copy.deepcopy(A.load(A.T597_JSON))
    d["b1_rows"][3]["plan_status"] = "measured"
    with pytest.raises(E, match="never 0"):
        A.t597_beside(st9, d)


def test_pending_fix_beside(st):
    b = [x for x in st["beside_v10"] if x["block_id"] == "T-606/F-T606-1@V10"][0]
    assert b["applied"] is False and b["valued"] == "0" and b["checker_lm"] == "11.170"
    assert b["candidate_v3_0_58"] == {"before": "209.428592", "after_if_wired": "198.258592"}
    assert b["after_manifest_v12"] == {"before": "209.728592", "after_if_wired": "198.558592"}


def test_nothing_released(st):
    assert st["released_quantities_changed"] == 0
    assert all(x["candidate_line"] is False for x in st["beside_v10"])
