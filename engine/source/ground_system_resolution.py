"""Ground-system source resolution (pre-S5.1): generic decisions over measured evidence, no geometry library, no kg.

The project builder measures (wall cover along a beam, side classes, support faces, levels, junctions); this module
turns those measurements into states with explicit rules. Every rule names what it does NOT decide:

  wall_relation        architectural wall above a ground-beam span: UNDER_EXTERIOR_WALL / UNDER_INTERIOR_WALL /
                       NO_WALL_ABOVE / AMBIGUOUS_WALL_RELATION / OUTSIDE_ARCH_COVERAGE (cover of the beam centreline by
                       wall-line elements, sampled; never nearest-text guessing)
  exterior_authority   per span, the architecture decides; the two geometric proxies (zone outline, footprint outline)
                       are recorded, never voted
  bar_run              member centreline / clear concrete / support face-to-face run, kept SEPARATE; the straight bar
                       lower bound is the support face-to-face run (physical: the bars cross the clear opening between
                       the support faces); never a numerical minimum of different bases; contradictions are
                       LENGTH_GEOMETRY_CONFLICT
  length_basis         which literal length condition holds on the clear and on the centreline basis; a component is
                       released on a basis-dependent detail only when every basis gives the same detail
  concentrated_load    CONCENTRATED_LOAD_PRESENT / NO_CONCENTRATED_LOAD_EVIDENCE / SOURCE_CONFLICT / UNKNOWN; the
                       absence of a symbol is not proof, so every member that bears on a span is listed
  candidate_details    the detail set for one span after exterior authority, length basis, nested conditions and the
                       "without concentrated load" clause
  follow_arch_depth    "depth FOLLOW ARCH." from the levels the source prints; BOUNDED when only one side is known
  free_end_class       what a span end that met no column / beam actually rests on
"""

from __future__ import annotations

POLICY_ID = "GROUND_SYSTEM_RESOLUTION_V1"

# ---------------------------------------------------------------------------------------------------- wall relation
WALL_RELATIONS = ("UNDER_EXTERIOR_WALL", "UNDER_INTERIOR_WALL", "NO_WALL_ABOVE", "AMBIGUOUS_WALL_RELATION",
                  "OUTSIDE_ARCH_COVERAGE")
SIDE_CLASSES = ("INSIDE", "OUTSIDE", "UNKNOWN")
WALL_EXTERIOR_CLASSES = ("EXTERIOR", "INTERIOR", "SITE_BOTH_OUTSIDE", "UNKNOWN_SIDE")
MIN_LINE_COVER = 0.50          # wall line (walls + openings in the line) over >= half the span
NO_WALL_COVER = 0.10           # < 10 % of the span under any wall-line element
CLASS_SHARE = 0.80             # one exterior class over >= 80 % of the covered wall length


def side_pair_class(a: str, b: str) -> str:
    """Exterior class of a wall from the classes of the space on its two faces."""
    s = {a, b}
    if s == {"INSIDE"}:
        return "INTERIOR"
    if s == {"INSIDE", "OUTSIDE"}:
        return "EXTERIOR"
    if s == {"OUTSIDE"}:
        return "SITE_BOTH_OUTSIDE"
    return "UNKNOWN_SIDE"


def vote(classes):
    """Majority class of a list of probe results (ties -> the first in sorted order; empty -> UNKNOWN_SIDE)."""
    if not classes:
        return "UNKNOWN_SIDE"
    best = max(sorted(set(classes)), key=lambda c: classes.count(c))
    return best


