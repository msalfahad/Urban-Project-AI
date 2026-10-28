"""T-313 read-only run on the development villa (Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip).
Every output goes to --out (outside the repository); the committed CSVs carry ids, lengths and states only (no
coordinates, no names).

    python3 -I research/agents_t313/t313_alsenan.py <P7757.dxf> <ARCH_ROOMS.json of an engine run> \
        <BOQ_LINES.csv of the candidate> --out <scratch>/t313

Per window (census handles, T-249 MERGED) the reveal depths are MEASURED on the plan: the frame band = the extreme
offsets across the wall of the census glazing lines parallel to the opening; the two wall faces = the nearest lines
parallel to it, outside the symbol, that end at a jamb of the opening (within 10 mm) on each side of the band; the
room side = the side whose probe point (0.30 m beyond the face, mid-opening) lies in an engine room polygon. Sizes:
T-237 OPENING_SIZES (MERGED, merged heads T-201 / T-207 / T-238); plaster band: the owner height of the room (T-237
ROOMS owner_h, Q-43 / Q-48 A) beside the drawing-derived range (dwg_paint_h). Doors: one reveal through the wall
(UP-FIN-PLASTER-001), wall thickness from T-150 (MERGED). Curved windows (W03, W17) and undrawn arches are not
measured here (developed surfaces: T-302 / T-238), they stay UNRESOLVED / HELD by name.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t313_reveal_ledger as L  # noqa: E402

TOL_END = 0.010     # m: a wall face line ends at the jamb
MAX_REACH = 0.60    # m: a wall face within this offset of the frame band
CURVED = {"W03", "W17"}


def sha8(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def segments(doc, scale):
    msp = doc.modelspace()
    out = []
    for e in msp.query("LINE LWPOLYLINE"):
        if e.dxftype() == "LINE":
            pts = [tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]]
            pairs = [(pts[0], pts[1])]
        else:
            pts = [tuple(p[:2]) for p in e.get_points()]
            pairs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if e.closed else [])
        for a, b in pairs:
            out.append((e.dxf.handle, e.dxf.layer, (a[0] * scale, a[1] * scale), (b[0] * scale, b[1] * scale)))
    return out


def measure_window(handles, segs_by_handle, all_segs):
    sym = [s for h in handles for s in segs_by_handle.get(h, ())]
    if not sym:
        return None, "no census glazing line found"
    longest = max(sym, key=lambda s: math.dist(s[2], s[3]))
    (ax, ay), (bx, by) = longest[2], longest[3]
    L0 = math.dist((ax, ay), (bx, by))
    ux, uy = (bx - ax) / L0, (by - ay) / L0
    nx, ny = -uy, ux

    def along(p):
        return (p[0] - ax) * ux + (p[1] - ay) * uy

    def across(p):
        return (p[0] - ax) * nx + (p[1] - ay) * ny

    def parallel(s):
        dx, dy = s[3][0] - s[2][0], s[3][1] - s[2][1]
        Ls = math.hypot(dx, dy)
        return Ls > 1e-6 and abs(ux * dy - uy * dx) / Ls < 0.01

    par = [s for s in sym if parallel(s)]
    offs = [across(p) for s in par for p in (s[2], s[3])]
    f0, f1 = min(offs), max(offs)
    al = [along(p) for s in sym for p in (s[2], s[3])]
    a0, a1 = min(al), max(al)
    hs = set(handles)
    lo, hi = [], []
    for s in all_segs:
        if s[0] in hs or not parallel(s):
            continue
        o = across(s[2])
        if abs(across(s[3]) - o) > 1e-4:
            continue
        e = sorted((along(s[2]), along(s[3])))
        touches = (abs(e[1] - a0) <= TOL_END and e[0] < a0 - TOL_END) or \
                  (abs(e[0] - a1) <= TOL_END and e[1] > a1 + TOL_END)
        if not touches:
            continue
        if f1 - 1e-4 <= o <= f1 + MAX_REACH:
            hi.append(o)
        elif f0 - MAX_REACH <= o <= f0 + 1e-4:
            lo.append(o)
    if not lo or not hi:
        return None, "a wall face ending at the jambs not found on both sides"
    s_lo, s_hi = max(lo), min(hi)
    mid = (a0 + a1) / 2

    def pt(o):
        return (ax + ux * mid + nx * o, ay + uy * mid + ny * o)

    return {"frame": (f0, f1), "faces": (s_lo, s_hi), "t": s_hi - s_lo, "width_sym": a1 - a0,
            "probe_lo": pt(s_lo - 0.30), "probe_hi": pt(s_hi + 0.30),
            "d_lo": f0 - s_lo, "d_hi": s_hi - f1}, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("rooms")
    ap.add_argument("lines")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import ezdxf
    from shapely.geometry import Point, Polygon
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.readfile(a.plan)
    unit = {4: 0.001, 6: 1.0, 5: 0.01}[doc.header.get("$INSUNITS")]
    segs = segments(doc, unit)
    by_h = {}
    for s in segs:
        by_h.setdefault(s[0], []).append(s)
    rooms = json.loads(Path(a.rooms).read_text(encoding="utf-8"))["rooms"]
    polys = [(r["room_id"], r["floor"], Polygon(r["polygon_m"])) for r in rooms if r.get("polygon_m")]
    cls = {r["room_id"]: r["class"] for r in rooms}
    inv = read_csv(RES / "agents_t249" / "OPENINGS_T249.csv")
    t150 = {x["ID"]: x for x in read_csv(RES / "agents_t150" / "OPENINGS_T150.csv")}
    t237 = read_csv(RES / "agents_t237" / "OPENING_SIZES_T237.csv")
    t237r = {x["room"]: x for x in read_csv(RES / "agents_t237" / "ROOMS_T237.csv")}
    t238 = {x["ID"]: x for x in read_csv(RES / "agents_t238" / "CENSUS_T238.csv")}
    t201 = {x["ID"]: x for x in read_csv(RES / "agents_t201" / "HEADS_T201.csv")}
    cand = read_csv(a.lines)
    reveal_lines = {x["room_id"].split("-STRIP-")[1] + "@" + x["floor"]: x for x in cand
                    if x["item_code"] == "ARCH.WINDOW_REVEAL"}

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    sizes = {}
    for x in t237:          # one size per opening (the same merged size in each room it bounds)
        cid = x["census_id"]
        sizes.setdefault(cid, {"w": num(x["merged_w"]), "sill": num(x["merged_sill"]), "head": num(x["merged_head"]),
                               "status": x["merged_status"], "rooms": []})
        sizes[cid]["rooms"].append(x["room"])

    openings, geo, binding = [], [], {}
    for r in inv:
        oid, kind, floor = r["ID"], r["KIND"], r["FLOOR"]
        sz = sizes.get(oid, {})
        w, sill, head = sz.get("w"), sz.get("sill"), sz.get("head")
        h = None if (head is None or sill is None) else round(head - sill, 6)
        if oid in ("W11", "W12"):     # T-207: h 2.20 DRAWING-CONFIRMED, sill HELD
            h = 2.20
        if h is None and t201.get(oid, {}).get("STATUS") == "DRAWING-CONFIRMED":   # T-201: height drawn, levels HELD
            h = num(t201[oid]["HEIGHT_M"])
        if oid == "W02":              # T-207: drawn count 1, height at the B-B cut 2.20, sill 0 (floor glazing); HELD D-53
            h = None
        hstat = sz.get("status", "")
        if kind == "WINDOW":
            ref = r["ENGINE_REF"].split(" ")[0]
            g, why = (None, "curved on plan: developed reveal not measured here (T-302 / T-238)") if oid in CURVED \
                else measure_window(r["HANDLES"].split(), by_h, segs)
            din = dout = None
            room = None
            src = why
            if g:
                ins = []
                for side, p in (("lo", g["probe_lo"]), ("hi", g["probe_hi"])):
                    hit = [rid for rid, fl, pg in polys if fl == floor and pg.contains(Point(p))]
                    ins.append((side, hit))
                inside = [s for s, hit in ins if hit]
                far = None
                if len(inside) == 2:     # a labelled room on one side, an unlabelled space (e.g. the Q-67 side
                    lab = [s for s, hit in ins if any(cls[x] != "UNLABELLED" for x in hit)]   # passage) on the other
                    if len(lab) == 1:
                        far = [hit for s, hit in ins if s != lab[0]][0][0]
                        inside = lab
                if len(inside) == 1:
                    s_in = inside[0]
                    room = [hit for s, hit in ins if s == s_in][0][0]
                    din = g["d_lo"] if s_in == "lo" else g["d_hi"]
                    dout = g["d_hi"] if s_in == "lo" else g["d_lo"]
                    din, dout = round(max(din, 0.0), 4), round(max(dout, 0.0), 4)
                    src = f"plan: wall faces t {g['t']:.3f} m, frame band {g['frame'][1] - g['frame'][0]:.3f} m" + \
                        (" (far side an unlabelled engine space: the side passage, Q-67 A conditional exterior)"
                         if far else "")
                else:
                    src = f"room side not established (probe in {len(inside)} rooms)"
                geo.append({"opening": oid, "floor": floor, "wall_t_plan_m": round(g["t"], 4),
                            "wall_t_t150_m": t150.get(oid, {}).get("WALL_T_M"),
                            "frame_band_m": round(g["frame"][1] - g["frame"][0], 4),
                            "width_symbol_m": round(g["width_sym"], 4), "depth_in_m": din, "depth_out_m": dout,
                            "engine_room": room, "basis": src})
            else:
                geo.append({"opening": oid, "floor": floor, "wall_t_plan_m": None,
                            "wall_t_t150_m": t150.get(oid, {}).get("WALL_T_M"), "frame_band_m": None,
                            "width_symbol_m": None, "depth_in_m": None, "depth_out_m": None, "engine_room": None,
                            "basis": src})
            rm = sz.get("rooms", [None])[0]
            hp = num(t237r.get(rm, {}).get("owner_h")) if rm else None
            fg = sill == 0.0 and oid not in ("W02",)
            openings.append({"id": oid, "kind": "FLOOR_GLAZING" if fg else "WINDOW", "width_m": w, "height_m": h,
                             "sill_m": sill, "depth_in_m": din, "depth_out_m": dout, "depth_in_source": src,
                             "depth_out_source": src, "plaster_height_m": hp, "height_status": hstat, "room": rm,
                             "dwg_paint_h": t237r.get(rm, {}).get("dwg_paint_h") if rm else None})
            key = ref + "@" + floor
            if key in reveal_lines:
                lid = reveal_lines[key]["line_id"]
                binding[(oid, "IN", "FLOOR_STRIP" if fg else "SILL")] = lid
                binding[(oid, "OUT", "THRESHOLD" if fg else "SILL")] = lid
        elif kind in ("DOOR", "GATE"):
            t = num(t150.get(oid, {}).get("WALL_T_M"))
            openings.append({"id": oid, "kind": kind, "width_m": w if w is not None else num(t150.get(oid, {}).get(
                "WIDTH_M")), "height_m": h, "wall_t_m": t, "height_status": hstat or t150.get(oid, {}).get(
                "HEIGHT_STATUS"), "room": ";".join(sz.get("rooms", []))})
        elif kind == "OPENING":
            t = num(t150.get(oid, {}).get("WALL_T_M"))
            dev = 1.223795 if oid == "A-GF-01" else None   # T-238: ARC 2422 r 0.5673, 28.2 .. 151.8 deg, chord 1.000
            openings.append({"id": oid, "kind": "ARCH", "width_m": w, "springing_m": 2.20 if oid == "A-GF-01" else None,
                             "developed_m": dev, "wall_t_m": t, "height_status": t238.get(oid, {}).get("STATUS"),
                             "jamb_state": "HELD", "head_state": "HELD", "room": ";".join(sz.get("rooms", []))})
    rows = L.bind_lines(L.ledger(openings), binding)
    for r in rows:      # evidence status (WORKFLOW_CONTROLS s.5) beside the measurement state
        hs = (r.get("height_status") or "").upper()
        uses_h = r["component"] == "JAMBS" or (r["kind"] in ("DOOR", "GATE") and False)
        if r["state"] in ("HELD", "UNRESOLVED"):
            r["evidence"] = r["state"] if r["state"] == "HELD" else "UNKNOWN"
        elif r["state"] == "NONE":
            r["evidence"] = "DRAWING-CONFIRMED (no surface)"
        elif uses_h and hs.startswith("ASSUMED"):
            r["evidence"] = "ASSUMED — OWNER-APPROVED (Q-55 C door height 2.20)"
        else:
            r["evidence"] = "DRAWING-CONFIRMED"
    lines_used = {r["line_id"] for r in rows if r["line_id"] != L.NO_LINE}
    unbound = sorted(k for k in reveal_lines if reveal_lines[k]["line_id"] not in lines_used)
    tot = L.totals(rows)
    summary = {"identity": {"plan": sha8(a.plan), "rooms": sha8(a.rooms), "lines": sha8(a.lines)},
               "openings": len(openings), "rows": len(rows), "reveal_lines": len(reveal_lines),
               "lines_bound": len(lines_used), "lines_unbound": unbound,
               "totals": {f"{k[0]}:{k[1]}": v for k, v in sorted(tot.items())},
               "exterior_edge_ml_measured": L.exterior_edge_ml(rows)}
    with open(out / "REVEAL_LEDGER_T313.csv", "w", newline="", encoding="utf-8") as f:
        ks = ["opening", "kind", "side", "component", "depth_m", "m2", "ml", "state", "basis", "height_status", "evidence",
              "room", "line_id"]
        wr = csv.DictWriter(f, fieldnames=ks, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    with open(out / "WINDOW_DEPTHS_T313.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(geo[0]))
        wr.writeheader()
        wr.writerows(geo)
    # ---- reconciliation of the exterior reveal EDGE (arris) m.l with the merged corners ledger (T-162 r2, MERGED
    # 4cc2847: 137.110 measured + 32.200 ASSUMED; the register's 189.630 is the superseded r1 figure)
    sys.path.insert(0, str(RES / "agents_t162"))
    import t162_alsenan_corners as K   # noqa: E402
    import t162_corners as KC          # noqa: E402
    per_t162 = KC.opening_arrises([(o, w, h, st, s) for o, f, sd, w, h, st, s in K.OPENINGS])
    edge = {}
    for r in rows:
        if r["side"] == "OUT":
            e = edge.setdefault(r["opening"], {"ml": 0.0, "open": []})
            if r["state"] == "MEASURED":
                e["ml"] += r["ml"]
            elif r["state"] != "NONE":
                e["open"].append(r["component"])
    rec = []
    for o, f, sd, w, h, st, s in K.OPENINGS:
        old = per_t162["per"][o]
        old_known = KC.opening_reveal_ml(w, h, s)[0] if old is None else old
        kind = "DOOR" if o.startswith("D-") else "WINDOW"
        if kind == "DOOR":
            new, cause = None, "door: one reveal through the wall (UP-FIN-PLASTER-001); arris 2 h + w at the outer " \
                               "face stays in the corners line (Q-55 C height), not re-derived here"
        else:
            e = edge.get(o, {"ml": None, "open": ["ALL"]})
            new = round(e["ml"], 6) if not e["open"] else None
            cause = "open components " + "/".join(e["open"])
            if new is not None:
                op = next(x for x in openings if x["id"] == o)
                parts = []
                if h is None and op.get("height_m") is not None:
                    parts.append(f"jambs newly established 2 x {op['height_m']:.2f} = +{2 * op['height_m']:.3f}")
                if s and op["kind"] == "FLOOR_GLAZING":
                    parts.append(f"floor-level opening: no sill arris -{w:.3f}")
                cause = "; ".join(parts) or "same composition (T-162 heights confirmed)"
        rec.append({"opening": o, "t162_status": st, "t162_ml": None if old is None else round(old, 6),
                    "t162_known_part_ml": round(old_known, 6), "t313_ml": new,
                    "delta_ml": None if new is None else round(new - old_known, 6), "cause": cause})
    t162_measured = round(per_t162["measured"], 3)
    with open(out / "EDGE_RECONCILIATION_T313.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rec[0]))
        wr.writeheader()
        wr.writerows(rec)
    summary["edge_reconciliation"] = {
        "t162_r2_measured_ml": t162_measured, "t162_r2_assumed_ml": round(per_t162["assumed"], 3),
        "register_r1_ml": 189.630, "r1_minus_r2": round(189.630 - t162_measured, 3),
        "t313_windows_measured_ml": round(sum(x["t313_ml"] for x in rec if x["t313_ml"] is not None), 6),
        "t162_known_part_same_openings_ml": round(sum(x["t162_known_part_ml"] for x in rec if x["t313_ml"] is not None),
                                                  6),
        "openings_open": [x["opening"] for x in rec if x["t313_ml"] is None]}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
