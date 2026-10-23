"""T-196: scope crosswalk v1 on the development villa (residential review R7). Reads only; prints counts, statuses,
item codes, engine keys and row ids (workbook code : sheet ordinal : row) - never a cell text, a coordinate or a name.

    python3 -I research/agents_t196/alsenan_t196.py <candidate run dir> --lines <V3_0_x_BOQ_LINES.json> [--out DIR]

<candidate run dir> is the v304 folder of research/agents_t167/v304_run.py on the Drive copies (P7757.dxf from
P7757_DXF_COMPRESSED.zip, "ST7757 dxf.dxf"), i.e. the opt-in candidate ARCH_TAKEOFF_V3.0.4 (d86de34a). --out writes
CROSSWALK_T196.json beside nothing in the repository unless asked (the committed CSVs are written by --commit-csv).

Inputs from the repository (no Drive file is copied):
  - freelancer rows: tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json (DETAIL / SUBTOTAL / COVER_TOTAL records);
    row id = <workbook code>:S<sheet ordinal in FREELANCER_RAW_ROWS.json order>:<row>. Sheet names are not printed.
  - ledger elements (merged, checker-verdict cited): T-183 pool, T-184 staircases, T-185 domes, T-164 railings.
  - required sheets: research/agents_t195/MISSING_T195.csv (T-195 document register, merged 06c2b045).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.source import element_register_v0 as E  # noqa: E402
from engine.source import scope_crosswalk_v1 as X  # noqa: E402

B1 = ROOT / "tests/alsenan/registers_b1"
P = "ALSENAN"            # ledger element id prefix (the register's own ids carry the project id and revision)

# ---- ledger elements (merged research; element first, ERS s.2 step 1) -------------------------------------------
LEDGER = [
    {"id": f"{P}/POOL-01", "kind": "POOL", "floor": "GF", "source": "T-183 r2 (MERGED 6380294; checker 16:14 base "
     "4.374 + walls 2.828 = 7.202 m3 VERIFIED)", "refs": ["ST p.7 pool detail", "ARCH GF plan sheet03", "NW cut"]},
    {"id": f"{P}/ST-01.GF-1F", "kind": "STAIR", "floor": "GF", "source": "T-184 (MERGED 924c2bd)",
     "refs": ["ST p.4", "section A-A sheet10"]},
    {"id": f"{P}/ST-01.1F-2F", "kind": "STAIR", "floor": "1F", "source": "T-184 (MERGED 924c2bd; D-T184-1)",
     "refs": ["ST p.5", "section A-A sheet10", "ARCH 1F / 2F plans"]},
    {"id": f"{P}/ST-01b", "kind": "STAIR", "floor": "GF", "source": "T-184 (MERGED 924c2bd)",
     "refs": ["ARCH GF plan sheet03", "section A-A sheet10"]},
    {"id": f"{P}/ST-02", "kind": "STAIR", "floor": "GF", "source": "T-184 (MERGED 924c2bd)",
     "refs": ["ST p.4", "ARCH GF / 1F plans"]},
    {"id": f"{P}/ST-03", "kind": "STAIR", "floor": "GF", "source": "T-184 (MERGED 924c2bd; entrance stair E1)",
     "refs": ["ARCH GF plan sheet03"]},
    {"id": f"{P}/DOME-A", "kind": "DOME", "floor": "2F", "source": "T-185 (MERGED 94e39ee6; S0 shell VERIFIED by "
     "the checker 18:15)", "refs": ["ST p.7 dome detail", "ST p.5"]},
    {"id": f"{P}/DOME-B", "kind": "DOME", "floor": "2F", "source": "T-185 (MERGED 94e39ee6)",
     "refs": ["ST p.7 dome detail", "ST p.5"]},
    {"id": f"{P}/DOME-TOWER", "kind": "DOME", "floor": "ROOF", "source": "T-185 (MERGED 94e39ee6; architectural "
     "only: elevation 441 / 215, no structural drawing, HELD)", "refs": ["ARCH elevations"]},
]
# the candidate stair line T-187 identified as a dome outline (register ruling 04:20): reported MISREAD, never a stair
MISREAD_KEY = "P-C:STAIRS:1F:SITE-b845e1e78b1f74a8"
RAIL_NOT_ELEMENTS = {"RL-11": "no railing drawn (render only, T-161)", "RL-12": "EXCLUDED: none drawn (UP-STAIR-013)"}


def railing_elements():
    out, seen = [], OrderedDict()
    for r in csv.DictReader((ROOT / "research/agents_t164/RAILINGS_T164.csv").open(encoding="utf-8")):
        seen.setdefault(r["RUN"], r)
    for run, r in seen.items():
        if run in RAIL_NOT_ELEMENTS:
            continue
        out.append({"id": f"{P}/{run}", "kind": "RAILING", "floor": None, "status": r["RUN_STATUS"],
                    "source": f"T-164 (MERGED 390fabf4) {r['KIND']} {r['RUN_STATUS']}", "refs": ["T-164 RAILINGS_T164"]})
    return out


# ---- candidate lines -> ledger elements (lines the register v0 leaves UNLINKED as later kinds) --------------------
def ledger_links(lines):
    """line_id -> [element ids], with the evidence for each binding; lines not bound keep the register's reason or the
    reason given here."""
    links, why, unbound = {}, {}, {}
    for ln in lines:
        k = ln["location"].get("element_id") or ""
        code = ln["item_code"]
        dims = ((ln.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
        if code == "STR.CONC.POOL" and k.startswith("P-C:SCOPE:POOL:"):
            links[ln["line_id"]] = [f"{P}/POOL-01"]
            why[ln["line_id"]] = "route G pool family: one pool drawn (T-183)"
        elif code == "STR.CONC.DOME" and k.startswith("P-C:SCOPE:DOMES:"):
            # two convention shells on the 2F family: the two terrace domes; which shell is A / B is not needed for
            # scope (each line is ONE of the two): bound to both as an aggregate pair
            links[ln["line_id"]] = [f"{P}/DOME-A", f"{P}/DOME-B"]
            why[ln["line_id"]] = "route G dome family 2F: the terrace domes (T-185 S0); tower dome has no line"
        elif code == "STR.CONC.STAIR" and k.startswith("P-C:SCOPE:STAIRS:GF:") and k.endswith(":FLIGHTS"):
            links[ln["line_id"]] = [f"{P}/ST-01.GF-1F"]
            why[ln["line_id"]] = "T-184: route G GF flights = ST-01 GF -> 1F only (2 flights + winder)"
        elif code == "STR.CONC.STAIR" and k.startswith("P-C:SCOPE:STAIRS:GROUND:") and k.endswith(":FLIGHTS"):
            links[ln["line_id"]] = [f"{P}/ST-03"]
            why[ln["line_id"]] = "T-184: route G GROUND flight 2.80 m wide, 5 risers = entrance stair E1"
        elif code == "STR.CONC.STAIR" and k.startswith("P-C:STAIRS:GROUND:SITE-") and \
                abs(float(dims.get("zone_m2") or 0) - 8.3723) < 0.001:
            links[ln["line_id"]] = [f"{P}/ST-02"]
            why[ln["line_id"]] = "T-184: the 8.37 m2 winder region on the ground-beam plan = part of ST-02"
        elif code == "STR.CONC.STAIR" and k.startswith(MISREAD_KEY):
            unbound[ln["line_id"]] = (
                "MISREAD: not a stair. A dome outline on the 1F roof read as a winder region (T-187 finding: 18 lines "
                "from one point to r 2.211 m over 360 deg; ELEMENT_REGISTER ruling 2026-10-23 04:20: owner trade "
                "DOMES, the stair trade takes nothing; HELD MISREAD in V3.0.6, retired by T-193 when the verified "
                f"dome shells replace the dome conventions). Zone {dims.get('zone_m2')} m2, width {dims.get('width_m')} m")
        elif code == "STR.CONC.STAIR" and k.startswith("P-C:STAIRS:"):
            unbound[ln["line_id"]] = (
                f"stair site region not bound to a staircase: kind {dims.get('kind')}, width {dims.get('width_m')} m, "
                f"zone {dims.get('zone_m2')} m2, storey rise {dims.get('storey_rise_m')} m; matches no T-184 flight by "
                "geometry (ST-01 1F -> 2F = two straight 1.20 m flights + landing): either the ST-01 shaft read as one "
                "winder region (the D-T184-1 place) or another drawing; physical element to establish (Lead / Checker)")
    return links, why, unbound


# ---- freelancer rows ------------------------------------------------------------------------------------------------
def sheet_ordinals():
    raw = json.loads((B1 / "FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    order = OrderedDict()
    for r in raw["rows"]:
        order.setdefault((r["file"], r["sheet"]), len(order))
    return order


def freelancer_rows():
    order = sheet_ordinals()
    bench = json.loads((B1 / "BENCHMARK_NORMALISED.json").read_text(encoding="utf-8"))
    rows = []
    for r in bench["records"]:
        s = order[(r["file"], r["sheet"])]
        unit = {"\u06452": "m2", "\u06453": "m3", "\u0645.\u0637": "m"}.get(r["unit"], r["unit"])
        rows.append({"row_id": f"{r['file']}:S{s}:{r['row']}", "trade": r["trade"], "unit": unit, "qty": r["qty"],
                     "row_kind": r["row_kind"], "floor": r.get("floor"), "subtrade": r.get("subtrade"),
                     "label_en": r.get("label_en")})
    return rows


FLOOR = {"GF": "GF", "1F": "1F", "ROOF": "2F"}      # his column / beam floors: ROOF = the columns of the 2F storey


def row_map(rows, elements):
    """the RC workbook (structure) in full; other workbooks NOT_MAPPED with the reason (next step of the review)."""
    m = {}
    labels = Counter((e["kind"], X._label_base(e.get("label")), e.get("floor")) for e in elements)
    has = lambda kind, base, floor=None: any(k == kind and b == base and (floor is None or f == floor)
                                             for (k, b, f) in labels)
    for r in rows:
        if r["row_kind"] != "DETAIL":
            continue
        rid, t, sub = r["row_id"], r["trade"], r.get("subtrade") or ""
        wb = rid.split(":")[0]
        if wb != "RC":
            m[rid] = {"status": "NOT_MAPPED", "reason": f"{wb} workbook: room / surface join is the next R7 step "
                      "(finish rows to register ROOM / WALL / OPEN elements)"}
            continue
        if t == "BLINDING":
            m[rid] = {"select": {"kind": "FTG"}, "component": "blinding", "basis": "blinding under the footings"}
        elif t == "FOOTING":
            mark = {"FF": "FF", "FN": "FN"}.get(sub, sub)
            m[rid] = {"select": {"kind": "FTG", "label_base": mark}, "component": "footing",
                      "basis": f"footing type mark {mark}: every footing printed with it"}
        elif t == "COLUMN" and sub.startswith("NECK:"):
            m[rid] = {"select": {"kind": "COL", "label_base": sub[5:] + ".NECK"}, "component": "neck",
                      "basis": "neck of every column printed with the mark"}
        elif t == "COLUMN" and sub.startswith("COLUMN:"):
            m[rid] = {"select": {"kind": "COL", "label_base": sub[7:], "floor": FLOOR.get(r["floor"])},
                      "component": "column", "basis": "columns of the mark on that storey"}
        elif t == "SLAB":
            m[rid] = {"select": {"kind": "SLAB", "floor": FLOOR.get(r["floor"])}, "component": "slab",
                      "basis": "his slab row covers the storey's slab panels"}
        elif t == "OTHER_CONCRETE" and sub == "GROUND_SLAB":
            m[rid] = {"select": {"kind": "SLAB", "floor": "GROUND"}, "component": "ground slab",
                      "basis": "ground slab panels"}
        elif t in ("STRAP_BEAM", "BEAM") or (t == "GROUND_BEAM"):
            m[rid] = {"status": "NOT_MAPPED", "reason": "beam / strap marks are not carried by register v0 "
                      "(route G bands have no printed mark): join by mark pending"}
        elif t == "OTHER_CONCRETE" and sub == "ELEVATOR_WALL":
            m[rid] = {"status": "NOT_MAPPED", "reason": "lift walls are a later register kind (no ledger merged)"}
        elif t == "STAIR_CONCRETE":
            lab = r.get("label_en") or ""
            if lab.startswith("entrance stair"):
                m[rid] = {"elements": [f"{P}/ST-03"], "basis": "T-184: his entrance stair = E1"}
            elif lab.startswith("stair 2"):
                m[rid] = {"elements": [f"{P}/ST-02"], "basis": "T-184: his 'stair 2' = the round reception stair"}
            elif lab.startswith("main stair"):
                m[rid] = {"elements": [{"id": f"{P}/ST-01.GF-1F", "component": "flights"},
                                       {"id": f"{P}/ST-01.1F-2F", "component": "flights"}],
                          "basis": "T-184: his main stair 4 flights = ST-01 both storeys"}
            elif lab.startswith("stair landing"):
                m[rid] = {"elements": [{"id": f"{P}/ST-01.GF-1F", "component": "landings"},
                                       {"id": f"{P}/ST-01.1F-2F", "component": "landings"}],
                          "basis": "T-184: his 3 landings = ST-01 half landings + arrival"}
        elif t == "OTHER_CONCRETE" and sub == "DOME":
            m[rid] = {"elements": [f"{P}/DOME-A", f"{P}/DOME-B", f"{P}/DOME-TOWER"],
                      "basis": "his 3 domes (T-185): two terrace domes drawn in structure, the tower dome only in "
                               "the architecture",
                      "not_drawn_parts": [{"part": "tower dome shell (3rd dome)", "discipline": "ST",
                                           "element": f"{P}/DOME-TOWER", "qty": round(r["qty"] / 3, 6),
                                           "searched": ["ST p.5", "ST p.6", "ST p.7 dome detail", "ARCH elevations"]}]}
        elif t == "OTHER_CONCRETE" and sub == "POOL":
            lab = r.get("label_en") or ""
            searched = ["ARCH GF plan sheet03", "ST p.7 pool detail", "NW cut", "sanitary-7757 (3 sheets)"]
            if lab.startswith("pool floor"):
                m[rid] = {"elements": [{"id": f"{P}/POOL-01", "component": "base"}], "basis": "T-183"}
            elif lab.startswith("pool walls"):
                m[rid] = {"elements": [{"id": f"{P}/POOL-01", "component": "walls"}], "basis": "T-183"}
            elif lab.startswith("pump-room"):
                m[rid] = {"status": "NOT_DRAWN", "searched": searched,
                          "basis": "T-183 item K: pump room / balance tank in no document read"}
            elif lab.startswith("pool steps"):
                m[rid] = {"status": "NOT_DRAWN", "searched": searched,
                          "basis": "T-183 item E: STEPS: NOT DRAWN, consultant item (owner 16:45)"}
    return m


def documents():
    fam = {"site / plot layout with external works": (["STR.CONC.BOUNDARY_WALL"], []),
           "roof plan (top roof: falls, drains, parapets, waterproofing)": (["FIN.WP.ROOF"], []),
           "door / window schedule": (["ARCH.WINDOW", "DOOR."], ["ALUMINIUM"]),
           "finishes schedule or specification": (["FIN.FLOOR", "FIN.WALL", "FIN.EXT"], []),
           "reflected ceiling plan": (["FIN.CEILING"], ["CEILING"]),
           "wet-room / kitchen details": (["FIN.WALL.TILE", "FIN.WP.WALL_UPTURN"], []),
           "stair details (architectural)": (["FIN.RAILING", "FIN.MARBLE.TREAD", "FIN.MARBLE.RISER"], ["MARBLE"]),
           "water supply": ([], []), "electrical": ([], []), "air conditioning": ([], [])}
    out = []
    for r in csv.DictReader((ROOT / "research/agents_t195/MISSING_T195.csv").open(encoding="utf-8")):
        f, t = fam.get(r["item"], ([], []))
        out.append({"item": r["item"], "status": r["status"], "families": f, "trades": t})
    return out


def run(run_dir, lines_file):
    reg = E.build_dir(run_dir, lines_file)
    lines = json.loads(Path(lines_file).read_text(encoding="utf-8"))
    links, reasons = X.register_links(reg)
    lk, why, unbound = ledger_links(lines)
    for lid, els in lk.items():
        links[lid] = els
        reasons.pop(lid, None)
    reasons.update(unbound)
    elements = X.build_elements(reg, LEDGER + railing_elements())
    rows = freelancer_rows()
    rmap = row_map(rows, elements)
    rep = X.crosswalk(elements, [{k: r[k] for k in ("row_id", "trade", "unit", "qty", "row_kind", "floor")}
                                 for r in rows], rmap, lines, links, (), documents(), reasons)
    return rep, reg, lines, why


def show(rep, lines):
    s = rep["summary"]
    print("ROWS", json.dumps(s["rows"], sort_keys=True), "accounted", s["all_rows_accounted"])
    for t, c in s["rows_by_trade"].items():
        print("  trade", t, json.dumps(c, sort_keys=True))
    print("LINES", json.dumps(s["lines"], sort_keys=True))
    un = Counter((ln["item_code"], ln["reason"][:90]) for ln in rep["lines"] if ln["status"] == "UNLINKED")
    for (c, rsn), n in sorted(un.items()):
        print("  UNLINKED", n, c, "-", rsn)
    print("PIECES", json.dumps(rep["pieces"], sort_keys=True)[:300])
    for (fl, mark, st, ncomp), n in sorted(columns(rep).items(), key=lambda t: tuple(map(str, t[0]))):
        print("  COLUMNS", fl, mark, st, "components", ncomp, "elements", n)
    for k, v in t119_check(rep).items():
        print("  T119", k, v["t119"], v["crosswalk"], "same" if v["t119"] == v["crosswalk"] else "DIFF")
    print("ELEMENTS", json.dumps(s["elements"], sort_keys=True), "missing by kind",
          json.dumps(s["elements_missing_by_kind"], sort_keys=True))
    for e in rep["elements"]:
        if e["source"] != "ELEMENT_REGISTER_V0":
            print("  LEDGER", e["id"], e["status"], "lines", len(e["lines"]), "rows", e["reference_rows"])
    for f in rep["findings"]:
        print("  FINDING", json.dumps(f, sort_keys=True)[:260])
    for d in rep["not_issued"]:
        print("  NOT_ISSUED", d["item"], "lines", len(d["candidate_lines"]), "rows", len(d["reference_rows"]))
    for r in rep["rows"]:
        if r["status"] in ("SCOPE_UNKNOWN",):
            print("  ROW", r["row_id"], r["status"], r.get("reason"))


# data note (checker 02:08): only what the crosswalk needs. His quantity and unit are written only where they ARE the
# finding (NOT_DRAWN rows and NOT_DRAWN parts: reference quantity on no drawing); every other row carries its id,
# status, elements and reason only (his values stay in the frozen tests/alsenan/registers_b1 benchmark).
CSV_ROWS = ("row_id", "status", "elements", "components", "not_applicable", "unit", "qty", "not_drawn_parts", "reason")


def _short(e):
    return e.split("/", 1)[-1] if e.startswith(P) else e.split("/")[-2] + "/" + e.split("/")[-1]


def columns(rep):
    """physical columns per (storey, mark) after the r2 collapse: members (concrete + steel components) and the
    NOT_APPLICABLE printed marks, for the checker's own count."""
    out = Counter()
    for e in rep["elements"]:
        if e["kind"] == "COL" and e["source"] == "ELEMENT_REGISTER_V0":
            st = "NOT_APPLICABLE" if e.get("register_status") == "NOT_APPLICABLE" else "MEMBER"
            out[(e["floor"], X._label_base(e.get("label")), st, len(e.get("components") or [None]))] += 1
    return out


