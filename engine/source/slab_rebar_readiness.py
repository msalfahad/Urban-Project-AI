"""SLAB REBAR READINESS - what an elevated structural slab may release to an accurate rebar takeoff (generic, no kg).

A readiness model only: it decides scope, thickness, rule applicability, bar runs, support ownership, opening
effects, count bases and token termination. It never computes a bar length total or a mass. Project facts live in
the project's source registers; nothing here names a project, a floor, a panel or a handle.

Scope (exactly one per physical slab-plan geometry):
  IN_SCOPE_S7                    an elevated structural slab panel supported by beams / walls
  EXCLUDED_SPECIAL_STRUCTURE     stair, landing, dome, lift pit, pool, water tank, parapet, ground slab, ... (S8)
  NOT_SLAB                       outside the building / court / a plan region with no slab of this sheet
  VOID_OR_OPENING                open to below, shaft, light well
  CLASSIFICATION_BLOCKED         the evidence cannot assign it (e.g. a void that also carries slab bars / a thickness
                                 mark, or a slab face designated for a special use)

Thickness precedence: LOCAL_PANEL > FLOOR_RULE > PROJECT_DEFAULT. Two different values at the same level are a
SOURCE_CONFLICT; nothing is chosen by nearest value or majority.

Temperature table: an exact row only. A thickness with no row is TABLE_NO_EXACT_ROW (no interpolation, no rounding
to a neighbouring row).

Lengths carry exactly one state: EXACT_PROJECT_LENGTH, LOWER_BOUND, UPPER_BOUND, PROJECT_BASIS_NUMERIC or
BLOCKED_UNQUANTIFIED (cover_authority directions: EXACT / LOWER / UPPER / NONE). A minimum cover makes the straight
run at that cover a maximum, never an exact length and never a lower bound.

Support / curtailment rules release a numeric extent only when the span basis L, the bar direction, the support type
and the measurement origin are all known. The span basis is read from the project detail; it is never carried over
from another member type.

Bars: one physical bar is counted once. A continuous bar crossing several panels is one bar run; a support top bar
belongs to the support, not to each adjacent panel. A spacing count keeps RATE, DISTRIBUTION_WIDTH and COUNT_RULE
apart; without an explicit project rule the count basis (and the edge bar) is unresolved. An opening is reasoned
bar direction by bar direction; opening extra / trim bars are separate records, never netted against deductions.
"""

from __future__ import annotations

import math
import re

from engine.source import cover_authority as CA
from engine.source import graphic_evidence as GE

TOL = 1e-9


class SlabReadinessError(ValueError):
    pass


# ------------------------------------------------------------------ scope
IN_SCOPE = "IN_SCOPE_S7"
EXCLUDED_SPECIAL = "EXCLUDED_SPECIAL_STRUCTURE"
NOT_SLAB = "NOT_SLAB"
VOID_OR_OPENING = "VOID_OR_OPENING"
CLASSIFICATION_BLOCKED = "CLASSIFICATION_BLOCKED"
SCOPES = (IN_SCOPE, EXCLUDED_SPECIAL, NOT_SLAB, VOID_OR_OPENING, CLASSIFICATION_BLOCKED)
SPECIAL_KINDS = ("STAIR", "STAIR_LANDING", "DOME", "LIFT_PIT", "POOL", "WATER_TANK", "PARAPET", "GROUND_SLAB",
                 "SPECIAL_FOUNDATION", "SPECIAL_ROOF_STRUCTURE", "ISOLATED_SPECIAL_BEAM")
SOURCE_CONFLICT = "SOURCE_CONFLICT"


