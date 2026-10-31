"""T-387 rules: structural element ownership and overlap census (research only, every villa; stdlib + shapely).

Nothing here produces or changes a BOQ quantity. It answers two questions about a candidate's structural concrete
lines:
  (a) is every line bound to ONE physical element and ONE owner trade, with its contractual status (a line under an
      unresolved Checker downgrade record is HELD whatever figure it carries; lesson of T-374);
  (b) for every intersecting element pair, is the shared volume (sum - union) billed once: 0.000 within TOL_M3, or a
      named DOUBLE (billed twice) / GAP (built, billed by neither) in m3 with the line ids.

R-T387-1 (binding) a structural concrete line is BOUND when it names an element id, its item code maps to exactly one
         element family and one owner trade, and no other line of the same code bills the same element id (split parts
         carry their own suffix: '.1', '.2' or ':PART'); otherwise it is UNBOUND with the reason. An UNBOUND line is
         never reported as OK.
R-T387-2 (status) contractual status = the weakest of: the line's own state (a blank figure = HELD; a line
         NOT_APPLICABLE_WITH_EVIDENCE bills nothing and is its own status), any unresolved
         downgrade record that names the line (HELD, figure kept for audit only). A HELD line is never summed, not as
         its figure and not as 0: sums carry valued m3 and the held line count beside it.
R-T387-3 (plan overlap of members on one level band) for members cast in one level band (beams, slab panels, columns
         of one floor): shared plan area = sum of the members' plan areas - area of their union; it is billed once when
         each line's billed plan (its net plan) equals its drawn plan minus exactly the parts owned by the other
         members (route G precedence COLUMN > BEAM > SLAB; between two beams the junction square is owned by one band).
         DOUBLE m2 = sum(billed plan) - area(union of drawn plans) when > TOL_M2; GAP m2 = area(union) - sum(billed)
         when > TOL_M2 (a junction deducted by both bands). Volume = m2 x the smaller depth of the pair it lies in.
R-T387-3a (arc chord) a slab face bounded by a curved member face and given as a chord polygon is measured on its
         exact outline: its polygon overlap with the ARC band is a chord artefact up to the polygon's excess over the
         exact area; only the overlap beyond the excess is shared volume.
R-T387-4 (stacked members) members stacked in z (neck under column, column under beam) share no volume when the
         upper member's billed bottom equals the lower member's billed top; a stated overlap or gap in m is turned into
         m3 by the shared plan section; levels not printed on either = UNDETERMINED (bounded, never 0, never deducted).
R-T387-5 (pairs carried from a merged ledger) a pair proven on a Checker-merged ledger (stair / beam T-192, buried
         components T-347) is carried only while every line the ledger bound is present in the candidate with the
         same figure; a changed or missing line re-opens the pair (RECHECK, never silently OK).
R-T387-7 (documented sub-tolerance deduction; T-392, Checker T-387 lesson 2026-10-31) a member residual is reconciled
         to EVERY merged ledger that wrote the line (formula / adjustment field first), not to one ledger; a residual
         that equals a documented, named deduction or addition (within 1e-6 m3) is reported BY THAT NAME
         (DOCUMENTED_ADJUSTMENT) even when it is below TOL_M3; labelling such a residual 'rounding' is refused. Only a
         residual within TOL_M3 that no documented item explains may be called rounding.
"""

from __future__ import annotations

import re

TOL_M3 = 0.001
TOL_M2 = 1e-4

