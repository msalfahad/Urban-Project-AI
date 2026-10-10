"""ALSENAN ROUND 3 - build and freeze the structural rebar truth registers (V3b and Round 2 are never written).

    python3 research/alsenan_rebar_truth_03/build_rebar_v3.py <work_dir | ctx.pkl> [--twice]

1. load the Alsenan context (pickled by the round-2 build, or rebuilt with alsenan_v3b.build);
2. read ST7757.dxf (source reader V2) and the CB schedule graphics;
3. alsenan_rebar_v3.build -> components / populations; invariants; BBS on the eligible components;
4. write the registers + REBAR_BAR_BY_BAR_AUDIT.md + INDEX.json (sha256 per file). --twice builds a second time from
   the same inputs and refuses to write if any output differs.
No benchmark register or value is read here (benchmark firewall; tested). post_freeze_rebar_compare.py runs later.
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "research" / "external_engine_lab"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_rebar_v3 as R3  # noqa: E402
import alsenan_structural_source_v2 as SRC  # noqa: E402
from engine.source import rebar_model as RM  # noqa: E402

OUT = HERE / "registers"
R1_GZB = ROOT / "research/alsenan_control_plane_01/registers/STRUCTURAL_POPULATION_COVERAGE_REGISTER.json"
LAP_BBS = ("LAP-TENSION-70D", 70)


def _num(o):
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, float):
        return round(o, 6)
    raise TypeError(type(o))


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item"):
        o = o.item()
    if isinstance(o, float):
        return round(o, 6)
    return o


def _text(o):
    return json.dumps(_clean(o), indent=1, ensure_ascii=False, default=_num) + "\n"


def load(src):
    p = Path(src)
    if p.is_file():
        return pickle.load(open(p, "rb"))
    import alsenan_v3b as V3B
    return V3B.build(p, "rebar-truth-round-3")


def old_v3b(ctx):
    """Old V3b net / technical kg per occurrence prefix (read from the in-memory V3b sets; never written)."""
    acc = defaultdict(lambda: {"net_kg": 0.0, "tech_kg": 0.0})
    for s in ctx["v3b"]["rebar"]["weighed"]:
        acc[(s["population"], s["ref"])]["net_kg"] += s.get("net_kg") or 0.0
        acc[(s["population"], s["ref"])]["tech_kg"] += s.get("tech_kg") or 0.0
    return acc


def _old(acc, pop, prefix):
    n = t = 0.0
    for (p, ref), v in acc.items():
        if p == pop and ref.startswith(prefix):
            n += v["net_kg"]
            t += v["tech_kg"]
    return {"v3b_net_kg": n, "v3b_technical_kg": t}


def build(ctx):
    gzb = json.loads(R1_GZB.read_text())["ground_zone_binding"]
    b = R3.build(ctx, gzb)
    comps, pops = b.comps, b.pops
    cby = defaultdict(list)
    for c in comps:
        cby[c["population_id"]].append(c)
    trade = RM.totals(pops)
    ps = {p["pop_id"]: p["release_state"] for p in pops}
    bb = RM.bbs(comps, ps, lap_factor=LAP_BBS[1], lap_rule_id=LAP_BBS[0])
    viol = {"completeness": RM.check_completeness(b.rc_occ, pops, comps),
            "duplicates": RM.check_duplicates(comps, pops),
            "provenance": RM.check_provenance(comps),
            "mass": RM.check_mass(comps, pops, trade, bb),
            "bbs_eligibility": RM.check_bbs_eligibility(bb, comps, ps)}
    viol.update(R3.project_invariants(b))
    acc = old_v3b(ctx)
    regs = {}
    sha = b.sha

    # ------------------------------------------------------------------ source definitions + authorities
    used_defs = set()
    for c in comps:
        d = (c["source"] or {}).get("definition")
        if d and c["net_kg"] > 0:
            used_defs.add(d)
    defs = [x for x in b.defs["definitions"]]
    regs["REBAR_SOURCE_DEFINITION_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_SOURCE_DEFINITION_V3", "drawing": "ST7757.dxf", "source_sha256": sha,
        "cover_rules": R3.COVER, "lap_rules": R3.LAP, "weight_formula": RM.KG_FORMULA,
        "count_rules": {"COUNT_ABSOLUTE": "printed count", "COUNT_PER_METRE_LB_PLUS_END_BAR":
                        "verified = ceil(rate x distribution); convention = ceil(distribution / spacing) + 1 (PROVISIONAL "
                        "end bar)", "SLAB_BINDER_COUNT_SPLIT": "binder floor(w/s)+1 kept as the convention count; "
                        "verified part = ceil(rate x w)"},
        "definitions": [{"element": x["element"], "type": x["type"], "block": x["block"],
                         "insert_handle": x["insert_handle"], "page": x["page"],
                         "interpretation_state": x["interpretation_state"], "fields": x["fields"],
                         "feeds_quantity": f"{x['element']} {x['type']}" in used_defs} for x in defs],
        "conflicts": b.defs["conflicts"],
        "definition_consumption_pct": 100.0 * sum(1 for x in defs if f"{x['element']} {x['type']}" in used_defs) / len(defs),
        "rule": "every quantity traces to one of these definitions (or a carried V3b set); T/M and LOAD are loads"}

    # ------------------------------------------------------------------ occurrences + completeness
    occ_rows = []
    for p in pops:
        occ_rows.append({k: p[k] for k in ("pop_id", "element_type", "occurrence_id", "level", "occurrence_state",
                                           "occurrence_why", "release_state", "verified_complete_kg", "lower_bound_kg",
                                           "provisional_kg", "budget_kg", "audit_kg", "missing_components",
                                           "component_states", "source")})
    by_type = defaultdict(lambda: defaultdict(float))
    for p in pops:
        t = by_type[p["element_type"]]
        for f in ("verified_complete_kg", "lower_bound_kg", "provisional_kg", "budget_kg", "audit_kg"):
            t[f] += p[f]
        t["populations"] += 1
        t["state:" + p["release_state"]] += 1
    regs["REBAR_OCCURRENCE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_OCCURRENCE_V3", "trade_totals": trade, "by_element_type": by_type,
        "rows": occ_rows, "rc_occurrences": len(b.rc_occ),
        "rule": "every reinforced-concrete occurrence has at least one population record; one release state each"}
    req = [c for c in comps if c["required"]]
    non_nis = [p for p in pops if p["release_state"] != RM.NIS]
    regs["REBAR_COMPONENT_COMPLETENESS_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_COMPONENT_COMPLETENESS_V3",
        "population_completeness_pct": 100.0 * sum(1 for p in non_nis if p["release_state"] == RM.VC) / len(non_nis),
        "component_completeness_pct": 100.0 * sum(1 for c in req if c["state"] == RM.COMPLETE) / len(req),
        "component_states": dict(Counter(c["state"] for c in comps)),
        "required_component_states": dict(Counter(c["state"] for c in req)),
        "populations": [{"pop_id": p["pop_id"], "release_state": p["release_state"],
                         "components": [{"comp_id": c["comp_id"], "role": c["bar_role"], "span": c["span"],
                                         "layer": c["layer"], "state": c["state"], "required": c["required"],
                                         "blocked_parts": c["blocked_parts"], "why": c["why"]} for c in cby[p["pop_id"]]],
                         "missing_components": p["missing_components"]} for p in pops],
        "invariant_violations": viol["completeness"],
        "rule": "VERIFIED_COMPLETE only when every required component is COMPLETE / NOT_REQUIRED; one BLOCKED / PARTIAL "
                "/ PROVISIONAL required component caps the population at LOWER_BOUND"}

    # ------------------------------------------------------------------ footings
    frows = []
    for p in [p for p in pops if p["element_type"].startswith("FOOTING") and p["occurrence_id"].startswith("FOOTING:")]:
        typ, n = p["occurrence_id"].split(":")[1].split("#")
        df = (b.dmap.get(("FOOTING", typ)) or b.dmap.get(("FOOTING_2_LAYER", typ)) or [{}])[0]
        F = df.get("fields", {})
        cs = []
        for c in cby[p["pop_id"]]:
            cs.append({"role": c["bar_role"], "dia_mm": c["dia_mm"], "count_mode": c["count_mode"],
                       "rate_per_m": c["rate_per_m"], "spacing_mm": c["spacing_mm"],
                       "count_verified": (c["count"] or {}).get("verified"),
                       "count_convention": (c["count"] or {}).get("convention"),
                       "distribution_m": (c["count"] or {}).get("distribution_m"),
                       "bar_length_m": c["verified_length_m"] + c["provisional_length_m"],
                       "kg_per_m": c["unit_weight_kg_m"], "verified_kg": c["verified_kg"],
                       "provisional_kg": c["provisional_kg"], "audit_kg": c["audit_kg"], "state": c["state"],
                       "why": c["why"], "formula": c["formula"], "cover_rule_id": c["cover_rule_id"]})
        frows.append({"occurrence": p["occurrence_id"], "type": typ, "element_type": p["element_type"],
                      "L_m": (F.get("L_cm") or 0) / 100, "W_m": (F.get("W_cm") or 0) / 100,
                      "D_m": (F.get("D_cm") or 0) / 100, "cover_m": 0.07, "occurrence_state": p["occurrence_state"],
                      "release_state": p["release_state"], "components": cs,
                      "new_verified_kg": p["verified_complete_kg"] + p["lower_bound_kg"],
                      "new_provisional_kg": p["provisional_kg"], "audit_kg": p["audit_kg"],
                      "old": _old(acc, "FOOTINGS", f"{typ} #{n} ")})
    regs["FOOTING_REBAR_REGISTER_V3"] = {"SCHEMA": "URBAN_ALSENAN_FOOTING_REBAR_V3", "rows": frows,
                                         "count_method": "FOOTING_BAR_COUNT_METHOD.md",
                                         "rule": "FT counts are printed; FTB / FF counts are bars per metre over side - "
                                                 "2 x cover (verified ceil, provisional end bar); BOXED kept raw"}

    # ------------------------------------------------------------------ beams + straps
    brows = []
    for p in [p for p in pops if p["element_type"] in ("BEAM", "STRAP_BEAM")]:
        parts = p["occurrence_id"].split(":")
        prefix = (f"{parts[1]} {parts[2]} {parts[3]} " if p["element_type"] == "BEAM" else
                  f"FOUNDATION {parts[1]} {parts[2]} ")
        brows.append({"occurrence": p["occurrence_id"], "element_type": p["element_type"],
                      "occurrence_state": p["occurrence_state"], "why": p["occurrence_why"],
                      "release_state": p["release_state"], "missing": p["missing_components"],
                      "components": [{"role": c["bar_role"], "dia_mm": c["dia_mm"], "count": (c["count"] or {}).get("verified"),
                                      "count_convention": (c["count"] or {}).get("convention"),
                                      "verified_length_m": c["verified_length_m"],
                                      "provisional_length_m": c["provisional_length_m"], "verified_kg": c["verified_kg"],
                                      "provisional_kg": c["provisional_kg"], "state": c["state"], "why": c["why"],
                                      "source_raw": (c["source"] or {}).get("raw")} for c in cby[p["pop_id"]]],
                      "new_verified_kg": p["verified_complete_kg"] + p["lower_bound_kg"],
                      "new_provisional_kg": p["provisional_kg"], "audit_kg": p["audit_kg"],
                      "old": _old(acc, "BEAMS", prefix)})
    regs["BEAM_REBAR_REGISTER_V3"] = {"SCHEMA": "URBAN_ALSENAN_BEAM_REBAR_V3", "rows": brows,
                                      "strap_conflicts": b.registers["STRAP_CONFLICTS"],
                                      "rule": "verified core = clear span; embedment to centrelines PROVISIONAL; end "
                                              "anchorage BLOCKED; side bars BLOCKED where depth > 60 (note 21 / REMARKS)"}

    # ------------------------------------------------------------------ continuous beams
    cbrows = []
    ROLE_ORDER = ("BOTTOM", "SUPPORT_TOP", "CONTINUOUS_TOP", "SPAN_TOP", "STIRRUPS", "SIDE_BARS")
    for p in [p for p in pops if p["element_type"] == "CONTINUOUS_BEAM"]:
        matrix = []
        for c in sorted(cby[p["pop_id"]], key=lambda c: (ROLE_ORDER.index(c["bar_role"]), str(c["span"]))):
            matrix.append({"component": f"{c['bar_role']} {c['span'] or ''}".strip(), "state": c["state"],
                           "count": (c["count"] or {}).get("verified"), "dia_mm": c["dia_mm"],
                           "core_m": c["verified_length_m"], "template_m": c["provisional_length_m"],
                           "blocked_parts": c["blocked_parts"], "verified_kg": c["verified_kg"],
                           "provisional_kg": c["provisional_kg"], "audit_kg": c["audit_kg"],
                           "laps": (c.get("laps") or {}).get("state"), "why": c["why"]})
        cbrows.append({"occurrence": p["occurrence_id"], "occurrence_state": p["occurrence_state"],
                       "why": p["occurrence_why"], "release_state": p["release_state"], "component_matrix": matrix,
                       "lower_bound_kg": p["lower_bound_kg"], "provisional_kg": p["provisional_kg"],
                       "audit_kg": p["audit_kg"]})
    regs["CONTINUOUS_BEAM_BAR_GEOMETRY_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_CB_BAR_GEOMETRY_V1", "snap_fraction": R3.SNAP_FRAC,
        "template_variants": b.cbg["template_variants"], "finding": b.cbg["finding"],
        "geometry": b.registers["CB_GEOMETRY"], "occurrences": cbrows,
        "definitions_without_occurrence": b.registers["CB_DEFINITIONS_WITHOUT_OCCURRENCE"],
        "rule": "bar role from geometry (row, support straddle, hooks); count / diameter from a one-to-one bound label "
                "(attribute or split TEXT callout); length = whole spans (schedule attributes, verified) + template "
                "fractions x real span (provisional); hooks / anchorage not dimensioned = BLOCKED; T/M = design load"}

    # ------------------------------------------------------------------ columns
    rec = b.registers["COLUMN_RECONCILIATION"]
    d5 = [r for r in rec if r["release_state"] == RM.BLK]
    d5_ver = 0.0
    for r in d5:
        d5_ver += sum(c["verified_kg"] for c in cby[f"POP:{r['occurrence']}"])
    regs["COLUMN_REBAR_RECONCILIATION"] = {
        "SCHEMA": "URBAN_ALSENAN_COLUMN_REBAR_RECONCILIATION_V3", "rows": rec,
        "valid_lower_bound_kg": sum(p["lower_bound_kg"] for p in pops if p["element_type"] == "COLUMN"),
        "valid_provisional_kg": sum(p["provisional_kg"] for p in pops if p["element_type"] == "COLUMN"),
        "d5_blocked": {"occurrences": len(d5), "audit_kg_total": sum(r["kg_if_geometry_accepted"] for r in d5),
                       "audit_kg_verified_equivalent": d5_ver,
                       "state": "BLOCKED_OCCURRENCE_NOT_ESTABLISHED"},
        "rule": "D5 occurrences keep their definitions and an audit weight; they never enter a verified total"}

    # ------------------------------------------------------------------ slab / ground slab / stairs
    slab_pops = [p for p in pops if p["element_type"] in ("SLAB", "GROUND_SLAB", "STAIR")]
    tb_add = sum(c["verified_kg"] + c["provisional_kg"] for c in comps if c["comp_id"].endswith("|T&B_TOP"))
    regs["SLAB_REBAR_AUDIT"] = {
        "SCHEMA": "URBAN_ALSENAN_SLAB_REBAR_AUDIT_V3", "t_and_b": b.registers["SLAB_TB"],
        "t_and_b_top_layer_added_kg": tb_add,
        "dedupe_audit": {"rows": b.registers["SLAB_TB"]["dedupe_audit"],
                         "finding": "both DUPLICATE_LABEL rows repeat the same bar family, direction, panel and layer "
                                    "flag as an earlier label (same text, count and length) - a repeated label, not a "
                                    "second layer; the dedupe key includes the top / bottom flag, so a genuine second "
                                    "layer is never collapsed"},
        "ground_slab_scope": b.registers["GROUND_SLAB_SCOPE"],
        "stairs": b.registers["STAIR_APPLICABILITY"],
        "populations": [{k: p[k] for k in ("pop_id", "release_state", "lower_bound_kg", "provisional_kg",
                                           "audit_kg", "occurrence_why")} for p in slab_pops],
        "rule": "T&B applied only with a strong positional binding; ground-slab scope from positive evidence (Q-S4 "
                "open: min -> max is never used); stairs bound only when the detail is proved applicable"}

    # ------------------------------------------------------------------ mass, BBS, provenance, gates
    regs["REBAR_MASS_CONSERVATION_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_MASS_CONSERVATION_V3",
        "component_kg": {f: sum(c[f] for c in comps) for f in ("verified_kg", "provisional_kg", "audit_kg")},
        "released_component_verified_kg": sum(c["verified_kg"] for c in comps if ps[c["population_id"]] in (RM.VC, RM.LB)),
        "population_kg": {f: sum(p[f] for p in pops) for f in ("verified_complete_kg", "lower_bound_kg",
                                                               "provisional_kg", "budget_kg", "audit_kg")},
        "trade_kg": trade, "bbs_total": bb["total"],
        "checks": {k: {"violations": v, "pass": not v} for k, v in viol.items()},
        "rule": "sum(component) = population = trade per bucket; BBS used >= net; purchased >= used; waste = purchased "
                "- used; no negative; no component in two populations; NET and PROCUREMENT never added together"}
    exc = Counter(e["comp_id"].split("|")[0] for e in bb["excluded"])
    regs["BBS_REGISTER_V3"] = {"SCHEMA": "URBAN_ALSENAN_BBS_V3", **{k: v for k, v in bb.items() if k != "included"},
                               "included_components": len(bb["included"]),
                               "excluded_by_population": dict(sorted(exc.items())),
                               "lap_rule": LAP_BBS[0]}
    regs["REBAR_PROVENANCE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_PROVENANCE_V3", "drawing_sha256": sha,
        "rows": [{"comp_id": c["comp_id"], "occurrence": c["occurrence_id"], "role": c["bar_role"],
                  "source": c["source"], "count_rule": (c["count"] or {}).get("rule_id"),
                  "count_formula": (c["count"] or {}).get("formula"), "formula": c["formula"],
                  "cover_rule_id": c["cover_rule_id"], "lap": (c.get("laps") or {}).get("rule"),
                  "weight_formula": c["weight_formula"], "state": c["state"], "verified_kg": c["verified_kg"],
                  "provisional_kg": c["provisional_kg"], "audit_kg": c["audit_kg"]} for c in comps],
        "violations": viol["provenance"]}
    regs["REBAR_GATE_TRANSITIONS"] = gates(viol)
    return regs, b, bb


GATES = [
    ("G11", "PASS", "two-layer FTB: both layers x both directions, bars per metre over side - 2 x cover (never an "
                    "absolute count); FF straight mesh consumed",
     "test_G11_two_layer_footing_quantity_consumer"),
    ("G13", "PASS", "SB1 / SB3 strap consumer (bottom / top / stirrups); SB2 BLOCKED SOURCE_CONFLICT (no row chosen)",
     "test_G13_strap_rebar_quantity_consumer"),
    ("G15", "XFAIL", "ground-slab scope: Q-S4 open; the bound cell is released as provisional with a BLOCKED scope "
                     "remainder - min -> max is not used", "test_G15_ground_zone_not_bound_by_minimum_area"),
    ("G23", "XFAIL", "stair detail applicability not proved (p.16 typical 0.00 / +2.00 / +4.00 vs rises 4.50 / 4.20)",
     "test_G23_stair_rebar_bound_to_typical_layout"),
    ("G24", "PASS", "continuous-beam component accounting: every CB occurrence has a component matrix with a state "
                    "per bar role / span", "test_G24_cb_component_accounting"),
    ("G25", "PASS", "rebar mass conservation", "test_G25_rebar_mass_conservation"),
    ("G26", "PASS", "source provenance on every quantity component", "test_G26_rebar_source_provenance"),
    ("G27", "PASS", "no benchmark leakage into the rebar builders", "test_G27_no_benchmark_leakage"),
    ("G28", "PASS", "no kg/m3 quantity production", "test_G28_no_ratio_quantity"),
    ("G29", "PASS", "no duplicate component / occurrence", "test_G29_no_duplicate_component"),
    ("G30", "PASS", "no incomplete population marked complete", "test_G30_no_incomplete_population_complete"),
    ("G31", "PASS", "every reinforced-concrete occurrence has a rebar population", "test_G31_every_rc_occurrence_has_rebar"),
]


def gates(viol):
    return {"SCHEMA": "URBAN_ALSENAN_REBAR_GATE_TRANSITIONS_V3",
            "rows": [{"gate": g, "final_state": st, "evidence": ev,
                      "proving_test": f"tests/alsenan_rebar_truth/test_rebar_truth_r3.py::{t}"} for g, st, ev, t in GATES],
            "round2_superseded": ["tests/alsenan_control_plane/test_control_plane_r2_gates.py::test_G11_two_layer_footing_"
                                  "quantity_consumer (xfail -> R3 PASS)",
                                  "tests/alsenan_control_plane/test_control_plane_r2_gates.py::test_G13_strap_rebar_"
                                  "quantity_consumer (xfail -> R3 PASS)"],
            "invariants_clean": all(not v for v in viol.values())}


def audit_md(b) -> str:
    """Human-readable bar-by-bar audit, grouped by element type, definition type, role and diameter."""
    g = defaultdict(lambda: {"occ": set(), "n": 0, "len": [], "tl": 0.0, "kg": 0.0, "pk": 0.0, "ak": 0.0,
                             "states": Counter(), "rate": None, "src": None, "rel": Counter()})
    pstate = {p["pop_id"]: p["release_state"] for p in b.pops}
    for c in b.comps:
        if c["element_type"] in R3.Build.CARRIED or c["state"] == RM.NOT_REQUIRED:
            continue
        parts = c["occurrence_id"].split(":")
        typ = parts[2] if parts[0] in ("BEAM", "CB", "COLUMN") else parts[1].split("#")[0] if parts[0] == "FOOTING" \
            else parts[1]
        k = (c["element_type"], typ, c["bar_role"] + (f" {c['layer']}" if c["layer"] and c["element_type"].startswith(
            "FOOTING") else ""), c["dia_mm"])
        r = g[k]
        r["occ"].add(c["occurrence_id"])
        n = (c["count"] or {}).get("verified")
        r["n"] += n or 0
        L = c["verified_length_m"] + c["provisional_length_m"]
        if L:
            r["len"].append(L)
        r["tl"] += (n or 0) * L
        r["kg"] += c["verified_kg"]
        r["pk"] += c["provisional_kg"]
        r["ak"] += c["audit_kg"]
        r["states"][c["state"]] += 1
        r["rel"][pstate.get(c["population_id"])] += 1
        r["rate"] = c["rate_per_m"] or r["rate"]
        r["src"] = (c["source"] or {}).get("locator", "")[:40]
    lines = ["# Alsenan Round 3 - bar-by-bar reinforcement audit", "",
             "One row per element type x definition type x bar role x diameter, summed over occurrences.",
             "Verified kg = verified count x verified length x D^2/162; provisional = template / hook / convention "
             "parts; audit = blocked populations (never released). BLOCKED components with no count show 0.", "",
             "| ELEMENT | TYPE | OCC | ROLE | DIA | COUNT / RATE | BAR LENGTH m (min-max) | TOTAL LENGTH m | KG/M | "
             "VERIFIED KG | PROVISIONAL KG | AUDIT KG | COMPONENT STATES | POPULATION STATES | SOURCE |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(g, key=lambda k: (k[0], str(k[1]), k[2], k[3] or 0)):
        r = g[k]
        cr = f"{r['rate']:g}/m (n={r['n']})" if r["rate"] else str(r["n"])
        bl = f"{min(r['len']):.3f}-{max(r['len']):.3f}" if r["len"] else "-"
        km = f"{RM.kgm(k[3]):.4f}" if k[3] else "-"
        st = ", ".join(f"{s}:{n}" for s, n in sorted(r["states"].items()))
        rs = ", ".join(f"{s}:{n}" for s, n in sorted((str(a), b_) for a, b_ in r["rel"].items()))
        lines.append(f"| {k[0]} | {k[1]} | {len(r['occ'])} | {k[2]} | {('Ø' + str(k[3])) if k[3] else '-'} | {cr} | {bl} | "
                     f"{r['tl']:.2f} | {km} | {r['kg']:.1f} | {r['pk']:.1f} | {r['ak']:.1f} | {st} | {rs} | {r['src']} |")
    return "\n".join(lines) + "\n"


def main(src, twice=False):
    ctx = load(src)
    regs, b, bb = build(ctx)
    texts = {k: _text(v) for k, v in regs.items()}
    texts_md = {"REBAR_BAR_BY_BAR_AUDIT.md": audit_md(b)}
    if twice:
        again, b2, _ = build(ctx)
        diff = [k for k, v in again.items() if _text(v) != texts[k]]
        if audit_md(b2) != texts_md["REBAR_BAR_BY_BAR_AUDIT.md"]:
            diff.append("REBAR_BAR_BY_BAR_AUDIT.md")
        if diff:
            raise SystemExit(f"NON-DETERMINISTIC: {diff}")
    OUT.mkdir(parents=True, exist_ok=True)
    idx = {}
    for k, t in texts.items():
        (OUT / f"{k}.json").write_text(t)
        idx[k] = hashlib.sha256(t.encode()).hexdigest()
    (HERE / "REBAR_BAR_BY_BAR_AUDIT.md").write_text(texts_md["REBAR_BAR_BY_BAR_AUDIT.md"])
    doc = {"SCHEMA": "URBAN_ALSENAN_REBAR_TRUTH_R3_INDEX", "registers": idx, "built_twice_identical": bool(twice),
           "audit_md_sha256": hashlib.sha256(texts_md["REBAR_BAR_BY_BAR_AUDIT.md"].encode()).hexdigest(),
           "st7757_sha256": b.sha, "rule": "frozen before the benchmark comparison (post_freeze_rebar_compare.py)"}
    (OUT / "INDEX.json").write_text(json.dumps(doc, indent=1) + "\n")
    t = regs["REBAR_OCCURRENCE_REGISTER"]["trade_totals"]
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in t.items()})
    print("invariants clean:", regs["REBAR_GATE_TRANSITIONS"]["invariants_clean"])
    for k, h in idx.items():
        print(f"{k:42s} {h[:12]}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0], "--twice" in sys.argv)
