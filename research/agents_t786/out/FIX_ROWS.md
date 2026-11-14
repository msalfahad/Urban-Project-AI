# T-786 fix rows on ARCH_TAKEOFF_V3.0.85: concrete UNRESOLVED residuals

Rule: UNMARKED_PIECE_DEPTH_V1 (proposed, research/agents_t786/t786_rules.py)

## Summary

```
{
 "lines_changed": 11,
 "lines_new": 0,
 "beam_m3_before": 79.243707,
 "beam_m3_after": 76.187107,
 "beam_delta_m3": -3.0566,
 "freelancer_beam_m3": 65.965875,
 "beam_vs_freelancer_before": "+13.28 m3 (+20.1 %)",
 "beam_vs_freelancer_after": "+10.22 m3 (+15.5 %)",
 "beam_unresolved_before_m3": 7.1341,
 "beam_unresolved_after_m3": 3.4779,
 "beam_rule_difference_moved_m3": 0.549624,
 "nonbeam_unresolved_m3": -5.838,
 "nonbeam_unresolved_gross_m3": 12.0116,
 "one_pct_of_his_rc_total_m3": 3.52,
 "acceptance": "every remaining UNRESOLVED m3 named with its drawing reference and designer item (beam and non-beam tables); none is replaceable by a printed schedule or section"
}
```

## Changed lines

| line | before | after | label | basis |
|---|---|---|---|---|
| L-634cefe5e8a7fb458e16 | 0.3599 | 0.0960 | DEFAULT | GF roof-edge projection band: 0.20 band north of B20, run 1 (edges 2C6 / 2C7): plan 0.5998 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0960 m3; was 0.3599 at the 0.60 beam default; cut by the section, which draws no concrete in it (owner Q-61 (5): not a beam); ST GF roof slab plan, cut A-A crosses it; SECTION A-A = B20 40 x 75 + upstand 20 x 20; D-26 replaces it |
| L-331d4bbef719a7f0bbca | 0.0630 | 0.0168 | DEFAULT | GF roof-edge projection band: 0.20 band north of B20, run 2 (edges 2C6 / 2C7): plan 0.1050 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0168 m3; was 0.0630 at the 0.60 beam default; cut by the section, which draws no concrete in it (owner Q-61 (5): not a beam); ST GF roof slab plan, same band as run 1 (cut A-A); D-26 replaces it |
| L-67f3d325019e618328eb | 0.3598 | 0.0960 | DEFAULT | 1F roof-edge projection band: 0.20 band north of B23, run 1 (edges 5E1 / 5E6): plan 0.5997 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0960 m3; was 0.3598 at the 0.60 beam default; cut by the section, which draws no concrete in it (owner Q-61 (5): not a beam); ST 1F roof slab plan, cut B-B crosses it; SECTION B-B = B23 45 x 75 + upstand 20 x 20; D-26 replaces it |
| L-54e397fe7b1485b2e8fe | 0.0629 | 0.0168 | DEFAULT | 1F roof-edge projection band: 0.20 band north of B23, run 2 (edges 5E1 / 5E6): plan 0.1048 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0168 m3; was 0.0629 at the 0.60 beam default; cut by the section, which draws no concrete in it (owner Q-61 (5): not a beam); ST 1F roof slab plan, same band as run 1 (cut B-B); D-26 replaces it |
| L-aba59a2157a48a69e2fb | 0.4920 | 0.1312 | DEFAULT | GF roof-edge projection band: 0.20 west outer band outside CB5, 4.10 m: plan 0.8200 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.1312 m3; was 0.4920 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST GF roof slab plan, west edge, continues the B20 band round its rounded corner; D-26 replaces it |
| L-a9d5e7dc22013e24d691 | 0.8999 | 0.2400 | DEFAULT | 1F roof-edge projection band: 0.20 west outer band outside CB10, 7.50 m (edges 5E7 / 5E5): plan 1.4999 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.2400 m3; was 0.8999 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 1F roof slab plan, west edge, continues the B23 band round its rounded corner; D-26 replaces it |
| L-56d278bedc8dda2837a9 | 0.9265 | 0.2471 | DEFAULT | 1F roof-edge projection band: 0.30 band outside CB12 north part, 4.28 m (edges 5DE / 629): plan 1.5441 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.2471 m3; was 0.9265 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 1F roof slab plan, east edge, rounded NE corner; D-26 replaces it |
| L-bb49e831f053bd30a6ce | 0.1619 | 0.0432 | DEFAULT | 1F roof-edge projection band: 0.30 x 0.90 SE box outside CB11 / CB12 (edges 5C1 / 619): plan 0.2698 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0432 m3; was 0.1619 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 1F roof slab plan, SE corner, rounded; D-26 replaces it |
| L-377cb988b2271c2e2e4d | 0.3414 | 0.0910 | DEFAULT | 1F roof-edge projection band: 0.10 band outside CB12 south part, 5.69 m: plan 0.5690 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0910 m3; was 0.3414 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 1F roof slab plan, east edge; D-26 replaces it |
| L-fbb65dfd2a66a16714ac | 0.2400 | 0.0640 | DEFAULT | 1F roof-edge projection band: 0.40 x 1.00 rounded box outside CB12 at the east column: plan 0.4000 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0640 m3; was 0.2400 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 1F roof slab plan, east edge, rounded; D-26 replaces it |
| L-17c4238c0ef76656d06e | 0.2610 | 0.0696 | DEFAULT | 2F roof-edge projection band: 0.10 edge band 4.35 m: plan 0.4350 m2 (T-721 DXF) x 0.16 printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast with the slab; UNMARKED_PIECE_DEPTH_V1) = 0.0696 m3; was 0.2610 at the 0.60 beam default; same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the roof edge, rounded facade corners): same element, not a beam; ST 2F roof slab plan, roof edge; D-26 replaces it |

