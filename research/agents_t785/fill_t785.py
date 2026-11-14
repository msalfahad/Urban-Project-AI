"""T-785 (F-19, lane A): wet-room waterproofing vs the freelancer, floor m2 and upturn in his unit (lm), on the candidate
line index ARCH_TAKEOFF_V3.0.82 (research/agents_t770/out/LINE_INDEX_V3_0_82.json). DELIVERY MODE fix-row set; nothing
is wired here (Worker 3 wires it in a T-770 round). Inputs are merged repository files only (no drawing, no client data):

  index      research/agents_t770/out/LINE_INDEX_V3_0_82.json
  rooms      research/agents_t546/t546_inputs.py (per-room hand basis T-074, doorway segments, open edges, his sheet row)
  his cells  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (floors / waterproofing workbook, waterproofing sheet
             rows 14-36, C = perimeter lm, D = area m2; G40 = 144.61 'upturns' in m.l, H39 = 72.01 m2)
  sunken     research/agents_t710/out/T710_WP_ROUND3.json (six suspended wet rooms: wall run, recess loop, beam bound)
  pantry     research/agents_t710 (c) (door D120 1.00 x wall 0.20, open side DIM 5E1 4.50), T-743 census (1 floor drain)

Outputs out/FIX_ROWS.json + out/FIX_ROWS.md: rows = changes to existing lines (6 sunken-room upturns, R-T785-2),
new_lines = 18 lm upturn lines (R-T785-1) + 6 recess lines (R-T785-2) + 5 pantry lines absent from the candidate.

    python3 -I research/agents_t785/fill_t785.py [--check]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "out"
IDX = ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_82.json"
T546 = ROOT / "research/agents_t546/t546_inputs.py"
RAW = ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
T710 = ROOT / "research/agents_t710/out/T710_WP_ROUND3.json"
T743 = ROOT / "research/agents_t743/out/T743_ALSENAN_COUNTS.json"
PANTRY = "GF-RC99C2A"
PANTRY_UPTURN_RUN = 9.50   # T-767 DEFAULT row: 15.00 - open side 4.50 - door 1.00
PANTRY_DOOR = 1.00         # D120 (T-710 c, printed)
PANTRY_WALL_T = 0.20       # wall thickness at D-GF-07 (T-710 c)
PANTRY_OPEN = 4.50         # DIM 5E1 4500 (T-710 c)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


R = _load("t785_rules", HERE / "t785_rules.py")
I546 = _load("t546_inputs", T546)


def r4(x):
    return round(x, 4) + 0.0


def r6(x):
    return round(x, 6) + 0.0


def his_cells():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    out = {}
    for x in d["rows"]:
        if x["file"] == "FIN" and x["sheet"] == "العازل":
            c = {k[0]: v["v"] for k, v in x["cells"].items()}
            out[x["row"]] = c
    return out


def build():
    L = {l["line_id"]: l for l in json.loads(IDX.read_text(encoding="utf-8"))["lines"]}
    his = his_cells()
    his_floor_tot, his_up_tot = his[39]["H"], his[40]["G"]
    sunk = {x["room"]: x for x in json.loads(T710.read_text(encoding="utf-8"))["sunken"]["rooms"]}
    cen = {x["room_id"]: x for x in json.loads(T743.read_text(encoding="utf-8"))["rows"]}
    H = float(I546.UPTURN_H)

    # ---------------------------------------------------------------- per-room table, both units
    table, rows, new = [], [], []
    for key, flid, _q, _u, _x, frow, _fd, _fc, hand_b, doors, opens in I546.ROOMS:
        fl = L[flid]
        room = fl["element_id"].split(":")[0]
        ulid, _ = I546.UPTURN[key]
        ul = L[ulid]
        assert ul["class"] == "RELEASED" and fl["class"] == "RELEASED", key
        run = R.run_lm(ul["measured_net"], H)
        if room == PANTRY:
            assert abs(run - PANTRY_UPTURN_RUN) < 1e-9
            doors, opens = [str(PANTRY_DOOR)], [("open side to the dining, no wall (DIM 5E1)", str(PANTRY_OPEN))]
        hf = his.get(frow, {}) if frow else {}
        gross = R.like_for_like_perimeter(run, [float(w) for w in doors], [float(v) for _n, v in opens])
        table.append({"room": room, "title": key, "freelancer_row": frow,
                      "floor_m2": fl["measured_net"], "his_floor_m2": hf.get("D"),
                      "run_lm": r6(run), "door_segments_lm": r4(sum(float(w) for w in doors)),
                      "open_edges_lm": r4(sum(float(v) for _n, v in opens)), "gross_lm": r6(gross),
                      "his_perimeter_lm": hf.get("C"), "hand_boundary_lm": hand_b,
                      "sunken": room in sunk})
        new.append({"item_code": "FIN.WP.WALL_UPTURN_LM", "unit": "lm", "element_id": f"{room}:wp_wall_upturn_lm",
                    "label": "DEFAULT" if room == PANTRY else "MEASURED",
                    "basis": (f"run of the upturn strip of line {ulid} = {ul['measured_net']:g} m2 / rule height "
                              f"{H:.2f} (R-T785-1; walls only, doorways and open edges are their own lines)"
                              + ("; pantry run = T-767 DEFAULT 15.00 - 4.50 - 1.00" if room == PANTRY else "")),
                    "net": r6(run),
                    "vs_freelancer": ({"freelancer_lm": hf.get("C"), "like_for_like_lm": r6(gross)} if hf else
                                      {"freelancer_lm": None, "note": "not in his list (pantry, owner Q-37 A)"})})

    # ---------------------------------------------------------------- R-T785-2 sunken rooms
    sunk_sum = {"upturn_before": 0.0, "upturn_after": 0.0, "recess": 0.0, "capped": 0}
    for room, s in sorted(sunk.items()):
        ulid = next(i for i, l in L.items() if l["element_id"] == f"{room}:wp_wall_upturn")
        ul = L[ulid]
        run = float(s["upturn_run_m"])
        assert abs(run * R.FLAT_UPTURN_H - ul["measured_net"]) < 1e-9, room
        res = R.sunken_room(run, [{"panel": x["panel"], "loop_m": float(x["loop_m"]),
                                   "d_max_m": float(x["d_max_m"]), "d_printed_m": None} for x in s["recess"]])
        parts = "; ".join(f"panel {p['panel']} loop {p['loop_m']:.4f} x d {p['d_m']:.2f}"
                          + (" (default 0.30 capped at the beam bound)" if p["capped"] else " (default 0.30)")
                          for p in res["parts"])
        rows.append({"line_id": ulid, "item_code": ul["item_code"], "unit": "m2", "element_id": ul["element_id"],
                     "before": {"class": ul["class"], "net": ul["measured_net"], "low": ul["held_low"],
                                "high": ul["held_high"]},
                     "after": {"class": "RELEASED", "net": r6(res["upturn_m2"])}, "label": "DEFAULT",
                     "basis": (f"sunken wet room (T-213 / T-710 panel {'+'.join(p['panel'] for p in res['parts'])}): "
                               f"company default 'recess + 0.30 up' (owner 2026-11-13): wall run {run:.2f} x 0.30 = "
                               f"{res['upturn_m2']:.3f} m2 (was x 0.20); recess on its own line (R-T785-2)")})
        new.append({"item_code": "FIN.WP.SUNKEN_RECESS", "unit": "m2", "element_id": f"{room}:wp_sunken_recess",
                    "label": "DEFAULT",
                    "basis": (f"membrane lining the recess (tray on the structural slab): {parts} = "
                              f"{res['recess_m2']:.4f} m2 (R-T785-2; drop unprinted D-41; bound d_max = beam depth - "
                              f"slab 0.16, T-710)"),
                    "net": r6(res["recess_m2"])})
        sunk_sum["upturn_before"] += ul["measured_net"]
        sunk_sum["upturn_after"] += res["upturn_m2"]
        sunk_sum["recess"] += res["recess_m2"]
        sunk_sum["capped"] += sum(1 for p in res["parts"] if p["capped"])

    # ---------------------------------------------------------------- pantry lines absent from the candidate
    fd = cen.get(PANTRY, {}).get("pcs", {})
    n_pen = sum(fd.values())
    if n_pen <= 0:
        raise SystemExit("pantry penetration count missing: refuse (never 0)")
    for code, unit, el, label, net, basis in (
            ("FIN.WP.DOORWAY", "m2", f"{PANTRY}:doorway D120", "DRAWING-READ", PANTRY_DOOR * PANTRY_WALL_T,
             "floor piece through door D120: printed gap 1.00 x wall 0.20 (T-710 c)"),
            ("FIN.WP.DOORWAY_TRANSITION_NR", "pcs", f"{PANTRY}:doorway transition nr D120", "DRAWING-READ", 1.0,
             "one transition per physical door (Q-35 C): D120"),
            ("FIN.WP.DOORWAY_TRANSITION", "m2", f"{PANTRY}:doorway transition D120", "ESTIMATE",
             PANTRY_DOOR * R.FLAT_UPTURN_H,
             "door width 1.00 x 0.20 upturn carried across the door (same basis as the 14 released transitions, "
             "T-767)"),
            ("FIN.WP.TERMINATION", "lm", f"{PANTRY}:termination open side", "DRAWING-READ", PANTRY_OPEN,
             "membrane edge on the open dining side, printed DIM 5E1 4.50 (T-710 c; Q-37 A)"),
            ("FIN.WP.PENETRATION", "pcs", f"{PANTRY}:wp_penetrations", "MEASURED", float(n_pen),
             f"T-743 sanitary census {fd} (one WP penetration per fixture, owner default)")):
        assert not any(l["element_id"] == el for l in L.values()), el
        new.append({"item_code": code, "unit": unit, "element_id": el, "label": label, "basis": basis,
                    "net": r6(net)})

    # ---------------------------------------------------------------- the two comparisons
    floor_ours = sum(t["floor_m2"] for t in table)
    floor_comps = [{"name": c["name"], "qty": c["qty"], "sign": c["sign"], "cause": c["cause"], "room": r["room"]}
                   for r in I546.floor_rows() for c in r["components"]]
    floor = R.split(floor_ours, his_floor_tot, floor_comps)
    up_ours = sum(t["run_lm"] for t in table)
    up_comps = []
    for t in table:
        if t["room"] == PANTRY:
            up_comps.append({"name": "pantry upturn run (not in his list, owner Q-37 A)", "qty": t["run_lm"],
                             "sign": 1, "cause": "RULE_DIFFERENCE", "room": t["title"]})
    for r in I546.upturn_rows():
        for c in r.get("components", []):
            cause = c["cause"]
            if c["name"].startswith("doorway segment"):
                cause = "RULE_DIFFERENCE"   # now a released line of its own (T-767), his perimeter runs across it
            up_comps.append({"name": c["name"], "qty": c["qty"], "sign": c["sign"], "cause": cause, "room": r["room"]})
    upturn = R.split(up_ours, his_up_tot, up_comps)
    by_cause = {}
    for nm, comps in (("floor", floor_comps), ("upturn", up_comps)):
        for c in comps:
            k = f"{nm}:{c['cause']}"
            by_cause[k] = r6(by_cause.get(k, 0.0) + float(c["qty"]) * c["sign"])
    like17 = [t for t in table if t["room"] != PANTRY]
    gross17 = sum(t["gross_lm"] for t in like17)

    for x in rows:
        assert x["after"]["net"] > 0 and x["label"] in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
    for x in new:
        assert x["net"] > 0 and x["label"] in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
    wp_m2_before = sum(l["measured_net"] for l in L.values() if l["item_code"] == "FIN.WP.WALL_UPTURN")
    summ = {
        "candidate": "ARCH_TAKEOFF_V3.0.82",
        "his_room_list": "17 rows (GF 10 incl. kitchen, 1F 6 incl. laundry, roof floor 1); ours 18 = his 17 + pantry",
        "floor_m2": {"ours": r6(floor_ours), "his": his_floor_tot, "diff": r6(floor["diff"]), "pct": round(floor["pct"], 2),
                     "residual": r6(floor["residual"]), "like_for_like_17_rooms": r6(floor_ours - 13.455),
                     "like_for_like_pct": round(100 * (floor_ours - 13.455 - his_floor_tot) / his_floor_tot, 2)},
        "upturn_lm": {"ours_run": r6(up_ours), "his": his_up_tot, "diff": r6(upturn["diff"]),
                      "pct": round(upturn["pct"], 2), "residual": r6(upturn["residual"]),
                      "like_for_like_17_gross": r6(gross17),
                      "like_for_like_pct": round(100 * (gross17 - his_up_tot) / his_up_tot, 2)},
        "by_cause": by_cause,
        "sunken_rooms": {"n": len(sunk), "upturn_before_m2": r6(sunk_sum["upturn_before"]),
                         "upturn_after_m2": r6(sunk_sum["upturn_after"]), "recess_m2": r6(sunk_sum["recess"]),
                         "recess_parts_capped": sunk_sum["capped"]},
        "wall_upturn_m2": {"before": r6(wp_m2_before),
                           "after": r6(wp_m2_before - sunk_sum["upturn_before"] + sunk_sum["upturn_after"])},
        "rows": len(rows), "new_lines": len(new),
        "flags": [
            "F-T785-1: the D-41 default recess 0.30 (main chat 13 Nov, used by T-765 drop walls) exceeds the T-710 "
            "beam bound d_max 0.24 on panels 275 / 276 / 280 / 287 / 5BF; R-T785-2 caps it there (298: 0.30 < 0.34). "
            "T-765 GF-W20 uses 0.30: 0.9308 x 0.06 = 0.056 m2 of blockwork, below materiality; one drop value per "
            "panel across trades is a T-770 wiring check",
            "F-T785-2: the pantry had 5 WP lines absent from the candidate (doorway, transition, transition nr, "
            "termination, penetration; T-710 c / T-767 note): added as new lines",
            "his 72.01 / 144.61 are also his wet-room gypsum ceiling and cornice figures (decor sheet H74 / H75): "
            "one room list feeds three trades"]}
    return {"schema": "URBAN_FIX_ROWS_V1", "task": "T-785", "candidate_version": "ARCH_TAKEOFF_V3.0.82",
            "inputs": [str(p.relative_to(ROOT)) for p in (IDX, T546, RAW, T710, T743)],
            "summary": summ, "rooms": table, "rows": rows, "new_lines": new,
            "floor_components": floor_comps, "upturn_components": up_comps}


def md(d):
    s = d["summary"]
    f, u = s["floor_m2"], s["upturn_lm"]
    o = ["# T-785 wet-room waterproofing vs the freelancer (V3.0.82; fix rows, unwired)", "",
         f"His room list: {s['his_room_list']}.", "",
         f"FLOOR m2: ours {f['ours']} vs his {f['his']} = {f['diff']:+} ({f['pct']:+} %); residual {f['residual']}. "
         f"Like for like (17 rooms, pantry out): {f['like_for_like_17_rooms']} ({f['like_for_like_pct']:+} %).",
         f"UPTURN lm: our wall run {u['ours_run']} vs his perimeter {u['his']} = {u['diff']:+} ({u['pct']:+} %); "
         f"residual {u['residual']}. On his gross-perimeter basis (17 rooms: run + doorway segments + open edges): "
         f"{u['like_for_like_17_gross']} ({u['like_for_like_pct']:+} %).", "",
         "| cause | net |", "|---|---|"]
    o += [f"| {k} | {v:+} |" for k, v in sorted(s["by_cause"].items())]
    sk = s["sunken_rooms"]
    o += ["", f"SUNKEN rooms (R-T785-2, {sk['n']}): upturn {sk['upturn_before_m2']} -> {sk['upturn_after_m2']} m2, recess "
          f"{sk['recess_m2']} m2 new ({sk['recess_parts_capped']} panel parts capped at the beam bound). Wall upturn m2 "
          f"{s['wall_upturn_m2']['before']} -> {s['wall_upturn_m2']['after']}.", ""]
    o += [f"- {x}" for x in s["flags"]]
    o += ["", "| room | title | his row | floor | his floor | run lm | doors lm | open lm | gross lm | his lm | sunken |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in d["rooms"]:
        o.append(f"| {t['room']} | {t['title']} | {t['freelancer_row']} | {t['floor_m2']} | {t['his_floor_m2']} | "
                 f"{t['run_lm']} | {t['door_segments_lm']} | {t['open_edges_lm']} | {t['gross_lm']} | "
                 f"{t['his_perimeter_lm']} | {t['sunken']} |")
    o += ["", "## Changed lines", "", "| line | element | before | after | label | basis |", "|---|---|---|---|---|---|"]
    for x in d["rows"]:
        o.append(f"| {x['line_id']} | {x['element_id']} | {x['before']['net']} | {x['after']['net']} | {x['label']} | "
                 f"{x['basis']} |")
    o += ["", "## New lines", "", "| item | unit | element | net | label | basis |", "|---|---|---|---|---|---|"]
    for x in d["new_lines"]:
        o.append(f"| {x['item_code']} | {x['unit']} | {x['element_id']} | {x['net']} | {x['label']} | {x['basis']} |")
    o += ["", "## Upturn components (lm, ours - his)", "", "| room | component | lm | cause |", "|---|---|---|---|"]
    for c in d["upturn_components"]:
        o.append(f"| {c['room']} | {c['name']} | {c['sign'] * float(c['qty']):+} | {c['cause']} |")
    o += ["", "## Floor components (m2, ours - his)", "", "| room | component | m2 | cause |", "|---|---|---|---|"]
    for c in d["floor_components"]:
        o.append(f"| {c['room']} | {c['name']} | {c['sign'] * float(c['qty']):+} | {c['cause']} |")
    return "\n".join(o) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        ok = (OUT / "FIX_ROWS.json").read_text(encoding="utf-8") == js
        print("T-785 check", "PASS" if ok else "FAIL (stale out/FIX_ROWS.json)")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "FIX_ROWS.json").write_text(js, encoding="utf-8")
    (OUT / "FIX_ROWS.md").write_text(md(d), encoding="utf-8")
    print(json.dumps(d["summary"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