def scope_decision(*, slab_face, outside=False, void=False, special=(), designated_special=(), slab_evidence=False):
    """One scope for one plan geometry.

    slab_face: the geometry is a face of the slab plan; outside: it lies outside the building / slab of this sheet;
    void: open-to-below evidence (X, VOID text); special: special-structure kinds whose evidence is the geometry's
    own (treads, dome radials); designated_special: a slab face designated for a special use (a note, a cloud);
    slab_evidence: slab reinforcement or a slab thickness mark inside the geometry."""
    special, designated = set(special), set(designated_special)
    bad = (special | designated) - set(SPECIAL_KINDS)
    if bad:
        raise SlabReadinessError(f"unknown special kinds {sorted(bad)}")
    if void and (slab_evidence or special):
        return {"scope": CLASSIFICATION_BLOCKED, "conflict": SOURCE_CONFLICT,
                "why": "open-to-below evidence and slab / special-structure evidence in the same geometry"}
    if void:
        return {"scope": VOID_OR_OPENING, "conflict": None, "why": "open-to-below evidence"}
    if special:
        return {"scope": EXCLUDED_SPECIAL, "conflict": None, "special": sorted(special),
                "why": "special-structure evidence: goes to the special-structures round"}
    if outside:
        if slab_evidence:
            return {"scope": CLASSIFICATION_BLOCKED, "conflict": SOURCE_CONFLICT,
                    "why": "outside face with slab evidence"}
        return {"scope": NOT_SLAB, "conflict": None, "why": "no slab of this sheet"}
    if designated:
        return {"scope": CLASSIFICATION_BLOCKED, "conflict": None, "special": sorted(designated),
                "why": "slab face designated for a special use: normal slab or special structure is not established"}
    if slab_face:
        return {"scope": IN_SCOPE, "conflict": None, "why": "elevated structural slab panel"}
    return {"scope": CLASSIFICATION_BLOCKED, "conflict": None, "why": "not a slab face and no other evidence"}


# ------------------------------------------------------------------ thickness
LOCAL_PANEL = "LOCAL_PANEL"
FLOOR_RULE = "FLOOR_RULE"
PROJECT_DEFAULT = "PROJECT_DEFAULT"
THICKNESS_LEVELS = (LOCAL_PANEL, FLOOR_RULE, PROJECT_DEFAULT)
THICKNESS_UNRESOLVED = "THICKNESS_UNRESOLVED"


def thickness_decision(*, local=(), floor=(), default=()):
    """LOCAL_PANEL > FLOOR_RULE > PROJECT_DEFAULT. Each argument is the list of values (mm) found at that level."""
    levels = ((LOCAL_PANEL, local), (FLOOR_RULE, floor), (PROJECT_DEFAULT, default))
    found = {lv: sorted({float(v) for v in vals if v is not None}) for lv, vals in levels}
    for lv, _ in levels:
        vs = found[lv]
        if len(vs) > 1:
            return {"value_mm": None, "authority": SOURCE_CONFLICT, "level": lv, "values_mm": vs, "overridden": []}
        if vs:
            lower = [{"level": o, "values_mm": found[o]} for o in THICKNESS_LEVELS[THICKNESS_LEVELS.index(lv) + 1:]
                     if found[o]]
            return {"value_mm": vs[0], "authority": lv, "level": lv, "values_mm": vs, "overridden":
                    [o for o in lower if o["values_mm"] != vs],
                    "confirms": [o["level"] for o in lower if o["values_mm"] == vs]}
    return {"value_mm": None, "authority": THICKNESS_UNRESOLVED, "level": None, "values_mm": [], "overridden": []}


# ------------------------------------------------------------------ temperature table
TABLE_EXACT_ROW = "TABLE_EXACT_ROW"
TABLE_NO_EXACT_ROW = "TABLE_NO_EXACT_ROW"
TEMPERATURE_THICKNESS_UNRESOLVED = "BLOCKED_THICKNESS_UNRESOLVED"


def temperature_row(thickness_mm, table):
    """Exact row of a thickness -> reinforcement table, or TABLE_NO_EXACT_ROW. Never interpolates; the bracketing
    rows are context only and carry no value."""
    rows = {float(k): v for k, v in table.items()}
    if thickness_mm is None:
        return {"state": TEMPERATURE_THICKNESS_UNRESOLVED, "row": None, "value": None, "interpolated": False}
    t = float(thickness_mm)
    if t in rows:
        return {"state": TABLE_EXACT_ROW, "row": t, "value": rows[t], "interpolated": False}
    below = max((k for k in rows if k < t), default=None)
    above = min((k for k in rows if k > t), default=None)
    return {"state": TABLE_NO_EXACT_ROW, "row": None, "value": None, "interpolated": False,
            "bracket_context_only": [below, above]}


