# C. Unlock matrix (INTERNAL, never sent): which A questions together close each whole BOQ line

Lead 2026-10-30. Line = the Checker's CLOSABLE LINES reference line (SCOREBOARD.md). "Closes" means the Checker names no
other blocker for the line except the listed questions and the internal work named. An answer moves a quantity only
through a task and a Checker verdict; nothing is released by an answer alone.

| Group | Line (unit) | Questions that must all be answered | Internal work still needed after the answers | Held / conflicting now |
|---|---|---|---|---|
| P-1 | Windows, aluminium (m2, pcs) | RFI-A01 | none named (Q-76 answered) | W02 1 .. 2 pcs, m2 HELD |
| P-2 | CONC.POOL (m3) | RFI-A02 | none named | access element HELD |
| P-3 | CONC.FOOTING (m3) | RFI-S02, S03, S04, S05 | integration of the answers (lane I) | F10+F 2.176 .. 2.275; SB3 0.0295 .. 0.2683; SB1 0 .. 0.385; boundary pads UNMEASURED |
| P-4 | CONC.BLINDING (m3) | RFI-S01, S02, S03, S04, S06, S07, S08 | as P-3 (shares S02 / S03 / S04) | D-14 0 .. 0.189; D-15 0 .. 0.913; F10+F 0.552 .. 0.590; FF >= 2.070; boundary-pad blinding UNMEASURED |
| P-5 | CONC.GROUND (m3) | RFI-S03, S04, S09, S10, S11 | none named | 24 exterior beams HELD (11.930 unsupported basis), 15 loaded spans, 5.00 m span |
| P-6 | CONC.BEAM (m3) | RFI-S12 .. S18 | none named | 7 runs CONFLICT 5.4421 / 5.7665; HELD 3.228 .. 7.6685 + 5 runs |
| P-7 | CONC.COLUMN (m3, necks incl.) | RFI-S01, S19, S20, S21, S22, S23 | neck depth on the lift columns also needs the lift-pit depth (lift supplier) | CONFLICT 15 = 8.034 .. 10.119; HELD 16; necks >= 9.2568 |
| P-8 | CONC.STAIR_DOME (m3) | RFI-S24 .. S28, A03, A04, A05 | stair system re-verification by the Checker | ST-03 0.948 unsupported; round stair 2.089 unresolved; dome / drums no value |
| P-9 | Floor area, internal (m2) | RFI-A06, A07 | the G4 +1.100 m2 is already settled (T-286), integration pending | under-stair 6.124; garden band 1.364; (A08 moved: area 2.970 m2 is in the floor scope with its area VERIFIED since V3.0.14; only the finish is open) |

Lines with NO priority group (no RFI set closes them alone): reinforcement (laps, T-273), blockwork (T-279 integration and
held walls), plaster / paint (T-313 / T-314 / T-326, roof datum, supplier door heads), ceilings, soffits, external sills.
Their designer questions go in B_REMAINING_RFI.md (next Lead run).
| P-9b | Floor finishes (m2, by finish) | RFI-A08 (use and floor finish of the unlabelled 1F space) | none named | finish material of 2.970 m2 HELD; area not held |

OWNER 2026-10-31: A08 re-filed from the floor-AREA group to the floor-FINISH group (no engine geometry change); main chat.
