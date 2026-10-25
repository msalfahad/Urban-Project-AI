"""T-292 development villa (Alsenan): the PLASTER / PAINT FACE-TO-LINE LEDGER (rule R-T292-1, t292_face_line_rules.py).

READ ONLY on merged research ledgers + the candidate's own lines (extracted from an own V3.0.15 run on the Drive copies):

  face lengths       research/agents_t250/FACE_LENGTH_T250.csv, ROOM_CLOSURE_T250.csv, ROOF_DATUM_T250.csv  (T-250)
  rooms / heights    research/agents_t128/ROOMS_T128_R3.csv, OPENINGS_T128_R3.csv                          (T-128 r3)
  merged openings    research/agents_t237 (load / merged_sizes / match: T-175 -> T-201 -> T-207 -> T-238)  (T-237)
  identity           research/agents_t262/ENGINE_ROOM_XWALK_T262.csv, T237_JOIN_CHECK_T262.csv             (T-262)
  candidate lines    research/agents_t292/CANDIDATE_V3015_WALL_FINISH_LINES.json  (--extract <v3015 run dir>)

Usage:
  python3 -I research/agents_t292/t292_alsenan.py --extract <run>/v3015   (writes the candidate json; ids, states,
                                                                            quantities only: no coordinate, no name)
  python3 -I research/agents_t292/t292_alsenan.py --write                  (writes the ledger CSVs + summary.json)
  python3 -I research/agents_t292/t292_alsenan.py --check                  (rebuilds in memory, compares byte for byte)
Nothing here changes a merged ledger, a candidate line or a released line: lane I (T-244) applies the ledger.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t237"))
import t292_face_line_rules as L      # noqa: E402
import alsenan_t237 as T237       # noqa: E402

CAND = HERE / "CANDIDATE_V3015_WALL_FINISH_LINES.json"
CODES = (L.PLASTER, L.PAINT, L.TILE, L.EXT)

# owner G1 heights (OWNER_RECONCILIATION_2026-10-20, Q-43 / Q-48 A): one height for plaster, paint and wet tile
G1 = "G1 (OWNER_RECONCILIATION_2026-10-20), Q-43 / Q-48 A; door head 2.20 Q-55 C where none is printed"
# Checker runs that verified a room's owner-method figure (T-211 inputs, the V3.0.9 Gate B record)
VERIFIED_BY = {"GF-15": "Verifier 2026-10-22 02:40 + 16:11 (own walk of the drawn faces, owner net 56.02)",
               "1F-11": "Verifier 2026-10-22 18:05 (own polygon, contour 22.1507 m, owner net 59.447)"}
# candidate room ids per T-128 row (T-211 ROUTE, own geometric check; T-262 ENGINE_ROOM_XWALK agrees for 1:1 rooms).
# GF-07 (pantry) lies in two candidate rooms; T-211 put its record on the first (GF-RC06FED), GF-08 on GF-RC99C2A.
ROUTE_T211 = {"GF-01": ["GF-R7512EA"], "GF-04": ["GF-R51E127"], "GF-08": ["GF-RC99C2A"], "GF-07": ["GF-RC06FED"],
              "GF-15": ["GF-R75FBAE"], "ST-GF": ["GF-R31F8AE"], "1F-01": ["1F-RB72F22"], "1F-04": ["1F-RED0D19"],
              "1F-10": ["1F-R0E919A"], "1F-11": ["1F-R3CFCFD"], "1F-13": ["1F-R78C367"], "ST-1F": ["1F-R78C367"],
              "2F-03": ["2F-R1DB2D2"], "2F-01": ["2F-R4D1B62"], "ST-2F": ["2F-R4D1B62"]}
# the two rooms whose ONE candidate room line holds two ledger rooms (T-211: the shaft part is its own record)
SHARED_ROOM = {"1F-R78C367": ("1F-13", "ST-1F"), "2F-R4D1B62": ("2F-01", "ST-2F")}
# W03 room-side vs window line (T-250 / T-286, Checker 6.7294): RULE_DIFFERENCE between trades, outside totals
W03_RULE_DIFF_M = 0.1616


def read(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f_(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------------------------------------- candidate lines
def extract(run_dir: Path):
    """the candidate's wall-finish lines (ids, item, floor, room, element, unit, state, quantities, rfi head)."""
    p = Path(run_dir) / "V3_0_15_BOQ_LINES.csv"
    rows = read(p)
    out = []
    for r in rows:
        if r["item_code"] not in CODES:
            continue
        out.append({k: r.get(k, "") for k in ("line_id", "item_code", "floor", "room_id", "physical_element", "unit",
                                               "gross", "measured_net", "bounded_low", "bounded_high",
                                               "evidence_state", "approval_state")}
                   | {"rfi": (r.get("rfi") or "")[:160]})
    import hashlib
    doc = {"source": "own V3.0.15 run (research/agents_t270/v3015_run.py) on Drive 'Alsenan chalet project' "
                     "P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55) and 'ST7757 dxf.dxf' (9f9d1179)",
           "csv_sha256_8": hashlib.sha256(p.read_bytes()).hexdigest()[:8], "lines_total": len(rows),
           "wall_finish_lines": out}
    CAND.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


def candidate():
    return json.loads(CAND.read_text(encoding="utf-8"))


def line_value(ln):
    """(state, lo, hi) of a candidate line: RELEASED / BOUNDED figure or None."""
    net, lo, hi = f_(ln["measured_net"]), f_(ln["bounded_low"]), f_(ln["bounded_high"])
    if net is not None:
        return ln["evidence_state"], net, net
    if lo is not None and hi is not None:
        return ln["evidence_state"], lo, hi
    return ln["evidence_state"], None, None


