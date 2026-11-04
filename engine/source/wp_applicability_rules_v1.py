"""WP_APPLICABILITY_RULES_V1: waterproofing applicability of exposed slab tops, by the physical surface (T-494).

A NEW rule version (Checker finding F-C-T486-1, T-486 verdict 2026-11-03): the existing UP-WP-ROOF-001 (owner,
2026-10-14; knowledge store 1.5.0 effective 1.1.0, purpose 'exterior horizontal surfaces exposed to water', scope
'balconies, terraces and roofs drawn as spaces') is keyed to ROOF / BALCONY / TERRACE spaces. An UNLABELLED slab top
open to the sky (e.g. the slab round a court void over an exterior space) falls outside that scope as written, so
this version states the applicability by exposure. UP-WP-ROOF-001 and every existing rule / knowledge version file are
left unchanged; this module supersedes nothing and is wired into no method (an unwired producer: candidate wiring is a
new ARCH_TAKEOFF_V3.0.x under Checker Gate B).

Authority: the owner rule's own purpose (UP-WP-ROOF-001), UP-WP-003 (0.20 m upturn, owner Q-03 / Q-24), UP-WP-004
(penetrations / interruptions by the detail), UP-WP-DOOR-001 (doorway transitions on their own), UP-WP-MAT-001 (net,
installed and procurement kept apart). The scope extension is agent-derived (T-486 census, Checker-endorsed), NOT an
owner decision: rows it creates carry rule_basis 'R-WP-APPL-EXPOSED-1 (scope extension, provenance T-486)'.

  R-WP-APPL-EXPOSED-1   every slab top OPEN TO THE SKY is a waterproofing zone whatever its label (label never
                        decides): exposed -> the roof membrane applies; COVERED (an element above, closed round) ->
                        NOT_APPLICABLE; covered but open at a side (a ledge under an overhang) or exposure not
                        established -> HELD with its measured area shown as the bound, never added, never 0.
  R-WP-APPL-FUNCTION-1  function names the family, never the membrane: a door opening onto the zone -> terrace /
                        balcony (B8-07); no door -> roof (B8-06); access not established -> HELD family.
  R-WP-APPL-ONCE-1      one physical membrane is one line: membrane m2 that a roof line already carries over the SAME
                        surface is CARRIED, never added; the zone row adds only an uncarried, measured remainder.
  R-WP-APPL-UPTURN-1    the membrane turns up UP-WP-003 0.20 m on every wall, parapet or standing-solid face. Below a
                        window the upturn is on the wall under the sill only when the sill stands at least 0.20 m above
                        the slab top; sill height not established -> that run is HELD (length shown); a sill lower than
                        the upturn, or a door, is a TRANSITION (UP-WP-DOOR-001), never an upturn.
  R-WP-APPL-EDGE-1      a slab edge or a void edge with no wall / parapet is a TERMINATION: length measured, treatment by
                        the detail (UP-WP-004), the treatment row HELD until a detail prints it.
  R-WP-APPL-DRAIN-1     an exposed zone with no outlet and no falls printed raises an RFI row (designer item); the RFI
                        never blocks or zeroes the membrane quantity.

component_rows() turns one measured zone into its BOQ component rows. Units: metres in, m2 / lm / nr out. Standard
library only; geometry arrives already measured (research/agents_t486 zone_geometry or any other measure).
"""

from __future__ import annotations

RULE_VERSION = "WP_APPLICABILITY_RULES_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"   # T-212: computes waterproofing component quantities, wired nowhere yet
UPTURN_H_M = 0.20                          # UP-WP-003 (owner): upturn height; a printed project detail overrides

MEASURED, HELD, NOT_APPLICABLE, CARRIED, RFI = "MEASURED", "HELD", "NOT_APPLICABLE", "CARRIED", "RFI"
FAMILY_ROOF, FAMILY_TERRACE = "B8-06", "B8-07"
EXPOSED, COVERED, COVERED_OPEN_SIDE = "EXPOSED", "COVERED", "COVERED_OPEN_SIDE"
SCOPE_BASIS = "R-WP-APPL-EXPOSED-1 (scope extension of UP-WP-ROOF-001 by its purpose, provenance T-486)"


