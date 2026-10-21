"""PRE-S6 documents (00 README, 11 questions, 12 S6 scope), written from the builder's own rows so every number in
them is the number in the registers. No kg is computed or printed."""

from __future__ import annotations

from collections import Counter

RELEASED = ("READY", "READY_LOWER_BOUND")


def _n(rows, **kw):
    return sum(1 for r in rows if all((r.get(k) in v) if isinstance(v, tuple) else r.get(k) == v
                                      for k, v in kw.items()))


def _occ(rows, sub):
    st = {}
    for r in rows:
        if r["SUBFAMILY"] == sub:
            st[r["OCCURRENCE_ID"]] = r["OCCURRENCE_STATUS"]
    return Counter(st.values()), len(st)


def _table(head, body):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(out)


def _comp_table(ready, sub, fams):
    sts = ["READY", "READY_LOWER_BOUND", "PROVISIONAL_ONLY", "SOURCE_CONFLICT", "BLOCKED_COMPONENT",
           "NO_APPLICABLE_DETAIL", "NOT_APPLICABLE"]
    body = []
    for f in fams:
        c = Counter(r["STATUS"] for r in ready if r["SUBFAMILY"] == sub and r["COMPONENT_FAMILY"] == f)
        if c:
            body.append([f] + [c.get(s, 0) or "" for s in sts])
    return _table(["Component"] + sts, body)


