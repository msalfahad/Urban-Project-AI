"""PROVISIONAL ESTIMATE (M1) - a planning estimate beside the verified release, never mixed into it (generic).

Every quantity item belongs to exactly one category:

    VERIFIED      source-supported and eligible under the strict release rules (a released row of a frozen stage);
                  low = base = high, no assumption
    PROVISIONAL   calculated from drawn / printed geometry with explicit, configurable assumptions; low <= base <= high;
                  every item names the assumptions it uses (or the frozen-stage model it reuses). On a new project
                  nothing is VERIFIED: an item whose every dimension is printed and whose outline the drawing confirms
                  is PROVISIONAL with support SOURCE_COMPLETE_UNREVIEWED (a release candidate, not a release)
    UNRESOLVED    not enough geometry for a defensible calculation; it carries no base value and never enters a total.
                  It may carry an indicative exposure range or a parameterised expression, shown on its own

Conventions are data: a convention set (JSON) lists every assumption with its value, its low / high alternatives,
its provenance and its rationale. An item never hard-codes an assumed dimension: it reads it from the set, so a changed
assumption recomputes the estimate (reversible). Choice-type conventions (a reading of a printed value, e.g. what a
beam depth is measured from) name the options; the base option is explicit and the alternatives give low / high.

Totals (rollup):
    verified                    sum of VERIFIED
    provisional low / base / high
    planning low / base / high  verified + provisional (the two never overlap: a component id is owned by one item)
    unresolved                  count, plus the exposure range of those that have one (never added)
The low and high columns sum each item's own low / high: they are planning brackets, not a joint confidence interval,
and mutually exclusive readings are never added (each item holds one reading as base and the others as its range).

Stdlib only; layers are checked with engine.source.quantity_scenarios (VERIFIED <= LOW <= BASE <= HIGH).
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from engine.source import quantity_scenarios as QS

CATEGORIES = ("VERIFIED", "PROVISIONAL", "UNRESOLVED")
TRADES = ("CONCRETE", "REINFORCEMENT")
UNITS = {"CONCRETE": "m3", "REINFORCEMENT": "kg"}
PROVENANCE = ("PRINTED_VALUE", "PRINTED_MINIMUM", "PRINTED_PROJECT_DEFAULT", "PRINTED_TYPICAL_DETAIL",
              "READING_OF_PRINTED_VALUE", "DRAWN_GEOMETRY", "FROZEN_STAGE_MODEL", "STANDARD_PRACTICE",
              "ENGINEERING_JUDGEMENT")
SUPPORT = ("RELEASED", "SOURCE_COMPLETE_UNREVIEWED", "CONVENTION_ONLY", "FROZEN_STAGE_MODEL", "ONE_ASSUMED_DIMENSION",
           "ASSUMPTION_DOMINATED", "NO_GEOMETRY")
CONFIDENCE = ("HIGH", "MEDIUM", "LOW")
EPS = 1e-9


class EstimateError(ValueError):
    pass


# ------------------------------------------------------------------ conventions
class Conventions:
    """A validated convention set. Number conventions: base / low / high (low <= base <= high, in `unit`).
    Choice conventions: base is one of `options`; the alternatives are the other options."""

    REQUIRED = ("id", "title", "kind", "base", "provenance", "source", "rationale")

    def __init__(self, data, overrides=None):
        if not isinstance(data, dict) or "conventions" not in data:
            raise EstimateError("a convention set is {'set': ..., 'conventions': [...]}")
        self.name = data.get("set", "unnamed")
        self.items = {}
        for c in data["conventions"]:
            miss = [k for k in self.REQUIRED if k not in c]
            if miss:
                raise EstimateError(f"convention {c.get('id')}: missing {miss}")
            if c["id"] in self.items:
                raise EstimateError(f"convention {c['id']} defined twice")
            if c["provenance"] not in PROVENANCE:
                raise EstimateError(f"convention {c['id']}: unknown provenance {c['provenance']}")
            c = dict(c)
            self._check(c)
            self.items[c["id"]] = c
        self.overrides = {}
        for k, v in (overrides or {}).items():
            if k not in self.items:
                raise EstimateError(f"override of an unknown convention {k}")
            c = dict(self.items[k], base=v, overridden_from=self.items[k]["base"])
            if c["kind"] == "number":
                c["base"] = float(v)
                c["low"], c["high"] = min(c["low"], c["base"]), max(c["high"], c["base"])
            self._check(c)
            self.items[k] = c
            self.overrides[k] = v

    @staticmethod
    def _check(c):
        if c["kind"] == "number":
            for k in ("low", "high"):
                if not isinstance(c.get(k), (int, float)):
                    raise EstimateError(f"convention {c['id']}: a number needs low and high")
            if not (c["low"] - EPS <= c["base"] <= c["high"] + EPS):
                raise EstimateError(f"convention {c['id']}: low <= base <= high fails")
        elif c["kind"] == "choice":
            if not c.get("options") or c["base"] not in c["options"]:
                raise EstimateError(f"convention {c['id']}: the base must be one of the options")
        else:
            raise EstimateError(f"convention {c['id']}: kind is number or choice")

    def __getitem__(self, cid):
        if cid not in self.items:
            raise EstimateError(f"unknown convention {cid}")
        return self.items[cid]

    def base(self, cid):
        return self[cid]["base"]

    def triple(self, cid):
        c = self[cid]
        if c["kind"] != "number":
            raise EstimateError(f"{cid} is a choice")
        return float(c["low"]), float(c["base"]), float(c["high"])

    def register(self):
        return [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in c.items()}
                for c in self.items.values()]

    def digest(self):
        import hashlib
        return hashlib.sha256(json.dumps({"set": self.name, "c": sorted(self.items.items())}, sort_keys=True,
                                         default=str).encode()).hexdigest()


def load_conventions(path, overrides=None):
    with open(path, encoding="utf-8") as fh:
        return Conventions(json.load(fh), overrides)


def by_choice(conv, cid, values):
    """values: {option: quantity}. base = the configured option; low / high = the min / max over every option that
    has a value. A missing option value is never a zero."""
    have = {k: v for k, v in values.items() if v is not None}
    b = conv.base(cid)
    if b not in have:
        raise EstimateError(f"{cid}: the base option {b} has no value")
    return min(have.values()), have[b], max(have.values())


def linear(conv, cid, coeff, const=0.0):
    """quantity = const + coeff x parameter, evaluated at the parameter's low / base / high (sorted)."""
    lo, b, hi = conv.triple(cid)
    vals = sorted(const + coeff * x for x in (lo, b, hi))
    return vals[0], const + coeff * b, vals[2]


