# T-017: independent masonry census (PAIR_MIDLINE_CENSUS_V1), wall by wall against the block ledger

Worker 2, 2026-10-23 19:41 - UTC (lane A, gate 2; defect D-N10-03: "there is no independent masonry reading"). A CHECK,
not a quantity: no released quantity, rule file, frozen method, engine module or registry is changed; nothing here is
wired. Development villa, not an accuracy claim. Drawings cited by Drive title and entity handle only (no coordinates).
ERS: read; s.2 (element, evidence, first-principles reconstruction, reconciliation in units, status), s.3 (physical
length vs the ledger's run conventions; build before deduct) and s.4 (rule, test, lessons row) applied.

## 1. Element and method

Element: every block wall on the three plan floors of Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip ->
P7757.dxf (sha256 ab54dd55...31cc4 = manifest), its PHYSICAL architectural run length per owner Q-69 B (columns cut,
doors / windows / passages kept in the run, glazed lines out, T stems to the face, masonry never in two walls).

`masonry_pair_census.py` (standard library only; test `test_independence_no_engine_import`) shares no code with the wall
stage (arch_walls), MASONRY_CENTRELINE_V1 / V2 or MASONRY_AREA_V1, and starts from the raw linework (its own ezdxf read,
inserts exploded): (1) wall-face segments merged into maximal lines; (2) two parallel lines at a thickness class
(0.10 .. 0.40 +- 0.006) form a both-faces piece on their midline; (3) gaps between pieces on one midline are classified
from the drawing: COLUMN (outline on the column layer covers >= half the thickness: cut, ends the run), ONE_FACE (one face
continues: a junction, in the run), OPENING (a door / window entity in the gap, or head / symbol lines on another layer
along BOTH faces across it: a passage), CROSSING (a perpendicular wall drawn through: counted once), SPLIT (no evidence:
the run ends); a mixed gap is cut at every face / head line end and each part classified; (4) ends: a corner square is
owned by the drawn faces: shared at the midlines when both outer faces run through it (L), the whole square to the wall
whose face crosses it when only one does (JUNCTION_OWN), none when the end sits on a face (T_STEM); (5) caps (jamb pairs)
are not walls. Curved walls are NOT READ (listed, never 0). Unit guard: a face longer than 200 m is refused (mm input).

Matching key only: each census run is placed on a ledger row through the plan run's band centrelines (one V2 capture,
`research/agents_t125/alsenan_v2_run.py`); no ledger number feeds the census.

## 2. Result: every wall (T017_WALL_AGREEMENT.csv, 75 rows = the T-143 hand list)

| Status | Walls | What |
|---|---|---|
| AGREE (abs d <= 0.050 m) | **59** | same length and thickness, read independently |
| DIFFERS, corner-square ownership (RULE_DIFFERENCE) | 9 | GF-W00 -0.100 / GF-W17 +0.100; 1F-W08 -0.100 / 1F-W04 +0.100; 1F-W21 -0.075 / 1F-W16 +0.075; GF-W02 -0.075 / GF-W23 +0.100; GF-W19 +0.075 (with GF-W30) |
| DIFFERS, oblique (45 deg) end not closed (UNRESOLVED) | 3 | GF-W20 -0.125, GF-W21 -0.062 (ledger holds 0 .. 0.137 m more there too); GF-W30 1.193 vs hand 1.525 (bounds) |
| NOT READ / NOT FOUND (never 0) | 4 | GF-W35 1.885 and 1F-W25 0.169 (curved); GF-W37 0.100 (piece at the pool-side glazing: no paired faces); GF-H02 0.900 (not on the wall-face layer; the ledger holds it) |

Thickness: the census and the ledger agree on every one of the 71 walls the census reads (0.15 / 0.20 / 0.40). No census
run is left without a ledger wall (no masonry the ledger lacks). GF-W30, which the engine's plan run misses (T-125
"MISSING"), is FOUND: 0.279 m both faces (D2:741 / D2:743) + 0.800 door + 0.039 m stub + 0.075 m corner.

## 3. Per floor and thickness (T017_BY_FLOOR_THICKNESS.csv), metres

| Floor / t | Ledger physical (T-108 r2) | Census | Census - ledger | Explained by |
|---|---|---|---|---|
| GF 0.15 | 39.313 | 38.935 | -0.378 | GF-W30 -0.332, 45 deg ends -0.187, corners +0.175, rows within tolerance -0.034 |
| GF 0.20 | 91.443 | 88.483 | -2.960 | not read 2.885 (GF-W35 1.885 curved, GF-H02 0.900, GF-W37 0.100) + GF-W02 corner -0.075: **residual 0.000** |
| GF 0.40 | 0.600 | 0.600 | 0.000 | (band through a 0.80 column: column cut, as the ledger) |
| 1F 0.15 | 56.736 | 56.736 | -0.000 | corners net 0 |
| 1F 0.20 | 60.021 | 59.835 | -0.186 | 1F-W25 0.169 not read (curved) + rows within tolerance -0.017 |
| 2F 0.15 | 10.900 | 10.900 | 0.000 | |
| 2F 0.20 | 28.700 | 28.700 | 0.000 | |

