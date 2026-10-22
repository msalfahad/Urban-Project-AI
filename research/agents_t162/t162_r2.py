"""T-162 r2 (research only, not a method, not wired): corners as four separate m.l figures, parapets as physical items,
the freelancer's parapet rows 78-84 reconciled in m2 and m.l, and the r1 opening-arris double count corrected.

    python3 -I research/agents_t162/t162_r2.py [--write]      (--write refreshes the r2 CSVs and summary.json "r2")

Rework of the Checker's rejection of 2026-10-22 10:20 (gate h): (a) corners are ONE m.l line per component with the
physical length, the contract quantity, the payable length under the freelancer's half convention, the Urban PDF
rate basis and the amount as separate columns, never m2; (b) each parapet run as its components; (c) openings marked
as resting on the unmerged T-150 census; (d) rule + regression pair in check_t162.py; (e) lessons row (report).

Inputs, all already in the repository or cited by branch and commit (no drawing, no client data here):
  - the freelancer's cells: tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file PLS, rows 77-84, invoice 24-26);
  - the facade openings: t162_alsenan_corners.OPENINGS (T-150 census, READY r2 d4a22b0, NOT merged);
  - the parapet runs per side: PARAPET_RUNS below, from agents/task-T-172 (READY d7f81ef, NOT verified),
    PARAPET_COMPONENTS_T172.csv, measured on the Drive plan DXF with the heights of section A-A (sheet 10);
  - the vertical arrises: VERTICAL below, from the same T-172 commit, VERTICAL_CORNERS_T172.csv.
The top surface and the inner face of each run are RE-COMPUTED here from the per-side runs (parapet_components), so the
T-172 totals are checked, not copied."""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t162_corners as C                                                     # noqa: E402
from t162_alsenan_corners import OPENINGS                                    # noqa: E402

RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"
SRC_T172 = "agents/task-T-172 d7f81ef (READY, not verified)"

# (chain, side, outer top arris m.l, inner top arris m.l, wall t m, height above the roof slab top m or (lo, hi))
PARAPET_RUNS = [
    ("ANNEX", "NE-6", 10.8, 10.4001, 0.2, 0.5), ("ANNEX", "SE-1", 6.7, 6.3, 0.2, 0.5),
    ("ANNEX", "SW-1", 3.1, 2.9, 0.2, 0.5), ("ANNEX", "SW-2 arc", 2.042, 1.7279, 0.2, 0.5),
    ("ANNEX", "NW-1", 0.5, 0.7, 0.2, 0.5), ("ANNEX", "SW-3", 6.2001, 6.4001, 0.2, 0.5),
    ("GF", "SW-9", 1.4999, 1.2999, 0.2, 0.5), ("GF", "NW-7", 7.9, 7.5, 0.2, 0.5),
    ("GF", "NE-4", 19.37, 19.17, 0.2, 0.5),
    ("1F", "SW-3", 6.7699, 6.5699, 0.2, 1.3), ("1F", "NW-1", 1.1703, 0.8752, 0.2, 1.299),
    ("1F", "NW-2 arc", 3.5283, 3.6931, 0.2, 1.3), ("1F", "NW-3", 0.578, 0.4829, 0.2, 1.299),
    ("1F", "NE-1", 0.08, 0.0, 0.2, (1.0996, 1.2996)), ("1F", "NW-4", 0.4673, 0.4673, 0.2, 1.099),
    ("1F", "SW-1", 0.08, 0.0, 0.2, (1.0996, 1.2996)), ("1F", "NW-5", 6.725, 6.525, 0.2, 0.448),
    ("1F", "NE-2", 19.27, 18.87, 0.2, 1.3), ("1F", "SE-1", 7.5, 7.1, 0.2, 1.041),
    ("1F", "SW-2", 4.4, 4.2001, 0.2, (0.385, 1.6)),
    ("2F", "NW-1", 6.8, 6.45, 0.2, 0.5), ("2F", "NE-1", 8.1, 7.7, 0.15, 0.5),
    ("2F", "SE-1", 6.8, 6.45, 0.2, 0.5), ("2F", "SW-1", 8.1, 7.7, 0.2, 0.5),
]
CHAIN_LEVELS = {"ANNEX": "+4.30 -> +4.80", "GF": "+5.50 -> +6.00", "1F": "+9.70 -> +11.00 printed (NE / SW); waves NW / SE",
                "2F": "+13.90 -> +14.40"}
