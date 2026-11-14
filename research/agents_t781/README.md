# T-781 ONE OPENING TABLE (OPENING_TABLE_V1, owner ACCURACY_PLAN_2026-11-14 change D)

New module `engine/source/opening_table_v1.py` (pure, project-agnostic; not wired: no candidate line changes; the
T-772 command registers it later in `tools/urban_boq_run.py` PLUGINS["opening_table"]).

One row per opening: id, floor, type (WINDOW / DOOR / SHUTTER / GLASS_DOOR / ARCH / PASSAGE / LIFT), side, W, H,
wall thickness, sill, head, opening m2 = masonry deduction m2 (Q-73), precast lintel (owner 2026-11-02), each value
labelled MEASURED / SCHEDULE / DRAWING-READ / DEFAULT / HELD. Classification by block / layer name first, then plan
geometry. Defaults (owner 2026-11-13): window sill 0.90 dry / 1.60 wet; window head = the floor's printed window head,
else 2.20; doors and passages on the floor, head 2.20 (Q-55 C) unless printed (a printed main-entrance head is never
spread). Elevation reads bind by floor + kind + width; a group of equal widths takes a reading only when the reads
agree, or when there is exactly one complete read per opening (group sums exact, PER_OPENING_ORDER_UNPROVEN); reads
with no plan opening become ELEVATION_ONLY rows (PLAN_SYMBOL_NOT_DETECTED). A missing width is HELD (never 0).
Arched heads: head = the window's own arch crown, area = W x crown (owner Q-32 A / Q-76 A).

## Alsenan run (Drive P7757_DXF_COMPRESSED.zip, geometry ARCH_TAKEOFF_V2.13 unchanged)

    bash scripts/agent_env.sh run --tree task-T-781 research/agents_t781/geometry_t781.py <plan.dxf> --out <private>/geo
    bash scripts/agent_env.sh run --tree task-T-781 research/agents_t781/alsenan_t781.py --geo <private>/geo \
        --out <private>/table --write-summary

Inputs: the run's ARCH_OPENINGS / OPENING_SCHEDULE / ARCH_ROOMS (60 plan openings) + 31 elevation reads taken from the
committed drawing readings (T-201 outlines, T-198 printed heights, T-207 louvred-leaf outline, T-238 arch crowns,
owner Q-76 A), bound by floor + kind + width only (census ids never bind). Output `out/OPENING_TABLE_ALSENAN.json`
(engine ids, sizes, labels only).

| check | table | reference | diff |
|---|---|---|---|
| rows with W or H blank | 0 of 62 | 0 | - |
| windows + shutters m2 | 100.096 (29 pcs) | T-768 candidate 100.05 (29 pcs) | +0.05 % |
| windows m2 vs freelancer | 100.10 | 116.9 | -14.4 %, split in T-768 (W02 head, drawn heads, W17 Q-76 A) |
| external doors pcs | 6 = 5 aluminium + 1 main entrance | his 5 (rows 4 + 1) | causes below |

Without the arch-crown reads (T-198 rectangular heads only) the table gives 102.05 m2 (+2.0 %): W17 3.50 band top read
as head (+1.64, owner Q-76 A says the crown 3.00) and W15 / W16 band crown 3.10 read as head (+0.31, T-238).

External doors "12 vs 6 pcs" (owner table 13 Nov): his 12 is the doors **m2** cell of his aluminium cover sheet
(4 x 1.00 x 2.40 + 1 x 1.00 x 2.40 = 12.0 m2 = 5 doors), UNIT_MISREAD. Pcs: ours 6 = 5 aluminium external + 1 main
entrance (2.00 double leaf, not in his aluminium workbook) -> residual 0 pcs; shutters / glass doors in his count: 0
(the classification hypothesis is refuted). m2 (aluminium external, 10.56 vs 12.00, -1.44): height 2.20 Q-55 C vs his
2.40 = -0.96 RULE_DIFFERENCE; plan band widths 0.90 on two doors vs his 1.00 = -0.48 ENGINE_RIGHT; residual 0.00.

Open: 5 rows PER_OPENING_ORDER_UNPROVEN (1F three 1.55 windows, 2F two 1.20 windows: group sums exact); W03 (6.57
curved) and W18 (0.50) are not detected on the plan by the V2.13 reader (ELEVATION_ONLY rows, D-N10-01 / L-P9-02);
lift openings come out as PASSAGE (the shaft is not a room kind the table reads yet); internal door count 16 vs T-768
PVC 20 (the T-198 closure-only doors, read from jamb hits, are not band openings in the V2.13 reader; not reconciled
in this row).
