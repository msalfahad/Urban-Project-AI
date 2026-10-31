"""T-328: ARCH_TAKEOFF_V3.0.31 (roof build-up as its own line family, from the checker-merged layer ledger and its line
binding) on a hand-calculated NON-Alsenan villa (V328), normal and adverse.

Villa V328, by hand (a build-up layer is measured to its OWN edge; one line per roof and layer; one owner trade each):
  R1 main roof +7.00, parapet on three sides, one drain, printed fall 1 %: inside the parapet / wall inner faces
     8.00 x 6.00 = 48.000 m2 (the roof outline); a 0.10 x 5.00 drip band at the stair-wall foot (nature unprinted) makes
     the face layers 47.500 .. 48.000 m2 (a range with its cause, never chosen); finish hatch = 48.000 - 0.500 (band)
     - 0.60 x 0.60 (drain sump) = 47.140 m2; screed t0 unprinted -> HELD blank; insulation / protection unprinted ->
     UNKNOWN blank
  R2 stair-head roof +10.00, walls all round, printed fall 1 % to one edge: 5.00 x 4.00 = 20.000 m2; screed printed
     t0 0.05 m + the wedge rise 1 % x 4.00 = 0.040 m at the far edge: 20.000 x 0.05 + 20.000 x 0.040 / 2 = 1.000 + 0.400
     = 1.400 m3; insulation printed 50 mm on the full roof 20.000 m2; protection UNKNOWN; finish 20.000 m2
  R3 roof held by an owner decision: every layer blank
  totals: FIN.ROOF.FINISH 47.140 + 20.000 = 67.140 m2; FIN.ROOF.INSULATION 20.000 m2; FIN.ROOF.SCREED 1.400 m3;
  8 blank lines (R1 screed / insulation / protection 3 + R2 protection 1 + R3 all four 4);
  every V3.0.30 line byte-identical; the membrane / upturn / parapet lines bound and untouched.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3031 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v328", "d" * 64
DOCS = [{"file": "v328_roof_plan.dxf", "sha256": "c" * 64}]
SRC = [{"task": "T-339", "file": "research/v328/fill.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 30 (Gate A PASS)"},
       {"task": "T-321", "file": "research/v328/ledger.json", "sha256": "2" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker run 29 (Gate A PASS)"}]


def _line(code, eid, ev, net=None, unit="m2", floor="RF"):
    kw = {"rfi": {"question": "held"}} if ev == "BLOCKED_RFI" else {}
    if code not in BL.ITEMS:
        kw.update(item_en=code, item_ar="-", trade="WATERPROOFING")
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element=eid,
                        formula=f"{eid} {net}", documents=DOCS, rule_id="R", rule_version="1", notes="v328", **kw)


def _parapet():
    """a V3.0.23-shaped parapet RC line: HELD blank with its bound record (the parapet family guard reads it)"""
    ln = _line("STR.CONC.PARAPET", "P1", "BLOCKED_RFI", unit="m3")
    ln["calculation"]["inputs"]["parapet_rc_v3023"] = {"chain": "RF", "runs": [{"run": "P1-1"}],
                                                       "bound": {"floor_at_least_m3": 0.5}}
    return BL.validate(ln)


def lines_3030():
    return [_line("FIN.WP.ROOF", "R1", "SOURCE_DERIVED", 48.0),
            _line("FIN.WP.ROOF_UPTURN", "R1", "SOURCE_DERIVED", 22.0, unit="lm"),
            _line("FIN.WP.ROOF", "R2", "SOURCE_DERIVED", 20.0),
            _line("FIN.WP.ROOF", "R3", "BLOCKED_RFI"),
            _parapet(),
            _line("STR.CONC.SLAB", "S-R1", "SOURCE_DERIVED", 7.2, unit="m3")]


def _b(lines, code, eid):
    ln = next(x for x in lines if x["item_code"] == code and x["location"]["element_id"] == eid)
    return {"line_id": ln["line_id"], "item_code": code, "evidence_state": ln["evidence_state"],
            "measured_net": ln["measured_net"], "element_id": eid}


def _ly(name, st, unit, **kw):
    d = {"layer": name, "source_task": "T-339", "status": st, "owner_trade": A.OWNER_TRADE[name], "unit": unit,
         "edge": "FINISH" if name == "FINISH" else "FACE", "edge_handles": ["H1", "H2"], "quantity": None,
         "thickness_m": None, "held_reason": None if st == "DRAWING-CONFIRMED" else "not printed (designer item)",
         "runs_up_parapet": False}
    d.update(kw)
    return d


def doc(lines=None):
    lines = lines or lines_3030()
    band = "drip band 0.10 x 5.00 at the stair-wall foot, nature unprinted: 47.500 or 48.000 m2"
    return {
        "schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
        "roofs": [
            {"roof": "R1", "element_id": "RF-R1", "floor": "RF", "outline_m2": 48.0, "fall_printed_pct": 1.0,
             "held_roof": None, "membrane_line": _b(lines, "FIN.WP.ROOF", "R1"),
             "upturn_line": _b(lines, "FIN.WP.ROOF_UPTURN", "R1"),
             "layers": [_ly("FALLS_SCREED", "HELD", "m3", basis_lo=47.5, basis_hi=48.0, range_cause=band,
                            held_reason="t0 unprinted (designer)"),
                        _ly("INSULATION", "UNKNOWN", "m2"), _ly("PROTECTION", "UNKNOWN", "m2"),
                        _ly("FINISH", "DRAWING-CONFIRMED", "m2", quantity=47.14, basis_lo=47.14, basis_hi=47.14)]},
            {"roof": "R2", "element_id": "RF-R2", "floor": "RF", "outline_m2": 20.0, "fall_printed_pct": 1.0,
             "held_roof": None, "membrane_line": _b(lines, "FIN.WP.ROOF", "R2"),
             "layers": [_ly("FALLS_SCREED", "DRAWING-CONFIRMED", "m3", quantity=1.4, basis_lo=20.0, basis_hi=20.0,
                            thickness_m=0.05, thickness_source="roof detail D1 't0 50'", above_t0_m3=0.4),
                        _ly("INSULATION", "DRAWING-CONFIRMED", "m2", quantity=20.0, basis_lo=20.0, basis_hi=20.0,
                            thickness_m=0.05, thickness_source="roof detail D1 '50 mm insulation'"),
                        _ly("PROTECTION", "UNKNOWN", "m2"),
                        _ly("FINISH", "DRAWING-CONFIRMED", "m2", quantity=20.0)]},
            {"roof": "R3", "element_id": "RF-R3", "floor": "RF", "outline_m2": None, "fall_printed_pct": None,
             "held_roof": {"reason": "owner decision: the top roof stays held"},
             "membrane_line": _b(lines, "FIN.WP.ROOF", "R3"),
             "layers": [_ly("FALLS_SCREED", "HELD", "m3"), _ly("INSULATION", "HELD", "m2"),
                        _ly("PROTECTION", "HELD", "m2"), _ly("FINISH", "HELD", "m2")]}],
        "parapet_lines": [_b(lines, "STR.CONC.PARAPET", "P1")]}


def run(d=None, lines=None):
    lines = lines or lines_3030()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _add(out, lines):
    ids = {x["line_id"] for x in lines}
    return [x for x in out if x["line_id"] not in ids]


# ------------------------------------------------------------------ normal
def test_hand_totals_and_states():
    lines, ch, log, out, ident = run()
    add = _add(out, lines)
    assert len(add) == 12 == ident["added"]                      # 3 roofs x 4 layers, one line each
    t = A304.code_totals(add)
    assert t["FIN.ROOF.FINISH|m2"]["released"] == pytest.approx(67.14, abs=1e-9)
    assert t["FIN.ROOF.INSULATION|m2"]["released"] == pytest.approx(20.0, abs=1e-9)
    assert t["FIN.ROOF.SCREED|m3"]["released"] == pytest.approx(1.4, abs=1e-9)
    blank = [x for x in add if x["evidence_state"] == "BLOCKED_RFI"]
    assert len(blank) == 8 and all(x["measured_net"] is None and not x.get("bounded_range") for x in blank)
    assert {(x["calculation"]["inputs"][A.REC_KEY]["roof"], x["calculation"]["inputs"][A.REC_KEY]["layer"])
            for x in blank} == {("R1", "FALLS_SCREED"), ("R1", "INSULATION"), ("R1", "PROTECTION"),
                                ("R2", "PROTECTION"), ("R3", "FALLS_SCREED"), ("R3", "INSULATION"),
                                ("R3", "PROTECTION"), ("R3", "FINISH")}
    assert ident["roof_buildup"]["roofs"] == 3


def test_every_v3030_line_byte_identical_and_only_roof_totals_move():
    lines, ch, log, out, ident = run()
    by = {x["line_id"]: x for x in out}
    assert all(A30.line_sha(x) == A30.line_sha(by[x["line_id"]]) for x in lines)
    assert ident["outside_rows_identical_to_v3_0_30"] == len(lines)
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved and all(k.split("|")[0] in A.ITEMS for k in moved)


def test_range_carried_beside_with_its_cause_never_a_figure():
    lines, ch, log, out, ident = run()
    s = next(x for x in _add(out, lines) if x["location"]["element_id"] == "ROOF:R1:FALLS_SCREED")
    rec = s["calculation"]["inputs"][A.REC_KEY]
    assert s["evidence_state"] == "BLOCKED_RFI" and s["unit"] == "m3" and s["measured_net"] is None
    assert rec["basis"]["lo"] == 47.5 and rec["basis"]["hi"] == 48.0 and "drip band" in rec["basis"]["cause"]
    assert "47.5 .. 48 m2 beside" in s["rfi"]["question"]
    assert "Q-41" in rec["evidence_status"]                        # the screed scope rests on the owner rule


def test_one_owner_trade_per_layer_and_screed_is_one_volume_per_roof():
    lines, ch, log, out, ident = run()
    add = _add(out, lines)
    sc = [x for x in add if x["item_code"] == A.SCREED]
    assert len(sc) == 3 and all(x["unit"] == "m3" and x["subtrade"] == "SCREED" for x in sc)
    assert all(x["trade"] == "ROOFING" for x in add)
    assert {x["calculation"]["inputs"][A.REC_KEY]["owner_trade"] for x in sc} == {"SCREED"}


def test_membrane_upturn_and_parapet_lines_untouched_and_bound():
    lines, ch, log, out, ident = run()
    for code in ("FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "STR.CONC.PARAPET"):
        assert [A30.line_sha(x) for x in lines if x["item_code"] == code] == \
            [A30.line_sha(x) for x in out if x["item_code"] == code]
    r1 = next(x for x in _add(out, lines) if x["location"]["element_id"] == "ROOF:R1:FINISH")
    assert r1["calculation"]["inputs"][A.REC_KEY]["membrane_line"] == lines[0]["line_id"]


def test_ledger_and_diff_rows():
    lines, ch, log, out, ident = run()
    rows = A.ledger_rows(ch, released_lines=[])
    assert len(rows) == 12 and all(r["before_v3_0_30"]["state"] == "NOT_IN_V3_0_30" for r in rows)
    assert all(r["owner_manual_method"] and r["drawing_derived_method"] for r in rows)
    d = A.diff_rows(lines, out, released_lines=[])
    assert sum(1 for r in d if r["vs_v3_0_30"] == "ADDED") == 12 and sum(1 for r in d if r["vs_v3_0_30"] == "SAME") \
        == len(lines)
    assert "FIN.ROOF.FINISH" in A.ledger_csv(rows)


def test_write_files(tmp_path):
    lines, ch, log, out, ident = run()
    names, ident2, led = A.write(tmp_path, lines, ch, log, A.load_inputs(doc(), PID), released_lines=[])
    assert names == sorted(["V3_0_31_BOQ_LINES.json", "V3_0_31_BOQ_LINES.csv", "V3_0_31_INTEGRATION_LEDGER.json",
                            "V3_0_31_INTEGRATION_LEDGER.csv", "V3_0_31_DIFF.csv", "V3_0_31_RUN.json"])
    assert led["integration_package"] is True and led["released_default"] is False


# ------------------------------------------------------------------ adverse
def _bad(mut, match):
    d = doc()
    mut(d)
    with pytest.raises(A.InputsError, match=match):
        A.load_inputs(d, PID)


def _r(d, rid):
    return next(r for r in d["roofs"] if r["roof"] == rid)


def _l(d, rid, name):
    return next(x for x in _r(d, rid)["layers"] if x["layer"] == name)


def test_adverse_a_second_falls_layer_for_q45_is_refused():
    _bad(lambda d: _r(d, "R1")["layers"].append(_ly("FALLS_SCREED", "HELD", "m3")), "booked twice")
    _bad(lambda d: _r(d, "R1")["layers"].append(dict(_ly("FINISH", "HELD", "m2"), layer="TILE_BED_FALLS")),
         "not a build-up layer")


def test_adverse_a_constant_layer_on_a_sloped_roof_is_refused():
    def m(d):
        s = _l(d, "R2", "FALLS_SCREED")
        s["quantity"], s["above_t0_m3"] = 1.0, None                  # 20.000 x 0.05 flat on a 1 % roof
    _bad(m, "constant-thickness screed")
    _bad(lambda d: _l(d, "R2", "FALLS_SCREED").update(quantity=1.0), "is not area x t0")


def test_adverse_held_as_zero_and_default_thickness_are_refused():
    _bad(lambda d: _l(d, "R1", "FALLS_SCREED").update(quantity=0.0), "held is BLANK")
    _bad(lambda d: _l(d, "R1", "INSULATION").update(thickness_m=0.05), "without its print")
    _bad(lambda d: _l(d, "R1", "INSULATION").update(held_reason=None), "names why it is blank")


def test_adverse_layer_edges_outline_and_parapet():
    _bad(lambda d: _l(d, "R1", "FINISH").update(edge="PARAPET_OUTER_FACE"), "INNER face")
    _bad(lambda d: _l(d, "R1", "FINISH").update(quantity=48.5), "above the roof outline")
    _bad(lambda d: _l(d, "R1", "FALLS_SCREED").update(basis_hi=48.6), "above the roof outline")
    _bad(lambda d: _l(d, "R1", "FALLS_SCREED").update(range_cause=None), "named cause")
    _bad(lambda d: _l(d, "R1", "PROTECTION").update(runs_up_parapet=True), "without a printed upturn")


def test_adverse_units_missing_rows_trade_and_held_roof():
    _bad(lambda d: _l(d, "R1", "FINISH").update(unit="m3"), "unit")
    _bad(lambda d: _r(d, "R2")["layers"].pop(2), "every roof carries all")
    _bad(lambda d: _l(d, "R1", "FALLS_SCREED").update(owner_trade="ROOFING B13-01"), "owner trade")
    _bad(lambda d: _l(d, "R3", "FINISH").update(status="DRAWING-CONFIRMED", quantity=10.0, held_reason=None),
         "held roof")
    _bad(lambda d: _l(d, "R1", "FINISH").update(source_task="T-999"), "no merged source")


def test_adverse_stale_binding_and_applied_twice():
    lines = lines_3030()
    d = doc(lines)
    d["roofs"][0]["membrane_line"]["measured_net"] = 47.0
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(d, PID), lines)
    d = doc(lines)
    d["parapet_lines"][0]["evidence_state"] = "SOURCE_DERIVED"
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(d, PID), lines)
    _, _, _, out, _ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(lines), PID), out)


def test_adverse_finished_lines_guard():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    x = next(ln for ln in bad if ln["location"]["element_id"] == "ROOF:R1:INSULATION")
    x["measured_net"] = 0.0
    with pytest.raises(ValueError, match="carries a figure"):
        A.check_roof_layers(bad)
    bad = copy.deepcopy(out)
    dup = copy.deepcopy(next(ln for ln in bad if ln["location"]["element_id"] == "ROOF:R2:FALLS_SCREED"))
    dup["line_id"] = "L-dup"
    bad.append(dup)
    with pytest.raises(ValueError, match="one line per roof and layer"):
        A.check_roof_layers(bad)
    bad = copy.deepcopy(out)
    p = next(ln for ln in bad if ln["item_code"] == "STR.CONC.PARAPET")
    x = next(ln for ln in bad if ln["location"]["element_id"] == "ROOF:R1:FINISH")
    x["location"]["element_id"] = p["location"]["element_id"]
    with pytest.raises(ValueError, match="parapet element"):
        A.check_roof_layers(bad)


def test_adverse_integrate_refuses_a_foreign_change():
    lines, ch, log, out, ident = run()
    c = copy.deepcopy(ch[0])
    c["after"] = copy.deepcopy(lines[0])
    with pytest.raises(ValueError):
        A.integrate(lines, [c])
