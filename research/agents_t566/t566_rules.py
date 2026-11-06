"""T-566 rules (research, unwired, stdlib only): column MARK REGISTRATION per position from the drawings alone, and the
naming of a beam family's UNTRACED residual per mark.

R-T566-1 (mark from printed labels at the position). A column position (one neck outline on the foundation sheets) takes
    its mark ONLY from the column labels printed at that position on the sheets that print labels (here FP, CAP, GBP),
    each label bound to its outline by a minimum-total-distance one-to-one assignment inside its own sheet. All present
    labels equal -> REGISTERED (support k / n sheets). Labels differ -> CONFLICT: every candidate mark kept with the sheets
    that print it; never resolved by majority, by the schedule, by a section match or by an estimate. No label -> HELD.
    A mark obtained from a label COUNT (how many 'C3' a sheet prints) is refused; a freelancer row or count is never
    evidence (Refused).
R-T566-2 (sections are evidence about a mark, never a resolution). For every candidate mark the schedule band of each
    storey is compared with the outline drawn at that storey and with a size text printed at the position: AGREE /
    DIFFERS / NO_BAND (an outline is drawn where the mark has no band) / NOT_DRAWN. The vector is reported beside a
    CONFLICT for the designer; it does not change the registration class.
R-T566-3 (continuity). A storey member over the position (SOLID outline on that storey's roof-slab plan within the
    position tolerance) carries the position's mark: the slab plans print no column labels, so a GF / 1F / 2F member is
    registered by continuity from the foundation sheets; a section change between storeys is read from the schedule
    band of that mark, never as a different mark. A candidate whose schedule has no band for a storey on which a member
    is drawn is marked NO_BAND for that storey (continuity break, evidence only).
R-T566-4 (bound of a CONFLICT). The section area of a member on a CONFLICT position is bounded by the candidate marks'
    schedule areas and the drawn area at that storey: [min, max] m2, m3 at a stated height; never one end.
R-T566-5 (an UNTRACED beam residual is named per mark, by row-to-run evidence, in m3 that re-add exactly):
    DRAWING_PRECISION  his row and the drawn line differ by less than PRECISION_M per row: ENGINE_RIGHT (drawn);
    COUNT              his lengths equal the drawn face-to-face lengths run by run and one row of his has no drawn run
                       of that mark: the whole mark residual is the extra row (re-classes the length split);
    MARK_BOUNDARY      his row continues collinearly through a support onto a piece the drawing labels with another
                       mark (bounded by that piece's length; the piece is billed once, under its own mark);
    BEYOND_EXTENT      his length exceeds the drawn outer-face extent of the mark and no drawn collinear beam continues it;
    UNRESOLVED         none of the above can be shown (named, never 0).
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

Q6 = Decimal("0.000001")
PRECISION_M = Decimal("0.05")          # his lengths are printed to 0.05 m (and 0.01 m): a per-row difference below this
LABEL_KINDS = ("PRINTED_LABEL",)       # the only evidence kind a registration accepts
CAUSES = ("DRAWING_PRECISION", "COUNT", "MARK_BOUNDARY", "BEYOND_EXTENT", "UNRESOLVED")


class Refused(ValueError):
    pass


def d6(x) -> Decimal:
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_EVEN)


def norm_mark(text: str, prefixes=("C",)) -> str:
    """'C3/F3' -> 'C3', 'CN/FN' -> 'CN', 'C/F' -> 'C'; anything that is not a column label is refused. `prefixes`
    are the column-label letters of the drawing set (this villa: 'C'; another set may print e.g. 'K')."""
    t = text.strip().upper()
    head = t.split("/")[0]
    for p in prefixes:
        rest = head[len(p):]
        if head.startswith(p) and (rest in ("", "N") or rest.isdigit()):
            return head
    raise Refused(f"not a column label: {text!r}")


def register_position(labels: dict, prefixes=("C",)) -> dict:
    """R-T566-1. labels = {sheet: {"text": ..., "kind": "PRINTED_LABEL"} or None}."""
    if not labels:
        raise Refused("no label sheets given")
    marks = {}
    for sheet, lab in labels.items():
        if lab is None:
            continue
        if lab.get("kind") not in LABEL_KINDS:
            raise Refused(f"{sheet}: evidence kind {lab.get('kind')!r} is not a printed label at the position")
        marks.setdefault(norm_mark(lab["text"], prefixes), []).append(sheet)
    n = len(labels)
    k = sum(len(v) for v in marks.values())
    if not marks:
        return {"class": "HELD", "mark": None, "candidates": {}, "support": f"0/{n}"}
    if len(marks) == 1:
        (m, sheets), = marks.items()
        return {"class": "REGISTERED", "mark": m, "candidates": {m: sorted(sheets)}, "support": f"{k}/{n}"}
    return {"class": "CONFLICT", "mark": None, "candidates": {m: sorted(s) for m, s in sorted(marks.items())},
            "support": f"{k}/{n}"}


def register_by_label_count(*_a, **_k):
    """A mark taken from how many labels of a kind a sheet prints is not a registration (adverse case)."""
    raise Refused("a mark from a label count alone is refused: register each position from the labels printed there")


def register_from_freelancer(*_a, **_k):
    raise Refused("a freelancer row or count is never evidence for a drawing registration")


def _sec(x):
    if x is None:
        return None
    a, b = (Decimal(str(v)) for v in x)
    if a <= 0 or b <= 0:
        raise Refused(f"section must be positive: {x}")
    return tuple(sorted((a, b)))


def section_vector(candidate_bands: dict, drawn: dict, unit: str = "mm") -> dict:
    """R-T566-2 / -3. candidate_bands = {mark: {storey: (W, D) cm or None}}; drawn = {storey: (W, D) in `unit` or None}.
    Returns {mark: {storey: AGREE / DIFFERS / NO_BAND / NOT_DRAWN}}."""
    f = {"mm": Decimal("0.1"), "cm": Decimal(1), "m": Decimal(100)}
    if unit not in f:
        raise Refused(f"unknown unit {unit!r}")
    out = {}
    for m, bands in candidate_bands.items():
        row = {}
        for st, dr in drawn.items():
            band = _sec(bands.get(st))
            d = _sec(dr)
            if d is not None:
                d = tuple(v * f[unit] for v in d)
            if d is None:
                row[st] = "NOT_DRAWN"
            elif band is None:
                row[st] = "NO_BAND"
            else:
                row[st] = "AGREE" if band == d else "DIFFERS"
        out[m] = row
    return out


def continuity(position_mark: str | None, members: dict) -> dict:
    """R-T566-3: each storey member over the position carries the position's mark (or the CONFLICT candidates)."""
    return {st: position_mark for st, mem in members.items() if mem is not None}


