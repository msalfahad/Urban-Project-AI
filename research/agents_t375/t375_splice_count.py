"""T-375 SPLICE-COUNT DEFECT of the FROZEN continuous_beams._with_laps (research code, stdlib + the engine read only).

Physical element. A continuous bar run of length L longer than the stock bar S is built from N pieces, each at most S
long, joined by N - 1 lap splices of length lap. The pieces must cover the run including the overlaps:
    N x S - (N - 1) x lap >= L   <=>   N >= (L - lap) / (S - lap)   =>   N = ceil((L - lap) / (S - lap))  (L > S)
    procurement length = L + (N - 1) x lap;  N = 1 (no splice) when L <= S;  lap >= S is BLOCKED (no bar can be spliced).
This is a fact of L, S and lap (arithmetic), not of the lap authority: the lap VALUE stays HELD wherever T-366 / T-373
hold it.

The frozen form (engine/source/continuous_beams.py `_with_laps`, read only, FROZEN) counts N - 1 = ceil(L / S) - 1,
which ignores the length every lap consumes. Proved here (exact rationals) and tested:
  P1  identity: ceil((L - lap) / (S - lap)) - 1 == ceil((L - S) / (S - lap)) for L > S, i.e. the proposed piece count is
      the owner formula (OWNER_RULE_REBAR_2026-10-24 s.2), bbs_optimiser.split_run and rebar_laps_v1.lap_count_exact
      (CONTINUOUS_BEAM_LAPS_V2, T-273, merged 42e32cf3): ONE formula, no third copy.
  P2  the frozen count is never above the correct one (frozen is a LOWER bound: it can only under-count laps).
  P3  they disagree exactly on the windows  S + k (S - lap) < L <= (k + 1) S,  k = 1, 2, ...  (width k x lap each);
      equivalently the frozen count is right only for lap <= S - (L - S) / n0, n0 = ceil(L / S) - 1 (T-366 s.5).
  P4  deficit = ceil((L - S) / (S - lap)) - ceil(L / S) + 1 < (L - S) lap / (S (S - lap)) + 1; it is 1 on every
      window while k x lap <= S - lap, i.e. for every run L <= (S / lap) x S (240 m at lap 0.6 m, S 12 m).

    python3 -I research/agents_t375/t375_splice_count.py build          # boundary table + caller census (committed)
    python3 -I research/agents_t375/t375_splice_count.py build --check  # rebuild in memory, compare with the files
    python3 -I research/agents_t375/t375_splice_count.py routeg <structural.dxf> --out <scratch>
        # instrumented route G run (private drawing; scratch output only): every _with_laps call, frozen vs proposed
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "T375_SPLICE_COUNT_V1"
METHOD_ID = "CONTINUOUS_BEAM_LAPS_V2"          # the existing new method version (engine/source/rebar_laps_v1.py, T-273)
RULE_ID = "R-T375-1"
STOCK_M = Fraction(12)                         # OD-V3-3: 12 m stock, ASSUMED - OWNER-APPROVED (T-366)
LAPS_M = ("0.40", "0.48", "0.64", "0.84")      # the row's boundary laps (40 d at 10 / 12 / 16 mm, 60 d at 14 mm)
L_FROM, L_TO, L_STEP = Fraction("11.9"), Fraction(48), Fraction("0.1")
BOUNDARY_CSV = HERE / "T375_BOUNDARY_TABLE.csv"
CALLERS_JSON = HERE / "T375_CALLERS.json"
SUMMARY_JSON = HERE / "T375_SUMMARY.json"
SCAN_DIRS = ("engine", "tools")


class SpliceError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ exact arithmetic
def q(value) -> Fraction:
    """a length in metres as an exact rational: decimal text, Decimal, int, Fraction or float (shortest repr)."""
    if isinstance(value, bool):
        raise SpliceError("a boolean is not a length")
    if isinstance(value, Fraction):
        x = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise SpliceError(f"length {value!r} not finite")
        x = Fraction(Decimal(repr(value)))
    else:
        try:
            x = Fraction(Decimal(str(value).strip()))
        except Exception as e:  # noqa: BLE001
            raise SpliceError(f"length {value!r} not a number") from e
    if x < 0:
        raise SpliceError(f"length {value!r} negative")
    return x


def _ceil(x: Fraction) -> int:
    return -((-x.numerator) // x.denominator)


def _check(L, lap, S):
    L, S = q(L), q(S)
    if S <= 0:
        raise SpliceError("stock length not given")
    lp = None if lap is None else q(lap)
    if L > S:
        if lp is None:
            raise SpliceError("a run longer than the stock needs a lap length to count its splices (HELD, never 0)")
        if lp >= S:
            raise SpliceError(f"lap {lp} m not shorter than the stock {S} m: BLOCKED")
    return L, lp, S


def frozen_laps(L, S=STOCK_M) -> int:
    """the FROZEN continuous_beams._with_laps count, n = ceil(L / S) - 1 (0 when L <= S); independent of the lap."""
    L, S = q(L), q(S)
    return 0 if L <= S else _ceil(L / S) - 1


def pieces(L, lap, S=STOCK_M) -> int:
    """PROPOSED (= CONTINUOUS_BEAM_LAPS_V2): pieces N = ceil((L - lap) / (S - lap)); 1 when L <= S."""
    L, lp, S = _check(L, lap, S)
    return 1 if L <= S else _ceil((L - lp) / (S - lp))


def laps(L, lap, S=STOCK_M) -> int:
    return pieces(L, lap, S) - 1


def procurement_length(L, lap, S=STOCK_M) -> Fraction:
    """L + (N - 1) x lap (installed run plus the lap steel; never the net quantity)."""
    n = laps(L, lap, S)
    return q(L) + (n * q(lap) if n else 0)


def frozen_length(L, lap, S=STOCK_M) -> Fraction:
    n = frozen_laps(L, S)
    return q(L) + (n * q(lap) if n else 0)


def covers(L, lap, S, n_pieces) -> bool:
    """physical check: n pieces of at most S joined by n - 1 laps reach L."""
    return n_pieces * q(S) - (n_pieces - 1) * q(lap) >= q(L)


def windows(lap, S=STOCK_M, L_max=Fraction(48)):
    """P3: the run-length windows (lo, hi] where the frozen count is short by exactly k -> (k, lo, hi, deficit)."""
    lp, S, L_max = q(lap), q(S), q(L_max)
    out, k = [], 1
    while S + k * (S - lp) < L_max:
        lo, hi = S + k * (S - lp), (k + 1) * S
        if lo < hi:
            out.append((k, lo, min(hi, L_max) if hi > L_max else hi))
        k += 1
    return out


def safe_lap_max(L, S=STOCK_M):
    """the largest lap for which the frozen count is right on a run L (None: any lap, L <= S)."""
    L, S = q(L), q(S)
    if L <= S:
        return None
    n0 = _ceil(L / S) - 1
    return S - (L - S) / n0


def deficit_bound(L, lap, S=STOCK_M) -> Fraction:
    """P4 strict upper bound of (correct - frozen): (L - S) lap / (S (S - lap)) + 1."""
    L, lp, S = _check(L, lap, S)
    return Fraction(1) if L <= S else (L - S) * lp / (S * (S - lp)) + 1


# ------------------------------------------------------------------------------------------------ boundary table
def _grid():
    L, out = L_FROM, []
    while L <= L_TO:
        out.append(L)
        L += L_STEP
    return out


def _fmt(x: Fraction, nd=4) -> str:
    return f"{float(x):.{nd}f}"


def boundary_rows():
    """(a): L 11.9 .. 48.0 m step 0.1 m, plus every window edge and a hair (1 mm) either side, at each row lap; S 12."""
    rows = []
    for lap_t in LAPS_M:
        lap = q(lap_t)
        Ls = set(_grid())
        for k, lo, hi in windows(lap):
            Ls |= {lo, lo + Fraction(1, 1000), hi, hi + Fraction(1, 1000) if hi + Fraction(1, 1000) <= L_TO else hi}
        Ls |= {STOCK_M, STOCK_M + Fraction(1, 1000)}
        for L in sorted(x for x in Ls if L_FROM <= x <= L_TO):
            nf, nv = frozen_laps(L), laps(L, lap)
            k = next((w[0] for w in windows(lap) if w[1] < L <= w[2]), "")
            rows.append({"run_m": _fmt(L, 3), "lap_m": lap_t, "stock_m": "12", "laps_frozen": nf, "laps_proposed": nv,
                         "pieces_proposed": nv + 1, "length_frozen_m": _fmt(frozen_length(L, lap)),
                         "length_proposed_m": _fmt(procurement_length(L, lap)),
                         "difference_m": _fmt(procurement_length(L, lap) - frozen_length(L, lap)),
                         "frozen_pieces_cover_run": "YES" if covers(L, lap, STOCK_M, nf + 1) else "NO",
                         "agree": "YES" if nf == nv else "NO", "window_k": k,
                         "frozen_safe_up_to_lap_m": "" if safe_lap_max(L) is None else _fmt(safe_lap_max(L))})
    return rows


def _csv_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


# ------------------------------------------------------------------------------------------------ caller census
def _is_frozen_form(node) -> bool:
    """`ceil(<x> / <stock-like>) - 1` anywhere (math.ceil or ceil)."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub) and isinstance(node.right, ast.Constant)
            and node.right.value == 1 and isinstance(node.left, ast.Call)):
        return False
    f = node.left.func
    name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
    if name != "ceil" or not node.left.args:
        return False
    a = node.left.args[0]
    if isinstance(a, ast.BinOp) and isinstance(a.op, ast.Sub):            # ceil(L / S - 1e-12) - 1
        a = a.left
    if not (isinstance(a, ast.BinOp) and isinstance(a.op, ast.Div)):
        return False
    den = a.right
    dn = den.id if isinstance(den, ast.Name) else (den.attr if isinstance(den, ast.Attribute) else "")
    return "stock" in dn.lower() or dn == "S"


