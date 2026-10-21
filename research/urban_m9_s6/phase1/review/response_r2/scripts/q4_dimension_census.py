"""Q4 (read-only, scratch): census of the DIMENSION entities of a plan DXF, and a cross-check of door / window /
passage widths and wall thicknesses against them.

Census per dimension: type, layer, sheet / plan region, text override, associativity, duplicate, stored vs recomputed
measurement. Usable for the cross-check = linear or aligned, inside a floor-plan region, no text override (or an
override equal to the measurement), not a duplicate, stored measurement equal to the defpoints.
Cross-check:
  OPENING  a usable dimension parallel to the opening's wall, whose two extension origins project onto the opening's
           two jambs (+- 15 mm along) and lie near the wall (within 400 mm of its faces): compare value vs width
  WALL     a usable dimension across a wall band (parallel to the band normal) whose origins sit on the two faces
           (+- 5 mm) inside the band's extent: compare value vs thickness
usage: python3 -I q4_dimension_census.py SRC PLAN ARCH_PLAN_JSON OPENINGS_PROBE_JSON OUT_JSON"""
import json, math, sys
from collections import Counter, defaultdict
SRC, PLAN, PJ, OPJ, OUT = sys.argv[1:6]
sys.path.insert(0, SRC)
import ezdxf
from engine.source import arch_plan as AP
from tools import urban_intake as UI

doc = ezdxf.readfile(PLAN)
unit_m = UI.INSUNITS_M.get(int(doc.header.get("$INSUNITS", 0) or 0), 0.001)
mm = unit_m * 1000
P = json.load(open(PJ))
regions = [(r["floor"], r["box"]) for r in P["regions"]]
others = [(o.get("sheet_id"), o.get("box"), o.get("titles_seen") or o.get("titles")) for o in (P.get("other_frames") or [])]
TYPES = {0: "LINEAR", 1: "ALIGNED", 2: "ANGULAR", 3: "DIAMETER", 4: "RADIUS", 5: "ANGULAR_3P", 6: "ORDINATE"}
assoc = any(o.dxftype() == "DIMASSOC" for o in doc.objects)


def where(p):
    for fl, b in regions:
        if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]:
            return "PLAN:" + fl
    for sid, b, t in others:
        if b and b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]:
            return f"OTHER_SHEET:{sid}"
    return "OUTSIDE_FRAMES"


dims = []
for d in doc.modelspace().query("DIMENSION ARC_DIMENSION"):
    t = TYPES.get(d.dimtype, str(d.dimtype)) if d.dxftype() == "DIMENSION" else "ARC"
    p2 = tuple(d.dxf.get("defpoint2", (0, 0, 0)))[:2]; p3 = tuple(d.dxf.get("defpoint3", (0, 0, 0)))[:2]
    stored = d.dxf.get("actual_measurement", None)
    try:                                         # the dimension linear factor: the displayed value = geometry x DIMLFAC
        lfac = float(d.override().get("dimlfac", 1.0) or 1.0) if d.dxftype() == "DIMENSION" else 1.0
    except Exception:                            # noqa: BLE001
        lfac = 1.0
    txt = d.dxf.get("text", None)
    rec = {"handle": d.dxf.handle, "type": t, "layer": d.dxf.layer, "p2": p2, "p3": p3, "dimlfac": lfac,
           "displayed_value": stored, "stored_mm": None if stored is None else stored / lfac * mm,
           "text_override": txt not in (None, "", "<>"), "where": where(((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2))}
    if t in ("LINEAR", "ALIGNED"):
        if t == "LINEAR":
            a = math.radians(d.dxf.get("angle", 0.0)); u = (math.cos(a), math.sin(a))
        else:
            L = math.dist(p2, p3) or 1.0; u = ((p3[0] - p2[0]) / L, (p3[1] - p2[1]) / L)
        rec["dir"] = u
        rec["recomputed_mm"] = abs((p3[0] - p2[0]) * u[0] + (p3[1] - p2[1]) * u[1]) * mm
    dims.append(rec)
seen = Counter((d["type"], round(min(d["p2"], d["p3"])[0], 1), round(min(d["p2"], d["p3"])[1], 1),
                round(max(d["p2"], d["p3"])[0], 1), round(max(d["p2"], d["p3"])[1], 1)) for d in dims)
for d in dims:
    k = (d["type"], round(min(d["p2"], d["p3"])[0], 1), round(min(d["p2"], d["p3"])[1], 1), round(max(d["p2"], d["p3"])[0], 1),
         round(max(d["p2"], d["p3"])[1], 1))
    d["duplicate"] = seen[k] > 1
    d["stored_matches_defpoints"] = (d.get("recomputed_mm") is not None and d["stored_mm"] is not None and
                                     abs(d["stored_mm"] - d["recomputed_mm"]) <= 0.5)
    reasons = []
    if d["type"] not in ("LINEAR", "ALIGNED"): reasons.append("NOT_LINEAR")
    if not d["where"].startswith("PLAN:"): reasons.append("NOT_ON_A_FLOOR_PLAN")
    if d["text_override"]: reasons.append("TEXT_OVERRIDE")
    if d["duplicate"]: reasons.append("DUPLICATE")
    if d["type"] in ("LINEAR", "ALIGNED") and not d["stored_matches_defpoints"]: reasons.append("STORED_VALUE_DISAGREES_WITH_DEFPOINTS")
    d["excluded_because"] = reasons
    d["usable"] = not reasons
# openings from the V2 probe (lintel_measure.openings, one call per floor in region order)
OP = json.load(open(OPJ))["lm_openings"]
floors = [fl for fl, _ in regions]
openings = [dict(o, floor=floors[i]) for i, call in enumerate(OP) for o in call]
# wall bands per floor (the frozen band path on the wall layer inside each region)
it = UI.read(PLAN)
walls = {lay for r in P["regions"] for lay, role in (r.get("layer_roles") or {}).items() if role == "WALL"}
bands = []
for fl, b in regions:
    segs = [s for s in it["segments"] if s["layer"] in walls and all(b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] for p in (s["a"], s["b"]))]
    for bd in AP._bands(segs, unit_m):
        bands.append({"floor": fl, "u": bd["u"], "n": bd["n"], "offA": bd["A"]["off"], "offB": bd["B"]["off"], "lo": bd["lo"], "hi": bd["hi"], "t_mm": bd["t"] * mm})
