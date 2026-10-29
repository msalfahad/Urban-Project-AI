"""T-324 on the development villa: the committed ledgers rebuild byte for byte from merged ledgers (T-311, T-305,
T-172) and MEASURED_T324.json (entity lengths only); no drawing needed. Pins ownership, closures and HELD handling."""
import csv
import io
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t324"
sys.path.insert(0, str(HERE))
import t324_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    B, corr, geo, _ = A.build()
    return B, corr, geo, A.render(B, corr, geo)


def _rows(files, name):
    return list(csv.DictReader(io.StringIO(files[name])))


def test_rebuild_byte_identical(built):
    for n, t in built[3].items():
        assert (HERE / n).read_text(encoding="utf-8") == t, n


def test_every_component_once_and_each_physical_item_once(built):
    rows = _rows(built[3], "COMPONENT_LEDGER_T324.csv")
    keys = [r["component_id"] for r in rows]
    assert len(keys) == len(set(keys))
    edges = [r["physical_item"] for r in rows if r["physical_item"]]
    assert len(edges) == len(set(edges))


def test_held_never_zero_unknown_has_no_number(built):
    for r in _rows(built[3], "COMPONENT_LEDGER_T324.csv"):
        if r["status"] == "UNKNOWN":
            assert r["qty_lo"] == r["qty_hi"] == ""
        if r["status"] == "HELD":
            assert r["qty_hi"] != "" and float(r["qty_hi"]) > 0


def test_upturn_lengths_close_on_the_roof_level_faces(built):
    s = json.loads(built[3]["summary.json"])["components"]
    # lower bound = the drawn inner faces (to the D bands / divider): T-321's independent roof-level face reading
    assert round(s["UPTURN_ML|ANNEX"][0], 3) == 29.628
    assert round(s["UPTURN_ML|GF"][0], 3) == 27.365       # T-321: parapet 26.470 + gate stub 0.894 (SW-9 drawn)
    assert round(s["UPTURN_ML|GF"][1], 3) == 27.770       # + the 0.406 D-band part (T-321 'door closure')
    assert round(s["UPTURN_ML|ANNEX|GF"][0], 3) == 2.600  # the divider, 1.300 on each roof
    assert round(s["UPTURN_ML|1F"][0], 3) == 48.265
    assert round(s["UPTURN_ML|2F"][0], 3) == 28.300


def test_sea_side_chord_equals_the_drawn_straight_inner_face(built):
    corr = {c["id"]: c for c in built[1]}
    assert round(corr["C3"]["delta_lo"], 4) == -0.4435
    geo = built[2]
    run = sum(geo[("1F", s)]["inner_hi"] for s in ("NW-1", "NW-2", "NW-3", "NW-4", "NW-5"))
    assert round(run, 6) == 11.6


def test_b34_extension_booked_once_outer_face_held(built):
    rows = {r["component_id"]: r for r in _rows(built[3], "COMPONENT_LEDGER_T324.csv")}
    assert float(rows["ANNEX/NE-6x/INNER_TOP_ARRIS"]["qty_lo"]) == pytest.approx(1.4)
    assert float(rows["ANNEX/NE-6x/TOP_SURFACE"]["qty_lo"]) == pytest.approx(0.26, abs=1e-4)
    assert rows["ANNEX/NE-6x/OUTER_FACE"]["status"] == "HELD"


def test_vertical_arrises_stay_in_the_facade_corner_line(built):
    rows = [r for r in _rows(built[3], "COMPONENT_LEDGER_T324.csv") if r["component"] == "VERTICAL_ARRIS_PARAPET_PART"]
    assert len(rows) == 1 and rows[0]["state"] == "OTHER_LINE" and float(rows[0]["qty_lo"]) == pytest.approx(4.0)


def test_reconciliation_names_every_delta(built):
    for r in _rows(built[3], "RECONCILIATION_T324.csv"):
        if abs(float(r["delta_lo"])) > 1e-6 or abs(float(r["delta_hi"])) > 1e-6:
            assert r["named_causes"]


def test_no_coordinates_or_client_text_in_measured_json():
    m = json.loads((HERE / "MEASURED_T324.json").read_text(encoding="utf-8"))
    for v in m["handles"].values():
        assert set(v) == {"layer", "length_m", "what"}
