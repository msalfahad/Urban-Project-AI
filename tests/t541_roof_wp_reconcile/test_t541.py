"""T-541: roof waterproofing reconciliation against a single freelancer row (research/agents_t541, R-T541-1).
Synthetic villa "R541" (not the training villa), hand calculations; adverse cases; then the development villa (the
drawing check is skipped when the private DXF is absent)."""
from __future__ import annotations

import math
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t541"))
import t541_inputs as I  # noqa: E402
import t541_reconcile as R  # noqa: E402

# ---- villa "R541" (hand): roof A 10.00 x 6.00 inside the parapet = 60.000 m2, perimeter 32.000 lm; roof B 8.00 x 5.00
# = 40.000 m2, perimeter 26.000 lm, with one skylight dome r 1.00 (pi = 3.141593 m2, ring 2 pi = 6.283185 lm) that the
# engine leaves open (membrane stops, 0.20 m ring); roof C 4.00 x 4.00 = 16.000 m2 (perimeter 16.000) HELD (no outline).
# Engine: 60 + 40 - 3.141593 = 96.858407 m2; 32 + 26 + 6.283185 = 64.283185 lm.
# Freelancer single row (domes kept, roof C in): 60 + 40 + 16 = 116.00 m2; 32 + 26 + 16 = 74.00 lm.
# Hand gap: 116 - 96.858407 = 19.141593 m2 = 16 (HELD C) + 3.141593 (dome) + 0 residual;
#           74 - 64.283185 = 9.716815 lm = 16 (HELD C) - 6.283185 (ring) + 0 residual.
S = "R541 A-201 roof plan"
EM2 = [{"line_id": "A", "qty": "60.000", "unit": "m2"}, {"line_id": "B", "qty": "36.858407", "unit": "m2"}]
ELM = [{"line_id": "A", "qty": "32.000", "unit": "lm"}, {"line_id": "B", "qty": "32.283185", "unit": "lm"}]


def cm2():
    return [{"name": "roof C held", "qty": "16.000", "unit": "m2", "sign": 1, "cause": "HELD", "source": S},
            {"name": "dome footprint", "qty": "3.141593", "unit": "m2", "sign": 1, "cause": "RULE_DIFFERENCE", "source": S}]


def clm():
    return [{"name": "roof C parapet", "qty": "16.000", "unit": "lm", "sign": 1, "cause": "HELD", "source": S},
            {"name": "dome ring", "qty": "6.283185", "unit": "lm", "sign": -1, "cause": "RULE_DIFFERENCE", "source": S}]


def test_r541_membrane_by_hand():
    t = R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=cm2())
    assert t["engine_total"] == "96.858407" and t["gap"] == "19.141593"
    assert Decimal(t["residual"]) == 0
    assert sum(Decimal(r["delta"]) for r in t["rows"]) == Decimal("19.141593")


def test_r541_upturn_by_hand():
    t = R.reconcile(unit="lm", freelancer_total="74.00", engine_lines=ELM, components=clm())
    assert t["gap"] == "9.716815" and Decimal(t["residual"]) == 0


def test_residual_named_never_absorbed():
    t = R.reconcile(unit="m2", freelancer_total="117.00", engine_lines=EM2, components=cm2())
    last = t["rows"][-1]
    assert last["cause"] == "UNRESOLVED" and Decimal(last["delta"]) == Decimal("1.000000")


def test_order_invariance():
    a = R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=cm2())
    b = R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2[::-1], components=cm2()[::-1])
    assert a["residual"] == b["residual"] and a["gap"] == b["gap"]


# ---- adverse
def test_adverse_upturn_lm_into_m2_without_printed_height_refused():
    bad = cm2() + [{"name": "upturn", "qty": "58.000", "unit": "lm", "sign": 1, "cause": "RULE_DIFFERENCE", "source": S}]
    with pytest.raises(R.ReconcileError, match="printed height"):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=bad)
    bad[-1]["printed_height"] = "0.20"  # a height with no source is still refused
    with pytest.raises(R.ReconcileError, match="printed height"):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=bad)


def test_printed_height_converts_and_shows_the_row():
    comp = cm2() + [{"name": "upturn band", "qty": "10.000", "unit": "lm", "sign": 1, "cause": "RULE_DIFFERENCE",
                     "source": S, "printed_height": "0.20", "height_source": "R541 detail 3"}]
    t = R.reconcile(unit="m2", freelancer_total="118.00", engine_lines=EM2, components=comp)
    assert t["rows"][2]["delta"] == "2.00000" and Decimal(t["residual"]) == 0


