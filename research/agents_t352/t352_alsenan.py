"""T-352 development-villa ledger: stair formwork faces the general ledger does not carry (flight sides, landing
edges, junction strips), the existing stair faces of T-163 r3 / T-332 listed by id (never re-added), the overlap
list, and the addendum FILL for T-199.

    python3 -I research/agents_t352/t352_alsenan.py [--write]

Inputs: ALSENAN_T352_INPUT.json (this folder; printed values and lengths by handle, re-read by t352_extract.py) and
research/agents_t332/FORMWORK_T332_BY_FACE.csv (read only). Without --write it checks that the committed outputs
are byte-identical to a fresh build."""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t352_rules import Face, check_faces, fill_rows, flight_profile, profile_strip, totals, write_fill_csv  # noqa: E402

T332_FACES = HERE.parent / "agents_t332" / "FORMWORK_T332_BY_FACE.csv"
OUT_FACES = HERE / "STAIR_FORMWORK_T352_BY_FACE.csv"
OUT_FILL = HERE / "T199_FILL_T352_ADDENDUM.csv"
OUT_EXIST = HERE / "EXISTING_STAIR_FACES_T332.csv"
OUT_SUMMARY = HERE / "summary_t352.json"

DC, AOA = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED"


def load_input():
    return json.loads((HERE / "ALSENAN_T352_INPUT.json").read_text(encoding="utf-8"))


def existing_stair_faces():
    """Every face of the general ledger on a stair element or next to a stair (read only)."""
    rows = []
    with T332_FACES.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["element"] == "STAIR" or "STAIR" in r["item"].upper() or "winders" in r["item"]:
                rows.append(r)
    return rows


