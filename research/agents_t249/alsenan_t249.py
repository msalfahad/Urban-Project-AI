"""T-249 development villa: the engine-independent opening inventory and its crosswalks.

Build (needs the private DXF, read-only; an optional engine run directory is used ONLY for the crosswalk, after the
inventory exists):
    python3 -I research/agents_t249/alsenan_t249.py build --dxf <P7757.dxf> [--engine-run <ARCH_TAKEOFF_V2.9 out dir>]
Check (the committed files are reproduced byte for byte from the same inputs):
    python3 -I research/agents_t249/alsenan_t249.py check --dxf <P7757.dxf> --engine-run <dir>

Sources of EXISTENCE (never the engine): plan door-leaf symbols (blocks carrying a swing arc; loose swing arcs), plan
glazing symbols (layer W clusters in a wall gap), the elevation features of research/agents_t194/ELEVATIONS_T194.csv
(T-194 MERGED: drawing reads of the NW / SE elevations from DXF DIMENSION entities and of the SW / NE scans), and the
DXF DIMENSION entities of the NW elevation for W03 / W18. The project issues no door / window schedule (designer D-07)
and draws no opening tag (0 TEXT / MTEXT / ATTRIB matching a W / D mark in model space or any block): the inventory ids
are therefore the census ids, attached AFTER the inventory by position (engine run) or by unique attributes.

No coordinate is written: rows carry entity handles, widths and relative positions only.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import inventory as INV  # noqa: E402

UNIT_M = 0.001                                   # P7757.dxf: 1 unit = 1 mm (T-198 own read: "+0.30" / "+4.30" 4000 apart)
REG_BLOCK = "A$C662819C0"                        # repeated on all three plans at one plan point (lower insert)
FRAMES_MM = {"GF": (-162500, -125000), "1F": (-207400, -169000), "2F": (-252300, -214000)}
PLAN_Y_MM = (-812000, -780000)
WINDOW_LAYER = "W"
SWING_LAYER = "D"
LOOSE_SWING_R_M = (0.55, 1.10)
# facade = the elevation seen from outside; coordinate grows left to right (T-194: all four bind unmirrored)
FACADES = {"SW": {"axis": "X", "sign": -1}, "NE": {"axis": "X", "sign": 1},
           "NW": {"axis": "Y", "sign": 1}, "SE": {"axis": "Y", "sign": -1}}
T194 = ROOT / "research" / "agents_t194" / "ELEVATIONS_T194.csv"
T198 = ROOT / "research" / "agents_t198" / "OPENINGS_T198.csv"
OUT = {"inventory": HERE / "OPENINGS_T249.csv", "crosswalk": HERE / "CROSSWALK_T249.csv",
       "delta": HERE / "DELTA_T249.csv", "summary": HERE / "summary.json"}
TAG_RE = re.compile(r"^\s*[WwDd]\s*-?\s*\d{1,3}[A-Za-z]?\s*$")


def _csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- DXF reads

def read_dxf(path):
    import ezdxf
    from ezdxf import bbox

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    def layer(e):
        try:
            return e.dxf.layer
        except Exception:                        # RTEXT carries no layer attribute in ezdxf
            return None

    def storey_of(x, y):
        if not (PLAN_Y_MM[0] <= y <= PLAN_Y_MM[1]):
            return None
        for s, (a, b) in FRAMES_MM.items():
            if a <= x <= b:
                return s
        return None

    reg = {}
    for e in msp.query("INSERT"):
        if e.dxf.name == REG_BLOCK:
            s = storey_of(e.dxf.insert.x, e.dxf.insert.y)
            if s and (s not in reg or e.dxf.insert.y < reg[s][1]):
                reg[s] = (e.dxf.insert.x, e.dxf.insert.y)
    if set(reg) != set(FRAMES_MM):
        raise SystemExit(f"registration block {REG_BLOCK} not found on every plan: {sorted(reg)}")

    # tags: none expected; counted so the claim is reproducible
    tags = 0
    for e in msp:
        t = e.dxftype()
        if t == "TEXT" and TAG_RE.match(e.dxf.text or ""):
            tags += 1
        elif t == "MTEXT" and TAG_RE.match(e.plain_text() or ""):
            tags += 1
        elif t == "INSERT":
            tags += sum(1 for a in e.attribs if TAG_RE.match(a.dxf.text or ""))
    for b in doc.blocks:
        for e in b:
            if e.dxftype() in ("TEXT", "ATTDEF") and TAG_RE.match(e.dxf.text or ""):
                tags += 1

    # glazing symbols per storey
    items = {s: [] for s in FRAMES_MM}
    for e in msp:
        if e.dxftype() not in ("LINE", "ARC", "LWPOLYLINE") or layer(e) != WINDOW_LAYER:
            continue
        bb = bbox.extents([e])
        s = storey_of(bb.center.x, bb.center.y)
        if not s:
            continue
        ox, oy = reg[s]
        curved = e.dxftype() == "ARC" or (e.dxftype() == "LWPOLYLINE" and any(abs(v[4]) > 1e-9 for v in e.get_points()))
        items[s].append({"handle": e.dxf.handle, "curved": curved,
                         "bbox": ((bb.extmin.x - ox) * UNIT_M, (bb.extmin.y - oy) * UNIT_M,
                                  (bb.extmax.x - ox) * UNIT_M, (bb.extmax.y - oy) * UNIT_M)})
    windows = []
    for s in FRAMES_MM:
        syms = [w for w in (INV.window_symbol(c) for c in INV.cluster(items[s], tol=0.03)) if w]
        for w in INV.merge_parallel_triples(syms):
            w["storey"] = s
            windows.append(w)

    # curved glazing: glass-line lengths (for the record; the width is the printed dimension, Q-38 A / Q-39 C)
    curved_len = {}
    for w in windows:
        if w["curved"]:
            ls = []
            for h in w["handles"]:
                e = doc.entitydb[h]
                if e.dxftype() == "LWPOLYLINE" or e.dxftype() == "ARC":
                    ls.append(round(_length(e), 3))
            curved_len[tuple(w["handles"])] = sorted(ls)

    # door leaves: blocks that carry a swing arc; arch blocks (no arc) are leafless openings
    leaf_blocks, arch_blocks = set(), set()
    for b in doc.blocks:
        kinds = [x.dxftype() for x in b]
        if not kinds or b.name.startswith("*"):
            continue
        if b.name.lower().startswith("arch"):
            arch_blocks.add(b.name)
        elif any(x.dxftype() == "ARC" and layer(x) == SWING_LAYER for x in b):
            leaf_blocks.add(b.name)
    doors, arches = [], []
    for e in msp.query("INSERT"):
        s = storey_of(e.dxf.insert.x, e.dxf.insert.y)
        if not s:
            continue
        ox, oy = reg[s]
        loc = ((e.dxf.insert.x - ox) * UNIT_M, (e.dxf.insert.y - oy) * UNIT_M)
        rec = {"storey": s, "handles": [e.dxf.handle], "symbol": f"block {e.dxf.name}", "loc": loc,
               "leaf_m": None}
        if e.dxf.name in leaf_blocks:
            arcs = [x for x in doc.blocks[e.dxf.name] if x.dxftype() == "ARC"]
            rec["leaf_m"] = sorted(round(a.dxf.radius * abs(e.dxf.xscale) * UNIT_M, 3) for a in arcs)
            doors.append(rec)
        elif e.dxf.name in arch_blocks:
            arches.append(rec)
    for e in msp.query("ARC"):
        if layer(e) != SWING_LAYER:
            continue
        r = e.dxf.radius * UNIT_M
        s = storey_of(e.dxf.center.x, e.dxf.center.y)
        if s and LOOSE_SWING_R_M[0] <= r <= LOOSE_SWING_R_M[1]:
            ox, oy = reg[s]
            doors.append({"storey": s, "handles": [e.dxf.handle], "symbol": "loose swing arc",
                          "loc": ((e.dxf.center.x - ox) * UNIT_M, (e.dxf.center.y - oy) * UNIT_M),
                          "leaf_m": [round(r, 3)]})

    # NW elevation DIMENSIONs for W03 / W18 (printed values; handle per value)
    dims = []
    for e in msp.query("DIMENSION"):
        try:
            m = e.get_measurement()
        except Exception:
            continue
        if isinstance(m, (int, float)):
            dims.append({"handle": e.dxf.handle, "value_mm": round(float(m), 1), "x": e.dxf.defpoint.x})
    arc_dims = []
    for e in msp.query("ARC_DIMENSION"):
        try:
            arc_dims.append({"handle": e.dxf.handle, "value_mm": round(float(e.get_measurement()), 1)})
        except Exception:
            pass
    return {"tags": tags, "windows": windows, "doors": doors, "arches": arches, "curved_len": curved_len,
            "dims": dims, "arc_dims": arc_dims, "reg": reg}


def _length(e):
    if e.dxftype() == "ARC":
        sw = (e.dxf.end_angle - e.dxf.start_angle) % 360.0
        return e.dxf.radius * math.radians(sw) * UNIT_M
    pts = list(e.get_points())
    tot = 0.0
    n = len(pts) if e.closed else len(pts) - 1
    for i in range(n):
        x1, y1, _, _, b = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)][:2]
        c = math.hypot(x2 - x1, y2 - y1)
        if abs(b) < 1e-12:
            continue                             # straight end stubs are not glass: the arc part only
        else:
            th = 4 * math.atan(abs(b))
            tot += c * th / (2 * math.sin(th / 2))
    return tot * UNIT_M


# ---------------------------------------------------------------- elevations

def elevation_features():
    feats = {}
    for i, r in enumerate(_csv(T194)):
        if r["source"] != "ELEVATION" or r["kind"] != "WINDOW" or not r["pos_m"] or r["facade"] not in FACADES:
            continue
        k = 0.001 if r["units"] == "mm" else 1.0
        w = float(r["width"]) * k if r["width"] and r["width_basis"] == "PRINTED" else None
        ref = f"T194:{r['facade']}:{r['storey']}:{float(r['pos_m']) * k:.3f}"
        feats.setdefault(r["facade"], []).append({"ref": ref, "storey": r["storey"], "pos_m": float(r["pos_m"]) * k,
                                                  "width_m": w, "row": i + 2})
    return feats


def bind_elevations(windows):
    feats = elevation_features()
    out, report = {}, {}
    for fac, spec in FACADES.items():
        cand = [w for w in windows if not w["curved"] and w["axis"] == spec["axis"]]
        curved = [w for w in windows if w["curved"]]
        # a curved window's facade coordinate is its box centre: candidate on the facade its curve faces
        syms = cand + ([] if spec["axis"] == "X" else curved)
        b, unb, amb, off = INV.bind_elevation(syms, feats.get(fac, []), spec, tol=0.05)
        report[fac] = {"features": len(feats.get(fac, [])), "bound": len(b), "unbound": unb, "ambiguous": amb,
                       "offset_m": None if off is None else round(off, 3)}
        for ref, (i, d) in b.items():
            out.setdefault(id(syms[i]), []).append((ref, d))
    return out, report


# ---------------------------------------------------------------- engine crosswalk (after the inventory)

def engine_bind(inv_rows, run_dir, reg):
    """attach the census id: engine opening / door element at the same plan point -> its census row (ENGINE_REF
    token). Used for the crosswalk only; existence is already settled by the inventory."""
    if not run_dir:
        return {}
    run = Path(run_dir)
    ops = json.loads((run / "ARCH_OPENINGS.json").read_text())["openings"]
    doors = json.loads((run / "DOOR_SCHEDULE.json").read_text())["doors"]["elements"]
    pts = []
    for o in ops:
        s = o["floor"]
        ox, oy = reg[s]
        c = o["position"]["centre_m"]
        pts.append((s, o["opening_id"], (c[0] - ox * UNIT_M, c[1] - oy * UNIT_M)))
    for d in doors:
        s = d["floor"]
        ox, oy = reg[s]
        c = d["centre"]
        pts.append((s, d["element_id"], ((c[0] - ox) * UNIT_M, (c[1] - oy) * UNIT_M)))
    hit = {}
    for key, r in inv_rows.items():
        reach = 0.35 if r["kind"] == "WINDOW" else 1.30
        near = sorted((math.dist(r["loc"], p[2]), p[1]) for p in pts
                      if p[0] == r["storey"] and math.dist(r["loc"], p[2]) <= reach
                      and (p[1].startswith("DOOR-") == (r["kind"] in ("DOOR", "GATE"))))
        if near:
            hit[key] = near[0]
    # one engine id per inventory row and vice versa (nearest wins)
    used = {}
    for key, (d, eid) in sorted(hit.items(), key=lambda kv: (kv[1][0], kv[0])):
        k = (inv_rows[key]["storey"], eid)               # opening ids repeat per storey (OP-004 on GF and on 1F)
        if k not in used:
            used[k] = key
    return {key: k[1] for k, key in used.items()}


def census_index():
    rows = _csv(T198)
    tok = {}
    for r in rows:
        for t in (x.strip() for x in (r["ENGINE_REF"] or "").split("/")):
            if t and not t.startswith("none"):
                tok[(r["FLOOR"], t.split(" ")[-1])] = r["ID"]
    return rows, tok


# ---------------------------------------------------------------- build

def build(dxf, run_dir):
    D = read_dxf(dxf)
    elev, elev_report = bind_elevations(D["windows"])
    obs, meta = [], {}
    for n, w in enumerate(sorted(D["windows"], key=lambda w: (w["storey"], w["centre"][1], w["centre"][0]))):
        ref = f"PW-{w['storey']}-{n:02d}"
        o = {"source": "PLAN_SYMBOL", "kind": "WINDOW", "storey": w["storey"], "loc": w["centre"], "tag": None,
             "handles": w["handles"], "ref": ref, "width_m": w["width_m"]}
        obs.append(o)
        meta[ref] = {"symbol": "glazing lines (curved)" if w["curved"] else
                     f"glazing lines ({w['n']} entities, axis {w['axis']})", "elev": elev.get(id(w), []),
                     "curved_len": D["curved_len"].get(tuple(w["handles"]))}
    for n, d in enumerate(sorted(D["doors"], key=lambda d: (d["storey"], d["loc"][1], d["loc"][0]))):
        ref = f"PD-{d['storey']}-{n:02d}"
        obs.append({"source": "PLAN_SYMBOL", "kind": "DOOR", "storey": d["storey"], "loc": d["loc"], "tag": None,
                    "handles": d["handles"], "ref": ref, "width_m": None})
        meta[ref] = {"symbol": d["symbol"], "leaf": d["leaf_m"], "elev": []}
    for n, a in enumerate(sorted(D["arches"], key=lambda d: (d["storey"], d["loc"][1], d["loc"][0]))):
        ref = f"PA-{a['storey']}-{n:02d}"
        obs.append({"source": "PLAN_SYMBOL", "kind": "OPENING", "storey": a["storey"], "loc": a["loc"], "tag": None,
                    "handles": a["handles"], "ref": ref, "width_m": None})
        meta[ref] = {"symbol": a["symbol"], "elev": []}
    rows = INV.build(obs, loc_tol=0.15)
    byref = {r["refs"][0]: r for r in rows}

    # census id: engine position first, unique attributes second; never existence
    census, tok = census_index()
    eng = engine_bind(byref, run_dir, D["reg"])
    cid, how = {}, {}
    for ref, eid in eng.items():
        r = byref[ref]
        c = tok.get((r["storey"], eid))
        if c:
            cid[ref], how[ref] = c, f"engine {eid} at the same plan point -> census ENGINE_REF"
    free = [c for c in census if c["ID"] not in cid.values()]
    for ref, r in byref.items():
        if ref in cid:
            continue
        m = meta[ref]
        if r["kind"] == "WINDOW":
            if m.get("curved_len"):
                cands = [c for c in free if c["FLOOR"] == r["storey"] and c["KIND"] == "WINDOW"
                         and c["ID"] in _curved_ids(census)]
                basis = "the only curved glazing symbol on this storey = the census's curved window of this storey"
            else:
                cands = [c for c in free if c["FLOOR"] == r["storey"] and c["KIND"] == "WINDOW" and c["WIDTH_M"]
                         and abs(float(c["WIDTH_M"]) - r["width_m"]) <= 0.01]
                basis = "the only census window of this storey and width"
        elif r["kind"] in ("DOOR",):
            cands = [c for c in free if c["FLOOR"] == r["storey"] and c["KIND"] in ("DOOR", "GATE")
                     and ("loose" in m["symbol"]) == ("D15 (0.69" in c["PRIOR_REF"])]
            basis = "the only census door of this storey drawn as a loose swing"
        else:
            cands = [c for c in free if c["FLOOR"] == r["storey"] and c["BOQ_LINE"] == "OPENING.ARCH_NO_LEAF"]
            basis = "the only census arch of this storey"
        if len(cands) == 1:
            cid[ref], how[ref] = cands[0]["ID"], basis
            free.remove(cands[0])
    return D, rows, meta, cid, how, census, elev_report


def _curved_ids(census):
    return {c["ID"] for c in census if c["KIND"] == "WINDOW" and (c["ENGINE_REF"].startswith("COP-")
            or "curved" in (c["NOTE"] or "").lower() or c["ID"] == "W03")}


def render(D, rows, meta, cid, how, census, elev_report):
    cen = {c["ID"]: c for c in census}
    inv = io.StringIO()
    w = csv.writer(inv, lineterminator="\n")
    w.writerow(["ID", "KIND", "FLOOR", "ENGINE_REF", "STATE", "EXISTENCE_SOURCES", "PLAN_SYMBOL", "HANDLES",
                "WIDTH_PLAN_M", "ELEVATION_REFS", "ELEV_RESIDUAL_MM", "ID_BINDING", "FLAGS", "NOTE"])
    out_rows = []
    for r in rows:
        ref = r["refs"][0]
        m = meta[ref]
        c = cid.get(ref)
        kind = r["kind"]
        if c and cen[c]["KIND"] == "GATE":
            kind = "GATE"
        srcs = list(r["sources"])
        if m["elev"]:
            srcs.append("ELEVATION")
        note = ""
        if m.get("leaf"):
            note = f"leaf radius {'/'.join(f'{x:.3f}' for x in m['leaf'])} m (identity only; the opening width is jamb to jamb)"
        if m.get("curved_len"):
            note = (f"curved glass lines (arc part) {', '.join(f'{x:.3f}' for x in m['curved_len'])} m (record only: width by the "
                    f"owner rule for this window, Q-38 A printed / Q-39 C outer arc)")
        extra = ROW_NOTES.get(c)
        if extra:
            note = (note + "; " if note else "") + extra
        if kind == "GATE":
            note += "; class GATE from T-150 (site frontage, no walls at its ends): class, not existence"
        out_rows.append([c or ref, kind, r["storey"], cen[c]["ENGINE_REF"] if c else "",
                         r["state"], "+".join(sorted(set(srcs))), m["symbol"], " ".join(r["handles"]),
                         "" if r["width_m"] is None else f"{r['width_m']:.4f}",
                         " ".join(x[0] for x in m["elev"]), " ".join(f"{x[1] * 1000:.0f}" for x in m["elev"]),
                         how.get(ref, "UNBOUND: no census row"), " ".join(r["flags"]), note])
    out_rows.sort(key=lambda x: ({"GF": 0, "1F": 1, "2F": 2}[x[2]], x[1], x[0]))
    for x in out_rows:
        w.writerow(x)

    inv_ids = {x[0]: x for x in out_rows}
    cw = io.StringIO()
    w2 = csv.writer(cw, lineterminator="\n")
    w2.writerow(["CENSUS_ID", "CENSUS_KIND", "FLOOR", "T198_LIST", "T236_INVENTORY", "T232_INPUT", "INVENTORY_T249",
                 "STATUS", "NOTE"])
    xw = {"DOOR": INV.crosswalk([i for i, x in inv_ids.items() if x[1] in ("DOOR", "GATE")],
                                [c["ID"] for c in census if c["KIND"] in ("DOOR", "GATE")]),
          "WINDOW": INV.crosswalk([i for i, x in inv_ids.items() if x[1] == "WINDOW"],
                                  [c["ID"] for c in census if c["KIND"] == "WINDOW"])}
    for c in census:
        k = c["KIND"]
        in_inv = c["ID"] in inv_ids
        t236 = "yes" if k in ("DOOR", "WINDOW") else "no (kind not counted)"
        if k in ("DOOR", "GATE", "WINDOW"):
            st = "AGREE" if in_inv else "EXTRA_IN_LIST"
            note = ""
        elif k == "OPENING" and c["BOQ_LINE"] == "OPENING.ARCH_NO_LEAF":
            st = "AGREE" if in_inv else "EXTRA_IN_LIST"
            note = "arch block on the plan"
        else:
            st = "NOT_IN_SCOPE"
            note = ("leafless / unglazed gap (passage, lift, filling, unresolved): no plan symbol of its own; existence "
                    "rests on T-175 / T-194 wall-gap reads, outside this inventory (named limit)")
        if c["ID"] in ("W03", "W18"):
            note = ("in the census and drawn on plan + elevation, but in NO window line of V2.9 or V3.0.8 (T-236 F5): "
                    "the engine produced no opening record for it")
        w2.writerow([c["ID"], k, c["FLOOR"], "yes", t236, "yes (T-198 ids)" if k in ("DOOR", "WINDOW") else "no",
                     "yes" if in_inv else "no", st, note])
    for i, x in inv_ids.items():
        if i not in cen:
            w2.writerow([i, x[1], x[2], "no", "no", "no", "yes", "MISSING_FROM_LIST", "drawn, in no list"])

    d = io.StringIO()
    w3 = csv.writer(d, lineterminator="\n")
    w3.writerow(["OPENING", "FLOOR", "CONSEQUENCE", "LINE", "UNIT", "IN_V29", "IN_V308", "DELTA", "STATUS", "SOURCE",
                 "NOTE"])
    for row in DELTAS:
        w3.writerow(row)

    summ = {
        "task": "T-249", "dxf_opening_tags_found": D["tags"], "schedule_issued": False,
        "plan_symbols": {"windows": sum(1 for x in out_rows if x[1] == "WINDOW"),
                         "doors": sum(1 for x in out_rows if x[1] == "DOOR"),
                         "gates": sum(1 for x in out_rows if x[1] == "GATE"),
                         "arches": sum(1 for x in out_rows if x[1] == "OPENING")},
        "windows_by_floor": {f: sum(1 for x in out_rows if x[1] == "WINDOW" and x[2] == f) for f in ("GF", "1F", "2F")},
        "doors_by_floor": {f: sum(1 for x in out_rows if x[1] == "DOOR" and x[2] == f) for f in ("GF", "1F", "2F")},
        "windows_with_elevation": sum(1 for x in out_rows if x[1] == "WINDOW" and x[9]),
        "crosswalk": xw, "elevation_binding": elev_report,
        "id_binding": {"engine_position": sum(1 for v in how.values() if v.startswith("engine")),
                       "unique_attribute": sum(1 for v in how.values() if not v.startswith("engine")),
                       "unbound": sum(1 for x in out_rows if x[11].startswith("UNBOUND"))},
        "nw_dimensions_mm": {k: [x["handle"] for x in D["dims"] if x["value_mm"] == v]
                             for k, v in (("W03_height_4300", 4300.0), ("W18_width_500", 500.0),
                                          ("W18_head_2160.7", 2160.7), ("W18_sill_839.3", 839.3))},
        "arc_dimensions_mm": sorted(x["value_mm"] for x in D["arc_dims"]),
    }
    return {"inventory": inv.getvalue(), "crosswalk": cw.getvalue(), "delta": d.getvalue(),
            "summary": json.dumps(summ, indent=1, sort_keys=True) + "\n"}


# evidence the elevation binding by position cannot give (these windows are drawn on no elevation that the position
# solver reads, or on one where T-194 bound them by pair / section): cited, never re-derived
ROW_NOTES = {
    "W02": "plan draws ONE continuous glazing symbol 6.3316 (no pier); NW draws the GF as a section (T-194 NOT_SHOWN); "
           "renders show two windows with a pier (T-161 F23, designer D-53): pcs HELD 1 .. 2, area HELD (D-45)",
    "W03": "NW elevation: vertical DIMENSION 2E7A 4300 from +1.00 (printed 430; T-198 own read, re-found this run); "
           "projected width not printed on the NW; width printed 657 on sheet03 (owner Q-38 A)",
    "W09": "annex court wall facing the SE: the SE elevation cuts the annex (T-194): on no elevation",
    "W10": "annex court wall facing the SE: the SE elevation cuts the annex (T-194): on no elevation",
    "W11": "fence elevation (Pages_11-12 p.12, T-194): two equal windows, which drawn window is W11 / W12 not "
           "distinguishable (symmetric); fence plan 195",
    "W12": "fence elevation (Pages_11-12 p.12, T-194): see W11",
}

# W18 / W03 consequences (areas by the owner rules; deltas for lane I; NOTHING applied here)
DELTAS = [
    ["W18", "1F", "window supply line", "WINDOWS (aluminium) m2", "m2", "absent", "absent", "+1.080",
     "DRAWING-CONFIRMED", "0.50 x 2.16: plan glazing symbol 0.500 (this inventory) = NW DIMENSION 500 (printed 50); NW "
     "839.3 / 2160.7 from +5.50 (printed 84 / 216, T-083 / T-194); rectangular, Q-32 A not engaged",
     "carry into the T-232 window line"],
    ["W18", "1F", "window supply line", "WINDOWS (aluminium) pcs", "nr", "absent", "absent", "+1", "DRAWING-CONFIRMED",
     "one plan glazing symbol, one NW elevation window", ""],
    ["W18", "1F", "blockwork deduction", "1F-W00 net block m2", "m2", "n/a (research)", "n/a (research)", "0.000",
     "DRAWING-CONFIRMED", "T-175 T175_OPENING_CONSEQUENCES.csv already deducts 1.080 from host 1F-W00",
     "no new delta: the masonry ledger knew the window; only the window line did not"],
    ["W18", "1F", "finishes deduction", "1F bath wall tile / external plaster-paint", "m2", "n/a (research)",
     "n/a (research)", "0.000", "DRAWING-CONFIRMED",
     "T-175 face A WALL_TILE 1.080, face B EXTERNAL_PLASTER_PAINT 1.080; T-128 r3 1F-12 W18 0.50 sill 0.84",
     "no new delta"],
    ["W03", "GF", "window supply line", "WINDOWS (aluminium) m2", "m2", "absent", "absent", "+28.251",
     "DRAWING-CONFIRMED",
     "6.57 (printed 657 on sheet03; owner Q-38 A names it the governing width) x 4.30 (NW DIMENSION 4300 from +1.00, printed 430); the plan symbol is the "
     "curved glazed band (glass lines 6.66 .. 6.79 m, record only)", "carry into the T-232 window line"],
    ["W03", "GF", "window supply line", "WINDOWS (aluminium) pcs", "nr", "absent", "absent", "+1", "DRAWING-CONFIRMED",
     "one curved glazing symbol on the GF plan; NW elevation draws it (T-194)", ""],
    ["W03", "GF", "blockwork deduction", "GF-W37 (glazed line)", "m2", "n/a", "n/a", "0.000", "NOT_APPLICABLE",
     "T-175: host is GLAZED, no masonry built in this line, nothing to deduct", "build before deduct (ERS s.3)"],
    ["W03", "GF", "finishes deduction", "GF-08 / GF-15 plaster-paint", "m", "n/a (research)", "n/a (research)",
     "HELD", "HELD", "T-128 r3 room-side split 1.625 + 5.106 = 6.731 m vs drawn room-face arc 6.5675 m (Verifier 00:12)",
     "T-250 owns the room-side developed line; not settled here"],
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--engine-run")
    a = ap.parse_args(argv)
    res = render(*build(a.dxf, a.engine_run))
    if a.mode == "build":
        for k, p in OUT.items():
            p.write_text(res[k], encoding="utf-8")
        print(res["summary"])
        return 0
    bad = [k for k, p in OUT.items() if not p.exists() or p.read_text(encoding="utf-8") != res[k]]
    print("T-249 check:", "OK" if not bad else f"DIFFER {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
