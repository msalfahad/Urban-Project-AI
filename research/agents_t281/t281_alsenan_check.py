"""T-281 development-villa stair-soffit ledger: every flight and landing of ST-01 and ST-02, method O and method D side
by side, the space below, the slab-plan stair zones reconciled in m2. Research only; nothing released.

    python3 -I research/agents_t281/t281_alsenan_check.py [--write]

Reads ALSENAN_T281_INPUT.json (values and handles only), writes LEDGER_T281.csv and summary.json (byte-stable)."""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t281_stair_soffit as S  # noqa: E402

INPUT = HERE / "ALSENAN_T281_INPUT.json"
COLS = ["id", "stair", "piece", "cls", "plan_O", "true_O", "plan_D", "true_D", "status", "held", "below", "src"]


def load(path=INPUT):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _riser(d, key):
    r = d["risers"][key]
    return r["rise"] / r["count"], r["source"]


def _flight(d, f):
    r, rs = _riser(d, f["riser"])
    return dict(f, r=r, r_source=rs, t=d["waist"]["t"], t_source=d["waist"]["source"],
                subs=[tuple(s[:2]) + (tuple(s[2]),) for s in f["subs"]])


def build(d):
    rows, lims, kinks_by_landing = [], {}, {}
    flights = {f["id"]: _flight(d, f) for f in d["flights"]}
    for fid, f in flights.items():
        fr, lim = S.flight_rows(f, f["subs"])
        for r in fr:
            r["stair"] = f["stair"]
        rows += fr
        lims[fid] = lim
    landings = {L["id"]: dict(L, subs=[tuple(s[:2]) + (tuple(s[2]),) for s in L["subs"]]) for L in d["landings"]}
    for k in d["kinks"]:
        f, lim = flights[k["flight"]], lims[k["flight"]]
        if k["into"] in landings:
            L = landings[k["into"]]
            kr, kd = S.kink_rows(f, lim, L["length"], L["width"], L["subs"], k["u_offset"], into=k["into"])
            kinks_by_landing.setdefault(k["into"], []).append(kd)
        else:
            p = k["plate"]
            subs = [tuple(s[:2]) + (tuple(s[2]),) for s in p["subs"]]
            kr, kd = S.kink_rows(f, lim, p["length"], p["width"], subs, k["u_offset"], into=k["into"])
            for r in kr:
                r["piece"] += "; the strip lies north of the top riser 315 under the slab plate (slab ceiling in method O)"
            if kd["rect"] is not None:
                sub_area = S.union_area([S._clip(s[2], kd["rect"]) for s in subs])
                rows.append({"id": f"{f['id']}/head kink/hidden pair 2CC / 2CD", "stair": f["stair"],
                             "piece": "hidden pair 2CC / 2CD inside the head kink", "cls": "UNKNOWN", "plan_O": 0.0,
                             "true_O": None, "plan_D": sub_area, "true_D": None, "status": "HELD",
                             "below": f["below"], "src": f["src"]})
        for r in kr:
            r["stair"] = f["stair"]
        rows += kr
    for lid, L in landings.items():
        lr = S.landing_rows(L, kinks_by_landing.get(lid, ()))
        for r in lr:
            r["stair"] = L["stair"]
        rows += lr
    # MS1-L CONFLICT: both readings, never one end
    c = d["conflict"]
    r_, rs = _riser(d, c["riser"])
    rng = {}
    for name, rd in c["readings"].items():
        s0 = rd["s_first"]
        col = c["column_36B"]
        f = {"id": c["id"], "n": rd["n"], "g": c["g"], "w": c["w"], "r": r_, "r_source": rs, "t": d["waist"]["t"],
             "t_source": d["waist"]["source"], "foot": {"type": "ground"},
             "head": {"type": "held_junction"}, "status": "CONFLICT", "below": c["below"], "src": c["src"]}
        sub = [("column 36B", "NO_SOFFIT", (col[0] - s0, col[1] - s0, col[2], col[3]))]
        fr, lim = S.flight_rows(f, sub)
        w = fr[0]
        borne = [x for x in fr if x["id"].endswith("slab-borne foot")][0]
        rng[name] = {"plan_O": w["plan_O"], "true_O": w["true_O"], "plan_D": w["plan_D"], "true_D": w["true_D"],
                     "slab_borne_D": borne["plan_D"], "column": fr[1]["plan_O"],
                     "open_in_GF025": (s0 - c["beam_face_from_45A"]) * c["w"] if s0 > c["beam_face_from_45A"] else 0.0,
                     "under_B20_band": max(0.0, c["beam_face_from_45A"] - s0) * c["w"]}
    lo = lambda k: min(v[k] for v in rng.values())
    hi = lambda k: max(v[k] for v in rng.values())
    rows.append({"id": c["id"], "stair": c["stair"], "piece": "waist soffit (two readings)", "cls": "STAIR_SOFFIT",
                 "plan_O": None, "true_O": None, "plan_D": None, "true_D": None, "status": "CONFLICT",
                 "held": f"{c['blocker']}; plan O {lo('plan_O'):.6f} .. {hi('plan_O'):.6f}, true O {lo('true_O'):.6f} .. "
                         f"{hi('true_O'):.6f}, true D {lo('true_D'):.6f} .. {hi('true_D'):.6f}",
                 "below": c["below"], "src": c["src"], "range": rng})
    for h in d["held"]:
        r = S.held_surface(h["id"], h["piece"], h["plan"], h["below"], h["src"], h["why"], h["status"])
        r["stair"] = "ST-01" if h["id"].startswith("ST01") else "ST-02"
        rows.append(r)
    for o in d["open"]:
        rows.append({"id": o["id"], "stair": "ST-01", "piece": o["piece"], "cls": "NO_SOFFIT", "plan_O": o["plan"],
                     "true_O": 0.0, "plan_D": o["plan"], "true_D": 0.0, "status": "DRAWING-CONFIRMED",
                     "below": "stair well (open to above)", "src": o["src"]})
    return rows, lims, rng


