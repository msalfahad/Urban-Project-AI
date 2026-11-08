"""T-640 development-villa build (research, unwired): the 72 HELD-blank B4 (m2) + B5 (m2) lines of the 10 Nov trial
BOQ dry run (T-630, candidate ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V15 overlay) classed one by one under R-T640-1
(t640_rules.py), with a fix row wherever a merged, Checker-verified ledger gives the area or a bound.

Rebuild (wrapper only): `URBAN_T640_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-640 tests/t640/test_t640.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-640 tests/t640`.

Reads only merged repository files (sha256-pinned below). Writes out/HOLD_CENSUS_T640.json and .md. No coordinate, no
drawing text, no client name. No candidate, released (V2.9 + route G), rule / knowledge version or registry file is
touched; the fix rows are proposals for the wiring manifest (lane I), not applied here."""
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
import t640_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T640_FINISH_HOLD_CENSUS_V1", "R-T640-1"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
V8 = "research/agents_t569/WIRING_MANIFEST_V8.json"
T173 = "research/agents_t173/SHAFT_T173.json"
T573 = "research/agents_t573/out/T573_CEILING_RECONCILE.json"
T622 = "research/agents_t622/out/WALL_TILE_REMEASURE_T622.json"
T313 = "research/agents_t313/REVEAL_LEDGER_T313.csv"
PINS = {T630: "e5dde7867c8fe6ad", INDEX: "fed5141ea31bfdd9", V8: "c71ecdc0eb11cba4", T173: "73603066376671fe",
        T573: "447804a48e21142e", T622: "9750dad42874b721", T313: "2cfa42112aa470c8"}
OUT_JSON = HERE / "out" / "HOLD_CENSUS_T640.json"
OUT_MD = HERE / "out" / "HOLD_CENSUS_T640.md"
SCOPE = (("B4", "m2"), ("B5", "m2"))
EXPECTED = {"FIN.PAINT": 33, "FIN.PLASTER": 10, "FIN.WALL.TILE": 6, "ARCH.WINDOW_REVEAL": 8, "ARCH.FACADE": 4,
            "FIN.EXT.FINISH": 3, "FIN.CEILING": 5, "FIN.CEILING.BULKHEAD": 1, "FIN.DOME.SOFFIT": 2}
BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}

# ---- static evidence (cause texts are summaries of the cited merged ledgers / owner answers) --------------------------
# wet rooms of the GF annex / stair core: candidate room id -> (T-622 held row, statement name, cause)
WET_HELD = {
    "GF-R8496F0": (47, "GF-02 wash by the dewaneya", "annex"),
    "GF-RB62B55": (48, "GF-03 W.C. by the dewaneya", "annex"),
    "GF-RFAD3C4": (49, "GF-05 driver W.C.", "annex"),
    "GF-RA3AD49": (50, "GF-06 kitchen", "annex"),
    "GF-RDF7D28": (51, "GF-10 W.C. 175 x 135 by the stair", "core"),
    "GF-RD36087": (52, "GF-11 basin space 110 x 135", "core"),
}
ANNEX_CAUSE = ("annex height: +4.30 is a roof mark, not a proven slab top (owner Q-54 B HOLD; D-06 / D-17 roof build-up; "
               "D-39 roof datum); the plaster runs to the slab underside (Q-72), the tile top / paint height follow the "
               "same unproven datum")
CORE_CAUSE = ("room floor level +0.30 or +1.00 not drawn (T-088; T-173 C-SH-2: the floor under the stair-core rooms "
              "has no edge or level); both the plaster band (floor -> 1F slab soffit, Q-72) and the tile band start "
              "from it")
SRC_WET = ["research/agents_t622/out/WALL_TILE_REMEASURE_T622.json held_rows (T-622 MERGED)",
           "OWNER_QUESTIONS_ANSWERED Q-54 B", "DESIGNER_CLARIFICATIONS D-17 / D-39",
           "research/agents_t292/CANDIDATE_V3015_WALL_FINISH_LINES.json rfi WALL_FINISH_HEIGHT_NOT_ESTABLISHED"]

