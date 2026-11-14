"""T-781 Alsenan run of OPENING_TABLE_V1 (read-only; outputs to --out outside the repository, plus a compact,
client-free summary to research/agents_t781/out/ with --write-summary).

Inputs:
  --geo   the geometry_t781.py output dir (ARCH_OPENINGS.json, OPENING_SCHEDULE.json, ARCH_ROOMS.json of the DXF)
  elevation reads: the committed drawing readings of earlier tasks, used ONLY as heights read from the drawings
          (floor + plan width + sill / head above FFL); census ids are never used to bind:
          research/agents_t201/HEADS_T201.csv  (vector elevation / section outlines, DRAWING-CONFIRMED rows and the
                                                outline-only heights)
          research/agents_t198/OPENINGS_T198.csv (rows whose height is PRINTED on a sheet)
          research/agents_t207/READINGS_T207.csv (louvred-leaf outline heights: shutter hint)
Checks (never inputs): research/agents_t768/out/FIX_ROWS.json totals, research/agents_t238/CENSUS_T238.csv ids.

    bash scripts/agent_env.sh run --tree task-T-781 research/agents_t781/alsenan_t781.py --geo <dir> --out <dir>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import opening_table_v1 as OT  # noqa: E402

KIND = {"WINDOW": "WINDOW", "DOOR": "DOOR", "OPENING": "PASSAGE"}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def elevation_reads():
    reads = []
    for r in csv.DictReader(open(ROOT / "research/agents_t201/HEADS_T201.csv", encoding="utf-8")):
        s, h, ht = _f(r["SILL_ABOVE_FFL_M"]), _f(r["HEAD_ABOVE_FFL_M"]), _f(r["HEIGHT_M"])
        if h is None and ht is None:
            continue
        reads.append({"floor": r["FLOOR"], "width_m": _f(r["WIDTH_M"]), "sill_m": s, "head_m": h,
                      "height_m": None if h is not None else ht, "kind": KIND.get(r["KIND"]),
                      "source": f"T-201 {r['VIEW']} outline"})
    for r in csv.DictReader(open(ROOT / "research/agents_t198/OPENINGS_T198.csv", encoding="utf-8")):
        if r["HEIGHT_STATUS"] != "PRINTED":
            continue
        s, ht = _f(r["SILL_M"]), _f(r["HEIGHT_M"])
        reads.append({"floor": r["FLOOR"], "width_m": _f(r["WIDTH_M"]), "sill_m": s,
                      "head_m": round(s + ht, 4) if s is not None and ht is not None else None,
                      "kind": KIND.get(r["KIND"]), "source": "T-198 printed height"})
    # T-207: louvred leaves drawn beside the jambs; outline 849 .. 3050 mm above the view's ground line (no FFL datum)
    rd = {(x["item"], x["quantity"]): x["value"] for x in csv.DictReader(open(
        ROOT / "research/agents_t207/READINGS_T207.csv", encoding="utf-8"))}
    for item in ("W11", "W12"):
        b, t = _f(rd.get((item, "outline_bottom_y"))), _f(rd.get((item, "outline_top_y")))
        w = _f(rd.get((item, "plan_width_printed")))
        if b is not None and t is not None and w is not None:
            reads.append({"floor": "GF", "width_m": w, "sill_m": None, "head_m": None,
                          "height_m": round((t - b) / 1000.0, 3), "kind": "WINDOW", "type_hint": "SHUTTER",
                          "source": "T-207 fence elevation louvred leaves"})
    # arched heads (owner Q-32 A / Q-76 A: window area = W x the window's own arch crown): the crown read from the
    # arch outline replaces a rectangular head read for the same floor + width (the T-198 rows read the band crown
    # 3.10 over W15 / W16 and the decorative band top 3.50 over W17 as heads: T-238 / Q-76)
    arched = []
    t238 = json.loads((ROOT / "research/agents_t238/summary.json").read_text(encoding="utf-8"))["outlines"]
    for k in ("W15", "W16"):
        o = t238.get(k) or {}
        if o.get("status") == "DRAWING-CONFIRMED" and o.get("crown_m") is not None:
            arched.append({"floor": "1F", "width_m": o["width_m"], "sill_m": 0.0, "head_m": o["crown_m"],
                           "kind": "WINDOW", "arched": True, "source": "T-238 arch outline crown (Q-32 A)"})
    arched.append({"floor": "1F", "width_m": 3.29, "sill_m": 0.0, "head_m": 3.00, "kind": "WINDOW", "arched": True,
                   "source": "owner Q-76 A: height to the window's own arch 3.00"})
    def _same(e, a):
        return e["floor"] == a["floor"] and abs(e["width_m"] - a["width_m"]) <= 0.02 and e["kind"] == a["kind"] \
            and e.get("head_m") is not None and e["head_m"] > a["head_m"] and (e.get("sill_m") or 0) == 0
    out = list(arched)
    for e in reads:
        if any(_same(e, a) for a in arched):
            continue  # a rectangular read of an arched window: superseded by its crown
        out.append(e)
    return out


def t768_check():
    d = json.loads((ROOT / "research/agents_t768/out/FIX_ROWS.json").read_text(encoding="utf-8"))
    fr = d.get("freelancer") or {}
    return {"window_m2_candidate_incl_W17": fr.get("windows m2 candidate after (incl. W17 9.87 MAIN_FILL_4)"),
            "freelancer_window_m2": fr.get("windows m2 (T-198 W x H, 29 rows)")}


def door_split(rows):
    """external doors, ours vs the freelancer's aluminium workbook: his cover total '12' is the doors m2 cell, not a
    count; his quantity rows are pcs x W x H. Numbers only (no text of his workbook is copied)."""
    d = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    alu = {(r["sheet"], r["row"]): r["cells"] for r in d["rows"] if r["file"] == "ALU"}
    cover = [c for (sh, n), c in alu.items() if f"B{n}" in c and f"E{n}" in c and (c[f"E{n}"].get("f") or "") == f"=B{n}"]
    door_rows = []
    for (sh, n), c in sorted(alu.items(), key=lambda x: x[0][1]):
        a_txt = str((c.get(f"A{n}") or {}).get("v") or "")
        if "\u0628\u0627\u0628" in a_txt and f"H{n}" in c:  # the word for door
            door_rows.append({"row": n, "pcs": c[f"B{n}"]["v"], "W": c[f"C{n}"]["v"], "H": c[f"D{n}"]["v"],
                              "m2": c[f"H{n}"]["v"]})
    his_pcs = sum(r["pcs"] for r in door_rows)
    his_m2 = round(sum(r["m2"] for r in door_rows), 3)
    ours = [r for r in rows if r["side"] == "EXTERNAL" and r["type"] in ("DOOR", "GLASS_DOOR")]
    main_door = [r for r in ours if r["W"] is not None and r["W"] >= 1.80]
    alu_doors = [r for r in ours if r not in main_door]
    ours_m2 = round(sum(r["area_m2"] for r in alu_doors), 3)
    w_sum = round(sum(r["W"] for r in alu_doors), 3)
    his_h = door_rows[0]["H"] if door_rows else None
    return {
        "freelancer_cover_cells_equal_to_his_door_m2": sorted({v["v"] for c in cover for k, v in c.items()
                                                               if k.startswith("B") and v.get("v") == his_m2}),
        "freelancer_door_rows": door_rows, "freelancer_pcs": his_pcs, "freelancer_m2": his_m2,
        "ours_external_pcs": len(ours), "ours_main_entrance_pcs": len(main_door),
        "ours_aluminium_external_pcs": len(alu_doors), "ours_aluminium_external_m2": ours_m2,
        "causes": {
            "UNIT_MISREAD (the owner-table '12 pcs' is his doors m2 cell 12.0 = sum of pcs x W x H)": "12 m2 -> "
            f"{his_pcs} pcs",
            "MAIN_ENTRANCE (double leaf >= 1.80, not in his aluminium workbook)": len(main_door),
            "pcs residual after the two causes": len(alu_doors) - his_pcs,
            "HEIGHT 2.20 (Q-55 C owner fallback) vs his 2.40, RULE_DIFFERENCE, m2":
                round(w_sum * (2.20 - his_h), 3) if his_h else None,
            "WIDTH: plan bands vs his 1.00 each, ENGINE_RIGHT (plan band widths), m2":
                round((w_sum - sum(r["pcs"] * r["W"] for r in door_rows)) * his_h, 3) if his_h else None,
            "m2 residual": round(ours_m2 - his_m2 - (w_sum * (2.20 - his_h)) -
                                 (w_sum - sum(r["pcs"] * r["W"] for r in door_rows)) * his_h, 4) if his_h else None,
            "shutters / glass doors in his door count": 0,
        }}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write-summary", action="store_true")
    a = ap.parse_args(argv)
    g = Path(a.geo)
    ops = json.loads((g / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))["openings"]
    sched = json.loads((g / "OPENING_SCHEDULE.json").read_text(encoding="utf-8"))["openings"]
    rooms = {r["room_id"]: {"kind": r.get("kind")} for r in
             json.loads((g / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]}
    reads = elevation_reads()
    rows = OT.build(ops, schedule=sched, elevation_reads=reads, rooms=rooms)
    summ = OT.summary(rows)
    win = [r for r in rows if r["type"] in ("WINDOW", "SHUTTER")]
    chk = t768_check()
    win_m2 = round(sum(r["area_m2"] or 0 for r in win), 3)
    summ["alsenan"] = {
        "plan_openings": len(ops), "elevation_reads": len(reads),
        "window_and_shutter_m2": win_m2, "window_and_shutter_pcs": len(win),
        "t768_window_m2_check": chk["window_m2_candidate_incl_W17"],
        "diff_vs_t768_pct": (round(100 * (win_m2 - chk["window_m2_candidate_incl_W17"]) /
                                   chk["window_m2_candidate_incl_W17"], 2)
                             if chk["window_m2_candidate_incl_W17"] else None),
        "freelancer_window_m2": chk["freelancer_window_m2"],
        "external_doors": [{"id": r["id"], "type": r["type"], "W": r["W"], "H": r["H"], "label": r["area_label"]}
                           for r in rows if r["side"] == "EXTERNAL" and r["type"] in ("DOOR", "GLASS_DOOR")],
        "labels_W": dict(Counter(r["W_label"] for r in rows)), "labels_H": dict(Counter(r["H_label"] for r in rows)),
        "findings": dict(Counter(f["code"] for r in rows for f in r["findings"])),
    }
    summ["alsenan"]["external_doors_vs_freelancer"] = door_split(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "OPENING_TABLE.json").write_text(json.dumps({"policy": OT.POLICY_ID, "rows": rows}, indent=1),
                                           encoding="utf-8")
    keys = ("id", "floor", "type", "side", "W", "W_label", "H", "H_label", "sill", "sill_label", "head", "head_label",
            "wall_t", "area_m2", "area_label", "lintel_m", "lintel_label", "glazing")
    with open(out / "OPENING_TABLE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(summ, indent=1))
    for r in rows:
        print(r["id"], r["type"], r["side"], r["W"], r["W_label"], r["sill"], r["sill_label"], r["head"],
              r["head_label"], r["area_m2"], r.get("read_binding", ""), [f["code"] for f in r["findings"]])
    if a.write_summary:
        (HERE / "out").mkdir(exist_ok=True)
        table = [{k: r.get(k) for k in keys} for r in rows]  # engine ids, types, sizes, labels only
        (HERE / "out/OPENING_TABLE_ALSENAN.json").write_text(json.dumps({"summary": summ, "rows": table}, indent=1),
                                                            encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
