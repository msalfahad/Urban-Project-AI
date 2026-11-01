"""T-433: a roll-up's HELD figure split by the item that holds it (R-T433-1 .. 7) and the Alsenan r4 split.

Villa R433 (hand fixture, NOT Alsenan). Roll-up HELD parts (engine 0 held - other side, m3):
  GB-A  held annex runs: his section 0.30 x 0.50 = 0.15 m2 x 12.00 m              = -1.800
  GB-A2 the same runs' length fields through two necks 2 x 0.40 m x 0.15           = +0.120  (same lines, same blocker)
  GB-C  court runs 4.00 m x 0.15                                                   = -0.600
  CL-X  two columns with a plan-vs-schedule conflict, withdrawn valued 0.48 + 0.36  = -0.840
  BL    blinding: one layer of his over a rectangle, engine 3 held lines            = -2.500  (one lump: JOINT)
  SL    slab cell held by an engine reading defect, own panels 20.0 m2 x 0.10       = -2.000
  HELD = -1.800 + 0.120 - 0.600 - 0.840 - 2.500 - 2.000 = -7.620
Items: annex depth (GB-A + GB-A2 = -1.680, RFI-1), court (-0.600, RFI_MISSING), column band (-0.840, RFI-2),
  blinding JOINT (-2.500, RFI-3 + RFI-4), slab cell ENGINE (-2.000, drawing named).  Sum -7.620.
Investigation ranked: [slab cell]; RFI items ranked: blinding, annex, column, court.
"""
import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t433"))
import t433_rules as R  # noqa: E402

PARTS = {"GB-A": round(-0.15 * 12.0, 6), "GB-A2": round(0.15 * 2 * 0.40, 6), "GB-C": round(-0.15 * 4.0, 6),
         "CL-X": round(-(0.48 + 0.36), 6), "BL": -2.5, "SL": round(-20.0 * 0.10, 6)}
HELD = -7.62
DS = ["sheet S-3 (ground-beam sections)"]


def items():
    return [
        dict(id="A", parts=["GB-A", "GB-A2"], m3=-1.68, lines=["L-a1", "L-a2"], blockers=["annex depth"],
             route="DESIGNER", rfi=["RFI-1"], drawings_searched=DS),
        dict(id="C", parts=["GB-C"], m3=-0.6, lines=["L-c1"], blockers=["court section"], route="DESIGNER",
             rfi=["RFI_MISSING"], drawings_searched=DS),
        dict(id="X", parts=["CL-X"], m3=-0.84, lines=["L-x1", "L-x2"], blockers=["outline vs schedule"],
             route="DESIGNER", rfi=["RFI-2"], drawings_searched=["S-2", "S-5"]),
        dict(id="B", parts=["BL"], m3=-2.5, lines=["L-b1", "L-b2", "L-b3"], joint=True,
             blockers=["projection not printed", "strap blinding not printed"], route="DESIGNER",
             rfi=["RFI-3", "RFI-4"], drawings_searched=["S-3", "S-4"]),
        dict(id="S", parts=["SL"], m3=-2.0, lines=["L-s1"], blockers=["engine reads free columns"], route="ENGINE",
             settle_drawing="S-1 slab-on-grade plan, own panels 20.0 m2 x T 0.10", drawings_searched=["S-1"]),
    ]


BESIDE = [{"line_id": "L-p1", "blocker": "parapet RC not detailed"}]


def test_normal_split_re_adds_exactly():
    assert R.check_items(items(), PARTS, HELD, BESIDE) == pytest.approx(HELD, abs=1e-9)


def test_order_invariant():
    assert R.check_items(list(reversed(items())), PARTS, HELD, BESIDE) == pytest.approx(HELD, abs=1e-9)


def test_ranking():
    inv, rfi, rfi_rank = R.ranked(items())
    assert [i["id"] for i in inv] == ["S"]
    assert [i["id"] for i in rfi] == ["B", "A", "X", "C"]
    assert rfi_rank[0][1] == pytest.approx(-2.5) and dict(rfi_rank)["RFI-1"] == pytest.approx(-1.68)


def _refused(its, parts=PARTS, held=HELD, beside=BESIDE, match=None):
    with pytest.raises(R.SplitError, match=match):
        R.check_items(its, parts, held, beside)


def test_adverse_part_in_two_items():
    its = items()
    its[1]["parts"] = ["GB-C", "GB-A2"]
    its[1]["m3"] = -0.48
    its[0]["parts"], its[0]["m3"] = ["GB-A", "GB-A2"], -1.68
    _refused(its, match="part GB-A2")


def test_adverse_part_left_out():
    its = items()[:-1]
    _refused(its, held=-5.62, match="parts in no item")


