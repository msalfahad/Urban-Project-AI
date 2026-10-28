"""T-316 suspended-slab TOP-BAR extent census by support (research ledger, lane S; every villa; stdlib only).

Physical element: the top bars over ONE support of a suspended slab, in one bar direction (a SUPPORT GROUP). At a
continuous support one group = the extent into the panel on each side + the part over the beam band; at an edge beam
one group = the extent into the end span + the part across the edge beam + the hook-down leg. Each side of a group is
booked by the panel line on that side, the part over the band half by each side, the group itself once.

What the governing drawings print (re-read for T-316 at 600 dpi; private copies only):
  * Plan note 2 (p.4 / p.5 / p.6, Arabic, identical on the three sheets): top bars 5 o 10/m over the beams of the slabs
    'with a length of one third of the span in both directions'. Which span, and whether the third is the whole bar or
    the part each side, is not printed (NOTE-BASIS; T-152 readings i = L/6 per side, ii = L/3 per side).
  * ST p.15 TYP. SLAB ON BEAMS DETAIL: continuous support: the top bar runs '.30 L1 OR .30 L2 WHICHEVER LARGER' from the
    support FACE (dimension measured from the face, the bar drawn on both sides, across the band); non-continuous
    support: the 'TOP ANCHOR BAR' runs '.25 L1' from the inner face of the edge beam into the span, across the edge
    beam, and hooks DOWN at the outer face (leg drawn, not dimensioned; the hook is drawn outboard of the bottom bar that
    stops '40 CL.' from the outer face); dashed 'EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE' beyond the
    edge beam (no length). Note 3 of the same sheet: 'WHERE TOP REINF. DIFFERS BETWEEN ADJACENT SPANS USE LARGER REINF.'
    L1 / L2 are the CLEAR spans of the two panels at the support (dimension lines face to face).
  * The structural DXF (layer S-REIN-SLAB, raw lines): every mesh bar line lies inside ONE slab panel; no 5 o 10/m top bar
    is drawn over any support. The only drawn top bars that cross a support carry their own '/Top' labels (beam lane).

Rules R316-1 .. R316-9 (research rules; no rule-file version; provenance T-152, T-306, T-307, Checker T-306 / T-307):
  R316-1  every top-bar end carries one support class (T-307 classes + CANTILEVER_ROOT, the end of a cantilever
          panel at its supporting beam); no class -> refused.
  R316-2  CONTINUOUS (and CONTINUOUS_WIDE_BEAM): p.15 extent each side = 0.30 x max(L_this, L_other) from the face,
          L the clear spans of the two panels on the bar line; the part over the band = w / 2 per side. Using the
          SHORTER span, or the panel's own span when the other span is unknown, is refused: an unknown L_other leaves
          the side HELD (never substituted).
  R316-3  EDGE_BEAM: p.15 in-span extent = 0.25 x L_this from the inner face; the part across the edge beam is drawn
          to the hook at the outer face, outboard of the '40 CL.' bottom-bar end: BOUND [w - 0.040, w] (the top-bar
          cover is not printed); the hook-down leg is HELD (a value offered is refused); concrete beyond the edge beam
          (cantilever strip / other level / not this slab) -> the dashed 50 % extension is UNRESOLVED (blank, never a
          value).
  R316-4  STEP_EDGE / IRREGULAR_SUPPORT / OPENING_EDGE / CANTILEVER_ROOT: p.15 draws no top bar there -> HELD, never
          0, never a continuous or end extent by default.
  R316-5  basis labels kept apart: DRAWING_DERIVED (p.15 extent with drawn spans and widths), NOTE_BASIS (plan note 2
          readings), UNRESOLVED (the 50 % extension, note 3 where top reinforcement differs), HELD. A note length offered
          for a bar the plan DRAWS (a '/Top' bar with a drawn length) is refused.
  R316-6  each group once: one side per panel, at most two sides (continuous) or one side (edge); a panel booking both
          sides of one support, or two records of one side, is refused.
  R316-7  units: lengths in m; a length > 50 reads as mm and is refused.
  R316-8  closure: the T-306 top cause rows of a line split by support class close to the line's cause figures within
          storage rounding (0.0015 kg per 3 dp figure); the residual is booked and named.
  R316-9  kg internal; t = kg / 1000 once at the export boundary (OWNER_RULE_REBAR_2026-10-24 s.1); sums per class /
          status only, never across statuses.
  R316-10 one span, one top steel: the extents of the two groups at the two ends of a bar line never sum past its
          clear span; where p.15 extents would (short span beside a long one), the in-span part is a BOUND [ln,
          min(a, ln) + min(b, ln)] (one through bar .. two overlapping bars, neither drawn), never a + b.
"""

