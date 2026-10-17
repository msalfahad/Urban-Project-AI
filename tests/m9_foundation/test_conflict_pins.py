"""M9 S1 conflict regression pins (M9A register C01-C24): today's behaviour of every existing implementation is
pinned under its own version, and the new owner behaviour only under the new rule set - nothing is unified silently.
Rows the S1 engine does not exercise are listed with the slice that will pin them, so no row is forgotten."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine import finishes_rules as FR
from engine.source import arch_quantity_truth as AQT
from engine.source import boq_line as BL
from engine.source import membrane_layout as ML
from engine.source import material_spec as MS
from engine.source import rule_store as RS
from engine.source import stair_geometry as SG
from engine.source import waterproofing_policy as WPP

ROOT = Path(__file__).resolve().parents[2]
WP1 = dict(floor=2.30 * 3.20, perimeter=11.0, door=0.90)
PINNED = {"C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C15", "C16", "C17", "C18", "C24"}
LATER = {"C11": "S3 (plaster behind full-height wet tile, Q-CER-2)", "C12": "S3 (paint vs plaster heights)",
         "C13": "S3 (ceiling area vs material)", "C14": "S2/S3 (per-trade opening table on real rooms, Q-OPN-1)",
         "C19": "owner rule pack (Q-PACK-1)", "C20": "S4 (riser band naming with the stair finish model)",
         "C21": "S4 (elevator marble into the finish model)", "C22": "after a freeze only (benchmark firewall)",
         "C23": "S2 (drawing conflict ledger -> RFI)"}


def test_every_register_row_is_pinned_or_scheduled():
    assert PINNED | set(LATER) == {f"C{i:02d}" for i in range(1, 25)} and not (PINNED & set(LATER))


def test_c01_upturn_today_per_implementation_and_the_new_rule():
    assert FR.upturn(WP1["perimeter"], openings_lm=WP1["door"]).value == pytest.approx(1.515)
    assert WPP.wet(floor_m2=WP1["floor"], perimeter_m=11.0, door_widths_m=[0.9], room="x")["upturn_m2"] == pytest.approx(1.515)
    edges = [{"length_m": 10.1, "kind": "WALL"}, {"length_m": 0.9, "kind": "DOOR"}]
    assert AQT.waterproofing(floor_m2=WP1["floor"], edges=edges)["upturn_area_reference_m2"] == pytest.approx(1.65)
    assert RS.rule("UP-WP-002", "1.4.0")["value"] == 0.15
    sf = ML.surfaces({"length_m": 2.3, "width_m": 3.2}, upturn_h=RS.rule("UP-WP-002")["value"],
                     doorways=[{"width_m": 0.9, "depth_m": 0.2}])
    assert sf["rows"][-1]["net_m2"] == pytest.approx(2.2)


def test_c02_doorway_piece_and_doorway_upturn_are_separate_rows_and_flagged():
    sf = ML.surfaces({"length_m": 2.3, "width_m": 3.2}, upturn_h=0.2, doorways=[{"width_m": 0.9, "depth_m": 0.2}])
    rows = {r["item_code"]: r["net_m2"] for r in sf["rows"]}
    assert rows["FIN.WP.DOORWAY"] == pytest.approx(0.18) and 0.9 * 0.2 == pytest.approx(0.18)
    assert "DOORWAY_DOUBLE_COVERAGE_REVIEW" in sf["flags"]


def test_c03_one_lap_factor_today_versus_the_roll_plan():
    assert WPP.procurement(9.74)["state"] == "NOT_APPLIED"
    assert WPP.procurement(9.74, system="X", lap_factor=1.1)["procurement_m2"] == pytest.approx(10.714)
    r = ML.plan({"length_m": 2.3, "width_m": 3.2}, MS.membrane(),
                constraints={"upturn_h_m": 0.2, "doorways": [{"width_m": 0.9, "depth_m": 0.2}], "direction": "ALONG_Y"})
    assert r["net_installed_m2"] == pytest.approx(9.74) and r["overlap_m2"] > 0 and r["packaging"]["packs"] == 2


def test_c04_c05_shower_and_method_text_keep_their_old_values_until_decided():
    assert RS.rule("UP-WP-004")["version"] == "1.0.0"
    assert RS.rule("UP-WP-004", include_proposed=True)["version"] == "1.1.0"
    reg = json.loads((ROOT / "rules/methods/URBAN_METHOD_REGISTER_V1.json").read_text(encoding="utf-8"))
    m = next(x for x in reg["methods"] if x["id"] == "URBAN-ROOF-WATERPROOF-UPTURN-200@v1")
    assert m["parameters"]["wet_upturn_m"] == 0.15 and "WET_ROOM" in m["never_applies_to"]


def test_c06_c07_structural_riser_face_and_railing_path_today():
    f = SG.straight_flight(12, 0.165, 0.28, 1.20, 0.15)
    assert f["FINISHING_RISER_AREA"] == pytest.approx(12 * 0.165 * 1.20)          # 2.376: the full structural riser
    assert 12 * (0.165 - 0.03) * 1.20 == pytest.approx(1.944)                         # UP-STAIR-003 visible marble riser
    assert f["HANDRAIL_PATH_LENGTH"] == pytest.approx(3.575, abs=5e-4) and f["run"] == pytest.approx(3.08)
    assert RS.rule("UP-STAIR-012", "1.4.0")["version"] == "1.0.0" and RS.rule("UP-STAIR-012")["version"] == "2.0.0"


def test_c08_c10_new_rules_exist_only_from_1_5_0():
    for rid in ("UP-STAIR-013", "UP-CER-009", "UP-WP-005", "UP-CER-010"):
        with pytest.raises(KeyError):
            RS.rule(rid, "1.4.0")
        assert RS.rule(rid)["status"] == "OWNER_APPROVED"
    assert RS.rule("UP-CER-009")["example_rationale_only"]["height_m"] == pytest.approx(4.50 - 0.60 - 0.15 - 0.08)


def test_c09_c15_c18_canonical_line_rules():
    base = dict(project_id="P", revision_set_sha256="0" * 64, unit="m2", element_id="E", formula="f", rule_id="R",
                rule_version="1", item_code="FIN.MARBLE.TREAD", evidence_state="SOURCE_DERIVED", measured_net=1.0)
    with pytest.raises(BL.LineError):
        BL.make_line(**base, measure_pair={"pair_id": "S", "price_one_basis": False})
    for voc, t in BL.LEGACY.items():
        for st in t:
            ev, _ = BL.adapt(voc, st, has_exposure=True, support="SOURCE_COMPLETE_UNREVIEWED")
            assert ev is None or BL.RANK[ev] <= BL.RANK[BL.CEILING[voc][st]]
    with pytest.raises(BL.LineError):
        BL.make_line(**dict(base, inputs={"waste_cost": 1}))


def test_c16_the_rule_store_reads_only_rules():
    src = (ROOT / "engine/source/rule_store.py").read_text(encoding="utf-8")
    assert 'STORE = ROOT / "rules"' in src and "tests/" not in src and "data/trade_rules" not in src.split('"""', 2)[2]


def test_c17_convention_defaults_today_and_the_m9_run_record():
    m2 = (ROOT / "tools/urban_boq_m2.py").read_text(encoding="utf-8")
    pr = (ROOT / "tools/urban_project_run.py").read_text(encoding="utf-8")
    assert 'GENERIC_CONVENTIONS = "engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json"' in m2
    assert 'DEFAULT_CONVENTIONS = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"' in pr
    m9 = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    assert '"conventions": conventions' in m9 and "rule_set_digest" in m9


def test_c24_opening_deductions_per_trade():
    old = RS.rule("UP-GEN-003", "1.4.0")
    assert old["version"] == "1.0.0"
    assert RS.rule("UP-GEN-003")["value"] == {"SKIRTING": "DEDUCT_DOOR_WIDTHS", "WALL_TILE": "GROSS_MINUS_OPENINGS",
                                              "WATERPROOFING_UPTURN": "NO_DEDUCTION",
                                              "PLASTER_PAINT": "OWNER_DECISION_PENDING"}
