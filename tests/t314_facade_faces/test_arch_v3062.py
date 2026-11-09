"""T-314 R-T314-1 on villa N (not the development villa; hand calculation here):

  house F.F.L. +0.60, annex F.F.L. +0.20 (a two-F.F.L. ground floor), 1F F.F.L. +4.00, 1F roof +7.40;
  GF storey line, one part +0.20 .. +4.00:
      A annex face +0.20 -> +3.70 x 6.00 m = 21.000 m2 DC, door D1 2.000 m2 (head 2.20 ASSUMED, sill 0.20 head 2.20)
      B house face +0.60 -> +4.00 x 7.00 m = 23.800 m2 DC, window W1 1.800 m2 DC (sill 1.60 head 2.80)
      gross 44.800, net 44.800 - 3.800 = 41.000 m2 (ASSUMED part: D1) -> PROVISIONAL 41.000
      run x storey height (13.00 x (4.00 - 0.20) = 49.400) is wrong by +4.600 m2: rows replace it
  1F storey line +4.00 .. +7.40: C 3.40 x 10.00 = 34.000 m2 DC, W2 HELD (sill / head unprinted) cap 3.000:
      net 31.000 .. 34.000, NO point value (BOUNDED_EXPOSURE)
  annex parapet outer +3.70 -> +4.20 x 6.00 = 3.000 m2 DC (its own line, never in GF)
  plinth +0.00 -> +0.60 x 7.00 = 4.200 DC + pool-side face bottom unprinted (top +0.60) 0.500 .. 0.800 HELD:
      4.700 .. 5.000 HELD
  1F slab edge: no depth printed -> blank, never 0
"""
import copy

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v304 as A304
from engine.source import arch_v3062 as A
from engine.source import boq_line as BL

PID = "villa-n"
GF, F1, OTHER = None, None, None
DC, AS, H = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD"


def _base():
    def held(eid, fl):
        return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="FIN.EXT.FINISH", unit="m2",
                            evidence_state="BLOCKED_RFI", element_id=eid, floor=fl, formula="HELD: facade",
                            rule_id="R-OLD", rule_version="1", rfi={"question": "exterior finish faces", "blocks": []},
                            item_en="Exterior finish", item_ar="تشطيب خارجي", trade="FACADE")
    other = BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="FIN.PLASTER", unit="m2",
                         evidence_state="MEASURED", measured_net=12.5, gross=12.5, element_id="GF-R1:plaster",
                         floor="GF", formula="4 x 3.125", rule_id="R-OLD", rule_version="1",
                         item_en="Plaster", item_ar="لياسة", trade="PLASTER")
    return [held("GF-FACADE:facade", "GF"), other, held("1F-FACADE:facade", "1F")]


