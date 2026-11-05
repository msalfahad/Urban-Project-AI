"""T-517: the layers built ABOVE (and round) the membrane of an exposed, roof-function slab zone (B8-06), as their own
physical rows (research, UNWIRED: read by no released method and no candidate V3.0.x; no candidate or released quantity
changes). Project-independent rules; the training-villa inputs live in t517_inputs.py.

PHYSICAL ELEMENT FIRST (ERS s.2.1). A slab top that the waterproofing applicability rules (WP_APPLICABILITY_RULES_V1,
R-WP-APPL-EXPOSED-1 / -FUNCTION-1) put in the ROOF family B8-06 is a roof: on site it is built as the same stack the
roof build-up family carries (T-321 ledger, R-T328-1 in ARCH_TAKEOFF_V3.0.31): screed to falls (the ONE falls volume,
Q-41 'if it is roof or balconies it is screed'), membrane (the waterproofing lines, cross-reference only), insulation,
protection, and the walking finish, each its own item with ONE owner trade, each to its OWN drawn edge. A zone that
carries a roof membrane line and none of the other rows is a silent omission (audit class: missing BOQ scope).

Rules (R-T517-1 .. 6, every villa):
  R-T517-1 COMPLETE STACK. A zone whose membrane function is ROOF has exactly one row per layer of BUILDUP_LAYERS
           (FALLS_SCREED, INSULATION, PROTECTION, FINISH): a layer missing or listed twice fails. The membrane is
           never a row here (its lines are WATERPROOFING; a membrane row is refused: double count).
  R-T517-2 ONE FALLS VOLUME; A BED ONLY IF PRINTED. The falls are made once, by FALLS_SCREED (Lead ruling,
           ELEMENT_REGISTER 'Roof / terrace SCREED TO FALLS' 2026-10-29: Q-45 'roofs: thickness from the falls' is that
           layer's mix, never a second falls volume). A finish bed ABOVE the screed (FINISH_BED) is a row only when a
           drawing prints it as its own layer (scope PRINTED); a bed opened from an owner floor band (Q-45 /
           UPC-TILE-BED-001, scope: floor-tile beds) on a roof is refused (OUT_OF_SCOPE).
  R-T517-3 AREA BY THE LAYER'S OWN EDGE, CITED. Face layers take the membrane plan of the zone (cited from the merged
           membrane rows, never re-derived here); the finish takes the designer's finish hatch. A finish area above
           the face area is refused (a layer cannot exceed its slab). Where the hatch edge and the face edge are two
           readings of one boundary, the row carries the hatch figure (R-T328-1: the finish to its hatch) and the
           face figure BESIDE as a range with its cause named; no hatch printed -> finish area HELD (AREA), never the
           face figure by default.
  R-T517-4 THICKNESS ONLY FROM A PRINT. m / cm / mm normalised (any other unit fails); unprinted -> HELD
           (THICKNESS), never a default. A constant layer's volume = area x t. The falls screed volume = area x (t0 +
           mean rise): it needs the printed t0 AND a falls basis (a printed slope with an outlet / edge drawn); with
           no outlet drawn the owner's falls rule (Q-45 '0.5 % per metre toward each drain') has nothing to run
           toward -> HELD (FALLS) + RFI, never a guessed rise.
  R-T517-5 ONE CEMENT : SAND KEY PER SITE-MIXED HOST. Only a layer whose item code the T-511 census classes HOST
           gets a key (FIN.ROOF.SCREED -> SCREED; a printed FINISH_BED -> TILE_BED); SCOPE_OPEN / NOT_A_KEY codes get
           none. A mix only from a printed note or an owner record whose scope names the layer (R-T514-2); the 1:n
           figure from ONE conversion per ratio (R-T514-3, the owner 1:4 figure governs). The proposed keys are
           checked against every merged producer row (T-511 + T-514): 0 keys with two producers, and no merged host
           on the zone already.
  R-T517-6 HELD BY NAME, NEVER 0. Every HELD row names each missing input (SCOPE, AREA, THICKNESS, FALLS, MIX,
           LAYER_TYPE, MATERIAL, ZONE); a zone hold (e.g. a covered ledge with an open side) holds every layer with
           its area bound BESIDE. Upturn / edge rows: the LENGTH is cited (measured), each build-up layer's height or
           edge treatment is HELD unless printed. A sensitivity figure is BESIDE, labelled NOT A QUANTITY.

Status vocabulary (WORKFLOW_CONTROLS s.5): MEASURED, ASSUMED - OWNER-APPROVED, HELD, UNKNOWN; never VERIFIED here.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

SCHEMA = "URBAN_T517_POOLCOURT_BUILDUP_V1"
GUARD_CLASS = "UNWIRED_RESEARCH"
RULES = ("R-T517-1", "R-T517-2", "R-T517-3", "R-T517-4", "R-T517-5", "R-T517-6")
TOL = 1e-6

BUILDUP_LAYERS = ("FALLS_SCREED", "INSULATION", "PROTECTION", "FINISH")
OPTIONAL_LAYERS = ("FINISH_BED",)
CODES = {"FALLS_SCREED": ("FIN.ROOF.SCREED", "m3"), "INSULATION": ("FIN.ROOF.INSULATION", "m2"),
         "PROTECTION": ("FIN.ROOF.PROTECTION", "m2"), "FINISH": ("FIN.ROOF.FINISH", "m2"),
         "FINISH_BED": ("FIN.FLOOR.BED.DRY", "m3")}
OWNER_TRADE = {"FALLS_SCREED": "SCREED", "INSULATION": "ROOFING B13-01", "PROTECTION": "ROOFING B13-01",
               "FINISH": "ROOFING B13-01", "FINISH_BED": "TILE_BED"}
EDGE = {"FALLS_SCREED": "FACE", "INSULATION": "FACE", "PROTECTION": "FACE", "FINISH": "FINISH",
        "FINISH_BED": "FINISH"}
SCOPES = ("PRINTED", "OWNER_RULE", "UNKNOWN")
FLOOR_BAND_RECORDS = ("Q-45", "UPC-TILE-BED-001")    # owner floor-bed records: scope floor-tile beds, not roofs

T511_PY = ROOT / "research/agents_t511/t511_cement_sand_census.py"
T514_PY = ROOT / "research/agents_t514/t514_screed_bed_producers.py"
T511_OUT = ROOT / "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json"
T514_OUT = ROOT / "research/agents_t514/out/SCREED_BED_PRODUCERS_T514.json"
T494_ROWS = ROOT / "research/agents_t494/T494_COMPONENT_ROWS.json"
INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
PINS = {T511_OUT: "a2716399281fbf9dde2e5e762b57562dabe8edccb53af9781da82bc58678aea5",
        INDEX57: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738"}


class Refused(ValueError):
    """an input the rules must not accept."""


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p, pin=None):
    if pin is not None and sha256(p) != pin:
        raise Refused(f"PIN: {Path(p).name} changed (sha256 differs)")
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def thickness_m(t):
    """R-T517-4: a printed thickness {'value', 'unit' m|cm|mm, 'source'} -> metres; None stays None."""
    if t is None:
        return None
    f = {"m": 1.0, "cm": 0.01, "mm": 0.001}.get(t.get("unit"))
    if f is None or not isinstance(t.get("value"), (int, float)) or isinstance(t.get("value"), bool):
        raise Refused(f"UNIT: thickness {t!r} has no m / cm / mm value")
    if not t.get("source"):
        raise Refused(f"UNSOURCED_THICKNESS: {t!r}: an unprinted thickness is HELD, never a default")
    if t["value"] <= 0:
        raise Refused(f"ZERO: thickness {t!r} is not a thickness (HELD is never 0)")
    return t["value"] * f


def rect_one_edge_mean_rise(width_m, fall):
    """falls model of a rectangle draining to ONE edge (gutter / scupper line along it): the rise grows linearly from
    0 at that edge to fall x width at the far edge, so the mean rise is fall x width / 2 (hand-checkable)."""
    if not (0 < fall < 0.2):
        raise Refused(f"FALL: {fall!r} is a ratio between 0 and 0.2 (1 % = 0.01)")
    if width_m <= 0:
        raise Refused(f"FALL: width {width_m!r}")
    return fall * width_m / 2.0


# ---------------------------------------------------------------- the ledger (R-T517-1 .. 4, 6) ------------------
def ledger(zone, prints):
    """one row per build-up layer of a zone.

    zone: {zone_id, function ('ROOF' | ...), held (reason or ''), face_m2 {'value', 'source'} | None,
           hatch_m2 {'value', 'source', 'edge_cause'} | None, area_bound_m2 (zone held: the bound shown),
           upturn_lm {'value', 'source'} | None, edges_lm {name: {'value', 'source'}},
           falls {'slope', 'outlet_drawn', 'mean_rise_m', 'source'} | None}
    prints: {layer: {'scope': PRINTED | OWNER_RULE | UNKNOWN, 'source', 'thickness', 'mix' (record id or printed
             ratio dict) | None, 'material' {'value', 'source'} | None, 'band_record' (refused on a roof)}}
    """
    if zone.get("function") != "ROOF":
        raise Refused(f"{zone['zone_id']}: function {zone.get('function')!r}: this ledger is for roof-function zones")
    if "MEMBRANE" in prints:
        raise Refused("MEMBRANE: carried by the waterproofing lines (B8-06), never a build-up row (double count)")
    unknown = sorted(set(prints) - set(BUILDUP_LAYERS) - set(OPTIONAL_LAYERS))
    if unknown:
        raise Refused(f"UNKNOWN_LAYER: {unknown}")
    missing_layers = [ly for ly in BUILDUP_LAYERS if ly not in prints]
    if missing_layers:
        raise Refused(f"INCOMPLETE_STACK: {zone['zone_id']} has no row for {missing_layers} (R-T517-1: a silent "
                      f"omission)")
    if "FINISH_BED" in prints:
        b = prints["FINISH_BED"]
        if b.get("scope") != "PRINTED" or any(r in str(b.get("band_record") or "") for r in FLOOR_BAND_RECORDS):
            raise Refused("OUT_OF_SCOPE: a finish bed on a roof is its own layer only when printed; the owner floor "
                          "band (Q-45 / UPC-TILE-BED-001) is a floor-tile bed record, and the roof falls are the one "
                          "FALLS_SCREED volume (R-T517-2)")
    face = zone.get("face_m2")
    hatch = zone.get("hatch_m2")
    held_zone = zone.get("held") or ""
    if face is not None and face["value"] <= 0:
        raise Refused(f"{zone['zone_id']}: a measured face area <= 0 (HELD is never 0)")
    if face is not None and hatch is not None and hatch["value"] - face["value"] > TOL:
        raise Refused(f"FINISH_OVER_FACE: hatch {hatch['value']} m2 > face {face['value']} m2 (R-T517-3)")
    rows = []
    for ly in BUILDUP_LAYERS + tuple(x for x in OPTIONAL_LAYERS if x in prints):
        p = prints[ly]
        if p.get("scope") not in SCOPES:
            raise Refused(f"{ly}: scope {p.get('scope')!r}")
        code, unit = CODES[ly]
        t = thickness_m(p.get("thickness"))
        miss = []
        if held_zone:
            miss.append(f"ZONE: {held_zone}")
        if p["scope"] == "UNKNOWN":
            miss.append("SCOPE: layer printed nowhere and in no owner rule")
        area, area_src, beside = None, None, None
        if EDGE[ly] == "FACE":
            if face is None:
                miss.append("AREA: no face plan for the zone")
            else:
                area, area_src = face["value"], face["source"]
        else:
            if hatch is None:
                miss.append("AREA: no finish hatch printed on the zone (the face plan is not the finish edge)")
            else:
                area, area_src = hatch["value"], hatch["source"]
                if face is not None and face["value"] - hatch["value"] > TOL:
                    beside = {"face_reading_m2": _r(face["value"]), "hatch_reading_m2": _r(hatch["value"]),
                              "difference_m2": _r(face["value"] - hatch["value"]),
                              "cause": hatch.get("edge_cause") or "UNNAMED",
                              "label": "range of one boundary, cause named; the row carries the hatch (R-T328-1)"}
                    if not hatch.get("edge_cause"):
                        raise Refused("UNNAMED_RANGE: a hatch vs face difference needs its cause (R-T517-3)")
        if held_zone:
            area = None
        volume = None
        if unit == "m3":
            if ly == "FALLS_SCREED":
                f = zone.get("falls")
                if t is None:
                    miss.append("THICKNESS: screed thickness at the outlet (t0) not printed")
                if not f or not f.get("outlet_drawn") or f.get("mean_rise_m") is None:
                    miss.append("FALLS: no outlet / falls drawn on the zone: the owner rule 'toward each drain' "
                                "(Q-45) has no drain to run to (RFI)")
                if not miss and area is not None:
                    volume = area * (t + f["mean_rise_m"])
            else:
                if t is None:
                    miss.append("THICKNESS: not printed")
                if not miss and area is not None:
                    volume = area * t
        if ly == "FINISH" and not (p.get("material") or {}).get("value"):
            mat_missing = "MATERIAL: finish type not printed and in no owner rule for this zone"
        else:
            mat_missing = None
        if p["scope"] == "OWNER_RULE":
            label = "ASSUMED - OWNER-APPROVED"
        elif p["scope"] == "UNKNOWN":
            label = "UNKNOWN"
        else:
            label = "MEASURED"
        qty_state = "HELD" if (area is None or (unit == "m3" and volume is None) or
                               (p["scope"] == "UNKNOWN")) else label
        rows.append({
            "zone": zone["zone_id"], "layer": ly, "item_code": code, "unit": unit, "owner_trade": OWNER_TRADE[ly],
            "edge": EDGE[ly], "scope": p["scope"], "scope_label": label, "scope_source": p.get("source"),
            "area_m2": _r(area), "area_source": area_src, "area_beside": beside,
            "area_bound_m2": _r(zone.get("area_bound_m2")) if held_zone else None,
            "thickness_m": _r(t), "thickness_source": (p.get("thickness") or {}).get("source"),
            "volume_m3": _r(volume), "quantity": _r(volume if unit == "m3" else (area if qty_state != "HELD" else None)),
            "state": qty_state, "missing": sorted(set(miss)), "material": (p.get("material") or {}).get("value"),
            "material_missing": mat_missing, "mix": p.get("mix")})
    return rows


def edge_rows(zone, prints):
    """R-T517-6: the build-up at the zone's vertical faces (upturn run) and open edges: lengths cited, every
    layer's upstand height / edge treatment HELD unless printed."""
    out = []
    up = zone.get("upturn_lm")
    if up is not None:
        for ly in BUILDUP_LAYERS:
            h = (prints.get(ly) or {}).get("upstand")
            out.append({"zone": zone["zone_id"], "layer": ly, "kind": "UPSTAND", "length_lm": _r(up["value"]),
                        "length_source": up["source"], "height_m": _r(thickness_m(h)) if h else None,
                        "state": "MEASURED length" if h else "MEASURED length, height HELD (not printed)"})
    for name, e in sorted((zone.get("edges_lm") or {}).items()):
        out.append({"zone": zone["zone_id"], "layer": "ALL", "kind": f"EDGE_TERMINATION:{name}",
                    "length_lm": _r(e["value"]), "length_source": e["source"],
                    "state": "MEASURED length, treatment HELD (edge detail not printed)"})
    return out


