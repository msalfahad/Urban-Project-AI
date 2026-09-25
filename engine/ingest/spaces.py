"""Physical space builder v2 (PA05 §9) and semantic anchors (§3).

Topology regions are flood-filled with a closure inserted at EVERY opening
site (the site's chord), so a missing door leaf never merges two spaces.
The site classification then states the relation between the spaces
(door, passage, unresolved).  Region numbers are never keys: each
physical space is identified by an interior anchor and its bounding
entities.  Semantic identity is a separate object attached by anchors.
"""

from __future__ import annotations

import math

import numpy as np

from engine import plan_regions as PR
from engine.ingest import ids

CELL_MM = 50
MIN_SPACE_M2, MAX_SPACE_M2 = 0.8, 400.0


def _prim_tuples(prims):
    out = []
    for p in prims:
        if p.kind == "SEGMENT":
            out.append(("SEGMENT", p.object_id, p.provenance.layer, p.x1, p.y1, p.x2, p.y2, None, None, None, None, None))
        elif p.kind == "ARC":
            out.append(("ARC", p.object_id, p.provenance.layer, None, None, None, None, p.cx, p.cy, p.radius, p.start_angle, p.end_angle))
        elif p.kind == "CIRCLE":
            out.append(("CIRCLE", p.object_id, p.provenance.layer, None, None, None, None, p.cx, p.cy, p.radius, None, None))
    return out


def build(view, layers, sites, faces, entity_ids, cell=CELL_MM):
    """Returns physical spaces for one plan view."""
    x0, y0, x1, y1 = view["BBOX_MM"]
    box = (x0 - 500, y0 - 500, x1 + 500, y1 + 500)
    tuples = _prim_tuples(view["PRIMITIVES"])
    # closures at every opening site: a synthetic barrier line on a reserved pseudo-layer
    for s in sites:
        (ax, ay), (bx, by) = s["CHORD_MM"]
        tuples.append(("SEGMENT", "SITE:" + s["OPENING_SITE_ID"], "__SITE__", ax, ay, bx, by, None, None, None, None, None))
    wall, door, meta = PR.rasterise(tuples, box, cell, wall_layers=tuple(layers["WALL_LAYERS"]), door_layers=tuple([l for l in (layers.get("DOOR_LAYER"),) if l] + ["__SITE__"]))
    seeds, k = {}, 0
    for x in np.arange(box[0] + 500, box[2], 1000):
        for y in np.arange(box[1] + 500, box[3], 1000):
            seeds[k] = (float(x), float(y)); k += 1
    label, _ = PR.flood(wall, door, seeds, meta, max_cells=4_000_000)
    labs, counts = np.unique(label[label > 0], return_counts=True)
    id_of_site = {"SITE:" + s["OPENING_SITE_ID"]: s for s in sites}
    spaces = []
    for lab, n in zip(labs, counts):
        area = float(n) * (cell / 1000) ** 2
        if area < MIN_SPACE_M2 or area > MAX_SPACE_M2:
            continue
        rs, cs = np.where(label == lab)
        r0, c0 = rs.mean(), cs.mean()
        kk = int(np.argmin((rs - r0) ** 2 + (cs - c0) ** 2))
        anchor = (meta["x0"] + cs[kk] * cell + cell / 2, meta["y1"] - rs[kk] * cell - cell / 2)
        runs = PR.merge_collinear(PR.boundary_faces(label, wall, door, int(lab), meta, min_run_cells=2))
        bounding, site_hits, open_edges, unresolved = set(), {}, [], []
        for run in runs:
            for e in run["ENTITY_IDS"]:
                if e.startswith("SITE:"):
                    site_hits[e] = round(site_hits.get(e, 0.0) + run["LENGTH_M"], 3)
                elif e in entity_ids:
                    bounding.add(entity_ids[e])
            if run["CLASS"] == "OPEN":
                open_edges.append({"LENGTH_M": run["LENGTH_M"], "GEOM": run["GEOM"]})
            if run["CLASS"] == "EDGE":
                unresolved.append({"LENGTH_M": run["LENGTH_M"], "GEOM": run["GEOM"]})
        site_rel = []
        for sk, lm in site_hits.items():
            s = id_of_site[sk]
            site_rel.append({"OPENING_SITE_ID": s["OPENING_SITE_ID"], "CLASS": s["CLASS"], "BOUNDARY_LM": lm})
        sid = ids.space_id(view["VIEW_ID"], anchor, sorted(bounding))
        wall_lm = round(sum(r["LENGTH_M"] for r in runs if r["CLASS"] == "WALL" and r["LENGTH_M"] >= 0.25), 3)
        spaces.append({"PHYSICAL_SPACE_ID": sid, "VIEW": view["VIEW_ID"], "TOPOLOGY_REGION_ID": ids.region_id(view["VIEW_ID"], anchor, area), "RUN_LABEL_NOT_A_KEY": int(lab),
                       "ANCHOR_MM": [round(anchor[0], 1), round(anchor[1], 1)], "AREA_M2": round(area, 3), "BOUNDARY_CHAIN": sorted(bounding), "WALL_BOUNDARY_LM": wall_lm,
                       "OPENING_SITES": site_rel, "OPEN_EDGES": open_edges, "UNRESOLVED_EDGES": unresolved,
                       "TOPOLOGY_STATUS": "CLOSED_BY_MATERIAL" if not site_rel and not open_edges and not unresolved else ("CLOSED_WITH_SITES" if not open_edges and not unresolved else "PARTIALLY_OPEN"),
                       "SEMANTIC_IDENTITY": None})
    # attach side spaces to atomic faces by probing the label grid
    lab_of = {s["RUN_LABEL_NOT_A_KEY"]: s["PHYSICAL_SPACE_ID"] for s in spaces}
    H, W = label.shape
    for f in faces:
        px, py = f["PROBE_MM"]
        r, c = int((meta["y1"] - py) / cell), int((px - meta["x0"]) / cell)
        f["SIDE_A_SPACE"] = lab_of.get(int(label[r, c])) if 0 <= r < H and 0 <= c < W and label[r, c] > 0 else None
    # pair the two faces of one entity
    by_ent = {}
    for f in faces:
        by_ent.setdefault(f["ENTITY_ID"], []).append(f)
    for fs in by_ent.values():
        if len(fs) == 2:
            fs[0]["SIDE_B_SPACE"], fs[1]["SIDE_B_SPACE"] = fs[1]["SIDE_A_SPACE"], fs[0]["SIDE_A_SPACE"]
    return spaces, {"label": label, "meta": meta}


