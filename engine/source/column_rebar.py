"""COLUMN REINFORCEMENT ENGINE (generic, project-independent).

Quantifies column reinforcement per STOREY SEGMENT (one column occurrence on one storey). Never TYPE x count: every
kilogram comes from one segment, one candidate definition and one named length kind, so it can be traced back.

Everything that differs between projects is an INPUT:
  - section, bar count / diameter, storey interval and clear-zone depth (from the project's census);
  - the tie rule (diameter, rate, per-metre semantics, zones) and the tie-topology bands with the link sets read from
    the project's detail (which bars each link encloses, in the detail's own bar indices);
  - cover rule, lap / anchorage / starter rules and the hook method, each with its own authority state;
  - project claims (stored with project_claims; applied only when they APPLY to this project + revision + flag).
No mark, storey height, cover, rate, band limit or claim value is written in this module.

Length kinds are kept apart: CORE_VERTICAL_RUN / STARTER / LAP_SPLICE / ANCHORAGE / OTHER_EXTRA for main bars, and
TIE_CORE_PATH / HOOK_1 / HOOK_2 for ties. A hook allowance never enters a core path.

Release reuses engineering_flags: every part carries the facts it depends on; open flags on those facts, the part's own
method basis and (under a type conflict) the agreement of the candidate definitions decide its release state.

Stdlib only.
"""

from __future__ import annotations

import copy
import math
from collections import Counter, defaultdict
from fractions import Fraction

from . import engineering_flags as EF
from . import project_claims as PC
from . import rebar_unit_mass as UM

POLICY_ID = "COLUMN_REBAR_V1"

# topologies of the closed links at one tie level
ONE_LINK = "ONE_LINK"
TWO_OVERLAPPING_LINKS = "TWO_OVERLAPPING_LINKS"
MULTI_LINK_SET = "MULTI_LINK_SET"
CUSTOM_LINK_SET = "CUSTOM_LINK_SET"
TOPOLOGIES = (ONE_LINK, TWO_OVERLAPPING_LINKS, MULTI_LINK_SET, CUSTOM_LINK_SET)

# meaning of a per-metre tie count
SETS_PER_M = "SETS_PER_M"           # n complete tie levels (all links of the topology) per metre
LINKS_PER_M = "LINKS_PER_M"         # n single closed links per metre, shared between the links of a level
UNRESOLVED = "UNRESOLVED"
RATE_SEMANTICS = (SETS_PER_M, LINKS_PER_M, UNRESOLVED)

# tie level count methods
RATE_COUNT = "RATE_COUNT"                   # ceil(rate x zone length)
SPACING_WITH_ENDS = "SPACING_WITH_ENDS"     # ceil(zone length / spacing) + 1
LEVEL_METHODS = (RATE_COUNT, SPACING_WITH_ENDS)

# tie vertical zone scenarios
CLEAR_ZONE = "CLEAR_COLUMN_ZONE"            # up to the soffit of the deepest framing member
FULL_ZONE = "FULL_STOREY"                   # through the joint, the full storey interval
ZONES = (CLEAR_ZONE, FULL_ZONE)

# length kinds
CORE = "CORE_VERTICAL_RUN"
STARTER = "STARTER"
LAP = "LAP_SPLICE"
ANCHORAGE = "ANCHORAGE"
EXTRA = "OTHER_EXTRA"
TIE_CORE = "TIE_CORE_PATH"
HOOK_1 = "HOOK_1"
HOOK_2 = "HOOK_2"
LENGTH_KINDS = (CORE, STARTER, LAP, ANCHORAGE, EXTRA, TIE_CORE, HOOK_1, HOOK_2)

# components (each required component ends in one terminal state)
C_MAIN, C_TIES, C_LAP, C_STARTER, C_ANCH, C_EXTRA = ("MAIN_BARS", "TIES", "LAP", "STARTER", "ANCHORAGE",
                                                     "OTHER_EXTRA")
COMPONENTS = (C_MAIN, C_TIES, C_LAP, C_STARTER, C_ANCH, C_EXTRA)
REQUIRED_COMPONENTS = (C_MAIN, C_TIES, C_LAP, C_STARTER)

VERIFIED = EF.VERIFIED
LOWER_BOUND = EF.LOWER_BOUND
PROVISIONAL = EF.PROVISIONAL_VALUE
BLOCKED = EF.BLOCKED
NOT_REQUIRED = "NOT_REQUIRED"
_RANK = {VERIFIED: 0, PROVISIONAL: 1, LOWER_BOUND: 2, BLOCKED: 4}

_EPS = 1e-06
OCC_STATES = {VERIFIED: "REBAR_COMPLETE", PROVISIONAL: "REBAR_PROVISIONAL", LOWER_BOUND: "REBAR_LOWER_BOUND",
              BLOCKED: "REBAR_BLOCKED", NOT_REQUIRED: "NOT_REQUIRED"}

# interval / zone / rule basis states
ESTABLISHED = "ESTABLISHED"
BOUNDED = "BOUNDED"                 # a safe bound (the true value is not smaller), usable as a lower bound basis
BOUND_LOWER = "LOWER_BOUND"         # interval known only as a minimum
RULE_GAP = "RULE_GAP"
EXACT_RULE = "EXACT_RULE"
RESOLVED_BY_CLAIM = "RESOLVED_BY_CLAIM"

# geometry states of a link
MEASURED = "MEASURED"                       # every edge fixed by section, cover and diameters
DERIVED_BAR_POSITIONS = "DERIVED_BAR_POSITIONS"   # an edge sits on an internal bar placed by the arrangement method

# facts each part depends on (flags touch facts; see engineering_flags.component_release)
FACTS = {
    "MAIN_CORE": ("member_type", "longitudinal_bars", "storey_interval", "occurrence", "boq_item"),
    "LAP": ("member_type", "longitudinal_bars", "lap_method", "occurrence", "boq_item"),
    "ANCHORAGE": ("member_type", "longitudinal_bars", "lap_method", "detailing", "occurrence", "boq_item"),
    "STARTER": ("member_type", "longitudinal_bars", "starter_method", "footing_depth", "occurrence", "boq_item"),
    "TIE_PERIMETER": ("member_type", "section", "cover", "transverse_count", "transverse_zone",
                      "transverse_level_count", "transverse_arrangement", "occurrence", "boq_item"),
    "TIE_INTERNAL": ("member_type", "section", "cover", "transverse_count", "transverse_zone",
                     "transverse_level_count", "transverse_arrangement", "tie_size", "occurrence", "boq_item"),
    "TIE_HOOK": ("member_type", "transverse_count", "transverse_zone", "transverse_level_count",
                 "transverse_arrangement", "tie_hook", "occurrence", "boq_item"),
    "EXTRA": ("special_detail", "detailing", "occurrence", "boq_item"),
    "TRANSITION": ("section_transition", "occurrence", "boq_item"),
}

