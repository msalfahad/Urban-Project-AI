"""OWNER_RULE_REGISTER.md and RULE_CONFLICT_PRECEDENCE_MATRIX.md from the committed registry (no hand transcription).

    python3 -I research/urban_m9_p2b1/make_registry_docs.py
"""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]
reg = json.loads((R / "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(R))
from engine.source import knowledge as K
OUT = R / "research/urban_m9_p2b1"


def cell(v):
    if isinstance(v, (list, tuple)):
        v = "; ".join(str(x) for x in v)
    return str(v or "-").replace("|", "/").replace("\n", " ")


L = ["# Permanent owner-rule register (deliverable 3)", "",
     f"Generated from `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json` (rule set `{reg.get('rule_set', K.RULE_SET)}`, "
     f"digest `{K.digest()[:16]}`; builder `tools/kb_build.py`). The JSON is the source of truth; this table is a view "
     "of it. Every rule names its authority, status, the code that applies it and the tests that prove it "
     "(`tests/m9_kb/test_kb_registry.py::test_every_code_and_test_link_exists` checks that every link exists).", "",
     f"{len(reg['rules'])} records; statuses: " + ", ".join(f"{s} {sum(1 for r in reg['rules'] if r['status'] == s)}"
                                                         for s in reg["statuses"] if any(r["status"] == s for r in reg["rules"])), "",
     "| Rule | Title | Status | Kind | Authority | Applied by | Proved by |", "|---|---|---|---|---|---|---|"]
for r in sorted(reg["rules"], key=lambda r: r["rule_id"]):
    a = r["authority"]
    L.append(f"| {r['rule_id']} | {cell(r['title'])} | {r['status']}" + (f" (superseded by {r['superseded_by']})" if
                                                                        r.get("superseded_by") else "") +
             f" | {r['kind']} | {cell(a.get('source'))} | {cell([c.split('::')[-1] for c in r['code']])} | "
             f"{cell([t.split('::')[-1] for t in r['tests']])} |")
L += ["", "## Rule logic (machine-readable records, abridged)", ""]
for r in sorted(reg["rules"], key=lambda r: r["rule_id"]):
    L.append(f"### {r['rule_id']} - {r['title']}")
    L.append("")
    L.append(f"- Purpose: {r['purpose']}")
    L.append(f"- Scope: {r['scope']}; elements {cell(r['elements'])}; locations {cell(r['locations'])}")
    if r.get("exceptions"):
        L.append(f"- Exceptions: {cell(r['exceptions'])}")
    L.append(f"- Logic: `{json.dumps(r['logic'], ensure_ascii=False, sort_keys=True)[:900]}`")
    if r.get("examples"):
        L.append(f"- Examples: `{json.dumps(r['examples'], ensure_ascii=False)[:600]}`")
    if r.get("limitations"):
        L.append(f"- Limitations: {cell(r['limitations'])}")
    L.append(f"- Dependent trades: {cell(r['dependent_trades'])}; assumptions permitted: {r['assumptions_permitted']}")
    if r.get("supersedes"):
        L.append(f"- Supersedes: {cell(r['supersedes'])}")
    L.append("")
(OUT / "OWNER_RULE_REGISTER.md").write_text("\n".join(L) + "\n", encoding="utf-8")

M = ["# Rule conflict and precedence matrix (deliverable 4)", "",
     "Generated from the registry (`precedence`, `conflicts`, rule UP-KB-PREC-001).", "",
     "## Precedence of evidence (UP-KB-PREC-001)", "", "| Rank | Evidence | Use |", "|---|---|---|"]
use = {"APPROVED_DRAWING": "a dimension, label or note on an approved drawing governs every rule below it",
       "APPROVED_SPECIFICATION": "a schedule or specification (door schedule, finish schedule, section heights)",
       "VERIFIED_GEOMETRY": "geometry the engine verifies itself (a strip that fits its opening, a closed face)",
       "PROJECT_DECISION": "a decision bound to one space of one project (URBAN_PROJECT_DECISIONS_V1)",
       "OWNER_RULE": "an owner-approved general rule (this registry)",
       "ASSUMPTION": "an owner fallback, labelled ASSUMED (HEIGHT_ASSUMED / AREA_ASSUMED); never confirmed",
       "UNRESOLVED": "no evidence: the item is withheld and asked for (B / C / D) or reported (E)"}
for p in K.PRECEDENCE:
    M.append(f"| {K.precedence_rank(p)} | {p} | {use.get(p, '-')} |")
prec = K.rule("UP-KB-PREC-001")["logic"]
M += ["", "Physical-fact hierarchy: " + " > ".join(prec.get("physical_fact_hierarchy") or []), "",
      "## Conflict register", "", "| Id | Between | State | Resolution |", "|---|---|---|---|"]
for c in reg["conflicts"]:
    M.append(f"| {c['id']} | {cell(c['between'])} | {c['state']} | {cell(c['resolution'])} |")
M += ["", "## Question categories (UP-KB-QUES-001)", "", "| Category | Meaning | Reaches the owner |", "|---|---|---|"]
cats = K.rule("UP-KB-QUES-001")["logic"]["categories"]
for c in K.CATEGORIES:
    M.append(f"| {c} | {cell(cats.get(c))} | {'yes (with an OQ id)' if c in ('C_RULE_CONFLICT', 'D_MISSING_OWNER_POLICY') else 'no'} |")
M += ["", "## Question catalogue (the reason patterns the engine raises -> category)", "",
      "| Pattern | Item | Category | Group | Rule | Owner question |", "|---|---|---|---|---|---|"]
for q in reg["question_catalogue"]:
    M.append(f"| `{q['pattern']}` | {cell(q.get('item'))} | {q['category']} | {q['group']} | {cell(q.get('rule'))} | "
             f"{cell(q.get('question_id'))} |")
(OUT / "RULE_CONFLICT_PRECEDENCE_MATRIX.md").write_text("\n".join(M) + "\n", encoding="utf-8")
print("ok", len(L), len(M))
