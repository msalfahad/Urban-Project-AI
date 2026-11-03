"""RULE STORE V2 (T-461, owner directive 2026-11-02 C6 (d)) - registers and resolves every URBAN_RULES overlay version
(generic; stdlib only; opt-in, read by no released method).

    registered()                                     -> the rule-set versions this store resolves, oldest first
    rule_set(version, include_proposed=False)        -> {"version", "digest", "rules": {rule_id: record}, "superseded": [...],
                                                        "chain": [overlay files applied, oldest first]}
    rule(rule_id, version, include_proposed=False)   -> the effective record (KeyError when absent)
    rule_ref(rule_id, version)                       -> what a quantity records about the rule it used
    check_chain()                                    -> problems of the overlay chain (empty = clean)
    knowledge_versions() / knowledge_registry(v)     -> the knowledge registry versions incl. 1.8.0, and one of them
                                                        (validated with engine/source/knowledge.validate, links checked)
    policy_record()

Why a new module: engine/source/rule_store.py (V1) resolves 1.4.0 and 1.5.0 only, and its policy_record() is written
into every M9 run, so adding versions there would change released run output. V1 stays byte-identical; V2 resolves
the same chain further: the owner library 1.4.0 (base) -> URBAN_RULES 1.5.0 -> 1.6.0 (UP-STAIR-015, T-158) -> 1.7.0
(UP-STAIR-016, T-267) -> 1.8.0 (UP-GEN-003 1.2.0 = Q-73 A, UP-STAIR-017 = Q-53 C; T-461). Each overlay names its base
version and file; the chain is followed from those fields and refused when a link disagrees. For 1.4.0 and 1.5.0 the
rule set and its digest are identical to V1 (same origin text, same digest function), so a result can move from V1
to V2 without any rule changing.

Knowledge 1.8.0 (UP-HGT-001 / UP-FIN-WALL-001 owner wall height, T-081 r2) is registered HERE, not in
engine/source/knowledge.py: that file is a released, frozen artefact (T-467 released freeze), so its VERSIONS stay
1.0.0 .. 1.7.0 and knowledge.using("1.8.0") stays refused; finish_height_v2.py keeps reading the 1.8.0 file directly.

Resolution, as V1: an OWNER_APPROVED overlay record replaces the record with the same rule_id or adds a new one; a
PROPOSED record is ignored unless asked for; no file is ever edited; there is no default version (the caller names
it). Nothing here knows a project.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "rules"
POLICY_ID = "URBAN_RULE_STORE_V2"
BASE_VERSION = "1.4.0"
BASE_FILE = "owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json"
OVERLAYS = {"1.5.0": "owner_decisions/URBAN_RULES_1.5.0.json",
            "1.6.0": "owner_decisions/URBAN_RULES_1.6.0.json",
            "1.7.0": "owner_decisions/URBAN_RULES_1.7.0.json",
            "1.8.0": "owner_decisions/URBAN_RULES_1.8.0.json"}
APPROVED, PROPOSED = "OWNER_APPROVED", "PROPOSED"
DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: resolves registered rule / knowledge versions; adds no default value
KNOWLEDGE_EXTRA = {"1.8.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json"}   # T-081 r2 heights


class RuleStoreError(ValueError):
    pass


def registered():
    return [BASE_VERSION] + list(OVERLAYS)


def _load(rel):
    return json.loads((STORE / rel).read_text(encoding="utf-8"))


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _chain(version, overlays=None):
    """overlay versions to apply for `version`, oldest first, followed through each file's own base field."""
    overlays = OVERLAYS if overlays is None else overlays
    if version == BASE_VERSION:
        return []
    if version not in overlays:
        raise RuleStoreError(f"unknown rule-set version {version!r}; registered: {', '.join([BASE_VERSION, *overlays])}")
    out, v, seen = [], version, set()
    while v != BASE_VERSION:
        if v in seen or v not in overlays:
            raise RuleStoreError(f"rule-set chain of {version} breaks at {v!r}")
        seen.add(v)
        doc = _load(overlays[v])
        if doc.get("version") != v:
            raise RuleStoreError(f"rules/{overlays[v]} says version {doc.get('version')!r}, registered as {v}")
        base = doc.get("base") or {}
        out.append(v)
        if base.get("library") == "URBAN_PROJECTS_RULE_LIBRARY":
            if base.get("version") != BASE_VERSION or base.get("file") != "rules/" + BASE_FILE:
                raise RuleStoreError(f"rules/{overlays[v]} names base {base}, not the owner library {BASE_VERSION}")
            v = BASE_VERSION
        else:
            nxt = base.get("version")
            if base.get("rule_set") != "URBAN_RULES" or nxt not in overlays or base.get("file") != "rules/" + overlays[nxt]:
                raise RuleStoreError(f"rules/{overlays[v]} names base {base}, which is not a registered overlay")
            v = nxt
    return list(reversed(out))