# transverse notation -> level-count method (an explicit project / owner policy may override)
RATE_PER_M = "RATE_PER_M"           # "n ties/m", "nØd/m": a count per metre
SPACING = "SPACING"                 # "Ød @ s": a spacing
DEFAULT_LEVEL_METHOD = {RATE_PER_M: RATE_COUNT, SPACING: SPACING_WITH_ENDS}


# ================================================================================================ basic quantities
def unit_mass_kg_per_m(dia_mm, density_kg_m3):
    """Mass per metre of a round bar: pi/4 x d^2 x density (d in mm, density in kg/m3)."""
    return math.pi / 4.0 * (dia_mm / 1000.0) ** 2 * density_kg_m3


def _mass_cfg(P):
    """The project's ONE unit-mass method (rebar_unit_mass). Legacy inputs carrying only a density are read as
    EXACT_DENSITY so earlier frozen rounds reproduce."""
    if P.get("unit_mass"):
        return UM.validate(P["unit_mass"])
    return {"method": UM.EXACT_DENSITY, "density_kg_m3": P["steel_density_kg_m3"]}


def _kg(count, length_mm, dia_mm, mass_cfg):
    return count * length_mm / 1000.0 * UM.kg_per_m(dia_mm, mass_cfg)


def parse_transverse_notation(text):
    """'nØd/m', 'n ties/m' -> RATE_PER_M; 'Ød @ s', 'Ød@s mm' -> SPACING. Anything else -> None (no guess)."""
    import re
    t = (text or "").replace("%%c", "\u00d8").replace(" ", "")
    m = re.search(r"(\d+(?:\.\d+)?)(?:\u00d8\d+|ties?|links?|stirrups?)?/m\b", t, re.I)
    if m and "@" not in t:
        return {"notation": RATE_PER_M, "rate_per_m": float(m.group(1))}
    m = re.search(r"@(\d+(?:\.\d+)?)(mm|cm)?", t, re.I)
    if m:
        v = float(m.group(1)) * (10 if (m.group(2) or "").lower() == "cm" else 1)
        return {"notation": SPACING, "spacing_mm": v}
    return None


def level_method(P):
    """Released level-count method from the tie rule's notation and the (owner / project) policy."""
    note = P["tie_rule"].get("notation", RATE_PER_M)
    pol = P.get("level_method_policy") or {}
    return pol.get(note, DEFAULT_LEVEL_METHOD[note])


def _worst(states):
    states = [s for s in states if s and s != NOT_REQUIRED]
    return max(states, key=lambda s: _RANK[s]) if states else NOT_REQUIRED


# ================================================================================================ schedule join
def schedule_row(definitions, column_type, storey, storey_band_of):
    """The one schedule row for (type, storey). storey_band_of maps the project's storey names to schedule band keys.
    Returns (row, state): state DEFINED, NO_ROW or DUPLICATE_ROW - a missing row is never borrowed from a neighbour."""
    band = storey_band_of.get(storey)
    rows = [d for d in definitions if d["column_type"] == column_type and d["storey_band"] == band]
    if not rows:
        rows = [d for d in definitions if d["column_type"] == column_type and d["storey_band"] == storey]
    if len(rows) == 1:
        return rows[0], "DEFINED"
    return (None, "NO_ROW") if not rows else (None, "DUPLICATE_ROW")


# ================================================================================================ claims
def _claim_value(claims, *, context, fact, flag_keys=(), element=None):
    """Value of the single live claim that APPLIES (project + revision + scope) for this fact, else None.
    Adjudications apply through the flag keys of the element; assertions through their member scope."""
    hits = []
    for c in PC.active(claims or []):
        if c["fact"] != fact:
            continue
        if c["kind"] == PC.ADJUDICATION:
            ok = any(PC.applicability(c, project_id=context["project_id"], drawing_revision=context["drawing_revision"],
                                      fact=fact, flag_key=k, claims=claims) == PC.APPLIES for k in flag_keys)
        else:
            ok = PC.applicability(c, project_id=context["project_id"], drawing_revision=context["drawing_revision"],
                                  fact=fact, element=element, claims=claims) == PC.APPLIES
        if ok:
            hits.append(c)
    if len(hits) == 1:
        return hits[0]
    return None


# ================================================================================================ tie topology
def _in_band(v, b):
    lo, hi = b.get("lo_mm"), b.get("hi_mm")
    if lo is not None and (v < lo or (v == lo and not b.get("lo_incl"))):
        return False
    if hi is not None and (v > hi or (v == hi and not b.get("hi_incl"))):
        return False
    return True


def select_band(long_side_mm, bands, *, context, claims=(), flag_keys=(), fact="TIE_TOPOLOGY_BAND"):
    """Topology band for the long side L. A value inside no band is a RULE_GAP; it is resolved only by a claim that
    APPLIES here, adjudicates exactly this L and picks one of the bands adjacent to it (never a far band)."""
    inside = [b for b in bands if _in_band(long_side_mm, b)]
    if len(inside) == 1:
        return {"state": EXACT_RULE, "band": inside[0], "candidates": [inside[0]["band_id"]], "claim_id": None}
    adjacent = [b["band_id"] for b in bands if b.get("lo_mm") == long_side_mm or b.get("hi_mm") == long_side_mm]
    c = _claim_value(claims, context=context, fact=fact, flag_keys=flag_keys)
    if c is not None:
        v = c["value"]
        if v.get("long_side_mm") == long_side_mm and v.get("band_id") in adjacent:
            band = next(b for b in bands if b["band_id"] == v["band_id"])
            return {"state": RESOLVED_BY_CLAIM, "band": band, "candidates": adjacent, "claim_id": c["claim_id"]}
    return {"state": RULE_GAP, "band": None, "candidates": adjacent, "claim_id": None}


def bar_layout(B_mm, D_mm, n_bars, bar_dia, tie_dia, cover_mm, arrangement):
    """Longitudinal bar positions along the long side (L = max(B, D)).
    arrangement: {"method": "CORNERS_PLUS_LONG_FACES"} puts the corner bars and every other bar on the two long faces
    (equal count per face); {"method": "PER_FACE", "per_long_face": k} gives k explicitly.
    Corner bar positions are fixed by cover + tie + bar radius; internal positions use equal spacing - a method, so the
    layout reports which positions are established and which are derived."""
    L, T = max(B_mm, D_mm), min(B_mm, D_mm)
    m = arrangement.get("method")
    if m == "PER_FACE":
        k = arrangement["per_long_face"]
        if 2 * k != n_bars:
            return {"state": BLOCKED, "why": "per-face count does not match the bar count"}
    elif m == "CORNERS_PLUS_LONG_FACES":
        if n_bars < 4 or n_bars % 2:
            return {"state": BLOCKED, "why": "odd or fewer than four bars - long-face arrangement not determined"}
        k = n_bars // 2
    else:
        return {"state": BLOCKED, "why": f"no bar arrangement method ({m})"}
    x0 = cover_mm + tie_dia + bar_dia / 2.0
    x1 = L - cover_mm - tie_dia - bar_dia / 2.0
    s = (x1 - x0) / (k - 1)
    return {"state": ESTABLISHED if k == 2 else DERIVED_BAR_POSITIONS, "L_mm": L, "T_mm": T, "per_long_face": k,
            "positions_mm": [x0 + i * s for i in range(k)], "spacing_mm": s, "x0_mm": x0, "x1_mm": x1,
            "method": m, "internal_positions": "NONE" if k == 2 else "EQUAL_SPACING_METHOD"}