# ------------------------------------------------------------------ cover and length states
EXACT_PROJECT_LENGTH = "EXACT_PROJECT_LENGTH"
LOWER_BOUND = "LOWER_BOUND"
UPPER_BOUND = "UPPER_BOUND"
PROJECT_BASIS_NUMERIC = "PROJECT_BASIS_NUMERIC"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
LENGTH_STATES = (EXACT_PROJECT_LENGTH, LOWER_BOUND, UPPER_BOUND, PROJECT_BASIS_NUMERIC, BLOCKED_UNQUANTIFIED)
_LENGTH_OF = {CA.EXACT: EXACT_PROJECT_LENGTH, CA.LOWER: LOWER_BOUND, CA.UPPER: UPPER_BOUND,
              CA.NONE: PROJECT_BASIS_NUMERIC}


# English minimum phrasings the frozen cover_authority vocabulary does not list ("shall not be less than");
# cover_authority itself is frozen with D1.2 and is not edited
_MIN_EXTRA = re.compile(r"\bnot\s+be\s+less\s+than\b|\bno\s+less\s+than\b|\bnot\s+to\s+be\s+less\s+than\b", re.I)


def cover_wording_kind(text):
    if _MIN_EXTRA.search(str(text or "")):
        return CA.MINIMUM
    return CA.wording_kind(text)


def cover_basis(rule_text, value_mm, *, detail_exact_mm=None):
    """The cover basis a cover rule supports (cover_authority): a minimum stays a minimum unless a detail fixes it."""
    return CA.classify_cover_basis(rule_kind=cover_wording_kind(rule_text), value_mm=value_mm,
                                   detail_exact_mm=detail_exact_mm)


def length_state(direction, *, blocked=False):
    """EXACT -> EXACT_PROJECT_LENGTH, LOWER -> LOWER_BOUND, UPPER -> UPPER_BOUND, NONE -> PROJECT_BASIS_NUMERIC."""
    if blocked:
        return BLOCKED_UNQUANTIFIED
    if direction not in _LENGTH_OF:
        raise SlabReadinessError(f"unknown direction {direction!r}")
    return _LENGTH_OF[direction]


def straight_run_state(dimension_mm, basis, *, unquantified_ends=0):
    """State of a straight run between two covers on a cover basis, with unquantified end portions (legs, hooks,
    anchorage) that can only add length."""
    claim = CA.straight_run_claim(dimension_mm, basis)
    if claim["state"] == CA.STRAIGHT_RUN_UNRESOLVED:
        return {"state": BLOCKED_UNQUANTIFIED, "run": claim}
    d = CA.with_unquantified_additions(claim["direction"], unquantified_ends)
    return {"state": length_state(d), "run": claim, "direction": d}


# ------------------------------------------------------------------ spans
CLEAR_SPAN = "CLEAR_SPAN"
SUPPORT_CENTERLINE = "SUPPORT_CENTERLINE"
PANEL_LENGTH = "PANEL_LENGTH"
OTHER = "OTHER"
L_UNDEFINED = "L_UNDEFINED"
L_BASES = (CLEAR_SPAN, SUPPORT_CENTERLINE, PANEL_LENGTH, OTHER, L_UNDEFINED)
DEFINED_L_BASES = (CLEAR_SPAN, SUPPORT_CENTERLINE, PANEL_LENGTH)


def spans(clear_mm, width_start_mm=None, width_end_mm=None):
    """Clear span and support-centreline span (clear + half of each support width; None if a width is unknown)."""
    if clear_mm is None or clear_mm <= 0:
        return {"clear_mm": None, "centreline_mm": None}
    c = float(clear_mm)
    if width_start_mm is None or width_end_mm is None:
        return {"clear_mm": c, "centreline_mm": None}
    return {"clear_mm": c, "centreline_mm": c + float(width_start_mm) / 2 + float(width_end_mm) / 2}


def span_for_basis(basis, *, clear_mm=None, centreline_mm=None, panel_mm=None):
    if basis == CLEAR_SPAN:
        return clear_mm
    if basis == SUPPORT_CENTERLINE:
        return centreline_mm
    if basis == PANEL_LENGTH:
        return panel_mm
    return None


