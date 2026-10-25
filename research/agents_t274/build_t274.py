"""T-274 builder: the sibling check of register v2's height pieces over every wall, the corrected pieces where they do
not close, the opening-in-masonry scan, and the established net before / after. Read-only over merged ledgers
(register v2 research/agents_t228, T-215, T-222, T-261 r3); writes only research/agents_t274/*. Numbers only: no drawing
coordinate, image or client name.

Inputs committed in this folder (made from the Drive drawings by t274_runs.py -> t274_geom.py -> t274_export.py):
  T274_RUN_PIECES.csv  every census run cut exactly at every column, beam band and slab face edge (stations along the run)
  T274_OPENING_GAPS.csv every drawn opening / glazing gap of the V2 run: part inside a column, inside the counted runs
Drawings: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and 'ST7757 dxf.dxf'
(sha 9f9d1179). Usage: python3 -I research/agents_t274/build_t274.py [--check]"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import piece_close as PC  # noqa: E402

REG = ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv"
T215 = ROOT / "research/agents_t215/T215_ROW_EFFECT.csv"
T261 = ROOT / "research/agents_t261/T261_SPLIT.csv"
T261S = ROOT / "research/agents_t261/summary.json"
ARCH = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55)"
ST = "Drive 'Alsenan chalet project' / ST7757 dxf.dxf (sha 9f9d1179)"
STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}
# 1F-W14 + 1F-W15: the T-222 junction piece (research/agents_t222/T222_RESULTS.csv rows 17 / 18, MERGED with T-222)
T222_JUNCTION = {"1F-W14 + 1F-W15": (0.077, 0.302)}
# GF-W11: the run carries the full-height glazed line W02 (T-108 r2 / T-150: glass, not masonry); census = run - glazing
GLAZED_OUT = {"GF-W11": "full-height glazed line W02 out of the masonry run (T-108 r2, T-150 IN_GROSS = NO)"}
# the W18 deduction in register v2 (T-227 delta: deductions 9.806 = W15 4.363 + W16 4.363 + W18 1.080 = 0.500 x 2.160)
W18 = {"wall": "1F-W00", "band": "WB-FL0041-FL0042", "schedule_w": 0.500, "area": 1.080}
PIECE_RE = re.compile(r"([^,;]*?\(([^)]*)\)): ([0-9.]+) m -> h ([0-9.]+)")
SLIVER_NOTE = "sub-mm drafting offset joined to its neighbour (rule 4)"


def f(x, n=4):
    return f"{x:.{n}f}"


def reg_rows():
    return list(csv.DictReader(open(REG, encoding="utf-8")))


def reg_pieces(r):
    ev = r["evidence"].split(" || ")[-1]
    seg = ev.split("member above / height:")[1].split("; storey heights")[0] if "member above / height:" in ev else ""
    out = []
    for m in PIECE_RE.finditer(seg):
        name, det, L, h = m.group(1).strip(), m.group(2), float(m.group(3)), float(m.group(4))
        key = next((t for t in name.split() if t.startswith("BM-")), None)
        if key is None:
            mm = re.search(r"slab (\S+)", name)
            key = mm.group(1) if mm else name
        d = re.search(r"(?:h|slab t) ([0-9.]+)", det)
        out.append({"name": name, "key": key, "length_m": L, "height_m": h,
                    "basis": round(h + float(d.group(1)), 4) if d else None})
    return out


def runs_of(r):
    m = re.search(r"V2 run (.*?) \(", r["evidence"].split(" || ")[-1])
    ids = m.group(1).split() if m else []
    return [f"{r['floor']}|{x}" for x in ids if x != "none"] if ids and ids[0] != "none" else []


def run_pieces():
    P = defaultdict(list)
    for x in csv.DictReader(open(HERE / "T274_RUN_PIECES.csv")):
        P[x["run_key"]].append(x)
    return P


BMR = ROOT / "research/agents_t110/BEAM_MEMBER_REGISTER.csv"


def candidates():
    """member id -> candidate depths (m) recorded for a member whose depth is not printed (T-043 / T-110 'candidates')."""
    out = {}
    for x in csv.DictReader(open(BMR, encoding="utf-8")):
        if "candidate" in (x["evidence"] or "").lower() and x["depth_m"] == "see candidates":
            ds = [int(b) / 100 for b in re.findall(r"\b\d{2}\s*x\s*(\d{2,3})\b", x["evidence"])]
            if ds:
                out[x["member_id"]] = sorted(set(ds))
    return out


CAND = candidates()


def corner_rule(ps, basis, ends):
    """rule 6 at the run ends: an L-corner piece under an undepthed band next to a printed beam piece."""
    if len(ps) < 2:
        return ps
    for i in (0, len(ps) - 1):
        p = ps[i]
        nb = ps[1] if i == 0 else ps[-2]
        if p["height_m"] is not None or p["kind"] != "BEAM" or nb is None or nb["kind"] != "BEAM" or nb["depth"] is None:
            continue
        end = ends[0] if i == 0 else ends[-1]
        if end != "L" or p["length_m"] > 0.30:
            continue
        h = PC.shared_corner_height(basis, nb["depth"], CAND.get(p["key"], []))
        if h is not None:
            p["height_m"] = h
            p["held_item"] = None
            p["name"] += (f" [corner shared with {nb['name']}: rule 6, {nb['depth']} >= every candidate "
                          f"{CAND.get(p['key'])} of the unprinted member (D-04 open)]")
    return ps


def exact_pieces(r, P, regp):
    """the exact pieces of the wall's census run(s), columns out, slivers joined, heights on the register's basis."""
    hmap = {p["key"]: p["height_m"] for p in regp}
    bases = {p["basis"] for p in regp if p["basis"] is not None}
    basis = bases.pop() if len(bases) == 1 else STOREY[r["floor"]]
    out = []
    for rk in runs_of(r):
        ps = []
        for x in P.get(rk, []):
            if x["kind"] == "COLUMN":
                continue
            L = float(x["len_m"])
            if x["kind"] == "BEAM":
                key, name = x["member_id"], f"{x['mark']} {x['member_id']} (h {x['depth_m'] or 'not printed'})"
                d = float(x["depth_m"]) if x["depth_m"] else None
                h = hmap.get(key, round(basis - d, 4) if d is not None else None)
                held = None if h is not None else f"{x['mark']} {x['member_id']}: depth not printed ({x['member_status']})"
            elif x["kind"] == "FACE" and x["face_cls"] == "SLAB" and x["slab_t_m"]:
                key, name = x["face_id"], f"slab {x['face_id']} (t {x['slab_t_m']})"
                h = hmap.get(key, round(basis - float(x["slab_t_m"]), 4))
                held = None
            elif x["kind"] == "FACE" and x["face_cls"] == "BEAM_OR_COLUMN":
                key, name, h, held = x["face_id"], f"edge face {x['face_id']}", None, \
                    f"face {x['face_id']} between drawn edges, no member identified"
            else:
                key = x["face_id"] or x["kind"]
                name, h = f"{x['face_cls'] or x['kind']} {x['face_id']}".strip(), None
                held = f"{name}: nothing with a printed soffit is drawn over this length"
            ps.append({"kind": x["kind"], "key": key, "name": name, "length_m": L, "height_m": h,
                       "held_item": held, "run": rk, "from_m": float(x["from_m"]), "to_m": float(x["to_m"]),
                       "depth": float(x["depth_m"]) if x["kind"] == "BEAM" and x["depth_m"] else None})
        ends = (P.get(rk) or [{}])[0].get("run_ends", "").split(";")
        out += corner_rule(PC.join_slivers(ps), basis, ends)
    return out


def t215_rows():
    return {x["row_id"]: x for x in csv.DictReader(open(T215))}


def build():
    R = reg_rows()
    P = run_pieces()
    J = t215_rows()
    t261 = defaultdict(list)
    for x in csv.DictReader(open(T261)):
        t261[x["wall_id"]].append(x)
    t261_net = json.load(open(T261S))["by_wall"]
    gaps = list(csv.DictReader(open(HERE / "T274_OPENING_GAPS.csv")))
    sib, corr = [], []
    est_before = est_after = 0.0
    m3_before = m3_after = 0.0
    for r in R:
        wid, L = r["wall_id"], float(r["length_m"])
        regp = reg_pieces(r)
        held_len = float(r["held_length_m"] or 0)
        rsum = sum(p["length_m"] for p in regp)
        rres = L - held_len - rsum
        reg_g = float(r["gross_m2"]) if r["gross_m2"] not in ("", None) else None
        row = {"wall_id": wid, "floor": r["floor"], "t_m": r["t_m"], "census_m": f(L, 3), "register_held_m": f(held_len, 3),
               "register_piece_sum_m": f(rsum, 3), "register_residual_m": f(rres, 3),
               "register_closes": ("NO PIECE LIST" if not regp and held_len < L - PC.TOL_M else
                                   "YES" if abs(rres) <= PC.TOL_M else "NO"), "register_gross_m2": r["gross_m2"],
               "register_gross_class": r["gross_class"], "net_class": r["net_class"]}
        ex, note, extra_g, extra_lo_hi = [], "", 0.0, None
        if wid in t261:
            s = sum(float(x["length_m"]) for x in t261[wid])
            row.update(exact_piece_sum_m=f(s), exact_residual_m=f(L - s), exact_closes="YES" if abs(L - s) <= PC.TOL_M
                       else "NO", exact_gross_m2="", delta_gross_m2="", basis="T-261 r3 drawn-extent split (MERGED "
                       "164b189f) governs this wall: its pieces close the census; established net "
                       f"{t261_net.get(wid)} m2 + HELD increment", status="CLOSED (T-261)")
            sib.append(row)
            continue
        rks = runs_of(r)
        if not rks or any(k not in P for k in rks):
            why = ("no straight V2 run (hand census, curved arc band or a T-222 piece row): not cut here; "
                   + ("register pieces do not close: HELD figure only" if regp and abs(rres) > PC.TOL_M else
                      "its own basis stands (T-222 / hand census)"))
            row.update(exact_piece_sum_m="", exact_residual_m="", exact_closes="NOT CUT", exact_gross_m2="",
                       delta_gross_m2="", basis=why, status="NOT CUT")
            sib.append(row)
            continue
        ex = exact_pieces(r, P, regp)
        run_len = sum(p["length_m"] for p in ex)
        census_pieces = list(ex)
        if wid in J:
            j = J[wid]
            dl, lo, hi = float(j["delta_m"]), float(j["d_gross_m2_min"]), float(j["d_gross_m2_max"])
            census_pieces.append({"kind": "JUNCTION", "key": "T-215", "name": f"T-215 junction piece {dl:+.4f} m "
                                  "(closed by the drawn masonry area, merged)", "length_m": dl, "height_m": None,
                                  "held_item": None})
            extra_g, extra_lo_hi = (lo + hi) / 2, (lo, hi)
            note = f"T-215 junction close {dl:+.4f} m, d_gross {lo:+.4f} .. {hi:+.4f} m2 (merged ledger)"
        if wid in T222_JUNCTION:
            dl, dg = T222_JUNCTION[wid]
            census_pieces.append({"kind": "JUNCTION", "key": "T-222", "name": f"T-222 junction piece {dl:.3f} m",
                                  "length_m": dl, "height_m": None, "held_item": None})
            extra_g, extra_lo_hi = dg, (dg, dg)
            note = f"T-222 junction piece {dl:.3f} m = {dg:.3f} m2 (merged ledger)"
        csum = sum(p["length_m"] for p in census_pieces)
        uniform = len({p["height_m"] for p in ex}) == 1 and ex[0]["height_m"] is not None
        if wid in GLAZED_OUT and uniform:
            note = GLAZED_OUT[wid] + f": run {run_len:.4f} m wholly under one soffit (h {ex[0]['height_m']}), so the " \
                   f"{L:.3f} m of masonry has that height wherever it stands in the run"
            census_pieces = [dict(ex[0], length_m=L)]
            csum = L
        res = L - csum
        row.update(exact_piece_sum_m=f(csum), exact_residual_m=f(res),
                   exact_closes="YES" if abs(res) <= PC.TOL_M else "NO")
        held = [p for p in ex if p["height_m"] is None]
        if abs(res) <= PC.TOL_M and not held:
            if wid in GLAZED_OUT:
                g = L * ex[0]["height_m"]
            else:
                g = sum(p["length_m"] * p["height_m"] for p in ex) + extra_g
            row["exact_gross_m2"] = f(g)
            row["delta_gross_m2"] = f(g - reg_g, 4) if reg_g is not None else ""
            if extra_lo_hi and extra_lo_hi[0] != extra_lo_hi[1]:
                gl = sum(p["length_m"] * p["height_m"] for p in ex) + extra_lo_hi[0]
                gh = sum(p["length_m"] * p["height_m"] for p in ex) + extra_lo_hi[1]
                row["exact_gross_m2"] = f"{gl:.4f} .. {gh:.4f}"
            row["status"] = "CLOSED"
        elif abs(res) <= PC.TOL_M:
            g = sum(p["length_m"] * p["height_m"] for p in ex if p["height_m"] is not None)
            row["exact_gross_m2"] = f"{g:.4f} + HELD " + "; ".join(f"{p['length_m']:.4f} m {p['held_item']}" for p in held)
            row["delta_gross_m2"] = ""
            row["status"] = "CLOSED WITH HELD PIECES"
        else:
            row["exact_gross_m2"] = ""
            row["delta_gross_m2"] = ""
            row["status"] = "NOT CLOSED"
        row["basis"] = (note + "; " if note else "") + " | ".join(
            f"{p['name']} {p['length_m']:.4f} m" + (f" h {p['height_m']}" if p["height_m"] is not None else " HELD")
            for p in ex)
        sib.append(row)
        # corrections: walls whose register pieces do not close and whose exact gross differs
        if row["register_closes"] == "NO" or (row["delta_gross_m2"] and abs(float(row["delta_gross_m2"])) >= 0.0005):
            corr.append({"wall_id": wid, "census_m": f(L, 3), "register_pieces": " | ".join(
                f"{p['name']} {p['length_m']:.2f} m h {p['height_m']}" for p in regp),
                "register_piece_sum_m": f(rsum, 3), "register_gross_m2": r["gross_m2"],
                "exact_pieces": row["basis"], "exact_piece_sum_m": row["exact_piece_sum_m"],
                "exact_gross_m2": row["exact_gross_m2"], "delta_gross_m2": row["delta_gross_m2"],
                "net_class": r["net_class"], "status": row["status"]})
    # opening in masonry (rule 5): the scan over every drawn gap and the 1F-W00 W18 correction
    scan = []
    for g in gaps:
        inc, inr, gap = float(g["in_columns_m"]), float(g["in_runs_m"]), float(g["gap_m"])
        if inc > PC.TOL_M:
            scan.append({"floor": g["floor"], "band_id": g["band_id"], "gap": g["bridged_by"], "gap_m": f(gap),
                         "in_column_m": f(inc), "in_masonry_m": f(inr), "finding": "jamb inside a column outline"})
    w18 = next(g for g in gaps if g["band_id"] == W18["band"] and g["bridged_by"] == "GLAZING_IN_BAND" and g["floor"] == "1F")
    w18_in = PC.opening_in_masonry(0.0, float(w18["gap_m"]), (0.0, float(w18["gap_m"])),
                                   [(0.0, float(w18["in_columns_m"]))])
    w18_h = W18["area"] / W18["schedule_w"]
    w18_fix = round((W18["schedule_w"] - w18_in) * w18_h, 6)
    # established net before / after (register v2 basis; T-261 proposal kept apart)
    by = {x["wall_id"]: x for x in sib}
    after_rows = []
    for r in R:
        cls = r["net_class"]
        if cls in ("", "HELD") or r["net_m2"] in ("", None):
            continue
        n0 = float(r["net_m2"])
        est_before += n0
        m3_before += float(r["net_m3"] or 0)
        n1 = n0
        x = by[r["wall_id"]]
        why = "unchanged"
        if x.get("status") == "CLOSED" and x.get("delta_gross_m2") and ".." not in x["exact_gross_m2"]:
            d = float(x["delta_gross_m2"])
            if abs(d) >= 0.0005:
                if cls == "VERIFIED":
                    why = f"VERIFIED by the Checker: figure kept; exact pieces differ by {d:+.4f} m2 (listed)"
                else:
                    n1 = n0 + d
                    why = f"exact closing pieces {d:+.4f} m2"
        if r["wall_id"] == W18["wall"]:
            n1 += w18_fix
            why = (why + "; " if why != "unchanged" else "") + f"W18 deducted by its {w18_in:.4f} m inside the masonry " \
                  f"(not 0.500): +{w18_fix:.4f} m2"
        est_after += n1
        m3_after += n1 * float(r["t_m"])
        after_rows.append({"wall_id": r["wall_id"], "net_class": cls, "net_before_m2": f(n0, 3), "net_after_m2": f(n1),
                           "delta_m2": f(n1 - n0), "why": why})
    # (iv) the stale unresolved_reason of 1F-W00 (register v2 is read-only here: the corrected text is listed)
    r00 = next(r for r in R if r["wall_id"] == W18["wall"])
    texts = [{"wall_id": W18["wall"], "field": "unresolved_reason", "register_v2_text": r00["unresolved_reason"],
              "corrected_text": "no held item: W15 and W16 deducted on their arched outlines 4.363 m2 each (T-227 / "
                                "T-238 merged), W18 by its 0.4673 m inside the masonry x 2.160 = "
                                f"{w18_in * w18_h:.4f} m2 (T-274 rule 5); pending the Checker's independent re-measure",
              "why": "the W16 height was established by T-227 (MERGED ebce3d97): 'W16 height HELD' is stale"}]
    m3_after_ = sum(float(a["net_after_m2"]) * float(next(r["t_m"] for r in R if r["wall_id"] == a["wall_id"]))
                    for a in after_rows)
    m3_before_ = sum(float(a["net_before_m2"]) * float(next(r["t_m"] for r in R if r["wall_id"] == a["wall_id"]))
                     for a in after_rows)
    summ = {"task": "T-274", "rule": PC.RULE_ID, "walls": len(R),
            "register_not_closing": sum(1 for x in sib if x["register_closes"] == "NO"),
            "register_without_piece_list": sum(1 for x in sib if x["register_closes"] == "NO PIECE LIST"),
            "register_not_closing_ids": [x["wall_id"] for x in sib if x["register_closes"] == "NO"],
            "exact_status": {k: sum(1 for x in sib if x["status"] == k) for k in sorted({x["status"] for x in sib})},
            "corrected_walls": len(corr),
            "established_net_register_v2_m2": round(est_before, 3),
            "established_net_after_m2": round(est_after, 4),
            "delta_m2": round(est_after - est_before, 4),
            "established_m3_before_net_x_t": round(m3_before_, 4), "established_m3_after_net_x_t": round(m3_after_, 4),
            "w18": {"gap_m": float(w18["gap_m"]), "in_column_m": float(w18["in_columns_m"]), "in_masonry_m": round(w18_in, 4),
                    "height_m": round(w18_h, 4), "register_deduction_m2": W18["area"],
                    "correct_deduction_m2": round(w18_in * w18_h, 4), "net_change_m2": w18_fix},
            "opening_scan_findings": len(scan), "opening_gaps_scanned": len(gaps),
            "t261_proposed_basis_m2": json.load(open(T261S))["established_net_proposed_m2"],
            "applied_to_register": False, "released_default": "V2.9 + route G (unchanged)"}
    return sib, corr, scan, after_rows, summ, texts


def csv_text(rows):
    if not rows:
        return ""
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue()


OUTS = {"T274_SIBLING_CHECK.csv": 0, "T274_CORRECTED.csv": 1, "T274_OPENING_SCAN.csv": 2, "T274_NET_BEFORE_AFTER.csv": 3,
        "T274_TEXT_CORRECTIONS.csv": 5}


def outputs():
    res = build()
    o = {k: csv_text(res[i]) for k, i in OUTS.items()}
    o["summary.json"] = json.dumps(res[4], indent=1) + "\n"
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    o = outputs()
    bad = []
    for k, v in o.items():
        p = HERE / k
        if a.check:
            if not p.exists() or p.read_text() != v:
                bad.append(k)
        else:
            p.write_text(v)
    if a.check:
        print("stale:", bad or "none")
        return 1 if bad else 0
    print(json.dumps(json.loads(o["summary.json"]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
