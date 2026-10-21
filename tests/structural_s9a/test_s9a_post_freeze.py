"""S9A post-freeze comparison: downstream of the freeze, classification only, nothing released."""

from __future__ import annotations

import csv
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_structural_s9a"
PF = PKG / "post_freeze"
MANIFEST = PKG / "18_S9A_CORRECTION_MANIFEST.json"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
FORBIDDEN = (44.19, 352.436075, 77.6305, 75.09, 39.7515, 65.965875, 59.8174, 21.8328, 12.348, 337.812, 333.173,
             22.619, 22.916)


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_downstream():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    DR.verify_frozen(MANIFEST, ROOT)
    assert not [k for k in list(m["inputs"]) + list(m["outputs"]) + list(m["code"]) if "post_freeze" in k]
    s = json.loads((PF / "05_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen"]["state"] == "DATED_CORRECTION_LAYER" and s["frozen"]["frozen_manifests_verified"] == 30
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0}


def test_census_hatch_zones_are_the_s9a_bands_and_ca_is_bound():
    bands = {b["DXF_HANDLE"]: b for b in rows(PKG / "03_BAND_CORRECTION_REGISTER.csv")}
    cw = rows(PF / "03_PRE_S8_BAND_CROSSWALK.csv")
    hz = [c for c in cw if c["PRE_S8_ID"].startswith("HZ-")]
    assert len(hz) == 8 and {c["DXF_HANDLE"] for c in hz} == set(bands)
    for c in hz:
        assert c["CLASS"] == "SAME_OBJECT" and abs(float(c["AREA_DIFF_M2"])) <= 0.001
        assert c["PRE_S8_ID"].endswith(c["DXF_HANDLE"]) and c["S9A_BAND"] == bands[c["DXF_HANDLE"]]["BAND_ID"]
    ca = next(c for c in cw if not c["PRE_S8_ID"].startswith("HZ-"))
    assert ca["CLASS"] == "SAME_OBJECT" and ca["S9A_BAND"] == "S9A-CP-01"
    assert float(ca["V3B_CA_LENGTH_M"]) == float(ca["S9A_BAND_LENGTH_M"]) == 1.15


def test_beam_and_ground_beam_comparison_classify_without_choosing():
    b = {r["STOREY"]: r for r in rows(PF / "01_BEAMS_VS_V3B.csv")}
    tot = {r["GROUP"]: r for r in rows(PKG / "06_BEAM_CONVENTION_TOTALS.csv") if r["SET"].startswith("conditional")}
    for st in ("GF", "1F", "2F"):
        assert float(b[st]["S9A_READING_A_M3"]) == float(tot[f"STOREY {st}"]["TOTAL_DEPTH_M3"])
        assert float(b[st]["S9A_READING_B_M3"]) == float(tot[f"STOREY {st}"]["BELOW_SLAB_M3"])
        assert float(b[st]["V3B_MINUS_S9A_DOWNSTAND_M3"]) == round(float(b[st]["V3B_TECHNICAL_M3"]) -
                                                                  float(b[st]["S9A_READING_A_DOWNSTAND_M3"]), 6)
    assert math.isclose(float(b["ALL"]["V3B_TECHNICAL_M3"]), math.fsum(float(b[s]["V3B_TECHNICAL_M3"])
                                                                      for s in ("GF", "1F", "2F")), abs_tol=1e-6)
    assert all("RFI-A01 stands" in r["EXPLANATION"] for r in b.values())
    g = {r["ITEM"]: r for r in rows(PF / "02_GROUND_BEAMS_AND_COLUMNS_VS_V3B.csv")}
    assert g["GROUND_BEAMS_EXTERIOR"]["V3B_STATUS"] == "BLOCKED"
    assert "RFI-A05" in g["GROUND_BEAMS_INTERIOR"]["EXPLANATION"]
    f = rows(PF / "04_POST_FREEZE_FINDINGS.csv")
    assert [x["ID"] for x in f] == [f"PF-0{i}" for i in range(1, 8)] and all(x["CLASS"] and x["ACTION"] for x in f)


def test_hygiene_no_benchmark_figure_and_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.suffix in (".md", ".csv", ".json")}
    assert len(before) == 6
    for name, b in before.items():
        t = b.decode("utf-8")
        assert not HYG.search(t), name
        for n in re.findall(r"(?<![0-9.])[0-9]+\.[0-9]+(?![0-9])", t):
            v = float(n)
            assert not any(abs(v - x * k) <= 1e-9 * max(1.0, abs(x * k)) for x in FORBIDDEN for k in (1, 1000))
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True, timeout=600)
    assert {p.name: p.read_bytes() for p in PF.iterdir() if p.suffix in (".md", ".csv", ".json")} == before