def anchors(view, spaces, grid, texts, printed_labels=(), owner_anchors=()):
    """Semantic anchors: DWG text insertions (and optional printed / owner anchors) mapped to the space that contains them.
    GEOMETRY_ID and SEMANTIC_IDENTITY stay separate; a label nearby never renames geometry."""
    label, meta = grid["label"], grid["meta"]
    lab_of = {s["RUN_LABEL_NOT_A_KEY"]: s for s in spaces}
    x0, y0, x1, y1 = view["BBOX_MM"]
    out = []
    def place(atype, text, pos, source, conf):
        px, py = pos
        if not (x0 <= px <= x1 and y0 <= py <= y1):
            return
        r, c = int((meta["y1"] - py) / meta["cell"]), int((px - meta["x0"]) / meta["cell"])
        inside = lab_of.get(int(label[r, c])) if 0 <= r < label.shape[0] and 0 <= c < label.shape[1] and label[r, c] > 0 else None
        cands = [inside["PHYSICAL_SPACE_ID"]] if inside else []
        if not inside:
            near = sorted(spaces, key=lambda s: math.hypot(s["ANCHOR_MM"][0] - px, s["ANCHOR_MM"][1] - py))[:2]
            cands = [s["PHYSICAL_SPACE_ID"] for s in near]
        out.append({"ANCHOR_ID": ids.anchor_id(view["VIEW_ID"], atype, text, pos), "SOURCE": source, "ANCHOR_TYPE": atype, "TEXT": text, "POSITION_MM": [round(px, 1), round(py, 1)],
                    "CANDIDATE_PHYSICAL_SPACES": cands, "ASSIGNED_PHYSICAL_SPACE": inside["PHYSICAL_SPACE_ID"] if inside else None,
                    "STATUS": "ASSIGNED" if inside else ("CANDIDATES_ONLY" if cands else "UNPLACED"), "CONFIDENCE_CLASS": conf if inside else "LOW",
                    "PROVENANCE": {"VIEW": view["VIEW_ID"], "RULE": "text insertion inside exactly one closed topology region"}})
    for t in texts:
        place("DWG_TEXT", t["TEXT"], (t["X"], t["Y"]), {"KIND": "CAD_TEXT", "LAYER": t.get("LAYER"), "HANDLE": t.get("HANDLE")}, "HIGH")
    for p in printed_labels:
        place("PRINTED_LABEL", p["TEXT"], (p["X"], p["Y"]), {"KIND": "RASTER_LABEL_VIA_TRANSFORM", "PAGE": p.get("PAGE")}, "MEDIUM")
    for o in owner_anchors:
        place("OWNER_CONFIRMED", o["TEXT"], (o["X"], o["Y"]), {"KIND": "OWNER_INPUT", "ID": o.get("ID")}, "HIGH")
    # attach to spaces without renaming geometry
    by_space = {}
    for a in out:
        if a["ASSIGNED_PHYSICAL_SPACE"]:
            by_space.setdefault(a["ASSIGNED_PHYSICAL_SPACE"], []).append(a)
    for s in spaces:
        al = by_space.get(s["PHYSICAL_SPACE_ID"], [])
        texts_ = sorted({a["TEXT"] for a in al})
        s["SEMANTIC_IDENTITY"] = {"ANCHORS": [a["ANCHOR_ID"] for a in al], "TEXTS": texts_, "STATUS": "NONE" if not al else ("SINGLE" if len(texts_) == 1 else "MULTIPLE_LABELS_ONE_TOPOLOGY_CELL"),
                                  "NOTE": None if len(texts_) <= 1 else "one topology region holds several labels: several functional rooms or a missing separator; identity per room is NOT_ESTABLISHED"}
    return out
