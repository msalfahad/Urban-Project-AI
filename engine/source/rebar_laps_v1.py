"""REBAR LAPS V1 (task T-273) - lap splices of reinforcement bar groups as their own rows, from the lap authority that
governs each bar group, and the lap-aware count that replaces the frozen continuous-beam lap count as a NEW method
version (CONTINUOUS_BEAM_LAPS_V2). An unwired producer: nothing in engine/ or tools/ imports it; the frozen
continuous_beams module (and every released or candidate route) is unchanged.

Physical element. A lap splice is the overlap of two bars of one continuous bar group where the run is longer than the
stock bar: each splice adds one lap length of steel that is really installed. A starter bar, a column splice already
carried by the column ledger, an anchorage or a BBS length that already contains its laps is NOT a lap of this module
(no second lap, no lap on top of an anchorage).

Count (owner formula, OWNER_RULE_REBAR_2026-10-24 s.2; identical to bbs_optimiser.split_run):
    laps = 0 if L <= S, else ceil((L - S) / (S - lap));  added length = laps x lap;  lap >= S is BLOCKED.
D-T273-01: the frozen continuous_beams._with_laps takes n = ceil(L / S) - 1, which ignores the length each lap consumes
(23.8 m and 24 m runs get 1 lap where 2 are needed, 35 m gets 2 instead of 3). with_laps_v2 is the corrected form; the
frozen formula is reproduced here only as frozen_with_laps for the before / after comparison.

Lap authority, in this order (owner 2026-10-24 15:31 s.4 (3)):
    1 DRAWING_LAP_SCHEDULE   a printed lap schedule naming the bar group          -> its value (EXACT)
    2 APPROVED_DETAIL        an approved detail drawing the lap                    -> its value (EXACT)
    3 DRAWING_NOTE           a general note, ONLY for the bar groups it names; a note that prints 'not less than' is a
                             MINIMUM (never an exact value, never a maximum); a note that distinguishes tension and
                             compression needs the zone of the splice, else the lap is HELD with both minimums shown
    4 OWNER_CONVENTION       the owner's 40 d (columns, ordinary walls) / 60 d (beams, slabs, retaining walls, footings)
                             estimating convention: PROVISIONAL, only where the project allows it and never where a
                             drawing note or detail for the same group exists (a conflict is a finding)
    else                     HELD (never 0, never a default)
Statuses per row: the splice COUNT and the lap LENGTH carry their own status; lap kg is a number only when both are
established. kg stays the calculation unit (unit mass from rebar_unit_mass under the project's method); t = kg / 1000
is a display value written once, at 6 decimals, never summed from rounded values.
Stdlib only; project-agnostic (no project name, sheet or member id in this module).
"""

from __future__ import annotations

import hashlib
import json
import math

from engine.source import bbs_optimiser as BB
from engine.source import rebar_unit_mass as RUM

POLICY_ID = "REBAR_LAPS_V1"
METHOD_ID = "CONTINUOUS_BEAM_LAPS_V2"          # the new method version of the continuous-beam lap count (D-T273-01)
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"       # T-212: computes lap quantities, wired nowhere (guard due at integration)
T_DECIMALS = 6

# authority tiers (highest first)
SCHEDULE, DETAIL, NOTE, CONVENTION = "DRAWING_LAP_SCHEDULE", "APPROVED_DETAIL", "DRAWING_NOTE", "OWNER_CONVENTION"
TIERS = (SCHEDULE, DETAIL, NOTE, CONVENTION)
EXACT, MINIMUM = "EXACT", "MINIMUM"
TENSION, COMPRESSION = "TENSION", "COMPRESSION"

# row / component statuses (WORKFLOW_CONTROLS s.5 vocabulary + the lap-specific states)
DRAWING_CONFIRMED, PROVISIONAL, HELD, NOT_REQUIRED, BLOCKED = (
    "DRAWING-CONFIRMED", "PROVISIONAL", "HELD", "NOT_REQUIRED", "BLOCKED")

# owner's estimating convention (OWNER_RULE_REBAR_2026-10-24 s.2): factor x d by element class; PROVISIONAL only
OWNER_CONVENTION_ID = "OWNER-LAP-CONVENTION-2026-10-24 (proposal, PROVISIONAL)"
OWNER_CONVENTION_D = {"COLUMN": 40, "WALL": 40, "BEAM": 60, "GROUND_BEAM": 60, "SLAB": 60, "RETAINING_WALL": 60,
                      "FOOTING": 60}

# element kinds whose splices another ledger already carries (columns: LAP / STARTER components)
ALREADY_CARRIED = ("LAP", "STARTER", "ANCHORAGE")