# ------------------------------------------------------------------------------------------------- openings
# r2 (Verifier F-T292-01, 2026-10-25): W17 under the ANSWERED Q-76 A (owner 2026-10-24 23:53): the opening crown is
# 3.00 above +5.50 (the 0.45 band above is wall). Q-76 A sets the WINDOW line (3.29 x 3.00 = 9.870 m2 of opening area);
# for plaster / paint the merged rule UP-OPEN-ARCH-001 v1.1 (T-238 arch_rules.check_masonry_deduction, A2) deducts the
# TRUE arched outline and refuses width x crown (RECTANGLE_FOR_MASONRY), and Q-76 itself says "blockwork, plaster and
# paint deduct the true arched hole whichever you choose". The developed outline on the curved glass line is not drawn
# (T-238 A5), so the deduction is bounded, not fixed, on the room-side length w (T-250 3.286):
#   upper  w x crown 3.000 (Q-76 A)                       = 9.858 m2 (the hole lies inside its enclosing rectangle)
#   lower  w x springing 1.350 (P7757.dxf NW frame, layer 1 opening jambs 2784 / 2565 from +5.50 to +6.85, where
#          the arch chain 2738 / 2741 starts)                = 4.4361 m2 (the full width is open at least to springing)
# INFORMATION, not a quantity: the elevation (projected) hole is 8.1338 m2 (jambs 3.0594 apart); stretched uniformly
# to the developed width it is 8.7362 m2; the projection-to-arc mapping needs the plan / elevation registration.
W17_SPRING_M, W17_CROWN_M = 1.350, 3.000
W17_Q76A_SRC = ("Q-76 A crown 3.00 (owner 2026-10-24 23:53) + UP-OPEN-ARCH-001 v1.1 true outline (T-238 A2 / A5): "
                "developed hole HELD between w x springing 1.350 (P7757.dxf NW 2784 / 2565) and w x crown 3.000")


R2_NAMED_T237_DIFF = {"1F-11": ("W17 only (r2, Q-76 A): T-237 part 4 holds the deduction 0 .. 10.024 (T-238 cap on the "
                                 "outer crown line 3.0505); the ledger holds 4.4361 .. 9.858 (springing 1.350 .. crown "
                                 "3.000 on w 3.286): lo +0.1660, hi -4.4361")}


def w17_q76a(w):
    return dict(w=w, sill=None, head=None, cap_m2=round(w * W17_CROWN_M, 4),
                ded_range_m2=(round(w * W17_SPRING_M, 4), round(w * W17_CROWN_M, 4)))


def openings():
    """per T-128 room: its opening deductions with the T-237 part-4 (merged) size and the T-128 r3 size, the census id
    corrected by geometry (T-262 JOIN_WRONG) and the host wall."""
    rooms, ops, hosts, _reg = T237.load()
    sizes = T237.merged_sizes(hosts)
    rows = T237.resolve_ambiguous(T237.match(ops, hosts), hosts)
    # T-262: four by-name joins put the census id in the twin room (1F-02 / 1F-03): swap to the geometric room
    jw = [r for r in read(RES / "agents_t262/T237_JOIN_CHECK_T262.csv") if r["RESULT"] == "JOIN_WRONG"]
    # r: room R deducts census id C, which geometry puts in the twin room; its partner o (room in C's geo rooms, same
    # kind, whose own id lies geometrically in R) is the opening R really deducts.
    corr = {}
    for r in jw:
        part = [o for o in jw if o is not r and o["T237_ROOM"] in r["GEO_ROOMS_OF_CENSUS_ID"].split()
                and r["T237_ROOM"] in o["GEO_ROOMS_OF_CENSUS_ID"].split() and o["CENSUS_ID"][:1] == r["CENSUS_ID"][:1]]
        if len(part) != 1:
            raise L.LedgerError(f"JOIN_UNRESOLVED: {r['T237_ROOM']} {r['CENSUS_ID']} has {len(part)} geometric partners")
        corr[(r["T237_ROOM"], r["CENSUS_ID"])] = part[0]["CENSUS_ID"]
    per = {}
    for r in rows:
        rid, cls = r["ROOM_ROW"], r["CLASS"]
        if cls in ("virtual", "wall"):
            continue
        w, s, h = f_(r["WIDTH_M"]), f_(r["SILL_M"]), f_(r["HEAD_M"])
        old = dict(w=w, sill=s, head=h)
        cid = r["cid"]
        z = sizes.get(cid) if cid else None
        # T-237 part 4 (alsenan_t237.py lines 404-421), unchanged
        if (z is not None and cls == "door" and z.get("w") and 0.005 < abs(z["w"] - w) <= 0.06
                and "split" not in r["basis"]):
            new = dict(w=z["w"], sill=s, head=h); src = "census frame width (T-237 rule d)"
        elif z is None or cls in ("door", "main"):
            new = dict(old); src = "T-128 r3 face (Q-55 C door head)" if cls in ("door", "main") else "T-128 r3 (unmatched)"
        elif z.get("fixed_m2") is not None:
            new = dict(w=w, fixed_m2=z["fixed_m2"]); src = z.get("src")
        elif z.get("sill") is not None and z.get("head") is not None:
            new = dict(w=w, sill=z["sill"], head=z["head"]); src = z.get("src")
        else:
            new = dict(w=w, sill=None, head=None, cap_m2=z.get("cap_m2")); src = z.get("src")
        if cid == "W17" and new.get("sill") is None:
            new, src = w17_q76a(w), W17_Q76A_SRC
        geo_cid = corr.get((rid, cid), cid) if cid else None
        host = hosts[geo_cid]["HOST_ROW"] if geo_cid and geo_cid in hosts else ""
        oid = geo_cid or f"T-128:{r['OPENING']}"
        per.setdefault(rid, []).append(dict(id=oid, t128=r["OPENING"], cls=cls, host=host, old=old, new=new,
                                            src=src, join_fixed=(geo_cid != cid),
                                            curved=(r.get("CURVED") == "yes")))
    return {r["ROW"]: r for r in rooms}, per


# ------------------------------------------------------------------------------------------------- faces
def finish_class(room):
    if room["KIND"] == "SHAFT":
        return "SHAFT"
    return "WET" if room["KIND"] == "WET" else "DRY"


