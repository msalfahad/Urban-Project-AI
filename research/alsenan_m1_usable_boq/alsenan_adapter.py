"""ALSENAN M1 ADAPTER - the frozen S1 - S9A registers as M1 quantity items (VERIFIED / PROVISIONAL / UNRESOLVED).

Reads only frozen stage outputs (their manifests are verified before and after by build_m1.py). Nothing here measures
the drawing again. Every PROVISIONAL value is one of:
    (a) a frozen stage's own conditional value or sensitivity case, under a named convention; or
    (b) a formula over geometry a frozen stage already established, with the one assumed dimension read from the
        convention set (never written here).
VERIFIED is exactly S9's release (158.070 m3 / 18,845.961 kg). A component has one owner; a component a later stage
superseded (S9A's re-owned beam spans, D1.1-retracted links that AD1 judged wrong, S8.6's lintels S8.6A replaced) is
never counted twice. No kg/m3 ratio is used anywhere: reinforcement is either a frozen stage's bar model or a printed
callout applied to established geometry.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from engine.source import delta_release as DR
from engine.source import provisional_estimate as PE

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "research"
S9, S9A = R / "alsenan_structural_s9", R / "alsenan_structural_s9a"
PATHS = {
    "S9_CONC": S9 / "02_CONCRETE_BOQ_RECONCILIATION.csv", "S9_BARS": S9 / "03_REINFORCEMENT_BOQ_RECONCILIATION.csv",
    "S9_SUMMARY": S9 / "14_RELEASE_SUMMARY.json", "S9A_BANDS": S9A / "03_BAND_CORRECTION_REGISTER.csv",
    "S9A_BEAMS": S9A / "05_BEAM_CONVENTION_COMPARISON.csv", "S9A_BEAM_TOT": S9A / "06_BEAM_CONVENTION_TOTALS.csv",
    "S9A_OVERLAP": S9A / "07_BEAM_SLAB_COLUMN_OVERLAP_AUDIT.csv", "S9A_GB": S9A / "08_GROUND_BEAM_AUDIT.csv",
    "S9A_COLS": S9A / "09_COLUMN_AUDIT.csv", "S9A_DELTAS": S9A / "10_S9A_DELTA_REGISTER.csv",
    "S6_REG": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json",
    "S87B_WAIST": R / "alsenan_stairs_s8_7b/08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv",
    "S83_CASES": R / "alsenan_dome_ring_s8_3/12_SENSITIVITY_CASES.csv",
    "S82_GEOM": R / "alsenan_swimming_pool_s8_2/03_CONCRETE_GEOMETRY_AND_QTO.csv",
    "S1_SLAB": R / "alsenan_structural_census_s1/SLAB_PANEL_REGISTER.json",
    "D11_S51A": R / "d1_1_stirrup_authority_audit/04_S5_1A_CORRECTIONS.csv",
    "D11_S61A": R / "d1_1_stirrup_authority_audit/03_S6_1A_CORRECTIONS.csv",
}
FROZEN_MANIFESTS = [S9 / "16_S9_FREEZE_MANIFEST.json", S9A / "18_S9A_CORRECTION_MANIFEST.json",
                    R / "alsenan_stairs_s8_7b/16_S8_7B_FREEZE_MANIFEST.json",
                    R / "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
                    R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
                    R / "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
                    R / "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json"]
RELEASED = ("RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA")
DRAWING = "ST7757.dxf / ST7757.pdf"
GB_CLASS_DEPTH = {"< 2.5 m (30x30)": 300.0, "2.5 - 5 m (30x40)": 400.0, "> 5 m (30x60)": 600.0}
NO_OCCURRENCE = ("NOT_APPLICABLE", "EXCLUDED_OWNED_BY_OTHER_FAMILY")


def verify_frozen():
    """Every frozen stage manifest this adapter reads from must still verify (code, inputs, outputs)."""
    return [DR.verify_frozen(m, ROOT)["manifest"] for m in FROZEN_MANIFESTS]


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(v):
    return None if v in (None, "", "None") else float(v)


def _dims(r):
    d = r.get("DIMENSIONS") or ""
    return json.loads(d) if d.startswith("{") else {}


def load():
    T = {k: (_rows(p) if p.suffix == ".csv" else _j(p)) for k, p in PATHS.items()}
    T["S9_CONC_BY_ID"] = {r["COMPONENT_ID"]: r for r in T["S9_CONC"]}
    return T


def _storey(s):
    return {"GF_ROOF": "GF", "1F_ROOF": "1F", "2F_ROOF": "2F"}.get(s, s)


# ============================================================================ verified
def verified(T):
    out = []
    for r in T["S9_CONC"]:
        if r["LANE"] in RELEASED:
            out.append(PE.item(item_id=f"V-C:{r['COMPONENT_ID']}", component_id=r["COMPONENT_ID"], trade="CONCRETE",
                               family=r["FAMILY"], storey=r["STOREY"], category="VERIFIED",
                               base=float(r["RELEASED_M3"]), source=f"S9 02 ({r['LANE']}); {r['SOURCE'][:120]}",
                               dimensions=_dims(r), formula="frozen S9 release", support="RELEASED",
                               confidence="HIGH", double_count_risk="none: S9 single owner (S9-MC1)"))
    for b in T["S9_BARS"]:
        if b["LANE"] == "RELEASED_FROZEN_STAGE":
            out.append(PE.item(item_id=f"V-S:{b['ITEM_ID']}", component_id=b["COMPONENT_ID"], trade="REINFORCEMENT",
                               family=b["FAMILY"], storey=b["STOREY"], category="VERIFIED",
                               base=float(b["AUTHORITATIVE_KG"]), dia_mm=float(b["DIA_MM"]),
                               source=f"S9 03 ({b['OWNER_STAGE']})", formula="frozen stage BBS (authoritative version)",
                               support="RELEASED", confidence="HIGH",
                               double_count_risk="none: one authoritative version per family (S9 04)"))
    return out


# ============================================================================ beams
def _drawn_width(src):
    m = re.search(r"drawn ([0-9.]+)", src or "")
    return float(m.group(1)) if m else None


def beams(T, conv):
    out = []
    untagged_w = {u["object_id"]: u.get("drawn_width_mm") for u in T["S6_REG"]["untagged"]}
    H_lo, _, H_hi = conv.triple("UNTAGGED_BEAM_DEPTH_RANGE")
    dc = "none: slab panels stop at the drawn beam faces (S9A BO-01, 243 of 243 edges); the B x t strip is in no panel"
    for b in T["S9A_BEAMS"]:
        st, cid = b["S9A_STATE"], b["COMPONENT_ID"]
        common = dict(component_id=cid, trade="CONCRETE", family="BEAMS", storey=b["STOREY"], double_count_risk=dc,
                      source=f"S9A 05 ({b['SUBFAMILY']}, {b['BEAM_LINE']}); S1 / S6 geometry; {DRAWING} pp.4-6, 10-12")
        dims = {"B_mm": _f(b["B_MM"]), "H_mm": _f(b["H_MM"]), "L_m": _f(b["L_M"]), "t_mm": _f(b["SLAB_T_MM"]),
                "L_source": b["L_SOURCE"], "t_basis": b["SLAB_T_BASIS"]}
        if st.startswith("RE_OWNED"):
            continue                                    # S9A: the span is the cantilever band (counted there)
        if st.startswith(("CONDITIONAL", "BAND_IS", "UPPER_BOUND")):
            a, bb = float(b["V_TOTAL_DEPTH_M3"]), float(b["V_BELOW_SLAB_M3"])
            lo, base, hi = PE.by_choice(conv, "BEAM_DEPTH_READING", {"TOTAL_DEPTH": a, "BELOW_SLAB": bb})
            asm = ["BEAM_DEPTH_READING"] + (["CURVED_BEAM_LENGTH"] if st.startswith("UPPER_BOUND") else [])
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                               dimensions=dims, formula="reading A: B x H x L; reading B: B x (H + t) x L",
                               assumptions=asm, support="CONVENTION_ONLY", confidence="MEDIUM",
                               limitations=("schedule depth datum not printed (RFI-A01); S2 holds the length as a "
                                            "lower bound" + ("; centre arc length is an upper bound"
                                                             if st.startswith("UPPER_BOUND") else "")),
                               blocker="BEAM_DEPTH_CONVENTION", **common))
        elif st == "SOURCE_CONFLICT" and b["V_TOTAL_DEPTH_M3"]:
            B, H, L, t = dims["B_mm"], dims["H_mm"], dims["L_m"], dims["t_mm"]
            Bd = _drawn_width(b["B_SOURCE"]) or B
            vals = {(w, rd): (wd / 1000) * ((H + (t if rd == "BELOW_SLAB" else 0)) / 1000) * L
                    for w, wd in (("SCHEDULE", B), ("DRAWN", Bd)) for rd in ("TOTAL_DEPTH", "BELOW_SLAB")}
            base = vals[(conv.base("BEAM_CONFLICT_WIDTH"), conv.base("BEAM_DEPTH_READING"))]
            dims["B_drawn_mm"] = Bd
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=min(vals.values()), base=base,
                               high=max(vals.values()), dimensions=dims,
                               formula="B (schedule or drawn) x H (or H + t) x L",
                               assumptions=["BEAM_DEPTH_READING", "BEAM_CONFLICT_WIDTH"], support="CONVENTION_ONLY",
                               confidence="LOW", limitations="drawn width differs from the schedule width",
                               blocker="SECTION_CONFLICT", **common))
        else:
            Bd = untagged_w.get(cid)
            L = dims["L_m"]
            if Bd and L:
                ex = (Bd / 1000 * H_lo / 1000 * L, Bd / 1000 * H_hi / 1000 * L)
                out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", dimensions=dict(dims, B_drawn_mm=Bd),
                                   expression=f"{Bd / 1000:g} x {L:g} x H (H not scheduled)",
                                   exposure_low=ex[0], exposure_high=ex[1], assumptions=["UNTAGGED_BEAM_DEPTH_RANGE"],
                                   support="NO_GEOMETRY", confidence="LOW", blocker="MISSING_SECTION",
                                   limitations="no tag binds the span and no schedule row exists (RFI-A09)", **common))
            else:
                miss = b["MISSING"] or "section"
                out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", dimensions=dims,
                                   expression="B x H x L with " + miss + " missing", support="NO_GEOMETRY",
                                   confidence="LOW", blocker="MISSING_LENGTH" if "L (" in miss else "MISSING_SECTION",
                                   limitations=st, **common))
    # beam-to-beam corner squares (S9A BO-04): in neither beam today
    o = {r["CHECK_ID"]: r for r in T["S9A_OVERLAP"]}["BO-04"]
    hi = float(re.search(r"at most ([0-9.]+) m3", o["DETAIL"]).group(1))
    tot = {r["SET"]: r for r in T["S9A_BEAM_TOT"] if r["GROUP"] == "ALL"}
    c = next(v for k, v in tot.items() if k.startswith("conditional"))
    ratio = float(c["TOTAL_DEPTH_M3"]) / float(c["BELOW_SLAB_M3"])
    a_val = hi * ratio
    base = a_val if conv.base("BEAM_DEPTH_READING") == "TOTAL_DEPTH" else hi
    out.append(PE.item(item_id="P-C:BEAM-CORNER-SQUARES", component_id="BEAM-CORNER-SQUARES", trade="CONCRETE",
                       family="BEAMS", storey="ALL", category="PROVISIONAL", low=a_val, base=base, high=hi,
                       dimensions={"corner_ends": int(o["COUNT"]), "max_m3_reading_B": hi, "A_over_B": ratio},
                       formula="sum of B1 x B2 x depth at the 10 beam ends that meet without a column; reading A "
                               "scaled by the building-wide A / B ratio",
                       assumptions=["BEAM_DEPTH_READING"], support="CONVENTION_ONLY", confidence="LOW",
                       source="S9A 07 BO-04", limitations="owner of the corner square not settled (RFI-A10)",
                       double_count_risk="none: both beams stop at the other's face, so the square is in neither",
                       blocker="BEAM_DEPTH_CONVENTION"))
    return out


# ============================================================================ cantilever bands
def bands(T, conv):
    out = []
    t_lo, t_b, t_hi = conv.triple("CANTILEVER_THICKNESS_MM")
    for b in T["S9A_BANDS"]:
        if b["OWNER_DECISION"].startswith("BEAMS"):
            continue                                    # CA's own hatch: counted in the CA beam row
        a = float(b["AREA_M2"])
        st = b["STOREY_SLAB"].split()[0]
        common = dict(component_id=b["BAND_ID"], family="CANTILEVER_PORTIONS", storey=st,
                      source=f"S9A 03 (DXF {b['DXF_HANDLE']}, {b['SHEET']}); {DRAWING} p.{b['PDF_PAGE']}",
                      double_count_risk="none: outside every slab panel and column; the S9 beam span on the same "
                                        "footprint is superseded (S9A D009 - D015)")
        out.append(PE.item(item_id=f"P-C:{b['BAND_ID']}", trade="CONCRETE", category="PROVISIONAL",
                           low=a * t_lo / 1000, base=a * t_b / 1000, high=a * t_hi / 1000,
                           dimensions={"area_m2": a, "W_mm": _f(b["WIDTH_MM"]), "L_mm": _f(b["LENGTH_MM"])},
                           formula="band area x thickness", assumptions=["CANTILEVER_THICKNESS_MM"],
                           support="ONE_ASSUMED_DIMENSION", confidence="MEDIUM",
                           limitations="classified from the plotted legend hatch; not engineer-confirmed (RFI-A08)",
                           blocker="CANTILEVER_THICKNESS", **common))
        out.append(PE.item(item_id=f"U-S:{b['BAND_ID']}", trade="REINFORCEMENT", category="UNRESOLVED",
                           support="NO_GEOMETRY", confidence="LOW", blocker="MISSING_REBAR_DETAIL",
                           expression="no cantilever bar detail bound to the band", **common))
    return out


# ============================================================================ columns and necks
def _footing_depth(T, fid, conv):
    r = T["S9_CONC_BY_ID"].get(fid)
    if not r:
        return None
    d = _dims(r)
    if "D_m" in d:
        return d["D_m"]
    if "candidates" in d:                                # the F / F10 conflict footing
        c = d["candidates"][conv.base("FOOTING_F_F10_TAG")]
        return c[2] / 100
    return None


def columns(T, conv):
    out = []
    mism = {r["COLUMN_ID"]: r for r in T["S9A_COLS"]}
    d_lo, d_b, d_hi = conv.triple("FOUNDING_DEPTH_M")
    top = conv.base("NECK_TOP_LEVEL_M")
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "COLUMNS" or r["LANE"] in RELEASED:
            continue
        cid, dims = r["COMPONENT_ID"], _dims(r)
        common = dict(component_id=cid, trade="CONCRETE", family="COLUMNS", storey=r["STOREY"],
                      source=f"S9 02 ({r['LANE']}); S1 column registers; {DRAWING}",
                      double_count_risk="none: the column owns its footprint over the storey (S9-MC1)")
        if r["STOREY"] == "FOUNDATION":
            df = _footing_depth(T, dims.get("footing"), conv)
            secs = {"SCHEDULE": dims.get("schedule_cm"), "DRAWN": dims.get("drawn_cm")}
            if cid in mism:
                secs = {"SCHEDULE": json.loads(mism[cid]["SCHEDULE_CM"]), "DRAWN": json.loads(mism[cid]["DRAWN_CM"])}
            if df is None or not secs["SCHEDULE"]:
                out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                   confidence="LOW", blocker="FOUNDING_LEVEL", dimensions=dims,
                                   expression="section x (top - (-founding depth + footing depth))", **common))
                continue
            area = {k: (v[0] * v[1] / 1e4 if v else None) for k, v in secs.items()}
            h = {d: top + d - df for d in (d_lo, d_b, d_hi)}
            choice = conv.base("COLUMN_MISMATCH_SECTION") if cid in mism else "SCHEDULE"
            vals = [area[k] * h[d] for k in area if area[k] for d in h]
            base = area[choice] * h[d_b]
            asm = ["FOUNDING_DEPTH_M", "NECK_TOP_LEVEL_M"] + (["COLUMN_MISMATCH_SECTION"] if cid in mism else []) + \
                (["FOOTING_F_F10_TAG"] if "CONFLICT_F_F10" in (dims.get("footing") or "") else [])
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=min(vals), base=base,
                               high=max(vals), dimensions=dict(dims, footing_depth_m=df, neck_area_m2=area),
                               formula="section x (top + founding depth - footing depth)", assumptions=asm,
                               support="ONE_ASSUMED_DIMENSION", confidence="MEDIUM",
                               limitations="founding level not printed (minimum 1.50 m); build-up and GB top level "
                                           "not printed" + ("; drawn section differs from the schedule"
                                                            if cid in mism else ""),
                               blocker="FOUNDING_LEVEL", **common))
        elif cid in mism:
            m = mism[cid]
            lo, base, hi = PE.by_choice(conv, "COLUMN_MISMATCH_SECTION", {"SCHEDULE": _f(m["M3_SCHEDULE"]),
                                                                         "DRAWN": _f(m["M3_DRAWN"])})
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                               dimensions=dict(dims, problem_kind=m["PROBLEM_KIND"]),
                               formula="section (schedule or drawn) x printed floor-to-floor",
                               assumptions=["COLUMN_MISMATCH_SECTION"], support="CONVENTION_ONLY",
                               confidence="MEDIUM" if m["PROBLEM_KIND"].startswith("INTERP") else "LOW",
                               limitations=m["WHY"], blocker="SECTION_CONFLICT", **common))
        elif r["CONDITIONAL_M3"]:
            p = float(r["CONDITIONAL_M3"])
            rng = json.loads(r["CONDITIONAL_RANGE_M3"]) if r["CONDITIONAL_RANGE_M3"] else [p, p]
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=min(rng[0], p), base=p,
                               high=max(rng[1], p), dimensions=dims,
                               formula="schedule section x printed floor-to-floor (S9 conditional point)",
                               assumptions=["FROZEN:S9_CONDITIONAL_POINT"], support="FROZEN_STAGE_MODEL",
                               confidence="MEDIUM", limitations=r["UNRESOLVED_REASON"][:200],
                               blocker="RELEASE_RULE_APPROVAL", **common))
        else:
            out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="SECTION_CONFLICT", dimensions=dims, limitations=r["UNRESOLVED_REASON"][:200],
                               expression="schedule section x storey interval", **common))
    return out


# ============================================================================ ground beams
def _gb_depths(a):
    """Interior p.13 depths (m) by (title reading, length basis); the overlap reading only differs below 2.5 m,
    where '< 2.5 m (30x30)' and '< 5 m (30x40)' both hold and the deeper section is the alternative."""
    out = {}
    for basis, k in (("CENTRE_TO_CENTRE", "CC"), ("CLEAR", "CLEAR")):
        d = GB_CLASS_DEPTH.get(a.get(f"CLASS_BY_{k}"))
        if d is None:
            continue
        out[("EXCLUSIVE_BANDS", basis)] = d / 1000
        if a.get("TITLE_OVERLAP") == "True":
            out[("OVERLAP_DEEPER_SECTION", basis)] = max(d, 400.0) / 1000
    return out


def ground_beams(T, conv):
    """Every ground-beam span S9 did not release. The range of an item covers every disclosed reading that applies
    to it (title reading x length basis x exterior / typical section x floor build-up); the base is the configured
    reading. Width 300 and the clear length are S5's; only the depth is ever assumed."""
    out = []
    gb = {r["OCCURRENCE_ID"]: r for r in T["S9A_GB"]}
    b_lo, b_b, b_hi = conv.triple("GB_EXTERIOR_BUILDUP_M")
    title_b, basis_b = conv.base("GB_TITLE_READING"), conv.base("GB_LENGTH_BASIS")
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "GROUND_BEAMS" or r["LANE"] in RELEASED:
            continue
        cid, dims = r["COMPONENT_ID"], _dims(r)
        a = gb.get(cid, {})
        kind = a.get("PROBLEM_KIND", "")
        L = dims.get("clear_concrete_length_m") or _f(a.get("CLEAR_M"))
        details = dims.get("details") or []
        common = dict(component_id=cid, trade="CONCRETE", family="GROUND_BEAMS", storey=r["STOREY"],
                      source=f"S9 02 / S9A 08 ({kind or r['LANE']}); S5 lengths; {DRAWING} p.13",
                      double_count_risk="none: ground beams run clear between column and footing faces (S9-MC1)",
                      dimensions=dict(dims, problem_kind=kind, class_by_cc=a.get("CLASS_BY_CC"),
                                      class_by_clear=a.get("CLASS_BY_CLEAR"), title_overlap=a.get("TITLE_OVERLAP"),
                                      exterior_candidate=a.get("EXTERIOR_CANDIDATE")))
        if cid.startswith("SOCC-") and a.get("WIDTH_STATE") == "CANDIDATE_CONFLICT" and L and dims.get("depth_mm"):
            wid = {k: v / 1000 for k, v in conv["SB2_WIDTH"]["values_mm"].items()}
            lo, base, hi = PE.by_choice(conv, "SB2_WIDTH", {k: w * L * dims["depth_mm"] / 1000 for k, w in wid.items()})
            out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                               formula="schedule width (row A 80 / row B 100 cm) x 0.50 x clear length",
                               assumptions=["SB2_WIDTH"], support="CONVENTION_ONLY", confidence="MEDIUM",
                               limitations="two schedule rows for one strap (PRE-S5.1 08, Q-S2)",
                               blocker="SECTION_CONFLICT", **common))
            continue
        if not L or not a:
            out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="FOUNDING_LEVEL" if "LOWER" in cid else "GB_MISSING_DETAIL",
                               expression="width x L x depth", limitations=r["UNRESOLVED_REASON"][:200], **common))
            continue
        w = (dims.get("width_mm") or 300.0) / 1000
        interior = {k: w * L * d for k, d in _gb_depths(a).items()}
        exterior = "P13-GB-EXTERIOR" in details or a.get("EXTERIOR_CANDIDATE") == "True"
        ext = {bu: w * L * (1.0 - bu) for bu in (b_lo, b_b, b_hi)}
        concentrated = "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD" in details
        if kind == "SOURCE_CONFLICT":
            typ = interior.get(("EXCLUSIVE_BANDS", basis_b)) or w * L * 0.30
            lo_x, hi_x = sorted((w * L * 0.30, typ))
            out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="GB_LEVEL_CONFLICT", exposure_low=lo_x, exposure_high=hi_x,
                               expression=f"{w:g} x {L:g} x D; D between the +0.30 annex level bound and the "
                                          "typical p.13 class section, which conflict",
                               limitations=a.get("NEEDED", "")[:200], **common))
            continue
        int_base = interior.get((title_b, basis_b)) or interior.get(("EXCLUSIVE_BANDS", basis_b))
        cands = dict(("INT:" + t + ":" + bs, v) for (t, bs), v in interior.items())
        asm = ["GB_TITLE_READING", "GB_LENGTH_BASIS"]
        if concentrated:
            cands["CONCENTRATED:GT5M"] = w * L * 0.60
            asm.append("GB_CONCENTRATED_LOAD_SECTION")
        if exterior:
            cands.update({f"EXT:buildup={bu:g}": v for bu, v in ext.items()})
            asm += ["GB_EXTERIOR_CANDIDATE", "GB_EXTERIOR_BUILDUP_M"]
        if exterior and (a.get("DEPTH_STATE") == "BOUNDED_ABOVE" or conv.base("GB_EXTERIOR_CANDIDATE") == "EXTERIOR"):
            base = ext[b_b]
            if a.get("DEPTH_STATE") == "BOUNDED_ABOVE" and "GB_EXTERIOR_SECTION_FLOOR" not in asm:
                asm.append("GB_EXTERIOR_SECTION_FLOOR")
        elif concentrated and conv.base("GB_CONCENTRATED_LOAD_SECTION") == "GT5M_CLASS":
            base = cands["CONCENTRATED:GT5M"]
        else:
            base = int_base
        if base is None:
            out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="GB_MISSING_DETAIL", expression="width x L x depth",
                               limitations=r["UNRESOLVED_REASON"][:200], **common))
            continue
        blk = ("GB_EXTERIOR_DEPTH" if exterior else "GB_MISSING_DETAIL" if concentrated else
               "GB_TITLES_AND_LENGTH_BASIS")
        conf = "MEDIUM" if blk == "GB_TITLES_AND_LENGTH_BASIS" else "LOW"
        out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=min(cands.values()), base=base,
                           high=max(cands.values()),
                           dimensions=dict(common.pop("dimensions"), width_m=w, clear_m=L,
                                           candidates_m3={k: round(v, 6) for k, v in sorted(cands.items())}),
                           formula=("interior: width x clear length x p.13 class depth; exterior: width x clear "
                                    "length x (1.00 - floor build-up), bounded above by 1.00 m"),
                           assumptions=asm, support="ONE_ASSUMED_DIMENSION" if exterior or concentrated
                           else "CONVENTION_ONLY", confidence=conf, limitations=a.get("NEEDED", "")[:200],
                           blocker=blk, **common))
    return out


