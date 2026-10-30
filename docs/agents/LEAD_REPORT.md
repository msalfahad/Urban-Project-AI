# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-10-30 16:30 UTC

Drive readable: nothing created or modified in the Urban BOQ private data folder or the Alsenan project folder since
30 Oct 12:00 (search empty; no photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6);
`.work` prepared by `status` (auto). Working branch 5bde82a7 -> 8f2b0354 (five Checker merges via 'engine push'); no
owner commit. Self-check: codemap PASS, pytest t061 PASS, freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since
your 29 Oct 22:05 review; nothing undone.

HEADLINE: five research pieces checked and merged, all first time on their round; the reveals package was sent back
for one isolated fault (three arched windows measured on their rectangle). The lap census exposed the most important
structural finding of the day: about 470 candidate rebar lines value a lap or development length from the starter-bar
note on bars that are not starters. That steel is valued on a borrowed basis; it is now bound line by line so the
Checker can move it to HELD with a downgrade-only record. No decision needed from you today beyond Q-78 (still open).

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; reinforcement
10,250.168 kg; whole verified lines in the candidate export 2, released 0; scored verified share CONCRETE 12.50 %
unchanged; candidate of record ARCH_TAKEOFF_V3.0.27, NOT RELEASED, unchanged since 11:35):
- REINFORCEMENT (kg; research, no line moved). LAP AUTHORITY (27 bar populations): only three printed sources, ST p.15
  NOTE 1 (40 x DIA, temperature bars), p.8 note 9 (starters >= 70 d tension / 40 d, zone never printed) and p.13
  typical footing '40 ø' starter projection, which CONFLICTS with note 9 (designer). 24 populations print none: 12
  laps HELD (column splices, ground-beam runs 18.57 / 13.77 m, boundary run 31.37 m, CB bottom overlap drawn
  undimensioned, slab mains), 12 not required. 12 m stock printed nowhere: ASSUMED - OWNER-APPROVED (OD-V3-3).
  F-T366-2: 470 candidate lines (beam ends 254, column storey laps 56, GB bar ends 62, slab development 98) use note 9
  outside its starter group: ENGINE_WRONG in basis, bounds only, none released. The frozen splice-count method gives 1
  instead of 2 laps on a 23.8 m run and 2 instead of 3 on a 35 m run at a 0.64 m lap (Checker's own hand runs agree):
  0.000 kg on Alsenan today because those laps are HELD, a real defect for any villa with a printed lap. BAR SHAPES
  (38 populations x 7 attributes, 2,505 lines bound): 7 schedulable now, all straight (442 lines); 10 after a named RFI
  (767); 19 GAP (1,150: bend diameter and hook extension printed nowhere, boxed footing bars, starter foot 'Min.
  30cm', link hooks, slab legs); 2 lap rows (58). The slab top hook-down leg is drawn INTO the edge beam, so the
  Checker's 'D less covers' bound applies to the bottom up-turn only (proposal, no value). POOL / STAIR / TANK
  DETAILS: 110 / 110 bar labels cited at r2; pool outer vertical 6ø12/m COUNTABLE AFTER RFI-B-S11; water-face bar
  printed d12 at one place and d14 on its shape (x1.36 kg/m on that population): CONFLICT, designer. Freelancer
  5,400 kg is one lump: RULE_DIFFERENCE, no %.
- REVEALS (m2; Gate B r1 REJECTED narrow 15:35): 67 / 70 changed or added lines agree with the Checker's own DXF depths
  (all 27 windows 0.08 / 0.10 m outside; 3,886 lines byte-identical; 4 / 4 hashes reproduced). W15 / W16 / W26 are
  arched: outside jambs + head booked 0.620 / 0.620 / 0.460 m2 on the band-crown rectangle vs 0.5477 / 0.5477 /
  0.4071 m2 on springing + developed arch (+13 %). ARCH.WINDOW_REVEAL 12.6364 -> about 12.4388 m2 after r2 (-0.20 m2,
  -1.6 %); FIN.PLASTER 580.5819 m2 unchanged. Freelancer has no reveal rows: RULE_DIFFERENCE.
- WALL TILE EDGES (m.l; merged 13:59 at r2): determinate 31.65 (was 38.95, -7.30, -18.7 %); finish 45-degree OR steel
  profile HELD on the 31.65, never summed; GF-14 edges and head arris HELD by name (the ST roof slab plan shows no beam
  under the HIDDEN pair; head printed nowhere). Freelancer 0 m.l: RULE_DIFFERENCE.
- FENCE / GATES (m.l, pcs; merged 15:37): street 8.30 = 5.80 fence + 2.50 opening with NO leaf drawn (leaf HELD); sea
  7.10 = 6.10 + 1.00 gate (leaf 0.90 x 2.10 drawn on two elevations, spec HELD Q-63 C); north 31.37; lower 1.20;
  railing infill not printed (HELD). Freelancer fence 37.20 vs engine 37.17 on his scope: AGREE (-0.08 %); no gate row.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: every Gate A piece passed first time on its round (r2 for two of them) because both r1 lessons of
this morning (read every label inside a detail; read the linetype at an open side) were applied. WHAT GOT WORSE:
nothing measured got worse; the reveals package lost one Gate B round. WHAT WAS LEARNED: a merged Gate A ledger can
carry a wrong basis into an integration when its acceptance did not test a special shape: the reveal ledger took
heights from the size table, which holds the band-crown rectangle, while the arch is in a separate outline record.
WHAT IS MISSING: about half the block walls (held by name), the 470 borrowed-basis rebar lines, bar bends / hooks /
laps (designer), and 12 integration rows (sills, formwork, roof, ceilings, skirting, waterproofing, outside plaster,
earthworks, foundation waterproofing, spatter dash, masonry accessories, mortar). GATES: lowest open gate 2 (M3
architectural ledger 11 Nov, M4 structural ledger 25 Nov). Week 2 (3 Nov): T-326 r2 and the sills package are the
realistic verified-coverage gains; formwork is at risk for 3 Nov at one integration package a day.

DECISIONS THIS RUN: reveals r2 first in the integration lane (fault and fix exactly as the Checker wrote them); NEW
gate 2: bind the 470 note-9 lines (first in the structural lane) and audit every trade line on the six arched
openings (first in the architectural lane); NEW gate 3: straight-bar cutting list for the 7 schedulable populations,
splice-count proof and a proposed new method version (frozen method untouched), designer RFI rows for the shape and
lap gaps (proposed text; I apply them to the consultant list; nothing sent). Queue check: 47 actionable rows, 0
flagged, 0 stall checks. TODO 8 (S 4, A 3, I 1 claimable + 12 queued by design).

LESSONS REGISTER PROPOSALS (standard s.7; for the Checker / main chat to confirm): (1) the Checker's row from
D-T326-1: '2026-10-30 | three arched-window reveals booked on the rectangle in a merged ledger and an integration
package | the reveal ledger took heights from the size table and did not read the merged arched-opening census; the
r2 Gate A checked depths, not head shape | every reveal / arris / perimeter quantity of an opening reads its OUTLINE
record first; R-T326-2 + regression test; T-377 audits the other trades | T-326 r2 / T-377 | PROPOSED'. (2) from
T-366: '2026-10-30 | a lap note scoped to starter bars was applied to 470 non-starter lines (beam ends, column laps, GB
ends, slab development) | the note's scope was not read before its arithmetic | a lap or development length is valued
only from an authority that names the bar population (R-T373-1, every villa); otherwise HELD by name | T-373 tests
normal / adverse | PROPOSED'.

TEAM HEALTH (12:38 - 16:30): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2 (the 13:00 run
closed 14:19, 79 min, an integration package: in budget), Checker x3, Lead x1); all self-checks PASS; scheduler last
runs SUCCEEDED (Worker 2 14:40, Worker 3 15:00, Dashboard 12:55). Six runs again base64-encoded the Drive connector's
raw download before 'agent_env.sh decode' (works; private files stayed in .work/private, sha verified). One board
push race (Checker 15:38 vs Worker 1, rebased once). READY 0. Scout paused (your 28 Oct choice).

