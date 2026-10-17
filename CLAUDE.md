# Urban-Project-AI: agent guide

Kuwait BOQ / quantity takeoff engine: DWG/DXF/PDF plans in, traceable BOQ out. Python 3.11, ezdxf 1.4.4, shapely 2.2.0.
Working branch: `claude/access-permissions-setup-ii24ws` (`main` holds only a README). Goal: quantities a reviewer can
independently verify; speed never outranks that.

## Find the code (navigation aids; the sources stay authoritative)

1. `docs/ROUTE_QUICK.md`: one table, task topic -> module to open first, risk, rules, defects, BOQ capability.
2. `python3 -I tools/codemap.py route "<task in words>"`: primary and secondary topics, modules, rules, unresolved defects,
   suggested tests. `python3 -I tools/codemap.py impact <path>`: importers, risk class, frozen status, tests that reach it.
3. `docs/ROUTING.md` (one section per topic), `docs/CODEMAP.md` (every module, symbol line ranges), `docs/RULES_INDEX.md`
   (every rule, version, supersession, code, tests).

Prefer targeted reading: grep the symbol, then read its line range; widen whenever correctness needs it. Consult
`research/` when it holds the relevant engineering decision, defect evidence, source provenance or frozen-method
constraint (the routing index points to it); do not load reports, skills or registries that the task does not need.

## Workflow

Route the task -> read its rules and unresolved defects -> locate the symbols -> `impact` on each file you will change ->
short plan if more than one file -> implement -> validate at the level below -> freeze check -> regenerate the maps if
you added, moved or renamed files, added a rule version or a defect register (`python3 -I tools/codemap.py`) -> handoff.

## Validation (your judgement; nothing is skipped automatically)

| Level | Use for | Run |
|---|---|---|
| L1 | iterating; LOW risk | `py_compile` on the changed file + its rule tests or one topic test folder |
| L2 | MEDIUM: one subsystem | the topic's test folders |
| L3 | HIGH: shared modules, geometry, CAD, units, rooms, walls, release, aggregation | L2 + the importer test folders `impact` lists |
| L4 | CRITICAL, a method-version release, an acceptance handoff | full suite on the final commit, compared test by test with the baseline |

`route` prints the L1-L3 commands for the topic. A full-suite result belongs to the commit it ran on; later changes need
their own validation. Keep known failures (private inputs absent, timing flakes) separate from new ones; never call a
failing suite green. After any change under `engine/`, `tools/`, `rules/`, `knowledge/` or `data/registry/`:
`PYTHONDONTWRITEBYTECODE=1 python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`
must print `frozen artefacts differing from the index: 0`; otherwise stop and report.

Targeted tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q tests/<folder or file>`. The root
`conftest.py` fails a session that changes files under `data/` or `tests/`; tests must write only to temporary folders.

## Never break

- Frozen methods (ARCH_TAKEOFF_V1 ... released versions), frozen baselines (`impact` marks frozen files) and existing
  rule / knowledge version files are never edited in place. A behaviour change is a new method or rule version.
- Do not change quantities, owner decisions or engineering assumptions unless the task asks for it.
- A module, a passing synthetic test or an index entry is not proof that a BOQ item is measured correctly: the BOQ family
  registry status (INTEGRATED_AND_TESTED, PARTIAL, EXPERIMENTAL, ...) and independent checks are.

## Size the work to the ask

Small (one value, one function, one rule record, one bug): minutes, L1-L2. Medium (new field, rule version, method tweak):
L2-L3. Large (new method version, new stage): 5-line plan first, L4 at the end. No reports, proofs, packages or registers
unless the prompt asks for them.

## Handoff

End with 3-5 lines (and the same in the commit message body): what changed (file:line), the validation level run and on
which commit, what was not done or remains uncertain. Deeper project skills live in `.claude/skills/` (BOQ proof, CAD audit,
freeze integrity, rule reconciliation, MCP benchmark, floor-plan vision review): use them for that kind of work only.