def build(inp=None):
    inp = inp or load_input()
    g, t, tl = inp["going"], inp["waist_t"]["value"], inp["landing_t"]["value"]
    rs = {k: v["rise"] / v["count"] for k, v in inp["risers"].items()}
    lid = inp["line_ids_V3_0_24"]
    conc = inp["concrete_t258"]
    faces, xcheck = [], {}

    def side(n, s_a, s_b, riser):
        return profile_strip(rs[riser], g, t, n, s_a, s_b)

    # ---- ST-01 MS1-L (CONFLICT C-ST-4): both readings, head strip beside the GF well-end junction
    rB, nA, nB = rs["ST01-GF"], 10, 12
    profA, profB = flight_profile(rB, g, t, nA), flight_profile(rB, g, t, nB)
    stripA = profile_strip(rB, g, t, nA, (nA - 1) * g - 0.05, (nA - 1) * g)
    stripB = profile_strip(rB, g, t, nB, (nB - 1) * g - 0.05, (nB - 1) * g)
    xcheck["ST01-MS1-L"] = {"A": [profA, conc["ST01-MS1-L"]["lo"] / 1.20], "B": [profB, conc["ST01-MS1-L"]["hi"] / 1.20]}
    L = lid["ST01-GF-PARENT"]
    faces += [
        Face("T352-01", "ST-01", "MS1-L", "FLIGHT_SIDE", "east (well)", "VOID", "CONFLICT", "HELD", L,
             lo=profA - stripA, hi=profB - stripB, source="p.4 256 / 25A well; C-ST-4",
             basis=f"well side FORMED on either reading; A 10 lines {profA:.6f} - head strip {stripA:.6f}, "
                   f"B 12 lines {profB:.6f} - {stripB:.6f}; held with the concrete CONFLICT (never one end)"),
        Face("T352-02", "ST-01", "MS1-L", "JUNCTION_STRIP", "east (well end)", "JUNCTION", "HELD", "HELD", L,
             lo=0.0, hi=max(stripA, stripB), source="p.4 well end / 25E",
             basis="last 0.050 m of the flight beside the 0.100 x 0.050 well end at the turn (MS1-T well strip, HELD)"),
        Face("T352-03", "ST-01", "MS1-L", "FLIGHT_SIDE", "west (shaft wall 284)", "WALL", "HELD", "HELD", L,
             lo=0.0, hi=profB, source="p.4 284 (band 286 beyond, shaft wall blockwork T-173)",
             basis="cast against the block wall or formed: construction sequence not printed"),
    ]
    # ---- ST-01 MS1-U
    f = inp["flights"]["ST01-MS1-U"]
    a = side(f["n_lines"], *f["s_free"], f["riser"])
    xcheck["ST01-MS1-U"] = [a, conc["ST01-MS1-U"]["m3"] / 1.20]
    L = lid["ST01-MS1-U+LD"]
    faces += [
        Face("T352-04", "ST-01", "MS1-U", "FLIGHT_SIDE", "west (well)", "VOID", "CALCULATED", DC, L, m2=a,
             source="p.4 25B .. B20 face 2C6, well 256 / 25A",
             basis="profile s 0 .. 3.100 (riser 4.50 / 27, going 0.300, T 16); head beyond the B20 face is B20's"),
        Face("T352-05", "ST-01", "MS1-U", "FLIGHT_SIDE", "east (lift-shaft wall 296)", "WALL", "HELD", "HELD", L,
             lo=0.0, hi=a, source="p.4 296 (band 292 / 293 beyond; lift walls blockwork, D-43)",
             basis="construction sequence not printed"),
    ]
    for k, (ln, contact, why) in inp["landings"]["ST01-MS1-LD"]["edges"].items():
        faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-01", "MS1-LD", "LANDING_EDGE", k, contact, "HELD", "HELD",
                          L, lo=0.0, hi=ln * tl, source="p.4 " + k.split()[1], basis=f"{ln:.3f} x {tl:.2f}: {why}"))
    # ---- ST-01 MS2-L
    f = inp["flights"]["ST01-MS2-L"]
    r2 = rs["ST01-1F"]
    foot = conc["ST01-MS2-L"]["owned_elsewhere"]["foot below the floor inside B20"] / 1.20
    ts = t * (((g ** 2 + r2 ** 2) ** 0.5) / g)
    foot_geo = ts * 0.15 - (r2 / g) * 0.15 ** 2 / 2.0       # waist below +5.50 over s 0 .. 0.150 (inside B20)
    a = side(f["n_lines"], *f["s_free"], f["riser"]) - foot_geo
    strip = side(f["n_lines"], *f["s_junction"], f["riser"])
    xcheck["ST01-MS2-L"] = [a + strip, conc["ST01-MS2-L"]["m3"] / 1.20, {"foot_geo": foot_geo, "foot_t192": foot}]
    L = lid["ST01-MS2-L"]
    faces += [
        Face(f"T352-{len(faces) + 1:02d}", "ST-01", "MS2-L", "FLIGHT_SIDE", "east (well)", "VOID", "CALCULATED", DC, L,
             m2=a, source="p.5 646 .. 632, well 62D / 62E, 633",
             basis="profile s 0 .. 3.250 less the waist below the floor inside B20 (B20's, T-192); s 0 .. 0.150 faces "
                   "the 1F arrival floor, open above +5.50"),
        Face(f"T352-{len(faces) + 2:02d}", "ST-01", "MS2-L", "JUNCTION_STRIP", "east (well end)", "JUNCTION", "HELD",
             "HELD", L, lo=0.0, hi=strip, source="p.5 633 / 632",
             basis="s 3.250 .. 3.300 beside the 0.100 x 0.050 well end (held in MS2-TR)"),
        Face(f"T352-{len(faces) + 3:02d}", "ST-01", "MS2-L", "FLIGHT_SIDE", "west (shaft wall 5E3, column 691)", "WALL",
             "HELD", "HELD", L, lo=0.0, hi=a + strip, source="p.5 5E3 (band 5C6), column 691 over s 0.95 .. 1.45",
             basis="block wall / column 691 (T-248 D-16 CONFLICT) beside the flight: sequence not printed"),
    ]
    # ---- ST-01 MS2-LD W / E edges
    for key in ("ST01-MS2-LD-W", "ST01-MS2-LD-E"):
        for k, (ln, contact, why) in inp["landings"][key]["edges"].items():
            faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-01", key[5:], "LANDING_EDGE", k, contact, "HELD",
                              "HELD", lid["ST01-MS2-LD"], lo=0.0, hi=ln * tl, source="p.5 " + k.split()[1],
                              basis=f"{ln:.3f} x {tl:.2f}: {why}"))
    # ---- ST-01 MS2-U
    f = inp["flights"]["ST01-MS2-U"]
    a = side(f["n_lines"], *f["s_free"], f["riser"])
    xcheck["ST01-MS2-U"] = [a, conc["ST01-MS2-U"]["m3"] / 1.20]
    L = lid["ST01-MS2-U"]
    faces += [
        Face(f"T352-{len(faces) + 1:02d}", "ST-01", "MS2-U", "FLIGHT_SIDE", "west (well)", "VOID", "CALCULATED", DC, L,
             m2=a, source="p.5 62F .. B23 face 5E1, well 62E",
             basis="profile s 0 .. 3.100 (riser 4.20 / 25); head beyond the B23 face is B23's"),
        Face(f"T352-{len(faces) + 2:02d}", "ST-01", "MS2-U", "FLIGHT_SIDE", "east (lift-shaft wall 5D4)", "WALL",
             "HELD", "HELD", L, lo=0.0, hi=a, source="p.5 5D4 (band 5D0 / 5D1 beyond)",
             basis="construction sequence not printed"),
    ]
    # ---- ST-01b D1 and ST-03 E1: support / waist not printed -> unbounded
    for i, sd in enumerate(inp["ends"]["ST01b-D1"]["sides"]):
        faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-01b", "D1", "FLIGHT_SIDE", sd,
                          "MEMBER" if "beam" in sd else "UNKNOWN", "HELD", "HELD", lid["ST01b-D1-STEPS"],
                          source="p.3 1C3 / 143, 15F", basis=inp["ends"]["ST01b-D1"]["why"]))
    for sd in inp["ends"]["ST03-E1"]["ends"]:
        faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-03", "E1", "FLIGHT_SIDE", sd,
                          "MEMBER" if "beam" in sd else "UNKNOWN", "HELD", "HELD", lid["ST03-E1"],
                          source="p.3 145 / 7CA, 186 / 187", basis=inp["ends"]["ST03-E1"]["why"]))
    # ---- ST-02 RS-S
    f = inp["flights"]["ST02-RS-S"]
    a = side(f["n_lines"], *f["s_free"], f["riser"])
    strip = side(f["n_lines"], *f["s_junction"], f["riser"])
    full = flight_profile(rs["ST02"], g, t, f["n_lines"])
    xcheck["ST02-RS-S"] = [full, conc["ST02-RS-S"]["m3"] / 1.20]
    L = lid["ST02-CLOSABLE"]
    faces += [
        Face(f"T352-{len(faces) + 1:02d}", "ST-02", "RS-S", "FLIGHT_SIDE", "north (light well 2D0)", "VOID",
             "CALCULATED", AOA, L, m2=a, source="p.4 2BA .. 2C4, 2D0",
             basis="profile s 0 .. 2.950 (riser 4.50 / 28 Q-50 A cond, going 0.300, T 16)"),
        Face(f"T352-{len(faces) + 2:02d}", "ST-02", "RS-S", "JUNCTION_STRIP", "north (corner of the RS-A lane)",
             "JUNCTION", "HELD", "HELD", L, lo=0.0, hi=strip, source="p.4 2CF / 2C4",
             basis="s 2.950 .. 3.000 beside the 0.050 strip between 2CF and 2C4 (what fills it is not drawn)"),
        Face(f"T352-{len(faces) + 3:02d}", "ST-02", "RS-S", "FLIGHT_SIDE", "south (B3 'With Stair' band 283, column 380)",
             "MEMBER", "HELD", "HELD", L, lo=0.0, hi=full, source="p.4 283 / 27E, column 380",
             basis="stair beam (Q-61 C HELD) and column 380 (D-16) beside the flight"),
    ]
    # ---- ST-02 RS-LD edges
    for k, (ln, contact, why) in inp["landings"]["ST02-RS-LD"]["edges"].items():
        if contact == "VOID":
            faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-02", "RS-LD", "LANDING_EDGE", k, "VOID", "CALCULATED",
                              DC, L, m2=ln * tl, source="p.4 289, column 374",
                              basis=f"{ln:.3f} x {tl:.2f}: {why}; 0.64 m below the GF-146 slab soffit +5.34"))
        else:
            faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-02", "RS-LD", "LANDING_EDGE", k, contact, "HELD",
                              "HELD", L, lo=0.0, hi=ln * tl, source="p.4 283, column 374",
                              basis=f"{ln:.3f} x {tl:.2f}: {why}"))
    # ---- ST-02 RS-A
    f = inp["flights"]["ST02-RS-A"]
    a = flight_profile(rs["ST02"], g, t, f["n_lines"])
    xcheck["ST02-RS-A"] = [a, conc["ST02-RS-A"]["m3"] / 1.20]
    for sd, src in (("west (light well 2CF)", "p.4 2C8 .. 315, 2CF"), ("east (free edge 289, below slab GF-146)", "p.4 289, GF-146")):
        faces.append(Face(f"T352-{len(faces) + 1:02d}", "ST-02", "RS-A", "FLIGHT_SIDE", sd, "VOID", "CALCULATED", AOA,
                          L, m2=a, source=src, basis="profile s 0 .. 1.200 (riser 4.50 / 28 Q-50 A cond); arrival "
                                                     "triangle beyond 315 is plate C-T1's"))
    existing = existing_stair_faces()
    check_faces(faces, existing_ids=[r["face_id"] for r in existing])
    return faces, existing, xcheck


