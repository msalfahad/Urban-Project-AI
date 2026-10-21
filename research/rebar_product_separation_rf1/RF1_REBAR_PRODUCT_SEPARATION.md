# RF.1: two separate reinforcement products (architecture correction before S4)

Baseline: `96978ef` (S3.1). S4 has not been started.

## The two products

| | ACCURATE_BOQ_REBAR | ROUGH_REBAR_SUMMARY |
|---|---|---|
| Arabic | حديد التسليح الفعلي من المخططات | تقدير تقريبي للحديد حسب حجم الخرسانة |
| purpose | official reinforcement takeoff | estimating / sanity check only |
| input | structural source registers (occurrences, schedules, details, deterministic geometry, approved claims, explicitly identified approved methods) | the final concrete register only |
| method | bar-by-bar / component-by-component (trade engines) | concrete m3 x category ratio |
| states | VERIFIED / LOWER_BOUND / PROVISIONAL / BLOCKED_MODELLED / BLOCKED_UNQUANTIFIED, never merged | released basis and modelled basis; blocked concrete excluded |
| status | FINAL / LOWER_BOUND / PARTIAL / BLOCKED per category; project FINAL or FINAL_REBAR_NOT_ESTABLISHED | URBAN_OWNER_ESTIMATING_RULE, SANITY_CHECK_ONLY |
| engine | `engine/source/accurate_boq_rebar.py` (collector) + the trade engines | `engine/source/rough_rebar_sanity.py` + `engine/profiles/URBAN_ROUGH_REBAR_PROFILE_V1.json` |

Dependency direction (enforced by test):

```
STRUCTURAL SOURCE REGISTERS -> ACCURATE BOQ REBAR  ---\
                                                       >  REPORT LAYER (rebar_sanity_variance, rebar_boq_sections)
CONCRETE REGISTER           -> ROUGH REBAR SUMMARY ---/
```

There is no arrow between the two engines. Only the report layer reads both, and it writes neither.

## What was implemented

- `accurate_boq_rebar.py`: collects parts. Each part needs a registered category and component (FOOTING_BOTTOM_SHORT ... SLAB_TOP_SUPPORT), one of the five states, and a basis from the admissible set. A basis such as ROUGH_RATIO, KG_PER_M3, FREELANCER_QS_REFERENCE, EXTERNAL_ORACLE or BENCHMARK is refused. A BLOCKED_UNQUANTIFIED part can never carry kg. Projected = released + provisional (never blocked). `from_column_rebar` maps the column-engine parts.
- `rough_rebar_sanity.py`: rewritten as ROUGH_REBAR_SUMMARY. It takes concrete occurrences only and refuses any steel / kg / bar field. The mandatory note is carried verbatim. RAFT, PILE_CAP, RETAINING_WALL, WATER_TANK, LIFT_*, PARAPET_*, LINTEL and SPECIAL_RC_ELEMENT return ROUGH_RATIO_NOT_CONFIGURED ("needs an explicit owner rule").
- `rebar_sanity_variance.py` (report layer): ACCURATE_PROJECTED_KG, ROUGH_REFERENCE_KG, SANITY_VARIANCE_KG / _PERCENT.
  - A variance is computed only when the category has nothing blocked; otherwise the figures are shown SIDE_BY_SIDE_ACCURATE_INCOMPLETE.
  - A large variance raises only REBAR_SANITY_REVIEW. Inputs are deep-copied and never changed, and the word "missing" never appears.
- `rebar_boq_sections.py` (report layer): SECTION 1 is ACCURATE BOQ REBAR (released / provisional / blocked t + official status). SECTION 2 is ROUGH REBAR SUMMARY (concrete / ratio / rough t + mandatory note). An optional SANITY VARIANCE section can follow. No row, column or total crosses sections.
- Profile V1: authority URBAN_OWNER_ESTIMATING_RULE (ratios unchanged), "BBS rules" added to `not`, and the history recorded.
- `tests/structural_comparison_engine/test_rebar_product_firewall.py` (+ `rebar_product_registry.py`):
  - static AST import closure, runtime-faithful (package `__init__` included), of every accurate module and builder: 9 engine modules + 8 project builders, 127 files reached;
  - a runtime `sys.modules` check;
  - a constants scan: no profile / module / reference-QS / oracle identifier, and no reference-QS or oracle figure, also in kg or rounded;
  - the rough closure is the rough file alone;
  - the report layer is the only reader of both;
  - every rebar-aware engine file must be declared;
  - accurate BBS tests must not use the rough engine, profile or reference figures;
  - plus behaviour tests.

