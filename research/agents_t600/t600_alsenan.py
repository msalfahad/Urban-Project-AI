"""T-600 development-villa run (research, unwired): the GF / 1F column-beam PAIR RESIDUAL left by T-599
(UP-CONC-JOINT-001 1.0.0) split into physical causes by column mark and beam mark (R-T600-1 .. 3), the GF B7 row
(F-C-T590-2) traced inside it, the column JOINT_HEAD readings T-551 / T-572 / T-576 reconciled member by member, and
the 2F 0.420 m3 cited from the Checker's P02 verdict (F-C-P02-1, not re-derived).

    .work/venv/bin/python -I research/agents_t600/t600_alsenan.py --freelancer .work/private/concrete_rebar.xlsx \
        --bands .work/private/t600/bands.json --dxf .work/private/st7757.dxf [--write]

bands.json: `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <out>`.
Inputs: the merged T-545 run (beam marks, his section, his through-support per mark, R-T395-4 allowance items, T-229
support input) re-run on the private workbook; the merged T-551 reader (V3.0.58 column classes, A, D_ctrl, his column
rows per mark); T-394 member -> line binding; T-576 B7 complete allowance (committed); ST7757 dxf outlines by handle
(S-COL.BON, read only in .work/private). Tracked output: out/T600_PAIR_RESIDUAL.json / .md: engine and drawing figures
and terms in m3 per column mark / beam mark; no row, length or count of the freelancer.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t545"))
sys.path.insert(0, str(RES / "agents_t551"))
import t600_rules as R  # noqa: E402

OUT_JSON = HERE / "out" / "T600_PAIR_RESIDUAL.json"
OUT_MD = HERE / "out" / "T600_PAIR_RESIDUAL.md"
T394 = RES / "agents_t394" / "summary_t394.json"
T576 = RES / "agents_t576" / "out" / "T576_COLUMN_CAUSES.json"
D = Decimal
STOREYS = ("GF", "1F")
# statement V7 / T-599 per-storey figures this run must reproduce (reference - engine, m3)
T_RECORD = {"GF": D("2.901714"), "1F": D("1.593362")}
J_RECORD = {"GF": D("2.28125"), "1F": D("0.385")}
B7_UNTRACED = D("0.120452")
# T-576 R-T576-3: B7 closing faces read on the drawing (curved / ledger-only pieces have no T-229 end record);
# carriers at their drawn widths; the two straight-piece column ends are read here from the outlines
B7_CARRIERS = (("BAND0006 end", "B8 BAND0003", "0.20"), ("BAND0006 end", "CB1 BAND0041.2", "0.35"),
               ("ring NW arc 2EE", "B8 face 46D", "0.20"), ("ring SW arc 2EF", "B8 face 46D", "0.20"),
               ("ring SW arc 2EF", "B17 face 42D", "0.45"), ("ring SE arc 312", "B17 face 42D", "0.45"),
               ("ring SE arc 312", "CB1 face 2A9", "0.35"), ("ring NE arc 313", "CB1 face 2A9", "0.35"))
B7_COLUMN_PIECE = "GF:BAND0025.1"
LEDGER_BESIDE: set = set()
BEYOND_SEARCH_M = 1.5          # R-T600-2: a piece ending at a carried member only: first real outline within this


def d6(x):
    return R.d6(x)


# ================================================================================================= inputs
def outlines_from_dxf(path, handles):
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(path)
    out = {}
    for h in handles:
        e = doc.entitydb.get(h)
        if e is None:
            continue
        b = bbox.extents([e])
        out[h] = (b.extmin.x / 1000.0, b.extmin.y / 1000.0, b.extmax.x / 1000.0, b.extmax.y / 1000.0)
    return out


def t119_dlow():
    """line id -> printed lower controlling depth (T-119 D_ctrl of the settled members) for D_ctrl-open columns."""
    import csv
    t119 = {r["id"]: r for r in csv.DictReader((RES / "agents_t119" / "COLUMNS_TO_CONTROLLING_MEMBER.csv")
                                               .open(encoding="utf-8"))}
    out = {}
    for r in json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]:
        t = t119.get(r.get("t119_id") or "")
        if t and t["D_ctrl"]:
            out[r["line_id"]] = D(t["D_ctrl"])
    return out


T119_DLOW: dict = {}


def column_kinds(freelancer):
    """(storey, handle) -> {kind REC / OPEN / HELD, mark, joint m3 or None, A, d_ctrl, line}. REC = the compared set of
    the record (T-551): RELEASED, D_ctrl known, a mark his rows carry."""
    import t551_alsenan as C
    cols = C.column_lines()
    hc, _ = C.his_rows(freelancer)
    hm = {st: defaultdict(int) for st in ("GF", "1F", "2F")}
    for st in hm:
        for r in hc[st]:
            lab = r["label"]
            if lab.startswith("PC"):
                lab = "P.C %dx%d" % (round(float(r["b"]) * 100), round(float(r["c"]) * 100))
            hm[st][lab] += r["n"]
    member_of = {r["line_id"]: r["member"] for r in json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]}
    out = {}
    for c in cols:
        mem = c.get("member") or member_of.get(c["line_id"]) or ""
        if ":" not in mem or c["storey"] not in hm:
            continue
        h = mem.split(":", 1)[1]
        rec = {"mark": c["mark"], "line": c["line_id"], "class": c["class"]}
        if c["class"] == "RELEASED":
            rec.update(A=c["A"], d_ctrl=c["d_ctrl"])
            if c["d_ctrl"] is None:
                rec["kind"] = "OPEN"
            elif hm[c["storey"]][c["mark"]] > 0:
                rec["kind"] = "REC"
                rec["joint"] = c["A"] * D(str(c["d_ctrl"]))
            else:
                rec["kind"] = "NOROW"
        elif c["class"] == "HELD":
            rec["kind"] = "HELD"
        else:
            continue
        out[(c["storey"], h)] = rec
    return out


# ================================================================================================= zones
def _band(bands, piece):
    st, band = piece.split(":")
    p = bands.get(f"{band}@{st}")
    return p["pts"] if p else None


DXF_PATH: list = []
RING_FACE_BAND = {"46D": "BAND0003", "42D": "BAND0044.1", "2A9": "BAND0041.2"}
RING_SUPERSET_HALF_W = 0.20    # census only: a 0.40 strip centred on the drawn ring edge holds the 0.20 ring either side


def b7_census_poly(bands, where, who, st):
    """Plan polygon of a B7 closing-face carrier for the node census (R-T600-1 r2). The capacity stays T-576's
    (verified). Straight piece BAND0006: its drawn crossing. Ring arcs: the tangent strip at the arc end on the face
    (superset, both sides of the drawn edge) crossed with the face member's band."""
    import math
    import ezdxf
    if where.startswith("BAND0006"):
        carrier = who.split(" ")[1]
        return R.crossing(_band(bands, f"{st}:BAND0006"), _band(bands, f"{st}:{carrier}"))["poly"], \
            "drawn crossing of BAND0006 (capacity T-576)"
    arc_h = where.split(" ")[-1]
    face_h = who.split(" ")[-1]
    doc = ezdxf.readfile(DXF_PATH[0]) if not hasattr(b7_census_poly, "_doc") else b7_census_poly._doc
    b7_census_poly._doc = doc
    arc, face = doc.entitydb.get(arc_h), doc.entitydb.get(face_h)
    fx0, fy0, fx1, fy1 = (face.dxf.start.x / 1000, face.dxf.start.y / 1000, face.dxf.end.x / 1000,
                          face.dxf.end.y / 1000)
    best = None
    for sgn, ang, pt in ((-1, arc.dxf.start_angle, arc.start_point), (1, arc.dxf.end_angle, arc.end_point)):
        px, py = pt.x / 1000, pt.y / 1000
        dist = abs((fx1 - fx0) * (fy0 - py) - (fx0 - px) * (fy1 - fy0)) / math.hypot(fx1 - fx0, fy1 - fy0)
        if best is None or dist < best[0]:
            best = (dist, sgn, ang, px, py)
    dist, sgn, ang, px, py = best
    if dist > 0.002:
        raise R.Refused(f"{arc_h}: no arc end on face {face_h}")
    from shapely.geometry import Polygon
    cx, cy, r = arc.dxf.center.x / 1000, arc.dxf.center.y / 1000, arc.dxf.radius / 1000
    w = float(next(x[2] for x in B7_CARRIERS if x[0] == where and x[1] == who))
    sweep = w / r                                   # the ring continued past its drawn end by the billed width
    h = RING_SUPERSET_HALF_W
    angs = [math.radians(ang) + sgn * sweep * i / 16 for i in range(17)]
    outer = [(cx + (r + h) * math.cos(t), cy + (r + h) * math.sin(t)) for t in angs]
    inner = [(cx + (r - h) * math.cos(t), cy + (r - h) * math.sin(t)) for t in reversed(angs)]
    return Polygon(outer + inner), (f"ring continued {w} m past its drawn end ({round(px, 3)}, {round(py, 3)}) on "
                                    f"face {face_h}, +-{h} m about the drawn edge (census superset; capacity T-576)")


