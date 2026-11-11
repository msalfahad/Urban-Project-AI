"""T-707 on the development villa (Alsenan; one application of R-T707-1 / -2, not an accuracy claim).

    python3 -I research/agents_t707/t707_alsenan.py --write | --check

Inputs (committed files only): the own ST read `out/T707_OWN_READ.json` (values, no coordinate), the T-689 B8 joint
bound (`research/agents_t689/out/T689_HELD_RANGES.json`, merged 66ffd421, Gate A PASS) and the candidate of record
V3.0.70 (`research/agents_t693/out/LINE_INDEX_V3_0_70.json`). Writes `out/T707_COLUMN_TAIL.json` / `.md`.
Research only, unwired: no candidate line, engine module, rule / knowledge version file or released default changes.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t707_rules as R  # noqa: E402

OWN = HERE / "out" / "T707_OWN_READ.json"
T689 = ROOT / "research" / "agents_t689" / "out" / "T689_HELD_RANGES.json"
INDEX = ROOT / "research" / "agents_t693" / "out" / "LINE_INDEX_V3_0_70.json"
OUT_J, OUT_M = HERE / "out" / "T707_COLUMN_TAIL.json", HERE / "out" / "T707_COLUMN_TAIL.md"

BASE_2F = X("9.65")          # 2F column base, APPROVED datum (T-669 / R-T658-4)
FINISHED_2F = X("13.90")     # finished roof mark, arch section A-A (D-39 ceiling of every 2F column)
GENERAL_NOTE_T = X("0.16")   # ST general note 18 'all slabs 16 cm unless stated' (own read 7D, T-044 r2)
PC_OFFSET = X("0.75")        # PC-2F planted on a 0.75 support (T-678 height formula, merged)
B15_DEPTH = X("1.20")        # B15 20 x 120 (schedule row 1F07)

# Plate-transfer members (F-T689-1) and the two tank columns. Section readings from the T-669 / T-678 / T-689 merged
# ledgers and this run's own read (drawn outline + schedule CGT 2ND row).
MEMBERS = [
    {"handle": "418", "line": "L-53f223b06db14ac41d47", "member": "C9 2F 20x70", "areas": ["0.14"], "perim": ["1.80", "1.80"],
     "kind": "PLATE", "h_hi": "4.25"},
    {"handle": "41B", "line": "L-26f6b6f2365c72e42291", "member": "C2 2F 20x50", "areas": ["0.10"], "perim": ["1.40", "1.40"],
     "kind": "PLATE", "h_hi": "4.25"},
    {"handle": "41E", "line": "L-33a9b7728781fcba12e2", "member": "C2 2F 20x50", "areas": ["0.10"], "perim": ["1.40", "1.40"],
     "kind": "PLATE", "h_hi": "4.25"},
    {"handle": "421", "line": "L-d79d17d14f39d5148cb8", "member": "C1 2F 20x50", "areas": ["0.10"], "perim": ["1.40", "1.40"],
     "kind": "PLATE", "h_hi": "4.25"},
    {"handle": "778", "line": "L-541c7e565bb93ecdb78b", "member": "PC-2F (drawn 20x40 vs text 77C P.C 20x50)",
     "areas": ["0.08", "0.10"], "perim": ["1.20", "1.40"], "kind": "PLATE", "offset": "0.75", "h_hi": "3.50"},
    {"handle": "40F", "line": "L-0ede77cfd0badc4c7d62", "member": "C2 2F tank (drawn 20x50 = schedule 2ND 20x50)",
     "areas": ["0.10"], "perim": ["1.40", "1.40"], "kind": "TANK", "item": "D-44 (B15 20x120 up / down-stand)"},
    {"handle": "424", "line": "L-c10e2945d582b5a03126", "member": "C3 2F tank (drawn 25x50 vs schedule 2ND 20x50)",
     "areas": ["0.10", "0.125"], "perim": ["1.40", "1.50"], "kind": "TANK",
     "item": "D-44 (B15 20x120 up / down-stand); section CONFLICT D-66"},
]
# The six columns T-693 changed (formwork consequence only; their concrete is not moved here)
T693_SIX = [
    {"line": "L-919a5749ef79759e01ca", "member": "C2 2F 412", "perim": ["1.40", "1.40"], "h": ["3.287", "4.25"],
     "panels": ["P1", "P2"]},
    {"line": "L-9f5a647014bbf83359f9", "member": "C GF annex 34A", "perim": ["1.20", "1.40"], "h": ["3.294", "4.05"],
     "t": ["0.16", "0.16"]},
    {"line": "L-c0b3340a906c2c7650f8", "member": "C GF annex 34D", "perim": ["1.20", "1.40"], "h": ["3.294", "4.05"],
     "t": ["0.16", "0.16"]},
    {"line": "L-e6c1c9a7feec10f64975", "member": "C GF annex 356", "perim": ["1.20", "1.40"], "h": ["3.294", "4.05"],
     "t": ["0.16", "0.16"]},
    {"line": "L-694a75c84dd6e4bb4491", "member": "C3 GF annex 350", "perim": ["1.20", "1.50"], "h": ["3.294", "4.05"],
     "t": ["0.16", "0.16"]},
    {"line": "L-bc01297b1c4a4c45a15f", "member": "C5 2F 415", "perim": ["1.40", "1.60"], "h": ["3.287", "4.25"],
     "panels": ["P4"]},
]


def s(v):
    return None if v is None else str(R.q6(X(str(v))))


def build():
    own = json.loads(OWN.read_text())
    t689 = json.loads(T689.read_text())
    idx = {l["line_id"]: l for l in json.loads(INDEX.read_text())["lines"]}
    assert own["source"]["sha256"].startswith("9f9d1179")
    pe = own["plane_evidence"]
    plate = {
        "outline": "SECOND FLOOR ROOF SLAB, outline 397 / 39A / 392 / 38D (8.10 x 6.80 m, own read)",
        "plan_texts_inside": [{"kind": "THICKNESS", "text": f"T {tt['cm']} ({tt['T']} / {tt['value']})"}
                              for p in own["panels"] for tt in p["thickness_texts"]]
        + [{"kind": "LEVEL", "text": h} for h in pe["level_texts_inside"]],
        "noncontinuous_inside": len([lt for lt in pe["linetypes_inside"] if lt != "CONTINUOUS"]),
        "section_marks_inside": pe["inserts_inside"],
        "section_steps": [{"section": "arch sheet 10 SECTION A-A", "step_m": "0", "inside_plane": None,
                           "evidence": "one continuous hatched roof slab, +13.90 on its top line (T-669, merged)"}],
        "level_convention": [f"LEVEL texts printed on the same drawing: {', '.join(pe['level_values_printed_on_the_drawing'])}",
                             f"+9.70 marks {' / '.join(pe['level_970_marks_beside_the_outline'])} print the lower roofs "
                             f"beside this outline on this plan"],
        "panels": {p["id"]: {"thickness_texts_m": [str(X(tt["cm"]) / 100) for tt in p["thickness_texts"]],
                             "general_note_m": str(GENERAL_NOTE_T)} for p in own["panels"]},
    }
    rec = R.check_plate(plate)
    s_lo = X(t689["b8_bound"]["s_lo"])
    src = own["b8_south_panels"]
    rows, fw_rows = [], []
    for m in MEMBERS:
        before = idx[m["line"]]
        assert before["item_code"] == "STR.CONC.COLUMN" and before["class"] == "HELD"
        touched = own["columns"][m["handle"]]["panels_touched"]
        top = R.column_top_lo(s_lo=s_lo, source_panels=src, plate_rec=rec, touched=touched, finished_mark=FINISHED_2F)
        assert top["state"] == "BOUNDED"
        h_lo = R.column_height_lo(top_lo=top["top_lo"], base=BASE_2F, offset=X(m.get("offset", "0")))
        tt = [rec["t"][p] for p in touched]
        if m["kind"] == "PLATE":
            low = R.q6(min(X(a) for a in m["areas"]) * h_lo)
            res = R.R89.narrow(before=(before["held_low"], before["held_high"]), after=(low, before["held_high"]),
                               source={"kind": "DRAWN_HEAD_UNDER_PRINTED_BEAM_PLATE_ZONES",
                                       "ref": f"R-T707-1 over R-T689-1 B8 s_lo {s_lo}, panel {top['governing_panel']}"})
            after = (res["low"], res["high"])
            h_hi = X(m["h_hi"])
            fw = R.formwork_sides(perimeters=m["perim"], h=(h_lo, h_hi), t=(min(tt), max(tt)))
        else:
            alt = {"DOWN-STAND (top = slab top <= +13.90)": "h <= 4.250000 m",
                   "UP-STAND (B15 bottom at the soffit of P2, the only panel on its band: top <= 13.90 - t_P2 + 1.20)":
                       f"h <= {R.q6(FINISHED_2F - rec['t']['P2'] + B15_DEPTH - BASE_2F)} m"}
            res = R.one_sided_low(areas=m["areas"], h_lo=h_lo, item=m["item"], alternatives=alt)
            assert before["held_low"] is None and before["held_high"] is None
            R.R89.narrow(before=(None, None), after=(res["low"], None),
                         source={"kind": "DRAWN_HEAD_UNDER_PRINTED_BEAM_PLATE_ZONES", "ref": "R-T707-2 over R-T707-1"})
            after = (res["low"], None)
            fw = R.formwork_sides(perimeters=m["perim"], h=(h_lo, None), t=(min(tt), max(tt)))
        rows.append({"line_id": m["line"], "member": m["member"], "handle": m["handle"], "kind": m["kind"],
                     "panels_touched": touched, "panel_t_m": [s(x) for x in tt],
                     "top_lo": s(top["top_lo"]), "governing_panel": top["governing_panel"], "h_lo": s(h_lo),
                     "areas_m2": m["areas"], "before": [s(before["held_low"]), s(before["held_high"])],
                     "after": [s(after[0]), s(after[1])],
                     "delta_low_m3": s((X(str(after[0])) - X(str(before["held_low"]))) if before["held_low"] is not None
                                       else X(str(after[0]))),
                     "class_after": "HELD (bounded)" if after[1] is not None else "HELD LOWER_ONLY (high OPEN)",
                     "item": m.get("item", "D-39 (2F roof slab top) high end"),
                     "beside": res.get("alternatives_beside_not_applied", {})})
        fw_line = [l for l in idx.values() if l["element_id"].startswith(f"FW:{m['line']}:")]
        fw_rows.append({"fw_line": fw_line[0]["line_id"], "column_line": m["line"], "member": m["member"],
                        "perimeter_m": m["perim"], "h_m": [s(h_lo), m.get("h_hi")], "t_m": [s(min(tt)), s(max(tt))],
                        "low_m2": s(fw["low_m2"]), "high_m2": s(fw["high_m2"]), "state": "HELD with the column"})
    for m in T693_SIX:
        t = m.get("t") or [str(min(rec["t"][p] for p in m["panels"])), str(max(rec["t"][p] for p in m["panels"]))]
        fw = R.formwork_sides(perimeters=m["perim"], h=m["h"], t=t)
        fw_line = [l for l in idx.values() if l["element_id"].startswith(f"FW:{m['line']}:")]
        assert fw_line and fw_line[0]["held_low"] is None and idx[m["line"]]["held_low"] is not None
        fw_rows.append({"fw_line": fw_line[0]["line_id"], "column_line": m["line"], "member": m["member"] + " (T-693)",
                        "perimeter_m": m["perim"], "h_m": m["h"], "t_m": [s(t[0]), s(t[1])],
                        "low_m2": s(fw["low_m2"]), "high_m2": s(fw["high_m2"]), "state": "HELD with the column"})
    # family effect on STR.CONC.COLUMN
    fam = [l for l in idx.values() if l["item_code"] == "STR.CONC.COLUMN" and l["class"] == "HELD"]
    lo0 = sum(X(str(l["held_low"])) for l in fam if l["held_low"] is not None)
    hi0 = sum(X(str(l["held_high"])) for l in fam if l["held_high"] is not None)
    plate_d = sum(X(r["delta_low_m3"]) for r in rows if r["kind"] == "PLATE")
    tank_lo = sum(X(r["after"][0]) for r in rows if r["kind"] == "TANK")
    named = X("0.133640")
    zone_cost = named - plate_d
    fam_out = {"before": {"bounded_lines": sum(1 for l in fam if l["held_low"] is not None), "low": s(lo0),
                          "high": s(hi0), "blank": sum(1 for l in fam if l["held_low"] is None)},
               "after": {"bounded_lines": sum(1 for l in fam if l["held_low"] is not None), "low": s(lo0 + plate_d),
                         "high": s(hi0), "lower_only_lines": 2, "lower_only_floor": s(tank_lo), "blank": 0},
               "plate_transfer_applied_m3": s(plate_d), "t689_one_plate_named_m3": s(named),
               "zone_allowance_m3": s(zone_cost)}
    # R-T669-2 restated under R-T707-1 (consistency, F-T689-1): W26 apex +12.50 under the T 18 stair-roof panel
    # (D-T173-1, Checker); its soffit >= 12.50, so a 0.16 panel top >= 12.66 (flush soffit), not 12.68.
    r69 = {"w26_panel_t": "0.18", "tank_panel_top_lo": "12.680000", "typical_panel_top_lo": "12.660000",
           "superseded_by": f"B8 bound {s_lo} (tank panels) / {s(s_lo - X('0.02'))} (0.16 panels)",
           "overstatement_if_b8_refused_m3": s(X("0.14") * X("0.02") + X("0.10") * X("0.02") + X("0.08") * X("0.02"))}
    return {"schema": "T707_COLUMN_TAIL_V1", "task": "T-707", "candidate": "ARCH_TAKEOFF_V3.0.70",
            "rules": [R.RULE_1, R.RULE_2], "plate": {"state": rec["state"], "t_by_panel": {k: s(v) for k, v in
                                                                                           sorted(rec["t"].items())},
                                                     "b8_south_panels": src, "s_lo_b8": s(s_lo),
                                                     "texts_inside": plate["plan_texts_inside"],
                                                     "level_convention": plate["level_convention"]},
            "lines": rows, "formwork": fw_rows, "family": fam_out, "r_t669_2_restated": r69,
            "not_claimed": "development villa; research only, unwired; no released quantity; freelancer not used"}


def md(res):
    L = ["# T-707 column tail (generated by t707_alsenan.py; values only)", "",
         f"Plate: {res['plate']['state']}; thickness by panel {res['plate']['t_by_panel']}; B8 south panels "
         f"{res['plate']['b8_south_panels']}; s_lo(B8) {res['plate']['s_lo_b8']}.", "",
         "| Line | Member | Panels (t) | top >= | h_lo m | before m3 | after m3 | d low | class |", "|---|---|---|---|---|---|---|---|---|"]
    for r in res["lines"]:
        L.append(f"| {r['line_id'][:10]} | {r['member']} ({r['handle']}) | {', '.join(f'{p} {t}' for p, t in zip(r['panels_touched'], r['panel_t_m']))} "
                 f"| {r['top_lo']} | {r['h_lo']} | {r['before'][0] or 'blank'} .. {r['before'][1] or 'OPEN'} | "
                 f"{r['after'][0]} .. {r['after'][1] or 'OPEN'} | {r['delta_low_m3']} | {r['class_after']} |")
    L += ["", "| FW line | Column | P m | h m | t m | low m2 | high m2 | state |", "|---|---|---|---|---|---|---|---|"]
    for f in res["formwork"]:
        L.append(f"| {f['fw_line'][:10]} | {f['member']} | {' .. '.join(f['perimeter_m'])} | {f['h_m'][0]} .. "
                 f"{f['h_m'][1] or 'OPEN'} | {' .. '.join(f['t_m'])} | {f['low_m2']} | {f['high_m2'] or 'OPEN'} | {f['state']} |")
    L += ["", f"Family: {json.dumps(res['family'])}", "", f"R-T669-2 restated: {json.dumps(res['r_t669_2_restated'])}", ""]
    return "\n".join(L)


def main(argv):
    res = build()
    text = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT_J.write_text(text)
        OUT_M.write_text(md(res))
    if "--check" in argv:
        assert OUT_J.read_text() == text and OUT_M.read_text() == md(res), "committed T-707 tables are stale"
        print("T707 check: committed tables reproduce")
    print(json.dumps(res["family"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
