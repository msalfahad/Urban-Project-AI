# T-663 rebar ratio: the four wiring conditions (R-T663-1 .. 4; generated)

Candidate ARCH_TAKEOFF_V3.0.61 + WIRING MANIFEST V20 (trial BOQ r4, T-654). NOTHING RELEASED; research, unwired; no candidate / engine / rule-version / knowledge / registry file changed; R-T662-1 used as it is.

## (1) Range check (R-T663-1)

| type | calibrated kg/m3 | status |
|---|---|---|
| FOOTING | 68.680658 .. 71.140741 | NOT_CHECKED_NO_CITED_SOURCE |
| BEAM | 147.788330 .. 175.869052 | NOT_CHECKED_NO_CITED_SOURCE |
| GROUND_SLAB | 61.728392 .. 61.728392 | NOT_CHECKED_NO_CITED_SOURCE |

Finding: no Drive engineering book that the connector can read prints a kg/m3 range per element type; owner question Q-81 alternative B (cited book ranges) has no source today.

Sources searched:

- Engineering Sources - Urban Projects / 01 Kuwait References: Kuwait Society of Engineers home-building guide 2023 (Arabic, 2.6 MB): read in full through the connector: contract templates and MEP clauses; no reinforcement kg/m3 table
- Engineering Sources - Urban Projects / 02 Construction Books: reinforced-concrete design summary to the 2020 code (Arabic, 5.2 MB): connector text is glyph-encoded (unreadable): SOURCE NOT READ
- Engineering Sources - Urban Projects / 02 Construction Books: code summary, site-supervision, finishes, construction-mistakes and project-management books: over the connector size limit (7.6 .. 82 MB): SOURCE NOT READ
- Engineering Sources - Urban Projects / 03 International Codes: ACI 318-2025, ACI 318-2014 Arabic, IBC 2009 / 2018 / 2021, IPC 2006: over the connector size limit (9.7 .. 45 MB): SOURCE NOT READ; design codes print minimum / maximum reinforcement percentages, not estimating kg/m3 per element type
- Engineering Sources - Urban Projects / 04 Regional Codes: QCS 2014, Dubai Building Code, Saudi codes, Egyptian code update: over the connector size limit or not a quantity reference: SOURCE NOT READ
- Urban Projects - Kuwait Engineering References (1rr88a1t...): folder listing: no file listed under this folder id by the connector
- Drive full-text search: 'kg/m3' + 'reinforcement'; 'كجم/م3'; 'steel per cubic meter': hits only in code books (units of other quantities) and project notes; no estimating ratio table

## (2) Footing PARTIAL members (R-T663-3)

- ST p.9 footing schedule: F12, F13, F14 and FF carry a closed cage symbol in REMARKS and TOP / BOT rows (n ø14/m TOP, n ø14 or ø16/m BOT); no leg length, no bar-shape code
- ST p.13 typical isolated footing (both variants): 'Boxed bars' drawn as an inverted U whose legs run down to the bottom mesh; no leg dimension
- ST p.14 lift footing (FF): closed cage, depth 'AS PER SCHEDULE' (H 55 cm on p.9); no leg dimension, no cover
- ST p.8 note 22: cover NOT LESS THAN 7 cm against soil (a minimum: a leg <= H - 2 x 7 cm is an upper bound only; no lower bound is printed)

Decision: R-T663-3: TOP_END_LEGS stay HELD blank by name; the four footings stay PARTIAL (no ratio, no calibration); FOOTING calibration stays n = 1 (F8, WEAK).

| member | blank groups | state | m3 | whole-member ratio (NOT applied) |
|---|---|---|---|---|
| FOOTING:SH10:F12:67454a | TOP_END_LEGS | PARTIAL | 9.856000 | 697.224062 .. 736.221300 |
| FOOTING:SH10:F13:6b1a4d | TOP_END_LEGS | PARTIAL | 5.160000 | 365.023961 .. 385.440535 |
| FOOTING:SH10:FF:8e679c | TOP_END_LEGS | PARTIAL | 11.385000 | 805.387170 .. 850.434203 |
| FOOTING:SH10:F14:73a8e9 | TOP_END_LEGS | PARTIAL | 6.270000 | 443.546557 .. 468.355068 |

