"""ENGINEERING KNOWLEDGE (M9 Phase 2B-1, ARCH_TAKEOFF_V2.3 only) - the owner rules, conflicts, question catalogue and
genuine owner questions in one machine-readable registry: knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json.

    registry()                       -> the validated registry (cached; a deep copy is returned)
    rule(rule_id) / ref(rule_id)     -> a record / what a BOQ line records about the rule it used
    door_standard(category)          -> UP-DOOR-OPEN-002: required nominal door opening, architectural wall opening
    reference_height(category)       -> UP-DOOR-HGT-001: the owner reference (fallback) door height
    wet_codes() / confirm_codes()    -> UP-WET-001: the owner wet-area room codes
    precedence_rank(kind)            -> UP-KB-PREC-001: 1 (approved drawing) .. 7 (unresolved)
    classify_question(entry)         -> the catalogue entry an unresolved item belongs to (category A .. E)
    owner_questions(unresolved, ...) -> grouped: owner questions, document requests, engineering backlog, rule
                                        conflicts handled by scenarios, and anything an approved rule should have
                                        answered (must be empty)
    validate(reg)                    -> problems (empty = clean): fields, statuses, supersession, code and test links

The registry is read by ARCH_TAKEOFF_V2.3 (version 1.0.0, the default) and ARCH_TAKEOFF_V2.4 (version 1.1.0, inside
`using("1.1.0")`). V1 .. V2.2 keep the frozen rule set rules/ 1.5.0 (their RUN_RULES digests are unchanged); rules/
gains no file. Project-agnostic; stdlib only.

    using(version)                   -> a context in which every accessor reads that registry version (1.0.0 outside)
    version() / rule_set()           -> the active version and its rule-set id (RULE_SET / PATH follow the context)
    wp_standard()                    -> 1.1.0: UP-WP-001 .. -003 roll, lap and upturn values
"""

from __future__ import annotations

import contextlib
import contextvars
import copy
import hashlib
import json
import re
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONS = {"1.0.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json",
            "1.1.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json",
            "1.2.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json",       # ARCH_TAKEOFF_V2.7
            "1.3.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.3.0.json",       # ARCH_TAKEOFF_V2.7.1
            "1.4.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json",       # ARCH_TAKEOFF_V2.8
            "1.5.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"}       # ARCH_TAKEOFF_V2.9
DEFAULT_VERSION = "1.0.0"
_ACTIVE = contextvars.ContextVar("urban_knowledge_version", default=DEFAULT_VERSION)
POLICY_ID = "URBAN_ENGINEERING_KNOWLEDGE_V1"
REQUIRED = ("rule_id", "title", "kind", "purpose", "scope", "elements", "locations", "preconditions", "exceptions",
            "authority", "status", "effective_version", "logic", "required_evidence", "assumptions_permitted",
            "conflicts", "dependent_trades", "tests", "code", "examples", "limitations", "history", "supersedes",
            "superseded_by")
CATEGORIES = ("A_ESTABLISHED", "B_MISSING_DRAWING_EVIDENCE", "C_RULE_CONFLICT", "D_MISSING_OWNER_POLICY",
              "E_ENGINEERING_DEFECT")
PRECEDENCE = OrderedDict((
    ("APPROVED_DRAWING", 1), ("APPROVED_SPECIFICATION", 2), ("VERIFIED_GEOMETRY", 3), ("PROJECT_DECISION", 4),
    ("OWNER_RULE", 5), ("ASSUMPTION", 6), ("UNRESOLVED", 7)))


class KnowledgeError(ValueError):
    pass


def version():
    return _ACTIVE.get()


def rule_set():
    return "URBAN_KB_" + _ACTIVE.get()


def __getattr__(name):
    # RULE_SET and PATH follow the active version (1.0.0 unless inside using())
    if name == "RULE_SET":
        return rule_set()
    if name == "PATH":
        return VERSIONS[_ACTIVE.get()]
    raise AttributeError(name)


@contextlib.contextmanager
def using(v):
    """every accessor reads registry version v inside the block (ARCH_TAKEOFF_V2.4: 1.1.0)."""
    if v not in VERSIONS:
        raise KnowledgeError(f"knowledge registry version {v} is not one of {sorted(VERSIONS)}")
    tok = _ACTIVE.set(v)
    try:
        yield v
    finally:
        _ACTIVE.reset(tok)


