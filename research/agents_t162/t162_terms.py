"""T-162 the freelancer's exterior Sigma / exterior plaster, term by term against the T-159 facade faces, and his 13
opening rows against the T-150 opening census (development villa; research only, not a method, not wired).

    python3 -I research/agents_t162/t162_terms.py <FACADE_SIDES_T159.csv> [--out <dir>]

Inputs: the freelancer's rows as already recorded in the repository (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json,
file PLS: sheet rows 29-41 / 51-97 and the invoice sheet rows 24-26, quantities only) and T-159's side table
(research/agents_t159/FACADE_SIDES_T159.csv on agents/task-T-159, READY f35bafb). Writes TERMS_T162.csv and
OPENINGS_T162.csv. Lengths, heights, areas and opening ids only: no names.

Mapping rule: each freelancer term is mapped to the T-159 faces it covers, matched by orientation, length and printed
height; the difference keeps its cause (plinth, set-back faces merged into one plane, porch faces, lengths); a term
that matches no face within the drawing's printed figures is UNRESOLVED, never forced. Two areas are given for the
drawing: GEOMETRIC (ground to top, T-159) and Q-07 (bands from the floor level: the plinth bands left out)."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"

# term -> faces: [(floor, side, {portion: length or "ALL"})]; status; cause
TERMS = [
    # SW (his 'west-south' group, rows 51-55: 275.16)
    ("SW", 51, [("GF", "SW-9", {"EDGE": 1.5})], "MAPPED",
     "GF SW-9 roof-edge part 1.50 m to the +6.00 parapet; he takes 6.00 from +-0.00, the drawing +0.15 -> +6.00"),
    ("SW", 52, [("GF", "SW-7", {"FLUSH": 6.77}), ("1F", "SW-3", {"STOREY": 6.77, "PARAPET": 6.77})], "MAPPED",
     "the 6.77 m of the SW face beside the 2F tower, GF + 1F to the +11.00 parapet ('130' sheet 07); his 10.00 = "
     "+1.00 -> +11.00 (no plinth), 6.90 against 6.77 m"),
    ("SW", 53, [("GF", "SW-7", {"FLUSH": 8.10}), ("1F", "SW-3", {"STOREY": 8.10}), ("2F", "SW-1", {"ALL": "ALL"})],
     "MAPPED", "the 8.10 m full-height face under the 2F tower; his 14.40 from +-0.00 over 7.90 m, the drawing +0.15 "
               "-> +14.40 over 8.10 m"),
    ("SW", 54, [("GF", "SW-1", {"ALL": "ALL"}), ("GF", "SW-2", {"ALL": "ALL"}), ("GF", "NW-1", {"ALL": "ALL"})],
     "MAPPED_AS_GROUP",
     "annex faces round the diwaniya corner (SW-1 3.10, arc SW-2 2.042, jog NW-1 0.50 = 5.642 m); his 4.00 m at 5.25 m: "
     "no 5.25 level is printed (sheet 07 '480'). Rows 54 + 55 + 60 = 18.50 m of annex faces against the drawing's "
     "18.742 m: the annex is all there, split between his SW and SE groups differently"),
    ("SW", 55, [("GF", "SW-3", {"ALL": "ALL"})], "MAPPED_AS_GROUP",
     "annex SW face at the court (6.40 m) to +4.80; his 13.00 m: see row 54 (group 54 + 55 + 60)"),
    # SE (rows 58-61: 191.54, of which frame 24.93)
    ("SE", 58, [("2F", "SE-1", {"ALL": "ALL"}), ("1F", "SE-2", {"ALL": "ALL"}), ("GF", "SE-4", {"ALL": "ALL"})],
     "PARTIAL", "street face of the stair tower: only 4.50 m runs flush from the ground to +14.40 (GF SE-4, 1F SE-2, 2F); "
                "2.30 m of the 2F face stands on the 1F roof (+9.70) over the porch; his one plane 14.40 x 6.75"),
    ("SE", 59, [("1F", "SE-1", {"ALL": "ALL"})], "PARTIAL",
     "1F street face 7.50 m: 3.40 m from the annex roof +4.30, 4.10 m from +5.50 over the porch court, wave top +11.30 "
     "(printed '6800' + '200') to +10.085; his 5.25 m x 11.85 m: neither printed"),
    ("SE", 60, [("GF", "SE-1", {"ALL": "ALL"})], "MAPPED_AS_GROUP",
     "annex street face 6.70 m, +-0.00 -> +4.80 (W11 / W12 in it); his 1.50 m: see row 54 (group 54 + 55 + 60)"),
    ("SE", 61, [], "NOT_IN_T159", "frame bands 2 x 0.45 x 27.70: T-159 measures wall faces only; frames not measured"),
    # NE (rows 63-65: 258.00)
    ("NE", 63, [("GF", "NE-6", {"ALL": "ALL"})], "MAPPED",
     "annex NE face 10.80 m to +4.80; his 10.00 m"),
    ("NE", 64, [("GF", "NE-4", {"ALL": "ALL"}), ("1F", "NE-2", {"ALL": "ALL"})], "RULE_DIFFERENCE",
     "two faces: GF 19.37 m +-0.00 -> +6.00 and the 1F set back 1.50 m, 19.27 m +5.50 -> +11.00 (sheet 09); his one "
     "plane 10.00 x 19.20 (+1.00 -> +11.00): no plinth, the 0.50 m where both faces exist counted once (T-159 HAND_RIGHT)"),
    ("NE", 65, [], "UNRESOLVED",
     "2 x 1.50 x 6.00 'annex vertical': no 1.50 m wide, 6.00 m high face on sheet 09; the 1.50 m is the 1F set-back "
     "depth, whose end faces are 1F SE-1 / NW-5 (measured there): possible double count"),
    # NW (rows 68-75: 389.94, of which dome 181.806, pool soffit 19.154, frame 3.9375)
    ("NW", 68, [], "UNRESOLVED",
     "1.50 x 6.00 'annex face': the GF block projects 1.50 m beyond the 1F on the sea side; its SW return (SW-9 1.50 m) "
     "is his row 51; no NW face 1.50 m wide is drawn"),
    ("NW", 69, [], "UNRESOLVED",
     "9.80 x 6.75 'high face': 6.75 m fits the 2F sea face (6.80 m), which is 4.70 m high (+9.70 -> +14.40) and stands "
     "6.77 m behind the 1F sea face; 9.80 m is not printed; the 2F sea face is mapped to row 77 (4.70 m printed), so "
     "row 69 as the 2F face would be a double count"),
    ("NW", 70, [("1F", "NW-1", {"ALL": "ALL"}), ("1F", "NW-2", {"ALL": "ALL"}), ("1F", "NW-3", {"ALL": "ALL"}),
                ("1F", "NE-1", {"ALL": "ALL"}), ("1F", "NW-4", {"ALL": "ALL"}), ("1F", "SW-1", {"ALL": "ALL"}),
                ("1F", "NW-5", {"ALL": "ALL"})], "PARTIAL",
     "rows 70 + 71 + 74 (4 x 4.95 m = 19.80 m at 5.50 / 5.70 m) against the 1F sea faces 12.628 m (+5.50 -> parapet, "
     "wave tops); 7.17 m of his length is not on the 1F sea face line (candidates: the pool-court walls, not house "
     "faces, or the GF pool glazing face NW-4)"),
    ("NW", 72, [], "EXCLUDED", "domes inside and outside 6 x 3.14 x 9.65 = 181.806: owner item 3 (no domes; T-161 renders)"),
    ("NW", 73, [], "ACCEPTED_12.834",
     "pool soffit 2 x 3.14 x 3.05 = 19.154: owner item 4 accepts the measured 12.834 (T-127, Checker 12.8343)"),
    ("NW", 75, [], "NOT_IN_T159", "frame band 0.45 x 8.75: not measured in T-159"),
    # ROOF (rows 77-79: 185.704) and annex parapets (83-84: 44.38)
    ("ROOF", 77, [("2F", "NE-1", {"ALL": "ALL"}), ("2F", "NW-1", {"ALL": "ALL"})], "PARTIAL",
     "2F faces not in his elevation rows: NE 8.10 + NW 6.80 = 14.90 m at 4.70 (printed 420 + 50); his 17.75 m"),
    ("ROOF", 78, [], "UNRESOLVED",
     "1F roof parapet, his 48.47 m x 1.70: the outer faces are in T-159 (50.569 m run); a run of 48.47 m fits the INNER "
     "face; 1.70 m is not printed (1.30 above +9.70 on sheets 07 / 09)"),
    ("ROOF", 79, [], "UNRESOLVED",
     "annex roof parapet, his 28.40 m x 0.70: outer run 29.342 m in T-159 (inner face fits 28.40); printed 0.50 "
     "(+4.30 -> +4.80)"),
    ("ROOF", 83, [], "UNRESOLVED",
     "'parapets of the annex roofs' 36.20 m x 0.70: GF house roof parapet outer run 28.770 m, printed 0.50 "
     "(+5.50 -> +6.00); 36.20 m fits no parapet run"),
    ("ROOF", 84, [], "UNRESOLVED", "parapet 27.20 m x 0.70: as row 83 (together 63.40 m against 28.770 m)"),
    ("FENCE", 87, [], "HELD_Q-65", "boundary wall 2.40 m high (rows 87-90, 107.24): owner Q-65 HELD; not a house face"),
    ("DRIP", 92, [], "HELD_UNANSWERED", "drip edge 0.28 x 181.70 = 50.876: owner has not answered (notes item 3)"),
]
# T-159 faces his rows do not hold (orientation of the face)
NOT_IN_HIS_ROWS = [
    ("GF", "SW-5", "porch: house face under the 1F plate (3.00 m)"), ("GF", "SW-6", "porch: flush face (1.40 m)"),
    ("GF", "SW-9", "COVERED 0.50 m under the 1F plate"), ("GF", "SW-8", "pool-court return"),
    ("1F", "SW-2", "1F face over the porch (4.40 m)"),
    ("GF", "SE-2", "entrance face under the porch (3.70 m, D-GF-07)"), ("GF", "SE-3", "porch return"),
    ("GF", "SE-5", "notch return"), ("GF", "P-2", "side-passage face (Q-67 A)"),
    ("GF", "NE-1", "porch return"), ("GF", "NE-2", "pool-court return"), ("GF", "NE-3", "pool-court return"),
    ("GF", "NW-7", "GF sea face 7.90 m (W02 saloon glazing 6.33 m in it)"),
    ("GF", "NW-2", "return"), ("GF", "NW-3", "pool-court return"), ("GF", "NW-4", "pool glazing face (W03)"),
    ("GF", "NW-5", "pool-court return"), ("GF", "NW-6", "pool-court face"), ("GF", "P-1", "side-passage face (Q-67 A)"),
]

# his opening rows (PLS sheet rows 29-41: 'windows, external openings'; row 96 reuses their 61.895 for the exterior;
# row 97: 11 x 0.70 x 0.50 for the spatter dash) -> the T-150 census ids (READY 8bbf39d), matched by width and kind
OPEN_MATCH = {
    29: (["W01"], "MATCH", "1.20 x 2.00 printed"),
    30: (["W13"], "MATCH", "1.20 x 2.30 printed"),
    31: (["W26"], "MATCH", "1.20 x 1.70 printed"),
    32: (["one of D-GF-01, D-GF-05, D-GF-06, D-2F-01"], "WIDTH_MATCH", "door 1.00; height 2.20 owner reference (ASSUMED)"),
    33: (["W14"], "MATCH_HEIGHT_DIFFERS", "2.45 x 1.60 printed against his 1.50"),
    34: (["four of D-GF-01, D-GF-03, D-GF-05, D-GF-06, D-GF-09, D-2F-01"], "WIDTH_MATCH",
         "the census has 6 outside-class doors 0.90 / 1.00 wide (D-GF-05 class HELD, Q-67)"),
    35: (["W08", "W09"], "WIDTH_MATCH", "1.50 wide; heights not printed (HELD)"),
    36: (["two of W10, W25, W27"], "WIDTH_MATCH", "1.00 wide; three candidates for two; heights HELD"),
    37: (["D-GF-07"], "MATCH_HEIGHT_DIFFERS", "main door 2.00 x 2.50 printed against his 2.30"),
    38: (["W15", "W16"], "MATCH_HEIGHT_DIFFERS", "1.55 x 3.10 printed (W16 INFERRED twin) against his 2.70"),
    39: (["W24", "?"], "PARTIAL", "W24 1.55 wide (height HELD); no second 1.50 / 1.55 window left in the census"),
    40: (["remaining outside doors + ?"], "PARTIAL",
         "rows 32 + 34 + 40 hold 11 doors 1.00 x 2.30; the census has 6 outside-class doors: 5 doors not identified "
         "(the 1.00 m lift-shaft / arch openings are interior)"),
    41: (["W18"], "MATCH_HEIGHT_DIFFERS", "0.50 x 2.16 printed against his 1.50"),
    97: (["W04", "W05", "W06", "W07", "W19", "W20", "W21", "W22", "W23", "W28"], "PARTIAL",
         "11 x 0.70 x 0.50 against the 10 small bathroom windows 0.60 wide (heights HELD) and W18 0.50 (row 41)"),
}
NOT_IN_HIS_LIST = [("W02", 6.33, None, "HELD"), ("W03", 6.57, 4.30, "PRINTED"), ("W17", 3.29, 3.50, "PRINTED"),
                   ("W11", 1.95, None, "HELD"), ("W12", 1.95, None, "HELD"), ("W29", 1.20, None, "HELD"),
                   ("one of W10 / W25 / W27", 1.00, None, "HELD")]
# facade openings with a printed (or inferred / owner-reference) height, T-150 (READY): id -> (w, h, status)
FACADE_KNOWN = {"W01": (1.20, 2.00, "PRINTED"), "W03": (6.57, 4.30, "PRINTED"), "W13": (1.20, 2.30, "PRINTED"),
                "W14": (2.45, 1.60, "PRINTED"), "W15": (1.55, 3.10, "PRINTED"), "W16": (1.55, 3.10, "INFERRED"),
                "W17": (3.29, 3.50, "PRINTED"), "W18": (0.50, 2.16, "PRINTED"), "W26": (1.20, 1.70, "PRINTED"),
                "D-GF-07": (2.00, 2.50, "PRINTED"), "D-GF-01": (1.00, 2.20, "ASSUMED"),
                "D-GF-03": (0.90, 2.20, "ASSUMED"), "D-GF-05": (1.00, 2.20, "ASSUMED"),
                "D-GF-06": (1.00, 2.20, "ASSUMED"), "D-GF-09": (0.90, 2.20, "ASSUMED"),
                "D-2F-01": (1.00, 2.20, "ASSUMED")}
FACADE_HELD = {"W02": 6.33, "W04": 0.60, "W05": 0.60, "W06": 0.60, "W07": 0.60, "W08": 1.50, "W09": 1.50, "W10": 1.00,
               "W11": 1.95, "W12": 1.95, "W19": 0.60, "W20": 0.60, "W21": 0.60, "W22": 0.60, "W23": 0.60, "W24": 1.55,
               "W25": 1.00, "W27": 1.00, "W28": 0.60, "W29": 1.20}


def load_raw():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    rows = {}
    for x in d["rows"]:
        if x["file"] == "PLS" and x["row"] in range(1, 100) and x["sheet"].startswith("البي"):
            rows[x["row"]] = {k[0:2].rstrip("0123456789"): v["v"] for k, v in x["cells"].items()}
    inv = {x["row"]: {k[0]: v["v"] for k, v in x["cells"].items()} for x in d["rows"]
           if x["file"] == "PLS" and x["sheet"] == "الفاتورة"}
    return rows, inv


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def side_area(t159, floor, side, portions, q07):
    """area of the named portions of one T-159 side (a share of a portion's length -> the same share of its area);
    a HELD band adds nothing here (T-159 keeps it as a range). q07: leave the plinth bands out."""
    tot, length = 0.0, 0.0
    seen = set()
    for r in t159:
        if r["FLOOR"] != floor or r["SIDE"] != side or not r["PORTION"]:
            continue
        want = portions.get(r["PORTION"], portions.get("ALL"))
        if want is None:
            continue
        pl = float(r["PORTION_LEN_M"])
        share = 1.0 if want == "ALL" else min(1.0, want / pl)
        if (r["PORTION"], pl) not in seen:
            length = max(length, pl * share)
            seen.add((r["PORTION"], pl))
        if q07 and r["SOURCE"].startswith("plinth"):
            continue
        if r["AREA_M2"]:
            tot += float(r["AREA_M2"]) * share
    return tot, length


def main():
    t159 = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else None
    rows, inv = load_raw()
    print("1. FREELANCER EXTERIOR PLASTER / SIGMA TERMS AGAINST THE T-159 FACES (m2)")
    trows, sums = [], {}
    for grp, rn, faces, status, cause in TERMS:
        r = rows[rn]
        h, ln, cnt, tot = num(r.get("F")), num(r.get("H")), num(r.get("E")) or 1.0, num(r.get("I"))
        geo = q07 = 0.0
        for fl, sd, por in faces:
            g, _ = side_area(t159, fl, sd, por, False)
            q, _ = side_area(t159, fl, sd, por, True)
            geo += g
            q07 += q
        # rows 70 / 71 / 74 are one term (the 1F sea faces)
        if rn == 70:
            his = sum(num(rows[k]["I"]) for k in (70, 71, 74))
        elif rn == 87:
            his = num(rows[90]["J"])                       # rows 87-90, total in J90
        elif tot is None:
            his = num(r.get("J"))                          # drip edge: total in J92
        else:
            his = tot
        d = geo - his if faces else None
        sums.setdefault(grp, [0.0, 0.0, 0.0])
        sums[grp][0] += his
        sums[grp][1] += geo
        sums[grp][2] += q07
        faces_txt = " + ".join(f"{fl} {sd}" + ("" if list(por) == ["ALL"] else " " + "/".join(
            f"{k} {v}" for k, v in por.items())) for fl, sd, por in faces)
        print(f"   {grp:5s} row {rn:3d}{' (+71, 74)' if rn == 70 else '':10s} his {his:9.3f} ({cnt:g} x {h} x {ln}) "
              f"| drawing geometric {geo:8.3f}, Q-07 {q07:8.3f} | diff {('%+.3f' % d) if d is not None else '-':>9s} | "
              f"{status} | {faces_txt}")
        trows.append([grp, rn if rn != 70 else "70+71+74", cnt, h, ln, f"{his:.4f}", faces_txt,
                      f"{geo:.4f}" if faces else "", f"{q07:.4f}" if faces else "",
                      f"{d:+.4f}" if d is not None else "", status, cause])
    print("   by group (his / drawing geometric / drawing Q-07):")
    for g, v in sums.items():
        print(f"     {g:5s} {v[0]:9.3f} / {v[1]:9.3f} / {v[2]:9.3f}")
    miss = 0.0
    print("   T-159 faces his rows do not hold:")
    for fl, sd, why in NOT_IN_HIS_ROWS:
        portions = {"COVERED": 0.5} if sd == "SW-9" else {"ALL": "ALL"}
        a, _ = side_area(t159, fl, sd, portions, False)
        miss += a
        print(f"     {fl} {sd:5s} {a:8.3f}  {why}")
        trows.append(["NOT_IN_HIS_ROWS", "", "", "", "", "", f"{fl} {sd}", f"{a:.4f}", "", "", "FACE_NOT_IN_HIS_ROWS",
                      why])
    print(f"     total {miss:.3f} m2 (geometric, measured part; HELD ranges of T-159 apart)")
    # his corner columns (A 'arrises and ends', B 'corners', m.l) by the same groups
    cg = {"walls (rows 51-75)": range(51, 76), "roof face (row 77)": range(77, 78),
          "parapets (rows 78-84)": range(78, 85), "boundary wall (rows 87-90)": range(87, 91), "drip edge (row 92)": [92]}
    ctot = 0.0
    print("   his corners (columns A + B, m.l):")
    for g, rr in cg.items():
        a = sum(num(rows[k].get("A")) or 0.0 for k in rr if k in rows)
        b = sum(num(rows[k].get("B")) or 0.0 for k in rr if k in rows)
        ctot += a + b
        print(f"     {g:28s} A {a:8.2f} + B {b:8.2f} = {a + b:8.2f}")
        trows.append(["HIS_CORNERS", g, "", "", "", "", "", "", "", "", "M.L", f"A {a:.2f} + B {b:.2f} = {a + b:.2f}"])
    print(f"     total {ctot:.2f} m.l (row 61 column A holds the text '8.3.1', not a number)")
    gross = num(inv[25]["B"])
    ded = num(inv[25]["D"])
    print(f"\n   his gross {gross:.3f}, deduction at half {ded:.4f} (65.745 / 2), net {num(inv[25]['F']):.4f}; "
          f"corners {num(inv[26]['B']):.2f} m.l at 2 m.l = 1 m2 -> {num(inv[26]['F']):.3f}")
    # 2. openings
    print("\n2. HIS 13 OPENING ROWS AGAINST THE T-150 CENSUS")
    orows, n_his = [], 0
    for rn in list(range(29, 42)) + [97]:
        r = rows[rn]
        cnt = num(r.get("E")) or 1.0
        h, w, a = num(r.get("F")), num(r.get("H")), num(r.get("I"))
        n_his += int(cnt)
        ids, st, why = OPEN_MATCH[rn]
        print(f"   row {rn:3d}: {cnt:g} x {w} x {h} = {a:.3f} | {', '.join(ids)} | {st} | {why}")
        orows.append([rn, cnt, w, h, f"{a:.4f}", "; ".join(ids), st, why])
    for oid, w, h, st in NOT_IN_HIS_LIST:
        print(f"   NOT IN HIS LIST: {oid} {w} x {h if h else 'HELD'} ({st})")
        orows.append(["NOT_IN_HIS_LIST", "", w, h if h else "", f"{w * h:.4f}" if h else "", oid, st,
                      "facade opening of the census with no row in his list"])
    kp = sum(w * h for w, h, s in FACADE_KNOWN.values() if s in ("PRINTED", "INFERRED"))
    ka = sum(w * h for w, h, s in FACADE_KNOWN.values() if s == "ASSUMED")
    hw = sum(FACADE_HELD.values())
    print(f"   his rows hold {n_his} openings (rows 29-41: 25; row 97: 11 small)")
    print(f"   facade openings in the census: {len(FACADE_KNOWN) + len(FACADE_HELD)}; with a printed / inferred height "
          f"{kp:.3f} m2, doors at the owner reference 2.20 (ASSUMED) {ka:.3f} m2, heights HELD on {len(FACADE_HELD)} "
          f"({hw:.2f} m of width)")
    T159 = 1022.534
    print(f"   NET (UP-GEN-003 1.1.0 PLASTER_PAINT = OWNER_DECISION_PENDING): HELD. Comparisons only: T-159 gross "
          f"{T159:.3f}; less the printed-height openings in full {T159 - kp:.3f}; at his half rule {T159 - kp / 2:.3f}; "
          f"his deduction 65.745 at half = 32.873")
    summary = {"terms": {g: {"his": round(v[0], 3), "geometric": round(v[1], 3), "q07": round(v[2], 3)}
                         for g, v in sums.items()},
               "faces_not_in_his_rows_m2": round(miss, 3), "his_openings_count": n_his,
               "facade_openings": len(FACADE_KNOWN) + len(FACADE_HELD), "facade_open_printed_m2": round(kp, 3),
               "facade_open_assumed_m2": round(ka, 3), "facade_open_held_width_m": round(hw, 2)}
    print("\nSUMMARY " + json.dumps(summary))
    if out:
        with open(out / "TERMS_T162.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["GROUP", "HIS_ROW", "COUNT", "HIS_H_M", "HIS_L_M", "HIS_M2", "T159_FACES", "DRAWING_GEOMETRIC_M2",
                        "DRAWING_Q07_M2", "DIFF_GEOMETRIC_MINUS_HIS_M2", "STATUS", "CAUSE"])
            w.writerows(trows)
        with open(out / "OPENINGS_T162.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["HIS_ROW", "COUNT", "HIS_W_M", "HIS_H_M", "HIS_M2", "CENSUS_IDS (T-150)", "MATCH", "NOTE"])
            w.writerows(orows)
        print("wrote", out / "TERMS_T162.csv", out / "OPENINGS_T162.csv")
    return summary


if __name__ == "__main__":
    main()
