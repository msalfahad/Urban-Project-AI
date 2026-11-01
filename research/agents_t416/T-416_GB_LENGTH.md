# T-416 Ground-beam length: every run net of its supports, frame by frame, and the GB-MAIN length residual

Worker 1 (lane S), 2026-11-01 UTC, run session_01E6cPneuSWphv5A9iAjx1dC, branch `agents/task-T-416`. Research only: no
engine, candidate, released line, rule or method version changed; nothing released. Development villa, not an accuracy
claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Owner rules: Q-61 C (member by member, face to face), UP-QTY-STATUS-001,
no-assumptions rule; register ruling FENCE GATE / band partition (2026-11-01 04:15).

## 0. Sources and reproduction

Drive "Urban BOQ private data / Alsenan chalet project" (read-only; decoded into `.work/private` only): 'ST7757 dxf.dxf'
(sha `9f9d1179`), the concrete + rebar workbook (quantities only, private step). Candidate ground-beam lines: the 58
STR.CONC.GROUND_BEAM lines as T-391 bound them (`research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json` + the V3.0.29
downgrades); the ids are those of V3.0.35 (V3.0.30 .. V3.0.35 moved no ground-beam line: T-397 columns, T-399 one paint
line, T-400 fence lines). The V3.0.35 chain was not re-run here.

```
.work/venv/bin/python -I research/agents_t416/t416_extract.py "<private>/ST7757.dxf"      # REPRODUCED (input check)
.work/venv/bin/python -I research/agents_t416/t416_alsenan.py                              # REPRODUCED (summary check)
.work/venv/bin/python -I research/agents_t416/t416_alsenan.py --freelancer "<private>/<workbook>.xlsx" --out <checkout>/.work/private/t416
```

Files: `t416_rules.py` (R-T416-1 .. 5, pure), `t416_extract.py` (own DXF read by handle, values only),
`t416_alsenan.py`, `ALSENAN_T416_INPUT.json` (44 bands: handles, lengths in m, cut positions along each band; no
coordinate), `summary_t416.json`; tests `tests/t416_gb_length` (19).

## 1. The physical element (ERS s.2.1)

A ground beam is b x D x L of its own concrete between the faces of what it frames into. At a column the neck runs from
the footing to the beam top (route G NECK_TOP = the ground-beam top, T-200; R-CONC-OWN-1): the joint is the neck's
concrete, never the beam's. Where two beams cross, the square is one solid, owned once. Footings and straps lie below
the beam soffit (exterior main house soffit +-0.00, highest foundation top -0.80, T-253 / T-407; interior beams D 0.30 ..
0.60 under the +0.95 top): their plan overlap with a beam band is not a beam deduction (0 shared volume). The beam's
own length is therefore NET = (where both face lines are drawn) - (necks, S-BW rings and crossing squares it passes).

## 2. Own read (acceptance a; `t416_extract.py`)

- BAND = two parallel layer-1 face lines of the GROUND BEAMS PLAN 150 .. 450 mm apart with no line between, over
  their common interval (DRAWN length on the centreline); arcs 157 / 158 and 139 / 13A on the centreline radius over
  the common sweep. 44 bands: X 19, Y 20, oblique 3 (17E / 17F, 180 / 181, 182 / 183), curved 2.
- Cuts on the centreline: S-COL.BON outlines (36 on GBP), S-BW rings, crossing squares (kept in the X band, R-T416-2).
- Frames (O-T407-1): the same neck on the FOUNDATION PLAN (p.2) and the COLUMN & AXIS PLAN (p.1), frames offset by one
  / two sheet pitches (checked on the S-BOUN plot outline); a column inside a band changes its cut, a column at a band
  end changes where the beam stops (near-face shift). GROUND FLOOR ROOF SLAB (p.4) draws the column above the slab: shown,
  never used (R-T416-3).
- Guard (R-T416-5): house band centrelines inside the GBP fence strip S-BOUN 7FE / 7FC / 810: **0.000 m**.
- Every one of the 58 engine lines is bound to exactly one drawn band (BINDING in `t416_alsenan.py`, T-289 run handles).

## 3. Run table (acceptance a; m; columns = GBP outlines cut inside the band, end = neck at a band end)

