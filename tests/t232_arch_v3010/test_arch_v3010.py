"""T-232: ARCH_TAKEOFF_V3.0.10, the SAME opt-in candidate as V3.0 .. V3.0.9 extended (engine.source.arch_v3010):
doors and windows as pcs AND m2 lines by type and floor from ONE opening list. Synthetic data only (no client drawing).

VILLA K-232 (not the development villa). Door head 2.20 where none is printed (Q-55 C, ASSUMED - OWNER-APPROVED);
window m2 = Q-32 A enclosing rectangle on the opening line. Hand values:
  GF  DA  aluminium external door 1.00 x 2.20 (assumed)            pcs 1, 2.200 m2   (engine line DOOR-GF-A)
      DB  PVC internal door 0.80 x 2.20 (assumed)                   pcs 1, 1.760 m2   (engine line DOOR-GF-B)
      DC  main entrance, DOUBLE leaf, printed 1.80 x 2.40           pcs 1 (one opening), 4.320 m2 DRAWING-CONFIRMED
                                                                    (no engine line: the engine missed it)
      DD  class held (aluminium if the passage is open-air, else PVC) 0.90 x 2.20: answered in BOTH classes as
          pcs [0, 1], m2 [0, 1.980]                                 (no engine line)
      WA  window 1.50 x 1.20 printed                                pcs 1, 1.800 m2   (engine line GF-R1:OP-001)
      WB  arched window 1.00 wide, opening crown 2.10 (the band 0.10 above is not the opening)
                                                                    pcs 1, 2.100 m2   (engine line GF-R1:OP-002)
      WC  window 0.60 wide, head not printed: height 1.20 .. 1.50  pcs 1, m2 HELD [0.720, 0.900] (engine OP-003)
  1F  WD  window 2.00 x 1.50 printed                                pcs 1, 3.000 m2   (engine line 1F-R2:OP-001)
      DE  PVC internal door 0.90 x 2.20 (assumed)                   pcs 1, 1.980 m2   (engine line DOOR-1F-E)
  Totals: aluminium pcs 1 + [0, 1], m2 2.200 + [0, 1.980]; PVC pcs 2 + [0, 1], m2 3.740 + [0, 1.980]; main
  entrance pcs 1, m2 4.320; windows pcs 4 (GF 3, 1F 1), m2 GF 3.900 + [0.720, 0.900], 1F 3.000.
  Unrelated lines (a reveal m2 line, a plaster line, a beam) stay byte-identical.
"""

from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3010 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402
from tools import alsenan_keymap as K                          # noqa: E402
from tools import alsenan_scoreboard as S                      # noqa: E402

AP = pytest.approx
PID = "synthetic-v3010-villa-k232"
DOCS = [{"file": "K-ARCH.dxf", "sha256": "2" * 64}]
ALU, PVC, MAIN, WIN = "DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "ARCH.WINDOW"
CODES = [ALU, PVC, MAIN, WIN]
DC, AS = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"
Q55 = "Q-55 C door head 2.20 (ASSUMED - OWNER-APPROVED)"


def line(eid, item, floor, unit="pcs", q=1, ev="SOURCE_DERIVED", room=None):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit=unit, evidence_state=ev,
                        measured_net=q, element_id=eid, floor=floor, room_id=room, physical_element=eid,
                        formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if ev == "BLOCKED_RFI" else None)


ENGINE = [("DOOR-GF-A", ALU, "GF", "DA"), ("DOOR-GF-B", PVC, "GF", "DB"), ("GF-R1:OP-001", WIN, "GF", "WA"),
          ("GF-R1:OP-002", WIN, "GF", "WB"), ("GF-R1:OP-003", WIN, "GF", "WC"), ("1F-R2:OP-001", WIN, "1F", "WD"),
          ("DOOR-1F-E", PVC, "1F", "DE")]


def l309():
    out = [line(e, c, f, room=e.split(":")[0]) for e, c, f, _ in ENGINE]
    out.append(line("GF-R1:OP-001:reveal", "ARCH.WINDOW_REVEAL", "GF", "m2", None, "BLOCKED_RFI"))
    out.append(line("GF-R1:plaster", "FIN.PLASTER", "GF", "m2", 30.0, "PROVISIONAL"))
    out.append(line("P-C:BEAMS:1F:B1", "STR.CONC.BEAM", "1F", "m3", 1.2))
    return out


