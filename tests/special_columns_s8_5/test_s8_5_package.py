"""S8.5 (research/alsenan_special_columns_s8_5): special columns - turned, dead and planted.

The checks re-derive the package from its outputs, the frozen stages and, when the private drawing is restored, the
drawing itself through independent tools (ezdxf, shapely):

- every earlier stage still verifies; the package is frozen before any comparison and is blind (PRE-S8 is read
  through a whitelist that never binds its quantity column);
- six records, six real column occurrences, no second column; each planted support is resolved or explicitly not;
- every S3.1 row of the eight special segments is cited once; nothing S3.1 or S6.1 owns is added again;
- the S3.1 4Ø16 extras, the S6.1 planted-column extra and every sensitivity recomputed by hand;
- nothing is released that the source does not fix; every blocked role has its question."""

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

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_special_columns_s8_5"
MANIFEST = PKG / "17_S8_5_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_SOURCE_AND_ANNOTATION_REGISTER.csv", "02_SIX_OCCURRENCE_POPULATION.csv",
           "03_COLUMN_PARENT_CROSSWALK.csv", "04_TWISTED_COLUMN_REINFORCEMENT.csv",
           "05_PLANTED_COLUMN_REINFORCEMENT.csv", "06_DEAD_COLUMN_TERMINATION_AUDIT.csv", "07_CONCRETE_QTO.csv",
           "08_INCREMENTAL_REBAR_QTO.csv", "09_INTERFACE_RECONCILIATION.csv", "10_BLOCKED_COMPONENTS.csv",
           "11_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "12_OWNERSHIP_DELTAS.csv", "13_SENSITIVITY_CASES.csv",
           "14_CONSERVATION_CHECKS.csv", "15_PROVENANCE.jsonl", "16_S8_5_SUMMARY.json"]
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not ST.exists(), reason="private client drawing not restored in data/inputs/by_sha256")
SIX = ("SPC-TURN_COLUMN-GFRS-31F", "SPC-TURN_COLUMN-GFRS-324", "SPC-DEAD_COLUMN-GFRS-38A",
       "SPC-PLANTED_COLUMN-GFRS-544", "SPC-PLANTED_COLUMN-GFRS-548", "SPC-PLANTED_COLUMN-FFRS-77C")
OWNERS = {SIX[0]: ["COL-C8-X15-Y06-GF", "COL-C8-X15-Y06-1F"], SIX[1]: ["COL-C9-X13-Y08-GF", "COL-C9-X13-Y08-1F"],
          SIX[2]: ["COL-C11-X06-Y04-GF"], SIX[3]: ["COL-P.C-X08-Y02-1F"], SIX[4]: ["COL-P.C-X15-Y02-1F"],
          SIX[5]: ["COL-P.C-X?-Y?@24888-15994-2F"]}
KG16, KG8 = 16 * 16 / 162.0, 8 * 8 / 162.0
S31 = ROOT / "research/alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json"
S61 = ROOT / "research/alsenan_superstructure_beam_rebar_s6_1/S6_1_DELTA_COMPONENTS.csv"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def comps():
    return {r["COMPONENT_ID"]: r for n in ("04_TWISTED_COLUMN_REINFORCEMENT.csv", "05_PLANTED_COLUMN_REINFORCEMENT.csv",
                                           "06_DEAD_COLUMN_TERMINATION_AUDIT.csv") for r in rows(n)}