class LapError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ the count
def lap_count(run_m, lap_m, stock_m):
    """number of lap splices of one continuous run (owner formula). None when the run is unknown. Raises when the lap
    is not shorter than the stock (no bar can be spliced)."""
    if run_m is None:
        return None
    if stock_m is None or stock_m <= 0:
        raise LapError("stock length not given")
    if run_m <= stock_m + 1e-9:
        return 0
    if lap_m is None:
        raise LapError("a run longer than the stock needs a lap length to count its splices")
    if lap_m >= stock_m:
        raise LapError(f"lap {lap_m} m not shorter than the stock {stock_m} m: BLOCKED")
    n = math.ceil((run_m - stock_m) / (stock_m - lap_m) - 1e-12)
    assert len(BB.split_run(run_m, lap_m, stock_m)) - 1 == n      # one formula in the engine (split_run)
    return n


def count_invariance(run_m, stock_m):
    """the splice count a run needs for EVERY lap length from 0 up to lap_max_m (the count changes above it):
    -> {"count", "lap_max_m"}. For a run within the stock: count 0 for any lap (lap_max_m None = unbounded)."""
    if run_m <= stock_m + 1e-9:
        return {"count": 0, "lap_max_m": None}
    n0 = math.ceil((run_m - stock_m) / stock_m - 1e-12)
    return {"count": n0, "lap_max_m": round(stock_m - (run_m - stock_m) / n0, 9)}


def frozen_with_laps(L, d_mm, lap_d, stock_m):
    """the FROZEN continuous_beams._with_laps (D-T273-01), reproduced for the before / after comparison only."""
    if L <= stock_m:
        return L
    n = math.ceil(L / stock_m) - 1
    return L + n * lap_d * d_mm / 1000.0


def with_laps_v2(L, d_mm, lap_d, stock_m):
    """CONTINUOUS_BEAM_LAPS_V2: the bar length of one continuous run including its laps (owner formula)."""
    lap = lap_d * d_mm / 1000.0
    return L + lap_count(L, lap, stock_m) * lap


def compare_with_frozen(L, d_mm, lap_d, stock_m):
    old, new = frozen_with_laps(L, d_mm, lap_d, stock_m), with_laps_v2(L, d_mm, lap_d, stock_m)
    lap = lap_d * d_mm / 1000.0
    n_old = 0 if L <= stock_m else math.ceil(L / stock_m) - 1
    return {"run_m": L, "d_mm": d_mm, "lap_d": lap_d, "stock_m": stock_m, "lap_m": round(lap, 9),
            "laps_frozen": n_old, "laps_v2": lap_count(L, lap, stock_m), "length_frozen_m": round(old, 9),
            "length_v2_m": round(new, 9), "difference_m": round(new - old, 9)}


