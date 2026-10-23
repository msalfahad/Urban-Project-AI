"""T-216: review-set bindings as an opt-in key-map path (tools/alsenan_keymap.py --set-bindings), on a hand-calculated
villa that is not the development villa (villa T216-V), with adverse cases; plus the development villa's binding file.

Hand calculation (written before running the tool), key FLOOR = FIN.FLOOR.PORCELAIN + FIN.FLOOR.WET_TILE, m2:
  released lines: F1 living porcelain 8.00 x 5.00 = 40.00 (MEASURED), F2 bath wet tile 2.50 x 2.50 = 6.25
                  (SOURCE_DERIVED)                                                                   = 46.25
  review set S-A (niche RA, basin only, 1.20 x 1.50 = 1.80, one doorless opening 0.90 x 0.20 = 0.18 strip):
      WET {PORCELAIN 0.18 (the strip), WET_TILE 1.80, WP.FLOOR 1.80}  DRY {PORCELAIN 1.98}
      bound WET: the strip 0.18 stays in the opening's threshold line -> key 1.80
  review set S-B (lobby RB, basin only, 2.00 x 1.10 = 2.20, no door closure):
      WET {WET_TILE 2.20, WP.FLOOR 2.20}  DRY {PORCELAIN 2.20}  -> bound WET: key 2.20
  set S-D (DOOR_OWNER_MINIMUM): no floor item, never bound
  freelancer floor 52.00
  both bound:   engine 46.25 + 1.80 + 2.20 = 50.25; err -1.75; WAPE 1.75 / 52 = 3.365 %; released 46.25 and
                ASSUMED — OWNER-APPROVED 4.00 reported apart
  S-A only:     S-B stays HELD -> the line is HELD (engine qty None, line total None, never 46.25 + 1.80)
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import alsenan_keymap as K
from tools import scoreboard_v2 as V

ROOT = Path(__file__).resolve().parents[2]
T216 = ROOT / "research" / "agents_t216"
T208 = ROOT / "research" / "agents_t208"
TOL = 1e-9
FLOOR_ITEMS = ["FIN.FLOOR.PORCELAIN [m2]", "FIN.FLOOR.WET_TILE [m2]"]


def line(lid, code, unit, ev, net, element):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "trade": "X", "location": {"element_id": element}}


def lines():
    return [line("F1", "FIN.FLOOR.PORCELAIN", "m2", "MEASURED", 40.0, "R1:floor"),
            line("F2", "FIN.FLOOR.WET_TILE", "m2", "SOURCE_DERIVED", 6.25, "R2:floor"),
            line("T1", "ARCH.THRESHOLD", "m2", "BLOCKED_RFI", None, "OP-1")]


def review(sid, subject, wet, dry, kind="REVIEW_CLASSIFICATION"):
    return {"set_id": sid, "subject": subject, "kind": kind, "mutually_exclusive": True,
            "scenarios": ["WET_SCOPE", "DRY_SCOPE"], "by_scenario": {"WET_SCOPE": wet, "DRY_SCOPE": dry}}


def release_report():
    return {"categories": {"CONDITIONAL": {"scenario_sets": [
        review("RC:S-A", "RA", {"FIN.FLOOR.PORCELAIN [m2]": 0.18, "FIN.FLOOR.WET_TILE [m2]": 1.80,
                                "FIN.WP.FLOOR [m2]": 1.80}, {"FIN.FLOOR.PORCELAIN [m2]": 1.98}),
        review("RC:S-B", "RB", {"FIN.FLOOR.WET_TILE [m2]": 2.20, "FIN.WP.FLOOR [m2]": 2.20},
               {"FIN.FLOOR.PORCELAIN [m2]": 2.20}),
        {"set_id": "DOOR_MIN", "kind": "DOOR_OWNER_MINIMUM", "mutually_exclusive": True,
         "by_scenario": {"A": {"doors": 3}, "B": {"doors": 4}}}]}}}


def key_map():
    return {"SCHEMA": "URBAN_ALSENAN_KEY_MAP_V1", "keys": [
        {"key": "FLOOR", "trade": "FLOOR_AREA", "reference_id": "R-FLR",
         "item_codes": ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"], "conditional_items": FLOOR_ITEMS}]}


def normalised():
    return {"records": [{"id": "R-FLR", "unit": "m2", "qty": 52.0, "row_kind": "COVER_TOTAL", "trade": "T"}]}


def bset(sid, subject, q, strip=None, closures=0, **kw):
    b = {"set_id": sid, "subject": subject, "kind": "REVIEW_CLASSIFICATION", "status": "ASSUMED_OWNER_APPROVED",
         "scenario": "WET_SCOPE", "rule_id": "Q-X A", "quantities": q, "closure_strip": strip,
         "door_closures": closures, "evidence": {"fixture_symbol": "BASIN block", "printed_size": "printed 120 x 150"},
         "geometry_status": "DRAWING-CONFIRMED", "verdict": {"commit": "abc1234", "source": "board verdict row"}}
    b.update(kw)
    return b


def bindings(which=("A", "B")):
    sets = []
    if "A" in which:
        sets.append(bset("RC:S-A", "RA", {"FIN.FLOOR.WET_TILE [m2]": 1.80, "FIN.WP.FLOOR [m2]": 1.80},
                         {"item": "FIN.FLOOR.PORCELAIN [m2]", "m2": 0.18}, 1))
    if "B" in which:
        sets.append(bset("RC:S-B", "RB", {"FIN.FLOOR.WET_TILE [m2]": 2.20, "FIN.WP.FLOOR [m2]": 2.20}))
    return {"SCHEMA": K.SET_BINDINGS_SCHEMA, "task": "T216-V", "keys": ["FLOOR"],
            "approved_rules": {"Q-X A": "answered owner question Q-X (a)"},
            "closure_strip_items": ["FIN.FLOOR.PORCELAIN [m2]"], "sets": sets}


def score(b=None, lns=None, rel=None):
    km = key_map() if b is None else K.with_set_bindings(key_map(), b)
    eng, rep = K.engine_rows(lines() if lns is None else lns, release_report() if rel is None else rel, km)
    res = K.S.score(eng, K.reference_rows(normalised(), km))
    return eng, rep, res["lines"][0], res


# ---- without the flag nothing changes ----------------------------------------------------------------------------------

def test_without_bindings_the_rows_and_report_are_unchanged():
    eng, rep, ln, _ = score()
    cond = [e for e in eng if e["id"].startswith("COND:")]
    assert [e["id"] for e in cond] == ["COND:RC:S-A:FLOOR", "COND:RC:S-B:FLOOR"]
    assert all(e["status"] == "HELD" and e["qty"] is None and set(e) == {"id", "trade", "unit", "qty", "status",
                                                                        "key", "surface"} for e in cond)
    assert "set_bindings" not in rep and ln["outcome"] == "HELD"


def test_cli_without_the_flag_is_byte_identical_to_the_v1_and_v2_functions(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "BOQ_LINES.json").write_text(json.dumps(lines()), encoding="utf-8")
    (run / "BOQ_RELEASE_REPORT.json").write_text(json.dumps(release_report()), encoding="utf-8")
    for n, d in (("km.json", key_map()), ("ref.json", normalised()),
                 ("ver.json", {"schema": V.VERDICTS_SCHEMA, "verdicts": []})):
        (tmp_path / n).write_text(json.dumps(d), encoding="utf-8")
    args = ["--run", str(run), "--reference", str(tmp_path / "ref.json"), "--key-map", str(tmp_path / "km.json"),
            "--out", str(tmp_path / "o.json"), "--markdown", str(tmp_path / "o.md"), "--v2-out",
            str(tmp_path / "v2.json"), "--v2-markdown", str(tmp_path / "v2.md"), "--v2-label", "A",
            "--v2-verdicts", str(tmp_path / "ver.json")]
    assert K.main(args) == 0
    res = K.run(run, normalised(), key_map())
    assert (tmp_path / "o.json").read_text(encoding="utf-8") == json.dumps(res, ensure_ascii=False, indent=1)
    assert (tmp_path / "o.md").read_text(encoding="utf-8") == K.S.markdown(res)
    r2 = V.build(run, "A", normalised(), key_map(), {"schema": V.VERDICTS_SCHEMA, "verdicts": []})
    assert (tmp_path / "v2.json").read_text(encoding="utf-8") == json.dumps(r2, ensure_ascii=False, indent=1)
    assert (tmp_path / "v2.md").read_text(encoding="utf-8") == V.markdown(r2)


# ---- bound, partly bound -----------------------------------------------------------------------------------------------

def test_both_sets_bound_the_line_is_compared_with_the_assumed_part_apart():
    eng, rep, ln, res = score(bindings())
    assert ln["outcome"] == "COMPARED"
    assert abs(ln["engine_qty"] - 50.25) < TOL and abs(ln["signed_error"] + 1.75) < TOL
    assert abs(res["buckets"][0]["wape"] - 1.75 / 52.0) < TOL
    a = next(e for e in eng if e["id"] == "COND:RC:S-A:FLOOR")
    assert a["qty"] == 1.80 and a["evidence"] == "ASSUMED — OWNER-APPROVED" and a["closure_strip_m2"] == 0.18
    k = rep["set_bindings"]["keys"]["FLOOR"]
    assert k["released_m2"] == 46.25 and k["released_lines"] == 2
    assert k["assumed_owner_approved_m2"] == 4.0 and len(k["bound_sets"]) == 2
    assert k["held_sets"] == [] and k["held_lines"] == [] and k["line_total"] == 50.25
    assert {b["verdict_commit"] for b in k["bound_sets"]} == {"abc1234"}


def test_one_bound_one_unbound_keeps_the_line_held_never_a_partial_sum():
    eng, rep, ln, _ = score(bindings(("A",)))
    assert ln["outcome"] == "HELD" and ln["engine_qty"] is None
    b = next(e for e in eng if e["id"] == "COND:RC:S-B:FLOOR")
    assert b["status"] == "HELD" and b["qty"] is None and b["binding"] == "UNBOUND"
    k = rep["set_bindings"]["keys"]["FLOOR"]
    assert k["line_total"] is None and k["assumed_owner_approved_m2"] == 1.8
    assert [h["set"] for h in k["held_sets"]] == ["COND:RC:S-B"]


def test_a_held_binding_stays_held_with_its_reason():
    b = bindings()
    b["sets"][1] = {"set_id": "RC:S-B", "kind": "REVIEW_CLASSIFICATION", "status": "HELD",
                    "reason": "a doorless cell is attached (D-C3)"}
    _, rep, ln, _ = score(b)
    assert ln["outcome"] == "HELD"
    assert rep["set_bindings"]["keys"]["FLOOR"]["held_sets"][0]["reason"] == "a doorless cell is attached (D-C3)"


def test_a_held_engine_line_keeps_the_line_held_even_with_every_set_bound():
    lns = lines() + [line("F3", "FIN.FLOOR.PORCELAIN", "m2", "BLOCKED_RFI", None, "R3:floor")]
    _, rep, ln, _ = score(bindings(), lns=lns)
    assert ln["outcome"] == "HELD" and rep["set_bindings"]["keys"]["FLOOR"]["held_lines"] == ["F3"]
    assert rep["set_bindings"]["keys"]["FLOOR"]["line_total"] is None


def test_a_key_the_file_does_not_name_is_untouched():
    b = bindings()
    b["keys"] = ["OTHER"]
    eng, rep, ln, _ = score(b)
    assert ln["outcome"] == "HELD"
    assert all(e["status"] == "HELD" and "binding" not in e for e in eng if e["id"].startswith("COND:"))


def test_bound_scenario_without_a_key_item_stays_held_never_zero():
    rel = release_report()
    rel["categories"]["CONDITIONAL"]["scenario_sets"][1]["by_scenario"]["WET_SCOPE"] = {"FIN.WP.FLOOR [m2]": 2.20}
    b = bindings()
    b["sets"][1]["quantities"] = {"FIN.WP.FLOOR [m2]": 2.20}
    eng, rep, ln, _ = score(b, rel=rel)
    e = next(x for x in eng if x["id"] == "COND:RC:S-B:FLOOR")
    assert e["qty"] is None and e["status"] == "HELD" and ln["outcome"] == "HELD"


def test_a_binding_for_a_set_this_run_does_not_hold_is_listed_unused():
    b = bindings()
    b["sets"].append(bset("RC:S-Z", "RZ", {"FIN.FLOOR.WET_TILE [m2]": 1.0}))
    _, rep, ln, _ = score(b)
    assert rep["set_bindings"]["unused_bindings"] == ["RC:S-Z"] and ln["outcome"] == "COMPARED"


# ---- adverse: refused ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("mutate,msg", [
    (lambda b: b["sets"][0].pop("verdict"), "verdict commit"),
    (lambda b: b["sets"][0]["verdict"].update(commit=""), "verdict commit"),
    (lambda b: b["sets"][0]["verdict"].update(commit="not-a-sha"), "verdict commit"),
    (lambda b: b["sets"][0]["verdict"].update(source=" "), "verdict commit"),
    (lambda b: b["sets"][0]["evidence"].update(fixture_symbol=""), "fixture_symbol"),
    (lambda b: b["sets"][0]["evidence"].pop("printed_size"), "printed_size"),
    (lambda b: b["sets"][0].update(rule_id="Q-Y B"), "approved answered owner rule"),
    (lambda b: b["approved_rules"].update({"Q-X A": ""}), "no answered-owner source"),
    (lambda b: b.update(SCHEMA="OTHER"), "schema"),
    (lambda b: b.update(keys=[]), "names the keys"),
    (lambda b: b["sets"].append(copy.deepcopy(b["sets"][0])), "repeated"),
    (lambda b: b["sets"][0].update(status="VERIFIED"), "status"),
    (lambda b: b["sets"][0].update(kind="DOOR_OWNER_MINIMUM"), "not a wet / dry review set"),
])
def test_refused_binding_files(mutate, msg):
    b = bindings()
    mutate(b)
    with pytest.raises(ValueError, match=msg):
        score(b)


def test_a_binding_that_would_also_carry_the_threshold_strip_is_refused():
    b = bindings()
    b["sets"][0]["quantities"]["FIN.FLOOR.PORCELAIN [m2]"] = 0.18      # the strip left in a space with a door closure
    b["sets"][0]["closure_strip"] = None
    with pytest.raises(ValueError, match="one strip, one line"):
        score(b)


def test_a_stale_binding_is_refused():
    b = bindings()
    b["sets"][1]["quantities"]["FIN.FLOOR.WET_TILE [m2]"] = 2.21
    with pytest.raises(ValueError, match="stale or foreign"):
        score(b)
    b = bindings()
    b["sets"][0]["closure_strip"]["m2"] = 0.20
    with pytest.raises(ValueError, match="closure strip"):
        score(b)


def test_binding_a_set_the_run_holds_as_another_kind_is_refused():
    rel = release_report()
    rel["categories"]["CONDITIONAL"]["scenario_sets"][1]["kind"] = "SCOPE_OPTION"
    with pytest.raises(ValueError, match="not REVIEW_CLASSIFICATION"):
        score(bindings(), rel=rel)


def test_binding_a_scenario_the_set_does_not_have_is_refused():
    b = bindings()
    b["sets"][1]["scenario"] = "LAUNDRY_SCOPE"
    with pytest.raises(ValueError, match="no LAUNDRY_SCOPE scenario"):
        score(b)


# ---- scoreboard v2 / v2.1 and the CLI -----------------------------------------------------------------------------------

def _files(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "BOQ_LINES.json").write_text(json.dumps(lines()), encoding="utf-8")
    (run / "BOQ_RELEASE_REPORT.json").write_text(json.dumps(release_report()), encoding="utf-8")
    for n, d in (("km.json", key_map()), ("ref.json", normalised()), ("sb.json", bindings()),
                 ("ver.json", {"schema": V.VERDICTS_SCHEMA, "verdicts": []})):
        (tmp_path / n).write_text(json.dumps(d), encoding="utf-8")
    return run


@pytest.mark.parametrize("layout", [V.LAYOUT_V2, V.LAYOUT_FIVE])
def test_scoreboard_v2_compares_the_floor_line_with_the_flag_only(tmp_path, layout):
    run = _files(tmp_path)
    ver = {"schema": V.VERDICTS_SCHEMA, "verdicts": []}
    kw = {"layout": layout}
    off = V.build(run, "A", normalised(), key_map(), ver, **kw)["sides"][0]
    on = V.build(run, "A", normalised(), K.with_set_bindings(key_map(), bindings()), ver, **kw)["sides"][0]
    assert off["buckets_v1"][0]["compared"] == 0 and on["buckets_v1"][0]["compared"] == 1
    assert "2 conditional review sets" in off["rows"][0]["cells"][-2] and on["rows"][0]["cells"][-2] == "0 ref lines HELD"
    assert on["adapter"]["set_bindings"]["keys"]["FLOOR"]["assumed_owner_approved_m2"] == 4.0


def test_cli_with_the_flag_names_the_binding_column(tmp_path):
    run = _files(tmp_path)
    args = ["--run", str(run), "--reference", str(tmp_path / "ref.json"), "--key-map", str(tmp_path / "km.json"),
            "--out", str(tmp_path / "o.json"), "--markdown", str(tmp_path / "o.md"), "--set-bindings",
            str(tmp_path / "sb.json"), "--v2-out", str(tmp_path / "v2.json"), "--v2-markdown",
            str(tmp_path / "v2.md"), "--v2-label", "A side", "--v2-verdicts", str(tmp_path / "ver.json")]
    assert K.main(args) == 0
    for md in ("o.md", "v2.md"):
        t = (tmp_path / md).read_text(encoding="utf-8")
        assert "Binding: ASSUMED — OWNER-APPROVED" in t and "| FLOOR | 46.2500 on 2 | 4.0000 on 2 |" in t
        assert "| 50.2500 |" in t
    o = json.loads((tmp_path / "o.json").read_text(encoding="utf-8"))
    assert o["adapter"]["set_bindings"]["keys"]["FLOOR"]["line_total"] == 50.25


# ---- the development villa's binding file --------------------------------------------------------------------------------

def test_development_villa_binding_file_reproduces():
    r = subprocess.run([sys.executable, "-I", "-B", str(T216 / "build_set_bindings.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_development_villa_floor_line_with_the_binding_file():
    inp = json.loads((T208 / "ALSENAN_T208_INPUT.json").read_text(encoding="utf-8"))
    sb = json.loads((T216 / "ALSENAN_SET_BINDINGS_T216.json").read_text(encoding="utf-8"))
    km_full = json.loads((ROOT / "tests" / "alsenan" / "T001B_KEY_MAP.json").read_text(encoding="utf-8"))
    km = dict(km_full, keys=[k for k in km_full["keys"] if k["key"] == "FLOOR.INTERNAL"])
    ref = json.loads((ROOT / "tests" / "alsenan" / "registers_b1" / "BENCHMARK_NORMALISED.json")
                     .read_text(encoding="utf-8"))
    rel = {"categories": {"CONDITIONAL": {"scenario_sets": inp["conditional_sets"]}}}
    eng, rep, = K.engine_rows(inp["lines"], rel, K.with_set_bindings(km, sb))
    ln = K.S.score(eng, K.reference_rows(ref, km))["lines"][0]
    k = rep["set_bindings"]["keys"]["FLOOR.INTERNAL"]
    assert ln["outcome"] == "COMPARED" and abs(ln["engine_qty"] - 385.633867) < 1e-6
    assert ln["reference_qty"] == 409.58 and round(100 * ln["signed_error"] / 409.58, 2) == -5.85
    assert abs(k["released_m2"] - 376.285672) < 1e-6 and k["assumed_owner_approved_m2"] == 9.348195
    assert sorted(b["set"] for b in k["bound_sets"]) == ["COND:REVIEW_CLASSIFICATION:GF:GF-R8496F0",
                                                        "COND:REVIEW_CLASSIFICATION:GF:GF-RD36087",
                                                        "COND:REVIEW_CLASSIFICATION:GF:GF-RDBD4F9"]
    # the two closure strips 0.150 / 0.180 stay in their ARCH.THRESHOLD lines, never in the floor key
    assert sorted(b["closure_strip_not_in_key_m2"] or 0 for b in k["bound_sets"]) == [0, 0.15, 0.18]
    assert rep["set_bindings"]["unused_bindings"] == []
