"""Phase 2B-9 invariance: worked example 1 (the sill window) and its floor-glazing variant under drawing transformations
that change no quantity - translated far from the origin, mirrored (every sheet about its own centre), drawn in
metres, entities reordered, and the plan alone turned 30 degrees (its schedule and section sheets stay upright, as on
a real drawing set). Every V2.8 height, opening and finish quantity must be the untransformed one. The metres
drawing runs with the reviewer's --units m: its only closed rectangles are the three sheet frames, which fit
centimetres better, and the admission rightly refuses to guess (UNITS_CONTRADICTED)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

pytest.importorskip("ezdxf")

import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402

F6 = F.F6

KINDS = ("translate", "mirror", "metres", "reorder", "plan_rot30")
ITEMS = (("FIN.PLASTER", "plaster"), ("FIN.PAINT", "paint"), ("FIN.SKIRTING", "skirting"),
         ("FIN.PLASTER", "window reveals"), ("FIN.PLASTER", "door jambs and head"),
         ("ARCH.WINDOW_REVEAL", "window sill surface"), ("FIN.FLOOR.PORCELAIN", "window floor strip"),
         ("FIN.FLOOR.PORCELAIN", "floor"))


def plan_rot30(src, dst, deg=30.0):
    """the plan sheet's entities turned about the room centre; the other sheets (schedule, section) untouched."""
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    c = (2200.0, 1700.0)
    m = Matrix44.chain(Matrix44.translate(-c[0], -c[1], 0), Matrix44.z_rotate(math.radians(deg)),
                       Matrix44.translate(c[0], c[1], 0))
    for e in list(msp):
        p = F6._ref(e)
        if e.dxf.layer in F6.SHEET or p is None or not (-6000 <= p[0] <= 24000 and -8000 <= p[1] <= 18000):
            continue
        e.transform(m)
    doc.saveas(str(dst))
    return dst


def summary(out):
    s = {}
    for code, el in ITEMS:
        got = R.all_of(out, code, el)
        got = [ln for ln in got if ln["physical_element"] == el] or got
        s[(code, el)] = tuple(sorted((round(ln["measured_net"], 4) if ln["measured_net"] is not None else None,
                                      ln["evidence_state"]) for ln in got))
    for o in R.opening_schedule(out):
        s[("OPENING", o["kind"])] = (o["class"], o["height"]["value_m"], o["sill"]["value_m"], o["area_m2"],
                                     o["height"]["governing"], o["sill"]["governing"])
    h = R.room_heights(out)
    s["HEIGHTS"] = tuple((tr, h[tr]["value_m"], h[tr]["governing"]) for tr in ("PLASTER", "PAINT"))
    return s


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    work = tmp_path_factory.mktemp("p2b9_inv")
    cache = {}

    def get(window, kind=None):
        if (window, kind) not in cache:
            base = work / f"e1_{window}.dxf"
            if not base.exists():
                F.example1(base, window=window)
            src = base
            if kind == "plan_rot30":
                src = plan_rot30(base, work / f"e1_{window}_{kind}.dxf")
            elif kind is not None:
                src = F.variant(base, work / f"e1_{window}_{kind}.dxf", kind)
            cache[(window, kind)] = summary(R.run(src, work / f"o_{window}_{kind}",
                                                  units="m" if kind == "metres" else None))
        return cache[(window, kind)]
    return get


@pytest.mark.parametrize("window", ("SILL", "FLOOR"))
@pytest.mark.parametrize("kind", KINDS)
def test_example1_is_invariant(runs, window, kind):
    base, got = runs(window), runs(window, kind)
    assert base[("FIN.PLASTER", "plaster")][0][0] is not None          # the baseline itself is measured
    assert got == base
