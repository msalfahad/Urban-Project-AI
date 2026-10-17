"""ALSENAN_CONTROL_V2 - the control-plane release candidate (round 2). Parallel to V3b; never overwrites it.

    physical space -> semantic zone (TS01) -> trade region (TRADE_DEPENDENCY_MATRIX) -> quantity -> RELEASE_V2

Inputs: the Alsenan context rebuilt with the round-2 production code (alsenan_v3b.build), the rebuilt V3b registers
(alsenan_v3b_registers.registers on that context), the frozen V3b BOQ lines (OLD release, read-only) and the
structural source reader V2. NO benchmark / freelancer value is read here (benchmark firewall; tested).

build(ctx, v3b_regs, frozen_lines, src) -> {register_name: register}
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from engine.source import calibration_v2 as CAL
from engine.source import opening_evidence as OE
from engine.source import release_model_v2 as R
from engine.source import terminal_ledger as TL
from engine.source import trade_dependency as TD

import alsenan_structural_source_v2 as SRC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "alsenan_control_plane_01"))
import extract_live as LIVE  # noqa: E402

FLOOR_OF_LEVEL = {"GF": "GF", "1F": "1F", "2F_ROOF": "2F"}
WET_ROOM_EN = re.compile(r"^(BATH|W\.?C|WASH|TOILET|SHOWER)$", re.I)
SEM_MAP = {"ONE_PHYSICAL_SPACE_ONE_SEMANTIC_ZONE": "SINGLE",
           "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED": "MULTI_UNRESOLVED",
           "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_ESTABLISHED": "MULTI_RESOLVED",
           "BOUNDARY_MISSING": "MULTI_UNRESOLVED", "UNLABELLED": "UNLABELLED"}
ROOM_TRADE = [("F-FL-", "FLOOR_FINISH"), ("F-SK-", "SKIRTING"), ("F-TH-", "THRESHOLD"), ("CE-CO-", "CORNICE"),
              ("CE-", "CEILING"), ("P-SP-", "PLASTER"), ("P-RP-", "PLASTER"), ("P-SD-", "SPATTER_DASH"),
              ("P-PA-", "PAINT"), ("T-WT-", "WALL_TILE"), ("T-SD-", "WALL_TILE"), ("T-TP-", "WALL_TILE"),
              ("T-WP-", "WATERPROOFING")]


def _r(v, n=3):
    return None if v is None else round(float(v), n)


# ============================================================================ rooms -> spaces
def spaces(ctx) -> dict:
    fin = {r["room"]: r for r in ctx["v3"]["finishes"]["rows"]}
    voids = ctx["v3"]["voids"]["items"]
    out = {}
    for r in ctx["v3"]["rooms"]["rows"]:
        f = fin.get(r["id"], {})
        classes = f.get("zone_classes") or [r["room_class"]]
        sem = SEM_MAP.get(r.get("semantic_state"), "UNLABELLED" if r.get("semantic_state") is None else "SINGLE")
        if sem == "UNLABELLED" and r.get("name_basis") and "CANDIDATE" in str(r.get("name_basis")):
            sem = "CANDIDATE_LABEL"
        vres = any(v["site"] == r["site"] and v["state"] == "COMPUTED" for v in voids)
        out[r["id"]] = {"room": r["id"], "floor": r["floor"], "class": r["class"], "room_class": r["room_class"],
                        "upstream_status": r["status"], "semantic_state": sem, "ts01_state": r.get("semantic_state"),
                        "semantic_zones": r.get("semantic_zones"), "zone_classes": classes,
                        "void_split_resolved": vres, "geometry": R.HIGH, "name_en": r["name_en"]}
    return out


def _room_of(code, rooms):
    return next((rid for rid in sorted(rooms, key=len, reverse=True) if code.endswith("-" + rid)), None)


def _room_trade(code):
    return next((t for p, t in ROOM_TRADE if code.startswith(p)), None)


# ============================================================================ populations from production records
def rebar_population_flags(ctx) -> dict:
    """(element, level) -> blocked terminal records (a rebar population with any is incomplete)."""
    lv = {"GF": "GF", "1F": "1F", "2F": "2F_ROOF", "FOUNDATION": "GF"}
    flags = defaultdict(list)
    for key, recs in ctx["v3"]["rebar"].items():
        if not isinstance(recs, list):
            continue
        for b in recs:
            if b.get("status") == "BLOCKED":
                flags[(key.upper(), lv.get(b.get("floor"), "GF"))].append(b.get("terminal_state") or b.get("why"))
    return flags


def blockwork_incomplete_levels(ctx) -> dict:
    lv = {"GF": "GF", "1F": "1F", "2F": "2F_ROOF"}
    out = defaultdict(float)
    for b in ctx["v3"]["blockwork"]["rows"]:
        if b["status"] == "BLOCKED":
            out[lv[b["floor"]]] += b.get("length_m") or 0.0
    return out


# ============================================================================ release V2 for every line
REBAR_POP = {"R-FOOTINGS": "FOOTINGS", "R-COLUMNS": "COLUMNS", "R-BEAMS": "BEAMS", "R-LINTELS": "LINTELS",
             "R-GROUND": "GROUND"}


def _occ_index(lines):
    n, out = Counter(), {}
    for l in lines:
        n[l["code"]] += 1
        out[(l["code"], n[l["code"]])] = l
    return out


def measurement_identity(ctx, frozen_v3a) -> dict:
    """Rebuilt V3a lines (round-2 code) against the frozen V3a lines: every measured number is compared."""
    new, old = _occ_index(ctx["v3b"]["v3a_lines"]), _occ_index(frozen_v3a)
    rows = []
    for k in sorted(set(new) | set(old)):
        a, b = old.get(k), new.get(k)
        qa, qb = (a or {}).get("qty"), (b or {}).get("qty")
        same = (qa is None and qb is None) or (qa is not None and qb is not None and abs(qa - qb) < 5e-4)
        rows.append({"code": k[0], "occurrence": k[1], "frozen_v3a_qty": qa, "rebuilt_v3a_qty": qb,
                     "frozen_v3a_status": (a or {}).get("status"), "rebuilt_v3a_status": (b or {}).get("status"),
                     "kind": "NEW" if a is None else "REMOVED" if b is None else
                     ("IDENTICAL" if same and a.get("status") == b.get("status") else
                      "STATUS_ONLY" if same else "NUMBER_CHANGED")})
    return {"rows": rows, "counts": dict(Counter(r["kind"] for r in rows)),
            "number_changed": [r for r in rows if r["kind"] == "NUMBER_CHANGED"]}


def release_lines(ctx, v3b_regs, frozen_lines, sp) -> list:
    flags = rebar_population_flags(ctx)
    bw_inc = blockwork_incomplete_levels(ctx)
    frozen = _occ_index(frozen_lines)
    seen = Counter()
    openings = ctx["v3"]["openings"]["rows"]
    rows = []
    for ln in v3b_regs["BOQ_LINES_V3B"]["lines"]:
        code, rel = ln["code"], ln["release"]
        t = rel["technical"]
        measured = t["qty"] if t["qty"] is not None else ln.get("measured_qty")
        comps = {"geometry": (R.HIGH, "source geometry / schedule"), "upstream_status": (R.HIGH, "no upstream object")}
        upstream, pop, refs, rule_dep, trade_key, room = "COMPLETE", True, [], True, None, None
        rtrade = _room_trade(code)
        room = _room_of(code, sp) if rtrade else None
        if room:
            s = sp[room]
            ev = TD.evaluate(rtrade, s)
            comps, rule_dep, trade_key = ev["components"], ev["quantity_rule_dependency"], rtrade
            upstream = s["upstream_status"]
            refs += ev["blocking"]
        elif code.split("-")[0] == "R" or code.startswith("R-"):
            base = "-".join(code.split("-")[:2])
            p = REBAR_POP.get(base)
            lvl = ln["level"]
            if p and flags.get((p, lvl)):
                pop = False
                refs += sorted(set(flags[(p, lvl)]))[:6]
            if base == "R-BEAMS" and flags.get(("BEAMS", "GF")) is not None and lvl == "GF":
                pop = False
            trade_key = "REBAR"
        elif code.startswith("B-") and ln["unit"] == "m2":
            trade_key = "BLOCKWORK"
            if bw_inc.get(ln["level"]):
                pop = False
                refs.append(f"BLOCKWORK_BLOCKED_AMBIGUOUS_BAND {bw_inc[ln['level']]:.2f} m on {ln['level']}")
        elif code.startswith("O-") and ln["unit"] == "lm" and code.endswith("-W"):
            fl = FLOOR_OF_LEVEL.get(ln["level"])
            if any(o["floor"] == fl and o.get("width_m") is None for o in openings):
                pop = False
                refs.append("OPENING_WIDTH_BLOCKED (closure not established)")
            trade_key = "OPENING_WIDTH"
        if ln.get("no_total"):
            trade_key = "DIMENSION_ONLY"
        v1 = {"technical": t, "commercial": rel["commercial"]}
        v2 = R.release_v2(technical_class=t["class"], measured_qty=measured, commercial=rel["commercial"],
                          population_complete=pop, upstream_status=upstream, components=comps,
                          quantity_rule_dependency=rule_dep, blocking_refs=refs, v1=v1)
        seen[code] += 1
        fz = frozen.get((code, seen[code]))
        ft = (fz or {}).get("release", {}).get("technical", {})
        fc = (fz or {}).get("release", {}).get("commercial", {})
        rows.append({
            "code": code, "line_id": ln["line_id"], "trade": ln["trade"], "level": ln["level"], "unit": ln["unit"],
            "desc_en": ln["desc_en"], "room": room, "trade_dependency": trade_key, "no_total": bool(ln.get("no_total")),
            "sumrow": ln.get("sumrow"), "old_v3b_frozen": None if fz is None else {
                "qty": fz.get("qty"), "technical_class": ft.get("class"), "technical_qty": ft.get("qty"),
                "in_technical_total": ft.get("in_total"), "commercial_class": fc.get("class"),
                "commercial_qty": fc.get("qty"), "procurement_eligible": fc.get("procurement_eligible"),
                "confidence": fc.get("confidence")},
            "rebuilt_v1": {"status": ln["status"], "technical_class": t["class"], "technical_qty": t["qty"],
                           "measured_qty": measured, "commercial_class": rel["commercial"]["class"],
                           "procurement_eligible_v1": rel["commercial"].get("procurement_eligible")},
            "v2": v2})
    return rows


def migration_register(rows) -> dict:
    out = []
    for r in rows:
        o = r["old_v3b_frozen"]
        v2 = r["v2"]
        old_ver = bool(o and o["in_technical_total"])
        old_proc = bool(o and o["procurement_eligible"])
        new_ver = v2["release_state"] == R.VERIFIED_COMPLETE
        new_proc = v2["procurement_eligible_v2"]
        oq = o and (o["technical_qty"] if o["technical_qty"] is not None else o["qty"])
        nq = r["rebuilt_v1"]["measured_qty"]
        num_same = (oq is None and nq is None) or (oq is not None and nq is not None and abs(oq - nq) < 5e-4) \
            or (oq is None and nq is not None)          # the old line hid its number (REVIEW / BLOCKED): not a change
        out.append({"code": r["code"], "line_id": r["line_id"], "trade": r["trade"], "level": r["level"],
                    "unit": r["unit"], "room": r["room"], "new_line": o is None,
                    "old_qty": oq, "new_measured_qty": nq, "measured_value_identical": num_same,
                    "old_technical_class": o and o["technical_class"], "old_in_technical_total": old_ver,
                    "old_procurement_eligible": old_proc, "old_confidence": o and o["confidence"],
                    "rebuilt_v1_technical_class": r["rebuilt_v1"]["technical_class"],
                    "v2_release_state": v2["release_state"], "v2_in_verified_total": new_ver,
                    "v2_procurement_eligible": new_proc, "v2_evidence_grade": v2["evidence_grade"],
                    "v2_weakest_dependency": v2["weakest_dependency"], "v2_release_reason": v2["release_reason"],
                    "blocking_refs": v2["blocking_refs"],
                    "release_changed": old_ver != new_ver or old_proc != new_proc,
                    "change_kind": ("NEW_LINE" if o is None else
                                    "RELEASE_ONLY" if (old_ver != new_ver or old_proc != new_proc) and num_same else
                                    "MEASUREMENT_AND_RELEASE" if not num_same else "UNCHANGED")})
    return {"SCHEMA": "URBAN_ALSENAN_RELEASE_V2_MIGRATION_V1", "policy": R.POLICY_ID, "rows": out,
            "counts": dict(Counter(r["change_kind"] for r in out)),
            "rule": "every line: OLD = frozen V3b (tests/alsenan/registers_v3b, read-only), V1 rebuilt with the "
                    "round-2 code, V2 release; a line whose release or procurement status changes is listed with the "
                    "reason - nothing changes silently"}


def totals_by_trade(rows) -> dict:
    acc = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r["no_total"] or r["code"].startswith("R-BBS"):
            continue
        k = f"{r['trade']}|{r['unit']}"
        v = r["v2"]
        for f, name in (("qty_verified", "verified"), ("qty_lower_bound", "lower_bound"),
                        ("qty_provisional", "provisional"), ("qty_budget", "budget"), ("qty_audit", "blocked_audit")):
            if v.get(f) is not None:
                acc[k][name] += v[f]
        o = r["old_v3b_frozen"]
        if o and o["in_technical_total"] and o["technical_qty"] is not None:
            acc[k]["old_v3b_technical_total"] += o["technical_qty"]
        acc[k]["lines_blocked"] += 1 if v["release_state"] == R.BLOCKED else 0
    return {k: {kk: _r(vv) for kk, vv in sorted(d.items())} for k, d in sorted(acc.items())}


# ============================================================================ wet labels
WET_TRADES = ["WALL_TILE", "WATERPROOFING", "FLOOR_FINISH (wet tile)"]


def wet_labels(ctx, live, sp) -> dict:
    rows = []
    for w in live["wet_labels"]:
        room = w["room"]
        s = sp.get(room) if room else None
        t = w["text"]
        is_pool = "سباحة" in t
        if w["located"] == "NO_SITE" and is_pool:
            st, why = "WET_LABEL_NOT_IN_SCOPE", "swimming-pool label: the pool population (structure + finish) " \
                                                "carries it, not a wet-room trade"
        elif w["located"] == "NO_SITE":
            st, why = "WET_LABEL_BLOCKED_NO_PHYSICAL_SITE", "the label lies in no closed physical site; the wet " \
                                                           "room's walls are missing / not closed in the source"
        elif w["located"] == "IN_NON_ROOM_SITE":
            st, why = "WET_LABEL_BLOCKED_NO_PHYSICAL_SITE", "the label lies in a site that is not a room row"
        elif s and s["room_class"] in ("WET", "SERVICE"):
            st, why = "WET_LABEL_BOUND_TO_REGION", f"bound to {room} ({s['room_class']}, {s['semantic_state']})"
        elif s and s["room_class"] == "MIXED_SEMANTIC_ZONE":
            st, why = ("WET_LABEL_BLOCKED_SEMANTIC_TRADE_BOUNDARY",
                       f"{room} holds dry and wet zones without a source boundary; its wet trades are BLOCKED")
        else:
            st, why = "WET_LABEL_SOURCE_CONFLICT", f"wet label inside {room} classed {s and s['room_class']}"
        rows.append({"floor": w["floor"], "text": t, "key": w["key"], "xy": w["xy"], "site": w["site"], "room": room,
                     "terminal_state": st, "reason": why, "is_wet_room_label": bool(WET_ROOM_EN.match(t)),
                     "affected_trades": [] if st in ("WET_LABEL_BOUND_TO_REGION", "WET_LABEL_NOT_IN_SCOPE") else
                     WET_TRADES})
    unacc = [r for r in rows if not r["terminal_state"]]
    blocked = [r for r in rows if r["terminal_state"] not in ("WET_LABEL_BOUND_TO_REGION", "WET_LABEL_NOT_IN_SCOPE")]
    return {"SCHEMA": "URBAN_ALSENAN_WET_LABEL_ACCOUNTING_V1", "rows": rows,
            "counts": dict(Counter(r["terminal_state"] for r in rows)),
            "wet_room_labels_en": dict(Counter(r["terminal_state"] for r in rows if r["is_wet_room_label"])),
            "unaccounted_wet_labels": unacc,
            "wet_trade_population_complete": not blocked,
            "rule": "no wet label disappears: every label ends BOUND / BLOCKED_NO_PHYSICAL_SITE / "
                    "BLOCKED_SEMANTIC_TRADE_BOUNDARY / SOURCE_CONFLICT / NOT_IN_SCOPE; a blocked label keeps the "
                    "wet-trade population incomplete (no wall tile / WP total is VERIFIED_COMPLETE for the project)"}


# ============================================================================ openings
def openings(ctx) -> dict:
    H = ctx["v3b"]["finish"]["heights"]
    A = {a["id"]: a for a in ctx["v3b"]["finish"]["areas"]}
    rows = []
    for o in ctx["v3"]["openings"]["rows"]:
        h, a = H.get(o["id"], {}), A.get(o["id"], {})
        tech = h.get("technical")
        hc = ("RASTER_DERIVED" if tech == "RASTER_DERIVED" else
              (h.get("commercial") or "BLOCKED") if h.get("height_m") is not None else "BLOCKED")
        ev = OE.evaluate({"kind": o["kind"], "width_m": o.get("width_m"), "height_m": h.get("height_m"),
                          "height_class": hc, "sill_m": a.get("sill_m")})
        rows.append({"id": o["id"], "floor": o["floor"], "kind": o["kind"], "width_m": o.get("width_m"),
                     "height_m": h.get("height_m"), "height_source_state": h.get("state"), "height_class": hc,
                     "sill_m": a.get("sill_m"), "v3a_record_status": o["status"],
                     "v3a_attribute_states": {k: o.get(k) for k in ("count_state", "width_state", "height_state_v2",
                                                                    "area_state")},
                     **{k: ev[k] for k in ("count", "width", "height", "area", "function", "material")},
                     "flags": ev["flags"]})
    c = {k: dict(Counter(r[k]["state"] for r in rows)) for k in ("count", "width", "height", "area", "function")}
    bad = [r["id"] for r in rows if r["v3a_record_status"] == "COMPUTED" and r["height"]["state"] == "BLOCKED"]
    return {"SCHEMA": "URBAN_ALSENAN_OPENING_EVIDENCE_V2", "policy": OE.POLICY_ID, "rows": rows, "counts": c,
            "glazed_door_candidates": [r["id"] for r in rows if "GLAZED_DOOR_CANDIDATE" in r["flags"]],
            "v3a_computed_with_blocked_height": bad,
            "rule": "count, width, height, area, function and material each carry their own state; area is never "
                    "more certain than width and height; no default height"}


# ============================================================================ wall conservation
def _class_band(width_mm, state):
    if state != "WALL_BAND_ESTABLISHED":
        return "AMBIGUOUS_BLOCKED"
    if width_mm > 400:
        return "EXCLUDED_WITH_REASON"
    return {150: "MASONRY_150", 200: "MASONRY_200"}.get(width_mm, "OTHER_MASONRY")


ROLE_CLASS = {"STRUCTURAL_OBSTACLE": "RC_INTERFACE", "GLAZING_BOUNDARY": "NON_MASONRY",
              "TOPOLOGY_BOUNDARY": "AMBIGUOUS_BLOCKED"}


def walls(ctx, led) -> dict:
    rows, tot = [], defaultdict(float)
    bw_rows = defaultdict(float)
    for b in ctx["v3"]["blockwork"]["rows"]:
        bw_rows[(b["floor"], b["band"])] = b.get("length_m") or 0.0
    for fl in ("GF", "1F", "2F"):
        res, inp = ctx["a2_raw"][fl]["res"], ctx["a2_raw"][fl]["inp"]
        u = (inp.unit_native_to_mm or 1.0) / 1000.0
        faces = set()
        per = defaultdict(float)
        for b in res["wall_bands"]["bands"]:
            L = (b["interval"][1] - b["interval"][0]) * u
            w = int(round(b["width"] * (inp.unit_native_to_mm or 1.0) / 10.0) * 10)
            cls = _class_band(w, b["state"])
            per[cls] += L
            faces.update([b["face_a"], b["face_b"]])
            oid = f"WALL_BAND:{fl}:{b['band_id']}"
            led.admit(oid, "WALL_BAND", b["band_id"], width_mm=w)
            led.terminate(oid, cls, "LENGTH" if cls.startswith("MASONRY") else "NONE",
                          blocking_reason=None if cls.startswith("MASONRY") else b["state"], downstream_trade="BLOCKWORK",
                          release_state=(R.VERIFIED_COMPLETE if cls.startswith("MASONRY") else
                                         R.BLOCKED if cls == "AMBIGUOUS_BLOCKED" else R.NOT_IN_SCOPE),
                          length_m=_r(L), blockwork_row=(fl, b["band_id"]) in bw_rows)
        unp = defaultdict(float)
        for it in res["_items"]:
            if it.source_id in faces:
                continue
            L = LIVE._seglen(it) * u
            cls = ROLE_CLASS.get(it.role, "AMBIGUOUS_BLOCKED")
            unp[(it.role, cls)] += L
            oid = f"BOUNDARY:{fl}:{it.source_id}:{it.role}"
            led.admit(oid, "UNPAIRED_BOUNDARY", it.source_id, role=it.role)
            led.terminate(oid, cls, "NONE", blocking_reason="masonry identity not established"
                          if cls == "AMBIGUOUS_BLOCKED" else None, downstream_trade="BLOCKWORK",
                          release_state=R.BLOCKED if cls == "AMBIGUOUS_BLOCKED" else R.NOT_IN_SCOPE, length_m=_r(L))
        amb_rows = sum(b.get("length_m") or 0.0 for b in ctx["v3"]["blockwork"]["rows"]
                       if b["floor"] == fl and b.get("terminal_state") == "BLOCKWORK_BLOCKED_AMBIGUOUS_BAND")
        raw_unp = unp[("TOPOLOGY_BOUNDARY", "AMBIGUOUS_BLOCKED")]
        row = {"floor": fl, "bands_m_by_class": {k: _r(v) for k, v in sorted(per.items())},
               "raw_ambiguous_m": _r(per["AMBIGUOUS_BLOCKED"]), "accounted_ambiguous_m": _r(amb_rows),
               "unaccounted_ambiguous_m": _r(per["AMBIGUOUS_BLOCKED"] - amb_rows),
               "unpaired_m_by_role_class": {f"{k[0]}|{k[1]}": _r(v) for k, v in sorted(unp.items())},
               "raw_unpaired_boundary_m": _r(raw_unp), "classified_unpaired_m":
                   _r(sum(v for k, v in unp.items() if k[1] != "AMBIGUOUS_BLOCKED")),
               "blocked_unpaired_m": _r(sum(v for k, v in unp.items() if k[1] == "AMBIGUOUS_BLOCKED")),
               "unaccounted_unpaired_m": 0.0,
               "blockwork_release": R.LOWER_BOUND if per["AMBIGUOUS_BLOCKED"] > 1e-6 or raw_unp > 1e-6
               else R.VERIFIED_COMPLETE}
        for k in ("raw_ambiguous_m", "accounted_ambiguous_m", "unaccounted_ambiguous_m", "raw_unpaired_boundary_m",
                  "classified_unpaired_m", "blocked_unpaired_m"):
            tot[k] += row[k] or 0.0
        for k, v in per.items():
            tot["band_" + k] += v
        rows.append(row)
    t = {k: _r(v, 2) for k, v in sorted(tot.items())}
    t["unaccounted_unpaired_m"] = 0.0
    return {"SCHEMA": "URBAN_ALSENAN_WALL_LENGTH_CONSERVATION_V2", "rows": rows, "totals": t,
            "classes": ["MASONRY_150", "MASONRY_200", "OTHER_MASONRY", "RC_INTERFACE", "NON_MASONRY",
                        "OPENING_TRANSITION", "AMBIGUOUS_BLOCKED", "NOT_WALL", "EXCLUDED_WITH_REASON"],
            "rule": "every admitted wall band and every boundary item outside a band ends in one class (ledger); "
                    "ambiguous length stays ambiguous and keeps blockwork at VERIFIED_PARTIAL_LOWER_BOUND"}


# ============================================================================ structural populations
def structural_populations(ctx, defs, led) -> dict:
    rb = ctx["v3"]["rebar"]
    ft_boxed = {d["type"]: d["fields"]["boxed"]["raw_boxed_value"] for d in defs["definitions"]
                if d["element"] == "FOOTING" and d["fields"]["boxed"]["raw_boxed_value"]}
    conflicts = {c["key"] for c in defs["conflicts"]}
    rows = []

    def state_of(recs, extra_block=None):
        blk = [x for x in recs if x.get("status") == "BLOCKED"]
        sets = [x for x in recs if x.get("status") != "BLOCKED"]
        if not recs:
            return R.BLOCKED, "NO_RECORD", []
        if not sets:
            return R.BLOCKED, blk[0].get("terminal_state") or "REBAR_BLOCKED", [b.get("why") for b in blk]
        if blk or extra_block or any(x.get("status") == "PARTIAL" for x in sets):
            whys = [b.get("terminal_state") or b.get("why") for b in blk] + ([extra_block] if extra_block else [])
            if any(x.get("status") == "PARTIAL" for x in sets):
                whys.append("hooks / anchorage BLOCKED_DETAILING (straight part measured)")
            return R.LOWER_BOUND, "REBAR_PARTIAL", whys
        return R.VERIFIED_COMPLETE, "REBAR_COMPLETE", []

    def add(pop, oid, src_ref, conc, st, term, whys, kg, **kw):
        led.admit(oid, pop, src_ref)
        led.terminate(oid, term, "KG" if st != R.BLOCKED else "NONE", blocking_reason="; ".join(map(str, whys)) or None,
                      downstream_trade="REBAR", release_state=st)
        rows.append({"population": pop, "occurrence": oid, "source_ref": src_ref, "concrete_state": conc,
                     "release_state": st, "terminal_state": term, "reasons": whys, "verified_kg":
                     _r(kg) if st == R.VERIFIED_COMPLETE else None, "lower_bound_kg": _r(kg) if st == R.LOWER_BOUND
                     else None, **kw})

    fsets = defaultdict(list)
    for b in rb["footings"]:
        t, n = b["ref"].split()[0], b["ref"].split()[1]
        fsets[(t, n)].append(b)
    for i, f in enumerate(ctx["a3"]["footings"]["rows"]):
        recs = fsets.get((f["type"], f"#{i + 1}"), [])
        bx = ft_boxed.get(f["type"])
        st, term, whys = state_of(recs, f"REBAR_BLOCKED_BOXED_SEMANTICS (raw '{bx}')" if bx else None)
        kg = sum(x.get("straight_weight_kg") or 0.0 for x in recs if x.get("status") != "BLOCKED")
        add("FOOTING", f"FOOTING:{f['type']}#{i + 1}", f["mark_key"].split("|")[1], f.get("status"), st, term, whys, kg,
            type=f["type"])
    csets = defaultdict(list)
    for b in rb["columns"]:
        p = b["ref"].split()
        csets[(p[0], p[2])].append(b)
    for r in ctx["b2a"]["columns"]["rows"]:
        tag = r["tag_key"].split("|")[1]
        oid = f"COLUMN:{r['floor']}:{r['type']}:{tag}"
        if r.get("state") == "NOT_IN_STOREY":
            led.admit(oid, "COLUMN", tag)
            led.terminate(oid, "NOT_REQUIRED", "NONE", downstream_trade="REBAR", release_state=R.NOT_IN_SCOPE)
            rows.append({"population": "COLUMN", "occurrence": oid, "source_ref": tag, "concrete_state": r["state"],
                         "release_state": R.NOT_IN_SCOPE, "terminal_state": "NOT_REQUIRED", "reasons":
                         ["the column type has no section in this storey"]})
            continue
        recs = csets.get((r["floor"], tag), [])
        st, term, whys = state_of(recs)
        aud = sum(((x.get("audit") or {}).get("vertical_straight_kg") or 0.0) +
                  ((x.get("audit") or {}).get("ties_straight_kg") or 0.0) for x in recs)
        kg = sum(x.get("straight_weight_kg") or 0.0 for x in recs if x.get("status") != "BLOCKED")
        add("COLUMN", oid, tag, r["state"], st, term, whys, kg, type=r["type"],
            audit_kg_not_released=_r(aud) if aud else None)
    bsets = defaultdict(list)
    for b in rb["beams"]:
        p = b["ref"].split()
        bsets[(p[0], p[1], p[2])].append(b)
    residue = {(b["floor"], b["type"], b["id"].split("|")[1]): b for b in ctx["v3b"]["struct"]["residue"]["beams"]}
    for fl in ("GF", "1F", "2F"):
        for o in ctx["b2a"]["sheets"][fl]["occurrences"]:
            tag = o["tags"][0].split("|")[1] if o.get("tags") else ""
            recs = bsets.get((fl, o["type"], tag), [])
            st, term, whys = state_of(recs)
            res = residue.get((fl, o["type"], tag))
            kg = sum(x.get("straight_weight_kg") or 0.0 for x in recs if x.get("status") != "BLOCKED")
            add("CONTINUOUS_BEAM" if o["type"].startswith("CB") else "BEAM", f"BEAM:{fl}:{o['type']}:{tag}", tag,
                o["state"], st, term, whys, kg, type=o["type"],
                v3b_residue_commercial=(res or {}).get("commercial", {}) and res["commercial"]["class"])
    for b in [x for x in rb["beams"] if x.get("element") == "STRAP"]:
        typ = b["ref"].split()[1]
        conf = typ in conflicts
        add("STRAP_BEAM", "STRAP:" + b["ref"], b["ref"], b.get("audit", {}).get("concrete_status"), R.BLOCKED,
            "REBAR_BLOCKED_SOURCE_CONFLICT" if conf else b["terminal_state"],
            (["SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY " + typ] if conf else []) + [b["why"]], 0.0, type=typ)
    for b in rb["lintels"]:
        if b.get("status") == "BLOCKED":
            add("LINTEL", "LINTEL:" + b["ref"], b["ref"], "BLOCKED", R.BLOCKED, b["terminal_state"], [b["why"]], 0.0)
    pop = {r["population"]: r for r in ctx["v3b"]["rebar"]["population"]["rows"]}
    for p in ("SLAB", "GROUND", "GROUND_SLAB", "DOME", "POOL", "BOUNDARY_WALL", "GROUND_BEAM_EXT", "COLUMN_STARTERS",
              "STAIRS", "BEAM_RESIDUE", "BEAM_SIDE_BARS", "FOOTING_F_F10"):
        r = pop.get(p)
        if not r:
            continue
        cls = set(r["classes"])
        st = (R.BLOCKED if r["blocked"] and not r["net_kg"] else R.VERIFIED_COMPLETE if cls == {"DERIVED"}
              else R.LOWER_BOUND if "PARTIAL" in cls or "BLOCKED" in cls else R.PROVISIONAL)
        if p == "STAIRS":
            st = R.BLOCKED
        add("POPULATION:" + p, "POPULATION:" + p, "V3b REBAR_POPULATION_REGISTER", None, st,
            "STAIR_REBAR_BLOCKED_APPLICABILITY_UNPROVED" if p == "STAIRS" else "POPULATION_ROW",
            [f"V3b classes {sorted(cls)}"] + (["p.16 typical stair layout not proven applicable"] if p == "STAIRS"
                                                else []), r["net_kg"] or 0.0, v3b_classes=sorted(cls))
    occ = [r for r in rows if not r["population"].startswith("POPULATION:")]
    c = {"complete": sum(r["release_state"] == R.VERIFIED_COMPLETE for r in occ),
         "partial": sum(r["release_state"] == R.LOWER_BOUND for r in occ),
         "blocked": sum(r["release_state"] == R.BLOCKED for r in occ),
         "not_required": sum(r["release_state"] == R.NOT_IN_SCOPE for r in occ)}
    d5 = [r for r in rows if r["terminal_state"] == "REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED"]
    return {"SCHEMA": "URBAN_ALSENAN_STRUCTURAL_POPULATION_COVERAGE_V2", "rows": rows, "occurrence_counts": c,
            "by_population": {k: dict(Counter(r["release_state"] for r in rows if r["population"] == k))
                              for k in sorted({r["population"] for r in rows})},
            "d5_excluded_from_verified": {"occurrences": len(d5),
                                          "audit_kg": _r(sum(r.get("audit_kg_not_released") or 0.0 for r in d5))},
            "rule": "every concrete / rebar population has a terminal state; BLOCKED is allowed, disappearance is "
                    "not; rebar of an occurrence whose concrete is not established never enters a verified total"}


# ============================================================================ structural source coverage / definitions
def source_registers(src, defs, led) -> tuple:
    cov = SRC.coverage(src, defs)
    for r in cov:
        led.admit(r["object_id"], "STRUCTURAL_SOURCE_OBJECT", r["object_id"])
        led.terminate(r["object_id"], r["coverage_state"], "DEFINITION" if r["coverage_state"].startswith("CONSUMED")
                      else "NONE", blocking_reason=None if r["interpretation_state"] == "INTERPRETED" else r["reason"],
                      downstream_trade=r.get("population") or "STRUCTURE", release_state=None)
    adm = [r for r in cov if r["coverage_state"] != "NOT_RELEVANT"]
    interp = sum(r["interpretation_state"] == "INTERPRETED" for r in adm)
    states = Counter(r["coverage_state"] for r in cov)
    coverage = {"SCHEMA": "URBAN_ALSENAN_STRUCTURAL_SOURCE_COVERAGE_V2", "source_sha256": src["sha256"],
                "terminal_states": ["CONSUMED_COMPLETE", "CONSUMED_PARTIAL", "BLOCKED_UNREAD", "SOURCE_CONFLICT",
                                    "NOT_RELEVANT"],
                "rows": cov, "counts": dict(sorted(states.items())),
                "interpretation_counts": dict(sorted(Counter(r["interpretation_state"] for r in cov).items())),
                "accounted": len(cov), "unaccounted": [r["object_id"] for r in cov if not r["coverage_state"]],
                "structural_source_accounting_pct": 100.0,
                "structural_source_interpretation_completion_pct": _r(100.0 * interp / len(adm), 1),
                "rule": "accounting (every admitted source object has a terminal coverage state) is separate from "
                        "interpretation (the object was successfully interpreted); UNREAD / CONFLICT are allowed, "
                        "an object without a state is not"}
    definition = {"SCHEMA": "URBAN_ALSENAN_STRUCTURAL_DEFINITION_V2", "drawing": src["drawing"],
                  "source_sha256": src["sha256"], "definitions": defs["definitions"], "conflicts": defs["conflicts"],
                  "counts": dict(Counter(f"{d['element']}|{d['interpretation_state']}" for d in defs["definitions"])),
                  "rule": "definitions only - no definition feeds a released quantity in round 2; T/M-n and LOAD are "
                          "design loads, never reinforcement; duplicate keys stay visible as SOURCE_CONFLICT"}
    return coverage, definition


# ============================================================================ calibration
def calibration(ctx) -> dict:
    rows = []
    for ref, s in sorted(ctx["v3b"]["raster"]["sheets"].items()):
        obs = [{"ref": o.get("ref"), "px": o["px"], "real_mm": o["printed_cm"] * 10.0} for o in s.get("observations") or []]
        c = CAL.xy([], obs)
        legacy = s.get("px_per_cm")
        repro = (10.0 / c["sy"]) if c.get("sy") else None
        rows.append({"sheet": ref, "legacy_state": s.get("state"), "legacy_px_per_cm": legacy,
                     "v2_mode": c["mode"], "v2_status": c["status"], "v2_flags": c["flags"],
                     "v2_sy_mm_per_px": c["sy"], "v2_sx_mm_per_px": c["sx"], "v2_calibration_id": c["calibration_id"],
                     "v2_reproduces_legacy_px_per_cm": repro,
                     "reproduction_rel_diff": _r(abs(repro - legacy) / legacy, 9) if repro and legacy else None,
                     "observations": len(obs), "rms_residual_mm": c.get("rms_residual_mm"),
                     "max_residual_mm": c.get("max_residual_mm"),
                     "finding": "vertical (level chain) only: X_NOT_OBSERVED. Heights are measured along Y (valid); "
                                "raster opening widths used to match CAD widths assume X = Y scale (flagged, no "
                                "quantity changed this round)"})
    return {"SCHEMA": "URBAN_ALSENAN_CALIBRATION_V2", "policy": CAL.POLICY_ID, "rows": rows,
            "rule": "UNIFORM / XY / AFFINE calibration objects; an unobserved axis is never copied from the other; "
                    "the Alsenan sheets are re-expressed as XY calibrations from the same level-chain observations "
                    "and no Alsenan quantity is recomputed"}


# ============================================================================ build
def build(ctx, v3b_regs, frozen_lines, src, frozen_v3a=None) -> dict:
    sp = spaces(ctx)
    live = LIVE.extract(ctx)
    led = TL.Ledger()
    lines = release_lines(ctx, v3b_regs, frozen_lines, sp)
    for r in lines:
        oid = "BOQ_LINE:" + r["code"] + ":" + r["line_id"]
        led.admit(oid, "BOQ_LINE", r["code"])
        led.terminate(oid, r["v2"]["release_state"], "QTY", blocking_reason=r["v2"]["release_reason"],
                      downstream_trade=r["trade"], release_state=r["v2"]["release_state"])
    room_states = defaultdict(list)
    for r in lines:
        if r["room"]:
            room_states[r["room"]].append(r["v2"]["release_state"])
    for rid, s in sp.items():
        led.admit("ROOM:" + rid, "ROOM", rid)
        st = room_states.get(rid)
        if st:
            worst = max(st, key=lambda x: R.ORDER.get(x, -1))
            led.terminate("ROOM:" + rid, "ROOM_TRADES_" + worst, "QTY", downstream_trade="FINISHES",
                          release_state=worst, trade_states=dict(Counter(st)))
        else:
            led.terminate("ROOM:" + rid, "NOT_IN_SCOPE_" + s["room_class"], "NONE",
                          blocking_reason="no finish trade for this room class (shaft / strip / unknown); owner "
                                          "question", release_state=R.NOT_IN_SCOPE)
    wl = wet_labels(ctx, live, sp)
    for w in wl["rows"]:
        oid = f"WET_LABEL:{w['key']}"
        led.admit(oid, "WET_LABEL", w["key"])
        led.terminate(oid, w["terminal_state"], "NONE", blocking_reason=w["reason"], downstream_trade="WET_TRADES")
    op = openings(ctx)
    for o in op["rows"]:
        led.admit("OPENING:" + o["id"], "OPENING", o["id"])
        led.terminate("OPENING:" + o["id"], "OPENING_AREA_" + o["area"]["state"], "AREA",
                      blocking_reason=o["area"]["reason"], downstream_trade="OPENINGS")
    wall = walls(ctx, led)
    defs = SRC.definitions(src)
    src_cov, src_def = source_registers(src, defs, led)
    spop = structural_populations(ctx, defs, led)
    chk = led.check()
    ledger = {"SCHEMA": "URBAN_ALSENAN_TERMINAL_OBJECT_LEDGER_V1", "policy": TL.POLICY_ID, "check": chk,
              "rows": led.rows(),
              "rule": "number of admitted quantity-bearing objects = number of terminal records; UNKNOWN is allowed, "
                      "UNACCOUNTED is not"}
    cand_tot = totals_by_trade(lines)
    candidate = {"SCHEMA": "URBAN_ALSENAN_CONTROL_V2_CANDIDATE_V1", "label": "ALSENAN_CONTROL_V2 (parallel to V3b)",
                 "totals_by_trade_unit": cand_tot, "lines": [
                     {"code": r["code"], "line_id": r["line_id"], "trade": r["trade"], "level": r["level"],
                      "unit": r["unit"], "desc_en": r["desc_en"],
                      "old_v3b_technical_qty": (r["old_v3b_frozen"] or {}).get("technical_qty"),
                      "old_v3b_release": (r["old_v3b_frozen"] or {}).get("technical_class"),
                      "new_release_state": r["v2"]["release_state"],
                      "new_procurement_eligible": r["v2"]["procurement_eligible_v2"],
                      "no_total": r["no_total"], "sumrow": r["sumrow"],
                      "v2_qty": {k: r["v2"].get(f"qty_{k}") for k in
                                 ("verified", "lower_bound", "provisional", "budget", "audit")},
                      "display": r["v2"]["display"], "blocking_reasons": r["v2"]["blocking_refs"],
                      "release_reason": r["v2"]["release_reason"], "population_complete": r["v2"]["population_complete"],
                      "evidence_grade": r["v2"]["evidence_grade"], "weakest_dependency": r["v2"]["weakest_dependency"],
                      "confidence_reasons": r["v2"]["confidence_reasons"]} for r in lines],
                 "source_coverage": {"accounting_pct": src_cov["structural_source_accounting_pct"],
                                     "interpretation_pct": src_cov["structural_source_interpretation_completion_pct"]},
                 "rule": "V3b is not overwritten; this candidate may lower VERIFIED totals because questionable "
                         "quantities become LOWER_BOUND / PROVISIONAL / BLOCKED - that is not a regression"}
    return {
        "ALSENAN_CONTROL_V2_CANDIDATE": candidate,
        "RELEASE_V2_MIGRATION_REGISTER": dict(migration_register(lines),
                                              v3a_measurement_identity=measurement_identity(ctx, frozen_v3a or [])),
        "TRADE_DEPENDENCY_MATRIX": TD.register(),
        "TERMINAL_OBJECT_LEDGER": ledger,
        "STRUCTURAL_SOURCE_COVERAGE_V2": src_cov,
        "STRUCTURAL_DEFINITION_REGISTER_V2": src_def,
        "STRUCTURAL_POPULATION_COVERAGE_V2": spop,
        "WET_LABEL_ACCOUNTING_REGISTER": wl,
        "OPENING_EVIDENCE_REGISTER_V2": op,
        "WALL_LENGTH_CONSERVATION_V2": wall,
        "CALIBRATION_V2_REGISTER": calibration(ctx),
        "ROOM_SPACES_V2": {"SCHEMA": "URBAN_ALSENAN_ROOM_SPACES_V2", "rows": list(sp.values()),
                           "rule": "physical space + TS01 semantic state + zone classes per room; no DRY wins"},
    }
