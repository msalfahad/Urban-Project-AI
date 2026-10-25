# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-25 14:15 UTC (Lead). Previous version: 2026-10-25 12:15 UTC. The released numbers did not change
(released concrete 92.77 vs 111.81 m3, -17.03 %; released default V2.9 + route G untouched). Your measure: whole BOQ
lines independently verified. The real export of the candidate now counts its FIRST whole verified line: the concrete
slab, 60.28 m3, checked panel by panel (62 of 62). Released: still 0 (nothing is released until you switch the
default). Waterproofing still cannot count as a whole line (no completeness list yet; that piece is queued). No
decision for you.

Since 12:15 (newest first; four pieces checked and merged, a new candidate of record):
- Concrete, exterior ground beams (main house): CHECKED AND MERGED into the candidate (13:35). The checker re-measured
  all 16 corrected lines on the drawing himself and agrees: 8.16 -> 15.96 m3 at the printed 0.95 m depth (+95.5 %).
  Ground beams in the candidate 27.36 -> 29.56 m3 with 12 lines held blank (annex and courtyard depths not printed).
  Columns 33.61 -> 28.22 m3: the second-floor and annex columns are now held (their heights are not printed), five
  members that are not on the drawings are removed with evidence, and the boundary ground beam now has a held line
  instead of no line. One curved beam stays "drawing-confirmed" only until its end detail is settled.
- Real export: reinforcement is now reported in tonnes (measured 10.25 t; held 15.25 .. 21.62 t, a range, not a
  figure), and the slab completeness check now matches panels by id, so the slab counts as a verified whole line.
- Reinforcement reconciliation (read-only): checked and merged. No ledger is counted twice (734 overlap groups, none
  double); the 16.39 t from the drawing extractor has no column steel and no steel for one ground-beam family, and
  its beam steel overlaps the checked beam ledger, so it is never added. No steel quantity moved. Next: your footing
  requirements (counts, lengths, the 5 cm cover question, the 874.86 kg footing line) as the next part of the same work;
  footing steel stays held.
- Formwork (missing from the candidate): part 1 merged (foundations, ground beams, columns; ground beams 47.95 m2
  measured, 74.36 m2 kept only as an alternative, never added). Part 2 (slabs, stairs, domes, tank) is queued.
