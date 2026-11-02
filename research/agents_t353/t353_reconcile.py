"""T-353 gap re-check (read-only research tool, no engine change): is a 'missing category' already carried by the
candidate? Rule R-T353-1 (every villa, lane I): before a family is integrated as a new method version, the merged
pieces (one record per BOQ line) are reconciled with the candidate's completeness row for that family (T-471
matrix, same item codes): equal line count, equal released total per unit, held lines blank (never 0). EQUAL means
the family is already in the candidate: no new version is built (a second one would count every piece twice);
anything else is a named difference, never netted.

    python3 -I research/agents_t353/t353_reconcile.py   (development villa: T-270 records vs the V3.0.42 matrix)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = "research/agents_t471/out/T471_MATRIX_V3_0_42.json"
TOL = 0.0000015


def record_totals(records):
    """records (one per BOQ line: item_code, unit, state RELEASED / HELD, value) -> {unit: {lines, released,
    held_lines}}; refuses a held record with a figure (0 included) and a released record without one."""
    out = {}
    for r in records:
        u = out.setdefault(r["unit"], {"lines": 0, "released": 0.0, "held_lines": 0})
        u["lines"] += 1
        if r["state"] == "HELD":
            if r.get("value") is not None:
                raise ValueError(f"{r.get('id')}: a held line carries a figure ({r.get('value')!r}); held is blank")
            u["held_lines"] += 1
        elif r["state"] == "RELEASED":
            v = r.get("value")
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                raise ValueError(f"{r.get('id')}: a released line without a positive figure")
            u["released"] = round(u["released"] + float(v), 6)
        else:
            raise ValueError(f"{r.get('id')}: state {r['state']!r}")
    return out


def matrix_row(matrix, family):
    rows = [r for r in matrix["rows"] if r.get("family") == family]
    if len(rows) != 1:
        raise ValueError(f"{family}: {len(rows)} matrix rows (one expected)")
    return rows[0]


def reconcile(records, row):
    """-> {verdict: ALREADY_CARRIED / DIFFERS / NOT_CARRIED, differences: [...]} for one family."""
    codes = {r["item_code"] for r in records}
    if not set(row.get("item_codes") or ()) & codes:
        return {"verdict": "NOT_CARRIED", "differences": ["no item code of the pieces in the candidate row"]}
    diffs = []
    if set(row["item_codes"]) != codes:
        diffs.append(f"item codes: candidate {sorted(row['item_codes'])} vs pieces {sorted(codes)}")
    mine = record_totals(records)
    q = row.get("quantities") or {}
    for unit in sorted(set(mine) | set(q)):
        a, b = mine.get(unit), q.get(unit)
        if a is None or b is None:
            diffs.append(f"{unit}: only in {'the candidate' if a is None else 'the pieces'}")
            continue
        if a["lines"] != b["lines"]:
            diffs.append(f"{unit}: {b['lines']} candidate lines vs {a['lines']} pieces")
        if abs(a["released"] - b["released"]) > TOL:
            diffs.append(f"{unit}: released {b['released']} in the candidate vs {a['released']} pieces "
                         f"({b['released'] - a['released']:+.6f})")
        if a["held_lines"] != b.get("held_unknown_lines", 0) or b.get("held_low") or b.get("held_high"):
            diffs.append(f"{unit}: held {b.get('held_unknown_lines')} blank (+ range {b.get('held_low')} .. "
                         f"{b.get('held_high')}) vs {a['held_lines']} blank pieces")
    return {"verdict": "DIFFERS" if diffs else "ALREADY_CARRIED", "differences": diffs, "pieces": mine}


def main():
    sys.path[:0] = [str(ROOT), str(ROOT / "research" / "agents_t270")]
    import t270_inputs as T  # noqa: E402
    matrix = json.loads((ROOT / MATRIX).read_text(encoding="utf-8"))
    res = reconcile(T.records(), matrix_row(matrix, "B8-08"))
    print(json.dumps(dict(res, candidate=matrix["candidate_version"], master=matrix["master_version"]), indent=1))
    return 0 if res["verdict"] == "ALREADY_CARRIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
