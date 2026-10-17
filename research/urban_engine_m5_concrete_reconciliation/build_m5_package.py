"""Build the M5 package: quotation-critical concrete reconciliation and independent quantity audit (ST7757).

    python3 -I research/urban_engine_m5_concrete_reconciliation/build_m5_package.py [--cache DIR] [--no-pdf] [--no-xlsx]

Phase: RECONCILIATION (engine/benchmark_protection). The Urban engine is the frozen M4 engine (35c0587, V3
conventions); it is run first and its register hashed (frozen) before any external figure is read. External figures
are read from their records, explain differences only, and never reach the engine.
Committed: CSV / JSON / MD / SVG / HTML. Generated, git-ignored: the PDF and the Excel workbooks.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG))
import m5_sources as S          # noqa: E402
sys.path.insert(0, str(S.ROOT))
import m5_reconcile as M        # noqa: E402
import m5_tables as T           # noqa: E402
import m5_audits as A           # noqa: E402
import m5_registers as G        # noqa: E402
from engine import benchmark_protection as bp   # noqa: E402


def _csv(rows, fields=None):
    if not rows:
        return ""
    fields = fields or list(rows[0].keys())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    return buf.getvalue()


def _cell(v):
    if isinstance(v, float):
        v = round(v, 6) + 0.0
        return f"{v:.6f}".rstrip("0").rstrip(".") if v else "0"
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, sort_keys=True, default=str)
    return "" if v is None else v


def _json(obj):
    return json.dumps(obj, indent=1, sort_keys=True, default=_jdefault) + "\n"


def _jdefault(o):
    if isinstance(o, (set, tuple)):
        return list(o)
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def compute(cache=None):
    """Everything the package writes, as data (no file is written here)."""
    # 1. the frozen Urban engine first: run, hash, freeze
    R = S.m4_run(cache)
    D = R["generic"]["D"]
    m4_items = sorted((i["item_id"], round(i["base"] or 0, 9), round(i.get("exposure_high") or 0, 9))
                      for i in R["items"] if i["trade"] == "CONCRETE")
    frozen = bp.freeze({"engine_commit": S.M4_FREEZE_COMMIT, "conventions": R["summary"]["conventions"],
                        "concrete_items": m4_items})
    if not bp.may_reconcile(frozen):
        raise RuntimeError("no frozen candidate: reconciliation refused")
    # 2. only now the external records (RECONCILIATION phase, declared)
    ext = bp.withhold({"freelancer": S.freelancer(), "mcp": S.mcp(), "brief": S.brief()}, phase=bp.RECONCILIATION)
    F, MC, BR = ext["payload"]["freelancer"], ext["payload"]["mcp"], ext["payload"]["brief"]
    rate = BR["concrete_rate_kwd_per_m3"]
    # 3. the Urban reference: M4 + S-stage, ownership decisions, M5 items from drawn evidence
    U = M.urban_items(R, S.m1_items())
    decisions, ctx = M.decisions(D, U, S.s9a_bands(), S.s81a_regions(), S.s87_elements())
    plot = M.plot_frame_sh08(D)
    runs = S.boundary_runs(D["sheets"]["SH08"]["sheet"]["box"])
    boundary = M.m5_items(D, U, S.boundary_typical(), runs, plot)
    planted = M.planted_columns(D, R["conv"])
    U.extend(planted)
    if planted:
        decisions.append({"DECISION_ID": "D-06", "KIND": "MISSING_DETECTION_ADDED", "ITEMS": ";".join(p["UID"] for p in planted),
                          "ACTION": "ADD as measured: printed section in the label x storey height",
                          "BASE_M3_MOVED": M.r6(sum(p["BASE"] for p in planted)), "EXPOSURE_HIGH_M3_DROPPED": 0.0,
                          "EVIDENCE": "; ".join(p["SOURCE"] for p in planted) + "; S8.5 records the planted column "
                          "population (SPC-PLANTED_COLUMN)", "NOTE": "M4 reads columns from the column plan only"})
    fam = M.urban_families(U)
    gs, gs_cells = A.gs_audit(D, U, F, MC)
    gb_rows = A.gb_audit(D, U, F)
    slab_rows, slab_floors = A.slab_audit(D, U, F, MC)
    frame = A.frame_per_floor(F, U, MC)
    blind_rows, blind_overlap, _ = A.blinding_audit(D, U, F, BR, gs)
    elements, members = T.elements(F, U, {"boundary": boundary}, rate)
    marks = A.beam_marks(elements)
    fam_rows = T.family_totals(F, U, MC, fam)
    bridge = T.bridge(F, U, fam, gs, rate)
    scope = G.scope_matrix(fam_rows)
    missing = G.missing_register(U, elements, rate)
    dcount = G.double_counts(decisions, gs, F, U, MC, rate)
    expo, scen, ladder, blind_cost, tot = G.exposure(fam, F, rate, blind_rows)
    rfi = G.rfis(fam, U, rate, slab_floors, blind_rows)
    m4_rc = R["summary"]["concrete_rc"]["PLANNING_BASE"]
    vctx = dict(ctx, christiannp_gb_length_m=MC["christiannp_explicit"]["GBP_LENGTH_m"],
                boundary_m=boundary["length_m"], plot=plot, m4_rc=m4_rc)
    checks = G.validation(F, U, D, fam, bridge, gs, elements, members, MC["rows"], vctx, BR)
    engine_change = v4_comparison(R, cache, planted)
    checks.append(engine_change["check"])
    inventory = S.inventory()
    baseline = four_source_baseline(F, R, MC, BR, fam)
    numbers = {"phase": ext["phase"], "freeze": frozen, "rate_kwd_per_m3": rate,
               "freelancer_rc_m3": F["total_rc"], "freelancer_plain_m3": F["categories"]["PLAIN_CONCRETE"]["quantity"],
               "m4_total_incl_plain_m3": R["summary"]["totals"]["CONCRETE"]["PLANNING_BASE"],
               "m4_rc_m3": m4_rc, "m4_plain_m3": fam["BLINDING"]["MEAS_BASE"],
               "urban_m5": {k: M.r6(v) for k, v in tot.items()},
               "families": {f: {k: M.r6(v) if isinstance(v, float) else v for k, v in fam[f].items()} for f in fam},
               "bridge": {"start": bridge["start"], "end": M.r6(bridge["end"]), "closure": bridge["closure_m3"]},
               "ground_slab": {k: (M.r6(v) if isinstance(v, float) else v) for k, v in gs.items()
                               if k != "footprint_parts"},
               "boundary": {k: (M.r6(v) if isinstance(v, float) else v) for k, v in boundary.items()},
               "checks_pass": sum(c["RESULT"] == "PASS" for c in checks), "checks": len(checks),
               "n_urban_items": len(U), "n_freelancer_rows": len(F["rows"]), "n_elements": len(elements)}
    return {"R": R, "D": D, "F": F, "MC": MC, "BR": BR, "U": U, "decisions": decisions, "ctx": ctx, "fam": fam,
            "gs": gs, "gs_cells": gs_cells, "gb_rows": gb_rows, "slab_rows": slab_rows, "slab_floors": slab_floors,
            "frame": frame, "blind_rows": blind_rows, "blind_overlap": blind_overlap, "elements": elements,
            "members": members, "marks": marks, "fam_rows": fam_rows, "bridge": bridge, "scope": scope,
            "missing": missing, "dcount": dcount, "expo": expo, "scen": scen, "ladder": ladder,
            "blind_cost": blind_cost, "rfi": rfi, "checks": checks, "inventory": inventory, "baseline": baseline,
            "numbers": numbers, "engine_change": engine_change, "boundary": boundary, "plot": plot, "runs": runs, "rate": rate, "tot": tot}


V4 = S.ROOT / "engine" / "profiles" / "URBAN_M5_GENERIC_CONVENTIONS_V4.json"


def v4_comparison(R3, cache, planted):
    """Phase 8: the same drawings through the engine with the M5 conventions (V4 = V3 + PLANTED_COLUMN_LABELS).
    Before (V3, the frozen M4 run) / after (V4), item by item; the M5 planted-column items must equal the engine's."""
    from tools import urban_boq_m2 as CLI
    R4 = CLI.compute([str(S.DXF_ST)], conventions=str(V4), profile=str(S.M4_PROFILE), route="G", cache_dir=cache,
                     evidence=str(S.M3_EVIDENCE), arch=[str(S.DXF_ARCH)], evidence_review=str(S.M4_READINGS))
    a = {i["item_id"]: i for i in R3["items"]}
    b = {i["item_id"]: i for i in R4["items"]}
    rows = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x and y and (x["base"], x.get("exposure_high")) == (y["base"], y.get("exposure_high")):
            continue
        it = y or x
        rows.append({"ITEM_ID": k, "TRADE": it["trade"], "FAMILY": it["family"], "STOREY": it["storey"],
                     "V3_M4_BASE": x["base"] if x else None, "V4_M5_BASE": y["base"] if y else None,
                     "CHANGE": "ADDED" if not x else ("REMOVED" if not y else "CHANGED"), "SOURCE": it["source"]})
    conc = [r for r in rows if r["TRADE"] == "CONCRETE"]
    eng = sorted(round(r["V4_M5_BASE"] or 0, 9) for r in conc if r["CHANGE"] == "ADDED")
    m5 = sorted(round(p["BASE"], 9) for p in planted)
    ok = eng == m5 and all(r["CHANGE"] == "ADDED" and r["FAMILY"] == "COLUMNS" for r in conc)
    check = {"CHECK_ID": "IV-19", "WHAT": "engine fix (V4) reproduces the M5 planted-column items and changes nothing "
             "else", "METHOD": "V3 vs V4 engine runs, item by item", "VALUE": f"{len(conc)} concrete items added, "
             f"{sum(eng):.3f} m3", "EXPECTED": f"{len(m5)} items, {sum(m5):.3f} m3", "RESULT": "PASS" if ok else "FAIL",
             "SHARED_CODE": "the M4 intake and detection (both runs)"}
    return {"rows": rows, "check": check, "v3_rc": R3["summary"]["concrete_rc"]["PLANNING_BASE"],
            "v4_rc": R4["summary"]["concrete_rc"]["PLANNING_BASE"], "conventions": R4["summary"]["conventions"]}