def wall_relation(samples, *, in_arch_coverage=True) -> dict:
    """samples: [{"len": mm, "element": wall-element kind or None, "ext": exterior class or None,
    "opening": bool, "handle": str or None}] along the span centreline (one per sampling station).

    The wall line is the wall elements plus the openings in that line (door / gate geometry between wall pieces).
    Returns the overlap figures and the relation (one of WALL_RELATIONS)."""
    L = sum(s["len"] for s in samples)
    wall = sum(s["len"] for s in samples if s.get("element"))
    opening = sum(s["len"] for s in samples if not s.get("element") and s.get("opening"))
    by_ext, by_kind = {}, {}
    for s in samples:
        if s.get("element"):
            by_ext[s["ext"]] = by_ext.get(s["ext"], 0.0) + s["len"]
            by_kind[s["element"]] = by_kind.get(s["element"], 0.0) + s["len"]
    line = wall + opening
    pct = line / L if L > 0 else 0.0
    ext_share = by_ext.get("EXTERIOR", 0.0) / wall if wall else 0.0
    int_share = by_ext.get("INTERIOR", 0.0) / wall if wall else 0.0
    if not in_arch_coverage:
        rel, why = "OUTSIDE_ARCH_COVERAGE", "span outside the architectural ground-floor plan"
    elif pct < NO_WALL_COVER:
        rel, why = "NO_WALL_ABOVE", f"wall line over {pct:.0%} of the span (< {NO_WALL_COVER:.0%})"
    elif wall == 0.0:
        rel, why = "AMBIGUOUS_WALL_RELATION", "openings only (no wall element) over the span"
    elif pct >= MIN_LINE_COVER and ext_share >= CLASS_SHARE:
        rel, why = "UNDER_EXTERIOR_WALL", f"wall line over {pct:.0%}; {ext_share:.0%} of the wall is exterior"
    elif pct >= MIN_LINE_COVER and int_share >= CLASS_SHARE:
        rel, why = "UNDER_INTERIOR_WALL", f"wall line over {pct:.0%}; {int_share:.0%} of the wall is interior"
    elif pct < MIN_LINE_COVER:
        rel, why = "AMBIGUOUS_WALL_RELATION", f"partial overlap: wall line over {pct:.0%} of the span"
    else:
        rel, why = "AMBIGUOUS_WALL_RELATION", ("mixed wall classes along the span: " +
                                               ", ".join(f"{k} {v / wall:.0%}" for k, v in sorted(by_ext.items())))
    return {"SPAN_LENGTH_MM": L, "WALL_LENGTH_MM": wall, "OPENING_LENGTH_MM": opening, "OVERLAP_LENGTH_MM": line,
            "OVERLAP_PERCENT": pct, "EXTERIOR_SHARE": ext_share, "INTERIOR_SHARE": int_share,
            "WALL_CLASS": max(sorted(by_kind), key=lambda k: by_kind[k]) if by_kind else None,
            "EXTERIOR_CLASS": max(sorted(by_ext), key=lambda k: by_ext[k]) if by_ext else None,
            "BY_EXTERIOR_CLASS_MM": by_ext, "BY_ELEMENT_MM": by_kind, "RELATION": rel, "WHY": why}


# ---------------------------------------------------------------------------------------------- exterior authority
EXTERIOR_AUTHORITY = ("EXTERIOR_SOURCE_VERIFIED", "INTERIOR_SOURCE_VERIFIED", "CANDIDATE_EXTERIOR", "SOURCE_CONFLICT",
                      "UNRESOLVED")
SLAB_EDGE = ("PERIMETER", "INTERNAL", "UNKNOWN")


def exterior_authority(*, relation: str, slab_edge: str, zone_test: bool, footprint_test: bool) -> dict:
    """Per-span exterior decision. The architecture decides; the ground-slab edge (structural plan) must not
    contradict it; the two geometric proxies are recorded only (no majority vote)."""
    proxies = {"V3_ZONE_OUTLINE": bool(zone_test), "R4_FOOTPRINT_OUTLINE": bool(footprint_test)}
    if relation == "UNDER_EXTERIOR_WALL":
        out = ("SOURCE_CONFLICT", "exterior wall above but the ground slab continues on both sides") \
            if slab_edge == "INTERNAL" else ("EXTERIOR_SOURCE_VERIFIED", "architectural exterior wall above the span")
    elif relation == "UNDER_INTERIOR_WALL":
        out = ("SOURCE_CONFLICT", "interior wall above but the ground slab ends at this beam") \
            if slab_edge == "PERIMETER" else ("INTERIOR_SOURCE_VERIFIED", "architectural interior wall above the span")
    elif relation == "NO_WALL_ABOVE":
        if slab_edge == "INTERNAL":
            out = ("INTERIOR_SOURCE_VERIFIED", "no wall above and ground slab on both sides: not under an exterior "
                                               "wall")
        elif slab_edge == "PERIMETER":
            out = ("CANDIDATE_EXTERIOR", "beam on the ground-slab edge with no wall above: the 'for exterior walls' "
                                         "title is not literally met, the interior titles assume a wall-free inside")
        else:
            out = ("UNRESOLVED", "no wall above and the slab edge position is unknown")
    elif relation == "AMBIGUOUS_WALL_RELATION":
        out = ("CANDIDATE_EXTERIOR", "partial / mixed wall relation on the slab edge") if slab_edge == "PERIMETER" \
            else ("UNRESOLVED", "partial / mixed wall relation")
    else:
        out = ("UNRESOLVED", "outside the architectural plan")
    return {"AUTHORITY": out[0], "WHY": out[1], "PROXIES": proxies,
            "PROXIES_AGREE_WITH_AUTHORITY": None if out[0] not in ("EXTERIOR_SOURCE_VERIFIED",
                                                                   "INTERIOR_SOURCE_VERIFIED")
            else all(v == (out[0] == "EXTERIOR_SOURCE_VERIFIED") for v in proxies.values())}