# item code -> (element family, owner trade). One code = one family = one owner trade (R-T387-1).
FAMILY_OF_CODE = {
    "STR.CONC.BLINDING": ("BLINDING", "CONCRETE (plain, CONC.BLINDING)"),
    "STR.CONC.FOOTING": ("FOOTING", "CONCRETE"),
    "STR.CONC.RAFT": ("FOOTING", "CONCRETE"),
    "STR.CONC.STRAP": ("STRAP", "CONCRETE"),
    "STR.CONC.NECK": ("NECK", "CONCRETE"),
    "STR.CONC.GROUND_BEAM": ("GROUND_BEAM", "CONCRETE"),
    "STR.CONC.BOUNDARY_WALL": ("GROUND_BEAM", "CONCRETE (boundary-wall ground beam)"),
    "STR.CONC.GROUND_SLAB": ("GROUND_SLAB", "CONCRETE"),
    "STR.CONC.COLUMN": ("COLUMN", "CONCRETE"),
    "STR.CONC.BEAM": ("BEAM", "CONCRETE"),
    "STR.CONC.SLAB": ("SLAB", "CONCRETE"),
    "STR.CONC.STAIR": ("STAIR", "CONCRETE"),
    "STR.CONC.DOME": ("DOME", "CONCRETE"),
    "STR.CONC.POOL": ("POOL", "CONCRETE"),
    "STR.CONC.PARAPET": ("PARAPET", "CONCRETE (parapet family, T-319)"),
}
PART_SUFFIX = re.compile(r"(\.\d+|:PART[^:]*|:P\d+)$")
VALUED_STATES = ("DRAWING_CONFIRMED", "DRAWING-CONFIRMED", "CALCULATED", "VERIFIED", "PROVISIONAL", "MEASURED",
                 "ASSUMED_OWNER_APPROVED", "RELEASED")


class Refused(ValueError):
    """an input the census must not accept silently."""


def family_of(item_code):
    if item_code in FAMILY_OF_CODE:
        return FAMILY_OF_CODE[item_code]
    for code, fam in FAMILY_OF_CODE.items():
        if item_code.startswith(code + "."):
            return fam
    return None


def _value(line):
    v = line.get("measured_net")
    return None if v is None else float(v)


def downgraded_ids(downgrades):
    """line id -> [downgrade ids] of the UNRESOLVED records (a record with resolved True no longer holds)."""
    out = {}
    for r in downgrades or []:
        if r.get("resolved") is True or str(r.get("state", "")).upper() in ("RESOLVED", "SUPERSEDED"):
            continue
        for lid in r.get("line_ids") or []:
            out.setdefault(lid, []).append(r.get("downgrade_id"))
    return out


def bind(lines, downgrades=()):
    """(a): one row per structural concrete line. Never drops a line: an unknown code or a missing element id is a row
    with binding UNBOUND and its reason."""
    dg = downgraded_ids(downgrades)
    rows, seen = [], {}
    for ln in lines:
        code = ln.get("item_code") or ""
        if not code.startswith("STR.CONC"):
            continue
        eid = ln.get("element_id") or (ln.get("location") or {}).get("element_id")
        fam = family_of(code)
        v = _value(ln)
        state = ln.get("evidence_state") or ""
        reasons = []
        if not eid:
            reasons.append("no element id")
        if fam is None:
            reasons.append(f"item code {code} maps to no element family / owner trade")
        key = (code, eid)
        if eid and key in seen and not PART_SUFFIX.search(eid):
            reasons.append(f"element {eid} already billed by {seen[key]} under the same code")
        if eid:
            seen.setdefault(key, ln["line_id"])
        held_by = dg.get(ln["line_id"], [])
        if held_by:
            status, why = "HELD", "downgrade " + ", ".join(held_by) + " (figure audit only)"
        elif state.upper().startswith("NOT_APPLICABLE"):
            status, why = "NOT_APPLICABLE", state     # retired / not applicable with evidence: no concrete billed
        elif v is None:
            status, why = "HELD", f"blank ({state})"
        else:
            status, why = "VALUED", state
        rows.append({"line_id": ln["line_id"], "item_code": code, "element_id": eid or "",
                     "family": fam[0] if fam else "", "owner_trade": fam[1] if fam else "",
                     "floor": ln.get("floor") or (ln.get("location") or {}).get("floor") or "",
                     "binding": "UNBOUND" if reasons else "BOUND", "binding_reason": "; ".join(reasons),
                     "status": status, "status_reason": why,
                     "valued_m3": v if status == "VALUED" else None,
                     "audit_m3": v if status != "VALUED" else None})
    return rows


