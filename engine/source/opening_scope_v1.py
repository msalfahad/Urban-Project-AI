"""OPENING_SCOPE_V1 (T-175): one opening, several physical consequences, each deducted only from what is built.

A check / ledger piece: NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged);
nothing here is read by a released line. Standard library only; imports no engine module.

Owner rule (Q-73, CONFIRMED 2026-10-22, final; ENGINEERING_REASONING_STANDARD.md section 8): "Deduct the full area of
every actual opening from the relevant blockwork. Apply the rule only to masonry that physically exists. Measure reveals
separately where applicable and prevent double counting." The same full-opening deduction applies to plaster and paint
(owner directive section 6). UP-GEN-003 v1.1.0 keeps the other trades: skirting deducts door widths, wall tile is gross
minus openings, the wet-room upturn is NOT deducted at doorways (UP-WP-002 v2.0.0).

Build before deduct (standard section 3). For every opening, per host wall:
  1. what is physically built in the wall line around it: BLOCK (masonry), GLAZED (a glazed bay or curtain line: no
     masonry, so no masonry deduction), RC (a concrete wall: no masonry deduction; finishes still deducted), NONE;
  2. whether the opening lies inside the measured gross run of that wall (IN_GROSS). An opening that sits in a gap the
     run does not cover (a free-end gap between two runs, a glazing span already taken out of the physical run) is not
     deducted again: that would be a double deduction;
  3. the opening area = width x height, each with its own evidence status (WORKFLOW_CONTROLS section 5). A HELD or
     UNKNOWN width or height makes the area HELD; the wall's net masonry is then HELD (value None, never 0), with the
     mathematical bounds [gross - known - sum(width x clear height), gross - known] reported as BOUNDS, not a quantity;
  4. separate consequences of the same id, never merged into one number: masonry deduction (m2), finish deduction per
     face (m2, family named by the caller), reveal length (m.l: two jambs + head, + sill for a window), reveal depth
     (the wall thickness only when no frame is set in the opening; with a frame its position is not on a plan: HELD),
     sill (windows) or threshold (doors, passages) in m.l, the waterproofing interface (wet side: the upturn runs
     across the doorway, not deducted), and the lintel band over the opening (a concrete element of the structural
     lintel line: its face is not masonry; reported as its own consequence, never silently netted).

Guards (each raises ValueError, so a wrong input never becomes a quantity):
  - a status outside the five section-5 statuses;
  - a width or height given in millimetres by mistake (> 20 m for one opening, or a height above 12 m);
  - one opening id twice on one wall, or the same id deducted from two walls (double count);
  - an opening head above the wall's clear height under the member above: flagged HEAD_ABOVE_SOFFIT and the masonry
    deduction is capped at the clear height (the masonry is not there to deduct), the area beyond is listed;
  - a negative net (deductions larger than the gross): refused, the inputs are inconsistent.
"""

from __future__ import annotations

METHOD = "OPENING_SCOPE_V1"
RULES = ("Q-73 (owner, CONFIRMED 2026-10-22)", "UP-GEN-003 v1.1.0", "UP-WP-002 v2.0.0", "UP-DOOR-HGT-001 / Q-55 C",
         "UP-OPEN-SCHED-001", "ENGINEERING_REASONING_STANDARD.md s.3 build before deduct")

STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
_RANK = {s: i for i, s in enumerate(STATUSES)}          # later = weaker evidence
CONSTRUCTIONS = ("BLOCK", "GLAZED", "RC", "NONE")
KINDS = ("DOOR", "WINDOW", "PASSAGE", "ARCH", "SHAFT", "GATE")
MAX_W_M = 20.0
MAX_H_M = 12.0
TOL = 1e-9


def weakest(*statuses):
    """The weakest evidence status of a combination (HELD and UNKNOWN dominate)."""
    for s in statuses:
        _check_status(s)
    return max(statuses, key=lambda s: _RANK[s])


