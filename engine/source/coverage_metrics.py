"""Coverage metrics per trade (generic) - explain WHY a quantity is low, not only how low.

    POPULATION %        occurrences with a terminal record that is not UNQUANTIFIED / occurrences admitted
    GEOMETRY %          per measured dimension: occurrences with that dimension known / occurrences
    SEMANTIC %          occurrences whose type / role is established
    SOURCE_AUTHORITY %  occurrences whose quantity rests on source facts only
    QUANTITY %          official quantity / best-provisional quantity (official coverage of the likely scope)
                        and best-provisional / (best-provisional + nothing unquantified) as provisional coverage
    BBS %               reinforcement components quantified / components required (when given)

All metrics are ratios of the engine's own records - no reference total enters. Stdlib only.
"""

from __future__ import annotations


def _pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def trade_coverage(trade, occurrences, *, official_qty=None, best_qty=None, bbs_quantified=None, bbs_required=None,
                   dimensions=()):
    """occurrences: [{terminal_state, known: {dim: bool}, semantic_established: bool, source_only: bool,
    unquantified_components: int}]."""
    n = len(occurrences)
    quantified = sum(1 for o in occurrences if o.get("terminal_state") != "UNQUANTIFIED")
    geo = {d: _pct(sum(1 for o in occurrences if (o.get("known") or {}).get(d)), n) for d in dimensions}
    sem = _pct(sum(1 for o in occurrences if o.get("semantic_established")), n)
    src = _pct(sum(1 for o in occurrences if o.get("source_only")), n)
    unq = sum(o.get("unquantified_components", 0) for o in occurrences)
    return {"trade": trade, "occurrences": n, "population_pct": _pct(quantified, n), "geometry_pct": geo,
            "semantic_pct": sem, "source_authority_pct": src,
            "quantity_official_pct_of_best": _pct(official_qty or 0.0, best_qty) if best_qty else None,
            "quantity_provisional_pct": None if n == 0 else _pct(quantified, n),
            "unquantified_components": unq,
            "bbs_pct": _pct(bbs_quantified or 0, bbs_required) if bbs_required else None,
            "basis": "ratios of the engine's own terminal records; no reference quantity used"}


def before_after(before, after):
    """Per-metric delta between two trade_coverage results of the same trade."""
    keys = ("population_pct", "semantic_pct", "source_authority_pct", "quantity_official_pct_of_best",
            "quantity_provisional_pct", "bbs_pct")
    out = {"trade": after["trade"]}
    for k in keys:
        b, a = before.get(k), after.get(k)
        out[k] = {"before": b, "after": a, "delta": None if a is None or b is None else round(a - b, 1)}
    return out
