"""T-553: floor tile reconciliation by room and tile size (research/agents_t553, R-T553-1).
Synthetic villa "K553" (not the training villa), hand calculations; adverse cases; then the development villa (the
drawing check is skipped when the private DXF is absent)."""
from __future__ import annotations

import copy
import json
import math
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t553"))
import t553_floor_tile_reconcile as T  # noqa: E402
import t553_inputs as I  # noqa: E402

# ---- villa "K553" (hand). Bed room 4.00 x 3.50 = 14.000 m2, porcelain 120 x 60 (finish schedule FS-1); bath 2.00 x
# 1.80 = 3.600 m2, wet tile 60 x 60 (FS-1); one 0.90 door between them in a 0.20 wall: marble threshold 0.90 x 0.20 =
# 0.180 m2, its own line L-thr1 (B3-04), in neither floor. Freelancer: bed room 14.18 (threshold taken into the room),
# bath 3.60, total 17.78. Engine 17.600; gap -0.180 = threshold owned by L-thr1 (RULE_DIFFERENCE).
FS = "K553 finish schedule FS-1"
BED = [(0, 0), (4.00, 0), (4.00, 3.50), (0, 3.50)]
BATH = [(4.20, 0), (6.20, 0), (6.20, 1.80), (4.20, 1.80)]


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def xf(pts, deg=0.0, mirror=False, scale=1.0):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        x = -x if mirror else x
        out.append(((x * math.cos(a) - y * math.sin(a)) * scale + 1234.5, (x * math.sin(a) + y * math.cos(a)) * scale - 77.0))
    return out


def krows():
    return [
        {"room": "bed", "tile_size": "120 x 60", "tile_size_source": FS, "freelancer_tile_size": "120x60",
         "freelancer_tile_size_source": FS,
         "engine_lines": [{"line_id": "L-bed", "item_code": "FIN.FLOOR.PORCELAIN", "qty": "14.000", "unit": "m2"}],
         "freelancer": [{"row": 5, "m2": "14.18"}], "freelancer_class": "DRY",
         "components": [{"name": "door threshold 0.90 x 0.20 taken into his room", "qty": "0.180", "sign": -1,
                         "cause": "RULE_DIFFERENCE", "basis": FS + " + UP-CER-001 (threshold is B3-04 marble)",
                         "owned_by": "L-thr1"}]},
        {"room": "bath", "tile_size": "60x60", "tile_size_source": FS, "freelancer_tile_size": "60x60",
         "freelancer_tile_size_source": FS,
         "engine_lines": [{"line_id": "L-bath", "item_code": "FIN.FLOOR.WET_TILE", "qty": "3.600", "unit": "m2"}],
         "freelancer": [{"row": 9, "m2": "3.60"}], "freelancer_class": "WET", "components": []},
    ]


def test_k553_hand_areas_any_frame_and_unit():
    for deg in (0, 37, 90, 211):
        for mirror in (False, True):
            for scale, f in ((1.0, 1), (1000.0, 1e6)):
                assert round(area(xf(BED, deg, mirror, scale)) / f, 9) == 14.0
                assert round(area(xf(BATH, deg, mirror, scale)) / f, 9) == 3.6
    assert Decimal("0.90") * Decimal("0.20") == Decimal("0.1800")


def test_k553_table_by_hand():
    t = T.reconcile(rows=krows(), freelancer_total="17.78", engine_total="17.600")
    assert t["gap_engine_minus_freelancer"] == "-0.180" and t["by_cause"] == {"RULE_DIFFERENCE": "-0.180"}
    assert t["by_size"] == {"120x60": {"engine": "14.000", "freelancer": "14.18", "delta": "-0.180"},
                            "60x60": {"engine": "3.600", "freelancer": "3.60", "delta": "0.000"}}
    assert t["class_split_engine"] == {"DRY": "14.000", "WET": "3.600"}


def test_size_not_given_is_its_own_class_never_a_default():
    r = krows()
    for x in r:
        for k in ("tile_size", "tile_size_source", "freelancer_tile_size", "freelancer_tile_size_source"):
            x.pop(k)
    t = T.reconcile(rows=r, freelancer_total="17.78", engine_total="17.600")
    assert list(t["by_size"]) == [T.NO_SIZE]


