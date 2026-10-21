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

POLICY_ID = "TRADE_TREATMENT_POLICY_V2"   # V2 (R8.11): semantic classes, object-footprint policies
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


# ======================================================================== R8.11: semantic class authority
@dataclass(frozen=True)
class SemanticClassRule:
    """Exact source label text -> SPACE CLASS, from one authority record, within one scope. Display text is never
    the generic identity: a spelling not listed here (other case, other spacing, a typo) maps to NOTHING."""
    rule_id: str
    version: int
    authority: str
    source_refs: tuple
    scope: dict
    by_label: dict = field(default_factory=dict)      # exact label text -> class
    otherwise_class: str | None = None                # class of every OTHER label in `scope_labels`
    scope_labels: tuple = ()                          # the label texts this rule covers at all

    def space_class(self, label):
        if label in self.by_label:
            return self.by_label[label]
        if self.otherwise_class and label in self.scope_labels:
            return self.otherwise_class
        return None


def class_treatments(site_labels, class_rule: SemanticClassRule, by_class: dict) -> dict:
    """{label: (space class, treatment)} - treatment through the authoritative class, never the raw string."""
    out = {}
    for n in sorted({x for x in site_labels if x}):
        c = class_rule.space_class(n)
        out[n] = (c, by_class.get(c) if c else None)
    return out


def class_rule_as_treatment(rule_id, version, trade, authority, refs, class_rule, by_class, object_footprints):
    """A TradeTreatmentRule whose by_name map is DERIVED from the semantic class rule (an adapter: the authority
    chain is label -> class (class_rule) -> treatment (by_class))."""
    names = {n: by_class.get(c) for n, c in class_rule.by_label.items() if by_class.get(c)}
    other = by_class.get(class_rule.otherwise_class) if class_rule.otherwise_class else None
    return TradeTreatmentRule(rule_id, version, trade, authority, tuple(refs) + (f"{class_rule.rule_id}@v"
                                                                                  f"{class_rule.version}",),
                              by_name=names, otherwise=other, object_footprints=object_footprints,
                              scope_names=tuple(sorted(set(class_rule.by_label) | set(class_rule.scope_labels))))


# ======================================================================== R8.11: object-footprint authority
FOOTPRINT_INCLUDED = "FOOTPRINT_INCLUDED"
FOOTPRINT_DEDUCTED = "FOOTPRINT_DEDUCTED"
ROLE_REQUIRED = "ROLE_REQUIRED"
NOT_APPLICABLE = "NOT_APPLICABLE"
ANY_NON_PARTITION_OBJECT = "ANY_NON_PARTITION_OBJECT"
IMPLICIT = "IMPLICIT_INCLUDED_BY_TOPOLOGY_CONVENTION"


@dataclass(frozen=True)
class TradeObjectFootprintPolicy:
    """How ONE trade treats the footprint of ONE object class. Separate from the object's ROLE: an object may stay
    ROLE_UNRESOLVED while a trade policy covering ANY_NON_PARTITION_OBJECT decides its footprint; a proven role
    does not by itself answer the footprint question."""
    policy_id: str
    version: int
    trade: str
    object_class: str                 # LOOSE_FURNITURE, FIXED_JOINERY, SANITARY_FIXTURE, ANY_NON_PARTITION_OBJECT ...
    treatment: str                    # FOOTPRINT_INCLUDED, FOOTPRINT_DEDUCTED, ROLE_REQUIRED, NOT_APPLICABLE
    authority: str
    scope: dict
    source_refs: tuple


def footprint_treatment(trade, object_class, policies) -> tuple:
    """(treatment, policy id) for an object class in a trade, or (None, None) when no authority exists."""
    for p in sorted(policies, key=lambda z: (z.policy_id, z.version)):
        if p.trade == trade and p.object_class == object_class:
            return p.treatment, f"{p.policy_id}@v{p.version}"
    for p in sorted(policies, key=lambda z: (z.policy_id, z.version)):
        if p.trade == trade and p.object_class == ANY_NON_PARTITION_OBJECT:
            return p.treatment, f"{p.policy_id}@v{p.version}"
    return None, None


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


def object_materiality(consequence_entry, rule: TradeTreatmentRule, footprint_policies=()) -> dict:
    """Materiality of the UNKNOWN-role objects of one site for one trade. consequence_entry: the site's
    consequence["unknown"] record (effect, sources) from role_authority.separator_analysis, or None."""
    if not consequence_entry or consequence_entry.get("effect") == "NONE":
        return {"state": NON_MATERIAL, "why": "the objects cannot change the site's topology at all", "sources": []}
    src = sorted(consequence_entry.get("sources", []))
    if consequence_entry.get("effect") == "SEPARATES_LABELS":
        return {"state": MATERIAL, "why": "the object could be a partition between the site's labels", "sources": src}
    tr, pid = footprint_treatment(rule.trade, ANY_NON_PARTITION_OBJECT, footprint_policies)
    if tr == FOOTPRINT_INCLUDED:
        return {"state": NON_MATERIAL, "sources": src, "footprint_policy": pid,
                "why": f"{pid}: this trade includes the footprint of any non-partition object, and the consequence "
                       "check proves the object cannot separate the labels (its role may stay unresolved)"}
    if tr in (ROLE_REQUIRED, FOOTPRINT_DEDUCTED):
        return {"state": MATERIAL, "sources": src, "footprint_policy": pid,
                "why": f"{pid}: the footprint treatment depends on the object's role ({tr})"}
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
           "semantic_class": "label text -> SPACE CLASS (SemanticClassRule, exact text, scoped) -> treatment",
           "object_footprint": [FOOTPRINT_INCLUDED, FOOTPRINT_DEDUCTED, ROLE_REQUIRED, NOT_APPLICABLE],
           "never": ["a treatment from a room name by itself", "a historical BOQ quantity as authority",
                     "a boundary invented between labels", "a global role assigned to release one quantity"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
