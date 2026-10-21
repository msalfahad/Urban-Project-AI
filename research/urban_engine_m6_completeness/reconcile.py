"""M6 reconciliation: the frozen ST7757 completeness runs against the freelancer BOQ and both MCP reports.

    python3 -I research/urban_engine_m6_completeness/reconcile.py [--write]

Runs: V1 - the blind run (01_BLIND_RUN_FREEZE.json, engine 090a470); V2 - the post-discovery run of the V2 engine
(03_V2_RUN_FREEZE.json; its rules were written after V1 was reconciled, so it is NOT blind and is never presented as
blind validation - the held-out synthetic villas are). Matchers, both applied to both runs in the same way:
  M1  the V1 matcher as first written (family + storey; marks by token; special families by family alone)
  M2  written before the V2 run was frozen: M1, plus (a) a finding that names the element's own route item (ITEMS)
      or drawing entity (the DXF handle the M5 membership records) reports that element, (b) a finding of family
      UNKNOWN whose evidence lists the element's family among its candidates ('could be ...') reports a special
      element as DETECTED_UNIDENTIFIED, (c) blinding (plain concrete) is outside an RC completeness count.

Phase RECONCILIATION (engine/benchmark_protection): only after a run is frozen (its manifest's file hashes are
checked here) are the external records opened - through the M5 package's own readers and its
element crosswalk (research/urban_engine_m5_concrete_reconciliation: 03 / 03A). They are evidence of what EXISTS on
the drawings; they never choose a reading and never tune a detector.

Questions, element by element (the M5 crosswalk, 157 groups):
  1. does an external source price it (freelancer row, MCP category)? does an Urban S-stage register measure it?
  2. does the generic takeoff hold it (route-G items, the takeoff the completeness pass audits)?
  3. if the takeoff misses it or holds it unresolved: did the frozen completeness run flag it (family and storey,
     with the finding ids as evidence)?
and, finding by finding: is it supported by an external source (it holds more where the finding says something is
missing; less where the finding says something is counted twice / over-counted), or is it engine-only?
The misses are the weaknesses M6 V2 is built from. Nothing here moves a quantity.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
M5 = ROOT / "research/urban_engine_m5_concrete_reconciliation"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import benchmark_protection as bp      # noqa: E402

# M5 element families -> the completeness engine's families
FAMILY = {"FOOTINGS": ("FOOTINGS",), "NECKS": ("COLUMNS",), "STRAPS": ("GROUND_BEAMS",),
          "GROUND_BEAMS": ("GROUND_BEAMS",), "GB_PERIMETER": ("GROUND_BEAMS", "BOUNDARY_WALL"),
          "GROUND_SLAB": ("SLABS",), "COLUMNS": ("COLUMNS",), "BEAMS": ("BEAMS",), "SLABS": ("SLABS",),
          "LINTELS": ("BEAMS",), "STAIRS": ("STAIRS",), "DOMES": ("DOMES",), "POOL": ("POOL",),
          "POOL_PUMP_ROOM": ("POOL",), "LIFT": ("LIFT",), "BOUNDARY_WALL": ("BOUNDARY_WALL",),
          "WATER_TANK": ("WATER_TANK",), "PARAPETS": ("PARAPETS",), "CANTILEVER_PORTIONS": ("CANTILEVER",),
          "BLINDING": ()}
SPECIAL = ("STAIRS", "DOMES", "POOL", "POOL_PUMP_ROOM", "LIFT", "BOUNDARY_WALL", "WATER_TANK", "PARAPETS",
           "CANTILEVER_PORTIONS", "GB_PERIMETER")
STOREYS = {"GF": ("GF",), "1F": ("1F",), "2F": ("2F",), "GROUND": ("GROUND",), "FOUNDATION": ("FOUNDATION", "GROUND"),
           "ROOF": ("2F", "1F", "GF", "ALL"), "SITE": None, "ALL": None, "UNKNOWN": None}
# M5 classes of an external item that has no drawing behind it: the engine is right to be silent
NO_DRAWING = ("SOURCE_CONFLICT",)
RUNS = {"V1": ("01_BLIND_RUN_FREEZE.json", "blind/COMPLETENESS_FINDINGS.csv"),
        "V2": ("03_V2_RUN_FREEZE.json", "post_discovery_v2/COMPLETENESS_FINDINGS.csv")}
NOT_RC = ("BLINDING",)                         # M2: plain concrete, outside an RC completeness count
ITEM_KINDS_EXCLUDED = ("UNRESOLVED_ITEMS", "DEPENDENCY")      # M2: list items without saying anything is missing
HANDLE = re.compile(r"\bDXF ([0-9A-F]{2,8})\b")
CANDIDATES = re.compile(r"could be ([A-Z_]+(?: or [A-Z_]+)*)")
MISSING_KINDS = ("DRAWN_NOT_MEASURED", "STAIR_NOT_MEASURED", "LABEL_NOT_CONSUMED", "PLACED_NOT_SCHEDULED",
                 "COLUMN_PRESENCE_NOT_ITEMIZED", "REGION_EXCLUDED", "SCHEDULE_ROW_UNREAD", "MEMBER_DETECTED_NOT_ITEMIZED",
                 "STOREY_PLAN_MISSING", "STOREY_COLUMN_BANDS_MISSING", "SLAB_COVERAGE_LOW", "UNRESOLVED_ITEMS",
                 "REFERENCED_NOT_DRAWN", "COLUMN_BAND_NOT_ON_PLAN", "LABEL_MEMBER_CONFLICT", "DEPENDENCY")
OVER_KINDS = ("COLUMN_ITEM_WITHOUT_PRESENCE", "MEMBER_OVERLAP", "MEMBER_OUTLINE_SUSPECT", "OPENING_NOT_DEDUCTED")


def _csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def frozen(run="V1"):
    """a frozen run, verified against its freeze manifest (any edit after the freeze is refused)."""
    mname, fpath = RUNS[run]
    man = json.loads((PKG / mname).read_text(encoding="utf-8"))
    for name, sha in man["files_sha256"].items():
        if hashlib.sha256((PKG / name).read_text(encoding="utf-8").encode("utf-8")).hexdigest() != sha:
            raise ValueError(f"{name} changed after the {run} freeze")
    if not bp.may_reconcile(man):
        raise ValueError("no frozen candidate: reconciliation refused")
    return man, _csv(PKG / fpath)


def external():
    """the M5 element crosswalk and its membership (freelancer rows, Urban items by origin), and the MCP rows."""
    sys.path.insert(0, str(M5))
    import m5_sources as S
    rows = _csv(M5 / "03_ELEMENT_BY_ELEMENT_COMPARISON.csv")
    members = defaultdict(list)
    for m in _csv(M5 / "03A_ELEMENT_MEMBERSHIP.csv"):
        members[m["ELEMENT_ID"]].append(m)
    mcp = S.mcp()["rows"]
    return bp.withhold({"elements": rows, "members": dict(members), "mcp": mcp}, phase=bp.RECONCILIATION)["payload"]


def _route(members):
    """what the generic takeoff holds for an element: route-G items (M4 V3 run) and the V4 planted columns."""
    base = cond = 0.0
    n_m = n_c = 0
    for m in members:
        src = m["SOURCE"]
        if not (src == "URBAN M4" or src.startswith("URBAN M5 (printed label)")):
            continue
        if m["STATE"] == "MEASURED":
            base += _f(m["BASE_M3"])
            n_m += 1
        elif m["STATE"] in ("CONDITIONAL", "UNMEASURABLE"):
            cond += _f(m["EXPOSURE_HIGH_M3"])
            n_c += 1
    return base, cond, n_m, n_c


def _stage(members):
    return sum(_f(m["BASE_M3"]) for m in members if m["SOURCE"].startswith("URBAN M1") and m["STATE"] == "MEASURED")


def _mcp_family(mcp):
    out = defaultdict(dict)
    key = {"STAIRS": "STAIRS", "DOME": "DOMES", "POOL": "POOL", "STRAP_BEAMS": "STRAPS", "GROUND_SLAB": "GROUND_SLAB",
           "GROUND_BEAMS": "GROUND_BEAMS", "FOUNDATIONS": "FOOTINGS"}
    for r in mcp:
        fam = key.get(r["category"])
        if fam:
            for src in ("UC4N", "CHRISTIANNP"):
                if r.get(src):
                    out[fam][src] = r[src]
    return out


def _matches(el, f):
    fams = FAMILY.get(el["FAMILY"], ())
    sto = STOREYS.get(el["FLOOR"])
    if f["FAMILY"] not in fams:
        shape_ok = el["FAMILY"] in ("DOMES",) and f["FAMILY"] == "UNKNOWN" and re.search(
            r"shape (RADIAL|CURVED)|radiate", f["EVIDENCE"])
        if not shape_ok:
            return False
    if sto is not None and f["STOREY"] not in sto and f["STOREY"] not in ("ALL", ""):
        return False
    if el["FAMILY"] in SPECIAL:
        return True
    tok = el["MARK_OR_PART"]
    if f["KIND"] in ("LABEL_NOT_CONSUMED", "PLACED_NOT_SCHEDULED", "SCHEDULED_NOT_PLACED", "LABEL_MEMBER_CONFLICT"):
        return bool(tok) and re.search(r"(?<![A-Z0-9])" + re.escape(tok) + r"(?![A-Z0-9])", f["EVIDENCE"]) is not None
    if f["KIND"] == "UNRESOLVED_ITEMS":
        return tok in ("UNLABELLED", "ALL", "CN") or tok in f["EVIDENCE"] or tok in f["ITEMS"]
    if f["KIND"] in ("COLUMN_ITEM_WITHOUT_PRESENCE",):
        return bool(tok) and (f":{tok}@" in f["ITEMS"] or f":{tok}@" in f["REFS"])
    return el["FAMILY"] in ("GROUND_SLAB", "SLABS") or tok in ("UNLABELLED", "ALL")


def _route_ids(members):
    return {m["RECORD_ID"] for m in members if m["SOURCE"] == "URBAN M4" or
            m["SOURCE"].startswith("URBAN M5 (printed label)")}


BASIS_ORDER = ("ENTITY", "ITEM", "M1", "CANDIDATES")


def _matches_m2(el, f, members):
    """the basis on which the finding reports the element (ENTITY / ITEM: that very element; M1: family, storey and
    mark; CANDIDATES: an unidentified finding of the storey that lists the family), or None."""
    refs = {x for x in re.split(r"[,;| ]+", f["REFS"] or "") if x}
    if refs & {h for m in members for h in HANDLE.findall(m.get("LOCATION") or "")}:
        return "ENTITY"                                # the finding names the element's drawing entity
    if f["KIND"] not in ITEM_KINDS_EXCLUDED and _route_ids(members) & {x for x in f["ITEMS"].split(",") if x}:
        return "ITEM"                                  # ... or its own route item
    if _matches(el, f):
        return "M1"
    c = CANDIDATES.search(f["EVIDENCE"])
    if f["FAMILY"] == "UNKNOWN" and c and el["FAMILY"] in SPECIAL and \
            set(c.group(1).split(" or ")) & set(FAMILY.get(el["FAMILY"], ())):
        sto = STOREYS.get(el["FLOOR"])
        if sto is None or f["STOREY"] in sto or f["STOREY"] in ("ALL", ""):
            return "CANDIDATES"
    return None


def reconcile(run="V1", matcher="M1", ext=None):
    man, F = frozen(run)
    ext = ext or external()
    mcpf = _mcp_family(ext["mcp"])
    rows, used = [], defaultdict(list)
    for el in ext["elements"]:
        mem = ext["members"].get(el["ELEMENT_ID"], [])
        fl = _f(el["FREELANCER_M3"])
        mc = mcpf.get(el["FAMILY"], {})
        rb, rc, n_m, n_c = _route(mem)
        st = _stage(mem)
        ref = max(fl, _f(el["URBAN_MEASURED_BASE_M3"]), st)
        evidence = [s for s, v in (("FREELANCER", fl), ("URBAN_STAGE", st)) if v > 0] + \
            [f"MCP_{k}" for k, v in mc.items() if v and el["FAMILY"] in ("STAIRS", "DOMES", "POOL")]
        if not evidence and _f(el["URBAN_CONDITIONAL_HIGH_M3"]) > 0:
            evidence = ["URBAN_CONDITIONAL"]
        if rb >= 0.5 * ref and ref > 0:
            route = "HOLDS"
        elif rb > 0:
            route = "HOLDS_PART"
        elif n_c:
            route = "HOLDS_UNRESOLVED"
        else:
            route = "ABSENT"
        basis = {f["FINDING_ID"]: (_matches_m2(el, f, mem) if matcher == "M2" else "M1" if _matches(el, f)
                                   else None) for f in F}
        hits = [f for f in F if basis[f["FINDING_ID"]]]
        for f in hits:
            used[f["FINDING_ID"]].append(el)
        if matcher == "M2" and el["FAMILY"] in NOT_RC:
            verdict = "OUT_OF_RC_SCOPE"
        elif route == "HOLDS" or not evidence:
            verdict = "NOT_A_COMPLETENESS_CASE" if route == "HOLDS" else "NO_EVIDENCE_OF_THE_ELEMENT"
        elif el["CLASS"].startswith(NO_DRAWING) or "not drawn" in el["EXPLANATION"].lower():
            verdict = "FLAGGED_ALTHOUGH_NOT_DRAWN" if hits else "CORRECTLY_SILENT_NOT_DRAWN"
        elif hits:
            fam_right = any(f["FAMILY"] in FAMILY.get(el["FAMILY"], ()) for f in hits)
            verdict = "DETECTED" if fam_right else "DETECTED_UNIDENTIFIED"
        else:
            verdict = "MISSED"
        rows.append({"ELEMENT_ID": el["ELEMENT_ID"], "FAMILY": el["FAMILY"], "FLOOR": el["FLOOR"],
                     "MARK_OR_PART": el["MARK_OR_PART"], "EXTERNAL_EVIDENCE": "+".join(evidence),
                     "FREELANCER_M3": round(fl, 3), "MCP": json.dumps(mc, sort_keys=True) if mc else "",
                     "URBAN_STAGE_M3": round(st, 3), "ROUTE_MEASURED_M3": round(rb, 3),
                     "ROUTE_UNRESOLVED_EXPOSURE_M3": round(rc, 3), "ROUTE": route, "M5_CLASS": el["CLASS"],
                     "VERDICT": verdict, "MATCH_BASIS": min((basis[f["FINDING_ID"]] for f in hits),
                                                            key=BASIS_ORDER.index, default=""),
                     "FINDINGS": ";".join(f"{f['FINDING_ID']}:{f['KIND']}" for f in sorted(
                         hits, key=lambda f: BASIS_ORDER.index(basis[f["FINDING_ID"]]))[:6])})
    frows = []
    for f in F:
        els = used.get(f["FINDING_ID"], [])
        sup, contra = [], []
        for el in els:
            r = next(x for x in rows if x["ELEMENT_ID"] == el["ELEMENT_ID"])
            fl, rb = r["FREELANCER_M3"], r["ROUTE_MEASURED_M3"]
            if f["KIND"] in OVER_KINDS:
                (sup if fl and fl < rb else contra if fl > rb else sup).append(el["ELEMENT_ID"]) if fl else None
            elif r["EXTERNAL_EVIDENCE"] and r["ROUTE"] != "HOLDS":
                sup.append(el["ELEMENT_ID"])
        state = "SUPPORTED_BY_EXTERNAL" if sup else "CONTRADICTED" if contra else \
            "LINKED_ELEMENT_HELD" if els else "ENGINE_ONLY"
        frows.append({"FINDING_ID": f["FINDING_ID"], "SEVERITY": f["SEVERITY"], "KIND": f["KIND"],
                      "FAMILY": f["FAMILY"], "SHEET": f["SHEET"], "STOREY": f["STOREY"], "STATE": state,
                      "SUPPORTING_ELEMENTS": ";".join(sup[:6]), "LINKED_ELEMENTS": ";".join(e["ELEMENT_ID"]
                                                                                       for e in els[:6]),
                      "EVIDENCE": f["EVIDENCE"][:220]})
    cases = [r for r in rows if r["VERDICT"] in ("DETECTED", "DETECTED_UNIDENTIFIED", "MISSED")]
    summ = {
        "phase": bp.RECONCILIATION, "run": run, "matcher": matcher, "run_phase": man.get("run_phase", man["phase"]),
        "frozen_hash": man["CANDIDATE_GEOMETRY_HASH"], "engine_commit": man["engine_commit"],
        "elements": len(rows), "verdicts": dict(sorted(Counter(r["VERDICT"] for r in rows).items())),
        "completeness_cases": len(cases),
        "detected": sum(1 for r in cases if r["VERDICT"] == "DETECTED"),
        "detected_unidentified": sum(1 for r in cases if r["VERDICT"] == "DETECTED_UNIDENTIFIED"),
        "detected_by_basis": dict(sorted(Counter(r["MATCH_BASIS"] for r in cases if r["VERDICT"] != "MISSED")
                                         .items())),
        "missed": [r["ELEMENT_ID"] for r in cases if r["VERDICT"] == "MISSED"],
        "missed_m3_external": round(sum(max(r["FREELANCER_M3"], r["URBAN_STAGE_M3"]) for r in cases
                                        if r["VERDICT"] == "MISSED"), 3),
        "findings": len(F), "finding_states": dict(sorted(Counter(r["STATE"] for r in frows).items())),
        "rule": "external records are evidence of what exists; they never choose a reading or tune a detector",
    }
    return rows, frows, summ


def _text(rows):
    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def outputs():
    """every available run under both matchers: the summary, the element table (four verdicts side by side) and
    each run's findings against the external records (M2)."""
    ext = external()
    runs = [r for r in RUNS if (PKG / RUNS[r][0]).exists()]
    res = {(r, m): reconcile(r, m, ext) for r in runs for m in ("M1", "M2")}
    summary = {"phase": bp.RECONCILIATION, "runs": runs,
               "matchers": {"M1": "family + storey; marks by token; special families by family alone (V1, as first "
                                  "written)",
                            "M2": "M1 + the finding names the element's route item or DXF entity; an UNKNOWN finding "
                                  "listing the element's family among its candidates (special families, as "
                                  "unidentified); blinding outside the RC count (written before the V2 run froze)"},
               "results": {f"{r}_{m}": {k: v for k, v in res[(r, m)][2].items() if k not in ("phase",)}
                           for r, m in res},
               "rule": "external records are evidence of what exists; they never choose a reading or tune a "
                       "detector; V2 is post-discovery (not blind) - its generalisation evidence is the held-out "
                       "synthetic villas"}
    base = res[(runs[0], "M1")][0]
    els = []
    for i, r in enumerate(base):
        row = {k: r[k] for k in ("ELEMENT_ID", "FAMILY", "FLOOR", "MARK_OR_PART", "EXTERNAL_EVIDENCE",
                                 "FREELANCER_M3", "URBAN_STAGE_M3", "ROUTE_MEASURED_M3", "ROUTE", "M5_CLASS")}
        for (rn, m), (rows, _, _) in res.items():
            row[f"{rn}_{m}"] = rows[i]["VERDICT"]
        for rn in runs:
            row[f"{rn}_M2_BASIS"] = res[(rn, "M2")][0][i]["MATCH_BASIS"]
            row[f"{rn}_M2_FINDINGS"] = res[(rn, "M2")][0][i]["FINDINGS"]
        els.append(row)
    out = {"reconciliation/01_RECONCILIATION_SUMMARY.json": json.dumps(summary, indent=1) + "\n",
           "reconciliation/02_ELEMENTS_VS_COMPLETENESS.csv": _text(els)}
    for rn in runs:
        out[f"reconciliation/03_FINDINGS_VS_EXTERNAL_{rn}.csv"] = _text(res[(rn, "M2")][1])
    return out


def main(argv):
    out = outputs()
    s = json.loads(out["reconciliation/01_RECONCILIATION_SUMMARY.json"])
    print(json.dumps({k: {x: v[x] for x in ("completeness_cases", "detected", "detected_unidentified", "missed",
                                            "findings")} for k, v in s["results"].items()}, indent=1))
    if "--write" in argv:
        (PKG / "reconciliation").mkdir(exist_ok=True)
        for k, v in out.items():
            (PKG / k).write_text(v, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
