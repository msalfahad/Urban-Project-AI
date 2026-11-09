"""T-557: the reconciled-quantities statement on every merged reconciliation (T-541, T-534 + F-C-T548-1, T-543 +
F-C-T543-1 restated by T-550, T-546, T-542 beside, T-545, T-547, T-552) with the T-548 builder and the T-554 adapters
(both read only). No private input.

  python3 -I research/agents_t557/t557_build.py --write   # write out/
  python3 -I research/agents_t557/t557_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t557_adapters as X  # noqa: E402

SA, S, A, D = X.SA, X.S, X.A, X.D
sys.path.insert(0, str(X.T554))
import t554_build as B554  # noqa: E402

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T557.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T557.md"
REPORTS_COVERED = ["T-541", "T-534", "T-543", "T-550", "T-546", "T-542", "T-545", "T-547", "T-552"]
REPORTS_PENDING = ["T-551", "T-553", "T-559", "T-560", "T-561"]
EXTRA_KEYS = ("verification", "verification_basis", "reclass", "h1_status", "fix_row")
NEW_SECTIONS = ("T-545/beams", "T-547/wall-tile", "T-552/plaster-internal", "T-552/plaster-external")


def _neg(x) -> Decimal:
    return -D(x)


def source_class_totals(d545: dict, d547: dict, d552: dict) -> dict:
    """Each report's OWN class totals in the statement sign (reference - engine), before the R-T557-1 (b) moves."""
    t545 = {c: Decimal(0) for c in S.CLASSES}
    for comp in d545["total"]["components"].values():
        t545[comp["verdict"]] += _neg(comp["m3"])
    t547 = {c: Decimal(0) for c in S.CLASSES}
    for c, v in d547["by_cause"].items():
        t547[c] += _neg(v)
    t552i = {c: Decimal(0) for c in S.CLASSES}
    for pair in ("DRY", "SHAFT", "RETURN"):
        for c, v in d552["internal"]["pairs"][pair]["by_cause"].items():
            t552i[c] += D(v)
    t552e = {c: Decimal(0) for c in S.CLASSES}
    for c, v in d552["external"]["bridge_lo"]["by_cause"].items():
        t552e[c] += D(v)
    return {"T-545/beams": t545, "T-547/wall-tile": t547, "T-552/plaster-internal": t552i,
            "T-552/plaster-external": t552e}


def check_class_moves(st_sec: dict, src_rows: list[dict], expected: dict) -> list[dict]:
    """Statement class totals = the report's own totals moved exactly by the rows' listed reclasses."""
    exp = dict(expected)
    moves = []
    for r in src_rows:
        m = r.get("reclass")
        if m:
            exp[m["from"]] -= D(m["delta"])
            exp[m["to"]] += D(m["delta"])
            moves.append({"section_id": st_sec["section_id"], "row": r["name"], **m})
    got = {c: D(v) for c, v in st_sec["by_class"].items()}
    if any(got[c] != exp[c] for c in S.CLASSES):
        raise X.AdapterError(f"{st_sec['section_id']}: class totals {st_sec['by_class']} != report totals moved by "
                             f"the listed reclasses {({c: S.s(v) for c, v in exp.items()})}")
    return moves


def assemble(index: dict) -> tuple[list[dict], dict, dict]:
    secs, prov = SA.all_sections(index)                  # T-541, T-534 (+F-C-T548-1), T-543 (+F-C-T543-1), T-546
    d550 = json.loads(X.T550_JSON.read_text(encoding="utf-8"))
    i543 = [i for i, x in enumerate(secs) if x["section_id"] == "T-543/blockwork"]
    if len(i543) != 1:
        raise X.AdapterError("T-543 section missing")
    old543 = secs[i543[0]]
    secs[i543[0]] = X.t550_restate(old543, d550, [lid for lid, _ in SA.PARAPET_RC_LINES])
    d545 = json.loads(X.T545_JSON.read_text(encoding="utf-8"))
    d547 = json.loads(X.T547_JSON.read_text(encoding="utf-8"))
    d552 = json.loads(X.T552_JSON.read_text(encoding="utf-8"))
    new = [X.t545_from(d545, index), X.t547_from(d547, index)] + X.t552_from(d552, index)
    for x in [secs[i543[0]]] + new:
        SA.refuse_held_as_zero(x)
        SA.bind_cross_family(x, index)
        prov["valued_lines_not_in_V3_0_57_index"][x["section_id"]] = A.bind_to_index(SA.for_builder(x), index)
    secs += new
    for p in (X.T545_JSON, X.T547_JSON, X.T550_JSON, X.T552_JSON, X.T552_INPUTS, HERE / "t557_adapters.py",
              X.T554 / "statement_adapters.py", X.T554 / "t554_build.py"):
        prov["inputs"][str(p.relative_to(X.ROOT))] = SA.sha(p)
    ctx = {"d550": d550, "old543": old543, "src": source_class_totals(d545, d547, d552)}
    return secs, prov, ctx