def map_link_ranges(band, per_long_face):
    """Bar-index ranges (per long face) of each link, from the band's detail. ONE_LINK always encloses every bar.
    If the schedule's bars per face differ from the detail's, ranges are scaled (state SCALED_FROM_DETAIL)."""
    topo = band["topology"]
    k = per_long_face
    if topo == ONE_LINK:
        return [[0, k - 1]], EXACT_RULE
    kd = band.get("drawn_bars_per_face")
    links = band.get("links") or []
    if not links or not kd:
        return None, BLOCKED
    if kd == k:
        return [list(x["bar_range"]) for x in links], EXACT_RULE
    f = Fraction(k - 1, kd - 1)
    out = []
    for x in links:
        a, b = x["bar_range"]
        out.append([int(round(float(a * f))), int(round(float(b * f)))])
    return out, "SCALED_FROM_DETAIL"


def link_geometry(B_mm, D_mm, layout, ranges, tie_dia, cover_mm):
    """One closed link per range: centreline rectangle across the short side (fixed by cover) and along the long side
    from the first to the last enclosed bar. Path = 2 x (across + along); no bend deduction or allowance."""
    T, L = min(B_mm, D_mm), max(B_mm, D_mm)
    across = T - 2 * cover_mm - tie_dia
    k = layout["per_long_face"]
    pos = layout["positions_mm"]
    bar_d = 2 * (layout["x0_mm"] - cover_mm - tie_dia)        # bar diameter recovered from the layout
    out = []
    for i, (a, b) in enumerate(ranges, start=1):
        along = (pos[b] - pos[a]) + bar_d + tie_dia
        corners = (a == 0 and b == k - 1)
        state = MEASURED if (a in (0, k - 1) and b in (0, k - 1)) or layout["state"] == ESTABLISHED \
            else DERIVED_BAR_POSITIONS
        out.append({"link_id": f"LINK-{i}", "bar_range_per_long_face": [a, b],
                    "bars_restrained": 2 * (b - a + 1), "encloses_all_bars": corners,
                    "across_mm": across, "along_mm": along, "core_path_mm": 2 * (across + along),
                    "geometry_state": state})
    perimeter = 2 * (across + (L - 2 * cover_mm - tie_dia))
    return out, perimeter


# ================================================================================================ tie levels
def tie_levels(zone_mm, rate_zones):
    """Tie levels over a zone. rate_zones: [{zone_id, rate_per_m, length_mm or None (= the remainder)}].
    RATE_COUNT = sum ceil(rate x length); SPACING_WITH_ENDS = sum ceil(length / spacing) + 1 (one closing level).
    Exact rational arithmetic - a spacing such as 1000/rate mm is never rounded."""
    fixed = sum(Fraction(z["length_mm"]) for z in rate_zones if z.get("length_mm") is not None)
    zone = Fraction(zone_mm)
    rem = zone - fixed
    if rem < 0:
        return {"state": BLOCKED, "why": "fixed tie zones longer than the tie zone"}
    rc = swe = 0
    detail = []
    for z in rate_zones:
        ln = Fraction(z["length_mm"]) if z.get("length_mm") is not None else rem
        r = Fraction(z["rate_per_m"]) if z.get("rate_per_m") is not None else \
            Fraction(1000) / Fraction(z["spacing_mm"])
        n = math.ceil(r * ln / 1000)
        rc += n
        swe += n
        detail.append({"zone_id": z["zone_id"], "length_mm": float(ln), "rate_per_m": float(r),
                       "equivalent_spacing_mm": float(Fraction(1000) / r), "levels_rate_count": n})
    swe += 1
    return {"state": ESTABLISHED, RATE_COUNT: rc, SPACING_WITH_ENDS: swe, "difference": swe - rc, "zones": detail}


def links_from_levels(levels, links_per_level, semantics):
    """Closed links placed for a per-metre count read with the given semantics.
    SETS_PER_M: each counted level carries every link of the topology. LINKS_PER_M: the count is of links, so the
    number of complete levels is count / links per level (rounded up)."""
    if semantics == SETS_PER_M:
        return levels, levels * links_per_level
    lv = math.ceil(Fraction(levels, links_per_level))
    return lv, lv * links_per_level


# ================================================================================================ one candidate
def _part(seg, cand, part_id, component, length_kind, facts_key, count, length_mm, dia, basis, density, **kw):
    kg = None if (count is None or length_mm is None) else _kg(count, length_mm, dia, density)
    return dict({"part_id": f"{seg['segment_id']}|{part_id}", "segment_id": seg["segment_id"],
                 "occurrence_id": seg["occurrence_id"], "candidate_type": cand["type"], "component": component,
                 "length_kind": length_kind, "count": count, "length_per_piece_mm": length_mm, "dia_mm": dia,
                 "total_length_m": None if kg is None else count * length_mm / 1000.0, "kg": kg,
                 "basis_state": basis, "depends_on": list(FACTS[facts_key])}, **kw)


def _ties(seg, cand, P, zone_mm, *, section=None):
    """Tie quantities for one candidate over one zone length; returns dict with link geometry and per-method data."""
    d = cand["definition"]
    B, D = (section or (d["B_mm"], d["D_mm"]))
    tr = P["tie_rule"]
    cov = seg.get("cover") or P["cover"]
    nb, db = d["bars"]["count"], d["bars"]["dia_mm"]
    layout = bar_layout(B, D, nb, db, tr["dia_mm"], cov["cover_mm"], P["bar_arrangement"])
    sel = select_band(max(B, D), P["topology_bands"], context=P["context"], claims=P.get("claims"),
                      flag_keys=seg.get("flag_keys", ()))
    out = {"band": sel, "layout": layout, "section_mm": [B, D], "cover": cov}
    if sel["band"] is None or layout["state"] == BLOCKED:
        out["state"] = BLOCKED
        return out
    ranges, rstate = map_link_ranges(sel["band"], layout["per_long_face"])
    if ranges is None:
        out["state"] = BLOCKED
        return out
    links, perim = link_geometry(B, D, layout, ranges, tr["dia_mm"], cov["cover_mm"])
    sem = tr["per_metre_semantics"]
    sem_claim = None
    if sem == UNRESOLVED:
        c = _claim_value(P.get("claims"), context=P["context"], fact="TIE_RATE_SEMANTICS",
                         flag_keys=seg.get("flag_keys", ()), element={"tie_rule_id": tr["rule_id"]})
        if c is not None and c["value"] in (SETS_PER_M, LINKS_PER_M):
            sem, sem_claim = c["value"], c["claim_id"]
    n_links = len(links)
    eff_sem = sem if sem != UNRESOLVED else (SETS_PER_M if n_links == 1 else LINKS_PER_M)
    lv = tie_levels(zone_mm, tr["zones"]) if zone_mm is not None else {"state": BLOCKED}
    by_method = {}
    if lv["state"] == ESTABLISHED:
        for m in LEVEL_METHODS:
            levels, pieces = links_from_levels(lv[m], n_links, eff_sem)
            by_method[m] = {"levels": levels, "links": pieces}
    hm = P.get("hook_method")
    hook_mm = None if hm is None else max(hm["extension_d"] * tr["dia_mm"], hm["min_extension_mm"])
    out.update({"state": ESTABLISHED, "ranges_state": rstate, "links": links, "perimeter_mm": perim,
                "links_per_level": n_links, "sum_link_paths_mm": sum(x["core_path_mm"] for x in links),
                "semantics": sem, "semantics_used": eff_sem, "semantics_claim": sem_claim, "levels": lv,
                "by_method": by_method, "hook_mm": hook_mm,
                "internal_state": MEASURED if all(x["geometry_state"] == MEASURED for x in links) and
                rstate == EXACT_RULE else DERIVED_BAR_POSITIONS})
    return out