def caller_census(root=ROOT, dirs=SCAN_DIRS):
    """(b) static part: every reference to _with_laps / physical_bars / a frozen-form copy in engine/ and tools/."""
    refs, copies = [], []
    for d in dirs:
        for p in sorted((Path(root) / d).rglob("*.py")):
            rel = p.relative_to(root).as_posix()
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            func_at = {}
            for fn in ast.walk(tree):
                if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for sub in ast.walk(fn):
                        if hasattr(sub, "lineno"):
                            func_at.setdefault(sub.lineno, fn.name)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Name, ast.Attribute)):
                    nm = node.id if isinstance(node, ast.Name) else node.attr
                    if nm in ("_with_laps", "physical_bars") and isinstance(getattr(node, "ctx", None), ast.Load):
                        refs.append({"file": rel, "line": node.lineno, "symbol": nm,
                                     "in_function": func_at.get(node.lineno, "<module>")})
                if _is_frozen_form(node):
                    copies.append({"file": rel, "line": node.lineno, "in_function": func_at.get(node.lineno, "<module>")})
    refs.sort(key=lambda r: (r["file"], r["line"], r["symbol"]))
    copies.sort(key=lambda r: (r["file"], r["line"]))
    return {"references": refs, "frozen_form_copies": copies}


COPY_VERDICTS = {
    # file -> function -> why it is or is not the defect (read, not inferred)
    ("engine/source/continuous_beams.py", "_with_laps"): "THE DEFECT (frozen, route G continuous-beam bar groups)",
    ("engine/source/rebar_laps_v1.py", "frozen_with_laps"): "reproduction for before / after only (T-273), not on a route",
    ("engine/source/rebar_laps_v1.py", "compare_with_frozen"): "reproduction for before / after only (T-273)",
    ("engine/source/rebar_laps_v1.py", "_coupler_row"): "CORRECT here: a mechanical coupler consumes no bar length, so "
                                                        "joints = ceil(L / S) - 1 (owner s.6.1 category)",
}