def _doc(base):
    gf, f1 = base[0]["line_id"], base[2]["line_id"]
    return {
        "schema": A.INPUTS_SCHEMA, "project": PID,
        "sources": [{"task": "T-N", "file": "ledger.csv", "sha256": "a" * 64, "merge_commit": "m", "checker_run": "c"}],
        "lines": [{"key": gf, "line_id": gf, "element": "STOREY", "floor": "GF", "parts": [[0.20, 4.00]]},
                  {"key": f1, "line_id": f1, "element": "STOREY", "floor": "1F", "parts": [[4.00, 7.40]],
                   "why_held": "W2 size"},
                  {"key": "PAR", "element": "PARAPET_OUTER", "floor": "GF", "element_id": "GF-FACADE:PAR",
                   "parts": [[3.70, 4.20]]},
                  {"key": "PLI", "element": "PLINTH", "floor": "GF", "element_id": "GF-FACADE:PLINTH",
                   "parts": [[0.0, 0.60]], "why_held": "pool-side bottom"},
                  {"key": "EDGE", "element": "SLAB_EDGE", "floor": "1F", "element_id": "1F-FACADE:EDGE",
                   "why_held": "slab edge depth"}],
        "faces": [
            {"face_id": "A", "line": gf, "element": "STOREY", "bottom": 0.20, "top": 3.70, "lo": 21.0, "hi": 21.0,
             "status": DC, "owner_q07": 21.0},
            {"face_id": "B", "line": gf, "element": "STOREY", "bottom": 0.60, "top": 4.00, "lo": 23.8, "hi": 23.8,
             "status": DC, "owner_q07": 23.8},
            {"face_id": "C", "line": f1, "element": "STOREY", "bottom": 4.00, "top": 7.40, "lo": 34.0, "hi": 34.0,
             "status": DC},
            {"face_id": "P", "line": "PAR", "element": "PARAPET_OUTER", "bottom": 3.70, "top": 4.20, "lo": 3.0,
             "hi": 3.0, "status": DC},
            {"face_id": "L1", "line": "PLI", "element": "PLINTH", "bottom": 0.0, "top": 0.60, "lo": 4.2, "hi": 4.2,
             "status": DC},
            {"face_id": "L2", "line": "PLI", "element": "PLINTH", "bottom": None, "top": 0.60, "lo": 0.5, "hi": 0.8,
             "status": H},
            {"face_id": "E", "line": "EDGE", "element": "SLAB_EDGE", "lo": None, "hi": None, "status": H}],
        "openings": [
            {"opening_id": "D1", "face_id": "A", "hole_m2": 2.0, "status": AS, "sill": 0.20, "head": 2.20},
            {"opening_id": "W1", "face_id": "B", "hole_m2": 1.8, "status": DC, "sill": 1.60, "head": 2.80},
            {"opening_id": "W2", "face_id": "C", "hole_m2": None, "cap_m2": 3.0, "status": H}],
        "items": [{"key": "FIN.EXT.CORNERS", "unit": "lm", "status": "HELD", "why": "registry family first"}],
        "expect": {gf: {"gross": [44.8, 44.8], "net": [41.0, 41.0]}, f1: {"gross": [34.0, 34.0], "net": [31.0, 34.0]},
                   "PAR": {"net": [3.0, 3.0]}, "PLI": {"gross": [4.7, 5.0], "net": [4.7, 5.0]},
                   "EDGE": {"gross": None, "net": None}}}


def _run(doc=None, base=None):
    base = base or _base()
    d = A.load_inputs(doc or _doc(base), PID)
    ch, log = A.changes_for(d, base)
    return base, ch, log


def test_normal_hand_figures_and_states():
    base, ch, log = _run()
    by = {c["line_key"]: c["after"] for c in ch}
    g, f = by[base[0]["line_id"]], by[base[2]["line_id"]]
    assert (g["evidence_state"], g["measured_net"], g["gross"]) == ("PROVISIONAL", 41.0, 44.8)
    assert g["line_id"] == base[0]["line_id"] and g["location"] == base[0]["location"]
    assert f["evidence_state"] == "BOUNDED_EXPOSURE" and f["measured_net"] is None
    assert (f["bounded_range"]["low"], f["bounded_range"]["high"]) == (31.0, 34.0)
    assert by["PAR"]["measured_net"] == 3.0 and by["PAR"]["evidence_state"] == "MEASURED"
    assert by["PLI"]["bounded_range"]["low"] == 4.7 and by["PLI"]["measured_net"] is None
    assert by["EDGE"]["evidence_state"] == "BLOCKED_RFI" and by["EDGE"]["measured_net"] is None
    assert log == dict(log, changed=2, added=3)
    assert g["calculation"]["inputs"][A.REC_KEY]["owner_q07_beside_m2"] == 44.8
    # the old formula: run x storey height on the two-F.F.L. ground floor is not the rows' gross
    assert abs(13.0 * (4.00 - 0.20) - 44.8 - 4.6) < 1e-9


def test_integrate_keeps_every_other_line_and_moves_only_ext_totals():
    base, ch, _ = _run()
    out, ident = A.integrate(base, ch)
    assert ident["replaced"] == 2 and ident["added"] == 3 and ident["outside_rows"] == 1
    assert A30.line_sha(out[1]) == A30.line_sha(base[1])
    assert ident["faces"] == {"face_lines": 5, "faces": 7, "openings": 3}
    moved = A.check_totals(A304.code_totals(base), A304.code_totals(out))
    assert set(moved) == {"FIN.EXT.FINISH|m2"}


