"""T-481 on the development villa (Alsenan): FIN.SKIRTING remainder after V3.0.44 (research ledger, no candidate change).

Readings were taken in this run from the Drive copies (folder "Alsenan chalet project": P7757_DXF_COMPRESSED.zip ->
P7757.dxf; the architectural DWF; Alsenan_Architectural_P7757_Pages_11-12 p.11) decoded into .work/private only. Only
derived numbers, entity handles and view names are kept here: no coordinate, image, note text or client data.

  python3 -I research/agents_t481/t481_alsenan.py           # writes the CSV / JSON outputs beside this file
  python3 -I research/agents_t481/t481_alsenan.py --check   # recomputes and compares byte for byte
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t481_skirting_rules as R  # noqa: E402

# ---------------------------------------------------------------- readings (levels in m, lengths in m, own reads)
# DWF SECTION B-B (vector, 1 unit = 1 mm): level-marker apexes ±0.00 (street side) and +0.30 (dewaneya floor) are
# 300.6 mm apart (printed 0.30); the street wall is cut 201 mm thick with a window drawn in the cut: frame base
# 999.1 mm and head 3200.5 mm above the ±0.00 apex (height 2.2014), masonry below the base down to the floor.
# The same section's sea end: +1.00 floor line (printed '100' from ±0.00) and the W02 frame base on that line
# (999.1 mm above the ±0.00 apex there), head 3200.5.
READINGS = [
    # (opening, view, quantity, value, unit, source, note)
    ("W11", "DWF SECTION B-B", "frame_base_level", 0.999, "m", "apex ±0.00 to frame base 999.1 mm",
     "street-wall cut; plan cut line 0.078 m outside W11's jamb (in the 0.81 pier); drawn opening 2.201 = W11"),
    ("W11", "DWF SECTION B-B", "ffl_level", 0.30, "m", "printed '+0.30' marker, same view (apex 300.6 mm)",
     "dewaneya floor; GF plan prints +0.30 in the room"),
    ("W11", "DWF FENCE ELEVATION", "base_above_view_ground", 0.849, "m", "T-207 READINGS (merged), own re-read",
     "no level printed in the view: ground line ±0.00 or +0.15 (plot) -> base +0.849 or +0.999"),
    ("W11", "current issue Pages_11-12 p.11 (scan)", "base_above_ffl_check", 0.72, "m",
     "400 dpi profile: floor line to sill edge over the printed 400 (floor to +4.30)", "check only, +-0.03"),
    ("W12", "DWF FENCE ELEVATION", "same_outline_as", "W11", "-", "T-207: top / bottom lines shared to 1 mm",
     "W12 binds to W11's reading"),
    ("W02", "DWF SECTION B-B", "frame_base_level", 1.000, "m", "frame base on the +1.00 floor line (999.1 mm above "
     "the ±0.00 apex)", "cut inside the 6.232 m glazing span; four glazing lines continuous on the plan"),
    ("W02", "DWF SECTION B-B", "ffl_level", 1.00, "m", "printed '100' dimension ±0.00 -> floor and '+1.00' marker",
     "saloon floor; GF plan prints +1.00"),
    ("W02", "current issue Pages_11-12 p.11 (scan)", "base_at_floor_check", 0.00, "m",
     "glazing starts on the floor line at the end of the printed '100'", "AGREES; T-201 overlay 0.025 m"),
    ("W17", "P7757.dxf NORTH WEST ELEVATION", "jamb_base_level", 5.50, "m",
     "jamb lines 2A46 .. start on the +5.50 marker block (handle-level read); printed chain 700/4300/200/3050.5 from "
     "the +1.00 marker: 1.00 + 4.30 + 0.20 = 5.50", "frame W 2A47 .. 2A50 base 0.050 above: a frame member"),
    ("W17", "P7757.dxf FIRST FLOOR plan", "ffl_level", 5.50, "m", "the only 1F level printed (5 texts '+5.50')",
     "1F-11 master bedroom"),
]

SILLS = {
    "W11": [("DWF SECTION B-B", R.sill_above_ffl(0.999, 0.30, "SECTION B-B printed markers")),
            ("DWF FENCE ELEVATION, ground ±0.00", R.sill_above_ffl(0.849, 0.30, "FENCE ground read as ±0.00 (reading 1 of 2)")),
            ("DWF FENCE ELEVATION, ground +0.15", R.sill_above_ffl(0.999, 0.30, "FENCE ground read as +0.15 (reading 2 of 2)"))],
    "W02": [("DWF SECTION B-B", R.sill_above_ffl(1.000, 1.00, "SECTION B-B printed markers"))],
    "W17": [("P7757.dxf NW ELEVATION", R.sill_above_ffl(5.50, 5.50, "NW elevation markers + printed chain"))],
}
SILLS["W12"] = SILLS["W11"]

# V3.0.44 lines (bound by T-422 to V3.0.43 = the T-296 ledger values; LINE_LEDGER_T296.csv)
LINES = {
    "W11+W12": {"line": "L-d32414916cfbd04c27be", "room": "GF-01 dewaneya", "range": "L-836720153cd9a3578f63",
                "net": 14.218037, "range_hi": 3.909839, "edges": {"W11": 1.954920, "W12": 1.954919},
                "gross": 20.127876, "doors": 2.000000},
    "W02": {"line": "L-71e2e002a3af624097f0", "room": "GF open plan (GF-07 / GF-08)", "range": "L-e7dcdc69e1a2b24f8616",
            "net": None, "range_hi": 6.331578, "edges": {"W02": 6.331578}},
    "W17": {"line": "L-309f118f6fce78b6c28e", "room": "1F-11", "range": "L-fbba0e0db25f6b481eaa",
            "net": 17.161172, "range_hi": 3.289498, "edges": {"W17": 3.289498}},
}

# 1F dressing (engine room 1F-RFFE7AF, line L-4a85470b BLOCKED_RFI): P7757.dxf layer 1 by handle
DRESSING = [
    {"id": "W", "length": 1.800, "stretches": [{"kind": "WALL", "length": 0.8908, "ref": "B03"},
                                               {"kind": "DOOR", "length": 0.8000, "ref": "door D315 BEE"},
                                               {"kind": "WALL", "length": 0.1092, "ref": "B04"}]},
    {"id": "E", "length": 1.800, "stretches": [{"kind": "WALL", "length": 1.800, "ref": "B00"}]},
    {"id": "N", "length": 1.650, "stretches": [{"kind": "WALL", "length": 1.650, "ref": "B20"}]},
    {"id": "S", "length": 1.650, "stretches": [{"kind": "WALL", "length": 0.500, "ref": "AD4"},
                                               {"kind": "PASSAGE", "length": 1.000, "ref": "arch A-1F-01 arch120 BEC"},
                                               {"kind": "WALL", "length": 0.150, "ref": "AD5"}]},
]
DRESSING_JOINERY = [{"length": 1.800, "ref": "box B0A / BE3 (layer 5) on E"},
                    {"length": 0.500, "ref": "box end on N"}, {"length": 0.500, "ref": "box end on S (AD4)"}]
DRESSING_DWF_CHECK = 5.1006  # earlier issue DWF, same walk: 0.891 + 0.110 + 1.799 + 1.651 + 0.4996 + 0.150

# ST-01 shaft faces on the 1F plan (face-local s in m from the north inner corner, handles of P7757.dxf).
# Stations: T-410 SIDE_TABLE (merged) bound to the nosing lines (layer 5) of the 1F plan: MS2-L first nosing AC0 at
# s 4.500 on the west face (rises north), MS1-U top nosing ABE at s 4.150 on the east face (rises south).
SHAFT = [
    {"id": "east B16 (1F-W03)", "length": 5.200, "walls": [(0.0, 5.200, "B16 (+ 2FF3 flush 4.700 .. 5.200)")],
     "windows": [], "floor_zone": [(4.150, 5.200)],
     "flights": [(0.0, 1.200, "MS2-LD.E", (7.516, 7.516)), (0.850, 4.150, "MS1-U.E1..E3", (3.50, 5.50))]},
    {"id": "west AF0 / C5C / AF1 (1F-W04)", "length": 4.625,
     "walls": [(0.0, 1.050, "AF0 (2FE1 flush)"), (2.250, 4.625, "AF1 (3005 proud 3.000 .. 3.500)")],
     "windows": [(1.050, 2.250, "W13 C5A-C5C")], "floor_zone": [(4.500, 4.625)],
     "flights": [(0.0, 1.200, "MS2-LD.W", (7.516, 7.516)), (1.200, 2.250, "MS2-L.W2", (5.50, 7.516)),
                 (2.250, 3.000, "MS2-L.W1B", (5.50, 7.516)), (3.000, 3.500, "MS2-L.W1C", (5.50, 7.516)),
                 (3.500, 4.500, "MS2-L.W1", (5.50, 7.516))]},
    {"id": "north ADE / W25 / ADD (1F-W10)", "length": 2.500,
     "walls": [(0.0, 1.400, "ADE"), (2.400, 2.500, "ADD")], "windows": [(1.400, 2.400, "W25 CE2 + CE8 / CDF")],
     "floor_zone": [], "flights": [(0.0, 2.500, "MS2-LD.N", (7.516, 7.516))]},
]
SHAFT_RETURNS = [(0.100, "STAIR", "MS2-L.W1C column 3005 returns 2 x 0.050 (T-410 r2)")]
T296_SHAFT_HELD = 10.232  # T-250 walk of the engine room part ST-1F (T-296 ledger), inside L-ba3599ec's net
L_LIVING = {"line": "L-ba3599ec2dc82c221617", "range": "L-079bc7669b2c68d5d11b", "net": 41.435360,
            "range_hi": 2.200000, "windows": {"W13": 1.2, "W25": 1.0}}

V3044 = {"certain": 189.818752, "held_high": 15.730915, "freelancer": 282.85}


def build():
    win_rows, line_rows = [], []
    dec = {}
    for w in ("W11", "W12", "W02", "W17"):
        d = R.decide(SILLS[w])
        dec[w] = d
        win_rows.append({"opening": w, "views": " | ".join(f"{v}: {s:.3f}" for v, s in SILLS[w]),
                         "decision": d["decision"], "spread_m": d["spread_m"],
                         "status": {"W11": "DRAWING-CONFIRMED (section B-B geometry on printed markers; fence elevation "
                                           "agrees on the decision under both ground readings; scan check 0.72)",
                                    "W12": "DRAWING-CONFIRMED (bound to W11: identical outline, fence elevation)",
                                    "W02": "DRAWING-CONFIRMED (section B-B; current issue agrees) - count / pier D-53 "
                                           "contingent",
                                    "W17": "DRAWING-CONFIRMED (printed chain from the +1.00 marker; jambs on +5.50)"}[w]})
    certain_delta, held_delta = 0.0, 0.0
    for key, ln in LINES.items():
        ws = list(ln["edges"])
        decisions = {dec[w]["decision"] for w in ws}
        assert len(decisions) == 1, key
        d = decisions.pop()
        edge = round(sum(ln["edges"].values()), 6)
        kw = {"gross": ln["gross"], "listed_doors": ln["doors"]} if d == R.SKIRTED else {}
        eff = R.line_effect(d, ln["net"], ln["range_hi"], min(edge, ln["range_hi"]), **kw)
        if d == R.SKIRTED:
            certain_delta += eff["net"] - ln["net"]
        held_delta += ln["range_hi"] - eff["range_hi"]
        line_rows.append({"line": ln["line"], "room": ln["room"], "openings": "+".join(ws), "decision": d,
                          "net_before": ln["net"], "net_after": eff["net"], "range_line": ln["range"],
                          "range_before": f"0 .. {ln['range_hi']:.6f}",
                          "range_after": "NOT_APPLICABLE_WITH_EVIDENCE" if eff["range_hi"] < 1e-6
                          else f"0 .. {eff['range_hi']:.6f}"})
    walk = R.walk_cell(DRESSING, DRESSING_JOINERY)
    assert abs(walk["skirting_lm"] - DRESSING_DWF_CHECK) < 0.002
    line_rows.append({"line": "L-4a85470b (new in V3.0.44)", "room": "1F dressing 1F-RFFE7AF", "openings": "-",
                      "decision": "WALKED", "net_before": None, "net_after": walk["skirting_lm"], "range_line": "-",
                      "range_before": "BLOCKED_RFI blank", "range_after": "SOURCE_DERIVED (DRAWING-CONFIRMED)"})
    certain_delta += walk["skirting_lm"]
    shaft_rows, room_lm, stair_lm, unk = [], 0.0, 0.0, 0.0
    for f in SHAFT:
        r = R.shaft_owners(f, 5.50)
        room_lm += r["lm"]["ROOM"]
        stair_lm += r["lm"]["STAIR"]
        unk += r["lm"]["UNKNOWN"]
        for s0, s1, o, ref, by in r["pieces"]:
            shaft_rows.append({"face": f["id"], "s0": f"{s0:.3f}", "s1": f"{s1:.3f}", "lm": f"{s1 - s0:.3f}",
                               "owner": o, "ref": ref, "by": by})
    for lm, o, why in SHAFT_RETURNS:
        stair_lm += lm
        shaft_rows.append({"face": "west", "s0": "", "s1": "", "lm": f"{lm:.3f}", "owner": o, "ref": why, "by": why})
    room_lm, stair_lm = round(room_lm, 6), round(stair_lm, 6)
    held_delta += L_LIVING["range_hi"]   # W13 / W25 leave the room range: they lie in B7 stretches (MS2-L.W2, MS2-LD.N)
    line_rows.append({"line": L_LIVING["line"], "room": "1F living + ST-1F", "openings": "W13+W25",
                      "decision": "STAIR-OWNED (R-T481-3)", "net_before": L_LIVING["net"],
                      "net_after": f"{L_LIVING['net']:.6f} (binding of the {stair_lm:.3f} lm B7 faces to the engine "
                                   f"edges at integration; T-250 walk {T296_SHAFT_HELD})",
                      "range_line": L_LIVING["range"], "range_before": "0 .. 2.200000",
                      "range_after": "NOT_APPLICABLE_WITH_EVIDENCE (owners MS2-L.W2 / MS2-LD.N, HELD in B7)"})
    cert = round(V3044["certain"] + certain_delta, 6)
    held = round(max(V3044["held_high"] - held_delta, 0.0), 6)
    summ = {
        "task": "T-481", "basis": "ARCH_TAKEOFF_V3.0.44 FIN.SKIRTING (json 8b2fe2b6), research ledger, no candidate change",
        "windows": {w: dec[w] for w in dec},
        "dressing": {k: walk[k] for k in ("skirting_lm", "gross_lm", "deductions", "joinery_backed_lm")},
        "shaft": {"room_floor_level_lm": room_lm, "stair_owned_lm": stair_lm, "unknown_lm": round(unk, 6),
                  "t250_walk_in_line_lm": T296_SHAFT_HELD,
                  "walk_closure_residual_lm": round(T296_SHAFT_HELD - stair_lm - room_lm, 6),
                  "living_net_after_binding": round(L_LIVING["net"] - stair_lm, 6)},
        "totals": {"certain_before": V3044["certain"], "certain_after": cert,
                   "certain_delta": round(certain_delta, 6), "held_high_before": V3044["held_high"],
                   "held_high_after": held, "freelancer": V3044["freelancer"],
                   "gap_after_lm": round(cert - V3044["freelancer"], 6),
                   "gap_after_pct": round(100 * (cert - V3044["freelancer"]) / V3044["freelancer"], 2),
                   "certain_includes_stair_owned_up_to_lm": stair_lm,
                   "certain_after_shaft_binding": round(cert - stair_lm, 6),
                   "gap_after_binding_pct": round(100 * (cert - stair_lm - V3044["freelancer"]) / V3044["freelancer"], 2)},
    }
    return win_rows, line_rows, shaft_rows, summ


def _csv(rows):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue()


def outputs():
    win, lines, shaft, summ = build()
    rd = [dict(zip(("opening", "view", "quantity", "value", "unit", "source", "note"), r)) for r in READINGS]
    return {"READINGS_T481.csv": _csv(rd), "WINDOWS_T481.csv": _csv(win), "LINES_T481.csv": _csv(lines),
            "SHAFT_FACES_T481.csv": _csv(shaft),
            "summary.json": json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=True) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = outputs()
    if "--check" in argv:
        bad = [n for n, t in out.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps(json.loads(out["summary.json"])["totals"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
