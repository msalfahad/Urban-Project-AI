"""R-T790-1 .. 3 on a synthetic villa (not Alsenan): wall view lines, mesh-strip levels, strip on a piece, sharmat."""
import importlib.util, pathlib, pytest

_P = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t790/t790_rules.py"
_s = importlib.util.spec_from_file_location("t790_rules", _P)
R = importlib.util.module_from_spec(_s); _s.loader.exec_module(R)


def test_view_lines_equal_block_once():
    # wall group 25.00 m2 at t 0.20: panel 25.00 m2 (REFERENCE), volume 5.000 m3
    p, v = R.view_lines(25.0, "RELEASED", 0.20)
    assert p == 25.0 and v == pytest.approx(5.0)


def test_view_lines_held_block_stays_held_never_zero():
    assert R.view_lines(None, "HELD", 0.20) is None
    assert R.view_lines(None, "EXCLUDED", 0.40) is None


def test_view_lines_units_refused():
    with pytest.raises(ValueError):
        R.view_lines(25.0, "RELEASED", 200)      # mm read as m
    with pytest.raises(ValueError):
        R.view_lines(0.0, "RELEASED", 0.20)


def test_levels_black_and_white():
    # black module 0.20: top 3.00 -> 0.60, 1.20, 1.80, 2.40 (3.00 + joint not < 3.00)
    assert R.levels(3.00) == [0.6, 1.2, 1.8, 2.4]
    # white family A 0.25 + 0.001: top 2.50 -> 0.762, 1.515, 2.268
    assert R.levels(2.50, R.WHITE_A) == [0.762, 1.515, 2.268]


def test_levels_unknown_or_mm_refused():
    with pytest.raises(ValueError):
        R.levels(None)
    with pytest.raises(ValueError):
        R.levels(3000)


def test_strip_with_door_by_hand():
    # 6.00 m black wall, top 3.00, door 1.00 x 2.10, lintel 1.50 x 0.20:
    # levels 0.6 / 1.2 / 1.8 cut 1.00 -> 5.00 x 3; level 2.4 above lintel top 2.30 -> 6.00 => 21.00 m
    assert R.strip(6.0, 3.0, [(1.0, 0.0, 2.10, 1.50, 0.20)]) == pytest.approx(21.0)


def test_strip_lintel_band_cuts_lintel_length():
    # door head 2.30 -> level 2.4 inside the lintel band [2.30, 2.50): cut 1.50 => 5 x 3 + 4.5 = 19.50 m
    assert R.strip(6.0, 3.0, [(1.0, 0.0, 2.30, 1.50, 0.20)]) == pytest.approx(19.5)


def test_strip_mirror_same():
    a = R.strip(6.0, 3.0, [(1.0, 0.0, 2.10, 1.50, 0.20), (0.6, 0.9, 1.5, 1.2, 0.2)])
    b = R.strip(6.0, 3.0, [(0.6, 0.9, 1.5, 1.2, 0.2), (1.0, 0.0, 2.10, 1.50, 0.20)])
    assert a == pytest.approx(b)


def test_strip_adverse():
    with pytest.raises(ValueError):
        R.strip(0.8, 3.0, [(1.0, 0.0, 2.1, 1.5, 0.2)])      # opening longer than the piece
    with pytest.raises(ValueError):
        R.strip(6.0, 3.0, [(1.0, 0.0, 2.1, 0.8, 0.2)])      # lintel shorter than its opening
    with pytest.raises(ValueError):
        R.strip(None, 3.0)


def test_ties():
    assert R.ties(3.00) == 4 and R.ties(2.50, R.WHITE_A) == 3