def _end_record(sup, piece, member):
    for e in sup["ends"]:
        if e["piece"] == piece and any(m[0] == member for m in e["members"]):
            return e
    return None


def _beyond_support(sup, rects, pts, axis, storey, piece_end_hint):
    """R-T600-2: the first COLUMN_BELOW outline the drawn band reaches beyond a carried member (within 1.5 m)."""
    from shapely.geometry import box
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    cx, cy = piece_end_hint
    if axis == "Y":
        up = abs(cy - hi_y) < abs(cy - lo_y)
        probe = box(lo_x, hi_y, hi_x, hi_y + BEYOND_SEARCH_M) if up else box(lo_x, lo_y - BEYOND_SEARCH_M, hi_x, lo_y)
    else:
        right = abs(cx - hi_x) < abs(cx - lo_x)
        probe = box(hi_x, lo_y, hi_x + BEYOND_SEARCH_M, hi_y) if right else box(lo_x - BEYOND_SEARCH_M, lo_y, lo_x, hi_y)
    best = None
    for h, o in sup["outlines"].items():
        if o["storey"] != storey or o["kind"] != "COLUMN_BELOW" or h not in rects:
            continue
        r = box(*rects[h])
        if r.intersects(probe) and r.intersection(probe).area > 1e-6:
            dist = r.distance(box(lo_x, lo_y, hi_x, hi_y))
            if best is None or dist < best[0]:
                best = (dist, h)
    return best[1] if best else None


