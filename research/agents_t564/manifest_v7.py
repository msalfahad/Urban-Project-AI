"""T-564 WIRING MANIFEST V7: the T-558 manifest (V6, pinned) extended by EVERY piece merged after it, up to the pinned
V7 base, on the candidate of record ARCH_TAKEOFF_V3.0.58, PLUS the two fix rows the Checker asked for on T-553 and a
FLOOR-FINISH COMPLETENESS CENSUS of the candidate (R-T564-1, floor_census.py). Research / integration preparation only
(lane I, non-candidate): nothing here writes a candidate, released, rule, knowledge or registry file; nothing is wired.

Coverage by R-T549-1 (V4's check_coverage, reused): range (V6 base 431ac67f, V7 base 33a5833f] on the first-parent line;
every 'Merge agents/task-T-<n>' in it is a source with that merge commit or a declared NO_WIRING piece.

What V7 adds against V6, each from the candidate's own line records or a merged piece's committed output:
  - T-553 F-T553-1 / F-T553-2, FOUND BY THE CENSUS RULE (not by id): C1 MISSING_FLOOR -> the 1F dressing gets a
    FIN.FLOOR.FINISH_HELD line at its released ARCH.SPACE area with its dry bed pair at the candidate's own bed depth;
    C2 WET_BED_DRY_FINISH -> the GF kitchen finish recoded FIN.FLOOR.PORCELAIN -> FIN.FLOOR.WET_TILE (0 m2). Their
    T-455 bindings one by one (adhesive bound rule re-derived and shown class-independent). T-553's own class split
    restated before / after.
  - T-561 ENGINE_OMISSION (Checker 13:55): no FIN.PAINT return line on the plastered door returns -> a named MISSING
    row per plastered return line, HELD, bound beside 0 .. its plaster m2, never 0; FIN.PAINT released unchanged.
  - T-551, T-562, T-566 (reconciliations / statement adapters, ENGINE_WRONG none or lines already HELD), T-558 (V6
    itself): no line moves.
Every source commit must be an ancestor of HEAD (manifest_t536.check_sources). No private drawing is read here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M6 = _load("research/agents_t558/manifest_v6.py", "manifest_v6_t564")              # read only
M5, M4, M2, M1 = M6.M5, M6.M4, M6.M2, M6.M1
FC = _load("research/agents_t564/floor_census.py", "floor_census_t564")
ManifestError = M6.ManifestError
sha256 = M1.sha256

SCHEMA = "URBAN_T564_WIRING_MANIFEST_V7"
RULE = "R-T564-1"
OUT_JSON = ROOT / "research/agents_t564/WIRING_MANIFEST_V7.json"
V6_JSON = M6.OUT_JSON
V6_PIN = "b44b919e4ef749e7d283da6d080e1a806f590a9eba9ef474eeb833c23c78cfe9"     # the merged V6 (3b46332d)
T553 = ROOT / "research/agents_t553/out/FLOOR_TILE_RECONCILE_T553.json"
T561 = ROOT / "research/agents_t561/out/T561_PAINT_RECONCILE.json"
T443_MD = ROOT / "research/agents_t443/T-443_STAIR_ROOM_SKIRTING_SPLIT.md"

V6_BASE = M6.V6_BASE          # 431ac67f Merge agents/task-T-557
V7_BASE = "33a5833f"          # Merge agents/task-T-561 (the newest merge when T-564 was claimed)

NEW_PIECES = {
    "T-551": {"merge": "ea98ad6e", "gate": "A", "rules": ["R-T551-1", "R-T551-2", "R-T551-3", "R-T551-4"],
              "verdict": "Verifier 2026-11-06 11:59Z GATE A PASS: B10 columns -8.770 / necks -8.805 / footing -9.936 / "
                         "blinding -34.321 m3 by component; no ENGINE_WRONG; PARTIAL GF C1-C3 marks -> T-566"},
    "T-553": {"merge": "b6e52d40", "gate": "A", "rules": ["R-T553-1"],
              "verdict": "Verifier 2026-11-06 12:01Z GATE A PASS: floor tile 387.094 vs 409.58 m2 (-5.49 %) by room; "
                         "ENGINE_WRONG F-T553-1 1F dressing 2.970 m2 no floor line, F-T553-2 GF kitchen coded "
                         "PORCELAIN on a wet bed / membrane (0 m2); wiring T-564"},
    "T-558": {"merge": "3b46332d", "gate": "A", "rules": ["R-T558-1"],
              "verdict": "Verifier 2026-11-06 12:00Z GATE A PASS: WIRING MANIFEST V6 + PLASTER_HEIGHT_V1_WIRING "
                         "(Gate B row T-563)"},
    "T-561": {"merge": "33a5833f", "gate": "A", "rules": ["R-T561-1"],
              "verdict": "Verifier 2026-11-06 13:55Z GATE A PASS: paint 217.2081 vs his 1249.375 m2 to cause; "
                         "ENGINE_OMISSION no FIN.PAINT return line (HELD <= 23.070); paint height basis right; 4 "
                         "released paint lines PROVISIONAL"},
    "T-562": {"merge": "81b0eb6f", "gate": "A", "rules": ["R-T562-1"],
              "verdict": "Verifier 2026-11-06 13:55Z GATE A PASS: statement adapters V3 (T-551 / T-553 / T-559 / "
                         "T-556); 25 host-wall terms -> HELD in the statement; no candidate line moves"},
    "T-566": {"merge": "733cf1dd", "gate": "A", "rules": ["R-T566-1", "R-T566-2", "R-T566-3", "R-T566-4"],
              "verdict": "Verifier 2026-11-06 13:55Z GATE A PASS: GF column marks 34 REGISTERED, 2 CONFLICT (10AE, "
                         "10E0: their GF / 1F lines already HELD); beam -0.365 m3 named; no line moves"},
}
NO_WIRING = {
    "T-551": "reconciliation to cause (B10 concrete vs the freelancer): moves no line; ENGINE_WRONG none",
    "T-558": "the V6 manifest itself: superseded here (every V6 statement carried unless listed in v6_to_v7)",
    "T-562": "statement adapters (milestone text): moves no candidate line",
    "T-566": "column mark registration: the 2 CONFLICT positions' lines (L-694a75c8, L-4c449657, L-1dc713c8) are "
             "already HELD; no line moves",
}
WIRING_SOURCES = {"T-553": ["F-T553-1", "F-T553-2"], "T-561": ["T-561 ENGINE_OMISSION (return paint)"]}
PIECES = dict(M6.PIECES, **NEW_PIECES)

# a C1 hit is ENGINE_RIGHT only with a cited owner line (checked: exists, owns floors, same storey) and its source
FLOOR_OWNERS = (
    {"key": "2F-ST-ARRIVAL", "owner_line": "L-5d2be30dd8d2ffeacc42",
     "source": "T-443 (MERGED): SKIRT-T443:2F-ST-ARRIVAL 'material HELD beside the Q-70 A marble landing L-5d2be30d'; "
               "Q-70 A (owner): the 2F stair arrival is marble like the 1F landing (B7), not a B3 floor line"},
)
PAINT_RETURN_TOKENS = ("OPENING", "REVEAL")      # T-561's own selection of plastered return lines (t561_alsenan.py)


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _d(x):
    return None if x is None else Decimal(str(x))


def _src(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def v6_manifest():
    if sha256(V6_JSON) != V6_PIN:
        raise ManifestError(f"PIN: {V6_JSON.name} sha256 {sha256(V6_JSON)[:8]} is not the pinned {V6_PIN[:8]}")
    return _json(V6_JSON)


# ------------------------------------------------------------------------------------------------- census
def _apply(idx, recodes):
    out = {}
    for k, l in idx.items():
        out[k] = dict(l, item_code=recodes[k]) if k in recodes else l
    return out


def floor_census(idx):
    """R-T564-1 on the candidate before, and after the expected fixes (the census must come back clean)."""
    lines = list(idx.values())
    before = FC.census(lines)
    cls = FC.classify(before, lines, FLOOR_OWNERS)
    recodes = {h["line_id"]: h["expected_item_code"] for h in before["C2_wet_bed_dry_finish"]}
    after_idx = _apply(idx, recodes)
    adds = []
    for h in cls["C1"]:
        if h["verdict"] == "ENGINE_WRONG":
            for n, a in enumerate(h["expected_after"]["add"]):
                adds.append({"line_id": f"NEW:{h['key']}:{n}", "item_code": a["item_code"],
                             "element_id": a["element_id"], "class": a["class"], "unit": a.get("unit", "m2"),
                             "measured_net": a.get("value"), "held_low": a.get("held_low"),
                             "held_high": a.get("held_high"), "binding": None, "unbound_records": []})
    after_lines = list(after_idx.values()) + adds
    after = FC.census(after_lines)
    right = {h["key"] for h in cls["C1"] if h["verdict"] == "ENGINE_RIGHT"}
    left_c1 = [h["key"] for h in after["C1_missing_floor"] if h["key"] not in right]
    if left_c1 or after["C2_wet_bed_dry_finish"] or after["C4_bed_pair"]:
        raise ManifestError(f"CENSUS_AFTER: the expected fixes leave hits: C1 {left_c1}, "
                            f"C2 {len(after['C2_wet_bed_dry_finish'])}, C4 {len(after['C4_bed_pair'])}")
    c3a = {s: v["state"] for s, v in after["C3_wp_floor_cover"].items()}
    if set(c3a.values()) != {"COVERED"}:
        raise ManifestError(f"CENSUS_AFTER: WP floor cover not closed after the fixes: {c3a}")
    c3b = before["C3_wp_floor_cover"]
    return {"rule": RULE, "before": before, "classified": cls, "after_hits": {
                "C1": sorted(h["key"] for h in after["C1_missing_floor"]),
                "C2": len(after["C2_wet_bed_dry_finish"]), "C4": len(after["C4_bed_pair"]),
                "C3": {s: [v["residual_m2"], v["state"]] for s, v in after["C3_wp_floor_cover"].items()}},
            "c3_explained": {s: {"residual_before_m2": v["residual_m2"],
                                 "residual_after_m2": after["C3_wp_floor_cover"][s]["residual_m2"],
                                 "state_before": v["state"], "state_after": c3a[s]} for s, v in c3b.items()},
            "recodes": recodes, "adds": adds}


# ------------------------------------------------------------------------------------------------- fix rows
def _t553():
    t = _json(T553)
    if t["index_sha256"] != sha256(M1.INDEX57):
        raise ManifestError("STALE_INPUT: T-553 ran on another line index than the candidate of record")
    return t


def fix_rows(idx, fc):
    """the two rows the Checker asked for on T-553, each from a census hit; T-553's own figures restated."""
    t = _t553()
    wrong = [h for h in fc["classified"]["C1"] if h["verdict"] == "ENGINE_WRONG"]
    missing = {m["element"]: m for m in t["missing_floor_lines"]}
    rows = []
    for h in wrong:
        m = missing.get(h["key"])
        if m is None or Decimal(str(m["area"])) != Decimal(str(h["expected_after"]["floor_change_m2"])) or \
                m["space_line"] != h["space_lines"][0][0]:
            raise ManifestError(f"{h['key']}: census hit is not T-553's missing floor line (area / space line)")
        rows.append({"id": f"FLOOR_MISSING:{h['key']}", "closes": "F-T553-1", "verdict": "ENGINE_WRONG",
                     "physical_element": "the finished floor of the enclosed 1F dressing (ceiling, ceiling paint and "
                                         "skirting lines exist; floor area = its ARCH.SPACE line)",
                     "before": "no floor-finish line, no bed line", "expected_after": h["expected_after"],
                     "evidence_status": "DRAWING-CONFIRMED area (ARCH.SPACE released since V3.0.14; Checker T-553 "
                                        "12:01 1.65 x 1.80 = 2.970); finish material HELD by name (unlabelled face, "
                                        "T-086); bed depth the candidate's own DRY range (Q-45)",
                     "source": _src("T-553")})
    for h in fc["classified"]["C2"]:
        l = idx[h["line_id"]]
        rows.append({"id": f"FLOOR_CLASS:{h['line_id']}", "closes": "F-T553-2", "verdict": "ENGINE_WRONG (class)",
                     "physical_element": f"the floor finish of {l['element_id'].split(':')[0]} on a WET bed "
                                         f"({', '.join(h['bed_lines'])}) under a floor membrane",
                     "before": {"item_code": h["item_code"], "class": l["class"], "m2": h["m2"]},
                     "expected_after": {"item_code": h["expected_item_code"], "class": l["class"], "m2": h["m2"],
                                        "m2_change": 0.0},
                     "evidence_status": "VERIFIED area (unchanged); class from the line's own wet bed + WP floor "
                                        "(Q-30 A, UP-WET-001, owner wet-area rule 2026-11-02)",
                     "source": _src("T-553")})
    if [r["closes"] for r in rows] != ["F-T553-1", "F-T553-2"]:
        raise ManifestError(f"the census did not yield exactly the two T-553 findings: {[r['id'] for r in rows]}")
    # T-553's own class split, restated after the two rows
    cs = {k: Decimal(v) for k, v in t["table"]["class_split_engine"].items()}
    tot = Decimal(t["table"]["engine_total"])
    code = {"DRY": "FIN.FLOOR.PORCELAIN", "WET": "FIN.FLOOR.WET_TILE", "FINISH_HELD": "FIN.FLOOR.FINISH_HELD"}
    for k, c in code.items():
        s = sum((_d(l["measured_net"]) for l in idx.values() if l["item_code"] == c and l["class"] == "RELEASED"),
                Decimal(0))
        if s != cs[k]:
            raise ManifestError(f"T-553 class {k} {cs[k]} is not the candidate's released {c} {s}")
    if sum(cs.values()) != tot:
        raise ManifestError("T-553 class split does not sum to its engine total")
    add = Decimal(str(rows[0]["expected_after"]["floor_change_m2"]))
    mv = Decimal(str(rows[1]["before"]["m2"]))
    after = {"DRY": cs["DRY"] - mv, "WET": cs["WET"] + mv, "FINISH_HELD": cs["FINISH_HELD"] + add}
    his = Decimal(t["table"]["freelancer_total"])
    tot_a = sum(after.values())
    return {"rows": rows, "t553_restated": {
        "before": {k: str(v) for k, v in cs.items()}, "after": {k: str(v) for k, v in after.items()},
        "total_before_m2": str(tot), "total_after_m2": str(tot_a), "freelancer_m2": str(his),
        "gap_before_pct": str(((tot - his) / his * 100).quantize(Decimal("0.01"))),
        "gap_after_pct": str(((tot_a - his) / his * 100).quantize(Decimal("0.01"))),
        "note": "areas installed, no waste; FINISH_HELD = area released, material HELD"}}