# ------------------------------------------------------------------ items
ITEM_KEYS = ("item_id", "component_id", "trade", "family", "storey", "category", "unit", "low", "base", "high",
             "dia_mm", "source", "dimensions", "formula", "assumptions", "support", "confidence", "limitations",
             "double_count_risk", "blocker", "exposure_low", "exposure_high", "expression", "part")


def item(*, item_id, component_id, trade, family, storey, category, base=None, low=None, high=None, dia_mm=None,
         source, dimensions=None, formula="", assumptions=(), support, confidence, limitations="",
         double_count_risk="", blocker="", exposure_low=None, exposure_high=None, expression="", part="WHOLE"):
    if trade not in TRADES:
        raise EstimateError(f"{item_id}: trade {trade}")
    if category not in CATEGORIES:
        raise EstimateError(f"{item_id}: category {category}")
    if support not in SUPPORT:
        raise EstimateError(f"{item_id}: support {support}")
    if confidence not in CONFIDENCE:
        raise EstimateError(f"{item_id}: confidence {confidence}")
    if not source:
        raise EstimateError(f"{item_id}: every item names its source")
    assumptions = list(assumptions)
    if category == "VERIFIED":
        if base is None:
            raise EstimateError(f"{item_id}: a VERIFIED item has a value")
        low = base if low is None else low
        high = base if high is None else high
        if abs(low - base) > EPS or abs(high - base) > EPS or assumptions or support != "RELEASED":
            raise EstimateError(f"{item_id}: a VERIFIED item has no range, no assumption and support RELEASED")
    elif category == "PROVISIONAL":
        if None in (low, base, high):
            raise EstimateError(f"{item_id}: a PROVISIONAL item needs low, base and high")
        if not (low - EPS <= base <= high + EPS) or low < -EPS:
            raise EstimateError(f"{item_id}: 0 <= low <= base <= high fails ({low}, {base}, {high})")
        if not assumptions:
            raise EstimateError(f"{item_id}: a PROVISIONAL item names its assumptions")
        if support in ("RELEASED", "ASSUMPTION_DOMINATED", "NO_GEOMETRY"):
            raise EstimateError(f"{item_id}: support {support} is not a provisional basis")
        if not formula:
            raise EstimateError(f"{item_id}: a PROVISIONAL item states its formula")
    else:
        if any(v is not None for v in (low, base, high)):
            raise EstimateError(f"{item_id}: an UNRESOLVED item carries no value (use the exposure range)")
        if (exposure_low is None) != (exposure_high is None):
            raise EstimateError(f"{item_id}: an exposure range needs both ends")
        if exposure_low is not None and exposure_low > exposure_high + EPS:
            raise EstimateError(f"{item_id}: exposure low > high")
        if not blocker:
            raise EstimateError(f"{item_id}: an UNRESOLVED item names what blocks it")
    if trade == "REINFORCEMENT" and category != "UNRESOLVED" and dia_mm is None:
        raise EstimateError(f"{item_id}: quantified reinforcement carries its bar diameter")
    return {"item_id": item_id, "component_id": component_id, "trade": trade, "family": family, "storey": storey,
            "category": category, "unit": UNITS[trade], "low": low, "base": base, "high": high, "dia_mm": dia_mm,
            "source": source, "dimensions": dimensions or {}, "formula": formula, "assumptions": assumptions,
            "support": support, "confidence": confidence, "limitations": limitations,
            "double_count_risk": double_count_risk, "blocker": blocker, "exposure_low": exposure_low,
            "exposure_high": exposure_high, "expression": expression, "part": part}


