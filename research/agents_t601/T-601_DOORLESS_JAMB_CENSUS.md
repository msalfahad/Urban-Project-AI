# T-601: doorless opening jamb census (F-T591-1 fix row; ELEMENT_REGISTER 'DOORLESS OPENING JAMB')

Worker 2, 2026-11-07, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t601/* and tests/t601_doorless_jambs/* only. Training villa; not an accuracy claim. ERS read: s.2.1,
2.3 (own drawing read), 2.4, 2.7 (no owner question: every condition is settled by an answered rule or a record), s.3,
s.4, s.7.

## 1. Physical element and rule (ERS s.2.1, R-T601-1 in t601_rules.py)

The jambs of a wall opening are its two return faces, each as deep as the wall. Skirting runs on them only when the
opening genuinely has no leaf or frame, both sides are dry skirting rooms and the dry floor finish reaches the jamb
(URBAN-SKIRTING-OPENING-METHOD v1 DOORLESS_OPENING; UP-SKIRT-001 1.4.0 'doorless_opening_jambs: included'); a door
(or a framed landing door) takes none (DOOR_PRESENT). The paired plaster / paint returns stay with the PLASTERED RETURN
FACE entry (UP-OPEN-SCHED-001 1.4.0), never billed here. The census decides from the gap's OWN drawn evidence, in order:
crossed strip -> not an opening; leaf / swing -> door; panel lines across the gap -> framed; glazing -> window; else
doorless, then side (outdoor -> outdoor scope HELD by name; wet -> NOT_APPLICABLE by Q-06 A / UP-THR-001; unknown ->
HELD), depth (unknown -> HELD, never 0), ends (real jamb vs a face continuous with a cross wall), engine treatment
(deducted -> fix row; one cell -> already in the outline).

## 2. Drawing read (own, this run)

Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf), decoded into the private folder only;
`t601_extract.py` reads every straight wall band (layer-1 faces, 0.09 .. 0.26 m, frozen opening_census) and every curved
band on the three plans, and writes handles + figures only (T601_DRAWN.json). 64 gaps: GF 31, 1F 25 (one curved),
2F 8 (incl. windows). Every door insert on the three plans sits in a census gap except '2D8' (the sea-side fence gate,
outside the house); one GF door drawn without a block (layer-D swing 334) is found by its swing. Gaps with no leaf and
no glazing: 3 on GF, 2 on 1F, 0 on 2F; framed (lift landing door: four lines across the gap at 0 / 0.05 / 0.10 / 0.20
and the shaft cross beyond): one per storey, stacked.

| Opening (record) | DXF faces | Width / wall | Ends | Evidence | Sides | Status | Jamb lm | Engine / his |
|---|---|---|---|---|---|---|---|---|
| A-1F-01 (1F OP-011) | AD0 AD1 AD4 AD5, arch120 BEC | 1.00 / 0.15 | masonry / masonry | arch head | bed room 380 x 430 / dressing: DRY / DRY | **FIX_ROW** | **0.30** | both lines deduct the arch, no jamb / his 0.30 |
| P-1F-01 (1F OP-009) | C09 C0A C0B; jambs C15 / C16 | 1.30 / 0.15 | nib end / continuous with the lobby's east wall (C10) | head lines C13 C14, no leaf | east bed room / its lobby: DRY / DRY | INCLUDED_IN_OUTLINE | 0.15 (one real jamb) | one cell L-309f118f (no OP-009 deduction, T-296) |
| A-GF-01 (GF OP-027) | 127 128 12A 12B, arch120 1F8 | 1.00 / 0.15 | masonry / masonry | arch head | dewaneya / hand-wash: DRY / WET (Q-06 A) | NOT_APPLICABLE | 0 | as T-591 / his gross row, no jamb |
| P-GF-01 (GF OP-020) | 215 21A 21C | 0.90 / 0.20 | column / masonry | head lines 33C 33D | stair hall / hand-wash: DRY / WET (Q-06 A) | NOT_APPLICABLE | 0 | candidate HELD line (RFI b) -> FR-T601-2 |
| P-GF-05 (GF OP-007, 'open side') | 120 15A | 1.20 / 0.20 | column / column | none | court +0.15 / open service passage: OUTDOOR | OUTDOOR_SCOPE (HELD) | bound 0.40 | his yard 81.32 lm, scope UNRESOLVED (T-574 s.4) |
| L-GF-01 (GF OP-011) | 20D 20E 21D 21E, panels 228-22B | 1.00 / 0.20 | masonry / masonry | landing-door panels | dining / lift shaft | FRAMED, no jamb | 0 | T-296 kind 'PASSAGE' -> lift (FR-T601-3) |
| L-1F-01 (1F OP-007) | AFD AFE B19 B1A, panels B98-B9B | 1.00 / 0.20 | masonry / masonry | landing-door panels | living / lift shaft | FRAMED, no jamb | 0 | same (FR-T601-3) |
| L-2F-01 (2F OP-002) | 1289 128A 129B 129C | 1.00 / 0.20 | masonry / masonry | landing-door panels | lobby / lift shaft | FRAMED, no jamb | 0 | already lift (T-443) |
| P-GF-02 'open side' | 103 111 85 | 1.40 | - | a cross-wall face (A3) inside the strip | outdoor passage end | NOT_AN_OPENING | 0 | - |
| (alignment) | 14F 336 337 | 13.27 | - | four cross walls | - | NOT_AN_OPENING | 0 | - |

T-591's two open names are closed: GF OP-011 and 1F OP-007 are the GF and 1F lift landing doors (drawn panels, the
census's stacked lift gaps; T-175 binds them L-GF-01 / L-1F-01), not doorless passages: no jamb skirting by the LIFT
DOOR GAP register; the whole-width deduction stands.

## 3. Skirting restated vs the freelancer (lm, by cause)

- A-1F-01: ours 0 -> **+0.30** (FR-T601-1); his 0.30 (2 x 0.15 in his 21.40 outline): AGREE after the fix. T-574 row 29
  UNRESOLVED -0.30 closes as FREELANCER_RIGHT (owner method); the 'bed room 2' group gap -2.00 -> -1.70.
- Candidate FIN.SKIRTING released 209.428592 -> **209.728592 lm (+0.143 %)** once FR-T601-1 is integrated; nothing else
  valued moves.
- P-GF-01: the HELD 0.40 jamb line becomes NOT_APPLICABLE (FR-T601-2): no valued change; RFI b keeps only the reveal's
  wall finish (B4 / B5).
- P-1F-01: no change; his 'bed room 1' -0.73933 stays UNRESOLVED (T-218), not a jamb cause.
- P-GF-05: 0.40 named inside the outdoor skirting scope (UNRESOLVED), never 0, never valued here.
- Lifts / A-GF-01: 0 both sides.

## 4. Verdict proposals, lesson, missing

- A-1F-01 jambs FREELANCER_RIGHT 0.30 lm (ENGINE_WRONG on our side): no leaf / frame and the 0.15 depth DRAWING-CONFIRMED (own read);
  both sides dry and the floor continuous on the T-175 / T-296 records (not re-measured).
- A-GF-01 / P-GF-01 RULE: NOT_APPLICABLE (Q-06 A marble threshold + full-height tile on the wet side); one class, one
  status (the candidate's HELD OP-020 jamb line disagreed with the merged A-GF-01 reading).
- GF OP-011 / 1F OP-007: ENGINE_RIGHT on the deduction, label wrong (lift, not passage).
- Lesson proposal (ERS s.7): "2026-11-07 | an engine opening labelled PASSAGE was carried as doorless | the kind label
  was the evidence | read the gap's own drawing (leaf, landing-door panels, glazing, head lines) before applying the
  doorless jamb rule | tests/t601_doorless_jambs | PROPOSED".
- Missing / uncertain: P-1F-01 'included in the outline' rests on the T-296 / T-574 cell records (the cell outline
  22.15067 was not re-polygonised here); the lobby's west 2.1 m runs behind a drawn joinery box (JOINERY_SCOPE, not this
  task); P-GF-05 side reading is a plan reading (the nearest-level figure there is not reliable); U-01 0.93 (T-150
  UNRESOLVED) matches no census gap.

## 5. For the Checker

1. `python3 -I research/agents_t601/t601_alsenan.py --check` (byte-identical; pins in the JSON); with the private DXF:
   `.work/venv/bin/python -I research/agents_t601/t601_extract.py --dxf <P7757.dxf>` (re-read identical).
2. A-1F-01: faces AD1 / AD5 end at one jamb, AD0 / AD4 start at the other, 1.000 apart, 0.150 deep: 2 x 0.15 = 0.30.
3. Re-read OP-011 / OP-007 (task ask): the gaps 20D-21E (GF) and AFD-B1A (1F) carry four layer-5 lines across the
   opening and the shaft cross beyond: landing doors.
