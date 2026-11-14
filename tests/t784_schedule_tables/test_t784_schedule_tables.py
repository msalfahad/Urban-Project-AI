"""T-784 SCHEDULE_TABLES_V1: synthetic (non-Alsenan) schedule fixture, hand-calculated.

Column schedule (cm, levels in m):  C1 30 x 60, C2 25 x 50, C3 40 x 40, C4 20 x 40, C5 20 x 40; all 0.00 .. 3.60.
Plan (metres): C1 tagged twice + drawn a third time untagged (unique size) -> 3; C2 tagged on a 25 x 60 outline
(size conflict, counted, schedule section governs) -> 1; C4, C5 tagged once each; one untagged 20 x 40 outline fits
C4 and C5 -> AMBIGUOUS (not counted, designer list); C3 has no plan symbol -> HELD (None, never 0); tag C9 has no row.
Hand calc: C1 3 x 0.30 x 0.60 x 3.60 = 1.944; C2 0.25 x 0.50 x 3.60 = 0.450; C4 = C5 = 0.20 x 0.40 x 3.60 = 0.288;
total 2.970 m3.
"""

import math

import pytest

from engine.source import schedule_tables_v1 as ST

GRID = [["MARK", "B", "D", "FROM", "TO"],
        ["C1", "30", "60", "0.00", "3.60"],
        ["C2", "25", "50", "0.00", "3.60"],
        ["C3", "40", "40", "0.00", "3.60"],
        ["C4", "20", "40", "0.00", "3.60"],
        ["C5", "20", "40", "0.00", "3.60"]]


def _texts(grid, angle_deg=0.0, origin=(100.0, 50.0), pitch=(2.0, 0.8)):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            lx, ly = j * pitch[0], -i * pitch[1]
            out.append({"value": v, "x": origin[0] + lx * c - ly * s, "y": origin[1] + lx * s + ly * c,
                        "rotation": angle_deg})
    return out


def _box(i, cx, cy, a, b):
    return {"id": i, "cx": cx, "cy": cy, "a": a, "b": b}


OUTLINES = [_box("o1", 0, 0, 0.3, 0.6), _box("o2", 5, 0, 0.6, 0.3), _box("o3", 10, 0, 0.3, 0.6),
            _box("o4", 15, 0, 0.25, 0.60), _box("o5", 20, 0, 0.2, 0.4), _box("o6", 25, 0, 0.2, 0.4),
            _box("o7", 30, 0, 0.4, 0.2)]
TAGS = [{"mark": "C1", "x": 0.2, "y": 0.5}, {"mark": "C1", "x": 5.3, "y": 0.4}, {"mark": "C2", "x": 15.2, "y": 0.5},
        {"mark": "C4", "x": 20.2, "y": 0.5}, {"mark": "C5", "x": 25.2, "y": 0.5}, {"mark": "C9", "x": 40, "y": 40}]


def _run(angle=0.0, outlines=OUTLINES, tags=TAGS):
    T = ST.read_text_table(_texts(GRID, angle), row_tol=0.3, col_pad=0.2)
    B = ST.bind(T["rows"], tags, outlines, tol=1.0, size_tol=0.02)
    return T, B, ST.quantities(T["rows"], B)


def test_normal_hand_calc():
    T, B, Q = _run()
    assert [r["mark"] for r in T["rows"]] == ["C1", "C2", "C3", "C4", "C5"]
    assert T["units"]["COLUMN"]["unit_m"] == 0.01
    q = {l["mark"]: l for l in Q["lines"]}
    assert q["C1"]["count"] == 3 and q["C1"]["by_status"] == {"TAGGED": 2, "DRAWN_UNTAGGED": 1}
    assert q["C1"]["volume_m3"] == pytest.approx(1.944)
    assert q["C2"]["volume_m3"] == pytest.approx(0.45) and q["C2"]["by_status"] == {"TAGGED_SIZE_CONFLICT": 1}
    assert q["C4"]["volume_m3"] == pytest.approx(0.288) and q["C5"]["volume_m3"] == pytest.approx(0.288)
    assert Q["total_m3"] == pytest.approx(2.97)
    assert q["C1"]["h_basis"] == "LEVEL_RANGE"


def test_adverse_no_plan_symbol_is_held_never_zero():
    _, B, Q = _run()
    q = {l["mark"]: l for l in Q["lines"]}
    assert q["C3"]["count"] is None and q["C3"]["volume_m3"] is None and "C3" in Q["held_marks"]
    st = {(d["mark"], d["status"]) for d in B["designer"]}
    assert ("C3", "NO_PLAN_SYMBOL") in st and ("C9", "NOT_IN_SCHEDULE") in st and ("C2", "TAGGED_SIZE_CONFLICT") in st
    amb = [d for d in B["designer"] if d["status"] == "AMBIGUOUS_OUTLINE"]
    assert len(amb) == 1 and amb[0]["candidates"] == ["C4", "C5"]


@pytest.mark.parametrize("angle", [30.0, 90.0, -45.0, 180.0])
def test_adverse_rotated_table_reads_the_same(angle):
    T0, _, Q0 = _run(0.0)
    T1, _, Q1 = _run(angle)
    assert [(r["mark"], r["dims_m"]) for r in T1["rows"]] == [(r["mark"], r["dims_m"]) for r in T0["rows"]]
    assert Q1["total_m3"] == pytest.approx(Q0["total_m3"])


