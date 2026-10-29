"""T-339 on the development villa (research/agents_t339): byte rebuild of the committed tables, every roof x layer bound
once, held never 0, closures named, nothing shared with the parapet rows, and the measurement re-read from the private
drawing when it is present (Drive 'Alsenan chalet project' P7757.dxf; never committed)."""
import csv
import io
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t339"
sys.path.insert(0, str(D))
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
import t339_alsenan as T   # noqa: E402
import t339_binding as B   # noqa: E402


def _csv_text(rows):
    buf = io.StringIO()
    keys = list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r[k] is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k])) for k in keys})
    return buf.getvalue()


@pytest.fixture(scope="module")
def built():
    return T.build()


def test_byte_rebuild(built):
    rows, clo, xc, fl, summ = built
    for name, data in (("BINDING_T339.csv", rows), ("CLOSURE_T339.csv", clo), ("CROSSCHECK_T339.csv", xc),
                       ("FILL_T328_T339.csv", fl)):
        assert (D / name).read_text(encoding="utf-8") == _csv_text(data), name
    assert json.loads((D / "summary.json").read_text(encoding="utf-8")) == json.loads(json.dumps(summ))


def test_every_roof_layer_once_and_held_blank(built):
    rows = built[0]
    assert B.check_bindings(rows)
    assert len(rows) == 24 and {r["roof"] for r in rows} == {"ROOF-430", "TERRACE-550", "ROOF-970", "ROOF-1390"}
    for r in rows:
        if r["status"] in ("HELD", "UNKNOWN"):
            assert r["quantity_lo"] is None and r["quantity_hi"] is None
        if r["roof"] == "ROOF-1390":
            assert r["status"] == "HELD" and r["area_lo"] is None and r["quantity_lo"] is None
        if r["layer"] == "FALLS_SCREED":
            assert r["unit"] == "m3" and r["quantity_lo"] is None and r["new_row"].startswith("B13-01 ROOF SCREED")
        if r["layer"] in ("INSULATION", "PROTECTION") and r["roof"] != "ROOF-1390":
            assert r["status"] == "UNKNOWN" and r["area_lo"] is None


def test_existing_lines_are_the_v3022_roof_wp_lines_unchanged(built):
    rows = built[0]
    cand = {l["line_id"]: l for l in json.loads(T.T342_CAND.read_text(encoding="utf-8"))["lines"]}
    bound = {r["line_id"]: r for r in rows if r["line_id"]}
    assert len(bound) == 8
    for lid, r in bound.items():
        assert cand[lid]["item_code"] == B.ITEM[r["layer"]] and cand[lid]["element_id"].startswith(r["element_id"])
        assert r["line_quantity"] == cand[lid]["quantity"]
    # AT385 is the same face as AT379 (T-342): bound through AT379's lines, never a second roof
    assert {r["element_id"] for r in rows if r["roof"] == "ROOF-970"} == {"2F-ROOF-AT379"}


def test_edges_inside_the_parapet_inner_face_and_closures(built):
    rows, clo, xc, _, summ = built
    assert summ["closures_close"] and all(c["closes"] for c in clo)
    assert summ["shared_with_parapet_m2"] < 1e-5   # the annex hatch arc flattening, 0.000002 m2
    r = summ["roofs"]
    # hand: slab zone = face + parapet footprint (+ named): ROOF-1390 8.10 x 6.80 = 7.70 x 6.45 + 5.415
    assert abs(r["ROOF-1390"]["outer_m2"] - 8.10 * 6.80) < 1e-9 and abs(r["ROOF-1390"]["footprint_m2"][0] - 5.415) < 1e-9
    # hand: terrace zone = 19.17 x 1.50 (boundary strip incl. the parapet) + 1.50 x 6.40 (east arm) = 38.355
    assert abs(r["TERRACE-550"]["outer_m2"] - (19.17 * 1.50 + 1.50 * 6.40)) < 1e-9
    # hand: 1F roof zone = 19.27 x 12.00 - the 2F block 6.77 x 6.80 (x 12.30 .. 19.07 is roof) ... by parts:
    # south band 19.27 x 5.20 + east arm 6.77 x 6.80 + west arm 4.40 x 2.30 = 100.204 + 46.036 + 10.12 = 156.36
    assert abs(r["ROOF-970"]["outer_m2"] - (19.27 * 5.20 + 6.77 * 6.80 + 4.40 * 2.30)) < 1e-9
    for rid in ("ROOF-430", "TERRACE-550", "ROOF-970"):
        fo = r[rid]
        assert fo["face_m2"][1] < fo["outer_m2"] - fo["footprint_m2"][0] + 1e-4
    # F-T339-1: the terrace face layers are a range to the D band like the other two roofs
    assert r["TERRACE-550"]["face_m2"] == [31.643, 32.721]
    fin = {x["roof"]: x["quantity_lo"] for x in rows if x["layer"] == "FINISH"}
    assert round(fin["ROOF-430"], 4) == 54.9203 and round(fin["TERRACE-550"], 4) == 31.643
    assert round(fin["ROOF-970"], 3) == 115.656 and fin["ROOF-1390"] is None


def test_fill_table_one_row_per_binding(built):
    rows, _, _, fl, _ = built
    assert len(fl) == len(rows)
    assert sum(1 for f in fl if f["action"].startswith("UNCHANGED")) == 8
    assert all(f["quantity_lo"] is None for f in fl if f["status"] in ("HELD", "UNKNOWN"))


def test_measurement_matches_the_drawing():
    dxf = os.environ.get("T339_P7757_DXF") or str(ROOT.parent / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf")
    if not Path(dxf).is_file():
        pytest.skip("private drawing not present (set T339_P7757_DXF to Drive 'Alsenan chalet project' P7757.dxf)")
    import t339_measure as M
    got = json.loads(json.dumps(M.measure(dxf), sort_keys=True))
    assert got == json.loads((D / "MEASURED_T339.json").read_text(encoding="utf-8"))
