"""T-732: formwork of moved concrete (R-T732-1 / -2). Villa V732 is hand-made (not the development villa): a roof plate
with base +6.00, a 0.25-zone (top >= 9.40) and a 0.20-zone (top >= 9.35), finished roof +10.00 (h <= 4.00):
- K1 0.30 x 0.60 column touching both zones, framed by settled 0.50 beams, joint record 0.35 m2 at D 0.50;
- K2 the same column with an unmarked framing piece whose depth may reach 1.00 (D open 0.50 .. 1.00);
- K3 a planted column drawn 0.20 x 0.40, text 0.20 x 0.50, standing on a beam and running to the soffit of a settled
  0.60 beam (concrete height basis = the controlling soffit);
- K4 a tank column with an open stand (member AT_LEAST, deepest framing 1.20).
Hand figures are written out in each test. The last tests rebuild the development-villa output from committed files."""
from __future__ import annotations

import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t732"))
import t732_rules as R  # noqa: E402

TOPS = {"Z25": "9.40", "Z20": "9.35"}


def _k1(**kw):
    # concrete: 0.18 x (9.40 - 6.00) = 0.612 .. 0.18 x 4.00 = 0.72 (column top on the 0.25 zone)
    args = dict(member={"cls": "BOUNDED", "low": "0.612", "high": "0.72"}, sections_m=[("0.30", "0.60")],
                base="6.00", panel_tops_lo=[TOPS["Z25"], TOPS["Z20"]], panel_t=["0.25", "0.20"], h_lo_conc="3.40",
                h_hi="4.00", d_min="0.50", d_max="0.50", d_settled=True,
                faces=[{"face_id": "J1", "kind": "JOINT", "fig": "0.35", "recorded_at": "D_MIN"},
                       {"face_id": "J2", "kind": "JOINT_CAP", "hi": "0.06"}])
    args.update(kw)
    return R.column_line("K1", **args)


# ---------------------------------------------------------------- normal
def test_k1_settled_depth_bounded():
    # shaft low 1.80 x (9.35 - 6.00 - 0.50) = 1.80 x 2.85 = 5.13 (least zone top, not the column's 9.40)
    # shaft high 1.80 x (4.00 - 0.50) = 6.30; joint 0.35 independent (no storey height in it); cap 0 .. 0.06
    r = _k1()
    assert r["cls"] == "BOUNDED"
    assert (r["low"], r["high"]) == (X("5.480000"), X("6.710000"))
    assert r["shaft_h_lo"] == X("2.85") and r["top_lo_used"] == X("9.35")
    # envelope 1.80 x (4.00 - 0.20) = 6.84 >= 6.71
    assert r["envelope"] == X("6.840")


def test_k2_open_depth_floor_is_shaft_high_at_d_min():
    # D 0.50 .. 1.00: low 1.80 x (3.35 - 1.00) = 4.23; high at D_min: 6.30 + 0.35 + 0.06 = 6.71
    r = _k1(d_max="1.00", d_settled=False)
    assert (r["cls"], r["low"], r["high"]) == ("BOUNDED", X("4.230000"), X("6.710000"))
    deps = {f["face_id"]: f["dep"] for f in r["faces"]}
    assert deps == {"SHAFT": "REDERIVED", "J1": "AT_D_MIN", "J2": "CAP_ONLY"}


def test_k3_planted_column_controlling_soffit_basis():
    # concrete 0.08 x (9.35 - 6.00 - 0.60) = 0.08 x 2.75 = 0.22 .. 0.10 x 3.40 = 0.34; shaft 1.20 x 2.75 = 3.30 ..
    # 1.40 x 3.40 = 4.76 (no second deduction of D, no slab t); joint record at one section -> DEPENDENT -> AT_LEAST
    r = R.column_line("K3", member={"cls": "BOUNDED", "low": "0.22", "high": "0.34"},
                      sections_m=[("0.20", "0.40"), ("0.20", "0.50")], base="6.00", panel_tops_lo=["9.35"],
                      panel_t=["0.20"], h_lo_conc="2.75", h_hi="3.40", d_min="0.60", d_max="0.60", d_settled=True,
                      faces=[{"face_id": "J", "kind": "JOINT", "fig": "0.40", "recorded_at": "D_MIN"},
                             {"face_id": "E", "kind": "EDGE", "fig": "0.07"}], basis="CTRL_SOFFIT")
    assert (r["cls"], r["low"], r["high"]) == ("AT_LEAST", X("3.300000"), None)
    assert r["faces"][0]["high"] == X("4.76")