## (3) Laps in the calibration kg (R-T663-2)

| type | members | passing | lap kg | end anchorage kg kept |
|---|---|---|---|---|
| BEAM | 44 | 44 | 0.000000 .. 0.000000 | 381.928000 .. 668.367000 |
| FOOTING | 1 | 1 | 0.000000 .. 0.000000 | 0.000000 .. 0.000000 |
| GROUND_SLAB | 24 | 24 | 0.000000 .. 0.000000 | 0.000000 .. 0.000000 |

Splice need (T-366): {"BEAM-SIMPLE-MAIN": "NOT_REQUIRED", "CB-BOTTOM": "DRAWN_OVERLAP", "FTG-BOTTOM": "NOT_REQUIRED", "FTG-TOP": "NOT_REQUIRED", "GROUND-SLAB-MESH": "NOT_ESTABLISHED"}.
BEAM sensitivity (shown, not applied): 113.636461 .. 116.103907 kg/m3 without the end anchorage.
Ground slab: ratio = 2 x 5 bars/m x 0.617284 kg/m (d10) / 0.10 m slab: the bare mesh, no lap kg inside (61.728395).

## (4) Binding of the NOT_BOUND members (R-T663-4)

| type / result | members |
|---|---|
| BEAM|NOT_BOUND | 15 |
| GROUND_BEAM|BOUND | 8 |
| GROUND_BEAM|NOT_BOUND | 63 |
| OTHER|NOT_BOUND | 8 |
| POOL_TANK_WALL|NOT_BOUND | 2 |
| SLAB|NOT_BOUND | 65 |
| STAIR|BOUND | 2 |
| STAIR|NOT_BOUND | 12 |

