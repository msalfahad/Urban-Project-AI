"""R9.1 christiannp post-freeze object-level comparison - package integrity (research only).

* every output matches INDEX.json;
* the Urban-only geometry extracts reproduce the frozen Urban registers they were derived from;
* crosswalk invariants: every Urban band / footing / tag / chain appears, every class is from the R9.1 list;
* the rebar parser columns are re-run live on the frozen token corpus (drift in an Urban parser fails here);
* firewall: no production module refers to this package or to the donor dataset, and R5 stays rejected;
* when the frozen christiannp dataset is present (R9_1_CHRIS_DIR), the whole package rebuilds byte for byte.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "R9_1_CHRIS_POST_FREEZE"
sys.path.insert(0, str(PKG / "scripts"))

import build_r9_1 as B  # noqa: E402

CHRIS_DIR = os.environ.get("R9_1_CHRIS_DIR")


def rows(name):
    return list(csv.DictReader(open(PKG / name, encoding="utf-8")))


def J(rel):
    return json.loads((PKG / rel).read_text(encoding="utf-8"))


def test_index_hashes():
    idx = J("INDEX.json")
    assert idx["stamp"]["URBAN_ENGINE_COMMIT"] == "2c00561"
    for rel, h in idx["files"].items():
        assert hashlib.sha256((PKG / rel).read_bytes()).hexdigest() == h, rel
    for n in ("00_EXECUTIVE_SUMMARY.md", "01_CHRIS_FORENSIC_INTAKE.md", "02_OBJECT_GAP_REGISTER.csv",
              "03_GB_OBJECT_CROSSWALK.csv", "04_GB_TECHNIQUE_ANALYSIS.md", "05_GROUND_SLAB_ROUTE_COMPARISON.csv",
              "06_BEAM_BINDING_CROSSWALK.csv", "07_WALL_PAIR_CROSSWALK.csv", "08_FOOTING_OCCURRENCE_CROSSWALK.csv",
              "09_COLUMN_CROSSWALK.csv", "10_SLAB_OPENING_CROSSWALK.csv", "11_REBAR_TOKEN_CORPUS.csv",
              "12_CHRIS_MANUAL_DECISION_GAP.csv", "13_DONOR_CODE_TECHNIQUES.md", "14_DONOR_TECHNIQUE_MATRIX_UPDATED.csv",
              "15_QUANTITY_RECONCILIATION_UPDATED.csv", "16_PRE_S4_DECISION.md", "17_TEST_FIXTURE_BACKLOG.md"):
        assert n in idx["files"], n


def test_input_ledger_identifies_frozen_dataset():
    led = J("CHRIS_INPUT_LEDGER.json")
    assert led["zip_sha256"] == B.ZIP_SHA256 and led["manifest_sha256"] == B.MANIFEST_SHA256
    assert led["drawings_match_urban"] == {"P7757.dxf": True, "ST7757.dxf": True}
    assert all(f["UNCHANGED"] for f in led["source_integrity"]["files"])
    assert len(led["files_read"]) >= 30


def test_urban_extracts_reproduce_frozen_registers():
    gb = J("urban_extract/URBAN_GB_GEOMETRY_EXTRACT.json")
    G = json.loads((ROOT / "tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json").read_text())["ground"]
    assert len(gb["bands"]) == G["bands"] == 43
    kept = [p for b in gb["bands"] for p in b["pieces"] if p["kept_as_span"]]
    assert len(kept) == len(G["spans"]) == 59
    assert abs(sum(p["length_m"] for p in kept) - sum(s["length_m"] for s in G["spans"])) < 1e-6
    assert {b["band_id"] for b in gb["bands"]} == {s["band"] for s in G["spans"]}
    assert J("urban_extract/URBAN_GROUND_CELL_GEOMETRY_EXTRACT.json")["REPRODUCES_FROZEN_EXTRACT"] is True
    so = J("urban_extract/URBAN_SLAB_OPENING_GEOMETRY_EXTRACT.json")["floors"]
    assert all(v["reproduction"]["REPRODUCES_FROZEN_B2A1"] for v in so.values())


def test_classes_are_from_the_r9_1_list():
    for name in ("02_OBJECT_GAP_REGISTER.csv", "03_GB_OBJECT_CROSSWALK.csv", "05_GROUND_SLAB_ROUTE_COMPARISON.csv",
                 "06_BEAM_BINDING_CROSSWALK.csv", "07_WALL_PAIR_CROSSWALK.csv", "08_FOOTING_OCCURRENCE_CROSSWALK.csv",
                 "09_COLUMN_CROSSWALK.csv", "10_SLAB_OPENING_CROSSWALK.csv"):
        for r in rows(name):
            c = r.get("DIFFERENCE_CLASS")
            if c:
                assert c in B.CLASSES, (name, c)
                assert "lower" not in c.lower() and "higher" not in c.lower()


def test_ground_beam_crosswalk_covers_every_object():
    gb = [r for r in rows("03_GB_OBJECT_CROSSWALK.csv") if r["TRADE"] == "GROUND_BEAM" and r["CHRIS_OBJECT_ID"].startswith("S")]
    assert len(gb) == 44
    urban = Counter(r["URBAN_OBJECT_ID"].split(" ")[0] for r in gb if r["URBAN_OBJECT_ID"] != "(none)")
    assert len(urban) == 43 and set(urban.values()) == {1}
    missed = [r for r in gb if r["DIFFERENCE_CLASS"] == "URBAN_MISSED_PHYSICAL_OBJECT"]
    assert [r["SOURCE_HANDLES"] for r in missed] == ["114|115"]


def test_other_crosswalks_cover_every_object():
    ft = rows("08_FOOTING_OCCURRENCE_CROSSWALK.csv")
    assert sum(1 for r in ft if r["CHRIS_ID"].startswith("FO") and r["URBAN_ID"]) == 26
    bm = [r for r in rows("06_BEAM_BINDING_CROSSWALK.csv") if r["CHRIS_TAG_ID"]]
    assert len(bm) == 119 and all(r["URBAN_BEAM_ID"] for r in bm)
    co = [r for r in rows("09_COLUMN_CROSSWALK.csv") if r["CHRIS_ID"].startswith("COL")]
    assert len(co) == 41 and len({r["URBAN_CHAIN"] for r in co}) == 39
    md = rows("12_CHRIS_MANUAL_DECISION_GAP.csv")
    assert [r["DECISION_ID"] for r in md] == [f"MD{i:02d}" for i in range(1, 19)]
    assert {r["DOES_URBAN_ALREADY_HANDLE_DETERMINISTICALLY"] for r in md} <= {"YES", "PARTIAL", "NO"}


def test_rebar_parser_columns_rerun_live():
    """The parser columns are recomputed from the raw token with the current Urban parsers (no christiannp data)."""
    for r in rows("11_REBAR_TOKEN_CORPUS.csv"):
        tok = r["RAW_TOKEN"]
        _, ecls = B._expected(tok)
        if ecls.startswith("COUNT_DIA_SPLIT_CELLS"):
            assert B._p_cells(tok) == r["SG_BAR_FROM_CELLS"], tok
        else:
            assert B._p_sg(tok) == r["SG_PARSE_BAR"], tok
            assert B._p_ss(tok) == r["SS_BAR_SPEC"], tok
            assert B._p_srb(tok) == r["SRB_PARSE"], tok
    foot = [r for r in rows("11_REBAR_TOKEN_CORPUS.csv") if "FOOTING" in r["ELEMENTS"]]
    assert foot and all(not r["URBAN_DISAGREEMENT"].startswith("SPLIT") for r in foot)


def test_r5_stays_rejected_and_raster_is_oracle_only():
    tm = {r["TECHNIQUE"]: r for r in rows("14_DONOR_TECHNIQUE_MATRIX_UPDATED.csv")}
    assert tm["R5 equal sharing"]["DECISION"] == "REJECT"
    assert tm["Raster flood fill"]["DECISION"] == "ORACLE_ONLY"
    assert all(r["ROUTE_CLASS"] == "ORACLE_ONLY" for r in rows("05_GROUND_SLAB_ROUTE_COMPARISON.csv")
               if r["ROUTE"].startswith("RASTER"))


def test_production_never_refers_to_this_package_or_the_donor():
    # the generic comparison-scope view label CHRISTIANNP_VIEW (engine/source/comparison_scope.py) is a name, not data;
    # what must never appear is a path into this package or into the frozen donor dataset
    pat = re.compile(r"R9_1_CHRIS_POST_FREEZE|CHRISTIANNP_FORENSIC_RERUN|christiannp_blind_process")
    for p in (ROOT / "engine").rglob("*.py"):
        assert not pat.search(p.read_text(encoding="utf-8", errors="ignore")), p


@pytest.mark.skipif(not CHRIS_DIR or not Path(CHRIS_DIR).is_dir(), reason="frozen christiannp dataset not present")
def test_rebuild_byte_for_byte(tmp_path):
    before = {k: (PKG / k).read_bytes() for k in J("INDEX.json")["files"]}
    subprocess.run([sys.executable, str(PKG / "scripts" / "build_r9_1.py"), CHRIS_DIR], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k