# ------------------------------------------------------------------------------------------------ the authority
def resolve_lap(group, authorities, *, convention_allowed=False):
    """the lap of one bar group. group: {"element_kind", "dia_mm", "zone" (TENSION / COMPRESSION / None)}.
    authorities: [{"tier", "lap_d" | "lap_m" | {"tension_d", "compression_d"}, "kind" (EXACT / MINIMUM), "governs"
    (True when the source names this bar group), "ref"}]. -> {"state", "lap_m", "lap_min_m", "basis", "ref",
    "findings"}: state DRAWING-CONFIRMED (an exact printed lap), PROVISIONAL (owner convention), HELD (minimum only,
    zone not printed, or no authority)."""
    d = None if group.get("dia_mm") is None else group["dia_mm"] / 1000.0
    findings = []
    governing = [a for a in authorities if a.get("governs")]
    for a in authorities:
        if a.get("tier") not in TIERS:
            raise LapError(f"unknown lap authority tier {a.get('tier')!r}")
        if not a.get("governs") and a["tier"] != CONVENTION:
            findings.append(f"{a['tier']} {a.get('ref')}: does not name this bar group, not applied")
    printed = [a for a in governing if a["tier"] != CONVENTION]
    for tier in (SCHEDULE, DETAIL, NOTE):
        hits = [a for a in printed if a["tier"] == tier]
        if not hits:
            continue
        a = hits[0]
        if len({json.dumps({k: a.get(k) for k in ("lap_d", "lap_m", "tension_d", "compression_d")}, sort_keys=True)
                for a in hits}) > 1:
            return {"state": HELD, "lap_m": None, "lap_min_m": None, "basis": f"{tier}: two sources disagree",
                    "ref": "; ".join(str(h.get("ref")) for h in hits),
                    "findings": findings + [f"CONFLICT between {tier} sources"]}
        if "tension_d" in a or "compression_d" in a:          # a note distinguishing the zones
            zone = group.get("zone")
            key = {TENSION: "tension_d", COMPRESSION: "compression_d"}.get(zone)
            if key is None:
                mins = sorted(x for x in (a.get("tension_d"), a.get("compression_d")) if x)
                return {"state": HELD, "lap_m": None, "lap_min_m": None if d is None else round(mins[0] * d, 9),
                        "basis": f"{tier}: tension {a.get('tension_d')} d / compression {a.get('compression_d')} d, "
                                 f"zone of the splice not printed", "ref": a.get("ref"),
                        "findings": findings + ["TENSION_COMPRESSION_ZONE_NOT_PRINTED"]}
            lap_d = a[key]
        else:
            lap_d = a.get("lap_d")
        if a.get("lap_m") is None and d is None:
            return {"state": HELD, "lap_m": None, "lap_min_m": None, "ref": a.get("ref"),
                    "basis": f"{tier}: {lap_d} x d, but the bar diameter is not established",
                    "findings": findings + ["DIAMETER_NOT_ESTABLISHED"]}
        lap_m = a["lap_m"] if a.get("lap_m") is not None else lap_d * d
        if a.get("kind") == MINIMUM:
            return {"state": HELD, "lap_m": None, "lap_min_m": round(lap_m, 9),
                    "basis": f"{tier}: 'not less than' {lap_d} d is a minimum, not a lap length", "ref": a.get("ref"),
                    "findings": findings + ["MINIMUM_ONLY"]}
        conv = [c for c in authorities if c["tier"] == CONVENTION]
        if conv:
            findings.append(f"owner convention not applied: {tier} {a.get('ref')} governs this group")
        return {"state": DRAWING_CONFIRMED, "lap_m": round(lap_m, 9), "lap_min_m": None,
                "basis": f"{tier}: {lap_d} x d" if a.get("lap_m") is None else f"{tier}: {lap_m} m",
                "ref": a.get("ref"), "findings": findings}
    if convention_allowed:
        f = OWNER_CONVENTION_D.get(group.get("element_kind"))
        if f is None or d is None:
            return {"state": HELD, "lap_m": None, "lap_min_m": None, "ref": OWNER_CONVENTION_ID,
                    "basis": f"owner convention has no class for {group.get('element_kind')!r}", "findings": findings}
        return {"state": PROVISIONAL, "lap_m": round(f * d, 9), "lap_min_m": None,
                "basis": f"{OWNER_CONVENTION_ID}: {f} x d", "ref": OWNER_CONVENTION_ID, "findings": findings}
    return {"state": HELD, "lap_m": None, "lap_min_m": None, "ref": None,
            "basis": "no lap schedule, detail or note names this bar group; the owner convention is not allowed "
                     "for it", "findings": findings}


