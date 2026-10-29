"""T-313: the opening reveal ledger (every villa). Research only: no engine quantity is changed.

Physical elements (ERS s.2.1), per opening and per SIDE of the wall, each measured once:

- WINDOW, room side (UP-REVEAL-001, OWNER_APPROVED): the reveal between the room's wall face and the frame / glazing.
  jambs = 2 x depth x the window height inside the plaster band; head soffit = depth x width only where wall remains
  above the head inside the band; the SILL SURFACE (depth x width) is its own row (finish by the window detail).
  Floor-level glazing: no sill row; the strip is floor (the room's floor finish), so it is a FLOOR row, not a reveal.
- WINDOW, outside: the exterior reveal between the frame and the outer wall face: jambs 2 x depth x height, head
  depth x width, the external sill depth x width as its own row. Its EDGE (arris) length = 2 h + w (+ w sill), the
  quantity the facade corners line carries (T-162 r2 opening_reveal_ml); the reveal SURFACE is never a facade face.
- DOOR / GATE (UP-FIN-PLASTER-001, OWNER_APPROVED): ONE reveal through the wall thickness: 2 x t x h + t x w (head);
  a door has NO sill reveal (refused). It is owned once (never split into two room finishes). r2: the candidate
  already carries it in FIN.PLASTER 'door jambs and head' where the engine has the opening: bind it there
  (`bind_lines` + `reconcile_line`); `book_missing` refuses to count a component another family carries.
- ARCH: jambs 2 x t x springing height + head t x DEVELOPED arc length (T-238); an undeveloped / undrawn arch is HELD.

Depth source is MEASURED (wall face to frame line on the plan) or the opening row is UNRESOLVED blank; a default or
typical depth is refused, a frame flush with a face gives depth 0 with that evidence (state NONE, no surface).
Finish: the owner method URBAN-REVEAL-FINISH-METHOD v1 (data/registry; default PLASTER, paint on a painted dry
surface, porcelain only when shown) is carried as the finish CANDIDATE with its source; UP-REF-REVEAL-001 is
REFERENCE_ONLY in the route, so the finish status stays OWNER_METHOD_CANDIDATE (never DRAWING-CONFIRMED).
Units: every length in metres; `to_m` converts an explicit unit; an unknown unit is refused.
"""

from __future__ import annotations

import math

UNIT_TO_M = {"m": 1.0, "mm": 0.001, "cm": 0.01}
STATES = ("MEASURED", "NONE", "UNRESOLVED", "HELD")
NO_LINE = "NO_LINE"


class LedgerError(ValueError):
    pass


def to_m(value, unit):
    if value is None:
        return None
    if unit not in UNIT_TO_M:
        raise LedgerError(f"unknown unit {unit!r}")
    return float(value) * UNIT_TO_M[unit]


def depth_from_plan(face_offset_m, frame_offset_m):
    """reveal depth = the perpendicular distance between a wall face and the frame line, both as signed offsets across
    the wall (any origin, any orientation: a mirror or rotation changes both signs and leaves the distance)."""
    if face_offset_m is None or frame_offset_m is None:
        return None
    return abs(float(face_offset_m) - float(frame_offset_m))


def _r(x):
    return None if x is None else round(x, 6)


def _need(op, key):
    v = op.get(key)
    if v is None:
        return None
    if not isinstance(v, (int, float)) or v < 0:
        raise LedgerError(f"{op['id']}: {key} must be a non-negative length in metres, got {v!r}")
    return float(v)


