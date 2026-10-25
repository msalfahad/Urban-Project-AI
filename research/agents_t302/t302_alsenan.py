"""T-302 on the development villa (P7757): the developed hole W17 leaves in the curved 1F wall, per face, and the
1F-11 plaster / paint line recomputed from T-292's face ledger with only the W17 hole replaced.

Drawing read (own, P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55), all values RELATIVE: plan values about the
arc centre of the curved bay (mm), elevation values about the elevation's crown axis and the +5.50 level mark (mm).
`python3 -I research/agents_t302/t302_alsenan.py --extract <P7757.dxf>` re-reads every handle below and fails on any
difference; `python3 -I research/agents_t302/t302_alsenan.py` rewrites the committed outputs.

Plan (layer 1 wall cut, layer W glass; arcs about ONE centre): room face BD2 r 2135 (135.1898 .. 223.4682 deg),
exterior face BCE r 1935 (135.1898 .. 223.3295), radial jamb lines BD9 (135.1898 at r 2135 and r 1935) and BD7
(223.4682 at r 2135 -> 223.3295 at r 1935). The room 1F-11 lies outside the circle (west): the bay is convex into the
room, concave to the exterior (east), where the elevation looks from.

Elevation (NW frame, layer 1): jamb lines 2A44 / 2A46 at u -1327.7832 / +1363.7108 rise from the +5.50 floor (u axis =
plan +y about the arc centre) and end ON the arch chain 2738 .. 2741 (12 chords, crown 3000 at u 0); the printed
horizontal chain 2D61 201.9 | 2D53 2691.5 | 2D46 166.0 dimensions them. The arch chain's ends u -1529.7059 / +1529.7058
at 1350 (lines 2784 / 2565 below them) are the projected ENDS OF THE CURVED BAY on the exterior face (BCD / BD0 r 1935 at
127.7635 / 232.2365 deg: 1935 sin 127.7635 = 1529.7059), not the window's jambs: the 1.350 'springing' is outside the hole.
"""
from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t302_arched_hole as R  # noqa: E402

ROOT = HERE.parents[1]
T292 = ROOT / "research" / "agents_t292" / "FACE_TO_LINE_LEDGER_T292.csv"
SOURCE = "P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55), own read 2026-10-25"

# ---- plan, mm about the arc centre (handles on P7757.dxf model space) -------------------------------------------
R_ROOM, R_EXT = 2135.0, 1935.0                     # BD2 (layer W, room-side glass line = room face), BCE (layer 5)
A_JAMB_N = 135.189832913944                        # BD9: radial, same angle at r 2135 and r 1935
A_JAMB_S_ROOM, A_JAMB_S_EXT = 223.4682228589107, 223.3294911776438   # BD7 ends (r 2135 / r 1935)
R_CL = (R_ROOM + R_EXT) / 2                        # wall centreline 2035 (0.20 wall)
BAY_ENDS_EXT = (127.7634663660, 232.2365336340)               # BCD start / BD0 end on r 1935 (the curved bay's exterior ends)

# ---- elevation, mm: u about the crown axis (= plan +y about the arc centre), height above the +5.50 mark ----------
HEAD = [(-1529.7059, 1350.0), (-1503.8830, 1768.8459), (-1365.5303, 2165.0242), (-1125.0000, 2508.8903),
        (-800.2902, 2774.7141), (-415.6976, 2942.6049), (0.0, 3000.0), (415.6976, 2942.6049),
        (800.2902, 2774.7141), (1125.0000, 2508.8903), (1365.5303, 2165.0242), (1503.8830, 1768.8459),
        (1529.7058, 1350.0)]                       # arch chain 2738 / 2739 / 273A / 27CC / 273B / 273C | 273D / 273E /
#                                                    27CD / 273F / 2740 / 2741
HEAD_HANDLES = ["2738", "2739", "273A", "27CC", "273B", "273C", "273D", "273E", "27CD", "273F", "2740", "2741"]
JAMBS_U = (-1327.7832, 1363.7108)                  # 2A44 / 2A46 (tops 2218.9881 / 2167.6254 = H at those u)
JAMB_TOPS = (2218.9881, 2167.6254)
PRINTED_CHAIN = {"2D61": 201.9227, "2D53": 2691.4940, "2D46": 165.9950}
LEVEL_MARKS = {"2888 (+5.50)": 0.0, "2886 (+1.00)": -4500.0}  # vertical 1 : 1 (4500 mm per 4.50 m)
SILL = 0.0                                          # the hole runs from the +5.50 floor (jamb lines from u-axis 0)

