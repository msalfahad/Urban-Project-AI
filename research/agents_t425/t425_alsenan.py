"""T-425 development-villa binding of the stair TREAD (B7-02) / STEP (B7-06) lines of the candidate to the drawn flights.

Build (needs the PRIVATE inputs, decoded into .work/private only, and a finished V3.0.36 run of
research/agents_t246/v3036_run.py on them):
    python3 -I research/agents_t425/t425_alsenan.py --dxf <P7757.dxf> --candidate <run>/v3036/V3_0_36_BOQ_LINES.json \
        --write
re-reads every front edge used below BY HANDLE in the architectural DXF (asserting layer, length 1.150 / 2.800 and the
0.300 front-to-front going), binds every candidate stair reading (calculation input 'flight_id') to a drawn flight with
its ROLE, and writes BINDING_T425.json, LINE_TABLE_T425.csv and FLIGHT_TABLE_T425.csv beside this file. Check (no
private input):
    python3 -I research/agents_t425/t425_alsenan.py --check
recomputes both tables from the committed BINDING_T425.json and prints REPRODUCED.

Only handles, run positions, lengths, counts, engine ids and quantities are written (no coordinates, no drawing text,
no client data). Drawn tread lists come from the merged T-412 census (research/agents_t412/ALSENAN_EDGES_T412.json,
MERGED f9c80501) and are re-read here by handle (--dxf).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import tread_binding as TB  # noqa: E402

T412 = ROOT / "research" / "agents_t412" / "ALSENAN_EDGES_T412.json"
BINDING = HERE / "BINDING_T425.json"
LINE_CSV = HERE / "LINE_TABLE_T425.csv"
FLIGHT_CSV = HERE / "FLIGHT_TABLE_T425.csv"
CODES = {"FIN.MARBLE.TREAD": "B7-02", "FIN.STAIR.STEP_LM": "B7-06"}

# drawn going of each tread = front-to-front spacing on the same sheet (0.300 on every straight flight, asserted by
# handle in --dxf), and for the LAST tread of a flight the distance to the drawn landing / floor edge or riser line:
#   MS1-L  9 straight treads DC .. C5; C5 -> 485 0.300 (485 = the front of the first winder: inside the HELD turn MS1-T)
#   MS1-U  11 treads A92 .. ABE; ABE's rear (the 1F floor edge) is NOT on the architectural plan but IS on the
#          structural GF roof slab plan (ST p.4, 12th line 459 at s 3.30): going 0.300 drawn on the second drawing
#   MS2-L  11 treads AC0 .. (A97 = landing edge MS2-LD)
#   MS2-U  11 treads 135B .. 1386; 1386's rear (the 2F floor edge) is drawn on neither sheet (ST p.5 draws 11 lines):
#          going NOT drawn -> that tread's m2 HELD by name; its piece / step lm stand (front edge 1386 drawn)
#   D1 3 treads 481 484 48F (490 = floor edge); RS-S 10 treads B43 .. (B4D = landing RS-LD); RS-A 4 (D22 = floor edge);
#   E1 4 treads (30A = platform edge), width 2.800
#   RS-C 12 radial treads: HELD (Q-50 A cond, curved part); MS1-T winder turn: HELD (owner S-9; three-source count
#   conflict C-ST-3, T-412 s.6)
LAST_GOING = {"MS1-U": ("ST p.4 459 at s 3.30 (12th line)", 0.300), "MS2-U": None}
HELD_FLIGHTS = {"RS-C": "Q-50 A cond: curved flight reconstructed from the plans, curved part HELD (RFI-S27)",
                "MS1-T": "owner S-9 / C-ST-3: winder turn counts conflict (A-A 5, arch plans 4 wedges, ST p.4 3 radial "
                         "+ 2 straight); winders never generated, HELD"}

# engine reading (candidate calculation input 'flight_id') -> (drawn flight, ROLE, basis). ROLE: OWN = the plan whose
# cut the flight lies below (its own reading); SEEN_THROUGH = the same flight drawn again on the plan above, through the
# stair opening; PARTIAL = a part of the flight on the plan below, above its cut (hidden lines)
ENGINE_TO_DRAWN = {
    "SITE-3759f2457b22cb4a:F1": ("MS1-L", "OWN", "GF plan, west lane; 8 hidden riser-face lines DE .. CD (+0.050), "
                                                 "7 treads; C5 and 485 above the cut not read"),
    "SITE-3759f2457b22cb4a:F2": ("D1", "OWN", "GF plan, 4 solid lines 481 .. 490"),
    "SITE-735e111dcf9b22c8:F1": ("RS-C", "OWN", "GF plan, RADIAL 13 lines"),
    "SITE-735e111dcf9b22c8:F2": ("RS-S", "PARTIAL", "GF plan above the cut (RS-S +2.929 -> +4.696); 7 lines"),
    "SITE-735e111dcf9b22c8:F3": ("RS-S", "PARTIAL", "GF plan, the rest of RS-S (4 lines), bound by elimination (T-412)"),
    "SITE-735e111dcf9b22c8:F4": ("RS-A", "PARTIAL", "GF plan above the cut (RS-A +4.696 -> +5.50)"),
    "SITE-a95bf979baf4cfae:F1": ("RS-C", "SEEN_THROUGH", "1F plan through the reception void"),
    "SITE-a95bf979baf4cfae:F2": ("MS2-L", "OWN", "1F plan, west lane, 12 solid lines AC0 .. A97"),
    "SITE-a95bf979baf4cfae:F3": ("MS1-U", "OWN", "1F plan, east lane, 11 solid lines A92 .. ABE"),
    "SITE-a95bf979baf4cfae:F4": ("RS-S", "OWN", "1F plan, 11 lines B43 .. B4D (below the 1F cut)"),
    "SITE-a95bf979baf4cfae:F5": ("MS1-T", "SEEN_THROUGH", "1F plan, ST-01 shaft north end: the winder turn seen down "
                                                          "through the opening (radials BE6 / BE8 / BEA solid with "
                                                          "companions BE7 / BE9 / BEB, layer 2)"),
    "SITE-a95bf979baf4cfae:F6": ("RS-A", "OWN", "1F plan, 5 lines B59 .. D22 (below the 1F cut)"),
    "SITE-d7254c68fd33723d:F1": ("MS2-L", "SEEN_THROUGH", "2F plan, west lane: 11 solid lines at the same run positions "
                                                          "-0.30 .. 2.70 as 1F AC0 .. A97 (137D .. 135F with hidden "
                                                          "companions +0.050); no flight leaves 2F (T-184 R-STAIR-CONT-1)"),
    "SITE-d7254c68fd33723d:F2": ("MS2-U", "OWN", "2F plan, east lane, 11 solid lines 135B .. 1386"),
}
LCOLS = ["line_id", "code", "engine_flight", "flight", "role", "engine_treads", "action", "before", "after", "delta",
         "status", "beside", "cause", "notes"]
FCOLS = ["flight", "stair", "drawn_treads", "treads_m2_valued", "treads_m2_held", "tread_m2_drawn", "step_lm_drawn",
         "readings", "valued_readings", "candidate_tread_m2_before", "candidate_step_lm_before",
         "candidate_tread_m2_after", "candidate_step_lm_after"]


def drawn_flights():
    """the drawn flights with every tread's width and going (from the merged T-412 edge table)."""
    d = json.loads(T412.read_text(encoding="utf-8"))
    out = []
    for f in d["flights"]:
        fid = f["flight"]
        es = sorted((e for e in d["edges"] if e["flight"] == fid), key=lambda e: e["riser_no"])
        treads = [e for e in es if e["kind"] == "TREAD" or (e["kind"] == "WINDER" and fid == "MS1-T")]
        if fid == "MS1-L":
            treads = [e for e in es if e["kind"] == "TREAD"]          # 485 (WINDER) belongs to the HELD turn
        if not treads:
            continue
        rows = []
        for e in treads:
            k = es.index(e)
            nxt = es[k + 1] if k + 1 < len(es) else None
            front = e["handles"][0] if e["handles"] else e["eid"]
            w = float(e["length_m"]) if e.get("length_m") is not None else None
            if fid in HELD_FLIGHTS:
                rows.append(TB.Tread(front, w if w is not None else 1.15, None))
                continue
            if nxt is not None and nxt["status"] == "DRAWING-CONFIRMED" and nxt["handles"]:
                g = round(abs(float(nxt["s"]) - float(e["s"])), 6)
                rows.append(TB.Tread(front, w, g, f"arch DXF {front} -> {nxt['handles'][0]}"))
            elif LAST_GOING.get(fid):
                src, g = LAST_GOING[fid]
                rows.append(TB.Tread(front, w, g, src))
            else:
                rows.append(TB.Tread(front, w, None))
        out.append(TB.Flight(fid, tuple(rows), HELD_FLIGHTS.get(fid, "")))
    return out