OWNER PACKAGE: no new item today. Q-78 (cement : sand mix for the black block-joint mortar, written in full in the
12:40 report and OWNER_QUESTIONS.md) is still open; not urgent: 3.870113 m3 of mortar is measured, only bags / sand
are held, the mortar integration is last in the integration lane. No push sent.

NEEDS FIXING (only you or the main chat): (1) 'agent_env.sh decode' accepts only base64 while the Drive connector now
saves raw bytes; every agent works around it by base64-encoding first (six runs since 12:38). A wrapper change that
accepts raw bytes when the input is not valid base64 and verifies the sha would remove the risk of a corrupt private
copy; I may not change it. (2) 'run' still allows only the two scoring tools. Neither blocks work.

## LEAD REPORT 2026-10-30 12:40 UTC

Drive readable: nothing created in the Urban BOQ private data folder or the Alsenan project folder since 30 Oct 08:00
(search empty; no photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6); `.work` prepared
by `status` (auto). Working branch 88ef8cb8 -> 5bde82a7 (six Checker merges via 'engine push'); no owner commit.
Self-check: codemap PASS, pytest t061 PASS, freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since your 29 Oct
answers; nothing undone.

HEADLINE: the slab bar ends entered the candidate on the FIRST pass, under your 29 Oct rule (only drawn bars valued);
candidate of record now ARCH_TAKEOFF_V3.0.27, NOT RELEASED. Six pieces checked and merged since 08:25, two sent back
for a narrow fix; nothing waits for the Checker now. One decision for you today (block-joint mortar mix, below).

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; reinforcement
10,250.168 kg; whole verified lines in the candidate export 2, released 0; scored verified share CONCRETE 12.50 %
unchanged):
- REINFORCEMENT (kg), Gate B PASS 11:35 first time (V3.0.27): slab bar-end lines re-booked end class by end class from
  the two merged end ledgers. Continuous ends: ST p.15 draws no development (bottom bars curtailed or running through,
  counted once in the mesh line): 8 lines NOT APPLICABLE with evidence (were 3.951 .. 7.778 kg each on note-9 lengths).
  Edge-beam ends: the drawn straight part only (beam width less 40 mm cover): 59 part lines 136.573 .. 150.695 kg.
  Top bars: note 2 vs the p.15 envelope, across-beam part added, past-span part removed: 612.079 .. 1,618.962 kg on 86
  lines. Up-turn / hook-down legs and undrawn ends BLANK by name. Valued slab bar-end steel 1,721.189 .. 3,744.324 ->
  748.652 .. 1,769.657 kg: mostly a move to HELD, not steel found absent. The Checker re-derived all 196 changed + 138
  added lines by his own script: 0 mismatches; 3,579 other lines byte-identical; hand checks GF-135 x 3.160 .. 3.259 kg,
  2F-047 y 3.704 .. 17.259 kg (0.000 %). Freelancer 5,400 kg is one lump: RULE_DIFFERENCE, no %. Engine vs freelancer
  for the trade stays NOT COMPARED line by line.