def test_adverse_unknown_quantity_never_zero():
    comp = cm2(); comp[0]["qty"] = None
    with pytest.raises(R.ReconcileError, match="never 0"):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=comp)
    eng = [dict(EM2[0]), {"line_id": "C", "qty": None, "unit": "m2"}]
    with pytest.raises(R.ReconcileError, match="never 0"):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=eng, components=cm2())


@pytest.mark.parametrize("field,value,msg", [
    ("unit", "mm2", "metres only"), ("cause", "UNRESOLVED", "residual"), ("cause", "GUESS", "not in"),
    ("source", "", "no source"), ("source", "freelancer workbook", "never a component"), ("sign", 0, "sign"),
    ("qty", "-3", "negative")])
def test_adverse_component_fields(field, value, msg):
    comp = cm2(); comp[1][field] = value
    with pytest.raises(R.ReconcileError, match=msg):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=EM2, components=comp)


def test_adverse_units():
    with pytest.raises(R.ReconcileError, match="m2 / lm"):
        R.reconcile(unit="mm", freelancer_total="1", engine_lines=[], components=[])
    with pytest.raises(R.ReconcileError, match="differs"):
        R.reconcile(unit="m2", freelancer_total="116.00", engine_lines=ELM, components=cm2())


# ---- development villa
def test_dev_villa_membrane_closes_exactly():
    t = R.reconcile(unit="m2", freelancer_total=I.FREELANCER_MEMBRANE_M2, engine_lines=I.ENGINE_M2,
                    components=I.membrane_components())
    assert t["engine_total"] == "209.658440" and t["gap"] == "75.341560"
    assert t["residual"] == "0.523000"
    assert sum(Decimal(r["delta"]) for r in t["rows"]) == Decimal("75.341560")
    assert Decimal(I.TOP_ROOF_INNER_M2) - Decimal(I.THIRD_DOME_M2) == Decimal(I.membrane_components()[0]["qty"])
    # the engine's own dome deduction = circles - discretisation
    assert Decimal(I.DOMES_970_CIRCLE_M2) - Decimal("0.018026") == Decimal(I.ENGINE_DOME_DEDUCTION_M2)


def test_dev_villa_upturn_closes_exactly():
    t = R.reconcile(unit="lm", freelancer_total=I.FREELANCER_UPTURN_LM, engine_lines=I.ENGINE_LM,
                    components=I.upturn_components())
    assert t["engine_total"] == "187.834160" and t["gap"] == "6.165840"
    assert t["residual"] == "11.893000"
    assert Decimal(I.DOMES_970_CIRCLE_LM) - Decimal("0.003396") == Decimal(I.ENGINE_DOME_RINGS_LM)


def test_dev_villa_circle_values_by_hand():
    assert f"{math.pi * 2.205018498 ** 2:.6f}" == I.THIRD_DOME_M2
    assert f"{2 * math.pi * 2.205018498:.6f}" == I.THIRD_DOME_RING_LM
    assert f"{2 * math.pi * 2.211091524 ** 2:.6f}" == I.DOMES_970_CIRCLE_M2
    assert f"{4 * math.pi * 2.211091524:.6f}" == I.DOMES_970_CIRCLE_LM
    assert f"{7.70 * 6.45:.6f}" == I.TOP_ROOF_INNER_M2


DXF = Path(os.environ.get("T541_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_dev_villa_drawing_handles():
    ezdxf = pytest.importorskip("ezdxf")
    db = ezdxf.readfile(str(DXF)).entitydb
    xs = [p.x for h in ("12B7", "1292", "1279", "1283") for p in (db[h].dxf.start, db[h].dxf.end)]
    ys = [p.y for h in ("12B7", "1292", "1279", "1283") for p in (db[h].dxf.start, db[h].dxf.end)]
    w, d = (max(xs) - min(xs)) / 1000, (max(ys) - min(ys)) / 1000
    assert (round(w, 6), round(d, 6)) == (7.7, 6.45)
    assert round(db["1300"].dxf.radius / 1000, 9) == 2.205018498
    assert round(db["12EB"].dxf.radius / 1000, 9) == round(db["2F33"].dxf.radius / 1000, 9) == 2.211091524
