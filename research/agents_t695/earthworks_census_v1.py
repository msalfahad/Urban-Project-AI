"""EARTHWORKS_CENSUS_V1 (T-695, lane S, every villa; stdlib only, pure).

Two jobs, both on numbers only (no drawing access):

1. CENSUS of the B1 earthworks lines of a candidate: one row per line (code, line id, zone, state, bound, cause class),
   reconciled BY ID to the candidate's line index: every STR.EARTH.* line exactly once, no row without a line, the
   family of the code (B1-02 excavation / B1-03 backfill / B1-04 disposal) agrees with the zone id. Cause classes:
     MEASURABLE_NOW  the drawings (with the owner-accepted level scenario S01 where named) establish a value or a
                     bounded range now;
     NEEDS_TEST      a site / laboratory test is missing (the test is named: ASTM D1557 MDD, in-situ dry density, ...);
     DESIGNER        a designer / supplier item (RFI or D-nn named);
     OWNER_RULE      an Urban rule is missing (the gap is named).
   A row may carry a primary and secondary causes; a HELD row never carries a value of 0 unless the 0 is CALCULATED
   from geometry (ZERO_BY_GEOMETRY with its condition and evidence).

2. ZONE GEOMETRY for MEASURABLE_NOW zones, scenario by scenario (never mixed): neat trench excavation (plan x depth from
   EXISTING ground to the formation), backfill = excavation - every permanent solid below EG at its position (once),
   formation compaction footprint, layers = ceil(zone backfill depth / lift) with the OWNER-PROVISIONAL 0.15 m lift,
   and the material account (import / disposal by dry mass) HELD naming each missing test.

Rules (R-T695-1, proposed): (a) a zone value is the envelope of its admissible scenarios, each computed alone; (b) a
deeper zone owns the plan it shares with a shallower one (pits > straps > ground-beam trenches), a shallower line's
part over it is netted once and named; (c) a calculated 0 needs a geometric proof (bottom of every solid and of its
blinding at or above EG for every admissible depth); (d) material quantities need measured densities: missing ->
HELD with the test named, never 0, never a default factor (the balance itself stays R-T505-1); (e) units are metres / m2 / m3 only.
"""
from __future__ import annotations

import math

VERSION = "EARTHWORKS_CENSUS_V1"
CLASSES = ("MEASURABLE_NOW", "NEEDS_TEST", "DESIGNER", "OWNER_RULE")
FAMILY_BY_CODE = {"STR.EARTH.EXCAVATION": "B1-02", "STR.EARTH.BACKFILL": "B1-03", "STR.EARTH.DISPOSAL": "B1-04"}
MATERIAL_TESTS = {
    "mdd": "maximum dry density by ASTM D1557 (Modified Proctor) on the excavated soil",
    "insitu_dry_density": "in-situ dry density of the excavated soil (ASTM D6938 or sand cone)",
    "loose_density": "loose (bulked) density of the excavated soil, measured",
    "suitability": "suitability of the excavated soil for re-use as fill (geotechnical classification)",
    "target_density": "placement target density (project specification; 95 % MPD is PROPOSED-SPEC only)",
}


MAX_DEPTH_M = 30.0          # a villa trench deeper than this is a unit error (mm read as m), refused


class CensusError(ValueError):
    pass


def _num(x, what):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or math.isnan(x) or math.isinf(x):
        raise CensusError(f"{what}: not a number: {x!r}")
    return float(x)


# ----------------------------------------------------------------------------------------------------- census ----

