"""M2 EVALUATION - the generic route on synthetic villas against spec-derived truth (tools/synthetic_villa.py).

    python3 -I tools/m2_evaluate.py OUT.json SEED [SEED ...]       (drawings are generated into a temporary folder)

Per drawing: runtime, components detected, detection precision / recall by position (footings, beams, slab panels),
quantity error by family (concrete and steel), unresolved / exception counts, end-to-end success. The truth never
comes from the engine: it is computed from the design by the generator.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import generic_route as GR            # noqa: E402
from engine.source import member_detection as MD         # noqa: E402
from engine.source import provisional_estimate as PE     # noqa: E402
from tools import synthetic_villa as SV                  # noqa: E402
from tools import urban_intake as UI                     # noqa: E402

GENERIC = ROOT / "engine" / "profiles" / "URBAN_M2_GENERIC_CONVENTIONS_V1.json"


def _centroid(p):
    a = cx = cy = 0.0
    for i in range(len(p)):
        (x1, y1), (x2, y2) = p[i], p[(i + 1) % len(p)]
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if abs(a) < 1e-12:
        return (sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p))
    return (cx / (3 * a), cy / (3 * a))


def _match(pred, true, tol):
    used, hit = set(), 0
    for t in true:
        best = None
        for k, p in enumerate(pred):
            if k in used:
                continue
            d = math.dist(p, t)
            if d <= tol and (best is None or d < best[0]):
                best = (d, k)
        if best:
            used.add(best[1])
            hit += 1
    return {"true": len(true), "pred": len(pred), "matched": hit,
            "recall": hit / len(true) if true else None, "precision": hit / len(pred) if pred else None}


def err(eng, tru):
    return None if not tru else (eng - tru) / tru


def evaluate(seed, work):
    t0 = time.perf_counter()
    dxf = SV.generate(work, seed)
    truth = json.loads((Path(work) / f"villa_{seed}.truth.json").read_text())
    prof = json.loads((Path(work) / f"villa_{seed}.profile.json").read_text())
    rec = {"seed": seed, "variant": {k: v for k, v in truth["variant"].items() if k != "layers"}}
    try:
        I = UI.read(dxf)
        D = GR.detect(I)
        conv = GR.merge_conventions(json.loads(GENERIC.read_text()), prof)
        items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
        PE.check(items, conv)
        convB = GR.merge_conventions(json.loads(GENERIC.read_text()), prof)
        convB = PE.Conventions({"set": "B", "conventions": [dict(c, base="BELOW_SLAB") if c["id"] ==
                                                            "BEAM_DEPTH_READING" else c for c in convB.items.values()]})
        itemsB, _, _ = GR.items_from(D, convB, GR.storey_heights(convB))
        rec["ok"] = True
    except Exception as e:                                                       # noqa: BLE001 - reported as failure
        rec.update(ok=False, error=f"{type(e).__name__}: {e}", seconds=round(time.perf_counter() - t0, 3))
        return rec
    rec["seconds"] = round(time.perf_counter() - t0, 3)
    u = D["unit_m"]

    def base(fam, trade="CONCRETE", items_=items, filt=None):
        return sum(i["base"] for i in items_ if i["family"] == fam and i["trade"] == trade and i["category"] ==
                   "PROVISIONAL" and (filt is None or filt(i)))
    q = truth["quantities"]
    fam = {
        "FOOTINGS": (base("FOOTINGS"), q["FOOTINGS"]),
        "COLUMNS": (base("COLUMNS"), q["COLUMNS"]),
        "BEAMS_TOTAL_DEPTH": (base("BEAMS"), q["BEAMS_TOTAL_DEPTH"]),
        "BEAMS_BELOW_SLAB": (base("BEAMS", items_=itemsB), q["BEAMS_BELOW_SLAB"]),
        "SLABS": (base("SLABS"), q["SLABS"]),
        "STEEL_FOOTINGS": (base("FOOTINGS", "REINFORCEMENT"), q["STEEL_FOOTINGS"]),
        "STEEL_COLUMNS_MAIN": (base("COLUMNS", "REINFORCEMENT", filt=lambda i: ":MAIN:" in i["item_id"]),
                               q["STEEL_COLUMNS_MAIN"]),
        "STEEL_BEAMS": (base("BEAMS", "REINFORCEMENT"), q["STEEL_BEAMS"]),
    }
    rec["quantities"] = {k: {"engine": round(e, 6), "truth": round(t, 6), "error": None if err(e, t) is None
                             else round(err(e, t), 6)} for k, (e, t) in fam.items()}
    tc = truth["component_list"]
    ftg = [((f["box"][0] + f["box"][2]) / 2, (f["box"][1] + f["box"][3]) / 2)
           for r in D["sheets"].values() for f in r.get("footings", []) if f.get("box") and
           f["state"] in ("CONFIRMED", "TYPE_BY_SIZE_MATCH", "SIZE_MISMATCH")]
    rec["detect_footings"] = _match(ftg, [tuple(f["at"]) for f in tc["footings"]], 0.15 / u)
    beams_p = []
    for r in D["sheets"].values():
        for b in r.get("beams", []):
            if b["state"] == "BOUND":
                beams_p.append(_centroid(b["polygon"]))
    tb = [tuple(b["at"]) for b in tc["beams"] if b["in_schedule"]]
    rec["detect_beams"] = _match(beams_p, tb, 0.3 / u)
    pan = []
    for r in D["sheets"].values():
        if r.get("slab"):
            pan += [f for f in r["slab"]["faces"] if f["class"] == "PANEL"]
    hit = sum(1 for t in tc["panels"] if any(MD.point_in_poly(t["at"][0], t["at"][1], f["polygon"]) for f in pan))
    rec["detect_panels"] = {"true": len(tc["panels"]), "pred": len(pan), "matched": hit,
                            "recall": hit / len(tc["panels"]) if tc["panels"] else None,
                            "precision": min(hit, len(pan)) / len(pan) if pan else None}
    cnt = {}
    for i in items:
        cnt[i["category"]] = cnt.get(i["category"], 0) + 1
    rec["categories"] = cnt
    rec["coverage_risk"] = len(risk)
    rec["rebar_register"] = {s: sum(1 for x in reg if x["REBAR_STATE"] == s) for s in GR.REBAR_STATES}
    rec["manual_inputs"] = prof.get("manual_inputs", 0)
    return rec


def summarize(recs):
    ok = [r for r in recs if r.get("ok")]
    out = {"drawings": len(recs), "end_to_end_success": len(ok), "failures": [r for r in recs if not r.get("ok")]}
    keys = sorted({k for r in ok for k in r["quantities"]})
    out["mean_abs_error"] = {k: round(sum(abs(r["quantities"][k]["error"]) for r in ok
                                          if r["quantities"][k]["error"] is not None) /
                                      max(1, sum(1 for r in ok if r["quantities"][k]["error"] is not None)), 6)
                             for k in keys}
    out["max_abs_error"] = {k: round(max([abs(r["quantities"][k]["error"]) for r in ok
                                          if r["quantities"][k]["error"] is not None] or [0]), 6) for k in keys}
    out["within_5pct"] = {k: sum(1 for r in ok if r["quantities"][k]["error"] is not None and
                                 abs(r["quantities"][k]["error"]) <= 0.05) for k in keys}
    for d in ("detect_footings", "detect_beams", "detect_panels"):
        m = sum(r[d]["matched"] for r in ok)
        t = sum(r[d]["true"] for r in ok)
        p = sum(r[d]["pred"] for r in ok)
        out[d] = {"recall": round(m / t, 4) if t else None, "precision": round(min(m, p) / p, 4) if p else None,
                  "matched": m, "true": t, "pred": p}
    out["mean_seconds"] = round(sum(r["seconds"] for r in ok) / max(1, len(ok)), 3)
    return out


def main(argv):
    out = Path(argv[0])
    seeds = [int(s) for s in argv[1:]]
    with tempfile.TemporaryDirectory() as td:
        recs = [evaluate(s, td) for s in seeds]
    res = {"seeds": seeds, "per_drawing": recs, "summary": summarize(recs)}
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res["summary"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
