"""SLAB QTO AUTHORITY (AD2) - which lane a slab reinforcement quantity belongs to, and how a project-basis QTO
quantity is formed without inventing a fabrication decision (generic, no kg).

Three quantity-authority lanes. Every quantity item carries exactly one:
  SOURCE_DERIVED_PHYSICAL   the drawing / source establishes the physical count, extent and role
  PROJECT_BASIS_QTO         the source establishes the specification / rate / role; Urban measures it with a declared
                            deterministic convention (rate density, a stated Urban rule, a minimum cover used as a
                            number). Never VERIFIED_PHYSICAL, never AS_BUILT, never SOURCE_EXACT.
  BLOCKED_UNQUANTIFIED      the reinforcement, its applicability, its extent or its classification is not established

Rates are densities. N bars/m over a width W m is N x W equivalent bars, unrounded: no ceil, no floor, no +1. The
physical BBS bar count stays UNRESOLVED unless a project-source count / edge-bar convention exists. A printed count
without '/m' is an explicit count only when it is bound to a finite bar object; its length may stay blocked while the
count releases.

A stated 50% / 50% curtailment is a density split for QTO (0.5 continuing, 0.5 curtailed). Which physical bars stop
is a BBS question and stays unresolved; an odd physical count is BBS-ambiguous and no extra bar is assigned.

Rules for one bar role: identity first (same physical family or not, from wording, location, role, support,
size / rate, scope). Different families coexist. The same family is governed by the more local source
(LOCAL_CALLOUT > FLOOR_PLAN_NOTE > GENERIC_TYPICAL_DETAIL); the loser is OVERRIDDEN_PROJECT_SOURCE, kept, never
summed. A local callout overrides a general rule for the same role at its own location only; it adds to it only
when the source shows a second physical family.

A support's continuity is physical: no structural slab beyond it (outside, void, open to below, no slab) is
NON_CONTINUOUS; a physical slab that is excluded, special, blocked, at another level or on a non-beam support is
CONTINUITY_UNRESOLVED. Analysis ownership never stands in for physical absence.

Irregular panels are measured by local bar lines: for each bar direction the panel polygon (with holes) is cut into
strips between consecutive vertex coordinates of the transverse axis; inside a strip every bar line meets the same two
boundary edges, so the local clear run varies linearly and its integral is exact. Strip integrals reconcile to the
polygon area. No bounding rectangle is used.

Nothing here names a project, a sheet, a panel or a handle.
"""

from __future__ import annotations

import math
import re

from engine.source import slab_rebar_readiness as SR

TOL = 1e-9

# ------------------------------------------------------------------ lanes
SOURCE_DERIVED_PHYSICAL = "SOURCE_DERIVED_PHYSICAL"
PROJECT_BASIS_QTO = "PROJECT_BASIS_QTO"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO, BLOCKED_UNQUANTIFIED)
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)
FORBIDDEN_LABELS = ("VERIFIED_PHYSICAL", "AS_BUILT", "SOURCE_EXACT")

# count bases
COUNT_SOURCE_EXPLICIT = "SOURCE_EXPLICIT_COUNT"          # 'NØD' bound to a finite bar object
COUNT_RATE_DENSITY = "URBAN_RATE_DENSITY"                # N/m x W, continuous, unrounded
COUNT_UNRESOLVED = "COUNT_UNRESOLVED"
COUNT_BASES = (COUNT_SOURCE_EXPLICIT, COUNT_RATE_DENSITY, COUNT_UNRESOLVED)
# extent bases
EXTENT_SOURCE_DIMENSION = "SOURCE_DIMENSION"             # a printed dimension
EXTENT_PROJECT_GEOMETRY = "PROJECT_GEOMETRY"             # face to face on project geometry
EXTENT_PROJECT_RULE = "PROJECT_SOURCE_RULE"              # a project rule (e.g. 0.125 L) on project geometry
EXTENT_URBAN_RULE = "URBAN_OWNER_MEASUREMENT_RULE"       # a declared Urban rule (e.g. 1/3 span, local bar line)
EXTENT_MINIMUM_COVER = "MINIMUM_PROJECT_COVER"           # a minimum cover used as a number
EXTENT_BLOCKED = "EXTENT_BLOCKED"
EXTENT_BASES = (EXTENT_SOURCE_DIMENSION, EXTENT_PROJECT_GEOMETRY, EXTENT_PROJECT_RULE, EXTENT_URBAN_RULE,
                EXTENT_MINIMUM_COVER, EXTENT_BLOCKED)
