"""M1 - A USABLE BOQ (ST7757 demonstration): the frozen S1 - S9A work as a functioning, auditable planning estimate.

    python3 -I research/alsenan_m1_usable_boq/build_m1.py

1. verifies every frozen stage manifest the adapter reads (S9 and the stages S9 froze over, S9A, S8.7B, S8.3,
   S8.2A, S6, D1.1) and the benchmark firewall (no external estimate is read before the freeze);
2. runs the one-command pipeline (tools/urban_structural_boq.py) on the structural DXF and PDF, writing boq/:
   V / P / U registers, contractor BOQ, family / floor / diameter summaries, sensitivity, blockers, exceptions,
   coverage of the S9 component inventory, the drawing inventory, BOQ_REPORT.html (+ .pdf, .xlsx: git-ignored);
3. writes the M1 research record: 01 bottleneck diagnosis, 02 beam conventions, 03 detection coverage of the
   drawing's layers, 04 automation audit, 05 usability record, 06 the freeze manifest.

Nothing here changes a frozen stage or the verified release (158.070256 m3 / 18,845.961347 kg). Every provisional
number is reversible: change conventions_alsenan.json or pass --set to the CLI.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_adapter as A                               # noqa: E402
from engine.source import delta_release as DR             # noqa: E402
from engine.source import provisional_estimate as PE      # noqa: E402
from tools import urban_structural_boq as CLI             # noqa: E402

AS_OF = "2026-10-10"
BY_SHA = ROOT / "data" / "inputs" / "by_sha256"
ST_DXF = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ST_PDF = BY_SHA / "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
CONV = HERE / "conventions_alsenan.json"
BOQ = HERE / "boq"
MANIFEST_NAME = "06_M1_FREEZE_MANIFEST.json"
VERIFIED_M3, VERIFIED_KG = 158.070256, 18845.961347
# never read before the freeze (benchmark firewall)
FORBIDDEN_INPUT = re.compile(r"registers_v3b|alsenan_arch_truth_05|R9_1|pre_s8_structural_completeness|post_freeze|"
                             r"multi_engine|freelancer|christiannp|U-C4N|u_c4n", re.I)
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
CODE = ["engine/source/provisional_estimate.py", "engine/source/drawing_inventory.py",
        "engine/source/profile_takeoff.py", "engine/source/structural_qto.py",
        "engine/source/quantity_scenarios.py", "engine/boq_m1_xlsx.py", "engine/boq_rc1_xlsx.py",
        "tools/urban_structural_boq.py", "tools/m1_report.py",
        "research/alsenan_m1_usable_boq/alsenan_adapter.py", "research/alsenan_m1_usable_boq/build_m1.py"]
NOT_FROZEN = ("STRUCTURAL_BOQ.xlsx", "BOQ_REPORT.pdf", "run_log.json")


class BuildError(RuntimeError):
    pass


def check(cond, msg):
    if not cond:
        raise BuildError(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ============================================================================ 1. integrity
def frozen():
    """The adapter's stage manifests, plus every stage manifest S9 froze over (found by the sha256 S9 recorded)."""
    out = A.verify_frozen()
    m = _j(A.S9 / "16_S9_FREEZE_MANIFEST.json")
    want = {v: k for k, v in m["frozen_baselines"].items()}
    found = {}
    for p in sorted((ROOT / "research").glob("*/*.json")):
        h = _sha(p)
        if h in want:
            DR.verify_frozen(p, ROOT)
            found[want[h]] = str(p.relative_to(ROOT))
    check(set(found) == set(m["frozen_baselines"]), "a stage manifest S9 froze over is missing or changed")
    return sorted(set(out) | set(found.values()))


def firewall():
    ins = [str(p.relative_to(ROOT)) for p in A.PATHS.values()] + [str(p.relative_to(ROOT)) for p in
                                                                  A.FROZEN_MANIFESTS]
    bad = [p for p in ins if FORBIDDEN_INPUT.search(p)]
    check(not bad, f"benchmark firewall: {bad}")
    return sorted(ins)


# ============================================================================ 3. the research record
def _sum(items, **kw):
    sel = [i for i in items if all(i[k] == v if not isinstance(v, tuple) else i[k] in v for k, v in kw.items())]
    return {"n": len(sel), "m3_base": sum(i["base"] or 0 for i in sel if i["trade"] == "CONCRETE"),
            "m3_low": sum(i["low"] or 0 for i in sel if i["trade"] == "CONCRETE"),
            "m3_high": sum(i["high"] or 0 for i in sel if i["trade"] == "CONCRETE"),
            "kg_base": sum(i["base"] or 0 for i in sel if i["trade"] == "REINFORCEMENT"),
            "kg_high": sum(i["high"] or 0 for i in sel if i["trade"] == "REINFORCEMENT"),
            "exposure_m3_high": sum(i["exposure_high"] or 0 for i in sel if i["trade"] == "CONCRETE")}


