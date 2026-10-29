"""T-336 core: bind a checked wet-area / pool waterproofing piece inventory to a candidate's WP line ids by PHYSICAL
face and PHYSICAL door, and write the FILL table an integration package consumes unchanged (R-T336-WP-BIND-1).

Project-independent research rule (not a rule-file version; provenance Q-35 C, UP-WP-003, T-303 / T-309 Checker
verdicts, ERS s.2 - s.4):

1. One physical piece, one line. A piece (room floor, room wall upturn, door threshold, door transition, door
   transition count, room floor penetrations, open-edge membrane termination, pool layer) is carried by exactly one
   candidate line or is a NEW row named by its key; a piece in two lines is a double count and is refused.
2. A door is one physical element: its threshold, its transition and its transition count are keyed by the door,
   never by a room side. Two room-side lines for one door are REPLACED by one door-keyed row; a door with none gets a
   door-keyed NEW row (blank when its measure is held), never 0.
3. An opening interrupts a layer only where it physically meets it: a window whose sill is above the layer's top
   (0.20 m wall upturn) is NOT deducted from it and carries no membrane termination; a sill at or below the top is.
   A sill that is not printed leaves the upturn HELD (never deducted by default, never kept by default).
4. A column standing inside a printed room box is not floor: the floor membrane is the drawn wall-face outline net of
   the column footprint that projects into the room (the printed box dimension runs to the wall face, not the
   column face).
5. HELD / UNKNOWN pieces carry a blank quantity (and a bound where one exists), never 0; a NOT_APPLICABLE piece carries
   its evidence; a procurement count (membrane rolls) is never a face and is never re-measured here.
"""
from __future__ import annotations

RULE_ID = "R-T336-WP-BIND-1"
SCHEMA = "T336_WP_BINDING_V1"
UPTURN_M = 0.20                       # UP-WP-003 (owner Q-03 / Q-24): 0.20 m wet-room wall upturn
TOL = 0.0005                          # a residual that prints 0.000 at 3 decimals (stated)

STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN",
            "NOT_APPLICABLE_WITH_EVIDENCE", "PROCUREMENT")
HELD_LIKE = ("HELD", "UNKNOWN")
ACTIONS = ("KEEP", "CORRECT", "REPLACE_BY_DOOR_ROW", "ADD_ROW", "SET_NOT_APPLICABLE")
UNITS = ("m2", "m3", "lm", "pcs")
KINDS = ("FLOOR", "WALL_UPTURN", "THRESHOLD", "TRANSITION", "TRANSITION_NR", "PENETRATION", "TERMINATION",
         "MEMBRANE_ROLLS", "POOL_MEMBRANE", "POOL_SCREED", "TANK", "ROOF", "ROOF_UPTURN")
DOOR_KINDS = ("THRESHOLD", "TRANSITION", "TRANSITION_NR")


class BindingError(ValueError):
    """the binding breaks R-T336-WP-BIND-1 (double count, held as 0, unit, missing evidence ...)."""


def _num(x, what, lo=0.0, hi=1e6):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise BindingError(f"{what}: number required, got {x!r}")
    if not (lo <= float(x) <= hi):
        raise BindingError(f"{what}: {x} outside {lo} .. {hi} (metres expected; a millimetre value is refused)")
    return float(x)


# --------------------------------------------------------------------------------------------- physical rules
def opening_interrupts(sill_m, layer_top_m=UPTURN_M):
    """rule 3: True when the opening reaches the layer (sill at or below its top). An unprinted sill raises."""
    if sill_m is None:
        raise BindingError("sill not printed: the layer behind the opening stays HELD (rule 3)")
    s = _num(sill_m, "sill", 0.0, 10.0)
    return s <= _num(layer_top_m, "layer top", 0.0, 10.0) + 1e-9