_SOURCE_EXTENTS = (EXTENT_SOURCE_DIMENSION, EXTENT_PROJECT_GEOMETRY, EXTENT_PROJECT_RULE)
_BASIS_EXTENTS = _SOURCE_EXTENTS + (EXTENT_URBAN_RULE, EXTENT_MINIMUM_COVER)


class SlabQtoError(ValueError):
    pass


def lane(count_basis, extent_bases, *, blockers=()):
    """The lane of one quantity item. extent_bases: every basis the item's extent uses."""
    if count_basis not in COUNT_BASES:
        raise SlabQtoError(f"unknown count basis {count_basis}")
    ext = [extent_bases] if isinstance(extent_bases, str) else list(extent_bases)
    if not ext or any(e not in EXTENT_BASES for e in ext):
        raise SlabQtoError(f"unknown extent basis {ext}")
    if blockers or count_basis == COUNT_UNRESOLVED or EXTENT_BLOCKED in ext:
        return BLOCKED_UNQUANTIFIED
    if count_basis == COUNT_SOURCE_EXPLICIT and all(e in _SOURCE_EXTENTS for e in ext):
        return SOURCE_DERIVED_PHYSICAL
    return PROJECT_BASIS_QTO


def check_label(label):
    if str(label).upper() in FORBIDDEN_LABELS:
        raise SlabQtoError(f"{label} is never a slab QTO state")
    return label


# ------------------------------------------------------------------ counts
_NOTATION = re.compile(r"^\s*(\d+)\s*(?:%%[cC]|[Øø])\s*(\d+)\s*(/\s*[mM])?\b", re.I)
FINITE_BAR_OBJECTS = ("BAR_GROUP", "SUPPORT_BAR_GRAPHIC", "CORNER_BAR_GROUP", "TRIM_BAR_GROUP")
COUNT_NOTATION_AMBIGUOUS = "COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE"
UNRESOLVED = "UNRESOLVED"


def parse_notation(text):
    m = _NOTATION.match(str(text or ""))
    if not m:
        return None
    return {"n": int(m.group(1)), "dia_mm": int(m.group(2)), "per_metre": bool(m.group(3))}


def rate_qto(rate_per_m, width_mm, *, fraction=1.0):
    """A rate is a density: equivalent bars = N x fraction x W (W in m), never rounded, never +1."""
    if rate_per_m is None or rate_per_m <= 0 or width_mm is None or width_mm < 0:
        raise SlabQtoError("rate and width are required")
    if not 0 < fraction <= 1:
        raise SlabQtoError("density fraction must be in (0, 1]")
    return {"count_basis": COUNT_RATE_DENSITY, "rate_per_m": float(rate_per_m), "density_fraction": float(fraction),
            "distribution_width_mm": float(width_mm),
            "equivalent_bar_count": float(rate_per_m) * float(fraction) * float(width_mm) / 1000.0,
            "physical_bbs_bar_count": UNRESOLVED, "rounded": False, "plus_one": False}


def explicit_count(notation, *, bound_object=None):
    """'NØD' without '/m': an explicit count only when bound to a finite bar object (a drawn bar group, a support-bar
    graphic, a corner group). Otherwise the notation is ambiguous (count or rate with '/m' omitted)."""
    p = parse_notation(notation)
    if p is None:
        raise SlabQtoError(f"not a bar notation: {notation!r}")
    if p["per_metre"]:
        return {"state": "RATE", "count_basis": COUNT_RATE_DENSITY, "rate_per_m": p["n"], "dia_mm": p["dia_mm"],
                "count_releases": False}
    if bound_object in FINITE_BAR_OBJECTS:
        return {"state": SR.COUNT_EXPLICIT, "count_basis": COUNT_SOURCE_EXPLICIT, "count": p["n"],
                "dia_mm": p["dia_mm"], "bound_object": bound_object, "count_releases": True}
    return {"state": COUNT_NOTATION_AMBIGUOUS, "count_basis": COUNT_UNRESOLVED, "count": None, "dia_mm": p["dia_mm"],
            "bound_object": bound_object, "count_releases": False}


# ------------------------------------------------------------------ 50 % curtailment
DENSITY_50_50 = "DENSITY_50_50"
BBS_AMBIGUOUS_ODD_COUNT = "BBS_AMBIGUOUS_ODD_COUNT"