# ============================================================================ smaller families
def ground_slab(T, conv):
    out = []
    n = conv.base("SOG_MESH")
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "GROUND_SLAB" or r["LANE"] != "CONDITIONAL_NOT_RELEASED":
            continue
        d = _dims(r)
        area = d.get("area_m2_s1")
        common = dict(component_id=r["COMPONENT_ID"], family="GROUND_SLAB", storey=r["STOREY"],
                      source=f"S9 02 (S8.1 / S8.1A face); {DRAWING} GBP note", dimensions=d,
                      double_count_risk="none: faces between the ground-beam faces (S8.1 topology)")
        p = float(r["CONDITIONAL_M3"])
        out.append(PE.item(item_id=f"P-C:{r['COMPONENT_ID']}", trade="CONCRETE", category="PROVISIONAL", low=p,
                           base=p, high=p, formula="face area x 0.10 (printed T=10cm)",
                           assumptions=["GROUND_SLAB_NOTE_SCOPE"], support="CONVENTION_ONLY", confidence="MEDIUM",
                           limitations=r["UNRESOLVED_REASON"][:200], blocker="NOTE_SCOPE", **common))
        if area:
            kg = PE.mesh_kg(area, n, 10)
            out.append(PE.item(item_id=f"P-S:{r['COMPONENT_ID']}:MESH", trade="REINFORCEMENT", category="PROVISIONAL",
                               low=kg, base=kg, high=kg, dia_mm=10.0,
                               formula=f"area x {n} bars/m x 2 directions x 10^2/162 kg/m",
                               assumptions=["GROUND_SLAB_NOTE_SCOPE", "SOG_MESH"], support="CONVENTION_ONLY",
                               confidence="MEDIUM", limitations="no laps, no edge or trimmer bars",
                               blocker="NOTE_SCOPE", **common))
    return out


