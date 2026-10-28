"""T-313 read-only run on the development villa (Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip).
Every output goes to --out (outside the repository); the committed CSVs carry ids, lengths and states only (no
coordinates, no names).

    python3 -I research/agents_t313/t313_alsenan.py <P7757.dxf> <ARCH_ROOMS.json of an engine run> \
        <V3_0_xx_BOQ_LINES.json of the candidate of record> --out <scratch>/t313

r2 (Verifier 2026-10-28 rejection): the candidate RECORD (json, every item family) is searched by physical element for
every census opening (floor + engine OP id from T-249, or the engine door ref) before a component is called NO_LINE:
the door reveals live in FIN.PLASTER 'door jambs and head' (UP-FIN-PLASTER-001), bound and reconciled per door; the
window sill / threshold rows in ARCH.WINDOW_REVEAL; every other line on an opening is listed with its physical role
(FAMILY_SEARCH_T313.csv) so a lane I consumer sees what is already carried.

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
import re
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


OP_RE = re.compile(r"(?<![A-Z])(C?OP-\d{3})")
DOOR_RE = re.compile(r"(DOOR-(?:GF|1F|2F)-[0-9a-f]{8})")


def family_search(lines, inv):
    """every candidate line of ANY item family tied to a census opening by its floor + engine OP id (room / element id),
    by the engine door ref, or (strip lines without an opening id) by a source entity handle of the census symbol
    (T-249 HANDLES); -> {census id: [hit]}
    (ids, codes, states and quantities only)."""
    by_op, by_ref, by_h = {}, {}, {}
    for r in inv:
        for hd in r.get("HANDLES", "").split():
            by_h[hd.upper()] = r["ID"]
        for tok in r["ENGINE_REF"].replace("/", " ").split():
            if OP_RE.fullmatch(tok):
                by_op[(r["FLOOR"], tok)] = r["ID"]
            elif DOOR_RE.fullmatch(tok):
                by_ref[tok] = r["ID"]
    out = {}
    for x in lines:
        loc = x.get("location") or {}
        text = " ".join(str(loc.get(k) or "") for k in ("room_id", "element_id"))
        cids = {by_op[(loc.get("floor"), m)] for m in OP_RE.findall(text) if (loc.get("floor"), m) in by_op}
        cids |= {by_ref[m] for m in DOOR_RE.findall(text) if m in by_ref}
        if "-STRIP-" in str(loc.get("room_id") or "") and not OP_RE.findall(text):
            # an opening strip line with no engine opening id (door closure / unattributed strip): tie it by the
            # census symbol handles among its source entities (room lines also list window handles as boundaries,
            # so the handle tie is used for strip lines only)
            ents = (((x.get("source") or {}).get("entities") or {}).get("entities") or [])
            cids |= {by_h[str(e.get("handle", "")).upper()] for e in ents if str(e.get("handle", "")).upper() in by_h}
        br = x.get("bounded_range") or None
        calc = (x.get("calculation") or {})
        for cid in sorted(cids):
            ops = OP_RE.findall(text)
            out.setdefault(cid, []).append({
                "line_id": x["line_id"], "item_code": x["item_code"], "floor": loc.get("floor"),
                "op": ops[0] if ops else None, "engine_ref": (ops or DOOR_RE.findall(text) or [None])[0],
                "evidence_state": x.get("evidence_state"), "measured_net": x.get("measured_net"),
                "range": [br["low"], br["high"]] if br else None, "range_basis": br.get("basis") if br else None,
                "physical_element": x.get("physical_element"), "inputs": calc.get("inputs") or {}})
    for v in out.values():          # one hit per line and opening (a line can name its OP twice)
        seen, keep = set(), []
        for h in v:
            if h["line_id"] not in seen:
                seen.add(h["line_id"])
                keep.append(h)
        v[:] = keep
    return out


ROLES = {
    "ARCH.WINDOW": "the window unit (nr), not a surface",
    "ARCH.PASSAGE": "the opening as a passage (nr), not a surface",
    "ARCH.DOOR": "the door leaf / set (nr), not a surface",
    "ARCH.WINDOW_REVEAL": "window strip line",
    "ARCH.THRESHOLD": "floor-level strip across the opening (a floor / threshold element; a door or an arch has no "
                      "sill reveal, so not a reveal component of this ledger)",
    "FIN.MARBLE.THRESHOLD": "floor-level strip across the opening (threshold finish), not a reveal component",
    "FIN.FLOOR.PORCELAIN": "floor finish through the opening (doorway strip), not a reveal component",
    "FIN.CEILING": "soffit / ceiling surface, not a reveal component",
}


def role_of(h):
    c = h["item_code"]
    if c.startswith("DOOR."):
        return "OTHER ELEMENT: the door set (nr), not a surface"
    if c.startswith("FIN.WP."):
        return "OTHER ELEMENT: waterproofing at the opening (WP family owns it), not a reveal surface"
    return "OTHER ELEMENT: " + ROLES.get(c, "not a reveal component (checked: no jamb / head / sill surface)")


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
    rec_doc = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    cand = rec_doc if isinstance(rec_doc, list) else rec_doc["lines"]
    reveal_lines = {x["location"]["room_id"].split("-STRIP-")[1] + "@" + x["location"]["floor"]: x for x in cand
                    if x["item_code"] == "ARCH.WINDOW_REVEAL"}
    search = family_search(cand, inv)

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
    # ---- doors: the reveal through the wall is carried by FIN.PLASTER 'door jambs and head' (r2)
    door_lines, carried = {}, {}
    for oid, hits in search.items():
        pl = [h for h in hits if h["item_code"] == "FIN.PLASTER" and h["physical_element"] == "door jambs and head"]
        if len(pl) > 1:
            raise SystemExit(f"{oid}: two door plaster lines {[h['line_id'] for h in pl]}")
        if pl:
            door_lines[oid] = pl[0]
            for comp in ("JAMBS", "HEAD"):
                binding[(oid, "THROUGH", comp)] = pl[0]["line_id"]
                carried[(oid, "THROUGH", comp)] = ("FIN.PLASTER", pl[0]["line_id"])
    rows = L.bind_lines(L.ledger(openings), binding)
    door_rec = []
    for oid, h in sorted(door_lines.items()):
        r = L.reconcile_line(rows, oid, ("JAMBS", "HEAD"), {"line_id": h["line_id"], "family": "FIN.PLASTER",
                                                          "measured": h["measured_net"], "range": h["range"]})
        op = next(x for x in openings if x["id"] == oid)
        inp = h["inputs"]
        diff = []
        for k_l, k_c in (("wall_t_m", "wall_t_m"), ("width_m", "width_m"), ("height_m", "height_m")):
            if inp.get(k_c) is not None and op.get(k_l) is not None and abs(float(inp[k_c]) - float(op[k_l])) > 1e-6:
                diff.append(f"{k_l} ledger {op[k_l]} vs line {inp[k_c]}")
        cause = "; ".join(diff) or ("same t / w / h as the line" if r["verdict"] == "EQUAL" else
                                     h.get("range_basis") or "")
        door_rec.append({"opening": oid, "floor": h["floor"], "engine_op": h["op"], "line_id": h["line_id"],
                         "line_state": h["evidence_state"], "line_m2": h["measured_net"],
                         "line_low": h["range"][0] if h["range"] else None,
                         "line_high": h["range"][1] if h["range"] else None,
                         "line_t": inp.get("wall_t_m"), "line_w": inp.get("width_m"), "line_h": inp.get("height_m"),
                         "line_h_state": inp.get("height_state"), "ledger_t": op.get("wall_t_m"),
                         "ledger_w": op.get("width_m"), "ledger_h": op.get("height_m"),
                         "ledger_m2": r["ledger_m2"], "residual_m2": r["residual_m2"], "verdict": r["verdict"],
                         "cause": cause})
    missing = L.book_missing(rows, carried)
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
    summary = {"identity": {"plan": sha8(a.plan), "rooms": sha8(a.rooms), "record": sha8(a.lines),
                            "record_lines": len(cand)},
               "openings": len(openings), "rows": len(rows), "reveal_lines": len(reveal_lines),
               "lines_bound": len(lines_used), "lines_unbound": unbound,
               "totals": {f"{k[0]}:{k[1]}": v for k, v in sorted(tot.items())},
               "exterior_edge_ml_measured": L.exterior_edge_ml(rows),
               "door_lines_bound": len(door_lines),
               "door_reconciliation": {v: sum(1 for d in door_rec if d["verdict"] == v)
                                       for v in sorted({d["verdict"] for d in door_rec})},
               "door_ledger_m2_in_line": round(sum(d["ledger_m2"] for d in door_rec if d["ledger_m2"] is not None), 6),
               "door_line_m2_provisional": round(sum(d["line_m2"] for d in door_rec if d["line_m2"] is not None), 6),
               "missing_scope": {f"{k[0]}:{k[1]}:{k[2]}": v for k, v in sorted(missing.items())},
               "missing_scope_m2": round(sum(v["m2"] for v in missing.values()), 6),
               "family_lines_on_openings": {}}
    for hits in search.values():
        for h in hits:
            fam = summary["family_lines_on_openings"]
            fam[h["item_code"]] = fam.get(h["item_code"], 0) + 1
    summary["family_lines_on_openings"] = dict(sorted(summary["family_lines_on_openings"].items()))
    with open(out / "DOOR_PLASTER_RECONCILIATION_T313.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(door_rec[0]))
        wr.writeheader()
        wr.writerows(door_rec)
    bound_ids = {r["line_id"] for r in rows}
    with open(out / "FAMILY_SEARCH_T313.csv", "w", newline="", encoding="utf-8") as f:
        ks = ["opening", "floor", "engine_ref", "item_code", "line_id", "evidence_state", "measured_net", "low", "high",
              "physical_element", "role"]
        wr = csv.DictWriter(f, fieldnames=ks, extrasaction="ignore")
        wr.writeheader()
        for oid in [r["ID"] for r in inv]:
            for h in search.get(oid, []):
                wr.writerow(dict(h, opening=oid, low=h["range"][0] if h["range"] else None,
                                 high=h["range"][1] if h["range"] else None,
                                 role=("BOUND: " + ("door reveal jambs + head (UP-FIN-PLASTER-001)"
                                                    if h["item_code"] == "FIN.PLASTER" else
                                                    "window sill / threshold rows"))
                                 if h["line_id"] in bound_ids else role_of(h)))
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
