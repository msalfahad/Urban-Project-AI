"""T-634 builder (development villa; research, unwired): the 31 UNKNOWN rows of statement V11 sections
T-552/plaster-internal (15) and T-561/paint-internal (16) (scorecard V11, research/agents_t620/out/SCORECARD_T620.json,
read only) rebuilt from this run's own drawing read (T634_DRAWN.json, R-T634-1) and the owner rules; the 24 / 25 HELD
rows are carried untouched and counted.

Sign: statement rows are reference - engine. Room rows follow R-T547-1's order with OUR face F from the drawing:
    length (his L - F) x his H      height (his H - G1) x F      openings sum w x band part at G1      line residual
A room's delta (his cell - engine line) is fixed by the two figures; the re-measure re-splits it and says whether each
stated row is DRAWING-CONFIRMED (|own - stated| < 0.010 m2) or DIFFERS. Beside each released dry line: the Q-72
plaster net at the slab-soffit height (T-556 heights) on the same own faces, and the paint net at G1.

    .work/venv/bin/python -I research/agents_t634/t634_alsenan.py            (writes out/T634_PLASTER_PAINT_REMEASURE.json)
    .work/venv/bin/python -I research/agents_t634/t634_alsenan.py --check    (rebuild, compare byte-identical)
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t634_rules as R  # noqa: E402

D = Decimal
Z = D(0)
DRAWN = HERE / "T634_DRAWN.json"
SCORECARD = ROOT / "research" / "agents_t620" / "out" / "SCORECARD_T620.json"
T556 = ROOT / "research" / "agents_t556" / "out" / "T556_PLASTER_HEIGHT.json"
OUT = HERE / "out" / "T634_PLASTER_PAINT_REMEASURE.json"
SECTIONS = ("T-552/plaster-internal", "T-561/paint-internal")

DOOR = ("0", "2.20", "Q-55 C door head 2.20 (ASSUMED - OWNER-APPROVED); width drawn (gap between the face pieces)")
HEADS = {  # opening -> (sill, head, source); widths always from this run's drawing read
    "W03": ("0", "4.30", "T-175 / T-150 PRINTED NW elevation +1.00 .. +5.30 (sill 0 on the GF FFL); width = the room-"
            "side glazing face 27D (layer W) at its true length"),
    "W14": ("1.40", "3.00", "T-175 PRINTED (height 160 SE DIMENSION 2B47, T-627 own read; sill 1.40)"),
    "W24": ("1.00", "2.50", "T-627 / T-201 DRAWING-CONFIRMED NE outline +6.50 .. +8.00 over the 1F +5.50"),
    "W29": ("1.00", "2.50", "T-627 / T-201 DRAWING-CONFIRMED SW outline +10.70 .. +12.20 over the 2F +9.70"),
    "D-GF-07": ("0", "2.50", "T-175 PRINTED 2.00 x 2.50 (plan / SE elevation; designer D-53 single vs double leaf)"),
}
# his plaster / paint cells (same rows in both workbooks' internal list: T-552 / T-561 inputs) and the engine lines
ROOMS = {  # room: (his L, his H, engine line net, G1 paint height, line id, zone)
    "GF-15": ("21.05", "3.6", "56.0131", "3.65", "L-0d93f2209cd9bb827c0a", "GF_MAIN"),
    "1F-01": ("17.5", "3.4", "51.415", "3.35", "L-af9621f43bc316a871ea", "1F"),
    "1F-04": ("17.3", "3.4", "52.005", "3.35", "L-971f0bdaf68d7fd0966c", "1F"),
    "2F-03": ("18.9", "3.4", "57.775", "3.35", "L-4ce74fc37a08d4bdf0d8", "2F"),
}
ENGINE_FACE = {"GF-15": "21.537", "1F-01": "17.7", "1F-04": "17.4", "2F-03": "18.9"}  # T-552 inputs (T-128 r3)
G1_SRC = "owner G1 room formula (Q-48 A): interval - 0.60 - 0.15 - 0.10 = GF 3.65 / 1F, 2F 3.35, FINISHED_CEILING basis"
GF02 = ("6.75", "3.6")   # his row 9 (T-552 inputs WET_IN_HIS_DRY)
SHAFT_HIS = (("2.5", "5.4"), ("11.25", "3.6"))
RETURN_HIS = ("14", "0.2", "5.7")
WET_WORDS = ("W.C.", "bath", "wash", "laundry", "basin")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def q(x, n=6):
    return str(D(x).quantize(D(1).scaleb(-n)))


def own_openings(room, H):
    parts = []
    for o in room["openings"]:
        oid, kind, w = o["id"], o["kind"], o["width"]
        if kind == "arch":
            parts.append({"id": oid, "kind": kind, "width": w, "held": "arch head not printed (T-175 HELD)"})
            continue
        sill, head, src = HEADS.get(oid, DOOR) if kind != "door" else HEADS.get(oid, DOOR)
        part = R.opening_part({"id": oid, "w": w, "sill": sill, "head": head}, H)
        parts.append({"id": oid, "kind": kind, "width": w, "sill": sill, "head": head, "source": src,
                      "edge": o["edge"], "part_m2": q(part)})
    return parts


def build():
    drawn = json.loads(DRAWN.read_text(encoding="utf-8"))
    sc = json.loads(SCORECARD.read_text(encoding="utf-8"))
    t556 = json.loads(T556.read_text(encoding="utf-8"))
    h556 = {r["room"]: r for r in t556["rows"]}
    refs = {r["section_id"]: r for r in sc["reference_lines"] if r["section_id"] in SECTIONS}
    rooms_out, own = {}, {}
    for rid, (hl, hh, line, g1, lid, zone) in ROOMS.items():
        rm = drawn["rooms"][rid]
        F = D(rm["perimeter"])
        parts = own_openings(rm, g1)
        op = sum((D(p["part_m2"]) for p in parts), Z)
        sp = R.split_room(hl, hh, F, g1, op, line)
        paint = R.face_net(F, {"H": g1, "basis": R.PAINT_BASIS},
                           [{"id": p["id"], "w": p["width"], "sill": p["sill"], "head": p["head"]} for p in parts],
                           "paint")
        # Q-72 plaster beside: T-556 height (floor part DRAWING-CONFIRMED / roof DRAWN-SECTION SCENARIO), own faces
        r6 = h556[rid]
        Hp = r6["H_floor_m"] or r6["H_roof_scenario_m"]
        pl = R.face_net(F, {"H": Hp, "basis": R.PLASTER_BASIS},
                        [{"id": p["id"], "w": p["width"], "sill": p["sill"], "head": p["head"]} for p in parts],
                        "plaster")
        be_lo, be_hi = D(r6["new"]["beam_ends_lo"]), D(r6["new"]["beam_ends_hi"])
        own[rid] = sp
        rooms_out[rid] = {
            "line_id": lid, "zone": zone, "face_lm_own": q(F), "face_lm_engine": ENGINE_FACE[rid], "chain": rm["chain"],
            "chain_source": rm["chain_source"], "openings": parts,
            "paint_G1": {"H": g1, "basis": R.PAINT_BASIS, "source": G1_SRC, "gross": q(paint["gross"]),
                         "openings": q(paint["openings"]), "net_own": q(paint["net"]), "engine_line": line,
                         "line_minus_own": q(D(line) - paint["net"]), "class": sp["residual_class"]},
            "plaster_Q72_beside": {"H": Hp, "basis": R.PLASTER_BASIS,
                                   "source": "T-556 (merged): slab 0.16 + floor build-up 0.05 (T-214 DRAWING-CONFIRMED)"
                                             " / roof DRAWN-SECTION SCENARIO 0.05 (D-39 / DCR-6, ESTIMATED)",
                                   "gross": q(pl["gross"]), "openings": q(pl["openings"]),
                                   "beam_ends": [q(be_lo), q(be_hi)],
                                   "net_own": [q(pl["net"] - be_hi), q(pl["net"] - be_lo)],
                                   "t556_net": [r6["new_lo"], r6["new_hi"]],
                                   "own_minus_t556": [q(pl["net"] - be_hi - D(r6["new_lo"])),
                                                      q(pl["net"] - be_lo - D(r6["new_hi"]))],
                                   "status": r6["status"]},
            "split": {k: q(v) for k, v in sp.items() if k != "residual_class"} | {"residual_class": sp["residual_class"]},
        }
    # GF-02 (wet space in his dry rows): face only
    g2 = drawn["rooms"]["GF-02"]
    F2 = D(g2["perimeter"])
    try:
        R.face_net(F2, {"H": "3.15", "basis": R.PAINT_BASIS}, [], "paint", face_class="WET")
        raise AssertionError("paint on a wet face must be refused")
    except R.RuleError:
        pass
    # returns: 26 valued doors, all re-read
    doors = {}
    for rm in drawn["rooms"].values():
        for o in rm["openings"]:
            if o["kind"] == "door":
                doors[o["id"]] = {"width": o["width"], "t": o["jambs_t"][0]["t"], "jambs": [j["handle"] for j in o["jambs_t"]],
                                  "host": rm["chain_source"]}
    for oid, v in drawn["doors"].items():
        doors[oid] = {"width": v["width"], "t": v["jambs_t"][0]["t"], "jambs": [j["handle"] for j in v["jambs_t"]],
                      "host": v["chain_source"] + " / " + v["edge"]}
    ret_total = Z
    hosts = {}
    import csv
    for r in csv.DictReader(open(ROOT / "research" / "agents_t175" / "T175_OPENING_HOSTS.csv", encoding="utf-8")):
        hosts[r["ID"]] = (r["SIDE_A"], r["SIDE_B"])
    ret_rows, wet_only = [], Z
    for oid in sorted(doors):
        v = doors[oid]
        head = HEADS.get(oid, DOOR)[1]
        a = R.return_face(v["t"], v["width"], head)
        ret_total += a
        sides = hosts.get(oid, ("", ""))
        wet = all(any(w.lower() in s.lower() for w in WET_WORDS) for s in sides)
        if wet:
            wet_only += a
        ret_rows.append({"id": oid, "t": v["t"], "width": v["width"], "head": head, "return_m2": q(a),
                         "jamb_face_handles": v["jambs"], "host": v["host"], "both_sides_wet": wet})
    rows_out, raw = [], {}
    counts = {}
    for sid in SECTIONS:
        ref = refs[sid]
        for i, r in enumerate(ref["rows"]):
            if r["status"] != "UNKNOWN":
                continue
            name, stated = r["name"], D(r["delta"])
            ownv, ev, basis = None, None, None
            rid = next((k for k in ROOMS if f"{k} " in name), None)
            if rid and "opening deductions" in name:
                ownv, basis = own[rid]["openings"], "own openings at G1 (drawn widths, heads per source)"
            elif rid and "length:" in name:
                ownv, basis = own[rid]["length"], "(his L - own F) x his H"
            elif rid and "height:" in name:
                ownv, basis = own[rid]["height"], "(his H - G1) x own F"
            elif "GF-02" in name and "length" in name:
                ownv, basis = (D(GF02[0]) - F2) * D(GF02[1]), "(his 6.75 - own F 7.2) x 3.6"
            elif "GF-02" in name:
                ownv, basis = F2 * D(GF02[1]), "own F (chain 11F / 12B / 118 / 12E) x his 3.6 (WET space, Q-06 A)"
            elif "SHAFT RESIDUAL" in name:
                ownv = sum((D(a) * D(b) for a, b in SHAFT_HIS), Z)
                basis = ("his two rows (2.50 x 5.40 + 11.25 x 3.60); no drawn face: the GF stair-hall / lobby piece "
                         "outlines re-read (12.3 / 4.6 lm, wall-layer 6.6 / 2.3 lm) lie inside the T-173 box")
            elif "RETURN RESIDUAL" in name:
                ownv = D(RETURN_HIS[0]) * D(RETURN_HIS[1]) * D(RETURN_HIS[2]) - ret_total
                basis = "his 14 x 0.20 x 5.70 - own 26 returns (t x (2 x head + w), each re-read)"
            elif name.startswith("RETURN: return faces"):
                ownv, basis = ret_total, "own 26 returns (t x (2 x head + w), each re-read)"
            if ownv is None:
                raise R.RuleError(f"row not matched: {name}")
            raw.setdefault(sid, []).append(D(ownv))
            ev, diff = R.row_evidence(ownv, stated)
            counts[sid] = counts.get(sid, {}) | {ev: counts.get(sid, {}).get(ev, 0) + 1}
            rows_out.append({"section": sid, "row_index": i, "name": name[:160], "class": r["class"],
                             "stated": q(stated), "own": q(ownv), "own_minus_stated": q(diff), "evidence": ev,
                             "basis": basis})
    for sid in SECTIONS:
        counts[sid]["HELD_untouched"] = refs[sid]["status_count"]["HELD"]
    # exact split per section: the signed UNKNOWN total is fixed; own rows re-split it
    split = {}
    for sid in SECTIONS:
        st = sum((D(r["stated"]) for r in rows_out if r["section"] == sid), Z)
        ow = sum(raw[sid], Z)
        # line residuals (own net - engine line) close the room rows to the fixed room deltas
        lr = sum((own[k]["line_residual"] for k in ROOMS), Z)
        # plaster only: the engine's 26 return lines (23.07) sit in the line side of the RETURN RESIDUAL row
        rr = (ret_total - D("23.07")) if sid == SECTIONS[0] else Z
        if ow + lr + rr != st:
            raise R.RuleError(f"{sid}: own split does not close: {ow + lr + rr} vs {st}")
        split[sid] = {"stated_unknown_sum": q(st), "own_rows_sum": q(ow), "line_residuals_sum": q(lr),
                      "return_line_residual": q(rr), "own_rows_plus_residuals": q(ow + lr + rr), "exact": True,
                      "scorecard_unknown_signed": refs[sid]["status_signed"]["UNKNOWN"]}
    return {
        "schema": "T634_PLASTER_PAINT_REMEASURE_V1", "rule": R.RULE_ID, "governing": R.GOVERNING,
        "inputs_sha256_16": {"T634_DRAWN.json": sha16(DRAWN), "SCORECARD_T620.json": sha16(SCORECARD),
                             "T556_PLASTER_HEIGHT.json": sha16(T556)},
        "drawing": drawn["source"], "rooms": rooms_out,
        "gf02_wet": {"face_lm_own": q(F2), "chain": g2["chain"], "paint_refused": True,
                     "openings": [{"id": o["id"], "kind": o["kind"], "width": o["width"]} for o in g2["openings"]]},
        "returns": {"rows": ret_rows, "own_total": q(ret_total), "engine_valued": "23.07",
                    "own_minus_engine": q(ret_total - D("23.07")),
                    "both_sides_wet_m2": q(wet_only),
                    "paint_return_bound": [q(ret_total - wet_only), q(ret_total)],
                    "note": "the paint return (ENGINE_OMISSION, fix row T-569) on a door with WET rooms on both sides "
                            "meets tiled faces (one finish per face, R-T634-1 step 4): paint there is not established; "
                            "the plaster (render) return stays on all 26"},
        "shaft_pieces": drawn["shaft_pieces"], "rows": rows_out, "evidence_count": counts, "split": split,
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    d = build()
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("check", "identical" if same else "DIFFERS")
        return 0 if same else 1
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    for r in d["rows"]:
        print(f"{r['section'][:5]} {r['evidence']:17s} st {r['stated']:>12s} own {r['own']:>12s} d {r['own_minus_stated']:>10s} {r['name'][:60]}")
    print(json.dumps(d["evidence_count"]), json.dumps(d["split"], indent=0))
    print("returns", d["returns"]["own_total"], d["returns"]["own_minus_engine"], d["returns"]["paint_return_bound"])
    for k, v in d["rooms"].items():
        print(k, v["face_lm_own"], v["paint_G1"]["net_own"], v["paint_G1"]["line_minus_own"],
              v["plaster_Q72_beside"]["net_own"], v["plaster_Q72_beside"]["own_minus_t556"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