def _tie_parts(seg, cand, P, t, zone_name, zone_state):
    dens = _mass_cfg(P)
    tr = P["tie_rule"]
    parts = []
    if t["state"] == BLOCKED or not t["by_method"]:
        why = "tie topology / bar arrangement not established" if t["state"] == BLOCKED else "tie zone not established"
        parts.append(_part(seg, cand, "TIE_PERIMETER", C_TIES, TIE_CORE, "TIE_PERIMETER", None, None, tr["dia_mm"],
                           BLOCKED, dens, why=why, zone=zone_name))
        return parts
    base_m = level_method(P)
    levels = t["by_method"][base_m]["levels"]
    basis_lb = LOWER_BOUND if zone_state in (ESTABLISHED, BOUNDED, BOUND_LOWER) else BLOCKED
    parts.append(_part(seg, cand, "TIE_PERIMETER", C_TIES, TIE_CORE, "TIE_PERIMETER", levels, t["perimeter_mm"],
                       tr["dia_mm"], basis_lb, dens, zone=zone_name, level_method=base_m,
                       why="outer perimeter path x tie levels: a lower bound of any closed-link set that encloses "
                           "every bar, over the shorter tie zone and the smaller level count"))
    excess = t["sum_link_paths_mm"] - t["perimeter_mm"]
    if t["links_per_level"] > 1 or excess > 1e-9:
        st = PROVISIONAL if basis_lb != BLOCKED else BLOCKED
        parts.append(_part(seg, cand, "TIE_INTERNAL", C_TIES, TIE_CORE, "TIE_INTERNAL", levels, excess, tr["dia_mm"],
                           st, dens, zone=zone_name, level_method=base_m,
                           why="sum of the link paths minus the perimeter: depends on internal bar positions "
                               f"({t['internal_state']}, ranges {t['ranges_state']})"))
    pieces = t["by_method"][base_m]["links"]
    n_hooks = (P.get("hook_method") or {}).get("hooks_per_link", 2)
    for hk in (HOOK_1, HOOK_2)[:n_hooks]:
        if t["hook_mm"] is None:
            parts.append(_part(seg, cand, hk, C_TIES, hk, "TIE_HOOK", None, None, tr["dia_mm"], BLOCKED, dens,
                               zone=zone_name, why="no hook method supplied"))
        else:
            parts.append(_part(seg, cand, hk, C_TIES, hk, "TIE_HOOK", pieces, t["hook_mm"], tr["dia_mm"],
                               PROVISIONAL if basis_lb != BLOCKED else BLOCKED, dens, zone=zone_name,
                               method_id=P["hook_method"]["method_id"],
                               why="hook allowance: provisional engineering method, never in a verified core"))
    return parts


def _main_parts(seg, cand, P):
    dens = _mass_cfg(P)
    d = cand["definition"]
    n, db = d["bars"]["count"], d["bars"]["dia_mm"]
    iv = seg["interval"]
    parts = []
    core_state = {ESTABLISHED: VERIFIED, BOUND_LOWER: LOWER_BOUND, BOUNDED: LOWER_BOUND}.get(iv["state"], BLOCKED)
    parts.append(_part(seg, cand, "MAIN_CORE", C_MAIN, CORE, "MAIN_CORE", n, iv.get("length_mm"), db,
                       core_state, dens, why=f"storey interval ({iv['state']}: {iv.get('basis')}) - bars run through "
                                             "the joint, never cut at the beam soffit"))
    lap_r, anc_r = P["lap_rule"], P["anchorage_rule"]
    above = seg.get("above") or {}
    if above.get("exists"):
        ab = (above.get("bars_by_candidate") or {}).get(cand["type"], above["bars"])
        na, da = ab["count"], ab["dia_mm"]
        n_lap = min(n, na)
        L = None if lap_r.get("current_D") is None else lap_r["current_D"] * da
        parts.append(_part(seg, cand, "LAP_TOP", C_LAP, LAP, "LAP", n_lap, L, da,
                           VERIFIED if lap_r["state"] == ESTABLISHED else
                           (PROVISIONAL if L is not None else BLOCKED), dens, rule_id=lap_r["rule_id"],
                           alternatives_D=lap_r.get("alternatives_D", []),
                           why="splice of the bars continuing into the storey above"))
        if n > na:
            L2 = None if anc_r.get("current_D") is None else anc_r["current_D"] * db
            parts.append(_part(seg, cand, "ANCHORAGE_TOP_STOPPED", C_ANCH, ANCHORAGE, "ANCHORAGE", n - na, L2, db,
                               VERIFIED if anc_r["state"] == ESTABLISHED else
                               (PROVISIONAL if L2 is not None else BLOCKED), dens, rule_id=anc_r["rule_id"],
                               alternatives_D=anc_r.get("alternatives_D", []),
                               why="bars not continued above are anchored at the floor"))
        if na > n:
            parts.append(_part(seg, cand, "ADDITIONAL_DOWELS", C_EXTRA, EXTRA, "EXTRA", na - n, None, da, BLOCKED,
                               dens, why="the storey above has more bars - dowel detail not established"))
        tr_ = section_transition(seg, cand, above) if P.get("check_section_transitions", True) else None
        if tr_ and tr_["state"] == BLOCKED:
            parts.append(_part(seg, cand, "SECTION_TRANSITION", C_EXTRA, EXTRA, "TRANSITION", None, None, db, BLOCKED,
                               dens, transition=tr_, why=tr_["why"]))
    else:
        L2 = None if anc_r.get("current_D") is None else anc_r["current_D"] * db
        parts.append(_part(seg, cand, "ANCHORAGE_TOP", C_ANCH, ANCHORAGE, "ANCHORAGE", n, L2, db,
                           VERIFIED if anc_r["state"] == ESTABLISHED else (PROVISIONAL if L2 is not None else BLOCKED),
                           dens, rule_id=anc_r["rule_id"], alternatives_D=anc_r.get("alternatives_D", []),
                           why="column stops - bars anchored into the closing slab / beam"))
    below = seg.get("below") or {}
    if below.get("kind") == "FOOTING":
        st = P.get("starter_rule")
        f = below.get("footing") or {}
        if st is None or f.get("depth_mm") is None:
            parts.append(_part(seg, cand, "STARTER", C_STARTER, STARTER, "STARTER", n, None, db, BLOCKED, dens,
                               why="starter rule or footing depth not established"))
        else:
            L = (f["depth_mm"] - st["bottom_cover_mm"]) + st["foot_mm"] + st["projection_D"] * db
            parts.append(_part(seg, cand, "STARTER", C_STARTER, STARTER, "STARTER", n, L, db,
                               VERIFIED if st["state"] == ESTABLISHED else PROVISIONAL, dens, rule_id=st["rule_id"],
                               footing_ref=f.get("ref"), footing_depth_mm=f["depth_mm"],
                               why="embedded depth (footing depth - bottom cover) + foot + projection"))
    elif below.get("kind") == "PLANTED_SUPPORT":
        L2 = None if anc_r.get("current_D") is None else anc_r["current_D"] * db
        parts.append(_part(seg, cand, "ANCHORAGE_BASE", C_ANCH, ANCHORAGE, "ANCHORAGE", n, L2, db,
                           VERIFIED if anc_r["state"] == ESTABLISHED else (PROVISIONAL if L2 is not None else BLOCKED),
                           dens, rule_id=anc_r["rule_id"], alternatives_D=anc_r.get("alternatives_D", []),
                           why="planted column - bars anchored into the supporting member"))
    for x in seg.get("extras", []):
        parts.append(_part(seg, cand, f"EXTRA:{x['extra_id']}", C_EXTRA, EXTRA, "EXTRA", x.get("count"),
                           x.get("length_mm"), x.get("dia_mm"), x["state"], dens, rule_id=x.get("rule_id"),
                           why=x.get("why")))
    return parts


