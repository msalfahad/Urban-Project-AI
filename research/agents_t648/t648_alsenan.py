"""T-648 development-villa build (research, unwired): the finishes share of finding F-T636-1 (HELD lines of the 10 Nov
trial BOQ T-636 with no committed cause record): B3 65, B8 48, B7 44, B6 14, B4 10, B2 2 (183 lines) plus the B13 lines
of F-T636-1 that T-646 did not class (15), each given ONE cause class under R-T648-1 (t648_rules.py).

Rebuild (wrapper only): `URBAN_T648_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-648 tests/t648/test_t648.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-648 tests/t648`.

Reads only merged repository files (sha256-pinned below); every cause is read from the merged record named in its
'source' (the candidate hold text where a committed extract carries it, else the merged task ledger that classed the
piece). No drawing content, coordinate or client name is stored; drawings are named by sheet only. No candidate,
released (V2.9 + route G), rule / knowledge version or registry file is touched. The freelancer is never a cause."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t648_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T648_FINISH_HOLD_CAUSE_CENSUS_V1", "R-T648-1"
T636 = "research/agents_t636/out/TRIAL_BOQ_T636.json"
LIDX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T646 = "research/agents_t646/out/ROOF_FENCE_HOLD_CENSUS_T646.json"
T500 = "research/agents_t500/out/TILE_BED_MORTAR_T500.json"
T336 = "research/agents_t336/WP_PIECES_T336.csv"
T310 = "research/agents_t310/summary_t310.json"
T347 = "research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json"
T474 = "research/agents_t474/out/FORMWORK_LINE_MAP_T474.csv"
T352 = "research/agents_t352/STAIR_FORMWORK_T352_BY_FACE.csv"
T332F = "research/agents_t352/EXISTING_STAIR_FACES_T332.csv"
T332 = "research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json"
T332B = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
T325 = "research/agents_t325/LINES_T325.csv"
T325L = "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
T340 = "research/agents_t340/FILL_T327_T340.csv"
T335 = "research/agents_t335/CANDIDATE_V3021_T335.json"
T561 = "research/agents_t561/out/T561_PAINT_RECONCILE.json"
T617 = "research/agents_t617/out/T617_HEAD_BOUNDS.json"
T232 = "research/agents_t232/t232_inputs.py"
T577 = "research/agents_t577/out/T577_MARBLE_RECONCILE.json"
T578 = "research/agents_t578/out/T578_RAIL_NOSING_RECONCILE.json"
T508 = "research/agents_t508/summary_t508.json"
T296 = "research/agents_t296/CANDIDATE_V3017_SKIRTING.json"
T553 = "research/agents_t553/out/FLOOR_TILE_RECONCILE_T553.json"
T400 = "research/agents_t400/summary_t400.json"
T534 = "research/agents_t534/out/T534_STAIR_BED_RECONCILE.json"
T580 = "research/agents_t580/out/OVERLAY_T580.json"
T343 = "research/agents_t343/T-343_OUTDOOR_FLOOR_INTEGRATION.md"
T443 = "research/agents_t443/T-443_STAIR_ROOM_SKIRTING_SPLIT.md"
T475 = "research/agents_t475/T-475_LIFT_MARBLE_CENSUS.md"
T511 = "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json"
PINS = {T636: "a08017cce5790891", LIDX: "fed5141ea31bfdd9", T646: "fd4988c7f2f9cf0d", T500: "e2689c7c3da11d9f",
        T336: "8a4f3ab75af755b7", T310: "0302c88b37cce04d", T347: "f6c1232bf9bc93a2", T474: "7a3bfa6a56628172",
        T352: "049fbd000f6614d9", T332F: "b5de40619cfa0bfe", T332: "60e642193f0c77f8", T325: "b85feb1afe272039",
        T325L: "ef6f2cb0c0d7619e", T340: "6f9d326e18e62455", T335: "7ac4ca7373c94b0c", T561: "f8d866b571e315ed",
        T617: "883043d7ae606f37", T232: "b8fe222fba71a51c", T577: "b1b684a3478982b7", T578: "75172951bf95cfdd",
        T508: "8e5f55876e7f49ad", T296: "d82ac42264244a58", T553: "6a58e668e48d8a7b", T400: "5d62bbd7aca59a10",
        T534: "a79bb0f45544b2f3", T580: "ef8f6ca2f163050f", T343: "015119eb4ca08085", T443: "d6a27006b98209f9",
        T475: "9c892fb4bd019fe1", T511: "a2716399281fbf9d",
        T332B: "15c188724a60d580"}
OUT_JSON = HERE / "out" / "FINISH_HOLD_CAUSE_CENSUS_T648.json"
OUT_MD = HERE / "out" / "FINISH_HOLD_CAUSE_CENSUS_T648.md"
GROUPS = ("B2", "B3", "B4", "B6", "B7", "B8")
EXPECT = {"B3": 65, "B8": 48, "B7": 44, "B6": 14, "B4": 10, "B2": 2, "B13": 15}
DC, OA = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"
FACE_KEY = "face_id"
D62 = "D-62 (sheets not in the issued set: no finishes schedule or specification, no door / window schedule)"


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input changed: {p} {_sha(p)} != pinned {h}")


def _json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _csv(p):
    with (ROOT / p).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _find(o, lid):
    """the first dict in o whose 'line_id' (or 'line' / 'id') is lid."""
    st = [o]
    while st:
        x = st.pop()
        if isinstance(x, dict):
            if lid in (x.get("line_id"), x.get("line"), x.get("id")):
                return x
            st.extend(x.values())
        elif isinstance(x, list):
            st.extend(x)
    return None


# ------------------------------------------------------------------ scope

def scope(t636):
    f = t636["findings"]["F-T636-1"]["by_item_code"]
    pl = {r["line_id"]: r for r in t636["per_line"]}
    t646 = {e["line_id"] for e in _json(T646)["lines"]}
    rows = []
    for k, v in sorted(f.items()):
        g = k.split()[0]
        if g not in GROUPS and g != "B13":
            continue
        for lid in v["line_ids"]:
            if g == "B13" and lid in t646:
                continue
            r = pl[lid]
            if r["class"] != "HELD" or r["measured_net"] is not None or r.get("finding") != "F-T636-1":
                raise R.RuleError(f"{lid}: not a HELD F-T636-1 line in T-636")
            rows.append(r)
    got = {}
    for r in rows:
        got[r["group"]] = got.get(r["group"], 0) + 1
    if got != EXPECT:
        raise R.RuleError(f"scope changed: {got}")
    return rows


def E(r, el, cls, cause, source, drawing, **kw):
    e = {"line_id": r["line_id"], "group": r["group"], "item_code": r["item_code"], "unit": r["unit"],
         "element_id": el, "held_low": S(r["held_low"]), "held_high": S(r["held_high"]), "measured_net": None,
         "class": cls, "cause": cause, "source": source, "drawing": drawing}
    e.update(kw)
    return e


# ------------------------------------------------------------------ resolvers (one per family)

def r_bed(r, el, ctx):
    """B3 tile beds: owner Q-45 band 3-4 cm floors / 4-6 cm wet rooms, 1:4: the bound is area x band, never a mid."""
    wet = r["item_code"].endswith(".WET")
    band = ("0.04", "0.06") if wet else ("0.03", "0.04")
    t5 = _find(ctx["t500"], r["line_id"])
    if t5 is not None:
        area, src = t5["area_m2"], f"T-500 (MERGED f1ea10f5) row {r['line_id']}: area {t5['area_m2']} m2, band {t5['band_m']}"
        if [str(D(x)) for x in t5["band_m"]] != [str(D(x)) for x in band]:
            raise R.RuleError(f"{r['line_id']}: T-500 band {t5['band_m']} != Q-45 {band}")
    else:   # overlay NEW line (F-T553-1 completeness wiring): area = its released finish companion
        comp = ctx["pl"].get(r["line_id"][:-1] + "0")
        if comp is None or comp["class"] != "RELEASED":
            raise R.RuleError(f"{r['line_id']}: no released finish companion for the bed area")
        area = comp["measured_net"]
        src = (f"T-636 overlay op FLOOR_FINISH_COMPLETENESS_WIRING|F-T553-1 (companion {comp['line_id']} "
               f"{S(area)} m2 RELEASED)")
    lo, hi = R.band_bound(area, band)
    if lo != q(r["held_low"]) or hi != q(r["held_high"]):
        raise R.RuleError(f"{r['line_id']}: bound {r['held_low']} .. {r['held_high']} != area {area} x {band}")
    return E(r, el, "OWNER_DECISION",
             f"tile bed thickness is an owner BAND ({'4-6 cm wet room' if wet else '3-4 cm floor'}, 1:4; Q-45): the "
             f"line is bounded area x band = {S(area)} x {band[0]} .. {band[1]} = {S(lo)} .. {S(hi)} m3 (re-computed), "
             "a mid value is refused; area as its floor line; released only if the owner fixes one thickness",
             src, "the room's floor outline (P7757 plan sheets, via the floor line); no build-up printed (D-40)",
             owner_ref="Q-45", bound_check={"area_m2": S(area), "band_m": list(band), "low": S(lo), "high": S(hi)})


def r_wp_wet(r, el, ctx):
    lid = r["line_id"]
    pc = ctx["t336"].get(lid)
    code = r["item_code"]
    if code == "FIN.WP.PENETRATION":
        return E(r, el, "DESIGNER_ITEM",
                 f"floor penetrations of wet room {pc['room']}: the drain / pipe count per wet room is not tabled and no "
                 "wet-room detail is issued (T-336 piece " + pc["key"] + ": 'drain / pipe count not tabled: HELD'); what "
                 "a penetration piece is (drain only, or every pipe through the membrane) has no printed detail",
                 f"T-336 WP_PIECES (MERGED c4246877) {pc['key']}",
                 "sanitary-7757 drainage sheets (floor drains drawn, no count table); no wet-room detail sheet (D-62)",
                 designer_ref="D-62")
    if code == "FIN.WP.DOORWAY_TRANSITION":
        if pc is not None:
            k, room = pc["key"], pc["room"]
        else:   # the 3 door rows T-310 added (D-GF-11, D-GF-12, D-1F-06)
            door = [d for d, l in ctx["t310"]["identity"]["wet_area_wp"]["doors"].items() if l == lid]
            if not door:
                raise R.RuleError(f"{lid}: transition with no door")
            k, room = f"T-310 ADD_HELD_DOOR {door[0]}", el.split(":")[0]
        return E(r, el, "OWNER_DECISION",
                 "doorway WP transition: one per physical door, built by DETAIL, never door width x 0.20 (owner Q-35 C, "
                 "UP-WP-DOOR-001); the detail is printed on no sheet, so its m2 stays blank (T-310 policy V3); the count "
                 "line carries the door" + (" (room-side twin replaced by the door row, T-336)" if pc is not None
                                            and pc["action"] == "REPLACE_BY_DOOR_ROW" else ""),
                 f"T-336 WP_PIECES / T-310 (MERGED) {k}; room {room}",
                 "door at the wet-room jamb (P7757 plan sheets); no transition detail issued (D-62)", owner_ref="Q-35 C")
    if code == "FIN.WP.TERMINATION":
        if lid == "L-f78da96a7d31f7b72068":
            return E(r, el, "ENGINE_DEFECT",
                     "engine 'termination other' on the GF core W.C. diagonal face: T-128 r3 reads that face as WALL, so "
                     "no membrane edge exists there (T-303 finding 5); register-only, held by name, never valued",
                     f"T-336 WP_PIECES (MERGED) {pc['key']}; T-303 finding (5)", "P7757 GF plan, core W.C. diagonal face")
        dep = {"L-9592048116294937ab6f": "L-868aee125705bb8d17f6", "L-c57860d79f54a4c1c4b3": "L-9bcc79e76f84667b244a",
               "L-a4df8fc50fbab4bef48f": "L-8090ff20f2b547d1bc96"}.get(lid)
        return E(r, el, "PRINTED_VALUE_GAP",
                 f"membrane edge on the open side {pc['key'].split('/')[1]}: where the membrane stops at a leafless "
                 "opening / open side is printed on no detail (Q-37 A fixes the threshold line only for the pantry); "
                 "bound 0 .. the opening width beside (T-336 rule 3)",
                 f"T-336 WP_PIECES (MERGED) {pc['key']}", "leafless opening on the P7757 GF plan; no wet-room detail",
                 also=f"companion line {dep}" if dep else None)
    if code == "FIN.WP.WALL_UPTURN":
        return E(r, el, "DESIGNER_ITEM",
                 "GF pantry upturn: walls round the printed box less the 1.00 door and the 4.49 m open side; the closure "
                 "of the open side and the wall heights are not printed (T-286; T-336 piece " + pc["key"] + ")",
                 f"T-336 WP_PIECES (MERGED) {pc['key']}", "P7757 GF pantry (DIMENSION 5E1 / 5D5 box)",
                 designer_ref="D-48")
    if code == "FIN.WP.MEMBRANE_ROLLS":
        return E(r, el, "OWNER_DECISION",
                 "membrane rolls to buy on the 2F top roof: a procurement count from the roof cutting plan (Q-49 / Q-58 A "
                 "conditional); the 2F top roof is PARKED by the owner (Q-34: held, raised again at the 12-13 Nov "
                 "milestone; no top-roof plan D-62), so its rolls stay HELD with it (T-646 ROOF-1390 R_ZONE_HELD)",
                 "T-303 inventory FIN.WP.MEMBRANE_ROLLS[pcs]/2F-ROOF-TOP/SUPPLY (MERGED 1d3f69b0); T-646 ROOF-1390",
                 "no top-roof plan in the issued set (D-62)", owner_ref="Q-34")
    raise R.RuleError(f"{lid}: unexpected wet WP code {code}")


def r_wp_fdn(r, el, ctx):
    t = _find(ctx["t347"], r["line_id"])
    f = t["formula"]
    if "D-43" in f:
        return E(r, el, "DESIGNER_ITEM", "lift pit walls: " + f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST p.14 lift pit ('as per lift manufacturer'); outline 1B2B FF", designer_ref="D-43")
    if "PRODUCT_NOT_PRINTED" in f:
        return E(r, el, "PRINTED_VALUE_GAP", f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST p.13 waterproofing notes: no product, laps or coats printed")
    if "Q-31 C" in f and "1B1B" in f:
        return E(r, el, "OWNER_DECISION", f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST foundation plan outline 1B1B (two schedule tags F + F10)", owner_ref="Q-31 C")
    if "Q-21 C" in f:
        return E(r, el, "OWNER_DECISION", f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST p.13 footing details (left > 2.5 m / right < 2.5 m); founding level not printed",
                 owner_ref="Q-21 C")
    if "DEPTH_HELD" in f:
        return E(r, el, "DESIGNER_ITEM", f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST p.13 ground-beam sections 'FOLLOW ARCH.'", designer_ref="D-35")
    if "print no coating" in f:
        return E(r, el, "PRINTED_VALUE_GAP", f, f"T-347 candidate extract (MERGED 509f90c2) {r['line_id']}",
                 "ST p.13 / p.14 boundary beam and strap details (no coating line)")
    raise R.RuleError(f"{r['line_id']}: unclassified foundation WP formula")


def r_formwork(r, el, ctx):
    m = ctx["t474"][r["line_id"]]
    host = m["concrete_line"]
    if host and ctx["lidx"][host]["class"] == "HELD":
        return E(r, el, "DEPENDENCY",
                 f"stair formwork faces of concrete line {host}, which is HELD ({ctx['lidx'][host]['element_id']}): the "
                 "form follows its concrete (T-474 map basis: '" + m["basis"] + "')",
                 f"T-474 FORMWORK_LINE_MAP (MERGED 86335fa8) {r['line_id']}", "ST p.4 / p.5 stair sections",
                 depends_on=host)
    if not host:
        fid = m["face_ids"]
        return E(r, el, "PRINTED_VALUE_GAP",
                 f"untied soffit face {fid} ({ctx['t332b'][fid]['item']}): " + ctx["t332b"][fid]["basis_note"] +
                 "; no concrete line owns it, held by name, at least the T-332 figure "
                 f"{ctx['t332b'][fid]['held_from']} m2 beside",
                 f"T-474 FORMWORK_LINE_MAP (MERGED 86335fa8) {r['line_id']}; T-332 FORMWORK_BY_FACE {fid}",
                 "ST p.4 stair ST-02 layer-5 pairs (handles 535 / 536, 2CC / 2CD)")
    faces = [ctx["t352"][fid] for fid in m["face_ids"].split() if fid in ctx["t352"]]
    if faces:
        why = "; ".join(f"{x['face_id']} {x['piece']} {x['kind']} {x['side']}: {x['basis']}" for x in faces)
        if any("D-43" in (x["source"] + x["basis"]) for x in faces):
            return E(r, el, "DESIGNER_ITEM", "stair side / landing-edge forms against the lift-shaft walls: " + why,
                     f"T-352 STAIR_FORMWORK_BY_FACE (MERGED b12e10de) {m['face_ids']}",
                     "ST p.4 / p.5 (" + ", ".join(x["source"] for x in faces)[:120] + ")", designer_ref="D-43")
        if any("T-258 D1-WAIST" in x["basis"] for x in faces):
            return E(r, el, "PRINTED_VALUE_GAP", "D1 flight sides: " + why,
                     f"T-352 STAIR_FORMWORK_BY_FACE (MERGED b12e10de) {m['face_ids']}", "ST p.3 D1 (1C3 / 143, 15F)")
        if any("Q-61 C" in x["basis"] for x in faces) or any("T-173" in x["basis"] for x in faces):
            return E(r, el, "PRINTED_VALUE_GAP", "landing-edge forms: " + why + " (form against a band / shaft wall "
                     "depends on the construction sequence, printed on no sheet)",
                     f"T-352 STAIR_FORMWORK_BY_FACE (MERGED b12e10de) {m['face_ids']}", "ST p.5 (5E3 / 5C0 / 5D4)")
        return E(r, el, "PRINTED_VALUE_GAP", "stair side / junction faces: " + why,
                 f"T-352 STAIR_FORMWORK_BY_FACE (MERGED b12e10de) {m['face_ids']}", "ST p.4 / p.5 stair sections")
    fid = m["face_ids"]
    fr = ctx["t332b"][fid]
    note = fr["basis_note"]
    if "D-16" in note:
        return E(r, el, "DESIGNER_ITEM",
                 f"soffit face {fid} ({fr['item']}) of a released flight, from {fr['held_from']} m2: " + note,
                 f"T-332 FORMWORK_BY_FACE (MERGED) {fid}; T-474 map {r['line_id']}", "ST p.4 / p.5 stair lane at the "
                 "column", designer_ref="D-16")
    return E(r, el, "PRINTED_VALUE_GAP", f"soffit face {fid} ({fr['item']}), from {fr['held_from']} m2: " + note,
             f"T-332 FORMWORK_BY_FACE (MERGED) {fid}; T-474 map {r['line_id']}", "ST p.4 stair sections")


def r_stair_conc(r, el, ctx):
    t = _find(ctx["t332"], r["line_id"])
    f = t["formula"]
    lid = r["line_id"]
    if lid == "L-7863355dfcb68a681d2d":
        return E(r, el, "DESIGNER_ITEM", "MS1 remainder: " + f[:420], f"T-332 candidate extract (MERGED) {lid}",
                 "ST GF roof slab plan riser lines 45A .. 25E vs architectural GF plan; section A-A", designer_ref="D-67")
    if lid == "L-b6b0354b7842f0ed6e41":
        return E(r, el, "OWNER_DECISION", "ST-02 curved remainder: " + f[:420], f"T-332 candidate extract (MERGED) {lid}",
                 "no section cuts the round reception stair (ST p.4; arch GF / 1F frames)", owner_ref="Q-50 / Q-51")
    if lid in ("L-061e18cf35a4b6b33d68", "L-821032bc04a0b0d02133"):
        return E(r, el, "PRINTED_VALUE_GAP", f[:460], f"T-332 candidate extract (MERGED) {lid}",
                 "ST p.3 entrance steps E1 / D1 (no waist thickness or support printed)")
    if lid == "L-659243ed9fc2831c3ae8":
        return E(r, el, "PRINTED_VALUE_GAP", "MS2 top run: " + f + " (the run's landing levels are scaled, never "
                 "printed; T-192 ledger)", f"T-332 candidate extract (MERGED) {lid}", "ST p.5 / section A-A MS2")
    raise R.RuleError(f"{lid}: unclassified stair concrete")


def r_threshold(r, el, ctx):
    lid = r["line_id"]
    t = ctx["t325"].get(lid, {})
    rfi = t.get("rfi", "")
    if rfi.startswith(("WALL_BAND_REMAINDER", "STRIP_NOT_ATTRIBUTED")):
        return E(r, el, "ENGINE_DEFECT",
                 "not a threshold piece: " + rfi.strip() + " -> T-325 (Checker-merged) classes the 5 unattributed strips "
                 "as wall bodies, not thresholds; held by name (strip polygon " + t.get("strip_m2", "") + " m2, not "
                 "geometry-verified), never valued as a threshold",
                 f"T-325 LINES (MERGED) {lid}; defect D-V26-07", "P7757 doorway wall band (no threshold drawn)")
    if t.get("t240_class") == "EXTERIOR_SILL":
        return E(r, el, "DESIGNER_ITEM",
                 f"external entrance threshold {t['census']}: area {t['low']} m2 bounded (width x wall depth, T-325 "
                 "ledger, DRAWING-CONFIRMED geometry) but the sill finish is by specification and none is printed; the "
                 "wet-door marble rule does not apply to external entrances (URBAN-WET-SERVICE-MARBLE-THRESHOLD v1)",
                 f"T-325 SILL_THRESHOLD_LEDGER (MERGED) {t['census']}; T-340 FILL KEEP", "P7757 plan door "
                 f"{t['census']} (width) x wall thickness", designer_ref="D-10")
    if lid == "L-56acf34557c315f65bb1":
        return E(r, el, "OWNER_DECISION",
                 "sea-side gate D-GF-15 (= G-02) threshold strip: width / host wall not established; the sea-side "
                 "element is HELD by the owner (Q-63 C: material, height, structure, gate)",
                 "T-327 (MERGED 3f8c7d03) ADDED HELD; T-400 / T-584 (MERGED)", "P7757 GF plan D120 block at G-02",
                 owner_ref="Q-63 C")
    if lid == "L-9bcc79e76f84667b244a":
        return E(r, el, "DEPENDENCY",
                 "GF OP-020 leafless passage into the W.C. GF-11: " + rfi + "; its treatment (wet threshold or floor "
                 "continues) follows the membrane edge at the same opening, held on L-c57860d79f54a4c1c4b3",
                 f"T-325 LINES (MERGED) {lid}; T-336 GF-11:DOORWAY_P-GF-01", "P7757 GF plan OP-020 (0.90 x 0.20)",
                 depends_on="L-c57860d79f54a4c1c4b3")
    if lid == "L-868aee125705bb8d17f6":
        fx = {"kind": "SET", "status": DC, "wired": False,
              "terms": {"clear_width_m": ("1.0", "T-325 ledger A-GF-01 (strip line inputs, geometry_verified True)"),
                        "wall_depth_m": ("0.15", "T-325 ledger A-GF-01 depth (P7757 wall faces)")},
              "value": "0.15", "unit": "m2",
              "basis": "A-GF-01 arch opening OP-027: floor strip through the opening (the floor finish continues, "
                       "UP-THR-001), 1.000 x 0.150 = 0.150 m2; T-340 FILL row (MERGED) states the same; the WP membrane "
                       "edge at this opening (L-9592048116294937ab6f) stays HELD on its own line"}
        return E(r, el, "PRINTED_VALUE_GAP",
                 "line blank in the candidate although both terms are printed (UP-THR-001 'floor continues'); the "
                 "merged T-340 FILL row was never carried by an overlay: FIX ROW below (not wired)",
                 f"T-325 LEDGER A-GF-01 / T-340 FILL_T327_T340 (MERGED) {lid}", "P7757 GF plan OP-027 jambs",
                 fix=fx)
    raise R.RuleError(f"{lid}: unclassified threshold")


def r_skirting(r, el, ctx):
    lid = r["line_id"]
    if lid == "L-47fa825d197d32754240":
        t = _find(ctx["t296"], lid)
        return E(r, el, "PRINTED_VALUE_GAP", "GF stair-hall parent remainder: " + t["rfi"] +
                 "; remainder 0.200 lm (GF-ST-CN strip north face, unread, T-574)", f"T-296 skirting extract (MERGED) {lid}",
                 "P7757 GF stair room")
    if lid.startswith("L-4e7d3bef") or lid.startswith("L-d589222e"):
        which = "divider band (RFI a: 2.200 cut / 3.400 outline beside)" if lid.startswith("L-4e7d") else \
            "back-lobby west face (RFI c: 1.150 lm beside if on the drawn line)"
        return E(r, el, "PRINTED_VALUE_GAP", f"GF stair-hall {which}: whether the band / face carries skirting is "
                 "printed on no sheet", f"T-443 report (MERGED) {el}", "P7757 GF stair room")
    t = _find(ctx["t508"], lid)
    if t and t.get("kind") == "LANDING":
        return E(r, el, "DESIGNER_ITEM",
                 f"stair landing skirting {el.split(':')[1]}: sills / heads of W13 / W25 / the landing openings against "
                 "the landing are not printed (T-508 'sills / heads vs the landing not printed')",
                 f"T-508 summary (MERGED 40ab9061) {lid}", "P7757 1F / 2F stair shaft, windows W13 / W25",
                 designer_ref="D-45")
    raise R.RuleError(f"{lid}: unclassified skirting")


def r_stair_skirt(r, el, ctx):
    lid = r["line_id"]
    t = _find(ctx["t508"], lid)
    form = "ZIGZAG (B7-07)" if r["item_code"].endswith("ZIGZAG") else "SLOPED (B7-08)"
    return E(r, el, "OWNER_OPEN",
             f"flight skirting {el.split(':')[1]} as {form}: one blank line per alternative form, never additive; the "
             "payable form is owner item ORR-007 (open); T-508 class " + str(t.get("cls")) +
             (f", figure beside {t['figure_beside_lm']} lm" if t.get("figure_beside_lm") else ""),
             f"T-508 summary (MERGED 40ab9061) {lid}; ELEMENT_REGISTER stair skirting (ORR-007)",
             "P7757 stair flights (ST-01 / ST-02 plans)", owner_ref="ORR-007")


def build():
    pins()
    t636 = _json(T636)
    ctx = {"pl": {r["line_id"]: r for r in t636["per_line"]},
           "lidx": {l["line_id"]: l for l in _json(LIDX)["lines"]},
           "t500": _json(T500), "t336": {x["line_id"]: x for x in _csv(T336)}, "t310": _json(T310),
           "t347": _json(T347), "t474": {x["line_id"]: x for x in _csv(T474)},
           "t352": {x["face_id"]: x for x in _csv(T352)}, "t332f": {x[FACE_KEY]: x for x in _csv(T332F)},
           "t332b": {x["face_id"]: x for x in _csv(T332B)},
           "t332": _json(T332), "t325": {x["line_id"]: x for x in _csv(T325)}, "t325l": _csv(T325L),
           "t296": _json(T296), "t508": _json(T508)}
    rows = scope(t636)
    entries = []
    for r in sorted(rows, key=lambda x: (x["group"], x["item_code"], x["unit"], x["line_id"])):
        el = (ctx["lidx"].get(r["line_id"]) or {}).get("element_id") or r["line_id"]
        entries.append(classify(r, el, ctx))
    return assemble(entries, t636)


def classify(r, el, ctx):
    c, lid = r["item_code"], r["line_id"]
    if c.startswith("FIN.FLOOR.BED."):
        return r_bed(r, el, ctx)
    if c.startswith("FIN.WP."):
        return r_wp_wet(r, el, ctx)
    if c.startswith("WP.FOUNDATION."):
        return r_wp_fdn(r, el, ctx)
    if c == "STR.FORMWORK.STAIR":
        return r_formwork(r, el, ctx)
    if c == "STR.CONC.STAIR":
        return r_stair_conc(r, el, ctx)
    if c == "ARCH.THRESHOLD":
        return r_threshold(r, el, ctx)
    if c == "FIN.SKIRTING":
        return r_skirting(r, el, ctx)
    if c.startswith("FIN.STAIR.SKIRTING."):
        return r_stair_skirt(r, el, ctx)
    return r_table(r, el, ctx)


def r_table(r, el, ctx):
    """the small families, each read from its merged record (named in 'source')."""
    lid, c = r["line_id"], r["item_code"]
    if c == "ARCH.SPACE":
        if "HELD_WITH" in el:
            return E(r, el, "DESIGNER_ITEM", "GF garden band curb strip 3.02 x 0.20 = 0.604 m2: whether the band is "
                     "open to sky or roofed / enclosed is a designer item (D-48); T-431 shrank the zone to the curb",
                     f"T-431 (MERGED a04e3ea8) / T-553 (MERGED) {lid}", "P7757 GF plan garden band",
                     designer_ref="D-48")
        return E(r, el, "OWNER_DECISION", "GF round-stair footprint 6.124412 m2 under the cut: out of the floor tile by "
                 "rule (UP-CER-001 stair footprint out of the tile, UP-STAIR-005; treads are the B7 marble lines): a "
                 "B2 space record held by rule, not a priced floor quantity", f"T-553 FLOOR_TILE_RECONCILE (MERGED) {lid}",
                 "P7757 GF stair room (T-341 / T-345 face)", owner_ref="UP-CER-001 / UP-STAIR-005")
    if c == "FIN.FLOOR.FINISH_HELD":
        return E(r, el, "DESIGNER_ITEM", "GF stair room centre strip (hall +1.00 / back-door lobby +0.30): floor material "
                 "porcelain or landing marble not printed (no finishes schedule); bound 0 .. 0.23 m2",
                 f"T-553 FLOOR_TILE_RECONCILE held_lines (MERGED) {lid}", "P7757 GF stair room", designer_ref="D-10")
    if c in ("FIN.PAINT", "FIN.PLASTER"):
        room = el.split(":")[2]
        t617 = _find(_json(T617), lid)
        if room.startswith("ST_"):
            return E(r, el, "DESIGNER_ITEM", f"stair-shaft {room} faces: floor build-up b 0 .. 0.10 and the held contacts "
                     "/ openings (winder turn, beam ends at the stair head, two window heads, a doorless passage head) "
                     "bound the net (T-173 s.1)", f"T-335 candidate extract (MERGED) {lid}",
                     "P7757 stair shaft; section A-A", designer_ref="D-40")
        if c == "FIN.PLASTER":
            return E(r, el, "DESIGNER_ITEM", f"room {room} plaster after PLASTER_HEIGHT_V1 (T-563 overlay op APPLIED): "
                     "plaster runs to the structural slab / roof underside (owner Q-72) and the opening heights not "
                     "printed (D-45: window schedule; door head 2.20 Q-55 C) keep the net a bound (T-617 head bounds)",
                     f"T-580 overlay op T-563|PLASTER_HEIGHT_V1|{lid}; T-561 / T-617 (MERGED)",
                     "P7757 elevations / sections (9 openings print sill / head)", designer_ref="D-45")
        return E(r, el, "DESIGNER_ITEM", f"room {room} paint: one or more opening heights printed on no sheet (window "
                 "schedule D-45; lift landing door / saloon glazing heights, T-561) keep the net a bound"
                 + (f"; T-617 head bounds row (low after {t617.get('held_low_after')})" if t617 else ""),
                 f"T-617 HEAD_BOUNDS / T-561 PAINT_RECONCILE (MERGED) {lid}",
                 "P7757 elevations / sections (9 openings print sill / head)", designer_ref="D-45")
    if c == "ARCH.SHUTTER":
        w = el.split(":")[1]
        return E(r, el, "DESIGNER_ITEM", f"shutter {w}: drawn on an elevation only, no size, type or schedule printed "
                 "(the drawings show shutters only at W14 and louvred leaves at W11 / W12 on the fence elevation; no "
                 "railing / shutter schedule)", "DESIGNER_CLARIFICATIONS D-54; T-232 HEADS (W11 / W12, T-207)",
                 "P7757 elevations sheet 9 (W11 / W12 / W14)", designer_ref="D-54")
    if c == "ARCH.WINDOW":
        return E(r, el, "DESIGNER_ITEM", "W02 GF saloon glazing: count 1 on every drawing vs 2 with a pier on the "
                 "render (WORKFLOW_CONTROLS s.8 DIFFERS): count HELD 1 .. 2, the m2 has no figure (with a pier the "
                 "glazed area is less by a width no sheet prints)", f"T-232 t232_inputs W02 (MERGED a0cd9bbc)",
                 "P7757 GF plan / section B-B (W02 6.33 x 2.20)", designer_ref="D-53")
    if c == "DOOR.MAIN_ENTRANCE":
        return E(r, el, "DESIGNER_ITEM", "main entrance D-GF-07: plan / SE elevation print a 2.00 x 2.50 double door, "
                 "the renders show a single leaf (WORKFLOW_CONTROLS s.8 DIFFERS): 1 pc / 5.000 m2 is the candidate only",
                 "T-232 t232_inputs ENGINE_HELD D-GF-07 (MERGED a0cd9bbc)", "P7757 GF plan, SE elevation (200 x 250)",
                 designer_ref="D-53")
    if c == "DOOR.INTERNAL.PVC":
        fl = el.split(":")[2]
        doors = "D-GF-02, D-GF-10, D-GF-14 (width 0.69 leaf .. 0.80 closure each)" if fl == "GF" else \
            "D-1F-03 (0.89 .. 1.00) and D-1F-04 (0.69 .. 0.80)"
        return E(r, el, "DESIGNER_ITEM", f"{fl} PVC doors held in the engine door schedule (element PROVISIONAL): "
                 f"{doors} x 2.20 m (owner fallback height Q-55, ASSUMED); no door schedule prints which width the door "
                 "unit takes (Q-04 relates a nominal door to its wall-to-wall opening, +0.10 m)",
                 "T-232 t232_inputs ENGINE_HELD (MERGED a0cd9bbc)", "P7757 plan sheets 3 / 4 (door symbols, widths)",
                 designer_ref="D-07")
    if c == "FIN.MARBLE.LIFT_SURROUND":
        t = _find(_json(T577), lid)
        return E(r, el, "PRINTED_VALUE_GAP", "lift landing surround (B6-06, marble jambs + head on the landing face): "
                 "the landing door height is printed on no sheet (ST p.14 'Lift door' without size; register LIFT "
                 f"LANDING DOOR), so the surround is bounded {t['m2']['bound'][0]} .. {t['m2']['bound'][1]} m2",
                 f"T-475 lift census (MERGED 803f39fc) / T-577 pieces (MERGED) {lid}", "ST p.14 lift; P7757 landing "
                 "walls")
    if c in ("FIN.MARBLE.TREAD", "FIN.MARBLE.LANDING"):
        t = _find(_json(T534), lid)
        return E(r, el, "PRINTED_VALUE_GAP", f"{t['note']}: a bound 0 .. {S(r['held_high'])} m2 (the piece is "
                 "seen in plan but its owner level / extent is printed on no stair section)",
                 f"T-534 STAIR_BED_RECONCILE (MERGED) {lid}", "P7757 GF / 1F / 2F stair rooms (ST-01 / ST-02)")
    if c in ("FIN.RAILING", "MET.RAILING.GUARD"):
        t = _find(_json(T578), lid)
        return E(r, el, "DESIGNER_ITEM", f"rail run {t['run']}: {t['why']}", f"T-578 RAIL_NOSING (MERGED) {lid}",
                 "P7757 stair ST-02 / fence p.12 elevation", designer_ref="D-54")
    if c == "EXT.FENCE.BLOCK_COUNT":
        return E(r, el, "OWNER_DECISION", "fence block type HELD (Q-65 C): the count follows the block specification, "
                 "never an assumed size", f"T-400 summary (MERGED 0c5d526c) {lid}", "fence p.12", owner_ref="Q-65 C")
    if c == "EXT.FENCE.MASONRY_BELOW_NG":
        return E(r, el, "PRINTED_VALUE_GAP", "masonry below N.G. between the two ground beams: formation printed only "
                 "as a minimum ('AS PER EXCAVATION DEPTH BELOW N.G.', ST p.14 A-A; p.9 n.1), so the height has no upper "
                 "bound; AT_LEAST 17.628 m2 beside", f"T-400 summary (MERGED) {lid}", "ST p.14 section A-A")
    if c == "EXT.FENCE.TOP":
        return E(r, el, "DESIGNER_ITEM", "street fence top profile drawn, not dimensioned (p.12 elevation: dip with X "
                 "railing, rounded end; R-T404-4); AT_LEAST 5.60 lm beside", f"T-400 summary (MERGED) {lid}",
                 "fence p.12 elevation", designer_ref="D-01")
    if c == "EXT.FENCE.GATE":
        if "G-02" in el:
            return E(r, el, "OWNER_DECISION", "sea gate G-02 (= D-GF-15, counted once): sea-side element HELD by the "
                     "owner (Q-63 C); opening 1.00 m beside", f"T-400 summary / T-361 (MERGED) {lid}",
                     "P7757 GF plan D120 at G-02", owner_ref="Q-63 C")
        return E(r, el, "PRINTED_VALUE_GAP", "street gate G-01: no leaf drawn (opening 2.50 m DRAWING-CONFIRMED, HIDDEN "
                 "gap = p.12 '250'); gate type / leaves printed nowhere", f"T-400 summary / T-361 (MERGED) {lid}",
                 "fence p.12")
    if c in ("EXT.FENCE.WALL", "EXT.FENCE.BLOCK"):
        run = el.split(":")[1]
        if run == "F-SEA":
            return E(r, el, "OWNER_DECISION", "sea-side element HELD by the owner (Q-63 C: material, height, structure, "
                     "gate); the 2.65 is drawn, not printed" + ("; block net with the plane" if c.endswith("BLOCK")
                                                                   else "; 6.36 m2 comparison only"),
                     f"T-400 summary (MERGED) {lid}", "P7757 GF plan sea side", owner_ref="Q-63 C")
        if run == "F-LOWER":
            return E(r, el, "PRINTED_VALUE_GAP", "passage closure 1.200 m: no top printed (partly under the GF roof "
                     "+5.50; T-361 E-02 stop-end HELD)" + ("; block net with the plane" if c.endswith("BLOCK") else ""),
                     f"T-400 summary (MERGED) {lid}", "fence p.12; P7757 GF plan passage")
        return E(r, el, "PRINTED_VALUE_GAP", f"{run} block net: the boundary columns (count not printed, M4) and the "
                 "lower 0.50 band are not separated from the block plane on any sheet; AT_MOST the run's plane "
                 f"(T-400 beside)", f"T-400 summary / T-396 ledger (MERGED) {lid}", "fence p.12 elevation / section")
    if c == "EXT.FLOOR.OUTDOOR":
        return E(r, el, "OWNER_OPEN", "covered porch / pool deck finish not decided: owner item OD-1 (interlock like "
                 "the court, or ceramic like house side areas) is OPEN; the area is DRAWING-CONFIRMED beside, the line "
                 "is an option bound never summed (T-495 / T-511)", f"OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 OD-1; T-511 "
                 f"census (MERGED) {lid}", "P7757 GF plan court", owner_ref="OD-1")
    if c == "EXT.POOL.WATER_FACE":
        return E(r, el, "DESIGNER_ITEM", "pool water-face finish not specified (no sheet, no Urban rule); bound "
                 "21.308727 m2 beside (floor 8.578838 + perimeter 11.069469 x 1.15)", f"T-343 report (MERGED bb772f51) "
                 f"{lid}", "ST p.7 pool; no finishes schedule", designer_ref="D-62")
    raise R.RuleError(f"{lid}: no resolver for {c}")


def assemble(entries, t636):
    held = {r["line_id"] for r in t636["per_line"] if r["class"] == "HELD"}
    c = R.census_counts(entries, held)
    before = {}
    for e in entries:
        k = f"{e['group']}|{e['unit']}"
        before[k] = before.get(k, 0) + 1
    return {"schema": SCHEMA, "rule": RULE, "task": "T-648", "inputs": {p: _sha(p) for p in PINS},
            "scope": "F-T636-1 finishes share (B2 2, B3 65, B4 10, B6 14, B7 44, B8 48) + B13 lines T-646 did not "
                     "class (15)",
            "counts": c,
            "census_per_trade_unit": {k: {"held_lines": v, "no_cause_before": v, "no_cause_after": 0}
                                      for k, v in sorted(before.items())},
            "fix_rows": [{"line_id": e["line_id"], **e["fix"]} for e in entries if e.get("fix")],
            "lines": entries}


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def render_md(b):
    c = b["counts"]
    out = ["# T-648 finishes HELD-line cause census (generated; do not edit)", "",
           f"Rule {b['rule']}; lines {c['lines']}; by class {c['by_class']}; fix rows {c['fix_rows']} (not wired).", "",
           "Census per trade and unit: HELD lines with no committed cause before -> after: " +
           ", ".join(f"{k} {v['no_cause_before']} -> {v['no_cause_after']}" for k, v in
                     b["census_per_trade_unit"].items()), "",
           "| line | code | unit | element | bound | class | ref | cause | source |", "|---|---|---|---|---|---|---|---|---|"]
    for e in b["lines"]:
        ref = e.get("owner_ref") or e.get("designer_ref") or e.get("depends_on") or ""
        bnd = "blank" if e["held_low"] is None and e["held_high"] is None else f"{e['held_low']} .. {e['held_high']}"
        out.append(f"| {e['line_id']} | {e['item_code']} | {e['unit']} | {e['element_id'][:60]} | {bnd} | {e['class']} "
                   f"| {ref} | {e['cause'][:160]} | {e['source'][:90]} |")
    if b["fix_rows"]:
        out += ["", "Fix rows (DRAWING-CONFIRMED, not wired):"]
        for f in b["fix_rows"]:
            out.append(f"- {f['line_id']}: {f['value']} {f['unit']} = " + " x ".join(f"{k} {v[0]}" for k, v in
                                                                                      f["terms"].items()) +
                       f" ({f['basis']})")
    return "\n".join(out) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b


if __name__ == "__main__":
    print(dumps(build())[:3000])
