# Masonry centreline run per wall thickness (T-027, MASONRY_CENTRELINE_V1)

Gate 2 (architectural coverage: blockwork by thickness). Rule UP-WALL-GEOM-001 (OWNER_APPROVED): the masonry run is the
wall CENTRELINE; each face is for finishing only. Columns in the wall line are concrete (UP-COL-ORIENT-001). Block m2 /
m3 stay HELD: the masonry height rule UP-MAS-HEIGHT-001 is REQUIRES_CONFIRMATION and owner question Q-60 is open.

## What was wrong

The released wall figure of ARCH_TAKEOFF_V2.9 (`arch_walls.walls`, `net_lm`) is the stretch where BOTH faces are drawn:
it leaves out the openings, the corner pieces and the T / cross pieces. On the T-019 synthetic villa SV-A the 0.20 m
walls give 44.4 m against the hand 54.6 m centreline (46.2 m after the listed openings). The band extent (`gross_lm`)
already includes the openings, the T pieces (on the wall that runs through) and the wall ends; what it still misses is
the L corner: both bands stop at the other's inner face (SV-A 0.20: 53.8 vs 54.6, four corners x 0.20).

## What the new piece does (engine/source/masonry_centreline.py, not wired)

Per floor and thickness family, from the band records: free ends kept; a T stem to the through-wall's face; an L corner
to the centrelines' meeting point (any angle; a 45 deg wedge included); a crossing of one family drawn as four stems
joined once; two collinear bands across exactly an opening's width joined (the opening is listed, never deducted);
curved walls on their centreline arc; columns cut from the centreline. Anything else (an end inside another band, a
partial corner, a crossing of two families with no wall running through) is HELD with the largest metres it could
add, never guessed and never 0.

## Results

| Case | Thickness | Hand centreline | Engine V2.9 net (face run) | New run | Openings listed |
|---|---|---|---|---|---|
| SV-A GF (mm, also 37 deg, mirror + m) | 0.20 | 54.60 | 44.40 | 54.60 | 8.40 |
| SV-A GF | 0.10 | 4.00 | 4.00 | 4.00 | 0 |
| SV-B GF / 1F (m, mirrored) | 0.30 | 39.20 / 39.20 | 30.00 / 30.65 | 39.20 / 39.20 | 7.10 / 6.60 |
| SV-B GF / 1F | 0.20 | 13.80 / 13.80 | 11.25 / 11.65 | 13.80 / 13.80 | 2.20 / 1.80 |
| SV-B GF / 1F | 0.15 | 7.85 / 5.00 | 6.10 / 4.20 | 7.85 / 5.00 | 1.60 / 0.80 |
| SV-C GF (37 deg; -121 deg mirror m; curved corner) | 0.20 | 68.499 | 54.699 | 68.499 | 11.60 |

Hand fixtures (tests/t027_masonry_centreline): L of 0.30 / 0.20, T of 0.20 / 0.10, crossings of one and two families,
column in the line / beside it / at a corner, 45 deg wedge, opening gap; each turned 37 and -121 deg, mirrored and in
metres: every value equals the hand figure to 1e-6 m.

## Alsenan

NOT MEASURED this run: decoding the Drive architectural DXF archive in the session was refused by the session
permission check ("[PII Data Handling]"), so the engine could not be run on Alsenan. The freelancer's blockwork rows
(Drive blockwork workbook) were read and summed by hand: FREELANCER_BLOCKWORK_METRES.csv. His metres:

| Group | GF | 1F | 2F / roof | Total |
|---|---|---|---|---|
| external walls (thickness not written) | 78.55 | 54.97 (+ 41.25 m2 projections, no metres) | 27.90 | 161.42 m |
| internal 0.15 | 47.53 | 57.14 | 3.00 | 107.67 m |
| internal 0.20 | 8.20 | 8.20 | 8.20 | 24.60 m |
| 0.15 parapets | - | 66.00 | 72.65 | 138.65 m |
| 0.15 boundary (site) wall | 37.20 | - | - | 37.20 m |

His rows are piece lengths at a height per row (GF 4.00 / 3.50, 1F 3.70 / 3.45, 2F 3.45 / 3.70; parapets 1.00 /
1.80; boundary 2.00); m2 1,260.69 after opening deductions (external 559.80, 0.15 617.25, 0.20 83.64). The heights are
the owner's Q-60 question; the comparison in metres is the next step once the engine runs on Alsenan (the hand table
per floor and thickness is T-103).
