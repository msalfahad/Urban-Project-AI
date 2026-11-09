"""T-659: the small B10 elements line by line (research/agents_t659, R-T659-1 .. 5). Hand villa "V659" (not the training
villa) with normal and adverse cases, then the development-villa ledger rebuilt from committed, pinned files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t659"))
import t659_rules as R  # noqa: E402
import t659_alsenan as A  # noqa: E402

OUT = ROOT / "research" / "agents_t659" / "out" / "T659_LEDGER.json"
D = Decimal


# ---- villa "V659" (hand) ----------------------------------------------------------------------------------------
# Boundary pads 1.20 x 0.70 x 0.30, ground beam 0.20 x 0.40 running through on the pad soffit:
#   gross 0.252, shared 0.20 x 1.20 x 0.30 = 0.072, net 0.180 m3 per pad. Its sheet PRINTS 8 pads -> 1.440 m3 VALUED.
def _pad():
    return R.pad_net_of_through_beam(R.dim("1.20", "V659 S-3 pad 120x70x30"), R.dim("0.70", "V659 S-3"),
                                     R.dim("0.30", "V659 S-3"), R.dim("0.20", "V659 S-3 G.B 20x40"),
                                     R.dim("0.40", "V659 S-3 G.B 20x40"))


def test_hand_pad_net_of_through_beam():
    p = _pad()
    assert (p["gross_m3"], p["shared_with_beam_m3"], p["net_m3"]) == (D("0.252"), D("0.072"), D("0.18"))
    row = R.component("L-V659-PAD", "STR.CONC.BOUNDARY_PAD", "V659:PADS", "VALUED", value=p["net_m3"] * 8,
                      sources=["V659 S-3 prints 8 pads"])
    assert row["value"] == "1.440000"


def test_hand_pad_count_not_printed_stays_blank_with_coefficient():
    p = _pad()
    row = R.component("L-V659-PAD2", "STR.CONC.BOUNDARY_PAD", "V659:PADS2", "HELD_BLANK", item="count 'SEE ARCH PLAN'",
                      coefficients=[{"per": "pad", "m3_per_unit": p["net_m3"], "basis": "V659 S-3"}])
    assert row["value"] is None and row["low"] is None and row["coefficients"][0]["m3_per_unit"] == "0.180000"


def test_hand_band_two_sections_bound_and_provisional_beside():
    lo = R.box(R.dim("50", "V659 band 50.00 printed"), R.dim("0.2", "V659 S-3"), R.dim("0.4", "V659 S-3 20x40"))
    hi = R.box(R.dim("50", "V659 band 50.00 printed"), R.dim("0.2", "V659 S-9"), R.dim("0.6", "V659 S-9 20x60"))
    row = R.component("L-V659-BAND", "STR.CONC.BOUNDARY_WALL", "V659:BAND", "BOUNDED", low=lo, high=hi,
                      low_basis="20x40 typical", high_basis="20x60 schedule", item="section RFI",
                      beside=[{"what": "owner provisional", "m3": "5.0"}])
    assert (row["low"], row["high"]) == ("4.000000", "6.000000")


def test_hand_dome_cap_and_rotation_order():
    assert R.cap_area_per_m(R.dim("6.00", "V659 S-7"), R.dim("1.00", "V659 S-7")) == D("31.415927")
    a = R.box(D("1.2"), D("0.7"), D("0.3"))
    assert a == R.box(D("0.7"), D("0.3"), D("1.2")) == R.box(D("0.3"), D("1.2"), D("0.7"))  # mirror / rotation


def test_totals_never_sum_a_blank_line():
    rows = [R.component("L-1", "STR.CONC.X", "e1", "BOUNDED", low="1", high="2", low_basis="a", high_basis="b",
                        item="i"),
            R.component("L-2", "STR.CONC.X", "e2", "HELD_BLANK", item="D-1")]
    t = R.ledger_totals(rows)
    assert t["total_stateable"] is False and t["carried_high_m3"] is None and t["blank"] == 1


# ---- adverse ----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("src", ["AS PER ARCH", "SEE ARCH PLAN", "as per lift manufacturer", "AS PER SCHEDULE",
                                 "default 0.10", "freelancer row 12", "", "generic neck"])
def test_unprinted_or_refused_source(src):
    with pytest.raises(R.Refused):
        R.dim("0.30", src)


@pytest.mark.parametrize("v", ["1300", "1300mm", None, "0", "-0.2", "5%"])
def test_bad_dimension(v):
    with pytest.raises(R.Refused):
        R.dim(v, "V659 S-3")


def test_blank_line_with_a_figure_or_without_item_refused():
    with pytest.raises(R.Refused):
        R.component("L-3", "STR.CONC.X", "e", "HELD_BLANK", low="1.0", item="D-1")
    with pytest.raises(R.Refused):
        R.component("L-3", "STR.CONC.X", "e", "HELD_BLANK")


def test_held_as_zero_refused_unless_existence_open():
    with pytest.raises(R.Refused):
        R.component("L-4", "STR.CONC.X", "e", "BOUNDED", low="0", high="1", low_basis="a", high_basis="b", item="i")
    ok = R.component("L-4", "STR.CONC.X", "e", "BOUNDED", low="0", high="1", low_basis="a", high_basis="b", item="i",
                     existence_open=True)
    assert ok["low"] == "0.000000"
    with pytest.raises(R.Refused):
        R.component("L-4", "STR.CONC.X", "e", "LOWER_ONLY", low="0", low_basis="a", item="i")


def test_coefficient_times_unprinted_count_refused():
    with pytest.raises(R.Refused):
        R.component("L-5", "STR.CONC.X", "e", "HELD_BLANK", item="count",
                    coefficients=[{"per": "pad", "m3_per_unit": "0.18", "basis": "x", "applied_to_count": 10}])


def test_provisional_reading_as_bound_refused():
    with pytest.raises(R.Refused):
        R.component("L-6", "STR.CONC.X", "e", "BOUNDED", low="4", high="6", low_basis="a", high_basis="b", item="i",
                    beside=[{"what": "owner provisional", "m3": "5", "as_bound": True}])
    with pytest.raises(R.Refused):
        R.component("L-6", "STR.CONC.X", "e", "BOUNDED", low="4", high="6", low_basis="freelancer", high_basis="b",
                    item="i")


def test_floor_only_beside_a_blank_line_and_needs_status():
    with pytest.raises(R.Refused):
        R.component("L-7", "STR.CONC.X", "e", "BOUNDED", low="1", high="2", low_basis="a", high_basis="b", item="i",
                    floor={"m3": "1", "basis": "x", "status": "DC"})
    with pytest.raises(R.Refused):
        R.component("L-7", "STR.CONC.X", "e", "HELD_BLANK", item="i", floor={"m3": "1", "basis": "x"})


def test_beam_wider_than_pad_and_line_twice_refused():
    with pytest.raises(R.Refused):
        R.pad_net_of_through_beam(D("1.2"), D("0.2"), D("0.3"), D("0.2"), D("0.4"))
    r = R.component("L-8", "STR.CONC.X", "e", "HELD_BLANK", item="i")
    with pytest.raises(R.Refused):
        R.ledger_totals([r, dict(r)])


# ---- development villa (committed, pinned inputs) ------------------------------------------------------------------
def test_alsenan_rebuild_equals_committed():
    built = json.loads(json.dumps(A.build(), sort_keys=True))
    assert built == json.loads(OUT.read_text())


def test_alsenan_every_line_once_and_key_figures():
    out = json.loads(OUT.read_text())
    rows = {r["line_id"]: r for r in out["rows"]}
    assert len(rows) == 16 == out["totals_after"]["lines"]
    assert out["totals_after"]["valued"] == 0 and out["totals_after"]["blank"] == 10
    assert out["totals_after"]["carried_low_m3"] == "13.279574" and out["totals_after"]["total_stateable"] is False
    bw = rows["L-6290a9f3d93f38cd46d6"]
    assert (bw["low"], bw["high"]) == ("5.639200", "11.032800")
    assert bw["before"]["candidate_V3_0_61"] == [7.2204, 7.2204]
    pad = rows["L-cda8f41522dc6f42b3d6"]["coefficients"]
    assert [c["m3_per_unit"] for c in pad] == ["0.234000", "0.312000"]
    floors = sum(D(r["floor"]["m3"]) for r in out["rows"] if r["floor"])
    assert floors == D("9.953943")  # parapets 8.050943 (T-319) + lift walls 1.903 (flagged)
    assert all(r["value"] is None for r in out["rows"])
    assert any(m["status"].startswith("MISSING") for m in out["named_missing"])


def test_alsenan_edited_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(A.PINS, A.T572, "0000000000000000")
    with pytest.raises(R.Refused):
        A.build()
