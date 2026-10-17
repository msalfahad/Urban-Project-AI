# Independent calculation evidence (Phase 2B-7)

No V2.7 number is accepted because the engine produced it. Each is set against a truth the engine did not compute.
There are four kinds of truth:

- **H** — hand truth derived from the fixture coordinates. It is written in the fixture's docstring and the test,
  before the engine change.
- **I** — an independent reader of the DXF itself: `tests/m9_p2b7/p2b7_indep.py`. It uses ezdxf and math only and
  imports no engine module.
- **C** — the private raw-entity census and the Stage C room reading. These were made in Phase 2B-6 from raw ezdxf
  entities and the owner rules, and are never committed; only aggregates are shown here.
- **E** — the run-to-run identity of transformed drawings (invariance).

## Synthetic drawings (shareable)

| case | quantity | truth (kind) | V2.6 | V2.7 |
|---|---|---|---|---|
| CROSSING (door in a 1.027 m gap, 77 mm return, partition mouth) | structural opening | 0.80 m (H) | 1.027 | **0.80** |
| | bathroom plaster (1.677 + 3.0) × 2 × 3.0 − 0.80 × 2.10 | 26.382 m2 (H) | 26.2203 | **26.382** |
| | wall tile 9.354 × 2.4 − 0.80 × 2.10 | 20.7696 m2 (H) | 20.6079 | **20.7696** |
| | skirting 9.354 − 0.80 | 8.554 m (H) | 8.477 | **8.554** |
| | threshold / doorway waterproofing 0.80 × 0.20 | 0.16 m2 (H) | 0.2054 | **0.16** |
| | waterproofing upturn 8.554 × 0.20 | 1.7108 m2 (H) | 1.7031 | **1.7108** |
| | door position (middle of the extreme full-thickness jamb lines, mid wall) | (1.400, 0.100) (I) | (1.5135, 0.100) | **(1.400, 0.100)**, 12 placements to 1 mm |
| B10 (curved east wall, r 2.50 / 2.70 m, sweep 2 asin 0.6) | room area / perimeter | 13.021882 m2 / 14.217506 m (H) | exact | exact; the polygon follows the arc (shoelace within 0.003 m2) |
| | curved band on the mid radius 2.6 × 1.287002 | 3.346206 m (H) | missing | **3.346206** (MIN 3.217506, MAX 3.474906) |
| | false termination of kind OTHER | none (H) | 3.0 m | **none** |
| PLAIN with one exploded door (roles inferred) | floor | 12.00 m2 (H) | 11.6152 (−π 0.7²/4) | **12.00** |
| Aligned column row AT_WALL / FREE_ROW | hall area / perimeter | 47.36 / 35.20; 47.52 / 36.80 (H) | −0.3848 m2 (door as window) | **exact** |
| Framed door block (FLAT / GROUP / NEST / GROUP_NEST) | frame | 0.80 m (H) | 0.80 / 2.40 / 4.40 / 4.40, door withheld in 3 | **0.80** in all four, released |
| W.C. + unlabelled lobby (10.20 m2) | lobby type | basin alone → REVIEW; basin + drawn WC (3 encodings) → wet; Arabic word → wet (H, the owner's rule) | wet from the basin | as truth; 4 adversaries REVIEW; 2 known errors (strict xfails) |
| Zero-length repair | ring segment roles | 0.05 / 0.099 mm piece merged; 2 mm kept; length 12.000 m conserved (H) | sliver typed OTHER | as truth |

**Invariance (E).** Each drawing family was moved, turned 30° / 90° / 37°, mirrored, drawn in metres, reordered and
nested two blocks deep. The families are CROSSING, B10, the W.C. plan, the aligned row and the turned villa. Every
quantity equals the base run to 1e-5.

## Per-line provenance (I)

There are 10 drawings: CROSSING ×5 placements, B10, B10 nested, B02 (mirrored door block), B09 (mirrored plan), and
the synthetic villa. For each:

- **Resolution.** Every traced reference resolves to a live entity of the DXF. Its INSERTs exist, each lives in the
  block of the one before it, and the entity lives in the innermost block.
- **Room boundaries.** Each room's entities run along the room's boundary within 1 mm. The boundary not covered by
  them is no longer than the room's own openings (doors, passages, window thresholds) + 2 mm.
- **Walls.** Every wall entity lies on a face of a wall of its thickness family.
- **Openings.** Every opening entity lies at its opening:
  - a door's within a leaf's reach of a jamb;
  - a window's inside the opening box;
  - a passage's at a gap corner.
- **Mirrored insert.** B02's swing is read through the mirrored insert matrix by ezdxf: its centre is the hinge, on
  a jamb at the wall face (1 mm), and its radius is the 0.80 m leaf.

## The private reference plan (C; aggregates only)

**Stage C: five rooms read independently, 66 checks.**

- **V2.6: 8 failing checks.**
  - Seven come from one door in a wider gap: the wall gap was taken instead of the jamb span.
  - One comes from a W.C.'s doorway waterproofing, booked in the neighbouring basin-only space, which V2.6 typed wet.
- **V2.7: 0 failing checks.** The authorization's warning applies: this sample alone does not prove the method. It
  is one plan and five rooms. The other 9 changes on that plan are explained in `BOQ_IMPACT.md`.

**The curved band (raw-ezdxf census, inserts exploded).** The census finds 6 wall-layer arcs in the plan regions.

- One concentric pair forms a curved band:
  - thickness 0.20 m, sweep 90°;
  - mid arc 1.884956 m (min 1.727876, max 2.042035);
  - strip 0.376991 m2.
- The other 4 arcs are short unpaired pieces of 0.04 – 0.30 m: no band.
- V2.7's curved band record: the same three lengths to 1e-6.

**The run audit (`tools/arch_run_audit.py`, with the drawing).**

| | HIGH | MEDIUM | REVIEW | INFO |
|---|---|---|---|---|
| V2.6 | 1 | 4 | 3 | 1 |
| V2.7 | 0 | 0 | 4 | 0 |

- **Gone in V2.7:**
  - the curved band missing from the run (A07);
  - the door held for review (A08);
  - three spaces typed wet from basins alone (A09).
- **Left (REVIEW):**
  - three inferred column layers to confirm (A04, as for any inferred column layer);
  - one hatched column-size rectangle on the door layer whose COLUMN role V2.7 refused itself (A06, naming the
    refusal).
