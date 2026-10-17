"""WALL-FACE SURFACE POLICY V2 (R8.18) - V1 (wall_faces) with ONE physically consistent wall-plane identity and two
area reconciliations that read DIFFERENT data.

WF-O1 (R8.17): V1's second area form used WALL_FACE x H, but a window span is booked as an opening span, so the wall
plane through every window was dropped AND the window rectangle deducted; windows had no below-sill / above-head
surface. V2:
  * every span on a wall line (wall face, window, door, sliding glazed door, floor-reaching glazing) is part of the
    wall PLANE; an opening removes exactly its rectangle clipped to [0, H];
  * the plane is partitioned into explicit surface records: WALL_FACE (a full-height wall span), BELOW_SILL
    (w x sill), ABOVE_OPENING (w x (H - top)), BESIDE_OPENING (span - opening width, full height) and HEAD_FACE
    (wall above an open passage with a head, each side present in the site);
  * METHOD A reads the conservation pass (aggregated plane span lengths) - gross plane - opening rectangles + head
    faces; METHOD B sums the generated surface records. They must agree within the predeclared tolerance, else the
    site is BLOCKED (AREA_RECONCILIATION_FAILED);
  * column and obstacle faces stay their own classes (never wall plane), topology closures are ZERO.
Heights carry authority; a window is deducted only with its position (sill authority) proven; no height -> no area.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from . import wall_contact_path as WC
from . import wall_faces as V1

POLICY_ID = "WALL_FACE_SURFACE_POLICY_V2"
WALL_FACE, COLUMN_FACE, OBSTACLE_FACE, ZERO, UNPROVEN = V1.WALL_FACE, V1.COLUMN_FACE, V1.OBSTACLE_FACE, V1.ZERO, \
    V1.UNPROVEN
BELOW_SILL, ABOVE_OPENING, BESIDE_OPENING, HEAD_FACE = "BELOW_SILL", "ABOVE_OPENING", "BESIDE_OPENING", V1.HEAD_FACE
PLANE_SURFACES = (WALL_FACE, BELOW_SILL, ABOVE_OPENING, BESIDE_OPENING, HEAD_FACE)
DOOR, SLIDING_DOOR, FLOOR_GLAZING, WINDOW = V1.DOOR, V1.SLIDING_DOOR, V1.FLOOR_GLAZING, V1.WINDOW
WITH_HEAD, FULL_HEIGHT = V1.WITH_HEAD, V1.FULL_HEIGHT
COMPUTED, BLOCKED = V1.COMPUTED, V1.BLOCKED
TOLERANCE_M2_PER_SURFACE = 1e-6
_r = V1._r


def reconcile(method_a_m2, surfaces, *, tolerance_per_surface=TOLERANCE_M2_PER_SURFACE) -> dict:
    """METHOD B = the sum of the wall-plane surface records; PASS when |A - B| <= tolerance x (1 + n)."""
    b = math.fsum(s["area_m2"] for s in surfaces if s["class"] in PLANE_SURFACES)
    tol = tolerance_per_surface * (1 + len(surfaces))
    return {"method_a_m2": _r(method_a_m2), "method_b_m2": _r(b), "difference_m2": _r(method_a_m2 - b),
            "tolerance_m2": tol, "state": "PASS" if abs(method_a_m2 - b) <= tol else "FAIL"}


def site_faces(edges, *, u, height_m, height_authority, jambs=(), eps=0.0, obstacle_authority=None,
               floor_contact_by_entity=None, opening_heights=None, passages=()) -> dict:
    """The physical wall surfaces of ONE site at ONE trade height (metres); arguments as V1."""
    oh = opening_heights or {}
    H = height_m if (height_m is not None and height_authority) else None
    spans, openings, blockers = [], [], []
    by = defaultdict(float)
    consumed = 0.0
    boundary = math.fsum(e["length"] for e in edges) * u
    for e in edges:                                            # ---- pass 1: classification + conservation
        ln = e["length"]
        jpart = 0.0
        if "p0" in e:
            for j in jambs:
                if WC.is_physical_jamb(j):
                    jpart += WC._overlap(e["p0"], e["p1"], j["segment"][0], j["segment"][1], eps)
        jpart = min(jpart, ln)
        consumed += jpart * u
        rest = (ln - jpart) * u
        if rest <= eps * u:
            continue
        c = WC.classify_v4(e, obstacle_authority=obstacle_authority, floor_contact_by_entity=floor_contact_by_entity)
        if c in V1.SPAN_OPENING:
            kind = V1.SPAN_OPENING[c]
            key = next((k for k in V1.opening_keys(e["sources"]) if k in oh), None)
            rec = dict(oh.get(key) or {})
            h = rec.get("height_m")
            if kind == FLOOR_GLAZING and h is None and H is not None:
                h, rec["authority"] = H, "reaches the floor and the trade height (no head proven)"
            sill = rec.get("sill_m") if kind == WINDOW else 0.0
            op = {"opening": key, "kind": kind, "span_m": _r(rest), "width_m": _r(rest), "height_m": h,
                  "height_authority": rec.get("authority"), "sill_m": sill,
                  "sill_authority": rec.get("sill_authority") if kind == WINDOW else "reaches the floor",
                  "sources": e["sources"][:3], "geom": V1._geom(e)}
            if h is None or not rec.get("authority"):
                blockers.append(f"OPENING_HEIGHT_NOT_ESTABLISHED: {kind} {key} ({_r(rest)} m)")
                op["state"] = BLOCKED
            elif kind == WINDOW and (sill is None or not rec.get("sill_authority")):
                blockers.append(f"WINDOW_POSITION_NOT_PROVEN: {key} ({_r(rest)} m, no sill authority)")
                op["state"] = BLOCKED
            else:
                op["state"] = COMPUTED
            openings.append(op)
            by["OPENING_SPAN"] += rest
            spans.append({"class": "OPENING", "kind": kind, "length_m": _r(rest), "sources": e["sources"][:3],
                          "geom": V1._geom(e)})
            continue
        s = V1.SURFACE_OF.get(c, UNPROVEN)
        if s == UNPROVEN:
            blockers.append(f"SURFACE_UNPROVEN: {c} ({_r(rest)} m) {e['sources'][:2]}")
        by[s] += rest
        spans.append({"class": s, "length_m": _r(rest), "sources": e["sources"][:3], "geom": V1._geom(e)})
    heads = []
    for p in passages:
        if p.get("head") == WITH_HEAD:
            if p.get("head_height_m") is None or not p.get("head_authority"):
                blockers.append(f"PASSAGE_HEAD_NOT_ESTABLISHED: {p['passage_id']}")
                continue
            heads.append(p)
        elif p.get("head") != FULL_HEIGHT:
            blockers.append(f"PASSAGE_HEAD_NOT_ESTABLISHED: {p['passage_id']}")
    if H is None:
        blockers.insert(0, "TRADE_HEIGHT_NOT_ESTABLISHED")
    span_sum = math.fsum(by.values())
    cons = {"boundary_m": _r(boundary), "consumed_by_physical_jambs_m": _r(consumed), "classified_m": _r(span_sum),
            "residual_m": _r(boundary - consumed - span_sum)}
    cons["reconciles"] = abs(boundary - consumed - span_sum) <= 1e-6 * (1 + len(edges))
    out = {"policy": POLICY_ID, "height_m": H, "height_authority": height_authority if H is not None else None,
           "lengths_m": {k: _r(v) for k, v in sorted(by.items())}, "spans": spans, "openings": openings,
           "conservation": cons, "blockers": blockers, "surfaces": [], "head_faces": []}
    if blockers or not cons["reconciles"]:
        out["state"] = BLOCKED
        return out
    surfaces = []                                              # ---- pass 2: explicit surface records (METHOD B)
    for s in spans:
        if s["class"] == WALL_FACE:
            surfaces.append({"class": WALL_FACE, "length_m": s["length_m"], "height_m": H,
                             "area_m2": s["length_m"] * H, "sources": s["sources"], "geom": s["geom"]})
        elif s["class"] in (COLUMN_FACE, OBSTACLE_FACE):
            surfaces.append({"class": s["class"], "length_m": s["length_m"], "height_m": H,
                             "area_m2": s["length_m"] * H, "sources": s["sources"], "geom": s["geom"]})
    rects = []
    for o in openings:
        w, h, sill = o["width_m"], o["height_m"], o["sill_m"] or 0.0
        lo, hi = min(sill, H), min(sill + h, H)
        rect = w * max(0.0, hi - lo)
        o.update(top_m=_r(sill + h), contained=sill + h <= H + 1e-9, rectangle_m2=_r(rect),
                 below_sill_m2=_r(w * lo), above_opening_m2=_r(w * max(0.0, H - hi)))
        rects.append(rect)
        for cls, a in ((BELOW_SILL, w * lo), (ABOVE_OPENING, w * max(0.0, H - hi)),
                       (BESIDE_OPENING, max(0.0, o["span_m"] - w) * H)):
            if a > 0:
                surfaces.append({"class": cls, "opening": o["opening"], "kind": o["kind"], "area_m2": a,
                                 "sources": o["sources"], "geom": o["geom"]})
    for p in heads:
        for side in ("SIDE_1", "SIDE_2"):
            a = p["width_m"] * max(0.0, H - p["head_height_m"])
            rec = {"class": HEAD_FACE, "passage": p["passage_id"], "side": side, "width_m": p["width_m"],
                   "height_m": _r(max(0.0, H - p["head_height_m"])), "area_m2": a, "authority": p["head_authority"]}
            surfaces.append(rec)
            out["head_faces"].append(rec)
    plane_len = by[WALL_FACE] + by["OPENING_SPAN"]                 # ---- METHOD A (aggregated lengths)
    method_a = plane_len * H - math.fsum(rects) + math.fsum(p["width_m"] * max(0.0, H - p["head_height_m"]) * 2
                                                            for p in heads)
    rec = reconcile(method_a, surfaces)
    for s in surfaces:
        s["area_m2"] = _r(s["area_m2"])
    out["surfaces"] = surfaces
    out["reconciliation"] = rec
    out["areas_m2"] = {"wall_plane_gross": _r(plane_len * H), "opening_rectangles": _r(math.fsum(rects)),
                       "passage_head_faces": _r(math.fsum(s["area_m2"] for s in surfaces if s["class"] == HEAD_FACE)),
                       "WALL_PLANE_NET": rec["method_a_m2"], "WALL_PLANE_NET_METHOD_B": rec["method_b_m2"],
                       "COLUMN_FACE": _r(by[COLUMN_FACE] * H), "OBSTACLE_FACE": _r(by[OBSTACLE_FACE] * H)}
    if rec["state"] != "PASS":
        blockers.append("AREA_RECONCILIATION_FAILED")
        out["state"] = BLOCKED
    else:
        out["state"] = COMPUTED
    return out


def double_count_guard(site_results: dict, reveals: list) -> dict:
    """One identity per physical surface: (site, class, sources, geometry, opening / passage side) or (opening,
    owning side, reveal surface)."""
    ids = []
    for sid, r in site_results.items():
        ids += [(sid, s["class"], tuple(s.get("sources", ())), str(s.get("geom")), s.get("opening"), s.get("side"))
                for s in r.get("surfaces", [])]
    ids += [("REVEAL", x["opening"], x.get("owner_site"), x["surface"]) for x in reveals]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    return {"surfaces": len(ids), "duplicates": dup, "state": "PASS" if not dup else "FAIL"}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "extends": V1.POLICY_ID, "path_classes_from": WC.POLICY_ID_V4,
           "plane_surfaces": list(PLANE_SURFACES), "separate_classes": [COLUMN_FACE, OBSTACLE_FACE, ZERO],
           "opening_kinds": [DOOR, SLIDING_DOOR, FLOOR_GLAZING, WINDOW],
           "method_a": "aggregated plane span lengths (conservation pass) x H - opening rectangles + head faces",
           "method_b": "sum of generated surface records WALL_FACE + BELOW_SILL + ABOVE_OPENING + BESIDE_OPENING + "
                       "HEAD_FACE",
           "tolerance_m2": f"{TOLERANCE_M2_PER_SURFACE} x (1 + surfaces)",
           "fixes": ["WF-O1: the window plane is never dropped; one rectangle per opening, clipped to [0, H]"],
           "never": V1.policy_record()["never"] + ["a window removing its span AND its rectangle",
                                                   "two area checks reading the same aggregate"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
