"""T-205 on the development villa (values, Drive titles, layers and DXF handles only; no drawing content).

Inputs: ALSENAN_NECK_INPUT.json (36 necks read from 'ST7757 dxf.dxf' this run), the committed freelancer rows
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, file RC, sheet 'walls + columns', rows 16-28) and the released
V2.9 route G neck lines (M4 PROVISIONAL_REGISTER, 28 lines, 10.8555 m3). Outputs: LEDGER_T205.csv, summary.json.
Run: python3 -I research/agents_t205/t205_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import neck_ends_v1 as N  # noqa: E402

# Project chain (T-200 / T-206, merged and Checker-verified source references; values only)
PROJECT = {
    "units": "m",
    "datums": {"FFL": {"value": 1.00, "status": "DRAWING-CONFIRMED", "source": "P7757 / ST7757 SH08 level marks"},
               "SLAB_TOP": None, "FORMATION": None},
    "layers": {"FLOOR_BUILD_UP": None},
    "formation_limit": {"bound": "AT_MOST", "value": -1.50,
                        "source": "ST7757.pdf p.9 boxed note 1: excavation not less than 1.5 m below the plot level"},
    "gb_top_relation": "SLAB_TOP",       # ST7757.pdf p.13 'Ground Beams for exterior walls': top = Ground Floor slab level
    "gb_basis": "NET_OF_COLUMN",         # route G ground-beam lines: 'column footprint split out' (generic_route.py:862)
}
RELEASED_TOP_M, RELEASED_UNDERSIDE_M = 1.00, -1.50   # profile NECK_TOP_LEVEL_M / FOUNDING_DEPTH_M (route G, V2.9)
GF_COLUMN_BOTTOM = ("FFL", 1.00)                     # released GF columns run FFL +1.00 -> +5.50 (profile rationale)
FREELANCER_FILE = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"


def load():
    return json.loads((HERE / "ALSENAN_NECK_INPUT.json").read_text(encoding="utf-8"))


def freelancer_rows():
    d = json.loads(FREELANCER_FILE.read_text(encoding="utf-8"))
    out = {}
    for r in d["rows"]:
        if r["file"] == "RC" and r["sheet"] == "الحوائط + الأعمدة" and 16 <= r["row"] <= 28:
            c = {k[0]: v["v"] for k, v in r["cells"].items()}
            out[c["A"]] = {"n": c["F"], "W": c["B"], "D": c["C"], "h": c["D"], "row": r["row"],
                           "m3": round(c["I"], 6)}
    return out


def run():
    data = load()
    fl = freelancer_rows()
    rows, released, census = [], [], {}
    for s in data["necks"]:
        r = N.neck(s, PROJECT)
        sch = s["sections"][0]
        a_sched = sch["W"] / 100 * sch["D"] / 100
        H = s["footing"].get("H")
        rel = s["released"]["m3"]
        rel_h = round(RELEASED_TOP_M - RELEASED_UNDERSIDE_M - H, 6) if (rel is not None and H is not None) else None
        if rel is not None:
            released.append({"type": s["type"], "area_m2": round(a_sched, 6), "length_m": rel_h})
        c = census.setdefault(s["type"], {"area_m2": round(a_sched, 6), "drawn": 0, "held": 0})
        c["drawn"] += 1
        c["held"] += rel is None
        wi = r["what_if"]
        rows.append({
            "neck_id": s["id"], "type": s["type"], "label_handle": s["label_handle"],
            "outline_handle": s["outline_handle"],
            "section_status": r["section"]["status"],
            "section_m2": r["section"]["area_m2"],
            "section_range_m2": r["section"]["range_m2"],
            "section_note": "; ".join(f"{n['source']} {n['W']}x{n['D']}" for n in r["section"]["notes"]) or "",
            "footing": s["footing"].get("type"), "footing_H_m": H,
            "top_datum": r["top"]["kind"], "top_m": r["top"]["value_m"],
            "footing_top_m": r["bottom"]["value_m"],
            "printed_stack_m": r["bottom"].get("stack_m"),
            "drawing_status": r["status"], "held_codes": "|".join(r["codes"]),
            "drawing_length_formula": (f"{wi['length_at_b0_d0_m']:.3f} - b + d" if wi else ""),
            "what_if_b0_d0_m3": (wi["const_m3"][0] if wi and wi["const_m3"][0] == wi["const_m3"][1]
                                 else (list(wi["const_m3"]) if wi else None)),
            "released_length_m": rel_h, "released_m3": rel,
            "freelancer_row": fl.get(s["type"], {}).get("row"),
            "freelancer_section_m2": (round(fl[s["type"]]["W"] * fl[s["type"]]["D"], 6) if s["type"] in fl else None),
            "freelancer_length_m": fl.get(s["type"], {}).get("h"),
        })
    rec = N.reconcile(fl, census, released)
    sum_A = round(sum(x["area_m2"] for x in released), 6)
    groups = {}
    for x in rows:
        if x["released_m3"] is None:
            g = "engine_held_footing_conflict" if "FOOTING_CONFLICT" in x["held_codes"] else "engine_held_neck_only_CN"
        elif "PIT_DEPTH_NOT_PRINTED" in x["held_codes"]:
            g = "lift_pit_raft"
        elif "SECTION_CONFLICT" in x["held_codes"]:
            g = "section_conflict"
        else:
            g = "printed_section"
        G = groups.setdefault(g, {"n": 0, "released_m3": 0.0, "sum_section_m2": 0.0, "what_if_b0_d0_m3": [0.0, 0.0]})
        G["n"] += 1
        G["released_m3"] = round(G["released_m3"] + (x["released_m3"] or 0.0), 6)
        G["sum_section_m2"] = round(G["sum_section_m2"] + (x["section_m2"] or 0.0), 6)
        w = x["what_if_b0_d0_m3"]
        if w is None:
            G["what_if_b0_d0_m3"] = None
        elif G["what_if_b0_d0_m3"] is not None:
            lo, hi = (w, w) if isinstance(w, float) else w
            G["what_if_b0_d0_m3"] = [round(G["what_if_b0_d0_m3"][0] + lo, 6), round(G["what_if_b0_d0_m3"][1] + hi, 6)]
    ref = groups
    stack = N.stack_check("GB_TOP", None, GF_COLUMN_BOTTOM[0], GF_COLUMN_BOTTOM[1], None)
    held = {}
    for x in rows:
        for c in x["held_codes"].split("|"):
            if c:
                held[c] = held.get(c, 0) + 1
    rel_set = [x for x in rows if x["released_m3"] is not None]
    summary = {
        "method": N.METHOD, "necks_drawn": len(rows), "released_lines": len(rel_set),
        "released_m3": round(sum(x["released_m3"] for x in rel_set), 6),
        "released_sum_section_m2": sum_A,
        "released_basis": "h = FFL +1.00 - (-1.50) - H: top at a FINISHED level (FINISHED_AS_STRUCTURAL), footing "
                          "underside at -1.50, i.e. a formation at -1.67 with the printed 0.17 underlay + blinding",
        "freelancer_m3": rec["freelancer_m3"],
        "reconciliation": rec,
        "drawing_derived": {
            "status": "HELD (every neck): neck top = GB top = ground-floor STRUCTURAL slab top, not printed; footing "
                      "end = formation + 0.17 + H, formation not printed (Q-21 C; limit AT_MOST -1.50 OPEN)",
            "length_formula_m": "h = 2.33 - H - b + d  (b = FFL -> slab-top build-up >= 0, d = formation depth below "
                                "the printed -1.50 limit >= 0; both unprinted)",
            "groups (what_if at b = d = 0, not a quantity)": ref,
            "per_0.10_m_build_up_m3": round(-0.1 * sum_A, 6),
            "per_0.10_m_deeper_formation_m3": round(0.1 * sum_A, 6),
            "released_equivalent": "the released 10.8555 m3 equals d - b = 0.17 m on every neck",
            "held_codes": held,
        },
        "stack_check_neck_vs_gf_column": stack,
        "rows": rows,
    }
    return summary


def ledger_csv(summary):
    buf = io.StringIO()
    keys = list(summary["rows"][0])
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in summary["rows"]:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


if __name__ == "__main__":
    s = run()
    if "--write" in sys.argv:
        (HERE / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (HERE / "LEDGER_T205.csv").write_text(ledger_csv(s), encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1, ensure_ascii=False))
