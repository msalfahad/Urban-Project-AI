"""T-707 R-T707-1 (one top plane with printed thickness zones: a slab-top bound crosses a thickness zone only less the
printed thickness difference) and R-T707-2 (a column framed by a beam of open up / down-stand: LOWER_ONLY).
Villa V707 is hand-made (not the development villa); the last tests rebuild the development-villa table from committed
files only (the own DXF read is committed as values; the drawing never is)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t707"))
import t707_alsenan as A  # noqa: E402
import t707_rules as R  # noqa: E402

# V707 by hand. Roof plate, finished mark +7.50, base +3.20 APPROVED. General note 'slabs 15 cm unless stated'; panel
# Q1 prints 'T 20' (a heavy zone), Q2 / Q3 print nothing (0.15 by the note). Down-stand beam RB 20 x 60 between K1 / K2
# borders Q1 and Q2; window head drawn +6.40 (tol 0.010) under RB -> s_lo = 6.40 - 0.010 + 0.60 = 6.990.
# t_src = max(0.20, 0.15) = 0.20. Column K3 touches Q2 / Q3 only: top >= 6.990 - (0.20 - 0.15) = 6.940, h >= 3.740 m;
# K4 touches Q1 (and Q3): top >= 6.990, h >= 3.790 m. Section 0.08 m2: K3 low 0.299200, K4 low 0.303200.


def plate(**over):
    p = {"outline": "V707 roof", "plan_texts_inside": [{"kind": "THICKNESS", "text": "T 20"}],
         "noncontinuous_inside": 0, "section_marks_inside": 0,
         "section_steps": [{"section": "S-1", "step_m": "0", "inside_plane": None, "evidence": "continuous top"}],
         "level_convention": ["+3.20 / +7.50 printed where levels change"],
         "panels": {"Q1": {"thickness_texts_m": ["0.20"], "general_note_m": "0.15"},
                    "Q2": {"thickness_texts_m": [], "general_note_m": "0.15"},
                    "Q3": {"thickness_texts_m": [], "general_note_m": "0.15"}}}
    p.update(over)
    return p


def test_normal_zone_transfer_by_hand():
    rec = R.check_plate(plate())
    assert rec["state"] == "ONE_TOP_PLANE" and rec["t"] == {"Q1": X("0.20"), "Q2": X("0.15"), "Q3": X("0.15")}
    k3 = R.column_top_lo(s_lo="6.990", source_panels=["Q1", "Q2"], plate_rec=rec, touched=["Q2", "Q3"],
                         finished_mark="7.50")
    k4 = R.column_top_lo(s_lo="6.990", source_panels=["Q1", "Q2"], plate_rec=rec, touched=["Q3", "Q1"])
    assert k3["top_lo"] == X("6.940000") and k4["top_lo"] == X("6.990000") and k4["governing_panel"] == "Q1"
    h3 = R.column_height_lo(top_lo=k3["top_lo"], base="3.20")
    h4 = R.column_height_lo(top_lo=k4["top_lo"], base="3.20")
    assert (h3, h4) == (X("3.740000"), X("3.790000"))
    assert R.q6(X("0.08") * h3) == X("0.299200") and R.q6(X("0.08") * h4) == X("0.303200")


def test_mirror_and_order_free():
    rec = R.check_plate(plate())
    a = R.column_top_lo(s_lo="6.990", source_panels=["Q1", "Q2"], plate_rec=rec, touched=["Q2", "Q3"])
    b = R.column_top_lo(s_lo="6.990", source_panels=["Q2", "Q1"], plate_rec=rec, touched=["Q3", "Q2"])
    assert a["top_lo"] == b["top_lo"]
    # rotating the plan relabels nothing physical: renamed panels give the same bound
    ren = plate(panels={"Z": {"thickness_texts_m": ["0.20"]}, "Y": {"general_note_m": "0.15"},
                        "W": {"general_note_m": "0.15"}})
    rec2 = R.check_plate(ren)
    c = R.column_top_lo(s_lo="6.990", source_panels=["Z", "Y"], plate_rec=rec2, touched=["Y", "W"])
    assert c["top_lo"] == a["top_lo"]


def test_one_thickness_everywhere_is_r_t678_2_exactly():
    rec = R.check_plate(plate(panels={"Q1": {"general_note_m": "0.15"}, "Q2": {"general_note_m": "0.15"}},
                              plan_texts_inside=[]))
    k = R.column_top_lo(s_lo="6.990", source_panels=["Q1"], plate_rec=rec, touched=["Q2"])
    assert k["top_lo"] == X("6.990000")


def test_thicker_receiving_panel_takes_the_full_bound():
    rec = R.check_plate(plate())
    k = R.column_top_lo(s_lo="6.990", source_panels=["Q2"], plate_rec=rec, touched=["Q1"])
    assert k["top_lo"] == X("6.990000")


@pytest.mark.parametrize("over, msg", [
    ({"plan_texts_inside": [{"kind": "LEVEL", "text": "+7.30"}]}, "two planes"),
    ({"plan_texts_inside": [{"kind": "STEP", "text": "STEP"}]}, "two planes"),
    ({"noncontinuous_inside": 1}, "hidden / dashed"),
    ({"section_marks_inside": 1}, "section mark"),
    ({"level_convention": []}, "absence of a level text proves nothing"),
    ({"section_steps": [{"section": "S-1", "step_m": "0.10", "inside_plane": True, "evidence": "drawn"}]}, "inside"),
    ({"section_steps": [{"section": "S-1", "step_m": "0.10", "inside_plane": None, "evidence": "drawn"}]},
     "never assumed outside"),
    ({"panels": {"Q1": {"thickness_texts_m": ["0.20"]}, "Q2": {"thickness_texts_m": []}}}, "never borrowed"),
    ({"panels": {"Q1": {"thickness_texts_m": ["0.20", "0.18"]}}}, "CONFLICT"),
    ({"panels": {"Q1": {"thickness_texts_m": ["18"]}}}, "cm / mm"),
    ({"outline": None}, "outline"),
])
def test_adverse_plates_refused(over, msg):
    with pytest.raises(R.Refused, match=msg):
        R.check_plate(plate(**over))


def test_adverse_window_head_only_stays_held():
    """A column whose only top datum is a window head with NO printed beam over it: no bound; the line keeps its
    previous state by name (never 0, never closed)."""
    import t689_rules as R89
    head = {"id": "WZ", "head_abs": "6.40", "tol": "0.010", "status": "DRAWING-CONFIRMED", "at": ("1.00", "2.20")}
    with pytest.raises(R.Refused, match="not printed"):
        R89.beam_top_lower_bound(beam={"id": "none", "depth": None, "stand": "DOWN", "span": ("0", "4")}, heads=[head])
    kept = R89.keep((None, None), "D-39 slab top not printed")
    assert kept == {"state": "HELD", "low": None, "high": None, "item": "D-39 slab top not printed"}
    with pytest.raises(R.Refused, match="cannot bound"):
        R89.beam_top_lower_bound(beam={"id": "RB", "depth": "0.60", "stand": "DOWN", "span": ("0", "4")},
                                 heads=[dict(head, status="ASSUMED - OWNER-APPROVED")])


def test_adverse_unknown_panel_and_flagged_bound():
    rec = R.check_plate(plate())
    with pytest.raises(R.Refused, match="not in the plate"):
        R.column_top_lo(s_lo="6.990", source_panels=["Q1"], plate_rec=rec, touched=["Q9"])
    with pytest.raises(R.Refused, match="touches no panel"):
        R.column_top_lo(s_lo="6.990", source_panels=["Q1"], plate_rec=rec, touched=[])
    f = R.column_top_lo(s_lo="7.60", source_panels=["Q1"], plate_rec=rec, touched=["Q1"], finished_mark="7.50")
    assert f["state"] == R.FLAGGED


def test_r_t707_2_one_sided_never_zero():
    r = R.one_sided_low(areas=["0.10", "0.125"], h_lo="3.740", item="D-xx up / down-stand")
    assert r["class"] == "LOWER_ONLY" and r["low"] == X("0.374000") and r["high"] is None
    with pytest.raises(R.Refused, match="names its designer item"):
        R.one_sided_low(areas=["0.10"], h_lo="3.74", item="")
    with pytest.raises(R.Refused, match="reading is missing"):
        R.one_sided_low(areas=["0.10", None], h_lo="3.74", item="D-xx")
    with pytest.raises(R.Refused, match="never 0"):
        R.one_sided_low(areas=["0.10"], h_lo=None, item="D-xx")


def test_formwork_sides_by_hand():
    f = R.formwork_sides(perimeters=("1.20", "1.40"), h=("3.740", "4.30"), t=("0.15", "0.20"))
    assert f["low_m2"] == X("4.248000") and f["high_m2"] == X("5.810000")   # 1.20 x 3.54 ; 1.40 x 4.15
    o = R.formwork_sides(perimeters=("1.40", "1.40"), h=("3.740", None), t=("0.15", "0.15"))
    assert o["high_m2"] is None and o["state"] == "HELD"
    with pytest.raises(R.Refused):
        R.formwork_sides(perimeters=("1.40", "1.40"), h=("0.10", "4.0"), t=("0.15", "0.15"))


# ---------------------------------------------------------------------------------------------- development villa
def test_alsenan_rebuild_equals_committed():
    res = A.build()
    assert json.loads((ROOT / "research/agents_t707/out/T707_COLUMN_TAIL.json").read_text()) == \
        json.loads(json.dumps(res, sort_keys=True))


def test_alsenan_figures():
    res = A.build()
    by = {r["handle"]: r for r in res["lines"]}
    assert res["plate"]["t_by_panel"]["P1"] == "0.180000" and res["plate"]["t_by_panel"]["P4"] == "0.160000"
    assert by["418"]["after"] == ["0.457380", "0.595000"] and by["41E"]["after"][0] == "0.326700"
    assert by["421"]["after"][0] == by["41B"]["after"][0] == "0.328700"
    assert by["778"]["after"][0] == "0.201360"
    for h in ("40F", "424"):
        assert by[h]["after"] == ["0.328700", None] and by[h]["class_after"].startswith("HELD LOWER_ONLY")
    for r in res["lines"]:                              # narrowing only: no low moves down, no high moves
        if r["before"][0] is not None:
            assert X(r["after"][0]) >= X(r["before"][0]) and r["after"][1] == r["before"][1]
    fam = res["family"]
    assert fam["plate_transfer_applied_m3"] == "0.127240" and fam["zone_allowance_m3"] == "0.006400"
    assert fam["after"]["low"] == "11.800070" and fam["after"]["high"] == fam["before"]["high"] == "15.501500"
    assert fam["after"]["lower_only_floor"] == "0.657400" and fam["after"]["blank"] == 0
    assert all(f["state"] == "HELD with the column" for f in res["formwork"]) and len(res["formwork"]) == 13
