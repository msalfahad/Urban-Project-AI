# T-050: trace of the foundation-level perimeter band (8 edges, 2 lost), Alsenan development villa

Worker 3, 2026-10-19 05:00-05:50 UTC. Diagnostic only: no engine, rule, knowledge, test or data file changed.
Development reference, not an accuracy claim. No drawing coordinates, labels or client data: entities are named by
DXF handle, span index, layer and length; sample points by their position along the edge (t = 0 .. 1).

**Limit of this run (read first).** The session permission check refused running repository code (route G, the
codemap tool and the freeze check: "Code from External"), and fetching other task branches. So this trace is a
**hand reading**: the DXF read with ezdxf 1.4.4 in a scratchpad venv by my own script (not committed), checked
against the frozen code read line by line. The engine's own state of each edge is NOT reproduced by a run here;
`research/agents_t050/edge_trace.py` (new, read only, not yet run) prints it for the verifier. One of the two lost
edges (inner span 2) is settled by deduction from the engine's own reported shape, not by its state record.

## Input

| Input | Where | sha256 |
|---|---|---|
| structural DXF | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (3 153 037 bytes) | 9f9d1179...38079 (= SOURCE_MANIFEST.json, = T-037) |

Engine side taken from T-037 (rerun on 56820cb): line L-b41f1c7e4f8707dce180, STR.CONC.BOUNDARY_WALL, SOURCE_DERIVED,
strip 0.20 x 60.17 m x H 0.60 (B.W row) = 7.220 m3; completeness finding CC-9fd936ab60, group entities
D2:5720:0,1,3 and D2:5721:0,1,3.

## The 8 edges (FOUNDATION PLAN, layer S-BOUN)

Two closed LWPOLYLINEs, no bulges: handle 1658 (= intake id D2:5720, outer, plot line) and 1659 (= D2:5721, inner,
offset 0.200 m all round). Span i runs from vertex i to vertex i+1. Span 2 of both is the long side on the
neighbour side, the side where the footings and columns are cast against the plot line.

| Edge | Span | Drawn length m | Centreline side m | Sample points explained (hand) | Fate | In engine strip m |
|---|---|---|---|---|---|---|
| D2:5720:0 | outer long side (street side) | 31.370 | 31.170 | 0 / 5 | UNEXPLAINED -> group | paired with 5721:0: 30.970 |
| D2:5720:1 | outer short side | 15.000 | 14.800 | 2 / 5 | UNEXPLAINED -> group | paired with 5721:1: 14.600 |
| **D2:5720:2** | **outer long side (neighbour side)** | **31.370** | **31.170** | **4 / 5** | **EXPLAINED_BY_MEMBER (removed before grouping)** | **0** |
| D2:5720:3 | outer short side | 15.000 | 14.800 | 1 / 5 | UNEXPLAINED -> group | paired with 5721:3: 14.600 |
| D2:5721:0 | inner long side | 30.970 | (same side as 5720:0) | 0 / 5 | UNEXPLAINED -> group | (pair above) |
| D2:5721:1 | inner short side | 14.600 | (same as 5720:1) | 3 / 5 | UNEXPLAINED -> group | (pair above) |
| **D2:5721:2** | **inner long side (neighbour side)** | **30.970** | (same as 5720:2) | **3 / 5 by drawn outlines** | **not in the group (deduced, see below); its partner is gone, so no pair either way** | **0** |
| D2:5721:3 | inner short side | 14.600 | (same as 5720:3) | 1 / 5 | UNEXPLAINED -> group | (pair above) |

Length check: centreline 2 x 31.170 + 2 x 14.800 = **91.940 m** (= T-037 E4). Engine 30.970 + 14.600 + 14.600 =
**60.170 m**. Difference 31.770 m = **31.170 m** (the lost neighbour side) + **0.600 m** (3 kept sides x 0.200 m:
the strip length is the paired overlap, i.e. the inner face length, not the centreline). Volume at the B.W section
0.20 x 0.60: 31.770 x 0.12 = **3.812 m3** (31.170 m -> 3.740 m3 lost side; 0.600 m -> 0.072 m3 corner basis).

