"""URBAN STRUCTURAL BOQ (M1) - one command from a drawing set to a planning BOQ, an exception report, Excel and PDF.

    python3 -m tools.urban_structural_boq run --drawings ST.dxf ST.pdf --out OUT [--conventions C.json]
                                             [--set ID=VALUE ...] [--profile P.json] [--no-pdf] [--no-xlsx]
    python3 -m tools.urban_structural_boq inventory --drawings NEW.dxf --out OUT     (inventory + profile template)

The eight steps (each one is timed in run_log.json):
    1 accept     every input file: sha256, size, kind (DXF read; PDF page count; DWG refused: convert it first)
    2 inventory  per DXF: sheets (frames), layers and their role guesses, tag families, candidate outlines
                 (engine.source.drawing_inventory)
    3 extract    ROUTE A, a drawing set the project registry knows (by sha256): the frozen S1 - S9A stage registers
                 of that project are replayed through its adapter (nothing is re-measured, the stage manifests are
                 verified first). ROUTE B, a new drawing set with a person-confirmed profile: footing and column
                 outlines, tags and schedule rows are extracted live (engine.source.profile_takeoff). ROUTE C, no
                 profile: the inventory and a profile template only; every family is UNRESOLVED.
    4 quantify   VERIFIED (released rows only) and source-complete quantities
    5 conventions PROVISIONAL quantities under the convention set (JSON; --set overrides one value, reversibly)
    6 check      one owner per component (no double counting), the low <= base <= high order, unresolved never in a
                 total; the exception report lists every unresolved item, conflict and low-confidence assumption
    7 report     V / P / U registers, family / floor / diameter summaries, sensitivity, blockers, contractor BOQ
    8 export     STRUCTURAL_BOQ.xlsx (engine.boq_m1_xlsx) and BOQ_REPORT.html -> BOQ_REPORT.pdf (Chromium)

Nothing here is engineering approval. The planning estimate is VERIFIED + PROVISIONAL base (each provisional item
holds one reading as base and its alternatives as its range); UNRESOLVED items are listed apart and never added.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import boq_m1_xlsx as XL                      # noqa: E402
from engine.source import drawing_inventory as DI         # noqa: E402
from engine.source import profile_takeoff as PT           # noqa: E402
from engine.source import provisional_estimate as PE      # noqa: E402
from tools import m1_report as REPORT                     # noqa: E402

POLICY_ID = "URBAN_STRUCTURAL_BOQ_M1"
CHROMIUM = "/opt/pw-browsers/chromium"
BANNER = ("PLANNING ESTIMATE - NOT ENGINEERING-APPROVED - NOT FOR TENDER OR CONTRACT - NO PRICES - VERIFIED IS THE "
          "ONLY RELEASED QUANTITY; UNRESOLVED ITEMS ARE NOT IN ANY TOTAL")
# Drawing sets whose frozen stage registers exist in this repository (route A), by the structural DXF's sha256.
KNOWN_PROJECTS = {
    "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079": {
        "project": "ST7757 villa (structural set)",
        "adapter": "research/alsenan_m1_usable_boq/alsenan_adapter.py",
        "conventions": "research/alsenan_m1_usable_boq/conventions_alsenan.json"},
}
FAMILY_TEXT = {
    "FOOTINGS": "Reinforced concrete in isolated / combined footings",
    "GROUND_BEAMS": "Reinforced concrete in ground beams and strap beams",
    "COLUMNS": "Reinforced concrete in columns and foundation necks",
    "BEAMS": "Reinforced concrete in suspended beams",
    "SLABS": "Reinforced concrete in suspended slabs",
    "CANTILEVER_PORTIONS": "Reinforced concrete in hatched cantilever portions",
    "GROUND_SLAB": "Reinforced concrete in slab on grade",
    "STAIRS": "Reinforced concrete in stairs and landings",
    "LINTELS": "Reinforced concrete in lintels",
    "LIFT": "Reinforced concrete in lift pit",
    "POOL": "Reinforced concrete in swimming pool",
    "DOMES": "Reinforced concrete in domes and ring beams",
    "WATER_TANK_ROOF": "Reinforced concrete in roof water tank",
    "PARAPETS": "Reinforced concrete in parapets",
    "BOUNDARY_WALL": "Reinforced concrete in boundary wall",
    "WALLS": "Reinforced concrete in walls",
    "PLAIN_CONCRETE": "Plain concrete blinding",
}
STOREY_ORDER = ("FOUNDATION", "GROUND", "GF", "1F", "2F", "ROOF", "ALL", "UNKNOWN")
REG_KEYS = ("item_id", "category", "trade", "family", "storey", "component_id", "part", "unit", "low", "base", "high",
            "dia_mm", "exposure_low", "exposure_high", "support", "confidence", "blocker", "assumptions", "formula",
            "expression", "dimensions", "source", "limitations", "double_count_risk")


class PipelineError(RuntimeError):
    pass


# ------------------------------------------------------------------ small helpers
def _sha(p):
    return DI.sha256_file(p)


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(round(v, 9))
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
    return v


def csv_text(rows, fields=None):
    keys = list(fields or (rows[0].keys() if rows else []))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    return buf.getvalue()


def _jdump(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True, default=str) + "\n"


def _storey_key(s):
    return (STOREY_ORDER.index(s) if s in STOREY_ORDER else len(STOREY_ORDER), str(s))


def _load_module(rel):
    p = ROOT / rel
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(p.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(p.parent))
    return mod


def parse_sets(pairs):
    out = {}
    for s in pairs or ():
        if "=" not in s:
            raise PipelineError(f"--set needs ID=VALUE, got {s!r}")
        k, v = s.split("=", 1)
        try:
            v = float(v)
        except ValueError:
            pass
        out[k.strip()] = v
    return out


# ------------------------------------------------------------------ steps 1 - 2
def accept(paths):
    rows = []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            raise PipelineError(f"input not found: {p}")
        kind = p.suffix.lower().lstrip(".")
        r = {"file": p.name, "path": str(p), "sha256": _sha(p), "bytes": p.stat().st_size, "kind": kind.upper()}
        if kind == "pdf":
            try:
                from pypdf import PdfReader
                rd = PdfReader(str(p))
                r["pages"] = len(rd.pages)
                r["text_layer"] = bool((rd.pages[0].extract_text() or "").strip()) if rd.pages else False
            except Exception as e:                                          # an unreadable PDF is an exception
                r["error"] = f"{type(e).__name__}"
        elif kind == "dwg":
            r["error"] = "DWG is not read: convert to DXF first (no pinned decoder in this repository)"
        elif kind != "dxf":
            r["error"] = "not a drawing format the pipeline reads"
        rows.append(r)
    if not any(r["kind"] == "DXF" and "error" not in r for r in rows):
        raise PipelineError("no readable DXF in the drawing set (a PDF alone carries no measurable geometry here)")
    return rows


def inventories(inputs):
    import ezdxf
    out, docs = [], {}
    for r in inputs:
        if r["kind"] != "DXF" or "error" in r:
            continue
        doc = ezdxf.readfile(r["path"])
        inv = DI.inventory(doc, r["path"])
        inv["file"] = r["file"]
        out.append(inv)
        docs[r["sha256"]] = doc
    return out, docs


# ------------------------------------------------------------------ step 3 - 5
def route_known(entry, conv_path, overrides):
    adapter = _load_module(entry["adapter"])
    conv = PE.load_conventions(ROOT / (conv_path or entry["conventions"]), overrides)
    frozen = adapter.verify_frozen() if hasattr(adapter, "verify_frozen") else []
    T = adapter.load()
    items, _ = adapter.build_items(conv, T)
    coverage = adapter.coverage(items, T)

    def rebuild(ov):
        c = PE.load_conventions(ROOT / (conv_path or entry["conventions"]), dict(overrides, **ov))
        return adapter.build_items(c, T)[0]
    return {"items": items, "conv": conv, "coverage": coverage, "rebuild": rebuild, "frozen": frozen,
            "exceptions": [], "adapter": entry["adapter"]}


def route_profile(profile, docs, invs):
    sha = profile.get("drawing_sha256")
    doc = docs.get(sha) if sha else (next(iter(docs.values())) if len(docs) == 1 else None)
    if doc is None:
        raise PipelineError("the profile names no drawing of this set (drawing_sha256)")
    inv = next((i for i in invs if i["sha256"] == (sha or i["sha256"])), None)
    extracted = {}
    for s in profile.get("sheets", []):
        box = s.get("box")
        d = {"texts": DI.texts(doc, box)}
        for fam, cfg in (profile.get("families") or {}).items():
            if s["sheet_id"] in (cfg.get("sheets") or []) and cfg.get("layers"):
                segs, curved = DI.segments(doc, set(cfg["layers"]), box)
                d[fam] = {"segments": segs, "curved": curved}
        extracted[s["sheet_id"]] = d
    items, exc, conv = PT.takeoff(profile, extracted, inv)
    return {"items": items, "conv": conv, "coverage": [], "rebuild": None, "frozen": [], "exceptions": exc,
            "adapter": None}


# ------------------------------------------------------------------ step 6 - 7
def exceptions(items, extra):
    rows = list(extra)
    n = len(rows)
    for i in items:
        kind = None
        if i["category"] == "UNRESOLVED":
            kind = "UNRESOLVED"
        elif i["category"] == "PROVISIONAL" and i["confidence"] == "LOW":
            kind = "LOW_CONFIDENCE_PROVISIONAL"
        elif i["category"] == "PROVISIONAL" and i["blocker"] in ("SECTION_CONFLICT", "SIZE_MISMATCH"):
            kind = "CONFLICT_RESOLVED_BY_CONVENTION"
        if kind:
            n += 1
            rows.append({"EXCEPTION_ID": f"EX-{n:04d}", "KIND": kind, "FAMILY": i["family"], "SHEET": i["storey"],
                         "DETAIL": f"{i['item_id']}: {i['blocker']}; {i['limitations'] or i['expression']}"[:300],
                         "LOCATION": i["component_id"]})
    return rows


def sensitivity(res):
    """One assumption at a time: every alternative option (choice) or the low / high value (number), the rest at
    base. Delta of the provisional base totals (concrete m3, steel kg)."""
    if res["rebuild"] is None:
        return []
    conv, items = res["conv"], res["items"]
    base = {t: sum(i["base"] for i in items if i["trade"] == t and i["category"] != "UNRESOLVED")
            for t in PE.TRADES}
    used = Counter(a for i in items for a in i["assumptions"])
    rows = []
    for cid, c in sorted(conv.items.items()):
        if not used.get(cid):
            continue
        alts = ([o for o in c["options"] if o != c["base"]] if c["kind"] == "choice" else
                [v for v in (c["low"], c["high"]) if abs(v - c["base"]) > 1e-12])
        for a in alts:
            new = res["rebuild"]({cid: a})
            tot = {t: sum(i["base"] for i in new if i["trade"] == t and i["category"] != "UNRESOLVED")
                   for t in PE.TRADES}
            rows.append({"CONVENTION_ID": cid, "BASE": c["base"], "ALTERNATIVE": a, "ITEMS_USING": used[cid],
                         "CONCRETE_M3_DELTA": tot["CONCRETE"] - base["CONCRETE"],
                         "STEEL_KG_DELTA": tot["REINFORCEMENT"] - base["REINFORCEMENT"],
                         "PROVENANCE": c["provenance"]})
    return rows


def boq_lines(items):
    conc = PE.rollup([i for i in items if i["trade"] == "CONCRETE"], ("family",))
    steel = PE.steel_by_diameter(items)
    unres_s = sum(1 for i in items if i["trade"] == "REINFORCEMENT" and i["category"] == "UNRESOLVED")
    lines = []
    order = list(FAMILY_TEXT)
    for k, r in enumerate(sorted(conc, key=lambda r: (order.index(r["family"]) if r["family"] in order else 99,
                                                      r["family"])), 1):
        lines.append({"ITEM": f"A.{k:02d}", "SECTION": "A CONCRETE", "FAMILY": r["family"],
                      "DESCRIPTION": FAMILY_TEXT.get(r["family"], f"Concrete: {r['family'].lower()}"), "UNIT": "m3",
                      "VERIFIED": r["VERIFIED"], "PROVISIONAL_LOW": r["PROVISIONAL_LOW"],
                      "PROVISIONAL_BASE": r["PROVISIONAL_BASE"], "PROVISIONAL_HIGH": r["PROVISIONAL_HIGH"],
                      "PLANNING_LOW": r["PLANNING_LOW"], "PLANNING_BASE": r["PLANNING_BASE"],
                      "PLANNING_HIGH": r["PLANNING_HIGH"], "N_VERIFIED": r["N_VERIFIED"],
                      "N_PROVISIONAL": r["N_PROVISIONAL"], "N_UNRESOLVED": r["N_UNRESOLVED"],
                      "UNRESOLVED_EXPOSURE_LOW": r["UNRESOLVED_EXPOSURE_LOW"],
                      "UNRESOLVED_EXPOSURE_HIGH": r["UNRESOLVED_EXPOSURE_HIGH"]})
    for k, r in enumerate(steel, 1):
        lines.append({"ITEM": f"B.{k:02d}", "SECTION": "B REINFORCEMENT", "FAMILY": "ALL",
                      "DESCRIPTION": f"High-yield bar reinforcement, {r['DIA_MM']:g} mm", "UNIT": "kg",
                      "VERIFIED": r["VERIFIED"], "PROVISIONAL_LOW": r["PROVISIONAL_LOW"],
                      "PROVISIONAL_BASE": r["PROVISIONAL_BASE"], "PROVISIONAL_HIGH": r["PROVISIONAL_HIGH"],
                      "PLANNING_LOW": r["PLANNING_LOW"], "PLANNING_BASE": r["PLANNING_BASE"],
                      "PLANNING_HIGH": r["PLANNING_HIGH"], "DIA_MM": r["DIA_MM"]})
    lines.append({"ITEM": "B.UN", "SECTION": "B REINFORCEMENT", "FAMILY": "ALL", "UNIT": "kg",
                  "DESCRIPTION": "Reinforcement with no bar model (unresolved; not in any total)",
                  "N_UNRESOLVED": unres_s})
    return lines


def compute(drawings, *, conventions=None, overrides=None, profile=None, project=None):
    """Steps 1 - 7 in memory. Returns the result dict (no file written)."""
    log, t0 = [], time.perf_counter()

    def step(name, t):
        log.append({"step": name, "seconds": round(time.perf_counter() - t, 3)})
        return time.perf_counter()
    t = time.perf_counter()
    inputs = accept(drawings)
    t = step("1 accept", t)
    invs, docs = inventories(inputs)
    t = step("2 inventory", t)
    known = [KNOWN_PROJECTS[i["sha256"]] for i in inputs if i["sha256"] in KNOWN_PROJECTS]
    overrides = dict(overrides or {})
    if known and not profile:
        res = route_known(known[0], conventions, overrides)
        route = "A_FROZEN_STAGE_REPLAY"
    elif profile:
        prof = json.loads(Path(profile).read_text(encoding="utf-8")) if not isinstance(profile, dict) else profile
        res = route_profile(prof, docs, invs)
        route = "B_PROFILE_TAKEOFF"
    else:
        res = route_profile({"profile": "NO_PROFILE", "units_to_mm": None}, docs, invs)
        route = "C_INVENTORY_ONLY"
    t = step("3-5 extract, quantify, conventions", t)
    items = res["items"]
    PE.check(items, res["conv"])
    exc = exceptions(items, res["exceptions"])
    sens = sensitivity(res)
    t = step("6 checks, exceptions and sensitivity", t)
    trades = {r["trade"]: r for r in PE.rollup(items, ("trade",))}
    strip = lambda r: {k: v for k, v in r.items() if k not in ("trade", "family")}       # noqa: E731
    rc = PE.rollup([i for i in items if i["trade"] == "CONCRETE" and i["family"] != "PLAIN_CONCRETE"], ("trade",))
    plain = PE.rollup([i for i in items if i["trade"] == "CONCRETE" and i["family"] == "PLAIN_CONCRETE"], ("trade",))
    summary = {
        "policy": POLICY_ID, "route": route, "project": known[0]["project"] if known else (project or "new project"),
        "inputs": [{k: v for k, v in r.items() if k != "path"} for r in inputs],
        "conventions": {"set": res["conv"].name, "digest": res["conv"].digest(), "overrides": overrides,
                        "n": len(res["conv"].items)},
        "totals": {t: {k: v for k, v in r.items() if k != "trade"} for t, r in trades.items()},
        "concrete_rc": strip(rc[0]) if rc else {}, "plain_concrete": strip(plain[0]) if plain else {},
        "steel_t": {k: trades["REINFORCEMENT"][k] / 1000 for k in ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE",
                                                                    "PLANNING_HIGH")} if "REINFORCEMENT" in trades
        else {},
        "n_items": len(items), "n_exceptions": len(exc),
        "exceptions_by_kind": dict(sorted(Counter(e["KIND"] for e in exc).items())),
        "frozen_manifests_verified": res["frozen"], "adapter": res["adapter"],
        "rule": "planning = verified + provisional base; low / high sum each item's own low / high; unresolved "
                "items are never added",
    }
    return {"summary": summary, "items": items, "conv": res["conv"], "coverage": res["coverage"], "exceptions": exc,
            "sensitivity": sens, "inventories": invs, "inputs": inputs, "log": log,
            "seconds": round(time.perf_counter() - t0, 3), "boq": boq_lines(items),
            "family": PE.rollup(items, ("trade", "family")),
            "floor": sorted(PE.rollup(items, ("trade", "storey", "family")),
                            key=lambda r: (r["trade"], _storey_key(r["storey"]), r["family"])),
            "steel": PE.steel_by_diameter(items), "blockers": PE.blockers(items),
            "template": DI.profile_template(invs[0]) if invs else None}


# ------------------------------------------------------------------ step 8: files
def _reg(items, cat):
    rows = []
    for i in items:
        if i["category"] != cat:
            continue
        rows.append({k.upper(): (";".join(i[k]) if k == "assumptions" else i[k]) for k in REG_KEYS})
    return sorted(rows, key=lambda r: (r["TRADE"], r["FAMILY"], _storey_key(r["STOREY"]), r["ITEM_ID"]))


def files(R, *, as_of):
    """{relative name: text} for every deterministic output (no timing, no absolute path)."""
    s = dict(R["summary"], as_of=as_of)
    conv_rows = sorted(R["conv"].register(), key=lambda r: r["id"])
    out = {
        "SUMMARY.json": _jdump(s),
        "VERIFIED_REGISTER.csv": csv_text(_reg(R["items"], "VERIFIED"), [k.upper() for k in REG_KEYS]),
        "PROVISIONAL_REGISTER.csv": csv_text(_reg(R["items"], "PROVISIONAL"), [k.upper() for k in REG_KEYS]),
        "UNRESOLVED_REGISTER.csv": csv_text(_reg(R["items"], "UNRESOLVED"), [k.upper() for k in REG_KEYS]),
        "ASSUMPTIONS.csv": csv_text(conv_rows, ["id", "title", "kind", "unit", "base", "low", "high", "options",
                                                "provenance", "source", "rationale", "overridden_from"]),
        "CONTRACTOR_BOQ.csv": csv_text(R["boq"], ["ITEM", "SECTION", "FAMILY", "DESCRIPTION", "UNIT", "VERIFIED",
                                                  "PROVISIONAL_LOW", "PROVISIONAL_BASE", "PROVISIONAL_HIGH",
                                                  "PLANNING_LOW", "PLANNING_BASE", "PLANNING_HIGH", "N_VERIFIED",
                                                  "N_PROVISIONAL", "N_UNRESOLVED", "UNRESOLVED_EXPOSURE_LOW",
                                                  "UNRESOLVED_EXPOSURE_HIGH"]),
        "FAMILY_SUMMARY.csv": csv_text(R["family"]),
        "FLOOR_SUMMARY.csv": csv_text(R["floor"]),
        "STEEL_BY_DIAMETER.csv": csv_text([dict(r, PLANNING_BASE_T=r["PLANNING_BASE"] / 1000) for r in R["steel"]]),
        "SENSITIVITY.csv": csv_text(R["sensitivity"], ["CONVENTION_ID", "BASE", "ALTERNATIVE", "ITEMS_USING",
                                                       "CONCRETE_M3_DELTA", "STEEL_KG_DELTA", "PROVENANCE"]),
        "BLOCKERS.csv": csv_text(R["blockers"]),
        "EXCEPTIONS.csv": csv_text(R["exceptions"], ["EXCEPTION_ID", "KIND", "FAMILY", "SHEET", "DETAIL",
                                                     "LOCATION"]),
        "INVENTORY.json": _jdump(R["inventories"]),
        "PROFILE_TEMPLATE.json": _jdump(R["template"]),
    }
    if R["coverage"]:
        out["COVERAGE.csv"] = csv_text(R["coverage"])
    out["BOQ_REPORT.html"] = REPORT.html(R, as_of=as_of, banner=BANNER)
    return out


def workbook_model(R):
    n = lambda v: None if v is None else float(v)                                   # noqa: E731
    m3, kg, t3 = "#,##0.000", "#,##0.0", "#,##0.000"
    conc = [b for b in R["boq"] if b["SECTION"].startswith("A") and b["FAMILY"] != "PLAIN_CONCRETE"]
    plain = [b for b in R["boq"] if b["SECTION"].startswith("A") and b["FAMILY"] == "PLAIN_CONCRETE"]
    steel = [b for b in R["boq"] if b["SECTION"].startswith("B") and b["ITEM"] != "B.UN"]
    s = R["summary"]
    lines = ["WHAT THIS IS",
             f"A planning estimate of the structural concrete and reinforcement of {s['project']}, route {s['route']}.",
             "VERIFIED: released under the strict verified-release rules. PROVISIONAL: calculated from drawn or "
             "printed geometry with the stated assumptions (sheet ASSUMPTIONS). UNRESOLVED: not enough geometry; "
             "never in a total.",
             "Planning = verified + provisional. Low and high add each item's own low and high: a bracket, not a "
             "probability. Mutually exclusive readings are never added - each item carries one reading as base.",
             "The planning estimate is not complete: see UNRESOLVED and EXCEPTIONS before using it.",
             "Blue numbers are copied from the registers; black cells are formulas (planning = verified + "
             "provisional, t = kg / 1000, totals).",
             "HOW TO CHANGE AN ASSUMPTION",
             "Re-run: python3 -m tools.urban_structural_boq run --drawings ... --set CONVENTION_ID=VALUE "
             "(the workbook is regenerated; nothing is edited by hand).",
             f"Convention set {s['conventions']['set']} (digest {s['conventions']['digest'][:16]}), overrides "
             f"{json.dumps(s['conventions']['overrides'])}."]
    hdr = ["Item", "Description", "Unit", "Verified", "Provisional low", "Provisional base", "Provisional high",
           "Planning low", "Planning base", "Planning high", "Unresolved items", "Unresolved exposure low (not added)",
           "Unresolved exposure high (not added)"]
    crow = [[b["ITEM"], b["DESCRIPTION"], "m3", n(b["VERIFIED"]), n(b["PROVISIONAL_LOW"]), n(b["PROVISIONAL_BASE"]),
             n(b["PROVISIONAL_HIGH"]), None, None, None, b["N_UNRESOLVED"], n(b["UNRESOLVED_EXPOSURE_LOW"]),
             n(b["UNRESOLVED_EXPOSURE_HIGH"])] for b in conc]
    prow = [[b["ITEM"], b["DESCRIPTION"], "m3", n(b["VERIFIED"]), n(b["PROVISIONAL_LOW"]), n(b["PROVISIONAL_BASE"]),
             n(b["PROVISIONAL_HIGH"]), None, None, None, b["N_UNRESOLVED"], n(b["UNRESOLVED_EXPOSURE_LOW"]),
             n(b["UNRESOLVED_EXPOSURE_HIGH"])] for b in plain]
    shdr = ["Item", "Description", "Unit", "Verified kg", "Provisional low kg", "Provisional base kg",
            "Provisional high kg", "Planning low kg", "Planning base kg", "Planning high kg", "Planning base t"]
    srow = [[b["ITEM"], b["DESCRIPTION"], "kg", n(b["VERIFIED"]), n(b["PROVISIONAL_LOW"]), n(b["PROVISIONAL_BASE"]),
             n(b["PROVISIONAL_HIGH"]), None, None, None, None] for b in steel]
    fl = [r for r in R["floor"] if r["trade"] == "CONCRETE"]
    frow = [[r["storey"], r["family"], n(r["VERIFIED"]), n(r["PROVISIONAL_LOW"]), n(r["PROVISIONAL_BASE"]),
             n(r["PROVISIONAL_HIGH"]), None, r["N_UNRESOLVED"]] for r in fl]

    def reg(cat):
        rows = _reg(R["items"], cat)
        keys = ["ITEM_ID", "CATEGORY", "TRADE", "FAMILY", "STOREY", "COMPONENT_ID", "UNIT", "LOW", "BASE", "HIGH",
                "DIA_MM", "EXPOSURE_LOW", "EXPOSURE_HIGH", "CONFIDENCE", "BLOCKER", "ASSUMPTIONS", "FORMULA",
                "EXPRESSION", "SOURCE", "LIMITATIONS", "DOUBLE_COUNT_RISK"]
        return keys, [[(n(r[k]) if k in ("LOW", "BASE", "HIGH", "DIA_MM", "EXPOSURE_LOW", "EXPOSURE_HIGH") else
                        _cell(r[k])) for k in keys] for r in rows]
    model = {
        "README": {"kind": "INFO", "note": "Read first.", "lines": lines},
        "BOQ_CONCRETE": {"kind": "TABLE", "header": hdr, "rows": crow, "total": "TOTAL reinforced concrete",
                         "formats": {3: m3, 4: m3, 5: m3, 6: m3, 7: m3, 8: m3, 9: m3, 11: m3, 12: m3},
                         "add": {7: [3, 4], 8: [3, 5], 9: [3, 6]}, "widths": {1: 52, 11: 16, 12: 16},
                         "note": "Reinforced concrete m3 by family. Unresolved exposure is shown apart and never "
                                 "added. Plain blinding is on BOQ_PLAIN_CONCRETE."},
        "BOQ_PLAIN_CONCRETE": {"kind": "TABLE", "header": hdr, "rows": prow, "total": "TOTAL plain concrete",
                               "formats": {3: m3, 4: m3, 5: m3, 6: m3, 7: m3, 8: m3, 9: m3, 11: m3, 12: m3},
                               "add": {7: [3, 4], 8: [3, 5], 9: [3, 6]}, "widths": {1: 52, 11: 16, 12: 16},
                               "note": "Plain (unreinforced) concrete, kept apart from the RC total."},
        "BOQ_REINFORCEMENT": {"kind": "TABLE", "header": shdr, "rows": srow, "total": "TOTAL (planning scope)",
                              "formats": {3: kg, 4: kg, 5: kg, 6: kg, 7: kg, 8: kg, 9: kg, 10: t3},
                              "add": {7: [3, 4], 8: [3, 5], 9: [3, 6]}, "scale": {10: (8, 0.001)},
                              "widths": {1: 44},
                              "note": "Reinforcement by bar diameter (bar models only; no kg/m3 ratio anywhere). "
                                      f"{s['totals'].get('REINFORCEMENT', {}).get('N_UNRESOLVED', 0)} reinforcement "
                                      "items are unresolved and not here."},
        "BY_FLOOR": {"kind": "TABLE", "header": ["Storey", "Family", "Verified m3", "Provisional low m3",
                                                  "Provisional base m3", "Provisional high m3", "Planning base m3",
                                                  "Unresolved items"], "rows": frow, "total": "TOTAL",
                     "formats": {2: m3, 3: m3, 4: m3, 5: m3, 6: m3}, "add": {6: [2, 4]},
                     "note": "Concrete by storey and family (the same quantities as BOQ_CONCRETE, split)."},
    }
    for cat in ("VERIFIED", "PROVISIONAL", "UNRESOLVED"):
        h, rows = reg(cat)
        model[cat] = {"kind": "TABLE", "header": h, "rows": rows, "category_col": 1, "wrap_cols": [16, 17, 18, 19],
                      "formats": {7: "#,##0.000", 8: "#,##0.000", 9: "#,##0.000", 11: "#,##0.000", 12: "#,##0.000"},
                      "widths": {0: 34, 5: 30, 16: 40, 17: 40, 18: 40, 19: 40, 20: 30},
                      "note": f"{cat} items, one row each, with source, formula, assumptions and limitations."}
    conv_rows = sorted(R["conv"].register(), key=lambda r: r["id"])
    ak = ["id", "title", "kind", "unit", "base", "low", "high", "options", "provenance", "source", "rationale"]
    model["ASSUMPTIONS"] = {"kind": "TABLE", "header": ak, "rows": [[_cell(c.get(k)) for k in ak] for c in conv_rows],
                            "wrap_cols": [1, 9, 10], "widths": {0: 30, 1: 34, 9: 50, 10: 70},
                            "note": "Every assumption: its base, its alternatives and why. Change with --set."}
    sk = ["CONVENTION_ID", "BASE", "ALTERNATIVE", "ITEMS_USING", "CONCRETE_M3_DELTA", "STEEL_KG_DELTA", "PROVENANCE"]
    model["SENSITIVITY"] = {"kind": "TABLE", "header": sk,
                            "rows": [[_cell(r[k]) if k not in ("CONCRETE_M3_DELTA", "STEEL_KG_DELTA") else
                                      float(r[k]) for k in sk] for r in R["sensitivity"]],
                            "formats": {4: "#,##0.000", 5: "#,##0.0"}, "widths": {0: 34},
                            "note": "One assumption at a time, the rest at base: change of the provisional base."}
    ek = ["EXCEPTION_ID", "KIND", "FAMILY", "SHEET", "DETAIL", "LOCATION"]
    model["EXCEPTIONS"] = {"kind": "TABLE", "header": ek, "rows": [[_cell(e.get(k)) for k in ek]
                                                                  for e in R["exceptions"]],
                           "wrap_cols": [4], "widths": {1: 30, 4: 90, 5: 40},
                           "note": "Everything the run could not settle, and every low-confidence assumption."}
    return model


def write_all(R, out, *, as_of, pdf=True, xlsx=True, created=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t = time.perf_counter()
    fs = files(R, as_of=as_of)
    for name, text in fs.items():
        (out / name).write_text(text, encoding="utf-8")
    R["log"].append({"step": "7 registers and report", "seconds": round(time.perf_counter() - t, 3)})
    res = {"files": sorted(fs)}
    t = time.perf_counter()
    if xlsx:
        model = workbook_model(R)
        created = created or datetime(2026, 1, 1)
        res["xlsx"] = XL.write(model, out / "STRUCTURAL_BOQ.xlsx", created=created, banner=BANNER)
        XL.validate(out / "STRUCTURAL_BOQ.xlsx", model)
    if pdf:
        res["pdf"] = print_pdf(out / "BOQ_REPORT.html", out / "BOQ_REPORT.pdf")
    R["log"].append({"step": "8 export", "seconds": round(time.perf_counter() - t, 3)})
    (out / "run_log.json").write_text(_jdump({"steps": R["log"], "seconds_compute": R["seconds"],
                                              "manual_interventions_during_run": 0,
                                              "outputs": res}), encoding="utf-8")
    return res


PDF_SCRIPT = r"""
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: process.env.M1_CHROMIUM });
  const p = await b.newPage();
  await p.emulateMedia({ media: 'print', colorScheme: 'light' });
  await p.goto('file://' + process.env.M1_HTML, { waitUntil: 'load' });
  await p.pdf({ path: process.env.M1_PDF, format: 'A4', printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="font:7px Arial,sans-serif;color:#777;width:100%;padding:0 10mm;display:flex;' +
      'justify-content:space-between"><span>Planning estimate - not engineering-approved - unresolved items are ' +
      'not in any total</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
    margin: { top: '10mm', bottom: '13mm', left: '10mm', right: '10mm' } });
  await b.close();
})();
"""


def print_pdf(html, pdf):
    if not Path(CHROMIUM).exists():
        return {"skipped": "Chromium not found"}
    sha = hashlib.sha256(Path(html).read_bytes()).hexdigest()
    env = dict(os.environ, M1_HTML=str(Path(html).resolve()), M1_PDF=str(Path(pdf).resolve()), M1_CHROMIUM=CHROMIUM)
    subprocess.run(["node", "-"], input=PDF_SCRIPT.encode(), env=env, check=True, cwd=str(Path(html).parent),
                   capture_output=True)
    from pypdf import PdfReader, PdfWriter
    r = PdfReader(str(pdf))
    w = PdfWriter(clone_from=r)
    w._info = None
    w.add_metadata({"/Title": "Structural BOQ planning estimate", "/Producer": "Chromium via urban_structural_boq",
                    "/Subject": f"rendering of BOQ_REPORT.html sha256 {sha}"})
    with open(pdf, "wb") as fh:
        w.write(fh)
    return {"pdf": Path(pdf).name, "pages": len(r.pages), "html_sha256": sha}


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="urban_structural_boq", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "inventory"):
        p = sub.add_parser(name)
        p.add_argument("--drawings", nargs="+", required=True)
        p.add_argument("--out", required=True)
        if name == "run":
            p.add_argument("--conventions")
            p.add_argument("--set", action="append", default=[], metavar="ID=VALUE")
            p.add_argument("--profile")
            p.add_argument("--no-pdf", action="store_true")
            p.add_argument("--no-xlsx", action="store_true")
            p.add_argument("--as-of", default=datetime.now().strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    if a.cmd == "inventory":
        inputs = accept(a.drawings)
        invs, _ = inventories(inputs)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "INVENTORY.json").write_text(_jdump(invs), encoding="utf-8")
        (out / "PROFILE_TEMPLATE.json").write_text(_jdump(DI.profile_template(invs[0])), encoding="utf-8")
        print(json.dumps({"inventory": str(out / "INVENTORY.json"), "frames": [len(i["frames"]) for i in invs]}))
        return 0
    R = compute(a.drawings, conventions=a.conventions, overrides=parse_sets(a.set), profile=a.profile)
    res = write_all(R, a.out, as_of=a.as_of, pdf=not a.no_pdf, xlsx=not a.no_xlsx)
    s = R["summary"]
    print(json.dumps({"route": s["route"], "concrete_m3": {k: round(s["totals"]["CONCRETE"][k], 3) for k in
                                                          ("VERIFIED", "PLANNING_LOW", "PLANNING_BASE",
                                                           "PLANNING_HIGH")},
                      "unresolved": {t: s["totals"][t]["N_UNRESOLVED"] for t in s["totals"]},
                      "exceptions": s["n_exceptions"], "outputs": res["files"] + [k for k in ("xlsx", "pdf")
                                                                                  if k in res]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
