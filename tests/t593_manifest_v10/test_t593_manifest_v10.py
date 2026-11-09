"""T-593: WIRING MANIFEST V10 + OVERLAY DRY RUN (R-T593-1).

Synthetic villa K593 (not the training villa; hand values): 2 house doors + 1 gate.
  door A: wall gap 1.00, jambs 0.05 + 0.05 -> nosing 0.90 (attribute), riser 0.15 -> 1.00 x 0.15 = 0.150 m2;
          owning threshold line 1.00 x 0.20 = 0.200 m2 (RELEASED)
  door B: wall gap 0.90, nosing 0.80, riser 0.20 -> 0.180 m2; owning line HELD exact 0.18 .. 0.18 (0.90 x 0.20)
  gate  : wall gap 1.20, nosing 1.10, riser 0.10 -> 0.120 m2, PARTIAL, its own row on a HELD-blank threshold line
  house = 1.90 lm nr 2 (never 1.70 = the nosings, never 3.10 with the gate), riser 0.330 m2.
Stair skirting K593: piece P1 two forms pitch 1.50 | zigzag 2.10 (exact bound on each form line), piece P2 held
0 .. 0.80 on the sloped form only. Adverse: a second reading of a door edge is EXCLUDED; both lengths payable,
nosing longer than the stone, payable x depth != line m2, riser with no figure and no bound, pitch > zigzag, HELD
0 .. 0, absorbing a quantity op or a differing before, a NO_LINE element with a live line: all refused / caught.
Then the training-villa build must be the rebuild and close by hand on the merged T-592 / T-585 figures."""

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t593"))
import manifest_v10 as M          # noqa: E402

OV = M.OV


def _l(lid, code, el, cls="RELEASED", net=None, unit="m2", lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": el, "class": cls, "measured_net": net,
            "held_low": lo, "held_high": hi}


def _opening(name, gap, nosing, riser, line, width=None):
    rm2 = None if riser is None else format((Decimal(gap) * Decimal(riser)).quantize(Decimal("0.001")), "f")
    return {"opening": name, "payable_lm": gap, "nosing_lm": nosing, "riser_m": riser, "riser_m2": rm2,
            "riser_m2_bound": None, "nr": 1, "nosing_basis": "VISIBLE_EDGE_BETWEEN_JAMBS (attribute, not payable)",
            "payable_basis": "INSTALLED_PIECE_MASONRY_OPENING", "owning_line": line,
            "t325_strip_width_m": width, "wall_depth_m": "0.2", "t325_state": "MEASURED" if line else "UNRESOLVED",
            "nosing_source": f"front edge E-{name}", "drawing_conflict": None}


@pytest.fixture
def villa():
    idx = {l["line_id"]: l for l in [
        _l("K-TA", "FIN.MARBLE.THRESHOLD", "K-STRIP-A", net=0.2),
        _l("K-TB", "ARCH.THRESHOLD", "K-STRIP-B", cls="HELD", lo=0.18, hi=0.18),
        _l("K-TG", "ARCH.THRESHOLD", "K-GATE-STRIP", cls="HELD"),
        _l("K-S1", "FIN.STAIR.SKIRTING.SLOPED", "STAIR-SKIRT:P1", cls="HELD", unit="lm"),
        _l("K-Z1", "FIN.STAIR.SKIRTING.ZIGZAG", "STAIR-SKIRT:P1", cls="HELD", unit="lm"),
        _l("K-S2", "FIN.STAIR.SKIRTING.SLOPED", "STAIR-SKIRT:P2", cls="HELD", unit="lm"),
        _l("K-Z2", "FIN.STAIR.SKIRTING.ZIGZAG", "STAIR-SKIRT:P2", cls="HELD", unit="lm"),
        _l("K-SK", "FIN.SKIRTING", "K-ROOM:skirting", net=12.0, unit="lm"),
    ]}
    t592 = {"openings": {"D-A": _opening("D-A", "1.00", "0.90", "0.15", "K-TA", "1.00"),
                         "D-B": _opening("D-B", "0.90", "0.80", "0.20", "K-TB", "0.90"),
                         "D-G": _opening("D-G", "1.20", "1.10", "0.10", None)}}
    return idx, t592


