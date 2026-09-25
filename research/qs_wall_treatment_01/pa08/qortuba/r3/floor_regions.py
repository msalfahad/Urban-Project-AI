"""PA08-QORTUBA-R3: the floor-finish MEASUREMENT region, which is not the physical wall model.

R2 was right to hold the physical wall model conservative, and wrong to let that decide the floor.  Where a floor finish stops is
a question about LINES, not about material roles: a room whose every boundary line is drawn has a measurable clear floor polygon
even when the engine cannot say whether the thing standing on one of those lines is a block wall, a duct or a lining.

The discriminator used here is THICKNESS EVIDENCE, not layer names and not labels:

  * a PAIRED band - two parallel faces at a candidate thickness - means something with a thickness stands on that line, whatever
    its material role turns out to be.  The floor stops there.  Basis: CAD_FACE_LINE_UNRESOLVED_ROLE.
  * an UNPAIRED single line has no thickness evidence at all.  It may be a partition, a glazing line, a furniture edge or an
    overhead element, and it cannot say where a floor stops.  The measurement region is assembled ACROSS it and the crossing is
    recorded, reversibly.
  * a door or passage is closed by a THRESHOLD_CLOSURE: zero material, no wall, no geometry authority, reversible.

Nothing here writes back into the physical layer.  A measurement closure never becomes a wall, and a floor region that is
established never promotes the material status of the band beside it.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np

from engine.ingest import material_bands as MB, planar_faces as PF

FLOOR_BOUNDARY_BASES = ("ESTABLISHED_WALL_FACE", "COLUMN_FACE", "WALL_INTERIOR_CHORD", "CAD_FACE_LINE_UNRESOLVED_ROLE",
                        "THRESHOLD_CLOSURE", "OPEN_EDGE_CLOSURE", "JOINERY_OUTLINE_EDGE")
NON_FLOOR_BOUNDARY_BASES = ("UNPAIRED_LINE_NO_THICKNESS_EVIDENCE",)
ESTABLISHING_BASES = FLOOR_BOUNDARY_BASES          # every one of these fixes a line the floor stops at
SNAP_MM = 2.0
AREA_AGREEMENT_SHARE = 0.03
AREA_AGREEMENT_MIN_M2 = 0.25


def seal_basis(seal, bands_by_id, sites_by_id):
    """The measurement basis a single seal provides, and whether the floor stops there."""
    kind = seal["KIND"]
    b = bands_by_id.get(seal.get("BAND_ID"))
    if kind == "FACE":
        if b is not None and b["STATUS"] == "ACCEPTED":
            return "ESTABLISHED_WALL_FACE", True, f"face of established band {seal['BAND_ID']}"
        return "CAD_FACE_LINE_UNRESOLVED_ROLE", True, f"drawn face line of band {seal.get('BAND_ID')} ({b['STATUS'] if b else '?'}): a paired thickness stands here whatever its material role"
    if kind == "COLUMN_FACE":
        return "COLUMN_FACE", True, "face of a column band"
    if kind == "THICKNESS_CHORD":
        return "WALL_INTERIOR_CHORD", True, "chord across a band's thickness: the floor stops at the element, never inside it"
    if kind == "JUNCTION_CHORD":
        return "ESTABLISHED_WALL_FACE", True, "junction chord: another wall occupies this stretch"
    if kind == "OPENING_CHORD":
        s = sites_by_id.get(seal.get("SITE_ID"))
        if s and s["CLASS"] == "CONFIRMED_OPEN_PASSAGE":
            return "OPEN_EDGE_CLOSURE", True, "confirmed open passage: the region is closed across it for measurement only"
        return "THRESHOLD_CLOSURE", True, f"door / opening threshold ({s['CLASS'] if s else 'opening'}): the region is closed on the jamb line for measurement only"
    if kind == "GLAZING_SEPARATOR":
        return "CAD_FACE_LINE_UNRESOLVED_ROLE", True, "glazing separator line"
    if kind == "UNRESOLVED_CHORD":
        if seal.get("OUTLINE"):
            return "JOINERY_OUTLINE_EDGE", True, f"edge of a closed outline of material lines {seal.get('OUTLINE_SIZE_MM')}: something is drawn standing here"
        if seal.get("OBJECT_ID") and seal.get("BAND_ID") is None:
            return "UNPAIRED_LINE_NO_THICKNESS_EVIDENCE", False, (f"single line {seal['OBJECT_ID']} with no parallel face anywhere: no thickness evidence, so it cannot fix where a floor stops; "
                                                                  f"the measurement region is assembled across it and the crossing is recorded")
        return "CAD_FACE_LINE_UNRESOLVED_ROLE", True, f"face or full-extent chord of paired band {seal.get('BAND_ID')} ({b['STATUS'] if b else '?'}): a paired thickness stands here"
    return "CAD_FACE_LINE_UNRESOLVED_ROLE", True, f"seal of kind {kind}"


def measurement_components(result, vid):
    """Re-label the raster with every NON-floor-boundary seal erased.

    A line with no thickness evidence does not bound a floor region, so the honest way to find the region is to remove exactly
    those lines and see what is then one connected piece of floor.  This is threshold-free: an incidental corner contact of a
    few cells does not join two rooms, and a genuine crossing does.
    """
    grid = result.grids7[vid]
    kind, idx = grid["kind"], grid["idx"]
    seals = result.seals[vid]
    bands_by_id = {b["BAND_ID"]: b for b in result.bands7[vid]}
    sites_by_id = {s["SITE_ID"]: s for s in result.sites7[vid]}
    non_fixing = [i for i, s in enumerate(seals) if not seal_basis(s, bands_by_id, sites_by_id)[1]]
    k2 = kind.copy()
    if non_fixing:
        k2[np.isin(idx, non_fixing) & (kind > 0)] = 0
    comp, _ = PF.label_faces(k2)
    return comp, non_fixing


def assemble(result, vid, seed_face_id, cell_class_of, comp=None, non_fixing=None):
    """The measurement region for one room: every physical cell that shares a connected piece of floor with the seed once the
    non-boundary lines are removed.  Returns (labels, crossings); each crossing is recorded so the assembly is reversible."""
    if comp is None:
        comp, non_fixing = measurement_components(result, vid)
    grid = result.grids7[vid]
    label = grid["label"]
    faces = {f["FACE_ID"]: f for f in result.faces[vid]}
    seed = faces[seed_face_id]["RUN_LABEL_NOT_A_KEY"]
    seed_cells = label == seed
    ids, counts = np.unique(comp[seed_cells], return_counts=True)
    ids = [int(i) for i, c in zip(ids.tolist(), counts.tolist()) if i]
    if not ids:
        return [seed], []
    target = int(ids[int(np.argmax([int((comp[seed_cells] == i).sum()) for i in ids]))])
    members, crossings = {seed}, []
    lab_of_face = {f["RUN_LABEL_NOT_A_KEY"]: f["FACE_ID"] for f in result.faces[vid]}
    other = np.unique(label[(comp == target) & (label > 0)])
    for o in other.tolist():
        o = int(o)
        if o == seed or o == 0:
            continue
        fid = lab_of_face.get(o)
        cls = cell_class_of.get(fid)
        if cls in ("OCCUPIABLE_FREE_SPACE", "SERVICE_FREE_SPACE", "OPEN_ROOF_OR_TERRACE", "STAIR_OR_LANDING_SPACE"):
            crossings.append({"TO_LABEL": o, "TO_FACE_ID": fid, "TO_CELL_CLASS": cls, "MERGED": False,
                              "WHY": "another room, roof or stair shares this connected piece of floor once the non-boundary lines are removed: never absorbed, recorded as a conflict",
                              "MATERIAL_PRESENT": False, "PHYSICAL_WALL": False, "GEOMETRY_AUTHORITY": False, "REVERSIBLE": True})
            continue
        members.add(o)
        crossings.append({"TO_LABEL": o, "TO_FACE_ID": fid, "TO_CELL_CLASS": cls, "MERGED": True,
                          "WHY": "separated from the seed only by lines with no thickness evidence, so it is part of the same clear floor region",
                          "MATERIAL_PRESENT": False, "PHYSICAL_WALL": False, "GEOMETRY_AUTHORITY": False, "REVERSIBLE": True})
    return sorted(members), crossings


def region_cells(result, vid, labels, non_fixing=None):
    """The raster cells the assembled region occupies, and the barrier grid that goes with them.

    A line with no thickness evidence was erased to assemble the region, so the floor drawn under it belongs to the region -
    but only where this region lies on BOTH sides of it.  Where the far side is a room this region refused to absorb, that line
    is the closure this region stops at, and its cells are not this region's floor.  The cells that are taken in stop being
    barriers, so the polygon and the raster cross-check describe the same piece of floor.
    """
    grid = result.grids7[vid]
    label, kind, idx = grid["label"], grid["kind"], grid["idx"]
    member = {int(l) for l in labels}
    mask = np.isin(label, sorted(member))
    k2 = kind.copy()
    if not non_fixing:
        return mask, k2
    H, W = label.shape
    erased = np.isin(idx, sorted(non_fixing)) & (kind > 0)
    if not erased.any():
        return mask, k2
    # a cell of an erased line is disqualified as soon as ONE of its four neighbours is floor this region does not own
    out = np.zeros_like(erased)
    rs, cs = np.nonzero(erased)
    for rr, cc in zip(rs.tolist(), cs.tolist()):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r2, c2 = rr + dr, cc + dc
            if not (0 <= r2 < H and 0 <= c2 < W):
                continue
            l2 = int(label[r2, c2])
            if (l2 and l2 not in member) or (l2 == 0 and kind[r2, c2] == 0):
                out[rr, cc] = True
                break
    takeable = erased & ~out
    grown = mask.copy()
    while True:
        pad = np.pad(grown, 1)
        touch = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        add = takeable & touch & ~grown
        if not add.any():
            break
        grown |= add
    taken = grown & ~mask
    k2[taken] = 0
    return grown, k2


def _snap(vals):
    out = []
    for v in sorted(vals):
        if not out or v - out[-1] > SNAP_MM:
            out.append(v)
    return out


def polygon(result, vid, labels, seal_indexes, non_fixing=None):
    """Arrangement area over a SET of raster labels: the axis-aligned lines that bound the assembled region are the cut lines."""
    grid = result.grids7[vid]
    label, meta, cell = grid["label"], grid["meta"], grid["cell"]
    seals = result.seals[vid]
    xs, ys, skew = set(), set(), []
    for i in seal_indexes:
        pts = seals[i]["PTS"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if abs(ax - bx) <= 1e-6 and abs(ay - by) <= 1e-6:
                continue
            if abs(ax - bx) <= 1e-6:
                xs.add(round(ax, 3))
            elif abs(ay - by) <= 1e-6:
                ys.add(round(ay, 3))
            else:
                skew.append({"SEAL_KIND": seals[i]["KIND"], "OBJECT_ID": seals[i].get("OBJECT_ID"), "P1": [round(ax, 1), round(ay, 1)], "P2": [round(bx, 1), round(by, 1)]})
    xs, ys = _snap(xs), _snap(ys)
    if len(xs) < 2 or len(ys) < 2:
        return None, {"METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES", "STATUS": "NOT_ESTABLISHED", "WHY": f"only {len(xs)} vertical and {len(ys)} horizontal boundary lines: not a closed region", "SKEW_SEGMENTS": skew}
    H, W = label.shape
    mask, kindg = region_cells(result, vid, labels, non_fixing)
    rects, area = [], 0.0
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rr, cc = int((meta["y1"] - cy) / cell), int((cx - meta["x0"]) / cell)
            if 0 <= rr < H and 0 <= cc < W and mask[rr, cc]:
                a = (x1 - x0) * (y1 - y0) / 1e6
                area += a
                rects.append({"X_MM": [round(x0, 1), round(x1, 1)], "Y_MM": [round(y0, 1), round(y1, 1)], "W_MM": round(x1 - x0, 1), "D_MM": round(y1 - y0, 1), "AREA_M2": round(a, 4)})
    # the same raster basis the physical layer uses: free cells plus the half-cell strip under the bounding line, so the
    # cross-check compares like with like (planar_faces.build, AREA_BASIS)
    bpad = np.pad(kindg, 1)
    barrier = ((bpad[:-2, 1:-1] > 0).astype(int) + (bpad[2:, 1:-1] > 0).astype(int) + (bpad[1:-1, :-2] > 0).astype(int) + (bpad[1:-1, 2:] > 0).astype(int))
    boundary_cells = int(barrier[mask].sum())
    raster = (float(mask.sum()) + 0.5 * boundary_cells) * cell * cell / 1e6
    tol = max(AREA_AGREEMENT_MIN_M2, AREA_AGREEMENT_SHARE * max(raster, 1e-9))
    fml = {"METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES", "CUT_LINES_X_MM": [round(v, 1) for v in xs], "CUT_LINES_Y_MM": [round(v, 1) for v in ys],
           "RECTANGLES": rects, "FORMULA": " + ".join(f"{r['W_MM']:.0f} x {r['D_MM']:.0f}" for r in rects) + f" = {area:.4f} m2",
           "RASTER_CROSS_CHECK_M2": round(raster, 4), "RASTER_BASIS": "free cells + half-cell strip under the bounding line, the same basis the physical layer records", "DIFFERENCE_M2": round(area - raster, 4), "TOLERANCE_M2": round(tol, 4),
           "SKEW_SEGMENTS_IGNORED": skew, "LABELS_ASSEMBLED": list(labels)}
    if abs(area - raster) > tol:
        fml.update({"STATUS": "NOT_ESTABLISHED", "WHY": "the arrangement of the bounding lines does not reproduce the assembled free cells within tolerance"})
        return None, fml
    fml["STATUS"] = "COMPUTED"
    return area, fml


def mark_interior_obstructions(segments, formula):
    """A seal that does not fix the floor line and lies INSIDE the measured polygon is an obstruction drawn on the floor, not a
    boundary of it.  It is recorded, it is not deducted, and it is not allowed to make the region unresolved."""
    rects = (formula or {}).get("RECTANGLES") or []
    if not rects:
        return segments, 0
    def inside(x, y, tol=1.0):
        return any(r["X_MM"][0] - tol <= x <= r["X_MM"][1] + tol and r["Y_MM"][0] - tol <= y <= r["Y_MM"][1] + tol for r in rects)
    moved = 0
    for seg in segments:
        if seg["FIXES_WHERE_THE_FLOOR_STOPS"] or not seg.get("PTS"):
            continue
        if all(inside(x, y) for x, y in seg["PTS"]):
            seg["SEGMENT_ROLE"] = "INTERIOR_OBSTRUCTION"
            seg["WHY"] = seg["WHY"] + "; its whole length lies inside the measured polygon, so it is an obstruction drawn on the floor, not a boundary of it"
            seg["COUNTS_AS_PERIMETER"] = False
            moved += 1
    return segments, moved


def boundary_segments(result, vid, labels):
    """Every seal stretch that bounds the assembled region, with its measurement basis and length."""
    grid = result.grids7[vid]
    label, kind, idx = grid["label"], grid["kind"], grid["idx"]
    seals = result.seals[vid]
    bands_by_id = {b["BAND_ID"]: b for b in result.bands7[vid]}
    sites_by_id = {s["SITE_ID"]: s for s in result.sites7[vid]}
    H, W = label.shape
    member = set(labels)
    counts, edge_cells = Counter(), Counter()
    rs, cs = np.nonzero(kind)
    for rr, cc in zip(rs.tolist(), cs.tolist()):
        touch_in = touch_out = False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r2, c2 = rr + dr, cc + dc
            if 0 <= r2 < H and 0 <= c2 < W:
                if label[r2, c2] and int(label[r2, c2]) in member:
                    touch_in = True
                elif label[r2, c2] or kind[r2, c2] == 0:
                    touch_out = True
        if touch_in:
            counts[int(idx[rr, cc])] += 1
            if touch_out:
                edge_cells[int(idx[rr, cc])] += 1
    segs, by_basis = [], Counter()
    for i, n in counts.items():
        if i < 0:
            continue
        s = seals[i]
        basis, stops, why = seal_basis(s, bands_by_id, sites_by_id)
        # a seal every one of whose cells has member floor on both sides lies INSIDE the region: an obstruction drawn on the
        # floor, not a boundary of it.  This is the same test the region assembly used, applied to the finished region.
        interior = edge_cells.get(i, 0) == 0
        pts = s["PTS"]
        length = sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
        segs.append({"SEAL_INDEX": i, "SEAL_KIND": s["KIND"], "BAND_ID": s.get("BAND_ID"), "SITE_ID": s.get("SITE_ID"), "PTS": [[round(x, 1), round(y, 1)] for x, y in pts],
                     "SEGMENT_ROLE": "INTERIOR_OBSTRUCTION" if interior else "BOUNDARY", "COUNTS_AS_PERIMETER": not interior,
                     "EDGE_CELLS": edge_cells.get(i, 0),
                     "OBJECT_ID": s.get("OBJECT_ID"), "BOUNDARY_BASIS": basis, "FIXES_WHERE_THE_FLOOR_STOPS": stops,
                     "WHY": why + ("; every cell of it has this region's floor on both sides, so it is an obstruction inside the region, not a boundary" if interior else ""),
                     "SEAL_LENGTH_MM": round(length, 1), "PERIMETER_CELLS": n,
                     "MATERIAL_PRESENT": basis in ("ESTABLISHED_WALL_FACE", "COLUMN_FACE", "CAD_FACE_LINE_UNRESOLVED_ROLE", "JOINERY_OUTLINE_EDGE"),
                     "PHYSICAL_WALL": basis == "ESTABLISHED_WALL_FACE",
                     "GEOMETRY_AUTHORITY": basis in ("ESTABLISHED_WALL_FACE", "COLUMN_FACE"),
                     "REVERSIBLE": basis in ("THRESHOLD_CLOSURE", "OPEN_EDGE_CLOSURE")})
        by_basis[basis] += n
    return segs, _summarise(segs)


def _summarise(segs):
    by_basis = Counter()
    for seg in segs:
        if seg.get("COUNTS_AS_PERIMETER", True):
            by_basis[seg["BOUNDARY_BASIS"]] += seg["PERIMETER_CELLS"]
    total = sum(by_basis.values())
    unresolved = sum(v for k, v in by_basis.items() if k not in ESTABLISHING_BASES)
    obstructions = [s for s in segs if s.get("SEGMENT_ROLE") == "INTERIOR_OBSTRUCTION"]
    return {"BY_BASIS_PERIMETER_CELLS": dict(by_basis), "PERIMETER_CELLS": total,
            "UNRESOLVED_PERIMETER_CELLS": unresolved,
            "INTERIOR_OBSTRUCTIONS": [{"OBJECT_ID": s.get("OBJECT_ID"), "SEAL_KIND": s["SEAL_KIND"], "LENGTH_MM": s["SEAL_LENGTH_MM"], "WHY": s["WHY"]} for s in obstructions],
            "ALL_SEGMENTS_FIX_THE_FLOOR_LINE": unresolved == 0 and total > 0}


def summarise(segs):
    return _summarise(segs)
