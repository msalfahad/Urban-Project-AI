"""M9 S2 components with independent expected values: exact plane operations, the polygon tile / membrane layouts
against the S1 rectangle engines, the architectural hatch reader (islands, mirrored OCS, block hatches) against the
unchanged route G reader, the stair / void recognisers, the open-plan rule, facts validation, and package hygiene."""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from engine.source import arch_measure as AM
from engine.source import arch_rooms as AR
from engine.source import material_spec as MS
from engine.source import membrane_layout as ML
from engine.source import plane_poly as PP
from engine.source import tile_layout as TL

ROOT = Path(__file__).resolve().parents[2]
L_ROOM = [(0, 0), (4, 0), (4, 2.5), (2, 2.5), (2, 3.5), (0, 3.5)]          # 4 x 2.5 + 2 x 1 = 12 m2


def _rot(poly, deg, about=(0.0, 0.0)):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return [(about[0] + (x - about[0]) * c - (y - about[1]) * s, about[1] + (x - about[0]) * s + (y - about[1]) * c)
            for x, y in poly]


# ---- plane_poly
def test_area_perimeter_clip_and_band_intervals():
    assert PP.area(L_ROOM) == pytest.approx(12.0)
    assert PP.perimeter(L_ROOM) == pytest.approx(4 + 2.5 + 2 + 1 + 2 + 3.5)
    assert PP.region_area_in_rect(L_ROOM, [], (1, 1, 3, 3)) == pytest.approx(2 * 1.5 + 1 * 0.5)
    hole = [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)]
    assert PP.region_area_in_rect(L_ROOM, [hole], (0, 0, 4, 3.5)) == pytest.approx(12.0 - 0.25)
    assert PP.band_intervals(L_ROOM, [], 2.0, 3.0) == [(0.0, 4.0)]
    assert PP.band_intervals(L_ROOM, [], 2.6, 3.4) == pytest.approx([(0.0, 2.0)])
    U = [(0, 0), (5, 0), (5, 3), (4, 3), (4, 1), (1, 1), (1, 3), (0, 3)]   # a U: two separate runs at the top
    assert PP.band_intervals(U, [], 1.5, 2.5) == pytest.approx([(0.0, 1.0), (4.0, 5.0)])


def test_frame_angle_follows_the_longest_wall():
    assert PP.frame_angle(_rot([(0, 0), (5, 0), (5, 2), (0, 2)], 30)) == pytest.approx(math.radians(30))
    assert PP.frame_angle(_rot([(0, 0), (5, 0), (5, 2), (0, 2)], 120)) == pytest.approx(math.radians(30))


# ---- polygon tile layout vs the S1 rectangle engine
@pytest.mark.parametrize("dims", [(4.0, 3.0), (2.8, 6.4), (3.37, 2.11), (1.0, 0.9)])
@pytest.mark.parametrize("size", MS.OWNER_TILE_SIZES)
def test_polygon_tiles_reproduce_the_rectangle_engine(dims, size):
    c = {"joint_m": 0.002, "min_reusable_m": 0.1, "min_cut_m": 0.05}
    a = TL.best({"length_m": dims[0], "width_m": dims[1]}, MS.tile(size), c)["selected"]
    b = TL.best_polygon({"polygon": [(0, 0), (dims[0], 0), (dims[0], dims[1]), (0, dims[1])]}, MS.tile(size),
                        c)["selected"]
    for k in ("net_installed_m2", "placed_m2", "consumed_m2", "cutting_waste_m2", "reusable_offcuts_m2"):
        assert b[k] == pytest.approx(a[k], abs=1e-9), k
    assert b["units"]["consumed_units"] == a["units"]["consumed_units"]
    assert b["method"] == TL.POLY_METHOD and a["method"] == TL.METHOD


def test_polygon_tiles_are_rotation_invariant_and_balanced():
    c = {"joint_m": 0.003, "min_reusable_m": 0.15}
    sp = MS.tile("TILE-60x60")
    a = TL.best_polygon({"polygon": L_ROOM}, sp, c)["selected"]
    b = TL.best_polygon({"polygon": _rot(L_ROOM, 37, (10, -5))}, sp, c)["selected"]
    assert b["units"]["consumed_units"] == a["units"]["consumed_units"]
    assert b["consumed_m2"] == pytest.approx(a["consumed_m2"], abs=1e-9)
    assert a["net_installed_m2"] == pytest.approx(12.0)
    parts = a["placed_m2"] + a["overlap_m2"] + a["cutting_waste_m2"] + a["reusable_offcuts_m2"]
    assert parts == pytest.approx(a["consumed_m2"], abs=1e-6)
    assert a["placed_m2"] <= a["net_installed_m2"] + 1e-9            # joints are not tiles


