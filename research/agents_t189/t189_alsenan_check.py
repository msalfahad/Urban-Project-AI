"""T-189 Alsenan check (development villa; not an accuracy claim): concrete at the stair heads / beams B20, B23 / floor
slabs and at the pool base / walls / footing F8 / boundary-wall band, measured once.

Reads ALSENAN_OVERLAP_INPUT.json (drawing readings, cited per value) and the T-184 ledger; uses the unwired module
engine/source/concrete_overlap_ownership.py. Writes nothing unless --out is given (stdlib + numpy; no drawing read).

    python3 -I research/agents_t189/t189_alsenan_check.py [--out T189_STAIR_LEDGER_REV2.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import concrete_overlap_ownership as C  # noqa: E402

INPUT = HERE / "ALSENAN_OVERLAP_INPUT.json"
T184 = ROOT / "research" / "agents_t184" / "T184_LEDGER.json"


def load():
    return json.loads(INPUT.read_text(encoding="utf-8"))


def flight(fid, s):
    x0, x1 = s["string_x"]
    # direction (0, -1): the width runs to the left of travel = +x when side = -1 ... choose the side that covers x0..x1
    f = C.Flight(fid, (x0, s["first_riser_line"]["y"]), tuple(s["direction"]), x1 - x0, s["z0"], s["riser"],
                 s["going"], s["goings"], s["n_triangles"], s["waist"], side=1)
    _, O, d, n = f.frame()
    if n[0] < 0:  # width must run from x0 towards x1
        f.side = -1
    return f


def stair_head_case(fid, s, beam_key, b, slab_key, sl, land_key, ld):
    """elements for one upper flight: the flight (physical incl. the arrival wedge), its beam at the head, the slab
    beyond the beam, the landing at its foot. Returns (flight, elements_rev1, elements_rev2, face_y)."""
    f = flight(fid, s)
    phys = f.pieces(include_arrival_wedge=True)
    rev1 = f.pieces(include_arrival_wedge=False)          # T-184: 12 triangles - the 12th (Q-62 wedge) = 11 + waist
    face = max(b["band_faces_y"])                         # the stair-side face of the band (flight travels -y)
    rev2 = C.clip(rev1, (0, -1, 0), -face, " (to the beam face)")   # keep y >= face
    x0, x1 = b["x"]
    y0, y1 = b["band_faces_y"]
    beam = C.box(x0, x1, y0, y1, b["top"] - b["depth"], b["top"], label=beam_key)
    slab = C.box(sl["x"][0], sl["x"][1], sl["y"][0], sl["y"][1], sl["top"] - sl["t"], sl["top"], label=slab_key)
    land = C.box(ld["x"][0], ld["x"][1], ld["y"][0], ld["y"][1], ld["top"] - ld["t"], ld["top"], label=land_key)
    led = s["ledger_T184"]
    e_beam = C.Element(beam_key, "BEAM", beam, ledger_m3=b["width"] * (x1 - x0) * b["depth"])
    e_slab = C.Element(slab_key, "SLAB", slab)
    e_land = C.Element(land_key, "LANDING", land)
    e1 = C.Element(fid, "STAIR", phys, billed=rev1, ledger_m3=led["steps"] + led["waist"] - led["q62_deducted"])
    e2 = C.Element(fid, "STAIR", phys, billed=rev2)
    return f, [e1, e_beam, e_slab, e_land], [e2, e_beam, e_slab, e_land], face, rev1


def in_band_parts(f, rev1, face, y_far):
    """the flight solid between the band's stair-side face and the last riser line, by part (steps / waist)."""
    band = C.box(-1e3, 1e3, y_far, face, -1e3, 1e3)[0]
    out = {}
    for p in rev1:
        v = C.volume(C.intersect(p, band))
        if v > 1e-12:
            out[p.label] = v
    return out


