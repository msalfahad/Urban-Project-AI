"""T-706 rules (project-agnostic; scope: any villa's suspended slab plans and any reference workbook). Research only,
unwired: changes no line, no quantity, no frozen method, no rule or knowledge version file.

R-T706-1 1.0.0  A TYPED REFERENCE SPLIT BY THICKNESS ZONE. Provenance: T-706 (2F roof slab of the development villa:
    reference 31.84 m2 x 0.16 + 13.35 m2 x 0.18 typed, no derivation), T-683 R-T683-2 (storey bridge), T-688 R-T688-2
    (one typed constant per storey), ERS s.2.6.
    (a) The physical element is the slab panel at its OWN thickness. A panel's zone is the thickness PRINTED inside it
        (e.g. 'T 18'); without a printed mark the zone is the sheet's stated default; a panel with neither (or with two
        conflicting marks) has no zone: the reconciliation is refused for that storey (the panel stays HELD, never 0
        and never moved into a zone by the reference).
    (b) The difference reference - engine (m3) is split zone by zone: term_z = (ref_z - engine_z) x t_z, each read
        with R-T688-2 at the zone's own printed resolution (rounding band, then scope). The terms re-add to the storey
        difference exactly (Decimal); a split that does not re-add is refused.
    (c) A zone-to-zone TRANSFER (the reference measured a panel of one zone in the other) is claimed only when a
        whole-panel subset of one zone fits, within both resolutions, the deficit of that zone AND the excess of the
        other; otherwise the gap is NOT_WHOLE_PANELS (partial panels or the reference's own dimensions) and stays
        UNRESOLVED with its terms named. The fitting subset closest to the reference is never picked.
    (d) The engine side of every zone is first checked against an own re-measure (R-T706-2); a zone whose own and
        engine areas differ beyond tol names OUR ERROR first.

R-T706-2 1.0.0  AN OWN RE-MEASURE IS A CHECK ONLY WHERE IT SEPARATES THE ENGINE FACES; EVERY EXCLUDED FACE GETS ITS
    PHYSICAL CLASS. Provenance: T-706 (GF: without the beam-edge layer one own face held 5 released panels + 5 beam
    strips + the B27 strip, 44.879 m2; with it 33 / 33 panels separate and agree to 0.000222 m2), T-688 R-T688-1.
    (a) Each engine slab line is located by its engine face's interior point in the own faces. A line alone in its
        own face is CHECKED (own area compared); a line sharing its own face with another engine face is NOT_CHECKED
        (the own noding missed a member edge: add the member-edge layer, never compare a merged face with a sum);
        a line in no own face is UNLOCATED. A storey with any released line not CHECKED cannot claim ENGINE_RIGHT on
        geometry.
    (b) Every EXCLUDED slab line and every own face no line owns is classed by drawn evidence only, in this order:
        DOME_SEGMENT (one of >= 8 equal faces whose centroids sit at one radius: a dome drawn on the plan, the dome
        family); STAIR_ZONE (inner flight lines >= 5; decided before the symbol count, a stair well also carries void
        symbols); DOME_OPENING (radial symbol lines >= 8); OPENING (at least two opening-symbol lines span it); a face
        with a printed thickness mark is a panel, never a band (UNRESOLVED when excluded); MEMBER_STRIP (inscribed
        width, the diameter of the largest inscribed circle, within tol of a drawn member section, or a member label
        inside and width <= the widest drawn section); NARROW_BAND (width below the narrowest drawn member section and
        no thickness mark: a drawn non-panel element or an edge offset, never slab); else UNRESOLVED. A storey's slab
        residual closes only when no excluded or unowned face is UNRESOLVED.

R-T706-3 1.0.0  A REFERENCE ARITHMETIC SLIP IS EXPLAINED ONLY WITH ITS MEMBER. Provenance: T-706 (1F beam: the
    reference total cell sums one row fewer than its carry cell), T-683 R-T683-3 (expand the cover chain), T-545.
    (a) The omitted rows are the rows inside the carry (or row-sum) range and outside the total range (and vice versa:
        a row counted twice); their values must re-add to total - carry exactly.
    (b) Each omitted row is explained only when it names the drawn member (mark, storey, section) AND the engine's
        treatment of that member is stated (OWNED: the engine bills that member on that storey; NOT_OWNED: it does not,
        which is then an engine scope question, not arithmetic). An omitted row without both stays UNRESOLVED.
    (c) The slip is a reference-side fact: it never moves an engine quantity and is never used as proof of one.
"""
from __future__ import annotations

import itertools
from decimal import Decimal

R1, R2, R3 = "R-T706-1 1.0.0", "R-T706-2 1.0.0", "R-T706-3 1.0.0"


class Refused(ValueError):
    pass


def D(v) -> Decimal:
    return Decimal(str(v))


def resolution(printed: str) -> Decimal:
    s = str(printed).strip()
    if not s or not all(ch.isdigit() or ch == "." for ch in s) or s.count(".") > 1:
        raise Refused(f"not a typed numeric constant: {printed!r}")
    return Decimal(1) if "." not in s else Decimal(1).scaleb(-len(s.split(".")[1]))


