# Provenance contract update: generic element identity

## What was wrong

- The pre-S5 `ground_system_provenance.validate_s5_part` built a view of each beam part in which `FOOTING_OCCURRENCE_ID`
  and `FOOTING_MARK` were filled with the beam's id and mark. It then called the footing validator
  (`accurate_boq_rebar.validate_s4_part`).
- Nothing was written to disk that way, but the contract accepted a beam identified through footing slots. A beam is
  not a footing.

## The contract now

| Field | Meaning |
|---|---|
| ELEMENT_OCCURRENCE_ID | physical occurrence (footing, ground-beam span, strap, ...) |
| ELEMENT_MARK | drawing mark / tag (or the typical-detail family when untagged) |
| ELEMENT_FAMILY | FOOTING, GROUND_BEAM, STRAP_BEAM, COLUMN, BEAM, SLAB |

- Every other field, vocabulary and rule is the S4 one: drawing sha, revision, sheet region, source handles and text,
  component, rule, convention, measurement / authority / release states, formula, inputs, engine / register / round
  stamp, bounds and blocking reason.
- These are imported from `accurate_boq_rebar`, never copied. No second provenance system exists.

## Compatibility

| Record | Result |
|---|---|
| frozen S4 record (FOOTING_* only) | read as ELEMENT_FAMILY = FOOTING; same verdict as validate_s4_part |
| FOOTING record carrying both | FOOTING_* must equal ELEMENT_* |
| GROUND_BEAM / STRAP_BEAM / ... with any FOOTING_* key | **rejected** |
| GROUND_BEAM with FOOTING_* as its only identity | **rejected** |
| S5 template | ELEMENT_* only (no FOOTING_* key is written for a beam) |

## How it was checked

- **Equivalence:** `rebar_provenance.validate_part` and `accurate_boq_rebar.validate_s4_part` were run over the 84
  frozen S4 provenance records, unmutated and with each of 9 mutations. That is 840 cases with identical accept /
  reject.
- **S4 is untouched:**
  - S4 files are not edited and the S4 freeze manifest still matches;
  - `footing_rebar` still calls `validate_s4_part`.
- **Pre-S5 package rebuilt:**
  - its templates now carry ELEMENT_* (no FOOTING_* key);
  - its bar-run text points here instead of the removed minimum;
  - no status changed.
