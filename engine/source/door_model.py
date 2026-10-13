"""DOOR MODEL (M9 Phase 2A P2-03 / P2-04, ARCH_TAKEOFF_V2.1 only) - every drawn door swing belongs to exactly one
physical door element; each element carries its state, its typed evidence, three separate widths, its height and
area (or why not), the spaces it joins and its BOQ class. Opt-in: V1 and V2 never call this module.

Owner door rules of 2026-10-13 (DOOR_RULE_ID; recorded in the run, not a rule-store file, so the rule-set digest of
V1 / V2 runs is unchanged):
    DOOR.INTERNAL.PVC          every confirmed ordinary internal door (both sides are inside the building)
    DOOR.EXTERNAL.ALUMINIUM    every confirmed ordinary external door: exterior adjacency is evidence-based (an
                               exterior space on one side, or the facade: nothing drawn beyond that side); never the
                               swing direction or a layer name
    DOOR.MAIN_ENTRANCE         one main entrance door, measured on its own; candidates are detected and reconciled:
                               zero or several left -> a REVIEW finding, never an assumed one. Never also counted as
                               PVC or aluminium; material NOT_ESTABLISHED unless a source gives it
    LIFT_SYSTEM / LIFT_DOOR    a door (or an opening) to a lift space: outside the ordinary door BOQ (EXCLUDED)
    one physical double-leaf door is ONE element (leaf count recorded), never two door items.

States (round 2, Q2; owner decision D4):
    CONFIRMED    a band opening (jamb to jamb) serves the swing(s) - evidence kind BAND_OPENING, or DIMENSION /
                 SCHEDULE / DECISION evidence; the only state that reaches released BOQ totals
    PROVISIONAL  the swing closes a wall-to-wall gap with no band opening (closure only): width = the closure,
                 range [swing radius, closure]; shown in the separate provisional section, never in released totals.
                 The nib cases (wall pieces under 100 mm) stay here: no nib rule (P2-13 needs its own review)
    UNRESOLVED   the swing closes no gap: no width; an engineering finding
Widths (owner requirement 2), each with its own source; no field is filled from another's source:
    structural_opening_width_m   jamb to jamb (band opening) or wall to wall (the leaf closure)
    frame_width_m                the door block's frame span across the opening (NOT_DRAWN when the block draws none)
    nominal_leaf_width_m         per leaf: the swing radius (evidence only: never a BOQ width)
Height: only from a source (facts opening_heights, keyed by class or DOOR, with its authority); else BLOCKED with the
missing source named. An explicitly authorised project fallback (facts opening_heights DOOR_ASSUMED) is labelled
ASSUMED and kept out of confirmed areas. Area = width x height only when both are established.

    elements(S, rooms, ents, unit_m, floor, ...)   -> {elements, swings, conservation, findings}
    classify / main_entrance(...)                  the class of each element and the main-entrance reconciliation
    boq_lines(ctx, model)                          released lines only (CONFIRMED, class established)
    schedule_rows(model)                           the door schedule (every element, every field)
Project-agnostic; stdlib + engine.source.boq_line / member_detection / arch_rooms.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from engine.source import arch_rooms as AR
from engine.source import boq_line as BL
from engine.source import member_detection as MD

POLICY_ID = "DOOR_MODEL_V1"
DOOR_RULE_ID = "OWNER_DOOR_CLASSES_2026_10_13"
CONFIRMED, PROVISIONAL, UNRESOLVED = "CONFIRMED", "PROVISIONAL", "UNRESOLVED"
CONFIRMING_KINDS = ("BAND_OPENING", "DIMENSION", "SCHEDULE", "DECISION")
PVC, ALU, MAIN, LIFT = "DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM", "DOOR.MAIN_ENTRANCE", "LIFT_SYSTEM/LIFT_DOOR"
CLASS_UNRESOLVED = "CLASS_UNRESOLVED"
RELEASED_CLASSES = (PVC, ALU, MAIN)
FRAME_DISAGREE_MM = 2.0
PAIR_TOL = 0.02                          # an exploded double leaf: r1 + r2 = hinge span within 2 %
PROBE_M = (0.25, 0.5, 1.0)               # side probes beyond the wall faces
ENTRANCE_RE = re.compile(r"(?i)(MAIN\s*(DOOR|ENTRANCE)|ENTRANCE|ENTRY|FOYER|LOBBY|مدخل)")
LIFT_RE = re.compile(r"(?i)((^|[^A-Z])LIFT|ELEVATOR|مصعد)")
ENTRANCE_TEXT_REACH_M = 3.0
ENTRANCE_SPACES = ("CORRIDOR", "RECEPTION", "MAJLIS", "LIVING")    # a plausible entrance (weak evidence only)
SIDE_CLASSES_THIN = ("DOORWAY", "WALL", "SLIVER")


def _mm(v_du, unit_m):
    return v_du * unit_m * 1000.0


def stable_id(floor, centre_du, width_du, unit_m, origin=(0.0, 0.0)):
    """unit- and translation-stable: floor, centre relative to the plan origin and width, in whole mm (a quarter-mm
    shift keeps drafted half-mm values off the rounding boundary)."""
    cx, cy = (_mm(centre_du[0] - origin[0], unit_m), _mm(centre_du[1] - origin[1], unit_m))
    w = _mm(width_du, unit_m) if width_du is not None else -1.0
    key = f"{floor}|{round(cx + 0.25)}|{round(cy + 0.25)}|{round(w + 0.25)}"
    return f"DOOR-{floor}-{hashlib.sha256(key.encode('utf-8')).hexdigest()[:8]}"


def _ev(eid, kind, **kw):
    return dict({"id": eid, "kind": kind}, **kw)


def _closure_geom(S, occ):
    for r in S.get("repairs") or ():
        if r.get("kind") == "DOOR_CLOSURE" and r.get("id") == f"CLOSURE|{occ}|A":
            return tuple(r["a"]), tuple(r["b"])
    return None


def _frame_span(occ, swings, ents, u, n, o_lo, o_hi, unit_m):
    """the door block's own lines (same insert occurrence) lying in the wall strip, projected on the wall axis, every
    leaf line of the insert excluded: their span is the frame width. None when the block draws no such line."""
    insert = occ.split("|")[0]
    leaves = [sw for k, sw in swings.items() if k.split("|")[0] == insert]
    tol = 0.02 / unit_m
    xs = []
    for s in ents.get("segments") or ():
        if (s.get("path") or [None])[0] != insert:
            continue
        L = math.dist(s["a"], s["b"])
        if any(min(math.dist(s["a"], sw["hinge"]), math.dist(s["b"], sw["hinge"])) <= tol * 5 and
               abs(L - sw["radius"]) <= 0.15 * sw["radius"] for sw in leaves):
            continue                                     # a leaf
        if all(o_lo - tol <= p[0] * n[0] + p[1] * n[1] <= o_hi + tol for p in (s["a"], s["b"])):
            xs += [p[0] * u[0] + p[1] * u[1] for p in (s["a"], s["b"])]
    return (max(xs) - min(xs)) if len(xs) >= 2 and max(xs) - min(xs) > tol else None


def _face_at(p, faces):
    for f in faces:
        if MD.point_in_poly(p[0], p[1], f["polygon"]) and not any(MD.point_in_poly(p[0], p[1], h)
                                                                   for h in f.get("hole_polygons") or ()):
            return f
    return None


def _ray_free(p, d, segments, reach):
    """True when a ray from p along d meets no wall-role segment within reach (the facade side)."""
    q = (p[0] + d[0] * reach, p[1] + d[1] * reach)
    for s in segments:
        a, b = s["a"], s["b"]
        d1 = (q[0] - p[0]) * (a[1] - p[1]) - (q[1] - p[1]) * (a[0] - p[0])
        d2 = (q[0] - p[0]) * (b[1] - p[1]) - (q[1] - p[1]) * (b[0] - p[0])
        d3 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        d4 = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        if d1 * d2 <= 0 and d3 * d4 <= 0:
            return False
    return True


def _kind_of(face):
    kinds = {AR.LEX[c][2] for c in face.get("codes") or () if c in AR.LEX}
    return kinds


def _side(c, n, sign, half_t, S, wall_segs, unit_m, reach):
    """what lies on one side of a door: {kind: SPACE | EXTERIOR_SPACE | LIFT | FACADE | UNKNOWN, face_id, codes}."""
    faces = S.get("faces") or []
    for d in PROBE_M:
        k = half_t + d / unit_m
        p = (c[0] + sign * n[0] * k, c[1] + sign * n[1] * k)
        f = _face_at(p, faces)
        if f is None:
            if _ray_free(p, (sign * n[0], sign * n[1]), wall_segs, reach):
                return {"kind": "FACADE", "face_id": None, "codes": [], "evidence": "nothing drawn beyond this side"}
            continue
        if f["class"] in SIDE_CLASSES_THIN:
            continue
        codes = f.get("codes") or []
        if "LIFT" in codes:
            return {"kind": "LIFT", "face_id": f["face_id"], "codes": codes, "evidence": "a LIFT space"}
        if AR.EXTERIOR in _kind_of(f) and len(_kind_of(f)) == 1:
            return {"kind": "EXTERIOR_SPACE", "face_id": f["face_id"], "codes": codes,
                    "evidence": "an exterior space (" + "+".join(codes) + ")"}
        return {"kind": "SPACE", "face_id": f["face_id"], "codes": codes, "evidence": "a space inside the plan"}
    return {"kind": "UNKNOWN", "face_id": None, "codes": [], "evidence": "no space and no facade found on this side"}


def _height(cls, facts):
    oh = (facts or {}).get("opening_heights") or {}
    for key in ([cls] if cls else []) + ["DOOR"]:
        if oh.get(key):
            return {"value_m": oh[key]["value_m"], "state": "SOURCE", "source": f"facts opening_heights.{key}",
                    "authority": oh[key]["authority"]}
    if oh.get("DOOR_ASSUMED"):
        return {"value_m": oh["DOOR_ASSUMED"]["value_m"], "state": "ASSUMED",
                "source": "facts opening_heights.DOOR_ASSUMED (explicitly authorised project fallback)",
                "authority": oh["DOOR_ASSUMED"]["authority"]}
    return {"value_m": None, "state": "BLOCKED",
            "source": "MISSING SOURCE: no door schedule, elevation, section or facts opening_heights gives the height"}


def elements(S, rooms, ents, unit_m, floor, *, wall_layers=(), origin=(0.0, 0.0), facts=None,
             promote_by_dimension=False, dimensions=(), decisions=None):
    """the door elements of one floor from the V2.1 spaces result S (arch_rooms.spaces) and its rooms."""
    swings = S.get("doors") or {}
    status = S.get("door_status") or {}
    ops = {o["opening_id"]: o for o in S.get("openings") or ()}
    room_of_face = {r["face_id"]: r for r in rooms}
    wall_l = set(wall_layers)
    wall_segs = [s for s in ents.get("segments") or () if s["layer"] in wall_l]
    xs = [p[i] for s in ents.get("segments") or () for p in (s["a"], s["b"]) for i in (0, 1)]
    reach = (max(xs) - min(xs)) * 2 if xs else 1e9
    out, findings, used = [], [], Counter()

    def add(el):
        for occ in el["swings"]:
            used[occ] += 1
        out.append(el)

    # 1. band openings served by swings: CONFIRMED (one element per opening; two leaves = one double door)
    for o in S.get("openings") or ():
        leaves = o.get("door_leaves") or ([o["door_symbol"]] if o.get("door_symbol") else [])
        if o.get("kind") != "DOOR" or not leaves:
            continue
        u, n = o["u"], o["n"]
        c = o["centre"]
        frame = None
        for occ in leaves:
            f = _frame_span(occ, swings, ents, u, n, o["o0"], o["o1"], unit_m) if occ in swings else None
            frame = f if f is not None and (frame is None or f > frame) else frame
        el = {"floor": floor, "opening_id": o["opening_id"], "swings": list(leaves), "leaf_count": len(leaves),
              "state": CONFIRMED, "centre": list(c), "u": list(u), "n": list(n), "wall_t_m": o["wall_t_m"],
              "structural_opening_width_m": o["width_m"], "structural_opening_source": "BAND_OPENING (jamb to jamb)",
              "frame_width_m": frame * unit_m if frame is not None else None,
              "frame_source": "door block frame span" if frame is not None else "NOT_DRAWN",
              "nominal_leaf_width_m": [swings[x]["radius"] * unit_m for x in leaves if x in swings],
              "evidence": [_ev(f"EV-{o['opening_id']}-BAND", "BAND_OPENING", opening_id=o["opening_id"],
                               jambs=[o["start_jamb"], o["end_jamb"]], width_m=o["width_m"])]
              + [_ev(f"EV-{x.split('|')[-1]}-SWING", "SWING", occ=x, radius_m=swings[x]["radius"] * unit_m)
                 for x in leaves if x in swings]}
        el["history"] = [{"from": None, "to": CONFIRMED, "evidence": el["evidence"][0]["id"]}]
        add(el)
    # 2. swings closed by their leaf with no band opening: PROVISIONAL (an exploded pair is one element)
    closed = [occ for occ in sorted(swings) if used[occ] == 0 and (status.get(occ) or {}).get("state") == "CLOSED"]
    paired = set()
    for i, a in enumerate(closed):
        for b in closed[i + 1:]:
            if a in paired or b in paired:
                continue
            sa, sb = swings[a], swings[b]
            span = math.dist(sa["hinge"], sb["hinge"])
            rr = sa["radius"] + sb["radius"]
            if abs(span - rr) <= PAIR_TOL * rr:
                paired |= {a, b}
                g = _closure_geom(S, a) or (tuple(sa["hinge"]), tuple(sb["hinge"]))
                add(_provisional(floor, [a, b], swings, status, g, span, ents, unit_m,
                                 extra=[_ev(f"EV-{a.split('|')[-1]}-PAIR", "EXPLODED_PAIR", hinge_span_m=span * unit_m,
                                            leaves_m=[sa["radius"] * unit_m, sb["radius"] * unit_m])]))
            elif span <= 1.3 * rr:
                findings.append({"level": "REVIEW", "code": "DOUBLE_LEAF_UNCERTAIN", "floor": floor,
                                 "swings": [a, b], "message": f"two leaf-closed swings {span * unit_m:.3f} m apart "
                                 f"(leaves {rr * unit_m:.3f} m): not a pair within 2 %; kept as two elements"})
    for occ in closed:
        if occ in paired:
            continue
        st = status[occ]
        g = _closure_geom(S, occ)
        add(_provisional(floor, [occ], swings, status, g, st.get("width"), ents, unit_m))
    # 3. swings closing no gap: UNRESOLVED
    for occ in sorted(swings):
        if used[occ]:
            continue
        sw = swings[occ]
        el = {"floor": floor, "opening_id": None, "swings": [occ], "leaf_count": 1, "state": UNRESOLVED,
              "centre": list(sw["hinge"]), "u": None, "n": None, "wall_t_m": None,
              "structural_opening_width_m": None, "structural_opening_source": "BLOCKED: the swing closes no gap",
              "frame_width_m": None, "frame_source": "NOT_ESTABLISHED",
              "nominal_leaf_width_m": [sw["radius"] * unit_m],
              "evidence": [_ev(f"EV-{occ.split('|')[-1]}-SWING", "SWING", occ=occ, radius_m=sw["radius"] * unit_m,
                               closure_state=(status.get(occ) or {}).get("state"),
                               why=(status.get(occ) or {}).get("why"))]}
        el["history"] = [{"from": None, "to": UNRESOLVED, "evidence": el["evidence"][0]["id"]}]
        add(el)
        findings.append({"level": "ENGINEERING", "code": "DOOR_SWING_UNRESOLVED", "floor": floor, "swing": occ,
                         "message": "a door swing closes no wall gap: no door width; the door is not in any total"})
    # ids, sides, frame check, dimension evidence, decisions
    for el in out:
        w = el["structural_opening_width_m"]
        el["element_id"] = stable_id(floor, el["centre"], w / unit_m if w is not None else None, unit_m, origin)
    seen = Counter(el["element_id"] for el in out)
    for el in out:
        if seen[el["element_id"]] > 1:
            el["element_id"] += "-" + el["swings"][0].split("|")[-1]
    for el in out:
        _sides(el, S, wall_segs, unit_m, reach, room_of_face)
        fw, w = el["frame_width_m"], el["structural_opening_width_m"]
        if fw is not None and w is not None and abs(fw - w) * 1000.0 > FRAME_DISAGREE_MM:
            findings.append({"level": "REVIEW", "code": "DOOR_CLOSURE_FRAME_DISAGREE", "floor": floor,
                             "element_id": el["element_id"], "opening_m": round(w, 4), "frame_m": round(fw, 4),
                             "message": f"structural opening {w * 1000:.0f} mm vs frame span {fw * 1000:.0f} mm"})
        for dm in dimensions or ():
            if dm.get("element_id") == el["element_id"]:
                el["evidence"].append(_ev(f"EV-{el['element_id']}-DIM", "DIMENSION", **{k: v for k, v in dm.items()
                                                                                       if k != "element_id"}))
                if promote_by_dimension and el["state"] == PROVISIONAL and dm.get("agrees"):
                    _transition(el, CONFIRMED, el["evidence"][-1]["id"])
        dec = (decisions or {}).get(el["element_id"])
        if dec:
            el["evidence"].append(_ev(f"EV-{el['element_id']}-DEC", "DECISION", **dec))
            if dec.get("state") in (CONFIRMED, PROVISIONAL, UNRESOLVED) and dec["state"] != el["state"]:
                _transition(el, dec["state"], el["evidence"][-1]["id"])
    return {"elements": out, "findings": findings,
            "conservation": conservation(swings, out, floor)}


def _provisional(floor, occs, swings, status, g, width_du, ents, unit_m, extra=()):
    sw0 = swings[occs[0]]
    if g is not None:
        a, b = g
        L = math.dist(a, b) or 1.0
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-u[1], u[0])
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    else:
        u = n = None
        c = tuple(sw0["hinge"])
    radii = [swings[x]["radius"] * unit_m for x in occs]
    w = width_du * unit_m if width_du is not None else None
    st = status.get(occs[0]) or {}
    el = {"floor": floor, "opening_id": None, "swings": list(occs), "leaf_count": len(occs), "state": PROVISIONAL,
          "centre": list(c), "u": list(u) if u else None, "n": list(n) if n else None, "wall_t_m": None,
          "structural_opening_width_m": w,
          "structural_opening_source": "CLOSURE (wall to wall along the closed leaf)" if w is not None else "BLOCKED",
          "width_range_m": [round(sum(radii), 6), round(w, 6)] if w is not None else None,
          "frame_width_m": None, "frame_source": "NOT_DRAWN",
          "nominal_leaf_width_m": radii,
          "evidence": [_ev(f"EV-{occs[0].split('|')[-1]}-CLOSURE", "CLOSURE", closure_a=st.get("closure_a"),
                           closure_b=st.get("closure_b"), hits=st.get("hits"), width_m=w)] + list(extra) +
                      [_ev(f"EV-{x.split('|')[-1]}-SWING", "SWING", occ=x, radius_m=swings[x]["radius"] * unit_m)
                       for x in occs],
          "uncertainty": "no band opening: the jambs are not proven (wall pieces too short for a wall band, or no "
                         "jamb drawn); width between the swing radius and the wall-to-wall closure"}
    if u:
        ins = occs[0]
        f = _frame_span(ins, swings, ents, u, n, *sorted((c[0] * n[0] + c[1] * n[1] - 0.15 / unit_m,
                                                        c[0] * n[0] + c[1] * n[1] + 0.15 / unit_m)), unit_m)
        if f is not None:
            el["frame_width_m"], el["frame_source"] = f * unit_m, "door block frame span"
    el["history"] = [{"from": None, "to": PROVISIONAL, "evidence": el["evidence"][0]["id"]}]
    return el


def _transition(el, to, evidence_id):
    ev = next((e for e in el["evidence"] if e["id"] == evidence_id), None)
    if to == CONFIRMED and (ev is None or ev["kind"] not in CONFIRMING_KINDS):
        raise ValueError(f"{el['element_id']}: CONFIRMED needs evidence of kind {CONFIRMING_KINDS}")
    el["history"].append({"from": el["state"], "to": to, "evidence": evidence_id})
    el["state"] = to


def attach_dimensions(els, door_evidence, *, promote=False):
    """DIMENSION evidence on door elements (read-only unless promote: a provisional door whose closure a usable
    dimension confirms within 5 mm becomes CONFIRMED - off in the V2.1 run, an owner decision is pending)."""
    by = {}
    for d in door_evidence:
        by.setdefault(d["element_id"], []).append(d)
    for el in els:
        for d in by.get(el["element_id"], ()):
            el["evidence"].append(_ev(f"EV-{el['element_id']}-DIM-{d['handle']}", "DIMENSION",
                                      **{k: v for k, v in d.items() if k != "element_id"}))
            if promote and el["state"] == PROVISIONAL and d.get("agrees"):
                _transition(el, CONFIRMED, el["evidence"][-1]["id"])
    return els


def confirming_evidence(el):
    return [e for e in el["evidence"] if e["kind"] in CONFIRMING_KINDS]


def _sides(el, S, wall_segs, unit_m, reach, room_of_face):
    if el["n"] is None:
        el["sides"] = [{"kind": "UNKNOWN", "face_id": None, "codes": [], "evidence": "no door axis"}] * 2
    else:
        half = (el["wall_t_m"] or 0.2) / 2.0 / unit_m
        el["sides"] = [_side(el["centre"], el["n"], sg, half, S, wall_segs, unit_m, reach) for sg in (1, -1)]
    for sd in el["sides"]:
        r = room_of_face.get(sd["face_id"])
        sd["room_id"] = r["room_id"] if r else None
        sd["room_name"] = r["name_en"] if r else None
    el["from_room"], el["to_room"] = (el["sides"][0].get("room_id"), el["sides"][1].get("room_id"))


def conservation(swings, els, floor):
    """drawn swings = the leaves of CONFIRMED + PROVISIONAL + UNRESOLVED elements; no swing in two elements."""
    c = Counter(occ for el in els for occ in el["swings"])
    twice = sorted(k for k, v in c.items() if v > 1)
    missing = sorted(set(swings) - set(c))
    extra = sorted(set(c) - set(swings))
    by = Counter(el["state"] for el in els)
    leaves = Counter()
    for el in els:
        leaves[el["state"]] += el["leaf_count"]
    return {"floor": floor, "swings": len(swings), "elements": dict(by), "leaves": dict(leaves),
            "ok": not twice and not missing and not extra and sum(leaves.values()) == len(swings),
            "in_two_elements": twice, "without_element": missing, "unknown_swings": extra}


def classify(el, ents=None, unit_m=1.0):
    """the BOQ class from the sides (typed evidence), the lift words of the door block, never a layer name alone."""
    kinds = [s["kind"] for s in el["sides"]]
    insert = (el["swings"][0].split("|")[0] if el["swings"] else "")
    if "LIFT" in kinds or (insert and LIFT_RE.search(insert)):
        el["class"], el["class_evidence"] = LIFT, "a lift space on one side" if "LIFT" in kinds else \
            "the door block is a lift door"
        return el
    outside = [k for k in kinds if k in ("FACADE", "EXTERIOR_SPACE")]
    inside = [k for k in kinds if k == "SPACE"]
    if len(inside) == 2:
        el["class"], el["class_evidence"] = PVC, "spaces inside the plan on both sides"
    elif len(inside) == 1 and len(outside) == 1:
        el["class"] = ALU
        el["class_evidence"] = "exterior adjacency: " + next(s["evidence"] for s in el["sides"]
                                                             if s["kind"] in ("FACADE", "EXTERIOR_SPACE"))
    else:
        el["class"], el["class_evidence"] = CLASS_UNRESOLVED, "sides " + " / ".join(kinds)
    return el


def main_entrance(els, faces_texts, texts, unit_m, *, entrance_floor):
    """the main-entrance reconciliation over every external door of the entrance floor: STRONG candidates carry an
    entrance word in the space they open into or a word within 3 m; exactly one STRONG -> it is the main entrance;
    otherwise a REVIEW finding names the candidates and none is assumed. -> (main element or None, findings,
    candidates)."""
    reach = ENTRANCE_TEXT_REACH_M / unit_m
    cands = []
    for el in els:
        if el.get("class") != ALU or el["floor"] != entrance_floor:
            continue
        ev = []
        for sd in el["sides"]:
            for t in faces_texts.get(sd.get("face_id"), ()):
                if ENTRANCE_RE.search(t["value"] or ""):
                    ev.append({"kind": "ENTRANCE_WORD_IN_SPACE", "text_id": t["id"], "text": t["value"]})
        for t in texts:
            if ENTRANCE_RE.search(t.get("value") or "") and math.dist((t["x"], t["y"]), el["centre"]) <= reach:
                ev.append({"kind": "ENTRANCE_WORD_NEAR", "text_id": t["id"], "text": t["value"]})
        weak = el["leaf_count"] > 1 or any(c in ENTRANCE_SPACES for sd in el["sides"] for c in sd.get("codes") or ())
        if not ev and not weak:
            continue
        cands.append({"element_id": el["element_id"], "strong": bool(ev), "evidence": ev,
                      "weak_evidence": "double leaf or opens into a hall / reception / majlis / living space"
                      if weak else None, "leaf_count": el["leaf_count"], "width_m": el["structural_opening_width_m"]})
    strong = [c for c in cands if c["strong"]]
    findings = []
    main = None
    if len(strong) == 1:
        main = next(el for el in els if el["element_id"] == strong[0]["element_id"])
    else:
        findings.append({"level": "REVIEW", "code": "MAIN_ENTRANCE_UNRESOLVED" if not strong else
                         "MAIN_ENTRANCE_AMBIGUOUS", "floor": entrance_floor,
                         "candidates": [c["element_id"] for c in (strong or cands)],
                         "message": (f"{len(strong)} external doors carry entrance evidence" if strong else
                                     f"no external door of {entrance_floor} carries entrance evidence "
                                     f"({len(cands)} plausible candidate(s) withheld from released totals)") +
                                    ": the main entrance is not assumed; a reviewer names it"})
    return main, findings, cands


def finalise(els, *, main, unresolved_main_candidates, facts):
    """BOQ class, height, area and the released flag of each element."""
    cand = set(unresolved_main_candidates)
    for el in els:
        if main is not None and el["element_id"] == main["element_id"]:
            el["boq_class"] = MAIN
            el["material"] = ((facts or {}).get("door_materials") or {}).get(MAIN) or "NOT_ESTABLISHED"
        elif el["element_id"] in cand:
            el["boq_class"] = "MAIN_ENTRANCE_CANDIDATE"
            el["material"] = "NOT_ESTABLISHED"
        else:
            el["boq_class"] = el.get("class")
            el["material"] = {PVC: "PVC (owner door rule)", ALU: "ALUMINIUM (owner door rule)"}.get(el["boq_class"],
                                                                                                "NOT_APPLICABLE")
        h = _height(el["boq_class"] if el["boq_class"] in RELEASED_CLASSES else None, facts)
        el["height"] = h
        w = el["structural_opening_width_m"]
        el["height_m"] = h["value_m"]
        if w is not None and h["value_m"] is not None:
            el["area_m2"] = round(w * h["value_m"], 6)
            el["area_state"] = "ASSUMED" if h["state"] == "ASSUMED" else "MEASURED_WIDTH_x_SOURCE_HEIGHT"
        else:
            el["area_m2"] = None
            el["area_state"] = "BLOCKED: " + ("width not established" if w is None else h["source"])
        el["released"] = el["state"] == CONFIRMED and el["boq_class"] in RELEASED_CLASSES
        el["section"] = ("RELEASED" if el["released"] else "LIFT_EXCLUDED" if el["boq_class"] == LIFT else
                         "PROVISIONAL_NOT_RELEASED")
    return els


def floor_model(S, rooms, ents, unit_m, floor, *, wall_layers=(), origin=(0.0, 0.0), facts=None, **kw):
    m = elements(S, rooms, ents, unit_m, floor, wall_layers=wall_layers, origin=origin, facts=facts, **kw)
    for el in m["elements"]:
        classify(el, ents, unit_m)
    m["lift_openings"] = lift_openings(S, rooms, ents, unit_m, floor, wall_layers=wall_layers)
    return m


def lift_openings(S, rooms, ents, unit_m, floor, *, wall_layers=()):
    """band openings without a door symbol that open into a lift space: lift entrances (LIFT_SYSTEM / LIFT_DOOR),
    outside the ordinary opening lines too."""
    wall_segs = [s for s in ents.get("segments") or () if s["layer"] in set(wall_layers)]
    xs = [p[i] for s in ents.get("segments") or () for p in (s["a"], s["b"]) for i in (0, 1)]
    reach = (max(xs) - min(xs)) * 2 if xs else 1e9
    out = []
    for o in S.get("openings") or ():
        if o.get("kind") == "DOOR":
            continue
        half = o["wall_t_m"] / 2.0 / unit_m
        sides = [_side(o["centre"], o["n"], sg, half, S, wall_segs, unit_m, reach) for sg in (1, -1)]
        if any(sd["kind"] == "LIFT" for sd in sides):
            out.append({"floor": floor, "opening_id": o["opening_id"], "kind": o["kind"], "width_m": o["width_m"],
                        "class": LIFT, "section": "LIFT_EXCLUDED",
                        "evidence": "a lift space on one side", "sides": [sd["kind"] for sd in sides]})
    return out


def building_model(floors, texts_of, faces_texts_of, unit_m, *, entrance_floor, facts=None):
    """floors: [(floor, floor_model)] -> the door model of the drawing (the main entrance is reconciled once)."""
    els = [el for _f, m in floors for el in m["elements"]]
    findings = [f for _f, m in floors for f in m["findings"]]
    main, mf, cands = main_entrance(els, faces_texts_of.get(entrance_floor, {}), texts_of.get(entrance_floor, ()),
                                    unit_m, entrance_floor=entrance_floor)
    unresolved = [c["element_id"] for c in cands if (c["strong"] or not any(x["strong"] for x in cands))] \
        if main is None else []
    finalise(els, main=main, unresolved_main_candidates=unresolved, facts=facts)
    findings += mf
    for el in els:
        if el["state"] == CONFIRMED and el["boq_class"] in RELEASED_CLASSES and el["height"]["state"] == "BLOCKED":
            findings.append({"level": "MISSING_SOURCE", "code": "DOOR_HEIGHT_MISSING", "floor": el["floor"],
                             "element_id": el["element_id"], "message": el["height"]["source"]})
    cons = [m["conservation"] for _f, m in floors]
    return {"policy": POLICY_ID, "rule_id": DOOR_RULE_ID, "elements": els, "findings": findings,
            "lift_openings": [x for _f, m in floors for x in m.get("lift_openings") or ()],
            "conservation": cons, "conservation_ok": all(c["ok"] for c in cons),
            "main_entrance": {"element_id": main["element_id"] if main else None, "candidates": cands,
                              "state": "IDENTIFIED" if main else "REVIEW"},
            "summary": summary(els)}


def summary(els):
    rel = [el for el in els if el["released"]]
    out = {"released": {}, "provisional_not_released": 0, "lift_excluded": 0, "unresolved": 0}
    for cls in RELEASED_CLASSES:
        sel = [el for el in rel if el["boq_class"] == cls]
        areas = [el["area_m2"] for el in sel if el["area_m2"] is not None and el["area_state"] != "ASSUMED"]
        out["released"][cls] = {"count": len(sel), "leaves": sum(el["leaf_count"] for el in sel),
                                "width_m": round(sum(el["structural_opening_width_m"] for el in sel), 6),
                                "area_m2_confirmed": round(sum(areas), 6) if len(areas) == len(sel) and sel else None,
                                "height_blocked": sum(1 for el in sel if el["height"]["state"] == "BLOCKED")}
    out["provisional_not_released"] = sum(1 for el in els if el["section"] == "PROVISIONAL_NOT_RELEASED")
    out["lift_excluded"] = sum(1 for el in els if el["section"] == "LIFT_EXCLUDED")
    out["unresolved"] = sum(1 for el in els if el["state"] == UNRESOLVED)
    out["by_state"] = dict(Counter(el["state"] for el in els))
    return out


def boq_lines(ctx, model, *, rule_set=None, rule_set_digest=None):
    """one line per RELEASED door element (count 1); width / height / area and their sources in the inputs; a BLOCKED
    height leaves the count and the width, never an invented height."""
    lines = []
    for el in model["elements"]:
        if not el["released"]:
            continue
        h = el["height"]
        notes = [f"height {h['state']}: {h['source']}"]
        if el["leaf_count"] > 1:
            notes.append(f"one door assembly with {el['leaf_count']} leaves")
        if el["boq_class"] == MAIN and el["material"] == "NOT_ESTABLISHED":
            notes.append("MAIN_ENTRANCE material NOT_ESTABLISHED (project-specific)")
        lines.append(BL.make_line(
            project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"], item_code=el["boq_class"],
            unit="pcs", evidence_state="SOURCE_DERIVED", measured_net=1, element_id=el["element_id"],
            floor=el["floor"], room_id=el["from_room"] or el["to_room"], physical_element=el["element_id"],
            formula="one door assembly (confirmed band opening); width jamb to jamb",
            inputs={"width_m": round(el["structural_opening_width_m"], 6), "height_m": h["value_m"],
                    "height_state": h["state"], "height_source": h["source"], "area_m2": el["area_m2"],
                    "area_state": el["area_state"], "leaf_count": el["leaf_count"],
                    "from_room": el["from_room"], "to_room": el["to_room"],
                    "frame_width_m": el["frame_width_m"], "material": el["material"]},
            documents=ctx["documents"], geometry_source="CAD_VECTOR", geometry_confidence="EXACT_FACE",
            rule_id=DOOR_RULE_ID, rule_version="1", rule_set=rule_set, rule_set_digest=rule_set_digest,
            material_state="PROJECT_OWNER_FACT" if el["boq_class"] in (PVC, ALU) else "BY_SPEC",
            notes="; ".join(notes)))
    return lines


SCHEDULE_COLUMNS = ("section", "element_id", "floor", "state", "boq_class", "leaf_count", "from_room", "to_room",
                    "structural_opening_width_m", "structural_opening_source", "frame_width_m", "frame_source",
                    "nominal_leaf_width_m", "width_range_m", "height_m", "height_state", "height_source", "area_m2",
                    "area_state", "material", "class_evidence", "evidence_kinds", "swings", "opening_id")


def schedule_rows(model):
    rows = []
    order = {"RELEASED": 0, "PROVISIONAL_NOT_RELEASED": 1, "LIFT_EXCLUDED": 2}
    for el in sorted(model["elements"], key=lambda e: (order[e["section"]], e["floor"], e["element_id"])):
        rows.append({"section": el["section"], "element_id": el["element_id"], "floor": el["floor"],
                     "state": el["state"], "boq_class": el["boq_class"], "leaf_count": el["leaf_count"],
                     "from_room": el["from_room"], "to_room": el["to_room"],
                     "structural_opening_width_m": _r(el["structural_opening_width_m"]),
                     "structural_opening_source": el["structural_opening_source"],
                     "frame_width_m": _r(el["frame_width_m"]), "frame_source": el["frame_source"],
                     "nominal_leaf_width_m": [_r(x) for x in el["nominal_leaf_width_m"]],
                     "width_range_m": el.get("width_range_m"), "height_m": el["height_m"],
                     "height_state": el["height"]["state"], "height_source": el["height"]["source"],
                     "area_m2": el["area_m2"], "area_state": el["area_state"], "material": el["material"],
                     "class_evidence": el.get("class_evidence"),
                     "evidence_kinds": sorted({e["kind"] for e in el["evidence"]}),
                     "swings": [s.split("|")[-1] for s in el["swings"]], "opening_id": el["opening_id"]})
    return rows


def _r(v):
    return None if v is None else round(v, 4)


def policy_record():
    return {"policy": POLICY_ID, "rule_id": DOOR_RULE_ID, "classes": [PVC, ALU, MAIN, LIFT],
            "states": [CONFIRMED, PROVISIONAL, UNRESOLVED], "confirming_evidence": list(CONFIRMING_KINDS),
            "frame_disagree_mm": FRAME_DISAGREE_MM, "pair_tol": PAIR_TOL,
            "never": ["a swing radius used as a BOQ width", "a provisional or lift door in a released total",
                      "a height invented (BLOCKED unless a source or an authorised ASSUMED fallback gives it)",
                      "a main entrance assumed when zero or several candidates remain",
                      "a main entrance also counted as PVC or aluminium", "the nib rule (P2-13, not reviewed)",
                      "external by swing direction or layer name"]}
