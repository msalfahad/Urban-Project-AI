# T-658: B10-06 column, B10-04 ground beam / strap, B10-02 footing HELD lines (research, unwired)

Candidate ARCH_TAKEOFF_V3.0.61 / trial BOQ r4 (T-654). 61 HELD m3 lines, each once in `out/T658_LEDGER.json`
(`python -I research/agents_t658/t658_alsenan.py`). Rules R-T658-1 .. 6 in `t658_rules.py`. Nothing wired, nothing
released; inputs are sha-pinned committed files plus the printed facts listed in `READS`.

| item | before (trial r4) | after (T-658 ledger) |
|---|---|---|
| STR.CONC.GROUND_BEAM (29) | 14 bounded 2.808073 .. 6.621731; 15 blank | 15 bounded 3.104473 .. 7.873294; 8 LOWER_ONLY floor 2.227973; 6 blank |
| STR.CONC.COLUMN (29) | 15 bounded 8.034 .. 10.119; 14 blank | 15 bounded 8.034 .. 10.119 (unchanged); 6 UPPER_ONLY ceiling 2.80125; 8 blank |
| STR.CONC.STRAP (2) | 0.0295 .. 0.6533 | unchanged (Q-74 checked: both are in-footing pieces) |
| STR.CONC.FOOTING (1) | 1.96 .. 2.275 | unchanged (R-T595-2) |

Ground beams. F-T658-1: 8 short spans (0.789 .. 2.1 m) carried as points at the 30x30 end while the 'less than 5m'
30x40 title also holds: 30x30 .. 30x40 (+0.347963 m3 high). F-T658-2: the 5.00 m span (ON_LIMIT, D-33): 30x40 .. 30x60
(low 0.9 -> 0.6), treated like the other D-33 spans; the Checker to rule one D-33 treatment (T-647 left two landing-beam
runs blank). F-T658-3: L-e24946df carries no bound although the T-430 register holds 0.5964 .. 0.9036. F-T658-4: 8 annex
exterior beams: literal +0.25 .. N.G. 0.00 depth is a floor (D-35: too shallow for the printed section), LOWER_ONLY.
Still blank: 3 court beams (no printed section), 1 neck-cut 0.10 m run, 2 landing-beam runs (T-647).

Columns. The 15 bounded lines are schedule vs drawn outline conflicts (D-16 / D-66); owner answer: hold as conflict,
never the schedule because it is printed: unchanged. 6 blanks with one printed section get a ceiling from the finished
mark above (2F base +9.65 to main roof +13.90; annex base +0.25 to annex roof +4.30): low stays blank (D-39 build-up,
Q-54 B). 8 stay blank: section CONFLICT with no second reading in the record (5), D-44 B15 upstand may rise above the
mark (2), planted column PC-2F (1).

Lesson proposal (ERS s.7): a held line carried as a point while a second printed title also holds is a picked end;
every held span shows the bound of all titles that hold literally (R-T658-1), and an on-limit span the two adjacent.
