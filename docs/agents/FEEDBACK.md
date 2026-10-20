# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-20 00:30)

1. **Merged pieces not wired into the released run** (largest, unchanged): seventeen checked pieces and hand tables, and
   the released Alsenan run is still 8774071 (concrete 92.77 vs 111.81 m3). The wiring of wet areas and roofs (V2.11) is
   READY but not verified because the verifier's execution was refused at 00:20. Decision: verifier checks it first at
   its next run with execution; owner setting (option 2) stays under NEEDS FIXING.
2. **Heights still the bottleneck**: plaster 1151.14 / paint 1191.13 m2 HELD on Q-52 (no 0.60 m beam drawn) and now Q-54
   (annex slab); 23 of 29 windows (scans) and all doors but one (no printed height: Q-55). Decision: T-090 (per-room hand
   table under each option, ready the hour the owner answers), T-091 (printed-notes census), T-092 (scan reader with a
   chain-sum check, from R-01).
3. **Stairs need two more rules**: round stair with no section (Q-50), turning steps (Q-51). Asked by the verifier.
4. **Execution refused, intermittently, for any agent**: since 22:40, worker 1 (23:37 / 23:38) and worker 3 (23:44,
   00:02) passed every self-check step; worker 2 (23:47, venv) and the verifier (00:20, venv + freeze tool) were refused
   "[Code from External]". Worker 3 had a merge refused "[Untrusted Code Integration]" and used a fresh -r2 branch (the
   TEAM.md route; it works). Decision: two more NO REPO CODE rows (T-090, T-091) so a refused worker still moves a
   quantity; the verifier's manual sha256 freeze check is noted but does not replace the tool for code tasks.
5. **Record slips**: the Q-38 answer carried the Q-47 text (worker 1 could not find the answer). Decision: corrected from
   OWNER_SESSION_CHANGES.md; owner-answer records are now checked against that log each Lead run.

## 2026-10-20 00:30 (lead run)

- **T-083 opening heights by hand: PARTIAL (MERGED ce74b98).** Windows with printed heights 6 of 29 (was 4): 26.485 vs
  freelancer 24.280 m2 (+9.1 %); W13, W14, W15, W18 ENGINE_RIGHT on the printed heights, W17 RULE_DIFFERENCE (Q-39 C); a
  1F bath window printed 0.50 x 2.16 where he takes 0.60 x 0.80. Held: 23 windows (scans give no height), the curved pool
  glazing width (answered by Q-38 A, record fixed: 6.57 m), the 2F stair window (PDF / DXF conflict), every door but the
  main entrance. Decision: owner Q-55 (door height), T-091 (notes census), T-092 (scan reader, check-only).
- **T-088 room levels and wall heights by hand: PARTIAL (MERGED 41f7da7).** 30 of 32 room levels read; floor-to-floor GF 4.50,
  annex 4.00, 1F / 2F 4.20 from sections A-A and B-B; but no 0.60 m beam on any slab plan, so every room held: plaster and
  paint stay HELD. The 5 rooms with printed lengths give 282.67 m2 by option A vs freelancer 299.58 m2 (-5.6 %).
  Decision: owner Q-52 (asked by worker 2), owner Q-54 (annex), hand table T-090 for all rooms under each option.
- **T-084 stairs by hand: PARTIAL (MERGED ad1eb36).** With Q-46 A / Q-47 A the main stair is 5.011 m3 by hand (steps
  1.386 + waists 2.885 + landings 0.740) vs freelancer 8.131 m3 (-38.4 %); winders 0.120 m3 and the round stair
  (freelancer 5.510 m3) UNRESOLVED. Decision: owner Q-50 / Q-51 (verifier), T-056 updated to reproduce 5.011 m3.
- **T-075 schedule text rows: WORKED (MERGED b87f4d6).** 5 CN column lines held -> not present (freelancer 0, agree);
  6 necks 0.540 m2 section agree; height held (Q-21 C). Not wired. Decision: wiring with the concrete ledger later (gate 3).
