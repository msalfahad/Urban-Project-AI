"""T-213 on the development villa (research/agents_t213/SUNKEN_PANELS_T213.json: handles, areas, lengths, statuses;
no coordinates). One set of six panels under two storey conventions (T-139 names by slab sheet, T-206 by the floor
carried); every drop-driven quantity HELD (no sheet prints the drop; D-41)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RES = json.loads((ROOT / "research" / "agents_t213" / "SUNKEN_PANELS_T213.json").read_text())
HAND = {"275": 3.325, "276": 2.5725, "280": 7.3009, "287": 2.0804, "298": 4.1076, "5BF": 5.4}


def test_one_set_two_conventions():
    P = {p["handle"]: p for p in RES["panels"]}
    assert set(P) == set(HAND)
    assert sum(p["floor_carried"] == "1F" for p in P.values()) == 5 and P["5BF"]["floor_carried"] == "2F"
    assert all(p["sheet"] == "GF roof slab" for h, p in P.items() if h != "5BF")
    m = RES["t139_match"]
    assert not m["unmatched_t139"] and not m["unmatched_dxf"] and len(m["pairs"]) == 6
    res = {b: r for a, b, _, _, r in m["pairs"]}
    assert res["298"] == pytest.approx(-0.01, abs=1e-4) and all(abs(v) < 1e-9 for k, v in res.items() if k != "298")
    assert RES["totals"] == {"1F": pytest.approx(19.3864), "2F": pytest.approx(5.4)}


def test_areas_and_statuses():
    for p in RES["panels"]:
        assert p["area_m2"] == pytest.approx(HAND[p["handle"]], abs=1e-4)
        assert p["area_status"] == "DRAWING-CONFIRMED" and p["unexplained_voids"] == []
        assert p["P_ext_m"] + p["P_shared_m"] == pytest.approx(p["perimeter_m"], abs=1e-3)
        assert p["drop_m"] is None and p["drop_status"].startswith("HELD")
        q = p["quantities"]
        assert q["slab_concrete_m3"]["value"] == pytest.approx(p["area_m2"] * 0.16, abs=1e-4)
        for k in ("step_riser_form_m2", "fill_buildup_m3_laneA", "waterproof_upturn_m2_laneA"):
            assert q[k]["value"] is None and q[k]["status"] == "HELD"


def test_shared_pairs_are_mutual_and_beam_widths_scheduled():
    P = {p["handle"]: p for p in RES["panels"]}
    for a, b, w in (("275", "276", 0.2), ("280", "287", 0.9)):
        assert b in P[a]["shared_with"] and a in P[b]["shared_with"]
        assert P[a]["shared_gap_m"][b] == pytest.approx(w)
    assert P["298"]["P_shared_m"] == 0 and P["5BF"]["P_shared_m"] == 0


def test_no_coordinates_published():
    txt = json.dumps(RES)
    assert "vertices" not in txt and "centroid" not in txt
