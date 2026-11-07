"""T-607 R-T607-1 on a non-Alsenan hand fixture (Villa K607) with normal and adverse cases.

Villa K607 (invented, hand-calculated, mm): a stair shaft 2.400 x 4.000 drawn on two storey plans; plan B is plan A
moved by (30000, 500). Flight F1 (plan A, west lane x 100 .. 1100): 5 tread fronts at y 300 .. 1500 (going 300) and the
landing edge at y 1800. Flight F2 (plan B, east lane x 1300 .. 2300): 5 tread fronts at y 1800 .. 600 and the floor
edge at y 300. Governing count 12 risers (levels 0.00 / 0.90 / 1.80, riser 150). Plan A ALSO draws one F2 front (y 600)
dashed above its cut: a second reading. The reference counts 13 pieces: one extra piece.
Hand: extra = 13 - 12 = 1; it coincides with F2-N05 (no new edge) -> ENGINE_RIGHT; storey estimate: ceil(0.90 / r)
twice is even, so no riser reproduces 13; his lm basis 1 x 1.20 = 1.20, counted once in a total over two lines.
"""
from __future__ import annotations

import importlib
import math
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t607"))
R = importlib.import_module("t607_rules")

SHIFT = (30000.0, 500.0)
WALLS = [((0, 0), (2400, 0)), ((2400, 0), (2400, 4000)), ((2400, 4000), (0, 4000)), ((0, 4000), (0, 0)),
         ((1200, 0), (1200, 2800)), ((2400, 1000), (2600, 1000)), ((0, 3000), (-200, 3000)), ((1200, 2800), (900, 2800))]


def xf(p, ang=0.0, mirror=False, scale=1.0):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return ((x * c - y * s) * scale, (x * s + y * c) * scale)


def fixture(ang=0.0, mirror=False, extra_real=False, scale=1.0):
    def on_b(p):
        return (p[0] + SHIFT[0], p[1] + SHIFT[1])
    A, B = {}, {}
    for i, y in enumerate((300, 600, 900, 1200, 1500, 1800), 1):
        A[f"F1-{i}"] = ((100, y), (1100, y))
    for i, y in enumerate((1800, 1500, 1200, 900, 600, 300), 1):
        B[f"F2-{i}"] = (on_b((1300, y)), on_b((2300, y)))
    A["A-X1"] = ((1300, 600), (2300, 600))                 # F2's 5th front seen above plan A's cut
    if extra_real:
        A["A-X2"] = ((100, 2100), (1100, 2100))            # a drawn front beyond the census (a possible piece)
    t = lambda p: xf(p, ang, mirror, scale)                # noqa: E731
    lines = {"A": {h: R.seg(t(p), t(q)) for h, (p, q) in A.items()},
             "B": {h: R.seg(t(p), t(q)) for h, (p, q) in B.items()}}
    wa = [t(p) for s in WALLS for p in s]
    wb = [t(on_b(p)) for s in WALLS for p in s]
    census = {f"F1-{i}": (f"K607-F1-N0{i}", "A") for i in range(1, 7)}
    census.update({f"F2-{i}": (f"K607-F2-N0{i}", "B") for i in range(1, 7)})
    return lines, wa, wb, census


def shifts(wa, wb):
    dx, dy, *_ = R.register(wa, wb)
    return {("A", "B"): (dx, dy), ("B", "A"): (-dx, -dy)}


def edges():
    e = {f"K607-F1-N0{i}": {"kind": "TREAD", "value": Decimal("1.000")} for i in range(1, 6)}
    e["K607-F1-N06"] = {"kind": "LANDING_EDGE", "value": Decimal("1.000")}
    e.update({f"K607-F2-N0{i}": {"kind": "TREAD", "value": Decimal("1.000")} for i in range(1, 6)})
    e["K607-F2-N06"] = {"kind": "FLOOR_EDGE", "value": Decimal("1.000")}
    return e


