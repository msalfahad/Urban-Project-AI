# T-376 Designer RFI rows for the rebar shape and lap gaps left open by T-366 / T-371 (development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPndQUxSmqyKp4KvbtAc, branch `agents/task-T-376`. Research
files only: proposed RFI rows as TEXT for the Lead, who applies them to `docs/agents/rfi/B_REMAINING_RFI.md` (the worker
never edits the rfi files). NOTHING IS SENT (owner 2026-10-29 22:05). No kg, length or count is computed; no candidate
line, rule, method or released quantity changes. Drawings named by Drive folder and title only.

## 0. Sources

- Merged ledgers (read only): T-371 `research/agents_t371/ALSENAN_BAR_SHAPE_INPUT.json` + `LINE_BINDING_T371.json`
  (38 shape populations, gaps G-T371-0 .. 7, findings F-T371-1 .. 4); T-366 `research/agents_t366/
  ALSENAN_LAP_AUTHORITY_INPUT.json` (27 lap populations, sheets searched with DXF handles, printed sources N9 / P13D40 /
  P15N1, findings F-T366-1 .. 5, designer items s.7); T-373 `research/agents_t373/T373_LAP_BINDING.csv` (the 351 lines of
  DGP-T373-LAP); T-273 r2 `research/agents_t273/T-273_LAPS_AND_TONNES.md` s.9.2 (starter projection kg).
- Candidate: ARCH_TAKEOFF_V3.0.27 projected without private data = merged T-297 extract of V3.0.16 (sha256 2f28367b..,
  2,505 reinforcement lines, ids stable) + merged T-318 slab bar-end inputs read through the engine's own
  `arch_v3027.load_inputs` (read only): 2,505 + 138 part lines = **2,643** = T-373's count of the reproduced V3.0.27
  (the same projection T-373's test proves equal to the reproduced file). Part lines are named by their engine element
  id `<parent>#SLAB_BAR_ENDS:VALUED` (their hash line id needs the private revision set); in `T376_LINE_UNLOCK.csv` they
  carry `<parent line id>#PART`. DGP-T373-LAP membership marked per line (V3.0.28 contractual view: HELD, UNSUPPORTED
  BASIS; range = audit only).
- Drawing cross-check this run (rule 2): Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523.., the file
  T-366 / T-371 read), decoded by the wrapper into the private folder only; p.13 rendered at 150 dpi, p.15 at 150 / 400
  dpi, read by eye. Confirmed: p.13 both TYP. DETAIL OF ISOLATED FOOTING print 'Min. 30cm' (starter foot) and 'Max.
  10cm'; the right-hand detail (LESS THAN 2.5m) dimensions '40 ø' from the footing top up the column; 'Boxed bars' drawn
  as an inverted U with diagonal marks at the two upper corners, legs down towards the mesh, no diameter or level; the
  exterior-walls G.B section draws an unlabelled X between its '2ø12/30cm' side bars; the G.B sections draw short
  verticals from the second bottom layer (unlabelled). p.15: TYP. SLAB ON BEAMS DETAIL, at the non-continuous support the
  TOP ANCHOR BAR turns down at the outer face and its leg ends BELOW the slab soffit inside the edge beam (F-T371-1,
  agreed), '40 CL.' printed at the face, no leg dimension; TEMPERATURE REINFORCEMENT SCHEDULE rows 100 / 125 / 150 / 175 /
  200 / 250 / 300, no 160 (agreed with T-366); NOTE 1 'LAP LENGHT FOR ALL TEMPERATUERE BARS SHALL BE 40xDIA'; TYP. DETAIL
  OF TWISTED COLUMN 'Spiral Stirrups 6ø8/m', '4ø16 EXTRA', no spiral diameter or end turn. No disagreement with the
  merged ledgers found.

