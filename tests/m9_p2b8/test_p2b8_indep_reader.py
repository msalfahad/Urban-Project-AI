"""Phase 2B-8: the independent drawing reader (tools/indep_reader) against hand truth. The reader is the second reading
that tools/arch_change_verify checks a BOQ change against; it is tested here on its own, without any engine output:
every truth below is derived by hand from the fixture coordinates (tests/m9_p2b6 / p2b7 / p2b8 docstrings).

    faces          CROSSING bath 1.677 x 3.00 = 5.031 m2 (perimeter 9.354), bedroom 2.173 x 3.00 = 6.519 m2 (10.346);
                   PLAIN bath 4.00 x 3.00 = 12.00 m2 (14.00); the W.C. lobby 3.40 x 3.00 = 10.20 m2 (12.80);
                   B10 12.00 + the circular segment 3.125 x (1.287002 - 0.96) = 13.021882 m2
    openings       door jamb spans 0.80 (CROSSING, PLAIN), 1.60 (DOUBLE), 0.80 + 1.00 (W.C. plan); window 0.60
    arc census     B10: 2.60 x 1.287002 = 3.346206 m; a both-face stretch under 0.30 m is a stub, listed apart
    fixtures       the basin lobby: one WASH insert; the loose W.C. on the sanitary layer: its lines, no insert
The reader imports no engine module."""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

ezdxf = pytest.importorskip("ezdxf")
pytest.importorskip("shapely")

import indep_reader as IR                                     # noqa: E402
import p2b8_fixtures as F                                     # noqa: E402

