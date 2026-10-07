"""PRE-S5 ground-system readiness package (research/pre_s5_ground_system_readiness).

* every output matches INDEX.json; the package rebuilds byte for byte from ST7757.dxf when it is present;
* the OLD network reproduces the frozen V3 register; every geometry change is MULTI_PARTNER_PAIRING or ARC_OVERLAP;
* conservation: every sheet line / layer-1 face / arc accounted, covered + unpaired = face length;
* applicability keeps the literal p.13 length conditions (L < 5, L = 5, L > 5) and the two lower rows distinct;
* readiness never publishes a kg, a conflicted member never releases, missing depth blocks stirrups only;
* S5 provenance = the S4 contract + member fields; the production path carries no donor value or id.
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

from engine.source import ground_system_provenance as GP

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "pre_s5_ground_system_readiness"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DXF = Path(os.environ.get("PRE_S5_ST7757_DXF") or ROOT / "data/inputs/by_sha256" / f"{DXF_SHA}.dxf")
sys.path.insert(0, str(PKG))


def J(n):
    return json.loads((PKG / n).read_text(encoding="utf-8"))


def rows(n):
    return list(csv.DictReader(open(PKG / n, encoding="utf-8")))


@pytest.fixture(scope="module")
def summary():
    return J("02_GROUND_BEAM_NETWORK_SUMMARY.json")


def test_index_matches_outputs_inputs_and_code():
    idx = J("INDEX.json")
    for group, base in (("outputs", PKG), ("inputs", ROOT), ("code", ROOT)):
        for k, h in idx[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    assert idx["drawing_sha256"] == DXF_SHA and re.match(r"^[0-9a-f]{7}\+code:[0-9a-f]{16}$", idx["engine_stamp"])


@pytest.mark.skipif(not DXF.is_file(), reason="ST7757.dxf not present")
def test_rebuild_is_byte_identical():
    idx = J("INDEX.json")
    before = {k: (PKG / k).read_bytes() for k in idx["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_pre_s5.py"), str(DXF)], check=True, capture_output=True,
                   cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


# ------------------------------------------------------------------ geometry
def test_old_network_reproduces_frozen_v3_and_r4(summary):
    v3 = json.loads((ROOT / "tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json").read_text())["ground"]
    assert summary["old"]["bands"] == v3["bands"] and summary["old"]["spans"] == len(v3["spans"])
    assert summary["old"]["span_length_m"] == pytest.approx(sum(s["length_m"] for s in v3["spans"]), abs=1e-3)
    assert summary["old"]["exterior_spans"] == sum(1 for s in v3["spans"] if s["exterior"])
    assert summary["conservation"]["old_footprint_test_reproduces_r4"]


def test_every_change_is_one_of_the_two_rules(summary):
    ch = rows("01_GROUND_BEAM_GEOMETRY_CHANGELOG.csv")
    assert ch and {r["CAUSE"] for r in ch} <= {"MULTI_PARTNER_PAIRING", "ARC_OVERLAP"}
    bands = [r for r in ch if r["OBJECT"] == "BAND"]
    assert Counter(r["CAUSE"] for r in bands) == {"MULTI_PARTNER_PAIRING": 1, "ARC_OVERLAP": 1}
    mp = next(r for r in bands if r["CAUSE"] == "MULTI_PARTNER_PAIRING")
    arc = next(r for r in bands if r["CAUSE"] == "ARC_OVERLAP")
    assert float(mp["DELTA_M"]) > 0 and float(arc["DELTA_M"]) < 0           # recovered strip; over-measure removed
    # geometry-neutral span changes are exterior-proxy knock-ons, and say so
    for r in ch:
        if r["OBJECT"] == "SPAN" and abs(float(r["DELTA_M"] or 0)) < 1e-3:
            assert r["DETAIL"].startswith(("EXTERIOR_FLAG", "EXTERIOR_FOOTPRINT_FLAG")), r
    assert summary["new"]["bands"] == summary["old"]["bands"]
    assert summary["new"]["band_length_m"] == pytest.approx(
        summary["old"]["band_length_m"] + sum(float(r["DELTA_M"]) for r in bands), abs=1e-3)


def test_arc_band_uses_the_common_angular_range():
    from engine.source import ground_beam_network as GN
    import math
    ch = rows("01_GROUND_BEAM_GEOMETRY_CHANGELOG.csv")
    arc = next(r for r in ch if r["OBJECT"] == "BAND" and r["CAUSE"] == "ARC_OVERLAP")
    rng = [float(x) for x in re.search(r"common \[([\d.]+), ([\d.]+)\]", arc["DETAIL"]).groups()]
    rc = float(re.search(r"r_c ([\d.]+)", arc["DETAIL"]).group(1))
    assert float(arc["NEW_LENGTH_M"]) == pytest.approx(rc * math.radians(rng[1] - rng[0]) / 1000, abs=1e-3)
    assert GN.RULES == ("MULTI_PARTNER_PAIRING", "ARC_OVERLAP")


def test_network_conservation(summary):
    c = summary["conservation"]
    assert c["all_pass"] and all(v for k, v in c.items() if k != "all_pass")
    n = summary["network"]
    split = n["band_length_split_m"]
    assert split["bands"] == pytest.approx(split["spans"] + split["inside_columns_or_dropped"], abs=2e-3)
    up = n["unpaired_physical_candidates"]
    assert up["count"] == len(up["rows"]) and all(r["reason"] for r in up["rows"])
    assert sum(n["nodes_by_kind"].values()) == 2 * n["support_to_support_spans"]


# ------------------------------------------------------------------ applicability
def test_literal_length_conditions_at_the_5m_threshold():
    import build_pre_s5 as B
    lib, _ = B.detail_library()
    occ = lambda L: {"clear_m": L, "cc_m": L, "exterior_zone_test": False, "exterior_footprint_test": False}
    lt, eq, gt = (B.applicability(occ(L), lib) for L in (4.999, 5.0, 5.001))
    assert lt["candidates"] == ["P13-GB-LT5M"] and lt["state"] == "EXPLICIT_LENGTH_CONDITION"
    assert gt["candidates"] == ["P13-GB-GT5M"] and gt["state"] == "EXPLICIT_LENGTH_CONDITION"
    assert eq["state"] == "CANDIDATE_DETAIL" and set(eq["candidates"]) == {"P13-GB-GT5M", "P13-GB-LT5M"}
    assert any("THRESHOLD_UNRESOLVED" in f for f in eq["flags"])
    # 'Less than 2.5m' and 'Less than 5m' both hold literally below 2.5 m: kept, never collapsed
    lo = B.applicability(occ(2.0), lib)
    assert lo["candidates"] == ["P13-GB-LT2_5M", "P13-GB-LT5M"] and any("NESTED" in f for f in lo["flags"])
    # length basis that crosses a threshold -> candidate
    d = B.applicability({"clear_m": 4.9, "cc_m": 5.2, "exterior_zone_test": False, "exterior_footprint_test": False}, lib)
    assert d["state"] == "CANDIDATE_DETAIL" and set(d["candidates"]) == {"P13-GB-GT5M", "P13-GB-LT5M"}


def test_long_beam_detail_is_not_promoted_and_rows_stay_distinct():
    import build_pre_s5 as B
    lib, _ = B.detail_library()
    gt = lib["P13-GB-GT5M"]
    assert gt["top"] == (3, 16) and gt["rows"] == [(3, 16), (3, 16)] and gt["D"] == 600
    det = rows("04_GROUND_BEAM_DETAIL_APPLICABILITY.csv")
    on_gt = [r for r in det if "P13-GB-GT5M" in json.loads(r["DETAIL_CANDIDATES"])]
    assert all(float(r["CLEAR_LENGTH_M"]) > 5 or float(r["SUPPORT_CENTRELINE_LENGTH_M"] or 0) > 5 or
               "THRESHOLD" in r["FLAGS"] for r in on_gt)
    mat = rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    comps = {r["COMPONENT"] for r in mat}
    assert {"BOTTOM_ROW_1", "BOTTOM_ROW_2"} <= comps


def test_exterior_depth_blocks_stirrups_not_the_member_or_longitudinal_bars():
    det = {r["OCCURRENCE_ID"]: r for r in rows("04_GROUND_BEAM_DETAIL_APPLICABILITY.csv")}
    mat = rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    ext = [o for o, r in det.items() if json.loads(r["DETAIL_CANDIDATES"]) == ["P13-GB-EXTERIOR"]]
    assert ext
    for r in mat:
        if r["OCCURRENCE_ID"] in ext:
            if r["COMPONENT"] in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2"):
                assert r["S5_STATUS"] == "READY_LOWER_BOUND"
            if r["COMPONENT"] in ("STIRRUP_CORE_PATH", "SIDE_BARS"):
                assert r["S5_STATUS"] == "BLOCKED_COMPONENT" and "FOLLOW ARCH" in (r["WHY"] + r["COMPONENT_VALUE"])


def test_readiness_never_publishes_kg_and_conflicts_never_release():
    for n in os.listdir(PKG):
        if n.endswith((".csv", ".json")):
            t = (PKG / n).read_text(encoding="utf-8").lower()
            assert '"kg"' not in t and ",kg," not in t and "_kg" not in t, n
    mat = rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    for r in mat:
        if r["DETAIL_APPLICABILITY"] in ("SOURCE_CONFLICT", "NO_APPLICABLE_DETAIL"):
            assert r["MAY_RELEASE"] == "False"
        if r["MAY_RELEASE"] == "True":
            assert r["S5_STATUS"] in ("READY", "READY_LOWER_BOUND")
        if r["CANDIDATE_INVARIANT"] == "True":
            assert r["DETAIL_APPLICABILITY"] == "CANDIDATE_DETAIL"
        if r["COMPONENT"].startswith(("DEVELOPMENT", "HOOK", "END_TREATMENT")):
            assert r["S5_STATUS"] == "BLOCKED_COMPONENT"


def test_strap_register_keeps_concrete_and_rebar_lengths_apart():
    st = {r["MARK"]: r for r in rows("03_STRAP_OCCURRENCE_REGISTER.csv")}
    assert set(st) == {"SB1", "SB2", "SB3"}
    for r in st.values():
        clear, cc = float(r["CLEAR_CONCRETE_LENGTH_M"]), float(r["CENTERLINE_SUPPORT_TO_SUPPORT_M"])
        assert 0 < clear < cc
    assert st["SB2"]["AUTHORITY_STATE"] == "SOURCE_CONFLICT" and st["SB1"]["AUTHORITY_STATE"] == "SOURCE_VERIFIED"
    assert "SOURCE_CONFLICT" in st["SB1"]["FLAGS"]          # start support is the F / F10 outline
    mat = [r for r in rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv") if r["MEMBER_FAMILY"] == "STRAP_BEAM"]
    for r in mat:
        if r["COMPONENT"] == "STIRRUP_CORE_PATH":
            assert r["S5_STATUS"] == "BLOCKED_COMPONENT"         # SBT gives no link topology
        if r["COMPONENT"] == "BOTTOM_ROW_2":
            assert r["S5_STATUS"] == "NOT_APPLICABLE"             # one BOTTOM total, never invented rows
    src = rows("05_STRAP_REBAR_SOURCE_REGISTER.csv")
    assert sum(1 for r in src if r["SOURCE_KIND"].startswith("SCHEDULE_ROW")) == 4


def test_f3_provenance_is_the_drawing_not_a_donor():
    f = J("F3_PROVENANCE_CHECK.json")
    a = f["corrected_authority"]
    assert a["authority"] == "PROJECT_DRAWING" and a["decision"].startswith("F3 = 2")
    assert len(a["evidence"]) == 2 and all(e["sizes_match"] for e in a["evidence"])
    assert all("R9" not in json.dumps(e) for e in a["evidence"])
    assert f["quantity_changed"] is False and f["s4_freeze_changed"] is False


# ------------------------------------------------------------------ provenance contract
def _part(**kw):
    prov = GP.template(family="GROUND_BEAM", occurrence_id="GSO-X", mark="GB", start_node={"kind": "COLUMN", "refs": ["C1"]},
                       end_node={"kind": "BEAM_JUNCTION", "refs": ["B2"]}, handles=["A", "B"],
                       detail_id=["P13-GB-LT5M"], applicability=kw.pop("app", "EXPLICIT_LENGTH_CONDITION"),
                       context={"PROJECT_ID": "P", "REVISION": "R", "DRAWING_ID": "D.dxf", "DRAWING_SHA": "a" * 64,
                                "ENGINE_COMMIT": "1234567+code:" + "b" * 16, "REGISTER_VERSION": "V1",
                                "CALCULATION_ROUND": "S5"})
    prov.update(SHEET_REGION="GBP", SOURCE_HANDLES=["A", "B"], SOURCE_TEXT="3Ø14", COMPONENT="BEAM_TOP_BAR",
                RULE_ID="R", CONVENTION_ID="C", MEASUREMENT_STATE="MEASURED", AUTHORITY_STATE="SOURCE_EXPLICIT",
                RELEASE_STATE="LOWER_BOUND", FORMULA="f", INPUTS={}, LOW=1.0, BEST=1.0, HIGH=None,
                UNQUANTIFIED_COMPONENTS=["ANCHORAGE"])
    prov.update(kw.pop("prov", {}))
    return {"part_id": "p1", "category": "GROUND_BEAMS", "component": "BEAM_TOP_BAR", "state": "LOWER_BOUND",
            "kg": 1.0, "basis": ["STRUCTURAL_DETAIL"], "provenance": prov, **kw}


def test_s5_provenance_reuses_the_s4_contract():
    GP.validate_s5_part(_part())
    assert not any(k.startswith("FOOTING_") for k in _part()["provenance"])   # generic identity (PRE-S5.1)
    with pytest.raises(ValueError):
        GP.validate_s5_part(_part(prov={"DRAWING_SHA": "nope"}))                 # S4 rule still applies
    with pytest.raises(ValueError):
        GP.validate_s5_part(_part(prov={"START_NODE": None}))                    # S5 member field
    with pytest.raises(ValueError):
        GP.validate_s5_part(_part(app="SOURCE_CONFLICT"))                         # a conflict never releases
    with pytest.raises(ValueError):
        GP.validate_s5_part(_part(app="CANDIDATE_DETAIL"))
    GP.validate_s5_part(_part(app="CANDIDATE_DETAIL", prov={"CANDIDATE_INVARIANT": True}))
    assert set(GP.S5_EXTRA_FIELDS) <= set(GP.S5_PROVENANCE_FIELDS)


def test_every_occurrence_has_a_complete_provenance_template():
    t = J("S5_PROVENANCE_TEMPLATES.json")
    assert t["context"]["DRAWING_SHA"] == DXF_SHA
    ids = {r["OCCURRENCE_ID"] for r in rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")}
    assert {x["ELEMENT_OCCURRENCE_ID"] for x in t["templates"]} == ids
    assert not any(k.startswith("FOOTING_") for x in t["templates"] for k in x)
    assert all(GP.provenance_ready(x) for x in t["templates"])


# ------------------------------------------------------------------ donor firewall
DONOR_TOKENS = ("christiannp", "CHRISTIANNP", "S008", "freelancer", "FREELANCER", "UC4N", "U-C4N", "R9_1_CHRIS",
                "multi_engine", "22.619", "6.036", "191.873", "208.129", "6.287")


def test_production_path_carries_no_donor_value_or_id():
    for f in ("engine/source/ground_beam_network.py", "engine/source/ground_system_provenance.py",
              "research/pre_s5_ground_system_readiness/build_pre_s5.py"):
        src = (ROOT / f).read_text(encoding="utf-8")
        for tok in DONOR_TOKENS:
            assert tok not in src, (f, tok)
    idx = J("INDEX.json")
    assert not any("R9_1" in k or "christiannp" in k.lower() or "multi_engine" in k for k in idx["inputs"])
