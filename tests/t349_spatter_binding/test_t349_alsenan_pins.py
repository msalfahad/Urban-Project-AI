"""T-349 development-villa pins (read-only over merged ledgers; no drawing is read): the committed CSVs are what the
builder produces, every bound figure closes on its candidate line / T-337 line, HELD stays blank or a range (never 0)."""

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t349"
sys.path.insert(0, str(HERE))
import t349_alsenan as A  # noqa: E402

OA = "ASSUMED — OWNER-APPROVED"


@pytest.fixture(scope="module")
def out():
    return A.outputs()


def rows_of(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_committed_outputs_reproduce(out):
    for name, text in out.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_one_face_once_and_every_row_bound(out):
    rows = rows_of(out["SPATTER_BINDING_T349.csv"])
    assert len(rows) == len({r["face_id"] for r in rows})            # double count 0
    assert all(r["target"] for r in rows)
    assert Counter(r["family"] for r in rows) == {"EXT_FACE": 109, "INT_WET_FACE": 105, "INT_DRY_LINE": 36,
                                                   "EXT_ITEM": 11, "INT_WET_RESIDUAL": 10}


def test_interior_determinate_equals_the_live_plaster_family(out):
    s = json.loads(out["summary.json"])
    assert s["interior"][OA]["m2"] == 575.2519                       # = FIN.PLASTER live V3.0.22 / V3.0.24 (T-331)
    assert (s["interior"]["HELD"]["lo"], s["interior"]["HELD"]["hi"]) == (489.481, 545.4606)


def test_hand_checks():
    rows = {r["face_id"]: r for r in rows_of((HERE / "SPATTER_BINDING_T349.csv").read_text(encoding="utf-8"))}
    # GF-13 backing faces: 6.81 m contour x 3.65 - D-GF-12 1.760 - W06 0.480 = 22.6165 (T-331 hand check)
    gf13 = [r for r in rows.values() if r["target"] == "L-302f7235046bbe0b6c09"]
    assert round(sum(float(r["m2"]) for r in gf13), 4) == 22.6165
    assert all(r["via"] == "L-a3cb2c8a9b6080769ebc" for r in gf13)        # the tile line named as via only
    # 1F storey face NE-2: the T-337 face 80.934 less W19 0.480, W20 0.480, W24 2.325 (OPENINGS_T337) = 77.649
    ne2 = rows["1F/NE-2/STOREY/storey"]
    b = {r["key"]: r for r in csv.DictReader(open(ROOT / "research/agents_t337/BINDING_T337.csv", encoding="utf-8"))}
    assert float(b["1F/NE-2/STOREY/storey"]["lo"]) == 80.934
    assert float(ne2["m2"]) == pytest.approx(80.934 - 0.48 - 0.48 - 2.325, abs=1e-6)
    # W02 face GF NW-7: the held hole 0 .. 28.485 keeps the face a range, never a point value
    nw7 = rows["GF/NW-7/EDGE/storey"]
    assert nw7["state"] == "HELD" and nw7["m2"] == "" and float(nw7["hi"]) - float(nw7["lo"]) == pytest.approx(28.485)


def test_fill_held_blank_never_zero(out):
    fill = rows_of(out["FILL_T349.csv"])
    for f in fill:
        if f["status"].startswith(("HELD", "UNKNOWN")):
            assert f["quantity"] == "", f
            if f["lo"]:
                assert float(f["hi"]) > 0
        if f["quantity"] != "":
            assert float(f["quantity"]) > 0, f
    pend = [f for f in fill if f["family"] == "PENDING"]
    assert round(sum(float(f["quantity"]) for f in pend if f["quantity"]), 4) == 13.597   # T-340: 9.667 + 3.930


def test_closure_on_t317(out):
    c = rows_of(out["CLOSURE_T349.csv"])
    hosts = [r for r in c if r["t317_item"] in ("FIN.PLASTER", "FIN.WALL.TILE")]
    moved = [r for r in hosts if r["delta_m2"] not in ("+0.000000", "-0.000000", "lo +0.000000 / hi +0.000000")]
    assert {r["t317_host"]: r["delta_m2"] for r in moved} == {
        "L-721a0f1441436193978c": "+32.342200",                         # the pantry fill (T-331)
        "L-31db3c83552682d92ca3": "lo -0.000050 / hi -0.000050"}         # 6-dp constant vs the 4-dp line
    s = json.loads(out["summary.json"])["line_level"]
    # T-317 exterior determinate 370.8105 -14.900 (2F band) -4.080 (lower-roof face into the GF HELD line)
    # +14.385 / +14.900 (GF / 2F parapet outer DC) +5.415 (2F parapet top) = 386.5305
    assert s["EXT"]["determinate"] == pytest.approx(370.8105 - 14.9 - 4.08 + 14.385 + 14.9 + 5.415, abs=1e-4)


def test_edited_ledger_stops_the_build(monkeypatch):
    real = A.rd

    def edited(p):
        rows = real(p)
        if str(p).endswith("BACKING_FACE_LEDGER_T329.csv"):
            rows[0] = dict(rows[0], backing_owner_m2="6.5713")          # 0.1 m2 more on one backing face
        return rows

    monkeypatch.setattr(A, "rd", edited)
    with pytest.raises(A.B.BindError, match="!= host"):
        A.build()