def _by_family(items, **kw):
    fam = sorted({i["family"] for i in items})
    out = {}
    for f in fam:
        s = _sum(items, family=f, **kw)
        if s["n"]:
            out[f] = {k: round(v, 6) for k, v in s.items()}
    return out


MANUAL_APPROVAL = {
    "RELEASE_RULE_APPROVAL": "columns whose drawn section equals the schedule, held only by S2's PROVISIONAL "
                             "minimum-thickness state (5 GF columns among them)",
    "NOTE_SCOPE": "19 slab-on-grade faces: the printed note 'T=10cm, 5D10/m E.W.' applies; only its scope needs a yes",
    "BEARING_NOT_CONFIRMED": "lintels S8.6A modelled; release waits for a bearing confirmation",
    "TIE_LINK_HOOK_RULE": "beam / ground-beam links and column ties fully modelled; D1.1 retracted them because hooks "
                          "and bend radius are not printed (an authority rule, not missing geometry)",
    "LAP_ANCHORAGE_RULE": "column laps, anchorages and starters modelled with the printed rule; release waits for "
                          "approval of that rule",
}
NEVER_DETECTED = [
    {"WHAT": "8 hatched cantilever portions (bands)", "FOUND_BY": "S9A (after S1 - S9)",
     "M1": "7 PROVISIONAL at the 16 cm project default; the 8th is CA's own hatch, counted in the CA beam"},
    {"WHAT": "10 beam-to-beam corner squares", "FOUND_BY": "S9A BO-04", "M1": "one PROVISIONAL item"},
    {"WHAT": "link and tie hooks of beams and ground beams", "FOUND_BY": "excluded by every link model (S5.1, S6.1)",
     "M1": "PROVISIONAL hook allowance (LINK_HOOK_ALLOWANCE_MM)"},
    {"WHAT": "the deeper-section reading of overlapping p.13 ground-beam titles", "FOUND_BY": "S9A",
     "M1": "the high end of the ground-beam ranges"},
]


def diagnosis(R, det):
    items = R["items"]
    gaps = sorted(r["LAYER"] for r in det if r["DETECTION_GAP"] == "YES")
    never = NEVER_DETECTED + [{"WHAT": f"drawn layers with geometry that no stage's code names: {len(gaps)} "
                                       f"({', '.join(gaps) or 'none'})", "FOUND_BY": "M1 drawing inventory (03)",
                               "M1": "listed as detection gaps; not measured"}]
    bl = PE.blockers(items)
    conc = sorted([b for b in bl if b["M3_UPPER"] > 0], key=lambda b: (-b["M3_UPPER"], b["BLOCKER"]))[:5]
    steel = sorted([b for b in bl if b["KG_UPPER"] > 0], key=lambda b: (-b["KG_UPPER"], b["BLOCKER"]))[:5]
    manual = []
    for k, why in MANUAL_APPROVAL.items():
        s = _sum(items, blocker=k, category="PROVISIONAL")
        manual.append({"BLOCKER": k, "WHY_IT_IS_ONLY_APPROVAL": why, "N_ITEMS": s["n"],
                       "M3_BASE": round(s["m3_base"], 6), "KG_BASE": round(s["kg_base"], 6)})
    d = {
        "as_of": AS_OF,
        "A_fully_measured_VERIFIED": _by_family(items, category="VERIFIED"),
        "B_calculated_blocked_only_by_a_convention_or_approval":
            _by_family(items, category="PROVISIONAL", support=("CONVENTION_ONLY", "FROZEN_STAGE_MODEL")),
        "C_incomplete_geometry_one_assumed_dimension":
            _by_family(items, category="PROVISIONAL", support="ONE_ASSUMED_DIMENSION"),
        "D_no_defensible_geometry_UNRESOLVED": _by_family(items, category="UNRESOLVED"),
        "E_never_detected_by_S1_S9": never,
        "F_depending_on_manual_approval": manual,
        "G_five_biggest_causes_concrete": [{k: b[k] for k in ("BLOCKER", "PROVISIONAL_M3_BASE", "M3_UPPER",
                                                               "N_PROVISIONAL", "N_UNRESOLVED", "FAMILIES")}
                                           for b in conc],
        "G_five_biggest_causes_steel": [{k: b[k] for k in ("BLOCKER", "PROVISIONAL_KG_BASE", "KG_UPPER",
                                                            "N_PROVISIONAL", "N_UNRESOLVED", "FAMILIES")}
                                        for b in steel],
        "H_pipeline_parts_that_run_on_a_new_villa": "see 04_AUTOMATION_AUDIT.csv",
    }
    return d