STATIC = {
    # annex dry-room paint (V3.0.21 record formula text)
    "L-cdf7f5cd2789b67004f1": ("B_HELD", ANNEX_CAUSE + "; owner 3.15 m shown beside as OWNER MANUAL METHOD - PROVISIONAL",
                               ["research/agents_t335/CANDIDATE_V3021_T335.json (GF_01 paint formula)",
                                "OWNER_QUESTIONS_ANSWERED Q-54 B"]),
    "L-d7d6d2f765489a95c408": ("B_HELD", ANNEX_CAUSE + "; owner 3.15 m shown beside as OWNER MANUAL METHOD - PROVISIONAL",
                               ["research/agents_t335/CANDIDATE_V3021_T335.json (GF_04 paint formula)",
                                "OWNER_QUESTIONS_ANSWERED Q-54 B"]),
    # door / arch / gate reveals through the wall still HELD by name (T-313 r2, MERGED 5f2bf0d5)
    "A-GF-01": ("B_HELD", "arch A-GF-01 through-wall reveal: candidate 2 x 0.150 x 2.200 + 0.150 x developed 1.223795 = "
                          "0.843569 m2 is SOURCE-SUPPORTED PENDING INDEPENDENT CHECK; the arch spring / rise is not "
                          "printed (D-45), so the outline (R-T326-2) is not settled",
                ["research/agents_t313/REVEAL_LEDGER_T313.csv A-GF-01", "DESIGNER_CLARIFICATIONS D-45"]),
    "A-1F-01": ("B_HELD", "arch A-1F-01 is drawn on no plan, elevation or section (T-313: UNKNOWN): width, height and "
                          "wall thickness not established",
                ["research/agents_t313/T-313_OPENING_REVEAL_LEDGER.md s.HELD"]),
    "D-GF-15": ("B_HELD", "gate D-GF-15: width / wall thickness not established (T-313 UNRESOLVED; D-53 entrance family)",
                ["research/agents_t313/REVEAL_LEDGER_T313.csv D-GF-15", "DESIGNER_CLARIFICATIONS D-53"]),
    # window reveals
    "W02_OUT": ("B_HELD", "W02 outside jambs: the window count (one drawn vs two rendered with a pier) is open (D-53), "
                          "so the jamb count and the head run are not settled; head 0.080 x 6.330 = 0.5064 m2 holds only "
                          "for the one-window reading",
                ["research/agents_t313/REVEAL_LEDGER_T313.csv W02 OUT", "DESIGNER_CLARIFICATIONS D-53",
                 "research/agents_t627/T-627_OPENING_AREA_EVIDENCE.md s.2 (W02 waits on D-53)"]),
    "W03": ("C_PENDING", "W03 curved floor glazing: the frame position in the curved wall (reveal depth per side) was "
                         "never measured (T-313 UNRESOLVED 'depth not measured'; T-197 left the GF curved glazing band "
                         "unrun); to read by handle on the architectural DXF (frame band vs inner / outer wall arcs), "
                         "developed along the arc (T-302 method); heights are printed (D-45 list)",
            ["research/agents_t313/REVEAL_LEDGER_T313.csv W03", "research/agents_t197/T-197_CURVED_GEOMETRY.md"]),
    "W17": ("C_PENDING", "W17 curved 1F window: opening 3.29 x 3.00 is owner Q-76 A, but the frame position in the 0.20 m "
                         "curved wall (IN / OUT reveal depth) is not measured (T-313: curved, T-302 developed hole; "
                         "T-302 s.78 'jamb reveals 0.20 deep, not measured'). Lead for the read: T-302 s.1 puts the glass line ON the "
                         "room face BD2 (r 2.135), which would make IN = NONE (a face that does not exist: EXCLUDED with "
                         "evidence, never 0) and OUT = the full radial 0.20 between jambs BD9 / BD7 under the arched head "
                         "(2.168 / 2.219 at the jambs, 3.00 crown); to confirm by handle on the architectural DXF (frame "
                         "lines vs both arcs) before any figure",
            ["research/agents_t313/T-313_OPENING_REVEAL_LEDGER.md", "research/agents_t302/T-302_W17_ARCHED_HOLE.md",
             "OWNER_QUESTIONS_ANSWERED Q-76 A"]),
    # facade family
    "FACADE": ("A_CARRIED", "register line beside the work line (REGISTER_BESIDE_WORK, F-T630-3 pattern): the storey's "
                            "facade m2 is the same face set as FIN.EXT.FINISH of that storey, measured once in the merged "
                            "T-305 / T-337 / T-348 r2 / T-567 face ledgers and wired as face rows by T-314 (QUEUED, owner "
                            "Gate B order item 2); an own figure here would count the faces twice",
               ["research/agents_t567/T-567_EXTERNAL_PLASTER_RECONCILE.md s.1 / s.3",
                "BOARD T-314 row", "research/agents_t630 F-T630-3"]),
    "PLINTH": ("B_HELD", "plinth below the lowest F.F.L.: the external ground level is not printed (no site / external "
                         "works plan, D-62); his planes start at +1.00 (owner Q-07 B, T-567 RULE_DIFFERENCE -31.5245 m2); "
                         "the plinth faces stay their own line until the ground level is issued",
               ["research/agents_t337/CANDIDATE_V3022_T337.json PLINTH_NOT_MEASURED",
                "research/agents_t567/T-567_EXTERNAL_PLASTER_RECONCILE.md", "DESIGNER_CLARIFICATIONS D-62"]),
    "EXT": ("A_CARRIED", "the storey's exterior render / Sigma area is measured face by face in the merged ledgers "
                         "(T-305: GF 387.285 .. 420.770 HELD on W02 / D-GF-07, 1F 234.526, 2F 132.205 in line; restated "
                         "by T-337 / T-348 r2 / T-567: gross 1,166.4517846 .. 1,185.4079770 m2 incl. parapets) and is "
                         "wired by T-314 (QUEUED, owner Gate B order item 2), which REPLACES this blank line by face "
                         "rows; a T-640 row on the same line would collide (overlay R1)",
            ["BOARD T-314 row", "research/agents_t305/T-305_EXTERIOR_PLASTER_SIGMA_LEDGER.md",
             "research/agents_t567/T-567_EXTERNAL_PLASTER_RECONCILE.md"]),
    "DOME": ("B_HELD", "dome intrados finish: the dome opening / closure (glazing at slab, at drum top or a closed "
                       "ceiling) is a designer item (D-20, DCR-4; owner Q-29 / Q-44); T-573 keeps both lines HELD "
                       "unbounded",
             ["research/agents_t573/out/T573_CEILING_RECONCILE.json DOME intrados", "DESIGNER_CLARIFICATIONS D-20"]),
}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def _json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def scope_lines():
    """the HELD-blank B4 / B5 m2 lines of the T-630 dry run, with element ids from the V3.0.57 index or the overlay."""
    pl = _json(T630)["per_line"]
    ix = {l["line_id"]: l for l in _json(INDEX)["lines"]}
    out = []
    for l in pl:
        if (l["group"], l["unit"]) in SCOPE and l["class"] == "HELD" and l["held_low"] is None \
                and l["held_high"] is None:
            lid = l["line_id"]
            el = ix[lid]["element_id"] if lid in ix else lid.split(":", 2)[2]
            out.append({"line_id": lid, "item_code": l["item_code"], "family": l["family"], "group": l["group"],
                        "element_id": el, "origin": "V3.0.57 index" if lid in ix else "overlay ADD (V15)"})
    return sorted(out, key=lambda x: (x["group"], x["item_code"], x["element_id"]))


