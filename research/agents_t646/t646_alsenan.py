"""T-646 development-villa build (research, unwired): the 43 HELD-blank B13 lines of the 10 Nov trial BOQ dry run (T-630:
candidate ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V15 overlay): FIN.ROOF.INSULATION 6 m2, FIN.ROOF.PROTECTION 6 m2,
FIN.ROOF.SCREED 6 m3, FIN.ROOF.FINISH 2 m2, EXT.FENCE.PLASTER 8 m2, EXT.FENCE.PAINT 8 m2, EXT.FENCE.FACE 7 m2, classed
one by one under R-T646-1 (t646_rules.py).

Rebuild (wrapper only): `URBAN_T646_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-646 tests/t646/test_t646.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-646 tests/t646`.

Reads only merged repository files (sha256-pinned below). Own read this run: the architectural DXF (Drive copy, sha256
ab54dd55, decoded into .work/private only): all 675 TEXT / MTEXT / ATTRIB entities (model space + blocks) searched for
insulation / screed / membrane / protection / tile / plaster / paint / sigma / render / finish / coping / cement /
mortar / slope / fall / thickness / cm / mm and the Arabic terms: 0 hits. No coordinate, drawing text or client name is
stored. No candidate, released (V2.9 + route G), rule / knowledge version or registry file is touched."""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t646_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T646_ROOF_FENCE_HOLD_CENSUS_V1", "R-T646-1"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
LIDX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T321 = "research/agents_t321/summary.json"
T404F = "research/agents_t404/FACES_T404.csv"
T404I = "research/agents_t404/ITEMS_T404.csv"
T517 = "research/agents_t517/T-517_POOLCOURT_BUILDUP.md"
PINS = {T630: "e5dde7867c8fe6ad", LIDX: "fed5141ea31bfdd9", T321: "5bad4277dd95971f", T404F: "d90c95947f44639c",
        T404I: "ba281937d2d719ab", T517: "f847500239f7b605"}
OUT_JSON = HERE / "out" / "ROOF_FENCE_HOLD_CENSUS_T646.json"
OUT_MD = HERE / "out" / "ROOF_FENCE_HOLD_CENSUS_T646.md"
SCOPE_CODES = {"FIN.ROOF.INSULATION": 6, "FIN.ROOF.PROTECTION": 6, "FIN.ROOF.SCREED": 6, "FIN.ROOF.FINISH": 2,
               "EXT.FENCE.PLASTER": 8, "EXT.FENCE.PAINT": 8, "EXT.FENCE.FACE": 7}
BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
DC, OA = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"

NOT_PRINTED = ("own DXF census this run: 675 texts, 0 build-up / finish notes (T-321 / T-517 the same); section A-A roof "
               "band a constant drafting band (T-214 / T-221); no finishes schedule or specification issued (D-62, "
               "RFI-B-A12)")
D39 = "designer D-39 (roof datum and build-up: falls screed, insulation, protection printed nowhere)"
# roof zone -> (released finish line, its value m2 = the ONE roof plan area, T-321 zone key)
ROOF_FINISH = {"ROOF-430": ("L-702487d5998861c463c1", "54.9203"), "TERRACE-550": ("L-a6ce29981d037284ec84", "31.643"),
               "ROOF-970": ("L-e005eb9041acb08d8b87", "115.65646"),
               "1F-POOLCOURT-550": ("NEW:FIN.ROOF.FINISH:1F-POOLCOURT-550:finish", "4.519172")}
ROOF_FINISH_VALUES = {v for _, v in ROOF_FINISH.values()}
OUTLETS = {"ROOF-430": 1, "TERRACE-550": 1, "ROOF-970": 3}   # drawn RWPs (sanitary sheets p.2 / p.3; T-221 / T-321)
FALL = "1 % ('SLOPE 1%' printed on the sanitary drainage sheets for +4.30, +5.50 and +9.70; Lead 2026-10-20 10:20)"
FACE_KEYS = ("F-NORTH:FACE:OUTSIDE", "F-NORTH:FACE:PLOT", "F-STREET:FACE:OUTSIDE", "F-STREET:FACE:PLOT",
             "F-SEA:FACE:OUTSIDE", "F-SEA:FACE:PLOT", "F-LOWER:FACE:OUTSIDE", "F-LOWER:FACE:PLOT",
             "F-STREET:FACE:END-G-01")
