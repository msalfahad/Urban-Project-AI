"""ALSENAN PHASE B2A.1 - self-contained package URBAN_QTO_ALSENAN_PHASE_B2A1_GENERIC_QA_PATCH.

The ZIP carries its canonical freeze (ALSENAN_PHASE_B2A1_FREEZE.json), the parent B2A freeze, every B2A.1 register,
the Alsenan and Qortuba regression records, the B2A engine sources, the one full-suite junit, the workbook and a
stdlib verify.py: the package verifies without GitHub access (python3 verify.py).

    python3 research/external_engine_lab/alsenan_b2a1_package.py <out_dir> <junit.xml> <rc> <head>
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import alsenan_b2a_registers as REGS                                                                # noqa: E402

REG = ROOT / "tests/alsenan/registers_b2a1"
PARENT = ROOT / "tests/alsenan/registers_b2a/ALSENAN_PHASE_B2A_FREEZE.json"
RECOMMENDATION = ROOT / "research/external_engine_lab/alsenan_phase_b2a1_recommendation.json"
NAME = "URBAN_QTO_ALSENAN_PHASE_B2A1_GENERIC_QA_PATCH"
FREEZE = "ALSENAN_PHASE_B2A1_FREEZE.json"
NOT_CANONICAL = ("ALSENAN_PHASE_B2A1_REGISTER_FREEZE", "QORTUBA_REGRESSION", "ALSENAN_REGRESSION")

VERIFY = r'''"""Verify this package offline (stdlib only): python3 verify.py  -> exit 0 when every check passes."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
canon = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
fz = json.loads((HERE / "ALSENAN_PHASE_B2A1_FREEZE.json").read_text())
man = json.loads((HERE / "MANIFEST.json").read_text())
checks = {}
checks["manifest_files"] = all((HERE / f).exists() and sha(HERE / f) == m["sha256"] for f, m in man["files"].items())
checks["freeze_in_manifest"] = man["files"]["ALSENAN_PHASE_B2A1_FREEZE.json"]["sha256"] == sha(HERE / "ALSENAN_PHASE_B2A1_FREEZE.json")
checks["register_files"] = all(sha(HERE / f) == h for f, h in fz["register_file_sha256"].items())
rf = json.loads((HERE / fz["register_freeze"]["file"]).read_text())
checks["register_freeze_file"] = sha(HERE / fz["register_freeze"]["file"]) == fz["register_freeze"]["sha256"]
checks["canonical_register_digests"] = all(
    canon(json.loads((HERE / "registers" / f"{n}.json").read_text())) == d
    for n, d in rf["register_digests"].items() if n not in fz["not_canonical"])
checks["parent_b2a_freeze"] = (sha(HERE / fz["parent_b2a_freeze"]["file"]) == fz["parent_b2a_freeze"]["sha256"]
                               == rf["parent_b2a_freeze"]["sha256"])
checks["engine_sources"] = all(sha(HERE / "engine_source" / f"{m}.py") == h for m, h in fz["engine_sha256"].items()) \
    and fz["engine_sha256"] == rf["b2a_engine_sha256"]
for k in ("alsenan_regression", "qortuba_regression", "xlsx", "recommendation", "junit"):
    checks[k] = sha(HERE / fz[k]["file"]) == fz[k]["sha256"]