def section_transition(seg, cand, above):
    """COLUMN_SECTION_TRANSITION between this storey and the one above. Where the section changes, the bars are not
    assumed straight: an explicit transition detail (straight / offset-crank / stopped bars + new starters / dowels)
    is required, else the transition is BLOCKED_TRANSITION_DETAIL. Returns None when the section does not change."""
    d = cand["definition"]
    here = (min(d["B_mm"], d["D_mm"]), max(d["B_mm"], d["D_mm"]))
    sec = (above.get("section_by_candidate") or {}).get(cand["type"], above.get("section_mm"))
    if not sec:
        return {"state": BLOCKED, "kind": "UNKNOWN_SECTION_ABOVE", "below_mm": list(here), "above_mm": None,
                "why": "BLOCKED_TRANSITION_DETAIL: section above not supplied"}
    up = (min(sec), max(sec))
    turned = bool(above.get("orientation_change"))
    if up == here and not turned:
        return None
    det = above.get("transition_detail")
    if det and det.get("kind") in ("STRAIGHT", "OFFSET_CRANK", "STOPPED_AND_NEW_STARTERS", "DOWELS"):
        return {"state": "DETAILED", "kind": det["kind"], "below_mm": list(here), "above_mm": list(up),
                "source_ref": det.get("source_ref"), "why": "transition detailed in the source"}
    return {"state": BLOCKED, "kind": "BLOCKED_TRANSITION_DETAIL", "below_mm": list(here), "above_mm": list(up),
            "orientation_change": turned,
            "why": f"BLOCKED_TRANSITION_DETAIL: section {here[0]}x{here[1]} -> {up[0]}x{up[1]}"
                   f"{' with a turn' if turned else ''}; straight continuation / offset-crank / stopped bars / new "
                   "starters / dowels not detailed - bars are not assumed straight"}


def _zones(seg):
    iv = seg["interval"]
    full = iv.get("length_mm")
    cz = seg.get("clear_zone") or {"state": BLOCKED}
    clear = None if (full is None or cz.get("framing_depth_mm") is None or cz["state"] == BLOCKED) \
        else full - cz["framing_depth_mm"]
    full_state = {ESTABLISHED: ESTABLISHED, BOUND_LOWER: BOUND_LOWER, BOUNDED: BOUND_LOWER}.get(iv["state"], BLOCKED)
    clear_state = BLOCKED if clear is None else (ESTABLISHED if (cz["state"] == ESTABLISHED and
                                                                 full_state == ESTABLISHED) else BOUNDED)
    return {CLEAR_ZONE: {"length_mm": clear, "state": clear_state, "basis": cz.get("basis")},
            FULL_ZONE: {"length_mm": full, "state": full_state, "basis": iv.get("basis")}}


def evaluate_candidate(seg, cand, P):
    zones = _zones(seg)
    base_zone = CLEAR_ZONE if zones[CLEAR_ZONE]["state"] != BLOCKED else FULL_ZONE
    ties = {z: _ties(seg, cand, P, zones[z]["length_mm"]) for z in ZONES}
    zstate = zones[base_zone]["state"] if base_zone == CLEAR_ZONE else BLOCKED
    parts = _main_parts(seg, cand, P) + _tie_parts(seg, cand, P, ties[base_zone], base_zone, zstate)
    alt_sections = {}
    for a in seg.get("section_alternatives", []):
        alt_sections[a["label"]] = _ties(seg, cand, P, zones[base_zone]["length_mm"], section=(a["B_mm"], a["D_mm"]))
    return {"type": cand["type"], "parts": parts, "zones": zones, "base_zone": base_zone, "ties": ties,
            "alt_sections": alt_sections}


# ================================================================================================ release
def _same(a, b):
    if (a is None) != (b is None):
        return False
    return a is None or abs(a - b) < 1e-9