CHAIN_ENDS = {"ANNEX": "both ABUT (no stop-end)", "GF": "ABUT the 1F NW face; passage-mouth end UNKNOWN: stop-end HELD "
              "0 .. 1.20 m.l", "1F": "both ABUT the 2F faces (no stop-end)", "2F": "closed ring (no end)"}

# vertical external arrises (T-172): (item, count, DRAWING-CONFIRMED m.l, HELD lo, HELD hi, note)
VERTICAL = [
    ("GF convex arrises", 13, 66.900, 2.10, 2.55, "3 pool-court corners from the +1.00 court level; plinth below "
     "the F.F.L. HELD 3 x 0.70 .. 0.85"),
    ("1F convex arrises", 9, 39.000, 0.0, 11.90, "+5.50 (+4.30 on SE-1) -> +9.70; parapet end parts HELD up to "
     "1.30 / 1.60 per corner; slab edges below +5.50 HELD (Q-68)"),
    ("2F convex arrises", 4, 18.800, 0.0, 0.0, "+9.70 -> +14.40 printed (420 + 50)"),
    ("GF wall ends at the two passage mouths (facade + passage side)", 8, 43.100, 0.0, 1.20,
     "to the +5.50 passage wall top; GF parapet stop-end at the NE mouth HELD 0 .. 1.20 (Q-67 A cond.)"),
]

# his parapet rows (sheet 1) -> the drawn chains they cover (T-172 mapping by run length and label)
HIS_PARAPET_MAP = [((79,), ("ANNEX",), "'annex roof parapet': run 28.40 = the annex inner run 28.428"),
                   ((83, 84), ("GF", "2F"), "'parapets of the annexes' roofs' + 'parapet' (J84 subtotal 44.38): "
                    "the GF house and 2F roof parapets, inner runs 27.970 + 28.300 = 56.270 m"),
                   ((78,), ("1F",), "'parapet' 48.47 = the 1F inner run 48.784")]


def lohi(x):
    return (x, x) if not isinstance(x, tuple) else x


def chains():
    out = {}
    for ch, side, o, i, t, h in PARAPET_RUNS:
        p = C.parapet_components(o, i, t, h)
        c = out.setdefault(ch, {"outer": 0.0, "inner": 0.0, "top": 0.0, "face_lo": 0.0, "face_hi": 0.0,
                                "held_sides": []})
        c["outer"] += o
        c["inner"] += i
        c["top"] += p["top_m2"]
        lo, hi = lohi(p["inner_face_m2"])
        c["face_lo"] += lo
        c["face_hi"] += hi
        if isinstance(h, tuple):
            c["held_sides"].append(side)
    return out


def his_rows():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    rows = {r["row"]: r["cells"] for r in d["rows"] if r["file"] == "PLS" and r["sheet"].startswith("البي")}
    inv = {r["row"]: r["cells"] for r in d["rows"] if r["file"] == "PLS" and not r["sheet"].startswith("البي")}

    def v(rn, col):
        c = rows.get(rn, {}).get(f"{col}{rn}")
        return c["v"] if c and isinstance(c["v"], (int, float)) else None
    return rows, inv, v


