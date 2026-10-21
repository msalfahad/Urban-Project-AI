# S9 structural completeness and exceptions report

Baseline `b85d2af`. Date 2026-10-10. **This is a partial structural BOQ. It is not a complete building
estimate.** The project regression gate stays INCOMPLETE.

## Quantity coverage by family

| Family | Components | Released | Conditional (valued) | No value | Released m3 | Conditional m3 (point) | Released kg | Not released (modelled) kg |
|---|---|---|---|---|---|---|---|---|
| FOOTINGS | 26 | 25 | 1 | 0 | 64.304 | 0.216 | 3,629.6 | - |
| COLUMNS | 95 | 32 | 31 | 32 | 20.584 | 15.324 | 4,657.7 | 2,830.5 |
| GROUND_BEAMS | 63 | 6 | 18 | 39 | 3.879 | 3.329 | 1,436.2 | 114.6 |
| BEAMS | 150 | 0 | 111 | 39 | - | 62.915 | 4,014.8 | 1,332.3 |
| SLABS | 53 | 47 | 0 | 6 | 57.099 | - | 3,802.0 | - |
| GROUND_SLAB | 21 | 2 | 19 | 0 | 3.786 | 12.978 | 233.7 | - |
| STAIRS | 15 | 3 | 0 | 12 | 0.517 | - | 59.0 | - |
| LIFT | 6 | 0 | 0 | 6 | - | - | - | - |
| POOL | 7 | 0 | 0 | 7 | - | - | - | - |
| DOMES | 7 | 2 | 0 | 5 | 5.081 | - | 602.1 | - |
| WATER_TANK_ROOF | 4 | 2 | 0 | 2 | 2.454 | - | 361.2 | - |
| LINTELS | 64 | 7 | 50 | 7 | 0.366 | 4.232 | 49.6 | 568.9 |
| PLAIN_CONCRETE | 2 | 0 | 0 | 2 | - | - | - | - |
| PARAPETS | 3 | 0 | 0 | 3 | - | - | - | - |
| BOUNDARY_WALL | 1 | 0 | 0 | 1 | - | - | - | - |
| OTHER | 3 | 0 | 0 | 3 | - | - | - | - |

"Conditional (valued)" components carry a value only under a stated condition (`02`, `CONDITIONAL_M3` / range).
"No value" components are blocked or in conflict with nothing to measure: their quantity is unknown, never zero.

## Coverage by storey

| Storey | Released m3 | Conditional m3 (point) | Released kg | Components with no value | Contents |
|---|---|---|---|---|---|
| FOUNDATION | 64.304 | 1.678 | 4,667.9 | 4 | footings and the foundation-storey column necks |
| GROUND | 7.665 | 16.307 | 1,669.9 | 48 | ground / strap beams, the slab on grade, the pool, the lift pit, entrance steps |
| GF | 47.170 | 47.049 | 6,448.3 | 32 | GF columns, GF-roof beams and slab (the +5.50 floor), GF lintels, the GF -> 1F stairs |
| 1F | 28.789 | 28.244 | 4,689.6 | 23 | 1F columns, 1F-roof beams and slab (+9.70), the domes, 1F lintels, the 1F -> 2F stair |
| 2F | 10.142 | 5.716 | 1,370.2 | 6 | 2F columns, 2F-roof beams and slab (+13.90), the water-tank roof, 2F lintels |
| ROOF | - | - | - | 3 | parapets above the roof slabs |
| SITE | - | - | - | 1 | boundary wall |

## Exceptions

- **Missing-quantity register** (`05`, 414 rows):
  - rebar measured, concrete missing: 181;
  - concrete measured, rebar missing: 0;
  - owned with no quantity: 113;
  - conditional only: 291;
  - possible multi-stage count: 9, each resolved to one owner (`11`).

  Whether a component is absent from the old BOQ is checked only after the freeze (`post_freeze/`).
- **Superseded figures** (`04`): S3 (by S3.1), S8.6's lintels (by S8.6A), and the S5.1 / S6.1 link paths and six S5
  bars (by AD1 / D1.1). Each is shown once and never added.
- **Source conflicts:** F / F10 footing, column type and section conflicts, the lift columns at the pit (drawn 200 /
  250 vs schedule 300), CB widths, ground-beam length classes, SB2, the dome rings and the boundary wall.
- **Owner scenarios:** stairs only. GF -> 1F 27 risers is the preferred research alternative and not approved;
  1F -> 2F 27 is provisional; the round stair is the observed 28. S8.7C's findings and RFIs are preserved. No flight
  is released.

  The owner's 110 - 120 mm unfinished riser is not used as a repeated concrete riser. The finished riser schedule
  stays exact, and each concrete substrate level is that finished level minus the finish build-up (S8.7A / S8.7B):
  30 mm stair marble or 20 mm landing marble, plus about 20 - 30 mm bedding. No build-up or waist is approved, so
  the flights stay unreleased.
- **Engineer RFIs** (`09`, 207 rows): 198 carried from the stages, plus 9
  consolidated by S9.

## Unresolved high-risk items

| Priority | To | Family | Question |
|---|---|---|---|
| P1 | engineer | FOUNDATION | Founding level of every footing (only 'excavation >= 1.50 m below plot level' is printed): it fixes the foundation-storey columns, the lift pit walls, any lower ground beam (P13) and the pool levels. |
| P1 | engineer | BEAMS | Beam schedule depth H: is it the overall depth including the slab (as S6 / D1.1 read it for links) or the depth below the slab? It decides about B x 0.16 m3 per metre of every beam. |
| P1 | engineer | GROUND_BEAMS | Ground-beam sections: which p.13 length class applies (centre-to-centre or clear length), the exterior 'FOLLOW ARCH' depths and the concentrated-load cases (S5). |
| P1 | engineer | COLUMNS | Column drawn section vs schedule (28 occurrences) and the lift columns drawn 200 / 250 vs 300 at the pit. |
| P2 | architect | ALL | Floor and roof build-ups (structural slab levels are not printed: column storeys use the printed floor-to-floor). |
| P2 | engineer | COLUMNS | Column ties: bend radius, hook and closure (S9-C01 holds 1,217.128 kg of S3.1 tie paths and hooks out of the released total until stated). |
| P2 | engineer | FOOTINGS | Footing FTG-CONFLICT_F_F10 (F or F10?) and whether the F9 / FN outlines really overlap; blinding thickness and projection. |
| P2 | architect | PARAPETS | Parapet and boundary-wall geometry (lengths, heights, sections). |
| P3 | engineer | SLABS | Sunken-slab drop depths and step details (6 panels). |
