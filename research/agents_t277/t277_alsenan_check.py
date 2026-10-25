"""T-277 on the development villa, from committed inputs only: the census tables and the per-trade consequence of
every width CONFLICT (no quantity is changed anywhere; nothing is wired or released).

Inputs: ALSENAN_T277_INPUT.json and ALSENAN_T277_WALLS.json (this folder; derived from Drive "Alsenan chalet project"
/ 'ST7757 dxf.dxf' sha 9f9d1179 and P7757_DXF_COMPRESSED.zip / P7757.dxf sha ab54dd55 by t277_extract.py and
t277_walls_extract.py), the merged T-252 CONC.BEAM ledger (lengths between supporting faces, depths), the T-110 member
register (run ids), the T-234 slab ledger (slab t beside each band) and the T-228 blockwork register v2 (wall ids).

    python3 -I research/agents_t277/t277_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import beam_width_census as C  # noqa: E402

VARY_TOL_M = C.AGREE_TOL_M


def _load():
    cen = json.load(open(HERE / "ALSENAN_T277_INPUT.json", encoding="utf-8"))
    walls = json.load(open(HERE / "ALSENAN_T277_WALLS.json", encoding="utf-8"))
    ledger = [r for r in csv.DictReader(open(RES / "agents_t252" / "LEDGER_T252.csv", encoding="utf-8"))
              if not r["superseded_by"]]
    reg = list(csv.DictReader(open(RES / "agents_t110" / "BEAM_MEMBER_REGISTER.csv", encoding="utf-8")))
    slab = list(csv.DictReader(open(RES / "agents_t234" / "LEDGER_T234.csv", encoding="utf-8")))
    bw = list(csv.DictReader(open(RES / "agents_t228" / "BLOCKWORK_WALL_REGISTER_V2.csv", encoding="utf-8")))
    return cen, walls, ledger, reg, slab, bw


def schedule(cen):
    rows = [(s["mark"], s["W"], s["H"], s["unit"], s["handle"]) for s in cen["schedule"]]
    return C.schedule_table(rows)


def label_rows(cen, table):
    out = []
    for r in cen["labels"]:
        s0 = r["stations"][0]
        rec = table.get(r["mark"])
        W = rec["w_m"] if rec else None
        ws = [x["width_m"] for x in s0["readings"]]
        if s0["status"] != "BOUND":
            cls = s0["status"]
        else:
            cls = C.classify_readings(ws, W)
        other = [sorted(x["width_m"] for x in s["readings"]) for s in r["stations"][1:] if s["status"] == "BOUND"]
        varies = any(len(o) != len(ws) or any(abs(a - b) > VARY_TOL_M for a, b in zip(o, sorted(ws))) for o in other)
        out.append(dict(sheet=r["sheet"], label=r["label"], mark=r["mark"], in_block=r["in_block"],
                        schedule_w_m=W, schedule_handle=(rec or {}).get("handles", [""])[0],
                        placement=s0["placement"] or "", readings_m=" / ".join("%.4f" % w for w in ws if w is not None),
                        edges=" ; ".join("%s|%s" % ("+".join(x["edges"][0]), "+".join(x["edges"][1]))
                                         for x in s0["readings"]),
                        interior=" ".join(h for x in s0["readings"] for h in x["interior"]),
                        clear_m=s0.get("dist_m"), cls=cls, side_stations_differ=varies))
    return out


def run_rows(cen, table, reg):
    R = {(r["member_id"], r["component"]): r for r in reg}
    out = []
    for x in cen["run_centres"]:
        r = R[(x["member"], x["component"])]
        rec = table.get(x["mark"])
        W = rec["w_m"] if rec else None
        bound = [s for s in x["stations"] if s["status"] == "BOUND"]
        ws = sorted({round(y["width_m"], 4) for s in bound for y in s["readings"] if y["width_m"] is not None})
        if not x["stations"]:
            cls = "NO_STATION"
        elif not bound:
            cls = x["stations"][0]["status"]
        elif W is None:
            cls = "NO_SCHEDULE"
        else:
            cls = C.classify_readings(ws, W)
        out.append(dict(storey=x["floor"], member=x["member"], component=x["component"], mark=x["mark"],
                        register_status=r["status"], register_type=r["type"], schedule_w_m=W,
                        drawn_m=" / ".join("%.4f" % w for w in ws), stations=len(x["stations"]), bound=len(bound),
                        basis=x.get("station_basis", ""), cls=cls))
    return out


def wall_map(bw):
    """(storey, V2 run id) -> register wall id, from the register's own evidence text."""
    m = {}
    for r in bw:
        for run in re.findall(r"V2 run (WB-FL\d+-FL\d+(?:#\d+)?)", r["evidence"]):
            m[(r["floor"], run)] = r["wall_id"]
    return m