def upturn_m2(boundary_lm, doors=(), leafless=(), open_edges=(), windows=(), height=UPTURN_M):
    """walls-only upturn (Q-35 C): boundary less door / leafless / open widths, less each window that reaches the
    upturn (rule 3); windows = [(width, sill)]. Returns (m2, lm)."""
    lm = _num(boundary_lm, "boundary", 0.0, 1000.0)
    for w in list(doors) + list(leafless) + list(open_edges):
        lm -= _num(w, "opening width", 0.0, 20.0)
    for w, sill in windows:
        if opening_interrupts(sill, height):
            lm -= _num(w, "window width", 0.0, 20.0)
    if lm < -1e-9:
        raise BindingError(f"openings exceed the boundary ({lm:.4f} lm)")
    lm = round(lm, 6)
    return round(lm * height, 6), lm


def threshold_m2(width_m, depth_m):
    """door threshold piece = jamb-to-jamb width x wall depth (both drawn); a missing value -> None (HELD)."""
    if width_m is None or depth_m is None:
        return None
    return round(_num(width_m, "door width", 0.3, 5.0) * _num(depth_m, "wall depth", 0.05, 1.0), 6)


def floor_net_m2(box_m2, column_footprints_m2=()):
    """rule 4: printed box (wall face to wall face) less the column footprints that project into the room."""
    a = _num(box_m2, "box", 0.0, 1e5)
    for c in column_footprints_m2:
        a -= _num(c, "column footprint", 0.0, 100.0)
    if a <= 0:
        raise BindingError("column footprints exceed the box")
    return round(a, 6)


# --------------------------------------------------------------------------------------------- door pieces
def door_transitions(doors, line_doors):
    """rule 2. doors: {door_id: (room, ...)}; line_doors: {line_id: door_id or None} (the transition lines).
    Returns {door_id: {"lines": [...], "class": ONE / DOUBLE / NONE}}; a line naming no inventory door is refused."""
    out = {d: {"lines": [], "rooms": tuple(r)} for d, r in doors.items()}
    for lid, d in sorted(line_doors.items()):
        if d not in out:
            raise BindingError(f"{lid}: transition line names no inventory door ({d!r})")
        out[d]["lines"].append(lid)
    for d, x in out.items():
        n = len(x["lines"])
        x["class"] = "ONE" if n == 1 else ("NONE" if n == 0 else "DOUBLE")
    return out


def door_row_key(item_code, unit, door_id, face):
    return f"{item_code}[{unit}]/DOOR:{door_id}/{face}"


# --------------------------------------------------------------------------------------------- pieces and binding
def piece(key, family, kind, unit, room, qty=None, status="HELD", line_id=None, new_row=None, evidence=None,
          bound=None, action="KEEP", before=None, before_state=None, note=None):
    return {"key": key, "family": family, "kind": kind, "unit": unit, "room": room, "qty": qty, "status": status,
            "line_id": line_id, "new_row": new_row, "evidence": evidence, "bound": bound, "action": action,
            "before": before, "before_state": before_state, "note": note}


