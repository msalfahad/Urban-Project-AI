"""QTO RUN MANIFEST (R8.11): every result names the exact inputs, claims, policies and method that produced it.

RUN_INPUT_DIGEST is a deterministic digest of the AUTHORITATIVE run inputs:
  source revision id + anchor sha256, region id, frame id, unit claim id + scale, canonical input digest (every
  record's identity, kind, layer, effective layer, visibility, geometry; texts; dimensions; region review),
  claims OFFERED (id + version + kind) and claims APPLIED (with their per-part / per-occurrence outcome),
  the evidence-version digest, every policy id + digest (geometry role, role authority, text role, semantic zone,
  topology tolerance, cross-check, owner-claim binding, trade treatment, wall band, topology closure, near-miss
  band), the method id + contract version, the closure policy, the decoder route and the installed kernel versions
(package metadata).
NOT in the digest (provenance metadata): the code commit and the timestamp. The code commit is bound separately in
CODE_BOUND_DIGEST: the methodology a result depends on is carried by the policy digests, so the same inputs under
the same policies give the same RUN_INPUT_DIGEST across commits that change nothing that matters.

Offered vs applied: a claim offered but not applicable (scope mismatch, stale fingerprint, not reviewed) is listed
with its outcome and never counts as authority used.

Project-agnostic; stdlib only (kernel versions are read lazily when installed).
"""

from __future__ import annotations

import hashlib
import json

from . import canonical_input as CI
from . import geometry_role as GR
from . import owner_claims as OC
from . import role_authority as RA
from . import semantic_zones as SZ
from . import text_role as TX
from . import topology_closures as TC
from . import topology_crosscheck as XC
from . import topology_policy as TP
from . import trade_regions as TR
from . import wall_bands as WB

SCHEMA = "URBAN_QTO_RUN_MANIFEST_V1"

# R8.12 digest hierarchy: each layer digests the layer below it plus ONLY its own authorities.
TOPOLOGY_LAYER = "TOPOLOGY_RUN_INPUT_DIGEST"   # everything that can change TS01 physical topology (= RUN_INPUT_DIGEST)
ROW_LAYER = "ROW_AUTHORITY_DIGEST"             # + the authorities that decide ONE row's state / value
RELEASE_LAYER = "RELEASE_INPUT_DIGEST"         # + source-anchor state, reviews, release policy / blockers
DIGEST_LAYERS = (TOPOLOGY_LAYER, ROW_LAYER, RELEASE_LAYER)


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def canonical_input_digest(inp: CI.CanonicalMeasurementInput) -> str:
    rev = inp.revision
    return _digest({
        "revision": [rev.revision_id, rev.anchor_sha256] if rev else None, "region": inp.region_id,
        "frame": inp.frame_id, "unit": [inp.unit_native_to_mm, inp.unit_claim_id],
        "parts": sorted([p.identity.key, p.kind, p.layer, list(CI.effective_layer(p)), p.visibility,
                         [repr(float(v)) for v in p.geometry]] for p in inp.parts),
        "texts": sorted([t.identity.key, t.value, repr(t.x), repr(t.y), t.layer, t.visibility] for t in inp.texts),
        "dimensions": sorted([d.identity.key, repr(d.measurement), repr(d.placed_points), d.visibility]
                             for d in inp.dimensions),
        "region_review": sorted(inp.region_review.items())})


def policy_digests() -> dict:
    tx = TX.policy_record()
    ra = RA.policy_record()
    return {
        "geometry_role": [GR.POLICY_ID, GR.policy_record()["digest"]],
        "role_authority": [RA.POLICY_ID, _digest(ra)],
        "text_role": [TX.POLICY_ID, _digest(tx)],
        "semantic_zone": [SZ.POLICY_ID, "ID_ONLY (no policy record)"],
        "topology_tolerance": [TP.POLICY_ID, TP.record()["digest"]],
        "crosscheck": [XC.CHECK_ID, "ID_ONLY (check-only; never a value)"],
        "owner_claim_binding": [OC.POLICY_ID, OC.policy_record()["digest"]],
        "trade_treatment": [TR.POLICY_ID, TR.policy_record()["digest"]],
        "wall_band": [WB.POLICY_ID, WB.policy_record()["digest"]],
        "topology_closure": [TC.POLICY_ID, TC.policy_record()["digest"]],
        "near_miss_review_band_mm": [RA.NEAR_MISS_REVIEW_BAND_MM, "REVIEW_ONLY"]}


def kernel_versions() -> dict:
    """Installed geometry-kernel versions, read as package METADATA (stdlib importlib) - this module never imports
    a kernel itself."""
    import importlib.metadata as md
    out = {}
    for mod in ("ezdxf", "shapely"):
        try:
            out[mod] = md.version(mod)
        except Exception:                                   # pragma: no cover - optional kernels
            out[mod] = "NOT_INSTALLED"
    return out


def loaded_geos_version() -> str:
    """Metadata only (NOT in the digest: it depends on whether a kernel happens to be loaded in this process)."""
    import sys
    sh = sys.modules.get("shapely")
    return ".".join(map(str, sh.geos_version)) if sh is not None and hasattr(sh, "geos_version") else "NOT_LOADED"


