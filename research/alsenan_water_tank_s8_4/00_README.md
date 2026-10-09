# S8.4: water-tank roof region, concrete and reinforcement QTO

Baseline `cce41a2`. Frozen before any comparison: `15_S8_4_FREEZE_MANIFEST.json`, `references_read: []`.

## Population

- **Two physical slab panels**, SP-2F_ROOF_SLAB-01 and -02, on the second-floor (tower) roof, are the roof slab designated for the tank.
  - One 'WATER TANK PLACE' note, leader and cloud (SPC-WATER_TANK-SFRS) mark both; the parent carries no quantity.
  - Beam B3 (BL003) separates the panels; each has its own T 18 tag and its own two (T&B) callouts.
- **No tank base, no tank walls, no tank member** in either discipline: not drawn, noted or scheduled.

## Released (PROJECT_BASIS_QTO)

- Concrete: **2.4543 m3** (net face area x 0.180 m).

| item | panel | area m2 | t mm | m3 |
|---|---|---|---|---|
| S8.4-C-01 | SP-2F_ROOF_SLAB-01 | 8.235 | 180 | 1.4823 |
| S8.4-C-02 | SP-2F_ROOF_SLAB-02 | 5.4 | 180 | 0.972 |

- Reinforcement: **361.208565 kg**, eight families (two panels x two directions x top and bottom), rate density face to face, D^2/162, unrounded.

| family | callout | Ø | /m | dir | layer | length m | kg | blocked stop zone kg |
|---|---|---|---|---|---|---|---|---|
| S8.4-R-01-X-B | 7A7 | 14 | 7 | X | BOTTOM | 54.36375 | 65.773426 | 3.969907 |
| S8.4-R-01-X-T | 7A7 | 14 | 7 | X | TOP | 57.645 | 69.743333 | 0 |
| S8.4-R-01-Y-B | 7A8 | 14 | 6 | Y | BOTTOM | 46.378125 | 56.111806 | 3.668194 |
| S8.4-R-01-Y-T | 7A8 | 14 | 6 | Y | TOP | 49.41 | 59.78 | 0 |
| S8.4-R-02-X-B | 798 | 12 | 6 | X | BOTTOM | 28.35 | 25.2 | 3.6 |
| S8.4-R-02-X-T | 798 | 12 | 6 | X | TOP | 32.4 | 28.8 | 0 |
| S8.4-R-02-Y-B | 796 | 12 | 6 | Y | BOTTOM | 30.375 | 27 | 1.8 |
| S8.4-R-02-Y-T | 796 | 12 | 6 | Y | TOP | 32.4 | 28.8 | 0 |

By diameter: Ø12 109.8 kg, Ø14 251.408565 kg.

## How it is measured

- **T 18 is the slab thickness**, 180 mm: a circled 'T' over '18', the project's 't' thickness block (which reads 16 = the 160 mm default elsewhere). It is never read as a Ø18 bar.
- **(T&B) gives the faces, not the directions.** Each direction has its own callout, bound to its own drawn bar; each carries its own (T&B). Nothing is inferred for a second direction.
- Bars run face to face of the supporting beams and columns. The bottom layer's stop zones at continuous or continuity-unresolved supports (the typical 50 % at 0.125 L) are blocked, not released, because neither their applicability to a (T&B) slab nor the continuity is established. The released quantity is common to every reading.
- No temperature steel and no note-2 top steel are added on the tank side; both are recorded with their reasons and the note-2 kg as sensitivity.

## S7 interface

- S7 stays **3,802.015 kg**.
- The 20.087449 kg of S7 top steel at the tank edges (items S7-0217, S7-0228, S7-0284, S7-0307) lies in panels 03, 04 and 06 and stays S7; S8.4 releases nothing on a support or beyond a face.
- All 22 S7 items excluded to the region and all 33 PRE-S7.1 transfers land on exactly one S8.4 row (07).

## Not released (08)

- BLOCKED_UNQUANTIFIED: 31
- NOT_ADDED: 4
- NOT_IN_SOURCE: 4

## Sensitivity (not released)

- SA-01: bottom bars run face to face with no stop zone (the typical curtailment does not govern the (T&B) slab) -> 374.246667 kg (13.038102)
- SA-02: stop zones only at the resolved continuous support (BL003 between the two panels); unresolved ends run through -> 368.476759 kg (7.268194)
- SA-03: plan note 2 also applies on the tank side (5Ø10/m, 1/3 local span from each beam face), additive to the (T&B) top layer -> 416.39375 kg (55.185185)
- SA-04: whole bars: each family's equivalent count rounded up, at its mean run, full length (a fabrication view, not a BBS) -> 380.747879 kg (19.539314)

## Conflicts and questions