import math
from collections import defaultdict

P15_CONT, P15_END = 0.30, 0.25      # ST p.15 TYP. SLAB ON BEAMS DETAIL (printed factors)
COVER_END_M = 0.040                  # p.15 '40 CL.' (printed, bottom-bar end at the edge beam's outer face)
ROUND_TOL = 0.0015                   # kg per 3 dp stored figure
NOTE2_D = 10                         # plan note 2: 5 o 10/m

CLASSES = ("CONTINUOUS", "CONTINUOUS_WIDE_BEAM", "EDGE_BEAM", "STEP_EDGE", "IRREGULAR_SUPPORT", "OPENING_EDGE",
           "CANTILEVER_ROOT")
HELD_CLASSES = {"STEP_EDGE": "level step at a sunken panel (drop not printed, D-41): p.15 draws one level",
                "IRREGULAR_SUPPORT": "column / junction / oblique or composite support: p.15 draws one square beam",
                "OPENING_EDGE": "no beam face at the slab edge: no top bar end drawn",
                "CANTILEVER_ROOT": "end of a cantilever panel at its supporting beam: its top steel is the "
                                   "cantilever's own main reinforcement, not the p.15 slab-on-beams case"}
CONCRETE_BEYOND = {"EDGE_HELD", "NOT_THIS_SLAB", "NOT_SLAB", "CANTILEVER"}


def kgm(d_mm):
    """unit mass d^2 / 162 kg/m (the project method, as the candidate lines)."""
    return d_mm * d_mm / 162.0


def _m(name, v):
    if v is None:
        return None
    if v < 0:
        raise ValueError(f"{name} negative: {v}")
    if v > 50.0:
        raise ValueError(f"UNIT_REFUSED: {name} = {v} reads as mm, not m (R316-7)")
    return float(v)


# ------------------------------------------------------------------------------------------------ R316-2 .. R316-5
def p15_extent(support, l_this, l_other=None, l_used=None):
    """p.15 in-panel extent of one top-bar side (m). l_used: the span a caller wants to apply; refused unless it is the
    span the detail names (max of the two at a continuous support, the own span at an edge beam)."""
    l_this, l_other, l_used = _m("l_this", l_this), _m("l_other", l_other), _m("l_used", l_used)
    if support in ("CONTINUOUS", "CONTINUOUS_WIDE_BEAM"):
        if l_other is None:
            if l_used is not None:
                raise ValueError("OWN_SPAN_SUBSTITUTED_REFUSED: the other clear span is unknown; the side stays HELD "
                                 "(R316-2)")
            return None
        gov = max(l_this, l_other)
        if l_used is not None and abs(l_used - gov) > 1e-9:
            raise ValueError("SHORTER_SPAN_REFUSED: p.15 '.30 L1 OR .30 L2 WHICHEVER LARGER' (R316-2)")
        return P15_CONT * gov
    if support == "EDGE_BEAM":
        if l_used is not None and abs(l_used - l_this) > 1e-9:
            raise ValueError("WRONG_SPAN_REFUSED: p.15 '.25 L1' at a non-continuous support is the end span's own "
                             "clear span (R316-3)")
        return P15_END * l_this
    if support in HELD_CLASSES:
        if l_used is not None:
            raise ValueError(f"HELD_CLASS_EXTENT_REFUSED: {support}: {HELD_CLASSES[support]} (R316-4)")
        return None
    raise ValueError(f"SUPPORT_CLASS_REFUSED: {support!r} (R316-1)")


