"""T-732 development-villa build (research, unwired): the STR.FORMWORK lines whose concrete member moved between the
T-714 basis (ARCH_TAKEOFF_V3.0.70 + merged ledgers T-711 / T-712 / T-721) and the candidate of record V3.0.73 (T-722:
T-707 plate lows and tank floors wired), re-derived face by face under R-T732-1, the census of moved members by line
id under R-T732-2, the T-724 restated soffits carried, and the four T-724 strip children given their faces.

Inputs: merged repository files, sha256-pinned in PINS.json, plus the own read of this run (column outlines by handle
on Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', sha256 9f9d1179; sizes only, no coordinates) held below as
constants and in out/T732_OWN_READ.json. Writes out/T732_FORMWORK_MOVED.json and out/T732_CENSUS.md. No candidate,
released (V2.9 + route G), rule / knowledge version or registry file is touched; nothing is wired, released or
VERIFIED.

    python3 -I research/agents_t732/t732_alsenan.py [--write | --check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, box

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, HERE.parent / "agents_t714", HERE.parent / "agents_t724"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t732_rules as R  # noqa: E402
import t714_alsenan as T714  # noqa: E402
import t724_alsenan as T724  # noqa: E402

D, BR = R.D, R.BR
SCHEMA = "URBAN_T732_FORMWORK_MOVED_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
I70 = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
I73 = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
T722 = "research/agents_t722/out/T722_SUMMARY.json"
T714J = "research/agents_t714/out/T714_FORMWORK_BOUNDS.json"
T638 = "research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json"
T332 = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
T119 = "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv"
T110 = "research/agents_t110/BEAM_MEMBER_REGISTER.csv"
T707 = "research/agents_t707/out/T707_COLUMN_TAIL.json"
T724J = "research/agents_t724/out/T724_FINDINGS.json"
PINS = (I70, I73, T722, T714J, T638, T332, T119, T110, T707, T724J,
        "research/agents_t711/out/T711_LEDGER.json", "research/agents_t712/out/T712_LEDGER.json",
        "research/agents_t721/out/T721_LEDGER.json", "research/agents_t402/HELD_LINES_T402.csv")
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T732_FORMWORK_MOVED.json"
OUT_MD = HERE / "out" / "T732_CENSUS.md"
OUT_READ = HERE / "out" / "T732_OWN_READ.json"

# own read this run (ezdxf, ST DXF sha256 9f9d1179): S-COL.BON closed LWPOLYLINE outlines, bounding sizes in mm.
OWN_READ = {"418": (200, 700), "41B": (200, 500), "41E": (200, 500), "421": (200, 500), "778": (200, 400),
            "40F": (200, 500), "424": (250, 500)}
OWN_READ_NOTES = [
    "418 / 41E: the 0.20 band below each column (edges 39C / 399 and 3A1 / 39E, 1.20 m from the column face to the "
    "inner face of the 0.20 band 394 / 393) carries no mark or text inside it (B1 / B2 texts 78E / 78F sit in the "
    "horizontal band): the unlabelled framing pieces BM-2F-017 / BM-2F-018, depth not printed (D-04)",
]
# second section reading printed in text / schedule (T-707 own read): (b, d) m
SECOND = {"778": (D("0.20"), D("0.50")), "424": (D("0.20"), D("0.50"))}
# concrete height basis: PC-2F runs to the soffit of B7 20x75 (T-119 COL-2F-59, T-707 '2.517 (- 0.75 support)')
CTRL_SOFFIT = {"778": D("0.75")}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    bad = {p: (sha16(p), v) for p, v in pins.items() if sha16(p) != v}
    if bad or set(pins) != set(PINS):
        raise R.Refused(f"input drift (sha256[:16] now, pinned): {bad or set(pins) ^ set(PINS)}")
    return pins


def _j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _csv(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load():
    pins = check_pins()
    d = {"pins": pins, "t714": _j(T714J), "t638": _j(T638), "t707": _j(T707), "t722": _j(T722), "t724": _j(T724J),
         "t332": {r["face_id"]: r for r in _csv(T332)}, "t119": {r["id"]: r for r in _csv(T119)},
         "t110": _csv(T110)}
    d["i70"] = {x["line_id"]: x for x in _j(I70)["lines"]}
    d["i73"] = {x["line_id"]: x for x in _j(I73)["lines"]}
    return d


# ---- member states (R-T732-2) -----------------------------------------------------------------------------------------

def t714_data(d, index):
    """the T-714 member reader on a given index, plus the T-707 tank floors when the index is V3.0.73."""
    base = T714.load()
    base["index"] = index
    return base


def member_states(d):
    old = {r["line_id"]: (r["member"]["class"], r["member"]["low"], r["member"]["high"]) for r in d["t714"]["lines"]}
    data = t714_data(d, d["i73"])
    for ln in d["t707"]["lines"]:
        if ln["kind"] == "TANK":
            data["ledgers"][ln["line_id"]] = {"line_id": ln["line_id"], "bound": "AT_LEAST",
                                              "at_least_m3": ln["after"][0], "item": ln["item"], "_src": "T-707"}
    # every AT_LEAST beside figure T-722 wired must equal the ledger figure the reader uses (or be a T-707 tank floor)
    for row in d["t722"]["rows"]:
        if row["action"] == "AT_LEAST":
            led = data["ledgers"].get(row["line_id"])
            if led is not None and led.get("at_least_m3") is not None:
                if D(repr(row["beside"]["value"] if isinstance(row["beside"], dict) else row["beside"])) != D(led["at_least_m3"]):
                    raise R.Refused(f"{row['line_id']}: T-722 beside {row['beside']} != ledger {led['at_least_m3']}")
    new = {}
    rows = {r["line_id"]: r for r in data["t638"]["lines"]}
    for lid in old:
        mem, _ = T714.member_of(rows[lid], data)
        new[lid] = (mem["cls"], T714._s(mem["low"]), T714._s(mem["high"]))
    return old, new, data


# ---- face reads (R-T732-1) --------------------------------------------------------------------------------------------

def _depth_hi(member_id, d):
    rows = [r for r in d["t110"] if r["member_id"] == member_id]
    if not rows:
        raise R.Refused(f"{member_id}: not in the beam register")
    out = []
    for r in rows:
        try:
            out.append(D(r["depth_m"]))
        except Exception:
            # an unmarked member: its depth is not printed (D-04); the register's range runs to the deepest beam type
            # printed on that floor (T-110 convention); cross-checked against the register's own m3 high (2 cm)
            printed = [D(x["depth_m"]) for x in d["t110"] if x["floor"] == r["floor"] and x["mark"] not in ("", "(none)")
                       and re.fullmatch(r"\d+(\.\d+)?", x["depth_m"] or "")]
            hi = max(printed)
            implied = D(r["m3_high"]) / (D(r["width_m"]) * D(r["length_m"]))
            if abs(implied - hi) > D("0.02"):
                raise R.Refused(f"{member_id}: register m3 high implies depth {implied:.3f}, not {hi}")
            out.append(hi)
    return max(out)


def d_range(col_id, d):
    r = d["t119"][col_id]
    lo, _, hi = r["D_ctrl"].partition("..")
    dmin, dmax = D(lo), D(hi or lo)
    held = re.findall(r"held: ([^|]+)", r["framing"])
    names = re.findall(r"(BM-\w+-\d+)", held[0]) if held else []
    for m in names:
        dmax = max(dmax, _depth_hi(m, d))
    return dmin, dmax, names


def col_id_of(fw_row, d):
    for f in fw_row["faces"]:
        if f["element"] == "COLUMN":
            m = re.match(r"(COL-\w+-\d+)", d["t332"][f["face_id"]]["item"])
            return m.group(1), f
    raise R.Refused(f"{fw_row['line_id']}: no column shaft face")


def walk_d(shaft_face, col, d):
    """the D_ctrl the walk's shaft record was made at: interval - h printed in the record text (one reading only)."""
    item = d["t332"][shaft_face["face_id"]]["item"]
    hs = re.findall(r"h (\d+\.\d+)", item)
    if ".." in item.split(" h ")[-1]:
        return None
    return D(d["t119"][col]["interval"]) - D(hs[0])


