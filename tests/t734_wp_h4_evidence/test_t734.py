"""T-734 waterproofing H4 evidence (R-T734-1 .. -3): synthetic villa W734 by hand (normal + adverse) and the
development villa pinned to the committed outputs.

Villa W734 (synthetic, not the development villa), by hand:
  L-shaped roof terrace, carriers walked from the south-west corner: E 10.00, N 4.00, W 6.00, N 3.00, W 4.00, S 7.00
    area = 10.00 x 4.00 + 4.00 x 3.00 = 52.000 m2, perimeter 2 x (10.00 + 7.00) = 34.000 m
  a 0.05 band on the west carrier over its 7.00 m: wall-face reading 52.000 + 0.05 x 7.00 = 52.350 m2
  one round skylight r 1.000 m: pi = 3.141593 m2; as a 1 mm-sagitta trace n = ceil(pi / acos(0.999)) = 71 chords,
    71/2 sin(2 pi / 71) = 3.137494 m2 (under-deduction 0.004099 m2)
  own band 52.000 - 3.141593 = 48.858407 .. 52.350 - 3.141593 = 49.208407 m2
  an engine release on the wall face with the chorded hole: 52.350 - 3.137494 = 49.212506 -> 49.213, ABOVE by 0.004593
"""
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t734"))
sys.path.insert(0, str(ROOT / "research" / "agents_t691"))
import t734_rules as R  # noqa: E402
import t691_rules as R691  # noqa: E402

OUT = ROOT / "research" / "agents_t734" / "out" / "T734_WP_H4_EVIDENCE.json"
W734 = [("H", "0"), ("V", "10.00"), ("H", "4.00"), ("V", "4.00"), ("H", "7.00"), ("V", "0")]
W734_WALL = W734[:-1] + [("V", "-0.05")]


def _draft(qty="49.213", state="HELD"):
    return R.record_draft(candidate_version="W734_V1", line_ids=["L-w734-roof"], unit="m2", engine_qty=qty,
                          state=state, basis_label="UNSUPPORTED BASIS", reason="above its own band",
                          evidence=["W734 roof plan=skylight r 1.000"])


# ------------------------------------------------------------------------ R-T734-2 face by named carriers
def test_l_shaped_face_by_hand():
    f = R.face(W734)
    assert (f["area_m2"], f["perimeter_m"], f["vertices"]) == (Decimal("52.000000"), Decimal("34.000000"), 6)


def test_band_reading_adds_band_times_run():
    assert R.face(W734_WALL)["area_m2"] - R.face(W734)["area_m2"] == Decimal("0.350000")


def test_mirror_and_rotation_keep_area():
    mirror = [(k, str(-Decimal(v)) if k == "V" else v) for k, v in W734]
    rot = [("V" if k == "H" else "H", v) for k, v in W734]          # x <-> y swap
    assert R.face(mirror)["area_m2"] == R.face(rot)["area_m2"] == Decimal("52.000000")


def test_mm_scale_gives_same_area():
    mm = [(k, str(Decimal(v) * 1000)) for k, v in W734]
    assert R.face(mm, "0.001")["area_m2"] == Decimal("52.000000")


def test_parallel_neighbours_refused():
    with pytest.raises(R.RuleError):
        R.face([("H", "0"), ("H", "1"), ("V", "2"), ("V", "0")])


def test_odd_carrier_count_refused():
    with pytest.raises(R.RuleError):
        R.face(W734[:-1])


def test_self_crossing_order_refused():
    bad = [("H", "0"), ("V", "10"), ("H", "4"), ("V", "-2"), ("H", "2"), ("V", "4"), ("H", "7"), ("V", "0")]
    with pytest.raises(R.RuleError):
        R.face(bad)


# ------------------------------------------------------------------------ disc deduction
def test_true_and_chorded_skylight_by_hand():
    n = R691.chords_for_sagitta(1.0, 0.001)
    assert n == 71
    assert R.net_membrane("52.000", ["1.0"]) == Decimal("48.858407")
    assert R.net_membrane("52.350", ["1.0"], chords=n) == Decimal("49.212506")


