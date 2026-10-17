"""Phase 2B-5 finding D-D2 (the room-reader benchmark, case B10): an arc-walled room through the BOQ.

B10 is a 4.00 x 3.00 m bathroom whose east wall is a circular arc (chord 3.00 m, rise 0.50 m, radius 2.50 m), one
0.80 m door. Hand truth (bench_cases.py; no engine value): floor 13.021882 m2 = 12 + 2.5^2 (2t - sin 2t) / 2 with
t = asin(0.6); room boundary 14.217506 m = 11 + 2.5 x 2t; wet-room upturn (boundary - door) x 0.20 = 2.683501 m2;
wall run along the room face (the engine's convention, as in B01: 14.0 m) 14.217506 m gross, 13.417506 m net.

What is asserted:
    exact      every area-based line (floor tile, ceiling, waterproofing floor) and the upturn - the engine's area
               and boundary length follow the arc
    as found   (D-D2, a defect: when it is corrected these assertions are to be replaced by the truth above)
               - the room's polygon / rect is the chord rectangle 4.00 x 3.00 m
               - the curved wall band is missing from the wall run: 11.0 m gross, 10.2 m net
               - the membrane cutting plan is laid on the chord rectangle: the same five 3.00 m floor strips as the
                 straight-walled B01, while its net is 13.021882 m2 (the 1.02 m2 segment has no planned piece)
Both ARCH_TAKEOFF_V2.5 and V2.6 (the defect is not method-specific)."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b5_bench"))

pytest.importorskip("ezdxf")

DECLARED = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")
T = math.asin(0.6)
AREA = 12.0 + 2.5 ** 2 * (2 * T - math.sin(2 * T)) / 2
BOUNDARY = 11.0 + 2.5 * 2 * T


def _run(case_id, tmp, method):
    import bench_cases as BC
    import bench_drawings as BD
    dxf = Path(BD.dxf(BC.BY_ID[case_id], tmp / f"{case_id}.dxf"))
    out = tmp / f"{case_id}_{method[-3:]}"
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m9.py"), "arch", "--drawings", str(dxf),
                        "--out", str(out), "--method", method, "--layer-roles", *DECLARED],
                       capture_output=True, text=True, cwd=str(tmp))
    assert r.returncode == 0, r.stderr[-2000:]
    lines = {}
    for x in csv.DictReader((out / "BOQ_LINES.csv").open(encoding="utf-8")):
        lines.setdefault(x["item_code"], []).append(x)
    room = json.loads((out / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"][0]
    plan = json.loads((out / "MEMBRANE_CUTTING_PLAN.json").read_text(encoding="utf-8"))["systems"][0]
    return lines, room, plan


@pytest.fixture(scope="module", params=["ARCH_TAKEOFF_V2.5", "ARCH_TAKEOFF_V2.6"])
def runs(request, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("curved")
    return _run("B10", tmp, request.param), _run("B01", tmp, request.param)


def _net(lines, code):
    return [float(x["measured_net"]) for x in lines[code]]


def test_the_hand_truth():
    assert abs(AREA - 13.021881929958) < 1e-9 and abs(BOUNDARY - 14.217505543966) < 1e-9


def test_area_and_boundary_lines_are_exact(runs):
    (lines, room, _), _ = runs
    assert abs(room["area_m2"] - AREA) < 1e-6 and abs(room["perimeter_lm"] - BOUNDARY) < 1e-6
    for code in ("FIN.FLOOR.WET_TILE", "FIN.CEILING", "FIN.WP.FLOOR"):
        assert [round(v, 6) for v in _net(lines, code)] == [round(AREA, 6)], code
    assert [round(v, 6) for v in _net(lines, "FIN.WP.WALL_UPTURN")] == [round((BOUNDARY - 0.8) * 0.2, 6)]


def test_d_d2_the_polygon_is_the_chord(runs):
    (_, room, _), _ = runs
    assert room["rect"] == pytest.approx([4.0, 3.0]) and room["dims"] == "4.00 x 3.00 m"
    xs = [p[0] for p in room["polygon_m"]]
    assert max(xs) == pytest.approx(4.2)                         # the arc reaches x = 4.70 m; the polygon stops at 4.20


def test_d_d2_the_curved_wall_is_missing_from_the_wall_run(runs):
    (lines, _, _), (b01, _, _) = runs
    run = lines["ARCH.WALL_RUN"][0]
    assert (float(run["gross"]), float(run["measured_net"])) == (11.0, 10.2)     # truth 14.217506 / 13.417506
    assert float(b01["ARCH.WALL_RUN"][0]["gross"]) == 14.0                        # the straight east wall is counted


def test_d_d2_the_membrane_plan_is_laid_on_the_chord(runs):
    (_, _, plan), (_, _, plan01) = runs
    strips = lambda p: [x["length_m"] for c in p["cutting_plan"] for x in c["pieces"]          # noqa: E731
                        if x["for"].startswith("floor strip")]
    assert strips(plan) == strips(plan01) == [3.0] * 5
    assert plan["net_m2"] == pytest.approx(AREA, abs=1e-6) and plan01["net_m2"] == pytest.approx(12.0)