def plate_tops(d):
    p = d["t707"]["plate"]
    s_lo, t_src = D(p["s_lo_b8"]), max(D(v) for v in p["t_by_panel"].values())
    return {k: s_lo - max(D(0), t_src - D(v)) for k, v in p["t_by_panel"].items()}, {k: D(v) for k, v in p["t_by_panel"].items()}


def restate_columns(d, moved):
    tops, tpan = plate_tops(d)
    t638 = {r["line_id"]: r for r in d["t638"]["lines"]}
    t707 = {ln["line_id"]: ln for ln in d["t707"]["lines"]}
    fw707 = {f["fw_line"]: f for f in d["t707"]["formwork"]}
    t714 = {r["line_id"]: r for r in d["t714"]["lines"]}
    out = []
    for lid in sorted(moved):
        row = t638[lid]
        conc = row["concrete_line"]
        ln = t707[conc]
        h = ln["handle"]
        col, sface = col_id_of(row, d)
        dmin, dmax, held = d_range(col, d)
        dw = walk_d(sface, col, d)
        b, dd = OWN_READ[h]
        secs = [(D(b) / 1000, D(dd) / 1000)] + ([SECOND[h]] if h in SECOND else [])
        areas = sorted({BR.mul(x, y) for x, y in secs})
        assert [str(a.normalize()) for a in areas] == [str(D(a).normalize()) for a in ln["areas_m2"]], (h, areas)
        top_col = D(ln["top_lo"])
        h_lo = D(ln["h_lo"])
        basis = "CTRL_SOFFIT" if h in CTRL_SOFFIT else "SLAB_TOP"
        base = top_col - h_lo - (CTRL_SOFFIT.get(h, D(0)))
        assert base == D("9.65"), (h, base)
        if basis == "CTRL_SOFFIT":
            assert dmin == dmax == CTRL_SOFFIT[h], (h, dmin, dmax)
        new_lo, new_hi = ln["after"]
        mem = {"cls": "BOUNDED" if new_hi is not None else "AT_LEAST", "low": new_lo, "high": new_hi}
        a_max = areas[-1]
        h_hi = None if new_hi is None else D(new_hi) / a_max
        faces = []
        for f in row["faces"]:
            if f["element"] == "COLUMN":
                continue
            if f["kind"] == "JOINT" and f["lo"] == "0.000000":
                faces.append({"face_id": f["face_id"], "kind": "JOINT_CAP", "hi": f["hi"]})
            elif f["kind"] == "JOINT":
                fig = f["held_from"] if f["held_from"] is not None else f["lo"]
                assert f["held_from"] is not None or f["lo"] == f["hi"], f["face_id"]
                faces.append({"face_id": f["face_id"], "kind": "JOINT", "fig": fig,
                              "recorded_at": "D_MIN" if dw is not None and dw == dmin else "UNSTATED"})
            elif f["kind"] == "SLAB_EDGE":
                faces.append({"face_id": f["face_id"], "kind": "EDGE", "fig": f["held_from"]})
            else:
                raise R.Refused(f"{f['face_id']}: face kind {f['kind']} not read")
        res = R.column_line(lid, member=mem, sections_m=secs, base=base,
                            panel_tops_lo=[tops[p] for p in ln["panels_touched"]],
                            panel_t=[tpan[p] for p in ln["panels_touched"]], h_lo_conc=h_lo, h_hi=h_hi,
                            d_min=dmin, d_max=dmax, d_settled=dmin == dmax, faces=faces, basis=basis)
        old = t714[lid]
        f7 = fw707.get(lid)
        out.append({
            "line_id": lid, "element_id": row["element_id"], "concrete_line": conc, "handle": h, "column": col,
            "member_before": list(t714[lid]["member"][k] for k in ("class", "low", "high")),
            "member_after": [mem["cls"], new_lo and format(D(new_lo), "f"), new_hi and format(D(new_hi), "f")],
            "hold": ln["item"], "panels": ln["panels_touched"], "top_lo_column": ln["top_lo"],
            "top_lo_shaft": format(res["top_lo_used"], "f"), "base": "9.65", "basis": basis,
            "d_ctrl": [format(dmin, "f"), format(dmax, "f")], "d_open_by": held, "d_walk": None if dw is None else format(dw, "f"),
            "sections_m": [[format(x, "f"), format(y, "f")] for x, y in secs],
            "perimeter_m": [format(x, "f") for x in res["p"]], "shaft_h_lo": format(res["shaft_h_lo"], "f"),
            "h_hi": None if h_hi is None else format(h_hi, "f"),
            "faces": [{"face_id": f["face_id"], "dep": f["dep"], "low": T714._s(BR.round_low(f["low"])),
                       "high": None if f["high"] is None else T714._s(BR.round_high(f["high"]))} for f in res["faces"]],
            "old": {"class": old["class_after"], "why": old["why"], "faces": [(f["face_id"], f["dep"]) for f in old["faces"]]},
            "old_shaft_record": {"face_id": sface["face_id"], "lo": sface["lo"], "hi": sface["hi"],
                                 "cause": sface["cause"][:120]},
            "t707_beside": None if f7 is None else [f7["low_m2"], f7["high_m2"]],
            "class_after": res["cls"], "low": T714._s(res["low"]),
            "high": None if res["high"] is None else T714._s(res["high"]),
            "envelope": None if res["envelope"] is None else T714._s(res["envelope"]),
        })
    return out


