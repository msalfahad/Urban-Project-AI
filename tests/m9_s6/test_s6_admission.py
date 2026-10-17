"""M9 S6 Phase 1 - drawing admission (ARCH_TAKEOFF_V2): a drawing that cannot be measured safely stops with exit 2,
no BOQ is published, the discovery report and the stopping finding are; a reviewer input (units, plan regions, an
accepted missing XREF) is recorded, never defaulted; an earlier run's BOQ in the same folder is moved aside."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_plan as AP              # noqa: E402
from engine.source import discovery as DS              # noqa: E402

V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"


def _blocked(h, out):
    assert not (out / "BOQ_LINES.json").exists() and not (out / "URBAN_ROOM_BOQ.xlsx").exists()
    B = h.read(out, "ADMISSION_BLOCKED.json")
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert B["boq_published"] is False and B["exit_code"] == 2
    assert D["gates"]["architectural_boq_may_run"] is False and D["gates"]["exit_code"] == 2
    return {f["code"] for f in B["stopping_findings"]}, D


@pytest.mark.parametrize("variant,code", [
    ("empty", "EMPTY_MODEL_SPACE"),
    ("insunits_0", "UNITS_NOT_DECLARED"),
    ("insunits_absent", "UNITS_NOT_DECLARED"),
    ("insunits_contradicted", "UNITS_CONTRADICTED"),
    ("paper_space_frames", "PAPER_SPACE_SHEETS"),
    ("no_frame", "PLAN_TITLES_OUTSIDE_ANY_FRAME"),
    ("title_wording", "NO_FLOOR_PLAN_TITLE"),
    ("rotate_all_30", "NO_PLAN_REGION"),
    ("xref_missing", "XREF_NOT_SUPPLIED"),
])
def test_unmeasurable_drawing_stops_with_exit_2_and_no_boq(build, cli, tmp_path, h, variant, code):
    out = tmp_path / "out"
    rc, stdout, _ = cli("--drawings", build(variant), "--out", out, "--method", V2, "--no-svg")
    assert rc == DS.EXIT_ADMISSION_BLOCKED == 2
    codes, D = _blocked(h, out)
    assert code in codes, codes
    assert '"ADMISSION_BLOCKED"' in stdout
    assert D["documents"] and D["documents"][0].get("sha256")             # the evidence names the drawing


def test_baseline_is_admitted(build, cli, tmp_path, h):
    out = tmp_path / "out"
    rc, _, _ = cli("--drawings", build("base"), "--out", out, "--method", V2, "--no-svg")
    assert rc == 0
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert D["gates"]["architectural_boq_may_run"] and not D["gates"]["stopping"]
    assert D["stages"]["4_units"]["unit_m_used"] == 0.001
    assert (out / "BOQ_LINES.json").exists() and (out / "FINISH_COVERAGE.json").exists()


def test_units_given_by_a_reviewer_are_recorded_and_measure_like_the_declared_drawing(build, cli, tmp_path, h):
    a, b = tmp_path / "a", tmp_path / "b"
    assert cli("--drawings", build("base"), "--out", a, "--method", V2, "--no-svg", "--no-m9-xlsx")[0] == 0
    assert cli("--drawings", build("insunits_0"), "--out", b, "--method", V2, "--no-svg", "--no-m9-xlsx",
               "--units", "mm")[0] == 0
    D = h.read(b, "DRAWING_DISCOVERY.json")
    assert D["reviewer_inputs"]["units"] == "mm"
    assert "UNITS_DECLARED_BY_REVIEWER" in {f["code"] for f in D["stages"]["4_units"]["findings"]}
    q = lambda o: sorted((ln["item_code"], ln["location"]["floor"], str(ln.get("measured_net")))  # noqa: E731
                         for ln in h.lines_of(o))
    assert q(a) == q(b)


def _frames(path):
    """{floor: frame box} of the villa as drawn (to give the paper-space variant its regions)."""
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    boxes = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "A-FRAME":
            pts = [tuple(p[:2]) for p in e.get_points()]
            boxes.append((min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)))
    out = {}
    for t in msp.query("TEXT"):
        fl = AP.floor_of_title(t.dxf.text)[0]
        if fl:
            p = t.dxf.insert
            out[fl] = next(b for b in boxes if b[0] <= p.x <= b[2] and b[1] <= p.y <= b[3])
    return out


def test_paper_space_sheets_measured_only_with_reviewer_regions(build, cli, tmp_path, h):
    ref = tmp_path / "ref"
    assert cli("--drawings", build("base"), "--out", ref, "--method", V2, "--no-svg", "--no-m9-xlsx")[0] == 0
    boxes = _frames(tmp_path / "base.dxf")
    out = tmp_path / "out"
    specs = [f"{fl}=" + ",".join(str(v) for v in b) for fl, b in sorted(boxes.items())]
    rc, _, _ = cli("--drawings", build("paper_space_frames"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx",
                   "--region", *specs)
    assert rc == 0
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert D["reviewer_inputs"]["regions"] == specs
    codes = {f["code"] for f in h.findings(D)}
    assert {"PLAN_REGIONS_FROM_REVIEWER", "PAPER_SPACE_CONTENT"} <= codes
    q = lambda o: sorted((r["floor"], r["class"], round(r["area_m2"], 6)) for r in h.read(o, "ARCH_ROOMS.json")["rooms"])  # noqa: E731
    assert q(out) == q(ref)


def test_missing_xref_can_be_accepted_explicitly(build, cli, tmp_path, h):
    out = tmp_path / "out"
    rc, _, _ = cli("--drawings", build("xref_missing"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx",
                   "--accept-missing-xref", "GF_PARTITIONS")
    assert rc == 0
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert D["reviewer_inputs"]["accepted_missing_xrefs"] == ["GF_PARTITIONS"]
    assert "XREF_ACCEPTED_MISSING" in {f["code"] for f in h.findings(D, DS.REVIEW)}
    U = h.read(out, "UNRESOLVED.json")["unresolved"]
    assert any(u["item"] == "ADMISSION:XREF_ACCEPTED_MISSING" for u in U)          # the flag travels with the BOQ


def test_reviewer_inputs_need_the_admission(build, cli, tmp_path):
    with pytest.raises(SystemExit, match="reviewer inputs"):
        cli("--drawings", build("insunits_0"), "--out", tmp_path / "o", "--method", V1, "--units", "mm")


def test_blocked_run_moves_an_earlier_boq_aside(build, cli, tmp_path, h):
    out = tmp_path / "out"
    assert cli("--drawings", build("base"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx")[0] == 0
    assert (out / "BOQ_LINES.json").exists()
    assert cli("--drawings", build("empty"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx")[0] == 2
    assert not (out / "BOQ_LINES.json").exists() and not (out / "FINISH_COVERAGE.json").exists()
    assert (out / "SUPERSEDED_1" / "BOQ_LINES.json").exists()
    assert h.read(out, "ADMISSION_BLOCKED.json")["superseded_earlier_outputs"]["moved_to"] == "SUPERSEDED_1"


def test_hidden_layer_content_is_a_review_flag_on_the_boq(build, cli, tmp_path, h):
    out = tmp_path / "out"
    assert cli("--drawings", build("layer_off_partition"), "--out", out, "--method", V2, "--no-svg",
               "--no-m9-xlsx")[0] == 0
    D = h.read(out, "DRAWING_DISCOVERY.json")
    hid = [f for f in h.findings(D, DS.REVIEW) if f["code"] == "HIDDEN_LAYER_CONTENT"]
    assert hid and hid[0]["evidence"]["layer"] == "A-WALL-DEMO"
    assert any(u["item"] == "ADMISSION:HIDDEN_LAYER_CONTENT" for u in h.read(out, "UNRESOLVED.json")["unresolved"])


def test_every_top_level_entity_has_a_reader_disposition(build):
    from tools import arch_discovery as AD
    doc = ezdxf.readfile(str(build("base")))
    k2 = AD.k2_census(doc)
    assert k2["missing_top_level"] == []
    assert k2["top_level"] == len(list(doc.modelspace()))


def test_a_missing_disposition_is_fatal():
    census = {"layouts": [{"name": "Model", "kind": "MODEL", "entities_by_type": {"LINE": 4}, "viewports": 0}],
              "xrefs": [], "minserts": 0, "hidden_layers": [], "kinds": {"LINE": 4}}
    fs = DS.inventory_findings(census, {"missing_top_level": ["D2:7"]})
    assert [f["code"] for f in fs if f["level"] == DS.FATAL] == ["ENTITY_DISPOSITION_MISSING"]


def test_gate_rule():
    r = DS.new_report([])
    DS.set_stage(r, "7_vertical_model", [DS.finding(DS.BLOCKED_ITEM, "NO_SECTION_SOURCE", "x")])
    assert DS.gate(r)["architectural_boq_may_run"] is True                     # later stage: blocks its items only
    DS.set_stage(r, "4_units", [DS.finding(DS.BLOCKED_ITEM, "UNITS_NOT_DECLARED", "x")])
    g = DS.gate(r)
    assert g["architectural_boq_may_run"] is False and g["stopping"] == ["4_units:UNITS_NOT_DECLARED"]
    r2 = DS.new_report([])
    DS.set_stage(r2, "9_finish_zones", [DS.finding(DS.FATAL, "SURFACE_UNACCOUNTED", "x")])
    assert DS.gate(r2)["exit_code"] == 2
    with pytest.raises(ValueError):
        DS.finding("INFO", "X", "x")
