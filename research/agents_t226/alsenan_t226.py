"""T-226 on the development villa: height pieces of the walls HELD on 'no member drawn above' or on a beam-depth /
register conflict, D-12 m3 ranges, register delta and before / after coverage. Read-only over merged ledgers.

Method (no engine change, no frozen file): the T-108 r2 pipeline (research/agents_t108/alsenan_t108.py, MASONRY_AREA_V1
r2) is re-run unchanged on the merged inputs (its output equals T108_BY_WALL.csv byte for byte: tested), then once
more with ONLY the pieces this package closes under UP-MAS-HPIECE-001 R4 rewritten from 'CONFLICT' to their printed
depth. Every other piece, deduction, opening and status is the merged one. The T-225 register builder then forms the
rows in the register v1 format; register_delta.csv holds only the rows that changed (v1 is never edited, T-228 builds
register v2 from the deltas).

Evidence read this run (cited by Drive folder and title only; no drawing content in the repository):
  ST7757 dxf.dxf (sha 9f9d1179): continuous-beam schedule cells CB2 B 20 / H 50 (spans 4.0 / 4.0), CB10 B 25 / H 50
  (spans 3.0 / 4.1); simple-beam schedule B6 25 / 50, B4 20 / 50, B7 20 / 75, B1 / B2 / B3 20 / 40, B8 20 / 75, B15
  20 / 120; roof-slab plans around each held piece (labels, band edges, column boxes).
  P7757.dxf (sha ab54dd55): wall bands in the ST frame (T-108 translations GF 202.33 / 841.64, 1F 208.46 / 841.64 m:
  GF-W36 lies on the 0.50 m band north of the CB6 column, 1F-W05 under the CB10 band, GF-W07 ends at the CB1 column).
  Alsenan_Architectural_P7757_Pages_11-12.pdf p.1 SECTION B-B and p7757_arch_sheet10.pdf SECTION A-A: the cuts hatch
  masonry and concrete alike and outline no beam separately: R6, not a depth source (neither confirms nor contradicts).

Usage: python3 -I research/agents_t226/alsenan_t226.py [--check]
"""
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
for p in (HERE, ROOT / "research/agents_t108", ROOT / "research/agents_t225"):
    sys.path.insert(0, str(p))
import height_rules as H        # noqa: E402
import alsenan_t108 as A        # noqa: E402
import build_t225 as B          # noqa: E402
import register_v1 as RV        # noqa: E402

DRIVE = "Drive 'Alsenan chalet project'"
ST = f"{DRIVE} / ST7757 dxf.dxf (sha 9f9d1179)"
STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}
WIDTH_CONFLICT = "width CONFLICT (T-110, Q-61 C(1), designer D-02 / D-27)"