# ---- T-724 strip children -----------------------------------------------------------------------------------------

def strip_children(d):
    """faces of the four named children (local frames of T-724, committed): soffit = plan area (depth-free part),
    exposed outer edge = boundary not against the column / beam band / neighbouring strip lines (m2 per m depth)."""
    pieces = {p["piece"]: p for p in d["t724"]["findings"][3]["pieces"]}
    out = []
    for s in T724.STRIPS:
        a, b = s["col"]
        piece = box(a, 0.0, b, 0.2)
        # south face y = 0 on the column / beam outer face; ends x = a / b against the two strip lines: only y = 0.2
        edge = D(repr(round(b - a, 6)))
        p = pieces[f"{s['floor']}-STRIP-AT-COL"]
        assert D(p["area_m2"]) == D(repr(round(piece.area, 6))), p
        out.append({"piece": p["piece"], "soffit_m2": p["area_m2"], "edge_m_per_m_depth": format(edge, "f"),
                    "contacts": "south face on column " + s["column"].split()[0] + " / beam band; ends on " +
                                " / ".join(k[:10] for k in s["lines"]),
                    "item": p["item"]})
        sq = box(0.0, 0.0, 0.2, 0.2)
        corner = sq.intersection(Point(T724.FILLET["cx"], T724.FILLET["cy"]).buffer(T724.FILLET["r"], quad_segs=20000))
        east, south = LineString([(0.2, -1), (0.2, 1)]), LineString([(-1, 0.0), (1, 0.0)])
        bnd = corner.exterior
        exposed = bnd.length - bnd.intersection(east.buffer(1e-9)).length - bnd.intersection(south.buffer(1e-9)).length
        q = pieces[f"{s['floor']}-NW-CORNER"]
        assert D(q["area_m2"]) == BR.round_point(D(repr(corner.area))), q
        out.append({"piece": q["piece"], "soffit_m2": q["area_m2"],
                    "edge_m_per_m_depth": format(BR.round_point(D(repr(exposed))), "f"),
                    "contacts": "east face on the north strip, south face on the west strip (T-724 own read)",
                    "item": q["item"]})
    for o in out:
        o.update(cls="BLANK_NAMED", why="concrete child NAMED blank (D-05 / D-26: no section / mark / bars / MATERIAL): "
                                        "whether a formed face exists at all is open; per-unit figures beside only")
    return out


