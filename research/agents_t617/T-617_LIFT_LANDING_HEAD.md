# T-617: lift landing head height from the drawings (F-T608-2)

Worker 2, 2026-11-08, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t617/* and tests/t617_lift_landing_head/* only. Training villa; not an accuracy claim. Drawings cited by
Drive folder / title and sheet only. ERS read: s.2.1 - 2.7, s.3, s.4, s.7.

## 1. Physical element and rule (R-T617-1, t617_rules.py)

The landing entrance's structural head = the underside of whatever closes the hole at the top of the 1.00 m gap in the
0.20 shaft-front wall. Nothing prints it. A hole cannot pass through concrete, so every member drawn across the gap in
the wall line bounds the head ABOVE: soffit = interval - slab-top build-up - overall depth D (schedule depth, slab inside
it, R-T395-1). A member placed only by a printed level (note) bounds it at that level whatever its reference point; if
its sides are not drawn it is a SCENARIO, never applied as firm. Nothing in the set bounds the head BELOW (a plan gap, a
sill at F.F.L. or a door symbol gives none): the low end stays 0, named. No default height (Q-55 2.20, his 2.40).
Face effect: deduction in [0, w x min(h_max, F)]; it narrows a face line only when h_max < F. A face measured to the
slab soffit (Q-72 plaster) always keeps w x (D - t) above an opening under a member of depth D (independent of b).

## 2. Drawing read (own, this run; T617_DRAWN.json + READINGS in the builder)

- Door side (P7757.dxf, T-608 handles): on every storey the gap lies on the SOUTH face of the shaft (opposite the shaft
  cross 224 / B94 / 12AC), stair hall west; plans stacked.
- Ring beam on that side (ST7757 dxf.dxf, own extraction): GF roof S-OPENING box 54F / 550 1.80 x 1.80 -> south mark
  B14 (45F); 1F roof box 73F / 740 -> south B7 (6CC); 2F roof (+13.90) closed over the shaft (T-401), box = 1F box minus
  the sheet pitch 38,724.4 mm -> south B2 (78A); a 0.200 band of two lines along the south side on all three. Other
  sides as T-401 (B1 / B7 / B1, B1 / B7 / B1, B1 / B1 / B1). Rendered plans (ST PDF p.4 / p.5 / p.6) agree by eye.
- Depths (ST PDF p.10 Schedule of Simple Beams): B14 20 x 75, B7 20 x 75, B2 20 x 40, B1 20 x 40.
- Levels: +1.00 / +5.50 / +9.70 / +13.90 (sheet 10 A-A); b 0.05 (T-214); slab 16 (ST p.8 note 18); roof build-up r not
  printed (D-39), scenario 0.05 (T-556).
- ST p.8 note 19 (raster, Arabic): beams tie the LIFT COLUMNS at 3.00 m where the storey exceeds 4.30 m: GF only (4.50).
  No section, no datum point, no sides; no tie-beam label on any plan (DXF search 0).
- ST p.14 lift detail (vector, no text layer): 'Lift door' at F.F.L. on the shaft wall 'AS PER PLAN', broken off above;
  pit depth 'As Per Lift Manufactures recommendations'. No head level. Sheet 9 = NE elevation (exterior); sheet 10 A-A
  does not cut the shaft; the DXF holds no section through it. Nothing else prints a head.

## 3. Result (out/T617_HEAD_BOUNDS.json / .md)

| Storey | Over the door | Head high firm (b, r >= 0) / at drawn b, r | Note-19 scenario | G1 face | Candidate lines | Q-72 plaster kept |
|---|---|---|---|---|---|---|
| GF | B14 D 0.75 | 4.50 - 0.75 = 3.75 / 3.70 | 3.00 | 3.65 | 0.000 m2 (scenario +0.65 on the low end of each GF-08 line) | 0.59 m2 (scenario 1.29) |
| 1F | B7 D 0.75 | 4.20 - 0.75 = 3.45 / 3.40 | - | 3.35 | 0.000 | 0.59 |
| 2F | B2 D 0.40 | 4.20 - 0.40 = 3.80 / 3.75 (ESTIMATED r) | - | 3.35 | 0.000 | 0.24 |

Head: BOUNDED above (DRAWING-BOUNDED), not settled; low end not printed. 1F-13 (111.0177 .. 114.3677) and 2F-01
(22.6502 .. 26.0002) plaster + paint stay as they are: the drawn soffits (3.40 / 3.75) lie above the 3.35 face, so the
range is set by the face, not the member. GF-08 unchanged on the firm reading (152.0505 .. 178.805, W02 also open); under
the note-19 reading 152.7005 .. 178.805 per line (SCENARIO, never applied). Released lines changed: 0.

Blockwork deduction: no narrowing (host-wall bound 3.35 / 3.65 below the soffit measured from the structural slab top;
GF slab-on-grade top not printed, T-401 RFI 1). Lintel: count 0 .. 1 unchanged (the head may meet the soffit, no lintel).

## 4. Freelancer and verdicts

- His 2.40 m (T-559, blockwork deduction 1.00 x 2.40 per landing): <= every drawn bound (3.00 .. 3.80), so the drawing
  neither supports nor contradicts it: UNRESOLVED (admissible, printed nowhere). Ours HELD with the bound: ENGINE_RIGHT
  to hold. No % (no value on our side).
- 1F-13 / 2F-01 / GF-08 ranges: ENGINE_RIGHT as carried (the members do not cut the G1 face).

## 5. Findings, fix rows, RFI

- F-T617-1 .. -4 in the JSON. FR-T617-1 (for T-558 / the plaster wiring, nothing wired here): when the plaster face goes
  to the slab soffit (Q-72), the lift-door deduction on 1F-13, 2F-01 and GF-08 is capped at 1.00 x soffit height: the
  range narrows by 0.59 / 0.24 / 0.59 m2 per line (the (D - t) band), the head itself still HELD.
- RFI (DRAFT, not sent): lift-supplier item 2 completed with "below the ring beam over each landing"; structural item 38
  completed with the sides of the note-19 tie beams and the reference point of the 3.00 m. A project fact, not an owner
  method: no owner question (ERS s.2.7 not met).
- Lesson proposal (ERS s.7): "2026-11-08 | an unprinted lift head was carried as 0 .. face height with no member bound;
  the DXF text census missed the raster notes and the text-less detail sheet | members over an opening and notes outside
  the DXF were not read | bound an unprinted head by the soffit of every member across it (D - t band stays on a
  slab-soffit face); census the PDF sheets that carry no text layer by eye | tests/t617_lift_landing_head | PROPOSED".

## 6. For the Checker

1. `python3 -I research/agents_t617/t617_alsenan.py --check` (byte-identical; T-608 table pinned by sha256); with the
   private files `.work/venv/bin/python -I research/agents_t617/t617_extract.py --st <ST7757 dxf.dxf> --arch <P7757.dxf>`
   (re-read identical).
2. Re-read one section of the member: ST p.5 (1F roof) shaft box, south beam label B7 inside the box above the 0.20 band;
   p.10 B7 = 20 x 75; 4.20 - 0.05 - 0.75 = 3.40 >= 3.35.
3. Re-read ST p.8 note 19 (3.00 m, > 4.30 m) and confirm no plan draws its sides.

Missing / uncertain: the head itself (supplier); note-19 tie-beam sides and datum (structural); r (D-39); that the
schedule depth is overall is the T-395 reading (both parties' beam volumes agree on it), not printed on p.10.
