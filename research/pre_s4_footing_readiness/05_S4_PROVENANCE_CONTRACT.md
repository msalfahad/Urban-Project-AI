# 05 S4 provenance contract

**What it is:**
- the minimum record every Accurate Footing Rebar (S4) part carries, from its first implementation;
- an extension of the existing accurate part (`engine/source/accurate_boq_rebar.py`), not a second provenance system;
- `part["provenance"]`, checked by `validate_s4_part()`. `summarise_s4()` refuses any part that fails it.

The run-manifest digests stay where they are (`run_manifest.py`). The comparison stamp is the same four fields that `comparison_scope` checks.

## Mandatory fields (`S4_PROVENANCE_FIELDS`)

| Field | Content | Check |
|---|---|---|
| PROJECT_ID | project key | non-empty |
| DRAWING_ID | source file name | non-empty |
| DRAWING_SHA | sha256 of the drawing | 64 hex |
| REVISION | source revision id (Alsenan: `ALSENAN_ST7757_DXF`) | non-empty |
| SHEET_REGION | sheet / region (e.g. Schedule of Footings p.9 + FP) | non-empty |
| SOURCE_HANDLES | insert / ATTRIB / tag / outline handles | non-empty list of strings |
| SOURCE_TEXT | the raw source text(s) | non-empty |
| FOOTING_OCCURRENCE_ID | the plan occurrence (outline + tag) | non-empty |
| FOOTING_MARK | type mark | non-empty |
| COMPONENT | accurate component | equals the part's `component` |
| RULE_ID | rule or method id | non-empty |
| CONVENTION_ID | measuring convention (cover, end detail, count convention) | non-empty |
| MEASUREMENT_STATE | `MEASURED` / `SCHEDULE_DERIVED` / `CONVENTION_DERIVED` / `NOT_MEASURED` | in list |
| AUTHORITY_STATE | see below | in list; constrains the state |
| RELEASE_STATE | VERIFIED / LOWER_BOUND / PROVISIONAL / BLOCKED_MODELLED / BLOCKED_UNQUANTIFIED | equals the part's `state` |
| FORMULA | the arithmetic, written out | non-empty |
| INPUTS | named inputs | a mapping (may be empty only on a blocked part) |
| ENGINE_COMMIT | code commit | non-empty (comparison stamp) |
| REGISTER_VERSION | register / schema version | non-empty (comparison stamp) |
| CALCULATION_ROUND | e.g. `S4` | non-empty (comparison stamp) |
| BLOCKING_REASON | required on `BLOCKED_UNQUANTIFIED` | non-empty |

## Bounds (`S4_BOUND_FIELDS`)

- The set `LOW`, `BEST`, `HIGH`, `UNQUANTIFIED_COMPONENTS` is all-or-none.
- `LOW ≤ BEST ≤ HIGH`, and `HIGH = None` means unbounded above.
- `UNQUANTIFIED_COMPONENTS` lists registered components only (e.g. `BOXED_REBAR`).
- A `LOWER_BOUND` part must carry the bounds.

## Authority → allowed state

| AUTHORITY_STATE | May carry kg in |
|---|---|
| SOURCE_EXPLICIT, SOURCE_DERIVED_HIGH_CONFIDENCE, APPROVED_PROJECT_CLAIM, APPROVED_ENGINEERING_METHOD | any state |
| UNAPPROVED_METHOD | PROVISIONAL / BLOCKED_MODELLED only |
| PROJECT_PATTERN_ONLY, GENERIC_HYPOTHESIS, UNRESOLVED, SOURCE_CONFLICT | none: the part is `BLOCKED_UNQUANTIFIED` |

This is the §11 / §13 rule in code: known accurate components plus explicit blocked components, never an invented BOXED interpretation.

## Footing release (`footing_rebar_guard.footing_release`)

| Footing state | When |
|---|---|
| REBAR_VERIFIED | every part VERIFIED and the occurrence established |
| REBAR_LOWER_BOUND | released parts exist and something is unquantified / lower-bound / provisional (e.g. BOXED blocked) |
| REBAR_PROVISIONAL | an occurrence query is open (F3 OQ-11), or only provisional parts exist |
| REBAR_BLOCKED | the occurrence is blocked (F / F10 conflict, tag without outline), or nothing is released |

## Comparison stamps (`comparison_scope`)

- `STAMP_FIELDS = ENGINE_COMMIT, REGISTER_VERSION, DRAWING_SHA, CALCULATION_ROUND`.
- `compare_stamped()` handles the three relations:
  - **different drawing:** `NOT_COMPARABLE`;
  - **different engine state:** refused unless the caller declares `cross_state=True` for a regression comparison, and then labelled `CROSS_ENGINE_STATE`;
  - **same state:** a normal comparison.
- A stamp with a missing or extra field is refused.

## Tests

`tests/pre_s4_footing_readiness/test_s4_provenance_contract.py` covers:
- every mandatory field missing or empty;
- consistency (component, state, sha, lists);
- the authority rules;
- the blocked reason;
- the bounds;
- `summarise_s4`;
- the stamp relations.

Existing non-S4 parts are unaffected; this is checked by a test and by the rest of the suite.