# Every held height piece of the walls in the T-226 scope (programme s.4: 'no member drawn above' and 'beam depth /
# register conflict'), one row per (wall, member). Lengths are the T-143 sampled piece lengths (the pipeline scales
# them to the run). Dome-opening pieces are T-227 (d): listed, never resolved here.
PIECES = [
    # R4: one mark, depth printed once and uncontested; width conflict only
    dict(wall="GF-W10", member="BM-GF-055", mark="CB2", kind="BEAM", length=3.46, marks=["CB2"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}],
         evidence=f"{ST}: continuous-beam schedule row CB2 B 20 / H 50 (2 spans 4.0 / 4.0); GROUND FLOOR ROOF SLAB label "
                  "CB2 bound to the band (T-110); band 0.25 drawn vs 0.20 printed = width only; no structural section "
                  "cuts it; section A-A / B-B do not cut it"),
    dict(wall="GF-W10", member="BM-GF-055", mark="CB2", kind="BEAM", length=3.36, marks=["CB2"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}], evidence="as above (span 2)"),
    dict(wall="1F-W05", member="BM-1F-031", mark="CB10", kind="BEAM", length=3.68, marks=["CB10"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}, {"kind": "ARCH_SECTION_NO_OUTLINE", "depth_m": None}],
         evidence=f"{ST}: continuous-beam schedule row CB10 B 25 / H 50 (2 spans 3.0 / 4.1); FIRST FLOOR ROOF SLAB band "
                  "0.30 drawn (T-110 CONFLICT D-02 on width only); the 0.20 wall lies inside the band over its whole "
                  "run; section B-B (Alsenan_Architectural_P7757_Pages_11-12.pdf p.1) cuts this end wall but outlines "
                  "no beam: R6, not a depth source"),
    dict(wall="1F-W05", member="BM-1F-031", mark="CB10", kind="BEAM", length=2.30, marks=["CB10"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}], evidence="as above (span 1)"),
    dict(wall="1F-W11", member="BM-1F-031", mark="CB10", kind="BEAM", length=0.12, marks=["CB10"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}],
         evidence=f"{ST}: west end of the wall under the CB10 band (0.10 m inside the 0.30 band); CB10 H 50"),
    dict(wall="1F-W16", member="BM-1F-030", mark="B6", kind="BEAM", length=0.26, marks=["B6"], width_conflict=True,
         sources=[{"kind": "SCHEDULE", "depth_m": 0.50}],
         evidence=f"{ST}: simple-beam schedule row B6 25 / 50; FIRST FLOOR ROOF SLAB vertical B6 span crosses the wall "
                  "(crossing = the band width); drawn 0.20 vs printed 0.25 = width only"),
    # R3: two marks
    dict(wall="GF-W03", member="BM-GF-057", mark="CB3 / B3 (With Stair)", kind="BEAM", length=2.64,
         marks=["CB3", "B3"], mark_depths={"CB3": 0.75, "B3": 0.40}, sources=[],
         evidence=f"{ST}: span 2 of the 3-span band carries CB3 (schedule H 75) and 'B3 (With Stair)' (schedule H 40) "
                  "0.15 m above it; owner Q-61 C(2) HOLD; designer D-03"),
    # R2: unlabelled members (owner Q-61 C(4)); candidates = the labelled members on the same band
    dict(wall="1F-W04", member="BM-1F-032", mark="(none)", kind="BEAM", length=0.80, marks=[],
         candidates=[0.40], sources=[],
         evidence=f"{ST}: FIRST FLOOR ROOF SLAB band 0.20 from the B23 face to the column (0.80 m), B2 printed on the "
                  "north span only; re-read this run: no text within the span; candidate B2 H 40 (T-110 D-04)"),
    dict(wall="2F-W02", member="BM-2F-015", mark="(none)", kind="BEAM", length=0.92, marks=[],
         candidates=[0.75, 0.40], sources=[],
         evidence=f"{ST}: SECOND FLOOR ROOF SLAB top band east end span past the column, B3 (west) and B8 (middle) "
                  "printed, none on this span (re-read this run); candidates B8 H 75 / B3 H 40 (T-110 D-04)"),
    dict(wall="2F-W03", member="BM-2F-018", mark="(none)", kind="BEAM", length=0.26, marks=[],
         candidates=[0.40], sources=[],
         evidence=f"{ST}: vertical piece below the column, B1 printed on the span above only (re-read); candidate B1 H 40"),
    dict(wall="2F-W03", member="BM-2F-017", mark="(none)", kind="BEAM", length=0.26, marks=[],
         candidates=[0.40], sources=[], evidence="as BM-2F-018 (the second vertical piece)"),
    dict(wall="2F-W05", member="BM-2F-017", mark="(none)", kind="BEAM", length=1.24, marks=[],
         candidates=[0.40], sources=[], evidence="as BM-2F-018: the wall runs under the unlabelled piece"),
    dict(wall="2F-W07", member="BM-2F-016", mark="(none)", kind="BEAM", length=2.94, marks=[],
         candidates=[1.20, 0.40], sources=[],
         evidence=f"{ST}: west band south span 3.10 m, B15 (H 120) printed on the north span only (re-read this run); "
                  "candidates B15 H 120 or a 20 x 40 type (T-110 D-04)"),
    dict(wall="GF-W36", member="(not in the T-110 register)", mark="(none)", kind="BEAM", length=0.50, marks=[],
         candidates=[0.75, 0.50], sources=[],
         evidence=f"{ST}: GROUND FLOOR ROOF SLAB: the 0.20 band between the CB6 column (north face) and the start of the "
                  "B7 arc, closed by a line at the arc start; collinear with B4 (south of CB6); no text of its own; the "
                  "wall band lies exactly under it. NEW: this 0.50 m beam piece is in no T-110 register record "
                  "(concrete 0.20 x 0.50 x 0.50 .. 0.75 = 0.050 .. 0.075 m3 in no line): lane S"),
    # column-edge piece (CONFLICT of column outline between the disciplines), not 'nothing drawn'
    dict(wall="GF-W07", member="CB1 band / column box", mark="(column edge)", kind="BEAM", length=0.12, marks=["CB1"],
         sources=[], width_conflict=False,
         evidence=f"{ST}: the wall's east end: the architecture draws the column 0.20 wide, the structure draws the "
                  "CB1 band and its column box 0.35 wide (0.14 m more on the wall side); the 0.12 m "
                  "stretch is block under CB1 (H 75) if the architecture governs, concrete column if the structure "
                  "does: column-outline CONFLICT (T-217 rule: kept apart, never picked)",
         conflict_bound=(0.0, 0.75)),
]
DOME = [("1F-W11", 4.01), ("1F-W13", 2.98), ("1F-W13", 1.40), ("1F-W17", 0.44), ("1F-W18", 0.44), ("1F-W24", 1.02)]


