# S5 post-freeze comparison

```
python3 -I research/alsenan_ground_system_rebar_s5/post_freeze_comparison.py <CHRISTIANNP_FORENSIC_RERUN dir>
```

- The script runs only after the S5 freeze (commit `627c823`, manifest state `FROZEN_BEFORE_REFERENCE_COMPARISON`). It refuses to run if any frozen hash has changed.
- No S5 output was changed after the comparison, and nothing was tuned.
- Only comparable scope is compared.
- Each difference has exactly one class.

## References

| Reference | What it holds for the ground system | Comparable? | Class |
|---|---|---|---|
| christiannp (REBAR_EVIDENCE.csv, sha `5a56ed58…`) | `GROUND_BEAM_REBAR` is EXCLUDED ("no GB schedule/section anywhere"); there is no strap row | No steel to compare | SCOPE_DIFFERENCE (59 spans and 3 straps) |
| Freelancer lineage | Steel is given only as lumps: ground beams + ground slab = 9.75 t; footings + straps + perimeter beam = 5.8 t. Concrete is two ground-beam length lumps: 100 + 111 = 211 m at 0.30 × 0.60 | Lengths only | SCOPE_DIFFERENCE. No kg difference or percentage is reported |
| U-C4N | One project total, net 22.619 t, KNOWN_INCOMPLETE | No | SCOPE_DIFFERENCE |
| Old Urban R4 `GROUND_BEAM_REBAR_V4` | 59 spans: 2,114.23 kg VERIFIED_PARTIAL (1,930.37 longitudinal + 183.86 stirrup) and 1,755.39 kg provisional | Yes, span by span. All 59 old spans map onto S5 spans by band handles and nearest length; there are 0 unmatched | See below |
| Old Urban R3 straps | SB1: 168.67 kg longitudinal + 26.90 kg links (PROVISIONAL). SB3: 58.34 kg longitudinal + 11.27 kg links. SB2: blocked | Yes | See below |
| Old Urban multi-engine row | Ground beams + ground slab released 1,973.6 kg | No | SCOPE_DIFFERENCE |

The freelancer's 211 m of ground-beam concrete agrees with S5's 210.1 m summed centreline length. S5's bars run only 170.5 m in total. That shortfall is support faces plus the withheld conflict runs (BAR_RUN_CONVENTION).

## Ground beams against old Urban R4

Longitudinal steel: S5 has 1,238.56 kg and old Urban R4 has 1,930.37 kg verified. The difference is −691.81 kg, and it decomposes exactly:

| Class | Rows | S5 kg | Old verified | Old provisional | Effect on S5 − old verified |
|---|---|---|---|---|---|
| SAME (same bars, same length) | 72 | 1,004.38 | 668.75 | 335.63 | +335.63 |
| DETAIL_APPLICABILITY_DIFFERENCE | 66 | 0 | 808.07 | 223.30 | −808.07 |
| BAR_RUN_CONVENTION | 36 | 215.69 | 453.55 | 81.38 | −237.86 |
| OCCURRENCE_DIFFERENCE | 3 | 18.49 | 0 | 4.27 | +18.49 |

How to read each row:

- **SAME, +335.63 kg.** Old Urban held this steel PROVISIONAL because the governing detail was ambiguous. S5 releases it as a LOWER_BOUND only because the bars are identical in every candidate detail.
- **DETAIL_APPLICABILITY_DIFFERENCE, −808.07 kg.** Two cases make up this row:
  - **45 rows (concentrated load).** S5 keeps the "without concentrated load" section blocked wherever a concentrated load is not excluded (Q1).
  - **21 rows (candidate details differ).** Old Urban picked a primary detail; S5 chooses none (Q8, Q3, Q4).
- **BAR_RUN_CONVENTION, −237.86 kg.** Also two cases:
  - **18 rows.** S5 withholds the bar run on the 7 length-geometry-conflict spans and the 1811-1812 span (Q3B, Q10).
  - **The rest.** Old Urban used a span length; S5 uses `BAR_STRAIGHT_RUN_LOWER_BOUND` to the support face. Two of these are spans whose free end lies inside a footing outline, classified in PRE-S5.1.
- **OCCURRENCE_DIFFERENCE, +18.49 kg.** On GSO-114-115-7DF-2, the PRE-S5 multi-partner pairing rebuilt the member: the old band {114, 7DF} became {114, 115, 7DF}, and the length went from 0.30 m to 1.30 m.

Components old Urban priced and S5 keeps blocked:

| Class | Old kg | What it is |
|---|---|---|
| STIRRUP_GEOMETRY_MISSING (40 spans) | 183.86 verified | Old Urban assumed a link path and legs; S5 gives a count only (Q6) |
| HOOK_MISSING (59 spans) | 734.47 provisional | Hook and perimeter allowance (Q6) |
| ASSUMED_COMPONENT (29 spans) | 376.34 provisional | Exterior side bars from an assumed FOLLOW ARCH. depth (Q2) |
| DEVELOPMENT_MISSING (118 ends) | 0 / 0 | Unquantified on both sides (Q7) |

## Straps

| Strap | S5 | Old Urban | Class |
|---|---|---|---|
| SB1 | 168.63 kg LB (4.550 m); links ≥ 37 | 168.67 kg (4.551 m) + 26.90 kg links (PROVISIONAL, F/F10 face); links 37 | BAR_RUN_CONVENTION (1 mm); STIRRUP_GEOMETRY_MISSING; HOOK_MISSING |
| SB2 | BLOCKED (two schedule rows) | BLOCKED | SAME. The freelancer used 100 × 50 × 2.3 m, which is SECTION_CONFLICT (S5 chooses no row) |
| SB3 | 50.80 kg LB (2.838 m); links ≥ 20 | 58.34 kg (3.259 m); links 23 | BAR_RUN_CONVENTION (PRE-S5 strap clear length rebuilt); STIRRUP_GEOMETRY_MISSING |

Freelancer strap lengths:

| Strap | Freelancer length | S5 bar run | Class |
|---|---|---|---|
| STB1 | 4.55 m | 4.55 m | SAME |
| STB3 | 3.25 m | 2.838 m | BAR_RUN_CONVENTION |

## Root causes

1. **Detail applicability (Q1, Q8, Q3, Q4).** This is the largest gap: 808 kg of old verified steel. S5 does not apply a "without concentrated load" section where loads are not excluded, and it never picks between differing candidates.
2. **Stirrup, hook and side-bar geometry (Q2, Q6).** This is 1,295 kg of old-Urban assumed steel. None of it is source-supported.
3. **Bar-run convention (Q3B, Q10).** S5 measures to the support face and withholds conflict runs.
4. **Development (Q7).** It is missing on both sides, so every reference total is incomplete.

None of these is a reason to change S5. Each one closes only through an engineering answer (Q1–Q10), followed by a new version.
