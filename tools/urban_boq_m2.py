"""URBAN BOQ M2 - the one-command BOQ with ROUTE G, the generic engine, on top of the frozen M1 pipeline.

    python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --out OUT [--profile P.json] [--route auto|A|B|G|C]
                                       [--conventions C.json] [--set ID=VALUE ...] [--no-pdf] [--no-xlsx]
                                       [--cache DIR] [--evidence DETAIL_EVIDENCE.json]

tools/urban_structural_boq.py (M1) is frozen (research/alsenan_m1_usable_boq/06_M1_FREEZE_MANIFEST.json) and is
used here unchanged: routes A / B / C are delegated to it as they are. This module adds:

    ROUTE G   the generic engine (engine.source.generic_route) reads sheets, schedules, footings, columns, beams,
              slabs and bar models from any DXF with no project register. A profile (optional) carries only printed
              values the drawing lacks (storey heights, typical ground-beam classes). The default for a drawing set
              the project registry does not know and that has no takeoff profile.
    outputs   COVERAGE_RISK.csv, REBAR_COMPLETENESS.csv, a "C NOT DETECTED" section in the contractor BOQ (every
              family the generic engine cannot quantify: with its drawing evidence, or "no label found - confirm
              absent"), overlays/*.svg + OVERLAYS.html -> VISUAL_QA_OVERLAYS.pdf, and the matching Excel sheets.

A new project is never VERIFIED: source-complete items are PROVISIONAL with support SOURCE_COMPLETE_UNREVIEWED.
No prices. Nothing here is engineering approval.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import boq_m1_xlsx as XL                      # noqa: E402
from engine.source import detail_evidence as DE           # noqa: E402
from engine.source import drawing_inventory as DI         # noqa: E402
from engine.source import family_coverage as FC           # noqa: E402
from engine.source import generic_route as GR             # noqa: E402
from engine.source import provisional_estimate as PE      # noqa: E402
from tools import m2_overlay as OV                        # noqa: E402
from tools import urban_intake as UI                      # noqa: E402
from tools import urban_structural_boq as M1              # noqa: E402

POLICY_ID = "URBAN_BOQ_M2"
GENERIC_CONVENTIONS = "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json"
BANNER = M1.BANNER


def _code_digest():
    """digest of the code an intake depends on: a cached intake is reused only by the same code."""
    import hashlib
    h = hashlib.sha256()
    for rel in ("tools/urban_intake.py", "engine/source/cad/kernel_ezdxf.py", "engine/source/realised.py"):
        p = ROOT / rel
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def cached_intake(dxf, cache_dir=None):
    """the intake of one DXF, from the cache when the same file (sha256) was read by the same code before. The
    cache holds this tool's own pickles only (never a downloaded file); delete the folder to clear it."""
    if not cache_dir:
        return UI.read(dxf["path"]), "NO_CACHE"
    import pickle
    c = Path(cache_dir)
    c.mkdir(parents=True, exist_ok=True)
    key = c / f"intake_{dxf['sha256'][:24]}_{_code_digest()}.pkl"
    if key.exists():
        with key.open("rb") as fh:
            return pickle.load(fh), "CACHE_HIT"
    I = UI.read(dxf["path"])
    with key.open("wb") as fh:
        pickle.dump(I, fh)
    return I, "CACHE_MISS_STORED"


def load_evidence(path):
    """a detail-evidence document (tools/pdf_evidence.py or a manual transcription); refused when it fails the schema
    check (a record that is not what it claims never reaches a quantity)."""
    if not path:
        return None
    ev = json.loads(Path(path).read_text(encoding="utf-8"))
    bad = DE.validate(ev)
    if bad:
        raise M1.PipelineError(f"detail evidence {path} fails validation: {bad[:5]}")
    return ev


