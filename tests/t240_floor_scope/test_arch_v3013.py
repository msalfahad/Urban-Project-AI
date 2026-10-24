"""T-240 WP1: ARCH_TAKEOFF_V3.0.13, the SAME opt-in candidate as V3.0 .. V3.0.12 extended (engine.source.arch_v3013):
one strip / face, one line, by its physical class. Synthetic data only (no client drawing).

VILLA K-240 (not the development villa), hand values:
  dressing K-DR (1F): enclosed between a 4.00 x 3.50 bedroom (open passage OP-021 1.00 wide) and its bath (door
      OP-022); no fixture, drainage plan read: INTERIOR, DRY. Printed 2.10 x 1.40 = 2.940 m2. The candidate carried it as
      an untyped space PROVISIONAL 2.940 (in no floor line). -> enters FLOOR.INTERNAL: +2.940 m2, material HELD.
  lift landing 1F OP-031 1.10 x 0.20 = 0.220 m2 (porcelain strip 0.220 in the candidate) -> ARCH.THRESHOLD HELD 0.220.
  exterior sill 2F OP-041 0.90 x 0.15 = 0.135 m2 (porcelain strip 0.135; a threshold twin already on OP-041, BLOCKED)
      -> the twin becomes the ONE threshold line, HELD 0.135; the porcelain strip retired.
  side passage GF K-SP: drawn 1.30 x 5.00 = 6.500 m2, bound EXTERIOR (owner decision); the candidate carries space
      pieces 2.400 + 3.700 and the mouth strip OP-051 0.260 (porcelain) = 6.360; missing 0.140 named (a band with no
      line) -> one outdoor line 6.500 m2, FLOOR.OUTDOOR; internal key -0.260 (only the porcelain mouth was internal
      floor; the two space pieces were untyped space).
  wall top GF OP-052 0.300 m2 porcelain strip + its threshold twin (BLOCKED): no opening drawn -> both retired.
  Internal floor line: before 30.000 (room) + 0.220 + 0.135 + 0.260 + 0.300 = 30.915; after 30.000 + 2.940 = 32.940
  (delta +2.940 - 0.915 = +2.025 m2). Unrelated lines byte-identical.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30                      # noqa: E402
from engine.source import arch_v3013 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402

AP = pytest.approx
PID = "synthetic-v3013-villa-k240"
DOCS = [{"file": "K-ARCH.dxf", "sha256": "4" * 64}]
POR, SP, THR = "FIN.FLOOR.PORCELAIN", "ARCH.SPACE", "ARCH.THRESHOLD"


def line(eid, item, floor, q=1.0, ev="SOURCE_DERIVED", unit="m2"):
    held = ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit=unit, evidence_state=ev,
                        measured_net=None if held else q, element_id=eid, floor=floor, physical_element=eid,
                        formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if held else None)


def l3012():
    return [line("1F-RBED", POR, "1F", 30.0),
            line("1F-RKDR", SP, "1F", 2.94, "PROVISIONAL"),
            line("1F-STRIP-OP-031", POR, "1F", 0.22),
            line("2F-STRIP-OP-041", POR, "2F", 0.135, "PROVISIONAL"),
            line("2F-THR-OP-041", THR, "2F", ev="BLOCKED_RFI"),
            line("GF-RSPA", SP, "GF", 2.4, "PROVISIONAL"),
            line("GF-RSPB", SP, "GF", 3.7, "PROVISIONAL"),
            line("GF-STRIP-OP-051", POR, "GF", 0.26, "PROVISIONAL"),
            line("GF-STRIP-OP-052", POR, "GF", 0.30, "PROVISIONAL"),
            line("GF-THR-OP-052", THR, "GF", ev="BLOCKED_RFI"),
            line("1F-RBATH", "FIN.FLOOR.WET_TILE", "1F", 4.2),
            line("P-C:BEAMS:GF:B1", "STR.CONC.BEAM", "GF", 1.2, unit="m3")]


def src():
    return {"file": "research/T-FT/LEDGER.csv", "sha256": "f" * 64, "task": "T-FT", "merge_commit": "def5678",
            "checker_run": "verifier run for T-FT"}


def ref(eid, item, floor, carried, why="moves"):
    return {"item_code": item, "floor": floor, "element_id": eid, "unit": "m2", "carried": carried, "why": why}


def records():
    return [
        {"id": "DRESSING", "kind": "ENTER_FLOOR", "floor": "1F", "dims": [[2.10, 1.40]], "area_m2": 2.94,
         "class": "INTERIOR", "wet_dry": "DRY", "area_status": "VERIFIED", "material_status": "HELD",
         "evidence": "enclosed, open passage OP-021 + door OP-022, no fixture, drainage read",
         "drawing_reference": "faces K1..K4", "verified_by": "checker run X",
         "line": ref("1F-RKDR", SP, "1F", 2.94, "untyped space in no floor line")},
        {"id": "LIFT-1F", "kind": "TO_THRESHOLD", "floor": "1F", "opening": "OP-031", "class": "LIFT_LANDING",
         "rule": "UP-DOOR-CLS-005", "dims": [[1.10, 0.20]], "area_m2": 0.22, "evidence": "lift jambs",
         "drawing_reference": "jambs J1 / J2", "line": ref("1F-STRIP-OP-031", POR, "1F", 0.22, "lift landing")},
        {"id": "SILL-2F", "kind": "TO_THRESHOLD", "floor": "2F", "opening": "OP-041", "class": "EXTERIOR_SILL",
         "rule": "UP-THR-001", "dims": [[0.90, 0.15]], "area_m2": 0.135, "evidence": "roof door",
         "drawing_reference": "door D9", "line": ref("2F-STRIP-OP-041", POR, "2F", 0.135, "exterior sill"),
         "twin": ref("2F-THR-OP-041", THR, "2F", None, "the threshold line of the same strip")},
        {"id": "PASSAGE", "kind": "TO_OUTDOOR", "floor": "GF", "dims": [[1.30, 5.00]], "area_m2": 6.5,
         "decision": "owner decision K-67 A", "material_status": "ASSUMED - OWNER-APPROVED",
         "material_source": "owner sides rule", "area_status": "VERIFIED", "evidence": "nothing across the mouth",
         "drawing_reference": "walls W1..W5",
         "lines": [ref("GF-RSPA", SP, "GF", 2.4), ref("GF-RSPB", SP, "GF", 3.7),
                   ref("GF-STRIP-OP-051", POR, "GF", 0.26)],
         "missing": {"m2": 0.14, "why": "the band under the beam has no line on any layer"}},
        {"id": "WALLTOP", "kind": "NO_FLOOR", "floor": "GF", "evidence": "boundary wall runs the full width",
         "drawing_reference": "wall lines B1 / B2",
         "line": ref("GF-STRIP-OP-052", POR, "GF", 0.30, "top of a solid wall"),
         "twin": ref("GF-THR-OP-052", THR, "GF", None, "the twin of a strip that is no opening")}]


def inputs(recs=None, declared=None):
    pc = {"piece": "FLOOR_SCOPE", "source": src(), "records": recs if recs is not None else records()}
    if declared is not None:
        pc["declared"] = declared
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "pieces": [pc]}


def run(recs=None, lines=None, declared=None):
    ls = lines if lines is not None else l3012()
    inp = A.load_inputs(inputs(recs, declared), PID)
    ch, logs = A.changes_for(inp, ls)
    out, ident = A.integrate(ls, ch)
    return ls, out, ch, logs, ident


def by_eid(lines):
    return {(ln["location"]["element_id"], ln["item_code"]): ln for ln in lines}


# ------------------------------------------------------------------------------------------------ normal case
def test_hand_values_and_floor_line():
    ls, out, ch, logs, ident = run(declared={"floor_internal_in_m2": 2.94, "floor_internal_out_m2": 0.915,
                                             "threshold_m2": 0.355, "outdoor_m2": 6.5})
    b = by_eid(out)
    d = b[("1F-RKDR", SP)]
    assert d["evidence_state"] == "SOURCE_DERIVED" and d["measured_net"] == AP(2.94)
    sc = d["calculation"]["inputs"]["floor_scope_v3013"]
    assert sc["floor_key"] == "FLOOR.INTERNAL" and sc["material_status"] == "HELD" and sc["wet_dry"] == "DRY"
    for e in ("1F-STRIP-OP-031", "2F-STRIP-OP-041", "GF-STRIP-OP-051", "GF-STRIP-OP-052"):
        assert b[(e, POR)]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    t1 = b[("HL:FLOOR_SCOPE:THRESHOLD:1F:OP-031", THR)]
    assert t1["evidence_state"] == "BOUNDED_EXPOSURE" and t1["bounded_range"]["low"] == AP(0.22) \
        and t1["bounded_range"]["high"] == AP(0.22)
    t2 = b[("2F-THR-OP-041", THR)]   # the twin replaced in place: ONE threshold line, never a second
    assert t2["evidence_state"] == "BOUNDED_EXPOSURE" and t2["bounded_range"]["high"] == AP(0.135)
    assert not any(k[0].startswith("HL:FLOOR_SCOPE:THRESHOLD:2F") for k in b)
    assert b[("GF-THR-OP-052", THR)]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    od = b[("HL:FLOOR_SCOPE:OUTDOOR:GF:PASSAGE", SP)]
    assert od["measured_net"] == AP(6.5)
    assert od["calculation"]["inputs"]["floor_scope_v3013"]["floor_key"] == "FLOOR.OUTDOOR"
    f12, f13 = A.floor_line(ls), A.floor_line(out)
    assert f12["internal"]["total"] == AP(30.0 + 0.22 + 0.135 + 0.26 + 0.30 + 4.2)
    assert f13["internal"]["total"] == AP(30.0 + 2.94 + 4.2)
    assert f13["outdoor"]["total"] == AP(6.5) and f13["threshold_held"]["total"] == AP(0.355)
    assert f13["internal"]["total"] - f12["internal"]["total"] == AP(2.025)
    assert logs[0]["totals"]["floor_internal_delta_m2"] == AP(2.025)
    assert ident["replaced"] == 9 and ident["added"] == 2 and ident["outside_rows"] == 3
    chk = A.check_one_strip_one_line(out, {c["after"]["line_id"] for c in ch})
    assert chk == {"strips": 2, "pre_existing_duplicates": []}   # OP-031, OP-041 by their threshold lines only
    assert A.check_one_strip_one_line(ls)["strips"] == 4         # V3.0.12: four porcelain strips (twins named apart)



def test_unrelated_lines_byte_identical_and_retired_figures_kept():
    ls, out, ch, _l, _i = run()
    b12 = {ln["line_id"]: ln for ln in ls}
    for ln in out:
        if ln["location"]["element_id"] in ("1F-RBED", "1F-RBATH", "P-C:BEAMS:GF:B1"):
            assert A30.line_sha(ln) == A30.line_sha(b12[ln["line_id"]])
    for c in ch:
        if c["after"]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            assert "never summed" in c["after"]["notes"] and c["before"] is not None


def test_ledger_and_diff_rows():
    ls, out, ch, _l, _i = run()
    rows = A.ledger_rows(ch, released_lines=ls)
    assert {r["action"] for r in rows} == {"REPLACE", "ADD"}
    assert all(r["release_status"] == "NOT RELEASED" for r in rows)
    held = [r for r in rows if r["item_code"] == THR and r["evidence_status"] == "HELD"]
    assert len(held) == 2
    diff = A.diff_rows(ls, out, ls)
    assert sum(1 for d in diff if d["vs_v3_0_12"] == "ADDED") == 2
    assert sum(1 for d in diff if d["vs_v3_0_12"] == "SAME") == 3


def test_added_lines_carry_their_guard_element():
    """the V3.0.7 guard re-check maps every added line to a register element (arch_v307._carried_map)."""
    _ls, _out, ch, _l, _i = run()
    adds = [c for c in ch if c["action"] == "ADD"]
    assert len(adds) == 2
    for c in adds:
        assert c["guard_element"] == {"element_id": c["after"]["location"]["element_id"], "part": "WHOLE"}


def test_write_files(tmp_path):
    ls = l3012()
    inp = A.load_inputs(inputs(), PID)
    ch, logs = A.changes_for(inp, ls)
    names, ident, led = A.write(tmp_path, ls, ch, logs, inp, ls)
    assert "V3_0_13_BOQ_LINES.json" in names and (tmp_path / "V3_0_13_DIFF.csv").exists()
    assert led["integration_package"] is False and ident["opening_strips"] == 2   # the two thresholds


def test_no_inputs_changes_nothing():
    ls = l3012()
    ch, logs = A.changes_for(None, ls)
    assert ch == [] and logs[0]["state"] == "NO_PROJECT_INPUT"
    out, ident = A.integrate(ls, ch)
    assert [A30.line_sha(x) for x in out] == [A30.line_sha(x) for x in ls]


# ------------------------------------------------------------------------------------------------ adverse cases
def _with(i, **kw):
    r = records()
    r[i] = dict(r[i], **kw)
    return r


@pytest.mark.parametrize("recs, msg", [
    (_with(0, **{"class": "SHAFT"}), "only an INTERIOR face"),                     # a shaft never enters
    (_with(0, wet_dry="HELD"), "wet / dry class"),                                  # class not settled
    (_with(0, material_status="DRAWING-CONFIRMED"), "names its source"),           # material without a source
    (_with(0, material_status="DRAWING-CONFIRMED", material_source="bed room", material_from_neighbour=True),
     "borrowed from the neighbouring room"),                                         # D-C3
    (_with(0, area_m2=3.10), "recomputed from its printed dimensions"),              # stated area off the print
    (_with(0, dims=[[2100, 1400]], area_m2=2940000.0), "unit slip"),                 # millimetres as metres
    (_with(0, dims=[[2.10, 0]]), "missing is never 0"),
    (_with(1, release=True), "never released"),                                       # held threshold released
    (_with(1, opening="lift"), "OP-nnn"),
    (_with(1, **{"class": "DOORWAY"}), "threshold class"),
    (_with(3, decision=None), "binding decision"),                                   # unbound exterior stays put
    (_with(3, missing={"m2": 0.14}), "names why"),                                    # missing piece unnamed
    (_with(3, missing=None), "every difference is named"),                            # silent 0.140
])
def test_inputs_refused(recs, msg):
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(inputs(recs), PID)


def test_line_named_twice_refused():
    r = records()
    r[2] = dict(r[2], line=ref("1F-STRIP-OP-031", POR, "1F", 0.22))
    with pytest.raises(A.InputsError, match="named by two records"):
        A.load_inputs(inputs(r), PID)


def test_carried_figure_must_match():
    with pytest.raises(A.InputsError, match="carries"):
        run(_with(1, line=ref("1F-STRIP-OP-031", POR, "1F", 0.25)))


def test_line_not_found_refused():
    with pytest.raises(A.InputsError, match="found 0 time"):
        run(_with(1, line=ref("1F-STRIP-OP-999", POR, "1F", 0.22)))


def test_sill_in_floor_and_threshold_refused():
    """a strip carried by a live floor line AND a threshold line is refused (one strip, one line)."""
    ls, out, *_ = run()
    bad = copy.deepcopy(out)
    for ln in bad:
        if ln["location"]["element_id"] == "1F-STRIP-OP-031":
            ln.update(evidence_state="SOURCE_DERIVED", measured_net=0.22)
    with pytest.raises(A.InputsError, match="one strip, one line"):
        A.check_one_strip_one_line(bad)


def test_untouched_duplicate_is_named_not_hidden():
    """a strip carried twice that this version does not touch (a wall-top strip with its twin, left for a later
    package) is returned as a named finding; the same pair touched by this version is refused."""
    ls = l3012()
    for ln in ls:
        if ln["location"]["element_id"] == "GF-THR-OP-052":
            ln["location"]["element_id"] = "GF-STRIP-OP-052:unattributed strip"
    recs = [r for r in records() if r["id"] != "WALLTOP"]
    _ls, out, ch, _l, _i = run(recs, lines=ls)
    chk = A.check_one_strip_one_line(out, {c["after"]["line_id"] for c in ch})
    assert [(d["floor"], d["opening"]) for d in chk["pre_existing_duplicates"]] == [("GF", "OP-052")]


def test_threshold_released_or_zero_refused():
    ls, out, *_ = run()
    for mutate in ({"evidence_state": "SOURCE_DERIVED", "measured_net": 0.22, "bounded_range": None},
                   {"bounded_range": {"low": 0.0, "high": 0.0, "basis": "x"}}):
        bad = copy.deepcopy(out)
        for ln in bad:
            if ln["location"]["element_id"] == "HL:FLOOR_SCOPE:THRESHOLD:1F:OP-031":
                ln.update(**mutate)
        with pytest.raises(A.InputsError, match="HELD with its area"):
            A.check_floor_scope(bad)


def test_outdoor_never_internal():
    ls, out, *_ = run()
    bad = copy.deepcopy(out)
    for ln in bad:
        sc = ln["calculation"]["inputs"].get("floor_scope_v3013")
        if isinstance(sc, dict) and sc.get("kind") == "TO_OUTDOOR":
            sc["floor_key"] = "FLOOR.INTERNAL"
    with pytest.raises(A.InputsError, match="never in the internal floor line"):
        A.check_floor_scope(bad)


def test_declared_total_mismatch_refused():
    with pytest.raises(ValueError, match="declared"):
        run(declared={"threshold_m2": 0.550})


def test_earlier_change_needs_naming():
    ls = l3012()
    lid = next(ln["line_id"] for ln in ls if ln["location"]["element_id"] == "1F-STRIP-OP-031")
    inp = A.load_inputs(inputs(), PID)
    with pytest.raises(A.InputsError, match="earlier candidate version"):
        A.changes_for(inp, ls, {lid})


def test_wrong_schema_and_project_refused():
    with pytest.raises(A.InputsError, match="schema"):
        A.load_inputs(dict(inputs(), schema="X"), PID)
    with pytest.raises(A.InputsError, match="project inputs are for"):
        A.load_inputs(inputs(), "another-project")


def test_policy_record_not_default():
    p = A.policy_record()
    assert p["released_default"] is False and p["extends"] == "ARCH_TAKEOFF_V3.0.12"