def diagnosis_md(d, R):
    s = R["summary"]
    C, S = s["totals"]["CONCRETE"], s["totals"]["REINFORCEMENT"]
    L = ["# 01 Bottleneck diagnosis", "",
         "Why the strict release stops at 158.070 m3 and 18,845.961 kg, and what the rest is waiting for. Every "
         "figure is a sum over the M1 item registers (`boq/`).", "",
         "| Category | Items | Concrete m3 (base) | Reinforcement kg (base) |", "|---|---:|---:|---:|"]
    for key, label in (("A_fully_measured_VERIFIED", "A. Fully measured (VERIFIED)"),
                       ("B_calculated_blocked_only_by_a_convention_or_approval",
                        "B. Calculated; blocked only by a convention or an approval"),
                       ("C_incomplete_geometry_one_assumed_dimension", "C. Incomplete geometry (one assumed dimension)"),
                       ("D_no_defensible_geometry_UNRESOLVED", "D. No defensible geometry (UNRESOLVED)")):
        n = sum(v["n"] for v in d[key].values())
        m3 = sum(v["m3_base"] for v in d[key].values())
        kg = sum(v["kg_base"] for v in d[key].values())
        L.append(f"| {label} | {n} | {m3:,.3f} | {kg:,.1f} |" if not key.startswith("D") else
                 f"| {label} | {n} | none (exposure up to {sum(v['exposure_m3_high'] for v in d[key].values()):,.1f}"
                 " m3, not added) | none |")
    L += ["", f"Planning estimate: concrete {C['PLANNING_BASE']:,.3f} m3 (range {C['PLANNING_LOW']:,.3f} to "
              f"{C['PLANNING_HIGH']:,.3f}); reinforcement {S['PLANNING_BASE']:,.1f} kg (range "
              f"{S['PLANNING_LOW']:,.1f} to {S['PLANNING_HIGH']:,.1f}).", "",
          "## The five biggest causes of missing concrete", "",
          "| Blocker | Provisional m3 (base) | Upper m3 | Provisional items | Unresolved items | Families |",
          "|---|---:|---:|---:|---:|---|"]
    for b in d["G_five_biggest_causes_concrete"]:
        L.append(f"| {b['BLOCKER']} | {b['PROVISIONAL_M3_BASE']:,.3f} | {b['M3_UPPER']:,.3f} | {b['N_PROVISIONAL']} | "
                 f"{b['N_UNRESOLVED']} | {', '.join(b['FAMILIES'])} |")
    L += ["", "## The five biggest causes of missing reinforcement", "",
          "| Blocker | Provisional kg (base) | Upper kg | Provisional items | Unresolved items | Families |",
          "|---|---:|---:|---:|---:|---|"]
    for b in d["G_five_biggest_causes_steel"]:
        L.append(f"| {b['BLOCKER']} | {b['PROVISIONAL_KG_BASE']:,.1f} | {b['KG_UPPER']:,.1f} | {b['N_PROVISIONAL']} | "
                 f"{b['N_UNRESOLVED']} | {', '.join(b['FAMILIES'])} |")
    L += ["", "Unresolved reinforcement has no exposure figure: no bar model exists for it, and M1 uses no kg/m3 "
              "ratio.", "", "## Held only by a manual approval", "",
          "These quantities are fully modelled. What holds them is an approval or an authority rule, not geometry.",
          "", "| Blocker | Items | m3 | kg | Why it is only an approval |", "|---|---:|---:|---:|---|"]
    for m in d["F_depending_on_manual_approval"]:
        L.append(f"| {m['BLOCKER']} | {m['N_ITEMS']} | {m['M3_BASE']:,.3f} | {m['KG_BASE']:,.1f} | "
                 f"{m['WHY_IT_IS_ONLY_APPROVAL']} |")
    L += ["", "## Never detected by S1 - S9", "", "| What | Found by | In M1 |", "|---|---|---|"]
    for n in d["E_never_detected_by_S1_S9"]:
        L.append(f"| {n['WHAT']} | {n['FOUND_BY']} | {n['M1']} |")
    L += ["", "## What runs automatically on a new villa", "",
          "See `04_AUTOMATION_AUDIT.csv`. In short, the inventory, the provisional estimating layer, the checks, the "
          "exception report, the Excel workbook and the PDF run on any DXF. Footings and columns are measured "
          "live once a person confirms a profile (layers, tags, sheets, schedule rows, storey heights). Beams, "
          "slabs, ground beams, stairs and every bar schedule still need the S1-type census and the per-family "
          "stages. Those stages are written for this drawing: hard-coded inserts, layers, tag patterns and a "
          "hand-transcribed rule set. On a new villa those families come out UNRESOLVED, with the tag evidence "
          "the inventory found.", ""]
    return "\n".join(L) + "\n"


