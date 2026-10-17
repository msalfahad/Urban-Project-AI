"""M8 SCOPE EVALUATION - every scope element a synthetic villa draws (tools/synthetic_villa_m8), measured or bounded by
route G + completeness + scope_quantities (conventions V6), against the element's design truth.

    python3 -I tools/m8_evaluate.py OUT.json SEED [SEED ...] [--heldout-vocabulary] [--hard] [--conventions C.json]

Per drawn element (pool, lift pit, pit in a footing, roof tank, dome, stair flight, sunken outline, boundary wall,
unknown outline):
  detected     a completeness finding, a scope item or a route stair item lies on the element (same storey, boxes
               within 0.6 m)
  outcome      MEASURED (a PROVISIONAL item of the element's family), MEASURED_OTHER_FAMILY, BOUNDED (an exposure
               range only), MISSED
  in_range     truth inside [low - 1 %, high + 1 %] of what the engine holds for the element (measured items' low /
               high plus the bounds' low / high); a truth range (a stair flight's bay: landing or void) overlaps it
  base error   (base - truth) / truth for a measured element, split by printed / convention dimensions
The core families (footings, columns, beams, slabs) of the same drawings are scored by tools/m7_evaluate's design
truth (tools/m7_evaluate.design_truth), so that the M7 rows can be compared V5 / V6 on identical inputs; the villa's
whole RC truth (core design + every scope element) is checked against the bounded total (BOQ section F).
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

from engine.source import concrete_completeness as CC   # noqa: E402
from tools import m7_evaluate as M7E                      # noqa: E402
from tools import synthetic_villa_m8 as SM8               # noqa: E402
from tools import urban_boq_m2 as CLI                     # noqa: E402

CONVENTIONS = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
TOL = 0.6
STOREY_OF = {"FOUNDATION": ("FOUNDATION", "GROUND"), "GF": ("GF",), "1F": ("1F",), "2F": ("2F",)}


def _touch(a, b, tol=TOL):
    return a[0] - tol <= b[2] and b[0] - tol <= a[2] and a[1] - tol <= b[3] and b[1] - tol <= a[3]


def engine_records(R):
    """every located engine record: scope items and bounds by their finding's box, route stair items by their zone."""
    g = R["generic"]
    D, u = g["D"], g["D"]["unit_m"]
    scope = g.get("scope") or {}
    fbox = {f["FINDING_ID"]: f for f in (scope.get("findings") or g["completeness"]["findings"])}
    out = []
    for it in R["items"]:
        if it["trade"] != "CONCRETE" or it["category"] == "UNRESOLVED":
            continue
        cid = it["component_id"]
        if cid.startswith("SCOPE:"):
            fid = cid.split(":")[3]
            f = fbox.get(fid)
            if f and f.get("BOX_M"):
                out.append({"src": "SCOPE_ITEM", "family": it["family"], "storey": f["STOREY"], "box": f["BOX_M"],
                            "low": it["low"], "base": it["base"], "high": it["high"], "id": it["item_id"],
                            "assumptions": it["assumptions"], "finding": fid})
        elif it["family"] == "STAIRS" and cid.startswith("STAIRS:"):
            face = cid.split(":")[-1]
            for sid, rec in D["sheets"].items():
                for fc in ((rec.get("slab") or {}).get("faces") or []):
                    if fc["face_id"] == face:
                        org = rec["sheet"].get("origin") or (0.0, 0.0)
                        out.append({"src": "ROUTE_STAIR", "family": "STAIRS", "storey": it["storey"],
                                    "box": CC._local_box(CC._bbox(fc["polygon"]), org, u), "low": it["low"],
                                    "base": it["base"], "high": it["high"], "id": it["item_id"],
                                    "assumptions": it["assumptions"]})
    for b in scope.get("bounds") or []:
        if b["SCOPE_STATE"] != "BOUNDED":
            continue
        f = fbox.get(b["FINDING_ID"])
        if f and f.get("BOX_M"):
            out.append({"src": "BOUND", "family": b["FAMILY"], "storey": b["STOREY"], "box": f["BOX_M"],
                        "low": b["LOW_M3"], "base": None, "high": b["HIGH_M3"], "id": b["FINDING_ID"],
                        "rule": b["RULE"]})
    return out


def _area(b):
    return max(b[2] - b[0], 1e-6) * max(b[3] - b[1], 1e-6)


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy / (_area(a) + _area(b) - ix * iy)


def _inside(a, b, tol=TOL):
    return b[0] - tol <= a[0] and a[2] <= b[2] + tol and b[1] - tol <= a[1] and a[3] <= b[3] + tol


def _matches(el, r):
    """a record is the element's when it lies on it: the same family touching it, or a record of another family that
    overlaps it (IoU >= 0.25) or nests with it at a comparable size (never a plot-long strip beside a small element)."""
    a, b = el["box"], r["box"]
    if not _touch(a, b):
        return False
    if r["family"] == el["family"]:
        return True
    return _iou(a, b) >= 0.25 or (_inside(b, a) and _area(b) >= 0.25 * _area(a)) or \
        (_inside(a, b) and _area(a) >= 0.25 * _area(b))


