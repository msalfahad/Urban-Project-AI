"""T-497: the URBAN_V3050_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.50 (engine.source.arch_v3050), built ONLY from
pinned files (an edited file stops the build):

  research/agents_t497/summary_t497.json   this task's re-measure under EXCAVATION_ZONE_OWNERSHIP_V1 (R-T497-1) on the
      Drive DXF (t497_alsenan.py); it must reproduce the Checker's own corrected trench of F-C-T350R4-1 EXACTLY
      (Verifier 2026-11-03 23:24 UTC Gate B hand check on the T-350 r4 package, merged 5de697ff): 1.069269 .. 1.176467
      m3, drawn-outline scenario; any other figure stops the build;
  research/agents_t484/summary_t484.json   T-484 (MERGED 12395ea4, Verifier Gate A 2026-11-03 09:56): the strip and
      zone plans the re-measure starts from (pinned by the same sha256 as the V3.0.48 inputs).

The V3.0.48 range it replaces (was_low / was_high) is READ from the T-350 r4 inputs builder (its own pins), never typed.

    python3 -I research/agents_t497/t497_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research/agents_t350r4"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t350r4_inputs as R4  # noqa: E402

S497 = ROOT / "research/agents_t497/summary_t497.json"
S484 = R4.S484
PINS = {S497: "ffcf016fd510260395f30cf6fd715274de1bf95dbd83c3dcc8a5002446c31f93", S484: R4.PINS[R4.S484]}
CHECKER = (1.069269, 1.176467)        # F-C-T350R4-1 corrected trench, drawn-outline scenario (Checker's own figures)
SOURCES = {
    "F-C-T350R4-1": {"task": "F-C-T350R4-1", "file": "research/agents_t497/summary_t497.json", "sha256": PINS[S497],
                     "merge_commit": "5de697ff",
                     "checker_run": "Verifier 2026-11-03 23:24 UTC Gate B hand check on T-350 r4 (session_01E6cPnbakYT7D"
                                    "pjoSWpJcC8D): own strip outside the pits AND the F10F / FF plans, beyond-plot "
                                    "1.071981 m2 AGREE; corrected trench 1.069269 .. 1.176467 m3 (drawn-outline "
                                    "scenario); T-497 re-measure reproduces it exactly (Gate B to confirm)"},
    "T-484": dict(R4.SOURCES["T-484"]),
}
ZONE = "Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)"


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return json.loads(b.decode("utf-8"))


def zones():
    s = _load(S497)
    _load(S484)
    was = next(z for z in R4.zones() if z["zone"] == ZONE)
    line = s["trench_line_m3_drawn_outline"]
    if tuple(line) != CHECKER or tuple(s["checker_drawn_outline_m3"]) != CHECKER:
        raise SystemExit(f"the re-measure {line} is not the Checker's corrected trench {CHECKER}")
    if s["v3048_trench_m3"] != [was["low"], was["high"]]:
        raise SystemExit("the V3.0.48 trench range moved (stale binding)")
    do = s["scenarios"]["drawn outline"]
    given = {k: v for k, v in do["trench_given_up_m2"].items() if v > 0}
    others = {k: v for k, v in s["scenarios"].items() if k != "drawn outline"}
    lo_o = min(v["trench_m3"][0] for v in others.values())
    hi_o = max(v["trench_m3"][1] for v in others.values())
    res = s["scenario_residual_m3"]
    beyond = round(line[1] - line[0], 6)
    return [{"action": "RESTATE_RANGE", "family": "B1-02", "zone": ZONE, "element_id": was["element_id"],
             "evidence_status": "HELD", "low": line[0], "high": line[1], "was_low": was["low"],
             "was_high": was["high"], "given_up_m2": given,
             "basis": (f"R-T497-1 own plan, dig order {' > '.join(s['dig_order'])}: T-484 strip "
                       f"{s['reproduced_t484']['strip_total_m2']} m2 less every earlier zone, in plot "
                       f"{do['trench_in_plot_m2']} m2, beyond the plot line {do['trench_beyond_plot_m2']} m2, x "
                       f"{s['depths_m']['trench']} (low end in plot only); F10F drawn-outline scenario (the F10F "
                       f"line's high end); Checker F-C-T350R4-1 AGREE exactly"),
             "held_items": f"plot-line clip S06 / D-14 ({beyond} m3 beyond the plot); working space HELD",
             "scenarios_beside": (f"other S02 F10F readings {lo_o} .. {hi_o} m3 (residual up to "
                                  f"{res['in plot, F10F reading other than the drawn outline (up to)']} in plot, "
                                  f"{res['with beyond plot (up to)']} with beyond-plot); V3.0.48 {was['low']} .. "
                                  f"{was['high']} and r2 route-G 1.391722 .. 1.418002 counted F10F / pits ground: "
                                  f"superseded"),
             "source_tasks": ["F-C-T350R4-1", "T-484"]}]


def build(project_id=None):
    from engine.source import arch_v3050 as A
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id,
            "sources": [SOURCES[k] for k in ("F-C-T350R4-1", "T-484")], "zones": zones()}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(d["zones"], indent=1))