def end_record(support, l_this, w=None, l_other=None, beyond="", hook_leg_m=None, offered_basis=None,
               drawn_length_m=None):
    """One top-bar END (one side of a group) -> dict with the p.15 drawn-derived parts, the note-2 readings and the
    held / unresolved items. offered_basis 'NOTE2' with a drawn_length_m (a bar the plan draws) is refused (R316-5)."""
    if support not in CLASSES:
        raise ValueError(f"SUPPORT_CLASS_REFUSED: {support!r} (R316-1)")
    l_this, w = _m("l_this", l_this), _m("w", w)
    if hook_leg_m is not None:
        raise ValueError("HOOK_LEG_VALUE_REFUSED: the hook-down leg is drawn, not dimensioned (R316-3)")
    if drawn_length_m is not None:
        _m("drawn_length_m", drawn_length_m)
        if offered_basis is not None:
            raise ValueError("NOTE_LENGTH_ON_DRAWN_BAR_REFUSED: the plan draws this bar with its length; a note "
                             "extent never replaces it (R316-5)")
        return dict(support=support, status="DRAWN_BAR", in_panel=drawn_length_m, over_band=0.0, across=(0.0, 0.0),
                    held=[], unresolved=[], note2_i=None, note2_ii=None)
    held, unres = [], []
    ext = p15_extent(support, l_this, l_other)
    over, across = 0.0, (0.0, 0.0)
    if support in ("CONTINUOUS", "CONTINUOUS_WIDE_BEAM"):
        if w is None:
            raise ValueError("continuous end without its drawn band width")
        over = w / 2.0
        if ext is None:
            held.append("OTHER_SPAN_UNKNOWN")
        status = "DRAWING_DERIVED" if ext is not None else "HELD"
    elif support == "EDGE_BEAM":
        if w is None or w <= COVER_END_M:
            raise ValueError("EDGE_BEAM end without a drawn width wider than the 40 mm end cover")
        across = (w - COVER_END_M, w)
        held.append("HOOK_DOWN_LEG")
        if beyond in CONCRETE_BEYOND:
            unres.append("EXTEND_50PCT_INTO_ADJACENT_SLAB")
        status = "DRAWING_DERIVED_WITH_HELD"
    else:
        held.append(support)
        status = "HELD"
    return dict(support=support, status=status, in_panel=ext, over_band=over, across=across, held=held,
                unresolved=unres, note2_i=l_this / 6.0, note2_ii=l_this / 3.0)


def span_overlap(ln, ext_lo, ext_hi):
    """R316-10: the two top-bar groups of one bar line (its two supports) cannot together occupy more than the clear
    span ln. Where ext_lo + ext_hi > ln (a short span beside a long one: 0.30 x L_long reaches past the short span),
    p.15 does not draw what happens: one bar through the span (top steel = ln) or two bars overlapping (each limited
    to ln) -> BOUND [ln, min(ext_lo, ln) + min(ext_hi, ln)]; one side HELD -> the valued side is limited to ln.
    -> dict(overlap, cut_low, cut_high) in m, to subtract from the plain sum of the valued extents."""
    ln = _m("ln", ln)
    a, b = _m("ext_lo", ext_lo), _m("ext_hi", ext_hi)
    if a is not None and b is not None:
        s = a + b
        if s <= ln + 1e-9:
            return dict(overlap=False, cut_low=0.0, cut_high=0.0)
        return dict(overlap=True, cut_low=s - ln, cut_high=s - (min(a, ln) + min(b, ln)))
    v = a if a is not None else b
    if v is None or v <= ln + 1e-9:
        return dict(overlap=False, cut_low=0.0, cut_high=0.0)
    return dict(overlap=True, cut_low=v - ln, cut_high=v - ln)