def test_adverse_line_in_two_items():
    its = items()
    its[2]["lines"] = ["L-x1", "L-a1"]
    _refused(its, match="line L-a1")


def test_adverse_beside_line_also_in_item():
    _refused(items(), beside=[{"line_id": "L-b1", "blocker": "x"}], match="beside line")


def test_adverse_beside_without_blocker():
    _refused(items(), beside=[{"line_id": "L-z", "blocker": ""}], match="no blocker")


def test_adverse_items_not_re_adding_to_rollup():
    _refused(items(), held=-7.50, match="R-T433-1")


def test_adverse_item_figure_not_its_parts():
    its = items()
    its[0]["m3"] = -1.80        # the neck length fields dropped from the item figure
    _refused(its, match="re-add")


def test_adverse_held_zero_or_positive():
    parts = dict(PARTS, Z=0.0)
    its = items() + [dict(id="Z", parts=["Z"], m3=0.0, lines=[], blockers=["z"], route="DESIGNER", rfi=["RFI-9"],
                          drawings_searched=DS)]
    _refused(its, parts=parts, match="R-T433-4")
    parts = dict(PARTS, P=0.2)
    its[-1].update(parts=["P"], m3=0.2)
    _refused(its, parts=parts, held=HELD + 0.2, match="R-T433-4")


def test_adverse_unknown_part():
    its = items()
    its[1]["parts"] = ["GB-C", "NOPE"]
    _refused(its, match="not a HELD part")


def test_adverse_no_drawing_searched():
    its = items()
    its[1]["drawings_searched"] = []
    _refused(its, match="no drawing searched")


def test_adverse_drawing_route_without_drawing():
    its = items()
    its[4]["route"] = "DRAWING"
    del its[4]["settle_drawing"]
    _refused(its, match="DRAWING route")


def test_adverse_designer_without_rfi():
    its = items()
    its[1]["rfi"] = []
    _refused(its, match="RFI id")


def test_adverse_joint_blockers_split_by_share_refused_without_joint_flag():
    its = items()
    del its[3]["joint"]
    _refused(its, match="JOINT")


def test_adverse_value_chosen_for_held_line():
    its = items()
    its[0]["value"] = 1.68
    _refused(its, match="never values")


def test_adverse_unknown_route():
    its = items()
    its[0]["route"] = "OWNER_PICKS"
    _refused(its, match="route")


# ---------------- Alsenan (committed merged summaries + committed candidate lines; no private input needed)
sys.path.insert(0, str(ROOT / "research" / "agents_t433"))


@pytest.fixture(scope="module")
def alsenan():
    import t433_alsenan as A
    return A.run()


def test_alsenan_held_total_and_items(alsenan):
    assert alsenan["held_total_m3"] == pytest.approx(-116.428339, abs=2e-6)
    assert len(alsenan["items"]) == 25 and len(alsenan["parts"]) == 34


def test_alsenan_pins(alsenan):
    m = {i["id"]: i["m3"] for i in alsenan["items"]}
    assert m["I-01"] == pytest.approx(-47.055) and m["I-02"] == pytest.approx(-8.805)
    assert m["I-05"] == pytest.approx(-0.18 * 31.5364 + 0.27594, abs=1e-6)       # D-35 annex incl. neck fields
    assert m["I-11"] == pytest.approx(-0.18 * 16.5989, abs=1e-6)                 # D-34
    assert m["I-21"] == pytest.approx(-0.18 * 5.7, abs=1e-6)                     # court
    assert m["I-04"] == pytest.approx(-(5.208 + 1.4625)) and m["I-16"] == pytest.approx(-(0.756 + 1.0125))
    assert m["I-06"] == pytest.approx(-(2.524568 + 1.263975 + 0.682), abs=1e-6)


def test_alsenan_routes(alsenan):
    br = alsenan["by_route"]
    assert br["ENGINE"] == pytest.approx(-3.56054) and br["SUPPLIER"] == pytest.approx(-1.65)
    assert br["DRAWING"] == 0
    assert alsenan["investigation_ranked"] == ["I-07"]


def test_alsenan_beside_lines_disjoint(alsenan):
    used = {x for i in alsenan["items"] for x in i["lines"]}
    beside = {b["line_id"] for b in alsenan["beside_no_comparison_term"]}
    assert not used & beside and "L-cda8f41522dc6f42b3d6" in beside


def test_alsenan_summary_reproduces(alsenan):
    import json
    s = json.loads((ROOT / "research" / "agents_t433" / "summary_t433.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(alsenan, sort_keys=True))


def test_alsenan_adverse_one_part_moved_breaks_family_closure(monkeypatch):
    import t433_alsenan as A
    monkeypatch.setitem(A.UNCHANGED_SPLIT, "CL-NECK", -8.705)
    with pytest.raises(AssertionError):
        A.build()
