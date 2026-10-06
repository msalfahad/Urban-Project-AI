"""Best-available quantity without pretending it is verified (generic).

Every physical occurrence (and every roll-up) publishes six separate layers:

    VERIFIED_QUANTITY           only parts whose value is VERIFIED
    LOWER_BOUND_QUANTITY        VERIFIED + proven minimum of LOWER_BOUND parts
    BEST_PROVISIONAL_QUANTITY   LOWER_BOUND + best value of PROVISIONAL / CANDIDATE / conflict parts
    LOW_SCENARIO / HIGH_SCENARIO  the bracket of the best provisional value
    UNQUANTIFIED_COMPONENTS     parts that exist but have no value (never a zero)

Invariant: VERIFIED <= LOWER_BOUND <= LOW <= BEST <= HIGH. A provisional value can never enter the VERIFIED or
LOWER_BOUND layers; layers are summed separately and never mixed. HIGH is None (UNBOUNDED) when any part has no
upper bound. Stdlib only.
"""

from __future__ import annotations

PART_STATES = ("VERIFIED", "LOWER_BOUND", "PROVISIONAL", "SOURCE_CONFLICT", "CANDIDATE", "UNQUANTIFIED")
_PROV = ("PROVISIONAL", "SOURCE_CONFLICT", "CANDIDATE")
EPS = 1e-9


class ScenarioError(ValueError):
    pass


def part(part_id, state, best=None, low=None, high=None, *, origin=None, why=None, unit=None):
    """One contributing part. VERIFIED: low = best = high. LOWER_BOUND: best is the proven minimum (low = best),
    high may be None (unbounded). Provisional kinds: low <= best <= high. UNQUANTIFIED: no value."""
    if state not in PART_STATES:
        raise ScenarioError(f"{part_id}: unknown part state {state}")
    if state == "UNQUANTIFIED":
        if any(v is not None for v in (best, low, high)):
            raise ScenarioError(f"{part_id}: an UNQUANTIFIED part carries no value")
        return {"part_id": part_id, "state": state, "best": None, "low": None, "high": None, "origin": origin,
                "why": why, "unit": unit}
    if best is None:
        raise ScenarioError(f"{part_id}: {state} needs a best value")
    low = best if low is None and state in ("VERIFIED", "LOWER_BOUND") else low
    if state == "VERIFIED":
        high = best if high is None else high
        if abs(low - best) > EPS or abs(high - best) > EPS:
            raise ScenarioError(f"{part_id}: a VERIFIED part has no range")
    if state in _PROV and (low is None or high is None):
        raise ScenarioError(f"{part_id}: a {state} part needs low and high")
    if low is not None and low > best + EPS:
        raise ScenarioError(f"{part_id}: low > best")
    if high is not None and high < best - EPS:
        raise ScenarioError(f"{part_id}: high < best")
    return {"part_id": part_id, "state": state, "best": best, "low": low, "high": high, "origin": origin,
            "why": why, "unit": unit}


def combine(parts, *, unit=None):
    """Roll parts up into the six layers (each summed separately)."""
    seen = set()
    v = lb = best = low = 0.0
    high = 0.0
    unbounded = False
    unq = []
    for p in parts:
        if p["part_id"] in seen:
            raise ScenarioError(f"part {p['part_id']} entered twice")
        seen.add(p["part_id"])
        st = p["state"]
        if st == "UNQUANTIFIED":
            unq.append({"part_id": p["part_id"], "why": p.get("why")})
            continue
        if st == "VERIFIED":
            v += p["best"]
            lb += p["best"]
            best += p["best"]
            low += p["best"]
        elif st == "LOWER_BOUND":
            lb += p["best"]
            best += p["best"]
            low += p["best"]
        else:
            best += p["best"]
            low += p["low"]
        if p["high"] is None:
            unbounded = True
        else:
            high += p["high"]
    q = {"VERIFIED_QUANTITY": v, "LOWER_BOUND_QUANTITY": lb, "BEST_PROVISIONAL_QUANTITY": best,
         "LOW_SCENARIO": low, "HIGH_SCENARIO": None if unbounded else high,
         "UNQUANTIFIED_COMPONENTS": unq, "unit": unit, "parts": len(seen)}
    check(q)
    return q


