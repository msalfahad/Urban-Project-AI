"""T-687 ARCH_TAKEOFF_V3.0.69 (PLASTER / PAINT GATE B ROUND 1) on a synthetic villa-K687 candidate (hand fixture, not
the development villa).

Villa K687 by hand (m2):
  SH  stair shaft plaster  HELD 40.00 .. 50.00 -> BOUND 42.50 .. 48.00 (heads applied, returns kept by band)
  SP  stair shaft paint    HELD blank          -> BOUND 41.00 .. 46.00
  W1  GF wet room backing  30.00 (PROVISIONAL, tile backing to H); band L 10.0 x (S 4.29 - H 3.65) = 6.40 (point,
      ASSUMED - OWNER-APPROVED H Q-48 A on a drawn soffit) -> PROVISIONAL 6.40
  W2  1F wet room backing  20.00; band L 8.0, H 3.35, floor S 3.99, roof share 0.5, roof S 3.74 .. 4.04, one beam
      end 0 .. 0.20: low 8 x (0.5 x 0.64 + 0.5 x 0.39) - 0.20 = 3.92, high 8 x (0.32 + 0.345) - 0 = 5.32 (HELD)
  W3  annex wet backing    HELD blank -> BOUND 10.00 .. 14.00; band L 5.0 x 0.59 (S - H fixed on one held datum)
      = 2.95 .. 2.95 HELD (datum-invariant, the datum itself held); joint room total 12.95 .. 16.95 beside
  OP  door reveal          HELD 1.08 .. 1.20 -> VALUE 1.08 (2 x 0.20 x 2.20 + 0.20 x 1.00, Q-55 C)
  AR  arch reveal          HELD blank -> CAUSE (stays blank, cause corrected)
  X   'paint above wall tile' EXCLUDED (a tiled face never carries paint): untouched; MAS.BLOCK 20.00 untouched
Totals: FIN.PLASTER 6 lines, released 50.00, held 41.08 .. 51.20 (2 bounded), 2 blank ->
        9 lines, released 57.48, held 59.37 .. 70.27 (4 bounded), 1 blank;
        FIN.PAINT 1 line blank -> 41.00 .. 46.00 (the excluded line outside the totals both times).
"""
import copy

import pytest

from engine.source import arch_v304 as A304
from engine.source import arch_v3069 as M
from engine.source import boq_line as BL

PID, REV = "villa-k687", "0" * 64
E = {"SH": "HL:WALL_FINISH:ST_K:PLASTER", "SP": "HL:WALL_FINISH:ST_K:PAINT", "W1": "GF-RW1:plaster",
     "W2": "1F-RW2:plaster", "W3": "GF-RW3:plaster", "OP": "GF-OPENING-OP-K1:door jambs and head",
     "AR": "1F-REVEAL-A-K:THROUGH:JAMBS_HEAD:HELD", "X": "GF-RW1:paint above wall tile", "MB": "GF-WALLS:k"}


def mk(key, code, state, net=None, rng=None, floor="GF"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=state,
                        measured_net=net, gross=net, element_id=E[key], floor=floor, formula="synthetic",
                        bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "k"},
                        rule_id="R-X", rule_version="1", notes="k" if state == "EXCLUDED_WITH_REASON" else "",
                        rfi={"question": "open"} if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None)


def lid(key, code):
    return BL.line_id(PID, code, E[key], "R-X", "1", "m2")


def base():
    return [mk("SH", "FIN.PLASTER", "BOUNDED_EXPOSURE", rng=(40.0, 50.0)),
            mk("SP", "FIN.PAINT", "BLOCKED_RFI"),
            mk("W1", "FIN.PLASTER", "PROVISIONAL", 30.0),
            mk("W2", "FIN.PLASTER", "PROVISIONAL", 20.0, floor="1F"),
            mk("W3", "FIN.PLASTER", "BLOCKED_RFI"),
            mk("OP", "FIN.PLASTER", "BOUNDED_EXPOSURE", rng=(1.08, 1.20)),
            mk("AR", "FIN.PLASTER", "BLOCKED_RFI", floor="1F"),
            mk("X", "FIN.PAINT", "EXCLUDED_WITH_REASON"),
            mk("MB", "MAS.BLOCK", "MEASURED", 20.0)]


SRC = [{"task": "T-K1", "file": "k1.json", "sha256": "a" * 64, "merge_commit": "abcdef12", "checker_run": "run 1"},
       {"task": "T-K2", "file": "k2.json", "sha256": "b" * 64, "merge_commit": "bcdef123", "checker_run": "run 2"}]
HELD = {"status": "HELD", "basis": "geometry drawn; build-up held"}


