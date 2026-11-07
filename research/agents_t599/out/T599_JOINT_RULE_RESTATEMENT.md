# T-599 column-beam joint rule: T-590 rows restated (generated)

Rule UP-CONC-JOINT-001@1.0.0 (rules/conventions/URBAN_CONVENTIONS_1.0.0.json, LEAD_ADOPTED under Q-62 A); RULES_INDEX: {'version': '1.0.0', 'status': 'LEAD_ADOPTED', 'library': 'rules/conventions/URBAN_CONVENTIONS_1.0.0.json'}. Input: research/agents_t590/out/T590_RULE_DIFF_PROVENANCE.json (T-590 MERGED 7855b9b2): its 38 m3 rows.

m3 rows 38: 37 joint rows UNRESOLVED -> RULE_DIFFERENCE SOURCED; apart (stays UNRESOLVED): T-545/beams@V7 row 7 0.120452 m3.

| | before (T-590) | after (T-599) |
|---|---|---|
| headline | {"UNRESOLVED": {"n": 6, "signed": "2.369278", "gross": "7.701778"}} | {"RULE_DIFFERENCE": {"n": 5, "signed": "2.248826", "gross": "7.581326"}, "UNRESOLVED": {"n": 1, "signed": "0.120452", "gross": "0.120452"}} |
| all rows (nested / superseded audited beside) | {"UNRESOLVED": {"n": 38, "signed": "-0.148146", "gross": "20.049354"}} | {"RULE_DIFFERENCE": {"n": 37, "signed": "-0.268598", "gross": "19.928902"}, "UNRESOLVED": {"n": 1, "signed": "0.120452", "gross": "0.120452"}} |

Headline signed 2.369278 m3 / gross 7.701778 m3 unchanged.

Headline by cause (m3): {"RULE_DIFFERENCE_SOURCED_matched_joint": {"signed": "0", "gross": "5.33250"}, "UNRESOLVED_pair_residual_T600": {"signed": "2.248826", "gross": "2.248826"}, "UNRESOLVED_untraced_apart": {"signed": "0.120452"}, "check_signed_total": "2.369278"}.

## Column / beam pair, V7 reading (m3, reference - engine)

| storey | beam THROUGH_SUPPORT | column JOINT_HEAD | net (residual, T-600) |
|---|---|---|---|
| 1F | 1.593362 | -0.385 | 1.208362 |
| 2F | 0.42 | 0 | 0.42 |
| GF | 2.901714 | -2.28125 | 0.620464 |

F-C-T590-1 restated on the V7 reading (T-545@V7 headline rows + T-551 column rows; sign reference - engine as in the statement): the per-storey pair does not cancel; the net is not a convention and stays its own residual (T-600). T-590's note quoted the pre-V7 2F beam -0.532760 and printed the GF / 1F nets with the opposite sign (-0.620464 / -1.208362): with the statement sign the reference carries MORE concrete in the pair (beam through-support > column joint head) on every storey

## Rows

| section | row | name | m3 | headline | outcome |
|---|---|---|---|---|---|
| T-545/beams | 2 | GF: THROUGH_SUPPORT | 2.901714 | False | SOURCED |
| T-545/beams | 11 | 1F: THROUGH_SUPPORT | 1.593362 | False | SOURCED |
| T-545/beams | 19 | 2F: THROUGH_SUPPORT | 0.42 | False | SOURCED |
| T-551/columns | 6 | columns GF: JOINT_HEAD | -2.28125 | True | SOURCED |
| T-551/columns | 15 | columns 1F: JOINT_HEAD | -0.385 | True | SOURCED |
| T-572/measured-columns_GF | 1 | columns_GF: JOINT_HEAD | -1.883750 | False | SOURCED |
| T-572/measured-columns_1F | 0 | columns_1F: JOINT_HEAD | -0.385000 | False | SOURCED |
| T-576/columns-GF | 1 | GF C1: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-GF | 2 | GF C10: JOINT_HEAD | -0.148750 | False | SOURCED |
| T-576/columns-GF | 5 | GF C11: JOINT_HEAD | -0.467500 | False | SOURCED |
| T-576/columns-GF | 8 | GF C2: JOINT_HEAD | -0.205000 | False | SOURCED |
| T-576/columns-GF | 10 | GF C4: JOINT_HEAD | -0.187500 | False | SOURCED |
| T-576/columns-GF | 11 | GF C5: JOINT_HEAD | -0.337500 | False | SOURCED |
| T-576/columns-GF | 13 | GF C6: JOINT_HEAD | -0.087500 | False | SOURCED |
| T-576/columns-GF | 15 | GF C7: JOINT_HEAD | -0.150000 | False | SOURCED |
| T-576/columns-GF | 18 | GF C9: JOINT_HEAD | -0.375000 | False | SOURCED |
| T-576/columns-1F | 0 | 1F C1: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-1F | 1 | 1F C2: JOINT_HEAD | -0.205000 | False | SOURCED |
| T-576/columns-1F | 3 | 1F P.C 20x50: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-1F | 5 | 1F P.C 20x70: JOINT_HEAD | -0.105000 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 1 | GF C1: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 2 | GF C10: JOINT_HEAD | -0.148750 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 5 | GF C11: JOINT_HEAD | -0.467500 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 8 | GF C2: JOINT_HEAD | -0.205000 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 10 | GF C4: JOINT_HEAD | -0.187500 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 11 | GF C5: JOINT_HEAD | -0.337500 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 13 | GF C6: JOINT_HEAD | -0.087500 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 16 | GF C8: JOINT_HEAD | -0.191250 | False | SOURCED |
| T-576/columns-GF-reading-10E0-C7 | 19 | GF C9: JOINT_HEAD | -0.375000 | False | SOURCED |
| T-576/columns-1F-reading-10E0-C7 | 0 | 1F C1: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-1F-reading-10E0-C7 | 1 | 1F C2: JOINT_HEAD | -0.205000 | False | SOURCED |
| T-576/columns-1F-reading-10E0-C7 | 3 | 1F C8: JOINT_HEAD | -0.135000 | False | SOURCED |
| T-576/columns-1F-reading-10E0-C7 | 5 | 1F P.C 20x50: JOINT_HEAD | -0.075000 | False | SOURCED |
| T-576/columns-1F-reading-10E0-C7 | 7 | 1F P.C 20x70: JOINT_HEAD | -0.105000 | False | SOURCED |
| T-545/beams@V7 | 2 | GF: THROUGH_SUPPORT | 2.901714 | True | SOURCED |
| T-545/beams@V7 | 7 | GF: UNTRACED -> GF B7 UNRESOLVED | 0.120452 | True | UNRESOLVED_APART |
| T-545/beams@V7 | 11 | 1F: THROUGH_SUPPORT | 1.593362 | True | SOURCED |
| T-545/beams@V7 | 19 | 2F: THROUGH_SUPPORT | 0.42 | True | SOURCED |
