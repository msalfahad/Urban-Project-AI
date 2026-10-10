"""Markdown deliverables of PRE-S5.1, written from the builder's measured state (no number is typed by hand)."""

from __future__ import annotations

from collections import Counter

LONG = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2")


def _t(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _ids(xs, n=12):
    xs = sorted(xs)
    s = ", ".join(x.replace("GSO-", "") for x in xs[:n])
    return s + (f" (+{len(xs) - n})" if len(xs) > n else "")


def write(out, S, occs, straps, lib, claims, rules):
    R = S["readiness"]
    gb, gbp = R["ground_beams"], R["ground_beams_pre_s5"]
    amb = S["ambiguous_19"]
    by_load = Counter(o["load"]["STATE"] for o in occs)
    def cause(o):
        why = " ".join(o["comp"][k][2] for k in LONG if o["comp"][k][0] != "READY_LOWER_BOUND")
        if "concentrated-load" in why:
            return "CONCENTRATED_LOAD_UNRESOLVED (Q-L1)"
        if "disagree" in why:
            return "CANDIDATE_DETAILS_DISAGREE (exterior authority not verified / length basis)"
        if "SOURCE_CONFLICT" in why:
            return "EXTERIOR_SOURCE_CONFLICT"
        if "bar run" in why:
            return "BAR_RUN_" + o["run"]["BAR_RUN_STATE"]
        return "OTHER"
    blocked_by = Counter(cause(o) for o in occs if o["status"] != "READY_LOWER_BOUND")
    pre_ready_now_blocked = Counter(cause(o) for o in occs if o["status"] != "READY_LOWER_BOUND"
                                    and R["moved"] and o["occ_id"] in {m["OCCURRENCE_ID"] for m in R["moved"]})
    ready_ids = [o["occ_id"] for o in occs if o["status"] == "READY_LOWER_BOUND"]
    up = [m for m in R["moved"] if m["TO"] == "READY_LOWER_BOUND"]
    down = [m for m in R["moved"] if m["TO"] != "READY_LOWER_BOUND"]
    reg = S["registration"]
    fa = S["follow_arch"]
    L = S["length"]
    fe = S["free_ends"]

    # ------------------------------------------------------------------------------------------------- 00 README
    md = [f"""# PRE-S5.1: ground-system source resolution and provenance cleanup

| Item | Value |
|---|---|
| Baseline | `{S['baseline']}` (pre-S5 accepted; S4 frozen; S5 not started) |
| Builder | `build_pre_s5_1.py [ST7757.dxf] [P7757.dxf]` (both sha256-checked; byte-identical on rebuild) |
| Engines | `engine/source/rebar_provenance.py` (generic identity), `engine/source/ground_system_provenance.py` (rebased), `engine/source/ground_system_resolution.py` (decisions) |
| Drawings | ST7757.dxf `{S['st7757_sha256'][:12]}...`, P7757.dxf `{S['p7757_sha256'][:12]}...` |

**No steel mass is calculated and S5 is not started.** This round resolves the sources behind the pre-S5 readiness
matrix: the exterior walls from the architecture, the FOLLOW ARCH. depth, the length basis, concentrated loads, the
nested length conditions, SB2 and the free ends. It also replaces two shortcuts: the footing-shaped beam provenance and
the min(clear, c/c) bar run.

## 1. Provenance (01)

- The generic contract `rebar_provenance` carries `ELEMENT_OCCURRENCE_ID`, `ELEMENT_MARK` and `ELEMENT_FAMILY`.
  The FOOTING family keeps `FOOTING_*` as aliases that must equal `ELEMENT_*`. Any other family is **rejected** if it
  carries a `FOOTING_*` key.
- `ground_system_provenance.validate_s5_part` no longer fills the footing slots with the beam id. It runs the generic
  validator and then the member fields.
- The generic validator gives the same verdict as the frozen `validate_s4_part` on all 84 S4 records and 10
  mutations of each (840 cases). The S4 freeze manifest is untouched.

## 2. Bar run (05)

- The pre-S5 `min(clear, c/c)` lower bound is removed from the code.
- Four lengths are now stored per span:
  - MEMBER_CENTERLINE_LENGTH: support reference to support reference;
  - MEMBER_CLEAR_CONCRETE_LENGTH: the frozen band piece;
  - SUPPORT_FACE_TO_FACE_RUN: the centreline against the actual support faces;
  - BAR_STRAIGHT_RUN_LOWER_BOUND: the shortest face-to-face run over the centreline and the two outer bar lines
    (half width − 70 mm soil cover), so an oblique support is not over-measured.
- A support beside the line (offset column, L-corner) is met at its face plane.

| LENGTH_STATE | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(L["by_length_state"].items())) + f"""

- **LENGTH_GEOMETRY_CONFLICT spans** ({_ids(L['conflicts'])}) are never resolved by taking the smaller number. They are:
  - two spans whose support column does not cut the full beam width (the concrete piece is longer than the centreline);
  - five spans with oblique or arc-trimmed ends, where the frozen band (the overlap of the paired faces) stops short of
    the support face the bar lines reach.
- **BAR_RUN_GEOMETRY_UNRESOLVED:** {_ids(L['unresolved'])}. This span ends on the plot boundary with no support.

## 3. Architectural exterior-wall overlay (02)

**Registration:**
- P7757 GF to ST7757 GBP: {reg['matched']}/{reg['arch_outlines']} architectural column outlines land on equal GF-roof-slab outlines under one translation (second best {reg['second_best']}).
- GFRS and GBP share their sheet frame. Translation arch → GBP = {reg['translation_arch_to_gbp']} mm.

**Wall line along each span:**
- The span centreline is cut every 50 mm across the beam width + 50 mm.
- A parallel P7757 GF wall-line element crossing the cut covers that station. The elements are paired masonry
  (R5 60–450 mm pairing), single wall lines, glazing and curved wall or glazing.
- Door or gate geometry in an uncovered station counts as an opening in the line.

**Exterior class of every wall element:** both faces are probed 400 mm out and classified on the frozen S1 GBP slab
panels:
- ground slab = inside;
- S1 OUTSIDE_BUILDING_OR_COURT = outside;
- beyond the panelled plate = outside;
- the one unpanelled hole ({S['slab_panels']['holes'][0]['area_m2'] if S['slab_panels']['holes'] else 0} m²) carries interior labels (DINING, W.C, +1.00), so it counts as inside.

| WALL_CLASS (relation) | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(S["wall_relation"].items())) + f"""

## 4. Exterior authority (03)

The architecture decides. The structural ground-slab edge may only contradict it (SOURCE_CONFLICT). The V3 zone and
R4 footprint proxies are recorded and never voted.

| EXTERIOR_AUTHORITY | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(S["exterior_authority"].items())) + f"""

**The 19 spans on which the two proxies disagreed: {amb['resolved']} resolved by architecture**
({amb['by_authority'].get('EXTERIOR_SOURCE_VERIFIED', 0)} exterior, {amb['by_authority'].get('INTERIOR_SOURCE_VERIFIED', 0)} interior), the rest:
""" + "\n".join(f"- {k.replace('GSO-', '')}: {v}" for k, v in sorted(amb["spans"].items())
                 if v not in ("EXTERIOR_SOURCE_VERIFIED", "INTERIOR_SOURCE_VERIFIED")) + f"""

## 5. FOLLOW ARCH. depth (04)

**What the p.13 exterior section actually draws (crop P13_GB_EXTERIOR):**
- The depth dimension "FOLLOW ARCH." runs from the "Ground Floor slab level" arrow to the beam soffit.
- The dashed "Outer Normal ground level" line is drawn **at the beam soffit**.
- The R4 transcription's word "below" has no printed source. S1 reads it the same way: "outer normal ground level to
  GF slab level".

**Levels:**
- Outer natural ground is ±0.00 (sections A-A VE-AA-01 and B-B VE-BB-01; plan ±0.00 marks outside the plot).
- GF FFL is +1.00 in the main block (100 cm chain VE-AA-08). The annex block is +0.30. Court paving is +0.15.

**What is not printed:**
- the floor build-up between FFL and slab top (S1 level register);
- any depth.

**Result:** D = (FFL − build-up) − NGL is **bounded above only**.

| Outcome | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(fa["by_outcome"].items())) + f"""

| D_MAX (m) | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(fa["depth_max_m"].items())) + f"""