def conflict_area_bound(candidate_bands: dict, storey: str, drawn_m: tuple | None, height_m=None) -> dict:
    """R-T566-4: [min, max] section area (m2) over the candidates' schedule bands and the drawn section; m3 at
    height_m when given. A candidate without a band at that storey is reported, never taken as 0."""
    areas, no_band = [], []
    for m, bands in sorted(candidate_bands.items()):
        b = _sec(bands.get(storey))
        if b is None:
            no_band.append(m)
            continue
        areas.append(b[0] * b[1] / Decimal(10000))
    if drawn_m is not None:
        s = _sec(drawn_m)
        areas.append(s[0] * s[1])
    if not areas:
        return {"low_m2": None, "high_m2": None, "no_band": no_band}
    lo, hi = min(areas), max(areas)
    out = {"low_m2": d6(lo), "high_m2": d6(hi), "no_band": no_band}
    if height_m is not None:
        h = Decimal(str(height_m))
        if h <= 0:
            raise Refused("height must be positive")
        out.update({"low_m3": d6(lo * h), "high_m3": d6(hi * h)})
    return out


def name_untraced(mark: str, untraced_m3, cause: str, verdict: str, evidence: str, bound_m3=None) -> dict:
    """R-T566-5 record; UNRESOLVED keeps its value (never 0)."""
    if cause not in CAUSES:
        raise Refused(f"unknown cause {cause!r}")
    u = d6(untraced_m3)
    if cause == "UNRESOLVED" and u == 0:
        raise Refused("an UNRESOLVED term is named with its value, never closed as 0")
    if not evidence:
        raise Refused("a named cause needs its drawing evidence")
    return {"mark": mark, "m3": str(u), "cause": cause, "verdict": verdict, "evidence": evidence,
            "bound_m3": None if bound_m3 is None else [str(d6(b)) for b in bound_m3]}


def precision_class(his_len_m, drawn_len_m) -> bool:
    """True when a row of his and the drawn line differ by less than PRECISION_M (per row)."""
    a, b = Decimal(str(his_len_m)), Decimal(str(drawn_len_m))
    if a <= 0 or b <= 0:
        raise Refused("lengths must be positive metres")
    if a > 100 or b > 100:
        raise Refused("length looks like millimetres; give metres")
    return abs(a - b) < PRECISION_M


def close_named(total_m3, named: list) -> dict:
    """The named terms re-add exactly to the residual they split (6 dp), else refused."""
    t = d6(total_m3)
    s = sum((Decimal(r["m3"]) for r in named), Decimal(0))
    if s != t:
        raise Refused(f"named terms {s} do not re-add to {t}")
    by = {}
    for r in named:
        by[r["cause"]] = str(d6(Decimal(by.get(r["cause"], "0")) + Decimal(r["m3"])))
    return {"total_m3": str(t), "by_cause": by}