# ------------------------------------------------------------------------------------------------ route G instrumentation
def instrument_route_g(structural_dxf, out_dir, *, profile=None, conventions=None):
    """(b) run part: route G (tools/urban_boq_m2.compute, route G, conventions V6 + the M4 drawing profile = the
    candidate's rule_id URBAN_M8_GENERIC_CONVENTIONS_V6+ST7757_M4) on the structural DXF with continuous_beams'
    _with_laps and physical_bars wrapped in memory (the frozen module file is not touched). Every bar group's three
    readings are recomputed with the proposed count; kg scenario = count x d^2 / 162 x (proposed - frozen) per reading."""
    from engine.source import continuous_beams as CBM
    from tools import urban_boq_m2 as M2
    profile = profile or ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
    conventions = conventions or ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
    orig_wl, orig_pb = CBM._with_laps, CBM.physical_bars
    calls, groups = [], []

    def rec_wl(L, d_mm, lap_d, stock_m):
        calls.append((L, d_mm, lap_d, stock_m))
        return orig_wl(L, d_mm, lap_d, stock_m)

    def rec_pb(m, row, **kw):
        start = len(calls)
        res = orig_pb(m, row, **kw)
        mine = calls[start:]
        lap_groups = [g for g in res["groups"] if g["role"] != "STIRRUP"]
        if len(mine) != 3 * len(lap_groups):
            raise SpliceError(f"call / group mismatch {len(mine)} vs 3 x {len(lap_groups)}")
        for i, g in enumerate(lap_groups):
            three = mine[3 * i:3 * i + 3]
            per = []
            for (L, d_mm, lap_d, stock_m) in three:
                lap = Fraction(Decimal(repr(float(lap_d)))) * Fraction(Decimal(repr(float(d_mm)))) / 1000
                Lq, Sq = q(float(L)), q(float(stock_m))
                nf, nv = frozen_laps(Lq, Sq), (laps(Lq, lap, Sq) if Lq > Sq else 0)
                dm = (nv - nf) * lap
                per.append({"run_m": round(float(L), 6), "lap_m": float(lap), "laps_frozen": nf, "laps_proposed": nv,
                            "delta_m_per_bar": float(dm),
                            "delta_kg": float(g["count"] * d_mm ** 2 / 162.0 * float(dm))})
            groups.append({"mark": row.get("mark"), "role": g["role"], "k": g["k"], "count": g["count"],
                           "dia_mm": g["dia_mm"], "readings": per})
        return res

    CBM._with_laps, CBM.physical_bars = rec_wl, rec_pb
    try:
        M2.compute([str(structural_dxf)], conventions=str(conventions), profile=str(profile), route="G",
                   completeness=True)        # as tools/urban_boq_m9.py arch --structural (default completeness)
    finally:
        CBM._with_laps, CBM.physical_bars = orig_wl, orig_pb
    runs = [r["run_m"] for g in groups for r in g["readings"]]
    summ = {"schema": SCHEMA + ":ROUTE_G_RUN", "structural_dxf_sha256": hashlib.sha256(
                Path(structural_dxf).read_bytes()).hexdigest(),
            "profile": Path(profile).relative_to(ROOT).as_posix(), "conventions": Path(conventions).relative_to(ROOT).as_posix(),
            "with_laps_calls": len(calls), "bar_groups": len(groups),
            "marks": sorted({g["mark"] for g in groups}), "stock_m": sorted({float(c[3]) for c in calls}),
            "lap_d": sorted({float(c[2]) for c in calls}),
            "longest_run_m": max(runs) if runs else None,
            "runs_over_stock": sum(1 for c in calls if float(c[0]) > float(c[3])),
            "readings_that_differ": sum(1 for g in groups for r in g["readings"] if r["laps_frozen"] != r["laps_proposed"]),
            "delta_kg_low_base_high": [round(sum(g["readings"][i]["delta_kg"] for g in groups), 6) for i in range(3)],
            "longest_by_role": {}}
    for g in groups:
        L = max(r["run_m"] for r in g["readings"])
        cur = summ["longest_by_role"].get(g["role"])
        if cur is None or L > cur["run_m"]:
            summ["longest_by_role"][g["role"]] = {"run_m": L, "mark": g["mark"], "dia_mm": g["dia_mm"]}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "T375_ROUTE_G_GROUPS.json").write_text(json.dumps(groups, indent=1), encoding="utf-8")
    (out / "T375_ROUTE_G_SUMMARY.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    return summ


# ------------------------------------------------------------------------------------------------ candidate lines
EXTRACT = ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"     # T-297 (merged), V3.0.16 = V3.0.17 rebar
T373_CSV = ROOT / "research/agents_t373/T373_LAP_BINDING.csv"                 # T-373 (merged), V3.0.27 lap-bearing lines
ROUTE_G_RUN = HERE / "T375_ROUTE_G_RUN.json"                                  # this run's instrumented route G summary
LATER_STEPS = tuple(f"engine/source/arch_v30{n}.py" for n in range(17, 29))   # V3.0.17 .. V3.0.28 integration steps
CB_TOKENS = (":CB_", "physical_bars", "_with_laps", "continuous_beams")


def candidate_binding(root=ROOT):
    """(b) candidate part: the reinforcement lines whose quantity could come through _with_laps. The only producer is
    route G's continuous-beam items (element id '...:CB_<role>'); on the candidate they are SUPERSEDED by the T-149 hand
    ledger (state NOT_APPLICABLE_WITH_EVIDENCE, no quantity). Later steps V3.0.17 .. V3.0.28 are scanned for any CB /
    continuous-beam token (none = they never re-book those lines); T-373's V3.0.27 lap-bearing set is checked too."""
    ex = json.loads(Path(EXTRACT).read_text(encoding="utf-8"))
    cb = [ln for ln in ex["lines"] if ":CB_" in (ln.get("element_id") or "")]
    later = {}
    for rel in LATER_STEPS:
        p = Path(root) / rel
        later[rel] = sorted(t for t in CB_TOKENS if p.exists() and t in p.read_text(encoding="utf-8")) \
            if p.exists() else "MISSING"
    with open(Path(root) / T373_CSV.relative_to(ROOT), encoding="utf-8", newline="") as f:
        t373_cb = [r["line_id"] for r in csv.DictReader(f) if ":CB_" in r["element_id"]]
    rg = json.loads(ROUTE_G_RUN.read_text(encoding="utf-8")) if ROUTE_G_RUN.exists() else None
    moved = None if rg is None else rg["delta_kg_low_base_high"]
    lines = [{"line_id": ln["line_id"], "element_id": ln["element_id"], "floor": ln.get("floor"),
              "evidence_state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
              "bounded_range": ln.get("bounded_range"),
              "scenario_delta_kg": "NO QUANTITY ON THE LINE (superseded); the route G steel behind it moves "
                                   + ("not measured" if moved is None else f"{moved} kg (40 / 50 / 60 d)")}
             for ln in sorted(cb, key=lambda x: x["line_id"])]
    states = sorted({ln["evidence_state"] for ln in cb})
    return {"schema": SCHEMA + ":CANDIDATE_BINDING", "extract": EXTRACT.relative_to(ROOT).as_posix(),
            "extract_candidate": ex.get("candidate"), "cb_lines": len(cb), "cb_states": states,
            "cb_lines_with_quantity": sum(1 for ln in cb if ln.get("measured_net") is not None or ln.get("bounded_range")),
            "later_steps_cb_tokens": later,
            "later_steps_touching_cb": sorted(k for k, v in later.items() if v),
            "t373_v3027_cb_lines": t373_cb, "route_g_run": rg, "lines": lines}


# ------------------------------------------------------------------------------------------------ outputs
def build():
    rows = boundary_rows()
    census = caller_census()
    cand = candidate_binding()
    for c in census["frozen_form_copies"]:
        c["verdict"] = COPY_VERDICTS.get((c["file"], c["in_function"]), "UNCLASSIFIED: read it before wiring")
    dis = [r for r in rows if r["agree"] == "NO"]
    summ = {"schema": SCHEMA, "method_id": METHOD_ID, "rule_id": RULE_ID, "stock_m": "12 (OD-V3-3)",
            "laps_m": list(LAPS_M), "rows": len(rows), "disagreements": len(dis),
            "disagreements_by_lap": {lp: [r["run_m"] for r in dis if r["lap_m"] == lp] for lp in LAPS_M},
            "windows_m": {lp: [[k, _fmt(lo, 4), _fmt(hi, 4)] for k, lo, hi in windows(q(lp))] for lp in LAPS_M},
            "frozen_ever_above_proposed": any(r["laps_frozen"] > r["laps_proposed"] for r in rows),
            "max_deficit_laps": max(r["laps_proposed"] - r["laps_frozen"] for r in rows),
            "frozen_pieces_short_of_run_when_disagree": all(r["frozen_pieces_cover_run"] == "NO" for r in dis),
            "callers": {"references": len(census["references"]),
                        "route_path": "generic_route._cb_model -> continuous_beams.physical_bars -> add -> _with_laps",
                        "frozen_form_copies": len(census["frozen_form_copies"])},
            "candidate": {"cb_lines": cand["cb_lines"], "cb_states": cand["cb_states"],
                          "cb_lines_with_quantity": cand["cb_lines_with_quantity"],
                          "later_steps_touching_cb": cand["later_steps_touching_cb"],
                          "t373_v3027_cb_lines": len(cand["t373_v3027_cb_lines"]),
                          "route_g_longest_run_m": (cand["route_g_run"] or {}).get("longest_run_m"),
                          "route_g_delta_kg": (cand["route_g_run"] or {}).get("delta_kg_low_base_high")}}
    return {"csv": _csv_text(rows), "callers": json.dumps(census, indent=1) + "\n",
            "candidate": json.dumps(cand, indent=1) + "\n",
            "summary": json.dumps(summ, indent=1, sort_keys=True) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--check", action="store_true")
    r = sub.add_parser("routeg")
    r.add_argument("structural")
    r.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "routeg":
        print(json.dumps(instrument_route_g(a.structural, a.out), indent=1))
        return 0
    out = build()
    files = {BOUNDARY_CSV: out["csv"], CALLERS_JSON: out["callers"], SUMMARY_JSON: out["summary"],
             HERE / "T375_CANDIDATE_BINDING.json": out["candidate"]}
    if a.check:
        bad = [p.name for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    for p, t in files.items():
        p.write_text(t, encoding="utf-8")
    print(out["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