# ---------------------------------------------------------------- cement / sand (R-T517-5) -----------------------
def code_class(code, M=None):
    M = M or _module(T511_PY, "t511_cement_sand_census")
    return M.CODE_TABLE.get(code, ("UNCLASSIFIED", None, None))


def producer_state(row, M, conv, records):
    """the cement : sand state of one ledger row: None when its code is no HOST; else
    {'state', 'missing', 'cement_bags', 'sand_m3', 'record'}."""
    kind, trade, _w = code_class(row["item_code"], M)
    if kind != "HOST":
        return None
    miss = []
    mix = row.get("mix")
    rec = None
    if mix is None:
        miss.append("MIX: no printed note and no owner record whose scope names this layer")
    elif isinstance(mix, dict) and mix.get("printed"):
        if not mix.get("source"):
            raise Refused("UNSOURCED_MIX: a printed mix needs its sheet / note")
        rec = {"ratio": mix["ratio"], "label": "DRAWING-CONFIRMED (printed note)", "id": mix["source"]}
    elif isinstance(mix, str) and mix in records:
        scope = records[mix]["scope"]
        need = "FLOOR_TILE_BED" if row["layer"] == "FINISH_BED" else "SITE_MIXED_SCREED"
        if need not in scope:
            raise Refused(f"OUT_OF_SCOPE: {mix} covers {scope}, not {row['layer']} (R-T514-2)")
        rec = {"ratio": records[mix]["ratio"], "label": records[mix]["label"], "id": mix}
    else:
        raise Refused(f"UNSOURCED_MIX: {mix!r} names no printed note and no owner record")
    if row["layer"] == "FALLS_SCREED" and not (isinstance(mix, dict) and mix.get("printed")):
        miss.append("LAYER_TYPE: roof falls layer (cement : sand screed or lightweight fill) not stated")
    if row["volume_m3"] is None:
        miss += [m for m in row["missing"] if not m.startswith("MATERIAL")] or ["AREA / VOLUME HELD"]
    if rec is not None and rec["ratio"] not in conv:
        miss.append(f"MIX: no conversion figure for {rec['ratio']} (R-T514-3)")
    if miss:
        return {"state": "HELD", "trade": trade, "missing": sorted(set(miss)), "record": rec and rec["id"],
                "cement_bags": None, "sand_m3": None}
    b, s, _src = conv[rec["ratio"]]
    v = row["volume_m3"]
    return {"state": "PRODUCED", "trade": trade, "missing": [], "record": rec["id"], "label": rec["label"],
            "ratio": rec["ratio"], "cement_bags": _r(v * b), "sand_m3": _r(v * s),
            "waste": "HELD: waste separate (owner); procurement HELD"}


