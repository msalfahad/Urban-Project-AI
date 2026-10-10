# 01 Bottleneck diagnosis

Why the strict release stops at 158.070 m3 and 18,845.961 kg, and what the rest is waiting for. Every figure is a sum over the M1 item registers (`boq/`).

| Category | Items | Concrete m3 (base) | Reinforcement kg (base) |
|---|---:|---:|---:|
| A. Fully measured (VERIFIED) | 1112 | 158.070 | 18,846.0 |
| B. Calculated; blocked only by a convention or an approval | 280 | 100.434 | 6,020.6 |
| C. Incomplete geometry (one assumed dimension) | 104 | 72.069 | 0.0 |
| D. No defensible geometry (UNRESOLVED) | 86 | none (exposure up to 34.4 m3, not added) | none |

Planning estimate: concrete 330.573 m3 (range 313.792 to 365.104); reinforcement 24,866.6 kg (range 24,533.4 to 24,968.7).

## The five biggest causes of missing concrete

| Blocker | Provisional m3 (base) | Upper m3 | Provisional items | Unresolved items | Families |
|---|---:|---:|---:|---:|---|
| BEAM_DEPTH_CONVENTION | 57.694 | 72.070 | 109 | 0 | BEAMS |
| SECTION_CONFLICT | 20.635 | 24.251 | 32 | 0 | BEAMS, COLUMNS, FOOTINGS, GROUND_BEAMS |
| GB_EXTERIOR_DEPTH | 20.832 | 23.147 | 23 | 0 | GROUND_BEAMS |
| NOT_PRINTED | 9.975 | 23.044 | 1 | 1 | PLAIN_CONCRETE |
| FOUNDING_LEVEL | 14.881 | 18.552 | 40 | 1 | COLUMNS, GROUND_BEAMS, LIFT |

## The five biggest causes of missing reinforcement

| Blocker | Provisional kg (base) | Upper kg | Provisional items | Unresolved items | Families |
|---|---:|---:|---:|---:|---|
| TIE_LINK_HOOK_RULE | 2,772.2 | 2,873.0 | 8 | 0 | BEAMS, COLUMNS, GROUND_BEAMS |
| LAP_ANCHORAGE_RULE | 1,288.5 | 1,288.5 | 5 | 0 | COLUMNS |
| NOTE_SCOPE | 801.1 | 801.1 | 38 | 0 | GROUND_SLAB |
| BEARING_NOT_CONFIRMED | 522.1 | 522.1 | 65 | 0 | LINTELS |
| DOME_RING_DEPTH | 311.9 | 311.9 | 6 | 0 | DOMES |

Unresolved reinforcement has no exposure figure: no bar model exists for it, and M1 uses no kg/m3 ratio.

## Held only by a manual approval

These quantities are fully modelled. What holds them is an approval or an authority rule, not geometry.

| Blocker | Items | m3 | kg | Why it is only an approval |
|---|---:|---:|---:|---|
| RELEASE_RULE_APPROVAL | 6 | 2.250 | 66.4 | columns whose drawn section equals the schedule, held only by S2's PROVISIONAL minimum-thickness state (5 GF columns among them) |
| NOTE_SCOPE | 38 | 12.978 | 801.1 | 19 slab-on-grade faces: the printed note 'T=10cm, 5D10/m E.W.' applies; only its scope needs a yes |
| BEARING_NOT_CONFIRMED | 65 | 4.611 | 522.1 | lintels S8.6A modelled; release waits for a bearing confirmation |
| TIE_LINK_HOOK_RULE | 8 | 0.000 | 2,772.2 | beam / ground-beam links and column ties fully modelled; D1.1 retracted them because hooks and bend radius are not printed (an authority rule, not missing geometry) |
| LAP_ANCHORAGE_RULE | 5 | 0.000 | 1,288.5 | column laps, anchorages and starters modelled with the printed rule; release waits for approval of that rule |

## Never detected by S1 - S9

| What | Found by | In M1 |
|---|---|---|
| 8 hatched cantilever portions (bands) | S9A (after S1 - S9) | 7 PROVISIONAL at the 16 cm project default; the 8th is CA's own hatch, counted in the CA beam |
| 10 beam-to-beam corner squares | S9A BO-04 | one PROVISIONAL item |
| link and tie hooks of beams and ground beams | excluded by every link model (S5.1, S6.1) | PROVISIONAL hook allowance (LINK_HOOK_ALLOWANCE_MM) |
| the deeper-section reading of overlapping p.13 ground-beam titles | S9A | the high end of the ground-beam ranges |
| drawn layers with geometry that no stage's code names: 1 (S-SHEET.LO) | M1 drawing inventory (03) | listed as detection gaps; not measured |

## What runs automatically on a new villa

See `04_AUTOMATION_AUDIT.csv`. In short, the inventory, the provisional estimating layer, the checks, the exception report, the Excel workbook and the PDF run on any DXF. Footings and columns are measured live once a person confirms a profile (layers, tags, sheets, schedule rows, storey heights). Beams, slabs, ground beams, stairs and every bar schedule still need the S1-type census and the per-family stages. Those stages are written for this drawing: hard-coded inserts, layers, tag patterns and a hand-transcribed rule set. On a new villa those families come out UNRESOLVED, with the tag evidence the inventory found.