def assign(elements, recs):
    """each record to the one element it matches best (highest IoU, then the same family, then the nearest centre):
    two neighbouring elements never share a record."""
    out = defaultdict(list)
    for k, r in enumerate(recs):
        cand = [el for el in elements if r["box"] and r["storey"] in STOREY_OF.get(el["sheet"], (el["sheet"],))
                and _matches(el, r)]
        if not cand:
            continue
        cx, cy = (r["box"][0] + r["box"][2]) / 2, (r["box"][1] + r["box"][3]) / 2

        def key(el):
            b = el["box"]
            return (-round(_iou(b, r["box"]), 3), -(el["family"] == r["family"]),
                    (cx - (b[0] + b[2]) / 2) ** 2 + (cy - (b[1] + b[3]) / 2) ** 2)
        out[min(cand, key=key)["id"]].append(k)
    return out


def score_element(el, recs, findings, mine=None):
    st = STOREY_OF.get(el["sheet"], (el["sheet"],))
    here = [recs[k] for k in mine] if mine is not None else \
        [r for r in recs if r["storey"] in st and r["box"] and _matches(el, r)]
    det = here or [f for f in findings if f.get("BOX_M") and f["STOREY"] in st and _touch(el["box"], f["BOX_M"])]
    meas = [r for r in here if r["base"] is not None]
    fam = el["family"]
    right = [r for r in meas if r["family"] == fam]
    bnd = [r for r in here if r["base"] is None]
    if right:
        outcome = "MEASURED"
    elif meas:
        outcome = "MEASURED_OTHER_FAMILY"
    elif bnd:
        outcome = "BOUNDED"
    else:
        outcome = "MISSED" if not det else "DETECTED_NO_RANGE"
    lo = sum(r["low"] for r in meas) + sum(r["low"] for r in bnd)
    hi = sum(r["high"] for r in meas) + sum(r["high"] for r in bnd)
    base = sum(r["base"] for r in right) if right else None
    t = el["truth_m3"]
    t_hi = el.get("truth_high_m3") or t
    tol = max(0.01 * t, 0.001)
    rec = {"id": el["id"], "kind": el["kind"], "family": fam, "sheet": el["sheet"], "printed": el["printed"],
           "truth_m3": t, "design": el["design"], "detected": bool(det), "outcome": outcome,
           "engine_low_m3": round(lo, 4), "engine_base_m3": None if base is None else round(base, 4),
           "truth_high_m3": t_hi, "engine_high_m3": round(hi, 4),
           "in_range": bool(here) and lo - tol <= t_hi and t - tol <= hi + tol,
           "base_error_rel": None if base is None or not t else round(
               0.0 if t - tol <= base <= t_hi + tol else (base - t) / t if base < t else (base - t_hi) / t_hi, 4),
           "records": [{k: r.get(k) for k in ("src", "family", "id", "rule")} for r in here]}
    return rec


def evaluate(seed, work, *, vocabulary="dev", hard=False, conventions=CONVENTIONS, core_v5=True):
    t0 = time.perf_counter()
    rec = {"seed": seed, "vocabulary": vocabulary, "hard": bool(hard), "ok": False}
    try:
        dxf = SM8.generate(work, seed, vocabulary=vocabulary, hard=hard)
        T = json.loads((Path(work) / f"villa_m8_{seed}.truth.json").read_text(encoding="utf-8"))
        prof = Path(work) / f"villa_m8_{seed}.profile.json"
        R = CLI.compute([str(dxf)], profile=str(prof), route="G", conventions=str(ROOT / conventions),
                        completeness=True)
        R5 = CLI.compute([str(dxf)], profile=str(prof), route="G", conventions=str(ROOT / M7E.CONVENTIONS),
                         completeness=True) if core_v5 else None
    except Exception as e:                                      # a crash is a result, never hidden
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    recs = engine_records(R)
    findings = (R["generic"].get("scope") or {}).get("findings") or R["generic"]["completeness"]["findings"]
    asg = assign(T["m8"]["elements"], recs)
    els = [score_element(el, recs, findings, asg.get(el["id"], [])) for el in T["m8"]["elements"]]
    core = {}
    for tag, RR in (("V6", R), ("V5", R5)):
        if RR is None:
            continue
        reading = RR["conv"].base("BEAM_DEPTH_READING") if "BEAM_DEPTH_READING" in RR["conv"].items else \
            "TOTAL_DEPTH"
        truth, amb = M7E.design_truth(seed, T, reading)
        prov, lo, hi, _ = M7E.engine_quantities(RR["items"])
        core[tag] = {f"{k[0]}|{k[1]}": {"truth": round(truth.get(k, 0.0), 4), "engine": round(prov.get(k, 0.0), 4),
                                        "exp_high": round(hi.get(k, 0.0), 4)} for k in sorted(set(truth) | set(prov))}
    sc = R["generic"].get("scope") or {}
    villa = None
    T6 = (sc.get("totals") or {}).get("RC")
    if T6 and "V6" in core:
        # the villa's whole RC truth (core design + every scope element; a stair bay's slab or void) against the
        # bounded total
        ct = sum(v["truth"] for v in core["V6"].values())
        amb = M7E.design_truth(seed, T, R["conv"].base("BEAM_DEPTH_READING") if "BEAM_DEPTH_READING" in
                               R["conv"].items else "TOTAL_DEPTH")[1]
        lo = ct - sum(amb.values()) + sum(e["truth_m3"] for e in T["m8"]["elements"])
        hi = ct + sum(e.get("truth_high_m3") or e["truth_m3"] for e in T["m8"]["elements"])
        villa = {"truth_low_m3": round(lo, 3), "truth_high_m3": round(hi, 3), "measured_base_m3": T6["measured_base"],
                 "bounded_low_m3": T6["bounded_low"], "bounded_high_m3": T6["bounded_high"],
                 "truth_in_bounded": T6["bounded_low"] - 0.01 * lo <= hi and lo <= T6["bounded_high"] * 1.01}
    rec.update(ok=True, seconds=round(time.perf_counter() - t0, 2), elements=els, core=core, villa=villa,
               totals=sc.get("totals"), variant=T["m6"]["variant"],
               findings_without_range=(sc.get("totals") or {}).get("findings_without_range"),
               conventions=Path(conventions).name)
    return rec


