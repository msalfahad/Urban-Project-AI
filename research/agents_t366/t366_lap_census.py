"""T-366 lap-length authority census (LAP_AUTHORITY_CENSUS_V1; research module, stdlib only, unwired).

For every bar population a released rebar route counts: which drawing note or detail prints a lap length for THAT
group, with its sheet / handle / position, value (in d or mm), kind (exact or 'not less than' minimum) and zone; or that
none does. No kg, no lap applied, no candidate line changed (owner 2026-10-25 10:33; OWNER_RULE_REBAR_2026-10-24).

Rules (ERS s.2.1 notation before arithmetic; owner 2026-10-24 s.4 (3) and s.6 (1)):
- A note or detail is an authority only for the bar groups its own wording or drawing names (`names`). A note naming
  another group (a 40 d note for temperature bars offered to beam bars) is refused.
- Detailing categories stay apart: LAP_SPLICE, STARTER_BARS, ANCHORAGE_DEVELOPMENT, HOOK_BEND, MECHANICAL_COUPLER.
- A note that splits tension / compression needs the splice zone printed for that population (handle); a zone without
  its own print is a guessed zone and is refused. Unprinted zone -> lap HELD (both minimums listed, never a range).
- 'not less than' is a MINIMUM, never the lap and never a maximum.
- A population record carries no kg and never a lap inside its net (`net_includes_lap` refused).
- Stock length: PRINTED (handle) or an owner-approved fallback with its source (WORKFLOW_CONTROLS s.4:
  ASSUMED - OWNER-APPROVED), else HELD; never a default.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from decimal import Decimal

CATEGORIES = ("LAP_SPLICE", "STARTER_BARS", "ANCHORAGE_DEVELOPMENT", "HOOK_BEND", "MECHANICAL_COUPLER")
AUTHORITY = ("PRINTED_DETAIL", "GENERAL_NOTE", "NOT_PRINTED")
VALUE_KIND = ("EXACT", "MINIMUM")
SPLICE_NEED = ("REQUIRED", "NOT_REQUIRED", "DRAWN_OVERLAP", "NOT_ESTABLISHED")
STOCK_STATUS = ("PRINTED", "ASSUMED - OWNER-APPROVED", "HELD")
FORBIDDEN_KEYS = ("kg", "t", "mass_kg", "lap_kg", "quantity", "quantity_kg", "lap_m_applied")


class CensusError(ValueError):
    pass


def _source(s, sid):
    if not isinstance(s, dict):
        raise CensusError(f"source {sid}: not a record")
    for k in ("sheet", "category", "names", "value_d", "value_kind", "zones"):
        if k not in s:
            raise CensusError(f"source {sid}: missing {k}")
    if s["category"] not in CATEGORIES:
        raise CensusError(f"source {sid}: unknown category {s['category']!r} (never guessed)")
    if not (s.get("handle") or s.get("position")):
        raise CensusError(f"source {sid}: no handle and no position: a source must be citable")
    if s["value_kind"] not in VALUE_KIND:
        raise CensusError(f"source {sid}: value_kind {s['value_kind']!r}")
    if not s["names"]:
        raise CensusError(f"source {sid}: names no bar group")
    return s


def classify(pop, sources):
    """-> dict row for one population: authority, value, zone, lap status. Raises CensusError on a refused reading."""
    pid = pop.get("id")
    for k in FORBIDDEN_KEYS:
        if k in pop:
            raise CensusError(f"{pid}: carries '{k}': the census computes no kg and applies no lap")
    if pop.get("net_includes_lap"):
        raise CensusError(f"{pid}: a lap counted inside the net kg is refused (laps are BBS / procurement rows)")
    if pop.get("splice_need") not in SPLICE_NEED:
        raise CensusError(f"{pid}: splice_need {pop.get('splice_need')!r}")
    if pop["splice_need"] in ("REQUIRED", "NOT_REQUIRED") and not pop.get("need_basis"):
        raise CensusError(f"{pid}: splice need stated without a basis (merged ledger / run length)")
    cited = pop.get("authorities", [])
    rows = []
    for a in cited:
        sid = a["source"]
        if sid not in sources:
            raise CensusError(f"{pid}: unknown source {sid}")
        s = _source(sources[sid], sid)
        if pop["group"] not in s["names"]:
            raise CensusError(f"{pid}: source {sid} names {s['names']} only, not group {pop['group']!r} "
                              "(a note is applied only to the groups it names)")
        if a.get("as_category", s["category"]) != s["category"]:
            raise CensusError(f"{pid}: source {sid} is {s['category']}, offered as {a['as_category']} (category mismatch)")
        zone = a.get("zone")
        if zone is not None:
            if zone not in s["zones"]:
                raise CensusError(f"{pid}: zone {zone!r} not among {sid}'s zones {list(s['zones'])}")
            if not a.get("zone_source"):
                raise CensusError(f"{pid}: zone {zone!r} for {sid} has no printed source: a guessed zone is refused")
        rows.append((sid, s, zone))
    if not rows:
        authority, value, status = "NOT_PRINTED", None, None
    else:
        sid, s, zone = rows[0]
        authority = "PRINTED_DETAIL" if s.get("kind") == "DETAIL" else "GENERAL_NOTE"
        zones = s["zones"]
        if len(zones) > 1 and zone is None:
            value = {z: zones[z] for z in zones}
            status = "HELD_ZONE_NOT_PRINTED"
        else:
            z = zone if zone is not None else next(iter(zones))
            value = {z: zones[z]}
            status = ("PRINTED_TYPICAL" if s.get("typical") else "PRINTED") + ("_MINIMUM" if s["value_kind"] == "MINIMUM" else "")
        if len(rows) > 1:
            # two authorities name the group: they agree only if every one gives the same single value
            vals = set()
            for _sid, s2, z2 in rows:
                zs = s2["zones"]
                vals |= {zs[z2]} if z2 is not None else set(zs.values())
            if len(vals) > 1:
                status = "CONFLICT_" + ("ZONE_NOT_PRINTED" if any(len(r[1]["zones"]) > 1 and r[2] is None for r in rows)
                                        else "VALUES") + " (" + " vs ".join(
                    f"{r[0]} {json.dumps(r[1]['zones'], sort_keys=True)} {r[1]['value_kind']}" for r in rows) + ")"
                value = {r[0]: r[1]["zones"] for r in rows}
    need = pop["splice_need"]
    if authority == "NOT_PRINTED":
        lap_status = "NOT_REQUIRED" if need == "NOT_REQUIRED" else "HELD_NO_AUTHORITY"
    elif need == "NOT_REQUIRED":
        lap_status = "NOT_REQUIRED (authority exists: " + status + ")"
    else:
        lap_status = status
    return {
        "id": pid, "trade_family": pop["family"], "group": pop["group"], "description": pop["description"],
        "bar_marks": pop.get("bar_marks", ""), "candidate_lines": pop.get("candidate_lines", ""),
        "authority": authority, "sources": ";".join(r[0] for r in rows),
        "where": ";".join(f"{r[1]['sheet']} {r[1].get('handle') or r[1].get('position')}" for r in rows),
        "category": ";".join(r[1]["category"] for r in rows),
        "value_d": json.dumps(value, sort_keys=True) if value else "",
        "value_kind": ";".join(r[1]["value_kind"] for r in rows),
        "zone_printed": "yes" if any(r[2] for r in rows) else ("n/a" if not rows or all(len(r[1]["zones"]) == 1 for r in rows) else "no"),
        "splice_need": need, "need_basis": pop.get("need_basis", ""),
        "lap_status": lap_status, "notes_checked_not_naming": ";".join(pop.get("checked_not_naming", [])),
        "finding": pop.get("finding", ""),
    }


def census(data):
    sources, pops = data["sources"], data["populations"]
    req = data["required_populations"]
    ids = [p["id"] for p in pops]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise CensusError(f"population listed twice: {dup}")
    missing = sorted(set(req) - set(ids))
    if missing:
        raise CensusError(f"released-route population missing from the census: {missing}")
    extra = sorted(set(ids) - set(req))
    if extra:
        raise CensusError(f"population not in the released-route list: {extra}")
    for sid, s in sources.items():
        _source(s, sid)
    rows = [classify(p, sources) for p in pops]
    stock = stock_status(data["stock"])
    return rows, stock


def stock_status(st):
    if st.get("printed_handle"):
        return {"status": "PRINTED", "value_m": st["value_m"], "source": st["printed_handle"]}
    if st.get("owner_source") and st.get("value_m"):
        return {"status": "ASSUMED - OWNER-APPROVED", "value_m": st["value_m"], "source": st["owner_source"],
                "searched": st.get("searched", "")}
    return {"status": "HELD", "value_m": None, "source": None, "searched": st.get("searched", "")}


# ---------------------------------------------------------------- splice count: owner formula vs frozen form
def _exact(x):
    if isinstance(x, bool) or x is None:
        raise CensusError("not a length")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, (int, Decimal)):
        return Fraction(x)
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            raise CensusError("not a finite length")
        return Fraction(Decimal(repr(x)))
    if isinstance(x, str):
        return Fraction(Decimal(x.strip()))
    raise CensusError(f"not a length: {x!r}")


def owner_laps(L, S, lap):
    """OWNER_RULE_REBAR_2026-10-24 s.2: 0 if L <= S else ceil((L - S) / (S - lap)); exact rationals."""
    L, S, lap = _exact(L), _exact(S), _exact(lap)
    if L <= 0 or S <= 0 or lap < 0:
        raise CensusError("lengths must be positive")
    if L <= S:
        return 0
    if lap >= S:
        raise CensusError("lap not shorter than the stock")
    q = (L - S) / (S - lap)
    return -((-q.numerator) // q.denominator)


def frozen_form_laps(L, S):
    """the count the frozen route G continuous_beams._with_laps uses: ceil(L / S) - 1 (independent of the lap)."""
    L, S = _exact(L), _exact(S)
    if L <= S:
        return 0
    q = L / S
    return -((-q.numerator) // q.denominator) - 1


def frozen_safe_lap_max(L, S):
    """largest lap for which the frozen count still equals the owner count (None: L <= S)."""
    L, S = _exact(L), _exact(S)
    if L <= S:
        return None
    n0 = frozen_form_laps(L, S)
    return S - (L - S) / n0


def worked_run(L, S, lap_d, d_mm):
    lap = _exact(lap_d) * _exact(d_mm) / 1000
    n_o, n_f = owner_laps(L, S, lap), frozen_form_laps(L, S)
    total_o = _exact(L) + n_o * lap
    total_f = _exact(L) + n_f * lap
    safe = frozen_safe_lap_max(L, S)
    return {"L_m": str(L), "S_m": str(S), "lap": f"{lap_d} d x {d_mm} mm = {float(lap):.3f} m",
            "owner_laps": n_o, "frozen_laps": n_f, "differs": n_o != n_f,
            "bar_length_owner_m": round(float(total_o), 6), "bar_length_frozen_m": round(float(total_f), 6),
            "short_by_m": round(float(total_o - total_f), 6),
            "frozen_right_up_to_lap_m": round(float(safe), 6) if safe is not None else None,
            "check_pieces": f"{n_o + 1} stock pieces cover {float((n_o + 1) * _exact(S) - n_o * lap):.3f} m >= L; "
                            f"{n_f + 1} pieces cover {float((n_f + 1) * _exact(S) - n_f * lap):.3f} m"}


CSV_COLS = ("id", "trade_family", "group", "description", "bar_marks", "authority", "sources", "where", "category",
            "value_d", "value_kind", "zone_printed", "splice_need", "need_basis", "lap_status", "candidate_lines",
            "notes_checked_not_naming", "finding")


def main(argv):
    import csv
    src = argv[1]
    data = json.load(open(src, encoding="utf-8"))
    rows, stock = census(data)
    runs = [worked_run(**w) for w in data["worked_runs"]]
    out_csv = argv[argv.index("--csv") + 1] if "--csv" in argv else None
    out_json = argv[argv.index("--json") + 1] if "--json" in argv else None
    if out_csv:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS, lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k: r[k] for k in CSV_COLS})
    counts = {}
    for r in rows:
        counts.setdefault(r["authority"], 0)
        counts[r["authority"]] += 1
    lap_counts = {}
    for r in rows:
        k = r["lap_status"].split(" (")[0]
        lap_counts[k] = lap_counts.get(k, 0) + 1
    summary = {"schema": "LAP_AUTHORITY_CENSUS_V1", "populations": len(rows), "authority_counts": counts,
               "lap_status_counts": lap_counts, "stock": stock, "worked_runs": runs,
               "kg_computed": 0, "candidate_lines_changed": 0}
    if out_json:
        json.dump(summary, open(out_json, "w", encoding="utf-8"), indent=1, sort_keys=True, ensure_ascii=False)
        open(out_json, "a", encoding="utf-8").write("\n")
    print(json.dumps({"populations": len(rows), "authority": counts, "lap_status": lap_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