# ---------------------------------------------------------------------------------------------------- bar run
LENGTH_STATES = ("CONSISTENT", "LENGTH_GEOMETRY_CONFLICT", "BAR_RUN_GEOMETRY_UNRESOLVED")
LEN_TOL_MM = 1.0


def bar_run(*, centreline_mm, clear_concrete_mm, face_start, face_end, bar_lines=()) -> dict:
    """face_start / face_end: station (mm along the member centreline) of the actual support face at each end, or
    None when that end has no support face (boundary / the centreline misses the support).
    bar_lines: [{"offset_mm": d, "run_mm": face-to-face along that bar line or None, "misses": [ends]}] for the
    outermost longitudinal bar lines (centreline +- (half width - cover)).

    All lengths are kept. The straight-bar lower bound is the shortest face-to-face run over the centreline and the
    outer bar lines (every bar spans at least between the two support faces along its own line; at an oblique
    support the acute-side line is the shortest bar). It is never a minimum of different length BASES, and it is
    withheld whenever one length contradicts another (LENGTH_GEOMETRY_CONFLICT)."""
    f2f = (face_end - face_start) if face_start is not None and face_end is not None else None
    run_issues, concrete_issues = [], []
    lines = list(bar_lines)
    for bl in lines:
        if bl.get("misses"):
            run_issues.append(f"bar line at {bl['offset_mm']:+.0f} mm misses the {'/'.join(bl['misses'])} support "
                              "(the support does not cut the full beam width)")
    runs = [f2f] + [bl["run_mm"] for bl in lines]
    lb_line = min(runs) if f2f is not None and all(r is not None for r in runs) else None
    if f2f is not None and f2f <= 0:
        run_issues.append(f"support faces overlap (face-to-face {f2f:.1f} mm)")
    if f2f is not None and centreline_mm is not None and f2f > centreline_mm + LEN_TOL_MM:
        run_issues.append(f"face-to-face {f2f:.1f} > centreline {centreline_mm:.1f} mm")
    if lb_line is not None and clear_concrete_mm is not None and lb_line > clear_concrete_mm + LEN_TOL_MM:
        run_issues.append(f"shortest bar line {lb_line:.1f} > clear concrete {clear_concrete_mm:.1f} mm")
    if centreline_mm is not None and clear_concrete_mm is not None and clear_concrete_mm > centreline_mm + LEN_TOL_MM:
        concrete_issues.append(f"clear concrete {clear_concrete_mm:.1f} > centreline {centreline_mm:.1f} mm (the "
                               "concrete piece runs past a support centre: the support does not cut the full width)")
    if f2f is None:
        state = "BAR_RUN_GEOMETRY_UNRESOLVED"
    elif run_issues or concrete_issues:
        state = "LENGTH_GEOMETRY_CONFLICT"
    else:
        state = "CONSISTENT"
    # withheld on any contradiction: where a support does not cut the full beam width, the bars in the uncut strip
    # have no face at that support (never resolved by taking the smaller number)
    lb = lb_line if state == "CONSISTENT" else None
    run_state = "LOWER_BOUND" if lb is not None else state
    return {"MEMBER_CENTERLINE_LENGTH_MM": centreline_mm, "MEMBER_CLEAR_CONCRETE_LENGTH_MM": clear_concrete_mm,
            "SUPPORT_FACE_TO_FACE_RUN_MM": f2f, "BAR_LINE_RUNS_MM": [bl["run_mm"] for bl in lines],
            "BAR_STRAIGHT_RUN_LOWER_BOUND_MM": lb, "LENGTH_STATE": state, "ISSUES": run_issues + concrete_issues,
            "BAR_RUN_STATE": run_state}


