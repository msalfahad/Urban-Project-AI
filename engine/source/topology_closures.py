"""ZERO-MATERIAL TOPOLOGY CLOSURES (R8.11).

Three things are kept apart:

  A  SOURCE GEOMETRY          what the CAD contains - never rewritten (no end point moved, no entity created)
  B  TOPOLOGY CLOSURE         a derived, reversible relationship used ONLY to establish connectivity / separation
  C  SOURCE CORRECTION CLAIM  a reviewed assertion that the authored geometry itself is wrong (not in R8.11)

A TopologyClosure is B. It carries NO material: it never adds wall length, wall area, plaster, paint or skirting,
and it never changes an opening width. Its only purpose is to stop a topology obstacle's interior (a wall core)
from leaking into occupiable free space.

WALL_END_CLOSURE_V1 (the only derivation in R8.11): an ALIGNED FREE END of an ESTABLISHED wall band (wall_bands)
is closed by the segment between the two FACE END POINTS - the faces' own source coordinates. The closure does not
depend on any cap line's coordinates; drawn caps (of any layer) are corroboration.

Release levels:  TOPOLOGY_CLOSURE_CANDIDATE -> DIAGNOSTIC_PASS -> (REVIEWED) -> AUTHORISED_FOR_SHADOW
                 -> (AUTHORISED_FOR_RELEASE, never in R8.11). TOPOLOGY_CLOSURE_UNRESOLVED when the safety test fails.
A closure is AUTHORISED_FOR_SHADOW by policy only when:
  the band is ESTABLISHED, the end is an ALIGNED_FREE_END, a drawn cap corroborates it (PROVEN or CANDIDATE), and
  the diagnostic safety test passes:
    - the partition of established label occurrences into sites is unchanged (no room splits, none merges, no
      label changes sides)
    - every piece the closure separates from a labelled site is a PURE BAND INTERIOR: bounded only by wall-band
      faces, closures and cross edges parallel to the closure, unlabelled, with no door / glazing closure
    - each labelled site loses exactly the area of the pieces separated from it
Without cap corroboration a passing closure stays DIAGNOSTIC_PASS (reported, never applied).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from . import topology as T
from . import wall_bands as WB

POLICY_ID = "TOPOLOGY_CLOSURE_POLICY_V1"
RULE = "WALL_END_CLOSURE_V1"
ROLE = "TOPOLOGY_CLOSURE"
CANDIDATE = "TOPOLOGY_CLOSURE_CANDIDATE"
DIAGNOSTIC_PASS = "DIAGNOSTIC_PASS"
REVIEWED = "REVIEWED"
AUTHORISED_FOR_SHADOW = "AUTHORISED_FOR_SHADOW"
AUTHORISED_FOR_RELEASE = "AUTHORISED_FOR_RELEASE"
UNRESOLVED = "TOPOLOGY_CLOSURE_UNRESOLVED"
PREFIX = "TCLOSURE|"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class TopologyClosure:
    closure_id: str
    source_revision: str
    region_id: str
    closure_kind: str
    geometry: tuple                     # (x1, y1, x2, y2): the two face end points
    source_evidence_ids: tuple          # (face a, face b, corroborating caps...)
    band_id: str
    derivation_rule: str = RULE
    authority: str = "ENGINE_DERIVED (" + POLICY_ID + ")"
    release: str = CANDIDATE
    physical_material: str = "NONE"
    affects_topology: bool = True
    affects_wall_quantity: bool = False
    affects_finish_quantity: bool = False
    reversible: bool = True
    corroboration: list = field(default_factory=list)
    safety: dict = field(default_factory=dict)

    def as_item(self):
        return T.BoundaryItem(PREFIX + self.closure_id, "SEGMENT", tuple(self.geometry), ROLE)

    def record(self):
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def derive(bands, *, revision_id, region_id) -> list:
    out = []
    for bd in bands:
        if bd.state != WB.ESTABLISHED:
            continue
        for e in bd.ends:
            if e["kind"] != WB.ALIGNED_FREE_END:
                continue
            pa, pb = e["face_a_end"], e["face_b_end"]
            cid = "TC-" + _digest({"rev": revision_id, "region": region_id, "band": bd.band_id, "end": e["end"],
                                   "pa": [round(v, 9) for v in pa], "pb": [round(v, 9) for v in pb]})[:16]
            caps = e.get("drawn_caps", [])
            out.append(TopologyClosure(cid, revision_id, region_id, "WALL_END_CLOSURE", (pa[0], pa[1], pb[0], pb[1]),
                                       tuple(e.get("faces") or (bd.face_a, bd.face_b)) +
                                       tuple(c["source"] for c in caps), bd.band_id,
                                       corroboration=caps))
    return sorted(out, key=lambda c: c.closure_id)


def _sites(items, eps_n):
    arr = T.build(list(items), eps_n)
    return arr, T.sites_of(arr, "DIAGNOSTIC", "DIAGNOSTIC")


def _label_partition(arr, sites, labels):
    by = {}
    for lt in labels:
        sid, _ = T.locate(arr, sites, (lt.x, lt.y), 0.0)
        by.setdefault(sid, set()).add(lt.occurrence)
    return {sid: frozenset(v) for sid, v in by.items() if sid is not None}


def diagnose(items, opening_closures, candidates, labels, bands, *, eps_n, eps_r) -> dict:
    """Run every candidate closure diagnostically (alone) against the arrangement without closures and set its
    release level. The authority arrangement is untouched."""
    base = list(items) + list(opening_closures)
    arr0, s0 = _sites(base, eps_n)
    lab0 = _label_partition(arr0, s0, labels)
    by0 = {s["site_id"]: s for s in s0}
    faces = {x for bd in bands if bd.state == WB.ESTABLISHED
             for x in (getattr(bd, "faces", None) or (bd.face_a, bd.face_b))}     # every member face of the band
    opening_ids = {c.source_id for c in opening_closures}
    out = {}
    for c in candidates:
        arr1, s1 = _sites(base + [c.as_item()], eps_n)
        lab1 = _label_partition(arr1, s1, labels)
        rec = {"label_partition_unchanged": sorted(map(sorted, lab0.values())) == sorted(map(sorted, lab1.values())),
               "separated_pieces": [], "area_balance_ok": True}
        children = {}
        for s in s1:
            pt = T.interior_point(arr1, s["cycle"], eps_r)
            if pt is None:
                continue
            parent, _ = T.locate(arr0, s0, pt, 0.0)
            if parent is not None:
                children.setdefault(parent, []).append(s)
        for parent, kids in children.items():
            if len(kids) < 2:
                continue
            lab_kids = [k for k in kids if any(T.locate(arr1, [k], (lt.x, lt.y), 0.0)[0] == k["site_id"]
                                               for lt in labels)]
            keep_ids = {k["site_id"] for k in lab_kids} or {max(kids, key=lambda z: z["area"])["site_id"]}
            pieces = []
            for k in kids:
                if k["site_id"] in keep_ids:
                    continue
                srcs = set(k["boundary_source_ids"]) | set(k.get("hole_source_ids", ()))
                pure = all(x in faces or x.startswith(PREFIX) or _cross_edge(x, base, c, eps_r)
                           for x in srcs) and not (srcs & opening_ids)
                pieces.append({"area": k["area"], "pure_band_interior": pure, "boundary": sorted(srcs)[:16]})
            kept = [k for k in kids if k["site_id"] in keep_ids]
            removed = sum(p["area"] for p in pieces)
            ok = abs(by0[parent]["area"] - sum(k["area"] for k in kept) - removed) <= eps_r * by0[parent]["perimeter"]
            rec["separated_pieces"] += [dict(p, from_site=parent) for p in pieces]
            rec["area_balance_ok"] = rec["area_balance_ok"] and ok
        rec["passes"] = rec["label_partition_unchanged"] and rec["area_balance_ok"] and \
            all(p["pure_band_interior"] for p in rec["separated_pieces"])
        corroborated = any(x["grade"] in (WB.CAP_PROVEN, WB.CAP_CANDIDATE) for x in c.corroboration)
        c.safety = rec
        c.release = (AUTHORISED_FOR_SHADOW if rec["passes"] and corroborated else
                     DIAGNOSTIC_PASS if rec["passes"] else UNRESOLVED)
        out[c.closure_id] = rec
    return out


def _cross_edge(sid, items, closure, eps):
    """A boundary parallel to the closure (across the band): the wall a band runs into, or a cap."""
    x1, y1, x2, y2 = closure.geometry
    cl = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    for it in items:
        if it.source_id == sid:
            if it.kind != "SEGMENT" or cl == 0.0:
                return False
            a1, b1, a2, b2 = it.geometry
            L = ((a2 - a1) ** 2 + (b2 - b1) ** 2) ** 0.5
            return L > 0 and abs((x2 - x1) * (b2 - b1) - (y2 - y1) * (a2 - a1)) / cl <= eps
    return False


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "rule": RULE, "material": "NONE: never wall length, area or finish",
           "geometry": "the segment between the two face end points of an aligned free end (source coordinates of "
                       "the faces; never a cap's coordinates; never a moved end point)",
           "authorised_for_shadow_requires": ["established band", "aligned free end", "drawn cap corroboration",
                                              "label partition unchanged", "separated pieces are pure band "
                                              "interiors (band faces, closures, cross edges parallel to the closure)",
                                       "area balance"],
           "release_levels": [CANDIDATE, DIAGNOSTIC_PASS, REVIEWED, AUTHORISED_FOR_SHADOW, AUTHORISED_FOR_RELEASE,
                              UNRESOLVED],
           "never": ["distance alone (a near-miss < 50 mm never joins anything)", "a closure between two labelled "
                     "rooms without stronger authority", "an opening width change", "a source edit"]}
    rec["digest"] = _digest(rec)
    return rec