def test_k4_tank_column_at_least():
    # member AT_LEAST 0.18 x 3.40 = 0.612; shaft floor 1.80 x (9.40 - 6.00 - 1.20) = 3.96, high open (stand open)
    r = R.column_line("K4", member={"cls": "AT_LEAST", "low": "0.612", "high": None}, sections_m=[("0.30", "0.60")],
                      base="6.00", panel_tops_lo=["9.40"], panel_t=["0.25"], h_lo_conc="3.40", h_hi=None,
                      d_min="0.50", d_max="1.20", d_settled=False,
                      faces=[{"face_id": "J", "kind": "JOINT", "fig": "0.70", "recorded_at": "UNSTATED"}])
    assert (r["cls"], r["low"], r["high"]) == ("AT_LEAST", X("3.960000"), None)


def test_mirror_rotation_and_panel_order_invariant():
    a = _k1()
    b = _k1(sections_m=[("0.60", "0.30")], panel_tops_lo=[TOPS["Z20"], TOPS["Z25"]], panel_t=["0.20", "0.25"])
    assert (a["low"], a["high"]) == (b["low"], b["high"])


def test_census_moves_only_through_a_face_read():
    old = {"F1": ("BOUNDED", "0.303", "0.425"), "F2": ("BLANK", None, None), "F3": ("RELEASED", "1", "1")}
    new = {"F1": ("BOUNDED", "0.3287", "0.425"), "F2": ("AT_LEAST", "0.3287", None), "F3": ("RELEASED", "1", "1")}
    c = R.census(old, new, {"F1": {}})
    assert [(x["line_id"], x["state"]) for x in c] == [("F1", "RESTATED"), ("F2", "MOVED_NOT_RESTATED")]


# ---------------------------------------------------------------- adverse
def test_adverse_concrete_bound_that_does_not_decompose_is_refused():
    with pytest.raises(R.Refused, match="does not decompose"):
        _k1(member={"cls": "BOUNDED", "low": "0.640", "high": "0.72"})


def test_adverse_missing_panel_top_never_defaults():
    with pytest.raises(R.Refused, match="panel top"):
        _k1(panel_tops_lo=[])


def test_adverse_mm_read_as_m():
    with pytest.raises(R.Refused, match="unit error"):
        _k1(sections_m=[("300", "600")])


def test_adverse_missing_joint_figure_is_not_zero():
    with pytest.raises(R.Refused, match="missing"):
        _k1(faces=[{"face_id": "J1", "kind": "JOINT", "fig": None}])


def test_adverse_deepest_member_reaches_base():
    with pytest.raises(R.Refused, match="no floor"):
        _k1(d_max="3.50", d_settled=False)


def test_adverse_d_inverted_and_planted_with_open_d():
    with pytest.raises(R.Refused, match="below D_min"):
        _k1(d_min="0.80", d_max="0.50")
    with pytest.raises(R.Refused, match="settled D"):
        R.column_line("K3", member={"cls": "BOUNDED", "low": "0.22", "high": "0.34"},
                      sections_m=[("0.20", "0.40"), ("0.20", "0.50")], base="6.00", panel_tops_lo=["9.35"],
                      panel_t=["0.20"], h_lo_conc="2.75", h_hi="3.40", d_min="0.60", d_max="0.80", d_settled=False,
                      faces=[], basis="CTRL_SOFFIT")


def test_adverse_record_above_envelope_refused():
    with pytest.raises(R.Refused, match="envelope"):
        _k1(faces=[{"face_id": "J1", "kind": "JOINT", "fig": "0.90", "recorded_at": "D_MIN"}])


def test_adverse_blank_member_has_no_floor():
    with pytest.raises(R.Refused, match="no floor to follow"):
        _k1(member={"cls": "BLANK", "low": None, "high": None})


def test_adverse_restated_without_move_refused():
    with pytest.raises(R.Refused, match="without a member move"):
        R.census({"F": ("BOUNDED", "1", "2")}, {"F": ("BOUNDED", "1", "2")}, {"F": {}})


# ---------------------------------------------------------------- development villa (committed inputs only)
def test_alsenan_rebuild_matches_committed():
    import t732_alsenan as A
    doc = A.make_doc()
    assert A.dump(doc) == A.OUT_JSON.read_text(encoding="utf-8")
    got = {r["handle"]: (r["class_after"], r["low"], r["high"]) for r in doc["restated"]}
    assert got == {"418": ("BOUNDED", "3.720600", "7.218122"), "41E": ("BOUNDED", "2.893800", "5.630111"),
                   "41B": ("BOUNDED", "4.206000", "5.582200"), "421": ("BOUNDED", "4.152000", "5.528200"),
                   "778": ("AT_LEAST", "3.020400", None), "40F": ("AT_LEAST", "2.921800", None),
                   "424": ("AT_LEAST", "2.893800", None)}
    assert len(doc["census"]) == 7 and all(c["state"] == "RESTATED" for c in doc["census"])
    f = doc["family"]
    assert (f["bounded_low_m2"], f["bounded_high_m2"], f["at_least_m2"]) == ("102.914777", "127.151372", "107.379697")
    assert f["by_class"] == {"BOUNDED": 30, "AT_LEAST": 35, "FIX_ROW": 54, "BLANK_NAMED": 251}