def ledger_beside():
    """Gaps whose beside-support strip the engine beam line already bills (T-229 SUPPORT_CUT_BESIDE in the T-252
    ledger run): {(piece a, piece b)}. His excess over the engine cannot lie there (R-T600-2)."""
    import csv
    import re
    out = set()
    for r in csv.DictReader((RES / "agents_t252" / "LEDGER_T252.csv").open(encoding="utf-8")):
        if r["status"] == "SUPERSEDED_R2":
            continue
        for cell in r.values():
            for mm in re.finditer(r"SUPPORT_CUT_BESIDE \(to ((?:GF|1F|2F):BAND[0-9.]+)\)", cell or ""):
                for p in re.split(r"[;|]", r["pieces"]):
                    out.add(tuple(sorted((p.strip(), mm.group(1)))))
    return out


def mark_zones(st, m, sup, bands, rects, kinds):
    """For one beam mark: column zones [(handle, zone dict)] and carrier items [(key, m3)], from its allowance items
    re-read on the drawing (R-T600-2). Returns (col_zones, carriers, notes)."""
    b, Dd = m["split"]["his_section"]
    b, Dd = D(str(b)), D(str(Dd))
    col_zones, carriers, notes = [], [], []
    items = m["allow_items"]
    if st == "GF" and m["mark"] == "B7":
        items = [it for it in items if it[0] == "END_COLUMN"]          # straight piece column ends (T-229)
        for where, who, w in B7_CARRIERS:
            key = f"B7 {where} -> {who}"
            poly, info = b7_census_poly(bands, where, who, st)
            carriers.append({"key": key, "mark": "B7", "m3": d6(D(w) * b * Dd), "poly": poly, "D": Dd, "b": b,
                             "w_drawn": None, "how": info, "L": w})
        notes.append("B7: complete closing-face set of T-576 (R-T576-3): curved / ring pieces have no T-229 end "
                     "record; carriers at drawn widths")
    for kind, piece, mem, ext in items:
        if kind == "END_BEAM":
            e = _end_record(sup, piece, mem)
            beam = next((x[0] for x in e["members"] if x[1] == "BEAM"), mem) if e else mem
            key = f"{m['mark']} {piece} -> {beam}"
            fp, cp = _band(bands, piece), _band(bands, beam)
            try:
                x = R.crossing(fp, cp)
                carriers.append({"key": key, "mark": m["mark"], "m3": R.entry_m3(x["L"], b, Dd), "poly": x["poly"],
                                 "D": Dd, "b": b, "w_drawn": x["w_framing"], "L": str(d6(x["L"])),
                                 "how": f"DRAWN_CROSSING sin {round(x['sin'], 3)} (w_carrier "
                                        f"{round(x['w_carrier'], 3)} / sin), T-229 recorded {ext}"})
            except R.Refused as why:
                if "parallel" not in str(why):
                    raise
                carriers.append({"key": key, "mark": m["mark"], "m3": d6(D(str(ext)) * b * Dd), "poly": None,
                                 "D": Dd, "b": b, "w_drawn": None, "L": str(ext),
                                 "how": "RECORDED_PARALLEL (collinear members: no crossing; T-229 recorded extent)"})
            continue
        pts = _band(bands, piece if kind == "END_COLUMN" else piece.split("|")[0])
        ax = R.axis_of(pts) if pts else "NONE"
        col = mem
        tag = kind
        if kind == "END_COLUMN":
            e = _end_record(sup, piece, mem)
            below = [x[0] for x in e["members"] if x[1] == "COLUMN_BELOW"] if e else []
            carried = sup["outlines"].get(mem, {}).get("kind") == "CARRIED_COLUMN"
            if carried and below:
                col, tag = below[0], "END_COLUMN (carried member over a real support: the support is read)"
            elif carried:
                r = rects[mem]
                col = _beyond_support(sup, rects, pts, ax, st, ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2))
                tag = "END_AT_CARRIED (beam billed to the receiving face, T-229): support beyond read"
                if col is None:
                    notes.append(f"{m['mark']} {piece}: carried end, no real support within 1.5 m: no zone")
                    continue
        elif sup["outlines"].get(mem, {}).get("kind") == "CARRIED_COLUMN":
            notes.append(f"{m['mark']} {piece}: gap under carried member {mem}: the beam line bills it (T-229), "
                         "not a support zone")
            continue
        key = f"{m['mark']}|{piece}|{kind}"
        if col not in rects or not pts:
            raise R.Refused(f"{m['mark']} {piece}: no drawn outline / band for support {col}")
        else:
            inside, beside, along = R.strip_zone(pts, rects[col], R.direction_of(pts))
            if kind == "GAP" and tuple(sorted(piece.split("|"))) in LEDGER_BESIDE:
                billed = R.d6(Decimal(repr(beside.area)) * Dd)
                notes.append(f"{m['mark']} {piece} at {col}: beside-support strip {billed} m3 billed by the engine "
                             "beam line (T-229 SUPPORT_CUT_BESIDE in the ledger run): not a zone of his excess")
                beside = beside.difference(beside)
            zone = {"key": key, "poly": inside, "beside": beside, "D": Dd, "axis": ax, "b": b,
                    "along_m": D(repr(round(along, 6))), "recorded_m": D(str(ext))}
        zone["tag"] = tag
        col_zones.append((col, zone))
    return col_zones, carriers, notes