def build_from(secs: list[dict], prov: dict, index: dict, ctx: dict) -> dict:
    st = B554.build_from(secs, prov, index)              # T-548 closure + T-554 correction checks
    by_id = {x["section_id"]: x for x in secs}
    moves = []
    for c in st["sections"]:
        src = by_id[c["section_id"]]
        if len(c["rows"]) != len(src["rows"]):
            raise X.AdapterError(f"{c['section_id']}: row count changed in the builder")
        for r, r0 in zip(c["rows"], src["rows"]):
            if r["name"] != r0["name"]:
                raise X.AdapterError(f"{c['section_id']}: row order changed in the builder")
            for k in EXTRA_KEYS:
                if k in r0:
                    r[k] = r0[k]
        if "beside" in src:
            c["beside"] = src["beside"]
        if c["section_id"] in NEW_SECTIONS:
            moves += check_class_moves(c, src["rows"], ctx["src"][c["section_id"]])
    # T-543 restated by T-550: class totals = T-554's + T-550's own change + the F-T557-6 move (R-T557-1 (e))
    t554 = json.loads(B554.JSON_OUT.read_text(encoding="utf-8"))
    old = [x for x in t554["sections"] if x["section_id"] == "T-543/blockwork"][0]
    c543 = [x for x in st["sections"] if x["section_id"] == "T-543/blockwork"][0]
    exp = X.t550_expected_by_class(old["by_class"], ctx["d550"], by_id["T-543/blockwork"]["rows"])
    if exp != c543["by_class"]:
        raise X.AdapterError(f"T-543 restated class totals {c543['by_class']} != expected {exp}")
    if c543["reference_total"] != old["reference_total"] or c543["engine_valued"] != old["engine_valued"]:
        raise X.AdapterError("T-543: the restatement moved the reference or the engine total")
    keep_old = [r for r in old["rows"] if not r["name"].startswith(X.T543_PARAPET_RESIDUAL)]
    keep_new = [r for r in c543["rows"] if r.get("correction") != "T-550"]
    for a, b in zip(keep_old, keep_new):
        if (a["name"], a["delta"], a["class"]) != (b["name"], b["delta"], b["class"]):
            raise X.AdapterError(f"T-543: row {a['name']} changed outside the T-550 target")
    if len(keep_old) != len(keep_new):
        raise X.AdapterError("T-543: rows added or lost outside the T-550 target")
    for r in by_id["T-543/blockwork"]["rows"]:
        if r.get("reclass"):
            moves.append({"section_id": "T-543/blockwork", "row": r["name"], **r["reclass"]})
    c543["restatement"] = {"by": "T-550 (R-T550-1, MERGED f052dfeb)", "H1": "MEASURED",
                           "unresolved_before_m2": old["by_class"]["UNRESOLVED"],
                           "unresolved_after_m2": c543["by_class"]["UNRESOLVED"],
                           "unresolved_named": [{"part": u["part"], "m2": u["m2"]} for u in ctx["d550"]["unresolved_after"]]}
    X.verify_engine_wrong(st)
    X.verify_labels(st)
    st["reclasses"] = moves
    st["reports_covered"] = REPORTS_COVERED
    st["reports_pending"] = REPORTS_PENDING
    st["rule"] = "R-T548-1 + R-T554-1 + R-T557-1"
    return json.loads(json.dumps(st, sort_keys=True))


def build() -> dict:
    index = SA.load_index()
    secs, prov, ctx = assemble(index)
    return build_from(secs, prov, index, ctx)


def to_markdown(st: dict) -> str:
    md = ("# T-557 reconciled-quantities statement (generated; reference - engine, + = in the reference only)\n\n"
          + S.to_markdown(st) + "\n")
    md += ("| Section | Unit | Reference | Engine valued | Bounded | Diff. | % of ref. | ENGINE_WRONG | HELD lines "
           "(own / cross-family) |\n|---|---|---|---|---|---|---|---|---|\n")
    for c in st["sections"]:
        b = c["engine_bounded"]
        xf = len(c.get("held_cross_family", []))
        md += (f"| {c['section_id']} | {c['unit']}{' (his ' + c['reference_label'] + ')' if c.get('reference_label') else ''}"
               f" | {c['reference_total']} | {c['engine_valued']} | AT_LEAST {b['low_at_least']} .. "
               f"{'OPEN' if b['high_open'] else b['high']} | {c['difference']} | {c['difference_pct_of_reference']} | "
               f"{c['by_class']['ENGINE_WRONG']} | {c['held_count'] - xf} / {xf} |\n")
    ew = [c for c in st["sections"] if c["section_id"] == "T-552/plaster-internal"][0]["beside"]["engine_wrong_restated"]
    md += (f"\nENGINE_WRONG beside (T-552, fix row {ew['fix_row']}): the 4 released dry plaster lines "
           f"{ew['released_lines_now_m2']} m2 restate to HELD (BOUNDED) {ew['released_lines_restated_HELD_BOUNDED_m2'][0]}"
           f" .. {ew['released_lines_restated_HELD_BOUNDED_m2'][1]} m2; all 11 dry lines miss "
           f"{ew['all_11_dry_lines_missing_m2'][0]} .. {ew['all_11_dry_lines_missing_m2'][1]} m2; never in the engine "
           "columns.\n")
    r = [c for c in st["sections"] if c["section_id"] == "T-543/blockwork"][0]["restatement"]
    md += (f"Blockwork restated by T-550: UNRESOLVED {r['unresolved_before_m2']} -> {r['unresolved_after_m2']} m2, "
           "named: " + "; ".join(f"{u['part'][:95]} {u['m2']}" for u in r["unresolved_named"]) + ".\n")
    md += "\nReclasses (R-T557-1 (b)): " + "; ".join(f"{m['tag']} {m['section_id']} {m['row'][:50]} {m['from']} -> "
                                                    f"{m['to']} {m['delta']}" for m in st["reclasses"]) + ".\n"
    md += ("\nCorrections applied: " + ", ".join(st["provenance"]["corrections_applied"])
           + f", T-550. Reports covered: {', '.join(REPORTS_COVERED)}; pending: {', '.join(REPORTS_PENDING)}.\n")
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-557 statement differs from out/")
            return 1
        print("T-557 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
