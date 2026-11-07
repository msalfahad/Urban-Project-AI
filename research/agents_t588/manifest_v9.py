"""T-588 WIRING MANIFEST V9 + OVERLAY DRY RUN (R-T588-1; lane I, non-candidate, research only).

V9 carries the merged pieces T-578 (rails / guards, nosing reconciliation), T-583 (dome / ring / lift-wall bar
components) and T-584 (E1 entrance step lm, stair steps count x length) into wiring rows on the candidate of record
ARCH_TAKEOFF_V3.0.58, and overlays them on a COPY of its line index AFTER the pending V2 .. V8 packages (the T-580
overlay order, R-T580-1 code reused read only). Nothing is wired; no candidate, released (V2.9 + route G), rule,
knowledge or registry file is written. No drawing is read: every figure comes from a committed, Checker-merged output.

R-T588-1 (every villa on the engine's line-index scheme):
  (a) one row = one line id, one unit, one op; a row states before (from the pinned index at its overlay step), after,
      a quantity class from one fixed map (RELEASED / AT_LEAST / HELD_RANGE / HELD / EXCLUDED) and the evidence status
      of WORKFLOW_CONTROLS s.5 with the verdict line it is read from (never from a handoff);
  (b) a HELD row never carries a value; a bound that collapses to 0 .. 0 is refused; an open high stays open;
  (c) two rows (or two packages) on one line id are refused; a later manifest replaces an earlier package only BY NAME
      (V9 REBAR_COMPONENTS supersedes V8 REBAR_OMISSION on the same 6 line ids);
  (d) DRAWN EDGE CENSUS (ELEMENT_REGISTER 'NOSING EDGE', T-412 s.7, UP-STAIR-008): every drawn nosing edge is priced
      by exactly ONE line: a tread / winder edge (in step basis) by the step-lm line (B7-06) of its flight, a landing /
      floor edge by the nosing line (B7-05); a second reading of a flight never claims an edge; railing lines never
      claim a nosing edge. Doubles and orphans are printed before and after the overlay; after must be 0 / 0
      (B7-05 edges count as T-424's, which adds them; V9 adds no nosing line).
Rebuild: `python3 -I research/agents_t588/manifest_v9.py` (`--check`).
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T580_DIR = ROOT / "research/agents_t580"
if str(T580_DIR) not in sys.path:
    sys.path.insert(0, str(T580_DIR))

import overlay as OV                                                  # noqa: E402  (R-T580-1, read only)


def _load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


T580 = _load(T580_DIR / "t580_alsenan.py", "t580_alsenan_t588")       # read only: packages V2 .. V8 in Gate B order

SCHEMA = "URBAN_T588_WIRING_MANIFEST_V9"
RULE = "R-T588-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V9.json"
IN = {
    "T578": ROOT / "research/agents_t578/out/T578_RAIL_NOSING_RECONCILE.json",
    "T583": ROOT / "research/agents_t583/out/T583_DOME_LIFT_COMPONENTS.json",
    "T584": ROOT / "research/agents_t584/out/T584_STEPS.json",
    "T412": ROOT / "research/agents_t412/NOSING_TABLE_T412.csv",
    "V8": ROOT / "research/agents_t569/WIRING_MANIFEST_V8.json",
    "OVERLAY": T580_DIR / "overlay.py",
    "T580": T580_DIR / "t580_alsenan.py",
    "T580_OUT": T580_DIR / "out/OVERLAY_T580.json",
}
CLASSES = ("RELEASED", "AT_LEAST", "HELD_RANGE", "HELD", "EXCLUDED")
EVIDENCE = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "HELD", "UNKNOWN", "WORKER-PROPOSED")

# verdict lines (board text, Verifier) the evidence is read from
VERDICT = {
    "T-583": "BOARD T-583 VERIFIER 2026-11-07T04:05Z (e): shell / ring / lift-wall lows re-derived AGREE; lift-wall "
             "A and B lows VERIFIED, highs bounded, h HELD: PARTIALLY VERIFIED; F-C-T583-1 east-ring low strict, "
             "tighter reading +0.021771 t open",
    "T-584:E1": "BOARD T-584 VERIFIER 2026-11-07T04:05Z (e): E1 4 x 2.80 = 11.20 lm, nr 4, ENGINE_OMISSION CONFIRMED, "
                "VERIFIED; 30A landing nosing RULE_DIFFERENCE AGREED",
    "T-584:FLIGHTS": "BOARD T-584 VERIFIER 2026-11-07T04:05Z (e): ST-01 45 x 1.150 = 51.75, ST-02 14 x 1.150 = 16.10, "
                     "causes re-summed; flight tread counts not re-measured (T-412 census): PARTIALLY VERIFIED",
    "T-578": "RUN_LOG Verifier 2026-11-07T02:08Z: T-578 RL-07 15.953174 lm rise basis AGREE, his side not re-read, "
             "PARTIALLY VERIFIED (board T-578 MERGED f4409c96); T-587 verdict 05:54Z (f): RL-07 V, guards PV, RL-08 WP "
             "(WP = the cause attribution under decomposition A, not the line's length)",
    "RAILS_LINES": "BOARD_ARCHIVE T-164 Checker verdict (f STATUS): RL-02 4.921 + RL-03 7.967 = 12.888 lm VERIFIED; RL-01 "
                   "6.262, RL-05 16.324, RL-06 2.400, RL-08 1.042 DRAWING-CONFIRMED (not re-measured)",
}


# cross-trade rulings added by V9 (a conflict on one host is EXPLAINED only by a named ruling, R-T580-1)
RULINGS_V9 = [
    {"layer": "FIN.STAIR", "host_re": r":flight \d+$", "sources": ["CANDIDATE", "STAIR_STEPS (T-584 FR-T584-1 / FR-T584-3)"],
     "ruling": "FIN.STAIR.FLIGHT (B7-01: sloping pitch length nosing to nosing, engine/source/arch_measure.py:930) and "
               "FIN.STAIR.STEP_LM (B7-06: commercial step per tread, UP-STAIR-008) are two elements of one flight "
               "(engine/source/coverage_census.py B7-01 vs B7-06); the same pair stands on every candidate flight; "
               "V9 writes only the step line",
     "fix_row": "none: two elements by the coverage census, no quantity shared"},
]


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _d(x):
    return None if x is None else Decimal(str(x))


# ---- R-T588-1 (a)/(b): state, class, row ---------------------------------------------------------------------------

def held(lo=None, hi=None):
    return {"class": "HELD", "measured_net": None, "held_low": lo, "held_high": hi}


def released(v):
    return {"class": "RELEASED", "measured_net": v, "held_low": None, "held_high": None}


def excluded():
    return {"class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None}


def class_of(st):
    """the one fixed map from an index state to the manifest quantity class."""
    c = st["class"]
    if c in ("RELEASED", "EXCLUDED"):
        return c
    if c != "HELD":
        raise ManifestError(f"unknown index class {c}")
    lo, hi = _d(st.get("held_low")), _d(st.get("held_high"))
    if lo is None and hi is None:
        return "HELD"
    if hi is None:
        return "AT_LEAST"
    return "HELD_RANGE"


def row(pkg, fix_row, kind, line_id, before, after, evidence, verdict, code=None, unit=None, elem=None, beside=None,
        note=None):
    if evidence not in EVIDENCE:
        raise ManifestError(f"{line_id}: evidence status {evidence!r} is not a WORKFLOW_CONTROLS s.5 status")
    st = after if after is not None else before
    if st is not None and st["class"] == "HELD" and _d(st.get("measured_net")) is not None:
        raise ManifestError(f"R2 HELD_AS_VALUE: {line_id} HELD row with a value {st['measured_net']}")
    if evidence == "VERIFIED" and st is not None and st["class"] == "HELD":
        raise ManifestError(f"{line_id}: a HELD quantity labelled VERIFIED")
    r = {"op_id": f"{pkg}|{fix_row}|{line_id}", "package": pkg, "row": fix_row, "kind": kind, "line_id": line_id,
         "before": before, "after": after, "source": pkg,
         "class_before": class_of(before) if before else None,
         "class_after": class_of(after) if after else (class_of(before) if before else None),
         "evidence": {"status": evidence, "verdict_line": verdict}}
    if code:
        r.update(item_code=code, unit=unit, element_id=elem)
    if beside is not None:
        r["beside"] = beside
    if note:
        r["note"] = note
    return r


def validate_rows(rows):
    """R-T588-1 (b)/(c) on the rows alone (before any index): delegated to the R-T580-1 checks."""
    OV.validate(rows)
    return True


# ---- V9 packages ------------------------------------------------------------------------------------------------

def kg(t):
    return None if t is None else float((Decimal(str(t)) * 1000).normalize())


def pkg_rebar(t583, v8):
    """T-583 restates the 6 V8 REBAR_OMISSION lines: same line ids, after = the T-583 strict low, high open by name."""
    P = "REBAR_COMPONENTS (T-583; supersedes V8 REBAR_OMISSION by name)"
    by_el = {r["row_id"]: r for r in t583["rows"]}
    v8rows = v8["rebar_omission"]["rows"]
    if sorted(by_el) != sorted(r["expected_after"]["element_id"] for r in v8rows):
        raise ManifestError("T-583 rows and V8 REBAR_OMISSION rows are not the same 6 elements")
    rows = []
    for r8 in v8rows:
        a8 = r8["expected_after"]
        t = by_el[a8["element_id"]]
        if t["unit"] != "t" or a8["unit"] != "kg":
            raise ManifestError(f"{a8['element_id']}: unit pair {t['unit']} / {a8['unit']} (t -> kg expected)")
        if t["concrete_line"] != r8["concrete_line"]:
            raise ManifestError(f"{a8['element_id']}: concrete line differs")
        beside = {"concrete_line": r8["concrete_line"]}
        if t["status"] == "HELD_BLANK":
            after, ev = held(), "HELD"
            beside["missing"] = t["missing"]
            if "formula" in t:
                f = t["formula"]
                beside["kg(h) = A h + B"] = {"A_kg_per_m": [kg(x) for x in f["A_t_per_m"]],
                                             "B_kg": [kg(x) for x in f["B_t"]], "h": "not printed (HELD)"}
                ev = "PARTIALLY VERIFIED"
        elif t["status"] == "HELD_RANGE_HIGH_OPEN":
            after, ev = held(kg(t["t_low"]), None), "PARTIALLY VERIFIED"
            beside["bounded_part_high_kg"] = kg(t["t_high_bounded_part"])
            beside["high_open_by_name"] = t["high_excluding"]
        else:
            raise ManifestError(f"T-583 status {t['status']}")
        if a8["element_id"].startswith("HL:DOME_RING:DOME-1F-E"):
            beside["F-C-T583-1"] = "strict low kept; the per-face reading of the side-bar label would add 21.771 kg"
        rows.append(row(P, "T-583", "ADD", f"NEW:STR.REBAR:{a8['element_id']}", None, after, ev, VERDICT["T-583"],
                        a8["item_code"], "kg", a8["element_id"], beside=beside))
    return P, rows


def pkg_rails(t578, idx):
    """T-578 runs: a HELD line takes its bound where one is formed (low > 0 or a finite high); the rest are stated."""
    P = "RAILS_GUARDS (T-578)"
    ev_of = {"RAIL:RL-07": ("VERIFIED", VERDICT["T-578"]), "RAIL:RL-02": ("VERIFIED", VERDICT["RAILS_LINES"]),
             "RAIL:RL-03": ("VERIFIED", VERDICT["RAILS_LINES"])}
    rows = []
    for run in t578["rails_lm"]["runs"]:
        lid = run["line"]
        cur = idx[lid]
        if cur["item_code"] != run["code"]:
            raise ManifestError(f"{lid}: code {cur['item_code']} vs T-578 {run['code']}")
        before = OV.state(cur)
        b = run.get("bound")
        if run["status"] == "HELD":
            lo, hi = (_d(b[0]), _d(b[1]) if b[1] is not None else None) if b else (None, None)
            if lo is not None and (lo > 0 or hi is not None):
                after = held(float(lo), None if hi is None else float(hi))
                rows.append(row(P, "R-T578-1 HELD bound", "SET", lid, before, after, "HELD", VERDICT["T-578"],
                                note=run["why"]))
            else:
                rows.append(row(P, "R-T578-1 HELD by name", "TEXT_ONLY", lid, before, None, "HELD", VERDICT["T-578"],
                                note="no bound formed (0 .. open): stays HELD blank by name; " + run["why"]))
        elif run["status"] == "NOT_APPLICABLE":
            rows.append(row(P, "R-T578-1 stated", "TEXT_ONLY", lid, before, None, "DRAWING-CONFIRMED", VERDICT["T-578"],
                            note=run.get("why")))
        else:
            if _d(run["value"]) != _d(cur["measured_net"]):
                raise ManifestError(f"{lid}: T-578 value {run['value']} vs index {cur['measured_net']}")
            ev, vl = ev_of.get(run["run"], (run["status"], VERDICT["RAILS_LINES"]))   # the line's own verdict
            rows.append(row(P, "R-T578-1 stated", "TEXT_ONLY", lid, before, None, ev, vl,
                            note=run.get("note") or None))
    return P, rows


def step_lines(t584):
    """{line_id: (stair, flight, role, treads)} from the T-584 flight table; E1 has no line before V9."""
    out = {}
    for stair, f in t584["flights"].items():
        for o in f["own"]:
            out[o["line"]] = (stair, o["flight"], "OWN", o["treads"])
        for o in f["held"]:
            out[o["line"]] = (stair, o["flight"], "OWN_HELD", o["treads"])
        for o in f["second_readings"]:
            out[o["line"]] = (stair, o["flight"], "SECOND_READING", None)
    return out


E1_ELEM = "GF-COURT#E1-STEPS"
E1_LINE = f"NEW:FIN.STAIR.STEP_LM:{E1_ELEM}"


def pkg_steps(t584, idx):
    """FR-T584-1 (E1 step line) + FR-T584-3 stair steps count x length (owner lines stated with nr, held owner lines
    take their bound, second readings leave HELD for EXCLUDED with evidence: their flight is owned once)."""
    P = "STAIR_STEPS (T-584 FR-T584-1 / FR-T584-3)"
    rows = []
    fx = next(r for r in t584["fix_rows"] if r["id"] == "FR-T584-1")
    e1 = t584["e1"]
    lm = Decimal(e1["lm"])
    if lm != Decimal(e1["treads"]) * Decimal("2.800"):
        raise ManifestError("E1: lm != treads x 2.800")
    rows.append(row(P, "FR-T584-1", "ADD", E1_LINE, None, released(float(lm)), "VERIFIED", VERDICT["T-584:E1"],
                    "FIN.STAIR.STEP_LM", "lm", E1_ELEM,
                    beside={"nr": e1["treads"], "binds": ["L-314c3ac6d45431b687c5", "L-0afa7bd369ec489ebfc2"],
                            "fronts": e1["fronts"][:e1["treads"]], "not_a_step": e1["fronts"][e1["treads"]:],
                            "material": "marble (OWNER_RULE_OUTDOOR_FLOORS)"},
                    note=fx["proposal"]))
    held_of = {o["line"]: o for f in t584["flights"].values() for o in f["held"]}
    for lid, (stair, flight, role, treads) in sorted(step_lines(t584).items()):
        cur = idx[lid]
        if cur["item_code"] != "FIN.STAIR.STEP_LM":
            raise ManifestError(f"{lid}: not a step lm line")
        before = OV.state(cur)
        if role == "OWN":
            if _d(cur["measured_net"]) != Decimal(treads) * Decimal("1.150"):
                raise ManifestError(f"{lid}: value != treads x 1.150")
            rows.append(row(P, "FR-T584-3", "BESIDE", lid, before, None, "PARTIALLY VERIFIED", VERDICT["T-584:FLIGHTS"],
                            beside={"nr": treads, "stair": stair, "flight": flight}))
        elif role == "OWN_HELD":
            b = held_of[lid]["bound"]
            after = held(float(b[0]), None if b[1] is None else float(b[1]))
            rows.append(row(P, "FR-T584-3", "SET", lid, before, after, "HELD", VERDICT["T-584:FLIGHTS"],
                            beside={"nr": treads, "stair": stair, "flight": flight}, note=held_of[lid]["why"]))
        elif cur["class"] == "EXCLUDED":
            rows.append(row(P, "FR-T584-3", "TEXT_ONLY", lid, before, None, "PARTIALLY VERIFIED",
                            VERDICT["T-584:FLIGHTS"], note=f"second reading of {stair} {flight}: stays EXCLUDED"))
        else:
            rows.append(row(P, "FR-T584-3", "SET", lid, before, excluded(), "PARTIALLY VERIFIED",
                            VERDICT["T-584:FLIGHTS"],
                            note=f"second reading of {stair} {flight} (T-129 / T-429; T-584): the flight is owned by "
                                 f"its own line; NOT_APPLICABLE_WITH_EVIDENCE, its HELD bound left the HELD sum"))
    return P, rows


# ---- R-T588-1 (d): drawn edge census --------------------------------------------------------------------------

def load_edges(path=None):
    rows = list(csv.DictReader(Path(path or IN["T412"]).open(encoding="utf-8")))
    return [{"eid": r["eid"], "stair": r["stair"], "flight": r["flight"], "kind": r["kind"], "status": r["status"],
             "in_step_basis": r["in_step_basis"] == "yes", "qty_lm": r["qty_lm"]} for r in rows]


def step_claims(edges, flight_of_line, live):
    """edges priced by each LIVE step-lm line: the in-step-basis edges of its flight; a winder flight (kind WINDER)
    owns every WINDER edge of its stair (a winder fan crossing a flight boundary is one turn)."""
    claims = {}
    for lid, (stair, flight) in flight_of_line.items():
        if lid not in live:
            continue
        mine = [e["eid"] for e in edges if e["stair"] == stair and e["in_step_basis"]
                and (flight == _winder_owner(edges, stair) if e["kind"] == "WINDER" else e["flight"] == flight)]
        claims[lid] = mine
    return claims


def _winder_owner(edges, stair):
    """the flight holding the most WINDER edges of the stair owns its winder turn."""
    n = {}
    for e in edges:
        if e["stair"] == stair and e["kind"] == "WINDER":
            n[e["flight"]] = n.get(e["flight"], 0) + 1
    return max(sorted(n), key=lambda f: n[f]) if n else None


def census(edges, claims, nosing_owner="B7-05 (T-424)"):
    """every edge priced exactly once: step lines claim in-step-basis edges, the nosing line the rest."""
    by = {e["eid"]: [] for e in edges}
    for lid, eids in claims.items():
        for x in eids:
            if x not in by:
                raise ManifestError(f"{lid} claims an edge {x} not in the census")
            by[x].append(lid)
    for e in edges:
        if not e["in_step_basis"]:
            by[e["eid"]].append(nosing_owner)
    doubles = {k: v for k, v in by.items() if len(v) > 1}
    orphans = sorted(k for k, v in by.items() if not v)
    per = {}
    for e in edges:
        s = per.setdefault(e["stair"], {"edges": 0, "step_basis": 0, "nosing_line": 0, "held": 0})
        s["edges"] += 1
        s["step_basis" if e["in_step_basis"] else "nosing_line"] += 1
        s["held"] += e["status"] == "HELD"
    return {"edges": len(edges), "doubles": doubles, "orphans": orphans, "by_stair": per}


def census_on(index, edges, t584, extra_lines=None):
    sl = step_lines(t584)
    flight_of = {lid: (s, f) for lid, (s, f, _, _) in sl.items()}
    flight_of.update(extra_lines or {})
    live = {k for k, l in index.items() if l["class"] != "EXCLUDED" and l["item_code"] == "FIN.STAIR.STEP_LM"}
    return census(edges, step_claims(edges, flight_of, live))


# ---- overlay ----------------------------------------------------------------------------------------------------

def v9_packages(t578, t583, t584, v8, idx):
    return [pkg_rebar(t583, v8), pkg_rails(t578, idx), pkg_steps(t584, idx)]


def overlay_order(base_pk, v9):
    """V2 .. V8 in the T-580 order, V8 REBAR_OMISSION replaced BY NAME by V9 REBAR_COMPONENTS, then the V9 rest."""
    out, replaced = [], False
    for n, ops in base_pk:
        if n == "REBAR_OMISSION":
            out.append(v9[0])
            replaced = True
        else:
            out.append((n, ops))
    if not replaced:
        raise ManifestError("V8 REBAR_OMISSION not found in the base order: nothing to supersede")
    return out + list(v9[1:])


def byte_identical_others(after_v8, after_v9, v9_lines):
    """every line V9 does not write is identical between the V8 overlay and the V9 overlay."""
    bad = [k for k in set(after_v8) | set(after_v9) if k not in v9_lines and after_v8.get(k) != after_v9.get(k)]
    return sorted(bad)


def build():
    m = T580.manifests()
    idx = T580.base_index()
    st = T580.stage()
    base_pk = T580.packages(m, idx, st)
    t578, t583, t584, v8 = _json(IN["T578"]), _json(IN["T583"]), _json(IN["T584"]), _json(IN["V8"])
    v9 = v9_packages(t578, t583, t584, v8, idx)
    for _, rows in v9:
        validate_rows(rows)
    after_v8, rep_v8 = OV.apply(idx, base_pk, T580.RULINGS)
    order = overlay_order(base_pk, v9)
    after_v9, rep = OV.apply(idx, order, list(T580.RULINGS) + RULINGS_V9)
    v9_lines = {r["line_id"] for _, rows in v9 for r in rows}
    edges = load_edges()
    e1 = {E1_LINE: ("ST-03", "E1")}
    cen_before = census_on(after_v8, edges, t584)
    cen_after = census_on(after_v9, edges, t584, e1)
    # T-578 nosing = the T-412 census (one source, never a second claim)
    conf = [e for e in edges if e["status"] == "DRAWING-CONFIRMED"]
    t578_n = t578["nosing_lm"]["totals"]
    one_source = {"t412_confirmed_n": len(conf), "t412_confirmed_lm": format(sum(Decimal(e["qty_lm"]) for e in conf), "f"),
                  "t412_held_n": len(edges) - len(conf), "t578_ours_lm": t578_n["ours"],
                  "t578_held_n": t578_n["held_n"],
                  "same": (Decimal(t578_n["ours"]) == sum(Decimal(e["qty_lm"]) for e in conf)
                           and t578_n["held_n"] == len(edges) - len(conf))}
    v9rows = [dict(r, package=n) for n, rows in v9 for r in rows]
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    t8, t9 = OV.totals(after_v8), OV.totals(after_v9)
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-588",
        "candidate": T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "supersedes": {"V8 REBAR_OMISSION": "V9 REBAR_COMPONENTS (same 6 line ids, T-583 states)"},
        "not_in_v9": {"FR-T584-2": "external door steps: the line pays ONE length (F-C-T584-1); enters V10 after T-592",
                      "B7-05 nosing lines": "T-424 (QUEUED) adds them from T-412; V9 adds none (T-578 reads the same "
                                            "census, one source)"},
        "rows": v9rows,
        "overlay": {
            "lines": {"base": len(idx), "after_v8": len(after_v8), "after_v9": len(after_v9)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order],
            "flagged_rows": [r for r in rep["rows"] if r["status"] != "APPLIED"],
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                   # OV.apply raises R1 otherwise
            "conflicts": rep["conflicts"],
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v8_overlay": byte_identical_others(after_v8, after_v9, v9_lines),
            "v9_vs_v8_totals": OV.diff_totals(t8, t9),
        },
        "edge_census": {"rule": "R-T588-1 (d)", "before_v9": cen_before, "after_v9": cen_after,
                        "t578_one_source": one_source},
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-588 manifest V9: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
