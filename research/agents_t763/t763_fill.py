"""T-763 F-04 PLASTER HEIGHT 4.34 / 4.04 + plaster, paint and corner-bead figures (DELIVERY MODE fix-row set; worker 2,
2026-11-13; r2 after the Checker's Gate A findings of 18:54).

Reads the candidate line index ARCH_TAKEOFF_V3.0.81 (T-770 r2, agents/task-T-770 @ c4005ffa = V3.0.79 + MAIN_FILL 81
+ T-762 + T-761 wired; the FIN.PLASTER / FIN.PAINT / FIN.PLASTER.BEAD / FIN.WALL.TILE lines are identical to the r1
index 9cbc24d9) and writes out/FIX_ROWS.json + out/FIX_ROWS.md: one row per FIN.PLASTER, FIN.PAINT and FIN.PLASTER.BEAD
line still HELD (blank or ranged) after MAIN_FILL, plus the RELEASED wet-room render / band lines whose split moves to
the 3.00 m tile top (sets RENDER_RESTATE / HEIGHT_RESTATE, separable). FIN.WALL.TILE (MAIN_FILL_4 TILE_300) and the
floor beds (MAIN_FILL_1) belong to MAIN_FILL: overlap with MAIN_FILL_ALL is asserted 0.

Heights (owner 2026-11-13; rule record RULE_T763_PLASTER_HEIGHT.json, r2):
  plaster height H = storey - slab 0.16 = 4.34 GF, 4.04 1F / 2F, 3.84 GF annex (+0.30 .. +4.30)
  false ceiling: dry rooms H - 0.90; wet rooms and kitchen 2.70 (company default, kept: never replaced by a bound)
  wet-room wall tiles 3.00 m from F.F.L. (owner, 'for tile height only')
  wet room 'plaster' line = render behind the tiles = run x 3.00 - drawn openings (all heads <= 2.50 < 3.00)
  wet room 'band' line    = run x (H - 3.00): the face above the tiles, all of it above the 2.70 ceiling, unpainted
  so render + band        = run x H - openings (the Checker's reading that honours both owner defaults).
Openings: drawn widths (ARCH_TAKEOFF_V2.9 room boundary runs 'door' / 'passage' and the room's window openings on the
architectural DXF; one window the opening reader missed read by hand); door / passage head 2.20 company default;
window sill / head from the vector elevations (T-201: every 0.60 window 1.70 .. 2.50 above F.F.L.; 1.50 / 1.00 windows
1.00 .. 2.50). Stair-shaft lines: points of the T-680 model with each held cause closed (t763_shaft.py).

  python3 -I research/agents_t763/t763_fill.py <LINE_INDEX_V3_0_81.json> [--check]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
T728 = os.path.join(HERE, "..", "agents_t728", "out", "T728_BEAD_RESTATEMENT.json")
INDEX_SHA16 = "3976b262611bc3bd"     # sha256[:16] of LINE_INDEX_V3_0_81.json at agents/task-T-770 c4005ffa (r2)
FAMILIES = ("FIN.PLASTER", "FIN.PAINT", "FIN.PLASTER.BEAD", "FIN.PAINT.EDGE")
T746 = os.path.join(HERE, "..", "agents_t746", "out", "T746_PAINT_EDGES.json")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")

SLAB = 0.16
H = {"GF": 4.50 - SLAB, "1F": 4.20 - SLAB, "2F": 4.20 - SLAB, "ANNEX": 4.00 - SLAB}   # 4.34 / 4.04 / 4.04 / 3.84
CEIL_DROP = 0.90            # dry-room false ceiling = clear height - 0.90 (company default, owner 2026-11-13)
WET_CEIL = 2.70             # wet rooms / kitchen false ceiling 2.70 (company default, owner 2026-11-13)
TILE_H = 3.00               # wet-room wall tiles 3.00 m from F.F.L. (owner 2026-11-13, tile height only)
HEAD = 2.20                 # door / passage head default where none is printed
DOOR = 1.00 * HEAD          # (kept for the reveal / bead defaults)
REVEAL_T = 0.15             # through-reveal depth: the 4 released THROUGH reveals of this candidate = perimeter x 0.15

r4 = lambda x: round(x + 0.0, 4)


def ceiling(zone: str, wet: bool = True) -> float:
    """false-ceiling height: wet rooms / kitchen 2.70, dry rooms H - 0.90 (company defaults, both kept as stated)"""
    return WET_CEIL if wet else H[zone] - CEIL_DROP


def openings_m2(doors_lm: float = 0.0, passages_lm: float = 0.0, windows=()) -> float:
    """area of the drawn openings below the tile top: doors / passages x head 2.20, windows width x (head - sill)"""
    tot = 0.0
    for v in (doors_lm, passages_lm):
        if v is None or v < 0:
            raise ValueError("opening width missing or negative: never 0 by default")
    tot += (doors_lm + passages_lm) * HEAD
    for w in windows:
        wd, sill, head = w["w"], w["sill"], w["head"]
        if wd is None or wd <= 0 or sill is None or head is None or head <= sill:
            raise ValueError(f"window {w.get('id')} without a drawn width / sill / head: never 0")
        if head > TILE_H:
            raise ValueError(f"window {w.get('id')} head {head} above the tile top: split it explicitly")
        tot += wd * (head - sill)
    return tot


def wet_render(run: float, zone: str, opening_m2: float) -> float:
    """render behind the tiles up to the 3.00 m tile top (the wet room's FIN.PLASTER 'plaster' line)"""
    if run is None or run <= 0:
        raise ValueError("wall run missing: a wet-room render line is never valued without its run")
    if opening_m2 is None or opening_m2 < 0:
        raise ValueError("openings not read: a wet-room render line is never valued without them")
    v = run * TILE_H - opening_m2
    if v <= 0:
        raise ValueError("openings exceed the face")
    return v


def wet_band(run: float, zone: str) -> float:
    """wall face above the tiles up to the soffit (FIN.PLASTER 'plaster band above ceiling'), all above the 2.70 ceiling"""
    if run is None or run <= 0:
        raise ValueError("wall run missing: a band line is never valued without its run")
    return run * (H[zone] - TILE_H)


# Wet rooms: (zone, run lm, doors lm, passages lm, windows). Run = the ledger runs MAIN_FILL_4 used for the same rooms'
# tile lines (CANDIDATE_V3021_T335 wall_run_lm; = the ARCH_TAKEOFF_V2.9 room perimeter, GF-RDBD4F9 without its open side
# 1.2557); zone from the T-676 hold class (Q-54 B = annex under the +4.30 roof). Doors / passages = the room's V2.9
# boundary runs 'door' / 'passage' on the architectural DXF (drawn gap widths); windows = the room's V2.9 window
# openings, sill / head per T-201 (vector elevations, by width class: every 0.60 window 1.70 .. 2.50; W08 / W09 1.50 and
# W10 1.00: 1.00 .. 2.50 above F.F.L.).
SMALL = lambda oid, w=0.60, lab="T-201 0.60 class 1.70 .. 2.50": {"id": oid, "w": w, "sill": 1.70, "head": 2.50, "src": lab}
WET = {
    "GF-R8496F0": ("ANNEX", 7.2, 0.8, 1.0, ()),
    "GF-RA3AD49": ("ANNEX", 14.5, 1.0, 0.0, ({"id": "OP-006", "w": 1.50, "sill": 1.00, "head": 2.50, "src": "T-201 W08 1.50 x 1.50"},)),
    "GF-RB62B55": ("ANNEX", 7.5, 0.8, 0.0, ()),
    "GF-RFAD3C4": ("ANNEX", 5.6, 0.8, 0.0, ()),
    "GF-RD36087": ("GF", 4.9, 0.797039, 0.9, ()),
    "GF-RDF7D28": ("GF", 6.2, 0.797039, 0.0, (SMALL("OP-014"),)),
    "GF-RD6F891": ("GF", 7.624665, 0.8, 0.0, (SMALL("OP-016"),)),
    "GF-RDBD4F9": ("GF", 8.243202, 1.6, 0.0, ()),
    "GF-RB28769": ("GF", 6.809808, 0.8, 0.0, (SMALL("OP-015"),)),
    "GF-RF38DAF": ("GF", 7.414038, 0.8, 0.0, ()),
    "1F-R8BDA49": ("1F", 9.0, 0.8, 0.0, (SMALL("OP-002"),)),
    "1F-RED23B8": ("1F", 7.6, 0.8, 0.0, (SMALL("OP-015"),)),
    "1F-R48AA46": ("1F", 9.0, 0.8, 0.0, (SMALL("OP-001"),)),
    "1F-R48CDA5": ("1F", 8.7, 0.8, 0.0, (SMALL("E-WALL", 0.50, "own DXF read: layer W frame, jambs 0.50 apart in the east "
                                               "wall (the V2.9 opening reader missed it; 'glazing_edge' 0.48); "
                                               "height = the 0.60 class 1.70 .. 2.50 (ESTIMATE)"),)),
    "1F-R26FA0D": ("1F", 16.94, 1.7, 0.0, (SMALL("OP-013"),)),
    "1F-R52AC05": ("1F", 6.54, 0.8, 0.0, (SMALL("OP-014"),)),
    "2F-RE83BED": ("2F", 9.7, 0.8, 0.0, (SMALL("OP-004"),)),
}
PANTRY = "GF-RC06FED"       # GF-07 pantry (kitchen ceiling 2.70)
PANTRY_RUN = 1.30 + 1.60    # own DXF read: west wall face 1.30 (window W10 1.00 in it, head 2.50 < 2.70) + south wall
                            # face 1.60 (incl. the flush column face 0.20); the east / north sides are layer-5 counter
                            # lines and the open side to the living room: no wall face above a ceiling there

# Bead hosts: element room key -> T-728 room; blank arrises valued by default (edge id: (lm, label, basis)).
BEAD_BLANK = {
    "A-GF-01#GF-01": (1.223795 + 2 * HEAD, "DEFAULT", "arch A-GF-01: head on the drawn arc 1.2238 (T-238 ARC, drawing) + 2 jambs x 2.20 head default"),
    "A-1F-01#1F-10": (1.00 + 2 * HEAD, "DEFAULT", "arch A-1F-01: width 1.00 (MAIN_FILL_2 basis) + 2 jambs x 2.20 head default"),
    "OPEN#ST-GF-OP020": (0.90 + 2 * HEAD, "DEFAULT", "doorless 0.90 opening OP-020: 0.90 head + 2 jambs x 2.20 head default"),
    "OPEN#GF-08-OP003": (2 * 3.65, "ESTIMATE", "open side OP-003 between columns: 2 column-jamb arrises x 3.65 (the room's measured arris height)"),
    "W03#IN": (6.6577 + 2 * (5.30 - 1.00), "DRAWING-READ", "curved W03 room side = the outside edge T-760 (merged): developed head 6.6577 + 2 jambs +1.00 .. +5.30"),
    "W17#IN": (3.29 + 2 * 3.00, "DRAWING-READ", "W17 room side: 3.29 x 3.00 (owner Q-76 A): head 3.29 + 2 jambs 3.00"),
}


def line_row(l, after, label, basis, set_name):
    return {"set": set_name, "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
            "element_id": l["element_id"],
            "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
            "after": {"class": "RELEASED", "net": r4(after)}, "label": label, "basis": basis}


def mid(l):
    return (l["held_low"] + l["held_high"]) / 2


def bead_hosts(t728_path):
    t = json.load(open(t728_path))
    hosts = {}
    for r in t["rows"]:
        hosts.setdefault(r["room"], []).append(r)
    return hosts


def bead_value(arrises):
    tot, parts, labels = 0.0, [], set()
    for a in arrises:
        if a["bead_state"] == "HELD_BLANK":
            if a["edge_id"] not in BEAD_BLANK:
                raise ValueError(f"blank arris {a['edge_id']} has no default: never 0")
            v, lab, b = BEAD_BLANK[a["edge_id"]]
            labels.add(lab); parts.append(f"{a['edge_id']} {v:.4f} ({b})")
        else:
            v = (a["low"] + a["high"]) / 2
            labels.add("MEASURED" if a["low"] == a["high"] else "ESTIMATE")
            parts.append(f"{a['edge_id']} {v:.4f}")
        tot += v
    label = "ESTIMATE" if "ESTIMATE" in labels else ("DEFAULT" if "DEFAULT" in labels else
                                                     ("DRAWING-READ" if "DRAWING-READ" in labels else "MEASURED"))
    return tot, label, "; ".join(parts)


def build(index_path, t728_path=T728):
    raw = open(index_path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    if sha != INDEX_SHA16:
        raise SystemExit(f"index sha {sha} != pinned {INDEX_SHA16}: rebuild on the newer index deliberately")
    idx = json.loads(raw)
    L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    by_eid = {l["element_id"]: l for l in L}
    by_id = {l["line_id"]: l for l in L}
    rows = []

    # 1. wet rooms: render (plaster) and band lines, split at the 3.00 m tile top, drawn openings
    for room, (zone, run, d_lm, p_lm, wins) in WET.items():
        p = by_eid.get(f"{room}:plaster"); b = by_eid.get(f"{room}:plaster band above ceiling")
        if p is None or b is None:
            raise ValueError(f"{room}: render or band line missing on the index")
        om = openings_m2(d_lm, p_lm, wins)
        est = any("ESTIMATE" in w["src"] for w in wins)
        ops = (f"doors {d_lm:g} lm" + (f" + passage {p_lm:g} lm" if p_lm else "") + " x head 2.20"
               + "".join(f" + window {w['id']} {w['w']:g} x ({w['head']:g} - {w['sill']:g}) [{w['src']}]" for w in wins))
        for l, val, kind in ((p, wet_render(run, zone, om), "render"), (b, wet_band(run, zone), "band")):
            if l["class"] not in ("HELD", "RELEASED"):
                raise ValueError(f"{l['element_id']}: class {l['class']}")
            if kind == "render":
                set_name = "PLASTER_WET" if l["class"] == "HELD" else "RENDER_RESTATE"
                basis = (f"{room}: render behind the tiles to the 3.00 m tile top: run {run} lm x 3.00 - openings "
                         f"{om:.4f} m2 ({ops}; drawn widths, ARCH_TAKEOFF_V2.9 room runs)")
            else:
                set_name = "PLASTER_BAND" if l["class"] == "HELD" else "HEIGHT_RESTATE"
                basis = (f"{room}: face above the tiles to the soffit: run {run} lm x (H {H[zone]:.2f} - 3.00) = x "
                         f"{H[zone] - TILE_H:.2f} (H = storey - slab 0.16; all above the 2.70 wet-room ceiling, unpainted)")
            if l["class"] == "RELEASED":
                basis += f"; was {l['measured_net']} (split at the old decor-ceiling height)"
            rows.append(line_row(l, val, "ESTIMATE" if est and kind == "render" else "DEFAULT", basis, set_name))
    pb = by_eid[f"{PANTRY}:plaster band above ceiling"]
    rows.append(line_row(pb, PANTRY_RUN * (H["GF"] - WET_CEIL), "DEFAULT",
                         f"GF-07 pantry: wall run {PANTRY_RUN:.2f} lm (own DXF read: west 1.30 + south 1.60) x (H 4.34 - "
                         "kitchen ceiling 2.70 default); window W10 head 2.50 below the ceiling", "PLASTER_BAND"))

    # 2. stair-shaft lines: the T-680 model at the owner height rule, every held cause closed (t763_shaft.py);
    #    band-share lines: bound width below 1 % of the family (Checker: may stay, label ESTIMATE)
    import t763_shaft as SH
    for lid, (band, fin, v) in SH.points().items():
        l = by_id[lid]
        if not (l["held_low"] - 0.001 <= v <= l["held_high"] + 0.001):
            raise ValueError(f"{lid}: shaft point {v:.3f} outside its merged bound {l['held_low']} .. {l['held_high']}")
        rows.append(line_row(l, v, "ESTIMATE",
                             f"stair shaft ST-01 {band} band {fin}: T-680 face model at b = 0 (owner: plaster = storey - "
                             "slab), NW floor +0.30 (T-441 lobby has no west face), OP-020 head 2.20 default, winder body "
                             "and B20 / B23 ends deducted per the structural plan (Q-46 open), W25 / W27 T-201 heads, 2F "
                             f"soffit +13.72 + B3; bound {l['held_low']} .. {l['held_high']}", "SHAFT"))
    for l in L:
        if l["class"] == "HELD" and str(l["element_id"]).startswith(("PLASTER-BAND@", "PAINT-BAND@")):
            rows.append(line_row(l, mid(l), "ESTIMATE",
                                 f"band share bound {l['held_low']} .. {l['held_high']} (width {l['held_high'] - l['held_low']:.3f} m2, "
                                 "below 1 % of the family): midpoint", "BAND_SHARE"))

    # 3. through-reveal plaster returns (blank): (2 jambs + head) x 0.15
    for eid, w, head_len, why in (("GF-REVEAL-A-GF-01:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.223795, "arch: drawn arc 1.2238 as head"),
                                  ("1F-REVEAL-A-1F-01:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.00, "arch drawn on no view: straight 1.00 head"),
                                  ("GF-REVEAL-D-GF-15:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.00, "door width 1.00 (T-602 drawn)")):
        l = by_eid[eid]
        perim = 2 * HEAD + head_len
        rows.append(line_row(l, perim * REVEAL_T, "DEFAULT",
                             f"{eid.split(':')[0]}: (2 x 2.20 head default + {head_len:.4f}) = {perim:.4f} lm x depth 0.15 "
                             f"(as the released THROUGH reveals); {why}", "REVEAL"))

    # 5. interior paint edges (lm, UP-FIN-PAINT-002 'edges' reading B, merged T-746 per-part causes): each open part closed
    #    by one physical reading; a determined 0 carries its cause, a part without a size takes the reveal defaults above
    t746 = {x["paint_element"].rsplit(":", 1)[0]: x for x in json.load(open(T746))["return_rows"]}
    held_size = {"GF-REVEAL-A-GF-01": (1.223795, "arch A-GF-01: head = the drawn arc 1.2238 (T-238) + 2 jambs x 2.20 head default"),
                 "1F-REVEAL-A-1F-01": (1.00, "arch A-1F-01: width 1.00, drawn on no view: straight head + 2 jambs x 2.20 default"),
                 "GF-REVEAL-D-GF-15": (1.00, "gate D-GF-15: width 1.00 (T-602 drawn) + 2 jambs x 2.20 head default")}
    for l in L:
        if l["item_code"] != "FIN.PAINT.EDGE" or l["class"] != "HELD":
            continue
        k = l["element_id"].rsplit(":", 1)[0]
        x = t746.get(k)
        if x is None:
            raise ValueError(f"{l['element_id']}: no T-746 return row")
        if x["status"] == "HELD":
            key = next(h for h in held_size if l["element_id"].startswith(h))
            w, why = held_size[key]
            rows.append(line_row(l, w + 2 * HEAD, "DEFAULT", f"{x['opening']}: no frame drawn, painted return = 2 x h + w: {why}",
                                 "PAINT_EDGE"))
            continue
        parts = {p["part"]: p for p in x["parts"]}
        if abs(sum(float(p["lm"][1]) for p in x["parts"]) - l["held_high"]) > 1e-6:
            raise ValueError(f"{l['element_id']}: T-746 parts differ from the line bound (stale ledger)")
        v, why, lab = 0.0, [], "ESTIMATE"
        jc = parts["JAMBS"]["cause"]
        for name, p in parts.items():
            lo, hi = float(p["lm"][0]), float(p["lm"][1])
            if lo == hi:
                v += lo; why.append(f"{name} {lo:g} ({p['cause']}, merged)")
            elif p["cause"] == "WET_BOTH_SIDES_TILE_NOT_ESTABLISHED":
                lab = "DEFAULT"
                why.append(f"{name} 0: tiled to 3.00 m on both sides (owner 2026-11-13) over the 2.20 head, a determined zero")
            elif p["cause"] == "FRAME_COVERAGE_NOT_PRINTED" and name == "HEAD" and jc == "FRAME_COVERS_RETURN_DRAWN":
                why.append("HEAD 0: the frame drawn over the full wall depth at both jambs is one three-sided lining, so it covers "
                           "the head return too (determined zero by the drawn frame)")
            elif p["cause"] == "FRAME_COVERAGE_NOT_PRINTED" and jc == "FRAME_COVERAGE_NOT_PRINTED":
                v += hi; why.append(f"{name} {hi:g}: no frame posts drawn over the wall depth, the return is plastered and painted")
            else:
                raise ValueError(f"{l['element_id']}: part {name} cause {p['cause']} has no closing reading")
        rows.append(line_row(l, v, lab, f"{x['opening']} ({x['rooms']}): " + "; ".join(why), "PAINT_EDGE"))

    # 4. corner beads: one line per host, its own arrises (T-728 restatement, merged), blank arrises by default
    hosts = bead_hosts(t728_path)
    for l in L:
        if l["item_code"] == "FIN.PLASTER.BEAD" and l["class"] == "HELD":
            key = l["element_id"].split("HL:WALL_FINISH:")[1].replace("#BEAD", "").replace("_", "-")
            arr = hosts.get(key)
            if not arr:
                raise ValueError(f"no T-728 arrises for {l['element_id']}")
            v, lab, basis = bead_value(arr)
            if l["held_low"] is not None and abs(sum((a['low'] or 0) for a in arr if a['bead_state'] != 'HELD_BLANK') - l["held_low"]) > 0.01:
                raise ValueError(f"{l['element_id']}: T-728 arris sum differs from the line's low bound (stale ledger)")
            rows.append(line_row(l, v, lab, f"{key}: {len(arr)} arris rows: {basis}", "BEAD"))

    # every held line of the families is covered, nothing twice
    ids = [r["line_id"] for r in rows]
    assert len(ids) == len(set(ids)), "a line written twice"
    held_left = [l["line_id"] for l in L if l["item_code"] in FAMILIES and l["class"] == "HELD" and l["line_id"] not in ids]
    assert not held_left, f"held lines left without a figure: {held_left}"
    assert all(r["label"] in LABELS and r["basis"] for r in rows)
    # a figure is > 0, except a PAINT_EDGE determined zero that names its physical cause
    assert all(r["after"]["net"] > 0 or (r["set"] == "PAINT_EDGE" and " 0: " in r["basis"]) for r in rows)
    return sha, idx.get("candidate_version"), rows, L


def summary(rows, L):
    s = {}
    for fam in FAMILIES:
        fam_lines = [l for l in L if l["item_code"] == fam]
        frows = [r for r in rows if r["item_code"] == fam]
        held = [l for l in fam_lines if l["class"] == "HELD"]
        rel_before = sum(l["measured_net"] or 0 for l in fam_lines if l["class"] == "RELEASED")
        moved = {r["line_id"]: r for r in frows}
        rel_after = sum((moved[l["line_id"]]["after"]["net"] if l["line_id"] in moved else (l["measured_net"] or 0))
                        for l in fam_lines if l["class"] in ("RELEASED", "HELD"))
        labels = {}
        for r in frows:
            labels[r["label"]] = labels.get(r["label"], 0) + 1
        s[fam] = {"lines": len(fam_lines), "held_before": len(held),
                  "blank_before": sum(1 for l in held if l["held_low"] is None),
                  "held_low_before": round(sum(l["held_low"] or 0 for l in held), 1),
                  "held_high_before": round(sum(l["held_high"] or 0 for l in held), 1),
                  "released_before": round(rel_before, 1), "held_after": 0, "released_after": round(rel_after, 1),
                  "rows": len(frows), "labels": labels}
    return s


MAIN_FILL = os.path.join(HERE, "..", "agents_t762", "MAIN_FILL_ALL_INPUT.json")


def overlap(rows, main_fill_path=MAIN_FILL):
    """line ids written both here and by MAIN_FILL_ALL (must be 0: MAIN_FILL owns its lines)"""
    mf = {r["line_id"] for r in json.load(open(main_fill_path))["rows"]}
    return sorted(r["line_id"] for r in rows if r["line_id"] in mf)


def write(index_path, main_fill_path=MAIN_FILL):
    sha, ver, rows, L = build(index_path)
    ov = overlap(rows, main_fill_path)
    if ov:
        raise ValueError(f"lines also written by MAIN_FILL_ALL: {ov}")
    out = {"schema": "T763_FIX_ROWS_V1", "candidate_version": ver, "index_sha16": sha,
           "base": "agents/task-T-770 c4005ffa (V3.0.81 r2 = V3.0.79 + MAIN_FILL 81 + T-762 + T-761)",
           "overlap_with_MAIN_FILL_ALL": 0, "summary": summary(rows, L), "rows": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    md = ["# T-763 fix rows (DEFAULT / ESTIMATE / DRAWING-READ / MEASURED; never verified until the Checker re-measures)", "",
          "| family | lines | held before (blank) | held range before | released before | released after |", "|---|---|---|---|---|---|"]
    for k, v in out["summary"].items():
        md.append(f"| {k} | {v['lines']} | {v['held_before']} ({v['blank_before']}) | {v['held_low_before']} .. {v['held_high_before']} | "
                  f"{v['released_before']} | {v['released_after']} |")
    md += ["", "| set | line | element | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        bb = f"{b['class']} {b['net'] if b['net'] is not None else ''}{'' if b['low'] is None else str(b['low']) + '..' + str(b['high'])}"
        md.append(f"| {r['set']} | {r['line_id'][:10]} | {r['element_id']} | {bb} | {r['after']['net']} | {r['label']} | {r['basis']} |")
    return text, "\n".join(md) + "\n", out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    mf = argv[argv.index("--main-fill") + 1] if "--main-fill" in argv else MAIN_FILL
    text, md, out = write(argv[1], mf)
    if "--check" in argv:
        if open(OUT).read() != text or open(OUT_MD).read() != md:
            raise SystemExit("FIX_ROWS is stale: rerun without --check")
        print(f"check OK {len(out['rows'])} rows")
        return
    open(OUT, "w").write(text); open(OUT_MD, "w").write(md)
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main(sys.argv)