def curtailment_density(*, source_states_split, continuing=0.5, curtailed=0.5, physical_count=None):
    """A source-stated split (e.g. 'stop 50%, balance continuous') is a density split for QTO."""
    if not source_states_split:
        return {"state": BLOCKED_UNQUANTIFIED, "why": "no source-stated split"}
    if abs(continuing + curtailed - 1.0) > TOL or continuing <= 0 or curtailed <= 0:
        raise SlabQtoError("the split must be two positive fractions summing to 1")
    out = {"state": DENSITY_50_50 if abs(continuing - 0.5) < TOL else "DENSITY_SPLIT",
           "continuous_density_fraction": continuing, "curtailed_density_fraction": curtailed,
           "physical_sequencing": UNRESOLVED, "which_bars_stop": UNRESOLVED}
    if physical_count is not None:
        out["physical_count"] = physical_count
        out["bbs"] = (BBS_AMBIGUOUS_ODD_COUNT if physical_count % 2 else "EVEN_COUNT_SEQUENCE_UNRESOLVED")
        out["extra_bar_assigned_to"] = None
    return out


# ------------------------------------------------------------------ bar-role identity and precedence
SAME_FAMILY = "SAME_PHYSICAL_BAR_FAMILY"
DIFFERENT_FAMILIES = "DIFFERENT_PHYSICAL_BAR_FAMILIES"
IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
LOCAL_CALLOUT = "LOCAL_CALLOUT"
FLOOR_PLAN_NOTE = "FLOOR_PLAN_NOTE"
GENERIC_TYPICAL_DETAIL = "GENERIC_TYPICAL_DETAIL"
SCOPE_RANK = {LOCAL_CALLOUT: 3, FLOOR_PLAN_NOTE: 2, GENERIC_TYPICAL_DETAIL: 1}
OVERRIDDEN_PROJECT_SOURCE = "OVERRIDDEN_PROJECT_SOURCE"
GOVERNING_PROJECT_SOURCE = "GOVERNING_PROJECT_SOURCE"
_PHYSICAL = ("layer", "location", "role", "support")


def bar_role_identity(a, b):
    """a, b: {"rule_id", "layer", "location", "role", "support", "dia_mm", "rate", "size_deferred_to", "scope"}.
    DIFFERENT when a physical feature contradicts; SAME when every physical feature agrees and the specification is
    equal or one rule defers its size / spacing to the other's source; UNRESOLVED otherwise."""
    ev, contra, missing = [], [], []
    for k in _PHYSICAL:
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            missing.append(k)
        elif va == vb:
            ev.append(f"{k}: both {va}")
        else:
            contra.append(f"{k}: {va} vs {vb}")
    spec = None
    da, db, ra, rb = a.get("dia_mm"), b.get("dia_mm"), a.get("rate"), b.get("rate")
    if da is not None and db is not None:
        if da == db and ra == rb:
            spec = "equal specification"
        else:
            contra.append(f"specification: {da}/{ra} vs {db}/{rb}")
    elif (da is None and a.get("size_deferred_to") and a["size_deferred_to"] == b.get("scope")) or \
            (db is None and b.get("size_deferred_to") and b["size_deferred_to"] == a.get("scope")):
        spec = "one rule defers its size / spacing to the other rule's source"
    if spec:
        ev.append(spec)
    if contra:
        identity = DIFFERENT_FAMILIES
    elif not missing and spec:
        identity = SAME_FAMILY
    else:
        identity = IDENTITY_UNRESOLVED
    return {"identity": identity, "evidence": ev, "contradictions": contra, "missing": missing,
            "rules": [a.get("rule_id"), b.get("rule_id")]}


def same_role_precedence(rules):
    """rules: [{"rule_id", "scope"}] of ONE physical family. The most local scope governs; ties at the top are a
    SOURCE_CONFLICT. Never summed."""
    if not rules:
        raise SlabQtoError("no rule")
    for r in rules:
        if r["scope"] not in SCOPE_RANK:
            raise SlabQtoError(f"unknown rule scope {r['scope']}")
    top = max(SCOPE_RANK[r["scope"]] for r in rules)
    win = [r["rule_id"] for r in rules if SCOPE_RANK[r["scope"]] == top]
    if len(win) > 1:
        return {"state": SR.SOURCE_CONFLICT, "governing": None, "tied": sorted(win), "overridden": [], "summed": False}
    return {"state": GOVERNING_PROJECT_SOURCE, "governing": win[0], "summed": False,
            "overridden": sorted(r["rule_id"] for r in rules if r["rule_id"] != win[0]),
            "overridden_state": OVERRIDDEN_PROJECT_SOURCE}