def faces():
    """face pieces per room: one per (room, wall) on straight runs (T-250 face_m less its open-side metres) + the
    off-line pieces (column faces proud, wall off-line, curved glazing, doorway reveals) + the walk-class residual
    (T-128 FACE_M - the T-250 pieces, named)."""
    rooms = {r["ROW"]: r for r in read(RES / "agents_t128/ROOMS_T128_R3.csv")}
    clos = {r["room"]: r for r in read(RES / "agents_t250/ROOM_CLOSURE_T250.csv")}
    out = {}
    for r in read(RES / "agents_t250/FACE_LENGTH_T250.csv"):
        k = (r["room"], r["wall_id"])
        e = out.setdefault(k, dict(room=r["room"], wall=r["wall_id"], length=0.0, virtual=0.0, handles=[], runs=[]))
        e["length"] += float(r["face_m"]) - float(r["virtual_m"])
        e["virtual"] += float(r["virtual_m"])
        e["runs"].append(r["run_id"])
    pieces = {}
    for (room, wall), e in sorted(out.items()):
        if e["length"] <= 1e-9:
            continue                          # a run side the room touches only as open side (virtual)
        wid = wall if not wall.startswith("(none") else "BAND-STRETCH"
        pieces.setdefault(room, []).append(dict(face_id=f"{room}|{wid}", room=room, wall=wid,
                                                length_m=round(e["length"], 4), length_source=L.DRAWN,
                                                kind="WALL FACE", basis="T-250 FACE_LENGTH (runs " + " ".join(sorted(set(e["runs"]))) + ")"))
    for room, c in clos.items():
        for col, kind in (("off: COLUMN", "COLUMN FACES PROUD"), ("off: WALL", "WALL OFF A STRAIGHT BAND"),
                          ("off: WINDOW", "GLAZING OFF A BAND"), ("off: DOOR+GAP", "DOORWAY REVEALS / CLOSURES")):
            v = float(c[col])
            if v > 1e-9:
                pieces.setdefault(room, []).append(dict(face_id=f"{room}|OFF:{kind.split()[0]}", room=room,
                                                        wall="OFF-LINE", length_m=round(v, 4),
                                                        length_source=L.DRAWN, kind=kind,
                                                        basis="T-250 ROOM_CLOSURE off-line metres"))
    for room, rr in rooms.items():
        ps = pieces.get(room, [])
        s = sum(p["length_m"] for p in ps)
        res = round(float(rr["FACE_M"]) - s, 4)
        if abs(res) > 1e-4:
            if room == "GF-16":
                why = ("T-128 r3 takes GF-16's face from the T-074 VERIFIED hand outline (7.625 m); the T-250 walk of the "
                       "T-147 region runs inside the GF-W19 / GF-W31 strips (3.252 m) and on the far faces: the walk "
                       "pieces overstate the bath's own faces; the room keeps the verified outline")
            else:
                why = ("T-250 classes these 5 mm samples at opening ends as VIRTUAL (open side) that T-128 r3 counts "
                       "as face (both walks on the same contour); carried at the room level so the line reproduces")
            ps.append(dict(face_id=f"{room}|WALK-CLASS-RESIDUAL", room=room, wall="ROOM", length_m=res,
                           length_source=L.DRAWN, kind="WALK CLASS RESIDUAL", basis=why))
        pieces[room] = ps
    return rooms, pieces


def roof_faces():
    return {(r["room"], r["wall_id"]): r for r in read(RES / "agents_t250/ROOF_DATUM_T250.csv")}


# ------------------------------------------------------------------------------------------------- the ledger
def _dedm2(o, H_lo, H_hi):
    """(lo-case deduction, hi-case deduction, held?) of one opening at the face height(s)."""
    if o.get("fixed_m2") is not None:
        return o["fixed_m2"], o["fixed_m2"], False
    if o.get("sill") is None or o.get("head") is None:
        full = o["w"] * H_lo
        if o.get("ded_range_m2") is not None:
            return min(full, o["ded_range_m2"][1]), min(o["w"] * H_hi, o["ded_range_m2"][0]), True
        return (min(full, o["cap_m2"]) if o.get("cap_m2") is not None else full), 0.0, True
    a = o["w"] * max(0.0, min(o["head"], H_lo) - max(o["sill"], 0.0))
    b = o["w"] * max(0.0, min(o["head"], H_hi) - max(o["sill"], 0.0))
    return a, b, False


def _assign(room, ops, pieces):
    """opening -> face piece: the (room, host wall) face, else the room's off-line glazing / doorway piece, else the
    largest face of the room (named)."""
    by_wall = {p["wall"]: p for p in pieces}
    off = {p["kind"]: p for p in pieces if p["wall"] == "OFF-LINE"}
    out = []
    for o in ops:
        if o["host"] in by_wall:
            p, how = by_wall[o["host"]], "host wall face"
        elif o["curved"] and "GLAZING OFF A BAND" in off:
            p, how = off["GLAZING OFF A BAND"], "curved glazing off the straight bands (T-250 room-side line)"
        elif o["cls"] in ("door", "doorway", "arch", "main", "lift") and "DOORWAY REVEALS / CLOSURES" in off:
            p, how = off["DOORWAY REVEALS / CLOSURES"], "doorway between collinear walls (off-line reveal piece)"
        else:
            big = max((q for q in pieces if q["wall"] not in ("ROOM",)), key=lambda q: q["length_m"])
            p, how = big, f"host {o['host'] or 'unknown'} has no straight face of this room: carried on its largest face"
        out.append((o, p, how))
    return out


