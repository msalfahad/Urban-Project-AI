"""T-621 builder (research, unwired): the 41 rows of the B3 floor tile line (statement V10 section T-553/floor-tile,
reference 409.58 vs engine 387.09405 m2, difference 22.48595 m2, scorecard V10 UNKNOWN 0 / 41) each given its own
drawn area by handle (R-T621-1) from the committed drawing read T621_DRAWN.json, the pinned statement and the merged
T-553 room table (engine and his figure per room; numbers only).

    python3 -I research/agents_t621/t621_alsenan.py            (write out/)
    python3 -I research/agents_t621/t621_alsenan.py --check    (rebuild, byte-identical)

Nothing here changes a candidate, engine, rule / knowledge version, registry or statement file; nothing is released;
no class moves (the rows' classes are the statement's); only the evidence of each row is established.
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
import t621_rules as R  # noqa: E402

D = Decimal
DRAWN = HERE / "T621_DRAWN.json"
STATEMENT = ROOT / "research/agents_t609/out/RECONCILED_STATEMENT_T609.json"
STATEMENT_SHA = "dc2b25d65003e383d9aee2d73da609891e35d28d780744b65702638bf8d665b7"
T553 = ROOT / "research/agents_t553/out/FLOOR_TILE_RECONCILE_T553.json"
T553_SHA = "6a58e668e48d8a7b3fe38a002c296495b7ba60ccebb341e0ad37e06333b3b8c4"
SECTION = "T-553/floor-tile"
OUT_JSON = HERE / "out" / "T621_ROW_EVIDENCE.json"
OUT_MD = HERE / "out" / "T621_ROW_EVIDENCE.md"
LIFT_DEPTH = D("0.300")   # UP-ELEV-005 certain floor part of a lift landing threshold (rule depth, not drawn)
ARRIVAL_RULE_PIECE = D("0.0475")   # T-240 / T-269: well end -0.010 + nosing band 0.0575 (by reference, not re-measured)

# (row index, name prefix, kind, terms, note / what closes it)
# terms: ROOM -> measure id; PIECE -> [(sign, measure id or ('LIFT', gap id))]; READING -> ('his', [(sign, id)], extra)
SPEC = [
    (0, "GF open room", "NOT_ESTABLISHED", None,
     "round-stair footprint not re-measured from its tread outline; closure only (own gross - own pieces - engine "
     "lines, printed). Closes: the tread outline by handle (T-341 treads 8.194412 - under-stair floor 2.07)"),
    (1, "GF open room", "PIECE", [(1, ("LIFT", "GF-LIFT-DOOR"))], "drawn door width x rule depth 0.300 (UP-ELEV-005)"),
    (2, "GF open room", "PIECE", [(1, "GF-BAND")], "band 7.02 x 1.30 less column 2FD5 notch; class HELD (D-48) kept"),
    (3, "GF open room", "PIECE", [(1, "GF-CURB")], "curb 3.02 x 0.20; class kept (D-48)"),
    (4, "GF open room", "PIECE", [(1, "GF-SOLID-COL-2FD2"), (1, "GF-SOLID-COL-2FC6"), (1, "GF-SOLID-WALL")],
     "columns 0.80 x 0.25 + 0.60 x 0.25 + wall 2.65 x 0.20 inside his gross outline"),
    (5, "GF open room", "READING", ("147.96", [(1, "GF-OPEN.full")]),
     "his rows 137.50 + 10.46 minus the own drawn gross outline (T-612 chain re-measured)"),
    (6, "GF dewaneya", "ROOM", "GF-DEWANEYA", ""),
    (7, "GF master bed room", "ROOM", "GF-MASTER",
     "room to the curved glazing face + the hall to its bath (2E0 / 319 / 2E7), column 2F85 notch"),
    (8, "GF driver room", "ROOM", "GF-DRIVER", ""),
    (9, "GF stair room", "NOT_ESTABLISHED", None,
     "hall 4.805 + lobby 1.3225 stay T-418 (by reference); closes: the hall / lobby outlines by riser and wall handles"),
    (10, "GF doorway strips", "PIECE", [(1, "GF-OP-010"), (1, "GF-OP-012")], "jamb-to-jamb x face-to-face"),
    (11, "1F living", "NOT_ESTABLISHED", None,
     "printed 2.50 x 1.95 = 4.875 re-read (DIMENSIONs D25 / 10DF); the +0.0475 (well end / nosing band, T-240 / T-269) "
     "is by reference; closes: those two drawn pieces by handle"),
    (12, "1F living", "PIECE", [(1, ("LIFT", "1F-LIFT-DOOR"))], "drawn door width x rule depth 0.300 (UP-ELEV-005)"),
    (13, "1F living", "NOT_ESTABLISHED", None,
     "own floor at +5.50 (printed landing edge) 38.5855 by handle; the residual also needs the +0.0475 arrival piece "
     "(by reference); his 38.96 vs the drawn east-flight-foot reading 38.988 (-0.028, outside his rounding)"),
    (14, "1F curved", "READING", ("17.29", [(1, "1F-CUR.ours")]),
     "his 17.29 vs own drawn room + lobby; readings 15.060 / 16.744 / 20.700 reproduce nothing: UNRESOLVED kept"),
    (15, "1F bed room 380 x 430", "PIECE", [(1, "1F-DRESSING")],
     "dressing 1.65 x 1.80 own outline; his 19.46 = own 16.34 + 2.97 + arch strip 0.15 (checked)"),
    (16, "1F bed room 500 x 365", "ROOM", "1F-500x365", ""),
    (17, "1F west bed room", "ROOM", "1F-WEST-BED", ""),
    (18, "1F doorway strips", "PIECE", [(1, "1F-OP-005"), (1, "1F-OP-006"), (1, "1F-OP-020"), (1, "1F-D-1F-03")], ""),
    (19, "2F maid room", "ROOM", "2F-MAID", ""),
    (20, "2F lobby", "PIECE", [(1, "2F-ARRIVAL")], "printed 2.50 x 1.95 (DIMENSIONs 138E / 14F1)"),
    (21, "2F lobby", "PIECE", [(1, ("LIFT", "2F-LIFT-DOOR"))], "drawn door width x rule depth 0.300 (UP-ELEV-005)"),
    (22, "2F lobby", "READING", ("7.7", [(1, "2F-CORR.ours")]),
     "his 7.70 vs own lobby + arrival (landing edge at the printed 1.95); east-foot reading 7.72 outside his rounding"),
    (23, "2F doorway strip", "PIECE", [(1, "2F-OP-007")], ""),
    (24, "GF lobby wash", "ROOM", "GF-LOBBY-WASH", ""),
    (25, "GF basin space", "PIECE", [(1, "GF-BASIN-REVEAL")], "printed 1.10 x 0.20 (DIMENSIONs 70F / 672)"),
    (26, "GF basin space", "READING", ("1.7", [(1, "GF-BASIN-STAIR"), (1, "GF-BASIN-REVEAL")]), "his 1.70 truncated"),
    (27, "GF master bath", "ROOM", "GF-MASTER-BATH", ""),
    (28, "GF core W.C. 245", "ROOM", "GF-WC-CORE-245", ""),
    (29, "GF core W.C. 289", "ROOM", "GF-WC-CORE-289", ""),
    (30, "GF stair-core W.C.", "ROOM", "GF-WC-STAIR", ""),
    (31, "GF kitchen", "ROOM", "GF-KITCHEN", "class move F-T553-2 (porcelain code, wet room) untouched: 0 m2"),
    (32, "GF W.C. by the reception", "ROOM", "GF-WC-REC", ""),
    (33, "GF wash by the reception", "ROOM", "GF-WASH-REC", ""),
    (34, "1F east bath", "ROOM", "1F-EAST-BATH", ""),
    (35, "1F bath by the laundry", "ROOM", "1F-BATH-LAUNDRY", ""),
    (36, "1F W.C. by the laundry", "ROOM", "1F-WC-LAUNDRY", ""),
    (37, "1F west bath A", "ROOM", "1F-WBATH-1", "A / B paired by equal area: the two baths are congruent (5.0225)"),
    (38, "1F west bath B", "ROOM", "1F-WBATH-2", "A / B paired by equal area: the two baths are congruent (5.0225)"),
    (39, "1F laundry", "ROOM", "1F-LAUNDRY", ""),
    (40, "2F roof-floor W.C.", "ROOM", "2F-ROOF-WC", ""),
]


def _sha(p: Path, sha: str) -> bytes:
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise R.RuleError(f"{p.name} changed: re-pin")
    return raw


def load():
    st = json.loads(_sha(STATEMENT, STATEMENT_SHA))
    sec = [s for s in st["sections"] if s["section_id"] == SECTION]
    if len(sec) != 1:
        raise R.RuleError("section of record not found once")
    t553 = json.loads(_sha(T553, T553_SHA))
    drawn = json.loads(DRAWN.read_text(encoding="utf-8"))
    return sec[0], t553["table"]["rows"], drawn["measures"]


def _room(rooms, name):
    hits = [r for r in rooms if name.startswith(r["room"])]
    if len(hits) != 1:
        raise R.RuleError(f"row '{name[:50]}' maps to {len(hits)} T-553 rooms")
    return hits[0]


def _val(meas, term):
    if isinstance(term, tuple) and term[0] == "LIFT":
        g = meas[term[1]]
        R.evidence(g)
        return R.rule_piece(D(g["width"]), LIFT_DEPTH, "UP-ELEV-005"), g["handles"][:2]
    m = meas[term]
    return R.evidence(m), m["handles"]


def build():
    sec, rooms, meas = load()
    rows = sec["rows"]
    if len(rows) != 41 or len(SPEC) != 41:
        raise R.RuleError("41 rows expected")
    out = []
    for (i, prefix, kind, terms, note), row in zip(SPEC, rows):
        name = row["name"]
        if not name.startswith(prefix):
            raise R.RuleError(f"row {i}: '{name[:40]}' is not '{prefix}'")
        room = _room(rooms, name)
        delta = D(row["delta"])
        rec = {"row": i, "name": name, "class": row["class"], "delta": str(delta), "kind": kind,
               "engine_room": room["engine"], "his_room": room["freelancer"], "note": note, "measures": []}
        own = engine = expected = None
        if kind == "ROOM":
            own, hs = _val(meas, terms)
            engine = D(room["engine"])
            rec["measures"] = [{"id": terms, "area": str(own), "handles": hs}]
            his_minus_own = D(room["freelancer"]) - own
            rec["his_minus_own"] = str(his_minus_own)
            R.check_class(row["class"], delta, kind, his_minus_own)
            if D(room["freelancer"]) - engine != delta:
                raise R.RuleError(f"row {i}: delta is not his - engine for a one-row room")
        elif kind == "PIECE":
            own = D(0)
            for sgn, t in terms:
                v, hs = _val(meas, t)
                own += sgn * v
                rec["measures"].append({"id": t if isinstance(t, str) else f"{t[1]} x {LIFT_DEPTH} (UP-ELEV-005)",
                                        "area": str(v), "handles": hs})
            R.check_class(row["class"], delta, kind)
        elif kind == "READING":
            his, ts = terms
            expected = D(his)
            for sgn, t in ts:
                v, hs = _val(meas, t)
                expected -= sgn * v
                rec["measures"].append({"id": t, "area": str(v), "handles": hs})
            R.check_class(row["class"], delta, kind)
        status, diff = R.judge(kind, delta, own=own, engine=engine, expected=expected)
        rec.update(own=None if own is None else str(own), expected_delta=None if expected is None else str(expected),
                   difference_to_row=None if diff is None else str(diff), evidence_status=status,
                   verdict_proposal=row["class"])
        out.append(rec)
    # closures printed beside (never a confirmation): the GF open room and the 380 x 430 pair
    g = {k: D(v["area"]) for k, v in meas.items()}
    lift_gf = R.rule_piece(D(meas["GF-LIFT-DOOR"]["width"]), LIFT_DEPTH, "UP-ELEV-005")
    stair_closure = (g["GF-OPEN.full"] - D("130.648285") - lift_gf - g["GF-BAND"] - g["GF-CURB"]
                     - g["GF-SOLID-COL-2FD2"] - g["GF-SOLID-COL-2FC6"] - g["GF-SOLID-WALL"])
    pair_380 = g["1F-380x430"] + g["1F-DRESSING"] + g["1F-OP-011"]
    liv_own = g["1F-LIV.floor_printed"]
    beside = {
        "gf_open_stair_footprint_by_closure": {"value": str(stair_closure), "row_0": "6.124412",
                                               "basis": "own gross 147.657717 - engine open-room lines 130.648285 - "
                                               "own lift / band / curb / solids; NOT a re-measure (uses the engine)"},
        "his_bed_room_2_reproduced": {"own": str(pair_380), "his": "19.46",
                                      "basis": "own 380 x 430 + own dressing + own arch strip OP-011"},
        "1F_living_own_floor_at_550": {"own_printed_edge": str(liv_own), "own_east_foot": str(g["1F-LIV.floor_drawn"]),
                                       "engine_porcelain_lift_arrival": "38.633536",
                                       "engine_minus_own": str(D("38.633536") - liv_own),
                                       "basis": "engine - own = 0.0475 arrival rule piece (by reference) + 0.000536"},
        "1F_arrival_printed": meas["1F-ARRIVAL"]["area"],
    }
    sp = R.split(out, D(sec["difference"]))
    return {"schema": "T621_ROW_EVIDENCE_V1", "rule": R.RULE_ID, "governing": R.GOVERNING, "section": SECTION,
            "statement": {"path": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA},
            "t553": {"path": str(T553.relative_to(ROOT)), "sha256": T553_SHA},
            "drawn": str(DRAWN.relative_to(ROOT)), "reference_total": sec["reference_total"],
            "engine_valued": sec["engine_valued"], "difference": sec["difference"], "area_tol": str(R.AREA_TOL),
            "rows": out, "split": sp, "beside": beside,
            "checker_top5": _top5(out)}


def _top5(out):
    rooms = {}
    for r in out:
        for m in r["measures"]:
            rooms[m["id"]] = (D(m["area"]), m["handles"])
    big = sorted(((a, k, h) for k, (a, h) in rooms.items()), key=lambda x: -x[0])[:5]
    return [{"id": k, "area": str(a), "handles": h} for a, k, h in big]


def markdown(d):
    L = [f"# T-621 floor tile rows: own drawn area per row (R-T621-1)", "",
         f"Section {d['section']}: reference {d['reference_total']} vs engine {d['engine_valued']} m2, difference "
         f"{d['difference']} m2 (reference - engine). Area tolerance {d['area_tol']} m2. No class moves; evidence only.",
         "", "| # | Row | Class | Delta | Kind | Own (m2) | Check diff | Evidence | Handles |", "|---|---|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        hs = "; ".join(f"{m['id']}: {' '.join(m['handles'])}" for m in r["measures"]) or "-"
        own = r["own"] or (r["expected_delta"] and f"exp {r['expected_delta']}") or "-"
        L.append(f"| {r['row']} | {r['name'][:70]} | {r['class']} | {r['delta']} | {r['kind']} | {own} | "
                 f"{r['difference_to_row'] or '-'} | {r['evidence_status']} | {hs} |")
    sp = d["split"]
    L += ["", f"Split (re-adds exactly to {sp['total']}): by class {sp['by_class']}; by evidence {sp['by_evidence']}; "
          f"rows {sp['count_by_evidence']}.", "", "Beside (never a confirmation):"]
    for k, v in d["beside"].items():
        L.append(f"- {k}: {v}")
    L += ["", "Checker re-measure set (5 largest own measures): " +
          "; ".join(f"{x['id']} {x['area']}" for x in d["checker_top5"]), ""]
    return "\n".join(L)


def main(argv):
    d = build()
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    md = markdown(d)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == txt and OUT_MD.read_text(encoding="utf-8") == md
        print("check", "identical" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(txt, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print("written", d["split"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