- **CF-S8.4-01** (RECORDED (S1 not edited; no quantity effect)): S1 binds 7A7 to bar graphic 799; 798 to bar graphic 797, which are other callouts' bars; S8.4 binds 7A7 to ['7A5', '7A6']; 798 to ['799', '79A']. S1's directions, diameters, rates and (T&B) bindings agree with S8.4.
- **CF-S8.4-02** (OPEN (no quantity depends on it)): the cloud is a scalloped marker over both panels and the beam between them; it does not follow the panel faces and is not dimensioned: no tank footprint, position or support points are given
- **CF-S8.4-03** (OPEN (no quantity depends on it)): architecture names no tank and has no roof plan of the +13.90 tower roof; section A-A shows one unlabelled element in view at parapet height (VR-S8.4-04), section B-B and the elevations none
- **CF-S8.4-04** (RESOLVED_BY_SOURCE (LOCAL_PANEL 180 for two panels; PROJECT_DEFAULT 160 elsewhere)): PRE-S7 C-05 carried: R4 TEMPERATURE register: whole 2F floor 180 mm; source: two T 18 marks inside the two water-tank panels, no floor note
- **CF-S8.4-05** (RESOLVED_FOR_OWNERSHIP (AD2-D08); engineer confirmation open (Q-S8.4-01)): PRE-S7 C-07 / Q-TANK (normal roof slab or water-tank structure): the source draws two slab panels on beams, thicker and doubly reinforced, under a 'WATER TANK PLACE' cloud, and no tank member; S8.4 owns and measures them as the roof slab designated for the tank
- **CF-S8.4-06** (OPEN (PROJECT_BASIS lane)): the legend asks for stated dimensions, not scale; the x spans and panel 02's y span follow from the printed axis chains less the scheduled 200 mm beams, but panel 01's 3.3 m y span depends on beam BL008, drawn 300 mm off the axis that carries BL011, which no dimension states
- **CF-S8.4-07** (OPEN (stop zones blocked)): S1 reads the panel edges on BL008, BL011 and BL002 as CONTINUOUS; AD2 (S7) leaves those supports CONTINUITY_UNRESOLVED because the tank panels were special; S7A G-01 finds 100 mm of panel 03 beyond panel 01's 0.30 m edge across column 421
- **Q-S8.4-01** (OPEN): Engineer: are the two T 18 panels the slab that carries the tank directly, or is there a tank base, plinth or RC tank (walls, cover slab)? If so, issue its drawings.
- **Q-S8.4-02** (OPEN): Engineer: does the typical slab-on-beams curtailment (50 % of bottom bars stop 0.125 L short of a continuous support) apply to the (T&B) mesh of the tank panels, or do all bars run through?
- **Q-S8.4-03** (OPEN): Engineer: does plan note 2 (5Ø10/m over beams, 1/3 span) also apply on the tank side, in addition to the (T&B) top layer?
- **Q-S8.4-04** (OPEN): Engineer: anchorage of the top and bottom bars into the edge beams, continuity or laps over BL003 (7Ø14 / 6Ø14 against 6Ø12), and the bar marks for a BBS.
- **Q-S8.4-05** (OPEN): Engineer: confirm no temperature steel in a (T&B) panel (the table has no 180 mm row) and give the cover / exposure for a tank-bearing roof slab (P8-N22 states >= 25 mm).
- **Q-S8.4-06** (OPEN): Engineer: continuity of the tank panels with panels 06, 03 and 04 over BL008, BL011 and BL002 (same 180 / 160 mm level?), and at column 421 (S7A G-01).
- **Q-S8.4-07** (OPEN): Engineer / architect: tank type, capacity, footprint, support points and any upstand, curb or dowels; architecture shows no tank and no tower-roof plan.
- **Q-S8.4-08** (OPEN): Engineer: dimension beam BL008's position (drawn 300 mm off the axis of BL011).

## Outputs

- `00_README.md`
- `01_SOURCE_REGISTER.csv`
- `02_POPULATION_AND_OWNERSHIP.csv`
- `03_THICKNESS_AND_CALLOUT_REGISTER.csv`
- `04_CONCRETE_QTO.csv`
- `05_REINFORCEMENT_QTO.csv`
- `06_REINFORCEMENT_BANDS.csv`
- `07_S7_OWNERSHIP_RECONCILIATION.csv`
- `08_BLOCKED_COMPONENTS.csv`
- `09_SOURCE_CONFLICTS_AND_QUESTIONS.csv`
- `10_INTERFACE_AUDIT.csv`
- `11_SENSITIVITY_CASES.csv`
- `12_CONSERVATION_CHECKS.csv`
- `13_PROVENANCE.jsonl`
- `14_S8_4_SUMMARY.json`
- `15_S8_4_FREEZE_MANIFEST.json`

Rebuild: `python3 -I research/alsenan_water_tank_s8_4/build_s8_4.py` (byte-identical). Renders and crops of the drawings stay outside git.
