# 12 Quotation status

**Verdict: NOT quotation-ready.** It stays so until two pieces of evidence exist. M8 adds neither.

1. **Engineer-released quantities.** A structural engineer, or a QS who signs, confirms the measured items and closes
   the bounded findings by RFI.
2. **A blind second project.** A villa the developer has never seen is run through a frozen engine, and its result
   is compared afterwards with an independent takeoff.

## What M8 changes for a quotation

**Every structural family on a drawing ends in one of two states.**

| State | What it means |
|---|---|
| measured | PROVISIONAL, from drawn geometry. Every dimension the drawing does not print is a named convention with its range |
| bounded | a stated range that a reviewer can close |

M7 left most of the scope volume-less: 85 of the 90 ST7757 findings carried no volume. Under V6, 0 findings are
without a range, on ST7757 and on all 80 held-out villas.

**The BOQ now prints a bounded total** (section F). Its parts are:
- the measured total;
- every unresolved item's exposure;
- every finding's range.

On the 80 held-out villas the whole RC design truth fell inside that bounded total every time. On ST7757 the range
is wide: from 313 to 476 m³ around 320 m³ measured. Its largest contributors (`st7757/SCOPE_BOUNDS.csv`) are the
RFIs a QS would raise first:
- parapets;
- unresolved beams;
- a footing of unknown depth;
- the roof tank;
- column bands with no outline.

**How it would be used: as a planning estimate with a stated range, not as a price.**

| Line type | How to read it |
|---|---|
| A measured line | priced as provisional |
| A bounded line | carried as an allowance |
| Reinforcement of the new families (stairs, pool, domes, tank, pit, boundary wall) | MISSING_DATA. It must be measured from the bar details; it is never estimated by a ratio |

## What still blocks it on ST7757

**Pool: the measurement covers part of the pool only.**
- Only the wall strip drawn on the ground-beam plan is read.
- The pool section on the detail sheet is not read.
- The stage record and the freelance QS both lie outside V6's range (W8-01).

**Core families: unchanged by M8.**
- The ground slab and the ground beams stay well below the external positions.
- The causes are the open items of the M5 bridge (W8-10).

**Unsettled families: bounded, not measured.**
- Lift, water tank and parapets are ranges only (W8-07, W8-08).

**Reinforcement:** missing for the new families (W8-09).

## Wording to use

> "M8 planning estimate: RC measured X m³, bounded range L – H m³, N findings with an open RFI. Not a released
> quantity; reinforcement of stairs, pool, domes, tank, pit and boundary wall not measured."

Never write "quotation-ready", "verified" or "final" for an M8 figure.
