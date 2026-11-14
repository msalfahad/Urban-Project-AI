"""R-T788-3 on a synthetic villa (not Alsenan): only the room side counts; an outdoor pocket in a clip adds 0."""
import importlib.util, math, pathlib, pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, MultiPolygon, Polygon, box

_P = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t788/t788_rules.py"
_s = importlib.util.spec_from_file_location("t788_rules", _P)
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)

# hall 10 x 8 with a chamfered NE corner of glazing: inner glazing face (10,6)-(8,8), outer face 0.10 m further out,
# (10,6.141)-(8.141,8); the triangle between the outer glazing and the clip corner (10,8) is OUTDOORS (open to the yard)
ROOM = Polygon([(0, 0), (10, 0), (10, 6), (8, 8), (0, 8)])
# outer wall faces 0.20 m outside the clip (wall body); the walls stop at the glazing ends
OUTLINE = Polygon([(-0.2, -0.2), (10.2, -0.2), (10.2, 6.141), (10, 6.141), (8.141, 8), (8.141, 8.2), (-0.2, 8.2)])
YARD = box(-5, -5, 15, 13).difference(OUTLINE)            # the plan face that leaks to the yard
CLIP = box(0, 0, 10, 8)                                    # zone cut region drawn to the wall lines
BARRIERS = [LineString([(0, 0), (10, 0), (10, 6)]), LineString([(8, 8), (0, 8), (0, 0)]),
            LineString([(10, 6), (8, 8)]), LineString([(10, 6.141), (8.141, 8)]),
            LineString([(10, 6), (10, 6.141)]), LineString([(8, 8), (8.141, 8)]),
            LineString([(10, 6.141), (10.2, 6.141), (10.2, -0.2), (-0.2, -0.2), (-0.2, 8.2), (8.141, 8.2), (8.141, 8)])]
ROOM_RUN = 10 + 6 + math.hypot(2, 2) + 8 + 8               # 34.828: inner faces only
CUT = 8 - 6.141                                            # 1.859: each clip cut bounding the pocket


def _run(face, clip, bars):
    _, pockets = R.split_outdoor(face, clip, bars)
    regs = {f"OUT-{i}": q for i, q in enumerate(pockets)}
    regs["ROOM"] = clip
    p = R.partition_perimeter(face, regs, "YARD")
    return p, pockets


def test_normal_bay_inner_face_only():
    # closed room (no leak): no pocket, run = inner faces incl. the glazing once
    p, pockets = _run(ROOM, CLIP, BARRIERS)
    assert pockets == [] and p["ROOM"] == pytest.approx(ROOM_RUN, abs=0.01)


def test_adverse_clip_pocket_beyond_glazing_adds_zero():
    face = MultiPolygon([ROOM, YARD])
    p, pockets = _run(face, CLIP, BARRIERS)
    assert len(pockets) == 1 and pockets[0].area == pytest.approx(CUT * CUT / 2, abs=0.01)
    assert p["ROOM"] == pytest.approx(ROOM_RUN, abs=0.01)                 # outer glazing face not counted
    assert p["OUT-0"] == pytest.approx(math.hypot(CUT, CUT), abs=0.02)   # outer glazing face goes to the pocket
    run = R.cornice_run([(p["ROOM"], "WALL"), (CUT, "OPEN_SIDE"), (CUT, "OPEN_SIDE")], True)
    assert run == pytest.approx(ROOM_RUN, abs=0.01)                       # r1 error: + 2.629 + 2 x 1.859


@pytest.mark.parametrize("tf", [lambda g: scale(g, -1, 1, origin=(0, 0)), lambda g: rotate(g, 37.0, origin=(3, 2))])
def test_adverse_mirror_rotation(tf):
    p, pockets = _run(MultiPolygon([tf(ROOM), tf(YARD)]), tf(CLIP), [tf(b) for b in BARRIERS])
    assert len(pockets) == 1 and p["ROOM"] == pytest.approx(ROOM_RUN, abs=0.02)


def test_adverse_no_barriers_is_held():
    with pytest.raises(ValueError):
        R.split_outdoor(MultiPolygon([ROOM, YARD]), CLIP, [])
