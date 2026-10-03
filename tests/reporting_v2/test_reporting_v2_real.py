"""Reporting V2 on the frozen registers: Alsenan (A3 + B2A.1) is the first fixture, Qortuba (RC1) must render too.
Zero quantity / status change; the frozen report records are reproduced by the committed code."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/external_engine_lab"))

import reporting_v2_alsenan as AL                                                                   # noqa: E402
import reporting_v2_qortuba as QO                                                                   # noqa: E402
from engine.reporting_v2 import model as M                                                          # noqa: E402
from engine.reporting_v2 import readback as RB                                                      # noqa: E402
from engine.reporting_v2 import xlsx as X                                                           # noqa: E402

FROZEN = ROOT / "tests/reporting_v2/frozen"
ORDER = ["00_TOTAL_SUMMARY", "01_GROUND_FLOOR", "02_FIRST_FLOOR", "03_ROOF_SECOND_FLOOR", "04_FOUNDATION_SUBSTRUCTURE",
         "05_OPENINGS_ALUMINIUM", "06_BLOCKERS_OWNER_QUESTIONS", "07_METHODS_TRACEABILITY"]


@pytest.fixture(scope="module")
def alsenan():
    return AL.build("2026-10-03", "02feef8")


@pytest.fixture(scope="module")
def qortuba():
    return QO.build("2026-10-03", "02feef8")


def test_alsenan_model_valid_and_every_value_from_a_register(alsenan):
    m, R = alsenan
    v = M.validate(m, R)
    assert v["state"] == "PASS", v["problems"]
    assert v["quantity_cells"] > 700 and v["lines"] == len(m["lines"])
    assert set(m["inputs"]) == set(R.files) and all(n.startswith(("A3.", "B2A1.")) for n in m["inputs"])


def test_sheet_order_and_one_sheet_per_floor(alsenan):
    m, _ = alsenan
    names = [s["name"] for s in m["sheets"]]
    assert names[:8] == ORDER and all(n.startswith("TECH_") for n in names[8:])
    roles = {s["name"]: s["role"] for s in m["sheets"]}
    assert roles["00_TOTAL_SUMMARY"] == "SUMMARY" and sum(r == "SUMMARY" for r in roles.values()) == 1
    floors = [s for s in m["sheets"] if s["name"] in ORDER[1:4]]
    assert [s["level"] for s in floors] == ["GF", "1F", "2F"]
    seq = lambda s: [x["id"] for x in s["sections"] if x["id"] != "ROOF_WP"]
    assert seq(floors[0]) == seq(floors[1]) == seq(floors[2]) == ["KPI", "ROOMS", "STRUCTURE", "BEAMS", "COLUMNS", "OPENINGS",
                                                                   "FINISHES", "NOTES"]
    assert "ROOF_WP" in [x["id"] for x in floors[2]["sections"]]
    for s in m["sheets"][1:6]:
        assert s["note"] in (None, "Project totals: use 00_TOTAL_SUMMARY only.") and (s["role"] not in ("BREAKDOWN", "SCHEDULE") or s["note"])


def test_only_the_summary_holds_additive_rows(alsenan):
    m, _ = alsenan
    for s, sec, i, r, j, c in M.iter_cells(m):
        if r["cls"] == "ADDITIVE":
            assert s["name"] == "00_TOTAL_SUMMARY"


def test_no_raw_json_in_main_sheets(alsenan):
    m, _ = alsenan
    for s, sec, i, r, j, c in M.iter_cells(m):
        if s["role"] != "TECH" and isinstance(c, str):
            assert not c.strip().startswith(("{", "[")), (s["name"], c[:40])


def test_quantities_equal_the_b2a1_freeze(alsenan):
    m, R = alsenan
    fz = R.data["B2A1.ALSENAN_PHASE_B2A1_REGISTER_FREEZE"]["summary"]
    con = {p["level"]: p["cell"]["q"] for ln in m["lines"] if ln["id"] == "CON-SUPER" for p in ln["parts"]}
    assert con == fz["physical_concrete_m3"]
    blk = {ln["id"]: ln for ln in m["lines"]}
    assert blk["CON-STAIR"]["status"] == "BLOCKED" and blk["CON-STAIR"]["qty"]["q"] is None
    assert blk["ALU-CURVED"]["basis"] == "MIN_RADIUS_ARC" and blk["ALU-CURVED"]["qty"]["q"] == pytest.approx(6.657684 + 3.101796)
    assert blk["WP-ROOF"]["qty"]["q"] == pytest.approx(61.612601 + 176.209166 + 126.209175)


def test_openings_never_published_as_window(alsenan):
    m, _ = alsenan
    sched = [s for s in m["sheets"] if s["name"] == "05_OPENINGS_ALUMINIUM"][0]["sections"][0]
    functions = {r["cells"][3] for r in sched["rows"] if r["role"] == "ITEM"}
    assert "WINDOW" not in functions and "WINDOW CANDIDATE" in functions and "GLAZED OPENING FUNCTION UNKNOWN" in functions


def test_foundation_is_separate_and_subtotals_match_registers(alsenan):
    m, R = alsenan
    f = [s for s in m["sheets"] if s["name"] == "04_FOUNDATION_SUBSTRUCTURE"][0]
    assert [x["id"] for x in f["sections"]] == ["FOOTINGS", "STRAPS", "SUBSTRUCTURE_OTHER"]
    pc = {r["item"]: r for r in R.data["B2A1.PHYSICAL_CONCRETE_REGISTER"]["explicit_items"]}
    sub = lambda sid: [c for r in [x for x in f["sections"] if x["id"] == sid][0]["rows"] if r["role"] == "SUBTOTAL"
                       for c in r["cells"] if M.is_q(c)][0]["q"]
    assert sub("FOOTINGS") == pc["FOOTINGS"]["volume_m3"] and sub("STRAPS") == pc["STRAPS"]["volume_m3"]
    other = [x for x in f["sections"] if x["id"] == "SUBSTRUCTURE_OTHER"][0]["rows"]
    assert len(other) == 6 and all(r["status"] in ("PARTIAL", "BLOCKED", "COMPUTED") for r in other)


def test_alsenan_xlsx_readback(alsenan, tmp_path):
    m, _ = alsenan
    x = X.render(m, tmp_path / "a.xlsx", logo=ROOT / "assets/logo.png")
    rb = RB.validate(tmp_path / "a.xlsx", m, x["cell_map"])
    assert rb["state"] == "PASS" and rb["formula_cells"] == 0 and rb["validated_quantity_cells"] > 700


def test_qortuba_renders_without_quantity_change(qortuba, tmp_path):
    m, R = qortuba
    assert M.validate(m, R)["state"] == "PASS"
    items = R.data["RC1.CANONICAL_BOQ"]["items"]
    shown = {ln["id"]: (ln["qty"]["q"], ln["parts"][0]["tech"]) for ln in m["lines"]}
    assert shown == {it["canonical_item_id"]: (it["qty"], it["status"]) for it in items}
    cls = {ln["id"]: ln["cls"] for ln in m["lines"]}
    assert cls["MRB-01"] == "ADDITIVE" and cls["MRB-02"] == "ALTERNATIVE_MEASURE" and cls["WIN-02"] == "ALTERNATIVE_MEASURE"
    x = X.render(m, tmp_path / "q.xlsx")
    assert RB.validate(tmp_path / "q.xlsx", m, x["cell_map"])["state"] == "PASS"


@pytest.mark.skipif(not (FROZEN / "REPORTING_MODEL_V2.json").exists(), reason="report records not frozen yet")
def test_frozen_report_records_are_reproduced(alsenan, qortuba):
    fm = json.loads((FROZEN / "REPORTING_MODEL_V2.json").read_text())
    assert fm["content_digest"] == alsenan[0]["content_digest"]
    fz = json.loads((FROZEN / "REPORTING_V2_FREEZE.json").read_text())
    assert fz["model_content_digest"] == {"alsenan": alsenan[0]["content_digest"], "qortuba": qortuba[0]["content_digest"]}
    assert fz["model_input_digests_equal_registers"] is True
    assert fz["input_register_digests"]["alsenan"] == alsenan[1].inputs()
    reg = json.loads((FROZEN / "REPORTING_V2_REGRESSION.json").read_text())
    assert reg["state"] == "PASS" and reg["engine_changed"] is False
    assert reg["alsenan"]["quantity_changes"] == [] and reg["qortuba"]["canonical_items_unchanged"] is True
    qa = json.loads((FROZEN / "REPORTING_READBACK_QA.json").read_text())
    assert qa["state"] == "PASS" and qa["alsenan"]["xlsx"]["formula_cells"] == 0 and qa["alsenan"]["pdf"]["sections_in_order"]


def test_engine_and_frozen_registers_untouched_since_b2a1():
    for d in ("engine/source", "tests/alsenan/registers_b2a1", "tests/alsenan/registers_a3", "tests/rc1/registers"):
        out = subprocess.run(["git", "-C", str(ROOT), "diff", "--stat", "02feef8", "--", d], capture_output=True, text=True)
        assert out.returncode == 0 and out.stdout.strip() == "", (d, out.stdout)
