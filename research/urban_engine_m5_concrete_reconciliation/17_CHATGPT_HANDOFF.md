# Notes for ChatGPT: what worked, what is not working, what to do next (M5)

## What worked

**Reproducing the four sources from their records.** The freelancer total comes from the 149 traced leaf rows; U-C4N and christiannp from their categories; M4 from its summary. Every brief figure is reproduced (IV-04, IV-05).

**Finding the real gap.** The brief's 40.39 m3 mixes 22.16 m3 of blinding into Urban's figure. Like for like, Urban's drawing-supported RC is 316.06 m3 against the freelancer's 352.44, a gap of 36.37 m3. Each part of that gap is located and classified (04).

**An element crosswalk with nothing dropped.** Every freelancer row and Urban item sits in exactly one group (IV-07). Beams compare per floor and mark; footings and columns per mark; stairs per stair; domes and the pool per component.

**Exact geometric crosswalks between registers**, through the sheet origins:

- the S8.1A regions decompose M4's lift / lobby cell exactly;
- the dome circles (S-BOUN) locate the ring arcs and the dome opening;
- the S9A hatches locate the cantilever portions.

**One real engine defect, fixed.** Planted columns labelled on slab plans were missed. The fix is gated in V4 and changes nothing else (IV-19).

## What is not working / not done

**Sources not in this environment.** The freelancer's original workbook and both sealed MCP reports are missing. U-C4N is only comparable at category level.

**Engine behaviour left as it is, because it is fail-safe:**

- the dome's radial lines read as winders;
- the dome ring arcs bound to B4;
- the pit outlines not used as face edges.

These are corrected by M5 ownership decisions for this project only (no generic rule). A generic rule needs a held-out set with domes and spiral stairs.

**Stairs, domes, pool and lift come from the frozen S-stages.** The generic route does not measure them yet.

**The quotation is not ready.** The beam depth reading alone swings 16.25 m3. Five element types have no drawing.

## Recommended next steps (in order)

1. **Get the minimum answers** (13): RFI-M5-15, RFI-M5-01, RFI-M5-07, RFI-M5-16, RFI-M5-02, RFI-M5-03.
   - The person review loop (M4 next step 1) turns each answer into MANUALLY_CONFIRMED.
2. **Upload the freelancer's original workbook and both MCP reports**, then rebuild 03 against their item tables.
3. **Bring stairs, domes, pool and lift into the generic route** (S8.x engines as modules), so that one run measures the whole RC scope.
4. **A held-out synthetic set with domes, spiral stairs and lift pits**, before any generic rule for E-02 to E-04.
5. **Quote on provisional quantities with a variation mechanism:**
   - measured 316.06 m3;
   - conditional allowances 14.55 - 35.38 m3;
   - exclusions for the undrawn items;
   - blinding as its own line.

