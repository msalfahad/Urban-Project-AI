"""T-332 Alsenan: the merged formwork r5 faces (T-308) bound to the ARCH_TAKEOFF_V3.0.21 concrete lines, the faces that
merges after r5 re-opened re-measured from the drawing, the totals closed back to formwork r3 (1,078.274 m2) by named
steps, and the FILL table T-199 consumes unchanged.

    python3 -I research/agents_t332/t332_alsenan.py            # build in memory and print the summary
    python3 -I research/agents_t332/t332_alsenan.py --write    # write the committed outputs

Inputs (all committed, read only): research/agents_t308/T199_FORMWORK_BY_LINE_T308.json + FORMWORK_R5_BY_FACE_T308.csv
(r5, T-308 MERGED efb38618), research/agents_t163/FORMWORK_LINES.csv (r3, T-163 MERGED 659f889f),
research/agents_t264/FORMWORK_LINES_R4.csv + FORMWORK_DELTA_R3_R4.csv (r4, T-264 MERGED 90203feb),
research/agents_t311/PARAPET_RUN_LEDGER_T311.csv (T-311 MERGED bd7b8c23), this folder's CANDIDATE_V3021_CONCRETE_LINES.json
(t332_candidate.py on an own V3.0.21 run) and ALSENAN_T332_INPUT.json (t332_extract.py on 'ST7757 dxf.dxf').
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t332_rules as R  # noqa: E402

R5_JSON = ROOT / "research/agents_t308/T199_FORMWORK_BY_LINE_T308.json"
R5_FACES = ROOT / "research/agents_t308/FORMWORK_R5_BY_FACE_T308.csv"
R3_CSV = ROOT / "research/agents_t163/FORMWORK_LINES.csv"
R4_CSV = ROOT / "research/agents_t264/FORMWORK_LINES_R4.csv"
R4_DELTA = ROOT / "research/agents_t264/FORMWORK_DELTA_R3_R4.csv"
PARAPET = ROOT / "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv"
CAND = HERE / "CANDIDATE_V3021_CONCRETE_LINES.json"
INP = HERE / "ALSENAN_T332_INPUT.json"

POOL_WALLS = "L-15a128c38982af899894"
POOL_BASE = "L-36efa902da4263479e0b"
F8_LINE = "L-10f3cd1eb0f81a3892f2"
F8_FORMED = "R4-012.L-10f3cd1eb0f81a3892f2"

# printed levels used (all merged, Checker-verified): pool base top -0.90, base underside -1.30, rim +0.30 (T-183 r2,
# ST p.7 + the NW elevation cut); existing ground at the pool +-0.00 (T-320: walls 2.121 m3 below EG = band 2.356726 x
# 0.90); F8 footing H 0.50 on the p.9 schedule, footing top -0.83 (T-320 pit chain), wholly inside the pool envelope's
# depth (-1.50 .. EG) where the envelope covers it on plan.
POOL_BASE_T, POOL_WALL_H, POOL_ABOVE_EG, POOL_BELOW_EG = 0.40, 1.20, 0.30, 0.90
F8_H = 0.50


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r6(x):
    return None if x is None else round(float(x), 6)


def load_candidate():
    c = json.loads(CAND.read_text(encoding="utf-8"))
    lines = [{"line_id": l["line_id"], "element_id": l["element_id"], "item_code": l["item_code"],
              "state": l["evidence_state"], "quantity": l["measured_net"], "low": l.get("bounded_low"),
              "high": l.get("bounded_high")} for l in c["lines"]]
    return c, lines


def r5_faces():
    d = json.loads(R5_JSON.read_text(encoding="utf-8"))
    faces = []
    for l in d["lines"]:
        for f in l["faces"]:
            g = dict(f)
            g["line_id"] = l["concrete_line_id"]
            g["element_id"] = l["element_id"]
            g["r5_line_state"] = l["concrete_state"]
            g["r5_item_code"] = l["item_code"]
            faces.append(g)
    for f in d["not_tied"]:
        g = dict(f)
        g["line_id"] = ""
        g["element_id"] = ""
        g["r5_line_state"] = ""
        faces.append(g)
    return d, faces


def remeasures(inp):
    """R-T332-3 deltas (face changed by a merge after r5) and the AGREES records (re-read, nothing moves)."""
    pool = inp["pool"]
    po, pw = pool["outer"]["perimeter"], pool["water"]["perimeter"]
    back = pool["outer"]["segments"][0]["len"]          # the straight back on the boundary-wall line (T-183 / T-320)
    deck = po - back                                    # = T-183's deck edge 8.997787
    f8 = inp["f8_vs_pool"]
    f8_in = sum(x["inside_envelope"] for x in f8["faces"])
    f8_all = sum(x["len"] for x in f8["faces"])
    ring = inp["lift_ring"]
    S183 = "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' S-BW 7C6 (outer D) / 7C5 (water D); ST p.7 pool detail"
    common = {"element": "POOL", "floor": "GF", "method": "E=G", "revision": "T-332 re-measure (T-183 r2 MERGED geometry)",
              "members": "POOL:POOL-1", "walk_face": ""}

    def pool_face(fid, line, item, kind, contact, status, alt, m2=None, lo=None, hi=None, note=""):
        return {"face_id": fid, "kind": "ADD", "cause": "T-183 r2 (MERGED) pool geometry never carried by r3 / r4 / r5 "
                "(r3 s.00 named it a follow-up) + T-320 (MERGED 5ddb2ba1) existing-ground split",
                "source": S183,
                "face": dict(common, item=item, face_kind=kind, contact=contact, status=status, alternative=alt,
                             m2=r6(m2), lo=r6(lo), hi=r6(hi), basis_note=note, line_id=line)}

    D = [
        {"face_id": "R4-340.WALLS", "kind": "REMOVE", "source": S183,
         "cause": "r4 placeholder 'pool walls (two faces) and floor edges' (HELD, no value) replaced by the measured faces"},
        {"face_id": "R4-340.BASE", "kind": "REMOVE", "source": S183,
         "cause": "r4 placeholder (HELD, no value) replaced by the measured base-edge faces"},
        pool_face("T332-POOL-WATER", POOL_WALLS, "pool water face, base top -0.90 to rim +0.30", "SIDE", "FORM",
                  "CALCULATED", "", m2=pw * POOL_WALL_H,
                  note=f"7C5 water perimeter {pw:.6f} (3.10 + 2 x 1.55 + pi 1.55) x 1.20; the void side, nothing to cast against"),
        pool_face("T332-POOL-OUT-ABOVE-EG", POOL_WALLS, "pool outer face above EG (0.00 .. +0.30), deck edge", "SIDE",
                  "FORM", "CALCULATED", "", m2=deck * POOL_ABOVE_EG,
                  note=f"deck edge = 7C6 perimeter {po:.6f} - back {back:.3f} = {deck:.6f} x 0.30 above the existing ground "
                  "(R-FW-GB-EXPOSED-1: nothing to cast against); the deck slab is cast later against the protected wall"),
        pool_face("T332-POOL-OUT-BURIED-F", POOL_WALLS, "pool outer wall face below EG (-0.90 .. 0.00), deck edge, FORMED",
                  "SIDE", "OQ10", "ALTERNATIVE", "OQ10_FORMED", m2=deck * POOL_BELOW_EG,
                  note=f"{deck:.6f} x 0.90; p.7 screed + membrane outside it: OQ-10 pair, never chosen"),
        pool_face("T332-POOL-OUT-BURIED-E", POOL_WALLS, "pool outer wall face below EG, EARTH_CAST", "SIDE", "EARTH",
                  "ALTERNATIVE", "OQ10_EARTH_CAST", m2=0.0),
        pool_face("T332-POOL-BASE-EDGE-F", POOL_BASE, "pool base edge (-1.30 .. -0.90), deck edge, FORMED", "SIDE", "OQ10",
                  "ALTERNATIVE", "OQ10_FORMED", m2=deck * POOL_BASE_T, note=f"{deck:.6f} x 0.40 (base under the walls, T-183)"),
        pool_face("T332-POOL-BASE-EDGE-E", POOL_BASE, "pool base edge, EARTH_CAST", "SIDE", "EARTH", "ALTERNATIVE",
                  "OQ10_EARTH_CAST", m2=0.0),
        pool_face("T332-POOL-BACK-WALL", POOL_WALLS, "pool back wall outer face on the boundary-wall line (-0.90 .. +0.30)",
                  "SIDE", "OQ10", "HELD", "", lo=0.0, hi=back * POOL_WALL_H,
                  note=f"back {back:.3f} x 1.20: the back face lies on the boundary-wall line (T-320 F-T320-05, Q-28 lower "
                  "band / pool back wall): what it is cast against is not established; HELD 0 .. back x 1.20"),
        pool_face("T332-POOL-BACK-BASE", POOL_BASE, "pool base edge on the boundary-wall line", "SIDE", "OQ10", "HELD", "",
                  lo=0.0, hi=back * POOL_BASE_T, note=f"back {back:.3f} x 0.40, same cause (Q-28)"),
        {"face_id": F8_FORMED, "kind": "REPLACE",
         "cause": "T-320 F-T320-02 (MERGED 5ddb2ba1): F8 collides with the pool envelope at the printed limit (CONFLICT); "
                  "the F8 faces inside the envelope leave the FORMED alternative for a HELD conflict face",
         "source": "'ST7757 dxf.dxf' S-FOOTINGS 1B24 (F8) vs S-BW 7C6 + 0.10 (p.7 layers), sheet translation 10EB / 7C2",
         "face": {"m2": r6((f8_all - f8_in) * F8_H),
                  "basis_note": f"2 (4.00 + 3.60) 0.50 = 7.600 less the faces inside the pool envelope "
                                f"({f8_in:.6f} m x 0.50 = {f8_in * F8_H:.6f})"}},
        {"face_id": "T332-F8-POOL-CONFLICT", "kind": "ADD",
         "cause": "T-320 F-T320-02 (MERGED): F8 / pool CONFLICT at the printed limit (designer item, T-183 interface 1)",
         "source": "'ST7757 dxf.dxf' 1B24 faces N / E inside 7C6 buffered 0.10",
         "face": {"element": "FOOTING", "floor": "FDN", "item": "F8 faces inside the pool envelope (CONFLICT)",
                  "face_kind": "SIDE", "contact": "OQ10", "alternative": "OQ10_FORMED", "method": "E=G",
                  "status": "HELD", "m2": None, "lo": 0.0, "hi": r6(f8_in * F8_H), "members": "FOOTING:F8",
                  "revision": "T-332 re-measure", "line_id": F8_LINE, "walk_face": "",
                  "basis_note": "; ".join(f"{x['face']} {x['inside_envelope']:.6f} m" for x in f8["faces"] if x["inside_envelope"])
                  + f" x 0.50; envelope overlap {f8['overlap_f8_envelope_m2']:.6f} m2 (T-320 1.616), outline overlap "
                  f"{f8['overlap_f8_outer_m2']:.6f} m2 (T-189 1.296442)"}},
        {"face_id": "R4-342", "kind": "REMOVE",
         "cause": "T-322 (MERGED d3bcd9d4) fixes the pit ring and the wall base (raft top): the aggregate row is replaced "
                  "by its two faces per metre of pit height",
         "source": "'ST7757 dxf.dxf' S-BW 10EB / 10EA, S-COL.BON 1099 / 1093 / 1096 / 1090; ST p.14"},
        {"face_id": "T332-LIFT-PIT-INNER", "kind": "ADD",
         "cause": "T-322 (MERGED): pit walls 20 on the raft top, pit depth 'as per lift manufacturer' (D-43)",
         "source": "'ST7757 dxf.dxf' 10EA 1.80 x 1.80 less the four columns",
         "face": {"element": "LIFT", "floor": "FDN", "item": "lift-pit wall pit-side face, per metre of pit height",
                  "face_kind": "SIDE", "contact": "FORM", "alternative": "", "method": "E=G", "status": "HELD",
                  "m2": None, "lo": None, "hi": None, "members": "LIFT:PIT", "revision": "T-332 re-measure",
                  "line_id": "", "walk_face": "",
                  "basis_note": f"{ring['inner']['not_on_a_column']:.3f} m2 per m of pit height (inner perimeter "
                                f"{ring['inner']['perimeter']:.2f} less {ring['inner']['perimeter'] - ring['inner']['not_on_a_column']:.2f} m "
                                "of column faces); height not printed (D-43): HELD, no value"},
         "tie_reason": "no candidate concrete line for the lift-pit walls (V3.0.21)"},
        {"face_id": "T332-LIFT-PIT-OUTER", "kind": "ADD",
         "cause": "T-322 (MERGED): outer face of the pit walls below EG, membrane + board outside it (OQ-10)",
         "source": "'ST7757 dxf.dxf' 10EB 2.20 x 2.20 less the four columns",
         "face": {"element": "LIFT", "floor": "FDN", "item": "lift-pit wall outer face, per metre of pit height (OQ-10)",
                  "face_kind": "SIDE", "contact": "OQ10", "alternative": "OQ10_FORMED", "method": "E=G", "status": "HELD",
                  "m2": None, "lo": None, "hi": None, "members": "LIFT:PIT", "revision": "T-332 re-measure",
                  "line_id": "", "walk_face": "",
                  "basis_note": f"{ring['outer']['not_on_a_column']:.3f} m2 per m of pit height (outer perimeter "
                                f"{ring['outer']['perimeter']:.2f} less {ring['outer']['perimeter'] - ring['outer']['not_on_a_column']:.2f} m "
                                "of column faces); height not printed (D-43) and OQ-10 open: HELD, no value"},
         "tie_reason": "no candidate concrete line for the lift-pit walls (V3.0.21)"},
    ]
    for r in csv.DictReader(io.StringIO(PARAPET.read_text(encoding="utf-8"))):
        D.append({"face_id": f"T332-PARAPET-{r['chain']}-{r['side']}", "kind": "ADD",
                  "cause": "T-311 (MERGED bd7b8c23): parapet RC part in NO concrete line (MISSING; T-319 QUEUED)",
                  "source": "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv (Checker Gate A 2026-10-28 22:09)",
                  "tie_reason": "NO_LINE: parapet RC concrete is a MISSING category (T-319), no line carries it",
                  "face": {"element": "PARAPET", "floor": r["roof_level"], "item": f"parapet {r['chain']} {r['side']} "
                           "cast faces (2 x RC height x centreline)", "face_kind": "SIDE", "contact": "FORM",
                           "alternative": "", "method": "G", "status": "HELD", "m2": None,
                           "lo": r6(r["formwork_m2_lo"]), "hi": r6(r["formwork_m2_hi"]), "members": f"PARAPET:{r['chain']}:{r['side']}",
                           "revision": "T-311 PARAPET_RUN_LEDGER_T311.csv", "line_id": "", "walk_face": "",
                           "basis_note": f"centreline {float(r['centreline_m']):.3f} m; RC height range (P1 upstand .. all RC); "
                                         f"material {r['material_status'][:40]}"}})
    agrees = [
        {"element": "FF raft (lift footing)", "merge": "T-322 MERGED d3bcd9d4", "source": "1B2B + p.9 row FF + p.14",
         "drawn": f"{inp['footings']['FF']['size'][0]:.2f} x {inp['footings']['FF']['size'][1]:.2f} x 0.55",
         "r5_face": "R4-026 FORMED 2 (4.60 + 4.50) 0.55 = 10.010", "after": "10.010 (unchanged)",
         "why": "raft = schedule = outline (DC); base on 0.05 screed over membrane over blinding: no form; the p.14 "
                "side build-up (membrane + board outside the face) does not settle OQ-10: pair kept"},
        {"element": "FF / footing blinding (DG-3521554d)", "merge": "T-322 / Checker downgrade", "source": "p.14",
         "drawn": "projection not printed", "r5_face": "none (blinding has no formwork row)", "after": "none",
         "why": "a blinding edge is not in any formwork revision and no footing base is formed: no face moves"},
        {"element": "F12 footing", "merge": "T-320 MERGED 5ddb2ba1", "source": "1ABF + p.9",
         "drawn": f"{inp['footings']['F12']['size'][0]:.2f} x {inp['footings']['F12']['size'][1]:.2f} x 0.70",
         "r5_face": "R4-018 FORMED 2 (4.40 + 3.20) 0.70 = 10.640", "after": "10.640 (unchanged)",
         "why": "T-320 pit chain uses the same outline; F12 is 0.5998 m clear of FF (T-322): no shared face"},
        {"element": "ring ground beam ARC:157+158 (BAND0043)", "merge": "T-255 V3.0.19 (concrete end closure)",
         "source": "arcs 157 / 158", "drawn": f"157 R {inp['ring_ground_beam_arcs']['157']['r']:.3f} x "
         f"{inp['ring_ground_beam_arcs']['157']['sweep_deg']:.3f} deg = {inp['ring_ground_beam_arcs']['157']['len']:.6f} m; "
         f"158 R {inp['ring_ground_beam_arcs']['158']['r']:.3f} x {inp['ring_ground_beam_arcs']['158']['sweep_deg']:.3f} deg = "
         f"{inp['ring_ground_beam_arcs']['158']['len']:.6f} m",
         "r5_face": "R4-148 6.239008 CALC; R4-149 5.963657 FORMED", "after": "unchanged",
         "why": "T-255 moved the concrete END closure (+0.012043 m3: ends close on the drawn straight-beam face and neck "
                "columns); an end that closes on a drawn face has no formed end face, and both arc faces are measured "
                "on the full drawn arcs already (6.567377 x 0.95 = 6.239008)"},
        {"element": "slab panels GF-081 (hatch 298) / GF-141 (hatch 280)", "merge": "T-323 MERGED 4410fb03",
         "source": "T-139 faces (panel by member faces)", "drawn": "4.1176 / 7.3009 m2",
         "r5_face": "PANEL:GF-081 / PANEL:GF-141 soffits", "after": "unchanged",
         "why": "r5 soffits are the T-139 panels (member faces), never the hatch: the hatch-cut does not reach formwork"},
        {"element": "sunken panels (275 / 276 / 280 / 287 / 298 / 5BF)", "merge": "T-224 r2 MERGED f8180b18",
         "source": "slab_step_v2 StepDetail; no printed step section", "drawn": "no free edge on any sunken panel",
         "r5_face": "sunken-panel faces HELD x 50.885 m (D-41)", "after": "HELD (unchanged)",
         "why": "all six are beam-framed: the step faces are beam sides above / below the drop d (D-41 unprinted)"},
    ]
    return D, agrees


def chain(bound_rows):
    """CALCULATED (methods G and E=G) by element type: r3 -> r4 -> r4 source rows -> r5 -> T-332, every step named."""
    def add(t, el, v):
        t[el] = t.get(el, 0.0) + v
    calc = lambda st, m: st == "CALCULATED" and m in ("G", "E=G")
    r3, r4 = {}, {}
    for r in csv.DictReader(io.StringIO(R3_CSV.read_text(encoding="utf-8"))):
        if calc(r["status"], r["method"]):
            add(r3, r["element"], float(r["m2"] or 0))
    for r in csv.DictReader(io.StringIO(R4_CSV.read_text(encoding="utf-8"))):
        if calc(r["status"], r["method"]):
            add(r4, r["element"], float(r["m2"] or 0))
    src, r5 = {}, {}
    steps = defaultdict(float)
    for r in csv.DictReader(io.StringIO(R5_FACES.read_text(encoding="utf-8"))):
        a = float(r["r4_m2"] or 0) if calc(r["r4_status"], r["method"]) else 0.0
        b = float(r["r5_m2"] or 0) if calc(r["r5_status"], r["method"]) else 0.0
        add(src, r["element"], a)
        add(r5, r["element"], b)
        if abs(b - a) > 1e-12:
            cause = r["rule"] or (f"T-293 ledger {r['ledger_tie']}" if r["ledger_tie"] != "TIED" else "T-293 ledger HELD")
            steps[("r4 source -> r5", r["element"], cause)] += b - a
    t332 = {}
    for r in bound_rows:
        if r.get("status") == "CALCULATED" and r.get("method") in ("G", "E=G"):
            add(t332, r["element"], float(r["m2"]))
    # r3 -> r4 by the T-264 delta rows (their own calc_delta column), r4 -> source by the T-282 / T-290 rows
    for r in csv.DictReader(io.StringIO(R4_DELTA.read_text(encoding="utf-8"))):
        # CALCULATED rows only (the r3 / r4 E rows are unchanged, so a changed CALCULATED row is a G / E=G row)
        a = float(r["r3_m2"] or 0) if r["r3_status"] == "CALCULATED" else 0.0
        b = float(r["r4_m2"] or 0) if r["r4_status"] == "CALCULATED" else 0.0
        d = b - a
        if abs(d) > 1e-12:
            steps[("r3 -> r4", r["element"], r["cause"][:90])] += d
    for el in set(src) | set(r4):
        d = src.get(el, 0.0) - r4.get(el, 0.0)
        if abs(d) > 1e-9:
            why = {"GROUND_BEAM": "T-282 ground-beam edge delta row 170+7C3#4 side B (+0.285)",
                   "STAIR": "T-290 stair pointer rows MS2-LD -0.065 / RS-A -0.040"}.get(
                el, "unrounded recomputation of 3-dp printed r4 rows (T-293 part 2, each row <= 0.0005)")
            steps[("r4 -> r4 source rows", el, why)] += d
    els = sorted(set(r3) | set(r4) | set(src) | set(r5) | set(t332))
    table = []
    for el in els:
        row = {"element": el, "r3": r6(r3.get(el, 0.0)), "r4": r6(r4.get(el, 0.0)), "r4_source": r6(src.get(el, 0.0)),
               "r5": r6(r5.get(el, 0.0)), "t332": r6(t332.get(el, 0.0))}
        for a, b, name in (("r3", "r4", "r3 -> r4"), ("r4", "r4_source", "r4 -> r4 source rows"),
                           ("r4_source", "r5", "r4 source -> r5")):
            named = sum(v for (s, e, _), v in steps.items() if s == name and e == el)
            res = row[b] - row[a] - named
            row[f"residual {name}"] = r6(res)
        table.append(row)
    tot = {k: r6(sum(r[k] for r in table)) for k in ("r3", "r4", "r4_source", "r5", "t332")}
    return table, {f"{s} | {e} | {c}": r6(v) for (s, e, c), v in sorted(steps.items())}, tot


def build():
    cand, lines = load_candidate()
    r5, faces = r5_faces()
    inp = json.loads(INP.read_text(encoding="utf-8"))
    tied = [f for f in faces if f["line_id"]]
    untied = [f for f in faces if not f["line_id"]]
    bound = R.rebind(tied, lines)
    for f in untied:
        g = dict(f)
        R.check_face(g)
        g.update(tie="NO_LINE" if f.get("tie") == "NO_CANDIDATE_LINE" else f.get("tie"), new_line_id="", new_state="",
                 tie_reason=f.get("tie_reason", ""))
        bound.append(g)
    by_line = {l["line_id"]: l for l in lines}
    D, agrees = remeasures(inp)
    # ADD faces on a line take that line's V3.0.21 identity; on no line NO_LINE with the reason
    for d in D:
        if d["kind"] == "ADD":
            f = d["face"]
            lid = f.get("line_id") or ""
            if lid:
                l = by_line[lid]
                f.update(tie="SAME", new_line_id=lid, new_state=l["state"], new_item_code=l["item_code"],
                         element_id=l["element_id"])
            else:
                f.update(tie="NO_LINE", new_line_id="", new_state="", tie_reason=d.get("tie_reason", ""))
    after, applied = R.apply_deltas(bound, D)
    clo = R.closure(bound, after)
    ch_table, ch_steps, ch_tot = chain([r for r in after if r.get("status") != "REMOVED"])
    calc = lambda s: (s["m2"] or 0.0) if s and s["status"] == "CALCULATED" and s["method"] in ("G", "E=G") else 0.0
    els = {r["face_id"]: r["element"] for r in after}
    named = defaultdict(float)
    for a in applied:
        d = calc(a["after"]) - calc(a["before"])
        if abs(d) > 1e-12:
            named[(els[a["face_id"]], a["face_id"])] += d
    for (el, fid), v in sorted(named.items()):
        ch_steps[f"r5 -> T-332 | {el} | {fid}"] = r6(v)
    for row in ch_table:
        n = sum(v for (el, _), v in named.items() if el == row["element"])
        row["residual r5 -> T-332"] = r6(row["t332"] - row["r5"] - n)
    return {"candidate": cand, "lines": lines, "r5": r5, "source": faces, "bound": bound, "after": after,
            "applied": applied, "agrees": agrees, "closure": clo, "chain": ch_table, "chain_steps": ch_steps,
            "chain_totals": ch_tot, "input": inp}


def _rows_csv(rows, cols):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: ("" if r.get(c) is None else (f"{r[c]:.6f}" if isinstance(r.get(c), float) else r[c])) for c in cols})
    return s.getvalue()


FACE_COLS = ["face_id", "element", "floor", "item", "face_kind", "contact", "alternative", "method", "status",
             "m2", "lo", "hi", "held_from", "line_id", "element_id", "r5_line_state", "tie", "new_line_id",
             "new_item_code", "new_state", "tie_reason", "rule", "delta_cause", "delta_source", "basis_note"]


def outputs(B):
    after = B["after"]
    src = {f["face_id"]: f for f in B["source"]}
    for r in after:
        s = src.get(r["face_id"])
        r.setdefault("r5_line_state", "" if s is None else s.get("r5_line_state", ""))
    fill = R.fill_table(after)
    fill_rows = []
    for lid, e in fill.items():
        for k, v in sorted(e["totals"].items()):
            st, alt, m = k.split("|")
            fill_rows.append({"line_id": lid, "item_code": e["item_code"], "line_state": e["line_state"], "status": st,
                              "alternative": alt, "method": m, "faces": v["faces"], "m2": v["m2"], "lo": v["lo"],
                              "hi": v["hi"], "held_from": v["held_from"],
                              "face_ids": " ".join(fid for fid in e["faces"]
                                                   if R.key(next(x for x in after if x["face_id"] == fid)) == k)})
    no_line = [r for r in after if r.get("tie") not in ("SAME", "REBOUND") and r.get("status") != "REMOVED"]
    rebound = [r for r in after if r.get("tie") == "REBOUND"]
    held_by_state = [r for r in after if "R-T332-2" in (r.get("rule") or "")]
    tot_before = R.totals([r for r in B["bound"]])
    tot_after = R.totals([r for r in after])
    tied_after = R.totals([r for r in after if r.get("tie") in ("SAME", "REBOUND")])
    cand = B["candidate"]
    live_without = sorted(l["line_id"] for l in B["lines"] if l["quantity"] is not None and l["line_id"] not in fill)
    summary = {
        "schema": "T332_SUMMARY_V1",
        "candidate": {"method": cand["candidate"], "lines_json_sha256": cand["candidate_lines_json_sha256"],
                      "lines_csv_sha256": cand["candidate_lines_csv_sha256"], "lines_total": cand["lines_in_candidate"],
                      "str_conc_lines": len(B["lines"]), "formwork_lines_in_candidate": cand["formwork_lines_in_candidate"]},
        "source": {"r5": "research/agents_t308 (T-308 MERGED efb38618)", "r5_candidate": B["r5"]["candidate"],
                   "faces": len(B["source"]), "tied_in_r5": sum(1 for f in B["source"] if f["line_id"])},
        "ties": {k: sum(1 for r in after if r.get("tie") == k) for k in sorted({r.get("tie") for r in after})},
        "rebound": [{"face_id": r["face_id"], "old": r["line_id"], "new": r["new_line_id"]} for r in rebound],
        "held_by_line_state_R-T332-2": [{"face_id": r["face_id"], "line": r["new_line_id"], "held_from": r["held_from"]}
                                        for r in held_by_state],
        "lines_with_faces": len(fill),
        "live_concrete_lines_without_faces": len(live_without),
        "live_concrete_lines_without_faces_ids": [
            {"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"]}
            for l in B["lines"] if l["line_id"] in set(live_without)],
        "totals_r5_bound": tot_before, "totals_t332": tot_after, "totals_t332_tied": tied_after,
        "closure": B["closure"], "deltas": B["applied"], "agrees": B["agrees"],
        "chain_by_element": B["chain"], "chain_steps": B["chain_steps"], "chain_totals": B["chain_totals"],
        "inputs_sha256": {str(p.relative_to(ROOT)): _sha(p) for p in (R5_JSON, R5_FACES, R3_CSV, R4_CSV, R4_DELTA, PARAPET,
                                                                       CAND, INP)},
    }
    consumer = {"schema": "T332_FORMWORK_BY_CONCRETE_LINE_V1", "candidate": cand["candidate"],
                "candidate_lines_json_sha256": cand["candidate_lines_json_sha256"],
                "revision": "FORMWORK_R5 (T-308) bound to V3.0.21 + T-332 re-measures",
                "rule": "faces never summed across status / alternative / method; HELD blank with its range or held_from, "
                        "never 0; scenario S1 rows never candidate faces; NO_LINE rows never in a line total",
                "lines": [dict(e, faces=[{c: next(x for x in after if x["face_id"] == fid).get(c) for c in FACE_COLS}
                                         for fid in e["faces"]]) for e in fill.values()],
                "no_line": [{c: r.get(c) for c in FACE_COLS} for r in sorted(no_line, key=lambda r: r["face_id"])]}
    return {
        "FORMWORK_T332_BY_FACE.csv": _rows_csv(sorted(after, key=lambda r: r["face_id"]), FACE_COLS),
        "T199_FILL_T332.csv": _rows_csv(fill_rows, ["line_id", "item_code", "line_state", "status", "alternative", "method",
                                                    "faces", "m2", "lo", "hi", "held_from", "face_ids"]),
        "T199_FORMWORK_BY_LINE_T332.json": json.dumps(consumer, indent=1, sort_keys=True) + "\n",
        "summary_t332.json": json.dumps(summary, indent=1, sort_keys=True) + "\n",
    }


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    B = build()
    out = outputs(B)
    if "--write" in a:
        for n, t in out.items():
            (HERE / n).write_text(t, encoding="utf-8")
    s = json.loads(out["summary_t332.json"])
    print(json.dumps({k: s[k] for k in ("candidate", "ties", "lines_with_faces", "live_concrete_lines_without_faces",
                                         "chain_totals")}, indent=1))
    print(json.dumps(s["totals_t332_tied"], indent=1))


if __name__ == "__main__":
    main()
