# 07 ST7757 before and after (V5 → V6)

**Phase: post-discovery, not blind.** The developer has seen ST7757 and its M5 bridge in earlier milestones, so this
run is not evidence for any M8 rule. It shows what V6 does on a real drawing set. The rules themselves were
validated on the held-out villas (`04_HELDOUT_VALIDATION.md`).

- Command: `python3 -I research/urban_engine_m8_full_scope/st7757_run.py` (route G, the same two structural
  drawings as M5–M7; sha256 in `st7757/SUMMARY.json`).
- Records: `st7757/BY_FAMILY.csv`, `st7757/SCOPE_ITEMS.csv`, `st7757/SCOPE_BOUNDS.csv`, `st7757/SUMMARY.json`.

## Headline

| Figure | V5 (M7) | V6 (M8) |
|---|---|---|
| RC measured base, m³ | 291.758 | 319.800 |
| RC bounded total, m³ (BOQ section F) | – (no section F) | 313.235 – 476.110 |
| Plain concrete measured, m³ | 22.155 | 22.155 (bounded 22.155 – 67.371) |
| Completeness findings | 90 | 86 |
| Scope rows (findings + unresolved items with no exposure) | – | 89 (86 + 3) |
| Findings with no volume range | 85 | **0** |

**Why the finding count falls from 90 to 86.** The route now measures stair zones, so three STAIR_NOT_MEASURED
findings and two UNRESOLVED_ITEMS findings (stair zones held as slab exposures) close. Among the DRAWN_NOT_MEASURED
findings, one leaves and two new ones appear.

**What the +28.04 m³ is.** It all comes from families that V5 left unmeasured:

| Family | Storey | V6 measured, m³ | Range of the items, m³ | How |
|---|---|---|---|---|
| Stairs | 1F | 4.451 | 3.842 – 5.075 | route stair zone, winder approximation (plan × (waist / cos θ + R / 2)) |
| Stairs | GF | 2.786 | 2.091 – 3.188 | scope pass: 3 drawn runs, 26 tread lines |
| Stairs | GROUND | 2.718 | – | route zone 1.770 + a loose flight 0.948 |
| Domes | 2F | 7.372 | 3.839 – 9.215 | two radial rib groups (19 and 20 ribs, r 2.211 m) on the top plan; spherical cap × shell |
| Pool | GROUND | 3.495 | 2.697 – 4.294 | the drawn 0.2 m wall strip (6.2 m) and its fill: walls × height + floor × thickness |
| Boundary wall | FOUNDATION | 7.220 | 7.220 | strip length × the B.W schedule row (0.2 × 0.6 m) chosen by the drawn width |
| **Total** | | **28.042** | | |

**What did not change.** Footings, columns, necks, ground beams, the ground slab, suspended beams, slabs, lintels
and blinding: the measured volume of every core family is identical under V5 and V6 (`DELTA_MEASURED` = 0 on every
core row). Reinforcement: no row moved; the new families carry no reinforcement (MISSING_DATA, W8-09).

**Two unresolved exposures fell**, because the stair zones they held are now measured as stairs:
- the ground slab's unresolved high: 4.767 → 3.930 m³;
- the 1F slabs' unresolved high: 2.740 → 0.

## Family coverage

| Family | V5 | V6 |
|---|---|---|
| Stairs | DETECTED_NOT_QUANTIFIED | PARTLY_QUANTIFIED |
| Domes | DETECTED_NOT_QUANTIFIED | QUANTIFIED |
| Pool | DETECTED_NOT_QUANTIFIED | QUANTIFIED (the drawn strip only, W8-01) |
| Walls (boundary wall) | NO_EVIDENCE_FOUND | QUANTIFIED |
| Water tank | DETECTED_NOT_QUANTIFIED | BOUNDED_NOT_MEASURED (0 – 10 m³) |
| Parapets | DETECTED_NOT_QUANTIFIED | BOUNDED_NOT_MEASURED (0 – 44.4 m³) |
| Lift | NO_EVIDENCE_FOUND | NO_EVIDENCE_FOUND (the foundation pit is bounded as LIFT / WALLS / WATER_TANK, 0 – 6.745 m³) |
| Column necks, lintels | PARTLY_QUANTIFIED | PARTLY_QUANTIFIED |
| Plain concrete | QUANTIFIED | QUANTIFIED |

**Why stairs stay PARTLY_QUANTIFIED.** Every measured stair takes its waist from the convention, and one run on the
ground plan is measured with the riser convention against a storey rise smaller than the drawn run (W8-12).

## The scope pass: 89 rows, every one with a state

The 89 rows are the 86 findings plus three route items held UNRESOLVED with no exposure. Those three are bounded at
0 .. the largest measured member of their family: two columns whose type is not in the schedule, and one neck.

| State | Rows | Adds to the bounded total |
|---|---|---|
| MEASURED | 6 | through its items (stairs, domes, pool, boundary wall) |
| BOUNDED | 60 | its low / high |
| HELD_BY_ITEMS | 13 | nothing: an existing item already carries it |
| EXPLAINED | 2 | nothing: a drawn group on the noted plan may be that element |
| QUALIFIER | 8 | nothing: a note, not a volume |

**The RC bounded total, in parts:**

| Part | Low, m³ | High, m³ |
|---|---|---|
| Measured items (PROVISIONAL low / high, VERIFIED base) | 307.168 | 343.780 |
| Unresolved items' exposure | 13.918 | 27.287 |
| Bounded rows (59 RC) | −7.851 | 105.043 |
| **Bounded total** | **313.235** | **476.110** |

The negative low belongs to hatch-on-member findings: a hatch over a measured member may mean its volume is
already counted.

**The largest RC bounds** (`st7757/SCOPE_BOUNDS.csv`, sorted by HIGH_M3) are the RFIs a QS would raise first:

| Finding | Family | Range, m³ | Basis |
|---|---|---|---|
| Parapets referenced, not drawn | PARAPETS | 0 – 44.400 | free roof edge 148.0 m × 1.2 m × 0.25 m (high); 0 if a block parapet |
| Roof tank referenced, not drawn | WATER_TANK | 0 – 10.000 | an RC tank 2.5 m square, 2 m high (high); 0 if a GRP tank |
| A footing drawn, not itemised | FOOTINGS | 0 – 7.903 | plan area × the deepest footing section (0.7 m) |
| A pit outline on the foundation plan | UNKNOWN (LIFT / WALLS / WATER_TANK) | 0 – 6.745 | a pit of the drawn size at the highest wall height, base and cover |
| 2F column band with no outline | COLUMNS | 0 – 5.880 | occurrences × the largest measured column of the storey |
| A footing type scheduled, not placed | FOOTINGS | 0 – 3.750 | one instance |

The plain-concrete bound (0 – 45.216 m³) is a fill drawn round the whole foundation plan, read as blinding at
0.1 m at most.

## What a reviewer should check first

1. **Pool (W8-01).** Only the wall strip on the ground-beam plan is read, at 3.495 m³. The pool detail sheet
   (its depth and the other walls) is not read, so this is very likely an under-measure.
2. **Domes (W8-06).** Two radial groups on the 2F plan are read as domes because the set names domes. This rests on
   `DOME_ON_TOP_PLAN`; a person should confirm the 2F radial groups are the domes.
3. **Parapets and tank.** Together they are 54.4 m³ of the bounded high. One RFI each (RC or block; RC or GRP)
   closes most of the width.
4. **Boundary wall.** The B.W row is chosen by the drawn width. The ablation shows it is the largest single
   convention effect on the bounded high (`09_ABLATION.md`).