def conflicts(cen, walls, ledger, slab, bw, table):
    L = {(r["storey"], r["run"].split("#", 1)[1] if "#" in r["run"] else r["run"]): r for r in ledger}
    tmap = wall_map(bw)
    t_by = {}
    for r in slab:
        t_by.setdefault(r["storey"], set()).add(r["t_m"])
    out = []
    for b in walls["bands"]:
        band_key = b["component"].split(":")[2]
        lr = L[(b["storey"], band_key)]
        rec = table[b["mark"]]
        D = float(lr["depth_m"]) if lr["depth_m"] else rec["d_m"]
        D_src = "ledger" if lr["depth_m"] else "schedule H %s (handle %s)" % (rec["sizes"][0][1], rec["handles"][0])
        t = 0.16                                            # T-234: every GF / 1F panel beside these bands 0.16
        assert t_by[b["storey"]] >= {"0.16"} and "0.16" in t_by[b["storey"]]
        Lr = float(lr["length_m"])
        pieces = []
        for w in b["walls"]:
            lens = w["len_m"]
            d_len = [round(v - lens["drawn"], 3) + 0.0 for k, v in lens.items() if k != "drawn"]
            kind = "crossing" if (w["angle_to_band_deg"] or 0) > 45 else "along"
            wid = None
            for pc in w["v2_pieces"]:
                wid = tmap.get((b["storey"], pc)) or tmap.get((b["storey"], pc + "#1")) or wid
            pieces.append(dict(wall=wid or "unmapped " + w["wall_run"], v2=w["v2_pieces"], kind=kind,
                               t_m=w["t_m"], under_drawn_m=lens["drawn"],
                               under_schedule_m=sorted(v for k, v in lens.items() if k != "drawn"),
                               delta_cover_m=sorted(d_len),
                               # more cover under the beam = lower wall top there: area change = - d_len x (D - t)
                               m2_change_range=sorted(round(-dl * (D - t), 4) + 0.0 for dl in d_len)))
        q = C.consequence(Lr, D, t, b["drawn_m"], b["schedule_m"])
        out.append(dict(storey=b["storey"], run=lr["run"], mark=b["mark"], edges=b["edges"],
                        drawn_m=b["drawn_m"], schedule_m=b["schedule_m"], delta_b_m=round(b["drawn_m"] - b["schedule_m"], 4),
                        L_m=Lr, D_m=D, D_source=D_src, t_m=t, designer=lr["designer"],
                        ledger_m3_low=float(lr["m3_low"]), ledger_m3_high=float(lr["m3_high"]),
                        conc_m3_drawn=q["conc_beam_m3"][0], conc_m3_schedule=q["conc_beam_m3"][1],
                        conc_m3_width_effect=round(q["conc_beam_m3"][0] - q["conc_beam_m3"][1], 6),
                        fw_soffit_m2_drawn=q["fw_beam_soffit_m2"][0], fw_soffit_m2_schedule=q["fw_beam_soffit_m2"][1],
                        fw_sides_m2_both=q["fw_beam_sides_m2"],
                        slab_soffit_change_m2=q["slab_soffit_delta_m2"], slab_m3_change=q["slab_conc_delta_m3"],
                        walls=pieces))
    return out


def build():
    cen, walls, ledger, reg, slab, bw = _load()
    table = schedule(cen)
    labs = label_rows(cen, table)
    runs = run_rows(cen, table, reg)
    conf = conflicts(cen, walls, ledger, slab, bw, table)
    cnt = Counter((r["sheet"], r["cls"]) for r in labs)
    summary = dict(
        schema="T277_SUMMARY_V1", rules=list(C.RULES),
        labels=len(labs), labels_by_sheet={s: sum(1 for r in labs if r["sheet"] == s) for s in ("GF", "1F", "2F")},
        label_classes={"%s %s" % k: v for k, v in sorted(cnt.items())},
        label_class_totals=dict(Counter(r["cls"] for r in labs)),
        runs=len(runs), run_classes=dict(Counter(r["cls"] for r in runs)),
        schedule_marks=len(table), schedule_duplicates=[m for m, v in table.items() if v["duplicate_conflict"]],
        conflict_runs=len(conf),
        conc_m3_drawn=round(sum(c["conc_m3_drawn"] for c in conf), 6),
        conc_m3_schedule=round(sum(c["conc_m3_schedule"] for c in conf), 6),
        fw_soffit_m2_drawn=round(sum(c["fw_soffit_m2_drawn"] for c in conf), 6),
        fw_soffit_m2_schedule=round(sum(c["fw_soffit_m2_schedule"] for c in conf), 6),
        blockwork_m2_change_low=round(sum(min(p["m2_change_range"]) for c in conf for p in c["walls"]), 4),
        blockwork_m2_change_high=round(sum(max(p["m2_change_range"]) for c in conf for p in c["walls"]), 4),
        align=walls["align"])
    return summary, labs, runs, conf


def _csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in r.items()})


def main(argv):
    summary, labs, runs, conf = build()
    print(json.dumps(summary, indent=1))
    for c in conf:
        print(c["storey"], c["run"], c["mark"], "drawn", c["drawn_m"], "sched", c["schedule_m"], "L", c["L_m"], "D",
              c["D_m"], "m3", c["conc_m3_drawn"], c["conc_m3_schedule"], "soffit", c["fw_soffit_m2_drawn"],
              c["fw_soffit_m2_schedule"], [(p["wall"], p["kind"], p["m2_change_range"]) for p in c["walls"]])
    if "--write" in argv:
        _csv(HERE / "CENSUS_LABELS_T277.csv", labs)
        _csv(HERE / "CENSUS_RUNS_T277.csv", runs)
        _csv(HERE / "CONFLICTS_T277.csv", [{k: v for k, v in c.items()} for c in conf])
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
