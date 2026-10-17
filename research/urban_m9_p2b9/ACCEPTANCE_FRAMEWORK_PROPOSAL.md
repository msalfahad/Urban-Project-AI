# Acceptance framework — proposal (UNAPPROVED)

- **Status.** This is a recommendation for the owner. The sealed protocol URBAN_BLIND_V2 and its SEAL are **not
  altered**. If the owner adopts any of this, it must be sealed as a new protocol version **before** a blind run;
  criteria set after results are seen are void.
- **Unsupported is never zero.** A category the engine does not support reports its reference total and is excluded
  from the score, never counted as 0 % or 100 %.
- **No accuracy claim** follows from this document.

## 1. Why the Phase 2B-8 criteria are not enough

The proposed criteria (coverage ≥ 0.90, within-tolerance ≥ 0.90, |total error| ≤ 3 %, no silent omission,
false positives ≤ 2 %) apply one rule to every metric. They do not separate:

- a missing room from a mis-measured one;
- a large error on skirting from the same error on porcelain;
- a held quantity, which is honest, from a wrong released one.

They also say nothing about provenance or assumption rates.

## 2. Proposed measures, per category

For each BOQ category (floor finishes, wall ceramic, plaster, paint, skirting, ceilings, waterproofing, doors,
windows, wall run, stairs):

| # | Measure | Definition | Proposed bar |
|---|---|---|---|
| A1 | **Completeness** | share of reference items with an engine line (released, provisional, flagged or not-applicable), not SILENT | ≥ 0.98; **0 silent items** in any category |
| A2 | **Room geometry** | per room: floor area and perimeter within tolerance (m² 0.10 / 2 %, lm 0.05 / 2 %) | ≥ 0.95 of rooms |
| A3 | **Per-item error** | released items within tolerance | ≥ 0.90 per category |
| A4 | **Category total error** | \|Σ engine released − Σ reference over the released items\| / Σ reference | ≤ 2 % finishes, ≤ 3 % waterproofing, exact counts for doors / windows |
| A5 | **False positives** | engine released quantity with no reference item / total | ≤ 1 % per category |
| A6 | **Missing items** | reference items SILENT or FLAGGED without a reason | 0 without a reason |
| A7 | **Duplicates** | an item counted in two lines (the conservation and once-only checks) | 0 |
| A8 | **Provenance** | released lines tracing to source entities and a rule id | 100 % |
| A9 | **Assumption rate** | released quantity that depends on an Urban default or an assumed value, share of the category | reported; ≤ 10 % for a pass; every assumption labelled |
| A10 | **RFI rate** | held / flagged items, share of the category | reported, not penalised when the reason is a missing drawing (the honest outcome); penalised when the reason is engine weakness |
| A11 | **Materiality** | errors weighted by a fixed, pre-sealed **quantity weight per category** (not price; prices are out of scope), so a 1 % error on porcelain counts more than 1 % on skirting | the weighted total error is reported next to A4 |

## 3. Category gate

A category **passes** only when:

- A1, A3, A4, A5, A6, A7 and A8 all hold; and
- A9 is within its bar.

Each category is reported on its own:

- one PASS / FAIL / UNSUPPORTED;
- the A-measures;
- the outcome counts.

There is **no single blended percentage**.

## 4. Claim rule

The "≥ 95 %" long-term target may be stated only when all of these hold:

- **two** independent blind villas;
- each with an independent QS reference;
- the same frozen method;
- every SUPPORTED category passing on both.

It is then stated **per category**, as the share of categories passing, with the category list.

## 5. What it would cost the current engine (Phase 2B-9, expected and honest)

- **Heights.** On a set without sections or schedules, wall areas are held. A10 would be high but not penalised; A3
  would not apply.
- **Windows.** Areas are held without a height. Counts and widths would be scored; areas would be UNSUPPORTED until
  schedules exist.
- **Waterproofing.** Corners and penetrations are held for lack of a detail. A10 is honest.

The open decisions for the owner are OD-P9-01 (adopt / amend this framework), OD-P8-01 (the earlier criteria) and
the category weights for A11.
