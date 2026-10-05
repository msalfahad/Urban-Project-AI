"""ALSENAN CONTROL-PLANE AUDIT R1 - diagnostic tests that still hold after Round 2.

Two groups:
  1. CHARACTERISATION - the frozen-data facts the round-1 review rests on (V3b release of the review floor, the V1
     release model, the A3 definition gaps) and seeded property tests.
  2. REGISTER / EVIDENCE INTEGRITY - the committed round-1 registers rebuild from the committed evidence (except the
     legacy-CAD reachability register, which scans live code that Round 2 deliberately changed) and the headline
     numbers the review quotes (325.251 m2, 209.35 / 46.63 m, 1739.7 kg ...) re-derive from the frozen registers.

Round 2 superseded the characterisation tests that pinned production defects and the R1 control gates G01-G23:
the fixed behaviour is asserted in test_control_plane_r2_gates.py, and research/alsenan_control_plane_02/registers/
GATE_TRANSITION_REGISTER.json lists every superseded test with the test that replaces it.

Property tests use a seeded random.Random (cad-ai-agent pattern) - no hypothesis dependency.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "research" / "external_engine_lab"
CP = ROOT / "research" / "alsenan_control_plane_01"
for p in (str(LAB), str(CP)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_v3_layers as V3L  # noqa: E402
import alsenan_v3_structure as V3S  # noqa: E402
import build_registers as BR  # noqa: E402
from engine.source import release_model as RM  # noqa: E402

REGS = CP / "registers"
FROZEN = ROOT / "tests" / "alsenan"


def _reg(name):
    return json.loads((REGS / f"{name}.json").read_text())


def _frozen(rel):
    return json.loads((FROZEN / rel).read_text())


# =============================================================================================== synthetic builders
def _beam_ctx(defs, occ):
    sheets = {fl: {"occurrences": []} for fl in V3S.FLOORS}
    sheets["GF"]["occurrences"] = occ
    return {"a3": {"rebar": {"definitions": defs}}, "b2a": {"sheets": sheets}}


def _occ(typ, state="MEASURED", B=30, D=50, Ls=5.0, Lc=4.6):
    return {"type": typ, "state": state, "B_cm": B, "D_cm": D, "tags": [f"X|H{typ}|"],
            "lengths": {"SUPPORT_CENTRELINE_LENGTH": Ls, "CLEAR_FACE_TO_FACE_LENGTH": Lc}}


BEAM_DEF = {"element": "BEAM", "type": "B1", "bars": {"top": [{"count": 2, "dia_mm": 12, "per_m": False}],
                                                      "bottom": [{"count": 3, "dia_mm": 16, "per_m": False}],
                                                      "stirrups": [{"count": 6, "dia_mm": 8, "per_m": False}]}}


# =============================================================================================== 1. characterisation


def test_c_review_floor_reaches_the_v3b_total_as_urban_standard():
    lines = {ln["code"]: ln for ln in _frozen("registers_v3b/BOQ_LINES_V3B.json")["lines"]}
    z = lines["F-FL-GF-Z04"]["release"]
    assert z["technical"]["class"] == "URBAN_STANDARD" and z["technical"]["in_total"]
    assert z["commercial"]["procurement_eligible"] and z["commercial"]["confidence"] == "H"


def test_d_partial_enters_total_and_is_procurement_eligible():
    rel = RM.release("PARTIAL", 10.0)
    assert rel["technical"]["in_total"] and rel["commercial"]["procurement_eligible"]
    assert rel["commercial"]["method"] == "AS TECHNICAL" and rel["commercial"]["confidence"] == "H"


def test_sd11_side_bars_blocked_although_schedule_prints_them():
    out = V3S.beam_rebar(_beam_ctx([BEAM_DEF], [_occ("B1", D=75)]))
    side = [x for x in out if x["ref"].endswith("side bars")]
    assert side and side[0]["status"] == "BLOCKED" and "not printed" in side[0]["why"]
    printed = {r["beam"] for r in json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["beam_remarks"]}
    assert len(printed) == 23 and {"B7", "B16", "B19", "B29"} <= printed


def test_sd12_sb2_duplicate_rows_one_kept_silently():
    rows = [r for r in json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["blocks"]["SBT"]
            if r["attributes"]["BEAM"] == "SB2"]
    assert sorted(r["attributes"]["W"] for r in rows) == ["100", "80"]
    defs = [d for d in _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"] if d["type"] == "SB2"]
    assert len(defs) == 1 and "conflict" not in json.dumps(defs).lower()


def test_sd08_boxed_column_unread():
    ft = json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["blocks"]["FT"]
    boxed = {r["attributes"]["FO-TY"] for r in ft if r["attributes"]["BOXED"]}
    assert boxed == {"F", "F2", "F3", "F4", "F5", "F6", "F7", "F9", "F10", "F11", "F15"}
    defs = {d["type"]: d for d in _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"]}
    assert all(defs[t].get("boxed") is None for t in boxed if t in defs)


def test_d1_cb_attributes_present_in_source_absent_in_definitions():
    s = json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["blocks"]
    cbs = s["C-BEAM2"] + s["C-BEAM3"]
    assert len(cbs) == 13 and all(r["attributes"]["BOT1-B"] and r["attributes"]["STR1-B"] for r in cbs)
    defs = _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"]
    assert not [d for d in defs if d["type"].startswith("CB")]


# ----------------------------------------------------------------------------------------- seeded property tests
def test_property_room_class_is_order_invariant():
    rng = random.Random(7757)
    names = ["PANTRY", "SALOON", "Wash", "DINING", "GARDEN", "BATH", "KITCHEN", "W.C", "LIVING AREA", "VOID"]
    for _ in range(60):
        pick = rng.sample(names, rng.randint(2, 5))
        base = V3L._room_class(" / ".join(pick), "")
        rng.shuffle(pick)
        assert V3L._room_class(" / ".join(pick), "") == base


def test_property_release_in_total_iff_technical_class_and_qty():
    rng = random.Random(42)
    for _ in range(200):
        cls = rng.choice(RM.TECH_IN_TOTAL + RM.TECH_OUT)
        q = rng.choice([None, round(rng.uniform(0, 500), 3)])
        t = RM.release(cls, q)["technical"]
        assert t["in_total"] == (cls in RM.TECH_IN_TOTAL and q is not None)


# =============================================================================================== 2. integrity
LIVE_CODE_REGISTERS = {"LEGACY_CAD_REACHABILITY_REGISTER"}     # scans tools/ - changed by the R2 legacy guard


def test_registers_rebuild_identically_from_committed_evidence():
    regs = BR.build()
    for name in BR.REGISTERS:
        if name in LIVE_CODE_REGISTERS:
            continue
        assert json.loads(json.dumps(regs[name], ensure_ascii=False)) == _reg(name), name


def test_index_hashes_match_committed_registers():
    import hashlib
    idx = json.loads((REGS / "INDEX.json").read_text())
    for name, h in idx["registers"].items():
        assert hashlib.sha256((REGS / f"{name}.json").read_bytes()).hexdigest() == h
    for name, h in idx["evidence"].items():
        assert hashlib.sha256((CP / "evidence" / name).read_bytes()).hexdigest() == h


def test_every_register_has_schema_rule_rows():
    for name in BR.REGISTERS:
        r = _reg(name)
        assert r["SCHEMA"].startswith("URBAN_ALSENAN_") and r["rule"] and r["rows"], name


def test_c_review_floor_is_325_251_independently():
    rooms = {r["id"]: r for r in _frozen("registers_v3/ROOM_REGISTER_V3.json")["rows"]}
    fin = _frozen("registers_v3/FINISH_REGISTER.json")["rows"]
    rev = sum(f["floor_area_m2"] for f in fin if rooms[f["room"]]["status"] != "COMPUTED")
    tot = sum(f["floor_area_m2"] for f in fin)
    assert round(rev, 2) == 325.25 and round(tot, 2) == 447.22


def test_i_wall_ledger_totals():
    t = _reg("WALL_LENGTH_CONSERVATION_REGISTER")["totals"]
    assert t["established_m"] == 209.35 and t["ambiguous_m"] == 46.63
    assert t["blockwork_counted_m"] == pytest.approx(t["established_excl_920_m"], abs=0.01)


def test_i_ambiguous_band_length_not_in_blockwork():
    for r in _reg("WALL_LENGTH_CONSERVATION_REGISTER")["rows"]:
        assert r["conservation"]["established_excl_920 - blockwork_counted"] == pytest.approx(0, abs=0.01)
        assert r["conservation"]["ambiguous_with_no_row"] == r["ambiguous_m"]


def test_j_unplaced_wet_labels():
    lost = _reg("ROOM_SEMANTIC_TRADE_RELEASE_REGISTER")["wet_rooms_lost"]
    assert sorted((x["floor"], x["label"], x["where"]) for x in lost) == [
        ("1F", "BATH", "NO_SITE"), ("1F", "W.C", "NO_SITE"), ("GF", "Wash", "GF-Z04"), ("GF", "Wash", "GF-Z06")]


def test_j_wet_label_in_dry_zone_gets_no_tile():
    rows = {r["room"]: r for r in _reg("ROOM_SEMANTIC_TRADE_RELEASE_REGISTER")["rows"]}
    for z in ("GF-Z04", "GF-Z06"):
        assert rows[z]["alsenan_room_class"] == "DRY" and rows[z]["release"]["wall_tile_T-WT"] is None


def test_e_every_schedule_block_has_a_state():
    reg = _reg("STRUCTURAL_SOURCE_COVERAGE_REGISTER")
    states = set(reg["states"])
    assert all(r["state"] in states for r in reg["rows"])
    sched = json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["blocks"]
    handles = set()
    for r in reg["rows"]:
        h = r.get("dxf_handle")
        handles.update(h if isinstance(h, list) else [h] if h else [])
    assert {b["handle"] for rows in sched.values() for b in rows} <= handles


def test_f_population_states_and_d5_magnitude():
    p = _reg("STRUCTURAL_POPULATION_COVERAGE_REGISTER")
    assert p["d5_rebar_without_concrete"]["occurrences"] == 26
    assert p["d5_rebar_without_concrete"]["kg"] == pytest.approx(1739.7, abs=0.2)
    assert p["counts"]["STRAP_BEAM"] == {"REBAR_BLOCKED": 3}
    assert p["counts"]["CONTINUOUS_BEAM"] == {"REBAR_BLOCKED": 11}


def test_o_legacy_adapter_reachability():
    rows = {r["entry_point"]: r for r in _reg("LEGACY_CAD_REACHABILITY_REGISTER")["rows"]}
    assert rows["Alsenan V3b (alsenan_v3b)"]["state"] == "NOT_REACHABLE"
    assert rows["RC1 Qortuba (rc1_qortuba)"]["state"] == "REACHABLE"
    assert rows["RC1 Qortuba (rc1_qortuba)"]["chain_module_level"][-2:] == [
        "research/external_engine_lab/r8_7_canonical.py", "engine/cad_adapter.py"]


def test_q_no_benchmark_is_source_truth():
    rows = _reg("BENCHMARK_CONFIDENCE_REGISTER")["rows"]
    assert not [r for r in rows if r["class"] == "VERIFIED_SOURCE_TRUTH"]
    cls = {r["benchmark"]: r["class"] for r in rows}
    assert cls["REBAR / ALL"] == "WEAK_HUMAN_REFERENCE" and cls["FLOOR / ALL"] == "STRONG_HUMAN_REFERENCE"


def test_scorecard_is_not_computed_from_benchmarks():
    src = (CP / "build_registers.py").read_text()
    body = src[src.index("def scorecard"):src.index("def build")]
    assert 'D["bench' not in body and "BENCHMARK_CONFIDENCE" not in body
