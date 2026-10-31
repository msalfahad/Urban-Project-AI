"""T-407 development-villa run: masonry below the house exterior ground beams, run by run (values only).

Usage (from the engine root):
    python3 -I research/agents_t407/t407_alsenan.py            # check the committed summary
    python3 -I research/agents_t407/t407_alsenan.py --write    # rebuild it
    python3 -I research/agents_t407/t407_alsenan.py --v3033 <private>/.../V3_0_33_BOQ_LINES.json [--write]
                                                               # also bind the runs to the candidate's lines

Inputs: ALSENAN_T407_INPUT.json (t407_extract.py, from the structural DXF by handle), the merged T-289 basis ledger
(exterior run ids and line ids), the merged T-403 summary (fence masonry, for the one-layer check). The printed facts
below are typed WITH their sheet; each is a figure printed on the sheet named (no derived or default value).
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t407_rules as R  # noqa: E402

OUT = os.path.join(HERE, "summary_t407.json")
INP = os.path.join(HERE, "ALSENAN_T407_INPUT.json")
LEDGER_289 = os.path.join(ROOT, "research/agents_t289/BASIS_LEDGER_T289.csv")
SUMMARY_403 = os.path.join(ROOT, "research/agents_t403/summary_t403.json")


def S(v, src):
    return {"value": v, "source": src}


# printed facts (sheet named; ST = structural set, Drive 'Alsenan chalet project')
FORMATION_MIN = S(1.50, "ST p.9 note 1: excavation not less than 1.5 m below the existing plot level (Q-21 C: a minimum)")
BAND_BLINDING_MAX = S(0.10, "ST p.14 A-A: 10 cm blinding drawn under the pad; under the lower G.B between pads not drawn (0 .. 0.10)")
BAND_DEPTH_MAX = S(0.60, "ST p.10 'B.W 20 x 60' vs p.14 plan '(20x40)': two printed readings, 0.40 | 0.60 (T-403)")
FOOTING_BUILDUP = S(0.15, "ST p.13 TYP. DETAIL OF ISOLATED FOOTING: 10 cm plain con. + membrane + 5 cm screed")
FOOTING_T = {"F": 0.30, "F8": 0.50, "F10": 0.50, "F11": 0.50, "F14": 0.50, "F15": 0.40, "FN": 0.30}  # ST p.9 schedule H
UNDER_BEAM_MAX = S(0.10, "ST p.13 'Ground Beams for exterior walls': 10 cm blinding drawn under the beam (kept or not over block: 0 .. 0.10)")
SOFFIT_MAIN = {"N.G.": S(0.00, "ST p.13 exterior section underside 'Outer Normal ground level' = +-0.00 (T-253 s.2, Checker-verified)")}
SOFFIT_ANNEX = {"L (levels, D 0.25)": S(0.00, "annex top +0.25 (T-214) to 'Outer Normal ground level' +-0.00 (T-253 s.3)"),
                "S (section, D unprinted)": None}  # D-35 CONFLICT, RFI-S09

# run meta: which printed facts govern each house band run
RUN_META = {
    "MAIN_S": {"owner": "MAIN", "side": "S (neighbour)", "masonry_note": True, "soffit": SOFFIT_MAIN,
               "note": "ST p.1 note 2: neighbour-side exterior ground beams cast with black block above and below, built from the foundation level"},
    "ANNEX_S": {"owner": "ANNEX", "side": "S (neighbour)", "masonry_note": True, "soffit": SOFFIT_ANNEX,
                "note": "ST p.1 note 2 (as MAIN_S); annex beam depth D-35 CONFLICT"},
    "MAIN_E_SEA": {"owner": "MAIN", "side": "E (sea)", "masonry_note": False, "soffit": SOFFIT_MAIN,
                   "note": "lower band drawn (S-BOUN 1658/1659); nothing printed between it and the beam; p.1 note 2 names the neighbour side only"},
    "ANNEX_W_STREET": {"owner": "ANNEX", "side": "W (street)", "masonry_note": False, "soffit": SOFFIT_ANNEX,
                       "note": "as MAIN_E_SEA; annex beam depth D-35 CONFLICT"},
}


def _ftg_type(key):
    t = key.split(":")[0]
    return [x for x in t.split("/") if x]


def members_for(run):
    ms = [{"kind": "BAND", "blinding_max": BAND_BLINDING_MAX, "depth_max": BAND_DEPTH_MAX}]
    for key, _ in run["footing_crossings_m"]:
        for t in _ftg_type(key):
            ms.append({"kind": "FOOTING", "buildup": FOOTING_BUILDUP,
                       "t": S(FOOTING_T[t], f"ST p.9 Schedule of Footings: {t} H")})
    return ms


def exterior_runs_inside_plot(plot_line_faces):
    """Every exterior / court ground-beam run of the T-289 ledger; those whose face pair has no plot-line face are
    inside the plot (no band below)."""
    out = []
    for r in csv.DictReader(open(LEDGER_289, encoding="utf-8")):
        ev = r["evidence"]
        if not any(k in ev for k in ("EXTERIOR_MAIN", "EXTERIOR_ANNEX", "COURT")):
            continue
        for chunk in ev.split(";"):
            chunk = chunk.strip()
            if chunk.startswith("runs "):
                chunk = chunk[5:]
            parts = chunk.split()
            if len(parts) < 2 or parts[1] not in ("EXTERIOR_MAIN", "EXTERIOR_ANNEX", "COURT"):
                continue
            rid, kind = parts[0], parts[1]
            ff = float(parts[3]) if parts[2] == "ff" else None
            faces = set(rid.replace("ARC:", "").split("#")[0].split("+"))
            on = sorted(faces & set(plot_line_faces))
            out.append({"run": rid, "kind": kind, "line_id": r["line_id"], "ff_m": ff, "line_status_v3015": r["status"],
                        "plot_line_face": on[0] if on else None})
    return sorted(out, key=lambda x: (x["plot_line_face"] is None, x["run"]))


def build(v3033=None):
    inp = json.load(open(INP, encoding="utf-8"))
    runs = inp["runs"]
    table = []
    for name in ("MAIN_S", "ANNEX_S", "MAIN_E_SEA", "ANNEX_W_STREET"):
        r, m = runs[name], RUN_META[name]
        cls = R.classify({"masonry_note": m["masonry_note"], "band_below": True, "exterior_section_on_ground": True})
        h = R.height_bound(m["soffit"], UNDER_BEAM_MAX, FORMATION_MIN, members_for(r))
        tk = R.run_takeoff({"id": name, "axis_m": r["band_axis_m"], "class": cls,
                            "columns_m": [(c[0], c[1]) for c in r["column_pieces_m"]]}, h)
        tk.update(owner=m["owner"], side=m["side"], evidence=m["note"], h=h,
                  footing_crossings_m=r["footing_crossings_m"], columns=r["column_pieces_m"],
                  house_gb_faces=r["house_gb_faces_on_plot_line_m"])
        table.append(tk)
    R.check_held(table)
    ext = exterior_runs_inside_plot(inp["guards"]["plot_line_house_faces"])
    # bind each band run to the ground-beam runs over it (by the plot-line face)
    face_of = {"MAIN_S": "FC", "ANNEX_S": "F8", "MAIN_E_SEA": "FD", "ANNEX_W_STREET": "136"}
    for t in table:
        t["gb_runs_over"] = [{"run": e["run"], "line_id": e["line_id"], "ff_m": e["ff_m"]} for e in ext
                             if e["plot_line_face"] == face_of[t["id"]]]
        t["gb_ff_sum_m"] = round(sum(e["ff_m"] for e in t["gb_runs_over"]), 4)
    inside = [dict(e, masonry=R.NA if e["kind"] != "COURT" else R.UNKNOWN,
                   reason=("ST p.13 exterior section: soffit on 10 cm blinding at the outer normal ground; no band "
                           "drawn below (foundation plan S-BOUN only on the plot line)") if e["kind"] != "COURT" else
                   "court run: no section printed (T-253 s.4) and no band below; nothing printed to build on; HELD with its section")
              for e in ext if e["plot_line_face"] is None]
    # one-layer check against the T-403 fence runs (chainage along the band axis is not committed; the input
    # proves it geometrically: the house axis inside the fence band is 0.000 mm and house + fence + pool = band)
    s403 = json.load(open(SUMMARY_403, encoding="utf-8"))
    fence_axis = s403["fence_band"]["axis_m"]
    pool_axis = s403["lower_band_split_L6290a9f3"]["by_class"]["POOL_BACK"]["axis_m"]
    house_axis = round(sum(t["axis_m"] for t in table), 4)
    conservation = round(house_axis + fence_axis + pool_axis - inp["guards"]["band_axis_total_m"], 4)
    if abs(conservation) > 1e-3 or inp["guards"]["house_axis_mm_inside_fence_band"] > 0.5:
        raise SystemExit("house / fence / pool runs do not partition the band")
    house_403 = sum(v["axis_m"] for k, v in s403["lower_band_split_L6290a9f3"]["by_class"].items() if k.startswith("HOUSE"))
    tot = {
        "printed_runs_axis_m": round(sum(t["axis_m"] for t in table if t["class"] == R.PRINTED), 4),
        "printed_runs_net_axis_m": round(sum(t["net_axis_m"] for t in table if t["class"] == R.PRINTED), 4),
        "at_least_net_m2_bounded_runs": round(sum(t["net_at_least_m2"] or 0.0 for t in table if t["net_at_least_m2"] is not None), 4),
        "at_least_gross_m2_bounded_runs": round(sum(t["gross_at_least_m2"] or 0.0 for t in table if t["gross_at_least_m2"] is not None), 4),
        "unbounded_printed_runs": [t["id"] for t in table if t["status"] == "MISSING_HELD_UNBOUNDED"],
        "existence_unknown_runs": [t["id"] for t in table if t["status"] == "HELD_EXISTENCE_UNKNOWN"],
    }
    out = {
        "schema": "URBAN_T407_SUMMARY_V1",
        "input_sha_note": "ALSENAN_T407_INPUT.json from ST7757 dxf.dxf 9f9d1179",
        "runs": table,
        "exterior_runs_inside_plot": inside,
        "totals": tot,
        "one_layer": {"house_axis_m": house_axis, "fence_axis_m_T403": fence_axis, "pool_axis_m_T403": pool_axis,
                      "band_axis_total_m": inp["guards"]["band_axis_total_m"], "partition_residual_m": conservation,
                      "house_axis_equals_T403_house_split_m": round(house_axis - house_403, 4),
                      "house_axis_mm_inside_fence_band": inp["guards"]["house_axis_mm_inside_fence_band"]},
        "freelancer": {"below_ground_block_rows": 0,
                       "note": "blockwork workbook: GF exterior rows at 4.0 / 3.5 m (above the slab), 'السور' 37.2 x 2 above N.G.; no row below N.G. or under the ground beams (quantities only)"},
    }
    if v3033:
        out["v3033_binding"] = bind_v3033(v3033, table, inside)
    else:
        prev = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
        if "v3033_binding" in prev:
            out["v3033_binding"] = prev["v3033_binding"]
    return out


def bind_v3033(path, table, inside):
    import hashlib
    raw = open(path, "rb").read()
    data = json.loads(raw)
    lines = data["lines"] if isinstance(data, dict) and "lines" in data else data
    by_id = {ln.get("line_id"): ln for ln in lines}
    ids = sorted({g["line_id"] for t in table for g in t["gb_runs_over"]} | {e["line_id"] for e in inside})
    gb = {}
    for i in ids:
        ln = by_id.get(i)
        gb[i] = None if ln is None else {"item_code": ln.get("item_code"), "state": ln.get("evidence_state"),
                                          "measured_net": ln.get("measured_net")}
    # masonry lines that could already carry block below N.G. / under the ground beams
    cand = []
    for ln in lines:
        code = str(ln.get("item_code", ""))
        txt = json.dumps(ln, ensure_ascii=False).upper()
        if code.startswith(("MAS", "ARCH.BLOCK", "MASONRY")) or "BLOCK" in code:
            if any(k in txt for k in ("BELOW N.G", "BELOW NG", "BELOW GROUND", "UNDER THE GROUND BEAM", "FOUNDATION",
                                      "SUBSTRUCTURE", "BOUNDARY")):
                cand.append({"line_id": ln.get("line_id"), "item_code": code, "state": ln.get("evidence_state")})
    return {"file_sha256_prefix": hashlib.sha256(raw).hexdigest()[:8], "lines_total": len(lines),
            "ground_beam_lines": gb, "masonry_lines_below_ng_or_boundary": cand,
            "masonry_below_house_gb": "MISSING" if not cand else "SEE_CANDIDATES"}


if __name__ == "__main__":
    v = None
    if "--v3033" in sys.argv:
        v = sys.argv[sys.argv.index("--v3033") + 1]
    data = build(v)
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(text)
        print(OUT)
    else:
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print(json.dumps(data["totals"], indent=1))
        print("committed summary reproduced:", same)
        sys.exit(0 if same else 1)