def release_segment(seg, evals, flags):
    """Combine the candidates (type conflict) and the open flags into one released part list.
    Under a conflict: a part identical in every candidate is released as a LOWER_BOUND; a differing part is PROVISIONAL
    at the single corroborated candidate if there is one, else BLOCKED (shown at the census interpretation).
    Flags named in seg['conflict_flag_keys'] act only through this rule; every other open flag acts through
    engineering_flags.component_release on the facts the part depends on."""
    conflict = set(seg.get("conflict_flag_keys", ()))
    resolved = seg["resolved_type"]
    likely = [c["type"] for c in seg["candidates"] if c.get("corroborated")]
    likely = likely[0] if len(likely) == 1 else None
    other_flags = [f for f in flags if f["flag_key"] not in conflict]
    ids = {seg["occurrence_id"], seg.get("chain_id")} | set(seg.get("element_aliases", ()))
    base = evals[resolved]["parts"]
    by_id = {t: {p["part_id"]: p for p in evals[t]["parts"]} for t in evals}
    all_ids = []
    for t in evals:
        for p in evals[t]["parts"]:
            if p["part_id"] not in all_ids:
                all_ids.append(p["part_id"])
    out = []
    for pid in all_ids:
        vals = {t: by_id[t].get(pid) for t in evals}
        if len(evals) == 1:
            p = copy.deepcopy(vals[resolved])
            alt_state, alt = None, {}
        else:
            present = {t: v for t, v in vals.items() if v is not None}
            kgs = [v["kg"] for v in present.values()]
            shared = len(present) == len(vals) and all(_same(kgs[0], k) for k in kgs[1:])
            pick = likely if (not shared and likely in present) else (resolved if resolved in present else
                                                                       next(iter(present)))
            p = copy.deepcopy(present[pick])
            alt = {t: (None if v is None else v["kg"]) for t, v in vals.items()}
            alt_state = LOWER_BOUND if shared else (PROVISIONAL if (likely and pick == likely) else BLOCKED)
            p["conflict_shared"] = shared
            p["likely_type"] = likely
        hit = [f for f in other_flags if EF.is_open(f) and ids & set(f["element_ids"]) and
               set(f["affected_facts"]) & set(p["depends_on"])]
        eff = p["basis_state"]
        for f in hit:
            e = f["release_effect"]
            if e in (EF.NO_QUANTITY_IMPACT, EF.VERIFIED):
                continue
            e = BLOCKED if e == EF.AUDIT_ONLY else e
            if _RANK[e] > _RANK[eff]:
                eff = e
        if alt_state is not None and _RANK[alt_state] > _RANK[eff]:
            eff = alt_state
        if alt_state == PROVISIONAL and eff == LOWER_BOUND:
            known = [v for v in alt.values() if v is not None]
            if p["kg"] is not None and known and p["kg"] > min(known) + 1e-9:
                eff = PROVISIONAL          # the likely value is not the smallest candidate: not a proven bound
        if p["kg"] is None:
            eff = BLOCKED
        p["release_state"] = eff
        p["flags"] = sorted({f["flag_key"] for f in hit} | (conflict if alt_state else set()))
        p["alternatives_kg"] = alt
        out.append(p)
    return out


def component_states(parts, seg):
    """Terminal state per component. A component with a releasable part beside a blocked one is a LOWER_BOUND (the
    released part is proven, the rest is not); BLOCKED only when nothing in it is releasable."""
    by_c = defaultdict(list)
    for p in parts:
        by_c[p["component"]].append(p["release_state"])
    out = {}
    for c in COMPONENTS:
        st = by_c.get(c)
        if not st:
            out[c] = NOT_REQUIRED
        elif BLOCKED in st and any(s != BLOCKED for s in st):
            out[c] = LOWER_BOUND
        else:
            out[c] = _worst(st)
    return out


def occurrence_state(comp_states):
    """Same rule one level up: REBAR_BLOCKED only when no required component is releasable; a blocked component
    beside released ones makes the occurrence a lower bound."""
    st = [comp_states[c] for c in COMPONENTS if comp_states[c] != NOT_REQUIRED]
    if st and all(s == BLOCKED for s in st):
        return OCC_STATES[BLOCKED]
    if BLOCKED in st:
        return OCC_STATES[_worst([s for s in st if s != BLOCKED] + [LOWER_BOUND])]
    return OCC_STATES[_worst(st)]


# ================================================================================================ chain checks
def validate_segments(segments, expected_occurrences):
    """Conservation of the input: one segment per occurrence, no duplicate, no orphan, and the continuity flags agree
    with the chain (a lap above needs a segment above; a terminating column has none)."""
    problems = []
    ids = Counter(s["segment_id"] for s in segments)
    problems += [f"duplicate segment {k}" for k, v in ids.items() if v > 1]
    occ = Counter(s["occurrence_id"] for s in segments)
    problems += [f"duplicate occurrence {k}" for k, v in occ.items() if v > 1]
    exp = set(expected_occurrences)
    problems += [f"missing occurrence {k}" for k in sorted(exp - set(occ))]
    problems += [f"unexpected occurrence {k}" for k in sorted(set(occ) - exp)]
    by_chain = defaultdict(dict)
    for s in segments:
        by_chain[s["chain_id"]][s["storey_index"]] = s
    for ch, st in by_chain.items():
        for i, s in st.items():
            up = (s.get("above") or {}).get("exists", False)
            if up and (i + 1) not in st:
                problems += [f"{s['segment_id']}: continues above but the chain has no segment above"]
            if not up and (i + 1) in st:
                problems += [f"{s['segment_id']}: chain has a segment above but no continuity / lap"]
    return problems


# ================================================================================================ run
def evaluate(segments, P, flags=(), expected_occurrences=None):
    """Evaluate every segment. Returns segments (with candidates' evaluations, released parts, component and occurrence
    states), the flat released part list and the input-conservation problems."""
    problems = validate_segments(segments, expected_occurrences or [s["occurrence_id"] for s in segments])
    res = []
    for seg in segments:
        evals = {c["type"]: evaluate_candidate(seg, c, P) for c in seg["candidates"]}
        parts = release_segment(seg, evals, list(flags))
        comps = component_states(parts, seg)
        res.append({"segment": seg, "evals": evals, "parts": parts, "components": comps,
                    "occurrence_state": occurrence_state(comps)})
    return {"segments": res, "parts": [p for r in res for p in r["parts"]], "input_problems": problems}


BUCKET = {VERIFIED: "verified", LOWER_BOUND: "lower_bound", PROVISIONAL: "provisional", BLOCKED: "blocked"}


def mass_conservation(result, floor_of):
    """Part -> segment -> floor -> project, by release bucket. Blocked parts without a value are counted, not summed."""
    seg_t = {}
    for r in result["segments"]:
        b = defaultdict(float)
        for p in r["parts"]:
            if p["kg"] is not None:
                b[BUCKET[p["release_state"]]] += p["kg"]
        b["total"] = sum(v for k, v in b.items() if k != "total")
        b["unquantified_blocked_parts"] = sum(1 for p in r["parts"] if p["kg"] is None)
        seg_t[r["segment"]["segment_id"]] = dict(b)
    fl = defaultdict(lambda: defaultdict(float))
    for r in result["segments"]:
        f = floor_of(r["segment"])
        for k, v in seg_t[r["segment"]["segment_id"]].items():
            fl[f][k] += v
    proj = defaultdict(float)
    for f in fl.values():
        for k, v in f.items():
            proj[k] += v
    parts_sum = sum(p["kg"] for p in result["parts"] if p["kg"] is not None)
    seg_sum = sum(v["total"] for v in seg_t.values())
    fl_sum = sum(v["total"] for v in fl.values())
    pid = Counter(p["part_id"] for p in result["parts"])
    checks = {"parts_equal_segments": abs(parts_sum - seg_sum) < _EPS,
              "segments_equal_floors": abs(seg_sum - fl_sum) < _EPS,
              "floors_equal_project": abs(fl_sum - proj["total"]) < _EPS,
              "buckets_equal_total": abs(sum(proj[b] for b in BUCKET.values()) - proj["total"]) < _EPS,
              "no_duplicate_part": all(v == 1 for v in pid.values()),
              "no_duplicate_segment": len(seg_t) == len(result["segments"]),
              "main_and_tie_parts_disjoint": all(
                  (p["component"] == C_TIES) == (p["length_kind"] in (TIE_CORE, HOOK_1, HOOK_2))
                  for p in result["parts"])}
    return {"segments": seg_t, "floors": {k: dict(v) for k, v in fl.items()}, "project": dict(proj),
            "checks": checks}