def beam_conventions(R):
    """Section 3: beam totals under both readings, the gaps and their reasons, slab overlap / intersections /
    ownership (read from S9A 05 - 07 and the M1 items)."""
    T = A.load()
    items = {i["component_id"]: i for i in R["items"] if i["family"] == "BEAMS" and i["trade"] == "CONCRETE"}
    rows, agg = [], defaultdict(lambda: {"n": 0, "A": 0.0, "B": 0.0, "n_unmeasurable": 0, "why": Counter()})
    for b in T["S9A_BEAMS"]:
        st = b["S9A_STATE"]
        grp = ("RELEASED" if st.startswith("RELEASED") else "RE_OWNED_TO_BAND" if st.startswith("RE_OWNED") else
               "CONDITIONAL" if st.startswith(("CONDITIONAL", "BAND_IS")) else
               "CURVED_UPPER_BOUND" if st.startswith("UPPER") else
               "SOURCE_CONFLICT" if st == "SOURCE_CONFLICT" and b["V_TOTAL_DEPTH_M3"] else "UNMEASURABLE")
        a, bb = (float(b["V_TOTAL_DEPTH_M3"]) if b["V_TOTAL_DEPTH_M3"] else None,
                 float(b["V_BELOW_SLAB_M3"]) if b["V_BELOW_SLAB_M3"] else None)
        g = agg[grp]
        g["n"] += 1
        if grp in ("CONDITIONAL", "CURVED_UPPER_BOUND", "SOURCE_CONFLICT", "RELEASED") and a is not None:
            g["A"] += a
            g["B"] += bb
        if grp == "UNMEASURABLE":
            g["n_unmeasurable"] += 1
            g["why"][b["MISSING"] or st] += 1
        it = items.get(b["COMPONENT_ID"])
        rows.append({"COMPONENT_ID": b["COMPONENT_ID"], "STOREY": b["STOREY"], "GROUP": grp, "S9A_STATE": st,
                     "B_MM": b["B_MM"], "H_MM": b["H_MM"], "L_M": b["L_M"], "SLAB_T_MM": b["SLAB_T_MM"],
                     "CONVENTION_A_TOTAL_DEPTH_M3": a, "CONVENTION_B_BELOW_SLAB_M3": bb,
                     "DIFFERENCE_M3": (bb - a) if a is not None else None,
                     "WHY_UNMEASURABLE": (b["MISSING"] or st) if grp == "UNMEASURABLE" else "",
                     "M1_ITEM": it["item_id"] if it else ("in the band items" if grp == "RE_OWNED_TO_BAND" else ""),
                     "M1_CATEGORY": it["category"] if it else ""})
    tot = {k: {"N": v["n"], "CONVENTION_A_M3": round(v["A"], 6), "CONVENTION_B_M3": round(v["B"], 6),
               "DIFFERENCE_M3": round(v["B"] - v["A"], 6), "N_UNMEASURABLE": v["n_unmeasurable"],
               "WHY": dict(sorted(v["why"].items()))} for k, v in sorted(agg.items())}
    ov = {r["CHECK_ID"]: {"RESULT": r["RESULT"], "DETAIL": r["DETAIL"]} for r in T["S9A_OVERLAP"]}
    measurable = [k for k in ("CONDITIONAL", "CURVED_UPPER_BOUND", "SOURCE_CONFLICT")]
    summary = {
        "beams_in_S9A_05": sum(v["N"] for v in tot.values()), "groups": tot,
        "convention_A_total_m3": round(sum(tot[k]["CONVENTION_A_M3"] for k in measurable if k in tot), 6),
        "convention_B_total_m3": round(sum(tot[k]["CONVENTION_B_M3"] for k in measurable if k in tot), 6),
        "still_unmeasurable": tot.get("UNMEASURABLE", {}).get("N", 0),
        "corner_squares_m3_reading_B": next((i["high"] for i in R["items"] if i["item_id"] ==
                                             "P-C:BEAM-CORNER-SQUARES"), None),
        "slab_overlap_and_intersections": ov,
        "ownership": "7 S9 beam spans re-owned by S9A to the cantilever bands (counted once, in CANTILEVER_PORTIONS); "
                     "CA's band is CA's own hatch (counted in the CA beam); slab panels stop at the drawn beam faces "
                     "(BO-01), so the B x t strip under reading B is in no slab panel",
        "m1_base_reading": "TOTAL_DEPTH (convention A); B is the high end of every beam item",
    }
    summary["difference_m3"] = round(summary["convention_B_total_m3"] - summary["convention_A_total_m3"], 6)
    return rows, summary


