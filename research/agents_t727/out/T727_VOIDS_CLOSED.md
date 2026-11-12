# T-727 V-01 light-well deductions closed (ARCH_TAKEOFF_V3.0.72; research, unwired; no line moved)

Rules R-T727-1 .. -4 (t727_rules.py); tolerance 0.005 m2.

## 1. F1 / F4 overlap by handle

- B43 (layer 5, F4 first riser) 1.15 m and B4E (layer 2, F1 last line) 1.15 m, parallel True, 0.05 m apart: strip 0.057500 m2.
- Engine footprints F1 x F4: 0.057438 m2 (0.05 x 1.15); handle - engine -0.000062 m2 (F1 is radial: its last riser is drawn 1.1498 wide (engine riser_widths), so its last quad is a hair short of the 1.150 rectangle between B43 and B4E).
- GF plan draws the same pair: {'B43': [['22F', '5']], 'B4E': [['234', '2']]}. Inside the void window 0.0, inside the well 0.057438 m2.

## 2. 1F living porcelain L-b06400d4

- Net 33.411036 (RELEASED); record of the net: RECORD_OF_NET (residual 0.000000).
- Face in well 26.1725: net record rows in the well -> DEDUCTED_ONCE (residual 0.000432); below-seen rows {'F1': '1.981743', 'F4': '3.352442', 'F6': '1.380000'} = 6.714185 (union 6.71423).
- Own geometry (void + union increments + remainder): DEDUCTED_ONCE (residual 0.000000).
- T-719 base-list check: DEDUCTED_TWICE (-0.057168); its if-corrected 33.468204 is NOT applied.
- Verdict: ENGINE_RIGHT on the net (the overlap is deducted once, on F1; F4 carries its union increment); T-719 finding (1) withdrawn: it checked the superseded base list (ENGINE_LIST_STALE, T-345), not the record that set the net. Corrected figure: **33.411036 m2** (unchanged).

## 3. Ceiling over V-01

- 2F plan over the well: {'CIRCLE/5': 1, 'INSERT/4': 1, 'LINE/S-COL.BON': 1}; opening outline found: False (roof slab closed; block ROOF).
- Decor face split {'decor': '51.0496', 'ST-01 stair zone': '10.7250', 'east dome HELD': '14.0359', 'stair beyond face': '0.1725', 'sum': '75.983000', 'face': '75.983002', 'residual': '0.000002'}; line L-43bf1f86 = ledger: True.
- Well top in the decor face 26.064062 m2; under the east dome (HELD) 0.108438 m2; ST-01 stair zone (own flights F2 / F3 / F5) in the well 0.0 m2, 3.686801 m away (the 0.1725 band piece is the ST-01 first going, T-283).
- Owner L-43bf1f86; [('L-35341ff2e6a848b9436b', 'DUPLICATE_FACE of L-43bf1f869e1588f1d3bd')]; result ONCE.

## 4. V-07

- HELD VOID_EXTENT_UNRESOLVED: 2F plan layer-2 circle 1300 r 2.205018 drawn 'above'; no opening line on any plan and no structural drawing; scenario S0 (approved design, no opening) vs S1 (open skylight) not decided (Q-29 / T-185).

## 5. Downstream (named)

- FIN.MARBLE.TREAD 1F-R78C367 flights 1 / 4 (HELD 0 .. high): highs 7.544413 vs union 7.486974 -> 0.057439 m2, DOUBLE_COUNT_RISK in the held highs (R-T727-1); stair ledger (lane A stairs / T-725 family); never valued as the sum.
