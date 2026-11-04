"""T-506 on villa M (hand fixture, not the development villa): three black walls.

  M-W1  0.15 m, 10.00 m2, one REQUIRED RC lintel face 0.32 m2 (D-M1)     -> T-453-style line HELD (0.15 module)
  M-W2  0.20 m,  8.00 m2, no lintel                                      -> PROVISIONAL-NET
  M-W3  0.20 m,  4.00 m2, one HELD lintel face 0 .. 0.34 m2 (D-M3)       -> RANGE-NET

Hand: joint mortar per m2 of the 0.39 x 0.19 unit + 10 / 10 mm (module 0.40 x 0.20) = t x (1 - 0.0741 / 0.08)
= 0.07375 t -> 0.0110625 (0.15) and 0.01475 (0.20) m3/m2.
  T-367 (contract area): W1 0.110625, W2 0.118, W3 0.059; total 0.287625 m3
  W1 lintel face 0.32 x 0.0110625 = 0.00354; W1 material base 9.68 x 0.0110625 = 0.107085 (HELD, beside)
  W2 PROVISIONAL-NET 0.118; W3 RANGE (4.00 - 0.34) x 0.01475 = 0.053985 .. 0.059
  0.287625 = 0.118 + 0.059 + 0.107085 + 0.00354  -> residual 0
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t506"))

import t506_mortar_reconcile as R  # noqa: E402


def _w(wid, t, a, m3, lid, floor="GF", kind="WHOLE"):
    return {"floor": floor, "wall_id": wid, "t_m": str(t), "kind": kind, "block_type": "BLACK",
            "area_m2": "" if a is None else f"{a:.4f}", "mortar_installed_m3": "" if m3 is None else f"{m3:.6f}",
            "part_line_id_v3026": lid, "area_status": "VERIFIED"}


def walls():
    return [_w("M-W1", 0.15, 10.0, 0.110625, "L-m1"), _w("M-W2", 0.20, 8.0, 0.118, "L-m2"),
            _w("M-W3", 0.20, 4.0, 0.059, "L-m3"), _w("M-W4", 0.20, None, None, "", kind="HELD WALL"),
            {"floor": "GF", "wall_id": "M-W5", "t_m": "0.2", "kind": "WHOLE", "block_type": "WHITE", "area_m2": "6.0",
             "mortar_installed_m3": "", "part_line_id_v3026": "L-m5", "area_status": "VERIFIED"}]


def ledger():
    def row(lid, t, net, status, req=(), held=()):
        return {"item": "LAYING_MATERIAL", "material_type": "BLACK", "line_id": lid, "thickness_m": t, "net_m2": net,
                "status": status, "lintel_deductions": [dict(x) for x in req],
                "lintel_held_faces": [dict(x) for x in held],
                "beside_t367_40x20": {"mortar_installed_m3": round(net * (0.0110625 if t == 0.15 else 0.01475), 6)}}
    return {"block_materials": [
        row("L-m1", 0.15, 10.0, "HELD", req=[{"opening_id": "D-M1", "host": "M-W1", "face_m2": 0.32}]),
        row("L-m2", 0.20, 8.0, "COMPUTED"),
        row("L-m3", 0.20, 4.0, "RANGE", held=[{"opening_id": "D-M3", "host": "M-W3", "face_max_m2": 0.34}]),
        {"item": "BLOCK_COUNT", "material_type": "BLACK", "line_id": "L-m2"}],
        "mortar": {"black_0_20_provisional_net": {"m3": 0.118}, "range_net": {"m3": [0.053985, 0.059]}}}


def bindings():
    return [{"table": "T-453", "row": "LAYING|L-m2", "line_id": "L-m2", "material": "MASONRY_LAYING",
             "kind": "mortar_m3", "value": 0.118, "bound": None, "estimate_beside": None, "stage": "INSTALLED"},
            {"table": "T-454", "row": "P1|WALL_PLASTER", "line_id": "L-p1", "material": "WALL_PLASTER",
             "kind": "mortar_m3", "value": 0.2, "bound": None, "estimate_beside": None, "stage": "INSTALLED"},
            {"table": "T-489", "row": "P1|WALL_PLASTER", "line_id": "L-p1", "material": "WALL_PLASTER",
             "kind": "mortar_m3", "value": 0.2, "bound": None, "estimate_beside": None, "stage": "INSTALLED"},
            {"table": "T-489", "row": "P1|WALL_PLASTER", "line_id": "L-p1", "material": "WALL_PLASTER",
             "kind": "cement_bags", "value": 1.5, "bound": None, "estimate_beside": None, "stage": "THEORETICAL"},
            {"table": "T-454", "row": "P1|WALL_PLASTER", "line_id": "L-p1", "material": "WALL_PLASTER",
             "kind": "cement_bags", "value": None, "bound": None, "estimate_beside": None, "stage": "THEORETICAL"}]


def build(w=None, led=None, bs=None):
    return R.build_from(walls() if w is None else w, ledger() if led is None else led,
                        bindings() if bs is None else bs)


# ------------------------------------------------------------------------------------------------ normal
def test_rate_by_hand():
    assert R.rate(0.15) == pytest.approx(0.0110625, abs=1e-12)
    assert R.rate(0.20) == pytest.approx(0.01475, abs=1e-12)


def test_reconciles_to_zero_residual_by_hand():
    out, _ = build()
    t = out["totals"]
    assert t["t367_m3"] == pytest.approx(0.287625, abs=1e-6)
    assert t[R.PNET]["m3"] == pytest.approx(0.118, abs=1e-6)
    assert t[R.RANGE]["low_m3"] == pytest.approx(0.053985, abs=1e-6)
    assert t[R.RANGE]["m3"] == pytest.approx(0.059, abs=1e-6)
    assert t[R.HELD015]["m3"] == pytest.approx(0.107085, abs=1e-6)
    assert t[R.LINTEL]["m3"] == pytest.approx(0.00354, abs=1e-6)
    assert t[R.LINTEL]["m2"] == pytest.approx(0.32, abs=1e-9)
    assert t["residual_m3"] == 0.0


def test_wall_rows_by_bucket():
    out, _ = build()
    by = {r["wall_id"]: r for r in out["rows"]}
    assert set(by) == {"M-W1", "M-W2", "M-W3"}
    assert by["M-W1"]["bucket"] == R.HELD015 and by["M-W1"]["governing_m3"] is None
    assert by["M-W1"]["beside_m3"] == pytest.approx(0.107085, abs=1e-6)
    assert by["M-W1"]["required_lintels"] == ["D-M1"]
    assert by["M-W2"]["governing_m3"] == pytest.approx(0.118, abs=1e-6)
    assert by["M-W3"]["governing_m3"] is None and by["M-W3"]["held_lintels"] == ["D-M3"]


def test_held_wall_stays_blank_never_zero():
    out, _ = build()
    assert [h["wall_id"] for h in out["held_walls"]] == ["M-W4"]
    assert "m3" not in out["held_walls"][0] and "governing_m3" not in out["held_walls"][0]
    assert all(r["wall_id"] != "M-W5" for r in out["rows"])          # white AAC: no mortar row at all


def test_roles_and_one_producer():
    out, roles = build()
    c = out["producer_census"]
    assert c["keys_with_two_producers"] == [] and c["reader_divergences"] == []
    role = {(b["table"], b["kind"], b["line_id"]): b["role"] for b in roles}
    assert role[("T-453", "mortar_m3", "L-m2")] == "PRODUCER"
    assert role[("T-367", "mortar_m3", "L-m2")] == "BESIDE"            # R-T506-2: T-367 never a second producer
    assert role[("T-454", "mortar_m3", "L-p1")] == "PRODUCER"
    assert role[("T-489", "mortar_m3", "L-p1")] == "READER"
    assert role[("T-489", "cement_bags", "L-p1")] == "PRODUCER"
    assert role[("T-454", "cement_bags", "L-p1")] == "BESIDE"


def test_summable_rows_count_each_quantity_once():
    out, roles = build()
    s = [b for b in roles if b["role"] == "PRODUCER" and b["value"] is not None and b["kind"] == "mortar_m3"]
    assert sorted((b["table"], b["line_id"]) for b in s) == [("T-453", "L-m2"), ("T-454", "L-p1")]


# ------------------------------------------------------------------------------------------------ adverse
def test_015_line_released_is_refused():
    led = ledger()
    led["block_materials"][0]["status"] = "COMPUTED"
    with pytest.raises(R.ReconcileError, match="0.15 m black line released"):
        build(led=led)


def test_015_unsourced_joint_stays_held_not_zero():
    out, _ = build()
    r = [x for x in out["rows"] if x["wall_id"] == "M-W1"][0]
    assert r["governing_m3"] is None and r["beside_m3"] > 0 and "NOT stated" in r["why"]


def test_held_wall_with_area_refused():
    w = walls()
    w[3]["area_m2"] = "0.0000"
    with pytest.raises(R.ReconcileError, match="held wall carries an area"):
        build(w=w)


def test_millimetre_or_wrong_rate_refused():
    w = walls()
    w[1]["mortar_installed_m3"] = "118.000000"          # mm-scale figure
    with pytest.raises(R.ReconcileError, match="joint geometry"):
        build(w=w)


def test_ledger_total_disagreement_refused():
    led = ledger()
    led["mortar"]["black_0_20_provisional_net"]["m3"] = 0.120
    with pytest.raises(R.ReconcileError, match="PROVISIONAL-NET"):
        build(led=led)


def test_unbounded_held_lintel_refused():
    led = ledger()
    led["block_materials"][2]["lintel_held_faces"][0]["face_max_m2"] = None
    with pytest.raises(R.ReconcileError, match="unbounded"):
        build(led=led)


def test_wall_twice_refused():
    w = walls()
    w.append(copy.deepcopy(w[1]))
    with pytest.raises(R.ReconcileError, match="twice"):
        build(w=w)


def test_two_producers_refused():
    """a binding with two producers: T-367 wired as a mortar figure beside T-453 (the T-372 row as first written)."""
    old = R.ROLE_RULES[("T-367", "MASONRY_LAYING", "mortar_m3")]
    R.ROLE_RULES[("T-367", "MASONRY_LAYING", "mortar_m3")] = "PRODUCER"
    try:
        with pytest.raises(R.ReconcileError, match="R-T506-3"):
            build()
    finally:
        R.ROLE_RULES[("T-367", "MASONRY_LAYING", "mortar_m3")] = old


def test_reader_divergence_refused():
    bs = bindings()
    bs[2]["value"] = 0.25
    with pytest.raises(R.ReconcileError, match="R-T506-3"):
        build(bs=bs)


def test_undeclared_role_refused():
    bs = bindings() + [{"table": "T-999", "row": "x", "line_id": "L-x", "material": "X", "kind": "k", "value": 1.0,
                        "bound": None, "estimate_beside": None, "stage": "THEORETICAL"}]
    with pytest.raises(R.ReconcileError, match="never guessed"):
        build(bs=bs)
