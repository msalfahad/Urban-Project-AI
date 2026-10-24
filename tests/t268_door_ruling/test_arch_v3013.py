"""T-268: ARCH_TAKEOFF_V3.0.13 door-ruling piece on a hand-calculated villa that is not the development villa (K-268).

Villa K-268, V3.0.10-style door / window lines (one opening list, pcs AND m2), head 2.20 Q-55 C where none printed:
  DA  GF aluminium, settled, 0.90 x 2.20 = 1.980
  DB  GF class held ALUMINIUM / MAIN ENTRANCE, 1.00 x 2.20             -> ruled ALUMINIUM, 1.000 (VERIFIED)
  DC  GF class held ALUMINIUM / PVC,           1.00 x 2.20             -> ruled ALUMINIUM, 1.000
  DD  GF aluminium, width held 0.90 .. 1.00 (leaf frame vs masonry)    -> ruled 0.900 (frame is a symbol)
  DE  GF PVC, width held 0.69 .. 0.80                                  -> not ruled: stays HELD
  DF  GF main entrance, held, 2.00 x 2.50 printed                      -> not ruled: stays HELD
  DG  1F PVC, settled, 0.80 x 2.20 = 1.760
  W1  GF window 1.50 x 1.20 = 1.800 (outside the piece: byte-identical)
By hand after the ruling:
  ALU  GF pcs 4 (DA DB DC DD), m2 1.980 + 2.200 + 2.200 + 1.980 = 8.360; the GF held ALU lines (pcs [0, 3], m2
       [0 + 0 + 1.98, 2.2 + 2.2 + 2.2] = [1.980, 6.600]) retired, figures kept as information;
  PVC  GF held pcs [0 + 1, 1 + 1] = [1, 2] -> [1, 1]; m2 [0 + 1.518, 2.200 + 1.760] = [1.518, 3.960] -> [1.518, 1.760];
       1F settled 1 / 1.760 unchanged (byte-identical);
  MAIN GF held pcs [0 + 1, 1 + 1] -> [1, 1]; m2 [0 + 5.000, 2.200 + 5.000] = [5.000, 7.200] -> [5.000, 5.000].
"""

from __future__ import annotations

import copy

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3013 as A

ALU, PVC, MAIN, WIN = "DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "ARCH.WINDOW"
DOORS = [ALU, PVC, MAIN]
AS, DC = "ASSUMED - OWNER-APPROVED", "DRAWING-CONFIRMED"
Q55 = "Q-55 C: door head 2.20 where no sheet prints one"
SRC = {"file": "research/fx/OPENINGS_FX.csv", "sha256": "1" * 64, "task": "T-FX", "merge_commit": "fx00001",
       "checker_run": "Verifier fixture"}
RSRC = {"file": "research/fx/RULING_FX.csv", "sha256": "2" * 64, "task": "T-FXR", "merge_commit": "fx00002",
        "checker_run": "Verifier fixture 2"}
PID, REV = "K-268", "3" * 64
H22 = {"value": 2.2, "status": AS, "source": Q55}


def _door(oid, floor, classes, width, pcs, m2, height=None, **kw):
    o = {"id": oid, "kind": "DOOR", "floor": floor, "classes": classes, "leaves": 1,
         "opening_definition": "structural opening between the jambs", "sources": [SRC],
         "width": width, "height": height or dict(H22), "pcs": pcs, "m2": m2}
    if (height or H22)["status"] == AS:
        o["assumption"] = Q55
    o.update(kw)
    return o


