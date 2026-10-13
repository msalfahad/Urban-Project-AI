"""S6 reproductions of the DWG admission path with a FAKE converter (fakebin/dwg2dxf) on PATH.

usage: S6_METHOD=... [S6_EXTRA=--strict-admission] python3 -I s6_repro_dwg_v.py REPO WORK_DIR FAKEBIN

(S6 Phase 1 version of research/urban_m9_s6/repro/s6_repro_dwg.py: method from the environment; D4 gives the
structural run an explicit conventions profile under V2; D5 / D6 added; the stopping findings are recorded.)
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

REPO, WORK, FAKE = (Path(a).resolve() for a in sys.argv[1:4])
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

ENV = dict(os.environ, PATH=str(FAKE) + os.pathsep + os.environ.get("PATH", ""))
CLI = [sys.executable, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch"]
METHOD = os.environ.get("S6_METHOD", "ARCH_TAKEOFF_V1")
EXTRA = os.environ.get("S6_EXTRA", "").split()
V6 = str(REPO / "engine" / "profiles" / "URBAN_M8_GENERIC_CONVENTIONS_V6.json")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fake_dwg(path, mode, dxf=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"AC1032\n{mode}\n{dxf}\n", encoding="ascii")
    return path


def run(args, out):
    p = subprocess.run(CLI + args + ["--out", str(out), "--method", METHOD, "--no-svg", "--no-m9-xlsx"] + EXTRA,
                       capture_output=True, text=True, env=ENV, cwd=str(WORK))
    rec = {"exit": p.returncode, "traceback": "Traceback (most recent" in p.stderr,
           "stderr_tail": p.stderr.strip().splitlines()[-1:]}
    for name in ("ADMISSION_BLOCKED.json", "COMPLETENESS_FAILED.json"):
        if (out / name).exists():
            B = json.loads((out / name).read_text())
            rec["blocked"] = {"file": name, "stopping": [f["code"] for f in B["stopping_findings"]],
                              "superseded": (B.get("superseded_earlier_outputs") or {}).get("moved_to")}
    if (out / "DRAWING_DISCOVERY.json").exists():
        D = json.loads((out / "DRAWING_DISCOVERY.json").read_text())
        rec["warnings"] = sorted({f["code"] for v in D["stages"].values() for f in v["findings"]
                                  if f["level"] == "WARNING"})
    rec["outputs_now"] = sorted(x.name for x in out.iterdir()) if out.exists() else []
    plan = out / "ARCH_PLAN.json"
    if plan.exists():
        P = json.loads(plan.read_text())
        L = json.loads((out / "BOQ_LINES.json").read_text())
        rec.update(read_sha=P["run"]["drawing"]["sha256"], regions=[r["floor"] for r in P["regions"]],
                   lines=len(L["lines"] if isinstance(L, dict) else L),
                   conversions=[{k: c.get(k) for k in ("dwg", "state", "pin_status", "dxf_sha256", "returncode")}
                                for c in P["run"].get("dwg_conversions") or ()])
    return rec


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    villa = WORK / "src" / "villa_A.dxf"
    villa.parent.mkdir(parents=True)
    AS.villa(str(villa))
    other = WORK / "src" / "villa_B_mirrored.dxf"
    AS.villa(str(other), mirror=True, dx=500.0)
    empty = WORK / "src" / "empty.dxf"
    d = ezdxf.new("R2018"); d.header["$INSUNITS"] = 4; d.saveas(str(empty))
    res = {"fixtures": {"A": sha(villa), "B": sha(other), "EMPTY": sha(empty)}}

    # D1 a converter that produces a valid DXF with no entities
    res["D1_empty_conversion"] = run(["--drawings", str(fake_dwg(WORK / "d1" / "plan.dwg", "COPY", empty))],
                                     WORK / "d1" / "out")
    # D2 a converter that exits 0 and writes nothing, after an earlier run into the same OUT
    o2 = WORK / "d2" / "out"
    first = run(["--drawings", str(fake_dwg(WORK / "d2" / "rev1" / "plan.dwg", "COPY", villa))], o2)
    second = run(["--drawings", str(fake_dwg(WORK / "d2" / "rev2" / "plan.dwg", "SILENT"))], o2)
    res["D2_stale_conversion"] = {"rev1": first, "rev2_converter_wrote_nothing": second,
                                  "rev2_read_rev1_drawing": second.get("read_sha") == first.get("read_sha")}
    # D3 a converter that writes garbage
    res["D3_garbage_conversion"] = run(["--drawings", str(fake_dwg(WORK / "d3" / "plan.dwg", "GARBAGE"))],
                                       WORK / "d3" / "out")
    # D4 the plan and the structural drawing have the same file name (different folders)
    a = fake_dwg(WORK / "d4" / "arch" / "villa.dwg", "COPY", villa)
    b = fake_dwg(WORK / "d4" / "struct" / "villa.dwg", "COPY", other)
    conv = ["--conventions", V6] if METHOD == "ARCH_TAKEOFF_V2" else []
    r4 = run(["--drawings", str(a), "--structural", str(b)] + conv, WORK / "d4" / "out")
    r4["plan_read_is_A"] = r4.get("read_sha") == res["fixtures"]["A"]
    r4["plan_read_is_B_structural"] = r4.get("read_sha") == res["fixtures"]["B"]
    res["D4_same_stem"] = r4
    # D5 the structural drawing without an explicit conventions profile
    res["D5_structural_without_conventions"] = run(["--drawings", str(a), "--structural", str(b)], WORK / "d5" / "out")
    # D6 the same file given as the plan and as the structural drawing
    res["D6_plan_is_structural"] = run(["--drawings", str(a), "--structural", str(a)] + conv, WORK / "d6" / "out")
    (WORK / "S6_REPRO_DWG.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, json.dumps(v)[:600])


if __name__ == "__main__":
    main()