def write(here, summary, ready, runs, spans, side, openings, tags, geo, heads, cb_occ):
    s_occ, s_n = _occ(ready, "SIMPLE_BEAM")
    c_occ, c_n = _occ(ready, "CONTINUOUS_BEAM")
    t = Counter(r["TERMINAL"] for r in tags)
    g = Counter((r["OBJECT_KIND"], r["TERMINAL"]) for r in geo)
    untag = [r for r in geo if r["TERMINAL"] == "GEOMETRY_WITHOUT_TAG"]
    untag_new = [r for r in untag if not r.get("S1_ROW_PRESENT")]
    seq = Counter(o["seq"]["state"] for o in cb_occ)
    orient = Counter(o["seq"]["orientation"] for o in cb_occ)
    simple_rel = _n(ready, SUBFAMILY="SIMPLE_BEAM", COMPONENT_FAMILY="BOTTOM_MAIN", STATUS="READY_LOWER_BOUND")
    cb_bottom = Counter(r["STATUS"] for r in ready if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and
                        r["COMPONENT_FAMILY"] == "BOTTOM")
    cb_mid = Counter(r["STATUS"] for r in ready if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and
                     r["COMPONENT_FAMILY"] == "MID_SUPPORT_TOP")
    cb_top = Counter(r["STATUS"] for r in ready if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and r["COMPONENT_FAMILY"] == "TOP")
    st_cnt = Counter((r["SUBFAMILY"], r["STATUS"]) for r in ready if r["COMPONENT_FAMILY"] == "STIRRUP_COUNT")
    st_mass = _n(ready, COMPONENT_FAMILY="STIRRUP_MASS")
    side_occ = Counter((r["SUBFAMILY"], r["STATUS"]) for r in ready if r["COMPONENT_FAMILY"] == "SIDE_REBAR")
    open_st = Counter(r["OPENING_STATE"] for r in openings)
    open_kind = Counter(r["OUTLINE_KIND"] for r in openings)
    rules = [(h["id"], h["spans"], r) for h in heads for r in h["rules"]]
    bound = [x for x in rules if x[2]["state"] in ("SOURCE_EXPLICIT", "SOURCE_DERIVED_HIGH_CONFIDENCE")]
    unres = [x for x in rules if x not in bound]
    cand = summary["candidate_tags"]
    changes = summary["s1_binding_changes"]
    prov = summary["provenance_templates"]
    cb_ids = {o["id"]: o for o in cb_occ}
    amb = sorted(i for i, o in cb_ids.items() if o["seq"]["orientation"] == "AMBIGUOUS")
    lconf = sorted(i for i, o in cb_ids.items() if o["seq"]["state"] == "SPAN_LENGTH_SOURCE_CONFLICT")
    cconf = sorted(i for i, o in cb_ids.items() if o["seq"]["state"] == "SPAN_COUNT_CONFLICT")
    rev = sorted(i for i, o in cb_ids.items() if o["seq"]["orientation"] == "REVERSED")
    long_lb = _n(ready, COMPONENT_FAMILY=("BOTTOM_MAIN", "TOP_MAIN", "BOTTOM"), STATUS="READY_LOWER_BOUND")
    simple_long = _n(ready, SUBFAMILY="SIMPLE_BEAM", COMPONENT_FAMILY=("BOTTOM_MAIN", "TOP_MAIN"),
                     STATUS="READY_LOWER_BOUND")
    curved = [r["OCCURRENCE_ID"] for r in ready if r["SUBFAMILY"] == "SIMPLE_BEAM" and
              r["COMPONENT_FAMILY"] == "BOTTOM_MAIN" and str(r["GEOMETRY_OBJECT"]).startswith("ARC:")]
    stair = sorted({r["OCCURRENCE_ID"] for r in ready if r["COMPONENT_FAMILY"] == "STAIR_EXTRA"})
    planted = sorted({r["OCCURRENCE_ID"] for r in ready if r["COMPONENT_FAMILY"] == "PLANTED_COLUMN_EXTRA"})
    free = [r["OCCURRENCE_ID"] for r in ready if r["SUBFAMILY"] == "SIMPLE_BEAM" and
            r["COMPONENT_FAMILY"] == "BOTTOM_MAIN" and r["RUN_STATE"] == "BLOCKED_UNQUANTIFIED" and
            not str(r["GEOMETRY_OBJECT"]).startswith("ARC:") and r["APPLICABILITY_STATE"] == "OK"]
    widths = summary["width_conflicts"]

    unres_txt = "\n".join(f"   - {h} ({n}-span) {r['dim']} '{r['text']}': {r.get('why') or r['state']}"
                          for h, n, r in unres)
    # ------------------------------------------------------------------------------------------------ 00 README
    readme = f"""# PRE-S6: superstructure beam rebar readiness (simple + continuous beams)

**No kg is calculated in this round.** S5 is frozen and was not reopened; the S4 / S5 manifests are untouched.

```
python3 -I research/pre_s6_superstructure_beam_readiness/build_pre_s6.py
```

The builder reads ST7757.dxf (sha256-checked) through the S1 lab census, the R3 continuous-beam frame parser and the
schedule reader V2, plus the frozen S1 registers (checked against the S1 INDEX) and the R4 rule / visual-claim
registers. No other package, reference quantity or old total is opened. Every decision is made by
`engine/source/beam_rebar_readiness.py`.

## Results

| | Count | State |
|---|---|---|
| Beam tags (GF / 1F / 2F roof) | {sum(t.values())} | {t.get('BOUND_VERIFIED', 0)} BOUND_VERIFIED, {t.get('BOUND_CANDIDATE', 0)} BOUND_CANDIDATE, {t.get('BOUND_SOURCE_CONFLICT', 0)} BOUND_SOURCE_CONFLICT, {t.get('DUPLICATE_TAG', 0)} DUPLICATE_TAG, {t.get('BLOCKED_BINDING', 0) + t.get('TAG_WITHOUT_GEOMETRY', 0)} unbound |
| Member spans | {sum(v for (k, _), v in g.items() if k == 'MEMBER_SPAN')} | {g.get(('MEMBER_SPAN', 'BOUND_VERIFIED'), 0)} verified, {g.get(('MEMBER_SPAN', 'BOUND_CANDIDATE'), 0)} candidate, {g.get(('MEMBER_SPAN', 'BOUND_SOURCE_CONFLICT'), 0)} conflict, {g.get(('MEMBER_SPAN', 'GEOMETRY_WITHOUT_TAG'), 0)} without tag |
| Arc bands | {sum(v for (k, _), v in g.items() if k == 'ARC_BAND')} | {g.get(('ARC_BAND', 'BOUND_VERIFIED'), 0)} verified, {g.get(('ARC_BAND', 'GEOMETRY_WITHOUT_TAG'), 0)} without tag |
| Short band fragments | {g.get(('BAND_FRAGMENT', 'NOT_BEAM'), 0)} | NOT_BEAM |
| Rule populations (lintels, lift ties) | {summary['conservation']['by_kind_terminal'].get('RULE_POPULATION', {}).get('OUT_OF_SCOPE_FAMILY', 0)} | OUT_OF_SCOPE_FAMILY |
| Simple-beam occurrences | {s_n} | {s_occ.get('LOWER_BOUND', 0)} LOWER_BOUND, {s_occ.get('BLOCKED', 0)} BLOCKED, {s_occ.get('READY', 0)} READY |
| Continuous-beam occurrences | {c_n} | {c_occ.get('LOWER_BOUND', 0)} LOWER_BOUND, {c_occ.get('BLOCKED', 0)} BLOCKED, {c_occ.get('READY', 0)} READY |
| Untagged geometry | {len(untag)} | NO_APPLICABLE_DETAIL ({len(untag_new)} of them were silently dropped by S1 and now terminate) |

Every tag, span, arc band, fragment and rule population terminates exactly once
({summary['conservation']['objects']} objects, {summary['s1_rows_mapped']} S1 superstructure rows mapped, {len(summary['s1_rows_unmapped'])} unmapped).

### Simple beams (component families)

{_comp_table(ready, 'SIMPLE_BEAM', ['BOTTOM_MAIN', 'TOP_MAIN', 'TOP_SUPPORT_EXTRA', 'BOTTOM_EXTRA', 'HANGER', 'SIDE_REBAR', 'STIRRUP_COUNT', 'STIRRUP_MASS', 'DEVELOPMENT_ANCHORAGE', 'HOOKS', 'OPENING_EXTRA', 'PLANTED_COLUMN_EXTRA', 'STAIR_EXTRA'])}

### Continuous beams (component families; one row per bar run / span)

{_comp_table(ready, 'CONTINUOUS_BEAM', ['BOTTOM', 'MID_SUPPORT_TOP', 'TOP', 'LONGITUDINAL', 'HANGER', 'SIDE_REBAR', 'STIRRUP_COUNT', 'STIRRUP_MASS', 'DEVELOPMENT_ANCHORAGE', 'HOOKS', 'OPENING_EXTRA'])}

## What was established

1. **Binding.** One evidence ladder for every tag against every band / arc band in reach: extent, distance window,
   span already claimed by another mark, orientation, schedule width, same-mark continuity. Distance never ranks;
   text rotation alone never verifies (an alternative excluded only by rotation leaves the tag a CANDIDATE, unless the
   tag lies off that member's end or that member already carries the same mark). Claims are iterated to a fixed point
   (GFRS {summary['binding_fixed_point_passes']['GFRS']} passes, FFRS {summary['binding_fixed_point_passes']['FFRS']}, SFRS {summary['binding_fixed_point_passes']['SFRS']}).
   Changes against S1: {'; '.join(f"{c[0]} {c[1]} {c[2] or ''} -> {c[3]} {c[4]}" for c in changes)}.
2. **Width.** {len(widths)} marks have a drawn width that conflicts with the schedule ({', '.join(f'{a} {b}' for a, b in widths)}). The geometry stays
   known; the type-specific rebar is SOURCE_CONFLICT.
3. **T/M-n** are design line loads: the unit ' t/m' is printed beside every value on the frame's load line
   (SOURCE_EXPLICIT, NOT_REBAR). They never feed S6.
4. **CB spans.** Sequence states: {dict(seq)}; reading direction: {dict(orient)}. {', '.join(rev) or 'none'} match only
   when read right to left (plan spans re-ordered into schedule order). {', '.join(amb) or 'none'} match in both directions (the span-to-schedule mapping is not
   decided; only candidate-invariant families release). Length conflicts keep both values: {', '.join(lconf) or 'none'};
   count conflicts: {', '.join(cconf) or 'none'}.
5. **CB typical headers.** Each parametric dimension was bound by its defpoints ({len(bound)} bound, {len(unres)} unresolved).
   In this drawing `L*` are face-to-face spans and `Ln*` are axis-to-axis spans (both from the dimensions themselves).
   MID support bars: 0.22 x Ln of each adjacent span from the support face (bound in all three typicals). End-span bottom
   bars: 7.5 cm beyond the far face of the interior support. The left end top bar of every typical is not
   dimensioned. Unresolved dimensions:
{unres_txt}
6. **MID bars** with a printed count, a template-shaped frame bar and both sides bound are VERIFIED complete bars
   ({cb_mid.get('READY', 0)} READY). An edited frame bar (CB3 support 1) or an empty schedule cell (CB3 MID2, CB8 MID1) stays
   blocked; a known count with no bound extent is BLOCKED_UNQUANTIFIED, never given a length.
7. **Bottom bars of CB** are one bar run per frame bar, crossing their supports once ({cb_bottom.get('READY_LOWER_BOUND', 0)}
   READY_LOWER_BOUND): clear span + support width + bound extension; end anchorage stays blocked.
8. **CB top bars** stay blocked ({sum(cb_top.values())} runs): the frames draw one top bar per span from the end support, the
   typical draws an end bar plus a second lapping row; no extent rule binds to the frame bar.
9. **Hangers.** SBT: no hanger field or detail (TOP BARS exist; their hanger role is not asserted). CB: the typical
   draws an unlabelled second top row - no count / diameter / extent, so HANGER is blocked, never invented.
10. **Simple beams.** SBT 'BOTTOM BARS' / 'TOP BARS' run support face to support face as the straight run (VERIFIED),
    development and hooks separate and blocked, so the complete bar is a LOWER_BOUND ({simple_rel} occurrences). The
    straight portion is not demoted. Curved ring beams ({len(curved)}), the cantilever, stair-qualified spans
    ({len(stair)}) and a span carrying a planted column ({len(planted)}) stay blocked.
11. **Stirrups.** Diameter and rate per metre are SOURCE_EXPLICIT; the count is a LOWER_BOUND ceil(rate x clear run)
    with no +1 ({st_cnt.get(('SIMPLE_BEAM', 'READY_LOWER_BOUND'), 0)} simple + {st_cnt.get(('CONTINUOUS_BEAM', 'READY_LOWER_BOUND'), 0)} CB spans). Legs, hooks, path, end zones and the first / last rule are not
    printed, so all {st_mass} stirrup-mass rows are blocked.
12. **Side bars.** SBT REMARKS and the CB 'MIDDLE REINT.' column print '2Ø12/30cm'-type tokens on every beam deeper
    than 60 cm; faces, vertical arrangement, length and ends are not stated, so side rebar is BLOCKED_COMPONENT
    ({side_occ.get(('SIMPLE_BEAM', 'BLOCKED_COMPONENT'), 0)} simple, {side_occ.get(('CONTINUOUS_BEAM', 'BLOCKED_COMPONENT'), 0)} CB occurrences). '/30 cm' is not interpreted.
13. **Openings.** {len(openings)} S-OPENING / void objects: {open_kind.get('CLOSED_OUTLINE', 0)} closed outlines, {open_kind.get('OPEN_LINEWORK', 0)} open line work
    (dome radials, shaft diagonals, three-sided slots closing on beam faces). {open_st.get('CANDIDATE', 0)} reach inside a beam band,
    so every OPENING_EXTRA_* is NOT_APPLICABLE.
14. **Provenance.** {prov} S6 provenance templates (generic ELEMENT_* identity, BAR_RUN_ID on every CB run) in
    `S6_PROVENANCE_TEMPLATES.json`; each passes `provenance_ready`.

## Deliverables

`01_BEAM_OCCURRENCE_CONSERVATION.csv`, `02_BEAM_BINDING_READINESS.csv` (every alternative of every tag),
`03_SIMPLE_BEAM_SCHEDULE_SEMANTICS.csv`, `04_CONTINUOUS_BEAM_SCHEDULE_SEMANTICS.csv`, `05_CB_SPAN_SEQUENCE.csv`,
`06_BEAM_BAR_RUN_READINESS.csv`, `07_BEAM_SIDE_REBAR_READINESS.csv`, `08_BEAM_OPENING_OCCURRENCES.csv`,
`09_BEAM_TOKEN_CORPUS.csv`, `10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv`, `11_ENGINEERING_QUESTIONS.md`,
`12_S6_SCOPE_RECOMMENDATION.md`, `PRE_S6_SUMMARY.json`, `S6_PROVENANCE_TEMPLATES.json`, `INDEX.json`, `TEST_RUN.md`.
"""
    (here / "00_README.md").write_text(readme, encoding="utf-8")

    # ------------------------------------------------------------------------------------------------ 11 questions
    def ids(fam, st=None, sub=None):
        return sorted({r["OCCURRENCE_ID"] for r in ready if r["COMPONENT_FAMILY"] == fam and
                       (st is None or r["STATUS"] in st) and (sub is None or r["SUBFAMILY"] == sub)})
    mid_ready = _n(ready, COMPONENT_FAMILY="MID_SUPPORT_TOP", STATUS="READY")
    side_blk = _n(ready, COMPONENT_FAMILY="SIDE_REBAR", STATUS="BLOCKED_COMPONENT")
    q = f"""# PRE-S6 engineering questions

Only questions whose answer changes a quantity. Each names the components it unblocks. No answer is assumed anywhere
in the registers.

## A. Engineering questions

**Q1 - Anchorage / development of beam longitudinal bars at end supports, and bar-end hooks.** The drawing gives a
development rule only for starter bars (note 9: 70Ø tension / 40Ø compression); the slab 0.25L / 0.30L rules are slab
rules. What anchorage applies to beam bottom and top bars at end supports (straight, hooked, length)?
Unblocks DEVELOPMENT_ANCHORAGE and HOOKS on {len(ids('DEVELOPMENT_ANCHORAGE'))} occurrences; turns {long_lb} LOWER_BOUND longitudinal
components into complete bars.

**Q2 - CB top bars and hangers.** The schedule frames draw one top bar per span, from the end support (with a leg) to
near the interior support, with a printed count and diameter. The typical elevation draws instead an end-support bar
('0.3 Ln2') and a separate second-row bar lapping the MID bar, unlabelled. Which governs, what are the extents, and
is the second row a hanger with its own count / diameter? Unblocks {sum(cb_top.values())} CB TOP runs and {len(ids('HANGER', sub='CONTINUOUS_BEAM'))} CB HANGER rows.

**Q3 - Typical-detail labels.** In the 2-span typicals the end top bar is dimensioned '0.3 Ln2' (a 2-span beam has
only Ln and Ln1) and the left end top bar is not dimensioned; the 3-span typical labels its third clear span 'L3'.
Which spans are meant?

**Q4 - 3-span middle bottom bar '0.15L'.** The bar enters span 1 at support 1 and span 3 at support 2; 'L' names the
clear span of span 1 in the typical. Is the extension 0.15 x the clear span it enters? Today the extension is left
out (the run is a lower bound).

**Q5 - Ln for the MID extent.** The typical dimensions 'Ln' axis to axis and 'L' face to face, so the MID bar is
released as 0.22 x (axis-to-axis span) from each face ({mid_ready} READY runs). Please confirm (in common notation Ln
is the clear span; if so the MID bars would be re-released on the clear span).

**Q6 - Side bars '2Ø12/30cm' (SBT REMARKS) and '2Ø12' + '30cm' (CB MIDDLE REINT.).** Per face or in total; does
'/30cm' mean a vertical spacing (so the count grows with depth) or something else; full length or between supports;
end treatment? Note 21 (AI transcription) asks for side bars in beams deeper than 60 cm. Unblocks {side_blk} side-rebar rows.

**Q7 - Stirrups.** Number of legs (the SBT REMARKS icons STR2 / str3 draw an outer and one / two inner closed links
on B17, B19-B26 and the straps; no legend), hook type and length, first stirrup position, any end-zone densification.
Unblocks all {st_mass} stirrup-mass rows (counts are already released as lower bounds).

**Q8 - Simple-beam longitudinal bars.** The release assumes SBT 'BOTTOM BARS' and 'TOP BARS' run at least support face
to support face, uncurtailed (no curtailment field or detail exists). Please confirm. Basis of {simple_long}
READY_LOWER_BOUND simple-beam components.

**Q9 - Special beams.** (a) Curved ring beams ({', '.join(curved)}): where along the ring do the bars stop (support
positions)? (b) 'WITH STAIR' spans ({', '.join(stair)}): does the p.16 stair-beam detail change the SBT bars? (c) The
span carrying a planted column ({', '.join(planted)}): does the p.15 detail add to or replace the SBT bars? (d) The
cantilever CA ({', '.join(free) or 'none'}): bar run to the free end and anchorage into the back span.

## B. Drawing reconciliation (confirm, nothing is assumed)

**R1 - Bindings left as candidates:** {', '.join(cand)}. 445 / 476 / 78F: an alternative member is excluded only by
text rotation; 45D: B1 on BL016 or the 200 mm band BL021 that shares a face with BL020; 474: CB5 on BL008 (same-mark
continuity with 475) or the parallel band BL017 that shares a face with it.

**R2 - Width conflicts:** {', '.join(f'{a} {b}' for a, b in widths)} (drawn band width vs schedule B). Which is right?

**R3 - CB span conflicts:** {', '.join(lconf)} (span lengths) and {', '.join(cconf)} (2 tagged spans vs 3 schedule spans;
including the adjacent untagged 3.825 m span would match - is it part of CB8?).

**R4 - CB reading direction:** {', '.join(amb)} match the schedule in both directions. Which end is span 1?

**R5 - CB3:** its middle span is also tagged 'B3 WITH STAIR' (1827); the MID1 cell is blank while a 3Ø16 callout is
drawn on a longer bar; MID2 is blank.

**R6 - Untagged geometry:** {len(untag)} spans / arcs carry no tag ({len(untag_new)} were not in the S1 census), including the six 1F dome
ring arcs. Which marks apply?
"""
    (here / "11_ENGINEERING_QUESTIONS.md").write_text(q, encoding="utf-8")

    # ------------------------------------------------------------------------------------------------ 12 scope
    rel = Counter((r["SUBFAMILY"], r["COMPONENT_FAMILY"], r["STATUS"]) for r in ready if r["STATUS"] in RELEASED)
    body = [[a, b, c, n] for (a, b, c), n in sorted(rel.items())]
    sc = f"""# S6 scope recommendation

**Decision: RESTRICTED GO.** S6 may compute kg only for the released components below, each as the state given here,
with the provenance template from `S6_PROVENANCE_TEMPLATES.json` ({prov} templates). Everything else stays blocked and
must appear in S6 as an unquantified component, never as zero and never as an allowance.

{_table(['Subfamily', 'Component', 'State', 'Rows'], body)}

## Rules S6 must keep

1. **S5 principle.** A VERIFIED straight run stays VERIFIED; while development / anchorage or hooks are blocked the
   complete bar is a LOWER_BOUND. Do not demote the straight portion and do not add a default anchorage.
2. **Straight runs** are support face to support face (simple beams) or the bound CB bar runs (clear span + support
   width + a bound extension). Never centreline, never min(clear, c/c), never a schedule span.
3. **MID support bars** are complete bars: 0.22 x Ln of each adjacent span from the face + the support width (Ln =
   axis-to-axis as the typical dimensions it; Q5 asks for confirmation).
4. **Stirrups**: count records only (ceil(rate x clear run), no +1). No stirrup mass until Q7 is answered.
5. **Never released**: CB top bars, hangers, side bars, development, hooks, curved ring beams, the cantilever,
   stair-qualified and planted-column spans, every SOURCE_CONFLICT / PROVISIONAL_ONLY / candidate binding, CB
   occurrences with span-count conflicts, untagged geometry, and slab rules (0.25L / 0.30L) applied to beams.
6. **Candidate invariance** decides ambiguous CB reading directions; nothing is chosen.
7. **Firewall**: freeze S6 before any comparison; no reference value enters production.

## What widens S6 later

Q1 (anchorage / hooks) completes {long_lb} lower-bound longitudinal components; Q2 releases CB top bars and hangers;
Q6 side bars; Q7 stirrup mass; R1-R6 move candidates, conflicts and untagged geometry into scope.
"""
    (here / "12_S6_SCOPE_RECOMMENDATION.md").write_text(sc, encoding="utf-8")