- BLOCKWORK accessories (research, merged 09:00 / 09:58, not yet in the candidate): white AAC mesh strip both supplier
  families, none chosen (A 310.83 + 10.00 held / B 412.42 m.l); 6 lintel bearings cut 4.0786 m.l (Checker 0.000 %),
  4 held; black mesh 545.3060 m.l (+0.34 %, five named walls). MORTAR (B9-04): 3.870113 m3 installed (bed 2.623806 +
  head 1.246308) on the 24 black walls / pieces already in the candidate at your 40 x 20 module and 10 mm joint
  (ASSUMED - OWNER-APPROVED, Q-75 + 29 Oct); Checker 0.000 %, line PARTIALLY VERIFIED: the joints against column faces
  and under beams are a physical component (+5.5 .. +13.4 % on 4 walls, about 0.2 .. 0.5 m3) HELD by name per junction;
  white AAC adhesive HELD (supplier item); cement / sand HELD (no mix set). Freelancer has no mortar row.
- EARTHWORKS / TEMPORARY WORKS (merged 09:00): excavation support TRIGGERED on all 4 plot sides (ST p.8 note 15: pits at
  or beyond the plot line >= 1.50 m deep; 10 excavations cross the line); dewatering CONDITIONAL (water -4.50 vs
  formations -1.50, 3.00 m clearance; lift pit about 4.80 m deep); quantities None (no extent drawn); freelancer 0 rows.
- JOINTS / SEALANTS (merged 09:58): 0 movement joints, water stops or sealants on 31 sheets and both DXF text lists;
  engine 0 / freelancer 0 = no quantity both; his 1,297.35 m.l 'joints' row is plaster.
- FACADE CLADDING (merged 11:40 at r2): none drawn (109 face keys NOT IN DRAWN SCOPE, 0.000 m2; freelancer 0 rows,
  agree); the porch arch quoins visible face 1.5149 m2 HELD (r1 was rejected on a block-outline reading that did not
  reproduce on the Checker's own handle check at r2); material an architect question, not sent.
- SENT BACK NARROW (12:02 / 12:04): exposed wall-tile edges: the Checker's own DXF re-measure agrees 31.65 m.l (24.35
  corners + pantry wall end and flat stop), but 7.30 m.l at GF-14 was given the full 3.65 band where the plan draws an
  overhead element (a HIDDEN-linetype pair across the opening): held until its head level is read, plus a head arris
  0 .. 1.256 m.l; bar-detail census: eight exploded bar-shape labels on the pool detail were not cited, one of them a
  6ø12/m vertical with a return under the shallow end that bears on a bar the census called 'not drawn'. No quantity
  moved by either.
