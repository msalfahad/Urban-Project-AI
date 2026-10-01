"""TRADE TREATMENT ASSIGNMENT AND TRADE MATERIALITY (R8.10).

A physical site may carry several semantic labels. Whether the unresolved boundary between them matters is a
question for each TRADE, never for the topology:

  1  every established label of the site gets a TREATMENT for the trade from an authority record (a project rule,
     an accepted Urban method, an owner claim) - never from a room name by itself, never from a historical quantity
  2  the whole certified site is ONE trade measurement region only when the treatment set is a singleton AND no
     unresolved text could imply another treatment AND no authored trade / finish boundary lies inside the site
     AND the trade treats the objects inside the site identically (object-footprint policy)
       SEMANTIC_SUBDIVISION_NOT_REQUIRED_FOR_TRADE   one treatment: measure the whole site, invent no boundary
       SEMANTIC_SUBDIVISION_REQUIRED                 different treatments: the zone boundary must be established
       TRADE_TREATMENT_UNRESOLVED                    a label or text has no authoritative treatment
  3  an object whose ROLE is unresolved (unknown geometry inside the site) is NON-MATERIAL to a trade when
       - the consequence check proves it cannot separate the site's labels (it is not a partition), AND
       - the trade's object-footprint policy measures the site footprint regardless of objects inside it
     -> ROLE_UNRESOLVED_BUT_NON_MATERIAL_TO_TRADE. Its global role stays unresolved; trade materiality is a separate
     record. Otherwise ROLE_MATERIAL_TO_TRADE (the role decision changes the trade's region).

Duplicate source occurrences (DUPLICATE_SOURCE_OCCURRENCE): two top-level insert occurrences of the same block
whose realised children are geometrically identical. Never deleted. Coincident geometry cannot change an area
topology; a COUNT trade needs its own rule (COUNT_RULE_REQUIRED).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field

from . import canonical_input as CI

POLICY_ID = "TRADE_TREATMENT_POLICY_V1"
NOT_REQUIRED = "SEMANTIC_SUBDIVISION_NOT_REQUIRED_FOR_TRADE"
REQUIRED = "SEMANTIC_SUBDIVISION_REQUIRED"
UNRESOLVED = "TRADE_TREATMENT_UNRESOLVED"
SINGLE_ZONE = "SINGLE_SEMANTIC_ZONE"
NON_MATERIAL = "ROLE_UNRESOLVED_BUT_NON_MATERIAL_TO_TRADE"
MATERIAL = "ROLE_MATERIAL_TO_TRADE"
NOT_DEDUCTED = "OBJECT_FOOTPRINTS_NOT_DEDUCTED"
POLICY_UNRESOLVED = "OBJECT_FOOTPRINT_POLICY_UNRESOLVED"
DUPLICATE = "DUPLICATE_SOURCE_OCCURRENCE"
COUNT_RULE_REQUIRED = "COUNT_RULE_REQUIRED"


@dataclass(frozen=True)
class TradeTreatmentRule:
    """One trade's treatment assignment from ONE authority record."""
    rule_id: str
    version: int
    trade: str                                   # e.g. "FLOOR_FINISH", "CEILING"
    authority: str                               # e.g. "PROJECT_OWNER_RULE", "OWNER_CLAIM", "URBAN_STANDARD"
    source_refs: tuple                           # the records it rests on (rule ids / claim ids), never a quantity
    by_name: dict = field(default_factory=dict)  # established label value -> treatment
    otherwise: str | None = None                 # treatment of every OTHER established label in scope, or None
    object_footprints: str = POLICY_UNRESOLVED   # NOT_DEDUCTED or POLICY_UNRESOLVED
    scope_names: tuple = ()                      # the label values this rule covers at all (empty: all)

    def treatment(self, name):
        if self.scope_names and name not in self.scope_names:
            return None
        return self.by_name.get(name, self.otherwise)


