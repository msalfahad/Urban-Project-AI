"""T-480 ARCH_TAKEOFF_V3.0.54 on a synthetic villa-D candidate (hand fixture, not the development villa): B7-09 railing
runs valued along the pitch line flight by flight; reader lines retired; held / unknown pieces blank by name; every other
candidate line byte-identical; adverse inputs refused.

Villa D by hand (dog-leg stair GF -> 1F, rail on the well side only; the wall side has no rail drawn):
  RL-01 F1  8 goings x 0.280 = 2.240 plan, 8 x 0.175 = 1.400 rise: hypot = sqrt(5.0176 + 1.96) = 2.641515 lm
        LD  half-landing well edge, level: 1.100 lm
        F2  9 x 0.280 = 2.520 plan, 9 x 0.175 = 1.575 rise: sqrt(6.3504 + 2.480625) = 2.971704 lm
        T-LD the rail over the landing turn: profile not drawn -> HELD blank by name (own line), never 0
        run figure = 2.641515 + 1.100 + 2.971704 = 6.713219 lm (PROVISIONAL)
  RL-02 roof-stair guard already valued 3.000 lm; census 3.0004 (level) AGREE within 0.0005 -> unchanged
  RL-03 garden steps: rise not printed -> HELD; run line stays blank (KEEP)
  U1    a band beside F1 whose rail existence is not drawn -> UNKNOWN, own blank line
  readers GF-RA flight 1 (= F1), GF-RA flight 2 (= F2), 1F-RB flight 1 (= F2 seen through the void): all retired to RL-01
  B7-09 total 3.000 -> 9.713219 lm (+6.713219)."""
import copy

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v3030 as A3030
from engine.source import arch_v304 as A304
from engine.source import arch_v3054 as M
from engine.source import boq_line as BL

PID, REV = "villa-d-t480", "0" * 64


def mk(eid, code, unit, state, net=None, floor="GF", run=None, treads=None):
    inputs = {A3030.REC_KEY: {"policy": "SYNTHETIC_METALWORK_V1", "run": run}} if run else {}
    if treads:
        inputs["treads"] = treads
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor=floor, formula="synthetic", rule_id="R-X",
                        rule_version="1", item_en=code, item_ar=code, inputs=inputs,
                        rfi={"question": "rail not measured"} if state == "BLOCKED_RFI" else None)


def candidate():
    return [mk("GF-WALLS:t=0.20", "MAS.BLOCK", "m2", "SOURCE_DERIVED", 40.0),
            mk("RAIL:RL-01", "FIN.RAILING", "lm", "BLOCKED_RFI", run="RL-01"),
            mk("RAIL:RL-02", "FIN.RAILING", "lm", "MEASURED", 3.0, floor="RF", run="RL-02"),
            mk("RAIL:RL-03", "FIN.RAILING", "lm", "BLOCKED_RFI", run="RL-03"),
            mk("GF-RA:flight 1", "FIN.RAILING", "lm", "BLOCKED_RFI", treads=8),
            mk("GF-RA:flight 2", "FIN.RAILING", "lm", "BLOCKED_RFI", treads=9),
            mk("1F-RB:flight 1", "FIN.RAILING", "lm", "BLOCKED_RFI", floor="1F", treads=9),
            mk("GF-RC:flight 1", "FIN.RAILING", "lm", "BLOCKED_RFI", treads=3)]   # another stair's F1 on GF


SRC = [{"task": "T-D", "file": "flight_census.csv", "sha256": "d" * 64, "merge_commit": "abcdef12",
        "checker_run": "run d"}]


def P(pid, kind, status, plan=None, rise=None, length=None, missing=None, **kw):
    p = {"piece_id": pid, "stair": "ST-D", "flight": pid.split(":")[-1], "side": "well", "kind": kind,
         "status": status, "plan_m": plan, "rise_m": rise, "length_lm": length, "source": "villa D plan + section"}
    if missing:
        p["missing"] = missing
    p.update(kw)
    return p


