"""S6 reproductions of the DWG admission path with a FAKE converter (fakebin/dwg2dxf) on PATH.

usage: python3 -I s6_repro_dwg.py REPO WORK_DIR FAKEBIN
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

REPO, WORK, FAKE = (Path(a).resolve() for a in sys.argv[1:4])
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

ENV = dict(os.environ, PATH=str(FAKE) + os.pathsep + os.environ.get("PATH", ""))
CLI = [sys.executable, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fake_dwg(path, mode, dxf=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"AC1032\n{mode}\n{dxf}\n", encoding="ascii")
    return path


def run(args, out):
    p = subprocess.run(CLI + args + ["--out", str(out), "--method", "ARCH_TAKEOFF_V1", "--no-svg"],
                       capture_output=True, text=True, env=ENV, cwd=str(WORK))
    rec = {"exit": p.returncode, "traceback": "Traceback (most recent" in p.stderr,
           "stderr_tail": p.stderr.strip().splitlines()[-1:]}
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
    r4 = run(["--drawings", str(a), "--structural", str(b)], WORK / "d4" / "out")
    r4["plan_read_is_A"] = r4.get("read_sha") == res["fixtures"]["A"]
    r4["plan_read_is_B_structural"] = r4.get("read_sha") == res["fixtures"]["B"]
    res["D4_same_stem"] = r4
    (WORK / "S6_REPRO_DWG.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, json.dumps(v)[:600])


if __name__ == "__main__":
    main()
