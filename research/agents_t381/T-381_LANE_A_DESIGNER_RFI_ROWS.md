# T-381 Designer RFI rows for the lane A holds no drawing settles (Alsenan; rule for every villa)

Worker 2 (lane A), 2026-10-31, branch `agents/task-T-381`. Research files only: proposed RFI rows as TEXT for the Lead,
who applies them to `docs/agents/rfi/B_REMAINING_RFI.md` (the worker never edits the rfi files). NOTHING IS SENT (owner
2026-10-29 22:05). No quantity is computed; no candidate line, rule, method or released quantity changes; V2.9 + route
G stays the default. Drawings named by Drive folder ('Alsenan chalet project') and title only.

Tool: `t381_rfi_rows.py` (DESIGNER_RFI_ROWS_LANE_A_V1, stdlib only) -> `T381_RFI_ROWS.csv` (7 rows),
`T381_SUMMARY.json`. Repeat: `python3 -I research/agents_t381/t381_rfi_rows.py --check`. Tests `tests/t381_rfi_rows`
(22). Every row is validated by R-RFI-BIND-1 (T-376): each citation must be found verbatim in the merged ledger it names,
one fact once, ADD_TO only an RFI id that exists, a NEW id that does not, owner rules searched and none settling the
fact, governed quantity a range or HELD with a reason (never 0), no Arabic script, no client name.

## 0. Sources

- Merged ledgers (Checker-verified, cited not re-derived, WORKFLOW_CONTROLS s.10.5): T-369 (MERGED 6b9ce820) shower
  register; T-370 (MERGED d7619aca) fixture register; T-377 (MERGED 30e7ab2a) arched audit, `CANDIDATE_T377.csv` (V3.0.27
  line ids), `HELD_CHECK_T377.csv`; T-238 census; T-302 W17 developed hole; T-368 r2 (MERGED) edge ledger.
- RFI files read for duplicates: rfi/A_PRIORITY_RFI.md, rfi/B_REMAINING_RFI.md, rfi/D_REMOVED_REVISED.md,
  DESIGNER_CLARIFICATIONS.md (D-45, D-62) and the T-376 rows (all structural: no overlap).
- Owner rules searched first (OWNER_QUESTIONS_ANSWERED.md): Q-30 A, Q-32 A, Q-39, Q-40 A, Q-48 A, Q-55 C, Q-76 A.
- Own sheet search this run (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55,
  and sanitary-7757.pdf, decoded by the wrapper into the private folder only):
  - P7757.dxf TEXT / MTEXT (model space and block definitions): no English text for sink, shower, valve, mixer, tray,
    header, beam, arch, soffit, ceiling or waterproofing (Arabic text is x-arab encoded and was not searched by
    pattern; T-369 / T-370 read it).
  - Insert census: fixtures only WASH2 x5 (basins); no sink, shower or tray block. Both arched openings are the block
    `arch120` (inserts 1F8 GF and BEC 1F, scale 1): a 1.00 x 0.15 m rectangle whose two long sides are on layer 2
    (HIDDEN = overhead), i.e. the plan marks a head but prints no level.
  - DIMENSIONs within 1.8 m of the bath labels C2C / C2F, WC 12B6, WC 1C8, the arch inserts, the kitchen 276, pantry
    178, laundry BDD and the GF-14 pair 2DB / 2DC: room and wall dimensions only (e.g. FF1 3650, 1008 / 101F 2050, 10AB
    2450; 138E 2500, 13D8 3000); none gives a screen position, a tray, an arch level or a head level.
  - 2DB / 2DC: LINEs on layer 2, linetype HIDDEN, 0.150 apart, between wall face 222 and wall end BC (agrees with
    T-368 r2).
  - sanitary-7757.pdf rendered at 300 dpi (private): p.1 GF kitchen holds FD 4 in and CO 4 in, no fixture; the W.C by
    the driver's room holds WC, basin, FD 4 in and the yellow valve symbol with no screen or tray; p.2 the two 1F west
    twin baths carry blue screen lines across the room with the valve beyond, undimensioned. All agree with T-369 /
    T-370.

## 1. The proposed rows (acceptance (a))

