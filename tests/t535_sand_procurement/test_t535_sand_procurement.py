"""T-535 sand purchase unit: generic rules on a hand fixture (not the training villa) + the restatement of every merged
sand key of the training villa.

Hand fixture FX-535 (a small villa, numbers by hand; 2.40 m3 theoretical loose sand in 3 keys):
  K1 tile bed     installed 0.99 m3 (0.90 m3 1:4 mortar x 1.1), Q-45 loss 5 % 0.0495 -> procurement 1.0395 m3
  K2 block mortar installed 1.10 m3 (1.00 m3 x 1.1), no loss ruled             -> procurement 1.1000 m3
  K3 stair bed    installed 0.31 m3, Q-45 loss 5 % 0.0155                       -> procurement 0.3255 m3
  group: installed 2.40 m3, procurement 2.465 m3 (fractional; the pack is HELD -> no loads, no tonnes)
  with a TEST-ONLY sourced load of 1.0 m3: ONE ceiling ceil(2.465) = 3 loads (3.0 m3 delivered);
      per-key ceilings 2 + 2 + 1 = 5 loads (never bought)
  with a TEST-ONLY sourced density 1.6 t/m3: 2.465 x 1.6 = 3.944 t
"""

import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "t535_sand_procurement", os.path.join(ROOT, "research", "agents_t535", "t535_sand_procurement.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

A = dict(abs=1e-6)
SRC = "Q-45 B 5 % (fixture)"


def _fx(villa="FX-535"):
    return [M.member("K1 tile bed", villa, installed=(0.99, 0.99), loss=(0.0495, 0.0495), loss_state="SOURCED",
                     loss_source=SRC),
            M.member("K2 block mortar", villa, installed=(1.10, 1.10)),
            M.member("K3 stair bed", villa, installed=(0.31, 0.31), loss=(0.0155, 0.0155), loss_state="SOURCED",
                     loss_source=SRC)]


def _rec(**kw):
    r = dict(M.SAND_RECORD)
    r.update(kw)
    return r


# ------------------------------------------------------------------ normal cases (FX-535 by hand) -------------------
def test_unit_is_loose_m3_and_pack_density_held_in_the_record():
    r = M.SAND_RECORD
    assert r["key"] == "SAND_LOOSE" and r["unit"].startswith("m3 loose")
    assert r["pack_m3"] is None and M.PACK_HELD in r["pack_status"]
    assert r["bulk_density_t_per_m3"] is None and M.DENSITY_HELD in r["density_status"]
    assert any("Q-45" in s for s in r["unit_source"]) and any("Q-53" in s for s in r["unit_source"])


def test_fixture_group_procurement_fractional_pack_held():
    g = M.procure("SAND_LOOSE", _fx())
    assert g["status"] == M.COMPUTED
    assert g["installed_known"] == [pytest.approx(2.40, **A)] * 2
    assert g["procurement_m3"] == [pytest.approx(2.465, **A)] * 2
    assert g["to_buy_loads"] is None and M.PACK_HELD in g["to_buy_status"]
    assert g["procurement_t"] is None and M.DENSITY_HELD in g["tonne_status"]


def test_sourced_pack_one_ceiling_per_villa_not_sum_of_key_ceilings():
    rec = _rec(pack_m3=1.0, pack_source="test-only synthetic supplier record")
    g = M.procure("SAND_LOOSE", _fx(), rec)
    assert g["to_buy_loads"] == [3, 3] and g["delivered_m3"] == [pytest.approx(3.0)] * 2
    parts = [M.procure(m["id"], [m], rec)["procurement_m3"] for m in _fx()]
    assert M.sum_of_ceilings(parts, 1.0) == [5, 5]


def test_sourced_density_gives_tonnes():
    rec = _rec(bulk_density_t_per_m3=1.6, density_source="test-only synthetic")
    g = M.procure("SAND_LOOSE", _fx(), rec)
    assert g["procurement_t"] == [pytest.approx(3.944, **A)] * 2 and g["tonne_status"] == "COMPUTED"


def test_range_ends_kept_apart():
    ms = [M.member("bed", "FX", installed=(0.30, 0.45), loss=(0.015, 0.0225), loss_state="SOURCED", loss_source=SRC)]
    g = M.procure("G", ms)
    assert g["procurement_m3"] == [pytest.approx(0.315, **A), pytest.approx(0.4725, **A)]


# ------------------------------------------------------------------ adverse cases -----------------------------------
def test_loss_without_source_keeps_installed_and_holds_procurement():
    ms = _fx()[:2] + [M.member("K3 stair bed", "FX-535", installed=(0.31, 0.31), loss_state="HELD")]
    g = M.procure("SAND_LOOSE", ms)
    assert g["status"] == M.HELD and g["procurement_m3"] is None
    assert g["installed_known"] == [pytest.approx(2.40, **A)] * 2
    assert g["procurement_at_least_m3"] == [pytest.approx(2.4495, **A)] * 2
    assert "K3 stair bed (loss HELD)" in g["open"]
    rec = _rec(pack_m3=1.0, pack_source="test-only")
    assert M.procure("SAND_LOOSE", ms, rec)["to_buy_loads"] is None      # no ceiling over a HELD group


def test_sourced_loss_figure_needs_a_source():
    with pytest.raises(M.SandError, match="LOSS_WITHOUT_SOURCE"):
        M.member("x", "FX", installed=(1.0, 1.0), loss=(0.05, 0.05), loss_state="SOURCED")


@pytest.mark.parametrize("kw,code", [
    ({"pack_m3": 1.0}, "PACK_UNSOURCED"),
    ({"pack_m3": 0.0, "pack_source": "s"}, "PACK_UNSOURCED"),
    ({"bulk_density_t_per_m3": 1.6}, "DENSITY_UNSOURCED"),
])
def test_unsourced_pack_or_density_refused(kw, code):
    with pytest.raises(M.SandError, match=code):
        M.procure("G", _fx(), _rec(**kw))


def test_two_villas_never_share_one_group():
    with pytest.raises(M.SandError, match="TWO_VILLAS_ONE_GROUP"):
        M.procure("SAND_LOOSE", _fx("FX-A") + _fx("FX-B"))


def test_open_member_never_zero():
    g = M.procure("G", _fx() + [M.member("K4 screed, mix not printed", "FX-535")])
    assert g["status"] == M.HELD and g["procurement_at_least_m3"] == [pytest.approx(2.465, **A)] * 2
    assert "K4 screed, mix not printed" in g["open"]
    g0 = M.procure("G", [M.member("only open", "FX")])
    assert g0["procurement_at_least_m3"] is None and g0["installed_known"] is None


def test_bad_range_refused():
    with pytest.raises(M.SandError, match="BAD_RANGE"):
        M.member("x", "FX", installed=(0.5, 0.4))


# ------------------------------------------------------------------ merged keys (training villa, regression) --------
@pytest.fixture(scope="module")
def merged():
    return M.run()


def test_merged_restatement_no_failure_and_committed_output_identical(merged):
    assert merged["failures"] == [] and merged["released_quantities_changed"] == 0
    assert M.OUT.read_text() == M._dump(merged)


def test_merged_group_held_with_known_part(merged):
    g = merged["group"]
    assert g["status"] == M.HELD and g["to_buy_loads"] is None and M.PACK_HELD in g["to_buy_status"]
    assert g["installed_known"] == [pytest.approx(16.973531, **A), pytest.approx(22.404053, **A)]
    assert g["procurement_at_least_m3"] == [pytest.approx(17.746996, **A), pytest.approx(23.44904, **A)]


def test_stair_allowance_is_beside_and_v7_procurement_used(merged):
    st = merged["trades"]["STONE_BED"]
    assert st["installed_known"] == [pytest.approx(1.06028, **A)] * 2
    assert st["procurement_at_least_m3"] == [pytest.approx(1.06028 * 1.05, abs=2e-6)] * 2
    b = merged["stair_allowance_beside"]
    assert b["t523_bound_procurement_m3"] == [pytest.approx(1.062939, **A)] * 2 and "PRELIMINARY" in b["layer"]
    # delta vs the T-523 print = stair restage + the T-520 perimeter key
    assert merged["delta_vs_t523_m3"] == [pytest.approx(0.050355 + 0.107959, abs=2e-6)] * 2


def test_perimeter_key_own_and_held_members_open(merged):
    p = merged["trades"]["PERIMETER_JOINT"]
    assert p["installed_known"] == [pytest.approx(0.107959, **A)] * 2 and p["status"] == M.HELD
    assert len(p["open"]) == 7      # 0.20 loss HELD + 0.15 module + 4 x 2F D-39 + GF-W22
    assert merged["trades"]["PLASTER_COATS"]["installed_known"] is None
