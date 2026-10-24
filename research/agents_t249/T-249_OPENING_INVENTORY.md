# T-249: an engine-independent opening inventory (development villa; rule for every villa)

Worker 2, 2026-10-24 01:45 - 03:00 UTC, run session_01VftBbWAkawzMhpZZXGgXua. Lane A, gate 1. New research files only
(`research/agents_t249/*`, `tests/t249_opening_inventory/*`); no engine file, rule file, registry, frozen method, census
version or released quantity changed; nothing applied to any line. Development villa (Alsenan), not an accuracy claim.
Drawings cited by Drive title; no image, coordinate, client name or personal data committed (rows carry entity handles).
ERS: read; s.2 steps 1-4 (physical element, evidence hierarchy, reconstruction NOT from the engine, reconciliation), s.3
(existence before arithmetic; a notation's meaning first), s.4 (rule + tests), s.7 row below.

## 1. Result in engineering terms

| Item | Engine-independent inventory (this run) | T-198 census (engine-seeded) | V2.9 / V3.0.8 lines (T-236) |
|---|---|---|---|
| Windows | **29** = GF 12 + 1F 13 + 2F 4, each from a plan glazing symbol with its handles; 23 also bound to an elevation window | 29 | 27 (W18, W03 in no line) |
| Doors (leaf) | **27** = GF 14 + 1F 10 + 2F 3 (26 door blocks + 1 loose swing arc) | 27 | 17 lines + 10 held in the door schedule |
| Site gate | 1 (door block in the site frontage; class GATE from T-150) | 1 | none |
| Arches (leafless, drawn as arch blocks) | 2 | 2 | - |
| Crosswalk | doors 28 / 28 and windows 29 / 29 AGREE; **0 missing, 0 extra** | - | - |

So the census the BOQ checks against is now confirmed from the drawings, not from the engine: T-236's named limit ("window
completeness is not yet engine-independent") is closed for doors and windows. The two windows that both runs omit are real
drawn windows:

- **W18** (1F sea-side bath): plan glazing symbol 0.500 m (handles C33 ...), NW elevation window bound by position
  (residual 0 mm; DIMENSION 500, sill 839.3 handle 2EEC, head 2160.7 handle 2EFA, printed 50 / 84 / 216).
  Window line delta **+1 pcs, +1.080 m2** (0.50 x 2.16, DRAWING-CONFIRMED).
- **W03** (GF curved pool glazing): one curved glazing symbol on the GF plan (handles 26D ...), glass lines (arc part)
  6.658 / 6.703 / 6.747 / 6.792 m = the four lines Q-38 names; width the printed 657 (owner Q-38 A), height NW DIMENSION
  2E7A 4300 from +1.00. Window line delta **+1 pcs, +28.251 m2** (6.57 x 4.30, DRAWING-CONFIRMED).

Engine vs freelancer (aluminium windows, T-181 like-for-like basis): the freelancer prices both (W18 0.60 x 0.80 = 0.480 m2,
W03 6.57 x 4.30 = 28.251 m2); our window lines carry neither, so the windows line is short by 2 pcs / 29.331 m2 against the
drawings in BOTH runs. With the delta, W03 AGREES with him exactly (28.251 vs 28.251, 0 %); W18 is +0.600 m2 (+125 %) on
his row, ENGINE_RIGHT (T-083: width and height printed; his 0.60 x 0.80 is printed nowhere). Not applied here: lane I
(T-232) carries it.

## 2. The physical element and the evidence hierarchy (ERS s.2 steps 1-2)

An opening is a gap in a wall closed by a leaf (door), glazing (window) or nothing (passage). Its existence is proved by
what the drawings draw or print, in this order: a schedule row, a plan tag, the plan symbol in the wall, an elevation /
section feature. On this project two of those do not exist:

- **No schedule** is issued (designer D-07, T-194).
- **No opening tag** is drawn: 0 TEXT / MTEXT / ATTRIB in model space or any block reads as a W / D mark (P7757.dxf, this
  run; `summary.json` `dxf_opening_tags_found: 0`). The ids W01 .. W29 / D-xx-nn are the team's census ids (T-083 / T-150),
  not drawing tags. So "tag census" on this villa means the drawn symbols; a villa that prints tags feeds the same
  `inventory.build` with PLAN_TAG / SCHEDULE observations.

What was read (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip / P7757.dxf, read-only):

1. **Plan glazing symbols**: layer W entities on each storey plan, clustered (touching within 0.03 m), kept when long >= 0.30
   and deep <= 0.35 m (a wall); three loose glass lines 0.05 m apart merged into one symbol only when they are equal and
   aligned. Width = the symbol's long extent (jamb to jamb); curved symbols carry no box width.
2. **Door leaves**: every block insert whose block carries a swing ARC on the door layer (D315, D120, D115, d220, D215,
   D200: 26 inserts) plus loose swing arcs 0.55 .. 1.10 m on the door layer (1: r 0.690, GF); arch blocks (arch120: no
   arc) are leafless openings.
3. **Elevations**: the merged T-194 elevation features (NW / SE read from DXF DIMENSION entities and jamb lines; SW / NE
   from the PDF scans Pages_07-08 p.7 and p7757_arch_sheet09), bound to the plan symbols by POSITION: one offset per facade
   solved from the data (the offset that binds the most features within 0.05 m), a feature binds only to a symbol of its
   own storey, a printed width must agree within 0.05 m. SW 12 / 12, NE 3 / 3, NW 4 / 4, SE 4 / 4 bound; 0 ambiguous, 0
   unbound; worst residual 19 mm (PDF scale read). Plans registered to the block A$C662819C0 repeated at one plan point on
   all three storeys.
4. Windows with no elevation by position: W02 (NW draws the GF as a section), W03 (NW chain printed, projected width not),
   W09 / W10 (annex court wall; SE cuts the annex), W11 / W12 (fence elevation, symmetric pair, T-194). Reasons in each
   row's NOTE; none is missing.

The census ids were attached AFTER the inventory existed: 57 rows by the engine record at the same plan point (V2.9 run on
the same DXF, scratchpad, exit 0; windows within 0.35 m, doors within 1.30 m, one id per row per storey) and 2 by unique
attributes: W03 and W18 have no engine record at all (T-236 F5), so W03 is the only curved glazing symbol on the GF plan and
W18 the only 1F census window of width 0.50 m. W17 binds to COP-001 by position. 0 rows unbound.

## 3. W18 and W03: which lines they belong to and why none carries them (the three consequences)

| Opening | Window supply line (m2, pcs) | Blockwork deduction | Finishes deduction |
|---|---|---|---|
| W18 | **absent** in V2.9 and V3.0.8: +1.080 m2, +1 pcs | already in the T-175 ledger (host 1F-W00, -1.080 m2): no new delta | already in T-175 (wall tile 1.080 bath side, external plaster / paint 1.080) and T-128 r3 (1F-12 W18 0.50, sill 0.84): no new delta |
| W03 | **absent** in V2.9 and V3.0.8: +28.251 m2, +1 pcs | NOT_APPLICABLE: the host GF-W37 is a glazed line, no masonry is built in it (T-175; build before deduct) | HELD: the room-side developed line (T-128 r3 1.625 + 5.106 = 6.731 m vs the drawn room-face arc 6.5675 m) belongs to T-250 |

Why no window line carries them: the window lines of both runs are built from the engine's opening records; the engine
finds a window as a band opening (a wall gap with jambs) carrying glazing. W18 sits inside a wall run as a glazed stretch
with no band opening of its own (T-040 G7: "V2 GLAZED_STRETCH 0.50", no opening id); W03 is a curved glazed LINE closing a
4.95 m straight gap (T-103 / T-175 GF-W37), which the curved-opening reader does not take as a window (it found only
W17, COP-001). The masonry and finish ledgers were built from the census (which knew both), the window lines from the
engine (which did not): the same drawn element, two different inventories. `DELTA_T249.csv` lists the deltas for lane I;
nothing is applied.

## 4. Reconciliation (ERS s.2 step 4)

- Inventory vs T-198 census: 59 / 59 rows in scope agree (27 doors, 1 gate, 29 windows, 2 arches); 9 census rows are
  leafless / unglazed gaps (SX-01, SX-03, L-GF / 1F / 2F-01, U-01, P-GF-01, P-1F-01, P-GF-05) with no plan symbol of their
  own: NOT_IN_SCOPE of a symbol inventory (their existence rests on the T-175 / T-194 wall-gap reads; named limit).
- Inventory vs T-236's inventory and T-232's inputs: both read the T-198 ids, so the same 29 / 27 agree; `OPENINGS_T249.csv`
  keeps the columns ID / KIND / FLOOR / ENGINE_REF, and the T-236 reader takes it in place of the T-198 seed (test).
- W02: the plan draws ONE continuous glazing symbol 6.3316 m (no pier), agreeing with sheet03 "633"; the renders show two
  windows with a pier (T-161 F23, designer D-53): pcs stays HELD 1 .. 2 (T-198 C6), area HELD (D-45). Not decided here.
- Elevation-only features (9 small squares, T-198 E-SE / E-FE) stay UNKNOWN: not windows of this inventory (R4).

## 5. General rule (proposed UP-OPEN-INV-001 v1.0.0, any villa; provenance: ERS s.2 step 3, the T-236 lesson, the T-017 lesson; new file, not a project fact)

Before a doors / windows line is checked for completeness, the openings are inventoried from the drawings alone: plan
symbols (leaf, glazing), plan tags, schedule rows and elevation / section features, each opening counted ONCE per physical
location with the entity handles it was read from. An opening known only to the engine or to a derived list is refused;
two tags on one opening are one opening (TWO_TAGS); one tag at two locations is two openings (DUPLICATE_TAG); an elevation
feature bound to no plan opening is ELEVATION_ONLY (pcs HELD, never counted, never measured); elevation positions bind
identity only (one offset per facade, solved from the data, same storey, width check, ambiguity refused). The engine's list
is used only afterwards, as a crosswalk (AGREE / MISSING_FROM_LIST / EXTRA_IN_LIST), never to settle existence.

## 6. Tests

`tests/t249_opening_inventory/test_inventory_rules.py` (fixture villa T249-K, NOT Alsenan, hand truth in the docstring:
three loose glass lines -> one 1.50 window, depth 0.10; ticked 0.90 symbol; curved symbol has no box width; a 0.20 sliver is
no window; a plan tag without an elevation; an untagged window bound only by its elevation; a duplicated tag W3 -> two
openings; two tags on one window -> counted once; an elevation-only window -> HELD, 5 settled + 1 held; adverse: an
engine-only and a derived-list-only opening refused (R1), one opening produced twice refused (R2, by location and by
handle), a symbol without handles refused (R5), a door and a window at one point refused, a mirrored facade binds fewer
features, millimetres read as metres bind nothing, one feature cannot solve an offset, a width that disagrees refuses the
binding, an equidistant feature is AMBIGUOUS, the rotated (Y-axis) facade binds the same; crosswalk never settles
existence). `test_alsenan_inventory.py` (counts by kind and floor, existence never the engine, unique handles, W18 / W03
bound without the engine, crosswalk 0 missing / 0 extra, no ambiguous elevation binding, residual <= 50 mm, the 29.331 m2
delta, held never 0, no coordinate committed, the T-236 reader takes the file; byte-for-byte rebuild when
URBAN_P7757_DXF and URBAN_T249_RUN are set: PASSED this run).

## 7. Lessons-register row (proposed, s.7)

2026-10-24 | Two drawn windows (W18, W03: 2 pcs, 29.331 m2) were in the census, the masonry and the finish ledgers but in
no window line of either run, and the completeness check could not see it because its window list came from the engine
| each ledger took its openings from a different inventory (census vs engine records) and the check compared the engine's
lines against an engine-seeded census | inventory openings from the drawings alone (symbols, tags, schedule, elevations,
with handles) before any completeness check; the engine list is a crosswalk, never an existence source (any villa) |
t249 `test_engine_only_opening_refused` (normal: symbol-sourced rows pass; adverse: engine-only / derived-list-only
refused) | READY (T-249), Checker to verify.

## 8. Held / unknown / missing (never 0)

W02 pcs 1 .. 2 and area (D-53, D-45); W03 room-side developed line (T-250); the 21 headless windows' areas (D-45, as
before); door heights ASSUMED — OWNER-APPROVED 2.20 (Q-55 C, unchanged); the leafless gaps (passages, lift, SX, U-01) are
outside a symbol inventory; which drawn fence-elevation window is W11 vs W12 (symmetric, no quantity effect).

## 9. For the Checker (re-count)

P7757.dxf: windows = layer W clusters on the three plans (handles per row in `OPENINGS_T249.csv`); doors = the 26 door-block
inserts + loose arc 334 (GF, r 0.690); W18 NW DIMENSIONs 2EEC / 2EFA and a 500 on the NW frame; W03 NW DIMENSION 2E7A and
glass polylines 27D / 27E / 27F / 280. Rebuild: `python3 -I research/agents_t249/alsenan_t249.py check --dxf <P7757.dxf>
--engine-run <ARCH_TAKEOFF_V2.9 out>`.