# ================================================================================================ scenarios
def tie_scenarios(r, P):
    """Clear vs full zone x RATE_COUNT vs SPACING_WITH_ENDS for the released (or likely) candidate of one segment."""
    seg = r["segment"]
    t = _released_type(r)
    ev = r["evals"][t]
    dens = _mass_cfg(P)
    m = UM.kg_per_m(P["tie_rule"]["dia_mm"], dens)
    out = {"segment_id": seg["segment_id"], "candidate_type": t}
    for z in ZONES:
        tz = ev["ties"][z]
        for meth in LEVEL_METHODS:
            key = f"{z}|{meth}"
            if tz.get("state") != ESTABLISHED or not tz.get("by_method"):
                out[key] = None
                continue
            bm = tz["by_method"][meth]
            core = bm["levels"] * tz["sum_link_paths_mm"] / 1000.0 * m
            nh = (P.get("hook_method") or {}).get("hooks_per_link", 2)
            hook = 0.0 if tz["hook_mm"] is None else bm["links"] * nh * tz["hook_mm"] / 1000.0 * m
            out[key] = {"zone_mm": ev["zones"][z]["length_mm"], "levels": bm["levels"], "links": bm["links"],
                        "core_kg": core, "hook_kg": hook, "perimeter_lb_kg": bm["levels"] * tz["perimeter_mm"] /
                        1000.0 * m}
    return out


def alt_section_tie_kg(r, P, label):
    """Tie kg (core + hooks, base zone, RATE_COUNT) if the alternative section `label` were used instead of the
    schedule section - the quantity a section-override flag puts at stake."""
    t = _released_type(r)
    tz = r["evals"][t]["alt_sections"].get(label)
    if not tz or tz.get("state") != ESTABLISHED or not tz.get("by_method"):
        return None
    m = UM.kg_per_m(P["tie_rule"]["dia_mm"], _mass_cfg(P))
    bm = tz["by_method"][RATE_COUNT]
    nh = (P.get("hook_method") or {}).get("hooks_per_link", 2)
    hook = 0.0 if tz["hook_mm"] is None else bm["links"] * nh * tz["hook_mm"]
    return (bm["levels"] * tz["sum_link_paths_mm"] + hook) / 1000.0 * m


def _released_type(r):
    seg = r["segment"]
    likely = [c["type"] for c in seg["candidates"] if c.get("corroborated")]
    return likely[0] if len(likely) == 1 and len(seg["candidates"]) > 1 else seg["resolved_type"]


# ================================================================================================ method flags
METHOD_FLAG_KINDS = {
    "TIE_ZONE_METHOD_REQUIRED": ("transverse_zone", EF.LOWER_BOUND, "ENGINEERING_METHOD_REQUIRED"),
    "END_LEVEL_COUNT_METHOD_REQUIRED": ("transverse_level_count", EF.LOWER_BOUND, "ENGINEERING_METHOD_REQUIRED"),
    "HOOK_METHOD_REQUIRED": ("tie_hook", EF.PROVISIONAL_VALUE, "ENGINEERING_METHOD_REQUIRED"),
    "LAP_METHOD_REQUIRED": ("lap_method", EF.PROVISIONAL_VALUE, "ENGINEERING_METHOD_REQUIRED"),
    "TIE_TOPOLOGY_RULE_GAP": ("transverse_arrangement", EF.BLOCKED, "RULE_GAP"),
    "COLUMN_SECTION_TRANSITION_DETAIL_REQUIRED": ("section_transition", EF.BLOCKED, "MISSING_DETAIL"),
}


