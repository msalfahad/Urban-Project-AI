"""T-288 builder: blockwork wall register v4 = register v3 (T-285, MERGED e418c5e0) + the wall pieces under the six
sunken slab panels HELD on the drop d (R-T288-1, register_v4.py) + the Checker's 2026-10-25 01:43 - 02:09 whole-wall
re-measures carried at the Checker's value (R-T285-1 rule 2) with its three named corrections. Read-only over the merged
ledgers; writes only research/agents_t288/*. Numbers, ids and handles only: no coordinate, image or client name.

Inputs:
  research/agents_t285/BLOCKWORK_WALL_REGISTER_V3.csv    register v3 (T-285, MERGED e418c5e0)
  research/agents_t274/T274_SIBLING_CHECK.csv            exact closing pieces per wall (T-274, MERGED aba9399a)
  research/agents_t288/CLIP_T288.json                    own clip of the walls against the six sunken regions
                                                         (alsenan_clip_t288.py on the private DXFs)
  research/agents_t288/CHECKER_VERIFIED_V4.csv           the 18 walls the Checker re-measured whole (GF-W12 withdrawn)
Drawings: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and 'ST7757 dxf.dxf'
(sha 9f9d1179). Usage: python3 -I research/agents_t288/build_t288.py [--check]"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t285"))
import register_v4 as R4  # noqa: E402
import register_v3 as R3  # noqa: E402

V3 = ROOT / "research/agents_t285/BLOCKWORK_WALL_REGISTER_V3.csv"
SIB = ROOT / "research/agents_t274/T274_SIBLING_CHECK.csv"
CLIP = HERE / "CLIP_T288.json"
VER = HERE / "CHECKER_VERIFIED_V4.csv"
STOREY_T = {"GF": (4.50, 0.16)}          # GF storey 4.50, roof slab t 0.16 (register basis; T-234 ledger)
SUNKEN_FACES = {"GF-015", "GF-016", "GF-081", "GF-128", "GF-141", "1F-018"}
PIECE = re.compile(r"slab (\S+) \(t ([0-9.]+)\) ([0-9.]+) m h ([0-9.]+)")
ANY = re.compile(r"\) ([0-9.]+) m h ([0-9.]+)")
# GF-W16: the B5 / slab GF-141 boundary. T-274's route-G band puts B5 0.0012 + 0.1999 = 0.2011 m and the sunken piece
# 2.9489 m; the drawn B5 band (ST 281 / 27C, 0.200 = SBT W 20) and the hatch 280 edge give 2.9500 (Checker 02:00 own
# cut; own clip axis 2.9500). The piece list keeps closing the census 4.4500.
PIECE_FIX = {"GF-W16": {"from": "B5 0.2011 m h 4.00 + slab GF-141 2.9489 m h 4.34",
                        "to": "B5 0.2000 m h 4.00 + slab GF-141 2.9500 m h 4.34 (drawn B5 band = hatch 280 edge)",
                        "pieces": [(0.1000, 3.75, False), (1.2000, 4.34, False), (0.2000, 4.00, False),
                                   (2.9500, 4.34, True)], "deductions": 3.7500}}
# The Checker's named corrections (BOARD Verifier 02:03 / 02:06 / 02:09) and what remains after them to reach the
# Checker's reported (3-decimal, own-geometry) value; each wall's change = sum of its named parts, residual 0.
NAMED = {
    "GF-W01": [("0.0026 m sliver inside B26's drawn outline at 3.65 (was HELD): +0.0026 x 3.65", 0.0095),
               ("v3 kept the T-143 VERIFIED gross 62.1550 over T-274's exact 62.1541", -0.0009),
               ("Checker own value 62.1638 reported 62.164 (own pieces CB8 15.170 / B1 1.1474 / CB1 0.150)", 0.0004)],
    "1F-W06": [("W24 deducted at its drawn jamb width 1.5523 (not the label 1.550): -0.0023 x 1.500", -0.0035),
               ("Checker own gross 57.7744 vs T-274 57.7747 and rounding of 54.4859 to 54.486", -0.0002)],
    "1F-W05": [("B23 piece 0.3500 (not 0.349) and CB10 3.6500 (not 3.651): 0.001 x (3.45 - 3.70)", -0.0003),
               ("Checker own W14 jamb 2.4498 vs 2.450 and rounding of 19.3028 to 19.303", 0.0003)],
    "1F-W00": [("Checker own value 12.935: census 6.571 vs run 6.5708 and rounding (Checker 02:01)", 0.0014)],
    "1F-W20": [("Checker own value 24.5073 reported 24.507 (v3 exact 24.5068)", 0.0002)],
    "1F-W22": [],                                   # Checker 20.401 = v3 20.4010: class only
}


def agreement(wid, face, diff):
    """own clip vs census piece: AGREE within 1 mm; otherwise the cause is named (never silently taken)."""
    if abs(diff) <= 0.001:
        return "AGREE (<= 1 mm)"
    if face == "GF-016" and wid in ("GF-W31", "GF-W32"):
        return ("JUNCTION: the face-span axis runs on through the 3-way 45-degree junction of GF-W20 / GF-W31 / "
                "GF-W32 under GF-016; the census run stops at the T-215 junction bound and books the junction once "
                "(T-274 piece kept; open for the Checker's re-clip)")
    if abs(diff) <= 0.002:
        return ("BAND EDGE (<= 2 mm): T-274's route-G band edge vs the drawn hatch edge at the beam between "
                "275 / 276; census piece kept, difference listed for the Checker (d coefficient only)")
    raise SystemExit(f"{wid} {face}: own clip differs from the census piece by {diff:.4f} m with no named cause")


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def f4(x):
    return "" if x is None else f"{x:.4f}"


def sunken_pieces(sib):
    """{wall_id: [(face_id, length_m, h_m)]} from T-274's exact pieces: the slab faces that are sunken panels."""
    out = {}
    for r in sib:
        for m in PIECE.finditer(r["basis"] or ""):
            face, t, L, h = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
            if face in SUNKEN_FACES:
                out.setdefault(r["wall_id"], []).append((face, L, h))
    return out


