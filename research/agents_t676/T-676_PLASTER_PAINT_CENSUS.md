# T-676 plaster / render / spatter / paint HELD census and MEASURABLE NOW faces (lane A, research, unwired)

Worker 2, 2026-11-10. Candidate ARCH_TAKEOFF_V3.0.64 (T-668 line index, file sha256 4403697..., lines d227173a). Nothing
wired or released; V2.9 + route G unchanged; no rule / knowledge version file touched. Rules R-T676-1 (census),
R-T676-2 (face / reveal measure), R-T676-3 (coat materials) in `t676_rules.py`; builder `t676_alsenan.py` (`--check`);
outputs `out/T676_PLASTER_PAINT_CENSUS.{json,md}`; tests `tests/t676_plaster_paint_census` (41).

## Physical elements and scope

The wall coats (spatter dash bond coat, internal plaster 2 coats, wet-wall levelling render, external render / Sigma)
and the paint on them. Scope codes: FIN.PLASTER, FIN.PAINT, FIN.EXT.FINISH, ARCH.FACADE, EXT.FENCE.PLASTER,
EXT.FENCE.PAINT, and any SPATTER / RENDER code. The candidate has NO spatter-dash or coat-material line at all (MISSING
category, T-364; materials only in the unwired T-489 / T-511 ledgers), so those appear as coats under their hosts.

## Census: 57 HELD lines = every HELD line of the scope codes (none missing, none twice)

| Class | Lines | What holds them |
|---|---|---|
| DESIGNER_ITEM | 20 | D-39 roof build-up under the slab (12 plaster, value at the drawn-section scenario, ESTIMATED), D-45 opening heights (5 paint) and arch profile (A-GF-01, A-1F-01), D-53 gate D-GF-15, D-62 plinth ground level |
| OWNER_OPEN | 16 | fence plaster 8 + paint 8: site-wall finish scope, OWNER_NOTES_SIGMA item 3 (open) |
| OPEN_BOUND | 6 | stair shaft GF / 1F / 2F plaster + paint (Q-72 full exposed height; build-up b 0 .. 0.10, contacts, W27 head) |
| OWNER_DECISION_HOLD | 6 | annex +4.30 datum, Q-54 B HOLD (4 wet-render plaster, 2 paint) |
| QUEUED_ROW | 6 | FIN.EXT.FINISH x 3 + ARCH.FACADE register x 3: measured face by face (T-305 / T-567), replaced by T-314 |
| PRINTED_VALUE_GAP | 2 | stair-core wet rooms: floor +0.30 / +1.00 not drawn (T-088, T-173 C-SH-2) |
| MEASURABLE_NOW | 1 | OP-009 door reveal (below) |

Totals (HELD, never 0; blank lines named, not summed): FIN.PLASTER 14 bounded 932.72581 .. 1,006.77641 m2 + 10 blank;
FIN.PAINT 7 bounded 487.121 .. 542.8606 m2 + 3 blank; FIN.EXT.FINISH 3, ARCH.FACADE 4, fence 16: all blank. The two
2F shaft lines are BLANK in the candidate although merged overlay rows give 44.512 .. 49.872 (plaster, FR-T640-29) and
42.722 .. 47.932 m2 (paint, FR-T640-28): listed beside, not summed (wiring gap for the integration lane).

Coat materials (R-T676-3; Q-79 1:4 / 1:4 / 1:2, Q-53 C 1.33 / 1,440 kg/m3 / 50 kg; thickness from
PLASTER_MATERIALS_TABLE_V1, KSE 'Bayt Al-Omr' 2023, ESTIMATED): internal plaster 0.02 m = 0.153216 bags + 0.02128 m3
sand per m2; on the 14 bounded dry hosts 142.908518 .. 154.235867 bags, 19.848404 .. 21.421648 m3 sand (HELD bound,
host areas held). Wet render (6 hosts), fence / class-not-established (11), exterior (3): HELD (host blank). Spatter
dash on all 35 hosts: HELD (no line, no thickness; T-364). Water: HELD everywhere (no w : c ratio printed or owner-given).

## MEASURABLE NOW: own measure this run (P7757 DXF, private copy, mm)

1. **L-f4175f99 GF OP-009 (D-GF-01) door jambs and head: 1.08 .. 1.20 -> 1.08 m2, ASSUMED - OWNER-APPROVED (Q-55 C).**
   Block D120 (1,000 leaf) on the SW facade wall: wall faces 200 apart, wall lines stop at 0 / 1,000 (clear 1.000),
   run -468 .. 2,632 = 3.100 m = facade SW-1 (T-159): AGREE with T-108 / T-194 / T-313. The GF plan has exactly ONE
   D200 (2,000 leaf) = the printed main entrance 2.00 x 2.50 (D-GF-07 / OP-021). The pending class 'main-entrance
   candidate 2.20 / 2.50' therefore closes: OP-009 is not the main entrance, no sheet prints its height, Q-55 C gives
   2.20 m: 2 x 0.20 x 2.20 + 0.20 x 1.00 = **1.08 m2** (-0.12 m2 vs the high end). Not wired.
2. **A-1F-01 (L-64cb94b4): cause correction, quantity stays HELD.** The candidate cause says 'drawn on no plan'; the
   1F plan does draw it: the one 1F arch120 block, 1,000 x 150, wall faces 150 apart stop at -500 / +500 (clear
   1.000; T-175 1F-W16 1.000 / 0.150 AGREE). Only the arch spring / rise is printed nowhere (D-45, like A-GF-01).

Nothing else is measurable now: every other blank or bounded line waits on a named D-nn, an owner item, or T-314.
T-314 / T-364 lines are named, not measured (no duplicate). Engine vs freelancer: no line moves except the 0.12 m2 high
end of OP-009 (his door reveals are not itemised: no verdict change). Verdict proposal: L-f4175f99 UNRESOLVED vs
the freelancer (he has no row); engine fix row 1.08 m2 from the drawing + Q-55 C.

## Findings for the Lead

- F-T676-1: 2F shaft plaster / paint lines blank in V3.0.64 while the merged overlay carries their bounds (wire them).
- F-T676-2: the annex GF_01 / GF_04 plaster lines carry a drawn-section ESTIMATED value (T-563, D-39) while their paint
  lines are blank under Q-54 B: the two codes of the same face use different hold treatments (no change made here).
- F-T676-3: no water line or ratio exists for any coat; under Q-79 cement / sand can wire, water stays HELD.

Lessons-register row (proposed, ERS s.7): 2026-11-10 | a door reveal stayed bounded 2.20 .. 2.50 m because the classifier
called a 1.00 m external door a 'main-entrance candidate' | the main entrance is the one door the drawings print (Q-55 C);
any other door, by its own drawn width, is not it | close a CLASS_PENDING height when the plan holds exactly one door of
the printed main-entrance width elsewhere (every villa) | tests/t676 (normal: reveal 1.08, full-height opening face,
shaft face; adverse: opening on another face / not built / taller or wider than the face, cm as m, held as 0) | PROPOSED.
