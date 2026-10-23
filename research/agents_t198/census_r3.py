"""T-198: opening census revision and the downstream deltas it causes (any villa; pure functions, no drawing access).

Three operations, each refusing what it cannot establish:

1. ``redatum``: a sill / head written in a derived list is a notation, not a number, until it is bound to a sheet's datum.
   It is reduced to a height ABOVE THE FINISHED FLOOR (FFL) from either an absolute LEVEL (read from the sheet's level
   marker) or a CHAIN of printed parts from a stated chain base. A value with no datum is refused, never guessed.
2. ``consequences``: one opening -> its separate BOQ consequences, each in its own unit and with a WORKFLOW_CONTROLS s.5
   status (build before deduct, standard s.3): opening m2, masonry deduction (only when masonry is built in the host line
   AND the opening lies inside the measured gross run), per-face finish deductions, reveal m.l (2 jambs + head, + sill for
   a window), reveal depth (the wall thickness only when frameless), threshold or sill m.l, the head soffit (width x wall
   thickness, wherever a member spans the opening), the lintel length (width + 2 bearings, only when a lintel is bound)
   and, for an opening OUTSIDE the measured run, the masonry above its head that no run carries (scope gap, never netted).
   A height that is not printed makes every height-dependent line HELD: value None, never 0.
3. ``wall_delta``: a wall's net masonry before and after an opening is added to the list, with mathematical bounds
   (gross less established deductions, and less each held opening's width x the clear height) that are never a quantity.

Units: metres. A width or height above 20 is refused as probably millimetres (the census is in metres).
Statuses: DRAWING-CONFIRMED, ASSUMED — OWNER-APPROVED, HELD, UNKNOWN, plus NOT_APPLICABLE for a consequence that does
not physically exist (it is not a zero quantity: the line is simply not built)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

DC = "DRAWING-CONFIRMED"
AOA = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
NA = "NOT_APPLICABLE"
S5 = (DC, AOA, HELD, UNKNOWN)

HOSTS = ("BLOCK", "RC", "GLAZED", "NONE")
KINDS = ("WINDOW", "DOOR", "PASSAGE", "ARCH", "LIFT", "GATE", "OPENING")
MAX_M = 20.0


def _m(value, what):
    if value is None:
        return None
    v = float(value)
    if v < 0:
        raise ValueError(f"{what}: negative ({v})")
    if v > MAX_M:
        raise ValueError(f"{what}: {v} > {MAX_M} looks like millimetres; the census is in metres")
    return v


# ---------------------------------------------------------------------------------------------------------- datum ---
def redatum(*, ffl_m, sill_level_m=None, head_level_m=None, chain_base_m=None, chain_parts_m=None):
    """Return (sill_above_ffl, head_above_ffl, basis).

    Either absolute levels (``sill_level_m`` / ``head_level_m``, read from the sheet's level marker) or a printed chain
    (``chain_base_m`` = the level the chain starts from, ``chain_parts_m`` = [to sill, sill to head]). Both bases at once
    must agree within 5 mm, else ValueError (two notations of one height that disagree are a conflict to report)."""
    if ffl_m is None:
        raise ValueError("FFL datum missing: a height above the floor needs the floor level of the room")
    out = []
    if sill_level_m is not None or head_level_m is not None:
        if sill_level_m is None or head_level_m is None:
            raise ValueError("absolute levels need both the sill and the head level")
        out.append((sill_level_m - ffl_m, head_level_m - ffl_m, "LEVEL"))
    if chain_parts_m is not None:
        if chain_base_m is None:
            raise ValueError("a chain part without its chain base is a notation without a datum (refused)")
        if len(chain_parts_m) != 2:
            raise ValueError("chain_parts_m = [base to sill, sill to head]")
        sill = chain_base_m + chain_parts_m[0]
        out.append((sill - ffl_m, sill + chain_parts_m[1] - ffl_m, "CHAIN"))
    if not out:
        raise ValueError("no level and no chain: nothing to re-datum")
    if len(out) == 2 and (abs(out[0][0] - out[1][0]) > 0.005 or abs(out[0][1] - out[1][1]) > 0.005):
        raise ValueError(f"level and chain disagree: {out[0][:2]} vs {out[1][:2]}")
    s, h, b = out[0]
    if s < -0.005 or h <= s:
        raise ValueError(f"sill {s:.3f} / head {h:.3f} above FFL are not physical")
    return round(max(s, 0.0), 3), round(h, 3), "+".join(x[2] for x in out)


# ------------------------------------------------------------------------------------------------------- opening ---
@dataclass(frozen=True)
class Opening:
    oid: str
    kind: str
    width_m: float | None
    height_m: float | None              # clear opening height (sill to head); None = not printed (HELD)
    host: str                           # BLOCK / RC / GLAZED / NONE: what is physically built in the line
    in_gross: bool                      # the opening lies inside the measured gross run of its host wall
    wall_t_m: float | None
    width_status: str = DC
    height_status: str = DC             # status of height_m when given (DC printed, AOA owner fallback)
    frameless: bool = True              # no frame set in the wall: reveal depth = wall thickness
    faces: tuple = ("INTERNAL", "INTERNAL")
    spanned: bool = True                # a head member (lintel, beam, masonry over a lintel) spans the opening
    lintel_bearing_m: float | None = None   # bearing each side when a lintel is bound; None = no lintel bound
    lintel_status: str = HELD
    clear_height_m: float | None = None     # storey clear height under the member above (for bounds / scope gaps)
    lintel_depth_m: float | None = None     # lintel depth (for the masonry above an out-of-run opening)
    on_plan: bool = True
    edge: str | None = None             # THRESHOLD / SILL / None (no floor edge: e.g. a passage mouth at one level)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"{self.oid}: unknown kind {self.kind}")
        if self.host not in HOSTS:
            raise ValueError(f"{self.oid}: unknown host {self.host}")
        for st in (self.width_status, self.height_status, self.lintel_status):
            if st not in S5:
                raise ValueError(f"{self.oid}: status {st!r} is not a WORKFLOW_CONTROLS s.5 status")
        for k in ("width_m", "height_m", "wall_t_m", "lintel_bearing_m", "clear_height_m", "lintel_depth_m"):
            _m(getattr(self, k), f"{self.oid} {k}")
        if self.height_m is not None and self.clear_height_m is not None and self.height_m > self.clear_height_m + 1e-9:
            raise ValueError(f"{self.oid}: head above the member soffit ({self.height_m} > {self.clear_height_m})")


def _worst(*sts):
    order = [NA, DC, AOA, HELD, UNKNOWN]
    real = [s for s in sts if s != NA]
    return max(real, key=order.index) if real else NA


def consequences(op: Opening) -> dict:
    """Every BOQ consequence of one opening: {line: (value or None, status)}. Never 0 for an unknown."""
    if not op.on_plan:
        # drawn on an elevation only: reported for the designer, never measured (UP-OPEN-CONSIST-001 proposal)
        return {"REPORT": ("ELEVATION_ONLY", UNKNOWN)}
    w, h, t = op.width_m, op.height_m, op.wall_t_m
    hs = op.height_status if h is not None else HELD
    ws = op.width_status if w is not None else HELD
    known = w is not None and h is not None
    area = round(w * h, 3) if known else None
    area_st = _worst(ws, hs) if known else HELD
    out = {"OPENING_M2": (area, area_st)}
    # masonry deduction: build before deduct
    if op.host != "BLOCK":
        out["BLOCK_DEDUCTION_M2"] = (None, NA)
    elif not op.in_gross:
        out["BLOCK_DEDUCTION_M2"] = (None, NA)          # already outside the measured run: deducting again = double
    else:
        out["BLOCK_DEDUCTION_M2"] = (area, area_st)
    # finishes per face (a glazed line has no wall face to deduct from)
    for i, fam in enumerate(op.faces):
        if op.host in ("GLAZED", "NONE") or fam is None:
            out[f"FINISH_FACE_{i + 1}_M2"] = (None, NA)
        else:
            out[f"FINISH_FACE_{i + 1}_M2:{fam}"] = (area, area_st)
    # reveals: 2 jambs + head (+ sill for a window); depth = wall thickness only when frameless
    if op.host == "NONE" and not op.spanned:
        out["REVEAL_LM"] = (None, NA)
    elif known:
        ml = 2 * h + w + (w if op.kind == "WINDOW" else 0.0)
        out["REVEAL_LM"] = (round(ml, 3), area_st)
    else:
        out["REVEAL_LM"] = (None, HELD)
    out["REVEAL_DEPTH_M"] = ((t, DC) if (op.frameless and t is not None) else (None, HELD))
    # head soffit: width x wall thickness, wherever something spans the opening (independent of the head height)
    if op.spanned and w is not None and t is not None:
        out["HEAD_SOFFIT_M2"] = (round(w * t, 3), ws)
    else:
        out["HEAD_SOFFIT_M2"] = (None, NA if not op.spanned else HELD)
    # floor edge
    if op.edge in ("THRESHOLD", "SILL"):
        out[f"{op.edge}_LM"] = ((w, ws) if w is not None else (None, HELD))
    else:
        out["EDGE_LM"] = (None, UNKNOWN if op.edge == "UNKNOWN" else NA)
    # lintel: only when one is bound (schedule row + support), else HELD / NA
    if op.lintel_bearing_m is not None and w is not None:
        out["LINTEL_LENGTH_M"] = (round(w + 2 * op.lintel_bearing_m, 3), op.lintel_status)
    else:
        out["LINTEL_LENGTH_M"] = (None, NA if not op.spanned else HELD)
    # masonry above the head of an opening that lies OUTSIDE the measured run: built, but in no run (scope gap)
    if op.host == "BLOCK" and not op.in_gross and op.spanned:
        if w is None or op.clear_height_m is None:
            out["MASONRY_ABOVE_HEAD_M2"] = (None, UNKNOWN)
        elif h is None:
            out["MASONRY_ABOVE_HEAD_M2"] = (None, HELD)
        else:
            d = op.lintel_depth_m or 0.0
            out["MASONRY_ABOVE_HEAD_M2"] = (round(w * max(op.clear_height_m - h - d, 0.0), 3),
                                            _worst(area_st, op.lintel_status if op.lintel_depth_m else DC))
    return out


def masonry_above_head_bounds(op: Opening):
    """Mathematical limits (lo, hi) of the masonry above an out-of-run opening while its head is HELD: the head can
    lie anywhere from the floor up to the lintel underside. Never a quantity."""
    if op.width_m is None or op.clear_height_m is None:
        return None
    d = op.lintel_depth_m or 0.0
    return 0.0, round(op.width_m * max(op.clear_height_m - d, 0.0), 3)


# ---------------------------------------------------------------------------------------------------------- wall ---
def wall_net(gross_m2: float, openings: Iterable[Opening]):
    """(net or None, status, bounds) of one wall's masonry; HELD never becomes 0."""
    ops = [o for o in openings if o.host == "BLOCK" and o.in_gross and o.on_plan]
    seen = set()
    for o in ops:
        if o.oid in seen:
            raise ValueError(f"{o.oid} twice on one wall")
        seen.add(o.oid)
    est, held, sts = 0.0, [], []
    for o in ops:
        v, st = consequences(o)["BLOCK_DEDUCTION_M2"]
        if v is None:
            held.append(o)
        else:
            est += v
            sts.append(st)
    if est > gross_m2 + 1e-9:
        raise ValueError(f"deductions {est:.3f} exceed the gross {gross_m2:.3f}")
    hi = round(gross_m2 - est, 3)
    if held:
        lo = hi
        for o in held:
            if o.width_m is None or o.clear_height_m is None:
                return None, HELD, (None, hi)
            lo -= o.width_m * o.clear_height_m
        return None, HELD, (round(max(lo, 0.0), 3), hi)
    return hi, _worst(DC, *sts), (hi, hi)


def wall_delta(gross_m2: float, before: Iterable[Opening], added: Opening):
    """Net masonry of one wall before and after ``added`` joins its opening list."""
    before = list(before)
    if any(o.oid == added.oid for o in before):
        raise ValueError(f"{added.oid} is already in the list")
    b = wall_net(gross_m2, before)
    a = wall_net(gross_m2, before + [added])
    delta = round(a[0] - b[0], 3) if (a[0] is not None and b[0] is not None) else None
    return {"before": b, "after": a, "delta_m2": delta}


# -------------------------------------------------------------------------------------------------------- census ---
@dataclass
class Revision:
    additions: list = field(default_factory=list)      # dict rows in the census columns
    redatums: dict = field(default_factory=dict)        # id -> {column: new value}
    pcs: dict = field(default_factory=dict)             # id -> (PCS_STATUS, reason)
    notes: dict = field(default_factory=dict)           # id -> R3_CHANGE text


def revise(rows: list, rev: Revision, extra_cols: tuple) -> list:
    """A new census version: the old rows copied (never edited in the old file), corrected cells set, additions appended.
    Refuses a duplicate id, a correction of an unknown id or of a column that does not exist."""
    ids = [r["ID"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate id in the census")
    cols = list(rows[0].keys()) if rows else []
    out = []
    for r in rows:
        n = {c: r[c] for c in cols}
        for c in extra_cols:
            n[c] = ""
        for c, v in rev.redatums.get(r["ID"], {}).items():
            if c not in n:
                raise ValueError(f"unknown column {c}")
            n[c] = v
        if r["ID"] in rev.pcs:
            n["PCS_STATUS"], n["PCS_REASON"] = rev.pcs[r["ID"]]
        n["R3_CHANGE"] = rev.notes.get(r["ID"], "")
        out.append(n)
    for oid in list(rev.redatums) + list(rev.pcs) + list(rev.notes):
        if oid not in ids and oid not in {a["ID"] for a in rev.additions}:
            raise ValueError(f"{oid}: not in the census")
    for a in rev.additions:
        if a["ID"] in ids:
            raise ValueError(f"{a['ID']} is already in the census")
        n = {c: a.get(c, "") for c in cols + list(extra_cols)}
        if a["ID"] in rev.pcs:
            n["PCS_STATUS"], n["PCS_REASON"] = rev.pcs[a["ID"]]
        n["R3_CHANGE"] = rev.notes.get(a["ID"], n.get("R3_CHANGE", ""))
        out.append(n)
        ids.append(a["ID"])
    return out


def pcs_summary(rows: list, boq_line: str):
    """(settled count, held ids) for one supply line: a row counts 1 only when its PCS_STATUS is SETTLED."""
    settled, held = 0, []
    for r in rows:
        if r.get("BOQ_LINE") != boq_line:
            continue
        if r.get("PCS_STATUS") == "SETTLED":
            settled += 1
        else:
            held.append(r["ID"])
    return settled, held


def with_height(op: Opening, h, status=DC) -> Opening:
    return replace(op, height_m=h, height_status=status)