## Beam UNRESOLVED after this set (named)

| line | m3 | label | designer | reference |
|---|---|---|---|---|
| L-56c49c3c2596a0869533 | +0.0960 | DEFAULT | D-05 | 1F strip at the column at B23's end (0.16 m2, T-724 census; not the outside projection band): beam piece, company 0.60 kept |
| L-f113ed57f7875fed9a67 | +0.0960 | DEFAULT | D-05 | GF strip at the column at B20's end (0.16 m2, T-724 census; not the outside projection band): beam piece, company 0.60 kept |
| L-7c3edce23ec8faa3d674 | +0.1120 | DEFAULT | D-04 | 2F span past a column, adjacent span B1 20 x 40 (ladder step 2) |
| L-dc8cbfc119d006ff3927 | +0.1120 | DEFAULT | D-04 | 2F span past a column, adjacent span B1 20 x 40 (ladder step 2) |
| L-8d031491396379f0cbb1 | +0.1695 | DEFAULT | D-04 | 2F perimeter piece, adjacent span B8 20 x 75 (ladder step 2) |
| L-d62d2fcf3d0023ad1ad1 | +0.7440 | DEFAULT | D-04 | 2F span past a column, adjacent span B15 20 x 120 (ladder step 2; B15 stand D-44) |
| L-f83c4a469845c7e14dfa | +0.0640 | DEFAULT | D-04 | 1F span past a column, adjacent span B2 20 x 40 (ladder step 2) |
| L-88ccf8d4505411deb9e5 | +0.3975 | DEFAULT | D-03 | GF CB3 / 'B3 (with stair)' one beam counted once at CB3 20 x 75 both sides |
| L-ab37afa17f2ac5b0efd1 | +0.8996 | DEFAULT | D-28 | east dome ring at the twin west ring B4 depth 0.50 (same ST p.7 dome detail) |
| L-634cefe5e8a7fb458e16 | +0.0960 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-331d4bbef719a7f0bbca | +0.0168 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-67f3d325019e618328eb | +0.0960 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-54e397fe7b1485b2e8fe | +0.0168 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-aba59a2157a48a69e2fb | +0.1312 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-a9d5e7dc22013e24d691 | +0.2400 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-56d278bedc8dda2837a9 | +0.2471 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-bb49e831f053bd30a6ce | +0.0432 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-377cb988b2271c2e2e4d | +0.0910 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-fbb65dfd2a66a16714ac | +0.0640 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| L-17c4238c0ef76656d06e | +0.0696 | DEFAULT | D-26 | projection band at the printed slab thickness: his beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not readable from his rows |
| T-777 C2a | -0.3244 | MEASURED / DRAWING-READ | D-27 / D-02 | drawn width vs his schedule width: GF B21 / B29 / CB2, 1F B6 / CB10 (ST GF and 1F roof slab plans vs schedule) |