def lintels(T, conv):
    out = []
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "LINTELS" or r["LANE"] in RELEASED or not r["CONDITIONAL_M3"]:
            continue
        p = float(r["CONDITIONAL_M3"])
        blocked = r["LANE"] == "BLOCKED_UNQUANTIFIED"
        out.append(PE.item(item_id=f"P-C:{r['COMPONENT_ID']}", component_id=r["COMPONENT_ID"], trade="CONCRETE",
                           family="LINTELS", storey=r["STOREY"], category="PROVISIONAL", low=0.0 if blocked else p,
                           base=p, high=p, dimensions=_dims(r), formula="B x D x lintel length (S8.6A)",
                           assumptions=["LINTEL_S86A_CONDITIONAL"], support="FROZEN_STAGE_MODEL",
                           confidence="LOW" if blocked else "MEDIUM", source="S9 02 (S8.6A)",
                           limitations=r["UNRESOLVED_REASON"][:200] + ("; may be a beam head, not a lintel (low 0)"
                                                                       if blocked else ""),
                           double_count_risk="checked by S8.6 against the beams (lintel / beam overlap audit)",
                           blocker="BEARING_NOT_CONFIRMED"))
    return out


def _stair_values(T, element):
    vals = defaultdict(lambda: {"net": 0.0, "upper": 0.0})
    for r in T["S87B_WAIST"]:
        eid = r["ELEMENT_ID"].split(" (")[0].split(":")[0]
        if eid != element or r["LANE"].startswith("ALREADY"):
            continue
        w = int(r["WAIST_MM"])
        vals[w]["net"] += float(r["NET_M3"] or r["GROSS_M3"] or 0)
        vals[w]["upper"] += float(r["UPPER_BOUND_M3"] or r["NET_M3"] or r["GROSS_M3"] or 0)
    return vals