def readings_from(lines):
    by = {}
    for x in lines:
        if x["item_code"] in CODES:
            inp = x["calculation"].get("inputs") or {}
            if "flight_id" in inp:
                by.setdefault(inp["flight_id"], {})[x["item_code"]] = x
    if set(by) != set(ENGINE_TO_DRAWN):
        raise SystemExit(f"candidate readings differ from the binding table: {sorted(set(by) ^ set(ENGINE_TO_DRAWN))}")
    out = []
    for fid, xs in sorted(by.items()):
        t, s = xs["FIN.MARBLE.TREAD"], xs["FIN.STAIR.STEP_LM"]
        fl, role, basis = ENGINE_TO_DRAWN[fid]
        st = t["evidence_state"]
        out.append({"engine_flight": fid, "flight": fl, "role": role, "tread_line": t["line_id"],
                    "step_line": s["line_id"], "state": st, "step_state": s["evidence_state"],
                    "treads": t["calculation"]["inputs"]["treads"], "tread_m2": t["measured_net"],
                    "step_lm": s["measured_net"], "width_m": t["calculation"]["inputs"].get("width_m"),
                    "kind": t["calculation"]["inputs"].get("kind"), "basis": basis})
    return out


def compute(readings):
    fl = drawn_flights()
    rs = [TB.Reading(r["engine_flight"], r["flight"], r["role"], r["tread_line"], r["step_line"], r["state"],
                     r["treads"], r["tread_m2"], r["step_lm"], r["basis"]) for r in readings]
    rows = TB.bind(fl, rs)
    return fl, rs, rows


