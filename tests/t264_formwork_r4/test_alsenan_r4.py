"""T-264 Alsenan formwork r4 from committed inputs only (merged r3 ledger research/agents_t163, the merged T-174 / T-233 /
T-239 / T-242 / T-248 / T-252 / T-253 / T-256 ledgers, and ALSENAN_R4_INPUT.json derived from Drive 'ST7757 dxf.dxf'
sha 9f9d1179). Pins the engineering results (development villa; not an accuracy claim; nothing wired or released)."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t264"


def _load():
    spec = importlib.util.spec_from_file_location("formwork_r4", HERE / "formwork_r4.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load()
R4, DELTA, INP, RG = M.build()
BY = {(r["element"], r["floor"], r["item"], r["method"]): r for r in R4}


def _items(sub):
    return [r for r in R4 if sub in r["item"]]


def test_r3_is_carried_and_totals_reproduce():
    t3 = M.totals(M.r3_lines())
    assert t3["G_CALCULATED"] == pytest.approx(1078.274) and t3["OQ10_FORMED"] == pytest.approx(103.14)
    assert sum(1 for r in R4 if r["change"] == "UNCHANGED") > 150


def test_committed_outputs_equal_a_fresh_build(tmp_path):
    M.write(str(tmp_path))
    for f in ("FORMWORK_LINES_R4.csv", "FORMWORK_DELTA_R3_R4.csv", "summary_r4.json"):
        assert (tmp_path / f).read_bytes() == (HERE / f).read_bytes(), f


def test_ring_b7_from_its_arcs():
    ring = INP["void_ring"]["pieces"]
    void_arcs = [p for p in ring["void"] if p["kind"] == "arc"]
    assert len(void_arcs) == 5 and all(p["beyond_kind"] == "VOID" for p in void_arcs)
    assert sum(p["length_m"] for p in void_arcs) == pytest.approx(5.763537, abs=2e-6)
    slab_arcs = [p for p in ring["outer"] if p["kind"] == "arc"]
    assert {p["beyond_kind"] for p in slab_arcs} == {"SLAB"}
    assert sum(p["length_m"] for p in slab_arcs) == pytest.approx(2.048524, abs=2e-6)
    # straight outer pieces lie on equal-depth beams (B8, B17, CB1, B7 0.75): covered
    assert {(p["handle"], p["beyond_D"]) for p in ring["outer"] if p["kind"] == "line"} == \
        {("46D", 0.75), ("42D", 0.75), ("2A9", 0.75), ("437", 0.75)}
    assert RG["d_soffit"] == pytest.approx(0.666406 - 0.275103, abs=2e-6)
    # sides: 2.048524 x 0.59 + 5.763537 x 0.59 + CB1 1.330413 x 0.59 - r3's two bound pieces 0.485975
    assert RG["d_side"] == pytest.approx((2.048524 + 5.763537 + 1.330413) * 0.59 - 0.485975, abs=2e-6)
    assert RG["d_band"] == pytest.approx((5.763537 + 1.330413) * 0.16, abs=2e-6)
    assert BY[("BEAM", "GF", "GF roof slab (p.4) beam soffits", "G")]["m2"] == pytest.approx(56.357303, abs=1e-6)
    assert BY[("BEAM", "GF", "GF roof slab (p.4) beam sides below the slab", "G")]["m2"] == \
        pytest.approx(171.368085, abs=1e-6)


def test_ring_adverse_no_ring_mix_left_and_void_band_owned_once():
    assert not [r for r in R4 if r["floor"] == "GF" and "RING_MIX" in r["item"]]
    pool = _items("pool-court void")
    assert len(pool) == 1 and pool[0]["status"] == M.OWNED and pool[0]["m2"] is None


def test_oblique_ends_already_on_the_carrier_face_in_r3():
    o = INP["oblique_ends"]
    b4 = o["BM-GF-017#BAND0018"]["faces"]["GF-153"]
    assert b4["on_edge_m"] == {"27D": pytest.approx(2.89066), "282": pytest.approx(3.03827)}
    assert b4["face_m2"] == pytest.approx(0.2 * (2.89066 + 3.03827) / 2, abs=1e-5)
    cb4 = o["BM-GF-021#BAND0021.1"]["faces"]["GF-129"]
    assert cb4["face_m2"] == pytest.approx(0.2 * (2.37438 + 2.64537) / 2, abs=1e-5)
    assert not [d for d in DELTA if d[0] and ("BM-GF-017" in d[0]["item"] or "BM-GF-021" in d[0]["item"])]


def test_ground_beams_rebased():
    ext = [r for r in R4 if r["element"] == "GROUND_BEAM" and r["status"] == M.CALC]
    # 16 straight exterior runs: the side with no panel above N.G.; + the ring's court face
    assert sum(r["m2"] for r in ext) == pytest.approx(47.663, abs=1e-3)
    arc = _items("ARC:157+158 inner face")[0]
    assert arc["m2"] == pytest.approx(6.567377 * 0.95, abs=1e-6)
    outer = _items("ARC:157+158 outer face (rooms side")[0]
    assert outer["status"] == M.ALT and outer["m2"] == pytest.approx((6.679704 - 0.30018 - 0.10199) * 0.95, abs=1e-6)
    annex = _items("(annex exterior)")
    assert len(annex) == 9 and all(r["status"] == M.HELD and r["held_hi"] is None for r in annex)
    # a panel not established beside a face: its EARTH_CAST alternative is held, never 0
    for run in ("109+7CB#2 side B", "145+7CA#1 side B", "7D0+FC#2 side B", "7D0+FC#3 side B"):
        h = _items("span %s EARTH_CAST (panel not established)" % run)[0]
        assert h["status"] == M.HELD and h["held_lo"] == 0.0 and h["held_hi"] > 0
    # interior runs released by T-242 at one p.13 class
    assert _items("span 109+7CB#1 L 4.4000 D 0.40 sides FORMED")[0]["m2"] == pytest.approx(3.52)
    assert _items("span 17C+7E3#1 L 3.2280 D 0.40 sides FORMED")[0]["m2"] == pytest.approx(2.5824)


def test_boundary_gb_oq10_pair_and_end_held():
    f = _items("boundary G.B 20 x 40 at N.G., 5 runs 44.07 m, two faces FORMED")[0]
    e = _items("boundary G.B 20 x 40 at N.G., 5 runs 44.07 m, two faces EARTH_CAST")[0]
    assert f["m2"] == pytest.approx(35.256) and e["m2"] == 0.0 and f["status"] == e["status"] == M.ALT
    end = _items("810#1 west end face")[0]
    assert end["status"] == M.HELD and end["held_hi"] == pytest.approx(0.08)


def test_columns_not_present_conflict_planted():
    assert not _items("undrawn column")
    c57 = [r for r in R4 if r["item"].startswith("COL-1F-57")][0]
    assert c57["status"] == M.CALC and c57["m2"] == pytest.approx(6.21)
    c32 = [r for r in R4 if r["item"].startswith("COL-1F-32")][0]
    assert c32["status"] == M.HELD and (c32["held_lo"], c32["held_hi"]) == (pytest.approx(5.18), pytest.approx(6.29))
    for cid in ("COL-2F-51", "COL-2F-53", "COL-2F-54"):
        r = [x for x in R4 if x["item"].startswith(cid)][0]
        assert r["status"] == M.HELD and r["held_lo"] is None and r["held_hi"] > 0
    j = [r for r in R4 if r["element"] == "JOINT" and r["floor"] == "1F" and r["status"] == M.CALC
         and "STATED" in r["item"]][0]
    assert j["m2"] == pytest.approx(2.214828, abs=1e-6)


def test_footings_and_straps():
    f10 = [r for r in R4 if r["item"].startswith("F10 ")][0]
    assert (f10["held_lo"], f10["held_hi"]) == (pytest.approx(4.65), pytest.approx(5.22))
    fn = _items("FN 180C / F9 notch")[0]
    assert fn["status"] == M.ALT and fn["m2"] == pytest.approx(-0.45)
    sides = [r for r in R4 if r["element"] == "STRAP" and r["status"] == M.ALT and "FORMED" in r["item"]]
    assert sum(r["m2"] for r in sides) == pytest.approx(9.4491, abs=1e-4)


def test_summary_deltas():
    s = json.loads((HERE / "summary_r4.json").read_text(encoding="utf-8"))
    d = s["delta"]
    assert d["G_CALCULATED"] == pytest.approx(-62.311, abs=1e-3)
    assert d["OQ10_FORMED"] == pytest.approx(105.972, abs=1e-3)
    assert s["totals_r4"]["BELOW_CALCULATED"] == pytest.approx(47.663, abs=1e-3)
    with open(HERE / "FORMWORK_DELTA_R3_R4.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert all(r["cause"] for r in rows)
