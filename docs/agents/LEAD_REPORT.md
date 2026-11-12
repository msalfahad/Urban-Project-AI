# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-12 00:16 UTC

Drive read OK (no file in the private project folders modified since 16:00 UTC 10 Nov, no photo task). Training villa: candidate of record now ARCH_TAKEOFF_V3.0.72 / master 1.73.0 (NOT RELEASED; released V2.9 + route G untouched). 8 pieces merged since 20:17, all checked by own re-measure; READY 0.
- MASONRY (m2 / pcs / m3): in the candidate: 18 blank lines carry a one-ended limit beside (2F 0.15 parent at most 1.965 m2; GF 0.15 parent at least 12.9311 m2; 2F part-host units at most 118.375 pcs, mortar at most 0.104762 m3); 10 held ranges rounded outward by rule (<= 4e-6 m3). 28 lines changed, 5,095 identical, 28 / 28 AGREE by hand, full suite 23,482 pass 0 fail. No total moved.
- CONCRETE (m3; released / bounded / one-sided / blank never summed): released 317 = 291.476251 unchanged. Checked, waiting for the concrete package: ground beams 17 lines at least 5.099845 (3 court lines blank, landing / yard level not printed, D-35; freelancer 0.30 x 0.60 gives 11.12 on the same plans, UNRESOLVED on D-33 / D-35); east dome ring at least 0.115155 (may tighten to 0.140345 if the detail's two levels define the depth: new task); 11 roof-edge strips blank (no depth printed, 6.9471 m2 per m depth); 0.378618 m2 of drawn strip in no line (new task).
- FORMWORK (m2): 370 B10-13 lines classed on their members: 26 bounded 87.94 .. 103.19, 32 at least 98.54, 54 fix rows 33.127, 258 blank by cause; soffit width ratio 0.2502 vs drawn 0.250 (-0.000555 m2 on one line, loose low end): new task; 20 stair formwork lines not yet classed: new task.
- FINISHES (m2): stair skirting 2.25 vs 2.20 m explained (0.05 m nosing; F-V715-1 closed); MS1-T / RS-C ceilings bounded. Voids drawn by floor (light well 26.240, domes 15.359 x 2, lift shaft 3.24 per floor, oval 3.824 exterior). ENGINE_WRONG candidate: 1F living porcelain 33.411 -> 33.468 m2 (+0.17 %, light well deducted twice by overlapping room pieces); a ceiling line over the void risks 16.005 m2 twice. Plaster like for like -15.81 .. -9.88 % unchanged; shaft 13.50 m2 unresolved (new task with the void register).
- REBAR: parked by your decision; nothing done.
- Learned: deduct a void once as the union of the pieces that cut it; a merge that adds a master version must promote it in the same merge; restatements without a drawing read keep leaving loose figures (new rows ask for a handle per figure).
- Team health: 10 runs since 20:17, all closed (one Checker run correctly stood down by its overlap guard); self-check PASS everywhere; Checker 7 Gate A + 1 Gate B in 4 h. Board: 8 TODO (S 3, A 3, I 2), queue check 19 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (concrete limits package T-722 next, V3.0.73). M3 (reconciled + scorecard): masonry limits in the candidate a day ahead of estimate; concrete 13 Nov MEDIUM-HIGH, plaster / paint 14-15 Nov MEDIUM.

OWNER PACKAGE: none today (no item meets section 2.7). The designer list (DESIGNER_QUESTIONS.md) is now per item: the roof datum D-39 holds the most lines (92 alone; plaster 1,115 .. 1,251 m2 bounded + 18 blank); send it when you choose.

NEEDS FIXING (owner only): (1) Decode fix PR #6 still open: the Drive download arrives as raw binary and the wrapper refuses it; two worker runs tonight re-encoded it by hand to read the drawing (works, costs time; one earlier run skipped the drawing). (2) Approved scheduled-task edits still not possible under the repository settings (no change since 11 Nov).

## LEAD REPORT 2026-11-11 20:25 UTC

Drive read OK (no file in the private project folders modified since 16:00 UTC 10 Nov, no photo task). Training villa: candidate of record now ARCH_TAKEOFF_V3.0.71 / master 1.72.0 (NOT RELEASED; released default V2.9 + route G untouched). Whole lines verified: 1 (CONC.SLAB), unchanged; scoreboard restated 20:04, no cell changed.
- CONCRETE (m3; released / bounded / blank never summed): released 317 = 291.476251 unchanged. LINTELS: 16 blank lines now carry an upper limit beside them in the candidate (family 1.322146 m3, measured stopper to stopper on one drawing; R-T704-2), text-only, no total moved; full suite 23,379 pass 0 fail. Checked, not wired: stair / parapet / lift / neck blanks 11 lower limits + 4 named designer items (lift pit walls >= 1.903 vs freelancer 1.65: engine right, his figure is below the drawn floor); with the Checker: ground beams 17 lines >= 5.099845 m3, 3 court lines blank (landing / yard datum not printed); freelancer's uniform 0.30 x 0.60 gives 11.12 on the same plans, UNRESOLVED on D-33 / D-35 (not a reason to raise ours). Still blank with no investigation: 12 beam lines -> new task.
- MASONRY (m2 / pcs / m3): checked parent one-ended limits: 2F 0.15 parent at most 1.965 m2, GF 0.15 at least 12.9311 m2; 5 parents blank by cause. Next into the candidate together with the earlier masonry limits (V3.0.72).
- STAIR FINISHES (m2 / lm): 85 held lines sorted by cause; risers 10.338610 m2 measured, nosing pitch 20.234818 lm; skirting payable 17.009 .. 23.300 lm conditional on ORR-007. PARTIAL: the worker could not read the drawing (raw download refused) and the Checker found one run reading 2.25 m on the plan vs a 2.20 m wall -> round 2.
- REBAR: parked by your decision; nothing done.
- Learned: a held line needs its cause as an id, not prose (1,157 held lines carry prose only, so the designer list cannot yet be counted per item); a finish length must be read on one drawn geometry before release.
- Team health: 14 runs since 16:22, all closed (one Checker run correctly stood down by its overlap guard); self-check PASS for every worker; Checker 4 Gate A + 1 Gate B in 4 h; READY 2. Board: 8 TODO (S 3, A 3, I 2), queue check 22 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (concrete blanks: beams, ground beams). M3 (reconciled + scorecard) at risk, estimate 13-14 Nov: masonry package next, concrete limits package after it (concrete before plaster, your order).

OWNER PACKAGE: none today (no item meets section 2.7). The designer list becomes per item when the census passes the Checker.

NEEDS FIXING (owner only): (1) Decode fix PR #6 still open: this evening a worker built a stair-finish package without reading the drawing because the raw download was refused; agents re-encode meanwhile, but it costs runs. (2) A Gate B full suite still takes about an hour of one Checker run (18:58 -> 20:05). (3) Scheduled-task edits you approved cannot be made under the current repository settings (as recorded 15:30).

## LEAD REPORT 2026-11-11 16:25 UTC

Drive read OK (no file in the private project folders modified since 16:00 UTC 10 Nov, no photo task). Training villa: candidate of record stays ARCH_TAKEOFF_V3.0.70 / master 1.71.0 (NOT RELEASED; released default V2.9 + route G untouched). No candidate line moved since 12:25: five research pieces merged (all unwired), one integration package rejected. Whole lines verified: 1 (CONC.SLAB), unchanged.
- CONCRETE (m3; released / bounded / blank never summed): released 317 = 291.476251 unchanged. Slab -0.77 % vs freelancer closed by storey: GF reference rounding, 2F thickness zones; 1F -0.556333 stays UNRESOLVED (his 1F row is a typed area). Beam -0.128 = his total's formula omits one row (his slip). Column tail settled from the drawing: 5 roof-plate lows +0.12724 (not the flat +0.13364); held 11.80007 .. 15.5015, tank pair LOWER_ONLY 0.3287 each (designer item). Still blank: lintel 21, ground beam 20, beam 12, stair 5, parapet 4, neck 4, lift 2: new investigations opened for all of them except beams (designer list).
- LINTELS: the wiring package (16 blank lintels get an upper bound, family 1.321826 m3) failed the full suite on a declaration test, not on quantities; my ruling raises the bound to 1.322146 m3 (measured stopper to stopper on one drawing); rework is first in lane I.
- PLASTER / PAINT (m2): like for like plaster -15.81 .. -9.88 % vs freelancer (unchanged). 40.50 of his 54.00 shaft row is the round-stair well, carried once by the engine (engine right); 13.50 unresolved. New omission found: double-height band plaster 0.84 .. 0.87 / paint 3.34 .. 3.53, to be wired after masonry.
- WATERPROOFING (m2): 58 held / missing lines classed: 46 designer, 8 measurable now (measured, unwired), 3 owner Q-34, 1 not an element; sunken wet-room panels add a HELD 0 .. 13.335 m2 recess membrane. Freelancer not compared.
- REBAR: parked by your decision; detailed 9,628.462205 kg kept as is; no ratio, no kg/m3 assumed.
- Learned: a rule conflict is settled by the drawing (it moved the plate low to a third value); compare like for like before calling a discrepancy; an upper bound comes from one geometry; read a reference total's formula before reconciling it.
- Team health: 13 runs since 12:21, all closed with a final line; self-check PASS for all three workers; Checker throughput 5 Gate A + 1 Gate B in 4 h; READY 0 now. Board: 8 TODO (S 4, A 2, I 2), queue check 20 actionable, 0 flagged.
- Gate: lowest open gate 1 (concrete blanks); M3 (reconciled quantities + scorecard, 12-13 Nov) at risk: the lintel and masonry packages must both pass Gate B by 13 Nov.

OWNER PACKAGE: none today. Designer list started (DESIGNER_QUESTIONS.md, 13 items by family); it is for you to send, and becomes per item once its census lands.

NEEDS FIXING (owner only): (1) Decode fix PR #6 (raw Drive downloads) still open: agents re-encode meanwhile. (2) A Gate B full suite takes longer than one Checker lock on 2 cores (T-693 needed 2 runs). (3) Scheduled-task edits you approved cannot be made from any session under the current repository settings (as recorded 15:30).