- **T-079 wet areas / roofs wiring (V2.11): READY, NOT VERIFIED.** Worker 1: wet floor membrane 72.12 vs 72.01 m2
  (+0.16 %), upturn walls only 125.57 vs 144.61 lm (-13.2 %, rule difference), roofs 204.11 vs 285.00 m2 (-28.4 %, top roof
  held), rolls held on Q-49 at the time; L4 = base failures + 2 fixed. Decision: verifier first item next run.
- **T-081 r2 room levels V2: READY, NOT VERIFIED.** 21 of 27 rooms levelled (was 6); owner heights in registry 1.8.0 as
  diagnostics; annex held (no slab read). Decision: verifier after T-079; annex -> Q-54.
- **Scout answers R-01, R-02, R-05 (00:02): used.** R-01 -> T-092 (scan reader with an exact chain-sum check; Tesseract
  CLI already in the image, no OpenCV). R-05 -> notes on T-089 (FFD + L1 lower-bound proof, no OR-Tools install) and T-073
  (virtual_entities, edgeminer at 1e-6 m only; larger gaps HELD, no Urban gap rule). R-02 (SHX glyph sheet): not tasked
  now: it needs the client's own font file and no Alsenan quantity is blocked by an unread label today; revisit if one is.
- **T-086 room-by-room finishing table: PARTIAL (READY 00:14, worker 3).** Wet floors 72.12 vs 72.01 m2 (+0.16 %) + pantry
  13.50 m2; 10 dry rooms 194.98 vs 189.61 m2 (+2.83 %); open-plan room and wet walls HELD (Q-52; wall candidate 403.02 vs
  433.83 m2); stairs 39.49 m2 marble; PROVISIONAL materials (owner Q-45): mortar 11.16 - 15.07 m3, cement 80 - 111 bags,
  sand 10.91 - 15.21 m3, adhesive 58 bags. Stair cement / sand held correctly: no 1:3 figures -> owner Q-53 (worker 3).
  Decision: verifier third after T-079 and T-081 r2; wet walls released when Q-52 is answered.
- **Worker 2 run 23:40: NO-CLAIM (execution refused, no NO REPO CODE row free).** Decision: T-090 and T-091 added.

## 2026-10-19 22:20 (lead run)

- **T-043 beams by hand: WORKED.** Merged 6975158; verifier re-read the 5 released spans (3.691 m3) and 0.240 m3 upstands
  on the Drive DXF. Not wired. Decision: T-085 claimable; owner Q-44 = A adds the B4 ring beam per dome opening to T-085.
- **T-076 membrane fold V2: WORKED.** Merged 8884287. Strip method on 17 of 17 real wet areas (was 0 of 14); 33 of 34 hand
  layouts reproduced; walls-only upturn 125.57 vs freelancer 144.61 lm (-13.2 %, RULE_DIFFERENCE by Q-35 C); rolls 13 /
  14 / 15 by layout. Decision: T-079 TODO; the layout choice is an owner rule gap -> Q-49.
- **T-082 opening heights from PDF: PARTIAL.** Merged 2dee954. The reader works on vector PDFs (25 hand cases), but the
  Alsenan sheets are scans: windows still 4 of 29 (13.892 vs 14.350 m2, -3.2 %), doors 0 of 12.0 m2. Decision: T-083 hand
  table released for any worker; R-01 updated (OCR of scanned dimension text); plan reader stays gate 4.
