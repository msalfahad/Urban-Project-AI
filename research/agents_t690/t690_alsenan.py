"""T-690 builder (development villa; research only, unwired): tiles round 2 on candidate ARCH_TAKEOFF_V3.0.66.

    python3 -I research/agents_t690/t690_alsenan.py [--check]

(a) census restated (R-T690-2) from the merged T-681 census; (b) the WIRING_GAP line closed (R-T690-3); (c) the wet-room
wall band above the finished ceiling per room (R-T690-1, F-T686-1); (d) the MS2-TR nosing: own read of this run
(t690_probe.py on P7757.dxf, private copy; relative stations only) against the merged T-598 edge. Every input is a
merged repository file pinned by sha256; no drawing coordinate, text or client data is written.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t690_rules as R  # noqa: E402

P = {
    "v3065": ("research/agents_t671/out/LINE_INDEX_V3_0_65.json", "e1887c34362b9d2f"),
    "v3066": ("research/agents_t677/out/LINE_INDEX_V3_0_66.json", "02065c41e79dd9df"),
    "t681": ("research/agents_t681/out/T681_TILES_CENSUS.json", "2ca16110154e890f"),
    "faces": ("research/agents_t312/FACE_LEDGER_T312.csv", "71ca2ef5d3fdf36c"),
    "openings": ("research/agents_t312/OPENINGS_T312.csv", "51ce597347d38553"),
    "rooms": ("research/agents_t128/ROOMS_T128_R3.csv", "696333bc12f0acb9"),
    "t686": ("research/agents_t686/out/T686_ROUND3.json", "f755ea4f6154e008"),
    "t598": ("research/agents_t598/ALSENAN_EDGES_T598.json", "2ee67610d6abe69a"),
}
OUT = HERE / "out"
TILE_SCOPE = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD", "EXT.FLOOR.PORCELAIN",
              "EXT.FLOOR.OUTDOOR", "FIN.WALL.TILE", "FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED",
              "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET")

# ---------------------------------------------------------------- heights (sources)
SLAB = ("0.16", "structural general note 16 cm unless stated (owner Q-14); T-556 SLAB")
FLOOR_BUILDUP = ("0.05", "T-214 drawn FFL -> slab top layer on every floor band, Verifier re-measured (T-556)")
ZONES = {  # zone -> interval FFL -> FFL / finished mark above, roof element over its roof part, G1 tile top
    "GF_MAIN": ("4.50", "TERRACE-550", "3.65"),
    "1F": ("4.20", "ROOF-970", "3.35"),
    "2F": ("4.20", "ROOF-1390", "3.35"),
}
ROOF_BUILDUP_MAX = {  # finished roof -> roof slab top; None = no printed maximum found in a merged record
    "ROOF-970": ("0.30", "parapet note ST p.14: b_roof < 0.30 (T-250 s.(d), MERGED)"),
    "ROOF-1390": ("0.30", "parapet note ST p.14: b_roof < 0.30 (T-250 s.(d), MERGED)"),
    "TERRACE-550": (None, "no merged record bounds the terrace build-up from above: the roof part's S runs down to H "
                          "(S >= H is the only physical bound)"),
}
H_SOURCE = "wall-tile top = finished ceiling, owner G1 (Q-43 / Q-48 A): GF 3.65, 1F / 2F 3.35 (ASSUMED - OWNER-APPROVED)"
S_SOURCE = ("plaster top = structural soffit, owner 2026-11-02 / Q-72, by R-T556-1: interval - floor build-up above "
            "- slab (floor part, DRAWING-CONFIRMED); roof part interval - b_roof - slab")
# crossing beams from T-128 r3 CROSSING_BEAMS with the T-110 schedule b x h (BEAM_MEMBER_REGISTER)
BEAMS = {"GF-07": [{"id": "B27", "b": "0.9", "h": "0.85", "src": "T-110 BM-GF-048 B27 90x85"}],
         "GF-14": [{"id": "B11", "b": "0.2", "h": "0.75", "src": "T-110 BM-GF-001 B11 20x75"}]}
PANTRY_LINES = {"plaster": "L-721a0f14", "tile": "L-f5c5a1a9"}  # T-399 carriers of the open pantry GF-07
ANNEX = ("GF-02", "GF-03", "GF-05", "GF-06")
CORE = ("GF-10", "GF-11")
CORE_LEVELS = {"floor_options": ("0.30", "1.00"), "slab_soffit_abs": "5.29", "g1_ceiling_abs": "4.65",
               "src": "C-SH-2 floor +0.30 or +1.00 not drawn (T-088 / T-173); soffit = 1F FFL +5.50 - 0.05 (T-214) - "
                      "0.16 (Q-14) = +5.29; tile top bound 2.20 (highest head, Q-55 C) .. G1 +4.65 - floor (T-686 "
                      "R-T686-3)"}
OPENING_CAPS = {("GF-10", "W05"): "0.48", ("GF-11", "T-128:doorway to the stair hall (no leaf drawn)"): None,
                ("GF-02", "A-GF-01"): None}

# ---------------------------------------------------------------- (d) own read this run (t690_probe.py, P7757 ab54dd55)
OWN_NOSING = {
    "1F plan": "west lane x 0 .. 1.150, well 1.150 .. 1.350, east lane 1.350 .. 2.500 (tread-set stations); west set "
               "12 tread lines at 0.300 to y 3.300 / 3.350 (front / face pair, layers 5 / 2); north wall inner face "
               "(layer 1) y 4.500; N-S pair in the north square: layer 5 at x 1.250 y 3.350 .. 4.500 (1.150) and "
               "layer 2 at x 1.300 (1.150, 0.050 behind): the closing-step front and its riser face",
    "2F plan": "same frame: layer 5 at x 1.250 y 3.300 .. 4.450 (1.150) + layer 2 at x 1.300; north wall face y 4.450",
    "GF plan": "the same two lines lie on layer 2 only (above the GF cut): not a GF object",
    "reading": "the front runs from the well end to the north wall face, 0.100 inside the well from each lane edge; "
               "the front (continuous) lies west of the face, i.e. it overhangs toward the lower west part (+7.516) "
               "from the upper east part (+7.684): one nosing, 1.150 lm, on two plans",
}


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def load(key):
    rel, pin = P[key]
    if sha(rel)[:16] != pin:
        raise R.RuleError(f"{rel}: sha256 changed (pinned {pin})")
    p = ROOT / rel
    if p.suffix == ".json":
        return json.loads(p.read_text())
    return list(csv.DictReader(p.open()))


# ---------------------------------------------------------------- (a)

def part_a(v65, v66, t681):
    R.census_restated(v65["lines"], v66["lines"], lambda c: c in TILE_SCOPE)
    held = sorted(l["line_id"] for l in v66["lines"] if l["class"] == "HELD" and l["item_code"] in TILE_SCOPE)
    ids = [e["line_id"] for e in t681["entries"]]
    if sorted(ids) != held or len(set(ids)) != len(ids):
        raise R.RuleError("T-681 census != V3.0.66 HELD filter")
    fixes = {f["line_id"]: f for f in t681["fix_rows"]}
    rows = []
    for e in t681["entries"]:
        if e["class"] != "MEASURABLE_NOW":
            continue
        f = fixes[e["line_id"]]
        rows.append({"line_id": e["line_id"], "item_code": e["item_code"], "stretch": f["stretch"],
                     "v3066": "HELD blank (unchanged since V3.0.65)", "after": f"{f['state']} "
                     f"{f['length_lm'] if f['length_lm'] is not None else ''} lm".replace("  ", " "),
                     "status": f["status"], "evidence": "T-681 own DXF read; Checker own re-measure AGREE (MERGED "
                     "ebd8a77d, Gate e)", "wired": False})
    by_class = {}
    for e in t681["entries"]:
        by_class[e["class"]] = by_class.get(e["class"], 0) + 1
    return {"candidate": v66["candidate_version"], "rule": "R-T690-2", "in_scope_lines_identical_v3065_v3066": True,
            "held_count": len(held), "by_class_v3066": dict(sorted(by_class.items())),
            "measurable_now": rows, "totals": t681["totals"], "materials": "unchanged from T-681 (areas unchanged): "
            "adhesive group 149 .. 248 bags HELD (no tile size printed)"}


# ---------------------------------------------------------------- (b)

def part_b(v66):
    by = {l["line_id"]: l for l in v66["lines"]}
    line = next(l for l in v66["lines"] if l["line_id"].startswith("L-6ff876ae"))
    hall = next(l for l in v66["lines"] if l["line_id"].startswith("L-af8221bd"))
    if R.D(hall["measured_net"]) != Decimal("6.550") - Decimal("1.000") - Decimal("0.900"):
        raise R.RuleError("GF-ST-HALL skirting is no longer 6.550 - OP-010 1.000 - OP-020 0.900")
    wet = next(l for l in v66["lines"] if l["element_id"] == "GF-RD36087:skirting")
    stair = [l for l in v66["lines"] if l["item_code"].startswith("FIN.STAIR.SKIRTING") and "OP-020" in l["element_id"]]
    neigh = [(hall, False, "4.650 lm = face 6.550 - OP-010 1.000 - OP-020 0.900 (T-443): the passage width is deducted "
                           "and no jamb return is added"),
             (wet, wet["class"] != "EXCLUDED", "basin space GF-11 skirting EXCLUDED (full-height tile, UP-CER-004)")]
    rec = R.wiring_gap_close(line, "EXCLUDED", neigh)
    rec.update({"element_id": line["element_id"], "settled_by": "FR-T601-2 (T-601 / T-604 manifest V12, restated V20, "
                "MERGED): NOT_APPLICABLE by Q-06 A, the passage's wash side is a basin-only wet space", "beside_removed_lm":
                "0.400", "stair_lines_naming_OP_020": len(stair), "effect": "FIN.SKIRTING HELD blank 7 -> 6 on "
                "V3.0.66 (5 after the T-681 W25 fix); valued lm unchanged; nothing moves into a neighbour"})
    assert by[hall["line_id"]] is hall
    return rec


# ---------------------------------------------------------------- (c)

def ledger(faces, openings):
    rooms = {}
    for f in faces:
        if f["scope"] != "TILED":
            continue
        r = rooms.setdefault(f["room"], {"engine_room": f["engine_room"], "length": Decimal(0), "h": set()})
        r["length"] += Decimal(f["length_m"])
        r["h"].add(f["owner_h_m"])
    ops = {}
    for o in openings:
        ops.setdefault(o["room"], []).append(o)
    return rooms, ops


def parse_opening(o):
    size = o["merged_size"]
    w = size.split("w ")[1].split()[0]
    rec = {"id": o["opening_id"], "width": w}
    if " sill " in size and " head " in size:
        rec["sill"] = size.split(" sill ")[1].split()[0]
        rec["head"] = size.split(" head ")[1].split()[0]
    else:
        cap = OPENING_CAPS.get((o["room"], o["opening_id"]), "MISSING")
        if cap == "MISSING":
            raise R.RuleError(f"{o['room']} {o['opening_id']}: unknown height and no cap rule")
        if cap is not None:
            rec["cap_m2"] = cap
    return rec


def cand_lines(v66):
    idx = {}
    for l in v66["lines"]:
        idx.setdefault(l["element_id"], []).append(l)
    return idx


def proof_main(room, er, v66idx):
    """the band is in no line now: backing plaster == wall tile (both to H); paint above wall tile EXCLUDED."""
    if room == "GF-07":
        pl = next(l for ls in v66idx.values() for l in ls if l["line_id"].startswith(PANTRY_LINES["plaster"]))
        tl = next(l for ls in v66idx.values() for l in ls if l["line_id"].startswith(PANTRY_LINES["tile"]))
        paint = [l for l in v66idx.get("HL:WALL_FINISH:GF_07:PAINT", [])]
    else:
        pl = next(l for l in v66idx[f"{er}:plaster"])
        tl = next(l for l in v66idx[f"{er}:wall_tile"])
        paint = v66idx.get(f"{er}:paint above wall tile", [])
    if pl["class"] != "RELEASED" or tl["class"] != "RELEASED" or R.D(pl["measured_net"]) != R.D(tl["measured_net"]):
        raise R.RuleError(f"{room}: backing plaster {pl['line_id']} != wall tile {tl['line_id']}")
    if not paint or any(p["class"] != "EXCLUDED" for p in paint):
        raise R.RuleError(f"{room}: paint over the tile is not EXCLUDED")
    return {"backing_plaster": pl["line_id"], "wall_tile": tl["line_id"], "both_m2": R.S6(R.D(pl["measured_net"])),
            "paint": [p["line_id"] for p in paint], "why": "the room's FIN.PLASTER line is the tile backing to H "
            "(equal to the tile line); paint EXCLUDED; ceiling lines are horizontal / bulkhead drops"}


def part_c(v66, faces, openings, rooms128, t686):
    rooms, ops = ledger(faces, openings)
    r128 = {r["ROW"]: r for r in rooms128}
    v66idx = cand_lines(v66)
    slab, bu = R.D(SLAB[0]), R.D(FLOOR_BUILDUP[0])
    out = []
    # main-house wet rooms (heights from the zone)
    for room in sorted(rooms):
        if room in ANNEX + CORE:
            continue
        info, row = rooms[room], r128[room]
        zone = row["ZONE"]
        interval, roof, g1 = ZONES[zone]
        H = R.D(g1)
        if info["h"] != {g1}:
            raise R.RuleError(f"{room}: ledger tile height {info['h']} != G1 {g1}")
        Sf = R.D(interval) - bu - slab
        r = R.D(row["UNDER_ROOF_SHARE"])
        L = info["length"]
        segs = []
        if r < 1:
            segs.append((L * (1 - r), [(Sf, H)]))
        if r > 0:
            bmax = ROOF_BUILDUP_MAX[roof][0]
            Sr_hi = R.D(interval) - slab
            Sr_lo = Sr_hi - R.D(bmax) if bmax is not None else H
            segs.append((L * r, [(Sr_lo, H), (Sr_hi, H)]))
        op = [parse_opening(o) for o in ops.get(room, [])]
        open_side = R.D(row["OPEN_SIDES_M"] or 0) > 0
        bms = [{"id": b["id"], "b": b["b"], "h": b["h"], "slab": SLAB[0], "ends": (0, 2) if open_side else (2, 2),
                "src": b["src"]} for b in BEAMS.get(room, [])]
        res = R.room_band(segs, op, bms)
        out.append({"room": room, "engine_room": info["engine_room"], "zone": zone, "face_length_m": R.S6(L),
                    "under_roof_share": str(r), "roof": roof if r > 0 else None, "H_m": g1,
                    "S_floor_m": R.S6(Sf), "S_roof_m": [R.S6(segs[-1][1][0][0]), R.S6(segs[-1][1][1][0])] if r > 0
                    else None, "openings_in_band": [o["id"] for o in op], "beams": [b["id"] for b in bms],
                    "band_low_m2": R.S6(res["low"]), "band_high_m2": R.S6(res["high"]),
                    "deducted_m2": [R.S6(res["deducted"][0]), R.S6(res["deducted"][1])],
                    "status": "ASSUMED - OWNER-APPROVED (H Q-48 A) on a DRAWING-CONFIRMED soffit" if r == 0 and not bms
                    else "HELD (bounded): " + ("roof build-up not printed (D-39 / DCR-6)" if r > 0 else "") +
                    ("; " if r > 0 and bms else "") + ("beam-end count in an open-sided room" if bms else ""),
                    "in_no_line_now": proof_main(room, info["engine_room"], v66idx),
                    "carrier": f"FIN.PLASTER, new component line '{info['engine_room']}:plaster band above ceiling' "
                               "(owner trade plaster, register ruling 2026-11-11)"})
    # annex: one datum s (T-686), S and H coupled
    d = t686["annex_datum"]
    s_lo, s_hi = R.D(d["s"][0]), R.D(d["s"][1])
    ffl, beam, ceil = (R.D(d["terms"][k][0]) for k in ("ffl", "beam", "ceiling"))
    pts = [(s - slab - ffl, s - beam - ceil - ffl) for s in R.datum_grid(s_lo, s_hi)]
    t686l = {l["room"]: l for l in t686["lines"]}
    for room in ANNEX + CORE:
        info = rooms[room]
        tl = t686l[room]
        if R.D(tl["length_m"]) != info["length"]:
            raise R.RuleError(f"{room}: T-686 length != T-312 ledger length")
        op = [parse_opening(o) for o in ops.get(room, [])]
        if room in ANNEX:
            room_pts = pts
            # proof: T-686's line stops at H: recompute its bound at the two datum ends from L x H - openings below H
            lo_line = info["length"] * pts[0][1] - sum(_below(o, pts[0][1]) [1] for o in op)
            hi_line = info["length"] * pts[-1][1] - sum(_below(o, pts[-1][1])[0] for o in op)
            if (R.q(lo_line), R.q(hi_line)) != (R.q(tl["held_low"]), R.q(tl["held_high"])):
                raise R.RuleError(f"{room}: T-686 line is not L x H - openings ({lo_line}, {hi_line})")
            status = "HELD (bounded): annex slab top s 3.544 .. 4.30 (Q-54 B / D-39); band height S - H = 0.59 on the " \
                     "whole datum range"
        else:
            room_pts = []
            for f in CORE_LEVELS["floor_options"]:
                S = R.D(CORE_LEVELS["slab_soffit_abs"]) - R.D(f)
                for H in (R.D("2.20"), R.D(CORE_LEVELS["g1_ceiling_abs"]) - R.D(f)):
                    room_pts.append((S, H))
            status = "HELD (bounded): stair-core floor +0.30 / +1.00 not drawn (C-SH-2, designer); tile top 2.20 .. G1"
        res = R.band_over_points(info["length"], room_pts, op)
        jt = R.joint_total(info["length"], room_pts, op)
        out.append({"room": room, "engine_room": info["engine_room"], "zone": "GF_ANNEX" if room in ANNEX else "CORE",
                    "face_length_m": R.S6(info["length"]), "datum_points": len(room_pts),
                    "S_m": [R.S6(min(p[0] for p in room_pts)), R.S6(max(p[0] for p in room_pts))],
                    "H_m": [R.S6(min(p[1] for p in room_pts)), R.S6(max(p[1] for p in room_pts))],
                    "openings_in_band": [o["id"] for o in op], "beams": [],
                    "band_low_m2": R.S6(res["low"]), "band_high_m2": R.S6(res["high"]),
                    "gross_m2": [R.S6(res["gross"][0]), R.S6(res["gross"][1])], "status": status,
                    "t686_line_below_H": {"line_id": tl["line_id"], "low": tl["held_low"], "high": tl["held_high"]},
                    "joint_total_plaster_to_S_m2": [R.S6(jt[0]), R.S6(jt[1])],
                    "in_no_line_now": {"why": "T-686 line = L x H - openings below H (re-computed at both datum ends) "
                                              "for the annex; stair-core lines stop at the tile top by construction; "
                                              "wall tile stops at H; 'paint above wall tile' EXCLUDED"},
                    "carrier": f"FIN.PLASTER, new component line '{info['engine_room']}:plaster band above ceiling'"})
    tot_lo = sum(R.D(o["band_low_m2"]) for o in out)
    tot_hi = sum(R.D(o["band_high_m2"]) for o in out)
    an = [o for o in out if o["zone"] == "GF_ANNEX"]
    return {"rule": "R-T690-1", "H_source": H_SOURCE, "S_source": S_SOURCE, "slab": SLAB, "floor_buildup": FLOOR_BUILDUP,
            "roof_buildup_max": {k: list(v) for k, v in ROOF_BUILDUP_MAX.items()}, "core_levels": CORE_LEVELS,
            "rooms": out, "total_low_m2": R.S6(tot_lo), "total_high_m2": R.S6(tot_hi),
            "annex_gross_m2": R.S6(sum(R.D(o["face_length_m"]) for o in an) * (R.D("0.59"))),
            "annex_low_high_m2": [R.S6(sum(R.D(o["band_low_m2"]) for o in an)),
                                  R.S6(sum(R.D(o["band_high_m2"]) for o in an))]}


def _below(o, H):
    """opening part below H (the T-686 line convention): known -> exact, unknown -> 0 .. w x min(cap height, H)."""
    w = R.D(o["width"])
    if o.get("head") is not None:
        v = w * max(Decimal(0), min(R.D(o["head"]), H) - R.D(o.get("sill", 0)))
        return v, v
    cap = R.D(o["cap_m2"]) if o.get("cap_m2") is not None else w * H
    return Decimal(0), min(cap, w * H)


# ---------------------------------------------------------------- (d)

def part_d(v66, t598):
    e = next(x for x in t598["result"]["edges"] if x["id"] == "ST01-MS2TR")
    rd = t598["reading"]["MS2TR"]
    if (R.D(e["lm"]), R.D(rd["front_len_m"]), R.D(rd["face_offset_m"])) != (R.D("1.15"), R.D("1.15"), R.D("0.05")):
        raise R.RuleError("T-598 MS2-TR edge changed")
    step = [l for l in v66["lines"] if l["item_code"] == "FIN.STAIR.STEP_LM" and l["element_id"] == "1F-R78C367:flight 2"]
    if len(step) != 1 or R.D(step[0]["measured_net"]) != 11 * R.D("1.15"):
        raise R.RuleError("MS2-L step lm is no longer 11 x 1.150")
    nos = [l for l in v66["lines"] if "NOSING" in l["item_code"]]
    return {"edge": "ST01-MS2TR", "own_read": OWN_NOSING, "own_lm": "1.150", "t598_lm": "1.15", "t684_lm": "1.150",
            "agree": True, "status": "DRAWING-CONFIRMED (arch 1F plan, own read this run; arch 2F plan + ST p.5, T-598 "
            "MERGED; one riser on section A-A, T-684)",
            "joins": "B7-05 nosing package T-424 (QUEUED): edge ST01-MS2TR in the landing / floor edges outside the step "
                     "basis (T-598 s.6: 8.550 -> 12.000 lm); V3.0.66 carries no nosing line yet ("
                     f"{len(nos)} lines with NOSING in the code)",
            "no_double_count": f"MS2-L step lm {step[0]['line_id']} = 11 x 1.150 = 12.65 (treads only, no landing edge); "
                               "the T-412 'position not drawn' HELD edge ST01-MS2TR-N01 is the same edge (one count)"}


def build():
    v65, v66, t681 = load("v3065"), load("v3066"), load("t681")
    res = {"schema": "URBAN_T690_TILES_ROUND2_V1", "task": "T-690", "candidate": v66["candidate_version"],
           "inputs": {k: v[1] for k, v in P.items()}, "rules": ["R-T690-1", "R-T690-2", "R-T690-3"],
           "a_census": part_a(v65, v66, t681), "b_wiring_gap": part_b(v66),
           "c_wet_band": part_c(v66, load("faces"), load("openings"), load("rooms"), load("t686")),
           "d_nosing": part_d(v66, load("t598")), "wired": False}
    return res


def md(r):
    a, b, c, d = r["a_census"], r["b_wiring_gap"], r["c_wet_band"], r["d_nosing"]
    L = [f"# T-690 tiles round 2 ({r['candidate']}; research, unwired)", "",
         f"(a) census restated: {a['held_count']} HELD lines, {a['by_class_v3066']}; in-scope lines identical to "
         "V3.0.65.", "", "| line | stretch | V3.0.66 | after (T-681, Checker AGREE) |", "|---|---|---|---|"]
    L += [f"| {x['line_id']} | {x['stretch']} | {x['v3066']} | {x['after']} {x['status']} |" for x in a["measurable_now"]]
    L += ["", f"(b) {b['line_id']} {b['element_id']}: {b['before']} -> {b['after']}; {b['effect']}", "",
          "(c) wet-room wall band above the finished ceiling (m2):", "",
          "| room | engine room | length m | S m | H m | band low | band high | status | joint plaster to S |",
          "|---|---|---|---|---|---|---|---|---|"]
    for o in c["rooms"]:
        if o.get("S_m"):
            S = " .. ".join(o["S_m"])
        else:
            S = ("" if o["under_roof_share"] == "1.0" else f"floor {o['S_floor_m']}; ") + (f"roof {o['S_roof_m'][0]} .. {o['S_roof_m'][1]} (share "
                                             f"{o['under_roof_share']})" if o["S_roof_m"] else "")
        L.append(f"| {o['room']} | {o['engine_room']} | {o['face_length_m']} | {S} | "
                 f"{o['H_m'] if isinstance(o['H_m'], str) else ' .. '.join(o['H_m'])} | {o['band_low_m2']} | "
                 f"{o['band_high_m2']} | {o['status']} | "
                 f"{' .. '.join(o['joint_total_plaster_to_S_m2']) if o.get('joint_total_plaster_to_S_m2') else ''} |")
    L += ["", f"Total {c['total_low_m2']} .. {c['total_high_m2']} m2; annex gross {c['annex_gross_m2']} "
          f"(net {c['annex_low_high_m2'][0]} .. {c['annex_low_high_m2'][1]}).", "",
          f"(d) {d['edge']}: own {d['own_lm']} lm = T-598 {d['t598_lm']} = T-684 {d['t684_lm']}; {d['status']}."]
    return "\n".join(L) + "\n"


def main(argv):
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True, default=str) + "\n"
    m = md(r)
    pj, pm = OUT / "T690_TILES_ROUND2.json", OUT / "T690_TILES_ROUND2.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == m
        print("T-690 outputs", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    pj.write_text(js)
    pm.write_text(m)
    print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