| Row | RFI | Fact | Governs (unit) | Unlocks | Stays HELD meanwhile |
|---|---|---|---|---|---|
| R01 | **RFI-B-A14 (a) NEW** | fixtures of the GF kitchen, GF pantry, 1F laundry (FD drawn, no fixture) | pcs, HELD unquantified (count per room printed nowhere) | B12-01 sink / appliance points in 3 rooms (no candidate line: B12-01 EXPERIMENTAL) | sinks / washer point UNKNOWN, never 0 |
| R02 | **RFI-B-A14 (b) NEW** | identity of the valve symbol in the GF W.C by the kitchen (UNK-GF-01) | 0 .. 1 pcs (shower 6 or 7; or a hand-shower point) | B12-01 shower count | UNK-GF-01 UNKNOWN; WP impact 0 m2 either way (T-369) |
| R03 | RFI-B-A12, add to its wet-room details | 3 tray sizes and 3 walk-in zone extents | HELD unquantified: governs NO current quantity | 6 HELD extents; tray size of 3 tray pcs | B8-04 stays 0.000 ASSUMED - OWNER-APPROVED (Q-40 A) |
| R04 | RFI-B-A04, add (b) | W17 head soffit through the 0.20 m curved wall: radial or straight in the view direction | **8.7414 .. 8.9965 m2** room-side hole on each of plaster and paint (range 0.2551 m2 each) | L-31db3c83552682d92ca3 FIN.PLASTER and L-349db74a70e1eecda2d2 FIN.PAINT (each 61.4626 .. 61.7177 m2), L-c90d5d6c06a671fc3b99 W17 reveal BLANK, W17 arris (T-314) | W17 finish HELD BOUND, reveals and arris HELD; window unit unchanged (Q-76 A) |
| R05 | RFI-B-A02, name the arch | A-GF-01 (GF dewaneya / wash, 1.00 m) springing, crown, form | deduction per face HELD, bound **3.15 m2** (T-292; drawn candidate 2.4131, T-238 A6), 2 faces | GF-01 / GF-02 plaster-paint deductions; GF-W26 masonry deduction and mesh k 1 .. 6; reveals; tile edge | every A-GF-01 edge and deduction item HELD (R-T377-2) |
| R06 | RFI-B-A02, name the arch (send with A RFI-A08) | A-1F-01 (1F master bed room / unlabelled space, 1.00 m) springing, crown, form | deduction 1F-10 face HELD, bound **3.35 m2**; other face UNKNOWN | 1F-10 deduction; 1F-W16 masonry deduction and mesh k 1 .. 6; reveals | every A-1F-01 edge and deduction item HELD |
| R07 | RFI-B-A10, add (c) | the hidden element over the GF-14 open side (1.256 m): what it is and its underside level | **0 .. 8.556 m.l** (two tile edges head .. 3.65 each + head arris 0 .. 1.256); header-face tile m2 HELD unquantified | GF-14#WEND, #FSTOP, #OS1#HEAD (T-368); header face on wall-tile line L-fa408571a8adcfaf1a1f (BLOCKED_RFI) | GF-14 open-side items HELD by name |

Ranges are per row and are NEVER added across rows. "Unlocks" means the answer is one input the item needs; an item
closes only through a task and a Checker verdict.

### Text for the Lead to apply (internal quantities stay internal, never sent)