def census(index_lines, register):
    """index_lines: the candidate line index rows (dicts with line_id, item_code, class, measured_net, held_low,
    held_high, unit, element_id). register: {element_id: {"cause": CLASS, "secondary": [CLASS..], "gap": str, ...}}
    keyed by the line's ELEMENT id (stable across candidates; the line id is checked against the index).
    Returns the census rows, ordered by family then element id. Raises on any reconciliation failure."""
    earth = [x for x in index_lines if str(x.get("item_code", "")).startswith("STR.EARTH.")]
    ids = [x["line_id"] for x in earth]
    if len(ids) != len(set(ids)):
        raise CensusError("a line id appears twice in the index")
    els = [x["element_id"] for x in earth]
    if len(els) != len(set(els)):
        raise CensusError("an earthworks element appears on two lines")
    missing = sorted(set(els) - set(register))
    if missing:
        raise CensusError(f"index lines with no census row: {missing}")
    extra = sorted(set(register) - set(els))
    if extra:
        raise CensusError(f"census rows naming no index line: {extra}")
    rows = []
    for x in earth:
        code = x["item_code"]
        fam = FAMILY_BY_CODE.get(code)
        if fam is None:
            raise CensusError(f"unknown earthworks code {code}")
        if f":{fam}:" not in x["element_id"]:
            raise CensusError(f"{x['line_id']}: code {code} ({fam}) disagrees with zone {x['element_id']}")
        if x.get("unit") != "m3":
            raise CensusError(f"{x['line_id']}: unit {x.get('unit')!r}, expected m3")
        reg = register[x["element_id"]]
        if reg.get("line_id") and reg["line_id"] != x["line_id"]:
            raise CensusError(f"{x['element_id']}: register line {reg['line_id']} != index {x['line_id']}")
        cause = reg.get("cause")
        if cause not in CLASSES:
            raise CensusError(f"{x['element_id']}: cause {cause!r} not one of {CLASSES}")
        for s in reg.get("secondary", []):
            if s not in CLASSES:
                raise CensusError(f"{x['element_id']}: secondary cause {s!r}")
        if cause != "MEASURABLE_NOW" and not reg.get("gap"):
            raise CensusError(f"{x['element_id']}: a {cause} row must name its gap")
        if cause == "NEEDS_TEST" and not reg.get("tests"):
            raise CensusError(f"{x['element_id']}: NEEDS_TEST must name the test(s)")
        state = x["class"]
        val, lo, hi = x.get("measured_net"), x.get("held_low"), x.get("held_high")
        if state != "RELEASED" and val not in (None,):
            raise CensusError(f"{x['line_id']}: a {state} line carries a value")
        if state != "RELEASED" and val == 0:
            raise CensusError(f"{x['line_id']}: HELD as 0")
        if (lo is None) != (hi is None):
            raise CensusError(f"{x['line_id']}: half a bound")
        if lo is not None and _num(lo, "low") > _num(hi, "high"):
            raise CensusError(f"{x['line_id']}: low > high")
        bound = ("VALUE" if val is not None else "RANGE" if lo is not None else "BLANK")
        rows.append({"family": fam, "code": code, "line_id": x["line_id"], "element_id": x["element_id"],
                     "zone": x["element_id"].split(":", 2)[2], "state": state, "bound": bound,
                     "value_m3": val, "low_m3": lo, "high_m3": hi, "cause": cause,
                     "secondary": list(reg.get("secondary", [])), "gap": reg.get("gap", ""),
                     "tests": list(reg.get("tests", [])), "proposal": reg.get("proposal", "")})
    rows.sort(key=lambda r: (r["family"], r["element_id"]))
    return rows


def census_counts(rows):
    out = {}
    for r in rows:
        k = f"{r['family']}|{r['cause']}"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


# ---------------------------------------------------------------------------------------------- geometry ----

def zero_by_geometry(top_m, depth_max_m, blinding_m, eg_m=0.0):
    """A ground-beam trench is a CALCULATED 0 when the bottom of its blinding is at or above EG for the deepest
    admissible section. Returns (is_zero, lowest bottom level, depth threshold D* above which a cut is needed)."""
    top, d, b, eg = (_num(top_m, "top"), _num(depth_max_m, "depth"), _num(blinding_m, "blinding"), _num(eg_m, "EG"))
    if d <= 0 or b < 0:
        raise CensusError("depth must be > 0, blinding >= 0")
    bottom = top - d - b
    return bottom >= eg - 1e-12, round(bottom, 6), round(top - b - eg, 6)


def layers(depth_m, lift_m):
    d, lift = _num(depth_m, "zone depth"), _num(lift_m, "lift")
    if lift <= 0:
        raise CensusError("lift must be > 0")
    if d < 0:
        raise CensusError("negative zone depth")
    return math.ceil(round(d / lift, 9)) if d > 0 else 0