def build():
    cand = candidate()
    lines = cand["wall_finish_lines"]
    rooms, pieces = faces()
    _r, per_ops = openings()
    roof = roof_faces()
    xw = {r["T128_MAPPED"]: r["ENGINE_ROOM"] for r in read(RES / "agents_t262/ENGINE_ROOM_XWALK_T262.csv")
          if r["T128_MAPPED"]}
    room_map = {}
    for rid in rooms:
        room_map[rid] = ROUTE_T211.get(rid) or ([xw[rid]] if rid in xw else [])

    face_rows, ded_rows, room_rows = [], [], []
    ledger_room = {}
    for rid in sorted(rooms):
        rr = rooms[rid]
        fc = finish_class(rr)
        ps = pieces[rid]
        ops = per_ops.get(rid, [])
        L.check_openings([dict(room=rid, opening_id=o["id"], face_id="-") for o in ops])
        for p in ps:
            if p["kind"] != "WALK CLASS RESIDUAL":
                L.check_length(p)
        walked = float(rr["FACE_M"])
        L.room_closure([p["length_m"] for p in ps], walked)
        # ---- heights per method
        H_own = f_(rr["OWNER_H_M"])
        own_held = None
        if rr["ZONE"] == "GF_ANNEX":
            own_held = "annex owner height not established (G2; Q-54 B HOLD, D-39): owner 3.15 shown as information"
        elif rr["KIND"] == "SHAFT":
            own_held = "owner shaft height (Q-72 open; T-173 shaft ledger carries the drawing-derived figure)"
        elif H_own is None:
            own_held = "room level not drawn (T-088): no owner storey"
        p_lo, p_hi = T237.rng(rr["DWG_PAINT_TILE_H_M"])
        pl_top = f_(rr["DWG_PLASTER_H_TOP_M"])
        share = f_(rr["UNDER_ROOF_SHARE"]) or 0.0
        assign = _assign(rid, ops, ps)
        ops_on = {}
        for o, p, how in assign:
            ops_on.setdefault(p["face_id"], []).append(o)
            for tag, H in (("owner", H_own),):
                pass
            Hh = H_own if H_own is not None else None
            if Hh is not None:
                a_new, b_new, held_new = _dedm2(o["new"], Hh, Hh)
                a_old, b_old, held_old = _dedm2(o["old"], Hh, Hh)
            else:
                a_new = b_new = a_old = b_old = None; held_new = held_old = None
            ded_rows.append(dict(room=rid, opening_id=o["id"], t128_name=o["t128"], kind=o["cls"], host_wall=o["host"],
                                 face_id=p["face_id"], assignment=how, join_fixed_by_geometry="yes" if o["join_fixed"] else "",
                                 merged_size=_size_text(o["new"]), merged_source=o["src"], t128_size=_size_text(o["old"]),
                                 owner_h_m=H_own if H_own is not None else "HELD",
                                 owner_ded_new_m2=_rng_text(a_new, b_new, held_new),
                                 owner_ded_t128_m2=_rng_text(a_old, b_old, held_old),
                                 held=("yes" if held_new else "")))
        # ---- per face rows (owner method = the line's method; drawing-derived beside)
        items = L.owners(fc)
        own_lo = own_hi = 0.0
        own_any_held = False
        for p in ps:
            fops = [o["new"] | {"id": o["id"]} for o in ops_on.get(p["face_id"], [])]
            held_ids = [o["id"] for o in ops_on.get(p["face_id"], []) if _dedm2(o["new"], 1.0, 1.0)[2]]
            # owner method
            if own_held or H_own is None:
                o_st, o_lo, o_hi, o_item = L.HELD, None, None, own_held
                own_any_held = True
            else:
                g, _g, k_lo, k_hi, n_lo, n_hi, held = L.face_net(p["length_m"], H_own, H_own, fops)
                if held:
                    o_st, o_lo, o_hi = L.BOUNDED, round(n_lo, 4), round(n_hi, 4)
                    o_item = "opening head / sill not printed: " + ", ".join(
                        (i + " (arched outline on the curved glass line not drawn developed, T-238 A5; crown 3.00 "
                         "Q-76 A; hole w x 1.350 .. w x 3.000)") if i == "W17" else i for i in held)
                else:
                    o_st = L.VERIFIED if rid in VERIFIED_BY else L.AOA
                    o_lo = o_hi = round(n_lo, 4); o_item = ""
                own_lo += n_lo; own_hi += n_hi
            # drawing-derived method (paint / tile height; plaster to the soffit beside)
            rf = roof.get((rid, p["wall"]))
            if rf is not None:
                d_st, d_val, d_item = L.HELD, "", ("roof datum DCR-6 (designer D-39 item 3" + (", annex Q-54 B" if rid.startswith("GF") else "")
                                                   + f"): interval {rf['interval_bounds_m']} m, {rf['m2 per 0.01 m (block and plaster alike)']} m2 per 0.01 m; T-250 one-datum face")
            elif p_lo is None:
                d_st, d_val, d_item = L.HELD, "", "room level not drawn (T-088)" if rr["ZONE"] == "LEVEL_UNCLEAR" else "drawing-derived height HELD (T-128 / T-173)"
            elif share >= 0.999:
                d_st, d_val, d_item = L.HELD, "", "roof datum DCR-6: the room lies 100 % under a finished roof mark (T-128 UNDER_ROOF_SHARE 1.0)"
            elif share > 0:
                d_st, d_val, d_item = L.HELD, "", (f"roof datum DCR-6 on {share:.0%} of the room's face (T-128 share); "
                                                    "which faces lie under the roof is not in a merged ledger")
            else:
                r_ = L.face_net(p["length_m"], p_lo, p_hi, fops)
                d_val = f"{r_[4]:.4f} .. {r_[5]:.4f}"
                d_st = L.BOUNDED
                d_item = "floor build-up b 0 .. 0.10 (T-128)" + ("; opening head / sill: " + ", ".join(r_[6]) if r_[6] else "")
            row = dict(face_id=p["face_id"], floor=rid[:2] if rid[:2] in ("GF", "1F", "2F") else rid[3:], room=rid,
                       engine_rooms=" ".join(room_map[rid]), finish_class=fc, wall_id=p["wall"], piece=p["kind"],
                       length_m=f"{p['length_m']:.4f}", length_source=p["length_source"], length_basis=p["basis"],
                       openings=" ".join(o["id"] for o in ops_on.get(p["face_id"], [])),
                       owner_h_m=(f"{H_own:.2f}" if H_own is not None else "HELD"),
                       owner_status=o_st, owner_net_lo_m2=("" if o_lo is None else f"{o_lo:.4f}"),
                       owner_net_hi_m2=("" if o_hi is None else f"{o_hi:.4f}"),
                       owner_source=(G1 if o_st in (L.AOA, L.VERIFIED, L.BOUNDED) else ""),
                       verified_by=VERIFIED_BY.get(rid, "") if o_st == L.VERIFIED else "",
                       owner_held_item=o_item, dwg_paint_h_m=rr["DWG_PAINT_TILE_H_M"] or "HELD",
                       dwg_plaster_top_m=rr["DWG_PLASTER_H_TOP_M"] or "HELD", dwg_status=d_st, dwg_net_m2=d_val,
                       dwg_held_item=d_item, roof_datum_face=("yes" if rf is not None else ""),
                       rule_difference_outside=(f"W03 room-side line vs window line +{W03_RULE_DIFF_M} m x the face "
                                                f"height (Q-38 A window line; T-250 / T-286), outside every total"
                                                if any(o["id"] == "W03" for o in ops_on.get(p["face_id"], [])) else ""))
            for code in items:
                rr2 = dict(row, item_code=code)
                if (fc, code) in L.SUBSTRATE_ONLY:
                    rr2.update(owner_status=L.HELD, owner_net_lo_m2="", owner_net_hi_m2="", owner_source="",
                               verified_by="", owner_held_item="plaster under full-height wall tile: not an owner rule "
                               "(T-211 s.5.4; V3.0.9b): substrate HELD, never 0")
                face_rows.append(rr2)
        ledger_room[rid] = dict(fc=fc, own_held=own_held, lo=round(own_lo, 4), hi=round(own_hi, 4))
    return dict(cand=cand, lines=lines, rooms=rooms, pieces=pieces, ops=per_ops, faces=face_rows, deds=ded_rows,
                room_map=room_map, ledger_room=ledger_room)