| Band (face handles) | Dir | Drawn | Necks inside (GBP) | Neck at end | Net GBP | Net FP / CAP | Net range | Engine lines (state) | Engine L |
|---|---|---|---|---|---|---|---|---|---|
| FC+7D0 (main S, plot line) | X | 18.870 | 200 0.301, 249 1.101, 251 0.501, 255 0.701 | 218 | 16.267 | 16.366 / 16.267 | **16.267 .. 16.366** | 0011.1 .. 0011.4 (V) | 16.270 |
| F8+7D4 (annex S) | X | 10.130 | 207 0.031, 20B 0.401 | 207 | 9.698 | 9.399 / 9.399 | **9.399 .. 9.698** | 0015 L-402dbe61 (H) | 10.130 |
| 170+7C3 (N) | X | 13.770 | 1E0 0.301, 1E4 0.601, 241 0.501 | 1DC | 12.367 | 12.367 / 12.367 | 12.367 | 0001.1 .. 0001.4 (V) | 12.370 |
| 184+7CF | X | 12.070 | 23C 0.601, 24D 0.801 | - | 10.668 | 10.668 / 10.668 | 10.668 | 0010.1 .. 0010.3 (H/V) | 10.670 |
| 109+7CB | Y | 12.900 | 1DC 0.200, 228 0.701, 234 0.501 | 1DC | 11.498 | 11.498 | 11.498 | 0006.1 .. 0006.3 (V) | 11.500 |
| FD+7E0 (main E, sea) | Y | 7.900 | 1FC 0.500, 200 0.500, 809 0.301 | - | 6.598 | 6.598 | 6.598 | 0026.1 L-9e28c701 (V) | 6.900 |
| 7DC+7DD | Y | 7.350 | **7F5 0.301** | 24D | 7.049 | 7.099 / 7.099 | 7.049 .. 7.099 | 0023 L-fe78ae28 (V) | 7.350 |
| 7E7+7E8 | Y | 7.350 | **7ED 0.301** | - | 7.049 | 7.049 | 7.049 | 0032 L-0e30aadb (V) | 7.350 |
| 177+7CD | X | 7.557 | 245 1.001 | - | 6.556 | 6.556 | 6.556 | 0008.1 (V), 0008.2 (H) | 6.557 |
| 136+7D5 (annex W, street) | Y | 6.400 | 204 0.401 | 207 | 6.000 | 5.899 / 5.899 | 5.899 .. 6.000 | 0016 L-4783c6e1 (H) | 6.400 |
| 13D+7D2 | X | 6.400 | 211 0.501 | 223 | 5.899 | 5.899 | 5.899 | 0013.2 L-d8b98b14 (H) | 5.800 |
| 137+138 | X | 3.100 | 204 0.301, 214 0.401 | - | 2.399 | 2.299 / 2.299 | 2.299 .. 2.399 | 0035 L-00465df9 (H) | 3.100 |
| ARC 157+158 (ring) | C | 6.287 | 17BA 0.301, 17BD 0.130 | - | 5.856 | 5.958 / 6.259 | **5.856 .. 6.259** | 0043 L-7076482d (V) | 6.287 |
| 31 other bands | | | | | net = engine L within 5 mm, except 107+7CE, ARC 139+13A and 17E+17F (s.4); all rows in `summary_t416.json` | | | | |

All 44 bands: NET 191.416 m (frame range **190.916 .. 191.970**), DRAWN 208.129, AXIS 217.335, GROSS 225.942; engine
194.289 m on the same 58 lines. By direction (X / Y / oblique / curved): net 91.572 / 86.853 / 5.329 / 7.662.

## 4. Engine vs drawn, band by band (acceptance b, c)

Engine length - own net = **+2.873 m** (frame range +2.319 .. +3.373), named:

| Kind | Bands (lines) | m | Effect on a value |
|---|---|---|---|
| VALUED line whose value runs through a drawn neck | 7DC+7DD (L-fe78ae28, 7F5), 7E7+7E8 (L-0e30aadb, 7ED): value length 7.350 vs net 7.049 (.. 7.099 FP) | 0.602 | **ENGINE_WRONG +0.045180 .. +0.054180 and +0.054180 m3** at the line's own D 0.60 (the joint is also in the neck lines 7F5 / 7ED, which run to the beam top) |
| HELD lines whose length field runs through necks | F8+7D4 0.4315, 137+138 0.701, 136+7D5 0.4005 | 1.533 | no value; the T-391 HELD term used these lengths (his section x 1.533 = 0.276 m3 of the -9.690 m3 named HELD is neck length) |
| VALUED lines whose length FIELD runs through necks but whose value is the net | FD+7E0 0.302 (value 1.881 = 6.60 x 0.30 x 0.95), 107+7CE 0.027, ring 0.431 (value length 6.1296 inside the frame range 5.856 .. 6.259) | 0.760 | none (length field only); the ring's value is a point inside a frame RANGE: R-T416-3 asks for the range |
| engine-only sliver beside neck 211 at the annex arc | BAND0013.1 L-be6708e0 (0.10 m, valued 0.009 m3) | 0.100 | UNRESOLVED (no drawn band carries it; neck 211 / arc square) |
| junction kept in the other band / oblique end | 13D+7D2 -0.099 (H), 17E+17F -0.040 (V, engine short 0.0048 m3) | -0.139 | ownership only / UNRESOLVED small read |
| 25 bands under 5 mm each | | 0.017 | rounding of the drawn ends |