# ------------------------------------------------------------------ support / curtailment rules
CONTINUOUS = "CONTINUOUS"
NON_CONTINUOUS = "NON_CONTINUOUS"
CONTINUITY_UNRESOLVED = "CONTINUITY_UNRESOLVED"
SUPPORT_TYPES = (CONTINUOUS, NON_CONTINUOUS, CONTINUITY_UNRESOLVED)
TOP_NONCONT = "TOP_ANCHOR_NON_CONTINUOUS"
TOP_CONT = "TOP_CONTINUOUS_WHICHEVER_LARGER"
BOTTOM_STOP = "BOTTOM_50PCT_STOP"
RULE_KINDS = (TOP_NONCONT, TOP_CONT, BOTTOM_STOP)
_RULE_FACTOR = {TOP_NONCONT: 0.25, TOP_CONT: 0.30, BOTTOM_STOP: 0.125}
_RULE_SUPPORT = {TOP_NONCONT: NON_CONTINUOUS, TOP_CONT: CONTINUOUS, BOTTOM_STOP: CONTINUOUS}
FACE_OF_SUPPORT = "FACE_OF_SUPPORT"
SUPPORT_CENTRELINE_ORIGIN = "SUPPORT_CENTRELINE"
ORIGINS = (FACE_OF_SUPPORT, SUPPORT_CENTRELINE_ORIGIN)
RELEASABLE = "RELEASABLE"
RULE_BLOCKED = "BLOCKED"


def rule_gate(rule_kind, *, L_basis, direction, support_type, origin):
    """A numeric rule extent may be used only when L, the bar direction, the support type and the origin are known
    and the rule applies to that support type."""
    if rule_kind not in RULE_KINDS:
        raise SlabReadinessError(f"unknown rule kind {rule_kind!r}")
    blockers = []
    if L_basis not in DEFINED_L_BASES:
        blockers.append("L_BASIS_UNKNOWN")
    if direction not in ("X", "Y"):
        blockers.append("DIRECTION_UNKNOWN")
    if support_type not in (CONTINUOUS, NON_CONTINUOUS):
        blockers.append("SUPPORT_TYPE_UNKNOWN")
    elif support_type != _RULE_SUPPORT[rule_kind]:
        blockers.append("RULE_NOT_FOR_THIS_SUPPORT_TYPE")
    if origin not in ORIGINS:
        blockers.append("ORIGIN_UNKNOWN")
    return {"state": RELEASABLE if not blockers else RULE_BLOCKED, "blockers": blockers}


def rule_extent(rule_kind, *, gate, L1_mm, L2_mm=None):
    """Rule extent (mm) measured from the rule's origin: 0.25 L1, 0.30 max(L1, L2), 0.125 L. Refused unless the
    gate is RELEASABLE."""
    if gate["state"] != RELEASABLE:
        raise SlabReadinessError(f"rule blocked: {', '.join(gate['blockers'])}")
    if L1_mm is None or L1_mm <= 0:
        raise SlabReadinessError("a rule extent needs L1")
    if rule_kind == TOP_CONT:
        if L2_mm is None or L2_mm <= 0:
            raise SlabReadinessError("the continuous-support rule needs L1 and L2")
        return _RULE_FACTOR[rule_kind] * max(float(L1_mm), float(L2_mm))
    return _RULE_FACTOR[rule_kind] * float(L1_mm)


def bottom_split(count=None, *, fraction=0.5, which_specified=False):
    """Split of a bottom-bar family into stopped / continuing bars. An odd count or an unknown count is not split by
    choice; which bars stop is a separate fact."""
    which = "SPECIFIED" if which_specified else "WHICH_50_PERCENT_UNRESOLVED"
    if count is None:
        return {"state": "COUNT_BASIS_UNRESOLVED", "stop": None, "continue": None, "which": which}
    n = int(count)
    s = n * fraction
    if abs(s - round(s)) < TOL:
        return {"state": "SPLIT_EXACT", "stop": int(round(s)), "continue": n - int(round(s)), "which": which}
    lo, hi = math.floor(s), math.ceil(s)
    return {"state": "SPLIT_AMBIGUOUS_ODD_COUNT", "stop": [lo, hi], "continue": [n - hi, n - lo], "which": which}