def _r(x):
    return None if x is None else round(float(x), 6)


def family_of(doors, label=None):
    """R-WP-APPL-FUNCTION-1 -> (family, function); doors None = access not established."""
    if label in ("BALCONY", "TERRACE") or (doors or 0) > 0:
        return FAMILY_TERRACE, "TERRACE_OR_BALCONY"
    if doors is None:
        return None, "ACCESS_UNKNOWN"
    return FAMILY_ROOF, "ROOF"


def _row(zone, comp, unit, qty, status, basis, evidence, **kw):
    r = {"zone_id": zone["zone_id"], "component": comp, "unit": unit, "qty": _r(qty), "status": status,
         "rule_basis": basis, "evidence": list(evidence or ()), "rule_version": RULE_VERSION}
    r.update(kw)
    if status == HELD and qty is not None:
        r["held_bound"] = _r(qty)          # the measured value shown beside a HELD row, never summed
        r["qty"] = None
    return r


def component_rows(zone):
    """one zone -> component rows. zone keys:
    zone_id; exposure EXPOSED / COVERED / COVERED_OPEN_SIDE / None; doors (int or None); label (optional);
    membrane_m2 (flat net, float or None); upturn_runs: list of {run, lm, kind WALL / PARAPET / SOLID / UNDER_WINDOW,
    sill_above_slab_m (UNDER_WINDOW only, None = not established)}; doorways: list of {id, width_m, depth_m};
    open_edge_lm, void_edge_lm (terminations); carried: list of {line_id, m2} (roof lines over the same surface);
    outlet_printed (True / False / None); evidence: {component: [str]}."""
    ev = zone.get("evidence") or {}
    exp = zone.get("exposure")
    fam, func = family_of(zone.get("doors"), zone.get("label"))
    rows = []
    if exp == COVERED:
        rows.append(_row(zone, "FLAT_MEMBRANE", "m2", 0.0, NOT_APPLICABLE, "R-WP-APPL-EXPOSED-1 (covered)",
                         ev.get("FLAT_MEMBRANE"), family=None))
        return rows
    held_zone = exp in (COVERED_OPEN_SIDE, None) or fam is None
    why = ("exposure: covered above, open at a side" if exp == COVERED_OPEN_SIDE else
           "exposure not established" if exp is None else "access not established (family)")
    carried = [dict(c) for c in zone.get("carried") or ()]
    area = zone.get("membrane_m2")
    if held_zone:
        rows.append(_row(zone, "FLAT_MEMBRANE", "m2", area, HELD, SCOPE_BASIS, ev.get("FLAT_MEMBRANE"),
                         family=fam, held_reason=why))
    elif carried:
        if any(c.get("m2") is None for c in carried):
            rows.append(_row(zone, "FLAT_MEMBRANE", "m2", None, HELD, "R-WP-APPL-ONCE-1", ev.get("FLAT_MEMBRANE"),
                             family=fam, held_reason="carried by a HELD roof line", carried_by=carried))
        else:
            cm = sum(c["m2"] for c in carried)
            rows.append(_row(zone, "FLAT_MEMBRANE", "m2", 0.0, CARRIED, "R-WP-APPL-ONCE-1", ev.get("FLAT_MEMBRANE"),
                             family=fam, carried_by=carried, carried_m2=_r(cm),
                             residual_m2=None if area is None else _r(area - cm)))
        return rows
    elif area is None:
        rows.append(_row(zone, "FLAT_MEMBRANE", "m2", None, HELD, SCOPE_BASIS, ev.get("FLAT_MEMBRANE"), family=fam,
                         held_reason="area not measured"))
    else:
        rows.append(_row(zone, "FLAT_MEMBRANE", "m2", area, MEASURED, SCOPE_BASIS, ev.get("FLAT_MEMBRANE"),
                         family=fam, function=func))
    for u in zone.get("upturn_runs") or ():
        kind, lm = u["kind"], u.get("lm")
        base = dict(family=fam, run=u["run"], length_lm=_r(lm), height_m=UPTURN_H_M)
        m2 = None if lm is None else lm * UPTURN_H_M
        if kind == "UNDER_WINDOW":
            s = u.get("sill_above_slab_m")
            if s is None:
                rows.append(_row(zone, "UPTURN", "m2", m2, HELD, "R-WP-APPL-UPTURN-1", ev.get(u["run"]),
                                 held_reason="sill height above the slab top not established", **base))
                continue
            if s < UPTURN_H_M:
                rows.append(_row(zone, "WINDOW_TRANSITION", "lm", lm, HELD, "R-WP-APPL-UPTURN-1 / UP-WP-DOOR-001",
                                 ev.get(u["run"]), held_reason="sill below the upturn height: transition by detail",
                                 family=fam, run=u["run"]))
                continue
        status = HELD if (held_zone or lm is None) else MEASURED
        rows.append(_row(zone, "UPTURN", "m2", m2, status, "R-WP-APPL-UPTURN-1 / UP-WP-003", ev.get(u["run"]),
                         **base, **({"held_reason": why if held_zone else "length not measured"}
                                    if status == HELD else {})))
    for d in zone.get("doorways") or ():
        a = None if d.get("width_m") is None or d.get("depth_m") is None else d["width_m"] * d["depth_m"]
        rows.append(_row(zone, "DOORWAY_TRANSITION", "m2", a, HELD if (held_zone or a is None) else MEASURED,
                         "UP-WP-DOOR-001", ev.get(d["id"]), family=fam, run=d["id"]))
    for comp, key in (("SLAB_EDGE_TERMINATION", "open_edge_lm"), ("VOID_EDGE_TERMINATION", "void_edge_lm")):
        lm = zone.get(key)
        if lm:
            rows.append(_row(zone, comp, "lm", lm, HELD, "R-WP-APPL-EDGE-1 / UP-WP-004", ev.get(comp), family=fam,
                             held_reason="treatment by the detail (none printed)"))
    if not held_zone and zone.get("outlet_printed") is not True:
        rows.append(_row(zone, "DRAINAGE_FALLS", "nr", None, RFI, "R-WP-APPL-DRAIN-1", ev.get("DRAINAGE_FALLS"),
                         family=fam, held_reason=("no outlet / falls printed" if zone.get("outlet_printed") is False
                                                  else "outlet / falls not read"), blocks_quantity=False))
    return rows


