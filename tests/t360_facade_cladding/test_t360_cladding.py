"""T-360: facade cladding / stone (B4-11). Non-Alsenan fixture with hand calculations + adverse cases, then the
development-villa ledger rebuild (committed inputs only, no private file)."""

import importlib.util
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t360")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t360_cladding_rules")
A = _load("t360_alsenan")

STONE = R.Mark("PRINTED_LEGEND", "limestone 3 cm", "fixture legend L1")


def _face(length=12.40, openings=(), marks=(STONE,), band=(0.00, 1.20), line="EXT-PLASTER-GF"):
    return R.Face("V2/S-1", length, 0.00, 4.20, openings=tuple(openings), marks=tuple(marks),
                  plaster_line=line, extra={"band": band})


# --- normal cases: a two-storey villa (not Alsenan), street face 12.40 m, storey 0.00 -> 4.20 -------------------

def test_printed_stone_plinth_band_hand():
    # hand: 12.40 x 1.20 = 14.880; door D1 1.20 wide from 0.00 to 2.40 -> 1.20 x 1.20 = 1.440 inside the band;
    # window W1 1.50 wide, sill 1.00 head 2.40 -> 1.50 x 0.20 = 0.300 inside; window W2 sill 1.40 -> 0
    ops = (R.Opening("D1", 1.20, 0.00, 2.40), R.Opening("W1", 1.50, 1.00, 2.40), R.Opening("W2", 1.00, 1.40, 2.40))
    row = R.face_state(_face(openings=ops))
    assert row["state"] == "MARKED_MATERIAL" and row["material"] == "limestone 3 cm"
    assert row["cladding_m2"] == pytest.approx(14.880 - 1.440 - 0.300, abs=1e-9)  # 13.140
    assert row["status"] == R.DC and row["replaces"] == "EXT-PLASTER-GF"


def test_full_height_cladding_units_mm_to_m():
    # the same face drawn in mm: 12400 mm -> 12.400 m; full height 4.20: 52.080 - D1 2.880 - W1 2.100 = 47.100
    length = 12400 / 1000.0
    ops = (R.Opening("D1", 1.20, 0.00, 2.40), R.Opening("W1", 1.50, 1.00, 2.40))
    row = R.face_state(_face(length=length, openings=ops, band=(0.00, 4.20)))
    assert row["cladding_m2"] == pytest.approx(52.080 - 2.880 - 2.100, abs=1e-9)


def test_unmarked_face_is_not_in_drawn_scope_never_zero_quantity():
    row = R.face_state(_face(marks=()))
    assert row["state"] == "NOT_MARKED" and row["status"] == "NOT IN DRAWN SCOPE" and row["cladding_m2"] is None


def test_section_cut_and_ground_hatches_are_not_finishes():
    marks = (R.Mark(R.hatch_kind("ANSI31", "cut")), R.Mark(R.hatch_kind("EARTH", "ground")))
    assert R.material_of(marks)[0] == "NOT_MARKED"


def test_curved_face_shading_is_not_a_hatch():
    cyl = [round(2000 * math.cos(math.radians(a)), 1) for a in range(0, 91, 15)]  # a 2.00 m radius drum, 15 deg steps
    assert R.is_curved_face_shading(cyl)
    assert R.is_curved_face_shading([-x for x in cyl])  # mirrored drawing
    assert not R.is_curved_face_shading([0, 300, 600, 900, 1200])  # coursed lines at 0.30: uniform, not a drum
    assert not R.is_curved_face_shading([0, 50, 60, 200, 210, 400])


# --- adverse cases -----------------------------------------------------------------------------------------------

def test_render_refused_as_material_source():
    with pytest.raises(R.RefusedSource):
        R.face_state(_face(marks=(R.Mark("RENDER", "grey stone", "3D render"),)))


def test_default_or_typical_stone_refused():
    for kind in ("DEFAULT", "TYPICAL", "FREELANCER", "UNNAMED_HATCH", "PHOTO"):
        with pytest.raises(R.RefusedSource):
            R.material_of((R.Mark(kind, "stone"),))
    with pytest.raises(R.RefusedSource):
        R.material_of((R.Mark("PRINTED_LEGEND", None, "legend without a name"),))