# ---- family restatement --------------------------------------------------------------------------------------------

def family(d, restated):
    t724 = {r["line_id"]: r for r in d["t724"]["findings"][1]["restated"]}
    new = {r["line_id"]: r for r in restated}
    b_lo = b_hi = a_lo = D(0)
    by = {"BOUNDED": 0, "AT_LEAST": 0, "FIX_ROW": 0, "BLANK_NAMED": 0}
    for r in d["t714"]["lines"]:
        cls, lo, hi = r["class_after"], r["low"], r["high"]
        if r["line_id"] in t724:
            lo, hi = t724[r["line_id"]]["after"].split(" .. ")
            assert cls == "BOUNDED"
        if r["line_id"] in new:
            n = new[r["line_id"]]
            cls, lo, hi = n["class_after"], n["low"], n["high"]
        by[cls] += 1
        if cls == "BOUNDED":
            b_lo, b_hi = b_lo + D(lo), b_hi + D(hi)
        elif cls == "AT_LEAST":
            a_lo += D(lo)
    s0 = d["t714"]["summary"]
    return {"by_class": by, "bounded_low_m2": format(b_lo, "f"), "bounded_high_m2": format(b_hi, "f"),
            "at_least_m2": format(a_lo, "f"),
            "t714": {"by_class": s0["by_class"], "bounded": [s0["bounded_low_m2"], s0["bounded_high_m2"]],
                     "at_least": s0["at_least_m2"]},
            "t724_restated_lines": sorted(t724)}


def build(d):
    old, new, _ = member_states(d)
    moved = {lid for lid in old if old[lid] != new[lid]}
    restated = restate_columns(d, moved)
    cen = R.census(old, new, {r["line_id"]: r for r in restated})
    return {"census": cen, "restated": restated, "children": strip_children(d), "family": family(d, restated),
            "unchanged_named": unchanged_named(d, old, new)}


def unchanged_named(d, old, new):
    """members T-722 / T-724 touched whose formwork lines do not move (named, with the reason)."""
    ids = {"L-fb7a6431fede62e93fd5": "member stays capped blank 0 .. 3.5256 (R-T724-3): no floor; faces OQ-10",
           "L-684fcad323adc0c8a267": "member AT_LEAST 1.903 already in T-714 (T-711 ledger); faces carry no figure (D-43)",
           "L-ab37afa17f2ac5b0efd1": "member AT_LEAST 0.115155 already in T-714 (T-721 ledger); soffit FLOOR_ONLY 1.7993 kept"}
    out = []
    for r in d["t714"]["lines"]:
        ml = [m["line_id"] for m in r["member"]["lines"]]
        for m in ml:
            if m in ids:
                assert old[r["line_id"]] == new[r["line_id"]], r["line_id"]
                out.append({"line_id": r["line_id"], "member": m, "class": r["class_after"], "why": ids[m]})
    return out


