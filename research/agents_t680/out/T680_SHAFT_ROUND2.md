# T-680 stair-shaft ST-01 plaster / paint storey-band lines, round 2

Candidate ARCH_TAKEOFF_V3.0.65. Research only, nothing wired.

Heads applied (R-T680-1, T-201 DWF vector, Checker-verified):
- 1F-north-window = W25: sill +5.500 / head +7.000, width 1.00 (DRAWING-CONFIRMED; DWF SOUTH WEST ELEVATION (vector); current issue Pages_07-08 p.7; issue check AGREES (max edge offset 0.006 m))
- W27 = W27: sill +9.700 / head +11.200, width 1.00 (DRAWING-CONFIRMED; DWF SOUTH WEST ELEVATION (vector); current issue Pages_07-08 p.7; issue check AGREES (max edge offset 0.013 m))

Baseline reproduction (T-173 model + T-640 corrections, before this task's changes):

| line | band | finish | reference | reproduced | match |
|---|---|---|---|---|---|
| L-95f2c45c2eccaaeccb08 | GF | plaster | 48.52 .. 62.01 | 48.52 .. 62.01 | True |
| L-145bd2394f2907558243 | GF | paint | 48.52 .. 62.01 | 48.52 .. 62.01 | True |
| L-0eac839f9132da7bd116 | 1F | plaster | 42.48 .. 47.67 | 42.48 .. 47.67 | True |
| L-2ab93d5029a4b7cc4dca | 1F | paint | 42.48 .. 47.67 | 42.48 .. 47.67 | True |
| L-418121a4b223cb4e8646 | 2F | plaster | 44.512 .. 49.872 | 44.508 .. 49.868 | True |
| L-5a7a5c6f070ec7142ca5 | 2F | paint | 42.722 .. 47.932 | 42.723 .. 47.933 | True |

| line | code | band | candidate | overlay | heads only | returns lo / hi | restated | change low / high |
|---|---|---|---|---|---|---|---|---|
| L-95f2c45c2eccaaeccb08 | FIN.PLASTER | GF | 48.52 .. 62.01 | - | 50.522 .. 62.011 | 0.423 / 0.423 | 50.945 .. 62.434 | 2.425 / 0.424 |
| L-145bd2394f2907558243 | FIN.PAINT | GF | 48.52 .. 62.01 | - | 50.522 .. 62.011 | 0.423 / 0.423 | 50.945 .. 62.434 | 2.425 / 0.424 |
| L-0eac839f9132da7bd116 | FIN.PLASTER | 1F | 42.48 .. 47.67 | - | 44.921 .. 46.168 | 0.396 / 0.396 | 45.317 .. 46.564 | 2.837 / -1.106 |
| L-2ab93d5029a4b7cc4dca | FIN.PAINT | 1F | 42.48 .. 47.67 | - | 44.921 .. 46.168 | 0.396 / 0.396 | 45.317 .. 46.564 | 2.837 / -1.106 |
| L-418121a4b223cb4e8646 | FIN.PLASTER | 2F | blank | 44.512 .. 49.872 | 46.948 .. 48.368 | 0.394 / 0.404 | 47.342 .. 48.772 | 2.830 / -1.100 |
| L-5a7a5c6f070ec7142ca5 | FIN.PAINT | 2F | blank | 42.722 .. 47.932 | 45.013 .. 46.433 | 0.379 / 0.389 | 45.392 .. 46.822 | 2.670 / -1.110 |

| code | HELD lines | before: bounded sum (n) + blank | after T-680 | change low / high | with T-676 OP-009 |
|---|---|---|---|---|---|
| FIN.PLASTER | 24 | 932.72581 .. 1006.77641 (14) + 10 blank | 985.32981 .. 1054.86641 (15) + 9 blank | 52.60400 / 48.09000 | 985.32981 .. 1054.74641 |
| FIN.PAINT | 10 | 487.1210 .. 542.8606 (7) + 3 blank | 537.7750 .. 589.0006 (8) + 2 blank | 50.6540 / 46.1400 | 537.7750 .. 589.0006 |

Shaft sums (m2): plaster 143.604 .. 157.770; paint 141.654 .. 155.820

Plaster coat materials (Q-79 1:4; T-676 R-T676-3):
- L-95f2c45c2eccaaeccb08 GF: cement 7.805589 .. 9.565888 bags, sand 1.08411 .. 1.328596 m3; spatter dash HELD; water HELD
- L-0eac839f9132da7bd116 1F: cement 6.943289 .. 7.13435 bags, sand 0.964346 .. 0.990882 m3; spatter dash HELD; water HELD
- L-418121a4b223cb4e8646 2F: cement 7.253552 .. 7.472651 bags, sand 1.007438 .. 1.037868 m3; spatter dash HELD; water HELD

Stair-core wet-room plaster lines (stay HELD, datum named):
- L-a636dabcd4bc7e59169a GF-RD36087:plaster: GF-RD36087 finished floor level: +0.30 (lobby) or +1.00 (main GF) - no floor edge or level is drawn under the stair-core rooms (T-088; T-173 C-SH-2): designer item; the top of the wet-wall render: the 1F slab soffit (+5.50 - b - 0.16), build-up b 0 .. 0.10; the head of the doorless passage OP-020 (0.90 m, shared with the stair hall; head lines hidden, no head printed; T-441)
- L-3f7fb1b37e68e6d6c7b7 GF-RDF7D28:plaster: GF-RDF7D28 finished floor level: +0.30 (lobby) or +1.00 (main GF) - no floor edge or level is drawn under the stair-core rooms (T-088; T-173 C-SH-2): designer item; the top of the wet-wall render: the 1F slab soffit (+5.50 - b - 0.16) or the soffit of the beam crossing the room (T-283: bulkhead edges on CONFLICT / HELD beams, Q-61 C); the window OP-014 head / sill (no T-201 record; the line carries the window as EXCLUDED)
