"""T-507: ARCH_TAKEOFF_V3.0.58 (B8-06 exposed-slab roof waterproofing lines) on the hand-calculated NON-Alsenan villa
R507 (own figures, no drawing).

  COURT-300 (1F slab top round a court void, open to the sky, no door -> B8-06 roof):
      slab 4.00 x 4.00 = 16.000 - void 2.00 x 1.50 = 3.000 - pier 1.00 x 1.00 = 1.000 -> membrane 12.000 m2;
      upturn runs: house wall 4.000 + parapet 4.000 + pier faces 2.000 = 10.000 lm x 0.20 = 2.000 m2 (MEASURED);
      under window W1 1.000 lm, sill height not read -> its own line HELD 0 .. 1.000 lm (never summed);
      slab edge 4.000 lm and void edge 7.000 lm terminations, drainage RFI: named beside the membrane line.
  COURT-300-LEDGE (0.30 m ledge under the floor above, open at the void side: COVERED_OPEN_SIDE):
      membrane 1.500 m2 -> HELD 0 .. 1.500 m2; bay wall 3.000 lm -> HELD 0 .. 3.000 lm; slab edge 0 by evidence;
      void edge 3.000 lm beside.
  Candidate roofs: R1 50.000 m2 valued + its upturn 30.000 lm; R2 HELD blank (both FIN.WP.ROOF lines in the overlap
  census at 0.000 m2). Totals: FIN.WP.ROOF 50.000 -> 62.000 m2 (+12.000), held range 0 .. 1.500 beside;
  FIN.WP.ROOF_UPTURN 30.000 -> 40.000 lm (+10.000), held 0 .. 4.000 beside.
Adverse: an unmeasured edge (HELD item 'length not measured', never no item), an edge not stated, an edge 0 with no
evidence, an area not measured (BLANK line, never 0), a door (B8-07) refused, an access-unknown zone refused, a non-zero
overlap refused, a roof line missing from the census, stale rows, VERIFIED as an input, mm, applied twice, a total
moved outside the codes, the totals view of an all-blank / bounded-only code (HELD, never 0.0), run order / mirrored
runs give the same lines.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3058 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402
from engine.source import wp_applicability_rules_v1 as W  # noqa: E402

PID, REV = "R507-SYNTHETIC", "e" * 64


def _ln(code, eid, state, net=None, rng=None, unit="m2", floor="1F"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, bounded_range=rng, element_id=eid, floor=floor,
                        formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                        geometry_source="SYNTHETIC_FIXTURE", material_state="SOURCE",
                        rfi={"question": "roof not drawn", "unlocks": eid} if state == "BLOCKED_RFI" else None,
                        notes="synthetic", **({} if code in BL.ITEMS else
                                              {"item_en": "roof membrane", "item_ar": "عازل", "trade": "WATERPROOFING"}))


LINES = [
    _ln("FIN.WP.ROOF", "1F-R1:wp_membrane", "SOURCE_DERIVED", 50.0),
    _ln("FIN.WP.ROOF_UPTURN", "1F-R1:wp_upturn", "SOURCE_DERIVED", 30.0, unit="lm"),
    _ln("FIN.WP.ROOF", "2F-R2:wp_membrane", "BLOCKED_RFI", floor="2F"),
    _ln("FIN.WP.TERMINATION", "1F-B1:termination", "BOUNDED_EXPOSURE", rng={"low": 0.0, "high": 0.6, "basis": "w"},
        unit="lm"),
]
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LINES}


def _src(t):
    return {"task": t, "file": f"research/r507/{t}.json", "sha256": "a" * 64, "merge_commit": "d" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def court(**kw):
    g = {"zone_id": "COURT-300", "exposure": W.EXPOSED, "doors": 0, "membrane_m2": 12.0,
         "upturn_runs": [{"run": "house_wall", "lm": 4.0, "kind": "WALL"},
                         {"run": "parapet", "lm": 4.0, "kind": "PARAPET"},
                         {"run": "pier", "lm": 2.0, "kind": "SOLID"},
                         {"run": "window_W1", "lm": 1.0, "kind": "UNDER_WINDOW", "sill_above_slab_m": None}],
         "doorways": [], "open_edge_lm": 4.0, "void_edge_lm": 7.0, "carried": [], "outlet_printed": False,
         "evidence": {"FLAT_MEMBRANE": ["4.00 x 4.00 - void 2.00 x 1.50 - pier 1.00 x 1.00"]}}
    g.update(kw)
    return g


def ledge(**kw):
    g = {"zone_id": "COURT-300-LEDGE", "exposure": W.COVERED_OPEN_SIDE, "doors": 0, "membrane_m2": 1.5,
         "upturn_runs": [{"run": "bay_wall", "lm": 3.0, "kind": "WALL"}], "open_edge_lm": 0.0, "void_edge_lm": 3.0,
         "carried": [], "outlet_printed": False,
         "evidence": {"SLAB_EDGE_TERMINATION": ["the ledge runs wall to void: no slab edge"]}}
    g.update(kw)
    return g


def zone(g, floor="1F"):
    return {"zone_id": g["zone_id"], "floor": floor, "geometry": g, "expected_rows": W.component_rows(g),
            "source_tasks": ["T-P"], "evidence_status": "DRAWING-CONFIRMED", "basis": "own hand measure"}


def overlap(ids=None):
    return [{"line_id": i, "overlap_m2": 0.0, "evidence": "another slab"}
            for i in (ids or [ID["1F-R1:wp_membrane"], ID["2F-R2:wp_membrane"]])]


def doc(zones=None, ov=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-P")],
            "template_line": ID["1F-R1:wp_membrane"], "zones": zones or [zone(court()), zone(ledge())],
            "overlap": ov or overlap()}


def run(d=None, prev=None):
    prev = prev or copy.deepcopy(LINES)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _by(lines, eid):
    return next(x for x in lines if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------- normal case
def test_hand_values():
    prev, ch, log = run()
    out, ident = A.integrate(prev, ch)
    m = _by(out, "1F-COURT-300:wp_membrane")
    assert m["item_code"] == "FIN.WP.ROOF" and m["unit"] == "m2" and m["evidence_state"] == "SOURCE_DERIVED"
    assert m["measured_net"] == 12.0 and m["subtrade"] == "B8-06"
    u = _by(out, "1F-COURT-300:wp_upturn")
    assert u["unit"] == "lm" and u["measured_net"] == 10.0
    rec = u["calculation"]["inputs"][A.REC_KEY]
    assert rec["upturn_m2_at_0_20"] == 2.0 and rec["height_m"] == 0.20
    w = _by(out, "1F-COURT-300:wp_upturn window_W1")
    assert w["evidence_state"] == "BOUNDED_EXPOSURE" and w["measured_net"] is None
    assert w["bounded_range"]["low"] == 0.0 and w["bounded_range"]["high"] == 1.0
    lm = _by(out, "1F-COURT-300-LEDGE:wp_membrane")
    assert lm["evidence_state"] == "BOUNDED_EXPOSURE" and lm["bounded_range"]["high"] == 1.5
    lu = _by(out, "1F-COURT-300-LEDGE:wp_upturn")
    assert lu["evidence_state"] == "BOUNDED_EXPOSURE" and lu["bounded_range"]["high"] == 3.0
    assert ident["added"] == 5 and ident["replaced"] == 0 and ident["outside_rows_identical_to_base"] == 4
    ex = ident["exposed_slab_wp"]
    assert ex["valued"] == {"FIN.WP.ROOF_UPTURN|lm": 10.0, "FIN.WP.ROOF|m2": 12.0}
    assert ex["bounded"] == {"FIN.WP.ROOF_UPTURN|lm": 4.0, "FIN.WP.ROOF|m2": 1.5} and ex["blank"] == 0


def test_beside_items_named_never_quantities():
    prev, ch, _ = run()
    out, _ = A.integrate(prev, ch)
    b = _by(out, "1F-COURT-300:wp_membrane")["calculation"]["inputs"][A.REC_KEY]["held_beside"]
    got = {(x["what"], x["bound"], x["status"]) for x in b}
    assert got == {("SLAB_EDGE_TERMINATION", 4.0, "HELD"), ("VOID_EDGE_TERMINATION", 7.0, "HELD"),
                   ("DRAINAGE_FALLS", None, "RFI")}
    lb = _by(out, "1F-COURT-300-LEDGE:wp_membrane")["calculation"]["inputs"][A.REC_KEY]["held_beside"]
    assert [(x["what"], x["bound"]) for x in lb] == [("VOID_EDGE_TERMINATION", 3.0)]   # slab edge 0 by evidence
    assert "beside, HELD, never in the quantity" in _by(out, "1F-COURT-300:wp_membrane")["calculation"]["formula"]


def test_totals_move_only_roof_codes():
    prev, ch, _ = run()
    out, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(out)
    moved = A.check_totals(t0, t1)
    assert set(moved) == {"FIN.WP.ROOF|m2", "FIN.WP.ROOF_UPTURN|lm"}
    assert t0["FIN.WP.ROOF|m2"]["released"] == 50.0 and t1["FIN.WP.ROOF|m2"]["released"] == 62.0
    assert t1["FIN.WP.ROOF|m2"]["held_high"] == 1.5
    assert t1["FIN.WP.ROOF_UPTURN|lm"]["released"] == 40.0 and t1["FIN.WP.ROOF_UPTURN|lm"]["held_high"] == 4.0
    v = moved["FIN.WP.ROOF|m2"]["view_v3_0_58"]
    assert v["status"] == "PARTIAL" and v["text"].startswith("AT_LEAST 62.0 + HELD (2 lines: 1 bounded, 1 blank)")
    for ln in prev:                                      # every candidate line byte-identical
        assert A30.line_sha(ln) == A30.line_sha(_by(out, ln["location"]["element_id"]))


def test_write_files_and_view(tmp_path):
    prev, ch, log = run()
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_58_RUN.json" in names and len(led["rows"]) == 5
    r = json.loads((tmp_path / "V3_0_58_RUN.json").read_text(encoding="utf-8"))
    view = r["code_totals_view"]
    assert view["FIN.WP.TERMINATION|lm"]["text"] == "HELD range 0.0..0.6 (1 bounded lines)"
    assert all(not v["text"].replace(".", "").isdigit() for v in view.values() if v["valued_lines"] == 0)
    assert r["codes_held_no_valued_line"] == ["FIN.WP.TERMINATION|lm"]
    assert ident["diff"]["vs_base"] == {"ADDED": 5, "SAME": 4}


def test_view_all_blank_code_prints_held_never_zero():
    e = {"lines": 3, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 3}
    assert A.total_view(e)["text"] == "HELD (3 blank lines)" and A.total_view(e)["released"] is None
    b = {"lines": 2, "released": 0.0, "held_low": 0.2, "held_high": 1.4, "bounded_lines": 2, "blocked_lines": 0}
    assert A.total_view(b) == dict(A.total_view(b), status="HELD_BOUNDED", held_range=[0.2, 1.4])
    z = {"lines": 1, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 0}
    assert A.total_view(z)["text"] == "0.0"            # a measured 0.0 stays a quantity


def test_run_order_and_mirror_invariance():
    g = court(upturn_runs=list(reversed(court()["upturn_runs"])))
    prev, ch, _ = run(doc([zone(g), zone(ledge())]))
    a = {c["after"]["location"]["element_id"]: A30._qty(c["after"]) for c in ch}
    prev, ch2, _ = run()
    b = {c["after"]["location"]["element_id"]: A30._qty(c["after"]) for c in ch2}
    assert a == b


def test_no_guard_block_logs_no_project_input():
    _, _, log = run()
    assert log["default_guard"] == {"piece": "DEFAULT_GUARD", "state": "NO_PROJECT_INPUT"}


# ------------------------------------------------------------------------------------------------- adverse cases
def test_unmeasured_edge_gives_held_item_never_no_item():
    _, ch, _ = run(doc([zone(court(void_edge_lm=None)), zone(ledge())]))
    b = next(c["after"] for c in ch if c["after"]["location"]["element_id"] == "1F-COURT-300:wp_membrane")
    items = b["calculation"]["inputs"][A.REC_KEY]["held_beside"]
    v = [x for x in items if x["what"] == "VOID_EDGE_TERMINATION"]
    assert len(v) == 1 and v[0]["bound"] is None and v[0]["why"] == "length not measured"


def test_edge_not_stated_or_zero_without_evidence_refused():
    g = court()
    del g["open_edge_lm"]
    with pytest.raises(A.InputsError, match="not stated"):
        run(doc([zone(g)]))
    with pytest.raises(A.InputsError, match="missing is never 0"):
        run(doc([zone(court(open_edge_lm=0.0))]))


def test_area_not_measured_is_blank_line_never_zero():
    _, ch, _ = run(doc([zone(court(membrane_m2=None)), zone(ledge())]))
    m = next(c["after"] for c in ch if c["after"]["location"]["element_id"] == "1F-COURT-300:wp_membrane")
    assert m["evidence_state"] == "BLOCKED_RFI" and m["measured_net"] is None and not m.get("bounded_range")
    assert "area not measured" in m["rfi"]["question"]


def test_door_or_unknown_access_refused():
    with pytest.raises(A.InputsError, match="B8-07"):
        run(doc([zone(court(doors=1))]))
    with pytest.raises(A.InputsError, match="B8-06 roof zones only"):
        run(doc([zone(court(doors=None))]))


def test_overlap_and_census_refused():
    ov = overlap()
    ov[0]["overlap_m2"] = 0.4
    with pytest.raises(A.InputsError, match="ONCE"):
        run(doc(ov=ov))
    with pytest.raises(A.InputsError, match="every roof line"):
        run(doc(ov=overlap([ID["1F-R1:wp_membrane"]])))


def test_stale_rows_verified_mm_refused():
    z = zone(court())
    z["expected_rows"][0]["qty"] = 12.5
    with pytest.raises(A.InputsError, match="stale"):
        run(doc([z]))
    z = zone(court())
    z["evidence_status"] = "VERIFIED"
    with pytest.raises(A.InputsError, match="Checker"):
        run(doc([z]))
    with pytest.raises(A.InputsError, match="mm"):
        run(doc([zone(court(membrane_m2=12000.0))]))


def test_applied_twice_refused():
    prev, ch, _ = run()
    out, _ = A.integrate(prev, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_total_outside_codes_refused():
    t0 = {"FIN.WP.FLOOR|m2": {"lines": 1, "released": 1.0}}
    t1 = {"FIN.WP.FLOOR|m2": {"lines": 1, "released": 2.0}}
    with pytest.raises(ValueError, match="outside"):
        A.check_totals(t0, t1)


def test_added_line_on_other_code_refused():
    prev, ch, _ = run()
    bad = copy.deepcopy(ch[0])
    bad["after"]["item_code"] = "FIN.WP.FLOOR"
    with pytest.raises(ValueError, match="not a change"):
        A.integrate(prev, [bad])
