"""T-192 concrete ownership at every stair foot, head, landing and column of the staircase system (R-CONC-OWN-1).

Development villa (Drive 'Alsenan chalet project'); not an accuracy claim. Reads ALSENAN_JUNCTION_INPUT.json (drawing
readings, handles cited) and the T-189 ledger rev2 (kept unchanged); uses the unwired module
engine/source/concrete_overlap_ownership.py READ ONLY (every new geometry here is a new function of this script).
Writes nothing unless --ledger-out / --out is given. stdlib + numpy.

    python3 -I research/agents_t192/t192_staircase_junctions.py [--ledger-out T192_STAIR_LEDGER_REV3.json] [--out res.json]

New functions (general, any villa):
  knee_top(flight, landing_top, landing_t)    the drawing-derived concrete under a landing / plate that a flight arrives
                                              into: between the flight's waist-soffit line produced and the landing
                                              soffit, beyond the last riser line (the owner's Q-47 A waist stops at the
                                              last riser line, so this solid is in no line);
  knee_bottom(flight, landing_t)              the part of the Q-47 A waist below the soffit of the landing a flight
                                              leaves (re-entrant corner: not built, over-measured by the plumb cut);
  foot_in_member(flight, member)              the flight solid below the floor it starts from that lies inside a member
                                              billed through the junction (foot corollary of R-CONC-OWN-1);
  junction_rows(...)                          one owner per intersection, with the evidence status.
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

INPUT = HERE / "ALSENAN_JUNCTION_INPUT.json"
REV2 = ROOT / "research" / "agents_t189" / "T189_STAIR_LEDGER_REV2.json"

# R-CONC-OWN-1 main clause applied to a column line billed through the flight (T-119: full storey interval, column
# 3.80 / 4.10 m + joint): precedence COLUMN 50 > STAIR 10 of the module's route G profile; the pair is added here as an
# established pair (proposed, labelled; the module's own table is not edited).
ESTABLISHED = dict(C.ESTABLISHED_PAIRS_ROUTE_G)
ESTABLISHED[frozenset(("COLUMN", "STAIR"))] = ("R-CONC-OWN-1 main clause (T-192, proposed): a column line billed "
                                               "through the flight (T-119 full interval) owns the intersection")


def load():
    return json.loads(INPUT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- general geometry (new functions)

def flight_y(fid, s, y_first_key="first_riser_y"):
    """a flight travelling +-y between string_x (width across x)."""
    x0, x1 = s["string_x"]
    f = C.Flight(fid, (x0, s[y_first_key]), tuple(s["direction"]), x1 - x0, s["z0"], s["riser"], s["going"],
                 s["goings"], s["n_triangles"], s["waist"] if s.get("waist") else 0.16, side=1)
    _, _, _, n = f.frame()
    if n[0] < 0:
        f.side = -1
    return f


def flight_x(fid, s):
    """a flight travelling +x between y[0] .. y[1] (width across y)."""
    y0, y1 = s["y"]
    f = C.Flight(fid, (s["first_riser_x"], y0), tuple(s["direction"]), y1 - y0, s["z0"], s["riser"], s["going"],
                 s["goings"], s["n_triangles"], s["waist"] if s.get("waist") else 0.16, side=1)
    _, _, _, n = f.frame()
    if n[1] < 0:
        f.side = -1
    return f


def _consts(f):
    r, g, t = f.riser, f.going, f.waist
    k = r / g
    d = t / (g / math.hypot(g, r))
    return r, g, t, k, d


def knee_top(f, landing_top, landing_t):
    """drawing-derived solid under the landing a flight arrives into (local s >= L, z' <= H - tl, z' >= k s - d)."""
    r, g, t, k, d = _consts(f)
    L = f.goings * g
    H = landing_top - f.z0
    lo = H - landing_t
    w = f.width
    rows = [((0, -1, 0), 0.0), ((0, 1, 0), w), ((-1, 0, 0), -L), ((0, 0, 1), lo), ((k, 0, -1), d)]
    p = f._local(rows, f"{f.id} top knee")
    s_top = (lo + d) / k
    hand = 0.5 * (s_top - L) * (lo - (k * L - d)) * w
    return p, hand, s_top


def knee_bottom(f, landing_t):
    """part of the Q-47 A waist below the soffit of the landing the flight leaves (0 <= s <= s_b): not built."""
    r, g, t, k, d = _consts(f)
    if d <= landing_t:
        return None, 0.0
    w = f.width
    rows = [((0, -1, 0), 0.0), ((0, 1, 0), w), ((-1, 0, 0), 0.0), ((0, 0, 1), -landing_t), ((k, 0, -1), d)]
    p = f._local(rows, f"{f.id} bottom knee")
    s_b = (d - landing_t) / k
    return p, 0.5 * s_b * (d - landing_t) * w


def waist_piece(f):
    return [p for p in f.pieces(include_arrival_wedge=False) if p.label.endswith("waist")]


def steps_only(f, include_arrival_wedge=True):
    return [p for p in f.pieces(include_arrival_wedge=include_arrival_wedge) if not p.label.endswith("waist")]


def foot_in_member(f, member_pieces):
    """flight solid (steps + waist, no arrival wedge) inside a member billed through the foot junction."""
    return C.intersection_volume(f.pieces(include_arrival_wedge=False), member_pieces)


def box(d, top_key="top", t_key="t", label=""):
    return C.box(d["x"][0], d["x"][1], d["y"][0], d["y"][1], d[top_key] - d[t_key], d[top_key], label=label)


def beam_box(b, label):
    return C.box(b["x"][0], b["x"][1], b["y"][0], b["y"][1], b["top"] - b["depth"], b["top"], label=label)


# ---------------------------------------------------------------- the staircase system, junction by junction

def st01(data):
    s = data["st01"]
    B20 = beam_box(s["beams"]["B20 span 2"], "B20 span 2")
    B23 = beam_box(s["beams"]["B23 span 2"], "B23 span 2")
    GF077 = box(s["slabs"]["GF-077 (part under the 1F arrival)"], label="GF-077 part")
    F062 = box(s["slabs"]["1F-062 (part under the 2F arrival)"], label="1F-062 part")
    lds = s["landings"]
    LD1 = box(lds["MS1-LD"], label="MS1-LD")
    LDE = box(lds["MS2-LD east"], label="MS2-LD east")
    LDW = box(lds["MS2-LD west"], label="MS2-LD west")
    f1u = flight_y("MS1-U", s["MS1-U"])
    f2l = flight_y("MS2-L", s["MS2-L"])
    f2u = flight_y("MS2-U", s["MS2-U"])

    # billed solids, rev3: each flight net of what a member billed through the junction owns
    def net(f, cut_members):
        out = f.pieces(include_arrival_wedge=False)
        for m in cut_members:
            out = C._minus_all(out, m)
        return out

    # T-184 deducted for MS2-L only the part of its arrival wedge inside the landing (0.030171 of 0.030240): the
    # sliver below the landing soffit stays in the stair line
    sliver_2l = C._minus_all([p for p in f2l.pieces(include_arrival_wedge=True) if "arrival wedge" in p.label], LDW)
    rev3 = {"MS1-U": net(f1u, [B20]), "MS2-L": net(f2l, [B20]) + sliver_2l, "MS2-U": net(f2u, [B23])}
    rev2 = {"MS1-U": net(f1u, [B20]), "MS2-L": f2l.pieces(include_arrival_wedge=False) + sliver_2l,
            "MS2-U": net(f2u, [B23])}

    foot_2l = foot_in_member(f2l, B20)
    parts = {}
    for p in f2l.pieces(include_arrival_wedge=False):
        v = C.intersection_volume([p], B20)
        if v > 1e-12:
            parts[p.label] = v

    # hand check of the MS2-L foot (s in [0, a], a = band face - first riser line; waist below the floor level only)
    r, g, t, k, d = _consts(f2l)
    a = s["beams"]["B20 span 2"]["y"][1] - s["MS2-L"]["first_riser_y"]
    hand_foot = (d * a - 0.5 * k * a * a) * f2l.width

    # knees
    kt_2l, kt_2l_hand, s_top_2l = knee_top(f2l, lds["MS2-LD west"]["top"], lds["MS2-LD west"]["t"])
    kb_1u, kb_1u_hand = knee_bottom(f1u, lds["MS1-LD"]["t"])
    kb_2u, kb_2u_hand = knee_bottom(f2u, lds["MS2-LD east"]["t"])

    col = s["columns"]["COL-1F-36"]
    COL = C.box(col["drawn_x"][0], col["drawn_x"][1], col["y"][0], col["y"][1], col["z"][0], col["z"][1],
                label="COL-1F-36 drawn")
    col_exposure = C.intersection_volume(f2l.pieces(include_arrival_wedge=False), COL)
    colg = s["columns"]["COL-GF-06"]

    # PHYSICAL solids (drawing-derived): owner-formula solid + arrival wedge, the top knee under MS2-LD west added
    # (net of the wedge, disjoint pieces), the bottom knees under MS1-LD / MS2-LD east removed (not built)
    wedge_2l = [p for p in f2l.pieces(include_arrival_wedge=True) if "arrival wedge" in p.label]
    knee_2l = C._minus_all([kt_2l], wedge_2l)
    phys = {"MS1-U": C._minus_all(f1u.pieces(include_arrival_wedge=True), [kb_1u]),
            "MS2-L": f2l.pieces(include_arrival_wedge=True) + knee_2l,
            "MS2-U": C._minus_all(f2u.pieces(include_arrival_wedge=True), [kb_2u])}
    # drawing-derived billing: rev3 with the knees settled (top knee billed to the stair, bottom knees not billed)
    dd = {"MS1-U": C._minus_all(rev3["MS1-U"], [kb_1u]), "MS2-L": rev3["MS2-L"] + knee_2l,
          "MS2-U": C._minus_all(rev3["MS2-U"], [kb_2u])}

    def elements(billed):
        return [
            C.Element("MS1-U", "STAIR", phys["MS1-U"], billed=billed["MS1-U"]),
            C.Element("MS2-L", "STAIR", phys["MS2-L"], billed=billed["MS2-L"]),
            C.Element("MS2-U", "STAIR", phys["MS2-U"], billed=billed["MS2-U"]),
            C.Element("B20 span 2", "BEAM", B20), C.Element("B23 span 2", "BEAM", B23),
            C.Element("GF-077 part", "SLAB", GF077), C.Element("1F-062 part", "SLAB", F062),
            C.Element("MS1-LD", "LANDING", LD1), C.Element("MS2-LD east", "LANDING", LDE),
            C.Element("MS2-LD west", "LANDING", LDW),
        ]

    chk2 = C.check_ownership(elements(rev2), established=ESTABLISHED)
    chk3 = C.check_ownership(elements(rev3), established=ESTABLISHED)
    chk_dd = C.check_ownership(elements(dd), established=ESTABLISHED)
    els3 = elements(dd)
    owned = C.owned_volumes(els3, established=ESTABLISHED)
    # column case: the drawn 0.25 section through MS2-L, column billed (T-119) vs not billed (A / V3.0.4)
    col_els = [C.Element("MS2-L", "STAIR", f2l.pieces(include_arrival_wedge=False)),
               C.Element("COL-1F-36", "COLUMN", COL)]
    col_chk = C.check_ownership(col_els, established=ESTABLISHED)
    sens = dict(foot_z=_zrange(f2l.pieces(include_arrival_wedge=False), B20),
                beam_z=[s["beams"]["B20 span 2"]["top"] - s["beams"]["B20 span 2"]["depth"], s["beams"]["B20 span 2"]["top"]])
    return dict(
        MS2L_foot_in_B20_m3=foot_2l, MS2L_foot_parts=parts, MS2L_foot_hand_m3=hand_foot, MS2L_foot_band_strip_m=a,
        MS2L_rev3_m3=s["MS2-L"]["ledger_rev2_m3"] - foot_2l, MS2L_wedge_sliver_m3=C.total_volume(sliver_2l),
        MS2L_rev2_geometry_m3=C.total_volume(rev2["MS2-L"]), MS2L_rev3_geometry_m3=C.total_volume(rev3["MS2-L"]),
        knee_top_MS2L=dict(m3=C.volume(kt_2l), hand_m3=kt_2l_hand, s_top=s_top_2l,
                           in_landing_m3=C.intersection_volume([kt_2l], LDW)),
        knee_bottom_MS1U=dict(m3=C.volume(kb_1u) if kb_1u else 0.0, hand_m3=kb_1u_hand),
        knee_bottom_MS2U=dict(m3=C.volume(kb_2u) if kb_2u else 0.0, hand_m3=kb_2u_hand),
        column_1F36=dict(exposure_drawn_m3=col_exposure, check_status=col_chk["status"],
                         pairs=[(p["pair"], p["status"], p.get("m3"), p.get("owner")) for p in col_chk["pairs"]],
                         schedule=col["schedule_section"], billed_A=col["billed_A"]),
        column_GF06=dict(into="MS1-L (HELD)", drawn=colg["drawn"],
                         exposure_note="0.05 x 0.50 projection over the MS1-L storey; MS1-L stays HELD (C-ST-4), so "
                                       "the deduction is applied with MS1-L when it is released"),
        check_rev2=_summ(chk2), check_rev3=_summ(chk3), check_drawing_derived=_summ(chk_dd),
        issues_rev3=chk3["issues"], owned_drawing_derived=owned,
        sum_owned_m3=sum(owned.values()), union_m3=chk_dd["union_m3"], sensitivity=sens)


def _zrange(pieces, member):
    zs = []
    for p in pieces:
        for q in member:
            pq = C.intersect(p, q)
            if C.volume(pq) <= 1e-12:
                continue
            A, b = pq.arrays()
            _, _, V, _ = C._vertices(A, b)
            zs += [v[2] for v in V]
    return [min(zs), max(zs)] if zs else None


def _summ(chk):
    return dict(status=chk["status"], double_m3=chk["double_m3"], gap_m3=chk["gap_m3"], union_m3=chk["union_m3"],
                billed_sum_m3=chk["billed_sum_m3"],
                pairs=[(p["pair"], p["status"], p.get("m3"), p.get("billed_twice_m3"), p.get("owner"))
                       for p in chk["pairs"]])


def st03(data):
    e = data["st03_e1"]
    f = flight_x("E1", e)
    steps = steps_only(f, include_arrival_wedge=True)        # T-184 ledger: 5 triangles = 4 + the arrival wedge
    wedge = [p for p in steps if "arrival wedge" in p.label]
    gs = e["ground_slab_face"]
    GS = C.box(gs["x"][0], gs["x"][1], gs["y"][0], gs["y"][1], gs["top"] - gs["t"], gs["top"], label="ground slab")
    gb = e["gb_band"]
    GB = C.plan_prism([(gb["x"][0], gb["y"][0]), (gb["x"][1], gb["y"][0]), (gb["x"][1], gb["y"][1]),
                       (gb["x"][0], gb["y"][1])], None, None, label="GB band")
    in_slab = C.intersection_volume(wedge, GS)
    in_gb_plan = C.intersection_volume(steps, GB)
    net_steps = C._minus_all(steps, GS)
    els = [C.Element("E1", "STAIR", steps, billed=steps), C.Element("ground slab L-83e4f6fa", "SLAB", GS),
           C.Element("GB band", "BEAM", GB, levels_known=False)]
    chk_before = C.check_ownership(els)
    els3 = [C.Element("E1", "STAIR", steps, billed=net_steps), C.Element("ground slab L-83e4f6fa", "SLAB", GS),
            C.Element("GB band", "BEAM", GB, levels_known=False)]
    chk_after = C.check_ownership(els3)
    owned = C.owned_volumes([els3[0], els3[1]])
    return dict(steps_m3=C.total_volume(steps), wedge_m3=C.total_volume(wedge), wedge_in_ground_slab_m3=in_slab,
                steps_in_gb_band_plan_m3=in_gb_plan, rev3_m3=e["ledger_m3"] - in_slab,
                check_before=_summ(chk_before), check_after=_summ(chk_after),
                held=[(h["pair"], h["status"], h["exposure_m3"]) for h in chk_after["held"]],
                sum_owned_m3=sum(owned.values()), union_m3=chk_after["union_m3"])


def st02_knees(data):
    s = data["st02"]
    rs = s["RS-S"]
    f_s = flight_x("RS-S", rs)
    kt_s, kt_s_hand, st_s = knee_top(f_s, s["RS-LD"]["top"], s["RS-LD"]["t"])
    ra = s["RS-A"]
    f_a = C.Flight("RS-A", (ra["x"][0], ra["first_riser_y"]), (0, 1), ra["width_ledger"], ra["z0"], ra["riser"],
                   ra["going"], ra["goings"], ra["n_triangles"], ra["waist"], side=1)
    _, _, _, n = f_a.frame()
    if n[0] < 0:
        f_a.side = -1
    kt_a, kt_a_hand, st_a = knee_top(f_a, 5.50, 0.16)       # arrival plate C-T1 at 1F +5.50, T 0.16 (ST p.8 note 18)
    kb_a, kb_a_hand = knee_bottom(f_a, s["RS-LD"]["t"])
    return dict(knee_top_RSS=dict(m3=C.volume(kt_s), hand_m3=kt_s_hand, s_top=st_s),
                knee_top_RSA=dict(m3=C.volume(kt_a), hand_m3=kt_a_hand, s_top=st_a, plate="C-T1 +5.50 T 0.16"),
                knee_bottom_RSA=dict(m3=C.volume(kb_a) if kb_a else 0.0, hand_m3=kb_a_hand))


def released_stair_head(data):
    """route G stair line L-ffef.. (V3.0.4 L-7863..): its east run (MS1-U) is measured by stair_geometry.straight_flight
    to the last riser line, 0.20 inside B20: the part of its own profile inside the band, per reading."""
    from engine.source import stair_geometry as SG
    rl = data["released_lines"]["STAIR_GF"]
    b = data["st01"]["beams"]["B20 span 2"]
    strip = data["st01"]["MS1-U"]["last_riser_y"] - b["y"][0]   # 45.148 - 44.948 ... band from the far face
    face_gap = b["y"][1] - data["st01"]["MS1-U"]["last_riser_y"]  # 0.20 from the stair-side face to the last riser
    w = rl["width"]
    out = {}
    for riser in rl["readings"]["riser_m"]:
        for waist in rl["readings"]["waist_m"]:
            res = SG.straight_flight(12, riser, 0.30, w, waist)
            run = res["run"]
            pts = res["outline"]
            area_in = _clip_area(pts, run - face_gap, run)
            out[f"riser {riser} waist {waist}"] = dict(flight_m3=res["STAIR_CONCRETE_VOLUME"], in_band_m3=area_in * w)
    base = out["riser 0.165 waist 0.175"]
    return dict(line=rl["line"], base=base, readings=out, strip_from_band_far_face_m=strip, in_band_strip_m=face_gap,
                corrected_m3=rl["m3"] - base["in_band_m3"],
                range_correction_m3=[min(v["in_band_m3"] for v in out.values()), max(v["in_band_m3"] for v in out.values())])


def _clip_side(poly, s, keep_below):
    """Sutherland-Hodgman clip of a simple polygon (s, z) by the vertical line at s."""
    def inside(p):
        return p[0] <= s + 1e-12 if keep_below else p[0] >= s - 1e-12
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if inside(a):
            out.append(a)
        if inside(a) != inside(b):
            tpar = (s - a[0]) / (b[0] - a[0])
            out.append((s, a[1] + tpar * (b[1] - a[1])))
    return out


def _clip_area(pts, s0, s1):
    """area of the part of a simple polygon (s, z) with s0 <= s <= s1 (the flight profile is convex in s-strips)."""
    poly = _clip_side(_clip_side(list(pts), s0, keep_below=False), s1, keep_below=True)
    if len(poly) < 3:
        return 0.0
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2.0


def formwork(data, r01):
    """T-163 r3 stair formwork against the same foot / head boundaries: the waist soffit inside a full-depth beam
    is not formed; the riser at a last riser line inside a band is the beam's side face above the tread (one owner)."""
    fw = data["formwork_T163_r3"]
    s = data["st01"]
    rows = []
    for fid, strip in (("MS1-U", 0.20), ("MS2-U", 0.20), ("MS2-L", r01["MS2L_foot_band_strip_m"])):
        f = s[fid]
        sec = math.hypot(f["going"], f["riser"]) / f["going"]
        w = f["string_x"][1] - f["string_x"][0]
        rows.append(dict(face=f"{fid} waist soffit inside the full-depth band", m2=-strip * w * sec))
    total = sum(r["m2"] for r in rows)
    return dict(rows=rows, stair_m2_before=fw["stairs_m2"], stair_m2_after=fw["stairs_m2"] + total, change_m2=total,
                riser_note="MS1-U / MS2-U riser 12 (0.200 / 0.2016 m2): the vertical face above the step-11 tread at the "
                           "band face is ONE face, counted as the stair riser form; the HELD 'beam side next to STAIR' "
                           "lines (T-163: GF 0 .. 13.731, 1F 0 .. 3.195 m2) must exclude it when they are released")


