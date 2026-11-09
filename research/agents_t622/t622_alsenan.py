"""T-622 builder (development villa; research, unwired): the 47 UNKNOWN rows of statement V10 section T-547/wall-tile
(scorecard V10, research/agents_t613/out/SCORECARD_T613.json, read only) rebuilt from this run's own drawing read
(T622_DRAWN.json, R-T622-1) and the owner rules; the 6 HELD rows are carried untouched and named.

Sign: statement rows are reference - engine (scorecard V10). Own components follow R-T547-1's fixed order (length at his
height, height on our face), computed with OUR face F and open side from the drawing, never with the T-312 ledger:
    open    + open x Hf                 length   - (F + open - C) x Hf      height  - F x (H - Hf)
    doors   + sum w x min(head, H)      windows  + sum band parts           line    - (line - own net)
A room's delta (his cell - engine line) is fixed by the two figures; the re-measure re-splits it and says whether each
stated row is DRAWING-CONFIRMED (|own - stated| < 0.010 m2) or DIFFERS.

    .work/venv/bin/python -I research/agents_t622/t622_alsenan.py            (writes out/WALL_TILE_REMEASURE_T622.json)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t622_rules as R  # noqa: E402

D = Decimal
Z = D(0)
DRAWN = HERE / "T622_DRAWN.json"
SCORECARD = ROOT / "research" / "agents_t613" / "out" / "SCORECARD_T613.json"
OUT = HERE / "out" / "WALL_TILE_REMEASURE_T622.json"
SECTION = "T-547/wall-tile"
HF = D("3")                                  # his flat height (ceramic sheet column F), T-547
GF_H, UP_H = D("3.65"), D("3.35")             # owner formula G1 / Q-48 A (ASSUMED - OWNER-APPROVED)
H_SRC = {GF_H: "Q-48 A tile top; owner formula 4.50 - 0.85 = 3.65 (G1)",
         UP_H: "Q-48 A tile top; owner formula 4.20 - 0.85 = 3.35 (G1)"}
DOOR = ("0", "2.20", "Q-55 C door head 2.20 (ASSUMED - OWNER-APPROVED); width drawn")
W60 = ("1.70", "2.50", "T-201 DRAWING-CONFIRMED (elevation, drawn geometry): sill 1.70 / head 2.50 above the floor")
W18 = ("0.84", "3.00", "printed on the NW elevation chain, DIMENSIONs 2EEC / 2EFA (84 / 216; drawn 0.83927 / 2.16073)")
WPAN = ("1.00", "2.50", "T-201 DRAWING-CONFIRMED (section A-A): sill 1.00 / head 2.50 above +1.00")

# room -> (statement room name, candidate line id, line value, his length C, H); his cell = C x 3 (ceramic sheet)
ROOMS = {
    "GF-12": ("GF-12 core W.C. wedge 289 x 167", "L-c34694477f67800ae2e3", "25.3011", "7.4", GF_H),
    "GF-13": ("GF-13 core W.C. wedge 245 x 167", "L-a3cb2c8a9b6080769ebc", "22.6165", "6.7", GF_H),
    "GF-14": ("GF-14 wash lobby, 2 basins", "L-fa408571a8adcfaf1a1f", "26.6544", "9.5", GF_H),
    "GF-16": ("GF-16 master bath", "L-ca4e74c59364f665b102", "25.5912", "7.6", GF_H),
    "1F-02": ("1F-02 west bath upper 245 x 205", "L-a34d09209fb5aad3eb63", "27.9101", "9", UP_H),
    "1F-03": ("1F-03 west bath lower 245 x 205", "L-88ed2535c1975adb702e", "27.9100", "8.9", UP_H),
    "1F-07": ("1F-07 laundry", "L-b2077eee5a71a975bd74", "52.5290", "16.85", UP_H),
    "1F-08": ("1F-08 W.C. 147 x 180", "L-1090bb5c8226afec2235", "19.6691", "6.48", UP_H),
    "1F-09": ("1F-09 bath by the laundry", "L-086e72207311265f81ab", "23.2201", "7.6", UP_H),
    "1F-12": ("1F-12 east bath 210 x 225", "L-82cd58d4a16fb94ddfc6", "26.3051", "8.7", UP_H),
    "2F-02": ("2F-02 roof-floor W.C. 300 x 185", "L-065bafe1b98e3a43881c", "30.2550", "9.75", UP_H),
}
PANTRY = ("GF-07", "GF-07 open pantry (wet, Q-37 A)", "L-f5c5a1a9c9ee2b644cb5", "32.3422", GF_H)
HEIGHTS = {"W18": W18, "W09": WPAN, "W10": WPAN}
HELD_WAITS = {
    "GF-02": "annex tile top: +4.30 is a roof mark (G2, Q-54 B HOLD, D-39); arch A-GF-01 head not printed",
    "GF-03": "annex tile top: +4.30 roof mark (G2, Q-54 B HOLD, D-39)",
    "GF-05": "annex tile top: +4.30 roof mark (G2, Q-54 B HOLD, D-39)",
    "GF-06": "annex tile top: +4.30 roof mark (G2, Q-54 B HOLD, D-39)",
    "GF-10": "room floor level +0.30 or +1.00 not drawn (T-088)",
    "GF-11": "room floor level +0.30 or +1.00 not drawn (T-088); doorway P-GF-01 head not printed",
}
SUFFIX = {"open": "open side, no wall, no tile", "length": "length: tiled face vs his lm",
          "height": "height: owner tile top vs his flat height", "doors": "doors / arches deducted (he deducts none)",
          "windows": "windows inside the band (he deducts none)", "rounding": "line rounding (per-face 4 dp)"}


def q(x, n=6):
    return D(x).quantize(D(1).scaleb(-n))


def _openings(room):
    out = []
    for o in room["openings"]:
        if o["kind"] == "door":
            sill, head, src = DOOR
        else:
            sill, head, src = HEIGHTS.get(o["id"], W60)
        out.append({"id": o["id"], "kind": o["kind"], "w": o["width"], "sill": sill, "head": head,
                    "handles": [o["edge"]] + o["jambs"], "height_source": src})
    return out


def own_room(rid, room, H):
    F = R.tiled_length(room["wall_lm"], [dict(x, role="OPEN") for x in room["open"]]) if room["open"] and \
        rid != "GF-07" else R.d(room["wall_lm"])
    opn = sum((R.d(x["lm"]) for x in room["open"]), Z)
    ops = _openings(room)
    net = R.room_net(faces=[{"id": f"{rid}.faces", "lm": F}], H=H, openings=ops)
    return F, opn, ops, net


def build(drawn=None, scorecard=None):
    drawn = drawn or json.loads(DRAWN.read_text(encoding="utf-8"))
    sc = scorecard or json.loads(SCORECARD.read_text(encoding="utf-8"))
    sec = next(x for x in sc["reference_lines"] if x["section_id"] == SECTION)
    rows = sec["rows"]
    stated = {r["name"]: r for r in rows}
    out_rooms, out_rows, used = [], [], set()
    split = {}

    def add(cause, v):
        split[cause] = split.get(cause, Z) + v

    for rid, (name, lid, line, C, H) in ROOMS.items():
        room = drawn["rooms"][rid]
        F, opn, ops, net = own_room(rid, room, H)
        line_d, C = D(line), D(C)
        comps = {}
        if opn:
            comps["open"] = (opn * HF, "ENGINE_RIGHT")
        ln = -(F + opn - C) * HF
        comps["length"] = (ln, "TOLERANCE" if abs(ln) < R.ROW_TOL else "ENGINE_RIGHT")
        comps["height"] = (-F * (H - HF), "RULE_DIFFERENCE")
        if net["doors"]:
            comps["doors"] = (net["doors"], "ENGINE_RIGHT")
        if net["windows"]:
            comps["windows"] = (net["windows"], "ENGINE_RIGHT")
        rnd = -(line_d - net["net"])
        comps["rounding"] = (rnd, "TOLERANCE" if abs(rnd) < R.ROW_TOL else "ENGINE_WRONG")
        delta = C * HF - line_d
        assert sum((v for v, _ in comps.values()), Z) == delta, rid
        for k, (v, cls) in comps.items():
            if v == 0:
                continue
            add(cls, v)
            sname = f"{name}: {SUFFIX[k]}"
            st = stated.get(sname)
            if st is None:
                if abs(v) >= R.ROW_TOL:
                    raise R.RuleError(f"{rid}: own component {k} {v} has no stated row and is not noise")
                out_rows.append({"row": None, "name": sname, "stated": None, "own": str(q(v)), "class": cls,
                                 "evidence": "OWN ONLY (CAD noise < 0.010, no stated row)", "diff": str(q(v))})
                continue
            used.add(sname)
            ev, diff = R.evidence(v, st["delta"])
            out_rows.append({"row": rows.index(st), "name": sname, "stated": st["delta"], "stated_class": st["class"],
                             "own": str(q(v)), "class": cls, "evidence": ev, "diff": str(q(diff))})
        out_rooms.append({"room": rid, "statement_room": name, "line_id": lid, "line": line,
                          "his_cell": str(C * HF), "chain": room["chain"], "chain_source": room["chain_source"],
                          "face_lm": str(F), "open": room["open"], "H": str(H), "H_source": H_SRC[H],
                          "openings": ops, "own_gross": str(q(F * H)), "own_net": str(q(net["net"])),
                          "line_minus_own": str(q(line_d - net["net"]))})
    # pantry: a scope row (engine only); physical value rebuilt, the line's shortfall named
    rid, name, lid, line, H = PANTRY
    room = drawn["rooms"][rid]
    F, opn, ops, net = own_room(rid, room, H)
    line_d = D(line)
    sname = f"{name}: room in the engine only"
    st = stated[sname]
    used.add(sname)
    phys = -net["net"]
    short = net["net"] - line_d
    add("RULE_DIFFERENCE", phys)
    add("ENGINE_WRONG" if abs(short) >= R.ROW_TOL else "TOLERANCE", short)
    ev, diff = R.evidence(phys, st["delta"])
    out_rows.append({"row": rows.index(st), "name": sname, "stated": st["delta"], "stated_class": st["class"],
                     "own": str(q(phys)), "class": "RULE_DIFFERENCE", "evidence": ev, "diff": str(q(diff)),
                     "line_shortfall": str(q(short)),
                     "note": "Q-37 A pantry wet + UP-PANTRY-003 host walls full height; open edge B3 4.50 tiles nothing "
                             "(UP-PANTRY-002); the line carries the T-312 face 10.491, the drawn faces are 10.500"})
    out_rooms.append({"room": rid, "statement_room": name, "line_id": lid, "line": line, "his_cell": None,
                      "chain": room["chain"], "chain_source": room["chain_source"], "face_lm": str(F),
                      "open": room["open"], "H": str(H), "H_source": H_SRC[H], "openings": ops,
                      "own_gross": str(q(F * H)), "own_net": str(q(net["net"])),
                      "line_minus_own": str(q(line_d - net["net"])), "box": drawn["dims"]["GF-07.box"]})
    unknown = [r for r in rows if r["status"] == "UNKNOWN"]
    missing = [r["name"] for r in unknown if r["name"] not in used]
    if missing:
        raise R.RuleError(f"stated rows not rebuilt: {missing}")
    stated_sum = sum((D(r["delta"]) for r in unknown), Z)
    own_sum = sum(split.values(), Z)
    if own_sum != stated_sum:
        raise R.RuleError(f"own split {own_sum} != stated UNKNOWN sum {stated_sum}")
    stated_split = {}
    for r in unknown:
        stated_split[r["class"]] = stated_split.get(r["class"], Z) + D(r["delta"])
    held = [{"row": rows.index(r), "name": r["name"], "delta": r["delta"], "status": "HELD (untouched)",
             "waits_on": HELD_WAITS[r["name"][:5]]} for r in rows if r["status"] == "HELD"]
    conf = [r for r in out_rows if r["row"] is not None]
    n_conf = sum(1 for r in conf if r["evidence"] == "DRAWING-CONFIRMED")
    return {
        "schema": "URBAN_T622_WALL_TILE_REMEASURE_V1", "rule": R.RULE_ID, "governing": R.GOVERNING,
        "section": SECTION, "statement": sc["statement"]["path"], "statement_schema": sc["statement"]["schema"],
        "drawing": drawn["source"], "unknown_rows": len(unknown), "rows_rebuilt": len(conf),
        "drawing_confirmed": n_conf, "differs": len(conf) - n_conf,
        "unknown_signed_stated": str(stated_sum),
        "stated_split_by_class": {k: str(v) for k, v in sorted(stated_split.items())},
        "own_split_by_cause": {k: str(q(v)) for k, v in sorted(split.items())},
        "rows": out_rows, "rooms": out_rooms, "held_rows": held,
        "reveal_not_in_line": {"GF-14 wall end BC": "0.15 m jamb face at the open side to the stair hall; a reveal, "
                                                    "measured separately (Q-73 answer), not in the face chain"},
        "sanitary_sheet": "Drive 'Alsenan chalet project' / sanitary-7757.pdf, 3 pages (GF / 1F / 2F drainage plans): "
                          "fixtures and floor drains only; no tile height and no fixed unit excluding tile printed",
    }


def main():
    res = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("written", OUT.relative_to(ROOT), "| rows", res["rows_rebuilt"], "/", res["unknown_rows"],
          "| confirmed", res["drawing_confirmed"], "| differs", res["differs"])
    print("stated", res["stated_split_by_class"], "sum", res["unknown_signed_stated"])
    print("own   ", res["own_split_by_cause"])
    for r in res["rows"]:
        if r["evidence"] != "DRAWING-CONFIRMED":
            print(" ", r["row"], r["evidence"], r["stated"], "->", r["own"], r["diff"], r["name"])
    for r in res["rooms"]:
        print(" ", r["room"], "F", r["face_lm"], "net", r["own_net"], "line", r["line"], "line-own", r["line_minus_own"])


if __name__ == "__main__":
    main()
