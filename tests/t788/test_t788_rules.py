"""R-T788-1 / -2 on a synthetic villa (not Alsenan): cornice runs of open-plan zones, hand-calculated."""
import importlib.util, pathlib, pytest
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon, box

_P = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t788/t788_rules.py"
_s = importlib.util.spec_from_file_location("t788_rules", _P)
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)

# open plan: hall 8 x 6 with an open kitchen 3 x 3 on its east side, flush with the south wall
# L-shape perimeter 11 + 3 + 3 + 3 + 8 + 6 = 34.00 m; kitchen walls 3 + 3 + 3 = 9.00; hall walls 34 - 9 = 25.00
FACE = Polygon([(0, 0), (11, 0), (11, 3), (8, 3), (8, 6), (0, 6)])
KIT = box(8, 0, 11, 3)


def test_partition_hand_calc():
    p = R.partition_perimeter(FACE, {"KITCHEN": KIT}, "HALL")
    assert p["KITCHEN"] == pytest.approx(9.0, abs=0.01)
    assert p["HALL"] == pytest.approx(25.0, abs=0.01)
    assert sum(p.values()) == pytest.approx(FACE.length, abs=0.01)


def test_cornice_open_side_not_counted_door_gap_counted():
    p = R.partition_perimeter(FACE, {"KITCHEN": KIT}, "HALL")
    # the 3.00 m kitchen / hall line has no wall; a 0.90 m door gap cut in a wall line carries the run over the head
    hall = R.cornice_run([(p["HALL"], "WALL"), (3.0, "OPEN_SIDE"), (0.90, "OPENING")], True)
    kit = R.cornice_run([(p["KITCHEN"], "WALL"), (3.0, "OPEN_SIDE")], True)
    assert hall == pytest.approx(25.90, abs=0.01) and kit == pytest.approx(9.0, abs=0.01)


@pytest.mark.parametrize("tf", [lambda g: scale(g, -1, 1, origin=(0, 0)),           # mirror
                                lambda g: rotate(g, 90, origin=(0, 0)),             # rotation
                                lambda g: rotate(g, 33.3, origin=(5, 5))])          # skew angle
def test_partition_mirror_rotation(tf):
    p = R.partition_perimeter(tf(FACE), {"KITCHEN": tf(KIT)}, "HALL")
    assert p["KITCHEN"] == pytest.approx(9.0, abs=0.02) and p["HALL"] == pytest.approx(25.0, abs=0.02)


def test_adverse_sliver_region_counted_once():
    # a clip box that reaches 0.2 m past the south wall (the wall body leaks in the plan face) never double counts
    p = R.partition_perimeter(FACE, {"KITCHEN": box(8, -0.2, 11, 3)}, "HALL")
    assert sum(p.values()) == pytest.approx(34.0, abs=0.01)


def test_adverse_units_and_missing():
    with pytest.raises(ValueError):
        R.partition_perimeter(scale(FACE, 1000, 1000, origin=(0, 0)), {"KITCHEN": KIT}, "HALL")   # mm
    with pytest.raises(ValueError):
        R.cornice_run([(25000.0, "WALL")], True)                     # mm edge
    with pytest.raises(ValueError):
        R.cornice_run([(25.0, "WALL")], None)                        # ceiling type unknown: HELD, never 0
    with pytest.raises(ValueError):
        R.cornice_run([(None, "WALL")], True)
    with pytest.raises(ValueError):
        R.cornice_run([(2.0, "CURTAIN")], True)
    with pytest.raises(ValueError):
        R.cornice_run([], True)


def test_no_decor_ceiling_is_not_applicable():
    # an open stair well under a sloped soffit carries no run (stated NOT_APPLICABLE by the caller)
    assert R.cornice_run([], False) == 0.0


def test_lobby_and_shaft_box_one_ceiling():
    # 2F lobby 4.50 x 1.95 beside a stair box 2.50 x 5.20 under one roof slab: one ceiling, run = outer walls only
    face = Polygon([(0, 0), (2.5, 0), (2.5, 3.25), (4.5, 3.25), (4.5, 5.2), (0, 5.2)])
    p = R.partition_perimeter(face, {"BOX": box(0, 0, 2.5, 5.2)}, "LOBBY")
    run = R.cornice_run([(p["LOBBY"], "WALL"), (p["BOX"], "WALL")], True)
    assert run == pytest.approx(2 * (4.5 + 5.2), abs=0.01)           # orthogonal L = its bounding rectangle