def method_flags(result, P, existing_flags=(), *, where=None):
    """Method / rule-gap flags raised by this engine, quantified in kg. An existing flag on the same fact and elements
    is reused when its release effect already matches; one with a different effect is SUPERSEDED by the quantified
    flag (history kept). Returns (new_flags, superseded_existing, quantification_by_kind)."""
    ctx = P["context"]
    where = where or {}
    rows = [(r, tie_scenarios(r, P)) for r in result["segments"]]
    q = {}
    # zone: clear vs full (rate count), over the segments where both zones are known
    both = [(r, s) for r, s in rows if s[f"{CLEAR_ZONE}|{RATE_COUNT}"] and s[f"{FULL_ZONE}|{RATE_COUNT}"]]
    a = sum(s[f"{CLEAR_ZONE}|{RATE_COUNT}"]["core_kg"] for _, s in both)
    b = sum(s[f"{FULL_ZONE}|{RATE_COUNT}"]["core_kg"] for _, s in both)
    q["TIE_ZONE_METHOD_REQUIRED"] = {
        "elements": [r["segment"]["occurrence_id"] for r, _ in rows],
        "segments_compared": len(both),
        "segments_clear_zone_not_established": sorted(r["segment"]["occurrence_id"] for r, s in rows
                                                      if not s[f"{CLEAR_ZONE}|{RATE_COUNT}"]),
        "current_kg": a, "alternative_kg": b, "quantity_affected_kg": b - a,
        "current": "ties over the clear column zone (to the soffit of the deepest framing member)",
        "alternative": "ties over the full storey interval (continuous through the joint)",
        "question": "Do the column ties stop at the soffit of the deepest beam, or continue through the beam-column "
                    "joint over the full storey height?"}
    a2 = c = 0.0
    for r, s in rows:
        z = r["evals"][s["candidate_type"]]["base_zone"]
        if s[f"{z}|{RATE_COUNT}"]:
            a2 += s[f"{z}|{RATE_COUNT}"]["core_kg"]
            c += s[f"{z}|{SPACING_WITH_ENDS}"]["core_kg"]
    q["END_LEVEL_COUNT_METHOD_REQUIRED"] = {
        "elements": [r["segment"]["occurrence_id"] for r, _ in rows],
        "current_kg": a2, "alternative_kg": c, "quantity_affected_kg": c - a2,
        "current": "RATE_COUNT = ceil(rate x zone length)",
        "alternative": "SPACING_WITH_ENDS = ceil(zone length / spacing) + 1",
        "question": "Is the per-metre tie count applied as rate x length, or as a spacing with a tie at both ends?"}
    hk = sum(p["kg"] for p in result["parts"] if p["length_kind"] in (HOOK_1, HOOK_2) and p["kg"] is not None)
    q["HOOK_METHOD_REQUIRED"] = {
        "elements": sorted({p["occurrence_id"] for p in result["parts"] if p["length_kind"] in (HOOK_1, HOOK_2)}),
        "current_kg": hk, "alternative_kg": 0.0, "quantity_affected_kg": hk,
        "current": f"hook method {(P.get('hook_method') or {}).get('method_id')} (provisional)",
        "alternative": "core path only (no hook allowance)",
        "question": "Which hook (angle and extension) do the column ties use?"}
    lap_parts = [p for p in result["parts"] if p["length_kind"] in (LAP, ANCHORAGE) and p["kg"] is not None]
    cur = sum(p["kg"] for p in lap_parts)
    alt = 0.0
    for p in lap_parts:
        ad = (p.get("alternatives_D") or [None])[0]
        rule = P["lap_rule"] if p["length_kind"] == LAP else P["anchorage_rule"]
        alt += p["kg"] * (ad / rule["current_D"]) if ad else p["kg"]
    q["LAP_METHOD_REQUIRED"] = {
        "elements": sorted({p["occurrence_id"] for p in lap_parts}),
        "current_kg": cur, "alternative_kg": alt, "quantity_affected_kg": alt - cur,
        "current": f"{P['lap_rule'].get('current_D')} x bar diameter ({P['lap_rule']['rule_id']})",
        "alternative": f"{(P['lap_rule'].get('alternatives_D') or [None])[0]} x bar diameter",
        "question": "Which lap / development length applies to column bar splices and to bars stopped at a floor "
                    "or anchored into a supporting beam?"}
    gaps = [r for r in result["segments"] for t, ev in r["evals"].items()
            if ev["ties"][ev["base_zone"]]["band"]["state"] == RULE_GAP]
    if gaps:
        q["TIE_TOPOLOGY_RULE_GAP"] = {
            "elements": sorted({r["segment"]["occurrence_id"] for r in gaps}),
            "current_kg": 0.0, "alternative_kg": None, "quantity_affected_kg": None,
            "current": "ties blocked (long side on a limit no band includes)",
            "alternative": "one of the adjacent bands",
            "question": "The long side sits on a band limit no band includes - which link arrangement applies?"}
    tparts = [p for p in result["parts"] if p.get("transition")]
    if tparts:
        q["COLUMN_SECTION_TRANSITION_DETAIL_REQUIRED"] = {
            "elements": sorted({p["occurrence_id"] for p in tparts}), "current_kg": 0.0, "alternative_kg": None,
            "quantity_affected_kg": None, "transitions": len({p["segment_id"] for p in tparts}),
            "current": "transition blocked (crank / stopped bars / new starters / dowels not detailed)",
            "alternative": "a transition detail from the consultant",
            "question": "Where a column section changes between storeys, are the bars cranked, stopped with new "
                        "starters, or continued with dowels? Please give the detail."}
    pol = P.get("level_method_policy") or {}
    note = P["tie_rule"].get("notation", RATE_PER_M)
    if pol.get("authority") and note in pol and "END_LEVEL_COUNT_METHOD_REQUIRED" in q:
        q["END_LEVEL_COUNT_METHOD_REQUIRED"]["resolved_by_policy"] = {
            "notation": note, "method": pol[note], "authority": pol["authority"]}
    new, superseded = [], []
    for kind, v in q.items():
        if not v["elements"] or v.get("resolved_by_policy"):
            continue
        fact, effect, issue = METHOD_FLAG_KINDS[kind]
        els = set(v["elements"])
        cover = [f for f in existing_flags if f["status"] != EF.SUPERSEDED and fact in f["affected_facts"] and
                 els & set(f["element_ids"])]
        if cover and all(f["release_effect"] == effect or not EF.is_open(f) for f in cover):
            v["covered_by"] = [f["flag_key"] for f in cover]
            continue
        sup = [f for f in cover if EF.is_open(f) and f["release_effect"] != effect]
        nf = EF.make_flag(project_id=ctx["project_id"], drawing_revision=ctx["drawing_revision"],
                          detector=f"column_rebar.{kind.lower()}", discipline="STRUCTURAL", trade="REINFORCEMENT",
                          element_type="COLUMN", element_id=f"{kind}", subject=kind, element_ids=sorted(els),
                          issue_type=issue,
                          issue_summary=f"{kind}: {v['current']} vs {v['alternative']}",
                          current_interpretation=v["current"], interpretation_authority="ENGINEERING_METHOD",
                          affected_facts=[fact], release_effect=effect,
                          quantity_affected=None if v["quantity_affected_kg"] is None
                          else round(v["quantity_affected_kg"], 3), unit="kg",
                          severity="HIGH" if kind in ("TIE_ZONE_METHOD_REQUIRED", "TIE_TOPOLOGY_RULE_GAP") else
                          "MEDIUM", question_for_engineer=v["question"], where_to_check=where.get(kind),
                          answer_options=[{"answer": v["current"], "effect": "current released basis"},
                                          {"answer": v["alternative"], "effect": "alternative quantity"}],
                          status=EF.OPEN,
                          context={"s3_kind": kind, "supersedes": [f["flag_key"] for f in sup],
                                   "quantification": {k: v[k] for k in ("current_kg", "alternative_kg",
                                                                         "quantity_affected_kg")}})
        new.append(nf)
        for f in sup:
            superseded.append(EF.transition(f, EF.SUPERSEDED, by="ENGINE", note=f"quantified by {nf['flag_key']}"))
    return new, superseded, q


def schema():
    return {"schema": "COLUMN_REBAR_SCHEMA", "policy_id": POLICY_ID, "topologies": list(TOPOLOGIES),
            "rate_semantics": list(RATE_SEMANTICS), "level_methods": list(LEVEL_METHODS), "zones": list(ZONES),
            "length_kinds": list(LENGTH_KINDS), "components": list(COMPONENTS),
            "required_components": list(REQUIRED_COMPONENTS), "occurrence_states": sorted(set(OCC_STATES.values())),
            "part_facts": {k: list(v) for k, v in FACTS.items()},
            "rules": ["quantities per storey segment, never type x count",
                      "core run = storey interval; bars are never cut at the beam soffit",
                      "lap / starter / anchorage / extras are separate parts with their own rule state",
                      "every link of a level has its own path from section, cover, bar positions and topology",
                      "the outer perimeter path is a lower bound of any closed-link set enclosing every bar",
                      "internal link edges on derived bar positions are provisional",
                      "RATE_COUNT is the released lower-bound basis; SPACING_WITH_ENDS is reported as alternative",
                      "clear-zone and full-storey tie zones are both computed; the clear zone is the lower bound",
                      "hooks are separate provisional parts, never inside a verified core",
                      "a band gap stays a RULE_GAP unless a claim that APPLIES (project + revision + flag) "
                      "adjudicates that exact value to an adjacent band",
                      "a per-metre count is read as tie sets only from the rule text or an applying claim",
                      "under a type conflict a part shared by every candidate is a lower bound; a differing part "
                      "is provisional at a single corroborated candidate, else blocked",
                      "input conservation: one segment per occurrence; continuity consistent with the chain"]}
