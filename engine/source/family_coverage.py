"""FAMILY COVERAGE (M3) - one record per structural family outside the core six, stating what the generic route
measured, what it found but could not measure, and why (generic, stdlib).

    coverage(D, items, risk, evidence=None) -> [{FAMILY, STATE, QUANTIFIED_IN, EVIDENCE, REASON, NEEDED}]

States:
    QUANTIFIED              items exist for the family (provisional at least)
    PARTLY_QUANTIFIED       items exist and some members of the family are UNRESOLVED
    COUNTED_IN_PARENT       the members are measured inside another family (a ring beam is a beam band, a cantilever
                            slab is a slab panel); no separate line
    DETECTED_NOT_QUANTIFIED the drawing shows the family (labels, detected zones, detail captions) and no measurement
                            exists; the reason names the missing input
    NO_EVIDENCE_FOUND       no label, zone or caption: NOT proof of absence - "confirm absent" before using the totals

Evidence is counts, keywords and sheet ids only; never source text.
"""

from __future__ import annotations

from collections import Counter

POLICY_ID = "FAMILY_COVERAGE_V1"
FAMILIES = ("PLAIN_CONCRETE", "COLUMN_NECKS", "CANTILEVER_PORTIONS", "LINTELS", "LIFT", "POOL", "STAIRS", "DOMES",
            "WATER_TANK", "PARAPETS", "WALLS")
RISK_KINDS = {"COLUMN_NECKS": ("NECK_UNRESOLVED",), "STAIRS": ("SLAB_STAIR_ZONE", "SLAB_PANEL_STAIR_LINES"),
              "PLAIN_CONCRETE": ("BLINDING_UNDER_BEAMS_NOT_ESTABLISHED", "BLINDING_FOOTING_WITHOUT_SIZE")}
NEEDED = {
    "PLAIN_CONCRETE": "the printed blinding thickness (profile BLINDING_THICKNESS_M)",
    "COLUMN_NECKS": "the printed founding depth and neck top level (profile FOUNDING_DEPTH_M, NECK_TOP_LEVEL_M)",
    "CANTILEVER_PORTIONS": "nothing separate: cantilever beams are schedule rows bound as beams, cantilever slabs are "
                           "panels when their free edge is on the beam-edge layer",
    "LINTELS": "the opening widths of the architectural drawings (route G reads the structural DXF only); the lintel "
               "schedule is by opening width",
    "LIFT": "the lift pit / shaft section (wall thickness, pit depth); no generic lift detector",
    "POOL": "the pool section and shell details (wall / floor thickness, depth); the pool shell is not a beam / slab "
            "network on the plans",
    "STAIRS": "the stair section (waist, risers / goings, landing levels); the zones are found and excluded from the "
              "slabs",
    "DOMES": "the dome section (shell thickness, rise); ring beams are measured as beam bands when bound",
    "WATER_TANK": "the tank details (wall / base / cover thickness)",
    "PARAPETS": "the parapet section (height, thickness) and its length on the roof plan",
    "WALLS": "the wall schedule or sections (boundary / retaining / shear walls)",
}


def _labels(scan, fam):
    s = scan.get(fam)
    return f"{s['n_texts']} labels ({', '.join(s['keywords'])}) on {', '.join(s['sheets'])}" if s else ""


def coverage(D, items, risk, scan, evidence=None):
    """scan: generic_route.scope_scan(D). -> one record per FAMILIES entry."""
    rk = Counter(r["KIND"] for r in risk)
    fam_items = Counter((i["family"], i["category"]) for i in items if i["trade"] == "CONCRETE")
    faces = [f for rec in D["sheets"].values() for f in ((rec.get("slab") or {}).get("faces") or [])]
    stair = [f for f in faces if f.get("region") == "STAIR_ZONE"]
    arcs = [b for rec in D["sheets"].values() for b in rec.get("beams", []) if b.get("kind") == "ARC"]
    via_sched = sum(1 for rec in D["sheets"].values() for m in rec.get("marks", [])
                    if m.get("family_from_schedule") and str(m.get("state", "")).startswith("BOUND"))
    caps = Counter(((c.get("caption") or {}).get("family")) for c in (evidence or {}).get("captions", []))
    necks = [i for i in items if i["family"] == "COLUMNS" and i["storey"] == "FOUNDATION" and i["trade"] == "CONCRETE"]
    out = []
    for fam in FAMILIES:
        ev, state, where, reason = [], None, "", ""
        lab = _labels(scan, fam)
        if lab:
            ev.append(lab)
        if fam == "PLAIN_CONCRETE":
            p, u = fam_items[("PLAIN_CONCRETE", "PROVISIONAL")], fam_items[("PLAIN_CONCRETE", "UNRESOLVED")]
            if p:
                state, where = "QUANTIFIED", "PLAIN_CONCRETE"
                reason = "blinding under the measured footings (and beams, when BLINDING_UNDER says so)"
            elif u:
                state, reason = "DETECTED_NOT_QUANTIFIED", "blinding thickness not printed: UNRESOLVED with exposure"
        elif fam == "COLUMN_NECKS":
            if necks:
                n_u = sum(1 for i in necks if i["category"] == "UNRESOLVED")
                state = "PARTLY_QUANTIFIED" if n_u else "QUANTIFIED"
                where = "COLUMNS / FOUNDATION"
                ev.append(f"{len(necks)} necks over footings ({n_u} unresolved)")
                reason = "necks from the foundation-plan columns, height from the printed levels"
        elif fam == "CANTILEVER_PORTIONS":
            if via_sched:
                ev.append(f"{via_sched} plan marks bound through their schedule table's family")
            state, where = ("COUNTED_IN_PARENT", "BEAMS / SLABS") if (via_sched or lab) else (None, "")
            reason = "measured inside the beam and slab families; no separate cantilever line"
        elif fam == "LINTELS":
            if caps.get("LINTEL"):
                ev.append(f"{caps['LINTEL']} lintel captions in the detail evidence")
        elif fam == "STAIRS":
            if stair:
                ev.append(f"{len(stair)} stair zones ({sum(f['area_m2'] for f in stair):.2f} m2) found by their tread "
                          "lines and excluded from the slabs")
        elif fam == "DOMES":
            if arcs:
                nb = sum(1 for b in arcs if b.get("state") == "BOUND")
                ev.append(f"{len(arcs)} curved bands ({nb} bound, measured as beams)")
        if state is None:
            state = "DETECTED_NOT_QUANTIFIED" if ev else "NO_EVIDENCE_FOUND"
            reason = reason or ("drawn or labelled, no generic measurement" if ev else
                                "no label, zone or caption found - not proof of absence: confirm absent before using "
                                "the totals")
        out.append({"FAMILY": fam, "STATE": state, "QUANTIFIED_IN": where, "EVIDENCE": "; ".join(ev),
                    "REASON": reason, "NEEDED": "" if state in ("QUANTIFIED", "COUNTED_IN_PARENT") else NEEDED[fam],
                    "RISK_RECORDS": sum(rk.get(k, 0) for k in RISK_KINDS.get(fam, ()))})
    return out


def policy_record():
    return {"policy": POLICY_ID, "families": list(FAMILIES),
            "rule": "an absent label is never an absent structure: NO_EVIDENCE_FOUND asks for confirmation"}
