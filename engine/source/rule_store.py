"""RULE STORE (M9 S1) - one versioned place the new engines read rules from (generic; stdlib only).

    rule_set(version="1.5.0", include_proposed=False) -> {"version", "digest", "rules": {rule_id: record}, "superseded": [...]}
    rule(rule_id, version="1.5.0")                    -> the effective record (KeyError when absent)
    material_specs() / material_spec(spec_id)         -> the material registry (membrane rolls, tile sizes)
    family_master()                                   -> the BOQ family master (99 families and their engine capability)
    check()                                           -> drift messages of rules/RULES_MANIFEST.json (empty = clean)

Resolution: the base owner library (1.4.0, a byte copy of data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json) and, for
1.5.0, the owner-decision overlay rules/owner_decisions/URBAN_RULES_1.5.0.json. An OWNER_APPROVED overlay record
replaces the base record with the same rule_id, or adds a new one; a PROPOSED record is ignored unless asked for. The
base file is never edited, and a result computed under one version names that version and its digest - an old rule can
never silently override a newer owner decision, and a newer decision never rewrites an old result.

Nothing here knows a project.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "rules"
LATEST_APPROVED = "1.5.0"
VERSIONS = ("1.4.0", "1.5.0")
APPROVED, PROPOSED = "OWNER_APPROVED", "PROPOSED"


class RuleStoreError(ValueError):
    pass


def _load(rel):
    return json.loads((STORE / rel).read_text(encoding="utf-8"))


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


@lru_cache(maxsize=None)
def _rule_set(version, include_proposed):
    if version not in VERSIONS:
        raise RuleStoreError(f"unknown rule-set version {version!r}; known: {', '.join(VERSIONS)}")
    base = _load("owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json")
    rules = {r["rule_id"]: dict(r, version=r.get("version", "1.0.0"), status=r.get("status", APPROVED),
                                origin="URBAN_PROJECTS_RULE_LIBRARY 1.4.0") for r in base["rules"]}
    superseded = []
    if version == "1.5.0":
        ov = _load("owner_decisions/URBAN_RULES_1.5.0.json")
        for r in ov["records"]:
            if r["status"] != APPROVED and not include_proposed:
                continue
            old = rules.get(r["rule_id"])
            if old is not None:
                superseded.append({"rule_id": r["rule_id"], "from": old["version"], "to": r["version"],
                                   "status": r["status"]})
            rules[r["rule_id"]] = dict(r, origin="URBAN_RULES 1.5.0 overlay")
    body = {"version": version, "include_proposed": include_proposed, "rules": rules}
    return {**body, "digest": _digest(body), "superseded": superseded}


def rule_set(version=LATEST_APPROVED, include_proposed=False):
    """the effective rule set of one version (a deep copy: callers cannot change the store by accident)."""
    return copy.deepcopy(_rule_set(version, bool(include_proposed)))


def rule(rule_id, version=LATEST_APPROVED, include_proposed=False):
    rs = _rule_set(version, bool(include_proposed))
    if rule_id not in rs["rules"]:
        raise KeyError(f"{rule_id} is not in rule set {version}")
    return copy.deepcopy(rs["rules"][rule_id])


def rule_ref(rule_id, version=LATEST_APPROVED):
    """what a quantity records about the rule it used."""
    r = rule(rule_id, version)
    return {"rule_id": rule_id, "version": r["version"], "rule_set": version, "rule_set_digest": _rule_set(version, False)["digest"],
            "status": r["status"]}


@lru_cache(maxsize=None)
def _materials():
    return _load("materials/URBAN_MATERIAL_SPECS_1.0.0.json")


def material_specs():
    return copy.deepcopy(_materials())


def material_spec(spec_id):
    for s in _materials()["specs"]:
        if s["spec_id"] == spec_id:
            return copy.deepcopy(s)
    raise KeyError(f"no material spec {spec_id}")


@lru_cache(maxsize=None)
def _families():
    return _load("coverage/BOQ_FAMILY_MASTER_1.0.0.json")


def family_master():
    return copy.deepcopy(_families())


def check():
    """drift between rules/ and its manifest / sources (delegates to tools/m9_rules_manifest.py)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("m9_rules_manifest", ROOT / "tools" / "m9_rules_manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check()


def policy_record():
    return {"policy_id": "URBAN_RULE_STORE_V1", "versions": list(VERSIONS), "latest_owner_approved": LATEST_APPROVED,
            "rule": "OWNER_APPROVED overlay records replace base records by rule_id; PROPOSED records are ignored unless "
                    "requested; every result records the rule-set version and digest it used"}
