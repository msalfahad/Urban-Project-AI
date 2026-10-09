"""S8.3 (research/alsenan_dome_ring_s8_3): dome and ring-beam structural QTO.

The checks re-derive the package from its own outputs, the frozen stages and, when the private drawings are restored,
the drawings themselves through independent tools (ezdxf's own arc geometry, shapely):

- every earlier stage still verifies; the package is frozen before any comparison and is blind;
- two structural domes and one architectural-only tower dome; repeated outlines are never counted again;
- the eight drawn ring segments are S6's BA001-BA008, transferred to S8.3 with no quantity moved;
- only the two shells (concrete) and their single mesh (rate density) are released; the rings stay conflicting or
  blocked; the tower dome is not quantified;
- S7's 43.1 kg of top-support steel at the dome bays stays with S7;
- every bar notation on the detail binds to exactly one family; conflicts, questions and sensitivity are kept apart."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import curved_member_geometry as G
from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_dome_ring_s8_3"
MANIFEST = PKG / "16_S8_3_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_SOURCE_REGISTER.csv", "02_DOME_POPULATION.csv", "03_DOME_PROFILE_AND_LEVELS.csv",
           "04_RING_GEOMETRY.csv", "05_S6_TO_S8_3_OWNERSHIP_DELTA.csv", "06_CONCRETE_REGISTER.csv",
           "07_REBAR_NOTATION_REGISTER.csv", "08_REBAR_QTO_REGISTER.csv", "09_BLOCKED_COMPONENTS.csv",
           "10_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "11_INTERFACE_AUDIT.csv", "12_SENSITIVITY_CASES.csv",
           "13_CONSERVATION_CHECKS.csv", "14_PROVENANCE.jsonl", "15_S8_3_SUMMARY.json"]
BY_SHA = ROOT / "data/inputs/by_sha256"
ST = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
AR = BY_SHA / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
SETP = [BY_SHA / f"{s}.pdf" for s in ("cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97",
                                       "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459")]
needs_inputs = pytest.mark.skipif(not (ST.exists() and AR.exists() and all(p.exists() for p in SETP)),
                                  reason="private client drawings not restored in data/inputs/by_sha256")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PKG / "15_S8_3_SUMMARY.json")


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_3" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 18 and {"S6", "S6.1", "S7", "S7A", "PRE-S8", "S8.2", "S8.2A"} <= set(s["frozen_baselines"])
    m = J(MANIFEST)
    for rel, h in m["inputs"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h, rel


def test_builder_and_engine_are_blind():
    for src in (PKG / "build_s8_3.py", ROOT / "engine/source/curved_member_geometry.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ", "U-C4N",
                    "kg/m3", "benchmark", "post_freeze", "02_STRUCTURAL_ELEMENT_CENSUS", "03_CONCRETE_COVERAGE",
                    "04_REBAR_COVERAGE", "08_SOURCE_CONFLICT_REGISTER"):
            assert tok not in text, (src.name, tok)
    assert not any("pre_s8" in k for k in J(MANIFEST)["inputs"])          # PRE-S8 is verified, never read


def test_registry_declares_the_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_dome_ring_s8_3/build_s8_3.py" in RP.ACCURATE_BUILDERS


# ------------------------------------------------------------------ population
def test_two_structural_domes_one_architectural_and_no_repeat_counted(s):
    pop = rows("02_DOME_POPULATION.csv")
    phys = [r for r in pop if r["COUNTED_AS_PHYSICAL"] == "True"]
    assert sorted(r["PHYSICAL_ID"] for r in phys) == ["DOME-A", "DOME-B", "DOME-TOWER"]
    assert [r["PHYSICAL_ID"] for r in phys if r["STRUCTURAL"] == "False"] == ["DOME-TOWER"]
    rep = [r for r in pop if r["ROW_KIND"] == "REPEATED_OUTLINE"]
    assert len(rep) == 2 and {r["PHYSICAL_ID"] for r in rep} == {"DOME-A", "DOME-B"}
    assert all(r["COUNTED_AS_PHYSICAL"] == "False" for r in pop if r["ROW_KIND"] != "PHYSICAL_DOME"
               and r["ROW_KIND"] != "PHYSICAL_DOME_ARCH_ONLY")
    assert s["physical_domes"] == {"structural": ["DOME-A", "DOME-B"], "architectural_only": ["DOME-TOWER"]}


def test_profile_is_established_and_dimensions_are_the_printed_ones():
    p = {r["ITEM_ID"]: r for r in rows("03_DOME_PROFILE_AND_LEVELS.csv")}
    assert (p["PR-04"]["VALUE"], p["PR-04"]["STATE"]) == ("SPHERICAL_ABOUT_AXIS", "ESTABLISHED")
    assert (p["PR-01"]["VALUE"], p["PR-02"]["VALUE"], p["PR-03"]["VALUE"]) == ("4.42", "1.9", "0.1")
    assert p["PR-13"]["STATE"] == "NOT_ESTABLISHED" and p["PR-13"]["VALUE"] == ""         # ring depth AS PER ARCH
    assert p["PR-16"]["STATE"] == "NOT_ESTABLISHED" and p["PR-17"]["VALUE"] == "NONE_DRAWN"


# ------------------------------------------------------------------ ring geometry and ownership transfer
def test_eight_segments_are_the_eight_s6_arcs_and_close_with_junctions():
    g = rows("04_RING_GEOMETRY.csv")
    segs = [r for r in g if r["KIND"] == "DRAWN_BAND_SEGMENT"]
    assert sorted(r["ROW_ID"].split("-")[-1] for r in segs) == [f"BA00{i}" for i in range(1, 9)]
    for r in segs:
        rc = (float(r["R1_MM"]) + float(r["R2_MM"])) / 2
        sw = math.radians(float(r["SWEEP_DEG"]))
        assert float(r["CENTRELINE_ARC_M"]) == pytest.approx(rc * sw / 1000, abs=1e-9)
        assert float(r["CENTRELINE_CHORD_M"]) == pytest.approx(2 * rc * math.sin(sw / 2) / 1000, abs=1e-9)
        assert float(r["CENTRELINE_CHORD_M"]) < float(r["CENTRELINE_ARC_M"])                   # chord is not length
        assert float(r["PLAN_AREA_M2"]) == pytest.approx(sw / 2 * (float(r["R2_MM"]) ** 2 - float(r["R1_MM"]) ** 2) / 1e6)
        assert float(r["CENTRELINE_ARC_M"]) == pytest.approx(float(r["S1_LENGTH_M"]), abs=2e-4)
    for d in ("DOME-A", "DOME-B"):
        for k in ("PLAN", "DETAIL"):
            part = next(r for r in g if r["ROW_ID"] == f"{d}-RING-{k}")
            m = re.search(r"annulus ([\d.]+) m2 = inside the bay \(ring\) ([\d.]+) \+ inside the framing members ([\d.]+)",
                          part["NOTE"])
            ann, inb, out = map(float, m.groups())
            r1, r2 = float(part["R1_MM"]), float(part["R2_MM"])
            assert ann == pytest.approx(math.pi * (r2 * r2 - r1 * r1) / 1e6, abs=1e-6)
            assert ann == pytest.approx(inb + out, abs=2e-6) and inb == pytest.approx(float(part["PLAN_AREA_M2"]), abs=1e-6)


def test_the_transfer_moves_no_quantity_and_names_every_segment(s):
    d = rows("05_S6_TO_S8_3_OWNERSHIP_DELTA.csv")
    assert [r["BAND_ID"] for r in d] == [f"BA00{i}" for i in range(1, 9)]
    assert all(r["CHANGE_KIND"] == DR.OWNERSHIP_TRANSFER and r["NEW_RELEASE_STATE"] == DR.TRANSFERRED_OUT
               and float(r["OLD_KNOWN_QUANTITY"]) == 0 and float(r["DELTA_KNOWN_QUANTITY"]) == 0 for r in d)
    assert {r["BASELINE_COMPONENT_ID"] for r in d if r["S6_TAG"] == "B4"} == {"BM-1F_ROOF-B4-BA001-1829",
                                                                               "BM-1F_ROOF-B4-BA002-1828"}
    assert {r["BASELINE_COMPONENT_ID"] for r in d if not r["S6_TAG"]} == {f"ARC:FFRS:BA00{i}" for i in range(3, 9)}
    assert Counter(r["DOME"] for r in d) == {"DOME-A": 4, "DOME-B": 4}
    assert len(s["ownership_transfers"]) == 8


# ------------------------------------------------------------------ released quantities, recomputed independently
def _numeric_shell(chord, rise, t, n=40000):
    R = (chord * chord / 4 + rise * rise) / (2 * rise)
    d, ri = R - rise, R - t
    dz = rise / n
    return sum(math.pi * (max(0.0, R * R - z * z) - max(0.0, ri * ri - z * z)) * dz
               for z in (d + (i + 0.5) * dz for i in range(n)))


def test_only_the_shells_and_their_mesh_are_released(s):
    c = rows("06_CONCRETE_REGISTER.csv")
    rel = [r for r in c if r["RELEASED"] == "True"]
    assert sorted(r["ITEM_ID"] for r in rel) == ["CQ-DOME-A-SHELL", "CQ-DOME-B-SHELL"]
    assert all(r["LANE"] == "PROJECT_BASIS_QTO" for r in rel)
    one = _numeric_shell(4.42, 1.90, 0.10)
    assert all(float(r["M3"]) == pytest.approx(one, rel=1e-7) for r in rel)
    assert s["released"]["concrete_m3"] == pytest.approx(2 * one, rel=1e-7)
    for r in c:
        if r["RELEASED"] != "True":
            assert r["M3"] == ""
    assert {r["LANE"] for r in c if r["COMPONENT"] == "RING_BEAM"} == {"SOURCE_CONFLICT"}
    b = rows("08_REBAR_QTO_REGISTER.csv")
    relb = [r for r in b if r["RELEASED"] == "True"]
    assert sorted(r["FAMILY"] for r in relb) == ["SHELL_HOOP", "SHELL_HOOP", "SHELL_MERIDIONAL", "SHELL_MERIDIONAL"]
    R = G.cap_radius(4.42, 1.90)
    mid = G.shell_between_caps(R, 1.90, 0.10)["area_mid"]
    assert mid == pytest.approx(2 * math.pi * (R - 0.05) * (1.90 - 0.05))
    for r in relb:
        assert float(r["EQUIVALENT_LENGTH_M"]) == pytest.approx(mid / 0.150) and float(r["KG"]) == pytest.approx(mid / 0.150 * 144 / 162)
    assert s["released"]["reinforcement_kg"] == pytest.approx(4 * mid / 0.150 * 144 / 162)
    for r in b:
        if r["RELEASED"] != "True":
            assert r["KG"] == "" and r["EQUIVALENT_LENGTH_M"] == ""
    ring = {r["FAMILY"]: r["LANE"] for r in b if r["DOME"] == "DOME-B"}
    assert ring["RING_TOP"] == ring["RING_BOTTOM"] == "SOURCE_CONFLICT"
    assert ring["RING_SIDE"] == ring["RING_LINKS"] == ring["SHELL_ANCHORAGE"] == "BLOCKED_UNQUANTIFIED"


def test_the_tower_dome_is_not_quantified(s):
    assert all(r["M3"] == "" for r in rows("06_CONCRETE_REGISTER.csv") if r["DOME"] == "DOME-TOWER")
    assert all(r["KG"] == "" for r in rows("08_REBAR_QTO_REGISTER.csv") if r["DOME"] == "DOME-TOWER")
    assert "DOME-TOWER" not in s["by_dome"]


# ------------------------------------------------------------------ notations, interfaces, conflicts, sensitivity
def test_every_notation_binds_to_one_family():
    n = rows("07_REBAR_NOTATION_REGISTER.csv")
    shell = {r["ROLE"]: r for r in n if r["ROLE"].startswith("SHELL_") and r["ROLE"] != "SHELL_BAR_INTO_RING"}
    assert set(shell) == {"SHELL_MERIDIONAL", "SHELL_HOOP"} and all(r["LAYERS_DRAWN"] == "1" for r in shell.values())
    ring = {r["ROLE"]: r for r in n if r["ROLE"].startswith("RING_") and r["ROLE"] != "RING_LINK_SHAPE"}
    assert set(ring) == {"RING_TOP", "RING_BOTTOM", "RING_SIDE", "RING_LINKS"}
    assert (ring["RING_TOP"]["COUNT"], ring["RING_TOP"]["DIAMETER_MM"]) == ("3", "16")
    assert (ring["RING_BOTTOM"]["COUNT"], ring["RING_BOTTOM"]["DIAMETER_MM"]) == ("3", "18")
    assert (ring["RING_SIDE"]["SPACING_MM"], ring["RING_LINKS"]["RATE_PER_M"]) == ("200", "8")
    assert all(len(json.loads(r["HANDLES"])) == 2 for r in ring.values())          # both cuts, one family


def test_s7_top_support_steel_stays_with_s7(s):
    k = s["s7_dome_adjacent_kg"]
    assert k["total"] == pytest.approx(43.113236, abs=1e-6) and k["total"] == pytest.approx(k["DOME-A"] + k["DOME-B"])
    assert k["state"] == "STAYS_WITH_S7"
    i = {r["INTERFACE"]: r for r in rows("11_INTERFACE_AUDIT.csv")}
    assert i["DOME OPENING -> S7 SLAB"]["BARS"].endswith(": 0") and i["SHELL -> RING"]["STATE"] == "OWNED_ONCE"


def test_conflicts_and_questions():
    cq = {r["ID"]: r for r in rows("10_SOURCE_CONFLICTS_AND_QUESTIONS.csv")}
    assert {f"CF-S8.3-0{i}" for i in range(1, 10)} <= set(cq)
    assert cq["PS8-C02"]["STATUS"] == "RESOLVED_BY_TRANSFER" and "PS8-C01" in cq["CF-S8.3-01"]["STATUS"]
    assert all(re.match(r"(Architect|Engineer)", r["NOTE"]) for k, r in cq.items() if r["KIND"] == "QUESTION")


def test_sensitivity_never_enters_a_total():
    sen = rows("12_SENSITIVITY_CASES.csv")
    assert sen and all(r["LANE"] == "SENSITIVITY_ONLY" and r["IN_OFFICIAL_TOTAL"] == "False" for r in sen)


def test_every_conservation_check_passes():
    c = rows("13_CONSERVATION_CHECKS.csv")
    assert [r["CHECK_ID"] for r in c] == [f"A-{i:02d}" for i in range(1, 15)] and all(r["RESULT"] == "PASS" for r in c)


def test_reconstructed_pdfs_are_marked_and_unused():
    src = {r["SOURCE_ID"]: r for r in rows("01_SOURCE_REGISTER.csv")}
    recon = [r for r in src.values() if r["ACQUISITION"] == "BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD"]
    assert len(recon) == 2 and all(r["ROLE_IN_S8_3"] == "NOT USED" and "never a separately obtained original" in r["NOTE"]
                                   for r in recon)


def test_no_client_drawing_or_owner_detail_in_the_package():
    assert not [p for p in PKG.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    for o in OUTPUTS:
        text = (PKG / o).read_text(encoding="utf-8")
        assert not re.search(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}", text), o


# ------------------------------------------------------------------ independent checks on the drawings
@needs_inputs
def test_segments_against_ezdxf_construction_arcs():
    """ezdxf's own ConstructionArc (not the S8.3 engine) gives the same drawn outer-edge sweeps."""
    import ezdxf
    doc = ezdxf.readfile(ST)
    g = {r["ROW_ID"]: r for r in rows("04_RING_GEOMETRY.csv") if r["KIND"] == "DRAWN_BAND_SEGMENT"}
    outer = [e for e in doc.modelspace().query("ARC") if abs(e.dxf.radius - 2411.091523536) < 1e-3]
    assert len(outer) == 8                     # each outer arc lies inside an inner edge: it is one segment's sweep
    assert sorted(round(e.construction_tool().angle_span, 6) for e in outer) == \
        sorted(round(float(r["SWEEP_DEG"]), 6) for r in g.values())


