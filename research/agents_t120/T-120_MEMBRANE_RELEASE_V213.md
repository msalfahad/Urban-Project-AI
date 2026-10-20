# T-120 ARCH_TAKEOFF_V2.13: membrane purchase release (owner Q-58 A proven by the plan; typed wet-zone size)

Worker 3, 2026-10-20. Opt-in method version, NOT the released default (owner 2026-10-20 12:15). Code:
`engine/source/arch_v213.py` (new), `tools/urban_boq_m9.py` (V2.13 wiring, own files `MEMBRANE_TABLE_V2_13.json`,
`MEMBRANE_PURCHASE_V2_13.csv`), tests `tests/t120_membrane_release_v213` (33), `tests/t034` method-order pin extended.
V2.12, MEMBRANE_FOLD_V3, MEMBRANE_CUTTING_PLAN_V2 and every frozen file untouched; registry 1.7.0, no new rule record.

## 1. What V2.13 releases, and only when

| Case | V2.12 | V2.13 |
|---|---|---|
| Area whose fewest rolls are the same under Q-58 A / B / C | RELEASED | identical (same dict, same line) |
| Area held on Q-58 (counts differ) and a layout with the fewest A rolls has a PROVEN physical plan | HELD, bounded low / high | RELEASED at the A count, SOURCE_DERIVED, with the proof, its cutting plan, the B plan and the B / C counts beside it (same line id) |
| Same, no layout proven | HELD, bounded | HELD, bounded, the failures named in the reason |
| Open-plan wet zone (wet + dry label in one face) with ONE usable typed printed size | FIN.WP.FLOOR and rolls BLOCKED_RFI | FIN.WP.FLOOR = printed L x W (OWNER_FACT basis, TYPED), its own rolls line, FIN.WP.WALL_UPTURN HELD unless the wall / door / open runs are typed |
| Zone with no / HELD / ASSUMED / other-project / ambiguous / non-positive record | held | held as V2.12 (reason logged in `typed_wet_zones`) |

The proof (owner directive Q-58 A conditional: width, length, overlap, upturn geometry, seam arrangement; "area alone is
no proof"), per layout: coverage residual 0 (V3 check: floor + 0.20 m mitred upturn, opening upturn); every main strip
piece and every piece cut from a roll re-packed into whole 1.00 x 10.00 m rolls and the count equal to the fold's; every
piece at most one roll long and wide; every own-offcut piece (need width = extent + 0.10 m lap per joining side, length
incl. end laps, as V3 computes it) placed at a stated position inside a real offcut of the FINAL rolls (full-width roll
end, or the side trim beside a narrower piece on the same roll), an offcut split once used, never reused; no two pieces
overlap and nothing lies outside its roll (checked on the rectangles with shapely, not on bookkeeping). Corner detail
pieces, the upturn's top termination and the factory lap edge are UNRESOLVED_BY_SYSTEM (MEM-URBAN-DEFAULT-1x10 has
corner_treatment null): listed, the same under every reading, not a reason to hold. No start offset (T-114's 0.05 m is a
recommendation, no Urban rule) and no new tolerance.

## 2. Hand fixtures (none is the development villa)