URBAN_TOP_EXTENT_RULE = "URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1"
URBAN_LOCAL_BAR_LINE_RULE = "URBAN_QTO_LOCAL_BAR_LINE_V1"
URBAN_OWNER_MEASUREMENT_RULE = "URBAN_OWNER_MEASUREMENT_RULE"
PROJECT_SOURCE_EXPLICIT = "PROJECT_SOURCE_EXPLICIT"


def top_extent(local_clear_span_mm, *, fraction=1.0 / 3.0, origin_explicit=None):
    """The extent of a top-over-support bar into one panel. With an origin stated by the source it is
    PROJECT_SOURCE_EXPLICIT; with none, the Urban rule: fraction x local clear span from the support face."""
    if local_clear_span_mm is None or local_clear_span_mm <= 0:
        raise SlabQtoError("a positive local clear span is required")
    v = fraction * float(local_clear_span_mm)
    if origin_explicit:
        return {"extent_mm": v, "origin": origin_explicit, "authority": PROJECT_SOURCE_EXPLICIT,
                "extent_basis": EXTENT_PROJECT_RULE}
    return {"extent_mm": v, "origin": SR.FACE_OF_SUPPORT, "rule_id": URBAN_TOP_EXTENT_RULE,
            "authority": URBAN_OWNER_MEASUREMENT_RULE, "extent_basis": EXTENT_URBAN_RULE}


# ------------------------------------------------------------------ local override, mismatch, ownership
LOCAL_SOURCE_OVERRIDE = "LOCAL_SOURCE_OVERRIDE"
GENERAL_RULE_SUPERSEDED_FOR_ROLE = "GENERAL_RULE_SUPERSEDED_FOR_ROLE"
COEXIST = "COEXIST"
ADDITIVE_SECOND_FAMILY = "ADDITIVE_SECOND_FAMILY"


def local_override(*, same_role, same_location, second_family_evidence=False):
    if not (same_role and same_location):
        return {"local": COEXIST, "general": COEXIST, "additive": True}
    if second_family_evidence:
        return {"local": ADDITIVE_SECOND_FAMILY, "general": COEXIST, "additive": True}
    return {"local": LOCAL_SOURCE_OVERRIDE, "general": GENERAL_RULE_SUPERSEDED_FOR_ROLE, "additive": False}


TRANSITION_PARTS = ("CROSS_SUPPORT_CONTINUATION", "LAP", "SPLICE", "DEVELOPMENT", "TRANSITION")


def mismatch_split(support_id, left, right):
    """left / right: {"family", "dia_mm", "rate"} (None when the side has no resolved family). Equal specs keep one
    run across the support; anything else is two runs to the support face and a blocked transition."""
    same = (left is not None and right is not None and left.get("dia_mm") == right.get("dia_mm") and
            left.get("rate") == right.get("rate") and left.get("dia_mm") is not None and left.get("rate") is not None)
    if same:
        return {"support": support_id, "state": "ONE_RUN_ACROSS_SUPPORT", "runs": [], "blocked": []}
    runs = [{"run": f"{support_id}:LEFT_PANEL_BAR_RUN", "family": (left or {}).get("family"), "to": "SUPPORT_FACE"},
            {"run": f"{support_id}:RIGHT_PANEL_BAR_RUN", "family": (right or {}).get("family"), "to": "SUPPORT_FACE"}]
    return {"support": support_id, "state": "SPLIT_AT_SUPPORT", "runs": runs,
            "blocked": [{"part": p, "state": BLOCKED_UNQUANTIFIED} for p in TRANSITION_PARTS],
            "chosen_by": None}


TRANSFERRED_S8 = "TRANSFERRED_S8"


def ownership_transfer(object_id, *, kind, to_stage, region, reason, conflict_preserved=False):
    if not to_stage or not region:
        raise SlabQtoError("a transfer names its stage and region")
    return {"object_id": object_id, "kind": kind, "from_stage": "S7", "to_stage": to_stage, "region": region,
            "reason": reason, "state": TRANSFERRED_S8, "quantity_lost": False,
            "source_conflict_preserved": bool(conflict_preserved)}


def transfer_conservation(before_ids, terminal):
    """terminal: {object id: state}. Every object terminates exactly once; nothing transferred is lost."""
    b = list(before_ids)
    return {"every_object_once": sorted(b) == sorted(terminal) and len(set(b)) == len(b),
            "no_unknown": set(terminal) <= set(b)}


