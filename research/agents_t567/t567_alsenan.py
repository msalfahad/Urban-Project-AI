"""T-567 builder (development villa): external plaster / Sigma reconciliation against the freelancer BY ELEVATION AND
FACE CLASS, exact in m2 (R-T567-1 .. 5, t567_rules.py), on the candidate of record ARCH_TAKEOFF_V3.0.58.
Writes out/T567_EXT_RECONCILE.json, out/ELEVATION_MATRIX_T567.csv, out/COMPONENTS_T567.csv, out/FACES_T567.csv;
--check rebuilds them byte-identical. Run: python3 -I research/agents_t567/t567_alsenan.py [--check].
Reads only repository files (inputs pinned by sha256 in the output)."""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import operator
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t567_inputs as I  # noqa: E402
import t567_rules as R  # noqa: E402

F = Fraction
OUT = HERE / "out"
ELEV_ORDER = ["SW", "SE", "NE", "NW", "PASSAGE", "ROOF (parapet inner + top)"]
GROUP_ORDER = [g for g, _, _ in I.GROUPS]
OTHER_FAMILY_ROWS = ("61", "72", "73", "75", "87-90", "92")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def ev(expr: str) -> Fraction:
    """Exact evaluation of a written-out formula (numbers, + - * /, parentheses)."""
    def go(n):
        if isinstance(n, ast.Expression):
            return go(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return F(ast.get_source_segment(expr, n))
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](go(n.left), go(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -go(n.operand)
        raise R.RuleError(f"formula element not allowed: {ast.dump(n)}")
    return go(ast.parse(expr, mode="eval"))


def elevation_of(key: str) -> str:
    side = key.split("/")[1]
    if side.startswith("P-"):
        return "PASSAGE"
    if side in ("AT225", "POOL-COURT-FRONT"):
        return "NW"
    return side.split("-")[0]


CLASS_OF_KIND = {"plinth": "PLINTH", "storey": "STOREY", "parapet": "PARAPET_OUTER", "slab_edge": "SLAB_EDGE"}


def load_faces():
    book = R.Book()
    for r in csv.DictReader((ROOT / I.FILES["binding"]).open(encoding="utf-8")):
        cls = CLASS_OF_KIND[r["kind"]]
        lo, hi = r["lo"].strip(), r["hi"].strip()
        st = r["status"]
        if not lo and not hi:
            f = R.face(r["key"], elevation_of(r["key"]), cls, None, None, "HELD", length=r["length_m"] or None,
                       owner_line=r["line"])
        else:
            f = R.face(r["key"], elevation_of(r["key"]), cls, lo, hi, "HELD" if lo != hi else st,
                       length=r["length_m"] or None, owner_line=r["line"])
        book.add(f)
    changes = []
    for r in csv.DictReader((ROOT / I.FILES["t348_fill"]).open(encoding="utf-8")):
        key, kind, st = r["key"], r["kind"], r["status"]
        cls = I.T348_CLASS[key.rsplit("/", 1)[1]]
        if st == "NOT_A_FACE":
            book.remove(key, "T-348 r2: the pier stands on the GF roof band, no slab edge below it")
            changes.append((key, "REMOVED", "NOT_A_FACE"))
            continue
        if r["m2"]:
            f = R.face(key, I.T348_ELEVATION, cls, r["m2"], None, "DRAWING-CONFIRMED", owner_line=r["consumer"])
        else:
            f = R.face(key, I.T348_ELEVATION, cls, r["m2_lo"], r["m2_hi"], "HELD", owner_line=r["consumer"])
        if kind.startswith("RE-MEASURE"):
            book.replace(key, f)
            changes.append((key, "RE-MEASURED", st))
        else:
            book.add(f)
            changes.append((key, "NEW", st))
    # R-T567-6: the SW pier's returns in front of the 1F NW-5 key (own DXF read, t567_inputs)
    fx, jx = R.projecting_returns(I.PIER_SEGMENTS, I.PIER_SPAN)
    bx, bj = R.projecting_returns(I.BAND_SEGMENTS, I.BAND_SPAN)
    assert jx == 0 and bx == 0
    for key, lo, hi, st in I.T567_NEW:
        book.add(R.returns_face(key, "NW", fx, lo, hi, st))
        changes.append((key, "NEW (T-567 R-T567-6)", st))
    return book, changes


def his_cells():
    raw = json.loads((ROOT / I.FILES["his_cells"]).read_text(encoding="utf-8"))
    rows = {r["row"]: r["cells"] for r in raw["rows"] if r["file"] == "PLS" and r["sheet"] == raw["rows"][0]["sheet"]}
    sheet0 = [r for r in raw["rows"] if r["file"] == "PLS"][0]["sheet"]
    rows = {r["row"]: r["cells"] for r in raw["rows"] if r["file"] == "PLS" and r["sheet"] == sheet0}

    def cell(c):
        row = int("".join(ch for ch in c if ch.isdigit()))
        v = rows[row][c]["v"]
        return F(repr(round(v, 9))) if isinstance(v, float) else F(v)   # float storage artefacts (1e-14) dropped
    return rows, cell


def t346_band(row, bottoms):
    want = bottoms.split("|")
    s = F(0)
    for r in csv.DictReader((ROOT / I.FILES["t346_bands"]).open(encoding="utf-8")):
        if r["his_row"] == row and r["band_bottom"] in want:
            s += F(r["his_minus_drawn_m2"])
    return s


def t324_row(row):
    for r in csv.DictReader((ROOT / I.FILES["t324_his"]).open(encoding="utf-8")):
        if r["his_row"] == row:
            return F(r["his_m2"]), F(r["drawing_inner_plus_top_lo"]), F(r["drawing_inner_plus_top_hi"])
    raise KeyError(row)


def build():
    book, changes = load_faces()
    rows_raw, cell = his_cells()

    def his_row_m2(rid):
        tot = F(0)
        for n in I.ROW_CELLS[rid]:
            c = rows_raw[n]
            key = f"I{n}" if f"I{n}" in c else f"J{n}"
            tot += cell(key)
        return tot

    # his statement, checked against his own subtotals
    his_rows_all = {}
    for g, jcell, rng in I.GROUPS:
        s = F(0)
        for n in rng:
            if n in rows_raw:
                c = rows_raw[n]
                k = f"I{n}" if f"I{n}" in c else (f"J{n}" if (g == "DRIP" and f"J{n}" in c) else None)
                if k:
                    s += cell(k)
        assert s == cell(jcell), (g, s, cell(jcell))
        his_rows_all[g] = s
    his_gross = cell(I.HIS_GROSS_CELL)
    assert his_gross == sum(his_rows_all.values()), "J93 holds each row once"
    his_open = cell(I.HIS_OPENINGS_CELL)
    assert his_open == cell("I96") + cell("I97") if "I96" in rows_raw[96] else True
    his_ded = his_open / 2
    assert his_gross - his_ded == F(I.HIS_NET)

    rows = []
    for spec in I.ROWS:
        rid = spec["row"]
        his = his_row_m2(rid)
        other = []
        terms = []
        if "other" in spec:
            h, lo, hi = t324_row(spec["other"][0])
            assert h == his, (rid, h, his)
            other.append((spec["other"][1], lo, hi))
        for name, cause, expr, src in spec.get("terms", []):
            if isinstance(expr, tuple) and expr[0] == "CSV":
                terms.append(R.term(name, cause, t346_band(expr[1], expr[2]), source=src))
            elif isinstance(expr, tuple) and expr[0] == "T324":
                h, lo, hi = t324_row(expr[1])
                terms.append(R.term(name, cause, h - lo, h - hi, source=src))
            else:
                terms.append(R.term(name, cause, ev(expr), source=src))
        his_only = [R.term(n, c, ev(e), source=s) for n, c, e, s in spec.get("his_only", [])]
        portions = [R.Portion(k, ev(p)) for k, p in spec["portions"]]
        rows.append(R.HisRow(rid, spec["group"], his, portions, terms, his_only, other))
    assert sorted(r.row for r in rows) == sorted(I.ROW_CELLS), "every row of his once"

    # our openings: full holes on the faces (Q-73), T-337 ledger
    op_fixed, op_lo, op_hi, op_by_elev = F(0), F(0), F(0), {}
    for r in csv.DictReader((ROOT / I.FILES["openings"]).open(encoding="utf-8")):
        if r["status"] == "NOT_AN_OPENING":
            continue
        e = elevation_of(r["face_key"])
        fx = F(r["fixed"]) if r["fixed"] else F(0)
        lo = F(r["lo"]) if r["lo"] else F(0)
        hi = F(r["hi"]) if r["hi"] else F(0)
        a = op_by_elev.setdefault(e, [F(0), F(0), F(0), 0])
        a[0] += fx; a[1] += lo; a[2] += hi; a[3] += 1
        op_fixed += fx; op_lo += lo; op_hi += hi
    res = R.bridge(book, rows, his_gross, his_ded, (op_fixed + op_lo, op_fixed + op_hi))

    # candidate of record: the facade lines carry no quantity (HELD blank); other families named
    li = json.loads((ROOT / I.FILES["line_index"]).read_text(encoding="utf-8"))
    L = {x["line_id"]: x for x in li["lines"]}
    cand = {}
    for lid, fl in I.CANDIDATE["FIN.EXT.FINISH"].items():
        x = L[lid]
        assert x["item_code"] == "FIN.EXT.FINISH" and x["class"] == "HELD" and x["measured_net"] is None
        cand[lid] = {"floor": fl, "item": "FIN.EXT.FINISH", "class": "HELD", "quantity": None}
    lid, item, q = I.CANDIDATE["pool_soffit"]
    assert L[lid]["item_code"] == item and F(repr(L[lid]["measured_net"])) == F(q)
    fam = {}
    for x in li["lines"]:
        if x["item_code"] in ("EXT.FENCE.PLASTER", "ARCH.WINDOW_REVEAL", "ARCH.FACADE", "FIN.EXT.FINISH"):
            a = fam.setdefault(x["item_code"], {"lines": 0, "valued": 0, "blank": 0, "valued_m2": F(0)})
            a["lines"] += 1
            if x["measured_net"] is None:
                a["blank"] += 1
            else:
                a["valued"] += 1
                a["valued_m2"] += F(repr(x["measured_net"]))
    assert fam["FIN.EXT.FINISH"]["valued"] == 0 and fam["EXT.FENCE.PLASTER"]["valued"] == 0

    # own-family faces kept apart (never in the render totals)
    own = {k: f for k, f in book.faces.items() if f.face_class in R.OWN_FAMILY_CLASSES}
    # T-337 ITEMS inner + top equals the T-324 ranges matched to his parapet rows (all of ours is in his rows)
    inner_lo = sum(o[1] for r in rows for o in r.matched_other)
    inner_hi = sum(o[2] for r in rows for o in r.matched_other)
    assert (R.fmt(inner_lo, 3), R.fmt(inner_hi, 3)) == ("120.959", "126.530")
    return book, changes, rows, res, his_rows_all, his_gross, his_open, his_ded, (op_fixed, op_lo, op_hi,
                                                                                    op_by_elev), cand, fam, own


def q(x):
    """Output text with 7 decimals; every value of this bridge terminates within 7 (asserted), so the printed
    figures add up exactly."""
    if (x * 10 ** 7).denominator != 1:
        raise R.RuleError(f"value {float(x)} does not terminate within 7 decimals")
    return R.fmt(x, 7)


def render():
    book, changes, rows, res, his_groups, his_gross, his_open, his_ded, ops, cand, fam, own = build()
    op_fixed, op_lo, op_hi, op_by_elev = ops
    out = {"task": "T-567", "candidate": "ARCH_TAKEOFF_V3.0.58 (= V3.0.57 facade lines, arch_v3058 (e))",
           "inputs_sha256_16": {k: sha(v) for k, v in I.FILES.items()},
           "his": {"gross_J93": q(his_gross), "groups": {g: q(his_groups[g]) for g in GROUP_ORDER},
                   "openings_J97": q(his_open), "deduction_half": q(his_ded), "net_invoice_r25": q(his_gross - his_ded)},
           "candidate_lines": cand,
           "candidate_families": {k: {"lines": v["lines"], "valued": v["valued"], "blank": v["blank"],
                                      "valued_m2": q(v["valued_m2"])} for k, v in sorted(fam.items())},
           "t348_changes": changes,
           "own_family_faces_not_in_totals": {k: {"class": f.face_class, "lo": None if f.lo is None else q(f.lo),
                                                 "hi": None if f.hi is None else q(f.hi), "status": f.status}
                                             for k, f in sorted(own.items())},
           "blank_faces_by_name": res["blank_faces"],
           "our_openings_full": {"fixed": q(op_fixed), "held_lo": q(op_lo), "held_hi": q(op_hi),
                                 "by_elevation": {e: {"fixed": q(v[0]), "held_hi": q(v[2]), "n": v[3]}
                                                  for e, v in sorted(op_by_elev.items())}},
           "passes": {}}
    # true net bound: the held openings (W02, D-GF-07) are independent of the held faces
    g_lo, g_hi = res["passes"]["lo"]["our_gross"], res["passes"]["hi"]["our_gross"]
    n_lo, n_hi = g_lo - (op_fixed + op_hi), g_hi - (op_fixed + op_lo)
    his_net = his_gross - his_ded
    other_family = [c for c in res["passes"]["lo"]["components"] if c["kind"] == "HIS_ONLY" and
                    c["row"] in OTHER_FAMILY_ROWS]
    his_cmp = his_gross - sum((c["m2"] for c in other_family), F(0))
    out["net_bound"] = {"our_net_lo": q(n_lo), "our_net_hi": q(n_hi), "his_net": q(his_net),
                        "his_minus_ours_lo": q(his_net - n_hi), "his_minus_ours_hi": q(his_net - n_lo),
                        "ours_vs_his_pct": [R.fmt((n_lo / his_net - 1) * 100, 2), R.fmt((n_hi / his_net - 1) * 100, 2)]}
    out["like_for_like_gross"] = {
        "his_rows_excluded_as_other_family_or_held_scope": sorted({c["row"] for c in other_family}),
        "his_excluded_m2": q(his_gross - his_cmp), "his_comparable_gross": q(his_cmp),
        "our_gross_lo": q(g_lo), "our_gross_hi": q(g_hi),
        "ours_vs_his_pct": [R.fmt((g_lo / his_cmp - 1) * 100, 2), R.fmt((g_hi / his_cmp - 1) * 100, 2)],
        "note": "his comparable = his gross less domes (owner item 3), the pool soffit row (a FIN.CEILING line), "
                "frames (HELD), boundary wall (EXT.FENCE.PLASTER, HELD) and drip (UNKNOWN); his double count (row 65) "
                "and the no-face part of row 74 stay inside (they are his errors on wall rows)",
        "his_comparable_net": q(his_cmp - his_ded), "our_net_lo": q(n_lo), "our_net_hi": q(n_hi),
        "net_ours_vs_his_pct": [R.fmt((n_lo / (his_cmp - his_ded) - 1) * 100, 2),
                                R.fmt((n_hi / (his_cmp - his_ded) - 1) * 100, 2)]}
    comp_rows, mat_rows = [], []
    for pas in ("lo", "hi"):
        p = res["passes"][pas]
        elev_tot = {}
        for (e, g), m in p["matrix"].items():
            elev_tot[e] = elev_tot.get(e, F(0)) + m
        for x in p["ours_only"]:
            elev_tot[x["elevation"]] = elev_tot.get(x["elevation"], F(0)) + x["m2"]
        grp = {g: {"drawn": F(0), "terms": F(0), "his_only": F(0)} for g in GROUP_ORDER}
        for (e, g), m in p["matrix"].items():
            grp[g]["drawn"] += m
        for c in p["components"]:
            if c["kind"] == "TERM":
                grp[c["group"]]["terms"] += c["m2"]
            elif c["kind"] == "HIS_ONLY":
                grp[c["group"]]["his_only"] += c["m2"]
        for g in GROUP_ORDER:
            assert grp[g]["drawn"] + grp[g]["terms"] + grp[g]["his_only"] == his_groups[g], g
        assert sum(elev_tot.values()) == p["our_gross"]
        cause = R.by_cause(p["components"])
        out["passes"][pas] = {
            "our_gross": q(p["our_gross"]), "his_gross": q(his_gross), "gross_diff": q(p["gross_diff"]),
            "residual": q(p["residual"]), "our_openings": q(p["our_openings"]), "our_net": q(p["our_net"]),
            "his_net": q(p["his_net"]), "net_diff": q(p["net_diff"]),
            "net_diff_check": "net_diff = gross_diff - his deduction + our openings",
            "by_cause": {k: q(v) for k, v in sorted(cause.items())},
            "our_by_elevation": {e: q(elev_tot.get(e, F(0))) for e in ELEV_ORDER},
            "his_by_group": {g: {"drawn_matched": q(grp[g]["drawn"]), "terms": q(grp[g]["terms"]),
                                 "his_only": q(grp[g]["his_only"]), "his": q(his_groups[g])} for g in GROUP_ORDER},
            "ours_only_by_elevation": {e: q(sum((x["m2"] for x in p["ours_only"] if x["elevation"] == e), F(0)))
                                       for e in ELEV_ORDER}}
        assert p["net_diff"] == p["gross_diff"] - his_ded + p["our_openings"]
        for e in ELEV_ORDER:
            row = {"pass": pas, "our_elevation": e}
            for g in GROUP_ORDER:
                row[g] = q(p["matrix"].get((e, g), F(0)))
            row["OURS_ONLY"] = out["passes"][pas]["ours_only_by_elevation"][e]
            row["our_total"] = out["passes"][pas]["our_by_elevation"][e]
            mat_rows.append(row)
        for c in p["components"]:
            comp_rows.append({"pass": pas, "row": c["row"], "group": c["group"], "kind": c["kind"],
                              "cause": c["cause"], "m2": q(c["m2"]), "name": c["name"], "source": c["source"]})
    faces = [{"key": k, "elevation": f.elevation, "class": f.face_class, "status": f.status,
              "lo": "" if f.lo is None else q(f.lo), "hi": "" if f.hi is None else q(f.hi)}
             for k, f in sorted(book.faces.items())]

    def to_csv(rows_, cols):
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_)
        return b.getvalue()
    return {
        "T567_EXT_RECONCILE.json": json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
        "ELEVATION_MATRIX_T567.csv": to_csv(mat_rows, ["pass", "our_elevation"] + GROUP_ORDER +
                                            ["OURS_ONLY", "our_total"]),
        "COMPONENTS_T567.csv": to_csv(comp_rows, ["pass", "row", "group", "kind", "cause", "m2", "name", "source"]),
        "FACES_T567.csv": to_csv(faces, ["key", "elevation", "class", "status", "lo", "hi"]),
    }


def main(argv):
    files = render()
    if "--check" in argv:
        bad = [n for n, t in files.items() if (OUT / n).read_text(encoding="utf-8") != t]
        print("CHECK", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for n, t in files.items():
        (OUT / n).write_text(t, encoding="utf-8")
    print("WROTE", ", ".join(sorted(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