def test_door_steps_hand_totals(villa):
    idx, t592 = villa
    P, rows, claims, house = M.pkg_door_steps(t592, idx, gate_line="K-TG")
    assert house == {"house_lm": "1.9", "house_nr": 2, "house_riser_m2": "0.330", "house_nosing_attribute_lm": "1.7"}
    by = {r["line_id"]: r for r in rows}
    assert by["K-TA"]["beside"]["step_lm_payable"] == "1" and by["K-TA"]["beside"]["riser_m2"] == "0.15"
    assert by["K-TB"]["beside"]["binding"]["payable_x_depth_eq_line_m2"] is True
    g = by["K-TG"]
    assert g["row"] == "FR-T592-2" and g["beside"]["status"] == "PARTIAL"
    assert g["beside"]["step_lm_payable"] == "1.2" and g["beside"]["riser_m2"] == "0.12"
    assert g["evidence"]["status"] == "PARTIALLY VERIFIED"
    assert all(r["kind"] == "BESIDE" and r["after"] is None for r in rows)       # no line's own state moves
    after, rep = OV.apply(idx, [(P, rows)])
    assert after == idx and all(r["status"] == "APPLIED" for r in rep["rows"])


def test_second_reading_of_a_door_edge_is_excluded(villa):
    idx, t592 = villa
    _, rows, claims, _ = M.pkg_door_steps(t592, idx, gate_line="K-TG")
    claims = claims + [("D-A:front edge E-D-A", "NEW:FIN.STAIR.STEP_LM:K-DOOR-A", "second-reading")]
    c = M.door_edge_census(claims)
    assert c["edges"] == 3
    assert c["excluded_second_readings"] == [{"edge": "D-A:front edge E-D-A", "claimant": "NEW:FIN.STAIR.STEP_LM:K-DOOR-A",
                                              "row": "second-reading", "class": "EXCLUDED",
                                              "repeats": c["owners"]["D-A:front edge E-D-A"]["row"]}]