# ------------------------------------------------------------------ sunken slabs, dense hatch
SUNKEN_EXTRAS = ("SUNKEN_STEP_VERTICAL_REBAR", "SUNKEN_EDGE_EXTRA", "LEVEL_CHANGE_DETAIL")


def sunken_decision(*, boundary, callout, thickness, supports, specified_extras=()):
    """A sunken panel keeps its normal mesh in S7 when its boundary, callout, thickness and supports are known; the
    step extras are separate and blocked unless specified."""
    known = {"boundary": bool(boundary), "callout": bool(callout), "thickness": bool(thickness),
             "supports": bool(supports)}
    mesh = "RETAINED_IN_S7" if all(known.values()) else BLOCKED_UNQUANTIFIED
    extras = {x: ("SPECIFIED" if x in specified_extras else BLOCKED_UNQUANTIFIED) for x in SUNKEN_EXTRAS}
    return {"mesh": mesh, "known": known, "extras": extras}


CANTILEVER_CANDIDATE = "CANTILEVER_CANDIDATE"
BEARING_WALL_CANDIDATE = "BEARING_WALL_CANDIDATE"


def _seg_on_line(seg, horizontal, coord, lo, hi, tol):
    (x0, y0), (x1, y1) = seg
    if horizontal:
        if abs(y0 - coord) > tol or abs(y1 - coord) > tol:
            return 0.0
        a, b = sorted((x0, x1))
    else:
        if abs(x0 - coord) > tol or abs(x1 - coord) > tol:
            return 0.0
        a, b = sorted((y0, y1))
    return max(0.0, min(b, hi) - max(a, lo))


def hatch_classification(rect, *, structural_lines, slab_faces_beyond=None, tol=5.0, min_cover=0.8):
    """rect (x0, y0, x1, y1) of a strip drawn with a hatch that the legend gives two meanings. Geometry decides:
      both long sides lie on structural lines (the strip fills a support band) -> BEARING_WALL_CANDIDATE
      one long side on a structural line, the other side free and no slab face beyond it -> CANTILEVER_CANDIDATE
      anything else -> CLASSIFICATION_BLOCKED. slab_faces_beyond(side) -> True when a slab face lies beyond that side.
    """
    x0, y0, x1, y1 = rect
    horizontal = (x1 - x0) >= (y1 - y0)
    lo, hi = (x0, x1) if horizontal else (y0, y1)
    sides = {"LOW": y0 if horizontal else x0, "HIGH": y1 if horizontal else x1}
    cover = {}
    for k, c in sides.items():
        got = sum(_seg_on_line(s, horizontal, c, lo, hi, tol) for s in structural_lines)
        cover[k] = min(1.0, got / max(hi - lo, TOL))
    ev = {"long_axis": "X" if horizontal else "Y", "width_mm": (y1 - y0) if horizontal else (x1 - x0),
          "length_mm": hi - lo, "line_cover": {k: round(v, 3) for k, v in cover.items()}}
    on = [k for k, v in cover.items() if v >= min_cover]
    if len(on) == 2:
        return {"state": BEARING_WALL_CANDIDATE, "why": "both long sides lie on structural lines: the strip fills a "
                                                        "support band", "evidence": ev}
    if len(on) == 1:
        free = "HIGH" if on[0] == "LOW" else "LOW"
        beyond = slab_faces_beyond(free) if slab_faces_beyond else None
        ev["slab_beyond_free_side"] = beyond
        if cover[free] < TOL and beyond is False:
            return {"state": CANTILEVER_CANDIDATE, "why": "attached along one structural line, free on the other "
                                                          "side, no slab beyond", "evidence": ev}
    return {"state": SR.CLASSIFICATION_BLOCKED, "why": "geometry does not decide", "evidence": ev}


# ------------------------------------------------------------------ edge continuity
OTHER_SIDE_ABSENT = ("NO_SLAB", "OUTSIDE_BUILDING", "VOID", "OPEN_TO_BELOW")
OTHER_SIDE_PHYSICAL = ("SLAB_IN_SCOPE", "SLAB_EXCLUDED_SPECIAL", "SLAB_CLASSIFICATION_BLOCKED", "SLAB_TRANSFERRED",
                       "CANTILEVER_CANDIDATE")