def t119_check(rep):
    """per (storey, mark): physical columns after the collapse vs the T-119 column ledger (MERGED; one row per drawn
    column, research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv). Counts only; foundation necks are not in T-119."""
    t = Counter((r["storey"], r["mark"]) for r in csv.DictReader(
        (ROOT / "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv").open(encoding="utf-8")))
    m = Counter()
    for (fl, mark, st, _c), n in columns(rep).items():
        if st == "MEMBER" and fl != "FDN":
            m[(fl, mark)] += n
    return {f"{fl} {mark}": {"t119": t[(fl, mark)], "crosswalk": m[(fl, mark)]}
            for fl, mark in sorted(set(t) | set(m), key=lambda k: tuple(map(str, k)))}


def rows_csv(rep):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_ROWS, lineterminator="\n")
    w.writeheader()
    for r in rep["rows"]:
        nd = r["status"] == "NOT_DRAWN"
        w.writerow({"row_id": r["row_id"], "status": r["status"],
                    "unit": r["unit"] if nd or r.get("not_drawn_parts") else "",
                    "qty": round(r["qty"], 6) if nd and r["qty"] is not None else "",
                    "elements": " ".join(_short(e) for e in r["elements"]),
                    "components": " ".join(r.get("components") or []),
                    "not_applicable": " ".join(_short(e) for e in r.get("not_applicable") or []),
                    "not_drawn_parts": "; ".join(f"{p['part']} ({p['discipline']}) {p['reference_qty']}"
                                                 for p in r.get("not_drawn_parts") or []),
                    "reason": r.get("reason") or r.get("basis") or ""})
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--out")
    ap.add_argument("--commit-csv", action="store_true", help="write ROWS_T196.csv / summary.json in this folder")
    a = ap.parse_args(argv)
    rep, reg, lines, why = run(a.run_dir, a.lines)
    again, _r, _l, _w = run(a.run_dir, a.lines)
    print("rerun identical", rep == again, "lines", len(lines), "register elements", len(reg["elements"]))
    show(rep, lines)
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "CROSSWALK_T196.json").write_text(json.dumps(rep, indent=1, sort_keys=True), encoding="utf-8")
    if a.commit_csv:
        (HERE / "ROWS_T196.csv").write_text(rows_csv(rep), encoding="utf-8")
        summ = dict(rep["summary"], ledger_elements={e["id"]: {"status": e["status"], "lines": len(e["lines"]),
                                                              "rows": e["reference_rows"]}
                                                     for e in rep["elements"] if e["source"] != "ELEMENT_REGISTER_V0"},
                    findings=rep["findings"], not_issued=[{k: (len(v) if isinstance(v, list) and k.endswith(
                        ("lines", "rows")) else v) for k, v in d.items()} for d in rep["not_issued"]],
                    line_bindings=sorted(set(why.values())),
                    pieces=rep["pieces"], t119_column_check=t119_check(rep),
                    columns=dict(sorted(sum((Counter({f"{fl} {mark} {st}": n}) for (fl, mark, st, _c), n in
                                             columns(rep).items()), Counter()).items())))
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
