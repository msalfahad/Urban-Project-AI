# Lead reports to the owner's main chat (newest first, last 10 entries)

## LEAD REPORT 2026-10-19 16:20 UTC

Repositories: Urban-Project-AI cloned (control and working branch); Drive readable. UrbanProjectsManager not needed this run.

PROGRESS (Alsenan; the released BOQ did not change: six checked pieces were merged since 14:30 but none is wired yet)
- Concrete: released 92.77 vs freelancer 111.81 m3 (-17.0 %), unchanged. Isolated footings by hand 64.35 vs 65.63 m3
  (-2.0 %, engine right: the freelancer counts one footing twice). Footing F10 drawn 3.25 m vs scheduled 2.80 m is held
  on your answer. Neck-only columns found in the schedule as plain text (5 columns the engine wrongly holds).
- Wet-area waterproofing floor (checked piece): 72.12 vs 72.01 m2 (+0.2 %; was -12.8 %). The membrane purchase table
  (waits for the checker): 14 wet areas 62.77 vs 62.43 m2 (+0.5 %), 13 rolls to buy, provisional; 9 rows held, never 0.
  Your 3 x 4 m kitchen is reproduced exactly (16.28 m2 cut, 2 rolls), but on the real Alsenan rooms the strip method ran
  on none of 14 (extra points on straight walls, two rooms at 45 degrees): a fix is on the board.
- Upturn: 123.13 lm on the full boundary (+0.4 % vs 122.61) or 110.33 lm on walls only (-10.0 %): your kitchen example and
  the registry doorway rule disagree: question Q-35 below.
- Roofs (checked piece): 204.11 vs 285.00 m2 (-28.4 %), upturn 181.59 vs 194.00 lm (-6.4 %); the three plan roofs equal
  the hand figure; the second-floor top roof is drawn on no plan (Q-34).
- Windows: only 3 of 29 have a printed height: 9.08 vs 9.70 m2 (-6.4 %, the drawing prints 1.60 / 2.30 where the
  freelancer used 2.00). The engine gives windows and doors as pieces only, so aluminium (12.0 + 116.9 m2) is not yet
  comparable; 2 windows are lost (curved pool glazing 6.57 m, a 0.50 m bath window): fix task on the board (gate 1).
- Gates: 0 done; 1 at risk (2 lost windows, pieces not wired); 2 and 3 started; 4 waiting.
- Next on the board (12 open tasks): lost windows; window and door areas from printed dimensions; membrane strips on real
  rooms; plot-edge foundation members; stairs from section A-A; pool from printed sizes; column schedule text rows;
  reading the supervisor's-eye book and the Kuwait specification chapters (waterproofing, floors, wall tiles, paint) as
  you asked; then wiring the wet-area, roof and membrane pieces into the released BOQ and re-measuring.

TEAM HEALTH
- All agents that ran since your 15:24 execution authorization could run code: verifier (16:10) PASS on clone, venv,
  codemap check, t061 test, freeze check; worker 2 (16:10) PASS on all five; worker 3 (16:03 claim) PASS on all five.
  Worker 1's last run (15:20) started before the change; its self-check shows from its 16:19 run.
- Verifier merged six tasks and pushed them itself (no more "[Merge Without Review]").
- Worker 2 had one command refused ("[Code from External]", a chained command); it did not retry and worked on.
- Every scheduled run since 13:30 left a RUN_LOG line. Research scout runs tonight.
- Fixed by me: Q-31 (footing F10) had been filed under "Answered" with no answer; moved back to Open.

QUESTIONS FOR OWNER (6 open, all no-assumptions questions; the list is long, the two new ones first)

Q-35 (NEW) Wet-room upturn at the door: does the 0.20 m upturn run across the door opening?
- Problem: your kitchen example counts the upturn on the whole boundary, door included (14.00 lm, 14.80 m2). The registry
  doorway rule UP-WP-DOOR-001 (your 2026-10-16 programme) says a doorway is never billed as width x 0.20 m but is a
  transition built by detail. On Alsenan's 14 wet areas: full boundary 123.13 lm (+0.4 % vs freelancer 122.61), walls only
  110.33 lm (-10.0 %); 12.80 lm of doorways.
- Where: your Q-30 kitchen answer; any Alsenan bathroom door (P7757 DXF / PDF part 01-02); the freelancer's
  waterproofing rows in his floors / waterproofing workbook.
- (A) Full boundary, doorway included: 123.13 lm, no separate doorway line.
- (B) Walls only 110.33 lm, plus a doorway transition line per door (pcs, with width), built to the detail.
- (C) Both: membrane to BUY follows your strip method (strips 0.20 m longer at both ends whatever is in the wall); the BOQ
  upturn line is walls only plus a doorway transition line per door.
- Recommendation: (C): your strip method already fixes the purchase, and a doorway needs a threshold detail that a
  length x 0.20 line hides (practice, not a code clause). For a single figure, (A) follows your newest words.

Q-36 (NEW) A new project folder appeared on Drive: may the team open it, and for what?
- Problem: at 15:27 UTC a third project folder was created under "Urban BOQ private data": an earlier-approved
  architectural plan, an architectural + structural plan "2" (uploaded twice), an all-floor-plans PDF and a photo; it
  looks like an old building and its new design. At 14:17 you cancelled the renovation test and said no new villa will
  come. No task names this folder (Drive shows its files were opened 16:03 - 16:06, by you or by a session). I will not
  decide whether it is a sample, a sealed blind test or not for the team.
- (A) Not for the team now; nobody opens it until you say. (B) Development sample for the PDF plan reader (say which files
  are old and new); no accuracy counted. (C) Sealed blind test: nobody opens it; you run it later.
- Recommendation: (A) until you say: opening a possible blind test cannot be undone and your direction is Alsenan only.

Still open (asked earlier today, full text in OWNER_QUESTIONS.md):
- Q-31 Footing F10 drawn 3.25 x 1.40 vs scheduled 2.80 x 1.40: (A) schedule 2.176 m3 with the F pad, (B) drawn 2.275 m3,
  (C) hold + RFI (recommended).
- Q-32 Arched windows: (A) to the arch top 9.42 m2 on the big window (recommended for aluminium supply), (B) true shape
  9.03, (C) to where the arch starts 8.20 + fan light apart.
- Q-33 Windows aluminium by default: (A) yes unless the drawing says otherwise (recommended), (B) only when drawn, (C) per
  project file.
- Q-34 Second-floor top roof on no plan: (A) from the 2F outer walls (at most 55.08 m2), (B) hold for the designer,
  (C) A as a provisional figure until confirmed (recommended).

NEEDS FIXING
- Nothing only you can do this run. (The execution settings now work for every agent that ran; the single-page sheets
  are being used.)

Team ids: merged T-060, T-065, T-042, T-010, T-071, T-040; READY T-072; CLAIMED T-074; new T-076, T-077, T-078, T-080
(TODO), T-079 (queued); T-073 released; Q-31 reopened; Q-35, Q-36 new.
