# T-257: K1 boundary declarations from the T-210 record

Head: working branch `e418c5e0`. Scope: test hygiene / infrastructure; no engine module, no rule, no quantity changed.
Tool: `research/agents_t257/k1_declarations.py` (stdlib only, static AST, writes nothing). Tests:
`tests/t257_k1_declarations/` (20). Record cited, not copied: `research/agents_t210/K1_DECISIONS.json` (Checker T-210
verdict, merge dadf8446).

## 1. What changed

| File | Change |
|---|---|
| `tests/r8_1/test_r8_1_boundaries.py` (`test_k1_is_stdlib_only_in_r8_1`, `by_design`) | +18 entries, one per ALLOWED_OUTSIDE_K1 record (17 x `{"shapely"}`, 1 x `{"numpy"}`), each with a comment naming its record. The assertion line, `EXPECTED_MODULES` (16 K1 core modules) and the loop are byte-identical. |
| `tests/t210_guard_followups/test_k1_decision_record.py` (2 real-tree tests) | **Outside the row's Files (reason in section 3).** `test_record_covers_every_offender_on_the_tree` runs the V2 check (same T-210 rules plus the declaration rules); `test_by_design_is_read_from_the_k1_test_itself` asserts by_design equals the four R8-era entries plus exactly one entry per ALLOWED record (18). Both stay exact; neither is narrowed. |
| `research/agents_t257/k1_declarations.py` | V2 check: the T-210 rules on the offenders under the four R8-era exceptions only, plus one check per declaration. |

## 2. Result on the tree

`python3 -I research/agents_t257/k1_declarations.py check`:
`offenders under the R8-era exceptions 24; records 24; declarations 18; K1 test still meets 6; K1 core modules reaching
one: 0; released engine/source/arch_v29.py reaches: []`, `problems 0`.

The K1 test **stays red, as the row expects**: it now meets only the six modules that may not be declared, in this order
(`... k1_declarations.py remaining`):

| Module | Package (line) | Decision |
|---|---|---|
| arch_v30.py | ezdxf (276) | OUTSIDE_K2_GATE |
| arch_v302.py | ezdxf (210) | OUTSIDE_K2_GATE |
| concrete_ledger_v3.py | ezdxf (204) | OUTSIDE_K2_GATE |
| opening_area.py | ezdxf (461) | OUTSIDE_K2_GATE |
| opening_height_pdf.py | pymupdf (84) | NOT_REGISTERED_HOLD |
| plot_edge_members.py | ezdxf (156) | OUTSIDE_K2_GATE |

Known-failures ledger (`research/agents_t202/known_failures.json`, keyed by id): the five boundary ids stay KNOWN and no
id is NEW. Delta for the ledger's next rebuild (not edited here: outside the row):

| Id | Before | After T-257 |
|---|---|---|
| `tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1` | K1_NOT_STDLIB, 24 modules, first `('engine/source/arch_v213.py', 'shapely.geometry')` | 18 shapely / numpy causes **closed by declaration**; still FAILED on the 6 modules above; first `('engine/source/arch_v30.py', 'ezdxf')`. Closes only when the 5 ezdxf fixes below and the pymupdf fix (T-210 (b)) merge. |
| `tests/r8_1/test_r8_1_kernel_ocs.py::test_k1_is_independent_of_ezdxf`, `tests/r8_2/test_r8_2_k2.py::test_k1_does_not_import_ezdxf` | K1_IMPORTS_EZDXF (5 modules) | unchanged; close with the 5 fixes below |
| the two B5_B6 ids (r8_0, r8_1) | DEPENDENCY_NOT_REGISTERED (pymupdf) | unchanged (licence, PLAN_READER 'never PyMuPDF'; T-210 (b) fix proposal) |

## 3. Why two T-210 test lines had to change (scope note for the Checker and the Lead)

The T-210 tool reads `by_design` from the K1 test itself. Declaring a module there removes it from the T-210 offender
list, so the unchanged T-210 check reports **18 STALE** and `test_by_design_is_read_from_the_k1_test_itself` (an exact
equality with the old four entries) fails: measured on this tree before the T-210 edit, 2 NEW failures
(`test_record_covers_every_offender_on_the_tree`, `test_by_design_is_read_from_the_k1_test_itself`). The row's Files
(K1 by_design, research/agents_t257, tests/t257_*) cannot hold a NEW-0 result. Least change chosen: the record and the
T-210 tool are untouched; the two real-tree tests are re-pointed, each still exact:
- the coverage test keeps every T-210 rule (UNRECORDED / STALE / PACKAGES_DIFFER / FIELD_MISSING / BAD_DECISION /
  NOT_REGISTERED_BUT_ALLOWED / K1_CORE_REACHES_OFFENDER) on all 24 modules and the `>= 24` floor, and adds the
  declaration rules;
- the snapshot test now pins 22 entries, derived from the record, instead of 4.
The eight synthetic T-210 tests are unchanged and pass. If the Checker rules this edit out of scope, the alternative is
the Lead widening the row's Files to the T-210 test file; there is no in-scope way to keep NEW 0.

## 4. Declaration rules (V2 check) and adverse cases

