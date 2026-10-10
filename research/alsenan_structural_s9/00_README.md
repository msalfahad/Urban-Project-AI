# S9: whole-building structural BOQ reconciliation

Baseline HEAD `b85d2af`. Date 2026-10-10. State: `FROZEN_BEFORE_COMPARISON` (`16_S9_FREEZE_MANIFEST.json`).

S9 reconciles every structural family from the frozen S1 - S8 stages. All 29 freeze manifests and the S1 / S2 / S3 /
S3.1 indexes verify unchanged before and after the build. No frozen stage and no production quantity is changed:
every new quantity is an auditable S9 delta (`10`).

**This is a partial structural BOQ, not a complete building estimate.** The project gate stays INCOMPLETE.

## Released structural BOQ (A)

**Concrete: 158.070 m3.**

- 12.204 m3 is carried from the frozen stages.
- 145.866 m3 is released here, as 110 S9 deltas.

| Family | Released m3 | of which S9 delta | Owner |
|---|---|---|---|
| FOOTINGS | 64.304 | 64.304 | S9 (FF counted once) |
| COLUMNS | 20.584 | 20.584 | S9 (GF / 1F / 2F, S2 VERIFIED) |
| GROUND_BEAMS | 3.879 | 3.879 | S9 (explicit sections) |
| SLABS | 57.099 | 57.099 | S9 (S2 VERIFIED panels) |
| GROUND_SLAB | 3.786 | - | S8.1 |
| STAIRS | 0.517 | - | S8.7 |
| DOMES | 5.081 | - | S8.3 |
| WATER_TANK_ROOF | 2.454 | - | S8.4 |
| LINTELS | 0.366 | - | S8.6A |

**Reinforcement: 18,845.961 kg (18.846 t).**
Each family is taken at its authoritative version; `04` shows the precedence.

| Family | Released kg | t | Authoritative version |
|---|---|---|---|
| COLUMNS | 4,657.725 | 4.658 | S3.1 - S9-C01 |
| FOOTINGS | 3,629.600 | 3.630 | S4 + S4.1 + D1.2 |
| GROUND_BEAMS | 1,436.232 | 1.436 | S5 + S5.1 - AD1 - D1.1 |
| BEAMS | 4,014.765 | 4.015 | S6 + S6.1 - D1.1 |
| SLABS | 3,802.015 | 3.802 | S7 |
| GROUND_SLAB | 233.695 | 0.234 | S8.1 |
| DOMES | 602.111 | 0.602 | S8.3 |
| WATER_TANK_ROOF | 361.209 | 0.361 | S8.4 |
| LINTELS | 49.589 | 0.050 | S8.6A |
| STAIRS | 59.021 | 0.059 | S8.7 |

The full released BOQ, by family, storey and bar diameter, is `07_RELEASED_STRUCTURAL_BOQ.csv`.

## How S9 decides

**S9-RR1, the release rule for new concrete.** A component no frozen stage measured is released only if all of these
hold:

- S2's census already VERIFIED its count, length or area;
- every dimension is printed (schedule, section, thickness) or taken from the S1 / S5 / S6 project geometry;
- its height or interval is established;
- it has no open conflict;
- S9's independent recomputation agrees (footing outline = schedule; slab polygon re-integrated).

The rule releases these families:

- **Footings:** 25 occurrences, L x W x D. The F9 / FN outline overlap is deducted at its maximum shared prism. FF
  (11.385 m3) is counted once here, not in the lift family.