@lru_cache(maxsize=None)
def _rule_set(version, include_proposed):
    chain = _chain(version)
    base = _load(BASE_FILE)
    rules = {r["rule_id"]: dict(r, version=r.get("version", "1.0.0"), status=r.get("status", APPROVED),
                                origin="URBAN_PROJECTS_RULE_LIBRARY 1.4.0") for r in base["rules"]}
    superseded = []
    for v in chain:
        for r in _load(OVERLAYS[v])["records"]:
            if r["status"] != APPROVED and not include_proposed:
                continue
            old = rules.get(r["rule_id"])
            if old is not None:
                superseded.append({"rule_id": r["rule_id"], "from": old["version"], "to": r["version"],
                                   "status": r["status"]})
            rules[r["rule_id"]] = dict(r, origin=f"URBAN_RULES {v} overlay")
    body = {"version": version, "include_proposed": include_proposed, "rules": rules}
    return {**body, "digest": _digest(body), "superseded": superseded,
            "chain": ["rules/" + BASE_FILE] + ["rules/" + OVERLAYS[v] for v in chain]}


def rule_set(version, include_proposed=False):
    """the effective rule set of one registered version (a deep copy)."""
    return copy.deepcopy(_rule_set(version, bool(include_proposed)))


def rule(rule_id, version, include_proposed=False):
    rs = _rule_set(version, bool(include_proposed))
    if rule_id not in rs["rules"]:
        raise KeyError(f"{rule_id} is not in rule set {version}")
    return copy.deepcopy(rs["rules"][rule_id])


def rule_ref(rule_id, version):
    r = rule(rule_id, version)
    return {"rule_id": rule_id, "version": r["version"], "rule_set": version,
            "rule_set_digest": _rule_set(version, False)["digest"], "status": r["status"], "store": POLICY_ID}


def check_chain(overlays=None):
    """-> problems (empty = clean): every registered overlay resolves through its own base fields, versions in order."""
    overlays = OVERLAYS if overlays is None else overlays
    out = []
    for v in overlays:
        try:
            ch = _chain(v, overlays)
        except (RuleStoreError, OSError, ValueError) as e:
            out.append(str(e))
            continue
        key = lambda s: tuple(int(x) for x in s.split("."))  # noqa: E731
        want = sorted((k for k in overlays if key(k) <= key(v)), key=key)
        if ch != want:
            out.append(f"{v}: chain {ch} skips or reorders registered overlays {want}")
    return out


def knowledge_versions():
    """knowledge registry versions: those engine/source/knowledge.py resolves, plus the ones registered here."""
    from engine.source import knowledge as K
    return {**{v: p for v, p in K.VERSIONS.items()}, **KNOWLEDGE_EXTRA}


@lru_cache(maxsize=None)
def _knowledge(v):
    from engine.source import knowledge as K
    vers = knowledge_versions()
    if v not in vers:
        raise RuleStoreError(f"knowledge registry version {v} is not one of {sorted(vers)}")
    reg = json.loads(vers[v].read_text(encoding="utf-8"))
    probs = K.validate(reg)
    if probs:
        raise RuleStoreError("knowledge registry invalid: " + "; ".join(probs[:5]))
    if reg.get("version") != v:
        raise RuleStoreError(f"knowledge registry {vers[v].name} says version {reg.get('version')}")
    return reg


def knowledge_registry(v):
    return copy.deepcopy(_knowledge(v))


def policy_record():
    return {"policy_id": POLICY_ID, "versions": registered(), "default": None,
            "knowledge_versions": sorted(knowledge_versions()),
            "rule": "the owner library 1.4.0 plus every URBAN_RULES overlay up to the named version, followed through "
                    "each file's base field; OWNER_APPROVED records replace by rule_id, PROPOSED ignored unless asked; "
                    "for 1.4.0 / 1.5.0 identical to engine/source/rule_store.py; no default version; read by no released "
                    "method"}