STEPS = {"STEP-F1": [f"K607-F1-N0{i}" for i in range(1, 6)], "STEP-F2": [f"K607-F2-N0{i}" for i in range(1, 6)]}
NOSE = {"NOSE-F1": ["K607-F1-N06"], "NOSE-F2": ["K607-F2-N06"]}


# ------------------------------------------------------------------ normal
@pytest.mark.parametrize("ang,mirror", [(0, False), (37, False), (90, False), (211, False), (0, True), (37, True)])
def test_registration_and_second_reading_any_rotation_or_mirror(ang, mirror):
    lines, wa, wb, cen = fixture(ang, mirror)
    sh = shifts(wa, wb)
    exp = xf(SHIFT, ang, mirror)                            # the shift moves with the drawing
    assert sh[("A", "B")][0] == pytest.approx(exp[0], abs=1.0) and sh[("A", "B")][1] == pytest.approx(exp[1], abs=1.0)
    c = R.classify(lines, cen, sh)
    assert c["A"]["A-X1"] == ("SECOND_READING", "K607-F2-N05")
    assert Counter(v[0] for p in c.values() for v in p.values()) == Counter({"CENSUS": 12, "SECOND_READING": 1})


def test_edge_table_one_line_per_edge():
    t = R.claims(edges(), STEPS, NOSE, {"STEP-F2-seen-on-A": []})
    assert len(t) == 12 and Counter(v["family"] for v in t.values()) == Counter({"STEP": 10, "NOSING": 2})
    assert t["K607-F1-N06"]["line"] == "NOSE-F1" and t["K607-F2-N03"]["line"] == "STEP-F2"


def test_extra_piece_settled_engine_right():
    lines, wa, wb, cen = fixture()
    c = R.classify(lines, cen, shifts(wa, wb))
    cls = Counter(v[0] for p in c.values() for v in p.values())
    rep = R.reproductions(13 - 12, {"plan A dashed F2 fronts": [(1, "SECOND_READING")]})
    assert len(rep) == 1 and rep[0]["admissible"] and not rep[0]["physical"]
    assert R.storey_estimate([("A->B", "0.00", "0.90"), ("B->C", "0.90", "1.80")], 13) == []
    extra, verdict, _ = R.extra_verdict(13, 12, cls, rep)
    assert (extra, verdict) == (1, "ENGINE_RIGHT")


def test_storey_estimate_hand():
    # 0.70 / 0.150 = 4.67 -> 5; 4.50 / 0.150 = 30; 4.20 / 0.150 = 28; at 0.1555: 5 + 29 + 28 = 62
    hits = R.storey_estimate([("a", "0.30", "1.00"), ("b", "1.00", "5.50"), ("c", "5.50", "9.70")], 63)
    assert [(str(h["lo_mm"]), str(h["hi_mm"])) for h in hits] == [("150.0", "155.0")]
    assert hits[0]["per_storey"] == [("a", 5), ("b", 30), ("c", 28)]


def test_shared_cause_counted_once():
    s = R.shared_cause("C-K607", "REF.B1", {"steps lm": "lm", "steps nr": "nr", "nosing lm": "lm"}, 1, "1.20")
    assert s["per_line"]["steps lm"] == (Decimal("1.20"), "lm") and s["per_line"]["steps nr"] == (1, "nr")
    assert R.total_across_lines([("C-K607", 1, "1.20"), ("C-K607", 1, "1.20")]) == (1, Decimal("1.20"))
    with pytest.raises(R.RuleError):
        R.summed_per_line([("C-K607", 1, "1.20"), ("C-K607", 1, "1.20")])


# ------------------------------------------------------------------ adverse
def test_winder_front_valued_refused():
    e = edges()
    e["K607-F1-N05"] = {"kind": "WINDER", "held": True, "value": Decimal("1.258")}
    with pytest.raises(R.RuleError, match="winder front"):
        R.claims(e, STEPS, NOSE)