def four_source_baseline(F, R, MC, BR, fam):
    q = BR["quoted_totals_m3"]
    tot = {r["category"]: r for r in MC["rows"]}["TOTAL_CONCRETE"]
    m4 = R["summary"]
    rows = [
        {"SOURCE": "FREELANCER (S3.1 lineage of the workbook)", "RC_M3": F["total_rc"],
         "PLAIN_M3": F["categories"]["PLAIN_CONCRETE"]["quantity"], "QUOTED_IN_BRIEF_M3": q["FREELANCER_RC"],
         "RC_EXCLUDES_PLAIN": "YES", "BASIS": "sum of 7 RC categories = leaf rows; plain concrete is a separate row "
         "of its own sheet", "ITEM_LEVEL": "YES (149 leaf rows)"},
        {"SOURCE": "URBAN M4 (frozen engine, route G)", "RC_M3": m4["concrete_rc"]["PLANNING_BASE"],
         "PLAIN_M3": fam["BLINDING"]["MEAS_BASE"], "QUOTED_IN_BRIEF_M3": q["URBAN_M4"],
         "RC_EXCLUDES_PLAIN": "NO in the brief figure: " + f"{m4['totals']['CONCRETE']['PLANNING_BASE']:.3f} = RC "
         f"{m4['concrete_rc']['PLANNING_BASE']:.3f} + plain {fam['BLINDING']['MEAS_BASE']:.3f}",
         "BASIS": "generic route: footings, necks, columns, ground beams + straps, ground slab, beams, slabs, lintels "
         "(no stairs, domes, pool, lift)", "ITEM_LEVEL": "YES"},
        {"SOURCE": "U-C4N (blind AutoCAD MCP run)", "RC_M3": tot["UC4N"], "PLAIN_M3": None,
         "QUOTED_IN_BRIEF_M3": q["UC4N_RC"], "RC_EXCLUDES_PLAIN": "YES (no blinding row in the record)",
         "BASIS": "category values recorded from the owner brief (S3.1 section 16)", "ITEM_LEVEL": "NO (report missing)"},
        {"SOURCE": "christiannp (blind AutoCAD MCP run)", "RC_M3": tot["CHRISTIANNP"], "PLAIN_M3": None,
         "QUOTED_IN_BRIEF_M3": q["CHRISTIANNP_RC"], "RC_EXCLUDES_PLAIN": "YES (A6 states a rule only)",
         "BASIS": "report-explicit values (sealed report not received)", "ITEM_LEVEL": "PARTLY (per floor / per stage)"},
    ]
    for r in rows:
        r["MATCH"] = "YES" if r["QUOTED_IN_BRIEF_M3"] is not None and abs(
            (r["RC_M3"] if "M4" not in r["SOURCE"] else r["RC_M3"] + (r["PLAIN_M3"] or 0)) -
            r["QUOTED_IN_BRIEF_M3"]) < 0.005 else "NO"
    return rows


