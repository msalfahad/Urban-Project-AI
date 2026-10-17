# Architectural report (Phase N10, ARCH_TAKEOFF_V2.9)

V2.9 is opt-in (`--method ARCH_TAKEOFF_V2.9`). It is V2.8 plus three additions:

- curved openings (`CURVED_AND_TOPOLOGY_DEFECT_REPORT.md`);
- masonry by thickness;
- the facade.

It reads knowledge registry 1.5.0. Every new rule is REQUIRES_CONFIRMATION.

## 1. Masonry by thickness (UP-MAS-HEIGHT-001)

**Panel height:**

- Default: the floor's own section band, U/S SLAB − T.O.S. (T.O.S. within 0.30 m below the F.F.L.). Build-up = F.F.L. − T.O.S.
- Otherwise, stated facts `masonry.{floor|*}.panel_height_m` and `floor_buildup_m`.
- A finish height (F.C.L., plaster height) or floor-to-floor is never a masonry height.

**Beams over walls:**

- A section B.O.B. gives a beam depth. The panel is then a range between the beam bottom and the soffit, because the plan does not say which walls carry the beam.
- A stated fact `beams_over_walls` NONE / DEPTH is used as given.
- Otherwise the panel is **held at its upper bound** (HELD_UPPER_BOUND).

**Area and volume:**

- Area = (wall-mass plan area / t) × panel + the wall above and below each opening. The run already excludes the gaps.
  - Doors and passages count from the slab: height + build-up.
  - Windows count min(h, panel).
  - An opening with an unknown height gives a range [0, w × panel].
  - Curved openings use the mid-band arc.
- Volume = area × t.
- Junction pieces between different thicknesses are their own volume line, never given to one thickness.

**Material:** MAS.BLOCK takes the panel area only when `masonry.materials.{family}` is stated. Otherwise it is an RFI naming exactly what is missing (the panel, the material, or both).

**Lines and output:** ARCH.WALL_PANEL (m²) and ARCH.WALL_VOLUME (m³) per thickness family, the junction volume, MAS.BLOCK. Output file: MASONRY.json.

| Proof (hand truth) | Expected | Engine |
|---|---|---|
| 0.20 m walls, T.O.S. −0.10, U/S SLAB +3.10, no beams stated | 43.26 m² / 8.652 m³ | 43.26 / 8.652 |
| two derivations (run-equivalent, centreline) | 43.26 = 43.26 | — |
| with B.O.B. +2.60 | range 35.86 – 43.26 m² | 35.86 – 43.26 |
| no T.O.S. in the section | held (MASONRY_HEIGHT_NOT_IN_THE_DRAWING) | held |
| two sections disagree on T.O.S. | CONFLICT, no value | CONFLICT |
| 0.15 m partition + 0.20 m walls | 9.60 m² / 1.44 m³ partition; 40.70 m² outer; junction 0.512 m³ | as expected |

**Reference plan:** no section band carries T.O.S. and U/S SLAB, so every masonry line is held, with the reason. That is 7 panel and 7 volume lines in each mode.

## 2. Facade (UP-FACADE-001)

**Run:**

- The run is the outer cycle of the floor's plan topology. Every opening is closed on its outer wall face, so the run includes the openings.
- A wall network inside another network's face is an **island** (a column or a wall in a room) and never a facade.
- A network that encloses nothing (loose lines) is not an outline.

**Several outlines:**

- A second exterior outline on a floor is reported as an RFI and **never added**.
- An outline around the building (a boundary wall drawn on a wall layer) **holds** the facade.

**Area:**

- Height: F.F.L. → next floor's F.F.L. from the floor's section band. Above the top floor it runs to the lowest parapet top. A stated fact `facade.{floor|*}.height_m` is a labelled fallback.
- Deductions: each opening on the outline by its width on the outline × its own band:
  - a door from the F.F.L.;
  - a window min(sill + h, H) − max(sill, 0).
- An unknown height gives a range.

**Finish and plinth:**

- FIN.EXT.FINISH takes the area only with a stated finish (`facade.finish`).
- The plinth below the lowest F.F.L. is an RFI: the external ground level is not read.

**Lines and output:** ARCH.FACADE_RUN (lm), ARCH.FACADE (m²) and FIN.EXT.FINISH (m²), with the room id `{floor}-FACADE`. Output file: FACADE.json, which holds each outline, its openings, its ring and the height evidence.

| Proof (hand truth) | Expected | Engine |
|---|---|---|
| 4.40 × 3.40 m box, F.F.L. 0.00 → +3.50 | run 15.60 m; net 54.60 − 2.20 − 1.80 = 50.60 m² | 15.60 / 50.60 |
| curved room (outer arc r 3.20) | run 12.226548 m; openings 1.00 and 4.599882 m on the outer face | as expected |
| free-standing column in the room | an island: 1 outline, run 15.60 m | as expected |
| annex box 3 m east | SEVERAL_OUTLINES: 15.60 m measured, 8.00 m an RFI | as expected |
| boundary wall around the box | ENCLOSED_BUILDING: held | held |
| no next F.F.L. on the section | run measured, area held | as expected |

**Reference plan:**

- **Run:** measured on all 3 floors, 191.8556 m in total. It is PROVISIONAL because each floor also has a thin second outline (L-N10-01).
- **Area:** held. No section band gives the next F.F.L.
- **Check:** the outline plate equals the engine's floor plate on all floors.
- **Independent outline:**
  - 2F: VERIFIED (exact);
  - GF: not established (the reader leaks, D-N10-02);
  - 1F: CONTRADICTED by 0.16 m (an undetected window recess, D-N10-01).

## 3. What did not change in V2.9 (the V2.8 behaviour is kept)

- floors, ceilings, wall finishes and skirting, except at curved openings;
- doors and windows (curved ones added);
- waterproofing;
- stairs.

Each keeps its V2.8 rule and status.

## 4. Remaining architectural gaps

| Gap | Why | Next |
|---|---|---|
| masonry on the real plan | no T.O.S. / U/S SLAB on a bound section band; beams over walls unknown; material unknown | section binding; OQ-06 / OQ-07 |
| facade area on the real plan | no next-floor F.F.L. on a bound band | OQ-08; section binding |
| facade at set-backs (exposed slab edge, parapet) | not separate items | roof / parapet reader |
| roofs and balconies | no roof plan reader | a roof-plan reader + separate waterproofing |
| external reveals | measured only for curved openings (strips) | extend to straight openings |