| Fixture | Hand count | V2.12 | V2.13 |
|---|---|---|---|
| R: roof 10.00 x 6.00 less a 7.50 x 3.15 notch; strips across, 12 strips (last 0.50 m), mains 3 x 6.40 + 9 x 3.25 = 48.45 m; step upturn 0.10 x 3.15 = 0.315 m2 uncovered -> upturn-only strip 3.25 m, need width 0.20 | A 5 (piece in the 0.50 x 3.25 trim of strip 12, roll 5; trim left 0.30 x 3.25), B 6 (51.70 m), C 6 | HELD 5 / 6 | RELEASED 5, proven; leftover 1.55 m (0.35 x 3 + 0.25 x 2); mirrored, 90 deg, mm identical |
| H (T-096): 9.00 x 4.60 less 2.00 x 2.00 | A 5 (0.20 x 2.10 in the 0.60 x 3.00 trim, roll 5 used 9.00 m), B 6, C 6 | HELD 5 / 6 | RELEASED 5 |
| X: 11.00 x 5.50 less 1.00 x 3.00, layout along / lower | mains 76.50 m in 8 rolls leave 3.50 m of roll end + a 0.50 m trim; four 1.00 x 1.00 patch pieces need 4.00 m: 8 impossible | (area released at 8 on another layout) | proof REFUSES this layout's V3 A count 8 (OFFCUT failure); area unchanged |
| H with its A piece made 0.20 x 3.50 (longer than every offcut) | not provable | HELD 5 / 6 | HELD 5 / 6, failure named, bounded line, never 0 |
| 10.00 x 6.00 less 1.00 x 4.45 | A 8 = B 8, C 7 (corner pieces ready-made) | HELD 7 / 8 | RELEASED 8 (owner chose A), C 7 shown |
| Kitchen 3 x 4, roof 12 x 5, notch 12 x 4.6 (released) | as V2.12 | RELEASED | identical dict |
| Zone 2.00 x 1.60 typed | 3.20 m2; across 3 strips (1.00, 1.00, 0.60) x 2.00 = 6.00 m, 1 roll, 4.00 m left | held | floor 3.20 released, 1 roll, upturn held; with typed runs walls 3.60 m -> 0.72 m2; its two un-listed doorways -> one held transition line |
| Zone 4.50 x 3.00 (the printed pantry size of Q-37) | 13.50 m2; 4 strips x 4.90 = 19.60 m, 2 rolls, 0.40 m left, trim 1.47 m2; across 6 x 3.40 = 20.40 m, 3 rolls | held | 2 rolls = T-114 hand plan exactly |

End to end (synthetic villa DXF, dining + pantry face; as drawn, mirrored, quarter turn, metres): V2.13 with the typed
record changes exactly 2 lines of V2.12 (pantry FIN.WP.FLOOR held -> 3.20 m2, rolls held -> 1, same line ids) and adds
1 held FIN.WP.WALL_UPTURN; wet total rolls +1 and complete; every line once. Without the record V2.13 = V2.12 line for
line; on the T-079 drawn roof (released under every reading) identical.

## 3. Finding: MEMBRANE_FOLD_V3's Q-58 A count can use one leftover twice

`membrane_fold_v3.counts` places the pieces taken from offcuts into the leftovers of the main strips' packing alone, then
packs the pieces that did not fit together with the main strips into new bins: the second packing may fill the very
leftover the first step promised away. Fixture X shows a V3 A count of 8 that no plan can reach (4.00 m needed, 3.50 m
left). V2.12 only shows A as one end of a held range, so no released quantity was wrong; V2.13 never releases an A count
without its own placement on the final rolls. Not fixed in V3 (released by V2.12: never edited); a later fold version
can count A on the final packing.

## 4. Development villa (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip): NOT RUN in this session

The decoding of the downloaded Drive zip was refused by the session permission check ("[Untrusted Code Integration]"),
so the engine was not run on the villa. Expected from the hand plans (T-114, verifier-checked): 2F roof 17 rolls under
Q-58 A (P0-A: strips stop at the opening edge, 0.30 x 4.60 step band from the 0.70 x 6.97 trim, 16 flap pieces from the
roof's own 3.03 m roll ends), 18 under B; pantry 4.50 x 3.00 = 2 rolls; wet areas 19 -> 21; 1F roofs 8 + 6 unchanged.
Whether V2.13 releases 17 depends on whether the engine's own A layout (V3: 8 opening patches 0.063 m2, its own cut
rule, 162.69 m) passes the placement proof on its final rolls; if it does not, the line stays HELD 17 / 18 with the
failure named (section 3 shows why that can happen). Verifier command:

    python3 -I research/agents_t120/alsenan_v213_run.py <P7757.dxf> --out <scratch>/t120.json \
        --zone-floor GF --zone-code PANTRY --zone-length 4.50 --zone-width 3.00 --zone-sheet "ground floor plan"

Accept on the villa: 2F roof RELEASED 17 with `proof_q58_a.proven` (or HELD with the failure), pantry 2 rolls and floor
13.50 m2, wet total 21 rolls, every other line of V2.12 (578) unchanged except the pantry's 2 lines and its added held
upturn line. Freelancer: roof membrane 285.00 m2 / 194.00 lm, wet floor 72.01 m2, no roll count and no pantry line:
rolls not comparable; the pantry adds 13.50 m2 of wet floor (72.12 -> 85.62 m2 engine with the pantry, +18.9 % over the
freelancer's 72.01 m2, RULE_DIFFERENCE: owner Q-37 A waterproofs the pantry, the freelancer does not).