def return_paint():
    rp = _json(V8)["return_paint"]
    out = {}
    for grp in ("valued", "held"):
        for f in rp[grp]:
            out["NEW:FIN.PAINT:" + f["face_id"]] = {"bound": f["paint_row"]["bound_beside_m2"],
                                                     "plaster_line": f["plaster_line"],
                                                     "plaster_class": f["plaster_class"], "group": grp}
    return out, rp["rule_text"]


def shaft_2f():
    """T-173 storey band above +9.70 (both cases) with the Checker's D-T173-1 corrections (T-173 verdict 2026-10-22):
    roof panel over the shaft prints T 18 (soffit +13.72, not +13.74): W -0.104, E -0.104, N up to -0.05 m2; roof B3
    downstand touches the top of W and E, about 0.04 m2 each. Low end takes every correction at its largest, high end
    only the certain W / E ones."""
    summ = _json(T173)["summary"]
    band = {}
    for s in summ:
        top = next(b for b in s["storeys"] if b["z_from"] == 9.7)
        band[(s["case"], s["finish"])] = top
    cw, ce, cn, b3 = D("0.104"), D("0.104"), D("0.05"), D("0.08")
    out = {}
    for fin in ("plaster", "paint"):
        lo_raw, hi_raw = D(band[("LO", fin)]["net_lo"]), D(band[("HI", fin)]["net_hi"])
        lo, hi = lo_raw - cw - ce - cn - b3, hi_raw - cw - ce
        out[fin] = {"low": lo, "high": hi,
                    "basis": f"T-173 band above +9.70: LO-case net_lo {S(lo_raw)} - D-T173-1 (W 0.104 + E 0.104 + "
                             f"N 0.05) - B3 contacts 0.08 = {S(lo)}; HI-case net_hi {S(hi_raw)} - (W 0.104 + E 0.104) "
                             f"= {S(hi)} m2"}
    return out