S1_STAGE_SOURCES = ("research/external_engine_lab", "research/alsenan_structural_s9a",
                    "research/alsenan_structural_census_s1")


def detection(R):
    """03: every drawing layer, whether any stage's code names it, and what it holds."""
    inv = R["inventories"][0]
    src = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                    for d in ("research", "engine/source") for p in sorted((ROOT / d).rglob("*.py"))
                    if "alsenan_m1_usable_boq" not in str(p))
    rows = []
    for lay in inv["layers"]:
        n = lay["layer"]
        if len(n) < 3:
            read = "UNDETERMINED (name too short to search for)"
        else:
            read = "NAMED_IN_STAGE_CODE" if (f'"{n}"' in src or f"'{n}'" in src) else "NOT_NAMED_BY_ANY_STAGE"
        geom = lay["closed_rectangles"] + lay["by_type"].get("HATCH", 0) + lay["closed_curved_outlines"]
        rows.append({"LAYER": n, "ROLE_GUESS": lay["role_guess"], "N_ENTITIES": lay["n_entities"],
                     "BY_TYPE": json.dumps(lay["by_type"], sort_keys=True), "CLOSED_RECTANGLES":
                     lay["closed_rectangles"], "HATCHES": lay["by_type"].get("HATCH", 0), "TEXTS": lay["texts"],
                     "READ_BY_A_STAGE": read,
                     "DETECTION_GAP": "YES" if read == "NOT_NAMED_BY_ANY_STAGE" and geom else ""})
    return rows


AUTOMATION = [
    ("1 accept DXF / PDF", "tools/urban_structural_boq.py accept()", "GENERIC", "YES", "none"),
    ("2 inventory sheets, layers, tags, outlines", "engine/source/drawing_inventory.py", "GENERIC", "YES",
     "none; role guesses are UNCONFIRMED"),
    ("3a census of footings and columns (outlines, tags, schedule binding)", "engine/source/profile_takeoff.py "
     "(structural_qto rectangles / associate / size_check)", "GENERIC + PROFILE", "PARTIAL",
     "a person confirms the profile: layers, tag pattern, sheets, storey heights, schedule rows"),
    ("3b census of beams, slabs, ground beams, stairs, lintels, domes, lift, pool",
     "research/external_engine_lab/alsenan_structural_s1.py + stage builders S4 - S8.8", "PROJECT_SPECIFIC", "NO",
     "the S1-type census and each family stage are written for this drawing (inserts, layers, tag regexes, DXF path)"),
    ("3c schedule tables", "engine/source/schedule_table.py (reader) + per-project table regions", "GENERIC READER, "
     "PROJECT REGIONS", "PARTIAL", "table regions and header bands per drawing; M1's profile takes typed rows"),
    ("3d printed rules (cover, laps, mesh notes)", "research rules_s1.py (hand transcription)", "MANUAL", "NO",
     "rules are transcribed from the PDF by hand"),
    ("4 supported quantities", "engine/source/structural_qto.py, structural_schedule.py, stage engines", "GENERIC",
     "PARTIAL", "footings and columns only on a new villa"),
    ("5 provisional conventions", "engine/source/provisional_estimate.py + a convention JSON", "GENERIC", "YES",
     "a convention set per project (the ST7757 set is a template)"),
    ("6 checks: one owner, order, unresolved apart", "provisional_estimate.check / quantity_scenarios", "GENERIC",
     "YES", "none"),
    ("6 missing components and overlaps", "profile_takeoff exceptions; S9A-type overlap audit", "GENERIC (outline "
     "level) / PROJECT (S9A)", "PARTIAL", "outline-level only on a new villa"),
    ("7 BOQ, registers, exception report", "tools/urban_structural_boq.py", "GENERIC", "YES", "none"),
    ("8 Excel and PDF", "engine/boq_m1_xlsx.py, tools/m1_report.py, Chromium", "GENERIC", "YES", "none"),
    ("strict verified release", "S1 - S9 stage gates + human review", "PROJECT + MANUAL", "NO",
     "release needs the stage review; M1 never releases"),
]


