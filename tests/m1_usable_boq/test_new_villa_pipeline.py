"""M1 new-villa route on a SYNTHETIC drawing (no project data): inventory -> profile takeoff -> BOQ -> Excel / PDF.

The drawing is written here with ezdxf: a foundation sheet (footings, one drawn at the wrong size, one untagged
outline, one tag with no outline, one outline holding two tags) and a ground-floor column sheet. The test proves the
generic route measures what is source-complete, refuses the rest as UNRESOLVED with an exception, never marks
anything VERIFIED, and runs end to end in one command. It is not a blind test on a real villa (none is available)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine import boq_m1_xlsx as XL                      # noqa: E402
from engine.source import drawing_inventory as DI         # noqa: E402
from tools import urban_structural_boq as CLI             # noqa: E402

FR1, FR2 = (0, 0, 42000, 29700), (50000, 0, 92000, 29700)


def rect(msp, x, y, w, h, layer):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True, dxfattribs={"layer": layer})


def tag(msp, text, x, y, layer="S-TEXT"):
    msp.add_text(text, dxfattribs={"layer": layer, "height": 150}).set_placement((x, y))


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    d = tmp_path_factory.mktemp("villa")
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    for b in (FR1, FR2):
        rect(msp, b[0], b[1], b[2] - b[0], b[3] - b[1], "FRAME")
    tag(msp, "FOUNDATION PLAN", 2000, 27000)
    tag(msp, "GROUND FLOOR COLUMN PLAN", 52000, 27000)
    for x in (5000, 10000):                                        # two F1, drawn at the schedule size
        rect(msp, x, 5000, 1500, 1500, "S-FTG")
        tag(msp, "F1", x + 600, 5700)
    rect(msp, 15000, 5000, 1800, 1500, "S-FTG")                    # F2 drawn 1800 x 1500, scheduled 2000 x 1500
    tag(msp, "F2", 15600, 5700)
    rect(msp, 20000, 5000, 1000, 1000, "S-FTG")                    # an outline with no tag
    tag(msp, "F3", 25000, 5000)                                    # a tag with no outline
    rect(msp, 30000, 5000, 1500, 1500, "S-FTG")                    # one outline, two tags
    tag(msp, "F1", 30300, 5700)
    tag(msp, "F2", 30900, 5700)
    rect(msp, 55000, 5000, 300, 300, "S-COL")
    tag(msp, "C1", 55100, 5100)
    rect(msp, 60000, 5000, 200, 500, "S-COL")
    tag(msp, "C2", 60050, 5200)
    rect(msp, 65000, 5000, 300, 300, "S-COL")
    tag(msp, "C9", 65100, 5100)                                    # not in the schedule
    for k in range(3):
        tag(msp, f"B{k + 1}", 70000 + 1000 * k, 9000)              # beam tags: evidence only
    path = d / "NEW_VILLA_SYNTHETIC.dxf"
    doc.saveas(path)
    profile = {
        "profile": "SYNTHETIC_VILLA_PROFILE", "confirmed_by": "test fixture", "units_to_mm": 1.0,
        "drawing_sha256": DI.sha256_file(path),
        "sheets": [{"sheet_id": "FP", "box": list(FR1), "storey": "FOUNDATION"},
                   {"sheet_id": "GFC", "box": list(FR2), "storey": "GF", "storey_height_m": 3.5,
                    "storey_height_source": "synthetic section A-A"}],
        "families": {
            "FOOTINGS": {"layers": ["S-FTG"], "tag_regex": r"^F\d+$", "sheets": ["FP"], "size_tol_mm": 10,
                         "schedule": {"F1": {"L_mm": 1500, "W_mm": 1500, "D_mm": 500},
                                      "F2": {"L_mm": 2000, "W_mm": 1500, "D_mm": 600}},
                         "schedule_source": "synthetic footing schedule"},
            "COLUMNS": {"layers": ["S-COL"], "tag_regex": r"^C\d+$", "sheets": ["GFC"], "size_tol_mm": 10,
                        "schedule": {"C1": {"B_mm": 300, "H_mm": 300}, "C2": {"B_mm": 200, "H_mm": 500}}}}}
    return path, profile, d


def test_inventory_finds_sheets_layers_tags_and_outlines(villa):
    path, _, _ = villa
    inv = DI.inventory(ezdxf.readfile(path), path)
    assert [f["box"] for f in inv["frames"]] == [list(map(float, FR1)), list(map(float, FR2))]
    lay = {r["layer"]: r for r in inv["layers"]}
    assert lay["S-FTG"]["role_guess"] == "FOOTING" and lay["S-FTG"]["closed_rectangles"] == 5
    assert lay["S-COL"]["role_guess"] == "COLUMN" and lay["S-COL"]["closed_rectangles"] == 3
    tags = {t["prefix"]: t for t in inv["tag_families"]}
    assert tags["F"]["count"] == 6 and tags["C"]["count"] == 3 and tags["B"]["family_guess"] == "BEAMS"
    tpl = DI.profile_template(inv)
    assert tpl["families"]["FOOTINGS"]["layers"] == ["S-FTG"] and tpl["units_to_mm"] is None
    assert all(s["storey"] is None and s["storey_height_m"] is None for s in tpl["sheets"])   # never defaulted


def test_profile_route_measures_only_what_is_source_complete(villa, tmp_path):
    path, profile, _ = villa
    R = CLI.compute([str(path)], profile=profile)
    s = R["summary"]
    assert s["route"] == "B_PROFILE_TAKEOFF"
    items = R["items"]
    assert not [i for i in items if i["category"] == "VERIFIED"]          # a new project is never VERIFIED
    prov = sorted((i["family"], round(i["base"], 6)) for i in items if i["category"] == "PROVISIONAL")
    assert prov == [("COLUMNS", 0.315), ("COLUMNS", 0.35), ("FOOTINGS", 1.125), ("FOOTINGS", 1.125)]
    assert {i["support"] for i in items if i["category"] == "PROVISIONAL"} == {"SOURCE_COMPLETE_UNREVIEWED"}
    un = {i["blocker"]: i for i in items if i["category"] == "UNRESOLVED" and i["family"] in ("FOOTINGS", "COLUMNS")}
    assert set(un) == {"SIZE_MISMATCH", "TAG_WITHOUT_OUTLINE", "COMBINED_OUTLINE", "TYPE_NOT_IN_SCHEDULE"}
    mm = un["SIZE_MISMATCH"]
    assert (round(mm["exposure_low"], 6), round(mm["exposure_high"], 6)) == (1.62, 1.8)
    kinds = {e["KIND"] for e in R["exceptions"]}
    assert {"RECTANGLE_WITHOUT_TAG", "TAG_OUTSIDE_EVERY_RECTANGLE", "RECTANGLE_WITH_SEVERAL_TAGS", "SIZE_MISMATCH",
            "TYPE_NOT_IN_SCHEDULE", "UNRESOLVED"} <= kinds
    beams = next(i for i in items if i["item_id"] == "U-C:BEAMS:NO_GENERIC_EXTRACTOR")
    assert "3 'B' tags" in beams["expression"]
    tot = s["totals"]["CONCRETE"]
    assert tot["PLANNING_BASE"] == pytest.approx(0.315 + 0.35 + 2 * 1.125)
    assert tot["PLANNING_BASE"] == tot["PLANNING_LOW"] == tot["PLANNING_HIGH"]
    res = CLI.write_all(R, tmp_path / "out", as_of="2026-10-10", pdf=False, xlsx=True)
    for name in ("SUMMARY.json", "PROVISIONAL_REGISTER.csv", "UNRESOLVED_REGISTER.csv", "EXCEPTIONS.csv",
                 "CONTRACTOR_BOQ.csv", "BOQ_REPORT.html", "STRUCTURAL_BOQ.xlsx", "run_log.json"):
        assert (tmp_path / "out" / name).exists(), name
    XL.validate(tmp_path / "out" / "STRUCTURAL_BOQ.xlsx", CLI.workbook_model(R))
    assert res["xlsx"]["file_sha256"] == CLI.write_all(R, tmp_path / "again", as_of="2026-10-10", pdf=False,
                                                       xlsx=True)["xlsx"]["file_sha256"]   # deterministic bytes


def test_no_profile_gives_an_inventory_a_template_and_only_unresolved(villa, tmp_path):
    path, _, _ = villa
    R = CLI.compute([str(path)])
    assert R["summary"]["route"] == "C_INVENTORY_ONLY"
    assert {i["category"] for i in R["items"]} == {"UNRESOLVED"}
    CLI.write_all(R, tmp_path, as_of="2026-10-10", pdf=False, xlsx=False)
    tpl = json.loads((tmp_path / "PROFILE_TEMPLATE.json").read_text())
    assert tpl["families"]["COLUMNS"]["layers"] == ["S-COL"]


def test_one_command_cli_with_pdf(villa, tmp_path):
    path, profile, d = villa
    pf = d / "profile.json"
    pf.write_text(json.dumps(profile))
    assert CLI.main(["run", "--drawings", str(path), "--profile", str(pf), "--out", str(tmp_path / "o"),
                     "--as-of", "2026-10-10", "--no-xlsx"] + ([] if Path(CLI.CHROMIUM).exists() else ["--no-pdf"])) == 0
    log = json.loads((tmp_path / "o" / "run_log.json").read_text())
    assert log["manual_interventions_during_run"] == 0
    assert [s["step"] for s in log["steps"]][:2] == ["1 accept", "2 inventory"]
    if Path(CLI.CHROMIUM).exists():
        from pypdf import PdfReader
        assert len(PdfReader(str(tmp_path / "o" / "BOQ_REPORT.pdf")).pages) >= 1
    assert CLI.main(["inventory", "--drawings", str(path), "--out", str(tmp_path / "inv")]) == 0
    assert json.loads((tmp_path / "inv" / "INVENTORY.json").read_text())[0]["n_layers"] >= 4


def test_unreadable_inputs_are_refused(tmp_path):
    p = tmp_path / "x.dwg"
    p.write_bytes(b"AC1032")
    with pytest.raises(CLI.PipelineError):
        CLI.accept([str(p)])
    with pytest.raises(CLI.PipelineError):
        CLI.parse_sets(["NOEQUALS"])
    assert CLI.parse_sets(["A=1.5", "B=TEXT"]) == {"A": 1.5, "B": "TEXT"}
