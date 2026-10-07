# S4: accurate footing rebar (Alsenan validation run)

**Baseline:** `e3633af`.

**Engine:**
- `engine/source/footing_rebar.py` (generic, accurate-side);
- guard: `engine/source/footing_rebar_guard.py`;
- contract: `accurate_boq_rebar.validate_s4_part`.

**Adapter:** `build_footing_rebar_s4.py`. It reads only the frozen S1 footing registers, the frozen pre-S4 package and the R4 rule register. It does not read the drawing, and it reads no reference, donor or old total.

## Headline

**KNOWN SOURCE-DERIVED FOOTING REBAR: FINAL FOOTING REBAR NOT ESTABLISHED**

| Bucket | kg |
|---|---|
| VERIFIED | 887.09 |
| LOWER_BOUND_KNOWN | 2742.51 (BEST with the +1 edge bar: 2836.40) |
| PROVISIONAL | 0 |
| BLOCKED_MODELLED | 0 |
| BLOCKED_UNQUANTIFIED | 24 components (no kg) |

There is no "total footing rebar". The known kg are a lower bound of the footing steel, because BOXED (21 occurrences), the F / F10 occurrence and FF's 2Ø16 label are unquantified.

## Section 0: F3 authority (`F3_AUTHORITY_DECISION.json`)

- **What OQ-11 is:** it comes only from the V3C donor audit's comparison with an external reference count ("the [reference] has one").
- **What it is not:** not an owner or consultant instruction, not a project claim, and not a conflict inside the project documents.
- **Decision:** **F3 = 2 occurrences, SOURCE_VERIFIED**. The drawing shows outlines 166B / 166C with tags 168F / 168E, both at the scheduled 160 × 140.
- The reference disagreement is an engineering / comparison flag. This supersedes the pre-S4 `COUNT_QUERIES`; the pre-S4 package itself is unchanged.

## Occurrences and components

**26 physical occurrences** (one row each in the occurrence register, never type × steel):

| Group | Occurrences |
|---|---|
| Single-layer (FT) | 20: F × 4, F2 × 2, F3 × 2, F4 × 2, F5 × 2, F6, F9, F11, F15, FN × 4 |
| Two-layer (FTB) | 5: F8, F12, F13, F14, FF |
| Source conflict | F / F10 × 1 |

| Component | VERIFIED | LOWER_BOUND | BLOCKED_UNQUANTIFIED | NOT_APPLICABLE |
|---|---|---|---|---|
| BOTTOM_SHORT | 20 | 5 | 1 (F / F10) | — |
| BOTTOM_LONG | 20 | 5 | 1 (F / F10) | — |
| TOP_SHORT / TOP_LONG | — | 5 / 5 | — | 21 / 21 |
| BOXED | — | — | 21 (20 FT + F / F10) | 5 (FTB rows) |
| STARTER_DOWEL_REFERENCE | — | — | — | 26 (column engine) |
| OTHER_EXPLICIT_EXTRA | — | — | 1 (FF 2Ø16, S4-Q1) | — |

**Release states:** 25 occurrences are REBAR_LOWER_BOUND and 1 is REBAR_BLOCKED (F / F10).

**Not computed:** F7 has a schedule row but no plan occurrence, and F10 is only a conflict candidate. No steel is created from a schedule row.

## Rules applied

| Rule | Source / authority |
|---|---|
| Net straight length = span − 70 − 70 mm | `COVER_AGAINST_SOIL_70MM` (P8-N22, cross-verified; applies to FOOTING / FOOTING_2_LAYER / FOOTING_LIFT) |
| SHORT bars span W and are counted along L; LONG the reverse | pre-S4 diagnostic (equal spacing both ways only in this reading), SOURCE_DERIVED_HIGH_CONFIDENCE |
| Bottom bars straight (no hook) | p.13 typical detail, SOURCE_DERIVED_HIGH_CONFIDENCE |
| Two-layer top-bar ends | not drawn → straight core only, LOWER_BOUND, END_TREATMENT named as missing |
| Explicit count (FT) | printed count → VERIFIED |
| Bars per metre (FTB) | n = ceil(rate × (dim − 2 × 70)) → LOWER_BOUND; the +1 edge bar is BEST only |
| Unit mass | D² / 162 (rebar_unit_mass) |
| Net only | no waste and no procurement (BBS used / purchased / waste columns empty) |

## Quantities

| Ø | kg | m |
|---|---|---|
| 12 | 596.14 | 670.66 |
| 14 | 2410.05 | 1991.98 |
| 16 | 623.41 | 394.50 |
| **all** | **3629.60** | **3057.14** |

- **Conservation:** all 8 checks pass (component = occurrence = project; BBS = parts; each required component once per occurrence; population reconciles; blocked carries no kg; accurate summary reconciles).
- **Provenance:** 84 / 84 quantity / blocked parts pass `validate_s4_part`.
- **Engine stamp:** `e3633af+code:<sha16 of the engine code>`.

## Freeze

`S4_FREEZE_MANIFEST.json` hashes the code, inputs and outputs. It was committed before any reference was read. The post-freeze comparison is in `post_freeze/` (see `post_freeze/S4_POST_FREEZE_COMPARISON.md`) and refuses to run if any hash has changed.

**Post-freeze result:**
- christiannp 3863.41 kg = S4 3629.60 + cover convention 176.39 + count convention 57.42 (residual −0.006 kg).
- Old Urban R3 verified = S4 known exactly; its 93.89 kg provisional = S4 BEST − LOW.
- The freelancer and U-C4N figures are scope-different or incomplete references.

S4 was not tuned.