def usability(R, det, cov, beams_sum):
    s = R["summary"]
    items = R["items"]
    C, S = s["totals"]["CONCRETE"], s["totals"]["REINFORCEMENT"]
    fam = {}
    for r in R["family"]:
        if r["trade"] != "CONCRETE":
            continue
        pb = r["PLANNING_BASE"]
        fam[r["family"]] = {"verified_share_of_planning_base": round(r["VERIFIED"] / pb, 6) if pb else None,
                            "planning_base_m3": round(pb, 6), "n_verified": r["N_VERIFIED"],
                            "n_provisional": r["N_PROVISIONAL"], "n_unresolved": r["N_UNRESOLVED"]}
    covc = Counter(r["M1"] for r in cov)
    return {
        "as_of": AS_OF, "route": s["route"], "inputs": [{k: i[k] for k in ("file", "kind", "sha256")}
                                                      for i in s["inputs"]],
        "runtime": "measured per run in boq/run_log.json (not frozen: it varies with the machine); see TEST_RUN.md",
        "manual_interventions_during_the_run": 0,
        "manual_work_embodied_in_the_inputs": "the frozen S1 - S9A stages (census, rule transcription, reviews) that "
                                              "route A replays; on a new villa, the profile a person confirms",
        "detection_coverage": {
            "s9_component_records": len(cov), "by_m1_disposition": dict(sorted(covc.items())),
            "missing_from_m1": covc.get("MISSING", 0),
            "drawing_layers": len(det), "layers_with_geometry_no_stage_names": sorted(
                r["LAYER"] for r in det if r["DETECTION_GAP"] == "YES")},
        "completeness_by_family_concrete": fam,
        "verified_vs_provisional": {
            "concrete_m3": {"verified": C["VERIFIED"], "provisional_base": C["PROVISIONAL_BASE"],
                            "planning_base": C["PLANNING_BASE"], "planning_low": C["PLANNING_LOW"],
                            "planning_high": C["PLANNING_HIGH"]},
            "rc_concrete_m3": s["concrete_rc"], "plain_concrete_m3": s["plain_concrete"],
            "reinforcement_kg": {"verified": S["VERIFIED"], "provisional_base": S["PROVISIONAL_BASE"],
                                 "planning_base": S["PLANNING_BASE"], "planning_low": S["PLANNING_LOW"],
                                 "planning_high": S["PLANNING_HIGH"]}},
        "unresolved": {"concrete_items": C["N_UNRESOLVED"], "reinforcement_items": S["N_UNRESOLVED"],
                       "concrete_exposure_m3_not_added": [C["UNRESOLVED_EXPOSURE_LOW"], C["UNRESOLVED_EXPOSURE_HIGH"]],
                       "concrete_items_with_exposure": C["N_UNRESOLVED_WITH_EXPOSURE"]},
        "beams": {k: beams_sum[k] for k in ("convention_A_total_m3", "convention_B_total_m3", "difference_m3",
                                             "still_unmeasurable")},
        "independent_benchmark": "NONE before the freeze. The post-freeze comparison (post_freeze/) classifies "
                                 "discrepancies against external estimates; none is an independent measured truth, "
                                 "so no accuracy percentage is claimed",
        "blind_test_on_a_different_villa": "NOT RUN: no second permitted villa dataset exists in this repository "
                                           "(data/inputs/by_sha256 holds only this project's drawings). The new-villa "
                                           "route is exercised on a synthetic drawing in tests/m1_usable_boq",
        "new_villa_without_repeating_S1_S9": "PARTIAL. Inventory, footings and columns (with a confirmed profile), "
                                             "conventions, checks, exceptions, Excel and PDF run in one command. "
                                             "Beams, slabs, ground beams, stairs and reinforcement would still need "
                                             "the S1-type census and the family stages, which are specific to this "
                                             "drawing",
        "n_items": len(items),
    }


