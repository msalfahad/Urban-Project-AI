# S8.2 work in progress: recovery note (not frozen, no outputs)

This commit is **not** the S8.2 freeze. It holds no outputs and no freeze manifest. No reference, donor or earlier pool
quantity has been opened (`references_read` stays `[]`).

## What happened

The cloud container was reclaimed while S8.2 was still uncommitted. The new container got a fresh clone of the branch
at `763a00e`. It does **not** have the client drawings in `data/inputs/by_sha256/`, which are never committed:

- `9f9d1179…dxf` (ST7757)
- `ab54dd55…dxf` (P7757)
- `74da1523…pdf` (ST7757)

The S8.2 work was recovered from the session transcript as follows.

| File | Recovery |
|---|---|
| `research/alsenan_swimming_pool_s8_2/build_s8_2.py` | **Exact.** The full text was rebuilt from three complete reads, then every later edit was replayed. One addition: a clear STOP when the drawings are absent. |
| `engine/source/pool_qto.py` | **About 80% verbatim** (the printed line ranges). The gaps were small helpers and were rewritten to the documented behaviour: the error class, `established`, the `parse_notation` branches, area / band / ring length, segment end / length / key / reverse / direction, point-to-segment distance and target distance. |
| `tests/swimming_pool_s8_2/test_pool_qto.py` | **Rewritten.** The originals were not in the transcript. There are 28 synthetic known-answer tests and they pass. |

## Pre-loss blind run: a regression fingerprint, not a reference

When the drawings return, the first rebuild must reproduce these values from the last run before the loss. Any
difference is a reconstruction defect in `pool_qto.py` and must be fixed before the freeze.

**Plan areas (m2)**

| Item | m2 |
|---|---|
| Structural footprint | 10.935563750809475 |
| Water | 8.578838175124607 |
| Wall band | 2.3567255756848677 |
| Run E | 0.7 |
| Run N | 0.31 |
| Run S | 0.3100000000000596 |
| Run W | 1.0367255756845697 |

**Bar runs and families**

- Main runs: R1 COMPOUND, R2 CRANKED, R3 CRANKED, R4 COMPOUND, R5 CRANKED, R6 CRANKED.
- One end mark, M1, on R5.
- 16 dot rows.
- Sub-detail shapes CR1 to CR10:
  - CR5 and CR9 are L.
  - CR1 and CR2 are COMPOUND.
  - The other six are CRANKED.
- 21 bar families: 11 base and 10 wall. 16 are BLOCKED_UNQUANTIFIED and 5 are SOURCE_CONFLICT.

**Terminal states of the 26 records**

| State | Count | Records |
|---|---|---|
| FAMILY_PRIMARY_LABEL | 17 | |
| SAME_FAMILY_SECOND_LABEL | 1 | |
| SECOND_VIEW_OF_FAMILY | 5 | 1860 → BF-R5, 187C → BF-R1-D14, 18D7 → BF-R6, 18DB → BF-R2, 1929 → BF-R4 |
| SECOND_VIEW_DIAMETER_CONFLICT | 1 | 18A8 |
| SECOND_VIEW_TOPOLOGY_DIFFERS | 1 | 18DD |
| SUB_DETAIL_BINDING_AMBIGUOUS | 1 | 1869 |

**Released quantities and checks**

- Released concrete: 0 m3. Released steel: 0 kg. Totals are unknown, not 0.
- Conservation checks C-01 to C-16: all PASS.

**Not yet run:** the last edit, which keeps only the bars that cross a level-change junction, was never executed.
Before it, the interface verdicts were BASE_ONLY 5, SINGLE_BENT_BAR 5 and UNRESOLVED 8. After it, expect fewer rows at
J-DEEP-SLOPE and J-SLOPE-SHALLOW.

## Remaining S8.2 steps

1. Restore the three drawings.
2. Rebuild twice and check the output is byte-identical.
3. Check the build against the fingerprint above.
4. Write the package tests.
5. Make the freeze commit.
6. Do the post-freeze comparison.
7. Run the full suite and write TEST_RUN.md.