FENCE_SCOPE = ("finish scope of the site wall OPEN with the owner: OWNER_NOTES_SIGMA_2026-10-21 item 3 'boundary wall "
               "... in Sigma: not answered yet' (which faces, which system, the top); fence p.12 section / elevation / "
               "plan print no finish, coping or render line (T-404 own read, Checker Gate A AGREE); " + NOT_PRINTED +
               "; the house plaster + Sigma method is NOT carried to a site wall (R-T404-5)")


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if h and _sha(p) != h:
            raise R.RuleError(f"input changed: {p} {_sha(p)} != pinned {h}")
    t = (ROOT / T517).read_text(encoding="utf-8")
    for s in ("4.519172", "0.639573", "no outlet"):
        if s not in t:
            raise R.RuleError(f"T-517 report no longer states {s!r}")


def _json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _csv(p):
    import csv
    with (ROOT / p).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def scope_lines():
    rows = [r for r in _json(T630)["per_line"] if r["group"] == "B13" and r["item_code"] in SCOPE_CODES
            and r["class"] == "HELD" and r["held_low"] is None and r["held_high"] is None]
    got = {}
    for r in rows:
        got[r["item_code"]] = got.get(r["item_code"], 0) + 1
        if r["measured_net"] is not None:
            raise R.RuleError(f"{r['line_id']}: HELD with a value in the dry run")
    if got != SCOPE_CODES:
        raise R.RuleError(f"scope changed: {got}")
    # the one roof area: the released finish lines of the dry run must still carry these values
    rel = {r["line_id"]: r for r in _json(T630)["per_line"] if r["item_code"] == "FIN.ROOF.FINISH"
           and r["class"] == "RELEASED"}
    for z, (lid, v) in ROOF_FINISH.items():
        if lid not in rel or D(rel[lid]["measured_net"]) != D(v):
            raise R.RuleError(f"{z}: released finish {lid} no longer {v}")
    if sum(D(v) for _, v in ROOF_FINISH.values()) != D("206.738932"):
        raise R.RuleError("released roof finish total is not 206.738932")
    return rows


def element_of(line_id, lidx):
    if line_id.startswith("NEW:"):
        _, code, zone, layer = line_id.split(":")
        return f"ROOF:{zone}:{layer.upper()}"
    return lidx[line_id]["element_id"]


