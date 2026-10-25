"""T-275: the sealed-input guard in front of the scoreboard, the scoreboard key map and census V2
(tools/scoreboard_guarded.py) on a hand-made NON-client villa SG-1. No client drawing: the two "drawings" are a few
made-up bytes in tmp_path; only their sha256 matter. Every expectation is written by hand before running the tool.

Villa SG-1 (project id SG-1): plan drawing P (b"SG-1 plan rev A"), structural drawing S (b"SG-1 structure rev A").
Architectural lines carry the revision set of P, route G lines the revision set of S (as the real engine does).
  footings  F1 2.00 x 2.00 x 0.50 = 2.000 m3, F2 1.50 x 1.50 x 0.50 = 1.125 m3        -> 3.125 m3 (SOURCE_DERIVED)
  slab      SL1 BLOCKED_RFI (thickness not printed)                                  -> HELD, quantity UNKNOWN
  paint     room R1 4.00 x 3.00, height 2.80: 2 x (4.00 + 3.00) x 2.80 = 39.200 m2   (MEASURED)
Reference rows (a made-up comparison list, not a freelancer's): FOOT 3.000 m3, SLAB 6.000 m3, WALL 40.000 m2.
Scoreboard by hand:
  CONCRETE m3: 2 ref lines, coverage 100.00, compared 1 (FOOT), WAPE |3.125 - 3.0| / 3.0 = 4.17 %, signed +4.17 %,
               held 1 ref line (SLAB: 1 engine line UNKNOWN, no bound)
  PAINT m2:    1 ref line, compared 1, WAPE |39.2 - 40.0| / 40.0 = 2.00 %, signed -2.00 %
Candidate SG-1.C: F2 re-measured 1.60 x 1.60 x 0.50 = 1.280 m3 -> footings 3.280 m3: WAPE 0.28 / 3.0 = 9.33 %.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL  # noqa: E402
from tools import alsenan_keymap as K  # noqa: E402
from tools import scoreboard_guarded as SG  # noqa: E402
from tools import scoreboard_v2 as V2  # noqa: E402
from tools import v30_gate_b_v2 as G  # noqa: E402

PID = "SG-1"


def h(b):
    return hashlib.sha256(b).hexdigest()


def rev(*shas):
    return h("|".join(sorted(shas)).encode())


def ln(v, eid, code, unit, state, net, *, route=False, revision=None, project=None):
    return BL.make_line(project_id=project or PID, revision_set_sha256=revision or (v["rev_s"] if route else v["rev_p"]),
                        item_code=code, unit=unit, evidence_state=state,
                        measured_net=net if state in BL.QUANTITY_STATES else None, element_id=eid, floor="GF",
                        formula="hand (test)", rule_id="UP-SYN", rule_version="1",
                        rfi={"question": "not printed"} if state == "BLOCKED_RFI" else None)


def run_lines(v, f2=1.125):
    return [ln(v, "F1", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 2.0, route=True),
            ln(v, "F2", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", f2, route=True),
            ln(v, "SL1", "STR.CONC.SLAB", "m3", "BLOCKED_RFI", None, route=True),
            ln(v, "R1:paint", "FIN.PAINT", "m2", "MEASURED", 39.2)]


def reference():
    rec = lambda rid, unit, q: {"id": rid, "unit": unit, "qty": q, "row_kind": "COVER_TOTAL", "trade": "T"}  # noqa
    return {"records": [rec("R-FOOT", "m3", 3.0), rec("R-SLAB", "m3", 6.0), rec("R-WALL", "m2", 40.0)]}


def key_map():
    return {"reference_row_kinds": ["COVER_TOTAL"], "keys": [
        {"key": "FOOT", "trade": "CONCRETE", "reference_id": "R-FOOT", "item_codes": ["STR.CONC.FOOTING"]},
        {"key": "SLAB", "trade": "CONCRETE", "reference_id": "R-SLAB", "item_codes": ["STR.CONC.SLAB"]},
        {"key": "WALL", "trade": "PAINT", "reference_id": "R-WALL", "item_codes": ["FIN.PAINT"]}]}


def verdicts():
    return {"schema": V2.VERDICTS_SCHEMA, "verdicts": [
        {"ref_id": "R-FOOT", "kind": "REMEASURE", "scope": "WHOLE", "source": "BOARD note (test)", "commit": "abc1234",
         "method": V2.REMEASURE_METHOD, "unit": "m3", "engine_qty": 3.125, "checker_qty": 3.125}]}


def wj(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def make_run(v, name="run", lines=None, project=PID, drawings=None, status="RUN_NO_EXPECTED_FIGURES"):
    d = v["dir"] / name
    d.mkdir()
    lines = run_lines(v) if lines is None else lines
    (d / "BOQ_LINES.json").write_text(BL.dumps(lines), encoding="utf-8")
    wj(d / "BOQ_RELEASE_REPORT.json", {"categories": {"CONDITIONAL": {"scenario_sets": []}}})
    wj(d / "MATERIAL_RESULTS.json", {"results": []})
    wj(d / "COVERAGE.json", {"families": []})
    outs = {n: h((d / n).read_bytes()) for n in ("BOQ_LINES.json", "MATERIAL_RESULTS.json", "COVERAGE.json")}
    man = {"schema": "URBAN_BASELINE_MANIFEST_V1", "baseline_id": "SG-1-RELEASED", "status": status,
           "spec_sha256": "0" * 64, "project": project, "engine": {"commit": "abc1234"},
           "inputs": drawings if drawings is not None else [dict(x) for x in v["drawings"]],
           "run": {"exit_code": 0, "line_count": len(lines), "outputs_sha256": outs}}
    wj(d / "BASELINE_MANIFEST.json", man)
    return d


def make_candidate(v, name="SG1C_BOQ_LINES.json", lines=None, project=PID, drawings=None):
    lines = run_lines(v, f2=1.28) if lines is None else lines
    p = v["dir"] / name
    p.write_text(BL.dumps(lines), encoding="utf-8")
    m = G.build_candidate_manifest(lines, h(p.read_bytes()), candidate_version="SG-1.C", code_commit="abc1234",
                                   project_id=project, drawings=drawings or v["drawings"])
    mp = wj(v["dir"] / (name + ".manifest.json"), m)
    return p, mp


@pytest.fixture()
def v(tmp_path):
    p, s = tmp_path / "sg1_plan.dxf", tmp_path / "sg1_structure.dxf"
    p.write_bytes(b"SG-1 plan rev A")
    s.write_bytes(b"SG-1 structure rev A")
    dr = [{"role": "plan", "file": p.name, "size": p.stat().st_size, "sha256": h(p.read_bytes())},
          {"role": "structural", "file": s.name, "size": s.stat().st_size, "sha256": h(s.read_bytes())}]
    v = {"dir": tmp_path, "drawings": dr, "rev_p": rev(dr[0]["sha256"]), "rev_s": rev(dr[1]["sha256"])}
    v["reference"] = wj(tmp_path / "REFERENCE_NORMALISED.json", reference())
    v["key_map"] = wj(tmp_path / "KEY_MAP.json", key_map())
    v["verdicts"] = wj(tmp_path / "VERDICTS.json", verdicts())
    return v


def sb_args(v, run, out, *extra):
    return ["--run", str(run), "--label", "A (SG-1 released)", "--reference", str(v["reference"]), "--key-map",
            str(v["key_map"]), "--verdicts", str(v["verdicts"]), "--out", str(out), "--markdown",
            str(out.with_suffix(".md")), "--heading", "2026-10-25 05:00 UTC", *extra]


def refused(capsys, argv, *codes, out=None):
    rc = SG.main(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    got = sorted(set(re.findall(r"SCOREBOARD REFUSED \[([A-Z_]+)\]", err)))
    assert got == sorted(codes), err
    if out is not None:
        assert not out.exists() and not out.with_suffix(".md").exists()     # nothing written on refusal
    return err


@pytest.fixture()
def no_scorer(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the scorer ran on a refused input")
    monkeypatch.setattr(V2, "build", boom)
    monkeypatch.setattr(K, "run", boom)


# ------------------------------------------------------------------------------------------------- normal cases
def test_hand_values_and_byte_identical_to_the_direct_scoreboard(v, capsys):
    run = make_run(v)
    rc = SG.main(["scoreboard"] + sb_args(v, run, v["dir"] / "g.json"))
    g_out = capsys.readouterr().out
    assert rc == 0
    assert V2.main(sb_args(v, run, v["dir"] / "d.json")) == 0
    d_out = capsys.readouterr().out
    assert g_out == d_out
    for sfx in (".json", ".md"):
        assert (v["dir"] / ("g" + sfx)).read_bytes() == (v["dir"] / ("d" + sfx)).read_bytes()
    res = json.loads((v["dir"] / "g.json").read_text(encoding="utf-8"))
    rows = {(r["trade"], r["unit"]): dict(zip(V2.COLUMNS, r["cells"])) for r in res["sides"][0]["rows"]}
    c = rows[("CONCRETE", "m3")]
    assert (c["Ref lines"], c["Coverage %"], c["Compared"], c["WAPE %"], c["Signed %"]) == \
        ("2", "100.00", "1", "4.17", "4.17")
    assert c["Verified share %"] == "50.00 (1 / 2)"
    assert c["Held or UNKNOWN"] == "1 ref line HELD; 1 engine line: 1 UNKNOWN (no bound)"      # never 0
    p = rows[("PAINT", "m2")]
    assert (p["Compared"], p["WAPE %"], p["Signed %"]) == ("1", "2.00", "-2.00")


def test_candidate_with_its_manifest_and_a_reproducible_guard_record(v, capsys):
    run = make_run(v)
    cl, cm = make_candidate(v)
    extra = ["--candidate-lines", str(cl), "--candidate-label", "SG-1.C", "--candidate-manifest", str(cm)]
    for n in ("g1", "g2"):
        assert SG.main(["scoreboard"] + sb_args(v, run, v["dir"] / f"{n}.json", *extra[:4], *extra[4:],
                                                "--guard-record", str(v["dir"] / f"{n}_GUARD.json"))) == 0
    capsys.readouterr()
    assert V2.main(sb_args(v, run, v["dir"] / "d.json", *extra[:4])) == 0
    assert (v["dir"] / "g1.json").read_bytes() == (v["dir"] / "d.json").read_bytes()
    g1, g2 = ((v["dir"] / f"{n}_GUARD.json").read_bytes() for n in ("g1", "g2"))
    assert g1 == g2 and str(v["dir"]) not in g1.decode("utf-8")              # no path, no timestamp
    rec = json.loads(g1)
    assert rec["schema"] == SG.RECORD_SCHEMA and rec["command"] == "scoreboard"
    sides = {s["side"]: s for s in rec["sides"]}
    assert sides["run"]["kind"] == "RELEASE" and sides["candidate"]["kind"] == "CANDIDATE"
    assert {i["drawing_roles"][0] for i in sides["run"]["identities"]} == {"plan", "structural"}
    assert [x["role"] for x in rec["not_pinned"]] == ["run:BOQ_RELEASE_REPORT.json"]
    cand = json.loads((v["dir"] / "g1.json").read_text(encoding="utf-8"))["sides"][1]
    foot = next(r for r in cand["rows"] if r["trade"] == "CONCRETE")
    assert dict(zip(V2.COLUMNS, foot["cells"]))["WAPE %"] == "9.33"           # 0.28 / 3.0


def test_release_run_without_project_id_beside_a_candidate_on_the_same_drawings(v, capsys):
    lines = [ln(v, x["location"]["element_id"], x["item_code"], x["unit"], x["evidence_state"], x["measured_net"],
                route=x["item_code"].startswith("STR."), project="new project") for x in run_lines(v)]
    run = make_run(v, lines=lines, project=None)
    cl, cm = make_candidate(v)
    assert SG.main(["scoreboard"] + sb_args(v, run, v["dir"] / "g.json", "--candidate-lines", str(cl),
                                            "--candidate-label", "SG-1.C", "--candidate-manifest", str(cm))) == 0


# ------------------------------------------------------------------------------------------------ adverse cases
def test_registered_sealed_sha256_under_another_name_refused(v, capsys, no_scorer, tmp_path):
    run = make_run(v)
    reg = wj(tmp_path / "REG.json", {"schema": G.SEALED_SCHEMA, "entries": [
        {"kind": "SEALED_FILE", "project_id": "SG-SEALED", "label": "a sealed test take-off",
         "sha256": h(v["reference"].read_bytes()), "names": ["sealed_takeoff.json"]}]})
    out = v["dir"] / "g.json"
    err = refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--sealed-registry", str(reg)), "SEALED", out=out)
    assert "whatever its name" in err


def test_named_sealed_file_refused_unopened(v, capsys, no_scorer):
    run = make_run(v)
    sealed = v["dir"] / "site_benchmark.json"                                    # engine/reference_mapping.py SEALED
    sealed.write_bytes(b"\xff not even json")                                    # proves it is never parsed
    out = v["dir"] / "g.json"
    args = sb_args(v, run, out)
    args[args.index("--reference") + 1] = str(sealed)
    refused(capsys, ["scoreboard"] + args, "SEALED", out=out)


def test_two_projects_refused(v, capsys, no_scorer):
    run = make_run(v)
    other = [ln(v, "F1", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 2.0, route=True, project="SG-2")]
    cl, cm = make_candidate(v, lines=other, project="SG-2")
    out = v["dir"] / "g.json"
    refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--candidate-lines", str(cl), "--candidate-label", "C",
                                             "--candidate-manifest", str(cm)), "PROJECT_MIX", out=out)


def test_unpinned_drawing_refused(v, capsys, no_scorer):
    # a line measured on a drawing the run's manifest does not pin: refused by identity, whatever label it prints
    lines = run_lines(v) + [ln(v, "F9", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 1.0, route=True,
                               revision=rev(h(b"another villa's structure")))]
    run = make_run(v, lines=lines)
    out = v["dir"] / "g.json"
    refused(capsys, ["scoreboard"] + sb_args(v, run, out), "REVISION_MIX", out=out)


def test_line_without_identity_refused(v, capsys, no_scorer):
    lines = run_lines(v)
    bare = copy.deepcopy(lines[3])
    del bare["project"]
    run = v["dir"] / "bare"
    run.mkdir()
    (run / "BOQ_LINES.json").write_text(json.dumps(lines[:3] + [bare]), encoding="utf-8")
    man = {"schema": "URBAN_BASELINE_MANIFEST_V1", "baseline_id": "X", "status": "RUN_NO_EXPECTED_FIGURES",
           "project": PID, "inputs": v["drawings"], "engine": {"commit": "a"},
           "run": {"line_count": 4, "outputs_sha256": {"BOQ_LINES.json": h((run / "BOQ_LINES.json").read_bytes())}}}
    wj(run / "BASELINE_MANIFEST.json", man)
    refused(capsys, ["scoreboard"] + sb_args(v, run, v["dir"] / "g.json"), "REVISION_MIX")


def test_manifest_problems_refused(v, capsys, no_scorer):
    out = v["dir"] / "g.json"
    run = make_run(v, name="nomanifest")
    (run / "BASELINE_MANIFEST.json").unlink()                                  # an unpinned run
    refused(capsys, ["scoreboard"] + sb_args(v, run, out), "MANIFEST_MISSING", out=out)
    run = make_run(v, name="nodrawing", drawings=[])                           # a manifest that pins no drawing
    refused(capsys, ["scoreboard"] + sb_args(v, run, out), "MANIFEST_INVALID", out=out)
    run = make_run(v, name="failed", status="ENGINE_EXIT_NONZERO")
    refused(capsys, ["scoreboard"] + sb_args(v, run, out), "MANIFEST_INVALID", out=out)
    run = make_run(v, name="drift")                                            # lines edited after the run
    (run / "BOQ_LINES.json").write_text(BL.dumps(run_lines(v, f2=1.2)), encoding="utf-8")
    refused(capsys, ["scoreboard"] + sb_args(v, run, out), "MANIFEST_MISMATCH", out=out)


def test_candidate_without_manifest_or_on_another_revision_refused(v, capsys, no_scorer):
    run = make_run(v)
    out = v["dir"] / "g.json"
    cl, cm = make_candidate(v)
    refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--candidate-lines", str(cl), "--candidate-label", "C"),
            "MANIFEST_MISSING", out=out)
    dr2 = [dict(v["drawings"][0], sha256=h(b"SG-1 plan rev B")), v["drawings"][1]]
    lines2 = [x if x["item_code"].startswith("STR.") else
              ln(v, "R1:paint", "FIN.PAINT", "m2", "MEASURED", 39.2, revision=rev(dr2[0]["sha256"]))
              for x in run_lines(v)]
    cl2, cm2 = make_candidate(v, name="REVB_BOQ_LINES.json", lines=lines2, drawings=dr2)
    refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--candidate-lines", str(cl2), "--candidate-label", "C",
                                             "--candidate-manifest", str(cm2)), "DRAWING_MISMATCH", out=out)


def test_sealed_drawing_and_sealed_project_refused(v, capsys, no_scorer, tmp_path):
    run = make_run(v)
    out = v["dir"] / "g.json"
    reg = wj(tmp_path / "REG1.json", {"schema": G.SEALED_SCHEMA, "entries": [
        {"kind": "SEALED_FILE", "project_id": "SG-SEALED", "label": "a sealed structure",
         "sha256": v["drawings"][1]["sha256"], "names": []}]})
    refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--sealed-registry", str(reg)), "SEALED", out=out)
    reg2 = wj(tmp_path / "REG2.json", {"schema": G.SEALED_SCHEMA, "entries": [
        {"kind": "SEALED_PROJECT", "project_id": PID, "label": "SG-1 sealed before its one use", "sha256": None}]})
    refused(capsys, ["scoreboard"] + sb_args(v, run, out, "--sealed-registry", str(reg2)), "SEALED", out=out)


def test_default_registry_names_refused(v, capsys, no_scorer):
    run = make_run(v)
    q = v["dir"] / "QORTUBA_BENCHMARK_SEAL.json"
    q.write_text("{}", encoding="utf-8")
    args = sb_args(v, run, v["dir"] / "g.json")
    args[args.index("--verdicts") + 1] = str(q)
    refused(capsys, ["scoreboard"] + args, "SEALED")


# ---------------------------------------------------------------------------------------------------- key map
def km_args(v, run, out):
    return ["--run", str(run), "--reference", str(v["reference"]), "--key-map", str(v["key_map"]), "--out",
            str(out), "--markdown", str(out.with_suffix(".md")), "--v2-out", str(out.with_name(out.stem + "_v2.json")),
            "--v2-label", "A", "--v2-verdicts", str(v["verdicts"])]


def test_keymap_byte_identical_and_refused_like_the_scoreboard(v, capsys, monkeypatch):
    run = make_run(v)
    assert SG.main(["keymap"] + km_args(v, run, v["dir"] / "g.json") + ["--guard-record",
                                                                         str(v["dir"] / "G.json")]) == 0
    g_out = capsys.readouterr().out
    assert K.main(km_args(v, run, v["dir"] / "d.json")) == 0
    assert capsys.readouterr().out == g_out
    for a, b in (("g.json", "d.json"), ("g.md", "d.md"), ("g_v2.json", "d_v2.json")):
        assert (v["dir"] / a).read_bytes() == (v["dir"] / b).read_bytes()
    assert json.loads((v["dir"] / "G.json").read_text(encoding="utf-8"))["command"] == "keymap"
    bad = make_run(v, name="nomanifest")
    (bad / "BASELINE_MANIFEST.json").unlink()
    monkeypatch.setattr(K, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("scorer ran")))
    refused(capsys, ["keymap"] + km_args(v, bad, v["dir"] / "x.json"), "MANIFEST_MISSING", out=v["dir"] / "x.json")


# ------------------------------------------------------------------------------------------------------- census
def test_census_on_pinned_sides_by_hand(v, capsys):
    run = make_run(v)
    cl, cm = make_candidate(v)
    out = v["dir"] / "census"
    assert SG.main(["census", "--released", str(run), "--candidate", str(cl), str(cm), "--out", str(out)]) == 0
    capsys.readouterr()
    r = json.loads((out / "run_CENSUS_V2.json").read_text(encoding="utf-8"))
    c = json.loads((out / "SG1C_BOQ_LINES_CENSUS_V2.json").read_text(encoding="utf-8"))
    foot = lambda d: next(x for x in d["rows"] if "STR.CONC.FOOTING" in (x.get("item_codes") or []))  # noqa
    assert foot(r)["run_state"] == "FOUND" and abs(foot(r)["by_unit"]["m3"]["found_qty"] - 3.125) < 1e-9
    assert abs(foot(c)["by_unit"]["m3"]["found_qty"] - 3.28) < 1e-9
    slab = next(x for x in r["rows"] if "STR.CONC.SLAB" in (x.get("item_codes") or []))
    assert slab["run_state"] == "HELD" and slab["by_unit"]["m3"]["found_lines"] == 0          # held, never 0 found
    rec = json.loads((out / "GUARD_RECORD.json").read_text(encoding="utf-8"))
    assert {s["side"] for s in rec["sides"]} == {"released:run", "candidate:SG1C_BOQ_LINES"}
    assert set(r["pinned_by"]) <= set("0123456789abcdef") and len(r["pinned_by"]) == 64


def test_census_refuses_a_drifted_material_file_and_writes_nothing(v, capsys):
    run = make_run(v)
    wj(run / "MATERIAL_RESULTS.json", {"results": [], "edited": True})
    out = v["dir"] / "census"
    refused(capsys, ["census", "--released", str(run), "--out", str(out)], "MANIFEST_MISMATCH")
    assert not out.exists()


# ------------------------------------------------------------------------------------------------------ hygiene
def test_wrapper_is_unwired_and_names_no_project():
    src = (ROOT / "tools" / "scoreboard_guarded.py").read_text(encoding="utf-8")
    assert "release_baseline" not in src                                     # tests/t165 hygiene rule
    named = src.replace("alsenan_keymap", "")                                # a repository tool's module name only
    assert not re.search("77" + "57" + r"|(?i:als[ey]?n[ya]?an)", named)
    for p in list((ROOT / "engine").rglob("*.py")) + list((ROOT / "tools").rglob("*.py")):
        if p.name != "scoreboard_guarded.py":
            assert "scoreboard_guarded" not in p.read_text(encoding="utf-8", errors="ignore"), p
    assert SG.DEFAULT_GUARD_CLASS == "TOOLING"


def test_cli_entry_point_refuses_with_exit_2(v):
    run = make_run(v)
    (run / "BASELINE_MANIFEST.json").unlink()
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "scoreboard_guarded.py"), "scoreboard"]
                       + sb_args(v, run, v["dir"] / "g.json"), capture_output=True, text=True, cwd=str(ROOT))
    assert r.returncode == 2 and "SCOREBOARD REFUSED [MANIFEST_MISSING]" in r.stderr
    assert not (v["dir"] / "g.json").exists()
