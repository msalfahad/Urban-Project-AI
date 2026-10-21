"""Phase 2B-3 (ARCH_TAKEOFF_V2.5) through the CLI: V2.5 is opt-in (a V2.4 run carries none of its outputs, keys or
methods); V2.5 is deterministic; the proof drawing PD-1 reproduces the WP-B hand calculation for both of its
bathrooms through the whole drawing route; the synthetic villa's procurement count is proven minimal; the V2.5-only
inputs are refused by the other methods."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import proof_cases as C                                       # noqa: E402
import proof_drawings as PD                                   # noqa: E402
import proof_engine as E                                      # noqa: E402
from tools import arch_synth as AS                            # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402


@pytest.fixture(scope="module")
def drawings(tmp_path_factory):
    d = tmp_path_factory.mktemp("dxf")
    AS.villa(d / "villa.dxf")
    return {"villa": d / "villa.dxf", "pd1": Path(PD.bathrooms(d / "pd1.dxf"))}


def _hashes(out):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(out).iterdir()) if p.is_file()}


def test_v2_5_is_opt_in(drawings, tmp_path):
    run = E.cli_run(drawings["villa"], tmp_path / "v24", method=E.V24)
    assert run["code"] == 0
    names = set(_hashes(run["out"]))
    assert "BOQ_TRACEABILITY.json" not in names and "BOQ_TRACEABILITY.csv" not in names
    assert run["read"]("OUTPUT_MANIFEST.json")["policy"] == "URBAN_OUTPUT_MANIFEST_V2_4"
    wp = run["read"]("WATERPROOFING_SCHEDULE.json")
    assert "v2_5" not in wp["run"] and all("proven_subtotal" not in a for a in wp["waterproofing"]["areas"])
    mats = [m for m in run["read"]("MATERIAL_RESULTS.json")["results"] if (m.get("method") or "").startswith("MEMB")]
    assert mats and all(m["method"] == "MEMBRANE_POLYGON_STRIPS_V2_4" for m in mats)
    assert all("band_planner" not in (m.get("layout") or {}) for m in mats)
    assert all("packing" not in s for s in run["read"]("MEMBRANE_CUTTING_PLAN.json")["systems"])
    v25 = E.cli_run(drawings["villa"], tmp_path / "v25")
    assert v25["read"]("OUTPUT_MANIFEST.json")["policy"] == "URBAN_OUTPUT_MANIFEST_V2_5"
    assert v25["read"]("WATERPROOFING_SCHEDULE.json")["run"]["policy"] == M9.ARCH_POLICY_ID_V25


def test_v2_5_is_deterministic(drawings, tmp_path):
    a = E.cli_run(drawings["pd1"], tmp_path / "a")
    b = E.cli_run(drawings["pd1"], tmp_path / "b")
    ha, hb = _hashes(a["out"]), _hashes(b["out"])
    assert ha.keys() == hb.keys() and [k for k in ha if ha[k] != hb[k]] == []


def test_the_drawing_route_reproduces_the_3x4_hand_calculation(drawings, tmp_path):
    """multi-drawing validation: both bathrooms of PD-1 are the WP-B bathroom drawn in a plan (rooms, walls, door
    blocks, wall depth from the drawing) - every quantity of the hand calculation comes back through the route."""
    run = E.cli_run(drawings["pd1"], tmp_path / "out")
    wp = run["read"]("WATERPROOFING_SCHEDULE.json")["waterproofing"]
    exp = C.WP_B["expected"]
    for a in wp["areas"]:
        got = {"A_net_m2": a["A_net_horizontal_m2"], "eligible_m": a["upturn"]["eligible_lm"],
               "upturn_m2": a["upturn"]["area_m2"], "doorway_continuation_m2": a["doorway_continuation_m2"],
               "proven_subtotal_m2": a["proven_subtotal"]["total_m2"], "laps_m2": a["laps_m2"],
               "B_m2": a["B_installed_m2"], "consumed_m2": a["consumed_m2"], "waste_m2": a["cutting_waste_m2"],
               "rolls": a["rolls_if_installed_alone"], "direction": a["direction"],
               "final_material_state": a["final_material_state"]}
        assert got == {k: exp[k] for k in got}, a["room_id"]
        assert a["doorway_transitions"]["unresolved"] == 1 and a["roll_sensitivity"]["changes_roll_count"] is False
    plan = run["read"]("MEMBRANE_CUTTING_PLAN.json")["systems"][0]
    assert (plan["rolls"], plan["packing"]["lower_bound"], plan["roll_count_state"]) == (4, 4, "PROVISIONAL")


def test_the_villa_procurement_is_proven_minimal(drawings, tmp_path):
    run = E.cli_run(drawings["villa"], tmp_path / "out")
    plan = run["read"]("MEMBRANE_CUTTING_PLAN.json")["systems"][0]
    assert plan["rolls"] == plan["packing"]["lower_bound"] and plan["packing"]["proven"]
    for a in run["read"]("WATERPROOFING_SCHEDULE.json")["waterproofing"]["areas"]:
        assert a["final_material_state"] in ("PROVISIONAL_DETAILS_OPEN", "COMPLETE_BASIS", "BLOCKED")
        assert a["proven_subtotal"]["total_m2"] <= a["B_installed_m2"]


def test_v2_5_inputs_are_refused_by_the_other_methods(drawings, tmp_path):
    with pytest.raises(SystemExit):
        M9.arch_compute(str(drawings["pd1"]), method="ARCH_TAKEOFF_V2.3", project_rules={"schema": "x"})
    with pytest.raises(SystemExit):
        M9.arch_compute(str(drawings["pd1"]), method=E.V24, independent_checks={"schema": "x"})
    chk = tmp_path / "c.json"
    chk.write_text(json.dumps({"schema": "URBAN_INDEPENDENT_CHECKS_V1", "checks": []}), encoding="utf-8")
    with pytest.raises(SystemExit):
        M9.main(["arch", "--drawings", str(drawings["pd1"]), "--out", str(tmp_path / "o"), "--method", E.V24,
                 "--independent-checks", str(chk)])
