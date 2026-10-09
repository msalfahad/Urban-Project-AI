# S8.2 recovery note: container loss, input restoration and verification

## What was lost

The cloud container was reclaimed while S8.2 was still uncommitted. The new container got a fresh clone at `763a00e`,
without the client drawings in `data/inputs/by_sha256/`, which are never committed.

The work in progress was recovered from the session transcript and committed as `b83dc9d`:

| File | How it was recovered |
|---|---|
| `build_s8_2.py` | Exactly, from three complete reads plus a replay of every later edit. |
| `engine/source/pool_qto.py` | About 80% verbatim. The small helpers in the gaps were rewritten. |
| `tests/swimming_pool_s8_2/test_pool_qto.py` | Rewritten. |

## Inputs restored

The user supplied `Urban_Alsenan_S8_2_Source_Restore.zip`. It was extracted into an empty scratch directory and read
as data only.

| File | SHA-256 | Match |
|---|---|---|
| ST7757.dxf | `9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079` | MATCH |
| P7757.dxf | `ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4` | MATCH |
| ST7757.pdf | `74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3` | MATCH |

Each full hash was checked against `SHA256SUMS.txt` and against the hashes the builder pins. The files are restored
under `data/inputs/by_sha256/<sha256>.<ext>`, which `.gitignore` excludes through `/data/*`. They are not in git.

## Step 1: the pre-loss fingerprint is reproduced exactly

The reconstructed code reproduces every value of the last pre-loss blind run, compared row by row with the printouts
of that session:

- **Plan areas (m2)**, bit for bit:

  | Item | m2 |
  |---|---|
  | Structural footprint | 10.935563750809475 |
  | Water | 8.578838175124607 |
  | Wall band | 2.3567255756848677 |
  | Run E | 0.7 |
  | Run N | 0.31 |
  | Run S | 0.3100000000000596 |
  | Run W | 1.0367255756845697 |

- **Dot rows:** all 16, with every member handle.
- **Main runs:** R1 to R6, segment by segment, including the rounded coordinates and drawn lengths.
- **End mark:** M1 on R5.
- **Bar families:** all 21 IDs in order, with their segments and their leg lengths per region to 1e-6 drawing units.
- **Sub-detail shapes:** CR1 to CR10, with their shapes, junctions and segment lengths, and their correspondence with
  the main-section families.
- **The 26 records:** binding method, binding state, bound runs, dot rows and shapes, derived role, S1 role check,
  family and terminal state.
- **Dot bindings, the 27 conflict and question IDs, and the interface rows.**
- **Conservation checks C-01 to C-16:** all PASS.

## Step 2: independent checks of the helpers on the real geometry

The helpers were not trusted because the synthetic tests pass. Each one was checked against references taken from
the raw DXF through ezdxf (not the S1 reader) and from shapely. These checks now run as
`tests/swimming_pool_s8_2/test_s8_2_real_geometry.py`. All 17 checks pass after the two corrections below.

| Helper | Reference | Result |
|---|---|---|
| `region_area_m2`, `band_area_m2`, `ring_length_m` | Raw LWPOLYLINE, bulges sampled on the true circle (`bulge_to_arc`); shapely; closed form | Agree to 1e-9 m2 / 1e-13 (closed form) |
| `_seg_end`, `_seg_len` | ezdxf LINE / ARC entities | Ends within 0.0007 units (S1 rounds to 1e-3); lengths within 0.001 units after correction 1 |
| `_reverse`, `_dir` | Numerical tangents | Within 5e-7 |
| `_geom_key` | Brute-force duplicate search on ezdxf entities | The same single pair, 1922 / 1924 |
| `_pt_seg`, `target_distance` | shapely distances, 6,498 pairs | Within 4e-12; arcs within 2e-8 after correction 2 |
| `leg_lengths_in` | shapely clipping | Within 3e-12 |
| `parse_notation` | An independent reading of all 26 labels | 19 RATE, 4 SPACING, 3 FINITE_GROUP |

ezdxf's `make_path` flattening was rejected as a reference. It draws bulges as Bézier curves, which lie about 0.5 mm
outside the true arc at R1750.

## Two latent defects, shared with the pre-loss code, corrected before the freeze

1. **The wrap-around arc 1849** is drawn from 270° to 0°. The S1 reader gives CCW angles with a1 < a0. The old code
   read that as a 270° clockwise sweep instead of 90° CCW, so its length was 104.27 units (r·π) too long. The builder
   now unwraps CCW sweeps, and `chain_runs` rejects a zero or over-full sweep.
   - Effect: BF-R4's leg length in SHALLOW_BASE drops from 5718.781385 to 5614.513008 drawing units, and R4's turns
     now read 90 / 90 / 90 / 45, symmetric with R1.
   - Unchanged: owner, shape, lane, terminal states, quantities and checks.
2. **`target_distance` measured to the full circle** of an arc. It now measures to the drawn sweep.
   - Effect: two false incidental contacts disappear, 1881 on arc 1886 (61.26 units from the drawn arc) and 1896 on
     arc 189A (54.90 units).
   - Unchanged: bindings, because the dot contacts already governed them.

## Two changes before the freeze

- One question was added, Q-S8.2-11: confirm that "(N.I.S)" means not to scale. S1 had recorded it as "not in
  scope".
- The interface audit now lists only the bars that cross a level-change junction. That gives 14 rows, down from 18
  before the loss.
