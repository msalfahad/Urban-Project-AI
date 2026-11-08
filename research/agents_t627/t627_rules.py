"""R-T627-1 OPENING AREA EVIDENCE PER OPENING (every villa; research rule, unwired; T-627).

Physical element: the STRUCTURAL OPENING of each window / aluminium door, width x height between the masonry jambs and
from the sill (or the floor the door opens from) to the head. Opening area is a distinct measure from the aluminium
assembly (frame) area and from the net glass area (owner 2026-10-24 23:53 with Q-76 A); this rule measures only the
opening area and refuses the other two.

  1. WIDTH. A printed width bound to the opening governs; else the masonry jamb-to-jamb distance on the plan (a window's
     two jamb cap lines; a door's wall-face line ends, which must agree on BOTH faces). A door block's frame width is
     never the opening width.
  2. HEIGHT. A printed height bound to the opening governs. Where several printed values disagree, the LATER-DATED
     sheet governs (RFI re-review 2026-11-02 B-S18); equal dates that disagree are a CONFLICT (HELD). Where nothing is
     printed, the drawn outline of a VECTOR view establishes it (UP-OPEN-GEOM-001 as used by T-201 / T-207) only when
     bound to the plan opening (left edge within 15 mm of the view's voted offset AND outline width = masonry width
     within 20 mm); an outline that matches only a door block's frame, or that another opening of the same wall
     claims, is a CANDIDATE, never a binding. A door's drawn height is its head minus the printed floor level it opens
     from; two views of one door must agree on the head level, else CONFLICT. Drawn readings are taken to the cm (the
     set prints levels to the cm). An owner fallback (Q-55 C door 2.20) stays the basis wherever (2) establishes nothing,
     labelled ASSUMED - OWNER-APPROVED.
  3. AREA = width x height (rectangle; an arched head per Q-32 A to the apex; a curved-on-plan window per Q-76 A).
  4. ROW SPLIT. Reference (w_r x h_r) minus own (w_o x h_o) splits exactly into a WIDTH term (w_r - w_o) x h_r and a
     HEIGHT term w_o x (h_r - h_o); an opening the reference omits is one term -w_o x h_o. A statement row is
     DRAWING_CONFIRMED when its delta equals the term computed from the own reading (|diff| <= 0.001 m2), else DIFFERS
     (a finding, never absorbed). HELD stays HELD with what it waits on; never 0.
  5. CLASS of a height term: ENGINE_RIGHT when the engine's height equals a printed or drawing-established height;
     RULE_DIFFERENCE when the engine's height rests on an owner fallback that (2) could not confirm.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

D = Decimal
Z = D("0")
RULE_ID = "R-T627-1"
GOVERNING = ["Q-32 A (opening area)", "Q-76 A (curved window 3.29 x 3.00)", "Q-55 C (door 2.20 fallback)",
             "Q-39 C (outer arc width)", "UP-OPEN-SCHED-001", "UP-DOOR-AREA-001", "UP-ELEV-SCHED-001",
             "UP-OPEN-GEOM-001 (T-201 vector geometry)", "RFI re-review 2026-11-02 B-S18 (later-dated sheet governs)",
             "R-T568-1 (row split)", "ERS s.2 / s.3"]
Q6, Q2 = D("0.000001"), D("0.01")
TOL_ROW = D("0.001")
TOL_BIND_W, TOL_BIND_EDGE = D("0.020"), D("0.015")
MEASURES_REFUSED = ("ASSEMBLY", "FRAME", "GLASS", "NET_GLASS")
PRINTED_KINDS = ("SCHEDULE", "ELEVATION", "SECTION", "PLAN", "DETAIL")


class RuleError(ValueError):
    pass


def d(x) -> Decimal:
    return D(repr(x)) if isinstance(x, float) else D(str(x))


def opening_area(width, height, measure: str = "OPENING") -> Decimal:
    if measure != "OPENING":
        raise RuleError(f"{measure} area is not opening area (R-T627-1 (3)); keep it as its own measure")
    w, h = d(width), d(height)
    if w <= 0 or h <= 0:
        raise RuleError("width and height must be positive (missing is HELD, never 0)")
    if w > 20 or h > 20:
        raise RuleError("a dimension above 20 m: millimetres given as metres?")
    return (w * h).quantize(Q6)


def governing(readings: list[dict]) -> dict:
    """choose the governing value of ONE dimension of ONE opening.

    reading: {"value": m, "kind": SCHEDULE/ELEVATION/SECTION/PLAN/DETAIL (printed) or GEOMETRY or OWNER_FALLBACK,
              "sheet": str, "date": 'YYYY-MM-DD' (printed), "bound": bool (geometry), "frame_only": bool}
    returns {"value", "basis", "sheet", "status"} where status is PRINTED / DRAWING_CONFIRMED / ASSUMED_OWNER_APPROVED /
    CONFLICT / HELD."""
    if not readings:
        return {"value": None, "basis": None, "sheet": None, "status": "HELD"}
    for r in readings:
        if r["kind"] not in PRINTED_KINDS + ("GEOMETRY", "OWNER_FALLBACK"):
            raise RuleError(f"unknown reading kind {r['kind']}")
        if r["kind"] in MEASURES_REFUSED:
            raise RuleError("assembly / glass is not an opening reading")
        if d(r["value"]) <= 0:
            raise RuleError("a reading of 0 or less is no reading")
    pr = [r for r in readings if r["kind"] in PRINTED_KINDS]
    if pr:
        vals = {d(r["value"]) for r in pr}
        if len(vals) == 1:
            r = max(pr, key=lambda r: date.fromisoformat(r["date"]))
            return {"value": d(r["value"]), "basis": r["kind"], "sheet": r["sheet"], "status": "PRINTED"}
        last = max(date.fromisoformat(r["date"]) for r in pr)
        top = [r for r in pr if date.fromisoformat(r["date"]) == last]
        if len({d(r["value"]) for r in top}) > 1:
            return {"value": None, "basis": "PRINTED", "sheet": " / ".join(r["sheet"] for r in top),
                    "status": "CONFLICT"}
        r = top[0]
        return {"value": d(r["value"]), "basis": r["kind"] + " (later-dated sheet governs)", "sheet": r["sheet"],
                "status": "PRINTED"}
    geo = [r for r in readings if r["kind"] == "GEOMETRY"]
    bound = [r for r in geo if r.get("bound") and not r.get("frame_only")]
    if bound:
        vals = {d(r["value"]).quantize(Q2) for r in bound}
        if len(vals) > 1:
            return {"value": None, "basis": "GEOMETRY", "sheet": " / ".join(r["sheet"] for r in bound),
                    "status": "CONFLICT"}
        return {"value": vals.pop(), "basis": "GEOMETRY", "sheet": " / ".join(sorted({r["sheet"] for r in bound})),
                "status": "DRAWING_CONFIRMED"}
    fb = [r for r in readings if r["kind"] == "OWNER_FALLBACK"]
    if fb:
        return {"value": d(fb[0]["value"]), "basis": "OWNER_FALLBACK", "sheet": fb[0]["sheet"],
                "status": "ASSUMED_OWNER_APPROVED"}
    return {"value": None, "basis": "GEOMETRY (candidates only)", "sheet": None, "status": "HELD"}


def door_height_from_views(views: list[dict], floor_levels: list) -> dict:
    """views: [{"sheet", "head_level", "bottom_level", "bound": bool, "frame_only": bool}]; floor_levels: printed plan
    levels on the two sides of the door. Head levels of the bound views must agree (to the cm); the height is the head
    minus the printed floor level the door's bound outline stands on (or, if none equals a printed level, the highest
    printed level beside the door: the door opens from its higher floor)."""
    bv = [v for v in views if v.get("bound") and not v.get("frame_only")]
    if not bv:
        return {"value": None, "status": "HELD", "why": "no bound view (frame-only or none)"}
    heads = {d(v["head_level"]).quantize(Q2) for v in bv}
    if len(heads) > 1:
        return {"value": None, "status": "CONFLICT", "why": f"views disagree on the head: {sorted(map(str, heads))}"}
    if not floor_levels:
        return {"value": None, "status": "HELD", "why": "no printed floor level beside the door"}
    lv = sorted({d(x) for x in floor_levels})
    stand = [x for x in lv if any(d(v["bottom_level"]).quantize(Q2) == x for v in bv)]
    ffl = stand[-1] if stand else lv[-1]
    head = heads.pop()
    if head <= ffl:
        raise RuleError("head at or below the floor")
    return {"value": head - ffl, "status": "DRAWING_CONFIRMED", "head": head, "ffl": ffl,
            "why": "head of the bound view(s) minus the printed floor level " + str(ffl)}


def split_terms(own_w, own_h, ref_w=None, ref_h=None) -> list[dict]:
    """reference - own, exactly: [WIDTH, HEIGHT] or [OMITTED] when the reference has no unit."""
    ow, oh = d(own_w), d(own_h)
    if ref_w is None:
        return [{"term": "OMITTED", "qty": (-(ow * oh)).quantize(Q6)}]
    rw, rh = d(ref_w), d(ref_h)
    t = [{"term": "WIDTH", "qty": ((rw - ow) * rh).quantize(Q6)}, {"term": "HEIGHT", "qty": (ow * (rh - oh)).quantize(Q6)}]
    if sum(x["qty"] for x in t) != (rw * rh - ow * oh).quantize(Q6):
        raise RuleError("split does not re-add")
    return t


def judge_row(delta, expected) -> tuple[str, Decimal]:
    diff = d(expected) - d(delta)
    return ("DRAWING_CONFIRMED" if diff.copy_abs() <= TOL_ROW else "DIFFERS"), diff


def split_exact(rows: list[dict], total) -> dict:
    tot = sum((d(r["delta"]) for r in rows), Z)
    if tot != d(total):
        raise RuleError(f"rows re-add to {tot}, statement says {total}")
    by_cls, by_ev = {}, {}
    for r in rows:
        if r["class"] == "HELD" and d(r["delta"]) == 0:
            raise RuleError("HELD is never 0")
        by_cls[r["class"]] = by_cls.get(r["class"], Z) + d(r["delta"])
        by_ev[r["evidence"]] = by_ev.get(r["evidence"], Z) + d(r["delta"])
    if sum(by_cls.values(), Z) != tot or sum(by_ev.values(), Z) != tot:
        raise RuleError("class / evidence split does not re-add")
    return {"total": str(tot), "by_class": {k: str(v) for k, v in sorted(by_cls.items())},
            "by_evidence": {k: str(v) for k, v in sorted(by_ev.items())}}