def _size_text(o):
    if o.get("fixed_m2") is not None:
        return f"outline {o['fixed_m2']} m2"
    if o.get("sill") is None or o.get("head") is None:
        if o.get("ded_range_m2") is not None:
            return f"w {o['w']} arched outline HELD, deduction {o['ded_range_m2'][0]} .. {o['ded_range_m2'][1]} m2"
        return f"w {o['w']} h HELD" + (f" (cap {o['cap_m2']} m2)" if o.get("cap_m2") is not None else "")
    return f"w {o['w']} sill {o['sill']} head {o['head']}"


def _rng_text(a, b, held):
    if a is None:
        return "HELD (room)"
    if held:
        return (f"{b:.4f} .. {a:.4f} (HELD)" if b else f"0 .. {a:.4f} (HELD)")
    return f"{a:.4f}"


# ------------------------------------------------------------------------------------------------- lines
LINE_CLASSES = (
    ("wall face", "ROOM_FACE"), ("stair hall", "ROOM_FACE"), ("door jambs and head", "JAMB"),
    ("window reveals", "REVEAL"), ("facade", "EXTERIOR"), ("paint above wall tile", "ROOM_FACE"),
    ("finish above wall tile", "ROOM_FACE"),
)


def line_class(ln):
    el = (ln.get("physical_element") or "").lower()
    if ln["item_code"] == L.EXT:
        return "EXTERIOR"
    for k, c in LINE_CLASSES:
        if el.startswith(k):
            return c
    return "ROOM_FACE"


def line_live(ln):
    return ln["evidence_state"] not in ("NOT_APPLICABLE_WITH_EVIDENCE", "SUPERSEDED")


def _t211_line_basis(rid, code, rr, ops):
    """the candidate's own figure for a T-211 room record, rebuilt from its merged inputs (reproduction guard)."""
    sys.path.insert(0, str(RES / "agents_t211"))
    import t211_inputs as T211   # noqa: E402
    r128, o128 = T211.rows()
    rec = T211.room_record(rid, r128[rid], o128.get(rid, []), code)
    if rec["state"] == "RELEASED":
        return rec["value"], rec["value"], rec["owner_method"]["deductions"]
    if rec["state"] == "BOUNDED":
        return rec["range"][0], rec["range"][1], rec["owner_method"]["deductions"]
    return None, None, []


