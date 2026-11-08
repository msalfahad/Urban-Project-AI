"""R-T622-1 WET-WALL FACE METHOD (every villa; research rule, unwired; T-622).

Physical element: the porcelain on the inner faces of a wet room (owner 2026-11-02 wet-area walls: spatter dash +
levelling render + adhesive and porcelain; no paint and no skirting on a tiled face), from the finished floor to the
tile top H (owner Q-48 A: underside of the decor ceiling; owner formula slab-to-slab - 0.60 - 0.15 - 0.10), net of the
part of every actual opening inside [0, H] (Q-73). Reveals are measured separately (Q-73 answer: 'measure reveals
separately where applicable and prevent double counting'): they are never inside a face length.

  1. FACES FROM THE DRAWING. The tiled length F of a room is its drawn face chain (R-T606-1 / R-T621-1 geometry:
     handles, vertices at intersections, column notches and their returns included) less every OPEN SIDE. An open side
     is a named drawn line that is not a wall face (threshold, step, counter front); its length is its own. A side with
     no wall is never closed by the nearest wall or by an assumed face (refused: 'closed across an open side').
  2. OPENINGS FROM THE DRAWING. Each opening's width is the gap between the wall-face pieces on its own face (masonry
     width, frame included); its sill / head come from a printed dimension, a merged drawn reading (named), or the owner
     rule (Q-55 C door head 2.20, ASSUMED - OWNER-APPROVED). Part inside the band: door w x min(head, H); window
     w x max(0, min(head, H) - max(sill, 0)). An opening with no head is HELD (range), never 0.
  3. FACE-LEVEL HEIGHT CAP. A face whose wall is lower than H (a half-height wall drawn with its own height) is tiled
     to min(h_wall, H) on each exposed side; its cap (top) is NOT a face: it stays HELD by name unless the drawing
     prints its finish (no default cap finish). The strip of a room face hidden behind the low wall's end is tiled only
     above it (band [h_from, H]).
  4. ONE FINISH PER FACE. A face carrying tile may not also carry paint (or skirting): refused (owner 2026-11-02).
  5. ROW EVIDENCE. A reconciled-quantities row is DRAWING-CONFIRMED when its own value rebuilt by 1-4 from the drawing
     equals the stated row within ROW_TOL (0.010 m2, the R-T547-1 tolerance; his 2-dp working and CAD noise); a larger
     difference is DIFFERS (a finding with its signed size), never absorbed. A row whose value rests only on an owner
     rule (height) is DRAWING-CONFIRMED for its drawn factor (F) and names the rule for the other.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
Z = D("0")
RULE_ID = "R-T622-1"
GOVERNING = ["owner 2026-11-02 wet-area walls", "Q-48 A tile top", "Q-73 openings / reveals", "Q-55 C door head",
             "R-T547-1 (row split)", "R-T606-1 / R-T621-1 (outline geometry)", "ERS s.2 / s.3"]
ROW_TOL = D("0.010")
FINISHES_EXCLUSIVE = ("paint", "skirting")


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


def tiled_length(chain_lm, open_sides) -> Decimal:
    """chain perimeter (incl. column returns) less the named open sides."""
    per = d(chain_lm)
    acc = Z
    for o in open_sides:
        if not o.get("handle"):
            raise RuleError("an open side must be a named drawn line (handle)")
        if o.get("role") == "WALL":
            raise RuleError("closed across an open side: a side with no wall is not a wall face")
        acc += d(o["lm"])
    if acc >= per:
        raise RuleError("open sides exceed the chain")
    return per - acc


def room_net(*, faces: list[dict], H, openings: list[dict]) -> dict:
    """faces: [{'id', 'lm', 'finishes': [...], 'h_wall': optional, 'h_from': optional, 'cap': optional}]; returns
    gross / doors / windows / net / held items. Each face is tiled over [h_from, min(h_wall, H)]."""
    H = d(H)
    if H <= 0 or H > 8:
        raise RuleError(f"tile top {H} refused (m expected)")
    gross, held = Z, []
    for f in faces:
        fin = set(f.get("finishes", ["tile"]))
        if "tile" in fin and fin & set(FINISHES_EXCLUSIVE):
            raise RuleError(f"face {f['id']}: tile and {sorted(fin & set(FINISHES_EXCLUSIVE))} on one face refused")
        L = d(f["lm"])
        if L <= 0 or L > 500:
            raise RuleError(f"face {f['id']}: length {L} refused (m expected)")
        top = min(H, d(f["h_wall"])) if f.get("h_wall") is not None else H
        base = d(f.get("h_from", 0))
        if base < 0 or base >= top:
            raise RuleError(f"face {f['id']}: band [{base}, {top}] empty or invalid")
        gross += L * (top - base)
        if f.get("cap") is not None:
            held.append({"id": f"{f['id']}.cap", "lm": str(d(f["cap"])), "state": "HELD",
                         "why": "cap finish not printed (R-T622-1 step 3); never 0"})
    doors = sum((opening_part(o, H) for o in openings if o["kind"] in ("door", "arch", "doorway")), Z)
    wins = sum((opening_part(o, H) for o in openings if o["kind"] == "window"), Z)
    return {"gross": gross, "doors": doors, "windows": wins, "net": gross - doors - wins, "held": held}


def evidence(own, stated) -> tuple[str, Decimal]:
    """(status, own - stated) for one row."""
    diff = d(own) - d(stated)
    return ("DRAWING-CONFIRMED" if abs(diff) < ROW_TOL else "DIFFERS"), diff
