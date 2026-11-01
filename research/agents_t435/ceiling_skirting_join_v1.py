"""CEILING_SKIRTING_JOIN_V1 (T-435, rule R-T435-1, any villa): a census of floored spaces joined to the two derived
per-room layers, ceilings (B10 decor ceiling, UP-CEIL-001) and skirting (B3 skirting, UP-SKIRT-001).

Research module, unwired, stdlib only. No layer name, room id or dimension of any villa is in this file.

The physical question (ERS s.2.1): a floored space has, physically, something above it (a ceiling, a stair / landing
soffit, the sky, a void) and something along its wall faces at floor level (skirting, a wall tile that runs to the
floor, a door frame, nothing on an open edge). A derived per-room layer that starts from its own room list (not from the
floor census) can miss a floored space silently (lesson 2026-11-01, T-414 / T-418). R-T435-1:

  1. The census starts from the floor-finish lines (every FIN.FLOOR.* m2 line that is not NOT_APPLICABLE and not a bed
     line) plus every floored part an integration row adds (READY / QUEUED, cited by task), never from the ceiling or
     skirting room list.
  2. Per space and per layer the result is exactly one of:
       OWNED            line ids of that layer on the same face (room id), with their m2 / lm and evidence states;
       REASON           a named reason from REASONS with its evidence, and, where the reason names another family as the
                        owner (stair soffit, wall tile, host face, passage jamb), that line id must exist in the lines;
       SILENT_OMISSION  neither: named with the space's floor m2 (ceiling) or its drawn wall-face lm (skirting; UNKNOWN
                        when not measured, never 0).
     A reason whose cited line does not exist is REFUSED (the space falls to SILENT_OMISSION). A space that has an
     owning line AND a reason that gives the layer to another family is DOUBLE_OWNED (a conflict, never summed).
  3. A face whose ceiling m2 is below its floor m2 by more than TOL is reported PARTIAL with the shortfall in m2 unless a
     reason covers the shortfall (a ceiling smaller than the floor is not an error by itself: stair zones, voids).
  4. Nothing is valued here; HELD stays HELD, UNKNOWN is never 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TOL = 0.005  # m2 / lm, rounding of the candidate's 6-decimal lines

CEILING = "CEILING"
SKIRTING = "SKIRTING"
LAYERS = (CEILING, SKIRTING)

OWNED = "OWNED"
REASON = "REASON"
SILENT = "SILENT_OMISSION"
DOUBLE = "DOUBLE_OWNED"
REFUSED = "REASON_REFUSED"
PARTIAL = "PARTIAL"

# reason code -> (layers it may explain, needs a cited line of another family, the family that must own that line)
REASONS = {
    # ceilings
    "OPEN_TO_SKY": ({CEILING}, False, None),
    "VOID_ABOVE": ({CEILING}, False, None),
    "UNDER_FLIGHT_SOFFIT": ({CEILING}, True, "STAIR"),          # the flight / landing underside: stair finish line
    "CEILING_ON_HOST_FACE": ({CEILING}, True, CEILING),         # the space is part of a face whose ceiling line covers it
    "OPENING_SOFFIT_IN_WALL": ({CEILING}, False, None),         # a doorway strip in the wall thickness: lintel soffit
    # skirting
    "WET_WALL_TILE_TO_FLOOR": ({SKIRTING}, True, "WALL_TILE"),  # wet room: the wall tile runs to the floor (UP-SKIRT-001
                                                                #  locations DRY_ROOMS only)
    "SKIRTING_ON_HOST_FACE": ({SKIRTING}, True, SKIRTING),      # the space's wall faces are inside the host face's line
    "DOORWAY_STRIP": ({SKIRTING}, False, None),                 # a strip across a door: frame / jambs, no wall face
    "NO_WALL_FACE": ({SKIRTING}, False, None),                  # every edge open (balustrade, band, void): B12 / L-18
    "STAIR_SKIRTING": ({SKIRTING}, True, "STAIR"),              # flight / landing sides: B7-07 / B7-08 lines
}


def family_of(item_code: str, trade: str = "") -> str | None:
    """the family a candidate line belongs to for this join (None = not a family the join reads)"""
    c = (item_code or "").upper()
    t = (trade or "").upper()
    if c.startswith("FIN.FLOOR.BED"):
        return "BED"
    if c.startswith("FIN.FLOOR."):
        return "FLOOR"
    if c.startswith("FIN.CEILING"):
        return CEILING
    if c.startswith("FIN.SKIRTING") or c.startswith("FIN.SKIRT"):
        return SKIRTING
    if c.startswith("FIN.WALL_TILE") or c.startswith("FIN.WALL.TILE") or t == "WALL_TILE":
        return "WALL_TILE"
    if (c.startswith("STAIR.") or c.startswith("FIN.STAIR") or t in ("STAIRS", "STAIR_FINISH")
            or c.startswith(("FIN.MARBLE.LANDING", "FIN.MARBLE.TREAD", "FIN.MARBLE.RISER"))):
        return "STAIR"   # a threshold marble (FIN.MARBLE.THRESHOLD, trade MARBLE) is NOT a stair line
    return None


def quantity(line: dict) -> tuple[float | None, tuple[float, float] | None]:
    """(measured value or None, bound or None); a HELD line with no value gives (None, bound or None), never 0"""
    q = line.get("measured_net")
    b = line.get("bounded_range")
    bound = None
    if isinstance(b, (list, tuple)) and len(b) == 2:
        bound = (float(b[0]), float(b[1]))
    elif isinstance(b, dict) and "low" in b and "high" in b:
        bound = (float(b["low"]), float(b["high"]))
    return (float(q) if q is not None else None), bound


@dataclass
class Space:
    space_id: str           # the face / room id the layers are keyed on
    floor: str
    m2: float | None        # floor-finish m2 (None = HELD area, never 0)
    floor_lines: list = field(default_factory=list)
    kind: str = "DRY"       # DRY / WET (from the floor finish code or the source row)
    source: str = "candidate"
    wall_face_lm: float | None = None   # drawn wall-face length at floor level, when a source measures it
    wall_face_status: str = "UNKNOWN"


def is_not_applicable(line: dict) -> bool:
    s = str(line.get("evidence_state") or "").upper()
    return s.startswith("NOT_APPLICABLE")


def census(lines: list[dict], extra_spaces: list[dict] | None = None, face_of=None) -> dict[str, Space]:
    """floored spaces from the floor-finish lines (+ parts an integration row adds), keyed by face id"""
    face_of = face_of or (lambda ln: ln.get("room_id"))
    spaces: dict[str, Space] = {}
    for ln in lines:
        if family_of(ln.get("item_code"), ln.get("trade")) != "FLOOR" or ln.get("unit") != "m2":
            continue
        if is_not_applicable(ln):
            continue
        fid = face_of(ln)
        if not fid:
            raise ValueError(f"floor line {ln.get('line_id')} has no face id")
        q, bound = quantity(ln)
        sp = spaces.setdefault(fid, Space(fid, ln.get("floor", ""), 0.0))
        if q is None:
            sp.m2 = None  # a HELD / bounded floor part makes the space's area HELD, never 0
        elif sp.m2 is not None:
            sp.m2 += q
        sp.floor_lines.append(ln.get("line_id"))
        if "WET" in str(ln.get("item_code")).upper():
            sp.kind = "WET"
    for e in extra_spaces or []:
        sid = e["space_id"]
        if sid in spaces:
            raise ValueError(f"extra space {sid} already in the candidate census: one m2 one line")
        spaces[sid] = Space(sid, e.get("floor", ""), e.get("m2"), [], e.get("kind", "DRY"), e.get("source", "extra"),
                            e.get("wall_face_lm"), e.get("wall_face_status", "UNKNOWN"))
    return spaces


def _by_room(lines: list[dict], fam: str, key_of) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for ln in lines:
        if family_of(ln.get("item_code"), ln.get("trade")) == fam:
            out.setdefault(key_of(ln), []).append(ln)
    return out


def join(spaces: dict[str, Space], lines: list[dict], reasons: list[dict] | None = None, key_of=None) -> list[dict]:
    """one result row per (space, layer); see the module text for the statuses"""
    key_of = key_of or (lambda ln: ln.get("room_id"))
    ids = {ln.get("line_id"): ln for ln in lines}
    own = {CEILING: _by_room(lines, CEILING, key_of), SKIRTING: _by_room(lines, SKIRTING, key_of)}
    rmap: dict[tuple[str, str], list[dict]] = {}
    for r in reasons or []:
        code = r["code"]
        if code not in REASONS:
            raise ValueError(f"unknown reason {code}")
        if r["layer"] not in REASONS[code][0]:
            raise ValueError(f"reason {code} cannot explain {r['layer']}")
        rmap.setdefault((r["space_id"], r["layer"]), []).append(r)
    rows = []
    for sid in sorted(spaces):
        sp = spaces[sid]
        for layer in LAYERS:
            owned = own[layer].get(sid, [])
            if layer == CEILING:
                # the decor ceiling's horizontal lines only (a bulkhead face is not a ceiling over the floor)
                owned_h = [ln for ln in owned if "BULKHEAD" not in str(ln.get("item_code")).upper()]
            else:
                owned_h = owned
            rs = rmap.get((sid, layer), [])
            valid, refused = [], []
            for r in rs:
                needs, fam = REASONS[r["code"]][1], REASONS[r["code"]][2]
                if needs:
                    cited = ids.get(r.get("line_id"))
                    if cited is None or family_of(cited.get("item_code"), cited.get("trade")) != fam:
                        refused.append(r)
                        continue
                valid.append(r)
            row = {"space_id": sid, "floor": sp.floor, "kind": sp.kind, "floor_m2": sp.m2, "source": sp.source,
                   "layer": layer, "line_ids": [ln.get("line_id") for ln in owned_h],
                   "states": sorted({str(ln.get("evidence_state")) for ln in owned_h}),
                   "reasons": [r["code"] for r in valid], "refused": [r["code"] for r in refused],
                   "evidence": "; ".join(r.get("evidence", "") for r in valid)}
            vals = [quantity(ln) for ln in owned_h]
            meas = [q for q, _ in vals if q is not None]
            row["line_qty"] = round(sum(meas), 6) if meas else None
            row["line_bound"] = None
            bounds = [b for q, b in vals if q is None and b is not None]
            if bounds:
                row["line_bound"] = (round(sum(b[0] for b in bounds), 6), round(sum(b[1] for b in bounds), 6))
            gives_away = [r for r in valid if REASONS[r["code"]][1] and REASONS[r["code"]][2] != layer]
            no_need = [r for r in valid if not REASONS[r["code"]][1]]
            if owned_h and (gives_away or (no_need and layer == SKIRTING and
                                           any(r["code"] in ("NO_WALL_FACE", "DOORWAY_STRIP") for r in no_need)) or
                            (no_need and layer == CEILING and
                             any(r["code"] in ("OPEN_TO_SKY", "VOID_ABOVE") for r in no_need))):
                row["status"] = DOUBLE
            elif owned_h:
                row["status"] = OWNED
                if layer == CEILING and sp.m2 is not None and row["line_qty"] is not None and row["line_bound"] is None:
                    short = round(sp.m2 - row["line_qty"], 6)
                    if short > TOL and not valid:
                        row["status"] = PARTIAL
                        row["shortfall_m2"] = short
            elif valid:
                row["status"] = REASON
            else:
                row["status"] = SILENT
            if row["status"] == SILENT:
                if layer == CEILING:
                    row["omission"] = {"unit": "m2", "value": sp.m2, "status": "HELD" if sp.m2 is None else
                                       "FLOOR-AREA (the ceiling's plan area before any eligible-surface deduction)"}
                else:
                    row["omission"] = {"unit": "lm", "value": sp.wall_face_lm, "status": sp.wall_face_status
                                       if sp.wall_face_lm is not None else "UNKNOWN"}
            rows.append(row)
    return rows


def overlap(rows: list[dict]) -> list[str]:
    """a line id owning two spaces in one layer (one m2 / one lm, one line) -> the ids, else []"""
    seen: dict[tuple[str, str], str] = {}
    dup = []
    for r in rows:
        for lid in r["line_ids"]:
            k = (r["layer"], lid)
            if k in seen and seen[k] != r["space_id"]:
                dup.append(lid)
            seen[k] = r["space_id"]
    return sorted(set(dup))


def totals(rows: list[dict]) -> dict:
    out: dict = {}
    for layer in LAYERS:
        rs = [r for r in rows if r["layer"] == layer]
        d = {}
        for st in (OWNED, PARTIAL, REASON, SILENT, DOUBLE):
            sel = [r for r in rs if r["status"] == st]
            d[st] = {"spaces": len(sel), "floor_m2": round(sum(r["floor_m2"] for r in sel if r["floor_m2"]), 4),
                     "floor_m2_held": sum(1 for r in sel if r["floor_m2"] is None)}
        sil = [r for r in rs if r["status"] == SILENT]
        if layer == SKIRTING:
            d[SILENT]["lm_measured"] = round(sum(r["omission"]["value"] for r in sil
                                                 if r["omission"]["value"] is not None), 4)
            d[SILENT]["lm_unknown_spaces"] = sum(1 for r in sil if r["omission"]["value"] is None)
        d["partial_shortfall_m2"] = round(sum(r.get("shortfall_m2", 0.0) for r in rs), 4)
        out[layer] = d
    return out