def check(items, conv=None):
    """Unique item ids; one owner per (trade, component, part); every cited assumption exists in the set; each layer
    rolls up in order (quantity_scenarios)."""
    ids = [i["item_id"] for i in items]
    if len(set(ids)) != len(ids):
        dup = sorted({x for x in ids if ids.count(x) > 1})
        raise EstimateError(f"duplicate item ids {dup[:5]}")
    owner = {}
    for i in items:
        if i["trade"] == "REINFORCEMENT":
            continue
        k = (i["trade"], i["component_id"], i["part"])
        if k in owner:
            raise EstimateError(f"{k} is owned twice ({owner[k]}, {i['item_id']})")
        owner[k] = i["item_id"]
    if conv is not None:
        for i in items:
            bad = [a for a in i["assumptions"] if a not in conv.items and not a.startswith("FROZEN:")]
            if bad:
                raise EstimateError(f"{i['item_id']}: unknown assumptions {bad}")
    for trade in TRADES:
        parts = []
        for i in items:
            if i["trade"] != trade:
                continue
            if i["category"] == "VERIFIED":
                parts.append(QS.part(i["item_id"], "VERIFIED", i["base"]))
            elif i["category"] == "PROVISIONAL":
                parts.append(QS.part(i["item_id"], "PROVISIONAL", i["base"], i["low"], i["high"]))
            else:
                parts.append(QS.part(i["item_id"], "UNQUANTIFIED", why=i["blocker"]))
        QS.combine(parts)
    return True


def _f(x):
    return 0.0 if x is None else float(x)


def rollup(items, keys=("trade",)):
    """Totals per key tuple. Every layer is summed separately; unresolved items only counted (exposure apart)."""
    out = defaultdict(lambda: {"verified": 0.0, "prov_low": 0.0, "prov_base": 0.0, "prov_high": 0.0,
                               "n_verified": 0, "n_provisional": 0, "n_unresolved": 0, "exp_low": 0.0,
                               "exp_high": 0.0, "n_exposure": 0})
    for i in items:
        k = tuple(i[x] if i[x] is not None else "" for x in keys)
        r = out[k]
        if i["category"] == "VERIFIED":
            r["verified"] += i["base"]
            r["n_verified"] += 1
        elif i["category"] == "PROVISIONAL":
            r["prov_low"] += i["low"]
            r["prov_base"] += i["base"]
            r["prov_high"] += i["high"]
            r["n_provisional"] += 1
        else:
            r["n_unresolved"] += 1
            if i["exposure_low"] is not None:
                r["exp_low"] += i["exposure_low"]
                r["exp_high"] += i["exposure_high"]
                r["n_exposure"] += 1
    res = []
    for k in sorted(out, key=lambda t: tuple(str(x) for x in t)):
        r = out[k]
        row = dict(zip(keys, k))
        row.update({"VERIFIED": r["verified"], "PROVISIONAL_LOW": r["prov_low"], "PROVISIONAL_BASE": r["prov_base"],
                    "PROVISIONAL_HIGH": r["prov_high"], "PLANNING_LOW": r["verified"] + r["prov_low"],
                    "PLANNING_BASE": r["verified"] + r["prov_base"], "PLANNING_HIGH": r["verified"] + r["prov_high"],
                    "N_VERIFIED": r["n_verified"], "N_PROVISIONAL": r["n_provisional"],
                    "N_UNRESOLVED": r["n_unresolved"], "UNRESOLVED_EXPOSURE_LOW": r["exp_low"] if r["n_exposure"]
                    else None, "UNRESOLVED_EXPOSURE_HIGH": r["exp_high"] if r["n_exposure"] else None,
                    "N_UNRESOLVED_WITH_EXPOSURE": r["n_exposure"]})
        if not (row["PLANNING_LOW"] - EPS <= row["PLANNING_BASE"] <= row["PLANNING_HIGH"] + EPS):
            raise EstimateError(f"rollup {k} out of order")
        res.append(row)
    return res