def test_one_edge_claimed_by_two_step_rows_refused():
    steps = dict(STEPS, **{"STEP-F2-again": ["K607-F2-N03"]})
    with pytest.raises(R.RuleError, match="one edge, one pricing line"):
        R.claims(edges(), steps, NOSE)


def test_edge_in_step_and_nosing_or_wrong_family_refused():
    with pytest.raises(R.RuleError):
        R.claims(edges(), STEPS, dict(NOSE, **{"NOSE-X": ["K607-F1-N02"]}))     # tread edge also a nosing
    with pytest.raises(R.RuleError, match="arrival edge"):
        R.claims(edges(), {"STEP-F1": STEPS["STEP-F1"] + ["K607-F1-N06"], "STEP-F2": STEPS["STEP-F2"]}, {"NOSE-F2":
                 ["K607-F2-N06"]})


def test_orphan_and_second_reading_claim_refused():
    with pytest.raises(R.RuleError, match="no pricing line"):
        R.claims(edges(), STEPS, {"NOSE-F1": ["K607-F1-N06"]})
    with pytest.raises(R.RuleError, match="second reading"):
        R.claims(edges(), STEPS, NOSE, {"STEP-F2-seen-on-A": ["K607-F2-N05"]})


def test_unmatched_drawn_front_keeps_extra_unresolved():
    lines, wa, wb, cen = fixture(extra_real=True)
    c = R.classify(lines, cen, shifts(wa, wb))
    cls = Counter(v[0] for p in c.values() for v in p.values())
    assert c["A"]["A-X2"] == ("UNMATCHED", None)
    rep = R.reproductions(1, {"plan A dashed": [(1, "SECOND_READING")]})
    assert R.extra_verdict(13, 12, cls, rep)[1] == "UNRESOLVED"


def test_physical_or_rejected_reproduction_never_engine_right():
    cls = Counter({"CENSUS": 12, "SECOND_READING": 1})
    rep = R.reproductions(1, {"open item": [(1, "PHYSICAL_OPEN")]})
    assert R.extra_verdict(13, 12, cls, rep)[1] == "UNRESOLVED"
    rej = R.reproductions(1, {"rejected count": [(1, "REJECTED_READING")]})
    assert rej and not rej[0]["admissible"] and R.extra_verdict(13, 12, cls, rej)[1] == "UNRESOLVED"
    assert R.extra_verdict(13, 12, cls, [])[1] == "UNRESOLVED"


def test_metres_read_as_millimetres_never_match():
    lines, wa, wb, cen = fixture()
    lines["A"]["A-X1"] = R.seg((1.3, 0.6), (2.3, 0.6))          # one line in metres among mm
    c = R.classify(lines, cen, shifts(wa, wb))
    assert c["A"]["A-X1"] == ("UNMATCHED", None)


def test_units_counts_and_options_refused():
    with pytest.raises(R.RuleError):
        R.shared_cause("C", "REF", {"x": "m2"}, 1, "1.2")         # nr and lm only
    with pytest.raises(R.RuleError):
        R.shared_cause("C", "REF", {"x": "lm"}, 1.5, "1.2")        # a fractional piece
    with pytest.raises(R.RuleError):
        R.total_across_lines([("C", 1, "1.20"), ("C", 2, "2.40")])  # same id, two amounts
    with pytest.raises(R.RuleError):
        R.reproductions(1, {"g": [(1.0, "SECOND_READING")]})
    with pytest.raises(R.RuleError):
        R.reproductions(1, {"g": [(0, "SECOND_READING")]})
    with pytest.raises(R.RuleError):
        R.extra_verdict(12, 12, Counter(), [])                      # no extra: nothing to settle
    with pytest.raises(R.RuleError):
        R.D(None)


def test_registration_ambiguous_refused():
    lattice = [(x * 1000.0, y * 1000.0) for x in range(4) for y in range(4)]
    with pytest.raises(R.RuleError, match="not unique"):
        R.register(lattice, [(x + 5000, y) for x, y in lattice])
