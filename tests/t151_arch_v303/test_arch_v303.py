"""T-151: ARCH_TAKEOFF_V3.0.3, the SAME opt-in candidate as V3.0 / V3.0.1 / V3.0.2 extended (engine.source.arch_v303),
on synthetic data only (no client drawing). Hand calculations (kg = count x length x d^2/162):

VILLA K (not the development villa), steel hand ledgers typed as records:
  COLUMNS, storey GF (scope COLUMNS / GF + 1F):
    K2 main 8 T 20 x 3.60 m (storey interval)   = 8 x 3.60 x 400/162      = 71.111111 kg  RELEASED, schedule row printed
    K2 links 6 T 8 /m, readings A 8.306 / B 8.768 / C 7.890 kg             -> HELD 7.890 .. 8.768 (Q-71: never one value)
    K3 main 6 T 16 x 3.60 held on a framing conflict: 6 x 3.6 x 256/162     = 34.133333 kg  HELD_DEFINED (shown, not added)
    PC planted column, a DUPLICATED schedule row gives 8 T 16 x 3.30         = 41.718519 kg  -> must be HELD (UNKNOWN),
       never released or VERIFIED; the 41.718519 kg is kept as information only
  BEAMS, GF: B1 bottom 4 T 16 x 4.20 m                                       = 26.548148 kg  RELEASED (checker re-measured
       -> VERIFIED); B1 side bars 2 T 12 x 4.20 'minimum only'               = 7.466667 kg   lower bound, upper NOT_ESTABLISHED
  GROUND BEAMS, FOUNDATION: G1 top 3 T 16 x 5.10                            = 24.177778 kg  RELEASED
  route G lines in scope: K2 main 100.0 + ties 20.0, an undrawn column D9 (V3.0.1 NOT_PRESENT) main 30.0, beam B1 50.0,
    ground beam 40.0 kg -> all five SUPERSEDED (NOT_APPLICABLE_WITH_EVIDENCE); out of scope and byte-identical: the neck
    (FOUNDATION) column line 15.0, the 2F beam line 12.0, the slab line 9.0
  totals: released 71.111111 + 26.548148 + 24.177778 = 121.837037 kg; held range 7.890 .. 8.768; held defined 34.133333;
    lower bound 7.466667; unknown 1 (PC)

D4: footing FA top short line 'END_TREATMENT_NOT_DRAWN' held 10.0 .. 12.0 kg; FA is listed with a closed-end detail ->
  re-cited, range unchanged, + 1 unquantified end-leg line; FB (not listed) unchanged.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "t131_arch_v30"))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v302 as A302                   # noqa: E402
from engine.source import arch_v303 as A303                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import provisional_estimate as PE          # noqa: E402

A = pytest.approx
PID = "synthetic-v303-villa-k"
KG = {8: 64 / 162, 12: 144 / 162, 16: 256 / 162, 20: 400 / 162}


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV",
                           conventions_digest="d" * 16)


def route_item(iid, family, storey, kg, trade="REINFORCEMENT"):
    return PE.item(item_id=iid, component_id=iid.split(":", 1)[1], trade=trade, family=family, storey=storey,
                   category="PROVISIONAL", low=kg, base=kg, high=kg, dia_mm=16 if trade == "REINFORCEMENT" else None,
                   formula="count x (span + 2 anchorage) x d^2/162", assumptions=["X"], support="CONVENTION_ONLY",
                   confidence="MEDIUM", blocker="NOT_REVIEWED", source="SV")


def footing_line(mark, comp, low, high):
    eid = f"FRP:FTG:FND:{mark}@1000,1000:aa:{comp}"
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="STR.REBAR", unit="kg",
                        evidence_state="BOUNDED_EXPOSURE", bounded_range={"low": low, "high": high, "basis": "A..B"},
                        element_id=eid, floor="FOUNDATION", physical_element="FOOTINGS", subtrade="FOOTINGS / 12 mm",
                        formula="held: per metre", inputs={"policy": "FOOTING_REBAR_POPULATION_V1", "mark": mark,
                                                           "component": comp, "reasons": [
                                                               "COUNT_RULE_NOT_SET: Q-71",
                                                               "END_TREATMENT_NOT_DRAWN: no detail cited for the top "
                                                               "bar ends; straight core only"]},
                        geometry_source="SCHEDULE_ONLY", geometry_confidence="INFERRED_CANDIDATE",
                        rule_id="URBAN-REBAR-FOOTING-POPULATION", rule_version="v1", material_state="SOURCE",
                        rfi={"question": "Q-71; END_TREATMENT_NOT_DRAWN", "unlocks": eid}, notes="V3.0.2 footing steel")


def base_lines():
    its = [route_item("P-S:COL:GF:K2@100,100:MAIN:D20", "COLUMNS", "GF", 100.0),
           route_item("P-S:COL:GF:K2@100,100:TIES:D8", "COLUMNS", "GF", 20.0),
           route_item("P-S:COL:1F:D9@900,900:MAIN:D16", "COLUMNS", "1F", 30.0),
           route_item("P-S:NECK:COL:K2@100,100:MAIN:D20", "COLUMNS", "FOUNDATION", 15.0),
           route_item("P-S:BEAMS:GF:BAND0001:BOT:D16", "BEAMS", "GF", 50.0),
           route_item("P-S:BEAMS:2F:BAND0009:BOT:D16", "BEAMS", "2F", 12.0),
           route_item("P-S:GROUND_BEAMS:FOUNDATION:BAND0002:TOP:D16", "GROUND_BEAMS", "FOUNDATION", 40.0),
           route_item("P-S:SLABS:GF:S1:BOT:D12", "SLABS", "GF", 9.0)]
    return [to_line(it) for it in its] + [footing_line("FA", "TOP_SHORT", 10.0, 12.0),
                                         footing_line("FB", "TOP_SHORT", 5.0, 6.0)]


def src(task):
    return {"file": f"research/{task}.csv", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task} (MERGED abc1234)"}


def records():
    col = [{"element": "K2", "floor": "GF", "mark": "K2", "component": "MAIN", "state": "RELEASED",
            "kg": 8 * 3.6 * KG[20], "schedule_row": "PRINTED", "printed": "SV column schedule K2: 8 T 20",
            "dia_mm": 20, "count": 8, "length_m": 3.6},
           {"element": "K2", "floor": "GF", "mark": "K2", "component": "LINKS", "state": "HELD_RANGE",
            "low": 7.890, "high": 8.768, "readings": {"A": 8.306, "B": 8.768, "C": 7.890},
            "reasons": ["count Q-71 open"]},
           {"element": "K3", "floor": "GF", "mark": "K3", "component": "MAIN", "state": "HELD_DEFINED",
            "kg": 6 * 3.6 * KG[16], "reasons": ["framing member width conflict (designer)"]},
           {"element": "PC", "floor": "1F", "mark": "P.C 20x50", "component": "MAIN", "state": "RELEASED",
            "kg": 8 * 3.3 * KG[16], "schedule_row": "DUPLICATE_ROW", "printed": "leader prints the size only"}]
    bm = [{"element": "B1", "floor": "GF", "mark": "B1", "component": "bottom", "state": "RELEASED",
           "kg": 4 * 4.2 * KG[16], "schedule_row": "PRINTED", "printed": "SV beam schedule B1: 4 T 16",
           "verified_by": "checker re-measured B1 (0.0 %)"},
          {"element": "B1", "floor": "GF", "mark": "B1", "component": "side bars", "state": "HELD_LOWER_BOUND",
           "low": 2 * 4.2 * KG[12], "reasons": ["2 T 12 / 30 cm: count from a spacing (Q-71); minimum only"]}]
    gb = [{"element": "G1", "floor": "FOUNDATION", "component": "TOP", "state": "RELEASED", "kg": 3 * 5.1 * KG[16],
           "schedule_row": "PRINTED", "printed": "SV typical ground-beam section: 3 T 16 top"}]
    return col, bm, gb


def inputs(col=None, bm=None, gb=None, d4=True):
    c, b, g = records()
    doc = {"schema": A303.INPUTS_SCHEMA, "project": PID, "ledgers": [
        {"piece": "COLUMN_STEEL", "source": src("T-C"), "scope": {"physical_element": "COLUMNS",
                                                                  "floors": ["GF", "1F"]}, "records": col or c},
        {"piece": "BEAM_STEEL", "source": src("T-B"), "scope": {"physical_element": "BEAMS", "floors": ["GF"]},
         "records": bm or b},
        {"piece": "GROUND_SYSTEM_STEEL", "source": src("T-G"),
         "scope": {"physical_element": "GROUND_BEAMS", "floors": ["FOUNDATION"]}, "records": gb or g}]}
    if d4:
        doc["evidence_fix"] = {"closed_top_ends": {"FA": "SV footing schedule closed box symbol"},
                               "source": "T-X merged"}
    return doc


def not_present_log(lines):
    d9 = next(ln for ln in lines if "D9@" in ln["location"]["element_id"])
    return {"steel_stale": [{"line_id": d9["line_id"], "reads": "column piece COL:1F:D9 (NOT_PRESENT)"}]}


def case(doc=None):
    base = base_lines()
    inp = A303.load_inputs(doc or inputs(), PID)
    ch, logs = A303.steel_changes(inp, base, not_present_log(base))
    ce, le = A303.evidence_fix_changes(inp, base)
    return base, ch, logs, ce, le


# ------------------------------------------------------------------------------------------------ steel ledgers
def test_route_lines_in_scope_superseded_and_ledger_lines_added_by_hand():
    base, ch, logs, ce, le = case()
    sup = [c for c in ch if c["action"] == "REPLACE"]
    assert len(sup) == 5
    for c in sup:
        assert c["after"]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and c["after"]["measured_net"] is None
    np_ = [c for c in sup if "D9@" in c["before"]["location"]["element_id"]]
    assert len(np_) == 1 and "NOT_PRESENT" in np_[0]["after"]["notes"] and "30.0 kg" in np_[0]["after"]["notes"]
    add = {(c["after"]["calculation"]["inputs"]["element"], c["after"]["calculation"]["inputs"]["component"]): c
           for c in ch if c["action"] == "ADD"}
    k2 = add[("K2", "MAIN")]["after"]
    assert k2["evidence_state"] == "SOURCE_DERIVED" and k2["measured_net"] == A(71.111111, abs=1e-6)
    assert add[("K2", "MAIN")]["evidence_status"] == "DRAWING-CONFIRMED"
    lk = add[("K2", "LINKS")]["after"]
    assert lk["evidence_state"] == "BOUNDED_EXPOSURE" and (lk["bounded_range"]["low"], lk["bounded_range"]["high"]) \
        == (A(7.890), A(8.768))
    k3 = add[("K3", "MAIN")]["after"]
    assert k3["evidence_state"] == "BLOCKED_RFI" and k3["measured_net"] is None
    assert k3["calculation"]["inputs"]["held_defined_kg"] == A(34.133333, abs=1e-6)
    b1 = add[("B1", "bottom")]
    assert b1["after"]["measured_net"] == A(26.548148, abs=1e-6) and b1["evidence_status"] == "VERIFIED"
    sb = add[("B1", "side bars")]["after"]
    assert sb["evidence_state"] == "BLOCKED_RFI" and sb["calculation"]["inputs"]["lower_bound_kg"] == A(7.466667,
                                                                                                         abs=1e-6)
    assert sb["calculation"]["inputs"]["upper_bound"] == "NOT_ESTABLISHED"
    assert add[("G1", "TOP")]["after"]["measured_net"] == A(24.177778, abs=1e-6)
    lg = {x["piece"]: x for x in logs}
    assert lg["COLUMN_STEEL"]["route_kg"] == A(150.0) and lg["COLUMN_STEEL"]["superseded_not_present"] == 1
    rel = sum(x["totals"]["released"] for x in logs)
    assert rel == A(121.837037, abs=1e-5)
    assert lg["COLUMN_STEEL"]["totals"]["held_defined"] == A(34.133333, abs=1e-6)


def test_a_duplicated_schedule_row_is_held_never_verified():
    base, ch, logs, ce, le = case()
    pc = next(c for c in ch if c["action"] == "ADD" and c["after"]["calculation"]["inputs"]["element"] == "PC")
    a = pc["after"]
    assert a["evidence_state"] == "BLOCKED_RFI" and a["measured_net"] is None
    assert pc["evidence_status"] == "UNKNOWN"
    assert "SCHEDULE_ROW_NOT_PRINTED" in a["rfi"]["question"]
    assert a["calculation"]["inputs"]["would_be_kg"] == A(41.718519, abs=1e-6)
    lg = next(x for x in logs if x["piece"] == "COLUMN_STEEL")
    assert lg["by_floor"]["1F"]["released"] == 0 and lg["by_floor"]["1F"]["forced_held"] == 1
    # even a 'verified_by' claim cannot release it
    c, b, g = records()
    c[3]["verified_by"] = "someone"
    _b, ch2, _l, _c, _e = case(inputs(col=c))
    pc2 = next(x for x in ch2 if x["action"] == "ADD" and x["after"]["calculation"]["inputs"]["element"] == "PC")
    assert pc2["evidence_status"] == "UNKNOWN" and pc2["after"]["measured_net"] is None


def test_a_record_without_a_schedule_row_is_held():
    c, b, g = records()
    del c[0]["schedule_row"]
    _b, ch, _l, _c, _e = case(inputs(col=c))
    k2 = next(x for x in ch if x["action"] == "ADD" and x["after"]["calculation"]["inputs"]["element"] == "K2"
              and x["after"]["calculation"]["inputs"]["component"] == "MAIN")
    assert k2["after"]["evidence_state"] == "BLOCKED_RFI"


@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d["ledgers"][0]["source"].pop("checker_run"), "checker_run"),
    (lambda d: d["ledgers"][0]["records"][0].pop("kg"), "RELEASED record carries kg"),
    (lambda d: d["ledgers"][0]["records"][1].update(low=9.0), "low <= high"),
    (lambda d: d["ledgers"][0]["records"][1].pop("reasons"), "names why"),
    (lambda d: d["ledgers"][0]["records"].append(dict(d["ledgers"][0]["records"][0])), "unique"),
    (lambda d: d["ledgers"][0]["records"][0].update(state="RELEASED_GUESS"), "state"),
    (lambda d: d["ledgers"].append(copy.deepcopy(d["ledgers"][0])), "once each"),
    (lambda d: d.update(schema="X"), "schema"),
    (lambda d: d["ledgers"][1]["scope"].pop("floors"), "scope"),
])
def test_inputs_are_checked(mutate, msg):
    d = inputs()
    mutate(d)
    with pytest.raises(A303.InputsError, match=msg):
        A303.load_inputs(d, PID)


def test_a_record_outside_its_scope_is_refused():
    c, b, g = records()
    b[0] = dict(b[0], floor="2F")
    with pytest.raises(A303.InputsError, match="outside the scope"):
        case(inputs(bm=b))


def test_no_inputs_changes_nothing():
    base = base_lines()
    ch, logs = A303.steel_changes(None, base)
    assert ch == [] and {x["state"] for x in logs} == {"NO_PROJECT_INPUT"}
    ce, le = A303.evidence_fix_changes(None, base)
    assert ce == [] and le["state"] == "NO_PROJECT_INPUT"


# ------------------------------------------------------------------------------------------------ D4
def test_d4_recites_closed_ends_keeps_the_range_and_adds_one_leg_line():
    base, ch, logs, ce, le = case()
    rep = [c for c in ce if c["action"] == "REPLACE"]
    add = [c for c in ce if c["action"] == "ADD"]
    assert len(rep) == 1 and len(add) == 1
    a = rep[0]["after"]
    assert a["bounded_range"] == rep[0]["before"]["bounded_range"]
    rs = a["calculation"]["inputs"]["reasons"]
    assert not any(x.startswith("END_TREATMENT_NOT_DRAWN") for x in rs)
    assert any("END_TREATMENT_DRAWN_CLOSED" in x and "closed box symbol" in x for x in rs)
    assert rep[0]["fixes_v3_0_2"]
    leg = add[0]["after"]
    assert leg["evidence_state"] == "BLOCKED_RFI" and leg["location"]["element_id"] == \
        "FRP:FTG:FND:FA@1000,1000:aa:TOP_END_LEGS"
    assert [x["change"] for x in le["lines"]].count("NONE (ends not drawn: kept)") == 1        # FB


# ------------------------------------------------------------------------------------------------ integrate, write
def test_integrate_identity_and_refusals():
    base, ch, logs, ce, le = case()
    l302, l303, ident = A303.integrate(base, [], [], [], ch + ce)
    assert ident["replaced"] == 6 and ident["added"] == len([c for c in ch + ce if c["action"] == "ADD"])
    by = {x["line_id"]: x for x in base}
    untouched = [x for x in l303 if x["line_id"] in by and A30.line_sha(x) == A30.line_sha(by[x["line_id"]])]
    assert len(untouched) == ident["outside_rows"] == 4         # neck, 2F beam, slab, FB footing
    # a line two V3.0.3 pieces change
    with pytest.raises(ValueError, match="two V3.0.3 pieces"):
        A303.integrate(base, [], [], [], ch + [ch[0]])
    # a line an earlier version changed, without a named defect fix
    fake302 = [{"piece": "X", "action": "REPLACE", "before": ch[0]["before"], "after": copy.deepcopy(ch[0]["before"])}]
    with pytest.raises(ValueError, match="earlier version"):
        A303.integrate(base, [], [], fake302, ch)


def test_write_files_ledger_and_totals(tmp_path):
    base, ch, logs, ce, le = case()
    names, ident, led = A303.write(tmp_path, base, [], [], [], ch + ce, logs + [le], inputs(), released_lines=base)
    assert set(names) == {"V3_0_3_BOQ_LINES.json", "V3_0_3_BOQ_LINES.csv", "V3_0_3_INTEGRATION_LEDGER.json",
                          "V3_0_3_INTEGRATION_LEDGER.csv", "V3_0_3_DIFF.csv", "V3_0_3_DOWNSTREAM.json",
                          "V3_0_3_RUN.json"}
    run = json.loads((tmp_path / "V3_0_3_RUN.json").read_text(encoding="utf-8"))
    assert run["released_default"] is False and run["extends"] == "ARCH_TAKEOFF_V3.0.2"
    s = run["steel_v3_0_3"]
    assert s["COLUMNS|GF"]["value_kg"] == A(71.111111, abs=1e-6) and s["COLUMNS|FOUNDATION"]["value_kg"] == A(15.0)
    assert s["BEAMS|2F"]["value_kg"] == A(12.0) and "COLUMNS|1F" in s and s["COLUMNS|1F"]["value_kg"] == 0
    assert ident["diff"]["vs_v3_0_2"]["SAME"] == 4 and ident["diff"]["vs_v3_0_2"]["CHANGED"] == 6
    assert led["integration_package"] is True
    for r in led["rows"]:
        assert r["evidence_status"] in A302.EVIDENCE_STATUS and r["release_status"] == "NOT RELEASED"
        assert r["verification"].get("task") and r["drawing_reference"]
    assert run["evidence_status_counts"]["VERIFIED"] == 1


def test_no_project_constants_in_the_module():
    text = (ROOT / "engine/source/arch_v303.py").read_text(encoding="utf-8")
    for word in ("Alsenan", "ST7757", "P7757", "COL-GF", "BM-GF", "1887", "5171"):
        assert word not in text


def test_the_earlier_method_lists_are_untouched():
    from tools import urban_boq_m9 as M9
    assert M9.CANDIDATE_METHODS == ("ARCH_TAKEOFF_V3.0",) and M9.CANDIDATE_EXTENSIONS == ("ARCH_TAKEOFF_V3.0.1",)
    assert M9.CANDIDATE_EXTENSIONS_V302 == ("ARCH_TAKEOFF_V3.0.2",)
    assert M9.CANDIDATE_EXTENSIONS_V303 == ("ARCH_TAKEOFF_V3.0.3",) and M9.V303 not in M9.ARCH_METHODS


def test_runner_refuses_to_run_without_the_route_g_profile(tmp_path):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t151/v303_run.py"), "plan.dxf", "st.dxf",
                        "--out", str(tmp_path / "o")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 2 and "--profile" in r.stderr
    assert not (tmp_path / "o").exists()


# ------------------------------------------------------------------------------------------------ end to end
def test_end_to_end_v3_0_2_files_unchanged_and_v3_0_3_beside_them(tmp_path):
    import test_arch_v30 as T131
    from tools import arch_synth as AS
    AS.villa(tmp_path / "villa.dxf")
    a = T131._run(tmp_path / "villa.dxf", tmp_path / "v302", "ARCH_TAKEOFF_V3.0.2")
    inp = tmp_path / "inp.json"
    inp.write_text(json.dumps(dict(inputs(), project=None)), encoding="utf-8")
    b = T131._run(tmp_path / "villa.dxf", tmp_path / "v303", "ARCH_TAKEOFF_V3.0.3", "--v303-inputs", str(inp))
    for name in ("V3_0_BOQ_LINES.json", "V3_0_1_BOQ_LINES.json", "V3_0_2_BOQ_LINES.json",
                 "V3_0_2_INTEGRATION_LEDGER.json", "BOQ_LINES.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    l302 = T131._lines(b / "V3_0_2_BOQ_LINES.json")
    l303 = T131._lines(b / "V3_0_3_BOQ_LINES.json")
    by = {x["line_id"]: x for x in l302}
    added = [y for y in l303 if y["line_id"] not in by]
    assert len(added) == 7                                     # the 7 ledger records (no route steel in this villa)
    for y in l303:
        if y["line_id"] in by:
            assert A30.line_sha(by[y["line_id"]]) == A30.line_sha(y)
    run = json.loads((b / "V3_0_3_RUN.json").read_text(encoding="utf-8"))
    assert sum(lg["totals"]["released"] for lg in run["piece_logs"] if lg.get("totals")) == A(121.837037, abs=1e-5)


# ------------------------------------------------------------------------------------------------ the typed ledgers
def test_the_typed_ledgers_reproduce_their_own_totals_and_load():
    """research/agents_t151/t151_ledgers.py on the three checker-merged ledger CSVs (tracked research files): the
    released kg re-add to each ledger's own total; straps are held on Q-74; no record is released without a printed
    schedule row; continuous beams carry their end-support top bars as UNKNOWN lines."""
    sys.path.insert(0, str(ROOT / "research" / "agents_t151"))
    import t151_ledgers as LG
    doc = A303.load_inputs(LG.inputs("dev"), "dev")
    t = {lg["piece"]: lg["declared_totals"] for lg in doc["ledgers"]}
    assert t["COLUMN_STEEL"]["released"] == A(1887.131, abs=0.01)          # T148_SUMMARY net_released_kg
    assert t["COLUMN_STEEL"]["held_defined"] == A(1552.435, abs=0.01)      # T148_SUMMARY net_held_defined_kg
    assert t["BEAM_STEEL"]["released"] == A(5171.03, abs=0.01)             # T149_SUMMARY totals RELEASED
    assert t["GROUND_SYSTEM_STEEL"]["released"] == A(1479.86 - 168.63 - 58.32, abs=0.01)   # SB1 / SB3 held (Q-74)
    for lg in doc["ledgers"]:
        assert lg["source"]["sha256"] == LG.sha(lg["source"]["file"])
        for r in lg["records"]:
            if r["state"] == "RELEASED":
                assert r["schedule_row"] == "PRINTED" and r.get("printed")
            if str(r["element"]).startswith("SB") and r["component"].startswith(("TOP", "BOTTOM", "STIRRUP")):
                assert r["state"] != "RELEASED" and any("Q-74" in x for x in r["reasons"])
    ends = [r for r in doc["ledgers"][2]["records"] if r["component"].startswith("END-SUPPORT")]
    assert ends and all(r["state"] == "UNQUANTIFIED" for r in ends)
