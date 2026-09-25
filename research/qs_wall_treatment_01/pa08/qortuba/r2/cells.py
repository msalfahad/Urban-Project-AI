"""PA08-QORTUBA-R2 §2-§4: cell forensics and free-space eligibility.

R1 separated the rooms but left 53 raster cells, most of them artifacts of the very chords that did the separating: the
interior of a wall strip that was capped at both ends, the pocket inside a door frame, the gap between two stair treads.
This module says, for every cell, WHICH physical element's interior it is - and only a cell that is nobody's interior can
become a floor region.

No rule here uses an area threshold as its reason.  A cell is rejected because a physical element explains it, or because
its clear width is below the thinnest material band the drawing itself contains.  A cell that nothing explains is
HUMAN_REVIEW, never silently deleted and never silently promoted.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.ingest import material_bands as MB

FREE_SPACE_CLASSES = ("OCCUPIABLE_FREE_SPACE", "SERVICE_FREE_SPACE", "STAIR_OR_LANDING_SPACE", "OPEN_ROOF_OR_TERRACE",
                      "WALL_BAND_INTERIOR", "COLUMN_INTERIOR", "FRAME_INTERIOR", "JOINERY_OR_FURNITURE_INTERIOR",
                      "ANNOTATION_ENCLOSURE", "SITE_OR_SHEET_REGION", "ARTIFACT_POCKET", "UNRESOLVED")
FLOOR_ELIGIBLE_CLASSES = ("OCCUPIABLE_FREE_SPACE", "SERVICE_FREE_SPACE")
INTERIOR_SAMPLE_GRID = 3                 # 3 x 3 interior probes per cell
INTERIOR_SHARE_FOR_BAND = 8 / 9.0        # a cell is an element's interior when nearly every probe lies in that element's strip
MATERIAL_SHARE_FOR_ROOM = 0.5            # more wall than hole: a room is bounded mostly by material, a pocket mostly by chords
STAIR_LAYER_TOKENS = ("STAIR", "STAIRS", "STEP", "TREAD")
ANNOTATION_ROLES = ("DIMENSION_LINE", "DIMENSION_EXTENSION", "DIMENSION_TEXT", "TEXT_OR_LABEL", "GRID_OR_LEVEL")
ROOF_TOKENS = ("ROOF", "TERRACE", "سطح")


MTEXT_CODES = ("\\f", "\\P", "{", "}", "|")
SHEET_REGION_SHARE = 0.5                 # a cell covering this share of the view's own extent is the sheet / site region


def _is_room_label(a):
    """A room stamp: a short plain token placed in a space.  An MTEXT with font codes and paragraph breaks, a level stamp or a
    site note names the SHEET, not the region it happens to fall in, and never makes that region a room."""
    if a.get("ROLE") not in ("ROOM_NAME", "UNCLASSIFIED_TEXT"):
        return False
    t = (a.get("TEXT") or "").strip()
    if not t or len(t) > 24 or "=" in t or any(c in t for c in MTEXT_CODES):
        return False
    letters = sum(1 for c in t if c.isalpha())
    return letters >= max(2, len(t.replace(" ", "")) // 2)


def _rc(meta, x, y):
    return int((meta["y1"] - y) / meta["cell"]), int((x - meta["x0"]) / meta["cell"])


def _probe_points(bbox, n=INTERIOR_SAMPLE_GRID):
    x0, y0, x1, y1 = bbox
    return [(x0 + (x1 - x0) * (i + 0.5) / n, y0 + (y1 - y0) * (j + 0.5) / n) for i in range(n) for j in range(n)]


def _band_class(b):
    """Which interior class a candidate band's strip represents."""
    reason = (b["REASON"] or "").split(" (")[0]
    if b.get("BAND_TYPE") == "COLUMN_BAND" or b.get("LOOP") or reason in ("CLOSED_LOOP_UNRESOLVED", "COLUMN_CANDIDATE", "WALL_NIB_OR_PIER"):
        return "COLUMN_INTERIOR"
    if reason in ("THIN_PAIR_BELOW_WALL_MINIMUM", "FRAME_WITHIN_HOST_BAND", "MIXED_BLOCK_STRIP", "REPEATED_BLOCK_SYMBOL_STRIP", "THIN_BAND_UNCONFIRMED"):
        return "FRAME_INTERIOR"
    if reason in ("REPETITION_FAMILY", "ENCLOSES_PARALLEL_FACES", "BORROWED_FACES_STRIP"):
        return "FRAME_INTERIOR"
    if reason in ("CLOSED_OUTLINE_AGAINST_WALL", "CLOSED_OUTLINE_UNCONFIRMED", "ISOLATED_PAIR"):
        return "JOINERY_OR_FURNITURE_INTERIOR"
    return "WALL_BAND_INTERIOR"


