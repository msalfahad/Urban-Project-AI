"""T-717 read-only run: ARCH_TAKEOFF_V3.0.74 (FINISH_GATE_B_V2, R-T717-1) on the candidate V3.0.73 (T-722, Gate B PASS).
Exactly research/agents_t722/v3073_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_72 =
f9578744), with --method ARCH_TAKEOFF_V3.0.74 and --v3074-inputs (t717_inputs.py: the merged T-701 / T-702 / T-709 /
T-719 ledgers and the T-723 map, sha-pinned, each ledger rebuilt by its own builder) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-717 research/agents_t717/v3074_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t717 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_73 of this run must be the T-722 run of record (asserted by its line index: research/agents_t722/out/
LINE_INDEX_V3_0_73.json names the lines sha). The second T-723 band prerequisite (the GF-08 region carries the GF
wall face under the 1F well wall) is checked here on the run's own room regions: the face, read by handle from the plan
DXF, must lie on the boundary of the GF room that carries the V-01 double height, with that room on the well side
(REGION_CHECK on the run's own V2.9 rooms; a FAIL fails the run: no run of record carries the bands). Every output goes to --out (outside the repository);
printed: item codes, units, states, quantities, handles and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", ROOT / "research" / "agents_t677", ROOT / "research" / "agents_t672",
          ROOT / "research" / "agents_t687", ROOT / "research" / "agents_t693", ROOT / "research" / "agents_t704",
          ROOT / "research" / "agents_t703", ROOT / "research" / "agents_t722", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3073_run as R73  # noqa: E402  (T-722; imports T-703's v3072_run and the whole chain)
import t717_inputs as L74  # noqa: E402

INDEX73 = ROOT / "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
FACE = "336"                 # the GF wall face in the plane of the 1F well wall (T-709 R-T709-1, Checker re-read)
VOID = "V01"                 # the engine's double-height id of the ST-02 light well (T-719 V-01)
TOL_MM = 30.0                # face-on-boundary tolerance (wall face line vs region edge)


def region_check(plan_dxf, rooms_json):
    """-> dict: the face by handle lies on the boundary of the ONE GF room carrying the V01 double height, the room on
    the well side (a probe 0.10 m off the face's midpoint, toward the void centroid side, is inside; the other side
    is not). Coordinates stay in memory."""
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon
    e = ezdxf.readfile(plan_dxf).entitydb.get(FACE)
    if e is None or e.dxftype() != "LINE":
        raise SystemExit(f"REGION_CHECK: handle {FACE} is not a LINE on the plan")
    a, b = (float(e.dxf.start[0]), float(e.dxf.start[1])), (float(e.dxf.end[0]), float(e.dxf.end[1]))
    seg = LineString([a, b])
    rooms = json.loads(Path(rooms_json).read_text(encoding="utf-8"))["rooms"]
    dh = [r for r in rooms if r.get("floor") == "GF" and any((x or {}).get("void_id") == VOID
                                                              for x in r.get("double_height") or ())]
    if len(dh) != 1:
        raise SystemExit(f"REGION_CHECK: {len(dh)} GF rooms carry {VOID} (expected 1)")
    r = dh[0]
    P = Polygon(r["polygon"]).buffer(0)
    on = seg.intersection(P.exterior.buffer(TOL_MM)).length
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / n, dx / n
    s1, s2 = P.contains(Point(mx + 100 * nx, my + 100 * ny)), P.contains(Point(mx - 100 * nx, my - 100 * ny))
    ok = abs(on - seg.length) <= 1.0 and s1 != s2
    return {"face": FACE, "face_m": round(seg.length / 1000, 3), "room": r["room_id"],
            "room_area_m2": round(r["area_m2"], 3), "double_height_m2": r.get("double_height_m2"),
            "on_boundary_m": round(on / 1000, 3), "room_one_side_only": s1 != s2, "state": "PASS" if ok else "FAIL"}


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-722 v3073_run, re-pointed at V3.0.74 (same inputs + --v3074-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.73", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.74"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3074_inputs.json"
        L74.rebuild_ledgers()
        f.write_text(json.dumps(L74.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3074-inputs", str(f)])
    M.main = hub
    try:
        R73.main(argv)        # its own wrappers re-point V3.0.72 -> .73 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    rooms = d / "ARCH_ROOMS.json"
    if not rooms.exists():
        cand = sorted(Path(d).parent.rglob("ARCH_ROOMS.json"))
        rooms = cand[0] if cand else None
    rc = region_check(argv[0], rooms)
    print("region check:", json.dumps(rc, sort_keys=True))
    if rc["state"] != "PASS":
        raise SystemExit("REGION_CHECK FAIL: this run is not a run of record (T-723 band prerequisite 2)")
    b73 = hashlib.sha256((d / "V3_0_73_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_74_BOQ_LINES.json").read_bytes()).hexdigest()
    want = json.loads(INDEX73.read_text(encoding="utf-8"))["inputs"]["lines"]
    if b73 != want:
        raise SystemExit(f"V3_0_73 {b73[:8]} is not the T-722 run of record {want[:8]} (its line index)")
    run = json.loads((d / "V3_0_74_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_73", b73[:8], "lines", ident["base_lines"], "-> V3_0_74_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_74_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "finishes",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: round(v["v3_0_74"][f] - (v["base"] or {}).get(f, 0), 6)
                                           for f in ("released", "held_low", "held_high", "lines", "bounded_lines",
                                                     "blocked_lines")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    for code in sorted(ident["fin_census_after"]):
        print("census", code, "before", json.dumps(ident["fin_census_before"][code], sort_keys=True))
        print("census", code, "after ", json.dumps(ident["fin_census_after"][code], sort_keys=True))
    for r in json.loads((d / "V3_0_74_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["piece"], r["action"], r["line_id"], r["item_code"], r["element_id"], "| after",
              (r["after_v3_0_74"] or {}).get("low"), (r["after_v3_0_74"] or {}).get("high"), "| was",
              (r["before_base"] or {}).get("low"), (r["before_base"] or {}).get("high"),
              (r["before_base"] or {}).get("value"), "| host", r.get("host_line_id"), "|", r.get("flag") or "",
              "|", " -> ".join(str(x) for x in r["class"]))
    return 0


if __name__ == "__main__":
    main()