def roof_entry(r, el, t321):
    _, zone, layer = el.split(":")
    code = r["item_code"]
    e = {"line_id": r["line_id"], "item_code": code, "unit": r["unit"], "element_id": el, "zone": zone,
         "layer": layer, "trade": "B13-01"}
    if zone == "ROOF-1390":
        z = t321["roof_1390_drawing_derived"]
        e.update({"class": "R_ZONE_HELD", "cause": "owner Q-34 PARKED: the 2F top roof stays HELD, raised again only "
                  "at the 12-13 Nov milestone; no roof plan (D-62), no outlet or fall drawn (DRAINS_NOT_DRAWN); every "
                  "layer of it blank" + ("" if layer == "FINISH" else "; and the layer itself: " + NOT_PRINTED),
                  "beside": {"inside_parapet_faces_m2": S(z["inside_parapet_faces_m2"]),
                             "dome_3_footprint_m2": S(z["dome_3_footprint_m2"]) + " (Q-29, not deducted here)",
                             "status": "DRAWING-DERIVED, comparison only"}})
        return e
    if zone == "1F-POOLCOURT-550-LEDGE":
        e.update({"class": "R_ZONE_HELD", "cause": "ZONE HELD (T-517 R-T517, register): the ledge round the void is "
                  "covered 4.20 m above and open at the void; no finish hatch on it (0.000000 m2), roof-function not "
                  "established; at most 0.639573 m2 (T-517 bound) beside, never 0",
                  "beside": {"at_most_m2": "0.639573"}})
        return e
    area = ROOF_FINISH[zone][1]
    if layer in ("INSULATION", "PROTECTION"):
        why = ("INSULATION: " + NOT_PRINTED + "; " + D39 + "; no owner rule names a roof insulation (the one printed "
               "'INSULATION' is the pool detail ST p.7, not extended to a roof, ERS s.3)") if layer == "INSULATION" else \
              ("PROTECTION: Q-41 gives ONE roof screed line ('falls / protection'), carried by FIN.ROOF.SCREED; a "
               "separate protection layer is " + NOT_PRINTED + "; " + D39 + "; valuing it would count the Q-41 screed "
               "twice")
        lq = R.layer_quantity(layer, area)
        if lq["class"] != "HELD":
            raise R.RuleError(f"{r['line_id']}: unprinted layer valued")
        e.update({"class": "R_LAYER_UNPRINTED", "cause": why,
                  "beside": {"roof_plan_area_if_present_m2": S(lq["beside_area_m2"]),
                             "basis": f"the released FIN.ROOF.FINISH line {ROOF_FINISH[zone][0]} (register: one roof "
                                      "plan area); not a bound"}})
        return e
    if layer != "FALLS_SCREED":
        raise R.RuleError(f"{r['line_id']}: unexpected layer {layer}")
    if zone == "1F-POOLCOURT-550":
        e.update({"class": "R_ZONE_HELD", "cause": "falls screed scope ASSUMED - OWNER-APPROVED (Q-41); no outlet and "
                  "no slope drawn for this slab (T-494 RFI, T-517) so no fall can be built, and t0 unprinted (D-39): "
                  "blank, no bound", "beside": {"roof_plan_area_m2": area,
                                                "sensitivity": "0.049069 m3 per cm on the 4.906867 m2 membrane plan "
                                                               "(T-517, not a quantity)"}})
        return e
    z, f = t321["zones"][zone], t321["falls"][zone]
    v, a, rmax = f["volume_above_t0_m3"][0], f["outline_area_m2"], f["rise_max_m"][0]
    low = R.screed_at_least(v, a, area, rmax, fall=FALL, outlets=OUTLETS[zone])
    e.update({"class": "R_SCREED_BOUNDED",
              "cause": "falls screed: scope " + OA + " (Q-41 'roof -> screed', own line; register SCREED TO FALLS one "
                       "volume); fall " + FALL + "; outlets drawn " + str(OUTLETS[zone]) + "; minimum thickness t0 at "
                       "the outlet unprinted (" + D39 + ") -> HELD, high OPEN; low = the screed above the t0 plane on "
                       "the roof plan area under the lowest rise model (EIKONAL, T-221 / T-321)",
              "fix": {"kind": "SET", "before": dict(BLANK),
                      "basis": f"AT_LEAST = V {S(v)} m3 over the falls outline {S(a)} m2 - (outline - roof plan area "
                               f"{area}) x highest rise {S(rmax)} m = {S(low)} m3 (T-321 summary falls / zones, MERGED "
                               "59c82a05)",
                      "after": {"class": "HELD", "measured_net": None, "held_low": S(low), "held_high": None}},
              "beside": {"face_plan_m2": S(z["face_wall_m2"]), "axis_model_above_t0_m3": S(f["volume_above_t0_m3"][1]),
                         "per_cm_t0_m3": S(q(D(area) * D("0.01")))}})
    return e


def fence_entry(r, el, faces, items):
    _, run, rest = el.split(":", 2)
    code = r["item_code"]
    parts = rest.split(":")
    face_key = f"{run}:{parts[0]}:{parts[1]}"
    e = {"line_id": r["line_id"], "item_code": code, "unit": r["unit"], "element_id": el, "face": face_key,
         "trade": "B13-04"}
    if face_key not in FACE_KEYS:
        raise R.RuleError(f"{r['line_id']}: unknown face {face_key}")
    if code == "EXT.FENCE.FACE":
        if parts[1] == "END-G-01":
            it = [i for i in items if i["item"].startswith("F-STREET/END-G-01")][0]
            e.update({"class": "F_FACE_HELD", "cause": "stop-end at the G-01 jamb: the end top is drawn rounded and "
                      "lower than the corner end, undimensioned (p.12 elevation; R-T404-4); designer item (street fence "
                      "top profile)", "beside": {"at_most_m2": S(it["at_most"])}})
            return e
        fr = faces[f"{run}/{parts[1]}"]
        if run == "F-STREET":
            cause = ("street fence top profile (curved dip with the X railing, rounded gate-end top) drawn but not "
                     "dimensioned (p.12 elevation, R-T404-4); designer item; gate G-01 deducted at full height")
        elif run == "F-SEA":
            cause = ("owner Q-63 C: sea-side element HELD (material, height, structure, finishes unknown); designer "
                     "clarification requested; comparison only 2.40 x 2.65 = 6.36 m2 per face (not a bound)")
        else:
            cause = "passage closure 1.200 m: no height printed (T-346 / T-404); designer item"
        e.update({"class": "F_FACE_HELD", "cause": cause,
                  "beside": {"at_most_m2": fr["at_most_m2"] or None,
                             "comparison_only_m2": fr["comparison_only_m2"] or None}})
        return e
    layer = code.split(".")[-1]
    fr = faces[f"{run}/{parts[1]}"]
    face_val = fr["net_m2"] or fr["at_most_m2"] or None
    fl = R.fence_layer(face_val, finish_printed=False, owner_scope_faces=None, face_key=face_key)
    if fl["class"] != "HELD":
        raise R.RuleError(f"{r['line_id']}: fence layer valued without a printed finish")
    e.update({"class": "F_LAYER_HELD",
              "cause": f"{layer}: " + FENCE_SCOPE + ("" if fr["net_m2"] else "; and the face itself is HELD (" +
                                                     (fr["face_held"] or "") + ")"),
              "beside": {"at_most_face_m2": S(fl["held_high"]) if fl["held_high"] is not None else None,
                         "face_status": fr["face_status"]}})
    return e