def _f(v):
    return "" if v is None else (f"{v:.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))


def tables(readings):
    fl, rs, rows = compute(readings)
    role = {r.engine_flight: (r.role, r.treads) for r in rs}
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(LCOLS)
    for r in sorted(rows, key=lambda r: (r.flight or "~", r.engine_flight, r.code)):
        w.writerow([r.line_id, r.code, r.engine_flight, r.flight or "", role[r.engine_flight][0],
                    role[r.engine_flight][1], r.action, _f(r.before), _f(r.after), _f(r.delta), r.status,
                    _f(r.beside), r.cause, " | ".join(r.notes)])
    lt = b.getvalue()
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(FCOLS)
    stair = {f["flight"]: f["stair"] for f in json.loads(T412.read_text(encoding="utf-8"))["flights"]}
    for f in fl:
        n, step, m2, held, beside = TB.drawn_quantities(f)
        mine = [r for r in rows if r.flight == f.fid]
        rd = sorted({r.engine_flight for r in mine})
        vd = sorted({r.engine_flight for r in mine if r.before is not None})
        def sm(code, k):
            vs = [getattr(r, k) for r in mine if r.code == code and getattr(r, k) is not None]
            return round(sum(vs), 6) if vs else None
        held_flight = bool(f.held_cause)
        w.writerow([f.fid, stair.get(f.fid, ""), n, "" if held_flight else n - len(held),
                    n if held_flight else len(held), "" if held_flight else _f(m2), "" if held_flight else _f(step),
                    " ".join(rd), " ".join(vd), _f(sm("B7-02", "before")), _f(sm("B7-06", "before")),
                    _f(sm("B7-02", "after")), _f(sm("B7-06", "after"))])
    return lt, b.getvalue(), TB.totals(rows)


def read_dxf(path):
    """own re-read by handle: every front edge used, its layer and length; the 0.300 spacing; the 2F west-lane lines
    at the 1F MS2-L run positions; the 1F winder radials."""
    import math
    import ezdxf
    msp = ezdxf.readfile(path).modelspace()
    H = {e.dxf.handle: e for e in msp if e.dxftype() == "LINE"}

    def L(h):
        e = H[h]
        return e.dxf.layer, round(math.hypot(e.dxf.end.x - e.dxf.start.x, e.dxf.end.y - e.dxf.start.y) / 1000, 3), \
            e.dxf.start.y / 1000

    d = json.loads(T412.read_text(encoding="utf-8"))
    checked = 0
    for e in d["edges"]:
        h = e["handles"][0] if e["handles"] else None
        if h in H and e["shape"] == "STRAIGHT" and e["kind"] != "WINDER" and e.get("length_m") is not None:
            lay, ln, _ = L(h)
            assert abs(ln - float(e["length_m"])) < 0.002 or e["flight"] in ("MS1-T",) or h == "C8", (h, ln, e["length_m"])
            checked += 1
    # 2F west lane = MS2-L seen through: 11 solid lines 0.300 apart, the same run positions as 1F ABF .. A97
    two_f = ["1387", "137D", "137E", "137F", "1380", "1375", "1376", "1378", "1377", "1360", "135F"]
    one_f = ["ABF", "AB5"]
    ys = [L(h)[2] for h in two_f]
    assert all(L(h)[0] == "5" and abs(L(h)[1] - 1.15) < 0.002 for h in two_f)
    assert all(abs((ys[i + 1] - ys[i]) - 0.300) < 1e-6 for i in range(10))
    off = L("ABF")[2] - ys[0]
    assert abs((L("AB5")[2] - off) - ys[1]) < 1e-6 and abs((L("A97")[2] - off) - ys[-1]) < 1e-6
    # 1F winder radials in the ST-01 shaft (the F5 reading): solid + companion layer 2
    rad = {h: L(h) for h in ("BE6", "BE8", "BEA", "BE7", "BE9", "BEB")}
    assert [rad[h][0] for h in ("BE6", "BE8", "BEA")] == ["5"] * 3 and [rad[h][0] for h in ("BE7", "BE9", "BEB")] == ["2"] * 3
    return {"edges_rechecked": checked, "2F_west_lane_lines": len(two_f) + 0 * len(one_f),
            "2F_west_lane_equals_1F_MS2L_positions": True,
            "1F_winder_radials": {h: rad[h][1] for h in rad}}


# The freelancer's ST-01 piece count (63, one piece per step, FIN workbook; quantities only, T-412 s.5) against the drawn
# 56 risers (MS1-L 10 + turn 5 + MS1-U 12 + MS2-L 12 + MS2-TR 1 + MS2-U 12 + D1 4; A-A, Q-46 A). Levels (T-184): lobby
# +0.30, GF stair foot +1.00, 1F +5.50, 2F +9.70. Hypothesis test: pieces = ceil(storey rise / r) per storey for a
# uniform assumed riser r, NOT the drawn count. Only r = 0.150 reproduces 63, on two splits.
LEVELS = {"D1": (0.30, 1.00), "GF-1F": (1.00, 5.50), "1F-2F": (5.50, 9.70)}
DRAWN_RISERS_ST01 = {"D1": 4, "GF-1F": 10 + 5 + 12, "1F-2F": 12 + 1 + 12}


def freelancer_trace(target=63, risers=(0.150, 0.155, 0.160, 0.165, 0.170, 0.175)):
    import math
    out = []
    for r in risers:
        per = {k: math.ceil(round((b - a) / r, 9)) for k, (a, b) in LEVELS.items()}
        merged = math.ceil(round((LEVELS["1F-2F"][0] - LEVELS["D1"][0]) / r, 9)) + per["1F-2F"]
        out.append({"riser_m": r, "per_storey": per, "sum_per_storey": sum(per.values()),
                    "sum_lobby_to_1F_merged": merged,
                    "matches": [n for n, v in (("per storey", sum(per.values())), ("lobby->1F merged", merged))
                                if v == target]})
    return out


def main(argv):
    if "--check" in argv:
        b = json.loads(BINDING.read_text(encoding="utf-8"))
        lt, ft, tot = tables(b["readings"])
        assert lt == LINE_CSV.read_text(encoding="utf-8") and ft == FLIGHT_CSV.read_text(encoding="utf-8"), "tables differ"
        assert tot == b["totals"], (tot, b["totals"])
        print("REPRODUCED", json.dumps(tot, sort_keys=True))
        return 0
    dxf = argv[argv.index("--dxf") + 1]
    cand = argv[argv.index("--candidate") + 1]
    import hashlib
    raw = Path(cand).read_bytes()
    lines = json.loads(raw)
    lines = lines["lines"] if isinstance(lines, dict) else lines
    rd = read_dxf(dxf)
    readings = readings_from(lines)
    lt, ft, tot = tables(readings)
    other = {}
    for x in lines:
        if x["item_code"] in ("FIN.MARBLE.LANDING", "FIN.MARBLE.RISER", "FIN.STAIR.FLIGHT"):
            other.setdefault(x["item_code"], []).append({"line_id": x["line_id"], "state": x["evidence_state"],
                                                          "net": x["measured_net"],
                                                          "flight_id": (x["calculation"].get("inputs") or {}).get("flight_id"),
                                                          "element": x["location"]["element_id"]})
    out = {"schema": "T425_BINDING_1", "candidate": "ARCH_TAKEOFF_V3.0.36", "file": Path(cand).name,
           "sha256": hashlib.sha256(raw).hexdigest(), "lines": len(lines), "dxf_reread": rd, "readings": readings,
           "other_stair_lines": other, "totals": tot}
    print(json.dumps(tot, indent=1, sort_keys=True))
    if "--write" in argv:
        BINDING.write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        LINE_CSV.write_text(lt, encoding="utf-8")
        FLIGHT_CSV.write_text(ft, encoding="utf-8")
    print(lt)
    print(ft)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
