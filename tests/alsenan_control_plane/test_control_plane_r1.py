"""ALSENAN CONTROL-PLANE AUDIT R1 - diagnostic tests (no production code is changed by this round).

Three groups:
  1. CHARACTERISATION - call the real lab functions on synthetic inputs and pin today's defective behaviour
     (D1-D6, the flooring / skirting / ceiling status, DRY-wins room class, PARTIAL release). They pass today; a fix
     that changes the behaviour must update them deliberately, together with the matching gate below.
  2. REGISTER / EVIDENCE INTEGRITY - the committed registers rebuild byte-identically from the committed evidence,
     every code anchor in SILENT_DROP_REGISTER still points at the line it names, and the headline numbers the review
     quotes (325.251 m2, 209.35 / 46.63 m, 1739.7 kg ...) are re-derived from the frozen registers independently.
  3. CONTROL GATES G01-G23 - what must be true after the fix rounds. Each is xfail(strict=True) with its defect id: it
     fails today (proving the defect) and an XPASS turns red, so the gate must be promoted when the defect is fixed.

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
import alsenan_v3_registers as V3R  # noqa: E402
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
def _finish_row(room, status, area=10.0, cls="DRY", name="ROOM", skirting=12.0):
    return {"room": room, "floor": "GF", "name_en": name, "name_ar": "", "room_class": cls, "status": status,
            "floor_area_m2": area, "floor_formula": "f", "floor_material": "PORCELAIN", "floor_material_authority": "A",
            "skirting_m": skirting, "ceiling_area_m2": area, "ceiling_formula": "c", "cornice_m": 12.0,
            "wall_tile_gross_m2": 20.0, "paint_blocked_length_m": 0.0}


def _L(rows):
    return {"finishes": {"rows": rows}, "rooms": {"rows": []}}


def _footing_ctx(defn, L=4.0, W=3.6, status="COMPUTED_SHADOW_COMPLETE", typ="FX"):
    defn = dict(defn, element="FOOTING", type=typ)
    return {"a3": {"rebar": {"definitions": [defn]},
                   "footings": {"rows": [{"type": typ, "status": status,
                                          "dims": {"L": {"m": L}, "W": {"m": W}}}]}}}


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
def test_c_flooring_status_is_computed_whatever_the_room_status():
    """registers.py:255 `"COMPUTED" if r["status"] == "COMPUTED" else "COMPUTED"` - both branches equal."""
    out = V3R.flooring(_L([_finish_row("R1", "COMPUTED_REVIEW"), _finish_row("R2", "BLOCKED")]))
    fl = [x for x in out if x["code"].startswith("F-FL-")]
    assert [x["status"] for x in fl] == ["COMPUTED", "COMPUTED"]


def test_c_skirting_and_ceiling_status_hardcoded_computed():
    L = _L([_finish_row("R1", "COMPUTED_REVIEW")])
    sk = [x for x in V3R.flooring(L) if x["code"].startswith("F-SK-")]
    ce = [x for x in V3R.ceilings(L) if x["code"].startswith("CE-R1")]
    assert sk[0]["status"] == "COMPUTED" and ce[0]["status"] == "COMPUTED"


def test_c_review_floor_reaches_the_v3b_total_as_urban_standard():
    lines = {ln["code"]: ln for ln in _frozen("registers_v3b/BOQ_LINES_V3B.json")["lines"]}
    z = lines["F-FL-GF-Z04"]["release"]
    assert z["technical"]["class"] == "URBAN_STANDARD" and z["technical"]["in_total"]
    assert z["commercial"]["procurement_eligible"] and z["commercial"]["confidence"] == "H"


def test_b_room_class_multi_name_dry_wins():
    assert V3L._room_class("PANTRY / SALOON / RECEPTION / Wash / DINING / GARDEN", "") == "DRY"
    assert V3L._room_class("DEWANEYA / Wash", "") == "DRY"
    assert V3L._room_class("Wash", "") == "WET"


def test_j_tile_wp_skips_a_dry_zone_with_a_wet_label():
    pytest.importorskip("engine.source.waterproofing_policy")
    dry = _finish_row("Z", "COMPUTED_REVIEW", cls="DRY", name="DEWANEYA / Wash")
    ctx = {"b2a": {"architecture": {"waterproofing": {"roof": []}}}}
    L = dict(_L([dry]), substructure={"footing_wp_m2": 1.0, "ground_beam_wp_m2": 1.0, "footing_membrane_m2": 1.0})
    out = V3R.tile_wp(ctx, L)
    assert not [x for x in out if x.get("trace") == "Z"]


def test_d_partial_enters_total_and_is_procurement_eligible():
    rel = RM.release("PARTIAL", 10.0)
    assert rel["technical"]["in_total"] and rel["commercial"]["procurement_eligible"]
    assert rel["commercial"]["method"] == "AS TECHNICAL" and rel["commercial"]["confidence"] == "H"


def test_d2_footing_per_metre_count_used_as_absolute_count():
    d = {"bars": {"long_bars": [{"count": 6, "dia_mm": 14, "per_m": True}],
                  "short_bars": [{"count": 6, "dia_mm": 14, "per_m": True}]}, "boxed": ["9 Ø 14/m"]}
    out = V3S.footing_rebar(_footing_ctx(d))
    bars = [x for x in out if x.get("status") != "BLOCKED"]
    assert sorted(x["count"] for x in bars) == [6, 6]                    # 6 bars over a 4.0 m footing, not 6 / m
    assert [x["why"] for x in out if x.get("status") == "BLOCKED"] == ["boxed bar shape not dimensioned"]


def test_d3_ff_empty_bar_definition_emits_nothing():
    out = V3S.footing_rebar(_footing_ctx({"bars": {}, "boxed": None}, typ="FF"))
    assert out == []                                                      # no rebar row and no BLOCKED row


def test_sd01_footing_skip_is_silent():
    d = {"bars": {"long_bars": [{"count": 6, "dia_mm": 12, "per_m": False}]}, "boxed": None}
    assert V3S.footing_rebar(_footing_ctx(d, status="BLOCKED")) == []


def test_d1_cb_measured_occurrence_emits_nothing():
    out = V3S.beam_rebar(_beam_ctx([BEAM_DEF], [_occ("CB1"), _occ("B1")]))
    assert out and all(" B1 " in x["ref"] for x in out)


def test_d4_strap_definition_filtered_out():
    strap = dict(BEAM_DEF, element="STRAP", type="SB1")
    assert V3S.beam_rebar(_beam_ctx([strap], [_occ("SB1")])) == []


def test_sd04_beam_without_length_is_silent():
    o = _occ("B1")
    o["lengths"] = {}
    assert V3S.beam_rebar(_beam_ctx([BEAM_DEF], [o])) == []


def test_sd11_side_bars_blocked_although_schedule_prints_them():
    out = V3S.beam_rebar(_beam_ctx([BEAM_DEF], [_occ("B1", D=75)]))
    side = [x for x in out if x["ref"].endswith("side bars")]
    assert side and side[0]["status"] == "BLOCKED" and "not printed" in side[0]["why"]
    printed = {r["beam"] for r in json.loads((CP / "evidence/ST7757_SCHEDULE_EXTRACT.json").read_text())["beam_remarks"]}
    assert len(printed) == 23 and {"B7", "B16", "B19", "B29"} <= printed


def test_d5_column_rebar_ignores_occurrence_state():
    defn = {"element": "COLUMN", "type": "C1", "bars": {"GROUND FLOOR": [{"count": 8, "dia_mm": 16}]}}
    row = {"type": "C1", "B_cm": 20.0, "D_cm": 50.0, "storey_band": "GROUND FLOOR", "floor": "GF",
           "tag_key": "X|H1|", "state": "NOT_DRAWN_ON_STOREY_SHEET", "volume_m3": None}
    ctx = {"a3": {"rebar": {"definitions": [defn]}}, "b2a": {"intervals": [{"from": "GF", "interval_m": 4.5}],
                                                              "columns": {"rows": [row]}}}
    out = V3S.column_rebar(ctx)
    assert {x["ref"].split()[-1] for x in out} == {"vertical", "ties"}


def test_d6_ground_zone_binds_the_smallest_containing_cell():
    src = (LAB / "alsenan_v3_structure.py").read_text().splitlines()
    assert "outer = min(hit, key=lambda p: p.area)" in src[107]
    g = _reg("STRUCTURAL_POPULATION_COVERAGE_REGISTER")["ground_zone_binding"]
    assert g["v3a_zone_1"]["outer_m2"] < g["footprints"][0]["area_m2"]


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


def test_mutation_room_status_does_not_reach_floor_status():
    """Metamorphic: mutate every room status; the floor line statuses must change if status were wired - they
    do not (the mutation is invisible), which is the defect pinned here."""
    rng = random.Random(1)
    rows = [_finish_row(f"R{i}", rng.choice(["COMPUTED", "COMPUTED_REVIEW", "BLOCKED"])) for i in range(30)]
    a = [x["status"] for x in V3R.flooring(_L(rows)) if x["code"].startswith("F-FL-")]
    for r in rows:
        r["status"] = "BLOCKED"
    b = [x["status"] for x in V3R.flooring(_L(rows)) if x["code"].startswith("F-FL-")]
    assert a == b == ["COMPUTED"] * 30


# =============================================================================================== 2. integrity
def test_registers_rebuild_identically_from_committed_evidence():
    regs = BR.build()
    for name in BR.REGISTERS:
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


def test_sd_code_anchors_hold():
    for r in _reg("SILENT_DROP_REGISTER")["rows"]:
        loc = r["code_location"]
        if not loc or ":" not in loc:
            continue
        path, line = loc.rsplit(":", 1)
        src = (ROOT / path).read_text().splitlines()
        window = "\n".join(src[int(line) - 2:int(line) + 1])
        assert r["anchor"] in window, (r["id"], loc)


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


# =============================================================================================== 3. control gates
def _xf(defect):
    return pytest.mark.xfail(strict=True, reason=f"control gate - fails until {defect} is fixed")


def _room_rows():
    return _reg("ROOM_SEMANTIC_TRADE_RELEASE_REGISTER")["rows"]


@_xf("C-1 flooring status")
def test_G01_no_review_room_floor_in_total():
    assert not [r for r in _room_rows() if "REVIEW_ROOM_FLOOR_IN_TOTAL" in r["flags"]]


@_xf("B-1 semantic zone not integrated")
def test_G02_unresolved_semantic_zone_is_blocked():
    assert not [r for r in _room_rows() if "TS01_UNRESOLVED_BUT_RELEASED" in r["flags"]]


@_xf("B-2 DRY wins")
def test_G03_multi_name_zone_with_wet_label_is_not_dry():
    assert V3L._room_class("DEWANEYA / Wash", "") != "DRY"


@_xf("J-1 wet labels lost")
def test_G04_every_wet_room_label_reaches_a_trade_region_or_blocked_row():
    assert _reg("ROOM_SEMANTIC_TRADE_RELEASE_REGISTER")["wet_rooms_lost"] == []


@_xf("C-2 skirting status hard-coded")
def test_G05_skirting_status_follows_room_status():
    sk = [x for x in V3R.flooring(_L([_finish_row("R1", "COMPUTED_REVIEW")])) if x["code"].startswith("F-SK-")]
    assert sk[0]["status"] != "COMPUTED"


@_xf("C-3 ceiling status hard-coded")
def test_G06_ceiling_status_follows_room_status():
    ce = [x for x in V3R.ceilings(_L([_finish_row("R1", "COMPUTED_REVIEW")])) if x["code"] == "CE-R1"]
    assert ce[0]["status"] != "COMPUTED"


@_xf("D-1 PARTIAL procurement-eligible")
def test_G07_partial_is_not_procurement_eligible_without_owner_approval():
    assert not RM.release("PARTIAL", 10.0)["commercial"]["procurement_eligible"]


@_xf("E-1 structural source coverage")
def test_G08_every_structural_source_object_consumed_or_not_relevant():
    bad = [r for r in _reg("STRUCTURAL_SOURCE_COVERAGE_REGISTER")["rows"]
           if r["state"] not in ("CONSUMED_COMPLETE", "NOT_RELEVANT")]
    assert not bad


@_xf("F-1 silent occurrences")
def test_G09_no_concrete_occurrence_dropped_silently():
    assert _reg("STRUCTURAL_POPULATION_COVERAGE_REGISTER")["silent_occurrences"] == 0


@_xf("D1 continuous beams")
def test_G10_cb_rebar_definitions_exist():
    defs = _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"]
    assert len({d["type"] for d in defs if d["type"].startswith("CB")}) == 13


@_xf("D2 two-layer footings")
def test_G11_two_layer_footing_respects_per_metre_and_both_layers():
    d = {"bars": {"long_bars": [{"count": 6, "dia_mm": 14, "per_m": True}],
                  "short_bars": [{"count": 6, "dia_mm": 14, "per_m": True}]}, "boxed": ["9 Ø 14/m"]}
    out = V3S.footing_rebar(_footing_ctx(d))
    assert all(x.get("status") != "BLOCKED" for x in out) and min(x["count"] for x in out) > 6


@_xf("D3 lift footing FF")
def test_G12_ff_emits_a_rebar_or_blocked_row():
    assert V3S.footing_rebar(_footing_ctx({"bars": {}, "boxed": None}, typ="FF"))


@_xf("D4 strap beams")
def test_G13_strap_beams_emit_rebar():
    strap = dict(BEAM_DEF, element="STRAP", type="SB1")
    assert V3S.beam_rebar(_beam_ctx([strap], [_occ("SB1")]))


@_xf("D5 rebar without concrete")
def test_G14_no_rebar_without_concrete():
    assert _reg("STRUCTURAL_POPULATION_COVERAGE_REGISTER")["d5_rebar_without_concrete"]["occurrences"] == 0


@_xf("D6 ground zone binding")
def test_G15_ground_zone_not_bound_by_minimum_area():
    assert "min(hit, key=lambda p: p.area)" not in (LAB / "alsenan_v3_structure.py").read_text()


@_xf("I-1 ambiguous wall bands")
def test_G16_ambiguous_wall_band_length_ends_in_a_row():
    assert _reg("WALL_LENGTH_CONSERVATION_REGISTER")["totals"]["ambiguous_m"] == 0


@_xf("I-2 unpaired boundary")
def test_G17_unpaired_topology_boundary_is_classified():
    assert _reg("WALL_LENGTH_CONSERVATION_REGISTER")["totals"]["topology_boundary_not_in_any_band_m"] == 0


@_xf("K-1 opening status")
def test_G18_no_v3a_opening_computed_with_blocked_height():
    assert not [r for r in _reg("OPENING_COMPLETENESS_REGISTER")["rows"]
                if "V3A_STATUS_COMPUTED_WITH_BLOCKED_HEIGHT" in r["flags"]]


@_xf("SD-12 duplicate schedule names")
def test_G19_duplicate_schedule_name_recorded_as_conflict():
    defs = [d for d in _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"] if d["type"] == "SB2"]
    assert "CONFLICT" in json.dumps(defs)


@_xf("SD-08 BOXED column")
def test_G20_boxed_column_parsed():
    defs = {d["type"]: d for d in _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"]}
    assert defs["F2"].get("boxed") is not None


@_xf("SD-11 side-bar remarks")
def test_G21_side_bar_remarks_consumed():
    defs = {d["type"]: d for d in _frozen("registers_a3/REBAR_EVIDENCE_REGISTER.json")["definitions"]}
    assert "side" in defs["B7"]["bars"]


@_xf("O-1 legacy CAD CLI")
def test_G22_user_cli_cannot_reach_legacy_adapter_without_deprecation_guard():
    rows = [r for r in _reg("LEGACY_CAD_REACHABILITY_REGISTER")["rows"] if r["path"].startswith("tools/")]
    assert all(r["state"] == "NOT_REACHABLE" or r["deprecation_guard"] for r in rows)


@_xf("SD-17 stair rebar")
def test_G23_stair_rebar_bound_to_typical_layout():
    pop = {r["population"]: r for r in _frozen("registers_v3b/REBAR_POPULATION_REGISTER.json")["rows"]}
    assert pop["STAIRS"]["blocked"] == 0
