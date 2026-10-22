"""T-131 read-only run for the verifier: the released ARCH_TAKEOFF_V2.9 and the ARCH_TAKEOFF_V3.0 candidate on the same
drawings (the development villa's Drive copies: the architectural DXF from P7757_DXF_COMPRESSED.zip and the structural
"ST7757 dxf.dxf"), with route G (conventions URBAN_M8_GENERIC_CONVENTIONS_V6). Prints the before / after table of
every line the candidate changes (quantities, units, states and engine ids only: no coordinates, no names). Every
output goes to --out (outside the repository).

    python3 -I research/agents_t131/alsenan_v30_run.py <plan.dxf> <structural.dxf> --out <scratch>/t131 \
        --profile research/urban_engine_m4_correctness/profile_st7757_m4.json [--no-decision]

Project inputs as T-120: research/agents_t010/sanitary_reading.json, research/agents_t071/alsenan_facts.json and the
pantry's printed 4.50 x 3.00 m typed as a project data record (owner Q-37 A, Q-17 A). The owner's Q-67 A answer is
bound as a project decision with its condition check (T-123, verifier run 45); --no-decision runs without it (the
facade run then stays a range)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PID = "development-villa-t131"
CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"


def facts(plan_name):
    from engine.source import arch_measure as AM
    f = {"schema": AM.FACTS_SCHEMA,
         "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
             encoding="utf-8"))["items"],
         "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(encoding="utf-8"))}
    f["project_data"] = {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": [{
        "key": "WET_ZONE_SIZE_GF_PANTRY", "project": PID, "kind": "table", "unit": "none",
        "value": {"length_m": 4.50, "width_m": 3.00}, "status": "DRAWING-VERIFIED", "drawing_file": plan_name,
        "drawing_number": "architectural set", "revision": "no revision printed", "sheet": "ground floor plan",
        "reference": "printed 4.50 x 3.00 m at the PANTRY label", "applies_to": {"floors": ["GF"], "members": ["PANTRY"]},
        "reviewer_or_source": "verifier hand reading (T-114 read the same printed size)", "entered_by": "TYPED"}]}
    return f


DECISIONS = {"schema": "URBAN_V30_PROJECT_DECISIONS_V1", "project": PID, "decisions": [{
    "question": "Q-67", "answer": "A", "conditional": True, "binds": "PASSAGE_SINGLE_OPEN_MOUTH_EXTERIOR",
    "floors": ["GF"], "condition": "open to outside air without enclosing doors or glazing (current drawings)",
    "condition_evidence": {"task": "T-123", "merge_commit": "6699bb6", "verifier_run": "run 45 (2026-10-20 21:05 UTC)",
                           "finding": "0 entities across the 1.20 m mouth; far end closed by a 0.20 m boundary wall; "
                                      "no door, no glazing"},
    "source": "owner in the main chat, 2026-10-20 18:45 UTC (OWNER_QUESTIONS.md Q-67)"}]}


def common_args(a, out):
    """the arguments every run of this script shares; the route G profile is required (T-142 D1)."""
    if not getattr(a, "profile", None):
        raise SystemExit("--profile (route G drawing profile) is required")
    return ["--drawings", a.plan, "--structural", a.structural, "--conventions", str(CONV), "--profile", a.profile,
            "--facts", str(Path(out) / "facts.json"), "--project", PID, "--no-svg"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-decision", action="store_true")
    ap.add_argument("--profile", required=True, help="route G drawing profile (T-142 D1: without it the route G "
                    "storey heights are not read and every column piece stays held)")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "facts.json").write_text(json.dumps(facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = common_args(a, out)
    M.main(["arch", "--out", str(out / "v29"), "--method", "ARCH_TAKEOFF_V2.9"] + common)
    extra = ["--v30-released", str(out / "v29" / "BOQ_LINES.json")]
    hist = []                                  # r2: the versions between V2.9 and V2.13 name each change's origin
    for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
        tag = "v" + m.split("_V")[-1].replace(".", "")
        M.main(["arch", "--out", str(out / tag), "--method", m] + common)
        hist.append(f"{m}={out / tag / 'BOQ_LINES.json'}")
    extra += ["--v30-history"] + hist
    if not a.no_decision:
        (out / "decisions.json").write_text(json.dumps(DECISIONS), encoding="utf-8")
        extra += ["--v30-decisions", str(out / "decisions.json")]
    M.main(["arch", "--out", str(out / "v30"), "--method", "ARCH_TAKEOFF_V3.0"] + common + extra)
    led = json.loads((out / "v30" / "V3_0_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((out / "v30" / "V3_0_RUN.json").read_text(encoding="utf-8"))

    def q(x):
        if not x or x.get("state") is None:
            return "-"
        if x.get("value") is not None:
            return f"{x['value']:.3f} {x['state']}"
        if x.get("low") is not None:
            return f"{x['low']:.3f}..{x['high']:.3f} {x['state']}"
        return x["state"]
    print("identity:", run["identity"])
    by = {}
    for r in led["rows"]:
        if r["piece"] == "INHERITED_FROM_BASE":
            k = (" + ".join(st["version"] for st in r["since_v2_9"]) or "?", r["action"], r["item_code"])
            by[k] = by.get(k, 0) + 1
    for (v, act, code), n in sorted(by.items()):
        print(f"inherited {n:4d}  {act:19s} {code:30s} {v}")
    for r in led["rows"]:
        if r["piece"] == "MEMBRANE_V2_13" and r["before_released_v2_9"]["state"] == r["after_v3_0"]["state"]:
            continue
        print(f"{r['piece']:20s} {r['action']:17s} {r['item_code']:22s} {r['floor'] or '':10s} {r['unit']:4s} "
              f"V2.9 {q(r['before_released_v2_9'])} | V2.13 {q(r['before_base_v2_13'])} | V3.0 {q(r['after_v3_0'])}")
    tot = {}
    for r in led["rows"]:
        if r["item_code"] == "STR.CONC.STRAP":
            t = tot.setdefault("strap", [0.0, 0.0, 0.0, 0.0])
            t[0] += r["before_base_v2_13"]["value"] or 0.0
            t[1] += r["after_v3_0"]["value"] or 0.0
            t[2] += r["after_v3_0"]["low"] or 0.0
            t[3] += r["after_v3_0"]["high"] or 0.0
    if "strap" in tot:
        t = tot["strap"]
        print(f"straps m3: V2.13 {t[0]:.3f} -> V3.0 measured {t[1]:.3f} + held {t[2]:.3f}..{t[3]:.3f}")
    return 0


if __name__ == "__main__":
    main()