def test_radius_in_mm_read_as_m_refused():
    with pytest.raises(R.RuleError):
        R.net_membrane("52.000", ["1000"])


def test_openings_larger_than_face_refused():
    with pytest.raises(R.RuleError):
        R.net_membrane("3.000", ["1.0"])


# ------------------------------------------------------------------------ R-T734-1 eligibility / record
def test_release_above_band_is_eligible():
    e = R.eligibility("49.213", "48.858407", "49.208407")
    assert (e["state"], e["excess"], e["eligible"]) == ("ABOVE_BAND", Decimal("0.004593"), True)


def test_release_inside_band_or_within_half_step_is_not_a_downgrade_case():
    assert R.eligibility("49.000", "48.858407", "49.208407")["eligible"] is False
    assert R.eligibility("49.2088", "48.858407", "49.208407")["eligible"] is False   # 0.0004 over: rounding


def test_inverted_band_and_negative_refused():
    with pytest.raises(R.RuleError):
        R.eligibility("49", "50", "49")
    with pytest.raises(R.RuleError):
        R.eligibility("-1", "0", "1")


def test_nan_refused():
    with pytest.raises(R.RuleError):
        R.eligibility(float("nan"), "1", "2")


def test_record_carries_no_quantity_and_only_downgrades():
    d = _draft()
    assert R.validate_draft(d) == []
    assert not set(R.QUANTITY_KEYS) & set(d)
    with pytest.raises(R.RuleError):
        _draft(state="RELEASED")
    assert R.validate_draft(dict(d, checker_qty=49.208)) != []


def test_record_needs_evidence():
    with pytest.raises(R.RuleError):
        R.record_draft(candidate_version="W", line_ids=["L-1"], unit="m2", engine_qty=1, state="HELD",
                       basis_label="UNSUPPORTED BASIS", reason="r", evidence=["no equals sign"])


def test_without_record_the_released_figure_stands():
    a = R.after_state("49.213", ("48.858407", "49.208407"))
    assert a["class"] == "RELEASED" and a["value"] == Decimal("49.213000")


def test_with_record_the_line_goes_held_with_the_band_and_audit_keeps_the_figure():
    a = R.after_state("49.213", ("48.858407", "49.208407"), _draft())
    assert a["class"] == "HELD" and (a["low"], a["high"]) == (Decimal("48.858407"), Decimal("49.208407"))
    assert a["audit_candidate_qty"] == Decimal("49.213000") and "value" not in a


def test_a_downgrade_never_raises():
    with pytest.raises(R.RuleError):
        R.after_state("49.213", ("49.0", "49.5"), _draft())


def test_a_stale_record_is_not_applied():
    a = R.after_state("49.214", ("48.858407", "49.208407"), _draft("49.213"))
    assert a["class"] == "RELEASED" and "STALE" in a["why"]


def test_raise_is_never_a_downgrade():
    assert R.is_downgrade("92.922", "92.925396") is False
    assert R.is_downgrade("115.832", "115.813974") is True


# ------------------------------------------------------------------------ R-T734-3 census
def test_restate_live_stale_gone():
    a = {"class": "HELD", "unit": "pcs", "measured_net": None, "held_low": None, "held_high": None,
         "item_code": "FIN.WP.PENETRATION", "element_id": "R1:wp_penetrations"}
    assert R.restate(a, dict(a))["state"] == "LIVE"
    s = R.restate(a, dict(a, held_high=2.0))
    assert s["state"] == "STALE" and s["changed"] == ["held_high"]
    assert R.restate(a, None)["state"] == "GONE"
    with pytest.raises(R.RuleError):
        R.restate(None, a)


def test_missing_stays_missing_only_without_a_line_for_its_room():
    lines = [{"item_code": "FIN.WP.DOORWAY", "element_id": "R2:door"}]
    assert R.missing_still_missing("FIN.WP.DOORWAY", "R1", lines) is True
    assert R.missing_still_missing("FIN.WP.DOORWAY", "R2", lines) is False
    assert R.missing_still_missing("FIN.WP.DOORWAY", "R", lines) is True      # prefix of another room id
    with pytest.raises(R.RuleError):
        R.missing_still_missing("FIN.WP.DOORWAY", "", lines)


