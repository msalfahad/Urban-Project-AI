# T-694 Concrete reconciliation statement round 3 (V3.0.68; concrete = V3.0.67) + the T-689 register gaps

Worker 1 (lane S), 2026-11-11, branch `agents/task-T-694`. Research only: no engine module, candidate line, rule or
knowledge version file, key map or released default changed; nothing released; no quantity changed. Development villa,
not an accuracy claim. Rules R-T679-1 / R-T683-1 (unchanged) + R-T694-1 .. -4 1.0.0 (`t694_rules.py`). Full tables:
`out/T694_STATEMENT.md` / `.json`. Drawings cited by Drive folder / title and DXF handle; no coordinate committed.

## 0. Inputs and runs

- Candidate of record V3.0.68 (T-672, `research/agents_t672/out/LINE_INDEX_V3_0_68.json`, lines d1de50cb); asserted:
  its 597 STR.CONC lines are identical to V3.0.67 (T-682), so concrete = V3.0.67. Master 1.69.0: census agrees on all
  14 concrete families (counts, sums, held / blank / excluded / verified, family by family).
- Causes: the T-683 statement (V3.0.66, Checker-passed) + R-T683-1 against the four wiring packages (T-668 / T-671 /
  T-677 / T-682); every wired HELD line's index bound equals its package after-state (checked line by line).
- OWN READ this run of Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (3,153,037 B, sha256 9f9d1179 = manifest),
  decoded into `.work/private` only: `t694_extract.py` -> `out/T694_OWN_READ.json` (values, relative offsets only).
- `t694_alsenan.py --write` / `--check`; tests `tests/t694_concrete_statement` (31).

## 1. (a) Component -> line -> family -> trade on V3.0.68 (m3; buckets never summed together)

R-T694-1 partition of all 597 STR.CONC lines: RELEASED 317 / HELD bounded 110 / HELD blank 80 / EXCLUDED 90; each
line in exactly one bucket (the test fails on a line in none or two).

| Bucket | V3.0.66 (T-683) | V3.0.68 (candidate of record) | After T-693 (PROPOSED, T-689 ledger) |
|---|---|---|---|
| Released | 317 / 291.476251 | 317 / **291.476251** | 317 / 291.476251 |
| HELD bounded | 101 / 42.014281 .. 66.193191 | 110 / **43.044431 .. 67.603665** | 115 / 44.452911 .. 69.834915 |
| HELD blank | 89 (11 MEASURABLE NOW) | **80** (DESIGNER 64, OPEN BOUND 16, MEASURABLE NOW 0) | 75 |
| Engine range | 333.490532 .. OPEN | **334.520682 .. OPEN** | 335.929162 .. OPEN |

Before -> after by line id: 9 lines moved blank -> bounded (7 lintels, PC-2F, annex C3), low +1.030150 and high
+1.410474 m3, exact (= T-682: LINTEL +0.436 / +0.554224, COLUMN +0.59415 / +0.85625); no released line moved; 2
lintels (D-1F-06, D-GF-04) stay blank with floors beside 0.036 / 0.048 (floors total 1.467046 m3, never in the range).
Family changes: B9-02 lintels bounded 24 / 1.361 .. 2.050636, blank 21; B10-06 columns bounded 22 / 10.26435 ..
13.27025, blank 7. Every other family as on V3.0.66.

R-T683-1 restatement: the 11 lines T-682 wired still carried T-683's 'MEASURABLE NOW' (= wire it). Restated with the
residual cause: 7 bounded lintels DESIGNER ITEM (cast length between 0.40 bearing and the drawn ceilings, T-516 RFI;
4 door lintels' existence on Q-55 C 2.20, ASSUMED - OWNER-APPROVED), 2 LOWER_ONLY lintels OPEN BOUND (an end with no
stopper, R-T678-3), PC-2F DESIGNER ITEM (section, s.3; top D-39), annex C3 DESIGNER ITEM (top datum D-39 only, s.4).