# ------------------------------------------------------------------------------------------------ R-T706-1
def zone_of(panel, sheet_default_t=None):
    """panel: {'marks': [t, ...] printed inside (m)}; returns t (Decimal) or raises Refused (no zone / conflict)."""
    marks = sorted({D(m) for m in panel.get("marks", [])})
    if len(marks) > 1:
        raise Refused(f"panel {panel.get('id')}: conflicting thickness marks {marks}")
    if marks:
        return marks[0]
    if sheet_default_t is None:
        raise Refused(f"panel {panel.get('id')}: no printed thickness and no stated sheet default (stays HELD)")
    return D(sheet_default_t)


def _subsets(vals, lo, hi):
    out = []
    for r in range(1, len(vals) + 1):
        for comb in itertools.combinations(range(len(vals)), r):
            if lo <= sum(vals[i] for i in comb) <= hi:
                out.append(comb)
    return out


def zone_reconcile(engine_panels, own_panels, reference, *, sheet_default_t=None, tol_m2="0.005"):
    """engine_panels: [{'id', 'm2', 'marks'}]; own_panels: {id: m2} (own re-measure of the same panels);
    reference: {t (str): printed area (str)} e.g. {'0.16': '31.84', '0.18': '13.35'}.
    Returns per-zone terms (m3), their sum, the storey difference and the status."""
    if {p["id"] for p in engine_panels} != set(own_panels):
        raise Refused("own re-measure must locate every engine panel (R-T706-1 (d))")
    zones = {}
    for p in engine_panels:
        zones.setdefault(zone_of(p, sheet_default_t), []).append(p)
    ref = {D(t): (D(a), resolution(a)) for t, a in reference.items()}
    rows, total_term = [], Decimal(0)
    for t in sorted(set(zones) | set(ref)):
        ps = zones.get(t, [])
        eng = sum((D(p["m2"]) for p in ps), Decimal(0))
        own = sum((D(own_panels[p["id"]]) for p in ps), Decimal(0))
        r, u = ref.get(t, (Decimal(0), Decimal(0)))
        our = own - eng
        term = (r - eng) * t
        total_term += term
        lo, hi = eng - (r + u / 2), eng - (r - u / 2)          # engine minus reference measured value, m2
        if abs(our) > D(tol_m2):
            st = "OUR_ERROR"
        elif lo <= 0 <= hi:
            st = "ROUNDING_ONLY"
        elif hi < 0:
            st = "REFERENCE_LARGER"
        else:
            n = len(_subsets([D(p["m2"]) for p in ps], lo, hi))
            st = "UNIQUE_CANDIDATE" if n == 1 else ("UNRESOLVED_AMBIGUOUS" if n > 1 else "NOT_WHOLE_PANELS")
        rows.append({"t_m": t, "panels": len(ps), "engine_m2": eng, "own_m2": own, "own_minus_engine_m2": our,
                     "reference_m2": r, "resolution_m2": u, "ref_minus_engine_m2": r - eng, "term_m3": term,
                     "status": st})
    eng_m3 = sum((D(p["m2"]) * zone_of(p, sheet_default_t) for p in engine_panels), Decimal(0))
    ref_m3 = sum((a * t for t, (a, _) in ref.items()), Decimal(0))
    diff = ref_m3 - eng_m3
    if total_term != diff:
        raise Refused(f"zone terms {total_term} do not re-add to the storey difference {diff} (R-T706-1 (b))")
    # (c) transfer: a whole-panel subset of zone A fitting both A's deficit and B's excess
    transfer = []
    for a, b in itertools.permutations([row for row in rows], 2):
        need_a = -a["ref_minus_engine_m2"]                     # area zone A lacks in the reference
        gain_b = b["ref_minus_engine_m2"]                      # area zone B has in excess
        if need_a <= 0 or gain_b <= 0:
            continue
        u = a["resolution_m2"] / 2 + b["resolution_m2"] / 2
        vals = [D(p["m2"]) for p in zones.get(a["t_m"], [])]
        for comb in _subsets(vals, need_a - u, need_a + u):
            s = sum(vals[i] for i in comb)
            if abs(s - gain_b) <= u:
                transfer.append({"from_t": a["t_m"], "to_t": b["t_m"], "panels": len(comb), "m2": s})
    if any(r["status"] == "OUR_ERROR" for r in rows):
        status = "OUR_ERROR"
    elif len(rows) == 1:
        status = rows[0]["status"]
    elif all(r["status"] == "ROUNDING_ONLY" for r in rows):
        status = "ROUNDING_ONLY"
    elif len(transfer) == 1:
        status = "TRANSFER_CANDIDATE"
    elif len(transfer) > 1 or any(r["status"] in ("UNIQUE_CANDIDATE", "UNRESOLVED_AMBIGUOUS") for r in rows):
        status = "UNRESOLVED_AMBIGUOUS"
    else:
        status = "NOT_WHOLE_PANELS"
    return {"rule": R1, "zones": rows, "engine_m3": eng_m3, "reference_m3": ref_m3, "difference_m3": diff,
            "terms_sum_m3": total_term, "transfers": transfer, "status": status}


