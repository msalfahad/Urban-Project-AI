"""M7 QUANTITY EVALUATION - route G quantities on CLUTTERED synthetic villas (tools/synthetic_villa_m6: the M2 frame
plus every completeness case, distractors and drafting noise) against the design the generator drew.

    python3 -I tools/m7_evaluate.py OUT.json SEED [SEED ...] [--mixed] [--hard] [--heldout-vocabulary] [--v2-cases]
                                    [--clean] [--conventions C.json]

The M2 evaluator (tools/m2_evaluate) scores clean villas; there the route is exact. Here everything a real drawing
adds - plot lines, walls, pools, pits, tanks, domes, stairs, sunken outlines, hatches, stray labels, extra schedule
rows, a missing column outline, a missing or a copied storey - is drawn on top, and the core families must still be
right or visibly unresolved. Per (family, storey):

  truth      FOOTINGS, COLUMNS, BEAMS (the conventions' depth reading), SLABS from the design (tools/synthetic_villa
             truth formulas, split by storey); planted columns are scored apart; a bay holding a drawn stair is
             ambiguous scope: the slab truth is a range (the bay void .. the bay slab); a storey whose plan is left out keeps
             its design truth (the engine must report it, not measure it); a plan copied as another storey makes that
             storey's beams and slab equal to the copied one's
  engine     PROVISIONAL + VERIFIED base; UNRESOLVED exposure low / high
  state      EXACT     |engine - truth| <= 1 % of truth (or 0.001 m3)
             IN_RANGE  inside an ambiguous-scope truth range (a stair bay counted or not)
             REPORTED  engine below truth and engine + unresolved exposure high reaches it, or the completeness pass
                       reports that storey's plan missing
             SILENT    anything else (an over-count is always SILENT)
The truth never reads the engine.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import synthetic_villa as SV            # noqa: E402
from tools import synthetic_villa_m6 as SM6        # noqa: E402
from tools import urban_boq_m2 as CLI              # noqa: E402

CONVENTIONS = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
FAMILIES = ("FOOTINGS", "COLUMNS", "BEAMS", "SLABS")
TOL_REL, TOL_ABS = 0.01, 0.001


def _bay_of(D, box_local):
    """the design bay (i, j) a sheet-local box lies in (local = design + 4 m)."""
    xs, ys = D["xs"], D["ys"]
    cx, cy = (box_local[0] + box_local[2]) / 2 - 4.0, (box_local[1] + box_local[3]) / 2 - 4.0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if xs[i] <= cx <= xs[i + 1] and ys[j] <= cy <= ys[j + 1]:
                return i, j
    return None


def design_truth(seed, T, depth_reading):
    """{(family, storey): m3} from the generator's own truth record, split by storey."""
    D = SV.design(seed)
    q, comp = T["quantities"], T["component_list"]
    m6 = T["m6"]
    hs = {st: D["heights"][st] for st in ("GF", "1F")}
    out = {("FOOTINGS", "FOUNDATION"): q["FOOTINGS"]}
    beams = q["BEAMS_TOTAL_DEPTH"] if depth_reading == "TOTAL_DEPTH" else q["BEAMS_BELOW_SLAB"]
    for st in ("GF", "1F"):
        out[("COLUMNS", st)] = q["COLUMNS"] * hs[st] / sum(hs.values())
        out[("BEAMS", st)] = beams / 2
        out[("SLABS", st)] = sum(p["area"] for p in comp["panels"] if p["storey"] == st) * D["slab_t"][st]
    ambiguous = {}                                   # (family, storey) -> the part that may be void
    for el in m6["elements"]:
        if el["kind"] == "STAIR" and el.get("box"):
            b = _bay_of(D, el["box"])
            st = "GF" if el["sheet"] == "GF" else el["sheet"]
            a = sum(p["area"] for p in comp["panels"] if p["storey"] == st and (p["i"], p["j"]) == b)
            if a:
                ambiguous[("SLABS", st)] = ambiguous.get(("SLABS", st), 0.0) + a * D["slab_t"][st]
    # a planted column drawn on the plan above stands under that plan's beam: the beam is measured face to face of it
    # (the column owns its footprint), which the frame's design truth does not know
    rows = {r["mark"]: r for r in SV.schedule_rows(D)["BEAM"]}
    for el in m6["elements"]:
        if el["kind"] == "PLANTED_COLUMN" and el.get("box_above"):
            mx, my = el["box"][0] + 0.3 - 4.0, el["box"][1] + 0.3 - 4.0
            bm = next((b for b in SV.beams_of(D) if abs(b["mid_design"][0] - mx) < 1e-6 and
                       abs(b["mid_design"][1] - my) < 1e-6), None)
            sb = rows.get(bm["type"]) if bm else None
            if sb:
                a_, b_ = el["section_cm"]
                along = (a_ if bm["axis"] == "x" else b_) / 100.0
                H = sb["H"] if depth_reading == "TOTAL_DEPTH" else sb["H"] + D["slab_t"]["1F"]
                out[("BEAMS", "1F")] -= along * sb["B"] * H
    if m6["variant"].get("extra_storey"):
        out[("BEAMS", "2F")] = out[("BEAMS", "1F")]
        out[("SLABS", "2F")] = out[("SLABS", "1F")]
    return out, ambiguous


def engine_quantities(items):
    prov, exp_lo, exp_hi, planted = defaultdict(float), defaultdict(float), defaultdict(float), 0.0
    for i in items:
        if i["trade"] != "CONCRETE":
            continue
        fam = {"GROUND_SLAB": "SLABS"}.get(i["family"], i["family"])
        if fam not in FAMILIES:
            continue
        k = (fam, i.get("storey"))
        if fam == "COLUMNS" and "PC@" in (i.get("component_id") or ""):
            planted += i.get("base") or 0.0
            continue
        if i["category"] in ("PROVISIONAL", "VERIFIED"):
            prov[k] += i.get("base") or 0.0
        elif i["category"] == "UNRESOLVED":
            exp_lo[k] += i.get("exposure_low") or 0.0
            exp_hi[k] += i.get("exposure_high") or 0.0
    return prov, exp_lo, exp_hi, planted


