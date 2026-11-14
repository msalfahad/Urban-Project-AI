"""R-T788-4 (Checker F-V788-1) on a synthetic villa (not Alsenan): doors are barriers for the outdoor ray test.

Plan (m): room 4 x 4 at x 0..4; west hall x -3..0 and east lobby x 4..7, both 4 deep. Door gaps 0.90 wide centred on
y = 2.00 in the four walls x = -3, 0, 4, 7 (two interior doors, two exterior doors, all on one axis). Clip piece = the
room inside its wall faces, representative point (2, 2). Rays at 0 and 180 deg pass all four gaps (2 escapes); the ray
at 22.5 deg meets x = 4 at y = 2 + 2 tan 22.5 = 2.83 > 2.45 (wall), so exactly 2 rays escape.
"""
import importlib.util, pathlib, pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, box

_P = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t799/t799_rules.py"
_s = importlib.util.spec_from_file_location("t799_rules", _P)
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)

G0, G1 = 1.55, 2.45                                   # door gap, 0.90 wide


def walls_with_gaps():
    out = []
    for x in (-3, 0, 4, 7):                           # the four walls carrying a door
        out += [LineString([(x, 0), (x, G0)]), LineString([(x, G1), (x, 4)])]
    out += [LineString([(-3, 0), (7, 0)]), LineString([(-3, 4), (7, 4)])]   # south / north walls
    return out


DOORS = [LineString([(x, G0), (x, G1)]) for x in (-3, 0, 4, 7)]             # closing chords of the 4 door gaps
ROOM = box(0.1, 0.1, 3.9, 3.9)


def test_defect_reproduced_r3_drops_the_indoor_room():
    p = ROOM.representative_point()
    assert (round(p.x, 3), round(p.y, 3)) == (2.0, 2.0)
    assert R.R3.is_outdoor(ROOM, walls_with_gaps()) is True      # R-T788-3: 2 escapes through aligned door gaps


def test_adverse_aligned_door_gaps_stay_indoor():
    assert R.is_outdoor_v4(ROOM, walls_with_gaps(), DOORS) is False


@pytest.mark.parametrize("tf", [lambda g: scale(g, -1, 1, origin=(0, 0)),     # mirror
                                lambda g: rotate(g, 90, origin=(0, 0))])      # rotation (rays at 90 / 270)
def test_adverse_mirror_rotation(tf):
    w, d, r = [tf(g) for g in walls_with_gaps()], [tf(g) for g in DOORS], tf(ROOM)
    assert R.R3.is_outdoor(r, w) is True
    assert R.is_outdoor_v4(r, w, d) is False


def test_normal_yard_piece_stays_outdoor():
    yard = box(10, 10, 12, 12)                        # beyond the east lobby, open on every side
    assert R.is_outdoor_v4(yard, walls_with_gaps(), DOORS) is True


def test_normal_doorless_openings_unchanged():
    # no door in any gap (open archways): the barrier set is R-T788-3's, the result is R-T788-3's
    assert R.is_outdoor_v4(ROOM, walls_with_gaps(), []) == R.R3.is_outdoor(ROOM, walls_with_gaps())


def test_split_moves_piece_only_by_doors():
    face, region = box(-3, 0, 7, 4), box(0, 0, 4, 4)
    ind3, out3 = R.R3.split_outdoor(face, region, walls_with_gaps())
    ind4, out4 = R.split_outdoor_v4(face, region, walls_with_gaps(), DOORS)
    assert len(out3) == 1 and out4 == [] and ind4.area == pytest.approx(16.0)


def test_adverse_doors_not_read_is_held():
    with pytest.raises(ValueError):
        R.is_outdoor_v4(ROOM, walls_with_gaps(), None)
    with pytest.raises(ValueError):
        R.is_outdoor_v4(ROOM, [], DOORS[:0])          # no barrier at all: R-T788-3 HELD kept
