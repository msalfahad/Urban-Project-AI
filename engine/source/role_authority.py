"""ROLE AUTHORITY (R8.9): a role CANDIDATE is not a role AUTHORITY.

R8.8 admitted a topology boundary from layer token + entity type + model-space context, and EXCLUDED geometry from
topology the same way (furniture / dimension / annotation layers). Both directions rest on the layer name alone. On
the new Qortuba revision four lines on a dimension layer lie exactly on the faces of walls the previous revision
drew on the wall layer; the layer-only exclusion silently merged three rooms. This module makes every layer-derived
decision answerable to its CONSEQUENCE and records the authority behind each admitted boundary.

1  Boundary authority grade (per admitted boundary part)
     STRUCTURAL         a derived opening closure, a reviewed source-scoped role claim, or a child of an established
                        building-assembly occurrence (occurrence structure is part of the evidence)
     NETWORK            layer role + entity type + context AND both ends meet other admitted boundaries (within eps_r):
                        it is part of a connected boundary network
     STUB               one end free: it can never split a site (an interior stub; recorded, still a boundary)
     CANDIDATE          neither end meets the network: NOT admitted. It becomes a blocking probe
                        (UNCONNECTED_BOUNDARY_CANDIDATE). A wall-layer line floating inside a room is unexplained.
   A site records the weakest grade among its boundary sources (site authority).

2  Consequence check of layer-only exclusion and of unknown geometry (separator analysis)
     Every OPEN linear part EXCLUDED by a layer-only rule (GR-09 .. GR-16) that bridges the admitted network, alone
     or as a chain (the only excluded linework that could separate), and every linear part of UNKNOWN role is added
     to the admitted set in a second, DIAGNOSTIC arrangement (the authority arrangement is untouched). Per site:
       SEPARATES_LABELS  its label occurrences would end up in different faces (what a wall does)
       CHANGES_AREA      it would split or lose area to an enclosed face
       NONE              it cannot change the site
     unknown + SEPARATES / CHANGES        -> TOPOLOGY_ROLE_UNRESOLVED (physical)
     unknown + NONE                       -> UNKNOWN_OBJECT_IN_SITE (trade only; the physical site stands)
     presentation exclusion (dimension / annotation / frame / hidden layer) + SEPARATES / CHANGES
                                          -> ROLE_CONFLICT_SEPARATOR (physical): presentation linework that would
                                             close a room is not silently ignored
     object exclusion (furniture / fixture / stair / lift layer) + SEPARATES_LABELS -> ROLE_CONFLICT_SEPARATOR
     object exclusion + CHANGES_AREA only -> FIXED_OBJECT_AGAINST_BOUNDARY (a trade NOTE: the role is positively
                                             excluded; whether a finish runs under it is a trade rule)

3  Source-scoped layer role claims
     A claim names one source revision AND its anchor hash, a layer (effective or source), a role, the evidence, its
     authority and review state, a scope, a version and what it supersedes. It applies to NO other source: not
     another project, not another revision of the same project, unless an explicit inheritance names it. A claim
     changes role authority only, never geometry, coordinates or identity: the topology is re-run from it.

4  Building-assembly occurrences
     An insert occurrence is BUILDING_ASSEMBLY only from positive evidence: boundary-layer children (wall / column /
     glazing effective layers) AND at least one independent corroboration: a nested door-symbol occurrence, a
     room-label text child, a dimension child, or a reviewed occurrence-role claim. Never by size. Unknown -> the
     children stay symbol content (fail closed).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from . import canonical_input as CI
from . import geometry_role as GR
from . import topology as T

POLICY_ID = "ROLE_AUTHORITY_POLICY_V1"
STRUCTURAL, NETWORK, STUB, CANDIDATE = "STRUCTURAL", "NETWORK", "STUB", "CANDIDATE"
GRADE_ORDER = {STRUCTURAL: 3, NETWORK: 2, STUB: 1, CANDIDATE: 0}
LAYER_ONLY_EXCLUSION_RULES = ("GR-09", "GR-10", "GR-11", "GR-12", "GR-13", "GR-14", "GR-15", "GR-16")
UNCONNECTED_BOUNDARY_CANDIDATE = "UNCONNECTED_BOUNDARY_CANDIDATE"
ROLE_CONFLICT_SEPARATOR = "ROLE_CONFLICT_SEPARATOR"
UNKNOWN_OBJECT_IN_SITE = "UNKNOWN_OBJECT_IN_SITE"
FIXED_OBJECT_AGAINST_BOUNDARY = "FIXED_OBJECT_AGAINST_BOUNDARY"

BUILDING_ASSEMBLY, SYMBOL, SHEET_FRAME, PRESENTATION, UNKNOWN_OCC = (
    "BUILDING_ASSEMBLY_OCCURRENCE", "SYMBOL_OCCURRENCE", "SHEET_FRAME_OCCURRENCE", "PRESENTATION_OCCURRENCE",
    "UNKNOWN_OCCURRENCE")

# claim review states / authorities
REVIEWED, SOURCE_EVIDENCE_CANDIDATE = "REVIEWED", "SOURCE_EVIDENCE_CANDIDATE"


def policy_record() -> dict:
    return {"id": POLICY_ID, "grades": list(GRADE_ORDER), "layer_only_exclusion_rules": list(LAYER_ONLY_EXCLUSION_RULES),
            "consequences": {
                "unknown geometry, SEPARATES_LABELS or CHANGES_AREA": "TOPOLOGY_ROLE_UNRESOLVED (physical)",
                "unknown geometry, NONE": UNKNOWN_OBJECT_IN_SITE + " (trade only; the physical site stands)",
                "presentation exclusion (GR-13 .. GR-16) that would SEPARATE or CHANGE a site": ROLE_CONFLICT_SEPARATOR
                + " (physical)",
                "object exclusion (GR-09 .. GR-12) that would SEPARATE LABELS": ROLE_CONFLICT_SEPARATOR + " (physical)",
                "object exclusion that would only CHANGE AREA": "FIXED_OBJECT_AGAINST_BOUNDARY (trade note)"},
            "exclusion_candidates": "open curves bridging the admitted network at both ends only",
            "unconnected": UNCONNECTED_BOUNDARY_CANDIDATE,
            "building_assembly_requires": ["boundary-layer children", "one of: nested door occurrence, room-label "
                                           "text child, dimension child, reviewed occurrence claim"],
            "never": ["layer name alone (either direction)", "size", "nearest geometry", "a desired quantity"],
            "claims": "source-scoped (revision id AND anchor hash); never transferred; change role authority only"}


# ======================================================================== source-scoped layer role claims
@dataclass(frozen=True)
class SourceLayerRoleClaim:
    claim_id: str
    source_revision_id: str
    source_anchor_sha256: str
    layer: str
    layer_basis: str                       # "EFFECTIVE" | "SOURCE"
    role: str                              # a geometry_role role
    evidence: tuple
    authority: str                         # e.g. "SOURCE_STRUCTURE", "REVIEWED_HUMAN"
    review_state: str                      # REVIEWED | SOURCE_EVIDENCE_CANDIDATE | ...
    scope: str = "WHOLE_SOURCE_REVISION"   # or a region id
    version: int = 1
    supersedes: str | None = None
    inherits_to: tuple = ()                # explicit (revision id, anchor sha256) pairs only
    part_keys: tuple = ()                  # optional: only these source parts (most specific)


def claim_applies(c: SourceLayerRoleClaim, revision: CI.SourceRevision, region_id=None) -> tuple:
    """(applies, reason). Never by project name, never across revisions unless explicitly inherited."""
    if c.review_state != REVIEWED:
        return False, f"NOT_REVIEWED ({c.review_state}): a candidate claim never changes a role"
    same = (c.source_revision_id == revision.revision_id and c.source_anchor_sha256 == revision.anchor_sha256)
    inherited = (revision.revision_id, revision.anchor_sha256) in tuple(c.inherits_to)
    if not (same or inherited):
        return False, "SOURCE_SCOPE_MISMATCH: the claim names another source revision / anchor"
    if c.scope not in ("WHOLE_SOURCE_REVISION", region_id):
        return False, "REGION_SCOPE_MISMATCH"
    return True, "APPLIES"


def apply_claims(inp: CI.CanonicalMeasurementInput, roles: dict, claims=()) -> tuple:
    """(roles', record). A reviewed, in-scope claim replaces the role of the matching parts (grade STRUCTURAL);
    everything else is recorded with the reason it did not apply."""
    out, rec = dict(roles), []
    for c in sorted(claims, key=lambda z: (z.claim_id, z.version)):
        ok, why = claim_applies(c, inp.revision, inp.region_id)
        hits = []
        if ok:
            for p in inp.parts:
                lay = CI.effective_layer(p)[0] if c.layer_basis == "EFFECTIVE" else p.layer
                if lay == c.layer and (not c.part_keys or p.identity.key in c.part_keys) and p.identity.key in out:
                    old = out[p.identity.key]
                    out[p.identity.key] = GR.RoleAssignment(p.identity.key, c.role, GR.STRUCTURAL,
                                                            "CLAIM:" + c.claim_id,
                                                            dict(old.evidence, CLAIM=c.claim_id, ROLE_BEFORE=old.role))
                    hits.append(p.identity.key)
        rec.append({"claim_id": c.claim_id, "version": c.version, "applies": ok, "reason": why, "parts": len(hits)})
    return out, rec


# ======================================================================== building-assembly occurrences
def occurrence_contexts(inp: CI.CanonicalMeasurementInput, adm: dict, frame_insert, occurrence_claims=None) -> dict:
    """{top-level insert handle: {context, evidence}} from positive evidence only."""
    occurrence_claims = occurrence_claims or {}
    children = defaultdict(list)
    for p in inp.parts:
        path = p.identity.instance_handles or ()
        if path:
            children[path[0]].append(p)
    texts = defaultdict(int)
    for t in inp.texts:
        path = t.identity.instance_handles or ()
        if path:
            texts[path[0]] += 1
    dims = defaultdict(int)
    for d in inp.dimensions:
        path = d.identity.instance_handles or ()
        if path:
            dims[path[0]] += 1
    out = {}
    for occ, ps in sorted(children.items()):
        lr = {GR.layer_role(CI.effective_layer(p)[0]) for p in ps}
        boundary = sorted(r for r in lr if r in GR.BOUNDARY_LAYER_ROLES)
        nested = {p.identity.instance_handles[1] for p in ps if len(p.identity.instance_handles) > 1}
        nested_doors = sorted(n for n in nested if GR.door_signature(
            [q for q in ps if len(q.identity.instance_handles) > 1 and q.identity.instance_handles[1] == n]) is not None)
        ev = {"boundary_layer_children": boundary, "nested_door_occurrences": len(nested_doors),
              "text_children": texts.get(occ, 0), "dimension_children": dims.get(occ, 0),
              "claim": occurrence_claims.get(occ)}
        if frame_insert is not None and occ == frame_insert:
            ctx = SHEET_FRAME
        elif occurrence_claims.get(occ) in (BUILDING_ASSEMBLY, SYMBOL, PRESENTATION):
            ctx = occurrence_claims[occ]
        elif boundary and (nested_doors or texts.get(occ) or dims.get(occ)):
            ctx = BUILDING_ASSEMBLY
        elif boundary:
            ctx = UNKNOWN_OCC                     # wall-layer content without corroboration: fail closed
        else:
            ctx = SYMBOL
        out[occ] = {"context": ctx, "evidence": ev}
    return out


# ======================================================================== boundary authority grades
def _touches(pt, prim, eps):
    if prim.kind == "S":
        return T._proj_seg(pt, prim.a, prim.b)[1] <= eps
    return T._near_on_arc(prim, pt, eps) is not None


def grade_boundaries(items, eps_r) -> dict:
    """{source id: {grade, connected_ends}} for every admitted boundary item (closures: STRUCTURAL)."""
    prims = [T._Prim(i, it) for i, it in enumerate(items)]
    order = sorted(range(len(prims)), key=lambda k: prims[k].bbox[0])
    out = {}
    for i, p in enumerate(prims):
        it = items[i]
        if it.source_id.startswith(("CLOSURE|", "GLAZED|")) or it.role == GR.OPENING_BOUNDARY:
            out[it.source_id] = {"grade": STRUCTURAL, "connected_ends": None}
            continue
        if p.full:
            out[it.source_id] = {"grade": NETWORK, "connected_ends": None}     # a closed curve is its own cycle
            continue
        ends = [p.point(t) for t in p.end_params()]
        n = 0
        for e in ends:
            for j in order:
                q = prims[j]
                if j == i or q.bbox[0] - eps_r > e[0] or q.bbox[2] + eps_r < e[0] or \
                        q.bbox[1] - eps_r > e[1] or q.bbox[3] + eps_r < e[1]:
                    continue
                if _touches(e, q, eps_r):
                    n += 1
                    break
        out[it.source_id] = {"grade": {2: NETWORK, 1: STUB, 0: CANDIDATE}[n], "connected_ends": n}
    return out


# ======================================================================== consequence (separator) analysis
PRESENTATION_EXCLUSION_RULES = ("GR-13", "GR-14", "GR-15", "GR-16")   # dimension / annotation / frame / hidden
OBJECT_EXCLUSION_RULES = ("GR-09", "GR-10", "GR-11", "GR-12")          # furniture / fixture / stair / lift


def separator_analysis(res, items, candidates, *, eps_n, eps_r, labels=()) -> dict:
    """What the candidate geometry WOULD do to each TS01 site if it were boundary (a diagnostic arrangement; the
    authority arrangement is untouched).
    candidates: [(T.BoundaryItem, origin)], origin = the rule that excluded it (GR-09 .. GR-16) or "UNKNOWN".
    Effect per affected site:
      SEPARATES_LABELS  the label occurrences of the site would end up in two or more different faces
      CHANGES_AREA      the site would split or lose area to an enclosed face, labels stay together
      NONE              the geometry cannot change the site (dangling / inside without closing)"""
    if not candidates:
        return {"sites": {}, "candidates": 0}
    arr0, sites0 = res["_arr"], res["sites"]
    origin = {c.source_id: o for c, o in candidates}
    aug = T.build(list(items) + [c for c, _ in candidates], eps_n)
    asites = T.sites_of(aug, "DIAGNOSTIC", "DIAGNOSTIC")
    by_parent = defaultdict(list)
    for a in asites:
        pt = T.interior_point(aug, a["cycle"], eps_r)
        if pt is None:
            continue
        sid, _ = T.locate(arr0, sites0, pt, 0.0)
        if sid is not None:
            by_parent[sid].append(a)
    lab_by_site = defaultdict(list)
    for lt in labels:
        sid, _ = T.locate(arr0, sites0, (lt.x, lt.y), 0.0)
        if sid is not None:
            lab_by_site[sid].append(lt)
    out = {}
    for s in sites0:
        kids = by_parent.get(s["site_id"], [])
        cand_src = sorted({x for a in kids for x in a["boundary_source_ids"] + a["hole_source_ids"] if x in origin})
        if not cand_src:
            continue
        bound = eps_r * s["perimeter"]
        changes = len(kids) >= 2 or abs(kids[0]["area"] - s["area"]) > bound
        holders = defaultdict(set)
        for lt in lab_by_site.get(s["site_id"], []):
            sid2, _ = T.locate(aug, kids, (lt.x, lt.y), 0.0)
            holders[lt.occurrence].add(sid2)
        occs = sorted(holders)
        # two DIFFERENT label occurrences would end in disjoint faces (one stamp split by a line is not two rooms)
        separates = any(not (holders[a] & holders[b]) for i, a in enumerate(occs) for b in occs[i + 1:])
        effect = ("SEPARATES_LABELS" if separates else "CHANGES_AREA" if changes else "NONE")
        hyp = []
        for a in sorted(kids, key=lambda z: -z["area"]):
            inside = sorted({lt.value for lt in lab_by_site.get(s["site_id"], [])
                             if T.locate(aug, [a], (lt.x, lt.y), 0.0)[0] == a["site_id"]})
            hyp.append({"area": a["area"], "labels_inside": inside,
                        "candidate_sources": sorted(x for x in a["boundary_source_ids"] + a["hole_source_ids"]
                                                    if x in origin)})
        out[s["site_id"]] = {"effect": effect, "sources": cand_src,
                             "origins": sorted({origin[x] for x in cand_src}), "hypothetical_sites": hyp}
    return {"sites": out, "candidates": len(candidates)}


def consequence_issue(entry) -> tuple:
    """(issue, level) for one affected site: level PHYSICAL blocks the physical site; TRADE blocks trade use only."""
    origins, effect = set(entry["origins"]), entry["effect"]
    if effect == "NONE":
        return (UNKNOWN_OBJECT_IN_SITE, "TRADE") if "UNKNOWN" in origins else (None, None)
    if "UNKNOWN" in origins:
        return "TOPOLOGY_ROLE_UNRESOLVED", "PHYSICAL"
    if origins & set(PRESENTATION_EXCLUSION_RULES) or effect == "SEPARATES_LABELS":
        return ROLE_CONFLICT_SEPARATOR, "PHYSICAL"
    return FIXED_OBJECT_AGAINST_BOUNDARY, "NOTE"         # positively excluded object against walls: a trade note


def bridging_subset(candidates, admitted_items, eps) -> list:
    """The excluded OPEN linework that bridges the admitted network, alone or as a CHAIN: repeatedly drop every
    candidate with an end touching neither an admitted boundary nor another remaining candidate (dangle pruning).
    Closed curves (dimension dots, symbols) are never separators."""
    admitted = [T._Prim(i, it) for i, it in enumerate(admitted_items)]
    keep = [(c, o) for c, o in candidates if not T._Prim(0, c).full]

    def hit(e, prims):
        return any(q.bbox[0] - eps <= e[0] <= q.bbox[2] + eps and q.bbox[1] - eps <= e[1] <= q.bbox[3] + eps
                   and _touches(e, q, eps) for q in prims)
    while True:
        cps = [T._Prim(i, c) for i, (c, _) in enumerate(keep)]
        nxt = []
        for i, (c, o) in enumerate(keep):
            others = [q for j, q in enumerate(cps) if j != i]
            if all(hit(e, admitted) or hit(e, others) for e in (cps[i].point(t) for t in cps[i].end_params())):
                nxt.append((c, o))
        if len(nxt) == len(keep):
            return nxt
        keep = nxt
