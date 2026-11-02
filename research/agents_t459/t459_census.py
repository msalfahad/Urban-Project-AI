"""T-459 REBAR LAPS (owner directive 2026-11-02 C4): bar-length census and before / after of the lap rule on route G
(research code; the engine is read only, the frozen continuous_beams module and the V6 profile are never written).

Physical element. A lap splice is installed steel where a continuous bar run L exceeds the stock S (12 m, ASSUMED -
OWNER-APPROVED OD-V3-3, T-366), and once per storey joint on column main bars. Two separate defects in route G:
  COUNT   continuous_beams._with_laps n = ceil(L / S) - 1 (frozen) vs ceil((L - S) / (S - lap)) (owner formula,
          CONTINUOUS_BEAM_LAPS_V2): matters only for runs L > S.
  LENGTH  BEAM_LAP_D and COLUMN_LAP_D = 40 / 50 / 60 d (base 50, STANDARD_PRACTICE) for both classes vs the owner
          classes 40 d columns / 60 d beams-slabs-footings (engine/source/rebar_lap_rule_v2.py, PROVISIONAL): matters
          wherever a lap is added at all (every column storey; beam runs > S).

    python3 -I research/agents_t459/t459_census.py routeg <structural.dxf> --out <scratch>
        # two instrumented route G runs (V6 as released / V6 with the V2 lap rule in memory); writes the summary and
        # the per-item diff to <scratch> (private drawing: scratch only); the committed T459_ROUTE_G_RUN.json is the
        # summary of that run (families, counts, kg; no drawing content beyond member family / storey / diameter)
    python3 -I research/agents_t459/t459_census.py candidate      # which candidate lines carry route G lap items
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "T459_LAP_CENSUS_V1"
PROFILE = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
CONVENTIONS = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
EXTRACT = ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"      # T-297 (merged): V3.0.16 rebar lines
ROUTE_G_RUN = HERE / "T459_ROUTE_G_RUN.json"
CANDIDATE_JSON = HERE / "T459_CANDIDATE_BINDING.json"
LAP_IDS = ("BEAM_LAP_D", "COLUMN_LAP_D")
TOKENS = ("P-S:", "COLUMN_LAP_D", "BEAM_LAP_D", "_with_laps", "continuous_beams", ":CB_")


def v2_conventions(src=CONVENTIONS):
    """the V6 convention set with the two lap entries replaced by the V2 class value (one value, low = base = high)."""
    from engine.source import rebar_lap_rule_v2 as V
    d = json.loads(Path(src).read_text(encoding="utf-8"))
    d = copy.deepcopy(d)
    seq = d.get("conventions") or d.get("items")
    for c in seq:
        if c["id"] in LAP_IDS:
            f = V.lap_factor_d("BEAM" if c["id"] == "BEAM_LAP_D" else "COLUMN")
            c.update(low=f, base=f, high=f, source="T-459 SCENARIO: REBAR_LAP_RULE_V2 owner class, PROVISIONAL")
    return d


def _run(dxf, conventions_path, *, v2_count):
    """one route G run; records every continuous-beam _with_laps call and every bar_shapes.mass_kg length."""
    from engine.source import bar_shapes as BS
    from engine.source import continuous_beams as CBM
    from tools import urban_boq_m2 as M2
    orig_wl, orig_mk = CBM._with_laps, BS.mass_kg
    wl, lengths = [], []

    def rec_wl(L, d_mm, lap_d, stock_m):
        if v2_count:
            lap = Fraction(str(float(lap_d))) * Fraction(str(float(d_mm))) / 1000
            Lq, Sq = Fraction(repr(float(L))), Fraction(repr(float(stock_m)))
            q = (Lq - Sq) / (Sq - lap)
            n = 0 if Lq <= Sq else -((-q.numerator) // q.denominator)
            out = float(L) + n * float(lap)
        else:
            out = orig_wl(L, d_mm, lap_d, stock_m)
        wl.append((float(L), float(d_mm), float(lap_d), float(stock_m), out))
        return out

    def rec_mk(length_m, d_mm, count=1):
        f = sys._getframe(1)
        lengths.append((float(length_m), float(d_mm), f.f_code.co_name))
        return orig_mk(length_m, d_mm, count)

    CBM._with_laps, BS.mass_kg = rec_wl, rec_mk
    try:
        res = M2.compute([str(dxf)], conventions=str(conventions_path), profile=str(PROFILE), route="G",
                         completeness=True)
    finally:
        CBM._with_laps, BS.mass_kg = orig_wl, orig_mk
    items = [i for i in res["items"] if i.get("trade") == "REINFORCEMENT"]
    return items, wl, lengths


def _num(x):
    return None if x is None else float(x)


def instrument_route_g(dxf, out_dir):
    before, wl_a, len_a = _run(dxf, CONVENTIONS, v2_count=False)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "conv_v6_lap_v2.json"
        p.write_text(json.dumps(v2_conventions()), encoding="utf-8")
        after, wl_b, _ = _run(dxf, p, v2_count=True)
    A = {i["item_id"]: i for i in before}
    B = {i["item_id"]: i for i in after}
    if set(A) != set(B):
        raise SystemExit(f"item sets differ: {len(set(A) ^ set(B))} ids")
    fam = defaultdict(lambda: {"items": 0, "changed": 0, "before_base_kg": 0.0, "after_base_kg": 0.0,
                               "before_low_kg": 0.0, "after_low_kg": 0.0, "before_high_kg": 0.0, "after_high_kg": 0.0})
    diff = []
    for k in sorted(A):
        a, b = A[k], B[k]
        key = f"{a.get('family')}|{a.get('storey')}"
        r = fam[key]
        r["items"] += 1
        for s in ("base", "low", "high"):
            r[f"before_{s}_kg"] += _num(a.get(s)) or 0.0
            r[f"after_{s}_kg"] += _num(b.get(s)) or 0.0
        if any(_num(a.get(s)) != _num(b.get(s)) for s in ("low", "base", "high")):
            r["changed"] += 1
            diff.append({"item_id": k, "family": a.get("family"), "storey": a.get("storey"), "dia_mm": a.get("dia_mm"),
                         "assumptions": a.get("assumptions"), "before": [a.get("low"), a.get("base"), a.get("high")],
                         "after": [b.get("low"), b.get("base"), b.get("high")]})
    for r in fam.values():
        for kk in list(r):
            if kk.endswith("_kg"):
                r[kk] = round(r[kk], 6)
        r["delta_base_kg"] = round(r["after_base_kg"] - r["before_base_kg"], 6)
    tot = lambda w: round(sum(r[w] for r in fam.values()), 6)          # noqa: E731
    over = [x for x in len_a if x[0] > 12.0 + 1e-9]
    by_caller = defaultdict(lambda: {"calls": 0, "max_length_m": 0.0})
    for L, d, c in len_a:
        by_caller[c]["calls"] += 1
        by_caller[c]["max_length_m"] = max(by_caller[c]["max_length_m"], round(L, 6))
    changed_fams = sorted({d["family"] for d in diff})
    summ = {
        "schema": SCHEMA + ":ROUTE_G_RUN",
        "structural_dxf_sha256": hashlib.sha256(Path(dxf).read_bytes()).hexdigest(),
        "profile": PROFILE.relative_to(ROOT).as_posix(), "conventions": CONVENTIONS.relative_to(ROOT).as_posix(),
        "scenario": "V6 with BEAM_LAP_D = 60 / 60 / 60 and COLUMN_LAP_D = 40 / 40 / 40 (REBAR_LAP_RULE_V2 owner "
                    "classes) + the continuous-beam count replaced by ceil((L - S) / (S - lap)); in memory only",
        "reinforcement_items": len(A),
        "items_changed": len(diff), "families_changed": changed_fams,
        "bar_length_census": {
            "mass_kg_calls": len(len_a), "longest_bar_m": round(max(x[0] for x in len_a), 6),
            "bars_over_stock_12m": len(over), "over_stock_callers": sorted({x[2] for x in over}),
            "by_caller": dict(sorted(by_caller.items())),
            "cb_with_laps_calls": len(wl_a), "cb_longest_run_m": round(max(x[0] for x in wl_a), 6) if wl_a else None,
            "cb_runs_over_stock": sum(1 for x in wl_a if x[0] > x[3] + 1e-9),
            "cb_lengths_that_change_by_count_or_lap": sum(1 for a, b in zip(wl_a, wl_b) if abs(a[4] - b[4]) > 1e-12),
        },
        "totals_kg": {"before_low": tot("before_low_kg"), "before_base": tot("before_base_kg"),
                      "before_high": tot("before_high_kg"), "after_low": tot("after_low_kg"),
                      "after_base": tot("after_base_kg"), "after_high": tot("after_high_kg")},
        "by_family_storey": dict(sorted(fam.items())),
    }
    summ["totals_kg"]["delta_base"] = round(summ["totals_kg"]["after_base"] - summ["totals_kg"]["before_base"], 6)
    summ["totals_t"] = {k: round(v / 1000.0, 6) for k, v in summ["totals_kg"].items()}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "T459_ROUTE_G_DIFF.json").write_text(json.dumps(diff, indent=1), encoding="utf-8")
    (out / "T459_ROUTE_G_SUMMARY.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    return summ


def candidate_binding():
    """the candidate lines that carry a route G lap convention (V3.0.16 extract, T-297) and the later integration
    steps that touch route G column / continuous-beam steel."""
    d = json.loads(EXTRACT.read_text(encoding="utf-8"))
    rows = defaultdict(lambda: {"lines": 0, "with_quantity": 0, "notes_superseded": 0})
    for l in d["lines"]:
        conv = l.get("conventions") or []
        hit = [c for c in LAP_IDS if c in conv]
        if not hit:
            continue
        r = rows[f"{'+'.join(hit)}|{l['evidence_state']}|{l['physical_element']}"]
        r["lines"] += 1
        r["with_quantity"] += l.get("measured_net") is not None or l.get("bounded_range") is not None
        r["notes_superseded"] += "SUPERSEDED" in str(l.get("notes") or "")
    later = {}
    for p in sorted((ROOT / "engine/source").glob("arch_v30*.py")):
        n = p.stem.replace("arch_v30", "")
        if n.isdigit() and int(n) >= 17:
            txt = p.read_text(encoding="utf-8")
            later[p.relative_to(ROOT).as_posix()] = sorted(t for t in TOKENS if t in txt)
    return {"schema": SCHEMA + ":CANDIDATE_BINDING", "extract": EXTRACT.relative_to(ROOT).as_posix(),
            "extract_candidate": d.get("candidate"), "extract_sha256": hashlib.sha256(EXTRACT.read_bytes()).hexdigest(),
            "lap_convention_lines": dict(sorted(rows.items())),
            "lap_convention_lines_with_quantity": sum(r["with_quantity"] for r in rows.values()),
            "later_steps_tokens": later,
            "later_steps_touching": sorted(k for k, v in later.items() if v)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("routeg")
    r.add_argument("structural")
    r.add_argument("--out", required=True)
    c = sub.add_parser("candidate")
    c.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "routeg":
        print(json.dumps({k: v for k, v in instrument_route_g(a.structural, a.out).items() if k != "by_family_storey"},
                         indent=1))
    else:
        rec = candidate_binding()
        if a.write:
            CANDIDATE_JSON.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
