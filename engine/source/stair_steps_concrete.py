"""STAIR CONCRETE V1 - the concrete of a stair as SEPARATE lines: steps, sloping waist slab, intermediate landings, stair
beams; floor landings named as part of the floor slab; formwork, reinforcement, marble and handrails named as later
items. A NEW method piece: it imports engine.source.stair_geometry (frozen, read only) and edits nothing; no released
method calls it.

Input is a stair CENSUS: what the drawings print and draw, each value with its source (sheet / view / printed text). The
piece never fills a missing value. Lengths come in the census unit ("mm" or "m"); every output is in metres.

Rules (owner answers and the Urban rule store; cited per line):
  Q-19   one step = 1/2 x riser x tread x width; steps concrete = one step x number of steps (straight steps).
  Q-20 C every stair detail is read first; step concrete, waist, intermediate and floor landings, stair beams and
         supports are separate lines; a dimension that is not printed holds only its own line, never dropped, never 0;
         no slab or landing concrete counted twice; typical values are sanity checks only.
  Q-46 A the riser count comes from the SECTION that cuts the stair; plan counts are checks only and every difference is
         listed for the architect (RFI).
  Q-47 A a slab tag ("T 16") printed inside a stair panel is the waist and landing thickness of that panel; waist volume
         = width x sloped length x thickness, sloped length = hypot(goings x tread, risers x riser) of the flight.
  UP-STAIR-002 geometry from the drawing, never from typical values.  UP-STAIR-009 riser = rise / counted risers; the
         0.155 - 0.165 m range is a diagnostic only.  UP-QTY-STATUS-001 statuses; missing never becomes 0.
  Open owner questions that HOLD lines here (never guessed):
  Q-50   a stair that no section cuts: may the plan count be used?          -> RISERS_NOT_COUNTED_ON_A_SECTION
  Q-51   turning (winder) and tapered steps: how is their concrete measured? -> WINDER_STEP_RULE_NOT_ANSWERED

Census shape (all keys optional unless marked *; a value is {"value": v, "source": "..."} or a bare number):
  {"id"*, "unit": "mm" | "m",
   "runs": [ {"id"*, "bottom_level", "top_level"          printed levels (census unit) -> rise
              "section_risers": {"value", "source"}       risers counted on a section cutting this run (Q-46 A)
              "plan_risers": [{"value", "source"}, ...]   plan counts: checks only
              "parts": [ part, ... ] } ],                  in walking order
   "not_present": [{"id", "evidence"}],                    a stair the census looked for and the section shows absent
   "beams": [ {"id"*, "width", "depth", "length", "source"} ]}
  part = {"id"*, "kind"*: "FLIGHT" | "WINDER" | "CURVED" | "LANDING" | "FLOOR_LANDING",
          FLIGHT:  "risers"* (counted on the section, each a step, Q-19), "goings", "tread", "width",
                   "thickness": {"value", "source", "basis": "DETAIL" | "PANEL_TAG"}  (waist; Q-47 A)
          WINDER / CURVED: "risers", "plan_area" (printed / drawn outline)  -> HELD (Q-51)
          TURN_RISER: a riser inside a landing turn (a flat quarter, then a closing riser up to the landing): its
                   concrete needs the two landing levels printed  -> HELD (LANDING_LEVELS_NOT_PRINTED)
          LANDING: "length", "width", "thickness" (as above)
          FLOOR_LANDING: the floor slab line owns it (named, no volume here)}

Checks (never in a total):
  RFI_RISER_COUNT      every plan count that differs from the section count, with the riser each would give.
  RISER_SANITY         riser outside 0.155 - 0.165 m (UP-STAIR-009): diagnostic only.
  ARRIVAL_WEDGE_IN_LANDING  the step wedge of a flight's last riser lies inside the landing it arrives on (exact overlap
                       of the wedge triangle with the landing plate, x width). The Q-19 / Q-46 A / Q-47 A basis counts
                       both; the volume is shown so the owner can decide (Q-20: no double counting).

    measure(census) -> {"method", "stair", "lines", "checks", "totals"}
    plan_check_from_lines(segments, unit, pitch_m=(0.23, 0.36)) -> drawn riser-line runs (count, tread) of a plan
    arrival_wedge_overlap(riser, tread, plate_thickness) -> m2 of profile (x width = m3)

Nothing here names a project, a sheet, a layer or a handle.
"""