## Audit: existing code against the firewall

Violations found and fixed:

1. **The S3.1 rough engine took accurate figures as input** (`rough_check(occurrences, profile, actual)`). That was an arrow from ACCURATE into ROUGH. The comparison now lives in the report layer, and the rough engine is concrete-only.
2. **The S3.1 default mapping sent RAFT and PILE_CAP to FOUNDATIONS_RELATED**, and the keyword classifier sent "RC retaining wall" to STRUCTURAL_WALL. All of these are now NOT_CONFIGURED.
3. **Profile authority was URBAN_OWNER_RULE.** It is now URBAN_OWNER_ESTIMATING_RULE.
4. **S3.1 variance labels were `delta_kg` / BBS_COMPLETE_VARIANCE.** They are now SANITY_VARIANCE / REBAR_SANITY_REVIEW.
5. **`tests/test_finance_outturn_steel.py` used 44,190 kg / 352.44 m3** (the reference-QS totals) in the ratio-band test, and 352.44 in the outturn test. Both were replaced with neutral synthetic values. The new scan catches the kg and rounded variants and fails on the old file.

Confirmed clean (no change needed):

- No accurate module or builder imports, opens or embeds the rough engine, the profile, the report layer, the comparison modules, the S3.1 comparison package or a reference-QS / oracle figure. This covers rebar_model, column_rebar, slab_rebar_binding, bbs_optimiser, rebar_unit_mass, waste_procurement (procurement), urban_methods_v3, bbs_steel, and the R3 / R4 / V3b / S3 / S3.1 builders.
- The existing BBS / known-answer tests use none of them.

Observations left unchanged (not violations, listed for decision):

- `engine/bbs_steel.ratio_check` (70–200 kg/m3 band) and `rebar_model.ratio_qa` (QA_ONLY) are kg/m3 QA helpers inside accurate modules. They never produce a quantity (existing G28 test plus the new firewall). I recommend moving them to the sanity layer in a cleanup. They were not moved now because `engine/__init__` and older tests import them.
- `engine/audit` R09 / T06 steel-ratio bands audit externally supplied BOQ workbooks. They are not a rebar product.
- The V3 / V3b structural BOQ workbooks (`engine/reporting_v3`) show accurate rebar only (NET / PROC / STRAIGHT bases, TOTAL PROJECT REBAR = PARTIAL) and contain no rough figure. They do not yet use the two-section layout; migrate them to `rebar_boq_sections` at the next structural BOQ rebuild.
- Five older non-rebar tests use 352.44 as sample concrete (analytics, audit log, create project, documents render, end-to-end), and the QS-audit fixture uses 39.75 / 77.63. They are outside the rebar firewall; I recommend neutralising them in a separate cleanup.
- The S3.1 comparison package is frozen: its builder now uses `s3_1_rough_rebar_snapshot.py` + `s3_1_rough_profile_snapshot.json`, and it rebuilds byte-identically.

## Open owner decisions

1. REBAR_SANITY_REVIEW threshold: the default is 25% (URBAN_DEFAULT_CANDIDATE). Please confirm or set a value.
2. Accurate category → rough category for the variance: WALLS, LIFT, PARAPET and SPECIAL_RC are NOT_CONFIGURED. Necks currently follow their accurate category. Confirm whether necks belong under FOUNDATIONS_RELATED.
3. Move the kg/m3 QA helpers out of the accurate modules (recommended).

## Next

S4: GENERIC FOOTING REBAR ENGINE, which produces ACCURATE_BOQ_REBAR parts only. The sequence is S3 columns → S4 footings → S5 beams → S6 slabs → S7 stairs / pool / dome / lift / parapet / special RC → full structural conservation. Not started.

## Test run

Full suite (`python -m pytest -q -p no:cacheprovider`) on the RF.1 working tree: 6265 collected (6237 + 28 new), 6162
passed, 100 xfailed (pre-existing), 3 skipped (pre-existing), 0 failed, 0 errors, 266 s. The S3.1 comparison package
rebuilt byte-identically (`--twice`).
