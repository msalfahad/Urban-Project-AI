"""t788_zone_pieces.zone_pieces on a synthetic plan (not Alsenan): every boundary piece goes to one drawn entity or
to the nearest door closure, and the pieces add up to the R-T788-2 partition. Hand-calculated."""
import importlib.util, pathlib, sys
import pytest
from shapely.geometry import LineString, Point, Polygon, box

_D = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t788"
sys.path.insert(0, str(_D))
_s = importlib.util.spec_from_file_location("t788_zone_pieces", _D / "t788_zone_pieces.py")
Z = importlib.util.module_from_spec(_s); _s.loader.exec_module(Z)
R = Z.R

# hall 8 x 6 (+ open kitchen 3 x 3 on the east): walls drawn as lines, the north wall has a 1.00 m door (no line)
FACE = Polygon([(0, 0), (11, 0), (11, 3), (8, 3), (8, 6), (0, 6)])
KIT = box(8, 0, 11, 3)
ENTS = [("A1", "1", "LINE", LineString([(0, 0), (11, 0)])),      # south 11.00
        ("A2", "1", "LINE", LineString([(11, 0), (11, 3)])),     # east 3.00 (kitchen)
        ("A3", "1", "LINE", LineString([(11, 3), (8, 3)])),      # kitchen north 3.00
        ("A4", "1", "LINE", LineString([(8, 3), (8, 6)])),       # hall east 3.00
        ("A5", "1", "LINE", LineString([(8, 6), (4.5, 6)])),     # north, east of the door 3.50
        ("A6", "1", "LINE", LineString([(3.5, 6), (0, 6)])),     # north, west of the door 3.50
        ("A7", "S-COL.BON", "LWPOLYLINE", LineString([(0, 6), (0, 0)]))]  # west 6.00
DOORS = [("D9", "D100", Point(4.0, 6.1))]


def _sum(d):
    return {k[0]: round(v, 3) for k, v in d.items()}


def test_pieces_add_up_and_name_the_handles():
    out = Z.zone_pieces(FACE, {"KITCHEN": KIT}, "HALL", ENTS, DOORS)
    hall, kit = _sum(out["HALL"]), _sum(out["KITCHEN"])
    assert kit == pytest.approx({"A1": 3.0, "A2": 3.0, "A3": 3.0}, abs=0.01)
    assert hall["A1"] == pytest.approx(8.0, abs=0.01) and hall["A7"] == pytest.approx(6.0, abs=0.01)
    # the door gap goes to its INSERT: 1.00 - 2 x 0.035 (the end samples within NEAR_M stay with the jamb lines)
    assert hall["DOOR-CLOSURE D9"] == pytest.approx(0.93, abs=0.01)
    part = R.partition_perimeter(FACE, {"KITCHEN": KIT}, "HALL")
    assert sum(hall.values()) == pytest.approx(part["HALL"], abs=0.01)  # 25.00, hand: 34 - 9
    assert sum(kit.values()) == pytest.approx(part["KITCHEN"], abs=0.01)


def test_adverse_undrawn_edge_is_not_given_to_a_far_entity():
    # adverse: the west wall line is missing and no door is near: its 6.00 m is reported as a closure / plan-box piece
    out = Z.zone_pieces(FACE, {"KITCHEN": KIT}, "HALL", ENTS[:-1], DOORS)
    hall = _sum(out["HALL"])
    # 6.00 - 2 x 0.035: the corner samples within NEAR_M stay with the south / north lines
    assert hall["GAP-CLOSURE/PLAN-BOX"] == pytest.approx(5.93, abs=0.01)
    assert "A7" not in hall