def stairs(T, conv):
    out = []
    w_lo, w_b, w_hi = (int(x) for x in conv.triple("STAIR_WAIST_MM"))
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "STAIRS" or r["LANE"] in RELEASED:
            continue
        cid = r["COMPONENT_ID"]
        v = _stair_values(T, cid)
        common = dict(component_id=cid, trade="CONCRETE", family="STAIRS", storey=r["STOREY"],
                      source=f"S8.7B 08 (waist sensitivity); S9 02 ({r['LANE']})", dimensions=_dims(r),
                      double_count_risk="S8.7 landing plates excluded (frozen, already released); beam-zone and "
                                        "column cut-outs deducted (S8.7B)")
        if not all(w in v for w in (w_lo, w_b, w_hi)):
            out.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                               confidence="LOW", blocker="STAIR_LEVELS_AND_WAIST",
                               limitations=r["UNRESOLVED_REASON"][:200], **common))
            continue
        if cid in ("B-F1", "D-F1"):
            opts = {"RC_WAIST_SLAB": v[w_b]["net"], "SOLID_RC": v[w_b]["upper"], "MASONRY_OR_FILL": 0.0}
            lo, base, hi = PE.by_choice(conv, "STEPS_ON_GRADE_FILL", opts)
            asm = ["STEPS_ON_GRADE_FILL", "STAIR_WAIST_MM"]
        else:
            lo, base, hi = v[w_lo]["net"], v[w_b]["net"], max(v[w_hi]["net"], v[w_hi]["upper"])
            asm = ["STAIR_WAIST_MM", "STAIR_OWNER_SCENARIO"]
        out.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                           formula="exact section integral (flights) / plane equivalent (winders) / plate (landings) "
                                   "at the waist", assumptions=asm, support="ONE_ASSUMED_DIMENSION",
                           confidence="LOW", limitations=r["UNRESOLVED_REASON"][:200],
                           blocker="STAIR_LEVELS_AND_WAIST", **common))
    out.append(PE.item(item_id="U-S:STAIRS", component_id="STAIRS-REINFORCEMENT", trade="REINFORCEMENT",
                       family="STAIRS", storey="ALL", category="UNRESOLVED", support="NO_GEOMETRY",
                       confidence="LOW", blocker="MISSING_REBAR_DETAIL", source="S9 03 stair rows (typical detail)",
                       expression="flight and landing bars: typical detail only, no plan callouts"))
    return out


