"""T-305 on the development villa: the committed ledger rebuilds byte for byte from merged ledgers + the committed
candidate extract (own V3.0.18 run, json ec741004 / csv af577422) and the two glazing bindings; no drawing needed."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t305"
sys.path.insert(0, str(HERE))
import t305_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def files():
    return A.outputs()


@pytest.fixture(scope="module")
def summ(files):
    return json.loads(files["summary.json"])


def rows(files, name):
    return list(csv.DictReader(files[name].splitlines()))


def test_rebuild_byte_identical(files):
    for n, t in files.items():
        assert (HERE / n).read_text(encoding="utf-8") == t, n


def test_candidate_identity_is_the_record(summ):
    c = summ["candidate"]
    assert (c["lines_json_sha256_8"], c["lines_csv_sha256_8"], c["lines_total"]) == ("ec741004", "af577422", 3705)


def test_every_drawn_face_once_residual_zero(summ, files):
    f = summ["faces"]
    assert f["residual_measured_vs_t159_csv_m2"] == 0.0
    assert f["measured_m2"] == pytest.approx(1022.5337, abs=1e-6)
    assert f["held_m2"] == pytest.approx([6.822226, 13.261431], abs=1e-6)
    keys = [(r["floor"], r["side"], r["portion"], r["bottom_m"], r["top_m"]) for r in rows(files, "FACE_LINE_LEDGER_T305.csv")]
    assert len(keys) == len(set(keys)) == 98
    st = summ["by_ledger_state"]
    assert st["IN_LINE"]["m2"] + st["NO_LINE"]["m2"] == pytest.approx(f["measured_m2"], abs=1e-6)


def test_in_line_faces_by_floor_and_formula_check(summ):
    by = {x["line_or_cause"]: x for x in summ["by_state_and_line"]}
    assert by["L-b05f70c92405dbcfbe62"]["m2"] == pytest.approx(479.9202, abs=1e-6)   # GF finish line
    assert by["L-8bb83e16cc7b104ab88b"]["m2"] == pytest.approx(265.3093, abs=1e-6)   # 1F
    assert by["L-d52c4f763b19aedf8b8b"]["m2"] == pytest.approx(140.06, abs=1e-6)     # 2F
    fx = summ["formula_run_x_h"]
    # GF: the passage face P-1 (4.70 m) and the covered annex strip of SW-3 (0.20 m) stand on the +0.30 annex F.F.L.:
    # 4.90 x 0.70 = 3.430 m2 more than run x 4.50 (T-159 areas at 4 decimals)
    assert fx["GF"]["difference_m2"] == pytest.approx(4.9 * 0.70, abs=2e-4)
    assert abs(fx["1F"]["difference_m2"]) < 2e-4 and fx["2F"]["difference_m2"] == 0.0


def test_no_line_parts_named_never_zero(summ):
    by = {x["line_or_cause"]: x for x in summ["by_state_and_line"]}
    assert by["parapet outer face above the next F.F.L."]["m2"] == pytest.approx(66.4279, abs=1e-6)
    assert by["plinth"]["m2"] == pytest.approx(66.7363, abs=1e-6)
    assert by["a face standing on a lower roof, below its own floor's F.F.L"]["m2"] == pytest.approx(4.08, abs=1e-9)
    assert by["slab edge over open air"]["slab_edge_m"] == pytest.approx(13.0789, abs=1e-6)


def test_openings_each_once_by_hole_never_the_window_measure(files):
    op = rows(files, "OPENING_HOLES_T305.csv")
    ids = [r["opening"] for r in op if not r["opening"].startswith("none") and "frame end" not in r["opening"]]
    assert len(ids) == len(set(ids)) == 36
    w17 = next(r for r in op if r["opening"] == "W17")
    assert float(w17["deduct_fixed_m2"]) == pytest.approx(8.1434) and float(w17["window_measure_m2"]) == 9.87
    w18 = next(r for r in op if r["opening"] == "W18")
    assert float(w18["deduct_fixed_m2"]) == pytest.approx(0.467302 * 2.16, abs=1e-6)
    held = {r["opening"]: r for r in op if r["deduct_status"] == "HELD"}
    assert set(held) == {"W02", "D-GF-07"} and all(r["deduct_fixed_m2"] == "" for r in held.values())


def test_line_nets(summ):
    L = {x["floor"]: x for x in summ["lines"]}
    assert (L["GF"]["net_lo_m2"], L["GF"]["net_hi_m2"]) == pytest.approx((387.285171, 420.770171), abs=1e-6)
    assert L["1F"]["net_hi_m2"] == pytest.approx(234.525528, abs=1e-6)
    assert L["2F"]["net_hi_m2"] == pytest.approx(132.205, abs=1e-6)
