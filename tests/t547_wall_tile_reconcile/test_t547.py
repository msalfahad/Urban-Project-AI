"""T-547: wet-room wall tile reconciliation, engine vs freelancer, room by room (R-T547-1). Synthetic villa fixture
(not the development villa) with hand arithmetic, adverse cases, and the development-villa table pinned to the
candidate line index and the freelancer's parsed rows (the drawing check is skipped when the private DXF is absent)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t547"))

import t547_inputs as inp  # noqa: E402
from t547_wall_tile_reconcile import ReconcileError, reconcile, net_area  # noqa: E402


def bath(**kw):
    """villa X bathroom 2.40 x 1.80 (face 8.40 m), tile top 3.00, door 0.90 head 2.10, window 0.60 sill 1.50 head 2.10;
    his row 8.50 lm x 2.80. Hand: 8.40 x 3.00 = 25.20 - 0.90 x 2.10 (1.89) - 0.60 x 0.60 (0.36) = 22.95 m2."""
    r = {"kind": "VALUED", "room": "X bath", "line_id": "L-x", "line": "22.95", "his_len": "8.50", "his_h": "2.80",
         "face": "8.40", "H": "3.00", "open_lm": "0", "h_basis": "villa X rule height", "face_basis": "printed 240 x 180",
         "openings": [{"id": "D1", "kind": "door", "w": "0.90", "sill": "0", "head": "2.10"},
                      {"id": "W1", "kind": "window", "w": "0.60", "sill": "1.50", "head": "2.10"}]}
    r.update(kw)
    return r


def run(rows, eng, fl):
    return reconcile(rows=rows, engine_total=eng, freelancer_total=fl)


# ---- fixture: one bathroom with a door and a window, hand net tile ----

def test_fixture_hand_net_and_exact_split():
    res = run([bath()], "22.95", "23.80")
    row = res["rows"][0]
    assert Decimal(res["gap"]) == Decimal("-0.85") and Decimal(res["residual"]) == 0
    parts = {c["name"].split(":")[0]: Decimal(c["delta"]) for c in row["components"]}
    assert parts["length"] == Decimal("-0.28")          # (8.40 - 8.50) x 2.80
    assert parts["height"] == Decimal("1.68")           # 8.40 x (3.00 - 2.80)
    assert parts["doors / arches deducted (he deducts none)"] == Decimal("-1.89")
    assert parts["windows inside the band (he deducts none)"] == Decimal("-0.36")


def test_window_above_the_band_deducts_only_its_part_inside():
    n, d, w = net_area("8.40", "2.00", [{"kind": "window", "w": "0.60", "sill": "1.50", "head": "2.10"}])
    assert w == Decimal("0.30") and n == Decimal("16.50")


def test_mirror_and_opening_order_invariance():
    a = run([bath()], "22.95", "23.80")
    b = run([bath(openings=list(reversed(bath()["openings"])))], "22.95", "23.80")
    assert a["by_cause"] == b["by_cause"]


# ---- adverse ----

def test_opening_not_deducted_is_refused():
    with pytest.raises(ReconcileError, match="opening not deducted"):
        run([bath(line="25.20")], "25.20", "23.80")


def test_foreign_or_stale_line_value_refused():
    with pytest.raises(ReconcileError, match="stale or foreign"):
        run([bath(line="23.40")], "23.40", "23.80")


def test_millimetre_height_refused():
    with pytest.raises(ReconcileError, match="millimetre"):
        run([bath(H="3000")], "22.95", "23.80")


def test_unknown_head_without_range_refused():
    ops = [{"id": "A", "kind": "arch", "w": "1.0", "sill": "0", "head": None}]
    with pytest.raises(ReconcileError, match="never 0"):
        run([bath(openings=ops, line="25.20")], "25.20", "23.80")


def held(**kw):
    r = {"kind": "HELD", "room": "X held", "line_id": "L-h", "line": None, "his_len": "6.0", "his_h": "3",
         "face": "6.0", "openings": [{"id": "D", "kind": "door", "w": "0.8", "sill": "0", "head": "2.20"}],
         "bound_lo": {"H": "2.20", "source": "head floor"}, "bound_hi": {"H": "3.00", "source": "owner upper"},
         "held_fact": "level not drawn"}
    r.update(kw)
    return r


def test_held_is_never_zero_and_carries_its_bound():
    res = run([bath(), held()], "22.95", "41.80")
    h = res["rows"][1]
    assert h["engine"] is None and h["delta"] == "-18.0" and h["components"][0]["cause"] == "HELD"
    assert (h["bound"]["lo"], h["bound"]["hi"]) == ("11.440", "16.240")   # 13.20 - 1.76 ; 18.00 - 1.76
    for bad in ("0", "0.0", "5"):
        with pytest.raises(ReconcileError, match="HELD line with a value"):
            run([held(line=bad)], "0", "18")


def test_bound_without_source_or_inverted_refused():
    with pytest.raises(ReconcileError, match="without a source"):
        run([held(bound_hi={"H": "3.00", "source": ""})], "0", "18")
    with pytest.raises(ReconcileError, match="lo .* > hi"):
        run([held(bound_lo={"H": "3.00", "source": "a"}, bound_hi={"H": "2.20", "source": "b"})], "0", "18")


def test_scope_row_needs_a_rule_not_tolerance():
    with pytest.raises(ReconcileError, match="scope row"):
        run([{"kind": "SCOPE", "room": "p", "line_id": "L", "line": "3", "cause": "TOLERANCE", "basis": "x"}], "3", "0")


def test_stale_totals_refused():
    with pytest.raises(ReconcileError, match="stale total"):
        run([bath()], "23.00", "23.80")
    with pytest.raises(ReconcileError, match="printed total"):
        run([bath()], "22.95", "24.00")


# ---- development villa ----

RES = run(inp.rows(), inp.ENGINE_TOTAL, inp.FREELANCER_TOTAL)


def test_dev_villa_table_sums_exactly():
    assert RES["gap"] == "-93.5262" and RES["gap_pct"] == "-21.56" and RES["residual"] == "0.0000"
    bc = {k: Decimal(v) for k, v in RES["by_cause"].items()}
    assert bc == {"HELD": Decimal("-138.39"), "RULE_DIFFERENCE": Decimal("75.5356"),
                  "ENGINE_RIGHT": Decimal("-30.672"), "TOLERANCE": Decimal("0.0002")}
    assert RES["held_bound_total"] == {"lo": "102.2085", "hi": "144.1735"}
    assert (RES["engine_with_held_bounds"]["lo_pct"], RES["engine_with_held_bounds"]["hi_pct"]) == ("2.00", "11.67")


def test_dev_villa_like_for_like_and_causes():
    valued = [r for r in RES["rows"] if r["state"] == "VALUED"]
    assert len(valued) == 11
    e = sum(Decimal(r["engine"]) for r in valued)
    f = sum(Decimal(r["freelancer"]) for r in valued)
    assert (e, f) == (Decimal("307.9616"), Decimal("295.44"))
    comp = {}
    for r in valued:
        for c in r["components"]:
            k = c["name"].split(":")[0].split(" (")[0]
            comp[k] = comp.get(k, Decimal(0)) + Decimal(c["delta"])
    assert comp["height"] == Decimal("43.19340") and comp["open side, no wall, no tile"] == Decimal("-3.735")
    assert comp["length"] == Decimal("1.083") and comp["doors / arches deducted"] == Decimal("-23.100")
    assert comp["windows inside the band"] == Decimal("-4.92")


def test_dev_villa_lines_are_the_candidate_lines():
    idx = json.loads((ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json").read_text())
    lines = {l["line_id"]: l for l in idx["lines"] if l["item_code"] == "FIN.WALL.TILE"}
    assert len(lines) == 18
    for r in RES["rows"]:
        ln = lines[r["line_id"]]
        if r["state"] == "HELD":
            assert ln["class"] == "HELD" and ln["measured_net"] is None
        else:
            assert Decimal(repr(ln["measured_net"])) == Decimal(r["engine"])


def test_dev_villa_freelancer_cells_are_his_rows():
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text())
    sheet = {r["row"]: r["cells"] for r in raw["rows"] if r["file"] == "FIN" and r["sheet"] == "سيراميك"}
    assert sheet[66]["G66"]["v"] == 433.83 and sheet[72]["H72"]["v"] == 433.83 and sheet[72]["I72"]["v"] == "م2"
    rows = {r["room"]: r for r in inp.rows()}
    used = set()
    for name, r in rows.items():
        if r["kind"] == "SCOPE":
            continue
        c = sheet[r["his_row"]]
        n = r["his_row"]
        assert Decimal(repr(c[f"C{n}"]["v"])) == Decimal(r["his_len"]) and c[f"F{n}"]["v"] == 3
        used.add(n)
    assert used == {42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 55, 56, 57, 58, 59, 60, 63}


DXF = Path(os.environ.get("T547_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_dev_villa_held_room_sizes_from_the_printed_dimensions():
    ezdxf = pytest.importorskip("ezdxf")
    db = ezdxf.readfile(str(DXF)).entitydb
    for room, dims in inp.PRINTED_DIMS.items():
        for h, mm in dims:
            assert round(db[h].get_measurement()) == mm, (room, h)
    faces = {r["room"][:5]: Decimal(r["face"]) for r in inp.rows() if r["kind"] == "HELD"}
    for room in ("GF-10", "GF-11", "GF-05", "GF-03", "GF-02"):
        a, b = (Decimal(mm) / 1000 for _h, mm in inp.PRINTED_DIMS[room])
        assert 2 * (a + b) == faces[room], room
    # the kitchen's 14.50 m face is the T-312 walk (300 x 270 + 105 x 150 with drawn piers); only its printed sizes
    # are re-read here, its perimeter is not a rectangle formula (named in the report, not asserted)
