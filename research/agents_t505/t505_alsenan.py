"""T-505 (lane S, non-candidate): DISPOSAL_BALANCE_V2 (loss accounts, R-T505-1) on the earthworks lines of the candidate
ARCH_TAKEOFF_V3.0.50 (T-497 MERGED 5f8814e8: the external ground-beam trench L-438a4abd3adc0475d0bd restated
1.203269 .. 1.432834 -> 1.069269 .. 1.176467 m3, still HELD / BOUNDED_EXPOSURE; every other V3.0.48 line
byte-identical, asserted by arch_v3050).

Inputs, each pinned by sha256 (an edited file stops the run); every figure and status is READ, none typed:
  research/agents_t503 terms()            the 19 V3.0.48 earthworks terms (its own pins: summary_t350r4, LINE_INDEX)
  research/agents_t497/summary_t497.json  the V3.0.50 trench range (and t497_inputs.zones(), the V3.0.50 input record)
  research/agents_t503/summary_t503.json  the V1 result, for the s = 0 end comparison

Facts for this villa (unchanged from T-503): no geotechnical evidence (s = 0 .. 1), no measured / specified density, no
measured bulking, contract basis silent (in situ). Losses: none measured, specified or documented: the Kuwait MPW
General Specifications for Buildings and Engineering Works (1990, Drive "Engineering Sources", 01 Kuwait References)
s.02220 and s.02223 (read in full, Part 4 measurement included) state no handling or procurement loss and no bulking
factor; the other reference folders hold no earthworks estimating source -> loss_reuse and loss_import HELD.

    python3 -I research/agents_t505/t505_alsenan.py          # writes summary_t505.json beside this file
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research/agents_t503", ROOT / "research/agents_t497", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import disposal_balance_v2 as B  # noqa: E402
import t503_alsenan as A503  # noqa: E402

S497 = ROOT / "research/agents_t497/summary_t497.json"
S503 = ROOT / "research/agents_t503/summary_t503.json"
PINS = {S497: "ffcf016fd510260395f30cf6fd715274de1bf95dbd83c3dcc8a5002446c31f93",
        S503: "67cf20fad53e414b13879ad3e1d737189a068cc1f065388993b5bb64dcaf9271"}
TRENCH = A503.TRENCH_PENDING
CANDIDATE = "ARCH_TAKEOFF_V3.0.50"


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return json.loads(b)


def trench_v3050():
    s = _load(S497)
    lo, hi = s["trench_line_m3_drawn_outline"]
    if [lo, hi] != list(s["checker_drawn_outline_m3"]):
        raise SystemExit("the V3.0.50 trench is not the Checker's corrected figure")
    return lo, hi


def terms():
    lo, hi = trench_v3050()
    out = []
    for t in A503.terms():
        if t["line_id"] == TRENCH:
            t = B.term(TRENCH, t["role"], status=B.HELD, zone=t["zone"],
                       held_parts=[f"{CANDIDATE}: HELD (BOUNDED_EXPOSURE) {lo:.6f} .. {hi:.6f} m3 in plot .. with "
                                   f"beyond-plot (T-497, R-T497-1); a HELD line's bound stays beside, never summed"])
        out.append(t)
    return out


def run():
    T = terms()
    res = B.balance(T, rho_insitu=B.density(None, B.HELD, kind="INSITU"),
                    rho_target=B.density(None, B.HELD, kind="PLACEMENT_TARGET"),
                    suit=B.suitability(), loss_reuse=B.loss(B.REUSE), loss_import=B.loss(B.IMPORT),
                    bulk=B.bulking(), contract_basis=None)
    lo, hi = trench_v3050()
    res["disposal_line"] = A503.DISPOSAL_LINE
    res["candidate"] = {"method": CANDIDATE, "base_lines_sha256": A503.CANDIDATE_SHA,
                        "restated_line": TRENCH, "restated_m3": [lo, hi]}
    res["held_bounds_beside"] = {"lines": [TRENCH], "low": lo, "high": hi,
                                 "if_taken_s0_end_m3": [round(res["disposal_insitu_m3"]["high"]["value"] + lo, 6),
                                                        round(res["disposal_insitu_m3"]["high"]["value"] + hi, 6)],
                                 "note": "named beside, never added (the trench line is HELD)"}
    v1 = _load(S503)
    res["v1_comparison"] = {
        "s0_disposal_v1": v1["disposal_insitu_m3"]["high"], "s0_import_v1": v1["import_compacted_m3"]["high"],
        "s0_unchanged": (res["disposal_insitu_m3"]["high"]["value"] == v1["disposal_insitu_m3"]["high"]["value"] and
                         res["import_compacted_m3"]["high"]["value"] == v1["import_compacted_m3"]["high"]["value"])}
    res["terms"] = [{k: t[k] for k in ("line_id", "role", "zone", "low", "high", "status")} for t in T]
    return res


def main(write=True):
    res = run()
    if write:
        (HERE / "summary_t505.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print("E", r["excavation"]["low"], "..", r["excavation"]["high"], "open", len(r["excavation"]["held_lines"]))
    print("D", r["fill_demand"]["low"], "..", r["fill_demand"]["high"], "open", len(r["fill_demand"]["held_lines"]))
    for k in ("disposal_insitu_m3", "import_compacted_m3"):
        print(k, "low:", B.describe_end(r[k]["low"]), "| high:", B.describe_end(r[k]["high"]))
    print("state", r["state"], "| beside", r["held_bounds_beside"]["if_taken_s0_end_m3"], "| v1", r["v1_comparison"]
          ["s0_unchanged"])