matches_o, matches_w = [], []
for d in dims:
    if not d["usable"]:
        continue
    fl = d["where"].split(":")[1]; u = d["dir"]
    for o in openings:
        if o["floor"] != fl or abs(u[0] * o["u"][0] + u[1] * o["u"][1]) < 0.9995:
            continue
        s = sorted(((p[0] * o["u"][0] + p[1] * o["u"][1]) for p in (d["p2"], d["p3"])))
        oo = [(p[0] * o["n"][0] + p[1] * o["n"][1]) for p in (d["p2"], d["p3"])]
        lo, hi = sorted((o["o0"], o["o1"]))
        if abs(s[0] - o["s0"]) * mm <= 15 and abs(s[1] - o["s1"]) * mm <= 15 and all(lo - 400 / mm <= x <= hi + 400 / mm for x in oo):
            matches_o.append({"dim": d["handle"], "floor": fl, "opening_centre": o["centre"], "opening_width_mm": round(o["width_m"] * 1000, 1),
                              "dim_mm": round(d["stored_mm"], 1), "diff_mm": round(d["stored_mm"] - o["width_m"] * 1000, 1)})
    for bd in bands:
        if bd["floor"] != fl or abs(u[0] * bd["n"][0] + u[1] * bd["n"][1]) < 0.9995:
            continue
        offs = sorted((p[0] * bd["n"][0] + p[1] * bd["n"][1]) for p in (d["p2"], d["p3"]))
        al = [(p[0] * bd["u"][0] + p[1] * bd["u"][1]) for p in (d["p2"], d["p3"])]
        fa, fb = sorted((bd["offA"], bd["offB"]))
        if abs(offs[0] - fa) * mm <= 5 and abs(offs[1] - fb) * mm <= 5 and all(bd["lo"] - 1 / mm <= x <= bd["hi"] + 1 / mm for x in al):
            matches_w.append({"dim": d["handle"], "floor": fl, "band_t_mm": round(bd["t_mm"], 1), "dim_mm": round(d["stored_mm"], 1),
                              "diff_mm": round(d["stored_mm"] - bd["t_mm"], 1)})
matched_openings = {(m["floor"], tuple(round(c, 1) for c in m["opening_centre"])) for m in matches_o}
summ = {"dimensions": len(dims), "by_type": dict(Counter(d["type"] for d in dims)), "by_layer": dict(Counter(d["layer"] for d in dims)),
        "by_location": dict(Counter(d["where"].split(":")[0] + (":" + d["where"].split(":")[1] if d["where"].startswith("PLAN") else "") for d in dims)),
        "associative_dimensions_present": assoc, "dimassoc_header": doc.header.get("$DIMASSOC"),
        "text_overrides": sum(d["text_override"] for d in dims), "duplicates": sum(d["duplicate"] for d in dims),
        "dimlfac_values": dict(Counter(str(d["dimlfac"]) for d in dims)),
        "excluded_reasons": dict(Counter(r for d in dims for r in d["excluded_because"])),
        "usable_for_cross_check": sum(d["usable"] for d in dims),
        "opening_matches": len(matches_o), "openings_with_a_matching_dimension": len(matched_openings), "openings_total": len(openings),
        "opening_width_diff_mm": dict(Counter("0" if abs(m["diff_mm"]) < 0.5 else ("<=5" if abs(m["diff_mm"]) <= 5 else ">5") for m in matches_o)),
        "wall_thickness_matches": len(matches_w),
        "wall_thickness_diff_mm": dict(Counter("0" if abs(m["diff_mm"]) < 0.5 else ("<=5" if abs(m["diff_mm"]) <= 5 else ">5") for m in matches_w))}
json.dump({"summary": summ, "dimensions": dims, "opening_matches": matches_o, "wall_matches": matches_w}, open(OUT, "w"), indent=1, default=str)
print(json.dumps(summ, indent=1))