def write_all(P, out=PKG, pdf=True, xlsx=True):
    files = {
        "00_NUMBERS.json": _json(P["numbers"]),
        "02_SOURCE_SCOPE_MATRIX.csv": _csv(P["scope"]),
        "02A_SOURCE_INVENTORY.csv": _csv(P["inventory"]),
        "02B_FOUR_SOURCE_BASELINE.csv": _csv(P["baseline"]),
        "02C_FAMILY_TOTALS.csv": _csv(P["fam_rows"]),
        "03_ELEMENT_BY_ELEMENT_COMPARISON.csv": _csv(P["elements"]),
        "03A_ELEMENT_MEMBERSHIP.csv": _csv(P["members"]),
        "04_FREELANCER_VS_URBAN_BRIDGE.csv": _csv(P["bridge"]["steps"]),
        "05A_GROUND_SLAB_CELLS.csv": _csv(P["gs_cells"]),
        "05B_GROUND_BEAM_CLASSES.csv": _csv(P["gb_rows"]),
        "06A_SLAB_PANELS.csv": _csv(P["slab_rows"]),
        "06B_SLAB_FLOORS.csv": _csv(P["slab_floors"]),
        "07A_MARK_CROSSWALK.csv": _csv(P["marks"]),
        "07B_FRAME_PER_FLOOR.csv": _csv(P["frame"]),
        "09A_BLINDING_OPTIONS.csv": _csv(P["blind_rows"]),
        "10_MISSING_CONCRETE_REGISTER.csv": _csv(P["missing"]),
        "11_DOUBLE_COUNT_REGISTER.csv": _csv(P["dcount"]),
        "11A_M5_OWNERSHIP_DECISIONS.csv": _csv(P["decisions"]),
        "12_QUOTATION_COST_EXPOSURE.csv": _csv(P["expo"]),
        "12A_QUOTATION_SCENARIOS.csv": _csv(P["scen"]),
        "13_PRIORITY_RFIS.csv": _csv(P["rfi"]),
        "15A_INDEPENDENT_CHECKS.csv": _csv(P["checks"]),
        "18_ENGINE_CHANGE_V3_TO_V4.csv": _csv(P["engine_change"]["rows"]),
    }
    import m5_docs as DOC
    files.update(DOC.documents(P))
    import m5_visual as V
    svgs, html = V.visuals(P)
    for name, text in svgs.items():
        files["visual/" + name] = text
    files["14_VISUAL_CONCRETE_QA.html"] = html
    for name, text in files.items():
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    made = {}
    if pdf:
        made["pdf"] = V.to_pdf(out / "14_VISUAL_CONCRETE_QA.html", out / "14_VISUAL_CONCRETE_QA.pdf")
    if xlsx:
        import m5_workbook as W
        made["xlsx"] = W.workbooks(P, out)
    return files, made


def main(argv):
    a = {argv[i]: (argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else True)
         for i in range(len(argv)) if argv[i].startswith("--")}
    P = compute(a.get("--cache") if isinstance(a.get("--cache"), str) else None)
    files, made = write_all(P, pdf="--no-pdf" not in a, xlsx="--no-xlsx" not in a)
    digest = hashlib.sha256("".join(f"{k}\n{v}" for k, v in sorted(files.items())).encode()).hexdigest()
    print(json.dumps({"files": len(files), "content_sha256": digest, "made": made,
                      "checks": f"{P['numbers']['checks_pass']} / {P['numbers']['checks']}",
                      "urban_m5_rc_base": P["numbers"]["urban_m5"]["MEAS_BASE"]}, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