def domes(T, conv):
    out = []
    cases = {r["CASE_ID"]: float(r["VALUE"]) for r in T["S83_CASES"]}
    d_lo, d_b, d_hi = conv.triple("DOME_RING_DEPTH_M")
    pos_b = conv.base("DOME_RING_POSITION")
    m16, m18 = PE.kg_per_m(16), PE.kg_per_m(18)
    for dome in ("A", "B"):
        area = {p: cases[f"SA-DOME-{dome}-RING-{p}-50"] / 0.50 for p in ("PLAN", "DETAIL")}
        vals = [area[p] * d for p in area for d in (d_lo, d_b, d_hi)]
        cid = f"CQ-DOME-{dome}-RING"
        out.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family="DOMES", storey="1F",
                           category="PROVISIONAL", low=min(vals), base=area[pos_b] * d_b, high=max(vals),
                           dimensions={"ring_plan_area_m2": area}, formula="ring plan area inside the bay x depth",
                           assumptions=["DOME_RING_DEPTH_M", "DOME_RING_POSITION"], support="ONE_ASSUMED_DIMENSION",
                           confidence="LOW", source="S8.3 12 sensitivity cases; S9 02 (SOURCE_CONFLICT)",
                           limitations="ring depth 'AS PER ARCH'; plan vs detail position (CF-S8.3-02, -03)",
                           double_count_risk="ring inside the bay only; the framing beams own their footprint (S8.3)",
                           blocker="DOME_RING_DEPTH"))
        kg = {p: cases[f"SA-DOME-{dome}-RINGBARS-{p}"] for p in ("PLAN", "DETAIL")}
        for d, m in ((16.0, m16), (18.0, m18)):
            share = m / (m16 + m18)
            out.append(PE.item(item_id=f"P-S:{cid}:T{int(d)}", component_id=cid, trade="REINFORCEMENT",
                               family="DOMES", storey="1F", category="PROVISIONAL", dia_mm=d,
                               low=min(kg.values()) * share, base=kg[pos_b] * share, high=max(kg.values()) * share,
                               formula="3 closed circles x 2 pi r_c x unit mass (3T16 top + 3T18 bottom)",
                               assumptions=["DOME_RING_BARS", "DOME_RING_POSITION"], support="CONVENTION_ONLY",
                               confidence="MEDIUM", source="S8.3 12 SA-*-RINGBARS",
                               limitations="no laps, no ring links", double_count_risk="ring bars only",
                               blocker="DOME_RING_DEPTH"))
        out.append(PE.item(item_id=f"U-C:CQ-DOME-{dome}-DRUM", component_id=f"CQ-DOME-{dome}-DRUM", trade="CONCRETE",
                           family="DOMES", storey="1F", category="UNRESOLVED", support="NO_GEOMETRY",
                           confidence="LOW", blocker="ARCHITECTURE_ONLY", source="S9 02 (S8.3)",
                           expression="the 1.30 m architectural drum: RC ring or wall not stated (the ring's high "
                                      "case already uses 1.30 m)"))
    out.append(PE.item(item_id="U-C:CQ-DOME-TOWER-SHELL", component_id="CQ-DOME-TOWER-SHELL", trade="CONCRETE",
                       family="DOMES", storey="1F", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="ARCHITECTURE_ONLY", source="S8.3 12 SA-TOWER-SHELL", exposure_low=0.0,
                       exposure_high=cases["SA-TOWER-SHELL"],
                       expression="architectural dome only; RC shell at t 0.10 if structural"))
    return out