def line_ledger(B):
    """per candidate line: the faces it carries, the ledger figure, the line's own figure and the named causes."""
    lines = [ln for ln in B["lines"]]
    live = [ln for ln in lines if line_live(ln)]
    room_face = [dict(ln) for ln in live if line_class(ln) == "ROOM_FACE"]
    # SHARED_ROOM: one candidate room holds the room-face record AND the shaft-part record (T-211 s.5.1): each line is
    # told apart by its own text (the shaft record names the shaft); exactly one of each per code, else refused
    for eng, (room_rec, shaft_rec) in SHARED_ROOM.items():
        for code in (L.PLASTER, L.PAINT):
            mine = [ln for ln in room_face if ln["room_id"] == eng and ln["item_code"] == code
                    and ln["physical_element"].startswith("wall face")]
            sh = [ln for ln in mine if "shaft" in ln["rfi"].lower()]
            rm = [ln for ln in mine if "shaft" not in ln["rfi"].lower()]
            if len(sh) != 1 or len(rm) != 1:
                raise L.LedgerError(f"FACE_TWICE: {eng} {code}: {len(rm)} room record(s) and {len(sh)} shaft record(s)")
            sh[0]["room_id"] = f"{eng}#{shaft_rec}"
            rm[0]["room_id"] = f"{eng}#{room_rec}"
    fc_faces = [dict(face_id=r["face_id"], room=r["room"], finish_class=r["finish_class"]) for r in B["faces"]]
    uniq = {f["face_id"]: f for f in fc_faces}
    # SHARED_ROOM: one candidate room line holds two ledger rooms; each ledger room's faces bind to it whole
    rmap = {}
    for rid, engs in B["room_map"].items():
        rmap[rid] = [(f"{e}#{rid}" if e in SHARED_ROOM else e) for e in engs]
    # a shared room's route lines (wet / dry route, not the records) stay on the bare engine room id: none here
    bindings, unmatched_faces, unmatched = L.bind(list(uniq.values()), room_face, rmap)
    out, causes_rows = [], []
    by_line = {}
    for (fid, code), bl in bindings.items():
        for lid, frac in bl:
            by_line.setdefault(lid, []).append((fid, code, frac))
    face_of = {}
    for r in B["faces"]:
        face_of[(r["face_id"], r["item_code"])] = r
    for ln in room_face:
        lid = ln["line_id"]
        st, v_lo, v_hi = line_value(ln)
        fl = by_line.get(lid, [])
        if not fl:
            continue                      # a line holding no face: listed below as UNMATCHED_LINE with its reason
        rooms_ = sorted({uniq[f]["room"] for f, _c, _x in fl})
        lo = hi = 0.0
        held = []
        for fid, code, frac in fl:
            r = face_of[(fid, code)]
            if r["owner_status"] == L.HELD:
                held.append(fid); continue
            lo += float(r["owner_net_lo_m2"]) * frac; hi += float(r["owner_net_hi_m2"]) * frac
        ledger_state = ("HELD" if held and len(held) == len(fl) else ("PART + HELD" if held else
                        ("BOUNDED" if abs(hi - lo) > 1e-6 else "DETERMINATE")))
        cause_txt, rest_lo, rest_hi, basis = "", "", "", ""
        if rooms_ and all(r_.startswith("ST-") for r_ in rooms_):
            # the stair shaft: one owner, the T-173 shaft ledger (actual exposed geometry, drawing-derived); the owner
            # method has no shaft height (Q-72). The T-250 faces are listed for identity, the figure is T-173's.
            sys.path.insert(0, str(RES / "agents_t211"))
            import t211_inputs as T211   # noqa: E402
            rec = [x for x in T211.shaft_records(ln["item_code"]) if x["room"] == rooms_[0]][0]
            ledger_state = "CITED T-173 (owner method HELD, Q-72)"
            if rec["state"] == "BOUNDED":
                lo, hi = rec["range"]
                ok = v_lo is not None and abs(lo - v_lo) <= 0.006 and abs(hi - v_hi) <= 0.006
                basis = ("REPRODUCED from T-173 SHAFT_T173.json via T-211 shaft_records" if ok else
                         f"NOT REPRODUCED (T-173 {lo} .. {hi})")
                rest_lo, rest_hi = (round(v_lo - lo, 4), round(v_hi - hi, 4)) if ok else ("", "")
            else:
                basis = "T-173 2F part HELD (D-T173-1 roof panel T 18; roof B3 contact): no figure, never 0"
            held = []
            out.append(dict(line_id=lid, item_code=ln["item_code"], floor=ln["floor"],
                            engine_room=ln["room_id"].split("#")[0], element=ln["physical_element"], line_state=st,
                            line_lo_m2=("" if v_lo is None else f"{v_lo:.4f}"), line_hi_m2=("" if v_hi is None else f"{v_hi:.4f}"),
                            ledger_rooms=" ".join(rooms_), faces=len(fl), faces_held=len(fl), ledger_state=ledger_state,
                            ledger_owner_lo_m2="", ledger_owner_hi_m2="", ledger_part_lo_m2="", ledger_part_hi_m2="",
                            ledger_dwg_t173_lo_m2=(f"{lo:.4f}" if rec["state"] == "BOUNDED" else ""),
                            ledger_dwg_t173_hi_m2=(f"{hi:.4f}" if rec["state"] == "BOUNDED" else ""),
                            line_basis=basis, line_minus_ledger_causes="none (the line is the T-173 figure)",
                            residual_lo_m2=("" if rest_lo == "" else f"{rest_lo:.4f}"),
                            residual_hi_m2=("" if rest_hi == "" else f"{rest_hi:.4f}")))
            continue
        if v_lo is not None and not held:
            # the line's basis: T-211 room records (owner method on the T-128 r3 opening table)
            b_lo = b_hi = 0.0; deds_old = []
            for rid in rooms_:
                rr = B["rooms"][rid]
                x = _t211_line_basis(rid, ln["item_code"], rr, None)
                if x[0] is None:
                    b_lo = None; break
                b_lo += x[0]; b_hi += x[1]; deds_old += [(rid, d) for d in x[2]]
            if b_lo is not None and abs(b_lo - v_lo) <= 0.006 and abs(b_hi - v_hi) <= 0.006:
                basis = "REPRODUCED from T-211 inputs (T-128 r3 opening table; W15 / W16 range)"
                causes = _causes(B, rooms_, deds_old)
                for c in causes:
                    causes_rows.append(dict(line_id=lid, item_code=ln["item_code"], **c))
                c_lo = sum(c["d_lo_m2"] for c in causes); c_hi = sum(c["d_hi_m2"] for c in causes)
                rest_lo = L.reconcile(v_lo, lo, [dict(cause="openings", m2=c_lo)])
                rest_hi = L.reconcile(v_hi, hi, [dict(cause="openings", m2=c_hi)])
                cause_txt = "; ".join(f"{c['opening_id']} {c['d_lo_m2']:+.4f} / {c['d_hi_m2']:+.4f} ({c['cause']})"
                                      for c in causes if abs(c["d_lo_m2"]) > 1e-6 or abs(c["d_hi_m2"]) > 1e-6)
            else:
                basis = f"NOT REPRODUCED (T-211 basis {b_lo} .. {b_hi})"
        out.append(dict(line_id=lid, item_code=ln["item_code"], floor=ln["floor"], engine_room=ln["room_id"].split("#")[0],
                        element=ln["physical_element"], line_state=st,
                        line_lo_m2=("" if v_lo is None else f"{v_lo:.4f}"), line_hi_m2=("" if v_hi is None else f"{v_hi:.4f}"),
                        ledger_rooms=" ".join(rooms_), faces=len(fl), faces_held=len(held), ledger_state=ledger_state,
                        ledger_owner_lo_m2=("" if held else f"{lo:.4f}"), ledger_owner_hi_m2=("" if held else f"{hi:.4f}"),
                        ledger_part_lo_m2=(f"{lo:.4f}" if held and len(held) < len(fl) else ""),
                        ledger_part_hi_m2=(f"{hi:.4f}" if held and len(held) < len(fl) else ""),
                        ledger_dwg_t173_lo_m2="", ledger_dwg_t173_hi_m2="",
                        line_basis=basis, line_minus_ledger_causes=cause_txt,
                        residual_lo_m2=("" if rest_lo in ("", None) else f"{rest_lo:.4f}"),
                        residual_hi_m2=("" if rest_hi in ("", None) else f"{rest_hi:.4f}")))
    rf_ids = {x["line_id"] for x in room_face}
    unmatched_ids = {x["line_id"] for x in unmatched}
    for ln in lines:
        if ln["line_id"] in rf_ids and ln["line_id"] not in unmatched_ids:
            continue
        el = (ln.get("physical_element") or "").lower()
        why = (("not live (NOT_APPLICABLE_WITH_EVIDENCE): " + (
                    "paint above full-height wall tile, none by UP-FIN-PAINT-001 / Q-48 A (a tiled face is not painted)"
                    if el.startswith("paint above") else
                    "route room line superseded by the V3.0.9 room record (T-211), carries no figure"))
               if not line_live(ln) else {
            "JAMB": "door jamb / head surfaces (UP-FIN-PLASTER-001): perpendicular to the wall face, not in any face length; own line, one owner",
            "REVEAL": "window reveal surfaces: perpendicular to the wall face, not in any face length; own line, one owner",
            "EXTERIOR": "exterior faces: no room face (T-250 'NO ROOM ON THIS SIDE'); owned by the facade / Sigma ledger (OWNER_NOTES_SIGMA_2026-10-21)",
        }.get(line_class(ln), "room-face line of a room with no face in this ledger"))
        if ln["line_id"] in unmatched_ids and ln["room_id"] == "GF-RC06FED" and ln["item_code"] == L.PAINT:
            why = ("holds no face: the pantry GF-07 is WET (owner Q-37 A; T-128 r3 class WET): tiled to the decor ceiling, "
                   "not painted (UP-FIN-PAINT-001); T-211 kept this HELD paint line so that no face was dropped silently")
        out.append(dict(line_id=ln["line_id"], item_code=ln["item_code"], floor=ln["floor"], engine_room=ln["room_id"],
                        element=ln["physical_element"], line_state=ln["evidence_state"],
                        line_lo_m2=(lambda v: "" if v[1] is None else f"{v[1]:.4f}")(line_value(ln)),
                        line_hi_m2=(lambda v: "" if v[2] is None else f"{v[2]:.4f}")(line_value(ln)),
                        ledger_rooms="", faces=0, faces_held=0, ledger_state="UNMATCHED_LINE: " + why,
                        ledger_owner_lo_m2="", ledger_owner_hi_m2="", ledger_part_lo_m2="", ledger_part_hi_m2="",
                        ledger_dwg_t173_lo_m2="", ledger_dwg_t173_hi_m2="",
                        line_basis="", line_minus_ledger_causes="", residual_lo_m2="", residual_hi_m2=""))
    return out, causes_rows, unmatched_faces