def edge_continuity(*, other_side, support_kind="BEAM", level_step=False):
    if other_side in OTHER_SIDE_ABSENT:
        return {"state": SR.NON_CONTINUOUS, "why": f"no structural slab beyond ({other_side})"}
    if other_side not in OTHER_SIDE_PHYSICAL:
        raise SlabQtoError(f"unknown other side {other_side}")
    if other_side != "SLAB_IN_SCOPE":
        return {"state": SR.CONTINUITY_UNRESOLVED, "why": f"a physical slab exists beyond ({other_side}); its "
                                                          "analysis is elsewhere, not absent"}
    if level_step:
        return {"state": SR.CONTINUITY_UNRESOLVED, "why": "slab beyond at another level (step not detailed)"}
    if support_kind != "BEAM":
        return {"state": SR.CONTINUITY_UNRESOLVED, "why": f"slab beyond over a {support_kind} support (the typical "
                                                          "detail is slab on beams)"}
    return {"state": SR.CONTINUOUS, "why": "slab on both sides at one level over a beam"}


# ------------------------------------------------------------------ cover, temperature, independence
def cover_lane(cover_basis):
    """A minimum cover used as a number is a project basis, never a source-exact length."""
    b = cover_basis.get("basis") if isinstance(cover_basis, dict) else cover_basis
    if b in ("MINIMUM_PROJECT_COVER",):
        return {"lane": PROJECT_BASIS_QTO, "extent_basis": EXTENT_MINIMUM_COVER, "never": list(FORBIDDEN_LABELS)}
    if b in ("EXACT_PROJECT_COVER", "DETAIL_EXACT"):
        return {"lane": SOURCE_DERIVED_PHYSICAL, "extent_basis": EXTENT_SOURCE_DIMENSION}
    return {"lane": BLOCKED_UNQUANTIFIED, "extent_basis": EXTENT_BLOCKED}


def temperature_item(thickness_mm, table):
    row = SR.temperature_row(thickness_mm, table)
    if row["state"] != SR.TABLE_EXACT_ROW:
        return {"lane": BLOCKED_UNQUANTIFIED, "table_state": row["state"], "interpolated": False, "value": None}
    return {"lane": None, "table_state": row["state"], "interpolated": False, "value": row["value"]}


def component_state(items):
    """A component's state comes from its own items only (blocking never propagates between components)."""
    lanes = [i["lane"] for i in items]
    if not lanes:
        raise SlabQtoError("a component has at least one item")
    for x in lanes:
        if x not in LANES + (TRANSFERRED_S8, GENERAL_RULE_SUPERSEDED_FOR_ROLE):
            raise SlabQtoError(f"unknown item state {x}")
    s7 = [x for x in lanes if x in LANES]
    if not s7:
        return TRANSFERRED_S8 if all(x == TRANSFERRED_S8 for x in lanes) else GENERAL_RULE_SUPERSEDED_FOR_ROLE
    rel = [x for x in s7 if x in RELEASED_LANES]
    if rel and len(rel) == len(s7):
        return "RELEASED_ALL"
    return "RELEASED_PARTIAL" if rel else "BLOCKED"


# ------------------------------------------------------------------ geometry: local bar strips
def polygon_area(ring):
    a = 0.0
    for i in range(len(ring)):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % len(ring)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def edge_crossing_direction(a, b):
    """The bar direction that crosses an edge squarely: X for a near-vertical edge, Y for a near-horizontal one."""
    return "X" if abs(b[0] - a[0]) < abs(b[1] - a[1]) else "Y"


def _local(p, direction):
    return (p[0], p[1]) if direction == "X" else (p[1], p[0])


