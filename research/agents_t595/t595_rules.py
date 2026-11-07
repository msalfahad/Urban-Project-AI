"""T-595 rules (research, unwired; every villa): two restatement rules for held structural bounds.

Physical elements (ERS s.2.1):
  * a SIDE-BAR POPULATION: the longitudinal bars drawn as dots on the vertical faces of a beam / ring section between
    the top and bottom layers, at one or more levels;
  * a FOOTING with SCENARIO READINGS: one plan element whose drawing admits several owner-accepted interpretations
    (e.g. a tagged pad alone / the pad + a second tagged pad / the one drawn outline at the deepest tagged depth).

R-T595-1  SIDE-BAR POPULATION FROM THE DRAWN SECTION (supersedes the one-face reading of R-T583 RING_SIDE; T-583 rows
          untouched). The population is levels_drawn x faces_drawn bars, every bar taking the label's diameter. A label
          ('2 d14 / 20 cm') states diameter and spacing; its leader marks one level and never sets the number of faces.
          A count with fewer faces or levels than the section draws is REFUSED (a single-face reading where two faces
          are drawn). Where the label count and the drawn dots disagree the drawn population governs; a real
          contradiction (dots of another diameter, a label naming a face) is a DRAWING_CONFLICT, never resolved by
          picking one. Further rows at the printed spacing over an unprinted depth stay HELD by name (high open).
R-T595-2  SCENARIO-SET BOUND (supersedes the T-572 reading-A low of a scenario element; T-572 rows untouched). When the
          owner has accepted a set of interpretations for one element, the component bound in each family is
          low = min, high = max over EVERY accepted scenario value of that family; a stated low above any accepted
          scenario value is REFUSED (not strict). Each scenario is carried as one consistent reading across families
          (concrete, reinforcement, formwork, excavation, blinding, backfill): a scenario view that takes one family
          from scenario X and another from scenario Y is REFUSED. A family whose per-scenario value is not measured
          keeps its existing bound and is listed as SCENARIO_SPLIT_OPEN, never filled from another family.
Provenance: T-595 (2026-11-07) on F-C-T583-1 (Checker own read ST p.7, T-589) and F-T589-1 (owner 2026-11-02 RFI
re-review (4), accepted S02 range 1.960 .. 2.275 m3). Quantities in m / m3 / kg; t = kg / 1000 once.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

EPS = 1e-9
Q6 = Decimal("0.000001")


class T595Error(ValueError):
    pass


def kgm(d_mm: int) -> float:
    """Nominal unit mass d^2 / 162 kg/m (the T-575 / T-583 convention)."""
    if not isinstance(d_mm, int) or d_mm <= 0 or d_mm > 50:
        raise T595Error("bar diameter in whole mm (6 .. 50)")
    return d_mm * d_mm / 162.0


# ---- R-T595-1 --------------------------------------------------------------------------------------------------------
def side_bar_population(levels_drawn: int, faces_drawn: int, levels_counted: int | None = None,
                        faces_counted: int | None = None, label_n: int | None = None) -> dict:
    """Number of side bars from the drawn section; refuses a reading that drops a drawn face or level."""
    for v in (levels_drawn, faces_drawn):
        if not isinstance(v, int) or v < 0:
            raise T595Error("drawn levels / faces are whole counts read from the section")
    if faces_drawn > 2:
        raise T595Error("a beam / ring section has at most two vertical faces")
    lc = levels_drawn if levels_counted is None else levels_counted
    fc = faces_drawn if faces_counted is None else faces_counted
    if fc < faces_drawn:
        raise T595Error(f"single-face reading refused: {fc} face(s) counted where the section draws {faces_drawn}")
    if lc < levels_drawn:
        raise T595Error(f"{lc} level(s) counted where the section draws {levels_drawn}")
    if fc > faces_drawn or lc > levels_drawn:
        raise T595Error("more faces / levels counted than drawn: not a drawing reading")
    n = levels_drawn * faces_drawn
    out = {"n": n, "levels": levels_drawn, "faces": faces_drawn, "status": "DRAWN"}
    if label_n is not None and label_n not in (levels_drawn, faces_drawn, n):
        out["status"] = "DRAWING_CONFLICT"
        out["conflict"] = f"label count {label_n} matches neither a level ({faces_drawn}), a face ({levels_drawn}) nor the section ({n})"
    return out


def side_bar_low_kg(population: dict, length_m: float, d_mm: int) -> float:
    if population.get("status") == "DRAWING_CONFLICT":
        raise T595Error("side-bar population is a DRAWING_CONFLICT: HELD, no single value")
    if length_m < 0:
        raise T595Error("length must be >= 0")
    if length_m > 200:
        raise T595Error("lengths in m (a value above 200 reads as mm)")
    return population["n"] * length_m * kgm(d_mm)


# ---- R-T595-2 --------------------------------------------------------------------------------------------------------
def d6(x) -> Decimal:
    if x is None:
        raise T595Error("missing value: HELD with its item, never 0")
    v = Decimal(str(x))
    if v < 0:
        raise T595Error("negative quantity")
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


def box(L, B, H) -> Decimal:
    for v in (L, B, H):
        if Decimal(str(v)) <= 0:
            raise T595Error("dimension must be > 0")
        if Decimal(str(v)) > 50:
            raise T595Error("dimensions in m (a value above 50 reads as mm)")
    return d6(Decimal(str(L)) * Decimal(str(B)) * Decimal(str(H)))


def scenario_bound(values: dict, stated_low=None, stated_high=None) -> dict:
    """values: {scenario_id: value or None}; every accepted scenario must carry a value for a bound."""
    if not values:
        raise T595Error("no accepted scenario")
    missing = [k for k, v in values.items() if v is None]
    if missing:
        raise T595Error(f"scenario(s) {missing} without a value: SCENARIO_SPLIT_OPEN, no scenario bound")
    vals = {k: d6(v) for k, v in values.items()}
    lo_id = min(vals, key=lambda k: (vals[k], k))
    hi_id = max(vals, key=lambda k: (vals[k], k))
    lo, hi = vals[lo_id], vals[hi_id]
    if stated_low is not None and d6(stated_low) > lo:
        raise T595Error(f"stated low {d6(stated_low)} exceeds accepted scenario {lo_id} = {lo}: not a strict low")
    if stated_high is not None and d6(stated_high) < hi:
        raise T595Error(f"stated high {d6(stated_high)} below accepted scenario {hi_id} = {hi}: not a strict high")
    return {"low": str(lo), "high": str(hi), "low_scenario": lo_id, "high_scenario": hi_id,
            "values": {k: str(v) for k, v in vals.items()}}


def scenario_view(table: dict, picks: dict) -> dict:
    """table: {family: {scenario_id: value}}; picks: {family: scenario_id}. One scenario across every family."""
    ids = set(picks.values())
    if len(ids) != 1:
        raise T595Error(f"scenario view mixes interpretations {sorted(ids)}: one scenario across every family")
    sid = ids.pop()
    out = {}
    for fam in picks:
        if fam not in table or sid not in table[fam]:
            raise T595Error(f"{fam}: scenario {sid} not measured (SCENARIO_SPLIT_OPEN)")
        out[fam] = str(d6(table[fam][sid]))
    return {"scenario": sid, "values": out}