def check(q):
    """VERIFIED <= LOWER_BOUND <= LOW <= BEST <= HIGH (HIGH may be unbounded)."""
    v, lb, lo, b, hi = (q["VERIFIED_QUANTITY"], q["LOWER_BOUND_QUANTITY"], q["LOW_SCENARIO"],
                        q["BEST_PROVISIONAL_QUANTITY"], q["HIGH_SCENARIO"])
    ok = v <= lb + EPS and lb <= lo + EPS and lo <= b + EPS and (hi is None or b <= hi + EPS)
    if not ok:
        raise ScenarioError(f"scenario layers out of order: {v}, {lb}, {lo}, {b}, {hi}")
    return True


def scale(q, k, unit=None):
    """Multiply every layer by k (k >= 0) - e.g. area -> volume at a VERIFIED thickness."""
    if k < 0:
        raise ScenarioError("negative scale")
    out = dict(q)
    for key in ("VERIFIED_QUANTITY", "LOWER_BOUND_QUANTITY", "BEST_PROVISIONAL_QUANTITY", "LOW_SCENARIO"):
        out[key] = q[key] * k
    out["HIGH_SCENARIO"] = None if q["HIGH_SCENARIO"] is None else q["HIGH_SCENARIO"] * k
    out["unit"] = unit or q.get("unit")
    return out


def release_label(q):
    """What the BOQ may call it: OFFICIAL only when nothing provisional or unquantified remains."""
    if q["BEST_PROVISIONAL_QUANTITY"] > q["LOWER_BOUND_QUANTITY"] + EPS or q["UNQUANTIFIED_COMPONENTS"]:
        return "PROVISIONAL_ONLY" if q["LOWER_BOUND_QUANTITY"] <= EPS else "PARTIAL_WITH_PROVISIONAL"
    if q["LOWER_BOUND_QUANTITY"] > q["VERIFIED_QUANTITY"] + EPS:
        return "LOWER_BOUND"
    return "OFFICIAL"


def rounded(q, n=3):
    out = dict(q)
    for k in ("VERIFIED_QUANTITY", "LOWER_BOUND_QUANTITY", "BEST_PROVISIONAL_QUANTITY", "LOW_SCENARIO",
              "HIGH_SCENARIO"):
        out[k] = None if q[k] is None else round(q[k], n)
    return out


# technical (release) classes that are established values / proven minimums
_TECH_VERIFIED = ("COMPUTED", "DERIVED", "OWNER_PROJECT_FACT", "VERIFIED")
_TECH_LOWER = ("PARTIAL", "LOWER_BOUND")


def parts_from_release(part_id, technical, commercial):
    """Turn a two-layer BOQ line (technical release + commercial / provisional layer) into scenario parts, so a
    technically BLOCKED line keeps its provisional value instead of becoming zero.

    technical: {class, qty, in_total}; commercial: {class, qty, low, high, budget, provisional} (may be empty).
    - technical value in the total: VERIFIED (or LOWER_BOUND for PARTIAL); a larger commercial value adds the
      difference as a PROVISIONAL part (never merged into the technical value)
    - no technical value, commercial value present: PROVISIONAL (BUDGET -> CANDIDATE with low 0 when no low given)
    - neither: UNQUANTIFIED (the line still exists)."""
    technical = technical or {}
    commercial = commercial or {}
    tq, cq = technical.get("qty"), commercial.get("qty")
    out = []
    if tq is not None and technical.get("in_total", True):
        st = "LOWER_BOUND" if technical.get("class") in _TECH_LOWER else "VERIFIED"
        out.append(part(f"{part_id}:T", st, tq, origin="SOURCE_FACT" if st == "VERIFIED" else "DERIVED"))
        if cq is not None and cq > tq + EPS:
            lo = max(0.0, (commercial.get("low") if commercial.get("low") is not None else cq) - tq)
            hi = max(cq, commercial.get("high") if commercial.get("high") is not None else cq) - tq
            out.append(part(f"{part_id}:C", "PROVISIONAL", cq - tq, min(lo, cq - tq), hi, origin="URBAN_PROVISIONAL",
                            why=f"commercial {commercial.get('class')} above the technical value"))
        return out
    if cq is not None:
        kind = "CANDIDATE" if commercial.get("budget") else "PROVISIONAL"
        lo = commercial.get("low")
        lo = (0.0 if kind == "CANDIDATE" else cq) if lo is None else lo
        hi = commercial.get("high") if commercial.get("high") is not None else cq
        out.append(part(f"{part_id}:C", kind, cq, min(lo, cq), max(hi, cq), origin="URBAN_PROVISIONAL",
                        why=f"technical {technical.get('class')}; commercial {commercial.get('class')}"))
        return out
    return [part(f"{part_id}:U", "UNQUANTIFIED", why=f"technical {technical.get('class')}, no commercial value")]