def lift_and_pool(T, conv):
    out = []
    d_lo, d_b, d_hi = conv.triple("FOUNDING_DEPTH_M")
    top = conv.base("NECK_TOP_LEVEL_M")
    ff = _dims(T["S9_CONC_BY_ID"]["FTG-FF-18688-14112"])["D_m"]
    for r in T["S9_CONC"]:
        if r["FAMILY"] != "LIFT" or r["LANE"] in NO_OCCURRENCE:
            continue
        cid = r["COMPONENT_ID"]
        if r["LANE"] == "INDICATIVE_ONLY_NOT_RELEASED":
            a = _dims(r)["footprint_m2"]
            vals = sorted(a * (top + d - ff) for d in (d_lo, d_b, d_hi))
            out.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family="LIFT",
                               storey=r["STOREY"], category="PROVISIONAL", low=vals[0], base=a * (top + d_b - ff),
                               high=vals[-1], dimensions=dict(_dims(r), ff_depth_m=ff),
                               formula="wall footprint x (top + founding depth - FF depth)",
                               assumptions=["FOUNDING_DEPTH_M", "NECK_TOP_LEVEL_M"], support="ONE_ASSUMED_DIMENSION",
                               confidence="MEDIUM", source=f"S9 02 (S8.8 06); {r['SOURCE'][:80]}",
                               limitations="pit depth not printed (manufacturer); founding level not printed",
                               double_count_risk="the FF footing below is counted once, in the footing family",
                               blocker="FOUNDING_LEVEL"))
        else:
            out.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family="LIFT",
                               storey=r["STOREY"], category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="NOT_IN_SOURCE" if r["LANE"] == "NOT_IN_SOURCE" else "MISSING_SECTION",
                               source="S9 02 (S8.8)", limitations=r["UNRESOLVED_REASON"][:200]))
    geo = {r["ROW_ID"]: r for r in T["S82_GEOM"]}
    t_lo, t_b, t_hi = conv.triple("POOL_BASE_THICKNESS_M")
    fp = float(geo["CG-02"]["VALUE"])
    out.append(PE.item(item_id="P-C:PL-BASE", component_id="PL-BASE", trade="CONCRETE", family="POOL",
                       storey="GROUND", category="PROVISIONAL", low=fp * t_lo, base=fp * t_b, high=fp * t_hi,
                       dimensions={"footprint_m2": fp, "covers": ["PL-BASE-DEEP", "PL-BASE-SLOPE",
                                                                  "PL-BASE-SHALLOW"]},
                       formula="structural footprint x base thickness (slope factor ignored)",
                       assumptions=["POOL_BASE_THICKNESS_M"], support="ONE_ASSUMED_DIMENSION", confidence="MEDIUM",
                       source="S8.2 03 CG-02; S8.2A SA-04", limitations="deep / slope / shallow extents 'AS PER ARCH'",
                       double_count_risk="wall footprint below the base top belongs to the base (S8.2 CO-01)",
                       blocker="ARCH_DEPTHS"))
    h_lo, h_b, h_hi = conv.triple("POOL_WALL_HEIGHT_M")
    for k, run in (("CG-04", "E"), ("CG-05", "N"), ("CG-06", "S"), ("CG-07", "W")):
        a = float(geo[k]["VALUE"])
        cid = f"PL-WALL-RUN-{run}"
        out.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family="POOL", storey="GROUND",
                           category="PROVISIONAL", low=a * h_lo, base=a * h_b, high=a * h_hi,
                           dimensions={"band_m2": a}, formula="wall plan band x height above the base",
                           assumptions=["POOL_WALL_HEIGHT_M"], support="ONE_ASSUMED_DIMENSION", confidence="LOW",
                           source=f"S8.2 03 {k}; S8.2A SA-01 / SA-02", limitations="wall height 'AS PER ARCH'; varies",
                           double_count_risk="the east wall stops at the boundary-wall corners (S8.2 CO-02)",
                           blocker="ARCH_DEPTHS"))
    out.append(PE.item(item_id="U-S:POOL", component_id="POOL-REINFORCEMENT", trade="REINFORCEMENT", family="POOL",
                       storey="GROUND", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="ARCH_DEPTHS", source="S8.2 04 / 05 (blocked)",
                       expression="base and wall bars depend on the unprinted depths"))
    return out


