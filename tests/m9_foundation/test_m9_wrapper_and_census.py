"""M9 S1 wrapper and coverage census: `urban_boq_m9 run` leaves every route G output byte-identical to `urban_boq_m2
run` (the M2-M8 behaviour is untouched), its canonical lines carry the route's numbers (totals reconcile to the
summary), every one of the 99 families gets a terminal state with its reason, and the small subcommands work."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.source import boq_line as BL
from engine.source import coverage_census as CS
from engine.source import rule_store as RS

ezdxf = pytest.importorskip("ezdxf")

ROOT = Path(__file__).resolve().parents[2]
V6 = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
ROOMS = ROOT / "research/urban_m9_s1/SYNTHETIC_ROOMS_S1.json"


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as M2
    from tools import urban_boq_m9 as M9
    d = tmp_path_factory.mktemp("m9run")
    dxf = SM8.generate(d, 21)
    common = ["--drawings", str(dxf), "--profile", str(d / "villa_m8_21.profile.json"), "--route", "G",
              "--conventions", str(ROOT / V6), "--no-pdf", "--as-of", "2026-01-01"]
    assert M2.main(["run", "--out", str(d / "m2")] + common) == 0
    assert M9.main(["run", "--out", str(d / "m9"), "--rooms", str(ROOMS), "--no-m9-xlsx"] + common) == 0
    return d


def test_route_g_outputs_are_byte_identical(runs):
    a, b = runs / "m2", runs / "m9"
    fa = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()}
    fb = {p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file() and not p.relative_to(b).as_posix().startswith("m9/")}
    assert fa == fb and len(fa) > 20
    diff = [f for f in sorted(fa) if f != "run_log.json" and (a / f).read_bytes() != (b / f).read_bytes()]
    assert diff == []
    la, lb = (json.loads((x / "run_log.json").read_text(encoding="utf-8")) for x in (a, b))
    assert [s["step"] for s in la["steps"]] == [s["step"] for s in lb["steps"]]      # only the timings differ


def test_canonical_lines_reconcile_to_the_route_summary(runs):
    lines = json.loads((runs / "m9/m9/BOQ_LINES.json").read_text(encoding="utf-8"))
    for ln in lines:
        BL.validate(ln)
    s_lines = [ln for ln in lines if ln["item_code"].startswith("STR.")]
    assert len({ln["line_id"] for ln in lines}) == len(lines)
    T = BL.totals(s_lines, by=("trade",))
    from tools import urban_boq_m2 as M2
    R = M2.compute([str(runs / "villa_m8_21.dxf")], profile=str(runs / "villa_m8_21.profile.json"), route="G",
                   conventions=str(ROOT / V6), completeness=True)
    for tr, unit in (("CONCRETE", "m3"), ("REINFORCEMENT", "kg")):
        assert T[(tr,)][unit]["net"] == pytest.approx(R["summary"]["totals"][tr]["PLANNING_BASE"], abs=1e-6)
    p = s_lines[0]["project"]                                    # the same items give the same line ids
    again = {BL.from_route_g(it, project_id=p["project_id"], revision_set_sha256=p["revision_set_sha256"],
                             conventions_set=R["summary"]["conventions"]["set"],
                             conventions_digest=R["summary"]["conventions"]["digest"])["line_id"] for it in R["items"]}
    assert again == {ln["line_id"] for ln in s_lines}


def test_the_census_gives_every_family_a_terminal_state(runs):
    cov = json.loads((runs / "m9/m9/COVERAGE.json").read_text(encoding="utf-8"))
    rows = cov["families"]
    assert len(rows) == 99 and {r["code"] for r in rows} == {f["code"] for f in RS.family_master()["families"]}
    assert all(r["run_state"] in CS.RUN_STATES and r["reason"] for r in rows)
    st = {r["code"]: r["run_state"] for r in rows}
    assert st["B10-02"] == "QUANTIFIED" and st["B8-05"] == "QUANTIFIED" and st["B11-03"] == "BLOCKED"
    assert st["B1-01"] == "NOT_IMPLEMENTED" and st["B12-02"] == "BLOCKED_BY_SOURCE"
    rr = json.loads((runs / "m9/m9/RUN_RULES.json").read_text(encoding="utf-8"))
    assert rr["rule_set"] == "1.5.0" and rr["store_drift"] == [] and rr["conventions"]["digest"]


def test_census_without_any_run_never_claims_a_quantity():
    rows = CS.census([])
    assert {r["run_state"] for r in rows} <= {"NOT_RUN", "NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE"}


def test_tiles_and_membrane_subcommands(capsys):
    from tools import urban_boq_m9 as M9
    assert M9.main(["tiles", "--length", "3", "--width", "2", "--joint", "0.002", "--min-cut", "0.1",
                    "--min-reusable", "0.1", "--selected", "TILE-120x60"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [c["consumed"] for c in out["candidates"]] == [9, 17, 5]
    assert M9.main(["membrane", "--length", "2.3", "--width", "3.2", "--door", "0.9:0.2", "--direction", "ALONG_Y"]) == 0
    m = json.loads(capsys.readouterr().out)
    assert m["net_installed_m2"] == pytest.approx(9.74) and m["layout"]["floor_strips"] == 3
    assert M9.main(["rules", "--check"]) == 0