def resolve_all():
    out = []
    for p in PIECES:
        fl = p["wall"][:2]
        if p.get("conflict_bound"):
            lo, d = p["conflict_bound"]
            hi = round(p["length"] * (STOREY[fl] - d), 6)
            r = {"status": H.HELD, "height_m": None, "bounds_m": (0.0, hi), "rule": "CONFLICT (column outline)",
                 "why": "block 0 (structure: column) .. under CB1 (architecture); never picked"}
        else:
            r = H.resolve_piece({"length_m": p["length"], "kind": p["kind"], "marks": p["marks"],
                                 "depth_sources": p["sources"], "width_conflict": p.get("width_conflict"),
                                 "candidate_depths_m": p.get("candidates"), "mark_depths_m": p.get("mark_depths")},
                                STOREY[fl])
        out.append({**p, "res": r})
    return out


def rewrite(s, closed):
    """Rewrite the closed pieces of one T-143 'members_above' string from CONFLICT to their printed depth; every other
    piece is left exactly as merged."""
    for mid, mark, d, h in closed:
        pat = re.compile(re.escape(mark) + r" " + re.escape(mid) + r" b (?:(?! BM-).)*?\[CONFLICT\]: (?:(?! BM-).)*?: "
                         r"(\d+\.\d+) m -> h HELD \(candidate [\d.]+\)")
        s, n = pat.subn(lambda m: f"{mark} {mid} b width-CONFLICT h {d} [CALCULATED]: {m.group(1)} m -> h {h:.2f}", s)
        if n == 0:
            raise SystemExit(f"closed piece {mark} {mid} not found")
    return s


def ledger(patch=None):
    """T-108 r2 pipeline, optionally with closed pieces rewritten; returns the by-wall CSV text."""
    orig = A.parse_pieces
    if patch:
        A.parse_pieces = lambda s: orig(rewrite(s, patch.get(s, [])) if s in patch else s)
    try:
        L, _ = A.build()
        return A.by_wall_csv(L)
    finally:
        A.parse_pieces = orig