def openings():
    w = lambda v: {"value": v, "status": DC, "source": "jambs"}  # noqa: E731
    held = "class held: checker to rule"
    return [
        _door("DA", "GF", [ALU], w(0.9), {"state": "SETTLED", "count": 1},
              {"state": "RELEASED", "value": 1.98, "evidence_status": AS}),
        _door("DB", "GF", [ALU, MAIN], w(1.0), {"state": "HELD", "range": [0, 1], "reasons": [held]},
              {"state": "BOUNDED", "range": [0.0, 2.2], "evidence_status": "HELD", "reasons": [held],
               "range_basis": "class held"}, class_hold=held),
        _door("DC", "GF", [ALU, PVC], w(1.0), {"state": "HELD", "range": [0, 1], "reasons": [held]},
              {"state": "BOUNDED", "range": [0.0, 2.2], "evidence_status": "HELD", "reasons": [held],
               "range_basis": "class held"}, class_hold=held),
        _door("DD", "GF", [ALU], {"range": [0.9, 1.0], "status": DC, "source": "frame vs masonry"},
              {"state": "HELD", "range": [1, 1], "reasons": ["width review"]},
              {"state": "BOUNDED", "range": [1.98, 2.2], "evidence_status": "HELD", "reasons": ["width review"]}),
        _door("DE", "GF", [PVC], {"range": [0.69, 0.8], "status": DC, "source": "leaf vs closure"},
              {"state": "HELD", "range": [1, 1], "reasons": ["width review"]},
              {"state": "BOUNDED", "range": [1.518, 1.76], "evidence_status": "HELD", "reasons": ["width review"]}),
        _door("DF", "GF", [MAIN], w(2.0), {"state": "HELD", "range": [1, 1], "reasons": ["designer item"]},
              {"state": "BOUNDED", "range": [5.0, 5.0], "evidence_status": "HELD", "reasons": ["designer item"]},
              height={"value": 2.5, "status": DC, "source": "printed 2.50"}),
        _door("DG", "1F", [PVC], w(0.8), {"state": "SETTLED", "count": 1},
              {"state": "RELEASED", "value": 1.76, "evidence_status": AS}),
        {"id": "W1", "kind": "WINDOW", "floor": "GF", "classes": [WIN], "leaves": 1, "sources": [SRC],
         "opening_definition": "opening line", "width": w(1.5), "height": {"value": 1.2, "status": DC, "source": "p"},
         "pcs": {"state": "SETTLED", "count": 1}, "m2": {"state": "RELEASED", "value": 1.8, "evidence_status": DC}},
    ]


def v3010_lines(recs=None):
    pc = {"piece": "OPENINGS", "item_codes": DOORS + [WIN], "source": SRC, "scope": {"floors": ["GF", "1F"]},
          "openings": recs or openings()}
    for o in pc["openings"]:
        A3010._check_opening(o, pc["item_codes"], ["GF", "1F"])
    groups = A3010.group_openings(pc)
    return [A3010.group_line(PID, REV, [], pc, k, groups[k])[0] for k in sorted(groups)]


def ruled(oid, cls, width, held_in, census=None, **kw):
    base = {o["id"]: o for o in openings()}[oid]
    o = copy.deepcopy(base)
    o.pop("class_hold", None)
    o.update(classes=[cls])
    o["width"] = {"value": width, "status": "VERIFIED", "verified_by": "Verifier fixture 2", "source": "both faces"}
    o["pcs"] = {"state": "SETTLED", "count": 1}
    o["m2"] = {"state": "RELEASED", "value": round(width * o["height"]["value"], 4), "evidence_status": AS}
    r = {"id": oid, "ruled_class": cls, "held_in": held_in, "verdict": f"{oid} ruled", "verified_by": "Verifier fx2",
         "census_width": width if census is None else census, "record": o}
    r.update(kw)
    return r


DECLARED = {ALU: {"pcs": {"settled": 4.0, "held": [0.0, 0.0], "no_figure": 0},
                  "m2": {"released": 8.36, "bounded": [0.0, 0.0], "unquantified": 0}},
            PVC: {"pcs": {"settled": 1.0, "held": [1.0, 1.0], "no_figure": 0},
                  "m2": {"released": 1.76, "bounded": [1.518, 1.76], "unquantified": 0}},
            MAIN: {"pcs": {"settled": 0.0, "held": [1.0, 1.0], "no_figure": 0},
                   "m2": {"released": 0.0, "bounded": [5.0, 5.0], "unquantified": 0}}}