def validate_pieces(pieces, candidate_line_ids):
    """every piece once, in one line or one named NEW row; statuses, units, held blank, NA with evidence."""
    seen, line_of = set(), {}
    for p in pieces:
        k = p["key"]
        if k in seen:
            raise BindingError(f"piece {k} listed twice")
        seen.add(k)
        if p["unit"] not in UNITS:
            raise BindingError(f"{k}: unit {p['unit']!r}")
        if p["kind"] not in KINDS:
            raise BindingError(f"{k}: kind {p['kind']!r}")
        if p["status"] not in STATUSES:
            raise BindingError(f"{k}: status {p['status']!r}")
        if p["action"] not in ACTIONS:
            raise BindingError(f"{k}: action {p['action']!r}")
        if p["status"] in HELD_LIKE and p["qty"] is not None:
            raise BindingError(f"{k}: a {p['status']} piece carries a blank quantity, never {p['qty']!r}")
        if p["status"] in ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED") and p["qty"] is None:
            raise BindingError(f"{k}: {p['status']} needs a quantity")
        if p["status"] in ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "NOT_APPLICABLE_WITH_EVIDENCE") \
                and not p["evidence"]:
            raise BindingError(f"{k}: {p['status']} without evidence")
        if p["status"] == "NOT_APPLICABLE_WITH_EVIDENCE" and p["qty"] not in (None,):
            raise BindingError(f"{k}: NOT_APPLICABLE carries no quantity")
        if bool(p["line_id"]) == bool(p["new_row"]):
            raise BindingError(f"{k}: exactly one of a candidate line id and a NEW row name")
        if p["line_id"]:
            if p["line_id"] not in candidate_line_ids:
                raise BindingError(f"{k}: {p['line_id']} is not a line of the candidate")
            if p["action"] == "ADD_ROW":
                raise BindingError(f"{k}: ADD_ROW on an existing line")
            line_of.setdefault(p["line_id"], []).append(p)
        elif p["action"] not in ("ADD_ROW", "SET_NOT_APPLICABLE"):
            raise BindingError(f"{k}: a NEW row is an ADD_ROW (or a register-only NOT_APPLICABLE row)")
        if p["action"] == "SET_NOT_APPLICABLE" and p["status"] != "NOT_APPLICABLE_WITH_EVIDENCE":
            raise BindingError(f"{k}: SET_NOT_APPLICABLE needs status NOT_APPLICABLE_WITH_EVIDENCE")
        if p["kind"] in DOOR_KINDS and "/DOOR:" not in k:
            raise BindingError(f"{k}: a door piece is keyed by its physical door (rule 2)")
    for lid, ps in line_of.items():
        live = [p for p in ps if p["action"] not in ("REPLACE_BY_DOOR_ROW",)]
        if len(live) > 1:
            raise BindingError(f"{lid} carries {len(live)} pieces {[p['key'] for p in live]}: one piece per line")
    return True


def fill_rows(pieces):
    """the FILL table: one row per candidate line touched or kept, one per NEW row; before / after side by side."""
    rows = []
    for p in sorted(pieces, key=lambda x: (x["family"], x["kind"], x["key"])):
        after = p["qty"]
        if p["status"] == "NOT_APPLICABLE_WITH_EVIDENCE" or p["action"] == "REPLACE_BY_DOOR_ROW":
            after = None
        ch = None
        if after is not None and p["before"] is not None:
            ch = round(after - p["before"], 6)
        rows.append({"row": p["line_id"] or p["new_row"], "piece": p["key"], "family": p["family"],
                     "kind": p["kind"], "unit": p["unit"], "room": p["room"], "action": p["action"],
                     "before_state": p["before_state"], "before": p["before"], "after_status": p["status"],
                     "after": after, "change": ch, "bound": p["bound"], "evidence": p["evidence"],
                     "note": p["note"]})
    return rows


def check_fill(rows):
    """an integration package refuses a FILL table that books a held piece as 0, a door row twice or a line twice."""
    ids = [r["row"] for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise BindingError(f"rows twice: {dup}")
    for r in rows:
        if r["after_status"] in HELD_LIKE and r["after"] is not None:
            raise BindingError(f"{r['row']}: held booked as {r['after']}")
        if r["after_status"] in HELD_LIKE and r["after"] == 0:
            raise BindingError(f"{r['row']}: held as 0")
    doors = {}
    for r in rows:
        if r["kind"] in DOOR_KINDS and r["action"] != "REPLACE_BY_DOOR_ROW" and r["after_status"] != \
                "NOT_APPLICABLE_WITH_EVIDENCE":
            k = (r["kind"], r["piece"])
            doors[k] = doors.get(k, 0) + 1
    twice = sorted(k for k, n in doors.items() if n > 1)
    if twice:
        raise BindingError(f"door pieces carried twice: {twice}")
    return True


def totals(rows, unit="m2", families=None, kinds=None):
    """before / after per kind; HELD never summed (counted apart)."""
    out = {}
    for r in rows:
        if r["unit"] != unit or (families and r["family"] not in families) or (kinds and r["kind"] not in kinds):
            continue
        t = out.setdefault(r["kind"], {"before": 0.0, "after": 0.0, "held_rows": 0, "rows": 0})
        t["rows"] += 1
        if r["before"] is not None:
            t["before"] = round(t["before"] + r["before"], 6)
        if r["after"] is not None:
            t["after"] = round(t["after"] + r["after"], 6)
        if r["after_status"] in HELD_LIKE:
            t["held_rows"] += 1
    return out
