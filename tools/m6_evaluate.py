"""M6 EVALUATION - the completeness engine on synthetic villas against what the generator drew.

    python3 -I tools/m6_evaluate.py OUT.json SEED [SEED ...] [--defects | --mixed] [--hard] [--heldout-vocabulary]
                                    [--v2-cases] [--conventions C.json]

For each seed: tools/synthetic_villa_m6 draws a villa with injected completeness cases and distractors; the CLI runs
route G with the completeness pass; every drawn element is matched to the findings that should report it (kind,
sheet storey, box within 0.6 m). Scores: detection recall by element kind, family accuracy (right / UNKNOWN /
wrong), false findings per drawing (an actionable finding that matches no drawn element and no known case of the
base design), runtime. The truth never comes from the engine.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import synthetic_villa_m6 as SM6        # noqa: E402
from tools import urban_boq_m2 as CLI              # noqa: E402

CONVENTIONS = "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"
NOT_ACTIONABLE = ("UNRESOLVED_ITEMS", "REFERENCED_NOT_DRAWN")
STOREY_OF = {"FOUNDATION": "FOUNDATION", "GF": "GF", "1F": "1F", "2F": "2F", "SCHED": "ALL"}
TOL = 0.6


def _touch(a, b, tol=TOL):
    return a[0] - tol <= b[2] and b[0] - tol <= a[2] and a[1] - tol <= b[3] and b[1] - tol <= a[3]


def _hits(el, findings, items):
    """the findings (and, for planted columns, the items) that report one drawn element."""
    kinds = set(el["expect"])
    st = el.get("storey") or STOREY_OF.get(el["sheet"])
    out = []
    for f in findings:
        if f["KIND"] not in kinds:
            continue
        if el["kind"] in ("SCHEDULE_ORPHAN", "SCHEDULE_UNREAD"):
            if el["token"] in f["EVIDENCE"]:
                out.append(f)
            continue
        if el["kind"] == "LABEL_ORPHAN" and f["KIND"] == "PLACED_NOT_SCHEDULED":
            if el["token"] in f["EVIDENCE"]:
                out.append(f)
            continue
        if el.get("box") and f.get("BOX_M"):
            fst = f["STOREY"]
            if fst == st and _touch(el["box"], f["BOX_M"]):
                out.append(f)
        elif not el.get("box") or not f.get("BOX_M"):
            if f["STOREY"] == st:
                out.append(f)
    for a in el.get("also") or []:              # the same element drawn on another storey (a planted column's outline)
        for f in findings:
            if f["KIND"] in kinds and f.get("BOX_M") and f["STOREY"] == a["storey"] and _touch(a["box"], f["BOX_M"]):
                out.append(f)
    if el["kind"] == "PLANTED_COLUMN":
        for it in items:
            if it["trade"] == "CONCRETE" and "PC@" in it["component_id"] and it["category"] != "UNRESOLVED":
                out.append({"KIND": "MEASURED", "FAMILY": "PLANTED_COLUMN", "FINDING_ID": it["item_id"]})
                break
    return out


def _family_state(el, fam):
    return ("NA" if not el.get("family") or el["family"] in ("UNKNOWN",) else
            "RIGHT" if el["family"] in fam or (el["family"] == "PLANTED_COLUMN" and "COLUMNS" in fam) else
            "UNKNOWN" if fam and set(fam) <= {"UNKNOWN"} else "WRONG" if fam else "NA")


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - ix * iy
    return ix * iy / ua if ua > 0 else (1.0 if _touch(a, b, 0.05) else 0.0)


def _route_column_errors(items, truth):
    """design columns (position, storey) the route holds no column item for: (x, y, storey) in sheet-local m.
    A column item is placed by its label position (within 1.5 m of the design column)."""
    import re
    have = []
    for it in items:
        m = re.match(r"^P-C:COL:SH\d+:[^@]+@(-?\d+),(-?\d+)\|(\w+)$", it["item_id"])
        if m and it["trade"] == "CONCRETE":
            have.append((float(m.group(1)), float(m.group(2)), m.group(3)))
    scale = None
    for x, y, _ in have:
        scale = 0.001 if abs(x) > 500 else 1.0
        break
    out = []
    gap = truth.get("column_gap_box")
    for c in truth.get("design_columns", []):
        cx, cy = c["local"]
        for st in c["storeys"]:
            if gap and st == "GF" and gap[0] <= cx <= gap[2] and gap[1] <= cy <= gap[3]:
                continue                                         # the injected gap is an element, not a route error
            if not any(st == hs and math.hypot(hx * (scale or 1) - cx, hy * (scale or 1) - cy) <= 1.5
                       for hx, hy, hs in have):
                out.append((cx, cy, st))
    return out


def _measured_as_panel(el, D):
    """a sunken-slab outline the slab engine closed as its own measured panel: measured (its level is not)."""
    if el["kind"] != "SUNKEN_SLAB" or not el.get("box"):
        return False
    u = D["unit_m"]
    for sid, rec in D["sheets"].items():
        if rec["sheet"]["role"] != "SLAB_PLAN" or rec["sheet"]["storey"] != el["sheet"]:
            continue
        o = rec["sheet"].get("origin") or (0.0, 0.0)
        for f in ((rec.get("slab") or {}).get("faces") or []):
            xs = [(x - o[0]) * u for x, _ in f["polygon"]]
            ys = [(y - o[1]) * u for _, y in f["polygon"]]
            if f.get("class") == "PANEL" and all(abs(a - b) <= 0.05 for a, b in zip(
                    (min(xs), min(ys), max(xs), max(ys)), el["box"])):
                return True
    return False


def evaluate(seed, work, defects=False, conventions=CONVENTIONS, vocabulary="dev", hard=False, m6v2=False):
    t0 = time.perf_counter()
    rec = {"seed": seed, "defects": bool(defects), "vocabulary": vocabulary, "hard": bool(hard), "m6v2": bool(m6v2),
           "ok": False}
    try:
        dxf = SM6.generate(work, seed, defects=defects, vocabulary=vocabulary, hard=hard, m6v2=m6v2)
        base_truth = json.loads((Path(work) / f"villa_m6_{seed}.truth.json").read_text(encoding="utf-8"))
        truth = base_truth["m6"]
        R = CLI.compute([str(dxf)], profile=str(Path(work) / f"villa_m6_{seed}.profile.json"), route="G",
                        conventions=str(ROOT / conventions), completeness=True)
    except Exception as e:                                    # a crash is a result, never hidden
        rec["error"] = f"{type(e).__name__}: {e}"
        return rec
    CR = R["generic"]["completeness"]
    F = CR["findings"]
    used = set()
    els = []
    for el in truth["elements"]:
        h = _hits(el, F, R["items"])
        if not h and _measured_as_panel(el, R["generic"]["D"]):
            h = [{"KIND": "MEASURED_AS_PANEL", "FAMILY": "SLAB_STEP", "FINDING_ID": f"PANEL:{el['id']}"}]
        for f in h:
            used.add(f["FINDING_ID"])
        fam = sorted({f["FAMILY"] for f in h})
        fam_state = _family_state(el, fam)
        best = max((f for f in h if f.get("BOX_M") and el.get("box")), key=lambda f: _iou(el["box"], f["BOX_M"]),
                   default=None)                 # the finding that sits on the element (a plot-wide box hits all)
        fam_best = _family_state(el, [best["FAMILY"]]) if best else fam_state
        els.append({"id": el["id"], "kind": el["kind"], "detected": bool(h), "by": sorted({f["KIND"] for f in h}),
                    "family": el.get("family"), "family_found": fam, "family_state": fam_state,
                    "family_state_best": fam_best,
                    "note": el.get("note"), "layer": el.get("layer")})
    for bk in truth["base_known"]:
        for f in F:
            if f["KIND"] not in bk["expect"]:
                continue
            if bk.get("token") and bk["token"] in f["EVIDENCE"]:
                used.add(f["FINDING_ID"])
            elif bk.get("box") and f.get("BOX_M") and f["STOREY"] == STOREY_OF.get(bk.get("sheet")) and \
                    _touch(bk["box"], f["BOX_M"]):
                used.add(f["FINDING_ID"])
    route_err = _route_column_errors(R["items"], truth)
    confirmed = []
    for f in F:                                  # a column finding at a design column the route did not count is a
        if f["FINDING_ID"] in used or not f["KIND"].startswith("COLUMN"):     # route error the engine caught
            continue
        st = f["STOREY"]
        if f.get("BOX_M") and any(st == e_st and _touch((x, y, x, y), f["BOX_M"], 0.8) for x, y, e_st in route_err):
            used.add(f["FINDING_ID"])
            confirmed.append(f["KIND"])
        elif not f.get("BOX_M") and any(st == e_st for _, _, e_st in route_err):
            used.add(f["FINDING_ID"])
            confirmed.append(f["KIND"])
    design_slab = (base_truth.get("quantities") or {}).get("SLABS")
    for f in F:                                  # consequences of an injected case the design truth confirms
        if f["FINDING_ID"] in used:
            continue
        if f["KIND"] == "SLAB_COVERAGE_LOW" and design_slab:
            got = sum(i.get("base") or 0 for i in R["items"] if i["trade"] == "CONCRETE" and i["family"] == "SLABS"
                      and i["storey"] == f["STOREY"] and i["category"] != "UNRESOLVED")
            if got < 0.6 * design_slab / 2:      # both roof slabs of the design share one layout and thickness
                used.add(f["FINDING_ID"])
                confirmed.append(f["KIND"])
        elif f["KIND"] == "MEMBER_OUTLINE_SUSPECT" and f.get("BOX_M"):
            if any(el.get("box") and STOREY_OF.get(el["sheet"]) == f["STOREY"] and _touch(el["box"], f["BOX_M"], 0.1)
                   for el in truth["elements"]):
                used.add(f["FINDING_ID"])
                confirmed.append(f["KIND"])
    fp = [{"kind": f["KIND"], "family": f["FAMILY"], "sheet": f["SHEET"], "storey": f["STOREY"], "box": f["BOX_M"],
           "evidence": f["EVIDENCE"][:160]} for f in F if f["FINDING_ID"] not in used and f["KIND"] not in
          NOT_ACTIONABLE]
    rec.update(ok=True, seconds=round(time.perf_counter() - t0, 2), elements=els, false_findings=fp,
               route_errors=len(route_err), route_errors_reported=confirmed,
               n_findings=len(F), variant=truth["variant"], scores=CR["scores"])
    return rec


def summarise(recs):
    by = defaultdict(lambda: Counter())
    fam = Counter()
    fam_best = Counter()
    fps = Counter()
    for r in recs:
        if not r.get("ok"):
            continue
        for e in r["elements"]:
            by[e["kind"]]["n"] += 1
            by[e["kind"]]["detected"] += int(e["detected"])
            if e["detected"]:
                fam[e["family_state"]] += 1
                fam_best[e.get("family_state_best", e["family_state"])] += 1
        for f in r["false_findings"]:
            fps[f["kind"]] += 1
    n_el = sum(v["n"] for v in by.values())
    n_det = sum(v["detected"] for v in by.values())
    ok = [r for r in recs if r.get("ok")]
    return {"drawings": len(recs), "crashed": [r["seed"] for r in recs if not r.get("ok")],
            "elements": n_el, "detected": n_det, "recall": round(n_det / n_el, 4) if n_el else None,
            "recall_by_kind": {k: {"n": v["n"], "detected": v["detected"],
                                   "recall": round(v["detected"] / v["n"], 3)} for k, v in sorted(by.items())},
            "family_of_detected": dict(sorted(fam.items())),
            "family_of_detected_best_match": dict(sorted(fam_best.items())),
            "route_column_errors": sum(r.get("route_errors", 0) for r in ok),
            "route_errors_reported_findings": sum(len(r.get("route_errors_reported", [])) for r in ok),
            "false_findings": sum(fps.values()),
            "false_findings_per_drawing": round(sum(fps.values()) / len(ok), 3) if ok else None,
            "false_findings_by_kind": dict(sorted(fps.items())),
            "seconds_mean": round(sum(r["seconds"] for r in ok) / len(ok), 2) if ok else None}


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
                                 conventions=conv, vocabulary="heldout" if "--heldout-vocabulary" in argv else "dev",
                                 hard="--hard" in argv, m6v2="--v2-cases" in argv))
    res = {"summary": summarise(recs), "drawings": recs}
    Path(out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res["summary"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