# ================================================================================================= build
def build(freelancer, bands_path, dxf_path):
    import t545_alsenan as A
    runs, marks, his, sub, his_slab, sup, db, lines = A.run_build(freelancer, bands_path)
    bands = json.loads(Path(bands_path).read_text(encoding="utf-8"))
    kinds = column_kinds(freelancer)
    rects = outlines_from_dxf(dxf_path, list(sup["outlines"]))
    T119_DLOW.clear()
    T119_DLOW.update(t119_dlow())
    LEDGER_BESIDE.clear()
    LEDGER_BESIDE.update(ledger_beside())
    DXF_PATH[:] = [dxf_path]
    doc = {"schema": "T600_PAIR_RESIDUAL_V2",
           "candidate": "ARCH_TAKEOFF_V3.0.58 (structural lines = V3.0.57 LINE_INDEX); NOT RELEASED",
           "rule": "R-T600-1 .. 3 r2 (PROPOSED; carrier node once, SHORT not a cause); UP-CONC-JOINT-001 1.0.0 (LEAD_ADOPTED)",
           "note": "engine / drawing figures and terms in m3; no row, length or count of the freelancer",
           "storeys": {}}
    for st in STOREYS:
        smarks = [m for m in marks if m["floor"] == st and d6(m["length"]["THROUGH_SUPPORT"]) != 0]
        T_marks = {}
        col_z = defaultdict(list)
        mark_terms = {}
        notes = []
        entries = []
        zone_polys = []
        sect = {}
        for m in smarks:
            t = -d6(m["length"]["THROUGH_SUPPORT"])
            if st == "GF" and m["mark"] == "B7":
                t += B7_UNTRACED                                   # T-576: the whole B7 excess is through-support
            T_marks[m["mark"]] = t
            sect[m["mark"]] = tuple(D(str(x)) for x in m["split"]["his_section"])
            cz, car, nt = mark_zones(st, m, sup, bands, rects, kinds)
            notes += nt
            zsum = Decimal(0)
            for col, z in cz:
                col_z[col].append(z)
                zone_polys.append((z["key"], col, z["poly"]))
                zsum += sum(R.zone_m3(z), Decimal(0))
            entries += car
            mark_terms[m["mark"]] = {"T_m3": str(t), "zones_m3": str(d6(zsum))}
        # R-T600-1 r2: carrier capacity once per physical node, across marks
        nodes = R.carrier_nodes(entries)
        node_of = {k: nd for nd in nodes for k in nd["keys"]}
        ent = {e["key"]: e for e in entries}
        for k, z_key, poly in [(e["key"], None, e["poly"]) for e in entries]:
            for zk, col, zp in zone_polys:
                if poly is not None and poly.intersection(zp).area > R.NODE_AREA_MIN:
                    notes.append(f"carrier {k} shares {round(poly.intersection(zp).area, 4)} m2 with column zone {zk}")
        mark_nodes = {mk: set() for mk in mark_terms}
        for e in entries:
            mark_nodes[e["mark"]].add(node_of[e["key"]]["id"])
        groups = R.mark_groups(mark_nodes)
        group_of = {mk: g for g in groups for mk in g}
        for mk, mt in mark_terms.items():
            mine = [e for e in entries if e["mark"] == mk]
            excl = sum((node_of[e["key"]]["capacity_m3"] for e in mine if not node_of[e["key"]]["shared"]),
                       Decimal(0))
            shared = sum((d6(e["m3"]) for e in mine if node_of[e["key"]]["shared"]), Decimal(0))
            lo, hi = R.short_bounds(D(mt["zones_m3"]) + excl, shared, D(mt["T_m3"]))
            mt.update({"carriers": [{"key": e["key"], "entry_m3": str(d6(e["m3"])), "L_m": str(e["L"]),
                                     "how": e["how"], "node": node_of[e["key"]]["id"],
                                     "node_shared": node_of[e["key"]]["shared"]} for e in mine],
                       "capacity_exclusive_m3": str(d6(D(mt["zones_m3"]) + excl)),
                       "capacity_shared_entries_m3": str(shared), "group": " + ".join(group_of[mk]),
                       "short_bounds_m3": [str(lo), str(hi)]})
            b, Dd = sect[mk]
            alone = len(group_of[mk]) == 1
            if alone and not shared and R.short_is_zero(lo, b, Dd):
                mt["proposal"] = ("PER-MARK: his row runs through every zone and carrier of the mark (|SHORT| "
                                  f"{abs(lo)} <= 0.01 x b x D): column classes of this mark realised")
            elif alone and not shared and any(R.short_is_zero(lo - node_of[e["key"]]["capacity_m3"], b, Dd)
                                              for e in mine):
                mt["proposal"] = ("CONDITIONAL: SHORT equals one carrier entry within 0.01 x b x D: his row runs "
                                  "through the column zones and stops at the carrier face (not proved: the "
                                  "split is not unique)")
            else:
                mt["proposal"] = "NONE: capacity bound only; SHORT UNRESOLVED (his rows carry no location)"
        pend = []
        for nd in nodes:
            pend.append(("CARRIER_NODE", nd["id"], nd["capacity_m3"]))
        for g in groups:
            capg = sum((D(mark_terms[mk]["zones_m3"]) for mk in g), Decimal(0)) + sum(
                (nd["capacity_m3"] for nd in nodes if set(nd["marks"]) & set(g)), Decimal(0))
            Tg = sum((D(mark_terms[mk]["T_m3"]) for mk in g), Decimal(0))
            sh = R.mark_short(capg, Tg)
            if "SHORT" in sh:
                pend.append(("UNRESOLVED_SHORT", " + ".join(g), -sh["SHORT"]))
            else:
                pend.append(("BEYOND", " + ".join(g), -sh["BEYOND"]))
            for mk in g:
                mark_terms[mk]["group_capacity_m3"] = str(d6(capg))
                mark_terms[mk]["group_T_m3"] = str(d6(Tg))
                mark_terms[mk]["group_" + next(iter(sh))] = str(next(iter(sh.values())))
        node_rows = [{"id": nd["id"], "marks": nd["marks"], "shared": nd["shared"],
                      "capacity_m3": str(nd["capacity_m3"]), "entries_sum_m3": str(nd["entries_sum_m3"]),
                      "entered_more_than_once_m3": str(nd["entries_sum_m3"] - nd["capacity_m3"]),
                      "how": sorted({ent[k]["how"] for k in nd["keys"]})} for nd in nodes]
        terms = list(pend)
        columns = {}
        for col, zz in sorted(col_z.items()):
            info = kinds.get((st, col))
            o = sup["outlines"].get(col, {})
            kind = info["kind"] if info else ("CARRIED" if o.get("kind") == "CARRIED_COLUMN" else "NOLINE")
            joint = info.get("joint") if info and kind == "REC" else None
            ct = R.column_zone_terms(zz, col_rect=rects[col], joint=joint)
            mark = info["mark"] if info else "(no column line)"
            label = f"{mark} {col}"
            row = {"mark": mark, "handle": col, "kind": kind, "outline_mm": [o.get("w_mm"), o.get("d_mm")],
                   "beams": [{"key": z["key"], "tag": z["tag"], "axis": z["axis"], "D": str(z["D"]),
                              "along_m": str(z["along_m"]), "recorded_m": str(z["recorded_m"]),
                              "inside_m2": str(d6(D(repr(z["poly"].area)))),
                              "beside_m2": str(d6(D(repr(z["beside"].area))))} for z in zz],
                   **{k: str(v) for k, v in ct.items()}}
            if info and kind == "OPEN":
                dl = T119_DLOW[info["line"]]
                row["d_low_printed_m"] = str(dl)
                row["joint_at_lower_bound_m3"] = str(d6(info["A"] * dl))
                row["lower_bound_note"] = ("T-119 FRAMING_MEMBER_HELD_D_OPEN: the printed framing members give D_low; "
                                           "an unprinted held member may be deeper (open above, never below)")
            columns[label] = row
            terms.append(("OVERLAP_CROSSING", label, ct["OVERLAP_CROSSING"]))
            terms.append(("OVERLAP_REPEAT", label, ct["OVERLAP_REPEAT"]))
            terms.append(("BESIDE", label, ct["BESIDE"]))
            if kind == "REC":
                terms.append(("UNCOVERED", label, -ct["UNCOVERED"]))
            else:
                cls = {"OPEN": "OUTSIDE_SET_OPEN", "HELD": "OUTSIDE_SET_HELD"}.get(kind, "OUTSIDE_SET_NOLINE")
                v = ct["UNION"]
                if kind == "HELD":
                    v = R.held_term(v)
                terms.append((cls, label, v))
        # joint of the compared set: every REC column, also those no beam of his reaches
        J = sum((v["joint"] for (s, h), v in kinds.items() if s == st and v["kind"] == "REC"), Decimal(0))
        assert d6(J) == d6(J_RECORD[st]), (st, J)
        reached = {c.split(" ")[-1] for c in columns}
        for (s, h), v in sorted(kinds.items()):
            if s == st and v["kind"] == "REC" and h not in reached:
                label = f"{v['mark']} {h}"
                columns[label] = {"mark": v["mark"], "handle": h, "kind": "REC", "beams": [],
                                  "JOINT": str(d6(v["joint"])), "UNION": "0.000000",
                                  "UNCOVERED": str(d6(v["joint"])), "note": "no beam mark of his with a "
                                  "through-support term meets this column"}
                terms.append(("UNCOVERED", label, -d6(v["joint"])))
        # per-mark who-is-right only where the mark's row provably runs through (PER-MARK / CONDITIONAL)
        run_through = {mk for mk, mt in mark_terms.items() if mt["proposal"].startswith(("PER-MARK", "CONDITIONAL"))}
        prop_kind = {"REC": "RULE_DIFFERENCE: joint matched (his beam row bills the joint the engine column line "
                            "bills once, UP-CONC-JOINT-001); no quantity error",
                     "HELD": "HELD: column partner HELD (CONFLICT), matched joint stays HELD, never 0",
                     "OPEN": "RULE_DIFFERENCE at the printed LOWER_BOUND (D_ctrl open above)"}
        for mk in sorted(run_through):
            rows = []
            for lab, c in columns.items():
                for bz in c["beams"]:
                    if bz["key"].split("|")[0] != mk:
                        continue
                    others = sorted({x["key"].split("|")[0] for x in c["beams"]} - {mk})
                    p = prop_kind.get(c["kind"], "UNRESOLVED: support without a column line")
                    if D(c.get("OVERLAP_CROSSING", "0")) + D(c.get("OVERLAP_REPEAT", "0")) > 0 and others:
                        strict = {m for m in run_through if mark_terms[m]["proposal"].startswith("PER-MARK")}
                        if set(others) <= strict and mk in strict:
                            p += "; OVERLAP with " + ", ".join(others) + " realised: ENGINE_RIGHT (one solid, two rows)"
                        elif set(others) <= run_through:
                            p += ("; OVERLAP with " + ", ".join(others) + " ENGINE_RIGHT only if the CONDITIONAL "
                                  "run-through holds (PLAUSIBLE)")
                        else:
                            p += "; OVERLAP with " + ", ".join(others) + " not provable (other row may stop short)"
                    if D(bz["beside_m2"]) > 0:
                        p += "; BESIDE strip: named geometry (owner per line, T-229 / T-610)"
                    rows.append({"column": lab, "kind": c["kind"], "inside_m2": bz["inside_m2"],
                                 "beside_m2": bz["beside_m2"], "D": bz["D"], "proposal": p})
            mark_terms[mk]["per_column"] = rows
        T = sum(T_marks.values(), Decimal(0))
        exp_T = T_RECORD[st] + (B7_UNTRACED if st == "GF" else 0)
        assert d6(T) == d6(exp_T), (st, T, exp_T)
        resid = d6(T) - d6(J)
        by_class = R.pair_closure(resid, terms)
        doc["storeys"][st] = {
            "through_support_T_m3": str(d6(T)), "joint_head_J_m3": str(d6(J)), "residual_m3": str(resid),
            "statement_pair_residual_m3": str(d6(T_RECORD[st] - J_RECORD[st])),
            "b7_untraced_folded_m3": str(B7_UNTRACED) if st == "GF" else "0",
            "by_class_m3": by_class, "columns": columns, "beam_marks": mark_terms, "carrier_nodes": node_rows,
            "groups": [" + ".join(g) for g in groups],
            "terms": [[c, k, str(d6(v))] for c, k, v in terms if d6(v) != 0], "notes": sorted(set(notes))}
    doc["readings"] = readings(kinds)
    doc["storey_2F"] = cite_2f()
    doc["verdicts"] = verdicts(doc)
    return doc


