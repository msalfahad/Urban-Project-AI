# Consultant / designer clarification list, Alsenan (owner 2026-10-23, main chat 17:50 UTC; DRAFT for the owner to send)

Owner rule (2026-10-23): before an item is sent, every available drawing, section, schedule and note has been searched;
each item states the conflicting evidence and the BOQ lines it holds; nothing the drawings already answer is asked.
Source register: DESIGNER_CLARIFICATIONS.md (D-nn rows, each raised by a task that read the sheets named there). Column
"search" = the tasks whose merged, checker-verified work read the listed sheets; LEAD: before the owner sends this list,
confirm each row's search is complete (all 12 architectural + 16 structural + 3 sanitary sheets relevant to it) or move
the row back to an investigation task. Items are ordered by the reference lines they block (closable-line effect).

SEND STATUS (main chat 18:00): rows 1-6, 10-12 READY TO SEND (two printed sources disagree, or the element is not drawn on
any sheet; recorded searches in the 'Search' column). Rows 7, 8, 9 NOT YET: drawing search in progress (T-227 claimed 17:42:
lift details ST p.14, section B-B, roof details; T-222 claimable: P-1F-01 / P-GF-05); each is sent only if those tasks end
with the item still unresolved, else removed. No row is answerable from the plans on the evidence merged so far.

LEAD SEARCH CONFIRMATION (Lead 2026-10-23 18:20 UTC, from the merged tasks' records and the Checker's verdicts; owner 17:50 (6)):
- SEND-READY, search complete: row 1 D-16 (structural plan text + dimension chain + outlines vs schedule: two printed sources
  disagree; T-217 + Checker 13:53 own ST DXF), row 3 pool steps (GF plan, ST p.7, sections; T-183, T-203: absence on every
  sheet that draws the pool), row 4 D-57 (ST p.7 two-zone pool vs answered Q-26 A: a drawing-vs-owner-decision conflict only
  the designer can settle), row 5 C-ST-4 (structural stair linework vs architectural plan / section, project-wide; T-184,
  T-189, T-192), row 6 D-63 (foundation plan vs column schedule; T-205, T-217), row 10 D-12 (note 20 vs architectural wall
  thicknesses; T-143, T-226), row 11 D-02 / D-27 (schedule blocks vs drawn bands, width only: Checker 18:01 read the schedule
  blocks itself; depths agree, so wall heights are not affected), row 12 D-65 (ST DXF + PDF at each member and the
  architectural 1F / 2F plans; T-220, Checker 15:52).
- HOLD SEND, row 2 D-44: the record covers the structural sheets only (ST p.10 schedule, the ST DXF tank area). The
  architectural roof plan, elevations and section B-B have not been recorded as searched for the tank enclosure / B15
  position. Moved back to an investigation step inside T-221 (lane S, second; roof plan, roof details, sections and
  elevations read on vector geometry). Send only if T-221 records it undrawn on every sheet.
- HOLD SEND, rows 7 (D-43) and 8 (D-06 / D-17): T-227 READY 18:00 (worker 2) reports both unresolved after reading ST p.14
  lift details, note 19, section B-B, roof details and elevations; send-ready only after the Checker's Gate A verdict on
  T-227 confirms that search (queued 18:49).
- HOLD SEND, row 9 (D-64 / D-60): T-222 (lane A, now first) records every architectural sheet searched for each opening.
Engineering note on row 2: this is an engineering question for the consultant, not an owner decision (ERS s.2.7); the
owner sends nothing from this list until each held row is cleared as above.

