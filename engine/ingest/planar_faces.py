"""Planar face extraction and physical spaces (PA07D).

No seed grid.  The free mask of a view (everything that is not a barrier) is labelled into connected components:
every component is a planar face, whatever its size or shape, so a 0.40 m wide room, a triangular room, a shaft and
a courtyard all exist before anything decides whether they are spaces.  Barriers are the seals of the accepted
material bands (face lines over material intervals, zero-material chords across openings, junctions, unresolved
intervals and band ends), accepted column faces, and role-only glazing separators (topology only, never material).

Per face: BOUNDARY_RELATIONS (what its boundary cells touch), AREA_GEOMETRIC, HAS_MATERIAL_BOUNDARY, OPEN_RELATIONS,
CONTAINS_SEMANTIC_ANCHOR, EXTERIOR_STATUS, SPACE_ELIGIBILITY, STATUS.  A face inside an accepted band strip is the
wall interior (or an opening reveal) and is never a space.  Nothing is invented for an anchor: MISSING_SPACE_QA
raises ANCHOR_WITHOUT_SPACE instead.

Boundary lengths per space come from the band geometry, not from cell counting: every material face interval is cut
where other accepted bands (walls meeting it, columns bonded into it) occupy the face line, and each remaining stretch
is attributed to the planar face beside it.  Developed lengths on curved bands follow the arc.  (FM-P6-10, FM-P6-14 in
the sense that the extraction no longer depends on where seeds fall.)
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from scipy import ndimage

from engine.ingest import ids
from engine.ingest import material_bands as MB

CELL_MM = 50.0
MIN_FACE_CELLS = 4                 # below this a component is a rasterisation sliver, recorded but never a space
SAMPLE_MM = 10.0                   # face-line sampling step for junction cuts and side attribution
EXTERIOR_STATUSES = ("EXTERIOR_CONNECTED", "ENCLOSED")
ELIGIBILITY = ("ELIGIBLE", "MATERIAL_INTERIOR", "EXTERIOR_CONNECTED", "NO_MATERIAL_BOUNDARY", "SLIVER")
KIND_CODES = {"FACE": 1, "COLUMN_FACE": 2, "OPENING_CHORD": 3, "JUNCTION_CHORD": 4, "UNRESOLVED_CHORD": 5, "THICKNESS_CHORD": 6, "GLAZING_SEPARATOR": 7}
CODE_KINDS = {v: k for k, v in KIND_CODES.items()}


# ------------------------------------------------------------------ rasterisation
def _grid(box, cell):
    x0, y0, x1, y1 = box
    W = int(math.ceil((x1 - x0) / cell)) + 1
    H = int(math.ceil((y1 - y0) / cell)) + 1
    return H, W, {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "cell": cell, "H": H, "W": W}


def _rc(meta, x, y):
    return int((meta["y1"] - y) / meta["cell"]), int((x - meta["x0"]) / meta["cell"])


def rasterise(seals, box, cell=CELL_MM):
    """kind grid (uint8, KIND_CODES) and seal-index grid (int32, -1 = none) for the barrier polylines."""
    H, W, meta = _grid(box, cell)
    kind = np.zeros((H, W), np.uint8)
    idx = np.full((H, W), -1, np.int32)
    for i, s in enumerate(seals):
        code = KIND_CODES[s["KIND"]]
        pts = s["PTS"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(bx - ax, by - ay) / (cell * 0.5)) + 1)
            for k in range(n):
                t = k / (n - 1)
                r, c = _rc(meta, ax + (bx - ax) * t, ay + (by - ay) * t)
                if 0 <= r < H and 0 <= c < W:
                    # a material face wins over a chord in the same cell; a chord wins over nothing
                    if kind[r, c] == 0 or (code in (1, 2) and kind[r, c] not in (1, 2)):
                        kind[r, c] = code; idx[r, c] = i
    return kind, idx, meta


def glazing_separators(prims, roles):
    """Role-only separators: single glazing lines / arcs.  Topology barriers with zero material, provisional."""
    out = []
    for p in prims:
        if roles.get(p.object_id, {}).get("ROLE") not in ("GLAZING", "WINDOW_FRAME"):
            continue
        if p.kind == "SEGMENT":
            pts = [(p.x1, p.y1), (p.x2, p.y2)]
        elif p.kind == "ARC":
            sw = ((p.end_angle - p.start_angle) % (2 * math.pi)) or 2 * math.pi
            n = max(2, int(p.radius * sw / 50) + 1)
            pts = [(p.cx + p.radius * math.cos(p.start_angle + sw * k / n), p.cy + p.radius * math.sin(p.start_angle + sw * k / n)) for k in range(n + 1)]
        else:
            continue
        out.append({"KIND": "GLAZING_SEPARATOR", "SIDE": None, "BAND_ID": None, "INTERVAL_ID": None, "OBJECT_ID": p.object_id, "MATERIAL": False, "PTS": pts,
                    "NOTE": "role-only separator (PA06 role); closes topology, adds no material, provisional"})
    return out


# ------------------------------------------------------------------ faces
def label_faces(kind):
    free = kind == 0
    label, n = ndimage.label(free, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    return label, n


def _inside_band(bands, x, y):
    for b in bands:
        if MB.in_strip(b, x, y, tol=0.0):
            return b
    return None


def build(view_id, box, seals, bands, texts=(), cell=CELL_MM, source_id=None):
    """Planar faces of one view.  Returns (faces, grids) where grids = {label, kind, idx, meta}."""
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    kind, idx, meta = rasterise(seals, box, cell)
    label, n = label_faces(kind)
    H, W = label.shape
    faces = []
    objs = ndimage.find_objects(label)
    # boundary relations: for each free cell, the barrier kinds among its 4 neighbours
    pad = np.pad(kind, 1)
    neigh = [pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]]
    ipad = np.pad(idx, 1, constant_values=-1)
    ineigh = [ipad[:-2, 1:-1], ipad[2:, 1:-1], ipad[1:-1, :-2], ipad[1:-1, 2:]]
    for lab in range(1, n + 1):
        sl = objs[lab - 1]
        if sl is None:
            continue
        m = label[sl] == lab
        cells = int(m.sum())
        rs, cs = np.nonzero(m)
        r0, c0 = sl[0].start, sl[1].start
        cy = meta["y1"] - (rs.mean() + r0 + 0.5) * cell; cx = meta["x0"] + (cs.mean() + c0 + 0.5) * cell
        touches_edge = bool(sl[0].start == 0 or sl[1].start == 0 or sl[0].stop == H or sl[1].stop == W)
        rel = defaultdict(int); seal_ids = defaultdict(int)
        for nk, ni in zip(neigh, ineigh):
            k = nk[sl][m]; i = ni[sl][m]
            for code in np.unique(k):
                if code:
                    rel[CODE_KINDS[int(code)]] += int((k == code).sum())
            for sidx in np.unique(i):
                if sidx >= 0:
                    seal_ids[int(sidx)] += int((i == sidx).sum())
        boundary = sum(rel.values())
        # sample up to 25 cells to test whether the face lies inside an accepted band strip
        step = max(1, cells // 25)
        sample = list(zip(rs[::step], cs[::step]))[:25]
        inside = 0
        for r, c in sample:
            x = meta["x0"] + (c + c0 + 0.5) * cell; y = meta["y1"] - (r + r0 + 0.5) * cell
            if _inside_band(accepted, x, y):
                inside += 1
        material_interior = sample and inside >= 0.8 * len(sample)
        area = (cells + 0.5 * boundary) * cell * cell / 1e6      # free cells plus the half-cell strip under the barrier line (raster area basis, not a quantity)
        open_sites = sorted({seals[i].get("SITE_ID") for i in seal_ids if seals[i]["KIND"] == "OPENING_CHORD" and seals[i].get("SITE_ID")})
        unresolved_sites = sorted({seals[i].get("SITE_ID") for i in seal_ids if seals[i]["KIND"] == "UNRESOLVED_CHORD" and seals[i].get("SITE_ID")})
        has_material = rel.get("FACE", 0) + rel.get("COLUMN_FACE", 0) > 0
        if cells < MIN_FACE_CELLS:
            elig, status = "SLIVER", "NOT_A_SPACE"
        elif material_interior:
            elig, status = "MATERIAL_INTERIOR", "NOT_A_SPACE"
        elif touches_edge:
            elig, status = "EXTERIOR_CONNECTED", "NOT_A_SPACE"
        elif not has_material:
            elig, status = "NO_MATERIAL_BOUNDARY", "NOT_A_SPACE"
        else:
            elig = "ELIGIBLE"
            if unresolved_sites or rel.get("UNRESOLVED_CHORD", 0) or rel.get("GLAZING_SEPARATOR", 0):
                status = "BOUNDARY_PROVISIONAL"
            elif rel.get("THICKNESS_CHORD", 0) > 0.25 * max(boundary, 1):
                status = "BOUNDARY_PROVISIONAL"
            else:
                status = "ESTABLISHED"
        faces.append({"FACE_ID": ids.make_id("TOPOLOGY_REGION", "PF7", view_id, [round(cx), round(cy), cells], tol=cell).replace("TR-", "PF-"), "VIEW_ID": view_id, "SOURCE_ID": source_id,
                      "RUN_LABEL_NOT_A_KEY": lab, "CENTROID_MM": [round(cx, 1), round(cy, 1)], "CELLS": cells, "AREA_GEOMETRIC_M2": round(area, 4), "AREA_BASIS": f"raster {cell:.0f} mm: free cells + half-cell strip under the boundary; topology / eligibility only, never a quantity",
                      "BBOX_MM": [round(meta["x0"] + c0 * cell, 1), round(meta["y1"] - sl[0].stop * cell, 1), round(meta["x0"] + sl[1].stop * cell, 1), round(meta["y1"] - r0 * cell, 1)],
                      "BOUNDARY_RELATIONS": dict(rel), "BOUNDARY_CELLS": boundary, "MATERIAL_BOUNDARY_SHARE": round((rel.get("FACE", 0) + rel.get("COLUMN_FACE", 0)) / boundary, 3) if boundary else 0.0,
                      "HAS_MATERIAL_BOUNDARY": has_material, "OPEN_RELATIONS": open_sites, "UNRESOLVED_RELATIONS": unresolved_sites,
                      "CONTAINS_SEMANTIC_ANCHOR": [], "EXTERIOR_STATUS": "EXTERIOR_CONNECTED" if touches_edge else "ENCLOSED",
                      "MATERIAL_INTERIOR": bool(material_interior), "SPACE_ELIGIBILITY": elig, "STATUS": status, "SEAL_INDEXES": sorted(seal_ids)})
    grids = {"label": label, "kind": kind, "idx": idx, "meta": meta, "cell": cell}
    # anchors: room-name texts inside faces
    lab_of = {f["RUN_LABEL_NOT_A_KEY"]: f for f in faces}
    for t in texts:
        r, c = _rc(meta, t["X"], t["Y"])
        if 0 <= r < H and 0 <= c < W and label[r, c]:
            f = lab_of.get(int(label[r, c]))
            if f is not None:
                f["CONTAINS_SEMANTIC_ANCHOR"].append({"TEXT": t["TEXT"], "ROLE": t.get("ROLE"), "CLASS": t.get("CLASS"), "SOURCE_KIND": t.get("SOURCE_KIND", "CAD_TEXT")})
    return faces, grids


# ------------------------------------------------------------------ boundary lengths from band geometry
def _cut_runs(b, side_sign, t0, t1, others, step=SAMPLE_MM):
    """Sub-intervals of [t0, t1] on face `side_sign` of band b that no other accepted band occupies (junction / column stretches removed)."""
    if t1 - t0 <= 0:
        return [], []
    n = max(1, int((t1 - t0) / step))
    ts = [t0 + (t1 - t0) * (k + 0.5) / n for k in range(n)]
    occ = []
    for t in ts:
        x, y = MB.band_point(b, t, side_sign * (b["THK"] / 2 + 1.0))
        occ.append(any(MB.in_strip(h, x, y, tol=0.0) for h in others))
    free, cut = [], []
    start = None
    for k, o in enumerate(occ):
        tk0 = t0 + (t1 - t0) * k / n
        if not o and start is None:
            start = tk0
        if o and start is not None:
            free.append((start, tk0)); start = None
    if start is not None:
        free.append((start, t1))
    # occupied runs
    start = None
    for k, o in enumerate(occ):
        tk0 = t0 + (t1 - t0) * k / n
        if o and start is None:
            start = tk0
        if not o and start is not None:
            cut.append((start, tk0)); start = None
    if start is not None:
        cut.append((start, t1))
    return free, cut


def _near(b, h, margin=800.0):
    """Cheap bbox prefilter between two bands."""
    def bb(z):
        pts = [MB.band_point(z, z["EXTENT"][0]), MB.band_point(z, z["EXTENT"][1])]
        if z["KIND"] == "C":
            pts += [MB.band_point(z, z["EXTENT"][0] + (z["EXTENT"][1] - z["EXTENT"][0]) * k / 8) for k in range(1, 8)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        m = z["THK"] / 2 + margin
        return min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m
    a, c = bb(b), bb(h)
    return not (a[2] < c[0] or c[2] < a[0] or a[3] < c[1] or c[3] < a[1])


def boundary_faces(view_id, faces, grids, bands, intervals, seals):
    """PA07_SPACE_BOUNDARY_FACE_REGISTER rows: per eligible face, every band face stretch beside it, with developed lengths."""
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    by_id = {b["BAND_ID"]: b for b in accepted}
    label, meta, cell = grids["label"], grids["meta"], grids["cell"]
    H, W = label.shape
    face_of_label = {f["RUN_LABEL_NOT_A_KEY"]: f for f in faces}
    rows = []

    def label_at(x, y):
        r, c = _rc(meta, x, y)
        return int(label[r, c]) if 0 <= r < H and 0 <= c < W else 0

    def attribute(b, side_sign, t0, t1, kind, interval_id, site_id, material):
        others = [h for h in accepted if h is not b and _near(b, h)]
        free, cut = _cut_runs(b, side_sign, t0, t1, others) if kind in ("FACE", "COLUMN_FACE") else ([(t0, t1)], [])
        for a, c in free:
            if c - a < 1e-6:
                continue
            # look just outside the face, at 1.5 cells, at three points along the run; majority label
            labs = []
            for q in (0.25, 0.5, 0.75):
                # PA07R1 (FM-P7-17): the first labelled cell beyond the face cell, never a cell further out than that
                lab_q = 0
                for k in (0.6, 1.1, 1.6):
                    x, y = MB.band_point(b, a + (c - a) * q, side_sign * (b["THK"] / 2 + k * cell))
                    lab_q = label_at(x, y)
                    if lab_q:
                        break
                labs.append(lab_q)
            lab = max(set(labs), key=labs.count)
            f = face_of_label.get(lab)
            # PA07R2 (FM-R1-10): a curved face runs at the face radius, not on the axis: scale the axis parameter run by (R +- t/2) / R
            face_scale = (b["R_AXIS"] + side_sign * b["THK"] / 2) / b["R_AXIS"] if b["KIND"] == "C" else 1.0
            rows.append({"SPACE_FACE_ID": f["FACE_ID"] if f else None, "SPACE_ELIGIBILITY": f["SPACE_ELIGIBILITY"] if f else "NONE", "VIEW_ID": view_id, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": interval_id, "SITE_ID": site_id,
                         "SEAL_KIND": kind, "SIDE": "A" if side_sign < 0 else "B", "AXIAL_START": round(a, 1), "AXIAL_END": round(c, 1), "LENGTH_MM": round((c - a) * face_scale, 1), "MATERIAL": material,
                         "CURVATURE_TYPE": "ARC" if b["KIND"] == "C" else "STRAIGHT", "LENGTH_SOURCE": "BAND_DEVELOPED_GEOMETRY",
                         "FACE_POSITION_STATUS": "AMBIGUOUS_FACE_DOUBLING" if b["EVIDENCE"].get("FACE_DOUBLING") else "ESTABLISHED"})
        for a, c in cut:
            rows.append({"SPACE_FACE_ID": None, "SPACE_ELIGIBILITY": "NONE", "VIEW_ID": view_id, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": interval_id, "SITE_ID": None, "SEAL_KIND": "JUNCTION_CUT",
                         "SIDE": "A" if side_sign < 0 else "B", "AXIAL_START": round(a, 1), "AXIAL_END": round(c, 1), "LENGTH_MM": round(c - a, 1), "MATERIAL": True,
                         "CURVATURE_TYPE": "ARC" if b["KIND"] == "C" else "STRAIGHT", "LENGTH_SOURCE": "BAND_DEVELOPED_GEOMETRY", "FACE_POSITION_STATUS": "NOT_APPLICABLE",
                         "NOTE": "another accepted band occupies this stretch of the face (wall meeting it or bonded column): owned there, never counted here"})

    for iv in intervals:
        b = by_id.get(iv["HOST_BAND_ID"])
        if b is None:
            continue
        t0, t1 = iv["AXIAL_START"], iv["AXIAL_END"]
        kind = {"MATERIAL": "FACE", "OPENING": "OPENING_CHORD", "JUNCTION": "JUNCTION_CHORD", "UNRESOLVED": "UNRESOLVED_CHORD"}[iv["CLASS"]]
        for sign in (-1, +1):
            attribute(b, sign, t0, t1, kind, iv["INTERVAL_ID"], iv.get("SITE_ID"), kind == "FACE")
    for b in accepted:
        if b.get("BAND_TYPE") == "COLUMN_BAND":
            for sign in (-1, +1):
                attribute(b, sign, b["EXTENT"][0], b["EXTENT"][1], "COLUMN_FACE", None, None, True)
            # the two short sides: attributed by the face just beyond the end, unless a wall band occupies it
            others = [h for h in accepted if h is not b and _near(b, h)]
            for t, tag, sign in ((b["EXTENT"][0], "START", -1), (b["EXTENT"][1], "END", +1)):
                # PA07R1 (FM-P7-07): the short side is sampled across its length, not at one axis point
                probes = [MB.band_point(b, t + sign * 1.0, d) for d in (-0.4 * b["THK"], -0.2 * b["THK"], 0.0, 0.2 * b["THK"], 0.4 * b["THK"])]
                if any(MB.in_strip(h, x1, y1, tol=0.0) for h in others for x1, y1 in probes):
                    rows.append({"SPACE_FACE_ID": None, "SPACE_ELIGIBILITY": "NONE", "VIEW_ID": view_id, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None, "SEAL_KIND": "JUNCTION_CUT", "SIDE": tag,
                                 "AXIAL_START": round(t, 1), "AXIAL_END": round(t, 1), "LENGTH_MM": round(b["THK"], 1), "MATERIAL": True, "CURVATURE_TYPE": "STRAIGHT", "LENGTH_SOURCE": "BAND_DEVELOPED_GEOMETRY",
                                 "FACE_POSITION_STATUS": "NOT_APPLICABLE", "NOTE": "column short side inside a wall band (embedded)"})
                    continue
                x, y = MB.band_point(b, t + sign * 1.5 * cell)
                f = face_of_label.get(label_at(x, y))
                rows.append({"SPACE_FACE_ID": f["FACE_ID"] if f else None, "SPACE_ELIGIBILITY": f["SPACE_ELIGIBILITY"] if f else "NONE", "VIEW_ID": view_id, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None,
                             "SEAL_KIND": "COLUMN_FACE", "SIDE": tag, "AXIAL_START": round(t, 1), "AXIAL_END": round(t, 1), "LENGTH_MM": round(b["THK"], 1), "MATERIAL": True, "CURVATURE_TYPE": "STRAIGHT",
                             "LENGTH_SOURCE": "BAND_DEVELOPED_GEOMETRY", "FACE_POSITION_STATUS": "ESTABLISHED"})
    return rows


def space_register(view_id, faces, boundary_rows, storey_id=None):
    """PA07_PHYSICAL_SPACE_REGISTER rows from eligible planar faces and their boundary composition."""
    by_face = defaultdict(list)
    for r in boundary_rows:
        if r["SPACE_FACE_ID"]:
            by_face[r["SPACE_FACE_ID"]].append(r)
    rows = []
    for f in faces:
        if f["SPACE_ELIGIBILITY"] != "ELIGIBLE":
            continue
        rs = by_face.get(f["FACE_ID"], [])
        comp = defaultdict(float)
        for r in rs:
            comp[r["SEAL_KIND"]] = round(comp[r["SEAL_KIND"]] + r["LENGTH_MM"], 1)
        material = round(sum(r["LENGTH_MM"] for r in rs if r["MATERIAL"]), 1)
        doubled = round(sum(r["LENGTH_MM"] for r in rs if r["MATERIAL"] and r["FACE_POSITION_STATUS"] != "ESTABLISHED"), 1)
        rows.append({"SPACE_ID": ids.make_id("PHYSICAL_SPACE", "PS7", view_id, f["CENTROID_MM"], f["CELLS"], tol=50.0), "FACE_ID": f["FACE_ID"], "VIEW_ID": view_id, "STOREY_ID": storey_id,
                     "AREA_GEOMETRIC_M2": f["AREA_GEOMETRIC_M2"], "BOUNDARY_COMPOSITION_MM": dict(comp), "MATERIAL_BOUNDARY_MM": material, "MATERIAL_BOUNDARY_FACE_DOUBLED_MM": doubled,
                     "OPENING_MM": comp.get("OPENING_CHORD", 0.0), "UNRESOLVED_MM": comp.get("UNRESOLVED_CHORD", 0.0), "COLUMN_FACE_MM": comp.get("COLUMN_FACE", 0.0),
                     "OPEN_RELATIONS": f["OPEN_RELATIONS"], "UNRESOLVED_RELATIONS": f["UNRESOLVED_RELATIONS"], "ANCHORS": f["CONTAINS_SEMANTIC_ANCHOR"],
                     "IDENTITY_STATUS": ("SINGLE" if len([a for a in f["CONTAINS_SEMANTIC_ANCHOR"] if a.get("ROLE") == "ROOM_NAME"]) == 1 else
                                         ("MULTIPLE" if len([a for a in f["CONTAINS_SEMANTIC_ANCHOR"] if a.get("ROLE") == "ROOM_NAME"]) > 1 else "NONE")),
                     # PA07R2 (gate Q03): a boundary that carries any unresolved chord is provisional whatever the raster status says
                     "GEOMETRY_STATUS": "BOUNDARY_PROVISIONAL" if comp.get("UNRESOLVED_CHORD", 0.0) > 0 else f["STATUS"], "MATERIAL_PRESENT_ON_CHORDS": False,
                     "PROVENANCE": {"RULE": "planar face of the free mask bounded by accepted band faces; lengths from band developed geometry cut at junctions"}})
    return rows


def missing_space_qa(faces, spaces, anchors_all):
    """ANCHOR_WITHOUT_SPACE, SPACE_WITHOUT_IDENTITY, MULTIPLE_ANCHORS_ONE_SPACE, OPEN_REGION, POSSIBLE_MISSED_SPACE.  Never invents a room."""
    issues = []
    elig = {f["FACE_ID"]: f for f in faces if f["SPACE_ELIGIBILITY"] == "ELIGIBLE"}
    for f in faces:
        rooms = [a for a in f["CONTAINS_SEMANTIC_ANCHOR"] if a.get("ROLE") == "ROOM_NAME"]
        if f["SPACE_ELIGIBILITY"] == "ELIGIBLE":
            if not rooms:
                issues.append({"KIND": "SPACE_WITHOUT_IDENTITY", "FACE_ID": f["FACE_ID"], "AREA_M2": f["AREA_GEOMETRIC_M2"], "NOTE": "physical space with no room label inside; identity UNRESOLVED, geometry stands"})
            elif len(rooms) > 1:
                issues.append({"KIND": "MULTIPLE_ANCHORS_ONE_SPACE", "FACE_ID": f["FACE_ID"], "LABELS": [a["TEXT"] for a in rooms], "NOTE": "several labels in one planar face: open plan, or a missed separator; never merged into one identity"})
            if f["OPEN_RELATIONS"]:
                issues.append({"KIND": "OPEN_REGION", "FACE_ID": f["FACE_ID"], "SITES": f["OPEN_RELATIONS"], "NOTE": "bounded partly by opening chords (zero material)"})
        else:
            if rooms:
                issues.append({"KIND": "ANCHOR_WITHOUT_SPACE", "FACE_ID": f["FACE_ID"], "LABELS": [a["TEXT"] for a in rooms], "ELIGIBILITY": f["SPACE_ELIGIBILITY"],
                               "NOTE": "a room label sits in a face that is not a space (exterior-connected, no material boundary, wall interior); no room is invented"})
                if f["SPACE_ELIGIBILITY"] in ("EXTERIOR_CONNECTED", "NO_MATERIAL_BOUNDARY") and f["HAS_MATERIAL_BOUNDARY"]:
                    issues.append({"KIND": "POSSIBLE_MISSED_SPACE", "FACE_ID": f["FACE_ID"], "LABELS": [a["TEXT"] for a in rooms], "NOTE": "labelled region with some material boundary leaks to the outside: a missing band, an unresolved opening or an open site"})
    placed = {a["TEXT"] for f in faces for a in f["CONTAINS_SEMANTIC_ANCHOR"]}
    for a in anchors_all:
        if a.get("ROLE") == "ROOM_NAME" and a["TEXT"] not in placed:
            issues.append({"KIND": "ANCHOR_WITHOUT_SPACE", "FACE_ID": None, "LABELS": [a["TEXT"]], "ELIGIBILITY": "ON_BARRIER_OR_OUTSIDE_VIEW", "NOTE": "label insertion point falls on a barrier cell or outside the view"})
    return issues


def summarise(faces, spaces, issues):
    out = {"FACES": len(faces), "BY_ELIGIBILITY": defaultdict(int), "SPACES": len(spaces), "SPACES_BY_STATUS": defaultdict(int), "IDENTITY": defaultdict(int), "QA": defaultdict(int),
           "MATERIAL_BOUNDARY_M_STRUCTURE_ONLY": 0.0, "OPENING_M": 0.0, "UNRESOLVED_M": 0.0}
    for f in faces:
        out["BY_ELIGIBILITY"][f["SPACE_ELIGIBILITY"]] += 1
    for s in spaces:
        out["SPACES_BY_STATUS"][s["GEOMETRY_STATUS"]] += 1
        out["IDENTITY"][s["IDENTITY_STATUS"]] += 1
        out["MATERIAL_BOUNDARY_M_STRUCTURE_ONLY"] = round(out["MATERIAL_BOUNDARY_M_STRUCTURE_ONLY"] + s["MATERIAL_BOUNDARY_MM"] / 1000, 3)
        out["OPENING_M"] = round(out["OPENING_M"] + s["OPENING_MM"] / 1000, 3)
        out["UNRESOLVED_M"] = round(out["UNRESOLVED_M"] + s["UNRESOLVED_MM"] / 1000, 3)
    for i in issues:
        out["QA"][i["KIND"]] += 1
    for k in ("BY_ELIGIBILITY", "SPACES_BY_STATUS", "IDENTITY", "QA"):
        out[k] = dict(out[k])
    return out
