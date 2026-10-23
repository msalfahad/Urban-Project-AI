"""T-225: wall register v1, three-way sources, gap reconstruction, before-coverage.

Fixture villa T225-F (NOT Alsenan), hand truth (m2):
  W1  0.15 BLACK, gross 10.000 DRAWING-CONFIRMED, door 1.00 x 2.00 = 2.000 deducted -> net 8.000 DRAWING-CONFIRMED
  W2  0.15 BLACK, gross 12.000 HELD (member above not printed), door 0.75 x 2.00 = 1.500 booked on it -> net HELD
  W3  0.15 BLACK, gross 6.000 DRAWING-CONFIRMED, window head not drawn -> net HELD, nothing deducted
  Established net = 8.000 (W2's 1.500 never reduces it). Established gross - all deductions = 16.000 - 3.500 = 12.500,
  which is NOT a net: gap 4.500 = W3 gross 6.000 - 0 - W2's 1.500.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t225"
sys.path.insert(0, str(HERE))

import build_t225 as B      # noqa: E402
import register_v1 as RV    # noqa: E402


def _csv(path):
    return list(csv.DictReader(Path(path).open(encoding="utf-8")))


def row(rid, gross, gs, ded, net, ns, t="0.15", ty="BLACK", why="", fl="X1"):
    return {"row_id": rid, "floor": fl, "t_m": t, "block_type": ty, "gross_m2": gross, "gross_status": gs,
            "deducted_m2": ded, "net_m2": net, "net_status": ns, "hold_reason": why}


FIX = [
    row("W1", "10.000", "DRAWING-CONFIRMED", "2.000", "8.000", "DRAWING-CONFIRMED"),
    row("W2", "12.000", "HELD", "1.500", "", "HELD", why="beam BX depth not established (not printed)"),
    row("W3", "6.000", "DRAWING-CONFIRMED", "0.000", "", "HELD", why="held opening(s): WX"),
]


# ---------------------------------------------------------------- fixture (not Alsenan): normal and adverse cases
def test_fixture_net_ignores_deductions_on_held_walls():
    t = RV.totals(FIX)[("X1", "0.15", "BLACK")]
    assert t["net DRAWING-CONFIRMED"] == pytest.approx(8.0)
    assert t["deductions on net HELD"] == pytest.approx(1.5)
    g = RV.gap(FIX)
    assert g["established_gross"] - g["all_deductions"] == pytest.approx(12.5)    # the naive figure ...
    assert g["established_net"] == pytest.approx(8.0)                            # ... is not the net
    assert g["gap"] == pytest.approx(4.5) and g["reconstructed"] == pytest.approx(4.5)
    assert g["deductions_on_held_gross"] == [("W2", 1.5)]
    assert g["gross_of_established_gross_held_net"] == [("W3", 6.0)]


def test_fixture_adverse_rows_refused():
    bad = dict(FIX[1], net_m2="10.500", net_status="DRAWING-CONFIRMED")         # net on a HELD gross
    with pytest.raises(ValueError):
        RV.totals([bad])
    with pytest.raises(ValueError):                                             # a HELD net with a figure
        RV.totals([dict(FIX[2], net_m2="6.000")])
    with pytest.raises(ValueError):                                             # net != gross - deductions
        RV.totals([dict(FIX[0], net_m2="10.000")])
    with pytest.raises(ValueError):                                             # unknown status
        RV.totals([dict(FIX[0], net_status="CALCULATED")])
    with pytest.raises(ValueError):                                             # held wall with no named cause
        RV.cause("", "")


def test_fixture_mirror_and_order_invariant():
    a = RV.gap(FIX)
    b = RV.gap(list(reversed(FIX)))
    assert a["gap"] == pytest.approx(b["gap"]) and a["established_net"] == pytest.approx(b["established_net"])


def test_status_classes():
    assert RV.status_class("DRAWING-CONFIRMED") == "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
    assert RV.status_class("ASSUMED — OWNER-APPROVED") == "PROJECT-SPECIFIC"
    assert RV.status_class("UNKNOWN") == "HELD"
    with pytest.raises(ValueError):
        RV.status_class("PROVISIONAL")


# ---------------------------------------------------------------- development villa ledger (Alsenan, reproduction)
def test_committed_files_reproduce():
    assert B.main(["--check"]) == 0


def test_register_sums_equal_t108_r2():
    t108 = _csv(ROOT / "research/agents_t108/T108_BY_WALL.csv")
    reg = _csv(HERE / "BLOCKWORK_WALL_REGISTER_V1.csv")
    assert [r["row_id"] for r in t108] == [r["wall_id"] for r in reg]
    inv = {v: k for k, v in RV.CLASS.items() if k != "UNKNOWN"}
    A, Bt = defaultdict(lambda: defaultdict(float)), defaultdict(lambda: defaultdict(float))
    for r in t108:
        k = (r["floor"], r["t_m"], r["block_type"])
        for c in ("physical_length_m", "held_length_m", "gross_m2", "deducted_m2", "net_m3"):
            A[k][c] += RV.f(r[c])
        A[k]["net " + r["net_status"]] += RV.f(r["net_m2"])
    for r in reg:
        k = (r["floor"], r["t_m"], r["block_type"])
        for c, rc in (("physical_length_m", "length_m"), ("held_length_m", "held_length_m"), ("gross_m2", "gross_m2"),
                      ("deducted_m2", "deductions_m2"), ("net_m3", "net_m3")):
            Bt[k][c] += RV.f(r[rc])
        Bt[k]["net " + inv[r["net_class"]]] += RV.f(r["net_m2"])
    assert set(A) == set(Bt)
    for k in A:
        for c in set(A[k]) | set(Bt[k]):
            assert Bt[k][c] == pytest.approx(A[k][c], abs=0.001), (k, c)


def test_every_held_wall_has_a_cause_and_counts():
    reg = _csv(HERE / "BLOCKWORK_WALL_REGISTER_V1.csv")
    held = [r for r in reg if r["owner_status_class"] == "HELD"]
    assert len(held) == 44
    assert all(r["held_cause_class"] and r["next_package"] and r["smallest_held_quantity"] for r in held)
    n = defaultdict(int)
    for r in held:
        n[r["held_cause_class"]] += 1
    assert dict(n) == {"annex datum (Q-54 B)": 9, "beam depth / register conflict": 10, "held opening": 12,
                       "no member drawn above": 6, "lift tie beam size (ST p.8 n.19)": 4,
                       "no wall band or member bound (glazed line / held strip)": 3}
    assert not any(r["owner_status_class"] == "VERIFIED" for r in reg)          # 0 VERIFIED before T-226..T-228
    assert all(r["net_m2"] == "" for r in held)                                 # held never a figure, never 0


def test_gap_reconstruction_wall_level():
    g = {(r["block_type"], r["t_m"]): r for r in _csv(HERE / "GAP_RECONSTRUCTION.csv")}
    b15, b20 = g[("BLACK", "0.15")], g[("BLACK", "0.2")]
    assert b15["gap_m2 (gross - deductions - net)"] == "3.464"
    assert b15["A: gross of walls with established gross and HELD net"] == "1F-W14 + 1F-W15 16.223"
    assert b15["C: deductions on HELD-gross walls"] == ("GF-W24 1.760 + GF-W27 1.760 + 1F-W11 1.760 + 1F-W13 3.960 "
                                                         "+ 1F-W16 1.760 + 1F-W17 1.760")
    assert abs(float(b15["residual_m2 (rounding of 3-decimal rows)"])) <= 0.001
    assert b20["gap_m2 (gross - deductions - net)"] == "12.001"
    assert b20["A: gross of walls with established gross and HELD net"] == "1F-W07 11.321 + 2F-W00 6.840"
    assert b20["B: deductions on those walls"] == "1F-W07 1.980"
    assert b20["C: deductions on HELD-gross walls"] == "GF-W08 2.200 + 2F-W05 1.980"


def test_freelancer_lines_traced_to_cells():
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    cells = {x["row"]: x["cells"] for x in raw["rows"] if x["file"] == "BLK" and x["sheet"] == "الكميات"}
    fl = {int(r["row"]): r for r in _csv(HERE / "FREELANCER_BLK_LINES.csv")}
    for n, (cnt, L, h, H) in {14: (1, 3.55, 4, 14.2), 176: (1, 3, 3.7, 11.1), 222: (3, 1, 2.4, 7.2)}.items():
        r = fl[n]
        assert r["cell_ref"] == f"B{n}:C{n}:D{n}:H{n}"
        assert (float(r["count"]), float(r["length_m"]), float(r["height_m"])) == (cnt, L, h)
        assert float(r["area_m2"]) == pytest.approx(H) == pytest.approx(cells[n][f"H{n}"]["v"])
    tot = {r["cell_ref"]: float(r["value_m2"]) for r in _csv(HERE / "FREELANCER_BLK_TOTALS.csv")}
    s = lambda a, b: sum(float(fl[i]["area_m2"]) for i in fl if a <= i <= b)
    assert s(14, 36) == pytest.approx(tot["H37"]) and s(133, 178) == pytest.approx(tot["H180"])
    assert s(185, 192) == pytest.approx(tot["H194"]) and s(203, 216) == pytest.approx(tot["H218"])
    assert "reads another row" in fl[74]["note"] and "no effect" in fl[74]["note"]     # H74 = D75 x C74 x B74


def test_older_automated_run_a():
    v = _csv(HERE / "V29_RUN_A_MASONRY_LINES.csv")
    runs = [x for x in v if x["item_code"] == "ARCH.WALL_RUN"]
    assert len(runs) == 7 and sum(float(x["measured_net"]) for x in runs) == pytest.approx(216.931, abs=0.0005)
    blk = [x for x in v if x["item_code"] in ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME")]
    assert len(blk) == 21 and all(x["evidence_state"] == "BLOCKED_RFI" and x["gross"] == "" for x in blk)
    assert {x["boq_lines_sha256"] for x in v} == {"b96185d468524743e600f1992d4e4b2028193ff4a379961bc5686c9662f8c115"}
    thk = _csv(HERE / "THREE_WAY_BY_FLOOR_THICKNESS_TYPE.csv")
    assert all("NOT COMPARABLE" in r["freelancer"] for r in thk)
    assert thk[0]["t_m"] == "0.10" and thk[0]["engine_physical_length_m"] == "0.000"   # no 100 mm wall anywhere


def test_no_client_names_or_cover_text_in_outputs():
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    cover = [str(v["v"]).strip() for x in raw["rows"] if x["file"] == "BLK" and x["sheet"] == "الغلاف"
             for k, v in x["cells"].items() if k[0] in "AF" and isinstance(v["v"], str) and len(v["v"].strip()) > 4]
    assert cover
    for p in HERE.iterdir():
        if p.suffix in (".csv", ".json", ".md"):
            text = p.read_text(encoding="utf-8")
            for c in cover:
                assert c not in text, (p.name, c)