def closed_by_string(res):
    t143 = {r["row_id"]: r for r in csv.DictReader((ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv")
                                                  .open(encoding="utf-8"))}
    patch = defaultdict(list)
    for p in res:
        if p["res"]["rule"] == "R4":
            s = t143[p["wall"]]["members_above"]
            k = (p["member"], p["mark"], p["res"]["depth_m"], p["res"]["height_m"])
            if k not in patch[s]:
                patch[s].append(k)
    return dict(patch), t143


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def to_csv(rs, cols=None):
    o = io.StringIO()
    cols = cols or list(rs[0])
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rs)
    return o.getvalue()


def build():
    res = resolve_all()
    patch, t143 = closed_by_string(res)
    before_txt = ledger()
    after_txt = ledger(patch)
    before, after = rows(before_txt), rows(after_txt)
    t108, t143r, hosts, t176, t215, *_ = B.inputs()
    t143p = {k: ({**v, "members_above": rewrite(v["members_above"], patch[v["members_above"]])}
                 if v["members_above"] in patch else v) for k, v in t143r.items()}
    reg_b = B.register(before, t143r, hosts, t176, t215)
    reg_a = B.register(after, t143p, hosts, t176, t215)
    v1 = list(csv.DictReader((ROOT / "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv").open(encoding="utf-8")))
    # the T-225 builder on the unchanged ledger must give register v1 exactly (same format, same numbers)
    same_v1 = to_csv(reg_b) == (ROOT / "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv").read_text(encoding="utf-8")
    vb = {r["wall_id"]: r for r in v1}
    delta = []
    QUANT = ("held_length_m", "height_weighted_m", "gross_m2", "gross_class", "deductions_m2", "net_m2", "net_class",
             "net_m3", "owner_status_class", "held_cause_class")
    for r in reg_a:
        b = vb[r["wall_id"]]
        ch = [k for k in QUANT if r[k] != b[k]]
        if ch:
            delta.append({"change": "; ".join(f"{k} {b[k] or '-'} -> {r[k] or '-'}" for k in ch),
                          "package": "T-226", **r, "verified_by_checker": "no"})
    # pieces table
    pt = []
    for p in res:
        r = p["res"]
        b = r.get("bounds_m")
        pt.append({"wall_id": p["wall"], "member": p["member"], "mark": p["mark"], "piece_length_m": f"{p['length']:.2f}",
                   "storey_m": f"{STOREY[p['wall'][:2]]:.2f}", "rule": r["rule"], "status": r["status"],
                   "owner_class": RV.status_class(r["status"]),
                   "height_m": "" if r.get("height_m") is None else f"{r['height_m']:.3f}",
                   "held_bound_m2 (not a quantity)": f"{b[0]:.3f} .. {b[1]:.3f}" if b else "",
                   "dependency": r.get("dependency", ""), "why": r["why"], "evidence": p["evidence"]})
    for w, L in DOME:
        pt.append({"wall_id": w, "member": "DOME_OPENING+RING (T-139 face)", "mark": "-", "piece_length_m": f"{L:.2f}",
                   "storey_m": "4.20", "rule": "R1", "status": "HELD", "owner_class": "HELD", "height_m": "",
                   "held_bound_m2 (not a quantity)": "", "dependency": "",
                   "why": "under the open dome ring: top of wall from the dome / ring details = T-227 (d), not this package",
                   "evidence": "T-143 members_above (T-139 face over the piece)"})
    # before / after by floor x thickness x type (R-T225-1 totals)
    tb, ta = RV.totals(before), RV.totals(after)
    ba = []
    for k in sorted(set(tb) | set(ta), key=lambda k: ("GF1F2F".index(k[0]), k[1], k[2])):
        x, y = tb.get(k, {}), ta.get(k, {})
        names = sorted(set(x) | set(y))
        row = {"floor": k[0], "t_m": k[1], "block_type": k[2]}
        for n in names:
            if n == "walls":
                row["walls"] = int(y.get(n, x.get(n, 0)))
                continue
            row[f"{n} before"] = f"{x.get(n, 0):.3f}"
            row[f"{n} after"] = f"{y.get(n, 0):.3f}"
        ba.append(row)
    cols = ["floor", "t_m", "block_type", "walls"]
    for r in ba:
        for c in r:
            if c not in cols:
                cols.append(c)
    ba = [{c: r.get(c, "0.000") for c in cols} for r in ba]
    # D-12 m3 ranges (net established rows only; gross / net m2 unchanged by D-12)
    d12 = []
    reg_by = {r["wall_id"]: r for r in reg_a}
    for c in csv.DictReader((ROOT / "research/agents_t117/D12_CONFLICT_RUNS.csv").open(encoding="utf-8")):
        for hr in (x.strip() for x in c["hand_rows"].split("+")):
            r = reg_by[hr]
            net = float(r["net_m2"]) if r["net_m2"] else None
            dd = H.d12_range(net, float(c["t_drawn_m"]), float(c["t_by_note_s2_m"]), r["block_type"])
            d12.append({"wall_id": hr, "floor": r["floor"], "block_type": r["block_type"], "run": c["engine_piece"],
                        "t_drawn_m": c["t_drawn_m"], "t_by_note_m": c["t_by_note_s2_m"],
                        "net_m2": r["net_m2"] or "HELD", "net_class": r["net_class"],
                        "m3_at_drawn": "" if dd["m3_drawn"] is None else f"{dd['m3_drawn']:.3f}",
                        "m3_at_note": "" if dd["m3_note"] is None else f"{dd['m3_note']:.3f}",
                        "d_m3": "" if dd["d_m3"] is None else f"{dd['d_m3']:.3f}", "status": dd["status"],
                        "flags": ";".join(dd["flags"]), "gross_m2_unchanged": r["gross_m2"]})
    sa = RV.gap(after)
    est = lambda R, s: round(sum(float(r["net_m2"] or 0) for r in R if r["net_status"] == s), 3)
    summ = {
        "pipeline_reproduces_T108_BY_WALL": before_txt == (ROOT / "research/agents_t108/T108_BY_WALL.csv").read_text(encoding="utf-8"),
        "builder_reproduces_register_v1": same_v1,
        "pieces": len(PIECES), "pieces_closed_R4": sum(1 for p in res if p["res"]["rule"] == "R4"),
        "pieces_held": {k: sum(1 for p in res if p["res"]["rule"] == k) for k in ("R2", "R3", "CONFLICT (column outline)")},
        "dome_pieces_T227": len(DOME),
        "walls_changed": [d["wall_id"] for d in delta],
        "net_established_m2": {s: {"before": est(before, s), "after": est(after, s)} for s in RV.ESTABLISHED},
        "gross_established_m2": {"before": round(sum(float(r["gross_m2"] or 0) for r in before if r["gross_status"] in RV.ESTABLISHED), 3),
                                 "after": round(sum(float(r["gross_m2"] or 0) for r in after if r["gross_status"] in RV.ESTABLISHED), 3)},
        "gap_after": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in sa.items() if k in ("gap", "reconstructed")},
        "d12_rows": len(d12), "d12_m3_range_on_established_net": {
            "at_drawn": round(sum(float(x["m3_at_drawn"]) for x in d12 if x["m3_at_drawn"]), 3),
            "at_note": round(sum(float(x["m3_at_note"]) for x in d12 if x["m3_at_note"]), 3)},
        "verified_by_checker": 0,
    }
    return {"register_delta.csv": to_csv(delta), "PIECE_RESOLUTION.csv": to_csv(pt), "BEFORE_AFTER.csv": to_csv(ba, cols),
            "D12_M3_RANGE.csv": to_csv(d12), "summary.json": json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = build()
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(files["summary.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
