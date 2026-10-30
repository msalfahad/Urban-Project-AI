"""T-367 read-only application on the development villa: masonry joint mortar on the V3.0.26 MAS.BLOCK lines.

Inputs (MERGED ledgers of this repository; no drawing coordinate, image or client name is read or written here):
  walls      research/agents_t279/t279_inputs.build(): the URBAN_V3026_INPUTS_V1 of ARCH_TAKEOFF_V3.0.26 (T-279 Gate B
             MERGED 88ef8cb8), itself built from the sha256-pinned T-333 r2 fill (MERGED bb54c5d6): per MAS.BLOCK line,
             every wall with block type, status, carried m2 (an edited ledger stops the build);
  part ids   engine/source/boq_line.line_id with the arch_v3026.part_line identity (project, MAS.BLOCK, parent element
             + '#BLOCKWORK:<status>_<type>', R-T279-1, T-279, m2): the V3.0.26 part line each wall sits in;
  D-12 flag  research/agents_t176/BLOCK_PROCUREMENT_BY_WALL.csv (walls drawn 0.20 next to 0.25 columns, ST p.8 note
             20; never chosen): mortar scales with t, so the flag is carried beside the row.

    python3 -I research/agents_t367/alsenan_t367.py [--write | --check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t279"))
sys.path.insert(2, str(ROOT))

import masonry_mortar_v1 as M          # noqa: E402
import t279_inputs as T279             # noqa: E402

V3026_MERGE = "88ef8cb8"
CANDIDATE_BLACK = {"0.15": 201.1421, "0.2": 111.5240}     # T-279 s.2 per block type (Checker Gate B 07:50)
CANDIDATE_WHITE = {"0.15": 25.8850, "0.2": 240.5500}
CANDIDATE_TOTAL = 579.1011
FREELANCER = {  # 'Alsenan chalet project' / blockwork workbook (Arabic title 'buildings'), cover sheet rows 15-19
    "exterior": 559.8015, "t0.15": 617.2480, "t0.20": 83.6400, "total": 1260.6895,
    "mortar_rows": 0, "glue_rows": 0}
OUT_WALL = HERE / "MORTAR_BY_WALL_T367.csv"
OUT_LINE = HERE / "MORTAR_BY_LINE_T367.csv"
OUT_SUM = HERE / "summary.json"


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def part_line_id(project_id, element_id, area_status, block_type):
    from engine.source import arch_v3026 as A, boq_line as BL
    part = A.part_name(area_status, block_type)          # the candidate's ASCII status spelling, as arch_v3026
    return BL.line_id(project_id, "MAS.BLOCK", A.part_element_id(element_id, part), A.RULE_ID, A.RULE_VERSION, "m2")


def d12_flags():
    p = ROOT / "research/agents_t176/BLOCK_PROCUREMENT_BY_WALL.csv"
    out = {}
    for r in csv.DictReader(p.open(encoding="utf-8", newline="")):
        if r.get("d12_flag"):
            out[r["row_id"]] = r["d12_flag"]
    return out


def build():
    doc = T279.build()
    pid = doc["project"]
    d12 = d12_flags()
    lines, rows = [], []
    for ln in doc["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        walls = []
        for w in ln["walls"]:
            st = w["status"]
            if st in ("HELD", "HELD ON DROP"):
                ast, area, kind = "HELD", None, ("DROP (U - L x d, never evaluated)" if st == "HELD ON DROP" else
                                                 "HELD WALL")
                plid = None
            else:
                ast = w["part_status"] if st == "ESTABLISHED PART + HELD" else st
                area = w["carried"]
                kind = "ESTABLISHED_PART (held piece named on the parent)" if st == "ESTABLISHED PART + HELD" else "WHOLE"
                plid = part_line_id(pid, ln["element_id"], ast, w["block_type"])
            walls.append({"wall_id": w["wall_id"], "block_type": w["block_type"], "area_m2": area,
                          "area_status": ast, "kind": kind, "part_line_id": plid})
        line = {"line_id": ln["line_id"], "floor": ln["floor"], "t_m": ln["family"], "walls": walls}
        lr = M.line_rows(line)
        for r in lr:
            r["d12"] = d12.get(r["wall_id"], "")
        rows += lr
        lines.append(line)
    return pid, lines, rows


def tables(rows):
    by_line = {}
    for r in rows:
        k = (r["floor"], r["t_m"], r["line_id"], r["part_line_id"] or "(parent: held)", r["block_type"],
             r["mortar_status"] if r["block_type"] == "BLACK" else ("ADHESIVE HELD" if r["block_type"] == "WHITE"
                                                                   else r["mortar_status"]),
             r["area_status"] or "")
        e = by_line.setdefault(k, {"walls": [], "area": 0.0, "mortar": 0.0, "alt": 0.0, "bed": 0.0, "head": 0.0,
                                   "blank": 0})
        e["walls"].append(r["wall_id"])
        if r["mortar_m3"] is not None:
            e["area"] += r["area_m2"]
            e["mortar"] += r["mortar_m3"]
            e["alt"] += r["alt_mortar_m3"]
            e["bed"] += r["bed_m3"]
            e["head"] += r["head_m3"]
        elif r["area_m2"] is not None:
            e["area"] += r["area_m2"]
            e["blank"] += 1
        else:
            e["blank"] += 1
    return by_line


def summarise(rows):
    blk = [r for r in rows if r["block_type"] == "BLACK"]
    est = [r for r in blk if r["mortar_m3"] is not None]
    by_t = {}
    for r in est:
        e = by_t.setdefault(str(r["t_m"]), {"area": 0.0, "mortar": 0.0, "alt": 0.0, "walls": 0})
        e["area"] += r["area_m2"]
        e["mortar"] += r["mortar_m3"]
        e["alt"] += r["alt_mortar_m3"]
        e["walls"] += 1
    for t, v in CANDIDATE_BLACK.items():
        if abs(by_t[t]["area"] - v) > 0.0005:
            raise ValueError(f"black t {t}: {by_t[t]['area']} != candidate {v}")
    black = M.close(rows, sum(CANDIDATE_BLACK.values()))
    white = [r for r in rows if r["block_type"] == "WHITE"]
    white_est = sum(r["area_m2"] for r in white if r["area_m2"] is not None)
    if abs(black + white_est - CANDIDATE_TOTAL) > 0.0005:
        raise ValueError(f"black {black} + white {white_est} != {CANDIDATE_TOTAL}")
    by_area_status = {}
    for r in est:
        e = by_area_status.setdefault(r["area_status"], {"area": 0.0, "mortar": 0.0, "walls": 0})
        e["area"] += r["area_m2"]
        e["mortar"] += r["mortar_m3"]
        e["walls"] += 1
    cs = M.cement_sand(sum(r["mortar_m3"] for r in est))
    fl = FREELANCER
    f15 = fl["t0.15"] * M.per_m2(M.MODULE_BLACK, 0.15)["total"]
    f20 = fl["t0.20"] * M.per_m2(M.MODULE_BLACK, 0.20)["total"]
    return {
        "task": "T-367", "method": M.METHOD, "candidate": "ARCH_TAKEOFF_V3.0.26", "candidate_merge": V3026_MERGE,
        "black_established_m2": _r(black, 4), "black_walls_established": len(est),
        "black_by_t": {t: {k: _r(v, 6) for k, v in e.items()} for t, e in by_t.items()},
        "black_mortar_m3": _r(sum(r["mortar_m3"] for r in est)),
        "black_mortar_bed_m3": _r(sum(r["bed_m3"] for r in est)),
        "black_mortar_head_m3": _r(sum(r["head_m3"] for r in est)),
        "black_mortar_alt_0x21_m3": _r(sum(r["alt_mortar_m3"] for r in est)),
        "black_by_area_status": {k: {kk: _r(vv, 6) for kk, vv in v.items()} for k, v in by_area_status.items()},
        "mortar_status": "ASSUMED — OWNER-APPROVED (every wall; module PROVISIONAL Q-75 + owner 2026-10-29)",
        "black_held_named": sorted(r["wall_id"] for r in blk if r["mortar_m3"] is None),
        "black_part_walls_held_piece_on_parent": sorted(r["wall_id"] for r in est if r["kind"].startswith("ESTABLISHED")),
        "white_established_m2": _r(white_est, 4),
        "white_walls_adhesive_held": sorted(r["wall_id"] for r in white if r["area_m2"] is not None),
        "white_held_walls": sorted(r["wall_id"] for r in white if r["area_m2"] is None),
        "unknown_type": sorted(r["wall_id"] for r in rows if r["block_type"] == "UNKNOWN"),
        "cement_sand": {"status": "HELD", "why": cs["why"]},
        "freelancer": {"rows": {k: v for k, v in fl.items()},
                       "mortar_if_his_15_20cm_areas_m3": _r(f15 + f20), "his_15cm_m3": _r(f15), "his_20cm_m3": _r(f20),
                       "verdict_proposal": "RULE_DIFFERENCE (no mortar / glue row: blockwork priced per m2, mortar "
                                           "inside his rate); no numeric verdict on mortar"},
    }


def wall_csv(rows):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["parent_line_id", "part_line_id_v3026", "floor", "t_m", "wall_id", "kind", "block_type", "area_m2",
                "area_status", "mortar_m3_per_m2", "bed_m3", "head_m3", "mortar_installed_m3", "mortar_status",
                "mortar_alt_module_0.40x0.21_m3 (beside, not merged)", "adhesive", "d12_flag (T-176 row of the same wall id, register r2; never chosen)", "why"])
    for r in rows:
        f = lambda x: "" if x is None else f"{x:.6f}"     # noqa: E731
        w.writerow([r["line_id"], r["part_line_id"] or "", r["floor"], r["t_m"], r["wall_id"], r["kind"],
                    r["block_type"], f(r["area_m2"]), r["area_status"] or "", f(r["mortar_per_m2"]), f(r["bed_m3"]),
                    f(r["head_m3"]), f(r["mortar_m3"]), r["mortar_status"], f(r["alt_mortar_m3"]),
                    r["adhesive"] or "", r["d12"], r["why"]])
    return s.getvalue()


def line_csv(rows):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["floor", "t_m", "parent_line_id", "part_line_id_v3026", "block_type", "mortar_or_adhesive_status",
                "area_status", "walls", "area_m2 (established)", "mortar_installed_m3", "bed_m3", "head_m3",
                "alt_module_0.40x0.21_m3", "walls_blank_by_name"])
    for k, e in sorted(tables(rows).items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][3], kv[0][4])):
        black_est = k[4] == "BLACK" and e["mortar"] > 0
        w.writerow([k[0], k[1], k[2], k[3], k[4], k[5], k[6], " ".join(e["walls"]),
                    f"{e['area']:.4f}" if e["area"] else "", f"{e['mortar']:.6f}" if black_est else "",
                    f"{e['bed']:.6f}" if black_est else "", f"{e['head']:.6f}" if black_est else "",
                    f"{e['alt']:.6f}" if black_est else "", e["blank"]])
    return s.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    _, _, rows = build()
    s = summarise(rows)
    files = {OUT_WALL: wall_csv(rows), OUT_LINE: line_csv(rows),
             OUT_SUM: json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True) + "\n"}
    if a.write:
        for p, t in files.items():
            p.write_text(t, encoding="utf-8")
    if a.check:
        bad = [p.name for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        if bad:
            print("STALE:", bad)
            return 1
    print(json.dumps({k: s[k] for k in ("black_established_m2", "black_by_t", "black_mortar_m3", "black_mortar_bed_m3",
                                        "black_mortar_head_m3", "black_mortar_alt_0x21_m3", "white_established_m2",
                                        "black_held_named", "freelancer")}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
