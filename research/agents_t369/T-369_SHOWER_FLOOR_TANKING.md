# T-369: B8-04 shower floor and tanking (Alsenan; every villa)

Worker 2 (lane A), 2026-10-30. Development villa, not an accuracy claim. Research only: no engine module, candidate line
or released line changes; V2.9 + route G stays the default. Drawings named by Drive folder and title only ("Alsenan
chalet project"). ERS s.2 - s.4 and s.7 applied. Files: `t369_shower_rules.py` (rules, any villa), `t369_alsenan.py`
(register from committed readings), `SHOWER_REGISTER_T369.csv`, `summary.json`, `tests/t369_shower_tanking/`.

## 1. The physical elements (ERS s.2.1)

| Element | What is built | Unit | Owner of the quantity |
|---|---|---|---|
| Shower zone | the floor wetted by a shower: a tray outline, or a screen / curtain line across the room with the end walls (walk-in) | m2 (extent) | information for B8-04, tiles, falls |
| Shower floor membrane | the membrane under that zone | m2 | **B8-01** (the room's floor membrane): UP-WP-004 1.0.0, owner-confirmed, value SAME_AS_THE_WET_ROOM_FLOOR |
| Shower-wall upturn | the 0.20 m upturn on the shower walls | m2 | **B8-03** (the room's upturn, same rule) |
| Shower-wall tanking | membrane ABOVE the 0.20 m upturn on the walls the zone touches | m2 | **B8-04**, only where a height is printed or ruled |

Evidence order (ERS s.2.2): a tanking height printed in a project detail first; then an owner rule; otherwise HELD.

## 2. What the drawings print (own read)

**Architectural plan** (P7757.dxf from P7757_DXF_COMPRESSED.zip, sha256 ab54dd55..): the wet rooms carry walls (layer 1),
doors (D315 inserts), windows (layer W), columns and the NET floor hatch (layer 3: GF bath 2E9, 1F baths 1255 / 1256, ...);
**no sanitary fixture, tray, screen line or drain is drawn** in any shower room (the only fixture block, WASH2, is a basin
in the GF core lobby and by the stair). No text SHOWER / شاور / دش anywhere (text and MTEXT search). The plan names the
rooms by label block: `bath` (C01, C11, C2C, C2F on 1F), text BATH 2ED on GF, `WC` (1C8, 1F7, 2DA, 322, 323, C19, 12B6).

**Sanitary sheets** (sanitary-7757.pdf, 3 scanned drainage plans, no text layer, read at 110 and 300 dpi; the title
block says "the builder to work with stated dimensions, not to scale drawing", so nothing is scaled from it). The legend
names FD, GCO, CO, RWP, ... but not the fixture symbols; they are read by their standard form:

| Id | Floor / room (T-336 id) | Plan label | Sanitary page and symbol | Kind |
|---|---|---|---|---|
| SH-GF-01 | GF bath by the master bedroom (GF-16) | BATH 2ED | p.1: square tray with diagonal and drain in the NW corner; WC; basin on the diagonal wall; FD 4" | TRAY |
| SH-1F-01 | 1F west twin bath (1F-02) | bath C2C / C2F | p.2: double screen line with centre mark across the room, wall mixer beyond it, FD 3" | WALK-IN |
| SH-1F-02 | 1F west twin bath (1F-03) | bath C2F / C2C | p.2: screen line across the room, wall mixer at the end wall beyond it, FD 4" by the WC | WALK-IN |
| SH-1F-03 | 1F bath by the laundry (1F-09) | bath C01 | p.2: square tray with diagonal and drain in the corner; WC; basin; FD 4" | TRAY |
| SH-1F-04 | 1F east bath (1F-12) | bath C11 | p.2: square tray with diagonal and drain in the SE corner; WC; basin; FD 4" | TRAY |
| SH-2F-01 | 2F W.C. (2F-02) | WC 12B6 | p.3: screen line across the room, wall mixer at the end wall beyond it; WC; FD 4"; basin | WALK-IN |
| UNK-GF-01 | GF driver W.C. (GF-05) | WC 1C8 | p.1: a wall mixer symbol by the FD 4", WC, rectangular basin; no tray, no screen, no text | UNKNOWN (not counted) |

Room binding: each symbol was placed in its room by the two sheets' common frame (street / sea / neighbour sides,
same orientation, no mirror) and the room's labels and doors; the tray / screen sits inside the room outline in every
case. Corroboration (not a rule): every room the plan labels `bath` / BATH holds a shower, and of the `WC` rooms only the
2F one does.

**No sheet dimensions a tray, a screen position or a tanking height**: no detail of the shower or the wet-room
waterproofing was found: the plan DXF's TEXT / MTEXT carry no waterproofing, tanking, membrane or shower note (search
for waterproof / عازل / tank / shower / شاور / دش: only the room label BATH), and the sanitary sheets carry fixtures and
pipes only. The scanned architectural PDF sheets were not re-read by this task (the DXF is the same drawing set).

## 3. Quantities (statuses WORKFLOW_CONTROLS s.5)

| Quantity | Alsenan | Status | Basis |
|---|---|---|---|
| Showers | **6** (3 trays, 3 walk-in) + 1 UNKNOWN mixer-only | DRAWING-CONFIRMED (sanitary sheet) | section 2 |
| Shower-zone floor extent | 6 x **HELD** | HELD | not dimensioned on any sheet; "not to scale" note; information only, no quantity depends on it |
| Walls touched by each zone | 6 x **HELD** | HELD | zone sides not printed |
| B8-04 shower floor membrane, extra over B8-01 | **0.000 m2** | ASSUMED - OWNER-APPROVED | UP-WP-004 1.0.0: the shower floor is the room's B8-01 membrane; the six rooms' B8-01 lines hold 27.615183 m2 (GF-16 3.717683 + 1F-02 5.0225 + 1F-03 5.0225 + 1F-09 3.5775 + 1F-12 4.725 + 2F-02 5.55) |
| B8-04 shower-wall upturn, extra over B8-03 | **0.000 m2** | ASSUMED - OWNER-APPROVED | same rule; inside the rooms' B8-03 0.20 m upturn lines |
| B8-04 tanking above the upturn | **0.000 m2** | ASSUMED - OWNER-APPROVED | Q-40 A (owner 2026-10-19 20:45: "Keep same membrane I gave instruction for, the wet area will be fully tiled, so no need to make extra waterproof"); its condition holds: Q-48 A wet-room tiles to the underside of the decor ceiling in all six rooms |
| UNK-GF-01 | none | UNKNOWN | not a shower on the printed evidence; if a designer confirms a shower there, its floor and upturn are already inside GF-05's B8-01 / B8-03 lines and Q-40 A gives no tanking: **0 m2 impact either way** |

A decided NONE (owner rule) is recorded as 0.000 with ASSUMED - OWNER-APPROVED and its source, never as a measured zero;
a missing extent or wall run stays None (HELD), never 0.

## 4. Double count against the candidate (acceptance c)

Line ids (T-336 piece table, V3.0.21 ids; re-checked on V3.0.28, section 5):

| Room | B8-01 floor line | B8-03 upturn line |
|---|---|---|
| GF-16 | L-538c929be1d81708f09f (3.717683) | L-8b981cb63e87f18b13d4 (1.364933) |
| 1F-02 | L-790a3049c29eda7dad2a (5.0225) | L-ba15212ec9887e6d4f73 (1.640) |
| 1F-03 | L-f15325df772daa7ceec0 (5.0225) | L-6e6daedebef2db6a83bd (1.640) |
| 1F-09 | L-6477c7ef451aae374ecc (3.5775) | L-a93486d24647a9e14445 (1.360) |
| 1F-12 | L-ef429ae8e32c8b5cc641 (4.725) | L-60f100105399a9bdfb08 (1.580) |
| 2F-02 | L-bed47a63708c41b2b150 (5.550) | L-b842beb71b67af783cd7 (1.780) |

B8-04 adds nothing on top of these lines: double count **0**. An integration that emits a B8-04 line must emit it as
0.000 ASSUMED - OWNER-APPROVED (Q-40 A, UP-WP-004) or not at all; `b8_04_floor(add_on_top=True)` is refused.

## 5. Candidate re-check

See the handoff on the board: the V3.0.28 run of this task (research/agents_t326/v3028_run.py on the Drive copies) and the
presence of the twelve line ids above with the quantities shown.

## 6. Against the freelancer (acceptance d)

His FIN workbook, sheet "العازل" rows 14-36 (as parsed in tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json): per
room a wall run (m.l, "height" column 1) and a floor (m2); totals floors 72.01 m2, upturn 144.61 m.l; summary sheet
rows 27-30 the same. **No shower, tray or tanking row.** Engine (this task) 0.000 m2 extra vs freelancer none:
**0.000 m2, 0 %**. Verdict proposal: **NO DIFFERENCE, both by the owner's method** (Q-40 A; he applies the same flat
upturn). His floor rows for the six shower rooms (rows 16, 30, 31, 28, 27, 36: 3.70, 5.00, 5.00, 3.60, 4.72, 5.62 m2)
belong to B8-01 and were reconciled by T-074.