def _check_status(s):
    if s not in _RANK:
        raise ValueError(f"status {s!r} is not one of the five section-5 statuses {STATUSES}")


def _num(v, what, cap):
    if v is None:
        return None
    v = float(v)
    if v < 0:
        raise ValueError(f"{what} {v} is negative")
    if v > cap:
        raise ValueError(f"{what} {v} m exceeds {cap} m: a value in millimetres? give metres")
    return v


def _known(v, status):
    return v is not None and status not in ("HELD", "UNKNOWN")


def opening_consequences(op, wall):
    """Every physical consequence of one opening on one host wall (dict). `op` keys: id, kind, width_m, width_status,
    height_m, height_status, sill_m (default 0), in_gross (bool), frame (bool), faces (two finish-family names or None
    per side, e.g. ("INTERNAL_PLASTER_PAINT", "EXTERNAL_PLASTER_PAINT"), "WALL_TILE", "NONE"), wet_side (bool),
    lintel ({row, depth_m, min_bearing_m} from the printed lintel schedule, or None), finish_top_m (optional, per side:
    the top of that face's finish band; given -> UP-OPEN-SCHED-001 caps the finish deduction at it; the masonry
    deduction is never capped by a finish). sill_m is the height ABOVE THE FINISHED FLOOR (a level or a chain part
    given by mistake shows up as HEAD_ABOVE_SOFFIT). `wall` keys: id, construction,
    t_m, clear_h_min_m (lowest underside of the member above along the run, None if not established)."""
    kind = op.get("kind")
    if kind not in KINDS:
        raise ValueError(f"opening {op.get('id')}: kind {kind!r} not in {KINDS}")
    cons = wall.get("construction")
    if cons not in CONSTRUCTIONS:
        raise ValueError(f"wall {wall.get('id')}: construction {cons!r} not in {CONSTRUCTIONS}")
    ws, hs = op.get("width_status", "UNKNOWN"), op.get("height_status", "UNKNOWN")
    _check_status(ws)
    _check_status(hs)
    w = _num(op.get("width_m"), f"opening {op.get('id')} width", MAX_W_M)
    h = _num(op.get("height_m"), f"opening {op.get('id')} height", MAX_H_M)
    sill = _num(op.get("sill_m") or 0.0, f"opening {op.get('id')} sill", MAX_H_M)
    t = _num(wall.get("t_m"), f"wall {wall.get('id')} thickness", 2.0)
    clear = _num(wall.get("clear_h_min_m"), f"wall {wall.get('id')} clear height", MAX_H_M)
    w_ok, h_ok = _known(w, ws), _known(h, hs)
    area_status = weakest(ws, hs) if (w_ok and h_ok) else ("HELD" if "UNKNOWN" not in (ws, hs) else "UNKNOWN")
    area = round(w * h, 6) if (w_ok and h_ok) else None
    flags = []
    out = {"id": op.get("id"), "kind": kind, "wall": wall.get("id"), "construction": cons,
           "in_gross": bool(op.get("in_gross")), "width_m": w, "width_status": ws, "height_m": h,
           "height_status": hs, "sill_m": sill, "opening_m2": area, "opening_status": area_status}

    # 1. masonry: only where masonry is built AND the opening lies inside the measured gross run
    if cons != "BLOCK":
        out["block_deduction"] = {"m2": None, "status": "NOT_APPLICABLE",
                                  "why": f"host is {cons}: no masonry is built in this line, nothing to deduct from"}
    elif not out["in_gross"]:
        out["block_deduction"] = {"m2": None, "status": "NOT_APPLICABLE",
                                  "why": "the opening lies outside the measured gross run (gap already excluded): "
                                         "deducting it again would be a double deduction"}
    elif area is None:
        out["block_deduction"] = {"m2": None, "status": area_status,
                                  "why": "width or height not established: deduction HELD (never 0)",
                                  "bound_max_m2": (round(w * max(clear - sill, 0.0), 6)
                                                   if (w_ok and clear is not None) else None)}
    else:
        m2, beyond = area, 0.0
        if clear is not None and sill + h > clear + TOL:
            flags.append("HEAD_ABOVE_SOFFIT")
            capped = round(w * max(clear - sill, 0.0), 6)
            beyond, m2 = round(area - capped, 6), capped
        out["block_deduction"] = {"m2": m2, "status": area_status, "beyond_masonry_m2": beyond or None}

    # 2. finishes, one per face (plaster / paint / tile per the caller's face families); RC and BLOCK both finished
    faces = tuple(op.get("faces") or (None, None))
    if len(faces) != 2:
        raise ValueError(f"opening {op.get('id')}: give exactly two face families (side A, side B)")
    tops = tuple(op.get("finish_top_m") or (None, None))
    fin = []
    for side, fam, top in zip(("A", "B"), faces, tops):
        top = _num(top, f"opening {op.get('id')} finish top side {side}", MAX_H_M)
        if fam in (None, "NONE"):
            fin.append({"side": side, "family": fam or "NONE", "m2": None, "status": "NOT_APPLICABLE"})
        elif cons == "GLAZED":
            fin.append({"side": side, "family": fam, "m2": None, "status": "NOT_APPLICABLE",
                        "why": "glazed line: no wall face to finish"})
        elif top is None or area is None:
            fin.append({"side": side, "family": fam, "m2": area, "status": area_status,
                        "band": "full opening (no finish top given; the finish method applies UP-OPEN-SCHED-001)"})
        else:
            # UP-OPEN-SCHED-001: deduction = width x (min(head, H) - max(sill, 0)), H = the finish band's top
            band = max(min(sill + h, top) - max(sill, 0.0), 0.0)
            fin.append({"side": side, "family": fam, "m2": round(w * band, 6), "status": area_status,
                        "band": f"UP-OPEN-SCHED-001 with finish top {top} m"})
    out["finish_deduction"] = fin

    # 3. reveals: two jambs + head (+ sill for a window); depth = wall thickness only without a frame
    if h_ok and w_ok:
        rl = 2 * h + w + (w if kind == "WINDOW" else 0.0)
        out["reveal_lm"] = {"m": round(rl, 6), "status": area_status}
    else:
        out["reveal_lm"] = {"m": None, "status": area_status}
    if cons == "GLAZED" or (cons == "NONE"):
        out["reveal_depth"] = {"m": None, "status": "NOT_APPLICABLE"}
    elif op.get("frame"):
        out["reveal_depth"] = {"m": None, "status": "HELD",
                               "why": "frame position in the wall depth is not drawn on a plan: the reveal returns "
                                      "on each side are not established (wall thickness minus frame depth, split)"}
    else:
        out["reveal_depth"] = {"m": t, "status": "DRAWING-CONFIRMED" if t else "UNKNOWN"}

    # 4. sill (window) / threshold (door, passage, arch, gate): one m.l line each, width only
    edge = "SILL" if kind == "WINDOW" else ("THRESHOLD" if kind in ("DOOR", "PASSAGE", "ARCH", "GATE") else None)
    out["edge"] = {"kind": edge, "m": w if (edge and w_ok) else None,
                   "status": ws if edge else "NOT_APPLICABLE"}

    # 5. waterproofing interface: a doorway into a wet room keeps the upturn across it (UP-WP-002 v2.0.0)
    if op.get("wet_side") and kind in ("DOOR", "PASSAGE", "ARCH"):
        out["waterproofing"] = {"upturn_deducted": False, "threshold_lm": w if w_ok else None,
                                "rule": "UP-WP-002 v2.0.0: the upturn runs across the doorway; not deducted"}
    else:
        out["waterproofing"] = None

    # 6. lintel band (structural lintel line): concrete, not masonry; listed, never netted silently
    lt = op.get("lintel")
    if cons != "BLOCK" or not out["in_gross"]:
        out["lintel"] = {"status": "NOT_APPLICABLE"}
    elif lt is None:
        out["lintel"] = {"status": "UNKNOWN", "why": "no printed lintel schedule given for this wall"}
    elif not (w_ok and h_ok) or clear is None:
        out["lintel"] = {"status": "HELD", "row": lt.get("row"),
                         "why": "head height or member soffit not established: whether a lintel is needed is open"}
    else:
        d = float(lt["depth_m"])
        room = clear - (sill + h)
        if room <= TOL:
            out["lintel"] = {"status": "NOT_APPLICABLE", "why": "the head reaches the member above (it is the lintel)"}
        else:
            depth = min(d, room)
            b = float(lt.get("min_bearing_m") or 0.0)
            out["lintel"] = {"status": "HELD", "row": lt.get("row"), "depth_m": depth,
                             "face_m2_candidate_at_min_bearing": round(depth * (w + 2 * b), 6),
                             "why": "the lintel length = width + two bearings; the schedule prints a MINIMUM bearing "
                                    "only and the masonry each side limits it: the face (not masonry) is listed as a "
                                    "candidate for the lintel line, not deducted here",
                             "partial_depth": depth < d}
    out["flags"] = flags
    return out