# ---- T-292 face ledger: the 1F-11 W17 piece and the owner face height ----------------------------------------------
FACE_LEN_T128, OWNER_H = 3.2860, 3.35               # T-292 row 1F-11|OFF:GLAZING (T-250 ROOM_CLOSURE, G1)
WINDOW_Q76A = round(3.29 * 3.00, 4)                          # 9.870 m2: the WINDOW line's measure (Q-76 A), never the hole


def _jamb_angle_on(r):
    """BD7 is a straight line from (r 2135, 223.4682) to (r 1935, 223.3295): its angle where it crosses radius r."""
    p = (R_ROOM * math.cos(math.radians(A_JAMB_S_ROOM)), R_ROOM * math.sin(math.radians(A_JAMB_S_ROOM)))
    q = (R_EXT * math.cos(math.radians(A_JAMB_S_EXT)), R_EXT * math.sin(math.radians(A_JAMB_S_EXT)))
    dx, dy = q[0] - p[0], q[1] - p[1]
    a, b, c = dx * dx + dy * dy, 2 * (p[0] * dx + p[1] * dy), p[0] ** 2 + p[1] ** 2 - r * r
    t = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    if not 0 <= t <= 1:
        t = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
    return math.degrees(math.atan2(p[1] + t * dy, p[0] + t * dx)) % 360


def model():
    prof = R.HeadProfile(HEAD)
    elev = R.Elevation(origin=(0.0, 0.0), e=(0.0, 1.0))
    ok, res = R.register(elev, (0.0, 0.0), R_EXT, A_JAMB_N, A_JAMB_S_EXT, JAMBS_U)
    return prof, elev, ok, res


def faces():
    prof, elev, ok, res = model()
    c = (0.0, 0.0)
    spec = [("EXTERIOR (reference, elevation face)", R_EXT, A_JAMB_N, A_JAMB_S_EXT, "BCE + BD9 / BD7 (r 1935)"),
            ("CENTRELINE (blockwork)", R_CL, A_JAMB_N, _jamb_angle_on(R_CL), "mid of BCE / BD2, BD9 / BD7 at r 2035"),
            ("ROOM SIDE (1F-11 plaster / paint)", R_ROOM, A_JAMB_N, A_JAMB_S_ROOM, "BD2 + BD9 / BD7 (r 2135)")]
    out = []
    for name, r, a1, a2, src in spec:
        f = R.face_record(name, prof, elev, c, r, a1, a2, R_EXT, SILL, registered=ok)
        f.update(a1=a1, a2=a2, source=src,
                 projected=prof.projected_area(*sorted(elev.u_on(c, r, math.radians(a)) for a in (a1, a2)), SILL)
                 if r == R_EXT else None)
        out.append(f)
    return out, ok, res


def _m2(v):
    return None if v is None else v / 1e6


def ledger_rows():
    fs, ok, res = faces()
    rows = []
    for f in fs:
        rows.append({
            "face": f["face"], "radius_m": f"{f['radius'] / 1000:.4f}",
            "jamb_angles_deg": f"{f['a1']:.4f} .. {f['a2']:.4f}",
            "developed_jamb_to_jamb_m": f"{f['developed_width'] / 1000:.4f}",
            "projected_m2": "" if f["projected"] is None else f"{_m2(f['projected']):.4f}",
            "hole_radial_m2": f"{_m2(f['radial']):.4f}", "hole_prismatic_m2": f"{_m2(f['prismatic']):.4f}",
            "hole_m2": (f"{_m2(f['lo']):.4f}" if f["status"] == R.STATUS_CONFIRMED else
                        f"{_m2(f['lo']):.4f} .. {_m2(f['hi']):.4f}"),
            "rectangle_cap_m2": f"{f['developed_width'] / 1000 * (max(h for _, h in HEAD) - SILL) / 1000:.4f}",
            "status": f["status"], "held_item": f["held_item"], "plan_source": f["source"],
            "elevation_source": "head 2738 .. 2741, jambs 2A44 / 2A46, chain 2D61 / 2D53 / 2D46, level 2888 / 2886",
        })
    return rows, ok, res