# ------------------------------------------------------------------------------------------------ R-T706-2
def check_location(lines):
    """lines: [{'line_id', 'class', 'own_face' (int|None), 'engine_m2', 'own_m2'}] of one storey.
    Returns per-line CHECKED / NOT_CHECKED / UNLOCATED and whether the storey may claim ENGINE_RIGHT on geometry."""
    count = {}
    for x in lines:
        if x["own_face"] is not None:
            count[x["own_face"]] = count.get(x["own_face"], 0) + 1
    out, ok = [], True
    for x in lines:
        if x["own_face"] is None:
            st = "UNLOCATED"
        elif count[x["own_face"]] > 1:
            st = "NOT_CHECKED"
        else:
            st = "CHECKED"
        if x["class"] == "RELEASED" and st != "CHECKED":
            ok = False
        d = (D(x["own_m2"]) - D(x["engine_m2"])) if st == "CHECKED" else None
        out.append({"line_id": x["line_id"], "class": x["class"], "check": st, "own_minus_engine_m2": d})
    return {"rule": R2, "lines": out, "geometry_claim_allowed": ok}


def classify_face(face, *, member_sections_m, tol=0.02):
    """face: {'mean_width_m' (the inscribed width), 'opening_lines', 'inner_lines', 'radial_lines' (opt),
    'radial_ring_segment' (opt), 'member_label', 'thickness_mark'}.
    Returns the physical class by drawn evidence (R-T706-2 (b))."""
    w = D(face["mean_width_m"])
    if w <= 0:
        raise Refused("face width must be positive")
    secs = sorted(D(s) for s in member_sections_m)
    if face.get("radial_ring_segment"):
        return "DOME_SEGMENT"
    if face.get("inner_lines", 0) >= 5:                       # flight lines decide before the void symbol count
        return "STAIR_ZONE"
    if face.get("radial_lines", 0) >= 8 or face.get("opening_lines", 0) >= 8:
        return "DOME_OPENING"
    if face.get("opening_lines", 0) >= 2:
        return "OPENING"
    if face.get("thickness_mark"):
        return "UNRESOLVED"                                   # a printed thickness means a panel: never a band
    if any(abs(w - s) <= D(tol) for s in secs) or (face.get("member_label") and w <= secs[-1] + D(tol)):
        return "MEMBER_STRIP"
    if w < secs[0] - D(tol):
        return "NARROW_BAND"
    return "UNRESOLVED"


def storey_closure(classes):
    """classes: {face: class}; the storey residual closes only when none is UNRESOLVED."""
    bad = sorted(k for k, v in classes.items() if v == "UNRESOLVED")
    return {"rule": R2, "closed": not bad, "unresolved": bad}


# ------------------------------------------------------------------------------------------------ R-T706-3
def omitted_rows(values, carry_rows, total_rows, carry_value, total_value):
    """values: {row: m3}; carry_rows / total_rows: the row sets the two cells sum. Returns the omitted / doubled rows,
    checked to re-add exactly to total - carry. A blank row (absent from values) sums as nothing and is never listed."""
    carry_rows = {r for r in carry_rows if r in values}
    total_rows = {r for r in total_rows if r in values}
    if sum(D(values[r]) for r in carry_rows) != D(carry_value) or sum(D(values[r]) for r in total_rows) != D(total_value):
        raise Refused("a cell value does not equal the sum of its rows: expand the chain first (R-T683-3)")
    omitted, extra = sorted(carry_rows - total_rows), sorted(total_rows - carry_rows)
    gap = D(total_value) - D(carry_value)
    if -sum(D(values[r]) for r in omitted) + sum(D(values[r]) for r in extra) != gap:
        raise Refused("omitted / doubled rows do not re-add to total - carry")
    return {"rule": R3, "omitted": omitted, "extra": extra, "gap_m3": gap}


def explain_slip(slip, members):
    """members: {row: {'mark', 'storey', 'section', 'engine': 'OWNED'|'NOT_OWNED'|None}} for the omitted rows."""
    out = []
    for r in slip["omitted"] + slip["extra"]:
        m = members.get(r) or {}
        if not (m.get("mark") and m.get("storey") and m.get("section")) or m.get("engine") not in ("OWNED", "NOT_OWNED"):
            st = "UNRESOLVED"
        else:
            st = "REFERENCE_ARITHMETIC" if m["engine"] == "OWNED" else "ENGINE_SCOPE_QUESTION"
        out.append({"row": r, "status": st, **{k: m.get(k) for k in ("mark", "storey", "section", "engine")}})
    return {"rule": R3, "rows": out, "engine_quantity_moved_m3": Decimal(0),
            "explained": bool(out) and all(o["status"] == "REFERENCE_ARITHMETIC" for o in out)}