Each declaration must have a T-210 record (DECLARED_WITHOUT_RECORD), decision ALLOWED_OUTSIDE_K1 (DECLARED_NOT_ALLOWED:
an OUTSIDE_K2_GATE or NOT_REGISTERED_HOLD module declared is refused), a package set equal to the record's
(DECLARATION_PACKAGES_DIFFER) and actually imported (DECLARED_NOT_IMPORTED), each package pinned `name==version` in
requirements.txt (NOT_PINNED) and in the B-5 register (NOT_REGISTERED); a whole-module (None) declaration is refused
(DECLARED_WHOLE_MODULE); a declared file name that exists twice under engine/source is refused, because the K1 test
matches by NAME and would exempt the second file silently (AMBIGUOUS_FILE_NAME; on this tree only `__init__.py` repeats,
never declared); the four R8-era exceptions may not change (R8_ERA_CHANGED); every ALLOWED record must be declared
(UNDECLARED_ALLOWED). A NEW third-party import anywhere in engine/source still fails as UNRECORDED, and a new package
inside a declared module still reaches the K1 test (the declaration names packages, not the file).

## 5. Fix proposals for the 5 OUTSIDE_K2_GATE modules (none done here; each its own task, new module version)

Common rule: the module never imports ezdxf; it takes what it needs from the K2 route `engine/source/cad/kernel_ezdxf.py`
(registered role "D2/K2 route only"). Two K2 facts every fix must respect:
- `kernel_ezdxf.load(path)` returns `(doc | None, [SourceFinding])` and turns a decode error (OSError,
  UnicodeDecodeError, StopIteration, DXFError) into a ROUTE_DECODE_FAILED finding, whereas the five modules call
  `ezdxf.readfile` and let it raise. A fix that silently changed raise -> empty result would turn a failed read into
  "no rows / no pieces", i.e. missing becomes 0. Each new version must keep the failure visible: either re-raise on
  `doc is None` with the finding's text, or return the module's own HELD state; the test must show both.
- K2 has no wrapper for `ezdxf.path` flattening or `ezdxf.xclip`. Those two need one small ADDITIVE function each in the
  K2 route (kernel_ezdxf.py is SHARED, 11 direct / 102 transitive importers, HIGH risk: L3 on its importers) or a sibling
  K2 module under engine/source/cad/ (which would then need the Lead's wording in the ezdxf register role and in the two
  'K1 does not import ezdxf' tests, since those exempt only kernel_ezdxf.py; never a by_design entry).

| Module (line) | What it uses ezdxf for | Callers | Proposed new version | Proof needed |
|---|---|---|---|---|
| arch_v30.py (276-277, `strap_changes`) | `ezdxf.readfile(structural)` then modelspace queries for strap outline pieces | tools/urban_boq_m9.py:3216; inside the Gate-B-verified V3.0.x chain (28 direct importers) | lane I, next V3.0.x step: a K2-reading `strap_changes` in the V3.0.x head module (arch_v30.py never edited), the runner switched to it | byte-identical strap changes and log on tests/t131_arch_v30 and on the V3.0.x candidate run; adverse: unreadable DXF -> visible failure, never 0 straps |
| arch_v302.py (210-212, `schedule_rows_from_drawing`) | `ezdxf.readfile` + INSERT attribs of the footing schedule | tools/urban_boq_m9.py:3258 | same V3.0.x step | **no test reaches this function today** (grep of tests/): a synthetic schedule DXF fixture comes first, then byte-identical rows; adverse: unreadable file |
| concrete_ledger_v3.py (204-205, `read_section_drawing`) | `ezdxf.readfile` + DIMENSION / LWPOLYLINE of a section DXF ($DIMLFAC) | internal (line 479); no engine importer | CONCRETE_LEDGER_V3 successor (V4 or a K2 reader module) | **no test reaches this function today**: synthetic section DXF fixture first (DIMLFAC override, LWPOLYLINE >= 4 vertices), then identical dims / outlines |
| opening_area.py (461, `read_view`) | `ezdxf.path` to flatten bulges / curves of an elevation frame | opening_height_pdf (OA), tests/t078_opening_area, tests/t013 | OPENING_AREA_V2 importing a K2 flattening helper | identical view segments on tests/t078 (bulged polyline, arc, nested insert) |
| plot_edge_members.py (156, `_xclipped`) | `ezdxf.xclip.XClip(ins).has_clipping_path` | arch_v30 (strap pieces), line 194 | PLOT_EDGE_MEMBERS_V2 importing a K2 `has_clipping_path(insert)` helper; an unreadable filter stays "clipped -> HELD" | tests/t073 identical; adverse: unreadable extension dict -> HELD, never measured |

Order recommended: plot_edge_members and opening_area first (smallest, already tested), then the two V3.0.x readers in
one lane I step (they share the runner), concrete_ledger_v3 last (unwired). pymupdf: T-210 (b) proposal stands
(OPENING_HEIGHT_PDF_V2 on a permissive reader); no owner question (PLAN_READER already decides 'never PyMuPDF').

## 6. Lessons-register row proposed

"A test that pins a snapshot of another test's configuration (T-210's exact by_design equality) makes the second test's
own extension mechanism unusable without editing the first: when a task uses a declaration mechanism, list every tool
or test that reads that declaration in the row's Files." Scope: test infrastructure; provenance T-257.
