# T-739: all-trade aggregation statement on ARCH_TAKEOFF_V3.0.74 (lane I, research; r2)

Worker 3, 2026-11-12. Research only, backlog-permitted: no candidate, rule, registry or released file changes; nothing
released (V3.0.74 NOT RELEASED; V2.9 + route G untouched). No drawing, workbook, client name or coordinate here.

Build: `python3 -I research/agents_t739/t739_alsenan.py --write | --check` (`--pin` rewrites the cause-source pin,
run of record only); tests `tests/t739_aggregation` (30). Output: `out/T739_AGGREGATION.md` (tables) and
`out/T739_AGGREGATION.json` (every line id per state, every HELD line with its cause, the hand re-add cells).

## r2 (Verifier REJECTED r1 2026-11-12T11:58Z: committed output != rebuild on the merged head)

- Root cause: r1 read the per-line cause records with a live glob over `research/agents_t6xx..t9xx/out/*.json`, so any
  later merge (T-717: 'T-676' 46 -> 49 winning records) changed the rebuild. Fix (general): the cause sources are now a
  committed sha-pinned list, `CAUSE_SOURCES_PIN.json` (104 files, written by `--pin` in the run of record); a pinned
  file that changes refuses the build; a file merged later is not read until a new run of record re-pins it.
- Restated on V3.0.74 ONLY (index `research/agents_t717/out/LINE_INDEX_V3_0_74.json`, lines sha bea5be02, master
  1.75.0); V3.0.73 is read only as the chain base, never mixed into a sum.
- The 32 lines T-717 ADDED (30 return-paint, 2 double-height band) had no line-id cause record anywhere (they did not
  exist before V3.0.74): bound to their committed T-709 records by element id through the T-717 row (`package_causes`):
  22 'frame-covered depth not printed', 5 'NOT_ESTABLISHED (wet rooms both sides)', 3 BLOCKED_RFI 'plaster return
  blank', 2 band status texts. Read, never invented; an unbound row stays F-T739-1.

## Method (R-T739-1, every villa; `t739_rules.py`, unchanged)

Physical element first: a BOQ line of the index is one element x one item code x one unit; its state is RELEASED,
BOUNDED, AT_LEAST, AT_MOST, BLANK or EXCLUDED, decided from the index fields alone, refused when contradictory.
Subtotals per trade (BOQ_FAMILY_MASTER 1.75.0 group) x unit x state only, in Decimal, re-added twice; a trade x unit
with any HELD line prints no single total. Register codes (ARCH.WALL_PANEL / VOLUME / RUN, ARCH.EXTERIOR) apart.

## Results on V3.0.74 (engineering terms)

- 5,155 lines = 1,515 RELEASED + 1,192 BOUNDED + 1,605 BLANK + 843 EXCLUDED (V3.0.73 + 29 BOUNDED + 3 BLANK added).
- Chain re-add: V3.0.73 + the 36 T-717 package rows (4 replaced, 32 added; before / after checked on all 36) =
  V3.0.74; 5,119 other lines byte-equal.
- B4 Walls m2 (plaster / paint): released 1,353.360803 (144) + bounded 1,711.938656 .. 2,012.175238 (73) + 27 BLANK:
  NO single total. FIN.PLASTER / FIN.PAINT counts and sums equal the T-717 census after exactly (plaster released
  388.58436, bounded 1,106.948597 .. 1,302.168817 (35); paint released 217.2081, bounded 604.990059 .. 710.006421 (38),
  3 BLANK).
- Every other trade unchanged from r1 (T-717 moved FIN.PLASTER / FIN.PAINT only): B10 concrete m3 released
  285.091370 (295) + bounded 43.219151 .. 67.784279 (91) + 49 BLANK; B8 WP m2 711.350096 (60) + 0 .. 2.458981 (12) +
  14 BLANK; B7 stairs lm 101.169174 (10) + 0 .. 29.8964 (3) + 65 BLANK. The Verifier's 4 r1 hand cells are reusable.
- Freelancer keyed (diagnostic, not accuracy): the 10 non-paint numeric SCOREBOARD v2 cells reproduce unchanged;
  paint key now 'at least -30.97 %, upper end open' (was -31.25 .. -24.48 %: the 3 BLANK return-paint lines open the
  upper end); plaster like for like -16.76 .. -8.68 % with his 13.50 m2 row apart, -17.72 .. -9.74 % vs his gross
  (T-717, quoted).
- Every HELD line (2,797) carries a committed cause; F-T739-1 = 0.
- 39 of 104 families have no line (master 1.75.0), unchanged.

## Findings

- F-T739-1: HELD lines with no committed cause: 0.
- F-T739-2 (kept): STR.CONC.GROUND_BEAM L-fb7a6431 is 0 .. 3.5256 m3 in the index; the ruled form (HELD BLANK,
  AT_MOST cap beside) is printed beside, carried by the T-729 package (concrete round 10), not applied here.
- F-T739-3 (kept): the T-662 per-line 'cause' field is the rebar ratio route, not a hold reason; not used.
- F-T739-4 (new): the T-717 package rows carry no hold-cause field for ADD rows; a lane I package that ADDS held
  lines should write the cause text on the row (the T-709 record is only reachable by element id).
- Component layer: only the T-717 / T-722 rows carry a committed per-line record equal to the V3.0.74 state (69
  lines); every other line's gross / deductions / additions live only in the private V3_0_74_BOQ_LINES (bea5be02).

Proposed lessons-register row: "A committed statement reads a pinned, sha-checked set of inputs, never a live glob of
the tree; a line added by a package carries its hold cause on the package row."