# ------------------------------------------------------------------ counts
COUNT_EXPLICIT = "EXPLICIT_COUNT"
COUNT_BASIS_EXPLICIT = "COUNT_BASIS_EXPLICIT"
COUNT_BASIS_UNRESOLVED = "COUNT_BASIS_UNRESOLVED"
EDGE_BAR_UNRESOLVED = "EDGE_BAR_UNRESOLVED"
COUNT_RULES = {"CEIL": lambda w, s: math.ceil(w / s - 1e-9), "CEIL_PLUS_1": lambda w, s: math.ceil(w / s - 1e-9) + 1,
               "FLOOR_PLUS_1": lambda w, s: math.floor(w / s + 1e-9) + 1}


def spacing_from_rate(bars_per_m):
    if bars_per_m is None or bars_per_m <= 0:
        raise SlabReadinessError("a rate needs a positive number of bars per metre")
    return 1000.0 / float(bars_per_m)


def count_decision(count_mode, value, *, distribution_mm=None, rule=None):
    """EXPLICIT_COUNT -> the printed count. A rate keeps RATE, DISTRIBUTION_WIDTH and COUNT_RULE apart: the
    candidate counts are listed and the basis stays unresolved unless the project states the rule."""
    if count_mode == COUNT_EXPLICIT:
        return {"state": COUNT_EXPLICIT, "count": int(value), "candidates": None, "rate": None,
                "distribution_mm": distribution_mm, "rule": "PRINTED_COUNT"}
    if count_mode != "BARS_PER_METRE":
        raise SlabReadinessError(f"unknown count mode {count_mode!r}")
    s = spacing_from_rate(value)
    cands = None
    if distribution_mm is not None and distribution_mm > 0:
        cands = {k: f(float(distribution_mm), s) for k, f in COUNT_RULES.items()}
    if rule is not None:
        if rule not in COUNT_RULES:
            raise SlabReadinessError(f"unknown count rule {rule!r}")
        return {"state": COUNT_BASIS_EXPLICIT, "count": cands[rule] if cands else None, "candidates": cands,
                "rate": float(value), "spacing_mm": s, "distribution_mm": distribution_mm, "rule": rule}
    return {"state": COUNT_BASIS_UNRESOLVED, "count": None, "candidates": cands, "rate": float(value),
            "spacing_mm": s, "distribution_mm": distribution_mm, "rule": None, "edge_bar": EDGE_BAR_UNRESOLVED,
            "ambiguous": bool(cands) and len(set(cands.values())) > 1}


# ------------------------------------------------------------------ bar runs and supports
def bar_runs(families, links):
    """One physical bar run per connected set of bar families.

    families: [{"family_id", "panel", "direction", "dia_mm", "spacing_mm" | "rate", "count_mode"}]
    links:    [{"support_id", "panels": (a, b), "direction": bars crossing it, "support_type"}]
    Families merge across a CONTINUOUS link in their direction only when diameter and spacing agree; a mismatch is
    recorded, never resolved. Each family belongs to exactly one run, so a continuous bar is counted once."""
    parent = {f["family_id"]: f["family_id"] for f in families}
    by_pd = {}
    for f in families:
        key = (f["panel"], f["direction"])
        if key in by_pd:
            raise SlabReadinessError(f"two bar families for one panel and direction: {key}")
        by_pd[key] = f

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    crossed, mismatches = {}, []
    for ln in links:
        if ln.get("support_type") != CONTINUOUS:
            continue
        a, b = ln["panels"]
        fa, fb = by_pd.get((a, ln["direction"])), by_pd.get((b, ln["direction"]))
        if not fa or not fb:
            continue
        same = (fa["dia_mm"] == fb["dia_mm"] and _spacing(fa) is not None and
                abs(_spacing(fa) - (_spacing(fb) or -1)) < 1e-6 and fa.get("count_mode") == fb.get("count_mode"))
        if not same:
            mismatches.append({"support_id": ln["support_id"], "families": [fa["family_id"], fb["family_id"]],
                               "why": "diameter / spacing differ across a continuous support"})
            continue
        ra, rb = find(fa["family_id"]), find(fb["family_id"])
        if ra != rb:
            parent[rb] = ra
        crossed.setdefault((fa["family_id"], fb["family_id"]), ln["support_id"])
    groups = {}
    for f in families:
        groups.setdefault(find(f["family_id"]), []).append(f)
    runs = []
    for root in sorted(groups, key=lambda r: sorted(f["family_id"] for f in groups[r])):
        fs = sorted(groups[root], key=lambda f: f["family_id"])
        ids = {f["family_id"] for f in fs}
        sup = sorted({s for (a, b), s in crossed.items() if a in ids and b in ids})
        runs.append({"families": [f["family_id"] for f in fs], "panels": [f["panel"] for f in fs],
                     "direction": fs[0]["direction"], "dia_mm": fs[0]["dia_mm"], "spacing_mm": _spacing(fs[0]),
                     "supports_crossed": sup, "multi_panel": len(fs) > 1})
    return {"runs": runs, "mismatches": mismatches}