# ================================================================================================= readings / 2F
def readings(kinds):
    """R-T600-3: the GF / 1F JOINT_HEAD of T-551 (record), T-572, T-576 and T-576 on 10E0 = C7, member by member."""
    out = {}
    rec = {st: {f"{v['mark']} {h}": d6(v["joint"]) for (s, h), v in kinds.items() if s == st and v["kind"] == "REC"}
           for st in STOREYS}
    low = {}
    for (s, h), v in kinds.items():
        if v["kind"] == "OPEN":
            low[(s, h)] = d6(v["A"] * D("0.75"))
    # the sets the three reports compared (their own text): T-572 = record less the CONFLICT-reading marks C3 / C8
    # (GF) ; T-576 (10E0 = C8) = T-572 + C7 at D_low (GF) / + P.C 20x50 at D_low (1F); T-576 (10E0 = C7) = T-572 +
    # C8 36E (GF) / + P.C 20x50 at D_low + C8 664 at D_low (1F)
    gf = rec["GF"]
    core = {k: v for k, v in gf.items() if not k.startswith(("C3 ", "C8 "))}
    sets = {"GF": {"T-551 (record)": gf, "T-572": core,
                   "T-576 (10E0 = C8)": {**core, "C7 368 (D_low 0.75, LOWER_BOUND)": low[("GF", "368")]},
                   "T-576 (10E0 = C7)": {**core, "C8 36E": gf["C8 36E"]}},
            "1F": {"T-551 (record)": rec["1F"], "T-572": rec["1F"],
                   "T-576 (10E0 = C8)": {**rec["1F"], "P.C 20x50 69D (D_low 0.75, LOWER_BOUND)": low[("1F", "69D")]},
                   "T-576 (10E0 = C7)": {**rec["1F"], "P.C 20x50 69D (D_low 0.75, LOWER_BOUND)": low[("1F", "69D")],
                                         "C8 664 (D_low 0.75, LOWER_BOUND)": low[("1F", "664")]}}}
    reported = {"GF": {"T-551 (record)": "2.28125", "T-572": "1.883750", "T-576 (10E0 = C8)": "2.033750",
                       "T-576 (10E0 = C7)": "2.075000"},
                "1F": {"T-551 (record)": "0.385", "T-572": "0.385000", "T-576 (10E0 = C8)": "0.460000",
                       "T-576 (10E0 = C7)": "0.595000"}}
    for st in STOREYS:
        out[st] = {}
        for name, s in sets[st].items():
            tot = sum(s.values(), Decimal(0))
            assert d6(tot) == d6(reported[st][name]), (st, name, tot)
            diff = R.reading_differences(sets[st]["T-551 (record)"], s)
            out[st][name] = {"joint_m3": str(d6(tot)), "minus_record_by_member_m3": {k: str(v) for k, v in diff.items()}}
    out["note"] = ("membership reconstructed from each report's own text and checked: every reported total is "
                   "reproduced exactly by these members; a member's joint is the same in every reading (A x D_ctrl, "
                   "or A x printed D_low labelled LOWER_BOUND)")
    return out


