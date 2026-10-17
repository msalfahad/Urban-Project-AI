"""S8.6 (research/alsenan_lintels_s8_6): lintels - opening census, schedule binding, lintel concrete and bars.

The checks re-derive the package from its outputs, the frozen stages and, when the private drawings are restored,
the drawings themselves through independent tools (ezdxf, shapely):

- every earlier stage still verifies; the package is frozen before any comparison and blind (PRE-S8 and R5 are read
  through whitelists that never bind a lintel quantity);
- every opening is one census row with one decision; R5's door + glazed-door pairs collapse to one opening;
- the schedule transcription is exact and every boundary width binds as printed;
- nothing is released under a beam, without a wall, curved, in the lift shaft or in the boundary wall;
- every released lintel's concrete and bars recomputed by hand from the schedule; totals by floor and diameter;
- every bend, hook and anchorage the details leave undimensioned is registered as blocked."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from engine.source import delta_release as DR
from engine.source import lintel_qto as LQ

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_lintels_s8_6"
MANIFEST = PKG / "15_S8_6_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_OPENING_CENSUS.csv", "02_LINTEL_SCHEDULE_TRANSCRIPTION.csv",
           "03_ARCH_STRUCTURAL_REGISTRATION.csv", "04_OPENING_LINTEL_BINDING_MATRIX.csv", "05_BEAM_OVERLAP_AUDIT.csv",
           "06_LINTEL_CONCRETE_QTO.csv", "07_LINTEL_REBAR_QTO.csv", "08_BLOCKED_AND_CONFLICTS.csv",
           "09_OPENING_REGISTER_FOR_BOQ.csv", "10_OWNERSHIP_RECONCILIATION.csv", "11_CONSERVATION_CHECKS.csv",
           "12_SOURCE_AUTHORITY.csv", "13_PROVENANCE.jsonl", "14_S8_6_SUMMARY.json"]
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists()),
                                  reason="private client drawings not restored in data/inputs/by_sha256")
PRINTED = {"L1": ("0 -100", "B x 20", "2Ø12", "2Ø10", "5Ø8/M"), "L2": ("101 - 200", "B x 20", "2Ø14", "2Ø12", "5Ø8/M"),
           "L3": ("201 - 300", "B x 30", "3Ø16", "3Ø14", "5Ø8/M"), "L4": ("301 - 500", "B x 40", "3Ø18", "3Ø14", "5Ø8/M"),
           "L5": ("501 - 750", "B x 55", "4Ø18", "3Ø14", "5Ø8/M")}
DECISIONS = {"SCHEDULE_BOUND_LINTEL", "EXISTING_STRUCTURAL_BEAM_ABOVE", "OTHER_ESTABLISHED_SUPPORT",
             "BLOCKED_SUPPORT_IDENTITY", "OPENING_NOT_REQUIRING_SEPARATE_LINTEL", "SOURCE_CONFLICT"}
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def F(v):
    return float(v) if v not in ("", None) else None


def jl(v):
    return json.loads(v) if v else []


@pytest.fixture(scope="module")
def s():
    return J(PKG / "14_S8_6_SUMMARY.json")


@pytest.fixture(scope="module")
def sched():
    out = {}
    for r in rows("02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"):
        if r["RECORD"] == "SCHEDULE_ROW":
            out[r["ROW_ID"]] = r
    return out


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_6" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS) and m["baseline"] == "818321e"
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 22 and {"S6.1", "PRE-S8", "S8.4", "S8.5"} <= set(s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*FREEZE_MANIFEST.json")):
        m = J(mp)
        if m.get("state") == "FROZEN_BEFORE_COMPARISON" and mp != MANIFEST:
            DR.verify_frozen(mp, ROOT)
    assert len(s["register_indexes"]) == 4 and s["s8_3_errata_sha256"]


def test_blind_whitelists_and_registry():
    m = J(MANIFEST)
    assert "CONCRETE_QUANTITY_STATE" not in m["pre_s8_columns_read"]
    assert not {"lintel_depth_m", "height", "sill_m", "area", "material"} & set(m["r5_fields_read"])
    src = (PKG / "build_s8_6.py").read_text(encoding="utf-8")
    assert "lintel_depth_m" not in src.replace('"lintel_depth_m", "height"', "")
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/lintel_qto.py", "engine/source/opening_census.py",
              "research/alsenan_lintels_s8_6/build_s8_6.py"):
        assert f'"{p}"' in reg


# ------------------------------------------------------------------ census
def test_census_one_row_per_opening_one_decision(s):
    cen = [r for r in rows("01_OPENING_CENSUS.csv") if r["RECORD"] == "OPENING"]
    ids = [r["OPENING_ID"] for r in cen]
    assert len(ids) == len(set(ids)) == 74
    bm = {r["OPENING_ID"]: r for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv")}
    assert set(bm) == set(ids) and all(r["DECISION"] in DECISIONS for r in bm.values())
    by = Counter(r["FLOOR"] for r in cen if r["KIND"] != "SLAB_OPENING")
    assert by == {"GF": 32, "1F": 26, "2F": 8}
    assert s["openings"]["wall_openings"] == 65 and s["openings"]["slab"] == 8
    rej = [r for r in rows("01_OPENING_CENSUS.csv") if r["RECORD"] == "REJECTED_CANDIDATE"]
    assert sorted(r["TYPE_BASIS"] for r in rej) == ["CLOSURE_WITHOUT_OPENING_EVIDENCE", "WALL_DEFLECTION",
                                                     "WALL_DEFLECTION"]
    assert sum(s["decisions"].values()) == 74


def test_lift_landings_stack_and_stay_blocked():
    cen = {r["OPENING_ID"]: r for r in rows("01_OPENING_CENSUS.csv")}
    lift = [r for r in cen.values() if r["TYPE"] == "6_SERVICE_SHAFT_OPENING"]
    assert sorted(r["FLOOR"] for r in lift) == ["1F", "2F", "GF"]
    xs = {round(json.loads(r["CENTRE_FRAME_XY"])[0]) for r in lift}
    assert max(xs) - min(xs) <= 2 and {F(r["WIDTH_MM"]) for r in lift} == {1000.0}
    bm = {r["OPENING_ID"]: r for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv")}
    assert {bm[r["OPENING_ID"]]["DECISION"] for r in lift} == {"BLOCKED_SUPPORT_IDENTITY"}


def test_r5_pairs_collapse_to_one_opening(s):
    assert sorted(s["r5_double_counts"]) == ["OP-GF-003", "OP-GF-007", "OP-GF-010", "OP-GF-019"]
    for k, v in s["r5_double_counts"].items():
        assert len(v) == 2 and any("-D-" in x for x in v) and any("-W" in x for x in v)
    dup = [r for r in rows("08_BLOCKED_AND_CONFLICTS.csv") if r["KIND"] == "DOUBLE_COUNT_FINDING"]
    assert len(dup) == 4


# ------------------------------------------------------------------ schedule
def test_schedule_transcription_exact(sched):
    assert set(sched) == set(PRINTED)
    for k, (w, sz, bot, top, st) in PRINTED.items():
        r = sched[k]
        assert (r["WIDTH_PRINTED"], r["SIZE_PRINTED"], r["BOTTOM_PRINTED"], r["TOP_PRINTED"], r["STIRRUPS_PRINTED"]) == \
               (w, sz, bot, top, st)
        assert (int(r["WIDTH_LO_CM"]), int(r["WIDTH_HI_CM"])) == LQ.parse_width_range(w)
    gaps = [r["ROW_ID"] for r in rows("02_LINTEL_SCHEDULE_TRANSCRIPTION.csv") if r["RECORD"] == "UNCOVERED_INTERVAL"]
    assert gaps == ["GAP-100-101", "GAP-200-201", "GAP-300-301", "GAP-500-501", "ABOVE-750"]


def test_boundary_cases_bind_as_printed():
    exp = {"W1000": "L1", "W999.9": "L1", "W1000.5": "BOUNDARY_GAP", "W1001": "BOUNDARY_GAP", "W1010": "L2",
           "W2000": "L2", "W2005": "BOUNDARY_GAP", "W2010": "L3", "W3000": "L3", "W3010": "L4", "W5000": "L4",
           "W5010": "L5", "W7500": "L5", "W7500.1": "ABOVE_SCHEDULE", "W7510": "ABOVE_SCHEDULE", "W0": "NOT_POSITIVE"}
    got = {}
    for r in rows("02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"):
        if r["RECORD"] == "BOUNDARY_CASE":
            got[r["ROW_ID"]] = r["SOURCE"] if r["BOUNDS"] == "IN_ROW" else r["BOUNDS"]
    for k, v in exp.items():
        assert got[k] == v, k


def test_binding_rows_recomputed(sched):
    rs = [{"row_id": k, "lo": int(r["WIDTH_LO_CM"]), "hi": int(r["WIDTH_HI_CM"])} for k, r in sorted(sched.items())]
    for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv"):
        if not r["WIDTH_MM"]:
            continue
        st, row = LQ.row_for_width(rs, float(r["WIDTH_MM"]))
        assert r["SCHEDULE_STATE"] == st and (r["SCHEDULE_ROW"] or None) == (row["row_id"] if st == "IN_ROW" else None)


# ------------------------------------------------------------------ decisions
def test_nothing_unsupported_is_released():
    cen = {r["OPENING_ID"]: r for r in rows("01_OPENING_CENSUS.csv")}
    for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv"):
        rel = r["DECISION"] == "SCHEDULE_BOUND_LINTEL"
        assert rel == (r["LANE"] == "PROJECT_BASIS_QTO")
        if rel:
            c = cen[r["OPENING_ID"]]
            assert r["BEAM_RELATION"] == "NONE" and c["KIND"] == "WALL_GAP" and r["LINTEL_ID"]
            assert c["TYPE"] not in ("6_SERVICE_SHAFT_OPENING",) and c["ZONE"] != "SITE_BOUNDARY"
        if r["BEAM_RELATION"] in ("FULL", "PARTIAL"):
            assert r["DECISION"] in ("BLOCKED_SUPPORT_IDENTITY", "EXISTING_STRUCTURAL_BEAM_ABOVE")
    so = [r for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv") if r["OPENING_ID"].startswith("SO-")]
    assert len(so) == 8 and {r["DECISION"] for r in so} == {"OPENING_NOT_REQUIRING_SEPARATE_LINTEL"}


def test_beam_audit_no_released_lintel_under_a_beam():
    ba = rows("05_BEAM_OVERLAP_AUDIT.csv")
    rel = {r["OPENING_ID"] for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv")
           if r["DECISION"] == "SCHEDULE_BOUND_LINTEL"}
    for r in ba:
        if r["OPENING_ID"] in rel and r["SCOPE"] == "OPENING_SPAN":
            assert r["RELATION"] == "NONE"
        if r["SCOPE"] == "RELEASED_LINTEL_FOOTPRINT":
            assert F(r["COLUMN_OVERLAP_MM2"]) <= 1000.0


# ------------------------------------------------------------------ quantities by hand
def test_concrete_by_hand(s):
    conc = [r for r in rows("06_LINTEL_CONCRETE_QTO.csv") if r["LANE"] == "PROJECT_BASIS_QTO"]
    assert len(conc) == 14
    by = defaultdict(float)
    for r in conc:
        B, D, L, W = F(r["B_MM"]), F(r["D_MM"]), F(r["LENGTH_MM"]), F(r["OPENING_W_MM"])
        assert L == pytest.approx(W + F(r["BEARING_START_MM"]) + F(r["BEARING_END_MM"]), abs=0.2)
        for side in ("START", "END"):
            b = F(r[f"BEARING_{side}_MM"])
            assert b <= 400.0 + 1e-6
            if r[f"{side}_SUPPORT"] == "MASONRY" and b < 400.0 - 0.5:
                assert any(f.startswith(f"BEARING_DEFICIT:{side.lower()}") for f in jl(r["FLAGS"]))
        assert F(r["GROSS_M3"]) == pytest.approx(B * D * L / 1e9, abs=2e-9)
        assert F(r["M3"]) == pytest.approx(F(r["GROSS_M3"]) - F(r["SHARED_CORNER_M3"]), abs=2e-9)
        by[r["FLOOR"]] += F(r["M3"])
    for fl, v in s["released"]["concrete_m3_by_floor"].items():
        assert v == pytest.approx(by.get(fl, 0.0), abs=1e-8)


def test_reinforcement_by_hand(s, sched):
    conc = {r["LINTEL_ID"]: r for r in rows("06_LINTEL_CONCRETE_QTO.csv") if r["LANE"] == "PROJECT_BASIS_QTO"}
    reb = [r for r in rows("07_LINTEL_REBAR_QTO.csv") if r["VIEW"] == "PROJECT_BASIS_QTO"]
    tot = defaultdict(float)
    for r in reb:
        c = conc[r["LINTEL_ID"]]
        sr = sched[c["ROW"]]
        B, D, L = F(c["B_MM"]), F(c["D_MM"]), F(c["LENGTH_MM"])
        d = int(r["DIA_MM"])
        if r["ROLE"] in ("BOTTOM", "TOP"):
            n, dd = LQ.parse_bars(sr[f"{r['ROLE']}_PRINTED"])
            assert (int(r["COUNT"]), d) == (n, dd) and F(r["EACH_MM"]) == pytest.approx(L - 50.0, abs=0.2)
        else:
            rate, dd = LQ.parse_rate(sr["STIRRUPS_PRINTED"])
            assert d == dd and int(r["COUNT"]) == math.ceil(rate * L / 1000.0 - 1e-6)
            assert F(r["EACH_MM"]) == pytest.approx(2 * (B - 58) + 2 * (D - 58), abs=0.2)
        assert F(r["KG"]) == pytest.approx(int(r["COUNT"]) * F(r["EACH_MM"]) / 1000.0 * d * d / 162.0, rel=1e-6)
        tot[(r["FLOOR"], r["DIA_MM"])] += F(r["KG"])
    for fl, m in s["released"]["kg_by_floor_and_diameter"].items():
        for dia, v in m.items():
            assert v == pytest.approx(tot[(fl, dia)], abs=1e-6)
    assert s["released"]["kg"] == pytest.approx(sum(tot.values()), abs=1e-6)


def test_every_missing_bar_component_registered():
    reb = rows("07_LINTEL_REBAR_QTO.csv")
    conc = {r["LINTEL_ID"]: r for r in rows("06_LINTEL_CONCRETE_QTO.csv") if r["LANE"] == "PROJECT_BASIS_QTO"}
    roles = defaultdict(set)
    for r in reb:
        if r["VIEW"] == "BLOCKED_ROLE":
            roles[r["LINTEL_ID"]].add(r["ROLE"])
    for lid, c in conc.items():
        assert {"BOTTOM_END_BENDS", "TOP_END_BENDS", "STIRRUP_HOOKS", "LAPS"} <= roles[lid]
        for side in ("START", "END"):
            if c[f"{side}_SUPPORT"] == "FRAME":
                assert f"ANCHORAGE_INTO_COLUMN_{side}" in roles[lid]
    bbs = [r for r in reb if r["VIEW"] == "PHYSICAL_BBS"]
    assert bbs and all(r["LANE"] == "BLOCKED_UNQUANTIFIED" and not r["KG"] for r in bbs)


# ------------------------------------------------------------------ registers
def test_boq_register_links():
    boq = rows("09_OPENING_REGISTER_FOR_BOQ.csv")
    assert len(boq) == 66
    lint = {r["OPENING_ID"]: r["LINTEL_ID"] for r in rows("04_OPENING_LINTEL_BINDING_MATRIX.csv")}
    for r in boq:
        oid = r["OPENING_ID"]
        assert r["BLOCKWORK_DEDUCTION"] == f"BW-DED:{oid}" and r["REVEAL_JAMB"] == f"RV:{oid}"
        assert jl(r["PLASTER_DEDUCTION"]) == [f"PL-DED:{oid}:A", f"PL-DED:{oid}:B"]
        assert (r["LINTEL_ITEM"] or None) == (lint[oid] or None)
        assert r["QUANTITY_STATE"].startswith("IDS_AND_OWNERSHIP_ONLY")


def test_ownership_and_conservation():
    own = {r["ID"]: r for r in rows("10_OWNERSHIP_RECONCILIATION.csv")}
    assert {"OWN-S1-BEAM", "OWN-S2", "OWN-S6", "OWN-S6-BEAMS", "OWN-S3.1", "OWN-S7", "OWN-PRE-S8"} <= set(own)
    assert "BLOCKED" in own["OWN-S2"]["OLD_STATE"]
    cons = rows("11_CONSERVATION_CHECKS.csv")
    assert len(cons) == 18 and {r["RESULT"] for r in cons} == {"PASS"}


def test_hygiene():
    for name in OUTPUTS:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_6.py")], check=True, cwd=ROOT, capture_output=True)
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o


@needs_inputs
def test_released_openings_independently_measured():
    """ezdxf + shapely: each released opening's strip is free of wall faces and both faces stop at the jambs."""
    import ezdxf
    from shapely.geometry import LineString, Polygon
    doc = ezdxf.readfile(str(ARCH))
    segs = []
    for e in doc.modelspace().query("LINE LWPOLYLINE"):
        if e.dxf.layer != "1":
            continue
        if e.dxftype() == "LINE":
            segs.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        else:
            p = [(q[0], q[1]) for q in e.get_points("xy")]
            if e.closed:
                p.append(p[0])
            if len(p) > 1:
                segs.append(LineString(p))
    cen = {r["OPENING_ID"]: r for r in rows("01_OPENING_CENSUS.csv")}
    for r in rows("06_LINTEL_CONCRETE_QTO.csv"):
        if r["LANE"] != "PROJECT_BASIS_QTO":
            continue
        c = cen[r["OPENING_ID"]]
        ang = math.radians(float(c["WALL_ANGLE_DEG"]))
        u, n = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        cx, cy = json.loads(c["CENTRE_ARCH_XY"])
        s0, s1 = json.loads(c["ALONG_WALL_MM"])
        om = cx * n[0] + cy * n[1]
        t = float(c["WALL_THICKNESS_MM"])
        P = lambda s_, o_: (s_ * u[0] + o_ * n[0], s_ * u[1] + o_ * n[1])  # noqa: E731
        inner = Polygon([P(s0 + 5, om - t / 2 + 5), P(s1 - 5, om - t / 2 + 5), P(s1 - 5, om + t / 2 - 5),
                         P(s0 + 5, om + t / 2 - 5)])
        assert not any(sg.crosses(inner) or sg.within(inner) for sg in segs), r["OPENING_ID"]
        assert abs((s1 - s0) - float(r["OPENING_W_MM"])) < 0.2
        for o_ in (om - t / 2, om + t / 2):
            for s_ in (s0, s1):
                probe = Polygon([P(s_ - 40, o_ - 2), P(s_ + 40, o_ - 2), P(s_ + 40, o_ + 2), P(s_ - 40, o_ + 2)])
                if c["START_JAMB" if s_ == s0 else "END_JAMB"] == "MASONRY_JAMB":
                    assert any(sg.intersects(probe) for sg in segs), (r["OPENING_ID"], s_)
