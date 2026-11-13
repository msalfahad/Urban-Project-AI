"""T-770 r2 read-only run: ARCH_TAKEOFF_V3.0.81 (FILL_WIRE_V1, R-T770-1 / R-T770-2) on the candidate V3.0.79 (T-314 r4,
merge 57e4a49f). Exactly research/agents_t314/v3079_run.py (its inputs unchanged; it runs the whole chain and asserts
V3_0_78 = the T-738 run of record), with --method ARCH_TAKEOFF_V3.0.81 and --v3081-inputs (the committed
research/agents_t770/V3081_PACKAGE.json, built by v3081_index.py) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3081_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t770 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3081_run.py --check-dir <the hub output dir
        holding V3_0_79 / V3_0_81_BOQ_LINES.json>        (the line check alone, on a finished run)

V3_0_79 of this run must be the T-314 run of record (asserted by its line index). The line check (r3) classifies as
the committed index does (T-479 rule: line class, then the Checker downgrades the index records APPLIED) and names the
one downgrade that re-binds on V3.0.81 (REBINDING), a finding for the Checker. Every output goes to --out (outside
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


def _snapshot():
    raw = DOWNGRADES.read_bytes()
    if hashlib.sha256(raw).hexdigest() != DOWNGRADES_SHA:
        raise SystemExit(f"{DOWNGRADES.name}: sha is not the pinned {DOWNGRADES_SHA[:8]}")
    doc = json.loads(raw)
    return doc["downgrades"] if isinstance(doc, dict) else doc


def T469_applied(lines, records):
    if str(ROOT / "research" / "agents_t469") not in sys.path:
        sys.path.insert(0, str(ROOT / "research" / "agents_t469"))
    import t469_trade_scoreboard as T469  # noqa: E402
    return T469.applied_downgrades(lines, records)


def _downgrades(lines):
    """-> ({line_id: downgrade_id}, [status]) by the T-469 binding rule (research/agents_t469, unchanged) on the pinned
    snapshot; the same rule research/agents_t479/t479_registry_census.index_lines applies to build a line index."""
    return T469_applied(lines, _snapshot())


# A Checker downgrade the committed index records as STALE (not applied) on V3.0.79 that binds again on the V3.0.81
# lines because a wired DEFAULT figure equals its engine quantity. Named here with its lines; any OTHER newly binding
# downgrade fails the run. DG-38971e0d1d5de81c (Verifier 2026-10-25, V3.0.16, UNSUPPORTED BASIS: court exterior ground
# beams, court section not printed, D-35 / GS-16) = 0.627 m3 on 3 STR.CONC.GROUND_BEAM lines; T-761 (Gate A PASS,
# merged 8d3bbf1c) filled the same 3 lines by the owner company default 2026-11-13 ("exterior GB same mark"):
# 0.456 + 0.054 + 0.117 = 0.627 m3 DEFAULT. Whether the owner default resolves the record or the 3 lines stay HELD is
# the Checker's call (only the Checker writes or resolves a downgrade); the index keeps the T-761 figures meanwhile.
REBINDING = {"DG-38971e0d1d5de81c": ("L-21795b350fbd09150c43", "L-62243c74c430d383be86", "L-a55bfa01b726ef11650c")}


def check(lines81, index):
    """-> (disagreements, named re-binding downgrades): the run's lines against the committed index, classified as the
    index classifies (T-479: line class, then the downgrades the index records APPLIED; never promotes)."""
    from engine.source import arch_v3081 as A
    idx = {ln["line_id"]: ln for ln in index["lines"]}
    applied_in_index = {r["downgrade_id"] for r in index["downgrades"] if r.get("status") == "APPLIED"}
    _held, status = _downgrades(lines81)
    got = {r["downgrade_id"] for r in status if r.get("status") == "APPLIED"}
    bad, rebind = [], []
    for did in sorted(applied_in_index - got):
        bad.append((did, "APPLIED in the index, not binding on the run"))
    for did in sorted(got - applied_in_index):
        if did not in REBINDING:
            bad.append((did, "binds on the run, not APPLIED in the index (unnamed)"))
    snap = {d["downgrade_id"]: d for d in _snapshot()}
    for did, ids in REBINDING.items():
        if did in got:
            if tuple(snap[did]["line_ids"]) != ids:
                bad.append((did, "named re-binding downgrade covers other lines"))
            rebind.append({"downgrade_id": did, "line_ids": list(ids), "engine_qty": snap[did]["engine_qty"],
                           "unit": snap[did]["unit"], "reason": snap[did]["reason"]})
    held = {}
    _h, _s = T469_applied(lines81, [snap[d] for d in sorted(applied_in_index)])
    held.update(_h)
    for ln in lines81:
        x = idx.get(ln["line_id"])
        c = A.line_class(ln)
        if c == "RELEASED" and ln["line_id"] in held:
            c = "HELD"
        if x is None or x["class"] != c:
            bad.append((ln["line_id"], c, x and x["class"]))
        elif c == "RELEASED" and abs(float(ln["measured_net"]) - float(x["measured_net"])) > 1e-6:
            bad.append((ln["line_id"], ln["measured_net"], x["measured_net"]))
    if len(lines81) != len(idx):
        bad.append(("line count", len(lines81), len(idx)))
    return bad, rebind


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main
    if argv[:1] == ["--check-dir"]:          # the check alone on a finished run's hub output dir (no drawing read)
        seen["out"] = Path(argv[1])
        return _report(seen["out"])

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
    return _report(seen["out"])


def _report(d):
    lines79 = json.loads((d / "V3_0_79_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines81 = json.loads((d / "V3_0_81_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_81_RUN.json").read_text(encoding="utf-8"))
    bad, rebind = check(lines81, json.loads(INDEX81.read_text(encoding="utf-8")))
    for r in rebind:
        print("FINDING (Checker's call, not a fault of the check):", json.dumps(r, sort_keys=True))
    print("base: V3_0_79 lines", len(lines79), "-> V3_0_81 lines", len(lines81), "| identity",
          json.dumps(run["identity"], sort_keys=True))
    print("V3_0_81_BOQ_LINES.json", hashlib.sha256((d / "V3_0_81_BOQ_LINES.json").read_bytes()).hexdigest()[:8],
          "| lines disagreeing with the committed index:", len(bad), bad[:5], "| named re-binding downgrades:",
          [r["downgrade_id"] for r in rebind])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
