"""T-537 R-T498-2: block material base of a host wall with BOUNDED / RANGED lintel faces.

Hand fixture K537 (not the training villa; numbers by hand):
  wall A 4.00 x 3.00 m = 12.00 m2, door 1.20 x 2.10 = 2.52 m2 -> contract net 9.48 m2
  lintel B 0.20 x D 0.20, w 1.20, bearing 0.15 .. 0.40 each end -> L [1.50, 2.00] m -> face [0.30, 0.40] m2
  material base = [9.48 - 0.40, 9.48 - 0.30] = [9.08, 9.18] m2 (low end with the HIGH bearing)
    white 0.20 (4.5 kg/m2): glue [40.86, 41.31] kg = [1.6344, 1.6524] bags of 25 kg -> to buy [2, 2] DETERMINATE
    white 0.15 (3.5 kg/m2, B 0.15): glue [31.78, 32.13] kg
    black 0.20: units x 12.5 = [113.5, 114.75] pcs; mortar x 0.20 (1 - 0.39 x 0.19 / 0.40 x 0.20) = 0.01475 m3/m2
                -> [0.13393, 0.135405] m3
  wall D 4.70 x 3.00 = 14.10 m2, window 1.20 x 2.20 = 2.64 -> net 11.46; same lintel -> base [11.06, 11.16] ->
    glue [49.77, 50.22] kg = [1.9908, 2.0088] bags -> to buy [2, 3]: a RANGE by name, never 'the 3'
  wall A + wall D in one purchasing group: [90.63, 91.53] kg = [3.6252, 3.6612] bags -> ONE ceiling [4, 4]
    (per-wall ceilings 2 + 2 .. 2 + 3 = 4 .. 5 are never bought)
  r2 HELD_BY_NAME (wall A, door w 1.20): START BOUNDED, masonry ceiling 0.60 m; END DEFICIT, a 0.10 m at a column
    T-524 (min-bearing basis): L [1.20 + 0.40 + 0, 1.20 + 0.40 + 0.10] = [1.60, 1.70]; 1.70 is NO ceiling
    ceiling-bound: L_hi = 1.70 + (0.60 - 0.40) = 1.90 = 1.20 + 0.60 + 0.10 -> face 0.20 x [1.60, 1.90] = [0.32, 0.38]
    base [9.48 - 0.38, 9.48 - 0.32] = [9.10, 9.16] m2 -> glue [40.95, 41.22] kg (the min-bearing hi would give
    a false low end 9.14 -> 41.13 kg)
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t537"))
import r_t498_2 as R          # noqa: E402
import t537_apply as AP       # noqa: E402

A = pytest.approx


def lz(oid="DA", lo=1.50, hi=2.00, B=0.20, D=0.20, state="BOUNDED_MIN_BEARING"):
    return {"opening_id": oid, "state": state, "section_B_D_m": [B, D], "length_m": [lo, hi]}


def base_of(net, *lintels, t=0.20):
    return R.material_base(net, [R.lintel_face(x, t) for x in lintels])


# ------------------------------------------------------------------ normal (K537 by hand) -------------------------
def test_face_is_D_times_the_length_interval():
    f = R.lintel_face(lz(), 0.20)
    assert f["face_m2"] == [A(0.30), A(0.40)] and not f["open"]


def test_base_low_end_takes_the_high_face():
    b = base_of(9.48, lz())
    assert b["state"] == "RANGE" and b["base_m2"] == [A(9.08), A(9.18)]


def test_white_glue_range_both_thicknesses():
    g = R.material_line(base_of(9.48, lz()), 4.5, "kg")
    assert g["state"] == "BOUNDED_EXPOSURE" and g["value"] is None
    assert g["range"] == [A(40.86), A(41.31)]
    g15 = R.material_line(base_of(9.48, lz(B=0.15), t=0.15), 3.5, "kg")
    assert g15["range"] == [A(31.78), A(32.13)]


def test_black_units_and_mortar_follow_the_same_base():
    b = base_of(9.48, lz())
    u = R.material_line(b, 12.5, "pcs")
    jr = R.joint_m3_per_m2(0.20, (0.39, 0.19), (0.40, 0.20))
    assert jr == A(0.01475)
    m = R.material_line(b, jr, "m3")
    assert u["range"] == [A(113.5), A(114.75)]
    assert m["range"] == [A(0.13393), A(0.135405)]


def test_degenerate_interval_is_one_value():
    b = base_of(9.48, lz(lo=2.00, hi=2.00, state="VALUED"))
    assert b["state"] == "EXACT"
    g = R.material_line(b, 4.5, "kg")
    assert g["state"] == "VALUED" and g["value"] == A(40.86) and g["range"] is None


def test_single_member_group_determinate_when_both_ceilings_agree():
    g = R.group_to_buy("AAC", [R.material_line(base_of(9.48, lz()), 4.5 / 25.0, "bags")], 1.0, loss_state="NONE")
    assert g["status"] == "COMPUTED" and g["procurement"] == [A(1.6344), A(1.6524)]
    assert g["to_buy"] == [2, 2] and g["reading"] == "DETERMINATE"


def test_range_across_a_bag_boundary_stays_a_range():
    d = R.material_line(base_of(11.46, lz()), 4.5, "kg")
    assert d["range"] == [A(49.77), A(50.22)]
    g = R.group_to_buy("AAC", [R.material_line(base_of(11.46, lz()), 4.5 / 25.0, "bags")], 1.0, loss_state="NONE")
    assert g["to_buy"] == [2, 3] and g["reading"].startswith("RANGE")


def test_one_ceiling_per_group_not_per_wall():
    a = R.material_line(base_of(9.48, lz("DA")), 4.5 / 25.0, "bags")
    d = R.material_line(base_of(11.46, lz("WD")), 4.5 / 25.0, "bags")
    g = R.group_to_buy("AAC", [a, d], 1.0, loss_state="NONE")
    assert g["procurement"] == [A(3.6252), A(3.6612)] and g["to_buy"] == [4, 4]


def test_loss_held_keeps_the_group_held_with_at_least():
    g = R.group_to_buy("AAC", [R.material_line(base_of(9.48, lz()), 4.5 / 25.0, "bags")], 1.0)
    assert g["status"] == "HELD" and g["at_least"] == [A(1.6344), A(1.6524)] and g["to_buy_at_least"] == [2, 2]


def test_legacy_held_face_with_proven_ceiling_kept_as_r_t498_1():
    held = {"opening_id": "W9", "state": "HELD_FACE", "face_max_m2": 0.50, "face_max_basis": "UPPER_PROVEN"}
    b = R.material_base(9.48, [R.lintel_face(lz(), 0.20), R.lintel_face(held, 0.20)])
    assert b["base_m2"] == [A(8.58), A(9.18)]


def _hbn_ends(ceiling=0.60, a=0.10, start_state="BOUNDED"):
    return [{"side": "START", "state": start_state, "ceiling_m": ceiling},
            {"side": "END", "state": "FLAGGED_DEFICIT", "a_m": a}]


def test_held_by_name_upper_length_bound_by_the_measured_ceiling():
    c = R.ceiling_length("DK", [1.60, 1.70], _hbn_ends())
    assert c["length_m"] == [A(1.60), A(1.90)] and c["length_hi_basis"] == "CEILING"
    li = {"opening_id": "DK", "state": "HELD_BY_NAME", "section_B_D_m": [0.20, 0.20], "length_m": c["length_m"],
          "length_hi_basis": c["length_hi_basis"]}
    b = base_of(9.48, li)
    assert b["base_m2"] == [A(9.10), A(9.16)]
    assert R.material_line(b, 4.5, "kg")["range"] == [A(40.95), A(41.22)]


def test_pair_on_one_host_carried_once():
    out = R.pair_faces({"pair": ["P1", "P2"], "D_m": 0.20, "length_m": [2.60, 3.00]}, {"P1": "H", "P2": "H"})
    assert list(out) == ["H"] and len(out["H"]) == 1 and out["H"][0]["face_m2"] == [A(0.52), A(0.60)]


# ------------------------------------------------------------------ adverse -----------------------------------------
def test_unbounded_face_holds_the_material_never_zero():
    b = base_of(9.48, lz(hi=None))
    g = R.material_line(b, 4.5, "kg")
    assert b["state"] == "HELD" and g["state"] == "HELD"
    assert g["value"] is None and g["range"] is None and g["value"] != 0
    assert g["at_most_beside"] == A(41.31)


def test_inverted_interval_refused():
    with pytest.raises(R.RuleError, match="inverted"):
        R.lintel_face(lz(lo=2.00, hi=1.50), 0.20)


@pytest.mark.parametrize("kw", [dict(B=200, D=200), dict(lo=1500, hi=2000), dict(D=-0.2)])
def test_millimetres_or_negative_refused(kw):
    with pytest.raises(R.RuleError):
        R.lintel_face(lz(**kw), 0.20)


def test_faces_above_the_net_refused():
    with pytest.raises(R.RuleError, match="exceed"):
        base_of(0.35, lz())
    with pytest.raises(R.RuleError, match="exceed"):
        base_of(0.25, lz())


def test_min_bearing_length_is_no_maximum():
    held = {"opening_id": "W9", "state": "HELD_FACE", "face_max_m2": 0.40, "face_max_basis": "MIN_BEARING_LENGTH"}
    b = R.material_base(9.48, [R.lintel_face(lz(), 0.20), R.lintel_face(held, 0.20)])
    assert b["state"] == "HELD" and b["base_m2"] == [None, A(9.18)]


def test_held_face_without_a_basis_refused():
    with pytest.raises(R.RuleError, match="basis"):
        R.lintel_face({"opening_id": "W9", "state": "HELD_FACE", "face_max_m2": 0.4}, 0.20)


def test_partial_depth_lintel_holds_the_host():
    f = R.lintel_face(lz(B=0.15), 0.20)
    assert f["open"] and f["face_m2"] == [0.0, None]


def test_pair_split_over_two_hosts_opens_both():
    out = R.pair_faces({"pair": ["P1", "P2"], "D_m": 0.20, "length_m": [2.60, 3.00]}, {"P1": "H1", "P2": "H2"})
    assert all(f["open"] for v in out.values() for f in v) and set(out) == {"H1", "H2"}


def test_same_lintel_twice_and_prerounded_refused():
    f = R.lintel_face(lz(), 0.20)
    with pytest.raises(R.RuleError, match="twice"):
        R.material_base(9.48, [f, dict(f)])
    with pytest.raises(R.RuleError, match="rounded"):
        R.group_to_buy("AAC", [{"state": "VALUED", "value": 2, "rounded": True}], 1.0)


def test_min_bearing_hi_at_a_bounded_end_refused_as_a_ceiling():
    li = {"opening_id": "DK", "state": "HELD_BY_NAME", "section_B_D_m": [0.20, 0.20], "length_m": [1.60, 1.70],
          "length_hi_basis": "MIN_BEARING"}
    f = R.lintel_face(li, 0.20)
    assert f["open"] and f["face_m2"] == [A(0.32), None] and f["min_bearing_face_hi_m2"] == A(0.34)
    b = R.material_base(9.48, [f])
    g = R.material_line(b, 4.5, "kg")
    assert b["state"] == "HELD" and g["value"] is None and g["range"] is None
    assert g["at_most_beside"] == A(41.22)                          # (9.48 - 0.32) x 4.5, never the false 41.13 low end


def test_held_by_name_hi_without_a_basis_refused():
    li = {"opening_id": "DK", "state": "HELD_BY_NAME", "section_B_D_m": [0.20, 0.20], "length_m": [1.60, 1.70]}
    with pytest.raises(R.RuleError, match="basis"):
        R.lintel_face(li, 0.20)


def test_bounded_end_without_a_ceiling_or_held_end_opens_the_length():
    for ends in (_hbn_ends(ceiling=None), _hbn_ends(start_state="HELD")):
        c = R.ceiling_length("DK", [1.60, 1.70], ends)
        assert c["length_m"] == [A(1.60), None] and c["length_hi_basis"] is None


@pytest.mark.parametrize("args, match", [
    (([1.60, 1.75], _hbn_ends()), "basis unknown"),               # T-524 hi != lo + deficit a
    (([1.70, 1.60], _hbn_ends()), "inverted"),
    (([1.60, 1.70], _hbn_ends(ceiling=0.30)), "below the printed minimum"),
    (([1.60, 1.70], _hbn_ends(a=0.45)), "not a deficit"),
    (([1600, 1700], _hbn_ends()), "metres|above"),
])
def test_ceiling_length_adverse_refused(args, match):
    with pytest.raises(R.RuleError, match=match):
        R.ceiling_length("DK", *args)


def test_no_midpoint_no_single_figure_on_a_range():
    g = R.material_line(base_of(9.48, lz()), 4.5, "kg")
    assert g["value"] is None and 41.085 not in g["range"]


# ------------------------------------------------------------------ the 2 staged glue hosts (development villa) ----
@pytest.fixture(scope="module")
def app():
    return AP.build()


def _host(app, lid):
    return [h for h in app["hosts"] if h["host_line_id"] == lid][0]


def test_gf_host_d_gf_06_ranged_face(app):
    h = _host(app, "L-a3f88ecda2402f67c500")
    assert h["before"]["glue_kg"] == A(23.535)
    f = h["after_r_t498_2"]["base"]["faces"][0]
    # T-524 [1.40, 1.54] is min-bearing at the BOUNDED START (0.759 m to a column, T-516): L_hi = 1.00 + 0.759 + 0.140
    assert f["opening_id"] == "D-GF-06" and f["length_m"] == [A(1.40), A(1.899)]
    assert f["t524_length_m"] == [A(1.40), A(1.54)]
    assert f["face_m2"] == [A(0.28), A(0.3798)]                                         # 0.20 x [1.40, 1.899]
    assert h["after_r_t498_2"]["base"]["base_m2"] == [A(5.2102), A(5.31)]
    assert h["after_r_t498_2"]["glue_kg"]["range"] == [A(23.4459), A(23.895)]          # Checker r1 re-derivation
    assert h["after_r_t498_2"]["bags_25kg_net"]["range"] == [A(0.937836), A(0.9558)]


def test_1f_host_held_by_the_four_min_bearing_maxima(app):
    h = _host(app, "L-2fdc0f971a94348ec855")
    a = h["after_r_t498_2"]
    faces = {f["opening_id"]: f for f in a["base"]["faces"]}
    assert faces["W14"]["face_m2"] == [A(0.975), A(1.23)]          # 0.30 x [3.25, 4.10]
    assert faces["W15"]["face_m2"] == [A(0.47), A(0.5674)]         # 0.20 x [2.35, 2.837]
    # W18: T-524 0.8673 (START 0.000 at a column, END kept at 0.40); V3 END ceiling 0.577 (T-527) -> 0.8673 + 0.177
    assert faces["W18"]["length_m"] == [A(0.8673), A(1.0443)]
    assert faces["W18"]["face_m2"] == [A(0.17346), A(0.20886)]
    assert sorted(k for k, f in faces.items() if f["open"]) == ["W16", "W19", "W20", "W24"]
    assert a["base"]["state"] == "HELD" and a["glue_kg"]["value"] is None
    assert a["glue_kg"]["at_most_beside"] == A(451.60893)           # (101.976 - 1.61846) x 4.5


def test_conditional_reading_reproduces_t530(app):
    h = _host(app, "L-2fdc0f971a94348ec855")
    c = h["conditional_beside"]
    assert c["agrees_with_t530"] and c["glue_kg"]["range"] == [A(443.27313), A(451.60893)]
    assert c["base_m2"] == [A(98.50514), A(100.35754)]             # 101.976 - 1.9709 - 1.5 .. - 1.61846


def test_glue_group_strict_and_conditional(app):
    g = app["glue_group"]
    assert g["after_conditional"]["at_least"] == [A(35.387755), A(36.226627)]
    s = g["after_r_t498_2"]
    assert s["status"] == "HELD"
    # 35.42625 - 17.77878 (host 1 leaves: open) - 0.9414 + 0.937836; 36.19665 - 18.04878 - 0.9414 + 0.9558
    assert s["at_least"] == [A(17.643906), A(18.16227)] and s["to_buy_at_least"] == [18, 19]
    assert app["released_quantities_changed"] == 0


def test_gf_ceiling_equals_t516_own_length_ceiling(app):
    """independent check: the ceiling-bound L_hi of D-GF-06 equals T-516's own length_hi_m (w + a_s + a_e)."""
    import json
    t516 = {r["opening_id"]: r for r in json.loads((ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json")
                                                    .read_text(encoding="utf-8"))["rows"]}
    f = _host(app, "L-a3f88ecda2402f67c500")["after_r_t498_2"]["base"]["faces"][0]
    assert f["length_m"][1] == A(t516["D-GF-06"]["length_hi_m"]) == A(1.899)
