# T-608: lift landing openings, scope by trade (GF OP-011 / 1F OP-007; 2F OP-002 beside)

Worker 2, 2026-11-07, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t608/* and tests/t608_lift_landing_scope/* only. Training villa; not an accuracy claim. Drawings are cited
by Drive folder / title only. ERS read: s.2.1 - 2.7, s.3, s.4, s.7.

## 1. Physical element and rule (R-T608-1, t608_rules.py)

A lift landing entrance at one storey = the structural opening in the 0.20 shaft-front wall (1.00 jamb to jamb, height
NOT printed) + the landing-door assembly in it (frame, sliding leaves, sill) + the threshold piece in front (B6-07) +
the surround on jambs and head (B6-06) + the wall round it (masonry, lintel, plaster / paint on the room face and the
shaft face). The kind is read from the gap's own drawing (panel lines + shaft symbol), never from the engine label.

## 2. Drawing read (own, this run; T608_DRAWN.json, handles and figures only)

- P7757.dxf (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip): on every storey the T-601 lift gap carries four
  layer-5 lines across the full 1.000 gap at 0 / 50 / 100 / 200 mm from the SHAFT face (the landing-door frame / leaf
  band on the shaft side, then the room face), and a layer-5 diagonal > 1 m in the shaft beyond (GF 224, 1F B94, 2F
  12AC): LIFT_LANDING_DOOR on all three, stacked. Wall 0.200, width 1.000 DRAWING-CONFIRMED (agrees with T-175 / T-601).
- Text census, architectural DXF 177 + structural DXF (ST7757 dxf.dxf) 1,934 text entities, raw and with the
  key-mapped Arabic decoded: 0 height notations; 7 hits, all read: the lift BASE label on the foundation plan and six
  structural member schedule titles. No note names the landing-door supply, a landing-door height or a door schedule.
- p7757_arch_sheet10.pdf (raster, no text layer), viewed: section A-A cuts the stairs and rooms (storey intervals 4.50 /
  4.20 / 4.20, levels +1.00 / +5.50 / +9.70 / +13.90); the lift is NOT IN THE DRAWING on this section; the doors it
  shows carry no height dimension (none scaled, Q-55 / sanitary note). Agrees with the Q-55 census (only the main
  entrance height is printed).

## 3. Scope table (task openings; 2F rows in out/T608_SCOPE_TABLE.md)

| Family | GF OP-011 (L-GF-01) | 1F OP-007 (L-1F-01) | Correct? / owner trade |
|---|---|---|---|
| Opening count ARCH.PASSAGE | L-77a427c8 RELEASED 1 pcs, kind PASSAGE | L-32d90a7a RELEASED 1 pcs | **WRONG -> FR-T608-1** (not a passage) |
| Door / frame / sill supply | no line (T-568: 'excluded: lift supply', no note) | no line | **OMISSION -> FR-T608-2**: HELD, trade not printed |
| Threshold | B6-07 0.5 m2 + 1.0 lm RELEASED; ARCH.THRESHOLD + porcelain strip EXCLUDED | same | correct (T-413); bed 'not stated' (T-511) |
| Surround jambs + head | B6-06 HELD blank; no plaster / paint return line, no bead | same | correct (LIFT ENTRANCE register) |
| Skirting | L-71e2e002 deducts 1.00 whole, no jamb (28.571589 lm) | L-ba3599ec same (V13 21.21536 lm) | correct (LIFT DOOR GAP; label fixed V12) |
| Blockwork | host GF-W08 HELD (MAS.BLOCK t=0.20 HELD) | 1F-W07 HELD | correct: deduction 1.00 x h, h HELD |
| Lintel | L-8f69c407 HELD (L1 0.20 x 0.20, if built 0.072 m3) | L-a500f10e HELD | correct: count 0 .. 1 on the head |
| Plaster + paint, room face | GF-08 HELD 152.0505 .. 178.805 m2 x 2 | 1F-13 HELD 111.0177 .. 114.3677 m2 x 2 | correct: full deduction, h HELD |
| Wall tile / doorway WP | none | none | correct (dry room / shaft) |

Range check (by construction in the builder, not assumed): 1F-13 width 3.3500 = 1.00 x 0 .. 3.35 exactly (W15 / W16
settled by T-238, T-292 ledger): the 1F living plaster AND paint lines are held by the landing-door height ALONE; the
same holds for 2F-01 (22.6502 .. 26.0002). GF-08: 26.7545 = lift 3.6500 + W02 23.1045 (W02 stays open).

## 4. Fix rows (for T-604's successor manifest; nothing wired here)

- FR-T608-1 SET: ARCH.PASSAGE L-77a427c8 (GF OP-011), L-32d90a7a (1F OP-007) and L-c91732d6 (2F OP-002, F-T604-1)
  RELEASED 1 pcs -> EXCLUDED (kind LIFT_LANDING_DOOR). ARCH.PASSAGE released 9 -> 6 pcs (-3). DRAWING-CONFIRMED.
- FR-T608-2 ADD: one HELD-blank landing-door assembly line per storey (proposed code DOOR.LIFT_LANDING; the Lead names
  it), count 1 beside each (3 nr DRAWING-CONFIRMED), owner trade HELD by name; never in DOOR.INTERNAL.PVC, never
  EXCLUDED as 'by others' until a printed note / spec names the lift package.
- No m2 / m3 / lm quantity moves. Released lines changed: 0.

## 5. Freelancer, verdicts, findings

- His blockwork deducts each lift opening 1.00 x 2.40 = 2.40 m2 (7.20 m2 for three; T-559): his 2.40 is printed nowhere
  (Q-55 refuses it without evidence): UNRESOLVED on his side; ours HELD (ENGINE_RIGHT to hold, no %).
- Passage count: ENGINE_WRONG (label as evidence), fix FR-T608-1. Supply: ENGINE_OMISSION, fix FR-T608-2.
- F-T608-1: T-568's 'excluded: lift supply' label is not supported by any note: restate 'trade HELD (no printed note)'.
- F-T608-2: the landing-entrance opening height is the single open fact behind 4 plaster / paint lines (1F-13, 2F-01),
  part of GF-08, 3 blockwork deductions, 3 lintel counts and the B6-06 surrounds. Its source is the lift supplier (as the
  pit depth, CLARIFICATIONS S14) or the architect: proposed for the RFI package together with the landing-door supply
  scope. A project fact, not an owner method: no owner question (ERS s.2.7).
- F-T608-3: Q-55's 2.20 m is the door-trade (internal door) fallback; a lift entrance height is fixed by the lift product:
  not extended (no borrowed value). A provisional lift-entrance height would need its own owner rule (none asked).
- Lesson proposal (ERS s.7): "2026-11-07 | lift landing doors stayed in the passage count and had no supply line after the
  skirting label was fixed | a label fix was made in one family only | when an opening's kind is corrected, walk every
  line family that reads the kind (count, supply, threshold, surround, skirting, masonry, lintel, faces, wet trades) in
  the same row set | tests/t608_lift_landing_scope | PROPOSED".

## 6. For the Checker

1. `python3 -I research/agents_t608/t608_alsenan.py --check` (byte-identical; input sha256 in the JSON); with the private
   files: `.work/venv/bin/python -I research/agents_t608/t608_extract.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf>`
   (re-read identical).
2. Re-read one gap: GF 20D / 20E / 21D / 21E faces 0.200 apart, gap 1.000; panels 228 / 229 / 22A / 22B at 0 / 50 / 100
   / 200 mm from the shaft face; diagonal 224 in the shaft.
3. Re-add the 1F-13 range: 114.3677 - 111.0177 = 3.3500 = 1.00 x 3.35; and FR-T608-1 9 -> 6 pcs.

Missing / uncertain: the MAS.BLOCK line holding each host wall is named as the storey's only HELD t=0.20 line (2F: all
t=0.20 lines HELD) on the T-175 s5 status, not re-bound wall by wall; the shaft-side face (T-388 SHAFT, Q-72 open)
takes the same deduction and stays HELD by name; whether the GF tie beam (note 19, 3.00 m) is the GF head is not
established (lintel count 0 .. 1 stands).