def wall_net(wall, openings):
    """Net masonry of one wall after its openings. `wall` keys as opening_consequences plus gross_m2, gross_status.
    Returns the per-opening consequences and the net (value None when any deduction is HELD / UNKNOWN or the gross is
    HELD; never 0 for a held quantity)."""
    ids = [o.get("id") for o in openings]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"wall {wall.get('id')}: opening(s) {dup} listed twice (double count)")
    gs = wall.get("gross_status", "UNKNOWN")
    _check_status(gs)
    gross = _num(wall.get("gross_m2"), f"wall {wall.get('id')} gross", 1e6)
    cons = [opening_consequences(o, wall) for o in openings]
    known, held, bound_extra, statuses = 0.0, [], 0.0, [gs]
    for c in cons:
        bd = c["block_deduction"]
        if bd["status"] == "NOT_APPLICABLE":
            continue
        if bd["m2"] is None:
            held.append(c["id"])
            bound_extra += bd.get("bound_max_m2") or 0.0
            statuses.append(bd["status"])
        else:
            known += bd["m2"]
            statuses.append(bd["status"])
    status = weakest(*statuses)
    if gross is None or not _known(gross, gs):
        net, status = None, ("HELD" if gs != "UNKNOWN" else "UNKNOWN")
    elif held:
        net = None
    else:
        net = round(gross - known, 6)
        if net < -TOL:
            raise ValueError(f"wall {wall.get('id')}: deductions {known:.3f} m2 exceed the gross {gross:.3f} m2")
    res = {"wall": wall.get("id"), "construction": wall.get("construction"), "gross_m2": gross,
           "gross_status": gs, "deducted_m2": round(known, 6), "held_openings": held, "net_m2": net,
           "net_status": status, "openings": cons}
    if held and gross is not None and _known(gross, gs):
        res["net_bounds_m2"] = (round(gross - known - bound_extra, 6) if bound_extra else None,
                                round(gross - known, 6))
    return res


def walls_net(walls):
    """Several walls; refuses an opening id deducted from two walls (one opening, one host)."""
    seen = {}
    out = []
    for w in walls:
        for o in w.get("openings") or ():
            key = o.get("id")
            if key in seen and seen[key] != w.get("id"):
                if o.get("in_gross") and w.get("construction") == "BLOCK":
                    raise ValueError(f"opening {key} deducted from two walls ({seen[key]}, {w.get('id')})")
            if o.get("in_gross") and w.get("construction") == "BLOCK":
                seen[key] = w.get("id")
        out.append(wall_net(w, w.get("openings") or ()))
    return out


def policy_record():
    return {"method": METHOD, "rules": list(RULES), "statuses": list(STATUSES), "wired": False,
            "scope": "every villa: per-opening consequence ledger; the masonry net only where masonry is built"}
