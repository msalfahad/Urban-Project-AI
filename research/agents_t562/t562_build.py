"""T-562: the reconciled-quantities statement V3 = the T-557 statement (read only) + T-551 (B10 columns / necks / lift
pit walls / footing line / blinding, m3) + T-553 (B3 floor tile, m2) as new sections, the T-559 restatement of the B9
openings leftover, and the T-556 supersession of the B5 dry-plaster restatement. No private input.

  python3 -I research/agents_t562/t562_build.py --write   # write out/
  python3 -I research/agents_t562/t562_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t562_adapters as Y  # noqa: E402

X, SA, S, A, D = Y.X, Y.SA, Y.S, Y.A, Y.D
sys.path.insert(0, str(Y.T557))
sys.path.insert(0, str(X.T554))
import t557_build as B557  # noqa: E402
import t554_build as B554  # noqa: E402

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T562.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T562.md"
REPORTS_COVERED = B557.REPORTS_COVERED + ["T-551", "T-553", "T-556", "T-559"]
REPORTS_PENDING = ["T-560", "T-561", "T-565", "T-567", "T-568"]
EXTRA_KEYS = B557.EXTRA_KEYS + ("correction",)
NEW_SECTIONS = ("T-551/columns", "T-551/necks", "T-551/lift-walls", "T-551/footing-line", "T-551/blinding",
                "T-553/floor-tile")
TOUCHED = ("T-543/blockwork", "T-552/plaster-internal")
ENGINE_WRONG_CONFIRMED = dict(X.ENGINE_WRONG_CONFIRMED)
ENGINE_WRONG_CONFIRMED[("T-553/floor-tile", "1F bed room 380 x 430")] = Y.T553_FIX
ROW_KEYS = ("name", "delta", "class", "source_cause", "engine_status", "held_line_ids", "fix_row", "source")


def assemble(index: dict) -> tuple[list[dict], dict, dict]:
    secs, prov, ctx = B557.assemble(index)
    ids = [x["section_id"] for x in secs]
    d559 = json.loads(Y.T559_JSON.read_text(encoding="utf-8"))
    d556 = json.loads(Y.T556_JSON.read_text(encoding="utf-8"))
    inp = SA._t543_inputs()
    held = [x for x in inp.engine_lines() if x["class"] == "HELD"]
    i543, ipl = ids.index("T-543/blockwork"), ids.index("T-552/plaster-internal")
    secs[i543] = Y.t559_restate(secs[i543], d559, inp.engine_walls(), held)
    secs[ipl] = Y.t556_supersede(secs[ipl], d556, index)
    new = Y.t551_sections(index) + [Y.t553_section(index)]
    for x in [secs[i543], secs[ipl]] + new:
        SA.refuse_held_as_zero(x)
        SA.bind_cross_family(x, index)
        prov["valued_lines_not_in_V3_0_57_index"][x["section_id"]] = A.bind_to_index(SA.for_builder(x), index)
    secs += new
    for p in (Y.T551_JSON, Y.T553_JSON, Y.T556_JSON, Y.T559_JSON, Y.T292_CSV, HERE / "t562_adapters.py",
              Y.T557 / "t557_adapters.py", Y.T557 / "t557_build.py"):
        prov["inputs"][str(p.relative_to(Y.ROOT))] = SA.sha(p)
    ctx.update({"d556": d556, "d559": d559})
    return secs, prov, ctx


def _row_core(r: dict) -> tuple:
    return tuple(json.dumps(r.get(k), sort_keys=True) for k in ROW_KEYS)


def check_unchanged(st: dict, by_id: dict, prev: dict) -> None:
    """Every T-557 section other than the two targets is identical; the targets change only where T-559 / T-556 act."""
    old = {c["section_id"]: c for c in prev["sections"]}
    new = {c["section_id"]: c for c in st["sections"]}
    for sid, c0 in old.items():
        c = new.get(sid)
        if c is None:
            raise Y.AdapterError(f"{sid}: section lost")
        if sid not in TOUCHED:
            if c != c0:
                raise Y.AdapterError(f"{sid}: changed outside the T-562 targets")
            continue
        for k in ("reference_total", "engine_valued", "engine_bounded", "difference", "held_count", "valued_count"):
            if c[k] != c0[k]:
                raise Y.AdapterError(f"{sid}: {k} moved ({c0[k]} -> {c[k]})")
    pl, pl0 = new["T-552/plaster-internal"], old["T-552/plaster-internal"]
    if [_row_core(r) for r in pl["rows"]] != [_row_core(r) for r in pl0["rows"]] or pl["by_class"] != pl0["by_class"]:
        raise Y.AdapterError("plaster internal: rows or classes changed (only the beside restatement may change)")
    b, b0 = new["T-543/blockwork"], old["T-543/blockwork"]
    replaced = {r["name"] for r in by_id["T-543/blockwork"]["t559"]["replaced_rows"]}
    keep0 = [r for r in b0["rows"] if r["name"] not in replaced]
    keep = [r for r in b["rows"] if r.get("correction") != "T-559"]
    if len(keep0) != len(keep):
        raise Y.AdapterError("blockwork: rows added or lost outside the T-559 target")
    for r, r0 in zip(keep, keep0):
        if _row_core(r) != _row_core(r0) or not (r.get("note") or "").startswith(r0.get("note") or ""):
            raise Y.AdapterError(f"blockwork: row {r0['name'][:60]} changed outside the T-559 target")
    exp = Y.t559_expected_by_class(b0["by_class"], by_id["T-543/blockwork"])
    if b["by_class"] != exp:
        raise Y.AdapterError(f"blockwork: class totals {b['by_class']} != expected {exp}")


def build_from(secs: list[dict], prov: dict, index: dict, ctx: dict, prev: dict | None = None) -> dict:
    st = B554.build_from(secs, prov, index)              # T-548 closure + T-554 correction checks
    by_id = {x["section_id"]: x for x in secs}
    prev = json.loads(B557.JSON_OUT.read_text(encoding="utf-8")) if prev is None else prev
    prev_by = {c["section_id"]: c for c in prev["sections"]}
    moves = list(prev["reclasses"])
    for c in st["sections"]:
        src = by_id[c["section_id"]]
        if [r["name"] for r in c["rows"]] != [r["name"] for r in src["rows"]]:
            raise Y.AdapterError(f"{c['section_id']}: row order changed in the builder")
        for r, r0 in zip(c["rows"], src["rows"]):
            for k in EXTRA_KEYS:
                if k in r0:
                    r[k] = r0[k]
        if "beside" in src:
            c["beside"] = src["beside"]
        if c["section_id"] in prev_by and "restatement" in prev_by[c["section_id"]]:
            c["restatement"] = prev_by[c["section_id"]]["restatement"]
        if c["section_id"] in NEW_SECTIONS:
            exp = Y.expected_by_class(src["source_by_class"], src["rows"])
            if c["by_class"] != exp:
                raise Y.AdapterError(f"{c['section_id']}: class totals {c['by_class']} != report moved by the "
                                     f"listed reclasses {exp}")
        if c["section_id"] in NEW_SECTIONS + ("T-543/blockwork",):
            for r in src["rows"]:
                m = r.get("reclass")
                if m and m["tag"].startswith("F-T562"):
                    moves.append({"section_id": c["section_id"], "row": r["name"], **m})
    check_unchanged(st, by_id, prev)
    t = by_id["T-543/blockwork"]["t559"]
    c543 = [x for x in st["sections"] if x["section_id"] == "T-543/blockwork"][0]
    c543["restatement_t559"] = {"by": "T-559 (R-T559-1 / R-T559-2, MERGED 431ac67f)",
                                "replaced_rows": t["replaced_rows"],
                                "openings_by_cause_report": t["openings_by_cause_report"],
                                "unresolved_before_m2": prev_by["T-543/blockwork"]["by_class"]["UNRESOLVED"],
                                "unresolved_after_m2": c543["by_class"]["UNRESOLVED"],
                                "edge_summary": t["edge_summary"]}
    X.verify_engine_wrong(st, ENGINE_WRONG_CONFIRMED)
    X.verify_labels(st, NEW_SECTIONS + ("T-545/beams", "T-547/wall-tile", "T-552/plaster-internal",
                                        "T-552/plaster-external"))
    for r in c543["rows"]:
        if r.get("correction") == "T-559" and r.get("verification") not in X.VERIF:
            raise Y.AdapterError(f"blockwork / {r['name']}: no verification label")
    Y.verify_supersession(st, ctx["d556"])
    Y.verify_per_run_held(st)
    Y.add_gross(st)
    Y.verify_gross(st)
    Y.verify_blinding_apart(st)
    st["reclasses"] = moves
    st["reports_covered"] = REPORTS_COVERED
    st["reports_pending"] = REPORTS_PENDING
    st["rule"] = "R-T548-1 + R-T554-1 + R-T557-1 + R-T562-1"
    return json.loads(json.dumps(st, sort_keys=True))


def build() -> dict:
    index = SA.load_index()
    secs, prov, ctx = assemble(index)
    return build_from(secs, prov, index, ctx)


def to_markdown(st: dict) -> str:
    md = ("# T-562 reconciled-quantities statement V3 (generated; reference - engine, + = in the reference only)\n\n"
          + S.to_markdown(st) + "\n")
    md += ("| Section | Unit | Reference | Engine valued | Bounded | Net diff. | Gross abs | % of ref. | ENGINE_WRONG | "
           "HELD (net / gross) | UNRESOLVED (net / gross) |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    for c in st["sections"]:
        b, k, g = c["engine_bounded"], c["by_class"], c["by_class_gross_abs"]
        md += (f"| {c['section_id']} | {c['unit']} | {c['reference_total']} | {c['engine_valued']} | AT_LEAST "
               f"{b['low_at_least']} .. {'OPEN' if b['high_open'] else b['high']} | {c['difference']} | "
               f"{c['gross_abs']} | {c['difference_pct_of_reference']} | {k['ENGINE_WRONG']} | {k['HELD']} / "
               f"{g['HELD']} | {k['UNRESOLVED']} / {g['UNRESOLVED']} |\n")
    secs = {c["section_id"]: c for c in st["sections"]}
    cur = Y.current_restatement(secs["T-552/plaster-internal"]["beside"])
    old = secs["T-552/plaster-internal"]["beside"]["engine_wrong_restated_superseded_T557"]
    md += (f"\nPlaster ENGINE_WRONG beside (CURRENT, {cur['source'][:40]}): the 4 released dry lines "
           f"{cur['released_lines_now_m2']} m2 restate to HELD (BOUNDED) "
           f"{' .. '.join(cur['released_lines_restated_HELD_BOUNDED_m2'])} m2; all 11 dry lines "
           f"{' .. '.join(cur['all_11_dry_lines_restated_HELD_BOUNDED_m2'])} m2; never in the engine columns. "
           f"SUPERSEDED (by {old['superseded_by']}): T-557 {' .. '.join(old['released_lines_restated_HELD_BOUNDED_m2'])}"
           " m2.\n")
    r = secs["T-543/blockwork"]["restatement_t559"]
    md += (f"Blockwork restated by T-559: UNRESOLVED {r['unresolved_before_m2']} -> {r['unresolved_after_m2']} m2 "
           f"(openings -26.284 by id: {', '.join(f'{k} {v}' for k, v in sorted(r['openings_by_cause_report'].items()))}"
           f"; edge members {r['edge_summary']['CARRIED_ONCE']} carried once, {r['edge_summary']['OMITTED']} omitted).\n")
    ew = secs["T-553/floor-tile"]["beside"]["engine_wrong_restated"]
    md += (f"Floor tile ENGINE_WRONG beside ({ew['finding']}, fix row {ew['fix_row']}): +{ew['corrected_area_m2']} m2 "
           f"{ew['area_status']}, finish class HELD; engine with the correction {ew['engine_with_correction_m2']} m2 "
           "(beside only).\n")
    bl = secs["T-551/blinding"]["beside"]
    md += (f"Blinding split beside: HELD {' .. '.join(bl['held_share_range_m3'])} + RULE_DIFFERENCE "
           f"{' .. '.join(bl['rule_difference_share_range_m3'])} m3 (one HELD row).\n")
    md += "\nReclasses (R-T557-1 (b), R-T562-1 (b) / (c)): " + "; ".join(
        f"{m['tag']} {m['section_id']} {m['row'][:50]} {m['from']} -> {m['to']} {m['delta']}" for m in st["reclasses"]) + ".\n"
    md += (f"\nReports covered: {', '.join(REPORTS_COVERED)}; pending: {', '.join(REPORTS_PENDING)}.\n")
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-562 statement differs from out/")
            return 1
        print("T-562 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
