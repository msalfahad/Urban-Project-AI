# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-20 04:20)

1. **Merged pieces not wired into the released run** (largest, unchanged): the released Alsenan run is still 8774071
   (concrete 92.77 vs 111.81 m3). The wiring fix (T-093) is being built by worker 1 since 03:20; the cutting plan
   (T-089) waits for a code-capable verifier run. Decision: verifier order T-089 then T-093; T-095 after both.
2. **Runs that leave no trace** (worse): since 02:15, four of the five finished worker runs wrote no RUN_LOG line and
   claimed nothing (worker 1 02:19, worker 2 02:39, worker 3 02:59 and 03:59, each 3 - 13 min); the verifier passed
   every code step at 02:26 and was refused venv / codemap at 03:50. The two runs that did work (worker 2 03:39, worker 1
   03:19) passed every self-check step. Decision: no board change can fix a run that ends before its first write; the
   owner setting (EXECUTION_PERMISSIONS.md section 5 option 2) stays under NEEDS FIXING; two NO REPO CODE rows stay free.
3. **Rule gaps found by finishing a method** (new, from T-089): straight strips cannot reach dome-opening upturns and
   slanted corners (1.15 m2 on the 2F roof); no rule says where those patches come from. Decision: owner Q-58; patches
   reported in m2, outside the roll count, until answered.
4. **Heights, finishes and ceilings still need rules**: Q-52, Q-54, Q-55, Q-56, Q-57 open (plaster 1151.14 / paint
   1191.13 m2 held).

## 2026-10-20 04:20 (lead run)

- **T-089 membrane cutting plan per wet room and roof: WORKED on its own evidence, NOT YET VERIFIED (READY b8738a5).**
  Alsenan 17 wet areas 19 rolls = hand 19; strips 122.99 vs 125.27 m (-1.8 %: same rolls, the opposite start wall in 4
  rooms, e.g. GF kitchen 15.30 vs 16.60 m, ENGINE_RIGHT proposal); pantry 2 = 2; roofs 17 + 6 + 8 = 31 = 31, 25.76 m
  left over; top roof HELD (Q-34); each count with a lower-bound proof (scout R-05). 22 hand tests not Alsenan. Freelancer
  has no roll lines: not comparable. No-assumption check: lap and roll are rule inputs (UP-WP-002), Q-49 A applied; the
  patch pieces were left out of the count and named as unruled: correct. Concern: 13-minute run for a new module with 22
  tests and an SVG output (depth check). Decision: verifier first on the next code-capable run with a hand re-derivation;
  owner Q-58 for the patches. No new task (cause already tasked: wiring T-093, T-095).
- **T-093 wiring rework: in progress (worker 1, claimed 03:20, branch pushed 9ead6fd, run still open at 04:10).** No
  decision until its handoff.

## 2026-10-20 02:10 (lead run)

- **T-079 wet areas / roofs wiring (V2.11): FAILED its acceptance (REJECTED gate d).** Sound otherwise: wet floor 72.12 vs
  72.01 m2 (+0.16 %, reproduced by the verifier on the Drive DXF), upturn walls-only 125.57 vs 144.61 lm (RULE_DIFFERENCE
  Q-35 C), roofs 204.11 m2 / 181.59 lm, 0 V2.10 lines changed. Wrong: rolls held on "Q-49 open" (Q-49 = A answered
  22:40: hand 19 wet / 21 with pantry / 31 roofs), and the 2F top roof (Q-34 held) has no line, hiding ~80.9 m2. No-
  assumption check: every released value cites a rule; the faults are under-application of answers, not assumptions.
  Decision: rework T-093 (first code task) with hand truth T-094 for the roofs.
- **T-081 r2 room levels V2 + owner wall rule: WORKED (MERGED d52b5dd).** 21 of 27 Alsenan rooms levelled (was 6), 6 held
  with reasons; owner heights GF 3.65 / 1F-2F 3.35 m as diagnostics; plaster / paint still held vs 1151.14 / 1191.13 m2
  (Q-52, Q-54). Verifier note: registry 1.8.0 is built on 1.5.0 and not registered. Decision: T-095 builds 1.9.0 = 1.7.0
  + 1.8.0 and registers it after T-093.
- **T-086 room-by-room finishing table: PARTIAL (MERGED 6002856).** Wet floors 72.12 vs 72.01 m2 (+0.16 %); 10 dry rooms
  194.98 vs 189.61 m2 (+2.83 %); stairs 39.49 m2 marble; materials PROVISIONAL (cement 80 - 111 bags, sand 10.91 - 15.21
  m3, adhesive 58 bags). Held: open-plan room, wet walls (Q-52), stair cement / sand (Q-53). UNRESOLVED: 1F living 44.87
  vs 38.96 m2 (+15.2 %: the face holds the corridor / landing, which he has in no row). Decision: owner Q-56 filed; T-091
  splits the room by printed sizes.
- **T-090 plaster / paint per room by hand: PARTIAL (MERGED 2fb9553).** 6 closed dry rooms: Q-52 A 336.94 / B 321.56 /
  C 331.49 vs freelancer 375.40 m2 (-10.2 / -14.3 / -11.7 %); same-wall 5 rooms -5.6 / -10.0 / -6.7 %. Found: opening
  deduction full band (UP-OPEN-SCHED-001) vs his half = RULE_DIFFERENCE; ceilings have no plaster / paint rule (his
  painted decor ceilings 452.33 m2); the old V1 plaster-termination method conflicts with the owner's 21:40 rule (owner
  governs). Decision: owner Q-57 (ceilings); supersession recorded in T-095; totals wait on Q-52 / Q-54 / Q-55.
- **T-091 printed-notes census: not started (worker 1 claim push refused 01:25).** Stays TODO for a refused run.

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
