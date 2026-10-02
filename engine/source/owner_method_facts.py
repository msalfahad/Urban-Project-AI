"""OWNER METHOD FACTS (R8.13) - an owner's BOQ / trade-measurement statements, kept apart from owner CLAIMS
(owner_claims: what a source part IS) and owner PHYSICAL facts (owner_facts: what is BUILT).

A method fact says HOW a trade is measured or finished inside an exact scope: "the floor finish is measured over the
whole room floor, object footprints included", "these rooms take wall tile to a stated height", "skirting is measured
in linear metres". It is data, never project logic in code, and it is bound like a claim:

  scope        revision + anchor + region + frame (+ plan, trade, space classes, finish) - all or nothing
  transfer     a method fact never transfers to another revision, project or space class (transfer_forbidden)
  domains      TRADE_FOOTPRINT / TRADE_FINISH_SCOPE / TRADE_UNIT only; NEVER topology, role, closure or passage
               detection - a method fact cannot change a TS01 digest by construction
  supersedes   a CHANGE of an existing rule is a versioned, scoped supersession; the same meaning is CORROBORATING;
               a narrower statement of the same meaning is MORE_SPECIFIC. Two in-force statements of different value
               for the same (trade, attribute, scope) without a supersession are a CONFLICT (never silently both).

Outcome per row: OFFERED / APPLIED / CORROBORATING_ONLY / REJECTED_SCOPE / STALE / CONFLICT (owner_facts outcomes).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

from . import owner_facts as OF
from . import trade_regions as TR

POLICY_ID = "OWNER_METHOD_FACT_POLICY_V4"      # V4 (R8.17): WINDOW_FLOOR_CONTACT may also reach TRADE_SURFACE
TRADE_FOOTPRINT = "TRADE_FOOTPRINT"
TRADE_FINISH_SCOPE = "TRADE_FINISH_SCOPE"
TRADE_UNIT = "TRADE_UNIT"
TRADE_ALLOCATION = "TRADE_ALLOCATION"           # V2: which trade region a strip belongs to (thresholds)
TRADE_SURFACE = "TRADE_SURFACE"                 # V2: reveal / soffit surfaces and their finish
TRADE_PATH = "TRADE_PATH"                       # V2: linear wall-contact paths (skirting)
DOMAINS = (TRADE_FOOTPRINT, TRADE_FINISH_SCOPE, TRADE_UNIT, TRADE_ALLOCATION, TRADE_SURFACE, TRADE_PATH)
FORBIDDEN_DOMAINS = (OF.TOPOLOGY_ROLE, OF.TOPOLOGY_CLOSURE_REVIEW, OF.BLOCKER_CLASSIFICATION, OF.PASSAGE_ATTRIBUTES,
                     "TOPOLOGY", "WALL_BAND", "PASSAGE_DETECTION")
KIND_DOMAINS = {"TRADE_OBJECT_FOOTPRINT": (TRADE_FOOTPRINT,), "FINISH_SCOPE": (TRADE_FINISH_SCOPE,),
                "MEASUREMENT_UNIT": (TRADE_UNIT,), "THRESHOLD_ALLOCATION": (TRADE_ALLOCATION,),
                "OPENING_REVEAL": (TRADE_SURFACE,), "SKIRTING_PATH": (TRADE_PATH,),
                "WINDOW_FLOOR_CONTACT": (TRADE_PATH, TRADE_SURFACE)}

CORROBORATING, MORE_SPECIFIC, SUPERSEDED_IN_SCOPE = "CORROBORATING", "MORE_SPECIFIC", "SUPERSEDED_IN_SCOPE"
RELATIONS = (CORROBORATING, MORE_SPECIFIC, SUPERSEDED_IN_SCOPE)
SCOPE_KEYS = ("source_revision_id", "source_anchor_sha256", "region_id", "frame_id")


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


@dataclass(frozen=True)
class MethodFact:
    fact_id: str
    version: int
    kind: str
    authority: tuple
    scope: dict                       # SCOPE_KEYS + plan / trade / space_classes / finish
    statement: dict
    unit: str | None = None
    transfer_forbidden: tuple = ()
    relations: tuple = ()             # ({"rule": ref, "relation": ..., "scope": ..., "why": ...}, ...)
    allowed_domains: tuple = ()

    @property
    def ref(self):
        return f"{self.fact_id}@v{self.version}"


def from_record(rec: dict) -> MethodFact:
    doms = tuple(rec.get("allowed_domains") or KIND_DOMAINS.get(rec["kind"], ()))
    bad = [d for d in doms if d in FORBIDDEN_DOMAINS or d not in DOMAINS]
    if bad:
        raise ValueError(f"{rec['fact_id']}: a method fact never reaches {bad}")
    for r in rec.get("relations", ()):
        if r["relation"] not in RELATIONS:
            raise ValueError(f"{rec['fact_id']}: unknown relation {r['relation']!r}")
        if r["relation"] == SUPERSEDED_IN_SCOPE and not r.get("scope"):
            raise ValueError(f"{rec['fact_id']}: a supersession needs its exact scope")
    return MethodFact(rec["fact_id"], int(rec["version"]), rec["kind"], tuple(rec["authority"]), dict(rec["scope"]),
                      dict(rec.get("statement", {})), rec.get("unit"), tuple(rec.get("transfer_forbidden", ())),
                      tuple(rec.get("relations", ())), doms)


def bind(fact: MethodFact, inp) -> dict:
    """APPLIES or REJECTED_SCOPE for THIS input (revision + anchor + region + frame, all or nothing)."""
    rev, sc = inp.revision, fact.scope
    got = {"source_revision_id": rev.revision_id if rev else None, "source_anchor_sha256": rev.anchor_sha256 if rev
           else None, "region_id": inp.region_id, "frame_id": inp.frame_id}
    ok = all(got[k] == sc.get(k) for k in SCOPE_KEYS)
    return {"fact": fact.ref, "binding": "APPLIES" if ok else OF.REJECTED_SCOPE,
            "mismatch": [] if ok else [k for k in SCOPE_KEYS if got[k] != sc.get(k)]}


def in_scope(fact: MethodFact, *, trade=None, space_classes=(), finish=None) -> bool:
    """Does a bound fact cover this trade / these space classes / this finish? Every class must be in scope."""
    sc = fact.scope
    if trade is not None and sc.get("trade") not in (None, trade):
        return False
    if sc.get("space_classes") and (not space_classes or not set(space_classes) <= set(sc["space_classes"])):
        return False
    if finish is not None and sc.get("finish") not in (None, finish):
        return False
    return True


def footprint_policy(fact: MethodFact) -> TR.TradeObjectFootprintPolicy:
    """The trade-layer object-footprint policy a TRADE_OBJECT_FOOTPRINT fact carries (scope kept on the policy)."""
    if fact.kind != "TRADE_OBJECT_FOOTPRINT":
        raise ValueError(f"{fact.ref} is not an object-footprint fact")
    st = fact.statement
    return TR.TradeObjectFootprintPolicy(fact.fact_id, fact.version, st["trade"], st.get("object_class",
                                         TR.ANY_NON_PARTITION_OBJECT), st["treatment"], "OWNER_METHOD_FACT",
                                         dict(fact.scope), (fact.ref,))


def policies_for(facts_and_bindings, *, trade, space_classes, finish=None) -> tuple:
    """The footprint policies a ROW may use: bound (APPLIES) footprint facts whose scope covers the row's trade, ALL
    its space classes and its finish. Anything else is out of scope for that row."""
    out = []
    for f, b in facts_and_bindings:
        if f.kind == "TRADE_OBJECT_FOOTPRINT" and b["binding"] == "APPLIES" and \
                in_scope(f, trade=trade, space_classes=space_classes, finish=finish):
            out.append(footprint_policy(f))
    return tuple(out)


def footprint_area(site_area, object_footprints, treatment):
    """The trade area one footprint treatment implies for one site: FOOTPRINT_INCLUDED -> the whole site;
    FOOTPRINT_DEDUCTED -> the site less every object footprint (exact sum, order independent); anything else ->
    None (no authority: the row is BLOCKED_TRADE_RULE, never a guess)."""
    if treatment == TR.FOOTPRINT_INCLUDED:
        return site_area
    if treatment == TR.FOOTPRINT_DEDUCTED:
        return site_area - math.fsum(sorted(object_footprints))
    return None


def row_outcome(fact: MethodFact, binding: dict, *, trade, space_classes, finish=None, used: bool,
                corroborates=False) -> str:
    """The fact's outcome for ONE row."""
    if binding["binding"] != "APPLIES":
        return OF.REJECTED_SCOPE
    if not in_scope(fact, trade=trade, space_classes=space_classes, finish=finish):
        return OF.REJECTED_SCOPE
    if used:
        return OF.APPLIED
    return OF.CORROBORATING_ONLY if corroborates else OF.OFFERED