def readme(R, d, beams_sum, use):
    s = R["summary"]
    C, S, RC, PL = (s["totals"]["CONCRETE"], s["totals"]["REINFORCEMENT"], s["concrete_rc"], s["plain_concrete"])
    t = lambda x: f"{x:,.3f}"                                                          # noqa: E731
    return f"""# M1 - a usable structural BOQ (ST7757 demonstration)

M1 adds a **provisional estimating layer** beside the strict verified release. It does not discard S1 - S9A or
change them: every frozen stage manifest verifies before the estimate is built, and the verified release is exactly
S9's (158.070256 m3 / 18,845.961347 kg). The gate stays INCOMPLETE. Nothing here is engineering approval.

## The planning estimate

| | Verified | Provisional (base) | Planning low | **Planning base** | Planning high | Unresolved items |
|---|---:|---:|---:|---:|---:|---:|
| Reinforced concrete, m3 | {t(RC['VERIFIED'])} | {t(RC['PROVISIONAL_BASE'])} | {t(RC['PLANNING_LOW'])} | **{t(RC['PLANNING_BASE'])}** | {t(RC['PLANNING_HIGH'])} | {RC['N_UNRESOLVED']} |
| Plain concrete (blinding), m3 | {t(PL.get('VERIFIED', 0))} | {t(PL.get('PROVISIONAL_BASE', 0))} | {t(PL.get('PLANNING_LOW', 0))} | **{t(PL.get('PLANNING_BASE', 0))}** | {t(PL.get('PLANNING_HIGH', 0))} | {PL.get('N_UNRESOLVED', 0)} |
| Reinforcement, kg | {S['VERIFIED']:,.1f} | {S['PROVISIONAL_BASE']:,.1f} | {S['PLANNING_LOW']:,.1f} | **{S['PLANNING_BASE']:,.1f}** | {S['PLANNING_HIGH']:,.1f} | {S['N_UNRESOLVED']} |

- **Planning = verified + provisional base.** Each provisional item holds one reading as its base and the
  alternatives as its range; exclusive readings are never added together.
- **Low and high** add each item's own low and high. They are a bracket, not a probability.
- **Unresolved items are in no total.** That is {C['N_UNRESOLVED']} concrete items, {C['N_UNRESOLVED_WITH_EXPOSURE']}
  of them with an indicative exposure of {C['UNRESOLVED_EXPOSURE_LOW']:,.1f} to {C['UNRESOLVED_EXPOSURE_HIGH']:,.1f}
  m3, and {S['N_UNRESOLVED']} reinforcement items with no bar model. The planning estimate is not complete.
- **Beams** (150 in S9A 05): {beams_sum['convention_A_total_m3']:,.3f} m3 under convention A (H includes the slab),
  {beams_sum['convention_B_total_m3']:,.3f} m3 under convention B (H below the slab), difference
  {beams_sum['difference_m3']:,.3f} m3. {beams_sum['still_unmeasurable']} spans are still unmeasurable. M1's base is A,
  and B is each beam's high end (`02_BEAM_CONVENTIONS.*`).

## Run it

```
python3 -I tools/urban_structural_boq.py run --drawings <ST.dxf> <ST.pdf> --out OUT [--set ID=VALUE ...]
python3 -I tools/urban_structural_boq.py run --drawings NEW.dxf --profile NEW_PROFILE.json --out OUT
python3 -I tools/urban_structural_boq.py inventory --drawings NEW.dxf --out OUT   # writes PROFILE_TEMPLATE.json
python3 -I research/alsenan_m1_usable_boq/build_m1.py                             # this package
```

`--set` changes one assumption, for example `--set BEAM_DEPTH_READING=BELOW_SLAB` or `--set FOUNDING_DEPTH_M=2.0`.
The estimate, the workbook and the PDF are regenerated, and the change is recorded in `SUMMARY.json`.

## Contents

| File | What |
|---|---|
| `conventions_alsenan.json` | Every assumption: base, alternatives, provenance, source, rationale |
| `alsenan_adapter.py` | The frozen S1 - S9A registers as VERIFIED / PROVISIONAL / UNRESOLVED items (route A) |
| `boq/` | The one-command run on ST7757: `VERIFIED_` / `PROVISIONAL_` / `UNRESOLVED_REGISTER.csv`, `CONTRACTOR_BOQ.csv`, `FAMILY_` / `FLOOR_SUMMARY.csv`, `STEEL_BY_DIAMETER.csv`, `SENSITIVITY.csv`, `BLOCKERS.csv`, `EXCEPTIONS.csv`, `COVERAGE.csv`, `ASSUMPTIONS.csv`, `INVENTORY.json`, `BOQ_REPORT.html`. Also `STRUCTURAL_BOQ.xlsx` and `BOQ_REPORT.pdf`, which are git-ignored |
| `01_BOTTLENECK_DIAGNOSIS.md` / `.json` | Measured, convention-blocked, incomplete, undetected, approval-only; the five biggest causes |
| `02_BEAM_CONVENTIONS.csv` / `.json` | Beam totals under A and B, the gaps with their reasons, overlap and ownership |
| `03_LAYER_DETECTION.csv` | Every drawing layer and whether any stage reads it |
| `04_AUTOMATION_AUDIT.csv` | Which pipeline steps run on a new villa |
| `05_USABILITY.json` | Coverage, completeness by family, verified vs provisional, unresolved, the new-villa answer |
| `06_M1_FREEZE_MANIFEST.json` | sha256 of the code, the inputs and every frozen output |
| `post_freeze/` | The external-estimate reconciliation, written after the freeze |

## Limits

- **Route A replays; it does not re-measure.** It runs on the frozen stage registers of this drawing, so it is not
  evidence that the extraction generalises.
- **New villas are only partly covered.** Route B measures footings and columns live, once a person confirms a
  profile. Every other family comes out UNRESOLVED (`05_USABILITY.json`).
- **No blind test on a second villa.** No permitted dataset exists, so no accuracy figure is claimed.
- **Steel ranges are narrow** wherever a frozen bar model exists. The model is taken as is: laps, anchorages and
  starters follow its printed rules, and only the hook allowance is varied.
"""


