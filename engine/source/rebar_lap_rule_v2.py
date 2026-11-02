"""REBAR LAP RULE V2 (task T-459, owner directive 2026-11-02 C4) - the lap LENGTH of a bar group by element class and
the lap-aware splice COUNT in one call, as a NEW rule version beside the frozen route G conventions. An unwired
producer: nothing in engine/ or tools/ imports it; continuous_beams (frozen), generic_route, the V6 convention profile
and every released or candidate route are unchanged.

Physical element. A lap splice is the overlap of two bars of one continuous bar group: where a run L is longer than the
stock bar S it is built from pieces joined by laps, each lap a length of really installed steel. A column's main bars
are spliced once per storey joint (each storey's bars = storey height + one lap); a beam / slab / footing bar is
spliced only where its run exceeds the stock.

What V2 changes against route G (URBAN_M*_GENERIC_CONVENTIONS_V6, BEAM_LAP_D and COLUMN_LAP_D):
  (1) LENGTH. Route G applies a 40 / 50 / 60 d low / base / high spread (provenance STANDARD_PRACTICE, no owner or
      drawing source) to columns AND beams alike, base 50 d. V2 takes the lap from the governing authority of the bar
      group, in the order of rebar_laps_v1.resolve_lap (lap schedule -> approved detail -> drawing note for the groups
      it names -> owner convention), and the owner convention is by element class: 40 d columns / ordinary walls, 60 d
      beams / slabs / retaining walls / footings (OWNER_RULE_REBAR_2026-10-24 s.2, restated as C4 on 2026-11-02). The
      convention is ONE value (low = base = high), PROVISIONAL, never applied where a drawing source names the group.
  (2) COUNT. laps = 0 if L <= S, else ceil((L - S) / (S - lap)) in exact rationals (rebar_laps_v1.lap_count_exact,
      = CONTINUOUS_BEAM_LAPS_V2 = bbs_optimiser.split_run); the frozen ceil(L / S) - 1 misses one lap on the windows
      S + k (S - lap) < L <= (k + 1) S (D-T273-01, T-375).
No assumption: an element class with no owner value, a missing diameter, a 'not less than' note or an unprinted
tension / compression zone gives HELD (length None), never 0 and never a default; a run within the stock needs no lap
whatever its length, so it is NOT_REQUIRED even when the lap is HELD.
Stdlib + rebar_laps_v1 only; project-agnostic (no project name, sheet or member id in this module).
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction

from engine.source import rebar_laps_v1 as RL

RULE_ID = "REBAR_LAP_RULE_V2"
SUPERSEDES_FOR_LAPS = ("URBAN_M8_GENERIC_CONVENTIONS_V6:BEAM_LAP_D", "URBAN_M8_GENERIC_CONVENTIONS_V6:COLUMN_LAP_D",
                       "continuous_beams._with_laps (count, D-T273-01)")
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
OWNER_SOURCE = "OWNER_RULE_REBAR_2026-10-24 s.2; owner directive 2026-11-02 C4"

# the owner's classes (rebar_laps_v1.OWNER_CONVENTION_D) and the route G family / member names that map onto them;
# anything else is not classified (HELD), never guessed
CLASS_ALIASES = {
    "COLUMN": "COLUMN", "COLUMNS": "COLUMN", "NECK": "COLUMN", "WALL": "WALL",
    "BEAM": "BEAM", "BEAMS": "BEAM", "CONTINUOUS_BEAM": "BEAM", "GROUND_BEAM": "GROUND_BEAM", "TIE_BEAM": "GROUND_BEAM",
    "STRAP_BEAM": "GROUND_BEAM", "SLAB": "SLAB", "SLABS": "SLAB", "RETAINING_WALL": "RETAINING_WALL",
    "FOOTING": "FOOTING", "FOOTINGS": "FOOTING", "RAFT": "FOOTING",
}
NOT_REQUIRED, HELD, PROVISIONAL, DRAWING_CONFIRMED, BLOCKED = (
    RL.NOT_REQUIRED, RL.HELD, RL.PROVISIONAL, RL.DRAWING_CONFIRMED, RL.BLOCKED)


class LapRuleError(ValueError):
    pass


def _q(value, unit="m"):
    """an exact length in metres; a Fraction already in metres passes through (internal calls)."""
    if isinstance(value, Fraction):
        if value < 0:
            raise LapRuleError(f"length {value} negative")
        return value
    return RL.length_exact_m(value, unit)


def _ceil(q):
    return -((-q.numerator) // q.denominator)


def element_class(kind):
    """the owner class of an element / route G family name, or None when it has none (-> HELD)."""
    if kind is None:
        return None
    return CLASS_ALIASES.get(str(kind).strip().upper())


def lap_factor_d(kind):
    """the owner convention factor (x d) of an element kind, or None."""
    c = element_class(kind)
    return None if c is None else RL.OWNER_CONVENTION_D.get(c)


def class_lap(kind, dia_mm, authorities=(), *, zone=None):
    """the lap of one bar group: rebar_laps_v1.resolve_lap with the owner convention allowed, by element class.
    -> {"state", "lap_m", "lap_min_m", "basis", "ref", "findings", "element_class"}."""
    c = element_class(kind)
    group = {"element_kind": c, "dia_mm": dia_mm, "zone": zone}
    res = RL.resolve_lap(group, list(authorities), convention_allowed=c is not None)
    if res["state"] == DRAWING_CONFIRMED and c is not None and RL.OWNER_CONVENTION_D.get(c) is not None:
        res = dict(res, findings=list(res.get("findings") or []) +
                   [f"owner convention {RL.OWNER_CONVENTION_D[c]} d not applied: {res.get('ref')} governs this group"])
    if c is None and res["state"] != DRAWING_CONFIRMED:
        res = dict(res, state=HELD, lap_m=None,
                   basis=f"element kind {kind!r} has no owner lap class and no drawing source names it")
    return dict(res, element_class=c)


def bar_with_laps(run, dia_mm, kind, *, stock=12, authorities=(), unit="m", zone=None):
    """one continuous bar run with its laps. run / stock as read (decimal text, mm integer with unit 'mm', Decimal or
    float). -> {"run_m", "lap_m", "laps", "length_m", "state", "basis", "ref", "findings"}; lengths are floats of the
    exact rationals (the count is exact). A run within the stock: laps 0, NOT_REQUIRED, whatever the lap."""
    L = _q(run, unit)
    S = _q(stock, unit)
    if S <= 0:
        raise LapRuleError("stock length not given")
    base = {"run_m": float(L), "stock_m": float(S), "element_class": element_class(kind), "dia_mm": dia_mm}
    if L <= S:
        return dict(base, lap_m=None, laps=0, length_m=float(L), state=NOT_REQUIRED,
                    basis="run within the stock bar: no splice for any lap length", ref=None, findings=[])
    lap = class_lap(kind, dia_mm, authorities, zone=zone)
    if lap["lap_m"] is None:
        inv = RL.count_invariance(float(L), float(S))
        return dict(base, lap_m=None, lap_min_m=lap.get("lap_min_m"), laps=None, length_m=None, state=HELD,
                    basis=lap["basis"], ref=lap.get("ref"),
                    findings=list(lap.get("findings") or []) +
                    [f"{inv['count']} splice(s) per bar for any lap up to {inv['lap_max_m']} m; length HELD with the lap"])
    lap_q = Fraction(str(lap["lap_m"]))
    if lap_q >= S:
        return dict(base, lap_m=float(lap_q), laps=None, length_m=None, state=BLOCKED,
                    basis=f"lap {float(lap_q)} m not shorter than the stock {float(S)} m", ref=lap.get("ref"),
                    findings=["LAP_NOT_SHORTER_THAN_STOCK"])
    n = _ceil((L - S) / (S - lap_q))         # = rebar_laps_v1.lap_count_exact, on the exact values
    return dict(base, lap_m=float(lap_q), laps=n, length_m=float(L + n * lap_q), state=lap["state"],
                basis=lap["basis"], ref=lap.get("ref"), findings=list(lap.get("findings") or []))


def storey_bar(height, dia_mm, *, kind="COLUMN", stock=12, authorities=(), unit="m"):
    """a column / wall main bar of one storey: storey height + ONE lap at the joint above (route G's form, with the
    class lap), plus any extra splices if that length itself exceeds the stock. -> as bar_with_laps, length_m includes
    the storey lap."""
    H = _q(height, unit)
    lap = class_lap(kind, dia_mm, authorities)
    if lap["lap_m"] is None:
        return {"run_m": float(H), "lap_m": None, "laps": None, "length_m": None, "state": HELD, "basis": lap["basis"],
                "ref": lap.get("ref"), "findings": list(lap.get("findings") or []), "element_class": lap["element_class"]}
    lap_q = Fraction(str(lap["lap_m"]))
    run = H + lap_q
    r = bar_with_laps(run, dia_mm, kind, stock=_q(stock, unit), authorities=authorities)
    extra = r["laps"] or 0
    return dict(r, run_m=float(H), laps=1 + extra, length_m=float(run + extra * lap_q), lap_m=float(lap_q),
                state=lap["state"], basis=f"storey height + 1 storey lap; {lap['basis']}", ref=lap.get("ref"))


def frozen_route_g(run_m, dia_mm, lap_d, stock_m=12.0):
    """the frozen route G length (continuous_beams._with_laps form, D-T273-01), for before / after only."""
    return RL.frozen_with_laps(run_m, dia_mm, lap_d, stock_m)


def route_g_triple_v2(kind):
    """the lap factor triple a NEW route G convention version would carry for a family: the owner class value once
    (low = base = high), or None (HELD) for a family with no class."""
    f = lap_factor_d(kind)
    return None if f is None else (float(f), float(f), float(f))


def policy_record():
    rec = {"rule_id": RULE_ID, "supersedes_for_laps": list(SUPERSEDES_FOR_LAPS), "guard": DEFAULT_GUARD_CLASS,
           "owner_source": OWNER_SOURCE, "owner_convention_d": RL.OWNER_CONVENTION_D, "aliases": CLASS_ALIASES,
           "status_of_convention": PROVISIONAL, "authority_order": list(RL.TIERS),
           "count": "laps = 0 if L <= S else ceil((L - S) / (S - lap)), exact rationals (rebar_laps_v1.lap_count_exact)",
           "never": ["the 40 / 50 / 60 d spread as a lap", "one lap value for columns and beams alike",
                     "a held lap shown as 0", "a lap where the run is within the stock",
                     "the owner convention where a drawing source names the group"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