"Sample points explained (hand)": the ledger samples every LINE at 5 points, t = 0, 0.25, 0.5, 0.75, 1
(`engine/source/concrete_completeness.py:523`, `_entities`); a point is explained when it is within
EXPLAIN_TOL_M = 0.03 m of a member footprint edge, or inside a solid member (column, band, ...), but not inside a
FOOTING unless the line is on a footing / column layer (`_explained_by`, `:581-590`; `footing_content_layer`,
`:238-240`; S-BOUN is neither); a line is EXPLAINED_BY_MEMBER when the share is >= EXPLAINED_SHARE = 0.8, i.e. 4 of
5 points (`_explained_share` `:1233-1238`, test at `:864-868`). By hand I used the drawn closed outlines on
S-COL.BON (columns) and S-FOOTINGS (footings) as the member footprints.

## Where the 2 edges go

### D2:5720:2 (outer, 31.37 m): explained away by the footings and columns on the plot line

| t | Explained by (hand) |
|---|---|
| 0 | on the edge of column outline 10A4 (corner column on the plot line) |
| 0.25 | on the edge of footing outline 1B1A (its side lies on the plot line) |
| 0.5 | on the edge of column outline 10DD |
| 0.75 | nothing (between footings) |
| 1 | on the edge of column outline 10AB (corner column) |

4 / 5 = 0.8 >= 0.8: **EXPLAINED_BY_MEMBER at `concrete_completeness.py:864-868`** (`geometry_ledger`), so the edge
never reaches `_split_outline_loops` (`:888`) or `_clusters` (`:890`). On this side the drawn footings cover
1.80 + 3.50 + 3.80 + 3.25 = 12.35 m of the 31.37 m plot line (39 %) and the columns a further part; the 5-point
sample happens to land on member edges at 4 of 5 points, so the whole 31.37 m line is taken as "the members' own
line". The same line is also the band's outer face.

### D2:5721:2 (inner, 30.97 m): absent from the group; exact stage to confirm with edge_trace.py

- By the drawn outlines it scores 3 / 5 (points t = 0, 0.5, 1 inside corner / plot-line columns; t = 0.25 inside
  footing 1B1A, which does not count for an S-BOUN line; t = 0.75 nothing): below 0.8, so by drawn outlines alone it
  would stay UNEXPLAINED.
- But it cannot have been in the group: with D2:5721:2 present, the 4 inner spans form a closed loop, `_describe_group`
  takes the loop branch (`:1256-1270`), and the inner loop alone (30.97 x 14.60 m, 2A / P = 9.9 m wide, outside
  STRIP_WIDTH_M 0.08-0.8) is a CLOSED_AREA, not the STRIP 60.17 m the engine reports. It was not taken out as a plot
  loop either (`_split_outline_loops` `:1031-1071` replaces a plot loop's ids with PLOT_EDGE ids, and the finding lists
  D2:5721:0,1,3). So D2:5721:2 left before grouping: EXPLAINED_BY_MEMBER (`:864-868`) by a member that is not a drawn
  closed outline (route G also makes strap bands, strap candidates and slab faces, `_members` `:408-458`, from paired
  lines), or CONTEXT_OF_OTHER_SHEET (`:869-883`, exact edges of measured members on another sheet of the same level
  group).
- Either way the length is lost by the **pairing**, not by this edge: once D2:5720:2 is gone, D2:5721:2 has no
  partner within 0.08-0.8 m, and `_parallel_pairs` (`:660-691`, called at `:1273-1279`, pairs at `:1274`) counts only paired overlap.
  So the drop of the neighbour side is caused by D2:5720:2 at `:864-868`, whatever state D2:5721:2 has.

## Why this is general (not Alsenan)

On a Kuwait villa the footings and columns on a neighbour side are routinely cast against the plot line (eccentric
footings), so the plot line, the boundary band's outer face and the footing / column edges coincide. Three general
defects follow:

1. **Sampling, not length (`:523` + `:1233-1238`).** A long line is explained by 5 points; whether it is "a member's
   line" depends on where the members happen to fall, not on how much of its length they cover (here 4 / 5 points
   for well under half the length).