@lru_cache(maxsize=None)
def _load_version(v):
    reg = json.loads(VERSIONS[v].read_text(encoding="utf-8"))
    probs = validate(reg, links=False)
    if probs:
        raise KnowledgeError("knowledge registry invalid: " + "; ".join(probs[:5]))
    if reg.get("version") != v:
        raise KnowledgeError(f"knowledge registry {VERSIONS[v].name} says version {reg.get('version')}")
    return reg


def _load():
    return _load_version(_ACTIVE.get())


def registry():
    return copy.deepcopy(_load())


@lru_cache(maxsize=None)
def _digest_version(v):
    return hashlib.sha256(VERSIONS[v].read_bytes()).hexdigest()


def digest():
    return _digest_version(_ACTIVE.get())


def rule(rule_id):
    for r in _load()["rules"]:
        if r["rule_id"] == rule_id:
            return copy.deepcopy(r)
    raise KeyError(f"{rule_id} is not in the knowledge registry {rule_set()}")


def ref(rule_id):
    r = rule(rule_id)
    return {"rule_id": rule_id, "version": r["effective_version"], "rule_set": rule_set(), "rule_set_digest": digest(),
            "status": r["status"]}


def door_standard(category):
    """-> {"required_nominal_door_m", "required_wall_opening_m", "allowance_m"} or None (no ordinary standard)."""
    lg = rule("UP-DOOR-OPEN-002")["logic"]
    row = lg["table"].get(category)
    if row is None:
        return None
    if abs(row["required_wall_opening_m"] - row["required_nominal_door_m"] - lg["allowance_m"]) > 1e-9:
        raise KnowledgeError(f"UP-DOOR-OPEN-002 {category}: the wall opening is not nominal + allowance")
    return dict(row, allowance_m=lg["allowance_m"])


def reference_height(category):
    return rule("UP-DOOR-HGT-001")["logic"]["owner_reference_height_m"].get(category)


def wp_standard():
    """1.1.0: the owner's waterproofing master standards (UP-WP-001 roll, UP-WP-002 lap, UP-WP-003 upturn)."""
    r1, r2, r3 = (rule(i)["logic"] for i in ("UP-WP-001", "UP-WP-002", "UP-WP-003"))
    if abs(r1["gross_roll_area_m2"] - r1["roll_width_m"] * r1["roll_length_m"]) > 1e-9:
        raise KnowledgeError("UP-WP-001: the gross roll area is not width x length")
    return {"roll_width_m": r1["roll_width_m"], "roll_length_m": r1["roll_length_m"],
            "gross_roll_area_m2": r1["gross_roll_area_m2"], "lap_m": r2["lap_m"], "upturn_h_m": r3["upturn_h_m"]}


def wet_codes():
    return tuple(rule("UP-WET-001")["logic"]["wet_codes"])


def confirm_codes():
    return tuple(rule("UP-WET-001")["logic"]["project_confirmation_codes"])


def precedence_rank(kind):
    return PRECEDENCE[kind]


def classify_question(entry):
    """the catalogue entry of one unresolved item ({"item", "reason"}); None when no entry matches."""
    reason = str(entry.get("reason") or entry.get("question") or "")
    item = str(entry.get("item") or "")
    for q in _load()["question_catalogue"]:
        if not re.search(q["pattern"], reason):
            continue
        if q.get("item") and not re.search(q["item"], item):
            continue
        return dict(q)
    return None


