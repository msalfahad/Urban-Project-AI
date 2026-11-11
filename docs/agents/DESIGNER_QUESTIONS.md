# Designer questions: the ONE list of what the drawings do not print (training villa)

Owner decision 2026-11-11 15:30 (2c): the Lead keeps ONE list of every dimension or detail the drawings do not print,
with the lines and quantity each affects. Agents never send it; the owner does. Full item text, drawing references and
history stay in DESIGNER_CLARIFICATIONS.md (D-ids); this file is the short, sendable index.

Rules for this list: quantities are from the candidate line index ARCH_TAKEOFF_V3.0.70 (not released); per unit, never
summed across units; a blank line has no bound and is never 0; a bound is low .. high of the bounded lines only.
Until T-716 maps every HELD line to its item, the figures below are FAMILY totals with the items known to hold them:
one family can be held by several items and by non-designer causes too (owner questions, method gaps).

Version: Lead 2026-11-11 16:25 (seed). Next update: when T-716 merges (per-item line counts).

| # | What the drawings do not print | D-ids | Family held on V3.0.70 (lines; bounded low .. high; blank) |
|---|---|---|---|
| 1 | Beam sizes where schedule and drawing disagree or no label is printed; section D-D width | D-02, D-03, D-04, D-27, D-30, D-44 | STR.CONC.BEAM 26 lines; 14 bounded 5.9832 .. 8.4127 m3; 12 blank |
| 2 | Lintel bearings / junction ends and the datum of 3 openings | D-45, D-58, D-60, D-64 (openings); datum per T-699 | STR.CONC.LINTEL 45 lines; 24 bounded 1.361 .. 2.0506 m3; 21 blank (16 get AT_MOST in T-704 r2) |
| 3 | Column sizes where outline and schedule differ; planted / upper columns; tank columns | D-16, D-46, D-63, D-65, D-66, D-44 | STR.CONC.COLUMN 29 lines; 27 bounded 11.6728 .. 15.5015 m3; 2 blank (tank pair, LOWER_ONLY 0.3287 m3 each) |
| 4 | Exterior ground-beam depth ('FOLLOW ARCH.'), section choice, concentrated-load spans | D-33, D-34, D-35 | STR.CONC.GROUND_BEAM 29 lines; 9 bounded 1.1784 .. 5.0968 m3; 20 blank (T-712) |
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