def others(T, conv):
    out = []
    by = T["S9_CONC_BY_ID"]
    # footing F / F10
    r = by["FTG-CONFLICT_F_F10-30008-7312"]
    c = _dims(r)["candidates"]
    vals = {k: v[0] / 100 * v[1] / 100 * v[2] / 100 for k, v in c.items()}
    lo, base, hi = PE.by_choice(conv, "FOOTING_F_F10_TAG", vals)
    out.append(PE.item(item_id=f"P-C:{r['COMPONENT_ID']}", component_id=r["COMPONENT_ID"], trade="CONCRETE",
                       family="FOOTINGS", storey="FOUNDATION", category="PROVISIONAL", low=lo, base=base, high=hi,
                       dimensions=_dims(r), formula="schedule L x W x D of the chosen tag",
                       assumptions=["FOOTING_F_F10_TAG"], support="CONVENTION_ONLY", confidence="LOW",
                       source="S9 02 (S1 tag conflict)", limitations=r["UNRESOLVED_REASON"][:200],
                       double_count_risk="none: one footing outline", blocker="SECTION_CONFLICT"))
    # sunken drops (exposure only)
    slabs = {p["panel_id"]: p for p in T["S1_SLAB"]["rows"]}
    s_lo, _, s_hi = conv.triple("SUNKEN_DROP_M")
    for r in T["S9_CONC"]:
        cid = r["COMPONENT_ID"]
        if cid.startswith("S9-SUNKEN-DROP-"):
            p = slabs.get(cid.replace("S9-SUNKEN-DROP-", ""))
            per = float(p["perimeter_m"]) if p else None
            out.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family="SLABS",
                               storey=r["STOREY"], category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="SUNKEN_DROP_DEPTH", source="S9 02; S1 panel perimeter",
                               exposure_low=per * 0.16 * s_lo if per else None,
                               exposure_high=per * 0.16 * s_hi if per else None, assumptions=["SUNKEN_DROP_M"],
                               expression="step concrete ~ panel perimeter x 0.16 x drop (drop not printed)"))
        elif cid in ("S9-PARAPET-GF_ROOF", "S9-PARAPET-1F_ROOF", "S9-PARAPET-2F_ROOF", "S9-BOUNDARY-WALL"):
            out.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family=r["FAMILY"],
                               storey=r["STOREY"], category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="ARCH_GEOMETRY", source="S9 02", limitations=r["UNRESOLVED_REASON"][:200],
                               expression="length x height x thickness from the architectural set"))
        elif cid.startswith("S8.4-C-TANK"):
            out.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family=r["FAMILY"],
                               storey=r["STOREY"], category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                               blocker="NOT_IN_SOURCE", source="S9 02 (S8.4)",
                               expression="tank base / walls not drawn as RC"))
    # blinding
    r = by["S9-BLINDING-FOOTINGS"]
    a = _dims(r)["released_footing_plan_m2"]
    b_lo, _, b_hi = conv.triple("FOOTING_BLINDING_EXPOSURE_M")
    out.append(PE.item(item_id="U-C:S9-BLINDING-FOOTINGS", component_id="S9-BLINDING-FOOTINGS", trade="CONCRETE",
                       family="PLAIN_CONCRETE", storey="FOUNDATION", category="UNRESOLVED", support="NO_GEOMETRY",
                       confidence="LOW", blocker="NOT_PRINTED", source="S9 02 (P8-N16 mix only)",
                       exposure_low=a * b_lo, exposure_high=a * b_hi, assumptions=["FOOTING_BLINDING_EXPOSURE_M"],
                       expression=f"{a:g} m2 footing plan x blinding thickness (no projection)"))
    tl, tb, th = conv.triple("GB_BLINDING")
    wl, wb, wh = conv.triple("GB_BLINDING_WIDTH_M")
    L = math.fsum(_f(g["CLEAR_M"]) or _f(g["CC_M"]) or 0.0 for g in T["S9A_GB"] if g["FAMILY"] == "GROUND_BEAM")
    out.append(PE.item(item_id="P-C:S9-BLINDING-GROUND-BEAMS", component_id="S9-BLINDING-GROUND-BEAMS",
                       trade="CONCRETE", family="PLAIN_CONCRETE", storey="GROUND", category="PROVISIONAL",
                       low=L * wl * tl, base=L * wb * tb, high=L * wh * th, dimensions={"gb_clear_length_m": L},
                       formula="sum of ground-beam clear lengths x strip width x thickness",
                       assumptions=["GB_BLINDING", "GB_BLINDING_WIDTH_M"], support="ONE_ASSUMED_DIMENSION",
                       confidence="LOW", source="S9A 08 lengths; ST7757 p.16 typical",
                       limitations="typical detail applied to every ground beam; plain concrete, not RC",
                       double_count_risk="none: blinding is below the structural concrete", blocker="NOT_PRINTED"))
    return out


# ============================================================================ provisional steel from frozen models
S31_HOOK_PER_LOOP_MM = 150.0       # what S3.1's frozen tie model used (2 x 75 mm per tie); the convention scales it


def _loops(topology):
    return 2 if "4_LEG" in (topology or "") else 1