def cite_2f():
    return {"residual_m3": "0.420000", "source": "Checker verdict T-180 P02 2F (SCOREBOARD 2026-11-07 15:00, F-C-P02-1, "
            "own ST7757 read): his roof-beam lengths through the support-column footprints 0.564 m3 (B3 0.028 + B8 "
            "0.120 + B15 0.240 + B1 0.176) less one drawn, tagged B1 run with no row of his 0.144 m3 (COUNT, "
            "ENGINE_RIGHT); residual 0.000. Cited, not re-derived (Lead amendment).",
            "column_partner": "every 2F column line is HELD (D-39, T-551 HELD -3.381): J = 0, the 0.564 joint sits in "
                              "held column lines (OUTSIDE_SET_HELD), never 0"}


def verdicts(doc):
    return {
        "UNCOVERED": "ENGINE_RIGHT: the column head A x D_ctrl outside every beam strip of his; his columns stop at "
                     "one soffit depth, his beams are narrower than the column: that concrete is in none of his rows",
        "OVERLAP_CROSSING / OVERLAP_REPEAT": "ENGINE_RIGHT where his rows reach: one solid inside one column billed "
                                             "by two of his beam rows; the engine bills it once (column line)",
        "BESIDE": "named geometry: his strip beside a narrower column (beam wider than the column); owner per line "
                  "(T-229 / T-610), not a joint",
        "OUTSIDE_SET_OPEN / HELD / NOLINE": "RULE_DIFFERENCE matched joint whose column partner is outside the "
                                            "compared set (D_ctrl open, HELD line, no line): the joint exists once "
                                            "under UP-CONC-JOINT-001; HELD partners stay HELD, never 0",
        "CARRIER_NODE": "CAPACITY, entered once per physical node (r2): the drawn crossing of the framing strip with "
                        "the carrier strip on the framing axis (w_carrier / sin); a node entered by several marks "
                        "counts its depth-layered union once; realised only as far as his rows reach (SHORT)",
        "UNRESOLVED_SHORT": "NOT A CAUSE (r2): capacity minus his through-support volume per group of marks sharing a "
                            "node; his rows carry no location, so which zone / node he stops short of is UNRESOLVED; "
                            "per-mark bounds printed",
        "BEYOND": "his length beyond every drawn support zone of the mark: UNRESOLVED by mark unless named"}