# ---------------------------------------------------------------------------------------------------- length basis
LEN_EQ_TOL_M = 0.001


def length_conditions(L_m, conditions: dict) -> list:
    """conditions: {detail_id: (op, threshold_m)} with op GT / LT. A length within 1 mm of a threshold meets no
    literal condition."""
    out = []
    for k, (op, th) in sorted(conditions.items()):
        if L_m is None or abs(L_m - th) <= LEN_EQ_TOL_M:
            continue
        if (op == "GT" and L_m > th) or (op == "LT" and L_m < th):
            out.append(k)
    return out


def length_basis(bases: dict, conditions: dict) -> dict:
    """bases: {"CLEAR": m, "CENTRELINE": m}. Returns the detail set on each basis and SAME_RESULT."""
    by = {k: length_conditions(v, conditions) for k, v in bases.items() if v is not None}
    on = sorted({f"{k}={v:.3f} m on {th} m" for k, v in bases.items() if v is not None
                 for _, (op, th) in conditions.items() if abs(v - th) <= LEN_EQ_TOL_M})
    same = len({tuple(v) for v in by.values()}) == 1 and len(by) == len(bases) and not on
    return {"DETAIL_BY_CLEAR_LENGTH": by.get("CLEAR"), "DETAIL_BY_CENTRELINE_LENGTH": by.get("CENTRELINE"),
            "SAME_RESULT": same, "ON_THRESHOLD": on,
            "UNION": sorted({d for v in by.values() for d in v})}


# ---------------------------------------------------------------------------------------------------- loads
LOAD_STATES = ("CONCENTRATED_LOAD_PRESENT", "NO_CONCENTRATED_LOAD_EVIDENCE", "SOURCE_CONFLICT", "UNKNOWN")
# evidence kind -> what it means for the span
PRESENT_KINDS = ("COLUMN_BEARING_ON_SPAN", "PLANTED_COLUMN_ON_SPAN", "POINT_LOAD_SYMBOL", "POINT_LOAD_NOTE")
UNKNOWN_KINDS = ("BEAM_END_REACTION", "BEAM_CROSSING", "STAIR_BEARING_CANDIDATE", "UNIDENTIFIED_SYMBOL")
RECORD_ONLY_KINDS = ("JUNCTION_AT_SUPPORT",)


def concentrated_load(evidence) -> dict:
    """evidence: [{"kind": ..., "ref": ..., "detail": ...}]. PRESENT when a member / symbol that is a concentrated
    load by definition bears on the span; UNKNOWN when something bears on the span whose status as a 'concentrated
    load' in the detail titles is not stated; NO_CONCENTRATED_LOAD_EVIDENCE otherwise (not proof of absence)."""
    kinds = {e["kind"] for e in evidence}
    bad = kinds - set(PRESENT_KINDS) - set(UNKNOWN_KINDS) - set(RECORD_ONLY_KINDS) - {"CONTRADICTING_NOTE"}
    if bad:
        raise ValueError(f"unknown load evidence kinds {sorted(bad)}")
    if "CONTRADICTING_NOTE" in kinds:
        st = "SOURCE_CONFLICT"
    elif kinds & set(PRESENT_KINDS):
        st = "CONCENTRATED_LOAD_PRESENT"
    elif kinds & set(UNKNOWN_KINDS):
        st = "UNKNOWN"
    else:
        st = "NO_CONCENTRATED_LOAD_EVIDENCE"
    return {"STATE": st, "EVIDENCE": list(evidence)}


# ---------------------------------------------------------------------------------------------------- precedence
PRECEDENCE_SOURCES = ("SOURCE_EXPLICIT", "SOURCE_LAYOUT_DERIVED", "SPECIFICITY_CANDIDATE", "UNRESOLVED")


def nested_precedence(*, explicit_note=False, layout_grouping=False, narrower_condition=None) -> dict:
    """Precedence between two literal conditions that hold together (e.g. < 2.5 m and < 5 m). Only an explicit note
    or a drawn grouping resolves it; 'the narrower condition wins' is a specificity CANDIDATE and both details are
    preserved."""
    if explicit_note:
        return {"RULE_PRECEDENCE_SOURCE": "SOURCE_EXPLICIT", "RESOLVED": True, "WINNER": narrower_condition}
    if layout_grouping:
        return {"RULE_PRECEDENCE_SOURCE": "SOURCE_LAYOUT_DERIVED", "RESOLVED": True, "WINNER": narrower_condition}
    if narrower_condition:
        return {"RULE_PRECEDENCE_SOURCE": "SPECIFICITY_CANDIDATE", "RESOLVED": False, "WINNER": None,
                "CANDIDATE_WINNER": narrower_condition}
    return {"RULE_PRECEDENCE_SOURCE": "UNRESOLVED", "RESOLVED": False, "WINNER": None}