def test_reversed_row_order_gives_the_same_lines():
    base = _base()
    doc = _doc(base)
    rev = dict(doc, faces=list(reversed(doc["faces"])), openings=list(reversed(doc["openings"])),
               lines=list(reversed(doc["lines"])))
    a = [A30.line_sha(c["after"]) for c in _run(doc, base)[1]]
    b = [A30.line_sha(c["after"]) for c in _run(rev, base)[1]]
    assert a == b


def _bad(mut, match):
    base = _base()
    doc = _doc(base)
    mut(doc, base)
    with pytest.raises(A.InputsError, match=match):
        _run(doc, base)


def test_adverse_parapet_band_in_a_storey_line_refused():
    def m(d, b):
        d["faces"][3].update(line=b[0]["line_id"])
    _bad(m, "PARAPET_OUTER band in the STOREY line")

    def m2(d, b):
        d["faces"][3].update(line=b[0]["line_id"], element="STOREY")     # relabelled: crosses the GF part top
    _bad(m2, "crosses a level part")


def test_adverse_band_crossing_a_level_refused():
    _bad(lambda d, b: d["faces"][1].update(top=4.40), "crosses a level part")


def test_adverse_held_as_zero_and_dc_range_refused():
    _bad(lambda d, b: d["faces"][5].update(lo=0.0, hi=0.0), "carried as 0")
    _bad(lambda d, b: d["faces"][0].update(hi=21.5), "carries one value")
    _bad(lambda d, b: d["faces"][0].update(lo=None, hi=None), "without an area")


def test_adverse_openings():
    _bad(lambda d, b: d["openings"].append(dict(d["openings"][1])), "deducted twice")
    _bad(lambda d, b: d["openings"][1].update(hole_m2=30.0), "larger than its face")
    _bad(lambda d, b: d["openings"][1].update(head=4.50), "leaves its band")
    _bad(lambda d, b: d["openings"][2].update(cap_m2=0.0), "bounded at 0")
    _bad(lambda d, b: d["openings"][2].update(hole_m2=1.5), "no point value")


def test_adverse_face_twice_units_items_expect():
    _bad(lambda d, b: d["faces"].append(dict(d["faces"][0])), "booked twice")
    _bad(lambda d, b: d["faces"][0].update(bottom=200.0 + 1, top=3700.0), "millimetres")
    _bad(lambda d, b: d["items"].append({"key": "FIN.EXT.DRIP", "unit": "lm", "value": 12.0}), "carries no number")
    _bad(lambda d, b: d["expect"][b[0]["line_id"]].update(net=[42.0, 42.0]), "expected")


def test_adverse_unbound_line_stale_binding_and_applied_twice():
    def drop(d, b):
        d["lines"] = [x for x in d["lines"] if x["key"] != b[2]["line_id"]]
        d["faces"] = [x for x in d["faces"] if x["face_id"] != "C"]
        d["openings"] = [x for x in d["openings"] if x["opening_id"] != "W2"]
        d["expect"].pop(b[2]["line_id"])
    _bad(drop, "not bound by the face rows")
    _bad(lambda d, b: d["lines"][0].update(line_id="L-nope"), "stale binding")
    base, ch, _ = _run()
    out, _ = A.integrate(base, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(_doc(base), PID), out)


def test_integrate_refuses_another_code_and_a_held_point():
    base, ch, _ = _run()
    bad = copy.deepcopy(ch)
    bad[0]["after"]["item_code"] = "FIN.PLASTER"
    with pytest.raises(ValueError, match="not a code this version"):
        A.integrate(base, bad)
    lines = [c["after"] for c in ch]
    f = next(x for x in lines if x["bounded_range"])
    f2 = copy.deepcopy(f)
    f2["bounded_range"]["high"] = 0.0
    with pytest.raises(ValueError, match="carried as 0"):
        A.check_faces([f2])