def d_shape(r, back, wall_t, n=36):
    """pool outline (T-183 kind D): half circle r round the origin on x <= 0, rectangle 0 .. back on x >= 0.
    Returns (base plan pieces, wall band pieces) as convex plan polygons (the arc as n chords, chords stated)."""
    ri = r - wall_t
    arc = [(math.pi / 2 + math.pi * k / n) for k in range(n + 1)]
    base = [[(0, -r), (back, -r), (back, r), (0, r)]]
    base += [[(0.0, 0.0), (r * math.cos(a0), r * math.sin(a0)), (r * math.cos(a1), r * math.sin(a1))]
             for a0, a1 in zip(arc, arc[1:])]                      # half disc as a fan of n convex triangles
    walls = [[(back - wall_t, -r), (back, -r), (back, r), (back - wall_t, r)],
             [(0, ri), (back - wall_t, ri), (back - wall_t, r), (0, r)],
             [(0, -r), (back - wall_t, -r), (back - wall_t, -ri), (0, -ri)]]
    for a0, a1 in zip(arc, arc[1:]):
        walls.append([(ri * math.cos(a0), ri * math.sin(a0)), (r * math.cos(a0), r * math.sin(a0)),
                      (r * math.cos(a1), r * math.sin(a1)), (ri * math.cos(a1), ri * math.sin(a1))])
    return base, walls


def pool_case(p, walls_from_underside=False):
    o, lv = p["outline"], p["levels"]
    base_pl, wall_pl = d_shape(o["r_outer"], o["back_x"], o["wall_t"])
    base = [q for pl in base_pl for q in C.plan_prism(pl, lv["base_underside"], lv["base_top"], label="pool base")]
    walls_phys = [q for pl in wall_pl for q in C.plan_prism(pl, lv["base_top"], lv["rim"], label="pool wall")]
    zb = lv["base_underside"] if walls_from_underside else lv["base_top"]
    walls_billed = [q for pl in wall_pl for q in C.plan_prism(pl, zb, lv["rim"], label="pool wall billed")]
    f8 = p["F8"]
    bw = p["BW_band"]
    els = [C.Element("POOL BASE", "POOL_BASE", base),
           C.Element("POOL WALLS", "POOL_WALL", walls_phys, billed=walls_billed),
           C.Element("F8", "FOOTING", C.plan_prism([(f8["x"][0], f8["y"][0]), (f8["x"][1], f8["y"][0]),
                                                     (f8["x"][1], f8["y"][1]), (f8["x"][0], f8["y"][1])], None, None,
                                                    label="F8"), levels_known=False),
           C.Element("B.W band", "BW_BASE", C.plan_prism([(bw["x"][0], bw["y"][0]), (bw["x"][1], bw["y"][0]),
                                                           (bw["x"][1], bw["y"][1]), (bw["x"][0], bw["y"][1])],
                                                          None, None, label="B.W band"), levels_known=False)]
    return els


