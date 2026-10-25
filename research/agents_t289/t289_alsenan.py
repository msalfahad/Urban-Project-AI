"""T-289 basis ledger for the development villa (Alsenan, ST7757 / P7757) from committed inputs only:

  research/agents_t289/CANDIDATE_V3015_BASIS_LINES.json   (t289_extract.py on an own V3.0.15 run)
  research/agents_t289/BAND_PAIRING_T289.json             (engine band id -> T-242 run handles)
  research/agents_t242/LEDGER_T242.csv                    (MERGED 9455a63d; runs face to face, D-35 range)
  research/agents_t253 (MERGED dff9cb79)                  main-house exterior datum +-0.00 -> D 0.95 DRAWING-CONFIRMED;
                                                          annex CONFLICT; court HELD
  research/agents_t248/LEDGER_T248.csv                    (MERGED 567dc972; columns by member, route G element id)
  research/agents_t258 (MERGED b1b72a50)                  ST-03 steps 0.355017 DRAWING-CONFIRMED, waist HELD (S-9)
  T-287 G1 (READY, NOT merged)                            CB5 columns 35F / 365: 1.4300 proposed -> PENDING, not carried

    python3 -I research/agents_t289/t289_alsenan.py [--write]      (--write: BASIS_LEDGER_T289.csv + summary json)
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import basis_ledger as B  # noqa: E402

NAMED = {"GB_EXTERIOR_24": 11.9346, "COL_2F": 3.528, "COL_ANNEX_7": 3.7125, "ST03": 0.948267,
         # found here: three released 'interior' lines lie on main-house exterior runs of T-253 (109+7CB#2,
         # 145+7CA#1, ring ARC:157+158); pinned at their candidate sum so a changed line is refused
         "GB_MAIN_EXTERIOR_IN_INTERIOR_LINES": 1.830623}
CB5 = ("GFRS:35F", "GFRS:365")

GB_PRINT = ("ST p.13 'Ground Beams for exterior walls': top 'Ground Floor slab level', underside 'Outer Normal ground "
            "level', depth 'FOLLOW ARCH.' (no figure); structural top +0.95 main / +0.25 annex (T-214); outer ground "
            "+-0.00 (T-253 s.2 readings 1-5); the interior classes (p.13 30x30 / 30x40 / 30x60 by span) are printed "
            "for interior beams only")
GB_SHEETS = "ST p.3, p.13, p.14 (A-A); arch GF sheet 03; arch section B-B (Pages_11-12 p.11)"
COL_SHEETS = ("ST p.1 - p.6 storey plans, p.12 column schedule; arch sections A-A / B-B; arch roof levels "
              "(T-248 s.2, T-214)")
ST_SHEETS = "arch GF sheet 03, section B-B, ST p.3 riser lines 18A / 189 / 188 / 17A / 179 (T-258); ST p.7 stair details"


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(v):
    return None if v in (None, "") else float(v)


def t242_runs():
    return {r["run"]: r for r in csv.DictReader((ROOT / "research/agents_t242/LEDGER_T242.csv").open(encoding="utf-8"))}


def run_class(r):
    """the merged class / status of one T-242 run after T-253 (MERGED dff9cb79)."""
    comp, part = r["component"], r["part"]
    if comp.startswith("GB-EXTERIOR") and part == "MAIN":
        # T-253 s.2: datum +-0.00 -> D = 0.95, the T-242 high end, run by run (pinned in tests/t253)
        return {"cls": "EXTERIOR_MAIN", "status": B.DRAWING_DERIVED_DC, "value": _f(r["high_m3"]),
                "item": "", "why": "T-253 D 0.95 (top +0.95 to N.G. +-0.00)"}
    if comp.startswith("GB-EXTERIOR") and part == "ANNEX":
        return {"cls": "EXTERIOR_ANNEX", "status": B.CONFLICT, "value": None, "lo": None, "hi": None,
                "item": "D-35 annex (literal 0.25 vs the printed exterior section)",
                "why": f"T-253 s.3 CONFLICT: literal reading {float(r['high_m3']):.4f} m3 at 0.25, never adopted"}
    if comp.startswith("GB-COURT"):
        return {"cls": "COURT", "status": B.HELD, "value": None, "lo": _f(r["low_m3"]), "hi": _f(r["high_m3"]),
                "item": "court section not printed (T-242 / T-253 s.4; GS-16 architect item)", "why": "T-253 s.4"}
    st = r["status"]
    if st == "CALCULATED":
        return {"cls": "INTERIOR", "status": B.DRAWING_DERIVED_DC, "value": _f(r["value_m3"]), "item": "",
                "why": "T-242 interior closable run"}
    return {"cls": "INTERIOR", "status": B.HELD, "value": None, "lo": _f(r["low_m3"]), "hi": _f(r["high_m3"]),
            "item": (r["reasons"] or "T-242 HELD")[:80], "why": "T-242 interior HELD"}


RANK = {B.DRAWING_DERIVED_DC: 0, B.HELD: 1, B.CONFLICT: 2}


def gb_records(lines, pairing, runs, group="GB_EXTERIOR_24"):
    recs, detail = [], []
    for l in lines:
        band = l["element_id"].rsplit(":", 1)[-1]
        d = l["dimensions"]
        net = _f(d.get("net_plan_m2"))
        depth = float(l["measured_net"]) / net if net else None
        p = (pairing["bands"].get(band) or {}).get("runs") or []
        cls = [dict(run_class(runs[h["run"]]), run=h["run"], overlap_m=h["overlap_m"],
                    ff_m=float(runs[h["run"]]["L_m"])) for h in p if h["run"] in runs]
        base = {"kind": "CARRIED", "group": group, "line_id": l["line_id"], "item_code": l["item_code"],
                "element_id": l["element_id"], "physical_element": "GROUND_BEAM (exterior / perimeter band)",
                "engine_qty_m3": float(l["measured_net"]), "source_ledger": "T-242 + T-253", "source_merged": True,
                "engine_basis": (f"net plan {net:.4f} m2 x interior class depth {depth:.2f} m (perimeter band, no "
                                 f"architectural wall evidence: CONVENTION_ONLY); band drawn {d.get('length_m')} m"
                                 if group == "GB_EXTERIOR_24" else
                                 f"net plan {net:.4f} m2 x interior class depth {depth:.2f} m (band typed interior: no "
                                 f"outside side found; CONVENTION_ONLY); band drawn {d.get('length_m')} m"),
                "printed_support": GB_PRINT, "sheets_searched": GB_SHEETS}
        if not cls:
            recs.append(dict(base, value_m3=None, held_item="pairing of band to a drawn run not established",
                             reason="no T-242 run under this band"))
            continue
        worst = max(cls, key=lambda c: RANK[c["status"]])
        runs_txt = "; ".join(f"{c['run']} {c['cls']} ff {c['ff_m']:.4f} m ({c['why']})" for c in cls)
        ff = math.fsum(c["ff_m"] for c in cls)
        ev = f"runs {runs_txt}; band drawn {d.get('length_m')} m vs face to face {ff:.4f} m"
        if worst["status"] == B.DRAWING_DERIVED_DC:
            v = math.fsum(c["value"] for c in cls)
            recs.append(dict(base, value_m3=v, status=B.DRAWING_DERIVED_DC, evidence=ev,
                             reason=f"sum of the merged runs: {v:.4f} m3 (D printed by two levels of the element; "
                                    "length face to face, T-230 ends)"))
        else:
            lo = [c.get("lo") if c["value"] is None else c["value"] for c in cls]
            hi = [c.get("hi") if c["value"] is None else c["value"] for c in cls]
            items = sorted({c["item"] for c in cls if c["item"]})
            recs.append(dict(base, value_m3=None, status_if_held=worst["status"], held_item="; ".join(items),
                             low_m3=math.fsum(lo) if all(x is not None for x in lo) else None,
                             high_m3=math.fsum(hi) if all(x is not None for x in hi) else None, evidence=ev,
                             reason=f"{worst['cls']} run(s): {worst['why']}"))
        detail.append({"line_id": l["line_id"], "band": band, "band_length_m": d.get("length_m"),
                       "face_to_face_m": round(ff, 4), "runs": [c["run"] for c in cls],
                       "classes": sorted({c["cls"] for c in cls})})
    return recs, detail


def t248_members():
    return {r["member"]: r for r in csv.DictReader((ROOT / "research/agents_t248/LEDGER_T248.csv").open(encoding="utf-8"))}


COL_RE = re.compile(r"^[A-Z]-C:COL:(SH\d+):([^@]+)@(-?\d+),(-?\d+)\|(\w+)$")


def _col_key(eid):
    m = COL_RE.match(eid or "")
    return None if m is None else (m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5))


def column_offset(lines, members):
    """the candidate run and the T-248 register draw the column sheet in two frames that differ by one translation:
    the modal (dx, dy) over every same-sheet, same-mark, same-storey pair (reported; every binding then <= 2 mm)"""
    reg = [k for k in (_col_key(m["route_g_line"]) for m in members.values()) if k]
    votes = collections.Counter()
    for l in lines:
        k = _col_key(l["element_id"])
        if k is None:
            continue
        for r in reg:
            if r[0] == k[0] and r[1] == k[1] and r[4] == k[4]:
                votes[(k[2] - r[2], k[3] - r[3])] += 1
    (dx, dy), n = votes.most_common(1)[0]
    return {"dx": dx, "dy": dy, "votes": n}


def bind_column(eid, members, off, tol=2):
    k = _col_key(eid)
    if k is None:
        return None
    hits = []
    for m in members.values():
        r = _col_key(m["route_g_line"])
        if r and r[0] == k[0] and r[1] == k[1] and r[4] == k[4] and abs(k[2] - off["dx"] - r[2]) <= tol and \
                abs(k[3] - off["dy"] - r[3]) <= tol:
            hits.append(m)
    return hits[0] if len(hits) == 1 else None


def col_records(group, lines, members, off):
    recs = []
    for l in lines:
        eid = l["element_id"]
        m = bind_column(eid, members, off)
        base = {"kind": "CARRIED", "group": group, "line_id": l["line_id"], "item_code": l["item_code"],
                "element_id": eid, "physical_element": "COLUMN", "engine_qty_m3": float(l["measured_net"]),
                "engine_basis": (l.get("formula") or "")[:160], "sheets_searched": COL_SHEETS,
                "source_ledger": "T-248", "source_merged": True}
        if m is None:
            recs.append(dict(base, value_m3=None, held_item="member not bound to T-248", reason="unbound"))
            continue
        top = f"top {m['top_lo'] or '?'} .. {m['top_hi'] or '?'}"
        sup = (f"{m['member']} {m['mark']} base {m['base_lo']} (T-214 structural top); {top}: "
               + ("only the finished roof level is printed (no structural roof level, no build-up: D-39)"
                  if "D-39" in m["causes"] else m["causes"]))
        causes = m["causes"].replace("|", "; ")
        if m["member"] in CB5:
            recs.append(dict(base, source_ledger="T-287 G1", source_merged=False, printed_support=sup,
                             low_m3=None, high_m3=_f(m["m3_hi"]),
                             held_item=f"T-287 G1 verdict (base +0.25 proposed, h 5.20); T-248 {causes}",
                             evidence=f"T-248 {m['member']} {m['status']} {m['m3_lo']} .. {m['m3_hi']} m3",
                             reason="T-287 READY, not merged: its 1.4300 m3 (both CB5 columns) is not carried"))
            continue
        recs.append(dict(base, value_m3=None, printed_support=sup, low_m3=_f(m["m3_lo"]), high_m3=_f(m["m3_hi"]),
                         held_item=causes, evidence=f"T-248 {m['member']} {m['status']} h {m['h_lo'] or '?'} .. "
                                                    f"{m['h_hi'] or '?'} m",
                         reason="column top at an unprinted roof datum (never the finished roof level)"))
    return recs


def st03_records(lines):
    out = []
    for l in lines:
        out.append({"kind": "CARRIED", "group": "ST03", "line_id": l["line_id"], "item_code": l["item_code"],
                    "element_id": l["element_id"], "physical_element": "STAIR FLIGHT ST-03 (entrance +0.15 -> +1.00)",
                    "engine_qty_m3": float(l["measured_net"]),
                    "engine_basis": "straight_flight(5 risers, riser 0.165 convention, going 0.30, width 2.80, waist "
                                    "0.175 convention) = 0.2772 steps + 0.6711 waist",
                    "printed_support": "5 risers over 0.85 m (riser 0.170 drawn), run 1.20 m, width 2.80; no waist "
                                       "thickness printed (T-187 / T-258; S-9)",
                    "sheets_searched": ST_SHEETS, "source_ledger": "T-258", "source_merged": True, "value_m3": None,
                    "low_m3": 0.355017, "high_m3": None,
                    "held_item": "S-9: ST-03 waist not printed (steps 0.355017 m3 DRAWING-CONFIRMED component)",
                    "evidence": "T-258 LEDGER ST-03 E1 steps 0.355017 net of the slab-owned wedge 0.001983",
                    "reason": "convention riser and waist; the line is HELD as a whole, its steps component known"})
    return out


def build():
    cand = _load(HERE / "CANDIDATE_V3015_BASIS_LINES.json")
    pairing = _load(HERE / "BAND_PAIRING_T289.json")
    ctx = {"project_id": cand["project"]["project_id"], "revision_set_sha256": cand["project"]["revision_set_sha256"],
           "candidate": cand["candidate"]}
    g = cand["groups"]
    runs = t242_runs()
    gb, detail = gb_records(g["GB_EXTERIOR_24"], pairing, runs)
    on_main = [l for l in g["GB_OTHER_RELEASED"] if any(
        run_class(runs[h["run"]])["cls"] == "EXTERIOR_MAIN" for h in
        (pairing["bands"].get(l["element_id"].rsplit(":", 1)[-1]) or {}).get("runs") or [] if h["run"] in runs)]
    gb2, detail2 = gb_records(on_main, pairing, runs, "GB_MAIN_EXTERIOR_IN_INTERIOR_LINES")
    gb, detail = gb + gb2, detail + [dict(d, group="GB_MAIN_EXTERIOR_IN_INTERIOR_LINES") for d in detail2]
    mem = t248_members()
    off = column_offset(g["COL_2F"] + g["COL_ANNEX_7"], mem)
    recs = gb + col_records("COL_2F", g["COL_2F"], mem, off) + col_records("COL_ANNEX_7", g["COL_ANNEX_7"], mem, off) + \
        st03_records(g["ST03"])
    rows = B.ledger(NAMED, recs, ctx)
    return cand, rows, detail


def cross_trade(cand):
    out = []
    for l in cand["cross_trade"]:
        out.append({"line_id": l["line_id"], "trade": l["trade"], "item_code": l["item_code"],
                    "element_id": l["element_id"], "unit": l["unit"], "measured_net": l["measured_net"],
                    "evidence_state": l["evidence_state"]})
    return out


def summary(cand, rows, detail):
    return {"schema": "T289_SUMMARY", "candidate": cand["candidate"],
            "candidate_lines_csv_sha256": cand["candidate_lines_csv_sha256"], "project": cand["project"],
            "named_totals_m3": NAMED, "residuals_m3": B.residuals(NAMED, rows), "totals": B.totals(rows),
            "gb_pairing": detail, "cross_trade_lines": cross_trade(cand)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    cand, rows, detail = build()
    s = summary(cand, rows, detail)
    if a.write:
        B.write_csv(HERE / "BASIS_LEDGER_T289.csv", rows)
        (HERE / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("residuals_m3", "totals")}, indent=1))
    return 0


if __name__ == "__main__":
    main()
