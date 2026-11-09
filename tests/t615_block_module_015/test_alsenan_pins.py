"""T-615 on the training villa: committed outputs reproduce; the 15 carried 0.15 m walls leave HELD with the T-533
S-A figures; 12 end + 49 interior ties and 367.9895 m.l strip leave HELD with the T-355 PRIMARY counts; the drawing
search found no printed 15 cm face."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t615"
sys.path.insert(0, str(HERE))
import t615_alsenan as T  # noqa: E402

S = json.loads((HERE / "out" / "SUMMARY_T615.json").read_text(encoding="utf-8"))


def _csv(name):
    return list(csv.DictReader((HERE / "out" / name).open(encoding="utf-8")))


def test_committed_files_reproduce():
    assert T.main(["--check"]) == 0


def test_t533_inputs_untouched_by_the_run():
    import t533_alsenan as A
    T.texts()
    assert A.INPUTS[2] == "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
    assert A.main(["--check"]) == 0


def test_fifteen_walls_restated():
    rows = _csv("WALLS_015_T615.csv")
    assert len(rows) == 15 and not {"GF-W22", "2F-W08"} & {r["wall_id"] for r in rows}
    for r in rows:
        assert r["status"] == "ASSUMED - OWNER-APPROVED"
        assert float(r["units_nr"]) == pytest.approx(float(r["material_base_m2"]) * 12.5, abs=1e-4)
        assert float(r["units_nr"]) > 0 and float(r["panel_mortar_m3"]) > 0
        assert float(r["panel_contract_m3"]) == pytest.approx(float(r["panel_t367_m3"]), abs=2e-6)


def test_totals_equal_t533_s_a():
    sa = S["reproduces"]
    assert f"{S['units_nr']['low']:.2f} .. {S['units_nr']['theoretical']:.2f}" == sa["t533_s_a_units"]
    assert f"{S['panel_mortar_m3']['low']:.6f} .. {S['panel_mortar_m3']['material_base']:.6f}" == sa["t533_s_a_panel"]
    assert [f"{S['perimeter_mortar_m3']['figure']:.6f}", f"{S['perimeter_mortar_m3']['high']:.6f}"] == sa["t533_s_a_perimeter"]
    assert S["units_nr"]["theoretical"] == pytest.approx(175.871 * 12.5)
    assert S["panel_mortar_m3"]["material_base"] == pytest.approx(1.945573, abs=1e-6)
    assert S["perimeter_mortar_m3"]["low"] == pytest.approx(0.078582, abs=1e-6)
    assert S["cement_bags_50kg"]["high"] == pytest.approx((1.945573 + 0.089890) * 8, abs=1e-3)
    assert S["units_nr"]["procurement"].startswith("HELD")


def test_accessories_restated():
    t = S["ties_pcs"]
    assert (t["end_restated"], t["end_walls"], t["interior_restated"], t["interior_junctions"]) == \
        (12, ["1F-W23", "2F-W08"], 49, 8)
    assert t["ledger_measured_after"] - t["ledger_measured_before"] == 61
    assert t["d39_2f_w08_tie_range"] == [6, 6]
    s = S["bed_joint_strip_ml"]
    assert (s["restated"], s["walls"]) == (367.9895, 25)
    assert s["ledger_measured_after"] == pytest.approx(s["ledger_measured_before"] + s["restated"], abs=1e-4)
    rows = _csv("ACCESSORIES_015_T615.csv")
    assert all(r["was"].startswith("HELD") and r["now"] not in ("", "0") for r in rows)


def test_drawing_search_reports_no_printed_face():
    assert all(d["verdict"] != "DIFFERENT FACE PRINTED" for d in S["drawing_search"])
    assert "nothing is reported against Q-80" in S["drawing_result"]
    assert any(f["id"] == "FR-T615-7" for f in S["fix_rows"])