def route_generic(inputs, conv_path, overrides, profile, cache_dir=None, evidence=None):
    dxf = next((r for r in inputs if r["kind"] == "DXF" and "error" not in r), None)
    if dxf is None:
        raise M1.PipelineError("route G needs a readable DXF (a DWG must be converted to DXF first; a PDF alone "
                               "carries no measurable geometry here)")
    I, cache_state = cached_intake(dxf, cache_dir)
    generic = json.loads((ROOT / (conv_path or GENERIC_CONVENTIONS)).read_text(encoding="utf-8"))
    # M3: an unmarked ground-beam network is searched at the printed typical widths only
    D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(GR.merge_conventions(generic, profile, overrides)))

    def build(ov):
        conv = GR.merge_conventions(generic, profile, ov)
        items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv), evidence=evidence)
        return conv, items, reg, risk
    conv, items, reg, risk = build(overrides)
    exc = [{"EXCEPTION_ID": f"CR-{k:04d}", "KIND": "COVERAGE_RISK:" + r["KIND"], "FAMILY": "", "SHEET": r["WHERE"],
            "DETAIL": str(r["DETAIL"])[:300], "LOCATION": ""} for k, r in enumerate(risk, 1)]
    return {"items": items, "conv": conv, "coverage": [], "rebuild": lambda ov: build(dict(overrides, **ov))[1],
            "frozen": [], "exceptions": exc, "adapter": None,
            "generic": {"D": D, "register": reg, "risk": risk, "intake_cache": cache_state, "evidence": evidence}}


def not_detected_lines(cov):
    """BOQ section C: one line per family outside the core six, with its coverage state (family_coverage). A family
    with no evidence is 'confirm absent', never 'absent'."""
    out = []
    for k, c in enumerate(cov, 1):
        text = f"{c['FAMILY']}: {c['STATE']}" + (f" in {c['QUANTIFIED_IN']}" if c["QUANTIFIED_IN"] else "") + \
            (f" - {c['EVIDENCE']}" if c["EVIDENCE"] else "") + f"; {c['REASON']}" + \
            (f"; needs {c['NEEDED']}" if c["NEEDED"] else "")
        out.append({"ITEM": f"C.{k:02d}", "SECTION": "C FAMILY COVERAGE (NOT DETECTED / NOT QUANTIFIED)",
                    "FAMILY": c["FAMILY"], "DESCRIPTION": text, "UNIT": "-", "EVIDENCE": c["STATE"]})
    return out


def missing_steel_lines(rc):
    """BOQ section D: every family / storey with components that carry no (or only part of their) bar quantity.
    A count, never a quantity: missing steel is never written as 0 kg."""
    out = []
    for k, r in enumerate([r for r in rc["by_family_storey"] if r["MISSING_STEEL_COMPONENTS"]], 1):
        out.append({"ITEM": f"D.{k:02d}", "SECTION": "D REINFORCEMENT NOT QUANTIFIED (MISSING STEEL)",
                    "FAMILY": r["FAMILY"], "UNIT": "-",
                    "DESCRIPTION": f"{r['FAMILY']} {r['STOREY']}: {r['MISSING_STEEL_COMPONENTS']} of {r['COMPONENTS']} "
                                   f"components without a full bar quantity (MISSING_DATA {r['MISSING_DATA']}, "
                                   f"PARTIAL_MISSING {r['PARTIAL_MISSING']}, unresolved steel items "
                                   f"{r['UNRESOLVED_STEEL_ITEMS']}) - not zero, not in any total",
                    "EVIDENCE": "MISSING_STEEL", "N_UNRESOLVED": r["MISSING_STEEL_COMPONENTS"]})
    return out


def missing_steel_html(rc):
    rows = [r for r in rc["by_family_storey"] if r["MISSING_STEEL_COMPONENTS"]]
    head = ("<h2 class='pb'>Reinforcement not quantified (missing steel)</h2><p class='muted small'>Every concrete "
            "component has one reinforcement state. MISSING_DATA: no bar quantity exists; PARTIAL_MISSING: bars for "
            "part of it, the rest UNRESOLVED. These are counts, never 0 kg, and are in no total. "
            f"Components: {sum(rc['totals'].values())}; " +
            ", ".join(f"{k} {v}" for k, v in sorted(rc["totals"].items())) + ".</p>")
    tr = "".join(f"<tr><td>{r['FAMILY']}</td><td>{r['STOREY']}</td><td class='num'>{r['COMPONENTS']}</td>"
                 f"<td class='num'>{r['PROVISIONAL_MODEL']}</td><td class='num'>{r['PARTIAL_MISSING']}</td>"
                 f"<td class='num'>{r['MISSING_DATA']}</td><td class='num'>{r['UNRESOLVED_STEEL_ITEMS']}</td></tr>"
                 for r in rows)
    return head + ("<table class='small'><thead><tr><th>Family</th><th>Storey</th><th>Components</th>"
                   "<th>Bar model</th><th>Partial</th><th>Missing</th><th>Unresolved steel items</th></tr></thead>"
                   f"<tbody>{tr}</tbody></table>" if rows else "<p>None.</p>")