def window_rows(op):
    """op: id, kind WINDOW / FLOOR_GLAZING, width_m, height_m, sill_m (above F.F.L.), depth_in_m, depth_out_m,
    depth_in_source / depth_out_source, plaster_height_m (room side band top above F.F.L., None = not established),
    height_status, room. -> rows (one per side component)."""
    if op.get("default_depth"):
        raise LedgerError(f"{op['id']}: a default reveal depth is refused (measure it or leave it UNRESOLVED)")
    w, h = _need(op, "width_m"), _need(op, "height_m")
    sill = _need(op, "sill_m")          # None = not established: never taken as 0 (the room-side band is HELD)
    din, dout = _need(op, "depth_in_m"), _need(op, "depth_out_m")
    Hp = _need(op, "plaster_height_m")
    floor_glz = op["kind"] == "FLOOR_GLAZING"
    rows = []

    def row(side, comp, area, ml, state, basis, depth=None):
        rows.append({"opening": op["id"], "kind": op["kind"], "side": side, "component": comp, "depth_m": _r(depth),
                     "m2": _r(area), "ml": _r(ml), "state": state, "basis": basis,
                     "height_status": op.get("height_status"), "room": op.get("room")})

    low = "FLOOR_STRIP" if floor_glz else "SILL"

    # ---- room side (UP-REVEAL-001)
    if din is None:
        for comp in ("JAMBS", "HEAD", low):
            row("IN", comp, None, None, "UNRESOLVED", "depth not measured")
    elif din == 0.0:
        for comp in ("JAMBS", "HEAD", low):
            row("IN", comp, 0.0, 0.0, "NONE", f"frame flush with the room face ({op.get('depth_in_source')})", 0.0)
    else:
        if h is None or sill is None or Hp is None or w is None:
            why = ("window height not established" if h is None else "sill level not established" if sill is None
                   else "room plaster height not established" if Hp is None else "width not established")
            row("IN", "JAMBS", None, None, "HELD", why, din)
            row("IN", "HEAD", None, None, "HELD", why, din)
        else:
            head = sill + h
            band = max(0.0, min(head, Hp) - max(sill, 0.0))
            row("IN", "JAMBS", 2 * din * band, 2 * band, "MEASURED",
                f"2 x {din:.3f} x {band:.3f} (band inside the plaster height {Hp:.2f})", din)
            above = head < Hp - 1e-9
            row("IN", "HEAD", din * w if above else 0.0, w if above else 0.0, "MEASURED" if above else "NONE",
                f"{din:.3f} x {w:.3f}" if above else "no wall above the head inside the plaster band", din)
        if w is None:
            row("IN", low, None, None, "HELD", "width not established", din)
        elif floor_glz:
            row("IN", low, din * w, 0.0, "MEASURED", "floor-level glazing: the strip is floor (floor finish)", din)
        else:
            row("IN", low, din * w, w, "MEASURED", f"internal sill surface {din:.3f} x {w:.3f} (own item)", din)
    # ---- outside (exterior reveal; its edge = the arris m.l at the outer face)
    olow = "THRESHOLD" if floor_glz else "SILL"
    if dout is None:
        for comp in ("JAMBS", "HEAD", olow):
            row("OUT", comp, None, None, "UNRESOLVED", "depth not measured")
    elif dout == 0.0:
        for comp in ("JAMBS", "HEAD", olow):
            row("OUT", comp, 0.0, 0.0, "NONE", f"frame flush with the outer face ({op.get('depth_out_source')})", 0.0)
    else:
        if h is None:
            row("OUT", "JAMBS", None, None, "HELD", "window height not established", dout)
        else:
            row("OUT", "JAMBS", 2 * dout * h, 2 * h, "MEASURED", f"2 x {dout:.3f} x {h:.3f}", dout)
        if w is None:
            row("OUT", "HEAD", None, None, "HELD", "width not established", dout)
            row("OUT", olow, None, None, "HELD", "width not established", dout)
        else:
            row("OUT", "HEAD", dout * w, w, "MEASURED", f"{dout:.3f} x {w:.3f}", dout)
            if floor_glz:
                row("OUT", olow, dout * w, 0.0, "MEASURED", "external threshold strip at floor level (own item; a "
                    "floor edge, no arris)", dout)
            else:
                row("OUT", olow, dout * w, w, "MEASURED", f"external sill {dout:.3f} x {w:.3f} (own item)", dout)
    return rows


def door_rows(op):
    """op: id, kind DOOR / GATE, width_m, height_m, wall_t_m, height_status. One reveal through the wall (owner rule
    UP-FIN-PLASTER-001); a sill reveal is refused."""
    if op.get("sill_reveal"):
        raise LedgerError(f"{op['id']}: a door has no sill reveal (refused)")
    if op.get("default_depth"):
        raise LedgerError(f"{op['id']}: a default reveal depth is refused")
    w, h, t = _need(op, "width_m"), _need(op, "height_m"), _need(op, "wall_t_m")
    base = {"opening": op["id"], "kind": op["kind"], "side": "THROUGH", "depth_m": _r(t),
            "height_status": op.get("height_status"), "room": op.get("room")}
    if w is None or t is None:
        return [dict(base, component=c, m2=None, ml=None, state="UNRESOLVED", basis="width / wall thickness not "
                     "established") for c in ("JAMBS", "HEAD")]
    head = dict(base, component="HEAD", m2=_r(t * w), ml=_r(w), state="MEASURED", basis=f"{t:.3f} x {w:.3f}")
    if h is None:
        return [dict(base, component="JAMBS", m2=None, ml=None, state="HELD", basis="door height not established"),
                head]
    return [dict(base, component="JAMBS", m2=_r(2 * t * h), ml=_r(2 * h), state="MEASURED",
                 basis=f"2 x {t:.3f} x {h:.3f}"), head]


