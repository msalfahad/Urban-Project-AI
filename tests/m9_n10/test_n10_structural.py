"""Phase N10 - formwork faces, excavation footprints and the reinforcement audit (engine.source.struct_n10) on the
route G register, against hand truth (one element at a time) and against the synthetic villa's DESIGN (tools/
synthetic_villa.py: footing, column and slab-panel sizes from the spec, never from the engine or the drawing)."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import struct_n10 as T                                        # noqa: E402
import synthetic_villa as SV                                  # noqa: E402
from engine.source import struct_n10 as SN                    # noqa: E402

A = 1e-6


def _row(fam, storey, dims, cat="PROVISIONAL", cid=None, base=None, trade="CONCRETE", formula="", support=""):
    return {"TRADE": trade, "FAMILY": fam, "STOREY": storey, "CATEGORY": cat, "COMPONENT_ID": cid or f"{fam}:{storey}",
            "ITEM_ID": f"P-C:{cid or fam}", "DIMENSIONS": json.dumps(dims), "BASE": base, "FORMULA": formula,
            "SUPPORT": support, "BLOCKER": "X" if cat == "UNRESOLVED" else ""}


SLAB = _row("SLABS", "GF", {"area_m2": 12.0, "t_m": 0.16}, cid="S1")
BEAM = _row("BEAMS", "GF", {"width_m": 0.2, "depth_m": 0.5, "net_plan_m2": 0.8, "length_m": 4.0}, cid="B1")
COL = _row("COLUMNS", "GF", {"section_m": [0.3, 0.5], "height_m": 3.6}, cid="C1")
FTG = _row("FOOTINGS", "FOUNDATION", {"schedule_m": [1.8, 1.6, 0.5]}, cid="F1")
GB = _row("GROUND_BEAMS", "FOUNDATION", {"width_m": 0.3, "depth_m": 0.6, "clear_length_m": 5.0}, cid="G1")


def _faces(rows):
    return {(f["component_id"], f["face"]): f for f in SN.formwork(rows)["faces"]}


def test_hand_truth_faces():
    f = _faces([SLAB, BEAM, COL, FTG, GB])
    assert f[("S1", "SOFFIT")]["area_m2"] == pytest.approx(12.0) and f[("S1", "SOFFIT")]["state"] == "MEASURED"
    assert f[("S1", "EDGES")]["state"] == "HELD" and "area_m2" not in f[("S1", "EDGES")]
    assert f[("B1", "SOFFIT")]["area_m2"] == pytest.approx(0.8)                       # 0.20 x 4.00
    assert f[("B1", "SIDES")]["alternatives_m2"] == {"BELOW_SLAB": pytest.approx(4.0),   # 2 x 4.00 x 0.50
                                                     "TOTAL": pytest.approx(2.72)}       # 2 x 4.00 x (0.50 - 0.16)
    assert f[("C1", "SIDES")]["area_m2"] == pytest.approx(2 * 0.8 * 3.44) and f[("C1", "SIDES")]["state"] == \
        "UPPER_BOUND"                                                                    # 5.504: framing beams in
    assert f[("F1", "SIDES")]["alternatives_m2"] == {"FORMED": pytest.approx(3.4), "EARTH_CAST": 0.0}  # 2 x 3.4 x 0.5
    assert f[("G1", "SIDES")]["alternatives_m2"] == {"FORMED": pytest.approx(6.0), "EARTH_CAST": 0.0}  # 2 x 5 x 0.6


def test_alternatives_are_never_summed_and_held_is_never_zero():
    rows = [SLAB, BEAM, _row("BEAMS", "GF", {"width_m": 0.2, "depth_m": 0.4, "net_plan_m2": 0.6}, cid="B2"),
            _row("BEAMS", "GF", {"depth_m": 0.4}, cat="UNRESOLVED", cid="B3"), _row("STAIRS", "GF", {}, cid="ST")]
    fw = SN.formwork(rows)
    s = fw["totals"]["BEAMS"]["SIDES"]
    assert s["state"] == "CONDITIONAL" and "area_m2" not in s
    assert s["alternatives_m2"] == {"BELOW_SLAB": pytest.approx(4.0 + 2.4), "TOTAL": pytest.approx(2.72 + 2 * 3 * 0.24)}
    assert fw["held"] == {"BEAMS": 1, "SLABS": 1, "STAIRS": 1}
    held = [f for f in fw["faces"] if f["state"] == "HELD"]
    assert all("area_m2" not in f and f["why"] for f in held)


def test_ground_slab_has_no_soffit_form():
    f = _faces([_row("GROUND_SLAB", "GF", {"area_m2": 40.0, "t_m": 0.15}, cid="GS")])
    assert f[("GS", "SOFFIT")]["area_m2"] == 0.0 and f[("GS", "EDGES")]["state"] == "HELD"


def test_columns_need_the_storey_slab_thickness():
    f = _faces([COL])
    assert f[("C1", "SIDES")]["state"] == "HELD" and "NO_SLAB_THICKNESS" in f[("C1", "SIDES")]["why"]
    neck = _faces([SLAB, _row("COLUMNS", "FOUNDATION", {"section_m": [0.3, 0.3], "footing": "F1"}, cid="N1")])
    assert neck[("N1", "SIDES")]["state"] == "HELD" and "HEIGHT" in neck[("N1", "SIDES")]["why"]


def test_excavation_is_held_without_levels_and_working_space():
    ex = SN.excavation([FTG, GB])
    assert ex["state"] == "HELD" and ex["volume_m3"] is None
    assert ex["footprint_m2"] == pytest.approx(1.8 * 1.6 + 5.0 * 0.3)                # 2.88 + 1.50
    assert "working space" in ex["why"] and "depth" in ex["why"]
    assert ex["backfill"]["state"] == "HELD"


def test_excavation_with_stated_depth_and_working_space():
    facts = {"excavation": {"working_space_m": {"value_m": 0.3, "authority": "OWNER_PROJECT_FACT: synthetic"},
                            "ngl_m": {"value_m": 0.0, "authority": "OWNER_PROJECT_FACT: synthetic"},
                            "founding_level_m": {"value_m": -1.5, "authority": "OWNER_PROJECT_FACT: synthetic"}}}
    one = SN.excavation([FTG], facts)
    assert one["state"] == "MEASURED" and one["depth_m"] == pytest.approx(1.5)
    assert one["volume_m3"] == pytest.approx((1.8 + 0.6) * (1.6 + 0.6) * 1.5)           # 5.28 x 1.5 = 7.92
    two = SN.excavation([FTG, GB], facts)
    assert two["state"] == "UPPER_BOUND"                                               # positions: no merge
    assert two["volume_m3"] == pytest.approx((5.28 + 5.0 * (0.3 + 0.6)) * 1.5)


def test_rebar_unit_mass_against_d2_over_162():
    rb = SN.rebar_audit([])
    by = {x["d_mm"]: x for x in rb["unit_mass"]}
    assert by[16]["d2_over_162"] == pytest.approx(256 / 162) and by[16]["method_vs_d2_162_pct"] == 0.0
    exact = math.pi / 4 * 0.016 ** 2 * 7850
    assert by[16]["d2_162_vs_exact_pct"] == pytest.approx(100 * (256 / 162 - exact) / exact, abs=1e-4)
    assert all(abs(x["d2_162_vs_exact_pct"]) < 0.2 for x in rb["unit_mass"])         # the site rule is within 0.2 %


def test_ratio_labelled_as_measured_is_a_violation():
    rows = [_row("SLABS", "GF", {}, trade="REINFORCEMENT", cid="R1", base=100.0, formula="80 kg/m3 x volume",
                 support="SOURCE_COMPLETE_UNREVIEWED"),
            _row("SLABS", "GF", {}, trade="REINFORCEMENT", cid="R2", base=90.0, formula="80 kg/m3 x volume",
                 support="CONVENTION_ONLY"),
            _row("BEAMS", "GF", {}, trade="REINFORCEMENT", cid="R3", base=10.0,
                 formula="count x (clear span + 2 anchorage) x d^2/162", support="CONVENTION_ONLY")]
    rb = SN.rebar_audit(rows)
    assert rb["rows"] == {"D2_OVER_162": 1, "RATIO": 2}
    assert [v["component_id"] for v in rb["violations"]] == ["R1"]


# ------------------------------------------------------------------------- the synthetic villa (design truth)
def _design_truth(seed, truth):
    D = SV.design(seed)
    sr = SV.schedule_rows(D)
    fr, cr, sb = ({r["mark"]: r for r in sr[k]} for k in ("FOOTING", "COLUMN", "BEAM"))
    return {"footing_sides": sum(2 * (fr[c["ftg"]]["L"] + fr[c["ftg"]]["W"]) * fr[c["ftg"]]["D"] for c in D["cols"]),
            "column_sides": sum(2 * (cr[c["type"]]["B"] + cr[c["type"]]["H"]) * (D["heights"][st] - D["slab_t"][st])
                                for st in ("GF", "1F") for c in D["cols"]),
            "slab_soffit": sum(p["area"] for p in truth["component_list"]["panels"]),
            "beam_soffit": sum(sb[b["type"]]["B"] * b["clear"] for st in ("GF", "1F") for b in SV.beams_of(D)
                               if b["type"] in sb),
            "curved": D["var"]["curved"]}


def _digest(d):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(d).iterdir()) if p.is_file()}


@pytest.fixture(scope="module", params=[3, 5])
def villa(request, tmp_path_factory):
    seed = request.param
    d = tmp_path_factory.mktemp(f"villa{seed}")
    SV.generate(str(d), seed)
    o = d / "o"
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m2.py"), "run", "--drawings",
                        str(d / f"villa_{seed}.dxf"), "--out", str(o), "--route", "G", "--profile",
                        str(d / f"villa_{seed}.profile.json"), "--no-pdf", "--no-xlsx"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1500:]
    truth = json.loads((d / f"villa_{seed}.truth.json").read_text(encoding="utf-8"))
    before = _digest(o)
    res = T.build(o, d / "n10")
    assert _digest(o) == before                                    # the route G run is read only
    return {"seed": seed, "out": o, "n10": d / "n10", "truth": _design_truth(seed, truth), "res": res}


def test_formwork_matches_the_design(villa):
    tt, dt = villa["res"]["formwork"], villa["truth"]
    assert tt["FOOTINGS"]["SIDES"]["alternatives_m2"]["FORMED"] == pytest.approx(dt["footing_sides"], abs=1e-6)
    assert tt["COLUMNS"]["SIDES"]["area_m2"] == pytest.approx(dt["column_sides"], abs=1e-6)
    assert tt["SLABS"]["SOFFIT"]["area_m2"] == pytest.approx(dt["slab_soffit"], abs=1e-3)   # route G rounds to 1e-4
    # every scheduled beam is either measured or held as an unresolved span with its own plan
    fw = json.loads((villa["n10"] / "FORMWORK.json").read_text(encoding="utf-8"))
    rows = T.read_rows(villa["out"])
    held = [r for r in SN.concrete_rows(rows) if r["FAMILY"] == "BEAMS" and r["CATEGORY"] == "UNRESOLVED"]
    held_plan = sum(SN._dims(r)["net_plan_m2"] for r in held)     # the held spans' own drawn plan
    assert not dt["curved"]
    assert tt["BEAMS"]["SOFFIT"]["area_m2"] + held_plan == pytest.approx(dt["beam_soffit"], abs=1e-6)
    assert fw["held"]["BEAMS"] == len(held)


def test_faces_conserve_the_route_g_concrete(villa):
    """soffit x depth, sides / perimeter + slab, L x W x D: each face set rebuilds the element's own volume."""
    rows = SN.concrete_rows(T.read_rows(villa["out"]))
    fw = json.loads((villa["n10"] / "FORMWORK.json").read_text(encoding="utf-8"))
    face = {(f["component_id"], f["face"]): f for f in fw["faces"]}
    t = {k: v[0] for k, v in fw["slab_thickness_m"].items()}
    n = 0
    for r in rows:
        if r["CATEGORY"] == "UNRESOLVED":
            continue
        d, base, cid = SN._dims(r), float(r["BASE"]), r["COMPONENT_ID"]
        if r["FAMILY"] == "BEAMS":
            assert face[(cid, "SOFFIT")]["area_m2"] * d["depth_m"] == pytest.approx(base, abs=1e-6)
            assert face[(cid, "SIDES")]["alternatives_m2"]["BELOW_SLAB"] / 2 * d["width_m"] == pytest.approx(base,
                                                                                                         abs=1e-6)
        elif r["FAMILY"] == "COLUMNS" and d.get("height_m"):
            a, c = d["section_m"]
            h = face[(cid, "SIDES")]["area_m2"] / (2 * (a + c)) + t[r["STOREY"]]
            assert a * c * h == pytest.approx(base, abs=1e-6)
        elif r["FAMILY"] == "FOOTINGS":
            L, W, D = d["schedule_m"]
            assert face[(cid, "SIDES")]["alternatives_m2"]["FORMED"] / (2 * (L + W)) * L * W == pytest.approx(
                base, abs=1e-6)
        else:
            continue
        n += 1
    assert n > 40


def test_route_g_reinforcement_is_derived_never_a_ratio(villa):
    rb = json.loads((villa["n10"] / "REBAR_AUDIT.json").read_text(encoding="utf-8"))
    assert set(rb["rows"]) <= {"D2_OVER_162", "COUNT_X_LENGTH"} and rb["violations"] == []
    ex = json.loads((villa["n10"] / "EXCAVATION.json").read_text(encoding="utf-8"))
    assert ex["state"] == "HELD" and ex["footprint_m2"] > 0