def test_graphic_form_only_is_held_blank():
    row = R.face_state(_face(marks=(R.Mark("GRAPHIC_FORM", None, "voussoir outlines"),)))
    assert row["state"] == "MARKED_FORM_MATERIAL_HELD" and row["status"] == R.HELD and row["cladding_m2"] is None


def test_two_printed_materials_conflict_held():
    m2 = R.Mark("TEXT_NOTE", "GRC panel", "note 4")
    row = R.face_state(_face(marks=(STONE, m2)))
    assert row["state"] == "CONFLICT" and row["status"] == R.HELD and row["cladding_m2"] is None


def test_material_without_printed_band_is_held():
    row = R.face_state(_face(band=None))
    assert row["status"] == R.HELD and row["cladding_m2"] is None


def test_held_opening_head_gives_blank_never_zero():
    ops = (R.Opening("W9", 1.00, 0.60, None),)
    row = R.face_state(_face(openings=ops))
    assert row["cladding_m2"] is None and row["status"] == R.HELD


def test_opening_deducted_once():
    op = R.Opening("D1", 1.20, 0.00, 2.40)
    with pytest.raises(R.DoubleCount):
        R.cladding_net(_face(openings=(op, op)), 0.00, 1.20)


def test_band_leaving_the_face_refused():
    with pytest.raises(ValueError):
        R.cladding_net(_face(), 0.00, 4.50)


def test_face_in_plaster_and_cladding_refused():
    row = dict(key="V2/S-1", band=(0.00, 1.20), cladding_m2=14.88)
    with pytest.raises(R.DoubleCount):
        R.check_no_double_count([row], {("V2/S-1", 0.00, 4.20): 52.08})
    # the plaster part re-cut above the band: no overlap -> 0
    assert R.check_no_double_count([row], {("V2/S-1", 1.20, 4.20): 37.20}) == 0.0
    # a HELD plaster part (None) is not a quantity, nothing to double count
    assert R.check_no_double_count([row], {("V2/S-1", 0.00, 4.20): None}) == 0.0


# --- development villa (committed inputs only) -------------------------------------------------------------------

def test_outputs_reproduce():
    out = A.build()
    for name, text in out.items():
        with open(os.path.join(HERE, name), encoding="utf-8", newline="") as fh:
            assert fh.read() == text, name


def test_alsenan_every_face_key_unmarked_and_no_double_count():
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(A.build()["FACE_STATE_T360.csv"])))
    assert len(rows) == 109 and len({r["key"] for r in rows}) == 109
    assert all(r["b4_11_state"] == "NOT_MARKED" and r["cladding_m2"] == "" for r in rows)
    assert all(r["double_count_m2"] == "0.000000" for r in rows)


def test_alsenan_porch_arch_held_blank_with_visible_geometry():
    import csv
    import io
    c = {r["id"]: r for r in csv.DictReader(io.StringIO(A.build()["CANDIDATES_T360.csv"]))}
    assert c["C-1"]["state"] == "MARKED_FORM_MATERIAL_HELD" and c["C-1"]["b4_11_status"] == "HELD"
    assert c["C-1"]["cladding_m2"] == ""  # never 0, never the visible part as a quantity
    assert "1.5149" in c["C-1"]["geometry"] and "UNKNOWN" in c["C-1"]["geometry"]
    assert "21 pieces" in c["C-1"]["geometry"] and "face = outer ring" in c["C-1"]["geometry"]
    # r2: all 10 blocks double-outlined (outer handles named per block); arch by hand within the pen-joint closing
    assert len(A.BLOCK_RINGS) == A.SURROUND["large_blocks"] == A.SURROUND["double_outline_blocks"] == 10
    blocks = [0.0897, 0.0931, 0.0930, 0.1054, 0.0932, 0.0933, 0.1349]
    band = [0.0476, 0.0511, 0.0513, 0.0448, 0.0514, 0.0257, 0.0046]
    assert sum(blocks) + sum(band) == pytest.approx(0.9791, abs=1e-4)
    assert A.SURROUND["arch_m2"] == pytest.approx(0.9799, abs=1e-4)
    assert abs(A.SURROUND["arch_m2"] - (sum(blocks) + sum(band))) / A.SURROUND["arch_m2"] < 0.001
    assert c["C-3"]["state"] == "REFUSED"
    # jamb by hand: 3 quoins 0.35 x 0.30 + band 0.20 x 1.10
    assert A.SURROUND["jamb_hand_m2"] == pytest.approx(3 * 0.35 * 0.30 + 0.20 * (0.20 + 3 * 0.30), abs=1e-9)


