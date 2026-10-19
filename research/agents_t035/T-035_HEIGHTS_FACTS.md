# T-035: Alsenan wall heights for plaster and paint (facts file), development villa

Worker run 2026-10-19. Development reference only, not an accuracy claim. Branch from 3f47ec2 (T-001b not merged).

## Result

No wall-finish height and no height component (slab soffit zone, floor build-up, ceiling zone) is printed on any
Alsenan drawing that can be read. `tests/alsenan/facts/ALSENAN_ARCH_FACTS_V1.json` therefore carries no height value:
it validates (`engine/source/arch_measure.py:61` validate_facts), records what was searched and, per floor and trade,
what is missing. With `--facts` the run is line-for-line identical to the run without it (1 455 lines, 0 differing in
item, location, quantity or state) and the PLASTER / PAINT scoreboard rows do not change: both stay covered but HELD.
Nothing was filled from the freelancer's sheets, a typical value or the floor-to-floor interval (UP-HGT-001).

## What the drawings print (heights only)

| Source (Drive "Alsenan chalet project") | Heights printed |
|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf (sha ab54dd55...31cc4 = manifest) | GF levels +0.15, +0.30, +1.00; 1F +5.50 and +4.30 (roof over part of GF); 2F +9.70; SE and NW elevations: level texts and vertical dimension chains (1 000, 4 500, 4 200, 500 parapet, 14 400 overall). No section drawing, no ceiling, soffit or build-up note. All texts read, nested blocks included. |
| ST7757 dxf.dxf (sha 9f9d1179...38079 = manifest) | Same plan levels, +9.70 on the second-floor roof slab plan; beam schedule depths 0.40 to 0.75 m; sections A-A to D-D dimension openings and bars only; "5 cm screed, 5 cm insulation membrane, 10 cm plain concrete" on the swimming-pool detail; "T=10cm" on the ground beams plan. No slab thickness is dimensioned or noted. |
| architectural DWF (title ends 2026-05-06T113026.059.dwf), text strings only | Adds sections A-A and B-B with levels up to +13.90 (roof) and vertical dimensions in cm (100, 450, 420, 420, 50, 1390, ...): level intervals and parapets. Viewing format: cross-check only (owner instruction 1), never a measured source. |
| sanitary-7757.pdf | Drainage plans; no heights. |
| architectural PDF (37.5 MB, 12 image pages) | Not readable: above the connector's 10 MB limit. Its sheet set appears to match the DWF (plans, area plans, 4 elevations, 2 sections, fence). |

## Why each candidate was not entered

- Floor-to-floor intervals (GF 4.50 / 5.20 / 5.50 m, 1F 4.20 m): a level interval alone is never a wall height
  (UP-HGT-001; WALL_HEIGHT_AUTHORITY_POLICY_V1). The engine already derives them from the plan levels and asks for the
  components (UP-CER-009 RFI on each held line).
- Beam depths: plaster runs to the slab soffit (UP-HGT-001 trades.PLASTER); which walls sit under a beam is not in the
  plan (UP-MAS-HEIGHT-001 logic.beams). A beam depth is not the room's soffit zone.
- Pool-detail build-up and T=10cm: they belong to the pool and the slab on grade, not to a room floor build-up or a
  suspended slab.
- Slab thickness: drawn in the structural sections but not dimensioned; a value scaled from the drawing is not a
  printed dimension (task acceptance).

## Held lines after the rerun (named reasons, same as T-001b)

| Trade | Held | Reason (count) |
|---|---|---|
| PLASTER (FIN.PLASTER) | 29 | WALL_FINISH_HEIGHT_NOT_ESTABLISHED UP-CER-009 (25: GF 12, 1F 11, 2F 2); STAIR_HALL_FINISH_NOT_ESTABLISHED Q-S6-4 (2); JAMB_HEIGHT_CLASS_PENDING UP-DOOR-HGT-001, bounded (2) |
| PAINT (FIN.PAINT) | 13 | WALL_FINISH_HEIGHT_NOT_ESTABLISHED UP-CER-009 (11: GF 5, 1F 5, 2F 1); STAIR_HALL_FINISH_NOT_ESTABLISHED Q-S6-4 (2) |

Released, unchanged: 20 plaster lines (door jambs and heads, PROVISIONAL, 17.74 m2); 14 paint lines are
NOT_APPLICABLE (paint above wall tile). Scoreboard rows (tools/alsenan_scoreboard.py, unchanged by the facts file):

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | Signed | False pos. | Duplicates |
|---|---|---|---|---|---|---|---|---|---|---|
| PAINT | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 |
| PLASTER | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 |

## For the lead

1. What would release these lines: per floor (GF, 1F, 2F) the slab soffit zone and the floor build-up (plaster), plus
   the ceiling zone (paint), each with an authority; or the plaster and paint heights directly. Only the owner (or the
   designer through him) can supply them as OWNER_PROJECT_FACT (rank 4). Owner question Q-14.
2. The 2F rooms have no level interval at all: the plans print nothing above +9.70; the roof +13.90 appears only in the
   sections of the DWF/PDF. Reading section levels is section-binding work (T-013), not a facts entry.
3. If the architectural PDF is put on Drive as a zip under 10 MB (or the section pages alone), a worker can confirm
   that its sections print no thickness or build-up either.

## Reproduce (outside the clone; nothing private committed)

```bash
python3 -I tools/urban_boq_m9.py arch --drawings P7757.dxf --out RUN --method ARCH_TAKEOFF_V2.9 --structural ST7757.dxf \
    --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json --no-m9-xlsx --no-svg \
    --facts tests/alsenan/facts/ALSENAN_ARCH_FACTS_V1.json
python3 -I tools/alsenan_keymap.py --run RUN --reference tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json \
    --key-map tests/alsenan/T001B_KEY_MAP.json --out SCORE.json --markdown SCORE.md
```
