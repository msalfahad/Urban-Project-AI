"""T-277 Alsenan census from committed inputs only (the coordinate-free census input and wall overlay derived from
Drive 'ST7757 dxf.dxf' sha 9f9d1179 and P7757.dxf sha ab54dd55; the merged T-252 ledger, T-110 register, T-234 slab
ledger and T-228 blockwork register). Pins the engineering results (development villa; no accuracy claim; nothing
wired, released or changed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t277"))
import t277_alsenan_check as K  # noqa: E402

SUM, LABS, RUNS, CONF = K.build()
BY_RUN = {c["run"]: c for c in CONF}


def test_every_label_of_the_three_slab_plans_compared():
    assert SUM["labels"] == 119 and SUM["labels_by_sheet"] == {"GF": 66, "1F": 38, "2F": 15}
    assert SUM["label_class_totals"] == {"AGREE": 111, "CONFLICT": 7, "AMBIGUOUS": 1}
    conf = sorted((r["sheet"], r["mark"]) for r in LABS if r["cls"] == "CONFLICT")
    assert conf == [("1F", "B6"), ("1F", "CB10"), ("1F", "CB10"), ("GF", "B21"), ("GF", "B29"), ("GF", "CB2"),
                    ("GF", "CB2")]
    amb = [r for r in LABS if r["cls"] == "AMBIGUOUS"]
    assert [(r["sheet"], r["label"], r["mark"], r["placement"]) for r in amb] == [("1F", "6DD", "CB12",
                                                                                   "BESIDE_STACKED")]


def test_runs_census_confirms_the_seven_conflicts_and_no_new_one():
    rc = SUM["run_classes"]
    assert rc["CONFLICT"] == 7 and rc["AGREE"] == 105
    # every run not compared is named: unlabelled / strip / upstand runs (no own mark: D-04 / D-05 / D-26),
    # void-ring arc pieces (no straight station; their labels bind the arcs at 0.200) and two held boxes / rings
    assert rc["NO_SCHEDULE"] == 18 and rc["NO_STATION"] == 5 and rc["NO_BAND"] == 2
    conf = sorted(r["component"] for r in RUNS if r["cls"] == "CONFLICT")
    assert conf == ["BEAMS:1F:BAND0009", "BEAMS:1F:BAND0026.1", "BEAMS:1F:BAND0026.2", "BEAMS:GF:BAND0008",
                    "BEAMS:GF:BAND0036.1", "BEAMS:GF:BAND0036.2", "BEAMS:GF:BAND0042"]


def test_drawn_and_schedule_widths_of_each_conflict():
    w = {c["run"]: (c["drawn_m"], c["schedule_m"]) for c in CONF}
    assert w["BM-GF-054#BAND0008"] == (pytest.approx(0.20), pytest.approx(0.25))      # B29
    assert w["BM-GF-055#BAND0036.1"] == (pytest.approx(0.25), pytest.approx(0.20))    # CB2 span 1
    assert w["BM-GF-056#BAND0042"] == (pytest.approx(0.40), pytest.approx(0.45))      # B21 (oblique)
    assert w["BM-1F-030#BAND0009"] == (pytest.approx(0.20), pytest.approx(0.25))      # B6 vertical span
    assert w["BM-1F-031#BAND0026.2"] == (pytest.approx(0.30), pytest.approx(0.25))    # CB10 inner strip


def test_concrete_readings_reproduce_d27_and_d02_independently():
    d27 = [c for c in CONF if c["designer"] == "D-27"]
    d02 = [c for c in CONF if c["designer"] == "D-02"]
    assert len(d27) == 5 and len(d02) == 2
    assert sum(c["conc_m3_drawn"] for c in d27) == pytest.approx(4.54927, abs=1e-5)
    assert sum(c["conc_m3_schedule"] for c in d27) == pytest.approx(5.022456, abs=1e-5)
    assert sum(c["conc_m3_schedule"] for c in d02) == pytest.approx(0.744, abs=1e-6)
    assert sum(c["conc_m3_drawn"] for c in d02) == pytest.approx(0.8928, abs=1e-6)
    assert SUM["conc_m3_drawn"] == pytest.approx(5.44207, abs=1e-5)
    assert SUM["conc_m3_schedule"] == pytest.approx(5.766456, abs=1e-5)


def test_formwork_soffit_both_readings_sides_unchanged():
    c = BY_RUN["BM-GF-056#BAND0042"]
    assert (c["fw_soffit_m2_drawn"], c["fw_soffit_m2_schedule"]) == (pytest.approx(2.99208), pytest.approx(3.36609))
    assert c["fw_sides_m2_both"] == pytest.approx(2 * (0.75 - 0.16) * 7.4802)
    assert SUM["fw_soffit_m2_drawn"] == pytest.approx(8.71398, abs=1e-5)
    assert SUM["fw_soffit_m2_schedule"] == pytest.approx(9.007215, abs=1e-5)


def test_blockwork_strips_under_the_conflict_bands():
    c = BY_RUN["BM-GF-055#BAND0036.2"]
    walls = {p["wall"]: p for p in c["walls"]}
    # the Checker's GF-W19 case (T-180 slot 18:04): 0.050 m of wall under the band at 0.25, 0 or 0.050 at 0.20
    assert walls["GF-W19"]["kind"] == "crossing" and walls["GF-W19"]["under_drawn_m"] == pytest.approx(0.05)
    assert walls["GF-W19"]["m2_change_range"] == [0.0, pytest.approx(0.017)]
    assert walls["GF-W20"]["m2_change_range"] == [0.0, pytest.approx(0.017)]          # found by this census
    assert walls["GF-W10"]["kind"] == "along" and walls["GF-W10"]["m2_change_range"] == [0.0, 0.0]
    b6 = {p["wall"]: p for p in BY_RUN["BM-1F-030#BAND0009"]["walls"]}
    assert b6["1F-W16"]["m2_change_range"] == [pytest.approx(-0.017), pytest.approx(-0.017)]
    assert SUM["blockwork_m2_change_low"] == pytest.approx(-0.017)
    assert SUM["blockwork_m2_change_high"] == pytest.approx(0.034)
    assert BY_RUN["BM-GF-054#BAND0008"]["walls"] == [] and BY_RUN["BM-GF-056#BAND0042"]["walls"] == []


def test_frames_aligned_exactly_and_schedule_duplicate_reported():
    assert SUM["align"]["GF"] == {"matched": 30, "arch_columns": 30, "resid_m": 0.0}
    assert SUM["align"]["1F"] == {"matched": 20, "arch_columns": 20, "resid_m": 0.0}
    assert SUM["schedule_duplicates"] == ["SB2"]                                      # D-38, a strap, not on a slab plan


def test_no_width_is_chosen_for_any_conflict():
    import beam_width_census as C
    for c in CONF:
        with pytest.raises(C.Refused):
            C.governing_width("CONFLICT", c["drawn_m"], c["schedule_m"], pick="larger")