def _causes(B, rooms_, deds_old):
    """per opening: (line deduction - ledger deduction) in the lo case and the hi case, named."""
    out = []
    for rid in rooms_:
        rr = B["rooms"][rid]
        H = f_(rr["OWNER_H_M"])
        old = {d["opening"]: d for r_, d in deds_old if r_ == rid}
        for o in B["ops"].get(rid, []):
            d = old.get(o["t128"])
            if d is None:
                continue
            if "m2" in d:
                ol_lo = ol_hi = d["m2"]
            else:
                ol_lo, ol_hi = d["range"][1], d["range"][0]
            n_lo, n_hi, held = _dedm2(o["new"], H, H)
            # net = gross - deduction: line - ledger = ledger deduction - line deduction
            dl, dh = round(n_lo - ol_lo, 6), round(n_hi - ol_hi, 6)
            cause = ("unchanged" if abs(dl) < 1e-9 and abs(dh) < 1e-9 else
                     ("merged size: " + o["src"]))
            out.append(dict(room=rid, opening_id=o["id"], t128_name=o["t128"], line_ded=_rng_text(ol_lo, ol_hi, False) if "m2" in d else f"{ol_hi:.4f} .. {ol_lo:.4f}",
                            ledger_ded=_rng_text(n_lo, n_hi, held), d_lo_m2=dl, d_hi_m2=dh, cause=cause))
    return out


# ------------------------------------------------------------------------------------------------- outputs
FACE_COLS = ("face_id", "item_code", "floor", "room", "engine_rooms", "finish_class", "wall_id", "piece", "length_m",
             "length_source", "length_basis", "openings", "owner_h_m", "owner_status", "owner_net_lo_m2",
             "owner_net_hi_m2", "owner_source", "verified_by", "owner_held_item", "dwg_paint_h_m", "dwg_plaster_top_m",
             "dwg_status", "dwg_net_m2", "dwg_held_item", "roof_datum_face", "rule_difference_outside")


def _csv(rows, cols):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=list(cols), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    return s.getvalue()


def outputs():
    B = build()
    for r in B["faces"]:
        L.check_row(dict(face_id=r["face_id"], status=r["owner_status"],
                         net_lo=f_(r["owner_net_lo_m2"]), net_hi=f_(r["owner_net_hi_m2"]),
                         held_item=r["owner_held_item"], verified_by=r["verified_by"], source=r["owner_source"],
                         residual=(r["piece"] in ("WALK CLASS RESIDUAL", "GLAZING OFF A BAND", "DOORWAY REVEALS / CLOSURES"))))
    lines_out, causes, unmatched_faces = line_ledger(B)
    # closures
    clos = []
    for rid, rr in sorted(B["rooms"].items()):
        ps = B["pieces"][rid]
        s = round(sum(p["length_m"] for p in ps), 4)
        lr = B["ledger_room"][rid]
        clos.append(dict(room=rid, finish_class=lr["fc"], t128_face_m=rr["FACE_M"], pieces=len(ps),
                         pieces_sum_m=f"{s:.4f}", residual_m=f"{s - float(rr['FACE_M']):.4f}",
                         ledger_owner_net=("HELD: " + lr["own_held"]) if lr["own_held"] else
                         (f"{lr['lo']:.2f}" if abs(lr["hi"] - lr["lo"]) < 0.005 else f"{lr['lo']:.2f} .. {lr['hi']:.2f}"),
                         t237_owner_net_new=_t237_room(rid), t209_wet_tile_net_A=_t209_room(rid)))
    files = {
        "FACE_TO_LINE_LEDGER_T292.csv": _csv(B["faces"], FACE_COLS),
        "OPENING_DEDUCTIONS_T292.csv": _csv(B["deds"], list(B["deds"][0].keys())),
        "LINE_SUMMARY_T292.csv": _csv(lines_out, list(lines_out[0].keys())),
        "LINE_CAUSES_T292.csv": _csv(causes, ("line_id", "item_code", "room", "opening_id", "t128_name", "line_ded",
                                              "ledger_ded", "d_lo_m2", "d_hi_m2", "cause")),
        "ROOM_CLOSURE_T292.csv": _csv(clos, list(clos[0].keys())),
    }
    summ = summary(B, lines_out, causes, unmatched_faces, clos)
    files["summary.json"] = json.dumps(summ, indent=1, ensure_ascii=False) + "\n"
    return files


def _t209_room(rid):
    """T-209 (merged wet-wall-tile ledger, Q-48 A) owner-method net, beside: it keeps the T-128 door face widths
    (1F-09: D-1F-07 0.75), the ledger takes the T-237 merged census frame width (0.80): -0.110 m2 there."""
    for r in read(RES / "agents_t209/WET_WALL_TILES_T209.csv"):
        if r["ROOM"] == rid:
            return r["A_NET_M2"] + (f" .. {r['A_NET_HI_M2']}" if r["A_NET_HI_M2"] else "")
    return ""


