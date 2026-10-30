"""T-351 development-villa run: kitchen / laundry / pantry tile zones (B4-02) face by face.

Usage (repository root, Python 3.11):
  python3 -I research/agents_t351/t351_alsenan.py --write      write the ledgers below from the committed inputs
  python3 -I research/agents_t351/t351_alsenan.py --check      rebuild in memory, compare byte for byte
  python3 -I research/agents_t351/t351_alsenan.py --geometry <P7757.dxf>
        re-read every cited handle on the private DXF (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip,
        sha256 ab54dd55...) and assert the face lengths below to 1 mm; prints lengths and handles only.

Inputs: the face tables below (this task's own vector reading of P7757.dxf: handles and lengths only, no
coordinates, no client data) and the merged ledgers research/agents_t312/FACE_LEDGER_T312.csv (wall-tile faces and
their line ids, T-312 MERGED 8943b5ed / T-315 r2 MERGED b0041dd2) and agents_t329/BACKING_FACE_LEDGER_T329.csv.
Outputs: ZONE_LEDGER_T351.csv, CROSSCHECK_T351.csv, DRAWING_DERIVED_T351.csv, summary.json (this folder).
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t351_zone_rules as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
T312 = os.path.join(ROOT, "research", "agents_t312", "FACE_LEDGER_T312.csv")
T329 = os.path.join(ROOT, "research", "agents_t329", "BACKING_FACE_LEDGER_T329.csv")

OA = "ASSUMED — OWNER-APPROVED"

# Openings: merged sizes (T-312 OPENINGS_T312.csv <- T-201 heads, T-237 census widths, Q-55 C door head 2.20).
OP = {
    "W08": R.Opening("W08", 1.501, 1.0, 2.5),
    "D-GF-05": R.Opening("D-GF-05", 1.0, 0.0, 2.2),
    "W21": R.Opening("W21", 0.6, 1.7, 2.5),
    "D-1F-05": R.Opening("D-1F-05", 0.9, 0.0, 2.2),
    "D-1F-06": R.Opening("D-1F-06", 0.8, 0.0, 2.2),
    "D-GF-06": R.Opening("D-GF-06", 1.0, 0.0, 2.2),
    "W10": R.Opening("W10", 1.0, 1.0, 2.5),
    "W09": R.Opening("W09", 1.5, 1.0, 2.5),
}

# Own vector reading of P7757.dxf (layer 1 walls, W windows, S-COL.BON columns, 5 counters / open edges).
# (face id, handles, length m, openings, host of an installation, open edge, note)
ROOMS = {
    "GF-06": dict(code="KITCHEN", label="AT31 'KITCHEN' (block kit, handle 276)", closed=True,
                  engine_room="GF-RA3AD49", line="L-c330b8dc47261d5ada7e", backing="L-595181aa140e7efb2ac7",
                  band=R.Band(0.0, None, "Q-48 A / UP-FIN-WALL-001 (annex storey)", "HELD",
                              "annex owner height not established (G2; Q-54 B HOLD, D-39): owner 3.15 information only"),
                  faces=[
                      ("K-N", "11B + W08 frame + 11A", 2.650, ["W08"], True, False, "north wall to the column 2FB1 face; counter 11C (north leg) along it; W08 above the counter"),
                      ("K-C1", "2FB1", 0.450, [], True, False, "column 2FB1 faces proud 0.05 (0.40 + 0.05), at the counter end"),
                      ("K-E1", "A4", 2.300, [], False, False, "east wall between the two columns"),
                      ("K-C2", "2FB7", 0.600, [], False, False, "column 2FB7 faces proud 0.05 (0.05 + 0.50 + 0.05)"),
                      ("K-E2", "A4 + D120 + A5", 1.300, ["D-GF-05"], False, False, "east wall with the door to the passage (jamb to jamb 1.000)"),
                      ("K-S1", "111", 1.050, [], False, False, "south wall of the lower bay"),
                      ("K-W2", "135", 1.500, [], False, False, "wall to the W.C. (lower bay)"),
                      ("K-S2", "14F", 1.650, [], False, False, "south wall of the upper bay (W.C. side); the west counter leg ends on it"),
                      ("K-W", "136", 3.000, [], True, False, "west wall; counter 137 (west leg) along it"),
                  ]),
    "1F-07": dict(code="LAUNDRY", label="AT226 'LAUNDRY' (block laun, handle BDD)", closed=True,
                  engine_room="1F-R26FA0D", line="L-b2077eee5a71a975bd74", backing="L-2948639faa08fa1cff81",
                  band=R.Band(0.0, 3.35, "Q-48 A / UP-HGT-001 1.8.0 (1F 3.35)", OA),
                  faces=[
                      ("L-S1", "ACF + D315 + AD2", 1.620, ["D-1F-06"], None, False, "south of the upper bay, door to the W.C. 0.80"),
                      ("L-E", "B0F", 3.050, [], None, False, "east wall of the lower bay"),
                      ("L-S2", "door d220 bay", 1.420, ["D-1F-05"], None, False, "south wall with the door 0.90"),
                      ("L-P", "pier at the lower bay", 0.850, [], None, False, "pier faces proud (0.80 + 0.05)"),
                      ("L-W2", "B05 (lower)", 1.200, [], None, False, "west face of the lower bay"),
                      ("L-S3", "B14", 2.000, [], None, False, "south face of the upper bay (lift side)"),
                      ("L-W", "B12", 3.000, [], None, False, "west wall"),
                      ("L-N", "ADB + W21 + ADC", 1.850, ["W21"], None, False, "north wall with W21 0.60"),
                      ("L-E1", "B07", 1.950, [], None, False, "wall to the W.C."),
                  ]),
    "GF-07": dict(code="PANTRY", label="AT14 'PANTRY' (block PAN, handle 178)", closed=False,
                  engine_room="GF-RC06FED", line="L-f5c5a1a9c9ee2b644cb5", backing="L-721a0f1441436193978c",
                  band=R.Band(0.0, 3.65, "Q-48 A (GF main 3.65); Q-37 A; UP-PANTRY-004", OA),
                  faces=[
                      ("P-W", "AE + W10 + AF + W09 + B0", 4.450, ["W10", "W09"], True, False, "west wall face from the column 2FAE underside; counter west leg back 3.066"),
                      ("P-C", "2FAE", 0.900, [], True, False, "column 2FAE underside face proud 0.05; counter north leg back"),
                      ("P-CR", "2FAE return", 0.050, [], True, False, "column return (R-T312-1: tiled, every wall hosts)"),
                      ("P-N", "158 + D120 + 159", 2.100, ["D-GF-06"], True, False, "north wall 0.759111 + door 1.000 + 0.340889; counter north leg back 0.50"),
                      ("P-S", "A6", 3.000, [], True, False, "south wall; counter south leg back 1.400"),
                      ("P-OPEN", "AD + B3 (layer 5)", 4.500, [], False, True, "open edge to the dining (peninsula counter, no wall)"),
                  ]),
}

# Drawing-derived reading beside the owner method: a splashback band behind the drawn counters only.
SPLASH = {
    "GF-06": (5.150, "counter 11C / 137 backs: north 2.650 (W08 sill 1.00 above the counter) + west 2.500 beyond the corner"),
    "1F-07": (0.0, "no counter, sink or appliance drawn on P7757.dxf (no layer 5 outline, no block) in the room"),
    "GF-07": (5.916, "T-312 counter backs: west 3.066 + north 1.450 (column 0.90 + wall 0.50 + 0.05) + south 1.400; the open-edge leg backs nothing"),
}

GEOM = {  # handle -> drawn length (m), for --geometry
    "11A": 0.600, "11B": 0.600, "136": 3.000, "14F": 1.650, "135": 1.500, "111": 1.050, "A4": 3.400, "A5": 0.100,
    "AE": 0.850, "AF": 1.050, "B0": 0.100, "158": 1.659111, "159": 0.340889, "A6": 3.000, "AD": 0.500, "B3": 4.000,
    "B0F": 3.050, "B12": 3.000, "B14": 2.000, "B07": 1.950,
}


def _fmt(v, nd=4):
    return "" if v is None else f"{v:.{nd}f}"


def build():
    t312 = list(csv.DictReader(open(T312, encoding="utf-8")))
    t329 = list(csv.DictReader(open(T329, encoding="utf-8")))
    wall_tile_faces, t312_room = {}, {}
    for r in t312:
        if r["room"] in ROOMS:
            agg = t312_room.setdefault(r["room"], {"tiled": 0.0, "open": 0.0, "net": 0.0, "held": False,
                                                   "line": set(), "pieces": 0})
            ln = float(r["length_m"])
            if r["scope"] == "OPEN_EDGE":
                agg["open"] += ln
                continue
            agg["tiled"] += ln
            agg["pieces"] += 1
            agg["line"].add(r["line_id"])
            if r["owner_net_m2"]:
                agg["net"] += float(r["owner_net_m2"])
            else:
                agg["held"] = True
    backing = {}
    for r in t329:
        if r["room"] in ROOMS:
            backing[r["room"]] = backing.get(r["room"], 0) + 1
    zones, cross, splash = [], [], []
    for room, spec in ROOMS.items():
        faces = [R.Face(fid, ln, tuple(OP[o] for o in ops), open_edge=oe, host=host)
                 for fid, _h, ln, ops, host, oe, _n in spec["faces"]]
        z = R.decide_room(room, spec["code"], spec["closed"], faces, owner_band=spec["band"],
                          wall_tile_line=spec["line"])
        # the T-312 ledger binds the room's tiled faces to one line: every own face maps to it
        for zz in z:
            if zz.carrier.startswith("BOUND_TO_WALL_TILE"):
                wall_tile_faces[(room, zz.face_id)] = spec["line"]
        R.check_results(z, wall_tile_faces)
        meta = {fid: (h, n) for fid, h, _l, _o, _ho, _oe, n in spec["faces"]}
        zones += [(spec, zz, meta[zz.face_id]) for zz in z]
        own_tiled = round(sum(zz.length_m for zz in z if zz.zone not in ("NONE_OPEN_EDGE", "NOT_HOST")), 4)
        own_open = round(sum(zz.length_m for zz in z if zz.zone == "NONE_OPEN_EDGE"), 4)
        own_net = R.room_total(z)
        a = t312_room[room]
        lines = sorted(a["line"])
        merged_net = None if a["held"] else round(a["net"], 4)
        cross.append({
            "room": room, "code": spec["code"], "engine_room": spec["engine_room"],
            "own_tiled_m": _fmt(own_tiled), "t312_tiled_m": _fmt(a["tiled"]), "d_tiled_m": _fmt(own_tiled - a["tiled"]),
            "own_open_m": _fmt(own_open), "t312_open_m": _fmt(a["open"]),
            "own_net_m2": _fmt(own_net), "line_net_m2": _fmt(merged_net),
            "d_net_m2": _fmt(None if own_net is None or merged_net is None else own_net - merged_net),
            "wall_tile_line": spec["line"], "t312_line": "|".join(lines),
            "line_agrees": ("YES" if lines == [spec["line"]] else
                            "ADDED BY T-315 r2 (T-312 NO_LINE; MERGED b0041dd2)" if lines == ["NO_LINE"] else "NO"),
            "b4_02_new_faces": "0", "b4_02_overlap_m2": "0.0000",
            "backing_line": spec["backing"], "backing_faces_t329": str(backing.get(room, 0)),
            "status": spec["band"].status,
            "held_item": spec["band"].held_item,
        })
        ln, why = SPLASH[room]
        splash.append({"room": room, "code": spec["code"], "host_back_m": _fmt(ln, 3), "host_evidence": why,
                       "printed_band": "none (T-091 MERGED: no sheet prints a wall-tile height or note; no interior "
                                       "elevation in the set)",
                       "band_m2": "", "status": "HELD", "held_item": "TILE_BAND_NOT_PRINTED (never a default 0.60)",
                       "use": "information beside the owner method; never fills a blank, never a quantity"})
    return zones, cross, splash


def render():
    zones, cross, splash = build()
    out = {}
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["room", "code", "face_id", "handles", "length_m", "zone", "basis", "band_bottom_m", "band_top_m",
                "openings", "deductions_m2", "net_m2", "status", "held_item", "carrier", "paint_under_zone",
                "plaster_under_zone", "note"])
    for spec, z, (h, n) in zones:
        w.writerow([z.room, z.code, z.face_id, h, _fmt(z.length_m), z.zone, z.basis, _fmt(z.band_bottom_m, 2),
                    _fmt(z.band_top_m, 2), " ".join(o for o, _ in z.deductions) or "",
                    " ".join(f"{o}={d:.4f}" for o, d in z.deductions), _fmt(z.net_m2), z.status, z.held_item,
                    z.carrier, z.paint_under_zone,
                    (z.plaster_under_zone + f" ({spec['backing']})") if z.plaster_under_zone else "", n])
    out["ZONE_LEDGER_T351.csv"] = f.getvalue()
    for name, rows in (("CROSSCHECK_T351.csv", cross), ("DRAWING_DERIVED_T351.csv", splash)):
        f = io.StringIO()
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        out[name] = f.getvalue()
    summ = {
        "task": "T-351", "family": "B4-02 kitchen / laundry / pantry tiled zones",
        "rooms": len(cross), "faces": sum(1 for _ in zones),
        "b4_02_new_faces": 0, "b4_02_overlap_m2": 0.0,
        "bound_to_wall_tile": {c["room"]: c["wall_tile_line"] for c in cross},
        "owner_method_net_m2": {c["room"]: (c["own_net_m2"] or "HELD") for c in cross},
        "line_net_m2": {c["room"]: (c["line_net_m2"] or "HELD") for c in cross},
        "drawing_derived": "HELD on every room (no printed band); host backs " +
                           ", ".join(f"{s['room']} {s['host_back_m']} m" for s in splash),
    }
    out["summary.json"] = json.dumps(summ, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return out


def geometry(path):
    import ezdxf
    doc = ezdxf.readfile(path)
    hs = {e.dxf.handle: e for e in doc.modelspace() if e.dxftype() == "LINE"}
    bad = 0
    for h, want in GEOM.items():
        e = hs[h]
        got = e.dxf.start.distance(e.dxf.end) / 1000.0
        ok = abs(got - want) <= 0.001
        bad += not ok
        print(f"{h} {got:.6f} m {'OK' if ok else 'DIFFERS from ' + str(want)}")
    for room, spec in ROOMS.items():
        print(room, "face sum", round(sum(x[2] for x in spec["faces"] if not x[5]), 4), "open",
              round(sum(x[2] for x in spec["faces"] if x[5]), 4))
    return bad


def main(argv):
    if len(argv) >= 2 and argv[0] == "--geometry":
        return 1 if geometry(argv[1]) else 0
    out = render()
    if argv == ["--write"]:
        for k, v in out.items():
            open(os.path.join(HERE, k), "w", encoding="utf-8").write(v)
        print("written", ", ".join(sorted(out)))
        return 0
    if argv == ["--check"]:
        bad = [k for k, v in out.items()
               if not os.path.exists(os.path.join(HERE, k)) or open(os.path.join(HERE, k), encoding="utf-8").read() != v]
        print("differs:", bad or "none")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
