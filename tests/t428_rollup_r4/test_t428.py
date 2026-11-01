"""T-428: roll-up r4 by sub-trace (R-T428-1 .. 7) and the Alsenan r4 restatement of the T-406 r3 concrete roll-up.

Villa R428 (hand fixture, NOT Alsenan). Merged roll-up of record (engine - other side, m3):
  GROUND  G  held runs -1.000 HELD | section +0.500 ENGINE_RIGHT | length -0.800 UNTRACED          (G = -1.300)
  STAIR   S  flight -0.600 UNRESOLVED | landings -0.100 ENGINE_RIGHT                              (S = -0.700)
  table: traced +0.400, held -1.000, unexplained -1.400, residual -2.000.
Merged T-950 sub-traces G's length -0.800: his lumps through the supports 5.00 m x 0.18 = -0.900
  BOUNDED_THROUGH_SUPPORTS (drawn allowance 6.00 m), a valued run through a neck 0.50 m x 0.18 = +0.090 ENGINE_WRONG
  (correction T-952), +0.010 UNRESOLVED.  -0.900 + 0.090 + 0.010 = -0.800.
Merged T-951 sub-traces S's flight -0.600: his length = run + rise, rise 2.00 m x 1.20 x 0.28 = -0.672 ENGINE_RIGHT,
  one length +0.072 ENGINE_RIGHT.  -> after: traced -1.010 (G -0.310, S -0.700; of which ENGINE_WRONG +0.090, bounded -0.900), held
  -1.000, unexplained +0.010, residual -2.000; STAIR closes, GROUND does not.
Scenario T-952 (QUEUED): the neck length leaves (-0.090, the ENGINE_WRONG part goes) and 0.300 valued is withdrawn into
  a held range (-0.300 HELD): G -1.300 -> -1.690, printed beside the as-is -1.300.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t428"))
import t428_rules as R  # noqa: E402

REF = "T-95x MERGED, Checker own re-measure"
MERGED = {"T-950": "aaaa0950", "T-951": "aaaa0951"}


def P(cause, m3, verdict, **kw):
    return {"cause": cause, "m3": m3, "verdict": verdict, **kw}


G_PARTS = [P("held runs", -1.0, "HELD"), P("section", 0.5, "ENGINE_RIGHT"), P("length", -0.8, "UNTRACED")]
S_PARTS = [P("flight", -0.6, "UNRESOLVED"), P("landings", -0.1, "ENGINE_RIGHT")]
BASE = [{"id": "G", "family": "GROUND", "parts": G_PARTS, "current": {"TRACED": 0.5, "HELD": -1.0, "UNEXPLAINED": -0.8}},
        {"id": "S", "family": "STAIR", "parts": S_PARTS, "current": {"TRACED": -0.1, "HELD": 0.0, "UNEXPLAINED": -0.6}}]
FAMS = {"GROUND": {"TRACED": 0.5, "HELD": -1.0, "UNEXPLAINED": -0.8, "components": 1},
        "STAIR": {"TRACED": -0.1, "HELD": 0.0, "UNEXPLAINED": -0.6, "components": 1}}


def st_g(**over):
    subs = [P("his lumps through the supports 5.00 m", -0.9, "BOUNDED_THROUGH_SUPPORTS", verdict_ref=REF,
              allowance_m=6.0, used_m=5.0, id="G-B"),
            P("valued run through a neck 0.50 m", 0.09, "ENGINE_WRONG", verdict_ref=REF, correction_owner="T-952",
              id="G-N"),
            P("small read", 0.01, "UNRESOLVED", id="G-U")]
    d = {"component": "G", "source": "T-950", "part_cause": "length", "part_m3": -0.8, "subparts": subs}
    d.update(over)
    return d


def st_s(**over):
    d = {"component": "S", "source": "T-951", "part_cause": "flight", "part_m3": -0.6, "subparts": [
        P("rise laid as plan length 2.00 m", -0.672, "ENGINE_RIGHT", verdict_ref=REF, id="S-R"),
        P("one length", 0.072, "ENGINE_RIGHT", verdict_ref=REF, id="S-O")]}
    d.update(over)
    return d


def run(sts=None, side=()):
    return R.rollup(BASE, FAMS, [st_g(), st_s()] if sts is None else sts, MERGED, side)


# ---------------- normal

def test_hand_fixture_by_hand():
    newparts, fams, tot = run()
    assert (tot["TRACED"], tot["HELD"], tot["UNEXPLAINED"], tot["residual_m3"]) == (-1.01, -1.0, 0.01, -2.0)
    assert fams["STAIR"]["cause_closes"] and not fams["GROUND"]["cause_closes"]
    st = R.subtotals(newparts["G"])
    assert (st["TRACED_of_which_ENGINE_WRONG"], st["TRACED_of_which_BOUNDED"]) == (0.09, -0.9)
    assert [p["cause"] for p in newparts["S"]][:2] == ["rise laid as plan length 2.00 m", "one length"]


def test_order_of_subtraces_does_not_matter():
    a = run([st_g(), st_s()])[2]
    b = run([st_s(), st_g()])[2]
    assert a == b


def test_scenario_printed_beside_as_is():
    newparts, _, _ = run()
    sc = R.scenario(newparts["G"], [{"removes": "valued run through a neck 0.50 m", "m3": -0.09},
                                    {"cause": "valued withdrawn into a held range", "m3": -0.3, "verdict": "HELD"}],
                    "T-952", MERGED, "QUEUED")
    assert sc["as_is"]["residual_m3"] == -1.3 and sc["after"]["residual_m3"] == -1.69
    assert sc["after"]["TRACED_of_which_ENGINE_WRONG"] == 0.0 and sc["after"]["HELD"] == -1.3


def test_engine_side_register_never_moves_the_table():
    side = [{"id": "E-1", "kind": "VERIFIED_WRONG", "m3": 0.2, "line_ids": ["L-1"], "residual_effect_m3": 0.0,
             "verdict_ref": REF, "correction_owner": "T-952"},
            {"id": "E-2", "kind": "HELD_RANGE", "range_m3": [0.4, 0.6], "line_ids": ["L-1"], "residual_effect_m3": 0.0,
             "verdict_ref": REF, "correction_owner": "T-952"}]
    assert run(side=side)[2] == run()[2]


# ---------------- adverse

@pytest.mark.parametrize("bad, msg", [
    (st_g(source="T-999"), "not in the merged register"),
    (st_g(part_cause="nothing"), "found 0 times"),
    (st_g(part_m3=-0.7), "found 0 times"),
    (st_g(subparts=[P("x", -0.7, "UNRESOLVED")]), "re-add"),
    (st_g(subparts=[P("x", -0.8, "ENGINE_RIGHT")]), "needs the Checker verdict"),
    (st_g(subparts=[P("x", -0.8, "HELD")]), "needs the Checker verdict"),
    (st_g(subparts=[P("x", -0.8, "ENGINE_WRONG", verdict_ref=REF)]), "owns the correction"),
    (st_g(subparts=[P("x", -0.8, "BOUNDED_THROUGH_SUPPORTS", verdict_ref=REF, allowance_m=4.0, used_m=5.0)]),
     "allowance"),
    (st_g(subparts=[P("x", -0.8, "BOUNDED_THROUGH_SUPPORTS", verdict_ref=REF)]), "allowance"),
    (st_g(subparts=[P("x", 0.0, "HELD", verdict_ref=REF), P("y", -0.8, "UNTRACED")]), "never 0"),
    (st_g(subparts=[P("length scaled pro rata", -0.8, "UNTRACED")]), "ratio"),
    (st_g(subparts=[P("x", -0.8, "UNRESOLVED", counted_as="TRACED")]), "counted as"),
    (st_g(subparts=[P("x", -0.8, "CLOSE_ENOUGH")]), "unknown verdict"),
    (st_g(component="Z"), "not a component"),
])
def test_refused_subtrace(bad, msg):
    with pytest.raises(R.Refused, match=msg):
        run([bad, st_s()])


def test_part_subtraced_twice_refused():
    with pytest.raises(R.Refused, match="sub-traced twice|found 0 times"):
        run([st_g(), st_g(), st_s()])


def test_base_parts_must_match_current():
    bad = [dict(BASE[0], current={"TRACED": 0.4, "HELD": -1.0, "UNEXPLAINED": -0.7}), BASE[1]]
    with pytest.raises(R.Refused, match="parts give"):
        R.rollup(bad, FAMS, [st_g()], MERGED)


def test_residual_counted_in_two_parts_refused():
    side = [{"id": "G-N", "kind": "VERIFIED_WRONG", "m3": 0.09, "line_ids": ["L-1"], "residual_effect_m3": 0.0,
             "verdict_ref": REF, "correction_owner": "T-952"}]
    with pytest.raises(R.Refused, match="counted in two parts"):
        run(side=side)


@pytest.mark.parametrize("item, msg", [
    ({"id": "E", "kind": "VERIFIED_WRONG", "m3": 0.2, "line_ids": ["L"], "residual_effect_m3": 0.2,
      "verdict_ref": REF, "correction_owner": "T"}, "never moves the residual"),
    ({"id": "E", "kind": "HELD_RANGE", "range_m3": [0.0, 0.0], "line_ids": ["L"], "residual_effect_m3": 0.0,
      "verdict_ref": REF, "correction_owner": "T"}, "never 0 .. 0"),
    ({"id": "E", "kind": "VERIFIED_WRONG", "m3": 0.2, "line_ids": [], "residual_effect_m3": 0.0,
      "verdict_ref": REF, "correction_owner": "T"}, "line ids"),
    ({"id": "E", "kind": "VERIFIED_WRONG", "m3": 0.2, "line_ids": ["L"], "residual_effect_m3": 0.0,
      "verdict_ref": REF}, "owns the correction"),
])
def test_engine_side_refused(item, msg):
    with pytest.raises(R.Refused, match=msg):
        run(side=[item])


def test_scenario_from_merged_task_refused():
    newparts, _, _ = run()
    with pytest.raises(R.Refused, match="is merged"):
        R.scenario(newparts["G"], [], "T-950", MERGED, "QUEUED")


def test_scenario_removal_must_cancel_the_engine_wrong_part():
    newparts, _, _ = run()
    with pytest.raises(R.Refused, match="does not cancel"):
        R.scenario(newparts["G"], [{"removes": "valued run through a neck 0.50 m", "m3": -0.05}], "T-952", MERGED,
                   "QUEUED")
    with pytest.raises(R.Refused, match="found 0 times"):
        R.scenario(newparts["G"], [{"removes": "small read", "m3": -0.01}], "T-952", MERGED, "QUEUED")


# ---------------- Alsenan (committed merged inputs only)

sys.path.insert(0, str(ROOT / "research" / "agents_t428"))
import t428_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def pub():
    return A.public_summary()


def test_alsenan_reproduces_committed_summary(pub):
    committed = json.loads((ROOT / "research" / "agents_t428" / "summary_t428.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(pub, sort_keys=True)) == committed


def test_alsenan_headline(pub):
    t = pub["totals_r4_current"]
    assert t["residual_m3"] == pub["totals_r3_current"]["residual_m3"] == -122.900258
    assert (t["TRACED"], t["HELD"], t["UNEXPLAINED"]) == (-1.387154, -116.428339, -5.084765)
    assert pub["unexplained_by_sign"] == {"negative_m3": -5.242949, "positive_m3": 0.158184, "parts": 16}


def test_alsenan_stairs(pub):
    sd = pub["restated_components"]["SD-STAIR"]["split"]
    assert (sd["TRACED"], sd["HELD"], sd["UNEXPLAINED"]) == (-2.43542, -4.772067, -2.476433)
    ids = {p.get("id"): p["m3"] for p in pub["restated_components"]["SD-STAIR"]["parts"]}
    assert ids["ST01-RISE-IN-LENGTH"] + ids["ST01-ONE-LENGTH"] == pytest.approx(-2.016, abs=1e-9)
    assert ids["ST01-LD-OWNERSHIP"] + ids["ST01-LD-COUNT"] == pytest.approx(0.1624, abs=1e-9)
    assert ids["ST02-RS-C-HELD"] == -1.244067 and ids["ST02-BEYOND"] == -2.476433


def test_alsenan_gb_main_as_is_and_after_t430(pub):
    gb = pub["restated_components"]["GB-MAIN"]["split"]
    assert gb["residual_m3"] == -10.354614
    assert (gb["TRACED_of_which_ENGINE_WRONG"], gb["TRACED_of_which_BOUNDED"]) == (0.108, -3.525102)
    a, b = pub["scenarios_gb_main_t430"]["A"], pub["scenarios_gb_main_t430"]["B"]
    assert a["as_is"]["residual_m3"] == b["as_is"]["residual_m3"] == -10.354614
    assert a["after"]["residual_m3"] == -12.154614 and a["t391_basis_held_term_after"] == -10.959354
    assert b["after"]["residual_m3"] == -14.219445
    assert a["after"]["TRACED_of_which_ENGINE_WRONG"] == 0.0


def test_alsenan_every_traced_or_held_subpart_names_its_verdict(pub):
    for c in pub["restated_components"].values():
        for p in c["parts"]:
            if p.get("_sub") and R.CLASS_OF[p["verdict"]] in ("TRACED", "HELD"):
                assert p["verdict_ref"].startswith(p["source"]) or p["source"] in p["verdict_ref"]


def test_alsenan_engine_side_register(pub):
    e = {x["id"]: x for x in pub["engine_side_register"]}
    assert e["E-1"]["m3"] == 0.423 and e["E-3"]["range_m3"] == [0.864171, 1.152231]
    assert all(x["residual_effect_m3"] == 0.0 for x in e.values())


def test_merged_register_is_ancestry():
    for task, sha in A.MERGED.items():
        r = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", sha, "HEAD"], capture_output=True)
        if r.returncode == 128:
            pytest.skip("git history not available")
        assert r.returncode == 0, f"{task} {sha} is not an ancestor of HEAD"
