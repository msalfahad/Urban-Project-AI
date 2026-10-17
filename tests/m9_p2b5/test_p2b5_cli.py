"""Phase 2B-5 (ARCH_TAKEOFF_V2.6) through the CLI: V2.6 is opt-in (a V2.5 run carries none of its outputs); V2.6
keeps every BOQ line of V2.5 byte for byte (the installation layer adds outputs, it changes no quantity); V2.6 is
deterministic; the PD-1 drawing (two WP-B bathrooms) gives, through the whole drawing route, the piece plan of the
hand-derived WP-B plan for both bathrooms; the shared cutting plan names each area's own cuts."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b3"))

import proof_drawings as PD                                   # noqa: E402
import proof_engine as E                                      # noqa: E402
from tools import arch_synth as AS                            # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402

V26 = "ARCH_TAKEOFF_V2.6"
NEW = ("MEMBRANE_PIECE_PLAN.json", "MEMBRANE_PIECE_PLAN.csv", "WP_INSTALLATION.json", "WP_INSTALLATION.csv")


@pytest.fixture(scope="module")
def drawings(tmp_path_factory):
    d = tmp_path_factory.mktemp("dxf")
    AS.villa(d / "villa.dxf")
    return {"villa": d / "villa.dxf", "pd1": Path(PD.bathrooms(d / "pd1.dxf"))}


@pytest.fixture(scope="module")
def runs(drawings, tmp_path_factory):
    t = tmp_path_factory.mktemp("runs")
    return {"v25": E.cli_run(drawings["pd1"], t / "v25"), "v26": E.cli_run(drawings["pd1"], t / "v26", method=V26),
            "v26b": E.cli_run(drawings["pd1"], t / "v26b", method=V26),
            "villa25": E.cli_run(drawings["villa"], t / "villa25"),
            "villa26": E.cli_run(drawings["villa"], t / "villa26", method=V26)}


def _hashes(out):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(out).iterdir()) if p.is_file()}


def test_v2_6_is_opt_in(runs):
    names = set(_hashes(runs["v25"]["out"]))
    assert not names & set(NEW)
    assert runs["v25"]["read"]("OUTPUT_MANIFEST.json")["policy"] == "URBAN_OUTPUT_MANIFEST_V2_5"
    assert all("trace" not in (m.get("layout") or {}) for m in runs["v25"]["read"]("MATERIAL_RESULTS.json")["results"])
    v26 = runs["v26"]
    assert v26["code"] == 0 and set(NEW) <= set(_hashes(v26["out"]))
    assert v26["read"]("OUTPUT_MANIFEST.json")["policy"] == "URBAN_OUTPUT_MANIFEST_V2_6"
    assert v26["read"]("WATERPROOFING_SCHEDULE.json")["run"]["policy"] == M9.ARCH_POLICY_ID_V26
    assert v26["read"]("RUN_RULES.json")["arch"]["v2_6"]["corrections"] == list(M9.V26_CORRECTIONS)


@pytest.mark.parametrize("pair", [("v25", "v26"), ("villa25", "villa26")])
def test_v2_6_keeps_every_boq_line(runs, pair):
    a, b = (runs[k]["out"] for k in pair)
    for n in ("BOQ_LINES.json", "BOQ_LINES.csv", "COVERAGE.csv", "WATERPROOFING_SCHEDULE.csv", "SURFACE_LEDGER.csv",
              "DOOR_FEASIBILITY.csv"):
        assert (a / n).read_bytes() == (b / n).read_bytes(), n


def test_v2_6_is_deterministic(runs):
    ha, hb = _hashes(runs["v26"]["out"]), _hashes(runs["v26b"]["out"])
    assert ha.keys() == hb.keys() and [k for k in ha if ha[k] != hb[k]] == []


def test_the_drawing_route_gives_the_wp_b_piece_plan(runs):
    plans = runs["v26"]["read"]("MEMBRANE_PIECE_PLAN.json")["piece_plans"]
    baths = [p for p in plans if p["state"] == "COMPUTED"]
    assert len(baths) == 2
    for p in baths:
        b = p["balance"]
        assert (b["consumed_m2"], b["installed_m2"], b["true_waste_m2"], b["reusable_m2"], b["roll_stock_m2"],
                b["rolls"]) == (17.8, 17.52, 0.28, 0.0, 2.2, 2)
        sizes = sorted((x["kind"], x["w_m"], x["l_m"]) for x in p["pieces"])
        assert sizes == sorted([("FLOOR", 1.0, 3.0)] * 4 + [("FLOOR", 0.4, 3.0), ("DOORWAY", 0.3, 1.0)] +
                               [("BAND", 0.3, 3.0), ("BAND", 0.3, 2.0)] + [("BAND", 0.3, 2.8)] * 3)
    inst = runs["v26"]["read"]("WP_INSTALLATION.json")
    for x in inst["installation"]:
        if x["state"] == "COMPUTED":
            assert "FLOOR_WALL_JUNCTION_UNRESOLVED" in x["flags"]
            assert x["junction"]["rolls_range"] == [2, 3]


def test_the_shared_cutting_plan_names_each_areas_cuts(runs):
    plans = runs["villa26"]["read"]("MEMBRANE_PIECE_PLAN.json")["piece_plans"]
    cut = {}
    for p in plans:
        for r in p.get("rolls") or ():
            for c in r["cuts"]:
                cut[f"{p['room_id']}:{c['id']}"] = c["length_m"]
    shared = runs["villa26"]["read"]("MEMBRANE_CUTTING_PLAN.json")["systems"]
    pieces = [x for s in shared for r in s["cutting_plan"] for x in r["pieces"]]
    assert pieces and sorted(x["cut_id"] for x in pieces) == sorted(cut)
    assert all(cut[x["cut_id"]] == x["length_m"] for x in pieces)


def test_v2_6_only_inputs_follow_v2_5(drawings, tmp_path):
    with pytest.raises(SystemExit):
        M9.main(["arch", "--drawings", str(drawings["pd1"]), "--out", str(tmp_path / "x"), "--method",
                 "ARCH_TAKEOFF_V2.4", "--independent-checks", str(tmp_path / "none.json")])
