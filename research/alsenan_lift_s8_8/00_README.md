# S8.8 lift pit, shaft walls, foundation and intermediate tie beam

Round S8_8, baseline `dc2d778`, engine `dc2d778+code:9be41378368006b5`. Frozen before any comparison
(`18_S8_8_FREEZE_MANIFEST.json`, `references_read: []`).

## Physical population

There is **one lift shaft**, LIFT-01. Every view of it groups into one physical shaft (`03`):

- the S-BW outlines on the foundation plan (10EA / 10EB) and the ground-beam plan (7BE / 7C2);
- the open-to-below panels on the GF and 1F roof sheets, and the roof panel on the 2F roof sheet;
- the inside faces on the three architectural plans.

The only other S-BW outline (GBP 7C5 / 7C6) is the S8.2 pool.

The shaft is 1800 x 1800 inside, with 200 walls and four corner columns:

- C2 at the SW corner;
- C1 at the NW corner;
- C9 at the SE corner;
- C2 at the NE corner.

It sits on the FF footing (460 x 450 x 55). It serves three stops (GF +1.00, 1F +5.50, 2F +9.70), each with a 1000 mm
door in the S wall, under the 2F roof at +13.90. No overrun is labelled.

## What is established and what is not

- **Plan geometry: established.**
  - The 3.24 m2 S8.1A opening equals the pit's inside area exactly.
  - The ring is 1.6 m2. The columns take 0.5 m2 of it, once.
  - The net wall pieces (S 1.8 m, N 1.8 m, W 1.2 m, E 0.7 m) give 1.1 m2.
  - Perimeters (m): inside 7.2, outside 8.8, centreline 8.
- **Pit floor.** It is the FF footing top: p.14 draws no pit slab, so no second base is added.
- **Levels: not established.**
  - The pit depth is 'As Per Lift Manufactures recommendations'.
  - The founding level is not printed. p.9 note 1 gives only a 1.5 m minimum excavation.
  - The wall top is the slab-on-grade top, which is FFL less a finish that is not printed.
- **Above the pit.** The enclosure is 'AS PER PLAN': 200 walls on the architectural plans only (blockwork, the
  S8.6 wall owner).

## Released

**0 m3 and 0 kg.**

- **Pit-wall concrete.** Blocked on the depth.
  - Coefficient: 1.1 m3 per metre of wall height.
  - Sensitivity: 2.145 m3, with FF at the -1.50 minimum founding and the wall top at +1.00. It is never released.
- **Wall bars.** p.14 draws 6Ø16/m vertical U-bars and 6Ø12/m horizontal bars on both faces of the two walls it
  cuts, the door wall (S) and the wall opposite (N). It also draws 2 Ø16 top and bottom in the footing under each
  wall, and 2Ø12 at the wall top. All are blocked: no bar length without the depth, no extents along the walls, and
  the W and E walls are not shown.
- **FF footing.**
  - The four mats are S4's: 720.239506 kg Ø14, a lower bound.
  - The concrete (11.385 m3) is computable. The footing family owns it and no frozen stage has measured it.
  - The S3.1 starters (85.271 kg) stay S3.1's.

## Tie beam (P8-N19)

| Storey | Floor to floor m | Floor-to-floor trigger | Clear to beam soffit | Requirement |
|---|---|---|---|---|
| GF | 4.5 | TRIGGERED | NOT_TRIGGERED | NOT_ESTABLISHED (triggered only under floor-to-floor; the note does not define its storey height) |
| 1F | 4.2 | NOT_TRIGGERED | NOT_TRIGGERED | NOT_REQUIRED (no measure gives a storey higher than 4.30 m: every other measure is smaller) |
| 2F | 4.2 | NOT_TRIGGERED | NOT_TRIGGERED | NOT_REQUIRED (no measure gives a storey higher than 4.30 m: every other measure is smaller) |
| FOUNDATION (footing to GF) | - | - | - | NOT_ESTABLISHED (no printed founding level; the pit walls are RC in this storey) |

## Open points

- **Conflict:** the foundation-storey column width (drawn 200 vs scheduled 300) at the pit walls (Q-LIFT-08).
- **Questions:** Q-LIFT-01 to Q-LIFT-13 in `14_RFI_QUESTIONS.csv`.

## Firewall

PRE-S8 is read through column whitelists only. No earlier lift figure is read before the freeze.
