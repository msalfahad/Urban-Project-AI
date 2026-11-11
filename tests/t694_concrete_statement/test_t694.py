"""T-694 R-T694-1 (partition), -2 (PROPOSED overlay), -3 (leader association), -4 (cause register). Villa V694 is
hand-made (not the development villa); the last tests rebuild the development-villa statement on V3.0.68 from committed
files only and check it against the line index and the master census to the last digit."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t694"))
import t694_rules as T  # noqa: E402


def ln(lid, cls, net=None, lo=None, hi=None, code="STR.CONC.COLUMN", unit="m3"):
    return {"line_id": lid, "item_code": code, "class": cls, "measured_net": net, "held_low": lo, "held_high": hi,
            "unit": unit, "element_id": lid}


# V694 by hand. C1 released 0.20 x 0.50 x 3.00 = 0.300; C2 held, section 0.20 x 0.40 .. 0.20 x 0.50, height 3.00 ..
# 3.50: 0.240 .. 0.350; C3 held blank (top datum not printed, section in conflict); C4 excluded (not present); a rebar
# line of another trade beside them.
def villa():
    return [ln("C1", "RELEASED", net=0.3), ln("C2", "HELD", lo=0.24, hi=0.35), ln("C3", "HELD"),
            ln("C4", "EXCLUDED"), ln("R1", "RELEASED", net=12.5, code="STR.REBAR", unit="kg")]


# ------------------------------------------------------------------------------------------------ R-T694-1
def test_partition_normal_by_hand():
    p = T.partition(villa(), prefix="STR.CONC", unit="m3")
    assert {k: [x["line_id"] for x in v] for k, v in p.items()} == {
        "RELEASED": ["C1"], "HELD_BOUNDED": ["C2"], "HELD_BLANK": ["C3"], "EXCLUDED": ["C4"]}
    t = T.totals(p)
    assert t["released"]["m3"] == "0.300000"
    assert (t["held_bounded"]["low"], t["held_bounded"]["high"]) == ("0.240000", "0.350000")
    assert t["engine_range"] == ["0.540000", "OPEN"]  # a blank line keeps the high end OPEN, never 0


@pytest.mark.parametrize("bad", [
    ln("C5", "HELD", lo=0.1),                 # one end only: in no bucket
    ln("C5", "HELD", net=0.2),                # a held line carrying a released number: in no bucket
    ln("C5", "RELEASED"),                     # released without a number
    ln("C5", "PROVISIONAL", net=0.2),         # unknown class
    ln("C5", "EXCLUDED", net=0.1),            # an excluded line carrying a quantity
])
def test_partition_refuses_a_line_in_no_bucket(bad):
    with pytest.raises(T.Refused, match="no bucket"):
        T.partition(villa() + [bad], prefix="STR.CONC", unit="m3")


def test_partition_refuses_a_line_in_two_buckets():
    with pytest.raises(T.Refused, match="two buckets"):
        T.partition(villa() + [ln("C5", "RELEASED", net=0.2, lo=0.1, hi=0.3)], prefix="STR.CONC", unit="m3")
    with pytest.raises(T.Refused, match="listed twice"):
        T.partition(villa() + [ln("C2", "HELD")], prefix="STR.CONC", unit="m3")


def test_partition_refuses_mixed_units():
    with pytest.raises(T.Refused, match="unit"):
        T.partition(villa() + [ln("C6", "RELEASED", net=300, unit="l")], prefix="STR.CONC", unit="m3")


# ------------------------------------------------------------------------------------------------ R-T694-2
def test_overlay_closes_an_open_end_and_raises_a_low():
    lines = villa()
    out, rows = T.overlay(lines, [
        {"line_id": "C3", "before": None, "after": ["0.24", "0.35"], "source": "ledger L"},
        {"line_id": "C2", "before": ["0.24", "0.35"], "after": ["0.26", "0.35"], "source": "ledger L"}])
    p = T.totals(T.partition(out, prefix="STR.CONC", unit="m3"))
    assert p["held_bounded"]["lines"] == 2 and p["held_blank"]["lines"] == 0
    assert (p["held_bounded"]["low"], p["held_bounded"]["high"]) == ("0.500000", "0.700000")
    assert p["engine_range"] == ["0.800000", "1.000000"]
    assert lines[2]["held_low"] is None  # the candidate itself is never changed
    assert [r["before"] for r in rows] == ["blank (OPEN)", ["0.240000", "0.350000"]]


@pytest.mark.parametrize("move,msg", [
    ({"line_id": "C2", "before": ["0.24", "0.35"], "after": ["0.20", "0.35"], "source": "x"}, "widened"),
    ({"line_id": "C2", "before": ["0.24", "0.35"], "after": ["0.24", "0.40"], "source": "x"}, "widened"),
    ({"line_id": "C2", "before": ["0.24", "0.34"], "after": ["0.25", "0.34"], "source": "x"}, "before"),
    ({"line_id": "C2", "before": ["0.24", "0.35"], "after": None, "source": "x"}, "blank / released"),
    ({"line_id": "C1", "before": None, "after": ["0.3", "0.3"], "source": "x"}, "HELD lines only"),
    ({"line_id": "C9", "before": None, "after": ["0.1", "0.2"], "source": "x"}, "not on the candidate"),
    ({"line_id": "C3", "before": None, "after": ["0.3", "0.2"], "source": "x"}, "not ordered"),
    ({"line_id": "C3", "before": None, "after": ["0.1", "0.2"], "source": ""}, "no source"),
])
def test_overlay_refusals(move, msg):
    with pytest.raises(T.Refused, match=msg):
        T.overlay(villa(), [move])


def test_overlay_refuses_a_line_moved_twice():
    m = {"line_id": "C3", "before": None, "after": ["0.1", "0.2"], "source": "x"}
    with pytest.raises(T.Refused, match="moved twice"):
        T.overlay(villa(), [m, dict(m)])


# ------------------------------------------------------------------------------------------------ R-T694-3
# V694 plan: text T at (0, 0) 'P.C 20x50'; outline A (0.20 x 0.50) 350 mm east of the text (the nearest); outline B
# (0.20 x 0.40) 2.6 m away; the leader runs from the text to 300 mm short of B.
OUT = {"A": (350, -100, 550, 400), "B": (2600, -1300, 2800, -900)}


def test_leader_beats_nearest():
    a = T.associate({"handle": "T", "at": [0, 0], "leader_far": [2300, -1100]}, OUT, 600)
    assert a["outline"] == "B" and a["basis"] == "LEADER" and a["gap_mm"] == 300
    assert T.nearest([0, 0], OUT)[0] == "A"  # nearest to the text is A: a wrong association


@pytest.mark.parametrize("sx,sy", [(-1, 1), (1, -1), (-1, -1)])
def test_leader_mirror_invariant(sx, sy):
    def m(b):
        xs, ys = sorted((sx * b[0], sx * b[2])), sorted((sy * b[1], sy * b[3]))
        return (xs[0], ys[0], xs[1], ys[1])
    a = T.associate({"handle": "T", "at": [0, 0], "leader_far": [sx * 2300, sy * -1100]},
                    {k: m(v) for k, v in OUT.items()}, 600)
    assert a["outline"] == "B"


def test_leader_rotation_90():
    rot = {k: (-b[3], b[0], -b[1], b[2]) for k, b in OUT.items()}  # (x, y) -> (-y, x)
    a = T.associate({"handle": "T", "at": [0, 0], "leader_far": [1100, 2300]}, rot, 600)
    assert a["outline"] == "B"


def test_no_leader_two_outlines_within_tol_unresolved():
    near = {"A": (350, -100, 550, 400), "C": (-500, -100, -300, 400)}
    a = T.associate({"handle": "T", "at": [0, 0], "leader_far": None}, near, 600)
    assert a["status"] == "UNRESOLVED" and a["outline"] is None


def test_leader_into_nothing_unresolved():
    a = T.associate({"handle": "T", "at": [0, 0], "leader_far": [9000, 9000]}, OUT, 600)
    assert a["status"] == "UNRESOLVED"


# ------------------------------------------------------------------------------------------------ R-T694-4
def test_cause_register_gap_and_spurious():
    rows = [{"line_id": "C2", "member_ref": "RS 12", "causes": [{"item": "D-9", "kind": "SECTION"}],
             "readings": ["0.08", "0.10"]},
            {"line_id": "C3", "member_ref": "RS 13", "causes": [{"item": "D-9", "kind": "SECTION"}],
             "readings": ["0.125", "0.125"]},
            {"line_id": "C5", "member_ref": "RS 15", "causes": [{"item": None, "kind": "SECTION"}],
             "readings": ["0.08", "0.10"]},
            {"line_id": "C6", "member_ref": "RS 11", "causes": [{"item": "D-9", "kind": "SECTION"}],
             "readings": ["0.08", "0.10"]}]
    sp, gaps = T.check_causes(rows, {"D-9": {"RS 11"}})
    assert [x["line_id"] for x in sp] == ["C3"]
    assert [(g["line_id"], g["item"]) for g in gaps] == [("C2", "D-9"), ("C5", None)]


# ------------------------------------------------------------------------------------------------ development villa
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
sys.path.insert(0, str(ROOT / "research" / "agents_t683"))


@pytest.fixture(scope="module")
def st():
    import t694_alsenan as Z
    return Z.build()


def test_dev_outputs_reproduce(st):
    import t679_alsenan as A
    import t694_alsenan as Z
    assert (Z.OUT_JSON.read_text(encoding="utf-8") == A.dumps(st)
            and Z.OUT_MD.read_text(encoding="utf-8") == Z.md(st))


def test_dev_totals_equal_index_to_the_digit(st):
    idx = json.loads((ROOT / "research/agents_t672/out/LINE_INDEX_V3_0_68.json").read_text(encoding="utf-8"))
    lines = [x for x in idx["lines"] if x["item_code"].startswith("STR.CONC")]
    rel = sum(X(repr(x["measured_net"])) for x in lines if x["class"] == "RELEASED")
    lo = sum(X(repr(x["held_low"])) for x in lines if x["class"] == "HELD" and x["held_low"] is not None)
    hi = sum(X(repr(x["held_high"])) for x in lines if x["class"] == "HELD" and x["held_high"] is not None)
    t = st["trade_total"]
    assert X(t["released"]["m3"]) == rel == X("291.476251")
    assert (X(t["held_bounded"]["low"]), X(t["held_bounded"]["high"])) == (lo, hi) == (X("43.044431"), X("67.603665"))
    assert sum(st["partition"].values()) == len(lines) == 597
    assert st["candidate"]["master_census_agrees"] == 14


def test_dev_no_measurable_now_left_and_restated_11(st):
    t = st["trade_total"]
    assert t["held_bounded"]["by_cause"]["MEASURABLE NOW"] == 0 and t["held_blank"]["by_cause"]["MEASURABLE NOW"] == 0
    assert len(st["stale_classes_restated"]) == 11


def test_dev_before_after_and_proposed(st):
    r = st["before_after_v3_0_66"]["reconcile"]
    assert (r["delta_low"], r["delta_high"]) == ("1.030150", "1.410474")
    p = st["after_t693_proposed"]["trade_total"]
    assert (p["held_bounded"]["low"], p["held_bounded"]["high"]) == ("44.452911", "69.834915")
    assert p["held_blank"]["lines"] == 75 and p["released"] == st["trade_total"]["released"]


def test_dev_pc2f_and_register(st):
    assert [a["outline"] for a in st["pc_2f"]["association"]] == ["329", "386", "77B"]
    assert [a["nearest_to_text"][0] for a in st["pc_2f"]["association"]] == ["359", "371", "67C"]
    assert [g["line_id"][:10] for g in st["cause_register"]["spurious"]] == ["L-fad18af6"]
    assert len(st["cause_register"]["gaps"]) == 6