def build():
    ch = chains()
    rows, inv, v = his_rows()
    # (b) parapet reconciliation in m2: his row = L x H; the physical scope he can cover = inner face + top
    #     (the outer face is in his elevation rows and in the T-159 faces)
    prec = []
    for rns, chs, why in HIS_PARAPET_MAP:
        hisL = sum(v(r, "H") for r in rns)
        hisA = sum(v(r, "I") for r in rns)
        hisH = sorted({v(r, "F") for r in rns})
        inner = sum(ch[c]["inner"] for c in chs)
        top = sum(ch[c]["top"] for c in chs)
        flo = sum(ch[c]["face_lo"] for c in chs)
        fhi = sum(ch[c]["face_hi"] for c in chs)
        phys_lo, phys_hi = flo + top, fhi + top
        length_eff = (hisL - inner) * hisH[0] if len(hisH) == 1 else None
        prec.append({"his_rows": "+".join(map(str, rns)), "drawn": "+".join(chs), "his_L_m": hisL, "his_H_m": hisH,
                     "his_m2": hisA, "inner_run_m": inner, "inner_face_m2": (flo, fhi), "top_m2": top,
                     "physical_m2": (phys_lo, phys_hi), "diff_m2": (hisA - phys_hi, hisA - phys_lo),
                     "length_effect_m2": length_eff, "why": why})
    # (a) corners: four figures per component
    ops = C.opening_arrises([(oid, w, h, st, sill) for oid, f, sd, w, h, st, sill in OPENINGS])
    tot_out = sum(c["outer"] for c in ch.values())
    tot_in = sum(c["inner"] for c in ch.values())
    lines = []
    for item, n, ml, hlo, hhi, note in VERTICAL:
        lines.append((item, n, ml, "DRAWING-CONFIRMED", f"HELD {hlo:.2f} .. {hhi:.2f}" if hhi else "-", note,
                      SRC_T172))
    lines.append(("parapet outer top arrises", 4, tot_out, "DRAWING-CONFIRMED", "-", "plan length of each outer run; "
                  "the 1F wave tops are longer than the plan length (UNKNOWN extra)", SRC_T172))
    lines.append(("parapet inner top arrises", 4, tot_in, "DRAWING-CONFIRMED", "-", "each on its own inner run "
                  "(outline offset by t, mitred, cut at higher construction)", SRC_T172))
    lines.append(("opening arrises (head + 2 jambs + sill), printed / inferred heights + head / sill of the HELD ones",
                  len(OPENINGS), ops["measured"], "DRAWING-CONFIRMED (T-150 census NOT merged)",
                  f"jambs HELD on {len(ops['held_ids'])} openings", "r2: r1 counted the jambs twice (2 x height per "
                  "opening added again in the caller); arch / curved heads at chord length (arc extra UNKNOWN)",
                  "T-150 READY r2 d4a22b0 (not merged)"))
    lines.append(("door arrises at the 2.20 m door height", sum(1 for o in OPENINGS if o[5] == "ASSUMED"),
                  ops["assumed"], "ASSUMED — OWNER-APPROVED (Q-55 C)", "-", "head + 2 jambs, no sill", "Q-55 C"))
    for item, rng, why in (("1F slab edge over open air (lower arris)", "13.079 m length, finish HELD (Q-68)",
                            "depth and finish not printed"),
                           ("arch frames SE stair tower / NW pool court", "98.002 .. 195.180 m.l", "profile not "
                            "detailed (designer)"),
                           ("drip / throat under a slab edge or parapet cap", "UNKNOWN", "nothing drawn; ST p.14 "
                            "typical parapet cap profile 'as per arch.'"),
                           ("boundary wall arrises", "HELD (Q-65)", "not a house face; height unprinted")):
        lines.append((item, "", None, "HELD", rng, why, "T-172 / T-162"))
    measured = sum(l[2] for l in lines if l[2] is not None and l[3].startswith("DRAWING"))
    return ch, prec, lines, ops, measured, rows, inv, v