def _g(rows, rid):
    return [r for r in rows if r["id"] == rid][0]


def reconcile(d, rows, rng):
    z = d["zones"]
    out = {}
    # GF-025: the ST-01 GF -> 1F zone
    B = rng["B_structural"]
    gf025 = {"MS1-L lane in the face (B20 face -> 25E, less column 36B)": (3.30 - 0.15) * 1.20 - B["column"],
             "column 36B (no soffit)": B["column"], "well GF": _g(rows, "ST01-WELL-GF")["plan_O"],
             "MS1-T": _g(rows, "ST01-MS1-T")["plan_O"], "MS1-LD": _g(rows, "ST01-MS1-LD")["plan_O"],
             "MS1-U": _g(rows, "ST01-MS1-U")["plan_O"]}
    face_parts = dict(gf025)
    face_parts.pop("column 36B (no soffit)")
    out["GF-025"] = {"face_m2": z["GF-025"]["face_m2"], "parts": gf025,
                     "residual": S.partition_check(z["GF-025"]["face_m2"], face_parts),
                     "MS1-L lane split by reading": {k: {"soffit (O)": v["plan_O"], "open to the shaft above": v["open_in_GF025"],
                                                         "under the B20 band in plan (outside the face)": v["under_B20_band"]}
                                                     for k, v in rng.items()}}
    # 1F-016: the ST-01 1F -> 2F zone
    ms2l = _g(rows, "ST01-MS2-L")["plan_O"]
    f1 = {"MS2-L waist": ms2l, "well 1F": _g(rows, "ST01-WELL-1F")["plan_O"], "MS2-TR well end": _g(rows, "ST01-MS2-TR")["plan_O"],
          "MS2-LD-W": _g(rows, "ST01-MS2-LD-W")["plan_O"], "MS2-LD-E": _g(rows, "ST01-MS2-LD-E")["plan_O"],
          "MS2-U": _g(rows, "ST01-MS2-U")["plan_O"]}
    col691 = _g(rows, "ST01-MS2-L/column 691 exposure")["plan_O"]
    out["1F-016"] = {"face_m2": z["1F-016"]["face_m2"], "parts": f1, "column 691 (outside the face, exposure HELD)": col691,
                     "residual": S.partition_check(z["1F-016"]["face_m2"], f1)}
    # T-271 GF stair soffit 9.853618 = ST-02 pieces inside its faces + bottom-step strip + slab north of 315
    t = z["T271-GF"]
    inside = sum(t["inside_pieces"].values())
    north = sum(t["north_of_315"].values())
    res = S.partition_check(t["held_m2"], {"inside": inside, "bottom": t["bottom_step_strip"], "north": north},
                            tol=1e-4, residual_named="T-271 arcs at 1024 segments vs 2048 here")
    st02_plan = sum((r["plan_O"] or 0.0) for r in rows if r["stair"] == "ST-02" and r["plan_O"] is not None
                    and r["cls"] != "NO_SOFFIT" and "head kink" not in r["id"])
    beam = z["ST02-beam-pieces"]
    beam_in = sum(beam["in_decor_ceiling"].values())
    sliv = sum(beam["outside_every_face"].values())
    out["T271-GF"] = {"held_m2": t["held_m2"], "ST-02 pieces inside the T-271 stair faces": inside,
                      "bottom-step strip inside the light-well outline (no soffit: no ceiling)": t["bottom_step_strip"],
                      "slab north of the top riser 315 (GF-131 / GF-132 parts; plate C-T1)": north,
                      "residual (named)": res,
                      "ST-02 plan, all rows less column 374 (method O)": st02_plan,
                      "ST-02 plan under T-139 beam / column pieces kept in the T-271 decor ceiling": beam_in,
                      "ST-02 plan inside column outlines, in no face": sliv,
                      "closure ST-02 plan = inside + beam pieces + slivers": inside + beam_in + sliv - st02_plan}
    if abs(out["T271-GF"]["closure ST-02 plan = inside + beam pieces + slivers"]) > 1e-5:
        raise S.SoffitError("ST-02 plan does not close against the T-139 faces")
    c = z["T271-GF-ceiling"]
    kink = _g(rows, "ST02-RS-A/head kink")["plan_D"] + _g(rows, "ST02-RS-A/head kink/hidden pair 2CC / 2CD")["plan_D"]
    out["T271-GF-effect"] = {
        "horizontal decor ceiling, T-271": c["horizontal_m2"],
        "less the beam / CA / column-edge pieces under the ST-02 lanes": -beam_in,
        "plus the slab north of 315 (method O: slab, not stair)": north,
        "horizontal decor ceiling, method O": S.exclude_from_ceiling(c["horizontal_m2"], beam_in) + north,
        "method D: the RS-A head kink under plate C-T1 also leaves the ceiling": -kink,
        "horizontal decor ceiling, method D": S.exclude_from_ceiling(c["horizontal_m2"], beam_in) + north - kink,
        "no ceiling, T-271 + bottom-step strip": c["no_ceiling_m2"] + t["bottom_step_strip"]}
    return out


