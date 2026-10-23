"""T-217 on the development villa: every neck / column instance x storey classified by SECTION_CONFLICT_V1.

Inputs (values and DXF handles only): ALSENAN_SECTION_INPUT.json (t217_extract.py, read this run from Drive
"Alsenan chalet project" / 'ST7757 dxf.dxf'), the released route G register (research/urban_engine_m4_correctness/
st7757_route_g/PROVISIONAL_REGISTER.csv: 28 neck lines + 61 storey column lines). Outputs: LEDGER_T217.csv, summary.json.
No released quantity is changed; volumes at the released heights are information on the released lines, not a
drawing-derived height (necks: T-205 HELD; storey columns: released FFL-to-FFL convention 4.50 / 4.20 / 4.20 m).

    python3 -I research/agents_t217/t217_alsenan_check.py [--write]
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
import section_conflict as SC  # noqa: E402

BAND = {"FOUNDATION": "FOU", "GF": "GR", "1F": "1ST", "2F": "2ND"}
REGISTER = ROOT / "research/urban_engine_m4_correctness/st7757_route_g/PROVISIONAL_REGISTER.csv"


def released_lines():
    out = {}
    with REGISTER.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["FAMILY"] != "COLUMNS" or r["UNIT"] != "m3" or r["TRADE"] != "CONCRETE" or r["ITEM_ID"] in out:
                continue
            dims = json.loads(r["DIMENSIONS"])
            out[r["ITEM_ID"]] = {"storey": r["STOREY"], "m3": float(r["BASE"]), "section_m": dims.get("section_m"),
                                 "height_m": dims.get("height_m")}
    return out


def sources_for(inst, storey, sched):
    st = inst["storeys"][storey]
    band = sched["bands"].get(BAND[storey])
    src = []
    if band:
        src.append({"kind": "SCHEDULE", "W": band["W"], "D": band["D"], "units": "cm",
                    "ref": f"CGT {sched['handle']} {BAND[storey]}"})
    for t in st["texts"]:
        src.append({"kind": "TEXT", "W": t["W_cm"], "D": t["D_cm"], "units": "cm", "ref": f"{t['sheet']} {t['handle']}"})
    for d in st["dims"]:
        src.append({"kind": "DIM", "W": d["W_mm"], "D": d["D_mm"], "units": "mm",
                    "ref": f"{d['sheet']} {'/'.join(d['handles'])}"})
    for d in st["drawn"]:
        src.append({"kind": "DRAWN", "W": d["W_mm"], "D": d["D_mm"], "units": "mm", "ref": f"{d['sheet']} {d['handle']}"})
    return src, band


def run():
    data = json.loads((HERE / "ALSENAN_SECTION_INPUT.json").read_text(encoding="utf-8"))
    rel = released_lines()
    rows = []
    for inst in data["instances"]:
        sched = data["schedule"][inst["mark"]]
        for storey in ("FOUNDATION", "GF", "1F", "2F"):
            src, band = sources_for(inst, storey, sched)
            drawn = bool(inst["storeys"][storey]["drawn"])
            if storey == "FOUNDATION":
                rid = "P-C:" + inst["id"]
            else:
                rid = f"P-C:{inst.get('engine_col_id')}|{storey}" if inst.get("engine_col_id") else None
            r_line = rel.get(rid) if rid else None
            if not drawn and band is None:
                if r_line:
                    raise SystemExit(f"released line without member: {rid}")
                continue                         # no member on this storey in any source
            if not drawn:
                existence = "SCHEDULE_TYPE_ONLY (not drawn on this storey's plan)"
            elif band is None:
                existence = "DRAWN_NO_SCHEDULE_BAND"
            else:
                existence = "DRAWN"
            rec = SC.classify(inst["fp_outline"], storey, src) if drawn else None
            r_sec = tuple(sorted(r_line["section_m"])) if r_line else None
            h = r_line["height_m"] if r_line and storey != "FOUNDATION" else (
                round(r_line["m3"] / (r_sec[0] * r_sec[1]), 6) if r_line else None)
            lo = hi = None
            if rec is not None and rec.status != "HELD" and h:
                lo, hi = rec.volume_m3(h)
            band_hint = ""
            if rec is not None and rec.status == "CONFLICT":
                hints = []
                for c in rec.candidates:
                    if any(s.startswith("DRAWN") or s.startswith("TEXT") for s in c["sources"]):
                        mb = SC.matching_band(c["section_m"], sched["bands"])
                        if mb:
                            hints.append(f"{c['section_m'][0]:.2f}x{c['section_m'][1]:.2f} = schedule band {'/'.join(mb)}")
                band_hint = "; ".join(hints)
            rows.append({
                "member": inst["fp_outline"], "mark": inst["mark"], "storey": storey, "footing": inst["footing"],
                "pit_raft": inst["pit_raft"], "existence": existence,
                "status": rec.status if rec else "NOT_DRAWN", "basis": rec.basis if rec else "",
                "candidates": " | ".join(f"{c['section_m'][0]:.2f}x{c['section_m'][1]:.2f} [{', '.join(c['sources'])}]"
                                         for c in rec.candidates) if rec else "",
                "candidate_range_m2": f"{rec.range_m2[0]:.4f}..{rec.range_m2[1]:.4f}" if rec and rec.range_m2 else "",
                "per_m_m3": (f"{rec.volume_m3()[0]:.4f}..{rec.volume_m3()[1]:.4f}" if rec and rec.status != "HELD"
                             else ""),
                "drawn_matches_band": band_hint,
                "released_line": rid if r_line else "",
                "released_section_m": f"{r_sec[0]:.2f}x{r_sec[1]:.2f}" if r_sec else "",
                "released_height_m": h, "released_m3": r_line["m3"] if r_line else None,
                "at_released_height_m3": (f"{lo:.4f}..{hi:.4f}" if lo is not None else ""),
                "evidence": "; ".join(rec.evidence) if rec else "",
            })
    return summarise(rows, data, rel)


def summarise(rows, data, rel):
    by = {}
    for r in rows:
        k = (r["storey"], r["status"])
        by[k] = by.get(k, 0) + 1
    conflicts = [r for r in rows if r["status"] == "CONFLICT"]
    impact = {}
    for r in conflicts:
        s = impact.setdefault(r["storey"], {"n": 0, "released_m3": 0.0, "range_at_released_height_m3": [0.0, 0.0],
                                            "range_per_m_m3": [0.0, 0.0], "members": []})
        s["n"] += 1
        lo, hi = (float(x) for x in r["per_m_m3"].split(".."))
        s["range_per_m_m3"] = [round(s["range_per_m_m3"][0] + lo, 6), round(s["range_per_m_m3"][1] + hi, 6)]
        if r["at_released_height_m3"]:
            a, b = (float(x) for x in r["at_released_height_m3"].split(".."))
            s["range_at_released_height_m3"] = [round(s["range_at_released_height_m3"][0] + a, 6),
                                                round(s["range_at_released_height_m3"][1] + b, 6)]
            s["released_m3"] = round(s["released_m3"] + r["released_m3"], 6)
        s["members"].append(f"{r['mark']} {r['member']} ({r['footing']})")
    rel_bound = {r["released_line"] for r in rows if r["released_line"]}
    not_drawn_released = [{"member": r["member"], "mark": r["mark"], "storey": r["storey"], "line": r["released_line"],
                           "m3": r["released_m3"]} for r in rows if r["status"] == "NOT_DRAWN" and r["released_line"]]
    extra = {fr: [{"handle": x["handle"], "section_m": [x["W_mm"] / 1000, x["D_mm"] / 1000],
                   "area_m2": round(x["W_mm"] * x["D_mm"] / 1e6, 6)} for x in v]
             for fr, v in data["outlines_not_over_a_neck"].items()}
    return {
        "method": SC.METHOD, "rule": SC.RULE,
        "instances": len(data["instances"]), "member_storey_rows": len(rows),
        "status_counts": {f"{k[0]} {k[1]}": v for k, v in sorted(by.items())},
        "conflict_impact_by_storey": impact,
        "released_lines_bound": len(rel_bound), "released_lines_total": len(rel),
        "released_lines_on_members_not_drawn_on_that_storey": {
            "status": "UNKNOWN (existence; the slab plan of that storey draws neither outline nor hatch there)",
            "lines": not_drawn_released,
            "m3": round(sum(x["m3"] for x in not_drawn_released), 6)},
        "outlines_not_over_a_neck": {
            "status": "UNKNOWN (drawn S-COL.BON outlines with no mark and no released line; element continuity T-188)",
            "by_slab_plan": extra,
            "area_m2_by_slab_plan": {fr: round(sum(x["area_m2"] for x in v), 6) for fr, v in extra.items()}},
        "rows": rows,
    }


def ledger_csv(summary):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(summary["rows"][0]), lineterminator="\n")
    w.writeheader()
    for r in summary["rows"]:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


if __name__ == "__main__":
    s = run()
    if "--write" in sys.argv:
        (HERE / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (HERE / "LEDGER_T217.csv").write_text(ledger_csv(s), encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1, ensure_ascii=False))
