# T-426 Ground-beam section class per run: the printed section of every run against the candidate line that bills it

Worker 3 (cross-lane, lane S row; lane I had no claimable row), 2026-11-01 UTC, run session_01E6cPndFUxsHAik8KkoJFng,
branch `agents/task-T-426`. Research only: no engine, candidate, released line, rule or method version changed; nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Owner rules: Q-61 C
(member by member, face to face), UP-QTY-STATUS-001, no-assumptions rule; register ruling GF LIFT TIE BEAM (a section is
never borrowed).

## 0. Sources and reproduction

Drive "Urban BOQ private data / Alsenan chalet project" (read-only; decoded into `.work/private` only): 'ST7757 dxf.dxf'
(sha `9f9d1179`), 'ST7757.pdf' (sha `74da1523`, p.13 read as an image), 'P7757_DXF_COMPRESSED.zip' -> P7757.dxf
(`ab54dd55`, for the candidate run only).

```
.work/venv/bin/python -I research/agents_t426/t426_extract.py "<private>/ST7757.dxf"        # REPRODUCED (own read)
.work/venv/bin/python -I research/agents_t426/t426_alsenan.py                                # REPRODUCED (census)
# candidate extract (private run, values only):
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t246/v3036_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t246 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t426/t426_alsenan.py --candidate <private>/t246/v3036/V3_0_36_BOQ_LINES.json \
    --downgrades .work/board/docs/agents/verdicts/V3.0.29/DOWNGRADES.json --write-candidate
```

Files: `t426_rules.py` (R-T426-1 .. 5, pure), `t426_spans.py` (run spans per frame from the merged T-416 band read, exact
cuts), `t426_extract.py` (own DXF read: section-mark census, supports beside the F-1 bands), `t426_alsenan.py`,
`ALSENAN_T426_READ.json` (counts, handles, along-band lengths and gaps in m; no coordinate, no drawing text),
`CANDIDATE_V3036_GB_LINES.json` (58 lines: id, state, b, D, L, value), `CENSUS_T426.json` / `CENSUS_T426.csv`;
tests `tests/t426_gb_section` (19).

Candidate of record reproduced here: V3_0_36_BOQ_LINES.json **sha `d462203f`** (and V3.0.35 `b011bace`, both = the
Checker's T-246 Gate B files), 59 STR.CONC.GROUND_BEAM lines: the 58 T-416 bound once + the boundary-wall G.B at N.G.
(T-254 line, HELD 0 .. 3.5256 m3 at 0.20 x 0.40 = the p.14 printed section: AGREE, not a run of the house network).
Joined V3.0.29/DOWNGRADES.json (sha `4ed94bf4`) with the export's own T-294 content check: DG-a31a0d7e9dd564ad holds 9
ground-beam lines, binding CURRENT on V3.0.36 (their content unchanged), so they are HELD here although the line file
values them; no other record in force names a ground-beam line.

## 1. The physical element (ERS s.2.1)

A ground-beam run is b x D x L of its own concrete between the faces of what supports it (founded neck / column, S-BW
ring, the face of the band it ends against). Its SECTION is what the drawings print for that run; it depends on the
run's own position (interior / exterior / court, T-242) and, for an interior run, on its own clear span. A beam landing
between the faces does not split the run (T-141) but it is a concentrated load (D-33).

## 2. What the drawings print for a section (own read)

- **GROUND BEAMS PLAN (p.3): no section mark on any run.** Own census of the 85 texts in the frame (model space + the
  blocks inserted there): 36 column / neck marks, 20 levels, 4 slab tag / bar callouts, 2 load tags, 2 titles / scale,
  21 others (plot-side labels, pool, court, title script); **0 section marks** (no 'b x h', 'G.B', 'GBn', 'TBn', 'Bn',
  'SECTION'). `ALSENAN_T426_READ.json` `gbp_text_census`.
- **ST p.13 (image read): four ground-beam sections and nothing else.** 'More than 5m length / without concentrated
  load' 30 x 60; 'Less than 5m length / without concentrated load' 30 x 40; 'Less than 2.5m length' 30 x 30 (**no load
  qualifier printed under this one**, new); 'for exterior walls' 30 x 'FOLLOW ARCH.' from 'Ground Floor slab level' to
  'Outer Normal ground level'. No schedule assigns a section to a run.
