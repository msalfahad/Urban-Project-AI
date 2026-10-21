"""S9A - structural completeness, the eight dense-hatch bands, beam depth conventions and conflict audit.

    python3 -I research/alsenan_structural_s9a/build_s9a.py

A dated correction layer over the frozen S9 (research/alsenan_structural_s9, unchanged). It

  A. recomputes every released concrete and steel family of S9 from the stages' own row registers (not from S9's CSVs)
     and checks S9's inventory, deltas, S9-C01 and the conditional point estimate;
  B. finds the dense-hatch bands in ST7757.dxf independently (layer, pattern, scale; not the PRE-S8 census), measures
     their hatch against the ST7757.pdf legend from the PDF's own vector paths, and checks every band against the S1
     slab panels, the drawn columns and the S1 / S6 beam lines;
  C. compares the two readings of the beam schedule depth for all 150 superstructure beams (overall depth vs depth
     below the slab), with the slab-strip arithmetic, the panel-face, beam-junction and beam-column checks;
  D. audits the ground-beam length classes, the exterior depths, the 28 column section mismatches, the lift columns and
     the column tie hooks, separating interpretation questions from missing source information;
  E. ranks the engineer answers by the concrete and steel each would unlock.

It releases nothing: S9's 158.070 m3 / 18,845.961 kg stays the released baseline, S9A changes owners and lanes only,
with a reason for each. It never reads the old Urban BOQ (V3b), R5, R9_1, the PRE-S8 data registers or any
post-freeze output: those are read only after the freeze, by post_freeze/.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import structural_completeness as SCQ  # noqa: E402
from engine.source import structural_reconciliation as SR  # noqa: E402

ROUND = "S9A"
DATE = "2026-10-10"
BASELINE_HEAD = "5f317d2"
POLICY = "S9A_STRUCTURAL_COMPLETENESS_CORRECTION_LAYER_V1"
R = ROOT / "research"
S9 = R / "alsenan_structural_s9"
S9_MANIFEST = S9 / "16_S9_FREEZE_MANIFEST.json"
BY_SHA = ROOT / "data/inputs/by_sha256"
ST_DXF = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ST_PDF = BY_SHA / "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
S1D, S2D = R / "alsenan_structural_census_s1", R / "alsenan_structural_s2"
F = {
    "S1_FDEF": S1D / "FOOTING_DEFINITION_REGISTER.json", "S1_FOCC": S1D / "FOOTING_OCCURRENCE_REGISTER.json",
    "S1_CDEF": S1D / "COLUMN_DEFINITION_REGISTER.json", "S1_COCC": S1D / "COLUMN_OCCURRENCE_REGISTER.json",
    "S1_BOCC": S1D / "BEAM_OCCURRENCE_REGISTER.json", "S1_CBOCC": S1D / "CONTINUOUS_BEAM_OCCURRENCE_REGISTER.json",
    "S1_SLAB": S1D / "SLAB_PANEL_REGISTER.json", "S1_LEVEL": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
    "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
    "S2_RELEASE": S2D / "ALSENAN_COMPONENT_RELEASE.json",
    "S31_RELEASE": R / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json",
    "S31_TIE": R / "alsenan_column_rebar_s3_1/COLUMN_TIE_REGISTER.json",
    "S4_BBS": R / "alsenan_footing_rebar_s4/FOOTING_BBS_NET.csv",
    "S5_BBS": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_BBS_NET.csv",
    "S5_GB": R / "alsenan_ground_system_rebar_s5/GROUND_BEAM_REBAR_SUMMARY.csv",
    "S5_STRAP": R / "alsenan_ground_system_rebar_s5/STRAP_BEAM_REBAR_SUMMARY.csv",
    "S51_DELTA": R / "alsenan_ground_system_rebar_s5_1/S5_1_DELTA_COMPONENTS.csv",
    "AD1_CORR": R / "ad1_authority_decisions/05_S5_AD1_CORRECTIONS.csv",
    "D11_S5": R / "d1_1_stirrup_authority_audit/04_S5_1A_CORRECTIONS.csv",
    "D11_S6": R / "d1_1_stirrup_authority_audit/03_S6_1A_CORRECTIONS.csv",
    "S6_BBS": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_BBS_NET.csv",
    "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
    "S6_REG": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json",
    "S61_DELTA": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_DELTA_COMPONENTS.csv",
    "PS7_THICK": R / "alsenan_slab_rebar_pre_s7/02_THICKNESS_REGISTER.csv",
    "S7_ITEMS": R / "alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
    "S81_CONC": R / "alsenan_ground_slab_s8_1/03_CONCRETE_QTO.csv",
    "S81_REBAR": R / "alsenan_ground_slab_s8_1/04_REINFORCEMENT_XY_QTO.csv",
    "S83_CONC": R / "alsenan_dome_ring_s8_3/06_CONCRETE_REGISTER.csv",
    "S83_REBAR": R / "alsenan_dome_ring_s8_3/08_REBAR_QTO_REGISTER.csv",
    "S84_CONC": R / "alsenan_water_tank_s8_4/04_CONCRETE_QTO.csv",
    "S84_REBAR": R / "alsenan_water_tank_s8_4/05_REINFORCEMENT_QTO.csv",
    "S86A_VIEW": R / "alsenan_lintels_s8_6a/05_CORRECTED_ELIGIBLE_RELEASE_VIEW.csv",
    "S87_CONC": R / "alsenan_stairs_s8_7/07_CONCRETE_QTO.csv",
    "S87_REBAR": R / "alsenan_stairs_s8_7/09_REBAR_QTO.csv",
    "S88_CONFLICTS": R / "alsenan_lift_s8_8/13_BLOCKED_AND_CONFLICTS.csv",
    "S9_CONC": S9 / "02_CONCRETE_BOQ_RECONCILIATION.csv", "S9_BARS": S9 / "03_REINFORCEMENT_BOQ_RECONCILIATION.csv",
    "S9_INV": S9 / "01_COMPONENT_INVENTORY.csv", "S9_DELTA": S9 / "10_S9_DELTA_REGISTER.csv",
    "S9_SUMMARY": S9 / "14_RELEASE_SUMMARY.json", "S9_RFI": S9 / "09_ENGINEER_RFI_REGISTER.csv",
    "S9_README": S9 / "00_README.md",
}
CODE = ["engine/source/structural_completeness.py", "engine/source/structural_reconciliation.py",
        "engine/source/delta_release.py", "research/alsenan_structural_s9a/build_s9a.py",
        "research/alsenan_structural_s9a/visual_s9a.py"]
OUTPUTS = ["00_README.md", "01_S9_TOTALS_VERIFICATION.csv", "02_S9_INVENTORY_VERIFICATION.csv",
           "03_BAND_CORRECTION_REGISTER.csv", "04_BAND_EVIDENCE.json", "05_BEAM_CONVENTION_COMPARISON.csv",
           "06_BEAM_CONVENTION_TOTALS.csv", "07_BEAM_SLAB_COLUMN_OVERLAP_AUDIT.csv", "08_GROUND_BEAM_AUDIT.csv",
           "09_COLUMN_AUDIT.csv", "10_S9A_DELTA_REGISTER.csv", "11_CONCRETE_AND_STEEL_RECONCILIATION.csv",
           "12_STRUCTURAL_COMPLETENESS_REPORT.md", "13_ENGINEER_RFI_REGISTER.csv", "14_UNLOCK_RANKING.csv",
           "15_CONSERVATION_CHECKS.csv", "16_S9A_SUMMARY.json", "17_PROVENANCE.jsonl"]
MANIFEST_NAME = "18_S9A_CORRECTION_MANIFEST.json"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
FIREWALL = re.compile(r"registers_v3b|R9_1|alsenan_arch_truth_05|post_freeze|pre_s8_structural_completeness")
RELEASED = ("RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA")
SHEETS = {"GFRS": ("GROUND FLOOR ROOF SLAB", 4, "GF"), "FFRS": ("FIRST FLOOR ROOF SLAB", 5, "1F"),
          "SFRS": ("SECOND FLOOR ROOF SLAB", 6, "2F")}
STOREY_SHEET = {v[2]: k for k, v in SHEETS.items()}
GB_BOUNDS = (2.5, 5.0)                                # p.13: < 2.5 m 30x30, 2.5 - 5 m 30x40, > 5 m 30x60
GB_DEPTH = {0: 300.0, 1: 400.0, 2: 600.0}


class S9AError(RuntimeError):
    pass


def check(cond, msg):
    if not cond:
        raise S9AError(msg)


# ------------------------------------------------------------------ io
def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(v):
    return None if v in (None, "", "None") else float(v)


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.9f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict, tuple)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(rows, fields=None):
    keys = fields or list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    return buf.getvalue()


# ------------------------------------------------------------------ integrity
def frozen_manifests():
    """The S9 manifest and every stage manifest S9 froze over, found by the sha256 S9 recorded."""
    m = _j(S9_MANIFEST)
    DR.verify_frozen(S9_MANIFEST, ROOT)
    want = dict((v, k) for k, v in m["frozen_baselines"].items())
    found = {}
    for p in sorted(R.glob("*/*.json")):
        h = _sha(p)
        if h in want:
            DR.verify_frozen(p, ROOT)
            found[want[h]] = str(p.relative_to(ROOT))
    check(set(found) == set(m["frozen_baselines"]), f"stage manifests missing: {set(m['frozen_baselines']) - set(found)}")
    for stage, sha in m["stage_indexes"].items():
        d = {"S1": S1D, "S2": S2D, "S3": R / "alsenan_column_rebar_s3", "S3.1": R / "alsenan_column_rebar_s3_1"}[stage]
        check(_sha(d / "INDEX.json") == sha, f"{stage} index changed")
    return {"S9": _sha(S9_MANIFEST), **{k: m["frozen_baselines"][k] for k in sorted(found)}}, found


# ============================================================================ A. verify S9
def _s2():
    return {c["element_id"]: c["release_state"] for c in _j(F["S2_RELEASE"])["components"] if c["component"] == "CONCRETE"}


def _shoelace(pts):
    return abs(math.fsum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def independent_concrete():
    """Every released concrete family recomputed from the row registers of the stage that owns it."""
    s2 = _s2()
    out = {}
    # footings: S1 schedule x outline, the shallower of two overlapping outlines gives up the shared prism
    fdef = {r["footing_type"]: r for r in _j(F["S1_FDEF"])["rows"]}
    occ = _j(F["S1_FOCC"])["rows"]

    def box(r):
        x0, y0, x1, y1 = r["outline"]["bbox"]
        return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
    ded = defaultdict(float)
    for i, a in enumerate(occ):
        for b in occ[i + 1:]:
            if not a["type"] or not b["type"]:
                continue
            ov = SR.rect_overlap(box(a), box(b)) / 1e6
            if ov > 0:
                da, db = fdef[a["type"]]["D_cm"], fdef[b["type"]]["D_cm"]
                ded[(a if da <= db else b)["footing_id"]] += ov * min(da, db) / 100
    foot = []
    for r in occ:
        if not r["type"] or s2.get(r["footing_id"]) != "VERIFIED" or r["terminal_state"] != "COUNTED_AND_DEFINED":
            continue
        d = fdef[r["type"]]
        x0, y0, x1, y1 = box(r)
        drawn = sorted([(x1 - x0) / 1000, (y1 - y0) / 1000])
        if abs(drawn[0] - min(d["L_cm"], d["W_cm"]) / 100) < 0.002 and abs(drawn[1] - max(d["L_cm"], d["W_cm"]) / 100) \
                < 0.002:
            foot.append(d["L_cm"] * d["W_cm"] * d["D_cm"] / 1e6 - ded[r["footing_id"]])
    out["FOOTINGS"] = (math.fsum(foot), len(foot), "S1 schedule L x W x D, outline = schedule, S2 VERIFIED; F9 / FN "
                                                   "overlap prism deducted once")
    # columns: schedule section x printed floor-to-floor, S2 VERIFIED, drawn = schedule
    h = {x["storey"]: x["floor_to_floor_m"] for x in _j(F["S1_LEVEL"])["intervals"]}
    cols = [r["schedule_section_cm"][0] * r["schedule_section_cm"][1] / 1e4 * h[r["floor"]]
            for r in _j(F["S1_COCC"])["rows"] if r["floor"] != "FOUNDATION" and s2.get(r["column_id"]) == "VERIFIED"
            and r["drawn_vs_schedule"] == "MATCH" and r["schedule_section_cm"]]
    out["COLUMNS"] = (math.fsum(cols), len(cols), "schedule section x printed floor-to-floor (4.5 / 4.2 / 4.2)")
    # ground beams: explicit width and depth x clear concrete length
    gb = [float(r["member_clear_concrete_length_m"]) * float(r["width_mm"]) * float(r["depth_mm"]) / 1e6
          for p in (F["S5_GB"], F["S5_STRAP"]) for r in _rows(p)
          if r["width_state"] == r["depth_state"] == "SOURCE_EXPLICIT"]
    out["GROUND_BEAMS"] = (math.fsum(gb), len(gb), "S5 explicit sections x clear concrete length")
    # slabs: S1 area x PRE-S7 thickness for S2-VERIFIED suspended panels not owned by an S8 stage
    thick = {r["SLAB_PANEL_ID"]: r for r in _rows(F["PS7_THICK"])}
    tank = {r["PANEL_ID"] for r in _rows(F["S84_CONC"]) if r["PANEL_ID"]}
    sl = []
    for r in _j(F["S1_SLAB"])["rows"]:
        if r["floor"] == "GROUND_SLAB_SOG" or r["class"] != "SLAB_PANEL" or r["panel_id"] in tank:
            continue
        if s2.get(r["panel_id"]) != "VERIFIED" or r["terminal_state"] != "COUNTED_AND_DEFINED":
            continue
        t = thick[r["panel_id"]]
        pts = [(x / 1000, y / 1000) for x, y in r["polygon_mm"]]
        a = _shoelace(pts) - math.fsum(_shoelace([(x / 1000, y / 1000) for x, y in hh]) for hh in r.get("holes_mm") or [])
        if t["STATE"] == "RESOLVED" and abs(a - r["area_m2"]) < 0.002:
            sl.append(r["area_m2"] * float(t["EFFECTIVE_THICKNESS_MM"]) / 1000)
    out["SLABS"] = (math.fsum(sl), len(sl), "S1 panel area x PRE-S7 thickness, S2 VERIFIED, own shoelace agrees")
    # frozen S8 stages: their own released rows
    out["GROUND_SLAB"] = (math.fsum(float(r["VOLUME_M3"]) for r in _rows(F["S81_CONC"]) if r["LANE"] == "PROJECT_BASIS_QTO"),
                          2, "S8.1 03 PROJECT_BASIS_QTO cells")
    out["DOMES"] = (math.fsum(float(r["M3"]) for r in _rows(F["S83_CONC"]) if r["RELEASED"] == "True"), 2,
                    "S8.3 06 released shells")
    out["WATER_TANK_ROOF"] = (math.fsum(float(r["VOLUME_M3"]) for r in _rows(F["S84_CONC"]) if r["RELEASED"] == "True"),
                              2, "S8.4 04 released panels")
    lv = [r for r in _rows(F["S86A_VIEW"]) if r["CORRECTED_LANE"] == "PROJECT_BASIS_QTO"]
    out["LINTELS"] = (math.fsum(float(r["CORRECTED_M3"]) for r in lv), len(lv), "S8.6A 05 corrected view (7 retained)")
    st = [r for r in _rows(F["S87_CONC"]) if r["LANE"] == "PROJECT_BASIS_QTO"]
    out["STAIRS"] = (math.fsum(float(r["CONCRETE_M3"]) for r in st), len(st), "S8.7 07 released plates")
    return out


def independent_steel():
    out, notes = {}, {}
    reg = _j(F["S31_RELEASE"])["rows"]
    vlb = [p for p in reg if p["release_state"] in ("VERIFIED", "LOWER_BOUND")]
    c01 = [p for p in vlb if p["component"] == "TIES" and p["length_kind"] in ("TIE_CORE_PATH", "HOOK_1", "HOOK_2")]
    out["COLUMNS"] = math.fsum(p["kg"] for p in vlb) - math.fsum(p["kg"] for p in c01)
    notes["COLUMNS"] = f"S3.1 VERIFIED + LOWER_BOUND parts ({len(vlb)}) less S9-C01 ({len(c01)} tie paths / hooks)"
    out["FOOTINGS"] = math.fsum(float(r["net_bbs_kg"]) for r in _rows(F["S4_BBS"]))
    notes["FOOTINGS"] = "S4 net BBS (D1.2 changes no kg)"
    s51 = math.fsum(max(0.0, float(r["DELTA_KNOWN_QUANTITY"] or 0)) for r in _rows(F["S51_DELTA"]))
    out["GROUND_BEAMS"] = (math.fsum(float(r["net_bbs_kg"]) for r in _rows(F["S5_BBS"])) + s51
                           + math.fsum(float(r["CORRECTION_KG"]) for r in _rows(F["AD1_CORR"]))
                           + math.fsum(float(r["CORRECTION_KG"]) for r in _rows(F["D11_S5"])))
    notes["GROUND_BEAMS"] = "S5 net BBS + S5.1 known deltas + AD1 + D1.1 corrections"
    s61 = math.fsum(max(0.0, float(r["DELTA_KNOWN_QUANTITY"] or 0)) for r in _rows(F["S61_DELTA"]))
    out["BEAMS"] = (math.fsum(float(r["net_bbs_kg"]) for r in _rows(F["S6_BBS"])) + s61
                    + math.fsum(float(r["CORRECTION_KG"]) for r in _rows(F["D11_S6"])))
    notes["BEAMS"] = "S6 net BBS + S6.1 known deltas + D1.1 corrections"
    out["SLABS"] = math.fsum(float(r["KG"]) for r in _rows(F["S7_ITEMS"]) if r["S7_LANE"] == "PROJECT_BASIS_QTO")
    notes["SLABS"] = "S7 01 release items"
    out["GROUND_SLAB"] = math.fsum(float(r["KG"]) for r in _rows(F["S81_REBAR"]) if r["LANE"] == "PROJECT_BASIS_QTO")
    notes["GROUND_SLAB"] = "S8.1 04 items"
    out["DOMES"] = math.fsum(float(r["KG"]) for r in _rows(F["S83_REBAR"]) if r["RELEASED"] == "True")
    notes["DOMES"] = "S8.3 08 released meshes"
    out["WATER_TANK_ROOF"] = math.fsum(float(r["RELEASED_KG"]) for r in _rows(F["S84_REBAR"]) if r["RELEASED"] == "True")
    notes["WATER_TANK_ROOF"] = "S8.4 05 released kg"
    out["LINTELS"] = math.fsum(float(r["CORRECTED_KG"]) for r in _rows(F["S86A_VIEW"])
                               if r["CORRECTED_LANE"] == "PROJECT_BASIS_QTO")
    notes["LINTELS"] = "S8.6A 05 corrected view"
    out["STAIRS"] = math.fsum(float(r["KG"]) for r in _rows(F["S87_REBAR"]) if r["QUANTITY_STATE"] == "PROJECT_BASIS_QTO")
    notes["STAIRS"] = "S8.7 09 released plates"
    return out, notes, math.fsum(p["kg"] for p in c01), len(c01)


def verify_s9():
    s9 = _j(F["S9_SUMMARY"])
    conc9 = _rows(F["S9_CONC"])
    bars9 = _rows(F["S9_BARS"])
    ic = independent_concrete()
    isteel, notes, c01_kg, c01_n = independent_steel()
    rows = []
    for fam, (v, n, how) in sorted(ic.items()):
        pub = s9["released_concrete_m3_by_family"][fam]
        rowsum = math.fsum(_f(c["RELEASED_M3"]) for c in conc9 if c["FAMILY"] == fam and c["LANE"] in RELEASED)
        rows.append({"TRADE": "CONCRETE", "FAMILY": fam, "UNIT": "m3", "S9_PUBLISHED": pub, "S9_ROW_SUM": _r(rowsum),
                     "INDEPENDENT_RECOMPUTE": _r(v), "INDEPENDENT_COMPONENTS": n,
                     "PUBLISHED_MINUS_INDEPENDENT": _r(pub - v, 12), "METHOD": how,
                     "RESULT": "AGREES" if abs(pub - v) < 5e-7 else "DIFFERS"})
    for fam, v in sorted(isteel.items()):
        pub = s9["released_reinforcement_kg_by_family"][fam]
        rowsum = math.fsum(_f(b["AUTHORITATIVE_KG"]) for b in bars9 if b["FAMILY"] == fam and b["LANE"] in RELEASED)
        rows.append({"TRADE": "REINFORCEMENT", "FAMILY": fam, "UNIT": "kg", "S9_PUBLISHED": pub,
                     "S9_ROW_SUM": _r(rowsum), "INDEPENDENT_RECOMPUTE": _r(v),
                     "PUBLISHED_MINUS_INDEPENDENT": _r(pub - v, 12), "METHOD": notes[fam],
                     "RESULT": "AGREES" if abs(pub - v) < 5e-7 else "DIFFERS"})
    tot_c = math.fsum(v for v, _, _ in ic.values())
    tot_s = math.fsum(isteel.values())
    rd = F["S9_README"].read_text(encoding="utf-8")
    rd = rd[rd.index("**Reinforcement:"):rd.index("The full released BOQ")]
    readme_kg = [float(x.replace(",", "")) for x in re.findall(r"\| ([0-9,]+\.[0-9]{3}) \| [0-9.]+ \| S", rd)]
    rows.append({"TRADE": "CONCRETE", "FAMILY": "TOTAL", "UNIT": "m3", "S9_PUBLISHED": s9["released_concrete_m3_total"],
                 "INDEPENDENT_RECOMPUTE": _r(tot_c), "PUBLISHED_MINUS_INDEPENDENT":
                 _r(s9["released_concrete_m3_total"] - tot_c, 12), "METHOD": "sum of the families",
                 "RESULT": "AGREES" if abs(s9["released_concrete_m3_total"] - tot_c) < 5e-7 else "DIFFERS"})
    rows.append({"TRADE": "REINFORCEMENT", "FAMILY": "TOTAL", "UNIT": "kg",
                 "S9_PUBLISHED": s9["released_reinforcement_kg_total"], "INDEPENDENT_RECOMPUTE": _r(tot_s),
                 "PUBLISHED_MINUS_INDEPENDENT": _r(s9["released_reinforcement_kg_total"] - tot_s, 12),
                 "METHOD": "sum of the families", "RESULT": "AGREES" if abs(s9["released_reinforcement_kg_total"] - tot_s)
                 < 5e-6 else "DIFFERS"})
    rows.append({"TRADE": "REINFORCEMENT", "FAMILY": "README_TABLE_3DP", "UNIT": "kg",
                 "S9_PUBLISHED": _r(math.fsum(readme_kg), 3), "INDEPENDENT_RECOMPUTE": _r(tot_s, 3),
                 "PUBLISHED_MINUS_INDEPENDENT": _r(math.fsum(readme_kg) - round(tot_s, 3), 6),
                 "METHOD": f"the S9 README family table ({len(readme_kg)} rows at 3 dp) summed: each family is rounded "
                           "before the sum, so the table adds up to 0.001 kg more than the unrounded total",
                 "RESULT": "ROUNDING_ONLY" if abs(math.fsum(readme_kg) - round(tot_s, 3)) <= 0.0015 else "DIFFERS"})
    check(len(readme_kg) == 10, "the S9 README steel table has 10 rows")
    return rows, {"concrete_m3": tot_c, "kg": tot_s, "c01_kg": c01_kg, "c01_parts": c01_n}


def verify_inventory():
    s9 = _j(F["S9_SUMMARY"])
    conc = _rows(F["S9_CONC"])
    inv = _rows(F["S9_INV"])
    dl = _rows(F["S9_DELTA"])
    lanes = Counter(c["LANE"] for c in conc)
    rows = []

    def add(cid, what, ok, detail):
        rows.append({"CHECK_ID": cid, "CHECK": what, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
        check(ok, f"{cid}: {what} ({detail})")
    add("V01", "560 inventory records, one per component id", len(conc) == 560 == len({c["COMPONENT_ID"] for c in conc})
        == len(inv) == s9["components"], f"{len(conc)} concrete rows, {len(inv)} inventory rows")
    add("V02", "every record holds exactly one lane, and the lanes are mutually exclusive",
        all(c["LANE"] for c in conc) and sum(lanes.values()) == 560 and dict(sorted(lanes.items())) ==
        s9["components_by_lane"], json.dumps(dict(sorted(lanes.items()))))
    rel9 = {c["COMPONENT_ID"]: _f(c["RELEASED_M3"]) for c in conc if c["LANE"] == "RELEASED_S9_DELTA"}
    d9 = [d for d in dl if d["DELTA_ID"].startswith("S9-D")]
    add("V03", "110 S9 concrete deltas, each on one released S9 component, equal in value",
        len(d9) == 110 == len(rel9) and {d["COMPONENT_ID"] for d in d9} == set(rel9) and
        all(abs(float(d["DELTA_M3"]) - rel9[d["COMPONENT_ID"]]) < 1e-9 for d in d9),
        f"{len(d9)} deltas, sum {math.fsum(float(d['DELTA_M3']) for d in d9):.6f} m3")
    add("V04", "the deltas sum to the published S9 delta release",
        abs(math.fsum(float(d["DELTA_M3"]) for d in d9) - s9["released_concrete_m3_s9_delta"]) < 5e-7,
        f"{s9['released_concrete_m3_s9_delta']} m3")
    c01 = [d for d in dl if d["DELTA_ID"] == "S9-C01"]
    reg = _j(F["S31_RELEASE"])["rows"]
    tie = [p for p in reg if p["release_state"] in ("VERIFIED", "LOWER_BOUND") and p["component"] == "TIES"
           and p["length_kind"] in ("TIE_CORE_PATH", "HOOK_1", "HOOK_2")]
    add("V05", "S9-C01 = the S3.1 tie paths and hook allowances, 288 parts, 1,217.128 kg",
        len(c01) == 1 and len(tie) == 288 and abs(float(c01[0]["DELTA_KG"]) + math.fsum(p["kg"] for p in tie)) < 1e-6
        and abs(math.fsum(p["kg"] for p in tie) - 1217.128) < 1e-6, f"{math.fsum(p['kg'] for p in tie):.3f} kg")
    def point(c):                     # S9's definition: the conditional value, else the low end of a two-sided range
        if c["CONDITIONAL_M3"]:
            return float(c["CONDITIONAL_M3"])
        rng = [v for v in (json.loads(c["CONDITIONAL_RANGE_M3"]) if c["CONDITIONAL_RANGE_M3"] else []) if v is not None]
        return rng[0] if len(rng) == 2 else None
    cond = [c for c in conc if c["LANE"] in ("CONDITIONAL_NOT_RELEASED", "SOURCE_CONFLICT") and point(c) is not None]
    cp = math.fsum(point(c) for c in cond)
    add("V06", "the 98.994 m3 conditional point sits only on unreleased rows, never in a released total",
        abs(cp - s9["conditional_point_m3"]) < 2e-6 and not any(c["RELEASED_M3"] for c in cond) and
        abs(math.fsum(_f(c["RELEASED_M3"]) for c in conc if c["LANE"] in RELEASED) - s9["released_concrete_m3_total"])
        < 5e-7, f"{cp:.6f} m3 conditional over {len(cond)} rows; released {s9['released_concrete_m3_total']} m3")
    add("V07", "unreleased rows carry no released quantity and no authoritative kg",
        not [c for c in conc if c["LANE"] not in RELEASED and c["RELEASED_M3"]] and
        not [b for b in _rows(F["S9_BARS"]) if b["LANE"] not in RELEASED and b["AUTHORITATIVE_KG"]], "")
    return rows


# ============================================================================ B. the dense-hatch bands
class Drawing:
    """ST7757.dxf sheets (frames = DEFPOINTS boxes holding the title inserts; local = model - frame origin)."""

    def __init__(self, path=ST_DXF):
        import ezdxf
        from ezdxf import bbox as BB
        self.doc = ezdxf.readfile(str(path))
        self.msp = self.doc.modelspace()
        frames = []
        for e in self.msp.query('LWPOLYLINE[layer=="DEFPOINTS"]'):
            b = BB.extents([e])
            if b.extmax.x - b.extmin.x > 20000 and b.extmax.y - b.extmin.y > 10000:
                frames.append((e.dxf.handle, (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)))
        self.frames = {}
        for name, (title, page, _) in SHEETS.items():
            ins = [i for i in self.msp.query("INSERT") if i.dxf.name == name]
            check(len(ins) == 1, f"title insert {name}")
            p = ins[0].dxf.insert
            hit = [f for f in frames if f[1][0] <= p.x <= f[1][2] and f[1][1] <= p.y <= f[1][3]]
            check(len(hit) == 1, f"frame of {name}")
            self.frames[name] = {"handle": hit[0][0], "box": hit[0][1], "title": title, "page": page}

    def sheet_of(self, x, y):
        for k, f in self.frames.items():
            a, b, c, d = f["box"]
            if a <= x <= c and b <= y <= d:
                return k
        return None

    def local(self, sheet, x, y):
        a, b, _, _ = self.frames[sheet]["box"]
        return (x - a, y - b)

    def hatch_polygon(self, e):
        """(vertices of the first boundary path, straight?) - a bulge or a curved edge makes it not straight."""
        p = e.paths[0]
        if hasattr(p, "vertices"):
            straight = all(abs(v[2] if len(v) > 2 else 0.0) < 1e-12 for v in p.vertices)
            return [(float(v[0]), float(v[1])) for v in p.vertices], straight
        straight = all(ed.EDGE_TYPE == "LineEdge" for ed in p.edges)
        return [(float(ed.start.x), float(ed.start.y)) for ed in p.edges if hasattr(ed, "start")], straight

    def lines(self, sheet, layers=("1",)):
        """Drawn segments on the layers (lines, polyline edges, arcs as 64-chord polylines), local mm."""
        out = []
        for e in self.msp.query("LINE LWPOLYLINE ARC"):
            if e.dxf.layer not in layers:
                continue
            if e.dxftype() == "LINE":
                segs = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))]
            elif e.dxftype() == "ARC":
                c, rr = e.dxf.center, e.dxf.radius
                a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                if a1 < a0:
                    a1 += 2 * math.pi
                pts = [(c.x + rr * math.cos(a0 + (a1 - a0) * i / 64), c.y + rr * math.sin(a0 + (a1 - a0) * i / 64))
                       for i in range(65)]
                segs = list(zip(pts, pts[1:]))
            else:
                pts = [(p[0], p[1]) for p in e.get_points()]
                segs = list(zip(pts, pts[1:] + (pts[:1] if e.closed else [])))
            for a, b in segs:
                if self.sheet_of(*a) == sheet and self.sheet_of(*b) == sheet:
                    out.append((self.local(sheet, *a), self.local(sheet, *b)))
        return out

    def columns(self, sheet):
        out = []
        for e in self.msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
            pts = [(p[0], p[1]) for p in e.get_points()]
            cx, cy = sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
            if self.sheet_of(cx, cy) == sheet:
                out.append((e.dxf.handle, [self.local(sheet, x, y) for x, y in pts]))
        return out

    def texts(self, sheet):
        out = []
        for t in self.msp.query("TEXT MTEXT"):
            s = t.dxf.text if t.dxftype() == "TEXT" else t.plain_text()
            p = t.dxf.insert
            if self.sheet_of(p.x, p.y) == sheet:
                out.append({"handle": t.dxf.handle, "layer": t.dxf.layer, "text": s,
                            "p": self.local(sheet, p.x, p.y)})
        return out


class PlotPDF:
    """ST7757.pdf vector paths (pages plotted at 1:100 from the same sheets; /Rotate 270)."""

    def __init__(self, path=ST_PDF):
        from pypdf import PdfReader
        self.reader = PdfReader(str(path))
        self._segs = {}

    def segments(self, page):
        if page in self._segs:
            return self._segs[page]
        pg = self.reader.pages[page - 1]
        mb = [float(v) for v in pg.mediabox]
        check(int(pg.get("/Rotate") or 0) == 270 and mb == [0.0, 0.0, 842.0, 1191.0], f"page {page} geometry")
        W, H = mb[2], mb[3]
        tok = re.compile(rb"(-?\d*\.?\d+(?:[eE][-+]?\d+)?)|([A-Za-z'\"*]+)|(\[|\]|<<|>>|/[^\s/\[\]()<>]+|\([^)]*\))")
        stack, ctm, gs, cur, segs = [], [1, 0, 0, 1, 0, 0], [], None, []

        def mul(m, n):
            a, b, c, d, e, f = m
            A, B, C, D, E, Fv = n
            return [a * A + b * C, a * B + b * D, c * A + d * C, c * B + d * D, e * A + f * C + E, e * B + f * D + Fv]

        def tr(x, y):
            a, b, c, d, e, f = ctm
            X, Y = a * x + c * y + e, b * x + d * y + f
            return (H - Y, W - X)                     # display frame of a /Rotate 270 page: u right, v down (pt)
        for m in tok.finditer(pg.get_contents().get_data()):
            num, op, other = m.groups()
            if num is not None:
                stack.append(float(num))
                continue
            if other is not None:
                stack = []
                continue
            o = op.decode()
            if o == "cm" and len(stack) >= 6:
                ctm = mul(stack[-6:], ctm)
            elif o == "q":
                gs.append(ctm[:])
            elif o == "Q":
                ctm = gs.pop() if gs else ctm
            elif o == "m" and len(stack) >= 2:
                cur = tr(*stack[-2:])
            elif o == "l" and len(stack) >= 2 and cur is not None:
                p = tr(*stack[-2:])
                segs.append((cur, p))
                cur = p
            stack = []
        self._segs[page] = segs
        return segs

    @staticmethod
    def diagonal_offsets(segs, box, pad):
        u0, v0, u1, v1 = box
        offs = []
        for a, b in segs:
            if not (u0 - pad <= min(a[0], b[0]) and max(a[0], b[0]) <= u1 + pad and v0 - pad <= min(a[1], b[1])
                    and max(a[1], b[1]) <= v1 + pad):
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 0.3:
                continue
            ang = math.degrees(math.atan2(dy, dx)) % 180
            if min(abs(ang - 45), abs(ang - 135)) < 3:
                n = (1 / math.sqrt(2), 1 / math.sqrt(2)) if abs(ang - 135) < 3 else (1 / math.sqrt(2), -1 / math.sqrt(2))
                offs.append(a[0] * n[0] + a[1] * n[1])
        cl = []
        for o in sorted(offs):
            if cl and o - cl[-1][-1] < 0.05:
                cl[-1].append(o)
            else:
                cl.append([o])
        return [sum(c) / len(c) for c in cl]

    def legend_boxes(self, page):
        """The four legend boxes (21.2 x 14.2 pt) of the slab-sheet legend, top to bottom."""
        segs = self.segments(page)
        hs = sorted((round(min(a[1], b[1]), 2), round(min(a[0], b[0]), 2), round(max(a[0], b[0]), 2)) for a, b in segs
                    if abs(a[1] - b[1]) < 0.01 and 21.0 < abs(a[0] - b[0]) < 22.5 and 1040 < a[0] < 1080
                    and 220 < a[1] < 320)
        boxes, used = [], set()
        for i, (v, ua, ub) in enumerate(hs):
            for j, (v2, ua2, ub2) in enumerate(hs):
                if j > i and abs(ua - ua2) < 0.1 and 13 < v2 - v < 14.5 and i not in used and j not in used:
                    boxes.append((ua, v, ub, v2))
                    used |= {i, j}
        return sorted(boxes, key=lambda b: b[1])


PT_TO_MODEL_MM = 25.4 / 72 * 100                      # 1 pt of a 1:100 plot


def band_population(dwg):
    """Every patterned S-HAT.BAT hatch on the three slab sheets, grouped by pattern and scale."""
    pop = []
    for e in dwg.msp.query("HATCH"):
        if e.dxf.layer != "S-HAT.BAT" or e.dxf.solid_fill:
            continue
        poly, straight = dwg.hatch_polygon(e)
        cx, cy = sum(x for x, _ in poly) / len(poly), sum(y for _, y in poly) / len(poly)
        sh = dwg.sheet_of(cx, cy)
        if sh is None:
            continue
        ln = e.pattern.lines[0]
        a = math.radians(ln.angle)
        spacing = abs(-ln.offset[0] * math.sin(a) + ln.offset[1] * math.cos(a))
        loc = [dwg.local(sh, x, y) for x, y in poly]
        pop.append({"handle": e.dxf.handle, "sheet": sh, "pattern": e.dxf.pattern_name,
                    "pattern_scale": float(e.dxf.pattern_scale), "pattern_angle": float(ln.angle),
                    "line_spacing_mm": _r(spacing, 3), "paths": len(e.paths), "straight": straight,
                    "polygon_local_mm": loc,
                    "polygon_model_mm": poly, "area_m2": _shoelace(loc) / 1e6,
                    "boundary_objects": [(h, (dwg.doc.entitydb.get(h).dxftype(), dwg.doc.entitydb.get(h).dxf.layer))
                                         for h in e.paths[0].source_boundary_objects]})
    return sorted(pop, key=lambda r: (r["sheet"], r["handle"]))


def beam_lines_index():
    """S1 / S6 beam lines: for each (sheet, BL) the occurrences that run on it, with their station range."""
    idx = defaultdict(list)
    for r in _j(F["S1_BOCC"])["rows"]:
        if r.get("member") and r.get("sheet") and r.get("span_stations_mm"):
            idx[(r["sheet"], r["member"])].append({"id": r["beam_id"], "stations": sorted(r["span_stations_mm"]),
                                                   "width_mm": r.get("width_drawn_mm"), "tagged": True,
                                                   "orientation": r.get("orientation_deg")})
    for r in _j(F["S1_CBOCC"])["rows"]:
        for i, s in enumerate(r["plan_spans"], 1):
            idx[(r["sheet"], s["member"])].append({"id": f"{r['cb_id']}#SPAN{i}", "stations": sorted([s["s0"], s["s1"]]),
                                                   "width_mm": (r.get("drawn_width_mm") or [None])[0], "tagged": True})
    for u in _j(F["S6_REG"])["untagged"]:
        m = re.match(r"SPAN:(\w+):(BL\d+):([\d.]+)-([\d.]+)", u["object_id"])
        if m:
            idx[(m.group(1), m.group(2))].append({"id": u["object_id"], "stations": sorted([float(m.group(3)),
                                                                                            float(m.group(4))]),
                                                  "width_mm": u["drawn_width_mm"], "tagged": False})
    return idx


def bands(dwg, pdf, s9conc):
    pop = band_population(dwg)
    dense = [p for p in pop if p["pattern"] == "ANSI31" and abs(p["line_spacing_mm"] - 100.0) < 0.5]
    sunken = [p for p in pop if p["pattern"] == "ANSI31" and abs(p["line_spacing_mm"] - 250.0) < 0.5]
    other = [p for p in pop if p not in dense and p not in sunken]
    check(not other, f"unclassified slab-sheet hatches: {[p['handle'] for p in other]}")
    check(all(p["straight"] and p["paths"] == 1 for p in dense), "a dense band with a curved or multiple boundary")
    # the legend: three symbols measured from the PDF's own vector paths, page by page
    legend = {}
    for sh, (_, page, _) in SHEETS.items():
        boxes = pdf.legend_boxes(page)
        check(len(boxes) >= 3, f"legend boxes on page {page}")
        segs = pdf.segments(page)
        for name, b in zip(("CANTILEVER_PORTION", "SUNKEN_SLAB", "BEARING_WALL"), boxes):
            hs = SCQ.hatch_spacing(pdf.diagonal_offsets(segs, b, 0.05), min_gap=0.2)
            legend[(page, name)] = {"box_pt": [round(v, 2) for v in b], "spacing_model_mm": _r(hs["spacing"] *
                                    PT_TO_MODEL_MM, 2), "lines": hs["lines"]}
    refs = {}
    for name in ("CANTILEVER_PORTION", "SUNKEN_SLAB", "BEARING_WALL"):
        vals = [legend[(p, name)]["spacing_model_mm"] for _, p, _ in SHEETS.values()]
        check(max(vals) - min(vals) < 0.01, f"legend {name} differs between pages")
        refs[name] = vals[0]
    check(abs(refs["CANTILEVER_PORTION"] - refs["BEARING_WALL"]) / refs["BEARING_WALL"] > 0.08,
          "the cantilever and bearing-wall symbols cannot be told apart")
    # plot calibration: the sheet frame plots at 1:100 inside the drawing border
    s1 = {r["panel_id"]: r for r in _j(F["S1_SLAB"])["rows"]}
    idx = beam_lines_index()
    s9 = {c["COMPONENT_ID"]: c for c in s9conc}
    rows, evid = [], []
    for k, b in enumerate(sorted(dense, key=lambda r: (["GFRS", "FFRS", "SFRS"].index(r["sheet"]),
                                                      r["polygon_local_mm"][0][1], r["polygon_local_mm"][0][0])), 1):
        sh = b["sheet"]
        loc = b["polygon_local_mm"]
        xs, ys = [x for x, _ in loc], [y for _, y in loc]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        check(abs(b["area_m2"] - (x1 - x0) * (y1 - y0) / 1e6) < 1e-6, f"{b['handle']}: not a rectangle")
        page = SHEETS[sh][1]
        fw, fh = (dwg.frames[sh]["box"][2] - dwg.frames[sh]["box"][0]), (dwg.frames[sh]["box"][3] - dwg.frames[sh]["box"][1])
        # display pt of the frame: right edge 1021.32 pt, bottom 818.28 pt (1418.5 / 1136.5 px at 100 dpi)
        U1, VB = 1418.5 * 0.72, 1136.5 * 0.72
        U0 = U1 - fw / PT_TO_MODEL_MM
        box_pt = (U0 + x0 / PT_TO_MODEL_MM, VB - y1 / PT_TO_MODEL_MM, U0 + x1 / PT_TO_MODEL_MM, VB - y0 / PT_TO_MODEL_MM)
        check(abs(fh / PT_TO_MODEL_MM - (1136.5 - 33.5) * 0.72) < 1.0, "the frame does not plot at 1:100")
        measured = None
        for pad in (0.2, 0.5, 1.0):
            hs = SCQ.hatch_spacing(pdf.diagonal_offsets(pdf.segments(page), box_pt, pad), min_gap=0.2)
            if hs and hs["lines"] >= 2:
                measured = {"pad_pt": pad, "spacing_model_mm": _r(hs["spacing"] * PT_TO_MODEL_MM, 2),
                            "lines": hs["lines"]}
                break
        label, dist = SCQ.nearest_reference(measured and measured["spacing_model_mm"], refs, max_rel=0.06)
        # overlaps: S1 slab panels (exact sampling), drawn columns, S1 / S6 beam lines on the band's edges
        panels = []
        for pid, r in s1.items():
            if r["sheet"] == sh and r.get("polygon_mm"):
                a = SCQ.rect_polygon_overlap((x0, y0, x1, y1), r["polygon_mm"], r.get("holes_mm") or [], step=5.0)
                if a > 0:
                    panels.append({"panel": pid, "class": r["class"], "m2": _r(a / 1e6, 6)})
        cols = []
        for h, cp in dwg.columns(sh):
            a = SCQ.rect_polygon_overlap((x0, y0, x1, y1), cp, step=5.0)
            cx = [x for x, _ in cp]
            cy = [y for _, y in cp]
            gap = max(x0 - max(cx), min(cx) - x1, y0 - max(cy), min(cy) - y1)
            if gap <= 1.0:
                cols.append({"column_outline": h, "overlap_m2": _r(a / 1e6, 6),
                             "bbox_local_mm": [round(v, 1) for v in (min(cx), min(cy), max(cx), max(cy))]})
        edges = {"S": ((x0, y0), (x1, y0)), "N": ((x0, y1), (x1, y1)), "W": ((x0, y0), (x0, y1)),
                 "E": ((x1, y0), (x1, y1))}
        faces = []
        for pid, r in s1.items():
            if r["sheet"] != sh or not r.get("polygon_mm"):
                continue
            P = r["polygon_mm"]
            for i, e in enumerate(r.get("edges") or []):
                a, c = P[i], P[(i + 1) % len(P)]
                for side, (p, q) in edges.items():
                    hz = side in "SN"
                    if hz and abs(a[1] - c[1]) < 1 and abs(a[1] - p[1]) < 3:
                        ov = min(max(a[0], c[0]), q[0]) - max(min(a[0], c[0]), p[0])
                    elif not hz and abs(a[0] - c[0]) < 1 and abs(a[0] - p[0]) < 3:
                        ov = min(max(a[1], c[1]), q[1]) - max(min(a[1], c[1]), p[1])
                    else:
                        continue
                    if ov > 50:
                        faces.append({"side": side, "panel": pid, "panel_class": r["class"], "support": e.get("support"),
                                      "support_ref": e.get("support_ref"), "shared_mm": round(ov)})
        horiz = (x1 - x0) >= (y1 - y0)
        along = (x0, x1) if horiz else (y0, y1)
        width = (y1 - y0) if horiz else (x1 - x0)
        lines_on = sorted({f["support_ref"] for f in faces if f["support"] == "BEAM" and f["support_ref"]})
        occ = []
        for bl in lines_on:
            for o in idx.get((sh, bl), []):
                ov = min(along[1], o["stations"][1]) - max(along[0], o["stations"][0])
                if ov > 0 and o["width_mm"] and abs(float(o["width_mm"]) - width) < 1.0:
                    occ.append({**o, "line": bl, "shared_along_mm": round(ov)})
        check(len(occ) <= 1, f"{b['handle']}: two beam occurrences claim the band")
        o = occ[0] if occ else None
        s9row = s9.get(o["id"]) if o else None
        near = sorted(((math.hypot(t["p"][0] - (x0 + x1) / 2, t["p"][1] - (y0 + y1) / 2), t) for t in dwg.texts(sh)
                       if x0 - 1500 <= t["p"][0] <= x1 + 1500 and y0 - 1500 <= t["p"][1] <= y1 + 1500),
                      key=lambda z: z[0])
        bar_callouts = [t["text"].replace("%%c", "Ø").replace("%%C", "Ø") for _, t in near
                        if t["layer"] == "S-TEXT-SLAB" and re.search(r"%%[cC]\d", t["text"])][:4]
        tagged_ca = o is not None and o["tagged"]
        bid = f"S9A-CP-{k:02d}"
        rows.append({
            "BAND_ID": bid, "DXF_HANDLE": b["handle"], "SHEET": sh, "STOREY_SLAB": f"{SHEETS[sh][2]} roof slab",
            "PDF_PAGE": page, "LAYER": "S-HAT.BAT", "PATTERN": f"{b['pattern']} scale {b['pattern_scale']:g}",
            "DXF_LINE_SPACING_MM": b["line_spacing_mm"],
            "POLYGON_LOCAL_MM": [[round(x, 1), round(y, 1)] for x, y in loc],
            "POLYGON_MODEL_MM": [[round(x, 1), round(y, 1)] for x, y in b["polygon_model_mm"]],
            "LENGTH_MM": round(max(x1 - x0, y1 - y0), 1), "WIDTH_MM": round(min(x1 - x0, y1 - y0), 1),
            "ORIENTATION": "E-W" if horiz else "N-S", "AREA_M2": _r(b["area_m2"], 6),
            "PDF_SPACING_MODEL_MM": measured and measured["spacing_model_mm"],
            "LEGEND_MATCH": label, "LEGEND_DISTANCE": {k2: _r(v, 4) for k2, v in dist.items()},
            "STRUCTURAL_FAMILY": "CANTILEVER_PORTION (slab projection)" if label == "CANTILEVER_PORTION" else
            "UNCLASSIFIED_DENSE_HATCH",
            "SLAB_PANEL_OVERLAP_M2": _r(sum(p["m2"] for p in panels), 6), "SLAB_PANELS": panels or None,
            "COLUMN_OVERLAP_M2": _r(sum(c["overlap_m2"] for c in cols), 6), "COLUMNS_TOUCHING": cols,
            "BOUNDING_PANEL_FACES": faces, "BEAM_LINE": o and o["line"],
            "S9_COMPONENT_SAME_FOOTPRINT": o and o["id"], "S9_LANE": s9row and s9row["LANE"],
            "S9_FAMILY": s9row and s9row["FAMILY"],
            "DOUBLE_COUNT_RISK": "none in any total: the S9 row holds no released value" if s9row and not
            s9row["RELEASED_M3"] else ("S9 row released" if s9row else "no S9 row"),
            "OWNER_DECISION": ("BEAMS (S9 conditional row of the tagged cantilever beam CA keeps the footprint; the "
                               "band is its cantilever-portion hatch, no second object)") if tagged_ca else
            ("SLABS / CANTILEVER_PORTIONS (S9A): the untagged S6 'beam' span is the hatched cantilever portion; it "
             "leaves the beam family"),
            "THICKNESS_MM": "UNKNOWN (no T mark, section or note for the band)",
            "NEARBY_BAR_CALLOUTS": bar_callouts or None,
            "CONCRETE_STATE": "BLOCKED_UNQUANTIFIED (thickness unknown)" if not tagged_ca else
            "OWNED_BY_BEAMS (CA, conditional in S9)",
            "REINFORCEMENT_STATE": "BLOCKED_UNQUANTIFIED (no cantilever bar detail bound; S7 owns only panel / "
                                   "support items, none inside the band)",
            "CONDITIONAL_M3_IF_ADJACENT_SLAB_T": None, "RELEASED_M3": 0.0, "RELEASED_KG": 0.0,
        })
        evid.append({"band": bid, "handle": b["handle"], "boundary_objects": b["boundary_objects"],
                     "pdf_box_pt": [round(v, 2) for v in box_pt], "pdf_measure": measured, "beam_occurrence": o,
                     "nearby_texts": [{"d_mm": round(d), "layer": t["layer"], "text": t["text"]} for d, t in near[:6]]})
    # conditional value at the adjacent panel thickness (context only)
    thick = {r["SLAB_PANEL_ID"]: r for r in _rows(F["PS7_THICK"])}
    for r in rows:
        ts = sorted({float(thick[f["panel"]]["EFFECTIVE_THICKNESS_MM"]) for f in r["BOUNDING_PANEL_FACES"]
                     if f["panel_class"] == "SLAB_PANEL" and f["panel"] in thick and
                     thick[f["panel"]]["STATE"] == "RESOLVED"})
        r["ADJACENT_SLAB_T_MM"] = ts or None
        if ts and r["CONCRETE_STATE"].startswith("BLOCKED"):
            r["CONDITIONAL_M3_IF_ADJACENT_SLAB_T"] = _r(r["AREA_M2"] * max(ts) / 1000, 6)
    summary = {"population": [{k: p[k] for k in ("handle", "sheet", "pattern", "pattern_scale", "line_spacing_mm",
                                                   "area_m2")} for p in pop],
               "dense_100mm": len(dense), "sunken_250mm": len(sunken), "dense_area_m2": _r(sum(p["area_m2"]
                                                                                                   for p in dense), 6),
               "legend_reference_spacing_mm": refs,
               "legend_by_page": {f"p{p}:{n}": v for (p, n), v in sorted(legend.items())},
               "bands": evid, "rule": "a band is classified only by the legend symbol its own plotted hatch matches "
                                      "(nearest within 6 %); thickness is never inferred from the legend"}
    return rows, summary, sunken


# ============================================================================ C. beams
def _beam_line(cid):
    m = re.search(r"(BL\d+)", cid)
    return m.group(1) if m else None


def beams(dwg, s9conc, band_rows):
    s1b = {r["beam_id"]: r for r in _j(F["S1_BOCC"])["rows"]}
    cbs = {}
    for r in _j(F["S1_CBOCC"])["rows"]:
        for i, s in enumerate(r["plan_spans"], 1):
            cbs[f"{r['cb_id']}#SPAN{i}"] = s
    s6 = {r["occurrence_id"]: r for r in _rows(F["S6_OCC"])}
    thick = {r["SLAB_PANEL_ID"]: r for r in _rows(F["PS7_THICK"])}
    panels = _j(F["S1_SLAB"])["rows"]
    edges_by_line = defaultdict(list)
    for p in panels:
        P = p.get("polygon_mm")
        for i, e in enumerate(p.get("edges") or []):
            if e.get("support") == "BEAM" and e.get("support_ref") and P:
                a, c = P[i], P[(i + 1) % len(P)]
                edges_by_line[(p["sheet"], e["support_ref"])].append((p, a, c))
    band_of = {r["S9_COMPONENT_SAME_FOOTPRINT"]: r["BAND_ID"] for r in band_rows if r["S9_COMPONENT_SAME_FOOTPRINT"]}
    out = []
    for c in s9conc:
        if c["FAMILY"] != "BEAMS" or c["LANE"] == "EXCLUDED_OWNED_BY_OTHER_FAMILY":
            continue
        cid = c["COMPONENT_ID"]
        d = json.loads(c["DIMENSIONS"]) if c["DIMENSIONS"].startswith("{") else {}
        sheet = STOREY_SHEET.get(c["STOREY"])
        line = _beam_line(cid)
        stations = None
        if cid in s1b and s1b[cid].get("span_stations_mm"):
            stations = sorted(s1b[cid]["span_stations_mm"])
        elif cid in cbs:
            stations = sorted([cbs[cid]["s0"], cbs[cid]["s1"]])
        else:
            m = re.match(r"SPAN:\w+:BL\d+:([\d.]+)-([\d.]+)", cid)
            if m:
                stations = sorted([float(m.group(1)), float(m.group(2))])
        adj, adj_cls = [], set()
        for p, a, q in edges_by_line.get((sheet, line), []):
            hz = abs(a[1] - q[1]) < 1
            lo, hi = sorted([a[0], q[0]] if hz else [a[1], q[1]])
            if stations and min(hi, stations[1]) - max(lo, stations[0]) <= 50:
                continue
            adj_cls.add(p["class"])
            t = thick.get(p["panel_id"])
            if p["class"] == "SLAB_PANEL" and t and t["STATE"] == "RESOLVED":
                adj.append((float(t["EFFECTIVE_THICKNESS_MM"]), p["panel_id"], t["AUTHORITY"]))
        ts = sorted({x[0] for x in adj})
        t_mm, t_basis = (max(ts), "ADJACENT_PANELS" + (" (MIXED: thicker taken)" if len(ts) > 1 else "")) if ts else \
            (160.0, "PROJECT_DEFAULT_NO_ADJACENT_SLAB_PANEL (P8-N18 16 cm)")
        B, H = d.get("B_mm"), d.get("H_mm")
        L = d.get("clear_m")
        L_basis = "S6 clear face to face" if L and c["EVIDENCE_STATUS"].startswith("SCHEDULE_SECTION + CLEAR_FACE") else \
            ("S1 continuous-beam clear span" if L else None)
        upper_only = False
        if L is None and d.get("cc_m"):
            L, L_basis, upper_only = d["cc_m"], "arc centre length only (upper bound)", True
        missing = [n for n, v in (("B (schedule width)", B), ("H (schedule depth)", H), ("L (clear length)", L)) if not v]
        vols = None
        if not missing:
            vols = SCQ.beam_convention_volumes(B / 1000, H / 1000, L, t_mm / 1000)
        s6r = s6.get(cid.split("#")[0]) or {}
        state = ("RE_OWNED_BY_S9A (cantilever portion " + band_of[cid] + ")") if cid in band_of and \
            not cid.startswith("BM-") else ("BAND_IS_THIS_BEAM'S_HATCH (" + band_of[cid] + ")" if cid in band_of
                                             else None)
        out.append({
            "COMPONENT_ID": cid, "STOREY": c["STOREY"], "SHEET": sheet, "SUBFAMILY": c["SUBFAMILY"], "BEAM_LINE": line,
            "STATIONS_MM": stations, "S9_LANE": c["LANE"], "S9_EVIDENCE": c["EVIDENCE_STATUS"],
            "B_MM": B, "B_SOURCE": "schedule (drawn " + str(d.get("drawn_width_mm")) + ", " +
                                  str(d.get("width_match") or "") + ")" if B else
            ("drawn " + str(s6r.get("drawn_width_mm") or "") + " mm only (no tag, no schedule row)"),
            "H_MM": H, "H_SOURCE": "beam schedule depth (convention not printed)" if H else "NONE (no schedule row)",
            "L_M": L, "L_SOURCE": L_basis, "UPPER_BOUND_ONLY": upper_only,
            "SLAB_T_MM": t_mm, "SLAB_T_BASIS": t_basis, "ADJACENT_PANEL_CLASSES": sorted(adj_cls) or None,
            "MISSING": missing or None,
            "V_TOTAL_DEPTH_M3": vols and _r(vols["TOTAL_DEPTH"]), "V_BELOW_SLAB_M3": vols and _r(vols["BELOW_SLAB"]),
            "SLAB_STRIP_M3": vols and _r(vols["STRIP"]),
            "DOWNSTAND_IF_TOTAL_DEPTH_M3": vols and _r(vols["DOWNSTAND_TOTAL_DEPTH"]),
            "START_SUPPORT": s6r.get("start_support") or None, "END_SUPPORT": s6r.get("end_support") or None,
            "S9A_STATE": state or ("CONDITIONAL (convention)" if vols and not upper_only and c["LANE"] ==
                                   "CONDITIONAL_NOT_RELEASED" else
                                   "SOURCE_CONFLICT" if c["LANE"] == "SOURCE_CONFLICT" else
                                   "UPPER_BOUND_ONLY" if upper_only else "BLOCKED (" + ", ".join(missing) + ")"
                                   if missing else c["LANE"]),
            "RELEASED_M3": 0.0,
        })
    check(len(out) == 150, f"150 superstructure beams expected, {len(out)}")
    return out


def beam_totals(rows):
    out = []
    groups = [("ALL", lambda r: True)] + [(f"STOREY {s}", (lambda st: lambda r: r["STOREY"] == st)(s))
                                          for s in ("GF", "1F", "2F")]
    for name, f in groups:
        rs = [r for r in rows if f(r)]
        full = [r for r in rs if r["V_TOTAL_DEPTH_M3"] is not None and not r["UPPER_BOUND_ONLY"] and
                not r["S9A_STATE"].startswith("RE_OWNED")]
        cond = [r for r in full if r["S9_LANE"] == "CONDITIONAL_NOT_RELEASED"]
        conf = [r for r in full if r["S9_LANE"] == "SOURCE_CONFLICT"]
        ub = [r for r in rs if r["UPPER_BOUND_ONLY"]]
        miss = [r for r in rs if r["MISSING"] and not r["S9A_STATE"].startswith("RE_OWNED")]
        reown = [r for r in rs if r["S9A_STATE"].startswith("RE_OWNED")]
        for label, sel in (("conditional (schedule section + clear length)", cond), ("source conflict", conf)):
            v1 = math.fsum(r["V_TOTAL_DEPTH_M3"] for r in sel)
            v2 = math.fsum(r["V_BELOW_SLAB_M3"] for r in sel)
            out.append({"GROUP": name, "SET": label, "BEAMS": len(sel), "TOTAL_DEPTH_M3": _r(v1, 6),
                        "BELOW_SLAB_M3": _r(v2, 6), "SENSITIVITY_M3": _r(v2 - v1, 6),
                        "SENSITIVITY_PCT": _r(100 * (v2 - v1) / v1, 2) if v1 else None,
                        "DOWNSTAND_IF_TOTAL_DEPTH_M3": _r(math.fsum(r["DOWNSTAND_IF_TOTAL_DEPTH_M3"] for r in sel), 6)})
        out.append({"GROUP": name, "SET": "curved bands (centre length: upper bounds)", "BEAMS": len(ub),
                    "TOTAL_DEPTH_M3": _r(math.fsum(r["V_TOTAL_DEPTH_M3"] or 0 for r in ub), 6),
                    "BELOW_SLAB_M3": _r(math.fsum(r["V_BELOW_SLAB_M3"] or 0 for r in ub), 6)})
        out.append({"GROUP": name, "SET": "missing a dimension (no value under either reading)", "BEAMS": len(miss)})
        out.append({"GROUP": name, "SET": "re-owned by S9A as cantilever portions", "BEAMS": len(reown)})
    return out


def overlap_audit(dwg, beam_rows, s9conc):
    """Can either reading count slab concrete twice? Panels must stop at drawn beam faces; beams at column faces."""
    out = []
    rel_panels = {c["COMPONENT_ID"] for c in s9conc if c["FAMILY"] == "SLABS" and c["LANE"] in RELEASED}
    s1 = {r["panel_id"]: r for r in _j(F["S1_SLAB"])["rows"]}
    on_face, off_face, kinds = 0, 0, Counter()
    off = []
    for sh in SHEETS:
        beam_lines = dwg.lines(sh, layers=("1", "S-BEAM"))
        col_lines = dwg.lines(sh, layers=("S-COL.BON",))
        for pid in sorted(rel_panels):
            p = s1[pid]
            if p["sheet"] != sh:
                continue
            P = p["polygon_mm"]
            for i, e in enumerate(p.get("edges") or []):
                if e.get("support") != "BEAM":
                    continue
                a, c = P[i], P[(i + 1) % len(P)]
                ok_b, cov_b = SCQ.edge_on_lines(a, c, beam_lines, tol=3.0, min_cover=0.9)
                ok_c, cov_c = SCQ.edge_on_lines(a, c, col_lines, tol=3.0, min_cover=0.9)
                ok_m, cov_m = SCQ.edge_on_lines(a, c, beam_lines + col_lines, tol=3.0, min_cover=0.9)
                if ok_b or ok_c or ok_m:
                    on_face += 1
                    kinds["BEAM_EDGE_LINE" if ok_b else "COLUMN_OUTLINE" if ok_c else "BEAM_AND_COLUMN"] += 1
                else:
                    off_face += 1
                    off.append({"panel": pid, "edge": i, "support_ref": e.get("support_ref"),
                                "cover": round(max(cov_b, cov_c, cov_m), 3)})
    out.append({"CHECK_ID": "BO-01", "CHECK": "every released slab-panel edge S1 marks as beam-supported lies on a drawn "
                                              "member face (beam edge line or arc, or a column outline where the beam "
                                              "frames into a column), so the panel stops at the face",
                "RESULT": "PASS" if off_face == 0 else "REVIEW", "COUNT": on_face,
                "DETAIL": json.dumps(off[:10]) if off else f"{on_face} of {on_face} edges on a drawn face: "
                                                          + json.dumps(dict(sorted(kinds.items())))})
    col_ov = []
    for sh in SHEETS:
        for h, cp in dwg.columns(sh):
            cx = [x for x, _ in cp]
            cy = [y for _, y in cp]
            for pid in rel_panels:
                p = s1[pid]
                if p["sheet"] != sh:
                    continue
                a = SCQ.rect_polygon_overlap((min(cx), min(cy), max(cx), max(cy)), p["polygon_mm"],
                                             p.get("holes_mm") or [], step=10.0)
                if a > 0:
                    col_ov.append({"panel": pid, "column": h, "m2": round(a / 1e6, 4)})
    out.append({"CHECK_ID": "BO-02", "CHECK": "no released slab panel overlaps a drawn column outline (the column owns "
                                              "its footprint over the storey, S9-MC1)",
                "RESULT": "PASS" if not col_ov else "REVIEW", "COUNT": len(col_ov),
                "DETAIL": json.dumps(col_ov[:10]) if col_ov else "0 m2"})
    cc = [r for r in beam_rows if r["L_M"] and not r["UPPER_BOUND_ONLY"]]
    bad = []
    s9 = {c["COMPONENT_ID"]: json.loads(c["DIMENSIONS"]) if c["DIMENSIONS"].startswith("{") else {} for c in s9conc}
    for r in cc:
        d = s9[r["COMPONENT_ID"]]
        if d.get("cc_m") and r["L_M"] > d["cc_m"] + 1e-9:
            bad.append(r["COMPONENT_ID"])
    out.append({"CHECK_ID": "BO-03", "CHECK": "every beam length is a clear length (never longer than its centre-to-"
                                              "centre length), so beams stop at column and supporting-beam faces",
                "RESULT": "PASS" if not bad else "FAIL", "COUNT": len(cc), "DETAIL": json.dumps(bad) if bad else ""})
    corners = []
    for r in beam_rows:
        for end in ("START_SUPPORT", "END_SUPPORT"):
            sup = json.loads(r[end]) if isinstance(r[end], str) and r[end].startswith("{") else (r[end] or {})
            if "CORNER" in str(sup.get("kind")) and r["B_MM"] and r["H_MM"]:
                corners.append({"beam": r["COMPONENT_ID"], "end": end, "with": sup.get("refs"),
                                "max_m3": _r(r["B_MM"] / 1000 * r["B_MM"] / 1000 * (r["H_MM"] + r["SLAB_T_MM"]) / 1000, 6)})
    out.append({"CHECK_ID": "BO-04", "CHECK": "beam-to-beam corners with no column: both beams stop at faces, so the "
                                              "corner square is in neither (an undercount, never a double count)",
                "RESULT": "INFO", "COUNT": len(corners),
                "DETAIL": f"{len(corners)} corner ends; at most {math.fsum(c['max_m3'] for c in corners):.4f} m3 "
                          f"unowned under the larger reading"})
    out.append({"CHECK_ID": "BO-05", "CHECK": "neither reading counts slab concrete twice: TOTAL_DEPTH gives the beam "
                                              "B x H (the slab zone above it included); BELOW_SLAB gives B x (H + t); "
                                              "the panels never hold the strip over a beam (BO-01)",
                "RESULT": "PASS" if off_face == 0 else "REVIEW", "COUNT": sum(1 for r in beam_rows if r["SLAB_STRIP_M3"]),
                "DETAIL": "identity checked per beam: BELOW_SLAB - TOTAL_DEPTH = B x t x L"})
    return out, corners


# ============================================================================ D. ground beams and columns
def ground_beam_audit():
    """Each unreleased ground / strap beam: what blocks it, and whether an interpretation or new source fixes it.

    p.13 titles its sections '< 2.5 m', '< 5 m' and '> 5 m'. Read literally, a 1.5 m span satisfies both '< 2.5 m'
    and '< 5 m' (S5's 'both titles hold'); read as exclusive bands (< 2.5 / 2.5 - 5 / > 5) each length has one class.
    The length that selects the class (centre-to-centre or clear) is a second, independent reading."""
    out = []
    for name, fam in (("S5_GB", "GROUND_BEAM"), ("S5_STRAP", "STRAP_BEAM")):
        for r in _rows(F[name]):
            cc, cl = _f(r["member_centerline_length_m"]), _f(r["member_clear_concrete_length_m"])
            details = json.loads(r.get("detail_ids") or "[]") if "detail_ids" in r else []
            ws, ds = r["width_state"], r["depth_state"]
            flags = r.get("flags") or ""
            k_cc = SCQ.length_class(cc, GB_BOUNDS) if cc is not None else None
            k_cl = SCQ.length_class(cl, GB_BOUNDS) if cl is not None else None
            exterior = any("EXTERIOR" in x for x in details)
            conc_load = any("CONCENTRATED" in x for x in details)
            title_overlap = "both hold" in (r.get("why_not_resolved") or "") or (
                ds == "CANDIDATE_CONFLICT" and {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= set(details))
            basis_changes = (k_cc != k_cl) if (k_cc is not None and k_cl is not None) else None
            parts = []
            if ws == ds == "SOURCE_EXPLICIT":
                kind, need = "RELEASED_IN_S9", "nothing"
            elif ds == "BOUNDED_ABOVE":
                kind, need = "MISSING_SOURCE_INFORMATION", ("the exterior ground-beam depth: p.13 gives 'FOLLOW ARCH.' "
                                                           "and no architectural section dimensions it")
            elif fam == "STRAP_BEAM":
                kind, need = "SOURCE_CONFLICT", "the SB2 width (S1 review queue item 9)"
            elif ds == "SOURCE_CONFLICT":
                kind = "SOURCE_CONFLICT"
                need = ("an exterior annex span: the +0.30 level bound cannot hold the drawn section (S5 flag "
                        "ANNEX_DEPTH_SOURCE_CONFLICT)") if "ANNEX_DEPTH" in flags else (r.get("why_not_resolved") or ds)
            elif conc_load:
                kind, need = "MISSING_SOURCE_INFORMATION", ("a detail for spans carrying a concentrated load (the project "
                                                           "has none)")
                if exterior:
                    need += "; and whether the span is exterior"
            elif ds == "CANDIDATE_CONFLICT":
                if title_overlap:
                    parts.append("TITLE_OVERLAP")
                if basis_changes:
                    parts.append("LENGTH_BASIS")
                if exterior:
                    parts.append("EXTERIOR_OR_INTERIOR")
                kind = "INTERPRETATION_" + "_AND_".join(parts or ["DETAIL_CHOICE"])
                need = "; ".join({"TITLE_OVERLAP": "whether the p.13 titles '< 2.5 m' / '< 5 m' are exclusive bands",
                                  "LENGTH_BASIS": "which length selects the class (centre-to-centre or clear)",
                                  "EXTERIOR_OR_INTERIOR": "whether the span is exterior (FOLLOW ARCH.) or interior",
                                  "DETAIL_CHOICE": "which p.13 detail applies"}[x] for x in (parts or ["DETAIL_CHOICE"]))
            else:
                kind, need = "SOURCE_CONFLICT", r.get("why_not_resolved") or ds
            w = _f(r["width_mm"]) or (300.0 if ws == "CANDIDATE_INVARIANT" else None)
            interp = kind.startswith("INTERPRETATION") and not exterior and w and cl
            v_cc = cl * w / 1000 * GB_DEPTH[k_cc] / 1000 if interp and k_cc is not None else None
            v_cl = cl * w / 1000 * GB_DEPTH[k_cl] / 1000 if interp and k_cl is not None else None
            labels = ["< 2.5 m (30x30)", "2.5 - 5 m (30x40)", "> 5 m (30x60)"]
            out.append({"OCCURRENCE_ID": r["occurrence_id"], "FAMILY": fam, "MARK": r["mark"], "CC_M": cc,
                        "CLEAR_M": cl, "CLASS_BY_CC": labels[k_cc] if k_cc is not None else None,
                        "CLASS_BY_CLEAR": labels[k_cl] if k_cl is not None else None,
                        "CLASS_CHANGES_WITH_BASIS": basis_changes, "TITLE_OVERLAP": title_overlap,
                        "EXTERIOR_CANDIDATE": exterior, "WIDTH_STATE": ws, "DEPTH_STATE": ds, "DETAILS": details,
                        "PROBLEM_KIND": kind, "NEEDED": need,
                        "M3_EXCLUSIVE_TITLES_CC_BASIS": _r(v_cc, 6), "M3_EXCLUSIVE_TITLES_CLEAR_BASIS": _r(v_cl, 6),
                        "M3_UPPER_BOUND_EXTERIOR": _r(cl * w / 1000 * _f(r["depth_bound_max_m"]), 6)
                        if ds == "BOUNDED_ABOVE" and w and cl and _f(r.get("depth_bound_max_m")) else None})
    return out


def column_audit(dwg_texts):
    cdef = defaultdict(dict)
    for r in _j(F["S1_CDEF"])["rows"]:
        cdef[r["column_type"]][r["storey_band"]] = sorted([r["B_cm"] or r.get("W_cm"), r["D_cm"]]) if r.get("D_cm") \
            else None
    band = {"FOUNDATION": "FOUNDATION", "GF": "GF", "1F": "1F", "2F": "2F"}
    s2 = _s2()
    out = []
    for r in _j(F["S1_COCC"])["rows"]:
        if r["drawn_vs_schedule"] != "MISMATCH":
            continue
        dw = sorted(r["drawn_section_cm"]) if r["drawn_section_cm"] else None
        sc = sorted(r["schedule_section_cm"]) if r["schedule_section_cm"] else None
        same_type_rows = {k: v for k, v in cdef.get(r["column_type"], {}).items() if v}
        other_band = [k for k, v in same_type_rows.items() if v == dw and k != band.get(r["floor"])]
        other_type = sorted(t for t, rows_ in cdef.items() if t != r["column_type"]
                            and any(v == dw for k, v in rows_.items() if v and k == r["floor"]))
        thin = dw and min(dw) < 20
        if other_band:
            kind = "INTERPRETATION_SCHEDULE_STOREY_ROW"
            why = f"the drawn section equals the {r['column_type']} schedule row for {other_band}: which row applies here"
        elif other_type:
            kind = "INTERPRETATION_TYPE_TAG"
            why = f"the drawn section equals the {r['floor']} schedule of {other_type}: tag or drawing"
        elif dw and sc and dw[0] == sc[0] or dw and sc and dw[1] == sc[1]:
            kind = "GENUINE_CONFLICT_ONE_DIMENSION"
            why = "one side agrees, the other does not: drawing or schedule is wrong"
        else:
            kind = "GENUINE_CONFLICT"
            why = "no schedule row of any storey or type matches the drawn section"
        out.append({"COLUMN_ID": r["column_id"], "FLOOR": r["floor"], "TYPE": r["column_type"],
                    "DRAWN_CM": r["drawn_section_cm"], "SCHEDULE_CM": r["schedule_section_cm"],
                    "SAME_TYPE_SCHEDULE_ROWS": same_type_rows, "PROBLEM_KIND": kind, "WHY": why,
                    "BELOW_20_CM_MIN": bool(thin), "S2_STATE": s2.get(r["column_id"]),
                    "LIFT_COLUMN": r["column_id"] in LIFT_COLS,
                    "M3_SCHEDULE": None, "M3_DRAWN": None})
    h = {x["storey"]: x["floor_to_floor_m"] for x in _j(F["S1_LEVEL"])["intervals"]}
    for o in out:
        hh = h.get(o["FLOOR"])
        if hh:
            if o["SCHEDULE_CM"]:
                o["M3_SCHEDULE"] = _r(o["SCHEDULE_CM"][0] * o["SCHEDULE_CM"][1] / 1e4 * hh, 6)
            if o["DRAWN_CM"]:
                o["M3_DRAWN"] = _r(o["DRAWN_CM"][0] * o["DRAWN_CM"][1] / 1e4 * hh, 6)
    # the column tie hooks: searched in the drawing text and the S1 rules
    pat = re.compile(r"HOOK|BEND|\b135\b|R\s*=\s*\d|\d+\s*[dDØ]\s*(?:EXT|HOOK)", re.I)
    hits = [t for t in dwg_texts if pat.search(t["text"] or "")]
    rules = _j(F["S1_RULES"])["rows"]
    rule_hits = [x.get("rule_id") for x in rules if pat.search(json.dumps(x, ensure_ascii=False))]
    tie = _j(F["S31_TIE"])["tie_rule"]
    ties = {"tie_rule": tie.get("raw"), "dxf_text_hits": [{"sheet": t["sheet"], "handle": t["handle"], "text": t["text"]}
                                                          for t in hits][:20],
            "s1_rule_hits": rule_hits, "state": "MISSING_SOURCE_INFORMATION" if not hits else "REVIEW_TEXT_HITS"}
    return out, ties


LIFT_COLS = {"COL-C1-X09-Y09-FOUNDATION", "COL-C2-X09-Y07-FOUNDATION", "COL-C2-X10-Y09-FOUNDATION",
             "COL-C9-X10-Y07-FOUNDATION"}


def lift_column_audit():
    occ = {r["column_id"]: r for r in _j(F["S1_COCC"])["rows"]}
    c01 = next(r for r in _rows(F["S88_CONFLICTS"]) if r["ID"] == "C-01")
    out = []
    for cid in sorted(LIFT_COLS):
        r = occ[cid]
        out.append({"COLUMN_ID": cid, "TYPE": r["column_type"], "DRAWN_CM": r["drawn_section_cm"],
                    "SCHEDULE_CM": r["schedule_section_cm"], "PLAN_SOURCE": r["plan_source"],
                    "S8_8": f"{c01['ID']} {c01['STATE']}: {c01['WHY']}", "PROBLEM_KIND": "GENUINE_CONFLICT",
                    "NEEDED": "which governs at the pit: the drawn 200 / 250 mm (flush with the 200 mm pit walls) or "
                              "the scheduled 300 mm (Q-LIFT-08); the founding level as well (neck height)"})
    return out


# ============================================================================ E. registers
def deltas(band_rows, beam_rows):
    out = []
    for r in band_rows:
        tagged = r["OWNER_DECISION"].startswith("BEAMS")
        out.append({"DELTA_ID": f"S9A-D{len(out) + 1:03d}", "CHANGE_KIND": "BAND_REGISTERED" if not tagged else
                    "BAND_BOUND_TO_EXISTING_OWNER", "COMPONENT_ID": r["BAND_ID"], "DXF_HANDLE": r["DXF_HANDLE"],
                    "FROM_OWNER": f"{r['S9_FAMILY']} ({r['S9_COMPONENT_SAME_FOOTPRINT']}, {r['S9_LANE']})",
                    "TO_OWNER": "BEAMS (unchanged)" if tagged else "SLABS / CANTILEVER_PORTIONS",
                    "FROM_LANE": r["S9_LANE"], "TO_LANE": "EXCLUDED_OWNED_BY_OTHER_FAMILY" if tagged else
                    "BLOCKED_UNQUANTIFIED", "DELTA_M3": 0.0, "DELTA_KG": 0.0,
                    "WHY": f"the band's own plotted hatch ({r['PDF_SPACING_MODEL_MM']} mm) is the legend's "
                           f"'{r['LEGEND_MATCH']}' symbol; it lies on {r['BEAM_LINE']}'s strip, outside every slab "
                           "panel and column; thickness UNKNOWN"})
    for b in beam_rows:
        if b["S9A_STATE"].startswith("RE_OWNED"):
            out.append({"DELTA_ID": f"S9A-D{len(out) + 1:03d}", "CHANGE_KIND": "OWNERSHIP_TRANSFER",
                        "COMPONENT_ID": b["COMPONENT_ID"], "FROM_OWNER": "BEAMS (S9 untagged geometry)",
                        "TO_OWNER": "SLABS / CANTILEVER_PORTIONS (" + b["S9A_STATE"].split("(")[1],
                        "FROM_LANE": b["S9_LANE"], "TO_LANE": "SUPERSEDED (re-owned; the band row carries it)",
                        "DELTA_M3": 0.0, "DELTA_KG": 0.0,
                        "WHY": "the 'untagged beam' is the hatched cantilever portion: no tag, no schedule row, and the "
                               "legend says cantilever; counted once, as the band"})
    return out


def reconciliation(verify_tot, s9sum, band_rows, beam_tot, gb_rows, col_rows):
    rows = []
    for fam, v in sorted(s9sum["released_concrete_m3_by_family"].items()):
        rows.append({"TRADE": "CONCRETE", "FAMILY": fam, "S9_RELEASED": v, "S9A_DELTA": 0.0, "S9A_RELEASED": v,
                     "UNIT": "m3"})
    for fam, v in sorted(s9sum["released_reinforcement_kg_by_family"].items()):
        rows.append({"TRADE": "REINFORCEMENT", "FAMILY": fam, "S9_RELEASED": v, "S9A_DELTA": 0.0, "S9A_RELEASED": v,
                     "UNIT": "kg"})
    rows.append({"TRADE": "CONCRETE", "FAMILY": "TOTAL", "S9_RELEASED": s9sum["released_concrete_m3_total"],
                 "S9A_DELTA": 0.0, "S9A_RELEASED": s9sum["released_concrete_m3_total"], "UNIT": "m3",
                 "NOTE": "partial structural BOQ; not a complete building estimate"})
    rows.append({"TRADE": "REINFORCEMENT", "FAMILY": "TOTAL", "S9_RELEASED": s9sum["released_reinforcement_kg_total"],
                 "S9A_DELTA": 0.0, "S9A_RELEASED": s9sum["released_reinforcement_kg_total"], "UNIT": "kg"})
    allb = next(r for r in beam_tot if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    rows.append({"TRADE": "CONCRETE", "FAMILY": "BEAMS (conditional, never released)", "UNIT": "m3",
                 "S9A_CONDITIONAL_LOW": allb["TOTAL_DEPTH_M3"], "S9A_CONDITIONAL_HIGH": allb["BELOW_SLAB_M3"],
                 "NOTE": f"{allb['BEAMS']} beams; low = H overall, high = H below the slab"})
    rows.append({"TRADE": "CONCRETE", "FAMILY": "CANTILEVER_PORTIONS (blocked)", "UNIT": "m3",
                 "S9A_CONDITIONAL_LOW": None, "S9A_CONDITIONAL_HIGH": None,
                 "NOTE": f"{sum(1 for r in band_rows if r['CONCRETE_STATE'].startswith('BLOCKED'))} bands, "
                         f"{sum(r['AREA_M2'] for r in band_rows if r['CONCRETE_STATE'].startswith('BLOCKED')):.3f} m2; "
                         "thickness unknown (value at the adjacent slab thickness in 03, context only)"})
    gbv = [r for r in gb_rows if r["M3_EXCLUSIVE_TITLES_CC_BASIS"] is not None]
    rows.append({"TRADE": "CONCRETE", "FAMILY": "GROUND_BEAMS (p.13 title reading, never released)", "UNIT": "m3",
                 "S9A_CONDITIONAL_LOW": _r(math.fsum(min(r["M3_EXCLUSIVE_TITLES_CC_BASIS"],
                                                         r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]) for r in gbv), 6),
                 "S9A_CONDITIONAL_HIGH": _r(math.fsum(max(r["M3_EXCLUSIVE_TITLES_CC_BASIS"],
                                                          r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]) for r in gbv), 6),
                 "NOTE": f"{len(gbv)} interior spans held only by the title / length-basis reading"})
    cv = [r for r in col_rows if r["M3_SCHEDULE"] is not None and r["M3_DRAWN"] is not None]
    rows.append({"TRADE": "CONCRETE", "FAMILY": "COLUMNS (section mismatch, never released)", "UNIT": "m3",
                 "S9A_CONDITIONAL_LOW": _r(math.fsum(min(r["M3_SCHEDULE"], r["M3_DRAWN"]) for r in cv), 6),
                 "S9A_CONDITIONAL_HIGH": _r(math.fsum(max(r["M3_SCHEDULE"], r["M3_DRAWN"]) for r in cv), 6),
                 "NOTE": f"{len(cv)} mismatched GF / 1F / 2F occurrences (drawn vs schedule)"})
    return rows


def rfis_and_unlock(s9conc, s9bars, beam_tot, beam_rows, gb_rows, col_rows, band_rows, corners, ties):
    cond = defaultdict(float)
    for c in s9conc:
        if c["LANE"] not in RELEASED and c["CONDITIONAL_M3"]:
            cond[c["FAMILY"]] += float(c["CONDITIONAL_M3"])
    kg_nr = defaultdict(float)
    for b in s9bars:
        if b["LANE"] not in RELEASED and b["NOT_RELEASED_KG"] and b["LANE"] != "SUPERSEDED":
            kg_nr[b["FAMILY"]] += float(b["NOT_RELEASED_KG"])
    allb = next(r for r in beam_tot if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    c01 = math.fsum(float(b["NOT_RELEASED_KG"] or 0) for b in s9bars if b["CORRECTIONS"] == "S9-C01")
    links = -math.fsum(float(r["CORRECTION_KG"]) for p in (F["D11_S5"], F["D11_S6"]) for r in _rows(p))
    neck = math.fsum(float(c["CONDITIONAL_M3"] or 0) for c in s9conc if c["FAMILY"] == "COLUMNS" and
                     c["STOREY"] == "FOUNDATION")
    pit = math.fsum(float(c["CONDITIONAL_M3"] or 0) for c in s9conc if c["FAMILY"] == "LIFT")
    gbv = [r for r in gb_rows if r["M3_EXCLUSIVE_TITLES_CC_BASIS"] is not None]
    gb_ext = [r for r in gb_rows if r["M3_UPPER_BOUND_EXTERIOR"]]
    colv = [r for r in col_rows if r["M3_SCHEDULE"] is not None]
    sog = cond.get("GROUND_SLAB", 0.0)
    lint = cond.get("LINTELS", 0.0)
    cp = [r for r in band_rows if r["CONCRETE_STATE"].startswith("BLOCKED")]
    items = [
        ("RFI-A01", "P1", "engineer", "BEAMS", "Is the beam schedule depth H the overall depth including the slab, or the "
         "depth below the slab?", f"{allb['BEAMS']} beams", allb["TOTAL_DEPTH_M3"], allb["BELOW_SLAB_M3"], 0.0,
         "releases the conditional beam concrete under the confirmed reading (the other reading differs by "
         f"{allb['SENSITIVITY_M3']} m3)"),
        ("RFI-A02", "P1", "engineer", "COLUMNS / BEAMS / GROUND_BEAMS", "Column ties and beam links: bend radius, hook "
         "length and closure (none is printed; S9-C01 and D1.1 hold the tie and link paths conditional)",
         "288 column tie parts + D1.1 link paths", 0.0, 0.0, _r(c01 + links, 3),
         f"{c01:.3f} kg of column ties + {links:.3f} kg of ground-beam and beam links back to released kg"),
        ("RFI-A03", "P1", "engineer", "FOUNDATION", "Founding level of the footings (only 'excavation >= 1.50 m below "
         "plot level' is printed)", "36 foundation necks + lift pit walls", _r(neck + pit, 6), _r(neck + pit, 6),
         None, "fixes the neck and pit-wall heights (indicative values shown, unbounded until then); the steel effect "
               "is not quantified here (starters and laps are a separate method question)"),
        ("RFI-A04", "P1", "engineer", "COLUMNS", "For the 28 column occurrences whose drawn section differs from the "
         "schedule (22 in GF - 2F, 6 foundation necks including the 4 lift columns drawn 200 / 250 vs 300 at the pit), "
         "which governs?",
         f"{len(colv)} occurrences", _r(math.fsum(min(r["M3_SCHEDULE"], r["M3_DRAWN"] or r["M3_SCHEDULE"])
                                                for r in colv), 6),
         _r(math.fsum(max(r["M3_SCHEDULE"], r["M3_DRAWN"] or r["M3_SCHEDULE"]) for r in colv), 6), 0.0,
         "releases the column concrete of those occurrences"),
        ("RFI-A05", "P2", "engineer", "GROUND_BEAMS", "p.13 ground-beam sections: are the titles '< 2.5 m' / '< 5 m' "
         "exclusive bands, which length selects the class (centre-to-centre or clear), and what are the exterior "
         "'FOLLOW ARCH.' depths?", f"{len(gbv)} interior + {len(gb_ext)} exterior spans",
         _r(math.fsum(min(r["M3_EXCLUSIVE_TITLES_CC_BASIS"], r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]) for r in gbv), 6),
         _r(math.fsum(max(r["M3_EXCLUSIVE_TITLES_CC_BASIS"], r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]) for r in gbv) +
            math.fsum(r["M3_UPPER_BOUND_EXTERIOR"] for r in gb_ext), 6), 0.0,
         "interior spans by the title and basis readings; exterior spans need the architectural depth (upper bound "
         "shown)"),
        ("RFI-A06", "P2", "architect / engineer", "GROUND_SLAB", "Scope of the 'T=10cm, 5Ø10/m E.W.' ground-slab note "
         "beyond the two source-zoned cells, and its cover", "19 slab-on-grade faces", _r(sog, 6), _r(sog, 6),
         0.0, "releases the remaining slab-on-grade faces at 10 cm"),
        ("RFI-A07", "P2", "engineer", "LINTELS", "Lintel bearings, column connections and head functions for the "
         "lintels S8.6A blocked", "57 lintels", _r(lint, 6), _r(lint, 6), _r(kg_nr.get("LINTELS", 0.0), 3),
         "releases the lintels whose bearing / head function is confirmed"),
        ("RFI-A08", "P2", "engineer", "SLABS / CANTILEVER_PORTIONS", "Thickness (and section) of the 8 cantilever "
         "portions hatched on the slab sheets (legend 'Cantilever portion'), and their bars",
         f"{len(cp)} bands, {sum(r['AREA_M2'] for r in cp):.3f} m2",
         _r(math.fsum(r["CONDITIONAL_M3_IF_ADJACENT_SLAB_T"] or 0 for r in cp), 6), None, 0.0,
         "measurable once a thickness is stated (value at the adjacent slab thickness shown)"),
        ("RFI-A09", "P3", "engineer", "BEAMS", "Section of the 25 untagged beam spans that are not cantilever portions "
         "(no tag binds them, no schedule row)", "25 spans", None, None, 0.0,
         "measurable once a mark or section is given (clear lengths are held)"),
        ("RFI-A10", "P3", "engineer", "BEAMS", "Which beam owns the corner square where two beams meet without a column?",
         f"{len(corners)} corner ends", 0.0, _r(math.fsum(c["max_m3"] for c in corners), 6), 0.0,
         "today the squares are in neither beam (undercount)"),
    ]
    ck = Counter(r["PROBLEM_KIND"].split(" + ")[0] for r in col_rows)
    gk = Counter(r["PROBLEM_KIND"] for r in gb_rows)
    kind = {
        "RFI-A01": "INTERPRETATION (H is printed; the face it is measured from is not)",
        "RFI-A02": "MISSING_SOURCE_INFORMATION (no bend radius, hook or closure printed)",
        "RFI-A03": "MISSING_SOURCE_INFORMATION (only a minimum excavation depth is printed)",
        "RFI-A04": f"INTERPRETATION ({ck['INTERPRETATION_SCHEDULE_STOREY_ROW'] + ck['INTERPRETATION_TYPE_TAG']} "
                   "occurrences match another schedule row or type) + SOURCE_CONFLICT "
                   f"({ck['GENUINE_CONFLICT'] + ck['GENUINE_CONFLICT_ONE_DIMENSION']} match nothing)",
        "RFI-A05": f"INTERPRETATION ({sum(v for k, v in gk.items() if k.startswith('INTERPRETATION'))} spans: titles, "
                   f"length basis, exterior or interior) + MISSING_SOURCE_INFORMATION "
                   f"({gk['MISSING_SOURCE_INFORMATION']} spans: exterior depth 'FOLLOW ARCH.', concentrated-load detail)",
        "RFI-A06": "MISSING_SOURCE_INFORMATION (the note's extent is not zoned)",
        "RFI-A07": "MISSING_SOURCE_INFORMATION (bearings and head functions not drawn)",
        "RFI-A08": "MISSING_SOURCE_INFORMATION (no thickness, section or bars for the hatched portions)",
        "RFI-A09": "MISSING_SOURCE_INFORMATION (no tag, no schedule row)",
        "RFI-A10": "INTERPRETATION (an ownership rule, not a dimension)",
    }
    rfi, unlock = [], []
    for rid, pr, to, fam, q, scope, lo, hi, kg, effect in items:
        rfi.append({"RFI_ID": rid, "PRIORITY": pr, "TO": to, "FAMILY": fam, "PROBLEM_TYPE": kind[rid],
                    "QUESTION": q, "SCOPE": scope,
                    "UNLOCKS_M3_LOW": lo, "UNLOCKS_M3_HIGH": hi, "UNLOCKS_KG": kg, "EFFECT": effect,
                    "STATUS": "OPEN"})
    m3_key = {r["RFI_ID"]: (r["UNLOCKS_M3_HIGH"] if r["UNLOCKS_M3_HIGH"] is not None else r["UNLOCKS_M3_LOW"]) or 0.0
              for r in rfi}
    kg_rank = {r["RFI_ID"]: i for i, r in enumerate(sorted([r for r in rfi if r["UNLOCKS_KG"]],
                                                            key=lambda r: -r["UNLOCKS_KG"]), 1)}
    ranked = sorted(rfi, key=lambda r: (-m3_key[r["RFI_ID"]], -(r["UNLOCKS_KG"] or 0.0)))
    m3_rank = {r["RFI_ID"]: i for i, r in enumerate([r for r in ranked if m3_key[r["RFI_ID"]]], 1)}
    for r in ranked:
        unlock.append({"RANK_CONCRETE": m3_rank.get(r["RFI_ID"]), "RANK_STEEL": kg_rank.get(r["RFI_ID"]),
                       "RFI_ID": r["RFI_ID"], "PROBLEM_TYPE": r["PROBLEM_TYPE"], "QUESTION": r["QUESTION"],
                       "UNLOCKS_M3_LOW": r["UNLOCKS_M3_LOW"],
                       "UNLOCKS_M3_HIGH": r["UNLOCKS_M3_HIGH"], "UNLOCKS_KG": r["UNLOCKS_KG"], "EFFECT": r["EFFECT"],
                       "RANK_BASIS": "concrete by the upper conditional m3, steel by kg; the values are conditional "
                                     "quantities the answer would make releasable, never a promise of release"})
    return rfi, unlock


def conservation(L):
    rows = []

    def A(cid, what, ok, detail=""):
        rows.append({"CHECK_ID": cid, "CHECK": what, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    s9 = L["s9sum"]
    A("C01", "S9 and the 29 stage manifests verify before and after", True, f"{len(L['frozen'])} manifests")
    A("C02", "every released S9 family agrees with its independent recompute (rounding only)",
      all(r["RESULT"] in ("AGREES", "ROUNDING_ONLY") for r in L["verify"]),
      json.dumps([r["FAMILY"] for r in L["verify"] if r["RESULT"] not in ("AGREES", "ROUNDING_ONLY")]))
    A("C03", "S9A releases nothing: the released totals stay 158.070 m3 / 18,845.961 kg",
      all(r["S9A_DELTA"] == 0.0 for r in L["recon"] if "S9A_DELTA" in r) and
      not any(d["DELTA_M3"] or d["DELTA_KG"] for d in L["deltas"]),
      f"{s9['released_concrete_m3_total']} m3 / {s9['released_reinforcement_kg_total']} kg")
    A("C04", "exactly 8 dense-hatch (100 mm) bands on the slab sheets, 4.947 m2, each with a unique id and handle",
      len(L["bands"]) == 8 and len({b["BAND_ID"] for b in L["bands"]}) == 8 == len({b["DXF_HANDLE"] for b in L["bands"]})
      and abs(sum(b["AREA_M2"] for b in L["bands"]) - 4.94725) < 2e-4, f"{sum(b['AREA_M2'] for b in L['bands']):.4f} m2")
    A("C05", "every band matches the legend's cantilever-portion symbol, not the bearing-wall symbol",
      all(b["LEGEND_MATCH"] == "CANTILEVER_PORTION" for b in L["bands"]),
      json.dumps({b["BAND_ID"]: b["PDF_SPACING_MODEL_MM"] for b in L["bands"]}))
    A("C06", "no band overlaps a slab panel or a column; each has one owner",
      all(b["SLAB_PANEL_OVERLAP_M2"] == 0 and b["COLUMN_OVERLAP_M2"] == 0 for b in L["bands"]) and
      all(b["OWNER_DECISION"] for b in L["bands"]), "")
    A("C07", "each band coincides with exactly one S9 beam row, which held no released value (no double count)",
      all(b["S9_COMPONENT_SAME_FOOTPRINT"] and b["DOUBLE_COUNT_RISK"].startswith("none") for b in L["bands"]), "")
    A("C08", "band thickness is UNKNOWN and nothing is released for a band",
      all(b["THICKNESS_MM"].startswith("UNKNOWN") and b["RELEASED_M3"] == 0 and b["RELEASED_KG"] == 0
          for b in L["bands"]), "")
    A("C09", "150 superstructure beams compared; no beam concrete released",
      len(L["beams"]) == 150 and all(b["RELEASED_M3"] == 0 for b in L["beams"]), "")
    A("C10", "per beam: BELOW_SLAB - TOTAL_DEPTH = B x t x L (the strip), and TOTAL_DEPTH = downstand + strip",
      all(b["V_TOTAL_DEPTH_M3"] is None or (abs(b["V_BELOW_SLAB_M3"] - b["V_TOTAL_DEPTH_M3"] - b["SLAB_STRIP_M3"]) < 1e-8
                                             and abs(b["V_TOTAL_DEPTH_M3"] - b["DOWNSTAND_IF_TOTAL_DEPTH_M3"] -
                                                     b["SLAB_STRIP_M3"]) < 1e-8) for b in L["beams"]), "")
    A("C11", "a missing dimension is never zero: no volume where B, H or L is missing",
      all((b["MISSING"] is None) == (b["V_TOTAL_DEPTH_M3"] is not None) for b in L["beams"]), "")
    A("C12", "slab panels stop at drawn beam faces and never overlap a column (BO-01, BO-02)",
      all(o["RESULT"] == "PASS" for o in L["overlaps"] if o["CHECK_ID"] in ("BO-01", "BO-02", "BO-03", "BO-05")),
      json.dumps([o["CHECK_ID"] for o in L["overlaps"] if o["RESULT"] not in ("PASS", "INFO")]))
    A("C13", "every ground beam and every mismatched column has a problem kind and a need",
      all(r["PROBLEM_KIND"] and r["NEEDED"] for r in L["gb"]) and all(r["PROBLEM_KIND"] for r in L["cols"]), "")
    A("C14", "the 28 column section mismatches S9 reported are all audited",
      len(L["cols"]) == 28, json.dumps(dict(Counter(r["FLOOR"] for r in L["cols"]))))
    A("C15", "the conditional values never enter a released total",
      all(r.get("S9A_RELEASED") is None or r.get("S9A_CONDITIONAL_LOW") is None for r in L["recon"]), "")
    A("C16", "every RFI names what it would unlock; the ranking covers every RFI",
      len(L["unlock"]) == len(L["rfi"]) and all(r["EFFECT"] for r in L["rfi"]), "")
    A("C17", "the builder reads no old-BOQ, R5, R9_1, PRE-S8 data or post-freeze input",
      not [str(p) for p in F.values() if FIREWALL.search(str(p))], "")
    return rows


# ============================================================================ write
def run():
    frozen, found = frozen_manifests()
    s9conc = _rows(F["S9_CONC"])
    s9bars = _rows(F["S9_BARS"])
    s9sum = _j(F["S9_SUMMARY"])
    verify, vt = verify_s9()
    inv = verify_inventory()
    dwg = Drawing()
    pdf = PlotPDF()
    band_rows, band_summary, sunken = bands(dwg, pdf, s9conc)
    beam_rows = beams(dwg, s9conc, band_rows)
    beam_tot = beam_totals(beam_rows)
    overlaps, corners = overlap_audit(dwg, beam_rows, s9conc)
    gb = ground_beam_audit()
    texts = [dict(t, sheet=sh) for sh in ("GFRS", "FFRS", "SFRS") for t in dwg.texts(sh)]
    cols, ties = column_audit(texts)
    lift = lift_column_audit()
    by = {r["COLUMN_ID"]: r for r in cols}
    for x in lift:
        r = by[x["COLUMN_ID"]]
        r["LIFT_PIT_CONFLICT"] = x["S8_8"]
        r["PROBLEM_KIND"] = r["PROBLEM_KIND"] + " + LIFT_PIT_CONFLICT"
        r["WHY"] = r["WHY"] + "; at the pit S8.8 keeps it a conflict: " + x["NEEDED"]
    dl = deltas(band_rows, beam_rows)
    recon = reconciliation(vt, s9sum, band_rows, beam_tot, gb, cols)
    rfi, unlock = rfis_and_unlock(s9conc, s9bars, beam_tot, beam_rows, gb, cols, band_rows, corners, ties)
    L = {"frozen": frozen, "s9sum": s9sum, "verify": verify, "vt": vt, "inv": inv, "bands": band_rows,
         "band_summary": band_summary, "sunken": sunken, "beams": beam_rows, "beam_tot": beam_tot,
         "overlaps": overlaps, "corners": corners, "gb": gb, "cols": cols, "ties": ties, "lift": lift, "deltas": dl,
         "recon": recon, "rfi": rfi, "unlock": unlock, "dwg": dwg, "s9conc": s9conc, "s9inv": _rows(F["S9_INV"]),
         "F": F}
    L["cons"] = conservation(L)
    check(all(c["RESULT"] == "PASS" for c in L["cons"]),
          "conservation: " + json.dumps([c for c in L["cons"] if c["RESULT"] != "PASS"]))
    frozen2, _ = frozen_manifests()
    check(frozen2 == frozen, "a frozen manifest changed during the build")
    return L


def summary(L):
    s9 = L["s9sum"]
    allb = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"].startswith("conditional"))
    conf = next(r for r in L["beam_tot"] if r["GROUP"] == "ALL" and r["SET"] == "source conflict")
    return {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "corrects": "research/alsenan_structural_s9 (frozen; unchanged)", "references_read": [],
        "released_unchanged": {"concrete_m3": s9["released_concrete_m3_total"],
                               "reinforcement_kg": s9["released_reinforcement_kg_total"]},
        "release_delta": {"concrete_m3": 0.0, "kg": 0.0},
        "verification": {"independent_concrete_m3": _r(L["vt"]["concrete_m3"], 9),
                         "independent_kg": _r(L["vt"]["kg"], 9),
                         "families_agree": sum(1 for r in L["verify"] if r["RESULT"] == "AGREES"),
                         "readme_table_rounding_kg": next(r["PUBLISHED_MINUS_INDEPENDENT"] for r in L["verify"]
                                                          if r["FAMILY"] == "README_TABLE_3DP"),
                         "s9_c01_kg": _r(L["vt"]["c01_kg"], 6), "s9_c01_parts": L["vt"]["c01_parts"]},
        "bands": {"count": len(L["bands"]), "area_m2": _r(sum(b["AREA_M2"] for b in L["bands"]), 6),
                  "legend_match": dict(Counter(b["LEGEND_MATCH"] for b in L["bands"])),
                  "already_in_s9_as": dict(Counter(b["S9_LANE"] for b in L["bands"])),
                  "registered_blocked": sum(1 for b in L["bands"] if b["CONCRETE_STATE"].startswith("BLOCKED")),
                  "bound_to_ca": sum(1 for b in L["bands"] if b["OWNER_DECISION"].startswith("BEAMS"))},
        "beams": {"compared": len(L["beams"]), "conditional": allb["BEAMS"], "total_depth_m3": allb["TOTAL_DEPTH_M3"],
                  "below_slab_m3": allb["BELOW_SLAB_M3"], "sensitivity_m3": allb["SENSITIVITY_M3"],
                  "conflict_beams": conf["BEAMS"], "conflict_total_depth_m3": conf["TOTAL_DEPTH_M3"],
                  "conflict_below_slab_m3": conf["BELOW_SLAB_M3"],
                  "missing_dimension": sum(1 for b in L["beams"] if b["MISSING"] and
                                           not b["S9A_STATE"].startswith("RE_OWNED")),
                  "re_owned": sum(1 for b in L["beams"] if b["S9A_STATE"].startswith("RE_OWNED"))},
        "ground_beams": dict(Counter(r["PROBLEM_KIND"] for r in L["gb"])),
        "columns": dict(Counter(r["PROBLEM_KIND"] for r in L["cols"])),
        "ties": L["ties"]["state"],
        "rfis": len(L["rfi"]), "unlock_top3": [u["RFI_ID"] for u in L["unlock"][:3]],
        "unlock_steel_top": [u["RFI_ID"] for u in sorted(L["unlock"], key=lambda u: u["RANK_STEEL"] or 99)
                             if u["RANK_STEEL"]][:2],
        "gate_note": "partial structural BOQ; the project gate stays INCOMPLETE",
        "rule": "a dated correction layer: owners and lanes only, each with a reason; nothing released, nothing "
                "selected to match an old estimate",
    }


def provenance(L):
    out = []
    for b in L["bands"]:
        out.append({"id": b["BAND_ID"], "source": "ST7757.dxf", "handle": b["DXF_HANDLE"], "sheet": b["SHEET"],
                    "pdf": "ST7757.pdf", "page": b["PDF_PAGE"], "method": "legend hatch spacing from PDF vector paths"})
    for r in L["beams"]:
        out.append({"id": r["COMPONENT_ID"], "source": "S9 02 + S1 + S6 + PRE-S7 thickness", "line": r["BEAM_LINE"],
                    "stations": r["STATIONS_MM"]})
    return "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in out)


def write(L):
    from importlib import util
    spec = util.spec_from_file_location("visual_s9a", HERE / "visual_s9a.py")
    V = util.module_from_spec(spec)
    spec.loader.exec_module(V)
    s = summary(L)
    texts = {
        OUTPUTS[1]: _csv(L["verify"]), OUTPUTS[2]: _csv(L["inv"]), OUTPUTS[3]: _csv(L["bands"]),
        OUTPUTS[4]: json.dumps(L["band_summary"], indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n",
        OUTPUTS[5]: _csv(L["beams"]), OUTPUTS[6]: _csv(L["beam_tot"]), OUTPUTS[7]: _csv(L["overlaps"]),
        OUTPUTS[8]: _csv(L["gb"]), OUTPUTS[9]: _csv(L["cols"]),
        OUTPUTS[10]: _csv(L["deltas"]), OUTPUTS[11]: _csv(L["recon"]), OUTPUTS[13]: _csv(L["rfi"]),
        OUTPUTS[14]: _csv(L["unlock"]), OUTPUTS[15]: _csv(L["cons"]),
        OUTPUTS[16]: json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n", OUTPUTS[17]: provenance(L),
    }
    texts[OUTPUTS[12]] = V.completeness_report(L, s)
    texts[OUTPUTS[0]] = V.readme(L, s)
    visuals = V.build(L, s)
    for name, t in list(texts.items()) + [(f"visual/{k}", v) for k, v in visuals.items()]:
        check(not HYGIENE.search(t), f"hygiene: {name}")
    (HERE / "visual").mkdir(exist_ok=True)
    for name, t in texts.items():
        (HERE / name).write_text(t, encoding="utf-8")
    for name, t in visuals.items():
        (HERE / "visual" / name).write_text(t, encoding="utf-8")
    outs = OUTPUTS + [f"visual/{k}" for k in sorted(visuals)]
    m = {"round": ROUND, "state": "DATED_CORRECTION_LAYER", "date": DATE, "baseline": BASELINE_HEAD,
         "corrects": "research/alsenan_structural_s9 (frozen; unchanged)",
         "s9_manifest_sha256": _sha(S9_MANIFEST), "frozen_baselines": L["frozen"], "references_read": [],
         "release_delta": {"concrete_m3": 0.0, "kg": 0.0},
         "drawing_sha256": {"ST7757.dxf": _sha(ST_DXF), "ST7757.pdf": _sha(ST_PDF)},
         "inputs": {str(Path(p).relative_to(ROOT)): _sha(p) for p in sorted(set(F.values()), key=str)},
         "code": {c: _sha(ROOT / c) for c in CODE}, "outputs": {o: _sha(HERE / o) for o in outs},
         "engine_commit_stamp": f"{BASELINE_HEAD}+code:" + hashlib.sha256("".join(_sha(ROOT / c) for c in CODE)
                                                                         .encode()).hexdigest()[:16],
         "rule": "frozen before the old Urban BOQ (V3b), R5, R9_1, the PRE-S8 data registers or any post-freeze figure "
                 "is read; S9 and the frozen stages unchanged; owners and lanes only"}
    (HERE / MANIFEST_NAME).write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    DR.verify_frozen(HERE / MANIFEST_NAME, ROOT)
    return s


def main():
    L = run()
    s = write(L)
    print(json.dumps({k: s[k] for k in ("released_unchanged", "verification", "bands", "beams", "ground_beams",
                                         "columns", "ties", "unlock_top3")}, indent=1))
    print(json.dumps({c["CHECK_ID"]: c["RESULT"] for c in L["cons"]}))


if __name__ == "__main__":
    main()
