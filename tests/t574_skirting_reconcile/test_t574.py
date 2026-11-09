"""T-574 skirting reconciliation (R-T574-1): a non-Alsenan hand fixture, adverse cases, and the development-villa
build pinned (byte-identical rebuild, closures, units)."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t574"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t574_rules")
_spec = importlib.util.spec_from_file_location("t574_alsenan", HERE / "t574_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal


# ---- hand fixture (not Alsenan): room 4.00 x 3.00, one 0.90 m door --------------------------------------------------
def test_room_fixture_one_door():
    faces = [("4.00", "DRY"), ("3.00", "DRY"), ("4.00", "DRY"), ("3.00", "DRY")]
    assert R.room_skirting(faces, [("D1", "0.90")]) == D("13.10")        # 2 x (4.00 + 3.00) - 0.90


def test_room_fixture_mirror_rotation_and_mm():
    faces = [("3.00", "DRY"), ("4.00", "DRY"), ("3.00", "DRY"), ("4.00", "DRY")]   # rotated / mirrored order
    assert R.room_skirting(faces, [("D1", "0.90")]) == D("13.10")
    mm = [("4000", "DRY"), ("3000", "DRY"), ("4000", "DRY"), ("3000", "DRY")]
    assert R.room_skirting(mm, [("D1", "900")], unit="mm") == D("13.10")


def test_tiled_and_open_faces_take_no_skirting():
    faces = [("4.00", "DRY"), ("3.00", "TILED"), ("4.00", "DRY"), ("3.00", "NO_WALL")]
    assert R.room_skirting(faces, [("D1", "0.90")]) == D("7.10")


def test_adverse_skirting_on_a_tiled_face_refused():
    with pytest.raises(R.RuleError, match="tiled face"):
        R.skirt_face("3.00", "TILED")
    with pytest.raises(R.RuleError, match="no wall base"):
        R.skirt_face("1.55", "NO_WALL")


def test_adverse_door_twice_jamb_unit_missing():
    faces = [("4.00", "DRY"), ("3.00", "DRY")]
    with pytest.raises(R.RuleError, match="twice"):
        R.room_skirting(faces, [("D1", "0.90"), ("D1", "0.90")])
    with pytest.raises(R.RuleError, match="without its id"):
        R.room_skirting(faces, [("", "0.90")])
    with pytest.raises(R.RuleError, match="jamb"):
        R.jamb_return("0.15")
    with pytest.raises(R.RuleError, match="unit"):
        R.room_skirting([("4.00", "DRY")], unit="ft")
    with pytest.raises(R.RuleError, match="never 0"):
        R.D(None)


def test_flight_developed_length_and_plan_refused():
    s = R.flight_length("3.00", "1.80", form="sloped")
    assert abs(s - D("3.498571")) < D("0.000001")                       # hypot(3.00, 1.80) = 3.499 lm
    assert R.flight_length("3.00", "1.80", form="zigzag") == D("4.80")
    with pytest.raises(R.RuleError, match="plan length"):
        R.flight_length("3.00", "1.80", form="plan")


def test_flight_bounds():
    assert R.flight_bound("1.60", "1.140175", "HELD-FORM") == (D("1.140175"), D("1.60"))
    assert R.flight_bound("1.716668", "1.233936", "HELD") == (D(0), D("1.716668"))
    assert R.flight_bound(None, None, "UNKNOWN") == (D(0), None)
    with pytest.raises(R.RuleError):
        R.flight_bound("1.60", None, "HELD-FORM")


# ---- reconcile (synthetic) --------------------------------------------------------------------------------------------
def _fix():
    lines = {"L1": {"class": "ROOM", "unit": "lm", "value": "13.10", "status": "DRAWING-CONFIRMED"},
             "L2": {"class": "STAIR_FLIGHT", "unit": "lm", "value": None, "status": "HELD"},
             "L3": {"class": "ROOM", "unit": "lm", "value": None, "status": "NOT_APPLICABLE"}}
    rows = {"R1": {"unit": "lm", "value": "14.00"}, "R2": {"unit": "lm", "value": "3.00"}}
    groups = [
        {"id": "room", "unit": "lm", "lines": ["L1", "L3"], "rows": ["R1"],
         "causes": [{"label": "door 0.90 (his gross perimeter)", "verdict": "RULE_DIFFERENCE", "kind": "DEDUCTION",
                     "amount": "-0.90", "source": "fixture"}]},
        {"id": "flight", "unit": "lm", "lines": ["L2"], "rows": ["R2"],
         "causes": [{"label": "flight held by form", "verdict": "HELD", "kind": "HELD", "amount": "-3.00",
                     "bound": ("3.00", "4.80"), "source": "fixture"}]}]
    return groups, lines, rows


def test_reconcile_normal():
    g, l, r = _fix()
    t = R.reconcile(g, l, r)
    assert t["groups"][0]["gap"] == D("-0.90") and t["groups"][0]["pct"] == D("-6.43")
    assert t["groups"][1]["pct"] is None and t["groups"][1]["held_bound"] == [D("3.00"), D("4.80")]
    assert t["totals"]["lm"]["comparable"] is False


def test_adverse_m2_row_compared_as_lm_refused():
    g, l, r = _fix()
    r["R1"] = {"unit": "m2", "value": "14.00"}
    with pytest.raises(R.RuleError, match="never m2"):
        R.reconcile(g, l, r)


def test_adverse_nr_row_in_lm_group_refused():
    g, l, r = _fix()
    r["R1"] = {"unit": "nr", "value": "14"}
    with pytest.raises(R.RuleError, match="compared in an lm group"):
        R.reconcile(g, l, r)


def test_adverse_held_as_zero_or_with_value_refused():
    g, l, r = _fix()
    l["L2"]["value"] = "0"
    with pytest.raises(R.RuleError, match="HELD with a value"):
        R.reconcile(g, l, r)


def test_adverse_verified_open_residual_double_use():
    g, l, r = _fix()
    l["L1"]["status"] = "VERIFIED"
    with pytest.raises(R.RuleError, match="Checker"):
        R.reconcile(g, l, r)
    g, l, r = _fix()
    g[0]["causes"][0]["amount"] = "-0.80"
    with pytest.raises(R.RuleError, match="close exactly"):
        R.reconcile(g, l, r)
    g, l, r = _fix()
    g[0]["causes"][0]["label"] = " "
    with pytest.raises(R.RuleError, match="unnamed"):
        R.reconcile(g, l, r)
    g, l, r = _fix()
    g[1]["lines"].append("L1")
    with pytest.raises(R.RuleError, match="two groups"):
        R.reconcile(g, l, r)
    g, l, r = _fix()
    g[1]["causes"][0]["amount"] = "-5.00"
    with pytest.raises(R.RuleError, match="outside its bound"):
        R.reconcile(g, l, r)


# ---- development villa (merged inputs only; sha256-pinned) ------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_rebuild_byte_identical(built):
    assert (HERE / "out" / "T574_SKIRTING_RECONCILE.json").read_text(encoding="utf-8") == A.dump(built)


def test_room_table_closes_to_both_totals(built):
    t = built["room"]
    assert t["totals"]["lm"]["ours"] == "197.278592" and t["totals"]["lm"]["his"] == "282.85"
    assert sum(D(g["ours"]) for g in t["groups"]) == D("197.278592")
    assert sum(D(g["his"]) for g in t["groups"]) == D("282.85")
    for g in t["groups"]:
        assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"])
    bv = t["by_verdict"]
    assert sum(D(v) for v in bv.values()) == D("-85.571408")
    assert bv["lm RULE_DIFFERENCE"] == "-43.62"


def test_candidate_lines_split_once(built):
    released = D(built["candidate_fin_skirting_released_lm"])
    assert released == D("209.428592")
    assert D(built["room"]["totals"]["lm"]["ours"]) + D(built["stairs"]["totals"]["lm"]["ours"]) == released
    ids = [l for s in ("room", "stairs") for g in built[s]["groups"] for l in g["lines"]]
    assert len(ids) == len(set(ids)) == 97      # 53 FIN.SKIRTING + 2 x 22 flight lines


def test_stairs_units_apart_and_held_bounded(built):
    s = built["stairs"]
    assert s["totals"]["lm"]["his"] == "29.87" and s["totals"]["nr"]["his"] == "96"
    assert s["totals"]["lm"]["pct"] is None and s["totals"]["nr"]["pct"] is None
    lo = sum(D(c["bound"][0]) for g in s["groups"] for c in g["causes"]
             if c["verdict"] == "HELD" and "form not chosen" in c["label"])
    assert lo == D("17.009049")                 # T-501 sloped total of the 13 HELD-FORM pieces


def test_gross_vs_gross(built):
    gg = built["room"]["gross_vs_gross"]
    assert gg["outline_gap"] == "-6.690903" and gg["ours_outline"] == "276.159097"


def test_adverse_his_label_not_lm_refused():
    cells = A.his_cells()
    cells["COV.F16"] = cells["COV.F15"]           # the internal skirting total labelled like the m2 floors row
    with pytest.raises(R.RuleError, match="is not lm"):
        A.rows_table(cells)


def test_no_client_text_in_outputs():
    arabic = re.compile("[" + chr(0x0600) + "-" + chr(0x06FF) + "]")
    for p in list(HERE.rglob("*")) + [Path(__file__)]:
        if p.is_file() and p.suffix in (".py", ".json", ".md", ".csv"):
            assert not arabic.search(p.read_text(encoding="utf-8")), p
    json.loads((HERE / "out" / "T574_SKIRTING_RECONCILE.json").read_text(encoding="utf-8"))
