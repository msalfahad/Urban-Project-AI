"""T-650 R-T650-1 lintel payable form per opening: a non-Alsenan fixture worked by hand (one scheduled RC lintel, one
unscheduled precast fit, one > 4.00 m, a black unscheduled wall, a schedule gap, a curved band, a width bound), the
adverse cases (scheduled opening given a precast piece, FLAGGED / HELD as 0, units, duplicates, freelancer cause), mirror
invariance, and the training-villa rebuild against the committed numbers-only output (merged inputs only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t650"
sys.path.insert(0, str(HERE))
import t650_payable_form as R  # noqa: E402

# villa X schedule (not Alsenan): printed for BLACK walls only, bands 0-120 cm D 20, 121-250 cm D 25 (gap 120 < w < 121)
SCHED = {"source": "villa X S-05 LINTEL SCHEDULE", "scope": ("BLACK",),
         "bands": [{"row": "A", "lo_cm": 0, "hi_cm": 120, "d_cm": 20}, {"row": "B", "lo_cm": 121, "hi_cm": 250,
                                                                         "d_cm": 25}]}
D_OF = {"A": 0.20, "B": 0.25}


def ev(a_s, a_e, st_s="END_OF_MASONRY", st_e="END_OF_MASONRY", sid_s="", sid_e="", cap_e=""):
    return {"START": {"available_m": a_s, "own_band_m": a_s, "stopper": st_s, "stopper_id": sid_s,
                      "beyond_band_end": "", "search_capped": ""},
            "END": {"available_m": a_e, "own_band_m": a_e, "stopper": st_e, "stopper_id": sid_e,
                    "beyond_band_end": "", "search_capped": cap_e}}


def villa_x():
    ops = [
        # D1 BLACK 1.20 (band A, inclusive 120): RC; ends 0.50 / 0.90 >= 0.40
        {"id": "D1", "storey": "GF", "block_type": "BLACK", "width_m": 1.20, "existence": "REQUIRED",
         "precast_cls": "PIECE", "precast_piece_m": 1.50},
        # W1 WHITE 0.90, no schedule for white: owner precast piece 1.20 (0.90 + 0.30), established
        {"id": "W1", "storey": "GF", "block_type": "WHITE", "width_m": 0.90, "existence": "REQUIRED",
         "precast_cls": "PIECE", "precast_piece_m": 1.20},
        # W2 WHITE 3.80: 3.80 + 0.30 = 4.10 > 4.00 -> FLAGGED_OVER_4M -> structural line
        {"id": "W2", "storey": "1F", "block_type": "WHITE", "width_m": 3.80, "existence": "REQUIRED",
         "precast_cls": "FLAGGED_OVER_4M"},
        # D2 BLACK 1.205: inside the printed gap 120 < w < 121 -> SCHEDULE_SILENT
        {"id": "D2", "storey": "1F", "block_type": "BLACK", "width_m": 1.205, "existence": "REQUIRED",
         "precast_cls": "PIECE", "precast_piece_m": 1.50},
        # D3 BLACK 2.00 (band B, D 0.25): RC with a FLAGGED_DEFICIT end -> R-T524-1 record
        {"id": "D3", "storey": "1F", "block_type": "BLACK", "width_m": 2.00, "existence": "REQUIRED",
         "precast_cls": "FLAGGED_NO_BEARING"},
        # D4 BLACK 0.80 existence HELD: RC form, HELD blank
        {"id": "D4", "storey": "2F", "block_type": "BLACK", "width_m": 0.80, "existence": "HELD",
         "cause": "head not printed", "precast_cls": "PIECE_IF_BUILT", "precast_piece_m": 1.20},
    ]
    evid = {"D1": ev(0.50, 0.90), "D2": ev(0.60, 0.60), "D3": ev(0.20, 1.00, st_s="COLUMN"), "D4": ev(0.45, 0.45)}
    lines = {o["id"]: {"line_id": f"L-{o['id']}", "class_now": "HELD", "held_low_m3": None, "held_high_m3": None}
             for o in ops}
    B_of = {"D1": 0.20, "W1": 0.20, "W2": 0.20, "D2": 0.20, "D3": 0.20, "D4": 0.15}
    t524 = {"D3": {"low_m3": 0.1100, "high_m3": 0.1200}}
    return ops, evid, lines, B_of, t524


def run(ops=None, evid=None, lines=None, B_of=None, t524=None):
    o, e, l, b, t = villa_x()
    return R.restate(ops or o, SCHED, evid or e, t524 if t524 is not None else t, lines or l, B_of or b, D_OF, 0.40)


def test_villa_x_forms_by_hand():
    per = run()
    assert {k: r["form"] for k, r in per.items()} == {
        "D1": R.RC, "W1": R.PCS, "W2": R.STRUCT, "D2": R.SYS_HELD, "D3": R.RC, "D4": R.RC}
    # D1 by hand: lo = 0.20 x 0.20 x (1.20 + 0.80) = 0.080; hi = 0.20 x 0.20 x (1.20 + 0.50 + 0.90) = 0.104
    assert per["D1"]["state"] == R.BOUNDED and per["D1"]["schedule_rows"] == ["A"]
    assert per["D1"]["low_m3"] == 0.08 and per["D1"]["high_m3"] == 0.104 and per["D1"]["pcs"] is None
    assert per["W1"]["pcs"] == 1.20 and per["W1"]["state"] == "ESTABLISHED" and per["W1"]["low_m3"] is None
    assert per["W2"]["state"] == "FLAGGED" and per["W2"]["owner_line"].startswith("the structural line")
    assert per["D2"]["state"] == R.HELD_BLANK and "SCHEDULE_SILENT" in per["D2"]["form_why"]
    assert per["D3"]["state"] == R.HELD_NAME and (per["D3"]["low_m3"], per["D3"]["high_m3"]) == (0.11, 0.12)
    assert per["D3"]["schedule_rows"] == ["B"] and per["D3"]["D_m"] == 0.25
    assert per["D4"]["state"] == R.HELD_BLANK and per["D4"]["low_m3"] is None


def test_summary_once_and_never_both():
    per = run()
    s = R.summary(per, {})
    assert s["forms"] == {R.RC: 3, R.PCS: 1, R.STRUCT: 1, R.SYS_HELD: 1}
    assert s["m3_bounded_set"]["low_m3"] == 0.19 and s["m3_bounded_set"]["high_m3"] == 0.224
    assert s["both_pcs_and_m3"] == []
    assert s["pcs_governing"]["by_stock"]["1.20"]["ESTABLISHED"] == ["W1"]


def test_unscheduled_black_wall_system_held():
    ops = [{"id": "B1", "block_type": "BLACK", "width_m": 1.0, "existence": "REQUIRED", "precast_cls": "PIECE"}]
    form, rows, why = R.payable_form(ops[0], None)
    assert form == R.SYS_HELD and rows is None and "Q-60" in why
    form, _, _ = R.payable_form(dict(ops[0], block_type="WHITE"), None)
    assert form == R.PCS


def test_curved_band_and_no_masonry_go_to_structural_line():
    op = {"id": "C1", "block_type": "BLACK", "width_m": 1.0, "existence": "REQUIRED"}
    assert R.payable_form(dict(op, curved_band=True), SCHED)[0] == R.STRUCT
    assert R.payable_form(dict(op, masonry_ends=0), SCHED)[0] == R.STRUCT
    assert R.payable_form(dict(op, masonry_ends=1), SCHED)[0] == R.RC


def test_width_bound_one_band_covered_two_bands_straddle_gap():
    op = {"id": "B2", "block_type": "BLACK", "width_bound_m": [0.90, 1.00], "existence": "HELD"}
    assert R.payable_form(op, SCHED)[:2] == (R.RC, ["A"])
    op2 = dict(op, width_bound_m=[1.10, 1.30])          # 120 < w < 121 inside the bound
    assert R.payable_form(op2, SCHED)[0] == R.SYS_HELD


def test_required_with_width_bound_held_not_one_end():
    o, e, l, b, t = villa_x()
    o[0] = dict(o[0], width_m=None, width_bound_m=[1.00, 1.10])
    per = run(ops=o)
    assert per["D1"]["form"] == R.RC and per["D1"]["state"] == R.HELD_BLANK and per["D1"]["low_m3"] is None


def test_mirror_and_reorder_invariance():
    o, e, l, b, t = villa_x()
    m = {k: {"START": v["END"], "END": v["START"]} for k, v in e.items()}
    a, z = run(), run(ops=list(reversed(o)), evid=m)
    for k in a:
        assert (a[k]["form"], a[k]["state"], a[k].get("low_m3"), a[k].get("high_m3")) == \
               (z[k]["form"], z[k]["state"], z[k].get("low_m3"), z[k].get("high_m3"))


def test_capped_end_high_open():
    o, e, l, b, t = villa_x()
    e = dict(e, D1=ev(0.50, 3.0, cap_e="YES"))
    per = run(evid=e)
    assert per["D1"]["low_m3"] == 0.08 and per["D1"]["high_m3"] is None
    assert R.summary(per, {})["m3_bounded_set"]["high_m3"] is None


# ------------------------------------------------------------------------------------------------ adverse
def test_scheduled_opening_given_precast_piece_refused():
    per = run()
    with pytest.raises(R.PayableFormError, match="never both"):
        R.check_asserted("D1", per, pcs_m=1.50)
    assert R.check_asserted("W1", per, pcs_m=1.20)
    with pytest.raises(R.PayableFormError, match="payable form is PRECAST_PCS"):
        R.check_asserted("W1", per, m3=0.05)


def test_flagged_and_held_as_zero_refused():
    per = run()
    for oid in ("W2", "D4", "D2"):
        with pytest.raises(R.PayableFormError):
            R.check_asserted(oid, per, m3=0.0)
    with pytest.raises(R.PayableFormError, match="outside"):
        R.check_asserted("D1", per, m3=0.0)
    assert R.check_asserted("D1", per, m3=0.09)


def test_deficit_without_t524_record_refused():
    with pytest.raises(R.PayableFormError, match="R-T524-1"):
        run(t524={})


@pytest.mark.parametrize("w", [1200, 120.0, 0, -1.0, float("nan"), True, "1.2"])
def test_width_units_refused(w):
    o, e, l, b, t = villa_x()
    o[0] = dict(o[0], width_m=w)
    with pytest.raises(R.PayableFormError):
        run(ops=o)


def test_duplicate_unknown_block_and_line_set_refused():
    o, e, l, b, t = villa_x()
    with pytest.raises(R.PayableFormError, match="second record"):
        run(ops=o + [o[0]])
    with pytest.raises(R.PayableFormError, match="block type"):
        run(ops=[dict(o[0], block_type="GREY")] + o[1:])
    with pytest.raises(R.PayableFormError, match="line set"):
        run(lines={k: v for k, v in l.items() if k != "D1"})
    with pytest.raises(R.PayableFormError, match="exactly one"):
        run(ops=[dict(o[0], width_bound_m=[1.0, 1.1])] + o[1:])


def test_freelancer_figure_as_cause_refused():
    o, e, l, b, t = villa_x()
    o[5] = dict(o[5], cause="freelancer carries 1 pc")
    with pytest.raises(R.PayableFormError, match="freelancer"):
        run(ops=o)


def test_precast_class_needed_where_precast_governs():
    with pytest.raises(R.PayableFormError, match="precast class"):
        R.payable_form({"id": "W9", "block_type": "WHITE", "width_m": 1.0, "existence": "REQUIRED"}, SCHED)


# ------------------------------------------------------------------------------------------------ training villa
def test_training_villa_rebuild_equals_committed():
    res = R.build()
    committed = json.loads((HERE / "out" / "T650_PAYABLE_FORM.json").read_text())
    assert json.loads(json.dumps(res)) == committed


def test_training_villa_one_form_per_opening_and_conservation():
    res = R.build()
    per, s = res["per_opening"], res["summary"]
    assert s["openings"] == 60 and sum(s["forms"].values()) == 60
    assert s["forms"] == {R.RC: 60, R.PCS: 0, R.STRUCT: 0, R.SYS_HELD: 0}
    assert s["pcs_governing"]["label"].startswith("NOT_APPLICABLE") and s["both_pcs_and_m3"] == []
    assert s["rc_states"] == {R.BOUNDED: 8, R.HELD_NAME: 10, R.HELD_BLANK: 42}
    # the 6 candidate bounded lines reproduce exactly (control); 12 lines gain a bound
    unchanged = sorted(k for k, r in per.items() if r["change"] == "UNCHANGED")
    assert unchanged == ["D-1F-02", "D-1F-08", "D-2F-01", "D-GF-13", "W14", "W15"]
    assert sum(1 for r in per.values() if r["change"].startswith("NEW_BOUND")) == 12
    assert res["t524_conservation"]["low_m3"] == 0.372692 and res["t524_conservation"]["high_m3"] == 0.437542
    assert s["m3_bounded_set"]["low_m3"] == 0.991692 and s["m3_bounded_set"]["high_open_on"] == ["D-2F-01"]
    assert all(c["agree"] for c in res["control_t519"]) and len(res["control_t519"]) == 16
    # new bounds by hand: A-1F-01 0.15 x 0.20 x (1.00 + 0.80) = 0.054; P-1F-01 (L2) 0.15 x 0.20 x (1.30 + 0.80) = 0.063
    assert per["A-1F-01"]["low_m3"] == 0.054 and per["P-1F-01"]["low_m3"] == 0.063
    assert per["P-1F-01"]["high_m3"] == 0.12042            # 0.03 x (1.30 + 0.449 + 2.265)
    for r in per.values():
        assert r["state"] != R.HELD_BLANK or (r.get("low_m3") is None and r.get("high_m3") is None)


def test_training_villa_held_lines_keep_a_cause():
    per = R.build()["per_opening"]
    for r in per.values():
        if r["state"] == R.HELD_BLANK:
            assert r["why"] and "0" != r["why"]