def run():
    data = load()
    st, bm, sl, ld = data["stairs"], data["beams"], data["slabs"], data["landings"]
    cases = [("MS1-U", "B20 span 2", "GF-077 (part under the 1F arrival)", "MS1-LD"),
             ("MS2-U", "B23 span 2", "1F-062 (part under the 2F arrival)", "MS2-LD (east half)")]
    res = {}
    for fid, bk, sk, lk in cases:
        f, el1, el2, face, rev1 = stair_head_case(fid, st[fid], bk, bm[bk], sk, sl[sk], lk, ld[lk])
        r1 = C.check_ownership(el1)
        r2 = C.check_ownership(el2)
        y_last = st[fid]["last_riser_line"]["y"]
        parts = in_band_parts(f, rev1, face, y_last)
        led = st[fid]["ledger_T184"]
        gross = led["steps"] + led["waist"]
        wedge = C.total_volume([p for p in f.pieces() if "arrival wedge" in p.label])
        head_in_band = sum(parts.values())
        res[fid] = dict(
            gross_m3=gross, arrival_wedge_m3=wedge, in_band_m3=head_in_band, in_band_parts=parts,
            rev1_ledger_m3=gross - led["q62_deducted"], rev2_m3=gross - led["q62_deducted"] - head_in_band,
            rev1_check=dict(status=r1["status"], double_m3=r1["double_m3"], gap_m3=r1["gap_m3"],
                            pairs=[(r["pair"], r["status"], r.get("m3"), r.get("billed_twice_m3"), r.get("owner"))
                                   for r in r1["pairs"]]),
            rev2_check=dict(status=r2["status"], double_m3=r2["double_m3"], gap_m3=r2["gap_m3"],
                            union_m3=r2["union_m3"], owned=r2["owned"],
                            pairs=[(r["pair"], r["status"], r.get("m3"), r.get("billed_twice_m3"), r.get("owner"))
                                   for r in r2["pairs"]]),
            beam_billed_m3=r2["elements"][bk]["billed_m3"], beam_released_line=bm[bk]["released_line"],
            sensitivity=sensitivity(f, rev1, bm[bk], face, y_last))
    pool = C.check_ownership(pool_case(data["pool"]))
    pool_adv = C.check_ownership(pool_case(data["pool"], walls_from_underside=True))
    res["POOL"] = dict(status=pool["status"], union_m3=pool["union_m3"], double_m3=pool["double_m3"],
                       gap_m3=pool["gap_m3"], base_m3=pool["elements"]["POOL BASE"]["billed_m3"],
                       walls_m3=pool["elements"]["POOL WALLS"]["billed_m3"],
                       held=[(h["pair"], h["status"], h["exposure_m3"]) for h in pool["held"]],
                       adverse_walls_from_base_underside=dict(status=pool_adv["status"],
                                                               double_m3=pool_adv["double_m3"]))
    return res


def sensitivity(f, rev1, b, face, y_last):
    """vertical margins: the in-band flight solid stays inside the beam section while the stair's reference plane is
    shifted by dz in [-up, +down] against the beam's (dz > 0 = stair lower)."""
    band = C.box(-1e3, 1e3, y_last, face, -1e3, 1e3)[0]
    zs = []
    for p in rev1:
        q = C.intersect(p, band)
        A, bb = q.arrays()
        _, _, verts, _ = C._vertices(A, bb)
        zs += [v[2] for v in verts]
    top, bot = b["top"], b["top"] - b["depth"]
    return dict(flight_in_band_z=[min(zs), max(zs)], beam_z=[bot, top],
                margin_up_m=top - max(zs), margin_down_m=min(zs) - bot)


# status of every ST-01 piece after the Checker's 15:00 / 17:18 runs (BOARD T-180 / T-184 verdicts) and owner 18:00 (4)
_STATUS = {
    "MS1-L": ("HELD", "owner 18:00 (4): structural GF roof slab plan draws 12 straight riser lines (16 with the winders) "
                      "vs architectural plan 10 + section A-A 15: consultant item C-ST-4; candidate 0.863 (section) .. "
                      "1.055 (structural plan), Checker 17:18", [0.863, 1.055]),
    "MS1-U": ("DRAWING-CONFIRMED", "rev2 = Checker quantity 0.9976 (17:18, D-CHK-T180-1); Checker to confirm on rev2", None),
    "MS2-L": ("VERIFIED", "Checker 15:00 (T-184 MERGED): 1.059", None),
    "MS2-U": ("DRAWING-CONFIRMED", "rev2 = Checker quantity 1.0014 (17:18, D-CHK-T180-1); Checker to confirm on rev2", None),
    "MS1-LD": ("VERIFIED", "Checker 17:18: 0.2304", None),
    "MS2-LD": ("PARTLY VERIFIED", "east half 0.240 VERIFIED, west half 0.2304 .. 0.240 not verified (Checker 17:18)", None),
}


