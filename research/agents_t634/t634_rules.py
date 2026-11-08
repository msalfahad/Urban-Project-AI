"""R-T634-1 DRY WALL PLASTER AND PAINT, ONE FACE TWO QUANTITIES (every villa; research rule, unwired; T-634).

Physical element: on each internal DRY wall face two separate layers are built: the plaster coat (spatter + plaster,
plasterer) from the finished floor to the underside of the structural slab / roof (Q-72, owner 2026-11-02: plaster
above the false ceiling), and the paint film on the same face from the finished floor to the finished ceiling (Q-72;
owner G1 room formula interval - 0.60 beam - 0.15 decor - 0.10 floor, Q-48 A). A WET face (tiled, owner 2026-11-02
wet-area walls) carries spatter + the tiler's levelling render + porcelain: never paint, never a dry plaster coat.

  1. FACES FROM THE DRAWING. The face length F of a room is its drawn face chain (R-T606-1 geometry: handles, vertices
     at intersections, column notches and their returns included; an arc edge at its true length).
  2. OPENINGS FROM THE DRAWING. Width = the gap between the wall-face pieces on its own face (masonry width) or, for a
     glazing face drawn on the window layer, the face's own length. Sill / head from a printed or merged drawn reading
     (named) or the owner rule (Q-55 C door head 2.20, ASSUMED - OWNER-APPROVED). Part inside a band of height H:
     w x max(0, min(head, H) - max(sill, 0)) (Q-73 full deduction of every actual opening). No head -> HELD (range),
     never 0.
  3. TWO HEIGHTS, NEVER MIXED. A plaster quantity carries the basis SLAB_SOFFIT (Q-72); a plaster height on the
     FINISHED_CEILING / G1 basis is refused. A paint quantity carries FINISHED_CEILING; a paint height on the slab
     basis is refused. The plaster and paint nets of one face are two numbers (gross x own H - openings cut at own H).
  4. ONE FINISH PER FACE. Paint on a tiled (wet) face is refused (owner 2026-11-02).
  5. RETURN FACES. The plastered / painted return of a door = t x (2 x head + w), t the drawn jamb cap (wall
     thickness), w the drawn gap, head per step 2; an opening with no head is HELD, never 0.
  6. ROW EVIDENCE (R-T547-1 split, reference - engine). A room's delta (his cell - the engine line) is fixed by the two
     figures; the re-measure re-splits it into length (his length - own F) x his height, height (his height - H) x own
     F, openings (own deductions) and the LINE residual (own net - engine line). |residual| < ROW_TOL is TOLERANCE,
     else ENGINE_WRONG with its signed size. A stated row is DRAWING-CONFIRMED when its own value equals it within
     ROW_TOL (0.010 m2), else DIFFERS (a finding, never absorbed). A row resting on an owner rule names the rule.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
Z = D("0")
RULE_ID = "R-T634-1"
GOVERNING = ["Q-72 plaster to the slab / roof underside, paint to the finished ceiling", "Q-48 A / owner G1 formula",
             "Q-73 full opening deduction, reveals separate", "Q-55 C door head 2.20",
             "owner 2026-11-02 wet-area walls (no paint on a tiled face)", "UP-FIN-PLASTER-001 returns",
             "R-T547-1 row split", "R-T606-1 / R-T621-1 outline geometry", "ERS s.2 / s.3"]
ROW_TOL = D("0.010")
PLASTER_BASIS = "SLAB_SOFFIT"
PAINT_BASIS = "FINISHED_CEILING"


class RuleError(ValueError):
    pass


def d(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) is never 0")
    if isinstance(x, float):
        return D(repr(x))
    return D(str(x))


def opening_part(op: dict, H) -> Decimal:
    H = d(H)
    w = d(op["w"])
    if op.get("head") is None:
        raise RuleError(f"opening {op.get('id')}: head not established: HELD (range), never 0")
    head, sill = d(op["head"]), d(op.get("sill", 0))
    if w <= 0 or head <= sill:
        raise RuleError(f"opening {op.get('id')}: width / head invalid")
    return w * max(Z, min(head, H) - max(sill, Z))


def face_net(face_lm, height: dict, openings, finish: str, face_class: str = "DRY") -> dict:
    """one finish on one room's faces. height = {'H': value, 'basis': ...}; finish 'plaster' | 'paint'."""
    if finish not in ("plaster", "paint"):
        raise RuleError(f"finish {finish} unknown")
    want = PLASTER_BASIS if finish == "plaster" else PAINT_BASIS
    if height.get("basis") != want:
        raise RuleError(f"{finish} height on the {height.get('basis')} basis refused (Q-72: {finish} -> {want})")
    if finish == "paint" and face_class == "WET":
        raise RuleError("paint on a tiled (wet) face refused (owner 2026-11-02)")
    if face_class not in ("DRY", "WET"):
        raise RuleError(f"face class {face_class} unknown")
    F, H = d(face_lm), d(height["H"])
    if F <= 0 or H <= 0:
        raise RuleError("face length / height must be positive")
    parts = [(op["id"], opening_part(op, H)) for op in openings]
    ded = sum((p for _, p in parts), Z)
    gross = F * H
    if ded > gross:
        raise RuleError("openings exceed the face")
    return {"gross": gross, "openings": ded, "parts": parts, "net": gross - ded}


def return_face(t, w, head) -> Decimal:
    if head is None:
        raise RuleError("return face: head not established: HELD, never 0")
    t, w, head = d(t), d(w), d(head)
    if t <= 0 or w <= 0 or head <= 0:
        raise RuleError("return face: thickness / width / head must be positive")
    return t * (2 * head + w)


def split_room(his_len, his_h, face_lm, H, own_openings, engine_line):
    """R-T547-1 order: length at his height, height on our face, openings, line residual. Exact by construction."""
    hl, hh, F, H, op, line = (d(x) for x in (his_len, his_h, face_lm, H, own_openings, engine_line))
    total = hl * hh - line
    length = (hl - F) * hh
    height = (hh - H) * F
    own_net = F * H - op
    resid = own_net - line
    if length + height + op + resid != total:
        raise RuleError("split does not close")
    cls = "TOLERANCE" if abs(resid) < ROW_TOL else "ENGINE_WRONG"
    return {"total": total, "length": length, "height": height, "openings": op, "line_residual": resid,
            "residual_class": cls, "own_net": own_net}


def row_evidence(own, stated) -> tuple:
    diff = d(own) - d(stated)
    return ("DRAWING-CONFIRMED" if abs(diff) < ROW_TOL else "DIFFERS"), diff
