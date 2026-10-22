"""T-165: the pinned release-baseline runner (tools/release_baseline.py) on a synthetic villa (tools/arch_synth.py plan +
tools/synthetic_villa_m8.py structural drawing with its printed-storey-height route G profile): no client drawing.

Hand-expected values: the synthetic structural generator writes its design truth by hand from its own coordinates
(villa_m8_<seed>.truth.json, never from the engine): seed 21 has 24 columns, COLUMNS 12.54 m3, storey heights GF 4.0 m /
1F 3.6 m printed in the profile. Without the profile route G cannot know a column height, so all 24 column lines must be
HELD with no quantity; with it they are released at the truth. The per-code figures are checked on a hand-made line list.
Every output goes to pytest's temporary folders.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import release_baseline as RB  # noqa: E402

V6 = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
SEED = 21


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    from engine.source import arch_measure as AM
    from tools import arch_synth as AS
    from tools import synthetic_villa_m8 as SM8
    d = tmp_path_factory.mktemp("t165_villa")
    st = SM8.generate(d, SEED)
    plan = d / "villa.dxf"
    AS.villa(plan)
    facts = d / "facts.json"
    facts.write_text(json.dumps({"schema": AM.FACTS_SCHEMA}), encoding="utf-8")
    truth = json.loads((d / f"villa_m8_{SEED}.truth.json").read_text(encoding="utf-8"))
    return {"dir": d, "plan": plan, "structural": Path(st), "profile": d / f"villa_m8_{SEED}.profile.json",
            "facts": facts, "truth": truth}


def spec(v, *, profile=True, **over):
    s = {"schema": RB.SPEC_SCHEMA, "baseline_id": "synthetic-v29-routeg" + ("-profiled" if profile else ""),
         "method": "ARCH_TAKEOFF_V2.9", "python": f"{sys.version_info.major}.{sys.version_info.minor}",
         "inputs": {"plan": {"sha256": RB.sha256_file(v["plan"]), "size": v["plan"].stat().st_size},
                    "structural": {"sha256": RB.sha256_file(v["structural"])}},
         "conventions": {"path": "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json", "sha256": RB.sha256_file(V6)},
         "profile": {"path": str(v["profile"]), "sha256": RB.sha256_file(v["profile"])} if profile else None,
         "facts": {"path": str(v["facts"]), "sha256": RB.sha256_file(v["facts"])},
         "project": "synthetic-villa", "as_of": "2026-01-01",
         "options": {"no_svg": True, "no_m9_xlsx": True, "no_completeness": False}}
    s.update(over)
    return s


def write_spec(d, s, name="spec.json"):
    p = Path(d) / name
    p.write_text(json.dumps(s, indent=1), encoding="utf-8")
    return p


def code_row(m, code, unit="m3"):
    return next(r for r in m["per_code"] if r["item_code"] == code and r["unit"] == unit)


@pytest.fixture(scope="module")
def runs(villa, tmp_path_factory):
    d = tmp_path_factory.mktemp("t165_runs")
    out = {}
    for tag, prof in (("P1", True), ("P2", True), ("U", False)):
        sp = write_spec(d, spec(villa, profile=prof), f"spec_{tag}.json")
        code, m = RB.run(sp, villa["plan"], villa["structural"], d / tag)
        out[tag] = {"code": code, "m": m, "dir": d / tag, "spec": sp}
    return out


# ---- the run and its manifest

def test_manifest_is_byte_identical_across_two_runs(runs):
    a = (runs["P1"]["dir"] / RB.MANIFEST_NAME).read_bytes()
    b = (runs["P2"]["dir"] / RB.MANIFEST_NAME).read_bytes()
    assert runs["P1"]["code"] == 0 and runs["P1"]["m"]["status"] == "RUN_NO_EXPECTED_FIGURES"
    assert a == b
    m = runs["P1"]["m"]
    assert m["run"]["exit_code"] == 0 and m["run"]["line_count"] > 0
    assert m["run"]["outputs_sha256"]["BOQ_LINES.csv"] == RB.sha256_file(runs["P1"]["dir"] / "BOQ_LINES.csv")


def test_manifest_carries_no_path_and_no_timestamp(runs, villa):
    text = (runs["P1"]["dir"] / RB.MANIFEST_NAME).read_text(encoding="utf-8")
    assert str(villa["dir"]) not in text and str(ROOT) not in text
    assert not re.search(r"\d{2}:\d{2}:\d{2}", text)
    m = runs["P1"]["m"]
    assert [i["file"] for i in m["inputs"]] == ["villa.dxf", villa["structural"].name]
    assert m["pinned_files"]["conventions"]["file"] == "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
    assert m["pinned_files"]["profile"]["file"] == villa["profile"].name
    assert m["spec"]["profile"]["path"] == villa["profile"].name


def test_profile_releases_the_columns_at_the_hand_truth_and_its_absence_holds_them(runs, villa):
    truth = villa["truth"]
    assert truth["components"]["columns"] == 24 and truth["storey_heights"] == {"GF": 4.0, "1F": 3.6}
    p, u = code_row(runs["P1"]["m"], "STR.CONC.COLUMN"), code_row(runs["U"]["m"], "STR.CONC.COLUMN")
    assert (p["lines"], p["released_lines"], p["held_lines"]) == (24, 24, 0)
    assert abs(p["released_qty"] - truth["quantities"]["COLUMNS"]) <= 5e-4          # 12.54 m3
    assert (u["lines"], u["released_lines"], u["held_lines"]) == (24, 0, 24)
    assert u["released_qty"] is None and u["held_low"] is None and u["held_high"] is None   # held is never 0
    # footings need no storey height: the same in both baselines, and at the hand truth
    assert code_row(runs["P1"]["m"], "STR.CONC.FOOTING") == code_row(runs["U"]["m"], "STR.CONC.FOOTING")
    assert abs(code_row(runs["U"]["m"], "STR.CONC.FOOTING")["released_qty"] - truth["quantities"]["FOOTINGS"]) <= 5e-4


def test_compare_names_the_profile_as_the_only_configuration_difference(runs):
    d = RB.compare(runs["U"]["m"], runs["P1"]["m"])
    assert [c["field"] for c in d["config_differences"]] == ["pinned_files"]
    assert d["config_differences"][0]["a"]["profile"] is None
    assert d["config_differences"][0]["b"]["profile"]["sha256"] == runs["P1"]["m"]["spec"]["profile"]["sha256"]
    codes = {(r["item_code"], r["unit"]) for r in d["rows"]}
    assert ("STR.CONC.COLUMN", "m3") in codes and ("STR.CONC.FOOTING", "m3") not in codes
    assert not [c for c in codes if not c[0].startswith("STR.")]   # the profile reaches route G only
    same = RB.compare(runs["P1"]["m"], runs["P2"]["m"])
    assert same["rows"] == [] and same["config_differences"] == [] and same["same_outputs"] is True
    assert d["same_outputs"] is False


def test_expected_figures_reproduced_and_not_reproduced(runs, villa, tmp_path):
    m = runs["P1"]["m"]
    good = {"line_count": m["run"]["line_count"], "boq_lines_csv_sha256": m["run"]["outputs_sha256"]["BOQ_LINES.csv"]}
    code, m2 = RB.run(write_spec(tmp_path, spec(villa, expected=good), "g.json"), villa["plan"], villa["structural"],
                      tmp_path / "good")
    assert code == 0 and m2["status"] == "REPRODUCED" and all(c["match"] for c in m2["expected_check"].values())
    bad = dict(good, line_count=good["line_count"] + 1)
    code, m3 = RB.run(write_spec(tmp_path, spec(villa, expected=bad), "b.json"), villa["plan"], villa["structural"],
                      tmp_path / "bad")
    assert code == 3 and m3["status"] == "NOT_REPRODUCED"
    assert m3["expected_check"]["line_count"] == {"expected": good["line_count"] + 1, "got": good["line_count"],
                                                  "match": False}


def test_cli_run_and_compare(runs, villa, tmp_path, capsys):
    assert RB.main(["run", str(runs["U"]["spec"]), "--plan", str(villa["plan"]), "--structural",
                    str(villa["structural"]), "--out", str(tmp_path / "cli")]) == 0
    assert (tmp_path / "cli" / RB.MANIFEST_NAME).read_bytes() == (runs["U"]["dir"] / RB.MANIFEST_NAME).read_bytes()
    assert RB.main(["compare", str(runs["U"]["dir"] / RB.MANIFEST_NAME), str(runs["P1"]["dir"] / RB.MANIFEST_NAME),
                    "--out", str(tmp_path / "diff.json")]) == 0
    printed = capsys.readouterr().out
    assert "config pinned_files" in printed and "STR.CONC.COLUMN m3" in printed
    assert json.loads((tmp_path / "diff.json").read_text(encoding="utf-8"))["codes_differing"] >= 1


# ---- refusals: nothing is run, nothing is written

def _refused(sp, plan, structural, out, **kw):
    with pytest.raises(RB.Refused) as ex:
        RB.run(sp, plan, structural, out, engine=lambda argv: pytest.fail("the engine must not run"), **kw)
    assert not Path(out).exists()
    return ex.value.problems


def test_a_changed_profile_sha_is_refused(villa, tmp_path):
    prof = tmp_path / "profile.json"
    shutil.copy(villa["profile"], prof)
    s = spec(villa)
    s["profile"] = {"path": str(prof), "sha256": RB.sha256_file(prof)}
    sp = write_spec(tmp_path, s)
    doc = json.loads(prof.read_text(encoding="utf-8"))
    doc["conventions"][0]["base"] = 4.1                                         # one printed value retyped
    prof.write_text(json.dumps(doc), encoding="utf-8")
    p = _refused(sp, villa["plan"], villa["structural"], tmp_path / "out")
    assert len(p) == 1 and p[0].startswith("profile file sha256")


def test_a_missing_facts_file_is_refused(villa, tmp_path):
    s = spec(villa)
    s["facts"] = {"path": str(tmp_path / "gone.json"), "sha256": "0" * 64}
    p = _refused(write_spec(tmp_path, s), villa["plan"], villa["structural"], tmp_path / "out")
    assert p == [f"facts file missing: {tmp_path / 'gone.json'}"]


def test_drawings_must_be_the_pinned_ones(villa, tmp_path):
    sp = write_spec(tmp_path, spec(villa))
    p = _refused(sp, villa["structural"], villa["plan"], tmp_path / "o1")          # swapped
    assert any(x.startswith("plan drawing sha256") for x in p) and any(x.startswith("structural drawing sha256")
                                                                         for x in p)
    p = _refused(sp, villa["plan"], None, tmp_path / "o2")
    assert p == ["the spec pins a structural drawing but --structural is not given"]
    s = spec(villa, profile=False)
    s.update(conventions=None, inputs={"plan": s["inputs"]["plan"], "structural": None})
    p = _refused(write_spec(tmp_path, s, "s2.json"), villa["plan"], villa["structural"], tmp_path / "o3")
    assert p == ["--structural given but the spec pins no structural drawing"]
    s = spec(villa)
    s["inputs"]["plan"]["size"] += 1
    p = _refused(write_spec(tmp_path, s, "s3.json"), villa["plan"], villa["structural"], tmp_path / "o4")
    assert len(p) == 1 and p[0].startswith("plan drawing size")


def test_spec_states_every_choice_and_names_a_released_method(villa, tmp_path):
    s = spec(villa)
    del s["profile"]                                                            # "no profile" must be written as null
    p = _refused(write_spec(tmp_path, s, "a.json"), villa["plan"], villa["structural"], tmp_path / "o1")
    assert "key 'profile' missing (write null to state 'none')" in p
    p = _refused(write_spec(tmp_path, spec(villa, method="ARCH_TAKEOFF_V3.0"), "b.json"), villa["plan"],
                 villa["structural"], tmp_path / "o2")
    assert any("ARCH_METHODS" in x for x in p)
    p = _refused(write_spec(tmp_path, spec(villa, as_of=None, extra=1), "c.json"), villa["plan"], villa["structural"],
                 tmp_path / "o3")
    assert "unknown key 'extra'" in p and "as_of must be 'YYYY-MM-DD'" in p
    s = spec(villa)
    s["options"] = {"no_svg": True}
    p = _refused(write_spec(tmp_path, s, "d.json"), villa["plan"], villa["structural"], tmp_path / "o4")
    assert any(x.startswith("options must give every one") for x in p)


def test_interpreter_and_out_folder_are_checked(villa, tmp_path):
    sp = write_spec(tmp_path, spec(villa, python="3.11"))
    p = _refused(sp, villa["plan"], villa["structural"], tmp_path / "o1", python_version="3.13")
    assert p == ["interpreter is Python 3.13, the spec pins 3.11"]
    full = tmp_path / "full"
    full.mkdir()
    (full / "x.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RB.Refused) as ex:
        RB.run(write_spec(tmp_path, spec(villa), "s2.json"), villa["plan"], villa["structural"], full,
               engine=lambda argv: pytest.fail("the engine must not run"))
    assert "exists and is not empty" in ex.value.problems[0]
    assert sorted(x.name for x in full.iterdir()) == ["x.txt"]


def test_engine_failure_is_recorded_not_hidden(villa, tmp_path):
    code, m = RB.run(write_spec(tmp_path, spec(villa)), villa["plan"], villa["structural"], tmp_path / "out",
                     engine=lambda argv: 2)
    assert code == 4 and m["status"] == "ENGINE_EXIT_NONZERO" and m["run"]["exit_code"] == 2
    assert m["run"]["line_count"] is None and m["per_code"] is None              # no lines: no figures, never 0
    assert m["run"]["outputs_sha256"]["BOQ_LINES.csv"] is None


def test_engine_argv_passes_every_pinned_item(villa, tmp_path):
    seen = []
    RB.run(write_spec(tmp_path, spec(villa)), villa["plan"], villa["structural"], tmp_path / "out",
           engine=lambda argv: seen.append(list(argv)) or 0)
    a = seen[0]
    pairs = {a[i]: a[i + 1] for i in range(len(a) - 1) if a[i].startswith("--") and not a[i + 1].startswith("--")}
    assert a[0] == "arch" and pairs["--method"] == "ARCH_TAKEOFF_V2.9" and pairs["--as-of"] == "2026-01-01"
    assert pairs["--profile"] == str(villa["profile"]) and pairs["--facts"] == str(villa["facts"])
    assert pairs["--conventions"] == str(V6) and pairs["--project"] == "synthetic-villa"
    assert "--no-svg" in a and "--no-m9-xlsx" in a and "--no-completeness" not in a


# ---- per-code figures on a hand-made line list (hand values)

def L(code, unit, state, net=None, low=None, high=None):
    return {"item_code": code, "unit": unit, "evidence_state": state, "measured_net": net,
            "bounded_range": None if low is None else {"low": low, "high": high}}


def test_per_code_figures_by_hand():
    lines = [L("X.A", "m2", "MEASURED", 10.0), L("X.A", "m2", "PROVISIONAL", 2.5),
             L("X.A", "m2", "BOUNDED_EXPOSURE", None, 1.0, 3.0), L("X.A", "m2", "BLOCKED_RFI"),
             L("X.A", "m2", "EXCLUDED_WITH_REASON"),
             L("X.A", "lm", "SOURCE_DERIVED", 7.25),                                # same code, other unit: apart
             L("X.B", "m3", "PROVISIONAL", None),                                   # a quantity state with no number
             L("X.B", "m3", "NOT_APPLICABLE_WITH_EVIDENCE")]
    rows = {(r["item_code"], r["unit"]): r for r in RB.per_code(lines)}
    assert list(rows) == [("X.A", "lm"), ("X.A", "m2"), ("X.B", "m3")]
    a = rows[("X.A", "m2")]
    assert (a["lines"], a["released_lines"], a["released_qty"]) == (5, 2, 12.5)
    assert (a["held_lines"], a["held_bounded_lines"], a["held_low"], a["held_high"], a["held_unbounded_lines"]) == \
        (2, 1, 1.0, 3.0, 1)
    assert a["excluded_lines"] == 1
    assert rows[("X.A", "lm")]["released_qty"] == 7.25
    b = rows[("X.B", "m3")]
    assert (b["released_lines"], b["released_qty"], b["held_lines"], b["held_low"], b["excluded_lines"]) == \
        (0, None, 1, None, 1)                                                     # missing never becomes 0


def test_per_code_is_order_independent():
    lines = [L("X.A", "m2", "MEASURED", 0.1), L("X.A", "m2", "MEASURED", 0.2), L("X.A", "m2", "MEASURED", 0.3)]
    assert RB.per_code(lines) == RB.per_code(list(reversed(lines)))
    assert RB.per_code(lines)[0]["released_qty"] == 0.6


# ---- hygiene

def test_nothing_imports_the_runner_and_it_names_no_project():
    for p in list((ROOT / "engine").rglob("*.py")) + list((ROOT / "tools").rglob("*.py")):
        if p.name == "release_baseline.py":
            continue
        assert "release_baseline" not in p.read_text(encoding="utf-8", errors="ignore"), p
    hyg = re.compile("YEARS" + r" 2013|" + "77" + "57" + r"|(?i:als[ey]?n[ya]?an)")
    for f in ("tools/release_baseline.py", "tests/t165_release_baseline/test_release_baseline.py"):
        assert not hyg.search((ROOT / f).read_text(encoding="utf-8")), f
