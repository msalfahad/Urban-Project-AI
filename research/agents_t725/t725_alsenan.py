"""T-725 development-villa build (research, unwired): the 20 HELD STR.FORMWORK.STAIR lines of the candidate of record
ARCH_TAKEOFF_V3.0.72 (line index of T-703) given, under R-T725-1..3 (t725_rules.py) and R-T714-1, the bound their
drawn stair geometry and merged stair concrete now carry, or kept HELD BLANK with the live cause named.

Reads only merged repository files (sha256-pinned in PINS.json) plus the drawing facts below, re-read this run from
Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179..., decoded by the wrapper into .work/private only),
by handle, as relative lengths (no coordinates, no drawing content). Writes out/T725_LEDGER.json and out/T725_CENSUS.md.
No candidate, released (V2.9 + route G), rule / knowledge version or registry file is touched; nothing is wired,
released or VERIFIED.

    python3 -I research/agents_t725/t725_alsenan.py [--write | --check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t725_rules as R  # noqa: E402

SCHEMA = "URBAN_T725_STAIR_FORMWORK_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.72"
INDEX = "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
T474 = "research/agents_t474/out/FORMWORK_LINE_MAP_T474.csv"
T352 = "research/agents_t352/STAIR_FORMWORK_T352_BY_FACE.csv"
T332 = "research/agents_t352/EXISTING_STAIR_FACES_T332.csv"
T281 = "research/agents_t281/LEDGER_T281.csv"
T711 = "research/agents_t711/out/T711_LEDGER.json"
T248 = "research/agents_t248/LEDGER_T248.csv"
INPUTS = (INDEX, T474, T352, T332, T281, T711, T248)
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T725_LEDGER.json"
OUT_MD = HERE / "out" / "T725_CENSUS.md"
ITEM = "STR.FORMWORK.STAIR"

# ---- drawing facts, own read this run ('ST7757 dxf.dxf' 9f9d1179), relative lengths in m, by handle
DRAWN = {
    "dxf_sha256_16": "9f9d1179a5d2a663",
    "g": 0.300,                      # going (riser-line spacing, every flight; E1 18A..179 perpendicular 0.300 each)
    "t": 0.16,                       # PRINTED 'T 16' (Q-47 A)
    "lane": 1.200,                   # p.4 284 -> 256 1.200 (MS1-L structural lane; riser lines 45A / 25E drawn 1.150)
    "ms1l_run_B": 3.300,             # p.4 45A -> 25E (12 lines, B)
    "ms1l_A_offset": 0.600,          # A: 10 lines from 0.600 later to 25E (C-ST-4, T-258 / T-281)
    "ms1l_col36B_m2": 0.025,         # column 36B in the lane: no soffit (T-281)
    "turn_region": (1.300, 1.150),   # p.4 284 -> 2F3 1.300 x 25E -> 279 1.150 (T-281 MS1-T, plan 1.495)
    "winder_lines_B": {"2F6": 1.2587, "2F4": 1.6263, "2F5": 1.2587, "2F3": 1.1500},
    "e1_riser_lines": {"18A": 2.800, "189": 2.800, "188": 2.800, "17A": 2.800, "179": 2.800},
    "e1_179_in_gb_band": 0.050,      # 179 lies 0.050 beyond the band face 178 (band 178 / 7DB 0.300)
    "e1_levels": (0.15, 1.00),       # RFI-S26 / T-258 (+0.15 -> +1.00, 5 risers, section B-B)
    "ms2tr_step_5E2": 1.150,         # p.5 step line 5E2 between the half landings
    "ms2l_5E2_to_632": 0.150,
}
STOREY = {"GF-1F": 4.50, "1F-2F": 4.20}
READ_A = R.Reading("A", STOREY["GF-1F"], (("MS1-L", 10), ("MS1-T", 5), ("MS1-U", 12)),
                   "section A-A + architectural GF plan (Q-46 A)", "section A-A 27", total_declared=27)
READ_B = R.Reading("B", STOREY["GF-1F"], (("MS1-L", 12), ("MS1-T", 4), ("MS1-U", 12)),
                   "structural p.4: 12 straight + 2F6 / 2F4 / 2F5 + closing 2F3 + 12", "the same plan's count 28",
                   total_declared=28)
READ_1F = R.Reading("1F", STOREY["1F-2F"], (("MS2-L", 12), ("MS2-TR", 1), ("MS2-U", 12)),
                    "section A-A 12 + turn riser + 12", "section A-A 25", total_declared=25)

LIVE_ITEMS = {"SEQ", "D-16", "F-T281-03", "RFI-A07", "RFI-S24", "RFI-S25", "RFI-S26", "RFI-S27", "RFI-A03", "RFI-A04",
              "C-ST-3", "C-ST-4", "D-08", "D-67", "Q-50", "Q-51", "GB-LEVEL"}
REMOVED_ITEMS = {"D-56", "D-68"}
CAUSES = {
    "SEQ": "contact with a block wall / member whose construction sequence is not printed (formed, or cast against "
           "it): contractor's sequence, not a designer dimension (T-352 s.1, ST p.8 notes 17 / 19 / 23)",
    "D-16": "column section CONFLICT (outline vs schedule, T-248): which side the schedule section loses is not "
            "printed, so the lane strip is column or soffit",
    "F-T281-03": "unmarked layer-5 pair under the soffit (member not identified): a wall below (bears, 0), a "
                 "downstand (its own soffit) or nothing (stair soffit)",
    "RFI-S26": "E1 / D1 waist or support not printed (steps on fill or self-supporting waist; section B-B draws E1 on "
               "fill); designer item 7",
    "RFI-S27": "RS-C curved part: rise (Q-50 A cond holds curved parts), helicoid soffit and thickness not printed "
               "(D-08); designer item 7",
    "RFI-S25": "MS2-TR junction between the plates 0.168 apart: thickness / depth not drawn (C-ST-3); designer item 7",
}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if set(pins) != set(INPUTS):
        raise R.Refused(f"pin set differs: {sorted(set(pins) ^ set(INPUTS))}")
    bad = {p: (sha16(p), v) for p, v in pins.items() if sha16(p) != v}
    if bad:
        raise R.Refused(f"input drift (sha256[:16] now, pinned): {bad}")
    return pins


def _csv(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load():
    pins = check_pins()
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    if idx["candidate_version"] != CANDIDATE:
        raise R.Refused("line index is not the candidate of record")
    held = {x["line_id"]: x for x in idx["lines"] if x["item_code"] == ITEM and x["class"] == "HELD"}
    fmap = {r["line_id"]: r for r in _csv(T474) if r["item_code"] == ITEM}
    t352 = {r["face_id"]: r for r in _csv(T352)}
    t332 = {r["face_id"]: r for r in _csv(T332)}
    t281 = {r["id"]: r for r in _csv(T281)}
    t711 = {r["line_id"]: r for r in json.loads((ROOT / T711).read_text(encoding="utf-8"))["lines"]}
    t248 = {r["member"]: r for r in _csv(T248)}
    for lid, x in held.items():
        if fmap[lid]["element_id"] != x["element_id"]:
            raise R.Refused(f"{lid}: element id drift between V3.0.72 and the T-474 face map")
        if x["measured_net"] is not None or x["held_low"] is not None or x["held_high"] is not None:
            raise R.Refused(f"{lid}: not a blank HELD line on V3.0.72")
    return pins, idx, held, fmap, t352, t332, t281, t711, t248


def F(fid, kind, lo, hi, basis, contact="FORMED"):
    return R.Face(fid, kind, lo, hi, basis, contact)


def cap(fid, kind, hi, basis):
    return R.Face(fid, kind, 0.0, hi, basis, "CAP_ONLY")


def block(fid, kind, basis):
    return R.Face(fid, kind, None, None, basis, "BLOCK")


def f352(t352, fid, *, hi_override=None):
    r = t352[fid]
    hi = hi_override if hi_override is not None else (float(r["hi"]) if r["hi"] else None)
    if r["status"] in ("CALCULATED",):
        raise R.Refused(f"{fid} is a released face, not a held one")
    if hi is None:
        return block(fid, r["kind"], r["basis"])
    return cap(fid, r["kind"], hi, f"{r['contact']}: {r['basis']}")


def build():
    pins, idx, held, fmap, t352, t332, t281, t711, t248 = load()
    g, t, w = DRAWN["g"], DRAWN["t"], DRAWN["lane"]
    rA, rB, r1F = READ_A.rise, READ_B.rise, READ_1F.rise
    lines = {}

    def put(lid, faces_by_reading, cause_key=None, cited=(), note="", host=None):
        res = R.class_line(lid, faces_by_reading, cause=CAUSES.get(cause_key, cause_key) if cause_key else None,
                           live_items=LIVE_ITEMS, removed_items=REMOVED_ITEMS, cited=cited)
        faces = {rd: [vars(f) for f in fs] for rd, fs in faces_by_reading.items()}
        lines[lid] = {
            "line_id": lid, "element_id": held[lid]["element_id"], "face_ids_t474": fmap[lid]["face_ids"].split(),
            "host_concrete": fmap[lid]["concrete_line"] or None, "host_state": host,
            "class_after": res.cls, "low": str(res.low) if res.low is not None else None,
            "high": str(res.high) if res.high is not None else None, "cap": str(res.cap) if res.cap is not None else None,
            "readings": {k: [None if v[0] is None else round(v[0], 6), None if v[1] is None else round(v[1], 6)]
                         for k, v in res.readings.items()},
            "cause": res.cause, "cited": list(cited), "faces": faces, "note": note,
        }

    # ------------------------------------------------------------ MS1-L profiles (R-T725-1 coherent readings)
    nA, nB = READ_A.n("MS1-L"), READ_B.n("MS1-L")
    prof = {}
    for rd, n, r in (("A", nA, rA), ("B", nB, rB)):
        e = (n - 1) * g
        for m, clip in (("O", False), ("D", True)):
            whole = R.side_profile(r, g, t, n, 0.0, e, clip_floor=clip)
            strip = R.side_profile(r, g, t, n, e - 0.05, e, clip_floor=False)
            prof[rd + m] = (whole, strip)
    # T-352 reading B as recorded (12 lines at the section's 4.50 / 27): refused by R-T725-1, shown for the finding
    try:
        R.Reading("B-as-recorded", 4.50, (("MS1-L", 12), ("MS1-T", 4), ("MS1-U", 12)), "structural p.4",
                  "section A-A 27", total_declared=27)
        raise AssertionError("an incoherent reading must be refused")
    except R.Refused as exc:
        refused_b = str(exc)
    b_rec = R.side_profile(rA, g, t, 12, 0.0, 3.3, clip_floor=False)
    b_rec_strip = R.side_profile(rA, g, t, 12, 3.25, 3.3, clip_floor=False)

    # 1. L-9c3643da MS1-L east (well) side, T352-01: FORMED on every reading; O / D side by side
    lid = "L-9c3643da524267bf47f6"
    put(lid, {rd: [F("T352-01", "FLIGHT_SIDE", prof[rd][0] - prof[rd][1], prof[rd][0] - prof[rd][1],
                     f"well side {rd[0]} method {rd[1]}: profile {prof[rd][0]:.6f} - head strip {prof[rd][1]:.6f}")]
              for rd in ("AO", "AD", "BO", "BD")},
        note="T-352 range 0.709344 .. 0.869164 restated: low = reading A method D (foot clipped at the GF floor top), "
             "high = coherent reading B (4.50 / 28) method O; T-352's high used 4.50 / 27 with 12 lines (F-T725-1)",
        host="AT_LEAST 1.213429 m3 (T-711, reading A)")

    # 2. L-d9790e45 MS1-L west wall + well-end junction (T352-02 / -03): CAP_ONLY, caps recomputed on coherent readings
    lid = "L-d9790e457fd530487553"
    put(lid, {rd: [cap("T352-02", "JUNCTION_STRIP", prof[rd + "O"][1], "well end at the turn (MS1-T strip, HELD)"),
                   cap("T352-03", "FLIGHT_SIDE", prof[rd + "O"][0], "shaft wall 284, sequence not printed")]
              for rd in ("A", "B")}, "SEQ", cited=("SEQ",), host="AT_LEAST 1.213429 m3 (T-711)",
        note="cap = coherent reading B method O (T-352 cap 0.888856 used 4.50 / 27, F-T725-1)")

    # 3. L-ffd491ad MS1-L risers + soffit + turn (R4-316 .. R4-319)
    lid = "L-ffd491ad529ee2251982"
    ms1l = t281["ST01-MS1-L"]
    turn_plan = DRAWN["turn_region"][0] * DRAWN["turn_region"][1]
    if abs(turn_plan - float(t281["ST01-MS1-T"]["plan_O"])) > 1e-9:
        raise R.Refused("turn region plan differs from T-281")
    fbr = {}
    for rd, rdg in (("A", READ_A), ("B", READ_B)):
        r = rdg.rise
        run = DRAWN["ms1l_run_B"] - (DRAWN["ms1l_A_offset"] if rd == "A" else 0.0)
        plan = run * w - DRAWN["ms1l_col36B_m2"]
        risers = R.riser_forms([w] * rdg.n("MS1-L"), r, drawn=True)
        if rd == "A":
            winders = R.winder_floor(rdg.n("MS1-T"), min(DRAWN["turn_region"]), r, region_drawn=True)
            wb = f"5 fronts not drawn (D-67), each >= the drawn region's narrow side 1.150 (R-T718-2) x {r:.6f}"
        else:
            winders = R.riser_forms(DRAWN["winder_lines_B"].values(), r, drawn=True)
            wb = f"drawn 2F6 / 2F4 / 2F5 / 2F3 = {sum(DRAWN['winder_lines_B'].values()):.4f} m x {r:.6f}"
        for m in ("O", "D"):
            soff = R.soffit_true(plan, r, g) if m == "O" else R.soffit_d(plan, w, r, g, t, foot_on_slab=True)
            fbr[rd + m] = [
                F("R4-317", "RISER", risers, risers, f"{rdg.n('MS1-L')} x {w} x {r:.6f}"),
                F("R4-318", "SOFFIT", soff, soff, f"method {m}, plan {plan:.6f} (run {run:.3f} x {w} - col 36B)"),
                F("R4-316", "SOFFIT", R.warped_floor(turn_plan, region_drawn=True), None,
                  "warped winder soffit not drawn (C-ST-3): floor = drawn region 1.300 x 1.150"),
                F("R4-319.RISERS", "RISER", winders, None, wb),
                cap("R4-319.SIDES", "SIDE", None, "turn sides on walls 284 / north: sequence not printed, open"),
            ]
    # the T-281 record's reading A must equal the primitives here (cross-check, 1e-6)
    a_rec = [float(x) for x in ms1l["held"].split("true O ")[1].split(",")[0].split(" .. ")]
    if abs(a_rec[0] - fbr["AO"][1].lo) > 1e-6:
        raise R.Refused("MS1-L reading A soffit differs from T-281")
    put(lid, fbr, host="AT_LEAST 1.213429 m3 (T-711)",
        note="T-332 held_from 5.706 (2.000 + 3.706) restated: risers at both readings, soffit by T-281 methods O / D, "
             "turn soffit floor 1.495 (F-T352-1), winder risers floor; high open (warped soffit, turn sides)")

    # 4-8. CAP_ONLY sides / edges of released or bounded hosts (T-352, sequence not printed)
    for lid, fids, host in (
            ("L-39d830b14a64c52bc7ec", ("T352-05", "T352-06", "T352-07"), "RELEASED 1.227952 m3 (MS1-LD + MS1-U)"),
            ("L-4c0e72c44c32c35b1f37", ("T352-09", "T352-10"), "RELEASED 1.033445 m3 (MS2-L)"),
            ("L-57fc16524398c58c45cd", ("T352-16",), "RELEASED 1.001373 m3 (MS2-U)"),
            ("L-7db84872f4e871c558b8", ("T352-22", "T352-23", "T352-25"), "RELEASED 1.536225 m3 (RS-S / RS-LD / RS-A)"),
            ("L-f93c7248b948b757aefb", ("T352-11", "T352-12", "T352-13", "T352-14"), "RELEASED 0.4696 m3 (MS2-LD)")):
        put(lid, {"one": [f352(t352, f) for f in fids]}, "SEQ", cited=("SEQ",), host=host,
            note="every face beside a block wall, a 'B3 (With Stair)' band, a column or a held junction; a "
                 "member-member interface is formed at most once (its cap is shared with the member's own "
                 "'next to STAIR' face, R-T725-2 (e))")

    # 9-10. column-exposure soffit strips (D-16)
    for lid, fid, row, col in (("L-1b5c40deb5c9a27da420", "R4-335.COL380", "ST02-RS-S/column 380 exposure", "GFRS:380"),
                               ("L-24da5c2af3a315778442", "R4-324.COL691", "ST01-MS2-L/column 691 exposure", "FFRS:691")):
        c = t248[col]
        if c["section_class"] != "CONFLICT":
            raise R.Refused(f"{col} is no longer a section CONFLICT")
        r = 4.50 / 28 if "380" in col else r1F
        hi = float(t281[row]["plan_O"]) * R.sec(r, g)
        put(lid, {"one": [cap(fid, "SOFFIT", hi, f"lane strip {t281[row]['plan_O']} m2 plan x sec; column "
                                                 f"{c['mark']} a {c['a_lo']} .. {c['a_hi']} m2")]},
            "D-16", cited=("D-16",), host="RELEASED (host flight)",
            note="drawn outline: the strip is column (0); schedule section: soffit only if the lost side is the lane side")

    # 11-14. untied hidden-pair soffit strips (F-T281-03)
    for lid, fid in (("L-7380736269ecfe6ce8a6", "R4-338.HIDDEN_2CC_2CD"), ("L-c7b17d201affddad4ed5", "R4-335.HIDDEN_535_536"),
                     ("L-cd188fe35575602f2ac7", "R4-336.HIDDEN_535_536"), ("L-cf06e7fa27a540eedd0f", "R4-336.HIDDEN_2CC_2CD")):
        hi = float(t332[fid]["held_from"])
        put(lid, {"one": [cap(fid, "SOFFIT", hi, t332[fid]["item"])]}, "F-T281-03", cited=("F-T281-03", "RFI-A07"),
            host="no host line (member not identified)",
            note="0 only if the pair is a wall the stair bears on (space under ST-02, RFI-A07); otherwise formed by "
                 "the stair or the downstand: the cap stays beside, never a floor")

    # 15. L-77ecb282 E1 riser forms (R4-329): drawn risers 1-4 stand; riser 5 inside the ground-beam band
    lid = "L-77ecb282cecee46e23f3"
    lo_lv, hi_lv = DRAWN["e1_levels"]
    e1 = R.Reading("E1", hi_lv - lo_lv, (("E1", len(DRAWN["e1_riser_lines"])),), "section B-B / ST p.3 5 lines",
                   "levels +0.15 / +1.00", total_declared=5)
    ws = list(DRAWN["e1_riser_lines"].values())
    four = R.riser_forms(ws[:4], e1.rise, drawn=True)
    fifth = ws[4] * e1.rise
    put(lid, {"one": [F("R4-329.1-4", "RISER", four, four, f"18A / 189 / 188 / 17A 4 x 2.800 x {e1.rise:.3f}"),
                      cap("R4-329.5", "RISER", fifth, "179 lies 0.050 inside the ground-beam band 178 / 7DB: the face "
                          "above tread 4 is the stair's or the ground beam's side (GB top level not printed, T-242 / "
                          "T-253); formed once, owner open")]},
        cited=("RFI-S26", "GB-LEVEL"), host="AT_LEAST 0.355017 m3 (T-711; waist RFI-S26)",
        note="riser faces do not contain the held waist (R-T714-1 INDEPENDENT); D-56 is removed from the package "
             "(drawn 5 x 0.170 kept): cited RFI-S26 / designer item 7 instead")

    # 16. L-739ee9fe MS2-TR (R4-325): the exposed turn riser at 5E2 stands; the junction below stays open
    lid = "L-739ee9feb2a4c3aa6fa7"
    tr = R.riser_forms([DRAWN["ms2tr_step_5E2"]], r1F, drawn=True)
    put(lid, {"one": [F("R4-325.RISER", "RISER", tr, tr, f"5E2 1.150 x {r1F:.3f} (25 risers, the turn riser is in "
                                                          "neither 12-riser flight row)"),
                      R.Face("R4-325.JUNCTION", "SOFFIT", 0.0, None, "junction soffit step + well end 0.100 x 0.050: "
                             "build-up not drawn (C-ST-3)", "FORMED")]},
        "RFI-S25", cited=("RFI-S25", "C-ST-3"), host="BLANK (T-711, C-ST-3)",
        note="the face between the lower plate top +7.516 and the upper top +7.684 is exposed whatever the junction "
             "member is; MS2-LD-E's edge along 5E2 is in no T-352 edge row (no double count)")

    # 17-20. blanks with no figure
    put("L-997777b321ab95220878", {"one": [block("R4-333", "SIDE", "RS-C curved faces")]}, "RFI-S27",
        cited=("RFI-S27", "D-08", "Q-50", "Q-51"), host="BLANK (T-711)",
        note="information only (not valued): 12 drawn riser faces 13.798024 lm (T-718) per m of rise")
    put("L-caa721ed972e7905d5e6", {"one": [f352(t352, "T352-19"), f352(t352, "T352-20")]}, "RFI-S26",
        cited=("RFI-S26",), host="AT_LEAST 0.355017 m3 (T-711)",
        note="D-56 (removed) restated: the ends' profile below the steps is the unprinted waist / support")
    put("L-e01bb929444556887537", {"one": [f352(t352, "T352-17"), f352(t352, "T352-18")]}, "RFI-S26",
        cited=("RFI-S26",), host="RELEASED 0.100286 m3 (D1 steps)")
    put("L-f19a44ba871f6020d965", {"one": [block("R4-332", "SOFFIT", "D1 waist soffit")]}, "RFI-S26",
        cited=("RFI-S26",), host="BLANK (D1 waist)",
        note="steps on fill (no soffit form) or a waist over a void: not printed")

    missing = set(held) - set(lines)
    extra = set(lines) - set(held)
    if missing or extra or len(lines) != 20:
        raise R.Refused(f"census: missing {sorted(missing)}, extra {sorted(extra)}")

    findings = {
        "F-T725-1": {
            "what": "MS1-L reading B (structural 12 + 4 + 12 = 28 risers) carried at the section's rise 4.50 / 27 in "
                    "T-258 / T-281 / T-352 (and T-711's MS1-L part); coherent B uses 4.50 / 28 (R-T725-1)",
            "refused": refused_b,
            "effect_highs_only": {
                "T352-01 hi": [round(b_rec - b_rec_strip, 6), round(prof["BO"][0] - prof["BO"][1], 6)],
                "T352-03 cap": [round(b_rec, 6), round(prof["BO"][0], 6)],
                "MS1-L concrete hi m3 (side x 1.20)": [round(b_rec * 1.2, 6), round(prof["BO"][0] * 1.2, 6)],
                "MS1-L soffit true O hi": [round(3.935 * R.sec(rA, g), 6), round(3.935 * R.sec(rB, g), 6)],
                "MS1-L soffit true D hi": [round(R.soffit_d(3.935, w, rA, g, t, foot_on_slab=True), 6),
                                           round(R.soffit_d(3.935, w, rB, g, t, foot_on_slab=True), 6)],
            },
            "floors_moved": 0,
        },
        "F-T725-2": "Lead ruling 2026-11-12 moves the 3 D-56 lines to D-67 / D-68: D-67 is the GF winder turn and D-68 "
                    "is WITHDRAWN; neither describes E1. The live item holding E1 is RFI-S26 (designer item 7); the "
                    "riser line is no longer held by any designer dimension except the ground-beam top level",
        "F-T725-3": "T-718 bounds the RS-C marble risers with 4.50 / 28 on the curved part, which Q-50 A cond holds "
                    "('curved parts HELD') and T-711 keeps blank; the RS-C formwork line stays blank here",
    }
    census = {}
    for x in lines.values():
        census[x["class_after"]] = census.get(x["class_after"], 0) + 1
    tot_lo = sum(float(x["low"]) for x in lines.values() if x["low"])
    out = {
        "schema": SCHEMA, "task": "T-725", "candidate": CANDIDATE, "rules": R.RULES, "inputs": pins, "drawn": DRAWN,
        "readings": {k: {"total": v.total, "rise": round(v.rise, 9), "pieces": v.pieces}
                     for k, v in (("A", READ_A), ("B", READ_B), ("1F", READ_1F))},
        "census": census, "sum_of_lows_m2_beside": round(tot_lo, 6), "findings": findings,
        "lines": [lines[k] for k in sorted(lines)],
    }
    return out


def census_md(out):
    L = [f"# T-725 census: {ITEM} HELD lines on {out['candidate']} (research, unwired)", "",
         f"Census: {out['census']} (20 / 20 by id). Sum of lows beside, never summed into the released total: "
         f"{out['sum_of_lows_m2_beside']:.6f} m2.", "",
         "| line | faces (T-474) | host | class after | low | high | cap | cause / cited |", "|---|---|---|---|---|---|---|---|"]
    for x in out["lines"]:
        L.append(f"| {x['line_id']} | {' '.join(x['face_ids_t474'])} | {x['host_state']} | {x['class_after']} | "
                 f"{x['low'] or ''} | {x['high'] or ''} | {x['cap'] or ''} | {', '.join(x['cited'])} |")
    return "\n".join(L) + "\n"


def main(argv):
    out = build()
    js = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    md = census_md(out)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if OUT_JSON.read_text(encoding="utf-8") != js or OUT_MD.read_text(encoding="utf-8") != md:
            print("T725 outputs differ from a fresh build")
            return 1
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
