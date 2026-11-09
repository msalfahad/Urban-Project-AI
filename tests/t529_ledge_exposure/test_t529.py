"""T-529: WP_APPLICABILITY_RULES_V2 exposure step (research/agents_t529/t529_exposure_v2.py, R-WP-APPL-EXPOSED-2a..e).
Synthetic villa "Q529" (not the training villa), hand calculations; adverse cases; then the development villa from
the private drawing (skipped when it is absent)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t529"))
from engine.source import wp_applicability_rules_v1 as W  # noqa: E402
import t529_exposure_v2 as V  # noqa: E402

S = "Q529 A-101 1F plan"

# ---- villa "Q529" (hand-drawn, metres): a 3.00 x 0.40 ledge, x 0 .. 3, y 0 .. 0.40; house wall along y = 0.40; end
# walls at x = 0 and x = 3; its front edge y = 0 is a void edge (open). A slab above covers x 0 .. 1.80 in plan.
# Hand: open-sky part 1.20 x 0.40 = 0.480 m2; covered part 1.80 x 0.40 = 0.720 m2; whole 1.200 m2.
LEDGE = [(0, 0), (3, 0), (3, 0.4), (0, 0.4)]
COVER = [(-0.5, -0.5), (1.8, -0.5), (1.8, 1.0), (-0.5, 1.0)]


def runs(front_covered="VOID_EDGE", front_open="VOID_EDGE", end_w="WALL", end_e="WALL", back="WALL"):
    return [{"run": "front_a", "kind": front_covered, "coords": [(0, 0), (1.8, 0)], "source": S},
            {"run": "front_b", "kind": front_open, "coords": [(1.8, 0), (3, 0)], "source": S},
            {"run": "end_e", "kind": end_e, "coords": [(3, 0), (3, 0.4)], "source": S},
            {"run": "back", "kind": back, "coords": [(3, 0.4), (0, 0.4)], "source": S},
            {"run": "end_w", "kind": end_w, "coords": [(0, 0.4), (0, 0)], "source": S}]


def surf(**kw):
    s = {"zone_id": "Q529-LEDGE", "outline": LEDGE, "boundary": runs(),
         "covers": [{"id": "1F slab over", "kind": "SLAB", "outline": COVER, "source": "Q529 A-102 2F plan"}]}
    s.update(kw)
    return s


def part(r, name):
    return [p for p in r["parts"] if p["part"] == name][0]


# ---- normal cases ---------------------------------------------------------------------------------------------------
def test_split_is_measured_and_a_covered_part_open_at_a_side_is_exposed():
    r = V.classify_surface(surf())
    assert r["open_m2"] == pytest.approx(0.48) and r["covered_m2"] == pytest.approx(0.72)
    assert part(r, "OPEN_SKY")["decision"] == V.EXPOSED and "2a" in part(r, "OPEN_SKY")["basis"]
    c = part(r, "COVERED")
    assert c["decision"] == V.EXPOSED and "2b" in c["basis"] and "UP-WP-ROOF-001" in c["basis"]
    assert c["open_sides_lm"] == pytest.approx(1.8 + 0.4, abs=2e-3)    # void edge under the cover + its interface
    assert r["membrane_m2"] == pytest.approx(1.2) and r["status"] == "MEASURED"


def test_acceptance_case_closed_covered_part_gives_the_open_part_only():
    # the covered 1.80 m part closed round: its front is a wall, a glazed screen with a drawn head on the cover line
    r = V.classify_surface(surf(boundary=runs(front_covered="WALL"),
                                screens=[{"id": "screen", "kind": "GLAZING", "coords": [(1.8, 0), (1.8, 0.4)],
                                          "head_drawn": True, "source": "Q529 section 1-1 head detail"}]))
    assert part(r, "COVERED")["decision"] == V.COVERED and "2c" in part(r, "COVERED")["basis"]
    assert r["membrane_m2"] == pytest.approx(0.48)                      # 1.20 x 0.40 by hand


def test_printed_detail_stopping_the_membrane_at_the_cover_line_governs():
    r = V.classify_surface(surf(detail={"extent": [(1.8, -1), (4, -1), (4, 1), (1.8, 1)],
                                        "source": "Q529 detail 7 membrane stop"}))
    assert r["membrane_m2"] == pytest.approx(0.48) and "2e" in r["basis"]
    assert V.classify_surface(surf(detail={"extent": "WHOLE", "source": "d"}))["membrane_m2"] == pytest.approx(1.2)
    assert V.classify_surface(surf(detail={"extent": "NONE", "source": "d"}))["membrane_m2"] == 0.0


def test_nothing_above_is_open_sky_and_closed_round_under_a_roof_is_not_applicable():
    r = V.classify_surface(surf(covers=[]))
    assert r["membrane_m2"] == pytest.approx(1.2) and r["covered_m2"] == 0.0
    whole = [(-1, -1), (4, -1), (4, 1), (-1, 1)]
    r2 = V.classify_surface(surf(boundary=runs(front_covered="WALL", front_open="WALL"),
                                 covers=[{"id": "roof", "kind": "ROOF", "outline": whole, "source": S}]))
    assert r2["membrane_m2"] == 0.0 and part(r2, "COVERED")["decision"] == V.COVERED
    assert V.v1_exposure(r2) == W.COVERED


def test_v1_rows_take_the_v2_exposure_unchanged():
    r = V.classify_surface(surf(covers=[{"id": "slab", "kind": "SLAB", "outline": [(-1, -1), (4, -1), (4, 1), (-1, 1)],
                                         "source": S}]))
    assert V.v1_exposure(r) == W.EXPOSED
    rows = W.component_rows({"zone_id": "Q529-LEDGE", "exposure": V.v1_exposure(r), "doors": 0,
                             "membrane_m2": r["membrane_m2"], "upturn_runs": [{"run": "back", "lm": 3.0, "kind": "WALL"}],
                             "void_edge_lm": 3.0, "outlet_printed": False})
    m = [x for x in rows if x["component"] == "FLAT_MEMBRANE"][0]
    u = [x for x in rows if x["component"] == "UPTURN"][0]
    assert m["status"] == W.MEASURED and m["qty"] == pytest.approx(1.2)
    assert u["status"] == W.MEASURED and u["qty"] == pytest.approx(0.6)          # 3.00 x 0.20 (UP-WP-003)
    with pytest.raises(ValueError):                                              # mixed decisions: split first
        V.v1_exposure(V.classify_surface(surf(boundary=runs(front_covered="WALL"),
                                              screens=[{"id": "s", "kind": "WALL", "coords": [(1.8, 0), (1.8, 0.4)],
                                                        "source": S}])))


# ---- adverse cases ----------------------------------------------------------------------------------------------------
def test_cover_outline_missing():
    r = V.classify_surface(surf(covers=None))                    # open at a side: exposed whichever way the cover runs
    assert r["membrane_m2"] == pytest.approx(1.2) and r["open_m2"] is None and r["covered_m2"] is None
    closed = V.classify_surface(surf(covers=None, boundary=runs(front_covered="WALL", front_open="WALL")))
    assert closed["status"] == "HELD" and closed["membrane_m2"] is None
    assert closed["held_bound_m2"] == pytest.approx(1.2)          # bound shown, never 0


def test_glazing_without_a_drawn_head_is_held():
    r = V.classify_surface(surf(boundary=runs(front_covered="WALL"),
                                screens=[{"id": "screen", "kind": "GLAZING", "coords": [(1.8, 0), (1.8, 0.4)],
                                          "head_drawn": None, "source": "Q529 plan only"}]))
    c = part(r, "COVERED")
    assert c["decision"] == V.HELD and "glazing without a drawn head" in c["held_reason"]
    assert r["membrane_m2"] is None and r["measured_part_m2"] == pytest.approx(0.48)
    assert r["held_bound_m2"] == pytest.approx(0.72) and r["status"] == "PART_HELD"
    g = V.classify_surface(surf(covers=[{"id": "skylight", "kind": "GLAZING", "outline": COVER, "source": S,
                                         "outline_drawn": False}]))
    assert g["status"] == "HELD" and g["held_bound_m2"] == pytest.approx(1.2)


def test_unknown_side_kind_without_an_open_side_is_held():
    r = V.classify_surface(surf(boundary=runs(front_covered="UNKNOWN"),
                                screens=[{"id": "s", "kind": "WALL", "coords": [(1.8, 0), (1.8, 0.4)], "source": S}]))
    assert part(r, "COVERED")["decision"] == V.HELD


def test_units_and_sources():
    mm = [(x * 1000, y * 1000) for x, y in LEDGE]
    r = V.classify_surface(surf(outline=mm, unit_m=0.001,
                                boundary=[dict(b, coords=[(x * 1000, y * 1000) for x, y in b["coords"]]) for b in runs()],
                                covers=[{"id": "c", "kind": "SLAB", "outline": [(x * 1000, y * 1000) for x, y in COVER],
                                         "source": S}]))
    assert r["membrane_m2"] == pytest.approx(1.2) and r["open_m2"] == pytest.approx(0.48)
    with pytest.raises(ValueError, match="units"):
        V.classify_surface(surf(outline=mm))                     # mm read as metres
    with pytest.raises(ValueError, match="source"):
        V.classify_surface(surf(boundary=[dict(runs()[0], source="")] + runs()[1:]))
    with pytest.raises(ValueError, match="source"):
        V.classify_surface(surf(detail={"extent": "WHOLE", "source": None}))
    with pytest.raises(ValueError, match="source"):
        V.classify_surface(surf(covers=[{"id": "c", "kind": "SLAB", "outline": COVER, "source": " "}]))
    with pytest.raises(ValueError, match="reconcile"):
        V.classify_surface(surf(boundary=runs()[:-1]))           # a side not described
    with pytest.raises(ValueError):
        V.classify_surface(surf(boundary=[]))


@pytest.mark.parametrize("angle,mirror", [(0, False), (37.5, False), (90, True), (213, True)])
def test_mirror_and_rotation_invariant(angle, mirror):
    t = lambda ring: V.transformed(ring, angle_deg=angle, mirror=mirror, dx=12.3, dy=-4.5)  # noqa: E731
    r = V.classify_surface(surf(outline=t(LEDGE), boundary=[dict(b, coords=t(b["coords"])) for b in runs()],
                                covers=[{"id": "c", "kind": "SLAB", "outline": t(COVER), "source": S}]))
    assert r["membrane_m2"] == pytest.approx(1.2, abs=1e-5) and r["open_m2"] == pytest.approx(0.48, abs=1e-5)
    r2 = V.classify_surface(surf(outline=t(LEDGE),
                                 boundary=[dict(b, coords=t(b["coords"])) for b in runs(front_covered="WALL")],
                                 covers=[{"id": "c", "kind": "SLAB", "outline": t(COVER), "source": S}],
                                 screens=[{"id": "s", "kind": "GLAZING", "coords": t([(1.8, 0), (1.8, 0.4)]),
                                           "head_drawn": True, "source": S}]))
    assert r2["membrane_m2"] == pytest.approx(0.48, abs=1e-5)


# ---- development villa (private drawing; skipped when absent) -------------------------------------------------------
def _dxf():
    p = os.environ.get("T486_DXF")
    for c in (p, str(ROOT.parent / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"),
              str(ROOT.parent / "private" / "P7757" / "P7757.dxf")):
        if c and os.path.exists(c):
            return c
    return None


@pytest.mark.skipif(_dxf() is None, reason="private drawing absent")
def test_development_villa():
    import t529_alsenan as X
    r = X.build(_dxf())
    d = r["decision"]
    assert d["area_m2"] == pytest.approx(0.639573) and d["covered_m2"] == pytest.approx(0.639573)
    assert d["open_m2"] == pytest.approx(0.0, abs=1e-6)               # wholly under the 2F slab and its projection
    assert abs(r["own_area_m2"] - r["t486_area_m2"]) < 1e-5
    assert r["parts"][0]["decision"] == V.EXPOSED and "2b" in r["parts"][0]["basis"]
    assert r["cover"]["projection_dim"]["printed"] == "35"
    assert r["cover_edge_distances_m"]["projection_edge (V2 read)"] == pytest.approx((0.295604, 1.045604), abs=1e-5)
    e = r["effect"]
    assert e["FIN.WP.ROOF_m2"]["after"] == pytest.approx(209.65844)
    assert e["ledge_upturn"]["after_measured_lm"] == pytest.approx(0.551614, abs=2e-6)
    assert e["ledge_upturn"]["transition_held_lm"] == pytest.approx(2.976663)
    assert r["open_sky_net_m2"] == pytest.approx(4.906867)
    rows = {(x["component"], x.get("run")): x for x in r["rows"]}
    assert rows[("VOID_EDGE_TERMINATION", None)]["status"] == W.HELD
    assert rows[("WINDOW_TRANSITION", "bay_face:BCE")]["status"] == W.HELD
