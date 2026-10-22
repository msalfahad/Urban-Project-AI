"""T-163 r2 (D-T163-1): formwork joint faces of columns (research/agents_t163/t163_formwork.py, research only).

Synthetic villa (not the development villa), hand values in the module's check() and check_r2_adverse() docstrings:
normal bay (sides 9.800, joints 0.560, edges 2.940 m2, plain / mirrored / mm, r1 and r2) and the adverse cases the
Checker's 12:05 rejection named: a beam narrower than the column face running THROUGH it flush with one face (1.767 m2),
a deeper oblique beam framing part of a face (1.215 m2), a column cut by a drafting diagonal (= uncut), a 20 mm break
sliver beyond a beam (held, not an outer face), and the stated-section joint (1.1325 m2 vs 1.3525 drawn; resized faces
with two open heights, stated < framing, square outline HELD). The r1 walk is asserted WRONG on each adverse case.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "research" / "agents_t163" / "t163_formwork.py"


def _load():
    spec = importlib.util.spec_from_file_location("t163_formwork", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_synthetic_bay_and_adverse_cases():
    _load().check()


def test_joint_through_flush_beam_r2_vs_r1():
    m = _load()
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    f = {"C.a": Polygon([(0, 0), (0, 0.25), (1.10, 0)]), "C.b": Polygon([(0, 0.25), (1.10, 0.25), (1.10, 0)]),
         "B1.w": box(-1.0, 0.05, 0, 0.25), "B1.e": box(1.10, 0.05, 2.10, 0.25), "SN": box(-1.0, 0.25, 2.10, 2.0),
         "SS": unary_union([box(-1.0, -2.0, 2.10, 0), box(-1.0, 0, 0, 0.05), box(1.10, 0, 2.10, 0.05)])}
    k = {"C.a": "COLUMN", "C.b": "COLUMN", "B1.w": "BEAM", "B1.e": "BEAM", "SN": "SLAB", "SS": "SLAB"}
    d = {"C.a": 0.85, "C.b": 0.85, "B1.w": 0.40, "B1.e": 0.40}
    t = {"SN": 0.16, "SS": 0.16}
    hand = 2 * 1.10 * 0.69 + 2 * (0.05 * 0.69 + 0.20 * 0.45)          # 1.767: the beam's own width only
    assert abs(m._r2_sums(f, k, d, t)[1] - hand) < 2e-3
    assert abs(m._r2_sums(f, k, d, t, "r1")[1] - hand) > 0.02           # the rejected r1 walk leaks past the wedge


def test_missing_depth_stays_held_never_zero():
    m = _load()
    c = dict(drawn="0.20x0.40", a=0.20, b=0.50, Dctrl="0.75")
    tr = {"S": dict(Ld=0.20, pieces=[("SLAB", "", 0.20, 0.59)]), "N": dict(Ld=0.20, pieces=[("SLAB", "", 0.20, 0.59)]),
          "W": dict(Ld=0.40, pieces=[("BEAM", "Bh", 0.40, None)]), "E": dict(Ld=0.40, pieces=[("SLAB", "", 0.40, 0.59)])}
    lo, hi, st, note = m.stated_joint(c, tr)
    assert st == m.HELD and hi > lo and note                            # W longer at the stated size, beam depth held