def totals(rows):
    """per family: valued m3 (VALUED only), held line count; a HELD line adds nothing and is counted beside."""
    out = {}
    for r in rows:
        t = out.setdefault(r["family"] or "UNBOUND", {"lines": 0, "valued_m3": 0.0, "held_lines": 0, "unbound": 0})
        t["lines"] += 1
        if r["binding"] == "UNBOUND":
            t["unbound"] += 1
        if r["status"] == "VALUED":
            t["valued_m3"] += r["valued_m3"]
        elif r["status"] == "HELD":
            t["held_lines"] += 1
    return out


def ok_rows(rows):
    """the rows the census may call OK: BOUND and not HELD. An UNBOUND row is refused as OK (R-T387-1)."""
    return [r for r in rows if r["binding"] == "BOUND" and r["status"] in ("VALUED", "NOT_APPLICABLE")]


# ---------------------------------------------------------------- R-T387-3: one level band, plan overlaps

def _poly(p):
    from shapely.geometry import Polygon
    if hasattr(p, "geom_type"):                    # already a shapely geometry (a group of member pieces)
        return p if p.is_valid else p.buffer(0)
    g = Polygon(p)
    if not g.is_valid:
        g = g.buffer(0)
    return g


def level_band_check(members, scale=1.0, tol_m2=TOL_M2):
    """members: [{id, kind (COLUMN / BEAM / SLAB), polygon (plan, drawing units), billed_m2 (the line's net plan, m2,
    None = HELD), depth_m (None = not printed), line_ids, drawn_m2 (optional exact plan, m2)}]. scale = metres per drawing unit.

    Returns the pair rows (shared plan m2 and m3, the owner by precedence, how many lines bill it) and the band totals:
    union m2, billed m2 (valued members), DOUBLE / GAP m2 and m3. A HELD member (billed None) is never taken as 0: its
    drawn plan is in the union, its pairs are UNDETERMINED and the totals exclude its area from both sides."""
    from shapely.ops import unary_union
    prec = {"COLUMN": 50, "BEAM": 40, "SLAB": 30}
    G = {m["id"]: _poly(m["polygon"]) for m in members}
    k2 = scale * scale
    by = {m["id"]: m for m in members}
    for m in members:
        if m["kind"] not in prec:
            raise Refused(f"{m['id']}: kind {m['kind']} not a level-band member")
    # owned plan of each member = drawn minus every higher-precedence member. Between two beams the junction square is
    # owned by ONE band (route G): the band whose billed plan includes it (read from the two lines: the band that
    # deducted it is the one whose billed plan is closer to its drawn plan minus the junction); when neither or both
    # lines show it (or a line is HELD) the lower id owns, and a junction both deducted / both kept shows as GAP / DOUBLE.
    def _hi(m):
        return [G[o["id"]] for o in members if o is not m and prec[o["kind"]] > prec[m["kind"]]
                and G[o["id"]].intersects(G[m["id"]])]

    base = {m["id"]: (G[m["id"]].difference(unary_union(_hi(m))) if _hi(m) else G[m["id"]]) for m in members}
    jowner = {}
    for i, m in enumerate(members):
        for o in members[i + 1:]:
            if not (m["kind"] == o["kind"] == "BEAM") or not G[m["id"]].intersects(G[o["id"]]):
                continue
            j = base[m["id"]].intersection(base[o["id"]])
            a = j.area * scale * scale
            if a <= tol_m2:
                continue
            ded = {}
            for x in (m, o):
                if x["billed_m2"] is None:
                    continue
                r0 = x["billed_m2"] - base[x["id"]].area * scale * scale
                ded[x["id"]] = abs(r0 + a) < abs(r0)
            if ded.get(m["id"]) and not ded.get(o["id"], False):
                own = o["id"]
            elif ded.get(o["id"]) and not ded.get(m["id"], False):
                own = m["id"]
            else:
                own = min(m["id"], o["id"])
            jowner[frozenset((m["id"], o["id"]))] = own
    owned = {}
    for m in members:
        cut = _hi(m) + [G[o["id"]] for o in members if o is not m and o["kind"] == m["kind"] == "BEAM"
                        and jowner.get(frozenset((m["id"], o["id"]))) == o["id"]]
        owned[m["id"]] = G[m["id"]].difference(unary_union(cut)) if cut else G[m["id"]]
    pairs = []
    ids = sorted(G)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if not G[a].intersects(G[b]):
                continue
            sh = G[a].intersection(G[b]).area * k2
            if sh <= tol_m2:
                continue
            ma, mb = by[a], by[b]
            if ma["kind"] == mb["kind"] and ma["kind"] != "BEAM":
                status, owner = "SAME_KIND_OVERLAP", None
            elif prec[ma["kind"]] != prec[mb["kind"]]:
                owner = a if prec[ma["kind"]] > prec[mb["kind"]] else b
                status = "OWNED"
            else:
                owner, status = jowner.get(frozenset((a, b)), min(a, b)), "OWNED"
            d = [x["depth_m"] for x in (ma, mb) if x["depth_m"] is not None]
            if ma["billed_m2"] is None or mb["billed_m2"] is None:
                status = "UNDETERMINED"
            pairs.append({"a": a, "b": b, "kind": f"{ma['kind']}/{mb['kind']}", "shared_m2": sh,
                          "shared_m3": sh * min(d) if len(d) == 2 else None, "owner": owner, "status": status,
                          "lines_a": ma.get("line_ids", []), "lines_b": mb.get("line_ids", [])})
    valued = [m for m in members if m["billed_m2"] is not None]
    held = [m for m in members if m["billed_m2"] is None]
    U = unary_union([G[m["id"]] for m in members])
    Uh = unary_union([owned[m["id"]] for m in held]) if held else None
    union_valued_m2 = (U.difference(Uh).area if Uh is not None else U.area) * k2
    billed_m2 = sum(m["billed_m2"] for m in valued)
    # per member: billed vs owned plan (the member's own residual names where a double / gap sits)
    per = []
    for m in valued:
        # drawn_m2 (optional): the member's exact plan from its source (arcs, holes) when the polygon given is a
        # chord / outer-ring approximation; the members it loses to others are still measured on the polygon
        poly_m2 = G[m["id"]].area * k2
        drawn = m.get("drawn_m2") if m.get("drawn_m2") is not None else poly_m2
        o = drawn - (poly_m2 - owned[m["id"]].area * k2)
        r = m["billed_m2"] - o
        per.append({"id": m["id"], "kind": m["kind"], "drawn_m2": drawn, "polygon_m2": poly_m2, "owned_m2": o,
                    "billed_m2": m["billed_m2"], "residual_m2": r, "depth_m": m["depth_m"],
                    "residual_m3": r * m["depth_m"] if m["depth_m"] is not None else None,
                    "line_ids": m.get("line_ids", [])})
    for p in per:
        p["within_tol"] = p["residual_m3"] is not None and abs(p["residual_m3"]) <= TOL_M3
    double = sum(p["residual_m2"] for p in per if p["residual_m2"] > tol_m2 and not p["within_tol"])
    gap = -sum(p["residual_m2"] for p in per if p["residual_m2"] < -tol_m2 and not p["within_tol"])
    return {"pairs": pairs, "members": per, "union_valued_m2": union_valued_m2, "billed_m2": billed_m2,
            "double_m2": double, "gap_m2": gap,
            "double_m3": sum(p["residual_m3"] for p in per if p["residual_m2"] > tol_m2 and p["residual_m3"] is not None
                             and not p["within_tol"]),
            "gap_m3": -sum(p["residual_m3"] for p in per if p["residual_m2"] < -tol_m2 and p["residual_m3"] is not None
                           and not p["within_tol"]),
            "held_members": [m["id"] for m in held],
            "status": ("PASS" if double <= tol_m2 and gap <= tol_m2 else "FAIL") +
                      ("_HELD" if held else "")}