def src(task):
    return {"file": f"research/{task}.csv", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task}"}


def dim(v, st=DC, rg=None):
    return {"range": rg, "status": st, "source": "hand"} if rg else {"value": v, "status": st, "source": "hand"}


def door(oid, floor, code, w, h=2.2, leaves=1, **kw):
    assumed = kw.pop("assumed", True)
    o = {"id": oid, "kind": "DOOR", "floor": floor, "classes": [code], "leaves": leaves,
         "opening_definition": "structural opening jamb to jamb", "sources": [src("T-CEN")],
         "width": dim(w), "height": dim(h, AS if assumed else DC),
         "pcs": {"state": "SETTLED", "count": 1},
         "m2": {"state": "RELEASED", "value": round(w * h, 4), "evidence_status": AS if assumed else DC}}
    if assumed:
        o["assumption"] = Q55
    o.update(kw)
    return o


def window(oid, floor, w, h=None, hr=None, **kw):
    o = {"id": oid, "kind": "WINDOW", "floor": floor, "classes": [WIN], "leaves": 1,
         "opening_definition": "structural opening on the opening line; Q-32 A", "sources": [src("T-CEN")],
         "width": dim(w), "height": dim(h, rg=hr), "pcs": {"state": "SETTLED", "count": 1}}
    if hr:
        o["m2"] = {"state": "BOUNDED", "range": [round(w * hr[0], 4), round(w * hr[1], 4)], "evidence_status": "HELD",
                   "reasons": ["head not printed"]}
    else:
        o["m2"] = {"state": "RELEASED", "value": round(w * h, 4), "evidence_status": DC}
    o.update(kw)
    return o


def openings():
    held = "class held: aluminium if the passage is open-air, else PVC"
    dd = door("DD", "GF", ALU, 0.90, classes=[ALU, PVC], class_hold=held,
              pcs={"state": "HELD", "range": [0, 1], "reasons": [held]},
              m2={"state": "BOUNDED", "range": [0.0, 1.98], "evidence_status": "HELD", "reasons": [held],
                  "range_basis": "0 in this class .. width x height"})
    return [door("DA", "GF", ALU, 1.00), door("DB", "GF", PVC, 0.80),
            door("DC", "GF", MAIN, 1.80, 2.40, leaves=2, assumed=False), dd,
            window("WA", "GF", 1.50, 1.20), window("WB", "GF", 1.00, 2.10), window("WC", "GF", 0.60, hr=[1.20, 1.50]),
            window("WD", "1F", 2.00, 1.50), door("DE", "1F", PVC, 0.90)]


def supersede():
    return [{"element_id": e, "floor": f, "item_code": c, "unit": "pcs", "carried": 1, "opening": o,
             "why": f"the same opening {o}"} for e, c, f, o in ENGINE]


DECLARED = {ALU: {"pcs": {"settled": 1, "held": [0, 1], "no_figure": 0},
                  "m2": {"released": 2.2, "bounded": [0.0, 1.98], "unquantified": 0}},
            PVC: {"pcs": {"settled": 2, "held": [0, 1], "no_figure": 0},
                  "m2": {"released": 3.74, "bounded": [0.0, 1.98], "unquantified": 0}},
            MAIN: {"pcs": {"settled": 1, "held": [0, 0], "no_figure": 0},
                   "m2": {"released": 4.32, "bounded": [0.0, 0.0], "unquantified": 0}},
            WIN: {"pcs": {"settled": 4, "held": [0, 0], "no_figure": 0},
                  "m2": {"released": 6.9, "bounded": [0.72, 0.9], "unquantified": 0}}}


def doc(ops=None, sup=None, declared=True, floors=("GF", "1F")):
    pc = {"piece": "OPENINGS", "item_codes": CODES, "source": src("T-CEN"), "sources": [src("T-HEADS")],
          "scope": {"floors": list(floors), "supersede_lines": sup if sup is not None else supersede(),
                    "other_elements": []},
          "openings": ops if ops is not None else openings(),
          "excluded": [{"id": "P-01", "why": "doorless passage: no supply item"}]}
    if declared:
        pc["declared_totals"] = copy.deepcopy(DECLARED)
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "pieces": [pc]}


def run(d=None, lines=None):
    lines = lines if lines is not None else l309()
    inp = A.load_inputs(d if d is not None else doc(), PID)
    ch, logs = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, logs