def arch_rows(op):
    """op: id, width_m (chord), springing_m (jamb height), developed_m (arc length or None), wall_t_m."""
    t, s, dev = _need(op, "wall_t_m"), _need(op, "springing_m"), _need(op, "developed_m")
    base = {"opening": op["id"], "kind": "ARCH", "side": "THROUGH", "depth_m": _r(t),
            "height_status": op.get("height_status"), "room": op.get("room")}
    out = []
    if t is None or s is None:
        out.append(dict(base, component="JAMBS", m2=None, ml=None, state="UNRESOLVED", basis="arch not drawn / "
                        "springing not established"))
    else:
        st = op.get("jamb_state", "HELD")
        v = (_r(2 * t * s), _r(2 * s)) if st == "MEASURED" else (None, None)   # a HELD row carries no quantity
        out.append(dict(base, component="JAMBS", m2=v[0], ml=v[1], state=st,
                        basis=f"2 x {t:.3f} x {s:.3f} = {2 * t * s:.6f} m2 candidate" if st != "MEASURED" else
                        f"2 x {t:.3f} x {s:.3f}"))
    if t is None or dev is None:
        out.append(dict(base, component="HEAD", m2=None, ml=None, state="UNRESOLVED", basis="arch not developed"))
    else:
        if op.get("width_m") is not None and dev < float(op["width_m"]) - 1e-9:
            raise LedgerError(f"{op['id']}: a developed arch shorter than its chord is refused")
        st = op.get("head_state", "HELD")
        v = (_r(t * dev), _r(dev)) if st == "MEASURED" else (None, None)
        out.append(dict(base, component="HEAD", m2=v[0], ml=v[1], state=st,
                        basis=f"{t:.3f} x developed {dev:.4f}" + ("" if st == "MEASURED" else
                                                                  f" = {t * dev:.6f} m2 candidate")))
    return out


def ledger(openings):
    """-> rows for every opening; each opening id once (a duplicate id is refused)."""
    seen, rows = set(), []
    for op in openings:
        if op["id"] in seen:
            raise LedgerError(f"opening {op['id']} listed twice")
        seen.add(op["id"])
        k = op["kind"]
        if k in ("WINDOW", "FLOOR_GLAZING"):
            rows += window_rows(op)
        elif k in ("DOOR", "GATE"):
            rows += door_rows(op)
        elif k == "ARCH":
            rows += arch_rows(op)
        else:
            raise LedgerError(f"{op['id']}: unknown opening kind {k!r}")
    return rows


def bind_lines(rows, binding):
    """binding: {(opening, side, component): line_id}. Every row gets one line id or NO_LINE; a line id may carry the
    components of ONE opening only (one opening in two lines or two openings in one line is refused); a binding to a
    row that does not exist is refused."""
    keys = {(r["opening"], r["side"], r["component"]) for r in rows}
    for k in binding:
        if k not in keys:
            raise LedgerError(f"binding names a row that does not exist: {k}")
    owner = {}
    for (oid, side, comp), lid in binding.items():
        if lid == NO_LINE:
            continue
        if owner.setdefault(lid, oid) != oid:
            raise LedgerError(f"line {lid} carries two openings ({owner[lid]}, {oid})")
    per_open = {}
    for (oid, side, comp), lid in binding.items():
        if lid != NO_LINE:
            per_open.setdefault(oid, set()).add(lid)
    for oid, lids in per_open.items():
        if len(lids) > 1:
            raise LedgerError(f"opening {oid} is carried in two lines {sorted(lids)}")
    return [dict(r, line_id=binding.get((r["opening"], r["side"], r["component"]), NO_LINE)) for r in rows]


def book_missing(rows, carried):
    """the MISSING-SCOPE total: MEASURED rows bound to NO_LINE. carried = {(opening, side, component): (family,
    line_id)} found by searching EVERY item family of the candidate of record by physical element (r2, Verifier
    2026-10-28: the door reveals live in FIN.PLASTER 'door jambs and head', not in ARCH.WINDOW_REVEAL). A row that
    another family's line already carries but is booked NO_LINE is refused (that would be a second count at
    integration). -> {(kind, side, component): {"m2", "ml", "openings"}}"""
    out = {}
    for r in rows:
        k = (r["opening"], r["side"], r["component"])
        if r.get("line_id", NO_LINE) != NO_LINE or r["state"] != "MEASURED":
            continue
        if k in carried:
            fam, lid = carried[k]
            raise LedgerError(f"{k[0]} {k[1]} {k[2]}: already carried in {fam} line {lid}; booking it as missing "
                              "scope is a second count (refused)")
        t = out.setdefault((r["kind"], r["side"], r["component"]), {"m2": 0.0, "ml": 0.0, "openings": []})
        t["m2"] += r["m2"]
        t["ml"] += r["ml"]
        t["openings"].append(r["opening"])
    for t in out.values():
        t["m2"], t["ml"] = round(t["m2"], 6), round(t["ml"], 6)
    return out