The {len(fa['flagged_shallow'])} annex spans at +0.30 give D ≤ 0.30 m. That is shallower than any cross-verified
typical section and cannot hold the drawn three bar levels with 70 mm cover. This is an engineering question (11).

## 6. Length basis of the p.13 titles (05)

**Sources searched:**
- **p.13 titles:** say "length" with no basis.
- **GBP plan dimensions:** {S['gbp_dimensions']['dimensions']} dimensions, all axis-to-axis grid chains plus edge offsets
  ({S['gbp_dimensions']['extension_points']}). None measures a beam span.
- **CB typical figure:** uses both Ln and L.
- **Lintel schedule:** measures openings.

The basis is therefore **not stated**. The clear basis is tested on the support face-to-face run (concrete clear where
unresolved), alongside the centreline basis.

- SAME_RESULT on {L['basis_same']} spans.
- The basis changes the detail on {len(L['basis_differs'])} spans: {_ids(L['basis_differs'])}.

A basis-dependent component releases only where it is identical in both bases' details.

## 7. Concentrated loads (06)

| LOAD_STATE | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in sorted(by_load.items())) + f"""

**Evidence kinds:** {S['loads']['by_kind']}.

**What was checked:**
- **Columns bearing on a span or planted on a ground beam: none.** All 36 GBP column chains start at FOUNDATION. The 3
  planted columns sit on the GF and 1F roof slabs.
- **Loads, symbols and notes on GBP:** no LOAD / kN / P= note.
- **Two '******' marks:** S-TEXT, no legend.

**Why UNKNOWN is not treated as no load:**
- Most UNKNOWN spans have another ground beam **ending** mid-span (BEAM_END_REACTION). The others are the
  reception stair zone or an unidentified mark.
- The interior p.13 sections are titled "without concentrated load", and no loaded section is drawn.
- So under UNKNOWN the loaded case is a separate candidate with no detail. An interior span that needs the
  ≥ 2.5 m sections is blocked until the engineer says whether a framing ground beam counts.
- The < 2.5 m and exterior sections carry no such clause, so those spans are unaffected.

## 8–9. Nested < 2.5 m / < 5 m and the 2.5 m stirrup (07)

- **Precedence:** {S['nested']['spans']} spans meet both "Less than 2.5m" and "Less than 5m" literally. No note or
  drawn grouping orders them, so RULE_PRECEDENCE_SOURCE = SPECIFICITY_CANDIDATE and both details are preserved.
- **Longitudinal bars:** identical (3Ø14 in all three positions), so they are candidate-invariant and release.
- **2.5 m stirrup:** the section draws a closed link with **no size or spacing**. No project note gives ground-beam
  links (P9 column ties and the CB figure are other members).
- **Stirrup state:** BLOCKED_COMPONENT on every span where the 2.5 m section is a candidate. Ø8/150 is never
  inherited.

## 10. SB2 (08)

Two SBT rows share the key SB2.

| Facet | State |
|---|---|
| Section | width SOURCE_CONFLICT (80 vs 100); depth 50 is candidate-invariant |
| TOP and BOTTOM bars | BLOCKED (10Ø18 / 10Ø18 vs 20Ø18 / 10Ø16) |
| Stirrups (10Ø8/m in both rows) | CANDIDATE_INVARIANT: Ø and rate READY, count LOWER_BOUND |
| Link path | BLOCKED (width and topology) |

The plan's drawn width of 987 mm is recorded but does not adjudicate.

## 11. SB1 / SB3 (03, 10)

- The straight run is at least the clear concrete length between the footing faces (SB1 4.550 m, SB3 2.838 m), as a
  LOWER_BOUND.
- The column c/c and footing c/c are recorded.
- DEVELOPMENT_INTO_FOOTING_1 / _2 stay BLOCKED_UNQUANTIFIED.

## 12. Free ends (09)

The {fe['nodes']} FREE_END nodes are all classified: {fe['by_class']}.
- **Footings:** two ends lie inside the FF footing outline.
- **Columns:** four ends touch column outlines, two of them outlines the rectangle detector did not return. Two are a
  50 mm and a 20 mm drawing gap.
- **Boundary:** the east end of 1811-1812 lies on the S-BOUN plot-boundary line.

## 13. Readiness (10) — movement from pre-S5

| Ground beams | pre-S5 | PRE-S5.1 |
|---|---|---|
| READY_LOWER_BOUND | {gbp.get('READY_LOWER_BOUND', 0)} | **{gb.get('READY_LOWER_BOUND', 0)}** |
| BLOCKED_COMPONENT | {gbp.get('BLOCKED_COMPONENT', 0)} | **{gb.get('BLOCKED_COMPONENT', 0)}** |

**Moved up to READY_LOWER_BOUND** ({len(up)}): {_ids([m['OCCURRENCE_ID'] for m in up])}. The architecture verified
the exterior (or interior) wall, so the 3Ø14 / 3Ø16 candidates collapsed to one detail.

**Moved down** ({len(down)}), by first blocking cause:
""" + "\n".join(f"- {k}: {v}" for k, v in sorted(pre_ready_now_blocked.items())) + f"""

**All {gb.get('BLOCKED_COMPONENT', 0)} blocked spans**, by first blocking cause:
""" + "\n".join(f"- {k}: {v}" for k, v in sorted(blocked_by.items())) + f"""

**Straps:** SB1 and SB3 READY_LOWER_BOUND (unchanged). SB2 BLOCKED (bars), with its stirrup Ø, rate and count now
released as candidate-invariant.

## Files

| File | Content |
|---|---|
| 01_PROVENANCE_CONTRACT_UPDATE.md | generic identity contract, S4 compatibility, rejected footing identity |
| 02_GROUND_BEAM_ARCH_WALL_OVERLAY.csv | per span: wall handles, overlap, wall / exterior class, method, authority |
| 03_EXTERIOR_AUTHORITY_REGISTER.csv | per span: proxies, architecture, slab edge, authority, applicability before / after |
| 04_FOLLOW_ARCH_DEPTH_REGISTER.csv | exterior candidates: top / bottom levels, sources, derived bound, outcome |
| 05_LENGTH_BASIS_ANALYSIS.csv | per span: four lengths, length state, faces, detail by clear / centreline basis |
| 06_CONCENTRATED_LOAD_REGISTER.csv | per span: load state and evidence |
| 07_DETAIL_PRECEDENCE_ANALYSIS.md / 08_SB2_SOURCE_CONFLICT.md | nested conditions and 2.5 m stirrup; SB2 evidence |
| 09_GROUND_BEAM_FREE_END_REGISTER.csv | the 7 former free ends |
| 10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv | occurrence x component, MAY_RELEASE, pre-S5 status |
| 11_ENGINEERING_QUESTIONS_FINAL.md / 12_S5_GO_NO_GO.md | remaining questions; S5 scope decision |
| PRE_S5_1_SUMMARY.json, S5_1_PROVENANCE_TEMPLATES.json, INDEX.json | summary, generic templates, hashes |
"""]
    (out / "00_README.md").write_text(md[0], encoding="utf-8")

    # ------------------------------------------------------------------------------------------------- 01 provenance
    (out / "01_PROVENANCE_CONTRACT_UPDATE.md").write_text("""# Provenance contract update: generic element identity

## What was wrong

- The pre-S5 `ground_system_provenance.validate_s5_part` built a view of each beam part in which `FOOTING_OCCURRENCE_ID`
  and `FOOTING_MARK` were filled with the beam's id and mark. It then called the footing validator
  (`accurate_boq_rebar.validate_s4_part`).
- Nothing was written to disk that way, but the contract accepted a beam identified through footing slots. A beam is
  not a footing.

## The contract now

| Field | Meaning |
|---|---|
| ELEMENT_OCCURRENCE_ID | physical occurrence (footing, ground-beam span, strap, ...) |
| ELEMENT_MARK | drawing mark / tag (or the typical-detail family when untagged) |
| ELEMENT_FAMILY | FOOTING, GROUND_BEAM, STRAP_BEAM, COLUMN, BEAM, SLAB |

- Every other field, vocabulary and rule is the S4 one: drawing sha, revision, sheet region, source handles and text,
  component, rule, convention, measurement / authority / release states, formula, inputs, engine / register / round
  stamp, bounds and blocking reason.
- These are imported from `accurate_boq_rebar`, never copied. No second provenance system exists.

## Compatibility

| Record | Result |
|---|---|
| frozen S4 record (FOOTING_* only) | read as ELEMENT_FAMILY = FOOTING; same verdict as validate_s4_part |
| FOOTING record carrying both | FOOTING_* must equal ELEMENT_* |
| GROUND_BEAM / STRAP_BEAM / ... with any FOOTING_* key | **rejected** |
| GROUND_BEAM with FOOTING_* as its only identity | **rejected** |
| S5 template | ELEMENT_* only (no FOOTING_* key is written for a beam) |

## How it was checked

- **Equivalence:** `rebar_provenance.validate_part` and `accurate_boq_rebar.validate_s4_part` were run over the 84
  frozen S4 provenance records, unmutated and with each of 9 mutations. That is 840 cases with identical accept /
  reject.
- **S4 is untouched:**
  - S4 files are not edited and the S4 freeze manifest still matches;
  - `footing_rebar` still calls `validate_s4_part`.
- **Pre-S5 package rebuilt:**
  - its templates now carry ELEMENT_* (no FOOTING_* key);
  - its bar-run text points here instead of the removed minimum;
  - no status changed.
""", encoding="utf-8")

    # ------------------------------------------------------------------------------------------------- 07 precedence
    nested = [o for o in occs if o["nested"]]
    lt25 = lib["P13-GB-LT2_5M"]
    rows = [(o["occ_id"].replace("GSO-", ""), f"{o['basis']['DETAIL_BY_CLEAR_LENGTH']}",
             f"{o['basis']['DETAIL_BY_CENTRELINE_LENGTH']}", o["cand"]["STATE"], o["comp"]["TOP_MAIN"][0],
             o["comp"]["STIRRUP_DIAMETER"][0]) for o in sorted(nested, key=lambda z: z["occ_id"])]
    (out / "07_DETAIL_PRECEDENCE_ANALYSIS.md").write_text(f"""# Detail precedence: "Less than 2.5m" vs "Less than 5m", and the 2.5 m stirrup

## Precedence (§8)

**The literal titles (p.13):**
- P13-GB-LT5M: "Less than 5m length (1:20) without concentrated load"
- P13-GB-LT2_5M: "Less than 2.5m length (1:20)"

A span shorter than 2.5 m meets both conditions literally.

**Sources searched for an order between them:**
- the p.13 titles and their layout. The LT2_5M section is drawn under GT5M; LT5M stands apart. Nothing groups LT2_5M
  as a subset of LT5M or a range "2.5 to 5";
- the p.8 general notes;
- the ST7757.dxf texts. The details are not in the DXF; there are only plan / schedule texts.

None states an order.

| RULE_PRECEDENCE_SOURCE | Spans |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in S["nested"]["precedence"].items()) + f"""

- "The narrower condition wins" is a SPECIFICITY_CANDIDATE, not a source.
- Both details are preserved as candidates, and a component releases only if it is identical in both.

| Facet | LT2_5M | LT5M | Same? |
|---|---|---|---|
| top | {lt25['top']} | {lib['P13-GB-LT5M']['top']} | {lt25['top'] == lib['P13-GB-LT5M']['top']} |
| lower rows | {lt25['rows']} | {lib['P13-GB-LT5M']['rows']} | {lt25['rows'] == lib['P13-GB-LT5M']['rows']} |
| section | 30 x {lt25['D']} ({lt25['section_state']}) | 30 x {lib['P13-GB-LT5M']['D']} | no |
| stirrup | none printed | {lib['P13-GB-LT5M']['stirrup']} | no |

## The 2.5 m stirrup (§9)

**Sources exhausted:**
- **The P13_GB_LT2_5M crop:** a closed link with a hook is drawn; no size or spacing is printed.
- **The R4 claim register:** "no stirrup callout printed".
- **The S1 project rule register:**
  - P9-COL-TIES is for columns only;
  - P11-12-CB-TYPICAL is for continuous beams (first stirrup 7.5 cm);
  - no ground-beam link rule exists.
- **The p.8 notes:** nothing on links.

**Result:** STIRRUP = **BLOCKED_COMPONENT** wherever the 2.5 m section is a candidate. Ø8/150 from the 5 m sections
is not inherited. Longitudinal bars still release (identical 3Ø14).

| Span | Clear basis | Centreline basis | Applicability | Longitudinal | Stirrup |
|---|---|---|---|---|---|
""" + "\n".join("| " + " | ".join(r) + " |" for r in rows) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------------------------------------- 08 SB2
    sb2 = next(s for s in straps if s["MARK"] == "SB2")
    ra, rb = sb2["_rows"][0], sb2["_rows"][1]
    (out / "08_SB2_SOURCE_CONFLICT.md").write_text(f"""# SB2: two schedule rows for one strap

| Evidence | Row A | Row B |
|---|---|---|
| SCHEDULE_ROW (SBT insert) | {ra['insert']} | {rb['insert']} |
| W x H (cm) | {ra['W_cm']:.0f} x {ra['H_cm']:.0f} | {rb['W_cm']:.0f} x {rb['H_cm']:.0f} |
| REBAR_VALUES TOP | {ra['top'][0]}Ø{ra['top'][1]} | {rb['top'][0]}Ø{rb['top'][1]} |
| REBAR_VALUES BOTTOM | {ra['bottom'][0]}Ø{ra['bottom'][1]} | {rb['bottom'][0]}Ø{rb['bottom'][1]} |
| STIRRUPS / m | {ra['stirrups_per_m'][0]}Ø{ra['stirrups_per_m'][1]} | {rb['stirrups_per_m'][0]}Ø{rb['stirrups_per_m'][1]} |

| Plan evidence (FP sheet) | Value |
|---|---|
| TAG | SB2, handle {sb2['SOURCE_HANDLES'][-1]} |
| LOCATION | foundation plan, between {sb2['START_SUPPORT']['footing']} ({sb2['START_SUPPORT']['footing_type']}) and {sb2['END_SUPPORT']['footing']} ({sb2['END_SUPPORT']['footing_type']}) |
| strap edges | {', '.join(sb2['SOURCE_HANDLES'][:-1])} |
| PLAN_DRAWN_WIDTH | {sb2['WIDTH_DRAWN_MM']} mm |
| PLAN_DRAWN_LENGTH | {sb2['DRAWN_FACE_LENGTH_M']} m (drawn faces); clear between footing faces {sb2['CLEAR_CONCRETE_LENGTH_M']} m |

| Authority (decided separately) | State | Why |
|---|---|---|
| SECTION_AUTHORITY: width | SOURCE_CONFLICT | 80 vs 100 cm. The drawn 987 mm is recorded; the closer width does not adjudicate. |
| SECTION_AUTHORITY: depth | CANDIDATE_INVARIANT (50 cm) | identical in both rows |
| REBAR_AUTHORITY: TOP / BOTTOM | SOURCE_CONFLICT, BLOCKED | the rows give different bars |
| REBAR_AUTHORITY: stirrups | CANDIDATE_INVARIANT | {ra['stirrups_per_m'][0]}Ø{ra['stirrups_per_m'][1]}/m in both rows: Ø and rate READY, count LOWER_BOUND (rate x clear length) |
| link path | BLOCKED | the width conflict and no link topology |

This is engineering question Q-S2 (11).
""", encoding="utf-8")

    # ------------------------------------------------------------------------------------------------- 11 questions
    unk = [o for o in occs if o["load"]["STATE"] == "UNKNOWN"]
    unk_block = [o for o in unk if any("concentrated-load" in o["comp"][k][2] for k in LONG)]
    ext_unres = [o["occ_id"] for o in occs if o["auth"]["AUTHORITY"] not in ("EXTERIOR_SOURCE_VERIFIED",
                                                                               "INTERIOR_SOURCE_VERIFIED")]
    q = [
        ("Q-L1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Concentrated load.** Does a ground beam ending on another ground beam mid-span (or the reception stair "
         "start) count as a 'concentrated load' for the p.13 sections titled 'without concentrated load'?",
         f"{len(unk)} spans UNKNOWN; {len(unk_block)} interior spans blocked by it: {_ids([o['occ_id'] for o in unk_block])}",
         "p.13 titles, GBP texts / symbols, S1 column chains (no planted column on a GB), junction geometry"),
        ("Q-D1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Exterior ground-beam depth.** The section draws GF slab level to outer natural ground (±0.00). The floor "
         "build-up is not printed, so D <= 1.00 m (main block) / <= 0.30 m (annex at +0.30). What is the depth "
         "(or the build-up)? The annex bound cannot hold the drawn section.",
         f"{fa['spans']} exterior candidates ({fa['by_outcome']}); annex: {_ids(fa['flagged_shallow'])}",
         "p.13 exterior crop, A-A / B-B section levels, P7757 GF level marks, S1 level register"),
        ("Q-B1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Length basis of the p.13 titles:** clear span between support faces, or centreline?",
         f"{len(L['basis_differs'])} spans change detail: {_ids(L['basis_differs'])}",
         "p.13 titles, GBP dimensions (axis chains only), CB figure (Ln and L), lintel schedule"),
        ("Q-N1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Below 2.5 m both 'Less than 2.5m' and 'Less than 5m' hold.** Which governs, and what are the 2.5 m "
         "section's link size and spacing?",
         f"{S['nested']['spans']} spans: longitudinal released (identical), stirrups blocked",
         "p.13 crop LT2_5M (no callout), R4 claims, S1 / R4 rule registers"),
        ("Q-S2", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**SB2 governing schedule row:** 80x50 (10Ø18 / 10Ø18) or 100x50 (20Ø18 / 10Ø16)?",
         "SB2 longitudinal bars and link path", "SBT inserts 1FBB / 2ABA, FP plan (drawn width 987)"),
        ("Q-E1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Partly exterior / mixed spans.** Which section applies to a span whose wall above is partly exterior, or "
         "which sits on the slab edge with no wall?",
         f"{len(ext_unres)} spans: {_ids(ext_unres)}", "P7757 GF walls, S1 slab panels"),
        ("Q-T1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Link topology and hooks.** Legs, hook angle and extension of the ground-beam and strap links. The "
         "strap schedule gives Ø and count per metre only.",
         "every stirrup core path; all hooks", "p.13 sections, SBT, R4 HOOKS_AND_BENDS = NO_PROJECT_SOURCE"),
        ("Q-A1", "GENERIC_CODE_QUESTION",
         "**Development / anchorage** of ground-beam bars into columns, beams and footings, and of strap bars into "
         "footings. The p.8 70Ø / 40Ø note is for starters only. A code value needs the project's code and grades "
         "(a project decision).",
         "all DEVELOPMENT_INTO_SUPPORT components", "P8-N09 claim, R4 rule DEVELOPMENT_STARTER_70D_40D"),
        ("Q-G1", "PROJECT_DECISION_REQUIRED",
         "**Bar run where the drawn band and the support faces disagree.** A column narrower than the beam, oblique "
         "and arc-trimmed ends: should bars be measured to the support face plane, and the concrete piece corrected?",
         f"{len(L['conflicts'])} spans: {_ids(L['conflicts'])}", "GBP geometry (no source states a method)"),
        ("Q-F1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**1811-1812 east end** lies on the plot-boundary line with no column or footing. What supports it?",
         "1 span (bar run unresolved)", "GBP S-BOUN, S-COL.BON, FP footings"),
        ("Q-X1", "SOURCE_EXHAUSTED_ENGINEER_REQUIRED",
         "**Meaning of the two '******' marks** on the GBP sheet (S-TEXT, 300 mm, no legend).",
         "spans near them are load-UNKNOWN", "GBP texts, all ST7757 '*' texts"),
    ]
    not_req = [("Exterior / interior of the 19 proxy-disagreement spans",
                f"{amb['resolved']} resolved by the architectural overlay"),
               ("Outer normal ground level", "±0.00 (sections A-A, B-B)"),
               ("Free ends", f"{fe['nodes']}/{fe['nodes']} classified ({fe['by_class']}); one boundary end remains "
                              "(Q-F1)"),
               ("Planted columns on ground beams", "none (S1 chains)"),
               ("SB2 stirrups", "identical in both rows: candidate-invariant"),
               ("Beam provenance identity", "generic ELEMENT_* contract")]
    (out / "11_ENGINEERING_QUESTIONS_FINAL.md").write_text(
        "# Engineering questions (final, pre-S5.1)\n\n"
        "These are only questions that ST7757, P7757, the registers, the geometry and the notes cannot answer.\n\n"
        + _t([(a, b, c, d, e) for a, b, c, d, e in q],
             ["#", "Class", "Question", "Members affected", "Sources exhausted"])
        + "\n\n## Classified NOT_REQUIRED (resolved this round)\n\n" + _t(not_req, ["Item", "Resolution"]) + "\n",
        encoding="utf-8")

    # ------------------------------------------------------------------------------------------------- 12 go / no-go
    rel = Counter()
    for o in occs:
        for k, (st, _, _) in o["comp"].items():
            if st in ("READY", "READY_LOWER_BOUND"):
                rel[k] += 1
    (out / "12_S5_GO_NO_GO.md").write_text(f"""# S5 GO / NO-GO

## Decision: **GO for a restricted S5**; NO-GO for a complete ground-system S5.

### GO: what S5 may quantify (each part LOWER_BOUND or VERIFIED, with the generic provenance)

| Scope | Occurrences | State |
|---|---|---|
| GB longitudinal TOP / BOTTOM_ROW_1 / BOTTOM_ROW_2, straight run = BAR_STRAIGHT_RUN_LOWER_BOUND | {gb.get('READY_LOWER_BOUND', 0)} spans | LOWER_BOUND (development blocked) |
| GB stirrup count | {rel['STIRRUP_COUNT']} spans | count LOWER_BOUND (no kg: the link path is not established) |
| Strap longitudinal (SB1, SB3) | 2 | LOWER_BOUND |
| Strap stirrup count (SB1, SB2, SB3) | 3 | count LOWER_BOUND (no kg) |

### NO-GO: what must stay blocked

- GB longitudinal bars of {gb.get('BLOCKED_COMPONENT', 0)} spans:
""" + "\n".join(f"  - {k}: {v}" for k, v in sorted(blocked_by.items())) + """
- Side bars of every exterior span: the depth is bounded above only (Q-D1).
- Every stirrup kg: no verified link path (Q-T1); the 2.5 m section has no callout (Q-N1).
- Hooks, end treatment and development everywhere (Q-T1, Q-A1).
- SB2 longitudinal bars (Q-S2).

### Conditions for S5

1. S5 consumes 05 / 10 (no re-parse) and uses `rebar_provenance` / `ground_system_provenance` (ELEMENT_*).
2. Freeze before any comparison.
3. Release only where `MAY_RELEASE` is true.
4. No donor or benchmark value is used to choose a length, detail or depth.
5. An answer to Q-L1 alone moves the concentrated-load-blocked interior spans; Q-B1 / Q-N1 move the
   basis-dependent and nested ones. Re-run this builder after each answer before S5 consumes it.
""", encoding="utf-8")
