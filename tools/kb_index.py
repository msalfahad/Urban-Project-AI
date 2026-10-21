"""KNOWLEDGE SOURCE INDEX (M9 Phase 2B-1) - one generated inventory of every place an owner rule, owner fact,
method, engine constant or owner question lives in this repository, and the crosswalk from earlier question ids to
the rule that now answers them.

    python3 -I tools/kb_index.py            print the index
    python3 -I tools/kb_index.py --write    write knowledge/RULE_SOURCE_INDEX.json
    python3 -I tools/kb_index.py --check    exit 1 when the committed index differs from a fresh build

Project identities are written as placeholders ({P}, {Q}); fact records are referenced by JSON pointer and digest.
Stdlib only."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "RULE_SOURCE_INDEX.json"
# the identities are assembled from fragments so that this file itself never carries them
SCRUB = ((re.compile("(?i)" + "qor" + "tuba"), "{Q}"), (re.compile("P" + "7757|ST" + "7757"), "{P}"),
         (re.compile("(?i)al[ -]?" + "rash" + "ed"), "{R}"))
# the project-rules files of the repository (one per project), found by name - no project id is written here
PROJECT_RULES = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "data" / "registry").glob("*_PROJECT_RULES.json"))

# earlier question ids (phase documents) -> what answers them now (knowledge registry 1.0.0)
CROSSWALK = [
    ("Q-S6-1 / O4 / OD-8", "doorway strip finish", "A_ESTABLISHED", "UP-THR-001"),
    ("Q7 / O5 / S6R-B4 / OD-9", "wet-room wall tile height and the band above it", "A_ESTABLISHED",
     "UP-FIN-WALL-001"),
    ("ORR-008", "which rooms are wet and take full wall ceramic", "A_ESTABLISHED", "UP-WET-001"),
    ("ORR-005", "pantry wall tile height", "A_ESTABLISHED", "UP-FIN-WALL-001 (full height = clear height)"),
    ("SE-07 / OD-12", "kitchen waterproofing", "A_ESTABLISHED", "UP-WET-001"),
    ("SE-01 .. SE-03 / OD-11 (finish part)", "reveal finish", "A_ESTABLISHED",
     "URBAN-REVEAL-FINISH-METHOD (plaster default) + UP-FIN-PLASTER-001"),
    ("SE-01 .. SE-03 / OD-11 (depth part)", "reveal depth", "B_MISSING_DRAWING_EVIDENCE",
     "window schedule / frame position"),
    ("DR-07", "door heights", "A_ESTABLISHED", "UP-DOOR-HGT-001 (ASSUMED fallback)"),
    ("DR-01 / OD-5", "main entrance", "B_MISSING_DRAWING_EVIDENCE", "UP-DOOR-CLS-004"),
    ("DR-02 / OD-2", "0.9 m / 1.0 m door width", "B_MISSING_DRAWING_EVIDENCE", "UP-DOOR-OPEN-002 (schedule)"),
    ("DR-03 / OD-3", "small unlabelled space next to the kitchen", "B_MISSING_DRAWING_EVIDENCE",
     "UP-SPACE-001 / UP-SPACE-002 (project decision binding)"),
    ("DR-05 / OD-13", "provisional doors", "B_MISSING_DRAWING_EVIDENCE", "UP-DOOR-CLS-001 (schedule)"),
    ("DR-06 / OD-4", "lift candidates", "B_MISSING_DRAWING_EVIDENCE", "UP-DOOR-CLS-005"),
    ("BA-11 / BA-12 / OD-1", "sill window or floor-level glazing", "B_MISSING_DRAWING_EVIDENCE",
     "UP-SKIRT-001 (window schedule)"),
    ("OD-6 / O8", "heights for Mode A", "B_MISSING_DRAWING_EVIDENCE", "URBAN-WALL-FINISH-HEIGHT-METHOD"),
    ("OD-7 / F-26", "deduction of openings that close a face without a gap", "B_MISSING_DRAWING_EVIDENCE",
     "UP-GEN-003 (door closure / glazing positions)"),
    ("Q-S6-4 / O6 / OD-10", "stair-hall finishes", "D_MISSING_OWNER_POLICY", "OQ-03"),
    ("Q1 / O7", "exterior scope", "D_MISSING_OWNER_POLICY", "OQ-04"),
    ("ORR-007", "stair skirting along the zigzag or the rake", "A_ESTABLISHED", "UP-STAIR-010 / UP-STAIR-011"),
    ("ORR-000", "elevator threshold depth", "A_ESTABLISHED", "UP-ELEV-005"),
    ("door classes (re-stated 2026-10-14)", "internal PVC / external aluminium / lift excluded", "A_ESTABLISHED",
     "UP-DOOR-CLS-001 / -002 / -005"),
]


def _scrub(v):
    if isinstance(v, str):
        for rx, rep in SCRUB:
            v = rx.sub(rep, v)
        return v
    if isinstance(v, list):
        return [_scrub(x) for x in v]
    if isinstance(v, dict):
        return {_scrub(k): _scrub(x) for k, x in v.items()}
    return v


def _h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _text(r):
    st = r.get("statement")
    if isinstance(st, dict):
        return st.get("text") or ""
    return st or r.get("rule_name") or r.get("title") or ""


def build():
    srcs = []
    lib = _load("rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json")
    srcs.append({"source": "rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json", "kind": "OWNER_RULE_LIBRARY",
                 "read_by": ["engine/source/rule_store.py (M9 V1 .. V2.3)"],
                 "records": [{"id": r["rule_id"], "version": r.get("version", "1.0.0"),
                              "status": r.get("status", "OWNER_APPROVED"), "trade": r.get("trade"),
                              "scope": r.get("scope"), "title": r.get("rule_name") or r.get("title")}
                             for r in lib["rules"]]})
    ov = _load("rules/owner_decisions/URBAN_RULES_1.5.0.json")
    srcs.append({"source": "rules/owner_decisions/URBAN_RULES_1.5.0.json", "kind": "OWNER_DECISION_OVERLAY",
                 "read_by": ["engine/source/rule_store.py (M9 V1 .. V2.3)"],
                 "records": [{"id": r["rule_id"], "version": r["version"], "status": r["status"],
                              "supersedes": r.get("supersedes"), "title": r.get("rule_name")} for r in ov["records"]]})
    for rel in ("rules/methods/URBAN_METHOD_REGISTER_V1.json", "rules/methods/URBAN_METHOD_REGISTER_V3.json"):
        d = _load(rel)
        ms = d.get("methods") or {}
        it = ms.items() if isinstance(ms, dict) else [((m.get("id") or m.get("method_id")), m) for m in ms]
        srcs.append({"source": rel, "kind": "URBAN_METHOD_REGISTER",
                     "read_by": ["engine/source/urban_methods*.py (earlier routes); not by the M9 arch route"],
                     "records": [{"id": k, "title": (v.get("statement") or v.get("title") or "")[:160]}
                                 for k, v in it]})
    d = _load("data/registry/URBAN_OWNER_METHOD_RULES.json")
    srcs.append({"source": "data/registry/URBAN_OWNER_METHOD_RULES.json", "kind": "URBAN_OWNER_METHOD_RULES",
                 "read_by": ["research/external_engine_lab (R8.x lab engines) and their tests; not by the M9 arch "
                             "route before ARCH_TAKEOFF_V2.3"],
                 "records": [{"id": r["rule_id"], "version": r.get("version"),
                              "applies_to": (r.get("scope") or {}).get("applies_to"), "digest": _h(r)}
                             for r in d["rules"]]})
    for rel, key in (("data/registry/OWNER_METHOD_FACTS.json", "facts"), ("data/registry/OWNER_FINISH_FACTS.json",
                                                                         "facts"),
                     ("data/registry/OWNER_PHYSICAL_FACTS.json", "facts")):
        d = _load(rel)
        srcs.append({"source": rel, "kind": "OWNER_PROJECT_FACTS (one other project, revision-scoped)",
                     "read_by": ["research/external_engine_lab only"],
                     "records": [{"pointer": f"{rel}#/{key}/{i}", "kind": r.get("kind"), "digest": _h(r),
                                  "statement": _text(r)[:200],
                                  "transfer": "FORBIDDEN (project / revision scoped)"
                                  if r.get("transfer_forbidden") or (r.get("statement") or {}).get("this_case_only")
                                  else "PROJECT_SCOPED"} for i, r in enumerate(d[key])]})
    d = _load("data/registry/OWNER_RULE_REQUESTS.json")
    srcs.append({"source": "data/registry/OWNER_RULE_REQUESTS.json", "kind": "OWNER_QUESTIONS (earlier route)",
                 "read_by": ["tools/a18_input_set.py"],
                 "records": [{"id": r["id"], "state": st, "subject": r.get("subject")}
                             for st in ("open", "answered") for r in d.get(st) or ()]})
    for rel in PROJECT_RULES:
        d = _load(rel)
        srcs.append({"source": rel, "kind": "PROJECT_RULES (the reference project)",
                     "read_by": ["tools/run_round6e.py", "tools/a18_input_set.py"],
                     "records": [{"pointer": f"{rel}#/{k}", "entries": len(v) if isinstance(v, (list, dict))
                                  else 1} for k, v in sorted(d.items()) if k in ("pantry", "stair", "elevator")]})
    srcs.append({"source": "engine/source/door_model.py", "kind": "ENGINE_CONSTANT",
                 "read_by": ["M9 V2.1 .. V2.3"],
                 "records": [{"id": "OWNER_DOOR_CLASSES_2026_10_13", "note": "owner door rules recorded as a code "
                              "constant only (not a rule-store file); now UP-DOOR-CLS-001 .. -006"}]})
    srcs.append({"source": "engine/source/arch_rooms.py LEXICON", "kind": "ENGINE_CONSTANT",
                 "read_by": ["M9 V1 .. V2.3"],
                 "records": [{"id": "room kinds", "note": "BATHROOM and LAUNDRY are WET; KITCHEN, PANTRY and "
                              "IRONING are SERVICE (dry finish path) - the owner wet-area scope (UP-WET-001) is "
                              "applied by ARCH_TAKEOFF_V2.3 only"}]})
    srcs.append({"source": "engine/profiles/URBAN_M*_GENERIC_CONVENTIONS_V*.json", "kind": "STRUCTURAL_CONVENTIONS",
                 "read_by": ["route G / M2 .. M8 structural routes"],
                 "records": [{"id": p.name} for p in sorted((ROOT / "engine/profiles").glob("*.json"))]})
    srcs.append({"source": "research/*/ (phase reports)", "kind": "QUESTION_LISTS_IN_DOCUMENTS",
                 "read_by": ["people only (no code reads them)"],
                 "records": [{"id": i, "topic": t} for i, t, _c, _r in CROSSWALK]})
    idx = {"schema": "URBAN_RULE_SOURCE_INDEX_V1", "generated_by": "tools/kb_index.py",
           "registry": "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json",
           "sources": srcs,
           "counts": {s["source"]: len(s["records"]) for s in srcs},
           "question_crosswalk": [{"earlier_ids": i, "topic": t, "category_now": c, "answered_by": r}
                                  for i, t, c, r in CROSSWALK]}
    return _scrub(idx)


def main(argv):
    text = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        OUT.write_text(text, encoding="utf-8")
    elif "--check" in argv:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == text
        print("index up to date" if same else "index differs from a fresh build: run tools/kb_index.py --write")
        return 0 if same else 1
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