def compute(drawings, *, conventions=None, overrides=None, profile=None, project=None, route="auto", cache_dir=None,
            evidence=None):
    prof = None
    if profile:
        prof = json.loads(Path(profile).read_text(encoding="utf-8")) if not isinstance(profile, dict) else profile
    takeoff = bool(prof and (prof.get("families") or prof.get("sheets")))
    want = route.upper()[:1] if route and route != "auto" else None
    inputs = M1.accept(drawings)
    known = [M1.KNOWN_PROJECTS[i["sha256"]] for i in inputs if i["sha256"] in M1.KNOWN_PROJECTS]
    if want in ("A", "B", "C") or (want is None and ((known and not prof) or takeoff)):
        if want == "C":                         # inventory only (M1 route C; a known set still replays route A)
            return M1.compute(drawings, conventions=conventions, overrides=overrides, profile=None, project=project)
        return M1.compute(drawings, conventions=conventions, overrides=overrides, profile=profile if want != "A"
                          else None, project=project)
    log, t0 = [], time.perf_counter()

    def step(name, t):
        log.append({"step": name, "seconds": round(time.perf_counter() - t, 3)})
        return time.perf_counter()
    t = step("1 accept", t0)
    invs, _ = M1.inventories(inputs)
    t = step("2 inventory", t)
    overrides = dict(overrides or {})
    ev = load_evidence(evidence) if isinstance(evidence, (str, Path)) else evidence
    res = route_generic(inputs, conventions, overrides, prof, cache_dir, evidence=ev)
    t = step("3-5 generic detection, quantities, conventions", t)
    items = res["items"]
    PE.check(items, res["conv"])
    exc = M1.exceptions(items, res["exceptions"])
    sens = M1.sensitivity(res)
    t = step("6 checks, exceptions and sensitivity", t)
    trades = {r["trade"]: r for r in PE.rollup(items, ("trade",))}
    strip = lambda r: {k: v for k, v in r.items() if k not in ("trade", "family")}       # noqa: E731
    rc = PE.rollup([i for i in items if i["trade"] == "CONCRETE" and i["family"] != "PLAIN_CONCRETE"], ("trade",))
    g = res["generic"]
    rcomp = GR.rebar_completeness(items, g["register"])
    g["rebar_completeness"] = rcomp
    cov = FC.coverage(g["D"], items, g["risk"], GR.scope_scan(g["D"]), g.get("evidence"))
    g["family_coverage"] = cov
    boq = M1.boq_lines(items) + not_detected_lines(cov) + missing_steel_lines(rcomp)
    summary = {
        "policy": POLICY_ID, "route": "G_GENERIC_ENGINE",
        "project": known[0]["project"] if known else (project or "new project"),
        "inputs": [{k: v for k, v in r.items() if k != "path"} for r in inputs],
        "conventions": {"set": res["conv"].name, "digest": res["conv"].digest(), "overrides": overrides,
                        "n": len(res["conv"].items)},
        "totals": {k: {kk: v for kk, v in r.items() if kk != "trade"} for k, r in trades.items()},
        "concrete_rc": strip(rc[0]) if rc else {}, "plain_concrete": {},
        "steel_t": {k: trades["REINFORCEMENT"][k] / 1000 for k in ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE",
                                                                    "PLANNING_HIGH")} if "REINFORCEMENT" in trades
        else {},
        "n_items": len(items), "n_exceptions": len(exc),
        "exceptions_by_kind": dict(sorted(Counter(e["KIND"] for e in exc).items())),
        "frozen_manifests_verified": [], "adapter": None,
        "coverage_risk_by_kind": dict(sorted(Counter(r["KIND"] for r in g["risk"]).items())),
        "rebar_completeness": dict(sorted(rcomp["totals"].items())),
        "missing_steel_components": rcomp["missing_steel_components"],
        "missing_steel_by_family_storey": [{k: r[k] for k in ("FAMILY", "STOREY", "COMPONENTS",
                                                               "MISSING_STEEL_COMPONENTS", "UNRESOLVED_STEEL_ITEMS")}
                                           for r in rcomp["by_family_storey"] if r["MISSING_STEEL_COMPONENTS"]],
        "not_detected_families": {b["FAMILY"]: b["EVIDENCE"] for b in boq if b["SECTION"].startswith("C")},
        "sheets": [{k: sh[k] for k in ("sheet_id", "role", "storey")} for sh in g["D"]["model"]["sheets"]],
        "intake_cache": g["intake_cache"],
        "detail_evidence": None if not ev else {
            "document": ev.get("document"), "records": dict(sorted(Counter(r["state"] for r in ev["records"]).items())),
            "ground_beam_details": [{"detail_id": d["detail_id"], "condition": d["condition"], "ocr": d["ocr"],
                                     "roles": sorted(d["bars"])} for d in DE.ground_beam_details(ev)]},
        "rule": "planning = verified + provisional base; low / high sum each item's own low / high; unresolved "
                "items and not-detected families are never added; a new project is never VERIFIED",
    }
    return {"summary": summary, "items": items, "conv": res["conv"], "coverage": [], "exceptions": exc,
            "sensitivity": sens, "inventories": invs, "inputs": inputs, "log": log,
            "seconds": round(time.perf_counter() - t0, 3), "boq": boq, "generic": g,
            "family": PE.rollup(items, ("trade", "family")),
            "floor": sorted(PE.rollup(items, ("trade", "storey", "family")),
                            key=lambda r: (r["trade"], M1._storey_key(r["storey"]), r["family"])),
            "steel": PE.steel_by_diameter(items), "blockers": PE.blockers(items),
            "template": DI.profile_template(invs[0]) if invs else None}