- Plaster and paint: sent back for a narrow fix (a test-file name clashed with the formwork one; the curved pool-side
  window's deduction to be re-read with your 9.870 m2 answer). Being redone now.
- Ceilings: every ceiling face tied to the candidate's ceiling lines (79 faces, 36 lines). Engine 403.16 vs drawing
  362.01 m2 (-10.2 %), every m2 of the gap named (domes, stair soffits, areas with no ceiling). Found: one first-floor
  dressing room ceiling (2.97 m2) has no line at all. Waiting for the checker.
- Team: no worker run stood down since 11:40 (the smaller pieces fit the hour). Nothing new on Drive; no new photos.

Since 10:15 (newest first; three pieces checked and merged, the checker's records written into the export):
- Real export of the candidate BOQ: the checker wrote his verified-line and "hold" records and re-ran the export on the
  real drawings. 21.95 m3 of concrete that rested on depths or heights the drawings do not print is now shown as held or
  in conflict instead of released (exterior ground beams, second-floor and annex columns, one stair flight). Rows: 5
  verified as components, 999 measured but not yet verified, 1,921 held (blank, never zero), 54 not measured, 774 out
  of scope. Still missing: reinforcement in tonnes (the export still writes kg by default) and the completeness join;
  both are the next piece of work (starts 12:39).
- Stairs and domes: checked and merged; the checker agreed every figure he re-derived (released 8.06 -> 7.59 m3 on the
  verified basis; 2.86 m3 of verified or owner-approved parts to be released by splitting held lines; dome drums in no
  line, to be shown held).
- Block walls: checked and merged. 422.53 m2 determinate is ready to replace the blank block-wall lines in the candidate
  (297.85 m2 of it checker-verified on 18 walls); it goes in after the stairs and the two windows, in your order.
- Excavation and backfill (missing from both the engine and the freelancer): checked and merged as a ledger; every volume
  stays held because the drawings give only "not less than 1.5 m" for the formation level.
- Plaster and paint: every wall face of the 32 rooms is now tied to the candidate's plaster and paint lines (residual
  0.0000). Plaster = paint 703.30 .. 768.81 m2 (a range, not a midpoint). One room line that the candidate releases
  (59.45 m2 on the first floor) becomes held, because the curved pool-side window's deduction is not settled for plaster.
  Waiting for the checker.
- Formwork (missing from the candidate): first part of the face-by-face ledger: 414 faces tied to their concrete lines,
  residual 0.000 m2. Found: the boundary ground beam has formwork faces (35.26 m2) but no concrete line in the candidate
  at all; 16 exterior ground-beam lines still sit at the interior depth (being corrected now). Waiting for the checker.
- Reinforcement (your 11:51 Stage B): the read-only reconciliation of the different steel ledgers starts at 12:19 (what
  replaces what, what overlaps, nothing added twice, in tonnes); the completeness safeguard follows it. No steel quantity
  moves.
- Team: two worker runs stood down again because the previous run of the same worker was still working (about 80
  minutes, and the full test suite did not fit); new pieces are sized smaller so the suite fits the hour.
- Nothing new on Drive; no new photos.

Since 08:15 (newest first; three pieces checked and merged, the first real export back with the checker):
- First real export of the candidate BOQ: CHECKED AND MERGED (10:17). One project identity over every line, every
  quantity unchanged, one command gives the spreadsheet and csv. The verified-line records (the slab line, the
  foundation waterproofing lines) and the "hold" records for the unsupported depths are written by the checker in his
  next run (10:51); until then the export shows 0 verified rows. Next: the exterior ground-beam correction goes in.
- Concrete, exterior ground beams: the checker confirmed the finding from the drawings himself. On the drawn runs at the
  printed 0.95 m depth the main-house exterior ground beams are 15.96 m3, against 8.16 m3 in the engine (+7.80 m3,
  +95.5 %); three of them were carried as interior beams. Verified as a basis, not yet in the candidate (next
  integration after the export). The second-floor column question is settled: 8 lines carry the 3.53 m3 to be held.
- Block walls (a material gap found): the candidate BOQ today carries NO block-wall quantity at all; every one of its 21
  block-wall lines is blank, waiting on wall heights. The wall-by-wall ledger now ties all 76 walls to those lines:
  422.53 m2 determinate (297.85 m2 checker-verified on 18 walls, 48.47 m2 confirmed from the drawings, 76.22 m2 on your
  approved rules), more on 10 partly held walls, 28 walls held, and the walls under the sunken roof panels carried as a
  term in the held drop (7.91 m2 per metre), never guessed. Waiting for the checker; then it goes into the candidate.
  Freelancer comparison: he uses one height per floor, no per-wall figure, so not compared wall by wall.
- Stairs and domes: every stair and dome line of the candidate is now tied to its pieces. The candidate releases 8.06 m3;
  on the verified basis it is 7.59 m3 (-5.9 %: one flight built on assumed riser and waist values comes out, one landing
  confirmed from the drawings goes in). 2.86 m3 of verified or owner-approved parts sit inside held lines and can be
  released by splitting those lines. Found: the two dome drums are in no line at all (they will be shown as held, the
  drawings do not give them). Waiting for the checker.
- Floor area: the pantry zone (1.10 m2 wet) is checked and merged (candidate floor 380.36 -> 381.46 m2, +0.29 %, once
  integrated with the stairs package).
- Scoring guard against sealed files: fixed, checked and merged.
- Team: two worker runs stood down because the previous run of the same worker was still working (the pieces took
  85 - 100 minutes, more than the 50 I sized them for); every new piece now names where to stop.
- Nothing new on Drive; no new photos.

Since 06:15 (newest first; two pieces checked and merged, the first real export sent back for a small fix):
- First real export of the candidate BOQ: the checker ran everything himself on the real drawings and it passed, except
  one housekeeping check (the code map was regenerated before the last report file was added). Sent back for that fix
  only (about 10 minutes), plus one small correction he found: a "hold this line" record must never turn a row that is
  out of scope into a held row. It goes first in the checker's queue as soon as it is back. One limit to know: today a
  verification record is tied to the whole candidate, so every later integration step makes every record "changed" and
  the checker has to re-issue them; a follow-up ties each record to its own lines only, queued behind the integrations
  you ordered.
- Concrete, two annex-edge columns: checked and merged; the checker confirmed from the drawings that they start at
  +0.25, so their concrete is 1.43 m3 where the candidate carries 1.24 m3 (-13.5 %). Verified as a piece, not yet in the
  candidate.
- Column rebar inside the foundations: checked and merged as a lower bound only (26 cores at least 734.8 kg, -8.3 %
  against the old figure; 10 cores held). Freelancer comparison: not measured for this item.
- Concrete, exterior ground beams, handed in, waiting for the checker (a material finding): three main-house exterior
  beams are carried in the candidate as interior beams, at the shallower interior depth. On the drawn runs at the
  printed 0.95 m depth the main-house exterior ground beams are 15.96 m3, against 8.16 m3 in the engine (+7.80 m3,
  +95.5 %). The annex beams (4.97 m3) stay blank: both their depth and their drawn length conflict; the three courtyard
  beams stay held. Second-floor columns stay held (carried to the finished roof level, not to the structure).
- Floor area: the small pantry zone by the kitchen counter (1.10 m2) is settled from the drawings as a wet floor, no
  designer question needed (candidate floor 380.36 -> 381.46 m2, +0.29 %, once checked and integrated). Waiting for the
  checker.
- Excavation and backfill (missing from both the engine's and the freelancer's BOQ): 26 footings matched; pit plan areas
  129.23 m2 and the footing footprint 109.85 m2 (= the checker's earlier figure); every volume held, because the drawings
  print only "not less than 1.5 m" for the formation. Finished, waiting for a checker slot.
- Team: two worker runs found nothing to claim (my planning gap: every open row was in the integration lane). Four new
  preparation pieces now feed the integration lane (stairs and domes, block walls, plaster and paint, formwork), so the
  workers stay busy without new research.
- Nothing new on Drive; no new photos.

Since 04:15 (newest first; four pieces checked and merged, one sent back narrow, the first real export handed in):
- The first real export of the candidate BOQ is handed in for the checker: one project identity and one drawing revision
  set over the structural and architectural drawings, every quantity unchanged, one command gives the spreadsheet and csv
  (3,699 rows; 1,878 held rows blank, never zero). The cause of the run-to-run file difference is found: the local file
  name of the structural drawing copy was written into the output; verification records now bind to the quantities
  themselves, so a harmless re-run no longer looks like a change. The checker must still run the full test suite (the
  worker could not), write the verified-line records and show the four lines with an unsupported depth or height as held.
  Metric tons as the default unit is not in this hand-in (allowed to follow).
- Merged: ceilings revision 3 (flat decorative ceiling 361.23 m2, -10.4 % against the released 403.16 m2 and -11.8 %
  against the freelancer's 409.58 m2), checked together with the new stair soffits so that every square metre under the
  stairs belongs to exactly one line; stair soffits (main stair about 17.2 m2 true area, second stair 8.5 m2 on plan,
  winder and curved parts held); block-wall register revision 4 (449.60 m2 minus 7.91 m2 for every metre the sunken roof
  panels drop; the drop is held, not guessed; 297.85 m2 on 18 walls checker-verified); a code-hygiene declaration.
- Buried ground-beam waterproofing coat: the checker re-measured all 32 faces himself (45.47 m2 against 45.47 m2,
  +0.008 %). That part is verified; the line as a whole stays partly verified because the faces whose depths the drawings
  do not print stay blank.
- Column rebar inside the foundations restated on the printed level chain: 26 cores fall from 801.3 to 734.8 kg
  (-66.5 kg, -8.3 %) as a lower bound, because the old figure left out the 17 cm under the footing; 10 cores (173.5 kg)
  stay held. Waiting for the checker. Freelancer comparison: not measured for this item.
- Designer list: of three open gaps, one is settled from the drawings (two columns at the annex edge start at +0.25, so
  their concrete is 1.43 m3 where the candidate carries 1.24 m3, -13.5 %); the stair winder and the tower dome stay on the list. Waiting for
  the checker.
- Sent back narrow: the scoring guard against sealed files missed two side files the census reads; a small fix.
- Nothing new on Drive; no new photos.

Since 02:15 (newest first; one integration step checked and merged, three pieces handed in, one finished and waiting):
- Foundation waterproofing is now in the candidate: checked line by line and merged. The candidate gains its own
  foundation waterproofing family: footing membrane 109.85 m2, its protection screed 109.85 m2 (5.49 m3), lift-pit
  membrane 47.43 m2, board 26.73 m2 and screed 20.70 m2 (1.04 m3), all verified by the checker himself; the buried
  ground-beam coat 45.47 m2 (32 faces, the newer face-by-face trace; 9 of the 32 faces checked by hand so far, so the line
  is partly verified); 11 lines whose depths the drawings do not print stay blank, never zero. Every one of the other
  3,680 candidate lines is unchanged. Neither the released engine nor the freelancer has these lines (his waterproofing
  covers wet areas and roofs only). Not released.
- The checker found that the candidate's json output changes slightly from run to run although every quantity column is
  identical. Harmless for the numbers, but a verified-line record tied to that file would look "changed" after a re-run;
  the first real export (next in the integration lane) must tie verification records to the quantities themselves.
- Handed in, waiting for the checker: ceilings revision 3 (flat decorative ceiling 361.23 m2, -10.4 % against the released
  403.16 m2 and -11.8 % against the freelancer's 409.58 m2; 1.94 m2 of stair flight hidden behind beams moved to the stair
  zone, held); the formwork end-face fix, third hand-in (the beam that runs into the open outline has no end face there,
  and the same cause removed ends on the lift-pit ring); a code-hygiene declaration of which modules may use the CAD and
  geometry libraries.
- Stair soffits measured flight by flight for the first time (neither the engine nor the freelancer has this line): main
  stair about 17.1 m2 on plan, 17.2 m2 true sloped area, one flight with a drawing conflict (3.2 to 3.9 m2) and the
  winder turn held; second stair 8.5 m2 on plan, its curved part held. Finished but held back because three pieces are
  already waiting for the checker; it will be checked together with the ceilings, since both share the stair zone (the
  two pieces must give every square metre under the stairs to exactly one line).
- Nothing new on Drive since the last report; no new photos.

Since 00:15 (newest first; two pieces checked and merged, one sent back narrow, a large block-wall check by the checker):
- Block walls, checked wall by wall by the checker himself: Checker-verified wall area rose from 105.00 to 297.85 m2 on
  18 walls (of 449.59 m2 settled), including the largest wall (62.16 m2) and four first-floor walls to within 0.01 m2.
  It also found a real error: six ground-floor roof panels are sunk (lowered by a depth the drawings do not print), and
  7.91 m of ground-floor wall under them was measured up to the normal ceiling height. Those pieces are held by that
  unknown depth (7.91 m2 less for every metre of drop; the drop itself is held, not guessed); one wall that was already marked
  verified was taken back. The slab concrete is not affected. The register gets one more revision before the walls go
  into the candidate, and the drop is now listed against walls, beam tops, formwork, fill and waterproofing on the
  designer list.
- Block-wall register: the closed height pieces were applied as one revision: settled net 449.26 -> 449.59 m2. Checked
  and merged.
- Floor-area scoring key: checked and merged. The scoreboard now scores the candidate's internal floor at 380.36 m2
  (-7.1 % against the freelancer's 409.58 m2). The checker confirmed the first-floor landing is counted once; he also
  found that the landing's marble (your earlier decision: landing in marble) has no material line in the candidate:
  added to the stairs step into the candidate.
- Formwork end faces: sent back narrow a second time on one row (a beam that runs on into an open outline was taken as
  a free end); everything else agrees.
- Designer list: two rows corrected from the checker's reading (the sunken-panel row now names what the drop really
  moves; the blinding request closes only together with the footing request). Still not ready to send.
- Nothing new on Drive since the last report; no new photos.

Since 22:15 (newest first; three pieces checked and merged, two sent back for narrow fixes, one handed in):
- Block walls: every wall's height pieces now add up exactly to its length (the old register sampled the band every
  2 cm and averaged, so 40 of 73 walls did not close). Checked and merged. The settled wall area would move from 449.26
  to 449.57 m2; nothing applied yet: the register is applied in one revision next, then the walls go into the
  candidate. Checker-verified wall area rose from 95.63 to 105.00 m2 (13 walls). The one window that sat 3 cm inside a
  column is the only such case in the 78-opening census.
- Buried-concrete waterproofing, second hand-in: checked and merged. 32 buried ground-beam faces, 45.47 m2, every beam
  end now stops on the face of what it frames into. Neither the released engine nor the freelancer has this line.
- Foundation waterproofing into the candidate: sent back narrow on one sub-line only. The checker confirmed the footing
  membrane 109.85 m2, its screed 5.49 m3 and the lift-pit layers himself; but the buried-beam figure carried (35.40 m2)
  came from the older trace that contained non-earth faces. Being redone with the 45.47 m2 trace.
- Beams drawn wider or narrower than their schedule: checked and merged. 7 of 137 runs conflict, exactly the ones on the
  designer list; beam concrete on them 5.44 m3 as drawn vs 5.77 m3 as scheduled, both kept until the designer answers.
- Formwork faces where beams end on columns or curves: sent back narrow. Side faces agree with the checker, but end
  faces were invented on lines joining two unequal beam-edge ends (0.22 m2 of a 0.34 m2 alternative was not real).
- Floor-area scoring key: fixed and handed in. The scoreboard will score the candidate's internal floor area at
  380.36 m2 (-7.1 % against the freelancer's 409.58 m2) instead of 372.47 m2; a scoring fix, no quantity changed.
- Nothing new on Drive since the last report; no new photos.

Since 20:15 (newest first; four pieces checked and merged, one sent back for a narrow fix, two handed in):
- Ceilings, ground-floor light well: fixed and merged. The checker split the 23.24 m2 face himself and agrees to
  0.001 m2: 13.39 m2 is the open light well, 1.55 m2 a small shaft (no ceiling), 0.89 m2 ordinary slab, and 7.40 m2 is
  the underside of the upper stair flights and landing, which is a stair soffit, not a decorative ceiling. Flat
  decorative ceiling now 363.17 m2 against 403.16 m2 in the released run (-9.9 %) and the freelancer's 409.58 m2
  (-11.3 %); not verified as a whole yet (first-floor rooms, domes and second floor not re-checked). Stair soffits are a
  scope no line carries yet: new work measures them flight by flight.
- Reinforcement laps and tons: merged with your acceptance points (the four boundary lengths at a 1.2 m lap, every
  column lap checked against its starter bars with no double count, the five detailing categories). Every lap stays
  held; effect on Alsenan 0.000 t. The worker found that the lower bound of the column cores starts from the
  excavation level instead of the footing top (the 17 cm of blinding and screed is ignored, about 74 kg): a new
  correction task.
- Ground-beam stirrups and the stair finish-level registration: merged (counts and weights stay held).
- Buried-concrete waterproofing, traced face by face: sent back narrow. The trace found 46.52 m2 of buried faces, but
  where a straight beam frames into the curved ring it cut the beam square and counted 0.37 m of ring face that is
  actually against concrete, and it took a 0.05 mm drawing offset beside a column as a beam face (0.59 m2). Held until
  fixed (at most 45.61 m2 on what the checker checked). The same drawing situation can mislead formwork, so the
  formwork ledger gets the same check.
- Block walls, checked by the checker himself: one first-floor wall nets 12.935 m2 against the register's 12.863 m2; the
  register deducts a window over its full width although 3 cm of it lies inside a column already taken out of the wall.
  The register fix is next in the queue.
- Handed in, with the checker next: foundation and lift-pit waterproofing into the candidate (a scope missing in the
  released run and in the freelancer's BOQ), and the census of beams drawn wider or narrower than their schedule (7 of
  137 runs conflict, all already on the designer list; beam concrete 5.44 m3 drawn vs 5.77 m3 scheduled on those runs).
- Nothing new on Drive since the last report; no new photos.

Since 18:15 (newest first; two pieces checked and merged, one checked and passed waiting for its merge, two sent back
for narrow fixes):
- Ceilings, rebuilt room by room on the checked floor pieces: 362.28 m2 of flat decorative ceiling against 403.16 m2 in
  the released run (-10.1 %) and the freelancer's 409.58 m2 (-11.6 %), plus 29.24 m2 of beam bulkhead faces by your
  manual method. Sent back narrow: over the ground-floor light well the work deducted 23.24 m2 as "no ceiling", but the
  slab plan opens only 16.01 m2 there (the released engine's figure, to the millimetre); the other 7.23 m2 is drawn slab
  with its own bar text. Being fixed: each of those strips classified by what is under it. Lesson recorded: an area
  bounded by beams is not an opening; the opening is what the slab plan marks as one.
- Ground-beam stirrups, second hand-in: links are now counted between the faces that support them, never through a
  crossing beam. The checker re-measured three runs and the curved ring from the drawing himself and agrees (ring 35 to
  44 links; the checker withdrew his own earlier 40 to 45, which used a fixed allowance at the columns). The whole
  count stays a held range (333 to 392 links on the outer beams) and the steel weight stays held, because the hook
  tail and bend are not printed. Passed; merged after the stair file below.
- Block-wall blockers settled from the drawings: merged. 11 walls re-measured by the checker, all agree to the
  millimetre. The settled net area would rise from 449.26 to 625.56 m2, but nothing is applied to the BOQ yet: the wall
  register first has to make every wall's height pieces add up to its length, then the walls go into the candidate.
- Floor area in the candidate: merged. The candidate's internal floor area is 380.36 m2 against 385.63 m2 in the released
  run (-1.37 %; the released run counts 6.24 m2 of stair footprint as living room). The scoreboard currently scores it
  at 372.47 m2, because its key does not yet pick up the dressing room and the arrival landing (7.89 m2): a scoring gap,
  not a quantity error; a fix is queued.
- Reinforcement laps and tons: the lap count method and the export in metric tons agree with the checker, but your
  acceptance points (the four boundary lengths at a 1.2 m lap as tests, the column laps against their starter bars, the
  five detailing categories) arrived after the hand-in; sent back narrow to add them. Every lap length stays held (no
  drawing names it for the beam bars); the effect on Alsenan is 0.000 t.
- Stair finish-level file: the one missing registration was added and is with the checker now.
- Nothing new on Drive since the last report; no new photos.


Since 16:15 (newest first; one piece checked and merged, two sent back for narrow fixes, one integration handed in):
- Waterproofing of buried concrete: a scope nobody carried. The structural detail asks for two coats of liquid
  waterproofing on every concrete surface in contact with earth. Neither the engine nor the freelancer has a line for
  it. Measured face by face from the sections: 35.40 m2 of ground-beam faces (11.34 m2 on the interior beams, 24.06 m2
  on the house side of the outer beams; their outside faces stand above natural ground and are not coated). The checker
  re-measured two runs himself and agrees. Footing tops and necks stay held until the foundation level is settled (your
  earlier answer path); the boundary beam stays held on the note's scope. Not yet in the candidate: queued after the
  floor-area step.
- Block walls, checked by the checker himself: 16 of the 37 walls with a settled net area are now re-measured, and
  95.63 m2 of the 449.26 m2 settled net is verified (67.57 m2 two hours ago). One wall cannot settle from the drawings:
  the beam over its end is drawn 25 cm wide but scheduled 20 cm (a 0.02 m2 difference on that wall, but the same kind of
  conflict changes beam concrete and formwork), so it goes to the designer list and every beam is now being compared
  drawn-against-schedule.
- Block-wall blockers settled from the drawings: second hand-in, 7 of 9 walls agree with the checker; two walls took a
  wall-register height over a length where no beam or slab edge is drawn. Being fixed now.
- Ground-beam stirrups: shape, hooks and cover agree with the checker, but the link count assumed links continue
  through crossing beams. Sent back to count per drawn span between supports; count and weight stay held, never 0.
- Floor area in the candidate: the next step is handed in (internal floor 380.36 m2 vs the released 385.63 m2, -1.4 %,
  every m2 named; under-stair, a band, the pantry doorway zone and part of the pantry still held). The checker takes it
  next.
- Team: one worker skipped two small fixes because they were labelled "rejected" rather than "to do"; corrected, and
  every fix the Lead orders is now labelled "to do".

Since 14:15 (newest first; three pieces checked and merged, two sent back for narrow fixes):
- Block walls, checked by the checker himself: 9 of the 37 walls with a settled net area are now re-measured from the
  drawings, and 67.57 m2 of the 449.26 m2 settled net is now verified (it was 4.46 m2 two hours ago). Seven walls agree
  to the millimetre. On two first-floor walls the wall register is off by -0.030 m2 and +0.017 m2: its height pieces do
  not add up to the wall's own length (one beam strip taken as 0.46 m where the drawing gives 0.403 m, one 0.125 m
  strip missed). Tiny in area, but it is a rule fault, so a correction with a check over all 76 walls is queued.
- Block-wall blockers settled from the drawings: the hand-in would add 149.3 m2 of wall whose height and openings the
  drawings already print (settled net 449.3 -> 598.5 m2). Sent back once: on two walls the leftover length at the end of
  the wall was given the height of the neighbouring beam instead of the beam actually over it (-0.29 m2 on one wall).
  Being fixed now.
- Aluminium doors line: in the candidate at 12.76 m2 / 6 doors vs the freelancer's 12.00 m2 (+6.3 %, explained door by
  door; your 2.20 m height rule, the measured widths, and one door he did not count).
- Ground-beam steel: checked and merged: boundary beam at least 315.6 kg and the outer main-house beams 995.4 kg
  (796.3 kg top / bottom bars + 199.1 kg side bars; all 17 runs agree with the checker's own lengths). Stirrups and laps
  stay held: no bend, hook or lap length is printed for them, and none is assumed.
- Checking tool: comparisons between two candidate versions are now pinned to the exact drawing files by fingerprint,
  never by file name; a change in an already-verified line is flagged.
- Your stair finish-level method (first riser, last riser, finishes on every surface): the module is built and the
  checker confirmed every formula by hand, level by level (your examples and Alsenan: 186.667 / 166.667 / 146.667 mm on
  the ground-to-first flight, 188 / 148 mm upstairs). Sent back for one housekeeping fault only: the new rule file was
  not added to the rule list the repository checks. No quantity changed.
- Your reinforcement decisions (tons in the final BOQ, laps only from the governing drawing note) are now a task in the
  structural lane, after the stair method fix.

Since 12:15 (newest first; four pieces checked and merged, one sent back once and fixed within the hour):
- Who owns which opening: three openings were tied to the wrong room by name (two bathrooms swapped). The checker
  re-traced the rooms from the wall geometry: the quantities were already right (0.000 m2 change in every trade), and the
  rule is now that an opening belongs to the room its jambs bound, never to a name.
- Stairs and domes: the closable part is now one settled figure, 10.805 m3 (8.344 verified, 0.925 confirmed on the
  drawing, 1.536 on your approved rules). The first hand-in was sent back: where the ground-floor flight lands, a small
  wedge (0.03 m3) sat inside the ground slab and was counted nowhere. The fix gives 0.026 m3 to the slab and keeps 0.006
  m3 in the stair. The rest of the stair / dome line still waits for the structural consultant (curved stair, unprinted
  waists, one dome).
- First-floor living room floor: the checker confirmed 38.63 m2 himself. The released run says 44.87 m2 (6.24 m2 too
  much: it counted stair and landing areas as floor); the freelancer has 38.96 m2 (-0.84 %). Of the round-stair treads
  over the pantry, 2.07 m2 is floor (under the flights above); 6.12 m2 stays held until the curved stair's structure is
  drawn.
- Formwork: the update for the members changed since the last formwork pass agrees with the checker's own lengths
  (ring beam, boundary beam, 47.66 m2 of outer ground-beam faces above ground). Formwork has no freelancer row to compare.
- Ground-beam steel: handed in for checking: the boundary beam at least 315.6 kg (2 bars top, 3 bottom, read layer by
  layer from the drawn bars), the outer main-house beams 796.3 kg top and bottom bars. Stirrups and side bars are held:
  no bend or hook length is printed, and the engine will not assume one.
- New work queued: interior ceilings (no ceiling quantity exists yet in any run; your gypsum-ceiling rule applies) and
  the ground-beam stirrups / side bars, measured only from what the drawings print.

Since 10:15 (newest first; five pieces checked and merged, none sent back):
- Aluminium doors: the checker measured the four held doors himself on both wall faces: three are aluminium (they open
  to the court, the open side passage and the outdoor landing) and the fourth is 0.90 m wide, not the 1.00 m of its block
  frame. The line becomes 12.76 m2 / 6 doors against the freelancer's 12.00 m2 (+6.3 %, explained door by door: your
  2.20 m height rule takes 1.00 m2 off, the widths 0.44 m2, and he counts one ground-floor door fewer than the drawing
  shows, +2.20 m2: engine right). It goes into the candidate in the next integration step; then it can close as a whole.
- Block walls: the wall register passed after one fix. Three wall pieces under the stair shaft are now held on every
  floor (no floor slab is drawn there at the upper storeys), so the area measured with confidence drops 494.19 -> 449.26
  m2 (-9.1 %). Nothing is lost: those metres are held with the reason, not dropped. 39 of 76 walls still have a held net.
- Foundation waterproofing (a scope missing from the engine AND from the freelancer): the checker measured it himself:
  membrane under the 24 footings 109.85 m2 with a 5 cm protection screed 5.49 m3, and the lift-pit layers (membrane 47.43
  m2, board 26.73 m2, screed 1.04 m3). Still held: one footing pair, the pit walls and the footing sides (which detail
  applies depends on the formation). It goes into the candidate as its own lines next.
- Plaster / paint: every room face is now tied to its wall on the drawing (no quantity change; it settles which room
  each opening belongs to).
- Outer ground beams of the main house: the checker measured all 17 runs himself: 15.969 vs 15.960 m3 (+0.06 %); one
  tiny 0.003 m2 strip is unconfirmed, so this part is 16 of 17. The ground-beam line as a whole still waits for the
  consultant.
- Floor area: the first of four integration steps is done (internal floor 340.76 -> 342.66 m2, +0.56 %: the dressing room
  added, three sills moved out to thresholds); one strip was found counted twice and is fixed in step two.

Since 08:15 (newest first):
- Concrete slab: the slab / beam move into the candidate passed the checker's full integration check. The candidate
  slab line is 60.2801 m3 against his own 62-panel measure 60.2804 m3 (a difference of 0.3 litres): the whole line is
  VERIFIED. Against the freelancer's 59.82 m3 it is +0.77 % (first floor: the engine is right at the dome corners; ground
  and second floor: a rule difference). The released run still says 61.55 m3 (+2.11 %): that stays a known discrepancy
  until you decide to release a method that carries the candidate line. Beams moved in with it: 66.32 m3 measured, plus
  5.14 .. 6.11 m3 where two drawings disagree and 3.23 .. 7.67 m3 held on designer items, plus 5 runs with no figure.
- Block walls: the wall register was sent back. The checker found that a 2.5 m stretch of a first-floor wall stands
  under the stair-shaft beam (printed "B3 (With Stair)"), where there is no first floor on that line; the same package
  had already held the identical stretch on the ground floor, but not its twin upstairs. A narrow fix (hold that piece,
  keep the rest) is first in the architectural lane; the team also adds a check so a finding on one floor is applied to
  the same printed condition on every floor.
- Openings to rooms: the geometric check is complete (59 openings, both sides of every one settled): 5 were linked to
  the wrong room by name; no total changes (the rooms involved have equal deductions), but room-by-room lines now
  follow the drawing. Waiting to hand in.
- Your workflow approval (10:02) is applied: the next lines that can close are worked first. Next: floor area (the
  remaining pieces are named and split into four short steps), then aluminium doors (the evidence for the 4 held doors
  is complete and goes to the checker now as the one extra hand-in allowed). Windows stay blocked on your W17 answer
  and one designer item.

Earlier, since 06:15 (newest first):
- Ground beams: the checker measured the boundary ground beam himself from the drawing (5 runs, 44.07 m, 20 x 40 cm at
  natural ground): 3.53 m3, the same to the litre. Neither our released run nor the candidate has it today (a real
  omission); the freelancer has it at a bigger section (7.56 m3). He also confirmed, from five printed level marks, that
  the outer ground around the main house is natural ground +-0.00 (the +0.15 in the courts is paving): that makes the
  main-house exterior ground beams 0.95 m deep, 15.96 m3, drawing-confirmed (he measured 6 of the 17 runs himself; the
  rest rest on geometry he verified earlier). The annex depth still conflicts between two prints and stays a range.
  Checked and merged; going into the candidate next after the slab move.
- Columns: the 15 columns whose drawn size differs from the schedule stay a range (8.03 .. 10.12 m3): no third
  drawing settles any of them; they go to the designer (two under the existing item, 13 under a new one). Five upper
  columns that the released run carries (2.27 m3) are drawn on no floor plan at all: they will be removed from the
  candidate as "not present", never shown as 0. Checked and merged.
- Test-infrastructure follow-ups: checked and merged; nothing in the quantities moved.
- Handed in, waiting for the checker: waterproofing under the footings, drawn on the structural sections but in no BOQ
  line and no freelancer row (membrane 109.85 m2 + protective screed 5.49 m3, plus the lift-pit layers); the wall-face
  crosswalk for plaster / paint (every metre of the 465.39 m room perimeter placed on its wall); the block-wall
  register (oldest, first in the checker's next run).
- Found: four windows / doors are linked to the wrong room by name (no total changes today, but room-by-room
  deductions would be wrong): a geometric fix is now first in the architectural lane. The candidate also releases one
  stair flight computed on a standard riser and waist that no drawing prints, while it holds stair parts the checker
  already verified: a correction is queued behind the stairs check.
- New work: waterproofing of all buried concrete (drawn, not yet measured), formwork for the members that changed,
  and ground-beam reinforcement by bar count.

Earlier, since 04:15 (newest first):
- Footings in the candidate: one footing drawn as a single outline but labelled with two schedule types is now held as
  a range of both drawing readings (2.18 .. 2.28 m3) instead of one label's value; the freelancer's 1.96 m3 sits below
  both (designer question already open). The candidate's released footings are now exactly the 25 footings the checker
  verified one by one, 64.30 m3 (was 66.26 m3 with the unclear one inside). Checked and merged.
- Beams: the ring beam around the ground-floor void and two slanted beam ends corrected; the checker measured the ring
  himself from its arcs (0.666 m2 x 0.75 m deep = 0.50 m3). Beam ledger 66.02 -> 66.32 m3 against the freelancer's
  65.97 (+0.54 %, not yet agreement: his two beams run through a column, and one of his rows has no location). Merged.
- Family-register test fixed and green; nothing in the quantities moved. Merged.
- Waiting for the checker: the boundary ground beam (3.53 m3, missing in both runs today; the freelancer's 7.56 m3 used
  a bigger section) and a reading that settles the exterior ground-beam depth for the main house (15.96 m3 proposed);
  the block-wall register (established net walls 337 -> 494 m2, one wall fully verified, 38 still held with the
  missing item named); and test-infrastructure follow-ups (no quantity).
- Next work: the slab / beam move into the candidate (to close the slab line), the stairs and domes split into what
  closes now and what waits for the designer, evidence for the four held aluminium doors, and the block walls whose
  missing heights another drawing prints.

Earlier, since 02:10 (newest first):
- Columns: the checker re-measured all 28 columns that close from the drawings himself (outline on the drawing AND the
  printed column schedule): 18.35 m3, every one agrees (0.0 %). Two of them stand on the ground-floor roof slab with
  nothing below (1.01 m3); the released structural route leaves them out and the candidate holds one of them: the
  candidate fix takes them in. The other 31 columns stay a range or held (designer items, top-storey and annex roof
  levels); a new task narrows the 15 conflicting columns column by column.
- Doors and windows by pieces AND m2 are now in the candidate (checked and merged): windows 76.26 m2 on 27 windows
  against the freelancer's 80.23 m2 on the same 27 (-3.98 m2, -4.95 %, every metre explained by window heights). The
  two windows found missing earlier (the 28.25 m2 pool glass wall and a 1.08 m2 window) are already inside these 27:
  the pool wall agrees with the freelancer exactly. Still held: the curved first-floor window (your question) and one
  ground-floor window counted once or twice (designer). What remains for those two windows is checking that walls,
  plaster and paint take them off once.
- Window and door list from the drawings alone: checked and merged (29 windows, 27 doors, 1 gate, 2 arches).
- Beams: the last two calculated pieces (two small upstands, 0.12 m3 each) agree; the correction of the ring beam
  and the two slanted ends (+0.30 m3, 66.02 -> 66.32 m3) is handed in for the checker.
- The fix for the family-register test is handed in (the check now reads item codes from the register, the test is
  unchanged); no quantity moved.

Earlier, since 00:10 (newest first):
- Columns as a whole line (waiting for the checker): 59 columns and 36 necks, each once. 28 columns close from the
  drawings, 18.35 m3; 15 have a schedule vs drawing conflict (8.03 .. 10.12 m3, designer items); 16 are held (roof
  level of the top storey and the annex not printed). Necks are held at no less than 9.26 m3 on 32 of them, which is
  already above the freelancer's 8.81 m3 (he used the 1.50 m limit as the neck length). The checker counted the 59
  columns himself from the drawing, a second way: the count agrees. Found: the candidate carries the top-storey columns
  up to the FINISHED roof and the annex columns at an assumed 4.50 m; both must be held, a fix is queued.
- Doors and windows by pieces AND m2 in the candidate (waiting for the checker): windows 76.26 m2 on 27 windows against
  the freelancer's 80.23 m2 on the same 27 (-3.98 m2, -4.95 %, fully explained), the curved pool window held at 9.87 ..
  11.52 m2 (your open question), aluminium doors 4.18 m2 plus 1.98 .. 8.80 m2 held, against his 12.00.
- Window and door list built from the drawings alone (not from the engine): 29 windows, 27 doors, 1 gate, 2 arches;
  every one found again on the other side. Two windows (1.08 m2 and the 28.25 m2 ground-floor pool glass wall) are drawn
  but in no window line of either run: they go into the candidate next (+2 pieces, +29.33 m2; the pool wall then
  agrees with the freelancer exactly).
- Ground beams as a whole line: only 5 interior runs carry a single printed section; those 2.268 m3 are checked by the
  checker face to face. The rest wait on designer answers (tee sections, section titles, the exterior depth printed as
  'follow architecture'), held as 13.44 .. 15.96 m3 for the exterior, never 0. Found: the candidate counts 24 exterior
  beams (11.93 m3) at the interior depth, which the drawings do not support (fix queued); a boundary ground beam
  (up to 3.53 m3) is in no line of either run (being measured).
- Beams: the checker re-measured every calculated beam run storey by storey; all agree except two places where the
  ledger is short by 0.305 m3 (a ring beam around the ground-floor dome void taken as straight pieces, and two beam ends
  on a slanting beam). A correction is queued before the beam line goes into the candidate.
- Floor area: all 47 pieces now re-measured by the checker; 32 agree to 0.0 %. The 15 others need three classification
  fixes (9 doorway strips 4.12 m2, the pantry as a wet floor by your rule, the landing at the foot of the first-floor
  stair) besides the dressing room and sills already found; these are now one integration step.
- The red drawing-register test is fixed and merged. A second test (the family register guard) went red when the
  completeness check was merged at 00:10: the check names the handrail item, which the guard reserves for code that
  measures it. No quantity is affected; the fix is first in line and every hand-in now runs the full test suite.
Earlier, 22:10 -> 00:10 (newest first):
- Beams as a whole line, every one of 140 beam runs once: 66.016 m3 measured from the drawings, plus 5.145 .. 6.111 m3
  where the schedule width and the drawn width disagree (designer items) and 4.163 .. 8.673 m3 held (depths not
  printed), never shown as 0. The released run has 64.820 m3; the difference is closed to named causes (two first-floor
  beams the released run cuts at planted columns +2.670, held pieces by their printed sections +2.408, one beam band
  the released run counts as slab +0.296, beam / slab joints counted twice once removed, a ring beam +0.474, and the
  conflicting widths now shown as ranges -5.022). The freelancer's 65.966 m3 is within 0.08 % of the released total,
  but that is a coincidence: 6 beam marks (9.883 m3) are missing from his sheet and are offset by lengths he takes
  through the supports. The checker re-measured three beams himself (0.0 %): the beam line is PARTIALLY VERIFIED.
- Completeness against drawn inventories that do not come from the engine: footings 25 of 26 drawn (one pair carries
  two tags on one outline: being read), slab panels 62 of 62, column necks 36 of 36, columns 59 of 59 (the released
  run still carries 2.268 m3 on 5 upper columns that no storey plan draws; the candidate holds them), doors 27 of 27,
  windows 27 of 29: two windows (1.08 m2 and the 28.25 m2 ground-floor pool glass wall) are in no window line of either
  run. The window list itself was built from the engine's own opening list, so it will be redone from the drawn tags.
- Plaster and paint are in the candidate for the first time (checker passed it): 166.88 m2 of paint on rooms the checker
  measured himself, 8 rooms held as ranges with named causes. A cross-check of every wall face between the block,
  plaster and window records (75 faces) found 0 double deductions and narrows the drawing net to 1,449.99 .. 1,560.92 m2
  (held openings 27 -> 11); it is not in the candidate yet. Three items stay held: the room side of the curved pool
  glass wall, one wedge-shaped wall and 18 faces under the first-floor roof whose two height readings disagree.
- The curved first-floor room is measured right by the engine (19.017 m2 on the curve, checker 19.0165); the small
  dressing room goes into the floor line, the ground-floor side passage (5.64 m2) is outside, the sills are thresholds.
- The arched-opening fix is merged (two first-floor arched windows 4.650 m2 each as window, 4.363 m2 as hole in the
  wall; one second-floor arched window 1.875 m2 as hole). The checker confirmed what the 0.45 m above the curved window
  over the pool is: a separate decorative band, not the window. That makes one of your earlier answers rest on a
  height our own question gave you: the question is below.
- The one-command BOQ export (spreadsheet + CSV + manifest, every quantity state in its own column, unknown = empty
  cell, never 0) is merged; on the real candidate it refuses, correctly, because the structural and architectural
  drawing sets carry two different project identities: a fix is first in line after the doors / windows step.
- One check on the working branch has been red since at least yesterday 21:00 (the drawing-register test: its saved
  output no longer reproduces). No quantity depends on it; it is now the first task of the architecture worker.
Earlier, 20:10 -> 22:10 (newest first):
- Whole slab line measured panel by panel for the first time (62 panels, 375.05 m2): 60.280 m3 from the drawings, and
  the line can close from the drawings alone (waiting for the checker). The released run has 61.551 m3, +1.271 m3
  (+2.1 %) too much, for two named reasons: the roof-tank slab thickness (0.18) was applied to five neighbouring panels
  that carry no thickness tag (+0.625 m3; the general note gives them their thickness), and 13 pieces that are not slab
  were counted as slab (+0.646 m3). The freelancer's 59.817 m3 is 0.463 m3 (0.8 %) below, explained floor by floor
  except 0.059 m3 in his first-floor lump figure, which has no breakdown. Not measured yet: the matching beam line.
- Floor area, checker's own room-by-room re-measure: 20 of 47 pieces agree to 0.0 %. Two findings keep the line from
  closing as released: a 2.970 m2 dressing room between a first-floor bedroom and its bath is in no floor line (the
  freelancer is right to include it), and 0.550 m2 of lift-landing / exterior sills are counted as porcelain floor
  although they are thresholds. Net +2.42 m2 (+0.6 %). The curved first-floor room is measured correctly by the engine
  (the curve, not the straight wall line, which is where the freelancer's +1.68 m2 comes from).
- Arched openings re-read on the drawing (68 openings): the two first-floor arched windows are 4.650 m2 each as window
  area by your rule (the freelancer is right) and 4.363 m2 as the hole in the wall for plaster and paint; one second-
  floor arched window is 1.875 m2 of hole, not 2.04; windows on the same 7 openings now 45.10 vs his 45.48 m2 (-0.8 %,
  was +3.4 %). The curved window over the pool stays held (9.87 .. 11.52 m2) until the checker confirms what the 0.45
  above it is (the arch or a decorative band); if it is a band, you will get one short question, because your earlier
  answer quoted a height that our own question had supplied.
- Plaster and paint handed in for the candidate room by room (waiting for the checker): paint 166.88 m2 released on
  checked rooms, 529.47 .. 595.05 m2 held as ranges with named causes, four pieces held without a figure.
- Block walls step 3 merged (the arched window now deducted by its true outline: wall net 12.863 m2); the roof / terrace
  falls are measured from the drawn outlets (0.19 .. 0.20 m rise on the +5.50 terrace), wet-room and sunken tops held.
Earlier, since 18:20 (newest first):
- Footings and blinding as whole lines (checker re-measured every footing outline itself): 25 footings 64.304 m3 =
  released = both candidates (0.0 %). The freelancer's 65.634 m3 is explained to the cubic metre: +1.960 one footing he
  prices at its schedule size that the drawing draws differently (held: a designer item, 2.176 .. 2.275 m3), -0.672 one
  footing type he counts once but the plan draws twice, +0.042 one small footing piece he counts twice (the drawing
  shows the larger footing owns it; this designer question is now ANSWERED FROM THE DRAWING and leaves the consultant
  list). Footing blinding 15.179 m3 (checker 0.0 %), of which 0.189 m3 lies beyond the plot line (held, designer item).
  His 47.055 m3 blinding is a whole-plot plate (15.00 x 31.37 x 0.10), a different rule, not an error. Both lines are
  PARTIALLY VERIFIED, not verified: the one held footing, the strap blinding and ground-beam blinding (designer items)
  remain.
- Floor area is scored for the first time on the released run (see above); the candidate stays held by 0 .. 0.52 m2 at
  the first-floor stair foot (designer items), never shown as 0. The candidate already floors the three hand-wash spaces,
  so the 9.348 m2 owner-approved addition is counted once, not twice.
- Block walls step 2b (checker-verified piece): the masonry above the 1.20 m ground-floor court opening is 2.640 m2
  (checker 0.0 %); the curved first-floor bay ends are wall, not glazing (+1.48 m2); one of the two opening questions
  for the consultant is answered from the drawings and leaves the list; the other is narrowed to its head level only.
- Block walls step 3 SENT BACK for one wall: the arched first-floor window W16 (and its twin W15) was deducted as
  1.55 x 3.10 = 4.805 m2, reading the top of a 10 cm decorative band around the arch; the real arched opening is
  4.362 m2 (+0.443 m2 too much deducted per window). The other three walls agreed. The same misreading sits in three
  merged opening records; the window AREA by your rule is 1.55 x 3.00 = 4.650 m2 (the freelancer is right there).
  A fix task corrects all of them and checks every other arched or banded opening before plaster, paint, doors and
  windows go into the candidate.
- Candidate step 8 merged (checker Gate B): verified straps 3.39 m3 (freelancer 3.39, -0.06 %); columns 34.45 ->
  33.61 m3 (two planted columns held, five undrawn upper lines shown held).
Next (from 00:19): the integration worker puts doors and windows into the candidate in pieces AND m2 (with the arched
window fix; the curved pool window held until you answer), then one footing conflict, the single project identity for
the export, and the slab / beam split (which closes the slab line); the architecture worker fixes the red check first,
then rebuilds the window list from the drawn tags; the structural worker closes the ground beams and then the columns
and necks as whole lines; while nothing waits for it, the checker finishes re-measuring the floor area (21 pieces left)
and starts the beams storey by storey.

Earlier (16:20 -> 18:20):
- Block walls (your programme, step 2 of 4, checker-verified): the first block wall is now INDEPENDENTLY VERIFIED: a
  ground-floor 20 cm white wall, 4.458 m2 net (the worker had 4.468; the checker's drawn-edge pieces are 0.010 m2 lower).
  A first-floor 20 cm white wall's gross area is verified at 23.223 m2 (net 19.303 m2 waits on one window height being
  re-measured). The other three walls the step raised keep their status (drawing-supported or held): the checker
  re-measured the beam depths but not every piece. Total wall length did not change (the new area is height on length
  already in the census, as your main chat checked). One wall's net (47.4 m2 with the window heads found this morning)
  waits for the checker's ruling at 18:49. Step 3 (annex, lift walls, remaining window heads) is ready: it gives a
  figure to four more walls (+126.8 m2 net drawing-supported) and finds the annex roof and the lift tie beam undrawn on
  every sheet it read.
- Beams at the planted columns (checker-verified): the two first-floor beams that carry planted columns are 4.19 and
  4.09 m3 drawn, against 3.34 and 3.79 m3 released plus held (they were cut at the planted column); across 127 beam
  pieces, 1.82 m3 of drawn beam concrete is in no line and 0.28 m3 is billed twice. Not yet in any BOQ (a later candidate step).
- Strap and ground-beam ends (checker-verified): three ground beams the released run stops at the lift footing in fact
  run to the lift pit wall (+0.28 .. +0.39 m3); one deep strap entering a shallower footing holds 0.03 .. 0.27 m3 (a
  designer item); every intersection is now owned by exactly one element.
- Candidate step 8 is ready for the checker: verified straps at 3.39 m3 (freelancer 3.39, -0.06 %); released columns
  in the candidate 34.45 -> 33.61 m3 (two planted columns held, five undrawn upper lines shown held); it found the three
  planted columns were already in a route line, so they replace it rather than being added twice.
- Consultant list: 8 of 12 rows are ready to send (each a printed conflict or an element no sheet draws); 4 are held
  back until a search finishes (tank beam: architectural sheets not yet recorded as searched; lift tie beam and annex
  roof: waiting for the checker on step 3; two openings: the next architectural task).
Next: the checker takes the candidate step, then blockwork step 3; plaster and paint go into the candidate right after
(two more trades become scoreable); the structural worker starts the first two concrete lines that need no consultant
answer (footings and blinding), then the roof / wet-room structural tops and the whole slab line.

Earlier (14:20 -> 16:20):
- Block walls (your blockwork programme, step 1 of 4, checker-verified): the freelancer's figures, the older automated
  run and the current engine were compared wall by wall. The older automated run never produced block m2 (wall lengths
  only), so there is no automated area to compare. The two open gaps are explained to the wall: black 15 cm 3.464 m2 =
  two first-floor walls whose openings are deducted while their gross is still held; black 20 cm 12.001 m2 = two walls
  (first floor, second floor) less three openings. Rule learned: an opening deduction keeps the status of its wall.
  Of the 74 walls, 252.8 m2 net rest on the drawings, 84.6 m2 are project-specific, none yet independently verified;
  44 walls are held (377.9 m2 gross, never shown as 0) for named reasons (annex datum, beam depth, held openings, lift
  tie beam). No 10 cm block wall exists on the drawings. Steps 2 and 3 (wall heights from the drawn beams; annex, lift
  walls, openings) are next for the architectural worker.
- Black block units (your 12.5 per m2 provisional rule): 290.05 m2 net -> 3,626 installed blocks (replaces the 563 m2 x
  12.5 = 7,040 gross figure) and 3.61 m3 laying mortar from the joint geometry; PROVISIONAL until the supplier's block
  size and joint are on record. Waste, cement and sand stay held (no approved allowance or mix).
- Angled strap beams (your axis-length rule): your 2.29 / 3.26 m confirmed from the drawing (2.2927 / 3.2580 m); strap
  concrete 3.39 m3 vs the freelancer's 3.39 (-0.06 %); released 3.78 m3 is too high. One strap is printed deeper than
  the footing it enters (0.03 .. 0.12 m3 held).
- Columns: the checker has now measured 29 of 59 columns itself (0.0 %). One planted first-floor column is measured and
  verified (0.588 m3); the other two stay held (owner split / size conflict). The 5 upper-floor column lines (2.27 m3)
  are confirmed NOT DRAWN on any slab plan: a consultant item, never priced as drawn.
- Candidate coverage register: now shows the pool (7.20 m3) and domes (5.08 m3) as integrated in the candidate.
- Safety test on the working branch is green again (it had been red about 14 h with no quantity effect).
Next: the verified straps and planted column go into the candidate (step 8) before the formwork / railing step; two new
structural tasks check where beams are wrongly cut at planted columns (about 0.20 m3 short) and how strap ends overlap
footings.

Earlier (12:20 -> 14:20):
- Columns: the checker has now measured 27 of 59 columns itself, all equal to the engine (0.0 %). The column line still
  cannot be called verified: column C8 and the four lift columns are drawn at one size and scheduled at another (C8:
  ground floor 0.900 .. 1.013 m3; lift necks 0.55 vs 0.75 m3 per metre of height) - both are now carried as ranges and
  are questions for the structural designer; 3 small columns standing on beams are drawn but are in no BOQ at all (about
  1.34 .. 1.43 m3), and 5 upper-floor column lines (2.27 m3) sit where the slab plans draw no column. A task now measures
  the 3 missing columns and checks the 5 lines.
- Floor build-up: the drawings show a 5 cm layer between the finished floor and the concrete on every dry floor
  (checker-confirmed on the vector sections and a high-resolution scan). Wet rooms, the lowered wet-room panels and the
  roof / terraces stay held (their layers and falls are not printed); a task now works those zones.
- Ground-floor annex kitchen: measured 9.630 m2 (checker 0.0 %); by your answer it is a wet room, so the wet floor total
  becomes 72.12 m2 vs the freelancer's 72.01 m2 (+0.15 %); the total floor area does not change. Two first-floor bedroom
  rows were re-paired with the freelancer's (exact match); one curved first-floor room is still 1.727 m2 apart and now has
  its own task. Two places where a closure strip could be billed twice were found before they reached any BOQ.
- Wet-room wall tiles (your method, 340.41 m2 on 12 rooms, 6 held) and the lowered wet-room panels (one set of 6) are
  checker-verified and merged; the wall tiles and the kitchen's wet class go into the candidate with plaster / paint.
- Block walls: the ground-floor wall ends that were held at 45 degree corners and columns are closed from the drawn wall
  faces: +1.21 .. +1.24 m2 of black block on the established 337.41 m2 (waiting for the checker). Three bounds remain held:
  one first-floor bay, the opening between two first-floor walls (the plan and section B-B disagree: a designer question)
  and the masonry above one ground-floor opening.
Released numbers: unchanged.

Earlier (10:20 -> 12:20):
- Candidate step 7 MERGED after the checker's own hand check of all 10 changed lines (0.0 %), NOT released: the
  checker-verified pool base + walls (7.202 m3) and the two terrace dome shells (2 x 2.541 m3) are now in the candidate,
  and the dome it billed twice is billed once. The candidate concrete error on the one line it can compare stays 1.84 %;
  the pool and dome lines themselves stay held as whole lines (pool steps not drawn, tower dome held), so the verified
  share of whole reference lines is still 0 of 8.
- Neck columns: released 10.855 vs freelancer 8.805 m3 (+2.05 m3, +23.3 %) explained exactly, nothing left over: he
  prices 1.350 m3 of necks the engine holds, uses a 0.40 m wide section where 0.30 is printed (-0.165), misses two necks
  (+0.720), and the rest (+2.846) is two different height bases, both wrong: the engine took the neck to the finished
  floor, he took the 1.5 m minimum founding depth as a neck length. From the drawings a neck runs from the footing top to
  the ground-beam top; two levels needed for that are not printed, so every neck stays held (checker-confirmed). Two
  printed size conflicts found (column C8, and the four lift columns: plan vs schedule) - now a task and a designer item.
- Floor area: the hand-wash spaces are settled and checker-verified (wet by your answer), but the scoreboard still
  cannot score the line because the scorer does not read that settlement yet; a task now wires it in (no quantity
  changes). Also found: the ground-floor kitchen is classed dry in the engine although your answer makes it wet - its
  floor total is unchanged, its waterproofing is not; a task measures the effect.
- Waiting for the checker: wet-room wall tiles room by room by your manual method (340.41 m2 on 12 rooms, 6 held; on the
  same 11 rooms as the freelancer 308.07 vs 295.44 m2, +4.28 %, fully explained: your 0.15 m decor-ceiling heights vs his
  flat 3.00 m add 43.19 m2, he deducts no doors or windows -27.91 m2, one open side -2.65 m2); the lowered wet-room slab
  panels (one set of 6, not two; slab concrete unchanged, step concrete 0 by geometry, drop not printed); the coverage
  registry with a candidate-level state; the safety-test fix.
Released numbers: unchanged.

Earlier (08:20 -> 10:20):
- Next candidate step (step 7) handed to the checker, NOT released: the checker-verified pool (base 4.374 + walls 2.828
  = 7.202 m3, on the 1.20 m structural height) and the two terrace dome shells (2 x 2.541 m3) replace the convention
  values; a dome that the engine was billing twice (once as a 'stair' on the first-floor slab sheet) is removed. Effect
  on the candidate: pool +3.707 m3, domes -2.290 m3. Against the freelancer: pool 7.202 vs 12.348 m3 (-41.7 %; his figure
  includes a pump room and steps that no drawing shows), domes 5.081 m3 + tower dome held vs his 6.780.
- Floor area: the 3 spaces that kept the floor-area line unscored are the ground-floor basin-only hand-wash spaces, wet
  by your answer on hand-wash spaces. With them settled the engine gives 385.634 m2 vs the freelancer's 409.58 m2
  (-5.85 %); on the same scope (he also counts a garden band, ground-floor stair treads, a second-floor corridor and the
  first-floor stair footprint: 23.990 m2) the difference is +0.044 m2. Waiting for the checker; a 1.379 m2 gap in the
  first-floor bedrooms is still unexplained.
- Lift core: the lift pit IS drawn and detailed (structural PDF typical detail; earlier searches read only the DXF):
  ring 1.600 m2 gross, 1.100 m2 net of the 4 lift columns. Pit depth is not printed (lift supplier), so its concrete,
  formwork and steel stay held. The freelancer's lift walls 2.400 m3 count the 4 column sections a second time (engine
  right on ownership; his 1.50 m height unexplained). Roof water tank: not drawn, held, a designer item.
- Windows: the two shuttered windows are 4.290 m2 each, measured between the shutter leaves (checker-verified; the
  freelancer's 7.800 used the frame height). Windows like for like on 28 of 29: 88.081 vs 89.681 m2 (-1.78 %, a
  development figure). One window's count is settled on every drawing and held only because of a render.
- Block walls: the engine piece is merged: established net 337.412 m2, 58.366 m3 on the measured walls (white blocks
  303.1 / 394.7 units by your supplier data), the rest held with named bounds; a task now closes those bounds.
- Foundation levels: the unread '2' under every footing is a 2 cm membrane (5 cm screed / 2 cm membrane / 10 cm blinding,
  checker read it from the vector PDF): footing bottom = formation + 0.17 m. The formation itself and the existing ground
  level are still not printed (your rule: 1.5 m is a minimum below existing ground), so excavation depths stay held.
  New: 6 lowered wet-room slab panels (every sanitary group sits on one), drop not printed; now a task.
- Columns re-measured by the checker: 23 of 59, all 0.0 % (line still partially verified).
Released numbers: unchanged.

Earlier (04:20 -> 08:20):
- Lift and roof water tank: an element-by-element, storey-by-storey inventory of both drawing sets found that the lift
  core (its footing, walls and pit) and the roof water tank have NO structural BOQ line in any engine state, while the
  freelancer prices the lift walls. The pit depth and walls are not printed (held, never 0). A task now builds their
  lines from what the drawings print (first for structure).
- Levels: the architectural and structural drawings share one zero (19 of 20 level marks coincide), but the structural
  set prints only finished floor levels, never a structural slab, beam or footing level. So every structural level is
  held until the structural PDF sections are read (next task). This also exposed that the released neck columns
  (10.855 m3) run up to the finished floor; the freelancer has 8.805 m3; that 2.05 m3 gap is now its own investigation.
- Windows: heads and sills of 18 more windows were found in a drawing format nobody had opened (the vector DWF of every
  sheet): 26 of 29 now drawing-confirmed, 5 checker-verified. On those 18 the freelancer has 26.950 m2 where the drawings
  give 22.730 m2 (-15.7 %: he used a flat 2.00 m height where 1.50 m is drawn). Still held: one window's count, two
  shuttered windows and three openings without a leaf.
- Candidate step 6 merged (still NOT released): the first-to-second-floor stair flights are back (lower 1.0334 and upper
  1.0014 m3 both checker-VERIFIED, landing held 0.470 .. 0.480 m3), the engine now refuses a convention where the drawings
  print a value, and the checker confirmed the 4.451 m3 'winder stair' is a dome outline (held as a misread). Next step:
  the verified pool (7.202 m3) and dome shells (5.081 m3) in, the misread removed.
- Pool steel: the base-mesh fix passed (R1 824.89 .. 883.59 kg, R2 572.45 .. 617.96 kg, checker count identical); the
  steel line stays held for the designer (two-zone detail vs your flat floor).
- Block walls (engine piece): sent back once because it used the hand-measured run where the physical wall run governs
  (at T-junctions the stem stops on the face); fixed within the hour and back with the checker: established net
  337.412 m2 (was 358.063, -5.8 %), 58.366 m3 on the measured walls, the rest held with reasons.
- Scope cross-check fixed: one element per physical column (12 -> 4 for the ground-floor C2 columns).
- Columns re-measured by the checker from the drawing: 17 of 59 now, all 0.0 % (whole line still partially verified).
- Safety: a sweep of all 48 merges since yesterday found no new failure; every one of the 396 failing test ids in the
  full suite is explained (390 need private files never committed). Three small infrastructure follow-ups queued.
Released numbers: unchanged.

Earlier (00:20 -> 04:20):
- Main stair, first to second floor: the candidate had dropped these flights entirely (2.6 m3 lost). They are now back
  in the next candidate step, waiting for the checker: lower flight 1.0334 m3 (checker-measured), upper flight 1.0014 m3
  (drawing-confirmed), the landing held at 0.470 .. 0.480 m3. The same step also stops the engine from using a
  convention where the drawings print a value (pool, domes, the two stairs are held with the printed value named).
- Found while doing it: a line the engine called a 4.451 m3 'winder stair' on the first floor is in fact a dome outline
  (18 lines from one centre, radius 2.211 m). It is now held as a misread and will be removed when the checked dome
  concrete goes in, so the dome is counted once.
- Stair concrete vs the roof beams is settled at every foot, head and landing: the stair system is 6.6479 m3 (checker
  re-measured the first riser inside the beam: 0.0 %); still PARTIALLY VERIFIED as you instructed, not all parts measured.
- Openings: the corrected list (three missing openings added; two windows' sill and head re-read on the floor level,
  1.00 / 3.00 m, checker's own reading) is merged. 21 windows still have no printed head: a task now reads them from the
  elevations and sections, and the block-area engine piece (block m2, m3 and white-block counts) can start now.
- Pool steel: sent back once for one counting fault on the base mesh (the per-metre bar count used only the
  maximum-spacing meaning, which was proven for footings, not for this mesh; about 14 kg too high at the low end); the
  walls, rings and outline re-measured exactly. Steel stays held for the designer (two-zone detail vs your flat floor).
- Scope cross-check (every freelancer row to a drawn element): sent back because the element list counts about three
  entries per physical column (12 for 4 columns); being fixed before any count from it is used.
- Checker re-measured 6 more columns from the drawing, all 0.0 % (8 of 59 so far).
- The safety test that stops steel being counted twice has been green again since 01:52 (it was red for 9 h).
Released numbers: unchanged (released concrete 92.77 vs 111.81 m3, -17.03 %).

Since 20:20 (to 00:20):
- Drawing register: all 31 issued sheets listed (architecture 12, structure 16, sanitary 3). No sheet prints a revision,
  so every quantity now cites the exact file it was measured on (file fingerprint); 543 citations in the merged work were
  checked: none points at a sheet outside the set. The structural set carries two dates (May 2025 on pages 1-7, May 2026
  on the later pages): which is the issue date is a designer item. Not issued at all: site plan, top-roof plan, door /
  window and finishes schedules, reflected ceiling plan, wet-room and stair details, water, electrical and A/C drawings.
- Openings checked plan = elevation = section: 71 openings, 10 widths agree on two independent sheets (worst 4.9 mm).
  Found: three openings missing from the opening list (0.90 m, 1.30 m and a 1.20 m opening drawn on the south-west
  elevation), and the list's sill / head for two windows taken on the wrong level base (e.g. 1.85 / 3.85 where the
  elevation gives 1.00 / 3.00 above the finished floor). No quantity moved yet; the list is being corrected and the
  effect on block, lintel and plaster deductions measured.
- Formwork (a category no BOQ has, the freelancer included): the two terrace dome soffits now carried from the checked
  dome detail (2 x 24.150 m2, checker 0.00 %); above-ground formwork calculated 1,078.274 m2 (+4.2 % from that), held
  parts listed; your client's no-dome request is shown beside it and never mixed in.
- Doors / windows now scored like for like (pieces vs pieces, m2 vs m2): windows 56.771 m2 on the 8 openings with
  printed heights vs his 54.931 m2 on the same 8 (+3.35 %), 21 windows held (no printed head), the window count held
  until one disputed window is classified; aluminium doors 10.560 m2 on your 2.20 m door height vs his 12.0 m2 (-12 %, a
  rule difference: he used 2.40 m, plus two 0.90 m doors).
- Fifth candidate extension (checked slab / stair steel and the dome ring) rejected once by the checker for one fault
  (the stair bar range used the low bar count at both ends, 65 kg too low at the top of the range), fixed and back with
  the checker; still NOT RELEASED.
Earlier (20:20 report): stair inside the roof beams (beams own the junction, staircase system 6.675 m3); terrace domes
5.081 m3 VERIFIED (engine convention +2.291 too much); plaster / paint one-room fix passed; block opening deductions by
physical scope; railings 38.916 m drawn and measured (now merged, checker 0.0 % on two runs).
Earlier today: Your pool (teaching case) is now reconstructed and checked: the checker re-read the cut itself and confirmed the concrete
wall is 1.20 m (rim to the structure line; your 1.15 m is the finished water depth) and the 0.15 m upstand above the deck
(1.350 m2 outer face along 8.998 m). Pool concrete 7.202 m3 (base 4.374 + walls 2.828) VERIFIED for the concrete scope;
engine 3.495 (-51.5 %), freelancer 12.348 (+71.5 %: pump room and steps drawn nowhere, base counted again in his wall
height). All eight of your conditions pass except the steel (held for the designer: the two-zone detail vs your flat
floor), so the whole pool line stays PARTIALLY VERIFIED and the verified count stays 0 of 8 by your whole-line rule.
Both staircases are reconstructed and merged: the stair beside the lift is the dog-leg main stair (ground to second
floor), the round stair goes ground to first only; own 6.790 m3 measured plus held parts vs freelancer 15.053 vs engine
4.635 m3. The checker re-measured one flight of each, both 0.0 %. Found: the engine drops the first-to-second-floor
flights entirely (-2.598 m3); the fix goes into the candidate after the next extension.
Also merged since 12:20: the per-metre footing notation (a maximum spacing; 2,769 .. 2,830 kg held only on a leg diameter
the drawing does not print), doors / windows by hand, corners and parapets as physical items with his Sigma rows mapped
onto them, and the fourth candidate extension (84 lines that rested on values the drawings do not print are now HELD,
e.g. the column necks 10.856 m3 -> held 3.075 .. 15.375 m3 because the founding depth is not printed).
Sent back: plaster / paint on one room only (first-floor east master: the room outline slips into the window-frame gap at
both ends of the curved glazing, +0.200 m of wall, owner net +1.25 %); everything else in it stands.
Next for structure: the pool bar lengths on the verified 1.20 m wall, then the stair feet and landings against the slabs.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; 29 of 29 windows accounted for; room levels from the marks; membrane rolls released (each room / roof alone); rooms-that-vanish guard and two hand checks of 24 older engine changes merged (22 right). NEW: the checker read the drawing and confirmed the ground-floor facade run misses the 1.20 m open-air side passage (engine 98.887 vs 105.887 m, -6.6 %): fix checked and merged (= hand; not wired); NEW: the slab plans show the passage roofed over its whole length, so whether it is outside at all is asked of you. The first-floor living gap is traced to 0.0001 m2 (engine 44.869 vs 38.588 m2: stair openings and stair well counted as floor, plus a small engine defect on winder steps 0.296 m2): fix checked and merged (38.459 .. 38.979 m2 vs hand 38.588 .. 38.990; not wired); with your marble answer for the landing the porcelain becomes 33.584 .. 34.104 m2, room-by-room proof on the board | on track |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table, fold, cutting plan, strips along a room's own wall (wedge W.C. 5.95 -> 5.45 m = hand), window areas for 6 windows, room levels, tiling table, plaster / paint per room by hand, tile count, blockwork metres by hand and the centreline code piece merged. NEW: every wall typed white / black from the structural notes and your fallback (no architectural sheet names a block type); skirting: all 28 nets right, 17.04 m of deductions not listed (fix queued). NEW: the code wall run checked against the hand table wall by wall (merged): not ready, it runs walls across open floor (+16.63 m on GF) and misses doorways at free wall ends (-10.37 m); a corrected version is on the board; the glass walls (12.05 m) asked of you. Membrane release version built (2F roof 17, pantry 2), waiting for the checker to run it on the drawing; an audit of every roll count for an offcut booked twice is on the board | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings, columns / necks, beams and stairs by hand, beam fix, typed drawing values, plot-edge members merged. NEW: blinding and columns by hand merged: the freelancer's blinding is a plate under the whole plot that no drawing shows; the engine counts 5 columns the upper slab plans do not draw. Next: columns to the deepest beam at each column (your existing rule), beam register, stairs flight by flight, beam / stair rework. Released concrete still 92.77 vs 111.81 m3 | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released concrete run, commit 8774071, unchanged; waterproofing released in ARCH_TAKEOFF_V2.11)
Since 00:20 (Lead 2026-10-22 04:20): no released number changed. In the opt-in candidate, footing steel moved from a
convention estimate to the drawing (874.86 kg confirmed + 2,742.51 .. 2,836.40 kg held) and soffits over outside air
(44.446 m2) were added, both through the integrated check. The released default stays until you switch it.
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none; now pinned as THE released run (no route G profile, 1,455 lines). The profiled run (5 lines, -17.16 %) is a comparison base, not released | within 2 % | released run unchanged; new pieces not wired |
| Suspended slabs, 62 panels on the three roof-slab plans (hand, CHECKED and merged) | m3 | engine slab faces 60.966; hand 60.280 (every panel matches an engine face within 0.002 m2) | 59.817 | hand +0.463 (+0.77 %); engine +1.149 (+1.92 %) | NEW row | within 2 % | engine's extra 0.686 m3 is 13 faces that are not slab (edge strips, a beam span, a ring piece, slivers): being sorted; the held 2.740 m3 face is the west dome opening and ring, not slab; sunken-slab step edges HELD (drop not printed) |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (piece, merged; checker ran it on the drawing) | m3 | 3.390 | 3.3925 | -0.0025 (-0.07 %) | now confirmed by the checker (engine right) | within 2 % | the released run still gives 3.781: one strap runs into an open footing outline (+0.39); the new piece is not wired |
| Beams (new concrete ledger, MERGED 23:28 after its rework; not wired yet) | m3 | 68.84 released + 18 pieces held (4.25 - 9.18 m3 if counted) | 65.97 | +2.87 (+4.4 %) on the released part only; line not compared while 18 pieces are held | was 64.82 (-1.7 %): +4.018 m3, each by hand (B26 3.905 and B27 3.787 as single spans, B7 strip 0.255 + arc 0.066, 1F ring beams 0.755 + 0.900, upstands 0.240) | within 2 % | 2 pieces settled by printed sections (1.91 m3, on the board); 16 pieces the drawings contradict or leave unmarked: asked you |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (flight-by-flight ledger MERGED 04:03, checker re-measured one flight 0.7248 m3 and both arrival wedges; not wired yet) | m3 | main stair 4.920 by your method / 4.746 by the drawing (was 5.011: three arrival wedges now counted once); slab under the winders in no line: HELD 0.230 .. 0.250; entrance steps 0.357 (its sloping slab held: not printed), lobby steps 0.126 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.211 (-39.5 %) | was -3.12 (-38.4 %): wedges counted once; checker: engine right (his 5.3 m flights are on no drawing) | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you; the last riser inside the arrival slab (0.163 m3) asked you |
| Blinding (piece, merged; checker re-measured) | m3 | 15.179 released under the 25 released footings (checker's own outline union 151.794 m2 x 0.10) + HELD: F10 0.480 .. 0.590, under ground beams 5.724 .. 9.423, under straps 0.772 (released run still 22.155) | 47.055 | not comparable: his figure is one plate under the whole plot, drawn nowhere (rule difference) | NEW: piece checked and merged | within 2 % | held parts wait on your Q-21 / Q-31 answers (C) and the designer; never shown as 0 |
| Columns (piece, merged; checker re-measured) | m3 | 34.446 (piece: the 5 occurrences no upper slab plan draws removed, -2.268); released run still 36.714 | 28.547 | piece +5.90 (+20.7 %); released +8.17 (+28.6 %) | NEW: piece checked and merged (engine right on the 5 columns); in the next candidate step | within 2 % | the rest is height: he takes storey minus 0.75 m everywhere; the Urban rule takes the deepest beam at each column: column-by-column table on the board |
| Columns to the deepest member framing into each column (hand, CHECKED and merged; your rule) | m3 | 28.816 .. 29.139 (range = column C8 drawn 30x80 vs schedule 30x90, and the two water-tank columns 3.00 .. 3.80 m high until the designer says whether the tank beam stands up or hangs down); the joints and column heads become their own lines, not lost | 28.547 | +0.27 .. +0.59 (+0.9 .. +2.1 %) | checked: two columns re-measured by the checker at 0.0 % | within 2 % | 33 columns calculated, 26 held on a held beam, a projection depth, the annex level or C8 |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | now the largest single concrete gap: a hand ledger of the walls and the flat 0.40 m floor at 1.15 m (your answer) is on the board; pool steel held (the drawing's two-zone detail vs your flat floor: designer) |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (released, your answer: each room alone) | rolls | 19 for 17 wet areas; 122.99 m of strips, 67.01 m left over | not given | not comparable | NEW: pantry cutting plan by hand merged: 2 rolls, so 21 with the pantry (your answer: waterproof it); release version on the board | exact | the only general gap: a wedge W.C. laid along its 45 deg wall saves 0.50 m of strip (same roll); now on the board |
| Roof waterproofing membrane (released) | m2 | 204.11 (3 roofs drawn on plans) + the second-floor top roof as a HELD line (your answer); rolls 8 + 6 released, 2F roof HELD 17 or 18; by hand 32 (8 + 6 + 18) | 285.00 | -80.89 (-28.4 %) | fix merged: 2F roof covered completely, its count shown as 17 or 18 until you answer; 1 of 578 BOQ lines changed | within 3 % | NEW: proven by hand and re-measured by the checker: with your answer (trim from the same roof) the 2F roof needs 17 rolls (strips stop at the opening edge, 16 flap pieces from its own roll ends; strict layout 18). Release version on the board; it stays opt-in until you confirm the reconciliation |
| Roof upturn (released) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | now released | within 3 % | top roof held (your answer) |
| Windows with a printed height, 6 of 29 (hand, merged) | m2 | 26.485 | 24.280 | +2.205 (+9.1 %) | was 4 of 29, 13.892 vs 14.350 | exact | engine right on 4 printed heights, 1 rule difference (curved window, your answer); 23 HELD (scans); the curved pool glazing is 6.57 m wide by your answer, height 4.30 m |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 26.49 of 116.9 in the released run; hand table (sent back for status fixes): counts agree with him, main entrance now HELD (renders show a single leaf, the plan prints a 2.00 x 2.50 double), one twin window HELD (no rule gives its height) | 116.9 / 12.0 | not comparable yet | main door moved from measured to held | exact | door heights 2.20 m by your answer (his 2.40: rule difference) |
| Floor-to-floor heights (piece) | m | GF 4.50, 1F 4.20, 2F 4.20 (your answer: +9.70 to +13.90) | not in his BOQ | - | 2F now given by you | exact | - |
| Plaster / paint wall height (both methods) | m | your manual method: GF 3.65, annex 3.15 (provisional), 1F and 2F 3.35; drawing-derived (hand, waiting for the checker): GF 4.09 .. 4.19, 1F / 2F 3.79 .. 3.89 to the decor ceiling | GF 3.60, upper 3.40 (flat) | drawing-derived is 0.44 .. 0.54 m higher everywhere: your 0.60 m beam allowance against the 0.16 m slab where no beam crosses | NEW: drawing-derived heights measured | exact | rooms under a roof wait on the roof level (designer); floor build-up not printed (0 .. 0.10 m range) |
| Facade run (pieces merged, not wired) | m | 1F 63.009 (released 63.169); GF released 98.887, merged piece 105.887 = hand (geometric perimeter); billable by your Q-64 B 105.787, reveal returns 0.100 apart | no run row (he prices exterior plaster per elevation) | 1F -0.160 (-0.25 %) = hand; GF engine -7.000 (-6.6 %) vs hand | NEW: GF fix checked and merged; the passage is roofed full length by the slab plans: outside or inside asked you (98.887 if inside) | exact | GF: the open-air side passage walls were missing; new finding: the first floor covers 4.08 m2 of that passage (soffit and slab over outside air measured nowhere: census on the board); a 0.10 m notch at the pool glass asked you (105.787 or 105.887) |
| Ceilings over outside air (hand, MERGED 04:03; checker re-measured the pool court 12.834 from the printed dimensions) | m2 | 44.446 (porch 19.181, side passage 5.640, pool court 12.834 = 16.525 gross less the drawn opening 3.690, 1F edges 4.374 + 2.417); opening heads and frame recess 1.665 listed apart; finish HELD (no note on any sheet; your Q-68 C, option A provisional only) | 19.154 (pool ceiling only) | pool ceiling his +6.320 (+49.2 % over hand): engine right | was 46.316 (checker basis that added the court walls' tops) | exact | finish waits on the Kuwait specification chapters / designer |
| Facade faces side by side, your request (hand, CHECKED and merged: two faces re-measured at 0.0 %; your Sigma reconciled term by term, waiting for the checker: 811.77 of the drawn 1,022.53 m2 are in his rows, 210.76 m2 of drawn faces (porch, sea face, pool glazing face, passage) in none; his 13 opening rows leave out the big glazings; corners 457.095 m.l measured vs his 1,297.35 m.l) | m2 | 1,022.534 measured + 6.822 .. 13.261 HELD + 13.079 m of slab edge (depth not printed); in your Q-07 bands without plinth 955.797 | his walls 968.237 (his exterior Sigma 1,502.84 gross includes domes, parapets, boundary wall, drip edge) | +54.30 (+5.6 %): rule difference (he takes one plane per elevation, the drawing has set-back faces) | NEW row | within 3 % | net after openings held; his Sigma is being reconciled term by term with your notes (13 openings, corners in m.l, domes out, pool ceiling 12.834 accepted) |
| Rebar | t | footings (piece MERGED 02:29): 0.875 t on 19 footings printed with a bar count + 2.743 .. 2.836 t HELD (your Q-71); ground beams and straps (hand, MERGED 05:07): 1.480 t net + laps / development 0.647 .. 1.195 t HELD + stock-length splices 0.018 .. 0.032 t HELD ; columns above the necks (hand, CHECKED and merged): 1.887 t net + 1.552 t HELD by cause, links 0.781 .. 0.829 t HELD (Q-71), laps on the note-9 range HELD; beams (hand, CHECKED and merged): 5.171 t net; suspended slabs (hand, CHECKED and merged): bottom 2.853 .. 3.068 t on your Q-71, top bars 0.753 .. 1.932 t HELD on a sheet-note vs typical-detail conflict (designer); stairs (hand, waiting for the checker): main bars 0.368 .. 0.421 t on your Q-71, typical-detail bars 0.277 .. 0.305 t HELD; pool HELD (designer); tank walls HELD (not drawn). In the opt-in candidate: footings through the integrated check; columns, ground beams and beams in the next package | footings + straps + ground beams one lump 5.8 t; walls + columns + necks one lump 7.95 t; total 44.19 t | not comparable (his lumps mix elements) | ground-beam steel now merged with its lap range | within 2 % | the drawing prints the lap rule (40 d / 70 d) but not which bars are in tension: a range, not a guess |
| Ground-beam spans split at the columns standing on them (code piece, waiting for the checker) | kg | ground-beam bottom steel 1,194.60 (was 1,238.56 by the released splitter, -43.96 kg, -3.5 %); 52 of 53 spans = the hand ledger within 0.3 mm | lump of another scope | not comparable | NEW row | - | two oblique straps HELD on their length (asked you Q-74) |
| Blockwork wall metres (hand, merged; code piece run on Alsenan, merged: 149.42 / 118.20 / 39.60, not ready to wire) | m | GF 143.16, 1F 120.75, 2F 39.78 (hand) | 134.28, 120.31, 39.10 | +8.88 (+6.6 %), +0.44 (+0.4 %), +0.68 (+1.7 %) | NEW: every wall typed: white 141.31 m and black 136.00 m by your fallback (ASSUMED), black 57.54 m by the structural note, 125.35 m held (parapets, street fence: asked you; sea-side 7.00 m) | within 3 % | GF over target: explained wall by wall, the two glass walls (12.05 m) are the whole gap: asked you; 3 walls drawn 0.15 hold a column the notes say must be built at column thickness (designer); he gives no block type on any row; a below-ground black block run (2 x 31.17 m) is in neither BOQ |
| Block wall area, gross before openings (hand, CHECKED and merged: one wall re-measured 62.155 m2 at 0.0 %; your Q-60 A height to the member above; the 214.36 m2 on provisional heights count as held) | m2 | 955.63 measured (GF 460.07, 1F 371.83, 2F 123.73); with the held walls at their candidate heights 1,036.5 .. 1,042.7; m3 172.19; white blocks 2,512 (62.5x25) or 3,268 (60x20) | 1,094.50 (GF 515.40, 1F 441.41, 2F 137.70) | -138.9 (-12.7 %); with held walls -5.3 .. -4.7 % | NEW row | within 3 % | net area HELD: no rule deducts openings from block (asked you Q-73); black count HELD (block size, asked Q-75); 12.91 m of walls with no height (designer) |
| Skirting (released run, audited by a merged-pending piece) | m | gross 262.56; certain net 185.52 (212.65 with held window edges) | 282.85 (gross, no door deduction) | gross -20.29 (-7.2 %) | new row | within 3 % | rule difference: your rule deducts doors, he does not; all 28 engine nets right, 17.04 m of window-frame credit not listed on the lines (listing fix queued) |
| Plaster / paint, dry walls gross (hand, both methods; SENT BACK by the checker: the ground-floor master bedroom was walked along the straight court line instead of the curved glazing, +1.7 % on that room; being redone on the checked room outlines) | m2 | your method: GF 391.17, 1F 375.03, 2F 107.92 (874.12 + stair shaft HELD); drawing-derived: 1,150.62 .. 1,177.59 whole house incl. the shaft | 1,209.39 gross plaster rows (paint 1,191.13) | drawing-derived -58.8 .. -31.8 (-4.9 .. -2.6 %); your method per floor: GF +0.8 %, 1F -15.0 % (his 1F open zone has 55.70 m of wall where the drawing has 38.61 m) | was held | within 3 % | nets (after doors and windows) wait on 18 window heights and arch heads; the stair shaft under your method asked you (Q-72) |
| Wall tile in wet rooms (hand, your method) | m2 | 483.44 (+2 rooms HELD on level); drawing-derived 546.24 .. 560.53 | 433.83 (one spatter area at 3.00 m flat) | +49.61 (+11.4 %) on your method; not comparable room by room | NEW | within 3 % | his total is one figure at a flat 3.00 m height |
| Ceilings, decor gypsum horizontal (hand, CHECKED and merged: master bedroom re-measured 16.549 vs 16.557 m2, +0.05 %; your Q-57 A modified) | m2 | 388.14 (GF 207.01, 1F 137.63, 2F 30.53) + bulkheads 32.78 by your method (175.76 drawing-derived, PROVISIONAL); paintable gypsum 420.92; dome openings 29.07 HELD; wet-board type, coves, drops HELD | decor rows 409.58; 452.33 painted | -21.44 (-5.2 %); paint -31.41 (-6.9 %), +2.8 % without his 42.75 m of cove strips | NEW: first measurement (was not measured) | within 3 % | GF -11.1 % is exactly the light well 23.24 + stair strips 2.45 he ceils (engine right, two drawings); 1F he omits about 23 m2 over the double-height void; coves have no detail (rule difference) |
| Dry-room floor tiles, 10 rooms (piece, merged) | m2 | 194.98 | 189.61 | +5.37 (+2.83 %) | NEW: fix merged: 1F living 38.459 .. 38.979 (candidate range) vs hand 38.588 .. 38.990; under your Q-66 B porcelain 33.584 .. 34.104 | within 1 - 2 % | first-floor living 44.869 vs hand 38.588 (38.990 if the foot of the east flight is landing) vs his 38.96: the engine counts the round-stair opening (2.10), the stair well (2.53) and the round-stair quarter landing (1.35) as floor, and loses 0.30 on winder steps; fix on the board. Landing finish: asked you (your two rules differ). Second-floor lobby 8.775 vs 7.70 engine right |
| Floor tile count per room (piece, merged) | tiles | held in all 25 floor rooms: no tile size printed on any Alsenan sheet; for 60x60 on 23 rooms 697 tiles without offcut reuse (+21 % over net m2) or 611 with reuse in the same room (+6 %) | not given | not comparable | new | exact | tile size per room and offcut reuse asked you |
| Stair marble (piece, merged; flight-once piece merged 23:33: released tread marble 27.324 -> 20.424 m2 + 0 .. 3.450 held, steps 91.028 -> 68.028 lm + 0 .. 11.500 held) | m2 | 39.49 (treads, risers, landings) | 295.44, of which 151.80 is the court paving counted a second time; stairs and landings alone 143.64 | not comparable: his step rows are metres added to m2 | NEW: his double count found in his own formulas | exact | turning steps and round stair held (your answers pending) |
| Tiling materials (piece, PROVISIONAL) | bags / m3 | cement 80 - 111 bags, sand 10.91 - 15.21 m3, adhesive 58 bags of 20 kg | not given | - | new | - | provisional by your answer; stair bed held on the 1:3 question |
| Floor area inside the house, room by room (hand, CHECKED and merged) | m2 | 376.86 .. 376.98 (GF 210.80, 1F 138.13 .. 138.25, 2F 27.93); wet 85.62, dry like for like 337.18 | wet 72.01; dry like for like 337.57 | dry -0.39 (-0.12 %); wet +13.61 = the pantry, wet by your answer | was held | within 1 - 2 % | every one of the 41 labels has a row, none silent; the released method still counts the open side passage (about 5.2 m2) as inside floor |
| Outside floors by your rule (hand from the sections, waiting for the checker) | m2 | open court interlock 119.542; porch floor at court level 10.680 (its own line, material open); entrance steps marble: treads 3.360, risers 1.960, top landing 5.180; north side walk porcelain: drawing 21.021 beside your method 23.955 (the difference is the boundary wall your 1.50 m includes); side passage porcelain 5.640; pool deck 7.939 HELD; garden band 13.986 HELD | yard 151.80 | like for like (court + porch + side walk) 151.234: -0.566 (-0.37 %) | was areas only | within 1 - 2 % | the 19.181 m2 noted for the porch is its roof, which also covers the entrance steps and landing (10.680 + 3.360 + 5.180 = 19.220); the porch floor itself is 10.680. Six door thresholds with a printed 0.15 m step and no step drawn held for the designer |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first).

## What the team has learned so far
- (21 Oct, 16:20) A CAD census area can contain surfaces that belong to other trades: the pool-court soffit's 14.704 m2
  CAD basis holds opening heads (1.104 m2), a glazing reveal (0.561) and wall tops (0.276) below the slab, so only the
  hand 12.834 m2 may feed the ceiling line. Floor area room by room shows the engine's dry floor is right like for like
  (-0.12 % against the freelancer) once his garden band, stair treads and landings are put back, and that the released
  method counts the open side passage as an inside floor.
- (21 Oct, 12:20) A dimension chain must close on its printed total before a part of it is trusted (three window sills were misread that way); the frozen structural route can release steel as verified from a duplicated schedule row, so every released bar line needs its printed row; ceilings differ from the freelancer mainly where he ceils the light well and skips the double-height void, not in the rooms.
- (21 Oct, 08:20) The column rule moves 5.467 m3 out of the column line, but it is not lost: it is exactly the joints
  (4.264) and the column heads (1.203), which no beam or slab line holds yet, so they must become their own lines. Block
  area to the member above each wall is 12.7 % under the freelancer, most of it his storey heights; the block BOQ cannot be
  finished until two of your rules exist (opening deduction, black block size).
- (21 Oct, morning) Measured room by room, your manual heights and the drawing-derived heights differ by the same
  0.44 .. 0.54 m everywhere: the 0.60 m beam allowance against a 0.16 m slab where no beam crosses the room; crossing
  beams are bulkheads, a ceiling item. Every room under a roof has the annex's level problem. The 62 slab panels agree
  with the engine to 0.002 m2; the engine's extra concrete is 13 faces that are not slab, so a slab face should be
  released only with slab evidence.
- (21 Oct, night) A candidate built on the newest opt-in version still has to show every line that differs from the
  RELEASED method, not only from the version under it; the checker counts 197 such lines. On Alsenan a printed beam
  section cut also crosses the 0.20 m projection strip, so "the one span at the printed width" decides, not "the span the
  cut crosses". Arabic notes on scans: free OCR misreads too much (published error rates 54 - 79 %); only closed lists
  (tile sizes, room names) checked by two readers may release a value.
- (20 Oct, late) A stair flight drawn on the upper floor plan for orientation is measured again by the released method
  (+3.45 m2 marble); the 2F "stair lobby 450 x 195" was two dimensions read as one room: the 1.95 m belongs to the stair's
  own dimension chain, so the arrival is landing. The freelancer's blinding plate covers the whole plot; the drawings give
  blinding only under footings, ground beams and straps.
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one side (60.17 m kept).
- The freelancer counts one footing twice; footing F10 is drawn longer than its schedule row.
- Neck-only columns (type CN) are typed in the schedule as plain text; read now, they are 5 columns that do not exist.
- All 17 wet areas by hand agree with the freelancer's floor (72.12 vs 72.01 m2) and full boundary (144.73 vs 144.61 lm).
- The membrane layout (direction and start wall) changes the rolls as much as the room size: 13 to 15 rolls for the same
  17 wet areas; the strip count by length beats the count by area (a laundry needs 3 rolls, not 2).
- The ground floor is a split level (+1.00 / +0.30); only 6 of 27 rooms print their own floor level.
- The Alsenan PDF sheets are scans: no code can read their heights until an OCR reader exists.
- Stairs: the section, the architectural plan and the structural plan each draw a different step count; the freelancer's
  main-stair flights are 37 - 54 % longer than the drawn ones.
- Beams: the engine splits a beam where a planted column sits on it, and misses beam upstands printed in the sections.
- No beam on the Alsenan roof-slab plans is 0.60 m deep (0.40, 0.50, 0.75, 0.85, 1.20 m), so your 0.60 m rule needs a
  choice for real beams; the ground-floor annex roof (+4.30) may or may not be a slab level.
- Only one door height is printed on the whole Alsenan set (the main entrance, 2.50 m); the freelancer's 2.40 m is not
  printed anywhere.

- A strip layout can look complete and still miss a piece: an outline step whose edge runs the same way as the
  strips leaves its upturn uncovered (0.84 m2 on the second-floor roof); only a full hand plan found it.
- Whether an offcut may be reused inside the same room is the open rule behind both the membrane rolls (one roll on
  this villa) and the tile count (15 - 20 % of the tiles bought).

- A new ledger version must be judged against the released run, not only against the ledger under it: the beam fix adds
  4.02 m3, but the new ledger also carries older holds, so its released concrete over all items is 229.57 m3, not 236.27.
- Two pieces of the drawings settle beams by themselves: sections A-A and B-B cut the B20 and B23 west spans and print
  their sizes; a third of the held beam pieces are contradictions only the designer or you can settle.
- The whole Alsenan set prints no tile size, no floor finish, no skirting, no ceiling and no door schedule; the only
  door height is the main entrance (2.50 m), and the sanitary sheets say "not to scale". The roof falls are printed 1 %.
- The freelancer's stair marble (295.44 m2) contains the court paving (151.80 m2) a second time, by his own formulas.
- A new engine piece can pass all of its own tests and still break a repository-wide guard (two pieces this morning);
  every new piece now runs that guard before it is handed in.
- Blockwork by hand is close to the freelancer on the upper floors (+0.4 %, +1.7 %) and 6.6 % over him on the ground
  floor; the old "140 m short" figure was an artefact of the engine's face-band run (a centreline run fixes it on the
  test villas: 54.60 m vs 44.40 m).
- Two readers agreeing is not proof: the code's independent reader and the engine agree on the ground-floor facade, but a
  hand reading finds a 1.20 m open-air passage both of them bridge (+7.00 m). The checker now reads the drawing itself.

- The freelancer's blinding (47.06 m3) is a plate under the whole plot; the drawings blind only under footings and the
  four ground-beam sections (20.7 - 26.4 m3 by hand).
- No architectural sheet names a block type; the structural notes do (neighbour-side ground-beam walls black, walls that
  hold columns at column thickness), so a block-type reader must read the structural notes, decoding the CAD Arabic.
- A room's floor area can include the stair opening and stair well inside it: on the first floor that is 4.6 m2 of the
  6.3 m2 the engine gives too much.

- The second-floor roof needs 17 rolls under your trim answer only if the strips stop at the opening edge and the step
  band is covered by flap pieces from that roof's own roll ends; a layout that looks the same with full strips needs 18.
- An open-air passage can sit partly under the floor above: on Alsenan 4.08 m2 of the side passage is roofed by a
  first-floor bathroom and bedroom, an exterior ceiling and a slab over outside air that no BOQ line measures yet.

- A wall band can run across open floor: the code's wall run on the ground floor joins two walls 12.2 m apart and crosses
  both passage mouths, so a total close to the hand (+4.4 %) hid +16.6 m too much and -10.4 m too little.
- Two drawings can disagree on whether a space is roofed: the slab plan puts a panel over the part of the side passage
  the architectural reading called open to the sky; only reading the slab plan settles which outside spaces are covered.
- A roll count can book the same leftover twice: one fold method claimed 8 rolls where the pieces cannot fit; every
  proven count is being re-checked piece by piece.
- Where a ground-beam plan has no marks and the sections are chosen by span length, a column the splitter misses changes
  the bars, not only the length (three such columns on Alsenan); and the structural general notes carry the lap and
  development lengths, so a steel ledger is not complete until it has read them.

## Being worked on now
(Lead 2026-10-25 02:15)
- Checker: foundation waterproofing into the candidate (second hand-in, in work now), the formwork end-face fix and the
  ceilings readiness check as they arrive; in between, the remaining block walls not under a sunken panel, largest first.
- Structural (worker 1): the formwork end-face fix (one row); then the sheet search for the three missing designer
  rows (column level where two ground slabs meet, main-stair winder turn and waists, tower dome); stair soffits; the
  column-core datum; excavation last.
- Architecture and finishes (worker 2): ceilings made ready for the candidate (in work); then the wall register's
  sunken-panel correction; then the plaster / paint blockers and the pantry doorway row.
- Integration (worker 3): foundation waterproofing into the candidate (in work); then one project identity for the
  export (the first real export, for internal review), then the held depths, stairs / domes (with the landing marble)
  and windows; then the settled block walls and the ceilings.

(Lead 2026-10-24 22:15, superseded)
- Checker: foundation waterproofing into the candidate first (with a challenge: part of the 35.40 m2 buried-coat
  figure it carries includes faces that are not against earth), then the drawn-vs-scheduled beam census, then the
  buried-faces fix when it arrives; in between, block walls and first-floor ceilings.
- Structural (worker 1): formwork faces where beams end on curved or angled members; stair soffits flight by flight;
  the column-core datum correction; excavation levels last.
- Architecture and finishes (worker 2): the buried-faces fix (in work); the wall register (height pieces add up to the
  length, windows deducted only where they sit in the wall); ceilings made ready for the candidate.
- Integration (worker 3): the scoring key for the dressing room and landing; two small tooling tasks; then the settled
  block walls and later the ceilings into the candidate.

(Lead 2026-10-24 20:15, superseded)
- Checker: merges the stair file registration and the stirrup count (both passed or in check now); then the laps / tons
  rework, the ceilings fix and the remaining buried-concrete faces as they arrive; the foundation waterproofing step
  into the candidate goes first when it is handed in.
- Structural (worker 1): laps and tons with your acceptance points (next run); then beams drawn wider or narrower than
  their schedule, every one; excavation levels last.
- Architecture and finishes (worker 2): the remaining buried-concrete faces (in work); the ceilings fix over the light
  well; then the wall-register check that every wall's height pieces add up to its length.
- Integration (worker 3): foundation waterproofing and the buried-concrete coat into the candidate (now unblocked);
  then the scoring key for the dressing room and landing; later the settled block walls into the candidate, once the
  register check is merged.

(Lead 2026-10-24 16:15, superseded)
- Checker: the next floor-area step into the candidate, the block-wall blockers fix and the stair method fix as they
  arrive; in between it keeps re-measuring the settled block walls, largest first.
- Structural (worker 1): the one-line fix to the stair method; then ground-beam stirrups / side bars from the prints;
  then laps and tons (your 14:23 / 15:31 decisions); excavation levels last.
- Architecture and finishes (worker 2): block-wall blockers fix (in work); coating of all buried concrete; ceilings;
  then the wall-register height check over all 76 walls.
- Integration (worker 3): floor area step 2 (in work), then foundation waterproofing, then the ground-beam / column
  corrections; a small tooling task (the fingerprint guard into the scoreboard) for an empty lane.

(Lead 2026-10-24 12:15, superseded)
- Checker: the aluminium doors step into the candidate first (it can close a whole line), then the stairs / domes
  closable split, the opening-to-room check, the formwork update and the ground-beam bars as they arrive.
- Structural (worker 1): hand in its three finished pieces one by one (stairs / domes, formwork, ground-beam bars)
  before starting anything new; then your stair finish-level method.
- Architecture and finishes (worker 2): hand in the opening-to-room check; the first-floor living and pantry floor
  pieces; then the coating of all buried concrete and the remaining wall blockers.
- Integration (worker 3): aluminium doors line, then floor area steps 2 - 4, then foundation waterproofing, then the
  ground-beam / column corrections.

(Lead 2026-10-24 04:15, superseded)
- Checker: the family-register test fix first, then the beam correction; then the next integration step; in between
  it re-measures neck sections and the conflicting columns, and the remaining first-floor stair flights.
- Structural (worker 1): the boundary ground beam and the court / annex ground beams from the drawings; then the 15
  conflicting columns column by column; excavation last (depth held until the existing ground level is known).
- Architecture and finishes (worker 2): the block-wall resolution ledger; room-face lengths for plaster / paint;
  foundation and lift-pit waterproofing.
- Integration (worker 3, one step every 2 h, the bottleneck): the footing with two tags as a conflict (in work); then
  the candidate's unprinted ground-beam depths and column heights held and the 28 checked columns taken in; the
  deductions for the two windows; one project identity for the export; the slab / beam split; the floor fixes.

## What is missing
- Window heads: 3 of 29 windows still held (one count, two shuttered) and three leafless openings (being closed); every door but the main entrance (2.20 m by your Q-55 C, stated as assumed).
- Ceilings: wet-room board type, cove detail, drop heights at openings, dome openings (designer); bar counts of the 3 planted columns (designer).
- Block walls: net area on 43 walls (28 openings still held; three openings missing from the list being added), black-block count (being investigated), wall tops under the dome openings and the lift tie beam (designer).
- Ceilings over outside air: area settled (44.446 m2); the finish has no note on any sheet (specification / designer).
- Stair soffits (underside of flights and landings, 7.40 m2 seen from the ground floor alone) in no line yet (being measured).
- Slab under the main-stair winders (0.23 .. 0.25 m3) in no line yet; 16 beam pieces the drawings contradict or leave unmarked (designer list).
- Roof levels and roof build-up (rooms under a roof), decor-ceiling levels and floor build-up, sunken-slab drops: three new
  designer requests (D-39, D-40, D-41). The sunken-slab drop now also holds 7.91 m of ground-floor block-wall height.
- Marble on the first-floor stair landing (4.92 m2): no material line in the candidate yet (being added).
- Columns by the deepest-beam rule (table on the board); the engine's 5 undrawn columns removed when the ledger is rewired.
- Blockwork: the code on Alsenan, the walls that hold columns, block m2 / m3; parapet and street-fence block type (asked).
- Tile sizes per room (none printed), ceiling layout, annex roof datum, round-stair section (designer list).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (to ask later).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- No decision for you today. You answered the curved window (9.87 m2 opening area) at 23:53; it is applied.
- The designer / consultant list: NOT ready to send yet (your 23:57 instruction). I checked all 30 rows against the
  merged, checked work: none is answered by the drawings, so none was removed; two "search still open" notes are now
  closed (the lift tie beam is a designer question, the lift pit depth goes to the lift supplier instead). I split the
  list into 9 priority requests, each unlocking one complete BOQ line (windows, pool concrete, footings, blinding,
  ground beams, beams, columns, stairs and domes, floor area) and the remaining questions. Six priority requests are
  complete; three (columns, stairs and domes, floor area) still lack a row for an item the checker names but nobody
  filed (the column level where two ground-slab levels meet, the main stair's winder turn and the stair waist
  thicknesses, the tower dome, and a doorway strip in the pantry). Two tasks write those rows with their sheet search;
  then the list is ready for you. (02:15: two rows corrected from the checker's reading; still not ready.)
- One small action, no decision: the two sealed reference take-offs (the Alsenan printed take-off and the second
  sealed benchmark) are protected only by file name, because the agents may not open sealed files to fingerprint them.
  If you record their SHA-256 fingerprints on the board (or tell the main chat), the checker's tool protects them by
  content. Until then only the site benchmark is protected by fingerprint.
- One thing only you can do, if it exists: a site / plot level survey (existing ground levels). Your rule fixes the
  excavation as at least 1.5 m below the EXISTING ground, and no issued sheet prints that ground level, so every
  excavation depth stays held until it is known.
