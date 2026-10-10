"""Build QS_MEASUREMENT_REGION_EXPERIMENT_01.

Reads the frozen E1.4 registers. Writes only inside its own directory.
Computes no area and no quantity.

    python3 -m research.qs_measurement_region_experiment_01.build
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from research.qs_measurement_region_experiment_01 import protocol as P

E14 = Path(P.E1_4_DIR)
OUT = Path("data/experiments/QS_MEASUREMENT_REGION_EXPERIMENT_01")

# How a frozen gap class maps onto a TOPOLOGICAL_SITE type. This is a
# RENAMING of evidence E1.4 already established, not a reclassification:
# no gap changes its class here and nothing is re-decided.
GAP_CLASS_TO_SITE = {
    "CONFIRMED_DOOR_PORTAL": "CONFIRMED_DOOR_OPENING",
    "PROBABLE_DOOR_PORTAL": "UNRESOLVED_GAP",
    "MATERIAL_CONTINUITY_GAP": "MATERIAL_CONTINUITY",
    "CAD_JUNCTION_GAP": "MATERIAL_CONTINUITY",
    "OPEN_PHYSICAL_EDGE": "CONFIRMED_OPEN_PASSAGE",
    "UNRESOLVED_GAP": "UNRESOLVED_GAP",
}

# Which chain elements E1.4 already records, and what they are in the
# three-layer vocabulary.
CHAIN_ELEMENT_TO_TOPOLOGICAL_ROLE = {
    "MATERIAL_WALL_FACE": "PHYSICAL_BOUNDARY",
    "EXPOSED_COLUMN_FACE": "PHYSICAL_BOUNDARY",
    "GLAZING_BOUNDARY": "PHYSICAL_BOUNDARY",
    "CURVED_MATERIAL_FACE": "PHYSICAL_BOUNDARY",
    "MATERIAL_CONTINUITY_SPAN": "PHYSICAL_BOUNDARY",
    "DOOR_PORTAL": "OPENING",
    "OPEN_EDGE": "OPEN_PHYSICAL_EDGE",
    "UNRESOLVED_EDGE": "UNRESOLVED_EDGE",
}

# Layer C. Whether an edge contributes to a trade is a statement about the
# PAIR (edge, trade) and is held here, never on the edge's geometry.
# No quantity is computed from these flags in this experiment.
def contribution(role: str) -> dict:
    physical = role == "PHYSICAL_BOUNDARY"
    return {
        "PLASTER_LENGTH_CONTRIBUTION": physical,
        "MATERIAL_LENGTH_CONTRIBUTION": physical,
        "WALL_CERAMIC_LENGTH_CONTRIBUTION": physical,
        "FLOOR_AREA_BOUNDARY_ROLE": role in (
            "PHYSICAL_BOUNDARY", "SYNTHETIC_MEASUREMENT_BOUNDARY"),
        "PLASTER_OPENING_DEDUCTION": role == "OPENING",
    }


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return sha_file(path)


def load(name: str) -> dict:
    return json.loads((E14 / name).read_text("utf-8"))


# ------------------------------------------------------------------
# layer A - the frozen physical model. Read, hashed, never written.
# ------------------------------------------------------------------
def physical_state(chains: dict) -> dict:
    """STATE A: the canonical physical facts this experiment must not move.

    Deliberately NOT a hash of the whole file: it is a hash of exactly the
    physical claims, so that adding a measurement layer beside them can be
    shown to leave them alone.
    """
    rows = []
    for c in chains["CANDIDATES"]:
        ch = c.get("CHAIN") or {}
        rows.append({
            "CANDIDATE_ID": c["CANDIDATE_ID"],
            "BOUNDARY_BASIS": c["BOUNDARY_BASIS"],
            "CLOSED_BY_DRAWN_MATERIAL": ch.get("CLOSED_BY_DRAWN_MATERIAL"),
            "RING_ENCLOSES_THE_POINT":
                (c.get("walk") or {}).get("RING_ENCLOSES_THE_POINT"),
            "chain_is_connected": ch.get("chain_is_connected"),
            "every_chain_end_meets_another":
                ch.get("every_chain_end_meets_another"),
            "material_length_mm": ch.get("material_length_mm"),
            "length_with_no_material_mm":
                ch.get("length_with_no_material_mm"),
            "ELEMENTS": [e["CHAIN_ELEMENT"] for e in (ch.get("CHAIN") or [])],
        })
    rows.sort(key=lambda r: r["CANDIDATE_ID"])
    return {"ROWS": rows, "STATE_HASH": sha_bytes(canon(rows).encode())}


# ------------------------------------------------------------------
# section 7 / 8 - the topological site
# ------------------------------------------------------------------
def opening_sites(gaps: dict, portals: dict) -> list:
    by_portal = {p.get("GAP_ID"): p for p in portals.get("PORTALS", [])
                 if isinstance(p, dict)}
    out = []
    for g in gaps["GAPS"]:
        cls = g["GAP_CLASS"]
        site = GAP_CLASS_TO_SITE.get(cls, "UNRESOLVED_GAP")
        doors = list(g.get("door_entities_in_the_gap") or ())
        hosts = list(g.get("host_wall_faces") or ())
        established = bool(g.get("IS_A_PORTAL")) and bool(
            g.get("confirming_evidence"))
        out.append({
            "SITE_ID": g["GAP_ID"].replace("GAP-", "SITE-"),
            "SOURCE_GAP_ID": g["GAP_ID"],
            "SITE_TYPE": site,
            "FROZEN_GAP_CLASS": cls,
            "THIS_IS_A_RENAMING_NOT_A_RECLASSIFICATION": True,
            # section 7: the void is the site. Ink inside it is optional.
            "THE_SITE_IS_THE_VOID_BETWEEN_TWO_WALL_TERMINATIONS": True,
            "wall_termination_a_mm": g.get("start_mm"),
            "wall_termination_b_mm": g.get("end_mm"),
            "BOTH_ENDPOINTS_ESTABLISHED": bool(
                g.get("start_mm") and g.get("end_mm") and len(hosts) >= 2),
            "host_wall_faces": hosts,
            "HAS_A_DRAWN_ENTITY_INSIDE_THE_VOID": bool(doors),
            "drawn_entities_in_the_void": doors[:12],
            "drawn_entities_in_the_void_count": len(doors),
            "DOOR_GRAPHICS_ARE_NOT_THE_OPENING": (
                "the leaf and the swing are evidence ABOUT the site. They "
                "are not the site, and the site exists without them"),
            "confirming_evidence": list(g.get("confirming_evidence") or ()),
            "probable_evidence": list(g.get("probable_evidence") or ()),
            "gap_mm": g.get("gap_mm"),
            "OPENING_IS_ESTABLISHED": established,
            "ELIGIBLE_FOR_A_MEASUREMENT_CLOSURE": (
                site == "CONFIRMED_DOOR_OPENING" and established
                and bool(g.get("start_mm")) and bool(g.get("end_mm"))),
            "WHY_NOT_ELIGIBLE": (
                None if site == "CONFIRMED_DOOR_OPENING" and established
                else f"site type {site} is not an established opening"),
            "portal_evidence_present": g["GAP_ID"] in by_portal,
        })
    return out


# ------------------------------------------------------------------
# section 3 - closures. Built from sites ALONE, before any region is
# attempted, so this step cannot see whether a region closed.
# ------------------------------------------------------------------
def closures(sites: list, trade: str, basis: str) -> list:
    out = []
    for s in sites:
        if not s["ELIGIBLE_FOR_A_MEASUREMENT_CLOSURE"]:
            continue
        out.append({
            "closure_id": s["SITE_ID"].replace("SITE-", "MC-"),
            "source_opening_id": s["SITE_ID"],
            "endpoint_a": s["wall_termination_a_mm"],
            "endpoint_b": s["wall_termination_b_mm"],
            "source_evidence_ids": s["host_wall_faces"]
                                   + s["drawn_entities_in_the_void"][:4],
            "measurement_basis": basis,
            "applicable_trade": trade,
            **P.CLOSURE_CONSTANTS,
            "status": "CONSTRUCTED",
            "provenance": {
                "FROZEN_GAP_ID": s["SOURCE_GAP_ID"],
                "FROZEN_GAP_CLASS": s["FROZEN_GAP_CLASS"],
                "confirming_evidence": s["confirming_evidence"],
                "E1_4_REGISTER": "E1_4_GAP_ONTOLOGY_REGISTER.json",
            },
            "IT_MAY_NEVER_BE_EVIDENCE_THAT_A_WALL_EXISTS_HERE": True,
        })
    return out


# ------------------------------------------------------------------
# section 5 - can the measurement region be FORMED? No area is computed.
# ------------------------------------------------------------------
def regions(chains: dict, sites: list, closure_ids: set) -> tuple:
    by_gap = {s["SOURCE_GAP_ID"]: s for s in sites}
    eligible_gapless = {s["SITE_ID"] for s in sites
                        if s["ELIGIBLE_FOR_A_MEASUREMENT_CLOSURE"]}
    rows, edges, unresolved = [], [], []

    for c in chains["CANDIDATES"]:
        cid = c["CANDIDATE_ID"]
        ch = c.get("CHAIN") or {}
        chain = ch.get("CHAIN") or []
        walk = c.get("walk") or {}
        els = Counter(e["CHAIN_ELEMENT"] for e in chain)

        # ---- layer C: every edge states both roles, separately -------
        for e in chain:
            role = CHAIN_ELEMENT_TO_TOPOLOGICAL_ROLE.get(
                e["CHAIN_ELEMENT"], "UNRESOLVED_EDGE")
            # E1.4 already puts a DOOR_PORTAL in the chain with no
            # material. In the three-layer reading that element IS a
            # measurement closure wearing a physical-chain costume.
            is_closure = role == "OPENING"
            edges.append({
                "CANDIDATE_ID": cid,
                "SEQ": e["SEQ"],
                "CHAIN_ELEMENT": e["CHAIN_ELEMENT"],
                "TOPOLOGICAL_ROLE": (
                    "SYNTHETIC_MEASUREMENT_BOUNDARY" if is_closure else role),
                "LAYER": (P.LAYER_B if is_closure else P.LAYER_A),
                "length_mm": e.get("length_mm"),
                "material_present": e.get("material_present"),
                "object_id": e.get("object_id"),
                "TRADE_CONTRIBUTION_ROLE": contribution(
                    "SYNTHETIC_MEASUREMENT_BOUNDARY" if is_closure else role),
                "E1_4_wall_length_contribution_mm":
                    e.get("wall_length_contribution_mm"),
            })

        # ---- can a measurement region be formed? ---------------------
        unresolved_edges = els.get("UNRESOLVED_EDGE", 0)
        open_edges = els.get("OPEN_EDGE", 0)
        portals = els.get("DOOR_PORTAL", 0)
        ends_meet = bool(ch.get("every_chain_end_meets_another"))
        ring = bool(walk.get("RING_ENCLOSES_THE_POINT"))

        reasons = []
        if unresolved_edges:
            reasons.append("AN_UNRESOLVED_GAP_LIES_ON_THE_BOUNDARY")
        if open_edges:
            reasons.append("AN_ENDPOINT_OF_AN_OPENING_IS_NOT_ESTABLISHED")
        if not ends_meet:
            reasons.append("THE_BOUNDARY_CHAIN_DOES_NOT_MEET_ITSELF")
        if not ring:
            reasons.append("THE_WALK_ESTABLISHED_NO_RING_AROUND_THE_POINT")

        established = not reasons
        # PHYSICAL closure, with every synthetic element REMOVED. This is
        # the number E1.4 reports as ENCLOSED_BY_DRAWN_MATERIAL, recomputed
        # honestly: a chain that needs a portal to close is not enclosed by
        # drawn material.
        physically_closed = bool(
            ch.get("CLOSED_BY_DRAWN_MATERIAL")) and portals == 0

        row = {
            "CANDIDATE_ID": cid,
            "IDENTITY_AS_DRAWN": c.get("IDENTITY_AS_DRAWN"),
            "PHYSICAL_REGION_STATUS": (
                "CLOSED_BY_DRAWN_MATERIAL" if physically_closed else "OPEN"),
            "PHYSICAL_REGION_REMAINS_OPEN_OR_CONNECTED": not physically_closed,
            "MEASUREMENT_REGION_STATUS": (
                "MEASUREMENT_REGION_CLOSED" if established
                else P.MEASUREMENT_REGION_NOT_ESTABLISHED),
            "E1_4_BOUNDARY_BASIS_AS_FROZEN": c["BOUNDARY_BASIS"],
            "E1_4_CLOSED_BY_DRAWN_MATERIAL_AS_FROZEN":
                ch.get("CLOSED_BY_DRAWN_MATERIAL"),
            "physical_boundary_elements": els.get("MATERIAL_WALL_FACE", 0)
                + els.get("EXPOSED_COLUMN_FACE", 0)
                + els.get("MATERIAL_CONTINUITY_SPAN", 0)
                + els.get("GLAZING_BOUNDARY", 0)
                + els.get("CURVED_MATERIAL_FACE", 0),
            "confirmed_openings_encountered": portals,
            "synthetic_measurement_closures_used": portals,
            "unresolved_gaps_on_the_boundary": unresolved_edges,
            "open_physical_edges": open_edges,
            "CHAIN_ELEMENTS": dict(els),
            "NOT_ESTABLISHED_BECAUSE": reasons or None,
            "NO_AREA_WAS_COMPUTED_FOR_THIS_REGION": True,
        }
        rows.append(row)
        if not established:
            unresolved.append({
                "CANDIDATE_ID": cid,
                "IDENTITY_AS_DRAWN": c.get("IDENTITY_AS_DRAWN"),
                "STATUS": P.MEASUREMENT_REGION_NOT_ESTABLISHED,
                "REASONS": reasons,
                "unresolved_gaps_on_the_boundary": unresolved_edges,
                "IT_WAS_NOT_CLOSED_HEURISTICALLY": True,
                "A19_WAS_NOT_ASKED": True,
                "NO_BENCHMARK_DECIDED_IT": True,
            })
    return rows, edges, unresolved


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    proto_hash = write(OUT / "00_PROTOCOL.json", P.record())

    # ---- section 1: freeze the input state -------------------------
    manifest = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "00_PROTOCOL_SHA256": proto_hash,
        "E1_4_DIR": str(E14),
        "INPUTS_ALLOWED": list(P.INPUTS_ALLOWED),
        "INPUTS_FORBIDDEN": list(P.INPUTS_FORBIDDEN),
        "NOTHING_IS_WRITTEN_BACK": P.NOTHING_IS_WRITTEN_BACK,
        "NO_AREA_IS_COMPUTED": P.NO_AREA_IS_COMPUTED,
        "INPUT_SHA256": {n: sha_file(E14 / n) for n in P.INPUTS_ALLOWED
                         if (E14 / n).exists()},
        "INPUTS_MISSING": [n for n in P.INPUTS_ALLOWED
                           if not (E14 / n).exists()],
    }
    e14_freeze = load("E1_4_FREEZE.json") if (E14 / "E1_4_FREEZE.json").exists() else {}
    manifest["E1_4_FREEZE_AS_FROZEN"] = {
        k: v for k, v in e14_freeze.items()
        if isinstance(v, (str, int, float, bool))}
    man_hash = write(OUT / "INPUT_MANIFEST.json", manifest)

    chains = load("E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
    gaps = load("E1_4_GAP_ONTOLOGY_REGISTER.json")
    portals = load("E1_4_PORTAL_EVIDENCE_REGISTER.json")

    # ---- STATE A ---------------------------------------------------
    state_a = physical_state(chains)
    write(OUT / "PHYSICAL_STATE_HASH.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "STATE": "A_BEFORE_ANY_MEASUREMENT_CONSTRUCT_EXISTS",
        "WHAT_IT_COVERS": (
            "exactly the physical claims this experiment must not move: "
            "per candidate, the boundary basis, whether a ring encloses "
            "the point, whether the chain closes on drawn material, the "
            "material lengths, and the ordered chain-element types"),
        "STATE_HASH": state_a["STATE_HASH"],
        "ROWS": state_a["ROWS"],
    })

    # ---- sites, then closures, then regions. Order is the guarantee.
    sites = opening_sites(gaps, portals)
    site_hash = write(OUT / "OPENING_SITE_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SITE_TYPES": list(P.SITE_TYPES),
        "a_site_may_exist_between_entities":
            P.A_SITE_MAY_EXIST_BETWEEN_ENTITIES,
        "no_new_semantic_classifier": P.NO_NEW_SEMANTIC_CLASSIFIER,
        "sites": len(sites),
        "BY_SITE_TYPE": dict(Counter(s["SITE_TYPE"] for s in sites)),
        "sites_with_a_drawn_entity_in_the_void": sum(
            1 for s in sites if s["HAS_A_DRAWN_ENTITY_INSIDE_THE_VOID"]),
        "sites_with_NO_drawn_entity_in_the_void": sum(
            1 for s in sites if not s["HAS_A_DRAWN_ENTITY_INSIDE_THE_VOID"]),
        "established_openings": sum(
            1 for s in sites if s["OPENING_IS_ESTABLISHED"]),
        "eligible_for_a_measurement_closure": sum(
            1 for s in sites if s["ELIGIBLE_FOR_A_MEASUREMENT_CLOSURE"]),
        "SITES": sites,
    })

    mcs = closures(sites, trade="PLASTER",
                   basis="GROSS_ROOM_PERIMETER_BEFORE_DEDUCTIONS")
    closure_hash = write(OUT / "MEASUREMENT_CLOSURE_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "CLOSURE_FIELDS": list(P.CLOSURE_FIELDS),
        "CLOSURE_CONSTANTS": dict(P.CLOSURE_CONSTANTS),
        "a_closure_may_only_bridge": P.A_CLOSURE_MAY_ONLY_BRIDGE,
        "an_unresolved_gap_may_never_receive_one":
            P.AN_UNRESOLVED_GAP_MAY_NEVER_RECEIVE_ONE,
        "a_closure_may_not_be_inferred_because":
            list(P.A_CLOSURE_MAY_NOT_BE_INFERRED_BECAUSE),
        "the_builder_is_blind_to_whether_it_succeeded":
            P.THE_BUILDER_IS_BLIND_TO_WHETHER_IT_SUCCEEDED,
        "closures_created": len(mcs),
        "unresolved_gaps_offered_and_refused": sum(
            1 for s in sites if s["SITE_TYPE"] == "UNRESOLVED_GAP"),
        "CLOSURES": mcs,
    })

    rows, edges, unresolved = regions(
        chains, sites, {m["closure_id"] for m in mcs})

    region_hash = write(OUT / "MEASUREMENT_REGION_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "both_may_be_true_at_once": P.BOTH_MAY_BE_TRUE_AT_ONCE,
        "one_region_is_not_one_room": P.ONE_REGION_IS_NOT_ONE_ROOM,
        "no_area_is_computed": P.NO_AREA_IS_COMPUTED,
        "candidates": len(rows),
        "ROWS": rows,
    })

    edge_hash = write(OUT / "EDGE_CONTRIBUTION_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_MANDATORY_INVARIANT": P.THE_MANDATORY_INVARIANT,
        "TOPOLOGICAL_ROLES": list(P.TOPOLOGICAL_ROLES),
        "TRADES_CONSIDERED": list(P.TRADES_CONSIDERED),
        "NO_QUANTITY_IS_SUMMED_FROM_THESE_FLAGS": True,
        "edges": len(edges),
        "BY_TOPOLOGICAL_ROLE": dict(
            Counter(e["TOPOLOGICAL_ROLE"] for e in edges)),
        "BY_LAYER": dict(Counter(e["LAYER"] for e in edges)),
        "EDGES": edges,
    })

    unres_hash = write(OUT / "UNRESOLVED_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "failure_is_a_result": P.FAILURE_IS_A_RESULT,
        "NOT_ESTABLISHED_REASONS": list(P.NOT_ESTABLISHED_REASONS),
        "not_established": len(unresolved),
        "BY_REASON": dict(Counter(
            r for u in unresolved for r in u["REASONS"])),
        "ROWS": unresolved,
    })

    print(json.dumps({
        "PROTOCOL_HASH": P.protocol_hash(),
        "STATE_A_HASH": state_a["STATE_HASH"],
        "sites": len(sites),
        "BY_SITE_TYPE": dict(Counter(s["SITE_TYPE"] for s in sites)),
        "closures_created": len(mcs),
        "candidates": len(rows),
        "measurement_regions_closed": sum(
            1 for r in rows
            if r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED"),
        "not_established": len(unresolved),
        "edges": len(edges),
        "SHA256": {"INPUT_MANIFEST": man_hash,
                   "OPENING_SITE_REGISTER": site_hash,
                   "MEASUREMENT_CLOSURE_REGISTER": closure_hash,
                   "MEASUREMENT_REGION_REGISTER": region_hash,
                   "EDGE_CONTRIBUTION_REGISTER": edge_hash,
                   "UNRESOLVED_REGISTER": unres_hash},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
