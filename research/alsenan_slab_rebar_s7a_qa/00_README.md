# S7A: dated engineering QA of the S7 slab release (2026-10-08)

S7 stays frozen and byte-identical. Its **RESTRICTED_S7_PROJECT_BASIS_KG = 3,802.015 kg** is unchanged.

This layer re-reads the sources for the top-over-support rule. It quantifies the alternative readings as SENSITIVITY_ONLY, tabulates the bottom rules by support type, and grades every strip end's continuity. It also withdraws one S7 wording (errata S7A-E01). Nothing is released.

## Source finding (01, 02, 03)

- **Plan note 2** (ST7757.dxf handles D8/D9/DA, E1/E2/E3, EA/EB/EC):
  - text: «يجب وضع حديد علوي 5Ø10/m للبلاطات فوق الجسور بطول ثلث البحر في الاتجاهين»;
  - meaning: top steel 5Ø10/m for the slabs over the beams, *with a length of* one third of the span, *in the two directions*.
  - It states the ratio (1/3) but no span basis, no origin, no total-versus-per-side and no rule for unequal spans.
  - The only other «البحر» in the drawing is a SEA VIEW site marker (the same word means "the sea").
- **p.15 TYP. SLAB ON BEAMS** (vector strokes, not to scale):
  - At the continuous support, one top bar crosses the beam and runs into both spans, measured from each face.
  - At the non-continuous support, the anchor bar runs into L1 and turns down.
  - The extents are per side, from the face: 0.30 max(L1, L2) and 0.25 L1.
  - Size and spacing are deferred to the "SCHEDULE OR PLAN".
- **Continuous-beam schedule:** fraction-of-Ln dimensions sit on each side of a support, each against its own span. This is the per-side convention, but for beams: analogous evidence only.
- **p.15 temperature note 2** gives top-over-beam steel as one total length (X 2000; 1000 at a spandrel). This is analogous evidence for a total-length reading.
- **Result:** the one-third extent is NOT ESTABLISHED by the source.
  - Reading A (S7) is an owner measurement convention (AD2-D06). Its supporting and contrary evidence are kept beside the other readings.
  - The note-2 / p.15 identity is SAME_FAMILY_SUPPORTED_NOT_PROVEN.
  - A separate p.15 family would have no size or spacing source, so it could not be quantified.

## Top-steel sensitivity on the S7-released strip ends (04, 05, 06)

| scenario | top extension kg | top incl. crossings kg | vs S7 | S7-scope total under it kg |
|---|---|---|---|---|
| A | 1,358.0 | 1,463.7 | +0.0 % | 3,802.0 |
| B | 679.0 | 784.7 | -50.0 % | 3,123.0 |
| C | 1,088.5 | 1,194.2 | -19.8 % | 3,532.5 |
| D1 | 1,313.1 | 1,418.8 | -3.3 % | 3,757.2 |
| D2 | 1,388.5 | 1,494.3 | +2.3 % | 3,832.6 |
| E | 1,609.1 | 1,714.8 | +18.5 % | 4,053.1 |

How the scenarios are computed:

- Each one changes only the top-extension length per strip end. Bottom steel, the crossings over beams and every blocked item are as frozen.
- The opposite-side clear span (for C, D and E) comes from the frozen PRE-S7.1 strips of the panel beyond, matched along the bar line.
- Where no strip faces the end, the own span is used. That width is reported per row.
- Reading A reproduces S7's kg row by row.

The definitions are in 04_TOP_SENSITIVITY_SCENARIOS.csv. No scenario is selected, and none is a release.

## Bottom rules by support type (07) and end-condition audit (08)

- The p.15 50/50 split with the 0.125 L stop is drawn only for a slab on beams at one level.
- At unresolved, oblique and unrecorded ends, S7 applied the stop as if the end were continuous, and blocked the stop zone.
- Strip-end grades:
  - ESTABLISHED_BY_GEOMETRY: 1242 strip ends; S7 top extension 869.3 kg; bottom stop deduction 146.9 kg.
  - INFERRED_FROM_S1_EDGE_ONLY: 378 strip ends; S7 top extension 187.1 kg; bottom stop deduction 2.6 kg.
  - INFERRED_GEOMETRY_OVERRIDES_S1: 56 strip ends; S7 top extension 23.6 kg; bottom stop deduction 4.1 kg.
  - NOT_ESTABLISHED: 614 strip ends; S7 top extension 278.0 kg; bottom stop deduction 67.4 kg.
- Same-level continuity across a beam is inferred from the panel classes (sunken hatch). No per-panel level text was found.

## Errata S7A-E01 (09)

S7's 476 release items say QUANTITY_AUTHORITY "a lower bound of the physical steel (every blocked portion is excluded, not zero)". The post-freeze write-up also calls the total a "restricted lower bound". Both are withdrawn.

- Why: the top extent is not established, several readings give less steel than S7, and many continuities are inferred.
- Replacement: S7 is a PROJECT_BASIS_QTO under the recorded interpretation. It is not a proven bound of the physical steel in either direction.
- The kg change is 0, and no S7 file is edited.

## Reproduce

```
python3 -I research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py
```

The build is byte-identical on rebuild. It reads no external reference or earlier estimate.