- So the printed section of a run is: interior -> the p.13 title(s) that hold on its own clear span (R-T426-1 .. 3);
  exterior main house -> 30 x 0.95 (two levels: +0.95 / +-0.00, T-253 MERGED, the T-289 Checker-verified basis); annex
  exterior -> no printed depth (D-35 source CONFLICT); court -> no printed section.

## 3. Clear spans per run, frame by frame (acceptance: table per run)

From the merged T-416 band read (Gate A b7bb914a; geometry reused with that citation, WORKFLOW_CONTROLS s.10.5), with
the Checker's F-C-T416-1 applied (cuts exact, the 0.5 mm buffer removed): a run = a band segment between splitting cuts
(neck / column of the frame read, S-BW ring, the junction square at the band's own end); a junction mid-band never
splits; the end-column shift of FP / CAP (O-T407-1) moves the end segment; GFRS never used (R-T416-3). Result: **all 32
interior runs reproduce the T-242 face-to-face lengths on the GBP frame** (31 within 0.5 mm; 17E+17F#1 2.4668 vs 2.4269,
the oblique end T-416 already named, both < 2.5). Frames differ only at 7DC+7DD#1 (GBP 3.525, FP / CAP 3.575: neck 24D
drawn 50 mm further) and on exterior / annex runs (no interior class): **no interior run changes title between frames.**
One run changes title between READINGS: 177+7CD#1 5.020 (band end / lift-ring end) vs 4.970 (face of column 1EC, which
stands 0.050 m beside the band face on GBP, FP and CAP alike, own read): GT5M vs LT5M (T-141 GAP_TO_COLUMN).

## 4. Census: 58 candidate lines (acceptance: mark, b x h printed, b x h used, length, m3 delta)

Full table: `CENSUS_T426.csv` (one row per line x run). Summary on V3.0.36 + the V3.0.29 downgrades (every line id,
state, depth and value equal to the T-416 V3.0.29 binding; the depth derived from value / plan within 0.5 mm):

| Verdict (R-T426-4) | Lines | Candidate value m3 | Section m3 at stake (used - printed) |
|---|---|---|---|
| AGREE (printed b x D = used b x D on every run) | 30 (16 exterior main at 0.95 incl. ring; 14 interior) | 22.914555 | 0 |
| **DIFFERS** | **2**: L-fe78ae28 (7DC+7DD), L-0e30aadb (7E7+7E8) | 2.646 | **+0.846** (+0.423 each) |
| INSIDE_RANGE (used = one end of a printed range) | 5: 4 under 2.5 m at 0.40 (D-34: 0.30 .. 0.40), L-e24946df 177+7CD#1 at 0.60 (0.40 .. 0.60, reading) | 2.055831 | 0 .. +0.589257 |
| NO_PRINTED_SECTION but valued | 1: L-be6708e0 (0.10 m sliver in the annex arc run, valued at 0.30) | 0.009 | not measurable (HELD) |
| HELD_LINE (no value) | 20 | - | none (never 0) |

Separately (R-T426-5): **14 of the 38 valued lines (8.977106 m3) bill a run that another beam lands on (D-33)**; their
class is printed only 'without concentrated load'. The census does not move them (D-33 is a consultant item, T-242);
it names them so no section on them is read as VERIFIED.

### 4.1 F-1 answered from the drawing (T-416 Checker finding, not checked there)

| | 7DC+7DD (L-fe78ae28) | 7E7+7E8 (L-0e30aadb) |
|---|---|---|
| band (faces) | 7.350 m drawn, 0.300 wide | 7.350 m drawn, 0.300 wide |
| neck inside (GBP / FP / CAP) | 7F5 / 10F6 / 892 at 3.525 .. 3.825, cut by the centreline on all three | 7ED / 10EE / 88F at 3.525 .. 3.825, all three |
| neck founded | CN on FN (T-205 ledger, T-416 Checker) | CN on FN (same) |
| run #1 | 24D face -> 7F5: **3.525 GBP, 3.575 FP / CAP** -> LT5M -> 30 x 40; 7E1+7E2 lands at 2.772 .. 3.072 (D-33) | 7CF face -> 7ED: **3.525** all frames -> LT5M -> 30 x 40; nothing lands (T-242 CALCULATED, VERIFIED 0.4230) |
| run #2 | 7F5 -> 177 face: **3.525** all frames -> LT5M -> 30 x 40; nothing lands (T-242 CALCULATED, VERIFIED 0.4230) | 7ED -> 177 face: **3.525** -> LT5M -> 30 x 40; 114 / 7DF land at 5.800 .. 6.100 (D-33) |
| candidate | 0.30 x 0.60 x 7.35 = 1.323 ('clear 7.35 m -> H 0.6': route G does not see the neck as a support) | same 1.323 |
| section term (runs) | 0.30 x 7.05 x (0.60 - 0.40) = **+0.423** | **+0.423** |
| length term (T-416, not here) | 0.30 x 0.60 x 0.30 neck = 0.054 (ENGINE_WRONG, T-416) | 0.054 |