def zone_decision(site_names, rule: TradeTreatmentRule, *, unresolved_texts=(), authored_trade_boundary=False):
    """Trade decision for ONE certified physical site with established label values `site_names` (one entry per
    label occurrence; bilingual stamps already reduced to their names)."""
    names = sorted({n for n in site_names if n})
    treat = {n: rule.treatment(n) for n in names}
    rec = {"rule": f"{rule.rule_id}@v{rule.version}", "trade": rule.trade, "authority": rule.authority,
           "treatments": treat, "unresolved_texts": list(unresolved_texts),
           "authored_trade_boundary": bool(authored_trade_boundary)}
    if not names:
        return dict(rec, state=UNRESOLVED, why="no established label")
    if any(t is None for t in treat.values()):
        return dict(rec, state=UNRESOLVED, why="a label has no authoritative treatment for this trade")
    if unresolved_texts:
        return dict(rec, state=UNRESOLVED, why="an unresolved text in the site could imply another treatment")
    if len(set(treat.values())) > 1:
        return dict(rec, state=REQUIRED, why="different treatments: the zone boundary must be established")
    if authored_trade_boundary:
        return dict(rec, state=REQUIRED, why="an authored trade / finish boundary lies inside the site")
    if len(names) == 1:
        return dict(rec, state=SINGLE_ZONE, why="one semantic zone")
    return dict(rec, state=NOT_REQUIRED, why="every established label has the same treatment for this trade")


def object_materiality(consequence_entry, rule: TradeTreatmentRule) -> dict:
    """Materiality of the UNKNOWN-role objects of one site for one trade. consequence_entry: the site's
    consequence["unknown"] record (effect, sources) from role_authority.separator_analysis, or None."""
    if not consequence_entry or consequence_entry.get("effect") == "NONE":
        return {"state": NON_MATERIAL, "why": "the objects cannot change the site's topology at all", "sources": []}
    src = sorted(consequence_entry.get("sources", []))
    if consequence_entry.get("effect") == "SEPARATES_LABELS":
        return {"state": MATERIAL, "why": "the object could be a partition between the site's labels", "sources": src}
    if rule.object_footprints == NOT_DEDUCTED:
        return {"state": NON_MATERIAL, "sources": src,
                "why": f"{rule.rule_id}: this trade measures the whole physical footprint whatever stands inside it, "
                       "and the object cannot separate the labels"}
    return {"state": MATERIAL, "sources": src,
            "why": f"{rule.rule_id}: no authority says how this trade treats an object footprint; the object's role "
                   "could change the region (e.g. a fixed obstacle vs loose furniture)"}


def duplicate_occurrences(inp: CI.CanonicalMeasurementInput) -> list:
    """Groups of top-level insert occurrences of the same block whose realised children are identical (geometry,
    kind, source layer, nested path below the top level)."""
    kids = defaultdict(list)
    block = {}
    for p in inp.parts:
        path = p.identity.instance_handles or ()
        if not path:
            continue
        kids[path[0]].append((p.kind, p.layer, tuple(path[1:]) and tuple(len(path[1:]) * ["*"]),
                              tuple(round(float(v), 6) for v in p.geometry)))
        if p.lineage:
            block[path[0]] = p.lineage[0].block_name
    sig = defaultdict(list)
    for occ, ks in kids.items():
        d = hashlib.sha256(json.dumps([block.get(occ)] + sorted(map(list, ks)), default=str).encode()).hexdigest()
        sig[d].append(occ)
    out = []
    for d, occs in sorted(sig.items(), key=lambda z: sorted(z[1])):
        if len(occs) > 1:
            occs = sorted(occs, key=lambda h: (len(h), h))
            out.append({"state": DUPLICATE, "occurrences": occs, "block": block.get(occs[0]), "children": len(kids[occs[0]]),
                        "geometry_digest": d, "kept": "ALL (never deleted)",
                        "area_topology": "coincident geometry adds no face: no area effect",
                        "count_trades": COUNT_RULE_REQUIRED})
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "zone_states": [NOT_REQUIRED, REQUIRED, UNRESOLVED, SINGLE_ZONE],
           "object_states": [NON_MATERIAL, MATERIAL], "object_footprint_policies": [NOT_DEDUCTED, POLICY_UNRESOLVED],
           "whole_site_region_requires": ["physical site CERTIFIED for the trade", "every established label has the "
                                          "same authoritative treatment", "no unresolved text could imply another",
                                          "no authored trade / finish boundary inside", "objects treated identically "
                                          "(object-footprint policy) or non-material"],
           "never": ["a treatment from a room name by itself", "a historical BOQ quantity as authority",
                     "a boundary invented between labels", "a global role assigned to release one quantity"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