def doc(c, **over):
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC,
         "runs": [{"run": "RL-01", "action": "VALUE", "source_tasks": ["T-D"],
                   "pieces": [P("ST-D:F1", "INCLINED", "DRAWING-CONFIRMED", 2.24, 1.4, 2.641515),
                              P("ST-D:LD", "HORIZONTAL", "DRAWING-CONFIRMED", 1.1, 0.0, 1.1),
                              P("ST-D:F2", "INCLINED", "DRAWING-CONFIRMED", 2.52, 1.575, 2.971704),
                              P("ST-D:T-LD", "TURN", "HELD", 0.2, 0.175, missing="turn profile not drawn")]},
                  {"run": "RL-02", "action": "CONFIRM", "source_tasks": ["T-D"],
                   "pieces": [P("ST-R:G1", "HORIZONTAL", "DRAWING-CONFIRMED", 3.0004, 0.0, 3.0004)]},
                  {"run": "RL-03", "action": "KEEP", "source_tasks": ["T-D"],
                   "pieces": [P("ST-G:E1", "INCLINED", "HELD", 1.2, None, missing="rise not printed")]}],
         "unknowns": [P("ST-D:U1", "HORIZONTAL", "UNKNOWN", 1.0, missing="rail existence not drawn", floor="GF",
                        source_tasks=["T-D"])],
         "retire": [{"reader_line_id": "L-" + "1" * 20, "floor": "GF", "reader_flight": "F1", "treads": 8, "physical_flight": "F1",
                     "reading": "PRIMARY", "homes": ["RL-01"], "why": "8 riser lines = F1", "source_tasks": ["T-D"]},
                    {"reader_line_id": "L-" + "2" * 20, "floor": "GF", "reader_flight": "F2", "treads": 9, "physical_flight": "F2",
                     "reading": "PRIMARY", "homes": ["RL-01"], "why": "9 riser lines = F2", "source_tasks": ["T-D"]},
                    {"reader_line_id": "L-" + "3" * 20, "floor": "1F", "reader_flight": "F1", "treads": 9, "physical_flight": "F2",
                     "reading": "SEEN_THROUGH_VOID", "homes": ["RL-01"], "why": "F2 seen from above",
                     "source_tasks": ["T-D"]}],
         "no_rail_sides": [{"stair": "ST-D", "flight": "F1", "side": "wall", "why": "no wall rail drawn"},
                           {"stair": "ST-D", "flight": "F2", "side": "wall", "why": "no wall rail drawn"}]}
    d.update(over)
    return d


def run(c, d):
    ch, log = M.changes_for(M.load_inputs(d, PID), c)
    return ch, log, M.integrate(c, ch)


def eid(ln):
    return ln["location"]["element_id"]


# ------------------------------------------------------------------------------------------------ normal
def test_pitch_line_hand_figures():
    assert M.pitch_length("INCLINED", 2.24, 1.4) == pytest.approx(2.641515, abs=1e-6)
    assert M.pitch_length("INCLINED", 2.52, 1.575) == pytest.approx(2.971704, abs=1e-6)
    assert M.pitch_length("HORIZONTAL", 1.1, 0) == 1.1


def test_run_valued_flight_by_flight():
    c = candidate()
    ch, log, (out, ident) = run(c, doc(c))
    by = {eid(ln): ln for ln in out}
    r1 = by["RAIL:RL-01"]
    assert r1["evidence_state"] == "PROVISIONAL" and r1["measured_net"] == pytest.approx(6.713219, abs=1e-6)
    assert r1["gross"] == r1["measured_net"] and r1["rfi"] is None
    assert r1["calculation"]["inputs"][A3030.REC_KEY]["run"] == "RL-01"          # V3.0.30 run record kept
    rec = r1["calculation"]["inputs"][M.REC_KEY]
    assert [p["piece_id"] for p in rec["pieces"]] == ["ST-D:F1", "ST-D:LD", "ST-D:F2", "ST-D:T-LD"]
    assert rec["held_pieces"] == ["ST-D:T-LD"]
    assert "hypot(2.24, 1.4) 2.641515" in r1["calculation"]["formula"]
    assert log["runs"] == {"RL-01": 6.713219} and log["valued_lm"] == 6.713219
    assert ident["rail_runs"] == {"valued_runs": 1, "valued_lm": 6.713219, "held_pieces": 1, "unknowns": 1,
                                  "retired": 3}