def build():
    v3 = rd(V3)
    R3.one_wall_once(v3)
    sib = {r["wall_id"]: r for r in rd(SIB)}
    clip = json.loads(CLIP.read_text())
    ver = {r["wall_id"]: float(r["net_m2"]) for r in rd(VER)}
    sp = sunken_pieces(sib.values())
    if sorted(sp) != sorted(clip["walls"]):
        raise SystemExit(f"walls with sunken pieces in T-274 {sorted(sp)} != own clip {sorted(clip['walls'])}")
    if clip["unclaimed"]:
        raise SystemExit(f"face lines under a sunken panel that no wall claims: {clip['unclaimed']}")
    pieces_rows, rows, causes = [], [], []
    for r in v3:
        wid = r["wall_id"]
        row = {k: r[k] for k in ("wall_id", "floor", "group", "block_type", "t_m", "length_m", "basis", "completeness",
                                 "conflict", "conflict_increment_m2", "held_items")}
        row.update({"net_m2_v3": r["net_m2_v3"], "class_v3": r["net_class_v3"], "state_v4": r["completeness"],
                    "net_m2_v4": r["net_m2_v3"], "upper_m2_v4": "", "drop_length_m": "", "expression_v4": "",
                    "class_v4": r["net_class_v3"], "verified_by_v4": r["verified_by"], "cause_v4": ""})
        if wid in sp:
            L_wall = 0.0
            for face, L, h in sp[wid]:
                if wid in PIECE_FIX and face == "GF-141":
                    L = 2.9500
                cl = clip["walls"][wid]["under"][face]
                storey, t = STOREY_T[r["floor"]]
                hh, held = R4.piece_height(storey, t, sunken=True)
                assert hh is None and abs(h - (storey - t)) < 1e-9, (wid, h)
                pieces_rows.append({
                    "wall_id": wid, "panel_face": face, "piece_m": f4(L), "booked_h_v3_m": f"{h:.2f}",
                    "height_v4": f"{storey - t:.2f} - d", "held": held,
                    "clip_axis_under_m": f4(cl["axis_under_panel_m"]),
                    "clip_hatch_to_column_gap_m": f4(cl["hatch_to_column_gap_m"]),
                    "clip_faces_in_hatch_m": " / ".join(f4(x) for x in cl["faces_in_hatch_m"]),
                    "clip_vs_piece_m": f4(cl["axis_under_panel_m"] - L),
                    "agreement": agreement(wid, face, cl["axis_under_panel_m"] - L)})
                L_wall += L
            # the d = 0 bound: the v3 net (GF-W16: re-cut on the drawn B5 band)
            if wid in PIECE_FIX:
                fx = PIECE_FIX[wid]
                w = R4.wall_with_drop(float(r["length_m"]), [{"length_m": a, "height_m": b, "sunken": c}
                                                             for a, b, c in fx["pieces"]], fx["deductions"])
                upper = round(w["upper_m2"], 4)
                d = round(upper - float(r["net_m2_v3"]), 4)
                causes.append({"wall_id": wid, "cause": "pieces re-cut on the drawn B5 band: " + fx["to"],
                               "delta_m2": d})
            else:
                upper = float(r["net_m2_v3"])
            row.update({"state_v4": R4.HELD_ON_DROP, "net_m2_v4": "", "upper_m2_v4": f4(upper),
                        "drop_length_m": f4(L_wall),
                        "expression_v4": f"{upper:.4f} - {L_wall:.4f} x d m2 (d HELD, D-41)",
                        "class_v4": R3.HELD if r["net_class_v3"] == R3.VERIFIED else r["net_class_v3"],
                        "verified_by_v4": ("WITHDRAWN by the Checker 2026-10-25 02:00 (whole 0.450 m under the "
                                           "lowered soffit of GF-081)" if r["net_class_v3"] == R3.VERIFIED else ""),
                        "held_items": ((r["held_items"] + " || ") if r["held_items"] else "") +
                                      f"drop d of the sunken panel(s) {', '.join(sorted({p[0] for p in sp[wid]}))} "
                                      f"(D-41): {L_wall:.4f} m at {STOREY_T[r['floor']][0] - STOREY_T[r['floor']][1]:.2f} - d"})
            R4.check_register_row(row, L_wall)
        elif wid in ver:
            new = ver[wid]
            old = float(r["net_m2_v3"])
            parts = NAMED.get(wid, [])
            if r["net_class_v3"] != R3.VERIFIED:
                if abs(sum(p[1] for p in parts) - round(new - old, 4)) > 0.00005:
                    raise SystemExit(f"{wid}: named parts {sum(p[1] for p in parts):.4f} != change {new - old:.4f}")
                for i, (what, dm) in enumerate(parts):
                    causes.append({"wall_id": wid, "cause": what, "delta_m2": dm})
                row.update({"net_m2_v4": f"{new:.4f}", "class_v4": R3.VERIFIED,
                            "verified_by_v4": next(x["checker_run"] for x in rd(VER) if x["wall_id"] == wid)})
            elif abs(new - old) > 0.00005:
                raise SystemExit(f"{wid}: VERIFIED in v3 at {old} but Checker list says {new}")
        R4_check_plain(row, sp)
        rows.append(row)
    R3.one_wall_once(rows)
    return rows, pieces_rows, causes, clip