PROPOSED column (R-T694-2, labelled, never the candidate): the T-689 ledger's 6 moves applied to V3.0.68: L-919a5749
low 0.303 -> 0.3287 (B8 joint) and 5 blank column lines bounded 1.382780 .. 2.231250. Columns become 27 bounded
11.67283 .. 15.50150, 2 blank. It becomes the candidate only when T-693 wires it and the Checker passes Gate B.

## 2. (b) Freelancer reference comparison, kept apart (key map T001B; % only where the key holds no HELD line)

| Key | Ref m3 | Engine released | Engine range V3.0.68 | After T-693 (PROPOSED) | Ref - released | % |
|---|---|---|---|---|---|---|
| CONC.SLAB | 59.8174 | 60.280155 | 60.280155 (all released, 62 / 62 VERIFIED) | same | -0.462755 | **-0.77** |
| CONC.BEAM | 65.965875 | 66.920678 | 72.903907 .. OPEN | same | -0.954803 | suppressed |
| CONC.COLUMN | 39.7515 | 19.7765 | 38.81325 .. OPEN | 40.22173 .. OPEN | 19.975 | suppressed |
| CONC.FOOTING / GROUND / BLINDING / STAIR_DOME / POOL | | | unchanged from T-683 | same | | suppressed |

- SLAB -0.77 %: UNRESOLVED (ambiguous scope), residual named: GF +0.050478 / 1F -0.556333 / 2F +0.043100 (T-683). 1F
  (T-688, merged): engine = own drawing re-measure on every panel (ENGINE_RIGHT on geometry), his typed 120 m2 rounding
  -0.080 .. +0.080, drawn panels outside his 120 -0.636333 .. -0.476333 UNRESOLVED (62 panel subsets fit; none named).
  2F: thickness-zone split (0.16: 31.25 vs 31.84 m2; 0.18: 13.635 vs 13.35 m2), not investigated.
- BEAM: his cover 65.965875 drops his own first 1F row 0.20 x 0.40 x 1.60 = 0.128 (R-T683-3); his rows 66.093875.
  Cover - released -0.954803, rows - released -0.826803; % suppressed (26 HELD beam lines).
- COLUMN: the engine range now reaches above his cover only with the PROPOSED column (lower end 40.22173 > 39.7515):
  not agreement and not a verdict; the key's scope bridge (T-683: lift walls 2.4 / necks 8.805 / columns 28.5465) and
  the 0.75 lift-ring SCOPE_DOUBLE (ENGINE_RIGHT) stand.

## 3. (c) PC-2F section: what the drawings print (R-T694-3, new)

Physical element: the planted column PC-2F starts on beam B19 at the 1F roof slab top +9.65 and rises to the B7 soffit
(T-220). Its section is drawn 0.20 x 0.40 on FFRS 77B (ANSI35 hatch: starts here) and SFRS 778 (solid). Own read this
run of every 'P.C' text of the ST DXF: there are three, 544 'P.C 20x70', 548 'P.C 20x50', 77C 'P.C 20x50', each with
a 3-vertex leader on S-TEXT-SLAB. The leader far ends are 311 / 311 / **298 mm** from outlines 329 / 386 / **77B**
(next outline 1,059 / 939 / 2,652 mm). So 77C belongs to 77B (DRAWING-CONFIRMED association), NOT to 67C, the 1F C2
outline 0.20 x 0.50 that sits **348 mm** from the text itself. For all three texts the outline nearest the text is the
wrong one (359, 371, 67C): a nearest-text rule would mis-assign every P.C; R-T694-3 makes the leader govern.