OVERLAPS = [
    ("OV-1", "R4-321 MS1-U riser forms (12 x 1.20 x 0.166667)", "the 12th riser line 459 lies 0.200 inside the B20 band: "
     "the face from the 11th tread (+5.333) to +5.50 is the B20 stair-side face 2C6, 1.20 x 0.166667 = 0.200000 m2",
     "R4-261.GF-066 (B20 BAND0043.2 side next to STAIR, HELD 0 .. 1.475) and the B20 top band", "no double count today "
     "(the beam faces are HELD); when they close, the 0.200000 m2 is carried once (riser row) and deducted there"),
    ("OV-2", "R4-327 MS2-U riser forms (12 x 1.20 x 0.168)", "arrival line 0.200 inside B23: the top face 1.20 x 0.168 = "
     "0.201600 m2 is the B23 stair-side face 5E1", "R4-285.1F-045 (B23 BAND0031.2 side next to STAIR, HELD 0 .. 1.474594)",
     "as OV-1"),
    ("OV-3", "R4-337.LANE RS-A riser forms (5 x 1.20 x 0.160714)", "the 5th riser at 315 rises into plate C-T1: 1.20 x "
     "0.160714 = 0.192857 m2 is the plate edge", "none valued (the stair-strip faces GF-131 / GF-132 run past 315; no "
     "slab-edge face at 315)", "listed only"),
    ("OV-4", "R4-261.GF-066 B20 stair-side face (HELD 0 .. 1.475)", "MS1-U's head bears on it from its soffit at the face "
     "(+5.039) to the slab soffit (+5.34): 1.20 x 0.300811 = 0.360973 m2 is cast against the flight, not formed",
     "this ledger's T352-04 stops at the face (no overlap)", "the held bound 1.475 overstates the formed part by up to "
     "0.360973 m2"),
    ("OV-5", "R4-285.1F-045 B23 stair-side face (HELD 0 .. 1.474594)", "MS2-U's head: soffit at the face +9.2366 to the "
     "2F slab soffit (T 16: +9.54): 1.20 x 0.303380 = 0.364056 m2 cast against the flight", "T352 MS2-U side stops at the "
     "face", "as OV-4"),
    ("OV-6", "R4-263.GF-146 slab edge at 289 next to STAIR (HELD 0 .. 0.375993)", "the slab wedge GF-146 (+5.34 .. +5.50) "
     "is ABOVE the round stair: RS-LD tops at +4.696, RS-A's stair-owned profile at +5.3393; its edge face is free",
     "T352 RS-LD east edge and RS-A east side lie below it (no shared area)", "finding F-T352-2: the face is formed "
     "(0.375993 m2 = 2.35 x 0.16), not a stair junction"),
    ("OV-7", "R4-339 'flight and landing side faces (stringer profiles)' aggregate, HELD, NAMED_NOT_TIED", "split by this "
     "ledger into one row per flight side / landing edge", "every T352 FLIGHT_SIDE / LANDING_EDGE row", "SUPERSEDED: "
     "T-199 takes the T352 rows and drops R4-339, never both"),
    ("OV-8", "R4-319 MS1-T turn faces (HELD, unbounded)", "carries every turn face (winder risers, turn sides, well-end "
     "face); drawn riser lines 2F6 1.2587 + 2F4 1.6263 + 2F5 1.2587 + 2F3 1.150 = 5.2937 m x 4.50 / 27 = 0.882283 m2 "
     "is information only (4 lines vs 5 risers on A-A, C-ST-4)", "no T352 row on the turn", "kept HELD there"),
    ("OV-9", "R4-316 slab under the MS1-T winders (HELD 1.440 .. 1.562)", "the bound is the T-111 plan-projection range; "
     "the turn plan is now drawn 1.30 x 1.15 = 1.495 m2 (T-281) and a warped soffit is never smaller than its plan",
     "no T352 row", "finding F-T352-1: lo 1.440 < 1.495 understates; hi not established for a warped surface"),
]


