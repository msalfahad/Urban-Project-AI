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
    assert total == pytest.approx(109.89, abs=1e-6)
    assert s["no_exterior_face_m2"] == pytest.approx(54.45)


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
    assert float(f["1F/NW-2/PARAPET/parapet"]["m2_lo"]) == pytest.approx(3.0594 * 1.30)
    assert f["1F/NW-2/PARAPET/parapet"]["before_t337"] == "HELD 4.223108 .. 4.585300"
    assert float(f["1F/NW-2/SCREEN-FRONT/storey"]["m2_lo"]) == pytest.approx(12.84948 - 8.525649, abs=1e-5)
    assert float(f["1F/NW-2/SCREEN-FRONT/storey"]["m2_hi"]) == pytest.approx(12.84948 - 8.134744, abs=1e-5)
    assert f["1F/NW-1/SLAB_EDGE_BELOW/slab_edge"]["status"] == "NOT_A_FACE"


def test_no_face_shared_with_the_interior_lines():
    s = json.loads(OUT["summary.json"])
    assert s["interior_cross_check"]["overlap_m2"] == 0.0
    assert all(not k.startswith("1F-11") for k in s["new_faces"])