def R4_check_plain(row, sp):
    """rule 3 on every wall: a wall with no sunken piece carries no drop term."""
    if row["wall_id"] not in sp:
        R4.check_register_row(row, 0.0)


def totals(rows, causes):
    def tot(basis):
        sel = [r for r in rows if r["basis"] in basis]
        det = [r for r in sel if r["net_m2_v4"] != ""]
        drop = [r for r in sel if r["state_v4"] == R4.HELD_ON_DROP]
        by = {}
        for r in det:
            by[r["class_v4"]] = round(by.get(r["class_v4"], 0) + float(r["net_m2_v4"]), 4)
        v3 = round(sum(float(r["net_m2_v3"]) for r in sel if r["net_m2_v3"]), 4)
        U = round(sum(float(r["upper_m2_v4"]) for r in drop), 4)
        L = round(sum(float(r["drop_length_m"]) for r in drop), 4)
        D = round(sum(float(r["net_m2_v4"]) for r in det), 4)
        m3 = round(sum(float(r["net_m2_v4"]) * float(r["t_m"]) for r in det), 4)
        return {"v3_net_m2": v3, "v4_at_d0_upper_bound_m2": round(D + U, 4), "drop_term_m": L,
                "v4_expression": f"{D + U:.4f} - {L:.4f} x d m2 (d HELD, D-41)",
                "determinate_net_m2": D, "determinate_net_m3": m3, "determinate_walls": len(det),
                "held_on_drop_walls": len(drop), "held_on_drop_upper_m2": U, "by_class_determinate_m2": by,
                "walls_with_figure": len(sel)}
    A = tot(("A",))
    B = tot(("A", "B"))
    res_A = R3.reconcile(A["v3_net_m2"], A["v4_at_d0_upper_bound_m2"], causes)
    res_B = R3.reconcile(B["v3_net_m2"], B["v4_at_d0_upper_bound_m2"], causes)
    return A, B, res_A, res_B