def bar_strips(polygon, holes=(), direction="X", tol=1e-6, extra_breaks=()):
    """Cut a polygon (with holes) into strips for bars in `direction`. Each strip [t0, t1] (transverse coordinate)
    holds one interval per inside run; an interval starts and ends on fixed edges (ring index, edge index), its run
    is s_end - s_start, linear in t. Returns intervals with L0 / L1 at t0 / t1 and their exact integral.
    extra_breaks: further transverse coordinates to cut at (e.g. the corners of neighbouring faces, so that what lies
    beyond each strip end is also fixed inside the strip)."""
    if direction not in ("X", "Y"):
        raise SlabQtoError("direction is X or Y")
    rings = [list(polygon)] + [list(h) for h in holes or ()]
    R = [[_local(p, direction) for p in r] for r in rings]
    own = sorted({p[1] for r in R for p in r})
    ts = sorted(set(own) | {t for t in extra_breaks if own[0] < t < own[-1]})
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 <= tol:
            continue
        tm = 0.5 * (t0 + t1)
        xs = []
        for ri, r in enumerate(R):
            n = len(r)
            for i in range(n):
                a, b = r[i], r[(i + 1) % n]
                if (a[1] < tm) != (b[1] < tm):
                    def s_at(t, a=a, b=b):
                        return a[0] + (b[0] - a[0]) * (t - a[1]) / (b[1] - a[1])
                    xs.append((s_at(tm), s_at(t0), s_at(t1), ri, i))
        xs.sort()
        if len(xs) % 2:
            raise SlabQtoError("open polygon: odd crossings")
        for k in range(0, len(xs), 2):
            lo, hi = xs[k], xs[k + 1]
            L0, L1 = hi[1] - lo[1], hi[2] - lo[2]
            out.append({"t0": t0, "t1": t1, "start_edge": (lo[3], lo[4]), "end_edge": (hi[3], hi[4]),
                        "s_start": (lo[1], lo[2]), "s_end": (hi[1], hi[2]), "L0": L0, "L1": L1,
                        "width": t1 - t0, "integral": 0.5 * (L0 + L1) * (t1 - t0)})
    return out


def strips_integral(strips, factor=1.0):
    return factor * sum(s["integral"] for s in strips)


def strips_reconcile(polygon, holes=(), direction="X", rel_tol=1e-9):
    st = bar_strips(polygon, holes, direction)
    area = polygon_area(polygon) - sum(polygon_area(h) for h in holes or ())
    got = strips_integral(st)
    return {"area": area, "integral": got, "reconciled": abs(got - area) <= rel_tol * max(area, 1.0)}


def edge_projection(a, b, direction):
    """Transverse range and along-bar coordinate of an edge, in the strip frame of `direction`."""
    pa, pb = _local(a, direction), _local(b, direction)
    if abs(pb[1] - pa[1]) <= TOL:
        return None
    lo, hi = sorted((pa[1], pb[1]))

    def s_at(t):
        return pa[0] + (pb[0] - pa[0]) * (t - pa[1]) / (pb[1] - pa[1])
    return {"t0": lo, "t1": hi, "s_at": s_at}


def face_beyond(s0, t, outward, faces, direction, max_gap):
    """Along the bar line t (strip frame of `direction`), from s0 outward (+1 / -1): the first face boundary within
    max_gap. faces: {id: (polygon, holes)}. Returns {"face", "gap", "edge": (a, b)} or None (nothing within reach)."""
    best = None
    for fid, (poly, holes) in faces.items():
        for ring in [poly] + list(holes or ()):
            n = len(ring)
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                pa, pb = _local(a, direction), _local(b, direction)
                if (pa[1] < t) != (pb[1] < t):
                    s = pa[0] + (pb[0] - pa[0]) * (t - pa[1]) / (pb[1] - pa[1])
                    g = (s - s0) * outward
                    if 1e-6 < g <= max_gap and (best is None or g < best["gap"]):
                        best = {"face": fid, "gap": g, "edge": (tuple(a), tuple(b))}
    return best


def crossing_integral(edges_a, edges_b, direction):
    """Bars in `direction` crossing a support between two faces: integral over the shared transverse range of the
    gap between the faces, and the shared width. edges_*: [(a, b)] boundary segments of each side on the support."""
    width, integ, gaps = 0.0, 0.0, []
    for ea in edges_a:
        pa = edge_projection(*ea, direction)
        if pa is None:
            continue
        for eb in edges_b:
            pb = edge_projection(*eb, direction)
            if pb is None:
                continue
            t0, t1 = max(pa["t0"], pb["t0"]), min(pa["t1"], pb["t1"])
            if t1 - t0 <= 1e-6:
                continue
            g0 = abs(pb["s_at"](t0) - pa["s_at"](t0))
            g1 = abs(pb["s_at"](t1) - pa["s_at"](t1))
            width += t1 - t0
            integ += 0.5 * (g0 + g1) * (t1 - t0)
            gaps += [g0, g1]
    return {"width": width, "integral": integ, "gap_min": min(gaps) if gaps else None,
            "gap_max": max(gaps) if gaps else None}