def restate():
    return [
        {"line_id": lid("SH", "FIN.PLASTER"), "item_code": "FIN.PLASTER", "action": "BOUND",
         "expect": {"class": "HELD", "low": 40.0, "high": 50.0}, "after": {"low": 42.5, "high": 48.0},
         "basis": "shaft band", "status": HELD, "still_open": ["build-up b"], "source_tasks": ["T-K1"]},
        {"line_id": lid("SP", "FIN.PAINT"), "item_code": "FIN.PAINT", "action": "BOUND",
         "expect": {"class": "HELD", "low": None, "high": None}, "after": {"low": 41.0, "high": 46.0},
         "basis": "shaft band paint", "status": HELD, "still_open": ["build-up b"], "source_tasks": ["T-K1"]},
        {"line_id": lid("W3", "FIN.PLASTER"), "item_code": "FIN.PLASTER", "action": "BOUND",
         "expect": {"class": "HELD", "low": None, "high": None}, "after": {"low": 10.0, "high": 14.0},
         "basis": "annex backing", "status": HELD, "still_open": ["annex slab top"], "source_tasks": ["T-K2"]},
        {"line_id": lid("OP", "FIN.PLASTER"), "item_code": "FIN.PLASTER", "action": "VALUE",
         "expect": {"class": "HELD", "low": 1.08, "high": 1.20}, "after": {"value": 1.08},
         "basis": "2 x 0.20 x 2.20 + 0.20 x 1.00",
         "status": {"status": "ASSUMED - OWNER-APPROVED", "source": "Q-55 C", "basis": "door height fallback"},
         "source_tasks": ["T-K1"]},
        {"line_id": lid("AR", "FIN.PLASTER"), "item_code": "FIN.PLASTER", "action": "CAUSE",
         "expect": {"class": "HELD", "low": None, "high": None}, "after": {}, "basis": "arch reveal",
         "status": {"status": "HELD", "basis": "spring not printed"}, "corrected_cause": "drawn 1.00 x 0.15; rise "
         "printed nowhere", "source_tasks": ["T-K1"]}]


def bands():
    return [
        {"engine_room": "GF-RW1", "room": "W1", "backing_line_id": lid("W1", "FIN.PLASTER"), "face_length_m": 10.0,
         "H_m": 3.65, "S_floor_m": 4.29, "S_roof_m": None, "under_roof_share": 0.0, "deducted_m2": [0.0, 0.0],
         "low": 6.4, "high": 6.4, "openings_in_band": [], "source_tasks": ["T-K2"], "still_open": None,
         "status": {"status": "ASSUMED - OWNER-APPROVED", "source": "Q-48 A", "basis": "H on a drawn soffit"}},
        {"engine_room": "1F-RW2", "room": "W2", "backing_line_id": lid("W2", "FIN.PLASTER"), "face_length_m": 8.0,
         "H_m": 3.35, "S_floor_m": 3.99, "S_roof_m": [3.74, 4.04], "under_roof_share": 0.5, "deducted_m2": [0.0, 0.2],
         "low": 3.92, "high": 5.32, "openings_in_band": ["W-K"], "source_tasks": ["T-K2"],
         "still_open": "roof build-up", "status": {"status": "HELD", "basis": "roof build-up not printed"}},
        {"engine_room": "GF-RW3", "room": "W3", "backing_line_id": lid("W3", "FIN.PLASTER"), "face_length_m": 5.0,
         "H_m": [2.5, 3.2], "S_m": [3.09, 3.79], "gross_m2": [2.95, 2.95], "joint_total_m2": [12.95, 16.95],
         "low": 2.95, "high": 2.95, "openings_in_band": [], "source_tasks": ["T-K2"], "still_open": "annex datum",
         "status": {"status": "HELD", "basis": "annex datum held"}}]


EXPECT = {"FIN.PLASTER|m2": {"lines": 9, "released": 57.48, "held_low": 59.37, "held_high": 70.27, "bounded_lines": 4,
                             "blocked_lines": 1},
          "FIN.PAINT|m2": {"lines": 1, "released": 0.0, "held_low": 41.0, "held_high": 46.0, "bounded_lines": 1,
                           "blocked_lines": 0}}


def doc(**kw):
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "restate": restate(), "bands": bands(),
         "expect_totals": EXPECT}
    d.update(kw)
    return copy.deepcopy(d)


def run(d=None, b=None, tmp=None):
    b = base() if b is None else b
    inp = M.load_inputs(d or doc(), PID)
    ch, log = M.changes_for(inp, b)
    new, ident = M.integrate(b, ch)
    return b, ch, log, new, ident


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