def summary(d):
    rows, lims, rng = build(d)
    rec = reconcile(d, rows, rng)
    tot = {}
    for st in ("ST-01", "ST-02"):
        tot[st] = S.totals([r for r in rows if r["stair"] == st and r["status"] != "CONFLICT"])
    by_cls = {}
    for r in rows:
        by_cls[r["cls"]] = by_cls.get(r["cls"], 0) + 1
    s = {"schema": "T281_SUMMARY", "method": S.METHOD, "rows": len(rows), "by_class": dict(sorted(by_cls.items())),
         "totals": tot, "MS1-L CONFLICT": rng,
         "pitch": {k: lims[k]["sec"] for k in sorted(lims)},
         "kinks_m": {k: {"foot": lims[k]["kink_foot"], "head": lims[k]["kink_head"]} for k in sorted(lims)},
         "reconciliation": rec, "released": False,
         "statement": "no quantity released; every true area of a curved, winder or junction piece is HELD (None), never 0"}
    return s, rows


def _fmt(v):
    return "" if v is None else (f"{v:.6f}" if isinstance(v, float) else str(v))


def render(d):
    s, rows = summary(d)
    js = json.dumps(s, indent=1, ensure_ascii=False, sort_keys=False, default=float,
                    allow_nan=False) + "\n"
    js = json.dumps(json.loads(js, parse_float=lambda x: round(float(x), 6)), indent=1, ensure_ascii=False) + "\n"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLS)
    for r in rows:
        w.writerow([_fmt(r.get(k, r.get("held_D") if k == "held" else None)) for k in COLS])
    return js, buf.getvalue()


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    js, cs = render(load())
    if "--write" in a:
        (HERE / "summary.json").write_text(js, encoding="utf-8")
        (HERE / "LEDGER_T281.csv").write_text(cs, encoding="utf-8")
    print(cs)


if __name__ == "__main__":
    main()
