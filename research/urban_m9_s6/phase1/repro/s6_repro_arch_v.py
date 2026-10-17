"""S6 Phase 1: the architectural finish defects (ARC-D2 / D3 / D4 / D7 / D8) before (V1) and after (V2), on the
synthetic villa + research/urban_m9_s2/SYNTHETIC_FACTS_S2.json, through the production CLI.

usage: python3 -I s6_repro_arch_v.py REPO WORK_DIR
"""
import json, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path

REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

FACTS = REPO / "research" / "urban_m9_s2" / "SYNTHETIC_FACTS_S2.json"


def run(dxf, out, method):
    a = [sys.executable, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch", "--method", method, "--no-svg",
         "--no-m9-xlsx", "--drawings", str(dxf), "--out", str(out), "--facts", str(FACTS)]
    p = subprocess.run(a, capture_output=True, text=True, cwd=str(WORK))
    if not (out / "BOQ_LINES.json").exists():
        return {"exit": p.returncode, "stderr": p.stderr[-400:]}
    L = json.loads((out / "BOQ_LINES.json").read_text())
    L = L["lines"] if isinstance(L, dict) else L
    U = json.loads((out / "UNRESOLVED.json").read_text())
    U = U.get("unresolved", U) if isinstance(U, dict) else U
    R = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    FA = json.loads((out / "ARCH_FLOOR_AREAS.json").read_text())["floors"]
    return {"exit": p.returncode, "L": L, "U": U, "R": R, "FA": FA}


def lines(res, rid, code):
    return [ln for ln in res["L"] if (ln.get("location") or {}).get("room_id") == rid and ln["item_code"] == code]


def unres(res, rid, code):
    return [u for u in res["U"] if u.get("room_id") == rid and str(u.get("item") or "").startswith(code)]


def judge(res):
    out = {}
    rooms = res["R"]
    wet = [r for r in rooms if r.get("kind") == "WET" and r["class"] in ("ROOM", "MIXED")]
    d2 = []
    for r in wet:
        p = lines(res, r["room_id"], "FIN.PAINT")
        d2.append({"room": "+".join(r.get("codes") or []) or r["room_id"], "paint_lines": [(x["evidence_state"],
                   x.get("measured_net")) for x in p], "paint_rfis": len(unres(res, r["room_id"], "FIN.PAINT"))})
    out["ARC-D2 finish above partial wet tile"] = {"rooms": d2, "silent": any(not x["paint_lines"] and not x["paint_rfis"]
                                                                              for x in d2)}
    st = [r for r in rooms if r.get("kind") == "STAIR"]
    d3 = []
    for r in st:
        row = {"room": "+".join(r.get("codes") or []) or r["room_id"]}
        for c in ("FIN.PLASTER", "FIN.PAINT", "FIN.SKIRTING"):
            row[c] = [(x["evidence_state"], x.get("measured_net")) for x in lines(res, r["room_id"], c)]
            row[c + "_rfis"] = len(unres(res, r["room_id"], c))
        d3.append(row)
    out["ARC-D3 stair-hall walls and skirting"] = {"rooms": d3, "silent": any(not x[c] and not x[c + "_rfis"] for x in d3
                                                                              for c in ("FIN.PLASTER", "FIN.PAINT",
                                                                                        "FIN.SKIRTING"))}
    strip_m2 = {f["floor"]: round((f.get("categories_m2") or {}).get("DOORWAY_STRIPS") or 0.0, 4) for f in res["FA"]}
    thr = [ln for ln in res["L"] if ln["item_code"] in ("ARCH.THRESHOLD", "ARCH.WINDOW_REVEAL")]
    by = defaultdict(float)
    for ln in thr:
        by[(ln["location"]["floor"], ln["item_code"])] += ln["calculation"]["inputs"]["measured_strip_m2"]
    out["ARC-D4/D8 doorway strips (thresholds, window reveals)"] = {
        "doorway_strip_m2_by_floor": strip_m2, "strip_lines": len(thr),
        "strip_lines_m2": {f"{k[0]}:{k[1]}": round(v, 4) for k, v in sorted(by.items())},
        "strip_line_states": sorted({ln["evidence_state"] for ln in thr}),
        "silent": any(v > 0 for v in strip_m2.values()) and not thr}
    return out


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    dxf = WORK / "villa.dxf"
    AS.villa(str(dxf))
    d7 = WORK / "villa_tashkeel.dxf"
    AS.villa(str(d7))
    doc = ezdxf.readfile(str(d7))
    plain = "".join(map(chr, (0x063A, 0x0631, 0x0641, 0x0629, 0x20, 0x0646, 0x0648, 0x0645)))
    marked = "".join(map(chr, (0x063A, 0x0631, 0x0651, 0x0641, 0x0629, 0x20, 0x0646, 0x0648, 0x0645)))
    n = 0
    for e in doc.modelspace().query("TEXT"):
        if e.dxf.text == plain:
            e.dxf.text = marked
            n += 1
    doc.saveas(str(d7))
    res = {}
    for m in ("ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"):
        r = run(dxf, WORK / f"out_{m}", m)
        res[m] = {"exit": r["exit"], **judge(r)}
        r7 = run(d7, WORK / f"out_tashkeel_{m}", m)
        gf = sorted(("+".join(x.get("codes") or []) or "-", x["class"], x.get("kind"), round(x["area_m2"], 3))
                    for x in r7["R"] if x["floor"] == "GF")
        base = sorted(("+".join(x.get("codes") or []) or "-", x["class"], x.get("kind"), round(x["area_m2"], 3))
                      for x in r["R"] if x["floor"] == "GF")
        space_rfis = [u["item"] for u in r7["U"] if str(u.get("item") or "").startswith(("ARCH.SPACE", "FIN.FLOOR / zone"))]
        res[m]["ARC-D7 diacritics on a room word"] = {"replaced": n, "exit": r7["exit"], "gf_rooms_same": gf == base,
                                                     "gf_rooms": gf, "space_rfis": space_rfis,
                                                     "silent": gf != base and not space_rfis}
    (WORK / "S6_REPRO_ARCH_V.json").write_text(json.dumps(res, indent=1, ensure_ascii=True))
    for m, v in res.items():
        print("==", m, "exit", v["exit"])
        for k, x in v.items():
            if k != "exit":
                print("  ", k, "SILENT" if x["silent"] else "not silent", json.dumps({a: b for a, b in x.items()
                                                                                    if a != "silent"})[:400])


if __name__ == "__main__":
    main()