def arc_chord_owned(exact_m2, polygon_m2, polygon_loss_m2, arc_overlap_m2):
    """R-T387-3a: a slab face with an arc edge given as a chord polygon (polygon_m2 > exact_m2). Its chord excess lies
    across the arc it stops at, so the polygon 'overlaps' the ARC band there by up to the excess. Returns the face's
    owned plan on the exact outline: exact - (losses to non-arc members) - max(0, arc overlap - excess), and the
    true arc overlap. A face whose polygon is not larger than its exact area has no chord: refused."""
    excess = polygon_m2 - exact_m2
    if excess <= TOL_M2:
        raise Refused("no chord excess: the polygon is the outline, use it as drawn")
    if arc_overlap_m2 > polygon_loss_m2 + TOL_M2:
        raise Refused("the arc overlap exceeds the polygon's whole loss")
    true_ov = max(0.0, arc_overlap_m2 - excess)
    return exact_m2 - (polygon_loss_m2 - arc_overlap_m2) - true_ov, true_ov


# ---------------------------------------------------------------- R-T387-4: stacked members

def stacked_check(lower_top_m, upper_bottom_m, section_m2):
    """overlap (> 0) or gap (< 0) between a lower member's billed top and an upper member's billed bottom, in m3.
    None on either level = UNDETERMINED (never 0)."""
    if lower_top_m is None or upper_bottom_m is None or section_m2 is None:
        return {"status": "UNDETERMINED", "m3": None}
    dz = lower_top_m - upper_bottom_m
    m3 = dz * section_m2
    if abs(m3) <= TOL_M3:
        return {"status": "OK", "m3": 0.0}
    return {"status": "DOUBLE" if m3 > 0 else "GAP", "m3": abs(m3)}