# ------------------------------------------------------------------ bottom-bar decomposition per strip
END_NON_CONTINUOUS = "END_NON_CONTINUOUS"
END_CONTINUOUS_RUN = "END_CONTINUOUS_RUN"          # same specification beyond: the run continues
END_CONTINUOUS_SPLIT = "END_CONTINUOUS_SPLIT"      # structurally continuous, specification differs / unresolved
END_UNRESOLVED = "END_UNRESOLVED"                  # continuity unresolved
END_OBLIQUE = "END_OBLIQUE"                        # the bar meets a support it does not cross squarely
END_NO_SUPPORT = "END_NO_SUPPORT_RECORD"           # a boundary edge with no support record
END_OPENING = "END_OPENING"                        # a hole / opening boundary
END_CLASSES = (END_NON_CONTINUOUS, END_CONTINUOUS_RUN, END_CONTINUOUS_SPLIT, END_UNRESOLVED, END_OBLIQUE,
               END_NO_SUPPORT, END_OPENING)
_CURTAIL = (END_CONTINUOUS_RUN, END_CONTINUOUS_SPLIT)                # 50% stop 0.125 L short of the face
_UNCERTAIN = (END_UNRESOLVED, END_OBLIQUE, END_NO_SUPPORT)           # stop zone exists only if continuous


def bottom_strip_items(L0, L1, width, end_start, end_end, *, stop_fraction=0.125, split=(0.5, 0.5)):
    """The density items of one strip interval of a bottom family under a stated 50/50 curtailment rule.
    Released: the in-panel portions (face to face, curtailed half shortened by stop_fraction x L at each continuous
    end and at each end whose continuity is unresolved). Blocked: the stop zones at unresolved ends (present only if
    the support is non-continuous) and every portion beyond a face (anchorage, transition, end detail). The crossing
    of a continuous support is not here: it belongs to the support, once."""
    ends = (end_start, end_end)
    for e in ends:
        if e not in END_CLASSES:
            raise SlabQtoError(f"unknown end class {e}")
    mean = 0.5 * (L0 + L1)
    n_c = sum(e in _CURTAIL for e in ends)
    n_u = sum(e in _UNCERTAIN for e in ends)
    items = []
    if n_c == 0 and n_u == 0:
        items.append({"item": "IN_PANEL", "density_fraction": 1.0, "run_factor": 1.0, "lane_hint": "RELEASE",
                      "integral": mean * width, "width": width})
    else:
        cont, curt = split
        items.append({"item": "IN_PANEL_CONTINUING", "density_fraction": cont, "run_factor": 1.0,
                      "lane_hint": "RELEASE", "integral": mean * width, "width": width})
        k = 1.0 - stop_fraction * (n_c + n_u)
        items.append({"item": "IN_PANEL_CURTAILED", "density_fraction": curt, "run_factor": k,
                      "lane_hint": "RELEASE", "integral": k * mean * width, "width": width})
        for i, e in enumerate(ends):
            if e in _UNCERTAIN:
                items.append({"item": "STOP_ZONE_UNRESOLVED", "end": i, "end_class": e, "density_fraction": curt,
                              "run_factor": stop_fraction, "lane_hint": "BLOCK", "integral": None, "width": width,
                              "why": "present only if the support is non-continuous"})
    for i, e in enumerate(ends):
        if e == END_NON_CONTINUOUS:
            items.append({"item": "END_ANCHORAGE", "end": i, "end_class": e, "density_fraction": 1.0,
                          "lane_hint": "BLOCK", "integral": None, "width": width,
                          "why": "bar end into the non-continuous support: shape only"})
        elif e == END_OPENING:
            items.append({"item": "END_DETAIL_AT_OPENING", "end": i, "end_class": e, "density_fraction": 1.0,
                          "lane_hint": "BLOCK", "integral": None, "width": width, "why": "opening end detail"})
        elif e == END_CONTINUOUS_SPLIT:
            items.append({"item": "TRANSITION", "end": i, "end_class": e, "density_fraction": split[0],
                          "lane_hint": "BLOCK", "integral": None, "width": width,
                          "why": "continuation / lap / splice / development across the support not established"})
        elif e in _UNCERTAIN:
            items.append({"item": "BEYOND_FACE_UNRESOLVED", "end": i, "end_class": e, "density_fraction": None,
                          "lane_hint": "BLOCK", "integral": None, "width": width,
                          "why": "anchorage or continuation depends on the unresolved support"})
    return items


def item_density_check(items):
    """At any point of the strip the released densities never exceed 1 (no physical group is counted twice)."""
    rel = [i for i in items if i["lane_hint"] == "RELEASE"]
    return abs(sum(i["density_fraction"] for i in rel) - 1.0) <= TOL
