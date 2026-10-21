"""M2 EVALUATION - the generic route on synthetic villas against spec-derived truth (tools/synthetic_villa.py).

    python3 -I tools/m2_evaluate.py OUT.json SEED [SEED ...] [--defects]   (drawings go to a temporary folder)

--defects draws the same designs with drafting noise (tools/synthetic_villa.py DEFECTS); the truth is unchanged.
--hard-defects widens the face-end gaps beyond the snap tolerance: measures whether the loss is REPORTED (risk area)
or silent (silent_missing_m2).

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

GENERIC = ROOT / "engine" / "profiles" / "URBAN_M3_GENERIC_CONVENTIONS_V2.json"


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


def evaluate(seed, work, defects=False):
    t0 = time.perf_counter()
    dxf = SV.generate(work, seed, defects=defects)
    truth = json.loads((Path(work) / f"villa_{seed}.truth.json").read_text())
    prof = json.loads((Path(work) / f"villa_{seed}.profile.json").read_text())
    rec = {"seed": seed, "variant": {k: v for k, v in truth["variant"].items() if k != "layers"},
           "defects_applied": truth.get("defects_applied", {})}
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
    risk_area = sum(r["slab"].get("risk_area_m2", 0.0) for r in D["sheets"].values() if r.get("slab"))
    true_area = sum(t["area"] for t in tc["panels"])
    eng_area = sum(f["area_m2"] for f in pan)
    rec["slab_area"] = {"truth_m2": round(true_area, 3), "engine_panel_m2": round(eng_area, 3),
                        "risk_m2": round(risk_area, 3),
                        "missing_m2": round(max(0.0, true_area - eng_area), 3),
                        "silent_missing_m2": round(max(0.0, true_area - eng_area - risk_area), 3)}
    rec["detect_panels"] = {"true": len(tc["panels"]), "pred": len(pan), "matched": hit,
                            "recall": hit / len(tc["panels"]) if tc["panels"] else None,
                            "precision": min(hit, len(pan)) / len(pan) if pan else None}
    # range sanity: no provisional item's high may exceed twice its base without a named reason (a polluted range is
    # invisible to a base-only comparison - M2 synthetic-demo finding)
    rec["range_ratio_max"] = {}
    for i in items:
        if i["category"] == "PROVISIONAL" and i["base"]:
            k = f"{i['trade']}:{i['family']}"
            rec["range_ratio_max"][k] = round(max(rec["range_ratio_max"].get(k, 0.0), i["high"] / i["base"]), 4)
    cnt = {}
    for i in items:
        cnt[i["category"]] = cnt.get(i["category"], 0) + 1
    rec["categories"] = cnt
    rec["coverage_risk"] = len(risk)
    rk = {}
    for x in risk:
        rk[x["KIND"]] = rk.get(x["KIND"], 0) + 1
    rec["coverage_risk_kinds"] = rk
    slab_flags = sum(v for k, v in rk.items() if k in ("SLAB_UNENCLOSED_BAND_SIDE", "SLAB_OPEN_BOUNDARY_FACE",
                                                        "HEAL_EXTEND_WIDE") or k.startswith("CELL_"))
    rec["slab_area"]["loss_reported"] = rec["slab_area"]["missing_m2"] <= 1.0 or slab_flags > 0
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
    out["slab_area"] = {k: round(sum(r["slab_area"][k] for r in ok), 3) for k in
                        ("truth_m2", "engine_panel_m2", "risk_m2", "missing_m2", "silent_missing_m2")}
    out["slab_loss_unreported_drawings"] = sum(1 for r in ok if not r["slab_area"]["loss_reported"])
    out["range_ratio_max"] = {}
    for r in ok:
        for k, v in r.get("range_ratio_max", {}).items():
            out["range_ratio_max"][k] = max(out["range_ratio_max"].get(k, 0.0), v)
    out["mean_seconds"] = round(sum(r["seconds"] for r in ok) / max(1, len(ok)), 3)
    return out


def main(argv):
    defects = "hard" if "--hard-defects" in argv else ("--defects" in argv)
    argv = [a for a in argv if a not in ("--defects", "--hard-defects")]
    out = Path(argv[0])
    seeds = [int(s) for s in argv[1:]]
    with tempfile.TemporaryDirectory() as td:
        recs = [evaluate(s, td, defects) for s in seeds]
    res = {"seeds": seeds, "defects": defects, "per_drawing": recs, "summary": summarize(recs)}
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res["summary"], indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