def files(R, *, as_of):
    out = M1.files(R, as_of=as_of)
    g = R.get("generic")
    if g:
        out["CONTRACTOR_BOQ.csv"] = M1.csv_text(R["boq"], ["ITEM", "SECTION", "FAMILY", "DESCRIPTION", "UNIT",
                                                         "VERIFIED", "PROVISIONAL_LOW", "PROVISIONAL_BASE",
                                                         "PROVISIONAL_HIGH", "PLANNING_LOW", "PLANNING_BASE",
                                                         "PLANNING_HIGH", "N_VERIFIED", "N_PROVISIONAL",
                                                         "N_UNRESOLVED", "UNRESOLVED_EXPOSURE_LOW",
                                                         "UNRESOLVED_EXPOSURE_HIGH", "EVIDENCE"])
        out["COVERAGE_RISK.csv"] = M1.csv_text(g["risk"], ["KIND", "WHERE", "DETAIL"])
        if g.get("family_coverage"):
            out["FAMILY_COVERAGE.csv"] = M1.csv_text(g["family_coverage"])
        rc = g.get("rebar_completeness") or GR.rebar_completeness(R["items"], g["register"])
        out["REBAR_COMPLETENESS.csv"] = M1.csv_text(rc["rows"])
        out["MISSING_STEEL_BY_FAMILY_STOREY.csv"] = M1.csv_text(rc["by_family_storey"])
        if "BOQ_REPORT.html" in out:                 # the frozen M1 report, with the missing-steel section added
            tail = "</main></body></html>"
            h = out["BOQ_REPORT.html"]
            out["BOQ_REPORT.html"] = (h.replace(tail, missing_steel_html(rc) + tail) if tail in h else
                                      h + missing_steel_html(rc))
        for name, svg in OV.sheet_svgs(g["D"]).items():
            out[f"overlays/{name}.svg"] = svg
        out["OVERLAYS.html"] = OV.html(g["D"], banner=BANNER)
    return out


