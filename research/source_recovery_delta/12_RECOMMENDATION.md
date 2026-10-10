# Recommendation: after the source-recovery delta

S4, S5 and S6 stay frozen. Nothing here changes a frozen quantity.

The engineer's statement made the issued set worth a second, graphics-first pass. That pass found ten newly source-resolved items, all of them graphic readings of the issued PDF and DXF:
- **S4:** S4-03, S4-07, S4-12.
- **S5:** S5-01, S5-04, S5-18.
- **S6:** S6-02, S6-04, S6-05, S6-14, S6-15.

It also withdrew one earlier reading: the "straight" single-layer footing bottom bars.

Most remaining blockers are true gaps in what the set prints: hook and development lengths, the boxed-bar meaning and diameter, and the concentrated-load definition. They are now recorded as `SOURCE_EXPECTED_NOT_LOCATED`, not "engineer required".

## 1. Run the three candidate rounds now. They do not depend on the engineer.

Run them in this order. Each round is freeze-before-compare, and no candidate may become VERIFIED.

1. **S6.1** (largest unlock):
   - C01: 80 single-link stirrup core paths. Lower bound 2(b-2c-d) + 2(h-2c-d), with c = 25 mm from note 22; hooks excluded.
   - C02: 7 STR2 core paths (outer link plus the inner link's legs).
   - C03: 14 CB end-support top-bar legs (90° leg down to the bottom-bar level).
   - C04: release the two B3 WITH STAIR spans on schedule bars over the plan run.
   - C05: release the B26 base components; the planted-column extra stays blocked.
   - Carried candidate: CB7's two candidate-invariant stirrup counts (from S6).
2. **S4.1** (correctness first):
   - C01-C03: 20 BOTTOM_LONG and 20 BOTTOM_SHORT single-layer components go from VERIFIED to LOWER_BOUND, and the two-layer bottoms gain an END_TREATMENT facet. The kg does not fall; the release claim becomes honest.
   - C04-C05: record the BOXED shape and the FF 2 + 2 Ø16 assignment as facets. Both stay blocked.
3. **S5.1:**
   - C01: 4 GB core paths that were blocked only by link topology.
   - C03: SB1 and SB3 strap core paths.
   - C02: classify each GB end as interior-continuing (through-support run, per p.13) or as an end support (still blocked).

**Owner decision needed first:** may `SOURCE_FOUND_DERIVED` graphic facets release `LOWER_BOUND` components? The candidates use only envelope lower bounds: the larger note-22 cover, with hooks and widths left out. No generic code value is involved.

## 2. Send the engineer one short pack

**A. Conflicts (`10_PENDING_ENGINEER_CONFLICTS.csv`, 13 rows):**
- F / F10 (pending separately);
- SB2: one yes / no, because the issued p.10 sheet shows only 100x50;
- the annex +0.30 depth;
- the GB band against the support face;
- the five beam-width conflicts;
- CB4, CB5 and CB8 span data;
- CB3 against B3 WITH STAIR.

**B. Expected but not located (`11_SOURCE_EXPECTED_NOT_LOCATED.csv`, 35 items).** Ask in this order, by number of frozen rows unlocked:

| # | Ask | Items | Frozen rows |
|---|---|---|---|
| 1 | Which sheet or note defines "without concentrated load" (and is there a "with" section)? | S5-10 | 210 |
| 2 | Beam and GB bar development and end hooks (lengths or a project rule) | S6-01, S6-03, S5-02, S5-03 | 512 |
| 3 | Stirrup hook angle and extension | S5-05, S6-07 | 242 |
| 4 | GB detail selection: <2.5 m against <5 m, length basis, mixed / exterior spans, and the <2.5 m link | S5-08, S5-09, S5-15, S5-17 | 230 |
| 5 | Side bars "2Ø12/30cm": per face or total; meaning of /30cm | S5-14, S6-11 | 83 |
| 6 | BOXED "3+n": what each number counts, diameter, orientation; FN blank | S4-01, S4-02, S4-04, S4-05 | 52 |
| 7 | Exterior GB depth: GF structural slab level or floor build-up | S5-06 | 22 |
| 8 | CB typical: hanger / second top row, "0.3 Ln2" in 2-span frames, the span meant by "0.15L" | S6-08, S6-09, S6-10 | 39 |
| 9 | FF 2 + 2 Ø16 length and whether all four pit walls carry them; two-layer end treatment; +1 edge bar | S4-08, S4-10, S4-11 | 31 |
| 10 | Single items: `******` marks, 1811-1812 support, CA cantilever, ring beams, untagged spans, bindings, CB reading direction, SBT curtailment, inner STR2 width, footing short-bar shape | S5-12, S5-13, S6-13, S6-16, S6-22, S6-21, S6-20, S6-23, S6-06, S4-13, S4-14 | — |

Under the new workflow, the engineer can answer each ask with a sheet and location in the issued set. If the answer is not in the set, it becomes a new project instruction (a versioned claim), never an assumption.

## 3. Tooling

**Adopt `vector_pdf.py` for the detail sheets (research only).** It is a pure-Python pypdf reader.
- It reads every stroke with its CAD layer (`S-REIN.D` and others), with no PyMuPDF and no rasteriser.
- That was enough to prove bar shapes, leader targets and link topology on pp.11-16.

Promoting it into `engine/source` is a separate owner decision. So is the PyMuPDF question; this lane removes the need for PyMuPDF on vector sheets.

## 4. Not in this round

- No S4 / S5 / S6 recalculation.
- No kg.
- No S7.
- No reference or benchmark figure was opened.
