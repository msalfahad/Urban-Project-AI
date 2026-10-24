"""T-250 Alsenan driver: geometric face crosswalk (face length per wall), curved room-side lines (W03, W17), the W06
room, and the one-datum reading of the 18 roof-datum faces. Research only: no engine module, method, rule / knowledge
version, registry or released quantity is changed; nothing is applied (deltas for T-244 only).

Inputs: the capture pickle written by capture_t250.py OUTSIDE the repository (coordinates stay there), and merged
research CSVs of this repository (listed in INPUTS). Outputs (this folder): lengths, handles and ids only.

Usage (project venv): python -I research/agents_t250/alsenan_t250.py <scratch>/t250_capture.pkl [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import face_crosswalk as X  # noqa: E402

INPUTS = {
    "t143": "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv",       # wall id -> V2 run ids (T-143, merged)
    "reg": "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv",     # register v1 lengths (T-225, merged)
    "t017": "research/agents_t017/T017_WALL_AGREEMENT.csv",           # independent census arch run (T-017, merged)
    "t237": "research/agents_t237/FACES_T237.csv",                    # room-wall faces + band per metre (T-237)
    "t237f": "research/agents_t237/FINDINGS_T237.csv",
    "walk": "research/agents_t128/walk_r3.json",                      # T-128 r3 walk (contours)
    "t128o": "research/agents_t128/OPENINGS_T128_R3.csv",
    "t128r": "research/agents_t128/ROOMS_T128_R3.csv",
    "t175": "research/agents_t175/T175_OPENING_HOSTS.csv",
    "t249": "research/agents_t249/OPENINGS_T249.csv",
}
CURVED_BANDS = ("ARCBAND", "CURVED_STUB")
R = lambda v, n=3: None if v is None else round(v, n)   # noqa: E731


def rd(key):
    return list(csv.DictReader(open(ROOT / INPUTS[key], encoding="utf-8")))


def wall_map():
    """(floor, run id) -> register wall id(s) (T-143 v2_runs). Two walls on one run stay together, as the register keeps them."""
    m = defaultdict(list)
    for r in rd("t143"):
        for run in (r["v2_runs"] or "").split():
            m[(r["floor"], run)].append(r["row_id"])
    return {k: " + ".join(sorted(set(v))) for k, v in m.items()}


def straight(bands):
    return [b for b in bands if b.get("kind") not in CURVED_BANDS and "|" not in b["band"]]


def face_reading(c, span):
    """what the side is, in words: every metre of the run named (closure residual 0 by construction, so the reading is
    the decomposition itself)."""
    room = sum(c["ROOM"].values())
    parts = []
    if room >= span - X.RESIDUAL_OK_M:
        return "ROOM FACE OVER THE WHOLE RUN"
    if room <= X.RESIDUAL_OK_M:
        parts.append("NO ROOM ON THIS SIDE (exterior, court, shaft or an unwalked space)" if c["NO_ROOM"] > span / 2
                     else "NO ROOM FACE")
    else:
        parts.append(f"room face {room:.3f} of {span:.3f}")
    for k, v in sorted(c["JUNCTION"].items()):
        if v >= 0.01:
            parts.append(f"inside {k} {v:.3f} (L / T end or crossing wall)")
    if c["COLUMN"] >= 0.01:
        parts.append(f"column outline {c['COLUMN']:.3f} (column proud of the face: its faces are off this line)")
    if c["NO_ROOM"] >= 0.01 and room > X.RESIDUAL_OK_M:
        parts.append(f"no room {c['NO_ROOM']:.3f}")
    return "; ".join(parts)


def crosswalk(C):
    wm = wall_map()
    reg = {r["wall_id"]: r for r in rd("reg")}
    t017 = {r["row_id"]: r for r in rd("t017")}
    face_rows, side_rows, room_un, room_strip = [], [], {}, {}
    for fl in ("GF", "1F", "2F"):
        RUN = C["runs"][fl]
        bands = X.prepare(straight(RUN["bands"]))
        smp = {r: [tuple(q) + (h,) for q, h in zip(v, C["handles"][r])] for r, v in C["samples"].items()
               if C["room_floor"][r] == fl}
        faces, un, strip = X.assign_samples(smp, bands, {r: C["polys"][r] for r in smp})
        room_un.update({r: dict(v) for r, v in un.items()})
        room_strip.update({r: dict(v) for r, v in strip.items()})
        spans = defaultdict(list)
        for s in RUN["spans"]:
            spans[s["parent"]].append(s)
        arch = {r["run_id"]: r for r in RUN["runs"]}
        for b in bands:
            L = b["_f"][4]
            # a split piece belongs to the final run that lists it as a member (V1 can re-join pieces, e.g. a
            # crossing-through-both split: WB-..#1 + #2 -> run #1)
            owner = {m: r["run_id"] for r in RUN["runs"] for m in (r.get("members") or [r["run_id"]])}
            pieces = sorted([(s["s0"], s["s1"], owner.get(s["run_id"], s["run_id"])) for s in spans.get(b["band"], [])]) \
                or [(0.0, L, b["band"])]
            for side in (1, -1):
                fs = faces.get((b["band"], side), {})
                parts = X.split_by_piece(fs, [(s0, s1, k) for k, (s0, s1, _) in enumerate(pieces)])
                for k, (s0, s1, run_id) in enumerate(pieces + [(None, None, None)]):
                    sub = parts.get(k if run_id is not None else None, {})
                    if run_id is None:
                        if not sub:
                            continue
                        stretch = [st for st in RUN["stretches"] if st["wall_id"] == b["band"] and not st["in_run"]]
                        wid, rid_out = "(none: band stretch outside every V2 run)", f"{b['band']} stretch"
                        why = "; ".join(f"{st['from_m']:.2f}-{st['to_m']:.2f} m" for st in stretch) or "band end"
                    else:
                        c = X.close_side(b, side, s0, s1, sub, bands, RUN["columns"])
                        past = X.room_faces_outside_run(sub, s0, s1)
                        wid = wm.get((fl, run_id), "")
                        rid_out = run_id
                        rg = reg.get(wid) or {}
                        cen = t017.get(wid) or {}
                        resid = c["residual_m"]
                        side_rows.append({
                            "floor": fl, "wall_id": wid or "(no register row)", "run_id": run_id, "t_m": b["t_m"],
                            "side": "+" if side > 0 else "-", "span_m": R(s1 - s0),
                            "v2_arch_run_m": R((arch.get(run_id) or {}).get("arch_run_lm")),
                            "register_length_m": rg.get("length_m", ""), "t017_census_arch_run_m": cen.get("census_arch_run_m", ""),
                            "room_face_m": R(sum(c["ROOM"].values())),
                            "rooms": "; ".join(f"{k} {v:.3f}" for k, v in sorted(c["ROOM"].items())),
                            "junction_m": R(sum(c["JUNCTION"].values())),
                            "junction_with": "; ".join(f"{k} {v:.3f}" for k, v in sorted(c["JUNCTION"].items()) if v >= 0.01),
                            "column_m": R(c["COLUMN"]), "no_room_m": R(c["NO_ROOM"]),
                            "room_face_past_run_end_m": R(sum(past.values())), "residual_m": R(resid, 4),
                            "status": "CLOSED" if abs(resid) <= X.RESIDUAL_OK_M else "OPEN",
                            "face_reading": face_reading(c, s1 - s0)})
                        why = ""
                    for room, g in sorted(sub.items()):
                        bc = g["by_class"]
                        face_rows.append({
                            "floor": fl, "room": room, "wall_id": wid or "(no register row)", "run_id": rid_out,
                            "t_m": b["t_m"], "side": "+" if side > 0 else "-", "face_m": R(g["m"]),
                            "finish_m (WALL+COLUMN)": R(sum(bc.get(k, 0) for k in X.FINISH_CLASSES)),
                            "window_m": R(bc.get("WINDOW", 0)), "door_m": R(bc.get("DOOR", 0)), "gap_m": R(bc.get("GAP", 0)),
                            "virtual_m": R(bc.get("VIRTUAL", 0)),
                            "drawn_handles_m (P7757.dxf)": " ".join(f"{h}:{m:.2f}" for h, m in sorted(
                                g["handles"].items(), key=lambda kv: -kv[1]) if m >= 0.05),
                            "note": (f"V2 split stretch {why}: wall face drawn by the room contour, no masonry run" if run_id is None else ""),
                            "status": "DRAWING-CONFIRMED (geometry of the merged T-128 r3 walk on P7757.dxf; Checker to re-measure)"})
    return face_rows, side_rows, room_un, room_strip


def room_closure(C, face_rows, room_un, room_strip):
    walk = json.load(open(ROOT / INPUTS["walk"]))["rooms"]
    curved = defaultdict(lambda: defaultdict(float))
    for oid, o in C["openings"].items():
        for p in o["pieces"]:
            if p["kind"] == "ARC":
                for room, m in p["touch"].items():
                    curved[room][oid] += m
    on = defaultdict(float)
    for f in face_rows:
        on[f["room"]] += f["face_m"]
    rows = []
    for room in sorted(walk):
        u = room_un.get(room, {})
        total_samples = sum(s[3] for s in C["samples"][room])
        rows.append({
            "room": room, "walk_contour_m (T-128 r3)": walk[room]["contour_m"], "sampled_m": R(total_samples),
            "on_straight_wall_faces_m": R(on[room]),
            "off_wall_line_m": R(sum(u.values())),
            "off: WALL": R(u.get("WALL", 0)), "off: COLUMN": R(u.get("COLUMN", 0)), "off: WINDOW": R(u.get("WINDOW", 0)),
            "off: DOOR+GAP": R(u.get("DOOR", 0) + u.get("GAP", 0)), "off: VIRTUAL (open side)": R(u.get("VIRTUAL", 0)),
            "of which inside a band strip (room between the two lines of a band)": R(sum(room_strip.get(room, {}).values())),
            "curved glazing touched": "; ".join(f"{k} {v:.3f}" for k, v in sorted(curved[room].items())),
            "closure_m": R(total_samples - on[room] - sum(u.values()), 4),
            "meaning of off-line metres": "column faces standing proud of the wall line (plastered as wall, T-128 COLUMN); "
                                          "curved glazing / curved stubs (no straight band); jamb returns and reveals of "
                                          "doorways between collinear walls; open sides (VIRTUAL, never plastered)"})
    return rows


def t237_faces(face_rows):
    by = defaultdict(float)
    fin = defaultdict(float)
    for f in face_rows:
        for w in f["wall_id"].split(" + "):
            by[(f["room"], w)] += f["face_m"]
            fin[(f["room"], w)] += f["finish_m (WALL+COLUMN)"]
    roof = {(r["room"], r["wall"]) for r in rd("t237f") if r["kind"] == "HEIGHT_DATUM_SPLIT_ROOF"}
    rows, seen = [], set()
    for r in rd("t237"):
        k = (r["room"], r["wall_id"])
        if k in seen:
            continue
        seen.add(k)
        L = by.get(k)
        bpm = r["band_m2_per_m_face"]
        rows.append({
            "room": r["room"], "wall_id": r["wall_id"], "height_code (T-237)": r["height_code"],
            "face_m (T-250)": R(L), "finish_m (T-250)": R(fin.get(k)),
            "band_m2_per_m_face (T-237)": bpm,
            "band_m2 (face_m x band per m)": R(L * float(bpm)) if (L is not None and bpm not in ("", None)) else "",
            "roof_datum_face": "yes" if k in roof else "",
            "m2 per 0.01 m of storey interval": R(X.sensitivity_m2(L, 0.01), 4) if L is not None else "HELD (no face found)",
            "status": "face found" if L is not None else "NOT FOUND on a straight band (curved / off-line face)"})
    return rows


def curved_room_side(C):
    t128 = defaultdict(float)
    for r in rd("t128o"):
        lab = r["OPENING"]
        for oid in ("W03", "W17"):
            if lab.startswith(oid):
                t128[oid] += float(r["WALKED_FACE_M"])
    out = []
    for oid in ("W03", "W17"):
        o = C["openings"][oid]
        arcs = [p for p in o["pieces"] if p["kind"] == "ARC"]
        face = max(arcs, key=lambda p: sum(p["touch"].values()))
        cand = [{"id": f"{p['handle']} (glass, r {p['radius_m']:.3f})", "kind": "GLASS", "arc_m": p["len_m"],
                 "touch_m": p["len_m"] - p["untouched_m"] if p is face else sum(p["touch"].values())} for p in arcs]
        cand += [{"id": f"{c['handle']} (layer {c['layer']}, r {c['radius_m']:.3f})", "kind": "BAND_FACE", "arc_m": c["len_m"],
                  "touch_m": sum(c["touch"].values())} for c in o["concentric"]
                 if c["handle"] not in {p["handle"] for p in arcs} and c["len_m"] > 1.0]
        returns = sum(p["len_m"] for p in o["pieces"] if p["handle"] == face["handle"] and p["kind"] == "LINE")
        lo, hi = face["untouched_m"], face["untouched_m"] + (2 * 0.006 if face["untouched_m"] > 0 else 0.0)
        printed = {"W03": 6.57, "W17": None}[oid]
        rec_lo = X.room_side_line(cand, t128[oid], returns, hi, printed)
        rec_hi = X.room_side_line(cand, t128[oid], returns, lo, printed)
        out.append({
            "opening": oid, "room_face_line": rec_lo["room_face_id"], "room_face_arc_m": R(face["len_m"], 4),
            "jamb_returns_on_wall_face_m": R(returns, 4),
            "partition_end_on_the_glass_m": f"{lo:.4f} .. {hi:.4f}" if hi else "0",
            "partition_on_glass (layer-1 handles)": " ".join(face["untouched_on_layer1"]),
            "developed_room_side_m": f"{rec_lo['developed_m']:.4f} .. {rec_hi['developed_m']:.4f}",
            "t128_walked_m": R(t128[oid], 4),
            "t128_minus_developed_m": f"{t128[oid] - rec_hi['developed_m']:+.4f} .. {t128[oid] - rec_lo['developed_m']:+.4f}",
            "refused_as_room_face": "; ".join(rec_lo["refused"]),
            "window_line_width_m": printed if printed else "Q-39 C outer arc (window trade)",
            "finish_vs_window_m": (f"{rec_lo['developed_m'] - printed:+.4f} .. {rec_hi['developed_m'] - printed:+.4f}" if printed else ""),
            "verdict": ("T-128 RIGHT for finishes (room-side line = outer glass line + jamb returns - partition end); "
                        "window line keeps the owner's Q-38 A 6.57: RULE_DIFFERENCE between trades, not a mismatch"
                        if oid == "W03" else
                        "T-128 RIGHT: room-side line = outer glass arc BD2 (= Q-39 C outer arc 3.29 of the window line); "
                        "height stays HELD (T-238: 3.50 is the archivolt)")})
    return out


LABEL_FINDINGS = {
    "W06": "T-175 / T-198 side label 'W.C. core wedge A' (carried from T-144) is wrong: the glass 3E6 (+ returns 3E3 / 3EC) "
           "bounds GF-13 = wedge B 245 x 167 only; GF-12 (wedge A) is 1.26 m away. T-128 r3 and T-209 already carry W06 in "
           "GF-13: no quantity moves; the census side label is corrected",
    "W19": "label swap: the census calls the room with W19 'bath west upper'; the glass lies in T-128's 1F-03, which T-128 "
           "names 'bath west lower'. Same physical room, opposite words: crosswalk by the drawn glass, never by the name",
    "W20": "label swap (as W19): the glass lies in T-128's 1F-02 ('bath west upper' in T-128, 'lower' in the census)",
}


def window_rooms(C):
    t175 = {r["ID"]: r for r in rd("t175")}
    t128 = defaultdict(set)
    for r in rd("t128o"):
        t128[r["OPENING"].split()[0]].add(r["ROOM_ROW"])
    names = {r["ROW"]: r["ROOM"] for r in rd("t128r")}
    out = []
    for oid, o in sorted(C["openings"].items()):
        tr = defaultdict(float)
        for p in o["pieces"]:
            for room, m in p["touch"].items():
                tr[room] += m
        rooms = {k: v for k, v in tr.items() if v >= 0.05}
        h = t175.get(oid) or {}
        sides = f"{h.get('SIDE_A', '')} / {h.get('SIDE_B', '')}" if h else ""
        named = "; ".join(f"{k} ({names.get(k, '')})" for k in sorted(rooms))
        flag = LABEL_FINDINGS.get(oid, "")
        out.append({"opening": oid, "floor": o["floor"], "rooms_touching_glass (T-128 ids and names)": named,
                    "touch_m": "; ".join(f"{k} {v:.3f}" for k, v in sorted(rooms.items())),
                    "t175_sides": sides, "t128_rooms": " ".join(sorted(t128.get(oid, []))), "finding": flag})
    return out


ROOF = {
    # storey interval of the faces under a roof: floor structural top (T-214, DRAWING-CONFIRMED) and slab top above
    "1F": {"roof": "ROOF-970 (+9.70 finished)", "floor_top": 5.451, "floor_src": "1F-FLOOR/SLAB_TOP 5.451 (T-214 R3, b 0.049)",
           "continuous": 9.65, "cont_src": "2F-FLOOR/SLAB_TOP 9.65 (T-214 R3) if the roof slab is the 2F floor slab carried on "
                                            "(SECTION A-A / B-B draw one band under both, T-221 s.3)",
           "stepped": "9.70 - b_roof, b_roof = t0 + falls 0.107 .. 0.144 + layers (T-221), < 0.30 at the parapet (ST p.14)"},
    "2F": {"roof": "ROOF-1390 (+13.90 finished, no outlets drawn)", "floor_top": 9.65, "floor_src": "2F-FLOOR/SLAB_TOP 9.65 (T-214 R3)",
           "continuous": None, "cont_src": "no slab at another level to carry on",
           "stepped": "13.90 - b_roof, b_roof HELD (DRAINS_NOT_DRAWN, T-221), < 0.30 at the parapet"},
    "GF": {"roof": "ROOF-430 (annex, +4.30 finished)", "floor_top": 0.25, "floor_src": "ANNEX-FLOOR/SLAB_TOP 0.25 (T-214 R3)",
           "continuous": None, "cont_src": "annex datum HELD (owner Q-54 B)",
           "stepped": "4.30 - b_roof, b_roof = t0 + falls 0.112 .. 0.147 + layers (T-221), < 0.30 at the parapet"},
}


def roof_datum(t237rows):
    faces = {(r["room"], r["wall_id"]): r for r in rd("t237")}
    out = []
    lens = {(r["room"], r["wall_id"]): r["face_m (T-250)"] for r in t237rows}
    for r in t237rows:
        if r["roof_datum_face"] != "yes":
            continue
        f = faces[(r["room"], r["wall_id"])]
        fl = r["room"].split("-")[0]
        RF = ROOF[fl]
        reg_interval = {"GF": 4.00, "1F": 4.20, "2F": 4.20}[fl]
        # the register's block height is (interval - member): its interval is the finished-mark difference
        cont = None
        if RF["continuous"] is not None:
            cont = X.one_datum({"floor_top": (RF["floor_top"], "DRAWING-CONFIRMED"),
                                "ceiling_top": (RF["continuous"], "DRAWING-CONFIRMED"), "slab_t": 0.16,
                                "readings": {"block": reg_interval, "finish": reg_interval}})
        held = X.one_datum({"floor_top": (RF["floor_top"], "DRAWING-CONFIRMED"), "ceiling_top": (None, X.HELD),
                            "slab_t": 0.16, "readings": {"block": reg_interval, "finish": reg_interval}})
        L = lens[(r["room"], r["wall_id"])]
        hi_b = 0.30
        out.append({
            "room": r["room"], "wall_id": r["wall_id"], "roof": RF["roof"], "face_m (T-250)": L,
            "register_interval_used_m": reg_interval, "register_block_h_m": f["block_h_m"],
            "plaster_top_t128_m": f["plaster_top_m"],
            "one_datum": f"floor {RF['floor_src']} -> slab top above",
            "reading_A_continuous_slab": (f"interval {cont['interval']:.3f} = register {reg_interval:.2f} ({RF['cont_src']}); "
                                          f"plaster top {cont['plaster_h']:.3f}") if cont else f"none: {RF['cont_src']}",
            "reading_B_slab_under_roof_finish": f"interval = {RF['stepped']} - {RF['floor_top']}",
            "interval_bounds_m": (f"{(9.70 - hi_b) - RF['floor_top']:.3f} .. {cont['interval']:.3f}" if fl == "1F" else
                                  f"> {({'2F': 13.90, 'GF': 4.30}[fl] - hi_b) - RF['floor_top']:.3f} (parapet bound); "
                                  f"register's {reg_interval:.2f} implies b_roof = {({'2F': 13.90, 'GF': 4.30}[fl] - RF['floor_top']) - reg_interval:.3f} m"),
            "m2 per 0.01 m (block and plaster alike)": R(X.sensitivity_m2(L, 0.01), 4) if L is not None else "HELD",
            "status": held["status"] + (" (both readings; D-39 item 3: continuous or stepped)" if fl == "1F" else
                                        " (both readings; D-39 + " + ("ROOF-1390 outlets" if fl == "2F" else "Q-54 B annex datum") + ")"),
            "same_datum_both_ledgers": "yes: the register's 4.20 and T-128's 4.04 + 0.16 are one interval; the split is in "
                                       "status only (register formed, plaster HELD), not in value" if fl == "1F" else
                                       "yes in value; both stay HELD"})
    return out


def write(name, rows):
    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def build(C):
    face_rows, side_rows, room_un, room_strip = crosswalk(C)
    rooms = room_closure(C, face_rows, room_un, room_strip)
    t237 = t237_faces(face_rows)
    curved = curved_room_side(C)
    wins = window_rooms(C)
    roof = roof_datum(t237)
    files = {"FACE_LENGTH_T250.csv": write("", face_rows), "WALL_SIDE_CLOSURE_T250.csv": write("", side_rows),
             "ROOM_CLOSURE_T250.csv": write("", rooms), "T237_FACES_WITH_LENGTH_T250.csv": write("", t237),
             "CURVED_ROOM_SIDE_T250.csv": write("", curved), "WINDOW_ROOMS_T250.csv": write("", wins),
             "ROOF_DATUM_T250.csv": write("", roof)}
    closed = [r for r in side_rows if r["status"] == "CLOSED"]
    walls = {r["wall_id"] for r in side_rows if r["room_face_m"]}
    summary = {
        "task": "T-250", "inputs": INPUTS,
        "wall_sides": len(side_rows), "wall_sides_closed": len(closed),
        "max_abs_residual_m": max(abs(r["residual_m"]) for r in side_rows),
        "room_faces_on_straight_walls": len(face_rows), "walls_with_a_room_face": len(walls),
        "rooms": len(rooms), "room_closure_max_abs_m": max(abs(r["closure_m"]) for r in rooms),
        "face_m_total": round(sum(f["face_m"] for f in face_rows), 3),
        "finish_m_total": round(sum(f["finish_m (WALL+COLUMN)"] for f in face_rows), 3),
        "off_wall_line_m_total": round(sum(r["off_wall_line_m"] for r in rooms), 3),
        "t237_faces": len(t237), "t237_faces_found": sum(1 for r in t237 if r["face_m (T-250)"] is not None),
        "roof_datum_faces": len(roof),
        "roof_datum_m_total": round(sum(r["face_m (T-250)"] or 0 for r in roof), 3),
        "curved": {r["opening"]: {k: r[k] for k in ("developed_room_side_m", "t128_walked_m", "finish_vs_window_m")}
                   for r in curved},
    }
    files["summary.json"] = json.dumps(summary, indent=1) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    C = pickle.load(open(a.capture, "rb"))
    files = build(C)
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("check", "PASS" if not bad else f"FAIL {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(files["summary.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
