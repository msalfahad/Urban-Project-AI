"""T-633 builder (research, unwired): the 39 UNKNOWN rows of the B9 blockwork statement section (scorecard V11,
T-543/blockwork: reference 1,260.6895 vs engine 467.7925 m2; UNKNOWN 39 rows signed 231.6737245 m2; the 50 HELD rows
561.2232755 m2 are untouched) each given an own value and an evidence level (R-T633-1, t633_rules.py):

  - 22 opening rows: own masonry width from the architectural DXF by handle (T633_DRAWN.json, t633_extract.py), own
    printed heights where the DXF prints them (SE / NW elevation DIMENSIONs), the NW elevation jamb verticals for the
    rectangular part of the twin arched windows; heights the DXF lacks are cited (T-627 DWF bindings, the T-227 / T-238
    arch segment) or are the owner's door fallback Q-55 C (2.20 m, no printed head);
  - 1 his-only row: own census of every straight 1F window (12 jamb pairs, 5 at 0.60 m);
  - 16 arithmetic / family rows: reproduced from the T-543 decomposition (identity gross = length x mean height) or
    cited (drift, boundary family, parapet centrelines, projections).

Built and checked by tests/t633_blockwork_row_evidence (the wrapper's pytest is the only execution path). Nothing here
changes a candidate, engine, rule / knowledge version, registry or statement file; nothing is released.
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t633_rules as R  # noqa: E402

D = Decimal
SCORECARD = ROOT / "research/agents_t620/out/SCORECARD_T620.json"
SCORECARD_SHA = "4e26155f2ae48c3a442b3678f928b11c7609e67a18b601597978d159652a81e3"
T543 = ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json"
T543_SHA = "a4cfcdeb01aab26e38b543fa73c89c2999b54cbad85916d9fe6023aa0af4f721"
T627 = ROOT / "research/agents_t627/T627_DRAWN.json"
T627_SHA = "324b4d5b0a7d80f32eafe34c55716a8f338af8261cb1f73bb94c072ad4cc6439"
DRAWN = HERE / "T633_DRAWN.json"
OUT_JSON = HERE / "out" / "T633_ROW_EVIDENCE.json"
OUT_MD = HERE / "out" / "T633_ROW_EVIDENCE.md"
SECTION = "T-543/blockwork"
Q55C = D("2.20")
ARCH_SEGMENT = D("1.0088")   # T-238 census / T-227 r2 (Checker 21:11 VERIFIED outline): segment above the jambs

# statement row index -> how the own value is formed.
# opening rows: (kind, opening id, his w, his h, height source)
OPENING_ROWS = {
    11: ("height", "D-GF-06", "1.00", "2.40", "T627_DWF"),
    12: ("width", "D-GF-03", "1.00", "2.40", "Q55C"),
    24: ("height", "D-GF-10", "0.80", "2.40", "Q55C"),
    28: ("height", "D-GF-13", "1.00", "2.40", "Q55C"),
    29: ("engine_only", "D-GF-09", None, None, "Q55C"),
    33: ("width", "D-GF-08", "1.10", "2.40", "Q55C"),
    35: ("height", "W25", "1.00", "2.00", "T627_DWF"),
    37: ("outline", "W15", "1.55", "3.00", "NW_JAMB+ARCH"),
    38: ("outline", "W16", "1.55", "3.00", "NW_JAMB+ARCH"),
    39: ("height", "W24", "1.55", "2.00", "T627_DWF"),
    40: ("height", "W14", "2.45", "2.00", "PRINTED"),
    41: ("height", "W13", "1.20", "2.00", "PRINTED"),
    43: ("height", "D-1F-04", "0.80", "2.40", "Q55C"),
    45: ("height", "D-1F-07", "0.80", "2.40", "Q55C"),
    47: ("height", "D-1F-08", "0.90", "2.40", "Q55C"),
    48: ("height", "D-1F-09", "0.90", "2.40", "Q55C"),
    49: ("width", "D-1F-03", "0.90", "2.40", "Q55C"),
    50: ("height", "D-1F-03", "0.90", "2.40", "Q55C"),
    51: ("engine_only", "W18", None, None, "PRINTED"),
    52: ("engine_only", "D-1F-10", None, None, "Q55C"),
    53: ("engine_only", "D-1F-02", None, None, "Q55C"),
    54: ("his_only", None, "0.60", "0.80", "CENSUS"),
}
ENGINE_NOMINAL_W = {"D-GF-10": "0.80", "W24": "1.55", "W15": "1.55", "W16": "1.55"}   # engine census widths (T-559)
# arithmetic rows: index -> (floor or None, formula key)
ARITH_ROWS = {6: ("GF", "drift"), 8: ("GF", "height"), 62: ("GF", "residual"), 66: ("1F", "drift"),
              68: ("1F", "height"), 69: ("1F", "residual"), 72: ("2F", "drift"), 75: ("2F", "residual")}
PARAPET_ROWS = {  # index -> (his length, engine centreline (cited T-319 / T-488 runs), his height, kind)
    80: ("66.00", "58.55495", "1.00", "length"), 81: ("66.00", "58.55495", "0.50", "height"),
    82: ("42.85", "49.23265", "1.80", "length"), 83: ("42.85", "49.23265", "0.50", "height"),
    87: ("29.80", "29.050", "0.50", "height"),
}
CITED_ROWS = {
    76: ("REPRODUCED", "his one row length x 2.00 = 74.40, no opening; the engine books the boundary wall under "
                       "EXT.FENCE.WALL (F-STREET 14.84 + F-NORTH 83.1305 valued, 2 planes HELD): family placement"),
    78: ("REPRODUCED", "ST p.14 P1 detail RC upstand 0.30 m (T-319 / T-482 reads, cited) x engine centreline 136.83760 m "
                       "= 41.05128: concrete, never masonry"),
    79: ("CITED", "print rounding of the stored block alternatives at 6 dp (T-543)"),
    88: ("OWN_DXF+CITED", "his 7.50 x 5.50 row. Own DXF search of every printed DIMENSION of 7.40-7.60 / 5.45-5.55 m: "
                          "7.50 = GF plan 4E9, the east facade overall that holds the glazed opening W02 (6.33, HELD "
                          "D-53), not a masonry panel; 7.45 = GF plan 6C4; 5.50 = NW elevation chain 29D0, the GF storey "
                          "(+0.00 to +5.50), not an element; no 7.50 x 5.50 masonry element found (T-225 / T-543 agree)"),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load():
    for p, s in ((SCORECARD, SCORECARD_SHA), (T543, T543_SHA), (T627, T627_SHA)):
        if _sha(p) != s:
            raise R.RuleError(f"{p.name} changed: re-pin")
    sc = json.loads(SCORECARD.read_text(encoding="utf-8"))
    sec = next(x for x in sc["reference_lines"] if x["section_id"] == SECTION)
    t543 = json.loads(T543.read_text(encoding="utf-8"))
    return sec, t543, json.loads(T627.read_text(encoding="utf-8")), json.loads(DRAWN.read_text(encoding="utf-8"))


def own_opening(oid, src, drawn, t627):
    """(w, h or area, evidence, basis, width handles)."""
    if oid in ("W15", "W16"):
        pl = drawn["plan"][oid]
        tw = drawn["nw_twin"]
        hs = {v["jamb_height"] for v in tw.values()}
        ws = {v["width"] for v in tw.values()}
        if len(hs) != 1 or ws != {pl["width"]}:
            raise R.RuleError("NW twin jambs disagree with the plan width")
        h = D(hs.pop())
        w = D(pl["width"])
        area = w * h + ARCH_SEGMENT
        return w, area, "OWN_DXF+CITED", (f"plan jambs {' / '.join(pl['jamb_handles'])} {w}; NW elevation jambs "
                                          f"{tw['pair_east']['jamb_handles']} / {tw['pair_west']['jamb_handles']} "
                                          f"{h} (chain 2E22 / 2DE7 shows 155); + arch segment {ARCH_SEGMENT} cited "
                                          f"(T-227 / T-238)"), pl["jamb_handles"]
    pl = drawn["plan"][oid]
    w = D(pl["width"])
    hnd = pl.get("jamb_handles") or pl.get("face_handles")
    if src == "Q55C":
        if pl["kind"] != "DOOR":
            raise R.RuleError("Q-55 C is a door fallback")
        return w, Q55C, "OWNER_RULE", f"plan wall-face ends {' / '.join(hnd)} {w}; head Q-55 C 2.20 (no printed head)", hnd
    if src == "PRINTED":
        p = drawn["printed"][oid]
        if not p["chain_inside_width_segment"]:
            raise R.RuleError(f"{oid}: height chain not bound to the opening")
        h = (D(p["height_shown"]) / 100).quantize(D("0.01"))
        return w, h, "OWN_DXF", (f"plan jambs {' / '.join(hnd)} {w}; {p['view']} DIMENSION {p['height_dim']} shows "
                                 f"{p['height_shown']} (measured {p['height_measured']})"), hnd
    if src == "T627_DWF":
        hits = [b for v, vb in t627["views"].items() for b in vb.get(oid, []) if b["status"] == "BOUND"
                and b["match"] == "opening"]
        hs = {D(b["height"]).quantize(D("0.01")) for b in hits}
        if len(hs) != 1:
            raise R.RuleError(f"{oid}: cited DWF height not single")
        h = hs.pop()
        return w, h, "OWN_DXF+CITED", (f"plan {' / '.join(hnd)} {w}; head {h} from the T-627 DWF binding (cited, not "
                                       f"re-read: the .dwf was not opened this run)"), hnd
    raise R.RuleError(f"unknown height source {src}")


def build():
    sec, t543, t627, drawn = load()
    rows = sec["rows"]
    unknown = [i for i, r in enumerate(rows) if r["status"] == "UNKNOWN"]
    held = [i for i, r in enumerate(rows) if r["status"] == "HELD"]
    covered = set(OPENING_ROWS) | set(ARITH_ROWS) | set(PARAPET_ROWS) | set(CITED_ROWS)
    if sorted(covered) != unknown:
        raise R.RuleError(f"row coverage mismatch: {sorted(set(unknown) ^ covered)}")
    dec = {r["decomposition"]["floor"]: r["decomposition"] for r in t543["rows"]
           if r.get("decomposition") and "floor" in r["decomposition"]}
    out = []
    for i in unknown:
        r = rows[i]
        stated = D(r["delta"])
        rec = {"index": i, "name": r["name"], "statement_class": r["class"], "statement_delta": str(stated),
               "statement_sub": r["sub"]}
        if i in OPENING_ROWS:
            kind, oid, wh, hh, src = OPENING_ROWS[i]
            if kind == "his_only":
                cen = drawn["census_1f_windows"]
                n060 = sum(1 for c in cen if c["width"] == "0.600")
                his060 = 6          # his 1F rows e2..e7: six 0.60 x 0.80 (T-559 PAIRS: five matched + this one)
                own = R.opening_delta("his_only", w_his=wh, h_his=hh, census_has_opening=(n060 >= his060))
                rec.update(own_delta=str(own), evidence="OWN_DXF", class_proposed=r["class"],
                           basis=f"own census of every straight 1F window: {len(cen)} jamb pairs, {n060} at 0.600 m "
                                 f"(W19 .. W23); his six 0.60 x 0.80 leave one with no drawn opening",
                           handles=[h for c in cen if c["width"] == "0.600" for h in c["jamb_handles"]])
                rec["residual"], rec["residual_class"] = "0", None
                out.append(rec)
                continue
            w, h_or_a, ev, basis, hnd = own_opening(oid, src, drawn, t627)
            if kind == "outline":
                own = R.opening_delta("outline", w_his=wh, h_his=hh, own_area=h_or_a)
                rec["own_w_x_h"] = f"{w} outline {h_or_a}"
            elif kind == "engine_only":
                own = R.opening_delta("engine_only", w_own=w, h_own=h_or_a)
                rec["own_w_x_h"] = f"{w} x {h_or_a}"
            else:
                own = R.opening_delta(kind, w_his=wh, h_his=hh, w_own=w, h_own=h_or_a)
                rec["own_w_x_h"] = f"{w} x {h_or_a}"
            drift = (w - D(ENGINE_NOMINAL_W[oid])) if oid in ENGINE_NOMINAL_W else None
            res, rc = R.residual_class(own, stated, drift)
            cls = r["class"]
            if oid == "D-GF-06" and kind == "height":
                cls = "ENGINE_RIGHT"   # head drawn 2.20 (DWF NE, cited T-627): no longer a Q-55 C rule difference
            rec.update(opening=oid, his=f"{wh} x {hh}" if wh else None, own_delta=str(own), evidence=ev,
                       class_proposed=cls, basis=basis, handles=hnd, residual=str(res), residual_class=rc)
        elif i in ARITH_ROWS:
            fl, f = ARITH_ROWS[i]
            d = dec[fl]
            sub = {x["name"]: D(x["delta"]) for x in d["rows"]}
            if f == "height":
                own = (D(d["H_his"]) - D(d["H_eng"])) * (D(d["L_eng"]) + D(d["L_held"]))
                basis = (f"(H_his {d['H_his']} - H_eng {d['H_eng']}) x (L_eng {d['L_eng']} + L_held {d['L_held']}) m: "
                         "his flat storey height vs clear height under each member (Q-72)")
                own = own.quantize(D("0.000001"))
            elif f == "residual":
                others = sum(v for k, v in sub.items() if "RESIDUAL" not in k)
                own = D(d["gap"]) - others
                basis = (f"identity: floor gap {d['gap']} - every other component of the floor split; "
                         f"length census L_his {d['L_his']} - L_eng {d['L_eng']} - L_held {d['L_held']} = "
                         f"{D(d['L_his']) - D(d['L_eng']) - D(d['L_held'])} m x H_his {d['H_his']}")
            else:
                own = next(v for k, v in sub.items() if "drift" in k)
                basis = "register V2 figure - V3.0.58 value on valued walls (T-543, cited)"
            # H_his / H_eng are stored at 6 dp: each can be off by 5e-7, times the length
            rb = (D("0.000001") * (D(d["L_eng"]) + D(d["L_held"]))) if f == "height" else None
            res, rc = R.residual_class(own, stated, None, rb)
            rec.update(own_delta=str(own), evidence="REPRODUCED" if f != "drift" else "CITED",
                       class_proposed=r["class"], basis=basis, handles=[], residual=str(res), residual_class=rc)
        elif i in PARAPET_ROWS:
            hl, cl, hh, k = PARAPET_ROWS[i]
            own = (D(hl) - D(cl)) * D(hh) if k == "length" else D(hh) * D(cl)
            res, rc = R.residual_class(own, stated, None)
            rec.update(own_delta=str(own), evidence="REPRODUCED", class_proposed=r["class"],
                       basis=(f"his {hl} m vs engine centreline {cl} m (T-319 / T-488 runs, cited) x {hh} m" if
                              k == "length" else f"his height above the slab exceeds the finished-roof height by {hh} m "
                              f"x engine centreline {cl} m: RC / build-up, not masonry (H1, T-543 s.3)"),
                       handles=[], residual=str(res), residual_class=rc)
        else:
            ev, basis = CITED_ROWS[i]
            own = stated if i != 78 else D("136.83760") * D("0.30")
            res, rc = R.residual_class(own, stated, None)
            rec.update(own_delta=str(own), evidence=ev, class_proposed=r["class"], basis=basis, handles=[],
                       residual=str(res), residual_class=rc)
        out.append(rec)
    # row totals: statement vs own; the signed split by proposed class must equal the own total exactly
    st_tot = sum(D(r["statement_delta"]) for r in out)
    tot, by_c, by_e = R.split([{"class": r["class_proposed"], "evidence": r["evidence"], "own_delta": r["own_delta"]}
                               for r in out])
    res_tot = sum(D(r["residual"]) for r in out)
    if tot - st_tot != res_tot:
        raise R.RuleError("own total - statement total != sum of residuals")
    return {"schema": "T633_ROW_EVIDENCE/1", "rule": "R-T633-1", "section": SECTION,
            "inputs": {"scorecard": SCORECARD_SHA, "t543": T543_SHA, "t627_drawn": T627_SHA,
                       "t633_drawn": _sha(DRAWN)},
            "unknown_rows": len(out), "held_rows_untouched": len(held),
            "held_signed_untouched": str(sum(D(rows[i]["delta"]) for i in held)),
            "statement_unknown_signed": str(st_tot), "own_unknown_signed": str(tot), "residual": str(res_tot),
            "by_class_proposed": {k: str(v) for k, v in sorted(by_c.items())},
            "by_evidence": {k: str(v) for k, v in sorted(by_e.items())},
            "rows": out}


def markdown(b) -> str:
    L = [f"# T-633 B9 blockwork UNKNOWN rows to evidence (generated by t633_alsenan.py; do not edit)", "",
         f"Section {b['section']}: {b['unknown_rows']} UNKNOWN rows, statement signed {b['statement_unknown_signed']} m2, "
         f"own {b['own_unknown_signed']} m2, residual {b['residual']} m2; {b['held_rows_untouched']} HELD rows "
         f"({b['held_signed_untouched']} m2) untouched.", "",
         "| # | Row | Stated | Own | Residual | Evidence | Class -> proposed | Basis |", "|---|---|---|---|---|---|---|---|"]
    for r in b["rows"]:
        L.append(f"| {r['index']} | {r['name'][:90]} | {r['statement_delta']} | {r['own_delta']} | {r['residual']}"
                 f"{' ' + r['residual_class'] if r['residual_class'] else ''} | {r['evidence']} | "
                 f"{r['statement_class']} -> {r['class_proposed']} | {r['basis']} |")
    L += ["", f"By proposed class: {b['by_class_proposed']}", f"By evidence: {b['by_evidence']}", ""]
    return "\n".join(L)


def dumps(b) -> str:
    return json.dumps(b, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    b = build()
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(markdown(b), encoding="utf-8")
    print("written", OUT_JSON.name, OUT_MD.name)
