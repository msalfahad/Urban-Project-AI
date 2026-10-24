"""T-272 Alsenan: ground-beam stirrups (boundary G.B and the 17 main-house exterior runs) on the merged T-265 run
geometry (committed ledgers only; no private file is read here). Development villa, not an accuracy claim.

Drawing facts (own read this run, Drive "Alsenan chalet project" / "ST7757.pdf", 100 + 400 dpi):
  p.13 'Ground Beams. for exterior walls' (1:20): 30 wide, depth 'FOLLOW ARCH.' (D 0.95 settled by T-253, Checker
       CONFIRMED); ONE closed link 'ø8/15cm', 2 vertical legs (the 'X' at mid-depth is the side-bar leader, not a
       cross-tie), corners drawn as curves, a hook PAIR drawn at the top right corner (two short S-REIN.D strokes
       turning into the core: a 135-degree shape, angle not printed), tails not dimensioned; no spacing zones, no first-stirrup position, no beam
       elevation for ground beams anywhere on pp.13-14.
  p.14 'TYPICAL BOUNDARY WALL' section A-A (N.I.S): upper G.B 20 x 40, 'ø8/20 STIRRUPS' (unit not written on the
       label; every dimension on the sheet is in cm: '40', '20 x 30', '130x80x30'), link drawn as a closed rectangle
       with sharp corners and NO hook or overlap (vector: 4 straight strokes, the long sides shared with the column
       bars that run through the band); 20 x 30 boundary columns pass through the band (count / positions
       'SEE ARCH PLAN', none drawn on either plan: M4, T-065 / T-253).
  p.13 'TYP. DETAIL OF ISOLATED FOOTING' (right) draws a ground beam in elevation: links at a regular pitch, the first
       about 0.57 pitch from each column face (undimensioned, not to scale; P8-N03 'do not scale'): QA only.
  p.8 note 22: cover >= 2.5 cm beams, >= 7 cm against soil (minimums); no bend, hook, link-closure or fabrication
       note anywhere (D1.1 source search, 4055 DXF texts + OCR pp.9-16, re-confirmed visually on pp.13-14 here).
Owner AD-4 (2026-10-08): hook angle = drawn shape only; hook extension BLOCKED unless the project dimensions it; code
hook values QA only. Designer list D-37 (link hooks) already carries the request.
Writes LEDGER_T272.csv and summary.json next to this file when run as a script.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t272_stirrups as S  # noqa: E402

T265 = HERE.parent / "agents_t265" / "LEDGER_T265.csv"
T242_INPUT = HERE.parent / "agents_t242" / "ALSENAN_GROUND_INPUT.json"
CLEAR = HERE / "CLEAR_SPANS_T272R2.json"     # r2: drawn clear spans + ring sweeps (t272_r2_extract.py, values only)
RING = "ARC:157+158"
QA_COVER_M = 0.025          # the printed minimum (note 22) used ONLY for the QA reading

SPACING_M = {"GB_EXTERIOR": 0.15, "BOUNDARY_GB": 0.20}

SHAPES = {
    "GB_EXTERIOR": {
        "b_m": 0.30, "h_m": 0.95, "d_mm": 8, "closure": "HOOKS",
        "cover": S.facet(S.MINIMUM_ONLY, 2.5, "ST7757.pdf p.8 note 22 (>= 2.5 cm; >= 7 cm against soil)", unit="cm"),
        "bend_radius": S.facet(S.NOT_PRINTED),
        "hook_angle": S.facet(S.SHAPE_ONLY, ref="ST7757.pdf p.13 exterior GB section: hook drawn at the top corner"),
        "hook_ext": S.facet(S.NOT_PRINTED)},
    "BOUNDARY_GB": {
        "b_m": 0.20, "h_m": 0.40, "d_mm": 8, "closure": "NONE_DRAWN",
        "cover": S.facet(S.MINIMUM_ONLY, 2.5, "ST7757.pdf p.8 note 22 (>= 2.5 cm; >= 7 cm against soil)", unit="cm"),
        "bend_radius": S.facet(S.NOT_PRINTED),
        "hook_angle": S.facet(S.NOT_PRINTED),
        "hook_ext": S.facet(S.NOT_PRINTED)},
}
COVER_CASES_M = {"beams >= 2.5 cm": 0.025, "against soil >= 7 cm": 0.07}

FIELDS = ["run", "family", "length_m", "clear_pieces_m", "split_by", "d_mm", "spacing_m", "count_low", "count_half_spacing_reading", "count_high",
          "t265_count", "count", "count_status", "count_basis", "cut_length_m", "cut_length_status",
          "cut_length_held", "kg_per_m", "kg", "kg_status", "qa_sharp_perimeter_m", "qa_kg_at_high_count_no_hooks",
          "qa_status", "r1_through_low", "r1_through_high"]


def _ring():
    import math
    d = json.loads(T242_INPUT.read_text(encoding="utf-8"))
    band = [a for a in d["arc_bands"] if a["arc_band"] == RING][0]
    return band["r_in_m"], band["r_out_m"], math


def main(write=True):
    runs = [r for r in csv.DictReader(T265.open(encoding="utf-8")) if r["component"] == "STIRRUP_COUNT"]
    r_in, r_out, math = _ring()
    clear = json.loads(CLEAR.read_text(encoding="utf-8"))
    rows = []
    for r in runs:
        fam, run, L = r["family"], r["member"], float(r["length_m"])
        s = SPACING_M[fam]
        through = S.count_envelope([(L, s)])
        split_by = ""
        if fam == "BOUNDARY_GB":
            env = dict(through, count=None, status=S.HELD, pieces_m=[L],
                       basis="boundary columns 20 x 30 pass through the band, count / positions not printed (M4): "
                             "no count envelope; [low, high] shown is the run WITHOUT columns, a reading only; "
                             + through["basis"])
        elif run == RING:
            rr = clear["ring_radial"]["pieces"]
            faces = {"inner": clear["ring"]["157"]["face_pieces_m"], "outer": clear["ring"]["158"]["face_pieces_m"]}
            env = S.ring_envelope(rr, s, faces)
            env["half_spacing_reading"] = math.ceil(L / s - S.EPS)
            env["pieces_m"] = [p["inner_arc_m"] for p in rr]
            split_by = "+".join(clear["ring_radial"]["blocked_by"])
            r_c = (r_in + r_out) / 2.0
            through = S.curved_count_envelope(L / r_c, r_in, r_out, s)      # r1 reading (one run, face arcs scaled)
        else:
            sp = clear["spans"][run]
            if abs(sp["face_to_face_m"] - L) > 5e-4:
                raise SystemExit(f"{run}: clear-span extraction {sp['face_to_face_m']} != T-265 length {L}")
            pieces = S.clear_pieces(L, [(t["from_face_m"], t["to_face_m"]) for t in sp["tees"]])
            assert [round(x, 4) for x in pieces] == sp["clear_pieces_m"], run
            env = S.pieces_envelope(pieces, s)
            split_by = "+".join(t["band_id"] for t in sp["tees"])
        rec = S.stirrup_run(run, fam, env, SHAPES[fam], qa_cover_m=QA_COVER_M)
        rec.update(length_m=L, spacing_m=s, t265_count=r["n_bars"] or "HELD",
                   cut_length_held="; ".join(rec["cut_length_held"]),
                   clear_pieces_m=" + ".join(f"{x:.4f}" for x in env["pieces_m"]), split_by=split_by,
                   r1_through_low=through["low"], r1_through_high=through["high"])
        if run == RING:
            rec["ring_face_reading"] = env["face_reading"]
        rows.append(rec)

    ext = [x for x in rows if x["family"] == "GB_EXTERIOR"]
    bnd = [x for x in rows if x["family"] == "BOUNDARY_GB"]
    t265_lo = sum(int(x["t265_count"].split("..")[0]) for x in ext)
    t265_hi = sum(int(x["t265_count"].split("..")[1]) for x in ext)
    summary = {
        "policy": S.POLICY_ID,
        "inputs": ["research/agents_t265/LEDGER_T265.csv", "research/agents_t242/ALSENAN_GROUND_INPUT.json (ring radii)",
                   "research/agents_t272/CLEAR_SPANS_T272R2.json (r2 drawn clear spans, ring sweeps)"],
        "unit_mass": {"method": S.UNIT_MASS_CFG["method"], "d8_kg_per_m": round(S.UM.kg_per_m(8, S.UNIT_MASS_CFG), 6)},
        "exterior": {
            "runs": len(ext), "length_m": round(sum(x["length_m"] for x in ext), 4),
            "count_envelope": [sum(x["count_low"] for x in ext), sum(x["count_high"] for x in ext)],
            "half_spacing_reading": sum(x["count_half_spacing_reading"] for x in ext),
            "t265_range": [t265_lo, t265_hi],
            "r1_through_envelope_superseded": [sum(x["r1_through_low"] for x in ext),
                                               sum(x["r1_through_high"] for x in ext)],
            "runs_split_by_framing_beams": sorted(x["run"] for x in ext if x["split_by"] and x["run"] != RING),
            "count_status": "HELD (end rule not printed)",
            "cut_length_status": "HELD", "cut_length_held": SHAPES_HELD("GB_EXTERIOR"),
            "kg": None, "kg_status": "HELD",
            "qa_kg_at_high_count_no_hooks": round(sum(x["qa_kg_at_high_count_no_hooks"] for x in ext), 3),
        },
        "boundary": {
            "runs": len(bnd), "length_m": round(sum(x["length_m"] for x in bnd), 4),
            "count_status": "HELD (M4 columns; end rule)", "no_column_reading": [sum(x["count_low"] for x in bnd),
                                                                               sum(x["count_high"] for x in bnd)],
            "cut_length_status": "HELD", "cut_length_held": SHAPES_HELD("BOUNDARY_GB"),
            "kg": None, "kg_status": "HELD",
            "qa_kg_at_no_column_high_count_no_hooks": round(sum(x["qa_kg_at_high_count_no_hooks"] for x in bnd), 3),
        },
        "design_flags": {fam: S.design_flags(SHAPES[fam], COVER_CASES_M) for fam in SHAPES},
        "ring": {"r_in_m": r_in, "r_out_m": r_out, "t265_centreline_arc_m": 6.0873,
                 "split_at": clear["ring_radial"]["blocked_by"],
                 "radial_sweeps": clear["ring_radial"]["pieces"],
                 "count_envelope": [[x for x in rows if x["run"] == RING][0]["count_low"],
                                    [x for x in rows if x["run"] == RING][0]["count_high"]],
                 "drawn_face_pieces_net_of_column_outlines_m": {
                     "inner": clear["ring"]["157"]["face_pieces_m"], "outer": clear["ring"]["158"]["face_pieces_m"]},
                 "face_reading": [x for x in rows if x["run"] == RING][0]["ring_face_reading"],
                 "column_outline_on_arc_m": {"inner": clear["ring"]["157"]["columns_on_arc"],
                                             "outer": clear["ring"]["158"]["columns_on_arc"]},
                 "drawn_arc_m": {"inner": clear["ring"]["157"]["drawn_arc_m"],
                                 "outer": clear["ring"]["158"]["drawn_arc_m"]}},
    }
    if write:
        with (HERE / "LEDGER_T272.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for x in rows:
                w.writerow(x)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return rows, summary


def SHAPES_HELD(fam):
    return S.cut_length(SHAPES[fam])[1]


if __name__ == "__main__":
    rows, summary = main(write=True)
    print(json.dumps(summary, indent=1, ensure_ascii=False))