## Moved to RULE_DIFFERENCE

- L-8ea71184fff91b4357b7 0.5496: GF BM-GF-059 B24 past its support 1.501 x 0.50 x 0.75 (measured 0.5496): his B24 row 5.75 m = engine B24 3.55 + this 1.50 + 0.70; the same concrete on his B24 line

## Non-beam UNRESOLVED (T-778 causes, named)

| family | cause | m3 | reference |
|---|---|---|---|
| STR.CONC.NECK | N-4 HEIGHT default / low-bound lines | +0.8151 | ST p.9 n.1 founding; lift raft level D-43 |
| STR.CONC.COLUMN | C-1 COUNT engine-only mark | +0.5040 | ST p.9 schedule CGT 1ST C6; D-66 |
| STR.CONC.COLUMN | C-2 COUNT 1F | +0.4140 | ST 1F column plan mark assignment C3 / C6 / C7 / C8 / C9; D-66 / T-566 |
| STR.CONC.COLUMN | C-3 SECTION (drawn / CONFLICT reading vs his row) | -0.4695 | C8 10E0 drawn 0.25 x 0.80 vs schedule; D-66 / T-566 |
| STR.CONC.COLUMN | C-5 STOREY_BASE 2F | -0.1675 | 2F roof section not printed; roof build-up DEFAULT 0.175 |
| STR.CONC.GROUND_BEAM (building) | G-1 SECTION DEFAULT interior p.13 class D 0.30 | -2.5553 | ST p.13 typical GB sections by clear span; D-33 loaded spans, D-34 length basis, D-35 exterior depth 'FOLLOW ARCH.' |
| STR.CONC.GROUND_BEAM (building) | G-1 SECTION DEFAULT interior p.13 class D 0.40 | -1.0962 | ST p.13 typical GB sections by clear span; D-33 loaded spans, D-34 length basis, D-35 exterior depth 'FOLLOW ARCH.' |
| STR.CONC.GROUND_BEAM (building) | G-1 SECTION DEFAULT interior p.13 class D 0.41 | -0.0440 | ST p.13 typical GB sections by clear span; D-33 loaded spans, D-34 length basis, D-35 exterior depth 'FOLLOW ARCH.' |
| STR.CONC.GROUND_BEAM (building) | G-2 LENGTH his lump 211 m vs the engine's bound runs face to face | -3.4841 | his two lumps 100 + 111 m vs the engine's bound runs (T-391 envelope 193.76 .. 231.91 m) |
| STR.CONC.GROUND_BEAM (building) | G-3 unbound piece (no footprint in the band ledger) | +0.1037 | BAND0009 no T-170 footprint |
| STR.CONC.GROUND_SLAB | GS-3 engine faces vs own panels (T-391 F3 small reads) | -0.0823 | T-391 F3 small reads |
| STR.CONC.STAIR | ST-10 ST-01 turn pieces (winders, flat turn, turn riser) DEFAULT | +0.4134 | ST-01 turn pieces; T-711 DEFAULT |
| STR.CONC.STAIR | ST-6 ST-02 curved part: his flat 1.2 x 0.28 vs wedges + helicoid waist (ESTIMATE) | -1.0259 | ST-02 curved stair no section; D-08 |
| STR.CONC.STAIR | ST-8 ST-03 his 0.28 flat vs steps + 0.16 waist on the slope (ESTIMATE) | +0.1866 | ST-03 no waist printed; S-9 / D-56 |
| STR.CONC.LIFT | L-2 GF tie beam (ST p.8 n.19) not in his sheet | +0.6500 | ST p.8 n.19 tie beam size not printed; D-43 |

Ignored small: GF-NW-CORNER / 1F-NW-CORNER (0.0293 m2 each) stay EXCLUDED: at 0.16 they are 0.0047 m3 each, still < 0.05