def ceiling_bounds():
    """T-573 (MERGED 587e47f9) bounds by line id, read from its JSON (board groups and classes)."""
    d = _json(T573)
    found = {}

    def walk(o):
        if isinstance(o, dict):
            if "lines" in o and "causes" in o:
                for c in o["causes"]:
                    if c.get("verdict") == "HELD":
                        found.setdefault(o["id"], []).append((c["label"], c.get("bound"), c.get("source")))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    return found


def build():
    pins()
    lines = scope_lines()
    counts = {}
    for l in lines:
        counts[l["item_code"]] = counts.get(l["item_code"], 0) + 1
    if counts != EXPECTED or len(lines) != 72:
        raise R.RuleError(f"scope differs from the T-640 row (72 = paint 33, plaster 10, ...): {counts}")
    rp, rp_rule = return_paint()
    shaft = shaft_2f()
    cb = ceiling_bounds()
    t622 = {r["row"]: r for r in _json(T622)["held_rows"]}
    t313 = list(csv.DictReader((ROOT / T313).open(encoding="utf-8")))
    a_gf01 = [r for r in t313 if r["opening"] == "A-GF-01"]
    entries = []
    for l in lines:
        lid, code, el = l["line_id"], l["item_code"], l["element_id"]
        e = dict(l)
        room = el.split(":")[0]
        if code in ("FIN.WALL.TILE", "FIN.PLASTER") and room in WET_HELD:
            row, name, kind = WET_HELD[room]
            assert t622[row]["status"].startswith("HELD")
            e.update({"class": "B_HELD", "cause": (ANNEX_CAUSE if kind == "annex" else CORE_CAUSE),
                      "room": name, "t622_waits_on": t622[row]["waits_on"], "sources": SRC_WET,
                      "status": "HELD"})
        elif code == "FIN.PAINT" and lid in rp:
            r = rp[lid]
            face = el
            if r["bound"] is None:
                key = next(k for k in ("A-GF-01", "A-1F-01", "D-GF-15") if k in face)
                cls, cause, src = STATIC[key]
                e.update({"class": cls, "cause": "paint on a plastered return whose plaster is itself HELD blank: "
                          + cause, "sources": src + [V8 + " return_paint.held"], "status": "HELD"})
            else:
                lo, hi = D(r["bound"][0]), D(r["bound"][1])
                e.update({"class": "A_BOUND", "status": "HELD",
                          "cause": "painted part = return face - frame-covered depth; frame detail not printed "
                                   "(T-561 ENGINE_OMISSION, R-T569-1); bound 0 .. the plaster m2 of the same face",
                          "sources": [V8 + " return_paint (T-569 MERGED 5aee8f5a; T-561 Checker 13:55Z)",
                                      f"plaster line {r['plaster_line']} ({r['plaster_class']})"],
                          "fix": {"id": None, "kind": "SET", "before": dict(BLANK),
                                  "after": {"class": "HELD", "measured_net": None, "held_low": S(lo),
                                            "held_high": S(hi)},
                                  "basis": f"R-T569-1: 0 .. plaster face {S(hi)} m2 ({r['plaster_line']}); the bound "
                                           f"moves from 'beside' into the line state; no low end is released (0)",
                                  "rule_text": rp_rule}})
        elif code == "FIN.PLASTER" and "REVEAL" in el:
            key = next(k for k in ("A-GF-01", "A-1F-01", "D-GF-15") if k in el)
            cls, cause, src = STATIC[key]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD"})
            if key == "A-GF-01":
                e["candidate_beside_m2"] = S(sum((D(r["basis"].split("=")[1].split()[0]) for r in a_gf01),
                                                 Decimal(0)))
        elif el.startswith("HL:WALL_FINISH:ST_2F:"):
            fin = "plaster" if code == "FIN.PLASTER" else "paint"
            sh = shaft[fin]
            e.update({"class": "A_BOUND", "status": "HELD",
                      "cause": "2F stair-shaft band above +9.70: held only for the Checker's T-173 corrections "
                               "(D-T173-1 roof panel T 18, roof B3 downstand contact), both now applied; the band keeps "
                               "its held items (W27 head / sill, B20 / B23 ends, roof build-up b 0 .. 0.10) as the range, "
                               "like the ST_GF / ST_1F lines of the same shaft",
                      "sources": [T173 + " summary (T-173 MERGED 8b4d2c83)",
                                  "BOARD_ARCHIVE T-173 verdict: D-T173-1 and B3 contacts (Checker own re-measure)",
                                  "LINE_INDEX_V3_0_57 ST_GF / ST_1F lines HELD 48.52 .. 62.01 / 42.48 .. 47.67"],
                      "fix": {"id": None, "kind": "SET", "before": dict(BLANK),
                              "after": {"class": "HELD", "measured_net": None, "held_low": S(q(sh["low"])),
                                        "held_high": S(q(sh["high"]))},
                              "basis": sh["basis"],
                              "low_end_note": "low end > 0: releasable with a HELD companion; kept bounded here "
                                              "because the sibling ST_GF / ST_1F bands are bounded HELD (one "
                                              "convention per shaft; Lead / Checker to rule for all three)"}})
        elif el.startswith("HL:WALL_FINISH:"):
            cls, cause, src = STATIC[lid]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD"})
        elif code == "ARCH.WINDOW_REVEAL":
            key = "W02_OUT" if "W02" in el else ("W03" if "W03" in el else "W17")
            if "COP-001" in el:
                key = "W17"
            cls, cause, src = STATIC[key]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD"})
        elif code == "ARCH.FACADE":
            key = "PLINTH" if "plinth" in el else "FACADE"
            cls, cause, src = STATIC[key]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD"})
            if cls == "A_CARRIED":
                e["carrier"] = "FIN.EXT.FINISH " + el.split("-")[0] + " face rows (T-314)"
        elif code == "FIN.EXT.FINISH":
            cls, cause, src = STATIC["EXT"]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD",
                      "carrier": "T-314 integration package (face rows keyed to the T-305 / T-337 ledger)"})
        elif code == "FIN.DOME.SOFFIT":
            cls, cause, src = STATIC["DOME"]
            e.update({"class": cls, "cause": cause, "sources": src, "status": "HELD"})
        elif code in ("FIN.CEILING", "FIN.CEILING.BULKHEAD"):
            e.update(ceiling_entry(lid, el, cb))
        else:
            raise R.RuleError(f"{lid} {code} {el}: no class rule")
        entries.append(e)
    n = 0
    for e in entries:
        if e.get("fix"):
            n += 1
            e["fix"]["id"] = f"FR-T640-{n}"
        R.check_entry(e)
    return assemble(entries)


