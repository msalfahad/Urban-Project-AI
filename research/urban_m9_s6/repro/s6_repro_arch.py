"""S6 architectural finish reproductions (ARC-D2/D3/D4/D7/D8) on the current HEAD, synthetic villa + its test facts.

usage: python3 -I s6_repro_arch.py REPO WORK_DIR
"""
import json, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path

REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

CLI = [sys.executable, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch", "--method", "ARCH_TAKEOFF_V1",
       "--no-svg"]
FACTS = REPO / "research" / "urban_m9_s2" / "SYNTHETIC_FACTS_S2.json"


def run(dxf, out, facts=True):
    a = CLI + ["--drawings", str(dxf), "--out", str(out)] + (["--facts", str(FACTS)] if facts else [])
    p = subprocess.run(a, capture_output=True, text=True, cwd=str(WORK))
    L = json.loads((out / "BOQ_LINES.json").read_text())
    L = L["lines"] if isinstance(L, dict) else L
    U = json.loads((out / "UNRESOLVED.json").read_text())
    U = U.get("unresolved", U) if isinstance(U, dict) else U
    R = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    return p.returncode, L, U, R


def by_room(L):
    d = defaultdict(list)
    for ln in L:
        loc = ln.get("location") or {}
        d[(loc.get("floor"), loc.get("room_id"))].append(ln)
    return d


def main():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    dxf = WORK / "villa.dxf"
    AS.villa(str(dxf))
    code, L, U, R = run(dxf, WORK / "out")
    room = {r["room_id"]: r for r in R}
    out = {"exit": code, "rooms": {}}
    for (fl, rid), lines in sorted(by_room(L).items(), key=lambda x: str(x[0])):
        r = room.get(rid) or {}
        items = defaultdict(list)
        for ln in lines:
            calc = ln.get("calculation") or {}
            inp = calc.get("inputs") or {}
            items[ln["item_code"]].append({"net": ln.get("measured_net"), "ev": ln.get("evidence_state"),
                                           "h": inp.get("height_m") or inp.get("finish_h_m") or inp.get("H_m"),
                                           "rule": (ln.get("rule") or {}).get("id") if isinstance(ln.get("rule"), dict) else ln.get("rule")})
        unres = sorted({u.get("item") for u in U if u.get("room_id") == rid})
        out["rooms"][f"{fl}:{'+'.join(r.get('codes') or [])}:{r.get('kind')}"] = {"items": dict(items), "unresolved": unres}
    # ARC-D7: the bedroom's Arabic word with a SHADDA (U+0651) on its second letter, as typed by many drafters
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
    code7, L7, U7, R7 = run(d7, WORK / "out_tashkeel")
    out["ARC_D7_tashkeel"] = {"replaced": n, "exit": code7,
                              "gf_rooms": sorted(("+".join(r.get("codes") or []) or "-", r["class"], r.get("kind"),
                                                  round(r["area_m2"], 3)) for r in R7 if r["floor"] == "GF"),
                              "lines": len(L7), "baseline_lines": len(L)}
    (WORK / "S6_REPRO_ARCH.json").write_text(json.dumps(out, indent=1, ensure_ascii=True))
    for k, v in out["rooms"].items():
        print(k, {i: [(x["net"], x["ev"], x["h"]) for x in xs] for i, xs in v["items"].items() if i.startswith(("FIN.PL", "FIN.PA", "FIN.WALL", "FIN.SK", "FIN.CEIL", "FIN.RAIL", "ARCH"))}, "UNRES", v["unresolved"])
    print("ARC-D7", json.dumps(out["ARC_D7_tashkeel"]))


if __name__ == "__main__":
    main()
