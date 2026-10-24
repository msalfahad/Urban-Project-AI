"""T-219 development-villa runner (Alsenan; not an accuracy claim). Values only; every source named.

Inputs (all committed, values only, no sheet coordinates):
- research/agents_t233/ALSENAN_FOOTING_INPUT.json: the 26 footing outlines of the FOUNDATION PLAN of Drive 'Alsenan
  chalet project' / 'ST7757 dxf.dxf' (sha 9f9d1179), drawn sizes and areas, tags, schedule rows (T-233, MERGED
  2ecb5bf0, Checker 20:14 re-measured all 26 outlines: reused with that citation, WORKFLOW_CONTROLS s.10 rule 5).
- ALSENAN_T219_INPUT.json (this folder): the underlay chain and side-face readings of ST7757.pdf p.13, the lift detail
  of p.14, the FN / F9 clip, strap-end contacts (T-174 / T-230 values), lift ring / C9 / FF sizes (own DXF read this
  run, handles 10EB / 1090 / 1B2B), and the freelancer rows searched.

Run: python3 -I research/agents_t219/t219_alsenan_check.py [--write]   (--write refreshes LEDGER_T219.csv and
summary.json; the tests run it without writing.)
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import foundation_wp_v1 as W  # noqa: E402

T233 = ROOT / "research" / "agents_t233" / "ALSENAN_FOOTING_INPUT.json"
INP = HERE / "ALSENAN_T219_INPUT.json"


def rect(a, b):
    return [(0.0, 0.0), (a, 0.0), (a, b), (0.0, b)]


def notched(a, b, nx, ny):
    """a x b rectangle less an nx x ny corner piece (a drawn one-owner clip)."""
    return [(0.0, 0.0), (a - nx, 0.0), (a - nx, ny), (a, ny), (a, b), (0.0, b)]


def build():
    t233 = json.loads(T233.read_text(encoding="utf-8"))
    inp = json.loads(INP.read_text(encoding="utf-8"))
    ch = inp["underlay_chain"]
    chain = W.UnderlayChain(ch["screed_t"], ch["membrane_t"], ch["blinding_t"], ch["membrane_extent"],
                            ch["membrane_product"], ch["source"])
    sd = inp["side_details"]
    side = W.SideDetails(sd["single"], sd["double"], sd["selected"], sd["why_held"])
    sched = t233["schedule"]
    contacts = {}
    for c in inp["contacts"]:
        L = c["face_length_m"]
        if "oblique_cos" in c:
            L = c["width_m"] / c["oblique_cos"]
        contacts.setdefault(c["outline"], []).append(
            W.Contact(c["with"], L, c["height_m"], c["status"], c.get("note", "")))
    clips = {c["outline"]: c for c in inp["clips"]}
    footings = []
    for o in t233["outlines"]:
        if o["id"] in inp["lift"]["exclude_outlines"]:
            continue                                           # FF: its own detail (p.14), lift pit below
        tags = tuple(o["tags"])
        if o["id"] in clips:
            c = clips[o["id"]]
            pts = notched(o["a"], o["b"], c["notch_x_m"], c["notch_y_m"])
        else:
            pts = rect(o["a"], o["b"])
        H = sched[tags[0]]["H"] if len(set(tags)) == 1 else None
        rows = None
        if len(set(tags)) > 1:
            rows = sum(sched[t]["L"] * sched[t]["W"] for t in sorted(set(tags)))
        footings.append(W.Footing(o["id"], tags, pts, "m", H, rows, tuple(contacts.get(o["id"], ()))))
    lf = inp["lift"]
    pit = W.LiftPit(lf["id"], rect(lf["base_a_m"], lf["base_b_m"]), lf["envelope_points_m"], "m", lf["H"],
                    lf["screed_t"], lf["pit_height_m"], lf["board_printed"])
    return t233, inp, chain, side, footings, pit


def main(write=False):
    t233, inp, chain, side, footings, pit = build()
    rows, comps = [], []
    for f in footings:
        cs = W.footing_components(f, chain, side)
        comps += cs
        for c in cs:
            rows.append({"outline": f.id, "type": "+".join(f.tags), **c.row()})
    lc = W.lift_pit_components(pit)
    comps += lc
    for c in lc:
        rows.append({"outline": "1B2B", "type": "FF", **c.row()})
    tot = W.totals(comps)
    # per type (membrane m2, measured outlines)
    by_type = {}
    for f, r in ((f, r) for f in footings for r in rows if r["outline"] == f.id and r["item"] == "WP.FOOTING_MEMBRANE"):
        if r["status"] == W.DC:
            n, a = by_type.get(f.tags[0], (0, 0.0))
            by_type[f.tags[0]] = [n + 1, round(a + r["qty"], 6)]
    side_rows = [r for r in rows if r["item"] == "WP.FOOTING_SIDES"]
    side_read = {}
    for r in side_rows:
        for k, v in r["readings"].items():
            if v is not None:
                side_read[k] = round(side_read.get(k, 0.0) + v, 6)
    summary = {
        "method": W.METHOD,
        "outlines": len(footings),
        "membrane_by_type": by_type,
        "totals": tot,
        "side_readings_sum_m2": side_read,
        "freelancer": inp["freelancer"],
        "sources": {"t233_input_sha_prefix": t233["source"]["sha256"][:8], "chain": inp["underlay_chain"]["source"],
                    "lift": inp["lift"]["source"]},
    }
    if write:
        buf = io.StringIO()
        cols = ["outline", "type", "element", "item", "unit", "qty", "status", "low", "high", "readings", "basis",
                "held_why"]
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(r[k], sort_keys=True) if k == "readings" else r[k]) for k in cols})
        (HERE / "LEDGER_T219.csv").write_text(buf.getvalue(), encoding="utf-8")
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    return rows, summary


if __name__ == "__main__":
    _, s = main(write="--write" in sys.argv)
    print(json.dumps({k: s[k] for k in ("outlines", "membrane_by_type", "totals", "side_readings_sum_m2")}, indent=1))