def rulings():
    return [ruled("DB", ALU, 1.0, [ALU, MAIN]), ruled("DC", ALU, 1.0, [ALU, PVC]), ruled("DD", ALU, 0.9, [ALU])]


def inputs(rs=None, declared=None):
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "pieces": [{"piece": "DOOR_RULING", "item_codes": DOORS, "source": RSRC, "sources": [SRC],
                        "base": {"task": SRC["task"], "merge_commit": SRC["merge_commit"]},
                        "scope": {"floors": ["GF", "1F"]}, "rulings": rulings() if rs is None else rs,
                        "declared_totals": DECLARED if declared is None else declared}]}


def run(inp=None, lines=None):
    lines = v3010_lines() if lines is None else lines
    inp = A.load_inputs(inputs() if inp is None else inp, PID)
    earlier = {ln["line_id"] for ln in lines}
    ch, logs = A.changes_for(inp, lines, earlier)
    out, ident = A.integrate(lines, ch)
    return lines, ch, logs, out, ident


def _by(lines, code, floor, unit, part):
    hit = [ln for ln in lines if ln["item_code"] == code and ln["unit"] == unit
           and ln["calculation"]["inputs"]["aggregation_key"]["floor"] == floor
           and ln["calculation"]["inputs"]["aggregation_key"]["part"] == part]
    assert len(hit) == 1, (code, floor, unit, part, len(hit))
    return hit[0]


# ---------------------------------------------------------------------------------------------------- normal case
def test_hand_figures_after_the_ruling():
    l10, ch, logs, out, ident = run()
    s = A.door_summary(out)
    assert s[ALU]["pcs"]["settled"] == 4 and s[ALU]["m2"]["settled"] == pytest.approx(8.36, abs=1e-9)
    assert s[ALU]["m2"]["settled_ids"] == ["DA", "DB", "DC", "DD"] == s[ALU]["pcs"]["settled_ids"]
    assert s[ALU]["m2"]["held_ids"] == [] and s[ALU]["m2"]["low"] == s[ALU]["m2"]["high"] == 0
    assert s[PVC]["m2"]["low"] == pytest.approx(1.518) and s[PVC]["m2"]["high"] == pytest.approx(1.76)
    assert s[PVC]["pcs"]["low"] == 1 and s[PVC]["pcs"]["high"] == 1 and s[PVC]["m2"]["held_ids"] == ["DE"]
    assert s[MAIN]["m2"]["low"] == pytest.approx(5.0) and s[MAIN]["m2"]["high"] == pytest.approx(5.0)
    assert s[MAIN]["pcs"]["held_ids"] == ["DF"]
    b = A.door_summary(l10)
    assert b[ALU]["m2"]["settled"] == pytest.approx(1.98)
    assert [b[ALU]["m2"]["low"], b[ALU]["m2"]["high"]] == pytest.approx([1.98, 6.6])
    assert [b[PVC]["m2"]["low"], b[PVC]["m2"]["high"]] == pytest.approx([1.518, 3.96])
    assert [b[MAIN]["m2"]["low"], b[MAIN]["m2"]["high"]] == pytest.approx([5.0, 7.2])


def test_settled_alu_line_keeps_its_id_and_is_owner_approved_provisional():
    l10, ch, logs, out, ident = run()
    old = _by(l10, ALU, "GF", "m2", f"SETTLED:{AS}")
    new = _by(out, ALU, "GF", "m2", f"SETTLED:{AS}")
    assert old["line_id"] == new["line_id"] and new["measured_net"] == pytest.approx(8.36)
    assert new["evidence_state"] == "PROVISIONAL"      # heads rest on Q-55 C, never shown as measured
    assert Q55 in new["calculation"]["inputs"]["assumptions"]
    assert {x["id"] for x in new["calculation"]["inputs"]["ruled_openings"]} == {"DB", "DC", "DD"}
    pcs = _by(out, ALU, "GF", "pcs", "SETTLED:DRAWING-CONFIRMED")
    assert pcs["measured_net"] == 4 and pcs["evidence_state"] == "SOURCE_DERIVED"


