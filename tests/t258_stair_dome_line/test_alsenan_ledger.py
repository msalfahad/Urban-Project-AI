"""T-258 development-villa ledger pinned: CONC.STAIR_DOME components, each once, from the committed input file."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t258"
_s = importlib.util.spec_from_file_location("t258_alsenan_check", HERE / "t258_alsenan_check.py")
A = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t258_alsenan_check", A)
_s.loader.exec_module(A)


@pytest.fixture(scope="module")
def run():
    s, comps = A.summary(A.load())
    return s, {c["id"]: c for c in comps}


def test_committed_files_regenerate_byte_identical():
    js, cs = A.render(A.load())
    assert (HERE / "summary.json").read_text(encoding="utf-8") == js
    assert (HERE / "LEDGER_T258.csv").read_text(encoding="utf-8") == cs


def test_components_and_classes(run):
    s, c = run
    assert s["components"] == 47
    assert s["by_class"] == {"CLOSABLE": 13, "CONFLICT": 1, "HELD": 11, "UNKNOWN": 1, "OWNED_ELSEWHERE": 15,
                             "BESIDE": 6}
    t = s["totals"]
    assert t["closable_total"] == pytest.approx(10.805258, abs=2e-6)
    assert t["closable"]["VERIFIED"] == pytest.approx(8.344131, abs=2e-6)
    assert t["closable"]["DRAWING-CONFIRMED"] == pytest.approx(0.924903, abs=2e-6)
    assert t["closable"]["ASSUMED — OWNER-APPROVED"] == pytest.approx(1.536225, abs=2e-6)
    assert t["conflict"] == pytest.approx([0.863029, 1.054813], abs=2e-6)
    assert t["line_closable"] is False


def test_checker_verified_figures_reproduced(run):
    _, c = run
    assert c["ST01-MS1-U"]["value"] == pytest.approx(0.9976, abs=1e-4)      # Checker 2026-10-22 17:18
    assert c["ST01-MS2-L"]["value"] == pytest.approx(1.033445, abs=2e-6)    # Checker 01:57 / T-187
    assert c["ST01-MS2-U"]["value"] == pytest.approx(1.001373, abs=2e-6)    # T-187 Gate B
    assert c["ST01-MS1-LD"]["value"] == pytest.approx(0.2304, abs=1e-9)
    assert c["DOME-A-SHELL"]["value"] == pytest.approx(2.540681, abs=1e-6)  # T-185 / V3.0.7
    assert c["ST02-RS-S"]["value"] + 0.028928 == pytest.approx(0.9716, abs=1e-4)  # Checker gross 0.9716


def test_ms2_landing_conflict_closed_by_the_flight_edge(run):
    s, c = run
    r = s["retired_readings"][0]
    assert r["accepted"] is False
    assert r["overlap_with_flight_m3"] == pytest.approx(0.0096, abs=1e-9)
    assert r["well_end_m3"] == pytest.approx(0.0008, abs=1e-9)
    assert c["ST01-MS2-LD-W"]["value"] + c["ST01-MS2-LD-E"]["value"] == pytest.approx(0.4696, abs=1e-9)
    # 0.480 = 0.4696 + flight overlap + well end: nothing lost, nothing counted twice
    assert 0.4696 + r["overlap_with_flight_m3"] + r["well_end_m3"] == pytest.approx(0.480, abs=1e-9)


def test_held_stays_held_never_zero(run):
    _, c = run
    for i in ("ST01-MS2-TR", "ST01b-D1-WAIST", "ST03-E1-WAIST", "ST02-RS-C", "ST02-RS-C-SOFFIT", "DOME-3-SHELL",
              "DOME-A-DRUM", "ST01-MS1-T", "ST01-MS1-T-SLAB"):
        assert c[i]["value"] is None and c[i]["cls"] in ("HELD", "UNKNOWN"), i
    assert c["ST01-MS1-L"]["cls"] == "CONFLICT" and c["ST01-MS1-L"]["value"] is None


def test_floor_landings_and_rings_are_other_lines(run):
    _, c = run
    for i in ("ST01-ARR-1F", "ST01-ARR-2F", "ST02-PLATE"):
        assert c[i]["owner_line"] == "SLAB" and c[i]["cls"] == "OWNED_ELSEWHERE"
    for i in ("DOME-A-RING", "DOME-B-RING", "ST01-MS1-U-HEAD", "ST01-MS2-U-HEAD", "ST01-MS2-L-FOOT", "ST01-B3"):
        assert c[i]["owner_line"] == "BEAM"


def test_freelancer_reconciliation(run):
    s, _ = run
    rec = s["reconciliation"]
    assert rec["ST01"]["flights"]["residual"] == pytest.approx(0.0, abs=1e-5)
    assert rec["ST01"]["landings"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert rec["ST03"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert rec["DOMES"]["residual"] == pytest.approx(0.0, abs=1e-9)
    f = json.loads((HERE / "ALSENAN_STAIR_DOME_INPUT.json").read_text(encoding="utf-8"))["freelancer"]
    parts = sum(f[k]["m3"] for k in ("main_flights", "main_landings", "stair_2", "entrance", "domes"))
    assert parts == pytest.approx(f["total"]["m3"], abs=1e-4)


def test_candidate_entrance_line_is_two_conventions():
    """The candidate releases ST-03 at the engine's own straight_flight(5, 0.165, 0.30, 2.80, 0.175): a convention riser
    (drawn 0.85 / 5 = 0.170) and a waist no sheet prints; the drawing closes only the steps."""
    sys.path.insert(0, str(ROOT))
    from engine.source import stair_geometry as SG
    d = json.loads((HERE / "CANDIDATE_V3011_STAIR_DOME_LINES.json").read_text(encoding="utf-8"))
    by = {r["line_id"]: r for r in d["lines"]}
    st03 = by["L-061e18cf35a4b6b33d68"]
    assert st03["state"] == "PROVISIONAL"
    conv = SG.straight_flight(5, 0.165, 0.30, 2.80, 0.175)["STAIR_CONCRETE_VOLUME"]
    assert float(st03["measured_net"]) == pytest.approx(conv, abs=1e-9)
    assert d["released_with_value_m3"] == pytest.approx(8.064447, abs=1e-6)
    s, c = A.summary(A.load())
    assert c and s["totals"]["closable_total"] - d["released_with_value_m3"] == pytest.approx(2.740811, abs=2e-6)


# ---------------- r2 (Verifier 2026-10-24 12:58 / 13:10)

def test_d1_arrival_wedge_split_into_the_ground_slab(run):
    s, c = run
    # 4 triangles 1/2 x 0.175 x 0.30 x 1.20 = 0.126; the 4th lies beyond 1C7 inside GS-08 (T 0.10 < r 0.175):
    # slab's part 0.0315 x (1 - (0.075 / 0.175)^2) = 0.025714; the sliver 0.005786 below the slab soffit stays
    assert c["ST01b-D1-SLAB"]["value"] == pytest.approx(0.0315 * (1 - (0.075 / 0.175) ** 2), abs=1e-12)
    assert c["ST01b-D1-SLAB"]["owner_line"] == "GROUND_SLAB" and c["ST01b-D1-SLAB"]["cls"] == "OWNED_ELSEWHERE"
    assert c["ST01b-D1-STEPS"]["value"] == pytest.approx(0.100286, abs=1e-6)
    assert c["ST01b-D1-STEPS"]["value"] + c["ST01b-D1-SLAB"]["value"] == pytest.approx(0.126, abs=1e-12)
    # the closable component sits inside the Verifier's range 10.799473 .. 10.830973 (D1 wedge out .. in)
    assert 10.799473 - 1e-6 <= s["totals"]["closable_total"] <= 10.830973 + 1e-6
    # the stair-hall floor is GS-08 (T-242), listed unvalued so the D1 part is not listed twice
    assert c["ST01-SHAFT-FLOOR"]["value"] is None and c["ST01-SHAFT-FLOOR"]["evidence"] == "DRAWING-CONFIRMED"


def test_every_flight_has_exactly_one_arrival_treatment(run):
    s, c = run
    arr = {a["flight"]: a for a in s["arrivals"]}
    flights = {i for i, x in c.items() if x["is_flight"]}
    assert set(arr) == flights == {"ST01-MS1-L", "ST01-MS1-U", "ST01-MS2-L", "ST01-MS2-U", "ST01b-D1-STEPS",
                                   "ST03-E1-STEPS", "ST02-RS-C", "ST02-RS-S", "ST02-RS-A"}
    assert arr["ST01b-D1-STEPS"]["kind"] == "OWNED_ELSEWHERE" and arr["ST01b-D1-STEPS"]["rows"] == ["ST01b-D1-SLAB"]
    assert arr["ST03-E1-STEPS"]["rows"] == ["ST03-E1-SLAB", "ST03-E1-GB"]
    assert arr["ST01-MS1-L"]["kind"] == "HELD_JUNCTION" and arr["ST02-RS-C"]["kind"] == "CONTINUES"
    for f in ("ST01-MS1-U", "ST01-MS2-L", "ST01-MS2-U", "ST02-RS-S", "ST02-RS-A"):
        assert arr[f]["kind"] == "DEDUCTED" and arr[f]["value"] > 0
    # adverse on the real ledger: drop D1's slab row -> refused
    comps = [x for i, x in c.items() if i != "ST01b-D1-SLAB"]
    with pytest.raises(A.SD.LedgerError, match="wedge row missing"):
        A.SD.check_arrivals(comps)


def test_round_stair_on_the_structural_lane(run):
    s, c = run
    # RS-LD: 2C4 -> 289 1.150 x 283 -> 2C8 1.200 - column 374 corner 0.0275 = 1.3525 m2 x 0.16 (Checker 13:10 own)
    assert c["ST02-RS-LD"]["value"] == pytest.approx(0.216400, abs=1e-9)
    # RS-A on the lane 2CF -> 289 = 1.200 (Checker 13:10 own 0.377093)
    assert c["ST02-RS-A"]["value"] == pytest.approx(0.377093, abs=1e-6)
    lanes = {r["reading"]: r for r in s["retired_readings"] if "structural_lane_m" in r}
    ra, rl = lanes["RS-A width 1.25 (ARCH DIM 1250)"], lanes["RS-LD 1.25 x 1.15"]
    assert ra["accepted"] is False and ra["overlap_width_m"] == pytest.approx(0.05)
    assert ra["overlap_with_slab_m3"] == pytest.approx(0.015712, abs=1e-6)
    assert rl["accepted"] is False and rl["overlap_with_slab_m3"] == pytest.approx(0.0092, abs=1e-9)


def test_e1_source_names_five_riser_lines(run):
    _, c = run
    src = c["ST03-E1-STEPS"]["source"]
    assert "5 riser lines 18A / 189 / 188 / 17A / 179" in src and "4 lines" not in src