def blockers(items):
    """What holds the unreleased quantity back: per blocker code, the provisional base (and range) and the unresolved
    count, by trade. Used to rank the causes of missing quantities."""
    out = defaultdict(lambda: {"m3_base": 0.0, "m3_high": 0.0, "kg_base": 0.0, "kg_high": 0.0, "n_provisional": 0,
                               "n_unresolved": 0, "families": set()})
    for i in items:
        if i["category"] == "VERIFIED":
            continue
        b = out[i["blocker"] or "UNSPECIFIED"]
        b["families"].add(i["family"])
        if i["category"] == "PROVISIONAL":
            b["n_provisional"] += 1
            if i["trade"] == "CONCRETE":
                b["m3_base"] += i["base"]
                b["m3_high"] += i["high"]
            else:
                b["kg_base"] += i["base"]
                b["kg_high"] += i["high"]
        else:
            b["n_unresolved"] += 1
            if i["exposure_high"] is not None:
                if i["trade"] == "CONCRETE":
                    b["m3_high"] += i["exposure_high"]
                else:
                    b["kg_high"] += i["exposure_high"]
    return [{"BLOCKER": k, "PROVISIONAL_M3_BASE": v["m3_base"], "M3_UPPER": v["m3_high"],
             "PROVISIONAL_KG_BASE": v["kg_base"], "KG_UPPER": v["kg_high"], "N_PROVISIONAL": v["n_provisional"],
             "N_UNRESOLVED": v["n_unresolved"], "FAMILIES": sorted(v["families"])}
            for k, v in sorted(out.items(), key=lambda kv: (-(kv[1]["m3_high"] + kv[1]["kg_high"] / 100.0), kv[0]))]


def steel_by_diameter(items):
    out = defaultdict(lambda: {"VERIFIED": 0.0, "PROVISIONAL_LOW": 0.0, "PROVISIONAL_BASE": 0.0,
                               "PROVISIONAL_HIGH": 0.0})
    for i in items:
        if i["trade"] != "REINFORCEMENT" or i["category"] == "UNRESOLVED":
            continue
        r = out[float(i["dia_mm"])]
        if i["category"] == "VERIFIED":
            r["VERIFIED"] += i["base"]
        else:
            r["PROVISIONAL_LOW"] += i["low"]
            r["PROVISIONAL_BASE"] += i["base"]
            r["PROVISIONAL_HIGH"] += i["high"]
    rows = []
    for d in sorted(out):
        r = out[d]
        rows.append({"DIA_MM": d, **r, "PLANNING_LOW": r["VERIFIED"] + r["PROVISIONAL_LOW"],
                     "PLANNING_BASE": r["VERIFIED"] + r["PROVISIONAL_BASE"],
                     "PLANNING_HIGH": r["VERIFIED"] + r["PROVISIONAL_HIGH"]})
    return rows


def kg_per_m(d_mm):
    """The project's unit mass method for bars (d^2 / 162, the method every Alsenan stage used)."""
    return d_mm * d_mm / 162.0


def mesh_kg(area_m2, bars_per_m, d_mm, directions=2):
    """A printed mesh rule over a known area: bars per metre each way x area x unit mass (no laps, no anchorage).
    A takeoff from a printed callout on drawn geometry, not a kg/m3 ratio."""
    if area_m2 is None or area_m2 < 0:
        raise EstimateError("a mesh needs a known area")
    return directions * bars_per_m * area_m2 * kg_per_m(d_mm)


def ring_bar_kg(radius_m, count, d_mm):
    """Closed circular bars at a known radius (no laps)."""
    return count * 2 * math.pi * radius_m * kg_per_m(d_mm)


def policy_record():
    return {"module": "engine.source.provisional_estimate", "categories": CATEGORIES, "provenance": PROVENANCE,
            "support": SUPPORT, "rule": "VERIFIED, PROVISIONAL and UNRESOLVED are summed separately; a component has "
                                        "one owner; unresolved items never enter a total; assumptions are data"}