def build():
    pins()
    rows = scope_lines()
    lidx = {l["line_id"]: l for l in _json(LIDX)["lines"]}
    t321 = _json(T321)
    faces = {f["key"]: f for f in _csv(T404F)}
    items = _csv(T404I)
    entries = []
    for r in sorted(rows, key=lambda x: (x["item_code"], x["line_id"])):
        el = element_of(r["line_id"], lidx)
        if r["item_code"].startswith("FIN.ROOF"):
            entries.append(roof_entry(r, el, t321))
        else:
            entries.append(fence_entry(r, el, faces, items))
    return assemble(entries)


def assemble(entries):
    c = R.census_counts(entries)
    bnd = {}
    for e in entries:
        fx = e.get("fix")
        if fx:
            a = bnd.setdefault(e["item_code"], {"n": 0, "low": Decimal(0)})
            a["n"] += 1
            a["low"] += D(fx["after"]["held_low"])
    beside = Decimal(0)
    for e in entries:
        if e["item_code"] in ("EXT.FENCE.PLASTER", "EXT.FENCE.PAINT") and e["beside"]["face_status"] == DC:
            beside += D(e["beside"]["at_most_face_m2"])
    return {"schema": SCHEMA, "rule": RULE, "task": "T-646", "inputs": {p: _sha(p) for p in PINS},
            "scope": "B13 HELD-blank lines of the T-630 dry run: " + ", ".join(f"{k} {v}" for k, v in
                                                                           SCOPE_CODES.items()),
            "counts": c, "bounded_by_code": {k: {"n": v["n"], "low": S(v["low"]), "high": "OPEN"}
                                             for k, v in sorted(bnd.items())},
            "roof_plan_area_m2": {z: v for z, (_, v) in sorted(ROOF_FINISH.items())},
            "roof_plan_area_total_m2": "206.738932",
            "fence_layers_at_most_on_released_faces_m2": S(beside),
            "own_read": "architectural DXF sha256 ab54dd55: 675 TEXT / MTEXT / ATTRIB, 0 build-up / finish notes",
            "lines": entries}


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def render_md(b):
    c = b["counts"]
    out = ["# T-646 roof layers + fence finishes HELD-blank census (generated; do not edit)", "",
           f"Rule {b['rule']}; lines {c['lines']}; by class {c['by_class']}; fix rows {c['fix_rows']} "
           f"(released {c['released_rows']}, bounded {c['bounded_rows']}); stay blank {c['stay_held_blank']}.", "",
           "Bounded HELD (by code): " + ", ".join(f"{k} {v['low']} .. {v['high']} ({v['n']})"
                                                  for k, v in b["bounded_by_code"].items()), "",
           f"One roof plan area (released FIN.ROOF.FINISH): {b['roof_plan_area_m2']} = {b['roof_plan_area_total_m2']} "
           f"m2. Fence layers at most on the released faces: {b['fence_layers_at_most_on_released_faces_m2']} m2.", "",
           "| line | code | element | class | after | cause |", "|---|---|---|---|---|---|"]
    for e in b["lines"]:
        fx = e.get("fix")
        aft = f"HELD {fx['after']['held_low']} .. OPEN" if fx else "HELD blank"
        out.append(f"| {e['line_id']} | {e['item_code']} | {e['element_id']} | {e['class']} | {aft} | "
                   f"{e['cause'][:150]} |")
    return "\n".join(out) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    print(dumps(build())[:3000])