def t292_1f11():
    """The 1F-11 rows of T-292's face ledger, per code: the 8 VERIFIED faces and the W17 piece's gross."""
    out = {}
    for r in csv.DictReader(T292.read_text(encoding="utf-8").splitlines()):
        if r["room"] != "1F-11":
            continue
        d = out.setdefault(r["item_code"], dict(verified=0.0, n=0, w17=None))
        if r["openings"] == "W17":
            d["w17"] = (float(r["length_m"]), float(r["owner_h_m"]), float(r["owner_net_lo_m2"]),
                        float(r["owner_net_hi_m2"]))
        else:
            assert r["owner_status"] == "VERIFIED", r["face_id"]
            d["verified"] += float(r["owner_net_lo_m2"])
            d["n"] += 1
    return out


def line_rows():
    fs, ok, res = faces()
    room = fs[2]
    lo_h, hi_h = _m2(room["lo"]), _m2(room["hi"])
    rows = []
    for code, d in sorted(t292_1f11().items()):
        w, h, t292_lo, t292_hi = d["w17"]
        gross = round(w * h, 4)
        assert (w, h) == (FACE_LEN_T128, OWNER_H)
        p_lo, p_hi = R.piece_net(gross, lo_h, hi_h)
        # T-292 reproduced first: its own hole bounds on the same gross give its own piece (residual 0.0000)
        rep = round(gross - FACE_LEN_T128 * 3.000, 4), round(gross - FACE_LEN_T128 * 1.350, 4)
        rows.append({
            "item_code": code, "room": "1F-11", "verified_faces": d["n"], "verified_m2": f"{d['verified']:.4f}",
            "w17_piece_gross_m2": f"{gross:.4f}",
            "t292_piece_m2": f"{t292_lo:.4f} .. {t292_hi:.4f}",
            "t292_reproduced_residual_m2": f"{abs(rep[0] - t292_lo) + abs(rep[1] - t292_hi):.4f}",
            "t302_hole_room_m2": f"{lo_h:.4f} .. {hi_h:.4f}",
            "t302_piece_m2": f"{p_lo:.4f} .. {p_hi:.4f}",
            "t302_line_m2": f"{d['verified'] + p_lo:.4f} .. {d['verified'] + p_hi:.4f}",
            "t292_line_m2": f"{d['verified'] + t292_lo:.4f} .. {d['verified'] + t292_hi:.4f}",
            "released_candidate_m2": "59.4511",
            "status": room["status"], "held_item": room["held_item"],
        })
    return rows