def evaluate(seed, work, *, defects=False, vocabulary="dev", hard=False, m6v2=False, conventions=CONVENTIONS,
             clean=False):
    """clean: the plain M2 villa (no completeness case drawn) - the regression check of the same truth."""
    t0 = time.perf_counter()
    rec = {"seed": seed, "defects": bool(defects), "vocabulary": vocabulary, "hard": bool(hard), "m6v2": bool(m6v2),
           "clean": bool(clean), "ok": False}
    try:
        if clean:
            dxf = SV.generate(work, seed, defects=defects)
            T = json.loads((Path(work) / f"villa_{seed}.truth.json").read_text(encoding="utf-8"))
            T["m6"] = {"elements": [], "variant": {}}
            prof = Path(work) / f"villa_{seed}.profile.json"
        else:
            dxf = SM6.generate(work, seed, defects=defects, vocabulary=vocabulary, hard=hard, m6v2=m6v2)
            T = json.loads((Path(work) / f"villa_m6_{seed}.truth.json").read_text(encoding="utf-8"))
            prof = Path(work) / f"villa_m6_{seed}.profile.json"
        R = CLI.compute([str(dxf)], profile=str(prof), route="G", conventions=str(ROOT / conventions),
                        completeness=True)
    except Exception as e:                                    # a crash is a result, never hidden
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    reading = R["conv"].base("BEAM_DEPTH_READING") if "BEAM_DEPTH_READING" in R["conv"].items else "TOTAL_DEPTH"
    truth, ambiguous = design_truth(seed, T, reading)
    prov, lo, hi, planted = engine_quantities(R["items"])
    missing = {f["STOREY"] for f in R["generic"]["completeness"]["findings"] if f["KIND"] == "STOREY_PLAN_MISSING"}
    rows = []
    for k in sorted(set(truth) | set(prov)):
        t, e = truth.get(k, 0.0), prov.get(k, 0.0)
        t_lo = t - ambiguous.get(k, 0.0)
        tol = max(TOL_REL * abs(t), TOL_ABS)
        err = e - t
        if abs(err) <= tol:
            st = "EXACT"
        elif k in ambiguous and t_lo - tol <= e <= t + tol:
            st = "IN_RANGE"
        elif e < t_lo and (e + hi.get(k, 0.0) >= t_lo - tol or k[1] in missing):
            st = "REPORTED"
        elif k in ambiguous and e < t and e + hi.get(k, 0.0) >= t_lo - tol:
            st = "REPORTED"
        elif err < 0 and not (k in ambiguous) and (e + hi.get(k, 0.0) >= t - tol or k[1] in missing):
            st = "REPORTED"
        else:
            st = "SILENT"
        rows.append({"family": k[0], "storey": k[1], "truth_m3": round(t, 4), "truth_low_m3": round(t_lo, 4),
                     "engine_m3": round(e, 4),
                     "error_m3": round(err, 4), "error_rel": round(err / t, 4) if t else None,
                     "unresolved_low_m3": round(lo.get(k, 0.0), 4), "unresolved_high_m3": round(hi.get(k, 0.0), 4),
                     "state": st})
    rec.update(ok=True, seconds=round(time.perf_counter() - t0, 2), rows=rows, planted_columns_m3=round(planted, 4),
               ambiguous_m3={f"{k[0]}|{k[1]}": round(v, 4) for k, v in ambiguous.items()},
               elements=[e["kind"] for e in T["m6"]["elements"]], variant=T["m6"]["variant"],
               conventions=Path(conventions).name)
    return rec


def summarise(recs):
    ok = [r for r in recs if r.get("ok")]
    by = defaultdict(Counter)
    err = defaultdict(float)
    tru = defaultdict(float)
    silent = []
    for r in ok:
        for x in r["rows"]:
            by[x["family"]][x["state"]] += 1
            err[x["family"]] += abs(x["error_m3"]) if x["state"] == "SILENT" else 0.0
            tru[x["family"]] += x["truth_m3"]
            if x["state"] == "SILENT":
                silent.append({"seed": r["seed"], **x, "elements": r["elements"]})
    return {"drawings": len(recs), "crashed": [(r["seed"], r.get("error")) for r in recs if not r.get("ok")],
            "states_by_family": {k: dict(v) for k, v in sorted(by.items())},
            "silent_rows": len(silent), "silent_abs_m3_by_family": {k: round(v, 3) for k, v in sorted(err.items())},
            "truth_m3_by_family": {k: round(v, 3) for k, v in sorted(tru.items())}, "silent": silent}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    conv = CONVENTIONS
    if "--conventions" in argv:
        conv = argv[argv.index("--conventions") + 1]
        args = [a for a in args if a != conv]
    out, seeds = args[0], [int(x) for x in args[1:]]
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in seeds:
            recs.append(evaluate(sd, td, defects="--defects" in argv or (sd % 2 == 1 and "--mixed" in argv),
                                 vocabulary="heldout" if "--heldout-vocabulary" in argv else "dev",
                                 hard="--hard" in argv, m6v2="--v2-cases" in argv, conventions=conv,
                                 clean="--clean" in argv))
    res = {"summary": summarise(recs), "drawings": recs}
    Path(out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    s = res["summary"]
    print(json.dumps({k: s[k] for k in ("drawings", "crashed", "states_by_family", "silent_rows",
                                        "silent_abs_m3_by_family")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