# ------------------------------------------------------------------------------------------------ the row
def lap_row(group, *, stock_m, stock_ref, lap, unit_mass_cfg):
    """one lap row of a bar group. group: {"element", "floor", "element_kind", "bar_type", "dia_mm", "bars", "run_m",
    "run_status", "continuity" (CONTINUOUS / NOT_ESTABLISHED), "already_carried" (a component kind that already holds
    its splices, or None), "length_includes_laps" (bool), "continues_above" (bool, columns / walls), "ref"}.
    lap: a resolve_lap() result. -> the row (kg full precision; t display values at 6 decimals)."""
    if group.get("already_carried") in ALREADY_CARRIED:
        raise LapError(f"{group['element']}: its splices are already carried as {group['already_carried']} "
                       f"components; a second lap is refused")
    if group.get("length_includes_laps"):
        raise LapError(f"{group['element']}: the bar length already includes its laps (BBS); a lap on top is refused")
    kgm = None if group.get("dia_mm") is None else RUM.kg_per_m(group["dia_mm"], unit_mass_cfg)
    bars, run = group.get("bars"), group.get("run_m")
    net_kg = None if bars is None or run is None or kgm is None else bars * run * kgm
    row = {"element": group["element"], "floor": group.get("floor"), "type": group.get("bar_type"),
           "dia_mm": group.get("dia_mm"), "bars": bars, "net_length_m": run, "lap_per_splice_m": lap.get("lap_m"),
           "lap_min_m": lap.get("lap_min_m"), "splices_per_bar": None, "splices": None, "added_length_m": None,
           "net_kg": net_kg, "lap_kg": None, "installed_kg": None, "count_status": None, "lap_status": lap["state"],
           "status": None, "count_valid_up_to_lap_m": None, "lap_basis": lap["basis"], "lap_ref": lap.get("ref"),
           "stock_m": stock_m, "stock_ref": stock_ref, "drawing_ref": group.get("ref"),
           "findings": list(lap.get("findings") or []), "unit_mass": RUM.describe(unit_mass_cfg)}
    if group.get("continues_above") is False:
        row.update(splices_per_bar=0, splices=0, added_length_m=0.0, lap_kg=0.0, count_status=NOT_REQUIRED,
                   status=NOT_REQUIRED)
        row["findings"].append("no bar continues beyond this element (top storey / free end): no splice")
        return _with_t(row)
    if run is None or bars is None or kgm is None:
        row.update(count_status=HELD, status=HELD)
        row["findings"].append("bar group or run not quantified: the lap waits on it")
        return _with_t(row)
    if group.get("continuity") != "CONTINUOUS":
        row.update(count_status=HELD, status=HELD)
        row["findings"].append("continuity of the bars over this run is not established by the drawing")
        return _with_t(row)
    inv = count_invariance(run, stock_m)
    row["count_valid_up_to_lap_m"] = inv["lap_max_m"]
    if inv["count"] == 0:
        row.update(splices_per_bar=0, splices=0, added_length_m=0.0, lap_kg=0.0, count_status=NOT_REQUIRED,
                   status=NOT_REQUIRED, lap_status=NOT_REQUIRED)
        row["findings"].append(f"run {run} m within the stock {stock_m} m: no splice for any lap length")
        return _with_t(row)
    lap_m = lap.get("lap_m")
    if lap_m is not None:
        n = lap_count(run, lap_m, stock_m)
        row["count_status"] = lap["state"]
    else:
        lmin = lap.get("lap_min_m") or 0.0
        if inv["lap_max_m"] is not None and lmin > inv["lap_max_m"]:
            n, row["count_status"] = None, HELD
        else:
            # the count is the same for every lap length 0 .. lap_max_m; above it the count is not established
            n, row["count_status"] = inv["count"], HELD
            row["findings"].append(f"splices {inv['count']} per bar for any lap length up to {inv['lap_max_m']} m; "
                                   f"lap length not established, count HELD with it")
    row["splices_per_bar"] = n
    row["splices"] = None if n is None else n * bars
    if lap_m is not None and n is not None:
        row["added_length_m"] = n * bars * lap_m
        row["lap_kg"] = row["added_length_m"] * kgm
        row["installed_kg"] = (net_kg + row["lap_kg"]) if group.get("run_status") == DRAWING_CONFIRMED else None
        row["status"] = lap["state"]
    else:
        row["status"] = HELD
    return _with_t(row)


def _t(kg):
    return None if kg is None else round(kg / 1000.0, T_DECIMALS)


def _with_t(row):
    """t display values: once, from the unrounded kg (never summed back)."""
    if row["installed_kg"] is None and row["status"] == NOT_REQUIRED and row["net_kg"] is not None:
        row["installed_kg"] = row["net_kg"]
    for k in ("net", "lap", "installed"):
        row[f"{k}_t"] = _t(row[f"{k}_kg"])
    return row


def totals(rows):
    """subtotals per status in kg (unrounded sums) and t (converted once from those sums); held rows are counted by
    name, never as 0."""
    out = {}
    for r in rows:
        s = out.setdefault(r["status"], {"rows": 0, "net_kg": 0.0, "lap_kg": 0.0, "lap_rows_without_kg": []})
        s["rows"] += 1
        s["net_kg"] += r["net_kg"] or 0.0
        if r["lap_kg"] is None:
            s["lap_rows_without_kg"].append(r["element"])
        else:
            s["lap_kg"] += r["lap_kg"]
    for s in out.values():
        s["net_t"], s["lap_t"] = _t(s["net_kg"]), _t(s["lap_kg"])
    return out


def policy_record():
    rec = {"policy_id": POLICY_ID, "method_id": METHOD_ID, "tiers": list(TIERS),
           "owner_convention": {"id": OWNER_CONVENTION_ID, "factors_d": OWNER_CONVENTION_D, "status": PROVISIONAL},
           "count": "laps = 0 if L <= S else ceil((L - S) / (S - lap)); lap >= S BLOCKED (bbs_optimiser.split_run)",
           "defect": "D-T273-01: continuous_beams._with_laps n = ceil(L / S) - 1 (frozen; corrected here as a new "
                     "method version, never in place)",
           "never": ["a default lap length", "a 'not less than' value used as the lap", "a second column lap or "
                     "starter", "a lap on an anchorage or a BBS length that contains it", "laps summed from rounded t",
                     "a held lap shown as 0"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
