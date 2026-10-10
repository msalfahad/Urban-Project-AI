"""URBAN BOQ M2 - the one-command BOQ with ROUTE G, the generic engine, on top of the frozen M1 pipeline.

    python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --out OUT [--profile P.json] [--route auto|A|B|G|C]
                                       [--conventions C.json] [--set ID=VALUE ...] [--no-pdf] [--no-xlsx]

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
from engine.source import drawing_inventory as DI         # noqa: E402
from engine.source import generic_route as GR             # noqa: E402
from engine.source import provisional_estimate as PE      # noqa: E402
from tools import m2_overlay as OV                        # noqa: E402
from tools import urban_intake as UI                      # noqa: E402
from tools import urban_structural_boq as M1              # noqa: E402

POLICY_ID = "URBAN_BOQ_M2"
GENERIC_CONVENTIONS = "engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json"
BANNER = M1.BANNER


def route_generic(inputs, conv_path, overrides, profile):
    dxf = next((r for r in inputs if r["kind"] == "DXF" and "error" not in r), None)
    if dxf is None:
        raise M1.PipelineError("route G needs a readable DXF")
    I = UI.read(dxf["path"])
    D = GR.detect(I)
    generic = json.loads((ROOT / (conv_path or GENERIC_CONVENTIONS)).read_text(encoding="utf-8"))

    def build(ov):
        conv = GR.merge_conventions(generic, profile, ov)
        items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
        return conv, items, reg, risk
    conv, items, reg, risk = build(overrides)
    exc = [{"EXCEPTION_ID": f"CR-{k:04d}", "KIND": "COVERAGE_RISK:" + r["KIND"], "FAMILY": "", "SHEET": r["WHERE"],
            "DETAIL": str(r["DETAIL"])[:300], "LOCATION": ""} for k, r in enumerate(risk, 1)]
    return {"items": items, "conv": conv, "coverage": [], "rebuild": lambda ov: build(dict(overrides, **ov))[1],
            "frozen": [], "exceptions": exc, "adapter": None,
            "generic": {"D": D, "register": reg, "risk": risk}}


def not_detected_lines(risk):
    nd = {r["WHERE"]: r for r in risk if r["KIND"] == "FAMILY_NOT_QUANTIFIED"}
    out = []
    for k, fam in enumerate(sorted(GR.SCOPE_WORDS), 1):
        r = nd.get(fam)
        text = (f"{fam}: drawing evidence, not quantified - {r['DETAIL']}" if r else
                f"{fam}: no label found on the drawing, and the generic engine cannot detect this family - confirm "
                f"it is absent before using the totals")
        out.append({"ITEM": f"C.{k:02d}", "SECTION": "C NOT DETECTED (COVERAGE RISK)", "FAMILY": fam,
                    "DESCRIPTION": text, "UNIT": "-", "EVIDENCE": "LABELS_FOUND" if r else "NO_LABEL_FOUND"})
    return out


def compute(drawings, *, conventions=None, overrides=None, profile=None, project=None, route="auto"):
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
    res = route_generic(inputs, conventions, overrides, prof)
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
    boq = M1.boq_lines(items) + not_detected_lines(g["risk"])
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
        "rebar_completeness": dict(sorted(Counter(r["REBAR_STATE"] for r in g["register"]).items())),
        "not_detected_families": {b["FAMILY"]: b["EVIDENCE"] for b in boq if b["SECTION"].startswith("C")},
        "sheets": [{k: sh[k] for k in ("sheet_id", "role", "storey")} for sh in g["D"]["model"]["sheets"]],
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
        out["REBAR_COMPLETENESS.csv"] = M1.csv_text(g["register"])
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
    rk = ["COMPONENT_ID", "FAMILY", "STOREY", "REBAR_STATE", "REASON", "PROVISIONAL_KG_BASE"]
    model["REBAR_COMPLETENESS"] = {"kind": "TABLE", "header": rk,
                                   "rows": [[M1._cell(r.get(k)) for k in rk] for r in g["register"]],
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
    a = ap.parse_args(argv)
    R = compute(a.drawings, conventions=a.conventions, overrides=M1.parse_sets(a.set), profile=a.profile,
                route=a.route)
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
