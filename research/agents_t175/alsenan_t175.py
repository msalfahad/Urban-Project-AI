"""T-175 step 2: the development villa's per-opening consequence ledger and the net block area per wall run, through
OPENING_SCOPE_V1 (engine/source/opening_scope_v1.py, not wired). Inputs are repository files only:
  research/agents_t175/T175_OPENING_HOSTS.csv   (step 1: opening -> host wall run, inside the gross or not)
  research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv (gross block m2 per run, Q-60 A heights, Q-69 B physical run)
  research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv (ST p.13 lintel schedule, MIN.40cm bearing)
Usage: python3 -I research/agents_t175/alsenan_t175.py [--out research/agents_t175]   (writes three files there)
       python3 -I research/agents_t175/alsenan_t175.py --check   (recomputes and compares with the committed files)"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from engine.source import opening_scope_v1 as OS          # noqa: E402

DC, AOA, HELD = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD"
OUTDOOR = ("outdoors", "outside", "roof", "terrace", "(Q-67)")
WET = ("W.C.", "bath", "wash", "laundry", "basin")
FLOORS = ("GF", "1F", "2F")


def face(side):
    s = side or ""
    if not s:
        return "INTERNAL_PLASTER_PAINT"
    if "lift shaft" in s:
        return "SHAFT_FACE"
    if any(k in s for k in OUTDOOR):
        return "EXTERNAL_PLASTER_PAINT"
    if any(k.lower() in s.lower() for k in WET):
        return "WALL_TILE"
    return "INTERNAL_PLASTER_PAINT"


def lintel_rows():
    out = []
    bearing = None
    for r in csv.DictReader(open(ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv",
                                 encoding="utf-8")):
        if r["RECORD"] == "SCHEDULE_ROW":
            out.append((int(r["WIDTH_LO_CM"]), int(r["WIDTH_HI_CM"]), r["ROW_ID"], int(r["D_CM"]) / 100))
        if r["ROW_ID"] == "MIN-BEARING":
            bearing = float(re.search(r"(\d+)\s*mm", r["BOUNDS"]).group(1)) / 1000
    return out, bearing


def lintel_for(w, rows, bearing):
    if w is None:
        return None
    cm = round(w * 100, 1)
    for lo, hi, rid, d in rows:
        if lo <= cm <= hi:
            return {"row": rid, "depth_m": d, "min_bearing_m": bearing}
    return {"row": None, "depth_m": 0.0, "min_bearing_m": bearing}      # in a schedule gap: listed, no depth


def clear_min(members):
    hs = [float(x) for x in re.findall(r"-> h (\d+\.\d+)", members or "")]
    return min(hs) if hs else None


def kind_of(h):
    i, k = h["ID"], h["KIND_T150"]
    if i.startswith("A-"):
        return "ARCH"
    if i.startswith("L-"):
        return "SHAFT"
    if i.startswith(("P-", "SX-")):
        return "PASSAGE"
    if i == "D-GF-15":
        return "GATE"
    if i == "U-01" or k == "WINDOW":
        return "WINDOW"
    return "DOOR"


def build():
    hosts = list(csv.DictReader(open(HERE / "T175_OPENING_HOSTS.csv", encoding="utf-8")))
    t143 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv",
                                                         encoding="utf-8"))}
    lrows, bearing = lintel_rows()
    by_row = {}
    ops = []
    for h in hosts:
        kind = kind_of(h)
        w = float(h["WIDTH_M"]) if h["WIDTH_M"] else None
        ws = DC if (w is not None and not h["WIDTH_LO_M"] and not h["HOLD_CAUSE"]) else HELD
        hv = float(h["HEIGHT_M"]) if h["HEIGHT_M"] else None
        hs = {"PRINTED": DC, "ASSUMED": AOA}.get(h["HEIGHT_STATUS_T150"], HELD)
        if hv is None:
            hs = HELD
        row = h["HOST_ROW"]
        glazed_line = h["ID"] in ("W02", "W03", "W17")
        no_wall = h["ID"] in ("U-01", "D-GF-15") or h["ID"] in ("P-GF-02", "P-GF-03", "P-GF-04", "P-GF-05")
        cons = "GLAZED" if glazed_line else ("NONE" if no_wall else "BLOCK")
        fa, fb = (face(h["SIDE_A"]), face(h["SIDE_B"])) if not no_wall else ("NONE", "NONE")
        op = {"id": h["ID"], "kind": kind, "width_m": w, "width_status": ws, "height_m": hv, "height_status": hs,
              "sill_m": float(h["SILL_ABOVE_FFL_M"]) if h["SILL_ABOVE_FFL_M"] else 0.0, "in_gross": h["IN_GROSS"] == "YES",
              "frame": kind in ("DOOR", "WINDOW", "SHAFT", "GATE"), "faces": (fa, fb),
              "wet_side": any(face(s) == "WALL_TILE" for s in (h["SIDE_A"], h["SIDE_B"])),
              "lintel": lintel_for(w, lrows, bearing)}
        t = float(t143[row]["t_m"]) if row in t143 else (float(h["WALL_T_M"]) if h["WALL_T_M"] else None)
        wall = {"id": row or f"(no T-143 run: {h['ID']})", "construction": cons, "t_m": t,
                "clear_h_min_m": clear_min(t143[row]["members_above"]) if row in t143 else None}
        c = OS.opening_consequences(op, wall)
        c["_host"] = h
        ops.append(c)
        if row in t143 and cons == "BLOCK" and op["in_gross"]:
            by_row.setdefault(row, []).append(op)
    walls = []
    for rid, r in t143.items():
        st = r["status"]
        g = float(r["gross_m2_q69_physical"]) if r["gross_m2_q69_physical"] not in ("", "HELD") else None
        arith_gs = DC if st in ("CALCULATED", "PROVISIONAL") else HELD
        wall = {"id": rid, "construction": "BLOCK", "t_m": float(r["t_m"]), "gross_m2": g, "gross_status": arith_gs,
                "clear_h_min_m": clear_min(r["members_above"])}
        res = OS.wall_net(wall, by_row.get(rid, []))
        res["floor"], res["group"], res["t143_status"] = r["floor"], r["group"], st
        res["block_type"] = r["block_type"]
        res["t_m"] = r["t_m"]
        res["held_candidate_t143"] = r["held_m2_candidate"]
        if st == "PROVISIONAL":
            res["s5_status"] = HELD
            res["s5_why"] = "gross PROVISIONAL in T-143 (" + (r["reason"] or "annex datum HELD, owner Q-54 B") + ")"
        elif st in ("PARTLY HELD", "HELD"):
            res["s5_status"] = HELD
            res["s5_why"] = "gross " + st + " in T-143: " + (r["reason"] or "")[:160]
        else:
            res["s5_status"] = res["net_status"]
            res["s5_why"] = ""
        walls.append(res)
    return ops, walls


def r3(v):
    return "" if v is None else f"{v:.3f}"


def tables(ops, walls):
    o = io.StringIO()
    w = csv.writer(o, lineterminator="\n")
    w.writerow(["opening", "floor", "kind", "host_row", "construction", "in_gross", "width_m", "width_status",
                "height_m", "height_status", "sill_m", "opening_m2", "opening_status", "block_deduction_m2",
                "block_status", "block_why", "face_A_family", "face_A_m2", "face_B_family", "face_B_m2",
                "finish_status", "reveal_lm", "reveal_lm_status", "reveal_depth_m", "reveal_depth_status", "edge",
                "edge_m", "wp_interface", "lintel_row", "lintel_status", "lintel_face_m2_candidate_min_bearing",
                "flags", "freelancer_w_x_h", "hold_cause", "binding_evidence"])
    for c in ops:
        h = c["_host"]
        bd, fa, fb = c["block_deduction"], c["finish_deduction"][0], c["finish_deduction"][1]
        lt = c["lintel"]
        fw = f"{h['FREELANCER_W']} x {h['FREELANCER_H']}" if h["FREELANCER_W"] and h["FREELANCER_H"] else ""
        w.writerow([c["id"], h["FLOOR"], c["kind"], h["HOST_ROW"], c["construction"], "YES" if c["in_gross"] else "NO",
                    r3(c["width_m"]), c["width_status"], r3(c["height_m"]), c["height_status"], r3(c["sill_m"]),
                    r3(c["opening_m2"]), c["opening_status"], r3(bd["m2"]), bd["status"], bd.get("why", ""),
                    fa["family"], r3(fa["m2"]), fb["family"], r3(fb["m2"]),
                    fa["status"] if fa["status"] != "NOT_APPLICABLE" else fb["status"],
                    r3(c["reveal_lm"]["m"]), c["reveal_lm"]["status"], r3(c["reveal_depth"]["m"]),
                    c["reveal_depth"]["status"], c["edge"]["kind"] or "", r3(c["edge"]["m"]),
                    "upturn across the doorway, NOT deducted (UP-WP-002 v2.0.0)" if c["waterproofing"] else "",
                    lt.get("row") or "", lt["status"], r3(lt.get("face_m2_candidate_at_min_bearing")),
                    ";".join(c["flags"]), fw, h["HOLD_CAUSE"], h["BINDING_EVIDENCE"]])
    a = o.getvalue()
    o = io.StringIO()
    w = csv.writer(o, lineterminator="\n")
    w.writerow(["row_id", "floor", "group", "t_m", "block_type", "t143_status", "gross_m2_t143", "openings_in_gross",
                "deducted_established_m2", "held_openings", "net_m2_on_t143_gross", "net_bounds_m2", "s5_status",
                "s5_why", "t143_held_candidate"])
    for x in walls:
        ids = ";".join(c["id"] for c in x["openings"])
        b = x.get("net_bounds_m2")
        w.writerow([x["wall"], x["floor"], x["group"], x["t_m"],
                    x["block_type"], x["t143_status"], r3(x["gross_m2"]), ids, r3(x["deducted_m2"]),
                    ";".join(x["held_openings"]), r3(x["net_m2"]),
                    f"{r3(b[0])} .. {r3(b[1])}" if b else "", x["s5_status"], x["s5_why"], x["held_candidate_t143"]])
    return a, o.getvalue()


def summary(ops, walls):
    s = {"method": OS.METHOD, "rules": list(OS.RULES), "floors": {}}
    for fl in FLOORS + ("ALL",):
        W = [x for x in walls if fl == "ALL" or x["floor"] == fl]
        O = [c for c in ops if fl == "ALL" or c["_host"]["FLOOR"] == fl]
        gross = sum(x["gross_m2"] or 0 for x in W)
        ded = {}
        for c in O:
            bd = c["block_deduction"]
            if bd["status"] == "NOT_APPLICABLE":
                continue
            k = bd["status"]
            ded.setdefault(k, [0, 0.0])
            ded[k][0] += 1
            ded[k][1] += bd["m2"] or 0.0
        net_rows = [x for x in W if x["net_m2"] is not None]
        net_dc = [x for x in net_rows if x["s5_status"] == DC]
        net_aoa = [x for x in net_rows if x["s5_status"] == AOA]
        fin = {}
        for c in O:
            for f in c["finish_deduction"]:
                if f["status"] == "NOT_APPLICABLE":
                    continue
                d = fin.setdefault(f["family"], {})
                e = d.setdefault(f["status"], [0, 0.0])
                e[0] += 1
                e[1] += f["m2"] or 0.0
        rev = {}
        for c in O:
            e = rev.setdefault(c["reveal_lm"]["status"], [0, 0.0])
            e[0] += 1
            e[1] += c["reveal_lm"]["m"] or 0.0
        s["floors"][fl] = {
            "t143_gross_measured_m2": round(gross, 3),
            "block_deductions_by_status": {k: {"n": v[0], "m2": round(v[1], 3)} for k, v in sorted(ded.items())},
            "rows": len(W), "rows_with_net": len(net_rows),
            "net_rows_gross_m2": round(sum(x["gross_m2"] for x in net_rows), 3),
            "net_rows_net_m2": round(sum(x["net_m2"] for x in net_rows), 3),
            "net_DRAWING_CONFIRMED_m2": round(sum(x["net_m2"] for x in net_dc), 3),
            "net_ASSUMED_OWNER_APPROVED_m2": round(sum(x["net_m2"] for x in net_aoa), 3),
            "net_on_provisional_gross_m2": round(sum(x["net_m2"] for x in net_rows if x["t143_status"] == "PROVISIONAL"), 3),
            "rows_net_held": [x["wall"] for x in W if x["net_m2"] is None or x["s5_status"] == HELD],
            "finish_deductions": {f: {k: {"n": v[0], "m2": round(v[1], 3)} for k, v in d.items()} for f, d in sorted(fin.items())},
            "reveal_lm_by_status": {k: {"n": v[0], "m": round(v[1], 3)} for k, v in sorted(rev.items())},
            "flags": sorted({(c["id"], f) for c in O for f in c["flags"]}),
            "gross_less_established_deductions_m2 (not a net: HELD openings remain)": round(
                gross - sum(v[1] for k, v in ded.items() if k != HELD), 3),
            "held_openings_in_gross": {"n": ded.get(HELD, [0])[0],
                                       "width_m": round(sum(c["width_m"] or 0 for c in O
                                                            if c["block_deduction"]["status"] == HELD), 3)},
            "lintel_face_candidates_min_bearing_m2": {
                "n": sum(1 for c in O if c["lintel"].get("face_m2_candidate_at_min_bearing") is not None),
                "m2": round(sum(c["lintel"].get("face_m2_candidate_at_min_bearing") or 0 for c in O), 3),
                "status": "HELD (lintel line; bearing beyond the printed MIN.40cm not established)"},
            "lintel_not_needed_head_at_member": [c["id"] for c in O if c["lintel"]["status"] == "NOT_APPLICABLE"
                                                 and c["construction"] == "BLOCK" and c["in_gross"]],
            "thresholds_lm": round(sum(c["edge"]["m"] or 0 for c in O if c["edge"]["kind"] == "THRESHOLD"), 3),
            "sills_lm": round(sum(c["edge"]["m"] or 0 for c in O if c["edge"]["kind"] == "SILL"), 3),
            "wet_doorways_upturn_not_deducted": [c["id"] for c in O if c["waterproofing"]],
        }
    s["census_gaps_found"] = [c["id"] for c in ops if c["_host"]["KIND_T150"] == "NOT IN THE T-150 CENSUS"]
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    ops, walls = build()
    t1, t2 = tables(ops, walls)
    js = json.dumps(summary(ops, walls), indent=1, ensure_ascii=False, default=list) + "\n"
    files = {"T175_OPENING_CONSEQUENCES.csv": t1, "T175_NET_BLOCK_BY_WALL.csv": t2, "summary.json": js}
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 0 if not bad else 1
    for n, t in files.items():
        (Path(a.out) / n).write_text(t, encoding="utf-8")
    print(json.dumps(summary(ops, walls)["floors"]["ALL"], ensure_ascii=False, default=list)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