Census decomposition (engine physical = both faces - columns + openings in the run + one-face + corner pieces): e.g. GF
0.20 75.979 - 13.160 + 21.360 + 2.029 + 2.275 = 88.483. The T-225 residual "0 .. 2.529 m, junction pieces and one-face
stretches" (agents/task-T-225 @ 96500525) is these junction pieces: census one-face + corner pieces GF 0.15 1.200 /
0.20 4.304, 1F 1.950 / 2.347, 2F 0.400 / 1.100 m. 2F 0.15 matches T-225 exactly (0.400 = 0.400); at 2F 0.20 the
0.600 m between 1.100 and 0.500 is exactly run A's both-faces length 22.300 less the census both faces net of columns
(25.800 - 4.100 = 21.700), i.e. a definition difference, not masonry. On GF and 1F the two splits are not like for like
(run A's both-faces length runs through columns, the census cuts them, and the opening widths differ by 0.15 m on GF
0.20), so the T-225 residual is now explained by kind (junction pieces and one-face stretches, listed per wall in the
band table), not re-derived as one number.

## 4. Engine vs freelancer (development reference, never a target), metres

| Floor | Census physical (0.15 + 0.20) | + glazed lines the physical run excludes | Freelancer | Difference | Like for like? |
|---|---|---|---|---|---|
| GF | 127.418 | + W02 6.332 = 133.750 | 134.28 | -0.530 (-0.4 %) | no: census leaves GF-W35 1.885 / GF-H02 0.900 / GF-W37 0.100 unread; he lacks GF-W30 and the W37 glass line (T-125) |
| 1F | 116.571 | + bay glass 3.579 = 120.150 | 120.31 | -0.160 (-0.1 %) | no: 1F-W25 stub 0.169 not read (with it +0.009) |
| 2F | 39.600 | none | 39.10 | +0.500 (+1.3 %) | yes (lengths): his 2F-W08 3.00 = ours; the rest is his end convention (T-125) |

What changed: nothing in any BOQ quantity. What is new: the ledger's wall lengths are now confirmed by a second,
independent reading on 59 walls (and per floor / thickness on everything it reads, to 0.000 m on GF 0.20, 1F 0.15, 2F),
which is evidence for the Checker, not a VERIFIED status.

## 5. What was learned (the differences that are not reading limits)

1. **Corner-square ownership is not uniform in the plan run.** At GF-W00 / GF-W17 and 1F-W04 / 1F-W08 the ledger
   splits the square at the midlines although the drawing carries one wall's face across it; at GF-W02 / GF-W23 and
   1F-W16 / 1F-W21 it gives the whole square to one wall although both outer faces run through (a drawn L read as a T).
   Same plan area either way (the square is counted once); per-wall lengths move by t / 2 .. t, and at GF-W02 / GF-W23
   0.075 m of 0.20 wall becomes 0.100 m of 0.15 wall (thickness family and block type change, 0.030 m2 of plan).
   Verdict proposal: RULE_DIFFERENCE (no Urban rule assigns the corner square; Q-69 B only forbids counting it twice).
2. **Oblique (45 deg) junctions stay open in both methods**: the census stops on the drawn pair, the ledger on its
   module end with a held bound; the true piece is a wedge between the two (GF-W30: 1.193 .. 1.525 m).
3. Passages are drawn as head / symbol lines along both faces on another layer (layers 5 and 2 here); reading them as
   "no evidence" split those runs in this census's first pass (each passage 0.90 .. 1.30 m, P-1F-01 among them).

## 6. Rule, test, lessons row (ERS s.4)

- Rule proposal **UP-MAS-CORNER-001 v1.0.0** (new file, any villa; provenance: Q-69 B + this census): the corner square
  of two walls belongs to the drawn faces: shared at the midlines when both outer faces run through it, to the wall
  whose face crosses it when only one does, never in two walls; a corner of two thickness families reports both
  lengths. A lane I rule version decides adoption; nothing here changes the ledger.
- Tests: `tests/t017_pair_census/test_pair_census.py` (12; fixture K17, not Alsenan: 0.20 ring 31.600 m with a column
  cut, window and passage in the run, 0.15 stem 5.800 m with T stems on the faces; adverse: mirror, 30 deg rotation,
  shift, mm input refused, missing column outline never bridged, crossing once, missing wall reported both ways
  (MISSING_IN_CENSUS / MISSING_IN_LEDGER), stem to the centreline (+0.200) and a duplicated stem (DUPLICATE) reported,
  no engine import) and `test_t017_alsenan_tables.py` (5: 75 walls once, every non-agreement has a cause and verdict,
  floor identity, components add up, no coordinates).
- Lessons row proposed: 2026-10-23 | wall lengths had no independent reading (D-N10-03) | every check re-used the plan
  run's own wall stage | an independent census from the raw face linework, sharing no code, agrees on 59 / 75 walls and
  names every other difference (corner ownership, oblique ends, curved walls, layer limits) | tests/t017_pair_census |
  PROPOSED (T-017 READY).

## 7. Reproduce

    python3 -I research/agents_t125/alsenan_v2_dump.py <P7757.dxf> --out <scratch>/t125_inputs.pkl
    python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/t125_inputs.pkl --out <scratch>/t125_v2.json
    python3 -I research/agents_t017/alsenan_t017.py <P7757.dxf> <scratch>/t125_inputs.pkl <scratch>/t125_v2.json --check

Files: `masonry_pair_census.py` (method), `alsenan_t017.py` (run + causes), `T017_WALL_AGREEMENT.csv` (75 walls),
`T017_BAND_AGREEMENT.csv` (64 plan-run bands), `T017_BY_FLOOR_THICKNESS.csv`, `summary.json`.
Missing: curved walls (GF-W35, 1F-W25) and oblique ends are not read; GF-H02 off the wall layer; heights / areas are
out of scope (a length census).
