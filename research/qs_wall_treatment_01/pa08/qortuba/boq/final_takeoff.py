"""The Qortuba quantity set as it stands before anybody writes a rate against it.

Two artifacts live here.  The first is the frozen pre-pricing takeoff: every measured quantity, its formula, its rule
and its status, sealed at a commit so that a later price cannot quietly move a measurement.  The second is the
comparison against the contractor's own aggregate sheet.

The comparison is validation, not correction.  The contractor measured the same flat under a commercial convention of
his own - what he bundles, what he halves, what he calls one item - and our figure comes from the drawing under
Urban's rules.  Where they agree closely the agreement means something, because neither was fitted to the other.
Where they differ the difference is a scope or basis question to be understood, and our number is not moved to close
it.  An item that is not the same item is NOT_COMPARABLE and is said to be.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
EXT = Path(PR.OUT_DIR) / "pa08_qortuba_ext01"

# Which of our rows a contractor line can honestly be set beside, and what would make them differ.
COMPARISON = [
    ("CC-01", "ceramic / porcelain floor", ["Q-13"],
     "the contractor bills one floor-tiling line; ours is the dry porcelain area alone, with the bathroom and pantry "
     "ceramic measured separately as Q-11 and Q-12"),
    ("CC-02", "hidden skirting", ["Q-01"],
     "the same payable path measured two ways: his tape around the rooms, ours the frozen room-side finish runs less "
     "the clear width of every opening that interrupts them"),
    ("CC-03", "hidden profile above the skirting", ["Q-02"],
     "the same path as the skirting, as US-08 requires and as his own sheet repeats"),
    ("CC-04", "bathrooms and kitchens", ["Q-05", "Q-06", "Q-11", "Q-12"],
     "one bundled wet-area line.  Ours separates bathroom wall ceramic, pantry wall ceramic and the two floors, and "
     "the wall part is measured to the 3.00 m tile height rather than to whatever height he tiled"),
    ("CC-05", "corners plus grooves", None,
     "a linear trim item with no measured counterpart in our takeoff: no corner or groove length has been established "
     "from the drawing, and inventing one to match a contractor's sheet is exactly what a benchmark must not do"),
    ("CC-06", "chamfered corners", None,
     "the same: a trim length that exists in his commercial convention and not in the frozen geometry"),
]


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def takeoff():
    qs = reg("QORTUBA_RECALCULATED_QUANTITIES_V1")
    rows = []
    for x in qs["ROWS"]:
        if x["STATUS"] == "NOT_APPLICABLE":
            continue
        rows.append({
            "QUANTITY_ID": x["QUANTITY_ID"], "TRADE": x["TRADE"], "ITEM": x["BOQ_ITEM"],
            "QUANTITY": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"],
            "STATUS": x["STATUS"], "FORMULA": x["FORMULA"],
            "RULE_ID": x["RULE_ID"], "SOURCE": x["PARAMETER_SOURCE"],
            "ROOMS": x["ROOMS"],
            "PHYSICAL_QUANTITY_STATE": x.get("PHYSICAL_QUANTITY_STATE"),
            "COMMERCIAL_ITEM_MAPPING": x.get("COMMERCIAL_ITEM_MAPPING"),
            "MAXIMUM_REMAINING_MOVEMENT_M2": x.get("MAXIMUM_REMAINING_MOVEMENT_M2"),
        })
    rows.sort(key=lambda z: (z["TRADE"], z["QUANTITY_ID"]))
    return rows


def contractor_comparison():
    ours = {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}
    cc = {r["ROW_ID"]: r for r in reg("QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER", EXT)["ROWS"]}
    out = []
    for cid, what, qids, why in COMPARISON:
        c = cc[cid]
        if not qids:
            out.append({"CONTRACTOR_ROW": cid, "CONTRACTOR_TEXT_AR": c["RAW_ARABIC_TEXT"], "ITEM": what,
                        "CONTRACTOR_QUANTITY": c["QUANTITY"], "CONTRACTOR_UNIT": c["UNIT"],
                        "OUR_QUANTITY_IDS": [], "OUR_QUANTITY": None, "OUR_UNIT": None,
                        "DELTA": None, "DELTA_PCT": None,
                        "LIKELY_BASIS_OR_SCOPE_DIFFERENCE": why, "STATUS": "NOT_COMPARABLE"})
            continue
        mine = round(sum(ours[q]["MEASURED_NET_QUANTITY"] for q in qids), 4)
        unit = ours[qids[0]]["UNIT"]
        delta = round(mine - c["QUANTITY"], 4)
        pct = round(100.0 * delta / c["QUANTITY"], 2) if c["QUANTITY"] else None
        out.append({"CONTRACTOR_ROW": cid, "CONTRACTOR_TEXT_AR": c["RAW_ARABIC_TEXT"], "ITEM": what,
                    "CONTRACTOR_QUANTITY": c["QUANTITY"], "CONTRACTOR_UNIT": c["UNIT"],
                    "OUR_QUANTITY_IDS": qids, "OUR_QUANTITY": mine, "OUR_UNIT": unit,
                    "DELTA": delta, "DELTA_PCT": pct,
                    "LIKELY_BASIS_OR_SCOPE_DIFFERENCE": why,
                    "STATUS": ("CLOSE_AGREEMENT" if pct is not None and abs(pct) <= 2.0
                               else "DIFFERENT_BASIS_OR_SCOPE")})
    return out


def finish():
    rows = takeoff()
    cmp_rows = contractor_comparison()
    body = json.dumps(rows, sort_keys=True, ensure_ascii=False, default=str).encode()
    by_status = {}
    for r in rows:
        by_status[r["STATUS"]] = by_status.get(r["STATUS"], 0) + 1
    rec = {
        "ARTIFACT": "QORTUBA_FINAL_PRE_PRICING_TAKEOFF",
        "WHAT_THIS_IS": "the Urban Projects quantity set BEFORE any unit rate is written against it.  It is frozen so "
                        "that a price can never quietly move a measurement, and it is not edited afterwards to match "
                        "a contractor's sheet",
        "STOREY": reg("FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01", Path(PR.OUT_DIR) / "pa08_qortuba_qs01")["STOREY"],
        "ROWS": rows, "COUNT": len(rows), "BY_STATUS": by_status,
        "RATES_SUPPLIED": 0, "WASTE_APPLIED": False,
        "CONTRACTOR_COMPARISON": cmp_rows,
        "CONTRACTOR_COMPARISON_RULE": "validation only.  No Qortuba quantity is moved to agree with a contractor "
                                      "figure, and an item that is not the same item is NOT_COMPARABLE",
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
        "WORKING_TREE_CLEAN": _git("status", "--porcelain") == "",
        "DIGEST": hashlib.sha256(body).hexdigest()[:16],
    }
    (OUT / "QORTUBA_FINAL_PRE_PRICING_TAKEOFF.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['COUNT']} rows  digest {r['DIGEST']}  head {r['GIT_HEAD']}  clean {r['WORKING_TREE_CLEAN']}")
    print("by status:", r["BY_STATUS"])
    print()
    print(f"{'item':38s} {'ours':>12s} {'contractor':>12s} {'delta':>10s} {'%':>8s}  status")
    for c in r["CONTRACTOR_COMPARISON"]:
        o = f"{c['OUR_QUANTITY']:.3f}" if c["OUR_QUANTITY"] is not None else "-"
        d = f"{c['DELTA']:+.3f}" if c["DELTA"] is not None else "-"
        p = f"{c['DELTA_PCT']:+.2f}" if c["DELTA_PCT"] is not None else "-"
        print(f"{c['ITEM'][:38]:38s} {o:>12s} {c['CONTRACTOR_QUANTITY']:>12} {d:>10s} {p:>8s}  {c['STATUS']}")
