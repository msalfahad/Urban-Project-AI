"""T-323 on the development villa (research/agents_t323/HATCH_CENSUS_T323.json and CONSUMERS_T323.json: handles,
face ids, lengths, areas; no coordinates). Every slab hatch of the three roof-slab plans of 'ST7757 dxf.dxf' against
the panel rebuilt from the drawn member faces (T-139 partition). Research only: no candidate or released line moves."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RES = json.loads((ROOT / "research" / "agents_t323" / "HATCH_CENSUS_T323.json").read_text())
CON = json.loads((ROOT / "research" / "agents_t323" / "CONSUMERS_T323.json").read_text())
H = {c["handle"]: c for c in RES["census"]}
SUNKEN_EXACT = ("275", "276", "280", "287", "5BF")
CANT_WHOLE = {"2B1": ["GF-112"], "38C": ["2F-007"], "390": ["2F-032"], "391": ["2F-048"],
              "54D": ["GF-143", "GF-144", "GF-158"]}
CANT_PORTION = {"273": ("GF-011", 0.25), "2B4": ("GF-066", 0.15), "5E0": ("1F-045", 0.20)}


def test_census_is_complete():
    assert len(H) == 14
    assert sum(c["legend"] == "Sunken slab." for c in H.values()) == 6
    assert sum(c["legend"] == "Cantilever portion." for c in H.values()) == 8
    assert len(RES["off_sheet"]) == 29 and all(o["why"].startswith("not on a roof-slab plan") for o in RES["off_sheet"])
    for c in H.values():
        assert sum(c["edge_m"].values()) == pytest.approx(c["hatch_perimeter_m"], abs=2e-3)
        assert c["edge_m"]["UNEXPLAINED"] == 0.0 and c["edge_m"]["FREE_EDGE"] == 0.0


def test_off_plan_hatches_are_wall_rings_not_slabs():
    rings = {o["handle"]: o for o in RES["off_sheet"] if o["pattern"] != "SOLID"}
    assert sorted(rings) == ["10E9", "1657", "7BD", "7C4", "7FB", "7FD", "80F"]
    assert rings["7BD"]["ring_net_m2"] == rings["10E9"]["ring_net_m2"] == pytest.approx(1.6)      # T-322 gross ring
    assert rings["7C4"]["ring_net_m2"] == pytest.approx(2.356726, abs=1.5e-3)                     # T-193 pool band
    assert sum(o["pattern"] == "SOLID" for o in RES["off_sheet"]) == 22


def test_five_sunken_hatches_are_their_panels():
    for h in SUNKEN_EXACT:
        c = H[h]
        assert c["hatch_is_panel_outline"] and c["rebuilt_status"] == "DRAWING-CONFIRMED"
        assert c["rebuilt_m2"] == c["hatch_m2"] and c["rebuilt_perimeter_m"] == c["hatch_perimeter_m"]
        assert abs(c["residual_m2"]) < 1e-4 and len(c["faces_under"]) == 1
        assert c["faces_under"][0]["t139_class"] == "SLAB"


def test_280_needs_both_region_loops():
    c = H["280"]
    assert c["region_loops"] == 2 and c["hatch_m2"] == pytest.approx(7.3009) and c["hatch_perimeter_m"] == pytest.approx(11.6255)
    assert c["consumer_readings"]["loop1_only_m2"] == pytest.approx(7.1231)              # the Checker's 11.612 reading
    assert c["consumer_readings"]["loop1_only_perimeter_m"] == pytest.approx(11.6122)


def test_298_is_not_its_panel_and_the_residual_is_named():
    c = H["298"]
    assert not c["hatch_is_panel_outline"]
    assert c["hatch_m2"] == pytest.approx(4.1076) and c["hatch_perimeter_m"] == pytest.approx(8.8426)   # pin 8.843
    assert c["rebuilt_m2"] == pytest.approx(4.1176) and c["rebuilt_perimeter_m"] == pytest.approx(8.8413)
    assert c["faces_under"][0]["t139_id"] == "GF-081"
    assert c["edge_m"]["ANNOTATION_CUT"] == pytest.approx(0.791) and list(c["annotation_cuts"]) == [
        "S-TEXT-SLAB CIRCLE 31C r 0.515"]
    assert c["residual_m2"] == pytest.approx(0.0100, abs=1e-4)
    assert c["residual_annotation_m2"]["S-TEXT-SLAB CIRCLE 31C r 0.515"] == pytest.approx(0.0225, abs=1e-4)
    assert c["hatch_beyond_panel_under_annotation_m2"]["S-TEXT-SLAB CIRCLE 31C r 0.515"] == pytest.approx(0.0125, abs=1e-4)
    assert c["residual_annotation_net_m2"] == pytest.approx(0.0100, abs=1e-4)
    assert c["residual_other_m2"] == pytest.approx(0.0, abs=1e-4)
    assert c["host_faces"][0]["t139_id"] == "GF-082" and c["host_faces"][0]["under_hatch_m2"] == pytest.approx(0.0125)
    assert c["consumer_readings"]["loop1_only_perimeter_m"] == pytest.approx(8.5594)     # the Checker's 8.560 reading


def test_cantilever_hatches_mark_beam_bands_not_slab_panels():
    for h, ids in CANT_WHOLE.items():
        c = H[h]
        assert c["hatch_is_panel_outline"] and [f["t139_id"] for f in c["faces_under"]] == ids
        assert all(f["t139_class"] == "BEAM_OR_COLUMN" for f in c["faces_under"])
        assert abs(c["residual_m2"]) < 1e-4 and c["candidate_slab_lines"] == []
    for h, (host, cut) in CANT_PORTION.items():
        c = H[h]
        assert c["rebuilt_status"] == "HELD" and c["rebuilt_m2"] is None and "PORTION" in c["held_why"]
        assert [f["t139_id"] for f in c["host_faces"]] == [host]
        assert c["host_faces"][0]["under_hatch_m2"] == pytest.approx(c["hatch_m2"])
        assert c["edge_m"]["ANNOTATION_CUT"] == pytest.approx(cut)
        assert c["annotation_cut_on_member_alignment_m"] == pytest.approx(cut)     # the support-face alignment
        assert all(k.startswith("S-REIN-SLAB") for k in c["annotation_cuts"])


def test_no_candidate_slab_line_reads_a_hatch_outline():
    lines = {h: H[h]["candidate_slab_lines"] for h in SUNKEN_EXACT + ("298",)}
    assert all(len(v) == 1 for v in lines.values())
    assert lines["298"][0]["line_id"] == "L-70830345ffdabc4cf7d5"
    assert lines["298"][0]["m3"] == pytest.approx(4.1176 * 0.16, abs=1e-5)          # the panel, not 4.1076 x 0.16
    assert abs(lines["298"][0]["m3"] - 4.1076 * 0.16) > 1e-3


def test_consumers_effect():
    t213 = CON["t213"]["298"]
    assert (t213["A_hatch_m2"], t213["A_panel_m2"]) == (4.1076, 4.1176)
    assert (t213["P_ext_hatch_m"], t213["P_ext_panel_m"]) == (8.8426, 8.8413)
    for h in ("275", "276", "287", "5BF"):
        r = CON["t213"][h]
        assert r["A_hatch_m2"] == r["A_panel_m2"] and r["P_ext_hatch_m"] == r["P_ext_panel_m"]
    w = CON["t288"]["walls_hatch_vs_panel"]
    assert w["GF-W12 under GF-081"]["axis_under_panel_m"] == [0.45, 0.45]          # T-288's column-gap step agrees
    assert w["GF-W32 under GF-016"]["axis_under_panel_m"] == [0.621, 0.6124]        # island loop past the panel edge
    assert CON["t288"]["clip_region_m2_hatch_vs_panel"]["287"] == [2.1456, 2.0804]
    assert CON["t288"]["unclaimed_hatch_vs_panel"] == [[], []]


PRIVATE = Path(os.environ.get("URBAN_PRIVATE", ROOT.parent / "private"))


@pytest.mark.skipif(not (PRIVATE / "ST7757.dxf").exists(), reason="private drawing not decoded in this checkout")
def test_census_reproduces_from_the_drawing():
    import sys
    sys.path.insert(0, str(ROOT / "research" / "agents_t323"))
    import alsenan_t323 as A
    assert json.loads(json.dumps(A.run(PRIVATE))) == RES