@pytest.mark.parametrize("mut, msg", [
    (lambda r: r[0]["freelancer"][0].update(m2="14.70", basis="procurement"), "procurement"),
    (lambda r: r[0]["freelancer"][0].update(multiplier="1.05"), "multiplier"),
    (lambda r: r[0]["engine_lines"][0].update(basis="procurement"), "installed"),
    (lambda r: r[0]["engine_lines"].append({"line_id": "L-thr1", "item_code": "FIN.MARBLE.THRESHOLD", "qty": "0.18",
                                            "unit": "m2"}), "not a floor tile line"),
    (lambda r: r[1]["components"].append({"name": "x", "qty": "0", "sign": 1, "cause": "TOLERANCE", "basis": FS,
                                          "owned_by": "L-thr1"}), "owned once"),
    (lambda r: r[0].update(tile_size_source=""), "no source"),
    (lambda r: r[0].update(freelancer_tile_size="60x60"), "never one row"),
    (lambda r: r[0]["components"][0].update(qty="0.170"), "components sum"),
    (lambda r: r[0]["components"][0].update(basis="freelancer row 5"), "never a component basis"),
    (lambda r: r[1]["components"].append({"name": "rounding", "qty": "0.010", "sign": 1, "cause": "TOLERANCE",
                                          "basis": FS}), "TOLERANCE"),
    (lambda r: r[0]["components"][0].update(cause="AGREE"), "not in"),
])
def test_adverse_refused(mut, msg):
    r = krows()
    mut(r)
    with pytest.raises(T.TileTableError, match=msg):
        T.reconcile(rows=r, freelancer_total="17.78" if msg != "procurement" else "18.30", engine_total="17.600")


def test_procurement_with_waste_against_installed_refused():
    """the acceptance adverse case: 14.00 x 1.05 waste = 14.70 m2 of tile to buy compared with 14.00 installed."""
    r = krows()
    r[0]["freelancer"] = [{"row": 5, "m2": "14.70", "basis": "procurement", "waste": "5 %"}]
    with pytest.raises(T.TileTableError, match="procurement"):
        T.reconcile(rows=r, freelancer_total="18.30", engine_total="17.600")


def test_held_is_never_zero_and_stays_outside_totals():
    r = krows()
    r.append({"room": "store", "engine_lines": [{"line_id": "L-st", "item_code": "FIN.FLOOR.FINISH_HELD", "qty": None,
                                                 "unit": "m2", "state": "HELD", "bound": ["0", "1.20"]}],
              "freelancer": [], "components": []})
    t = T.reconcile(rows=r, freelancer_total="17.78", engine_total="17.600")
    assert t["held_lines"][0]["line_id"] == "L-st" and t["rows"][2]["state"] == "HELD"
    r[2]["engine_lines"][0]["qty"] = "0"
    with pytest.raises(T.TileTableError, match="never 0"):
        T.reconcile(rows=r, freelancer_total="17.78", engine_total="17.600")


def test_stale_totals_refused():
    with pytest.raises(T.TileTableError, match="engine rows sum"):
        T.reconcile(rows=krows(), freelancer_total="17.78", engine_total="17.700")
    with pytest.raises(T.TileTableError, match="printed total"):
        T.reconcile(rows=krows(), freelancer_total="17.70", engine_total="17.600")
    idx = {"L-bed": {"item_code": "FIN.FLOOR.PORCELAIN", "measured_net": 14.0},
           "L-bath": {"item_code": "FIN.FLOOR.WET_TILE", "measured_net": 3.6},
           "L-hall": {"item_code": "FIN.FLOOR.PORCELAIN", "measured_net": 2.0}}
    with pytest.raises(T.TileTableError, match="missing from the table"):
        T.reconcile(rows=krows(), freelancer_total="17.78", index=idx)
    idx.pop("L-hall")
    idx["L-bed"]["measured_net"] = 14.1
    with pytest.raises(T.TileTableError, match="stale"):
        T.reconcile(rows=krows(), freelancer_total="17.78", index=idx)


def test_completeness_join_finds_a_space_with_ceiling_and_no_floor():
    lines = [{"line_id": "L-1", "item_code": "ARCH.SPACE", "class": "RELEASED", "element_id": "K-R1:space", "measured_net": 2.5},
             {"line_id": "L-2", "item_code": "FIN.CEILING", "class": "RELEASED", "element_id": "K-R1:ceiling", "measured_net": 2.5},
             {"line_id": "L-3", "item_code": "ARCH.SPACE", "class": "RELEASED", "element_id": "K-R2:space", "measured_net": 4.0},
             {"line_id": "L-4", "item_code": "FIN.CEILING", "class": "RELEASED", "element_id": "K-R2:ceiling", "measured_net": 4.0},
             {"line_id": "L-5", "item_code": "FIN.FLOOR.FINISH_HELD", "class": "HELD", "element_id": "K-R2:floor", "measured_net": None}]
    assert T.missing_floor_lines(lines) == [{"element": "K-R1", "space_line": "L-1", "area": 2.5}]