def test_normal_hand_figures():
    b, ch, log, new, ident = run()
    n = by_eid(new)
    assert n[E["SH"]]["bounded_range"]["low"] == 42.5 and n[E["SH"]]["bounded_range"]["high"] == 48.0
    assert n[E["SP"]]["evidence_state"] == "BOUNDED_EXPOSURE" and n[E["SP"]]["bounded_range"]["high"] == 46.0
    assert n[E["OP"]]["evidence_state"] == "PROVISIONAL" and n[E["OP"]]["measured_net"] == 1.08
    assert n[E["AR"]]["evidence_state"] == "BLOCKED_RFI" and n[E["AR"]]["measured_net"] is None
    assert "1.00 x 0.15" in n[E["AR"]]["rfi"]["question"]
    w1 = n["GF-RW1" + M.BAND_SUFFIX]
    assert w1["evidence_state"] == "PROVISIONAL" and w1["measured_net"] == 6.4 and w1["item_code"] == "FIN.PLASTER"
    w2 = n["1F-RW2" + M.BAND_SUFFIX]
    assert (w2["bounded_range"]["low"], w2["bounded_range"]["high"]) == (3.92, 5.32)
    w3 = n["GF-RW3" + M.BAND_SUFFIX]
    assert (w3["bounded_range"]["low"], w3["bounded_range"]["high"]) == (2.95, 2.95)
    rec = w3["calculation"]["inputs"][M.REC_KEY]
    assert rec["joint_total_beside_m2"] == [12.95, 16.95] and rec["backing_line_id"] == lid("W3", "FIN.PLASTER")
    assert n[E["W1"]] == by_eid(b)[E["W1"]] and n[E["X"]] == by_eid(b)[E["X"]] and n[E["MB"]] == by_eid(b)[E["MB"]]
    assert ident["replaced"] == 5 and ident["added"] == 3 and ident["outside_rows"] == len(b) - 5
    assert ident["finishes"] == {"BOUND": 3, "VALUE": 1, "CAUSE": 1, "band_value": 1, "band_bound": 2}
    assert log["bands"] == {"VALUE": 1, "BOUND": 2}


def test_totals_by_hand(tmp_path):
    b, ch, log, new, ident = run()
    t0, t1 = A304.code_totals(b), A304.code_totals(new)
    assert t0["FIN.PLASTER|m2"] == {"lines": 6, "released": 50.0, "held_low": 41.08, "held_high": 51.2,
                                    "bounded_lines": 2, "blocked_lines": 2}
    for k, z in EXPECT.items():
        for f, v in z.items():
            assert abs(t1[k][f] - v) < 1e-6, (k, f)
    assert t1["MAS.BLOCK|m2"] == t0["MAS.BLOCK|m2"]
    names, ident2, led = M.write(tmp_path, b, ch, log, None, (), EXPECT)
    assert "V3_0_69_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident2["diff"]["vs_base"] == {"SAME": 4, "CHANGED": 5, "ADDED": 3}


def test_mirror_order_same_lines():
    d = doc(restate=list(reversed(restate())), bands=list(reversed(bands())))
    _b, _c, _l, new2, _i = run(d)
    _b, _c, _l, new1, _i = run()
    assert sorted(BL.dumps([x]) for x in new1) == sorted(BL.dumps([x]) for x in new2)


def test_band_figure_recomputed():
    assert M.band_figure(bands()[1]) == (3.92, 5.32)
    assert M.band_figure(bands()[0]) == (6.4, 6.4)


@pytest.mark.parametrize("mut, msg", [
    (lambda d: d["restate"][0]["expect"].update(high=51.0), "started from"),
    (lambda d: d["restate"][3]["after"].update(value=1.30), "inside"),
    (lambda d: d["restate"][3].update(status={"status": "HELD", "basis": "x"}), "ASSUMED"),
    (lambda d: d["restate"][4].update(after={"value": 1.0}), "blank"),
    (lambda d: d["restate"][0].update(status={"status": "VERIFIED", "basis": "x"}), "never VERIFIED"),
    (lambda d: d["restate"][0].update(item_code="STR.CONC.BEAM"), "FIN.PLASTER / FIN.PAINT"),
    (lambda d: d["restate"][1]["after"].update(low=0.0), "0 < low"),
    (lambda d: d["restate"][1]["after"].update(low=46.0), "a point is a VALUE"),
    (lambda d: d["restate"].append(copy.deepcopy(d["restate"][0])), "named twice"),
    (lambda d: d["bands"][1].update(high=5.40), "recomputed"),
    (lambda d: d["bands"][1].update(face_length_m=8000.0), "recomputed"),         # millimetres as metres
    (lambda d: d["bands"][0].update(low=0.0, high=0.0), "low <="),                # blank is never 0
    (lambda d: d["bands"][1].update(status={"status": "ASSUMED - OWNER-APPROVED", "source": "Q", "basis": "x"}),
     "only as a point"),
    (lambda d: d["bands"][2].update(still_open=None), "names its open datum"),
    (lambda d: d["bands"][2].update(gross_m2=[2.95, 3.50]), "gross high"),
    (lambda d: d["bands"].append(copy.deepcopy(d["bands"][0])), "two band lines"),
    (lambda d: d["bands"][1].update(under_roof_share=0.5, S_roof_m=None), "roof soffit"),
    (lambda d: d.update(schema="X"), "schema"),
])
def test_adverse_inputs_refused(mut, msg):
    d = doc()
    mut(d)
    with pytest.raises(M.InputsError, match=msg):
        run(d)