**RFI-B-A14 (NEW) Sanitary fixtures not drawn.** Drawing: sanitary-7757.pdf p.1 (GROUND FLOOR DRAINAGE PLAN) and p.2
(FIRST FLOOR); architectural P7757 sheets 03 / 04. (a) The sanitary sheets drain the GF kitchen (FD 4"), the GF pantry
(FD 3") and the 1F laundry (FD 4") but draw no fixture in them, and the architectural plans draw none either: which
fixtures are provided in each (kitchen sink, pantry sink, washing-machine point) and where do they waste? (b) In the GF
W.C beside the kitchen (by the driver's room), p.1 draws next to the FD 4" the valve symbol that p.2 / p.3 draw inside
the screened shower zones, with no screen, no tray and no legend entry: is it a shower, a hand-shower / shattaf point, or
something else?

**RFI-B-A12, add to the wet-room details request:** the sizes of the three shower trays (GF bath by the master bedroom,
1F bath by the laundry, 1F east bath) and the extents of the three screened walk-in zones (both 1F west twin baths, the
2F W.C). The sanitary sheets draw them but are marked not to scale and no sheet dimensions them.

**RFI-B-A04, add (b):** W17 (1F, curved on plan, over the pool): the NW elevation draws the arched head on the exterior
face only. Does the head soffit run radially through the 0.20 m curved wall (same head height on both faces along each
radius, like the drawn radial jambs) or straight through in the view direction? A section or interior elevation of W17
settles it.

**RFI-B-A02, name the arches inside "arch rise of ... 3 arches":** (i) the 1.00 m arched opening between the GF dewaneya
and its wash space (plan: opening with overhead lines; one section draws a segmental arch in the wall beyond the cut with
no dimension); (ii) the 1.00 m arched opening on 1F between the master bed room and the unlabelled space of A RFI-A08
(plan only; no elevation or section draws it). For each: springing and crown levels (or rise) and the arch form.

**RFI-B-A10, add (c):** GF plan, the 1.256 m open side between the wash lobby by the core W.Cs and the lift lobby: a pair
of hidden (overhead) lines 0.15 m apart is drawn across it in the plane of the wall; the GF roof slab plan draws no beam
there and no section cuts it. What is the element (block header, bulkhead, other) and at what level is its underside?

Count effect for the B header: architect 12 -> 13 questions (A14 new); A02, A04, A10, A12 extended.

## 2. Duplicates (acceptance (b))

| Row | Checked against | Verdict |
|---|---|---|
| R01 / R02 | B-A12 (issue MEP, wet-room / kitchen details, finishes schedule); D-62 | B-A12 asks for sheets not issued; R01 / R02 ask what an ISSUED sheet draws: different facts, NEW A14 |
| R03 | B-A12 (wet-room details) | the same request family: added inside A12, never its own question |
| R04 | B-A04 (W17 head above beam soffit, CONFLICT); B-A02 (W17 is among the 9 printed openings); Q-32 / Q-39 / Q-76 A | different fact from A04 (a); owner rules cover the window unit only; added to A04 so W17 gets one reply |
| R05 / R06 | B-A02 / D-45 ("arch rise of 20 windows and 3 arches"; the 3 = A-GF-01 on its two faces GF-01 / GF-02 and A-1F-01, T-144) | SAME fact: named inside A02 by position, not asked twice. R06 joint with A RFI-A08 (the space beyond) |
| R07 | B-A10 (P-1F-01 head); P-GF-01 (0.90 m in GF-W14, a different opening and wall; its match to the 0.20 x 0.90 hidden pair 33C / 33D of T-368 r2 is not checked here) | different opening: added to A10 as (c) |
| all | T-376 rows R01 - R16 (reinforcement) | no overlap |

Not filed, with reason: UNK-GF-01 waterproofing (0 m2 either way, T-369 s.3); W17 head vs beam (already A04 (a)); W17
window m2 (owner Q-76 A); shower tanking height (owner Q-40 A with Q-48 A); A-GF-01 / A-1F-01 as new questions (same
fact as A02); P-GF-01 / P-1F-01 heads (other openings; P-1F-01 already in A10).

## 3. Engine vs freelancer; verdict proposals

No BOQ line moves (candidate_lines_changed 0, quantities_computed 0). Freelancer: no fixture count (lump sums), no
shower / tanking row, arched windows as width x full height (Q-32 A matches for the unit), no tile-edge row: every row
is RULE_DIFFERENCE or not comparable, no %. Verdict proposals: R01, R02, R03, R05, R06, R07 UNRESOLVED (designer);
R04 UNRESOLVED (designer), engineering reading RADIAL (T-302: the jambs are drawn radial; a straight-through soffit
would warp the room-side head from 2.17 to 1.77 m over 0.20 m), never applied without the answer.

## 4. Rule and lessons (ERS s.7)

R-RFI-BIND-1 (T-376) applied to lane A without change, plus one addition proposed for every villa (provenance T-381; a
rule version only when adopted): **a designer item that governs no current BOQ quantity is not filed as its own
question; it rides inside an existing request of the same family (here R03 inside A12), with "governs no current
quantity" stated.**

Lessons-register row (proposed): | 2026-10-31 | Two lane A holds (A-GF-01, A-1F-01) were about to be raised as new
designer questions although D-45 / B-A02 already asks "arch rise of 3 arches" without naming them | the existing
question named a count, not the openings | an RFI that asks for N items names each item by position; a new hold is
first matched by fact to every open question (scope every villa; T-381) | tests/t381_rfi_rows (same fact twice refused;
ADD_TO unknown id refused; NEW id that exists refused) | PROPOSED |

## 5. Self-gate and not done

self-gate: a (real code + 22 tests), c (synthetic villa E381 by hand: bound 0.90 x 3.00 = 2.70 m2, adverse cases), d
(research and tests files only, freeze 0), f (HELD never 0, nothing computed or released), h (every citation resolved
verbatim by the tool; line ids from the merged T-377 V3.0.27 extract) PASS. Not done: the rfi files are not edited
(Lead); the Arabic text of P7757.dxf was not pattern-searched (x-arab encoding; T-369 / T-370 read it); sanitary p.3 not
re-rendered this run (T-369 / T-370 read it at 110 / 600 dpi); whether any blockwork ledger carries the GF-14 header is a
Lead check.