- CONSULTANT QUESTIONS (NOT SENT): the Checker's corrections to the remaining 26 are applied (S10 tank sheet, S12
  rewritten to links and bar ends only, S13 sheets, S18 undated p.8 and two source drawings, S22 third beam B19 and the
  drawn extent, A02 elevations as source); A03 / A04 elevation sheet numbers still to name. Nothing goes out without you.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: a second Gate B package passed first time today (blockwork 07:50, slab bar ends 11:35) because both
were wired line by line from ledgers the Checker had already verified. WHAT GOT WORSE: nothing measured; the valued
slab bar-end kg fell because undrawn parts moved to HELD under your option B (a truer basis, not a loss). WHAT WAS
LEARNED: two first-round rejections had one cause, a drawing mark inside the detail's own extent left unread (the pool
detail's shape row; a HIDDEN linetype that means 'overhead'). WHAT IS MISSING: about half the block walls (held by name),
mortar / accessories / reveals / sills / formwork / earthworks integration (13 lane I rows, one at a time), shower
tanking, sanitary fixture count, bar shapes, lap sources (new or open research rows). GATES: lowest open gate 2
(M3 architectural ledger 11 Nov, M4 structural ledger 25 Nov).

LESSONS REGISTER PROPOSALS (standard s.7; for the Checker / main chat to confirm): (1) '2026-10-30 | a bar-detail census
missed the detail's own exploded bar-shape row (T-359 r1) | labels searched near the section only | census every bar
label inside the detail's extent and tie each to one population or name it (every villa) | t359 r2 adverse: uncited
label refused | PROPOSED'. (2) '2026-10-30 | a wall-tile edge at an open side was given the full band where the plan
draws a HIDDEN-linetype element across the opening (T-368 r1, 7.30 m.l) | linetype not read; open side assumed full
height | an open side crossed by a HIDDEN-linetype element is an opening under a head until the head level is
established (R-T368-7; every villa, every trade using the side: tile, plaster, ceiling, blockwork) | t368 r2 normal /
adverse | PROPOSED'. (3) from T-318: 'research ledgers keyed by line id must be consumed by the integration that owns
those lines; bar-end lines are re-booked end class by end class (Checker's row, PROPOSED)'.

TEAM HEALTH (08:25 - 12:40): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Checker x4,
Lead x1); all self-checks PASS (this Lead session's venv has pytest this time). Worker 3's 09:00 run wrote 'run unknown'
and lasted 93 min (T-318, a full integration package: in budget). Process note: Worker 1 (11:41) reported that
'agent_env.sh decode' turned an already-binary Drive download into garbage (sha mismatch) and copied the raw download
straight into .work/private (still the private folder, outside the repository, sha recorded: no exposure); the other
workers base64-encode first, which works: I wrote that path on the board. Queue check: 47 actionable rows, 0 flagged,
0 stall checks. READY 0; TODO 8 (S 3: T-359 r2, T-366, T-371; A 4: T-368 r2, T-361, T-369, T-370; I 1 claimable:
T-326, 12 QUEUED behind it by design). Scout paused (your 28 Oct choice).

OWNER PACKAGE (one item; standard s.2.7: a material genuinely unspecified and an Urban estimating method).
ISSUE: cement and sand for the block-joint mortar of BLACK (cement) block walls. EVIDENCE: no drawing note or
specification prints a masonry mortar mix (31 sheets, both DXF text lists; merged T-367 / T-365 searches); your
answered rules give a mix only for the tile / marble bed 1:4 (Q-45) and the stair bed 1:3 (Q-53), and the engine refuses
to borrow either for masonry. INVESTIGATION: mortar volume is settled by your module rule and 10 mm joint: 3.870113 m3
installed on the walls now in the candidate (Checker 0.000 %), plus perimeter joints about 0.2 .. 0.5 m3 held by name;
about half the black walls are still held, so the final volume will grow with them. ALTERNATIVES the record leaves
open: (A) 1:4 cement : sand for masonry, priced like your Q-45 figures (about 8 bags of 50 kg and 1.1 m3 sand per m3 of
mortar): on today's 3.87 m3 about 31 bags and 4.3 m3 sand; (B) 1:3 (about 9.6 bags and 1.0 m3 sand per m3, as your Q-53
derivation): about 37 bags and 3.9 m3 sand; (C) another mix you use for block laying, with its bag and sand figures.
QUANTITY IMPACT: only cement bags and sand on the mortar line; no m2, m3 or other trade moves. RECOMMENDATION: (A) 1:4 if
that is what Urban buys for block laying, because it is the general-purpose masonry mix and keeps one procurement basis
with your Q-45 figures; this is an estimating convention only you can set. WHAT STAYS HELD meanwhile: cement / sand /
bags of the mortar line; the mortar m3 itself is not held. NEXT ACTION: written as Q-78 in OWNER_QUESTIONS.md; your answer there feeds the
mortar integration (queued last in the integration lane) uses it. Not urgent: no work is waiting on it; no push sent.