def added(out, code, floor, unit):
    return [ln for ln in out if ln["item_code"] == code and ln["location"]["floor"] == floor and ln["unit"] == unit
            and (ln["calculation"]["inputs"] or {}).get("policy") == "OPENINGS_PCS_AND_M2_V1"]


def by_part(out, code, floor, unit):
    return {ln["calculation"]["inputs"]["aggregation_key"]["part"]: ln for ln in added(out, code, floor, unit)}


# ------------------------------------------------------------------------------------------------ normal
def test_villa_k_hand_values_per_type_floor_and_unit():
    _, out, ident, _, logs = run()
    w = by_part(out, WIN, "GF", "m2")
    assert w["SETTLED:DRAWING-CONFIRMED"]["measured_net"] == AP(1.80 + 2.10)
    assert w["SETTLED:DRAWING-CONFIRMED"]["evidence_state"] == "SOURCE_DERIVED"
    assert w["HELD"]["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (w["HELD"]["bounded_range"]["low"], w["HELD"]["bounded_range"]["high"]) == (AP(0.72), AP(0.90))
    assert by_part(out, WIN, "GF", "pcs")["SETTLED:DRAWING-CONFIRMED"]["measured_net"] == 3
    assert by_part(out, WIN, "1F", "m2")["SETTLED:DRAWING-CONFIRMED"]["measured_net"] == AP(3.0)
    a = by_part(out, ALU, "GF", "m2")
    assert a["SETTLED:" + AS]["measured_net"] == AP(2.2)
    assert a["SETTLED:" + AS]["evidence_state"] == "PROVISIONAL"          # owner fallback: never a confirmed number
    assert a["SETTLED:" + AS]["calculation"]["inputs"]["assumptions"] == [Q55]
    assert a["HELD"]["bounded_range"]["low"] == 0 and a["HELD"]["bounded_range"]["high"] == AP(1.98)
    p = by_part(out, PVC, "GF", "m2")
    assert p["SETTLED:" + AS]["measured_net"] == AP(1.76) and p["HELD"]["bounded_range"]["high"] == AP(1.98)
    m = by_part(out, MAIN, "GF", "m2")["SETTLED:DRAWING-CONFIRMED"]
    assert m["measured_net"] == AP(4.32) and m["evidence_state"] == "SOURCE_DERIVED"
    tot = logs[0]["totals"]
    assert tot[WIN]["m2"] == {"released": AP(6.9), "bounded": [AP(0.72), AP(0.9)], "unquantified": 0}
    assert tot[PVC]["pcs"] == {"settled": 2, "held": [0, 1], "no_figure": 0}
    assert ident["replaced"] == 7 and ident["outside_rows_identical_to_v3_0_9"] == 3


def test_double_leaf_is_one_opening_and_one_pcs():
    _, out, *_ = run()
    m = by_part(out, MAIN, "GF", "pcs")["SETTLED:DRAWING-CONFIRMED"]
    assert m["measured_net"] == 1
    assert m["calculation"]["inputs"]["openings"][0]["leaves"] == 2


def test_pcs_and_m2_come_from_the_same_opening_ids():
    _, out, *_ = run()
    assert A.check_same_openings(out) == {ALU: 2, MAIN: 1, PVC: 3, WIN: 4}
    for code in CODES:
        ids = {u: sorted(i for f in ("GF", "1F") for ln in added(out, code, f, u)
                         for i in ln["calculation"]["inputs"]["opening_ids"]) for u in ("pcs", "m2")}
        assert ids["pcs"] == ids["m2"]


def test_engine_count_lines_superseded_by_name_never_summed_beside():
    lines, out, _, ch, logs = run()
    sup = {c["before"]["line_id"]: c["after"] for c in ch if c["action"] == "REPLACE"}
    assert len(sup) == 7
    assert all(x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and x["measured_net"] is None
               for x in sup.values())
    live_pcs = sum(ln["measured_net"] for ln in out if ln["item_code"] == WIN and ln["unit"] == "pcs"
                   and ln["evidence_state"] in ("SOURCE_DERIVED", "PROVISIONAL", "MEASURED"))
    assert live_pcs == 4                                       # 4 windows, not 4 + the 4 engine lines
    assert {s["opening"] for s in logs[0]["scope_lines"]} == {o for *_, o in ENGINE}


def test_unrelated_lines_byte_identical():
    lines, out, *_ = run()
    by = {ln["line_id"]: ln for ln in out}
    for ln in lines[-3:]:
        assert by[ln["line_id"]] == ln


def test_record_order_does_not_change_the_lines():
    _, out1, *_ = run()
    ops = openings()
    random.Random(7).shuffle(ops)
    _, out2, *_ = run(doc(ops))
    assert [BL.dumps([x]) for x in out1] == [BL.dumps([x]) for x in out2]


def test_held_without_a_figure_is_blocked_never_zero():
    ops = openings()
    wc = next(o for o in ops if o["id"] == "WC")
    wc["m2"] = {"state": "UNQUANTIFIED", "evidence_status": "HELD", "reasons": ["count 1 vs 2 (render)"],
                "info": {"area_on_the_drawn_count_m2": 0.81}}
    d = doc(ops)
    d["pieces"][0]["declared_totals"][WIN]["m2"] = {"released": 6.9, "bounded": [0.0, 0.0], "unquantified": 1}
    _, out, *_ = run(d)
    ln = by_part(out, WIN, "GF", "m2")["HELD_NO_FIGURE"]
    assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["bounded_range"] is None
    assert ln["rfi"]["question"]


def test_scorer_reads_m2_for_the_m2_reference_and_no_unit_refusal():
    """acceptance: a reference line in m2 is answered by the m2 lines (no UNIT_MISMATCH); pcs lines stay apart."""
    km = {"keys": [{"key": "WINDOWS.ALUMINIUM", "trade": "WINDOWS", "item_codes": [WIN], "reference_id": "R-W"},
                   {"key": "DOORS.ALUMINIUM", "trade": "DOORS", "item_codes": [ALU], "reference_id": "R-D"}]}
    ref = [{"id": "R-W", "trade": "WINDOWS", "unit": "m2", "qty": 8.0, "key": "WINDOWS.ALUMINIUM"},
           {"id": "R-D", "trade": "DOORS", "unit": "m2", "qty": 2.4, "key": "DOORS.ALUMINIUM"}]
    _, out, *_ = run()
    eng, _ = K.engine_rows(out, None, km)
    res = S.score(eng, ref)
    outc = {ln["ref_id"]: ln["outcome"] for ln in res["lines"]}
    assert outc == {"R-W": S.OUT_HELD, "R-D": S.OUT_HELD}        # held parts keep the whole line HELD (never low)
    before = S.score(K.engine_rows(l309(), None, km)[0], ref)
    assert {ln["ref_id"]: ln["outcome"] for ln in before["lines"]}["R-W"] == S.OUT_UNIT_MISMATCH
    # with every window settled, the m2 line is compared on the sum of width x height
    ops = [o for o in openings() if o["id"] != "WC"]
    d = doc(ops, sup=[s for s in supersede() if s["opening"] != "WC"], declared=False)
    lines = [ln for ln in l309() if ln["location"]["element_id"] != "GF-R1:OP-003"]
    _, out2, *_ = run(d, lines)
    res2 = S.score(K.engine_rows(out2, None, km)[0], ref)
    w = next(ln for ln in res2["lines"] if ln["ref_id"] == "R-W")
    assert w["outcome"] == S.OUT_COMPARED and w["engine_qty"] == AP(6.9)


# ------------------------------------------------------------------------------------------------ adverse
def test_opening_counted_in_pcs_but_missing_from_m2_is_refused():
    _, out, *_ = run()
    bad = copy.deepcopy(out)
    ln = by_part(bad, WIN, "GF", "m2")["SETTLED:DRAWING-CONFIRMED"]
    ln["calculation"]["inputs"]["opening_ids"].remove("WB")
    with pytest.raises(A.InputsError, match="same openings"):
        A.check_same_openings(bad)
    ops = openings()
    del next(o for o in ops if o["id"] == "WB")["m2"]
    with pytest.raises(A.InputsError, match="m2.state"):
        A.load_inputs(doc(ops), PID)


def test_opening_twice_in_one_unit_is_refused():
    _, out, *_ = run()
    bad = copy.deepcopy(out)
    by_part(bad, WIN, "1F", "pcs")["SETTLED:DRAWING-CONFIRMED"]["calculation"]["inputs"]["opening_ids"].append("WA")
    with pytest.raises(A.InputsError):
        A.check_same_openings(bad)
    ops = openings() + [window("WA", "GF", 1.50, 1.20)]
    with pytest.raises(A.InputsError, match="listed twice"):
        A.load_inputs(doc(ops), PID)


def test_double_leaf_counted_twice_is_refused():
    ops = openings()
    next(o for o in ops if o["id"] == "DC")["pcs"]["count"] = 2
    with pytest.raises(A.InputsError, match="double leaf is ONE opening"):
        A.load_inputs(doc(ops), PID)


def test_area_not_width_times_height_is_refused():
    ops = openings()
    next(o for o in ops if o["id"] == "DA")["m2"]["value"] = 2.40          # a height printed nowhere
    with pytest.raises(A.InputsError, match="width x height"):
        A.load_inputs(doc(ops), PID)


def test_millimetres_given_as_metres_are_refused():
    ops = openings()
    o = next(o for o in ops if o["id"] == "WD")
    o["width"]["value"], o["m2"]["value"] = 2000.0, 3000.0
    with pytest.raises(A.InputsError, match="unit slip"):
        A.load_inputs(doc(ops), PID)


def test_assumed_height_needs_its_owner_source_on_the_line():
    ops = openings()
    del next(o for o in ops if o["id"] == "DB")["assumption"]
    with pytest.raises(A.InputsError, match="assumption"):
        A.load_inputs(doc(ops), PID)
    ops = openings()
    next(o for o in ops if o["id"] == "DB")["m2"]["evidence_status"] = DC       # an assumed height shown as drawn
    with pytest.raises(A.InputsError, match="dimensions make it"):
        A.load_inputs(doc(ops), PID)


def test_class_held_opening_is_never_settled_and_starts_from_zero():
    ops = openings()
    dd = next(o for o in ops if o["id"] == "DD")
    dd["pcs"] = {"state": "SETTLED", "count": 1}
    with pytest.raises(A.InputsError, match="class-held"):
        A.load_inputs(doc(ops), PID)
    ops = openings()
    next(o for o in ops if o["id"] == "DD")["pcs"]["range"] = [1, 1]
    with pytest.raises(A.InputsError, match="from 0"):
        A.load_inputs(doc(ops), PID)


def test_opening_settled_in_two_classes_is_refused():
    ops = openings()
    next(o for o in ops if o["id"] == "DE")["classes"] = [PVC, ALU]
    with pytest.raises(A.InputsError, match="class hold"):
        A.load_inputs(doc(ops), PID)


def test_held_dimension_cannot_release_an_area():
    ops = openings()
    wc = next(o for o in ops if o["id"] == "WC")
    wc["m2"] = {"state": "RELEASED", "value": 0.9, "evidence_status": DC}       # the larger end, picked
    with pytest.raises(A.InputsError, match="range is BOUNDED"):
        A.load_inputs(doc(ops), PID)


def test_held_count_never_zero():
    ops = openings()
    next(o for o in ops if o["id"] == "DD")["pcs"]["range"] = [0, 0]
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(doc(ops), PID)


def test_unaccounted_engine_line_is_refused():
    with pytest.raises(A.InputsError, match="only adds is refused"):
        run(doc(sup=supersede()[:-1]))


def test_named_line_the_candidate_lacks_is_refused():
    sup = supersede() + [{"element_id": "DOOR-GF-Z", "floor": "GF", "item_code": PVC, "unit": "pcs", "carried": 1,
                          "opening": "DB", "why": "x"}]
    with pytest.raises(A.InputsError, match="does not have"):
        run(doc(sup=sup))


def test_superseded_figure_must_be_the_lines():
    sup = supersede()
    sup[0]["carried"] = 2
    with pytest.raises(A.InputsError, match="carries"):
        run(doc(sup=sup))


def test_door_line_on_a_floor_outside_the_scope_is_refused():
    lines = l309() + [line("DOOR-2F-X", PVC, "2F")]
    with pytest.raises(A.InputsError, match="outside the scope"):
        run(doc(), lines)


def test_declared_totals_must_match():
    d = doc()
    d["pieces"][0]["declared_totals"][WIN]["m2"]["released"] = 7.0
    with pytest.raises(ValueError, match="declared"):
        run(d)


def test_superseded_line_must_name_an_opening_record():
    sup = supersede()
    sup[0]["opening"] = "D-NONE"
    with pytest.raises(A.InputsError, match="names an opening record"):
        A.load_inputs(doc(sup=sup), PID)
