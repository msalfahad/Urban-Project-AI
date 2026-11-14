"""R-T795-1 / -2 on a synthetic villa (not Alsenan), hand-calculated."""
import csv, importlib.util, json, pathlib
import pytest

_D = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t795"
_s = importlib.util.spec_from_file_location("t795_rules", _D / "t795_rules.py")
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)

# synthetic: bath B1 and laundry L share door d1 (0.75 x 2.10 printed); L has d2 to a dry corridor (0.90, head not
# printed -> 2.20); kitchen K has a 1.20 arch printed 3.20 high (above the 3.00 tile top: jambs to 3.00, no head edge)
FACES = [{"room": "B1", "opening": "d1", "W": 0.75, "H": 2.10},
         {"room": "L", "opening": "d1", "W": 0.75, "H": 2.10},
         {"room": "L", "opening": "d2", "W": 0.90, "H": R.DEFAULT_DOOR_HEAD_M},
         {"room": "K", "opening": "a1", "W": 1.20, "H": 3.20}]


def test_one_face_hand_calc():
    assert R.door_edge_lm(0.80, 2.20, 3.00) == (5.2, 4.4, 0.8)          # 2 x 2.20 + 0.80


def test_villa_total_both_faces_and_tall_arch():
    # d1 twice: 2 x (4.20 + 0.75) = 9.90; d2: 4.40 + 0.90 = 5.30; a1: 2 x 3.00 + 0 = 6.00 -> 21.20 (jambs 8.40 + 4.40 + 6.00)
    tot, jambs, heads = R.faces_total(FACES)
    assert (tot, jambs, heads) == (pytest.approx(21.20), pytest.approx(18.80), pytest.approx(2.40))


def test_rotation_mirror_invariant():
    # the edge depends on W, H and the tile top only: a mirrored / rotated plan lists the same faces in another order
    assert R.faces_total(list(reversed(FACES))) == R.faces_total(FACES)


@pytest.mark.parametrize("w,h,t", [(None, 2.2, 3.0), (0.8, None, 3.0), (0.8, 2.2, None)])
def test_adverse_missing_value_is_held_never_zero(w, h, t):
    with pytest.raises(ValueError, match="HELD"):
        R.door_edge_lm(w, h, t)


def test_adverse_units_and_double_count():
    with pytest.raises(ValueError, match="metres"):
        R.door_edge_lm(800, 2200, 3000)                                  # millimetres read as metres
    with pytest.raises(ValueError, match="twice"):
        R.faces_total(FACES + [FACES[0]])


def test_range_to_point():
    assert R.range_to_point(6.124412, 6.124412, False) == 6.124412
    assert R.range_to_point(0.0, 0.23, True) == 0.23
    with pytest.raises(ValueError, match="HELD"):
        R.range_to_point(0.0, 0.23, False)                               # adverse: open range, drawing silent
    with pytest.raises(ValueError, match="HELD"):
        R.range_to_point(None, 0.23, True)


def test_alsenan_fix_rows_close_on_the_committed_faces():
    faces = [dict(r, W=float(r["W"]), H=float(r["H"])) for r in csv.DictReader(open(_D / "DOOR_FACES_T795.csv"))]
    fx = json.load(open(_D / "out/FIX_ROWS.json"))
    tot, jambs, heads = R.faces_total(faces)
    assert fx["rows"][0]["after"]["net"] == tot == pytest.approx(115.2)
    assert len(faces) == 22 and jambs == pytest.approx(22 * 4.40)
    assert fx["summary"]["held_ranges_after"] == 0
    assert all(r["after"]["class"] == "RELEASED" and r["after"]["net"] > 0 for r in fx["rows"])
