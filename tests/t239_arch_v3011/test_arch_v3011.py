"""T-239: ARCH_TAKEOFF_V3.0.11, the SAME opt-in candidate as V3.0 .. V3.0.10 extended (engine.source.arch_v3011): a
footing outline that carries two or more schedule tags is a HELD CONFLICT carrying every reading, never one tag; its
blinding follows it. Synthetic data only (no client drawing).

VILLA K-239 (not the development villa). One drawn outline K-OUT-7, rectangular 2.60 x 1.20 = 3.12 m2, carries the two
tags FA and FB. Schedule rows: FA 2.20 x 1.20 x 0.60, FB 0.80 x 0.70 x 0.40. Blinding detail: projection 0.15 each
side, thickness 0.08. Hand values:
  footing  reading ROWS_SEPARATELY          2.20 x 1.20 x 0.60 + 0.80 x 0.70 x 0.40 = 1.584 + 0.224 = 1.808 m3
           reading OUTLINE_AT_DEEPEST_DEPTH 3.12 x 0.60 (FA is the deeper tag)          = 1.872 m3
           -> HELD 1.808 .. 1.872 m3 (the candidate carried FA alone: PROVISIONAL 1.584, a range that excludes both)
  blinding reading ROWS_SEPARATELY          (2.50 x 1.50 + 1.10 x 1.00) x 0.08 = (3.75 + 1.10) x 0.08 = 0.388 m3
           reading OUTLINE_AT_DEEPEST_DEPTH (2.90 x 1.50) x 0.08 = 4.35 x 0.08                    = 0.348 m3
           -> HELD 0.348 .. 0.388 m3 (the candidate carried BOUNDED 0.300 .. 0.388: its low is FA alone)
  Q-31 C provisional view: the BIGGER footing reading (outline, 1.872); the blinding view follows the footing's
  reading (outline, 0.348), which here is the SMALLER blinding figure: never chosen because it is larger.
  Unrelated lines (the other footing, a beam, a column) stay byte-identical.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30                      # noqa: E402
from engine.source import arch_v3011 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402

AP = pytest.approx
PID = "synthetic-v3011-villa-k239"
DOCS = [{"file": "K-STR.dxf", "sha256": "3" * 64}]
FOOT, BLIND = "STR.CONC.FOOTING", "STR.CONC.BLINDING"


def line(eid, item, floor="FOUNDATION", q=1.0, ev="SOURCE_DERIVED", br=None):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit="m3", evidence_state=ev,
                        measured_net=None if ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI") else q, bounded_range=br,
                        element_id=eid, floor=floor, physical_element=eid, formula="route", documents=DOCS,
                        rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI") else None)


def l3010():
    return [line("FTG:K-OUT-7", FOOT, q=1.584, ev="PROVISIONAL"),
            line("BLD:K-OUT-7", BLIND, ev="BOUNDED_EXPOSURE", br={"low": 0.300, "high": 0.388, "basis": "route"}),
            line("FTG:K-OUT-1", FOOT, q=0.900),
            line("BLD:FOOTINGS", BLIND, q=1.250, ev="PROVISIONAL"),
            line("P-C:BEAMS:GF:B1", "STR.CONC.BEAM", "GF", 1.2),
            line("P-C:COLS:GF:C1", "STR.CONC.COLUMN", "GF", 0.4)]


def src():
    return {"file": "research/T-FTG/LEDGER.csv", "sha256": "e" * 64, "task": "T-FTG", "merge_commit": "abc1234",
            "checker_run": "verifier run for T-FTG"}


def record(**kw):
    r = {"outline": "K-OUT-7", "tags": ["FA", "FB"], "floor": "FOUNDATION", "owner_item": "Q-31 C",
         "reasons": ["one drawn outline carries two schedule tags; the designer has not said which footing it is"],
         "schedule": {"FA": {"L": 2.20, "W": 1.20, "H": 0.60, "source": "schedule row FA"},
                      "FB": {"L": 0.80, "W": 0.70, "H": 0.40, "source": "schedule row FB"}},
         "drawn": {"a": 2.60, "b": 1.20, "area": 3.12, "rectangular": True, "source": "outline K-OUT-7"},
         "blinding": {"projection_m": 0.15, "thickness_m": 0.08, "source": "typical footing detail"},
         "footing": {"item_code": FOOT, "floor": "FOUNDATION", "element_id": "FTG:K-OUT-7", "unit": "m3",
                     "carried": 1.584, "why": "the candidate carried FA alone",
                     "readings": {"ROWS_SEPARATELY": 1.808, "OUTLINE_AT_DEEPEST_DEPTH": 1.872},
                     "range": [1.808, 1.872], "state": "HELD"},
         "blinding_line": {"item_code": BLIND, "floor": "FOUNDATION", "element_id": "BLD:K-OUT-7", "unit": "m3",
                           "carried": [0.300, 0.388], "why": "the candidate's low was FA alone",
                           "readings": {"ROWS_SEPARATELY": 0.388, "OUTLINE_AT_DEEPEST_DEPTH": 0.348},
                           "range": [0.348, 0.388], "state": "HELD"},
         "provisional_view": "OUTLINE_AT_DEEPEST_DEPTH"}
    r.update(kw)
    return r


def inputs(rec=None, **pc):
    p = {"piece": "MULTI_TAG_OUTLINE", "source": src(), "records": [rec or record()],
         "declared": {"footing": [1.808, 1.872], "blinding": [0.348, 0.388]}}
    p.update(pc)
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "pieces": [p]}


def run(inp=None, lines=None, earlier=()):
    lines = lines or l3010()
    doc = A.load_inputs(inp or inputs(), PID)
    ch, logs = A.changes_for(doc, lines, earlier)
    out, ident = A.integrate(lines, ch)
    return {ln["location"]["element_id"]: ln for ln in out}, ch, logs, ident, lines


# ------------------------------------------------------------------------------------------------ normal
def test_villa_k_hand_values_footing_and_blinding():
    g = A.readings_of(record())
    assert g["footing"]["ROWS_SEPARATELY"] == AP(1.808, abs=1e-9)
    assert g["footing"]["OUTLINE_AT_DEEPEST_DEPTH"] == AP(1.872, abs=1e-9)
    assert g["blinding_m2"]["ROWS_SEPARATELY"] == AP(4.85, abs=1e-9)
    assert g["blinding_m2"]["OUTLINE_AT_DEEPEST_DEPTH"] == AP(4.35, abs=1e-9)
    assert g["blinding"]["ROWS_SEPARATELY"] == AP(0.388, abs=1e-9)
    assert g["blinding"]["OUTLINE_AT_DEEPEST_DEPTH"] == AP(0.348, abs=1e-9)
    assert g["deepest_tag"] == "FA"
    by, ch, logs, ident, _ = run()
    f, b = by["FTG:K-OUT-7"], by["BLD:K-OUT-7"]
    for ln, lo, hi in ((f, 1.808, 1.872), (b, 0.348, 0.388)):
        assert ln["evidence_state"] == "BOUNDED_EXPOSURE" and ln["measured_net"] is None
        assert (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) == (AP(lo), AP(hi))
        rec = ln["calculation"]["inputs"]["multi_tag_outline_v3011"]
        assert rec["status"] == "CONFLICT" and rec["evidence_status"] == "HELD"
        assert set(rec["readings"]) == set(A.READINGS)
    assert ident["replaced"] == 2 and ident["added"] == 0 and ident["outside_rows"] == 4
    log = logs[0]
    assert log["totals"] == {"footing": [AP(1.808), AP(1.872)], "blinding": [AP(0.348), AP(0.388)]}
    assert log["released_moved"] == {"footing": AP(-1.584), "blinding": AP(0.0)}
    assert all(c["evidence_status"] == "HELD" for c in ch)


def test_provisional_view_is_information_only_and_blinding_follows_the_footing_reading():
    by, *_ = run()
    f = by["FTG:K-OUT-7"]["calculation"]["inputs"]["multi_tag_outline_v3011"]["provisional_view"]
    b = by["BLD:K-OUT-7"]["calculation"]["inputs"]["multi_tag_outline_v3011"]["provisional_view"]
    assert (f["reading"], f["value"]) == ("OUTLINE_AT_DEEPEST_DEPTH", AP(1.872))
    assert (b["reading"], b["value"]) == ("OUTLINE_AT_DEEPEST_DEPTH", AP(0.348))   # NOT the larger 0.388
    for ln in (by["FTG:K-OUT-7"], by["BLD:K-OUT-7"]):
        assert ln["measured_net"] is None
    tot = BL.totals(list(by.values()), by=("item_code",))
    assert tot[(FOOT,)]["m3"]["net"] == AP(0.900)          # only the other footing is released; the view is not


def test_unrelated_lines_byte_identical():
    by, _, _, ident, lines = run()
    old = {ln["location"]["element_id"]: ln for ln in lines}
    for eid in ("FTG:K-OUT-1", "BLD:FOOTINGS", "P-C:BEAMS:GF:B1", "P-C:COLS:GF:C1"):
        assert A30.line_sha(by[eid]) == A30.line_sha(old[eid])
    assert ident["outside_rows_identical_to_v3_0_10"] == 4


def test_rotated_outline_and_swapped_tags_give_the_same_readings():
    r = record(drawn={"a": 1.20, "b": 2.60, "area": 3.12, "rectangular": True, "source": "outline (rotated)"},
               tags=["FB", "FA"])
    by, *_ = run(inputs(r))
    assert by["FTG:K-OUT-7"]["bounded_range"]["low"] == AP(1.808)
    assert by["BLD:K-OUT-7"]["bounded_range"]["high"] == AP(0.388)


def test_line_id_kept_and_old_figure_kept_as_information():
    by, _, _, _, lines = run()
    old = {ln["location"]["element_id"]: ln for ln in lines}
    assert by["FTG:K-OUT-7"]["line_id"] == old["FTG:K-OUT-7"]["line_id"]
    info = by["FTG:K-OUT-7"]["calculation"]["inputs"]["multi_tag_outline_v3011"]["info_qty_v3_0_10"]
    assert info["value"] == AP(1.584) and info["state"] == "PROVISIONAL"


def test_no_inputs_changes_nothing():
    lines = l3010()
    ch, logs = A.changes_for(None, lines)
    assert ch == [] and logs[0]["state"] == "NO_PROJECT_INPUT"
    out, ident = A.integrate(lines, ch)
    assert [A30.line_sha(x) for x in out] == [A30.line_sha(x) for x in lines]


# ------------------------------------------------------------------------------------------------ adverse
def test_one_tag_picked_is_refused():
    with pytest.raises(A.InputsError, match="two or more distinct tags"):
        A.load_inputs(inputs(record(tags=["FA"], schedule={"FA": record()["schedule"]["FA"]})), PID)
    r = record()
    r["footing"] = dict(r["footing"], readings={"ROWS_SEPARATELY": 1.808})
    with pytest.raises(A.InputsError, match="single reading"):
        A.load_inputs(inputs(r), PID)


def test_range_that_excludes_a_reading_is_refused():
    r = record()
    r["footing"] = dict(r["footing"], range=[1.584, 1.808])         # the candidate's old low: excludes 1.872
    with pytest.raises(A.InputsError, match="excludes a reading"):
        A.load_inputs(inputs(r), PID)
    r = record()
    r["footing"] = dict(r["footing"], range=[1.5, 1.9])            # wider than the readings: adds a figure
    with pytest.raises(A.InputsError, match="smallest / largest"):
        A.load_inputs(inputs(r), PID)


def test_stated_reading_must_be_the_recomputed_one():
    r = record()
    r["footing"] = dict(r["footing"], readings={"ROWS_SEPARATELY": 1.584, "OUTLINE_AT_DEEPEST_DEPTH": 1.872})
    with pytest.raises(A.InputsError, match="recomputed"):
        A.load_inputs(inputs(r), PID)


def test_outline_at_the_shallower_depth_is_not_a_reading():
    r = record()
    r["footing"] = dict(r["footing"], readings={"ROWS_SEPARATELY": 1.808, "OUTLINE_AT_DEEPEST_DEPTH": 3.12 * 0.40})
    with pytest.raises(A.InputsError, match="recomputed"):
        A.load_inputs(inputs(r), PID)


def test_blinding_of_a_held_footing_released_is_refused():
    r = record()
    r["blinding_line"] = dict(r["blinding_line"], state="RELEASED")
    with pytest.raises(A.InputsError, match="blinding of a held footing is never released"):
        A.load_inputs(inputs(r), PID)


def test_footing_released_on_one_reading_is_refused():
    r = record()
    r["footing"] = dict(r["footing"], state="RELEASED")
    with pytest.raises(A.InputsError, match="never released on one reading"):
        A.load_inputs(inputs(r), PID)


def test_provisional_view_must_be_the_bigger_footing_reading():
    with pytest.raises(A.InputsError, match="BIGGER"):
        A.load_inputs(inputs(record(provisional_view="ROWS_SEPARATELY")), PID)


def test_millimetres_given_as_metres_are_refused():
    r = record(drawn={"a": 2600, "b": 1200, "area": 3120000, "rectangular": True, "source": "outline"})
    with pytest.raises(A.InputsError, match="unit slip"):
        A.load_inputs(inputs(r), PID)


def test_missing_depth_or_row_is_refused_never_zero():
    r = record()
    r["schedule"] = dict(r["schedule"], FB={"L": 0.80, "W": 0.70, "H": None, "source": "row FB"})
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(inputs(r), PID)
    r = record()
    r["schedule"] = {"FA": r["schedule"]["FA"]}
    with pytest.raises(A.InputsError, match="schedule row"):
        A.load_inputs(inputs(r), PID)


def test_area_that_is_not_the_sides_is_refused():
    r = record(drawn={"a": 2.60, "b": 1.20, "area": 3.40, "rectangular": True, "source": "outline"})
    with pytest.raises(A.InputsError, match="rectangular outline"):
        A.load_inputs(inputs(r), PID)
    r = record(drawn={"a": 2.60, "b": 1.20, "area": 3.12, "source": "outline"})
    with pytest.raises(A.InputsError, match="rectangular"):
        A.load_inputs(inputs(r), PID)


def test_carried_figure_must_be_the_lines():
    r = record()
    r["footing"] = dict(r["footing"], carried=1.960)
    with pytest.raises(A.InputsError, match="carries"):
        run(inputs(r))


def test_line_the_candidate_lacks_is_refused():
    r = record()
    r["blinding_line"] = dict(r["blinding_line"], element_id="BLD:NOWHERE")
    with pytest.raises(A.InputsError, match="found 0 time"):
        run(inputs(r))


def test_earlier_changed_line_needs_its_earlier_change_named():
    lines = l3010()
    fid = lines[0]["line_id"]
    with pytest.raises(A.InputsError, match="earlier candidate version"):
        run(lines=lines, earlier={fid})
    r = record()
    r["footing"] = dict(r["footing"], earlier_change="V3.0.x set it PROVISIONAL on FA alone")
    by, *_ = run(inputs(r), lines=l3010(), earlier={fid})
    assert by["FTG:K-OUT-7"]["evidence_state"] == "BOUNDED_EXPOSURE"


def test_declared_range_must_match():
    with pytest.raises(ValueError, match="declared"):
        run(inputs(declared={"footing": [1.808, 1.900]}))


def test_finished_line_with_a_range_off_its_readings_is_refused():
    by, ch, *_ = run()
    bad = copy.deepcopy(by["FTG:K-OUT-7"])
    bad["bounded_range"]["low"] = 1.584
    with pytest.raises(A.InputsError, match="is not its readings"):
        A.check_conflicts([bad])
    bad = copy.deepcopy(by["FTG:K-OUT-7"])
    bad.update(evidence_state="PROVISIONAL", measured_net=1.872, bounded_range=None)
    with pytest.raises(A.InputsError, match="BOUNDED_EXPOSURE"):
        A.check_conflicts([bad])


def test_wrong_schema_or_project_is_refused():
    doc = inputs()
    with pytest.raises(A.InputsError, match="schema"):
        A.load_inputs(dict(doc, schema="URBAN_V3010_INPUTS_V1"), PID)
    with pytest.raises(A.InputsError, match="for"):
        A.load_inputs(dict(doc, project="another"), PID)


def test_piece_without_a_checker_merged_source_is_refused():
    p = inputs()
    p["pieces"][0]["source"] = dict(src(), merge_commit=None)
    with pytest.raises(A.InputsError, match="merge_commit"):
        A.load_inputs(p, PID)


def _with_downstream(eid, why="depends on the outline"):
    lines = l3010()
    dl = next(ln for ln in lines if ln["location"]["element_id"] == eid)
    r = record()
    r["footing"] = dict(r["footing"], downstream=[{"line_id": dl["line_id"], "element_id": eid, "why": why}])
    return r, lines


def test_downstream_held_line_is_named_and_left_as_it_is():
    lines = l3010()
    lines.append(line("FRP:K-OUT-7:ALL", "STR.REBAR", ev="BLOCKED_RFI"))
    dl = lines[-1]
    r = record()
    r["footing"] = dict(r["footing"], downstream=[{"line_id": dl["line_id"], "element_id": "FRP:K-OUT-7:ALL",
                                                   "why": "bars of which type"}])
    by, ch, *_ = run(inputs(r), lines=lines)
    assert A30.line_sha(by["FRP:K-OUT-7:ALL"]) == A30.line_sha(dl)
    assert ch[0]["downstream"][0]["line_id"] == dl["line_id"]


def test_released_downstream_of_a_conflict_is_refused():
    r, lines = _with_downstream("P-C:COLS:GF:C1")              # a live line named as resting on the outline
    with pytest.raises(A.InputsError, match="never released"):
        run(inputs(r), lines=lines)


def test_downstream_entry_without_its_line_is_refused():
    r = record()
    r["footing"] = dict(r["footing"], downstream=["the rebar"])
    with pytest.raises(A.InputsError, match="downstream entry"):
        A.load_inputs(inputs(r), PID)
