"""Alsenan S3.1: column corrections and the post-freeze multi-engine comparison package.

Checks the committed outputs: S3.1 headline split, transitions blocked, one unit-mass method, S3 untouched; the
comparison was built after the production freeze; the freelancer lineage sums back to every summary cell; scope notes
exist where the label hides scope; no percentage on a NOT_COMPARABLE row; the rough profile is the engine profile;
the population list is complete. Values are read from the registers, never typed here."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / "research" / "alsenan_column_rebar_s3"
S31 = ROOT / "research" / "alsenan_column_rebar_s3_1"
CMP = ROOT / "research" / "alsenan_multi_engine_comparison"

from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import rough_rebar_sanity as RR  # noqa: E402
from engine.source import structural_population_discovery as SPD  # noqa: E402


def J(d, name):
    return json.loads((d / name).read_text(encoding="utf-8"))


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------------ S3.1 columns
def test_s3_1_outputs_indexed_and_s3_untouched():
    idx = J(S31, "INDEX.json")
    for k, h in idx["outputs"].items():
        assert _h(S31 / k) == h
    assert idx["s3_outputs_modified"] is False and idx["benchmark_read"] is False
    s3 = J(S3, "INDEX.json")
    for k, h in s3["outputs"].items():
        assert _h(S3 / k) == h, f"frozen S3 output changed: {k}"


def test_s3_1_headline_split_has_no_single_final_figure():
    hl = J(S31, "COLUMN_REBAR_S3_1_SUMMARY.json")["headline"]
    for k in ("VERIFIED_KG", "LOWER_BOUND_KG", "PROVISIONAL_KG", "BLOCKED_MODELLED_KG", "UNQUANTIFIED_BLOCKED_PARTS"):
        assert k in hl
    assert not any(k.upper().startswith("FINAL") for k in hl)
    parts = hl["VERIFIED_KG"] + hl["LOWER_BOUND_KG"] + hl["PROVISIONAL_KG"] + hl["BLOCKED_MODELLED_KG"]
    assert abs(parts - hl["MODELLED_SUM_NOT_FINAL_KG"]) < 0.01
    assert hl["UNQUANTIFIED_BLOCKED_PARTS"] > 0


def test_s3_1_one_unit_mass_method_and_rate_notation():
    s = J(S31, "COLUMN_REBAR_S3_1_SUMMARY.json")
    assert s["unit_mass_method"]["method"] == UM.D2_OVER_162
    assert s["headline"]["unit_mass"] == UM.describe(s["unit_mass_method"])
    assert s["tie_notation"]["notation"] == "RATE_PER_M"
    assert s["end_level_flag"]["method"] == "RATE_COUNT" and "URBAN_OWNER_RULE" in s["end_level_flag"]["authority"]


def test_s3_1_section_transitions_blocked_not_assumed_straight():
    st = J(S31, "COLUMN_REBAR_S3_1_SUMMARY.json")["section_transitions"]
    assert st["segments"] > 0
    assert set(st["kinds"]) == {"BLOCKED_TRANSITION_DETAIL"}
    assert sum(st["kinds"].values()) == st["segments"]


# ------------------------------------------------------------------------------------------- comparison package
def test_comparison_outputs_indexed_and_freeze_recorded_first():
    idx = J(CMP, "INDEX.json")
    for k, h in idx["outputs"].items():
        assert _h(CMP / k) == h
    assert _h(CMP / "URBAN_PRODUCTION_FREEZE.json") == idx["production_freeze_sha256"]
    fz = J(CMP, "URBAN_PRODUCTION_FREEZE.json")
    assert fz["freelancer_workbook_opened_before_this_record"] is False
    assert idx["production_registers_modified"] is False


def test_production_freeze_still_holds():
    fz = J(CMP, "URBAN_PRODUCTION_FREEZE.json")["inputs"]
    present = {k: h for k, h in fz.items() if (ROOT / k).exists()}
    if not present:
        pytest.skip("frozen production registers not on disk (data/ is not in git)")
    for k, h in present.items():
        assert _h(ROOT / k) == h, f"production changed after freeze: {k}"


def test_lineage_sums_back_to_every_summary_value():
    lin = J(CMP, "FREELANCER_CATEGORY_LINEAGE.json")
    assert lin["role"] == "FREELANCER_QS_REFERENCE"
    by_cell = {c["summary_cell"]: c for c in lin["categories"]}
    for c in lin["categories"]:
        for f in ("category_id", "arabic_name", "summary_cell", "summary_value", "source_sheets", "source_cells",
                  "formula", "subcomponents", "quantity", "unit", "possible_overlap", "notes"):
            assert f in c, (c["category_id"], f)
        if c["category_id"] == "TOTAL_STEEL":
            assert c["steel_is_formula"] is False          # typed values: no lineage to trace
            continue
        traced = 0.0
        for s in c["subcomponents"]:
            if s["kind"] == "SUMMARY_ROW":                  # a total of summary rows: sum the referenced categories
                traced += by_cell[f'{s["sheet"]}!{s["cell"]}']["summary_value"]
            elif s.get("value") is not None:
                traced += s["value"]
        assert abs(traced - c["summary_value"]) < 1e-6, c["category_id"]


def test_scope_map_flags_labels_wider_than_their_name():
    sm = {c["category_id"]: c for c in J(CMP, "FREELANCER_STRUCTURAL_SCOPE_MAP.json")["categories"]}
    for cid in ("FOUNDATIONS_RELATED", "WALLS_AND_COLUMNS", "STAIRS_AND_DOME", "SWIMMING_POOL"):
        assert len(sm[cid]["physical_scope"]) > 1, cid     # the label hides more than one physical kind
    assert sm["BEAMS"]["possible_overlap"] and sm["SLABS"]["possible_overlap"]
    assert not any("#REF!" in n for c in sm.values() for n in c["notes"])


@pytest.mark.parametrize("name", ["MULTI_ENGINE_CONCRETE_COMPARISON.json", "MULTI_ENGINE_AREA_COMPARISON.json"])
def test_no_percentage_on_not_comparable_rows(name):
    rows = J(CMP, name)["rows"]
    assert rows
    for r in rows:
        assert r["measurement_basis"]
        for who, v in r["vs"].items():
            if v["status"] == "NOT_COMPARABLE":
                assert v["difference"] is None and v["difference_percent"] is None, (r["category"], who)


def test_rough_profile_is_the_engine_profile_and_calibration_rounds_to_it():
    pkg = J(CMP, "URBAN_ROUGH_REBAR_PROFILE_V1.json")
    eng = json.loads((ROOT / pkg["engine_profile_path"]).read_text(encoding="utf-8"))
    RR.validate_profile(eng)
    assert pkg["profile"] == eng
    for r in pkg["calibration_sample"]["rows"]:
        exact = 1000.0 * r["steel_t"] / r["concrete_m3"]
        assert round(exact) == eng["ratios_kg_per_m3"][r["category"]], r["category"]


def test_rebar_comparison_rough_never_replaces_actual():
    reb = J(CMP, "MULTI_ENGINE_REBAR_COMPARISON.json")
    assert reb["footer"] == RR.FOOTER
    for r in reb["rows"]:
        assert r["rough_reference_kg_modelled"] is not None
        if not r["actual_complete"]:
            assert "missing" not in json.dumps(r).lower()
    assert all(o["answer"] == "INCOMPLETE" for o in reb["oracle_net_rebar"])   # never compared as complete


def test_population_register_is_complete_and_nothing_silent():
    pop = J(CMP, "STRUCTURAL_POPULATION_REGISTER.json")
    assert pop["complete_list"] is True
    names = {r["population"] for r in pop["rows"]}
    assert names == set(SPD.ALL_POPULATIONS)
    for r in pop["rows"]:
        assert r["state"] in ("PRESENT", "NOT_PRESENT", "BLOCKED", "UNKNOWN")
        if r["state"] == "NOT_PRESENT":
            assert r["refs"]


def test_oracle_register_never_overwrites_urban():
    reg = J(CMP, "SOURCE_ORACLE_COMPARISON_REGISTER.json")
    assert reg["rows"]
    for r in reg["rows"]:
        assert r["result"] in ("MATCH", "CLOSE", "CONFLICT", "NOT_COMPARABLE", "ORACLE_UNAVAILABLE")
        if r["result"] in ("NOT_COMPARABLE", "ORACLE_UNAVAILABLE"):
            assert r["difference_percent"] is None


def test_rebuild_reproduces_committed_outputs():
    sys.path.insert(0, str(CMP))
    import build_multi_engine_s3_1 as B
    if not B.FREELANCER_WB.exists():
        pytest.skip("freelancer reference workbook is client data (not in git)")
    try:
        _, _, blobs = B.main(write=False)
    except SystemExit as e:
        pytest.skip(f"production inputs unavailable: {e}")
    idx = J(CMP, "INDEX.json")
    for k, b in blobs.items():
        assert hashlib.sha256(b).hexdigest() == idx["outputs"][k], k