def ledger_rev2(res):
    """T-184 ST-01 ledger rev1 (kept unchanged in research/agents_t184) -> rev2: the head of MS1-U / MS2-U net of the
    flight solid inside the full-depth beams B20 / B23 (R-CONC-OWN-1); every other row unchanged."""
    old = json.loads(T184.read_text(encoding="utf-8"))
    st = {s["stair_id"]: s for s in old["stairs"]}
    st01 = st["ST-01"]
    head = {"MS1-U": res["MS1-U"]["in_band_m3"], "MS2-U": res["MS2-U"]["in_band_m3"]}
    flights = {}
    for r in st01["rows"]:
        fid = r["part"].split()[0]
        if r.get("owner") == "FLOOR_SLAB":
            continue
        flights.setdefault(fid, 0.0)
        flights[fid] += r["m3"]
    q62 = {"MS1-U": 0.03, "MS2-U": 0.03024, "MS2-L": 0.030171}
    rows = []
    for fid, gross in flights.items():
        net1 = gross - q62.get(fid, 0.0)
        net2 = net1 - head.get(fid, 0.0)
        status, why, rng = _STATUS[fid]
        rows.append(dict(piece=fid, gross_m3=round(gross, 6), q62_wedge_m3=q62.get(fid, 0.0),
                         head_in_full_depth_beam_m3=round(head.get(fid, 0.0), 6), rev1_net_m3=round(net1, 6),
                         rev2_net_m3=round(net2, 6), status=status, why=why, held_range_m3=rng))
    tot1 = sum(r["rev1_net_m3"] for r in rows)
    tot2 = sum(r["rev2_net_m3"] for r in rows)
    held_ms1l = next(r for r in rows if r["piece"] == "MS1-L")
    others = {k: st[k]["net_m3"] for k in ("ST-01b", "ST-02", "ST-03")}
    sys1 = tot1 + sum(others.values())
    sys2 = tot2 + sum(others.values())
    return dict(
        schema="T189_STAIR_LEDGER_REV2", supersedes="research/agents_t184/T184_LEDGER.json (rev1, kept unchanged)",
        rule="R-CONC-OWN-1 (research/agents_t189/R-CONC-OWN-1.json, proposed)",
        st01_rows=rows, st01_rev1_m3=round(tot1, 4), st01_rev2_m3=round(tot2, 4),
        st01_change_m3=round(tot2 - tot1, 4),
        other_stairs_unchanged_m3={k: round(v, 4) for k, v in others.items()},
        staircase_system_rev1_m3=round(sys1, 4), staircase_system_rev2_m3=round(sys2, 4),
        staircase_system_rev2_not_held_m3=round(sys2 - held_ms1l["rev2_net_m3"], 4),
        held_unchanged=[h for s in old["stairs"] for h in s["held"] if h["id"] != "HEAD-CLASH"],
        resolved=dict(id="HEAD-CLASH", candidate_rev1=[0.1147, 0.1147],
                      resolution="flight solid inside B20 / B23 (billed at 0.75 full depth through the shaft in the "
                                 "released route G lines) deducted from the stair, owned by the beams; the riser-count "
                                 "RFI (Q-46) stays open for the designer, quantities follow its answer"),
        system_status="PARTIALLY VERIFIED (owner 16:45; never VERIFIED as a whole while pieces are held)",
        beams=dict(B20=res["MS1-U"]["beam_released_line"], B23=res["MS2-U"]["beam_released_line"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--ledger-out")
    a = ap.parse_args()
    res = run()
    if a.ledger_out:
        Path(a.ledger_out).write_text(json.dumps(ledger_rev2(res), indent=1) + "\n", encoding="utf-8")
    for k in ("MS1-U", "MS2-U"):
        r = res[k]
        print(f"{k}: gross {r['gross_m3']:.4f}  rev1 (T-184) {r['rev1_ledger_m3']:.4f} -> {r['rev1_check']['status']} "
              f"double {r['rev1_check']['double_m3']:.4f} | in band {r['in_band_m3']:.4f} -> rev2 {r['rev2_m3']:.4f} "
              f"{r['rev2_check']['status']} double {r['rev2_check']['double_m3']:.6f} gap {r['rev2_check']['gap_m3']:.6f}")
    print(json.dumps(res, indent=1, default=float))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