def steel(T, conv):
    """Unreleased bars that a frozen stage modelled bar by bar. Nothing is invented: the counts, cut lengths and
    diameters are the stage's. The one configurable part is the link / tie hook allowance (LINK_HOOK_ALLOWANCE_MM per
    closed loop), which the beam and ground-beam link models excluded and S3.1's tie model put at 150 mm."""
    out = []
    h_lo, h_b, h_hi = conv.triple("LINK_HOOK_ALLOWANCE_MM")
    agg = defaultdict(lambda: {"kg": 0.0, "n": 0, "hook_m": 0.0})
    d11 = {r["ORIGINAL_DELTA_ID"]: r for r in T["D11_S51A"] + T["D11_S61A"]}
    for b in T["S9_BARS"]:
        kg = _f(b["NOT_RELEASED_KG"]) or 0.0
        fam, lane, role = b["FAMILY"], b["LANE"], b["BAR_ROLE"]
        if lane == "RELEASED_FROZEN_STAGE" or kg <= 0:
            continue
        key = None
        if fam == "COLUMNS" and lane in ("CONDITIONAL_NOT_RELEASED", "BLOCKED_UNQUANTIFIED"):
            grp, sub = (role.split(" / ") + [""])[:2]
            if grp == "TIES":
                grp = "TIES (hook allowance)" if sub.startswith("HOOK") else "TIES (core path)"
            blk = ("TIE_LINK_HOOK_RULE" if grp.startswith("TIES") else
                   "LAP_ANCHORAGE_RULE" if grp.startswith(("LAP", "ANCHORAGE", "STARTER")) else
                   "RELEASE_RULE_APPROVAL")
            if lane == "BLOCKED_UNQUANTIFIED":
                blk = "COLUMN_SECTION_OR_LEVEL"
            key = ("COLUMNS", grp, b["DIA_MM"], blk, "STEEL_COLUMN_TIES_LAPS_STARTERS")
        elif fam in ("BEAMS", "GROUND_BEAMS") and lane == "SUPERSEDED" and "CORE_PATH" in role:
            c = d11.get(b["ITEM_ID"].split(":")[-1])
            if c is None:
                raise PE.EstimateError(f"{b['ITEM_ID']}: no D1.1 link record")
            dia = b["DIA_MM"] or c["LINK_DIA_MM"]
            key = (fam, "LINKS (core path)", dia, "TIE_LINK_HOOK_RULE", "STEEL_MODELLED_LINKS")
            agg[key]["hook_m"] += int(c["COUNT"]) * _loops(c["TOPOLOGY"]) / 1000.0
        elif fam == "LINTELS" and lane == "CONDITIONAL_NOT_RELEASED":
            key = (fam, role, b["DIA_MM"], "BEARING_NOT_CONFIRMED", "LINTEL_S86A_CONDITIONAL")
        if key:
            agg[key]["kg"] += kg
            agg[key]["n"] += 1
    for (fam, role, dia, blk, asm), v in sorted(agg.items()):
        d = float(dia)
        lo = base = hi = v["kg"]
        asms, formula = [asm], "frozen stage bar model (count x cut length x unit mass), summed"
        lim = "modelled with the printed lap / starter rule; range not quantified"
        if role == "TIES (hook allowance)":
            lo, base, hi = (v["kg"] * x / S31_HOOK_PER_LOOP_MM for x in (h_lo, h_b, h_hi))
            asms.append("LINK_HOOK_ALLOWANCE_MM")
            formula = "S3.1 hook rows (2 x 75 mm per tie) scaled to the configured allowance per closed loop"
            lim = "hook length, bend radius and closure not printed (RFI-A02)"
        elif "core path" in role:
            lim = "sharp-corner core path; rounded corners shorten it by (8 - 2 pi) R per loop (R not printed)"
        out.append(PE.item(item_id=f"P-S:{fam}:{role}:D{dia}:{blk}", component_id=f"{fam}:{role}",
                           trade="REINFORCEMENT", family=fam, storey="ALL", category="PROVISIONAL", low=lo, base=base,
                           high=hi, dia_mm=d, dimensions={"bar_rows": v["n"]}, formula=formula, assumptions=asms,
                           support="FROZEN_STAGE_MODEL", confidence="MEDIUM",
                           source="S9 03 (S3.1 / S6.1 / S5.1 / S8.6A models); D1.1 03 / 04 counts",
                           limitations=lim, double_count_risk="none: these parts are not in the released kg (S9 03 lanes)",
                           blocker=blk))
        if v["hook_m"]:
            m = PE.kg_per_m(d)
            lo, base, hi = (v["hook_m"] * x * m for x in (h_lo, h_b, h_hi))
            out.append(PE.item(item_id=f"P-S:{fam}:LINKS (hook allowance):D{dia}", component_id=f"{fam}:LINK_HOOKS",
                               trade="REINFORCEMENT", family=fam, storey="ALL", category="PROVISIONAL", low=lo,
                               base=base, high=hi, dia_mm=d,
                               dimensions={"closed_loops": round(v["hook_m"] * 1000), "bar_rows": v["n"]},
                               formula="closed loops (D1.1 count x loops per set) x hook allowance x d^2/162",
                               assumptions=["STEEL_MODELLED_LINKS", "LINK_HOOK_ALLOWANCE_MM"],
                               support="FROZEN_STAGE_MODEL", confidence="LOW",
                               source="D1.1 03 / 04 (COUNT, TOPOLOGY, LINK_DIA_MM)",
                               limitations="hook length and closure not printed; the S3.1 tie allowance is reused",
                               double_count_risk="none: the core-path model excludes hooks", blocker=blk))
    # families with bars nobody modelled: one unresolved item per family / role
    miss = defaultdict(int)
    for b in T["S9_BARS"]:
        if b["LANE"] in ("BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "NOT_IN_SOURCE") and not (_f(b["NOT_RELEASED_KG"])):
            miss[(b["FAMILY"], b["BAR_ROLE"].split(" / ")[0])] += 1
    for (fam, role), n in sorted(miss.items()):
        if fam in ("STAIRS",):
            continue                                    # one stair item already
        out.append(PE.item(item_id=f"U-S:{fam}:{role}", component_id=f"{fam}:{role}", trade="REINFORCEMENT",
                           family=fam, storey="ALL", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                           blocker="MISSING_REBAR_DETAIL", source="S9 03 (blocked bar rows)",
                           dimensions={"bar_rows": n}, expression=f"{n} bar rows with no source cut length"))
    return out


def build_items(conv, T=None):
    T = T or load()
    items = (verified(T) + beams(T, conv) + bands(T, conv) + columns(T, conv) + ground_beams(T, conv) +
             ground_slab(T, conv) + lintels(T, conv) + stairs(T, conv) + domes(T, conv) + lift_and_pool(T, conv) +
             others(T, conv) + steel(T, conv))
    PE.check(items, conv)
    return items, T


def coverage(items, T):
    """Every S9 concrete record lands in exactly one M1 item (or is an excluded / not-applicable record)."""
    owned = {i["component_id"] for i in items if i["trade"] == "CONCRETE"}
    superseded = {d["COMPONENT_ID"] for d in T["S9A_DELTAS"] if d["CHANGE_KIND"] == "OWNERSHIP_TRANSFER"}
    pool = {"PL-BASE-DEEP", "PL-BASE-SLOPE", "PL-BASE-SHALLOW"}
    rows = []
    for r in T["S9_CONC"]:
        cid = r["COMPONENT_ID"]
        if cid in owned:
            how = "ITEM"
        elif cid in superseded:
            how = "SUPERSEDED_BY_S9A_BAND"
        elif cid in pool:
            how = "COVERED_BY_PL-BASE"
        elif r["LANE"] in NO_OCCURRENCE:
            how = r["LANE"]
        elif r["FAMILY"] == "OTHER":
            how = "NO_PLAN_OCCURRENCE (typical detail only)"
        elif r["FAMILY"] == "BEAMS" and r["LANE"] == "EXCLUDED_OWNED_BY_OTHER_FAMILY":
            how = r["LANE"]
        else:
            how = "MISSING"
        rows.append({"COMPONENT_ID": cid, "FAMILY": r["FAMILY"], "S9_LANE": r["LANE"], "M1": how})
    return rows