def _csv(rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue()


def summary():
    fs, ok, res = faces()
    ext, cl, room = fs
    lines = line_rows()
    return {
        "task": "T-302", "rule": R.R_ID, "source": SOURCE,
        "registration": {"ok": ok, "residual_mm": [round(x, 4) for x in res], "tolerance_mm": R.REG_TOL_MM,
                         "printed_chain_mm": PRINTED_CHAIN},
        "exterior_hole_m2": round(_m2(ext["lo"]), 4), "exterior_status": ext["status"],
        "exterior_projected_m2": round(_m2(ext["projected"]), 4),
        "centreline_hole_m2": [round(_m2(cl["lo"]), 4), round(_m2(cl["hi"]), 4)],
        "room_hole_m2": [round(_m2(room["lo"]), 4), round(_m2(room["hi"]), 4)],
        "room_hole_radial_m2": round(_m2(room["radial"]), 4), "room_status": room["status"],
        "elevation_full_chain_projected_m2": round(R.HeadProfile(HEAD).projected_area(HEAD[0][0], HEAD[-1][0]) / 1e6,
                                                   4),
        "window_line_q76a_m2": WINDOW_Q76A,
        "line_1f11": {r["item_code"]: r["t302_line_m2"] for r in lines},
        "quantity_changed_in_candidate": False,
    }


def outputs():
    rows, ok, res = ledger_rows()
    return {"W17_HOLE_LEDGER_T302.csv": _csv(rows), "LINE_1F11_T302.csv": _csv(line_rows()),
            "summary.json": json.dumps(summary(), indent=2, sort_keys=True) + "\n"}


def extract(path):
    """Re-read every handle on the private DXF and compare with the committed relative constants (mm, 1e-3)."""
    import ezdxf  # noqa: PLC0415
    db = ezdxf.readfile(path).entitydb
    bd2 = db["BD2"]
    cx, cy = bd2.dxf.center.x, bd2.dxf.center.y
    chk = []

    def same(a, b, what, tol=1e-3):
        chk.append((what, a, b))
        if abs(a - b) > tol:
            raise SystemExit(f"DIFFERS {what}: drawing {a} vs committed {b}")

    for h, r, a1, a2 in (("BD2", R_ROOM, A_JAMB_N, A_JAMB_S_ROOM), ("BCE", R_EXT, A_JAMB_N, A_JAMB_S_EXT)):
        e = db[h]
        same(e.dxf.center.x, cx, f"{h} centre x")
        same(e.dxf.center.y, cy, f"{h} centre y")
        same(e.dxf.radius, r, f"{h} r")
        same(e.dxf.start_angle, a1, f"{h} a1", 1e-6)
        same(e.dxf.end_angle, a2, f"{h} a2", 1e-6)
    for h, ang in (("BD9", (A_JAMB_N, A_JAMB_N)), ("BD7", (A_JAMB_S_ROOM, A_JAMB_S_EXT))):
        e = db[h]
        for p, a in zip((e.dxf.start, e.dxf.end), ang):
            same(math.degrees(math.atan2(p.y - cy, p.x - cx)) % 360, a, f"{h} angle", 1e-3)
    for h, a in (("BCD", BAY_ENDS_EXT[0]), ("BD0", BAY_ENDS_EXT[1])):
        e = db[h]
        same(e.dxf.radius, R_EXT, f"{h} r")
        same(e.dxf.start_angle if h == "BCD" else e.dxf.end_angle, a, f"{h} bay end", 1e-3)
    crown = db["273C"].dxf.end
    ex, ey = crown.x, crown.y - 3000.0
    pts = []
    for h in HEAD_HANDLES:
        e = db[h]
        s, t = (e.dxf.start.x - ex, e.dxf.start.y - ey), (e.dxf.end.x - ex, e.dxf.end.y - ey)
        if not pts:
            pts.append(s)
        pts.append(t)
    for (u, hh), (cu, ch) in zip(pts, HEAD):
        same(u, cu, "head u")
        same(hh, ch, "head h")
    for h, u, top in (("2A44", JAMBS_U[0], JAMB_TOPS[0]), ("2A46", JAMBS_U[1], JAMB_TOPS[1])):
        e = db[h]
        same(e.dxf.start.x - ex, u, f"{h} u")
        same(min(e.dxf.start.y, e.dxf.end.y) - ey, 0.0, f"{h} foot")
        same(max(e.dxf.start.y, e.dxf.end.y) - ey, top, f"{h} top")
    for h, m in PRINTED_CHAIN.items():
        same(db[h].get_measurement(), m, f"{h} printed")
    for k, v in LEVEL_MARKS.items():
        same(db[k.split()[0]].dxf.insert.y - ey, v, f"level {k}")
    # elevation u axis = plan +y about the arc centre: the plan jambs on r 1935 project onto 2A44 / 2A46
    same(R_EXT * math.sin(math.radians(A_JAMB_S_EXT)), JAMBS_U[0], "plan->elev south jamb")
    same(R_EXT * math.sin(math.radians(A_JAMB_N)), JAMBS_U[1], "plan->elev north jamb")
    same(R_EXT * math.sin(math.radians(BAY_ENDS_EXT[0])), HEAD[-1][0], "bay end -> arch end", 0.05)
    print(f"EXTRACT OK: {len(chk)} values agree")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--extract":
        extract(sys.argv[2])
    else:
        for n, t in outputs().items():
            (HERE / n).write_text(t, encoding="utf-8")
            print("wrote", n)
