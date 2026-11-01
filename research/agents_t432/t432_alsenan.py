"""T-432 development villa (Alsenan is one sample): is the freelancer's ST-02 length 16.4 m one drawn construction?

Build (needs the PRIVATE structural DXF 'ST7757 dxf.dxf' from Drive folder 'Alsenan chalet project', decoded into
.work/private only, sha256 9f9d1179...):
    python3 -I research/agents_t432/t432_alsenan.py --dxf <ST7757 dxf.dxf> --write
reads ST p.4 (GF roof slab plan) BY HANDLE (type and layer asserted), measures the plan length of every ST-02 piece
(RS-C curved, RS-S straight, RS-LD corner landing, RS-A straight) on four paths (INNER, CENTRE, RISERS, OUTER), and
writes summary_t432.json beside this file (lengths in m and counts only: no coordinates, no drawing content).
Check (no private input):
    python3 -I research/agents_t432/t432_alsenan.py --check
re-derives every construction and the classification from the committed summary and prints REPRODUCED.

Freelancer side: his ST-02 row as recorded by the merged T-415 (1.2 x 16.4 x 0.28 = 5.5104 m3, his own printed
figures); the row text stays in the private workbook. Engine side: merged T-258 r2 / T-415 drawn plan areas (cited).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t432_rules as R  # noqa: E402

SUMMARY = HERE / "summary_t432.json"
MM = 0.001
RISE = 4.50 / 28  # Q-50 A cond: plan count 28 (ASSUMED — OWNER-APPROVED), as T-415 / T-258
RSC = ["2EA", "2E9", "2E8", "2E7", "2E6", "2E5", "2E4", "2E3", "2E2", "2E1", "2E0", "2DF"]  # walking order
RSS = ["2BA", "2C1", "2C0", "2BF", "2BE", "2BD", "2BC", "2BB", "2C2", "2C3", "2C4"]          # sorted by x below
RSA = ["2C8", "2C9", "2CA", "2CB", "315"]
HIS = dict(w=1.2, l=16.4, t=0.28)                 # T-415 record of his own printed figures
DRAWN_AREA = 10.835596                            # T-415 MERGED 8c8372a4: RS-C 4.443096 + RS-S 3.600 + RS-LD 1.3525 + RS-A 1.440
AREA_BEYOND_M3 = -2.476433                        # T-415 term AREA_BEYOND_DRAWN (engine - freelancer)
LOWER_TREADS_P3 = 9                               # T-415 s.4: the 9 lower treads also drawn on ST p.3 (cited)
GOING = 0.300                                     # drawn spacing of the straight riser lines (RS-S / RS-A)


def build(dxf_path: str) -> dict:
    import ezdxf

    db = ezdxf.readfile(dxf_path).entitydb

    def ent(h, typ, layer):
        e = db[h]
        assert e.dxftype() == typ, (h, e.dxftype(), typ)
        assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
        return e

    inner, outer = ent("2DE", "ARC", "S-OPENING"), ent("2DD", "ARC", "S-OPENING")
    c = inner.dxf.center
    assert math.hypot(outer.dxf.center[0] - c[0], outer.dxf.center[1] - c[1]) < 1e-3
    r_in, r_out = inner.dxf.radius * MM, outer.dxf.radius * MM

    def rel(p):
        return ((p[0] - c[0]) * MM, (p[1] - c[1]) * MM)

    void = ent("2D0", "LINE", "S-OPENING")      # RS-S void-side edge (inner straight edge)
    b3 = ent("283", "LINE", "1")                # 'B3 (With Stair)' band face: RS-S / landing outer edge
    e289 = ent("289", "LINE", "1")              # slab opening edge: landing / RS-A outer edge
    e2cf = ent("2CF", "LINE", "S-OPENING")      # RS-A void-side edge
    y_void, y_b3 = rel(void.dxf.start)[1], rel(b3.dxf.start)[1]
    x_289, x_2cf = rel(e289.dxf.start)[0], rel(e2cf.dxf.start)[0]
    assert abs(rel(void.dxf.end)[1] - y_void) < 1e-6 and abs(rel(b3.dxf.end)[1] - y_b3) < 1e-6
    assert abs(rel(e289.dxf.end)[0] - x_289) < 1e-6 and abs(rel(e2cf.dxf.end)[0] - x_2cf) < 1e-6

    def line(h):
        e = ent(h, "LINE", "2")
        return rel(e.dxf.start), rel(e.dxf.end)

    # straight risers: RS-S vertical lines (x const), RS-A horizontal lines (y const)
    xs = sorted(line(h)[0][0] for h in RSS)
    for h in RSS:
        (a, b) = line(h)
        assert abs(a[0] - b[0]) < 1e-6
    ys = [line(h)[0][1] for h in RSA]
    for h in RSA:
        (a, b) = line(h)
        assert abs(a[1] - b[1]) < 1e-6
    assert ys == sorted(ys)
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)] + [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    assert all(abs(g - GOING) < 1e-4 for g in gaps), gaps
    x_2ba, x_2c4 = xs[0], xs[-1]
    assert abs(line("2BA")[0][0] - x_2ba) < 1e-9 and abs(line("2C4")[0][0] - x_2c4) < 1e-9
    y_2c8, y_315 = ys[0], ys[-1]
    assert abs(y_2c8 - y_void) < 1e-4, "RS-A first riser on the RS-S void edge line"

    def angle_on_circle(h, r):
        """angle (deg, 0..360) where the infinite riser line h meets the circle of radius r (the root nearest h)."""
        (p, q) = line(h)
        dx, dy = q[0] - p[0], q[1] - p[1]
        A = dx * dx + dy * dy
        B = 2 * (p[0] * dx + p[1] * dy)
        C = p[0] ** 2 + p[1] ** 2 - r * r
        disc = B * B - 4 * A * C
        assert disc > 0, (h, r)
        ts = [(-B + s * math.sqrt(disc)) / (2 * A) for s in (1, -1)]
        t = min(ts, key=lambda t_: abs(t_ - 0.5))
        x, y = p[0] + t * dx, p[1] + t * dy
        return math.degrees(math.atan2(y, x)) % 360

    def mid(h):
        (p, q) = line(h)
        return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)

    # RS-C plan from riser 2EA to riser 2BA on each path
    a_in_end = inner.dxf.end_angle                              # inner arc meets the void edge 2D0
    p_in_end = rel(inner.end_point)
    assert abs(p_in_end[1] - y_void) < 1e-3
    a_out_end = outer.dxf.end_angle                             # outer arc meets the B3 face 283
    p_out_end = rel(outer.end_point)
    assert abs(p_out_end[1] - y_b3) < 1e-3
    r_c = (r_in + r_out) / 2
    y_c = (y_void + y_b3) / 2                                   # straight-lane centre
    rsc = dict(
        INNER=r_in * math.radians(a_in_end - angle_on_circle("2EA", r_in)) + (x_2ba - p_in_end[0]),
        CENTRE=r_c * math.radians(270.0 - angle_on_circle("2EA", r_c)) + x_2ba,
        RISERS=sum(math.dist(mid(a), mid(b)) for a, b in zip(RSC, RSC[1:] + ["2BA"])),
        OUTER=r_out * math.radians(a_out_end - angle_on_circle("2EA", r_out)) + (x_2ba - p_out_end[0]),
    )
    rsc_chord = dict(CENTRE=math.dist((r_c * math.cos(math.radians(angle_on_circle("2EA", r_c))),
                                       r_c * math.sin(math.radians(angle_on_circle("2EA", r_c)))), (x_2ba, y_c)))
    dth = [angle_on_circle(b, r_c) - angle_on_circle(a, r_c) for a, b in zip(RSC, RSC[1:])]
    rss = {p: x_2c4 - x_2ba for p in R.PATHS}
    # corner landing between 2C4 (x) and 2C8 (y): path from the RS-S path line to the RS-A path line
    x_a = dict(INNER=x_2cf, CENTRE=(x_2cf + x_289) / 2, OUTER=x_289)
    y_s = dict(INNER=y_void, CENTRE=y_c, OUTER=y_b3)
    rsld = {p: max(0.0, x_a[p] - x_2c4) + max(0.0, y_2c8 - y_s[p]) for p in ("INNER", "CENTRE", "OUTER")}
    rsld["RISERS"] = math.dist(mid("2C4"), mid("2C8"))
    rsa = {p: y_315 - y_2c8 for p in R.PATHS}
    r6 = R.r6
    geo = dict(
        schema="T432_ALSENAN_ST02_LENGTHS",
        drawing="'ST7757 dxf.dxf' sha256 9f9d1179 (Drive 'Alsenan chalet project'), ST p.4 GF roof slab plan",
        total_rise=4.50, drawn_risers=28, riser_status="ASSUMED — OWNER-APPROVED (Q-50 A cond, plan count 28, no section)",
        lane=dict(r_in=r_in, r_out=r_out, r_centre=r_c, straight_inner=-y_void, straight_outer=-y_b3,
                  straight_width=y_void - y_b3, rsa_width=x_289 - x_2cf,
                  centre_jump_at_270=r_c - (-y_c), inner_arc_end_deg=a_in_end, outer_arc_end_deg=a_out_end),
        rsc_dtheta_centre_deg=dict(min=min(dth), max=max(dth)),
        pieces=[
            dict(id="ST02-RS-C", kind="curved", n_risers=len(RSC), handles=f"{RSC[0]} .. {RSC[-1]} -> 2BA", plan=rsc,
                 chord=rsc_chord),
            dict(id="ST02-RS-S", kind="straight", n_risers=len(RSS), handles="2BA .. 2C4", plan=rss),
            dict(id="ST02-RS-LD", kind="landing", n_risers=0, handles="2C4 -> 2C8 (283 / 289 / 2CF / 2D0)", plan=rsld),
            dict(id="ST02-RS-A", kind="straight", n_risers=len(RSA), handles="2C8 .. 315", plan=rsa),
        ],
        n_treads=dict(RS_C=len(RSC), RS_S=len(RSS) - 1, RS_A=len(RSA) - 1),
    )
    return _round(geo)


def _round(o):
    if isinstance(o, float):
        return R.r6(o)
    if isinstance(o, dict):
        return {k: _round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v) for v in o]
    return o


def stair_from(g) -> R.Stair:
    pieces = [R.Piece(p["id"], p["kind"], p["n_risers"], p["plan"], p.get("chord", {})) for p in g["pieces"]]
    return R.Stair(pieces, g["total_rise"] / g["drawn_risers"], g["drawn_risers"], g["riser_status"])


def derive(g: dict) -> dict:
    st = stair_from(g)
    nt = sum(g["n_treads"].values())
    land = {p: next(x for x in g["pieces"] if x["kind"] == "landing")["plan"][p] for p in ("CENTRE", "OUTER")}
    cands = R.constructions(st, n_treads=nt, going=GOING, landing_plans=land)
    # double-drawing candidate (T-415): the lower RS-C treads drawn again on ST p.3 counted a second time (plan only)
    dth = math.radians(g["rsc_dtheta_centre_deg"]["min"])
    radius = dict(INNER=g["lane"]["r_in"], CENTRE=g["lane"]["r_centre"], OUTER=g["lane"]["r_out"])
    for p, r in radius.items():
        cands[f"{p} / PROFILE + RS-C treads 1-{LOWER_TREADS_P3} again (ST p.3)"] = R.r6(
            cands[f"{p} / PROFILE"] + LOWER_TREADS_P3 * r * dth)
    res = R.classify(HIS["l"], cands)
    restated = R.restate_area_beyond(AREA_BEYOND_M3, HIS["l"], HIS["w"], HIS["t"], DRAWN_AREA, res)
    centre_profile = cands["CENTRE / PROFILE"]
    # Illustrative only (never a term): what his length would leave if the T-417 profile convention were his on ST-02
    illus = dict(label="ILLUSTRATIVE, not a term: T-417 convention (CENTRE / PROFILE) assumed for ST-02",
                 profile_m=centre_profile, remainder_m=R.r6(HIS["l"] - centre_profile),
                 rise_in_length_m3=R.r6(-st.rise * HIS["w"] * HIS["t"]),
                 remainder_m3=R.r6(AREA_BEYOND_M3 + st.rise * HIS["w"] * HIS["t"]))
    plan_drawn_len = DRAWN_AREA / HIS["w"]
    return dict(rise=R.r6(st.rise), drawn_risers=st.drawn_risers, n_treads=nt,
                plan_by_path={p: R.r6(sum(x["plan"][p] for x in g["pieces"])) for p in R.PATHS},
                drawn_plan_length_on_his_width=R.r6(plan_drawn_len),
                his_beyond_drawn_m=R.r6(HIS["l"] - plan_drawn_len),
                classification=res, n_constructions=len(cands),
                within_his_rounding_band=[t[0] for t in res["table"] if abs(t[2]) <= 0.05],
                rsc_centre_profile_m=R.r6(R.flight_profile(st, "ST02-RS-C", "CENTRE")),
                restated=restated, illustrative=illus)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        d = derive(s["geometry"])
        if json.dumps(d, sort_keys=True) == json.dumps(s["derived"], sort_keys=True):
            print("REPRODUCED")
            return 0
        print("DIFFERS")
        print(json.dumps(d, indent=1))
        return 1
    g = build(a.dxf)
    s = dict(geometry=g, derived=derive(g))
    txt = json.dumps(s, indent=1, ensure_ascii=False)
    if a.write:
        SUMMARY.write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
