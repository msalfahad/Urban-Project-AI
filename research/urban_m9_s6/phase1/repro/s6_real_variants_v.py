"""Apply the S6 metamorphic transforms to a PRIVATE plan drawing and run the production CLI on each (counts only).

usage: S6_METHOD=... python3 -I s6_real_variants_v.py REPO PLAN.dxf WORK_DIR
The drawing and every output stay outside the repository; the summary keeps counts and areas only.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

REPO, PLAN, WORK = (Path(a).resolve() for a in sys.argv[1:4])
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from ezdxf.math import Matrix44                               # noqa: E402

METHOD = os.environ.get("S6_METHOD", "ARCH_TAKEOFF_V1")
CLI = [sys.executable, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch", "--method", METHOD, "--no-svg",
       "--no-m9-xlsx"]


def v_base(doc):
    return doc


def v_metres(doc):
    f = {4: 0.001, 5: 0.01, 6: 1.0}[int(doc.header.get("$INSUNITS", 4) or 4)]
    m = Matrix44.scale(f, f, f)
    for e in list(doc.modelspace()):
        e.transform(m)
    doc.header["$INSUNITS"] = 6
    return doc


def v_nested2(doc):
    msp = doc.modelspace()
    b1, b2 = doc.blocks.new("S6_WRAP_L1"), doc.blocks.new("S6_WRAP_L2")
    for e in list(msp):
        msp.move_to_layout(e, b1)
    b2.add_blockref("S6_WRAP_L1", (0, 0), dxfattribs={"layer": "0"})
    msp.add_blockref("S6_WRAP_L2", (0, 0), dxfattribs={"layer": "0"})
    return doc


def v_frames_exploded(doc):
    msp = doc.modelspace()
    for e in list(msp):
        if e.dxftype() == "LWPOLYLINE" and e.closed and len(e) == 4:
            pts = [tuple(p[:2]) for p in e.get_points()]
            xs, ys = sorted({round(p[0], 3) for p in pts}), sorted({round(p[1], 3) for p in pts})
            if len(xs) == 2 and len(ys) == 2 and min(xs[1] - xs[0], ys[1] - ys[0]) > 5000:
                for i in range(4):
                    msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": e.dxf.layer})
                msp.delete_entity(e)
    return doc


VARIANTS = {"base": v_base, "metres": v_metres, "nested2": v_nested2, "frames_exploded": v_frames_exploded}


def summary(out, p):
    s = {"exit": p.returncode, "traceback": "Traceback (most recent" in p.stderr}
    if (out / "DRAWING_DISCOVERY.json").exists():
        D = json.loads((out / "DRAWING_DISCOVERY.json").read_text())
        s["stopping"] = D["gates"].get("stopping")
        s["review_flags"] = sorted({f["code"] for v in D["stages"].values() for f in v["findings"]
                                    if f["level"] in ("REVIEW_REQUIRED", "BLOCKED_ITEM")})
        s["column_evidence"] = D["stages"]["6_geometry_readiness"].get("column_evidence")
    if (out / "FINISH_COVERAGE.json").exists():
        s["coverage"] = {f["floor"]: f["gate"] for f in json.loads((out / "FINISH_COVERAGE.json").read_text())["floors"]}
    if not (out / "ARCH_PLAN.json").exists():
        return s
    P = json.loads((out / "ARCH_PLAN.json").read_text())
    R = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    L = json.loads((out / "BOQ_LINES.json").read_text())
    L = L["lines"] if isinstance(L, dict) else L
    FA = {f["floor"]: f for f in json.loads((out / "ARCH_FLOOR_AREAS.json").read_text())["floors"]}
    s["lines"] = len(L)
    s["regions"] = {}
    for reg in P["regions"]:
        rr = [r for r in R if r.get("region_id") == reg["region_id"]]
        s["regions"][reg["floor"]] = {
            "state": reg["stage_state"], "columns": reg.get("columns"), "openings": reg.get("openings"),
            "door_symbols": reg.get("door_symbols"), "plate_m2": round((reg.get("plate") or {}).get("largest_m2") or 0, 2),
            "rooms": len(rr), "room_classes": {c: sum(1 for r in rr if r["class"] == c) for c in sorted({r["class"] for r in rr})},
            "room_area_m2": round(sum(r["area_m2"] or 0 for r in rr), 2),
            "unallocated_m2": round(sum(v for k, v in (FA.get(reg["floor"], {}).get("categories_m2") or {}).items()
                                        if k.startswith("UNALLOCATED")), 3)}
    return s


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, fn in VARIANTS.items():
        d = WORK / name
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
        dxf = d / "plan.dxf"
        doc = ezdxf.readfile(str(PLAN))
        from ezdxf.entities import DXFTagStorage
        msp = doc.modelspace()
        raw = [e for e in msp if isinstance(e, DXFTagStorage)]
        kinds = sorted({e.dxftype() for e in raw})
        for e in raw:
            msp.delete_entity(e)
        doc = fn(doc)
        doc.saveas(str(dxf))
        p = subprocess.run(CLI + ["--drawings", str(dxf), "--out", str(d / "out")], capture_output=True, text=True,
                           cwd=str(WORK))
        (d / "stderr.txt").write_text(p.stderr)
        res[name] = summary(d / "out", p)
        res[name]["removed_untransformable"] = {"count": len(raw), "types": kinds}
        print(name, json.dumps(res[name]), flush=True)
    (WORK / "S6_REAL_VARIANTS.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