Tool: `t376_rfi_rows.py` (DESIGNER_RFI_ROWS_V1, stdlib + the engine's read-only `arch_v3027.load_inputs`) ->
`T376_RFI_ROWS.csv` (16 rows), `T376_LINE_UNLOCK.csv` (one row per row x line), `T376_SUMMARY.json`. Repeat:
`python3 -I research/agents_t376/t376_rfi_rows.py`. Tests `tests/t376_rfi_rows` (16).

## 1. Engineering question and method (ERS s.2.7 / s.6)

Each open item is a designer fact the issued drawings do not print, or a conflict between two printed documents of the
same set; none is an owner decision (no Q- question). One question per fact; the question asks for the drawing
information only, never our convention (owner option B 2026-10-29 keeps counting only drawn parts meanwhile). Every
row carries: the sheets / details where the search ended, each citation resolved by the tool against the merged
T-366 / T-371 ledgers (a row with no resolvable citation, a quote or DXF handle the ledger does not carry, or a state
the census did not give is refused); the bar populations and the V3.0.27 lines it unlocks; the kg now on those lines
(valued low .. high, BLANK lines counted, never 0); and the kg the answer governs: a merged ledger range, the lines' own
range, or HELD unquantified with the reason. "Unlocks" means the answer is one of the inputs a line needs; a line
closes only through a task and a Checker verdict, and most lines need several answers (column `joint`).

## 2. The proposed rows (acceptance (a))

| Row | RFI | Gap | Lines V3.0.27 (valued / BLANK) | kg now on them | kg the answer governs | DGP-T373-LAP lines |
|---|---|---|---|---|---|---|
| R01 | RFI-B-S21 (d) bend diameter / hook extension, all marks | G-T371-0, F-T371-3 | 1,972 (922 / 1,050) | 14,374.406 .. 18,331.921 | HELD, unquantified (cutting length of every bent shape; hook tails undimensioned) | 264 |
| R02 | RFI-B-S21 (e) link closure, every link class | G-T371-3 (links) | 515 (193 / 322) | 3,105.815 .. 3,990.402 | HELD, unquantified (lines book the perimeter only, 'hooks not printed') | 0 |
| R03 | **RFI-B-S29** NEW column head and section change | G-T371-3 (columns) | 90 (0 / 90) | BLANK | HELD, unquantified | 0 |
| R04 | **RFI-B-S30** NEW footing boxed bars | G-T371-1 = F-T371-4 | 20 (0 / 20) | BLANK | HELD, unquantified | 0 |
| R05 | **RFI-B-S31 (a) (b)** NEW starter foot, up-bend, deep-detail cranks | G-T371-2 | 28 (0 / 28) | BLANK | HELD, unquantified (30 cm is a minimum only) | 0 |
| R06 | **RFI-B-S31 (c)** starter projection 40 ø vs note 9 | F-T366-1 | 28 (0 / 28) | BLANK | **278.836 .. 487.963** (T-273 r2 s.9.2: 40 D on 31 chains; +209.127 at 70 D; scenario, not in the candidate) | 0 |
| R07 | **RFI-B-S32** NEW lap length / splice zone: columns, ground beams, boundary G.B, slabs | T-366 item (1), F-T366-2 | 58 (58 / 0) | 517.818 .. 906.178 | **517.818 .. 906.178** (note-9 audit range the answer replaces) | 58 (DG-8afa33d5.., DG-aaabf79a..) |
| R08 | RFI-B-S21 (f) CB bottom overlap at interior supports | F-T366-3 | 29 (29 / 0) | 239.868 .. 419.769 | **239.868 .. 419.769** (joint with S21 (a): both ends on the same lines) | 29 (DG-30f59008..) |
| R09 | **RFI-B-S33** NEW twisted-column spiral | G-T371-4 | 2 (0 / 2) | BLANK | HELD, unquantified | 0 |
| R10 | **RFI-B-S34** NEW bars of projection bands / B20 - B23 upstands | G-T371-5 | 12 (0 / 12) | BLANK | HELD, unquantified (joint with A RFI-S18) | 0 |
| R11 | RFI-B-S09 (e) unlabelled G.B section marks | G-T371-6, F-T371-2 | 30 (0 / 30) | BLANK | HELD, unquantified (verticals: no line, never added) | 0 |
| R12 | RFI-B-S10 (e) slab bottom up-turn leg | G-T371-7 | 118 (59 parts / 59 parents) | 136.573 .. 150.695 (drawn straight parts) | HELD, unquantified (legs: option B) | 0 |
| R13 | RFI-B-S10 (f) slab top hook-down leg into the edge beam | F-T371-1 | 115 (56 / 59) | 429.268 .. 1,089.754 (valued top parts) | HELD, unquantified ('D less covers' refused for this leg) | 0 |
| R14 | RFI-B-S10 (g) corner / extra slab bars | G-T371-7 | 2 (0 / 2) | BLANK | HELD, unquantified | 0 |
| R15 | RFI-B-S10 (h) ground-slab mesh edges | G-T371-7 | 24 (24 / 0) | 1,064.240 | HELD, unquantified (edge legs add to the area x rate lines) | 0 |
| R16 | RFI-B-S10 (i) temperature bars of the 16 cm slabs | T-366 SLAB-TEMPERATURE | 3 (0 / 3) | BLANK | HELD, unquantified | 0 |

Units kg (t only at the export boundary). Distinct lines unlocked by at least one row: 2,116 of 2,643 (a line can
appear in several rows; the kg columns are per row and are NEVER added across rows). R12 / R13 select only the lines
whose T-318 held items name the leg (UPTURN_LEG / HOOK_DOWN_LEG) and their part lines. The four DGP-T373-LAP records
cover 87 of the unlocked lines in R07 / R08 and 264 in R01 (beam and GB bar ends), on V3.0.28.

### Text for the Lead to apply (each as the row asks; quantities stay internal, never sent)

**RFI-B-S21, add (d), (e), (f)** (and drop (c)'s beam-only link hook wording, now inside (e)):
- (d) Which bend (mandrel) diameter and which hook / bend extension apply to the bent bar marks (links, legs, cranks,
  spirals, starter feet), or which standard and edition governs them? No bend diameter, hook extension or bar-bending
  legend is printed (ST p.8 notes 1 - 24; DXF texts, only hit 1BA9 '* L=LENGTH OF COLUMN.').
- (e) How is each link closed (hook angle and extension, or overlap) for column links including the necks and the
  beam-column joints (ST p.9 DETAILS OF COLUMN REINFORCEMENT, 1BAA '6ø8/m'), ground-beam stirrups and strap links (ST
  p.13 G.B sections, p.10 SB rows), as for the beam links (ST p.15 slab-on-beams section)? Every section draws a closed
  link with an undimensioned corner tick.
- (f) On the continuous beams (ST p.11 / p.12 schedules 206B / 272B / 2035 and their typical span diagram), what is the
  overlap length of the bottom bars of two adjacent spans across an interior support? The overlap is drawn, not
  dimensioned.

**RFI-B-S29 (NEW) Column head and section change.** Drawing: ST p.9 column schedule (1B3A; size and bars per storey);
ST p.15 (no column-head detail). Missing: how the main bars end at the top of each column (roof) and what happens at a
section reduction between storeys. Requested: the column-head bar detail and the section-change detail (crank offset, or
new bars lapped), or the typical detail governing both.

**RFI-B-S30 (NEW) Footing boxed bars.** Drawing: ST p.9 footing schedule (1C32, BOXED column); ST p.13 both TYP. DETAIL
OF ISOLATED FOOTING ('Boxed bars': inverted U, legs towards the mesh, marks at the upper corners). Missing: diameter, leg
end level, the corner marks. Requested: the three, or a dimensioned boxed-bar detail. (Carries the T-171 / T-299
designer item that never reached rfi/: F-T371-4.)

**RFI-B-S31 (NEW) Starter bars.** Drawing: ST p.13 both TYP. DETAIL OF ISOLATED FOOTING; ST p.8 note 9 (Arabic, starter
bars 'اشاير': not less than 70 x dia in tension zones, 40 x dia in compression zones). (a) The foot is printed 'Min.
30cm': what is its length, and is its end bent up? (b) What are the crank offsets drawn in the deeper detail (upper G.B
more than 2.5 m above)? (c) The shallower detail (less than 2.5 m) dimensions the projection above the footing top as
'40 ø', note 9 asks at least 70 x dia in tension zones: which governs, and which of the two details applies to each
footing?

**RFI-B-S32 (NEW) Lap length and splice zones (members other than beams and planted columns).** Drawing: none prints a
lap for these bars (ST p.8 note 9 names starter bars; ST p.15 NOTE 1 names temperature bars only). Requested: lap length
and permitted splice zone for (a) column main bars at storey joints (bar count changes per storey, ST p.9), (b)
ground-beam main bars where a run exceeds the stock length (runs to 18.57 m), (c) the boundary-wall ground beam (ST p.14,
run 31.37 m), (d) slab bottom / top bars and the ground-slab mesh where spliced.

**RFI-B-S33 (NEW) Twisted-column spiral.** Drawing: ST p.15 TYP. DETAIL OF TWISTED COLUMN ('Spiral Stirrups 6ø8/m',
circle in plan). Requested: spiral diameter (or its cover) and the end turns / anchorage. ('6ø8/m' is read as a rate.)

**RFI-B-S34 (NEW) Bars of the projection bands and the B20 / B23 upstands.** Drawing: ST p.4 / p.5 roof slab plans; ST
p.10 schedule (1E47: no row). Requested: the bars of each section asked in A RFI-S18 (sent together with it).

**RFI-B-S09, add (e).** In the four ST p.13 ground-beam sections: what are the unlabelled X between the side bars of the
exterior-wall ground beam, and the short verticals from the second bottom layer to the bottom bars (bars or not;
diameter, spacing)?

**RFI-B-S10, add (e) - (i).** ST p.15 TYP. SLAB ON BEAMS DETAIL: (e) the length of the up-turned bottom-bar leg at a
non-continuous support ('40 CL.' from the outer face); (f) the length / end level of the top anchor bar's hook-down leg,
drawn passing below the slab soffit into the edge beam; (g) shape, length and layer of the corner bars ('Corner
Reinforcement', e.g. 12 ø14 on 1F) and of the second-bar zone bars (the GF-126 zone extent stays in S10 as asked); (h)
ST p.3: how the ground-slab mesh '5ø10/m E.W. T=10cm' ends at the ground beams; (i) the temperature bars of the 16 cm
slabs (the p.15 TEMPERATURE REINFORCEMENT SCHEDULE has no 160 mm row; NOTE 1 already prints their lap, 40 x dia).

New ids: proposed as the next free B structural numbers that do not collide with A's RFI-S01 .. S28; the Lead confirms.

## 3. Duplicates against rfi/A and rfi/B (acceptance (b))

| Row | Existing question checked | Verdict |
|---|---|---|
| R01 | B-S21 (beam link hook type and length) | different fact (bend diameter of every bent mark): added to S21, one reply |
| R02 | B-S21 (c) beam link hook; B-S20 nested links; A RFI-S11 '< 2.5 m link' size / spacing | SAME fact as S21 (c) for beams -> MERGED: S21's item widened to every link class, never asked twice; S20 / S11 different facts, kept |
| R03 | A RFI-S19 / S20 / S21 (column concrete); B-S12 (planted columns) | none asks a column head or section change: NEW |
| R04 | B-S09 (top-bar ends of F8 / F12 - F14 / FF) | different bars (cage end legs vs boxed bars): NEW |
| R05 | A RFI-S01 (founding level) | different fact (S01 fixes the vertical length, not the foot / cranks): NEW, joint dependency named |
| R06 | B-S09 / B-S21 (note 9 cited for ground-beam and beam ends) | neither asks the starters note 9 names: NEW |
| R07 | B-S21 (beam laps / note-9 scope); B-S12 (planted-column laps) | other members: NEW, kept apart; stock length not asked (owner-approved 12 m) |
| R08 | B-S21 (a) (end supports) | interior overlap is a separate drawn item: added to S21 |
| R09 | B-S22 (planted-column 4ø16, stair-beam crank) | different bar: NEW |
| R10 | A RFI-S18 (projection-band section) | S18 asks the concrete only: NEW, sent with S18 |
| R11 | B-S09 (bar ends); B-S19 ('2ø12/30cm' notation) | neither asks the marks: added to S09 |
| R12 - R16 | B-S10 (top-bar extent, bar-less panels, tank slab, GF-126 zone extent) | legs, corner-bar shape, ground-slab edges and temperature bars are different facts: added to S10; GF-126 extent NOT re-asked |

The tool refuses two rows with one fact, a row extending an RFI id that is in no RFI file, and a new id that already
exists (tests).

Not asked (no row), with reason: stock length (owner-approved fallback OD-V3-3, procurement not design); F-T366-2 beam
ends on note 9 (already B-S21 (a) / (b); 254 lines under DG-30f59008..); footing cage top-end legs and top mesh (B-S09);
ground-beam bar ends (B-S09); SB / CB bar ends and the CB top corner leg (B-S21; the bend is R01); nested links (B-S20);
beam side bars (B-S19); planted-column 4ø16 ends (B-S22); slab top-bar extent and bar-less panels (B-S10); pool / stair
/ tank bars (T-359 census).

## 4. C unlock matrix (acceptance (c))

No P-group row changes: none of P-1 .. P-9b is a reinforcement line and no row above closes a concrete line. The
paragraph "Lines with NO priority group" changes for reinforcement: "reinforcement (laps T-273 / T-366; bar shapes
T-371; designer items B-S09 (e), B-S10 (e) - (i), B-S21 (d) - (f), B-S29 .. B-S34)". No reinforcement line closes on one
answer: every bent shape also needs R01, and the four DGP-T373-LAP records stay until a lap authority is printed (R07 /
R08 / S21) or an owner rule is answered.

## 5. Engine vs freelancer; verdict proposals

No BOQ line moves (kg_computed 0, candidate_lines_changed 0). The freelancer's reinforcement is a kg/m3 lump (44.19 t)
with no shape, hook or lap row: RULE_DIFFERENCE, no %. Verdict proposals: every gap UNRESOLVED (designer); F-T366-1
CONFLICT between two printed documents (p.13 typical vs p.8 note 9), UNRESOLVED (designer).

## 6. Rule proposed (every villa; provenance T-376; a rule version only when adopted)

**R-RFI-BIND-1**: a designer RFI row is filed only with (i) at least one citation that resolves against a merged
evidence ledger (sheet / detail / handle, quoted), (ii) the populations and candidate line ids it unlocks with their kg
now (BLANK counted, never 0) and the kg the answer governs (ledger range, the lines' own range, or HELD unquantified
with its reason), (iii) a duplicate check against every open question by FACT, not by sheet; a fact already asked is
merged into the existing question, never asked twice.

## 7. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | Designer items found by the shape / lap censuses (boxed bars since T-171, starter 40 ø vs note 9, slab legs,
column heads) sat in task reports for days without an RFI row, and S21's beam-only link hook would have been asked a
second time for columns | items were carried as prose findings; RFI rows were written per sheet, not per fact | every
designer item leaves a row bound to its ledger citation and its unlocked lines, deduplicated by fact (R-RFI-BIND-1;
every villa; T-376) | tests/t376_rfi_rows (uncited row refused; handle / quote not in the ledger refused; one fact
twice refused; held range 0 refused) | PROPOSED |

## 8. Self-gate and not done

self-gate: a (real code + 16 tests), c (synthetic villa by hand: 7.25 .. 8.75 kg on 2 valued lines + 1 BLANK; adverse
cases), d (research files only, freeze 0), f (HELD BLANK everywhere, no kg computed, nothing released), h (every row's
lines bound by id; V3.0.27 projection = T-373's 2,643; DGP line kg equal the T-373 CSV on all 351) PASS. Not done: the
part-line hash ids of V3.0.27 (need the private revision set; the Checker maps them by element id); the rfi files are
not edited (Lead); the exact wording of note 9 was not re-read this run (T-366 and the Checker's 05:00 citation run
read it); no sheet other than p.13 / p.15 re-read this run.
