"""T-746 development-villa builder: PAINT AT OPENING EDGES AS LM (R-T746-1 .. -3) on ARCH_TAKEOFF_V3.0.74
(research, unwired: no line moves; wiring is the later hub package T-749).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t717/out/LINE_INDEX_V3_0_74.json   candidate of record V3.0.74: the 30 FIN.PAINT ':RETURN_PAINT' lines
                                                     and their FIN.PLASTER return faces
  research/agents_t313/REVEAL_LEDGER_T313.csv        per opening and side: depth, jamb / head / sill m.l (T-313, MERGED;
                                                     door heights 2.20 ASSUMED - OWNER-APPROVED Q-55 C, D-GF-07 2.50
                                                     printed; window sizes T-237; window frame position by DXF handle)
  research/agents_t709/out/T709_RESIDUALS.json       R-T709-4 return flags (5 faces between two wet rooms)
  research/agents_t740/out/T740_PAINT_RULE.json      T-740 face restatement (reading A) and its totals
No coordinate, client name, drawing content or workbook text is stored.

    python3 -I research/agents_t746/t746_alsenan.py           # writes out/T746_PAINT_EDGES.json and .md
    python3 -I research/agents_t746/t746_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t746_rules as R  # noqa: E402

D, q6 = R.D, R.q6
INDEX = ROOT / "research/agents_t717/out/LINE_INDEX_V3_0_74.json"
LEDGER = ROOT / "research/agents_t313/REVEAL_LEDGER_T313.csv"
T709 = ROOT / "research/agents_t709/out/T709_RESIDUALS.json"
T740 = ROOT / "research/agents_t740/out/T740_PAINT_RULE.json"
FRAMES = HERE / "DOOR_FRAMES_T746.csv"
PINS = {INDEX: "6733cbc143cdfffd82eeaee54457f97bbfa7b91b541f648a411825887b8b3bca",
        LEDGER: "2cfa42112aa470c8792d4abe07c9b7471ceecd526974dcd2276dacbff5598730",
        T709: "fcbd5aa7d9a12018358a757a284fa746302f44b9ddb122f51c9ad7a53bd82151",
        T740: "3918f7e4382728ea990b900cce5bdda059ede9d9356b4f24c7a24f6835efaff8",
        FRAMES: "ec54cd8870ee76f41772ecadb6e571c9d5dd8619cf3b864f0e2ad1069c042049"}
OUT_JSON = HERE / "out" / "T746_PAINT_EDGES.json"
OUT_MD = HERE / "out" / "T746_PAINT_EDGES.md"
RET = ":RETURN_PAINT"
KIND = {"D": "DOOR", "W": "WINDOW", "A": "ARCH"}
GATES = {"D-GF-15"}                      # T-249 census: the gate (width / height HELD)


def _pins():
    return dict(PINS)


def _pinned(p, pins):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != pins[p]:
        raise SystemExit(f"input changed: {p.relative_to(ROOT)} sha256 {h} (pinned {pins[p]})")
    return p


def _kind(oid):
    return "GATE" if oid in GATES else KIND[oid[0]]


def _ledger(pins):
    """opening -> {side -> {component -> row}}; refuses a component twice."""
    out = {}
    with open(_pinned(LEDGER, pins), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            side = out.setdefault(r["opening"], {"kind": r["kind"], "sides": {}})["sides"].setdefault(r["side"], {})
            if r["component"] in side:
                raise SystemExit(f"ledger: {r['opening']} {r['side']} {r['component']} twice")
            side[r["component"]] = r
    return out


def _size(side):
    """(width, height, depth, src) of one side from its JAMBS / HEAD rows; None where not measured."""
    j, h = side.get("JAMBS"), side.get("HEAD")
    if not j or not h or j["state"] != "MEASURED" or h["state"] != "MEASURED" or not j["ml"] or not h["ml"]:
        return None, None, (j or {}).get("depth_m") or None, "jambs / head not measured in the T-313 ledger: " + \
            ", ".join(f"{c} {r['state']}" for c, r in side.items() if c in ("JAMBS", "HEAD"))
    width, height = D(h["ml"]), D(j["ml"]) / 2
    if D(j["depth_m"]) != D(h["depth_m"]):
        raise SystemExit("jamb and head depths differ")
    return width, height, D(j["depth_m"]), f"T-313 ledger: {j['basis']}; {h['basis']} ({j['evidence']})"


def build():
    pins = _pins()
    idx = json.loads(_pinned(INDEX, pins).read_text(encoding="utf-8"))
    t709 = json.loads(_pinned(T709, pins).read_text(encoding="utf-8"))
    t740 = json.loads(_pinned(T740, pins).read_text(encoding="utf-8"))
    led = _ledger(pins)
    by_el = {x["element_id"]: x for x in idx["lines"]}
    by_line = {x["line_id"]: x for x in idx["lines"]}
    # plaster return line id -> opening (T-313 binding of the 22 doors), REVEAL element ids name the rest
    plaster_to_open = {}
    for oid, o in led.items():
        for side in o["sides"].values():
            for r in side.values():
                if r["line_id"].startswith("L-") and r["component"] in ("JAMBS", "HEAD") and o["kind"] != "WINDOW":
                    plaster_to_open.setdefault(r["line_id"], set()).add(oid)
    wet_both = {r["face_id"] for r in t709["c_return_paint"]["rows"]
                if "NOT_ESTABLISHED" in str((r.get("paint_row") or {}).get("flag", ""))}
    if len(wet_both) != 5:
        raise SystemExit(f"T-709 wet-both flags {len(wet_both)} != 5")
    a_faces = {f["paint_element"]: f for f in t740["faces"] if f["class"] == "RETURN"}
    with open(_pinned(FRAMES, pins), encoding="utf-8") as f:
        frames = {r["opening"]: r for r in csv.DictReader(f)}

    # ---- (2) the 30 return-paint lines, by line id
    ret_lines = sorted((x for x in idx["lines"] if x["element_id"].endswith(RET)), key=lambda x: x["element_id"])
    if len(ret_lines) != 30:
        raise SystemExit(f"{len(ret_lines)} return-paint lines, expected 30")
    rows, pairs, bound_open = [], [], set()
    for q in ret_lines:
        pel = q["element_id"][: -len(RET)]
        p = by_el[pel]
        m = re.search(r"REVEAL-([ADW]-[A-Z0-9]+-\d+|[AD]-\d?[A-Z]+-\d+)", pel)
        if m:
            oid = m.group(1)
        else:
            s = plaster_to_open.get(p["line_id"], set())
            if len(s) != 1:
                raise SystemExit(f"{pel}: plaster line {p['line_id']} binds {sorted(s)} in the ledger")
            oid = next(iter(s))
        pairs.append((oid, q["line_id"]))
        bound_open.add(oid)
        o = led[oid]
        w, h, t, src = _size(o["sides"]["THROUGH"])
        kind = _kind(oid)
        plaster = None
        if p["class"] == "RELEASED":
            plaster = (D(p["measured_net"]), D(p["measured_net"]))
        elif p["held_low"] is not None and p["held_high"] is not None:
            plaster = (D(p["held_low"]), D(p["held_high"]))
        fr = frames.get(oid) or {}
        frame_drawn = fr.get("frame_at_jambs") == "True" and w is not None
        if frame_drawn and (D(fr["opening_w_m"]) != w or D(fr["wall_depth_m"]) != t):
            raise SystemExit(f"{oid}: frame block {fr['opening_w_m']} x {fr['wall_depth_m']} vs ledger {w} x {t}")
        head_c = "WET_BOTH_SIDES_TILE_NOT_ESTABLISHED" if pel in wet_both else "FRAME_COVERAGE_NOT_PRINTED"
        if w is None:
            e = R.edge_parts(kind, None, None)
        elif frame_drawn:
            e = R.edge_parts(kind, w, h, jambs="FRAME_COVERS_RETURN_DRAWN", head=head_c)
        else:
            e = R.edge_parts(kind, w, h, jambs=head_c, head=head_c)
        frame_ev = (f"plan block {fr.get('block')} handle {fr.get('handle')}: frame posts {fr.get('post_w_m')} m over "
                    f"the full wall depth {fr.get('wall_depth_m')} m at the drawn masonry jambs (offsets "
                    f"{fr.get('jamb_offsets_mm')} mm)" if frame_drawn else
                    f"handle {fr.get('handle') or '-'}: {fr.get('evidence') or 'no census symbol'}"
                    + (f" (block {fr.get('opening_w_m')} m vs masonry {fr.get('masonry_w_m')} m)"
                       if fr.get("masonry_w_m") else ""))
        r = R.restate_return_line(plaster, t, e) if (plaster is not None or e["status"] == "HELD") else None
        if plaster is None and e["status"] != "HELD":
            # a blank plaster face with known sizes: the lm stays HELD with the face (never a value on a blank face)
            e = dict(e, status="HELD", lm=None, cause="PLASTER_FACE_BLANK",
                     why="the plaster return line is blank: its edge lm is HELD with it (sizes known: "
                         f"{e['gross_lm']} lm gross)")
            r = R.restate_return_line(None, t, e)
        eng = None
        if q["class"] == "RELEASED":
            eng = (D(q["measured_net"]),) * 2
        elif q["held_low"] is not None and q["held_high"] is not None:
            eng = (D(q["held_low"]), D(q["held_high"]))
        af = a_faces.get(q["element_id"])
        if af is None:
            raise SystemExit(f"{q['element_id']} not in the T-740 faces")
        floor = pel[:2]
        rows.append({"opening": oid, "kind": kind, "floor": floor,
                     "rooms": (o["sides"]["THROUGH"].get("JAMBS") or {}).get("room", ""),
                     "plaster_line": p["line_id"], "paint_line": q["line_id"], "paint_element": q["element_id"],
                     "depth": None if t is None else str(t), "width": None if w is None else str(w),
                     "height": None if h is None else str(h), "size_source": src,
                     "plaster_m2": None if plaster is None else [str(q6(plaster[0])), str(q6(plaster[1]))],
                     "paint_m2_before_engine": None if eng is None else [str(q6(eng[0])), str(q6(eng[1]))],
                     "paint_m2_before_rule_A": af["rule_paint"],
                     "paint_m2_after_B": None if r["paint_m2_after"] is None else [str(x) for x in r["paint_m2_after"]],
                     "edge_lm_after_B": None if e["lm"] is None else [str(x) for x in e["lm"]],
                     "gross_lm": None if e["gross_lm"] is None else str(e["gross_lm"]),
                     "status": e["status"], "cause": e["cause"], "why": e["why"],
                     "parts": e.get("parts", []), "frame": frame_ev})
    R.bind_once(pairs)
    # every door / arch / gate of the census is bound to exactly one return line
    through = sorted(k for k, o in led.items() if "THROUGH" in o["sides"])
    missing = sorted(set(through) - bound_open)
    if missing:
        raise SystemExit(f"census openings with no return line: {missing}")

    # ---- (1) windows: room side and outside, by opening id
    win = []
    for oid in sorted(k for k, o in led.items() if o["kind"] in ("WINDOW", "FLOOR_GLAZING")):
        sides = led[oid]["sides"]
        for side in ("IN", "OUT"):
            s = sides.get(side, {})
            states = {r["state"] for c, r in s.items() if c in ("JAMBS", "HEAD")}
            if side == "IN" and states == {"NONE"}:
                e = R.edge_lm("WINDOW", D("1"), D("1"), zero_cause="FRAME_FLUSH_NO_RETURN")
                e = dict(e, gross_lm=None, why="frame flush with the room face (T-313 by DXF handle, DRAWING-CONFIRMED): "
                                               "no room-side return, 0 lm (also in a tiled wall)")
                w = h = t = None
                src = "T-313 WINDOW_DEPTHS: depth_in 0.000"
            else:
                w, h, t, src = _size(s)
                e = R.edge_lm("WINDOW", w, h)
                if e["status"] == "HELD":
                    known = [f"{c} {r['ml']} m.l" for c, r in s.items() if c in ("JAMBS", "HEAD") and r["ml"]]
                    if known:
                        e = dict(e, why=e["why"] + "; known part " + ", ".join(known) + " (not a value of the whole)")
            sill = s.get("SILL") or s.get("THRESHOLD")
            win.append({"opening": oid, "side": side, "kind": led[oid]["kind"],
                        "room": (s.get("JAMBS") or s.get("HEAD") or {}).get("room", ""),
                        "depth": None if t is None else str(t), "width": None if w is None else str(w),
                        "height": None if h is None else str(h), "size_source": src,
                        "edge_lm": None if e["lm"] is None else [str(x) for x in e["lm"]],
                        "status": e["status"], "cause": e["cause"], "why": e["why"],
                        "sill": None if not sill or side == "IN" else
                        f"{sill['component']} {sill['ml'] or '0'} m.l: own item (bound to ARCH.WINDOW_REVEAL "
                        f"{sill['line_id']}), finish not printed as paint: not a paint edge",
                        "line": "NO LINE (window outside jambs / head: missing family, T-313)" if side == "OUT"
                        else "none needed (0)"})

    # ---- (3) totals and per floor
    def tot(rs, key):
        return R.sum_lm([{"lm": None if r[key] is None else tuple(r[key])} for r in rs])

    door_lm = tot(rows, "edge_lm_after_B")
    win_out = [w for w in win if w["side"] == "OUT"]
    win_lm = tot(win_out, "edge_lm")
    by_floor = {}
    for fl in ("GF", "1F", "2F"):
        rr = [r for r in rows if r["floor"] == fl]
        ret_a = [tuple(r["paint_m2_before_rule_A"]) for r in rr if r["paint_m2_before_rule_A"]]
        ret_e = [tuple(r["paint_m2_before_engine"]) for r in rr if r["paint_m2_before_engine"]]
        before = t740["by_floor"][fl]
        ra = R.paint_after(before["rule_paint"], ret_a)
        re_ = R.paint_after(before["engine_paint"], ret_e)
        by_floor[fl] = {"return_lines": len(rr), "door_edge_lm": [str(x) for x in tot(rr, "edge_lm_after_B")["lm"]],
                        "door_edge_held": tot(rr, "edge_lm_after_B")["held"],
                        "window_out_edge_lm": [str(x) for x in tot([w for w in win_out if
                                                                    _wfloor(w) == fl], "edge_lm")["lm"]],
                        "rule_paint_A": before["rule_paint"], "rule_paint_B": [str(x) for x in ra["after"]],
                        "returns_removed_rule": [str(x) for x in ra["removed"]],
                        "engine_paint": before["engine_paint"], "engine_paint_returns_out": [str(x) for x in re_["after"]],
                        "returns_removed_engine": [str(x) for x in re_["removed"]]}
    allA = [tuple(r["paint_m2_before_rule_A"]) for r in rows if r["paint_m2_before_rule_A"]]
    allE = [tuple(r["paint_m2_before_engine"]) for r in rows if r["paint_m2_before_engine"]]
    tA = R.paint_after(t740["totals"]["rule_paint"], allA)
    tE = R.paint_after(t740["totals"]["engine_paint"], allE)
    # residual: the floors re-add to the total (rooms untouched: only the 30 return lines move)
    resid = [q6(D(tA["after"][e]) - sum((D(by_floor[f]["rule_paint_B"][e]) for f in by_floor), D(0))) for e in (0, 1)]
    if any(resid):
        raise SystemExit(f"floor re-add residual {resid}")
    # identity on each valued line: plaster high = depth x gross lm (asserted in R.restate_return_line)
    status_n = {}
    for r in rows:
        status_n[r["status"]] = status_n.get(r["status"], 0) + 1
    wstatus = {}
    for w in win:
        k = f"{w['side']} {w['status']}"
        wstatus[k] = wstatus.get(k, 0) + 1
    parts_sum = {}
    for r in rows:
        for pt in r["parts"]:
            a = parts_sum.setdefault(pt["part"], [D(0), D(0), D(0)])
            a[0] += D(pt["lm"][0])
            a[1] += D(pt["lm"][1])
            a[2] += D(pt["gross"])
    frames_drawn = sum(1 for r in rows if r["frame"].startswith("plan block"))
    return {"schema": "URBAN_T746_PAINT_EDGES_V1", "candidate": idx["candidate_version"],
            "rules": list(R.RULE_IDS), "owner_rule": R.OWNER_RULE,
            "inputs_sha256_16": {str(p.relative_to(ROOT)): h[:16] for p, h in pins.items()},
            "return_lines": {"count": len(rows), "by_status": dict(sorted(status_n.items())),
                             "edge_lm": [str(x) for x in door_lm["lm"]], "held": door_lm["held"],
                             "paint_m2_removed_rule_A": [str(x) for x in tA["removed"]],
                             "paint_m2_removed_engine": [str(x) for x in tE["removed"]],
                             "frames_drawn_full_depth": frames_drawn,
                             "by_part": {k: {"lm": [str(q6(v[0])), str(q6(v[1]))], "gross": str(q6(v[2]))}
                                         for k, v in sorted(parts_sum.items())}},
            "windows": {"sides": len(win), "by_side_status": dict(sorted(wstatus.items())),
                        "outside_edge_lm": [str(x) for x in win_lm["lm"]], "outside_held": win_lm["held"]},
            "paint_m2": {"rule_A_T740": t740["totals"]["rule_paint"], "rule_B_after": [str(x) for x in tA["after"]],
                         "engine_V3_0_74": t740["totals"]["engine_paint"],
                         "engine_returns_out": [str(x) for x in tE["after"]], "floor_readd_residual": [str(x) for x in resid]},
            "by_floor": by_floor, "return_rows": rows, "window_rows": win}


def _wfloor(w):
    room = w["room"]
    return {"ST-GF": "GF", "ST-1F": "1F", "ST-2F": "2F"}.get(room, room[:2])


def md(o):
    L = [f"# T-746 paint at opening edges as lm on {o['candidate']} (generated; research, unwired)", "",
         f"Rules {', '.join(o['rules'])}; {o['owner_rule']}. A return is an lm item (2 x h + w per opening side), its "
         "paint m2 moves to the lm line; plaster m2 untouched.", "",
         "## Totals", "",
         f"- 30 return-paint lines: edge lm {o['return_lines']['edge_lm'][0]} .. {o['return_lines']['edge_lm'][1]}, "
         f"HELD {o['return_lines']['held']}; by status {o['return_lines']['by_status']}; frames drawn over the full "
         f"wall depth {o['return_lines']['frames_drawn_full_depth']}; by part {o['return_lines']['by_part']}",
         f"- paint m2 leaving the m2 lines: rule (reading A, T-740) {o['return_lines']['paint_m2_removed_rule_A']}, "
         f"engine V3.0.74 {o['return_lines']['paint_m2_removed_engine']}",
         f"- windows ({o['windows']['sides']} sides): {o['windows']['by_side_status']}; outside edge lm "
         f"{o['windows']['outside_edge_lm'][0]} .. {o['windows']['outside_edge_lm'][1]}, HELD {o['windows']['outside_held']}",
         f"- paint m2: rule A {o['paint_m2']['rule_A_T740']} -> rule B {o['paint_m2']['rule_B_after']}; engine "
         f"{o['paint_m2']['engine_V3_0_74']} -> returns out {o['paint_m2']['engine_returns_out']}; floor re-add residual "
         f"{o['paint_m2']['floor_readd_residual']}", "",
         "## By floor (m2 unless lm)", "",
         "| floor | return lines | door edge lm | window outside lm | rule paint A | rule paint B | engine paint | engine returns out |",
         "|---|---|---|---|---|---|---|---|"]
    for fl, d in o["by_floor"].items():
        L.append(f"| {fl} | {d['return_lines']} | {' .. '.join(d['door_edge_lm'])} (HELD {d['door_edge_held']}) | "
                 f"{' .. '.join(d['window_out_edge_lm'])} | {' .. '.join(d['rule_paint_A'])} | {' .. '.join(d['rule_paint_B'])} | "
                 f"{' .. '.join(d['engine_paint'])} | {' .. '.join(d['engine_paint_returns_out'])} |")
    L += ["", "## Return-paint lines restated (by line id)", "",
          "| opening | floor | rooms | paint line | depth | w | h | plaster m2 | paint m2 engine | paint m2 A | paint m2 B | edge lm B | status | cause | frame |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    j = lambda v: "blank" if v is None else (" .. ".join(v) if isinstance(v, list) else v)  # noqa: E731
    for r in o["return_rows"]:
        L.append(f"| {r['opening']} | {r['floor']} | {r['rooms']} | {r['paint_line']} | {j(r['depth'])} | {j(r['width'])} | "
                 f"{j(r['height'])} | {j(r['plaster_m2'])} | {j(r['paint_m2_before_engine'])} | {j(r['paint_m2_before_rule_A'])} | "
                 f"{j(r['paint_m2_after_B'])} | {j(r['edge_lm_after_B'])} | {r['status']} | {r['cause'] or '-'} | {r['frame']} |")
    L += ["", "## Windows (room side and outside)", "",
          "| opening | side | room | depth | w | h | edge lm | status | cause | sill / threshold |", "|---|---|---|---|---|---|---|---|---|---|"]
    for w in o["window_rows"]:
        L.append(f"| {w['opening']} | {w['side']} | {w['room']} | {j(w['depth'])} | {j(w['width'])} | {j(w['height'])} | "
                 f"{j(w['edge_lm'])} | {w['status']} | {w['cause'] or '-'} | {w['sill'] or '-'} |")
    return "\n".join(L) + "\n"


def main(argv):
    o = build()
    js = json.dumps(o, indent=1, ensure_ascii=False) + "\n"
    mdt = md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == mdt
        print("T746 outputs " + ("match" if ok else "DIFFER"))
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(mdt, encoding="utf-8")
    print(json.dumps({k: o[k] for k in ("return_lines", "windows", "paint_m2")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
