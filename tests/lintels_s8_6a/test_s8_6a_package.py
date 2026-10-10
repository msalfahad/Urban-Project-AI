"""S8.6A (research/alsenan_lintels_s8_6a): the dated correction layer over the frozen S8.6 lintel release.

- the S8.6 freeze and every earlier freeze verify, and no S8.6 file differs from its manifest;
- every one of the 14 released lintels has one corrected state; the six named cases are classified as the drawn
  geometry says, and the glazed opening is not released automatically;
- the corrected concrete and steel are recomputed by hand from the frozen rows; the reconciliation closes by floor;
- the shared corner prism has exactly one released owner;
- cover and stirrup readings are labelled and their sensitivities ordered;
- the opening census is unchanged (74 ids) and the R5 / V3b missed populations are explained;
- with the private drawing: a byte-identical rebuild and an independent shapely check of every end."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_lintels_s8_6a"
S86 = ROOT / "research" / "alsenan_lintels_s8_6"
MAN = PKG / "12_S8_6A_CORRECTION_MANIFEST.json"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists()), reason="private client drawings not restored")
EXPECTED = {"LT-OP-GF-005": "BLOCKED_BEARING_REQUIREMENT", "LT-OP-GF-021": "BLOCKED_BEARING_REQUIREMENT",
            "LT-OP-GF-029": "BLOCKED_BEARING_REQUIREMENT", "LT-OP-1F-017": "BLOCKED_BEARING_REQUIREMENT",
            "LT-OP-GF-013": "BLOCKED_COLUMN_CONNECTION", "LT-OP-GF-018": "BLOCKED_COLUMN_CONNECTION",
            "LT-OP-GF-014": "BLOCKED_HEAD_FUNCTION_UNRESOLVED"}
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def F(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def s():
    return J(PKG / "11_S8_6A_SUMMARY.json")


def test_manifest_and_untouched_freeze():
    m = J(MAN)
    assert m["state"] == "DATED_CORRECTION_LAYER" and m["baseline"] == "974bff2" and m["references_read"] == []
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o
    s86 = J(S86 / "15_S8_6_FREEZE_MANIFEST.json")
    DR.verify_frozen(S86 / "15_S8_6_FREEZE_MANIFEST.json", ROOT)
    for o, h in s86["outputs"].items():
        assert hashlib.sha256((S86 / o).read_bytes()).hexdigest() == h, o
    assert m["s8_6_manifest_sha256"] == hashlib.sha256((S86 / "15_S8_6_FREEZE_MANIFEST.json").read_bytes()).hexdigest()


def test_every_previous_freeze_verifies(s):
    pv = rows(PKG / "10_PREVIOUS_FREEZE_VERIFICATION.csv")
    man = [r for r in pv if r["MANIFEST"].endswith("FREEZE_MANIFEST.json")]
    assert len(man) == 23 and {r["RESULT"] for r in pv} == {"VERIFIED"} and "S8.6" in {r["ROUND"] for r in man}
    assert len(pv) == 23 + 3 + 4                       # + the S8.3 errata files and the four register indexes
    for r in man:
        DR.verify_frozen(ROOT / r["MANIFEST"], ROOT)


def test_fourteen_states(s):
    reg = {r["LINTEL_ID"]: r for r in rows(PKG / "01_RELEASE_AUTHORITY_REGISTER.csv")}
    assert len(reg) == 14
    for lid, r in reg.items():
        assert r["CORRECTED_STATE"] == EXPECTED.get(lid, "RETAINED_PROJECT_BASIS_QTO"), lid
        if r["CORRECTED_STATE"] == "RETAINED_PROJECT_BASIS_QTO":
            assert F(r["START_AVAILABLE_MM"]) >= 400 and F(r["END_AVAILABLE_MM"]) >= 400
            assert r["BEAMS_OVER_OPENING"] == "[]" and r["OPENING_TYPE"] in ("1_INTERNAL_DOOR",
                                                                             "7_OPEN_ARCHWAY_OR_PASSAGE")
    six = rows(PKG / "02_SIX_CASE_INVESTIGATION.csv")
    assert {r["LINTEL_ID"] for r in six} == {k for k in EXPECTED if k != "LT-OP-GF-014"}
    for r in six:
        assert F(r["INDEPENDENT_AVAILABLE_MM"]) < 400
        if r["CLASSIFICATION"] == "BLOCKED_COLUMN_CONNECTION":
            assert r["TERMINATOR"] == "COLUMN" and 99 < F(r["INDEPENDENT_AVAILABLE_MM"]) < 102


def test_independent_bearing_agrees_with_frozen_geometry():
    for r in rows(PKG / "03_BEARING_AND_COLUMN_CONNECTION_AUDIT.csv"):
        if r["TERMINATOR"] != "OBLIQUE_JUNCTION":
            assert r["AGREES_WITH_FROZEN"] == "True", (r["LINTEL_ID"], r["END"])
        assert "none stated" in r["COLUMN_CONNECTION_DETAIL"]


def test_corrected_quantities_by_hand(s):
    conc = {r["LINTEL_ID"]: r for r in rows(S86 / "06_LINTEL_CONCRETE_QTO.csv") if r["LANE"] == "PROJECT_BASIS_QTO"}
    bars = [r for r in rows(S86 / "07_LINTEL_REBAR_QTO.csv") if r["VIEW"] == "PROJECT_BASIS_QTO"]
    kept = set(s["retained"])
    assert len(kept) == 7
    m3 = defaultdict(float)
    for lid in kept:
        c = conc[lid]
        m3[c["FLOOR"]] += F(c["B_MM"]) * F(c["D_MM"]) * F(c["LENGTH_MM"]) / 1e9      # gross: 1F-018 owns its corner
    kg = defaultdict(float)
    for b in bars:
        if b["LINTEL_ID"] in kept:
            d = int(b["DIA_MM"])
            kg[(b["FLOOR"], d)] += int(b["COUNT"]) * F(b["EACH_MM"]) / 1000.0 * d * d / 162.0
    assert s["corrected"]["m3"] == pytest.approx(sum(m3.values()), abs=1e-9)
    assert s["corrected"]["kg"] == pytest.approx(sum(kg.values()), abs=1e-6)
    for f, v in s["corrected"]["by_floor"].items():
        assert v["m3"] == pytest.approx(m3.get(f, 0.0), abs=1e-9)
        for d, k in v["kg_by_dia"].items():
            assert k == pytest.approx(kg.get((f, int(d)), 0.0), abs=1e-6)
    assert s["corrected"]["m3"] == pytest.approx(0.366, abs=1e-9)


def test_reconciliation_closes_by_floor():
    rec = rows(PKG / "09_QUANTITY_RECONCILIATION.csv")
    assert rec[0]["STAGE"] == "FROZEN" and F(rec[0]["M3"]) == pytest.approx(0.745261681, abs=1e-9)
    assert F(rec[0]["KG"]) == pytest.approx(96.427279858, abs=1e-8) and rec[0]["LINTELS"] == "14"
    assert rec[-1]["STAGE"] == "CORRECTED_RETAINED"
    for col in ("M3", "KG", "M3_GF", "M3_1F", "M3_2F", "KG_GF", "KG_1F", "KG_2F"):
        assert sum(F(r[col]) for r in rec[:-1]) == pytest.approx(F(rec[-1][col]), abs=1e-6), col
    re_ = [r for r in rec if r["STAGE"] == "OVERLAP_REALLOCATION"]
    assert len(re_) == 1 and F(re_[0]["M3"]) == pytest.approx(0.0045, abs=1e-12)


def test_shared_corner_one_owner(s):
    (ov,) = s["overlap"]
    assert ov["pair"] == ["LT-OP-1F-017", "LT-OP-1F-018"] and ov["frozen_owner"] == "LT-OP-1F-017"
    assert ov["corrected_owner"] == "LT-OP-1F-018" and ov["m3"] == pytest.approx(150 * 150 * 200 / 1e9)
    view = {r["LINTEL_ID"]: r for r in rows(PKG / "05_CORRECTED_ELIGIBLE_RELEASE_VIEW.csv")}
    assert F(view["LT-OP-1F-018"]["CORRECTED_M3"]) == pytest.approx(0.054)
    assert F(view["LT-OP-1F-017"]["CORRECTED_M3"]) == 0.0
    assert F(view["LT-OP-1F-017"]["CONDITIONAL_M3"]) == pytest.approx(0.043792802 - 0.0045, abs=1e-9)


def test_cover_and_stirrup_authority_labels():
    rv = rows(PKG / "04_COVER_AND_STIRRUP_AUTHORITY.csv")
    comp = {r["COMPONENT"]: r["AUTHORITY"] for r in rv if r["RECORD"] == "COMPONENT"}
    assert comp["COVER"] == "PROJECT_WIDE_RULE_SCOPE_NOT_CONFIRMED"
    assert comp["STIRRUP_RATE"] == "EXPLICIT_PROJECT_DETAIL" and comp["STIRRUP_COUNT"] == "URBAN_MEASUREMENT_CONVENTION"
    assert comp["HOOKS_BENDS_LAPS_ANCHORAGE"] == "UNRESOLVED_FABRICATION_DETAIL"
    cov = [F(r["KG"]) for r in rv if r["RECORD"] == "COVER_SENSITIVITY"]
    assert cov == sorted(cov, reverse=True) and len(cov) == 5
    st = {r["COMPONENT"]: F(r["COUNT"]) for r in rv if r["RECORD"] == "STIRRUP_COUNT_READING"}
    assert st["CLEAR_SPAN_RATE"] < st["EQUIVALENT_RATE"] <= st["RATE_COUNT"] < st["SPACING_WITH_ENDS"]


def test_rebar_reclassification():
    rr = rows(PKG / "07_REINFORCEMENT_RECLASSIFICATION.csv")
    reg = {r["LINTEL_ID"]: r["CORRECTED_STATE"] for r in rows(PKG / "01_RELEASE_AUTHORITY_REGISTER.csv")}
    assert len(rr) == 42
    for r in rr:
        assert (r["CORRECTED_LANE"] == "PROJECT_BASIS_QTO") == (reg[r["LINTEL_ID"]] == "RETAINED_PROJECT_BASIS_QTO")


def test_census_unchanged_and_explained(s):
    cv = rows(PKG / "08_OPENING_CENSUS_VERIFICATION.csv")
    ids = [r["OPENING_ID"] for r in cv if r["RECORD"] == "OPENING"]
    s86 = [r["OPENING_ID"] for r in rows(S86 / "01_OPENING_CENSUS.csv") if r["RECORD"] == "OPENING"]
    assert sorted(ids) == sorted(s86) and len(ids) == 74
    c = s["census"]
    assert len(c["r5_missed"]) == 9 and len(c["v3b_missed"]) == 10 and c["difference"] == ["OP-GF-B01"]


def test_hygiene_and_registry():
    for o in J(MAN)["outputs"]:
        assert not HYG.search((PKG / o).read_text(encoding="utf-8")), o
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"engine/source/lintel_release_audit.py"' in reg and '"research/alsenan_lintels_s8_6a/build_s8_6a.py"' in reg
    src = (PKG / "build_s8_6a.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and "V3B_M3" not in src


@needs_inputs
def test_rebuild_byte_identical():
    m = J(MAN)
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_6a.py")], check=True, cwd=ROOT, capture_output=True)
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o


@needs_inputs
def test_ends_checked_with_a_different_method():
    """shapely: just past a short end the centreline is in open space (or inside a column); every retained end is
    masonry over its full 400 mm (inside a wall: faces both sides across one axis)."""
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon
    msp = ezdxf.readfile(str(ARCH)).modelspace()
    segs, cols = [], []
    for e in msp:
        if e.dxftype() == "LINE" and e.dxf.layer == "1":
            segs.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        elif e.dxftype() == "LWPOLYLINE":
            p = [(q[0], q[1]) for q in e.get_points("xy")]
            if e.dxf.layer == "1" and len(p) > 1:
                segs.append(LineString(p + ([p[0]] if e.closed else [])))
            elif e.dxf.layer == "S-COL.BON" and e.closed:
                cols.append(Polygon(p).convex_hull)
    cen = {r["OPENING_ID"]: r for r in rows(S86 / "01_OPENING_CENSUS.csv")}

    def hits(a, b):
        L_ = LineString([a, b])
        return any(L_.intersects(sg) for sg in segs)

    def free(p, n, half):
        """no wall face within half a wall thickness on either side across the wall: open centreline"""
        return not hits(p, (p[0] + n[0] * half, p[1] + n[1] * half)) and not hits(p, (p[0] - n[0] * half,
                                                                                      p[1] - n[1] * half))

    for r in rows(PKG / "03_BEARING_AND_COLUMN_CONNECTION_AUDIT.csv"):
        o = cen[r["OPENING_ID"]]
        ang = math.radians(float(o["WALL_ANGLE_DEG"]))
        u, n = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        cx, cy = json.loads(o["CENTRE_ARCH_XY"])
        s0, s1 = json.loads(o["ALONG_WALL_MM"])
        om = cx * n[0] + cy * n[1]
        t = float(o["WALL_THICKNESS_MM"])
        sj, sg = (s0, -1) if r["END"] == "START" else (s1, 1)
        P = lambda d: ((sj + sg * d) * u[0] + om * n[0], (sj + sg * d) * u[1] + om * n[1])  # noqa: E731
        av = float(r["INDEPENDENT_AVAILABLE_MM"])
        if r["END_STATE"] == "MASONRY_OK":
            run = 0
            for d in range(10, 400, 10):
                p = P(d)
                assert not any(c.contains(Point(p)) for c in cols), (r["LINTEL_ID"], r["END"], d)
                run = run + 10 if free(p, n, t / 2 + 5) else 0
                assert run <= 250, (r["LINTEL_ID"], r["END"], d)          # only a wall crossing is open
        elif r["TERMINATOR"] == "COLUMN":
            assert any(c.contains(Point(P(av + 30))) for c in cols), r["LINTEL_ID"]
        elif r["TERMINATOR"] in ("T_JUNCTION", "L_CORNER"):
            p = P(av + 40)
            assert not hits((p[0] - n[0] * (t / 2 + 5), p[1] - n[1] * (t / 2 + 5)),
                            (p[0] + n[0] * (t / 2 + 5), p[1] + n[1] * (t / 2 + 5))), (r["LINTEL_ID"], r["END"])
