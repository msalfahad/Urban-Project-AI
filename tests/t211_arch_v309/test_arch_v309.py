"""T-211: ARCH_TAKEOFF_V3.0.9, the SAME opt-in candidate as V3.0 .. V3.0.8 extended (engine.source.arch_v309), on
synthetic data only (no client drawing).

VILLA W (not the development villa). Owner heights GF 3.65, 1F 3.35 (Q-43 / Q-48 A); door head 2.20 (Q-55 C).
Hand values:
  room A (GF, dry): face 16.00 m x 3.65 = 58.40 m2; door 0.90 x 2.20 = 1.98; window 1.20 wide, sill 1.00, head 2.20 ->
    1.20 x 1.20 = 1.44; net 58.40 - 1.98 - 1.44 = 54.98 m2 (RELEASED, checker re-measured -> VERIFIED, the owner
    heights stay ASSUMED - OWNER-APPROVED on the line);
  room B (1F, dry): face 12.00 m x 3.35 = 40.20 m2; door 1.00 x 2.20 = 2.20; window 1.50 wide, head not printed ->
    held 0 .. 1.50 x 3.35 = 5.025; net 40.20 - 2.20 - 5.025 = 32.975 .. 38.00 m2 (BOUNDED, HELD);
  room C (GF annex): owner height not established -> UNQUANTIFIED, HELD (never 0);
  wet room D (GF): its route plaster line (PROVISIONAL 20.00) is outside the scope and stays byte-identical;
  a door jamb / head plaster line (no room) stays byte-identical.
The candidate (route) carries room A / B / C plaster and paint as held lines without a figure.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v309 as A309                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402

A = pytest.approx
PID = "synthetic-v309-villa-w"
DOCS = [{"file": "W-ARCH.dxf", "sha256": "1" * 64}]
CODES = ["FIN.PLASTER", "FIN.PAINT"]
ROOMS = {"A": ("GF", "GF-RA"), "B": ("1F", "1F-RB"), "C": ("GF", "GF-RC")}


def line(eid, item, floor, room=None, q=None, ev="BLOCKED_RFI", pe="plaster"):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit="m2", evidence_state=ev,
                        measured_net=q, element_id=eid, floor=floor, room_id=room, physical_element=pe,
                        formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if ev == "BLOCKED_RFI" else None)


def l308():
    out = []
    for k, (fl, rid) in ROOMS.items():
        for code in CODES:
            out.append(line(f"{rid}:{code.split('.')[-1].lower()}", code, fl, rid))
    out.append(line("GF-RD:plaster", "FIN.PLASTER", "GF", "GF-RD", 20.0, "PROVISIONAL"))
    out.append(line("GF-OPENING-OP-001:door jambs and head", "FIN.PLASTER", "GF", None, 1.06, "PROVISIONAL"))
    out.append(BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="STR.CONC.BEAM", unit="m3",
                            evidence_state="SOURCE_DERIVED", measured_net=1.2, element_id="P-C:BEAMS:1F:B1", floor="1F",
                            physical_element="BEAMS", formula="route", documents=DOCS, rule_id="SV", rule_version="1"))
    return out


def src(task):
    return {"file": f"research/{task}.csv", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task}"}


def rec_a(code, **kw):
    r = {"room": "A", "item_code": code, "floor": "GF", "route_rooms": ["GF-RA"], "state": "RELEASED", "value": 54.98,
         "evidence_status": "VERIFIED", "verified_by": "checker own walk 16.00 m",
         "assumption": "owner height G1 (Q-43 / Q-48 A), door head 2.20 (Q-55 C)",
         "owner_method": {"height_m": 3.65, "face_m": 16.0, "gross": 58.4,
                          "deductions": [{"opening": "door", "m2": 1.98}, {"opening": "window", "m2": 1.44}]},
         "drawing_method": {"gross_m2": "65.4 .. 67.0"},
         "guard_element": {"element_id": "ROOM_FACE:A", "part": code.split(".")[-1]}}
    r.update(kw)
    return r


def rec_b(code, **kw):
    r = {"room": "B", "item_code": code, "floor": "1F", "route_rooms": ["1F-RB"], "state": "BOUNDED",
         "range": [32.975, 38.0], "evidence_status": "HELD", "reasons": ["window head not printed"],
         "owner_method": {"height_m": 3.35, "face_m": 12.0, "gross": 40.2,
                          "deductions": [{"opening": "door", "m2": 2.2}, {"opening": "window", "range": [0, 5.025]}]},
         "drawing_method": {"gross_m2": "45.5 .. 46.7"},
         "guard_element": {"element_id": "ROOM_FACE:B", "part": code.split(".")[-1]}}
    r.update(kw)
    return r


def rec_c(code, **kw):
    r = {"room": "C", "item_code": code, "floor": "GF", "route_rooms": ["GF-RC"], "state": "UNQUANTIFIED",
         "evidence_status": "HELD", "reasons": ["annex owner height not established (G2)"],
         "owner_method": {"height_m": 3.15, "status": "PROVISIONAL"}, "drawing_method": {"gross_m2": "HELD"},
         "guard_element": {"element_id": "ROOM_FACE:C", "part": code.split(".")[-1]}}
    r.update(kw)
    return r


def supersede():
    return [{"element_id": f"{rid}:{c.split('.')[-1].lower()}", "floor": fl, "item_code": c, "carried": A309.NO_FIGURE,
             "why": "the same room face"} for (fl, rid) in ROOMS.values() for c in CODES]


def doc(records=None, sup=None, other=None, unit="m2", declared=True):
    recs = records if records is not None else [f(c) for c in CODES for f in (rec_a, rec_b, rec_c)]
    pc = {"piece": "WALL_FINISH", "item_codes": CODES, "unit": unit, "source": src("T-RF"),
          "sources": [src("T-SH")],
          "scope": {"floors": ["GF", "1F"], "rooms": ["1F-RB", "GF-RA", "GF-RC"],
                    "supersede_lines": sup if sup is not None else supersede(), "other_elements": other or []},
          "records": recs}
    if declared:
        pc["declared_totals"] = {c: {"released": 54.98, "bounded": [32.975, 38.0], "unquantified": 1} for c in CODES}
    return {"schema": A309.INPUTS_SCHEMA, "project": PID, "pieces": [pc]}


def run(d=None, lines=None):
    lines = lines if lines is not None else l308()
    inp = A309.load_inputs(d if d is not None else doc(), PID)
    ch, logs = A309.changes_for(inp, lines)
    out, ident = A309.integrate(lines, ch)
    return lines, out, ident, ch, logs


def by_eid(lines, eid):
    return next(ln for ln in lines if ln["location"]["element_id"] == eid)


# ---------------------------------------------------------------------------------------------------------- normal
def test_normal_room_lines_owner_method_of_record_with_drawing_method_beside():
    before, out, ident, ch, logs = run()
    a = by_eid(out, "HL:WALL_FINISH:A:PLASTER")
    assert a["evidence_state"] == "PROVISIONAL" and a["measured_net"] == A(54.98) and a["unit"] == "m2"
    assert a["gross"] == A(58.4)
    inp = a["calculation"]["inputs"]
    assert inp["evidence_status"] == "VERIFIED" and "ASSUMED" not in inp["evidence_status"]
    assert "Q-43" in inp["assumption"] and inp["drawing_derived_method"] == {"gross_m2": "65.4 .. 67.0"}
    assert inp["owner_net_recomputed"] == [A(54.98), A(54.98)]
    b = by_eid(out, "HL:WALL_FINISH:B:PAINT")
    assert b["evidence_state"] == "BOUNDED_EXPOSURE" and b["measured_net"] is None
    assert (b["bounded_range"]["low"], b["bounded_range"]["high"]) == (A(32.975), A(38.0))
    c = by_eid(out, "HL:WALL_FINISH:C:PLASTER")
    assert c["evidence_state"] == "BLOCKED_RFI" and c["measured_net"] is None and c["bounded_range"] is None
    assert ident["replaced"] == 6 and ident["added"] == 6 and ident["v3_0_9_lines"] == len(before) + 6
    log = logs[0]
    assert log["totals"]["FIN.PLASTER"]["released_added"] == A(54.98)
    assert log["totals"]["FIN.PAINT"]["superseded"]["no_figure_lines"] == 3


def test_normal_superseded_lines_kept_not_applicable_never_deleted():
    before, out, *_ = run()
    for (fl, rid) in ROOMS.values():
        for c in CODES:
            ln = by_eid(out, f"{rid}:{c.split('.')[-1].lower()}")
            assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["measured_net"] is None
            assert "SUPERSEDED" in ln["notes"]


def test_normal_lines_outside_the_scope_byte_identical():
    from engine.source import arch_v30 as A30
    before, out, ident, *_ = run()
    for eid in ("GF-RD:plaster", "GF-OPENING-OP-001:door jambs and head", "P-C:BEAMS:1F:B1"):
        assert A30.line_sha(by_eid(before, eid)) == A30.line_sha(by_eid(out, eid))
    assert ident["outside_rows"] == 3


def test_normal_net_of_bounds():
    assert A309.net_of({"gross": 40.2, "deductions": [{"m2": 2.2}, {"range": [0, 5.025]}]}) == (A(32.975), A(38.0))
    assert A309.net_of({"gross": None}) is None


def test_normal_write_files(tmp_path):
    before, out, ident, ch, logs = run()
    names, ident2, led = A309.write(tmp_path, before, ch, logs, A309.load_inputs(doc(), PID))
    assert "V3_0_9_BOQ_LINES.json" in names and "V3_0_9_DIFF.csv" in names
    assert ident2["diff"]["vs_v3_0_8"] == {"SAME": 3, "CHANGED": 6, "ADDED": 6}
    run_doc = json.loads((tmp_path / "V3_0_9_RUN.json").read_text(encoding="utf-8"))
    assert run_doc["released_default"] is False and "FIN.PLASTER|m2" in run_doc["totals_moved_by_code"]
    assert led["integration_package"] is True and all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


# --------------------------------------------------------------------------------------------------------- adverse
def test_adverse_an_unaccounted_scope_line_is_refused():
    with pytest.raises(A309.InputsError, match="neither superseded"):
        run(doc(sup=supersede()[1:]))


def test_adverse_the_superseded_figure_must_be_the_one_the_line_carries():
    sup = supersede()
    sup[0]["carried"] = 0.0          # a held line with no figure stated as a measured 0
    with pytest.raises(A309.InputsError, match="carries"):
        run(doc(sup=sup))


def test_adverse_a_named_line_the_candidate_does_not_have_is_refused():
    sup = supersede() + [{"element_id": "GF-RX:plaster", "floor": "GF", "item_code": "FIN.PLASTER",
                          "carried": A309.NO_FIGURE, "why": "x"}]
    with pytest.raises(A309.InputsError, match="does not have"):
        run(doc(sup=sup))


def test_adverse_released_value_must_equal_the_recomputed_net():
    recs = [rec_a(c, value=56.42) for c in CODES] + [f(c) for c in CODES for f in (rec_b, rec_c)]
    with pytest.raises(A309.InputsError, match="recomputed"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_face_in_millimetres_is_refused_by_the_recompute():
    om = {"height_m": 3.65, "face_m": 16000.0, "gross": 58400.0, "deductions": [{"m2": 1.98}, {"m2": 1.44}]}
    recs = [rec_a(c, owner_method=om) for c in CODES] + [f(c) for c in CODES for f in (rec_b, rec_c)]
    with pytest.raises(A309.InputsError, match="recomputed"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_a_held_opening_never_gives_a_released_number():
    om = dict(rec_b("FIN.PLASTER")["owner_method"])
    recs = [rec_b(c, state="RELEASED", value=38.0, evidence_status="ASSUMED - OWNER-APPROVED", assumption="G1",
                  owner_method=om) for c in CODES] + [f(c) for c in CODES for f in (rec_a, rec_c)]
    with pytest.raises(A309.InputsError, match="every deduction known"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_verified_needs_the_checker_run():
    recs = [rec_a(c, verified_by=None) for c in CODES] + [f(c) for c in CODES for f in (rec_b, rec_c)]
    with pytest.raises(A309.InputsError, match="VERIFIED names"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_the_owner_assumption_never_disappears_from_a_released_line():
    recs = [rec_a(c, assumption=None) for c in CODES] + [f(c) for c in CODES for f in (rec_b, rec_c)]
    with pytest.raises(A309.InputsError, match="assumption"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_both_methods_side_by_side_required():
    recs = [rec_a(c, drawing_method=None) for c in CODES] + [f(c) for c in CODES for f in (rec_b, rec_c)]
    with pytest.raises(A309.InputsError, match="drawing-derived"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_bounded_range_must_equal_the_recomputed_bounds():
    recs = [rec_b(c, range=[33.0, 40.2]) for c in CODES] + [f(c) for c in CODES for f in (rec_a, rec_c)]
    with pytest.raises(A309.InputsError, match="recomputed"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_a_held_range_never_collapses_to_zero():
    recs = [rec_b(c, range=[0, 0], owner_method={"note": "x"}) for c in CODES] + \
        [f(c) for c in CODES for f in (rec_a, rec_c)]
    with pytest.raises(A309.InputsError, match="high > 0"):
        A309.load_inputs(doc(recs), PID)


def test_adverse_corners_in_metres_are_never_an_m2_line():
    with pytest.raises(A309.InputsError, match="m.l item is never an m2 line"):
        A309.load_inputs(doc(unit="m"), PID)


def test_adverse_a_scope_room_without_a_record_is_a_silent_omission():
    recs = [f(c) for c in CODES for f in (rec_a, rec_b)]
    d = doc(recs, declared=False)
    with pytest.raises(A309.InputsError, match="silent omission"):
        A309.load_inputs(d, PID)


def test_adverse_record_without_a_merged_source_is_refused():
    d = doc()
    d["pieces"][0]["source"]["merge_commit"] = ""
    with pytest.raises(A309.InputsError, match="merge_commit"):
        A309.load_inputs(d, PID)


def test_adverse_declared_totals_disagree():
    d = doc()
    d["pieces"][0]["declared_totals"]["FIN.PLASTER"]["released"] = 55.0
    with pytest.raises(ValueError, match="declared"):
        run(d)


def test_adverse_an_approved_line_is_never_superseded():
    lines = l308()
    ln = by_eid(lines, "GF-RA:plaster")
    ln["approval_state"] = "APPROVED"
    with pytest.raises(ValueError, match="approved line"):
        run(lines=lines)


def test_adverse_project_mix_refused():
    with pytest.raises(A309.InputsError, match="are for"):
        A309.load_inputs(doc(), "another-project")


def test_no_inputs_changes_nothing():
    lines = l308()
    ch, logs = A309.changes_for(None, lines)
    assert ch == [] and logs[0]["state"] == "NO_PROJECT_INPUT"
    out, ident = A309.integrate(lines, ch)
    assert ident["outside_rows"] == len(lines)


# --------------------------------------------------------------------------------------------------------- wiring
def test_cli_method_registered_and_inputs_need_the_method():
    from tools import urban_boq_m9 as M
    assert M.V309 == A309.METHOD and M.CANDIDATE_EXTENSIONS_V309 == (A309.METHOD,)
    with pytest.raises(SystemExit, match="--v309-inputs needs"):
        M.main(["arch", "--drawings", "x.dxf", "--out", "o", "--method", "ARCH_TAKEOFF_V3.0.8",
                "--v309-inputs", "i.json"])


def test_module_is_a_guard_host_and_names_no_reinforcement_word():
    assert A309.DEFAULT_GUARD_CLASS == "GUARD_HOST"
    text = (ROOT / "engine/source/arch_v309.py").read_text(encoding="utf-8").lower()
    for w in ("rebar", "reinforc", "steel"):
        assert w not in text


def test_inputs_record_is_copied_not_mutated():
    d = doc()
    keep = copy.deepcopy(d)
    run(d)
    assert d == keep
