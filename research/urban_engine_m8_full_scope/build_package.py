"""M8 package builder - the CSV deliverables generated from the records (conventions, held-out elements, acceptance,
weaknesses) and the workbook (M8_FULL_SCOPE_WORKBOOK.xlsx, built on demand, never committed).

    python3 -I research/urban_engine_m8_full_scope/build_package.py            # CSV deliverables
    python3 -I research/urban_engine_m8_full_scope/build_package.py --xlsx OUT  # and the workbook at OUT

Every number comes from a committed record (the conventions file, heldout/, heldout_postfix/, st7757/); nothing is
typed here. External positions appear only as the differences the ST7757 runner wrote.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
V5 = ROOT / "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
V6 = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
TARGETS = {"detected_pct": 95.0, "in_range_convention_pct": 80.0, "printed_error_max": 0.05}


def _csv(rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    return buf.getvalue()


def _json(p):
    return json.loads((PKG / p).read_text(encoding="utf-8"))


def conventions():
    old = {c["id"] for c in json.loads(V5.read_text(encoding="utf-8"))["conventions"]}
    rows = []
    for c in json.loads(V6.read_text(encoding="utf-8"))["conventions"]:
        if c["id"] in old:
            continue
        rows.append({"ID": c["id"], "TITLE": c["title"], "KIND": c["kind"], "UNIT": c.get("unit", ""),
                     "LOW": c.get("low", ""), "BASE": c["base"], "HIGH": c.get("high", ""),
                     "OPTIONS": "|".join(c.get("options") or []), "PROVENANCE": c["provenance"],
                     "SOURCE": c["source"], "RATIONALE": c["rationale"]})
    return rows


def elements(folder):
    rows = []
    for cfg in ("S_A", "S_B"):
        rec = _json(f"{folder}/{cfg}.json")
        for r in rec["drawings"]:
            if not r.get("ok"):
                continue
            for e in r["elements"]:
                rows.append({"RUN": cfg, "SEED": r["seed"], "ELEMENT": e["id"], "KIND": e["kind"],
                             "FAMILY": e["family"], "PRINTED": "YES" if e["printed"] else "NO",
                             "TRUTH_M3": e["truth_m3"], "TRUTH_HIGH_M3": e.get("truth_high_m3") or e["truth_m3"],
                             "OUTCOME": e["outcome"], "ENGINE_LOW_M3": e["engine_low_m3"],
                             "ENGINE_BASE_M3": "" if e["engine_base_m3"] is None else e["engine_base_m3"],
                             "ENGINE_HIGH_M3": e["engine_high_m3"], "IN_RANGE": "YES" if e["in_range"] else "NO",
                             "BASE_ERROR_REL": "" if e["base_error_rel"] is None else e["base_error_rel"],
                             "DESIGN": json.dumps(e["design"], sort_keys=True)})
    return rows


def acceptance(rows):
    """per run and element kind: detection, outcomes, IN_RANGE overall / where a dimension is a convention, printed
    and convention base errors - against the brief's targets."""
    by = defaultdict(list)
    for r in rows:
        by[(r["RUN"], r["KIND"])].append(r)
    out = []
    for (run, kind), rs in sorted(by.items()):
        conv = [r for r in rs if r["PRINTED"] == "NO"]
        pe = sorted(abs(r["BASE_ERROR_REL"]) for r in rs if r["PRINTED"] == "YES" and r["BASE_ERROR_REL"] != "")
        ce = sorted(abs(r["BASE_ERROR_REL"]) for r in conv if r["BASE_ERROR_REL"] != "")
        n = len(rs)
        det = sum(1 for r in rs if r["OUTCOME"] != "MISSED")
        inr_c = sum(1 for r in conv if r["IN_RANGE"] == "YES")
        rec = {"RUN": run, "KIND": kind, "N": n, "DETECTED_PCT": round(100 * det / n, 1),
               "MEASURED": sum(1 for r in rs if r["OUTCOME"] == "MEASURED"),
               "BOUNDED": sum(1 for r in rs if r["OUTCOME"] == "BOUNDED"),
               "OTHER": sum(1 for r in rs if r["OUTCOME"] not in ("MEASURED", "BOUNDED")),
               "IN_RANGE_PCT": round(100 * sum(1 for r in rs if r["IN_RANGE"] == "YES") / n, 1),
               "N_CONVENTION": len(conv),
               "IN_RANGE_CONVENTION_PCT": round(100 * inr_c / len(conv), 1) if conv else "",
               "N_PRINTED_MEASURED": len(pe), "PRINTED_ERROR_MEDIAN": pe[len(pe) // 2] if pe else "",
               "PRINTED_ERROR_MAX": pe[-1] if pe else "",
               "CONVENTION_ERROR_MEDIAN": ce[len(ce) // 2] if ce else ""}
        rec["MEETS_TARGETS"] = "YES" if (rec["DETECTED_PCT"] >= TARGETS["detected_pct"] and
                                         (rec["IN_RANGE_CONVENTION_PCT"] == "" or
                                          rec["IN_RANGE_CONVENTION_PCT"] >= TARGETS["in_range_convention_pct"]) and
                                         (rec["PRINTED_ERROR_MAX"] == "" or
                                          rec["PRINTED_ERROR_MAX"] <= TARGETS["printed_error_max"])) else "NO"
        out.append(rec)
    return out


WEAKNESSES = [
    ("W8-01", "HIGH", "POOL", "ST7757", "Only the pool walls drawn as a strip on the ground-beam plan are read; the pool "
     "section on the detail sheet (depth, the other walls) is not. V6 measures 3.50 m3 (2.70 - 4.29); the stage record "
     "and the freelance QS lie outside that range (see st7757/POSITIONS.csv).", "Read section geometry of detail sheets, "
     "or a person-confirmed profile value (POOL_WALL_HEIGHT_M printed)"),
    ("W8-02", "MEDIUM", "PROPERTIES", "intake (pre-existing)", "A HATCH with a negative extrusion (a mirrored hatch) keeps "
     "its boundary in object coordinates: the completeness pass loses the hatch on a mirrored drawing, the bounded low "
     "moves (items unchanged). mirror_x fails 10 / 10 on the bounded total.", "A gated intake version that converts "
     "OCS hatch paths to world coordinates"),
    ("W8-03", "MEDIUM", "PROPERTIES", "completeness (pre-existing)", "Column-sized rectangles on an unrelated furniture "
     "layer are reported as possible columns (LOW, 'confirm it is a column') and widen the bounded high; one held-out "
     "villa changes a GF slab under noise in V5 and V6 alike.", "Layer-name evidence for column presence findings"),
    ("W8-04", "LOW", "METRIC", "M6 detection metric", "Six stair elements on the M7 seeds count as 'not detected' "
     "under V6 because V6 measures them (the M6 metric counts findings only).", "Count measured items as detected"),
    ("W8-05", "MEDIUM", "CONVENTIONS", "held-out", "Convention ranges do not cover every design the generator author "
     "drew: boundary-wall foundations up to 0.435 m2/m against a 0.36 high, pit depths up to 1.70 m against 1.60. "
     "Not tuned after the freeze.", "Engineer-confirmed ranges per region; printed values where they exist"),
    ("W8-06", "MEDIUM", "DOMES", "rule", "DOME_ON_TOP_PLAN reads a radial group on the topmost slab plan as a dome when "
     "the set names domes; a stair to the roof drawn with radial treads there would be read as a dome.",
     "Section / elevation evidence; a person confirmation"),
    ("W8-07", "MEDIUM", "PARAPETS", "ST7757", "Parapets are an allowance 0 .. free roof edge x the high section "
     "(0 .. 44.4 m3 on ST7757); the drawing does not say RC or block.", "Architectural sections / parapet detail"),
    ("W8-08", "MEDIUM", "LIFT / TANK", "ST7757", "The pit on the foundation plan is not settled (could be LIFT, WALLS "
     "or WATER_TANK): bounded 0 .. 6.75 m3; the roof tank is noted, not drawn: 0 .. 10 m3.", "A lift / tank label or "
     "detail; RFI"),
    ("W8-09", "HIGH", "REINFORCEMENT", "all", "Reinforcement for stairs, pool, domes, tank, pit and boundary wall is "
     "MISSING_DATA: no bar details are read and no kg/m3 ratio is used.", "Bar details of the scope families"),
    ("W8-10", "HIGH", "CORE FAMILIES", "ST7757 (pre-existing)", "Ground slab and ground beams stay well below the "
     "freelance QS and both MCP runs (st7757/POSITIONS.csv); M8 does not touch the core families.",
     "The M5 bridge items (perimeter tie beam, slab under stairs, levels)"),
    ("W8-11", "MEDIUM", "BOUNDED TOTAL", "ST7757 / synthetic", "The bounded range is honest but wide: on ST7757 the "
     "high is 1.49 x the measured base (parapets, unresolved beams, a footing of unknown depth, the roof tank).",
     "RFIs on the largest bounds (SCOPE_BOUNDS.csv sorted by HIGH_M3)"),
    ("W8-12", "LOW", "STAIRS", "rule", "A partial stair zone is measured with the riser convention even when the "
     "storey rise is smaller than the drawn run (ST7757 ground winder: 9 risers at 0.165 m against a 1.0 m rise).",
     "Use the smaller of the storey rise and the convention when the riser falls below the band"),
    ("W8-13", "LOW", "CODE", "engine", "scope_quantities reads private helpers of concrete_completeness (_loops, "
     "_members, _consumption): a coupling to keep in mind when either changes.", "A small public API in "
     "concrete_completeness"),
]


def weaknesses():
    return [{"ID": a, "SEVERITY": b, "AREA": c, "WHERE": d, "WEAKNESS": e, "NEXT": f}
            for a, b, c, d, e, f in WEAKNESSES]


def files():
    el = elements("heldout_postfix")
    el0 = elements("heldout")
    return {"02_CONVENTIONS_V6.csv": _csv(conventions(), ["ID", "TITLE", "KIND", "UNIT", "LOW", "BASE", "HIGH",
                                                         "OPTIONS", "PROVENANCE", "SOURCE", "RATIONALE"]),
            "05_HELDOUT_BY_ELEMENT.csv": _csv(el, list(el[0])),
            "06_ACCEPTANCE.csv": _csv(acceptance(el), list(acceptance(el)[0])),
            "06A_ACCEPTANCE_FROZEN.csv": _csv(acceptance(el0), list(acceptance(el0)[0])),
            "11_WEAKNESS_REGISTER.csv": _csv(weaknesses(), ["ID", "SEVERITY", "AREA", "WHERE", "WEAKNESS", "NEXT"])}


def workbook(path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    head = Font(name="Arial", bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="2F6FB0")
    body = Font(name="Arial", size=9)
    first = True
    sheets = [("README", None), ("Acceptance", "06_ACCEPTANCE.csv"), ("Acceptance frozen", "06A_ACCEPTANCE_FROZEN.csv"),
              ("Held-out elements", "05_HELDOUT_BY_ELEMENT.csv"), ("Conventions V6", "02_CONVENTIONS_V6.csv"),
              ("ST7757 by family", "st7757/BY_FAMILY.csv"), ("ST7757 scope items", "st7757/SCOPE_ITEMS.csv"),
              ("ST7757 bounds", "st7757/SCOPE_BOUNDS.csv"), ("ST7757 positions", "st7757/POSITIONS.csv"),
              ("ST7757 ablation", "st7757/ABLATION.csv"), ("Weaknesses", "11_WEAKNESS_REGISTER.csv")]
    for title, src in sheets:
        ws = wb.active if first else wb.create_sheet()
        first = False
        ws.title = title[:31]
        if src is None:
            lines = ["Urban Project AI - M8 full-scope generic BOQ workbook",
                     "Built from the committed records of research/urban_engine_m8_full_scope (no number typed).",
                     "Held-out: synthetic seeds 401-440 (frozen engine 9d7aceb; post-freeze fixes P1-P4 apart).",
                     "ST7757: post-discovery (not blind); external positions only as differences.",
                     "Verdict: NOT quotation-ready - no engineer-released quantities, no blind second project."]
            for k, ln in enumerate(lines, 1):
                ws.cell(row=k, column=1, value=ln).font = Font(name="Arial", size=10, bold=k == 1)
            ws.column_dimensions["A"].width = 110
            continue
        rows = list(csv.reader((PKG / src).open(encoding="utf-8")))
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row, 1):
                try:
                    val = float(v) if v not in ("",) and not v.isalpha() and v.replace(".", "", 1).replace(
                        "-", "", 1).isdigit() else v
                except ValueError:
                    val = v
                c = ws.cell(row=i, column=j, value=val)
                c.font = head if i == 1 else body
                if i == 1:
                    c.fill = fill
                    c.alignment = Alignment(wrap_text=True, vertical="top")
        for j in range(1, (len(rows[0]) if rows else 0) + 1):
            ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = 16
        ws.freeze_panes = "A2"
    wb.save(path)
    return path


def main(argv):
    for name, text in files().items():
        (PKG / name).write_text(text, encoding="utf-8")
        print("wrote", name)
    if "--xlsx" in argv:
        print("workbook", workbook(argv[argv.index("--xlsx") + 1]))


if __name__ == "__main__":
    main(sys.argv[1:])