ROLES = {"A-WALL": "WALL", "A-COL": "COLUMN", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR"}


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_indep")


def _rooms(D, lo=1.0, hi=80.0):
    return sorted((round(f.area, 6), round(f.exterior.length, 6)) for f in D.faces() if lo <= f.area <= hi)


@pytest.mark.parametrize("plan,seeds", [
    ("CROSSING", [((1.0, 1.7), 5.031, 9.354), ((3.0, 1.7), 6.519, 10.346)]),
    ("PLAIN", [((2.0, 1.7), 12.0, 14.0)]),
])
def test_door_plan_faces(work, plan, seeds):
    D = IR.Drawing(F.door_plan(work / f"{plan}.dxf", plan), roles=ROLES)
    for seed, area, perim in seeds:
        f = D.face_at(seed)
        assert abs(f["area_m2"] - area) < 1e-6 and abs(f["perimeter_m"] - perim) < 1e-6 and f["holes"] == 0


def test_lobby_face_and_fixture_census(work):
    D = IR.Drawing(F.wc_plan(work / "WC_BASIN.dxf", "BASIN"), roles=ROLES)
    lob = D.face_at((4.0, 1.5))
    assert abs(lob["area_m2"] - 10.2) < 1e-6 and abs(lob["perimeter_m"] - 12.8) < 1e-6
    assert D.fixture_census(lob["polygon"]) == {"basins": 1, "water_closets": 0, "showers_baths": 0,
                                                "sanitary_layer_lines": 0}
    wc = D.face_at((1.0, 2.0))
    assert abs(wc["area_m2"] - 6.0) < 1e-6
    assert D.fixture_census(wc["polygon"])["basins"] == 0


def test_loose_sanitary_linework_is_counted_not_named(work):
    """EXPLODED: the W.C. drawn as loose lines on the sanitary layer - a cistern polyline (4 segments) and an ellipse
    bowl: 5 pieces inside the lobby, and no water-closet insert (the census counts what is drawn, never infers)."""
    D = IR.Drawing(F.wc_plan(work / "WC_EXPLODED.dxf", "EXPLODED"), roles=ROLES)
    c = D.fixture_census(D.face_at((4.0, 1.5))["polygon"])
    assert c["basins"] == 1 and c["water_closets"] == 0 and c["sanitary_layer_lines"] == 5


def test_an_anonymous_block_names_nothing(work):
    D = IR.Drawing(F.wc_plan(work / "WC_ANON.dxf", "ANON_BLOCK"), roles=ROLES)
    c = D.fixture_census(D.face_at((4.0, 1.5))["polygon"])
    assert c == {"basins": 1, "water_closets": 0, "showers_baths": 0, "sanitary_layer_lines": 0}


def test_opening_widths(work):
    D = IR.Drawing(F.door_plan(work / "CROSSING.dxf", "CROSSING"), roles=ROLES)
    assert [(round(d["width_m"], 6), d["wall_t_m"]) for d in D.doors()] == [(0.8, 0.2)]
    assert [round(w["width_m"], 6) for w in D.windows()] == [0.6]
    D2 = IR.Drawing(F.door_plan(work / "DOUBLE.dxf", "DOUBLE"), roles=ROLES)
    assert [round(d["width_m"], 6) for d in D2.doors()] == [1.6]
    D3 = IR.Drawing(F.wc_plan(work / "WC_B2.dxf", "BASIN"), roles=ROLES)
    assert sorted(round(d["width_m"], 6) for d in D3.doors()) == [0.8, 1.0]


def test_openings_on_a_face(work):
    """the PLAIN bath: its 0.80 m door and its 0.60 m window lie on its boundary; no closure is left uncovered."""
    D = IR.Drawing(F.door_plan(work / "PLAIN.dxf", "PLAIN"), roles=ROLES)
    ops, free = D.openings_on(D.face_at((2.0, 1.7)))
    assert sorted((o["kind"], round(o["width_m"], 6)) for o in ops) == [("DOOR", 0.8), ("WINDOW", 0.6)]
    assert free < 1e-4


def test_curved_room_and_arc_census(work):
    D = IR.Drawing(F.F7.arc_room(work / "B10.dxf"), roles=ROLES)
    f = D.face_at((2.0, 1.7))
    truth = 12.0 + 2.5 ** 2 / 2 * (2 * math.asin(0.6) - math.sin(2 * math.asin(0.6)))
    assert abs(f["area_m2"] - truth) < 1e-4
    ac = D.arc_census()
    assert len(ac["bands"]) == 1 and abs(ac["mid_lm"] - 2.6 * 2 * math.asin(0.6)) < 1e-6
    assert ac["short_stubs"] == []


def test_short_curved_stubs_are_listed_apart(work):
    """two concentric wall arcs 0.20 m apart over 0.10 rad on r 1.00 m: both faces over 0.10 m < 0.30 m - a stub,
    listed apart (1.10 x 0.10 = 0.11 m on the mid radius), never in the band length."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    for r in (1.0, 1.2):
        msp.add_arc((0, 0), r, 0, math.degrees(0.10), dxfattribs={"layer": "A-WALL"})
    p = work / "STUB.dxf"
    doc.saveas(str(p))
    ac = IR.Drawing(p, roles=ROLES).arc_census()
    assert ac["bands"] == [] and ac["mid_lm"] == 0 and abs(ac["short_stubs_mid_lm"] - 0.11) < 1e-6


@pytest.mark.parametrize("transform", ["rot30", "mirror", "metres"])
def test_faces_are_invariant(work, transform):
    src = F.door_plan(work / "CROSSING_T.dxf", "CROSSING")
    base = _rooms(IR.Drawing(src, roles=ROLES))
    moved = _rooms(IR.Drawing(F.variant(src, work / f"CROSSING_{transform}.dxf", transform), roles=ROLES))
    assert len(base) == len(moved) and all(abs(a[0] - b[0]) < 1e-5 and abs(a[1] - b[1]) < 1e-5
                                           for a, b in zip(base, moved))


def test_layer_zero_takes_the_insert_layer(work):
    """B10's door is a block whose lines are on layer 0, inserted on the door layer: they read as door pieces."""
    D = IR.Drawing(F.F7.arc_room(work / "B10_L0.dxf"), roles=ROLES)
    door = D.pieces(role="DOOR")
    assert door and all(p["insert_path"] for p in door)


def test_roles_from_layer_names():
    assert [IR.role_of_name(x) for x in ("A-WALL", "S-COL", "A-GLAZ", "WIN-1", "A-DOOR", "A-FURN")] == \
        ["WALL", "COLUMN", "WINDOW", "WINDOW", "DOOR", None]


def test_the_reader_imports_no_engine_module():
    src = (ROOT / "tools" / "indep_reader.py").read_text(encoding="utf-8")
    assert "from engine" not in src and "import engine" not in src
    code = ("import sys; sys.path.insert(0, %r); import indep_reader; "
            "print(sorted(m for m in sys.modules if m.startswith('engine')))" % str(ROOT / "tools"))
    r = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "[]", r.stdout + r.stderr