def faces_csv(faces):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["face_id", "stair", "piece", "kind", "side", "contact", "status", "evidence", "line_id", "m2", "lo",
                "hi", "source", "basis", "rule"])
    f6 = lambda v: "" if v is None else f"{v:.6f}"
    for f in faces:
        w.writerow([f.face_id, f.stair, f.piece, f.kind, f.side, f.contact, f.status, f.evidence, f.line_id or "",
                    f6(f.m2), f6(f.lo), f6(f.hi), f.source, f.basis, "STAIR_FORMWORK_T352_V1"])
    return buf.getvalue()


def existing_csv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["face_id", "item", "status", "m2", "lo", "hi", "held_from", "line_id", "t352_treatment"])
    for r in rows:
        fid = r["face_id"]
        treat = "CARRIED (T-332 value, not re-added)"
        if fid == "R4-339":
            treat = "SUPERSEDED by the T352 flight-side / landing-edge rows (OV-7)"
        elif fid == "R4-319":
            treat = "KEPT HELD (turn faces; OV-8 information only)"
        elif fid == "R4-316":
            treat = "KEPT HELD; finding F-T352-1 on its bound (OV-9)"
        elif fid in ("R4-321", "R4-327", "R4-337.LANE"):
            treat = "CARRIED; overlap listed (OV-1 / OV-2 / OV-3)"
        elif fid in ("R4-261.GF-066~BM-GF-043#BAND0043.2.BEAM_SIDE_HELD_M2",):
            treat = "KEPT HELD; contact with the MS1-U head (OV-1 / OV-4)"
        elif fid.startswith("R4-285.1F-045~BM"):
            treat = "KEPT HELD; contact with the MS2-U head (OV-2 / OV-5)"
        elif fid.startswith("R4-263.GF-146"):
            treat = "KEPT HELD; finding F-T352-2 (OV-6)"
        elif "next to STAIR" in r["item"]:
            treat = "KEPT HELD (member face next to a stair; not a stair face)"
        w.writerow([fid, r["item"], r["status"], r["m2"], r["lo"], r["hi"], r["held_from"], r["line_id"], treat])
    return buf.getvalue()


