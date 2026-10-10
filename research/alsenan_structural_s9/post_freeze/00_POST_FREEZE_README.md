# S9 post-freeze comparison

Run after the S9 freeze (`16_S9_FREEZE_MANIFEST.json`, sha `0a7d69920aa1`). The S9 manifest and
the 29 stage manifests it froze over verify before and after. Comparison only, after the freeze: S9 is not tuned, nothing is released and no frozen quantity changes; a finding that needs a change goes to a separately approved correction layer.

**Release delta: 0 m3, 0 kg.**

## Old Urban V3b BOQ, concrete

S9 releases 158.070 m3. The V3b technical lines total
282.840 m3. The two use different conventions and populations, so neither total is a
check on the other; each group is classified below.

| Group | V3b m3 | S9 released m3 | S9 conditional point m3 | Class |
|---|---|---|---|---|
| FOOTINGS | 64.346 | 64.304 | 0.000 | METHOD |
| BLINDING | 28.828 | 0.000 | 0.000 | AUTHORITY |
| STRAP_BEAMS | 3.392 | 2.160 | 0.000 | AUTHORITY |
| GROUND_BEAMS | 11.245 | 1.719 | 0.000 | AUTHORITY |
| COLUMN_NECKS | - | 0.000 | 12.017 | NO_DIFFERENCE |
| GROUND_SLAB | 11.539 | 3.786 | 12.978 | AUTHORITY + SCOPE |
| COLUMNS_GF | 15.298 | 13.613 | 6.638 | METHOD + SCOPE |
| COLUMNS_1F | 7.676 | 4.284 | 5.964 | METHOD + SCOPE |
| COLUMNS_2F | 3.377 | 2.688 | 1.260 | METHOD + SCOPE |
| BEAMS_GF | 21.414 | 0.000 | 38.266 | AUTHORITY + METHOD |
| BEAMS_1F | 13.523 | 0.000 | 20.678 | AUTHORITY + METHOD |
| BEAMS_2F | 2.650 | 0.000 | 3.971 | AUTHORITY + METHOD |
| SLABS_GF | 44.286 | 32.958 | 0.000 | METHOD + SCOPE |
| SLABS_1F | 27.160 | 19.141 | 0.000 | METHOD + SCOPE |
| SLABS_2F | 9.986 | 5.000 | 0.000 | METHOD + SCOPE |
| LINTELS_GF | 2.726 | 0.102 | 2.485 | AUTHORITY |
| LINTELS_1F | 1.493 | 0.264 | 1.641 | AUTHORITY |
| LINTELS_2F | 0.530 | 0.000 | 0.485 | AUTHORITY |
| STAIRS | - | 0.517 | 0.000 | SCOPE |
| DOMES | 7.523 | 5.081 | 0.000 | METHOD + AUTHORITY |
| POOL | 5.848 | 0.000 | 0.000 | AUTHORITY |
| STRUCTURAL_WALLS | - | 0.000 | 0.000 | MISSED_OBJECT |
| BOUNDARY_WALL | - | 0.000 | 0.000 | NO_DIFFERENCE |

The footings differ by -0.042 m3, which is exactly the F9 / FN overlap prism S9 deducts.

**Slab area reconciliation.** V3b measures one net plate per floor. S9 measures released panels, plus the areas it
gives to other owners and to the beam and column footprints:

| Storey | V3b plate m2 | S9 panels m2 | Other owners m2 (stairs) | Beams m2 | Columns m2 | Residual m2 | Residual if V3b nets the stairs m2 |
|---|---|---|---|---|---|---|---|
| GF | 276.788 | 205.986 | 37.540 (37.540) | 56.240 | 4.500 | -27.478 | 10.062 |
| 1F | 169.751 | 119.630 | 40.693 (10.415) | 33.908 | 2.440 | -26.920 | -16.505 |
| 2F | 55.478 | 31.250 | 13.635 (0.000) | 7.468 | 0.940 | 2.185 | 2.185 |

V3b states one net plate per floor and no breakdown, so the residual cannot be decomposed further. It is context for
the METHOD + SCOPE class, not a quantity.

## Old Urban V3b BOQ, reinforcement

S9 releases 18,845.961 kg. The V3b technical populations total
20,651.367 kg (hooks outside).

| Group | V3b kg | S9 released kg | S9 not released (modelled) kg | Class |
|---|---|---|---|---|
| COLUMNS | 5,329.857 | 4,657.725 | 2,830.459 | METHOD |
| FOOTINGS | 1,132.674 | 3,629.600 | 0.000 | NOT_DECOMPOSABLE |
| GROUND_BEAMS | 1,687.528 | 1,436.232 | 0.000 | METHOD |
| BEAMS | 4,115.881 | 4,014.765 | 0.000 | METHOD |
| SLABS | 4,876.896 | 3,802.015 | 0.000 | SCOPE + METHOD |
| GROUND_SLAB | 286.087 | 233.695 | 0.000 | SCOPE |
| DOMES | 2,054.227 | 602.111 | 0.000 | SCOPE + AUTHORITY |
| LINTELS | 582.479 | 49.589 | 522.091 | AUTHORITY |
| POOL | 585.738 | 0.000 | 0.000 | AUTHORITY |
| STAIRS | 0.000 | 59.021 | 0.000 | SCOPE |
| BOUNDARY_WALL | 0.000 | 0.000 | 0.000 | NO_DIFFERENCE |
| WATER_TANK_ROOF | - | 361.209 | - | SCOPE |

## Findings

| Finding | Kind | Severity | Subject | Recommendation |
|---|---|---|---|---|
| F-01 | MISSED_OBJECT | MEDIUM | 8 cantilever / bearing-wall hatch bands (4.947 m2 in plan) | a dated S9 correction layer registers them as BLOCKED_UNQUANTIFIED with an owner and an RFI (legend: cantilever portion vs bearing wall, thickness); needs approval |
| F-02 | AUTHORITY | INFO | footings: S9 64.304 vs V3b 64.346 m3 | confirm the F9 / FN outlines on site or with the engineer (S9-RFI-07) |
| F-03 | NOT_DECOMPOSABLE | HIGH | footing steel: S9 (S4) 3,629.6 kg vs V3b 1,132.674 kg | treat the V3b footing steel as unreliable; do not reuse it |
| F-04 | METHOD | INFO | slabs / beams / columns: V3b and S9 split the same concrete differently | compare totals only on one convention; never mix lines |

F-01 is a genuine S9 omission: the PRE-S8 census lists cantilever / bearing-wall hatch bands that no stage owns, and
S9 (which may not read the PRE-S8 data registers before its freeze) has no row for them. No released figure changes,
because no thickness is printed. They need a separately approved correction layer.

## Files

| File | Content |
|---|---|
| `01_OLD_BOQ_CONCRETE_COMPARISON.csv` | V3b concrete groups vs S9, plus the slab area reconciliation |
| `02_OLD_BOQ_REBAR_COMPARISON.csv` | V3b reinforcement populations vs S9 |
| `03_PRE_S8_CENSUS_CROSSWALK.csv` | Every PRE-S8 census family against the S9 components |
| `04_ABSENT_FROM_OLD_BOQ.csv` | S9 items with no V3b line, V3b lines with no S9 row, R5 context |
| `05_POST_FREEZE_FINDINGS.csv` | Findings and recommendations |
| `06_POST_FREEZE_SUMMARY.json` | Summary |
