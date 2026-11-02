"""T-450 part 1: per-project config schema for declared project facts (A1 class B) + loader.

The fixture is a SYNTHETIC villa (VILLA-SYNTH-01); every expected value below is a hand calculation from the
fixture text, never an engine or freelancer result. Normal cases, then adverse cases (units, missing data,
refused sources, version conflicts, malformed files).
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from engine import project_config as pc

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "villa_synth_01.json"
ROOT = HERE.parents[1]
MODULE = ROOT / "engine" / "project_config.py"


def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def fact(**over):
    base = {
        "fact_id": "STR.FOOTING.DEPTH",
        "version": 1,
        "quantity_kind": "LENGTH",
        "value": 0.6,
        "unit": "m",
        "source": {"kind": "DRAWING", "reference": "synthetic sheet S-01"},
        "approval": {"status": "APPROVED", "by": "CONSULTANT", "date": "2026-10-01"},
        "affected_lines": ["CONC.FOOTING"],
        "confidence": "CONFIRMED",
    }
    base.update(over)
    return base


def cfg_with(*facts):
    return {"schema": pc.SCHEMA, "project_id": "VILLA-SYNTH-02", "config_version": "0.1.0", "facts": list(facts)}


def codes_of(data, **kw):
    with pytest.raises(pc.ProjectConfigError) as ei:
        pc.parse_project_config(data, **kw)
    return ei.value.codes


# ---------------------------------------------------------------- normal cases

def test_synthetic_project_loads_with_every_fact():
    cfg = pc.load_project_config(FIXTURE)
    assert cfg.project_id == "VILLA-SYNTH-01" and cfg.config_version == "1.2.0"
    assert len(cfg.facts) == 7 and len(cfg.active_facts()) == 6  # ceiling v1 is SUPERSEDED
    assert re.fullmatch(r"[0-9a-f]{64}", cfg.content_sha256)


def test_lengths_convert_to_metres_by_hand():
    cfg = pc.load_project_config(FIXTURE)
    assert cfg.lookup("STR.SLAB.ROOF.THICKNESS").base_value() == pytest.approx(0.200, abs=1e-12)  # 200 mm
    assert cfg.lookup("ARC.WALL.TILE.HEIGHT.WET").base_value() == pytest.approx(2.400, abs=1e-12)  # 2400 mm
    assert cfg.lookup("ARC.CEILING.HEIGHT.GF").base_value() == pytest.approx(3.20, abs=1e-12)      # m stays m


def test_same_fact_in_mm_and_m_gives_the_same_metres():
    a = pc.parse_project_config(cfg_with(fact(value=150, unit="mm")))
    b = pc.parse_project_config(cfg_with(fact(value=0.15, unit="m")))
    assert a.lookup("STR.FOOTING.DEPTH").base_value() == pytest.approx(b.lookup("STR.FOOTING.DEPTH").base_value())
    assert a.lookup("STR.FOOTING.DEPTH").value() == 150  # the declared value is kept as declared


def test_superseded_version_is_history_and_the_new_one_is_used():
    cfg = pc.load_project_config(FIXTURE)
    hist = cfg.history("ARC.CEILING.HEIGHT.GF")
    assert [f.version for f in hist] == [1, 2] and hist[0].approval_status == "SUPERSEDED"
    look = cfg.lookup("ARC.CEILING.HEIGHT.GF")
    assert look.fact.version == 2 and look.value() == 3.20


def test_evidence_status_follows_workflow_controls_section_5():
    cfg = pc.load_project_config(FIXTURE)
    assert cfg.lookup("STR.SLAB.ROOF.THICKNESS").status == pc.DRAWING_CONFIRMED      # drawing, confirmed
    assert cfg.lookup("ARC.WALL.TILE.HEIGHT.WET").status == pc.DRAWING_CONFIRMED     # specification, confirmed
    assert cfg.lookup("ARC.CEILING.HEIGHT.GF").status == pc.ASSUMED_OWNER_APPROVED   # owner, provisional
    assert "Q-S4" in cfg.lookup("ARC.CEILING.HEIGHT.GF").reason                       # source stays attached
    statuses = {f.evidence_status() for f in cfg.active_facts()}
    assert "VERIFIED" not in statuses  # only the Checker verifies


def test_category_and_boolean_facts():
    cfg = pc.load_project_config(FIXTURE)
    assert cfg.lookup("ARC.BLOCK.TYPE.EXTERNAL").value() == "AAC_200"
    assert cfg.lookup("SITE.POOL.PRESENT").value() is True
    with pytest.raises(TypeError):
        cfg.lookup("SITE.POOL.PRESENT").base_value()


def test_facts_affecting_a_line():
    cfg = pc.load_project_config(FIXTURE)
    assert [f.fact_id for f in cfg.facts_affecting("FIN.PLASTER.INT")] == ["ARC.CEILING.HEIGHT.GF"]
    assert [f.version for f in cfg.facts_affecting("FIN.PLASTER.INT")] == [2]  # superseded v1 not returned
    assert cfg.facts_affecting("CONC.COLUMN") == ()


def test_hash_ignores_key_order_and_layout_but_not_values(tmp_path):
    data = raw()
    shuffled = {k: data[k] for k in reversed(list(data))}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(shuffled, indent=7), encoding="utf-8")
    assert pc.load_project_config(p).content_sha256 == pc.load_project_config(FIXTURE).content_sha256
    data["facts"][0]["value"] = 201
    assert pc.parse_project_config(data).content_sha256 != pc.load_project_config(FIXTURE).content_sha256


def test_known_line_ids_accept_the_fixture_lines():
    lines = {ln for f in raw()["facts"] for ln in f["affected_lines"]}
    assert pc.parse_project_config(raw(), known_line_ids=lines).project_id == "VILLA-SYNTH-01"


# ---------------------------------------------------------------- missing data never becomes 0

def test_absent_fact_is_held_never_zero():
    cfg = pc.load_project_config(FIXTURE)
    look = cfg.lookup("STR.COLUMN.HEIGHT.GF")
    assert look.status == pc.HELD and not look.usable and look.fact is None
    with pytest.raises(LookupError):
        look.value()
    with pytest.raises(LookupError):
        look.base_value()


def test_pending_fact_is_held():
    look = pc.load_project_config(FIXTURE).lookup("MAT.BLOCK.WASTE")
    assert look.status == pc.HELD and "PENDING" in look.reason
    with pytest.raises(LookupError):
        look.value()


def test_every_version_superseded_is_held():
    data = cfg_with(fact(approval={"status": "SUPERSEDED", "by": "CONSULTANT", "date": "2026-10-01"}))
    look = pc.parse_project_config(data).lookup("STR.FOOTING.DEPTH")
    assert look.status == pc.HELD and "SUPERSEDED" in look.reason


def test_null_or_missing_value_is_refused():
    assert codes_of(cfg_with(fact(value=None))) == ["MISSING_VALUE"]
    f = fact()
    del f["value"]
    assert codes_of(cfg_with(f)) == ["MISSING_VALUE"]


def test_missing_file_is_a_clear_error(tmp_path):
    with pytest.raises(pc.ProjectConfigError) as ei:
        pc.load_project_config(tmp_path / "nope.json")
    assert ei.value.codes == ["NO_FILE"]


# ---------------------------------------------------------------- adverse: units and values

@pytest.mark.parametrize("kind,unit", [("LENGTH", "m2"), ("AREA", "m"), ("VOLUME", "m2"), ("RATIO", "mm"),
                                       ("CATEGORY", "m"), ("LENGTH", "M"), ("LENGTH", "none")])
def test_unit_not_legal_for_its_kind(kind, unit):
    value = "X" if kind == "CATEGORY" else 1.0
    assert "UNIT_KIND_MISMATCH" in codes_of(cfg_with(fact(quantity_kind=kind, unit=unit, value=value)))


@pytest.mark.parametrize("value,code", [("0.6", "BAD_VALUE"), (True, "BAD_VALUE"), (-0.1, "NEGATIVE_VALUE"),
                                        ([0.6], "BAD_VALUE")])
def test_bad_numeric_values(value, code):
    assert codes_of(cfg_with(fact(value=value))) == [code]


def test_count_is_whole_and_category_not_empty():
    assert codes_of(cfg_with(fact(quantity_kind="COUNT", unit="nr", value=2.5))) == ["BAD_VALUE"]
    assert pc.parse_project_config(cfg_with(fact(quantity_kind="COUNT", unit="nr", value=3)))
    assert codes_of(cfg_with(fact(quantity_kind="CATEGORY", unit="none", value="  "))) == ["BAD_VALUE"]
    assert codes_of(cfg_with(fact(quantity_kind="BOOLEAN", unit="none", value=1))) == ["BAD_VALUE"]


def test_percent_converts_to_ratio():
    cfg = pc.parse_project_config(cfg_with(fact(quantity_kind="RATIO", unit="%", value=5)))
    assert cfg.lookup("STR.FOOTING.DEPTH").base_value() == pytest.approx(0.05)


def test_nan_and_infinity_are_refused_in_files(tmp_path):
    for token in ("NaN", "Infinity", "-Infinity"):
        p = tmp_path / f"{token}.json"
        p.write_text(json.dumps(raw()).replace('"value": 200', f'"value": {token}', 1), encoding="utf-8")
        with pytest.raises(pc.ProjectConfigError) as ei:
            pc.load_project_config(p)
        assert ei.value.codes == ["BAD_VALUE"]
    assert codes_of(cfg_with(fact(value=float("inf")))) == ["BAD_VALUE"]


# ---------------------------------------------------------------- adverse: sources and approval

@pytest.mark.parametrize("kind", ["FREELANCER", "FREELANCER_WORKBOOK", "BENCHMARK", "REFERENCE_BOQ", "ENGINE_RESULT"])
def test_comparison_references_are_refused_as_sources(kind):
    assert codes_of(cfg_with(fact(source={"kind": kind, "reference": "workbook row 12"}))) == ["REFUSED_SOURCE"]


def test_source_needs_a_reference_and_a_known_kind():
    assert codes_of(cfg_with(fact(source={"kind": "DRAWING", "reference": " "}))) == ["MISSING_REFERENCE"]
    assert codes_of(cfg_with(fact(source={"kind": "GUESS", "reference": "x"}))) == ["BAD_SOURCE"]
    assert codes_of(cfg_with(fact(source="sheet S-01"))) == ["BAD_SOURCE"]


def test_confirmed_needs_approval_and_approved_needs_an_approver():
    pending = {"status": "PENDING", "date": "2026-10-01"}
    assert codes_of(cfg_with(fact(approval=pending))) == ["CONFIRMED_NOT_APPROVED"]
    assert pc.parse_project_config(cfg_with(fact(approval=pending, confidence="PROVISIONAL")))
    assert codes_of(cfg_with(fact(approval={"status": "APPROVED", "date": "2026-10-01"}))) == ["APPROVER_REQUIRED"]
    assert codes_of(cfg_with(fact(approval={"status": "APPROVED", "by": "WORKER", "date": "2026-10-01"}))) == \
        ["APPROVER_REQUIRED", "BAD_APPROVAL"]


@pytest.mark.parametrize("date", ["2026-13-01", "01-10-2026", "2026-10-1", "", None])
def test_bad_dates(date):
    assert codes_of(cfg_with(fact(approval={"status": "APPROVED", "by": "CONSULTANT", "date": date}))) == ["BAD_DATE"]


# ---------------------------------------------------------------- adverse: lines, ids, versions

def test_affected_lines_rules():
    assert codes_of(cfg_with(fact(affected_lines=[]))) == ["NO_AFFECTED_LINES"]
    assert codes_of(cfg_with(fact(affected_lines=["CONC FOOTING"]))) == ["BAD_LINE_ID"]
    assert codes_of(cfg_with(fact(affected_lines=["CONC.FOOTING", "CONC.FOOTING"]))) == ["DUPLICATE_LINE"]
    assert codes_of(cfg_with(fact()), known_line_ids={"CONC.SLAB"}) == ["UNKNOWN_LINE"]


def test_two_active_versions_are_refused():
    v2 = fact(version=2, value=0.7)
    assert codes_of(cfg_with(fact(), v2)) == ["TWO_ACTIVE_VERSIONS", "STALE_ACTIVE_VERSION"]


def test_supersedes_must_point_at_an_earlier_superseded_version():
    old = fact(approval={"status": "SUPERSEDED", "by": "CONSULTANT", "date": "2026-10-01"})
    assert pc.parse_project_config(cfg_with(old, fact(version=2, value=0.7, supersedes=1)))
    assert codes_of(cfg_with(old, fact(version=2, supersedes=3))) == ["BAD_SUPERSEDES"]
    assert codes_of(cfg_with(fact(version=2, supersedes=1))) == ["BAD_SUPERSEDES"]          # v1 not declared
    assert "BAD_SUPERSEDES" in codes_of(cfg_with(fact(), fact(version=2, supersedes=1)))     # v1 still active


def test_newest_version_cannot_be_the_superseded_one():
    newer_dead = fact(version=2, approval={"status": "SUPERSEDED", "by": "CONSULTANT", "date": "2026-10-02"})
    assert codes_of(cfg_with(fact(), newer_dead)) == ["STALE_ACTIVE_VERSION"]


def test_duplicate_fact_version_and_kind_change():
    assert "DUPLICATE_FACT" in codes_of(cfg_with(fact(), fact()))
    old = fact(approval={"status": "SUPERSEDED", "by": "CONSULTANT", "date": "2026-10-01"})
    assert codes_of(cfg_with(old, fact(version=2, quantity_kind="AREA", unit="m2", supersedes=1))) == ["KIND_CHANGED"]


@pytest.mark.parametrize("fid", ["str.footing", "1STR", "STR..X", "", 7])
def test_bad_fact_ids(fid):
    assert codes_of(cfg_with(fact(fact_id=fid))) == ["BAD_FACT_ID"]


def test_unknown_and_missing_fields():
    assert codes_of(cfg_with(fact(rate=12.5))) == ["UNKNOWN_FIELD"]
    f = fact()
    del f["confidence"]
    assert codes_of(cfg_with(f)) == ["MISSING_FIELD"]


def test_top_level_errors_are_all_reported_together():
    data = raw()
    data["schema"] = "URBAN_PROJECT_CONFIG_V0"
    data["project_id"] = "villa synth"
    data["config_version"] = "1.2"
    data["extra"] = 1
    data["facts"][0]["unit"] = "m2"
    assert sorted(codes_of(data)) == sorted(["UNKNOWN_FIELD", "WRONG_SCHEMA", "BAD_PROJECT_ID",
                                             "BAD_CONFIG_VERSION", "UNIT_KIND_MISMATCH"])


def test_malformed_files(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(pc.ProjectConfigError) as ei:
        pc.load_project_config(p)
    assert ei.value.codes == ["NOT_JSON"]
    p.write_text('{"schema": "URBAN_PROJECT_CONFIG_V1", "schema": "X", "project_id": "A1", '
                 '"config_version": "1.0.0", "facts": []}', encoding="utf-8")
    with pytest.raises(pc.ProjectConfigError) as ei:
        pc.load_project_config(p)
    assert ei.value.codes == ["DUPLICATE_KEY"]
    assert codes_of([1, 2]) == ["NOT_OBJECT"]


def test_an_empty_project_is_valid_and_holds_everything():
    cfg = pc.parse_project_config(cfg_with())
    assert cfg.facts == () and cfg.lookup("ANY.FACT").status == pc.HELD


def test_parse_does_not_mutate_its_input():
    data = raw()
    before = copy.deepcopy(data)
    pc.parse_project_config(data)
    assert data == before


# ---------------------------------------------------------------- generality guards (A2 acceptance, part 1)

def test_module_is_project_independent_and_stdlib_only():
    text = MODULE.read_text(encoding="utf-8")
    assert not re.search(r"7757|alsenan|senan|qortuba", text, re.IGNORECASE)
    imports = re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", text, re.MULTILINE)
    assert all(m.split(".")[0] in {"__future__", "hashlib", "json", "math", "re", "dataclasses", "pathlib", "typing"}
               for m in imports), imports


def test_fixture_is_synthetic():
    assert not re.search(r"7757|alsenan|senan|qortuba", FIXTURE.read_text(encoding="utf-8"), re.IGNORECASE)


def test_part_1_wires_nothing_into_the_engine():
    users = [p for p in (ROOT / "engine").rglob("*.py")
             if p != MODULE and re.search(r"\bproject_config\b", p.read_text(encoding="utf-8", errors="ignore"))]
    assert users == []