Searched for a print that fixes the section: no dimension and no size text within 0.60 m of 77B / 778 (only slab bar
texts 709 '5ø10/m', 7A2 '5ø18/Top'); no 'PLANT' / 'CARRYING' text in the DXF; T-220 (merged): ST p.15 'beam carrying
planted col.' detail is generic (no size), no schedule row for P.C; T-217 / T-256 (Checker-verified): p.9 schedule,
slab plans, sections A-A .. D-D, PDF plot = copy. Result: the drawn outline (0.08 m2, two sheets) and the member's own
text (0.10 m2) disagree and no third print exists. **DESIGNER ITEM: proposed addition to D-66** ("which section is
built: drawn 0.20 x 0.40 or text 'P.C 20x50'"). Quantity: 0.08 .. 0.10 m2 x 2.28 .. 3.50 m, already inside
L-541c7e56 0.1824 .. 0.35 m3; nothing moves. Named, not used: 548 and 77C print the identical pair 'P.C 20x50' /
'8ø16' (a copied label is one possible origin; not evidence).

## 4. (d) The 5 lines absent from D-66 (R-T694-4, new) + one spurious cause

| Line | Outline (drawn) | Schedule | Own read this run: size texts / dims within 0.60 m | Cause |
|---|---|---|---|---|
| L-9f5a6470 / L-c0b3340a / L-e6c1c9a7 | GFRS 34A / 34D / 356, 0.20 x 0.40 | C GR 20 x 50 | 0 / 0 (no text at all) | DESIGNER: add to D-66 |
| L-694a75c8 | GFRS 350, 0.20 x 0.40 | C3 GR 25 x 50 | 0 / 0 (no text at all) | DESIGNER: add to D-66 |
| L-bc01297b | SFRS 415, 0.60 x 0.20 | C5 2ND 20 x 50 | 0 / 0 (79F '4ø16/Top' slab bar, 434 mm) | DESIGNER: add to D-66 |

No measurable cause: the same D-66 search standard (0 size texts / dimensions within 0.60 m; schedule vs outline
CONFLICT T-217) finds no third print for any of the five. Each is added to D-66 on the board as a PROPOSED addition
(T-694), with its handle, for the Lead's consultant pack. **F-T694-2 (spurious cause):** T-689 lists L-fad18af6
(annex C3, GFRS 353) with a D-66 SECTION cause, but its outline 0.25 x 0.50 agrees with the schedule C3 GR 25 x 50
(T-566 registration AGREE) and its bound 0.125 x 3.294 .. 0.125 x 4.05 uses one section: the cause is top datum only
(D-39 / Q-54 B). No quantity moves; the cause record is corrected in this statement.

## 5. Methods side by side (ERS s.2.2)

Owner manual method: member by member, a section conflict is held with both readings and a designer request (Q-61 C,
X6); a missing datum is held. Drawing-derived: the same holds; this run adds only which outline a printed text belongs
to (by its leader). Both methods give identical quantities here. Freelancer: not used for any bound.

## 6. Verdict proposals

- PC-2F section: UNRESOLVED -> designer (D-66 addition); association 77C -> 77B: DRAWING-CONFIRMED (Checker item 1).
- 5 column lines: UNRESOLVED -> designer (D-66 additions).
- L-fad18af6 cause: corrected to D-39 only (Checker may re-read GFRS 353).
- SLAB -0.77 %: UNRESOLVED (scope), ENGINE_RIGHT on geometry (T-688). BEAM: reference arithmetic (-0.128 his).
- No owner question: ERS 2.7 not met (designer items; no owner method / contract decision).

## 7. Checker re-measure list (3 lines not re-measured before)

1. L-541c7e56: text 77C + leader 77F far end 298 mm from 77B (0.20 x 0.40); text 348 mm from 67C; 544 / 545 -> 329
   and 548 / 549 -> 386 at 311 mm.
2. L-bc01297b: SFRS 415 0.60 x 0.20; no size text / dimension within 0.60 m.
3. L-694a75c8: GFRS 350 0.40 x 0.20 vs schedule C3 GR 25 x 50; nothing printed within 0.60 m.

## 8. Lessons rows (ERS s.7, PROPOSED)

| 2026-11-11 | a member text was carried against an outline 2.8 m away while another outline sat 0.35 m from the text, with no
recorded reason | the leader decides; on this set the outline nearest every P.C text is the wrong one | R-T694-3 (leader
governs; no leader and two outlines within tolerance = UNRESOLVED) | tests/t694_concrete_statement |
| 2026-11-11 | a SECTION cause was cited on a column whose outline and schedule agree | a spurious cause hides the real
one (top datum) and misdirects the designer list | R-T694-4 (a SECTION cause needs two differing readings; every cited
item must list the member) | tests/t694_concrete_statement |
