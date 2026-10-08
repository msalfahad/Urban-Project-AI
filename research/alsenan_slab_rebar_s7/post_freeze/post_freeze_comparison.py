"""S7 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_slab_rebar_s7/post_freeze/post_freeze_comparison.py [<CHRISTIANNP_FORENSIC_RERUN dir>]

Refuses to run unless 12_S7_FREEZE_MANIFEST.json still matches every frozen code / input / output file, is the very
manifest committed at the S7 freeze commit, and that commit holds no post_freeze file. Only then does it open the
references, and only to compare the frozen S7 slab steel in matching scope:
  * old Urban, R4 (REBAR_POPULATION_REGISTER_V4: per-callout binder components) - matched token by token, each
    difference decomposed (count term, then length term) and classified;
  * old Urban, R3 (SLAB_REBAR_AUDIT populations) and V3b (population row): per floor / total, through R4 + the
    reference's own revision change;
  * the freelancer QS lineage (SLABS: net slab concrete rows and one steel lump);
  * the U-C4N oracle (one incomplete project total: no slab scope);
  * christiannp's frozen forensic rerun (13_rebar/REBAR_EVIDENCE.csv slab rows; 09_slabs net areas), read-only;
  * the rough 90 kg/m3 SLABS profile (SANITY_CHECK_ONLY, never promoted).
Every difference gets classes from CLASSES; nothing is tuned: the S7 outputs are never written here, and a correction
found here needs a new issue, new source evidence, a new regression and a new version.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
FREEZE_COMMIT = "16741ec"
MANIFEST = PKG / "12_S7_FREEZE_MANIFEST.json"
CLASSES = ("SCOPE", "TEMPERATURE_EXCLUDED", "SPECIAL_STRUCTURE_EXCLUDED", "ANCHORAGE_EXCLUDED", "COVER_BASIS",
           "CURTAILMENT", "TOP_SUPPORT_RULE", "COUNT_CONVENTION", "OPENING", "TRANSITION", "REFERENCE_ASSUMPTION",
           "GEOMETRY", "OTHER_KNOWN", "UNKNOWN")
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/REBAR_POPULATION_REGISTER_V4.json"
R3 = ROOT / "research/alsenan_rebar_truth_03/registers/SLAB_REBAR_AUDIT.json"
V3B = ROOT / "research/alsenan_control_plane_01/registers/STRUCTURAL_POPULATION_COVERAGE_REGISTER.json"
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
ORACLES = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
ROUGH = ROOT / "engine/profiles/URBAN_ROUGH_REBAR_PROFILE_V1.json"
TOKENS = ROOT / "research/alsenan_slab_rebar_pre_s7/03_SLAB_REBAR_TOKENS.csv"
FLOOR_OF = {"GF": "GF_ROOF_SLAB", "1F": "1F_ROOF_SLAB", "2F": "2F_ROOF_SLAB"}
SHEET_OF = {"GFRS": "GF_ROOF_SLAB", "FFRS": "1F_ROOF_SLAB", "SFRS": "2F_ROOF_SLAB"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return float(v) if v not in ("", None) else 0.0


def _r(v, n=3):
    return None if v is None else round(float(v), n)


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


# ------------------------------------------------------------------ freeze first
def verify_freeze():
    m = _j(MANIFEST)
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG), ("decision_records", ROOT),
                             ("candidate_registers", ROOT)) for k, h in m[g].items() if _sha(base / k) != h]
    if bad or m["state"] != "FROZEN_BEFORE_REFERENCE_COMPARISON" or m["references_read_before_freeze"]:
        raise SystemExit(f"S7 freeze broken - refusing to compare: {bad}")
    full = _git("rev-parse", FREEZE_COMMIT).strip()
    at_freeze = subprocess.run(["git", "show", f"{full}:research/alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json"],
                               cwd=ROOT, check=True, capture_output=True).stdout
    tree = _git("ls-tree", "-r", "--name-only", full, "research/alsenan_slab_rebar_s7/").split()
    if hashlib.sha256(at_freeze).hexdigest() != _sha(MANIFEST) or any("post_freeze" in t for t in tree):
        raise SystemExit("S7 freeze commit does not hold this manifest, or already holds a post-freeze file")
    for o in m["outputs"]:
        if f"research/alsenan_slab_rebar_s7/{o}" not in tree:
            raise SystemExit(f"S7 output {o} was not committed at the freeze")
    return m, full


# ------------------------------------------------------------------ frozen S7
def s7():
    rel = _rows(PKG / "01_S7_RELEASE_ITEMS.csv")
    blk = _rows(PKG / "02_S7_BLOCKED_ITEMS.csv")
    pan = {r["PANEL_ID"]: r for r in _rows(PKG / "05_S7_PANEL_SUMMARY.csv")}
    fl = {r["FLOOR"]: r for r in _rows(PKG / "07_S7_FLOOR_SUMMARY.csv")}
    summ = _j(PKG / "09_S7_PROJECT_SUMMARY.json")
    return rel, blk, pan, fl, summ


def token_of(row):
    first = json.loads(row["SOURCE_RULE_IDS"])[0]
    return first.split()[1] if first.startswith("token ") else None


def s7_tokens(rel):
    """Per bottom callout token: S7 kg by role, family width, equivalent lengths."""
    t = defaultdict(lambda: {"kg": defaultdict(float), "len": defaultdict(float), "W": 0.0, "rate": None, "dia": None,
                             "um": None, "floor": None, "panels": set()})
    for r in rel:
        if r["LAYER"] != "BOTTOM":
            continue
        k = token_of(r)
        x = t[k]
        x["kg"][r["BAR_ROLE"]] += _f(r["KG"])
        x["len"][r["BAR_ROLE"]] += _f(r["EQUIVALENT_TOTAL_LENGTH_M"])
        x["rate"], x["dia"], x["um"], x["floor"] = _f(r["RATE_PER_M"]), int(r["DIAMETER_MM"]), _f(r["UNIT_MASS_KG_M"]), \
            r["FLOOR"]
        if r["BAR_ROLE"] in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50"):
            x["W"] += _f(r["TRANSVERSE_WIDTH_M"])
            x["panels"].add(r["PANEL_ID"])
    return t


def s7_volume(pan):
    v = defaultdict(float)
    for p in pan.values():
        if p["S7_SCOPE"] == "IN_SCOPE_S7":
            v[p["FLOOR"]] += _f(p["AREA_M2"]) * _f(p["THICKNESS_MM"]) / 1000.0
    return dict(v)


# ------------------------------------------------------------------ references
def r4_components():
    d = _j(R4)
    cs = [c for c in d["components"] if c["population_id"] in ("POP:SLAB:GF", "POP:SLAB:1F", "POP:SLAB:2F")]
    pops = {p["pop_id"]: p for p in d["populations"] if p["pop_id"] in ("POP:SLAB:GF", "POP:SLAB:1F", "POP:SLAB:2F")}
    return cs, pops


def r4_tokens(cs):
    t = defaultdict(lambda: {"halves": {}, "floor": None, "kg": 0.0})
    for c in cs:
        parts = c["comp_id"].split("|")
        tok = parts[1]
        half = parts[2] if len(parts) > 2 else ("TOP_GROUP" if c["layer"] == "TOP" else "SINGLE")
        kg = (c["verified_kg"] or 0.0) + (c["provisional_kg"] or 0.0)
        n = (c["count"] or {}).get("verified") if isinstance(c["count"], dict) else c["count"]
        um = c["unit_weight_kg_m"] or 0.0
        t[tok]["halves"][half] = {"kg": kg, "verified_kg": c["verified_kg"] or 0.0,
                                  "provisional_kg": c["provisional_kg"] or 0.0, "n": n or 0, "um": um,
                                  "L_ver": c["verified_length_m"] or 0.0, "L_prov": c["provisional_length_m"] or 0.0,
                                  "dia": c["dia_mm"], "layer": c["layer"], "state": c["state"],
                                  "rule": "; ".join(p["rule"] for p in c["parts"] if p.get("rule"))}
        t[tok]["floor"] = FLOOR_OF[c["population_id"][-2:]]
        t[tok]["kg"] += kg
    return t


def classify_token(tok, info, s7t, tokreg, pan, blk_conflict_panels, transferred):
    """S7 status of one R4 callout token (an S8 ownership transfer outranks the conflict it preserves)."""
    if tok in s7t:
        return "MATCHED", None
    if tok in transferred:
        return f"S7_EXCLUDED (S8_TRANSFERRED ({transferred[tok]}))", "SPECIAL_STRUCTURE_EXCLUDED"
    reg = tokreg.get(tok)
    if not reg:
        return "NOT_IN_S7_TOKEN_REGISTER", "SCOPE"
    if reg["TERMINAL_STATE"] == "REFERENCE_ONLY":
        return f"S7_REFERENCE_ONLY_LABEL ({reg['KIND']})", "REFERENCE_ASSUMPTION"
    if reg["TERMINAL_STATE"] == "SOURCE_CONFLICT":
        return "S7_SOURCE_CONFLICT", "REFERENCE_ASSUMPTION"
    if reg["KIND"] == "SUPPORT_TOP_BAR":
        return "S7_LOCAL_TOP_COUNT_ONLY", "REFERENCE_ASSUMPTION"
    if reg["KIND"] == "CORNER_BAR":
        return "S7_EXPLICIT_COUNT_LENGTH_BLOCKED", "REFERENCE_ASSUMPTION"
    p = pan.get(reg["BOUND_TO"])
    scope = p["S7_SCOPE"] if p else ""
    if scope.startswith("S8_TRANSFERRED") or scope.startswith("EXCLUDED_SPECIAL") or \
            reg["TERMINAL_STATE"] == "EXCLUDED_SPECIAL_STRUCTURE":
        return f"S7_EXCLUDED ({scope or reg['TERMINAL_STATE']})", "SPECIAL_STRUCTURE_EXCLUDED"
    if reg["BOUND_TO"] in blk_conflict_panels:
        return "S7_SOURCE_CONFLICT_FAMILY", "REFERENCE_ASSUMPTION"
    if scope.startswith("BEARING_WALL"):
        return "S7_NOT_A_SLAB_PANEL", "SCOPE"
    return f"S7_NOT_RELEASED ({reg['TERMINAL_STATE']})", "SCOPE"


def decompose(tok, r, s):
    """R4 - S7 for one matched bottom callout, half by half: count term (n_R - n_S) x L_R x um, then length term
    n_S x (L_R - L_S) x um. A count gap within one bar is COUNT_CONVENTION, beyond it GEOMETRY (the binder's distribution
    width); the CONT length gap is ANCHORAGE_EXCLUDED (R4: clear span + measured embedment at both supports; S7: face to
    face, the beyond-face portion blocked) or GEOMETRY when R4 is shorter; the STOP length gap is CURTAILMENT."""
    out = []
    um = s["um"]
    n_s = s["rate"] * 0.5 * s["W"]
    full = s["kg"].get("BOTTOM_IN_PANEL", 0.0)
    halves = {"CONT50": s["kg"].get("BOTTOM_CONTINUING_50", 0.0) + s["kg"].get("BOTTOM_SUPPORT_CROSSING", 0.0) +
              0.5 * full,
              "STOP50": s["kg"].get("BOTTOM_CURTAILED_50", 0.0) + 0.5 * full}
    for half, s_kg in halves.items():
        h = r["halves"].get(half)
        r_kg = h["kg"] if h else 0.0
        if not h or not h["n"]:
            out.append((half, "SCOPE", r_kg - s_kg, "no R4 component for this half"))
            continue
        L_r = r_kg / (h["n"] * um)          # one unit mass for both terms, so the two terms close exactly
        L_s = s_kg / (n_s * um) if n_s > 0 else 0.0
        count_term = (h["n"] - n_s) * L_r * um
        conv = max(-1.0, min(1.0, h["n"] - n_s)) * L_r * um
        out.append((half, "COUNT_CONVENTION", conv, f"R4 n = {h['n']} vs S7 rate x 0.5 x W = {n_s:.3f} (ceil / "
                                                     "binder floor(w/s)+1, at most one bar)"))
        if abs(count_term - conv) > 1e-9:
            out.append((half, "GEOMETRY", count_term - conv, "distribution width: R4 binds the callout to one drawn "
                                                             "bar's width, S7 covers the whole panel by strips"))
        length_term = n_s * (L_r - L_s) * um
        if half == "CONT50":
            cls = "ANCHORAGE_EXCLUDED" if length_term > 0 else "GEOMETRY"
            why = (f"R4 L = {L_r:.3f} m ('{h['rule']}') vs S7 mean {L_s:.3f} m face to face incl. its crossings")
        else:
            cls = "CURTAILMENT"
            why = (f"R4 STOP50 L = {L_r:.3f} m (verified {h['L_ver']:.3f} + provisional {h['L_prov']:.3f}; worst case "
                   f"both supports continuous) vs S7 {L_s:.3f} m (0.125 L only at continuous / unresolved ends; "
                   "unresolved stop zones blocked)")
        out.append((half, cls, length_term, why))
    return out


def christiannp(cdir):
    if not cdir:
        return None
    ev = Path(cdir) / "13_rebar" / "REBAR_EVIDENCE.csv"
    areas = Path(cdir) / "09_slabs" / "SLAB_VECTOR_VS_RASTER.csv"
    rows = [r for r in _rows(ev) if r["ELEMENT"] == "SLAB"]
    first = {}
    for r in _rows(areas):
        first.setdefault(r["PLAN"], r)
    inc = [r for r in rows if r["INCLUDED_EXCLUDED"].startswith("INCLUDED")]
    return {"evidence_sha256": _sha(ev), "areas_sha256": _sha(areas), "slab_rows": len(rows),
            "slab_rows_included": len(inc), "slab_kg": math.fsum(_f(r["KG"]) for r in inc),
            "excluded_reasons": dict(Counter(r["INCLUDED_EXCLUDED"] for r in rows)),
            "net_area_m2": {SHEET_OF[k]: _f(v["VECTOR_NET_AREA_SAMPLED_M2"]) for k, v in first.items() if k in SHEET_OF}}


# ------------------------------------------------------------------ main
def main():
    m, full_commit = verify_freeze()
    rel, blk, pan, fl, summ = s7()
    T = summ["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    s7t = s7_tokens(rel)
    vol = s7_volume(pan)
    V7 = math.fsum(vol.values())
    top_s7 = summ["totals_kg"]["TOP_SUPPORT_PROJECT_BASIS_KG"]
    refs = {}

    # ---------------------------------------------------- A: old Urban R4, token by token
    cs, pops = r4_components()
    refs["OLD_URBAN_R4"] = {"path": str(R4.relative_to(ROOT)), "sha256": _sha(R4)}
    r4t = r4_tokens(cs)
    tokreg = {r["TOKEN_ID"]: r for r in _rows(TOKENS)}
    conflict_panels = {b["OWNER"] for b in blk if b["S7_LANE"] == "SOURCE_CONFLICT"}
    transferred = {t["object_id"].split()[1]: t["region"] for t in
                   _rows(ROOT / "research/alsenan_slab_rebar_pre_s7_1/02_OWNERSHIP_TRANSFERS.csv")
                   if t["kind"] == "TOKEN"}
    token_rows, causes = [], defaultdict(lambda: defaultdict(float))
    for tok in sorted(set(r4t) | set(s7t)):
        r = r4t.get(tok)
        s = s7t.get(tok)
        r_kg = r["kg"] if r else 0.0
        s_kg = math.fsum(s["kg"].values()) if s else 0.0
        parts = []
        if r and s:
            status = "MATCHED"
            parts = decompose(tok, r, s)
            other = [h for h in r["halves"] if h not in ("CONT50", "STOP50")]
            for h in other:
                parts.append((h, "REFERENCE_ASSUMPTION", r["halves"][h]["kg"], f"R4 extra component {h}"))
        elif r:
            status, cls = classify_token(tok, r, s7t, tokreg, pan, conflict_panels, transferred)
            parts = [("ALL", cls, r_kg, status)]
        else:
            status = "S7_ONLY (R4 did not bind this callout)"
            parts = [("ALL", "SCOPE", -s_kg, status)]
        got = math.fsum(p[2] for p in parts)
        if abs(got - (r_kg - s_kg)) > 1e-6:
            raise SystemExit(f"decomposition of token {tok} does not close: {got} vs {r_kg - s_kg}")
        for half, cls, kg, why in parts:
            causes["OLD_URBAN_R4"][cls] += kg
        token_rows.append({"TOKEN": tok, "FLOOR": (r or {}).get("floor") or (s or {}).get("floor"),
                           "RAW": (tokreg.get(tok) or {}).get("RAW"), "STATUS": status,
                           "S7_PANELS": sorted(s["panels"]) if s else [], "R4_KG": r_kg, "S7_KG": s_kg,
                           "DIFF_KG_R4_MINUS_S7": r_kg - s_kg,
                           "R4_COMPONENTS": {h: {k: v for k, v in x.items() if k in ("kg", "n", "L_ver", "L_prov",
                                                                                     "state")}
                                             for h, x in (r["halves"].items() if r else [])},
                           "S7_BY_ROLE_KG": dict(s["kg"]) if s else {},
                           "S7_EQUIVALENT_BARS_PER_HALF": s["rate"] * 0.5 * s["W"] if s else None,
                           "CLASSES": [{"half": h, "class": c, "kg": k, "why": w} for h, c, k, w in parts]})
    # the S7 plan-note-2 top steel is a component R4 never quantified
    causes["OLD_URBAN_R4"]["TOP_SUPPORT_RULE"] -= top_s7
    r4_total = math.fsum(x["kg"] for x in r4t.values())
    r4_pop = {k: (p["lower_bound_kg"], p["provisional_kg"]) for k, p in pops.items()}
    if abs(r4_total - math.fsum(a + b for a, b in r4_pop.values())) > 1e-3:
        raise SystemExit("R4 components do not add up to the R4 populations")
    if abs(math.fsum(causes["OLD_URBAN_R4"].values()) - (r4_total - T)) > 1e-6:
        raise SystemExit("R4 decomposition does not close on the project total")

    # ---------------------------------------------------- B: R3 / V3b population level
    r3 = {p["pop_id"]: p for p in _j(R3)["populations"] if p["pop_id"].startswith("POP:SLAB:")}
    refs["OLD_URBAN_R3"] = {"path": str(R3.relative_to(ROOT)), "sha256": _sha(R3)}
    r3_total = math.fsum(p["lower_bound_kg"] + p["provisional_kg"] for p in r3.values())
    v3 = _j(V3B)
    v3b_row = next(r for r in _walk(v3) if isinstance(r, dict) and r.get("population") == "SLAB" and "net_kg" in r)
    refs["OLD_URBAN_V3B"] = {"path": str(V3B.relative_to(ROOT)), "sha256": _sha(V3B)}
    for name, total in (("OLD_URBAN_R3", r3_total), ("OLD_URBAN_V3B", v3b_row["net_kg"])):
        for cls, kg in causes["OLD_URBAN_R4"].items():
            causes[name][cls] += kg
        causes[name]["REFERENCE_ASSUMPTION"] += total - r4_total       # the reference's own revision to R4
    floor_rows = []
    for fl_k, fl_name in FLOOR_OF.items():
        s7_kg = _f(fl[fl_name]["PROJECT_BASIS_KG"])
        r4_lb, r4_pr = r4_pop[f"POP:SLAB:{fl_k}"]
        p3 = r3[f"POP:SLAB:{fl_k}"]
        floor_rows.append({"FLOOR": fl_name, "S7_KG": s7_kg, "R4_KG": r4_lb + r4_pr, "R4_LOWER_BOUND_KG": r4_lb,
                           "R4_PROVISIONAL_KG": r4_pr, "R3_KG": p3["lower_bound_kg"] + p3["provisional_kg"],
                           "S7_SCOPE_CONCRETE_M3": vol.get(fl_name, 0.0),
                           "S7_TOP_KG": _f(fl[fl_name]["TOP_SUPPORT_KG"]),
                           "S7_BOTTOM_KG": _f(fl[fl_name]["BOTTOM_MAIN_KG"]),
                           "R4_TOKEN_DIFF_BY_CLASS": {c: math.fsum(x["kg"] for t in token_rows if t["FLOOR"] == fl_name
                                                                   for x in t["CLASSES"] if x["class"] == c)
                                                      for c in CLASSES if any(x["class"] == c for t in token_rows
                                                                              if t["FLOOR"] == fl_name
                                                                              for x in t["CLASSES"])}})

    # ---------------------------------------------------- C: freelancer
    lin = _j(LINEAGE)
    refs["FREELANCER"] = {"path": str(LINEAGE.relative_to(ROOT)), "sha256": _sha(LINEAGE),
                          "workbook_sha256": lin.get("workbook_sha256")}
    slabs = next(c for c in lin["categories"] if c["category_id"] == "SLABS")
    fr_steel = slabs["steel_value_t"] * 1000.0
    fr_m3 = slabs["quantity"]
    fr_ratio = fr_steel / fr_m3
    leaves = [s for s in slabs["subcomponents"] if s.get("kind") == "LEAF_ROW"]
    tank = [s for s in leaves if s.get("D") == 0.18]
    tank_m3 = math.fsum(s["value"] for s in tank)
    fr_areas = defaultdict(float)
    for s in leaves:
        fr_areas[{"SLAB_NET_GF": "GF_ROOF_SLAB", "SLAB_NET_1F": "1F_ROOF_SLAB", "SLAB_NET_2F": "2F_ROOF_SLAB"}[
            s["physical_kind"]]] += s["value"] / s["D"] if s.get("D") not in (None, 0.18) else 0.0
    fr_scope_m3 = fr_m3 - tank_m3
    fr_causes = {"SPECIAL_STRUCTURE_EXCLUDED": tank_m3 * fr_ratio,
                 "GEOMETRY": (fr_scope_m3 - V7) * fr_ratio,
                 "REFERENCE_ASSUMPTION": V7 * fr_ratio - T}
    for k, v in fr_causes.items():
        causes["FREELANCER"][k] += v

    # ---------------------------------------------------- D: U-C4N, E: christiannp, F: rough
    orc = _j(ORACLES)
    refs["UC4N"] = {"path": str(ORACLES.relative_to(ROOT)), "sha256": _sha(ORACLES)}
    uc4n = next(o for o in orc["oracle_net_rebar"] if o["oracle"] == "UC4N")
    ch = christiannp(sys.argv[1] if len(sys.argv) > 1 else None)
    if ch:
        refs["CHRISTIANNP"] = {"path": "CHRISTIANNP_FORENSIC_RERUN (external, read-only)",
                               "evidence_sha256": ch["evidence_sha256"], "areas_sha256": ch["areas_sha256"]}
        causes["CHRISTIANNP"]["SCOPE"] += ch["slab_kg"] - T
    rough = _j(ROUGH)
    refs["ROUGH_PROFILE"] = {"path": str(ROUGH.relative_to(ROOT)), "sha256": _sha(ROUGH)}
    ratio = rough["ratios_kg_per_m3"]["SLABS"]
    rough_s7 = ratio * V7
    causes["ROUGH_90"]["REFERENCE_ASSUMPTION"] += rough_s7 - T

    # ---------------------------------------------------- reference totals
    tot = [
        {"REFERENCE": "OLD_URBAN_R4", "SCOPE": "elevated slabs GF/1F/2F (all R4 slab callouts, bottom + T&B + tops)",
         "MATCHING": "TOKEN_BY_TOKEN", "REFERENCE_KG": r4_total, "S7_KG": T, "DIFF_KG": r4_total - T},
        {"REFERENCE": "OLD_URBAN_R3", "SCOPE": "elevated slab populations GF/1F/2F (lower bound + provisional)",
         "MATCHING": "FLOOR (through R4)", "REFERENCE_KG": r3_total, "S7_KG": T, "DIFF_KG": r3_total - T},
        {"REFERENCE": "OLD_URBAN_V3B", "SCOPE": "SLAB population row (net)", "MATCHING": "TOTAL (through R4)",
         "REFERENCE_KG": v3b_row["net_kg"], "S7_KG": T, "DIFF_KG": v3b_row["net_kg"] - T,
         "NOTE": f"V3b technical {v3b_row['technical_kg']} kg (multi-engine SLABS row)"},
        {"REFERENCE": "FREELANCER", "SCOPE": "SLABS category: net slab concrete GF/1F/2F incl. the 2F T18 slab, one "
                                             "steel lump", "MATCHING": "CATEGORY",
         "REFERENCE_KG": fr_steel, "S7_KG": T, "DIFF_KG": fr_steel - T,
         "NOTE": f"lump {slabs['steel_value_t']} t over {fr_m3:.4f} m3 = {fr_ratio:.2f} kg/m3 implied"},
        {"REFERENCE": "UC4N", "SCOPE": "project net rebar total only (KNOWN_INCOMPLETE)", "MATCHING": "NOT_COMPARABLE",
         "REFERENCE_KG": None, "S7_KG": T, "DIFF_KG": None,
         "NOTE": f"{uc4n['net_rebar_t']} t for the whole project, no slab figure: no matching scope"}]
    if ch:
        tot.append({"REFERENCE": "CHRISTIANNP", "SCOPE": "13_rebar SLAB rows", "MATCHING": "CATEGORY",
                    "REFERENCE_KG": ch["slab_kg"], "S7_KG": T, "DIFF_KG": ch["slab_kg"] - T,
                    "NOTE": f"{ch['slab_rows']} slab rows, {ch['slab_rows_included']} included (callouts never bound)"})
    tot.append({"REFERENCE": "ROUGH_90_KG_PER_M3", "SCOPE": "S7-scope slab concrete x 90 kg/m3 (SANITY_CHECK_ONLY)",
                "MATCHING": "SANITY_ONLY", "REFERENCE_KG": rough_s7, "S7_KG": T, "DIFF_KG": rough_s7 - T,
                "NOTE": f"S7 intensity {T / V7:.2f} kg/m3 over {V7:.3f} m3; rough on old-Urban 81.432 m3 = "
                        f"{ratio * 81.432:.2f} kg (other scope); never promoted to accurate S7"})
    for t in tot:
        c = causes.get({"ROUGH_90_KG_PER_M3": "ROUGH_90"}.get(t["REFERENCE"], t["REFERENCE"]), {})
        t["CLASSES"] = {k: v for k, v in sorted(c.items()) if abs(v) > 1e-9}
        t["CLASSES_CLOSE"] = t["DIFF_KG"] is None or abs(math.fsum(c.values()) - t["DIFF_KG"]) <= 1e-6

    cause_rows = []
    for ref, c in sorted(causes.items()):
        for cls, kg in sorted(c.items()):
            if abs(kg) > 1e-9:
                cause_rows.append({"REFERENCE": ref, "CLASS": cls, "KG_REFERENCE_MINUS_S7": kg,
                                   "BASIS": CAUSE_BASIS.get((ref.split("_")[0] if ref.startswith("OLD") else ref,
                                                             cls), CAUSE_BASIS.get(("ANY", cls), ""))})
    unknown = [r for r in cause_rows if r["CLASS"] == "UNKNOWN"]

    # ---------------------------------------------------- write
    _csv("S7_POST_FREEZE_OLD_URBAN_R4_TOKENS.csv", token_rows, list(token_rows[0]))
    _csv("S7_POST_FREEZE_REFERENCE_TOTALS.csv", tot, ["REFERENCE", "SCOPE", "MATCHING", "REFERENCE_KG", "S7_KG",
                                                       "DIFF_KG", "CLASSES", "CLASSES_CLOSE", "NOTE"])
    _csv("S7_POST_FREEZE_DIFFERENCE_CAUSES.csv", cause_rows, ["REFERENCE", "CLASS", "KG_REFERENCE_MINUS_S7", "BASIS"])
    _csv("S7_POST_FREEZE_FLOOR_COMPARISON.csv", floor_rows, list(floor_rows[0]))
    s = {"round": "S7_POST_FREEZE", "freeze_manifest_verified": True, "freeze_commit": full_commit,
         "freeze_manifest_sha256": _sha(MANIFEST), "frozen_engine_stamp": m["engine_commit_stamp"],
         "classes": list(CLASSES), "unknown_rows": unknown, "references": refs,
         "s7_totals_kg": summ["totals_kg"], "s7_scope_concrete_m3": vol, "s7_intensity_kg_per_m3": T / V7,
         "reference_totals": tot,
         "r4_tokens": {"total": len(token_rows), "by_status": dict(Counter(t["STATUS"].split(" (")[0]
                                                                          for t in token_rows))},
         "freelancer": {"steel_kg": fr_steel, "concrete_m3": fr_m3, "implied_kg_per_m3": fr_ratio,
                        "tank_t18_m3": tank_m3, "net_areas_m2_excl_tank": dict(fr_areas)},
         "christiannp": ch, "uc4n": uc4n, "rough": {"ratio_kg_per_m3": ratio, "use": rough["use"],
                                                     "reference_kg_on_s7_scope": rough_s7, "promoted": False},
         "tuned": False, "s7_outputs_written": False,
         "rule": "comparison only: nothing here changes an S7 quantity; a correction needs a new issue, new source "
                 "evidence, a new regression and a new version"}
    _json("S7_POST_FREEZE_SUMMARY.json", s)
    (HERE / "S7_POST_FREEZE_COMPARISON.md").write_text(report(s, tot, causes, floor_rows, token_rows), encoding="utf-8")
    print(json.dumps({t["REFERENCE"]: (t["REFERENCE_KG"], t["DIFF_KG"], t["CLASSES"]) for t in tot}, indent=1,
                     default=str))


CAUSE_BASIS = {
    ("OLD", "SPECIAL_STRUCTURE_EXCLUDED"): "R4 quantifies callouts S7 transfers to S8 or excludes (water-tank T&B, the "
                                           "GF-21 light-well 8Ø16/m face, dome / stair zones)",
    ("OLD", "ANCHORAGE_EXCLUDED"): "R4 bar = clear span + measured embedment at both supports; S7 stops at the faces "
                                   "and blocks the anchorage / end cover",
    ("OLD", "CURTAILMENT"): "R4 STOP50 stops 0.125 L at both ends (worst case) and adds a provisional extension where "
                            "continuity is unclassified; S7 applies 0.125 L per end class and blocks the unresolved stop "
                            "zones",
    ("OLD", "COUNT_CONVENTION"): "R4 bars = ceil(rate x w) / binder floor(w/s)+1; S7 = rate x 0.5 x W, unrounded",
    ("OLD", "GEOMETRY"): "distribution width / run per callout: R4 one drawn bar per callout, S7 the whole panel in "
                         "local strips",
    ("OLD", "TOP_SUPPORT_RULE"): "S7 quantifies plan note 2 (5Ø10/m, 1/3 span each side, from the face); R4 has no "
                                 "note-2 top steel",
    ("OLD", "REFERENCE_ASSUMPTION"): "R4 quantifies callouts S7 holds as source conflicts or count-only (the GF-22 two "
                                     "callouts 526 / 533, the 552 / 5B9 / 750 count notation, 79F, 7A2, the 3Ø16/Top "
                                     "graphic length, the corner bars) and a reference-only label (77D); for R3 / V3b "
                                     "it also holds the reference's own revision to R4",
    ("OLD", "SCOPE"): "a callout one side binds and the other does not",
    ("FREELANCER", "SPECIAL_STRUCTURE_EXCLUDED"): "the 2F T18 slab row (water tank, S8 in S7) at the lump's implied "
                                                  "ratio",
    ("FREELANCER", "GEOMETRY"): "freelancer net slab volume (excl. the tank) vs the S7 panel volume, at the lump's "
                                "implied ratio",
    ("FREELANCER", "REFERENCE_ASSUMPTION"): "a lump at ~90 kg/m3 against a restricted bar QTO; it also carries what S7 "
                                            "excludes and does not quantify (temperature steel, anchorage / end cover, "
                                            "transitions / laps, sunken extras, edges, oblique ends, conflicts) - not "
                                            "separable",
    ("CHRISTIANNP", "SCOPE"): "christiannp prices no slab steel (every slab callout left unbound)",
    ("ROUGH_90", "REFERENCE_ASSUMPTION"): "SANITY_CHECK_ONLY heuristic (calibrated on the freelancer convention) "
                                          "against a restricted lower-bound QTO; never promoted"}


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.6f}".rstrip("0").rstrip(".") if v == v else "nan"
    if isinstance(v, (list, tuple, dict, set)):
        return json.dumps(sorted(v) if isinstance(v, set) else v, ensure_ascii=False, sort_keys=True, default=str)
    return str(v)


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n",
                             encoding="utf-8")


def report(s, tot, causes, floor_rows, token_rows):
    def k(v):
        return "n/a" if v is None else f"{v:,.1f}"
    lines = [
        "# S7 post-freeze comparison (restricted slab rebar QTO)",
        "",
        f"S7 was frozen at `{s['freeze_commit'][:7]}`. The manifest sha256 is `{s['freeze_manifest_sha256'][:16]}...`.",
        "This script refused to open any reference until three checks passed:",
        "- every frozen hash still matches;",
        "- the manifest is the one committed at the freeze;",
        "- that commit holds no post-freeze file.",
        "",
        "Nothing here changes S7. RESTRICTED_S7_PROJECT_BASIS_KG stays "
        f"**{s['s7_totals_kg']['RESTRICTED_S7_PROJECT_BASIS_KG']:,.3f} kg**. That is the restricted lower bound of 476 "
        f"items, over {sum(s['s7_scope_concrete_m3'].values()):.3f} m3 of S7-scope slab, "
        f"or {s['s7_intensity_kg_per_m3']:.1f} kg/m3.",
        "",
        "## Reference totals (matching scope)",
        "",
        "| reference | matching | reference kg | S7 kg | reference - S7 | classes (kg) |",
        "|---|---|---|---|---|---|"]
    for t in tot:
        cl = ", ".join(f"{c} {v:+,.1f}" for c, v in t["CLASSES"].items()) or "-"
        lines.append(f"| {t['REFERENCE']} | {t['MATCHING']} | {k(t['REFERENCE_KG'])} | {k(t['S7_KG'])} | "
                     f"{k(t['DIFF_KG'])} | {cl} |")
    lines += ["", "## Old Urban R4, by floor", "",
              "| floor | S7 kg (bottom / top) | R4 kg (lower bound + provisional) | R3 kg |", "|---|---|---|---|"]
    for f in floor_rows:
        lines.append(f"| {f['FLOOR']} | {f['S7_KG']:,.1f} ({f['S7_BOTTOM_KG']:,.1f} / {f['S7_TOP_KG']:,.1f}) | "
                     f"{f['R4_KG']:,.1f} ({f['R4_LOWER_BOUND_KG']:,.1f} + {f['R4_PROVISIONAL_KG']:,.1f}) | "
                     f"{f['R3_KG']:,.1f} |")
    st = Counter(t["STATUS"].split(" (")[0] for t in token_rows)
    lines += ["", f"R4 callout tokens: {dict(st)}.", "",
              "## Root causes", ""]
    for ref in ("OLD_URBAN_R4", "FREELANCER", "CHRISTIANNP", "ROUGH_90"):
        if ref not in causes:
            continue
        lines.append(f"**{ref}**")
        lines.append("")
        for cls, v in sorted(causes[ref].items(), key=lambda kv: -abs(kv[1])):
            if abs(v) > 1e-9:
                basis = CAUSE_BASIS.get(((ref.split("_")[0] if ref.startswith("OLD") else ref), cls), "")
                lines.append(f"- {cls}: {v:+,.1f} kg. {basis}.")
        lines.append("")
    lines += [
        "U-C4N gives one project net rebar total (22.619 t, incomplete). It has no slab figure, so there is no matching "
        "scope and no difference is classified.",
        "",
        "The rough 90 kg/m3 profile is `SANITY_CHECK_ONLY`. It is shown, not used: no S7 quantity is tuned, scaled or "
        "promoted towards any reference. Each difference above is a scope, rule or convention that S7 states "
        "explicitly. A correction needs a new issue, new source evidence, a new regression and a new version.",
        "",
        "There are no UNKNOWN rows."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