def _spacing(f):
    if f.get("spacing_mm") is not None:
        return float(f["spacing_mm"])
    if f.get("rate") is not None and f.get("count_mode") == "BARS_PER_METRE":
        return spacing_from_rate(f["rate"])
    return None


EXTERIOR = "EXTERIOR"


def supports_from_edges(edges):
    """Unique supports from panel edge views. A shared edge seen from both panels is one support; a support top bar
    belongs to that support record, not to each panel.

    edges: [{"panel", "neighbour" (None = no slab beyond), "support_ref", "edge_index", "length_mm", "continuity"}]"""
    sup = {}
    for e in edges:
        other = e["neighbour"] or f"{EXTERIOR}:{e['panel']}:{e['edge_index']}"
        key = (e["support_ref"], tuple(sorted((e["panel"], other))))
        rec = sup.setdefault(key, {"support_ref": e["support_ref"], "sides": tuple(sorted((e["panel"], other))),
                                   "views": [], "lengths_mm": [], "continuities": []})
        rec["views"].append((e["panel"], e["edge_index"]))
        rec["lengths_mm"].append(e["length_mm"])
        rec["continuities"].append(e["continuity"])
    out = []
    for key in sorted(sup, key=lambda k: (str(k[0]), k[1])):
        r = sup[key]
        panels_seen = {p for p, _ in r["views"]}
        slab_sides = [s for s in r["sides"] if not str(s).startswith(EXTERIOR)]
        out.append(dict(r, seen_from=sorted(panels_seen),
                        symmetric=len(slab_sides) < 2 or set(slab_sides) <= panels_seen))
    return out


def support_bar_owner(support, bar_tokens):
    """Every top bar drawn at a support is owned by that support once (not once per adjacent panel)."""
    return [{"token": t, "owner": "SUPPORT", "support_ref": support["support_ref"], "sides": support["sides"],
             "counted": 1} for t in bar_tokens]


# ------------------------------------------------------------------ openings
NOT_PRESENT = "NO_BARS_IN_THIS_DIRECTION"
UNAFFECTED = "UNAFFECTED"
INTERRUPTED = "INTERRUPTED"
REMOVED = "REMOVED"


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def opening_effect(opening, families):
    """Effect of an axis-aligned opening on each bar family, direction by direction.

    opening: (x0, y0, x1, y1); families: {"X" | "Y": coverage rectangle (x0, y0, x1, y1) of that bar family, or None}.
    X bars run along x and are spaced in y; a bar is affected when its y lies inside the opening's y-extent and its
    run crosses the opening. The affected band is reported; the number of bars in it depends on the count basis."""
    ox0, oy0, ox1, oy1 = opening
    out = {}
    for d in ("X", "Y"):
        cov = families.get(d)
        if not cov:
            out[d] = {"effect": NOT_PRESENT, "band_mm": None}
            continue
        cx0, cy0, cx1, cy1 = cov
        if d == "X":
            band, along, run = _overlap(oy0, oy1, cy0, cy1), _overlap(ox0, ox1, cx0, cx1), cx1 - cx0
            lim = (max(oy0, cy0), min(oy1, cy1))
        else:
            band, along, run = _overlap(ox0, ox1, cx0, cx1), _overlap(oy0, oy1, cy0, cy1), cy1 - cy0
            lim = (max(ox0, cx0), min(ox1, cx1))
        if band <= TOL or along <= TOL:
            out[d] = {"effect": UNAFFECTED, "band_mm": None}
        else:
            out[d] = {"effect": REMOVED if along >= run - TOL else INTERRUPTED, "band_mm": [lim[0], lim[1]],
                      "band_width_mm": band, "count_in_band": COUNT_BASIS_UNRESOLVED}
    return out


