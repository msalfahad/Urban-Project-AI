"""T-354 development villa (committed inputs only: ALSENAN_SOIL_TREATMENT_INPUT.json, sheet / note numbers and handles
read from ST7757.pdf, 'ST7757 dxf.dxf' sha 9f9d1179, P7757.dxf sha ab54dd55, the architectural and sanitary PDFs).
Re-runs the check without writing and pins the engineering result: B1-05 NOT_IN_DRAWN_SCOPE, quantity None."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t354"
sys.path.insert(0, str(HERE))
import t354_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
INP = json.loads((HERE / "ALSENAN_SOIL_TREATMENT_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_references_only():
    txt = (HERE / "ALSENAN_SOIL_TREATMENT_INPUT.json").read_text(encoding="utf-8")
    assert "9f9d1179" in txt and "ab54dd55" in txt
    assert not re.search(r"\d{5,}\.\d", txt)  # no drawing coordinates
    assert not re.search(r"[؀-ۿ]", txt)  # no Arabic note text copied


def test_every_sheet_of_the_set_searched_and_absent():
    assert len(INP["set_sheets"]) == 31 and len(ROWS) == 31
    assert {r["sheet"] for r in ROWS} == set(INP["set_sheets"])
    assert all(r["searched"] and r["soil_treatment"] == "absent" for r in ROWS)
    assert SUM["sheets"] == {"ST": {"sheets": 16, "requires": 0}, "ARCH": {"sheets": 12, "requires": 0},
                             "SAN": {"sheets": 3, "requires": 0}}


def test_b1_05_not_in_drawn_scope_never_zero():
    sc = SUM["b1_05_scope"]
    assert sc["status"] == "NOT_IN_DRAWN_SCOPE" and sc["area_m2"] is None and sc["unsearched"] == []
    assert SUM["quantity_m2"] is None and SUM["freelancer_row"] is None and SUM["engine_line"] is None


def test_p8_recommendations_read_in_full():
    p8 = next(r for r in INP["sheet_search"] if r["sheet"] == "ST p.8")
    assert "1-24" in p8["notes_read"] and p8["requires"] == []


def test_related_layers_are_owned_elsewhere_not_soil_treatment():
    classes = {r["class"] for r in INP["related_printed_layers"]}
    assert "FOUNDATION_WATERPROOFING" in classes and "CONCRETE_MATERIAL" in classes
    assert all(r["owner"] for r in INP["related_printed_layers"])
    assert SUM["dxf_hits_by_class"] == {"FALSE_POSITIVE": 1, "NOT_SOIL_TREATMENT": 2}


def test_zones_named_for_a_future_source_are_not_summed():
    zs = INP["zones_if_required"]
    assert [z["zone"] for z in zs] == SUM["zones_if_required"]
    assert any(z["plan_m2"] is None for z in zs)  # Z-S, Z-T, Z-W not formed: no total can be written
    assert SUM["quantity_m2"] is None
    assert not any(isinstance(v, (int, float)) and abs(v - (125.344805 + 11.851051)) < 1e-6
                   for v in json.loads(json.dumps(SUM, default=str)).values())