@needs_inputs
def test_ring_partition_against_shapely():
    shapely = pytest.importorskip("shapely")
    from shapely.geometry import Point, box
    g = {r["ROW_ID"]: r for r in rows("04_RING_GEOMETRY.csv")}
    for d in ("DOME-A", "DOME-B"):
        f = {k: float(g[f"{d}-FACE{k}"]["R1_MM"]) for k in ("+x", "-x", "+y", "-y")}
        bay = box(f["-x"], f["-y"], f["+x"], f["+y"])
        for k in ("PLAN", "DETAIL"):
            r1, r2 = float(g[f"{d}-RING-{k}"]["R1_MM"]), float(g[f"{d}-RING-{k}"]["R2_MM"])
            ring = Point(0, 0).buffer(r2, quad_segs=4096).difference(Point(0, 0).buffer(r1, quad_segs=4096))
            assert ring.intersection(bay).area / 1e6 == pytest.approx(float(g[f"{d}-RING-{k}"]["PLAN_AREA_M2"]), rel=2e-5)
        op = Point(0, 0).buffer(float(g[f"{d}-OPENING"]["R2_MM"]), quad_segs=4096).intersection(bay).area / 1e6
        assert op == pytest.approx(float(g[f"{d}-OPENING"]["PLAN_AREA_M2"]), rel=2e-5)


@needs_inputs
def test_rebuild_is_byte_identical():
    names = OUTPUTS + [MANIFEST.name]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_3.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
