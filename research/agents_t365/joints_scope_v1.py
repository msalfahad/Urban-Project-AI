"""JOINT_SCOPE_V1 (T-365, research rule, not wired): movement / expansion joints and sealants (family B13-05).

Physical elements (ERS s.2.1), each its own item in m.l:
  STRUCTURAL_MOVEMENT     a joint through the frame (two columns / beams side by side, slabs separated)
  SLAB_ON_GRADE           contraction / isolation joint in a ground-bearing slab
  CONSTRUCTION_JOINT      a planned pour break (with or without a water stop)
  ROOF_FIELD              a movement joint through the roof screed / roof tiles
  TILE_FIELD              a movement joint in an outside tiled floor (balcony, side walk, terrace)
  TILE_PERIMETER          a joint between a tiled field and a wall / upstand
  PAVING                  a joint in external paving (interlock, slabs, in-situ concrete)
  BOUNDARY_WALL_BUILDING  a separation between the boundary wall and the building
  BOUNDARY_WALL_PANEL     a joint along the boundary wall itself
  OPENING_SEALANT         a sealant bead round a door / window frame (belongs to the openings trade when printed)
  PARAPET                 a joint through a parapet / coping

Rules (every villa; provenance T-365):
  R-JT-1  POSITION comes only from the project drawings: a DRAWN joint line (sheet + handle / detail) or a PRINTED spacing
          rule (sheet + note) applied on a DRAWN extent (its own source). Textbook, a picture's numbers, 'typical', the
          freelancer, an engine default and a HATCH are never a position or a spacing (a hatch pitch is a drawing pattern).
  R-JT-2  An owner rule may give a joint's WIDTH / TYPE (Q-42: expansion joint 3 mm); it does not give a position or a
          spacing unless the rule itself states one. Width known + position unknown = HELD, never 0, never measured.
  R-JT-3  Spacing notation is read before arithmetic: MAX ('not exceeding s') -> ceil(L / s) - 1 interior joints per
          direction; EXACT ('at s c/c') -> L / s - 1 only when L / s is a whole number within 1 mm, otherwise HELD
          (layout not fixed); UNSTATED -> HELD.
  R-JT-4  Status: MEASURED (position fixed by R-JT-1 / R-JT-3), HELD (in scope by a printed note or an owner rule, position or
          spacing missing), NOT_IN_DRAWN_SCOPE (nothing printed, no owner rule puts it in scope). A quantity is written only
          when MEASURED; HELD and NOT_IN_DRAWN_SCOPE carry None (never 0).
  R-JT-5  Sealant m.l = joint m.l x the number of sealed faces PRINTED in the joint's type; no printed sealant -> HELD.
  R-JT-6  One joint, one owner trade: a joint segment measured on two lines (for example the paving line and the screed
          line) is a DOUBLE_COUNT and is refused.
  R-JT-7  An RFI candidate is raised only for a DRAWN joint without its type (filler / sealant / water stop), never for an
          undrawn one (absence is NOT_IN_DRAWN_SCOPE, not a question to the designer).

stdlib only.
"""

from __future__ import annotations

import math

RULE_ID = "JOINT_SCOPE_V1"

KINDS = ("STRUCTURAL_MOVEMENT", "SLAB_ON_GRADE", "CONSTRUCTION_JOINT", "ROOF_FIELD", "TILE_FIELD", "TILE_PERIMETER",
         "PAVING", "BOUNDARY_WALL_BUILDING", "BOUNDARY_WALL_PANEL", "OPENING_SEALANT", "PARAPET")
MEASURED, HELD, NOT_IN_DRAWN_SCOPE = "MEASURED", "HELD", "NOT_IN_DRAWN_SCOPE"
POSITION_SOURCES = ("DRAWN_LINE", "PRINTED_SPACING")
REFUSED_SOURCES = ("TEXTBOOK", "PICTURE", "TYPICAL", "FREELANCER", "ENGINE_DEFAULT", "HATCH")
SPACING_KINDS = ("MAX", "EXACT", "UNSTATED")
UNITS = {"m": 1.0, "mm": 0.001, "cm": 0.01}


class JointError(ValueError):
    """A refused input (non-source, missing source, held 0, double count, unit)."""


def to_m(value, unit):
    if unit not in UNITS:
        raise JointError(f"unit {unit!r} not supported")
    return float(value) * UNITS[unit]


def _need_source(obj, what):
    src = obj.get("source")
    if not src or not str(src).strip():
        raise JointError(f"{what} without a source (sheet + handle / note)")
    return src


def check_source_kind(kind, what="position"):
    if kind in REFUSED_SOURCES:
        raise JointError(f"{what} from {kind} refused (R-JT-1): only a drawn line or a printed spacing on a drawn extent")
    if kind not in POSITION_SOURCES:
        raise JointError(f"{what} source kind {kind!r} unknown")


def segment_length(seg):
    """seg = {"p0": [x, y], "p1": [x, y], "unit": "m"|"mm"|"cm"} -> metres."""
    u = seg.get("unit", "m")
    (x0, y0), (x1, y1) = seg["p0"], seg["p1"]
    return math.hypot(to_m(x1, u) - to_m(x0, u), to_m(y1, u) - to_m(y0, u))