def ceiling_entry(lid, el, cb):
    src573 = T573 + " (T-573 MERGED 587e47f9)"

    def bound(gid, label_part):
        for label, b, source in cb[gid]:
            if label_part in label:
                return label, b, source
        raise R.RuleError(f"T-573 bound {gid!r} / {label_part!r} not found")

    if el in ("1F-R78C367:ceiling", "1F-R78C367:ceiling over void"):
        return {"class": "A_CARRIED", "status": "HELD",
                "cause": "blank PARENT of the 1F living decor group line L-43bf1f869e1588f1d3bd (FIN.CEILING "
                         "1F-R78C367:ceiling#DECOR_GROUP, RELEASED 51.0496 m2): the normal / double-height split is not "
                         "drawn, so the room's board is carried whole by the group line (R-T284-1, never pro rata); a "
                         "figure here would count it twice",
                "carrier": "L-43bf1f869e1588f1d3bd (RELEASED 51.0496 m2)",
                "sources": [src573 + " board '1F living (group line + 2 blank parents)'", INDEX],
                "fix": {"id": None, "kind": "RETIRE_CARRIED", "before": dict(BLANK), "after": None,
                        "basis": "the quantity is in L-43bf1f869e1588f1d3bd; the blank parent leaves the BOQ line "
                                 "count (proposal: RETIRE with the carrier named, Checker to rule; never 0)"}}
    if el == "GF-RFD4E1D:west-strip:ceiling":
        label, b, source = bound("GF reception + dining + entrance (incl. pantry, south dining piece)", "west strip")
        basis = "west strip OP-003 3.80 x 0.20 = 0.760 m2 drawn; no ceiling reading (finish / level) for the strip"
    elif el == "GF-RFD4E1D:bulkhead":
        label, b, source = bound("BULKHEAD vertical faces (all rooms)", "GF-RFD4E1D")
        basis = "free beam edge 6.5428 m x owner-method drop 0.15 = 0.98142 m2 high end; drop depth not decided (T-431)"
    elif el == "2F-R4D1B62:stairwell ceiling":
        label, b, source = bound("2F stair hall lobby (his 'corridor')", "stair box top")
        basis = "stair box top under the 2F roof 12.9742 m2 drawn (T-271 / T-283 r3); finish at the box top not " \
                "printed (Q-72 / O-P8-02)"
    elif el == "GF-R31F8AE:stairwell ceiling":
        label, b, source = bound("GF service stair room ST-01 (stairwell line HELD blank)", "stair top under the slab")
        b = ["0", "1.750"]
        basis = "stair top under the 1F slab 1.750 m2 (T-283 r3, T-573 label); the flight soffit pieces are counted " \
                "once in the STAIR soffit table (T-281), never in this line, so the open high of T-573 closes at 1.750"
    else:
        raise R.RuleError(f"{lid} {el}: no ceiling rule")
    lo, hi = D(b[0]), D(b[1])
    return {"class": "A_BOUND", "status": "HELD",
            "cause": f"{label} (finish / level not printed: O-P8-02 every ceiling line is PROVISIONAL by design)",
            "sources": [src573, f"T-573 source {source}"],
            "fix": {"id": None, "kind": "SET", "before": dict(BLANK),
                    "after": {"class": "HELD", "measured_net": None, "held_low": S(lo), "held_high": S(hi)},
                    "basis": basis}}