# ================================================================================================= markdown
def markdown(doc):
    L = ["# T-600 column-beam pair residual by cause (generated)", "",
         f"Candidate {doc['candidate']}; {doc['rule']}. {doc['note']}.", ""]
    for st, s in doc["storeys"].items():
        L += [f"## {st}: T {s['through_support_T_m3']} - J {s['joint_head_J_m3']} = R {s['residual_m3']} m3 "
              f"(statement pair {s['statement_pair_residual_m3']} + B7 folded {s['b7_untraced_folded_m3']})", "",
              "| class | m3 |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in s["by_class_m3"].items()]
        L += ["", "| column | kind | zones | union | joint | overlap X / R | beside | uncovered |", "|---|---|---|---|---|---|---|---|"]
        for lab, c in s["columns"].items():
            L.append(f"| {lab} | {c['kind']} | {c.get('ZONES', '0')} | {c['UNION']} | {c.get('JOINT', '')} | "
                     f"{c.get('OVERLAP_CROSSING', '0')} / {c.get('OVERLAP_REPEAT', '0')} | {c.get('BESIDE', '0')} | "
                     f"{c.get('UNCOVERED', '')} |")
        L += ["", "| carrier node | marks | capacity | entries sum | entered more than once |", "|---|---|---|---|---|"]
        for n in s["carrier_nodes"]:
            L.append(f"| {n['id']} | {', '.join(n['marks'])} | {n['capacity_m3']} | {n['entries_sum_m3']} | "
                     f"{n['entered_more_than_once_m3']} |")
        L += ["", "| beam mark | T | zones | exclusive capacity | shared entries | SHORT bounds | group | proposal |",
              "|---|---|---|---|---|---|---|---|"]
        for mk, b in s["beam_marks"].items():
            L.append(f"| {mk} | {b['T_m3']} | {b['zones_m3']} | {b['capacity_exclusive_m3']} | "
                     f"{b['capacity_shared_entries_m3']} | {b['short_bounds_m3'][0]} .. {b['short_bounds_m3'][1]} | "
                     f"{b['group']} | {b['proposal']} |")
        for mk, b in s["beam_marks"].items():
            for r in b.get("per_column", []):
                L.append(f"- {mk} at {r['column']} ({r['kind']}, inside {r['inside_m2']} m2, beside {r['beside_m2']} m2,"
                         f" D {r['D']}): {r['proposal']}")
        if s["notes"]:
            L += [""] + [f"- {n}" for n in s["notes"]]
        L.append("")
    L += ["## JOINT_HEAD readings (R-T600-3)", ""]
    for st in STOREYS:
        for name, r in doc["readings"][st].items():
            L.append(f"- {st} {name}: {r['joint_m3']} m3; minus record by member {r['minus_record_by_member_m3']}")
    L += ["", f"## 2F (cited): {doc['storey_2F']['residual_m3']} m3. {doc['storey_2F']['source']} "
          f"{doc['storey_2F']['column_partner']}", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer", required=True)
    ap.add_argument("--bands", required=True)
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build(a.freelancer, a.bands, a.dxf)
    txt = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if a.write:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(txt, encoding="utf-8")
        OUT_MD.write_text(markdown(doc), encoding="utf-8")
    for st, s in doc["storeys"].items():
        print(st, s["residual_m3"], json.dumps(s["by_class_m3"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