def test_adverse_mirrored_plan_same_counts():
    o = [dict(x, cx=-x["cx"]) for x in OUTLINES]
    t = [dict(x, x=-x["x"]) for x in TAGS]
    _, _, Q = _run(outlines=o, tags=t)
    assert Q["total_m3"] == pytest.approx(2.97)


def test_adverse_missing_height_held_until_caller_gives_it():
    grid = [r[:3] for r in GRID]
    T = ST.read_text_table(_texts(grid), row_tol=0.3)
    B = ST.bind(T["rows"], TAGS, OUTLINES, tol=1.0, size_tol=0.02)
    Q = ST.quantities(T["rows"], B)
    assert Q["total_m3"] == 0.0 and all(l["volume_m3"] is None for l in Q["lines"])
    Q2 = ST.quantities(T["rows"], B, height_m=3.6)
    assert Q2["total_m3"] == pytest.approx(2.97)
    assert {l["h_basis"] for l in Q2["lines"] if l["volume_m3"]} == {"CALLER_HEIGHT"}


def test_footing_table_mm_with_thickness_and_level_cell():
    grid = [["TYPE", "W", "L", "T"], ["F1", "1200", "1500", "400"], ["F2", "2000", "2000", "500"]]
    T = ST.read_text_table(_texts(grid, 12.0, pitch=(900.0, 400.0)), row_tol=120.0)
    assert T["units"]["FOOTING"]["unit_m"] == 0.001
    B = ST.bind(T["rows"], [{"mark": "C1/F1", "x": 0, "y": 0}],
                [_box("a", 50, 0, 1500, 1200), _box("b", 9000, 0, 1200, 1500)], tol=500, size_tol=0.02,
                unit_m=0.001)
    Q = ST.quantities(T["rows"], B)
    q = {l["mark"]: l for l in Q["lines"]}
    assert q["F1"]["count"] == 2 and q["F1"]["volume_m3"] == pytest.approx(2 * 1.2 * 1.5 * 0.4)
    assert q["F2"]["volume_m3"] is None
    assert ST._level_range("0.00 - 3.60") == (0.0, 3.6) and ST._level_range("-1.50 to +0.95") == (-1.5, 0.95)


def test_attribute_reader_rows_banded():
    sched = {"rows": [{"mark": "C1", "family": "COLUMN", "source": "INSERT 1", "dims_m": {},
                       "by_storey": {"GF": {"dims_m": {"W": 0.25, "H": 1.1}}, "FOUNDATION": {"dims_m": {"W": 0.3,
                                                                                                        "H": 1.1}}}},
                      {"mark": "F3", "family": "FOOTING", "source": "INSERT 2",
                       "dims_m": {"W": 1.6, "H": 1.4, "D": 0.3}, "by_storey": {}}]}
    gf = ST.rows_from_reader(sched, band="GF", families={"COLUMN"})
    assert gf == [{"mark": "C1", "family": "COLUMN", "dims_m": {"B": 0.25, "D": 1.1}, "level": None, "band": "GF",
                   "source": "INSERT 1"}]
    ft = ST.rows_from_reader(sched, families={"FOOTING"})
    assert ft[0]["dims_m"] == {"B": 1.6, "D": 1.4, "H": 0.3}


def test_carried_tags_count_outlines_only_and_offset():
    # an upper storey drawn 1000 to the left: tags carried from the setting-out plan
    up = [dict(o, cx=o["cx"] - 1000.0) for o in OUTLINES if o["id"] in ("o1", "o2", "o5")]
    off = ST.align_offset(OUTLINES, up, snap=0.5)
    assert off["dx"] == -1000.0 and off["dy"] == 0.0 and off["share"] == 1.0
    T = ST.read_text_table(_texts(GRID), row_tol=0.3)
    tags = [dict(t, x=t["x"] + off["dx"]) for t in TAGS]
    B = ST.bind(T["rows"], tags, up, tol=1.0, size_tol=0.02, carried=True)
    Q = ST.quantities(T["rows"], B)
    q = {l["mark"]: l for l in Q["lines"]}
    assert q["C1"]["count"] == 2 and q["C2"]["volume_m3"] is None and q["C4"]["count"] == 1
    assert not any(d["status"] in ("TAG_ONLY", "NOT_IN_SCHEDULE") for d in B["designer"])
    assert Q["total_m3"] == pytest.approx(2 * 0.648 + 0.288)


def test_adverse_offset_refused_when_plans_do_not_match():
    far = [_box("z1", 500, 500, 0.3, 0.6), _box("z2", 777, 123, 0.3, 0.6), _box("z3", 9, 999, 0.2, 0.4)]
    assert ST.align_offset(OUTLINES, far, snap=0.5, min_share=0.9) is None
    assert ST.align_offset([], far, snap=0.5) is None


def test_alsenan_research_output_reproduces_and_closes():
    import os
    import subprocess
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    r = subprocess.run([sys.executable, "-I", os.path.join(root, "research/agents_t784/schedule_first.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "CHECK OK" in r.stdout
    md = open(os.path.join(root, "research/agents_t784/out/SCHEDULE_FIRST.md")).read()
    assert md.count("| CLOSED |") == 4 and "| OPEN |" not in md