def summarise(recs):
    ok = [r for r in recs if r.get("ok")]
    by = defaultdict(Counter)
    err = defaultdict(lambda: {"printed": [], "convention": []})
    width = defaultdict(list)                     # engine high / truth: how wide the range is (a bound from 0 is easy)
    for r in ok:
        for e in r["elements"]:
            k = e["kind"]
            by[k]["n"] += 1
            by[k]["detected"] += e["detected"]
            by[k][e["outcome"]] += 1
            by[k]["in_range"] += e["in_range"]
            if e["base_error_rel"] is not None:
                err[k]["printed" if e["printed"] else "convention"].append(abs(e["base_error_rel"]))
            if e["truth_m3"] and e["engine_high_m3"]:
                width[k].append(e["engine_high_m3"] / e["truth_m3"])

    def med(xs):
        xs = sorted(xs)
        return None if not xs else round(xs[len(xs) // 2], 4)
    fam = {}
    for k, c in sorted(by.items()):
        n = c["n"]
        fam[k] = {"n": n, "detected_pct": round(100 * c["detected"] / n, 1), "in_range_pct": round(100 *
                                                                                                c["in_range"] / n, 1),
                  "outcomes": {o: c[o] for o in ("MEASURED", "MEASURED_OTHER_FAMILY", "BOUNDED", "DETECTED_NO_RANGE",
                                                 "MISSED") if c[o]},
                  "median_abs_base_error_printed": med(err[k]["printed"]),
                  "median_abs_base_error_convention": med(err[k]["convention"]),
                  "n_measured_printed": len(err[k]["printed"]), "n_measured_convention": len(err[k]["convention"]),
                  "median_high_over_truth": med(width[k])}
    core_moves = []
    for r in ok:
        c5, c6 = r["core"].get("V5"), r["core"].get("V6")
        if not (c5 and c6):
            continue
        for k in sorted(set(c5) | set(c6)):
            a, b = c5.get(k, {}), c6.get(k, {})
            if abs((a.get("engine") or 0) - (b.get("engine") or 0)) > 1e-6:
                core_moves.append({"seed": r["seed"], "row": k, "V5": a.get("engine"), "V6": b.get("engine"),
                                   "truth": b.get("truth") or a.get("truth")})
    vil = [r["villa"] for r in ok if r.get("villa")]
    villa = {"n": len(vil), "truth_in_bounded": sum(1 for v in vil if v["truth_in_bounded"]),
             "median_bounded_high_over_truth_high": med([v["bounded_high_m3"] / v["truth_high_m3"] for v in vil]),
             "median_bounded_low_over_truth_low": med([v["bounded_low_m3"] / v["truth_low_m3"] for v in vil]),
             "median_measured_over_truth_low": med([v["measured_base_m3"] / v["truth_low_m3"] for v in vil])}
    return {"drawings": len(recs), "crashed": [(r["seed"], r.get("error")) for r in recs if not r.get("ok")],
            "by_kind": fam, "villa_total": villa, "core_rows_moved_v5_to_v6": core_moves,
            "findings_without_range": sum(r.get("findings_without_range") or 0 for r in ok)}


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
            recs.append(evaluate(sd, td, vocabulary="heldout" if "--heldout-vocabulary" in argv else "dev",
                                 hard="--hard" in argv, conventions=conv))
    res = {"summary": summarise(recs), "drawings": recs}
    Path(out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    s = res["summary"]
    print(json.dumps({k: s[k] for k in ("drawings", "crashed", "by_kind", "villa_total", "findings_without_range")},
                     indent=1))
    print("core rows moved V5 -> V6:", len(s["core_rows_moved_v5_to_v6"]))


if __name__ == "__main__":
    main(sys.argv[1:])
