"""T-501 development villa: stair skirting pieces, the 1F shaft binding and the stream F line proposal.

    python3 -I research/agents_t501/t501_alsenan.py --dxf <P7757.dxf> --write   # re-reads every station by handle
    python3 -I research/agents_t501/t501_alsenan.py --check                     # no private input: rebuild + compare

Drawing: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55..), read BY HANDLE.
Committed here: handles, layers and face stations (metres from the shaft's north-west inner corner); no coordinate,
image, note text or client data. ST-01 shaft faces share one y on the GF / 1F / 2F plans (T-493): E = the lift wall
(GF 21B / 21C, 1F B16, 2F 129A), W = the shaft west wall (GF 297 / 298, 1F AF0 / AF1, 2F 12B8 / 12B7), N = the north wall
(GF 2AB / 26F, 1F ADE / ADD, 2F 127E / 127D); s on E / W runs north -> south, s on N runs west -> east.
Flight data (risers, riser, goings) from the committed T-410 sides (T-184 counts, Q-46 A); ST-02 / ST-03 rows carried
from T-410 unchanged (not on these faces).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t501_stair_skirting_home as K  # noqa: E402

T410 = ROOT / "research" / "agents_t410"
E, W, N = "ST-01 E", "ST-01 W", "ST-01 N"

# ------------------------------------------------------------------ stations read by handle (own read, this run)
# (handle, layer, face, kind 'span' (s0, s1) or 'at' (s), expected)
STATIONS = [
    ("21B", "1", E, "span", (0.000, 2.100)), ("33C", "2", E, "span", (2.100, 3.000)), ("21C", "1", E, "span", (3.000, 5.000)),
    ("B16", "1", E, "span", (0.000, 5.200)), ("129A", "1", E, "span", (0.000, 5.200)),
    ("481", "5", E, "at", 1.150), ("490", "5", E, "at", 2.050),            # GF: D1 nosings (MS1-LD south edge = 481)
    ("A92", "5", E, "at", 1.150), ("ABE", "5", E, "at", 4.150), ("ABD", "2", E, "at", 4.200),   # 1F: MS1-U first / last
    ("135B", "5", E, "at", 1.150), ("1386", "5", E, "at", 4.150), ("1385", "2", E, "at", 4.200),  # 2F: MS2-U first / last
    ("138B", "5", E, "at", 4.500),                                         # 2F slab-opening edge (T-418 foot strip end)
    ("297", "1", W, "span", (0.000, 1.050)), ("298", "1", W, "span", (2.250, 5.000)),
    ("AF0", "1", W, "span", (0.000, 1.050)), ("C5C", "W", W, "span", (1.050, 2.250)), ("AF1", "1", W, "span", (2.250, 4.625)),
    ("12B8", "1", W, "span", (0.000, 1.050)), ("12D1", "W", W, "span", (1.050, 2.250)),
    ("A97", "5", W, "at", 1.200), ("AC0", "5", W, "at", 4.500), ("AC2", "2", W, "at", 4.450),   # 1F: MS2-L last / first
    ("DC", "5", W, "at", 3.900), ("485", "2", W, "at", 1.200),             # GF: MS1-L first nosing / first winder front
    ("ADE", "1", N, "span", (0.000, 1.400)), ("CE8", "W", N, "span", (1.400, 1.450)), ("CE2", "W", N, "span", (1.450, 2.350)),
    ("CDF", "W", N, "span", (2.350, 2.400)), ("ADD", "1", N, "span", (2.400, 2.500)),
    ("127E", "1", N, "span", (0.000, 1.400)), ("127D", "1", N, "span", (2.400, 2.500)),
    ("BE4", "5", N, "at", 1.250), ("BE5", "2", N, "at", 1.300), ("12B4", "5", N, "at", 1.250), ("12B5", "2", N, "at", 1.300),
]
# plan origins (x of the west inner face, y of the north inner face), one per plan; checked against the handles
ORIGINS = {"GF": (-145039.8555, -791993.5401), "1F": (-189892.5106, -791993.5401), "2F": (-234745.1656, -791993.5401)}
PLAN_OF = {**{h: "GF" for h in ("21B", "33C", "21C", "481", "490", "297", "298", "DC", "485")},
           **{h: "2F" for h in ("129A", "135B", "1386", "1385", "138B", "12B8", "12D1", "127E", "127D", "12B4", "12B5")}}


def verify_dxf(path) -> list:
    import ezdxf
    db = ezdxf.readfile(path).entitydb
    out = []
    for h, layer, face, kind, exp in STATIONS:
        e = db.get(h)
        assert e is not None and e.dxftype() == "LINE" and e.dxf.layer == layer, (h, layer)
        x0, y0 = ORIGINS[PLAN_OF.get(h, "1F")]
        a, b = e.dxf.start, e.dxf.end
        if face == N:
            got = sorted(((a.x - x0) / 1000.0, (b.x - x0) / 1000.0)) if kind == "span" else None
            if kind == "at":
                assert abs(a.x - b.x) < 1, h
                got = (a.x - x0) / 1000.0
            else:
                assert abs(a.y - y0) < 1 and abs(b.y - y0) < 1, h
        else:
            if kind == "span":
                assert abs(a.x - b.x) < 1, h
                got = sorted(((y0 - a.y) / 1000.0, (y0 - b.y) / 1000.0))
            else:
                assert abs(a.y - b.y) < 1, h
                got = (y0 - a.y) / 1000.0
        if kind == "span":
            assert abs(got[0] - exp[0]) < 0.001 and abs(got[1] - exp[1]) < 0.001, (h, got, exp)
        else:
            assert abs(got - exp) < 0.001, (h, got, exp)
        out.append(h)
    return out


# ------------------------------------------------------------------ pieces
def flights():
    return json.load(open(T410 / "ALSENAN_SIDES_T410.json", encoding="utf-8"))["flights"]


def t410_rows():
    with open(T410 / "SIDE_TABLE_T410.csv", newline="", encoding="utf-8") as f:
        return {r["sid"]: r for r in csv.DictReader(f)}


def pieces():
    fl = flights()
    P = []

    def flight(pid, el, face, cls, s_foot, s_head, a, b, lv_foot, lv_head, risers, returns=0.0, cause="", ev=""):
        """a .. b are face stations inside the flight s_foot -> s_head (either direction)."""
        f = fl[el]
        run, rise = f["goings"] * f["going"], f["risers"] * f["riser"]
        def lv(s):
            return lv_foot + (lv_head - lv_foot) * abs(s - s_foot) / abs(s_head - s_foot)
        s0, s1 = min(a, b), max(a, b)
        P.append(K.Piece(pid, el, face, K.FLIGHT, cls, s0, s1, lv(s0), lv(s1), risers, f["riser"], run, rise,
                         returns, cause, ev))

    def level(pid, el, face, cls, s0, s1, lvl, kind=K.LANDING, returns=0.0, cause="", ev=""):
        P.append(K.Piece(pid, el, face, kind, cls, s0, s1, lvl, lvl, 0, 0.0, 0.0, 0.0, returns, cause, ev))

    # MS1-L (GF west, +1.00 at DC s 3.900 rising north to the first winder front 485 s 1.200): T-410 stretches
    flight("MS1-L.W1", "MS1-L", W, K.WALL, 3.900, 1.200, 3.900, 3.500, 1.00, 2.666667, 2, ev="GF 298")
    flight("MS1-L.W1C", "MS1-L", W, K.WALL, 3.900, 1.200, 3.500, 3.000, 1.00, 2.666667, 1, 0.100, ev="GF 298, column 2FBD 0.050 proud")
    flight("MS1-L.W1B", "MS1-L", W, K.WALL, 3.900, 1.200, 3.000, 2.250, 1.00, 2.666667, 3, ev="GF 298")
    flight("MS1-L.W2", "MS1-L", W, K.HELD, 3.900, 1.200, 2.250, 1.200, 1.00, 2.666667, 4,
           cause="GF window 352-354 in the face beside treads +2.00 .. +2.67; sill / head not printed", ev="GF 352-354")
    # MS1-T winder corner (+2.667 -> +3.50): HELD (S-9)
    level_cause = "winder corner: 5 risers on A-A vs 4 wedges on the plans (T-184); winders never generated (S-9)"
    P.append(K.Piece("MS1-T.W", "MS1-T", W, K.FLIGHT, K.HELD, 0.000, 1.200, 3.50, 2.666667, 0, 0, 0, 0, 0, level_cause, "GF 49E / 4A0 / 4A2"))
    P.append(K.Piece("MS1-T.N", "MS1-T", N, K.FLIGHT, K.HELD, 0.000, 1.150, 2.666667, 3.50, 0, 0, 0, 0, 0, level_cause, "GF 26E"))
    # MS1-LD (+3.50): E 0 .. 1.150 (21B / B16), N 1.350 .. 2.500 HELD (opening 3FD / 3FE, 1F window above)
    level("MS1-LD.E", "MS1-LD", E, K.WALL, 0.000, 1.150, 3.50, ev="GF 21B, 1F B16; south edge 481 / A92 s 1.150")
    level("MS1-LD.N", "MS1-LD", N, K.HELD, 1.350, 2.500, 3.50,
          cause="0.103 wall + 0.900 opening (3FD / 3FE) + 0.147 wall; head / sill vs +3.50 not printed", ev="GF 2AB / 3FD / 26F")
    # MS1-U (+3.50 at A92 s 1.150 -> +5.50; T-410 run 3.300 = 11 goings to s 4.450)
    flight("MS1-U.E1", "MS1-U", E, K.WALL, 1.150, 4.450, 1.150, 2.100, 3.50, 5.50, 4, ev="GF 21B; 1F B16")
    flight("MS1-U.E2", "MS1-U", E, K.HELD, 1.150, 4.450, 2.100, 3.000, 3.50, 5.50, 3,
           cause="GF hidden opening 33C / 33D (0.90) in the face; height vs the flight not printed", ev="GF 33C / 33D")
    flight("MS1-U.E3a", "MS1-U", E, K.WALL, 1.150, 4.450, 3.000, 4.150, 3.50, 5.50, 4, ev="GF 21C; 1F B16; to ABE s 4.150")
    P.append(K.Piece("MS1-U.E3b", "MS1-U", E, K.FLIGHT, K.CONFLICT, 4.150, 4.450,
                     3.50 + 2.0 * 3.0 / 3.3, 5.50, 1, fl["MS1-U"]["riser"], 3.3, 12 * fl["MS1-U"]["riser"], 0.0,
                     "arch plans end MS1-U at its 11th riser line (ABE nosing s 4.150 / ABD face 4.200: 1F floor beyond); "
                     "section A-A counts 12 risers and ST p.4 draws the 12th edge 459 at s 3.30 of the flight (s 4.450); "
                     "Q-46 RFI / B20 head clash (T-412)", "1F ABE / ABD; ST p.4 459 (T-412)",
                     beside={"carried_by": ["1F-ROOM.E2"]}))
    # MS2-L (1F west: +5.50 at AC0 s 4.500 rising north to A97 s 1.200, +7.516)
    flight("MS2-L.W1", "MS2-L", W, K.WALL, 4.500, 1.200, 4.500, 3.500, 5.50, 7.516, 4, ev="1F AF1; 2F 12B7")
    flight("MS2-L.W1C", "MS2-L", W, K.WALL, 4.500, 1.200, 3.500, 3.000, 5.50, 7.516, 1, 0.100, ev="1F AF1, column 3005 0.050 proud")
    flight("MS2-L.W1B", "MS2-L", W, K.WALL, 4.500, 1.200, 3.000, 2.250, 5.50, 7.516, 3, ev="1F AF1; 2F 12B7")
    flight("MS2-L.W2", "MS2-L", W, K.HELD, 4.500, 1.200, 2.250, 1.200, 5.50, 7.516, 4,
           cause="1F window C5A-C5C (W13) and 2F window 12CF-12D1 beside treads +7.18 .. +7.52; sill / head not printed",
           ev="1F C5C, 2F 12D1")
    # MS2-LD split landing (T-493: closing riser MS2-TR at x 1.25 nosing / 1.30 riser face, BE4 / BE5, 12B4 / 12B5)
    level("MS2-LD.W", "MS2-LD", W, K.WALL, 0.000, 1.050, 7.516, ev="1F AF0, 2F 12B8 (wall on both plans)")
    level("MS2-LD.W13", "MS2-LD", W, K.HELD, 1.050, 1.200, 7.516,
          cause="W13 (1F C5C / 2F 12D1) in the face beside the landing; sill / head vs +7.516 not printed", ev="1F C5C")
    level("MS2-LD.NW", "MS2-LD", N, K.WALL, 0.000, 1.300, 7.516, ev="1F ADE, 2F 127E; to the MS2-TR riser face BE5 / 12B5")
    level("MS2-LD.NE", "MS2-LD", N, K.WALL, 1.300, 1.400, 7.684, ev="1F ADE, 2F 127E; from the MS2-TR riser face")
    level("MS2-LD.W25", "MS2-LD", N, K.HELD, 1.400, 2.400, 7.684,
          cause="W25 (1F CE8 / CE2 / CDF, 2F 1348 / 1342 / 133F stacked) in the face; sill / head vs +7.684 not printed",
          ev="1F CE2")
    level("MS2-LD.NE2", "MS2-LD", N, K.WALL, 2.400, 2.500, 7.684, ev="1F ADD, 2F 127D")
    level("MS2-LD.E", "MS2-LD", E, K.WALL, 0.000, 1.150, 7.684, ev="1F B16, 2F 129A; to 135B s 1.150 (MS2-U first nosing)")
    P.append(K.Piece("MS2-TR.N", "MS2-TR", N, K.STEP, K.HELD, 1.300, 1.300, 7.516, 7.684, 1, 0.168, 0, 0, 0,
                     "closing riser meets the north wall at x 1.30 (BE5 / 12B5, T-493); the 2F diagonal 2F1F / 2F20 is "
                     "unexplained (Q-ST-11): the step's place on the wall not established", "1F BE4 / BE5, 2F 12B4 / 12B5"))
    # MS2-U (+7.684 at 135B s 1.150 -> +9.70; T-410 run 3.300 to s 4.450)
    flight("MS2-U.E", "MS2-U", E, K.WALL, 1.150, 4.450, 1.150, 4.450, 7.684, 9.70, 12, ev="1F B16, 2F 129A, no opening")
    # D1 (GF east lane, +0.30 at 481 s 1.150 -> +1.00 at s 2.050)
    flight("D1.E", "D1", E, K.WALL, 1.150, 2.050, 1.150, 2.050, 0.30, 1.00, 4, ev="GF 21B")
    # room pieces on the same faces (one owner check, level-aware)
    level("GF-ST-LOBBY030.E", "room", E, K.WALL, 0.000, 1.150, 0.30, kind=K.ROOM, ev="T-441 / T-443 child, 21B")
    level("GF-ST-HALL.E", "room", E, K.WALL, 3.000, 5.000, 1.00, kind=K.ROOM, ev="T-441 / T-443 child, 21C")
    level("1F-ROOM.E2", "room", E, K.WALL, 4.150, 5.200, 5.50, kind=K.ROOM, ev="L-ba3599ec remainder (T-481), B16")
    level("1F-ROOM.W2", "room", W, K.WALL, 4.500, 4.625, 5.50, kind=K.ROOM, ev="L-ba3599ec remainder (T-481), AF1")
    level("2F-ST-ARRIVAL.E", "room", E, K.WALL, 4.500, 5.200, 9.70, kind=K.ROOM, ev="T-441 / T-443 child, 2F72 / 129A")
    return P


# the 1F room line L-ba3599ec faces measured at +5.50 along the shaft (T-481 SHAFT_FACES_T481.csv)
ROOM_SEGMENTS = [
    ("L-ba3599ec E 0 .. 4.150", E, 0.000, 4.150, 5.50, "certain (net 41.435360)"),
    ("L-ba3599ec W AF0", W, 0.000, 1.050, 5.50, "certain"),
    ("L-ba3599ec W13 (range L-079bc766)", W, 1.050, 2.250, 5.50, "held range"),
    ("L-ba3599ec W AF1 2.250 .. 4.500", W, 2.250, 4.500, 5.50, "certain (+ 3005 returns 0.100)"),
    ("L-ba3599ec N ADE", N, 0.000, 1.400, 5.50, "certain"),
    ("L-ba3599ec W25 (range L-079bc766)", N, 1.400, 2.400, 5.50, "held range"),
    ("L-ba3599ec N ADD", N, 2.400, 2.500, 5.50, "certain"),
]

# T-410 rows carried unchanged (other stairs, not on the ST-01 faces)
CARRIED = ["RS-S.S0", "RS-S.S1", "RS-S.S2", "RS-LD.S1", "RS-LD.S2", "RS-C.OUT", "E1.S"]


def build():
    P = pieces()
    K.check_one_owner(P)
    binding = K.retire(ROOM_SEGMENTS, P)
    stair = [p for p in P if p.kind != K.ROOM]
    lines = [K.line(p) for p in stair]
    t410 = t410_rows()
    for sid in CARRIED:
        r = t410[sid]
        landing = r["element"] == "RS-LD"
        lines.append({"pid": sid, "element": r["element"], "face": f"{r['element']} {r['side']}", "kind":
                      K.LANDING if landing else K.FLIGHT, "cls": r["class"], "s0": None, "s1": None,
                      "plan_lm": float(r["plan_lm"]), "risers": int(r["risers_in"] or 0), "returns_lm": float(r["returns_lm"]),
                      "level0": None, "level1": None,
                      "family": K.ROOM_TRADE if landing else "B7-07 | B7-08",
                      "value_lm": float(r["qty_lm"]) if r["qty_lm"] else None,
                      "status": r["status"] if r["status"] != "UNKNOWN" else "UNKNOWN",
                      "zigzag_lm": float(r["zigzag_lm"]) if r["zigzag_lm"] and not landing else None,
                      "sloped_lm": float(r["sloped_lm"]) if r["sloped_lm"] and not landing else None,
                      "cause": r["cause"], "evidence": r["evidence"] + " (carried from T-410)"})
    K.check_lines(lines)
    return P, binding, lines


def totals(lines, binding):
    def s(rows, key):
        return round(sum(r[key] for r in rows if r[key] is not None), 6)
    land_ok = [r for r in lines if r["family"] == K.ROOM_TRADE and r["status"] == K.CONFIRMED]
    form = [r for r in lines if r["status"] == K.FORM_HELD and r["kind"] == K.FLIGHT]
    held = [r for r in lines if r["status"] not in (K.CONFIRMED, K.FORM_HELD)]
    retired = [b for b in binding if b["decision"].startswith("NOT_APPLICABLE")]
    t = {
        "landing_fin_skirting_confirmed_lm": s(land_ok, "value_lm"),
        "landing_lines": {r["pid"]: r["value_lm"] for r in land_ok},
        "flight_form_held": {"lines": len(form), "zigzag_lm": s(form, "zigzag_lm"), "sloped_lm": s(form, "sloped_lm"),
                             "risers": sum(r["risers"] for r in form)},
        "held_lines": len(held),
        "held_plan_lm": round(sum(r["plan_lm"] for r in held), 6),
        "retired_from_room_line": {"certain_lm": round(sum(b["lm"] for b in retired if b["status_before"] != "held range")
                                                       + 0.100, 6),
                                   "held_range_lm": round(sum(b["lm"] for b in retired if b["status_before"] == "held range"), 6),
                                   "residual_lm": round(sum(b["residual_lm"] for b in retired), 6)},
    }
    t["fin_skirting_certain_change_lm"] = round(t["landing_fin_skirting_confirmed_lm"] - t["retired_from_room_line"]["certain_lm"], 6)
    return t


COLS = ["pid", "element", "face", "kind", "cls", "s0", "s1", "plan_lm", "risers", "returns_lm", "level0", "level1",
        "family", "status", "value_lm", "zigzag_lm", "sloped_lm", "cause", "evidence"]


def render(lines, binding, tot):
    a = io.StringIO()
    w = csv.DictWriter(a, fieldnames=COLS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in lines:
        w.writerow(r)
    b = io.StringIO()
    w2 = csv.DictWriter(b, fieldnames=list(binding[0].keys()), lineterminator="\n")
    w2.writeheader()
    for r in binding:
        w2.writerow(r)
    summ = json.dumps({"task": "T-501", "dxf_sha8": "ab54dd55", "totals": tot}, indent=1, sort_keys=True) + "\n"
    return {"LINES_T501.csv": a.getvalue(), "BINDING_T501.csv": b.getvalue(), "summary.json": summ}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.dxf:
        hs = verify_dxf(a.dxf)
        print(f"DXF stations VERIFIED by handle: {len(hs)}")
    _, binding, lines = build()
    out = render(lines, binding, totals(lines, binding))
    if a.write:
        if not a.dxf:
            ap.error("--write needs --dxf (stations are re-read from the drawing)")
        for k, v in out.items():
            (HERE / k).write_text(v, encoding="utf-8")
        print("WRITTEN")
    if a.check:
        bad = [k for k, v in out.items() if (HERE / k).read_text(encoding="utf-8") != v]
        print("REPRODUCED" if not bad else f"DIFFERS: {bad}")
        return 1 if bad else 0
    print(out["summary.json"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
