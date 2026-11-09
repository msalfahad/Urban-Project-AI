"""T-514: screed / threshold / outdoor bed producers (research/agents_t514/t514_screed_bed_producers.py).

Fixture villa K514 (not the training villa), by hand:
  SC1  protection screed printed '50 mm screed', on a 40.00 m2 m2 partner: m3 line 2.000 m3 (40 x 0.050).
       Normal: a PRINTED project note 'screed 1:4' (a record whose scope names SITE_MIXED_SCREED, ratio 1:4 at the
       owner's 1:4 figure 8.0 bags / 1.1 m3) -> cement 16.000 bags, sand 2.200 m3 installed; the record states no
       waste -> waste and procurement HELD (never 0).
       Without a record (layer printed 'screed' only) -> HELD naming LAYER_TYPE and MIX; sensitivity beside
       (1:4: 16.000 bags; 1:3: 19.152 bags) is NOT A QUANTITY.
  TH1  marble door threshold 0.90 x 0.20 = 0.180 m2, no printed bed -> HELD naming MIX and THICKNESS.
  OW1  outdoor porcelain side walk 10.00 m2 on the owner's regular-floor bed 0.03 .. 0.04 m, 1:4 (UPC-TILE-BED-001):
       0.300 .. 0.400 m3 -> cement 2.400 .. 3.200 bags, sand 0.330 .. 0.440 m3; waste 5 % (Q-45 B) 0.120 .. 0.160
       bags; procurement 2.520 .. 3.360 bags, 0.3465 .. 0.462 m3 sand.
Adverse: an unsourced mix (a ratio with no record) refused; a record used outside its scope refused; a second 1:4
conversion (7.6608) refused; a screed m3 that does not reproduce m2 x thickness refused; an unknown thickness unit
refused; mm / cm / m give the same figure; a second producer on one key refused by the census; a HELD host never
carries 0; line order does not change any figure.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t514"))

import t514_screed_bed_producers as T  # noqa: E402

M = T.t511()
REC = T.mix_records()


def line(lid, code, unit, net, cls="RELEASED"):
    return {"line_id": lid, "item_code": code, "class": cls, "measured_net": net, "held_low": None,
            "held_high": None, "unit": unit, "element_id": lid}


SC1 = line("K-SC1", "WP.FOUNDATION.FOOTING_SCREED", "m3", 2.0)
SC1_M2 = line("K-SC1A", "WP.FOUNDATION.FOOTING_SCREED", "m2", 40.0)
TH1 = line("K-TH1", "FIN.MARBLE.THRESHOLD", "m2", 0.18)
OW1 = line("K-OW1", "EXT.FLOOR.PORCELAIN", "m2", 10.0)

D_SC1 = {"kind": "SCREED_PRODUCT_NOT_STATED", "thickness": {"value": 50, "unit": "mm"}, "partner": "K-SC1A"}
D_SC1_MIXED = dict(D_SC1, kind="SITE_MIXED_SCREED")
D_TH1 = {"kind": "THRESHOLD_STONE_BED", "thickness": None}
D_OW1 = {"kind": "FLOOR_TILE_BED", "floor_class": "REGULAR", "thickness": None}

SPEC = {"label": "DRAWING-CONFIRMED", "source": "K514 sheet S-3 note 'screed 1:4'", "scope": ("SITE_MIXED_SCREED",),
        "ratio": "1:4", "bags_per_m3": 8.0, "sand_m3_per_m3": 1.1, "band_m": None, "waste": None,
        "waste_source": "no waste printed"}


def recs(**extra):
    r = dict(REC)
    r.update(extra)
    return r


def val(rows, mat, stage):
    r = [x for x in rows if x["material"] == mat and x["stage"] == stage]
    assert len(r) == 1
    return r[0]["low"], r[0]["high"]


# ---------------------------------------------------------------- normal cases (hand) --------------------------------
def test_screed_with_a_printed_mix_record_is_produced_by_hand():
    st, m3, missing, rid = T.resolve(SC1, D_SC1_MIXED, recs(K514_SPEC=SPEC), SC1_M2)
    assert (st, rid, missing) == ("PRODUCED", "K514_SPEC", [])
    assert m3 == (2.0, 2.0)
    rows = T.producer_rows(M, SC1, m3, SPEC, rid, "SCREED", "SCREED")
    assert val(rows, M.CEMENT, M.INSTALLED) == (16.0, 16.0)
    assert val(rows, M.SAND, M.INSTALLED) == (2.2, 2.2)
    assert val(rows, M.CEMENT, M.WASTE) == (None, None)       # no waste source: HELD, never 0
    assert val(rows, M.CEMENT, M.PROCUREMENT) == (None, None)


def test_screed_printed_screed_only_is_held_by_name_with_sensitivity_beside():
    st, m3, missing, rid = T.resolve(SC1, D_SC1, recs(K514_SPEC=SPEC), SC1_M2)
    assert st == "HELD" and rid is None
    assert any(m.startswith("LAYER_TYPE") for m in missing) and any(m.startswith("MIX") for m in missing)
    conv, fails = T.conversions(REC)
    assert fails == []
    s = T.sensitivity(SC1, D_SC1, conv)
    assert s["1:4"]["cement_bags"] == [16.0, 16.0]
    assert s["1:3"]["cement_bags"] == [19.152, 19.152]            # 2.0 x 9.576 (UP-STAIR-017)
    assert "NOT A QUANTITY" in s["label"]


def test_threshold_with_no_printed_bed_is_held_naming_mix_and_thickness():
    st, m3, missing, rid = T.resolve(TH1, D_TH1, REC)
    assert st == "HELD" and m3 is None and rid is None
    assert sorted(m.split(":")[0] for m in missing) == ["MIX", "THICKNESS"]


def test_outdoor_porcelain_bed_by_hand():
    st, m3, missing, rid = T.resolve(OW1, D_OW1, REC)
    assert (st, rid) == ("PRODUCED", "UPC-TILE-BED-001")
    assert m3 == pytest.approx((0.30, 0.40))
    rows = T.producer_rows(M, OW1, m3, REC[rid], rid, "OUTDOOR_BED", "FLOOR_TILE_BED")
    assert val(rows, M.CEMENT, M.INSTALLED) == (2.4, 3.2)
    assert val(rows, M.SAND, M.INSTALLED) == (0.33, 0.44)
    assert val(rows, M.CEMENT, M.WASTE) == (0.12, 0.16)
    assert val(rows, M.CEMENT, M.PROCUREMENT) == (2.52, 3.36)
    assert val(rows, M.SAND, M.PROCUREMENT) == (0.3465, 0.462)
    assert REC[rid]["label"] == "ASSUMED - OWNER-APPROVED"


def test_wet_floor_class_takes_the_wet_band():
    st, m3, _, _ = T.resolve(OW1, dict(D_OW1, floor_class="WET"), REC)
    assert st == "PRODUCED" and m3 == pytest.approx((0.40, 0.60))


# ---------------------------------------------------------------- adverse cases ---------------------------------------
def test_unsourced_mix_is_refused():
    with pytest.raises(T.ProducerError, match="UNSOURCED_MIX"):
        T.resolve(SC1, D_SC1_MIXED, REC, SC1_M2, mix={"ratio": "1:4"})
    with pytest.raises(T.ProducerError, match="UNSOURCED_MIX"):
        T.resolve(SC1, D_SC1_MIXED, REC, SC1_M2, mix={"record": "MY_GUESS"})


def test_record_outside_its_scope_is_refused():
    with pytest.raises(T.ProducerError, match="OUT_OF_SCOPE"):
        T.resolve(SC1, D_SC1_MIXED, REC, SC1_M2, mix={"record": "UPC-TILE-BED-001"})
    with pytest.raises(T.ProducerError, match="OUT_OF_SCOPE"):
        T.resolve(TH1, D_TH1, REC, mix={"record": "UP-STAIR-017"})


def test_a_second_conversion_for_one_ratio_is_refused():
    conv, fails = T.conversions(REC, extra=[("1:4", 7.6608, 1.064, "T-489 V2 (Q-53 C method on 1:4)")])
    assert [f["kind"] for f in fails] == ["CONVERSION_CONFLICT"]
    conv, fails = T.conversions(REC)
    assert fails == [] and conv["1:4"][:2] == (8.0, 1.1) and conv["1:3"][:2] == (9.576, 0.9975)
    assert sorted(conv["1:4"][2]) == ["Q-78-A", "UPC-TILE-BED-001"]


def test_screed_volume_must_reproduce_area_times_thickness():
    bad = dict(SC1, measured_net=2.1)
    with pytest.raises(T.ProducerError, match="REPRODUCE"):
        T.resolve(bad, D_SC1_MIXED, recs(K514_SPEC=SPEC), SC1_M2)


def test_thickness_units_mm_cm_m_agree_and_unknown_unit_fails():
    a = T.thickness_m({"value": 50, "unit": "mm"})
    b = T.thickness_m({"value": 5, "unit": "cm"})
    c = T.thickness_m({"value": 0.05, "unit": "m"})
    assert a == pytest.approx(b) == pytest.approx(c) == pytest.approx(0.05)
    with pytest.raises(T.ProducerError, match="UNIT"):
        T.thickness_m({"value": 2, "unit": "in"})


def test_held_area_stays_held_never_zero():
    held = line("K-OW2", "EXT.FLOOR.PORCELAIN", "m2", None, cls="HELD")
    st, m3, missing, _ = T.resolve(held, D_OW1, REC)
    assert st == "HELD" and m3 is None and any(m.startswith("AREA") for m in missing)


def test_paver_sand_bed_never_takes_a_cement_ratio():
    pv = line("K-PV", "EXT.PAVING.INTERLOCK", "m2", 50.0)
    st, _, missing, rid = T.resolve(pv, {"kind": "PAVER_SAND_BED", "thickness": None}, REC)
    assert st == "HELD" and rid is None and not any(m.startswith("MIX") for m in missing)


def test_second_producer_on_one_key_is_refused_by_the_census():
    st, m3, _, rid = T.resolve(OW1, D_OW1, REC)
    rows = T.producer_rows(M, OW1, m3, REC[rid], rid, "OUTDOOR_BED", "FLOOR_TILE_BED")
    dup = [dict(r, table="OTHER") for r in rows]
    code_table = {"EXT.FLOOR.PORCELAIN": ("HOST", "OUTDOOR_BED", "x")}
    ok = M.census([OW1], rows, {}, code_table)
    assert ok["fails"] == []
    bad = M.census([OW1], rows + dup, {}, code_table)
    assert {f["kind"] for f in bad["fails"]} == {"TWO_PRODUCERS"}


def test_line_order_does_not_change_any_figure():
    a = [T.resolve(ln, d, REC) for ln, d in ((OW1, D_OW1), (TH1, D_TH1))]
    b = [T.resolve(ln, d, REC) for ln, d in ((TH1, D_TH1), (OW1, D_OW1))][::-1]
    assert a == b


# ---------------------------------------------------------------- the candidate of record ---------------------------
@pytest.fixture(scope="module")
def built():
    return T.build()


def test_candidate_build_has_no_failure_and_one_producer_per_key(built):
    assert built["fails"] == []
    assert built["keys_with_two_producers"] == 0
    assert built["released_quantities_changed"] == 0
    assert len(built["hosts"]) == 32


def test_every_scope_host_ends_produced_or_held_by_name(built):
    for h in built["hosts"]:
        assert h["state"] in ("PRODUCED", "HELD")
        if h["state"] == "HELD":
            assert h["missing"], h["line_id"]
    by = built["hosts_by_kind"]
    assert by["FLOOR_TILE_BED"] == {"PRODUCED": 1}
    assert by["SCREED_PRODUCT_NOT_STATED"] == {"HELD": 4} and by["ROOF_FALLS_SCREED"] == {"HELD": 4}
    assert by["THRESHOLD_STONE_BED"] == {"HELD": 17} and by["STONE_CLADDING_FIXING"] == {"HELD": 3}


def test_outdoor_walk_bed_and_project_restatement_by_hand(built):
    w = next(h for h in built["hosts"] if h["line_id"] == "L-ab44fbc79bed353bde99")
    assert w["m3"] == [0.630426, 0.840568]                    # 21.0142 x 0.03 / 0.04
    assert w["cement_bags"] == [5.043408, 6.724544]           # x 8
    assert w["sand_m3"] == [0.693469, 0.924625]               # x 1.1
    p = built["subtotals"]["PROJECT"]["INSTALLED"][M.CEMENT]
    old = built["t511_project"]["INSTALLED"][M.CEMENT]
    assert p["status"] == "HELD" and p["low"] is None          # never a partial project total
    assert p["at_least_low"] == pytest.approx(old["at_least_low"] + 5.043408, abs=1e-6) == pytest.approx(125.12628)
    assert p["at_least_high"] == pytest.approx(old["at_least_high"] + 6.724544, abs=1e-6)
    assert built["subtotals"]["SCREED"]["INSTALLED"][M.CEMENT]["at_least_low"] is None


def test_screed_volume_and_sensitivity(built):
    assert built["screed_released_m3"] == 8.052003            # 5.4925 + 1.035 + 1.524503
    s = sum(b["1:4"]["cement_bags"][0] for b in built["beside"] if b["basis"] == "released m3")
    assert s == pytest.approx(64.416024)
    assert [f["id"] for f in built["findings"]] == ["F-T514-1"]


def test_states_outside_the_scope_are_the_t511_states(built):
    old = built["t511_host_states_cement"]
    new = built["host_states_cement"]
    assert new["PRODUCED"] == old["PRODUCED"] + 1 and new["HELD"] == old["HELD"] - 1
    assert new["NOT_APPLICABLE"] == old["NOT_APPLICABLE"]


def test_no_held_row_carries_zero(built):
    for r in built["rows"]:
        if r["status"] == "HELD":
            assert r["low"] is None and r["high"] is None


def test_committed_output_rebuilds_byte_identical(built, tmp_path):
    T.write(built, tmp_path)
    for n in ("SCREED_BED_PRODUCERS_T514.json", "SCREED_BED_PRODUCERS_T514.csv"):
        assert (tmp_path / n).read_bytes() == (ROOT / "research/agents_t514/out" / n).read_bytes()