def test_hold_ledger_backing_form():
    """a room whose backing line carries the hold-ledger element form HL:WALL_FINISH:<room>:PLASTER is its own room's
    line (development villa GF-07); another room's HL line is not."""
    ln = {"location": {"element_id": "HL:WALL_FINISH:GF_07:PLASTER"}}
    assert M.room_line(ln, "GF-RC06FED", "GF-07")
    assert not M.room_line(ln, "GF-RC06FED", "GF-08")
    assert not M.room_line({"location": {"element_id": "HL:WALL_FINISH:GF_07:PAINT"}}, "GF-RC06FED", "GF-07")


def test_adverse_backing_lines():
    d = doc()
    d["bands"][0]["backing_line_id"] = lid("W2", "FIN.PLASTER")                    # another room's line
    with pytest.raises(M.InputsError, match="not this room's line"):
        run(d)
    d = doc()
    d["bands"][0]["backing_line_id"] = lid("X", "FIN.PAINT")                       # the excluded paint line
    with pytest.raises(M.InputsError, match="not a candidate FIN.PLASTER"):
        run(d)
    b = base()
    b[2] = mk("W1", "FIN.PLASTER", "EXCLUDED_WITH_REASON")
    with pytest.raises(M.InputsError, match="excluded backing"):
        run(None, b)


def test_adverse_released_line_and_twice():
    b = base()
    b[0] = mk("SH", "FIN.PLASTER", "MEASURED", 45.0)                                # a valued line is not restated
    with pytest.raises(M.InputsError, match="HELD"):
        run(None, b)
    _b, _c, _l, new, _i = run()
    with pytest.raises(M.InputsError, match="applied once"):
        M.changes_for(M.load_inputs(doc(), PID), new)


def test_adverse_totals_and_stray_change(tmp_path):
    b, ch, log, new, ident = run()
    bad = dict(EXPECT, **{"FIN.PAINT|m2": dict(EXPECT["FIN.PAINT|m2"], held_high=47.0)})
    with pytest.raises(ValueError, match="not the inputs'"):
        M.write(tmp_path, b, ch, log, None, (), bad)
    stray = copy.deepcopy(ch)
    mb = copy.deepcopy(by_eid(b)[E["MB"]])
    stray.append({"piece": M.P_FIN, "action": "CHANGE", "before": by_eid(b)[E["MB"]], "after": mb})
    with pytest.raises(ValueError, match="not a code this version may touch"):
        M.integrate(b, stray)


def test_tiled_face_keeps_no_paint():
    """adverse (task acceptance): a wet-room face keeps no paint: the excluded 'paint above wall tile' line is never
    restated, and no band is ever a FIN.PAINT line."""
    d = doc()
    d["restate"].append({"line_id": lid("X", "FIN.PAINT"), "item_code": "FIN.PAINT", "action": "BOUND",
                         "expect": {"class": "HELD", "low": None, "high": None}, "after": {"low": 1.0, "high": 2.0},
                         "basis": "x", "status": HELD, "still_open": ["x"], "source_tasks": ["T-K1"]})
    with pytest.raises(M.InputsError, match="not a HELD"):
        run(d)
    _b, ch, _l, new, _i = run()
    assert all(ln["item_code"] == "FIN.PLASTER" for ln in new if ln["location"]["element_id"].endswith(M.BAND_SUFFIX))
    assert by_eid(new)[E["X"]]["evidence_state"] == "EXCLUDED_WITH_REASON"


def test_policy_record():
    p = M.policy_record()
    assert p["released_default"] is False and p["extends"] == "ARCH_TAKEOFF_V3.0.68" and set(p["codes"]) == {
        "FIN.PLASTER", "FIN.PAINT"}