def outputs():
    rows, pieces, causes, clip = build()
    A, B, rA, rB = totals(rows, causes)
    files = {}

    def csvtext(rs, fields):
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rs)
        return b.getvalue()

    reg_fields = ["wall_id", "floor", "group", "block_type", "t_m", "length_m", "basis", "net_m2_v3", "class_v3",
                  "state_v4", "net_m2_v4", "upper_m2_v4", "drop_length_m", "expression_v4", "class_v4",
                  "verified_by_v4", "conflict", "conflict_increment_m2", "held_items", "completeness", "cause_v4"]
    by_wall = {}
    for c in causes:
        by_wall.setdefault(c["wall_id"], []).append(f"{c['cause']} ({c['delta_m2']:+.4f})")
    for r in rows:
        if r["state_v4"] == R4.HELD_ON_DROP:
            by_wall.setdefault(r["wall_id"], []).append(f"R-T288-1: {r['drop_length_m']} m under a sunken panel "
                                                        f"carried at {STOREY_T[r['floor']][0] - STOREY_T[r['floor']][1]:.2f} - d")
        r["cause_v4"] = " | ".join(by_wall.get(r["wall_id"], []))
    files["BLOCKWORK_WALL_REGISTER_V4.csv"] = csvtext(rows, reg_fields)
    files["SUNKEN_PIECES_T288.csv"] = csvtext(pieces, list(pieces[0]))
    rec = [{"step": "v3 (T-285 basis A, 449.5934) -> v4 at d = 0", "wall_id": c["wall_id"], "cause": c["cause"],
            "delta_m2": f"{c['delta_m2']:+.4f}"} for c in causes]
    files["RECONCILIATION_V4.csv"] = csvtext(rec, ["step", "wall_id", "cause", "delta_m2"])
    changed = [r for r in rows if r["state_v4"] != r["completeness"] or r["net_m2_v4"] != r["net_m2_v3"] or r["class_v4"] != r["class_v3"]]
    ledger = [{"wall_id": r["wall_id"], "before_v3": f"{r['net_m2_v3']} {r['class_v3']}",
               "after_v4": (r["expression_v4"] if r["expression_v4"] else f"{r['net_m2_v4']} {r['class_v4']}"),
               "cause": r["cause_v4"]} for r in changed]
    files["CHANGED_WALLS_V4.csv"] = csvtext(ledger, ["wall_id", "before_v3", "after_v4", "cause"])
    reg_sha = hashlib.sha256(files["BLOCKWORK_WALL_REGISTER_V4.csv"].encode()).hexdigest()
    verified = sorted(r["wall_id"] for r in rows if r["class_v4"] == R3.VERIFIED)
    summary = {"task": "T-288", "rule": R4.RULE_ID, "walls": len(rows), "basis_A": A, "basis_B": B,
               "residual_A_m2": rA, "residual_B_m2": rB,
               "held_on_drop_walls": sorted(r["wall_id"] for r in rows if r["state_v4"] == R4.HELD_ON_DROP),
               "sunken_pieces_m": round(sum(float(p["piece_m"]) for p in pieces), 4),
               "verified_walls": verified,
               "verified_net_m2": round(sum(float(r["net_m2_v4"]) for r in rows if r["class_v4"] == R3.VERIFIED), 4),
               "clip_frames": clip["frames"], "faces_on_panel_edges": [e["handle"] for e in clip["on_edge"]],
               "register_v4_csv_sha256": reg_sha}
    files["summary.json"] = json.dumps(summary, indent=1, ensure_ascii=True) + "\n"
    export = {"register": "BLOCKWORK_WALL_REGISTER_V4", "rule": [R4.RULE_ID, R3.RULE_ID], "csv_sha256": reg_sha,
              "status": "research register for lane I (T-279); NOT RELEASED; no BOQ line moves",
              "walls": [{"wall_id": r["wall_id"], "floor": r["floor"], "block_type": r["block_type"],
                         "t_m": float(r["t_m"]), "state": r["state_v4"], "class": r["class_v4"],
                         "net_m2": float(r["net_m2_v4"]) if r["net_m2_v4"] else None,
                         "upper_bound_m2_at_d0": float(r["upper_m2_v4"]) if r["upper_m2_v4"] else None,
                         "drop_length_m": float(r["drop_length_m"]) if r["drop_length_m"] else None,
                         "held_items": r["held_items"] or None, "conflict": r["conflict"] or None,
                         "basis": r["basis"] or None} for r in rows],
              "totals": {"A": A, "B": B}}
    files["REGISTER_V4_EXPORT.json"] = json.dumps(export, indent=1, ensure_ascii=True) + "\n"
    return files, summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="refuse if a committed output differs")
    a = ap.parse_args(argv)
    files, summary = outputs()
    bad = []
    for name, txt in files.items():
        p = HERE / name
        if a.check:
            if not p.exists() or p.read_text() != txt:
                bad.append(name)
        else:
            p.write_text(txt)
    if bad:
        print("DIFFERS:", ", ".join(bad))
        return 1
    print(json.dumps({k: summary[k] for k in ("basis_A", "residual_A_m2", "sunken_pieces_m", "verified_net_m2")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
