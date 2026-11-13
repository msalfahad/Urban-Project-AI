"""T-770 r2 read-only run: ARCH_TAKEOFF_V3.0.81 (FILL_WIRE_V1, R-T770-1 / R-T770-2) on the candidate V3.0.79 (T-314 r4,
merge 57e4a49f). Exactly research/agents_t314/v3079_run.py (its inputs unchanged; it runs the whole chain and asserts
V3_0_78 = the T-738 run of record), with --method ARCH_TAKEOFF_V3.0.81 and --v3081-inputs (the committed
research/agents_t770/V3081_PACKAGE.json, built by v3081_index.py) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3081_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t770 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_79 of this run must be the T-314 run of record (asserted by its line index). Every output goes to --out (outside
the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT / "research" / "agents_t314", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3079_run as R79  # noqa: E402  (T-314; imports T-738's v3078_run and the whole chain)

INDEX79 = ROOT / "research/agents_t314/out/LINE_INDEX_V3_0_79.json"
INDEX81 = HERE / "out/LINE_INDEX_V3_0_81.json"
PACKAGE = HERE / "V3081_PACKAGE.json"
DOWNGRADES = ROOT / "research/agents_t469/DOWNGRADES_SNAPSHOT.json"       # the snapshot the T-479 indexes bind
DOWNGRADES_SHA = "817326399e5b9ffff1d727b9599dff46d1f917c930e759c37e1d5721f0f85766"


def _downgrades(lines):
    """-> ({line_id: downgrade_id}, [status]) by the T-469 binding rule (research/agents_t469, unchanged) on the pinned
    snapshot; the same rule research/agents_t479/t479_registry_census.index_lines applies to build a line index."""
    if str(ROOT / "research" / "agents_t469") not in sys.path:
        sys.path.insert(0, str(ROOT / "research" / "agents_t469"))
    import t469_trade_scoreboard as T469  # noqa: E402
    raw = DOWNGRADES.read_bytes()
    if hashlib.sha256(raw).hexdigest() != DOWNGRADES_SHA:
        raise SystemExit(f"{DOWNGRADES.name}: sha is not the pinned {DOWNGRADES_SHA[:8]}")
    doc = json.loads(raw)
    return T469.applied_downgrades(lines, doc["downgrades"] if isinstance(doc, dict) else doc)


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-314 v3079_run, re-pointed at V3.0.81 (same inputs + --v3081-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.79", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.81"
        seen["out"] = Path(args[args.index("--out") + 1])
        return real(args + ["--v3081-inputs", str(PACKAGE)])
    M.main = hub
    try:
        R79.main(argv)        # its own wrapper re-points .78 -> .79 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    lines79 = json.loads((d / "V3_0_79_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines81 = json.loads((d / "V3_0_81_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_81_RUN.json").read_text(encoding="utf-8"))
    idx81 = {ln["line_id"]: ln for ln in json.loads(INDEX81.read_text(encoding="utf-8"))["lines"]}
    # the BOQ-line view must agree with the committed line index, line by line, classified AS THE INDEX CLASSIFIES
    # (T-770 r3, Verifier FAULT 2): the T-479 index rule = line class, then a binding Checker downgrade of the pinned
    # T-469 snapshot moves RELEASED -> HELD (never promotes). DG-1b0eacce2d68f2a5 holds 38 STR.REBAR footing lines
    # (874.86 kg) in V3.0.79 and V3.0.81 alike; the applied set must equal the one the committed index records.
    from engine.source import arch_v3081 as A
    dg_held, dg_status = _downgrades(lines81)
    want = sorted(r["downgrade_id"] for r in json.loads(INDEX81.read_text(encoding="utf-8"))["downgrades"]
                  if r.get("status") == "APPLIED")
    got = sorted(r["downgrade_id"] for r in dg_status if r.get("status") == "APPLIED")
    if got != want:
        print("applied downgrades", got, "differ from the committed index", want)
        return 1
    bad = []
    for ln in lines81:
        x = idx81.get(ln["line_id"])
        c = A.line_class(ln)
        if c == "RELEASED" and ln["line_id"] in dg_held:
            c = "HELD"
        if x is None or x["class"] != c:
            bad.append((ln["line_id"], c, x and x["class"]))
        elif c == "RELEASED" and abs(float(ln["measured_net"]) - float(x["measured_net"])) > 1e-6:
            bad.append((ln["line_id"], ln["measured_net"], x["measured_net"]))
    print("base: V3_0_79 lines", len(lines79), "-> V3_0_81 lines", len(lines81), "| identity",
          json.dumps(run["identity"], sort_keys=True))
    print("V3_0_81_BOQ_LINES.json", hashlib.sha256((d / "V3_0_81_BOQ_LINES.json").read_bytes()).hexdigest()[:8],
          "| lines disagreeing with the committed index:", len(bad), bad[:5])
    return 1 if bad or len(lines81) != len(idx81) else 0


if __name__ == "__main__":
    sys.exit(main())
