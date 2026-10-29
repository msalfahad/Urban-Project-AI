"""T-329 Alsenan runner: the WET-ROOM PLASTER BACKING under wall tile and the band ABOVE the tile, face by face on
the 18 tiled rooms + pantry, tied to the wet rooms' blank FIN.PLASTER line ids (R-T329-1 .. 4).

Inputs (merged, committed; no drawing is re-read here, no private file is needed):
  ../agents_t312/FACE_LEDGER_T312.csv    every wet-room / pantry face once (T-312 MERGED 8943b5ed; Checker re-measured
                                          every tile face in T-315 r1, own 340.2484 m2)
  ../agents_t312/OPENINGS_T312.csv       every opening once per room side with its band part
  ../agents_t312/ROOM_CLOSURE_T312.csv   the 18 rooms' walked contours (residual 0.0000 m)
  ../agents_t312/LINE_SUMMARY_T312.csv   the 17 FIN.WALL.TILE lines (+ pantry NO_LINE)
  ../agents_t312/RECONCILIATION_T312.csv the freelancer's wet-wall rows (his boundary lm x 3.00, no deduction)
  ../agents_t311/CANDIDATE_V3019_T311.json  the candidate of record's FIN.PLASTER lines (V3.0.19 json b35475bf;
                                          line ids are version-independent hashes, T-313 s.3a: equal on V3.0.20)

    python3 -I t329_alsenan.py --write | --check
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t329_backing_rules as R  # noqa: E402

T312 = HERE.parent / "agents_t312"
T311 = HERE.parent / "agents_t311" / "CANDIDATE_V3019_T311.json"
DECOR_M = 0.15            # owner Q-48 A: 0.15 m decor ceiling in every room (the drawing-derived tile top uses it too)
PANTRY_ROOM = "GF-07"
PANTRY_LINE_ELEMENT = "HL:WALL_FINISH:GF_07:PLASTER"
OWNER_PLASTER_SRC = "Q-43 (owner 2026-10-19 21:40): plaster and paint count to 3.65 GF / 3.35 1F, 2F = the Q-48 A tile top"
DWG_BAND_HELD = ("Q-52 C MODIFIED: 'plaster may run above the false ceiling ... depending on the specification'; no "
                 "specification or section prints it; URBAN-PLASTER-TO-MASONRY-TERMINATION@v1 (drawing method) "
                 "takes plaster to the soffit -> band 0 .. length x 0.15 decor; beam faces on the wall line not split")
OUT = {
    "faces": HERE / "BACKING_FACE_LEDGER_T329.csv",
    "rooms": HERE / "ROOM_BACKING_T329.csv",
    "lines": HERE / "PLASTER_LINE_MAP_T329.csv",
    "recon": HERE / "RECONCILIATION_T329.csv",
    "summary": HERE / "summary.json",
}


def _rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(s):
    s = (s or "").strip()
    return float(s) if s else None


def parse_size(kind, s):
    """'w 0.6 sill 1.7 head 2.5' / 'w 0.8 sill 0.0 head 2.2' / 'w 1.0 h HELD' -> opening dict (head None = HELD)."""
    w = float(re.search(r"w ([0-9.]+)", s).group(1))
    m_s, m_h = re.search(r"sill ([0-9.]+)", s), re.search(r"head ([0-9.]+)", s)
    k = "window" if kind == "window" else "door"      # arch / doorway: a full-height hole from the floor
    return {"kind": k, "w": w, "sill": float(m_s.group(1)) if m_s else (0.0 if k == "door" else None),
            "head": float(m_h.group(1)) if m_h else None}


def candidate_plaster():
    d = json.loads(T311.read_text(encoding="utf-8"))
    by_el = {}
    for ln in d["lines"]:
        if ln["item_code"] == R.PLASTER:
            by_el[ln["element_id"]] = ln
    return d, by_el


def build():
    faces = _rows(T312 / "FACE_LEDGER_T312.csv")
    ops = _rows(T312 / "OPENINGS_T312.csv")
    closure = {r["room"]: r for r in _rows(T312 / "ROOM_CLOSURE_T312.csv")}
    tile_lines = _rows(T312 / "LINE_SUMMARY_T312.csv")
    recon = {r["room"]: r for r in _rows(T312 / "RECONCILIATION_T312.csv")}
    cand, by_el = candidate_plaster()

    ops_of_face = {}
    for o in ops:
        ops_of_face.setdefault(o["face_id"], []).append(o)

    room_engine = {}
    for f in faces:
        if f["engine_room"]:
            room_engine[f["room"]] = f["engine_room"].split(" ")[0]

    # R-T329-4: each room's own FIN.PLASTER line (the wet rooms' 'room:plaster' record; the pantry's room-face record)
    plaster_line = {}
    for room, er in room_engine.items():
        el = PANTRY_LINE_ELEMENT if room == PANTRY_ROOM else f"{er}:plaster"
        plaster_line[room] = [by_el[el]["line_id"]] if el in by_el else []

    face_rows, per_room = [], {}
    for f in faces:
        room = f["room"]
        tile_scope = f["scope"]
        piece = "OPEN" if tile_scope == R.OPEN_EDGE else "WALL"
        has = R.backing_scope(tile_scope, piece)
        R.check_scope({"face_id": f["face_id"], "tile_scope": tile_scope, "piece": piece, "backing": has})
        rr = per_room.setdefault(room, {"faces": 0, "open_m": 0.0, "backing": [], "tile": [], "band": [],
                                        "dwg_band_hi": 0.0, "len": 0.0, "status": set(), "held": set(),
                                        "floor": f["floor"], "class": f["room_class"]})
        if not has:
            rr["open_m"] += float(f["length_m"])
            face_rows.append({"face_id": f["face_id"], "floor": f["floor"], "room": room, "room_class": f["room_class"],
                              "piece": f["piece"], "length_m": f["length_m"], "tile_scope": tile_scope,
                              "backing": "NO (open side: no wall)", "openings": "", "tile_top_m": "",
                              "owner_plaster_top_m": "", "backing_owner_m2": "", "band_owner_m2": "",
                              "tile_owner_m2": "", "closure_m2": "", "owner_status": "", "held_item": "",
                              "dwg_backing_status": "", "dwg_band_m2": "", "dwg_held_item": "",
                              "plaster_line_id": "", "tile_line_id": "", "mortar_m3_info": ""})
            continue
        L = float(f["length_m"])
        held_room = (f["owner_status"] or "").startswith("HELD") or not (f["owner_net_m2"] or "").strip()
        Hval = None if held_room else _f(f["owner_h_m"])
        tile_h = {"value_m": Hval, "source": f["owner_h_source"] or "HELD"}
        plaster_h = {"value_m": Hval, "source": OWNER_PLASTER_SRC} if Hval is not None else None
        fops = ops_of_face.get(f["face_id"], [])
        spaced = any(" " in o["opening_id"] for o in fops)       # one T-128 doorway id carries spaces
        ids_face = [f["openings"]] if spaced else [x for x in (f["openings"] or "").split() if x]
        R.check_same_openings([o["opening_id"] for o in fops], ids_face)   # R-T329-3: the tile ledger's ids
        res = R.face_backing(L, tile_h, plaster_h, [parse_size(o["kind"], o["merged_size"]) | {"id": o["opening_id"]}
                                                    for o in fops],
                             correction=f["piece"] == "WALK CLASS RESIDUAL" and L < 0)
        tile_m2 = _f(f["owner_net_m2"]) if not held_room else None
        back = res["backing"] if not held_room else None
        band = res["band"] if not held_room else None
        clos = R.closure_to_tile(back, tile_m2)
        status = R.COAT["status"] if back is not None else "HELD"
        held = "" if back is not None else (f["owner_held_item"] or "; ".join(res["held"]) or "HELD")
        line = R.bind({"face_id": f["face_id"], "room": room}, plaster_line)
        tline = next((t["line_id"] for t in tile_lines if t["rooms"] == room), R.NO_LINE)
        dwg_hi = round(L * DECOR_M, 4)
        rr["faces"] += 1
        rr["len"] += L
        rr["backing"].append(back)
        rr["tile"].append(tile_m2)
        rr["band"].append(band)
        rr["dwg_band_hi"] += dwg_hi
        rr["status"].add(status)
        if held:
            rr["held"].add(held)
        face_rows.append({
            "face_id": f["face_id"], "floor": f["floor"], "room": room, "room_class": f["room_class"],
            "piece": f["piece"], "length_m": f["length_m"], "tile_scope": tile_scope,
            "backing": "YES (UP-FIN-PAINT-001 substrate; Q-45 B 0.02 m 1:4)", "openings": " ".join(o["opening_id"]
                                                                                              for o in fops),
            "tile_top_m": f"{Hval:.2f}" if Hval is not None else "HELD",
            "owner_plaster_top_m": f"{Hval:.2f}" if Hval is not None else "HELD",
            "backing_owner_m2": f"{back:.4f}" if back is not None else "",
            "band_owner_m2": f"{band:.4f}" if band is not None else "",
            "tile_owner_m2": f"{tile_m2:.4f}" if tile_m2 is not None else "",
            "closure_m2": f"{clos:.4f}" if clos is not None else "",
            "owner_status": status, "held_item": held,
            "dwg_backing_status": "HELD (= the tile face, T-312 drawing columns)",
            "dwg_band_m2": (f"0 .. {dwg_hi:.4f} (HELD)" if L > 0 else
                            f"{dwg_hi:.4f} (named correction piece of the room outline, HELD)"),
            "dwg_held_item": f["dwg_held_item"] + " | band: specification of plaster above the decor ceiling not printed (Q-52)",
            "plaster_line_id": line, "tile_line_id": tline,
            "mortar_m3_info": f"{R.mortar_m3(back):.4f}" if back is not None else "",
        })

    room_rows = []
    for room in sorted(per_room):
        rr = per_room[room]
        b_tot, b_held = R.total(rr["backing"])
        t_tot, _ = R.total(rr["tile"])
        band_tot, _ = R.total(rr["band"])
        held_room = b_held > 0
        clos = R.closure_to_tile(None if held_room else b_tot, None if held_room else t_tot)
        cl = closure[room]
        cont = float(cl["contour_m"])
        res_m = round(cont - rr["len"] - rr["open_m"], 4) + 0.0     # no "-0.0000"
        if abs(res_m) > 0.002 * max(1, rr["faces"]):
            raise R.BackingError(f"CLOSURE: {room} faces {rr['len']:.4f} + open {rr['open_m']:.4f} vs {cont:.4f}")
        line = (plaster_line.get(room) or [R.NO_LINE])[0]
        room_rows.append({
            "room": room, "floor": rr["floor"], "room_class": rr["class"], "backing_faces": rr["faces"],
            "contour_m": f"{cont:.4f}", "backing_len_m": f"{rr['len']:.4f}", "open_m": f"{rr['open_m']:.4f}",
            "contour_residual_m": f"{res_m:.4f}",
            "backing_owner_m2": "" if held_room else f"{b_tot:.4f}",
            "tile_owner_m2": "" if held_room else f"{t_tot:.4f}",
            "closure_to_tile_m2": "" if clos is None else f"{clos:.4f}",
            "band_owner_m2": "" if held_room else f"{band_tot:.4f}",
            "dwg_band_m2": f"0 .. {rr['dwg_band_hi']:.4f} (HELD)",
            "status": "HELD" if held_room else R.COAT["status"],
            "held_item": "; ".join(sorted(rr["held"])),
            "mortar_m3_info": "" if held_room else f"{R.mortar_m3(b_tot):.4f}",
            "plaster_line_id": line, "engine_room": room_engine.get(room, ""),
        })

    # line map: every wet-room FIN.PLASTER room line + the pantry's two plaster lines
    rooms_by_line = {r["plaster_line_id"]: r for r in room_rows}
    line_rows = []
    wet_engine = {t["engine_room"].split(" ")[0] for t in tile_lines if t["line_id"] != R.NO_LINE}
    pantry_er = room_engine[PANTRY_ROOM]
    for el, ln in sorted(by_el.items(), key=lambda kv: (kv[1]["floor"], kv[1]["room_id"], kv[0])):
        if ln["room_id"] not in wet_engine | {pantry_er}:
            continue
        if "jamb" in (ln.get("physical_element") or ""):
            continue
        r = rooms_by_line.get(ln["line_id"])
        if r is not None and r["status"] != "HELD":
            prop, val, why = "FILL", r["backing_owner_m2"], (
                f"backing under the wall tile of {r['room']} = its tile faces ({r['backing_faces']} faces, closure to "
                f"tile {r['closure_to_tile_m2']} m2), band above the tile 0.0000 (Q-43 = Q-48 A); ASSUMED — "
                f"OWNER-APPROVED (UP-FIN-PAINT-001 substrate, Q-45 B coat PROVISIONAL)")
        elif r is not None:
            prop, val, why = "HELD by name", "", f"{r['room']}: {r['held_item']} (same item as its wall tile; never 0)"
        else:
            prop, val, why = ("NOT_APPLICABLE_WITH_EVIDENCE (kept)", "",
                              f"room record superseded by the room-face line {PANTRY_LINE_ELEMENT} (T-211 SUPERSEDE: "
                              f"one owner per face); the pantry backing is booked there once")
        line_rows.append({"line_id": ln["line_id"], "floor": ln["floor"], "engine_room": ln["room_id"],
                          "element_id": el, "room": r["room"] if r else PANTRY_ROOM,
                          "candidate_state": ln["evidence_state"],
                          "candidate_qty": "blank" if ln["measured_net"] is None else ln["measured_net"],
                          "proposal": prop, "proposed_m2": val, "basis": why})

    rec_rows = []
    for room in sorted(per_room):
        r = next(x for x in room_rows if x["room"] == room)
        fl = recon.get(room, {})
        flm = _f(fl.get("fl_m2"))
        own = _f(r["backing_owner_m2"])
        if own is not None and flm is not None:
            d = own - flm
            rec_rows.append({"room": room, "his_wet_wall_m2": f"{flm:.2f}", "own_backing_m2": f"{own:.4f}",
                             "diff_m2": f"{d:+.4f}", "diff_pct": f"{100 * d / flm:+.2f}",
                             "length_m2": fl["length_m2"], "height_m2": fl["height_m2"], "doors_m2": fl["doors_m2"],
                             "windows_m2": fl["windows_m2"], "residual_m2": fl["residual_m2"],
                             "verdict": "height RULE_DIFFERENCE (Q-43 / Q-48 A vs his flat 3.00); openings "
                                        "ENGINE_RIGHT (the coat stops at the hole, he deducts none); length per T-312; "
                                        "element: his row is a spatter-dash coat (separate item, URBAN-FINISH-EXTRAS-"
                                        "SEPARATE-ITEMS@v1), compared by AREA only"})
        else:
            rec_rows.append({"room": room, "his_wet_wall_m2": "" if flm is None else f"{flm:.2f}",
                             "own_backing_m2": r["backing_owner_m2"], "diff_m2": "", "diff_pct": "",
                             "length_m2": "", "height_m2": "", "doors_m2": "", "windows_m2": "", "residual_m2": "",
                             "verdict": ("SCOPE: he has no pantry row; ours = the tiled host walls (T-312)"
                                         if room == PANTRY_ROOM else f"not compared: our room HELD ({r['held_item']})")})

    det_rooms = [r for r in room_rows if r["status"] != "HELD"]
    in_lines = sum(float(r["backing_owner_m2"]) for r in det_rooms if r["room"] != PANTRY_ROOM)
    pantry = next(r for r in room_rows if r["room"] == PANTRY_ROOM)
    cmp = [x for x in rec_rows if x["diff_m2"]]
    fl_sum = sum(float(x["his_wet_wall_m2"]) for x in cmp)
    own_sum = sum(float(x["own_backing_m2"]) for x in cmp)
    summary = {
        "rule": R.RULE_ID, "coat": R.COAT,
        "inputs": {"t312_face_ledger": "FACE_LEDGER_T312.csv (MERGED 8943b5ed)",
                   "candidate": {"file": "agents_t311/CANDIDATE_V3019_T311.json", "json_sha256_8":
                                 cand["lines_json_sha256_8"], "lines_total": cand["lines_total"]}},
        "faces": {"backing": sum(1 for x in face_rows if x["backing"].startswith("YES")),
                  "open_sides": sum(1 for x in face_rows if x["backing"].startswith("NO"))},
        "rooms": len(room_rows),
        "owner_method": {"determinate_rooms": len(det_rooms),
                         "backing_m2": round(sum(float(r["backing_owner_m2"]) for r in det_rooms), 4),
                         "in_wet_lines_m2": round(in_lines, 4), "pantry_m2": float(pantry["backing_owner_m2"]),
                         "band_above_tile_m2": round(sum(float(r["band_owner_m2"]) for r in det_rooms), 4),
                         "held_rooms": [r["room"] for r in room_rows if r["status"] == "HELD"],
                         "closure_to_tile_max_abs_m2": max(abs(float(r["closure_to_tile_m2"])) for r in det_rooms),
                         "mortar_m3_info": round(sum(float(r["mortar_m3_info"]) for r in det_rooms), 4)},
        "drawing_method": {"backing": "HELD (= the tile faces; roof datum DCR-6, sunken panels, build-up b)",
                           "band_above_tile_hi_m2": round(sum(float(r["dwg_band_m2"].split(" .. ")[1].split(" ")[0])
                                                              for r in room_rows), 4),
                           "band_status": "HELD: " + DWG_BAND_HELD},
        "lines": {"mapped": len(line_rows),
                  "fill": sum(1 for x in line_rows if x["proposal"] == "FILL"),
                  "held": sum(1 for x in line_rows if x["proposal"].startswith("HELD")),
                  "not_applicable": sum(1 for x in line_rows if x["proposal"].startswith("NOT_APPLICABLE"))},
        "freelancer": {"rooms": len(cmp), "his_m2": round(fl_sum, 2), "own_m2": round(own_sum, 4),
                       "diff_m2": round(own_sum - fl_sum, 4), "diff_pct": round(100 * (own_sum - fl_sum) / fl_sum, 2)},
    }
    return face_rows, room_rows, line_rows, rec_rows, summary


def _csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def render():
    f, r, ln, rec, s = build()
    return {OUT["faces"]: _csv(f), OUT["rooms"]: _csv(r), OUT["lines"]: _csv(ln), OUT["recon"]: _csv(rec),
            OUT["summary"]: json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True) + "\n"}


def main(argv):
    out = render()
    if "--write" in argv:
        for p, s in out.items():
            p.write_text(s, encoding="utf-8")
        print("written", len(out))
        return 0
    bad = [p.name for p, s in out.items() if not p.exists() or p.read_text(encoding="utf-8") != s]
    print("check:", "OK" if not bad else f"DIFFERS {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
