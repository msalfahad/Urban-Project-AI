"""Phase 2B-5 (ARCH_TAKEOFF_V2.6): the trace is what the engine cut, and only that.

    - with the trace on (V2.6) the V2.5 layout is the same plan: every quantity, roll record, scrap record and band
      piece of the V2.5 layout is unchanged; only the method name and the added trace differ
    - the traced plan of the three audited rooms is, cut for cut, the plan the Phase 2B-4 audit rebuilt by hand
      (WPB-A1, WPE-A1, WPD-A1: the same rolls, rips, cross-cuts, laying order and doorway pieces; names aside)
    - the installation layer is deterministic
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "m9_p2b4"))
sys.path.insert(0, str(HERE.parent / "m9_p2b3"))

import construct_cases as CC                                  # noqa: E402
import install_cases as IC                                    # noqa: E402
import install_engine as IE                                   # noqa: E402
import proof_cases as PC                                      # noqa: E402
import proof_engine as PE                                     # noqa: E402

from engine.source import knowledge as K                      # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402


def canon(p):
    """a plan's structure without its names: per roll the cuts in order, each as (width, length, rip parts, cross-cut
    pieces); the band runs and doorway pieces as their sizes."""
    size = {}

    def node(n, w, ln):
        size[n] = (w, ln)
        parts = tuple(node(k, x, ln) for k, x in p.get("rip", {}).get(n, ()))
        cuts = tuple(node(k, w, x) for k, x in p.get("cross", {}).get(n, ()))
        return (w, ln, parts, cuts)
    rolls = tuple(tuple(node(c, 1000, ln) for c, ln in r) for r in p["rolls"])
    return {"along": p["along"], "j": p["j"], "rolls": rolls,
            "floor": [size[e] if isinstance(e, str) else [size[x] for x in e] for e in p["floor"]],
            "runs": [[size[x] for x in r] for r in p["runs"]],
            "doorways": {d: size[x] for d, x in p.get("doorways", {}).items()}}


@pytest.mark.parametrize("audit,ex", [(CC.WPB_A1, IC.IX02), (CC.WPE_A1, IC.IX03), (CC.WPD_A1, IC.IX04)],
                         ids=["WP-B", "WP-E", "WP-D"])
def test_the_traced_plan_is_the_audited_plan(audit, ex):
    eng = IE.plan(IE.area(ex["room"], room_id=ex["id"]))
    assert canon(eng) == canon(audit["plan"])


def _v25_view(a):
    lay = copy.deepcopy(a["layout"])
    lay.pop("method")
    lay["layout"].pop("trace", None)
    row = {k: v for k, v in a["row"].items()}
    return lay, row


V26_ROW_KEYS = {"final_material_state", "material_state_reasons", "installation_state", "installation_flags",
                "true_waste_m2", "reusable_offcuts_subject_to_n7_m2", "roll_stock_m2", "band_joints",
                "min_joint_corner_m", "min_joint_seam_end_m", "best_order_min_corner_m", "best_order_min_seam_end_m",
                "junction", "roll_sensitivity_v26"}


@pytest.mark.parametrize("case", [PC.WP_A, PC.WP_B, PC.WP_C, PC.WP_D, PC.WP_E, PC.WP_F, PC.WP_G, PC.WP_S, PC.WP_W,
                                  PC.WP_BX, PC.WP_CX, PC.WP_LX], ids=lambda c: c["id"])
def test_the_trace_changes_nothing_of_the_v25_layout(case, monkeypatch):
    a25 = PE.wp_area(case, PE.V25)
    real = WS.build_area

    def v26(area, resolver, **kw):                               # the proof adapter's own call, with v26 on
        kw.pop("v25", None)
        area = dict(area, ring_segments=None)
        return real(area, resolver, v26=True)
    monkeypatch.setattr(WS, "build_area", v26)
    a26 = PE.wp_area(case, PE.V25)
    l25, r25 = _v25_view(a25)
    l26, r26 = _v25_view(a26)
    assert a26["layout"]["method"] == "MEMBRANE_POLYGON_STRIPS_V2_6"
    assert json.dumps(l25, sort_keys=True, default=str) == json.dumps(l26, sort_keys=True, default=str)
    for k, v in r25.items():
        if k == "final_material_state":
            assert r26[k] in (v, "PROVISIONAL_DETAILS_OPEN")
            continue
        assert r26[k] == v, k
    assert set(r26) - set(r25) <= V26_ROW_KEYS
    assert a26["v25"] == a25["v25"]


def test_the_installation_layer_is_deterministic():
    for ex in IC.SINGLE:
        one = IE.area(ex["room"], room_id=ex["id"])
        two = IE.area(ex["room"], room_id=ex["id"])
        assert json.dumps(one["v26"], sort_keys=True, default=str) == json.dumps(two["v26"], sort_keys=True,
                                                                                default=str)


def test_v25_never_reaches_the_installation_layer():
    with K.using("1.1.0"):
        a = PE.wp_area(PC.WP_B, PE.V25)
    assert "v26" not in a and "trace" not in a["layout"]["layout"]
    assert a["layout"]["method"] == "MEMBRANE_POLYGON_STRIPS_V2_5"