checks["alsenan_regression_state"] = json.loads((HERE / fz["alsenan_regression"]["file"]).read_text())["state"] == "PASS"
checks["qortuba_regression_state"] = json.loads((HERE / fz["qortuba_regression"]["file"]).read_text())["state"] in ("UNCHANGED", "PROVENANCE_ONLY")
checks["xlsx_matches_register_freeze"] = fz["xlsx"]["sha256"] == rf["xlsx"]["file_sha256"]
t = ET.parse(HERE / fz["junit"]["file"]).getroot()
s = t if t.tag == "testsuite" else t.find("testsuite")
tr = fz["test_result"]
checks["junit_counts"] = (int(s.get("tests")), int(s.get("failures")), int(s.get("errors"))) == (tr["tests"], tr["failures"], tr["errors"])
checks["suite_green"] = tr["exit_code"] == 0 and tr["failures"] == 0 and tr["errors"] == 0
checks["benchmark_closed"] = rf["BENCHMARK_OPENED"] is False
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
ok = all(checks.values())
print("VERIFY", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
'''


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def junit(path, rc):
    t = ET.parse(path).getroot()
    s = t if t.tag == "testsuite" else t.find("testsuite")
    a = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    xf = sum(1 for c in s.iter("testcase") for k in c if k.tag == "skipped" and "xfail" in (k.get("type", "") + k.get("message", "")))
    return {"tests": a["tests"], "failures": a["failures"], "errors": a["errors"], "skipped_total": a["skipped"],
            "xfailed": xf, "skipped": a["skipped"] - xf, "passed": a["tests"] - a["failures"] - a["errors"] - a["skipped"],
            "exit_code": int(rc), "time_s": float(s.get("time", 0))}


def md(regs, tr, head) -> dict:
    rf = regs["ALSENAN_PHASE_B2A1_REGISTER_FREEZE"]
    st, cu = regs["STAIR_REGISTER"], regs["CURVED_OPENING_REGISTER"]
    al, qo = regs["ALSENAN_REGRESSION"], regs["QORTUBA_REGRESSION"]
    M = {}
    M["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan Phase B2A.1 - generic QA patch

Head `{head}`; code commit `{rf['code_commit']}`; parent B2A freeze sha256 `{rf['parent_b2a_freeze']['sha256']}`.

- Stair engine STAIR_CONCRETE_V2: riser and tread counts are independent inputs; any missing count or dimension
  blocks; tread = riser - 1 only on a stated SOURCE_ESTABLISHED relation. Alsenan stair: **{st['result']['state']}**.
- Curved bases: MIN_RADIUS_ARC / MID_BAND_ARC / MAX_RADIUS_ARC / CHORD; ROOM_SIDE / EXTERIOR_SIDE only where a probe
  establishes them; INNER / CENTRE / OUTER are aliases only. Commercial default: MIN_RADIUS_ARC (unchanged lengths).
- Alsenan regression vs frozen B2A: **{al['state']}** ({al['registers_compared']} registers; unchanged
  {len(al['unchanged'])}; schema / terminology only {len(al['schema_only'])}; failed {al['failed']}).
- Qortuba RC1 regression: **{qo['state']}** ({qo['identical']}/{qo['registers']} identical; changed {qo['changed']}).
- Full suite (one run, final commit): {tr['passed']} passed / {tr['failures']} failed / {tr['errors']} errors /
  {tr['skipped']} skipped / {tr['xfailed']} xfailed, exit {tr['exit_code']}.
- This package carries its canonical freeze ({FREEZE}); run `python3 verify.py` to verify it offline.

NO BENCHMARK CALIBRATION. NO NEW ALSENAN OWNER ASSUMPTIONS. NO PRICING. NO PRODUCTION MIGRATION.
"""
    k, u = st["known_inputs"], st["unknown_inputs"]
    M["01_STAIR_COUNT_MODEL"] = """# Stair count model (STAIR_CONCRETE_V2)

Previous defect: STAIR_CONCRETE_V1 took one count and used it for the horizontal run and for the step wedges, so the
tread count was silently equal to the riser count. No Alsenan quantity came from it (the stair was blocked).

Flight inputs (each with an authority; CANDIDATE / UNKNOWN never computes): RISER_COUNT, TREAD_COUNT, RISER_HEIGHT,
TREAD_GOING, FLIGHT_WIDTH, WAIST_THICKNESS. Landing: area, thickness. Stair beams are separate structural elements.

    VERTICAL_RISE  = RISER_COUNT x RISER_HEIGHT
    HORIZONTAL_RUN = TREAD_COUNT x TREAD_GOING
    SLOPING_LENGTH = sqrt(rise^2 + run^2)
    WAIST          = SLOPING_LENGTH x FLIGHT_WIDTH x WAIST_THICKNESS
    STEP_WEDGES    = 0.5 x RISER_HEIGHT x TREAD_GOING x FLIGHT_WIDTH x TREAD_COUNT
    LANDINGS       = LANDING_AREA x LANDING_THICKNESS

## Alsenan (stays BLOCKED)

Known inputs:

""" + table(["input", "value", "authority"],
            [["tread going", k["tread_going_m"]["value"], k["tread_going_m"]["authority"]],
             ["flight width", k["flight_width_m"]["values"], k["flight_width_m"]["authority"]],
             ["tread count", "observed tread-line runs: " + ", ".join(f"{r['floor']}/{r['layer']}:{r['tread_lines']}"
                                                                    for r in k["observed_tread_line_runs"]),
              k["tread_count"]["authority"] + " - " + k["tread_count"]["why"]]]) + "\n\nUnknown inputs:\n\n" + table(
        ["input", "why"], [[n, w] for n, w in u.items()]) + f"\n\nResult: {st['result']['state']}; volume {st['result']['volume_m3']}.\n"
    rows = []
    for r in cu["rows"]:
        b, o = r["bases_m"], r["orientation"]
        rows.append([r["id"], b["MIN_RADIUS_ARC"], b["MID_BAND_ARC"], b["MAX_RADIUS_ARC"], b["CHORD"], o["state"],
                     o.get("room_side"), r["commercial_basis"], r["commercial_m"]])
    M["02_CURVED_BASIS_TERMINOLOGY"] = """# Curved basis terminology (CURVED_OPENING_V1_1)

Geometric bases: MIN_RADIUS_ARC, MID_BAND_ARC, MAX_RADIUS_ARC, CHORD. Semantic sides ROOM_SIDE_ARC / EXTERIOR_SIDE_ARC
are published only where a probe establishes them (300 mm inside the smallest radius and outside the largest at mid
sweep: exactly one probe in a room site and the other in no site). MIN_RADIUS_ARC is never assumed to be the room side.
Aliases only: INNER = MIN_RADIUS_ARC, CENTRE = MID_BAND_ARC, OUTER = MAX_RADIUS_ARC. Overrides: MIN_RADIUS, MID_BAND,
MAX_RADIUS, CHORD, ROOM_SIDE, EXTERIOR_SIDE (the last two blocked unless established).

""" + table(["id", "MIN_RADIUS_ARC m", "MID_BAND_ARC m", "MAX_RADIUS_ARC m", "CHORD m", "side", "room side", "commercial basis", "commercial m"], rows) + """

Observation: on both Alsenan curves the probe places the room beyond the largest radius, so the minimum-radius arc
(the commercial default, method URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1) is the exterior-side face there. The
default is kept as instructed and is named for what it is; nothing was re-selected.
"""
    M["03_ALSENAN_REGRESSION"] = "# Alsenan regression (B2A.1 vs frozen B2A)\n\nState: **" + al["state"] + "**. Rule: " + al["rule"] + ".\n\n" + table(
        ["register", "state", "classes", "changes", "added leaves"],
        [[n, v["state"], ", ".join(v.get("classes", [])), v.get("change_count"), v.get("added_leaves")] for n, v in sorted(al["per_register"].items())]) + "\n"
    M["04_QORTUBA_REGRESSION"] = (f"# Qortuba RC1 regression\n\nState: **{qo['state']}**; registers {qo['registers']}; identical "
                                  f"{qo['identical']}; changed {qo['changed']}; extra {qo['extra']}.\n\nQortuba is RC1_REFERENCE: no file "
                                  "edited, no Qortuba-specific code, no quantity changed.\n")
    M["05_FREEZE_AND_VERIFY"] = f"""# Freeze and offline verification

- `{FREEZE}` (package root) is the canonical freeze of this patch: parent B2A freeze digest, code commit, engine
  digests, register digests (file and canonical), the full-suite result, the Alsenan and Qortuba regression digests.
- `parent/ALSENAN_PHASE_B2A_FREEZE.json` is the parent freeze itself; `registers/` holds every B2A.1 register;
  `engine_source/` the B2A engines; `FINAL_JUNIT.xml` the one full-suite run.
- `python3 verify.py` recomputes every digest with the standard library and exits 0 only when all checks pass. No
  GitHub access is needed.
"""
    M["06_TEST_RESULTS"] = "# Test results\n\n```json\n" + json.dumps(tr, indent=1) + "\n```\n\nSynthetic: tests/alsenan/test_b2a_engines_synthetic.py; frozen registers: tests/alsenan/test_alsenan_b2a_real.py, tests/alsenan/test_alsenan_b2a1_real.py.\n"
    return M


def main(out, junit_path, rc, head):
    out = Path(out) / NAME
    if out.exists():
        shutil.rmtree(out)
    for d in ("registers", "parent", "engine_source"):
        (out / d).mkdir(parents=True)
    regs = {p.stem: json.loads(p.read_text()) for p in sorted(REG.glob("*.json"))}
    rf = regs["ALSENAN_PHASE_B2A1_REGISTER_FREEZE"]
    tr = junit(junit_path, rc)
    for p in sorted(REG.glob("*.json")):
        shutil.copy(p, out / "registers" / p.name)
    shutil.copy(PARENT, out / "parent" / PARENT.name)
    for m in rf["b2a_engine_sha256"]:
        shutil.copy(ROOT / "engine/source" / f"{m}.py", out / "engine_source" / f"{m}.py")
    shutil.copy(RECOMMENDATION, out / RECOMMENDATION.name)
    shutil.copy(junit_path, out / "FINAL_JUNIT.xml")
    model = REGS.workbook(regs)
    x = REGS.write_xlsx(model, out / REGS.XLSX_NAME)
    rb = REGS.readback(out / REGS.XLSX_NAME, model)
    for n, t in md(regs, tr, head).items():
        (out / f"{n}.md").write_text(t)
    (out / "verify.py").write_text(VERIFY)
    f = lambda p: {"file": p, "sha256": sha(out / p)}
    fz = {"SCHEMA": "URBAN_ALSENAN_PHASE_B2A1_FREEZE_V1", "phase": "ALSENAN_PHASE_B2A1_GENERIC_QA_PATCH",
          "code_commit": rf["code_commit"], "head": head,
          "parent_b2a_freeze": f("parent/" + PARENT.name),
          "register_freeze": f("registers/ALSENAN_PHASE_B2A1_REGISTER_FREEZE.json"),
          "engine_sha256": rf["b2a_engine_sha256"],
          "register_file_sha256": {f"registers/{p.name}": sha(p) for p in sorted((out / "registers").glob("*.json"))},
          "canonical_register_digests": rf["register_digests"], "not_canonical": list(NOT_CANONICAL),
          "test_result": tr, "junit": f("FINAL_JUNIT.xml"),
          "alsenan_regression": dict(f("registers/ALSENAN_REGRESSION.json"), state=regs["ALSENAN_REGRESSION"]["state"]),
          "qortuba_regression": dict(f("registers/QORTUBA_REGRESSION.json"), state=regs["QORTUBA_REGRESSION"]["state"]),
          "xlsx": dict(f(REGS.XLSX_NAME), readback=rb["state"]), "recommendation": f(RECOMMENDATION.name),
          "BENCHMARK_OPENED": False, "verify": "python3 verify.py",
          "rule": "self-contained: every digest above is recomputable from the files in this package"}
    (out / FREEZE).write_text(json.dumps(fz, indent=1, ensure_ascii=False) + "\n")
    files = sorted(p for p in out.rglob("*") if p.is_file())
    man = {"package": NAME, "head": head, "files": {str(p.relative_to(out)): {"sha256": sha(p), "bytes": p.stat().st_size}
                                                    for p in files}}
    (out / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
    z = out.parent / f"{NAME}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(q for q in out.rglob("*") if q.is_file()):
            zi = zipfile.ZipInfo(f"{NAME}/{p.relative_to(out)}", date_time=(2026, 10, 3, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, p.read_bytes())
    print(json.dumps({"dir": str(out), "files": len(files) + 1, "xlsx": x["file_sha256"], "readback": rb["state"],
                      "freeze_sha256": sha(out / FREEZE), "zip": str(z), "zip_sha256": sha(z), "tests": tr}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