## 7. Differences from the earlier reading (T-010 / T-074)

T-010's sanitary reading (and the T-074 hand table built on it) has 4 showers: GF-13 (core W.C. 245 x 167), 1F-02,
1F-03, 2F-02. This read finds 6, and differs on four rooms:

- GF: the tray is in the bath by the master bedroom (GF-16, label BATH), not in the core W.C. GF-13 (T-010 itself flagged
  the GF core attribution as uncertain). GF-13 shows WC + basin + FD only.
- 1F: the bath by the laundry (1F-09, `bath` C01) and the east bath (1F-12, `bath` C11) each show a square tray that
  T-010 / T-074 list as WC + basin + FD.

**Quantity effect: none** (all these rooms are wet already; B8-01 / B8-03 unchanged; Q-40 A gives no tanking). It
matters for B12-01 fixture counts (T-370 should count 6 showers, not 4) and for any wet-room evidence that cites the
shower as its reason. Cause: room-level fixture lists read at 110 dpi and attributed by position, without the symbol per
room at a resolution where the tray outline is legible.

## 8. General rule (proposed, research; ERS s.4 B) and test

R-T369-1 (scope: every villa; provenance UP-WP-004 1.0.0, Q-40 A, Q-48 A, this task):
1. A shower is identified by a printed mark: tray symbol, screen line with a mixer in its zone, or text. A bath tub
   without a shower mark is not a shower; a mixer symbol alone is UNKNOWN and is not counted.