def test_held_and_unknown_pieces_blank_by_name_never_zero():
    c = candidate()
    _, _, (out, _) = run(c, doc(c))
    by = {eid(ln): ln for ln in out}
    for e in ("RAIL:RL-01:ST-D:T-LD", "RAIL:ST-D:U1"):
        ln = by[e]
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["gross"] is None
        assert ln["bounded_range"] is None and ln["rfi"]["question"]
    assert by["RAIL:RL-03"] == [x for x in c if eid(x) == "RAIL:RL-03"][0]         # KEEP: byte-identical


def test_readers_retired_against_their_run():
    c = candidate()
    _, _, (out, _) = run(c, doc(c))
    home = {eid(ln): ln for ln in out}["RAIL:RL-01"]["line_id"]
    ret = [ln for ln in out if ":flight " in eid(ln) and eid(ln) != "GF-RC:flight 1"]
    assert len(ret) == 3
    assert {eid(ln): ln for ln in out}["GF-RC:flight 1"] == candidate()[7]          # same floor + flight, 3 treads
    for ln in ret:
        assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["measured_net"] is None
        assert ln["calculation"]["inputs"][M.REC_KEY]["home_lines"] == [home]


def test_confirm_and_everything_else_byte_identical_totals_only_railing():
    c = candidate()
    ch, log, (out, ident) = run(c, doc(c))
    assert log["confirmed"]["RL-02"]["difference_lm"] == pytest.approx(-0.0004, abs=1e-9)
    named = {x["after"]["line_id"] for x in ch}
    for a in c:
        if a["line_id"] not in named:
            assert A30.line_sha(a) == A30.line_sha([x for x in out if x["line_id"] == a["line_id"]][0])
    assert ident["replaced"] == 4 and ident["added"] == 2 and len(out) == len(c) + 2
    moved = M.check_totals(A304.code_totals(c), A304.code_totals(out))
    assert set(k.split("|")[0] for k in moved) == {"FIN.RAILING"}
    t0, t1 = A304.code_totals(c), A304.code_totals(out)
    k = [k for k in moved][0]
    assert str(t0[k]) != str(t1[k])


def test_write_files(tmp_path):
    c = candidate()
    d = M.load_inputs(doc(c), PID)
    ch, log = M.changes_for(d, c)
    names, ident, led = M.write(tmp_path, c, ch, log)
    assert "V3_0_54_BOQ_LINES.json" in names and len(led["rows"]) == 6
    assert led["summary"]["no_rail_sides"] == 2 and led["released_default"] is False


# ------------------------------------------------------------------------------------------------ adverse
def _piece_doc(c, piece, run_id="RL-01"):
    d = doc(c)
    for r in d["runs"]:
        if r["run"] == run_id:
            r["pieces"] = [piece] + [p for p in r["pieces"] if p["piece_id"] != piece["piece_id"]]
    return d


@pytest.mark.parametrize("piece, msg", [
    (P("ST-D:F1", "INCLINED", "DRAWING-CONFIRMED", 2.24, 1.4, 2.24), "not the pitch-line length"),     # plan length
    (P("ST-D:F1", "INCLINED", "DRAWING-CONFIRMED", 2.24, 0.0, 2.24), "plan length is never billed"),  # no rise
    (P("ST-D:LD", "HORIZONTAL", "DRAWING-CONFIRMED", 1.1, 0.2, 1.1), "is inclined"),                  # rise on level
    (P("ST-D:T-LD", "TURN", "DRAWING-CONFIRMED", 0.2, 0.175, 0.27), "turn is valued only"),           # valued turn
    (P("ST-D:F1", "INCLINED", "DRAWING-CONFIRMED", 2240.0, 1400.0, 2641.515), "mm / cm refused"),    # mm units
    (P("ST-D:T-LD", "TURN", "HELD", 0.2, 0.175, 0.0, missing="x"), "carries no length"),             # held as 0
    (P("ST-D:T-LD", "TURN", "HELD", 0.2, 0.175), "missing missing"),                                 # no reason
    (P("ST-D:F2", "INCLINED", "DRAWING-CONFIRMED", 2.52, 1.575, 2.971704, pitch="PER_GOING"),
     "per-going piece is valued only"),                                                              # VALUE per going
])
def test_adverse_pieces_refused(piece, msg):
    c = candidate()
    with pytest.raises(M.InputsError, match=msg):
        M.load_inputs(_piece_doc(c, piece), PID)