# ---------------------------------------------------------------------------------------------------- candidates
NO_DETAIL_IF_LOADED = "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD"


def candidate_details(*, authority: str, length_union, load_state: str, clause_details, exterior_detail: str,
                      basis_same: bool, nested: bool, precedence: dict) -> dict:
    """The candidate detail set of one ground-beam span and its DETAIL_APPLICABILITY_STATE.

    clause_details: details whose title carries 'without concentrated load'. Under CONCENTRATED_LOAD_PRESENT they
    are excluded; under UNKNOWN they stay but the loaded case is added as its own candidate (the remaining details,
    or NO_DETAIL_IF_LOADED when none remains) so that a component is only invariant if it is the same in both cases."""
    length_union = sorted(length_union)
    clause = set(clause_details)
    notes = []
    if authority == "EXTERIOR_SOURCE_VERIFIED":
        return {"CANDIDATES": [exterior_detail], "STATE": "PROJECT_GENERAL_DETAIL",
                "NOTES": ["exterior wall verified on the architectural plan; the exterior section has no length or "
                          "load clause"]}
    loaded = [d for d in length_union if d not in clause]
    if load_state == "CONCENTRATED_LOAD_PRESENT":
        base = loaded
        notes.append("concentrated load present: the 'without concentrated load' sections do not apply")
    elif load_state in ("UNKNOWN", "SOURCE_CONFLICT"):
        base = list(length_union)
        if any(d in clause for d in length_union):
            if not loaded:
                base = base + [NO_DETAIL_IF_LOADED]
            notes.append("concentrated-load condition unresolved: the loaded case is a separate candidate")
    else:
        base = list(length_union)
    if authority == "INTERIOR_SOURCE_VERIFIED":
        cands = sorted(set(base))
        if not cands:
            state = "NO_APPLICABLE_DETAIL"
        elif NO_DETAIL_IF_LOADED in cands or not basis_same or (nested and not precedence.get("RESOLVED")) or \
                load_state in ("UNKNOWN", "SOURCE_CONFLICT") and any(d in clause for d in cands):
            state = "CANDIDATE_DETAIL"
        else:
            state = "EXPLICIT_LENGTH_CONDITION"
    else:                                   # CANDIDATE_EXTERIOR / UNRESOLVED / SOURCE_CONFLICT
        cands = sorted(set(base) | {exterior_detail})
        state = "SOURCE_CONFLICT" if authority == "SOURCE_CONFLICT" else "CANDIDATE_DETAIL"
        notes.append(f"exterior authority {authority}: exterior and interior sections are both candidates")
    if not basis_same:
        notes.append("the length basis changes the detail: both bases' details are candidates")
    if nested and not precedence.get("RESOLVED"):
        notes.append("'Less than 2.5m' and 'Less than 5m' both hold literally; precedence is a "
                     f"{precedence.get('RULE_PRECEDENCE_SOURCE')} - both preserved")
    return {"CANDIDATES": cands, "STATE": state, "NOTES": notes}


# ---------------------------------------------------------------------------------------------------- follow arch
DEPTH_STATES = ("SOURCE_EXPLICIT", "SOURCE_DERIVED", "BOUNDED", "UNRESOLVED")


