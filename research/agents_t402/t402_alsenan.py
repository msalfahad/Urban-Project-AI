"""T-402 the HELD beam lines of the candidate, one by one (development villa; research only, nothing released).

Inputs
  research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json  candidate structural lines (V3.0.21 = V3.0.29 binding by
      research/agents_t387/BINDING_T387.csv; V3.0.30 .. V3.0.32 change no STR.CONC.BEAM line, T-284 / T-395)
  research/agents_t387/BINDING_T387.csv                     held / valued status of each beam line
  <private>/t402/READ_T402.json                             own drawing read (t402_read.py) of the held bands
Output (tracked): HELD_LINES_T402.csv (one row per held line) and summary_t402.json: engine ids, marks, DXF handles,
lengths, widths, m3; no coordinates, no client data, no freelancer row.

    python3 -I research/agents_t402/t402_alsenan.py --read <private>/t402/READ_T402.json --write
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t402_rules as R  # noqa: E402

ENVELOPE = (0.40, 1.20)   # printed depths of the set: simple beams B1 .. B29, CA, B.W and CB1 .. CB13 (ST p.10 / p.11)
SLAB_T = 0.16             # printed S.S 16 CM over the beams (slab pairing of a width alternative, R-T402-5)

SHEETS = "ST7757 DXF roof-slab plans GF / 1F / 2F; ST p.10 simple-beam schedule; ST p.11 continuous-beam schedule"

# per held line: mark(s), designer item, class, schedule rows (b, D), notes of the own read
SPEC = {
    # width conflicts (schedule row vs drawn edges), D-27 / D-02
    "L-9e4895663f76d7f03ac9": dict(mark="B29", item="D-27", cls="WIDTH", sched=(0.25, 0.75), add_m3_per_m_w=0.0024 / 0.20,
                                   why="schedule b 0.25 (p.10 row B29) vs drawn edges 0.200 (463 / 2CE); no section cuts it; ends on B22 face and the B21 face (oblique)"),
    "L-2c7b0b1e1a439d9ffd1e": dict(mark="CB2", item="D-27", cls="WIDTH", sched=(0.20, 0.50),
                                   why="schedule b 0.20 (p.11 row CB2) vs drawn 0.250 (274 / 278); no section cuts it; between columns 32F / 332"),
    "L-60f09eece6568b15f6ce": dict(mark="CB2", item="D-27", cls="WIDTH", sched=(0.20, 0.50),
                                   why="schedule b 0.20 vs drawn 0.250 (274 / 278); no section; columns 332 / 377"),
    "L-1fd49f3e7c5a7dd19d4d": dict(mark="B21", item="D-27", cls="WIDTH", sched=(0.45, 0.75), add_m3_per_m_w=(0.0095 + 0.0093) / 0.40,
                                   why="schedule b 0.45 (p.10 row B21) vs drawn 0.400 measured square to the inclined axis (433 / 434); no section; columns 322 / 37A"),
    "L-39ca5340879eafc35355": dict(mark="B6", item="D-27", cls="WIDTH", sched=(0.25, 0.50), add_m3_per_m_w=0.0010 / 0.25,
                                   why="schedule b 0.25 (p.10 row B6) vs drawn 0.200 (5CC / 5CD) on this span, the other four B6 spans drawn 0.25; no section; column 77B"),
    "L-50667f69855b6d588011": dict(mark="CB10", item="D-02", cls="WIDTH", sched=(0.25, 0.50),
                                   why="schedule b 0.25 (p.11 row CB10) vs drawn 0.300 (5E7 / 5E8); mirror CB13 printed 0.30 = drawn; no section; columns 685 / 68B"),
    "L-43e804ba4a4c07529fd5": dict(mark="CB10", item="D-02", cls="WIDTH", sched=(0.25, 0.50),
                                   why="schedule b 0.25 vs drawn 0.300 (5E7 / 5E8); no section; column 685"),
    # two marks on one span, D-03
    "L-88ccf8d4505411deb9e5": dict(mark="CB3|B3", item="D-03", cls="TWO_MARKS", sched=None, depths=(0.40, 0.75),
                                   why="CB3 printed under all spans of the band and in its p.11 row (0.20 x 0.75); 'B3 (With Stair)' printed over span 2 (p.10 row B3 0.20 x 0.40); drawn 0.200 (27E / 283); no section cuts it"),
    # unlabelled spans across a support, D-04
    "L-efd3f7806bf10b6a8e98": dict(mark=None, item="D-04", cls="UNLABELLED", b=0.20, L=0.50,
                                   why="no mark on the 0.50 m piece past the support; route G band only (not in the band fit file); edges continue the neighbour's"),
    "L-8ea71184fff91b4357b7": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   why="no mark on the 1.50 m piece past column 335 (B24 band continued to the east edge); section cut D (181D) crosses it: D-D prints no dimension ('AS PER SCH.'), drawn 1.391 x 3.000 = 0.35 x 0.75 at the 1:25 implied by the three other D cuts on CB1 (0.35 x 0.75): an INDICATION whose width disagrees with the drawn 0.50"),
    "L-f83c4a469845c7e14dfa": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   why="no mark on the 0.80 m piece past column 691 (B2 band continued); edges 5C6 / 5E3 continue through several marks"),
    "L-8d031491396379f0cbb1": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   why="no mark on the 1.13 m piece past column 415 (B8 band continued); edges 38D (8.10 m) / 38E (7.90 m) run on through it"),
    "L-d62d2fcf3d0023ad1ad1": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   faces=("397", "3AD"), why="no mark on the 3.10 m piece south of column 424 (B15 band continued); edges 397 / 3AD run through B15 and this piece; a 0.075 facade line beside it (3C7 / 3CA) is not a face"),
    "L-dc8cbfc119d006ff3927": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   why="no mark on the 1.40 m piece past column 418; edges 399 / 39C (6.60 m) run through B1 AND B3 spans: continuity does not bind a mark"),
    "L-7c3edce23ec8faa3d674": dict(mark=None, item="D-04", cls="UNLABELLED",
                                   why="no mark on the 1.40 m piece past column 41E; edge 3A1 (6.60 m) runs through marked spans of two types"),
    # slab-edge projections, D-05 / D-26
    "L-634cefe5e8a7fb458e16": dict(mark=None, item="D-05/D-26", cls="PROJECTION",
                                   why="0.20 strip north of B20; section A-A (55A) cuts it and draws B20 0.40 x 0.75 + the 0.20 x 0.20 upstand on the beam's outer half only, no slab either side: not conclusive (Q-61 C(5))"),
    "L-331d4bbef719a7f0bbca": dict(mark=None, item="D-05/D-26", cls="PROJECTION", why="0.20 strip north of B20, past the support; no section; rounded plan corner"),
    "L-aba59a2157a48a69e2fb": dict(mark=None, item="D-26", cls="PROJECTION", b=0.20, L=4.10, why="GF outer west strip 0.20 x 4.10 (no engine band); depth not printed"),
    "L-67f3d325019e618328eb": dict(mark=None, item="D-05/D-26", cls="PROJECTION",
                                   why="0.20 strip north of B23; section B-B (76E) cuts it, draws B23 + upstand only, no slab either side: not conclusive"),
    "L-54e397fe7b1485b2e8fe": dict(mark=None, item="D-05/D-26", cls="PROJECTION", why="0.20 strip north of B23 past the support; no section"),
    "L-a9d5e7dc22013e24d691": dict(mark=None, item="D-05/D-26", cls="PROJECTION", why="1F outer west strip 0.20 x 7.50 outside CB10 (5E5 / 5E7); rounded ends; no section"),
    "L-bb49e831f053bd30a6ce": dict(mark=None, item="D-05/D-26", cls="PROJECTION", why="1F SE box 0.30 x 0.90 (5C1 / 619); no section"),
    "L-56d278bedc8dda2837a9": dict(mark=None, item="D-05/D-26", cls="PROJECTION", faces=("629", "5DE"),
                                   why="1F strip outside CB12: 0.30 between 629 / 5DE over 4.51 m with a 0.05 step (628) over 3.96 m; no section"),
    "L-fbb65dfd2a66a16714ac": dict(mark=None, item="D-26", cls="PROJECTION", b=0.40, L=1.00, approx=True, why="1F rounded box outside CB12 about 0.40 x 1.00 (T-110 outline; no engine band)"),
    "L-377cb988b2271c2e2e4d": dict(mark=None, item="D-26", cls="PROJECTION", b=0.10, L=5.69, why="1F 0.10 strip outside CB12 over 5.69 m (no engine band)"),
    "L-17c4238c0ef76656d06e": dict(mark=None, item="D-26", cls="PROJECTION", b=0.10, L=4.35, why="2F 0.10 strip west of the B15 band (partition face 2F-031); no tag, no bars"),
    # dome ring, D-28
    "L-ab37afa17f2ac5b0efd1": dict(mark=None, item="D-28", cls="RING", area=1.7993,
                                   why="east dome-opening ring: no B4 or other mark within 3.2 m (west ring prints two B4); dome detail ring 20 wide, depth 'AS PER ARCH'"),
}


def load():
    d = {l["line_id"]: l for l in json.loads((RES / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json").read_text(encoding="utf-8"))["lines"]}
    b = [r for r in csv.DictReader((RES / "agents_t387" / "BINDING_T387.csv").open(encoding="utf-8"))
         if r["item_code"] == "STR.CONC.BEAM" and r["status"] == "HELD"]
    return d, b


def _faces(run, only=None):
    """Main face pair: the two outermost faces carrying most of the band length (or the named handles)."""
    fs = sorted((f for f in run["faces"] if not only or f["handle"] in only), key=lambda f: -f["clipped_m"])
    main = [f for f in fs if f["clipped_m"] >= 0.6 * run["band_length_m"]]
    offs = sorted({f["offset_m"] for f in main})
    w = round(offs[-1] - offs[0], 4) if len(offs) > 1 else None
    Ls = [f["clipped_m"] for f in main if f["offset_m"] in (offs[0], offs[-1])]
    return w, round(sum(Ls) / len(Ls), 4), [f["handle"] for f in main]


def build(read):
    cand, held = load()
    rows = []
    for r in held:
        lid = r["line_id"]
        s = SPEC[lid]
        c = cand[lid]
        run = read.get(lid)
        w_drawn = L = None
        handles = []
        if run:
            w_drawn, L, handles = _faces(run, s.get("faces"))
        if s.get("b") is not None:
            w_drawn, L = s["b"], s["L"]
        row = dict(line_id=lid, floor=r["floor"], element_id=r["element_id"], mark=s["mark"] or "(none)",
                   designer_item=s["item"], cls=s["cls"], why_held=s["why"], sheets_searched=SHEETS,
                   edge_handles=" ".join(handles), drawn_width_m=w_drawn, f2f_length_m=L,
                   cand_low=c["bounded_low"], cand_high=c["bounded_high"])
        if s["cls"] in ("PROJECTION", "RING"):
            area = s.get("area") if s["cls"] == "RING" else (round(w_drawn * L, 4) if w_drawn and L else None)
            if lid == "L-56d278bedc8dda2837a9":
                area = round(0.2985 * 4.5097 + 0.05 * 3.9594, 4)
            res = R.resolve(R.HeldPiece(lid, None, projection=True, plan_area_m2=area))
            if s["cls"] == "RING":
                res["missing"] = "ring section (no mark; dome detail depth 'AS PER ARCH'); B4 only where identified (Q-61 C(3))"
        elif s["cls"] == "WIDTH":
            pc = R.HeldPiece(lid, s["mark"], widths=[R.Reading(s["sched"][0], "SCHEDULE_ROW", s["mark"]),
                                                     R.Reading(w_drawn, "DRAWN_EDGES", row["edge_handles"])],
                             depths=[R.Reading(s["sched"][1], "SCHEDULE_ROW", s["mark"])],
                             length=R.Reading(L, "FACE_TO_FACE"))
            res = R.resolve(pc)
            sp = R.slab_pairing(w_drawn, s["sched"][0], L, SLAB_T)
            res["slab_pairing"] = f'{sp["kind"]} {sp["slab_m3"]:.6f} m3 (slab net of the drawn faces; t {SLAB_T})'
            res["total_shift_m3"] = round((s["sched"][0] - w_drawn) * L * (s["sched"][1] - SLAB_T), 6)
            k = s.get("add_m3_per_m_w", 0.0)   # merged T-229 oblique-end additions, per metre of width
            if k:
                lo_w, hi_w = sorted((s["sched"][0], w_drawn))
                res["low"] = round(res["low"] + k * lo_w, 6)
                res["high"] = round(res["high"] + k * hi_w, 6)
        elif s["cls"] == "TWO_MARKS":
            pc = R.HeldPiece(lid, s["mark"], widths=[R.Reading(0.20, "SCHEDULE_ROW", "CB3"), R.Reading(0.20, "SCHEDULE_ROW", "B3"),
                                                     R.Reading(w_drawn, "DRAWN_EDGES", row["edge_handles"])],
                             depths=[R.Reading(d, "SCHEDULE_ROW", m) for d, m in zip(s["depths"], ("B3", "CB3"))],
                             length=R.Reading(L, "FACE_TO_FACE"))
            res = R.resolve(pc)
        else:  # UNLABELLED
            pc = R.HeldPiece(lid, None, widths=[R.Reading(w_drawn, "DRAWN_EDGES", row["edge_handles"])],
                             depths=[R.Reading(ENVELOPE[0], "SCHEDULE_ENVELOPE", "set"), R.Reading(ENVELOPE[1], "SCHEDULE_ENVELOPE", "set")]
                             + ([R.Reading(0.75, "SCALED_SECTION", "D-D at 1:25 implied")] if lid == "L-8ea71184fff91b4357b7" else []),
                             length=R.Reading(L, "FACE_TO_FACE"))
            res = R.resolve(pc)
        row.update(result=res["result"], value_m3=res["m3"], low_m3=res["low"], high_m3=res["high"],
                   plan_area_m2=res.get("plan_area_m2"), missing_fact=res["missing"], basis=res["basis"],
                   slab_pairing=res.get("slab_pairing", "slab net of the drawn band; piece inside its band (T-387: held member, pair UNDETERMINED)"),
                   total_shift_schedule_minus_drawn_m3=res.get("total_shift_m3"),
                   indication="; ".join(f"{v} ({r})" for v, r in res.get("indication", [])))
        rows.append(row)
    return rows


def summarise(rows):
    out = {"lines": len(rows), "by_floor": {}, "by_result": {}, "by_class": {}}
    for r in rows:
        out["by_floor"][r["floor"]] = out["by_floor"].get(r["floor"], 0) + 1
        out["by_result"][r["result"]] = out["by_result"].get(r["result"], 0) + 1
        k = out["by_class"].setdefault(r["cls"], {"lines": 0, "low_m3": 0.0, "high_m3": 0.0, "cand_low": 0.0,
                                                   "cand_high": 0.0, "plan_area_m2": 0.0})
        k["lines"] += 1
        for a, b in (("low_m3", "low_m3"), ("high_m3", "high_m3"), ("cand_low", "cand_low"), ("cand_high", "cand_high"),
                     ("plan_area_m2", "plan_area_m2")):
            if r[b] is not None:
                k[a] = round(k[a] + float(r[b]), 6)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--read", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    read = json.load(open(a.read, encoding="utf-8"))["runs"]
    rows = build(read)
    for r in rows:
        R.refuse_zero(r["value_m3"])
    summ = summarise(rows)
    print(json.dumps(summ, indent=1))
    for r in rows:
        print(r["floor"], r["line_id"], r["mark"], r["cls"], r["result"], r["drawn_width_m"], r["f2f_length_m"],
              r["low_m3"], r["high_m3"], "cand", r["cand_low"], r["cand_high"], r["plan_area_m2"])
    if a.write:
        with (HERE / "HELD_LINES_T402.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        (HERE / "summary_t402.json").write_text(json.dumps(summ, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
