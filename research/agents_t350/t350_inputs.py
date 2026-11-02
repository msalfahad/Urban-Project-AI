"""T-350: the URBAN_V3043_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.43 (engine.source.arch_v3043), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every zone, bound, coefficient, held item
and bound line id is READ from those files; typed here are only the element-id prefix of the new lines, the floor
word, the template line (a footing line whose project / documents the new lines carry) and the range-fix line ids and
ranges the merged texts print (bound by the module: a stale binding stops).

  research/agents_t347/FILL_T350_T347.csv   T-347 (MERGED 509f90c2, Verifier 2026-10-30 01:05 UTC Gate A PASS on
      80b607b8: own re-measure of the 24 neat pit outlines by handle, union 129.234375 m2, D-14 1.890 m2, pool envelope
      12.216758 m2 -> in the plot 17.776576 m3, pits bound 188.017198 vs 188.017207 m3 (chord only); HELD blank on the
      committed CSV): 18 zones (B1-02 x 12, B1-03 x 5, B1-04 x 1);
  research/agents_t356/FILL_T350_T356.csv   T-356 (MERGED 15fc9ad4, Verifier 2026-10-30 01:59 UTC Gate A PASS on
      89a02f28: own SB1 strip re-measure 0.90 x 4.55; strap range LEDGER_RIGHT): the strap blinding range 0 .. 0.912684;
  research/agents_t357/EG_COEFFICIENTS_T357.csv + summary.json   T-357 (MERGED 90135e91, Verifier 2026-10-30 03:53
      UTC Gate A PASS on db32aebb): existing ground DERIVED +-0.00 (external datum at the plot edge, interior
      UNKNOWN), coefficients per metre of EG rise; clearance NOT IN DRAWN SCOPE (no line);
  research/agents_t347/FINDINGS ... F-T347-1 (T-347 verdict 'stays with T-350 as ACCEPTED'): the SB3-in-F3 line's
      held range 0.0295 .. 0.1181 -> 0.0295 .. 0.2683 m3 (T-230 / T-233 finding 4).

    python3 -I research/agents_t350/t350_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

F347 = ROOT / "research/agents_t347/FILL_T350_T347.csv"
F356 = ROOT / "research/agents_t356/FILL_T350_T356.csv"
E357 = ROOT / "research/agents_t357/EG_COEFFICIENTS_T357.csv"
S357 = ROOT / "research/agents_t357/summary.json"
PINS = {F347: "a232946c9c197c44011eb871260a414b912729386cac7a4ef00d06da5d31c783",
        F356: "8093c616678b339ba6fb182389e8e055f9ecf15b32fc032df611966f4b139428",
        E357: "72e1def6d5a07c7ec569738c9cf44471e788213d631816fdd801e42e258d1705",
        S357: "49b89c55cc1b63d515838fdd8367b78db2f1c8e81d4ed03dc1d17330460325de"}
SOURCES = {
    "T-347": {"task": "T-347", "file": "research/agents_t347/FILL_T350_T347.csv", "sha256": PINS[F347],
              "merge_commit": "509f90c2",
              "checker_run": "Verifier 2026-10-30 01:05 UTC (Gate A PASS on 80b607b8; own re-measure of the 24 neat "
                             "pits 129.234375 m2, D-14 1.890 m2, pool envelope in the plot 17.776576 m3, pits bound "
                             "188.017198 m3; HELD blank on the committed CSV)"},
    "T-356": {"task": "T-356", "file": "research/agents_t356/FILL_T350_T356.csv", "sha256": PINS[F356],
              "merge_commit": "15fc9ad4",
              "checker_run": "Verifier 2026-10-30 01:59 UTC session_01E6cPncEPDnZBN6ASzDr4w4 (Gate A PASS on "
                             "89a02f28; own SB1 strip 0.90 x 4.55 = 4.095 m2; strap range LEDGER_RIGHT, PARTIALLY "
                             "VERIFIED 1 / 3 straps)"},
    "T-357": {"task": "T-357", "file": "research/agents_t357/EG_COEFFICIENTS_T357.csv; research/agents_t357/summary.json",
              "sha256": f"{PINS[E357]}; {PINS[S357]}", "merge_commit": "90135e91",
              "checker_run": "Verifier 2026-10-30 03:53 UTC (Gate A PASS on db32aebb; LEL marks re-read, plot 470.55 "
                             "m2 DERIVED, EG +-0.00 DERIVED external datum, coefficients re-derived)"},
}
FAMILY = {"B1-02 EXCAVATION": "B1-02", "B1-03 BACKFILL": "B1-03", "B1-04 DISPOSAL": "B1-04"}
BOUND = {"AT_LEAST 1": "AT_LEAST", "HELD 1": "HELD", "ZERO_BY_BOUND 1": "ZERO_BY_BOUND"}
ELEMENT_PREFIX = "EW-T350:"
FLOOR = "FOUNDATION"
TEMPLATE_LINE = None          # set from the candidate by the run (first bound footing line); see build(template=...)
# T-357 coefficient rows by the FILL zone they belong to (excavation rows only; backfill follows its excavation)
EG_ROW = {("B1-02", "Z1-PITS-24"): "Z1 24 neat footing pits (in plot, T-347 lo 188.017207)",
          ("B1-02", "Z1-POOL"): "Z1 pool envelope in plot (T-347 lo 17.776576)",
          ("B1-03", "Z2"): "Z2 fill above EG under the GF slabs"}
# F-T347-1 (T-347 verdict: 'stays with T-350 as ACCEPTED'; T-230 / T-233 finding 4)
SB3_LINE = "L-c823e0dbd81e30c66aa5"
SB3 = {"line_id": SB3_LINE, "item_code": None, "expect": {"low": 0.0295, "high": 0.1181}, "low": 0.0295,
       "high": 0.2683, "basis": "SB3 inside F3: the T-230 / T-233 ledger range (finding 4), D-15 strap soffit",
       "why": "F-T347-1: the line kept the stale T-174 range; the merged T-230 / T-233 ledger gives 0.0295 .. 0.2683",
       "source_tasks": ["T-347"]}


def _bytes(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return b.decode("utf-8")


def _csv(p):
    return list(csv.DictReader(io.StringIO(_bytes(p))))


def _f(x):
    return None if x in (None, "") else float(x)


def zones():
    eg = {r["id"]: r for r in _csv(E357)}
    out = []
    for r in _csv(F347):
        fam = FAMILY[r["family"]]
        key = r["zone"].split(" ")[0]
        b = BOUND[r["bound_classes"]]
        if r["value_m3"] not in ("", None):
            raise SystemExit(f"{r['row_id']}: the FILL row carries a value (held rows are blank)")
        if b == "HELD" and r["status"] != "HELD":
            raise SystemExit(f"{r['row_id']}: bound class and status disagree")
        z = {"family": fam, "zone": r["zone"], "element_id": f"{ELEMENT_PREFIX}{fam}:{key}", "floor": FLOOR,
             "bound": b, "at_least": _f(r["lo_m3"]), "upper": _f(r["hi_m3"]),
             "coef_per_m": _f(r["coef_m3_per_m_d"]), "held_items": r["held_items"],
             "bound_lines": r["bound_to_lines"].split() if r["bound_to_lines"] else [],
             "known_parts": r["info"] or None, "basis": r["source"],
             "physical_element": {"B1-02": "excavation", "B1-03": "backfill", "B1-04": "disposal"}[fam]
                                 + f" zone {key}",
             "source_tasks": ["T-347"]}
        if b == "ZERO_BY_BOUND":
            z["condition"] = r["held_items"].split(";")[0].replace("condition: ", "")
        er = EG_ROW.get((fam, key))
        if er:
            e = eg[er]
            z["eg_coef_per_m"] = (f"{e['coef_m3_per_m'] or 'HELD'} m3 per m of existing-ground rise "
                                  f"({e['reference']}, T-357)")
            z["source_tasks"] = ["T-347", "T-357"]
        out.append(z)
    if len(out) != 18:
        raise SystemExit(f"FILL_T350_T347 has {len(out)} rows, not 18")
    return out


def ranges(sb3_code="STR.CONC.STRAP", sb3=True):
    rows = {r["line_id"]: r for r in _csv(F356)}
    st = rows["L-35382b18e2e362df3ae6"]
    if st["status"] != "HELD" or st["value_m3"]:
        raise SystemExit("T-356 strap row is not HELD blank")
    out = [{"line_id": st["line_id"], "item_code": "STR.CONC.BLINDING", "expect": {"low": 0.377803, "high": 0.771877},
            "low": float(st["lo_m3"]), "high": float(st["hi_m3"]),
            "basis": f"strap blinding: low {st['lo_basis']}; high {st['hi_basis']}",
            "why": "F-T347-2 / T-356 LEDGER_RIGHT: both candidate ends rested on an inadmissible basis (a plan "
                   "deduction of ground-beam blinding at another level; a strip inside the unseen F10+F outline)",
            "source_tasks": ["T-356"]}]
    if sb3:
        out.append(dict(SB3, item_code=sb3_code))
    return out


def build(project_id=None, template=None, sb3_code="STR.CONC.STRAP", sb3=True):
    s357 = json.loads(_bytes(S357))
    eg = s357["existing_ground"]
    if s357["clearance"]["status"] != "NOT_IN_DRAWN_SCOPE":
        raise SystemExit("T-357 clearance is not NOT_IN_DRAWN_SCOPE")
    from engine.source import arch_v3043 as A
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id,
            "sources": [SOURCES[k] for k in ("T-347", "T-356", "T-357")],
            "existing_ground": {"status": eg["status"], "datum": f"+-{eg['value_m']:.2f}",
                                "source": "T-357: the printed +-0.00 marks at the plot corners (external datum)",
                                "residual": "interior ground UNKNOWN (no spot level inside the plot)"},
            "template_line": template, "zones": zones(), "ranges": ranges(sb3_code, sb3)}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None, template="L-" + "0" * 20)
    print(json.dumps({"zones": len(d["zones"]), "by_bound": {b: sum(z["bound"] == b for z in d["zones"])
                                                            for b in ("AT_LEAST", "ZERO_BY_BOUND", "HELD")},
                      "at_least": {z["element_id"]: z["at_least"] for z in d["zones"] if z["at_least"]},
                      "ranges": [(r["line_id"], r["low"], r["high"]) for r in d["ranges"]]}, indent=1))
