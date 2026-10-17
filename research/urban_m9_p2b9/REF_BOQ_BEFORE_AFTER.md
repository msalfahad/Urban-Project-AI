# Reference-plan BOQ before / after (ARCH_TAKEOFF_V2.7.1 → V2.8)

These are aggregates only: no room ids and no private names.

- **Mode A** uses the stated synthetic project facts file (the S2 facts: wall heights and door / window heights).
- **Mode U** uses no facts.

The figures are from the final snapshot of the committed tree (`REGRESSION_AND_FROZEN_EVIDENCE.md`).

## 1. Line states

| Mode | Method | Lines | SOURCE_DERIVED | PROVISIONAL | BOUNDED_EXPOSURE | BLOCKED_RFI | NOT_APPLICABLE | Confirmed / held / excluded |
|---|---|---|---|---|---|---|---|---|
| A | V2.7.1 | 487 | 196 | 100 | 66 | 125 | 0 | 296 / 191 / 0 |
| A | V2.8 | 487 | 196 | 100 | 66 | 125 | 0 | 296 / 191 / 0 |
| U | V2.7.1 | 476 | 152 | 100 | 35 | 161 | 28 | 252 / 196 / 28 |
| U | V2.8 | 476 | 152 | 100 | 35 | 161 | 28 | 252 / 196 / 28 |

## 2. Quantity changes

| Item | Mode | V2.7.1 | V2.8 | Change | Drawing evidence → formula → hand → engine → status |
|---|---|---|---|---|---|
| ARCH.WALL_RUN (first floor, 0.20 m family) | A and U | 216.7625 m (all floors) | 216.9311 m | **+0.16854 m (+0.08 %)** | a concentric wall-arc pair, both faces drawn over a 0.0828 rad sweep beside a curved window → centreline r 2.035 m × 0.082820668 rad → 0.16854 m → 0.16854 m → **VERIFIED** (independent arc census) |
| every other item | A and U | — | — | **0** | — |

**Why so little changed.**

- **No height evidence.** The plan has no door / window schedule, no section the reader can bind to a floor, no
  height notes and no opening marks. The new height and opening logic therefore keeps the V2.7.1 reading: facts in
  Mode A, blocked in Mode U.
- **Skirting.** Every window's sill is unknown, but all 23 windows on room boundaries already had their threshold
  edges in the F-17 range, so the edge-by-edge check moves nothing. A first draft moved 30.75 m twice; that was
  caught and fixed.
- **Wall run.** The reader found one curved stub (verified). The return census found no straight return inside the
  plan regions.

## 3. Missing height evidence on the reference plan

| Item | Mode A | Mode U |
|---|---|---|
| rooms: plaster height (soffit) | 25 (project facts, not drawing) | 25 (none) |
| rooms: paint height (finished ceiling) | 25 (facts) | 25 (none) |
| wet rooms: wall-tile height | 14 (facts) | 14 (none) |
| windows: height | 26 (facts) | 26 (none) |
| windows: sill | 26 (none) | 26 (none) |
| doors: height | 22 (facts) | 22 (Urban default, labelled assumed) |
| **items** | **138** | see the note below |

Mode U is confirmed from the final snapshot below.

## 4. Other V2.8 outputs on the reference plan

| Output | Content |
|---|---|
| OPENING_SCHEDULE | 48 openings; 26 windows, 0 with a sill; 0 heights from the drawing |
| WINDOW_REVEALS | 0 measured (no sill established) |
| WALL_GEOMETRY | every band with centreline, thickness and plan strip; curved bands with three arcs; 1 stub; conservation per floor |
| HEIGHT_EVIDENCE | 0 schedules; 2 elevation views with level texts but no finished-floor band; 0 project notes |
| unclosed labels | 0 rooms; 11 open-area labels (garden, roof, pool, void) |
