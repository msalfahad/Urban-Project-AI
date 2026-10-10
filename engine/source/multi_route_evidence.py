"""Multi-route evidence for high-impact elements (generic).

Two or more independent extractors (e.g. tag-to-schedule vs parallel-face for beams, topology vs face pairing for
walls, closed boundary vs cell union for slabs) each propose physical objects with a geometric key. Objects are
matched across routes by key (or a caller-supplied matcher); one physical object is kept once:

    all routes agree within tolerance   -> CONFIDENCE_UP
    routes disagree                     -> ROUTE_CONFLICT  (values kept side by side, never averaged)
    only one route sees it              -> SINGLE_ROUTE

Stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

CONFIDENCE_UP, ROUTE_CONFLICT, SINGLE_ROUTE = "CONFIDENCE_UP", "ROUTE_CONFLICT", "SINGLE_ROUTE"


class RouteError(ValueError):
    pass


def reconcile(routes, *, rel_tol=0.02, abs_tol=1e-6, key="key", value="value"):
    """routes: {route_name: [{key, value, ...}]}. A route may not list the same key twice (one object once)."""
    by_key = defaultdict(dict)
    for rname, objs in routes.items():
        for o in objs:
            k = o[key]
            if k in by_key and rname in by_key[k]:
                raise RouteError(f"route {rname} lists {k} twice")
            by_key[k][rname] = o
    out = []
    for k in sorted(by_key, key=str):
        seen = by_key[k]
        vals = {r: o.get(value) for r, o in seen.items()}
        if len(seen) == 1:
            state = SINGLE_ROUTE
        else:
            vs = [v for v in vals.values() if v is not None]
            ref = max(abs(v) for v in vs) if vs else 0.0
            agree = len(vs) == len(vals) and max(vs) - min(vs) <= max(abs_tol, rel_tol * ref)
            state = CONFIDENCE_UP if agree else ROUTE_CONFLICT
        out.append({"key": k, "routes": sorted(seen), "values": vals, "state": state,
                    "value": vals[sorted(seen)[0]] if state == CONFIDENCE_UP else None})
    return out


def physical_objects(reconciled):
    """One record per physical object (never one per route)."""
    keys = [r["key"] for r in reconciled]
    if len(keys) != len(set(keys)):
        raise RouteError("a physical object appears twice after reconciliation")
    return reconciled