def _t237_room(rid):
    for r in read(RES / "agents_t237/ROOMS_T237.csv"):
        if r["room"] == rid:
            return r["owner_net_new_m2"]
    return ""


def summary(B, lines_out, causes, unmatched_faces, clos):
    faces = B["faces"]
    tot = {}
    for r in faces:
        k = (r["item_code"], r["owner_status"])
        e = tot.setdefault(k, dict(rows=0, lo=0.0, hi=0.0))
        e["rows"] += 1
        if r["owner_net_lo_m2"]:
            e["lo"] += float(r["owner_net_lo_m2"]); e["hi"] += float(r["owner_net_hi_m2"])
    dwg = {}
    for r in faces:
        k = (r["item_code"], r["dwg_status"])
        dwg[k] = dwg.get(k, 0) + 1
    # residual: per room, the ledger owner net = the T-237 part-4 owner net (to its 0.01 rounding)
    repro = []
    for c in clos:
        t = c["t237_owner_net_new"]
        if c["ledger_owner_net"].startswith("HELD") or t in ("", "HELD"):
            continue
        a = T237.rng(c["ledger_owner_net"]); b = T237.rng(t)
        ok = abs(a[0] - b[0]) <= L.TOL_M2 and abs(a[1] - b[1]) <= L.TOL_M2
        repro.append(dict(room=c["room"], ledger=c["ledger_owner_net"], t237=t, ok=ok)
                     | ({} if ok else {"named_cause": R2_NAMED_T237_DIFF.get(c["room"], "")}))
    return {
        "task": "T-292", "rule": L.RULE_ID,
        "candidate": {k: B["cand"][k] for k in ("source", "csv_sha256_8", "lines_total")},
        "candidate_wall_finish_lines": len(B["lines"]),
        "face_pieces": len({r["face_id"] for r in faces}), "face_rows": len(faces),
        "rooms": len(clos), "room_length_residual_max_m": max(abs(float(c["residual_m"])) for c in clos),
        "owner_totals_by_item_status": {f"{k[0]} | {k[1]}": dict(rows=v["rows"], lo=round(v["lo"], 4), hi=round(v["hi"], 4))
                                        for k, v in sorted(tot.items())},
        "drawing_status_rows": {f"{k[0]} | {k[1]}": v for k, v in sorted(dwg.items())},
        "roof_datum_face_rows": sorted({r["face_id"] for r in faces if r["roof_datum_face"]}),
        "lines": {"room_face_bound": sum(1 for x in lines_out if not x["ledger_state"].startswith("UNMATCHED")),
                  "unmatched": sum(1 for x in lines_out if x["ledger_state"].startswith("UNMATCHED"))},
        "unmatched_faces": unmatched_faces,
        "t237_room_reproduction": {"rooms": len(repro), "ok": sum(1 for r in repro if r["ok"]),
                                   "differs": [r for r in repro if not r["ok"]],
                                   "differs_unexplained": sum(1 for r in repro if not r["ok"] and not r["named_cause"])},
        "line_residual_max_abs_m2": max([abs(float(x[k])) for x in lines_out for k in ("residual_lo_m2", "residual_hi_m2")
                                         if x[k] != ""] or [0.0]),
        "line_residual_note": "the candidate states room nets to 4 dp; the ledger sums per-face figures rounded to 4 dp: "
                              "|residual| <= 0.0005 m2 is that rounding, anything larger is refused (UNEXPLAINED)",
        "closure_faces_vs_lines": closure(B, lines_out),
        "w03_rule_difference": {"room_side_deducted_m": 6.731, "window_line_m": 6.5675,
                                "difference_m": round(6.731 - 6.5675, 4),
                                "owner_method_m2": round((6.731 - 6.5675) * 3.65, 4),
                                "note": "finishes deduct W03 on the room-side glass line (T-128 6.731; drawing 6.7291, "
                                        "Checker 6.7294); the window line keeps Q-38 A 6.5675: RULE_DIFFERENCE between "
                                        "trades, outside every total (head 4.30 > owner 3.65)"},
    }


def closure(B, lines_out):
    """rule 6: per item code, the faces bound to a line (owner method, determinate + bounded) = the lines' ledger sums."""
    out = {}
    bound_rooms = {}
    for x in lines_out:
        if x["ledger_state"].startswith(("UNMATCHED", "CITED")):
            continue
        for r_ in x["ledger_rooms"].split():
            bound_rooms[(r_, x["item_code"])] = True
    for code in (L.PLASTER, L.PAINT, L.TILE):
        f_lo = sum(float(r["owner_net_lo_m2"]) for r in B["faces"] if r["item_code"] == code
                   and r["owner_net_lo_m2"] and (r["room"], code) in bound_rooms)
        f_hi = sum(float(r["owner_net_hi_m2"]) for r in B["faces"] if r["item_code"] == code
                   and r["owner_net_hi_m2"] and (r["room"], code) in bound_rooms)
        l_lo = sum(float(x["ledger_owner_lo_m2"] or x["ledger_part_lo_m2"] or 0) for x in lines_out
                   if x["item_code"] == code and not x["ledger_state"].startswith(("UNMATCHED", "CITED")))
        l_hi = sum(float(x["ledger_owner_hi_m2"] or x["ledger_part_hi_m2"] or 0) for x in lines_out
                   if x["item_code"] == code and not x["ledger_state"].startswith(("UNMATCHED", "CITED")))
        out[code] = dict(faces_lo=round(f_lo, 4), faces_hi=round(f_hi, 4), lines_lo=round(l_lo, 4),
                         lines_hi=round(l_hi, 4), residual_lo=round(f_lo - l_lo, 4), residual_hi=round(f_hi - l_hi, 4))
    return out


def main(argv):
    if argv[:1] == ["--extract"]:
        d = extract(Path(argv[1])); print("extracted", len(d["wall_finish_lines"]), "lines", d["csv_sha256_8"]); return 0
    files = outputs()
    if argv[:1] == ["--write"]:
        for n, t in files.items():
            (HERE / n).write_text(t, encoding="utf-8")
        print("written", ", ".join(files)); return 0
    if argv[:1] == ["--check"]:
        bad = [n for n, t in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}"); return 1 if bad else 0
    print(files["summary.json"]); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