**F-1 (a second consequence of 7F5 / 7ED, not adopted here).** With the neck as a support, the two clear spans of
each 7.35 m band are 3.5245 m: the p.13 class for spans under 5 m is 30 x 40, as the released T-141 span ledger
(7DC+7DD #1 / #2 P13-GB-LT5M, supports COL:24D / COL:7F5 / junction 177+7CD) and the T-242 hand ledger (one half
CALCULATED D 0.40, the half receiving 7E1+7E2 HELD by D-33) already print. The engine note reads 'clear 7.35 m -> H 0.6'
because route G does not see 7F5 / 7ED as supports. If the class follows the drawn supports, each line is 0.42294 m3
(3.5245 x 0.30 x 0.40) valued + one half HELD (D-33) instead of 1.323 m3; this is a section question for the Checker
and lane I (it moves no figure here).

## 5. The GB-MAIN length residual -3.007980 m3 (acceptance b; R-T416-4)

The other side bills one section 0.30 x 0.60 over two lump lengths (longitudinal + transverse) that together exceed
the engine's 194.289 m by 16.711 m (T-391). Restated exactly on the drawn readings of the same 44 bands:

| Term (engine - other, m3) | m3 | Class proposal |
|---|---|---|
| engine length beyond the drawn net, +0.18 x 2.873 m (s.4, band by band) | **+0.517122** (frame range +0.417 .. +0.607) | named per band: 0.108 ENGINE_WRONG (through neck, valued), 0.276 HELD length, 0.137 length-field only, 0.018 sliver UNRESOLVED, -0.025 ownership / small read, 0.003 rounding |
| the other side beyond the drawn net, -0.18 x 19.584 m | **-3.525102** | **BOUNDED_THROUGH_SUPPORTS**: his total lies between DRAWN 208.129 (the face lines run through the necks inside the bands) and AXIS 217.335 (+ half of each end support): his lumps include necks and crossing squares that the engine bills in the neck lines (R-CONC-OWN-1) and in the crossing beam. Allowance 34.526 m, used 19.584 m; beyond GROSS 0.000 m |
| UNRESOLVED (beyond every drawn reading) | **0.000000** | - |
| total | **-3.007980** | re-adds exactly |

Direction test (private step; which plan direction each of his lumps is, and which lump holds the oblique and curved
bands, is not printed in his rows, so all 8 assignments are placed): 4 of 8 place both lumps inside the drawn readings
(e.g. longitudinal = the Y bands with the oblique bands, transverse = the X bands with the curved ones: both lumps
between DRAWN and AXIS); the 4 others put one lump beyond the drawn GROSS of its direction (or short of its NET). So no assignment-free per-direction trace exists; the total test above is the one that holds for
every assignment. A per-run or per-support split from a lump is refused (R-T416-4).

**Verdict proposals.** The engine's face-to-face basis is right in kind (Q-61 C; the joint is the neck's): ENGINE_RIGHT on
the -3.525102 m3 (class BOUNDED_THROUGH_SUPPORTS: mechanism traced and bounded by the drawn allowance, the per-support
split not recoverable; never closed by its sign: it is closed by the drawn readings and stays a bound, not a point).
Whether his necks (one uniform height on every mark) stop under his beam or run through it decides RULE_DIFFERENCE (no double on his
side) vs a double on his side: not readable from his rows, the engine is right either way. ENGINE_WRONG +0.108360 m3 on
L-fe78ae28 / L-0e30aadb (through neck; at the FP face of 24D +0.099360). UNRESOLVED +0.018 sliver, -0.0048 oblique end.

## 6. Owner manual method and drawing-derived method side by side

| Item | Owner manual method | Drawing-derived (this task) | Candidate V3.0.35 | Freelancer |
|---|---|---|---|---|
| Beam length | Q-61 C member by member, face to face | NET of necks / rings / crossings, range over the neck frames: 190.916 .. 191.970 m | 194.289 m (length fields) | two lumps, 16.711 m more than the engine |
| Joint at a neck | (necks: route G to the beam top) | in the neck, never in the beam | in the neck, except 7F5 / 7ED (0.602 m inside two valued beams) | not separable from his lumps |
| Crossing square | once | once (X band keeps it) | once (T-230 ends) | not separable |
| Class of a span cut by a neck | p.13 by clear span | 3.5245 m spans -> 30 x 40 (F-1) | 7.35 m -> 30 x 60 | 0.60 everywhere |

