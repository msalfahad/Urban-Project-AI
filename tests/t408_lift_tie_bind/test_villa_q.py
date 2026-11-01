"""T-408 LIFT_TIE_BIND_V1 on hand villa Q (not the development villa). Every expected value is a hand calculation.

Ring outer 2.30 x 2.10, shaft 1.80 x 1.60 (walls 0.25). GF column outlines: SW 0.25 x 0.60, NW 0.25 x 0.60, NE 0.25 x 0.50,
SE 0.35 x 0.80 (0.10 proud of the ring, outwards). Clear runs: S 2.05 - 0.25 = 1.80, N 1.80, W 1.50 - 0.60 = 0.90,
E 1.60 - 0.80 = 0.80 -> 5.30 m. Storeys: GF 0.00 -> 4.80 (> 4.30: tie), 1F 4.80 -> 8.90 (4.10: none), 2F 8.90 -> 13.60
(4.70: tie). 2F SE column 0.25 x 0.60: E run 1.60 - 0.60 = 1.00 -> 5.50 m. Tie section printed for THIS member 0.25 x 0.45:
GF concrete 5.30 x 0.25 x 0.45 = 0.596250 m3; side forms 2 x 5.30 x 0.45 = 4.770 m2; soffit 5.30 x 0.25 = 1.325 m2; block
displaced 5.30 x 0.45 = 2.385 m2. 2F concrete 5.50 x 0.25 x 0.45 = 0.618750 m3. Clash: tie at +3.00, top 3.45; GF roof
ring beam top +4.70, depth 0.80 -> soffit 3.90: gap 0.45 CLEAR; a 1.40 m deep ring beam (soffit 3.30) clashes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t408"))
import lift_tie_v1 as X  # noqa: E402

RING, SHAFT = [0, 0, 2.30, 2.10], [0.25, 0.25, 2.05, 1.85]
GF_COLS = [[0, 0, 0.25, 0.60], [0, 1.50, 0.25, 2.10], [2.05, 1.60, 2.30, 2.10], [2.05, 0, 2.40, 0.80]]
F2_COLS = [[0, 0, 0.25, 0.60], [0, 1.50, 0.25, 2.10], [2.05, 1.60, 2.30, 2.10], [2.05, 0, 2.30, 0.60]]
RULE = {"limit": 4.30, "level": 3.00, "ref": "note 19"}
SEC = {"b": 0.25, "d": 0.45, "source": X.OWN_PRINT, "ref": "lift section A-A"}
GF = {"name": "GF", "ffl": 0.00, "next_ffl": 4.80}
F1 = {"name": "1F", "ffl": 4.80, "next_ffl": 8.90}
F2 = {"name": "2F", "ffl": 8.90, "next_ffl": 13.60}


def comp(res, suffix=""):
    return next(c for c in res["components"] if c["id"] == f"TIE_BEAM:{res['storey']}{suffix}")


def test_runs_on_the_storeys_own_columns():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    assert g["runs_m"] == {"S": 1.8, "N": 1.8, "W": 0.9, "E": 0.8}
    assert g["run_total_m"] == pytest.approx(5.30)
    assert X.storey_runs(RING, SHAFT, F2_COLS, "m")["run_total_m"] == pytest.approx(5.50)


def test_normal_valued_tie_and_dependent_items():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    r = X.tie_beam(GF, RULE, g, SEC, line_id="L-tie-gf", column_line_ids=["L-c1", "L-c2"],
                   ring_above={"top": 4.70, "depth": 0.80})
    assert r["required"] and r["tie_level_m"] == 3.0
    assert comp(r)["value"] == pytest.approx(0.596250) and comp(r)["status"] == X.DC
    assert comp(r, ":FORM_SIDES")["value"] == pytest.approx(4.770)
    assert comp(r, ":FORM_SOFFIT")["value"] == pytest.approx(1.325)
    assert comp(r, ":BLOCK_DISPLACED")["value"] == pytest.approx(2.385)
    assert comp(r, ":REBAR")["value"] is None and comp(r, ":REBAR")["status"] == X.HELD
    assert r["clash"] == {"state": "CLEAR", "detail": pytest.approx(0.45)}


def test_storey_not_over_limit_needs_no_tie_and_second_storey_over_limit_gets_its_own():
    g1 = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    assert X.tie_beam(F1, RULE, g1, SEC)["required"] is False
    g2 = X.storey_runs(RING, SHAFT, F2_COLS, "m")
    r = X.tie_beam(F2, RULE, g2, SEC, line_id="L-tie-2f")
    assert comp(r)["value"] == pytest.approx(0.618750)


def test_section_not_printed_is_held_with_length_never_zero():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    r = X.tie_beam(GF, RULE, g, None, line_id="L-tie-gf")
    for c in r["components"]:
        assert c["value"] is None and c["status"] == X.HELD and c["missing"]
        assert c["length_m"] == pytest.approx(5.30)
    r2 = X.tie_beam(GF, RULE, g, None)  # no candidate line at all
    assert all(c["status"] == X.MISSING and c["value"] is None for c in r2["components"])
    assert r["clash"]["state"] == X.OPEN and "tie-beam section (b x d)" in r["clash"]["detail"]


@pytest.mark.parametrize("src", ["RING_BEAM B7", "NEIGHBOUR B1", "GROUND_BEAM", "DEFAULT", "FREELANCER", None])
def test_section_borrowed_from_another_member_refused(src):
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    with pytest.raises(X.Refused) as e:
        X.tie_beam(GF, RULE, g, {**SEC, "source": src}, line_id="L-tie-gf")
    assert e.value.code == "SECTION_BORROWED"


def test_own_section_without_sheet_reference_refused():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    with pytest.raises(X.Refused) as e:
        X.tie_beam(GF, RULE, g, {**SEC, "ref": ""})
    assert e.value.code == "SECTION_BORROWED"


def test_tie_also_in_the_column_line_refused():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    with pytest.raises(X.Refused) as e:
        X.tie_beam(GF, RULE, g, SEC, line_id="L-c1", column_line_ids=["L-c1", "L-c2"])
    assert e.value.code == "TIE_IN_COLUMN_LINE"


def test_tie_measured_through_the_columns_refused():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    centre_line = 2 * ((2.30 - 0.25) + (2.10 - 0.25))  # 7.80 m round the ring centre line
    with pytest.raises(X.Refused) as e:
        X.tie_beam(GF, RULE, g, SEC, line_id="L-tie-gf", claimed_length_m=centre_line)
    assert e.value.code == "TIE_THROUGH_COLUMNS"


def test_tie_clashing_with_the_ring_beam_above_refused():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    with pytest.raises(X.Refused) as e:
        X.tie_beam(GF, RULE, g, SEC, line_id="L-tie-gf", ring_above={"top": 4.70, "depth": 1.40})
    assert e.value.code == "TIE_IN_RING_BEAM"


def test_unprinted_slab_level_leaves_clash_open_not_clear():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    r = X.tie_beam(GF, RULE, g, SEC, line_id="L-tie-gf", ring_above={"top": None, "depth": 0.80})
    assert r["clash"]["state"] == X.OPEN


def test_column_outline_missing_at_the_storey_refused():
    with pytest.raises(X.Refused) as e:
        X.storey_runs(RING, SHAFT, GF_COLS[:3] + [None], "m")
    assert e.value.code == "COLUMN_OUTLINE_MISSING"
    with pytest.raises(X.Refused):
        X.storey_runs(RING, SHAFT, [], "m")


def test_column_alternative_outwards_keeps_runs_inwards_refused():
    wider_out = [[-0.05, 0, 0.25, 0.60]] + GF_COLS[1:]   # 0.30 across the ring, growth outwards
    assert X.storey_runs(RING, SHAFT, wider_out, "m")["run_total_m"] == pytest.approx(5.30)
    wider_in = [[0, 0, 0.30, 0.60]] + GF_COLS[1:]        # growth into the shaft clear
    with pytest.raises(X.Refused) as e:
        X.storey_runs(RING, SHAFT, wider_in, "m")
    assert e.value.code == "SHAFT_CLEAR_REDUCED"


def test_mirror_quarter_turn_and_millimetres_identical():
    mx = lambda r: [-r[2], r[1], -r[0], r[3]]  # noqa: E731
    qt = lambda r: [-r[3], r[0], -r[1], r[2]]  # noqa: E731
    mm = lambda r: [v * 1000 for v in r]  # noqa: E731
    base = X.storey_runs(RING, SHAFT, GF_COLS, "m")["run_total_m"]
    assert X.storey_runs(mx(RING), mx(SHAFT), [mx(c) for c in GF_COLS], "m")["run_total_m"] == pytest.approx(base)
    assert X.storey_runs(qt(RING), qt(SHAFT), [qt(c) for c in GF_COLS], "m")["run_total_m"] == pytest.approx(base)
    assert X.storey_runs(mm(RING), mm(SHAFT), [mm(c) for c in GF_COLS], "mm")["run_total_m"] == pytest.approx(base)
    with pytest.raises(X.Refused):
        X.storey_runs(RING, SHAFT, GF_COLS, "ft")


def test_binding_drift_is_a_finding():
    exp = [{"component": "RING", "line_id": "L-1", "item_code": "STR.CONC.BEAM", "state": "PROVISIONAL", "value": 0.27},
           {"component": "CAP", "line_id": "L-2", "item_code": "STR.CONC.SLAB", "state": "PROVISIONAL", "value": 0.5184},
           {"component": "GONE", "line_id": "L-3", "item_code": "STR.CONC.BEAM", "state": "PROVISIONAL", "value": 1.0}]
    lines = {"L-1": {"item_code": "STR.CONC.BEAM", "state": "PROVISIONAL", "value": 0.27 + 1e-9},
             "L-2": {"item_code": "STR.CONC.SLAB", "state": "BLOCKED_RFI", "value": None}}
    rows = {r["component"]: r["result"] for r in X.bind_check(exp, lines)}
    assert rows == {"RING": "BOUND", "CAP": "BINDING_DRIFT:state/value", "GONE": "LINE_GONE"}


def test_held_line_must_name_every_fact():
    facts = {"pit depth": ["pit depth", "lift supplier"], "GF build-up": ["build-up", "slab-on-grade top"]}
    assert X.held_facts_check("held: pit depth as per lift supplier (D-43)", facts) == ["GF build-up"]
    assert X.held_facts_check("pit depth (supplier) and GF build-up F.F.L. -> slab top", facts) == []


def test_block_displacement_paired_with_the_tie():
    g = X.storey_runs(RING, SHAFT, GF_COLS, "m")
    held = X.tie_beam(GF, RULE, g, None, line_id="L-tie-gf")["components"]
    assert X.displacement_pairs(held, "BLOCKED_RFI")["result"] == "PAIRED"
    assert X.displacement_pairs(held, "PROVISIONAL")["result"] == "OPEN"