def opening_record(opening_id, *, deductions, extras):
    """Deductions and extra / trim bars stay separate lists; they are never netted."""
    for e in extras:
        if e.get("netted_against"):
            raise SlabReadinessError(f"{opening_id}: an opening extra is never netted against a deduction")
    return {"opening_id": opening_id, "deductions": list(deductions), "extras": list(extras),
            "net_figure": None}


def void_conflict(*, void_marks, slab_marks):
    """A void that also carries slab reinforcement / thickness marks is a source conflict, never decided silently."""
    if void_marks and slab_marks:
        return {"state": SOURCE_CONFLICT, "void_marks": list(void_marks), "slab_marks": list(slab_marks),
                "candidates": ["SLAB", "VOID", "OPENING_EXTRA", "MISBOUND_TEXT"]}
    if void_marks:
        return {"state": "VOID", "void_marks": list(void_marks), "slab_marks": []}
    return {"state": "NO_VOID", "void_marks": [], "slab_marks": list(slab_marks)}


# ------------------------------------------------------------------ graphics
def graphic_length(cls, length_mm, *, basis, nts=False, conditions=None):
    """A drawn bar may give a length only through the graphic-evidence policy (an N.T.S. / shape-only graphic never
    does)."""
    try:
        return {"state": "ADMITTED", "length_mm": GE.admit_length(cls, length_mm, basis=basis, nts=nts,
                                                                  conditions=conditions)}
    except GE.GraphicPolicyError as ex:
        return {"state": BLOCKED_UNQUANTIFIED, "length_mm": None, "why": str(ex)}


# ------------------------------------------------------------------ tokens
BOUND_TO_PANEL = "BOUND_TO_PANEL"
BOUND_TO_SUPPORT = "BOUND_TO_SUPPORT"
BOUND_TO_OPENING = "BOUND_TO_OPENING"
BOUND_TO_MULTI_PANEL_BAR_RUN = "BOUND_TO_MULTI_PANEL_BAR_RUN"
REFERENCE_ONLY = "REFERENCE_ONLY"
DESIGN_NOTE = "DESIGN_NOTE"
DUPLICATE_GRAPHIC = "DUPLICATE_GRAPHIC"
UNBOUND = "UNBOUND"
EXCLUDED_SPECIAL_TOKEN = "EXCLUDED_SPECIAL_STRUCTURE"
TOKEN_STATES = (BOUND_TO_PANEL, BOUND_TO_SUPPORT, BOUND_TO_OPENING, BOUND_TO_MULTI_PANEL_BAR_RUN, REFERENCE_ONLY,
                DESIGN_NOTE, DUPLICATE_GRAPHIC, SOURCE_CONFLICT, UNBOUND, EXCLUDED_SPECIAL_TOKEN)
BAR_PRODUCING = (BOUND_TO_PANEL, BOUND_TO_SUPPORT, BOUND_TO_OPENING, BOUND_TO_MULTI_PANEL_BAR_RUN)


def terminate_token(token_id, state, *, bar_families=(), bound_to=None, reason, explicit_multi=False):
    """One terminal state per token. Only a bound state may produce bars, and a token produces at most one bar
    family unless the source explicitly draws one bar across several panels."""
    if state not in TOKEN_STATES:
        raise SlabReadinessError(f"{token_id}: unknown token state {state!r}")
    fams = list(bar_families)
    if fams and state not in BAR_PRODUCING:
        raise SlabReadinessError(f"{token_id}: a {state} token produces no bars")
    if len(fams) > 1 and not (state == BOUND_TO_MULTI_PANEL_BAR_RUN and explicit_multi):
        raise SlabReadinessError(f"{token_id}: one token, one bar family (multi-panel needs explicit source)")
    if not str(reason).strip():
        raise SlabReadinessError(f"{token_id}: a terminal state states its reason")
    return {"token_id": token_id, "state": state, "bar_families": fams, "bound_to": bound_to, "reason": reason}