def workbook_model(R):
    model = M1.workbook_model(R)
    g = R.get("generic")
    if not g:
        return model
    nd = [b for b in R["boq"] if b["SECTION"].startswith("C")]
    model["NOT_DETECTED"] = {"kind": "TABLE", "header": ["Item", "Family", "Evidence", "Detail (keywords only)"],
                             "rows": [[b["ITEM"], b["FAMILY"], b["EVIDENCE"], b["DESCRIPTION"]] for b in nd],
                             "wrap_cols": [3], "widths": {1: 24, 2: 18, 3: 100},
                             "note": "Families the generic engine does not quantify: a coverage risk, never a zero. "
                                     "Not in any total."}
    model["COVERAGE_RISK"] = {"kind": "TABLE", "header": ["Kind", "Where", "Detail"],
                              "rows": [[r["KIND"], r["WHERE"], str(r["DETAIL"])] for r in g["risk"]],
                              "wrap_cols": [2], "widths": {0: 34, 1: 16, 2: 100},
                              "note": "Everything the generic route may have missed or merged: read before use."}
    rk = ["COMPONENT_ID", "FAMILY", "STOREY", "REBAR_STATE", "REASON", "PROVISIONAL_KG_BASE",
          "UNRESOLVED_STEEL_ITEMS"]
    rc = g.get("rebar_completeness") or GR.rebar_completeness(R["items"], g["register"])
    mk = ["FAMILY", "STOREY", "COMPONENTS", "PROVISIONAL_MODEL", "PARTIAL_MISSING", "MISSING_DATA", "EXPLICIT_NONE",
          "OUTSIDE_SCOPE", "UNRESOLVED_STEEL_ITEMS"]
    model["MISSING_STEEL"] = {"kind": "TABLE", "header": mk,
                              "rows": [[M1._cell(r.get(k)) for k in mk] for r in rc["by_family_storey"]],
                              "widths": {0: 18, 1: 12},
                              "note": "Components without a full bar quantity, by family and storey: counts, never "
                                      "0 kg, and in no total."}
    model["REBAR_COMPLETENESS"] = {"kind": "TABLE", "header": rk,
                                   "rows": [[M1._cell(r.get(k)) for k in rk] for r in rc["rows"]],
                                   "wrap_cols": [4], "widths": {0: 40, 4: 70},
                                   "note": "One row per concrete component and its bar model state. MISSING_DATA: "
                                           "no bar quantity exists for it (never a kg/m3 ratio)."}
    return model


def write_all(R, out, *, as_of, pdf=True, xlsx=True, created=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t = time.perf_counter()
    fs = files(R, as_of=as_of)
    for name, text in fs.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(text, encoding="utf-8")
    R["log"].append({"step": "7 registers and report", "seconds": round(time.perf_counter() - t, 3)})
    res = {"files": sorted(fs)}
    t = time.perf_counter()
    if xlsx:
        model = workbook_model(R)
        res["xlsx"] = XL.write(model, out / "STRUCTURAL_BOQ.xlsx", created=created or datetime(2026, 1, 1),
                               banner=BANNER)
        XL.validate(out / "STRUCTURAL_BOQ.xlsx", model)
    if pdf:
        res["pdf"] = M1.print_pdf(out / "BOQ_REPORT.html", out / "BOQ_REPORT.pdf")
        if (out / "OVERLAYS.html").exists():
            res["overlays_pdf"] = M1.print_pdf(out / "OVERLAYS.html", out / "VISUAL_QA_OVERLAYS.pdf")
    R["log"].append({"step": "8 export", "seconds": round(time.perf_counter() - t, 3)})
    (out / "run_log.json").write_text(M1._jdump({"steps": R["log"], "seconds_compute": R["seconds"],
                                                 "manual_interventions_during_run": 0, "outputs": res}),
                                      encoding="utf-8")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(prog="urban_boq_m2", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--drawings", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--conventions")
    p.add_argument("--set", action="append", default=[], metavar="ID=VALUE")
    p.add_argument("--profile")
    p.add_argument("--route", default="auto", choices=["auto", "A", "B", "G", "C"])
    p.add_argument("--no-pdf", action="store_true")
    p.add_argument("--no-xlsx", action="store_true")
    p.add_argument("--as-of", default=datetime.now().strftime("%Y-%m-%d"))
    p.add_argument("--cache", help="folder for cached intakes (by drawing sha256 and code digest); optional")
    p.add_argument("--evidence", help="DETAIL_EVIDENCE.json from tools/pdf_evidence.py (or a manual transcription "
                                      "in the same schema): typical-detail bars the DXF does not carry")
    a = ap.parse_args(argv)
    R = compute(a.drawings, conventions=a.conventions, overrides=M1.parse_sets(a.set), profile=a.profile,
                route=a.route, cache_dir=a.cache, evidence=a.evidence)
    writer = write_all if R.get("generic") else M1.write_all
    res = writer(R, a.out, as_of=a.as_of, pdf=not a.no_pdf, xlsx=not a.no_xlsx)
    s = R["summary"]
    print(json.dumps({"route": s["route"], "concrete_m3": {k: round(s["totals"]["CONCRETE"][k], 3) for k in
                                                          ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE",
                                                           "PLANNING_HIGH")},
                      "unresolved": {t: s["totals"][t]["N_UNRESOLVED"] for t in s["totals"]},
                      "not_detected": s.get("not_detected_families"),
                      "exceptions": s["n_exceptions"], "outputs": len(res["files"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
