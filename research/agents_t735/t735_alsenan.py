"""T-735 development-villa build (research, unwired): the FORMWORK CONFLICT DECIDER for the 7 STR.FORMWORK lines that
T-730 carried BLANK (F-T730-1 / F-T730-2): the 6 column lines T-707 bounded by P x (h - t) and T-714 later stated BLANK
without declaring a restatement, and the beam-side line L-867e155d whose T-714 record caps it at 0 .. 0. Each gets ONE
live form on ARCH_TAKEOFF_V3.0.73 (R-T732-1 for the columns, R-T735-2 for the beam side) and the supersession of
every earlier form by name (R-T735-1).

Inputs: merged repository files, sha256-pinned in PINS.json (T-732's builder and its pins are reused read-only), plus
the own read of this run on Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179, decoded by the wrapper
into the private folder only; sizes, handles and edge directions recorded, no coordinate) held below as constants and
in out/T735_OWN_READ.json. Writes out/T735_DECIDER.json and out/T735_DECIDER.md. No candidate, released (V2.9 +
route G), rule / knowledge version or registry file is touched; nothing is wired, released or VERIFIED.

    python3 -I research/agents_t735/t735_alsenan.py [--write | --check | --pin]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, HERE.parent / "agents_t732", HERE.parent / "agents_t707"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t735_rules as R  # noqa: E402
import t732_rules as R32  # noqa: E402
import t732_alsenan as T732  # noqa: E402
import t707_alsenan as T707  # noqa: E402

D, BR = R.D, R.BR
SCHEMA = "URBAN_T735_FORMWORK_DECIDER_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
T689 = "research/agents_t689/out/T689_HELD_RANGES.json"
T707J = "research/agents_t707/out/T707_COLUMN_TAIL.json"
T714J = "research/agents_t714/out/T714_FORMWORK_BOUNDS.json"
T732J = "research/agents_t732/out/T732_FORMWORK_MOVED.json"
T730R = "research/agents_t730/out/T730_ROWS.csv"
WALK = "research/agents_t293/T293P2_WALK_RECORDS.json"
PANELS = "research/agents_t139/PANELS.csv"
T110 = "research/agents_t110/BEAM_MEMBER_REGISTER.csv"
I73 = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
PINS = (T689, T707J, T714J, T732J, T730R, WALK, PANELS, T110, I73, "research/agents_t732/PINS.json")
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T735_DECIDER.json"
OUT_MD = HERE / "out" / "T735_DECIDER.md"
OUT_READ = HERE / "out" / "T735_OWN_READ.json"

# ---- own read this run (ezdxf, ST DXF sha256 9f9d1179) -----------------------------------------------------------------
# S-COL.BON closed LWPOLYLINE outlines by handle, bounding sizes in mm (orientation as drawn)
OWN_READ = {"412": (200, 500), "415": (600, 200), "34A": (200, 400), "34D": (400, 200), "356": (400, 200),
            "350": (400, 200)}
# 1F roof slab face 1F-072 (the CB10 band, drawn 0.30 wide, 6.85 m long, by the T-139 face polygoniser on the same
# file): its edges against SLAB panels are all on ONE long side (constant x), along the band; the panels are
# 1F-041 / 1F-060 / 1F-090 / 1F-094 (0.785 + 1.046 + 1.046 + 1.142 = 4.019 m; the walk's three runs book
# 1.885119 + 1.828259 + 0.300056 = 4.013434 m beside slab: the 0.006 m is the 0.02 m line extension at the corners)
OWN_EDGES_1F072 = {"slab_edges_m": {"1F-041": "0.785", "1F-060": "1.046", "1F-090": "1.046", "1F-094": "1.142"},
                   "all_along_member": True, "across_edges_beside_slab_m": "0",
                   "other_side": "outer west strip 1F-059 / 1F-079 / 1F-093 (EDGE_HELD, BM-1F-034 HELD)",
                   "dome_side": "1F-073 west dome opening + ring (RING_MIX): held length, not in this line"}

# handle -> (concrete line, section readings (b, d) m). The drawn outline (own read) and the schedule band (T-566 /
# T-689, merged); the trio 34A / 34D / 356 is identical so the line-to-outline pairing (not asserted) changes nothing.
COLS = {
    "L-6f83fc39933954d0e3e6": ("412", "L-919a5749ef79759e01ca", [("0.20", "0.50")]),
    "L-b35c1688058336adc729": ("415", "L-bc01297b1c4a4c45a15f", [("0.20", "0.50"), ("0.20", "0.60")]),
    "L-6cba8c04e5f32a060b06": ("34A", "L-9f5a647014bbf83359f9", [("0.20", "0.40"), ("0.20", "0.50")]),
    "L-ddec0b3f3436cdbdbf8b": ("34D", "L-c0b3340a906c2c7650f8", [("0.20", "0.40"), ("0.20", "0.50")]),
    "L-f9836bd6176bc3f9cc84": ("356", "L-e6c1c9a7feec10f64975", [("0.20", "0.40"), ("0.20", "0.50")]),
    "L-7fe93376cb482ad01860": ("350", "L-694a75c84dd6e4bb4491", [("0.20", "0.40"), ("0.25", "0.50")]),
}
BEAM_LINE = "L-867e155d6f8f0a452eba"
# GF annex datum (R-T678-2, merged, Checker-verified): one plane; slab top >= +3.544 (W08 head +2.80 drawn under CB6
# 20x75, tol 0.006), <= +4.30 (finished roof mark); base +0.25 APPROVED; GFRS annex prints no thickness: note 18 0.16.
ANNEX = {"base": D("0.25"), "top_lo": D("3.544"), "top_hi": D("4.30"), "t": D("0.16")}


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


def load():
    pins = check_pins()
    d = T732.load()                                   # T-732's own pinned inputs (T-638, T-332, T-119, T-110, ...)
    d.update(pins735=pins, t689=_j(T689), t732=_j(T732J), walk=_j(WALK)["records"])
    with open(ROOT / PANELS, encoding="utf-8", newline="") as fh:
        d["panels"] = {r["id"]: r for r in csv.DictReader(fh)}
    with open(ROOT / T730R, encoding="utf-8", newline="") as fh:
        d["t730"] = list(csv.reader(fh))
    return d


# ---- the 6 columns (R-T732-1) -------------------------------------------------------------------------------------------

def column(lid, d):
    h, conc, secs = COLS[lid]
    t638 = {r["line_id"]: r for r in d["t638"]["lines"]}[lid]
    assert t638["concrete_line"] == conc, lid
    m = d["i73"][conc]
    assert m["item_code"] == "STR.CONC.COLUMN" and m["class"] == "HELD" and m["held_low"] is not None, conc
    mem = {"cls": "BOUNDED", "low": repr(m["held_low"]), "high": repr(m["held_high"])}
    # own read = one of the readings; T-689 areas = the concrete line's readings
    b, dd = sorted(OWN_READ[h])
    assert (D(b) / 1000, D(dd) / 1000) in {(D(x), D(y)) for x, y in secs}, (h, OWN_READ[h])
    t689 = {r["line_id"]: r for r in d["t689"]["blank_to_bounded"]["lines"]}
    six = {x["line"]: x for x in T707.T693_SIX}[conc]
    a_sorted = sorted({BR.mul(x, y) for x, y in secs})
    if conc in t689:
        assert [D(a) for a in t689[conc]["areas_m2"]] == a_sorted, (conc, a_sorted)
    per = sorted({BR.mul(2, D(x) + D(y)) for x, y in secs})
    assert [D(p) for p in six["perim"]] == [per[0], per[-1]], (conc, per)
    h_lo, h_hi = D(six["h"][0]), D(six["h"][1])
    col, sface = T732.col_id_of(t638, d)
    dmin, dmax, held = T732.d_range(col, d)
    if h in ("412", "415"):
        tops, tpan = T732.plate_tops(d)
        panels = six["panels"]
        base = T707.BASE_2F
        ptops, pt = [tops[p] for p in panels], [tpan[p] for p in panels]
        # the column top follows the highest member (B8 joint, R-T689-1 / R-T707-1): concrete h_lo = 12.937 - 9.65
        assert h_lo == D(d["t707"]["plate"]["s_lo_b8"]) - base, (h, h_lo)
    else:
        panels = ["ANNEX (one plane, R-T678-2)"]
        base = ANNEX["base"]
        ptops, pt = [ANNEX["top_lo"]], [ANNEX["t"]]
        assert h_lo == ANNEX["top_lo"] - base and h_hi == ANNEX["top_hi"] - base, (h, h_lo, h_hi)
    faces = []
    for f in t638["faces"]:
        if f["element"] == "COLUMN":
            continue
        if f["kind"] == "JOINT" and f["lo"] == "0.000000":
            faces.append({"face_id": f["face_id"], "kind": "JOINT_CAP", "hi": f["hi"]})
        elif f["kind"] == "JOINT":
            fig = f["held_from"] if f["held_from"] is not None else f["lo"]
            assert f["held_from"] is not None or f["lo"] == f["hi"], f["face_id"]
            dw = T732.walk_d(sface, col, d)
            faces.append({"face_id": f["face_id"], "kind": "JOINT", "fig": fig,
                          "recorded_at": "D_MIN" if dw is not None and dw == dmin else "UNSTATED"})
        elif f["kind"] == "SLAB_EDGE":
            faces.append({"face_id": f["face_id"], "kind": "EDGE", "fig": f["held_from"]})
        else:
            raise R.Refused(f"{f['face_id']}: face kind {f['kind']} not read")
    res = R32.column_line(lid, member=mem, sections_m=secs, base=base, panel_tops_lo=ptops, panel_t=pt,
                          h_lo_conc=h_lo, h_hi=h_hi, d_min=dmin, d_max=dmax, d_settled=dmin == dmax, faces=faces)
    # the envelope of the perimeter faces (shaft + joints) beside, as information: never a line high (edge band outside)
    env = BR.round_high(BR.mul(per[-1], h_hi - min(pt)))
    live = {"cls": res["cls"], "low": format(res["low"], "f"),
            "high": None if res["high"] is None else format(res["high"], "f")}
    f707 = {f["fw_line"]: f for f in d["t707"]["formwork"]}[lid]
    r714 = {r["line_id"]: r for r in d["t714"]["lines"]}[lid]
    form707 = {"cls": "BOUNDED", "low": f707["low_m2"], "high": f707["high_m2"]}
    # T-707 high = P_max x (h_hi - t) = the perimeter envelope exactly (asserted)
    assert D(f707["high_m2"]) == BR.mul(per[-1], h_hi - D(f707["t_m"][0])), lid
    earlier = [
        {"piece": "T-707", "form": form707, "cause": "UPPER_BOUND_METHOD_NOT_A_FLOOR",
         "note": f"low {f707['low_m2']} = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, "
                 f"F-T732-1); high {f707['high_m2']} = P_max x (h_hi - t) = the perimeter envelope "
                 f"(ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)"},
        {"piece": "T-714", "form": {"cls": r714["class_after"], "low": None, "high": None,
                                    "cap": r714["cap_beside"]},
         "cause": "BLANK_WITH_POSITIVE_FLOOR",
         "note": f"T-714 '{r714['why']}': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the "
                 f"shaft at P_min x (least panel top - base - D_max) = {format(R32.BR.round_low(res['faces'][0]['low']), 'f')} "
                 f"for every reading"},
    ]
    dec = R.decide(lid, live, earlier)
    return {
        "line_id": lid, "element_id": t638["element_id"], "handle": h, "column": col, "concrete_line": conc,
        "member": [mem["cls"], mem["low"], mem["high"]], "sections_m": [list(s) for s in secs],
        "single_section": res["single_section"], "perimeter_m": [format(per[0], "f"), format(per[-1], "f")],
        "base": format(base, "f"), "panels": panels, "top_lo_shaft": format(res["top_lo_used"], "f"),
        "h_conc": [format(h_lo, "f"), format(h_hi, "f")], "d_ctrl": [format(dmin, "f"), format(dmax, "f")],
        "d_open_by": held, "shaft_h_lo": format(res["shaft_h_lo"], "f"),
        "faces": [{"face_id": f["face_id"], "dep": f["dep"], "low": format(BR.round_low(f["low"]), "f"),
                   "high": None if f["high"] is None else format(BR.round_high(f["high"]), "f")} for f in res["faces"]],
        "live": live, "perimeter_envelope_beside": format(env, "f"), "superseded": dec["superseded"],
    }


# ---- the beam side L-867e155d (R-T735-2) ---------------------------------------------------------------------------------

def beam_side(d):
    t638 = {r["line_id"]: r for r in d["t638"]["lines"]}[BEAM_LINE]
    face = t638["faces"][0]
    assert face["face_id"] == "R4-282.1F-072~REST.BEAM_SIDE" and face["lo"] == face["hi"] == "0.000000"
    recs = [r for r in d["walk"] if r["floor"] == "1F" and r["face"] == "1F-072" and r.get("run") == "REST"]
    by = {r["category"]: r["m2"] for r in recs}
    assert by["BEAM_SIDE"] == 0.0 and by["BEAM_SIDE_HELD_LEN"] > 0, by     # the walk held the depth
    walk_slab = sum(r["m2"] for r in d["walk"] if r["floor"] == "1F" and r["face"] == "1F-072"
                    and r["category"] == "BEAM_SIDE_HELD_LEN")
    own = sum(D(v) for v in OWN_EDGES_1F072["slab_edges_m"].values())
    assert abs(own - D(repr(walk_slab))) < D("0.01"), (own, walk_slab)    # the held lengths are the slab edges read
    ts = {d["panels"][p]["t"] for p in OWN_EDGES_1F072["slab_edges_m"]}
    assert ts == {"0.16"}, ts
    reg = [r for r in d["t110"] if r["member_id"] == "BM-1F-031"]
    cands = []
    for r in reg:
        lo, hi = r["m3_low"], r["m3_high"]
        cands += [("0.25", "0.50", r["length_m"], lo), (r["width_m"], "0.50", r["length_m"], hi)]
    # schedule CB10 25x50 (TOTAL depth from the slab top, OQ-11 settled by ST p.14); drawn width 0.30 (D-02)
    assert all("CB10 25x50" in r["schedule"] for r in reg) and {r["width_m"] for r in reg} == {"0.3"}
    res = R.held_depth_side(held_len=repr(by["BEAM_SIDE_HELD_LEN"]),
                            edges_along=[OWN_EDGES_1F072["all_along_member"]], candidates=cands, t=ts.pop(),
                            cap_contacts=[f"{k} {round(v, 6)} m" for k, v in sorted(by.items())
                                          if k.startswith("BEAM_SIDE_HELD_LEN:") or k == "JUNCTION_HELD_LEN"])
    live = {"cls": res["cls"], "low": format(res["low"], "f"), "high": format(res["high"], "f")}
    r714 = {r["line_id"]: r for r in d["t714"]["lines"]}[BEAM_LINE]
    earlier = [{"piece": "T-714", "form": {"cls": r714["class_after"], "low": None, "high": None,
                                           "cap": r714["cap_beside"]},
                "cause": "CAP_ZERO_FROM_HELD_DEPTH",
                "note": "the 0 .. 0 face is the walk's held-depth convention (D None -> 0 m2 + held length "
                        f"{round(by['BEAM_SIDE_HELD_LEN'], 6)} m), not a measured zero; no ZERO_BY_GEOMETRY: the "
                        "band is 0.50 deep under a 0.16 slab along that length"}]
    dec = R.decide(BEAM_LINE, live, earlier)
    return {"line_id": BEAM_LINE, "element_id": t638["element_id"], "member": "BM-1F-031 (CB10 span 1 / 2, width "
            "0.25 schedule vs 0.30 drawn, D-02)", "member_lines": t638["member_lines"],
            "held_len_beside_slab_m": format(D(repr(by["BEAM_SIDE_HELD_LEN"])), "f"), "d": format(res["d"], "f"),
            "t": format(res["t"], "f"), "exact_m2": format(res["exact"], "f"), "dep": res["dep"],
            "candidates": [list(c) for c in cands], "not_in_this_line": res["named_beside"],
            "live": live, "superseded": dec["superseded"]}


# ---- family and the T-730 conflict rows --------------------------------------------------------------------------------

def family(d, lines):
    rest = [{"line_id": r["line_id"], "class_after": r["class_after"], "low": r["low"], "high": r["high"]}
            for r in d["t732"]["restated"]]
    rest += [{"line_id": r["line_id"], "class_after": r["live"]["cls"], "low": r["live"]["low"],
              "high": r["live"]["high"]} for r in lines]
    assert len({r["line_id"] for r in rest}) == len(rest), "a line decided twice (T-732 / T-735 overlap)"
    f = T732.family(d, rest)
    f0 = d["t732"]["family"]
    f["t732"] = {"by_class": f0["by_class"], "bounded": [f0["bounded_low_m2"], f0["bounded_high_m2"]],
                 "at_least": f0["at_least_m2"]}
    return f


def t730_rows(d, ids):
    out = []
    for row in d["t730"][1:]:
        for lid in ids:
            if row[5] == lid:
                out.append({"source": row[0], "line_id": lid, "state": row[7], "value": row[8]})
    return out


def build(d):
    cols = [column(lid, d) for lid in sorted(COLS)]
    beam = beam_side(d)
    return {"columns": cols, "beam_side": beam, "family": family(d, cols + [beam]),
            "t730_rows": t730_rows(d, set(COLS) | {BEAM_LINE})}


def render_md(doc):
    L = [f"# T-735 formwork conflict decider: 7 lines, one live form each, on {CANDIDATE}", "",
         "Research only: nothing wired, released or VERIFIED; figures beside, never summed into a released total.", "",
         "| line | column | member m3 | sections | shaft h lo / D | T-707 | T-714 | **T-735 live (m2)** |",
         "|---|---|---|---|---|---|---|---|"]
    for r in doc["columns"]:
        s7 = r["superseded"][0]["form"]
        lv = r["live"]
        fw = f"{lv['low']} .. {lv['high']}" if lv["cls"] == "BOUNDED" else f">= {lv['low']}"
        L.append(f"| {r['line_id'][:10]} | {r['handle']} {r['column']} | {r['member'][1]} .. {r['member'][2]} | "
                 f"{' / '.join('x'.join(s) for s in r['sections_m'])} | {r['shaft_h_lo']} / "
                 f"{r['d_ctrl'][0]}..{r['d_ctrl'][1]} | {s7['low']} .. {s7['high']} | BLANK | **{lv['cls']} {fw}** |")
    b = doc["beam_side"]
    L.append(f"| {b['line_id'][:10]} | BM-1F-031 REST side | beam held (width) | D {b['d']} t {b['t']} | "
             f"L {b['held_len_beside_slab_m']} | - | BLANK cap 0 | **{b['live']['cls']} {b['live']['low']}** |")
    f = doc["family"]
    L += ["", "| family B10-13 | after T-732 | after T-735 |", "|---|---|---|",
          f"| BOUNDED | {f['t732']['by_class']['BOUNDED']}: {f['t732']['bounded'][0]} .. {f['t732']['bounded'][1]} | "
          f"{f['by_class']['BOUNDED']}: {f['bounded_low_m2']} .. {f['bounded_high_m2']} |",
          f"| AT_LEAST | {f['t732']['by_class']['AT_LEAST']}: >= {f['t732']['at_least']} | "
          f"{f['by_class']['AT_LEAST']}: >= {f['at_least_m2']} |",
          f"| BLANK_NAMED | {f['t732']['by_class']['BLANK_NAMED']} | {f['by_class']['BLANK_NAMED']} |",
          f"| FIX_ROW | {f['t732']['by_class']['FIX_ROW']} | {f['by_class']['FIX_ROW']} |", "",
          "## Supersession (R-T735-1)", ""]
    for r in doc["columns"] + [b]:
        for e in r["superseded"]:
            L.append(f"- {r['line_id'][:10]} {e['piece']}: {e['cause']}: {e['note']}")
    return "\n".join(L) + "\n"


def make_doc():
    d = load()
    b = build(d)
    return {"schema": SCHEMA, "task": "T-735", "candidate": CANDIDATE, "rules": {**R.RULES, **R32.RULES},
            "pins": d["pins735"],
            "not_claimed": "development villa; nothing wired, released or VERIFIED; no freelancer formwork row "
                           "(FREELANCER_NO_ROW): no %; V2.9 + route G unchanged", **b}


def dump(doc):
    return json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"


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
                                        "face_1F_072": OWN_EDGES_1F072}, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8")
    elif "--check" in sys.argv:
        assert OUT_JSON.read_text(encoding="utf-8") == dump(doc), "committed output differs from the rebuild"
        print("CHECK OK")
    print(render_md(doc))
