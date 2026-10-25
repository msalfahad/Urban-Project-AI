"""T-292 on the development villa: the committed ledger rebuilds byte for byte from the merged research ledgers and the
extracted candidate lines, and its closures hold (no drawing needed: the candidate json is the extract of an own
V3.0.15 run, csv a4dc01dd)."""
import csv
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t292"
sys.path.insert(0, str(HERE))
import t292_alsenan as A      # noqa: E402
import t292_face_line_rules as L  # noqa: E402


@pytest.fixture(scope="module")
def files():
    return A.outputs()


def rows(files, name):
    return list(csv.DictReader(files[name].splitlines()))


def test_rebuild_byte_identical(files):
    for n, t in files.items():
        assert (HERE / n).read_text(encoding="utf-8") == t, n


def test_candidate_identity():
    c = A.candidate()
    assert c["csv_sha256_8"] == "a4dc01dd" and c["lines_total"] == 3699
    assert len(c["wall_finish_lines"]) == 132


def test_every_line_once_and_every_room_closed(files):
    ls = rows(files, "LINE_SUMMARY_T292.csv")
    assert len(ls) == 132 == len({r["line_id"] for r in ls})
    s = json.loads(files["summary.json"])
    assert s["rooms"] == 32 and s["room_length_residual_max_m"] == 0.0
    for code, c in s["closure_faces_vs_lines"].items():
        assert c["residual_lo"] == 0.0 and c["residual_hi"] == 0.0, code
    assert s["line_residual_max_abs_m2"] <= 0.0005
    rep = s["t237_room_reproduction"]
    # r2: 20 of 21 rooms = T-237 part 4; 1F-11 differs by W17 only, named (Q-76 A crown, springing bound)
    assert rep["rooms"] == 21 and rep["ok"] == 20 and rep["differs_unexplained"] == 0
    assert [d["room"] for d in rep["differs"]] == ["1F-11"] and "Q-76 A" in rep["differs"][0]["named_cause"]


def test_each_face_once_per_item_and_owner_rules(files):
    fr = rows(files, "FACE_TO_LINE_LEDGER_T292.csv")
    keys = [(r["face_id"], r["item_code"]) for r in fr]
    assert len(keys) == len(set(keys))
    for r in fr:
        if r["finish_class"] == "WET":
            assert r["item_code"] in (L.TILE, L.PLASTER)          # a tiled face is not painted
            if r["item_code"] == L.PLASTER:
                assert r["owner_status"] == L.HELD and r["owner_net_lo_m2"] == ""
        if r["owner_status"] == L.HELD:
            assert r["owner_net_lo_m2"] == "" and r["owner_held_item"]
        if r["owner_status"] == L.VERIFIED:
            assert r["verified_by"] and r["room"] in ("GF-15", "1F-11")
        assert r["length_source"] == "DRAWN"


def test_roof_datum_faces_held_blank_in_the_drawing_method(files):
    fr = rows(files, "FACE_TO_LINE_LEDGER_T292.csv")
    roof = [r for r in fr if r["roof_datum_face"] == "yes"]
    assert len({r["face_id"] for r in roof}) == 16            # 18 T-237 faces less the two without a straight face
    for r in roof:
        assert r["dwg_status"] == L.HELD and r["dwg_net_m2"] == "" and "D-39" in r["dwg_held_item"]


def test_named_line_moves(files):
    ls = {r["line_id"]: r for r in rows(files, "LINE_SUMMARY_T292.csv")}
    # 1F-04: W24 head now DRAWING-CONFIRMED (T-201): 49.1375 .. 54.33 -> 52.0051 determinate
    r = ls["L-971f0bdaf68d7fd0966c"]
    assert (r["line_lo_m2"], r["line_hi_m2"], r["ledger_owner_lo_m2"], r["ledger_owner_hi_m2"]) == \
        ("49.1375", "54.3300", "52.0051", "52.0051")
    # 1F-11: the line releases W17 at 3.286 x 3.35 = 11.0081; r2 (Q-76 A crown 3.00, UP-OPEN-ARCH-001 true outline):
    # the developed arched hole lies between 3.286 x 1.350 = 4.4361 and 3.286 x 3.000 = 9.858 -> the W17 piece nets
    # 11.0081 - 9.858 = 1.1501 .. 11.0081 - 4.4361 = 6.5720; 8 VERIFIED faces 59.4510 + piece = 60.6011 .. 66.0230
    for lid in ("L-31db3c83552682d92ca3", "L-349db74a70e1eecda2d2"):
        r = ls[lid]
        assert r["line_lo_m2"] == "59.4511" and (r["ledger_owner_lo_m2"], r["ledger_owner_hi_m2"]) == ("60.6011", "66.0230")
    assert 60.6011 - 59.4511 > 1.149                           # the released line is low even at the ledger's lo end
    fr = {(r["face_id"], r["item_code"]): r for r in rows(files, "FACE_TO_LINE_LEDGER_T292.csv")}
    g = fr[("1F-11|OFF:GLAZING", L.PLASTER)]
    assert (g["owner_net_lo_m2"], g["owner_net_hi_m2"]) == ("1.1501", "6.5720") and "Q-76 A" in g["owner_held_item"]
    # the Q-76 A WINDOW area (3.29 x 3.00 = 9.870) is never the finish deduction (RECTANGLE_FOR_MASONRY)
    assert abs((11.0081 - float(g["owner_net_lo_m2"])) - 3.29 * 3.00) > 0.005
    # the pantry paint line holds no face (GF-07 is WET)
    assert ls["L-c3f7e68ce91a436802e2"]["ledger_state"].startswith("UNMATCHED_LINE: holds no face")


def test_no_coordinates_in_outputs(files):
    for n, t in files.items():
        assert not re.search(r"-?\d{4,}\.\d{2,}", t), n        # no drawing coordinates (only m / m2 figures)
