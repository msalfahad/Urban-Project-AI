"""T-790 F-24 fix rows on ARCH_TAKEOFF_V3.0.85 (worker 2, 2026-11-14): the 26 blank ARCH.WALL_PANEL / ARCH.WALL_VOLUME
lines (R-T790-1) and the two ranged B9-03 accessories MAS.MESH_STRIP / MAS.SHARMAT as points (R-T790-2 / 3, owner Q-77).

Inputs, merged files only: research/agents_t770/out/LINE_INDEX_V3_0_85.json (candidate), research/agents_t765/out/FIX_ROWS.json
(labels of the wired MAS.BLOCK lines), T-355 / T-362 level and junction ledgers (certain + held segments), T-765 component
heights (the DEFAULT tops that now replace 'block top unknown' / 'annex datum').

  python3 -I research/agents_t790/t790_fill.py [--check]
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t790_rules as R  # noqa: E402

IDX = RES / "agents_t770/out/LINE_INDEX_V3_0_85.json"
T765 = RES / "agents_t765/out/FIX_ROWS.json"
OUT = HERE / "out/FIX_ROWS.json"
MESH_LINE, TIE_LINE = "L-e765c5938bc82e046c3f", "L-82df9974b923558a31b4"
LD = 0.20            # lintel depth L1 / L2 (ST p.13 schedule, read in merged T-355) for openings up to 1.95 m
STD = (1.20, 1.50, 2.50, 3.00, 4.00)


def lintel(w):
    return next(L for L in STD if L >= w + 0.30 - 1e-9)


def door(w, head=2.20):
    return (w, 0.0, head, lintel(w), LD)


def win(w, sill, head):
    return (w, sill, head, lintel(w), LD)


B, A = R.BLACK, R.WHITE_A
# --- walls with NO level in T-355 / T-362 (annex datum, lift tie, no top): pieces at the T-765 DEFAULT tops ---------
# (wall, course, [(length, top, openings)], concrete tie face m2 inside the wall, T-765 basis)
ZERO = [
    ("GF-W00", B, [(9.90, 3.25, [])], 0, "annex 4.00 - CB7 0.75"),
    ("GF-W02", B, [(1.65, 3.84, [])], 0, "annex under slab 3.84"),
    ("GF-W03", B, [(2.64, 3.75, [])], 0, "4.50 - CB3 0.75 (ESTIMATE, D-03)"),
    ("GF-W08", B, [(2.44, 4.34, [door(1.00)]), (1.86, 3.75, [door(1.00, 2.10)])], 0.75 * 1.80, "lift wall, B14 tie 0.75 x 1.80"),
    ("GF-W09", B, [(1.80, 4.10, [])], 0.40 * 1.80, "lift wall 4.50 - B1 0.40, tie 0.40 x 1.80"),
    ("GF-W13", B, [(0.70, 4.10, [])], 0.40 * 0.70, "lift wall 4.50 - B1 0.40, tie 0.40 x 0.70"),
    ("GF-W14", B, [(2.66, 4.10, [door(0.90)]), (1.24, 3.75, [])], 0.75 * 1.20, "lift wall B2 / B7, tie 0.75 x 1.20"),
    ("GF-W23", B, [(1.30, 3.84, [])], 0, "annex under slab 3.84"),
    ("GF-W24", B, [(4.50, 3.84, [door(0.80)])], 0, "annex 3.84, D-GF-04"),
    ("GF-W25", B, [(4.50, 3.84, [])], 0, "annex 3.84"),
    ("GF-W27", B, [(1.50, 3.84, [door(0.80)])], 0, "annex 3.84, D-GF-02"),
    ("GF-W30", B, [(1.525, 4.34, [door(0.80)])], 0, "stub 1.525 x 4.34, D-GF-14 (ESTIMATE)"),
    ("HOUSE_BELOW_NG:MAIN_S", B, [(16.27, 0.70, [])], 0, "below-ground run 0.70"),
    ("HOUSE_BELOW_NG:ANNEX_S", B, [(10.00, 0.70, [])], 0, "below-ground run 0.70"),
    ("GF-W04", A, [(5.85, 3.25, [door(0.90), win(0.60, 0.90, 1.70), win(1.50, 0.90, 2.40)])], 0, "annex 4.00 - CB6 0.75; D-GF-03, W04, W08 sill 0.90 default"),
    ("GF-W06", A, [(2.50, 3.60, [door(1.00)])], 0, "annex 4.00 - B2 0.40, D-GF-01"),
    ("GF-W12", A, [(0.45, 4.04, [])], 0, "drop wall 4.34 - D-41 recess 0.30"),
    ("GF-W17", A, [(3.70, 3.60, [door(1.00)])], 0, "annex 4.00 - CB5 / B1 0.40, D-GF-05"),
    ("GF-W18", A, [(6.10, 3.25, [win(1.95, 0.90, 2.50), win(1.95, 0.90, 2.50)])], 0, "annex 4.00 - B9 0.75, W11 / W12 head 2.50"),
    ("GF-W35", A, [(1.29, 3.84, []), (0.40, 3.25, [])], 0, "annex 3.84 / 4.00 - B7 0.75"),
    ("GF-W36", A, [(0.50, 3.40, [])], 0, "member face 4.00 - 0.60 default"),
]
# white walls with an ESTABLISHED area but no run pieces (T-362 UNKNOWN_WALLS): area / level spacing (ESTIMATE)
WHITE_AREA = {"1F-W25": 1.490, "1F-W00/W01 BAY-ENDS": 0.572, "GF P-GF-05 ABOVE-LINTEL": 2.640}
# DEFAULT tops (T-765 / company defaults) of the pieces T-355 / T-362 held as 'block top unknown'
TOP = {"GF-W01": 3.75, "GF-W20": 4.04, "GF-W31": 4.04, "GF-W32": 4.04, "GF-W34": 4.04, "1F-W11": 3.70, "1F-W13": 3.70,
       "1F-W17": 3.70, "1F-W24": 3.70, "2F-W05": 3.65, "GF-W10": 3.90, "GF-W16": 4.04, "1F-W04": 3.60, "1F-W05": 3.60,
       "1F-W10": 3.60, "2F-W02": 3.50, "2F-W03": 3.65, "2F-W04": 3.65, "2F-W07": 3.05}
# held-extent openings: (width, head) defaults; wall top where T-765 lowered it
OPEN_HELD = {"A-GF-01": (1.00, 2.20), "A-1F-01": (1.00, 2.20), "L-1F-01": (1.00, 2.10), "L-2F-01": (1.00, 2.10)}
WALL_TOP = {"GF-W26": 3.50}           # T-765: annex 4.00 - B4 0.50 (T-355 levelled it to 4.00)
BEARING = 0.15                        # owner lintel rule: 0.15 each side


def held_built(wall, course, z, held, cause):
    """the part of a T-355 / T-362 held segment that the T-765 defaults build."""
    j = course[1]
    top = WALL_TOP.get(wall)
    if top is not None and z + j >= top:
        return 0.0, f"{wall} top {top} (T-765) below the level"
    if cause.startswith("BLOCK_TOP_UNKNOWN"):
        t = TOP[wall]
        return (held, f"top {t} DEFAULT") if z + j < t else (0.0, f"top {t} DEFAULT below the level")
    if cause.startswith("OPENING_EXTENT_UNKNOWN"):
        oid = re.search(r"\(([A-Z]-[0-9A-Z]+-\d+)", cause).group(1)
        w, head = OPEN_HELD[oid]
        if z < head - 1e-9:
            return held - w, f"{oid} head {head} DEFAULT: width cut"
        if z < head + LD - 1e-9:
            return held - lintel(w), f"{oid} lintel {lintel(w)} cut"
        return held, f"{oid} above its lintel"
    if cause.startswith("LINTEL_BEARING"):
        return max(held - 2 * BEARING, 0.0), "bearing 2 x 0.15 DEFAULT"
    raise ValueError(cause)


def mesh():
    rest = {(r["wall_id"], r["k"]): r for r in csv.DictReader(open(RES / "agents_t362/BLACK_RESTATED_T362.csv"))}
    certain = held_tot = built = drop_certain = 0.0
    walls_levels = {}
    for r in csv.DictReader(open(RES / "agents_t355/MESH_LEVELS_T355.csv")):
        rr = rest.get((r["wall_id"], r["k"]), r)
        z, net, held = float(r["level_m"]), float(rr["net_m"]), float(rr["held_m"] or 0)
        walls_levels.setdefault(r["wall_id"], set()).add(z)
        top = WALL_TOP.get(r["wall_id"])
        if top is not None and z + B[1] >= top:
            drop_certain += net
        certain += net
        held_tot += held
        if held > 1e-9:
            built += held_built(r["wall_id"], B, z, held, rr["held"])[0]
    for r in csv.DictReader(open(RES / "agents_t362/WHITE_MESH_LEVELS_T362.csv")):
        if r["family"] != "A":
            continue
        z = float(r["level_lo_m"])
        certain += float(r["certain_net_m"])
        h = float(r["held_m"] or 0) + float(r["band_held_m"] or 0)
        held_tot += h
        if h > 1e-9:
            built += held_built(r["wall_id"], A, z, h, r["held"] or "BLOCK_TOP_UNKNOWN")[0]
    zero = {}
    for wall, course, pieces, tie_m2, why in ZERO:
        v = sum(R.strip(L, t, ops, course) for L, t, ops in pieces)
        sp = 3 * (course[0] + course[1])
        v -= tie_m2 / sp
        zero[wall] = round(v, 4)
    white_area = sum(WHITE_AREA.values()) / (3 * (A[0] + A[1]))
    total = certain - drop_certain + built + sum(zero.values()) + white_area
    return {"certain_T355_T362_m": round(certain, 4), "held_T355_T362_m": round(held_tot, 4),
            "held_built_by_defaults_m": round(built, 4), "certain_dropped_GF_W26_m": round(drop_certain, 4),
            "zero_level_walls_m": zero, "zero_level_walls_total_m": round(sum(zero.values()), 4),
            "white_area_walls_m": round(white_area, 4), "point_m": round(total, 2)}, walls_levels


def sharmat(walls_levels):
    rows = list(csv.DictReader(open(RES / "agents_t355/SHARMAT_T355.csv")))
    certain = sum(int(r["ties"]) for r in rows if r["state"] == "MEASURED" and r["block_type"] == "BLACK")
    wa = [r for r in csv.DictReader(open(RES / "agents_t362/WHITE_SHARMAT_T362.csv")) if r["family"] == "A"]
    certain += sum(int(r["ties"]) for r in wa if r["state"] == "MEASURED")
    # GF-W26 measured at the 4.00 datum: T-765 top 3.50 -> one level less per junction
    w26 = [r for r in rows if r["wall_id"] == "GF-W26" and r["state"] == "MEASURED"]
    corr = sum(R.ties(3.50) - int(r["ties"]) for r in w26)
    seg_top = {("GF-W08", "2.500000"): 4.34, ("GF-W08", "1.800000"): 3.75, ("GF-W14", "1.200000"): 3.75,
               ("GF-W14", "2.700000"): 4.10}
    wall_top = {"GF-W00": 3.25, "GF-W09": 4.10, "GF-W13": 4.10, "GF-W04": 3.25, "GF-W06": 3.60, "GF-W17": 3.60,
                "GF-W18": 3.25, "GF-W12": 4.04, "GF-W36": 3.40, **TOP}
    held, det = 0, {}
    for r in rows:
        if r["state"] != "HELD" or r["block_type"] != "BLACK":
            continue
        w = r["wall_id"]
        t = seg_top.get((w, r["block_segment_m"])) or wall_top.get(w)
        n = R.ties(t) if t else len([z for z in walls_levels.get(w, ())])
        held += n
        det[w] = det.get(w, 0) + n
    for r in wa:
        if r["state"] != "HELD":
            continue
        n = R.ties(wall_top[r["wall_id"]], A)
        held += n
        det[r["wall_id"]] = det.get(r["wall_id"], 0) + n
    return {"certain_pcs": certain, "GF_W26_correction_pcs": corr, "held_junctions_pcs": held, "by_wall": det,
            "point_pcs": certain + corr + held}


def build():
    idx = {l["line_id"]: l for l in json.load(open(IDX))["lines"]}
    lab = {r["line_id"]: r for r in json.load(open(T765))["rows"]}
    block = {l["element_id"]: l for l in idx.values() if l["item_code"] == "MAS.BLOCK"}
    rows = []
    for l in sorted(idx.values(), key=lambda x: (x["item_code"], x["element_id"])):
        if l["item_code"] not in ("ARCH.WALL_PANEL", "ARCH.WALL_VOLUME") or l["class"] == "RELEASED":
            continue
        b = block[l["element_id"]]
        t = float(re.search(r"t=(0\.\d+)", l["element_id"]).group(1))
        src = lab.get(b["line_id"])
        if b["class"] == "EXCLUDED":
            rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
                         "before": {"class": l["class"], "net": None}, "after": {"class": "EXCLUDED", "net": None,
                         "reason": "NOT_APPLICABLE_WITH_EVIDENCE"}, "label": "NOT_APPLICABLE", "role": "REFERENCE",
                         "basis": (f"view of {b['line_id']} MAS.BLOCK EXCLUDED (T-765): element GF-H01, a 0.60 m long 0.40 band "
                                   "under beam B20 at the GF reception glazed line (T-103 / T-143 / T-228: material, base and top "
                                   "not drawn, NO_PIECE). It is NOT the Q-28 A plot-boundary band (0.20 x 0.60 B.W beam on the "
                                   "plot line, structure B10, billed by T-776). Owner trade: A masonry if ever drawn as block; "
                                   "0 blockwork today, so its panel / volume views are NOT_APPLICABLE, never a figure")})
            continue
        assert b["class"] == "RELEASED" and src and abs(src["after"]["net"] - b["measured_net"]) < 1e-6, l["element_id"]
        panel, vol = R.view_lines(b["measured_net"], b["class"], t)
        net = round(panel, 4) if l["item_code"] == "ARCH.WALL_PANEL" else round(vol, 6)
        rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": None}, "after": {"class": "RELEASED", "net": net},
                     "label": src["label"], "role": "REFERENCE (not in the Blockwork subtotal: geometry view, block m2 once)",
                     "basis": (f"= MAS.BLOCK {b['line_id']} {b['measured_net']} m2 (T-765, wired V3.0.83)"
                               + ("" if l["item_code"] == "ARCH.WALL_PANEL" else f" x t {t}") + " (R-T790-1)")})
    m, wl = mesh()
    s = sharmat(wl)
    for lid, code, unit, net, basis, lo_hi in (
            (MESH_LINE, "MAS.MESH_STRIP", "lm", m["point_m"],
             (f"Q-77 strip on every 3rd course (R-T790-2/3): certain {m['certain_T355_T362_m']} (T-355 black restated by "
              f"T-362 + white family A) - GF-W26 level above its T-765 top {m['certain_dropped_GF_W26_m']} + held segments "
              f"built by the T-765 / company default tops, heads 2.20 / 2.10 and lintels {m['held_built_by_defaults_m']} "
              f"(of {m['held_T355_T362_m']}) + {len(m['zero_level_walls_m'])} walls with no level placed (annex, lift, "
              f"below-ground; T-765 heights) {m['zero_level_walls_total_m']} + 3 established white areas / 0.753 "
              f"{m['white_area_walls_m']}; white family A (62.5 x 25) as the white units line (T-765, ESTIMATE); OPTIONAL "
              "item, never inside the block m2"), (idx[MESH_LINE]["held_low"], idx[MESH_LINE]["held_high"])),
            (TIE_LINE, "MAS.SHARMAT", "pcs", s["point_pcs"],
             (f"Q-77 one tie per 3rd course at every wall-to-column junction: {s['certain_pcs']} at the resolved junctions "
              f"(T-355 black 182 + T-362 white A 111) {s['GF_W26_correction_pcs']:+d} GF-W26 (top 3.50) + the 60 held "
              f"junctions at the T-765 / company default tops {s['held_junctions_pcs']} (levels beside the column); "
              "OPTIONAL item"), (idx[TIE_LINE]["held_low"], idx[TIE_LINE]["held_high"]))):
        rows.append({"line_id": lid, "item_code": code, "unit": unit, "element_id": idx[lid]["element_id"],
                     "before": {"class": idx[lid]["class"], "low": lo_hi[0], "high": lo_hi[1]},
                     "after": {"class": "RELEASED", "net": net}, "label": "ESTIMATE", "role": "OPTIONAL B9-03", "basis": basis})
    panel_add = sum(r["after"]["net"] for r in rows if r["item_code"] == "ARCH.WALL_PANEL" and r["after"]["net"])
    rel_panel = sum(l["measured_net"] for l in idx.values() if l["item_code"] == "ARCH.WALL_PANEL" and l["class"] == "RELEASED")
    pel = {l["element_id"] for l in idx.values() if l["item_code"] == "ARCH.WALL_PANEL"}
    blk_all = sum(l["measured_net"] for l in idx.values() if l["item_code"] == "MAS.BLOCK" and l["class"] == "RELEASED")
    blk = sum(l["measured_net"] for l in idx.values() if l["item_code"] == "MAS.BLOCK" and l["class"] == "RELEASED"
              and l["element_id"] in pel)
    assert abs(rel_panel + panel_add - blk) < 1e-3, (rel_panel + panel_add, blk)      # every view = its block line, once
    assert all(l["item_code"] != "ARCH.WALL_PANEL" or l["element_id"] in block for l in idx.values())
    return {"schema": "URBAN_FIX_ROWS_V1", "task": "T-790", "rule": "R-T790-1 .. 3 (t790_rules.py, every villa)",
            "base": "ARCH_TAKEOFF_V3.0.85 (LINE_INDEX_V3_0_85.json)",
            "summary": {"blank_before": sum(1 for r in rows if r["item_code"].startswith("ARCH.")), "blank_after": 0,
                        "panel_m2_total_after": round(rel_panel + panel_add, 4), "MAS.BLOCK_m2_same_groups": round(blk, 4),
                        "MAS.BLOCK_m2_all": round(blk_all, 4), "below_ground_no_view_line_m2": round(blk_all - blk, 4),
                        "blockwork_subtotal_change_m2": 0.0, "mesh": m, "sharmat": s},
            "rows": rows}


if __name__ == "__main__":
    out = build()
    txt = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        ok = OUT.read_text() == txt
        print("check", "OK" if ok else "DIFFERS", len(out["rows"]), "rows")
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt)
    print(len(out["rows"]), "rows;", json.dumps({k: v for k, v in out["summary"].items() if k not in ("mesh", "sharmat")}))
    print(json.dumps(out["summary"]["mesh"]), json.dumps(out["summary"]["sharmat"]))
