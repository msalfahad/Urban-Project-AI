"""T-543: B9 blockwork reconciliation against a multi-section freelancer total (research/agents_t543, R-T543-1).
Synthetic villa "B543" (not the training villa), hand calculations; adverse cases; then the development villa from
merged repository files only (no private input needed)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t543"))
import t543_alsenan as A  # noqa: E402
import t543_inputs as I  # noqa: E402
import t543_reconcile as R  # noqa: E402

# ---- villa "B543" (hand), one floor, two walls, one opening ------------------------------------------------------
# W1 external t 0.20: length 5.00, clear height under its beam 3.60 -> gross 18.00; door 1.00 x 2.20 = 2.20 -> net
#    15.80 m2, VALUED.
# W2 internal t 0.15: length 4.00 x 3.50 = 14.00 gross, no opening; HELD (no member drawn above).
# Freelancer: one flat height 4.00; W1 taken 5.20 m (he owns the corner square), W2 4.00 m: gross 20.80 + 16.00 =
# 36.80, his door 1.00 x 2.40 = 2.40 -> net 34.40; plus one parapet row 3.00 m2 in his masonry section; total 37.40.
# Hand gap 37.40 - 15.80 = 21.60 = parapet 3.00 (RULE_DIFFERENCE) + walls 18.60, and 18.60 =
#   HELD W2 14.00 + drift 0 + held length 0 + height (9.00 x (4.00 - 32.00 / 9.00)) = 4.00
#   + openings -(2.40 - 2.20) = -0.20 + residual (9.20 - 9.00) x 4.00 = 0.80.
S = "B543 A-101 plan / S-201 beams"
W1 = {"wall_id": "W1", "floor": "GF", "t_m": "0.2", "group": "EXTERNAL", "valued_m2": "15.80",
      "state_v3_0_58": "VERIFIED", "length_m": "5.00", "held_length_m": "0", "gross_v2_m2": "18.00",
      "deductions_v2_m2": "2.20", "held_cause_v2": "", "held_items_v4": ""}
W2 = {"wall_id": "W2", "floor": "GF", "t_m": "0.15", "group": "INTERNAL", "valued_m2": None, "state_v3_0_58": "HELD",
      "length_m": "4.00", "held_length_m": "0", "gross_v2_m2": "14.00", "deductions_v2_m2": "0",
      "held_cause_v2": "no member drawn above", "held_items_v4": ""}
HIS = {"length_m": "9.20", "gross_m2": "36.80", "openings_m2": "2.40"}
LINES = [{"line_id": "L1", "qty": "15.80", "unit": "m2"}]


def comps(dec):
    return [{"name": "GF walls", "engine_valued_m2": "15.80", "engine_status": "PARTIAL", "his_m2": dec["his_net_m2"],
             "cause": "SPLIT", "decomposition": dec, "source": S},
            {"name": "parapet row", "engine_valued_m2": None, "engine_status": "STR.CONC.PARAPET record",
             "his_m2": "3.00", "cause": "RULE_DIFFERENCE", "source": S}]


def rowmap(dec):
    return {r["name"].split(":")[0]: Decimal(r["delta"]) for r in dec["rows"]}


def test_hand_net_vs_gross_and_decomposition():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    assert Decimal(dec["his_net_m2"]) == Decimal("34.40")            # gross 36.80 - 2.40
    assert Decimal(dec["engine_valued_m2"]) == Decimal("15.80")      # gross 18.00 - 2.20
    assert Decimal(dec["gap"]) == Decimal("18.60")
    rows = {r["name"]: (Decimal(r["delta"]), r["cause"]) for r in dec["rows"]}
    assert rows["HELD walls: no member drawn above / no band"] == (Decimal("14.00"), "HELD")
    height = [v for k, v in rows.items() if k.startswith("height convention")][0]
    assert height == (Decimal("4.000000"), "RULE_DIFFERENCE")
    opening = [v for k, v in rows.items() if k.startswith("openings census")][0]
    assert opening == (Decimal("-0.20"), "UNRESOLVED")
    resid = [v for k, v in rows.items() if k.startswith("RESIDUAL")][0]
    assert resid == (Decimal("0.800000"), "UNRESOLVED")
    assert sum(v for v, _ in rows.values()) == Decimal("18.60")


def test_hand_partition_closes_exactly():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    res = R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=comps(dec))
    assert Decimal(res["gap"]) == Decimal("21.60")
    assert sum(Decimal(r["difference_m2"]) for r in res["rows"]) == Decimal("21.60")
    assert Decimal(res["by_cause"]["HELD"]) == Decimal("14.00")
    assert Decimal(res["by_cause"]["RULE_DIFFERENCE"]) == Decimal("7.000000")   # parapet 3.00 + height 4.00


def test_mirror_and_order_invariant():
    a = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    b = R.floor_decomposition(floor="GF", his=HIS, walls=[W2, W1])
    assert rowmap(a) == rowmap(b)


# ---- adverse ------------------------------------------------------------------------------------------------------
def test_adverse_held_wall_counted_as_zero_refused():
    w2 = dict(W2, valued_m2="0")
    with pytest.raises(R.ReconcileError, match="HELD wall with a valued figure"):
        R.floor_decomposition(floor="GF", his=HIS, walls=[W1, w2])


def test_adverse_held_component_as_engine_zero_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    c = comps(dec)
    c.append({"name": "annex walls", "engine_valued_m2": "0", "engine_status": "HELD", "his_m2": "0",
              "cause": "HELD", "source": S})
    with pytest.raises(R.ReconcileError, match="HELD is never 0"):
        R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=c)


def test_adverse_held_component_classed_agreement_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    c = comps(dec)
    c[1] = dict(c[1], engine_status="HELD (material)", cause="ENGINE_RIGHT")
    with pytest.raises(R.ReconcileError, match="can only be classed HELD"):
        R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=c)


def test_adverse_none_as_number_refused():
    with pytest.raises(R.ReconcileError, match="never 0"):
        R.D(None)


def test_adverse_partition_not_his_total_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    with pytest.raises(R.ReconcileError, match="his components sum"):
        R.partition(freelancer_total="40.00", engine_valued_lines=LINES, components=comps(dec))


def test_adverse_stale_engine_total_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    lines = LINES + [{"line_id": "L2", "qty": "1.00", "unit": "m2"}]
    with pytest.raises(R.ReconcileError, match="stale or double"):
        R.partition(freelancer_total="37.40", engine_valued_lines=lines, components=comps(dec))


def test_adverse_held_line_as_valued_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    lines = LINES + [{"line_id": "L2", "qty": None, "unit": "m2"}]
    with pytest.raises(R.ReconcileError, match="not a valued line"):
        R.partition(freelancer_total="37.40", engine_valued_lines=lines, components=comps(dec))


def test_adverse_lm_and_mm_refused():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    c = comps(dec)
    c[1] = dict(c[1], unit="lm")
    with pytest.raises(R.ReconcileError, match="m2 only"):
        R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=c)
    with pytest.raises(R.ReconcileError, match="m2 only"):
        R.partition(freelancer_total="37.40", engine_valued_lines=[dict(LINES[0], unit="mm2")],
                    components=comps(dec))


def test_adverse_tampered_decomposition_refused():
    dec = copy.deepcopy(R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2]))
    dec["rows"][0]["delta"] = str(Decimal(dec["rows"][0]["delta"]) + 1)
    with pytest.raises(R.ReconcileError, match="decomposition sums"):
        R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=comps(dec))


def test_adverse_wall_on_wrong_floor_and_unallocated_deduction():
    with pytest.raises(R.ReconcileError, match="is not on"):
        R.floor_decomposition(floor="1F", his=HIS, walls=[W1])
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    c = comps(dec) + [{"name": "his openings", "engine_valued_m2": None, "engine_status": "", "his_m2": "-1.00",
                       "cause": "UNRESOLVED", "source": S}]
    with pytest.raises(R.ReconcileError, match="negative part"):
        R.partition(freelancer_total="36.40", engine_valued_lines=LINES, components=c)
    c[-1]["his_deduction"] = True
    res = R.partition(freelancer_total="36.40", engine_valued_lines=LINES, components=c)
    assert Decimal(res["gap"]) == Decimal("20.60")


def test_adverse_engine_only_held_scope_never_summed():
    dec = R.floor_decomposition(floor="GF", his=HIS, walls=[W1, W2])
    with pytest.raises(R.ReconcileError, match="engine-only HELD"):
        R.partition(freelancer_total="37.40", engine_valued_lines=LINES, components=comps(dec),
                    engine_only_held=[{"name": "below-ground", "engine_valued_m2": "0"}])


# ---- development villa (merged files only) -----------------------------------------------------------------------
def test_freelancer_partition_exact():
    assert I.freelancer_check()["total"] == "1260.6895"


def test_alsenan_table_closes_and_matches_the_stored_output():
    res = A.build()
    assert res["engine_valued_total"] == "467.7925"
    assert Decimal(res["gap"]) == Decimal("792.8970")
    assert sum(Decimal(r["difference_m2"]) for r in res["rows"]) == Decimal("792.8970")
    assert sum(Decimal(v) for v in res["by_cause"].values()) == Decimal("792.8970")
    assert "ENGINE_WRONG" not in res["by_cause"]
    stored = json.loads((ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(res, sort_keys=True)) == stored


def test_alsenan_held_rows_carry_no_valued_figure():
    res = A.build()
    two_f = [r for r in res["rows"] if r["name"].startswith("2F")][0]
    assert two_f["engine_valued_m2"] is None and two_f["engine_status"].startswith("HELD")
    for r in res["rows"]:
        if r["decomposition"]:
            for x in r["decomposition"]["rows"]:
                assert x["cause"] in R.CAUSES
    assert {h["name"] for h in res["engine_only_held_beside"]} == {"HOUSE_BELOW_NG:MAIN_S", "HOUSE_BELOW_NG:ANNEX_S"}
