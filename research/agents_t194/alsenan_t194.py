"""T-194 (R6): Alsenan opening consistency, plan = elevation = opening list, through OPENING_CONSISTENCY_V1.

Repository inputs only (no drawing is read here; the readings were made by hand / ezdxf this run and committed as
numbers): PLAN_T194.csv (plan records: ARCH_TAKEOFF_V2.9 on P7757.dxf + 5 plan items V2.9 does not record, with
along-facade positions relative to the facade's first opening), ELEVATIONS_T194.csv (elevation / section readings),
research/agents_t150/OPENINGS_T150.csv (the hand census = the opening LIST; no schedule is issued, D-07).

    python3 -I alsenan_t194.py            writes CONSISTENCY_T194.csv, ISSUES_T194.csv, summary.json
    python3 -I alsenan_t194.py --check    regenerates in memory and compares with the committed files (exit 1 if not)

No quantity is produced: findings are issue rows and HELD causes (WORKFLOW_CONTROLS s.5).
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import opening_consistency_v1 as OC        # noqa: E402

T150 = ROOT / "research" / "agents_t150" / "OPENINGS_T150.csv"
KIND_T150 = {"DOOR": "DOOR", "WINDOW": "WINDOW", "GATE": "GATE", "OPENING": "OPENING", "LIFT": "OPENING",
             "UNRESOLVED": None}
BASIS_T150 = {"W17": "ARC_OUTER", "W03": "ARC_FACE", "SX-01": "PRINTED"}


def _read(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def plan_obs():
    out = []
    for r in _read(HERE / "PLAN_T194.csv"):
        out.append({"opening_id": r["opening_id"], "source": "PLAN", "ref": "plan (P7757.dxf; " +
                    (r["engine_ref"] or "hand read") + ")", "units": "m", "kind": r["kind"] or None,
                    "width": r["width"] or None, "width_basis": r["width_basis"] or None,
                    "chord_m": r["chord_m"] or None, "storey": r["storey"], "facade": r["facade"] or None,
                    "pos_m": r["pos_m"] or None, "drawn": True, "note": r["src"]})
    return out


def census_obs():
    """The T-150 census as the derived opening LIST. Its SILL_M column is read the way its name and its consumers
    (T-128 / T-144 / T-175 inputs) read it: above the finished floor. Only PRINTED heights are entered; an ASSUMED
    owner-fallback height (Q-55 C) is not a drawing value and is reported, not compared."""
    out, assumed = [], {}
    for r in _read(T150):
        o = {"opening_id": r["ID"], "source": "CENSUS", "ref": "T-150 OPENINGS_T150.csv", "units": "m",
             "kind": KIND_T150.get(r["KIND"]), "drawn": True}
        if r["WIDTH_M"]:
            o["width"] = r["WIDTH_M"].split(" ")[0]
            o["width_basis"] = BASIS_T150.get(r["ID"], "JAMB_TO_JAMB")
        if r["HEIGHT_STATUS"] == "PRINTED" and r["HEIGHT_M"]:
            sill = float(r["SILL_M"] or 0.0)
            o.update({"sill": sill, "head": round(sill + float(r["HEIGHT_M"]), 6), "level_basis": "ABOVE_FFL"})
        elif r["HEIGHT_STATUS"] == "ASSUMED":
            assumed[r["ID"]] = "ASSUMED — OWNER-APPROVED (Q-55 C) head 2.20 in the BOQ; no sheet prints it"
        out.append(o)
    return out, assumed


def elevation_obs():
    rows = _read(HERE / "ELEVATIONS_T194.csv")
    out = []
    for r in rows:
        o = {k: (v if v != "" else None) for k, v in r.items()}
        o["drawn"] = r["drawn"] == "1"
        out.append(o)
    return out


def run():
    plan = plan_obs()
    census, assumed = census_obs()
    elev = elevation_obs()
    plan_n = [OC.normalise(o) for o in plan]
    bound_obs, bind_rows, elev_only, unmatched = [], [], [], []
    by_fac = {}
    for o in elev:
        if o["opening_id"]:
            bound_obs.append(o)
        else:
            by_fac.setdefault(o["facade"], []).append(o)
    for fac, feats in sorted(by_fac.items()):
        fn = [OC.normalise(f) for f in feats]
        res = OC.bind([p for p in plan_n if p["facade"] == fac], fn)
        for code, detail in res["issues"]:
            bind_rows.append({"facade": fac, "code": code, "detail": detail})
        for f, pid in res["bound"]:
            src = next(raw for norm, raw in zip(fn, feats) if norm is f)
            o = dict(src)
            o["opening_id"] = pid
            bound_obs.append(o)
            bind_rows.append({"facade": fac, "code": "BOUND",
                              "detail": f'{f["storey"]} at {f["pos_m"]:.3f} m -> {pid}'})
        elev_only += OC.elevation_only_issues(res["unbound_features"])
        unmatched += [(fac, p["opening_id"]) for p in res["unmatched_plan"]]
        bind_rows.append({"facade": fac, "code": "ORIENTATION",
                          "detail": f'mirrored={res["mirrored"]} offset={res.get("offset_m")}'})
    result = OC.check(plan + census + bound_obs)
    issues = result["issues"] + elev_only
    for fac, pid in unmatched:
        # a plan opening on a facade that the elevation does not draw and no record explains
        if not any(o["opening_id"] == pid for o in bound_obs):
            issues.append({"opening_id": pid, "attr": "EXISTENCE", "code": "NOT_ON_ELEVATION",
                           "detail": f"on the {fac} facade of the plan, no feature of the {fac} elevation binds to it",
                           "boq_lines": OC.BOQ_LINES["EXISTENCE"]})
    return result, issues, bind_rows, assumed


def tables():
    result, issues, bind_rows, assumed = run()
    c = io.StringIO()
    w = csv.writer(c, lineterminator="\n")
    w.writerow(["opening_id"] + [f"{a}_VERDICT" for a in OC.ATTRS] + ["WIDTH_VALUES", "SILL_VALUES", "HEAD_VALUES",
                                                                       "KINDS", "SHOWN_ON", "NOT_SHOWN_ON",
                                                                       "HELD_LINES", "BOQ_HEIGHT_BASIS"])
    for row in result["openings"]:
        a = row["attrs"]
        w.writerow([row["opening_id"]] + [a[x]["verdict"] for x in OC.ATTRS] + [
            "; ".join(f"{b}: " + ", ".join(f"{lab} {x:.4f}" for lab, x in v) for b, v in a["WIDTH"]["values"].items()),
            "; ".join(f"{lab} {x:.3f}" for lab, x in a["SILL"]["values"]),
            "; ".join(f"{lab} {x:.3f}" for lab, x in a["HEAD"]["values"]),
            "/".join(a["KIND"]["values"]), "; ".join(a["EXISTENCE"]["drawn"]), "; ".join(a["EXISTENCE"]["hidden"]),
            "; ".join(sorted(row["held"])), assumed.get(row["opening_id"], "")])
    i = io.StringIO()
    w2 = csv.writer(i, lineterminator="\n")
    w2.writerow(["opening_id", "attr", "code", "detail", "boq_lines", "known_cover"])
    for x in sorted(issues, key=lambda x: (x["opening_id"] or "~", x["attr"], x["code"])):
        cover = assumed.get(x["opening_id"], "") if x["code"] == "HEAD_NOT_PRINTED" else ""
        w2.writerow([x["opening_id"] or "", x["attr"], x["code"], x["detail"], " ".join(x["boq_lines"]), cover])
    codes = {}
    for x in issues:
        codes[x["code"]] = codes.get(x["code"], 0) + 1
    verdicts = {a: {} for a in OC.ATTRS}
    for row in result["openings"]:
        for a in OC.ATTRS:
            v = row["attrs"][a]["verdict"]
            verdicts[a][v] = verdicts[a].get(v, 0) + 1
    summary = {"method": OC.METHOD, "openings": len(result["openings"]), "issues": len(issues),
               "issue_codes": dict(sorted(codes.items())), "verdicts": verdicts,
               "binding": bind_rows, "head_not_printed_covered_by_q55c": sum(
                   1 for x in issues if x["code"] == "HEAD_NOT_PRINTED" and x["opening_id"] in assumed)}
    return c.getvalue(), i.getvalue(), json.dumps(summary, indent=1, ensure_ascii=False) + "\n"


def main(argv):
    out = dict(zip(("CONSISTENCY_T194.csv", "ISSUES_T194.csv", "summary.json"), tables()))
    if "--check" in argv:
        bad = [n for n, t in out.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("reproduces" if not bad else f"DIFFERS: {bad}")
        return 1 if bad else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps(json.loads(out["summary.json"])["issue_codes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