def summary(faces, existing, xcheck):
    tot = totals(faces)
    ex_calc = sum(float(r["m2"]) for r in existing if r["status"] == "CALCULATED" and r["m2"])
    ex_stair_calc = sum(float(r["m2"]) for r in existing if r["status"] == "CALCULATED" and r["m2"] and r["element"] == "STAIR")
    return {
        "rule": "STAIR_FORMWORK_T352_V1",
        "new_faces": len(faces),
        "new": {k: round(v, 6) if isinstance(v, float) else v for k, v in tot.items()},
        "existing_stair_faces_t332": len(existing),
        "existing_stair_element_calculated_m2": round(ex_stair_calc, 6),
        "existing_all_listed_calculated_m2": round(ex_calc, 6),
        "stair_family_calculated_after_m2": round(ex_stair_calc + tot["calculated_m2"], 6),
        "cross_check_side_vs_t258_net_over_width": {k: v for k, v in xcheck.items()},
        "overlaps": [o[0] for o in OVERLAPS],
        "double_count": 0,
    }


def outputs():
    faces, existing, xcheck = build()
    fill = write_fill_csv(fill_rows(faces))
    summ = json.dumps(summary(faces, existing, xcheck), indent=1, ensure_ascii=False, default=float) + "\n"
    return {OUT_FACES: faces_csv(faces), OUT_FILL: fill, OUT_EXIST: existing_csv(existing), OUT_SUMMARY: summ}


def main(argv):
    outs = outputs()
    if "--write" in argv:
        for p, s in outs.items():
            p.write_text(s, encoding="utf-8")
        print("written", ", ".join(p.name for p in outs))
        return 0
    bad = [p.name for p, s in outs.items() if not p.exists() or p.read_text(encoding="utf-8") != s]
    print("byte-identical" if not bad else f"DIFFERS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