| # | D | Element | Conflicting / missing evidence (drawing references) | Question to the consultant | BOQ lines held | Search |
|---|---|---|---|---|---|---|
| 1 | D-16 | Column C8 | Structural plan prints 30X80 (dimensioned 70 + 10, five 0.80 outlines); column schedule prints 30 x 90 | Which section is built? | CONC.COLUMN reference line (blocks VERIFIED); neck 0.240 .. 0.270 m2, GF 0.900 .. 1.0125 m3, 1F 0.180 .. 0.200 m2 | T-100, T-119, T-217 + Checker own ST DXF re-measure 13:53 |
| 2 | D-44 | Beam B15 20 x 120 at the water tank (sets the 2F tank-column heights) | ST slab plan prints B15 20 x 120 (ST p.10 schedule agrees: B15 20 / 120); no section shows whether it is an upstand or a downstand; if upstand, B3 0.40 controls: 2F C2 / C3 heights 3.00 .. 3.80 m | Is B15 an upstand or a downstand? | CONC.COLUMN reference line (2F C2 / C3 heights), the tank joint 0.160 m3 | T-119, T-119 r2; main chat 18:00: the ST DXF 'WATER TANK PLACE' area prints marks and bars only, no level |
| 3 | (pool) | Pool steps / access | No step, bench or ladder drawn on the GF plan, ST p.7 or the sections ("STEPS: NOT DRAWN" is absence of evidence) | Steps, benches or a ladder? If concrete, their drawing | CONC.POOL whole line (base + walls 7.202 m3 VERIFIED; line PARTIALLY VERIFIED) | T-183, T-203 |
| 4 | D-57 | Pool reinforcement on the flat floor | ST p.7 draws a two-zone pool (R1 / R2, slope, step); owner Q-26 A fixed a flat floor at 1.15 m | Which bar population the flat floor and walls take | Pool steel HELD (R1 888.90 .. 927.54, R2 615.34 .. 639.45 kg) | T-166, T-191 r2 |
| 5 | C-ST-4 | Main stair MS1-L riser count | Structural stair linework vs the architectural plan / section riser count disagree | Riser count (and landing edge) as built | Staircase system 6.648 m3 PARTIALLY VERIFIED (MS1-L HELD) | T-184, T-189, T-192 |
| 6 | D-63 | Lift necks / columns on footing FF | Foundation plan 20X50 (three) and 25X100; column schedule FOUNDATION row 30 x 50 / 30 x 100 | Which section governs | Neck / column concrete CONFLICT 0.55 vs 0.75 m3/m; neck depth HELD | T-205, T-217 |
| 7 | D-43 | GF lift-wall tie beam (ST p.8 note 19) | Level 3.00 m given, size not printed on any sheet | Tie-beam section | 4 lift block walls (200 mm black) 43.37 m2 gross HELD; tie-beam concrete HELD | T-143, T-227 (in progress: re-reads ST p.14 lift details first) |
| 8 | D-06 / D-17 | Annex roof +4.30 | Section B-B: +4.30 on top of one ~0.23 m band; plans give finished roof levels; drainage prints 1 % falls | Structural slab top of the annex roof and its build-up | 9 annex block walls 83.82 m2 black + 29.30 m2 white HELD; annex plaster / paint / tile heights | T-112, T-143, T-227 (in progress: tests owner Q-54 B against B-B, roof details, elevations) |
| 9 | D-64 / D-60 | Openings P-1F-01 and P-GF-05 | P-1F-01: leafless on the 1F plan, no head on any sheet, section B-B draws two leafed doors; P-GF-05: opening on the SW elevation, no head, frame or leaf | What is built and its head level | 1F-W14 + W15 net 10.971 .. 16.223 m2; masonry above 0 .. 4.992 m2; P-GF-05 masonry above 2.232 .. 2.700 m2 | T-215, T-222 (claimable) |
| 10 | D-12 | Walls containing columns (ST p.8 note 20) | Architectural plans print 0.15 / 0.20 walls round 0.25-wide columns | Wall thickness where a column sits inside the wall | Block m3 on 19 rows 23.407 .. 31.737 m3 (m2 unaffected) | T-143, T-226 |
| 11 | D-02 / D-27 | Beams whose drawn width differs from the schedule (CB10, B29, CB2, B21, B6 ...) | Schedule vs drawn width | Which width is built | Beam concrete CONFLICT ranges | T-110, T-226 |
| 12 | D-65 | Five released upper column lines | Released lines 2.268 m3 with no column drawn on the upper plans | Do these columns exist? | Released CONC.COLUMN lines NOT_DRAWN | T-220 |

Not on this list (answered by the drawings or already owner rules): opening deduction (Q-73), black block module (Q-75
provisional, supplier list), door height fallback (Q-55 C). Further designer items (D-01 .. D-62 not above) stay in the
register and are added here only when they block a reference line.