# ---------------------------------------------------------------- R-T387-5: carried pairs

DOC_EPS_M3 = 1e-6


def classify_residual(residual_m3, documented, label=None):
    """R-T387-7. documented: [(name, signed m3), ...] from every merged ledger that wrote the line. Returns
    {'verdict': DOCUMENTED_ADJUSTMENT | OK_ROUNDING | UNEXPLAINED, 'named': [...], 'unexplained_m3': x}.
    label: a verdict the caller proposes; 'OK_ROUNDING' for a residual a documented item explains is Refused."""
    if residual_m3 is None:
        raise Refused("RESIDUAL_MISSING: a HELD member has no residual (never 0)")
    items = [(str(n), float(v)) for n, v in documented]
    if any(not n.strip() for n, _ in items):
        raise Refused("UNNAMED_ADJUSTMENT: a documented adjustment needs its ledger name")
    total = sum(v for _, v in items)
    if items and abs(residual_m3 - total) <= DOC_EPS_M3:
        verdict = "DOCUMENTED_ADJUSTMENT"
        out = {"verdict": verdict, "named": [n for n, _ in items], "unexplained_m3": residual_m3 - total}
    elif abs(residual_m3 - total) <= TOL_M3 and not items:
        out = {"verdict": "OK_ROUNDING", "named": [], "unexplained_m3": residual_m3}
    else:
        out = {"verdict": "UNEXPLAINED", "named": [n for n, _ in items], "unexplained_m3": residual_m3 - total}
    if label is not None and label != out["verdict"]:
        if label == "OK_ROUNDING" and out["verdict"] == "DOCUMENTED_ADJUSTMENT":
            raise Refused("DOCUMENTED_NOT_ROUNDING: %s explains %.6f m3; a documented deduction is named, never "
                          "called rounding" % ("; ".join(out["named"]), residual_m3))
        raise Refused(f"LABEL_MISMATCH: proposed {label}, the rule gives {out['verdict']}")
    return out


def carried_pair(ledger_lines, candidate_by_id, tol=1e-6):
    """ledger_lines: {line_id: figure the merged ledger bound (None = held there)}. OK only when every line is present
    with the same figure (or still blank where the ledger held it); otherwise RECHECK with the lines that moved."""
    moved = []
    for lid, fig in ledger_lines.items():
        c = candidate_by_id.get(lid)
        if c is None:
            moved.append((lid, "missing"))
            continue
        v = _value(c)
        if (fig is None) != (v is None) or (fig is not None and abs(fig - v) > tol):
            moved.append((lid, f"{fig} -> {v}"))
    return {"status": "RECHECK" if moved else "CARRIED_OK", "moved": moved}
