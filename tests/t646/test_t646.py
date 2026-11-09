"""T-646: roof layers + fence finishes hold census (R-T646-1). Synthetic villa "R646" (not the training villa): one roof
10.00 x 8.00 m whose section prints a 50 mm screed and no insulation, one fence 30.00 x 2.50 m with no finish printed,
by hand, with adverse cases (unprinted screed thickness used, mm as m, membrane as a roof layer, house Sigma carried to a
site wall, bound inventing screed, held as 0, order); then the development villa: the 43 HELD-blank B13 lines of the
T-630 dry run classed (repository files only)."""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t646"))
import t646_rules as R  # noqa: E402
import t646_alsenan as A  # noqa: E402

D = Decimal

# ---- villa "R646" (hand) --------------------------------------------------------------------------------------------
# roof plan 10.00 x 8.00 = 80.000 m2 (the released finish area). Section prints 'SCREED 50mm', nothing else.
#   screed  80.000 x 0.050 = 4.000 m3 DRAWING-CONFIRMED
#   insulation: printed nowhere, no owner rule -> HELD blank, 80.000 beside
# falls variant (no constant screed printed): above-t0 volume 4.000 m3 over an 85.000 m2 outline (to the wall faces),
#   highest rise 0.120 m, roof plan basis 80.000: AT_LEAST = 4.000 - 5.000 x 0.120 = 3.400 m3
# fence 30.00 x 2.50 = 75.000 m2 per face; no finish printed: plaster / paint HELD at most 75.000; printed -> 75.000


def test_r646_screed_printed_insulation_unprinted():
    s = R.layer_quantity("SCREED", "80.000", printed=True, thickness_m="0.050", thickness_source="section 'SCREED 50mm'")
    assert s["class"] == "RELEASED" and s["value"] == D("4.000000") and s["status"] == "DRAWING-CONFIRMED"
    i = R.layer_quantity("INSULATION", "80.000")
    assert i["class"] == "HELD" and i["value"] is None and i["beside_area_m2"] == D("80.000000")
    p = R.layer_quantity("PROTECTION", "80.000", printed=True)
    assert p["class"] == "RELEASED" and p["value"] == D("80.000000")


def test_r646_adverse_unprinted_thickness_refused():
    with pytest.raises(R.RuleError, match="no printed source"):
        R.layer_quantity("SCREED", "80.000", owner_rule="Q-41", thickness_m="0.050")
    # owner rule establishes the screed, thickness unprinted: HELD, never a default, never 0
    h = R.layer_quantity("FALLS_SCREED", "80.000", owner_rule="Q-41")
    assert h["class"] == "HELD" and h["value"] is None
    with pytest.raises(R.RuleError, match="mm read as m"):
        R.layer_quantity("SCREED", "80.000", printed=True, thickness_m="50", thickness_source="section")
    with pytest.raises(R.RuleError, match="B8-06"):
        R.layer_quantity("MEMBRANE", "80.000", printed=True)
    with pytest.raises(R.RuleError, match="never 0"):
        R.layer_quantity("INSULATION", "0")


def test_r646_falls_bound_by_hand_and_adverse():
    assert R.screed_at_least("4.000", "85.000", "80.000", "0.120", fall="1 %", outlets=2) == D("3.400000")
    # the whole outline as basis: the bound is the above-t0 volume itself
    assert R.screed_at_least("4.000", "85.000", "85.000", "0.120", fall="1 %", outlets=1) == D("4.000000")
    with pytest.raises(R.RuleError, match="invent screed"):
        R.screed_at_least("4.000", "80.000", "85.000", "0.120", fall="1 %", outlets=1)
    with pytest.raises(R.RuleError, match="no outlet"):
        R.screed_at_least("4.000", "85.000", "80.000", "0.120", fall="1 %", outlets=0)
    with pytest.raises(R.RuleError, match="no printed fall"):
        R.screed_at_least("4.000", "85.000", "80.000", "0.120", fall=None, outlets=1)
    with pytest.raises(R.RuleError, match="mm read as m"):
        R.screed_at_least("4.000", "85.000", "80.000", "120", fall="1 %", outlets=1)
    with pytest.raises(R.RuleError, match="never 0"):
        R.screed_at_least("0.500", "85.000", "80.000", "0.120", fall="1 %", outlets=1)