def proposed_line(row):
    lid = f"PROPOSED-T517:ROOF:{row['zone']}:{row['layer']}"
    return {"line_id": lid, "element_id": f"ROOF:{row['zone']}:{row['layer']}", "item_code": row["item_code"],
            "unit": row["unit"], "class": "HELD" if row["state"] == "HELD" else "RELEASED",
            "measured_net": row["quantity"] if row["state"] != "HELD" else None, "held_low": None,
            "held_high": None, "binding": None, "unbound_records": []}


def census_check(rows, pins=True):
    """R-T517-5 on the merged producers: the proposed hosts join the T-511 census (with the T-514 rows), one key
    each; returns {'fails', 'keys', 'existing_on_zone', 'states'}."""
    M = _module(T511_PY, "t511_cement_sand_census")
    T514 = _module(T514_PY, "t514_screed_bed_producers")
    records = T514.mix_records(pins)
    conv, cfails = T514.conversions(records)
    o511 = load(T511_OUT, PINS[T511_OUT] if pins else None)
    o514 = load(T514_OUT)
    merged = [r for r in o511["rows"]] + [r for r in o514["rows"]]
    lines, states, info = [], {}, []
    for row in rows:
        ln = proposed_line(row)
        st = producer_state(row, M, conv, records)
        kind = code_class(row["item_code"], M)[0]
        info.append({"line_id": ln["line_id"], "item_code": row["item_code"], "code_class": kind,
                     "cement_sand": st})
        if kind == "HOST":
            lines.append(ln)
            if st["state"] == "HELD":
                states[ln["line_id"]] = ("HELD", st["trade"], "HELD (T-517): " + "; ".join(st["missing"]))
    new_rows = []
    for row, i in zip(rows, info):
        st = i["cement_sand"]
        if st and st["state"] == "PRODUCED":
            for mat, val in ((M.CEMENT, st["cement_bags"]), (M.SAND, st["sand_m3"])):
                new_rows.append(M.prow("T-517", M.PRODUCER, i["line_id"], i["line_id"], st["trade"], mat,
                                       M.INSTALLED, val, val, read={"class": "RELEASED", "net": row["quantity"]},
                                       reason=f"{st['record']} {st['ratio']}", trade=st["trade"]))
                for stg in (M.WASTE, M.PROCUREMENT):
                    new_rows.append(M.prow("T-517", M.PRODUCER, i["line_id"], i["line_id"], st["trade"], mat, stg,
                                           None, None, read={"class": "RELEASED", "net": row["quantity"]},
                                           reason="waste separate (owner): HELD", trade=st["trade"]))
    c = M.census(lines, merged + new_rows, states)
    zones = {r["zone"] for r in rows}
    idx = load(INDEX57, PINS[INDEX57] if pins else None)["lines"]
    on_zone = [x["line_id"] for x in idx if any(f":{z}:" in f":{x['element_id']}:" or x["element_id"].startswith(
        f"ROOF:{z}:") for z in zones) and x["item_code"].startswith("FIN.ROOF.")]
    merged_hosts = sorted({r["host"] for r in merged if any(z in str(r["host"]) for z in zones)})
    two = [f for f in c["fails"] if f["kind"] == "TWO_PRODUCERS"]
    return {"fails": c["fails"] + cfails, "keys_with_two_producers": len(two), "info": info,
            "existing_candidate_lines_on_zone": on_zone, "existing_producer_hosts_on_zone": merged_hosts,
            "states": {f"{k[0]}|{k[1]}": v for k, v in sorted(c["states"].items()) if k[0].startswith("PROPOSED-")},
            "t514_missing_hosts": o514.get("missing_hosts"), "conversions": {k: list(v[:2]) for k, v in conv.items()}}


def sensitivity_per_cm(area_m2, conv, ratio="1:4"):
    """BESIDE, NOT A QUANTITY: material per centimetre of an unprinted layer thickness, at a ratio the project
    already uses (R-T514-6 style)."""
    b, s, _ = conv[ratio]
    m3 = area_m2 * 0.01
    return {"m3_per_cm": _r(m3), "ratio": ratio, "cement_bags_per_cm": _r(m3 * b), "sand_m3_per_cm": _r(m3 * s),
            "label": "NOT A QUANTITY: sensitivity per cm of the unprinted thickness; enters no subtotal"}
