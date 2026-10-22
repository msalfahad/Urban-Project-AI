"""T-167 read-only run: ARCH_TAKEOFF_V3.0.4 on the development villa's Drive copies (the architectural DXF from
P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"). Every output goes to --out (outside the repository);
printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    python3 -I research/agents_t167/v304_run.py <plan.dxf> <structural.dxf> --out <scratch>/t167 \
        [--reuse <dir holding v29 / v210 .. v212 of a run with the M4 profile>] \
        [--restricted <dir of a finished T-151 v303_run.py run on profile_st7757_q17a.json>] \
        [--single KEY=<dir of a finished T-151 v303_run.py run on the M4 profile minus KEY> ...]

Steps:
  1. RESTRICTED comparison run: the V3.0.3 candidate (research/agents_t151/v303_run.py, unchanged) on the Q-17 A
     profile research/agents_t167/profile_st7757_q17a.json (unless --restricted gives a finished one);
  2. --single runs (optional, attribution only): the V3.0.3 candidate on the M4 profile minus one value;
  3. the V3.0.4 run (tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.4) on the M4 profile with --v304-inputs
     naming the project data file research/urban_engine_m4_correctness/project_data_st7757_t064.json, the T-044 audit
     classes and the comparison runs; the V3.0.3 inputs, decisions and history runs as T-151.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t131", ROOT / "research" / "agents_t142", ROOT / "research" / "agents_t151"):
    sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402
import t151_ledgers as LG       # noqa: E402
import v302_run as T142         # noqa: E402
import v303_run as T151         # noqa: E402

M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
Q17A = HERE / "profile_st7757_q17a.json"
DATA = ROOT / "research/urban_engine_m4_correctness/project_data_st7757_t064.json"
# research/agents_t044/T-044_PROFILE_AUDIT.md (r2) class of each value the data file does not make usable
AUDIT_CLASSES = {"FOUNDING_DEPTH_M": "PRINTED as a minimum (excavation level, base / low 1.50); high NOT_PRINTED; "
                                     "owner Q-21 C: founding datum unresolved",
                 "CB_SUPPORT_BAR_EXTENT_FRAC": "DIFFERENT (0.22 Ln and 0.3 Ln2 both printed)",
                 "CB_SUPPORT_BAR_SPAN_BASIS": "NOT_PRINTED (Ln carries no axis / face note)"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reuse", help="an earlier run directory holding v29 / v210 / v211 / v212 (M4 profile)")
    ap.add_argument("--restricted", help="a finished T-151 run on profile_st7757_q17a.json")
    ap.add_argument("--single", nargs="*", default=[], metavar="KEY=DIR")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if a.restricted:
        rdir = Path(a.restricted).resolve()
    else:
        rdir = out / "restricted"
        T151.main([a.plan, a.structural, "--out", str(rdir), "--profile", str(Q17A)]
                  + (["--reuse", a.reuse] if a.reuse else []))
    runs = [{"id": "RESTRICTED", "removed_keys": sorted(AUDIT_CLASSES), "profile": str(Q17A),
             "lines": str(rdir / "v303" / "V3_0_3_BOQ_LINES.json")}]
    for s in a.single:
        k, _, d = s.partition("=")
        if k not in AUDIT_CLASSES:
            raise SystemExit(f"--single {k}: one of {sorted(AUDIT_CLASSES)}")
        d = Path(d).resolve()
        runs.append({"id": f"MINUS_{k}", "removed_keys": [k], "profile": str(d / "profile_used.json"),
                     "lines": str(d / "v303" / "V3_0_3_BOQ_LINES.json")})
        if not (d / "profile_used.json").exists():
            prof = json.loads(M4.read_text(encoding="utf-8"))
            prof["conventions"] = [c for c in prof["conventions"] if c["id"] != k]
            (d / "profile_used.json").write_text(json.dumps(prof, indent=1), encoding="utf-8")
    (out / "v304_inputs.json").write_text(json.dumps({
        "schema": "URBAN_V304_PROFILE_AUDIT_FILES_V1", "project": T131.PID, "data_file": str(DATA),
        "audit_classes": AUDIT_CLASSES, "runs": runs}, indent=1), encoding="utf-8")
    src = Path(a.reuse).resolve() if a.reuse else out
    a.profile = str(M4)
    (out / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = T131.common_args(a, out)
    if not a.reuse:     # the released V2.9 and the V2.10 .. V2.12 history runs on the M4 profile, as T-151
        for m in ("ARCH_TAKEOFF_V2.9", "ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
            M.main(["arch", "--out", str(out / ("v" + m.split("_V")[-1].replace(".", ""))), "--method", m] + common)
    hist = [f"{m}={src / ('v' + m.split('_V')[-1].replace('.', '')) / 'BOQ_LINES.json'}"
            for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12")]
    (out / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    (out / "v302_inputs.json").write_text(json.dumps(T142.INPUTS, ensure_ascii=False), encoding="utf-8")
    (out / "v303_inputs.json").write_text(json.dumps(LG.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    extra = ["--v30-released", str(src / "v29" / "BOQ_LINES.json"), "--v30-history"] + hist + [
        "--v30-decisions", str(out / "decisions.json"), "--v302-inputs", str(out / "v302_inputs.json"),
        "--v303-inputs", str(out / "v303_inputs.json"), "--v304-inputs", str(out / "v304_inputs.json")]
    M.main(["arch", "--out", str(out / "v304"), "--method", "ARCH_TAKEOFF_V3.0.4"] + common + extra)
    run = json.loads((out / "v304" / "V3_0_4_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1))
    print("evidence status:", run["evidence_status_counts"])
    lg = run["piece_logs"][0]
    print("removed:", lg.get("removed_keys"), "held:", lg.get("lines_held"))
    print("by cause:", json.dumps(lg.get("by_cause"), indent=1))
    print("restricted only:", len(lg.get("restricted_only") or ()), "no quantity in V3.0.3:",
          len(lg.get("no_quantity_in_v3_0_3") or ()))
    for k, v in run["totals_moved_by_code"].items():
        print(f"{k:28s} V3.0.3 {v['v3_0_3']} | V3.0.4 {v['v3_0_4']}")
    return 0


if __name__ == "__main__":
    main()
