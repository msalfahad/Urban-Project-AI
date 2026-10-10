"""COLUMN_CONCRETE_GEOMETRY - column concrete independent of column reinforcement (generic).

Rebar uncertainty (tie topology, laps, starters, section transitions, unbound upper members) never blocks concrete.
Every column occurrence with a section and a vertical interval produces a concrete geometry record:

    GROSS_INTERVAL      B x D x storey interval (the occurrence's own interval and its state)
    NET_OF_SLAB         B x D x (interval - slab thickness above)   - the column + joint body when the slab plate is
                        measured full depth over the column (no double count with the slab)
    CLEAR_BELOW_BEAMS   only when the governing beam depth is known (otherwise UNQUANTIFIED in that basis only)

COLUMN_CONCRETE_CONSERVATION: occurrences in = concrete records out. An occurrence without a section is kept as
UNQUANTIFIED with its identity. Rebar fields in the input are refused, so no rebar blocker can reach this module.
Stdlib only.
"""

from __future__ import annotations

from engine.source import population_conservation as PC
from engine.source import quantity_scenarios as QS

_REBAR_FIELDS = ("rebar", "tie", "lap", "starter", "bar", "kg")


class ColumnConcreteError(ValueError):
    pass


def record(occ, *, slab_t_m=None, slab_t_low_m=None, slab_t_high_m=None, interval_low_m=None, interval_high_m=None):
    """occ: {occurrence_id, B_m, D_m, interval_m, interval_state (ESTABLISHED/LOWER_BOUND/BOUNDED),
    floor, source_handles, beam_depth_m?}."""
    bad = [k for k in occ if any(w in k.lower() for w in _REBAR_FIELDS)]
    if bad:
        raise ColumnConcreteError(f"{occ['occurrence_id']}: reinforcement fields {bad} cannot enter concrete geometry")
    base = {"occurrence_id": occ["occurrence_id"], "source_handles": occ.get("source_handles", []),
            "position": occ.get("position"), "count": 1,
            "known_geometry": {k: occ.get(k) for k in ("B_m", "D_m", "interval_m", "floor")},
            "candidate_definitions": occ.get("candidate_definitions", [])}
    B, D, H = occ.get("B_m"), occ.get("D_m"), occ.get("interval_m")
    if not (B and D and H):
        part = QS.part(occ["occurrence_id"], "UNQUANTIFIED", why="section or interval unknown")
        return {"occurrence_id": occ["occurrence_id"], "gross_m3": None, "net_of_slab_m3": None, "part": part,
                "terminal": PC.terminal(base, "UNQUANTIFIED", unresolved=["SECTION_OR_INTERVAL"])}
    A = B * D
    gross = A * H
    t = slab_t_m or 0.0
    net = A * (H - t)
    st = occ.get("interval_state", "ESTABLISHED")
    lo_h = interval_low_m if interval_low_m is not None else H
    hi_h = interval_high_m if interval_high_m is not None else H
    tl = slab_t_high_m if slab_t_high_m is not None else t        # thicker slab -> less column body
    th = slab_t_low_m if slab_t_low_m is not None else t
    if st == "ESTABLISHED" and lo_h == hi_h:
        if tl == th:
            part = QS.part(occ["occurrence_id"], "VERIFIED", net, origin="DERIVED")
        else:
            part = QS.part(occ["occurrence_id"], "PROVISIONAL", net, A * (H - tl), A * (H - th), origin="DERIVED",
                           why="slab thickness range above the column")
        state = "MEASURED_COMPLETE"
    elif st == "LOWER_BOUND" and interval_high_m is None:
        part = QS.part(occ["occurrence_id"], "LOWER_BOUND", net, origin="DERIVED")
        state = "BOUNDED_QUANTIFIED"
    else:
        part = QS.part(occ["occurrence_id"], "PROVISIONAL", net, min(net, A * (lo_h - tl)), max(net, A * (hi_h - th)),
                       origin="DERIVED", why=f"interval {st}")
        state = "BOUNDED_QUANTIFIED"
    clear = None
    if occ.get("beam_depth_m") is not None:
        clear = A * (H - occ["beam_depth_m"])
    unresolved = [] if state == "MEASURED_COMPLETE" else ["INTERVAL"]
    if state == "MEASURED_COMPLETE" and part["state"] != "VERIFIED":
        state = "BOUNDED_QUANTIFIED"
        unresolved = ["SLAB_THICKNESS"]
    return {"occurrence_id": occ["occurrence_id"], "floor": occ.get("floor"), "A_m2": A, "gross_m3": gross,
            "net_of_slab_m3": net, "clear_below_beams_m3": clear, "part": part,
            "terminal": PC.terminal(base, state, quantity=net, unresolved=unresolved)}


def conserve(occurrences, records):
    """COLUMN_CONCRETE_CONSERVATION: occurrence count in = concrete geometry terminal records out."""
    return PC.require_conserved([{"occurrence_id": o["occurrence_id"]} for o in occurrences],
                                [r["terminal"] for r in records])