def _adh_bound(net):
    """T-455 adhesive bound beside a released tile line of unknown size: net / 5 .. net / 3 (Q-45 bags per m2), 6 dp."""
    n = Decimal(str(net))
    return [float(round(n / 5, 6)), float(round(n / 3, 6))]


def tile_bindings(bs, idx, fx):
    """T-455 bindings of the kitchen line (re-coded, bound unchanged) and of the dressing's new line (HELD blank, as
    the 3 FINISH_HELD lines the candidate already carries)."""
    t455 = [b for b in bs if b["table"] == "T-455"]
    n = 0
    for b in t455:
        if b["kind"] == "adhesive_bags_20kg" and b["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE") and \
                (b["read"] or {}).get("class_read") == "RELEASED":
            if b["bound"] != _adh_bound(b["read"]["net_read"]):
                raise ManifestError(f"ADH_RULE: {b['row']} bound {b['bound']} is not net/5 .. net/3")
            n += 1
    fh = [b for b in t455 if b["item_code"] == "FIN.FLOOR.FINISH_HELD"]
    if not fh or any(b["bound"] is not None or b["value"] is not None for b in fh):
        raise ManifestError("FINISH_HELD bindings are not all HELD blank (precedent unproven)")
    cls_row = next(r for r in fx["rows"] if r["closes"] == "F-T553-2")
    lid = cls_row["id"].split(":", 1)[1]
    rows = []
    for b in sorted((b for b in t455 if b["line_id"] == lid), key=lambda x: x["row"]):
        rows.append({"row": b["row"], "kind": b["kind"],
                     "before": {"item_code": b["item_code"], "bound": b["bound"], "value": b["value"],
                                "status": b["status"]},
                     "expected_after": {"item_code": cls_row["expected_after"]["item_code"], "bound": b["bound"],
                                        "value": None, "status": b["status"]}, "change": "CODE_ONLY"})
    if len(rows) != 2:
        raise ManifestError(f"{lid}: expected 2 T-455 bindings (adhesive, tiles), found {len(rows)}")
    miss = next(r for r in fx["rows"] if r["closes"] == "F-T553-1")
    new_el = miss["expected_after"]["add"][0]["element_id"]
    rows += [{"row": f"{p}|NEW:{new_el}", "kind": k, "before": None,
              "expected_after": {"item_code": "FIN.FLOOR.FINISH_HELD", "bound": None, "value": None, "status": "HELD"},
              "change": "NEW_HELD_BLANK"} for p, k in (("ADH", "adhesive_bags_20kg"), ("TILE", "tiles_nr"))]
    adh = {c: [sum((Decimal(str(b["bound"][i])) for b in t455 if b["item_code"] == c and b["bound"] and
                    b["kind"] == "adhesive_bags_20kg"), Decimal(0)) for i in (0, 1)]
           for c in ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")}
    kb = [Decimal(str(x)) for x in rows[0]["before"]["bound"]] if rows[0]["kind"] == "adhesive_bags_20kg" else \
        [Decimal(str(x)) for x in rows[1]["before"]["bound"]]
    sub = {"FIN.FLOOR.PORCELAIN": {"before": [float(x) for x in adh["FIN.FLOOR.PORCELAIN"]],
                                   "after": [float(a - k) for a, k in zip(adh["FIN.FLOOR.PORCELAIN"], kb)]},
           "FIN.FLOOR.WET_TILE": {"before": [float(x) for x in adh["FIN.FLOOR.WET_TILE"]],
                                  "after": [float(a + k) for a, k in zip(adh["FIN.FLOOR.WET_TILE"], kb)]}}
    return {"rule": "T-455: adhesive bound beside a released tile line = net / 5 .. net / 3 bags (Q-45, size not given),"
                    " the same for PORCELAIN and WET_TILE: reproduced on every released row", "reproduced_on": n,
            "rows": rows, "adhesive_bound_by_code": sub,
            "note": "the project-total adhesive bound does not change (one purchasing group PROJECT for both codes); "
                    "only the per-code split moves; bags stay BOUND_ONLY until a tile size is printed"}


# ------------------------------------------------------------------------------------------------- T-561 return paint
def return_paint(idx):
    t = _json(T561)
    pl = sorted((l for l in idx.values() if l["item_code"] == "FIN.PLASTER" and
                 any(k in l["element_id"] for k in PAINT_RETURN_TOKENS)), key=lambda l: l["line_id"])
    paint_el = {l["element_id"] for l in idx.values() if l["item_code"] == "FIN.PAINT"}
    rows, rel = [], Decimal(0)
    for l in pl:
        twin = l["element_id"].replace("PLASTER", "PAINT")
        if any(k in e for e in paint_el for k in PAINT_RETURN_TOKENS):
            raise ManifestError("a FIN.PAINT return line exists: the T-561 omission is not on this candidate")
        if l["class"] == "RELEASED":
            hi = _d(l["measured_net"])
            rel += hi
        elif l["held_high"] is not None:
            hi = _d(l["held_high"])
        else:
            hi = None
        rows.append({"plaster_line": l["line_id"], "plaster_element": l["element_id"], "plaster_class": l["class"],
                     "expected_after": {"item_code": "FIN.PAINT", "element_id": twin + ":RETURN_PAINT",
                                        "class": "HELD", "value": None,
                                        "bound_beside_m2": None if hi is None else [0.0, float(hi)],
                                        "why": "painted part = return face - frame-covered depth; frame detail not "
                                               "printed (T-561)"}})
    if rel != Decimal("23.07"):
        raise ManifestError(f"valued plastered returns {rel} m2 are not T-561's 23.070")
    cand = Decimal(str(t["candidate_valued_FIN_PAINT_m2"]))
    paint_rel = sum((_d(l["measured_net"]) for l in idx.values() if l["item_code"] == "FIN.PAINT" and
                     l["class"] == "RELEASED"), Decimal(0))
    if cand != paint_rel:
        raise ManifestError(f"T-561 valued paint {cand} is not the candidate's released FIN.PAINT {paint_rel}")
    return {"id": "PAINT_RETURN_MISSING", "closes": "T-561 ENGINE_OMISSION", "verdict": "ENGINE_OMISSION (named "
            "MISSING, HELD)", "rows": rows, "lines": len(rows), "valued_plaster_returns_m2": float(rel),
            "bound_beside_total_m2": [0.0, float(rel)], "fin_paint_released_before_m2": float(paint_rel),
            "fin_paint_released_after_m2": float(paint_rel),
            "evidence_status": "HELD (frame detail not printed); bound from T-561 (Checker 13:55)",
            "owner_row": "none yet: Lead to open (B6 paint, stream F; not inside T-563 plaster or T-423 r2 skirting)",
            "source": _src("T-561")}


# ------------------------------------------------------------------------------------------------- assemble
def wiring_rows(fx, tb, rp):
    return [
        {"id": "FLOOR_FINISH_COMPLETENESS_WIRING", "closes": "F-T553-1 + F-T553-2 (no owning row before V7)",
         "gate": "B (integration package; adds 3 lines and re-codes 1; every other line byte-identical)",
         "steps": [f"1. add {a['item_code']} {a['element_id']} {a['class']} "
                   f"{a['value'] if a['value'] is not None else [a['held_low'], a['held_high']]} {a['unit']}"
                   for a in fx["rows"][0]["expected_after"]["add"]] +
                  [f"2. re-code {fx['rows'][1]['id'].split(':', 1)[1]} {fx['rows'][1]['before']['item_code']} -> "
                   f"{fx['rows'][1]['expected_after']['item_code']} (0 m2)",
                   f"3. T-455 bindings: {len(tb['rows'])} rows to their expected_after (2 code-only, 2 new HELD blank)",
                   "4. FIN.FLOOR total +2.970 m2 (FINISH_HELD); the T-553 class split as t553_restated; the new dry "
                   "bed is bound to the tile-bed mortar producers like the existing FINISH_HELD beds (materials "
                   "binding row of the package, mortar HELD with its bed m3)",
                   "5. census R-T564-1 re-run on the package's line index: C1 only ENGINE_RIGHT hits, C2 / C4 empty, "
                   "C3 COVERED on every storey"],
         "order": "after T-498 / T-423 r2 / T-563 (one candidate package at a time); independent of their lines"},
        {"id": rp["id"], "closes": rp["closes"], "gate": "B (adds HELD blank lines only; FIN.PAINT released "
                                                         "unchanged)",
         "steps": [f"1. {rp['lines']} FIN.PAINT return lines, HELD blank, bound beside 0 .. the plaster return m2 "
                   f"(released total {rp['valued_plaster_returns_m2']})", "2. every other line byte-identical"],
         "order": "any time after T-423 r2 (same B6 family); never folded into a released paint line"},
    ]


def packages():
    return {
        "T-498 (S package)": {"v7_changes": [], "why": "no V7 piece moves a MAS line or a glue host"},
        "T-563 PLASTER_HEIGHT_V1_WIRING": {"v7_changes": [], "why": "T-561 confirms the paint height basis (only "
                                                                    "plaster moves); V6 row unchanged"},
        "T-423 r2 (paint / skirting)": {"v7_changes": [], "why": "the dressing skirting L-4a85470b exists; return "
                                                                 "paint is its own row PAINT_RETURN_MISSING"},
        "T-509 (B1-04 disposal)": {"v7_changes": [], "why": "no V7 piece touches B1"},
        "T-363 / T-372 / T-513 / F package": {"v7_changes": [], "why": "no V7 piece moves their lines"},
        "FLOOR_FINISH_COMPLETENESS_WIRING (new)": {"v7_changes": ["see wiring_rows[0]"], "why": "T-553 + R-T564-1"},
        "PAINT_RETURN_MISSING (new)": {"v7_changes": ["see wiring_rows[1]"], "why": "T-561"},
    }


def build(bs=None):
    v6 = v6_manifest()
    M2.check_sources(PIECES)
    cov = M4.check_coverage(NEW_PIECES, V6_BASE, V7_BASE)
    if not set(NO_WIRING) <= set(NEW_PIECES) or set(NO_WIRING) & set(WIRING_SOURCES):
        raise ManifestError("NO_WIRING and WIRING_SOURCES must be disjoint pieces of this manifest")
    if set(NO_WIRING) | set(WIRING_SOURCES) != set(NEW_PIECES):
        raise ManifestError("every new piece is a wiring source or a declared NO_WIRING piece")
    idx = M1.line_index()
    bs = bs if bs is not None else M5._t523()["bindings"]
    fc = floor_census(idx)
    fx = fix_rows(idx, fc)
    tb = tile_bindings(bs, idx, fx)
    rp = return_paint(idx)
    man = {
        "schema": SCHEMA, "rule": RULE, "candidate": M1.CANDIDATE, "task": "T-564",
        "supersedes": "T-558 WIRING_MANIFEST_V6.json (every V6 / V5 / V4 / V3 / V2 statement carried unless listed "
                      "in v6_to_v7)",
        "coverage_rule": M4.RULE_COVERAGE, "coverage": cov,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V6_JSON, T553, T561, T443_MD, M1.INDEX57, ROOT / M5.T523_MAP,
                    ROOT / "research/agents_t564/floor_census.py")},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())}, "no_wiring": NO_WIRING,
        "wiring_sources": WIRING_SOURCES,
        "floor_census": fc, "fix_rows": fx, "tile_bindings": tb, "return_paint": rp,
        "wiring_rows": wiring_rows(fx, tb, rp), "packages": packages(),
        "v6_rows_carried": {"PLASTER_HEIGHT_V1_WIRING": v6["wiring_row"]["id"] == "PLASTER_HEIGHT_V1_WIRING"},
        "candidate_lines_moved_v6_to_v7": 0, "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    man["v6_to_v7"] = [
        {"what": "floor finish completeness", "v6": "no row", "v7": "FLOOR_FINISH_COMPLETENESS_WIRING (+2.970 m2 "
                 "FINISH_HELD, 1 re-code 0 m2)", "cause": "T-553 + R-T564-1"},
        {"what": "return paint", "v6": "no row", "v7": f"PAINT_RETURN_MISSING ({rp['lines']} HELD lines)",
         "cause": "T-561"}]
    man["findings"] = [
        "F-T564-1: the census finds F-T553-1 and F-T553-2 by rule (C1 / C2) and NO OTHER ENGINE_WRONG floor in the "
        "candidate; the one other C1 hit (2F-ST-ARRIVAL skirting) is ENGINE_RIGHT: its floor is the B7 landing "
        "L-5d2be30d (Q-70 A)",
        "F-T564-2: the GF WP-floor cover residual 9.630133 m2 is the kitchen re-code (9.630001) + 0.000132 rounding "
        "of the pantry membrane printed to 3 dp (13.455 vs 13.454868 of wet finishes in 4 pieces): after the "
        "re-code every storey is COVERED",
        "F-T564-3: T-561's return-paint omission had no owning row; PAINT_RETURN_MISSING carries it HELD, never 0",
    ]
    return man


def dumps(man):
    return M1.dumps(man)


if __name__ == "__main__":
    m = build()
    if "--check" in sys.argv:
        ok = dumps(m) == OUT_JSON.read_text(encoding="utf-8")
        print("CHECK", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT_JSON.write_text(dumps(m), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT))