NEEDS FIXING (only you or the main chat): (1) 'agent_env.sh decode' expects base64 while the Drive connector now saves
raw bytes; on raw input it either fails ('Invalid base64') or, per Worker 1 today, produces a corrupt file. Workers
work around it (base64-encode first). A wrapper change (accept raw bytes when the input is not valid base64, verify the
sha) would remove the risk; I may not change it. (2) Still open: 'run' allows only the two scoring tools. Neither blocks
work.

## LEAD REPORT 2026-10-30 08:25 UTC

Drive readable: nothing created in the Alsenan project folder since 29 Oct (search createdTime > 30 Oct 04:00 empty; no
photo review task). Repositories: attached Urban-Project-AI checkout (main eafbb0f6); `.work` prepared by `status`.
Working branch 90135e91 -> 88ef8cb8 (three Checker merges via 'engine push'); no owner commit. Self-check: codemap PASS,
pytest t061 FAIL ('/home/claude/urban-project-ai/.work/venv/bin/python: No module named pytest': this session's venv
only; every worker and Checker run since 04:25 shows PASS), freeze PASS (0). OWNER_SESSION_CHANGES: no new entry since
your 29 Oct answers; nothing undone.

HEADLINE: the blockwork walls entered the candidate on the FIRST pass (candidate of record now ARCH_TAKEOFF_V3.0.26, NOT
RELEASED). The block-wall lines that were blank now carry 579.10 m2, of which 297.85 m2 the Checker measured himself.
Two research pieces merged (kitchen / laundry / pantry tile zones, soil treatment), three are handed in and wait for
the Checker. Nothing needs your decision today.

ALSENAN, per trade (released V2.9 + route G unchanged: concrete 92.77 vs freelancer 111.81 m3, -17.03 %; whole
verified lines in the candidate export 2, released 0; scored verified share: CONCRETE 12.50 % unchanged, blockwork row
restated by the Checker at 07:55):
- BLOCKWORK (m2), Gate B PASS 07:50 first time: MAS.BLOCK 0 -> 579.1011 m2 on 57 part lines (VERIFIED 297.847 on 18
  walls at the Checker's own wall values; DRAWING-CONFIRMED 157.6488; ASSUMED - OWNER-APPROVED 123.6053, source your
  Q-55 door rule); wall volume 104.468865 m3; wall-panel geometry twin 579.1011 m2 (not additive). HELD by name, blank:
  28 walls, 10 pieces and one slab-drop band (46.8019 - 7.9131 d). The other 3,697 lines byte-identical. Checker's own
  re-measure of every drawing-confirmed / owner-approved wall from the architectural DXF and the structural bands and
  schedules: largest line deviation 0.03 %. Engine vs freelancer: his 1,260.69 m2 is NOT COMPARED while about half the
  walls are held (a % now would compare a part with a whole). Finding F-T279-1: the open end of GF-W28 (0.063 m) is not
  named on any line: sent to the accessories integration as an acceptance item.
- WALL TILE (m2), MERGED 06:05 (research): kitchen / laundry / pantry add 0 faces / 0.0000 m2: the three rooms are wet
  (UP-WET-001 / UP-FIN-WALL-001 / Q-48 A), so their zone is the full-height tile already on the candidate's wall-tile
  line. Checker's own DXF: laundry 16.940 m / 52.5290 m2 = line (freelancer 50.55, +3.91 %, RULE_DIFFERENCE proposal
  stands: his height); pantry 10.500 m / 32.3750 m2 vs line 32.3422 (+0.0328 m2, +0.10 %): a named correction for the
  next finishes package. Kitchen 14.500 m stays HELD (G2). Splashback drawing-derived HELD (no printed band).