def main():
    ch, prec, lines, ops, measured, rows, inv, v = build()
    print("(b) PARAPETS, component by component (re-computed from the per-side runs)")
    for k, c in ch.items():
        print(f"  {k:5s} {CHAIN_LEVELS[k]:42s} outer {c['outer']:7.3f}  inner {c['inner']:7.3f} m.l  top "
              f"{c['top']:6.3f} m2  inner face {c['face_lo']:7.3f} .. {c['face_hi']:7.3f} m2  ends: {CHAIN_ENDS[k]}"
              + (f"  HELD heights: {', '.join(c['held_sides'])}" if c["held_sides"] else ""))
    T = {k: sum(c[k] for c in ch.values()) for k in ("outer", "inner", "top", "face_lo", "face_hi")}
    print(f"  total outer {T['outer']:.3f} + inner {T['inner']:.3f} = {T['outer'] + T['inner']:.3f} m.l; top "
          f"{T['top']:.3f} m2; inner faces {T['face_lo']:.3f} .. {T['face_hi']:.3f} m2")
    print("\n   his parapet rows (m2) against inner face + top of the runs they cover:")
    for p in prec:
        print(f"  rows {p['his_rows']:6s} -> {p['drawn']:6s}: his {p['his_L_m']:.2f} m x {p['his_H_m']} = "
              f"{p['his_m2']:.3f}; drawn inner run {p['inner_run_m']:.3f} m, face {p['inner_face_m2'][0]:.3f} .. "
              f"{p['inner_face_m2'][1]:.3f} + top {p['top_m2']:.3f} = {p['physical_m2'][0]:.3f} .. "
              f"{p['physical_m2'][1]:.3f}; his - drawn {p['diff_m2'][0]:+.3f} .. {p['diff_m2'][1]:+.3f}; of which "
              f"length {p['length_effect_m2']:+.3f}")
    his_par = sum(p["his_m2"] for p in prec)
    ph = (sum(p["physical_m2"][0] for p in prec), sum(p["physical_m2"][1] for p in prec))
    print(f"  his rows 78-84 {his_par:.3f} m2 vs drawn inner faces + tops {ph[0]:.3f} .. {ph[1]:.3f} m2: "
          f"{his_par - ph[1]:+.3f} .. {his_par - ph[0]:+.3f}")
    A = sum(v(r, "A") for r in (78, 79, 83, 84))
    B = sum(v(r, "B") for r in (78, 79, 83, 84))
    print(f"  his parapet m.l: B {B:.2f} (2 x L) vs outer + inner top arrises {T['outer'] + T['inner']:.3f} "
          f"({B - T['outer'] - T['inner']:+.3f}); A {A:.2f} (1 x L, a third line: no physical arris)")
    print("\n(a) CORNERS, one m.l line per component (four figures; never m2)")
    for item, n, ml, st, held, note, src in lines:
        ff = C.four_figures(ml)
        print(f"  {item[:60]:60s} {('' if ml is None else f'{ml:9.3f}'):>9s} m.l  payable(half) "
              f"{('' if ml is None else format(ff['payable_ml_half_convention'], '9.3f')):>9s}  amount "
              f"{('' if ml is None else format(ff['amount_kwd'], '8.2f')):>8s} KWD  {st}  {held}")
    ff = C.four_figures(measured)
    print(f"  measured (DRAWING-CONFIRMED) {measured:.3f} m.l; payable at his half convention "
          f"{ff['payable_ml_half_convention']:.3f} m.l; amount at 1.25 KWD/m.l {ff['amount_kwd']:.2f} KWD")
    his = C.four_figures(None, contract_ml=1297.35)
    print(f"  his line: contract 1,297.35 m.l, payable {his['payable_ml_half_convention']:.3f} m.l, amount "
          f"{his['amount_kwd']:.2f} KWD (Urban PDF: 1,300 x 1.25 = 1,625.00)")
    if "--write" in sys.argv:
        with open(HERE / "PARAPETS_T162.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["CHAIN", "LEVELS", "OUTER_TOP_ARRIS_ML", "INNER_TOP_ARRIS_ML", "TOP_M2", "INNER_FACE_M2",
                        "ENDS", "HEIGHTS_HELD_ON", "STATUS", "SOURCE"])
            for k, c in ch.items():
                w.writerow([k, CHAIN_LEVELS[k], f"{c['outer']:.3f}", f"{c['inner']:.3f}", f"{c['top']:.3f}",
                            f"{c['face_lo']:.3f}" + ("" if c["face_lo"] == c["face_hi"] else f"..{c['face_hi']:.3f}"),
                            CHAIN_ENDS[k], " ".join(c["held_sides"]),
                            "DRAWING-CONFIRMED geometry; plaster scope of inner face / top: UNKNOWN (no specification)",
                            SRC_T172])
            w.writerow([])
            w.writerow(["HIS_ROWS", "DRAWN_CHAINS", "HIS_L_M", "HIS_H_M", "HIS_M2", "INNER_RUN_M", "PHYSICAL_M2",
                        "HIS_MINUS_PHYSICAL_M2", "LENGTH_EFFECT_M2", "MAPPING"])
            for p in prec:
                w.writerow([p["his_rows"], p["drawn"], f"{p['his_L_m']:.2f}", "/".join(map(str, p["his_H_m"])),
                            f"{p['his_m2']:.3f}", f"{p['inner_run_m']:.3f}",
                            f"{p['physical_m2'][0]:.3f}..{p['physical_m2'][1]:.3f}",
                            f"{p['diff_m2'][0]:+.3f}..{p['diff_m2'][1]:+.3f}", f"{p['length_effect_m2']:+.3f}",
                            p["why"]])
        with open(HERE / "CORNERS_R2_T162.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["COMPONENT", "COUNT", "PHYSICAL_ML", "CONTRACT_ML", "PAYABLE_ML_HALF_CONVENTION",
                        "RATE_BASIS", "AMOUNT_KWD_AT_URBAN_PDF_RATE", "STATUS", "HELD_OR_UNKNOWN", "NOTE", "SOURCE"])
            for item, n, ml, st, held, note, src in lines:
                ff = C.four_figures(ml)
                f3 = (lambda x: "" if x is None else f"{x:.3f}")
                w.writerow([item, n, f3(ml), f3(ff["contract_ml"]), f3(ff["payable_ml_half_convention"]),
                            ff["rate_basis"], "" if ml is None else f"{ff['amount_kwd']:.2f}", st, held, note, src])
        s = json.loads((HERE / "summary.json").read_text())
        s["corners"].pop("r1_opening_reveals_note", None)
        s["corners"]["opening_reveals_measured_ml"] = round(ops["measured"], 3)
        s["corners"]["opening_reveals_assumed_ml"] = round(ops["assumed"], 3)
        s["corners"]["r1_opening_reveals_note"] = ("r1 189.630 measured / 58.600 assumed counted the jambs twice "
                                                   "(-52.520 / -26.400 m.l in r2)")
        s["his"].pop("corners_m2_equiv", None)
        s["his"]["corners_payable_ml_half_convention"] = 648.675
        s["r2"] = {"parapets": {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in c.items()}
                                for k, c in ch.items()},
                   "parapet_rows_reconciliation": [{k: (round(x, 3) if isinstance(x, float) else
                                                        ([round(y, 3) for y in x] if isinstance(x, tuple) else x))
                                                    for k, x in p.items()} for p in prec],
                   "corners_measured_ml": round(measured, 3),
                   "corners_measured_payable_ml_half_convention": round(measured / 2, 3),
                   "corners_measured_amount_kwd_at_1_25": round(measured * 1.25, 2),
                   "opening_arrises_assumed_ml": round(ops["assumed"], 3),
                   "his_parapet_ml": {"A": round(A, 2), "B": round(B, 2)}}
        (HERE / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n")
        print("wrote PARAPETS_T162.csv, CORNERS_R2_T162.csv, summary.json r2")


if __name__ == "__main__":
    main()