## 7. Checker re-measure list

- FC+7D0: 18.870 - (200 0.301 + 249 1.101 + 251 0.501 + 255 0.701) = 16.266; FP: neck 218 0.40 wide (GBP 0.50), near face
  0.100 further west -> 16.366 (O-T407-1 16.27 .. 16.37 reproduced on the beam itself; GF roof-slab 16.466 not used).
- 7DC+7DD: face lines 7DC / 7DD 7.350 m common; S-COL.BON 7F5 0.30 x 0.30 on the centreline (FP 10F6, CAP 892 the same
  column; no column above on p.4) -> 7.049; value 1.323 = 7.35 x 0.30 x 0.60.
- 109+7CB: 12.900 - (1DC 0.200 + 228 0.701 + 234 0.501) = 11.498 = 4.40 + 4.40 + 2.70 (+0.002 ends).
- Ring 157 / 158: r 2.25 / 2.55, common sweep 150.086 deg, centreline r 2.40 -> 6.2866; 17BA cut 0.301 on GBP, absent
  on CAP -> range 5.856 .. 6.259.

## 8. Rules, tests, lessons row, lane I proposal

Rules R-T416-1 .. 5 (`t416_rules.py`; research, every villa). Tests `tests/t416_gb_length` (19): Villa V416 hand fixture
(band through a neck, end neck and crossing; NET 12.90 / DRAWN 13.20 / AXIS 13.90 / GROSS 14.60; lump 13.60 split
+0.018 / -0.126), mirror / order invariance, overlapping supports as a union; adverse: column deducted twice, junction
kept in two bands or none, one frame chosen without a reason, the above-slab frame as a neck frame, a band run counted in
two partitions, a per-support split of a lump, lump short of net / beyond gross named UNRESOLVED, missing length as 0,
mm as m, a support outside the band, width in mm; the Alsenan summary pins (58 lines bound once, guard 0.000 m, terms
re-add, no coordinate in the committed input).

Lessons-register row proposed (ERS s.7): | 2026-11-01 | GB-MAIN length -3.008 m3 stood UNEXPLAINED (T-391) and the
own strip total 193.758 m 'agreed' with the engine's 194.289 m while the two sets differed in membership (lift-ring
walls and an S-BW ring read as strips, a 3.25 m beam missing from an unclosed face) | a length was compared total vs
total on a polygon partition, never band by band on the drawn face lines with each support cut once and each frame
read | a ground-beam length is read per band on its two face lines, cut by every neck / ring / crossing once (the neck
owns the joint), as a RANGE over the frames that draw the neck; a lump length of the other side is placed between NET,
DRAWN, AXIS and GROSS of the same set and only the part beyond GROSS (or short of NET) is UNRESOLVED; a valued line
whose value runs through a drawn neck is ENGINE_WRONG by that length (every villa; provenance T-416) |
tests/t416_gb_length | PROPOSED |

Lane I proposal (no candidate line here): (1) L-fe78ae28 / L-0e30aadb value length 7.35 -> 7.049 (GBP; 7.099 at the FP
face of 24D for L-fe78ae28), -0.054180 m3 each at D 0.60, and the F-1 class question (D 0.40 by the drawn clear spans,
one half D-33 HELD) to the Checker; (2) the ring L-7076482d carried as the range 5.856 .. 6.259 m (frames differ at
17BA / 17BD), not the point 6.1296; (3) the three HELD exterior annex lines' length fields restated net of their necks
(F8+7D4 9.399 .. 9.698, 137+138 2.299 .. 2.399, 136+7D5 5.899 .. 6.000), which also restates the T-391 HELD term by
+0.276 m3 at the other side's section and the length term by the same amount the other way (sum unchanged).

## 9. Not done / uncertain

- The V3.0.35 chain was not re-run; the 58 ids and figures are V3.0.29's (no ground-beam move to V3.0.35 per the merged
  statements).
- End supports of the curved and oblique bands are not walked (their AXIS / GROSS = DRAWN): the allowance is a lower
  bound there.
- The 7C5 / 7C6 S-BW ring and the lift-ring wall strips (0.20) that T-391 counted as beam strips are not ground beams
  here; what 7C5 / 7C6 is was not identified (no ground-beam line binds to it).
- BAND0013.1 (0.10 m) not located beyond 'beside neck 211 at the annex arc'.
