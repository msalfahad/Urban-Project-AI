"""T-358 Alsenan check (committed inputs only: ALSENAN_TEMPWORKS_INPUT.json; sheet / note numbers, handles and
plot-local metres). Writes SHEET_SEARCH_T358.csv, EXPOSURE_T358.csv, SIDES_T358.csv, ITEMS_T358.csv and summary.json next
to this file when run as a script; main(write=False) returns the results for the tests."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tempworks_scope_v1 as R  # noqa: E402

INPUT = HERE / "ALSENAN_TEMPWORKS_INPUT.json"


def _union(iv):
    iv = sorted(iv)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1e-9:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return round(sum(b - a for a, b in out), 6), [[round(a, 4), round(b, 4)] for a, b in out]


def line_lengths(exc, rows, plot):
    """Length (m) of each plot side over which an excavation face is ON / BEYOND the line or WITHIN its depth of it."""
    lx, ly = plot
    by_id = {e["id"]: e for e in exc}
    res = {}
    for s in ("S0", "S1", "S2", "S3"):
        out = {}
        for cls in ("ON_OR_BEYOND_LINE", "WITHIN"):
            iv = []
            for r in rows:
                if r["side"] != s or r["class"] != cls:
                    continue
                x0, y0, dx, dy = by_id[r["id"]]["rect_m"]
                p = by_id[r["id"]]["projection_m"] or 0.0
                if s in ("S0", "S1"):
                    iv.append((max(0.0, x0 - p), min(lx, x0 + dx + p)))
                else:
                    iv.append((max(0.0, y0 - p), min(ly, y0 + dy + p)))
            out[cls] = _union(iv)
        res[s] = {"on_or_beyond_m": out["ON_OR_BEYOND_LINE"][0], "on_or_beyond_intervals": out["ON_OR_BEYOND_LINE"][1],
                  "within_only_m": out["WITHIN"][0], "within_intervals": out["WITHIN"][1]}
    return res


def main(write: bool = True):
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    plot = (inp["plot"]["Lx_m"], inp["plot"]["Ly_m"])
    dw = R.dewatering(inp["formations"], inp["water"], note_conditional=True)
    lift = next(r for r in dw["rows"] if r["kind"] == "PARAMETRIC")
    sens_wl = inp["water"]["sensitivity"]["level"]
    sens = {"water_level": sens_wl, "pits_clearance_m": round(-1.5 - sens_wl, 6),
            "lift_threshold_m": round((sens_wl - 0.3) / -1.0, 6)}
    exc = [{"id": e["id"], "rect": e["rect_m"], "projection": e["projection_m"] or 0.0, "depth": e["depth"]}
           for e in inp["excavations"]]
    sup = R.support_by_side(exc, plot, inp["plot"]["sides"])
    lengths = line_lengths(inp["excavations"], sup["rows"], plot)
    beyond = sorted({r["id"] for r in sup["rows"] if r["distance_m"] < -1e-9})
    items = [
        {"item": "B1-06a DEWATERING", "status": dw["status"],
         "trigger": f"water {dw['water_level']:+.2f} (ST p.9 note 4, EG datum INTERPRETED); drawn formations -1.50 (pits / "
                    f"boundary trenches AT_MOST, pool PRINTED): clearance {dw['min_clearance_m']:.2f} m; lift FF "
                    f"{lift['trigger']}; ST p.8 note 14 'if groundwater is found'",
         "source": "ST p.8 note 14; ST p.9 notes 1, 2, 4", "quantity": None, "extent": None},
        {"item": "B1-06b EXCAVATION SUPPORT / PROTECTION", "status": "TRIGGERED",
         "trigger": "ST p.8 note 15 requires a specialist study and the protection / shoring needed; faces on or beyond "
                    "the plot line on all four sides at >= 1.50 m (section 4)",
         "source": "ST p.8 note 15; ST p.1 bullet 2; ST p.14 boundary wall; ST p.9 note 1", "quantity": None, "extent": None},
        {"item": "B1-06c OTHER TEMPORARY WORKS", "status": inp["temporary_other"]["status"],
         "trigger": inp["temporary_other"]["why"], "source": "31 sheets searched", "quantity": None, "extent": None},
    ]
    for it in items:
        R.write_quantity(it)
    summary = {
        "rule": R.RULE_ID,
        "sheets_searched": len(inp["sheet_search"]),
        "sheets_stating": {r["sheet"]: [s["note"] + " " + s["class"] for s in r["states"]]
                           for r in inp["sheet_search"] if r["states"]},
        "dewatering": {"status": dw["status"], "water_level": dw["water_level"], "min_clearance_m": dw["min_clearance_m"],
                       "rows": dw["rows"], "site_condition_note_14": dw["site_condition"],
                       "sensitivity_ffl_datum": sens, "quantity": None},
        "support": {s: {k: v for k, v in d.items()} | lengths[s] for s, d in sup["sides"].items()},
        "beyond_plot_line": beyond,
        "items": items,
        "freelancer_rows": inp["freelancer"]["rows"],
        "engine_lines": inp["engine"]["lines"],
        "verdict_proposal": "SCOPE_ITEMS_NOT_QUANTITIES: both BOQs omit B1-06; the drawings put support in scope "
                            "(TRIGGERED, extent by the contractor's specialist study) and dewatering CONDITIONAL; neither "
                            "carries a drawn extent, so neither BOQ can carry a quantity: RULE_DIFFERENCE none, an item "
                            "line (no quantity) is the correct representation",
    }
    sheet_rows = [{"sheet": r["sheet"], "searched": r["searched"],
                   "b1_06": "states (" + "; ".join(f"note {s['note']}: {s['class']}" for s in r["states"]) + ")"
                   if r["states"] else "absent", "read": r["read"], "notes_read": r["notes_read"]}
                  for r in inp["sheet_search"]]
    exp_rows = [{k: r[k] for k in ("id", "side", "side_name", "distance_m", "class", "trigger_depth_m", "depth_kind")}
                for r in sup["rows"]]
    side_rows = [{"side": s, "name": d["name"], "status": d["status"], "nearest_m": d["nearest_m"],
                  "on_or_beyond_line_m": lengths[s]["on_or_beyond_m"], "within_depth_only_m": lengths[s]["within_only_m"],
                  "on_or_beyond": " ".join(d["on_or_beyond_line"]), "within": " ".join(d["within"]),
                  "conditional_min_trigger_m": d["conditional_min_trigger_m"], "quantity": None}
                 for s, d in sup["sides"].items()]
    if write:
        def w(name, rows):
            with open(HERE / name, "w", newline="", encoding="utf-8") as f:
                wr = csv.DictWriter(f, fieldnames=list(rows[0]))
                wr.writeheader()
                wr.writerows(rows)
        w("SHEET_SEARCH_T358.csv", sheet_rows)
        w("EXPOSURE_T358.csv", exp_rows)
        w("SIDES_T358.csv", side_rows)
        w("ITEMS_T358.csv", items)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    return {"sheets": sheet_rows, "exposure": exp_rows, "sides": side_rows, "items": items, "summary": summary}


if __name__ == "__main__":
    out = main()
    s = out["summary"]
    print(json.dumps({"dewatering": s["dewatering"]["status"], "clearance": s["dewatering"]["min_clearance_m"],
                      "sides": {r["side"]: (r["status"], r["on_or_beyond_line_m"], r["nearest_m"]) for r in out["sides"]},
                      "beyond": s["beyond_plot_line"]}, indent=1))