def test_polygon_tiles_cut_around_a_column_and_count_shaped_pieces():
    c = {"joint_m": 0.002}
    sp = MS.tile("TILE-60x60")
    col = [(1.0, 1.0), (1.4, 1.0), (1.4, 1.4), (1.0, 1.4)]
    r = TL.best_polygon({"polygon": [(0, 0), (3, 0), (3, 3), (0, 3)], "holes": [col]}, sp, c)["selected"]
    assert r["net_installed_m2"] == pytest.approx(9.0 - 0.16)
    assert r["layout"]["obstructions"] == 1 and any("OBSTRUCTIONS" in x for x in r["concerns"])
    tri = TL.best_polygon({"polygon": [(0, 0), (3, 0), (0, 3)]}, sp, c)["selected"]
    assert tri["layout"]["shaped_cuts"] > 0 and tri["state"] == "COMPUTED_REVIEW"
    assert tri["net_installed_m2"] == pytest.approx(4.5)


def test_the_s1_rectangle_engine_still_blocks_polygons():
    r = TL.best({"polygon": L_ROOM}, MS.tile("TILE-60x60"), {"joint_m": 0.002})["selected"]
    assert r["state"] == "BLOCKED" and r["blocked_by"] == TL.POLYGON_BLOCK


# ---- polygon membrane vs the S1 rectangle engine
@pytest.mark.parametrize("dims", [(3.0, 2.0), (2.4, 1.6), (4.5, 2.2), (12.0, 3.0), (2.8, 2.4)])
def test_polygon_membrane_reproduces_the_rectangle_engine(dims):
    c = {"upturn_h_m": 0.20, "doorways": [{"door_id": "D1", "width_m": 0.8, "depth_m": 0.2}],
         "doorway_detail": "NOT_ESTABLISHED", "direction": "MIN_MATERIAL", "min_reusable_m": 0.3}
    a = ML.plan({"length_m": dims[0], "width_m": dims[1]}, MS.membrane(), constraints=c)
    b = ML.plan_polygon({"polygon": [(0, 0), (dims[0], 0), (dims[0], dims[1]), (0, dims[1])]}, MS.membrane(),
                        constraints=c)
    for k in ("net_installed_m2", "overlap_m2", "consumed_m2", "cutting_waste_m2", "reusable_offcuts_m2"):
        assert b[k] == pytest.approx(a[k], abs=1e-9), k
    assert b["units"]["consumed_units"] == a["units"]["consumed_units"]
    assert b["layout"]["direction"] == a["layout"]["direction"]


def test_polygon_membrane_balances_on_l_rooms_columns_and_rotation():
    c = {"upturn_h_m": 0.20, "doorways": [], "direction": "MIN_MATERIAL", "min_reusable_m": 0.3}
    L = ML.plan_polygon({"polygon": [(0, 0), (3, 0), (3, 1), (1, 1), (1, 2), (0, 2)]}, MS.membrane(), constraints=c)
    assert L["net_installed_m2"] == pytest.approx(4.0 + 10.0 * 0.20)
    R = ML.plan_polygon({"polygon": _rot([(0, 0), (3, 0), (3, 1), (1, 1), (1, 2), (0, 2)], 53)}, MS.membrane(),
                        constraints=c)
    assert R["consumed_m2"] == pytest.approx(L["consumed_m2"], abs=1e-9)
    col = [(1.0, 0.8), (1.3, 0.8), (1.3, 1.1), (1.0, 1.1)]
    H = ML.plan_polygon({"polygon": [(0, 0), (3, 0), (3, 2), (0, 2)], "holes": [col]}, MS.membrane(), constraints=c)
    assert H["net_installed_m2"] == pytest.approx(6.0 - 0.09 + (10.0 + 1.2) * 0.20)
    assert [r["length_m"] for r in H["layout"]["band_runs"]] == pytest.approx([10.0, 1.2])
    for r in (L, R, H):
        parts = r["placed_m2"] + r["overlap_m2"] + r["cutting_waste_m2"] + r["reusable_offcuts_m2"]
        assert parts == pytest.approx(r["consumed_m2"], abs=1e-6)