def run():
    data = load()
    r01 = st01(data)
    r03 = st03(data)
    r02 = st02_knees(data)
    rel = released_stair_head(data)
    fw = formwork(data, r01)
    return dict(st01=r01, st03=r03, st02=r02, released_GF_stair=rel, formwork=fw)


def ledger_rev3(res):
    old = json.loads(REV2.read_text(encoding="utf-8"))
    rows = []
    for r in old["st01_rows"]:
        r = dict(r)
        r["rev3_net_m3"] = r["rev2_net_m3"]
        r["rev3_change_m3"] = 0.0
        if r["piece"] == "MS2-L":
            d = res["st01"]["MS2L_foot_in_B20_m3"]
            r["foot_in_full_depth_beam_m3"] = round(d, 6)
            r["rev3_net_m3"] = round(r["rev2_net_m3"] - d, 6)
            r["rev3_change_m3"] = round(-d, 6)
            r["status"] = "DRAWING-CONFIRMED"
            r["why"] = ("rev2 1.0589 was VERIFIED (Checker 15:00) on the owner formula; rev3 deducts the waist below the "
                        "1F floor inside B20 (first riser line 646 y 45.198 is 0.15 m inside the band, R-CONC-OWN-1 foot "
                        "corollary): Checker to re-measure")
        rows.append(r)
    st01_3 = sum(r["rev3_net_m3"] for r in rows)
    others = dict(old["other_stairs_unchanged_m3"])
    e1 = res["st03"]["wedge_in_ground_slab_m3"]
    others_rev3 = dict(others)
    others_rev3["ST-03"] = round(others["ST-03"] - e1, 4)
    sys3 = st01_3 + sum(others_rev3.values())
    held_ms1l = next(r for r in rows if r["piece"] == "MS1-L")["rev3_net_m3"]
    knees = [
        dict(id="KNEE-MS2L-TOP", m3=round(res["st01"]["knee_top_MS2L"]["m3"], 6), where="under MS2-LD west, beyond the "
             "MS2-L last riser line"),
        dict(id="KNEE-RSS-TOP", m3=round(res["st02"]["knee_top_RSS"]["m3"], 6), where="under RS-LD beyond the RS-S last riser line"),
        dict(id="KNEE-RSA-TOP", m3=round(res["st02"]["knee_top_RSA"]["m3"], 6), where="under the arrival plate C-T1"),
        dict(id="KNEE-MS1U-BOTTOM", m3=round(-res["st01"]["knee_bottom_MS1U"]["m3"], 6), where="MS1-U foot under MS1-LD (not built)"),
        dict(id="KNEE-MS2U-BOTTOM", m3=round(-res["st01"]["knee_bottom_MS2U"]["m3"], 6), where="MS2-U foot under MS2-LD east (not built)"),
        dict(id="KNEE-RSA-BOTTOM", m3=round(-res["st02"]["knee_bottom_RSA"]["m3"], 6), where="RS-A foot under RS-LD (not built)"),
    ]
    return dict(
        schema="T192_STAIR_LEDGER_REV3", supersedes="research/agents_t189/T189_STAIR_LEDGER_REV2.json (rev2, kept unchanged)",
        rule="R-CONC-OWN-1 (research/agents_t189/R-CONC-OWN-1.json, proposed) + R-CONC-OWN-1a foot / knee / column "
             "corollaries (research/agents_t192/R-CONC-OWN-1a.json, proposed)",
        st01_rows=rows, st01_rev2_m3=old["st01_rev2_m3"], st01_rev3_m3=round(st01_3, 4),
        st01_change_m3=round(st01_3 - old["st01_rev2_m3"], 4),
        other_stairs_rev2_m3=others, other_stairs_rev3_m3=others_rev3,
        st03_change=dict(m3=round(-e1, 6), why="E1 arrival wedge (5th triangle, x 94.468 .. 94.768) inside the released "
                         "ground-slab line L-83e4f6fa87db7452e2d2 (face 4.18 m2 from x 94.718) over its last 0.05 m: "
                         "slab owns (Q-62 A cond)"),
        staircase_system_rev2_m3=old["staircase_system_rev2_m3"], staircase_system_rev3_m3=round(sys3, 4),
        staircase_system_rev3_not_held_m3=round(sys3 - held_ms1l, 4),
        drawing_derived_not_in_owner_method=dict(
            knees=knees, net_m3=round(sum(k["m3"] for k in knees), 4),
            status="DRAWING-DERIVED (owner manual method Q-47 A stops the waist at the first / last riser line; shown "
                   "side by side, NOT added to the owner-method ledger, NOT released)"),
        held_unchanged=old["held_unchanged"],
        undetermined=[
            dict(id="COL-1F-36 x MS2-L", exposure_m3=[0.0, round(res["st01"]["column_1F36"]["exposure_drawn_m3"], 6)],
                 why="drawn 0.25 x 0.50 projects 0.05 into the west lane over y 46.148 .. 46.648; the schedule section is "
                     "0.20 x 0.50 (T-119) and its position is not established; columns are billed by no line in A or "
                     "V3.0.4 (BLOCKED_RFI), so the stair keeps it now; owner COLUMN once T-119 lines are wired"),
            dict(id="COL-GF-06 x MS1-L", exposure_m3=None, why="0.25 x 0.50 drawn = scheduled, 0.05 projection; MS1-L HELD"),
            dict(id="E1 head x GB band", exposure_m3=[0.0, round(res["st03"]["steps_in_gb_band_plan_m3"], 6)],
                 why="last riser line 179 (x 94.468) 0.05 inside the 0.30 ground beam band 178 / 7DB; ground-beam lines "
                     "are not billed in A (UNBOUND exposures); top level not printed: stair keeps it until a GB line "
                     "bills through"),
            dict(id="D1 head / MS1-L foot x ST-01 shaft floor", exposure_m3=None,
                 why="the shaft floor at +1.00 / +0.30 (face 11.52 m2 on ST p.3) is in no ground-slab line and prints no "
                     "slab: scope UNKNOWN (lane A / Lead), never 0; the D1 arrival wedge (0.0315) stays in the stair"),
            dict(id="RS-LD / RS-A x hidden pair 2CC / 2CD", exposure_m3=None,
                 why="layer-5 double line 0.10 apart across the corner landing, RS-A and the plate: no mark, no schedule"),
        ],
        system_status="PARTIALLY VERIFIED (owner 16:45); rev3 pieces DRAWING-CONFIRMED until the Checker re-measures",
        released_line_corrections=[
            dict(line=res["released_GF_stair"]["line"], change_m3=round(-res["released_GF_stair"]["base"]["in_band_m3"], 4),
                 range_change_m3=[round(-x, 4) for x in res["released_GF_stair"]["range_correction_m3"]][::-1],
                 why="its east run (MS1-U) is measured to the last riser line 0.20 inside B20, billed in full by "
                     "P-C:BEAMS:GF:BAND0043.2: by its own profile (straight_flight, 12 risers, width 1.15) the part inside "
                     "the band; lane I: deduct in any V3.0.x stair line or replace the line by ledger rev3"),
            dict(line="L-83e4f6fa87db7452e2d2 (ground slab 0.418) vs L-5493f3e0cc5801512838 (E1 0.948)", change_m3=0.0,
                 why="engine E1 run is plumb-cut at the last riser line (x 94.468), 0.25 short of the slab face: no "
                     "double in A; the ledger rev3 E1 carries the slab-owned 0.0020 deduction"),
            dict(line="L-507f96568d2bbe8899dd (ground-slab stair zone, BOUNDED_EXPOSURE) vs L-496d997d755b6367a169 (ST-02)",
                 change_m3=0.0,
                 why="not billed together in A; if the exposure is ever released it must be net of the stair line "
                     "measuring the same 8.37 m2 zone"),
        ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--ledger-out")
    a = ap.parse_args()
    res = run()
    if a.ledger_out:
        Path(a.ledger_out).write_text(json.dumps(ledger_rev3(res), indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1, default=float))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