from __future__ import annotations

import math

from engine.source import stair_geometry as SGEO

METHOD = "STAIR_CONCRETE_V1"
RULES = ("OWNER-Q-19", "OWNER-Q-20", "OWNER-Q-46", "OWNER-Q-47", "UP-STAIR-002", "UP-STAIR-009", "UP-QTY-STATUS-001")
UNITS = {"mm": 0.001, "m": 1.0}
RISER_SANITY_M = (0.155, 0.165)          # UP-STAIR-009: a diagnostic range, never a value
THICKNESS_BASES = ("DETAIL", "PANEL_TAG")  # printed in a stair detail / section, or a slab tag inside the stair panel
LATER_ITEMS = ("FORMWORK", "REINFORCEMENT", "MARBLE_TREAD_AND_RISER", "HANDRAILS")

MEASURED = "MEASURED"
HELD = "HELD"
COUNTED_ELSEWHERE = "COUNTED_IN_FLOOR_SLAB"
NOT_PRESENT = "NOT_APPLICABLE_WITH_EVIDENCE"
LATER = "UNSUPPORTED_LATER_ITEM"

NEEDS_DRAWING = "REQUIRES_DRAWING_EVIDENCE"
NEEDS_OWNER = "REQUIRES_OWNER_DECISION"


class StairCensusError(ValueError):
    pass


def _r(v, nd=6):
    return None if v is None else round(v, nd)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _val(item):
    """(value, source) of a census value; (None, None) when absent."""
    if item is None:
        return None, None
    if isinstance(item, dict):
        v = item.get("value")
        return (v if _num(v) else None), item.get("source")
    return (item if _num(item) else None), None


def _len(item, k):
    v, src = _val(item)
    return (None if v is None else v * k), src


def _count(item):
    v, src = _val(item)
    if v is None:
        return None, src
    if int(v) != v or v < 0:
        raise StairCensusError(f"a count must be a whole number, got {v!r}")
    return int(v), src


def _line(stair, run, part, element, status, *, quantity_m3=None, reason=None, reason_class=None, rules=(),
          calc=None, sources=(), **extra):
    if status == MEASURED and not _num(quantity_m3):
        raise StairCensusError("a measured line needs a quantity")
    if status != MEASURED and quantity_m3 is not None:
        raise StairCensusError("only a measured line carries a quantity")
    ln = {"method": METHOD, "stair": stair, "run": run, "part": part, "element": element, "unit": "m3",
          "status": status, "quantity_m3": _r(quantity_m3), "reason": reason, "reason_class": reason_class,
          "rules": list(rules), "calc": calc, "sources": [s for s in sources if s]}
    ln.update(extra)
    return ln


# ====================================================================== geometry helpers
def arrival_wedge_overlap(riser, tread, plate_thickness):
    """profile area (m2) of the wedge triangle (riser x tread, under the arrival tread) that lies inside a plate of the
    given thickness whose top is the arrival level: the triangle (0, -r), (0, 0), (t, 0) cut by z >= -th."""
    if riser <= 0 or tread <= 0 or plate_thickness <= 0:
        raise StairCensusError("riser, tread and plate thickness must be positive")
    full = 0.5 * riser * tread
    if plate_thickness >= riser:
        return full
    below = riser - plate_thickness
    return full - 0.5 * below * (below * tread / riser)


