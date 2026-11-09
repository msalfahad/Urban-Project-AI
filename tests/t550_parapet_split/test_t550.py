"""T-550: parapet rows of a freelancer masonry total split to physical causes (research/agents_t550, R-T550-1).
Synthetic villa "B550" (not the training villa), hand calculations; adverse cases; then the development villa from
merged repository files only (no private input needed)."""
from __future__ import annotations

import copy
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t550"))
import t550_parapet_split as P  # noqa: E402

# ---- villa "B550" (hand): one roof, slab with an RC upstand --------------------------------------------------------
# Finished roof level F. Structural slab top F - 0.10 (build-up 0.10); RC upstand 0.30 above the slab top (0.20 of it
# above F); edge member 0.40 deep below the slab top (bottom F - 0.50). Printed parapet heights ABOVE F:
#   R1 10.00 m at 0.60 (PRINTED); R2 2.00 m at 0.40 (PRINTED, a low run); R3 1.00 m HELD range 0.50 .. 0.70.
# Both datums by hand for R1: above finish 0.60, above the slab top 0.60 + 0.10 = 0.70, from the edge-member bottom
# 0.60 + 0.10 + 0.40 = 1.10.
# Engine face above finish (upper ends): 10 x 0.60 + 2 x 0.40 + 1 x 0.70 = 7.50 m2; centreline 13.00 m.
# Freelancer: one row 13.50 m x 1.10 (= printed 0.60 + 0.50 below the finish) = 14.85 m2. Hand split of 7.35:
#   length (13.50 - 13.00) x 1.10 = 0.55 | below finish 13.00 x 0.50 = 6.50 (concrete) | R2 2 x (0.60 - 0.40) = 0.40
#   (PRINTED, ENGINE_RIGHT) + R1 0 | R3 1 x (0.60 - 0.70) = -0.10 (HELD)  -> 0.55 + 6.50 + 0.40 - 0.10 = 7.35.
EVID = "B550 S-301 P1: RC upstand above the slab top; A-301 cut hatches the edge member to F - 0.50"
RUNS = [
    {"run": "R1", "centreline_m": "10.00", "h_m": "0.60", "h_datum": "FINISH", "h_status": "PRINTED"},
    {"run": "R2", "centreline_m": "2.00", "h_m": "0.40", "h_datum": "FINISH", "h_status": "PRINTED"},
    {"run": "R3", "centreline_m": "1.00", "h_m": "0.70", "h_datum": "FINISH", "h_status": "HELD"},
]


def split(runs=None, **kw):
    a = dict(chain="B550", his_length_m="13.50", his_height_m="1.10", printed_nominal_h_m="0.60",
             runs=copy.deepcopy(RUNS if runs is None else runs), below_finish_evidence=EVID)
    a.update(kw)
    return P.split_chain(**a)


def test_hand_split_closes_exactly():
    s = split()
    assert Decimal(s["his_m2"]) == Decimal("14.85")
    assert Decimal(s["engine_face_m2"]) == Decimal("7.50")
    assert Decimal(s["difference_m2"]) == Decimal("7.35")
    assert Decimal(s["delta_m"]) == Decimal("0.50")
    d = {(r["cause"], r["name"].split(":")[1][:7]): Decimal(r["delta"]) for r in s["rows"]}
    vals = sorted((r["cause"], Decimal(r["delta"])) for r in s["rows"])
    assert vals == sorted([("UNRESOLVED", Decimal("0.55")), ("ENGINE_RIGHT", Decimal("6.50")),
                           ("ENGINE_RIGHT", Decimal("0.40")), ("HELD", Decimal("-0.10"))])
    assert sum(d.values()) == Decimal("7.35")
    bc = {k: Decimal(v) for k, v in P.by_cause(s["rows"]).items()}
    assert bc == {"ENGINE_RIGHT": Decimal("6.90"), "HELD": Decimal("-0.10"), "UNRESOLVED": Decimal("0.55")}


def test_both_datums_by_hand_r1_only():
    # R1 alone, his 10.00 m measured from the edge-member bottom (1.10): only the below-finish zone remains
    s = split(runs=[RUNS[0]], his_length_m="10.00")
    assert Decimal(s["difference_m2"]) == Decimal("11.00") - Decimal("6.00")
    below = [r for r in s["rows"] if "below the finished roof" in r["name"]][0]
    assert Decimal(below["delta"]) == Decimal("5.00") and below["cause"] == "ENGINE_RIGHT"


def test_adverse_height_from_slab_top_used_as_above_finish_refused():
    bad = copy.deepcopy(RUNS)
    bad[0]["h_m"], bad[0]["h_datum"] = "0.70", "SLAB_TOP"
    with pytest.raises(P.SplitError, match="not a height above finish"):
        split(runs=bad)


def test_adverse_held_run_counted_as_agreement_refused():
    bad = copy.deepcopy(RUNS)
    bad[2]["class"] = "ENGINE_RIGHT"
    with pytest.raises(P.SplitError, match="HELD run height can only be classed HELD"):
        split(runs=bad)
    bad[2]["class"] = "TOLERANCE"
    with pytest.raises(P.SplitError, match="HELD"):
        split(runs=bad)


def test_adverse_no_material_evidence_keeps_zone_held():
    s = split(below_finish_evidence=None)
    below = [r for r in s["rows"] if "below the finished roof" in r["name"]][0]
    assert below["cause"] == "HELD"


def test_adverse_negative_delta_none_mm_and_unbased_length_refused():
    with pytest.raises(P.SplitError, match="below the printed height"):
        split(his_height_m="0.55")
    with pytest.raises(P.SplitError, match="never 0"):
        split(his_length_m=None)
    with pytest.raises(P.SplitError, match="mm"):
        split(his_height_m="1100", printed_nominal_h_m="600")
    with pytest.raises(P.SplitError, match="drawing basis"):
        split(length_cause="ENGINE_RIGHT")
    bad = copy.deepcopy(RUNS)
    bad[0]["unit"] = "mm"
    with pytest.raises(P.SplitError, match="metres"):
        split(runs=bad)


def test_mirror_and_order_invariance():
    a = split()
    b = split(runs=list(reversed(RUNS)))
    assert a["difference_m2"] == b["difference_m2"] and P.by_cause(a["rows"]) == P.by_cause(b["rows"])


# ---- development villa: merged repository files only --------------------------------------------------------------
def test_development_villa_restatement():
    import t550_alsenan as X
    res = X.build()
    assert Decimal(res["parapet_residual_t543"]) == Decimal("71.46577750")
    assert Decimal(res["t543_unresolved"]) == Decimal("101.43193450")
    assert Decimal(res["restated_by_cause"]["UNRESOLVED"]) == Decimal("25.92243700")
    assert sum(Decimal(v) for v in res["restated_by_cause"].values()) == Decimal(res["gap"]) == Decimal("792.8970")
    assert all(Decimal(s["delta_m"]) == Decimal("0.50") for s in res["parapet_split"])
    below = sum(Decimal(r["delta"]) for s in res["parapet_split"] for r in s["rows"]
                if "below the finished roof" in r["name"])
    assert below == Decimal("68.41880")
    assert res["H1"].startswith("MEASURED")
    held = [r for s in res["parapet_split"] for r in s["rows"] if r["cause"] == "HELD"]
    assert len(held) == 1 and Decimal(held[0]["delta"]) == Decimal("-1.289983")  # SW-2 -1.290015 + NE-1 / SW-1 2 x 0.000016