def assemble(entries):
    c = R.census_counts(entries)
    fam = {}
    for e in entries:
        k = (e["family"], e["item_code"])
        f = fam.setdefault(k, {"lines": 0, "fix_rows": 0, "classes": {}, "bound_low": Decimal(0),
                               "bound_high": Decimal(0)})
        f["lines"] += 1
        f["classes"][e["class"]] = f["classes"].get(e["class"], 0) + 1
        fx = e.get("fix")
        if fx and fx["kind"] == "SET":
            f["fix_rows"] += 1
            f["bound_low"] += D(fx["after"]["held_low"])
            f["bound_high"] += D(fx["after"]["held_high"])
        elif fx:
            f["fix_rows"] += 1
    fam_rows = [{"family": k[0], "item_code": k[1], "lines": v["lines"], "fix_rows": v["fix_rows"],
                 "classes": dict(sorted(v["classes"].items())), "fix_bound_m2": [S(v["bound_low"]),
                                                                                 S(v["bound_high"])]}
                for k, v in sorted(fam.items())]
    lo = sum((D(e["fix"]["after"]["held_low"]) for e in entries if e.get("fix") and e["fix"]["kind"] == "SET"),
             Decimal(0))
    hi = sum((D(e["fix"]["after"]["held_high"]) for e in entries if e.get("fix") and e["fix"]["kind"] == "SET"),
             Decimal(0))
    return {"schema": SCHEMA, "rule": RULE, "task": "T-640",
            "candidate": "ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V15 overlay (T-630 dry run, 5,141 lines)",
            "pins": PINS, "scope": "B4 m2 + B5 m2 HELD-blank lines (T-630 per_line: class HELD, no bound)",
            "counts": c, "families": fam_rows,
            "fix_bound_total_m2": [S(lo), S(hi)],
            "not_claimed": "development villa; nothing wired, released or verified; fix rows are proposals for the "
                           "lane I manifest; V3.0.58 NOT RELEASED; V2.9 + route G unchanged",
            "lines": entries}


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def render_md(b):
    c = b["counts"]
    out = [f"# T-640 finishes hold census (R-T640-1): {c['lines']} HELD-blank B4 / B5 m2 lines", "",
           f"Candidate {b['candidate']}. {b['not_claimed']}.", "",
           f"Classes: {', '.join(f'{k} {v}' for k, v in c['by_class'].items())}. Fix rows {c['fix_rows']} "
           f"(lines leaving HELD blank); {c['stay_held_blank']} stay HELD blank with a named cause. Fix-row bounds "
           f"total {b['fix_bound_total_m2'][0]} .. {b['fix_bound_total_m2'][1]} m2 (HELD, not released).", "",
           "| Family | Item | Lines | Fix rows | Classes | Fix bound m2 |", "|---|---|---|---|---|---|"]
    for f in b["families"]:
        out.append(f"| {f['family']} | {f['item_code']} | {f['lines']} | {f['fix_rows']} | "
                   f"{', '.join(f'{k} {v}' for k, v in f['classes'].items())} | {f['fix_bound_m2'][0]} .. "
                   f"{f['fix_bound_m2'][1]} |")
    out += ["", "| Line | Item | Element | Class | Fix | Cause |", "|---|---|---|---|---|---|"]
    for e in b["lines"]:
        fx = e.get("fix")
        fs = "-" if not fx else (f"{fx['id']} RETIRE (carried)" if fx["kind"] != "SET" else
                                 f"{fx['id']} HELD {fx['after']['held_low']} .. {fx['after']['held_high']}")
        out.append(f"| {e['line_id']} | {e['item_code']} | {e['element_id']} | {e['class']} | {fs} | "
                   f"{e['cause'][:160]} |")
    return "\n".join(out) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b