def test_band_pieces_keep_full_precision_on_irregular_perimeters():
    # a 7.414038 m boundary used to break the roll balance when band pieces were rounded to 0.1 mm
    poly = [(0.4435, 0.0), (1.0568, 0.6132), (1.6225, 1.1789), (1.6654, 1.2219), (0.0, 2.8873), (0.0, 0.0), (0.3, 0.0)]
    r = ML.plan_polygon({"polygon": poly, "perimeter_lm": 7.414038}, MS.membrane(),
                        constraints={"upturn_h_m": 0.20, "doorways": [], "direction": "ALONG_X"})
    assert r["state"] != "BLOCKED"


# ---- the architectural hatch reader vs route G's reader (unchanged)
def test_hatch_reader_reads_islands_mirrored_ocs_and_block_hatches(tmp_path):
    pytest.importorskip("ezdxf")
    from tools import arch_intake as AI
    from tools import arch_synth as AS
    fx = AS.hatch_islands(tmp_path / "h.dxf")
    got = AI.hatches(fx["path"])
    assert len(got) == len(fx["truth"])
    for t in fx["truth"]:
        m = [h for h in got if h["layer"] == t["layer"] and abs(h["area_native"] * 1e-6 - t["area_m2"]) < 1e-6 and
             abs(PP.bbox(h["rings"][0])[0] - t["box_mm"][0]) < 1e-6 and abs(PP.bbox(h["rings"][0])[2] -
                                                                              t["box_mm"][2]) < 1e-6]
        assert len(m) == 1, t
        assert m[0]["islands"] == t["islands"]


def test_route_g_hatch_reading_is_unchanged(tmp_path):
    """the frozen reader keeps its first-path, model-space-only behaviour (changing it alters M6-M8 results and
    needs owner approval): this documents the defect the architectural reader corrects."""
    pytest.importorskip("ezdxf")
    from tools import arch_synth as AS
    from tools import urban_intake as UI
    fx = AS.hatch_islands(tmp_path / "h.dxf")
    v1 = UI.read(fx["path"])["hatches"]
    assert {h["layer"] for h in v1} == {"H-ISLAND", "H-MIRROR"}       # block hatches are not read
    isl = next(h for h in v1 if h["layer"] == "H-ISLAND")
    assert abs(PP.area(isl["ring"])) * 1e-6 == pytest.approx(12.0)   # the island is not subtracted


# ---- recognisers
def _seg(i, a, b, layer="ST"):
    return {"id": f"S{i}", "layer": layer, "a": a, "b": b}


def test_tread_flights_are_recognised_and_furniture_is_not():
    segs = [_seg(i, (0, 280.0 * i), (1100, 280.0 * i)) for i in range(12)]            # 12 lines, going 0.28
    segs += [_seg(100 + i, (5000, 900.0 * i), (6000, 900.0 * i)) for i in range(5)]   # 0.90 apart: not treads
    segs += [_seg(200 + i, (8000, 300.0 * i), (8300, 300.0 * i)) for i in range(6)]   # 0.30 long: too short
    fl = AR.tread_flights(segs, 0.001)
    assert len(fl) == 1
    assert (fl[0]["tread_lines"], fl[0]["going_m"], fl[0]["width_m"]) == (12, pytest.approx(0.28),
                                                                         pytest.approx(1.1))
    assert fl[0]["run_m"] == pytest.approx(11 * 0.28)


def test_void_symbol_is_a_rectangle_with_both_diagonals():
    rect = [_seg(1, (0, 0), (3000, 0)), _seg(2, (3000, 0), (3000, 2000)), _seg(3, (3000, 2000), (0, 2000)),
            _seg(4, (0, 2000), (0, 0))]
    assert not AR.void_symbols(rect, 0.001)
    one = rect + [_seg(5, (0, 0), (3000, 2000))]
    assert not AR.void_symbols(one, 0.001)
    both = one + [_seg(6, (0, 2000), (3000, 0))]
    (v,) = AR.void_symbols(both, 0.001)
    assert v["area_m2"] == pytest.approx(6.0)


