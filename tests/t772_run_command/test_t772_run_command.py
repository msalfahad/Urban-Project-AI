"""T-772: tools/urban_boq_run.py, the one manifest-driven command, on a synthetic (non-Alsenan) villa.

Fixture: tools/synth_villa SV-A (hand truth in tests/synth_villa: GF rooms LIVING 6.0 x 8.0 = 48.0 m2, KITCHEN
2.9 x 4.0 = 11.6, BATH 2.8 x 4.0 = 11.2, BEDROOM 5.8 x 3.8 = 22.04), written as DXF under tmp_path.
Normal: plan only, no inputs sheet -> the command runs end to end, the workbook is the boq_export_v1 workbook of the
geometry run, the exceptions list names the absent inputs sheet and the absent structural drawing, and the run
changes no engine line (the export lines equal the geometry run's lines).
Adverse: missing plan -> FATAL, exit 2, no geometry and no BOQ written (never 0); a present data object without a
reader -> PRESENT_NOT_WIRED, nothing applied; rotated + mirrored + metres drawing -> same room areas as the plain one;
reach against a hand-made candidate index (direct / restated / fill / overlay-only); a refused zero -> HELD export
copy, engine line unchanged. Every test writes only under tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import urban_boq_run as R          # noqa: E402
from tools.synth_villa import build as B       # noqa: E402

PID = "synthetic-villa-t772"


def _manifest(tmp, **kw):
    m = {"schema": R.MANIFEST_SCHEMA, "project_id": PID, "drawings": {}, "rules": {}, "data_objects": {},
         "compare": {}}
    for k, v in kw.items():
        m[k] = v
    p = tmp / "RUN_MANIFEST.json"
    p.write_text(json.dumps(m), encoding="utf-8")
    return p


def _villa(tmp, name="sv_a.dxf", **kw):
    p = tmp / name
    B.write_villa("SV-A", p, **kw)
    return p


@pytest.fixture(scope="module")
def plain_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("t772_plain")
    dxf = _villa(tmp)
    rc = R.run(_manifest(tmp, drawings={"plan": str(dxf)}), tmp / "out")
    return rc, tmp / "out"


def _ex(out):
    return json.loads((out / "EXCEPTIONS.json").read_text(encoding="utf-8"))["exceptions"]


def _room_areas(out):
    lines = json.loads((out / "geometry" / "BOQ_LINES.json").read_text(encoding="utf-8"))
    return lines


def test_normal_runs_end_to_end_with_exceptions_not_defaults(plain_run):
    rc, out = plain_run
    assert rc == 0
    rec = json.loads((out / "RUN_RECORD.json").read_text(encoding="utf-8"))
    assert rec["geometry"]["exit"] == 0 and rec["geometry"]["lines"] > 0
    assert rec["released_default"] is False and rec["changes_engine_lines"] is False
    codes = {e["code"] for e in _ex(out)}
    assert {"INPUTS_SHEET_ABSENT", "STRUCTURAL_DRAWING_NOT_GIVEN", "PROJECT_FACTS_NOT_GIVEN"} <= codes
    assert not any(e["level"] == R.FATAL for e in _ex(out))
    assert len(rec["exports"]) == 1 and rec["exports"][0]["identity"] == "architectural"
    assert (out / rec["exports"][0]["xlsx"]).is_file()


def test_export_rows_are_the_geometry_lines_unchanged(plain_run):
    _rc, out = plain_run
    geo = json.loads((out / "geometry" / "BOQ_LINES.json").read_text(encoding="utf-8"))
    exp = json.loads((out / "export" / "architectural" / "LINES_EXPORTED.json").read_text(encoding="utf-8"))
    assert sorted(json.dumps(x, sort_keys=True) for x in geo) == sorted(json.dumps(x, sort_keys=True) for x in exp)
    man = json.loads((out / "export" / "architectural" / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    assert man["row_counts"]["total"] == len(geo)


def test_hand_truth_room_area_reaches_the_lines(plain_run):
    """SV-A GF LIVING 6.0 x 8.0 = 48.0 m2 (hand): some floor-area line of the run carries exactly 48.0."""
    _rc, out = plain_run
    lines = _room_areas(out)
    nets = [ln["measured_net"] for ln in lines if ln.get("unit") == "m2" and ln.get("measured_net") is not None
            and (ln.get("location") or {}).get("floor") == "GF"]
    assert any(abs(n - 48.0) < 1e-6 for n in nets), sorted(set(round(n, 3) for n in nets))[:20]


def test_missing_plan_is_fatal_and_writes_no_boq(tmp_path):
    rc = R.run(_manifest(tmp_path, drawings={"plan": str(tmp_path / "absent.dxf")}), tmp_path / "out")
    assert rc == 2
    codes = {(e["level"], e["code"]) for e in _ex(tmp_path / "out")}
    assert (R.FATAL, "PLAN_DRAWING_MISSING") in codes
    assert not (tmp_path / "out" / "geometry").exists() and not (tmp_path / "out" / "export").exists()


def test_no_plan_named_is_fatal(tmp_path):
    rc = R.run(_manifest(tmp_path), tmp_path / "out")
    assert rc == 2 and any(e["code"] == "PLAN_DRAWING_NOT_GIVEN" for e in _ex(tmp_path / "out"))


def test_manifest_without_project_or_with_unknown_object_is_refused(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"schema": R.MANIFEST_SCHEMA, "drawings": {}}), encoding="utf-8")
    with pytest.raises(R.ManifestError):
        R.load_manifest(p)
    p.write_text(json.dumps({"schema": R.MANIFEST_SCHEMA, "project_id": PID, "data_objects": {"x": "y"}}),
                 encoding="utf-8")
    with pytest.raises(R.ManifestError):
        R.load_manifest(p)
    assert R.main(["--manifest", str(p), "--out", str(tmp_path / "o")]) == 2


def test_present_data_object_without_reader_is_recorded_not_applied(tmp_path):
    dxf = _villa(tmp_path)
    sheet = tmp_path / "inputs.json"
    sheet.write_text(json.dumps({"storey_height_m": 99.0}), encoding="utf-8")
    m, ex = R.load_manifest(_manifest(tmp_path, drawings={"plan": str(dxf)}, data_objects={"inputs_sheet":
                                                                                            str(sheet)}))
    hit = [e for e in ex if e["code"] == "INPUTS_SHEET_PRESENT_NOT_WIRED"]
    assert len(hit) == 1 and hit[0]["level"] == R.ACTION and len(hit[0]["sha256"]) == 64
    assert not any(e["code"] == "INPUTS_SHEET_ABSENT" for e in ex)


def test_missing_named_structural_or_rule_set_is_fatal(tmp_path):
    dxf = _villa(tmp_path)
    _m, ex = R.load_manifest(_manifest(tmp_path, drawings={"plan": str(dxf), "structural": str(tmp_path / "no.dxf")},
                                       rules={"conventions": str(tmp_path / "no_rules.json")}))
    codes = {e["code"] for e in ex if e["level"] == R.FATAL}
    assert {"STRUCTURAL_DRAWING_MISSING", "RULE_SET_MISSING"} <= codes
    _m, ex = R.load_manifest(_manifest(tmp_path, drawings={"plan": str(dxf), "structural": str(dxf)}))
    assert any(e["code"] == "SAME_DRAWING_TWICE" for e in ex)


def test_rotated_mirrored_metres_drawing_gives_the_same_lines(tmp_path, plain_run):
    _rc, out0 = plain_run
    dxf = _villa(tmp_path, name="sv_a_rot.dxf", rotate_deg=-121.0, mirror=True, units="m")
    assert R.run(_manifest(tmp_path, drawings={"plan": str(dxf)}), tmp_path / "out") == 0

    def key(out):
        lines = json.loads((out / "geometry" / "BOQ_LINES.json").read_text(encoding="utf-8"))
        return sorted((ln["item_code"], (ln.get("location") or {}).get("floor"), ln["evidence_state"],
                       None if ln.get("measured_net") is None else round(ln["measured_net"], 3)) for ln in lines)
    assert key(tmp_path / "out") == key(out0)


def _line(lid, code, state, net, eid="E:1"):
    return {"line_id": lid, "item_code": code, "unit": "m2", "evidence_state": state, "measured_net": net,
            "element_id": eid}


def test_reach_classes_against_a_hand_index():
    geo = [_line("L-a", "X.ONE", "MEASURED", 10.0), _line("L-b", "X.ONE", "MEASURED", 5.0),
           _line("L-c", "X.TWO", "MEASURED", 2.0), _line("L-g", "X.TWO", "MEASURED", 1.0)]
    idx = {"candidate_version": "SYNTH", "lines": [
        {"line_id": "L-a", "item_code": "X.ONE", "unit": "m2", "class": "RELEASED", "measured_net": 10.0,
         "element_id": "E:1"},                                                            # direct
        {"line_id": "L-b", "item_code": "X.ONE", "unit": "m2", "class": "RELEASED", "measured_net": 6.0,
         "element_id": "E:1"},                                                            # restated by an overlay
        {"line_id": "L-c", "item_code": "X.TWO", "unit": "m2", "class": "RELEASED", "measured_net": 3.0,
         "element_id": "GF-W:L-0123456789abcdef", "method_label": "DEFAULT"},              # restated by a fix row
        {"line_id": "L-d", "item_code": "X.TWO", "unit": "m2", "class": "RELEASED", "measured_net": 4.0,
         "element_id": "1F-W:L-fedcba9876543210"},                                        # overlay only
        {"line_id": "L-e", "item_code": "X.THREE", "unit": "m2", "class": "HELD", "measured_net": None,
         "element_id": "E:2", "method_label": "ESTIMATE"},                                # fill only
        {"line_id": "L-f", "item_code": "X.THREE", "unit": "m2", "class": "EXCLUDED", "measured_net": None,
         "element_id": "E:3"}]}
    master = {"families": [{"code": "F1", "item_en": "one", "item_codes": ["X.ONE"]},
                           {"code": "F2", "item_en": "two", "item_codes": ["X.TWO"]}]}
    rows, fams, back, not_in = R.reach(geo, idx, master)
    by = {r["line_id"]: r["reach"] for r in rows}
    assert by == {"L-a": "GEOMETRY_DIRECT", "L-b": "GEOMETRY_RESTATED", "L-c": "FILL_RESTATED",
                  "L-d": "OVERLAY_ONLY", "L-e": "FILL_ONLY", "L-f": "OVERLAY_ONLY"}
    f = {x["family"]: x for x in fams}
    assert f["F1"]["lines"] == 2 and f["F1"]["GEOMETRY_DIRECT"] == 1 and f["F1"]["reached_share"] == 0.5
    assert f["NO_FAMILY"]["lines"] == 1 and f["NO_FAMILY"]["excluded"] == 1       # X.THREE has no family
    assert not_in == ["L-g"]
    groups = {(b["item_code"], b["element_group"], b["reach"]) for b in back}
    assert ("X.TWO", "<FLOOR>-W:L-*", "FILL_RESTATED") in groups and ("X.TWO", "<FLOOR>-W:L-*", "OVERLAY_ONLY") in groups
    items = {(a["family"], a["item_code"]): a for a in R.backlog_by_item(back)}
    assert items[("F2", "X.TWO")]["lines"] == 2 and items[("F2", "X.TWO")]["candidate_released_qty"] == 7.0
    assert items[("F2", "X.TWO")]["geometry_released_qty"] == 2.0                  # L-c read 2.0, restated 3.0
    assert items[("F1", "X.ONE")]["geometry_released_qty"] == 5.0                  # L-b read 5.0, restated 6.0


def test_refused_zero_is_exported_held_and_engine_line_unchanged():
    ln = {"line_id": "L-z", "evidence_state": "PROVISIONAL", "measured_net": 0.0, "bounded_range": None,
          "rfi": None, "notes": ""}
    c = R.held_copy(ln, "why")
    assert c["evidence_state"] == "BLOCKED_RFI" and c["measured_net"] is None and c["rfi"]["question"] == "why"
    assert ln["evidence_state"] == "PROVISIONAL" and ln["measured_net"] == 0.0