def totals(rows):
    """per family and component: MEASURED sum (a value) and the HELD bounds listed separately (never summed in).
    A component with any HELD row reports state PART (measured part AT_LEAST) or HELD (nothing measured)."""
    out = {}
    for r in rows:
        k = (r.get("family") or "UNASSIGNED", r["component"])
        t = out.setdefault(k, {"unit": r["unit"], "measured": 0.0, "measured_rows": 0, "held_rows": 0,
                               "held_bounds": [], "other_rows": 0, "rows": 0})
        t["rows"] += 1
        if r["status"] == MEASURED:
            t["measured"] = round(t["measured"] + r["qty"], 6)
            t["measured_rows"] += 1
        elif r["status"] in (HELD, RFI):
            t["held_rows"] += 1
            if r.get("held_bound") is not None:
                t["held_bounds"].append(r["held_bound"])
        else:
            t["other_rows"] += 1            # CARRIED / NOT_APPLICABLE: adds nothing, by evidence
    for t in out.values():
        if t["held_rows"] == 0:
            t["state"] = "VALUED" if t["measured_rows"] else "NOTHING_TO_ADD"
        else:
            t["state"] = "PART_AT_LEAST" if t["measured_rows"] else "HELD"
        if t["state"] in ("HELD", "NOTHING_TO_ADD") and not t["measured_rows"]:
            t["measured"] = None if t["state"] == "HELD" else 0.0
    return {f"{f}|{c}": v for (f, c), v in sorted(out.items())}


__all__ = ["component_rows", "totals", "family_of", "RULE_VERSION", "UPTURN_H_M", "MEASURED", "HELD",
           "NOT_APPLICABLE", "CARRIED", "RFI", "EXPOSED", "COVERED", "COVERED_OPEN_SIDE", "FAMILY_ROOF",
           "FAMILY_TERRACE"]