**F-1: the drawn class of both beams is 30 x 40 ('less than 5 m'), on every frame**; the frames differ (3.525 / 3.575)
but give the same title. Verdict proposal: **ENGINE_WRONG section** on the two unloaded halves (+0.2115 m3 each, own
read = T-242 VERIFIED 0.4230 per half); on the two loaded halves the unloaded class is printed but the section is
**HELD by D-33** (never the 0.60 of the whole band: that would be a section borrowed from the band's total length,
R-T426-1).

### 4.2 The other lines that are not AGREE

| Line | Run | Span (frames / readings) | Printed | Used | Stake m3 | Proposal |
|---|---|---|---|---|---|---|
| L-c0b7102a | 114+115+7DF#1 | 2.325 (all) | 30 x 30 .. 30 x 40 (D-34) | 30 x 40 | 0 .. +0.069750 | HELD range (D-34 open; a picked end of a range is not a printed value) |
| L-1487bdda | 142+7D8#1 | 2.450 | 30 x 30 .. 30 x 40 (D-34), loaded (D-33 on the 30 x 40 title only) | 30 x 40 | 0 .. +0.073500 | HELD range |
| L-0e852cca | 15C+7CC#1 | 2.400 | 30 x 30 .. 30 x 40 (D-34) | 30 x 40 | 0 .. +0.072000 | HELD range |
| L-0bb78acc | 17E+17F#1 | 2.4668 (T-242 2.4269) | 30 x 30 .. 30 x 40 (D-34), loaded | 30 x 40 | 0 .. +0.072807 | HELD range |
| L-e24946df | 177+7CD#1 | 5.020 band end / 4.970 column 1EC face | 30 x 40 .. 30 x 60, loaded | 30 x 60 | 0 .. +0.301200 | HELD range (reading + D-33) |
| L-be6708e0 | ARC:139+13A (annex exterior) | 0.10 m sliver | none (D-35 annex CONFLICT) | 30 x 30 | not measurable | HELD blank, never 0 (T-416 UNRESOLVED sliver) |

The 4 short runs: below 2.5 m both 'less than 2.5 m' and 'less than 5 m' hold literally (D-34, T-242 Checker-verified as
open); the candidate values the deeper one. No owner answer or rule picks the title (searched
OWNER_QUESTIONS_ANSWERED.md, DECISION_REGISTER.md, the downgrade records V3.0.16 .. V3.0.29: none names these lines).
**Finding F-T426-1 (asymmetric hold):** the Checker's D-34 record DG-a31a0d7e (V3.0.25, re-issued to V3.0.29) holds the 9
lines that show the 0.30 title ('the less than 5 m title also holds literally') and the 5.00 m line, but the same D-34
holds these 4 runs from the other side (0.40 shown, 0.30 also holds literally): 1.152231 m3 stay valued at the deeper
end of an unanswered pair. The record's own reason applies to them word for word with the titles swapped; nothing in
the record or the board says why they were left out (the issuing proposal DGP-T356-GB-D34 listed only 0.30 lines).

## 5. GB-MAIN headline restated with the section term (engine - freelancer, m3)

T-391 split GB-MAIN -10.354614 = section +2.343720 (exterior 0.95 vs his 0.60 +5.796522; interior 0.40 vs 0.60 -3.443815;
0.30 vs 0.60 -0.009; interior 0.60 runs 0.000 AGREE) + held -9.690354 + length -3.007980 (T-416: +0.517 engine beyond
the drawn net / -3.525 BOUNDED_THROUGH_SUPPORTS). On the candidate as it stands **no figure moves**; the census
re-classes the "interior 0.60 runs 0.000 AGREE" term: of its 4 lines, 7E1+7E2 (6.72 m, GT5M) agrees with the drawing;
**on 7DC+7DD and 7E7+7E8 (14.10 m of runs) the engine and the freelancer agree with each other at 0.60 but both are
above the printed 0.40**: +0.423 m3 ENGINE_WRONG (unloaded halves) and +0.423 m3 above the unloaded class on the D-33
halves; 177+7CD#1 sits inside its reading range (0 .. +0.3012). If lane I carries s.6 (1), GB-MAIN moves on the valued
side by -1.800 m3 (two lines 1.323 -> 0.423 each): section -0.423 (joins the ENGINE_RIGHT 0.40 term: -3.443815 ->
-3.866815), length -0.108 (T-416 necks), and 2 x 0.6345 = 1.269 m3 of his section moves into the HELD term (-9.690354
-> -10.959354); the unexplained part stays -3.007980 less the 0.108 neck term already named by T-416. Not measured: the
freelancer's own per-run section (two lumps, one section).

