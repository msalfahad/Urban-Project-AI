"""OWNER / SOURCE CLAIMS BOUND TO SOURCE IDENTITY (R8.10).

An owner answer enters the evidence loop only as a versioned claim with an explicit scope, and it never edits a
record: it changes ROLE AUTHORITY (part claims) or SOURCE-COMPLETENESS AUTHORITY (xref claims) and nothing else.
Source layer, geometry, coordinates, handle and identity stay exactly as the source has them.

Applicability is decided by SOURCE IDENTITY, never by coordinates:

  revision id + anchor sha256      a claim never transfers to another revision (or another anchor of "the same"
                                   revision, e.g. a DWG whose identity with the DXF is not established)
  region id + frame id (the plan)  a claim never transfers to another plan variant, floor or sheet
  part key + fingerprint           each claimed part is named by its source key (handle, sub-part); the claim also
                                   records a fingerprint of the part's kind, source layer and exact geometry. A part
                                   whose key is gone is PART_NOT_IN_SOURCE; a part whose key is present but whose
                                   fingerprint differs is STALE_PART_FINGERPRINT. Neither applies, and nothing ever
                                   binds to "whatever now occupies the same coordinates"
  occurrence handle + facts        an xref claim names each insert occurrence and the source facts of it (xref
                                   name, path, insert point, scale, layer). Different facts -> OCCURRENCE_FACTS_MISMATCH

Xref completeness (four states; there is no generic IGNORE_XREF setting):

  XREF_PRESENT_AND_ADMITTED                    the referenced content is in the source and was realised
  XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION       content missing, but positive placement evidence puts it outside
  XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING content missing; a reviewed owner claim for THIS occurrence, THIS
                                               revision and THIS region says it contributes no physical geometry
  XREF_MISSING_POTENTIALLY_CONTRIBUTING        anything else: blocks the region

Only the first three let the selected region continue. A cleared occurrence stays in provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import canonical_input as CI
from . import role_authority as RA

POLICY_ID = "OWNER_CLAIM_BINDING_POLICY_V1"
PART_ROLE = "PART_ROLE"
XREF_NONCONTRIBUTING = "XREF_NONCONTRIBUTING_TO_SELECTED_REGION"
ACTIVE = "ACTIVE"

APPLIES = "APPLIES"
NOT_ACTIVE = "CLAIM_NOT_ACTIVE"
NOT_REVIEWED = "CLAIM_NOT_REVIEWED"
SOURCE_SCOPE_MISMATCH = "SOURCE_SCOPE_MISMATCH"
REGION_SCOPE_MISMATCH = "REGION_SCOPE_MISMATCH"
PLAN_SCOPE_MISMATCH = "PLAN_SCOPE_MISMATCH"
PART_NOT_IN_SOURCE = "PART_NOT_IN_SOURCE"
STALE_PART_FINGERPRINT = "STALE_PART_FINGERPRINT"
OCCURRENCE_NOT_CLAIMED = "OCCURRENCE_NOT_CLAIMED"
OCCURRENCE_FACTS_MISMATCH = "OCCURRENCE_FACTS_MISMATCH"

XREF_PRESENT_AND_ADMITTED = "XREF_PRESENT_AND_ADMITTED"
XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION = "XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION"
XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING = "XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING"
XREF_MISSING_POTENTIALLY_CONTRIBUTING = "XREF_MISSING_POTENTIALLY_CONTRIBUTING"
XREF_STATES = (XREF_PRESENT_AND_ADMITTED, XREF_MISSING_BUT_PROVEN_OUTSIDE_REGION,
               XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING, XREF_MISSING_POTENTIALLY_CONTRIBUTING)
XREF_CONTINUES = frozenset(XREF_STATES[:3])
XREF_CODES = ("XREF_CONTENT_NOT_IN_SOURCE", "XREF_NOT_RESOLVED", "XREF_UNLOADED")


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def part_fingerprint(part) -> str:
    """Kind, source layer, source handle and exact geometry (rounded to 1e-6 native units, far below any authored
    precision) of one source part."""
    return _digest({"kind": part.kind, "layer": part.layer, "handle": part.identity.source_handle,
                    "geometry": [round(float(v), 6) for v in part.geometry]})


def occurrence_fingerprint(facts: dict) -> str:
    keep = {k: facts.get(k) for k in ("handle", "xref_name", "xref_path", "insert", "scale", "layer")}
    if keep.get("insert") is not None:
        keep["insert"] = [round(float(v), 6) for v in keep["insert"]]
    if keep.get("scale") is not None:
        keep["scale"] = [round(float(v), 9) for v in keep["scale"]]
    return _digest(keep)


# ======================================================================== part-scoped role claims
@dataclass(frozen=True)
class PartRoleClaim:
    claim_id: str
    version: int
    source_revision_id: str
    source_anchor_sha256: str
    region_id: str
    frame_id: str
    parts: tuple                      # ((part key, source layer, fingerprint), ...)
    role: str                         # a geometry_role role
    authority: tuple                  # e.g. ("PROJECT_OWNER", "SOURCE_STRUCTURE_CORROBORATION")
    statement: str
    review_state: str = RA.REVIEWED
    status: str = ACTIVE
    supersedes: str | None = None
    plan_label: str | None = None


def _scope(c, inp):
    if c.status != ACTIVE:
        return NOT_ACTIVE
    if c.review_state != RA.REVIEWED:
        return NOT_REVIEWED
    rev = inp.revision
    if rev is None or (c.source_revision_id, c.source_anchor_sha256) != (rev.revision_id, rev.anchor_sha256):
        return SOURCE_SCOPE_MISMATCH
    if c.region_id != inp.region_id:
        return REGION_SCOPE_MISMATCH
    if c.frame_id != inp.frame_id:
        return PLAN_SCOPE_MISMATCH
    return APPLIES


def part_claim_status(c: PartRoleClaim, inp: CI.CanonicalMeasurementInput) -> dict:
    scope = _scope(c, inp)
    by = {p.identity.key: p for p in inp.parts}
    per = []
    for key, layer, fp in c.parts:
        p = by.get(key)
        if scope != APPLIES:
            st = scope
        elif p is None:
            st = PART_NOT_IN_SOURCE
        elif part_fingerprint(p) != fp or p.layer != layer:
            st = STALE_PART_FINGERPRINT
        else:
            st = APPLIES
        per.append({"part": key, "state": st})
    ok = [x["part"] for x in per if x["state"] == APPLIES]
    return {"claim_id": c.claim_id, "version": c.version, "scope_state": scope,
            "state": APPLIES if ok and len(ok) == len(per) else (scope if scope != APPLIES else
                                                                 "PARTIAL_OR_STALE" if ok else STALE_PART_FINGERPRINT),
            "parts": per, "applied_parts": ok}


def role_claims(claims, inp: CI.CanonicalMeasurementInput) -> tuple:
    """(role_authority claims for the parts that apply, status records). Each applying part becomes a reviewed
    part-keyed SourceLayerRoleClaim on its own SOURCE layer: the record itself is never touched."""
    out, rec = [], []
    for c in sorted(claims, key=lambda z: (z.claim_id, z.version)):
        st = part_claim_status(c, inp)
        rec.append(st)
        layers = {layer for key, layer, _ in c.parts if key in st["applied_parts"]}
        for layer in sorted(layers):
            keys = tuple(sorted(k for k, lay, _ in c.parts if lay == layer and k in st["applied_parts"]))
            out.append(RA.SourceLayerRoleClaim(
                f"{c.claim_id}@v{c.version}", c.source_revision_id, c.source_anchor_sha256, layer, "SOURCE", c.role,
                ("PART_SCOPED_CLAIM",) + tuple(c.authority), "+".join(c.authority), RA.REVIEWED, c.region_id,
                c.version, c.supersedes, (), keys))
    return out, rec


# ======================================================================== xref occurrence claims
@dataclass(frozen=True)
class XrefScopeClaim:
    claim_id: str
    version: int
    source_revision_id: str
    source_anchor_sha256: str
    region_id: str
    frame_id: str
    occurrences: tuple                # ((occurrence handle, occurrence fingerprint), ...)
    authority: tuple
    statement: str
    review_state: str = RA.REVIEWED
    status: str = ACTIVE
    supersedes: str | None = None
    plan_label: str | None = None
    kind: str = XREF_NONCONTRIBUTING


def xref_state(u: dict, claims, inp: CI.CanonicalMeasurementInput) -> tuple:
    """(state, claim id or None, reason) for one MISSING xref occurrence record `u` (code in XREF_CODES; u["path"]
    names the occurrence; u["xref"] carries the source facts of the insert, or is absent)."""
    path = tuple(u.get("path") or ())
    occ = path[-1] if path else None
    facts = u.get("xref")
    reasons = []
    for c in sorted(claims, key=lambda z: (z.claim_id, z.version)):
        scope = _scope(c, inp)
        if scope != APPLIES:
            reasons.append(f"{c.claim_id}: {scope}")
            continue
        named = dict(c.occurrences)
        if occ not in named:
            reasons.append(f"{c.claim_id}: {OCCURRENCE_NOT_CLAIMED}")
            continue
        if facts is None or occurrence_fingerprint(facts) != named[occ]:
            reasons.append(f"{c.claim_id}: {OCCURRENCE_FACTS_MISMATCH}")
            continue
        return XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING, f"{c.claim_id}@v{c.version}", "APPLIES"
    return XREF_MISSING_POTENTIALLY_CONTRIBUTING, None, "; ".join(reasons) or "no claim names this occurrence"


def evidence_version(*claim_sets) -> str:
    """Digest of every claim that entered a run (ids, versions, scopes, parts / occurrences): every derived result
    carries it, so a result always says which claim versions produced it."""
    flat = []
    for cs in claim_sets:
        for c in cs:
            flat.append({k: getattr(c, k) for k in c.__dataclass_fields__})
    return _digest(sorted(flat, key=lambda z: json.dumps(z, sort_keys=True, default=str)))


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "binding": ["revision id + anchor sha256", "region id + frame id", "part key + fingerprint",
                       "occurrence handle + source facts"],
           "never": ["coordinates alone", "layer-wide inference from part claims", "transfer to another revision, "
                     "anchor, plan, region or project", "editing a record (layer, geometry, handle, identity)",
                     "a quantity"],
           "part_states": [APPLIES, PART_NOT_IN_SOURCE, STALE_PART_FINGERPRINT, SOURCE_SCOPE_MISMATCH,
                           REGION_SCOPE_MISMATCH, PLAN_SCOPE_MISMATCH, NOT_REVIEWED, NOT_ACTIVE],
           "xref_states": list(XREF_STATES), "xref_states_that_continue": sorted(XREF_CONTINUES)}
    rec["digest"] = _digest(rec)
    return rec


def xref_inventory(occurrence_facts: dict, unrealised_result: dict) -> dict:
    """{occurrence handle: four-state record} for every xref occurrence the SOURCE contains (occurrence_facts, read
    from the source itself). An occurrence with no unrealised record had its content realised:
    XREF_PRESENT_AND_ADMITTED. Otherwise its disposition from the unrealised accounting is its state."""
    disp = {}
    for kind in ("recorded", "blocking_input"):
        for u in unrealised_result.get(kind, []):
            if u.get("code") in XREF_CODES and u.get("path"):
                disp[str(u["path"][-1])] = (u["disposition"], u.get("claim"), kind)
    out = {}
    for h in sorted(occurrence_facts):
        d, claim, kind = disp.get(h, (XREF_PRESENT_AND_ADMITTED, None, "realised"))
        if d not in XREF_STATES:
            d = XREF_MISSING_POTENTIALLY_CONTRIBUTING if kind == "blocking_input" else d
        out[h] = {"state": d, "continues": d in XREF_CONTINUES, "claim": claim,
                  "facts": occurrence_facts[h], "provenance": "kept"}
    return out