def test_penetration_cause():
    assert R.penetration_cause(1, 1) == "MEASURABLE_NOW"
    assert R.penetration_cause(1, 2) == "DESIGNER"
    for lo, hi in ((0, 0), (2, 1), ("1.5", 2)):
        with pytest.raises(R.RuleError):
            R.penetration_cause(lo, hi)


def test_census_counts_refuse_held_zero_and_no_cause():
    assert R.census_counts([{"key": "a", "cause": "X"}, {"key": "b", "cause": "X"}]) == {"X": 2}
    with pytest.raises(R.RuleError):
        R.census_counts([{"key": "a", "cause": "X", "status": "HELD", "value": 0}])
    with pytest.raises(R.RuleError):
        R.census_counts([{"key": "a"}])


# ------------------------------------------------------------------------ development villa (pinned)
@pytest.fixture(scope="module")
def dev():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_rebuild_equals_committed(dev):
    import t734_alsenan as B
    assert json.loads(json.dumps(B.build(), sort_keys=True, default=str)) == dev


def test_roof_band_and_eligibility(dev):
    r = dev["roof"]
    assert r["band_own"] == ["115.656474", "115.813974"]
    assert r["eligibility"]["state"] == "ABOVE_BAND" and r["released_vs_band"]["above_high_m2"] == "0.018026"
    assert all(abs(Decimal(v)) < Decimal("0.00002") for v in r["band_agree"].values())    # T-321 agrees
    assert r["engine_reconstruction"]["rounded"] == r["released"] == "115.832"


def test_roof_record_draft_is_downgrade_only(dev):
    d = dev["roof"]["downgrade_record_draft"]
    assert R.validate_draft(d) == [] and d["state"] == "HELD" and d["line_ids"] == ["L-636fd3ff1784a12e653b"]
    assert d["engine_qty_binding"] == 115.832 and d["candidate_version"] == "ARCH_TAKEOFF_V3.0.73"
    a = dev["roof"]["after_state"]
    assert a["class"] == "HELD" and (a["low"], a["high"]) == ("115.656474", "115.813974")


def test_upturn_is_not_a_downgrade(dev):
    u = dev["roof"]["upturn"]
    assert u["true_lm"] == "92.925396" and "NOT A DOWNGRADE" in u["class"] and u["corrected_lm"] == "92.925"
    assert u["residual_named"] == "0.000000"                 # 65.140 + 2 x 13.891 = 92.922 exactly


def test_census_on_v3073(dev):
    c = dev["census"]
    assert (c["held"], c["missing"], c["stale"], c["gone"]) == (53, 5, [], [])
    assert c["wp_line_ids_equal"] is True and c["wp_entries_differing"] == 0
    assert c["by_cause_t710"] == {"DESIGNER": 46, "MEASURABLE_NOW": 8, "NEEDS_OWNER_RULE": 3, "NO_PHYSICAL_ELEMENT": 1}
    assert c["by_cause"] == {"DESIGNER": 41, "MEASURABLE_NOW": 13, "NEEDS_OWNER_RULE": 3, "NO_PHYSICAL_ELEMENT": 1}
    assert len(c["cause_moved"]) == 5 and all(r["restate"] == "MISSING" for r in c["missing_rows"])


def test_d41_stays_held_never_zero(dev):
    x = dev["d41"]
    assert x["status"] == "HELD" and x["high_m2"] == "13.335040" and x["hosts_released_m2"] == "9.148000"
    assert all(h["restate"] == "LIVE" for h in x["hosts"])


def test_disc_sanity_true_vs_chord(dev):
    dm = dev["roof"]["dome"]
    r = float(dm["r_m"])
    assert abs(float(dm["true_m2"]) - math.pi * r * r) < 1e-5 and dm["chords"] == 105