def claims_offered_and_applied(owner_claims: dict, unrealised: dict, role_claim_records=()) -> dict:
    parts = owner_claims.get("part_claims", [])
    offered = [{"claim": f"{p['claim_id']}@v{p['version']}", "kind": OC.PART_ROLE} for p in parts] + \
        [{"claim": c, "kind": OC.XREF_NONCONTRIBUTING} for c in owner_claims.get("xref_claims", [])] + \
        [{"claim": f"{r['claim_id']}@v{r['version']}", "kind": "SOURCE_LAYER_ROLE"} for r in role_claim_records
         if not str(r["claim_id"]).startswith(tuple(p["claim_id"] for p in parts))]
    applied, rejected = [], []
    for p in parts:
        entry = {"claim": f"{p['claim_id']}@v{p['version']}", "applied_parts": p["applied_parts"],
                 "outcome": p["state"], "per_part": p["parts"]}
        (applied if p["applied_parts"] else rejected).append(entry)
    used = {}
    for u in (unrealised or {}).get("recorded", []):
        if u.get("claim"):
            used.setdefault(u["claim"], []).append(u["obs_id"])
    for c in owner_claims.get("xref_claims", []):
        (applied if c in used else rejected).append({"claim": c, "occurrences": sorted(used.get(c, [])),
                                                     "outcome": "APPLIES" if c in used else "NOT_APPLIED"})
    for r in role_claim_records:
        if r["claim_id"].startswith(tuple(p["claim_id"] for p in parts)):
            continue
        (applied if r["applies"] and r["parts"] else rejected).append(
            {"claim": f"{r['claim_id']}@v{r['version']}", "outcome": r["reason"], "parts": r["parts"]})
    return {"offered": sorted(offered, key=lambda z: z["claim"]), "applied": sorted(applied, key=lambda z: z["claim"]),
            "rejected": sorted(rejected, key=lambda z: z["claim"])}


def build(inp: CI.CanonicalMeasurementInput, res: dict, *, method_id, contract_version, closure_policy=None,
          provenance=None) -> dict:
    provenance = dict(provenance or {})
    oc = res.get("owner_claims", {})
    claims = claims_offered_and_applied(oc, res.get("unrealised"), (res.get("roles") or {}).get("claims", []))
    rev = inp.revision
    core = {
        "schema": SCHEMA,
        "source_revision_id": rev.revision_id if rev else None,
        "source_anchor_sha256": rev.anchor_sha256 if rev else None,
        "region_id": inp.region_id, "frame_id": inp.frame_id,
        "unit_claim_id": inp.unit_claim_id, "unit_native_to_mm": inp.unit_native_to_mm,
        "canonical_input_digest": canonical_input_digest(inp),
        "claims_offered": claims["offered"], "claims_applied": claims["applied"],
        "claims_rejected": claims["rejected"],
        "evidence_version": oc.get("evidence_version"),
        "policies": policy_digests(),
        "method": {"id": method_id, "contract_version": contract_version, "closure_policy": closure_policy},
        "decoder_route": (inp.notes or {}).get("route"),
        "kernel_versions": kernel_versions()}
    run_input_digest = _digest(core)
    commit = provenance.get("code_commit")
    return dict(core, run_id="RUN-" + run_input_digest[:16], RUN_INPUT_DIGEST=run_input_digest,
                TOPOLOGY_RUN_INPUT_DIGEST=run_input_digest, digest_layer=TOPOLOGY_LAYER,
                code_commit=commit, CODE_BOUND_DIGEST=_digest([run_input_digest, commit]) if commit else None,
                metadata=dict({k: v for k, v in provenance.items() if k != "code_commit"},
                              geos_loaded=loaded_geos_version()),
                not_in_digest=["code_commit", "timestamp", "run_id", "metadata"])


def row_authority_digest(topology_digest, *, row_id, row_method, trade_rules=(), semantic_class_rules=(),
                         footprint_policies=(), row_claims=(), owner_facts_applied=()) -> dict:
    """ROW_AUTHORITY_DIGEST: the topology digest + the authorities that decided this row. A fact that is only
    CORROBORATING (the engine established the same reading) is listed outside the digest: it changed no row."""
    core = {"layer": ROW_LAYER, "topology": topology_digest, "row": row_id, "method": row_method,
            "trade_rules": sorted(map(str, trade_rules)), "semantic_class_rules": sorted(map(str, semantic_class_rules)),
            "footprint_policies": sorted(map(str, footprint_policies)), "row_claims": sorted(map(str, row_claims)),
            "owner_facts_applied": sorted(map(str, owner_facts_applied))}
    return dict(core, digest=_digest(core))


def release_input_digest(row_digest, *, source_anchor_state, reviews=(), release_policy=None, release_blockers=(),
                         owner_facts_applied=()) -> dict:
    """RELEASE_INPUT_DIGEST: the row authority digest + everything a release decision reads."""
    core = {"layer": RELEASE_LAYER, "row": row_digest, "source_anchor_state": source_anchor_state,
            "reviews": sorted(map(str, reviews)), "release_policy": release_policy,
            "release_blockers": sorted(map(str, release_blockers)),
            "owner_facts_applied": sorted(map(str, owner_facts_applied))}
    return dict(core, digest=_digest(core))

