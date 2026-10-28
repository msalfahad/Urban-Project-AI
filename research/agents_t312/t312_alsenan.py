"""T-312 (development villa): the WALL TILE FACE-TO-LINE LEDGER on the candidate of record ARCH_TAKEOFF_V3.0.19.
Research only: no engine module, rule / knowledge file, candidate line or released line changes.

    python3 -I research/agents_t312/t312_alsenan.py --geometry <P7757.dxf>     # pantry installation hosts (lengths only)
    python3 -I research/agents_t312/t312_alsenan.py --extract <run>/t255/v3019 # the candidate's wall-tile lines
    python3 -I research/agents_t312/t312_alsenan.py --write                    # the ledger files
    python3 -I research/agents_t312/t312_alsenan.py --check                    # rebuild byte for byte

Inputs (all merged, cited, none re-derived): T-292 FACE_TO_LINE_LEDGER_T292.csv (FIN.WALL.TILE rows: the drawn faces of
every wet room by T-250, owner heights G1 / Q-48 A, owner nets, drawing-derived statuses), OPENING_DEDUCTIONS_T292.csv
(each opening once per room side, merged sizes T-237 part 4), T-209 ALSENAN_T209_INPUT.json (room contours T-074 /
T-128 r3, open sides, freelancer lm) and WET_WALL_TILES_T209.csv (freelancer m2 per room). New here: the pantry host
walls read on P7757.dxf (UP-PANTRY-003) and the binding to the V3.0.19 line ids. Drive 'Alsenan chalet project' files
are read in the private folder only; this file and its outputs hold handles, lengths and areas, no coordinates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import t312_wall_tile_rules as R  # noqa: E402

T292 = ROOT / "research" / "agents_t292"
T209 = ROOT / "research" / "agents_t209"
CAND = HERE / "CANDIDATE_V3019_WALL_TILE_LINES.json"
HOSTS = HERE / "PANTRY_HOSTS_T312.json"
OUT = {
    "faces": HERE / "FACE_LEDGER_T312.csv",
    "rooms": HERE / "ROOM_CLOSURE_T312.csv",
    "lines": HERE / "LINE_SUMMARY_T312.csv",
    "openings": HERE / "OPENINGS_T312.csv",
    "recon": HERE / "RECONCILIATION_T312.csv",
    "summary": HERE / "summary.json",
}
PANTRY = "GF-07"
PANTRY_WALL_FACES = ("GF-07|GF-W16", "GF-07|GF-W01", "GF-07|GF-W05", "GF-07|OFF:COLUMN")
DRAWINGS = "Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55), 'ST7757 dxf.dxf' (9f9d1179)"


def f_(x):
    try:
        return None if x in (None, "") else float(x)
    except ValueError:
        return None


def read(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------------------------------------ --geometry
# P7757.dxf handles (pantry box: T-286 s.2; counters: layer 5 outlines). Box relative frame: x east from the west wall
# face AE, y north from the south wall face A6.
H = {"west_face": "AE", "south_face": "A6", "north_face_w": "158", "north_face_e": "159", "open_edge": ("B3", "AD"),
     "column_nw": "2FAE", "west_counter": ("335", "B1", "15C", "33F"), "east_counter": ("B2", "AA", "B4", "15D"),
     "room_label": "178"}


def geometry(dxf_path):
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(dxf_path)
    db = doc.entitydb
    S = 1000.0  # drawing unit mm

    def seg(h):
        e = db[h]
        return ((e.dxf.start.x / S, e.dxf.start.y / S), (e.dxf.end.x / S, e.dxf.end.y / S))

    x0 = seg("AE")[0][0]
    y0 = seg("A6")[0][1]
    rel = lambda p: (round(p[0] - x0, 4), round(p[1] - y0, 4))  # noqa: E731
    east = rel(seg("B3")[0])[0]
    north = rel(seg("158")[0])[1]
    col = bbox.extents([db["2FAE"]])
    col_s = round(col.extmin.y / S - y0, 4)
    col_e = round(col.extmax.x / S - x0, 4)
    # counter outlines (layer 5): west L = 335 (south end) / B1 (front of the west leg) / 15C (front of the north leg)
    # / 33F (east end of the north leg); east L = B2 (west end) / AA (front of the south leg) / B4 (front of the east
    # leg) / 15D (north end)
    w_s = rel(seg("335")[0])[1]
    w_front = rel(seg("B1")[0])[0]
    n_front = rel(seg("15C")[0])[1]
    n_end = rel(seg("33F")[0])[0]
    e_w = rel(seg("B2")[0])[0]
    e_front_s = rel(seg("AA")[0])[1]
    e_front_e = rel(seg("B4")[0])[0]
    e_n = max(rel(seg("15D")[0])[1], rel(seg("15D")[1])[1])
    assert all(db[h].dxf.layer == "5" for h in H["west_counter"] + H["east_counter"])
    runs = {
        "west_counter.west_leg": dict(back=[(0.0, w_s), (0.0, col_s)], depth=round(w_front - 0.0, 4),
                                      handles="335 / B1 (front) / AE + AF + window W09 face"),
        "west_counter.north_leg": dict(back=[(0.0, col_s), (col_e, col_s), (col_e, north), (n_end, north)],
                                       depth=round(col_s - n_front, 4),
                                       handles="15C (front) / 33F (end) / column 2FAE face + 158"),
        "east_counter.south_leg": dict(back=[(e_w, 0.0), (east, 0.0)], depth=round(e_front_s, 4),
                                       handles="B2 (end) / AA (front) / A6"),
        "east_counter.east_leg": dict(back=[(east, 0.0), (east, e_n)], depth=round(east - e_front_e, 4),
                                      handles="B4 (front) / 15D (end) / B3 (open edge)"),
    }
    backs = []
    for k, r in runs.items():
        pts = r["back"]
        for a, b in zip(pts, pts[1:]):
            backs.append((k, [a, b]))
    faces = {   # the T-292 face ids of GF-07 with the drawn face line(s) they stand for
        "GF-07|GF-W16": [[(0.0, 0.0), (0.0, col_s)]],                          # west wall (W10, W09 in it)
        "GF-07|GF-W01": [[(0.0, 0.0), (east, 0.0)]],                           # south wall A6
        "GF-07|GF-W05": [[(col_e, north), (east, north)]],                      # north wall 158 + door D120 + 159
        "GF-07|OFF:COLUMN": [[(0.0, col_s), (col_e, col_s)]],                  # column 2FAE south face
        "OPEN|B3": [[(east, 0.0), (east, north)]],                              # the open edge to the dining
    }
    out = {}
    for fid, segs in faces.items():
        tot = 0.0
        by = {}
        for s in segs:
            for k, b in backs:
                m = R.host_overlap_m(s, [b])
                if m > 1e-9:
                    by[k] = round(by.get(k, 0.0) + m, 4)
                    tot += m
        out[fid] = dict(host_m=round(tot, 4), by_run=by,
                        face_line_m=round(sum(((s[1][0] - s[0][0]) ** 2 + (s[1][1] - s[0][1]) ** 2) ** 0.5
                                              for s in segs), 4))
    doc_out = {
        "about": "T-312 pantry installation hosts (UP-PANTRY-003) read on " + DRAWINGS + ". Lengths in m only; "
                 "no coordinate. A run's BACK is the edge it is fixed along; its END against a side wall hosts nothing.",
        "dxf_sha256_8": hashlib.sha256(Path(dxf_path).read_bytes()).hexdigest()[:8],
        "box_m": [round(east, 4), round(north, 4)],
        "column_2FAE_notch_m": [round(col_e, 4), round(north - col_s, 4)],
        "runs": {k: dict(depth_m=r["depth"], back_m=round(sum(((b[1][0] - b[0][0]) ** 2 + (b[1][1] - b[0][1]) ** 2)
                                                                ** 0.5 for b in zip(r["back"], r["back"][1:])), 4),
                         handles=r["handles"]) for k, r in runs.items()},
        "faces": out,
        "label": "INSERT 178 block PAN (room label PANTRY); no sink block in the pantry on P7757.dxf; floor drain on "
                 "sanitary-7757.pdf (Q-37 problem text)",
    }
    HOSTS.write_text(json.dumps(doc_out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc_out


# ------------------------------------------------------------------------------------------------ --extract
def extract(run_dir):
    run_dir = Path(run_dir)
    p = run_dir / "V3_0_19_BOQ_LINES.csv"
    rows = read(p)
    keep = []
    for r in rows:
        el = (r.get("physical_element") or "").lower()
        if r["item_code"] == R.TILE or (r["item_code"] == "FIN.PAINT" and "wall tile" in el) or \
                r.get("room_id") == "GF-RC06FED":
            keep.append({k: r.get(k, "") for k in ("line_id", "item_code", "floor", "room_id", "physical_element", "unit",
                                                   "gross", "measured_net", "bounded_low", "bounded_high",
                                                   "evidence_state", "approval_state")}
                        | {"rfi": (r.get("rfi") or "")[:160]})
    js = run_dir / "V3_0_19_BOQ_LINES.json"
    doc = {"source": "own V3.0.19 run (research/agents_t167/v304_run.py then research/agents_t255/v3019_run.py) on "
                     + DRAWINGS,
           "csv_sha256_8": hashlib.sha256(p.read_bytes()).hexdigest()[:8],
           "json_sha256_8": hashlib.sha256(js.read_bytes()).hexdigest()[:8] if js.exists() else None,
           "lines_total": len(rows), "lines": keep}
    CAND.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


# ------------------------------------------------------------------------------------------------ ledger
def _parse_size(s):
    """'w 0.6 sill 1.7 head 2.5' -> dict; 'h HELD' parts -> None."""
    out = {}
    t = (s or "").split()
    for i, k in enumerate(t):
        if k in ("w", "sill", "head") and i + 1 < len(t):
            out[k] = f_(t[i + 1])
    return out


def build():
    t209 = json.loads((T209 / "ALSENAN_T209_INPUT.json").read_text(encoding="utf-8"))
    rooms209 = {r["id"]: r for r in t209["rooms"]}
    fl209 = {r["ROOM"]: r for r in read(T209 / "WET_WALL_TILES_T209.csv")}
    faces292 = [r for r in read(T292 / "FACE_TO_LINE_LEDGER_T292.csv") if r["item_code"] == R.TILE]
    ded292 = read(T292 / "OPENING_DEDUCTIONS_T292.csv")
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    hosts = json.loads(HOSTS.read_text(encoding="utf-8"))
    tile_lines = [ln for ln in cand["lines"] if ln["item_code"] == R.TILE]
    line_of_eroom = {}
    for ln in tile_lines:
        line_of_eroom.setdefault(ln["room_id"], []).append(ln["line_id"])
    by_id = {ln["line_id"]: ln for ln in cand["lines"]}

    wet_rooms = sorted({f["room"] for f in faces292})
    assert set(wet_rooms) == set(rooms209), "the T-292 wet set must be the T-209 set (18 rooms)"

    # ---- openings: each once per room side, band part re-derived under R-T312-3
    op_rows = []
    ded_by_face = {}
    for d in ded292:
        if d["room"] not in rooms209:
            continue
        H = None
        face = next((f for f in faces292 if f["face_id"] == d["face_id"]), None)
        assert face is not None, d["face_id"]
        H = f_(face["owner_h_m"])
        size = _parse_size(d["merged_size"])
        kind = "door" if d["kind"] in ("door",) else ("window" if d["kind"] == "window" else d["kind"])
        op = dict(id=d["opening_id"], kind="door" if kind == "door" else "window", w=size.get("w"),
                  sill=size.get("sill"), head=size.get("head"))
        claimed = f_(d["owner_ded_new_m2"])
        band = None
        state = "HELD"
        if H is not None and kind in ("door", "window") and op["head"] is not None and \
                (kind == "door" or op["sill"] is not None):
            band = R.opening_band(op, H)
            R.check_claimed_deduction(op, H, claimed)
            state = "DETERMINATE" if face["owner_status"] != "HELD" else "HELD (room height: " + \
                face["owner_held_item"][:40] + ")"
            ded_by_face[d["face_id"]] = ded_by_face.get(d["face_id"], 0.0) + band
        top_rel = None if (H is None or op.get("sill") is None or kind == "door") else round(op["sill"] - H, 4)
        op_rows.append(dict(room=d["room"], opening_id=d["opening_id"], kind=d["kind"], face_id=d["face_id"],
                            merged_size=d["merged_size"], merged_source=d["merged_source"],
                            tile_top_m="" if H is None else f"{H:.2f}",
                            band_m2="" if band is None else f"{band:.4f}",
                            t292_owner_ded_m2=d["owner_ded_new_m2"], state=state,
                            sill_minus_tile_top_m="" if top_rel is None else f"{top_rel:.4f}",
                            rule="R-T312-3: part inside [0, tile top]; " + (
                                "door w x min(head, H)" if kind == "door" else
                                "window w x (min(head, H) - max(sill, 0))" if kind == "window" else
                                "head not printed: HELD range (T-209)")))
    R.check_openings_once([(o["room"], o["opening_id"]) for o in op_rows])

    # ---- faces
    rows = []
    for f in faces292:
        room = f["room"]
        r209 = rooms209[room]
        is_pantry = room == PANTRY
        cls = R.pantry_class(r209["open_m"]) if is_pantry else R.WET
        host = None
        if is_pantry and f["face_id"] in PANTRY_WALL_FACES:
            host = hosts["faces"][f["face_id"]]["host_m"]
            sc, why = R.face_scope(cls, "WALL", host)
        elif is_pantry:
            # a T-250 off-line / walk-class piece on the pantry perimeter, not tied to one wall: tiled only when EVERY
            # drawn pantry wall hosts a run (then any wall piece of the perimeter lies on a host wall)
            ah = min(hosts["faces"][k]["host_m"] for k in PANTRY_WALL_FACES)
            if ah >= R.HOST_MIN_M:
                host = ah
                sc, why = R.TILED, ("UP-PANTRY-003 FULL_WALL: a perimeter wall piece (T-250 " + f["piece"].lower() +
                                    "); every drawn pantry wall hosts a counter run (min " + f"{ah:.3f}" + " m)")
            else:
                sc, why = R.UNRESOLVED, "UP-PANTRY-003: piece not tied to one wall and not every wall hosts"
        else:
            sc, why = R.face_scope(cls, "WALL")
        L = f_(f["length_m"])
        Hh = f_(f["owner_h_m"])
        hrec = {"value_m": Hh, "source": f["owner_source"] or f["owner_status"]}
        prov = None
        if Hh is not None and f["owner_status"] != "HELD":
            R.check_height(hrec)
            gross = L * Hh
            net = round(gross - ded_by_face.get(f["face_id"], 0.0), 4)
            t292net = f_(f["owner_net_lo_m2"])
            assert abs(net - t292net) <= 1e-4, (f["face_id"], net, t292net)
        else:
            # HELD: the owner height is not established for this room (annex G2 / Q-54 B, or the room level T-088);
            # the annex owner-manual 3.15 figure is shown as information only, never as the quantity
            R.check_height({"value_m": None, "source": f["owner_held_item"]})
            net = None
            if Hh is not None:
                prov = round(L * Hh - ded_by_face.get(f["face_id"], 0.0), 4)
        eroom = f["engine_rooms"]
        ls = line_of_eroom.get(eroom, [])
        if sc == R.TILED:
            if len(ls) > 1:
                raise R.TileError(f"FACE_TWICE: {f['face_id']} in {ls}")
            line = ls[0] if ls else R.NO_LINE
        else:
            line = ""
        rows.append(dict(face_id=f["face_id"], floor=f["floor"], room=room, room_class=cls, piece=f["piece"],
                         wall_id=f["wall_id"], length_m=f"{L:.4f}", length_source=f["length_basis"],
                         scope=sc, scope_rule=why, host_m="" if host is None else f"{host:.4f}",
                         openings=f["openings"], owner_h_m=f["owner_h_m"], owner_h_source=f["owner_source"],
                         owner_status=f["owner_status"] if net is not None else "HELD",
                         owner_net_m2="" if net is None else f"{net:.4f}",
                         owner_held_item=f["owner_held_item"],
                         info_owner_manual_provisional_m2="" if prov is None else f"{prov:.4f}", dwg_status=f["dwg_status"],
                         dwg_held_item=f["dwg_held_item"], engine_room=eroom, line_id=line,
                         line_state=by_id[line]["evidence_state"] if line in by_id else ""))
    # open edges (no wall: nothing tiled; UP-PANTRY-002 / open side)
    for room in wet_rooms:
        om = rooms209[room]["open_m"]
        if om and om > 0:
            rows.append(dict(face_id=f"{room}|OPEN", floor=room[:2], room=room,
                             room_class=R.pantry_class(om) if room == PANTRY else R.WET, piece="OPEN EDGE",
                             wall_id="", length_m=f"{om:.4f}", length_source="T-209 / T-128 r3 open side (no wall drawn)",
                             scope=R.OPEN_EDGE, scope_rule=("UP-PANTRY-002: open edge to the dining tiles nothing"
                                                            if room == PANTRY else
                                                            "open side to the stair hall: no wall, nothing to tile"),
                             host_m="", openings="", owner_h_m="", owner_h_source="", owner_status="",
                             owner_net_m2="", owner_held_item="", info_owner_manual_provisional_m2="", dwg_status="", dwg_held_item="",
                             engine_room="", line_id="", line_state=""))
    for r in rows:
        R.check_scope(dict(r, piece="OPEN" if r["scope"] == R.OPEN_EDGE else "WALL",
                           host_m=f_(r["host_m"]) if r["host_m"] != "" else None))
    R.check_line_claims([(r["line_id"], r["face_id"]) for r in rows if r["scope"] == R.TILED])

    # ---- room closure: faces (tiled + not tiled) + open edges = the walked contour (T-074 / T-128 r3)
    room_rows = []
    for room in wet_rooms:
        rr = [r for r in rows if r["room"] == room]
        pieces = [float(r["length_m"]) for r in rr]
        res = R.room_closure(pieces, rooms209[room]["contour_m"])
        tiled = [r for r in rr if r["scope"] == R.TILED]
        nets = [f_(r["owner_net_m2"]) for r in tiled]
        held = any(n is None for n in nets)
        room_rows.append(dict(room=room, contour_m=f"{rooms209[room]['contour_m']:.4f}", pieces=len(rr),
                              tiled_m=f"{sum(float(r['length_m']) for r in tiled):.4f}",
                              not_tiled_m=f"{sum(float(r['length_m']) for r in rr if r['scope'] == R.NOT_TILED):.4f}",
                              open_m=f"{sum(float(r['length_m']) for r in rr if r['scope'] == R.OPEN_EDGE):.4f}",
                              residual_m=f"{res + 0.0:.4f}".replace("-0.0000", "0.0000"),
                              owner_net_m2="" if held else f"{sum(nets):.4f}",
                              status="HELD" if held else tiled[0]["owner_status"],
                              held_item=tiled[0]["owner_held_item"] if held else "",
                              line_id=tiled[0]["line_id"]))

    # ---- lines: every FIN.WALL.TILE line of the candidate once, plus NO_LINE
    line_rows = []
    for ln in tile_lines:
        rr = [r for r in rows if r["line_id"] == ln["line_id"]]
        rooms_ = sorted({r["room"] for r in rr})
        nets = [f_(r["owner_net_m2"]) for r in rr]
        held = (not rr) or any(n is None for n in nets)
        line_rows.append(dict(line_id=ln["line_id"], floor=ln["floor"], engine_room=ln["room_id"],
                              rooms=" ".join(rooms_), faces=len(rr), candidate_state=ln["evidence_state"],
                              candidate_qty=ln["measured_net"] or (f"{ln['bounded_low']} .. {ln['bounded_high']}"
                                                                   if ln["bounded_low"] else "blank"),
                              ledger_owner_m2="" if held else f"{sum(nets):.4f}",
                              ledger_status="HELD" if held else rr[0]["owner_status"],
                              held_item=(rr[0]["owner_held_item"] if rr else "no face") if held else ""))
    nl = [r for r in rows if r["line_id"] == R.NO_LINE]
    line_rows.append(dict(line_id=R.NO_LINE, floor="GF", engine_room="GF-RC06FED (pantry: no FIN.WALL.TILE line)",
                          rooms=" ".join(sorted({r["room"] for r in nl})), faces=len(nl), candidate_state="MISSING",
                          candidate_qty="blank",
                          ledger_owner_m2=f"{sum(f_(r['owner_net_m2']) for r in nl):.4f}",
                          ledger_status=nl[0]["owner_status"] if nl else "", held_item=""))

    # ---- freelancer (his wet-wall rows = his lm x 3.00, no opening deducted; T-209 / T-010 / T-086)
    rec = []
    for rr in room_rows:
        room = rr["room"]
        fl = f_(fl209[room]["FL_M2"]) if room in fl209 else None
        own = f_(rr["owner_net_m2"])
        r209 = rooms209[room]
        if fl is None or own is None:
            rec.append(dict(room=room, fl_m2="" if fl is None else f"{fl:.2f}", own_m2="" if own is None else
                            f"{own:.4f}", length_m2="", height_m2="", doors_m2="", windows_m2="", residual_m2="",
                            verdict=("not compared: our room HELD (" + rr["held_item"][:60] + ")") if own is None else
                            "SCOPE: he has no pantry row; our pantry tile = UP-PANTRY-003 host walls (all three "
                            "walls host a counter run), Q-37 A wet"))
            continue
        face = sum(float(r["length_m"]) for r in rows if r["room"] == room and r["scope"] == R.TILED)
        Hh = f_(next(r["owner_h_m"] for r in rows if r["room"] == room and r["scope"] == R.TILED))
        fl_lm = r209["fl_lm"]
        dl = (face - fl_lm) * 3.00
        dh = face * (Hh - 3.00)
        doors = -sum(f_(o["band_m2"]) for o in op_rows if o["room"] == room and o["kind"] == "door"
                     and o["band_m2"] != "")
        wins = -sum(f_(o["band_m2"]) for o in op_rows if o["room"] == room and o["kind"] == "window"
                    and o["band_m2"] != "")
        resid = own - (fl + dl + dh + doors + wins)
        assert abs(resid) < 2e-4, (room, resid)
        rec.append(dict(room=room, fl_m2=f"{fl:.2f}", own_m2=f"{own:.4f}", length_m2=f"{dl:.4f}",
                        height_m2=f"{dh:.4f}", doors_m2=f"{doors:.4f}", windows_m2=f"{wins:.4f}",
                        residual_m2=f"{resid:.4f}",
                        verdict="height RULE_DIFFERENCE (Q-48 A vs his flat 3.00); openings ENGINE_RIGHT (UP-CER-005 "
                                "/ Q-73 A, he deducts none); length ENGINE_RIGHT (drawn faces vs his rounded lm"
                                + (", open side not walled" if r209["open_m"] else "") + ")"))

    det_in = sum(f_(r["ledger_owner_m2"]) for r in line_rows if r["line_id"] != R.NO_LINE and r["ledger_owner_m2"])
    det_no = sum(f_(r["ledger_owner_m2"]) for r in line_rows if r["line_id"] == R.NO_LINE and r["ledger_owner_m2"])
    cmp_ = [r for r in rec if r["residual_m2"] != ""]
    summary = dict(
        rule=R.RULE_ID, candidate=dict(csv_sha256_8=cand["csv_sha256_8"], json_sha256_8=cand["json_sha256_8"],
                                       lines_total=cand["lines_total"], wall_tile_lines=len(tile_lines)),
        dxf_sha256_8=hosts["dxf_sha256_8"],
        rooms=len(wet_rooms), faces=sum(1 for r in rows if r["piece"] != "OPEN EDGE"),
        open_edges=sum(1 for r in rows if r["piece"] == "OPEN EDGE"),
        tiled_faces=sum(1 for r in rows if r["scope"] == R.TILED),
        not_tiled_faces=sum(1 for r in rows if r["scope"] == R.NOT_TILED),
        unresolved_faces=sum(1 for r in rows if r["scope"] == R.UNRESOLVED),
        closure_max_abs_residual_m=max(abs(f_(r["residual_m"])) for r in room_rows),
        owner_method=dict(in_line_m2=round(det_in, 4), no_line_m2=round(det_no, 4),
                          determinate_m2=round(det_in + det_no, 4),
                          held_rooms=sorted(r["room"] for r in room_rows if r["status"] == "HELD"),
                          determinate_rooms=sum(1 for r in room_rows if r["status"] != "HELD"),
                          status="ASSUMED — OWNER-APPROVED (G1 heights Q-43 / Q-48 A, door heads Q-55 C); faces "
                                 "DRAWING-CONFIRMED (T-250); windows DRAWING-CONFIRMED (T-201 / T-175)"),
        lines=dict(bound=sum(1 for r in line_rows if r["line_id"] != R.NO_LINE and r["faces"]),
                   determinate=sum(1 for r in line_rows if r["line_id"] != R.NO_LINE and r["ledger_owner_m2"]),
                   held=sum(1 for r in line_rows if r["line_id"] != R.NO_LINE and not r["ledger_owner_m2"]),
                   no_line_faces=len(nl)),
        freelancer=dict(compared_rooms=len(cmp_), fl_m2=round(sum(f_(r["fl_m2"]) for r in cmp_), 2),
                        own_m2=round(sum(f_(r["own_m2"]) for r in cmp_), 4),
                        length_m2=round(sum(f_(r["length_m2"]) for r in cmp_), 4),
                        height_m2=round(sum(f_(r["height_m2"]) for r in cmp_), 4),
                        doors_m2=round(sum(f_(r["doors_m2"]) for r in cmp_), 4),
                        windows_m2=round(sum(f_(r["windows_m2"]) for r in cmp_), 4),
                        residual_m2=round(sum(f_(r["residual_m2"]) for r in cmp_), 4),
                        fl_total_m2=t209["freelancer_total_m2"]),
        pantry=dict(hosts={k: v["host_m"] for k, v in hosts["faces"].items()}, runs=hosts["runs"]),
    )
    fr = summary["freelancer"]
    fr["diff_m2"] = round(fr["own_m2"] - fr["fl_m2"], 4)
    fr["diff_pct"] = round(100 * fr["diff_m2"] / fr["fl_m2"], 2)
    return rows, room_rows, line_rows, op_rows, rec, summary


def _csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def render():
    rows, room_rows, line_rows, op_rows, rec, summary = build()
    return {OUT["faces"]: _csv(rows), OUT["rooms"]: _csv(room_rows), OUT["lines"]: _csv(line_rows),
            OUT["openings"]: _csv(op_rows), OUT["recon"]: _csv(rec),
            OUT["summary"]: json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry")
    ap.add_argument("--extract")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.geometry:
        print(json.dumps(geometry(a.geometry)["faces"], indent=1, sort_keys=True))
    if a.extract:
        d = extract(a.extract)
        print("lines", d["lines_total"], "kept", len(d["lines"]), d["csv_sha256_8"], d["json_sha256_8"])
    if a.write:
        for p, s in render().items():
            p.write_text(s, encoding="utf-8")
        print(json.dumps(json.loads(OUT["summary"].read_text(encoding="utf-8")), indent=1, sort_keys=True))
    if a.check:
        bad = [p.name for p, s in render().items() if p.read_text(encoding="utf-8") != s]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