def follow_arch_depth(*, top_ffl_m, top_source, buildup_known_m, bottom_levels_m, bottom_source) -> dict:
    """'depth FOLLOW ARCH. (Ground Floor slab level ... Outer Normal ground level)'. Top = GF slab level = FFL of
    the floor the beam carries minus the floor build-up; bottom = the outer normal ground level drawn at the beam
    soffit. Unknown build-up only bounds the depth from above (build-up >= 0)."""
    if top_ffl_m is None or not bottom_levels_m:
        return {"STATE": "UNRESOLVED", "DEPTH_MAX_M": None, "DEPTH_MIN_M": None,
                "DERIVATION": "the floor level the beam carries or the outer ground level is not established",
                "TOP_SOURCE": top_source, "BOTTOM_SOURCE": bottom_source}
    lo_ngl, hi_ngl = min(bottom_levels_m), max(bottom_levels_m)
    if buildup_known_m is not None and len(set(bottom_levels_m)) == 1:
        d = top_ffl_m - buildup_known_m - lo_ngl
        return {"STATE": "SOURCE_DERIVED", "DEPTH_MAX_M": d, "DEPTH_MIN_M": d,
                "DERIVATION": f"({top_ffl_m:+.2f} - {buildup_known_m:.3f}) - ({lo_ngl:+.2f})",
                "TOP_SOURCE": top_source, "BOTTOM_SOURCE": bottom_source}
    return {"STATE": "BOUNDED", "DEPTH_MAX_M": round(top_ffl_m - lo_ngl, 3), "DEPTH_MIN_M": None,
            "DERIVATION": f"D = ({top_ffl_m:+.2f} - b) - NGL, b = floor build-up (not printed, >= 0), NGL in "
                          f"[{lo_ngl:+.2f}, {hi_ngl:+.2f}] -> D <= {top_ffl_m - lo_ngl:.2f} m; no lower bound",
            "TOP_SOURCE": top_source, "BOTTOM_SOURCE": bottom_source}


# ---------------------------------------------------------------------------------------------------- free ends
FREE_END_CLASSES = ("FOOTING", "COLUMN", "WALL_RETURN", "BOUNDARY", "ARCHITECTURAL_TERMINATION", "DRAWING_BREAK",
                    "UNRESOLVED")
GAP_TOL_MM = 50.0


def free_end_class(*, column_gap_mm=None, column_outline_gap_mm=None, inside_footing=None, boundary_gap_mm=None,
                   band_gap_mm=None, arch_wall_beyond_mm=None, arch_wall_at_end=False) -> dict:
    """Ordered physical tests for a span end that touched no column and no beam (TOUCH = 5 mm)."""
    if column_gap_mm is not None and column_gap_mm <= GAP_TOL_MM:
        return {"CLASS": "COLUMN", "WHY": f"column outline {column_gap_mm:.0f} mm from the end (drawing gap)"}
    if column_outline_gap_mm is not None and column_outline_gap_mm <= GAP_TOL_MM:
        return {"CLASS": "COLUMN", "WHY": f"column outline lines {column_outline_gap_mm:.0f} mm from the end (an "
                                          "outline the rectangle detector did not return, or closer than it)"}
    if inside_footing:
        return {"CLASS": "FOOTING", "WHY": f"the end lies inside footing outline {inside_footing}"}
    if boundary_gap_mm is not None and boundary_gap_mm <= GAP_TOL_MM:
        return {"CLASS": "BOUNDARY", "WHY": f"the end lies on the plot boundary line ({boundary_gap_mm:.0f} mm)"}
    if band_gap_mm is not None and band_gap_mm <= GAP_TOL_MM:
        return {"CLASS": "DRAWING_BREAK", "WHY": f"another beam band {band_gap_mm:.0f} mm away"}
    if arch_wall_beyond_mm is not None and arch_wall_beyond_mm > 300.0:
        return {"CLASS": "WALL_RETURN", "WHY": f"the wall above continues {arch_wall_beyond_mm:.0f} mm past the end"}
    if arch_wall_at_end:
        return {"CLASS": "ARCHITECTURAL_TERMINATION", "WHY": "the wall above ends with the beam"}
    return {"CLASS": "UNRESOLVED", "WHY": "no support, boundary, beam or wall evidence at the end"}


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "wall_relation": {"MIN_LINE_COVER": MIN_LINE_COVER, "NO_WALL_COVER": NO_WALL_COVER,
                                                      "CLASS_SHARE": CLASS_SHARE},
            "exterior_authority": "architecture decides; ground-slab edge may only contradict (SOURCE_CONFLICT); "
                                  "zone / footprint proxies recorded, never voted",
            "bar_run": "member centreline, clear concrete and support face-to-face kept separate; straight-bar lower "
                       "bound = face-to-face run; no numerical minimum",
            "length_basis": "release a basis-dependent component only when every basis gives the same detail",
            "concentrated_load": {"present": list(PRESENT_KINDS), "unknown": list(UNKNOWN_KINDS)},
            "free_end_gap_tol_mm": GAP_TOL_MM, "length_tol_mm": LEN_TOL_MM}