- SOIL TREATMENT (B1-05), MERGED 06:05: NOT IN DRAWN SCOPE (31 sheets, both DXF text censuses, the Arabic notes); no
  freelancer row; no line (never 0).
- BURIED CONCRETE (m3): the Checker issued the two downgrade-only records on V3.0.25 (boundary lower band 7.2204 m3 ->
  HELD, audit range 5.6392 .. 11.0328; 9 ground-beam lines 1.943901 m3 -> HELD, 1.643901 .. 2.291867); line m3 not
  edited; the earthworks package reads them.
- HANDED IN, NO VERDICT YET: excavation support / dewatering (support TRIGGERED on all 4 plot sides by structural note
  15: pits at or beyond the plot line >= 1.50 m deep, 10 excavations cross the line; dewatering CONDITIONAL: water printed
  at -4.50 vs formations at -1.50, the lift pit about 4.80 m deep; quantities None: no extent drawn; freelancer 0 rows);
  facade cladding (0 of 14 sheets / views print a cladding; one drawn form, the porch-mouth arch quoins, HELD with a
  visible 1.5102 m2 and its material a proposed architect question, not sent); white AAC mesh strip (both supplier
  families shown, none chosen: A 310.83 + 10.00 held / B 412.42 m.l; lintel bearings 6 cut 4.0786 m.l, 4 held; black
  mesh 543.4739 -> 545.3060 m.l, +0.34 %).
- CONSULTANT QUESTIONS (NOT SENT): the Checker re-checked the 26 remaining questions: 18 right, 5 sheet corrections, 1
  wrong (S12: the planted-column main bars ARE printed; only links and bar ends remain to ask), 2 partial (elevation
  sheets). I apply these next run; nothing goes out without you.
Development project 2: paused, not measured.

WHAT IMPROVED / WHY: the first verified block-wall m2 carried into the candidate this week, first pass, because the
wall-by-wall fill (status labels fixed on 29 Oct) was integrated exactly as verified. WHAT GOT WORSE: nothing measured.
WHAT WAS LEARNED: a 'missing' category can already be carried by another family (kitchen / laundry tile is wet-room
tile); an open wall end can drop between two line families unless every piece is named (F-T279-1).
WHAT IS MISSING: about half the block walls (held by name), all finishes / formwork / earthworks integration packages
(13 lane I rows, one at a time), mortar, joints, tile edges, lap sources (new research rows).
GATES: lowest open gate 2 (architectural and structural ledgers, M3 11 Nov / M4 25 Nov).

LESSONS REGISTER PROPOSALS (standard s.7; for the Checker / main chat to confirm): (1) 'Before calling a BOQ family
missing, search the families that may already carry its faces (T-351: kitchen / laundry tile = wet-room full-height
tile); normal case wet kitchen, adverse case a dry kitchen with a printed splashback band.' (2) 'An integration package
names every wall piece, open end included, or holds it by name (F-T279-1, GF-W28 0.063 m).'

TEAM HEALTH (04:25 - 08:25): every STARTED line has a final line (Worker 1 x2, Worker 2 x2, Worker 3 x2, Checker x2 +
two correct overlap-guard lines, Lead x1); all self-checks PASS except this Lead session's pytest (venv without
pytest). Worker run lengths, STARTED to final line (T-279 57 min, T-354 10 min, T-358 14 min,
T-360 19 min, T-362 15 min, T-351 17 min): research rows are finishing well under the 50-minute package; the new rows
are sized larger (census + ledger + rule + fixture). Stamp drift: the T-351 row said READY 05:35 vs its final line 04:57
(Checker note); this Lead's STARTED line says 08:25 for about 08:17. Queue check: 49 actionable rows, 0 flagged, 0 stall
checks. READY 3 = the target; TODO 7 (S 3, A 3, I 1 claimable: lane I runs one row at a time by design, 12 QUEUED
behind T-318). Scout paused (your 28 Oct choice).

OWNER PACKAGE: none today. No genuine decision is due under standard s.2.7: every held quantity has an investigation
or a consultant question in the unsent pack.

NEEDS FIXING (only you or the main chat): (1) the Lead session's venv lacked pytest this run (others had it): if it
recurs, the wrapper's setup should reinstall the pinned requirements; I did not change it (not permitted). (2) Still
open from earlier: the 'decode' wrapper expects base64 while Drive returns raw bytes (workers wrap them; working);
'run' allows only the two scoring tools (each research package reproduces through its own test). Neither blocks work.
