"""Phase 2B-7 Section 6 "no unexplained BOQ changes": every BOQ total that differs between ARCH_TAKEOFF_V2.6 and
V2.7 on one drawing is covered by a V2.7 correction record (tools/arch_v27_explain.py). The layer roles are declared
here, so no floor-wide LAYER_ROLE record can cover a difference: each one must be traced to the record of its own
correction (a door's jamb span, a frame, a curved band, an arc polygon, a wet-room decision, a merged sliver)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "m9_p2b5_bench"))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402
from tools import arch_v27_explain as X                       # noqa: E402

BENCH_ROLES = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_explained")


def _bench(work, case):
    import bench_cases as BC
    import bench_drawings as BD
    return BD.dxf(BC.BY_ID[case], work / f"{case}.dxf") or work / f"{case}.dxf"


def _crossing_rot37(work):
    base = F.door_plan(work / "CROSSING.dxf", "CROSSING")
    return F.variant(base, work / "CROSSING_rot37.dxf", "rot37_metres")


def _plain_rot37(work):
    """D-P6-06: PLAIN turned 37 degrees and drawn in metres - V2.6 adds a zero-length waterproofing termination."""
    base = F.door_plan(work / "PLAIN.dxf", "PLAIN")
    return F.variant(base, work / "PLAIN_rot37.dxf", "rot37_metres")


# drawing -> (roles, the correction kinds that must explain every difference, at least one difference expected)
CASES = {
    "CROSSING": (lambda w: F.door_plan(w / "CROSSING.dxf", "CROSSING"), F.ROLES, {"DOOR_OPENING"}, True),
    "CROSSING_rot37_metres": (_crossing_rot37, F.ROLES, {"DOOR_OPENING"}, True),
    "PLAIN_rot37_metres": (_plain_rot37, F.ROLES, {"SLIVER_MERGE"}, True),
    "B10": (lambda w: _bench(w, "B10"), BENCH_ROLES, {"ARC_POLYGON", "CURVED_WALL_BAND"}, True),
    "WC_BASIN": (lambda w: F.wc_plan(w / "WC_BASIN.dxf", "BASIN"), F.ROLES, {"WET_EVIDENCE"}, True),
    "WC_EXPLODED": (lambda w: F.wc_plan(w / "WC_EXPLODED.dxf", "EXPLODED"), F.ROLES, {"WET_EVIDENCE"}, False),
    "FRAMED_GROUP": (lambda w: F.framed_door_plan(w / "FR_GROUP.dxf", "GROUP"), F.ROLES, {"DOOR_FRAME"}, True),
    "FRAMED_NEST": (lambda w: F.framed_door_plan(w / "FR_NEST.dxf", "NEST"), F.ROLES, {"DOOR_FRAME"}, True),
    "OPEN_SIDE": (lambda w: F.door_plan(w / "OPEN_SIDE.dxf", "OPEN_SIDE"), F.ROLES, set(), False),
    "B01": (lambda w: _bench(w, "B01"), BENCH_ROLES, set(), False),
}


@pytest.mark.parametrize("name", list(CASES))
def test_every_v26_to_v27_difference_is_explained(work, name):
    make, roles, kinds, some = CASES[name]
    dxf = make(work)
    a = R.run(dxf, work / f"o_{name}_26", roles=roles, facts=True, method=R.V26)
    b = R.run(dxf, work / f"o_{name}_27", roles=roles, facts=True)
    rep = X.explain(a, b)
    bad = [d for d in rep["differences"] if d["state"] == "UNEXPLAINED"]
    assert not bad, bad[:5]
    assert bool(rep["differences"]) == some, rep["summary"]
    used = {k for d in rep["differences"] for k in d["kinds"]}
    assert used <= kinds, (used, kinds)
    assert all("LAYER_ROLE" not in d["kinds"] for d in rep["differences"])


def test_the_explainer_flags_an_unexplained_difference(work, tmp_path):
    """a V2.7 output with its correction log emptied: the same differences are now UNEXPLAINED (the explainer does
    not explain by default) and the CLI exits 1."""
    import json
    import shutil
    dxf = F.door_plan(work / "CROSSING_x.dxf", "CROSSING")
    a = R.run(dxf, work / "o_x_26", roles=F.ROLES, facts=True, method=R.V26)
    b = R.run(dxf, work / "o_x_27", roles=F.ROLES, facts=True)
    c = tmp_path / "o_x_27_nolog"
    shutil.copytree(b, c)
    p = c / "CORRECTIONS_V2_7.json"
    d = json.loads(p.read_text())
    d["corrections"] = []
    p.write_text(json.dumps(d))
    rep = X.explain(a, c)
    assert rep["differences"] and all(x["state"] == "UNEXPLAINED" for x in rep["differences"])
    assert X.main(["--before", str(a), "--after", str(c)]) == 1
