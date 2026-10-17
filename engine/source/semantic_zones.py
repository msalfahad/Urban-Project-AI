"""PHYSICAL SPACE != SEMANTIC ZONE != TRADE MEASUREMENT REGION (R8.9).

    PHYSICAL_TOPOLOGICAL_SITE   TS01: what physical space is connected (topology, certificate, role authority)
    SEMANTIC_ZONE_CANDIDATE     which named / functional zones exist inside it (label occurrences + subdivision
                                evidence)
    TRADE_MEASUREMENT_REGION    what region a trade measures (later trade rules decide; here: the object and its
                                blockers)

They are separate objects with separate ids and separate authority. TS01 never splits a physical site because it
carries several labels; an open plan (HALL + DINING + RECEPTION, M.B.ROOM + DRESS) is not an error.

Subdivision of one physical site into several semantic zones needs POSITIVE source evidence: an authored
SEMANTIC_BOUNDARY line (finish / zone / threshold layer, geometry_role GR-18) that would put the label occurrences
into different faces, or a reviewed zone claim. Never two labels alone, wet-wins, first / largest / nearest label,
an assumed rectangle, a benchmark or a desired total.

States of a physical site (the R8.9 interpretation classes):
    UNLABELLED                                              no established room label
    ONE_PHYSICAL_SPACE_ONE_SEMANTIC_ZONE                    one label occurrence: the zone is the whole site
    ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_ESTABLISHED  subdivision evidence separates every label occurrence
    ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED   several labels, no subdivision evidence
                                                            (MULTI_SEMANTIC_PHYSICAL_SPACE: affected trades blocked)
    TOPOLOGY_BOUNDARY_MISSING_FROM_ROLE_ADMISSION           several labels AND excluded linework would separate them
                                                            (ROLE_CONFLICT_SEPARATOR): a role question, not a
                                                            semantic one

THRESHOLD / OPENING SITES: TS01's OPENING_SITE (the zone between the two closures of a proven opening) is kept as
its own object with its area and the sites on either side. Its trade allocation (side A, side B, own finish zone,
continuous finish) is a later TRADE RULE: TRADE_RULE_REQUIRED unless an authoritative Urban rule answers it.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib

from . import geometry_role as GR
from . import role_authority as RA
from . import topology as T

POLICY_ID = "SEMANTIC_ZONE_POLICY_V1"
UNLABELLED = "UNLABELLED"
ONE_ZONE = "ONE_PHYSICAL_SPACE_ONE_SEMANTIC_ZONE"
MULTI_ESTABLISHED = "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_ESTABLISHED"
MULTI_UNRESOLVED = "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED"
BOUNDARY_MISSING = "TOPOLOGY_BOUNDARY_MISSING_FROM_ROLE_ADMISSION"
MULTI_SEMANTIC_PHYSICAL_SPACE = "MULTI_SEMANTIC_PHYSICAL_SPACE"
TRADE_RULE_REQUIRED = "TRADE_RULE_REQUIRED"
ALLOCATION_STATES = ("ALLOCATED_TO_SIDE_A", "ALLOCATED_TO_SIDE_B", "SEPARATE_FINISH_ZONE", "SAME_FINISH_CONTINUOUS",
                     TRADE_RULE_REQUIRED)


def _id(prefix, *parts):
    return prefix + "-" + hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def build(res, items, semantic_candidates, labels, *, eps_n, eps_r, zone_claims=None) -> dict:
    """{zones, sites (state per physical site), thresholds} - deterministic.
    semantic_candidates: [T.BoundaryItem] of role SEMANTIC_BOUNDARY (authored finish / zone lines)."""
    zone_claims = zone_claims or {}
    sub = RA.separator_analysis(res, items, [(c, "GR-18") for c in semantic_candidates], eps_n=eps_n, eps_r=eps_r,
                                labels=labels)["sites"]
    occ_values = {}
    for lt in labels:
        occ_values.setdefault(lt.occurrence, []).append(lt.value)
    zones, states = [], {}
    for s in res["sites"]:
        sid, occs = s["site_id"], sorted(s["labels"])
        if s.get("kind") == T.OPENING_SITE:
            continue
        if not occs:
            states[sid] = {"state": UNLABELLED}
            continue
        if len(occs) == 1:
            states[sid] = {"state": ONE_ZONE}
            zones.append({"zone_id": _id("ZONE", sid, occs[0]), "physical_site_id": sid, "label_occurrences": occs,
                          "label_values": sorted(occ_values.get(occs[0], [])), "geometry": "WHOLE_PHYSICAL_SITE",
                          "area": s["area"], "authority": "ONE_LABEL_OCCURRENCE", "state": "ESTABLISHED"})
            continue
        e = sub.get(sid)
        if RA.ROLE_CONFLICT_SEPARATOR in s["issues"]:
            st = BOUNDARY_MISSING
        elif sid in zone_claims:
            st = MULTI_ESTABLISHED
        elif e and e["effect"] == "SEPARATES_LABELS" and _every_occurrence_alone(e, s, labels, occ_values):
            st = MULTI_ESTABLISHED
        else:
            st = MULTI_UNRESOLVED
        states[sid] = {"state": st, "subdivision_evidence": e and {"effect": e["effect"], "sources": e["sources"]}}
        for o in occs:
            area = None
            if st == MULTI_ESTABLISHED and e:
                hits = [h["area"] for h in e["hypothetical_sites"]
                        if set(occ_values.get(o, [])) & set(h["labels_inside"])]
                area = hits[0] if len(hits) == 1 else None
            zones.append({"zone_id": _id("ZONE", sid, o), "physical_site_id": sid, "label_occurrences": [o],
                          "label_values": sorted(occ_values.get(o, [])),
                          "geometry": "SUBDIVISION_FACE" if area is not None else "UNRESOLVED_WITHIN_PHYSICAL_SITE",
                          "area": area, "authority": ("SEMANTIC_BOUNDARY_EVIDENCE" if area is not None
                                                      else MULTI_SEMANTIC_PHYSICAL_SPACE),
                          "state": "ESTABLISHED" if area is not None else "UNRESOLVED"})
    adj = {a["opening"]: a["sites"] for a in res.get("opening_adjacency", [])}
    thresholds = []
    for s in res["sites"]:
        if s.get("kind") == T.OPENING_SITE:
            sides = adj.get(s.get("opening_of"), [])
            thresholds.append({"threshold_id": _id("THRESHOLD", s["site_id"]), "physical_site_id": s["site_id"],
                               "opening": s.get("opening_of"), "area": s["area"], "sides": sides,
                               "allocation": TRADE_RULE_REQUIRED,
                               "why": "which side's finish covers the strip is a trade rule; no authoritative Urban "
                                      "rule answers it, and TS01 never moves it into a room to match a total"})
    return {"policy": POLICY_ID, "zones": zones, "sites": states, "thresholds": thresholds}


def _every_occurrence_alone(e, s, labels, occ_values):
    """Every label occurrence of the site ends in a subdivision face holding no other occurrence."""
    faces = [set(h["labels_inside"]) for h in e["hypothetical_sites"]]
    for o in s["labels"]:
        mine = set(occ_values.get(o, []))
        others = set().union(*(set(occ_values.get(x, [])) for x in s["labels"] if x != o)) if len(s["labels"]) > 1 \
            else set()
        if not any(mine & f and not (others & f) for f in faces):
            return False
    return True


def trade_regions(zone_out, res, trade) -> list:
    """TRADE_MEASUREMENT_REGION candidates for one trade: one per established zone, with every blocker that applies
    (the physical site's physical issues, the zone's semantic state, trade issues of objects inside). The trade
    RULE (what is measured, deductions, allocation) is not decided here."""
    by_site = {s["site_id"]: s for s in res["sites"]}
    out = []
    for z in zone_out["zones"]:
        s = by_site[z["physical_site_id"]]
        blockers = []
        if s.get("physical_issues"):
            blockers.append({"class": "BLOCKED_ROLE" if {"TOPOLOGY_ROLE_UNRESOLVED", RA.ROLE_CONFLICT_SEPARATOR}
                             & set(s["physical_issues"]) else "BLOCKED_PHYSICAL", "issues": s["physical_issues"]})
        if z["state"] != "ESTABLISHED":
            blockers.append({"class": "BLOCKED_SEMANTIC_ZONE", "issues": [MULTI_SEMANTIC_PHYSICAL_SPACE]})
        sem = [i for i in s.get("semantic_issues", []) if i != T.MULTIPLE_SEMANTIC_LABELS]
        if sem:
            blockers.append({"class": "BLOCKED_SEMANTIC_ZONE", "issues": sem})
        if s.get("trade_issues"):
            blockers.append({"class": "BLOCKED_TRADE_RULE", "issues": s["trade_issues"]})
        out.append({"region_id": _id("TMR", z["zone_id"], trade), "trade": trade, "zone_id": z["zone_id"],
                    "physical_site_id": z["physical_site_id"], "area": z["area"], "blockers": blockers,
                    "trade_notes": s.get("trade_notes", []),
                    "state": "READY_FOR_TRADE_RULE" if not blockers else "BLOCKED"})
    return out


def obstacle_interiors(res, roles) -> dict:
    """{site id: evidence} for unlabelled sites whose EVERY boundary source is a STRUCTURAL_OBSTACLE (a column
    outline): the inside of the obstacle, not free space. Never by area, width or thickness. The core between the
    two faces of a double-line wall is NOT classified here (the faces of one wall are not identified as one source
    object): it stays an unlabelled site."""
    out = {}
    for s in res["sites"]:
        if s["labels"] or s.get("kind") == T.OPENING_SITE:
            continue
        src = set(s["boundary_source_ids"]) | set(s["hole_source_ids"])
        rs = {roles[x].role for x in src if x in roles}
        if src and all(x in roles for x in src) and rs == {GR.STRUCTURAL_OBSTACLE}:
            out[s["site_id"]] = {"kind": "OBSTACLE_INTERIOR", "obstacle_sources": sorted(src),
                                 "rule": "every enclosing edge is a STRUCTURAL_OBSTACLE source"}
    return out