def conflicts(facts, rules) -> list:
    """In-force statements of DIFFERENT value for the same (trade, attribute, scope) with no supersession between
    them. `rules`: [{"ref", "trade", "attribute", "value", "scope"}] of existing rules; facts carry theirs in
    statement["values"] = [{"trade", "attribute", "value"}]."""
    out = []
    for f in facts:
        sup = {r["rule"] for r in f.relations if r["relation"] == SUPERSEDED_IN_SCOPE}
        for v in f.statement.get("values", ()):
            for r in rules:
                if (r["trade"], r["attribute"]) == (v["trade"], v["attribute"]) and r["value"] != v["value"] and \
                        r["ref"] not in sup:
                    out.append({"fact": f.ref, "rule": r["ref"], "attribute": v["attribute"],
                                "fact_value": v["value"], "rule_value": r["value"]})
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "domains": list(DOMAINS), "forbidden_domains": list(FORBIDDEN_DOMAINS),
           "kind_domains": {k: list(v) for k, v in KIND_DOMAINS.items()}, "relations": list(RELATIONS),
           "binding": "revision + anchor + region + frame (all or nothing); then trade / space classes / finish",
           "outcomes": list(OF.OUTCOMES),
           "never": ["a topology, role, closure or passage input", "a transfer to another revision, project or "
                     "space class", "'ignore furniture globally' (scope is the trade + classes + finish)",
                     "two in-force contradictory statements without a supersession", "project logic in code",
                     "a quantity"]}
    rec["digest"] = _digest(rec)
    return rec
