# Engineering skills and knowledge audit (Phase 2B-6, Part 9)

## 1. The six repository skills (`.claude/skills/urban-*/SKILL.md`)

| skill | correct? | actually invoked by the workflow? | duplicates | consistent with the registry? | prevents repeated mistakes? | tested? |
|---|---|---|---|---|---|---|
| `urban-boq-proof` (verification chain) | yes: the expected value is never taken from the implementation | **no**: a skill is guidance a Claude session loads by its description; no CLI, CI job or test invokes it | overlaps `urban-mcp-benchmark` on "independent truth" | yes | yes, by method; it did not stop tonight's D-P6-02 (a benchmark blind spot) | structure only |
| `urban-cad-audit` (drawing readiness) | **was stale**: it ran V2.5 and did not know the exploded-door, turned / exploded-column, nested-plan or basin-only failure modes. **Updated tonight** to V2.6 and `tools/arch_run_audit.py` | no (guidance); the run audit makes its checks executable | - | yes | **now yes**: the audit turns the checks into findings with evidence | structure; the audit itself has 9 tests |
| `urban-rule-reconciliation` | yes: precedence and provenance classes | no | - | it lists knowledge 1.1.0 and rules 1.5.0. The owner's Part 4 basin statement is not yet in either (knowledge 1.2.0, `NEXT_IMPLEMENTATION_PLAN.md`) | yes, if followed | structure only |
| `urban-freeze-integrity` | yes | no; but `tools/freeze_verify.py` and the byte-identity snapshots are executed every phase | partly duplicates `research/freeze_integrity/README.md` | yes | yes (freeze verifier 0 differing for every phase) | the verifier has its own tests |
| `urban-mcp-benchmark` | yes; tonight's library run of U-C4N followed its method on synthetic fixtures | no | overlaps `urban-boq-proof` | n/a | yes | structure only |
| `urban-floorplan-vision-review` | yes: vision is never a BOQ basis | no | - | n/a | yes | structure only |

`tests/m9_p2b5_bench/test_skills.py` checks the files and their structure, not their behaviour. Six required sections
are present, every referenced path exists, and no private name appears.

**Conclusion.** The skills are correct, but they are documentation: they protect only a session that reads them. What
actually prevents repeated mistakes in this repository is executable:

- tests asserting defects as found;
- the freeze verifier;
- byte-identity snapshots;
- now, the run audit.

**Recommendation.** Every skill that describes a check should name the executable that performs it. `urban-cad-audit`
now does: `tools/arch_run_audit.py`.

## 2. How the engine should remember decisions: knowledge classes

**What exists today.**

- `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json`: 39 rules with kind, authority, status, history, conflicts and
  grouped owner questions. Every run pins its digest.
- `rules/` 1.5.0: the measured rules, materials and conventions.
- `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl` and `ERRATA.jsonl`: append-only, hash-chained.
- Each phase's `OWNER_DECISIONS.md`: three copies, partly duplicated (deduplicated tonight in `OWNER_DECISIONS.md`).

**The gap.** These hold only some of the classes Part 9 requires, in different places, with no rule that every
statement carries exactly one class.

| class | definition | where it lives today | proposed home (version-controlled) | may it make a BOQ quantity? |
|---|---|---|---|---|
| VERIFIED_FACT | a mathematical or physical truth, or a measured result proven against independent truth | tests (hand truth), worked examples | `knowledge/` as ENGINEERING_RULE with a `proof` (test id) | yes (as method) |
| DRAWING_EVIDENCE | what a given drawing shows (entity handles, dimensions, texts) | run outputs (per run, not remembered) | per-run evidence, referenced by hash; never promoted to a rule | yes (as input) |
| OWNER_POLICY | an owner-approved standard for all projects | `knowledge/` OWNER_RULE / OWNER_STANDARD | unchanged; the Part 4 statements of this program go in as new versions (e.g. the basin rule) | yes (as rule) |
| PROJECT_DECISION | a decision valid for one project | `knowledge/` PROJECT_DECISION; the project rules sheet | unchanged, scoped by project id and drawing revision; invalidated on a new revision | yes, in that project |
| ASSUMPTION | a stated fallback in the absence of evidence (e.g. a height) | `rules/` conventions (low / base / high); facts files | every use labelled ASSUMED with its authority; never silent | only as ASSUMED / bounded |
| INTERPRETATION | how the software reads ambiguous evidence (e.g. a held door) | method code and run records | method documentation per method version; each output field carries its interpretation state (e.g. DOOR_SYMBOL_FIT_REVIEW) | only as PROVISIONAL |
| UNVERIFIED_CLAIM | something stated but not checked (a paper's accuracy, a tool's README, an earlier report's figure) | report prose | a claims list in each research report, with "verified by" empty until checked | never |
| SOFTWARE_DEFECT | the software misreads evidence | defect registers per phase; tests "as found" | one register (`ENGINEERING_DEFECT_REGISTER.md`), each defect with its as-found test, until a method closes it | - |
| OWNER_QUESTION | a decision only the owner can make | `knowledge/` `owner_questions` (4, grouped); phase lists | one register; each question keyed by (topic, scope) and checked against existing rules before it is asked; answered questions link to the rule that answers them | - |

## 3. Deduplicating questions (the gate before asking)

A question may be put to the owner only if all four checks fail:

1. **Does a registry rule or owner statement answer it?** Then cite the rule. Tonight: the basin lobby (Part 4), the
   wet-room skirting (UP-WET-001), the door-opening meaning (UP-DOOR-OPEN-002).
2. **Does the drawing settle it?** Then read the drawing. Tonight: the held door's width.
3. **Is it the software's inability to read the drawing?** Then it is a defect, not a question. Tonight: single-instance
   layers, turned columns.
4. **Is it already open under another wording?** Then merge it. The key is (topic, scope).

`OWNER_DECISIONS.md` applies this gate to the three earlier lists:

- 4 questions are answered or withdrawn;
- 3 are reclassified as software or drawing matters;
- 10 remain open, including the authorisations and inputs this program needs.

## 4. Proposed implementation (design only; changing `knowledge/` changes run records, so it rides with the next method)

1. **knowledge 1.2.0**, a new file beside 1.1.0, which stays unchanged and is used by V2.6. It adds a `class` field to
   every record, plus the new owner rules:
   - UP-WET-002: a basin alone does not make a space wet;
   - the Part 4 door statements, already in UP-DOOR-OPEN-002, cross-referenced.
2. **One machine-readable owner-question register**, with the four-check gate as a test: a new question whose key
   matches a rule's `answers` list fails the test.
3. **Every SOFTWARE_DEFECT has an as-found test** (as `tests/m9_p2b6/test_p2b6_found_defects.py` does). Closing a
   defect moves its assertion to the new method's tests with the truth; the old method keeps the as-found assertion.
4. **Every skill names its executable check.**