def build(result, vid, semantic_of=None):
    """One forensic row per space, with the free-space class and whether it may become a floor region."""
    view = next(v for v in result.views if v["VIEW_ID"] == vid)
    faces = {f["FACE_ID"]: f for f in result.faces[vid]}
    seals, bands, grid = result.seals[vid], result.bands7[vid], result.grids7[vid]
    roles = result.roles[vid]
    label, meta = grid["label"], grid["meta"]
    vb = view.get("BBOX_MM")
    view_area = (vb[2] - vb[0]) * (vb[3] - vb[1]) if vb else 0.0
    strips = [b for b in bands if b["KIND"] == "S"]
    accepted_thk = [b["THK"] for b in bands if b["STATUS"] == "ACCEPTED" and b.get("BAND_TYPE") != "COLUMN_BAND"]
    # the thinnest material band the SOURCE itself contains: a free gap narrower than that is drafting space, not a room
    thinnest = min(accepted_thk) if accepted_thk else MB.WALL_MIN_MM
    sites = {s["SITE_ID"]: s for s in result.sites7[vid]}
    brows = defaultdict(list)
    for r_ in result.brows[vid]:
        if r_["SPACE_FACE_ID"]:
            brows[r_["SPACE_FACE_ID"]].append(r_)

    lines_in = defaultdict(list)
    for p in view["PRIMITIVES"]:
        if p.kind != "SEGMENT":
            continue
        rr, cc = _rc(meta, (p.x1 + p.x2) / 2, (p.y1 + p.y2) / 2)
        if 0 <= rr < label.shape[0] and 0 <= cc < label.shape[1] and label[rr, cc]:
            lines_in[int(label[rr, cc])].append(p)

    rows = []
    for sp in sorted(result.spaces[vid], key=lambda z: -z["AREA_GEOMETRIC_M2"]):
        f = faces[sp["FACE_ID"]]
        L = f["RUN_LABEL_NOT_A_KEY"]
        bbox = f["BBOX_MM"]
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        minor = min(w, h)
        pts = _probe_points(bbox)
        hits = defaultdict(int)
        for px, py in pts:
            for b in strips:
                if MB.in_strip(b, px, py, tol=0.0):
                    hits[b["KEY"]] += 1
        host = None
        for k, c in sorted(hits.items(), key=lambda kv: -kv[1]):
            b = next(x for x in strips if x["KEY"] == k)
            if c / len(pts) >= INTERIOR_SHARE_FOR_BAND and minor <= b["THK"] + meta["cell"]:
                host = b
                break
        idx = f.get("SEAL_INDEXES", [])
        outlines = sorted({tuple(seals[i]["OUTLINE_SIZE_MM"]) for i in idx if seals[i].get("OUTLINE")})
        rel = dict(f["BOUNDARY_RELATIONS"])
        mat_share = f["MATERIAL_BOUNDARY_SHARE"]
        anchors = [a.get("TEXT") for a in sp["ANCHORS"] if a.get("TEXT")]
        classes = [a.get("CLASS") for a in sp["ANCHORS"] if a.get("CLASS") and a.get("CLASS") != "UNKNOWN"]
        # only a ROOM_NAME makes a cell a named room.  A site note, a level stamp or an undecodable title-block string names
        # the sheet, not the space it happens to sit in: the 636 m2 plot region carries three of them and is not a room.
        room_names = [a.get("TEXT") for a in sp["ANCHORS"] if _is_room_label(a)]
        exterior = sp.get("SPACE_CLASS") in ("EXTERIOR", "EXTERIOR_LABELLED")
        stair_lines = [p.object_id for p in lines_in.get(L, []) if any(t in p.provenance.layer.upper() for t in STAIR_LAYER_TOKENS)]
        ann_lines = [p.object_id for p in lines_in.get(L, []) if roles.get(p.object_id, {}).get("ROLE") in ANNOTATION_ROLES]
        other_lines = [p for p in lines_in.get(L, []) if p.object_id not in stair_lines and p.object_id not in ann_lines]
        site_ids = sorted({seals[i].get("SITE_ID") for i in idx if seals[i].get("SITE_ID")})
        band_ids = sorted({seals[i].get("BAND_ID") for i in idx if seals[i].get("BAND_ID")})
        door_rel = [{"SITE_ID": s, "CLASS": sites[s]["CLASS"], "STATUS": sites[s]["STATUS"], "SPAN_MM": sites[s]["SPAN_MM"]} for s in site_ids if s in sites]

        is_stair = bool(stair_lines) or (host is not None and any(t in " ".join(sorted({p.provenance.layer.upper() for p in view["PRIMITIVES"] if p.object_id in host["FACES"]})) for t in STAIR_LAYER_TOKENS))
        roof = any(any(t in (a or "").upper() or t in (a or "") for t in ROOF_TOKENS) for a in anchors)

        if view_area and (w * h) / view_area >= SHEET_REGION_SHARE:
            cls = "SITE_OR_SHEET_REGION"
            why = (f"the cell's extent covers {(w * h) / view_area:.0%} of the whole view: it is the sheet's own region - the plot, the site "
                   f"and everything outside the building envelope - and the texts inside it are sheet notes, not room stamps")
        elif host is not None:
            cls = _band_class(host)
            why = (f"every interior probe of this cell lies inside the strip of band {host['KEY']} "
                   f"({round(host['THK'])} mm, {host['STATUS']}{', ' + (host['REASON'] or '').split(' (')[0] if host['REASON'] else ''}), and the cell's clear width "
                   f"{round(minor)} mm does not exceed that strip: it is that element's interior, not free space")
            if is_stair:
                cls, why = "STAIR_OR_LANDING_SPACE", why + "; stair-layer geometry runs through it"
        elif outlines:
            cls = "JOINERY_OR_FURNITURE_INTERIOR"
            why = f"the cell is sealed by the edges of a closed outline of unpaired material lines {outlines}: a niche, duct, counter or wardrobe interior, never floor of the room beside it"
        elif is_stair:
            cls = "STAIR_OR_LANDING_SPACE"
            why = f"stair-layer geometry ({stair_lines[:3]}) runs inside the cell: a stair flight or landing, measured by the stair trade, not as a floor-finish region"
        elif minor < thinnest:
            cls = "ARTIFACT_POCKET"
            why = (f"the cell's clear width {round(minor)} mm is below {round(thinnest)} mm, the thinnest material band this drawing itself contains: "
                   f"a drafting sliver between two elements, not a space a floor finish can occupy")
        elif ann_lines and not other_lines:
            cls = "ANNOTATION_ENCLOSURE"
            why = f"the only geometry inside the cell is annotation ({ann_lines[:3]}): a dimension or label enclosure"
        elif roof or exterior:
            cls = "OPEN_ROOF_OR_TERRACE"
            why = "the cell carries a roof / terrace label: an external region, kept separate from internal floor finishes"
        elif not room_names and anchors and mat_share < MATERIAL_SHARE_FOR_ROOM:
            cls = "ANNOTATION_ENCLOSURE"
            why = (f"the cell carries {len(anchors)} text anchor(s) but not one of them is a room name ({[str(a)[:24] for a in anchors[:3]]}): "
                   f"a site note, level stamp or title-block string that happens to fall inside the region; with only {mat_share:.2f} of the boundary material this is the sheet's own area, not a room")
        elif mat_share < MATERIAL_SHARE_FOR_ROOM and not room_names:
            cls = "ARTIFACT_POCKET" if len(set(band_ids)) <= 1 else "UNRESOLVED"
            why = (f"the cell carries no label and only {mat_share:.2f} of its boundary is material: it is more chord than wall"
                   + (f", and every chord belongs to one element ({band_ids[:1]}): a pocket of that element" if len(set(band_ids)) <= 1
                      else "; which element it belongs to is not decided, so it is left for human review"))
        elif room_names:
            wet = any(c in ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM") for c in classes)
            cls = "SERVICE_FREE_SPACE" if wet else "OCCUPIABLE_FREE_SPACE"
            why = (f"labelled free space ({anchors[:2]}) with {mat_share:.2f} of its boundary material and no element claiming its interior"
                   + ("; a wet-room class, which the trade treats separately" if wet else ""))
            why = f"room name {room_names[:2]} on a cell with {mat_share:.2f} of its boundary material and no element claiming its interior" + ("; a wet-room class, which the trade treats separately" if wet else "")
        else:
            cls = "UNRESOLVED"
            why = (f"an unlabelled cell of {sp['AREA_GEOMETRIC_M2']:.2f} m2 with {mat_share:.2f} material boundary that no element explains: "
                   f"it may be a real unlabelled room (a lobby, a shaft, a stair hall) or an artifact; HUMAN_REVIEW")

        rows.append({
            "CELL_ID": sp["SPACE_ID"], "FACE_ID": sp["FACE_ID"], "AREA_M2": sp["AREA_GEOMETRIC_M2"],
            "BBOX_MM": bbox, "CLEAR_WIDTH_MM": round(minor, 1),
            "BOUNDARY_IDS": band_ids, "BOUNDARY_TYPES": rel, "MATERIAL_BOUNDARY_SHARE": mat_share,
            "SEMANTIC_ANCHORS": anchors, "ROOM_NAMES": room_names, "SEMANTIC_CLASSES": sorted(set(classes)), "SPACE_CLASS": sp.get("SPACE_CLASS"),
            "DOOR_RELATIONS": door_rel, "ADJACENT_CELLS": [], "MATERIAL_BANDS": [x["BAND_ID"] for x in brows.get(sp["FACE_ID"], [])][:12],
            "IS_INSIDE_WALL_BAND": bool(host is not None and _band_class(host) == "WALL_BAND_INTERIOR"),
            "IS_FRAME_INTERIOR": bool(host is not None and _band_class(host) == "FRAME_INTERIOR"),
            "IS_COLUMN_INTERIOR": bool(host is not None and _band_class(host) == "COLUMN_INTERIOR"),
            "IS_STAIR_COMPONENT": bool(is_stair),
            "IS_FURNITURE_OR_CASEWORK_INTERIOR": bool(outlines) or bool(host is not None and _band_class(host) == "JOINERY_OR_FURNITURE_INTERIOR"),
            "IS_TRUE_FREE_SPACE": cls in FLOOR_ELIGIBLE_CLASSES,
            "HOST_ELEMENT": {"BAND_KEY": host["KEY"], "THICKNESS_MM": round(host["THK"], 1), "STATUS": host["STATUS"],
                             "REASON": host["REASON"]} if host is not None else None,
            "INTERIOR_PROBES_IN_A_STRIP": max(hits.values()) if hits else 0, "INTERIOR_PROBES": len(pts),
            "SPACE_ELIGIBILITY": cls,
            "MAY_BECOME_FLOOR_REGION": cls in FLOOR_ELIGIBLE_CLASSES,
            "REASON": why,
            "STATUS": "CLASSIFIED" if cls != "UNRESOLVED" else "HUMAN_REVIEW",
            "ENGINE_GEOMETRY_STATUS": sp["GEOMETRY_STATUS"],
        })
    return rows, {"THINNEST_ACCEPTED_BAND_MM": round(thinnest, 1), "RULE": "derived from this drawing's own accepted bands; never a fixed project constant"}


def room_adjacency(result, vid, cell_rows):
    """Room-to-room relations that see THROUGH the doorway pocket.

    A doorway is a cell of its own: the free strip inside the wall line between the two jambs.  Two rooms joined by a door are
    therefore not raster-adjacent to each other, they are each adjacent to that pocket.  A relation read from direct adjacency
    alone reports a door as a solid wall, which is how R1 mis-read the bath / dress partition.  Non-free-space cells are
    traversed here as connectors, and the site on the connector names the relation.
    """
    from research.qs_wall_treatment_01.pa08.qortuba.r1.reconcile import space_adjacency
    faces = {f["FACE_ID"]: f for f in result.faces[vid]}
    lab_of = {r["CELL_ID"]: faces[r["FACE_ID"]]["RUN_LABEL_NOT_A_KEY"] for r in cell_rows}
    cell_of_lab = {v: k for k, v in lab_of.items()}
    by_id = {r["CELL_ID"]: r for r in cell_rows}
    adj = space_adjacency(result.grids7[vid], result.seals[vid])
    sites = {s["SITE_ID"]: s for s in result.sites7[vid]}
    nb = defaultdict(list)
    for (a, b), e in adj.items():
        nb[a].append((b, e)); nb[b].append((a, e))
    rooms = [r["CELL_ID"] for r in cell_rows if r["MAY_BECOME_FLOOR_REGION"] or r["SPACE_ELIGIBILITY"] in ("STAIR_OR_LANDING_SPACE", "OPEN_ROOF_OR_TERRACE", "UNRESOLVED")]
    out = []
    for cid in rooms:
        la = lab_of[cid]
        for lb, e1 in nb.get(la, []):
            other = cell_of_lab.get(lb)
            if other is not None and other in rooms:
                out.append({"ROOM_A": cid, "ROOM_B": other, "VIA": None, "KINDS": dict(e1["KINDS"]),
                            "SITES": [{"SITE_ID": s, "CLASS": sites[s]["CLASS"], "STATUS": sites[s]["STATUS"], "SPAN_MM": sites[s]["SPAN_MM"]} for s in sorted(e1["SITES"]) if s in sites]})
                continue
            if other is not None:
                continue                                   # a classified non-room cell that is itself a listed room: handled above
            for lc, e2 in nb.get(lb, []):                   # one hop through the connector cell
                third = cell_of_lab.get(lc)
                if third is None or third == cid or third not in rooms:
                    continue
                sids = sorted(set(e1["SITES"]) | set(e2["SITES"]))
                kinds = Counter(e1["KINDS"]); kinds.update(e2["KINDS"])
                out.append({"ROOM_A": cid, "ROOM_B": third, "VIA": f"connector-cell-{lb}", "KINDS": dict(kinds),
                            "SITES": [{"SITE_ID": s, "CLASS": sites[s]["CLASS"], "STATUS": sites[s]["STATUS"], "SPAN_MM": sites[s]["SPAN_MM"]} for s in sids if s in sites]})
    # deduplicate, preferring a relation that carries a site
    best = {}
    for rel in out:
        k = tuple(sorted((rel["ROOM_A"], rel["ROOM_B"])))
        if k not in best or (rel["SITES"] and not best[k]["SITES"]):
            best[k] = rel
    for rel in best.values():
        s = rel["SITES"]
        if any("DOOR" in x["CLASS"] for x in s):
            rel["RELATION"] = "SEPARATED_BY_DOOR"
        elif any(x["CLASS"] in ("CONFIRMED_WINDOW_OPENING", "CONFIRMED_GLAZED_OPENING", "CONFIRMED_OPEN_PASSAGE") for x in s):
            rel["RELATION"] = "SEPARATED_BY_OPENING"
        elif s:
            rel["RELATION"] = "SEPARATED_BY_UNRESOLVED_SITE"
        elif "OPENING_CHORD" in rel["KINDS"]:
            rel["RELATION"] = "SEPARATED_BY_OPENING"
        elif "UNRESOLVED_CHORD" in rel["KINDS"]:
            rel["RELATION"] = "SEPARATED_BY_UNRESOLVED_BOUNDARY"
        else:
            rel["RELATION"] = "SEPARATED_BY_MATERIAL_WALL"
    return sorted(best.values(), key=lambda z: (z["ROOM_A"], z["ROOM_B"]))
