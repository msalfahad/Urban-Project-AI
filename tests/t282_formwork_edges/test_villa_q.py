"""T-282 villa Q (not Alsenan; hand values in research/agents_t282/formwork_t282.py check()): each member's side faces
closed on its carrier's drawn face per edge (R-FACE-CLOSE-1), a sub-mm column offset is the column's face
(R-FACE-SNAP-1), a band framing into a ring at two stations covers the arc between its edge hits (R-FACE-OWN-1), end
faces only at free ends (R-FACE-END-1). Normal and adverse cases; rotation and mirror give the same faces."""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t282"
sys.path.insert(0, str(HERE))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FT = _load("face_trace")
FW = _load("formwork_t282")

COL = {"C1": [(0, -50), (400, -50), (400, 350), (0, 350)]}


def _g2():
    return {"edges": {"A": ((3700, -300), (4600, 600)), "B": ((3912.132, -512.132), (4812.132, 387.868))},
            "width": 300.0, "spans": [(0.0, 1.0, "G2#1")],
            "ends": {"start": {"kind": "FREE_END", "carriers": []}, "end": {"kind": "FREE_END", "carriers": []}}}


def _g1(b_end=4300):
    return {"edges": {"A": ((400, 0), (4000, 0)), "B": ((400, 300), (b_end, 300))}, "width": 300.0,
            "spans": [(0.4, 4.0, "G1#1")],
            "ends": {"start": {"kind": "COLUMN", "carriers": ["C1"]},
                     "end": {"kind": "BEAM_JUNCTION", "carriers": ["G2"]}}}


def _xf(members, cols, f):
    """apply a point map f to every coordinate (rotation / mirror); stations are re-derived from the new geometry."""
    out = {}
    for k, m in members.items():
        e = {s: (f(*m["edges"][s][0]), f(*m["edges"][s][1])) for s in ("A", "B")}
        (a0, a1) = e["A"]
        L = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
        u = ((a1[0] - a0[0]) / L, (a1[1] - a0[1]) / L)
        old = m["edges"]["A"]
        L0 = math.hypot(old[1][0] - old[0][0], old[1][1] - old[0][1])
        u0 = ((old[1][0] - old[0][0]) / L0, (old[1][1] - old[0][1]) / L0)
        # station shift: the A start point keeps its station along the member
        s_old = (old[0][0] * u0[0] + old[0][1] * u0[1]) / 1000.0
        s_new = (a0[0] * u[0] + a0[1] * u[1]) / 1000.0
        spans = [(s0 - s_old + s_new, s1 - s_old + s_new, sid) for s0, s1, sid in m["spans"]]
        out[k] = dict(m, edges=e, spans=spans)
    return out, {k: [f(*p) for p in v] for k, v in cols.items()}


def test_hand_fixture():
    assert FW.check() is True


def test_oblique_carrier_each_edge_and_square_cut_refused():
    t = FT.trace({"G1": _g1(), "G2": _g2()}, COL)
    assert t["sides"][("G1#1", "A")] == pytest.approx(3.6, abs=1e-4)
    assert t["sides"][("G1#1", "B")] == pytest.approx(3.9, abs=1e-4)
    assert not [k for k in t["ends"] if k[0] == "G1#1"]                # no invented end face / earth pocket
    with pytest.raises(FT.Refused):
        FT.square_cut_refused(3.6, 3.9, 3.6, 3.6)                      # both sides billed at the shorter edge


@pytest.mark.parametrize("name,f", [
    ("rot30", lambda x, y: (x * math.cos(math.radians(30)) - y * math.sin(math.radians(30)),
                            x * math.sin(math.radians(30)) + y * math.cos(math.radians(30)))),
    ("mirror", lambda x, y: (-x, y)),
    ("offset", lambda x, y: (x + 123456.7, y - 98765.4)),
])
def test_rotation_mirror_offset_same_faces(name, f):
    mem, cols = _xf({"G1": _g1(), "G2": _g2()}, COL, f)
    t = FT.trace(mem, cols)
    assert t["sides"][("G1#1", "A")] == pytest.approx(3.6, abs=2e-4), name
    assert t["sides"][("G1#1", "B")] == pytest.approx(3.9, abs=2e-4), name


def test_short_line_closed_and_beyond_cap_held():
    t = FT.trace({"G1": _g1(4200), "G2": _g2()}, COL)
    assert t["sides"][("G1#1", "B")] == pytest.approx(3.9, abs=1e-4)
    assert [c["closed_m"] for c in t["closed"]] == [0.1]
    t3 = FT.trace({"G1": _g1(3600), "G2": _g2()}, COL)                # 0.700 short > 2 x 0.30: never invented
    assert t3["held"] and t3["held"][0]["side"] == "B"
    assert t3["sides"][("G1#1", "B")] < 3.9


def test_column_005mm_inside_band_edge_is_column_face():
    cols = dict(COL, C3=[(2000, -50), (2500, -50), (2500, 299.95), (2000, 299.95)])
    t = FT.trace({"G1": _g1(), "G2": _g2()}, cols)
    assert t["sides"][("G1#1", "B")] == pytest.approx(3.4, abs=1e-4)
    assert t["columns"]["C3"] == pytest.approx(1.1, abs=1e-4)
    tx = FT.trace({"G1": _g1(), "G2": _g2()}, cols, snap=0.01)       # adverse: no snap -> 0.5 m of false beam face
    assert tx["sides"][("G1#1", "B")] == pytest.approx(3.9, abs=1e-4)
    assert FT.snap_owner(0.052) == "COLUMN_FACE" and FT.snap_owner(1.5) == "TWO_FACES"
    for bad in (0.0, 5.0, 10.0):
        with pytest.raises(FT.Refused):
            FT.snap_owner(0.3, tol=bad)


def test_oblique_tee_width_on_carrier():
    assert FT.tee_width_on_carrier(0.30, 90.0) == pytest.approx(0.30)
    assert FT.tee_width_on_carrier(0.30, 45.0) == pytest.approx(0.424264, abs=1e-6)
    with pytest.raises(FT.Refused):
        FT.tee_width_on_carrier(0.30, 0.0)
