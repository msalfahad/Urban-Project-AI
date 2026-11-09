"""T-314: the development-villa inputs of V3.0.60 rebuild from the merged T-337 / T-348 r2 / T-567 ledgers (no drawing
needed); every line figure recomputed by R-T314-1 equals the FILL tables (+ the named T-348 / T-567 faces); the face
rows equal the T-567 face set of record key by key; every face / opening once; held never 0."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t314"))

import t314_inputs as L  # noqa: E402
from engine.source import arch_v3060 as A  # noqa: E402


@pytest.fixture(scope="module")
def d():
    return A.load_inputs(L.build())


def test_every_line_equals_the_fill_tables(d):
    exp = L.build()["expect"]
    assert len(d["lines"]) == 18 and set(exp) == set(d["lines"])
    for k, e in exp.items():
        f = A.line_figures(d, k)
        for part in ("gross", "net"):
            if part not in e:
                continue
            if e[part] is None:
                assert f[part] is None, k
            else:
                assert f[part] == pytest.approx(e[part], abs=1e-6), (k, part)


def test_storey_lines(d):
    gf = A.line_figures(d, "L-b05f70c92405dbcfbe62")
    assert gf["state"] == "RANGE" and gf["net"] == pytest.approx([376.694149, 410.179149])
    assert gf["deduct_fixed"] == pytest.approx(59.150029) and gf["deduct_held"] == [0.0, 33.485]
    assert gf["assumed_holes"] == pytest.approx(10.56) and gf["faces"] == 30 and gf["openings"] == 20
    f1 = A.line_figures(d, "L-8bb83e16cc7b104ab88b")            # T-337 234.525528 + T-348 / T-567 faces
    assert f1["state"] == "RANGE" and f1["net"] == pytest.approx([248.178057, 249.954348])  # moulding steps HELD
    f2 = A.line_figures(d, "L-d52c4f763b19aedf8b8b")
    assert (f2["state"], f2["net"], f2["assumed_holes"]) == ("ASSUMED", [117.305, 117.305], 2.2)


def test_every_face_and_opening_once_and_closure(d):
    assert len(d["faces"]) == 118 + 8 and len(d["openings"]) == 38
    held = {o: x["cap_m2"] for o, x in d["openings"].items() if x["status"] == "HELD"}
    assert held == {"W02": 28.485, "D-GF-07": 5.0}
    fixed = sum(x["hole_m2"] for x in d["openings"].values() if x["hole_m2"] is not None)
    assert fixed == pytest.approx(97.788801, abs=1e-6)                   # T-567 our_openings_full fixed
    # the face set of record: T-567 FACES (render classes) key by key, value by value, status by status
    with open(ROOT / "research" / "agents_t567" / "out" / "FACES_T567.csv", encoding="utf-8") as f:
        rec = {r["key"]: r for r in csv.DictReader(f) if r["class"] in ("STOREY", "PARAPET_OUTER", "PLINTH",
                                                                         "SLAB_EDGE")}
    mine = {k: x for k, x in d["faces"].items() if x["element"] in A.LEVELLED + ("SLAB_EDGE",)}
    assert set(rec) == set(mine) and len(rec) == 118
    for k, r in rec.items():
        assert (r["lo"] == "") == (mine[k]["lo"] is None) and r["status"] == mine[k]["status"], k
        if r["lo"]:
            assert (float(r["lo"]), float(r["hi"])) == pytest.approx((mine[k]["lo"], mine[k]["hi"]), abs=1e-6), k
    # T-567 gross 1,166.4517846 .. 1,185.4079770 = these faces + the parapet inner faces counted WITH the upturn zone
    # (T-324: one face 94.123 .. 99.558; the zone part is the waterproofing item, named MISSING here, never summed)
    lo = sum(x["lo"] for x in d["faces"].values() if x["lo"] is not None)
    hi = sum(x["hi"] for x in d["faces"].values() if x["hi"] is not None)
    inner_top_lo = sum(x["lo"] for x in d["faces"].values() if x["element"] in ("PARAPET_INNER", "PARAPET_TOP"))
    assert hi == pytest.approx(1185.4079770, abs=1e-6)
    assert lo + (120.959425 - inner_top_lo) == pytest.approx(1166.4517846, abs=1e-6)


def test_no_parapet_or_plinth_band_in_a_storey_line_and_slab_edge_blank(d):
    for k, ln in d["lines"].items():
        for fid in d["by_line"][k]:
            assert d["faces"][fid]["element"] == ln["element"]
    se = A.line_figures(d, "NEW FIN.EXT.FINISH SLAB-EDGE 1F")
    assert se["state"] == "BLANK" and se["net"] is None and len(se["faces_blank"]) == 6    # T-567: 6 by name
    assert "1F/NW-1/SLAB_EDGE_BELOW/slab_edge" not in d["faces"]            # T-348 r2: no physical face


def test_m_l_items_are_named_missing_never_numbers(d):
    keys = [x["key"] for x in d["items"]]
    assert "FIN.EXT.CORNERS (all floors)" in keys and "FIN.EXT.COPING" in keys
    assert all(set(x) == {"key", "unit", "status", "why"} for x in d["items"])