- **Columns:** GF / 1F / 2F occurrences whose S2 state is VERIFIED and whose drawn section equals the schedule. They
  are measured on the printed floor-to-floor; structural slab levels are not printed, so this is a project-basis value
  (the same interval S3.1's main bars use).
- **Ground and strap beams:** the spans whose width and depth are both explicit.
- **Slab plates:** the 47 S2-VERIFIED suspended slab panels (S1's GF / 1F / 2F roof slabs) that no S8 stage owns.
  Each is panel area x printed or default thickness.

**S9-MC1, the measurement convention.** No cubic metre is counted twice:

- columns own their footprint over the full storey, including the joints;
- beams run clear between column and beam faces, at full depth;
- slab panels lie between the beam and column faces (S1 geometry);
- ground beams run clear between column and footing faces.

**What stays conditional.** Superstructure beams: S2 holds their lengths only as a lower bound, and the drawings never
state whether schedule depth H includes the slab. `02` gives B x H x L and the alternative B x (H + 0.16) x L. The
rest is blocked: foundation-storey columns (no printed founding level), the pit walls and tie beam, the pool, parapets,
blinding, the boundary wall, the dome rings and the ground-slab remainder. None is ever counted as zero.

**S9-C01, a new correction.** S3.1 measured column ties on the sharp outer perimeter and added hook allowances.
D1.1 later proved that a sharp path is not a lower bound and that unknown hooks prove none. D1.1 limited itself to
S4.1 / S5.1 / S6.1; S9 applies the same rule to columns. 1,217.128 kg moves from released to
conditional. It is kept in `03`, and the change can be reversed once a bend radius and hook are stated.

**No unsupported lap or anchorage is added.** S9 adds no bar length of its own. The column laps, anchorages,
starters and twisted-column extras that stay released (174.523 kg) are S3.1's
printed-rule parts only: p.8 note 9, the p.13 typical footing detail and the p.15 twisted-column detail. Every other
lap, anchorage, hook and bend stays blocked or conditional (`03`, `05`).

**Stairs.** S8.7's three plates are carried unchanged, and S8.7A / S8.7B / S8.7C add nothing. The owner scenarios
stay scenarios:

- GF -> 1F with 27 risers is the preferred research alternative, not approved;
- 1F -> 2F with 27 is provisional;
- the round stair is the observed 28.

The owner's 110 - 120 mm unfinished riser is not used as a repeated concrete riser. The finished riser schedule
stays exact, and each concrete substrate level is that finished level minus its build-up: 30 mm stair marble or
20 mm landing marble, plus about 20 - 30 mm bedding. The waist is unknown. The landing, B20, B23, winder and CA
conflicts stay open, so no flight and no stair bar is added.

**Lift.** S8.8 is carried unchanged: the pit walls, the pit bars and the conditional tie beam stay blocked. FF is
counted once, in the footings. The four foundation-storey lift columns (C1 / C2 / C9 at the pit) are a
`SOURCE_CONFLICT`: they are drawn 200 / 250 mm, but the schedule gives 300 mm (S8.8 C-01, S9-RFI-04).

## Components

There are 560 components. By lane:

| Lane | Components |
|---|---|
| BLOCKED_UNQUANTIFIED | 125 |
| CONDITIONAL_NOT_RELEASED | 234 |
| EXCLUDED_OWNED_BY_OTHER_FAMILY | 26 |
| INDICATIVE_ONLY_NOT_RELEASED | 4 |
| NOT_APPLICABLE | 14 |
| NOT_IN_SOURCE | 6 |
| RELEASED_FROZEN_STAGE | 16 |
| RELEASED_S9_DELTA | 110 |
| SOURCE_CONFLICT | 25 |

## Files

| File | Content |
|---|---|
| `01_COMPONENT_INVENTORY.csv` | One row per structural component: owner, storey, source, lanes, linked reinforcement |
| `02_CONCRETE_BOQ_RECONCILIATION.csv` | Dimensions, gross, deductions, net, released, conditional / range, reason |
| `03_REINFORCEMENT_BOQ_RECONCILIATION.csv` | Per bar item: diameter, count, rate, shape, cut / total length, laps / anchorage / hooks, unit mass, original kg, corrections, authoritative kg / t, owner stage, lane |
| `04_OWNERSHIP_AND_PRECEDENCE_REGISTER.csv` | Every version of every family; authoritative and superseded |
| `05_MISSING_AND_BLOCKED_REGISTER.csv` | Missing and blocked quantities, by category |
| `06_FLOOR_SUMMARY.csv` | Storey x family |
| `07_RELEASED_STRUCTURAL_BOQ.csv` | Released BOQ (A) |
| `08_STRUCTURAL_COMPLETENESS_REPORT.md` | Completeness and exceptions (B) |
| `09_ENGINEER_RFI_REGISTER.csv` | Engineer RFI register |
| `10_S9_DELTA_REGISTER.csv` | S9 deltas and S9-C01 |
| `11_OVERLAP_AND_DOUBLE_COUNT_AUDIT.csv` | Overlap and double-count audit |
| `12_CONSERVATION_CHECKS.csv` | Conservation checks |
| `13_COVERAGE_BY_FAMILY.csv` | Coverage by family |
| `14_RELEASE_SUMMARY.json` / `15_PROVENANCE.jsonl` / `16_S9_FREEZE_MANIFEST.json` | Summary, provenance, freeze |
| `S9_STRUCTURAL_BOQ.xlsx` | Workbook view, written by `build_workbook.py` from these CSVs after the freeze. It is not frozen, and it is not committed (`*.xlsx` is git-ignored); rebuild it on demand |

## Reproduce

```
python3 -I research/alsenan_structural_s9/build_s9.py
```

The builder reads only frozen registers; no drawing is needed. Two builds are byte-identical.