def trench_scenario(name, plan_m2, formation_depth_m, solids_m3, cut_owned_by_others_m3=0.0, fill_depth_m=None,
                    lift_m=None):
    """One admissible scenario of one trench zone. plan_m2: the neat plan this zone owns (deeper zones' plans already
    removed); formation_depth_m: EG -> formation; solids_m3: {name: m3 of a permanent solid below EG inside the plan};
    cut_owned_by_others_m3: the part of this zone's cut already carried by a shallower valued line (netted once)."""
    plan, dep = _num(plan_m2, "plan"), _num(formation_depth_m, "depth")
    if plan < 0 or dep < 0:
        raise CensusError(f"{name}: negative plan or depth")
    if dep > MAX_DEPTH_M:
        raise CensusError(f"{name}: formation depth {dep} is not in metres")
    other = _num(cut_owned_by_others_m3, "netted cut")
    exc = plan * dep - other
    disp = sum(_num(v, f"solid {k}") for k, v in solids_m3.items())
    fill = exc - disp
    if exc < -1e-9 or fill < -1e-9:
        raise CensusError(f"{name}: solids exceed the cut ({exc:.6f} m3 cut, {disp:.6f} m3 solids)")
    out = {"scenario": name, "plan_m2": round(plan, 6), "formation_depth_m": round(dep, 6),
           "excavation_m3": round(exc, 6), "displacement_m3": round(disp, 6), "backfill_m3": round(fill, 6),
           "netted_cut_m3": round(other, 6), "compaction_footprint_m2": round(plan, 6)}
    if fill_depth_m is not None and lift_m is not None:
        out["fill_depth_m"] = round(_num(fill_depth_m, "fill depth"), 6)
        out["layers"] = layers(fill_depth_m, lift_m)
    return out


def envelope(scenarios, keys=("excavation_m3", "backfill_m3", "compaction_footprint_m2", "layers")):
    """The zone's bounded range: min / max of each quantity over its admissible scenarios (each computed alone)."""
    if not scenarios:
        raise CensusError("no scenario")
    names = [s["scenario"] for s in scenarios]
    if len(names) != len(set(names)):
        raise CensusError("scenario named twice")
    out = {"scenarios": len(scenarios)}
    for k in keys:
        vals = [s[k] for s in scenarios if k in s]
        if vals:
            out[k] = [min(vals), max(vals)]
            out[k + "_by"] = [min(scenarios, key=lambda s: s.get(k, math.inf))["scenario"],
                              max(scenarios, key=lambda s: s.get(k, -math.inf))["scenario"]]
    return out


def at_least_trench(parts):
    """A trench whose depth has only a LOWER bound (a designer section): AT_LEAST = sum(free strip x minimum depth
    below EG). parts: [(name, free_strip_m2, min_depth_below_eg_m)]. Never a value, never an upper bound."""
    tot = 0.0
    for nm, a, d in parts:
        a, d = _num(a, f"{nm} plan"), _num(d, f"{nm} depth")
        if a < 0 or d < 0:
            raise CensusError(f"{nm}: negative")
        tot += a * d
    return {"kind": "AT_LEAST", "m3": round(tot, 6)}


def material_account(volumes_m3, facts):
    """Gate of the import / disposal account (owner 2026-11-02 18:00: dry mass only, with MEASURED densities). This
    module never balances the masses itself: the balance is R-T505-1 (research/agents_t505/disposal_balance_v2.py).
    facts: {key: value or None} for the MATERIAL_TESTS keys. Any missing fact -> HELD with every missing test named;
    the geometric volumes stay beside (in-situ / compacted m3), never converted with a default factor."""
    for k in facts:
        if k not in MATERIAL_TESTS:
            raise CensusError(f"unknown material fact {k}")
    geo = {k: round(_num(v, k), 6) for k, v in volumes_m3.items()}
    missing = [k for k in MATERIAL_TESTS if facts.get(k) in (None, "")]
    for k in MATERIAL_TESTS:
        if k not in missing:
            _num(facts[k], k)
    if missing:
        return {"state": "HELD", "geometry_m3": geo, "missing_tests": [MATERIAL_TESTS[k] for k in missing],
                "balance": None}
    return {"state": "INPUTS_COMPLETE", "geometry_m3": geo, "missing_tests": [],
            "balance": "run R-T505-1 DISPOSAL_BALANCE_V2 (research/agents_t505/disposal_balance_v2.py) on these inputs"}
