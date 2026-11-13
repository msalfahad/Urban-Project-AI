# IGNORED_SMALL: concrete pieces known to be below 0.05 m3 (owner materiality rule 2026-11-13 14:00)

Rule (DELIVERY_MODE s.3): a concrete piece KNOWN to be < 0.05 m3 is ignored and logged here by line id; the ONE safety
line STR.CONC.SAFETY = 1 m3 if the ignored sum is below 1 m3, else the sum. The rule file and its test belong to T-757;
rows that apply it append here. Sizes are the DEFAULT figures of the source fix-row set (never VERIFIED).

| line | item | element | size m3 | basis | source |
|---|---|---|---|---|---|
| L-89d266a3e5280a10a3b9 | STR.CONC.BEAM | 1F-NW-CORNER strip piece | 0.0176 | 0.029309 m2 x 0.60 default | T-761 |
| L-e296002577c012f0afd4 | STR.CONC.BEAM | GF-NW-CORNER strip piece | 0.0176 | 0.029309 m2 x 0.60 default | T-761 |
| L-b4a13a43967ee4765662 | STR.CONC.GROUND_BEAM | BAND0017.2 | 0.0450 | 0.15 m2 x 0.30 class depth | T-761 |
| L-be6708e07b40efa02779 | STR.CONC.GROUND_BEAM | BAND0013.1 | 0.0090 | 0.03 m2 x 0.30 class depth | T-761 |
| L-1313767d897f06ef95b6 | STR.CONC.LINTEL | W04 | 0.0360 | 0.20 x 0.20 x (0.60 + 0.30) | T-761 |
| L-17953d7882899d43473f | STR.CONC.LINTEL | D-GF-14 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-1c0e7646345156fcd0cb | STR.CONC.LINTEL | D-2F-02 | 0.0480 | 0.20 x 0.20 x (0.90 + 0.30) | T-761 |
| L-274b112580029084b80e | STR.CONC.LINTEL | D-GF-04 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-2c1c49db7cd7b16c6206 | STR.CONC.LINTEL | D-1F-01 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-961608860fcb38c106af | STR.CONC.LINTEL | D-1F-09 | 0.0360 | 0.15 x 0.20 x (0.90 + 0.30) | T-761 |
| L-9ec762c0bd529b924f33 | STR.CONC.LINTEL | D-1F-06 | 0.0330 | 0.15 x 0.20 x (0.80 + 0.30) | T-761 |
| L-b729bd6381f216153df8 | STR.CONC.LINTEL | A-GF-01 | 0.0390 | 0.15 x 0.20 x (1.00 + 0.30) | T-761 |
| L-d887eecf51c121831336 | STR.CONC.LINTEL | P-GF-01 | 0.0480 | 0.20 x 0.20 x (0.90 + 0.30) | T-761 |

Sum T-761: 0.4282 m3 on 13 lines (< 1 m3) -> STR.CONC.SAFETY 1.00 m3 (SAFETY), proposed in
research/agents_t761/out/FIX_ROWS.json on agents/task-T-761. T-757 adds the bounded small ranges to this same table and
keeps ONE safety line.
