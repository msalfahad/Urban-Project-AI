"""Phase 2B-0: the V2.2 wall-finish and skirting lines (released, ranged and blocked alike) are invariant when the plan is
translated far from the origin, rotated at any angle, mirrored or redrawn in metres - on the Phase 2B-0 fixtures (a
multi-room passage, openings meeting at a corner, a frame on the room face, curtain glazing) and on the synthetic villa.
Runs below the plan-region split, as the Phase 2A metamorphic suite does (tests/m9_p2a/p2a_helpers.py)."""

from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m9_p2a"))

import p2a_helpers as H                                       # noqa: E402
import p2b0_fixtures as FX                                    # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import arch_plan as AP                     # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import robust_geometry as RG               # noqa: E402

LR = {"A-WALL": "WALL", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR", "A-THIN": "OTHER"}
CODES = ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE", "FIN.SKIRTING")
CASES = {
    "translate_1e7": (lambda p: (p[0] + 1e7, p[1] + 1e7), 1.0, False),
    "rotate_90": (H.rot(90.0), 1.0, False),
    "rotate_37_37": (H.rot(37.37), 1.0, False),
    "rotate_random_far": (H.rot(random.Random(9).uniform(0.0, 360.0), (3e5, -2e5)), 1.0, False),
    "mirror": (lambda p: (-p[0], p[1]), 1.0, True),
    "mm_to_m": (lambda p: (p[0] * 1e-3, p[1] * 1e-3), 1e-3, False),
}


def _regions(path):
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    E = UI.read(str(path))
    A = AI.read_arch(path, unit_m=E["unit_m"])
    E = dict(E, hatches=[dict(h, ring=h["rings"][0]) for h in A["hatches"] if h["rings"]], texts=A["texts"],
             inserts=A["inserts"], segments=E["segments"] + A["extra_segments"], arcs=E["arcs"] + A["extra_arcs"])
    P = AP.plan_regions(E, split="EMPTY_BANDS", frames_from_lines_fallback=True)
    out = {}
    for r in P["regions"]:
        b = r["box"]
        ents = AP.region_entities(E, b)
        eps = max(1e-3 / E["unit_m"], max(b[2] - b[0], b[3] - b[1]) * 1e-6)
        out[r["floor"]] = dict(ents, segments=[s for s in ents["segments"]
                                               if not AP._on_frame_side(s["a"], s["b"], b, eps)])
    return out, E["unit_m"]


def _finish_lines(ents, unit_m, floor, roles):
    g = RG.Geometry(unit_m)
    roles = roles or AP.layer_roles(ents, unit_m, tol="UNIT_RELATIVE", geom=g)["roles"]
    S = AR.spaces(ents, roles, unit_m, region_id="R", tol="UNIT_RELATIVE", geom=g, release_safety=True)
    M = AM.measure(S, floor=floor, project_id="P", revision_set_sha256="0" * 64, facts=FX.HEIGHT_FACTS, documents=[],
                   release_safety=True)
    out = Counter()
    for ln in M["lines"]:
        if ln["item_code"] in CODES:
            br = ln.get("bounded_range") or {}
            out[(ln["item_code"], ln["physical_element"], ln["evidence_state"],
                 None if ln.get("measured_net") is None else round(ln["measured_net"], 6),
                 (round(br["low"], 6), round(br["high"], 6)) if br else None)] += 1
    return out


@pytest.fixture(scope="module")
def plans(tmp_path_factory):
    d = tmp_path_factory.mktemp("p2b0_meta")
    fx = {"wide": (FX.open_plan(d / "wide.dxf", zone_x=6000), LR),
          "narrow": (FX.open_plan(d / "narrow.dxf", zone_x=11000), LR),
          "corner": (FX.corner_openings(d / "corner.dxf"), LR),
          "on_face": (FX.windows(d / "on_face.dxf", "ON_FACE"), LR),
          "curtain": (FX.windows(d / "curtain.dxf", "CURTAIN"), LR)}
    out = {k: (_regions(p), roles) for k, (p, roles) in fx.items()}
    regs, u = H.villa_regions(d)
    out["villa_1F"] = (({"1F": regs["1F"]}, u), None)           # 1F: no columns (F-9: rotated columns are lost)
    return out


def test_the_fixtures_carry_ranges_and_multi_room_passages(plans):
    states = Counter()
    for (regs, u), roles in plans.values():
        for floor, ents in regs.items():
            states.update(k[2] for k in _finish_lines(ents, u, floor, roles).elements())
    assert states["SOURCE_DERIVED"] and states["BOUNDED_EXPOSURE"] >= 3


@pytest.mark.parametrize("case", list(CASES))
def test_v2_2_finish_lines_are_invariant(plans, case):
    f, sc, mir = CASES[case]
    for name, ((regs, u), roles) in plans.items():
        for floor, ents in regs.items():
            base = _finish_lines(ents, u, floor, roles)
            got = _finish_lines(H.transform(ents, f, scale=sc, mirror=mir), u / sc, floor, roles)
            assert got == base, (name, floor, case, sorted((base - got).items())[:3], sorted((got - base).items())[:3])