# ---- development villa
@pytest.fixture(scope="module")
def run():
    import t553_alsenan as A
    return A, A.build()


def test_alsenan_output_reproduces(run):
    A, o = run
    assert A.OUT.read_text() == A.text(o)


def test_alsenan_totals_and_causes(run):
    t = run[1]["table"]
    assert (t["engine_total"], t["freelancer_total"], t["gap_engine_minus_freelancer"]) == ("387.094050", "409.58", "-22.485950")
    assert t["by_cause"] == {"ENGINE_RIGHT": "-0.797732", "ENGINE_WRONG": "-2.970", "HELD": "-9.705",
                             "RULE_DIFFERENCE": "-15.941912", "TOLERANCE": "0.028416", "UNRESOLVED": "6.900278"}
    assert t["by_size"] == {T.NO_SIZE: {"engine": "387.094050", "freelancer": "409.58", "delta": "-22.485950"}}
    assert t["class_split_engine"] == {"DRY": "305.020973", "FINISH_HELD": "6.1275", "WET": "75.945577"}
    assert t["class_split_freelancer"] == {"DRY": "337.57", "WET": "72.01"}
    assert [h["line_id"] for h in t["held_lines"]] == ["L-a788de4672b1f0d2e6c1"]


def test_alsenan_every_floor_line_once_and_owner_lines_exist(run):
    d = I.load_index()
    idx = {v["line_id"]: v for v in d["lines"]}
    placed = [ln["line_id"] for r in I.rows(d) for ln in r["engine_lines"]]
    valid = [k for k, v in idx.items() if v["item_code"] in T.FLOOR_CODES and v["class"] != "EXCLUDED"]
    assert sorted(placed) == sorted(valid) and len(placed) == len(set(placed))
    codes = {"gf_stair_footprint": "ARCH.SPACE", "garden_band": "ARCH.EXTERIOR", "band_curb": "ARCH.SPACE",
             "arrival_1f": "FIN.MARBLE.LANDING", "arrival_2f": "FIN.MARBLE.LANDING"}
    for k, lid in I.OWN.items():
        assert idx[lid]["item_code"] == codes.get(k, "FIN.MARBLE.LIFT_THRESHOLD")
    assert run[1]["missing_floor_lines"] == [{"element": "1F-RFFE7AF", "space_line": "L-390e3b9f1ce6e01d4d15", "area": 2.97}]


def test_alsenan_freelancer_cells_match_his_sheet():
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text())
    sheet = {r["row"]: r["cells"] for r in raw["rows"] if r["file"] == "FIN" and r["sheet"] == "سيراميك"}
    for _room, _f, _e, cells, *_ in I.DRY:
        for row, m2 in cells:
            assert Decimal(str(sheet[row][f"D{row}"]["v"])) == Decimal(m2)
            assert f"F{row}" not in sheet[row]          # no multiplier / height on a dry floor row
    for _room, _e, row, m2, _c in I.WET:
        assert Decimal(str(sheet[row][f"H{row}"]["v"])) == Decimal(m2) and sheet[row][f"H{row}"]["f"] == f"=D{row}"
    assert sheet[70]["H70"]["f"] == "=H65+D31" and Decimal(str(sheet[70]["H70"]["v"])) == Decimal(I.FREELANCER_TOTAL)


def test_alsenan_outdoor_is_outside_the_internal_pair(run):
    o = run[1]["outdoor"]
    assert o["valued_m2"] == "140.5558" and [list(x) for x in o["porcelain_tile"]] == [["L-ab44fbc79bed353bde99", "GF-COURT#NORTH-WALK", 21.0142]]
    assert {h[1] for h in o["held"]} == {"GF-COURT#POOL-DECK", "GF-COURT#PORCH"}


DXF = Path(os.environ.get("T553_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_alsenan_drawing_dimensions():
    ezdxf = pytest.importorskip("ezdxf")
    db = ezdxf.readfile(str(DXF)).entitydb
    for h, mm in {"568": 4000, "57F": 6300, "53A": 1750, "5C9": 4500, "7B0": 4000, "890": 4820}.items():
        assert round(db[h].get_measurement()) == mm, h
    assert abs(4.0 * 6.3 - (1.21 - math.pi * 1.21 / 4) - 24.940332) < 0.0002
