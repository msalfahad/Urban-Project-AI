"""T-565 development-villa run (research, unwired): B1 EARTHWORKS on the candidate of record V3.0.58 against the
freelancer, by component (R-T565-1 .. 4 in t565_rules.py).

Engine lines: research/agents_t507/out/LINE_INDEX_V3_0_57.json (V3.0.58 changes FIN.WP.ROOF / ROOF_UPTURN only,
R-T507-1 (e); every STR.EARTH / STR.CONC line asserted below). Earthworks terms: the merged T-350 r2 (FILL, summary),
T-484 (displacement re-measure), T-497 (trench ownership) and T-320 (displacement ledger) files. Benchmark: the B1
census of every non-empty row of the six freelancer workbooks (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json,
885 rows, hashed against the Drive files) and the web-app report rows (WEB_APP_ROWS.json, 88 rows); the concrete +
rebar workbook is re-read from .work/private when present (`private_check`). Tracked output:
out/T565_EARTHWORKS_RECONCILE.json (engine figures, component terms and search counts only; no row of his).

    python3 -I research/agents_t565/t565_alsenan.py [--write] [--private <concrete_rebar.xlsx>]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
ROOT = RES.parent
sys.path.insert(0, str(HERE))
import t565_rules as R  # noqa: E402

LINE_INDEX = RES / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
T350R2 = RES / "agents_t350r2" / "summary_t350r2.json"
T484 = RES / "agents_t484" / "summary_t484.json"
T320_LEDGER = RES / "agents_t320" / "LEDGER_T320.csv"
RAW_ROWS = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"
WEB_ROWS = ROOT / "tests" / "alsenan" / "registers_b1" / "WEB_APP_ROWS.json"
OUT = HERE / "out" / "T565_EARTHWORKS_RECONCILE.json"

# Earthworks vocabulary searched in his rows (Arabic roots + English): excavation, backfill / filling, soil, levelling,
# compaction, transport / disposal, sand, termite / soil treatment, site clearance.
KEYWORDS = ("حفر", "ردم", "دفان", "تربة", "تربه", "تسوية", "دمك", "رص ", "نقل", "مخلفات", "رمل", "نمل", "مبيد",
            "تنظيف الموقع", "excavat", "backfill", "fill", "earth", "soil", "compact", "termite", "disposal")
D = Decimal

# components in the order of the reconciliation table; family code -> BOQ family
FAMILY = {"STR.EARTH.EXCAVATION": "B1-02", "STR.EARTH.BACKFILL": "B1-03", "STR.EARTH.DISPOSAL": "B1-04"}
BASIS = {"STR.EARTH.EXCAVATION": "IN_SITU", "STR.EARTH.BACKFILL": "COMPACTED", "STR.EARTH.DISPOSAL": "IN_SITU"}


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- engine side
def index():
    d = _json(LINE_INDEX)
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return d["lines"]


def earth_lines(lines):
    out = []
    for ln in lines:
        if not ln["item_code"].startswith("STR.EARTH."):
            continue
        assert ln["unit"] == "m3"
        code, basis = ln["item_code"], BASIS[ln["item_code"]]
        if ln["class"] == "RELEASED":
            q = R.valued(ln["measured_net"], basis, "m3")
        elif ln["held_low"] is not None:
            q = R.held_range(ln["held_low"], ln["held_high"], basis, "m3", "bounded held zone")
        else:
            q = R.held_blank(basis, "zone held blank (formation / extent / section / density not printed)")
        out.append({"line_id": ln["line_id"], "code": code, "family": FAMILY[code],
                    "zone": ln["element_id"].split(":", 2)[2], "q": q})
    return sorted(out, key=lambda r: (r["code"], r["zone"]))


def family_totals(rows):
    out = {}
    for code in FAMILY:
        t = R.total([r["q"] for r in rows if r["code"] == code])
        out[code] = {"family": FAMILY[code], "basis": t["basis"], "lines": t["n"], "valued": t["valued"],
                     "held_low": t["held_low"], "held_high": t["held_high"], "held_blank_lines": t["held_blank"]}
    return out


# --------------------------------------------------------------------------------------------- benchmark side
def search_rows(path, keywords=KEYWORDS):
    """Every non-empty row of every file (cell values AND formulas), keyword hits per file; returns counts only."""
    d = _json(path)
    rows = d["rows"]
    per_file, hits = {}, {}
    for r in rows:
        f = r.get("file") or "WEB"
        per_file[f] = per_file.get(f, 0) + 1
        s = json.dumps(r, ensure_ascii=False).lower()
        for k in keywords:
            if k.lower() in s:
                hits.setdefault(f, {}).setdefault(k, 0)
                hits[f][k] += 1
    return {"rows": len(rows), "per_file": per_file, "hits": hits}


def benchmark():
    raw = search_rows(RAW_ROWS)
    web = search_rows(WEB_ROWS)
    # every hit is read and classified (ids and category keys only): the web-app 'sand' rows are material loads
    # under the tiling, plaster and black-structure bands (unit 'qty', no m3, no plan): not an earthworks component
    web["hits_read"] = [{"id": r["id"], "category": r.get("category_nfkc"), "unit": r.get("unit"),
                         "class": "MATERIAL_LOAD_NOT_EARTHWORKS"}
                        for r in _json(WEB_ROWS)["rows"] if "رمل" in json.dumps(r, ensure_ascii=False)]
    assert not raw["hits"], f"freelancer earthworks keyword hits to read and classify: {raw['hits']}"
    # 'fill' / 'earth' / 'soil' substrings: any hit is listed by file and keyword, then read (none expected)
    return {"freelancer": raw, "web_app": web}


def private_check(xlsx):
    """Re-read the concrete + rebar workbook from .work/private: non-empty rows per sheet must equal the census and
    no cell (value or formula) carries an earthworks keyword. Returns counts only."""
    import openpyxl
    wb = openpyxl.load_workbook(xlsx)
    census = {}
    for r in _json(RAW_ROWS)["rows"]:
        if r["file"] == "RC":
            census[r["sheet"]] = census.get(r["sheet"], 0) + 1
    out, hits = {}, 0
    for ws in wb:
        n = 0
        for row in ws.iter_rows():
            vals = [c.value for c in row if c.value is not None]
            if vals:
                n += 1
                s = " ".join(str(v) for v in vals).lower()
                hits += sum(1 for k in KEYWORDS if k.lower() in s)
        out[ws.title] = {"rows": n, "census": census.get(ws.title)}
    return {"sheets": out, "keyword_hits": hits,
            "census_complete": all(v["rows"] == v["census"] for v in out.values())}


# --------------------------------------------------------------------------------------- buried ownership (R-4)
def footing_lines(lines):
    return {ln["element_id"]: ln for ln in lines if ln["item_code"] == "STR.CONC.FOOTING"}


def handle(eid):
    return eid.rsplit(":", 1)[1]


TOL_MM = 2      # insertion points are printed to the mm in both frames (one pair differs by 1 mm)
FTG_RE = re.compile(r"FTG:SH10:(?P<t>[A-Z0-9]+)@(?P<x>-?\d+),(?P<y>-?\d+):(?P<h>[0-9a-f]+)$")


def _ftg(eid):
    m = FTG_RE.search(eid)
    return (m["t"], int(m["x"]), int(m["y"]), m["h"]) if m else None


def join_footings(lines, ledger_groups):
    """Join the candidate footing lines (candidate frame) to the T-320 pit groups (foundation-sheet frame) by mark
    and position: the frame offset is derived from the pairs whose DXF handle is equal (every such pair must give
    the same offset), then every pit is matched by mark + shifted insertion point; a handle alone is NOT the key
    (6 of the 24 pits carry another handle in the candidate: the outline vs the insertion entity)."""
    fl = {e: _ftg(e) for e in footing_lines(lines) if _ftg(e)}
    pg = {g: _ftg(g) for g in ledger_groups}
    byh = {v[3]: (g, v) for g, v in pg.items()}
    offs = [(a[1] - byh[a[3]][1][1], a[2] - byh[a[3]][1][2]) for a in fl.values() if a[3] in byh]
    dx, dy = max(set(offs), key=offs.count)
    if any(abs(o[0] - dx) > TOL_MM or abs(o[1] - dy) > TOL_MM for o in offs):
        raise AssertionError(f"frame offset not unique within {TOL_MM} mm: {sorted(set(offs))}")
    pairs = {}
    for e, a in fl.items():
        hit = [g for g, v in pg.items() if v[0] == a[0] and abs(v[1] + dx - a[1]) <= TOL_MM
               and abs(v[2] + dy - a[2]) <= TOL_MM]
        if len(hit) > 1:
            raise AssertionError(f"{e}: two pits within {TOL_MM} mm")
        if hit:
            pairs[e] = hit[0]
    if len(set(pairs.values())) != len(pairs):
        raise AssertionError("two candidate lines on one pit")
    return pairs, (dx, dy)


def footing_ownership(lines):
    """Every footing concrete line -> the excavation zone(s) whose backfill it displaces, by element id."""
    fl = footing_lines(lines)
    s2 = _json(T350R2)["pits24"]
    env = {k.split(":", 1)[1]: v for k, v in s2["pool_interfaces"]["pits_in_env"].items()}   # 'SH10:F4@..:h'
    led = [r for r in csv.DictReader(open(T320_LEDGER, newline="", encoding="utf-8")) if r["kind"] == "FOOTING"]
    pit_groups = [r["group"] for r in led if r["value_m3"]]
    assert len(pit_groups) == 24
    pairs, offset = join_footings(lines, pit_groups)
    elements, shares, ff = {}, [], []
    for eid, ln in fl.items():
        if ln["class"] != "RELEASED":
            assert eid.endswith("T652:10A5")                         # F10 + F, held line (Q-31 C)
            continue
        v = R.d6(ln["measured_net"])
        elements[eid] = v
        if eid in pairs:
            g = pairs[eid].split(":", 2)[2]                          # 'SH10:F4@..:h'
            e = R.d6(D(str(env[g]["footprint_in_env_m2"])) * D(str(env[g]["H"]))) if g in env else D(0)
            shares.append((eid, "Z1-PITS-24", v - e))
            if e:
                shares.append((eid, "Z1-POOL-INTERFACE (held, F-T350R2-2)", e))
        elif _ftg(eid) and _ftg(eid)[0] == "FF":                     # lift raft: its own (held-blank) zone
            shares.append((eid, "Z1-PIT-FF (held blank)", v))
            ff.append(eid)
        else:
            raise AssertionError(f"valued footing line with no zone: {eid}")
    if len(pairs) != 24 or len(ff) != 1:
        raise AssertionError(f"pits joined {len(pairs)} / 24, FF {len(ff)}")
    own = R.ownership(elements, shares)
    # the pits share must equal the T-350 r2 displacement term, which nets the FN / F9 notch from the ledger instead
    led_sum = sum((R.d6(r["value_m3"]) for r in led if r["value_m3"]), D(0))
    return {"lines": len(fl), "valued_lines": len(elements), "valued_m3": sum(elements.values(), D(0)),
            "pits_joined": len(pairs), "frame_offset_mm": list(offset),
            "handle_differs": sorted(e for e, g in pairs.items() if _ftg(e)[3] != _ftg(g)[3]),
            "per_zone": own["per_zone"], "t350r2_footings_m3": R.d6(s2["displacement"]["footings"]),
            "t320_ledger_pits_m3": led_sum,
            "held_line": {"element": "P-C:FTG:SH10:T652:10A5", "zone": "Z1-PIT-F10F (own zone, S02)",
                          "bound": [D("2.176"), D("2.275")]}}


def blinding_split(lines):
    bl = next(ln for ln in lines if ln["element_id"].endswith("BLINDING_FOOTINGS_RELEASED"))
    s2 = _json(T350R2)["pits24"]
    zone = R.d6(s2["displacement"]["blinding"])
    pool = R.d6(bl["measured_net"]) - zone
    per_pit = sum((R.d6(v["neat_in_env_m2"]) - R.d6(v["neat_in_env_beyond_plot_m2"])
                   for v in s2["pool_interfaces"]["pits_in_env"].values()), D(0))
    own = R.ownership({bl["element_id"]: R.d6(bl["measured_net"])},
                      [(bl["element_id"], "Z1-PITS-24", zone),
                       (bl["element_id"], "Z1-POOL-INTERFACE (held, under-pool band)", pool)])
    return {"line_id": bl["line_id"], "line_m3": R.d6(bl["measured_net"]), "per_zone": own["per_zone"],
            "in_env_in_plot_plan_from_line_m2": R.d6(pool * 10),
            "in_env_in_plot_plan_per_pit_sum_m2": per_pit,
            "overlap_inside_envelope_m2": per_pit - R.d6(pool * 10)}


def strap_ownership(lines):
    t484 = _json(T484)["strap_ends"]
    vals = {ln["element_id"].split(":")[2]: R.d6(ln["measured_net"]) for ln in lines
            if ln["item_code"] == "STR.CONC.STRAP" and ln["class"] == "RELEASED"}
    shares = []
    for sb, v in vals.items():
        ends = [r for r in t484["rows"] if r["strap"] == sb]
        pits = sum((R.d6(r["m3"]) for r in ends if r["zone"] == "PITS24"), D(0))
        f10 = sum((R.d6(r["m3"]) for r in ends if r["zone"] != "PITS24"), D(0))
        shares.append((sb, "Z1-PITS-24", pits))
        if f10:
            shares.append((sb, "Z1-PIT-F10F", f10))
        shares.append((sb, "Z1-TRENCH-STRAPS (held blank)", v - pits - f10))
    own = R.ownership(vals, shares)
    assert own["per_zone"]["Z1-PITS-24"] == R.d6(t484["m3"])
    return {"lines": vals, "per_zone": own["per_zone"], "per_element": own["per_element"]}


def neck_ownership(lines):
    rows = _json(T484)["necks"]["rows"]
    held_lines = [ln for ln in lines if ln["item_code"] == "STR.CONC.NECK"]
    by = {}
    for r in rows:
        z = ("Z1-PITS-24" if r["status"] in ("CALCULATED", "CONFLICT") else
             "Z1-PIT-FF" if r["footing"] == "FF" else "Z1-PIT-F10F")
        by.setdefault(z, []).append(r)
    calc = sum((R.d6(r["m3"]) for r in rows if r["status"] == "CALCULATED"), D(0))
    return {"concrete_lines": len(held_lines), "concrete_held_bound": [
                sum((R.d6(ln["held_low"]) for ln in held_lines if ln["held_low"] is not None), D(0)),
                sum((R.d6(ln["held_high"]) for ln in held_lines if ln["held_high"] is not None), D(0))],
            "necks_per_zone": {z: len(v) for z, v in sorted(by.items())},
            "pits_calculated_29_m3_S01": calc, "pits_C8_conflict_m3": [D("0.24"), D("0.27")],
            "all_concrete_lines_held": all(ln["class"] == "HELD" for ln in held_lines)}


# ------------------------------------------------------------------------------------------- reconciliation
def components(rows, ft, bench):
    """One row per physical component; the engine side is the candidate line state, his side NO_ROW (census)."""
    ev = (f"no row in {bench['freelancer']['rows']} non-empty rows of the six freelancer workbooks "
          f"({', '.join(sorted(bench['freelancer']['per_file']))}); keyword hits "
          f"{sum(sum(v.values()) for v in bench['freelancer']['hits'].values())}")
    out = []
    for r in rows:
        his = R.no_row(r["q"]["basis"], ev)
        c = R.compare(r["q"], his)
        out.append({"component": f"{r['family']} {r['zone']}", "line_id": r["line_id"], "engine": r["q"],
                    "his": his["state"], "class": c["class"], "difference": c["difference"], "pct": c["pct"]})
    # compaction and soil treatment: not BOQ lines in the candidate (information beside; T-350 r2 / T-354)
    s2 = _json(T350R2)
    out.append({"component": "compaction layers (pits zone backfill, 0.15 m OWNER-PROVISIONAL lift)",
                "line_id": None, "engine": R.valued(R.layers(s2["pits24"]["backfill_zone_depth_m"], "0.15"), "COUNT"),
                "his": "NO_ROW", "class": "NOT_COMPARABLE", "difference": None, "pct": None,
                "note": "information beside the backfill line, not a BOQ line (no compaction standard adopted)"})
    out.append({"component": "formation compaction footprint, pits + pool", "line_id": None,
                "engine": R.valued(R.d6(s2["pits24"]["formation_compaction_m2"]) + R.d6(s2["pool"]["plan_m2"]), "AREA"),
                "his": "NO_ROW", "class": "NOT_COMPARABLE", "difference": None, "pct": None,
                "note": "the ext GB trench footprint 13.917 .. 14.180 m2 beside (T-350 r2), not added"})
    st = R.not_in_scope("AREA", "T-354: 31 sheets, DXF text, specification, owner rules searched: NOT_IN_DRAWN_SCOPE")
    out.append({"component": "B1-05 soil treatment / anti-termite", "line_id": None, "engine": st,
                "his": "NO_ROW", "class": R.compare(st, R.no_row("AREA", ev))["class"],
                "difference": None, "pct": None})
    return out


def build(private=None):
    lines = index()
    rows = earth_lines(lines)
    ft = family_totals(rows)
    bench = benchmark()
    comp = components(rows, ft, bench)
    # closures (R-T565-3): each family total re-adds from its zone rows, valued and held apart
    for code, t in ft.items():
        sub = [r["q"] for r in rows if r["code"] == code]
        v = [q for q in sub if q["state"] == "VALUED"]
        h = [q for q in sub if q["state"] == "HELD_RANGE"]
        if v:
            R.table_closes(v, "value", t["valued"])
        if h:
            R.table_closes(h, "low", t["held_low"])
            R.table_closes(h, "high", t["held_high"])
        assert len(v) + len(h) + t["held_blank_lines"] == t["lines"]
    s484 = _json(T484)["pits_backfill"]
    exc_pits = next(r["q"]["value"] for r in rows if (r["family"], r["zone"]) == ("B1-02", "Z1-PITS-24"))
    ver, rem = R.d6(s484["verified_displacement_m3"]), [R.d6(x) for x in s484["remeasured_displacement_m3"]]
    bf = next(r["q"] for r in rows if (r["family"], r["zone"]) == ("B1-03", "Z1-PITS-24"))
    closure = {"excavation": exc_pits, "verified_displacement": ver, "remeasured_displacement": rem,
               "backfill_low": exc_pits - ver - rem[1], "backfill_high": exc_pits - ver - rem[0],
               "line_low": bf["low"], "line_high": bf["high"]}
    assert closure["backfill_low"] == bf["low"] and closure["backfill_high"] == bf["high"]
    s2 = _json(T350R2)["pits24"]["displacement"]
    disp_parts = {k: R.d6(s2[k]) for k in ("blinding", "underlay", "footings")}
    assert sum(disp_parts.values(), D(0)) == ver
    doc = {
        "schema": "URBAN_T565_EARTHWORKS_RECONCILE_V1", "candidate": "ARCH_TAKEOFF_V3.0.58 (lines of V3.0.57, "
        "R-T507-1 (e): V3.0.58 moves FIN.WP.ROOF only)", "method": "EARTHWORKS_RECONCILE_V1 (R-T565-1 .. 4)",
        "level_basis": "S01 ESTIMATED (owner-accepted): footing underside -1.50, underlay 0.07 + blinding 0.10; EG "
                       "+-0.00 DERIVED (T-357)",
        "family_totals": ft, "zone_lines": rows, "components": comp, "benchmark_search": bench,
        "pits_backfill_closure": closure, "pits_verified_displacement_parts": disp_parts,
        "ownership": {"footings": footing_ownership(lines), "blinding": blinding_split(lines),
                      "straps": strap_ownership(lines), "necks": neck_ownership(lines)},
        "sensitivity_S01_pits_excavation_m3": {k: R.d6(v["excavation_insitu_m3"])
                                               for k, v in _json(T350R2)["pits24_sensitivity"].items()},
        "printed_minimum_bound_pits_m3": R.d6(_json(T350R2)["pits24_printed_minimum_bound_m3"]),
    }
    if private:
        doc["private_check"] = private_check(private)
    return doc


def _plain(o):
    if isinstance(o, Decimal):
        return format(o, "f")
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    return o


def dump(doc):
    return json.dumps(_plain(doc), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    priv = a[a.index("--private") + 1] if "--private" in a else None
    doc = build(priv)
    if "--write" in a:
        d = dict(doc)
        d.pop("private_check", None)                       # the tracked file never depends on private data
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(dump(d), encoding="utf-8")
    print(dump({k: doc[k] for k in ("family_totals", "pits_backfill_closure", "ownership")
                if k in doc} | ({"private_check": doc["private_check"]} if priv else {})))