def render_md(doc):
    f = doc["family"]
    L = [f"# T-732 census: STR.FORMWORK lines whose concrete member moved, {CANDIDATE} vs the T-714 basis", "",
         "Research only: nothing wired, released or VERIFIED; figures beside, never summed into a released total.", "",
         "| line | column | member before -> after (m3) | shaft h lo / D | faces | T-714 | T-732 formwork m2 |",
         "|---|---|---|---|---|---|---|"]
    for r in doc["restated"]:
        fw = f"{r['low']} .. {r['high']}" if r["class_after"] == "BOUNDED" else f">= {r['low']}"
        fs = "; ".join(f"{x['face_id'][-22:]} {x['dep']} {x['low']}..{x['high']}" for x in r["faces"])
        L.append(f"| {r['line_id'][:10]} | {r['handle']} {r['column']} | {r['member_before'][1]} .. "
                 f"{r['member_before'][2]} -> {r['member_after'][1]} .. {r['member_after'][2]} | {r['shaft_h_lo']} / "
                 f"{r['d_ctrl'][0]}..{r['d_ctrl'][1]} | {fs} | {r['old']['class']} | {r['class_after']} {fw} |")
    L += ["", f"Census (R-T732-2): {len(doc['census'])} formwork lines with a moved member; "
          f"{sum(c['state'] == 'RESTATED' for c in doc['census'])} restated, "
          f"{sum(c['state'] != 'RESTATED' for c in doc['census'])} not.", "",
          "| family | T-714 | after T-724 + T-732 |", "|---|---|---|",
          f"| BOUNDED | {f['t714']['by_class'].get('BOUNDED')}: {f['t714']['bounded'][0]} .. {f['t714']['bounded'][1]} | "
          f"{f['by_class']['BOUNDED']}: {f['bounded_low_m2']} .. {f['bounded_high_m2']} |",
          f"| AT_LEAST | {f['t714']['by_class'].get('AT_LEAST')}: >= {f['t714']['at_least']} | "
          f"{f['by_class']['AT_LEAST']}: >= {f['at_least_m2']} |",
          f"| BLANK_NAMED | {f['t714']['by_class'].get('BLANK_NAMED')} | {f['by_class']['BLANK_NAMED']} |",
          f"| FIX_ROW | {f['t714']['by_class'].get('FIX_ROW')} | {f['by_class']['FIX_ROW']} |", "",
          "## T-724 strip children (NAMED blank; per-unit beside)", "", "| piece | soffit m2 | edge m2 per m depth |",
          "|---|---|---|"]
    L += [f"| {c['piece']} | {c['soffit_m2']} | {c['edge_m_per_m_depth']} |" for c in doc["children"]]
    L += ["", "## Touched members whose formwork does not move", "", "| line | member | class | why |", "|---|---|---|---|"]
    L += [f"| {u['line_id'][:10]} | {u['member'][:10]} | {u['class']} | {u['why']} |" for u in doc["unchanged_named"]]
    return "\n".join(L) + "\n"


def make_doc():
    d = load()
    b = build(d)
    return {"schema": SCHEMA, "task": "T-732", "candidate": CANDIDATE, "rules": R.RULES, "pins": d["pins"],
            "not_claimed": "development villa; nothing wired, released or VERIFIED; no freelancer formwork row "
                           "(FREELANCER_NO_ROW): no %; V2.9 + route G unchanged", **b}


def dump(doc):
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    if "--pin" in sys.argv:
        PIN_FILE.write_text(json.dumps({p: sha16(p) for p in PINS}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    doc = make_doc()
    if "--write" in sys.argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(dump(doc), encoding="utf-8")
        OUT_MD.write_text(render_md(doc), encoding="utf-8")
        OUT_READ.write_text(json.dumps({"drawing": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' sha256 9f9d1179",
                                        "outlines_mm": {k: list(v) for k, v in OWN_READ.items()},
                                        "notes": OWN_READ_NOTES}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    elif "--check" in sys.argv:
        assert OUT_JSON.read_text(encoding="utf-8") == dump(doc), "committed output differs from the rebuild"
        print("CHECK OK")
    print(render_md(doc))