def plan_check_from_lines(segments, unit, pitch_m=(0.23, 0.36), len_tol_m=0.12, min_lines=3, angle_tol=0.5):
    """drawn riser lines of a plan (segments (id, (x0, y0), (x1, y1)) in the census unit) grouped into runs by
    stair_geometry.detect_tread_runs (rotation and mirror free: it works on directions and offsets). Returns one record
    per run: count of lines, the tread as the median pitch (m), its spread, the line length (m). A CHECK only (Q-46 A):
    the number of lines is not the riser count (the arrival riser is often the slab edge, not a drawn line)."""
    k = UNITS.get(unit)
    if k is None:
        raise StairCensusError(f"unit must be one of {sorted(UNITS)}")
    segs_mm = [(sid, (a[0] * k * 1000.0, a[1] * k * 1000.0), (b[0] * k * 1000.0, b[1] * k * 1000.0))
               for sid, a, b in segments]
    runs = SGEO.detect_tread_runs(segs_mm, pitch=(pitch_m[0] * 1000.0, pitch_m[1] * 1000.0),
                                  len_tol=len_tol_m * 1000.0, min_lines=min_lines, angle_tol=angle_tol)
    out = []
    for rn in runs:
        p = sorted(rn["pitches"])
        mid = p[len(p) // 2] if len(p) % 2 else 0.5 * (p[len(p) // 2 - 1] + p[len(p) // 2])
        out.append({"lines": rn["count"], "tread_m": _r(mid / 1000.0), "pitch_spread_m": _r((p[-1] - p[0]) / 1000.0),
                    "line_length_m": _r(rn["length"] / 1000.0), "ids": rn["ids"]})
    return out


# ====================================================================== thickness (waist / landing)
def _thickness(part, k):
    t = part.get("thickness")
    if not isinstance(t, dict):
        return None, None, None
    v, src = _len(t, k)
    basis = t.get("basis")
    if v is None or v <= 0 or basis not in THICKNESS_BASES or not src:
        return None, None, None
    return v, src, basis


def _thickness_rule(basis):
    return "OWNER-Q-47" if basis == "PANEL_TAG" else "UP-STAIR-002"


# ====================================================================== one run (level to level)
def _run(stair, run, k, lines, checks):
    rid = run.get("id")
    if not rid:
        raise StairCensusError("every run needs an id")
    parts = run.get("parts") or []
    b, bsrc = _len(run.get("bottom_level"), k)
    t, tsrc = _len(run.get("top_level"), k)
    rise = None if b is None or t is None else t - b
    if rise is not None and rise <= 0:
        raise StairCensusError(f"run {rid}: the top level must be above the bottom level")
    sec, sec_src = _count(run.get("section_risers"))

    # risers per part on the section must add up to the section count, or the run is inconsistent
    counted = 0
    for p in parts:
        if p.get("kind") in ("FLIGHT", "WINDER", "CURVED", "TURN_RISER"):
            n, _ = _count(p.get("risers"))
            counted += n or 0
    hold_run = None
    if rise is None:
        hold_run = ("RISER_HEIGHT_NOT_ESTABLISHED", NEEDS_DRAWING, "the bottom or the top level is not printed")
    elif sec is None:
        hold_run = ("RISERS_NOT_COUNTED_ON_A_SECTION", NEEDS_OWNER, "no section cuts this run (owner Q-50 open)")
    elif sec != counted:
        hold_run = ("RISER_COUNT_INCONSISTENT", NEEDS_DRAWING,
                    f"the parts count {counted} risers, the section {sec}")
    riser = None if hold_run else SGEO.riser_height(rise, sec)
    rsrc = [bsrc, tsrc, sec_src]

    # checks: plan counts (RFI) and the riser sanity range
    for pc in run.get("plan_risers") or []:
        n, src = _count(pc)
        if n is not None and sec is not None and n != sec:
            checks.append({"check": "RFI_RISER_COUNT", "stair": stair, "run": rid, "section_risers": sec,
                           "plan_risers": n, "plan_source": src, "section_source": sec_src,
                           "riser_section_m": _r(riser), "riser_plan_m": _r(rise / n) if rise and n else None,
                           "rule": "OWNER-Q-46"})
    if riser is not None and not (RISER_SANITY_M[0] <= riser <= RISER_SANITY_M[1]):
        checks.append({"check": "RISER_SANITY", "stair": stair, "run": rid, "riser_m": _r(riser),
                       "range_m": list(RISER_SANITY_M), "rule": "UP-STAIR-009", "note": "diagnostic only"})

    for i, p in enumerate(parts):
        kind, pid = p.get("kind"), p.get("id")
        if not pid:
            raise StairCensusError(f"run {rid}: every part needs an id")
        if kind == "FLIGHT":
            _flight(stair, rid, p, k, riser, hold_run, rsrc, parts[i + 1] if i + 1 < len(parts) else None,
                    lines, checks)
        elif kind in ("WINDER", "CURVED"):
            n, _ = _count(p.get("risers"))
            a, asrc = _len(p.get("plan_area"), k * k) if p.get("plan_area") is not None else (None, None)
            cand = None if (riser is None or a is None) else 0.5 * riser * a
            why = "WINDER_STEP_RULE_NOT_ANSWERED" if kind == "WINDER" else "TAPERED_STEP_RULE_NOT_ANSWERED"
            if hold_run and hold_run[0] != "RISER_COUNT_INCONSISTENT":
                why = f"{hold_run[0]}+{why}"
            lines.append(_line(stair, rid, pid, "TURNING_STEPS", HELD, reason=why, reason_class=NEEDS_OWNER,
                               rules=("OWNER-Q-51", "OWNER-Q-19"), risers=n, riser_m=_r(riser),
                               plan_area_m2=_r(a), candidate_m3_option_A=_r(cand),
                               calc=(f"candidate (Q-51 option A, not released): 1/2 x {riser:.6f} x {a:.4f}"
                                     if cand is not None else None), sources=[asrc]))
            lines.append(_line(stair, rid, pid, "TURNING_STEPS_SOFFIT", HELD,
                               reason="WAIST_UNDER_TURNING_STEPS_NOT_ESTABLISHED", reason_class=NEEDS_OWNER,
                               rules=("OWNER-Q-51", "OWNER-Q-20")))
        elif kind == "TURN_RISER":
            n, _ = _count(p.get("risers"))
            lines.append(_line(stair, rid, pid, "TURN_RISER", HELD, reason="LANDING_LEVELS_NOT_PRINTED",
                               reason_class=NEEDS_DRAWING, rules=("OWNER-Q-19", "OWNER-Q-20", "UP-STAIR-002"),
                               risers=n, riser_m=_r(riser)))
        elif kind == "LANDING":
            _landing(stair, rid, p, k, lines)
        elif kind == "FLOOR_LANDING":
            lines.append(_line(stair, rid, pid, "FLOOR_LANDING", COUNTED_ELSEWHERE,
                               reason="THE_FLOOR_SLAB_LINE_OWNS_IT", rules=("OWNER-Q-20",)))
        else:
            raise StairCensusError(f"run {rid}: unknown part kind {kind!r}")


def _flight(stair, rid, p, k, riser, hold_run, rsrc, nxt, lines, checks):
    pid = p["id"]
    n, _ = _count(p.get("risers"))
    g, _ = _count(p.get("goings"))
    tr, trsrc = _len(p.get("tread"), k)
    w, wsrc = _len(p.get("width"), k)
    if n is None or n < 1:
        raise StairCensusError(f"flight {pid}: risers (counted on the section) are required")

    # steps (Q-19): n x 1/2 x riser x tread x width
    if hold_run:
        why, cls = hold_run[0], hold_run[1]
    elif tr is None:
        why, cls = "TREAD_NOT_ESTABLISHED", NEEDS_DRAWING
    elif w is None:
        why, cls = "WIDTH_NOT_PRINTED", NEEDS_DRAWING
    else:
        why = cls = None
    one = None if why else 0.5 * riser * tr * w
    if why:
        lines.append(_line(stair, rid, pid, "STEPS", HELD, reason=why, reason_class=cls,
                           rules=("OWNER-Q-19", "OWNER-Q-46", "UP-STAIR-009"), steps=n, riser_m=_r(riser),
                           tread_m=_r(tr), width_m=_r(w), sources=rsrc + [trsrc, wsrc]))
    else:
        lines.append(_line(stair, rid, pid, "STEPS", MEASURED, quantity_m3=n * one,
                           rules=("OWNER-Q-19", "OWNER-Q-46", "UP-STAIR-009", "UP-STAIR-002"), steps=n,
                           riser_m=_r(riser), tread_m=_r(tr), width_m=_r(w),
                           calc=f"{n} x 1/2 x {riser:.6f} x {tr:.4f} x {w:.4f}", sources=rsrc + [trsrc, wsrc]))

    # waist (Q-47 A basis): width x hypot(goings x tread, risers x riser) x thickness
    th, thsrc, basis = _thickness(p, k)
    if why:
        wwhy, wcls = why, cls
    elif g is None:
        wwhy, wcls = "GOINGS_NOT_COUNTED", NEEDS_DRAWING
    elif th is None:
        wwhy, wcls = "STAIR_WAIST_NOT_PRINTED", NEEDS_DRAWING
    else:
        wwhy = wcls = None
    if wwhy:
        lines.append(_line(stair, rid, pid, "WAIST", HELD, reason=wwhy, reason_class=wcls,
                           rules=("OWNER-Q-20", "OWNER-Q-47"), goings=g, width_m=_r(w)))
    else:
        sl = SGEO.inclined_length(g * tr, n * riser)
        lines.append(_line(stair, rid, pid, "WAIST", MEASURED, quantity_m3=w * sl * th,
                           rules=("OWNER-Q-20", "OWNER-Q-47", _thickness_rule(basis)), goings=g,
                           sloped_length_m=_r(sl), thickness_m=_r(th), thickness_basis=basis, width_m=_r(w),
                           calc=f"{w:.4f} x hypot({g} x {tr:.4f}, {n} x {riser:.6f}) x {th:.4f}",
                           sources=[thsrc]))

    # double-count check: the last riser's wedge inside the landing it arrives on (shown, never deducted here)
    if not why and nxt is not None and nxt.get("kind") == "LANDING":
        lth, _, _ = _thickness(nxt, k)
        if lth is not None:
            a = arrival_wedge_overlap(riser, tr, lth)
            checks.append({"check": "ARRIVAL_WEDGE_IN_LANDING", "stair": stair, "run": rid, "flight": pid,
                           "landing": nxt.get("id"), "overlap_m3": _r(a * w), "rule": "OWNER-Q-20",
                           "note": "counted in the steps line and in the landing line on the Q-19 / Q-47 A basis; "
                                   "shown for the owner, not deducted"})
    if not why and nxt is not None and nxt.get("kind") == "FLOOR_LANDING":
        checks.append({"check": "ARRIVAL_WEDGE_AT_FLOOR_SLAB", "stair": stair, "run": rid, "flight": pid,
                       "wedge_m3": _r(0.5 * riser * tr * w), "rule": "OWNER-Q-20",
                       "note": "the last riser's wedge lies under the floor slab edge if the slab runs to the riser "
                               "line; the floor slab line owns the slab: shown as the whole wedge (upper bound), "
                               "not deducted"})


def _landing(stair, rid, p, k, lines):
    pid = p["id"]
    ln, lsrc = _len(p.get("length"), k)
    w, wsrc = _len(p.get("width"), k)
    th, thsrc, basis = _thickness(p, k)
    if ln is None or w is None:
        lines.append(_line(stair, rid, pid, "LANDING", HELD, reason="LANDING_SIZE_NOT_PRINTED",
                           reason_class=NEEDS_DRAWING, rules=("OWNER-Q-20",), length_m=_r(ln), width_m=_r(w),
                           sources=[lsrc, wsrc]))
    elif th is None:
        lines.append(_line(stair, rid, pid, "LANDING", HELD, reason="LANDING_NOT_PRINTED",
                           reason_class=NEEDS_DRAWING, rules=("OWNER-Q-20", "OWNER-Q-47"), length_m=_r(ln),
                           width_m=_r(w), plan_area_m2=_r(ln * w), sources=[lsrc, wsrc]))
    else:
        lines.append(_line(stair, rid, pid, "LANDING", MEASURED, quantity_m3=ln * w * th,
                           rules=("OWNER-Q-20", "OWNER-Q-47", _thickness_rule(basis)), length_m=_r(ln),
                           width_m=_r(w), thickness_m=_r(th), thickness_basis=basis,
                           calc=f"{ln:.4f} x {w:.4f} x {th:.4f}", sources=[lsrc, wsrc, thsrc]))


def _beam(stair, b, k, lines):
    bid = b.get("id")
    if not bid:
        raise StairCensusError("every stair beam needs an id")
    w, _ = _len(b.get("width"), k)
    d, _ = _len(b.get("depth"), k)
    ln, _ = _len(b.get("length"), k)
    src = b.get("source")
    if w is None or d is None:
        lines.append(_line(stair, None, bid, "STAIR_BEAM", HELD, reason="STAIR_BEAM_SECTION_NOT_PRINTED",
                           reason_class=NEEDS_DRAWING, rules=("OWNER-Q-20",), sources=[src]))
    elif ln is None:
        lines.append(_line(stair, None, bid, "STAIR_BEAM", HELD, reason="STAIR_BEAM_LENGTH_OR_LEVELS_NOT_PRINTED",
                           reason_class=NEEDS_DRAWING, rules=("OWNER-Q-20",), width_m=_r(w), depth_m=_r(d),
                           sources=[src]))
    else:
        lines.append(_line(stair, None, bid, "STAIR_BEAM", MEASURED, quantity_m3=w * d * ln,
                           rules=("OWNER-Q-20", "UP-STAIR-002"), width_m=_r(w), depth_m=_r(d), length_m=_r(ln),
                           calc=f"{w:.4f} x {d:.4f} x {ln:.4f}", sources=[src]))


# ====================================================================== the stair
def measure(census):
    """every concrete line of one stair, separately; totals only of MEASURED lines (None when no line is measured,
    never 0); every HELD line listed by name."""
    sid = census.get("id")
    if not sid:
        raise StairCensusError("the stair needs an id")
    k = UNITS.get(census.get("unit"))
    if k is None:
        raise StairCensusError(f"unit must be one of {sorted(UNITS)}")
    lines, checks = [], []
    for np_ in census.get("not_present") or []:
        lines.append(_line(sid, None, np_.get("id"), "STAIR_RUN", NOT_PRESENT, reason=np_.get("evidence"),
                           rules=("UP-QTY-STATUS-001",)))
    for run in census.get("runs") or []:
        _run(sid, run, k, lines, checks)
    for b in census.get("beams") or []:
        _beam(sid, b, k, lines)
    if census.get("runs"):
        for item in LATER_ITEMS:
            lines.append(_line(sid, None, None, item, LATER, reason="SEPARATE_LATER_ITEM_NOT_MEASURED_HERE",
                               rules=("OWNER-Q-20",), unit_of_item=None))
    by = {}
    for ln in lines:
        if ln["status"] == MEASURED:
            by[ln["element"]] = by.get(ln["element"], 0.0) + ln["quantity_m3"]
    measured = sum(by.values()) if by else None      # nothing measured is not 0 m3 (UP-QTY-STATUS-001)
    return {"method": METHOD, "stair": sid, "lines": lines, "checks": checks,
            "totals": {"measured_m3": _r(measured), "measured_by_element_m3": {e: _r(v) for e, v in sorted(by.items())},
                       "held": [f"{ln['part']}:{ln['element']}:{ln['reason']}" for ln in lines
                                if ln["status"] == HELD],
                       "counted_elsewhere": [ln["part"] for ln in lines if ln["status"] == COUNTED_ELSEWHERE],
                       "later_items": [ln["element"] for ln in lines if ln["status"] == LATER],
                       "not_present": [ln["part"] for ln in lines if ln["status"] == NOT_PRESENT]}}


def measure_all(censuses):
    """several stairs: one result per stair and the project totals of MEASURED lines (held lines listed by stair)."""
    res = [measure(c) for c in censuses]
    ids = [r["stair"] for r in res]
    if len(set(ids)) != len(ids):
        raise StairCensusError("stair ids must be unique")
    return {"method": METHOD, "stairs": res,
            "totals": {"measured_m3": _r(sum(r["totals"]["measured_m3"] for r in res
                                             if r["totals"]["measured_m3"] is not None)),
                       "held": {r["stair"]: r["totals"]["held"] for r in res if r["totals"]["held"]}}}