def interior_count(length_m, spacing_m, kind):
    """Interior joints across one direction of a field (R-JT-3); None = HELD."""
    if kind not in SPACING_KINDS:
        raise JointError(f"spacing kind {kind!r} unknown")
    if spacing_m is None or kind == "UNSTATED":
        return None
    if spacing_m <= 0 or length_m <= 0:
        raise JointError("spacing and extent must be positive")
    q = length_m / spacing_m
    if kind == "MAX":
        return max(0, math.ceil(q - 1e-9) - 1)
    r = round(q)
    if abs(q - r) * spacing_m > 0.001:
        return None
    return max(0, r - 1)


def spacing_field_length(field):
    """A rectangular drawn field (Lx x Ly, its own source) with a printed spacing rule: interior joint m.l, or None."""
    _need_source(field, "drawn extent")
    sp = field["spacing"]
    check_source_kind(sp.get("source_kind"), "spacing")
    _need_source(sp, "spacing rule")
    u = field.get("unit", "m")
    lx, ly = to_m(field["Lx"], u), to_m(field["Ly"], u)
    s = None if sp.get("value") is None else to_m(sp["value"], sp.get("unit", "m"))
    nx = interior_count(lx, s, sp["kind"])   # joints across x run along y
    ny = interior_count(ly, s, sp["kind"])
    if nx is None or ny is None:
        return None
    return round(nx * ly + ny * lx, 6)


def evaluate(joint):
    """One physical joint record -> status, length (m.l or None), sealant (m.l or None), rfi flag."""
    kind = joint["kind"]
    if kind not in KINDS:
        raise JointError(f"joint kind {kind!r} unknown")
    if "quantity_m" in joint and joint["quantity_m"] == 0 and joint.get("status") != MEASURED:
        raise JointError("a held joint written as 0 (R-JT-4)")
    pos = joint.get("position")
    owner_scope = joint.get("owner_rule")      # e.g. {"id": "Q-42", "width_mm": 3, "spacing": None}
    printed_scope = joint.get("printed_scope")  # e.g. {"source": "ST p.8 note n"}
    out = {"id": joint["id"], "kind": kind, "trade": joint.get("trade"), "line": joint.get("line", "NO LINE"),
           "status": None, "length_m": None, "sealant_m": None, "rfi": None, "why": ""}
    if pos:
        check_source_kind(pos.get("source_kind"))
        _need_source(pos, "joint position")
        if pos["source_kind"] == "DRAWN_LINE":
            length = round(sum(segment_length(s) for s in pos["segments"]), 6)
        else:
            length = spacing_field_length(pos["field"])
        if length is None:
            out.update(status=HELD, why="printed spacing does not fix a layout on the drawn extent (R-JT-3)")
            return out
        out.update(status=MEASURED, length_m=length, why=f"position: {pos['source']}")
        jtype = joint.get("type")
        if not jtype:
            out["rfi"] = f"drawn joint {joint['id']} without its type (filler / sealant / water stop) (R-JT-7)"
            out["sealant_m"] = None
        else:
            _need_source(jtype, "joint type")
            faces = jtype.get("sealed_faces")
            out["sealant_m"] = None if not faces else round(length * int(faces), 6)
        return out
    if joint.get("spacing_from"):
        check_source_kind(joint["spacing_from"], "spacing")  # raises for textbook / picture / hatch ...
    if owner_scope or printed_scope:
        src = (owner_scope or {}).get("id") or (printed_scope or {}).get("source")
        out.update(status=HELD, why=f"in scope by {src}; position / spacing not printed (R-JT-2)")
        return out
    out.update(status=NOT_IN_DRAWN_SCOPE, why=joint.get("evidence", "no sheet prints this joint"))
    return out


def _seg_key(seg):
    u = seg.get("unit", "m")
    a = (round(to_m(seg["p0"][0], u), 3), round(to_m(seg["p0"][1], u), 3))
    b = (round(to_m(seg["p1"][0], u), 3), round(to_m(seg["p1"][1], u), 3))
    return tuple(sorted((a, b)))


def check_double_count(joints):
    """R-JT-6: the same drawn segment on two BOQ lines / trades is refused. Returns the list of segment keys checked."""
    seen = {}
    for j in joints:
        pos = j.get("position") or {}
        for s in pos.get("segments", []) if pos.get("source_kind") == "DRAWN_LINE" else []:
            k = _seg_key(s)
            owner = (j.get("trade"), j.get("line", "NO LINE"))
            if k in seen and seen[k][1] != owner:
                raise JointError(f"DOUBLE_COUNT: segment {k} on {seen[k][1]} and {owner} ({seen[k][0]}, {j['id']})")
            seen.setdefault(k, (j["id"], owner))
    return sorted(seen)


def classify_hatch(h):
    """A hatch is a drawing pattern: never a joint (R-JT-1). Returns the record for the census."""
    return {"handle": h["handle"], "pattern": h["pattern"], "class": "HATCH_NOT_JOINT",
            "why": "a hatch pitch is a drawing pattern, not a joint position or spacing (R-JT-1)"}


def evaluate_all(joints):
    check_double_count(joints)
    rows = [evaluate(j) for j in joints]
    status = {s: sum(1 for r in rows if r["status"] == s) for s in (MEASURED, HELD, NOT_IN_DRAWN_SCOPE)}
    measured = [r["length_m"] for r in rows if r["status"] == MEASURED]
    return {"rule": RULE_ID, "rows": rows, "by_status": status,
            "measured_total_m": round(sum(measured), 6) if measured else None,
            "rfi": [r["rfi"] for r in rows if r["rfi"]]}