def owner_questions(unresolved, *, method):
    """-> the unresolved items grouped by their underlying question. Owner questions are the D (and unresolved C)
    groups only; B groups are document requests; E groups are engineering backlog; A (an approved rule answers it)
    must be empty under ARCH_TAKEOFF_V2.3 - any A item left is a defect of the run, never a question."""
    groups = OrderedDict()
    unmatched = []
    for u in unresolved:
        q = classify_question(u)
        if q is None:
            unmatched.append(u)
            continue
        key = (q["category"], q["group"])
        g = groups.setdefault(key, {"category": q["category"], "group": q["group"], "rule": q.get("rule"),
                                    "request": q.get("request"), "question_id": q.get("question_id"),
                                    "history": q.get("history") or [], "instances": 0, "floors": set(),
                                    "items": set(), "examples": []})
        g["instances"] += 1
        g["floors"].add(str(u.get("floor") or "-"))
        g["items"].add(str(u.get("item") or "-"))
        if len(g["examples"]) < 3:
            g["examples"].append({"floor": u.get("floor"), "room_id": u.get("room_id"), "item": u.get("item"),
                                  "reason": str(u.get("reason") or "")[:240]})
    out = {"policy": POLICY_ID, "rule": "UP-KB-QUES-001", "method": method, "rule_set": rule_set(),
           "rule_set_digest": digest(), "by_category": {c: [] for c in CATEGORIES}, "unclassified": []}
    for g in groups.values():
        g = dict(g, floors=sorted(g["floors"]), items=sorted(g["items"]))
        out["by_category"][g["category"]].append(g)
    qids = {g["question_id"] for c in ("C_RULE_CONFLICT", "D_MISSING_OWNER_POLICY")
            for g in out["by_category"][c] if g.get("question_id")}
    out["owner_questions"] = [q for q in _load()["owner_questions"] if q["id"] in qids]
    out["unclassified"] = [{"floor": u.get("floor"), "item": u.get("item"), "reason": str(u.get("reason") or "")[:240]}
                           for u in unmatched]
    out["summary"] = {
        "unresolved_items": len(unresolved),
        "groups": {c: len(out["by_category"][c]) for c in CATEGORIES},
        "instances": {c: sum(g["instances"] for g in out["by_category"][c]) for c in CATEGORIES},
        "owner_questions": len(out["owner_questions"]),
        "established_but_still_raised": sum(g["instances"] for g in out["by_category"]["A_ESTABLISHED"]),
        "unclassified": len(unmatched)}
    return out


def policy_record():
    path = VERSIONS[version()]
    return {"policy": POLICY_ID, "rule_set": rule_set(),
            "registry": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name,
            "digest": digest(), "rules": len(_load()["rules"]), "precedence": list(PRECEDENCE),
            "categories": list(CATEGORIES)}


def _link_ok(spec, kind):
    path, _, name = spec.partition("::")
    f = ROOT / path
    if not f.is_file():
        return False
    if not name:
        return True
    name = re.sub(r"\[.*\]$", "", name)
    return re.search(rf"^\s*def {re.escape(name)}\(", f.read_text(encoding="utf-8", errors="replace"), re.M) is not None


def validate(reg, *, links=True):
    """-> [problem]; links=True also checks that every code and test reference exists (file and function)."""
    probs = []
    if reg.get("schema") != "URBAN_ENGINEERING_KNOWLEDGE_V1":
        probs.append("schema")
    statuses = set(reg.get("statuses") or ())
    ids = [r.get("rule_id") for r in reg.get("rules") or ()]
    if len(ids) != len(set(ids)):
        probs.append("duplicate rule_id")
    for r in reg.get("rules") or ():
        miss = [k for k in REQUIRED if k not in r]
        if miss:
            probs.append(f"{r.get('rule_id')}: missing {miss}")
            continue
        if r["status"] not in statuses:
            probs.append(f"{r['rule_id']}: status {r['status']}")
        if r["superseded_by"] and r["superseded_by"] not in ids:
            probs.append(f"{r['rule_id']}: superseded_by {r['superseded_by']} unknown")
        if r["status"] == "DEPRECATED" and not r["superseded_by"]:
            probs.append(f"{r['rule_id']}: DEPRECATED without superseded_by")
        if r["status"] == "OWNER_APPROVED" and not (r["authority"] or {}).get("source"):
            probs.append(f"{r['rule_id']}: OWNER_APPROVED without an authority source")
        if r["status"] in ("OWNER_APPROVED", "PROJECT_SPECIFIC") and not r["tests"]:
            probs.append(f"{r['rule_id']}: no test")
        if links:
            for spec in r["code"]:
                if not _link_ok(spec, "code"):
                    probs.append(f"{r['rule_id']}: code link {spec}")
            for spec in r["tests"]:
                if not _link_ok(spec, "test"):
                    probs.append(f"{r['rule_id']}: test link {spec}")
    for q in reg.get("question_catalogue") or ():
        if q.get("category") not in CATEGORIES:
            probs.append(f"question {q.get('pattern')}: category")
        if q.get("rule") and q["rule"] not in ids and not str(q["rule"]).startswith(("UP-", "URBAN-")):
            probs.append(f"question {q.get('pattern')}: rule {q['rule']}")
        try:
            re.compile(q["pattern"])
        except (re.error, KeyError):
            probs.append(f"question pattern {q.get('pattern')}")
    oq = {q["id"] for q in reg.get("owner_questions") or ()}
    for q in reg.get("question_catalogue") or ():
        if q.get("question_id") and q["question_id"] not in oq:
            probs.append(f"question {q['pattern']}: owner question {q['question_id']} missing")
    return probs