## 6. Proposals for lane I (no candidate line changed here)

1. L-fe78ae28 and L-0e30aadb: split by run at the neck (R-T426-1): the unloaded half valued 0.30 x 0.40 x 3.525 =
   0.4230 (T-242 VERIFIED component, own read agrees), the loaded half HELD by D-33 with the unloaded-class figure
   0.4230 beside (7DC+7DD#1 0.4230 .. 0.4290 over the FP / CAP frame 3.575), the neck length out (T-416, exact cut).
2. The 4 runs under 2.5 m and 177+7CD#1: HELD with the printed range beside, never the deeper end: the 4 short lines
   0.864171 .. 1.152231 m3 (valued today at the 1.152231 end); 177+7CD#1 0.5964 (4.97 x 0.30 x 0.40) .. 0.9036 (valued
   today at 5.02 x 0.30 x 0.60).
3. L-be6708e0: blank (no printed section), the sliver's ownership as T-416 left it (UNRESOLVED).
4. Route G should read a founded neck cut by a band as a support for the CLASS (it already cuts it for nothing): the
   'clear 7.35 m' note is the defect (every villa).

## 7. Rules, tests, lessons row

Rules R-T426-1 .. 5 (`t426_rules.py`; research, every villa). Tests `tests/t426_gb_section` (19): Villa V426 hand
fixture (8.00 m band split by a neck into 3.85 + 3.85 -> 0.40, line at 0.60 DIFFERS 0.462 m3; frames 4.98 / 5.03 RANGE;
2.00 m D-34 range; exactly 5.000 ON_LIMIT; exterior by levels AGREE / DIFFERS -0.495; mirror, end-frame shift, run order
invariance; a depth derived within 0.5 mm is the printed depth); adverse: section borrowed from the band refused, held line never valued 0, no printed section never 0,
missing span, mm as m, exterior depth in mm, unknown position, one frame chosen; Alsenan pins (census reproduces from
committed inputs, 58 lines once, 0 section marks, the two DIFFERS lines at +0.423, held lines have no stake, no
coordinate in the committed read, the candidate is V3.0.36 d462203f, the 9 DG-a31a0d7e lines HELD).

Lessons-register row proposed (ERS s.7): | 2026-11-01 | Two valued ground beams (7DC+7DD, 7E7+7E8) carried 30 x 60
over 7.35 m while the drawn neck in each splits it into two 3.525 m spans printed 30 x 40; T-242 had the halves right
(one VERIFIED each) but the candidate line kept the band's class | the class was read on the band's total ('clear 7.35
m') because the route does not treat a founded neck inside a band as a support; no check compared each line's depth with
the printed section of each run it bills | a ground-beam section is read per RUN from that run's own clear span between
drawn supports, frame by frame and reading by reading, never from the band or the neighbour; a line billing several
runs carries each run's printed section; a picked end of a printed range is HELD, not a value (every villa; provenance
T-426) | tests/t426_gb_section | PROPOSED |

## 8. Not done / uncertain

- The census binds the lines to runs through the merged T-289 pairing and the T-416 binding; three oblique lines have
  no T-289 pairing and are bound by their band's own run (17E+17F#1, 180+181#1, 182+183#1), as T-416 did.
- D-33 (a beam landing on a run) and D-34 (title below 2.5 m) stay consultant items; this census only states which runs
  they hold. The < 2.5 m title prints no load qualifier (own read): D-33 does not hold the 30 x 30 reading of a loaded
  short run, but D-34 still keeps 30 x 40 open beside it.
- Annex exterior depth (D-35) and the court runs: no printed section; no figure here.
- The freelancer's section per run is not recoverable (one section over two lumps): the s.5 restatement is on the
  engine side only.