@pytest.fixture(scope="module")
def s():
    return J(PKG / "16_S8_5_SUMMARY.json")


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_5" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 21 and {"S6.1", "PRE-S8", "S8.3A", "S8.4"} <= set(s["frozen_baselines"])
    found = {}
    for mp in sorted((ROOT / "research").glob("*/*FREEZE_MANIFEST.json")):
        found.setdefault(hashlib.sha256(mp.read_bytes()).hexdigest(), mp)
    for k, h in s["frozen_baselines"].items():
        assert h in found, k
        DR.verify_frozen(found[h], ROOT)
    m = J(MANIFEST)
    for rel, h in m["inputs"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h, rel
    for name, h in s["s8_3_errata_sha256"].items():
        assert hashlib.sha256((ROOT / "research/alsenan_dome_ring_s8_3/errata" / name).read_bytes()).hexdigest() == h
    # the unmanifested earlier stages (S1, S2, S3, S3.1) still match their own register indexes
    for idx, key in (("alsenan_structural_census_s1", "registers"), ("alsenan_structural_s2", "outputs"),
                     ("alsenan_column_rebar_s3", "outputs"), ("alsenan_column_rebar_s3_1", "outputs")):
        d = ROOT / "research" / idx
        for name, v in J(d / "INDEX.json")[key].items():
            h = v["sha256"] if isinstance(v, dict) else v
            f = d / (v["file"] if isinstance(v, dict) else name)
            assert hashlib.sha256(f.read_bytes()).hexdigest() == h, f


def test_builder_and_engine_are_blind():
    for src in (PKG / "build_s8_5.py", ROOT / "engine/source/special_column_components.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ", "U-C4N",
                    "kg/m3", "benchmark", "post_freeze", "03_CONCRETE_COVERAGE", "04_REBAR_COVERAGE",
                    "08_SOURCE_CONFLICT_REGISTER", "control_plane", "multi_engine", "URBAN_LINES", "CR_TRADE"):
            assert tok not in text, (src.name, tok)
    m = J(MANIFEST)
    pre = [k for k in m["inputs"] if "pre_s8" in k]
    assert pre == ["research/pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv"]
    assert "CONCRETE_QUANTITY_STATE" not in m["pre_s8_columns_read"]
    sys.path.insert(0, str(PKG))
    import build_s8_5 as B
    assert set(B.PRE_S8_COLUMNS).isdisjoint(B.PRE_S8_FIREWALLED) and "CONCRETE_QUANTITY_STATE" in B.PRE_S8_FIREWALLED


def test_registry_declares_the_builder_and_engine():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_special_columns_s8_5/build_s8_5.py" in RP.ACCURATE_BUILDERS
    assert "engine/source/special_column_components.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ population
def test_starting_population_matches_pre_s8_ids_only(s):
    """PRE-S8's candidate register names the same six records (only the id column is read)."""
    with open(ROOT / "research/pre_s8_structural_completeness/06_S8_CANDIDATE_REGISTER.csv", encoding="utf-8") as fh:
        ids = [json.loads(r["ELEMENT_IDS"]) for r in csv.DictReader(fh) if r["S8_FAMILY"] == "SPECIAL_COLUMN"]
    assert len(ids) == 1 and sorted(ids[0]) == sorted(SIX) == sorted(s["starting_population"])
    s1 = J(ROOT / "research/alsenan_structural_census_s1/SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json")["rows"]
    assert sorted(r["special_id"] for r in s1 if r["kind"] in ("TURN_COLUMN", "DEAD_COLUMN", "PLANTED_COLUMN")) == \
        sorted(SIX)


def test_six_records_six_real_columns_no_second_column(s):
    pop = {r["SPECIAL_ID"]: r for r in rows("02_SIX_OCCURRENCE_POPULATION.csv")}
    assert list(pop) == list(SIX)
    s1 = {r["column_id"]: r for r in J(ROOT / "research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json")
          ["rows"]}
    for sid, owners in OWNERS.items():
        assert json.loads(pop[sid]["COLUMN_OWNERS"]) == owners
        assert all(o in s1 for o in owners) and pop[sid]["TERMINAL"].startswith("RESOLVED_TO_COLUMN_OCCURRENCE")
    assert {sid: json.loads(pop[sid]["STOREYS"]) for sid in SIX} == {
        SIX[0]: ["GF", "1F"], SIX[1]: ["GF", "1F"], SIX[2]: ["GF"], SIX[3]: ["1F"], SIX[4]: ["1F"], SIX[5]: ["2F"]}
    # planted on the GF roof -> the 1F storey (+5.50 -> +9.70); on the 1F roof -> 2F (+9.70 -> +13.90)
    assert pop[SIX[3]]["VERTICAL_EXTENT"] == pop[SIX[4]]["VERTICAL_EXTENT"] == "1F: FFL +5.50 -> +9.70 m"
    assert pop[SIX[5]]["VERTICAL_EXTENT"] == "2F: FFL +9.70 -> +13.90 m"
    assert pop[SIX[4]]["SUPPORT_OR_PARENT"] == "BM-GF_ROOF-B26-BL014-4CC"
    for sid in (SIX[3], SIX[5]):
        assert pop[sid]["SUPPORT_OR_PARENT"].startswith("UNRESOLVED (NODE:") and "SUPPORT_UNRESOLVED" in pop[sid]["TERMINAL"]
    assert s["planted_hosts"]["544"]["candidates"] == ["BM-GF_ROOF-B27-BL002-532", "BM-GF_ROOF-B4-BL022-497",
                                                       "BM-GF_ROOF-B5-BL022-498", "SPAN:GFRS:BL002:2844-4653"]
    assert s["planted_hosts"]["77C"]["candidates"] == ["BM-1F_ROOF-B1-BL014-6D0", "BM-1F_ROOF-B19-BL029-6CF",
                                                       "BM-1F_ROOF-B6-BL014-6C5", "SPAN:FFRS:BL029:26630-29105"]
    x = rows("03_COLUMN_PARENT_CROSSWALK.csv")
    cols = [r["MEMBER"] for r in x if r["MEMBER_KIND"] == "COLUMN_OCCURRENCE"]
    assert len(cols) == len(set(cols)) == 11                    # C8 x3, C9 x3, C11 x2, P.C x3: each once
    assert sorted(r["MEMBER"] for r in x if r["S8_5_TOUCHES"] == "True") == sorted(o for v in OWNERS.values() for o in v)


def test_turn_overlap_and_dead_end(s):
    assert s["spiral"]["overlap_mm"] == {"31F": [200.0, 250.0], "324": [200.0, 250.0]}
    dead = rows("06_DEAD_COLUMN_TERMINATION_AUDIT.csv")
    assert [r["COMPONENT_ID"] for r in dead if r["DECISION"] == "NOT_REQUIRED"] == ["DC-06"]   # nothing above it
    s1 = {r["column_id"]: r for r in J(ROOT / "research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json")
          ["rows"]}
    assert s1["COL-C11-X06-Y04-GF"]["continues_above"] is False and "COL-C11-X06-Y04-1F" not in s1


# ------------------------------------------------------------------ ownership, no double count
def test_every_s3_1_row_of_the_special_segments_is_cited_once():
    reg = J(S31)["rows"]
    segs = sorted({o for v in OWNERS.values() for o in v})
    want = Counter(f"S3.1:{r['occurrence_id']}|{r['part_id'].split('|', 1)[1]}" for r in reg if r["occurrence_id"] in segs)
    got = Counter(e for c in comps().values() for e in json.loads(c["EXISTING_OWNER"]) if e.startswith("S3.1:"))
    assert got == want and set(got.values()) == {1}
    assert len(want) == 56


def test_nothing_already_owned_is_added_again(s):
    c = comps()
    for r in c.values():
        if r["DECISION"] == "ALREADY_OWNED":
            assert r["S8_5_KG"] == "0" and r["QUANTITY_STATE"] == "NOT_ADDED" and json.loads(r["EXISTING_OWNER"])
    assert not [r for r in c.values() if r["DECISION"] == "INCREMENTAL"]
    assert s["released"] == {"concrete_m3": 0.0, "reinforcement_kg": 0.0, "reinforcement_items": []}
    assert s["incremental_by_diameter_kg"] == {"8": 0.0, "16": 0.0}
    q = rows("08_INCREMENTAL_REBAR_QTO.csv")
    assert len(q) == len(c) == 61 and math.fsum(float(r["INCREMENTAL_KG"] or 0) for r in q) == 0.0
    assert Counter(r["DECISION"] for r in c.values()) == Counter(ALREADY_OWNED=33, BLOCKED=24, NOT_REQUIRED=4)


def test_twisted_extras_are_s3_1s_and_recompute_by_hand():
    reg = {(r["occurrence_id"], r["part_id"].split("|", 1)[1]): r for r in J(S31)["rows"]}
    c = comps()
    for k, occ in (("31F", "COL-C8-X15-Y06-GF"), ("324", "COL-C9-X13-Y08-GF")):
        ex = reg[(occ, "EXTRA:TURN_EXTRA_BARS")]
        assert ex["release_state"] == "LOWER_BOUND" and abs(4 * 2.0 * KG16 - ex["kg"]) < 5e-4      # 4Ø16 x (1 + 1) m
        r = c[f"TC-{k}-05"]
        assert r["DECISION"] == "ALREADY_OWNED" and float(r["EXISTING_KG"]) == ex["kg"] and "(equal)" in r["CHECK"]
        sp = c[f"TC-{k}-10"]
        assert reg[(occ, "EXTRA:TURN_SPIRAL")]["release_state"] == "BLOCKED"
        assert sp["DECISION"] == "BLOCKED" and sp["S8_5_KG"] == "" and sp["QUESTION"] == "Q-01"
        assert c[f"TC-{k}-06"]["DECISION"] == "BLOCKED"           # the drawn crank is not dimensioned
        assert c[f"TC-{k}-07"]["DECISION"] == "NOT_REQUIRED"      # no hook drawn at the bottom end


def test_spiral_sensitivity_by_hand(s):
    sens = {r["CASE_ID"]: r for r in rows("13_SENSITIVITY_CASES.csv")}
    pitch, turns = 1000 / 6, 12                                 # 6/m over 1 m + 1 m
    w, h = 200 - 2 * 25 - 8, 250 - 2 * 25 - 8                    # P8-N22 cover 25 mm, Ø8: 142 x 192
    circ = turns * math.hypot(math.pi * w, pitch) / 1000 * KG8
    a, b = w / 2, h / 2
    hh = ((a - b) / (a + b)) ** 2
    P = math.pi * (a + b) * (1 + 3 * hh / (10 + math.sqrt(4 - 3 * hh)))
    ell = turns * math.hypot(P, pitch) / 1000 * KG8
    for k in ("31F", "324"):
        assert float(sens[f"SA-{k}-SPI-C"]["KG"]) == pytest.approx(circ, abs=1e-8)
        assert float(sens[f"SA-{k}-SPI-E"]["KG"]) == pytest.approx(ell, abs=1e-8)
        cont = sens[f"SA-{k}-CONT"]
        assert float(cont["KG_LOW"]) == pytest.approx(4 * 0.36 * KG16) and float(cont["KG_HIGH"]) == pytest.approx(12 * 0.36 * KG16)
    assert s["spiral"]["state"] == "BLOCKED_UNQUANTIFIED" and s["spiral"]["turns"] == 12.0


def test_planted_548_extra_is_s6_1s_and_recomputes_by_hand():
    d = {r["DELTA_ID"]: r for r in csv.DictReader(open(S61, encoding="utf-8"))}["S6.1-D1324"]
    assert d["OCCURRENCE_ID"] == "BM-GF_ROOF-B26-BL014-4CC" and d["PORTION"] == "STRAIGHT_PROJECTION"
    assert float(d["NEW_KNOWN_QUANTITY"]) == pytest.approx(4 * (2 * 0.850 + 0.200) * KG16, abs=1e-6)
    r = comps()["PC-548-08"]
    assert r["DECISION"] == "ALREADY_OWNED" and json.loads(r["EXISTING_OWNER"]) == ["S6.1:S6.1-D1324"]
    sens = {x["CASE_ID"]: x for x in rows("13_SENSITIVITY_CASES.csv")}
    x = [x for x in rows("03_COLUMN_PARENT_CROSSWALK.csv") if x["CROSSWALK_ID"] == "X-548-B26-BL014"][0]
    th = math.radians(float(x["ORIENTATION"]))
    along = 500 * abs(math.cos(th)) + 200 * abs(math.sin(th))   # the 50 x 20 footprint along B26
    assert float(sens["SA-548-EXTRA-B26"]["KG"]) == pytest.approx(4 * (1700 + along) / 1000 * KG16, abs=2e-5)
    assert comps()["PC-548-10"]["DECISION"] == "NOT_REQUIRED"      # B26's own links are already 10 / m


def test_unresolved_hosts_are_blocked_with_every_reading_as_sensitivity():
    c = comps()
    sens = {x["CASE_ID"]: x for x in rows("13_SENSITIVITY_CASES.csv")}
    xw = {x["MEMBER"]: x for x in rows("03_COLUMN_PARENT_CROSSWALK.csv") if x["MEMBER_KIND"] == "BEAM_OCCURRENCE"}
    for k, dims, cases in (("544", (700, 200), {"B27": 850, "B4": 500, "B5": 500}),
                           ("77C", (200, 400), {"B1": 400, "B6": 500, "B19": 750})):
        for n in ("08", "09", "10"):
            assert c[f"PC-{k}-{n}"]["DECISION"] == "BLOCKED" and c[f"PC-{k}-{n}"]["S8_5_KG"] == ""
        assert sorted(json.loads(c[f"PC-{k}-08"]["SENSITIVITY_IDS"])) == sorted(f"SA-{k}-EXTRA-{m}" for m in cases)
        for mark, depth in cases.items():
            x = [v for v in xw.values() if v["CROSSWALK_ID"].startswith(f"X-{k}-{mark}-")][0]
            assert json.loads(x["SECTION_SCHEDULE_CM"])[1] * 10 == depth and x["ROLE"] == "SUPPORT_CANDIDATE"
            th = math.radians(float(x["ORIENTATION"]))
            along = dims[0] * abs(math.cos(th)) + dims[1] * abs(math.sin(th))
            assert float(sens[f"SA-{k}-EXTRA-{mark}"]["KG"]) == pytest.approx(4 * (2 * depth + along) / 1000 * KG16,
                                                                                abs=2e-5)
        assert sens[f"SA-{k}-EXTRA-{list(cases)[0]}"]["RELEASED"] == "False"


def test_starter_sensitivity_and_planted_owners():
    c = comps()
    sens = {x["CASE_ID"]: x for x in rows("13_SENSITIVITY_CASES.csv")}
    for k, n in (("544", 10), ("548", 8), ("77C", 8)):
        assert float(sens[f"SA-{k}-STARTER"]["KG"]) == pytest.approx(n * 1.0 * KG16)
        for i in ("05", "06", "07"):
            assert c[f"PC-{k}-{i}"]["DECISION"] == "BLOCKED" and c[f"PC-{k}-{i}"]["QUESTION"] == "Q-06"
        for i in ("01", "02", "03", "04"):
            assert c[f"PC-{k}-{i}"]["DECISION"] == "ALREADY_OWNED"
            assert all(e.startswith("S3.1:COL-P.C-") for e in json.loads(c[f"PC-{k}-{i}"]["EXISTING_OWNER"]))


def test_frozen_totals_unchanged(s):
    reg = J(S31)
    assert reg["totals_kg"]["total"] == s["s3_1"]["total_kg"]
    assert reg["occurrence_states"] == {"REBAR_LOWER_BOUND": 95}
    s61 = J(ROOT / "research/alsenan_superstructure_beam_rebar_s6_1/S6_1_RELEASE_SUMMARY.json")
    assert s61["s6_1_known_kg"] == s["s6_1"]["known_kg"]
    assert s61["delta_by_kind_kg"]["planted_column_extra"] == pytest.approx(4 * 1.9 * KG16)


def test_concrete_never_re_added():
    conc = rows("07_CONCRETE_QTO.csv")
    owned = [r for r in conc if r["LANE"] == "NOT_ADDED"]
    assert sorted(r["COLUMN_ID"] for r in owned) == sorted(o for v in OWNERS.values() for o in v)
    assert all(r["S8_5_M3"] == "0" and r["EXISTING_OWNER"].startswith("S2:") for r in owned)
    assert all(r["S8_5_M3"] == "" for r in conc if r["LANE"] == "NOT_IN_SOURCE")


def test_interfaces():
    inter = {r["INTERFACE_ID"]: r for r in rows("09_INTERFACE_RECONCILIATION.csv")}
    assert all(r["RESULT"] == "PASS" for r in inter.values())
    for k in ("31F", "324", "38A"):
        assert "STARTER" in inter[f"I-{k}-01"]["EXISTING_OWNER"] and inter[f"I-{k}-01"]["NEW_EXTRA_OWNER"] == "none"
        assert json.loads(inter[f"I-{k}-02"]["EXISTING_OWNER"])                       # ground beams under S5
    s4 = [r for r in csv.DictReader(open(ROOT / "research/alsenan_footing_rebar_s4/FOOTING_REBAR_COMPONENTS.csv",
                                         encoding="utf-8"))
          if r["occurrence_id"] in ("FOCC-1B24", "FOCC-180F", "FOCC-1ADB") and r["component"] == "STARTER_DOWEL_REFERENCE"]
    assert len(s4) == 3 and {r["state"] for r in s4} == {"NOT_APPLICABLE"}
    assert inter["I-548-01"]["NEW_EXTRA_OWNER"] == "S6.1"
    assert inter["I-544-01"]["QUANTITY_STATE"] == inter["I-77C-01"]["QUANTITY_STATE"] == "BLOCKED_UNQUANTIFIED"


def test_blocked_questions_conflicts_and_deltas(s):
    blocked = rows("10_BLOCKED_COMPONENTS.csv")
    cq = {r["ID"]: r for r in rows("11_SOURCE_CONFLICTS_AND_QUESTIONS.csv")}
    assert len(blocked) == 24 and len({b["BLOCKED_ID"] for b in blocked}) == 24
    assert {b["QUESTION"] for b in blocked} == {f"Q-0{i}" for i in range(1, 9)} and all(b["QUESTION"] in cq for b in blocked)
    for cid in ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-09", "C-10"):
        assert cq[cid]["KIND"] == "SOURCE_CONFLICT"
    assert "projection ABOVE the beam" in cq["C-04"]["TEXT"]
    od = rows("12_OWNERSHIP_DELTAS.csv")
    assert all(r["KG_MOVED"] == "0" and r["DATE"] == "2026-10-09" for r in od)
    assert sum(1 for r in od if r["NEW_STATE"] == "SUPERSEDED_CLAIM") == 6
    sens = rows("13_SENSITIVITY_CASES.csv")
    assert sens and all(r["RELEASED"] == "False" and r["LANE"] == "SENSITIVITY_ONLY" for r in sens)


def test_conservation_and_hygiene(s):
    assert all(v == "PASS" for v in s["conservation"].values()) and len(s["conservation"]) == 16
    assert not [p for p in PKG.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    for o in OUTPUTS:
        text = (PKG / o).read_text(encoding="utf-8")
        assert not re.search(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}", text), o


# ------------------------------------------------------------------ independent checks on the drawing
@needs_inputs
def test_labels_circles_leaders_and_outlines_with_ezdxf():
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.readfile(ST)
    db = doc.entitydb
    for h, t in (("31F", "T.C"), ("324", "T.C"), ("38A", "D.C"), ("544", "P.C 20x70"), ("548", "P.C 20x50"),
                 ("77C", "P.C 20x50"), ("543", "10%%C16"), ("547", "8%%C16"), ("77D", "8%%C16")):
        assert db[h].dxf.text.strip() == t, h
    pat = re.compile(r"^\s*[TDP]\s*\.\s*C(?![A-Za-z])")
    found = sorted(e.dxf.handle for e in doc.modelspace().query("TEXT MTEXT")
                   if pat.match(e.dxf.text if e.dxftype() == "TEXT" else e.text))
    assert found == sorted(["31F", "324", "38A", "544", "548", "77C"])
    def bbox(h):
        pts = [(p[0], p[1]) for p in db[h].get_points("xy")]
        return (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))
    origin = {sh: bbox(fr)[:2] for sh, fr in (("GFRS", "B4"), ("FFRS", "B5"), ("SFRS", "B6"))}   # sheet frames
    sheet = {**{h: "GFRS" for h in ("36E", "31B", "37A", "322", "35C", "329", "386")},
             **{h: "FFRS" for h in ("664", "667", "66A", "69D", "77B")}, "778": "SFRS"}
    rect = {}
    for h, sh in sheet.items():                                  # outlines in their sheet's own frame
        x0, y0, x1, y1 = bbox(h)
        ox, oy = origin[sh]
        rect[h] = (x0 - ox, y0 - oy, x1 - ox, y1 - oy)
    for leader, circle, outline in (("545", "546", "329"), ("549", "54A", "386"), ("77F", "77E", "77B")):
        c = db[circle]
        cx, cy, r = c.dxf.center.x, c.dxf.center.y, c.dxf.radius
        x0, y0, x1, y1 = bbox(outline)
        assert abs(cx - (x0 + x1) / 2) < 0.01 and abs(cy - (y0 + y1) / 2) < 0.01        # centred on the column
        ends = [(p[0], p[1]) for p in db[leader].get_points("xy")]
        assert min(abs(math.dist(e, (cx, cy)) - r) for e in (ends[0], ends[-1])) < 5.0  # the leader lands on it
    for a, b in (("31B", "664"), ("322", "667"), ("329", "66A"), ("386", "69D"), ("77B", "778")):
        assert rect[a] == pytest.approx(rect[b], abs=1e-6)         # the slab-plan outline is the storey column
    assert (rect["77B"][2] - rect["77B"][0], rect["77B"][3] - rect["77B"][1]) == pytest.approx((200, 400))


@needs_inputs
def test_turn_overlap_and_circles_with_shapely():
    shapely = pytest.importorskip("shapely")
    from shapely.geometry import Point, box
    ezdxf = pytest.importorskip("ezdxf")
    db = ezdxf.readfile(ST).entitydb

    def poly(h):
        pts = [(p[0], p[1]) for p in db[h].get_points("xy")]
        return box(min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))
    for lo, up, circ in (("36E", "31B", "31C"), ("37A", "322", "323")):
        ov = poly(lo).intersection(poly(up))
        assert ov.area == pytest.approx(200 * 250) and ov.bounds[2] - ov.bounds[0] == pytest.approx(200)
        c = db[circ]
        disc = Point(c.dxf.center.x, c.dxf.center.y).buffer(c.dxf.radius, 256)
        assert disc.buffer(1.0).contains(poly(lo)) and disc.intersects(poly(up))
    c = db["389"]
    assert Point(c.dxf.center.x, c.dxf.center.y).buffer(c.dxf.radius, 256).buffer(1.0).contains(poly("35C"))


@needs_inputs
def test_rebuild_is_byte_identical():
    names = OUTPUTS + [MANIFEST.name]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_5.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