| member | state | bound | concrete | reason |
|---|---|---|---|---|
| BEAM:BM-GF-039 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-7D0-FC-4 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| STAIR:ST-01:GF-STRIP | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01:GF-STRIP (composite or absent concrete part) |
| SLAB:2F-011 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-169 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-184-7CF-3 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0010.1  | (c) GROUND_BEAMS:GROUND:BAND0010.1 is also named by ['GROUND_SYSTEM:GSO-184-7CF-1']: shared band, never split by guess |
| BEAM:BM-GF-027 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| BEAM:BM-1F-007 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| SLAB:1F-088 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-139 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-126 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-098 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-142-7D8-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-141-7DA-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| STAIR:ST-01:MS2-U | PARTIAL | yes | HL:STAIR_CONCRETE:ST-01:MS2_U ['1.001373', '1.001373'] | (a)-(c) the same stair part id in both hand ledgers (separator '-' / '_' normalised), one live line; (d) no second m3 measure for the steel row: binding by id only |
| GROUND_SYSTEM:GSO-145-7CA-2 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0005.1  | (c) GROUND_BEAMS:GROUND:BAND0005.1 is also named by ['GROUND_SYSTEM:GSO-145-7CA-1']: shared band, never split by guess |
| SLAB:GF-105 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| BEAM:BM-2F-003 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-17D-7E4-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0029 ['0.512675', '0.512675'] | (a)-(d) pass: register 0.512640 vs line 0.512675 m3 |
| SLAB:1F-020 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-7D0-FC-3 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:1F-086 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| POOL_TANK_WALL:POOL:R1 | NONE | no | -  | (a) pool bar rows R1 / R2 each mix wall and floor bars; the pool concrete is split WALLS / BASE: no one-to-one id |
| GROUND_SYSTEM:GSO-7E7-7E8-2 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0032 ['0.423000', '0.423000'] | (a)-(d) pass: register 0.423000 vs line 0.423000 m3 |
| GROUND_SYSTEM:GSO-170-7C3-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-027 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| STAIR:ST-03:E1 | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-03:E1 (composite or absent concrete part) |
| BEAM:BM-GF-050 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| STAIR:ST-01:MS1-U | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01:MS1-U (composite or absent concrete part) |
| SLAB:GF-128 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-077 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-10A-7C9-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-141 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:2F-047 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| POOL_TANK_WALL:POOL:R2 | NONE | no | -  | (a) pool bar rows R1 / R2 each mix wall and floor bars; the pool concrete is split WALLS / BASE: no one-to-one id |
| GROUND_SYSTEM:GSO-7E9-7EA-1 | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-170-7C3-3 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-13F-7D3-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0014 ['0.516000', '0.516000'] | (a)-(d) pass: register 0.516000 vs line 0.516000 m3 |
| SLAB:1F-025 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:2F-016 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-170-7C3-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-114-115-7DF-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7E0-FD-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0026.1  | (d) two measures disagree: register 1.039500 vs line 1.881000 m3 |
| SLAB:GF-124 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-7D4-F8-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-17E-17F-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0037.1  | (d) two measures disagree: register 0.296040 vs line 0.218423 .. 0.291231 m3 |
| SLAB:1F-091 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-052 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| BEAM:BM-GF-051 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| SLAB:2F-045 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-015 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-023 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-15E-15F-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0036.1  | (d) two measures disagree: register 0.360000 vs line 0.324000 m3 |
| SLAB:1F-096 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-063 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-145-7CA-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0005.1  | (c) GROUND_BEAMS:GROUND:BAND0005.1 is also named by ['GROUND_SYSTEM:GSO-145-7CA-2']: shared band, never split by guess |
| GROUND_SYSTEM:GSO-A-157-158-1 | NONE | no | -  | (b) GROUND_BEAMS:GROUND:BAND0044: 0 candidate ids / not exactly one live line |
| STAIR:ST-01:MS1-L | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01:MS1-L (composite or absent concrete part) |
| SLAB:GF-020 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-016 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-036 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:2F-033 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-018 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-018 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-140-7D7-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0018 ['0.516000', '0.516000'] | (a)-(d) pass: register 0.516000 vs line 0.516000 m3 |
| STAIR:ST-02:RS-A | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-02:RS-A (composite or absent concrete part) |
| SLAB:1F-094 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:SB1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| BEAM:BM-1F-013 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-107-7CE-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-16F-7FF-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| BEAM:BM-1F-028 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| STAIR:ST-02:RS-S | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-02:RS-S (composite or absent concrete part) |
| SLAB:GF-079 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-135 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-032 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| BEAM:BM-GF-038 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-180D-180E-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0040  | (d) two measures disagree: register 0.567000 vs line 0.189000 .. 0.189000 m3 |
| GROUND_SYSTEM:GSO-137-138-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-184-7CF-2 | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| STAIR:ST-01:MS2-L | PARTIAL | yes | HL:STAIR_CONCRETE:ST-01:MS2_L ['1.033445', '1.033445'] | (a)-(c) the same stair part id in both hand ledgers (separator '-' / '_' normalised), one live line; (d) no second m3 measure for the steel row: binding by id only |
| GROUND_SYSTEM:GSO-7E7-7E8-1 | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-039 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:SB2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7E0-FD-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:1F-084 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-081 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-073/c1 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-041 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-101 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:through column 20B (7D4-F8) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-173 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-134 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-176 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| STAIR:ST-01:1F-STRIP | PARTIAL | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01:1F-STRIP (composite or absent concrete part) |
| SLAB:1F-065 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:through column 1E0 (170-7C3) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-10B-7D1-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0012.1  | (d) concrete line HELD blank: no second measure |
| GROUND_SYSTEM:GSO-1811-1812-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0041  | (d) concrete line HELD blank: no second measure |
| GROUND_SYSTEM:GSO-A-139-13A-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-078 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:2F-025 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:SB3 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7D0-FC-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-176-7E6-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0031 ['0.450000', '0.450000'] | (a)-(d) pass: register 0.450000 vs line 0.450000 m3 |
| BEAM:BM-GF-022 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| BEAM:BM-GF-060 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-10B-7D1-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-17C-7E3-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-178-7DB-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0022  | (d) concrete line HELD blank: no second measure |
| SLAB:1F-090 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-185-7C7-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-137 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-17B-7E5-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-172 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-13D-7D2-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7DC-7DD-2 | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:through column 251 (7D0-FC) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:1F-073/c0 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-13E-7D6-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0017.1  | (d) two measures disagree: register 0.918000 vs line 0.516000 m3 |
| GROUND_SYSTEM:GSO-109-7CB-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0006.1  | (d) two measures disagree: register 2.565000 vs line 0.528000 m3 |
| GROUND_SYSTEM:through column 1E4 (170-7C3) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-180-181-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0038 ['0.071008', '0.071008'] | (a)-(d) pass: register 0.071010 vs line 0.071008 .. 0.071008 m3 |
| SLAB:1F-076/c1 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:through column 249 (7D0-FC) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:2F-013 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-062 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-136-7D5-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0016  | (d) concrete line HELD blank: no second measure |
| GROUND_SYSTEM:GSO-109-7CB-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7D4-F8-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7E1-7E2-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0027 ['1.209600', '1.209600'] | (a)-(d) pass: register 1.209600 vs line 1.209600 m3 |
| STAIR:ST-01b:D1 | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01b:D1 (composite or absent concrete part) |
| BEAM:BM-GF-015 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-15C-7CC-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-146 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:GF-059 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:band 170-7C3 continuous run | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-7D0-FC-2 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| GROUND_SYSTEM:GSO-15D-7C8-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| BEAM:BM-2F-014 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-114-115-7DF-1 | PARTIAL | no | P-C:GROUND_BEAMS:GROUND:BAND0025.1  | (d) two measures disagree: register 0.708750 vs line 0.209250 .. 0.279000 m3 |
| GROUND_SYSTEM:GSO-182-183-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0039  | (d) two measures disagree: register 0.248760 vs line 0.186592 .. 0.186592 m3 |
| GROUND_SYSTEM:GSO-184-7CF-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0010.1  | (c) GROUND_BEAMS:GROUND:BAND0010.1 is also named by ['GROUND_SYSTEM:GSO-184-7CF-3']: shared band, never split by guess |
| SLAB:GF-061 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F-076/c0 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-13C-7D9-1 | PARTIAL | no | -  | (a) no committed register row names a concrete component of the member |
| BEAM:BM-GF-052 | PARTIAL | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:GSO-177-7CD-1 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0008.1  | (c) GROUND_BEAMS:GROUND:BAND0008.1 is also named by ['GROUND_SYSTEM:GSO-177-7CD-2']: shared band, never split by guess |
| SLAB:1F-057 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:through column 255 (7D0-FC) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:1F-060 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-7DC-7DD-1 | NONE | no | -  | (b) GROUND_BEAMS:GROUND:BAND0023.1: 0 candidate ids / not exactly one live line |
| STAIR:ST-01:MS1-T | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-01:MS1-T (composite or absent concrete part) |
| STAIR:ST-02:RS-LD | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-02:RS-LD (composite or absent concrete part) |
| GROUND_SYSTEM:GSO-175-7DE-1 | NONE | yes | P-C:GROUND_BEAMS:GROUND:BAND0024 ['0.450000', '0.450000'] | (a)-(d) pass: register 0.450000 vs line 0.450000 m3 |
| SLAB:GF-076 | PARTIAL | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:GSO-177-7CD-2 | NONE | no | P-C:GROUND_BEAMS:GROUND:BAND0008.1  | (c) GROUND_BEAMS:GROUND:BAND0008.1 is also named by ['GROUND_SYSTEM:GSO-177-7CD-1']: shared band, never split by guess |
| SLAB:2F | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| BEAM:BM-1F-039 | BOUNDED | no | -  | (a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids |
| GROUND_SYSTEM:through column 241 (170-7C3) | FULL | no | -  | (a) no committed register row names a concrete component of the member |
| SLAB:GF-034 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| GROUND_SYSTEM:band 7D0-FC continuous run | BOUNDED | no | -  | (a) no committed register row names a concrete component of the member |
| STAIR:ST-02:RS-C | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part ST-02:RS-C (composite or absent concrete part) |
| SLAB:1F-092 | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| SLAB:1F | NONE | no | -  | (a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line |
| STAIR:TANK:2F | NONE | no | -  | (b) 0 HL:STAIR_CONCRETE lines for part TANK:2F (composite or absent concrete part) |
| OTHER:DG5:DOME-3:SHELL:REBAR | NONE | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY:REBAR | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:HL:DOME_RING:DOME-1F-W:RING:RING_BEAM_B4_IN_BAY:REBAR | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:HL:DOME_SHELL:DOME-A:SHELL:REBAR | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:HL:DOME_SHELL:DOME-B:SHELL:REBAR | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:LIFT_PIT:WALLS:REBAR | NONE | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:LINTEL_BARS:FLAGGED | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |
| OTHER:LINTEL_BARS:PRODUCED | PARTIAL | no | -  | type outside the owner's ratio list (dome shell / ring, lintel bars) |

## Gate-B ratio table for T-664

28 rows, wiring-ready 0; total 2204.240949 .. 2909.015321 kg ESTIMATE (released detailed 9628.462205 kg unchanged, kept apart).

| member | type | concrete | m3 | kg/m3 | kg ESTIMATE | ready | blockers |
|---|---|---|---|---|---|---|---|
| FOOTING:SH10:F5:04f491 | FOOTING | RELEASED L-4d689805e55dca54f7cf | 2.016000 .. 2.016000 | 68.680658 .. 71.140741 | 142.614013 .. 150.590721 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F2:3919bf | FOOTING | RELEASED L-a244493709ce2e0d23da | 1.130500 .. 1.130500 | 68.680658 .. 71.140741 | 79.972788 .. 84.445838 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F11:109682 | FOOTING | RELEASED L-5d3e72daa69dc769ca5e | 2.625000 .. 2.625000 | 68.680658 .. 71.140741 | 185.695329 .. 196.081667 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F4:ab0b66 | FOOTING | RELEASED L-1f0b37d3309ac5bb4c07 | 1.760000 .. 1.760000 | 68.680658 .. 71.140741 | 124.504297 .. 131.468089 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F4:142c12 | FOOTING | RELEASED L-cc381dfe7b49cb758166 | 1.760000 .. 1.760000 | 68.680658 .. 71.140741 | 124.504297 .. 131.468089 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:FN:cf72aa | FOOTING | RELEASED L-f6af8a29e2c1b5fdcfd0 | 0.300000 .. 0.300000 | 68.680658 .. 71.140741 | 21.222323 .. 22.409333 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F:88b429 | FOOTING | RELEASED L-057ca0aa9960e83c2ce3 | 0.216000 .. 0.216000 | 68.680658 .. 71.140741 | 15.280073 .. 16.134720 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:FN:0e0098 | FOOTING | RELEASED L-d2c75eb10451e4dd1db5 | 0.258000 .. 0.258000 | 68.680658 .. 71.140741 | 18.251198 .. 19.272027 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F9:3192fb | FOOTING | RELEASED L-35da88665bf36b89a8fc | 5.049000 .. 5.049000 | 68.680658 .. 71.140741 | 357.171702 .. 377.149081 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F3:38c592 | FOOTING | RELEASED L-a753af083197621c2ea4 | 0.672000 .. 0.672000 | 68.680658 .. 71.140741 | 47.538004 .. 50.196907 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F3:b6c1c9 | FOOTING | RELEASED L-3403073af4f952e49df1 | 0.672000 .. 0.672000 | 68.680658 .. 71.140741 | 47.538004 .. 50.196907 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F:878832 | FOOTING | RELEASED L-5146145453fda384253d | 0.216000 .. 0.216000 | 68.680658 .. 71.140741 | 15.280073 .. 16.134720 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:FN:b61882 | FOOTING | RELEASED L-dec7d97d6a15bedee772 | 0.300000 .. 0.300000 | 68.680658 .. 71.140741 | 21.222323 .. 22.409333 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:T652:10A5 | FOOTING | HELD_BOUNDED L-164ae9d338976be9e582 | 1.960000 .. 2.275000 | 68.680658 .. 71.140741 | 138.652512 .. 169.937445 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F5:f1403e | FOOTING | RELEASED L-01830823b3fe396ad418 | 2.016000 .. 2.016000 | 68.680658 .. 71.140741 | 142.614013 .. 150.590721 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F:767bc7 | FOOTING | RELEASED L-222e42d97ea28ca69931 | 0.216000 .. 0.216000 | 68.680658 .. 71.140741 | 15.280073 .. 16.134720 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F15:932498 | FOOTING | RELEASED L-1b7eaa73e9a5e911054d | 0.720000 .. 0.720000 | 68.680658 .. 71.140741 | 50.933576 .. 53.782400 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F:0ce993 | FOOTING | RELEASED L-92617ae61830c3cdce52 | 0.216000 .. 0.216000 | 68.680658 .. 71.140741 | 15.280073 .. 16.134720 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F2:277c2f | FOOTING | RELEASED L-2bae08911f281f31553f | 1.130500 .. 1.130500 | 68.680658 .. 71.140741 | 79.972788 .. 84.445838 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| FOOTING:SH10:F6:cf553f | FOOTING | RELEASED L-bd8e800cb07a297b25d7 | 2.860000 .. 2.860000 | 68.680658 .. 71.140741 | 202.319482 .. 213.635645 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| BEAM:BM-1F-033 | BEAM | HELD_BOUNDED L-54e397fe7b1485b2e8fe, L-67f3d325019e618328eb | 0.282000 .. 0.846000 | 147.788330 .. 175.869052 | 42.926598 .. 156.224479 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| BEAM:BM-1F-029 | BEAM | RELEASED L-28396d852c7ae317a153 | 0.120000 .. 0.120000 | 147.788330 .. 175.869052 | 18.266638 .. 22.159501 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| BEAM:BM-1F-035 | BEAM | HELD_BOUNDED L-bb49e831f053bd30a6ce | 0.135000 .. 0.202500 | 147.788330 .. 175.869052 | 20.549967 .. 37.394157 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| BEAM:BM-GF-053 | BEAM | RELEASED L-18a6faa46b46d2c35db8 | 0.120000 .. 0.120000 | 147.788330 .. 175.869052 | 18.266638 .. 22.159501 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| BEAM:BM-1F-036 | BEAM | HELD_BOUNDED L-56d278bedc8dda2837a9 | 0.676000 .. 1.015000 | 147.788330 .. 175.869052 | 102.902058 .. 187.432442 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| FOOTING:SH10:FN:8f5b19 | FOOTING | RELEASED L-7d8bf3e464a8406bfcb4 | 0.300000 .. 0.300000 | 68.680658 .. 71.140741 | 21.222323 .. 22.409333 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE; (2) calibration n = 1 < 3 (WEAK) |
| BEAM:BM-1F-034 | BEAM | HELD_BOUNDED L-a9d5e7dc22013e24d691 | 0.600000 .. 1.800000 | 147.788330 .. 175.869052 | 91.333188 .. 332.392508 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
| BEAM:BM-GF-058 | BEAM | HELD_BOUNDED L-331d4bbef719a7f0bbca, L-634cefe5e8a7fb458e16 | 0.282000 .. 0.846000 | 147.788330 .. 175.869052 | 42.926598 .. 156.224479 | no | (1) range check NOT_CHECKED_NO_CITED_SOURCE |
