"""T-249: the development villa's committed engine-independent inventory, crosswalk and W18 / W03 deltas.

Invariants: 29 windows (GF 12, 1F 13, 2F 4), 27 doors (GF 14, 1F 10, 2F 3) + 1 gate, 2 arches, each existing by a plan
symbol with its entity handles (never by the engine); handles unique; the crosswalk to the T-198 census agrees 29 / 29
windows and 28 / 28 door elements with nothing missing or extra; W18 and W03 carry their census ids by attributes (no
engine record exists for either); the W18 + W03 window-line delta is 1.080 + 28.251 = 29.331 m2 and 2 pcs, applied
nowhere; no drawing coordinate is committed; T-236's census reader can take this file in place of the T-198 seed.
The byte-for-byte rebuild needs the private DXF (URBAN_P7757_DXF) and a V2.9 run directory (URBAN_T249_RUN).
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t249"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t236"))


def _rows(name):
    with open(HERE / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_counts_by_kind_and_floor():
    inv = _rows("OPENINGS_T249.csv")
    n = lambda k, f=None: sum(1 for r in inv if r["KIND"] == k and (f is None or r["FLOOR"] == f))  # noqa: E731
    assert (n("WINDOW"), n("WINDOW", "GF"), n("WINDOW", "1F"), n("WINDOW", "2F")) == (29, 12, 13, 4)
    assert (n("DOOR"), n("DOOR", "GF"), n("DOOR", "1F"), n("DOOR", "2F")) == (27, 14, 10, 3)
    assert n("GATE") == 1 and n("OPENING") == 2
    assert len(inv) == 59


def test_existence_is_never_the_engine():
    inv = _rows("OPENINGS_T249.csv")
    for r in inv:
        assert "PLAN_SYMBOL" in r["EXISTENCE_SOURCES"].split("+"), r["ID"]
        assert "ENGINE" not in r["EXISTENCE_SOURCES"]
        assert r["HANDLES"].strip(), r["ID"]
        assert r["STATE"] == "LOCATED"
    hs = [h for r in inv for h in r["HANDLES"].split()]
    assert len(hs) == len(set(hs))


def test_w18_w03_bound_without_engine():
    inv = {r["ID"]: r for r in _rows("OPENINGS_T249.csv")}
    for w in ("W18", "W03"):
        assert w in inv and not inv[w]["ID_BINDING"].startswith("engine")
        assert inv[w]["ENGINE_REF"].startswith("none")
    assert inv["W18"]["WIDTH_PLAN_M"] == "0.5000" and "T194:NW:1F" in inv["W18"]["ELEVATION_REFS"]
    assert inv["W03"]["WIDTH_PLAN_M"] == ""                                # curved: width by Q-38 A, never the box
    assert "6.658, 6.703, 6.747, 6.792" in inv["W03"]["NOTE"]           # the four glass lines Q-38 names
    assert "pcs HELD 1 .. 2" in inv["W02"]["NOTE"]


def test_crosswalk_agrees_and_names_scope():
    cw = _rows("CROSSWALK_T249.csv")
    s = json.loads((HERE / "summary.json").read_text())
    for k in ("DOOR", "WINDOW"):
        assert s["crosswalk"][k]["MISSING_FROM_LIST"] == [] and s["crosswalk"][k]["EXTRA_IN_LIST"] == []
    assert len(s["crosswalk"]["WINDOW"]["AGREE"]) == 29 and len(s["crosswalk"]["DOOR"]["AGREE"]) == 28
    st = {r["CENSUS_ID"]: r["STATUS"] for r in cw}
    assert all(st[i] == "NOT_IN_SCOPE" for i in ("SX-01", "SX-03", "L-GF-01", "L-1F-01", "L-2F-01", "U-01",
                                                  "P-GF-01", "P-1F-01", "P-GF-05"))
    assert not any(v == "MISSING_FROM_LIST" or v == "EXTRA_IN_LIST" for v in st.values())
    assert s["dxf_opening_tags_found"] == 0 and s["schedule_issued"] is False
    assert s["id_binding"]["unbound"] == 0


def test_elevation_binding_has_no_ambiguity():
    s = json.loads((HERE / "summary.json").read_text())
    for fac, r in s["elevation_binding"].items():
        assert r["ambiguous"] == [] and r["unbound"] == [] and r["bound"] == r["features"], fac
    inv = _rows("OPENINGS_T249.csv")
    res = [int(x) for r in inv for x in r["ELEV_RESIDUAL_MM"].split()]
    assert res and max(res) <= 50
    assert s["windows_with_elevation"] == 23


def test_delta_w18_w03():
    d = _rows("DELTA_T249.csv")
    m2 = [r for r in d if r["CONSEQUENCE"] == "window supply line" and r["UNIT"] == "m2"]
    assert {r["OPENING"]: float(r["DELTA"]) for r in m2} == {"W18": 1.080, "W03": 28.251}
    assert round(sum(float(r["DELTA"]) for r in m2), 3) == 29.331
    assert sum(int(r["DELTA"]) for r in d if r["UNIT"] == "nr") == 2
    assert round(0.50 * 2.16, 3) == 1.080 and round(6.57 * 4.30, 3) == 28.251
    held = [r for r in d if r["STATUS"] == "HELD"]
    assert held and all(r["DELTA"] == "HELD" for r in held)              # held is never 0
    assert all(r["IN_V308"] in ("absent", "n/a", "n/a (research)") for r in d)


def test_no_coordinates_committed():
    big = re.compile(r"(?<![\w-])-?\d{5,}\.\d+|(?<![\w-])-\d{6,}")      # not a hash inside an id
    for name in ("OPENINGS_T249.csv", "CROSSWALK_T249.csv", "DELTA_T249.csv", "summary.json"):
        assert not big.search((HERE / name).read_text()), name


def test_t236_reader_takes_this_file(monkeypatch):
    import alsenan_t236 as T

    real = T._csv

    def swap(p):
        return real(str(HERE / "OPENINGS_T249.csv")) if str(p).endswith("OPENINGS_T198.csv") else real(p)

    monkeypatch.setattr(T, "_csv", swap)
    out, tokens, ids = T.opening_inventories()
    by = {o["trade"]: o for o in out}
    assert len(by["DOORS"]["elements"]) == 27 and len(by["WINDOWS"]["elements"]) == 29
    assert {"W18", "W03"} <= {e["label"] for e in by["WINDOWS"]["elements"]}


@pytest.mark.skipif(not (os.environ.get("URBAN_P7757_DXF") and os.environ.get("URBAN_T249_RUN")),
                    reason="private DXF / engine run not provided (URBAN_P7757_DXF, URBAN_T249_RUN)")
def test_rebuild_byte_for_byte():
    import alsenan_t249 as A
    assert A.main(["check", "--dxf", os.environ["URBAN_P7757_DXF"], "--engine-run", os.environ["URBAN_T249_RUN"]]) == 0
