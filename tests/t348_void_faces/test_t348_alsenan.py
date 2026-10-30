"""T-348 development villa: rebuild byte for byte from the committed T-337 binding and the recorded drawing values;
check the invariants the T-314 package relies on. Reads committed research files only (no private drawing)."""
import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t348"
sys.path.insert(0, str(HERE))

import t348_alsenan as T  # noqa: E402

OUT = T.outputs()


def rows(name):
    return list(csv.DictReader(io.StringIO(OUT[name])))


def test_byte_identical_rebuild():
    for name, text in OUT.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_statement_closes_on_his_109_890():
    s = json.loads(OUT["summary.json"])
    assert s["his_total_m2"] == pytest.approx(109.89, abs=1e-9)
    assert s["residual_m2"] == 0.0
    total = sum(float(r["m2"]) for r in rows("RECON_T348.csv") if r["class"] != "RESIDUAL")
    assert total == pytest.approx(109.89, abs=1e-5)          # 14 parts, each rounded to 6 decimals in the CSV
    # r2: row 74's SW side carries the NW-3 end return; the rest has no drawn exterior face
    assert s["drawn_in_row74_m2"] == pytest.approx(0.298259 * 4.20 + 0.298259 * 1.10 + 0.498259 * 0.20, abs=1e-6)
    assert s["no_exterior_face_m2"] + s["drawn_in_row74_m2"] == pytest.approx(54.45)


def test_bound_faces_carry_t337_values_and_new_keys_are_new():
    b = T.t337_rows()
    for r in rows("FACES_T348.csv"):
        if r["bound_to_t337"] == "NEW":
            assert r["key"] not in b
        else:
            assert r["bound_to_t337"] in b
            if not r["before_t337"]:
                assert r["m2_lo"] == b[r["key"]]["lo"] and r["m2_hi"] == b[r["key"]]["hi"]
    keys = [r["key"] for r in rows("FACES_T348.csv")]
    assert len(keys) == len(set(keys))


def test_fill_held_rows_blank_never_zero():
    for r in rows("FILL_T314_T348.csv"):
        if r["status"] in ("HELD", "UNKNOWN", "NOT_A_FACE"):
            assert r["m2"] == ""
        else:
            assert float(r["m2"]) > 0


def test_screen_values_and_parapet_remeasure():
    f = {r["key"]: r for r in rows("FACES_T348.csv")}
    assert float(f["1F/NW-2/PARAPET/parapet"]["m2_lo"]) == pytest.approx(3.059412 * 1.30, abs=1e-6)
    assert f["1F/NW-2/PARAPET/parapet"]["before_t337"] == "HELD 4.223108 .. 4.585300"
    # r2 (R-T348-6): the hole is the inner arch from the DXF handles; both screen faces DRAWING-CONFIRMED
    assert T.R.poly_area(T.ARCH_INNER) == pytest.approx(8.13382, abs=1e-6)
    assert T.R.poly_area(T.ARCH_OUTER) == pytest.approx(8.524556, abs=1e-6)
    for k in ("1F/NW-2/SCREEN-FRONT/storey", "1F/NW-2/SCREEN-BACK/storey"):
        assert f[k]["status"] == "DRAWING-CONFIRMED"
        assert float(f[k]["m2_lo"]) == pytest.approx(3.059412 * 4.20 - 8.13382, abs=1e-6)
    assert float(f["1F/NW-2/SCREEN-INTRADOS/reveal"]["m2_lo"]) == pytest.approx(0.298259 * 7.735694, abs=1e-5)
    assert f["1F/NW-1/SLAB_EDGE_BELOW/slab_edge"]["status"] == "NOT_A_FACE"


def test_arch_handles_listed_once_and_widths_match_the_plan():
    for h, pts, width in ((T.ARCH_INNER_H, T.ARCH_INNER, 3.059412), (T.ARCH_OUTER_H, T.ARCH_OUTER, 3.159412),
                          (T.MOULD2_H, T.MOULD2, 3.959412), (T.MOULD3_H, T.MOULD3, 4.059412)):
        hs = h.split()
        assert len(hs) == len(set(hs)) == len(pts) - 1
        assert pts[-1][0] - pts[0][0] == pytest.approx(width, abs=1e-6)
        assert pts[0][1] == 0.0 and pts[-1][1] == 0.0


def test_r2_pier_faces_beyond_the_ring_keys():
    f = {r["key"]: r for r in rows("FACES_T348.csv")}
    inc = 0.872035 + 0.468504 - 1.170294
    assert float(f["1F/NW-1/CORNER-ARC/storey"]["m2_lo"]) == pytest.approx(inc * 4.20, abs=1e-6)
    assert float(f["1F/NW-1/CORNER-ARC/parapet"]["m2_lo"]) == pytest.approx(inc * 1.30, abs=1e-6)
    assert float(f["1F/NW-3/SW-RETURN/storey"]["m2_lo"]) == pytest.approx(1.252688, abs=1e-6)
    assert float(f["1F/NW-3/SW-RETURN/parapet"]["m2_lo"]) == pytest.approx(0.427737, abs=1e-6)
    for k in ("1F/NW-1/CORNER-ARC/storey", "1F/NW-1/CORNER-ARC/parapet", "1F/NW-3/SW-RETURN/storey",
              "1F/NW-3/SW-RETURN/parapet"):
        assert f[k]["status"] == "DRAWING-CONFIRMED" and f[k]["bound_to_t337"] == "NEW"
    s = json.loads(OUT["summary.json"])
    assert s["pier_outline_closure_m"]["NW-3"] == pytest.approx(0.578 + 2 * 0.298259, abs=1e-6)
    eff = s["t337_line_effects"]
    assert eff["L-8bb83e16cc7b104ab88b (1F exterior storey)"]["added_m2"] == pytest.approx(1.967717, abs=1e-6)
    lo, hi = eff["NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70"]["after"]
    assert lo == pytest.approx(53.550644 - 4.223108 + 3.977236 + 0.221319 + 0.427737, abs=2e-6)
    assert hi - lo == pytest.approx((59.290836 - 53.550644) - (4.5853 - 4.223108), abs=1e-6)


def test_r2_moulding_steps_held_with_their_bound():
    f = {r["key"]: r for r in rows("FILL_T314_T348.csv")}
    r = f["1F/NW-2/SCREEN-MOULDING-STEPS/storey"]
    assert r["status"] == "HELD" and r["m2"] == ""
    assert float(r["m2_hi"]) == pytest.approx(0.05 * 7.89373 + 0.10 * 9.158016 + 0.05 * 9.316052, abs=1e-5)


def test_no_face_shared_with_the_interior_lines():
    s = json.loads(OUT["summary.json"])
    assert s["interior_cross_check"]["overlap_m2"] == 0.0
    assert all(not k.startswith("1F-11") for k in s["new_faces"])
