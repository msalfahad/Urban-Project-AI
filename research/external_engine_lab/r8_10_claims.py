"""R8.10 lab: the two Qortuba owner answers as versioned, source-identity-bound claims (a new evidence version).

    python3 research/external_engine_lab/r8_10_claims.py <work>        # (re)writes data/registry/OWNER_SOURCE_CLAIMS.json

Project semantics live here only. The engine (engine/source/owner_claims.py) knows nothing about Qortuba: it binds
a claim to a revision id + anchor sha, a region + frame, part keys + fingerprints and xref occurrences + facts.

OWNER ANSWER 1 (R8.10 brief §2): the unresolved external-reference occurrences do not contribute physical geometry
to PLAN_VARIANT_4_SELECTED. The occurrences are re-verified from the DXF itself (both, and only these two, exist).
OWNER ANSWER 2 (R8.10 brief §3): DIM-layer lines 7116 / 7117 / 7118 / 7119 are real walls (7116 side: the bathroom
wall; 7119 side: the room wall). Part-scoped: no other DIM entity, no other region, no other revision.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import geometry_role as GR, owner_claims as OC, role_authority as RA      # noqa: E402

C = LAB.C
CLAIMS = ROOT / "data/registry/OWNER_SOURCE_CLAIMS.json"
PREVIOUS = ROOT / "data/registry/OWNER_PROJECT_CLAIMS.json"
PLAN = "PLAN_VARIANT_4_SELECTED"
DIM_WALL_ID = "QORTUBA-NEW-DIM-LINES-7116-7119-ARE-WALLS-OWNER-001"
XREF_ID = "QORTUBA-NEW-XREFS-NONCONTRIBUTING-TO-PLAN-VARIANT-4-OWNER-001"
DIM_HANDLES = ("7116", "7117", "7118", "7119")
XREF_HANDLES = ("16783", "17716")
OLD_WALL_FACE = {"7116": "H467", "7117": "H465", "7118": "H817", "7119": "H513"}     # R8.9 F-R89-02


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def xref_occurrence_facts(dxf: Path, cache: Path | None = None) -> dict:
    """{decimal handle: facts} for EVERY insert of an xref block definition anywhere in the file (model space,
    paper space, nested in blocks), read from the DXF itself."""
    if cache is not None and cache.exists():
        return json.loads(cache.read_text())
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    defs = {b.name: b for b in doc.blocks if b.block_record.is_xref}
    out = {}
    containers = [("LAYOUT:" + lay.name, lay) for lay in doc.layouts] + \
                 [("BLOCK:" + b.name, b) for b in doc.blocks if not b.block_record.is_any_layout]
    for where, cont in containers:
        for e in cont.query("INSERT"):
            if e.dxf.name in defs:
                h = str(int(e.dxf.handle, 16))
                out[h] = {"handle": h, "hex_handle": e.dxf.handle, "xref_name": e.dxf.name,
                          "xref_path": defs[e.dxf.name].block.dxf.get("xref_path"),
                          "flags": defs[e.dxf.name].block.dxf.get("flags"), "container": where,
                          "insert": list(e.dxf.insert)[:2], "scale": [e.dxf.xscale, e.dxf.yscale],
                          "layer": e.dxf.layer}
    out = {k: out[k] for k in sorted(out)}
    if cache is not None:
        cache.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def attach_xref_facts(unrealised: list, facts: dict) -> list:
    return [dict(u, xref=facts[str(u["path"][-1])]) if u["code"] in OC.XREF_CODES and u.get("path")
            and str(u["path"][-1]) in facts else u for u in unrealised]


def make_records(new, facts: dict) -> dict:
    by = {p.identity.source_handle: p for p in new.parts if not p.identity.instance_handles}
    parts = []
    for h in DIM_HANDLES:
        p = by[h]
        assert p.layer == "DIM" and p.kind == "SEGMENT", (h, p.layer, p.kind)
        parts.append({"key": p.identity.key, "handle": h, "source_layer": p.layer, "kind": p.kind,
                      "fingerprint": OC.part_fingerprint(p), "geometry": [round(v, 6) for v in p.geometry],
                      "old_revision_wall_face_on_same_line": OLD_WALL_FACE[h]})
    assert sorted(facts) == sorted(XREF_HANDLES), f"xref occurrences in the file: {sorted(facts)}"
    occ = [{"handle": h, "facts": facts[h], "fingerprint": OC.occurrence_fingerprint(facts[h])} for h in XREF_HANDLES]
    scope = {"project": "QORTUBA", "revision_id": new.revision.revision_id,
             "source_anchor_sha256": new.revision.anchor_sha256, "plan": PLAN, "region_id": new.region_id,
             "frame_id": new.frame_id}
    never = ["another plan variant (PLAN_VARIANT_1..3)", "another floor or sheet", "facade / detail sheets",
             "another source revision or anchor (including the candidate DWG e4babbc2...: identity NOT_ESTABLISHED)",
             "another project", "an Urban company rule"]
    return {
        "SCHEMA": "URBAN_OWNER_SOURCE_CLAIMS_V1",
        "evidence_version": 2,
        "previous_evidence_version": {"version": 1, "file": str(PREVIOUS.relative_to(ROOT)), "sha256": sha(PREVIOUS),
                                      "relation": "UNCHANGED_AND_STILL_ACTIVE (this file adds claims; it supersedes "
                                                  "nothing)"},
        "binding_policy": OC.policy_record(),
        "claims": [
            {"claim_id": DIM_WALL_ID, "version": 1, "kind": OC.PART_ROLE, "role": GR.TOPOLOGY_BOUNDARY,
             "authority": ["PROJECT_OWNER", "SOURCE_STRUCTURE_CORROBORATION"], "review_state": RA.REVIEWED,
             "status": OC.ACTIVE, "supersedes": None, "scope": scope, "parts": parts,
             "owner_statement": "7116, 7117, 7118 and 7119 ARE REAL WALL LINES: drawn on the DIM layer, their "
                                "physical role is WALL",
             "owner_clarification": {"7116": "the wall around the 7116 side is the BATHROOM wall",
                                     "7119": "the wall around the 7119 side is the ROOM wall"},
             "corroboration": "each line lies exactly on a face of a wall the previous revision drew on the WALL "
                              "layer (H467 / H465 / H817 / H513), as two 150 mm face pairs (R8.9 F-R89-02)",
             "changes": "role authority of exactly these four source parts",
             "never_changes": ["source layer (stays DIM)", "geometry / coordinates", "handle", "source identity",
                               "any other DIM entity", "any quantity"],
             "never_transfers_to": never, "author": "Mohammad", "author_role": "PROJECT_OWNER",
             "channel": "R8.10 brief §3 (answer to the R8.9 owner review CONFIRM_QORTUBA_NEW_DIM_LINES_ARE_WALLS)",
             "timestamp": "2026-10-01"},
            {"claim_id": XREF_ID, "version": 1, "kind": OC.XREF_NONCONTRIBUTING, "authority": ["PROJECT_OWNER"],
             "review_state": RA.REVIEWED, "status": OC.ACTIVE, "supersedes": None, "scope": scope,
             "occurrences": occ,
             "verification": {"xref_definitions_in_file": sorted({f["xref_name"] for f in facts.values()}),
                              "xref_occurrences_in_file": sorted(facts),
                              "all_claimed": sorted(facts) == sorted(XREF_HANDLES),
                              "read_from": f"the DXF itself ({new.revision.anchor_sha256[:12]}...), every layout and "
                                           "block"},
             "owner_statement": "the external attached drawings / referenced block files that are not part of the "
                                "selected bottom-most plan are not part of this BOQ scope; they may be ignored for "
                                "this selected measurement region only",
             "meaning": "these exact unresolved external-reference occurrences contribute no physical geometry to "
                        "PLAN_VARIANT_4_SELECTED / the selected region; NOT 'xrefs are irrelevant everywhere'",
             "changes": "source-completeness authority of exactly these occurrences, in this region",
             "never_changes": ["the xref records (kept in provenance)", "any other unresolved / custom / proxy "
                               "entity", "the source-complete state of the file as a whole", "any quantity"],
             "never_transfers_to": never, "author": "Mohammad", "author_role": "PROJECT_OWNER",
             "channel": "R8.10 brief §1-§2 (answer to CONFIRM_QORTUBA_NEW_ATTACHED_XREFS_OUTSIDE_PLAN)",
             "timestamp": "2026-10-01"}]}


def load(path: Path = CLAIMS) -> tuple:
    """(part claims, xref claims, raw record) - the engine dataclasses from the committed evidence file."""
    raw = json.loads(path.read_text())
    parts, xrefs = [], []
    for c in raw["claims"]:
        s = c["scope"]
        if c["kind"] == OC.PART_ROLE:
            parts.append(OC.PartRoleClaim(c["claim_id"], c["version"], s["revision_id"], s["source_anchor_sha256"],
                                          s["region_id"], s["frame_id"],
                                          tuple((p["key"], p["source_layer"], p["fingerprint"]) for p in c["parts"]),
                                          c["role"], tuple(c["authority"]), c["owner_statement"], c["review_state"],
                                          c["status"], c["supersedes"], s["plan"]))
        elif c["kind"] == OC.XREF_NONCONTRIBUTING:
            xrefs.append(OC.XrefScopeClaim(c["claim_id"], c["version"], s["revision_id"], s["source_anchor_sha256"],
                                           s["region_id"], s["frame_id"],
                                           tuple((o["handle"], o["fingerprint"]) for o in c["occurrences"]),
                                           tuple(c["authority"]), c["owner_statement"], c["review_state"],
                                           c["status"], c["supersedes"], s["plan"]))
    return parts, xrefs, raw


def main(work):
    work = Path(work)
    inps = LAB.inputs(work)
    facts = xref_occurrence_facts(LAB.NEW_DXF, work / "xref_facts_new.json")
    rec = make_records(inps["NEW_K2"], facts)
    CLAIMS.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print(CLAIMS, sha(CLAIMS))


if __name__ == "__main__":
    main(sys.argv[1])