def reconcile_line(rows, opening, components, line, tol=1e-6):
    """one candidate line that carries several ledger components of ONE opening (e.g. FIN.PLASTER 'door jambs and
    head' = 2 t h + t w). line: {"line_id", "family", "measured" (float or None), "range" ([lo, hi] or None)}.
    -> {"ledger_m2", "line_m2" / "line_range", "residual_m2", "verdict"}: EQUAL (|residual| <= tol), WITHIN_BOUND
    (ledger inside the line's range; the residuals to both ends named), DIFFERS (residual named), or LEDGER_OPEN
    (a component not MEASURED: no comparison, never 0)."""
    sel = [r for r in rows if r["opening"] == opening and r["component"] in components]
    if {r["component"] for r in sel} != set(components):
        raise LedgerError(f"{opening}: components {components} not all in the ledger")
    rec = {"opening": opening, "line_id": line["line_id"], "family": line["family"],
           "line_m2": line.get("measured"), "line_range": line.get("range")}
    if any(r["state"] != "MEASURED" for r in sel):
        return dict(rec, ledger_m2=None, residual_m2=None, verdict="LEDGER_OPEN")
    led = round(sum(r["m2"] for r in sel), 6)
    rec["ledger_m2"] = led
    if line.get("measured") is not None:
        res = round(led - float(line["measured"]), 6)
        return dict(rec, residual_m2=res, verdict="EQUAL" if abs(res) <= tol else "DIFFERS")
    lo, hi = (float(x) for x in line["range"])
    if lo - tol <= led <= hi + tol:
        return dict(rec, residual_m2=[round(led - lo, 6), round(led - hi, 6)], verdict="WITHIN_BOUND")
    return dict(rec, residual_m2=[round(led - lo, 6), round(led - hi, 6)], verdict="DIFFERS")


def refuse_facade_overlap(rows, facade_face_ids):
    """a reveal surface counted again as a facade face is refused (the EDGE stays in the corners m.l line)."""
    for r in rows:
        if r["side"] == "OUT" and f"{r['opening']}:{r['component']}" in facade_face_ids:
            raise LedgerError(f"{r['opening']} {r['component']}: reveal surface counted in the facade face too")
    return True


def totals(rows):
    """per side and component: measured m2 / m.l, and the openings HELD / UNRESOLVED by name (never 0)."""
    out = {}
    for r in rows:
        k = (r["side"], r["component"])
        t = out.setdefault(k, {"m2": 0.0, "ml": 0.0, "n_measured": 0, "none": [], "held": [], "unresolved": []})
        if r["state"] == "MEASURED":
            t["m2"] += r["m2"]
            t["ml"] += r["ml"]
            t["n_measured"] += 1
        elif r["state"] == "NONE":
            t["none"].append(r["opening"])
        elif r["state"] == "HELD":
            t["held"].append(r["opening"])
        else:
            t["unresolved"].append(r["opening"])
    for t in out.values():
        t["m2"], t["ml"] = round(t["m2"], 6), round(t["ml"], 6)
    return out


def exterior_edge_ml(rows):
    """exterior reveal EDGE length (arrises at the outer face) = jambs + head + sill m.l of the OUT rows that are
    MEASURED; NONE (flush) frames still have the arris: their edge is taken from the opening size, passed in the
    row's ml when known."""
    return round(sum(r["ml"] for r in rows if r["side"] == "OUT" and r["state"] == "MEASURED"), 6)


def reconcile(value, parts, tol=1e-6):
    """value = sum(parts.values()) within tol, else refused with the residual named."""
    s = sum(parts.values())
    if abs(value - s) > tol:
        raise LedgerError(f"reconciliation does not close: {value} vs {s} (residual {value - s:+.6f})")
    return round(value - s, 9)


__all__ = ["LedgerError", "NO_LINE", "to_m", "depth_from_plan", "window_rows", "door_rows", "arch_rows", "ledger",
           "bind_lines", "book_missing", "reconcile_line", "refuse_facade_overlap", "totals", "exterior_edge_ml", "reconcile", "math"]