2. **An explained face takes its strip partner with it (`:864-868` -> `:1273-1279`).** The ledger removes a line as
   explained without checking that it is also one face of a same-layer strip, so the strip loses the whole side and
   nothing is held or reported for it: UP-QTY-STATUS-001 (an element is never silently dropped).
3. **Strip length basis (`:1276-1279`).** The length of a paired strip is the paired overlap (the shorter face), not
   the centreline: a closed band loses one width per corner (0.20 m x 4 = 0.80 m on a full ring, 0.60 m here).

Not traced: other S-BOUN groups on other sheets (the ground-beams plan repeats the outer outline only, handle 81D:
one loop, no band).

## Proposed fix task (for the lead; I opened none)

**T-0xx Perimeter band: an explained face never takes its strip with it.** New version pieces beside the frozen
code (`concrete_completeness.py` is FROZEN; e.g. a new module `engine/source/strip_faces.py` used by a new
completeness option, off by default so frozen runs reproduce):
- (a) explained share by **covered length** (the union of the line's stretches within EXPLAIN_TOL_M of member edges,
  over its length), not by 5 points;
- (b) before grouping, a line on a non-member layer (layer family BOUNDARY_WALL / WALLS / UNKNOWN) that has a same-layer
  parallel partner within STRIP_WIDTH_M stays in the strip search even when explained; the part both faces share
  with member edges is recorded (a coincident footing face is a fact, not a reason to drop the band);
- (c) a closed band read as two nested loops gives length = ring area / width (centreline), and an unpaired face
  becomes a HELD finding with its length, never 0 and never silent;
- (d) the CLOSED_AREA trap: when all 8 edges are present the inner loop alone must not become CLOSED_AREA
  (`:1256-1270`): two nested loops of the same layer at a strip offset are a RING / band.
Fixture (hand calculated, not Alsenan): plot 20.00 x 10.00 m, band 0.20 m inside it on layer BOUNDARY, three footings
1.50 m wide butting the south plot line placed so that 4 of the 5 sample points of the south line fall on footing
or column edges; expected centreline 2 x (19.80 + 9.80) = **59.20 m**, plan 11.84 m2, at 0.20 x 0.60: **7.104 m3**;
adversarial: (i) mirror (footings on the north side), (ii) rotated 30 degrees, (iii) in mm and in m, (iv) the
south inner face not drawn -> the south side HELD with its outer length, never 0, (v) no footing on the line ->
the same 59.20 m (regression of today's behaviour on a clean band), (vi) a footing covering the whole side.
Whether the band belongs in the footing line stays owner Q-12 (c): the task does not decide it.

## Verdict proposal (for the verifier)

| Line / term | Proposal | Basis |
|---|---|---|
| CONC.FOOTING, edge strip length | **ENGINE wrong (short)**: drawing 91.94 m -> 11.033 m3 at 0.20 x 0.60; engine 60.17 m (7.220 m3); freelancer 71.7 m (8.604 m3) also short of the drawing, so UNRESOLVED for him (his 71.7 m is not identifiable as a set of drawn sides) | the 8 edges above |
| Silent omission | **yes, 3.812 m3** (31.17 m side + 0.60 m corner basis) appears in no released, held or finding line | UP-QTY-STATUS-001 |

## Uncertain / not done

- No engine run in this session (permission refusal above): the states in the table are hand emulations of the frozen
  rule on the drawn outlines; the verifier should run `edge_trace.py` (command in its docstring, handles 5720 5721)
  and compare. If D2:5720:2 shows a state other than EXPLAINED_BY_MEMBER, this trace's cause is wrong.
- The stage that removes D2:5721:2 is deduced (two candidates named), not read from a state record.
- Freeze check and `codemap.py build / check` were not run (same refusal). This branch changes only `research/`
  (no file under engine/, tools/, rules/, knowledge/, data/registry/), but adds the folder `research/agents_t050/`,
  so docs/CODEMAP.md's research folder table is stale until the verifier runs `python3 -I tools/codemap.py build`.
- Whether the B.W 20 x 60 row is the band's section is T-037's inference (mark and width), not printed on the plan.