def test_r646_fence_layers_and_adverse():
    h = R.fence_layer("75.000", face_key="N:OUT")
    assert h["class"] == "HELD" and h["held_high"] == D("75.000000") and h["held_low"] is None
    assert R.fence_layer("75.000", finish_printed=True)["measured_net"] == D("75.000000")
    assert R.fence_layer("75.000", owner_scope_faces={"N:PLOT"}, face_key="N:PLOT")["class"] == "RELEASED"
    assert R.fence_layer("75.000", owner_scope_faces={"N:PLOT"}, face_key="N:OUT")["class"] == "HELD"
    with pytest.raises(R.RuleError, match="house facade"):
        R.fence_layer("75.000", house_system=True)
    assert R.fence_layer(None)["class"] == "HELD"


def test_r646_one_area_and_entry_checks():
    assert R.one_area("80.000", "80.000") == 0
    with pytest.raises(R.RuleError, match="no named cause"):
        R.one_area("85.000", "80.000")
    assert R.one_area("85.000", "80.000", cause="membrane to the wall faces") == D("5.000")
    base = {"line_id": "X", "class": "R_SCREED_BOUNDED", "cause": "c",
            "fix": {"after": {"class": "HELD", "measured_net": None, "held_low": "3.4", "held_high": None}}}
    assert R.check_entry(base)
    for bad, msg in ((dict(base, cause=""), "no named cause"), (dict(base, **{"class": "X"}), "class"),
                     (dict(base, fix={"after": {"class": "HELD", "held_low": "0", "held_high": None}}), "never 0"),
                     (dict(base, fix={"after": {"class": "HELD", "held_low": "5", "held_high": "4"}}), "low"),
                     (dict(base, fix={"after": {"class": "RELEASED", "measured_net": "0"}}), "released as 0")):
        with pytest.raises(R.RuleError, match=msg):
            R.check_entry(bad)


def test_r646_order_invariant():
    a = [{"line_id": str(i), "class": c, "cause": "x"} for i, c in enumerate(R.CLASSES)]
    assert R.census_counts(a) == R.census_counts(list(reversed(a)))


# ---- development villa ----------------------------------------------------------------------------------------------
@pytest.mark.skipif(os.environ.get("URBAN_T646_WRITE") != "1", reason="writer only on request")
def test_write_outputs():
    A.write_outputs()


def test_build_reproduces_committed_output():
    b = A.build()
    assert A.dumps(b) == A.OUT_JSON.read_text(encoding="utf-8")
    assert A.render_md(b) == A.OUT_MD.read_text(encoding="utf-8")


def test_alsenan_census():
    b = A.build()
    c = b["counts"]
    assert c["lines"] == 43 and len({e["line_id"] for e in b["lines"]}) == 43
    assert c["by_class"] == {"F_FACE_HELD": 7, "F_LAYER_HELD": 16, "R_LAYER_UNPRINTED": 8, "R_SCREED_BOUNDED": 3,
                             "R_ZONE_HELD": 9}
    assert c["released_rows"] == 0 and c["bounded_rows"] == 3
    lows = {e["zone"]: e["fix"]["after"]["held_low"] for e in b["lines"] if e.get("fix")}
    # hand: 2.7176 - 1.078 x 0.1901; 3.4008 - 0.6400 x 0.1187; 8.089 - 30.87554 x 0.1068
    assert lows == {"TERRACE-550": "2.512672", "ROOF-430": "3.324832", "ROOF-970": "4.791492"}
    assert b["bounded_by_code"]["FIN.ROOF.SCREED"]["low"] == "10.628996"
    assert b["roof_plan_area_total_m2"] == "206.738932"
    assert b["fence_layers_at_most_on_released_faces_m2"] == "330.402"   # 2 x (83.1305 + 82.0705)
    for e in b["lines"]:
        assert "measured_net" not in e or e["measured_net"] is None
        if e["item_code"] in ("FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION") and e["class"] == "R_LAYER_UNPRINTED":
            assert e["beside"]["roof_plan_area_if_present_m2"] in A.ROOF_FINISH_VALUES
        if "ROOF-1390" in e["element_id"]:
            assert e["class"] == "R_ZONE_HELD" and "Q-34" in e["cause"] and not e.get("fix")


def test_no_coordinates_or_client_text():
    s = A.OUT_JSON.read_text(encoding="utf-8") + A.OUT_MD.read_text(encoding="utf-8")
    for bad in ("Alsenan", "alsenan", "chalet"):
        assert bad not in s