def test_per_going_bounds():
    c = candidate()
    ok = P("ST-R:G1", "INCLINED", "DRAWING-CONFIRMED", 2.587274, 1.928568, 3.228281, pitch="PER_GOING")
    assert M.load_inputs(_piece_doc(c, ok, "RL-02"), PID)
    bad = dict(ok, length_lm=3.1)                                     # below the straight pitch line 3.226974
    with pytest.raises(M.InputsError, match="outside"):
        M.load_inputs(_piece_doc(c, bad, "RL-02"), PID)
    bad = dict(ok, length_lm=4.6)                                     # above plan + rise 4.515842
    with pytest.raises(M.InputsError, match="outside"):
        M.load_inputs(_piece_doc(c, bad, "RL-02"), PID)


def test_stale_bindings_refused():
    c = candidate()
    d = doc(c)
    d["runs"][0]["run"] = "RL-02"                       # VALUE on a valued run
    d["runs"][1]["run"] = "RL-01"
    with pytest.raises(M.InputsError, match="stale binding"):
        run(c, d)
    d = doc(c)
    d["runs"][1]["pieces"][0].update(plan_m=3.01, length_lm=3.01)  # CONFIRM disagreement 0.010 lm
    with pytest.raises(M.InputsError, match="a re-measure"):
        run(c, d)
    d = doc(c)
    d["retire"][0]["treads"] = 7                        # no reading with 7 treads on GF F1
    with pytest.raises(M.InputsError, match="stale binding"):
        run(c, d)
    d = doc(c)
    d["retire"][0]["homes"] = ["RL-09"]                 # home run absent
    with pytest.raises(M.InputsError, match="has no line"):
        run(c, d)


def test_reader_with_a_figure_and_run_line_never_retired():
    c = candidate()
    c2 = copy.deepcopy(c)
    c2[4] = mk("GF-RA:flight 1", "FIN.RAILING", "lm", "MEASURED", 2.2, treads=8)
    d = doc(c2)
    with pytest.raises(M.InputsError, match="carries a figure"):
        run(c2, d)
    d = doc(c)
    d["retire"][2]["treads"] = 8
    d["retire"][2]["floor"] = "GF"                      # two readings bound to one candidate line
    with pytest.raises(M.InputsError, match="named twice"):
        run(c, d)


def test_applied_once_and_no_input():
    c = candidate()
    _, _, (out, _) = run(c, doc(c))
    with pytest.raises(M.InputsError, match="applied once"):
        M.changes_for(M.load_inputs(doc(out), PID), out)
    assert M.changes_for(None, c)[1]["state"] == "NO_PROJECT_INPUT"


def test_check_runs_catches_a_tampered_line():
    c = candidate()
    _, _, (out, _) = run(c, doc(c))
    bad = copy.deepcopy(out)
    for ln in bad:
        if eid(ln) == "RAIL:RL-01":
            ln["measured_net"] = ln["gross"] = 2.24 + 1.1 + 2.52           # plan lengths
    with pytest.raises(ValueError, match="pitch-line sum"):
        M.check_runs(bad)
    bad = [ln for ln in out if eid(ln) != "RAIL:RL-01:ST-D:T-LD"]           # held piece line dropped
    with pytest.raises(ValueError, match="has no blank line"):
        M.check_runs(bad)