def test_both_lengths_payable_refused(villa):
    idx, t592 = villa
    t592["openings"]["D-A"]["nosing_basis"] = "PAYABLE_EDGE"
    with pytest.raises(M.ManifestError, match="one payable length"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")


def test_nosing_longer_than_stone_refused(villa):
    idx, t592 = villa
    t592["openings"]["D-B"]["nosing_lm"] = "0.95"
    with pytest.raises(M.ManifestError, match="longer than the stone"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")


def test_step_on_the_wrong_line_refused(villa):
    idx, t592 = villa
    t592["openings"]["D-A"]["owning_line"] = "K-TB"          # 1.00 x 0.20 = 0.200 != 0.18
    t592["openings"]["D-A"]["t325_strip_width_m"] = None
    with pytest.raises(M.ManifestError, match="!= line m2"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")
    t592["openings"]["D-A"]["owning_line"] = "K-SK"          # not a threshold m2 line
    with pytest.raises(M.ManifestError, match="not a threshold m2 line"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")


def test_riser_without_figure_stays_held_never_0(villa):
    idx, t592 = villa
    o = t592["openings"]["D-B"]
    o["riser_m"], o["riser_m2"] = None, None
    with pytest.raises(M.ManifestError, match="HELD with its bound"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")
    o["riser_m2_bound"] = ["0", "0.270"]
    _, rows, _, house = M.pkg_door_steps(t592, idx, gate_line="K-TG")
    b = next(r for r in rows if r["line_id"] == "K-TB")["beside"]
    assert b["riser_m2"] is None and b["riser_m2_held"] == ["0", "0.270"]
    assert house["house_riser_m2"] == "0.150"                  # only the figure that exists; the held one is named
    o["riser_m"], o["riser_m2_bound"] = "0", None
    with pytest.raises(M.ManifestError, match="equal levels"):
        M.pkg_door_steps(t592, idx, gate_line="K-TG")


def _t585(held=None):
    return {"stairs": {"by_stair": {"K": {"held": held if held is not None else
                                          [{"pid": "P2", "class": "HELD", "bound": ["0", "0.8"], "cause": "window"}],
                                          "steps_held": []}},
                       "two_form_pitch_lm": "1.5", "two_form_zigzag_lm": "2.1", "flight_lo": "1.5"}}


PIECES = {"P1": {"pid": "P1", "kind": "FLIGHT", "status": "HELD-FORM", "sloped_lm": "1.5", "zigzag_lm": "2.1"},
          "P2": {"pid": "P2", "kind": "FLIGHT", "status": "HELD", "sloped_lm": "0.8", "zigzag_lm": "1.2"}}


def test_two_forms_exact_bound_never_added(villa):
    idx, _ = villa
    P, rows, sk = M.pkg_stair_skirting(copy.deepcopy(PIECES), _t585(), idx)
    after, rep = OV.apply(idx, [(P, rows)], M.RULINGS_V10[:0] + [dict(M.RULINGS_V10[0], sources=["CANDIDATE", P])])
    assert after["K-S1"]["held_low"] == after["K-S1"]["held_high"] == 1.5
    assert after["K-Z1"]["held_low"] == after["K-Z1"]["held_high"] == 2.1
    assert (after["K-S2"]["held_low"], after["K-S2"]["held_high"]) == (0.0, 0.8)
    assert OV.state(after["K-Z2"]) == OV.state(idx["K-Z2"])        # the form P2's source does not bound
    t = OV.totals(after)
    assert t["FIN.STAIR.SKIRTING.SLOPED|lm"]["held_low"] == "1.5" and t["FIN.STAIR.SKIRTING.SLOPED|lm"]["held_high"] == "2.3"
    assert t["FIN.STAIR.SKIRTING.ZIGZAG|lm"]["held_low"] == "2.1" and t["FIN.STAIR.SKIRTING.ZIGZAG|lm"]["held_blank_n"] == 1
    assert all(l["class"] != "RELEASED" for k, l in after.items() if "SKIRTING." in l["item_code"])
    assert sk["flight_lower_bound_lm"] == "1.5"
    assert all(c["status"] == "EXPLAINED" for c in rep["conflicts"])


def test_pitch_above_zigzag_refused(villa):
    idx, _ = villa
    bad = copy.deepcopy(PIECES)
    bad["P1"]["sloped_lm"] = "2.2"
    with pytest.raises(M.ManifestError, match="pitch <= zigzag"):
        M.pkg_stair_skirting(bad, _t585(), idx)


def test_held_bound_collapsing_to_0_refused(villa):
    idx, _ = villa
    P, rows, _ = M.pkg_stair_skirting(copy.deepcopy(PIECES), _t585([{"pid": "P2", "class": "HELD", "bound": ["0", "0"],
                                                                      "cause": "x"}]), idx)
    with pytest.raises(OV.OverlayError, match="HELD_AS_0"):
        OV.apply(idx, [(P, rows)])


def test_absorb_only_text_only_with_same_before(villa):
    idx, _ = villa
    st = OV.state(idx["K-TA"])
    txt = {"op_id": "X|T|K-TA", "package": "X", "row": "T", "kind": "TEXT_ONLY", "line_id": "K-TA", "before": st,
           "after": None, "source": "X", "note": "printed figure checked"}
    order, taken = M.absorb([("X", [txt])], "X", "K-TA", st)
    assert order == [("X", [])] and taken["op_id"] == "X|T|K-TA"
    with pytest.raises(M.ManifestError, match="stated before differs"):
        M.absorb([("X", [txt])], "X", "K-TA", dict(st, measured_net=0.25))
    q = dict(txt, kind="SET", after=M.M9.released(0.25))
    with pytest.raises(M.ManifestError, match="only a TEXT_ONLY"):
        M.absorb([("X", [q])], "X", "K-TA", st)
    # without the absorb, a V10 row on the same line is refused by R1
    P, rows, _, _ = M.pkg_door_steps(villa[1], idx, gate_line="K-TG")
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(idx, [("X", [txt]), (P, rows)])


def test_no_line_probe_catches_a_live_line():
    r = M.no_line_rows(_ALS["T585"])[0]
    idx = {"L-x": _l("L-x", "FIN.SKIRTING", "STAIR-SKIRT:E1-LD:landing", net=3.5, unit="lm")}
    assert M.probe_no_line(idx, r) == ["L-x"]
    idx["L-x"]["class"] = "EXCLUDED"
    assert M.probe_no_line(idx, r) == []


# ---- training villa ---------------------------------------------------------------------------------------------

_ALS = {"T585": json.loads(M.IN["T585"].read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def built():
    return M.build()


def test_committed_output_is_the_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_overlay_clean(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v9": 5124, "after_v10": 5124}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v9_overlay"] == []
    assert [r["op_id"] for r in o["flagged_rows"]] == ["T-498|HOST_FACES_V5|L-4ccc5dc26bd2472b03ad"]   # T-580's own
    order = {x["package"]: x for x in o["order"]}
    assert order["T-423 r2"]["ops"] == 17                           # one TEXT_ONLY op absorbed by name
    assert order["DOOR_STEPS (T-592 FR-T592-1 / FR-T592-2)"]["status"] == {"APPLIED": 5}
    assert order["STAIR_SKIRTING_FORMS (T-585 flights)"]["status"] == {"APPLIED": 44}
    assert set(o["v10_vs_v9_totals"]) == {"FIN.STAIR.SKIRTING.SLOPED|lm", "FIN.STAIR.SKIRTING.ZIGZAG|lm"}
    assert built["released_quantities_changed"] == 0 and built["candidate_files_touched"] == 0
    assert built["stair_edge_census_after_v10"] == {"doubles": 0, "orphans": 0, "edges": 89}


def test_door_steps_close_by_hand(built):
    h = built["door_steps"]["house"]
    # wall gaps 1.000 + 0.900 + 1.000 + 0.900; riser 3.80 x 0.15; edges 0.9 + 0.8 + 0.9 + 0.9
    assert h == {"house_lm": "3.8", "house_nr": 4, "house_riser_m2": "0.570", "house_nosing_attribute_lm": "3.5"}
    g = built["door_steps"]["gate"]
    assert (g["step_lm"], g["riser_m2"], g["status"], g["in_house_total"]) == ("1.0", "0.150", "PARTIAL", False)
    rows = [r for r in built["rows"] if r["package"].startswith("DOOR_STEPS")]
    assert sorted(r["line_id"] for r in rows) == sorted(["L-b3933a51bd95e9bc542b", "L-74cd61b430eec9933d15",
                                                         "L-c8b5c7f742b22388339e", "L-8111095f6db78f0e674b",
                                                         "L-56acf34557c315f65bb1"])
    assert all(r["kind"] == "BESIDE" for r in rows)
    assert all(r["beside"]["binding"]["payable_x_depth_eq_line_m2"] for r in rows if r["row"] == "FR-T592-1")
    absorbed = next(r for r in rows if r["line_id"] == "L-c8b5c7f742b22388339e")["absorbs"]
    assert absorbed["op_id"] == "T-423 r2|TEXT_ONLY_22|L-c8b5c7f742b22388339e"
    assert built["door_steps"]["edge_census"]["excluded_second_readings"] == []
    d09 = next(r for r in rows if r["line_id"] == "L-8111095f6db78f0e674b")["beside"]
    assert d09["riser_m2"] == "0.135" and "drawing_conflict_named" in d09


def test_stair_skirting_close_by_hand(built):
    sk = built["stair_skirting"]
    assert (sk["two_form_pieces"], sk["pitch_lm"], sk["zigzag_lm"]) == (13, "17.009049", "23.300481")
    assert sk["flight_lower_bound_lm"] == "19.359049" == sk["t585_flight_lo"]          # 17.009049 + 2.35
    t = built["overlay"]["v10_vs_v9_totals"]
    s, z = t["FIN.STAIR.SKIRTING.SLOPED|lm"]["after"], t["FIN.STAIR.SKIRTING.ZIGZAG|lm"]["after"]
    # sloped high = 17.009049 + 1.233936 + 1.052389 + 0.350796 + 1.230432 + 0.232143; zigzag high = + 0.168 (MS2-TR.N)
    assert (s["held_low"], s["held_high"], s["held_blank_n"], s["released_n"]) == ("17.009049", "21.108745", 4, 0)
    assert (z["held_low"], z["held_high"], z["held_blank_n"], z["released_n"]) == ("23.300481", "23.468481", 8, 0)


def test_no_line_rows(built):
    nl = {r["row"]: r for r in built["no_line_rows"]}
    assert nl["E1 LANDING SKIRTING"]["status"] == "NOT_IN_DRAWING" and nl["E1 LANDING SKIRTING"]["live_lines_after"] == []
    y = nl["YARD SKIRTING"]
    assert y["beside"]["drawing_confirmed_lm"] == "0" and y["beside"]["his_lm"] == "81.32"
    assert y["live_lines_before"] == y["live_lines_after"] == []


def test_no_coordinates_or_names_in_output():
    text = M.OUT_JSON.read_text(encoding="utf-8")
    assert not any(ord(c) > 127 for c in text)
    assert "Alsenan" not in text and "alsenan" not in text