# ------------------------------------------------------------------------------------------------ R316-6
def check_groups(records):
    """records: dicts with group, panel, side_key (bar position / reading tag), books ('THIS' or 'BOTH').
    One side per panel per group; a whole-bar booking from one panel ('BOTH') or a repeated side is refused."""
    seen = set()
    panels = defaultdict(set)
    for r in records:
        if r.get("books", "THIS") != "THIS":
            raise ValueError(f"GROUP_BOTH_SIDES_REFUSED: {r['group']} booked on both sides by {r['panel']} (R316-6)")
        k = (r["group"], r["panel"], r["side_key"])
        if k in seen:
            raise ValueError(f"GROUP_SIDE_TWICE_REFUSED: {k} (R316-6)")
        seen.add(k)
        panels[r["group"]].add(r["panel"])
    for g, ps in panels.items():
        if len(ps) > 2:
            raise ValueError(f"GROUP_MORE_THAN_TWO_SIDES_REFUSED: {g} {sorted(ps)}")
    return {g: sorted(ps) for g, ps in panels.items()}


# ------------------------------------------------------------------------------------------------ T-152 per-end figures
def t152_end(ln, cont, gap, nb_chord):
    """the T-152 booking of one top-bar end (m): readings i, ii, p15 and the crossing (for closure only)."""
    p15 = P15_CONT * max(ln, nb_chord if nb_chord is not None else ln) if cont else P15_END * ln
    return dict(i=ln / 6.0, ii=ln / 3.0, p15=p15, cross=(gap / 2.0) if cont else 0.0)


def line_path(ends_A, ends_B):
    """T-306 decompose_top choices from the per-reading sums: (low reading at A, high reading at B, crossing tag)."""
    names = ("i", "ii", "p15")
    sA = {k: sum(e[k] for _c, e in ends_A) for k in names + ("cross",)}
    sB = {k: sum(e[k] for _c, e in ends_B) for k in names + ("cross",)}
    lo = min(names, key=lambda k: sA[k])
    hi = max(names, key=lambda k: sB[k])
    return lo, hi, ("B" if sB["cross"] >= sA["cross"] else "A")


def split_causes(ends_A, ends_B, lo_r, hi_r, cross_tag="B"):
    """T-306 top causes of one line split by support class (R316-8). ends_X: list of (class, t152_end dict) at count X.
    lo_r / hi_r: the line's low reading at A and high reading at B (T-306 path). -> {cause: {class: m}} (multiply by
    the unit mass)."""
    path = [lo_r]
    if lo_r != "ii" and hi_r != lo_r:
        path.append("ii")
    if hi_r not in path:
        path.append(hi_r)
    out = defaultdict(lambda: defaultdict(float))
    for p, q in zip(path, path[1:]):
        code = "TOP_NOTE2_WORDING" if {p, q} == {"i", "ii"} else "TOP_NOTE2_VS_P15"
        for c, e in ends_A:
            out[code][c] += e[q] - e[p]
    for c, e in ends_B:
        out["COUNT_CONVENTION"][c] += e[hi_r]
    for c, e in (ends_B if cross_tag == "B" else ends_A):
        out["TOP_CROSSING"][c] += e["cross"]
    for c, e in ends_A:
        out["COUNT_CONVENTION"][c] -= e[hi_r]
    return out


def close_line(line_id, causes_line, split_m, u, n_figures=3):
    """R316-8: the class split (m x u) of each cause equals the line's T-306 cause figure within storage rounding."""
    res = {}
    for code, fig in causes_line.items():
        got = sum(split_m.get(code, {}).values()) * u
        r = fig - got
        if abs(r) > ROUND_TOL * n_figures + 1e-9:
            raise ValueError(f"{line_id}: {code} split {got:.6f} vs T-306 {fig:.6f} ({r:+.6f} kg unexplained)")
        res[code] = r
    return res


def tonnes(kg):
    """R316-9: once, at the export boundary."""
    return kg / 1000.0


def isclose(a, b, tol=1e-6):
    return math.isclose(a, b, abs_tol=tol)