def test_emptied_held_lines_are_retired_never_zero():
    l10, ch, logs, out, ident = run()
    for unit in ("pcs", "m2"):
        old = _by(l10, ALU, "GF", unit, "HELD")
        new = {ln["line_id"]: ln for ln in out}[old["line_id"]]
        assert new["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and new["measured_net"] is None
        assert "RETIRED" in new["notes"]
    acts = sorted((x["key"]["item_code"], x["key"]["unit"], x["key"]["part"], x["action"]) for x in logs[0]["lines"])
    assert acts == sorted([(ALU, "m2", "HELD", "REPLACE"), (ALU, "pcs", "HELD", "REPLACE"),
                           (ALU, "m2", f"SETTLED:{AS}", "REPLACE"), (ALU, "pcs", "SETTLED:DRAWING-CONFIRMED", "REPLACE"),
                           (PVC, "m2", "HELD", "REPLACE"), (PVC, "pcs", "HELD", "REPLACE"),
                           (MAIN, "m2", "HELD", "REPLACE"), (MAIN, "pcs", "HELD", "REPLACE")])


def test_every_other_line_byte_identical_and_same_openings():
    l10, ch, logs, out, ident = run()
    assert ident["replaced"] == 8 and ident["added"] == 0
    by = {ln["line_id"]: ln for ln in l10}
    touched = {c["after"]["line_id"] for c in ch}
    same = [ln for ln in out if ln["line_id"] not in touched]
    assert same and all(A30.line_sha(by[ln["line_id"]]) == A30.line_sha(ln) for ln in same)
    assert {ln["item_code"] for ln in same} >= {WIN, PVC}       # the window and the 1F PVC lines untouched
    assert A3010.check_same_openings(out)[ALU] == 4


def test_ruling_order_never_changes_a_line():
    a = run()[3]
    b = run(inputs(rs=list(reversed(rulings()))))[3]
    assert [A30.line_sha(x) for x in a] == [A30.line_sha(x) for x in b]


def test_new_group_is_added_when_the_class_has_no_line_on_that_floor():
    rs = [ruled("DC", PVC, 1.0, [ALU, PVC])]
    decl = {PVC: {"pcs": {"settled": 2.0, "held": [1.0, 1.0], "no_figure": 0},
                  "m2": {"released": 3.96, "bounded": [1.518, 1.76], "unquantified": 0}}}
    l10, ch, logs, out, ident = run(inputs(rs=rs, declared=decl))
    assert ident["added"] == 2                                 # PVC GF settled pcs + m2 did not exist
    assert _by(out, PVC, "GF", "m2", f"SETTLED:{AS}")["measured_net"] == pytest.approx(2.2)


# ---------------------------------------------------------------------------------------------------- adverse cases
def test_adverse_ruling_a_settled_door_refused():
    rs = rulings() + [ruled("DA", ALU, 0.9, [ALU])]
    with pytest.raises(A.InputsError, match="ruled once"):
        run(inputs(rs=rs))


def test_adverse_held_in_mismatch_refused():
    rs = [ruled("DB", ALU, 1.0, [ALU])] + rulings()[1:]
    with pytest.raises(A.InputsError, match="holds it in"):
        run(inputs(rs=rs))


def test_adverse_ruling_without_a_checker_run_refused():
    rs = rulings()
    rs[0]["verified_by"] = ""
    with pytest.raises(A.InputsError, match="verified_by"):
        A.load_inputs(inputs(rs=rs), PID)


def test_adverse_verified_width_without_its_checker_run_refused():
    rs = rulings()
    rs[0]["record"]["width"].pop("verified_by")
    with pytest.raises(A.InputsError, match="VERIFIED width"):
        A.load_inputs(inputs(rs=rs), PID)


def test_adverse_width_differs_from_census_without_downstream_refused():
    rs = rulings()
    rs[2]["census_width"] = 1.0                                # deductions carry 1.00, ruled 0.90
    with pytest.raises(A.InputsError, match="deduction change"):
        A.load_inputs(inputs(rs=rs), PID)
    rs[2]["downstream"] = [{"task": "T-FXD", "what": "masonry deduction 1.00 -> 0.90"}]
    A.load_inputs(inputs(rs=rs), PID)                          # named, never applied here


def test_adverse_width_outside_the_held_range_needs_why():
    rs = rulings()[:2] + [ruled("DD", ALU, 1.2, [ALU])]
    decl = copy.deepcopy(DECLARED)
    decl[ALU]["m2"]["released"] = round(8.36 - 1.98 + 2.64, 4)
    with pytest.raises(A.InputsError, match="outside the held range"):
        run(inputs(rs=rs, declared=decl))
    rs[2]["outside_range_why"] = "fixture: both faces measure 1.20"
    run(inputs(rs=rs, declared=decl))


def test_adverse_unit_slip_mm_as_m_refused():
    rs = rulings()
    rs[0]["record"]["width"]["value"] = 1000.0
    rs[0]["record"]["m2"]["value"] = 2200.0
    rs[0]["census_width"] = 1000.0
    with pytest.raises(A.InputsError, match="unit slip"):
        A.load_inputs(inputs(rs=rs), PID)


def test_adverse_head_moved_by_a_ruling_refused():
    rs = rulings()
    rs[0]["record"]["height"] = {"value": 2.4, "status": DC, "source": "freelancer 2.40"}
    rs[0]["record"]["m2"] = {"state": "RELEASED", "value": 2.4, "evidence_status": DC}
    rs[0]["record"].pop("assumption", None)
    with pytest.raises(A.InputsError, match="never moves the head"):
        run(inputs(rs=rs))


def test_adverse_two_classes_in_a_ruling_refused():
    rs = rulings()
    rs[0]["record"]["classes"] = [ALU, MAIN]
    with pytest.raises(A.InputsError, match="ONE class"):
        A.load_inputs(inputs(rs=rs), PID)


def test_adverse_unknown_door_refused():
    rs = rulings()
    rs[0] = dict(rs[0], id="DZ", record=dict(rs[0]["record"], id="DZ"))
    with pytest.raises(A.InputsError, match="holds it in"):
        run(inputs(rs=rs))


def test_adverse_declared_totals_mismatch_refused():
    decl = copy.deepcopy(DECLARED)
    decl[ALU]["m2"]["released"] = 12.0                         # e.g. the freelancer's figure
    with pytest.raises(ValueError, match="totals"):
        run(inputs(declared=decl))


def test_adverse_tampered_candidate_line_refused():
    lines = v3010_lines()
    ln = _by(lines, ALU, "GF", "m2", f"SETTLED:{AS}")
    ln["measured_net"] = 2.5                                   # a line that is not the V3.0.10 line of its table
    with pytest.raises(A.InputsError, match="not reproduced"):
        run(lines=lines)


def test_adverse_earlier_change_must_be_named_by_the_engine_not_silently():
    lines = v3010_lines()
    inp = A.load_inputs(inputs(), PID)
    ch, _ = A.changes_for(inp, lines, set())                  # no earlier change: still a clean replace
    assert all(c["action"] in ("REPLACE", "ADD") for c in ch)
    for c in ch:
        if c["action"] == "REPLACE":
            assert "EARLIER_CHANGE" in c["codes"]


def test_no_inputs_changes_nothing():
    lines = v3010_lines()
    ch, logs = A.changes_for(None, lines, set())
    out, ident = A.integrate(lines, ch)
    assert ident["replaced"] == ident["added"] == 0 and logs[0]["state"] == "NO_PROJECT_INPUT"