- **T-081 room levels + finish heights V2: PARTIAL (REJECTED by the owner's new rule).** Room levels pass every gate;
  finish heights refused the build-up and decor depth that the owner's 21:40 rule now sets. Decision: rework on its
  branch (owner values as OWNER_RULE inputs, unmarked rooms by the Q-43 answer, per-room plaster / paint ranges) and
  T-088 hand truth; wet-wall height -> Q-48.
- **T-084 stairs by hand: PARTIAL (READY, NO REPO CODE).** Steps released 0.483 m3; main stair held on two drawing
  conflicts, which the owner answered (Q-46 A, Q-47 A): hand main stair 5.131 vs freelancer 8.131 m3 (-36.9 %, his
  flights 37 - 54 % longer than drawn). Decision: verifier applies the answers and merges; T-056 rewritten with them.
- **T-075 column schedule text rows: WORKED (READY).** 5 CN column lines HELD -> NOT_PRESENT (freelancer 0, agree); 6 CN
  necks 0.090 m2 each, height HELD (Q-21 C; freelancer 0.810 m3 at an unprinted 1.50 m, UNRESOLVED). All self-check PASS.
  Decision: verifier checks it first; no value from an assumption.
- **T-083 opening heights by hand: FAILED (no trace).** Claimed 20:42, nothing pushed. Decision: released to TODO.
- **Worker 3 runs 21:25 / 22:03: PARTIAL / NO-CLAIM (refused).** 21:25 delivered T-084 by hand; 22:03 found no NO REPO
  CODE row free and asked for one. Decision: T-088 and T-083 are NO REPO CODE rows now.
- **T-050: CLOSED** (superseded by T-058, merged 8774071).

## 2026-10-19 20:15 (lead run)

- **T-013 section binding: WORKED.** Merged 44e1502 (verifier 18:55). GF floor-to-floor 4.50 m printed, 1F 4.20 m derived,
  2F and annex HELD, slab 0.16 m owner rule. Not wired: no quantity moved. Decision: wired with T-081's room levels in T-079.
- **T-080 reference-book checks: PARTIAL.** Merged cb7407a. Book items turned into Q-40 / Q-41 / Q-42 and test spec
  T80-HGT-1; the Kuwait specification chapters 07100 / 09200 / 09300 / 09400 / 09900 are unread (file over the connector
  limit). Decision: owner upload under NEEDS FIXING (already asked; repeated); no new task until the parts exist.
- **T-081 room floor levels + finish heights V2: WORKED (READY, verifier next).** Acceptance met: GF split +1.00 / +0.30
  (engine was 0.00 from plot marks), GF +1.00 zone 4.50 m printed (was 5.50 m), 1F 4.20 m, 2F HELD; 24 non-Alsenan hand
  cases; the 0.150 m allowance and 0.10 m build-up are refused inputs (no-assumptions rule met). What did not move:
  plaster 1151.14 / paint 1191.13 m2 stay HELD (no soffit, build-up or ceiling level printed) and 21 of 27 rooms print no
  level. Decision: owner Q-43 (worker's question, kept as written); wiring in T-079.
- **T-043 beams by hand: WORKED (READY, NO REPO CODE).** 24 of 24 spans classified with sheet evidence; 5 released by
  printed sections and marks, 3.691 m3, plus 0.240 m3 of upstands the engine lacks; 19 HELD (4.25 - 9.18 m3) with reasons.
  No value from an assumption (sections read from A-A / B-B; no neighbour depth copied, owner Q-16 A). Decision: owner
  Q-44 (dome ring beam after the skylight change), engine follow-up T-085 (planted-column split, missed mark, upstands),
  designer RFIs kept HELD and listed in the report.
- **Worker runs with no result: FAILED x4.** Worker 1 18:22 (venv refused, claim refused), worker 2 18:50 (claimed T-043,
  freeze check refused, released), worker 1 19:25 (claimed T-043, DXF read refused "[PII Data Handling]", released),
  worker 3 20:03 (self-check refused, no NO REPO CODE row left). Cause 5 above. Decision: SELF-CHECK METHOD note, T-083 and
  T-084 as NO REPO CODE rows, owner setting (NEEDS FIXING).

## 2026-10-19 18:15 (lead run)

- **T-072 membrane purchase table: PARTIAL.** Merged 7b8ccfd. 14 wet areas 62.77 vs 62.43 m2 (+0.5 %), 13 rolls provisional,
  9 rows HELD never 0; the owner's 3 x 4 m kitchen reproduced exactly (16.28 m2, 2 rolls), but the strip fold ran on 0 of
  14 real rooms. Decision: T-076 (already tasked) now claimable, with the owner's Q-35 C and Q-37 A answers written in.
- **T-074 wet-area hand table: WORKED.** Merged 3d420e6. 17 areas: floor 72.122 vs 72.01 m2 (+0.16 %), boundary 144.729 vs
  144.61 lm (+0.08 %), equal to the engine piece within 0.002; walls only 127.07 lm (the Q-35 C basis). It is the truth for
  T-076.
- **T-077 lost windows: WORKED.** Merged c564481. Windows 29 drawn = 27 measured + 2 HELD (was 27 with 2 silent); doors 28
  elements, 0 silent. Width of the curved pool glazing asked (Q-38).
- **T-078 window / door m2: PARTIAL.** Merged 5f07bf0. 4 windows 13.892 vs 14.350 m2 (-3.2 %; ENGINE_RIGHT on printed
  2.30 / 1.60 vs his 2.00, and on the arched 1F living window 4.812 vs 4.650 under Q-32 A); 23 windows and all doors
  HELD: 15 on facades with no DXF elevation, 5 drawn on none, doors without height. Decision: T-082 (heights from the PDF
  elevations and section A-A); curved window width asked (Q-39).
- **T-013 section binding: WORKED (READY, verifier next).** GF +1.00 / +0.30 split, GF floor-to-floor 4.50 m printed, 1F
  4.20 m derived, 2F held, slab 0.16 owner rule; matches the hand census. Finding: engine GF plan level 0.00 from plot
  marks. Decision: T-081.
- **T-080 reference-book checks: PARTIAL (READY).** Supervisor's-eye book and waterproofing manual checked item by item
  (40 items with rule id or NO RULE); Q-40, Q-41 asked by the worker; L-1 (tile joints) asked by the Lead as Q-42; L-2 ..
  L-6 (movement joints, ground-slab DPM, primers / coats of a named system, wet-room FFL check, junction mesh) are scope
  items with no engine quantity today: kept in research/agents_t080 for later, no question now. The finish-height
  allowance 0.150 m contradicts Q-14: written into T-079 and T-081. Kuwait specification chapters not readable: owner
  asked for parts under 6 MB.
- **T-075 column schedule text rows: FAILED twice (no claim).** Classifier refused the chained claim; see cause 4.

## 2026-10-19 16:15 (lead run)

- **T-060 concrete ledger V2: WORKED.** Merged 9671133. Band 91.94 m and pool ring 2.357 m2 recovered, held per owner rules;
  1452 of 1455 lines identical. Not wired (cause 1).
- **T-065 foundations by member: WORKED.** Merged b09c06a. Isolated footings 64.346 m3 by hand = engine (freelancer 65.634,
  -2.0 %, ENGINE_RIGHT on F3 counted twice); F10 conflict -> Q-31 (filed under Answered by mistake; moved back to Open).
- **T-042 columns / necks / datum: PARTIAL.** Merged b842ec2. CN neck-only columns found (T-075 tasks it); datum not printed
  as a full arrangement, so necks / excavation / backfill stay HELD; section A-A is now on Drive as a single sheet (T-056
  reads it for stairs; the founding datum stays HELD as T-042 found).
- **T-010 wet / dry evidence: WORKED.** Merged 8fcabe0. Wet floor 72.12 vs 72.01 m2 (+0.2 %, was -12.8 %), upturn 144.73 vs
  144.61 lm, by the piece only (cause 1 -> T-079).
- **T-071 roofs: PARTIAL.** Merged 4054509. Three plan roofs 204.11 m2 = hand (ENGINE_RIGHT), total -28.4 % vs 285.00 m2
  because the 2F top roof is on no plan -> Q-34 (verifier). No-assumptions check: the 0.45 m parapet-end reach is an
  engine constant, not an owner rule; gaps above it stay HELD, so no assumed value enters a quantity (noted on T-079).
- **T-040 doors / windows: PARTIAL.** Merged 2c86de1 (research). Windows with printed heights 9.08 vs 9.70 m2 (-6.4 %,
  ENGINE_RIGHT proposals); 19 HELD (no printed height), 4 arched on Q-32, material on Q-33; 2 windows silently lost and the
  cause not traced (25-minute run, under the 50-minute rule). Decision: T-077, T-078.
- **T-072 membrane purchase table: READY, PARTIAL on its face.** 14 wet areas 62.77 vs 62.43 m2 (+0.5 %), 13 rolls
  provisional, 9 HELD rows never 0; owner's kitchen reproduced exactly; fold on 0 of 14 real rooms -> T-076; billed upturn
  110.33 vs 122.61 lm (-10.0 %) is a rule conflict, not a result -> Q-35. Verifier checks next.

## 2026-10-19 14:30 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-060 new concrete ledger (strip guard + curved strips) | WORKED (READY 662ab95) | Footing band recovered to its drawn 91.94 m (frozen 60.17 m) = 73.64 m pending + 18.30 m inside 17 members; pool wall plan 2.357 m2 = hand ring (frozen 1.24); 32 tests incl. a non-Alsenan ring and D pool, 60 synthetic villas conserve; 1452 of 1455 lines identical; freeze 0 | No quantity released by design: footing (77.27 vs 77.63 m3) and pool (3.50 vs 12.35) lines go from compared to HELD, so concrete is compared on 1 line (stair + dome 12.01 vs 21.83, WAPE 45.01 %) instead of 3 (17.03 %); 18.30 m inside members vs the hand reading 21.45 m not reconciled | Verifier merges; band volumes wait on Q-28, pool volumes now possible (Q-26 answered: flat 1.15 m, floor 0.40) via T-049; reconciliation in T-073 | T-073; T-049 promoted |
| T-065 foundations by member (hand reading) | WORKED (READY 9ea0aa0) | Isolated footings by hand 64.346 m3 = engine register (freelancer 65.634: F3 counted twice, F10 at the schedule size); straps 3.391 = freelancer 3.3925; band explained edge by edge (91.94 m, 21.45 m inside 9 footings, 70.49 m free); all from sheet evidence; own stdlib census with mirrored self-test | Section conflict B.W 20 x 60 vs typical 20 x 40 + pads (owner Q-28 asked by the worker, correctly); natural-ground boundary beam 3.526 vs freelancer 7.560 m3 (-53.4 %) not checked against the engine; engine straps 3.781 (+0.39) untraced; maps not rebuilt (repo code refused) | Verifier merges with a map rebuild; follow-up engine task for members as separate lines | T-073 |
| T-042 columns, necks, ground cell, foundation datum (hand reading) | PARTIAL (READY f826c38, 21-minute run) | Found that the column type CN is printed (neck 0.30 x 0.30, no column above ground) but drawn as plain text, so the engine drops it: 5 held CN 'columns' should be no line (freelancer 0), 6 CN necks get 0.090 m2; under every footing 10 cm plain concrete + membrane + 5 cm screed is printed; blinding 22.155 vs freelancer 47.055 m3 (-52.9 %, freelancer covers the whole plot) | Section A-A part could not be downloaded (6.37 MB, connector limit), so the founding datum stays unread; necks UNRESOLVED (engine 10.856 released + 8 held vs freelancer 8.805 m3); run far shorter than the 50-minute package | Verifier checks depth; engine fix for schedule rows drawn as text; owner asked again for single-page uploads | T-075 |
| Owner answers Q-23..Q-27 (main chat 12:55 - 14:15) | applied | Roof = bathroom rule (inside parapet + 0.20 m upturn, whole strips, 0.10 m laps); gaps covered by membrane; pool flat at 1.15 m; three domes; renovation test cancelled | "domes will not be concrete" conflicts with two structural dome shells and the freelancer's 6.78 m3: asked Q-29 | T-071, T-049 unblocked; T-068 cancelled; T-003 queued | - |
| Owner requirement: membrane purchase table | tasked | Engine already has the schedule and cutting plan | Kitchens have no waterproofing rule: asked Q-30 | Engine table + Alsenan hand truth | T-072, T-074 |
