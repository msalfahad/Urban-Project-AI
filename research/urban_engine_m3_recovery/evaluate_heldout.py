"""M3 held-out evaluation: the SAME generated drawings scored by two engines (the M2 engine at its commit, checked out
in a separate worktree, and the current M3 engine), each in its own process so their modules never mix.

    python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py generate --drawings DIR --seeds 501-540 \
            --mode clean|defects|m3
    python3 -I research/urban_engine_m3_recovery/evaluate_heldout.py score --engine-root ROOT --drawings DIR \
            --seeds 501-540 --out OUT.json

The truth is the generator's (tools/synthetic_villa.py, computed from the design, never from a DXF). The seeds were
never used in M1 or M2 development or evaluation. Scoring repeats tools/m2_evaluate.py's measures (detection by
position, quantity error by family, slab area loss reported or silent) on a drawing that already exists.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _seeds(spec):
    out = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def generate(drawings, seeds, mode):
    sys.path.insert(0, str(ROOT))
    from tools import synthetic_villa as SV
    for s in seeds:
        SV.generate(Path(drawings), s, defects=(mode == "defects"), m3=(mode == "m3"))


def _centroid(p):
    a = cx = cy = 0.0
    for i in range(len(p)):
        (x1, y1), (x2, y2) = p[i], p[(i + 1) % len(p)]
        c = x1 * y2 - x2 * y1
        a, cx, cy = a + c, cx + (x1 + x2) * c, cy + (y1 + y2) * c
    return (sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p)) if abs(a) < 1e-12 else \
        (cx / (3 * a), cy / (3 * a))


def _match(pred, true, tol):
    used, hit = set(), 0
    for t in true:
        best = None
        for k, p in enumerate(pred):
            if k not in used and math.dist(p, t) <= tol and (best is None or math.dist(p, t) < best[0]):
                best = (math.dist(p, t), k)
        if best:
            used.add(best[1])
            hit += 1
    return {"true": len(true), "pred": len(pred), "matched": hit}


def score(engine_root, drawings, seeds):
    sys.path.insert(0, str(engine_root))
    from engine.source import generic_route as GR
    from engine.source import member_detection as MD
    from engine.source import provisional_estimate as PE
    from tools import urban_intake as UI
    gen = engine_root / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json"
    gen = gen if gen.exists() else engine_root / "engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json"
    out = []
    for s in seeds:
        dxf = Path(drawings) / f"villa_{s}.dxf"
        truth = json.loads((Path(drawings) / f"villa_{s}.truth.json").read_text())
        prof = json.loads((Path(drawings) / f"villa_{s}.profile.json").read_text())
        rec = {"seed": s, "defects_applied": truth.get("defects_applied", {})}
        t0 = time.perf_counter()
        try:
            I = UI.read(dxf)
            D = GR.detect(I)
            conv = GR.merge_conventions(json.loads(gen.read_text()), prof)
            items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
            PE.check(items, conv)
        except Exception as e:                                               # noqa: BLE001 - reported as failure
            out.append(dict(rec, ok=False, error=f"{type(e).__name__}: {e}"))
            continue
        rec.update(ok=True, seconds=round(time.perf_counter() - t0, 3))
        u = D["unit_m"]

        def base(fam, trade="CONCRETE", filt=None):
            return sum(i["base"] for i in items if i["family"] == fam and i["trade"] == trade and
                       i["category"] == "PROVISIONAL" and (filt is None or filt(i)))
        q = truth["quantities"]
        fam = {"FOOTINGS": (base("FOOTINGS"), q["FOOTINGS"]), "COLUMNS": (base("COLUMNS"), q["COLUMNS"]),
               "BEAMS_TOTAL_DEPTH": (base("BEAMS"), q["BEAMS_TOTAL_DEPTH"]), "SLABS": (base("SLABS"), q["SLABS"]),
               "STEEL_FOOTINGS": (base("FOOTINGS", "REINFORCEMENT"), q["STEEL_FOOTINGS"]),
               "STEEL_BEAMS": (base("BEAMS", "REINFORCEMENT"), q["STEEL_BEAMS"])}
        rec["quantities"] = {k: {"engine": round(e, 6), "truth": round(t, 6),
                                 "error": round((e - t) / t, 6) if t else None} for k, (e, t) in fam.items()}
        tc = truth["component_list"]
        beams_p = [_centroid(b["polygon"]) for r in D["sheets"].values() for b in r.get("beams", [])
                   if b["state"] == "BOUND"]
        rec["detect_beams"] = _match(beams_p, [tuple(b["at"]) for b in tc["beams"] if b["in_schedule"]], 0.3 / u)
        pan = [f for r in D["sheets"].values() if r.get("slab") for f in r["slab"]["faces"] if f["class"] == "PANEL"]
        hit = sum(1 for t in tc["panels"] if any(MD.point_in_poly(t["at"][0], t["at"][1], f["polygon"]) for f in pan))
        rec["detect_panels"] = {"true": len(tc["panels"]), "pred": len(pan), "matched": hit}
        rec["footing_records"] = len([f for r in D["sheets"].values() for f in r.get("footings", [])
                                      if f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY",
                                                            "NESTED_OR_DUPLICATE_OUTLINE")])
        rec["footings_true"] = len(tc["footings"])
        rec["unresolved"] = sum(1 for i in items if i["category"] == "UNRESOLVED")
        out.append(rec)
    return out


def summarize(recs):
    ok = [r for r in recs if r.get("ok")]
    keys = sorted({k for r in ok for k in r["quantities"]})
    res = {"drawings": len(recs), "end_to_end_success": len(ok),
           "failures": [{"seed": r["seed"], "error": r["error"]} for r in recs if not r.get("ok")]}
    res["mean_abs_error"] = {k: round(sum(abs(r["quantities"][k]["error"] or 0) for r in ok) / max(1, len(ok)), 6)
                             for k in keys}
    res["max_abs_error"] = {k: round(max([abs(r["quantities"][k]["error"] or 0) for r in ok] or [0]), 6)
                            for k in keys}
    res["within_1pct"] = {k: sum(1 for r in ok if abs(r["quantities"][k]["error"] or 0) <= 0.01) for k in keys}
    for d in ("detect_beams", "detect_panels"):
        m, t, p = (sum(r[d][x] for r in ok) for x in ("matched", "true", "pred"))
        res[d] = {"recall": round(m / t, 4) if t else None, "precision": round(min(m, p) / p, 4) if p else None,
                  "matched": m, "true": t, "pred": p}
    res["footings"] = {"records": sum(r["footing_records"] for r in ok), "true": sum(r["footings_true"] for r in ok)}
    res["unresolved_items"] = sum(r["unresolved"] for r in ok)
    res["mean_seconds"] = round(sum(r["seconds"] for r in ok) / max(1, len(ok)), 3)
    return res


def main(argv):
    cmd = argv[0]
    a = dict(zip(argv[1::2], argv[2::2]))
    seeds = _seeds(a["--seeds"])
    if cmd == "generate":
        generate(a["--drawings"], seeds, a.get("--mode", "clean"))
        return 0
    recs = score(Path(a["--engine-root"]).resolve(), a["--drawings"], seeds)
    res = {"engine_root": Path(a["--engine-root"]).name, "seeds": a["--seeds"], "per_drawing": recs,
           "summary": summarize(recs)}
    Path(a["--out"]).write_text(json.dumps(res, indent=1))
    print(json.dumps(res["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
