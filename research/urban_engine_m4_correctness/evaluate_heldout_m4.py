"""M4 held-out evaluation: the SAME generated drawings scored by the M3 engine (its commit checked out in a separate
worktree) and the current M4 engine, each in its own process so their modules never mix.

    python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py generate --drawings DIR --seeds 601-640 \
            --mode clean|m3|m4
    python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py score --engine-root ROOT \
            --conventions V2|V3 --drawings DIR --seeds 601-640 --out OUT.json

The truth is the generator's (tools/synthetic_villa.py, from the design, never from a DXF); the seeds 601-640 were
never used before. Besides the family errors of the M3 evaluation, every beam span WITHOUT its own label is scored:
    CORRECT              a section was given and the concrete is the truth (within 2 %)
    WRONG_SECTION        a section was given and it is not the truth's
    UNRESOLVED_COVERS    held unresolved; provisional + exposure range contains the truth
    UNRESOLVED_MISSES    held unresolved; the range does not contain the truth
    MISSED               no band found on the span
precision = CORRECT / (CORRECT + WRONG_SECTION) of the sections the engine assigned to unlabelled spans;
recall = CORRECT / unlabelled spans. Per drawing, the beam concrete truth is also tested against the planning
envelope [provisional base, base + unresolved exposure high] (an engine that holds a span back is right when the
envelope covers the truth; a beam type missing from the schedule is outside the truth and inside the exposure).
Nothing here reads a project file.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHEETS = ["FOUNDATION", "GF", "1F", "SCHED"]


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
        SV.generate(Path(drawings), s, m3=(mode == "m3"), m4=(mode == "m4"))


def _centroid(p):
    return sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p)


def _span_rect(b, st, units):
    """the span between the column faces, in drawing units, widened by 0.05 m: (u0, u1, v0, v1, axis)."""
    s = 1.0 if units == "m" else 1000.0
    n = SHEETS.index(st)
    (ax, ay), (bx, by) = b["a"], b["b"]
    X = lambda x: (n * 45.0 + 4.0 + x) * s                        # noqa: E731
    Y = lambda y: (4.0 + y) * s                                    # noqa: E731
    if b["axis"] == "x":
        return (X(min(ax, bx)), X(max(ax, bx)), Y(ay) - (b["B"] / 2 + 0.05) * s, Y(ay) + (b["B"] / 2 + 0.05) * s, "x")
    return (Y(min(ay, by)), Y(max(ay, by)), X(ax) - (b["B"] / 2 + 0.05) * s, X(ax) + (b["B"] / 2 + 0.05) * s, "y")


def score(engine_root, conventions, drawings, seeds):
    sys.path.insert(0, str(engine_root))
    from engine.source import generic_route as GR
    from engine.source import provisional_estimate as PE
    from tools import urban_intake as UI
    name = {"V2": "URBAN_M3_GENERIC_CONVENTIONS_V2.json", "V3": "URBAN_M4_GENERIC_CONVENTIONS_V3.json"}[conventions]
    gen = json.loads((engine_root / "engine/profiles" / name).read_text())
    out = []
    for s in seeds:
        dxf = Path(drawings) / f"villa_{s}.dxf"
        truth = json.loads((Path(drawings) / f"villa_{s}.truth.json").read_text())
        prof = json.loads((Path(drawings) / f"villa_{s}.profile.json").read_text())
        rec = {"seed": s}
        t0 = time.perf_counter()
        try:
            I = UI.read(dxf)
            conv = GR.merge_conventions(gen, prof)
            D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(conv))
            items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
            PE.check(items, conv)
        except Exception as e:                                               # noqa: BLE001 - reported as failure
            out.append(dict(rec, ok=False, error=f"{type(e).__name__}: {e}"))
            continue
        rec.update(ok=True, seconds=round(time.perf_counter() - t0, 3))
        q = truth["quantities"]

        def base(fam, trade="CONCRETE"):
            return sum(i["base"] for i in items if i["family"] == fam and i["trade"] == trade and
                       i["category"] == "PROVISIONAL")
        fams = {"FOOTINGS": (base("FOOTINGS"), q["FOOTINGS"]), "COLUMNS": (base("COLUMNS"), q["COLUMNS"]),
                "BEAMS_TOTAL_DEPTH": (base("BEAMS"), q["BEAMS_TOTAL_DEPTH"]), "SLABS": (base("SLABS"), q["SLABS"])}
        rec["quantities"] = {k: {"engine": round(e, 6), "truth": round(t, 6), "error": round((e - t) / t, 6)
                                 if t else None} for k, (e, t) in fams.items()}
        conc = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE" and i["family"] == "BEAMS"}
        bands = {st: [(b, _centroid(b["polygon"])) for r in D["sheets"].values() if r["sheet"]["role"] == "SLAB_PLAN"
                      and r["sheet"]["storey"] == st for b in r.get("beams", [])] for st in ("GF", "1F")}
        spans = []
        for b in truth["component_list"]["beams"]:
            if b.get("tagged", True) or b.get("axis") == "arc" or "B" not in b:
                continue
            u0, u1, v0, v1, ax = _span_rect(b, b["storey"], truth["variant"]["units"])
            hit = [bd for bd, (x, y) in bands.get(b["storey"], [])
                   if (u0 <= (x if ax == "x" else y) <= u1 and v0 <= (y if ax == "x" else x) <= v1)]
            tv = b["B"] * b["H"] * b["clear"]
            its = [conc.get(f"BEAMS:{b['storey']}:{bd['band_id']}") for bd in hit]
            its = [i for i in its if i]
            prov = sum(i["base"] for i in its if i["category"] == "PROVISIONAL")
            if not its:
                kind = "MISSED"
            elif all(i["category"] == "PROVISIONAL" for i in its):
                kind = "CORRECT" if abs(prov - tv) <= 0.02 * tv else "WRONG_SECTION"
            else:
                lo = prov + sum(i.get("exposure_low") or 0 for i in its if i["category"] == "UNRESOLVED")
                hi = prov + sum(i.get("exposure_high") or 0 for i in its if i["category"] == "UNRESOLVED")
                kind = "UNRESOLVED_COVERS" if lo - 0.01 * tv <= tv <= hi + 0.01 * tv else "UNRESOLVED_MISSES"
            spans.append({"storey": b["storey"], "type": b["type"], "cb": bool(b.get("cb")), "truth_m3": round(tv, 6),
                          "provisional_m3": round(prov, 6), "outcome": kind})
        rec["unlabelled_spans"] = spans
        rec["cb_concrete"] = {"engine": round(sum(i["base"] for i in items if i["family"] == "BEAMS" and
                                                  i["trade"] == "CONCRETE" and i["category"] == "PROVISIONAL" and
                                                  "CB1" in (i.get("source") or "")), 6),
                              "truth": q.get("CB_CONCRETE")}
        bu = [i for i in items if i["family"] == "BEAMS" and i["trade"] == "CONCRETE" and i["category"] == "UNRESOLVED"]
        b0 = fams["BEAMS_TOTAL_DEPTH"][0]
        rec["beams_range"] = {"low": round(b0, 6), "high": round(b0 + sum(i.get("exposure_high") or 0 for i in bu), 6),
                              "truth": q["BEAMS_TOTAL_DEPTH"], "n_unresolved": len(bu)}
        rec["unresolved"] = sum(1 for i in items if i["category"] == "UNRESOLVED")
        out.append(rec)
    return out


def summarize(recs):
    ok = [r for r in recs if r.get("ok")]
    keys = sorted({k for r in ok for k in r["quantities"]})
    res = {"drawings": len(recs), "end_to_end_success": len(ok),
           "failures": [{"seed": r["seed"], "error": r["error"]} for r in recs if not r.get("ok")],
           "mean_abs_error": {k: round(sum(abs(r["quantities"][k]["error"] or 0) for r in ok) / max(1, len(ok)), 6)
                              for k in keys},
           "max_abs_error": {k: round(max([abs(r["quantities"][k]["error"] or 0) for r in ok] or [0]), 6)
                             for k in keys}}
    sp = [x for r in ok for x in r["unlabelled_spans"]]
    from collections import Counter
    c = Counter(x["outcome"] for x in sp)
    given = c["CORRECT"] + c["WRONG_SECTION"]
    res["unlabelled_spans"] = {"spans": len(sp), "outcomes": dict(sorted(c.items())),
                               "precision": round(c["CORRECT"] / given, 4) if given else None,
                               "recall": round(c["CORRECT"] / len(sp), 4) if sp else None,
                               "never_wrong_or_covered": round((c["CORRECT"] + c["UNRESOLVED_COVERS"]) / len(sp), 4)
                               if sp else None}
    for flag in (True, False):
        s2 = [x for x in sp if x["cb"] is flag]
        c2 = Counter(x["outcome"] for x in s2)
        res["unlabelled_spans"]["cb_spans" if flag else "simple_beam_spans"] = dict(sorted(c2.items()))
    cbs = [r["cb_concrete"] for r in ok if r["cb_concrete"]["truth"]]
    res["cb_concrete_mae"] = round(sum(abs(x["engine"] - x["truth"]) / x["truth"] for x in cbs) / len(cbs), 6) \
        if cbs else None
    rg = [r["beams_range"] for r in ok]
    res["beams_truth_in_base_plus_exposure"] = {
        "drawings": sum(1 for x in rg if x["low"] - 0.005 * x["truth"] <= x["truth"] <= x["high"] + 0.005 * x["truth"]),
        "of": len(rg), "mean_width_pct": round(100 * sum((x["high"] - x["low"]) / x["truth"] for x in rg) /
                                              max(1, len(rg)), 3)}
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
    recs = score(Path(a["--engine-root"]).resolve(), a.get("--conventions", "V3"), a["--drawings"], seeds)
    res = {"engine_root": Path(a["--engine-root"]).name, "conventions": a.get("--conventions", "V3"),
           "seeds": a["--seeds"], "per_drawing": recs, "summary": summarize(recs)}
    Path(a["--out"]).write_text(json.dumps(res, indent=1))
    print(json.dumps(res["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