def write():
    fz = frozen()
    ins = firewall()
    check(ST_DXF.exists() and ST_PDF.exists(), "the structural DXF / PDF are not in data/inputs/by_sha256")
    R = CLI.compute([str(ST_DXF), str(ST_PDF)], conventions=str(CONV.relative_to(ROOT)))
    s = R["summary"]
    check(s["route"] == "A_FROZEN_STAGE_REPLAY", "the ST7757 set must take route A")
    tot = s["totals"]
    check(abs(tot["CONCRETE"]["VERIFIED"] - VERIFIED_M3) < 1e-6, "verified concrete differs from S9")
    check(abs(tot["REINFORCEMENT"]["VERIFIED"] - VERIFIED_KG) < 1e-6, "verified steel differs from S9")
    check(not [r for r in R["coverage"] if r["M1"] == "MISSING"], "an S9 record has no M1 disposition")
    res = CLI.write_all(R, BOQ, as_of=AS_OF, pdf=True, xlsx=True)
    det = detection(R)
    d = diagnosis(R, det)
    brows, bsum = beam_conventions(R)
    use = usability(R, det, R["coverage"], bsum)
    out = {
        "00_README.md": readme(R, d, bsum, use),
        "01_BOTTLENECK_DIAGNOSIS.json": CLI._jdump(d), "01_BOTTLENECK_DIAGNOSIS.md": diagnosis_md(d, R),
        "02_BEAM_CONVENTIONS.csv": CLI.csv_text(brows), "02_BEAM_CONVENTIONS.json": CLI._jdump(bsum),
        "03_LAYER_DETECTION.csv": CLI.csv_text(det),
        "04_AUTOMATION_AUDIT.csv": CLI.csv_text([dict(zip(("STEP", "MODULE", "KIND", "RUNS_ON_A_NEW_VILLA",
                                                           "MANUAL_WORK"), a)) for a in AUTOMATION]),
        "05_USABILITY.json": CLI._jdump(use),
    }
    for k, v in out.items():
        (HERE / k).write_text(v, encoding="utf-8")
    outputs = {k: _sha(HERE / k) for k in sorted(out)}
    outputs.update({f"boq/{k}": _sha(BOQ / k) for k in sorted(res["files"])})
    for k in outputs:
        txt = (HERE / k).read_text(encoding="utf-8")
        check(not HYGIENE.search(txt), f"hygiene: {k}")
    man = {"round": "M1", "as_of": AS_OF, "kind": "PROVISIONAL_ESTIMATING_LAYER (no release, no stage change)",
           "code": {c: _sha(ROOT / c) for c in CODE},
           "inputs": {i: _sha(ROOT / i) for i in ins + ["research/alsenan_m1_usable_boq/conventions_alsenan.json"]},
           "outputs": outputs, "frozen_manifests_verified": fz, "references_read": [],
           "not_frozen": list(NOT_FROZEN), "verified_release": {"m3": VERIFIED_M3, "kg": VERIFIED_KG},
           "planning": {"concrete": {k: tot["CONCRETE"][k] for k in ("PLANNING_LOW", "PLANNING_BASE",
                                                                     "PLANNING_HIGH")},
                        "reinforcement": {k: tot["REINFORCEMENT"][k] for k in ("PLANNING_LOW", "PLANNING_BASE",
                                                                               "PLANNING_HIGH")}}}
    (HERE / MANIFEST_NAME).write_text(CLI._jdump(man), encoding="utf-8")
    DR.verify_frozen(HERE / MANIFEST_NAME, ROOT)
    for m in fz:
        DR.verify_frozen(ROOT / m, ROOT)
    return R, res, use, bsum


def main():
    R, res, use, bsum = write()
    s = R["summary"]
    print(json.dumps({"route": s["route"], "rc_concrete": {k: round(s["concrete_rc"][k], 3) for k in
                                                          ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE",
                                                           "PLANNING_HIGH")},
                      "steel_kg": {k: round(s["totals"]["REINFORCEMENT"][k], 1) for k in
                                   ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE", "PLANNING_HIGH")},
                      "beams": {k: bsum[k] for k in ("convention_A_total_m3", "convention_B_total_m3",
                                                     "still_unmeasurable")},
                      "unresolved": use["unresolved"], "pdf": res.get("pdf"), "seconds": R["seconds"]}, indent=1))


if __name__ == "__main__":
    main()
