"""WALL-FACE SURFACE ENGINE (R8.17) - the vertical surfaces of a room, from the classified one-sided boundary spans of
a certified TS01 site (WALL_CONTACT_PATH_POLICY_V4 classes) and the opening / passage records, at ONE stated trade
height with its authority. Never room perimeter x height.

PHYSICAL layer (this module; geometry decides no material):
  WALL_FACE        a REAL_WALL_FACE span (and the wall plane across a WINDOW_ABOVE_FLOOR span)
  COLUMN_FACE      a COLUMN_FACE span                  (its own class: never merged with wall faces)
  OBSTACLE_FACE    an AUTHORISED_OBSTACLE_FACE span    (its own class)
  OPENING          a door / sliding glazed door / floor-reaching glazing / window: its FULL area (width x height)
                   is an opening in the wall plane (US-06); the wall plane above a lower opening is a LINTEL_FACE
  HEAD_FACE        the wall plane above an open passage WITH a head (both sides of the strip when both lie in the site)
  JAMB / HEAD REVEAL  opening surfaces (opening_reveals): their own identity, never room wall face; the sill is not a
                   reveal (US-07); a FULL_HEIGHT passage has jambs only
  ZERO             a topology closure: zero material, zero surface
  UNPROVEN         any other span (blocks the site)
Only a PHYSICAL jamb record consumes a boundary span (V4); that span is an opening reveal, never wall face.

Heights: the trade height and every opening height carry an authority (source dimension / schedule / section >
source-bound owner or project fact > permitted fallback > BLOCKED). A window is deducted in full only when its
position inside the trade height is proven (sill + height); otherwise the site is blocked. No height -> no area.

Reconciliation per site: every boundary span lands in exactly one class (conservation), every opening span has a
height authority, and the net wall area = gross wall plane - opening areas (+ head faces) is computed both ways.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from . import wall_contact_path as WC

POLICY_ID = "WALL_FACE_SURFACE_POLICY_V1"
WALL_FACE, COLUMN_FACE, OBSTACLE_FACE = "WALL_FACE", "COLUMN_FACE", "OBSTACLE_FACE"
LINTEL_FACE, HEAD_FACE, ZERO, UNPROVEN = "LINTEL_FACE", "HEAD_FACE", "ZERO_TOPOLOGY_CLOSURE", "UNPROVEN"
JAMB_REVEAL, HEAD_REVEAL = "JAMB_REVEAL", "HEAD_REVEAL"
DOOR, SLIDING_DOOR, FLOOR_GLAZING, WINDOW = "DOOR", "SLIDING_GLAZED_DOOR", "FLOOR_REACHING_GLAZING", "WINDOW"
WITH_HEAD, FULL_HEIGHT = "OPEN_PASSAGE_WITH_HEAD", "OPEN_PASSAGE_FULL_HEIGHT"
COMPUTED, BLOCKED = "COMPUTED", "BLOCKED"
SPAN_OPENING = {WC.DOOR_PRESENT: DOOR, WC.SLIDING_GLAZED_DOOR_TO_FLOOR: SLIDING_DOOR,
                WC.FULL_HEIGHT_GLAZED: FLOOR_GLAZING, WC.WINDOW_ABOVE_FLOOR: WINDOW}
SURFACE_OF = {WC.REAL_WALL_FACE: WALL_FACE, WC.COLUMN_FACE: COLUMN_FACE, WC.AUTHORISED_OBSTACLE_FACE: OBSTACLE_FACE,
              WC.TOPOLOGY_CLOSURE: ZERO}


def opening_keys(sources) -> list:
    """Candidate opening keys of one boundary span: the door occurrence of a door closure, the glazed occurrence of
    a glazed closure, and every source / source entity (a window is keyed by its glazing entity)."""
    out = []
    for s in sources:
        if s.startswith("CLOSURE|GLAZED|"):
            out.append(s.split("|", 1)[1].rsplit("|", 1)[0])
        elif s.startswith("CLOSURE|"):
            out.append(s.split("|")[1])
        out += [s, WC._entity(s)]
    return out


def _geom(e):
    return [list(map(lambda c: round(c, 4), e[k])) for k in ("p0", "p1") if k in e]


def _r(v):
    return None if v is None else round(v, 6)


def site_faces(edges, *, u, height_m, height_authority, jambs=(), eps=0.0, obstacle_authority=None,
               floor_contact_by_entity=None, opening_heights=None, passages=()) -> dict:
    """The physical wall-plane surfaces of ONE site at ONE trade height (metres). `u` converts native units to m.
    opening_heights: key -> {"height_m", "authority"[, "sill_m", "sill_authority"]}; passages: the open passages
    whose strip lies INSIDE this site: [{"passage_id", "width_m", "head", "head_height_m", "head_authority"}]."""
    oh = opening_heights or {}
    H = height_m if (height_m is not None and height_authority) else None
    spans, openings, blockers = [], [], []
    by = defaultdict(float)
    consumed = 0.0
    boundary = math.fsum(e["length"] for e in edges) * u
    for e in edges:
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
        if c in SPAN_OPENING:
            kind = SPAN_OPENING[c]
            key = next((k for k in opening_keys(e["sources"]) if k in oh), None)
            rec = oh.get(key) or {}
            h = rec.get("height_m")
            sill = rec.get("sill_m", 0.0) if kind == WINDOW else 0.0
            if kind == FLOOR_GLAZING and h is None:
                h, rec = H, {"authority": "reaches the floor and the trade height (no head proven)"}
            op = {"opening": key, "kind": kind, "width_m": _r(rest), "height_m": h, "height_authority":
                  rec.get("authority"), "sill_m": sill if kind == WINDOW else 0.0,
                  "sill_authority": rec.get("sill_authority") if kind == WINDOW else "reaches the floor",
                  "sources": e["sources"][:3]}
            if h is None or not rec.get("authority"):
                blockers.append(f"OPENING_HEIGHT_NOT_ESTABLISHED: {kind} {key} ({_r(rest)} m)")
                op["state"] = BLOCKED
            elif kind == WINDOW and not rec.get("sill_authority"):
                blockers.append(f"WINDOW_POSITION_NOT_PROVEN: {key} ({_r(rest)} m, no sill authority)")
                op["state"] = BLOCKED
            elif H is not None:
                top = min(H, sill + h)
                op.update(state=COMPUTED, contained=sill + h <= H + 1e-9, gross_plane_m2=_r(rest * H),
                          deduction_m2=_r(rest * max(0.0, top - sill)),
                          lintel_m2=_r(rest * max(0.0, H - (sill + h))) if kind != WINDOW else None)
            openings.append(op)
            by["OPENING_SPAN"] += rest
            spans.append({"class": "OPENING", "kind": kind, "length_m": _r(rest), "sources": e["sources"][:3],
                          "geom": _geom(e)})
            continue
        s = SURFACE_OF.get(c, UNPROVEN)
        if s == UNPROVEN:
            blockers.append(f"SURFACE_UNPROVEN: {c} ({_r(rest)} m) {e['sources'][:2]}")
        by[s] += rest
        spans.append({"class": s, "length_m": _r(rest), "sources": e["sources"][:3], "geom": _geom(e),
                      "area_m2": None if (H is None or s == ZERO) else _r(rest * H) if s != ZERO else 0.0})
    heads = []
    for p in passages:
        if p.get("head") == WITH_HEAD:
            hh = p.get("head_height_m")
            if hh is None or not p.get("head_authority"):
                blockers.append(f"PASSAGE_HEAD_NOT_ESTABLISHED: {p['passage_id']}")
                continue
            for side in ("SIDE_1", "SIDE_2"):
                heads.append({"passage": p["passage_id"], "side": side, "class": HEAD_FACE, "width_m": p["width_m"],
                              "height_m": None if H is None else _r(max(0.0, H - hh)),
                              "area_m2": None if H is None else _r(p["width_m"] * max(0.0, H - hh)),
                              "authority": p["head_authority"]})
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
           "head_faces": heads, "conservation": cons, "blockers": blockers,
           "state": COMPUTED if not blockers and cons["reconciles"] else BLOCKED}
    if out["state"] == COMPUTED:
        wall = by[WALL_FACE] * H
        ded = math.fsum(o["deduction_m2"] for o in openings)
        gross = (by[WALL_FACE] + by["OPENING_SPAN"]) * H
        lint = math.fsum(o["lintel_m2"] or 0.0 for o in openings)
        head = math.fsum(h["area_m2"] for h in heads)
        win = math.fsum(o["deduction_m2"] for o in openings if o["kind"] == WINDOW)
        net_a = gross - ded + head
        net_b = wall - win + lint + head
        out["areas_m2"] = {"wall_plane_gross": _r(gross), "opening_deductions": _r(ded), "lintels": _r(lint),
                           "passage_head_faces": _r(head), "WALL_FACE_NET": _r(net_a),
                           "COLUMN_FACE": _r(by[COLUMN_FACE] * H), "OBSTACLE_FACE": _r(by[OBSTACLE_FACE] * H),
                           "check_two_ways": abs(net_a - net_b) <= 1e-6}
        if not out["areas_m2"]["check_two_ways"]:
            out["state"] = BLOCKED
            blockers.append("AREA_RECONCILIATION_FAILED")
    return out


def opening_reveals(opening, *, width_m, depth_m, depth_basis, height_m, head=True,
                    sides=("LEFT_JAMB", "RIGHT_JAMB")) -> list:
    """The reveal surfaces of ONE opening (its own identity; counted once, never per room): the PHYSICAL jambs at the
    opening height (`sides`: only those the source establishes) and the head (top reveal / soffit) - never the sill
    (US-07). None depth or height -> no area."""
    if depth_m is None or height_m is None:
        return [{"opening": opening, "surface": s, "state": BLOCKED, "depth_basis": depth_basis}
                for s in (list(sides) + (["TOP_REVEAL"] if head else []))]
    out = [{"opening": opening, "surface": s, "class": JAMB_REVEAL, "depth_m": _r(depth_m), "height_m": _r(height_m),
            "area_m2": _r(depth_m * height_m), "depth_basis": depth_basis, "state": COMPUTED}
           for s in sides]
    if head:
        out.append({"opening": opening, "surface": "TOP_REVEAL", "class": HEAD_REVEAL, "depth_m": _r(depth_m),
                    "width_m": _r(width_m), "area_m2": _r(depth_m * width_m), "depth_basis": depth_basis,
                    "state": COMPUTED})
    return out


def double_count_guard(site_results: dict, reveals: list) -> dict:
    """Every physical surface has ONE identity: a site span (site + sources + class), an opening span, a passage head
    face (passage + side) or an opening reveal (opening + surface)."""
    ids = []
    for sid, r in site_results.items():
        ids += [(sid, s["class"], tuple(s["sources"]), str(s.get("geom")), s["length_m"]) for s in r["spans"]]
        ids += [("HEAD", h["passage"], h["side"]) for h in r.get("head_faces", [])]
    ids += [("REVEAL", x["opening"], x["surface"]) for x in reveals]
    dup = sorted({str(i) for i in ids if ids.count(i) > 1})
    return {"surfaces": len(ids), "duplicates": dup, "state": "PASS" if not dup else "FAIL"}


def trade_assignment(space_class, trade_rules: dict) -> dict:
    """The trades ONE space class carries on its physical wall surfaces, from rule DATA only (never from geometry):
    trade_rules[space_class] = {trade: {"state": "APPLIES" | "NONE", "authority": ...}}. Unknown class -> nothing."""
    return {t: dict(v) for t, v in sorted((trade_rules.get(space_class) or {}).items())}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "path_classes_from": WC.POLICY_ID_V4,
           "physical_classes": [WALL_FACE, COLUMN_FACE, OBSTACLE_FACE, LINTEL_FACE, HEAD_FACE, JAMB_REVEAL,
                                HEAD_REVEAL, ZERO, UNPROVEN],
           "opening_kinds": [DOOR, SLIDING_DOOR, FLOOR_GLAZING, WINDOW], "passage_heads": [WITH_HEAD, FULL_HEIGHT],
           "deduction": "US-06: the FULL opening area (width x height, inside the trade height) for every door, window, "
                        "sliding door and glazed opening; the wall plane above a lower opening is a lintel face",
           "reveals": "opening surfaces (left / right jamb, top), counted once per opening, never the sill; source depth "
                      "first, the US-07 fallback only where no source depth exists",
           "height_hierarchy": ["source dimension / schedule / section", "source-bound owner / project fact",
                                "permitted fallback", "BLOCKED"],
           "window_position": "deducted in full only when sill + height inside the trade height is proven",
           "reconciliation": ["span conservation per site", "net area computed two ways", "one identity per surface"],
           "never": ["room perimeter x height", "a topology closure with material or area", "an opening width as an m2 "
                     "deduction", "a material decided by geometry", "a height without authority", "a jamb counted as "
                     "room wall face", "a published trade quantity without a frozen, blind-tested policy"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
