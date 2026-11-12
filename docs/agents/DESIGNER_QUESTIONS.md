# Designer questions: the ONE list of what the drawings do not print (training villa)

Owner decision 2026-11-11 15:30 (2c): the Lead keeps ONE list of every dimension or detail the drawings do not print,
with the lines and quantity each affects. Agents never send it; the owner does. Full item text, drawing references and
history stay in DESIGNER_CLARIFICATIONS.md (D-ids); this file is the short, sendable index.

Rules for this list: quantities are from the candidate line index ARCH_TAKEOFF_V3.0.70 (not released); per unit, never
summed across units; a blank line has no bound and is never 0; a bound is low .. high of the bounded lines only.
Until T-716 maps every HELD line to its item, the figures below are FAMILY totals with the items known to hold them:
one family can be held by several items and by non-designer causes too (owner questions, method gaps).

Version: Lead 2026-11-12 00:16 (T-716 MERGED 17aaab4b: per-item census on V3.0.70, engine file research/agents_t716/out/T716_CENSUS.md; T-712 / T-721 MERGED; candidate now V3.0.72, the census lines are unchanged by it except the 28 masonry lines of T-703, text / one-ended figures only).

PER ITEM (T-716 census, HELD lines of V3.0.70 citing each D-id; SOLE = held by that item alone, SHARED = held with another item; rebar lines are parked and counted apart; per unit, never summed):
D-39 roof datum 92 sole + 21 shared (m2 30 bounded 1,115.33 .. 1,250.82 + 18 blank; m3 6 bounded 2.07365 .. 2.80125 + 23 blank; pcs 10 blank; kg 5 blank) = the largest item, send first; D-04 58 + 6; D-36 62 sole (all parked rebar); D-27 38 + 8; D-33 21 + 26; D-34 19 + 25; D-35 24 + 3 (+ the 3 court ground-beam lines L-62243c74 / L-21795b35 / L-a55bfa01 that the census put under METHOD_GAP: they belong to D-35, Checker F-V716-1); D-57 19; D-02 15; D-63 11 + 29; D-66 0 + 36; D-03 11; D-16 9; D-41 9 + 8; D-43 8 + 3; D-05 0 + 10; D-26 2 + 10; D-28 5; D-53 4; D-56 3; D-62 3 + 1; D-14 2; D-38 2; D-15 1 + 1; D-44 0 + 4; D-22 0 + 1; D-40 0 + 1. 27 D-ids hold 297 active lines; 19 of the 37 seed D-ids are cited by no HELD line (T-716 finding): they stay in DESIGNER_CLARIFICATIONS.md but are NOT sent until a line cites them.
D-56 is out of the designer package (D_REMOVED_REVISED s.2) yet 3 stair lines cite it (L-061e18cf, L-77ecb282, L-caa721ed: 1 STR.CONC.STAIR m3 blank, 2 formwork m2 blank): they move to item 7 under D-67 / D-68 when the stair package re-states them (Lead ruling 2026-11-12: a removed D-id is never cited; the line names the live item that holds it).

| # | What the drawings do not print | D-ids | Family held on V3.0.70 (lines; bounded low .. high; blank) |
|---|---|---|---|
| 1 | Beam sizes where schedule and drawing disagree or no label is printed; section D-D width | D-02, D-03, D-04, D-27, D-30, D-44 | STR.CONC.BEAM 26 lines; 14 bounded 5.9832 .. 8.4127 m3; 12 blank (T-721 MERGED: 11 roof-edge strips D-05 / D-26 blank, 6.9471 m2 per m depth; east dome ring D-28 AT_LEAST 0.115155 m3) |
| 2 | Lintel bearings / junction ends and the datum of 3 openings | D-45, D-58, D-60, D-64 (openings); datum per T-699 | STR.CONC.LINTEL 45 lines; 24 bounded 1.361 .. 2.0506 m3; 21 blank (16 carry AT_MOST beside in V3.0.71, family 1.322146 m3) |
| 3 | Column sizes where outline and schedule differ; planted / upper columns; tank columns | D-16, D-46, D-63, D-65, D-66, D-44 | STR.CONC.COLUMN 29 lines; 27 bounded 11.6728 .. 15.5015 m3; 2 blank (tank pair, LOWER_ONLY 0.3287 m3 each) |
| 4 | Exterior ground-beam depth ('FOLLOW ARCH.'), section choice, concentrated-load spans | D-33, D-34, D-35 | STR.CONC.GROUND_BEAM 29 lines; 9 bounded 1.1784 .. 5.0968 m3; 20 blank (T-712 MERGED: 17 AT_LEAST 5.099845 m3 beside, unwired until T-722; 3 court lines blank, D-35: landing / yard datum not printed) |
| 5 | Roof datum and roof build-up; parapet height; the 2F top-roof interval | D-06, D-17, D-39, D-62 | STR.CONC.PARAPET 4 blank; FIN.ROOF.* 13 lines held; masonry 2F hosts (T-696 AT_MOST beside) |
| 6 | Lift tie beam size, lift necks, lift walls | D-43, D-63 | STR.CONC.LIFT 2 blank; lift-wall block area PROVISIONAL |
| 7 | Stair geometry not dimensioned (curved stair, GF winder turn, riser counts) | D-08, D-13, D-29, D-56, D-67, D-68 | STR.CONC.STAIR 5 blank (T-711); stair finishes 85 lines held (T-715) |
| 8 | Floor build-up per floor and ceiling levels (no reflected ceiling plan) | D-09, D-22, D-24, D-40, D-47 | FIN.FLOOR.BED.DRY 23 lines 9.0456 .. 12.0607 m3; BED.WET 21 lines 3.423 .. 5.1345 m3; FIN.CEILING 5 blank m2 |
| 9 | Sunken wet-room slab panels: membrane position | D-41 | WP recess HELD 0 .. 13.335 m2 (T-710) |
| 10 | W.C. outlet type (penetrations) | (T-691 / T-710 datum; D-id to be given by T-716) | FIN.WP.PENETRATION 17 lines blank pcs (19 .. 31 pcs named in T-710) |
| 11 | Walls under the dome openings: top of wall | D-20, D-42 | wall heights there held (masonry / plaster) |
| 12 | Window sills / heads not printed | D-45 | ARCH.WINDOW / reveal lines held |
| 13 | Missing sheets (site plan, top roof, door / window / finishes schedules) | D-62 | many families; listed per line by T-716 |

Not on this list (they are not designer items): rebar (parked by the owner 2026-11-11, approximate tons at the end);
owner questions (OWNER_QUESTIONS.md Open); method gaps the team closes itself.