2. The shower floor membrane and its 0.20 m upturn are the room's B8-01 / B8-03 lines (extra 0, never added on top).
   A shower in a room with no B8-01 line is HELD, never 0.
3. Tanking above the upturn: printed height x printed wall run first; else Q-40 A gives NONE where the wet walls are
   tiled full height (Q-48 A); else HELD. A default height is refused.
4. Extents and wall runs only from printed dimensions; never scaled from a sheet marked "not to scale".

Test: tests/t369_shower_tanking (17 cases): villa E369 tray 0.90 x 0.90 -> 0.81 m2, 1.80 m.l, printed 1.80 m ->
2.88 m2; walk-in 1.00 x 2.00 -> 2.00 m2, 4.00 m.l, Q-40 A -> 0.000 OA; mm / cm / m; mirror / rotation; adverse: default
height refused, shower floor on top refused, bath as shower refused, mixer only UNKNOWN, missing dimensions HELD,
unitless refused, Q-40 A with tiling unknown HELD; Alsenan register pins.

## 9. Lessons register row (proposed, ERS s.7)

| 2026-10-30 | Two shower trays missed and one shower placed in the wrong GF room by the T-010 / T-074 sanitary reading (6 showers, not 4) | fixtures read as room lists at low resolution and attributed by position; no per-room symbol record | every fixture reading records the symbol kind per room with the sheet page and the room's plan label; a shower needs a printed mark (tray, screen + mixer, text); a mixer alone is UNKNOWN (scope: every villa; provenance T-369) | tests/t369_shower_tanking (register pins; mixer-only and bath-only refused as showers) | PROPOSED |

## 10. Open

- Tray sizes and walk-in zone depths are not dimensioned (6 HELD extents): only needed if a later rule measures shower
  floors separately (falls screed, a separate tray item), not for B8-01 / B8-04.
- UNK-GF-01 (GF driver W.C. mixer symbol): designer clarification candidate only if a fixture count needs it; 0 m2 WP
  impact either way.
