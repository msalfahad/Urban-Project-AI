# T-739: all-trade aggregation statement on ARCH_TAKEOFF_V3.0.73 (lane I, research)

Worker 3, 2026-11-12. Research only, backlog-permitted: no candidate, rule, registry or released file changes; nothing
released (V3.0.73 NOT RELEASED; V2.9 + route G untouched). No drawing, workbook, client name or coordinate here.

Build: `python3 -I research/agents_t739/t739_alsenan.py --write | --check`; tests `tests/t739_aggregation` (25).
Output: `out/T739_AGGREGATION.md` (tables) and `out/T739_AGGREGATION.json` (every line id per state, every HELD line
with its cause, the hand re-add cells).

## Method (R-T739-1, every villa; `t739_rules.py`)

Physical element first: a BOQ line of the index is one element x one item code x one unit; its state is RELEASED,
BOUNDED, AT_LEAST, AT_MOST, BLANK or EXCLUDED, decided from the index fields alone, refused when contradictory.
Subtotals per trade (BOQ_FAMILY_MASTER 1.74.0 group) x unit x state only, in Decimal, re-added twice; a trade x unit
with any HELD line prints no single total. Register codes (ARCH.WALL_PANEL / VOLUME / RUN, ARCH.EXTERIOR) apart.

## Results (engineering terms)

- 5,123 lines = 1,515 RELEASED + 1,163 BOUNDED + 1,602 BLANK + 843 EXCLUDED; AT_LEAST / AT_MOST in the index: 0
  (the T-722 concrete AT_LEAST figures, 17.4 m3 over 27 lines, exist only beside in the run record, and the T-714
  formwork AT_LEAST rows are unwired until T-729: both printed beside, never in a state sum).
- Every trade x unit carries HELD lines except B6 Openings lm and the register lm, so the candidate has NO single total
  in any payable trade; e.g. B10 concrete m3 released 285.091370 + bounded 43.219151 .. 67.784279 (91) + 49 BLANK.
- Chain re-add: V3.0.72 + the 33 T-722 package rows = V3.0.73 (5 rows move an index field, 28 are beside / named);
  5,090 other lines byte-equal.
- Keyed freelancer ranges recomputed here reproduce all 11 numeric SCOREBOARD v2 cells (CONC.* x 8, paint, aluminium
  doors, windows); plaster is quoted like for like only (-14.83 .. -8.82 %, his 13.50 m2 row apart, T-726).
- Every HELD line (2,765) carries a committed cause: the latest detailed record (T-654 .. T-732), else the T-716
  cause class; the T-716 class is printed beside every line.
- 39 of 104 families have no line: the 38 of T-692 minus B7-01 (now lined) plus B7-14 / B11-03 (outside the T-692
  primary set).

## Findings

- F-T739-1: HELD lines with no committed cause: 0 (34 are caused only by the T-716 class bucket, no detailed text).
- F-T739-2: STR.CONC.GROUND_BEAM: the T-722 printed census counts L-fb7a6431 (index 0 .. 3.5256 m3, the T-724 cap) as
  blank while the index carries both bounds; the index reading (bounded 1.178378 .. 5.096771 on 9 lines + 20 BLANK)
  equals SCOREBOARD v2; a 0 low on a HELD line is a cap, not a measured lower end (proposal: the census convention
  should say which).
- F-T739-3: the T-662 per-line 'cause' field is the rebar ratio route, not a hold reason; it is not used as a cause.
- Component layer: only the T-722 rows carry a committed per-line component record; every other line's gross /
  deductions / additions live only in the private V3_0_73_BOQ_LINES (c5a0b128) and are NOT re-added here.

Proposed lessons-register row: "A statement total is a sum per (trade, unit, state); a cause field is checked for what
it states before it is used (T-662 route note), and a 0 low is a cap, not a measured lower end."