# ---- the open-plan rule and the facts
def test_open_plan_of_dry_kinds_is_one_dry_room_and_mixed_kinds_are_not():
    assert AM._kind({"codes": ["DINING", "LIVING", "PANTRY"]}) == AR.DRY
    assert AM._kind({"codes": ["CORRIDOR", "LIVING"]}) == AR.DRY
    assert AM._kind({"codes": ["LIVING", "VOID"]}) is None
    assert AM._kind({"codes": ["BATHROOM", "BEDROOM"]}) is None
    assert AM._kind({"codes": ["BATHROOM"]}) == AR.WET


def test_facts_need_values_with_their_authority():
    ok = {"schema": AM.FACTS_SCHEMA, "wall_heights": {"*": {"PLASTER": {"value_m": 3.0, "authority": "OWNER: x"}}},
          "stairs": {"1F": {"riser_m": {"value_m": 0.17, "authority": "SECTION A-A"}}}}
    assert AM.validate_facts(ok) is ok
    for bad in ({"schema": "X"},
                {"schema": AM.FACTS_SCHEMA, "wall_heights": {"*": {"PLASTER": {"value_m": 3.0}}}},
                {"schema": AM.FACTS_SCHEMA, "wall_heights": {"*": {"ROOF": {"value_m": 3.0, "authority": "x"}}}},
                {"schema": AM.FACTS_SCHEMA, "opening_heights": {"DOOR": {"authority": "x"}}},
                {"schema": AM.FACTS_SCHEMA, "stairs": {"1F": {"riser_m": {"value_m": 0.17}}}}):
        with pytest.raises(AM.FactsError):
            AM.validate_facts(bad)


def test_a_floor_to_floor_interval_is_never_a_wall_height():
    h = AM.heights("GF", 0.0, 3.5, {})
    for tr in AM.TRADES:
        assert h[tr]["state"] != "ESTABLISHED", tr
    assert h["_interval"]["value_m"] == pytest.approx(3.5)


# ---- hygiene of the S2 files (generic vocabulary only, no client identity)
S2_FILES = ["engine/source/arch_plan.py", "engine/source/arch_rooms.py", "engine/source/arch_measure.py",
            "engine/source/plane_poly.py", "tools/arch_intake.py", "tools/arch_overlay.py", "tools/arch_synth.py",
            "tools/urban_boq_m9.py", "engine/boq_room_workbook.py", "research/urban_m9_s2/SYNTHETIC_FACTS_S2.json",
            "tests/m9_s2_arch/test_arch_route.py"]
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|als[ey]?n[ya]?an|qortuba", re.I)
ARABIC = re.compile(r"[؀-ۿ]+")


def test_s2_files_carry_no_client_identity_and_only_controlled_arabic():
    from engine.source import arch_plan as AP
    from engine.source import boq_line as BL
    from engine.source import rule_store as RS
    vocab = set()
    for _en, ar, _t, _u in BL.ITEMS.values():
        vocab.update(ARABIC.findall(ar))
    for f in RS.family_master()["families"]:
        vocab.update(ARABIC.findall(f["item_ar"]))
    for s in RS.material_specs()["specs"]:
        vocab.update(ARABIC.findall(s.get("name_ar") or ""))
    for _c, _en, ar, _k, pats in AR.LEXICON:                        # the generic room lexicon (controlled)
        vocab.update(ARABIC.findall(ar))
        for p in pats:
            vocab.update(ARABIC.findall(p))
    vocab.update(ARABIC.findall(AR.UNNAMED[1]))
    for _fl, _o, pats in AP.FLOOR_TITLES:
        for p in pats:
            vocab.update(ARABIC.findall(p))
    for p in AP.NOT_A_PLAN:
        vocab.update(ARABIC.findall(p))
    lex_files = {"engine/source/arch_rooms.py", "engine/source/arch_plan.py"}
    for f in S2_FILES:
        text = (ROOT / f).read_text(encoding="utf-8")
        assert not HYGIENE.search(text), f
        if f not in lex_files:
            assert not set(ARABIC.findall(text)) - vocab, f


def test_no_drawing_or_workbook_is_tracked_in_the_s2_package():
    import subprocess
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "research/urban_m9_s2", "tests/m9_s2_arch"],
                             capture_output=True, text=True).stdout.split()
    assert not [t for t in tracked if t.endswith((".xlsx", ".pdf", ".dxf", ".dwg", ".png", ".zip", ".svg"))]