def token_conservation(swept_ids, records):
    ids = [r["token_id"] for r in records]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    missing = sorted(set(swept_ids) - set(ids))
    extra = sorted(set(ids) - set(swept_ids))
    fam = [f for r in records for f in r["bar_families"]]
    shared = sorted({f for f in fam if fam.count(f) > 1})
    checks = {"every_token_terminates_once": not dup and not missing, "no_unknown_token": not extra,
              "no_bar_family_from_two_tokens": not shared,
              "only_bound_tokens_produce_bars": all(r["state"] in BAR_PRODUCING or not r["bar_families"]
                                                    for r in records)}
    return {"checks": checks, "all_pass": all(checks.values()), "duplicates": dup, "missing": missing,
            "extra": extra, "shared_families": shared}


# ------------------------------------------------------------------ components
COMPONENT_TYPES = ("BOTTOM_X", "BOTTOM_Y", "TOP_X", "TOP_Y", "TOP_SUPPORT_X", "TOP_SUPPORT_Y", "MID_STRIP_TOP",
                   "COLUMN_STRIP_TOP", "TEMPERATURE_X", "TEMPERATURE_Y", "OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM",
                   "OPENING_TRIM", "EDGE_BAR", "CORNER_BAR", "DIAGONAL_BAR", "CURTAILMENT_SEGMENT",
                   "CONTINUOUS_BAR_RUN", "LAP", "DEVELOPMENT", "HOOK", "BEND")
S7_RELEASE_CANDIDATE = "S7_RELEASE_CANDIDATE"
BLOCKED_FROM_S7 = "BLOCKED_FROM_S7"


def component(component_type, *, owner, project_support, blockers=(), **facts):
    """A component is instantiated only when a project source supports its type; it carries no kg."""
    if component_type not in COMPONENT_TYPES:
        raise SlabReadinessError(f"unknown component type {component_type!r}")
    if not project_support:
        raise SlabReadinessError(f"{component_type}: not instantiated without a project source")
    if "kg" in {k.lower() for k in facts}:
        raise SlabReadinessError("a readiness component carries no kg")
    b = sorted(set(blockers))
    return dict(facts, component=component_type, owner=owner, project_support=project_support, blockers=b,
                readiness=S7_RELEASE_CANDIDATE if not b else BLOCKED_FROM_S7, kg=None)


def population_conservation(geometry_ids, rows, key="id"):
    ids = [r[key] for r in rows]
    checks = {"every_geometry_terminates_once": sorted(ids) == sorted(set(ids)) and set(ids) == set(geometry_ids),
              "every_row_has_one_scope": all(r.get("scope") in SCOPES for r in rows),
              "no_excluded_row_in_scope": all(not (r.get("scope") == IN_SCOPE and r.get("special")) for r in rows)}
    return {"checks": checks, "all_pass": all(checks.values()),
            "missing": sorted(set(geometry_ids) - set(ids)), "extra": sorted(set(ids) - set(geometry_ids))}


def policy_record():
    return {"scopes": list(SCOPES), "special_kinds": list(SPECIAL_KINDS), "thickness_levels": list(THICKNESS_LEVELS),
            "length_states": list(LENGTH_STATES), "l_bases": list(L_BASES), "token_states": list(TOKEN_STATES),
            "component_types": list(COMPONENT_TYPES),
            "rules": ["local panel > floor rule > project default; conflicts are never voted",
                      "a temperature table row is used only on an exact thickness match; no interpolation",
                      "a minimum cover gives a maximum straight run, never an exact length or a lower bound",
                      "a numeric support rule needs L, direction, support type and origin",
                      "a continuous bar and a support top bar are counted once",
                      "rate, distribution width and count rule stay separate; no edge-bar convention is assumed",
                      "openings are reasoned per bar direction; extras are never netted against deductions",
                      "an N.T.S. or shape-only graphic never creates a length",
                      "special structures leave this round; no component carries kg"]}