# --- r2: R-T360-6 drawn face of a unit block (synthetic linework in mm, not Alsenan) ------------------------------

def _rect_lines(x0, y0, x1, y1):
    from shapely.geometry import LineString
    return [LineString([(x0, y0), (x1, y0)]), LineString([(x1, y0), (x1, y1)]),
            LineString([(x1, y1), (x0, y1)]), LineString([(x0, y1), (x0, y0)])]


def test_double_outline_block_takes_its_outer_ring():
    from shapely.geometry import box
    # hand: inner outline 300 x 280, second ring drawn 10 mm outside -> face 320 x 300 = 96,000 mm2 = 0.096 m2
    inner = box(0, 0, 300, 280)
    lines = _rect_lines(0, 0, 300, 280) + _rect_lines(-10, -10, 310, 290)
    face, kind = R.block_face(inner, lines)
    assert kind == "DOUBLE" and face.area / 1e6 == pytest.approx(0.096, abs=1e-9)


def test_single_outline_block_is_not_offset_even_with_a_neighbour_10mm_away():
    from shapely.geometry import LineString, box
    # adverse: one outline only; a band piece's edge runs 10 mm above and a joint 10 mm right, both PAST the block's
    # corners (a joint, not a second ring) -> the single line is the face: 300 x 280 = 0.084 m2, never 0.096
    inner = box(0, 0, 300, 280)
    lines = _rect_lines(0, 0, 300, 280) + [LineString([(-400, 290), (700, 290)]), LineString([(310, -300), (310, 600)])]
    face, kind = R.block_face(inner, lines)
    assert kind == "SINGLE" and face.area / 1e6 == pytest.approx(0.084, abs=1e-9)
    # adverse: the outer ring drawn on three sides only -> SINGLE (never decided by a count of blocks)
    face, kind = R.block_face(inner, _rect_lines(0, 0, 300, 280) + _rect_lines(-10, -10, 310, 290)[:3])
    assert kind == "SINGLE" and face.area / 1e6 == pytest.approx(0.084, abs=1e-9)


def test_double_outline_block_cut_by_a_section_line():
    from shapely.geometry import LineString, box
    # the view stops at a section line x = 305: the outer ring's right side and corners lie beyond it -> still DOUBLE
    # inside the view; visible face 315 x 300 = 0.0945 m2 (hand), the part beyond the cut is not counted
    clip = box(-100, -100, 305, 400)
    inner = box(0, 0, 300, 280)
    lines = [g.intersection(clip) for g in _rect_lines(0, 0, 300, 280) + _rect_lines(-10, -10, 310, 290)]
    lines = [g for g in lines if not g.is_empty] + [LineString([(305, -100), (305, 400)])]
    face, kind = R.block_face(inner, lines, clip=clip)
    assert kind == "DOUBLE" and face.intersection(clip).area / 1e6 == pytest.approx(0.0945, abs=1e-9)


def test_no_coordinates_or_client_text_committed():
    import re
    for name in os.listdir(HERE):
        if name.endswith((".csv", ".json", ".md")):
            text = open(os.path.join(HERE, name), encoding="utf-8").read()
            assert not re.search(r"-?\d{6}\.\d", text), name  # no drawing coordinates
            assert not re.search(r"[؀-ۿ]{3,}", text), name  # no Arabic client / title-block text
