"""T-569 WIRING MANIFEST V8: the T-564 manifest (V7, pinned by sha256) extended by EVERY piece merged after it up to the
pinned V8 base, on the candidate of record ARCH_TAKEOFF_V3.0.58, PLUS the three fix rows the Checker asked for and the
two integration gaps the Checker CONFIRMED on the newest merges. Research / integration preparation only (lane I,
non-candidate): nothing here writes a candidate, released, rule, knowledge or registry file; nothing is wired.

Coverage by R-T549-1 (V4's check_coverage, reused): range (V7 base 33a5833f, V8 base 540bc99c] on the first-parent
line; every 'Merge agents/task-T-<n>' in it is a wiring source with that merge commit or a declared NO_WIRING piece.

Fix rows (each from the candidate's own line records or a merged piece's committed output; no drawing read here):
  1. RETURN_PAINT_FACES (T-561 ENGINE_OMISSION, register PLASTERED RETURN FACE, R-T569-1): one FIN.PAINT row per
     plastered return FACE ID (the plaster line's element id), HELD blank, bound beside 0 .. the plaster m2 of the
     same face, never 0; the valued faces must re-add to T-561's 23.070 m2 by count and by sum; the blank plaster
     returns stay HELD by name (their own HELD bound, or none). Pairing check: after the wiring every plastered return
     has exactly one paint row (an unpaired return is refused).
  2. DRESSING_FLOOR_CLASS (F-C-T564-1): the V7 dressing floor row keeps its 2.970 m2 and its item code; its finish
     class becomes A08 ESTIMATED = the floor finish of the adjacent bed room (RFI RE-REVIEW 2026-11-02), read from the
     neighbour's own released floor line, with the source note; ESTIMATED is never VERIFIED (refused).
  3. PIER_RETURNS_EXT (T-567 R-T567-6): the SW pier return faces go to the FIN.EXT.FINISH ledger of the storey's line
     (HELD blank until T-314); no internal line takes them (checked).
  4. W17_Q76A (F-C-T568-1, Checker 17:57 CONFIRMED integration gap): the 1F ARCH.WINDOW HELD line 9.870 .. 11.515 m2
     is W17 alone; owner Q-76 A fixes 3.29 x 3.00 = 9.870 m2: the HELD line retires, the 1F settled line takes it.
  5. REBAR_OMISSION (T-560 ENGINE_OMISSION, Checker 17:57 CONFIRMED): one HELD-blank STR.REBAR row tied to each live
     dome shell / dome ring / lift-pit wall concrete line that has no rebar line (never 0).
"""

from __future__ import annotations

import csv
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


M7 = _load("research/agents_t564/manifest_v7.py", "manifest_v7_t569")              # read only
M6, M5, M4, M2, M1 = M7.M6, M7.M5, M7.M4, M7.M2, M7.M1
ManifestError = M7.ManifestError
sha256 = M1.sha256

SCHEMA = "URBAN_T569_WIRING_MANIFEST_V8"
RULE = "R-T569-1"
RULE_TEXT = ("R-T569-1 (one face, two layers): a plastered return face carries a B6 paint row on the SAME face id; "
             "while the frame-covered depth is not printed the paint row is HELD, bound beside 0 .. the plaster m2 "
             "of that face (never 0, never folded into a released paint line); a blank plaster return stays HELD "
             "by name; after wiring, every plastered return has exactly one paint row.")
OUT_JSON = ROOT / "research/agents_t569/WIRING_MANIFEST_V8.json"
V7_JSON = M7.OUT_JSON
V7_PIN = "72d2714cb46d190890e591a03b2db9531bcd5d9877a86161b25f80a68c2b8ed0"     # the merged V7 (d66df952)
T561 = M7.T561
T567_FACES = ROOT / "research/agents_t567/out/FACES_T567.csv"
T567_JSON = ROOT / "research/agents_t567/out/T567_EXT_RECONCILE.json"
T292_LEDGER = ROOT / "research/agents_t292/FACE_TO_LINE_LEDGER_T292.csv"

V7_BASE = M7.V7_BASE          # 33a5833f Merge agents/task-T-561
V8_BASE = "540bc99c"          # Merge agents/task-T-568 (the newest merge when T-569 was claimed)

NEW_PIECES = {
    "T-564": {"merge": "d66df952", "gate": "A", "rules": ["R-T564-1"],
              "verdict": "Verifier 2026-11-06 15:58Z GATE A PASS: V7 + census R-T564-1; F-C-T564-1 dressing finish "
                         "class must carry A08 ESTIMATED with its source (no quantity change)"},
    "T-565": {"merge": "4af6a9f2", "gate": "A", "rules": ["R-T565-1", "R-T565-2", "R-T565-3", "R-T565-4"],
              "verdict": "Verifier 2026-11-06 15:58Z GATE A PASS: earthworks scope ENGINE_RIGHT; quantity "
                         "UNRESOLVED / NOT_COMPARABLE (no row of his); B1-05 AGREE_ABSENT"},
    "T-567": {"merge": "8aba0d81", "gate": "A", "rules": ["R-T567-6"],
              "verdict": "Verifier 2026-11-06 15:58Z GATE A PASS: SW pier returns 0.536522 m length-confirmed "
                         "(2.2533924 m2); FIN.EXT.FINISH stays HELD blank (T-314)"},
    "T-560": {"merge": "8ba76061", "gate": "A", "rules": ["R-T560-1", "R-T560-2", "R-T560-3", "R-T560-4",
                                                          "R-T560-5"],
              "verdict": "Verifier 2026-11-06 17:57Z GATE A PASS: his 44.19 t TYPED_LUMP -> RULE_DIFFERENCE; dome + "
                         "lift pit wall rebar ENGINE_OMISSION CONFIRMED -> HELD-blank STR.REBAR lines tied to the "
                         "concrete lines (never 0)"},
    "T-570": {"merge": "cc6da4a5", "gate": "A", "rules": ["R-T570-1"],
              "verdict": "Verifier 2026-11-06 17:57Z GATE A PASS: statement adapters V4; F-C-T570-1 the 23.07 m2 "
                         "return-paint row must be restated HELD <= 23.07 once T-569's paint lines exist"},
    "T-568": {"merge": "540bc99c", "gate": "A", "rules": ["R-T568-1"],
              "verdict": "Verifier 2026-11-06 17:57Z GATE A PASS: door counts ENGINE_RIGHT; F-C-T568-1 CONFIRMED "
                         "integration gap: W17 still HELD 9.870 .. 11.515 although Q-76 A fixes 9.870 m2"},
}
NO_WIRING = {
    "T-565": "reconciliation to cause (B1 earthworks vs the freelancer, NO_ROW): moves no line; ENGINE_WRONG none",
    "T-570": "statement adapters V4 (milestone text): moves no candidate line; its F-C-T570-1 restatement is carried "
             "in packages (PAINT_RETURN_FACES)",
}
WIRING_SOURCES = {"T-564": ["F-C-T564-1"], "T-567": ["R-T567-6"], "T-568": ["F-C-T568-1"],
                  "T-560": ["T-560 ENGINE_OMISSION (dome / lift pit rebar)"]}
PIECES = dict(M7.PIECES, **NEW_PIECES)

PAINT_RETURN_TOKENS = M7.PAINT_RETURN_TOKENS          # T-561's own selection (OPENING / REVEAL plaster lines)
T561_FACES = 26                                       # Checker 13:55: 26 valued returns
T561_M2 = Decimal("23.070")

# A08 (RFI RE-REVIEW 2026-11-02, board head): "the 2.970 m2 dressing area takes the adjacent master-bedroom floor
# finish (project pattern), labelled ESTIMATED". The neighbour is read from the candidate's own records: the arch
# A-1F-01 joining the bed room and the unlabelled space is on face 1F-W16 of room 1F-10 = space 1F-R0E919A (T-292
# ledger), and T-553 pairs the space with that room (his row 23 = 16.340 + 2.970 + 0.150, perimeter 21.40).
A08 = {"space": "1F-RFFE7AF", "neighbour": "1F-R0E919A", "via": "A-1F-01",
       "other_bed_rooms": ["1F-R3CFCFD"],
       "source": "RFI RE-REVIEW 2026-11-02 (board head, A08 ESTIMATED: adjacent master-bedroom floor finish, project "
                 "pattern; stream F applies it) + owner 2026-10-31 (area 2.970 m2 floor scope, no geometry fix)"}

PIER_KEY = "SW-PIER-RETURNS"
W17 = {"held_line": "L-0392d37452e98050dd1b", "settled_line": "L-ba28ba2da13f62445c9f", "width": "3.29",
       "height": "3.00", "band_height": "3.50",
       "source": "owner Q-76 A (2026-10-24 23:53): 3.29 x 3.00 = 9.870 m2, the 0.45 m band above is wall; width "
                 "Q-39 C (outer arc)"}
REBAR_HOSTS = ("DOME", "LIFT_PIT")
REBAR_CONC = ("STR.CONC.DOME", "STR.CONC.BEAM", "STR.CONC.LIFT")


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _d(x):
    return None if x is None else Decimal(str(x))


def _src(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def v7_manifest():
    if sha256(V7_JSON) != V7_PIN:
        raise ManifestError(f"PIN: {V7_JSON.name} sha256 {sha256(V7_JSON)[:8]} is not the pinned {V7_PIN[:8]}")
    return _json(V7_JSON)


def check_status(row):
    """an ESTIMATED / ASSUMED / HELD basis is never shown as VERIFIED (WORKFLOW_CONTROLS s.5)."""
    basis = str(row.get("basis", ""))
    st = str(row.get("evidence_status", ""))
    if any(k in basis for k in ("ESTIMATED", "ASSUMED", "HELD")) and "VERIFIED" in st.replace("NOT VERIFIED", ""):
        raise ManifestError(f"STATUS: {row.get('id')} rests on {basis} but is shown as {st}")
    return row


# ------------------------------------------------------------------------------------------------- 1 return paint
def _is_return(l, code):
    return l["item_code"] == code and any(k in l["element_id"] for k in PAINT_RETURN_TOKENS)


def return_faces(lines, faces_expected=None, m2_expected=None):
    """R-T569-1 on any line list: one HELD paint row per plastered return face id."""
    if any(_is_return(l, "FIN.PAINT") for l in lines):
        raise ManifestError("a FIN.PAINT return line exists: the omission is not on this candidate")
    pl = sorted((l for l in lines if _is_return(l, "FIN.PLASTER")), key=lambda l: l["element_id"])
    ids = [l["element_id"] for l in pl]
    if len(set(ids)) != len(ids):
        raise ManifestError("DOUBLE_FACE: a return face id carries two plaster lines")
    valued, held = [], []
    for l in pl:
        face = l["element_id"]
        row = {"face_id": face, "plaster_line": l["line_id"], "plaster_class": l["class"],
               "paint_row": {"item_code": "FIN.PAINT", "element_id": face + ":RETURN_PAINT", "class": "HELD",
                             "value": None, "unit": "m2"}}
        if l["class"] == "RELEASED" and l["measured_net"] is not None:
            hi = _d(l["measured_net"])
            if hi <= 0:
                raise ManifestError(f"{face}: plastered return {hi} m2 is not positive")
            row["plaster_m2"] = float(hi)
            row["paint_row"]["bound_beside_m2"] = [0.0, float(hi)]
            row["basis"] = "HELD (frame-covered depth not printed)"
            row["evidence_status"] = "HELD, upper bound = the plaster m2 of the same face"
            valued.append(row)
        else:
            hi = _d(l["held_high"])
            row["plaster_m2"] = None
            row["paint_row"]["bound_beside_m2"] = None if hi is None else [0.0, float(hi)]
            row["basis"] = "HELD (plaster return itself HELD)"
            row["evidence_status"] = ("HELD by name, bound = the plaster's own HELD high" if hi is not None else
                                      "HELD by name, no bound (plaster return blank)")
            held.append(row)
    tot = sum((Decimal(str(r["plaster_m2"])) for r in valued), Decimal(0))
    if faces_expected is not None and len(valued) != faces_expected:
        raise ManifestError(f"COUNT: {len(valued)} valued return faces, not the confirmed {faces_expected}")
    if m2_expected is not None and tot != m2_expected:
        raise ManifestError(f"SUM: valued return faces {tot} m2 are not the confirmed {m2_expected}")
    return {"valued": valued, "held": held, "valued_faces": len(valued), "valued_m2": float(tot),
            "bound_beside_total_m2": [0.0, float(tot)]}


def check_pairs(lines_after):
    """after the wiring: every plastered return face has exactly one paint row on the same face id."""
    paint = {}
    for l in lines_after:
        if _is_return(l, "FIN.PAINT"):
            paint.setdefault(l["element_id"], []).append(l)
    for l in lines_after:
        if _is_return(l, "FIN.PLASTER"):
            n = len(paint.get(l["element_id"] + ":RETURN_PAINT", []))
            if n != 1:
                raise ManifestError(f"UNPAIRED: {l['element_id']} carries plaster and {n} paint rows")
            p = paint[l["element_id"] + ":RETURN_PAINT"][0]
            if p["class"] != "HELD" or p.get("measured_net") not in (None,):
                raise ManifestError(f"{p['element_id']}: a return paint row is valued before the frame detail")
    return True


def return_paint(idx):
    t = _json(T561)
    r = t["internal"]["pairs"]["RETURN"]
    if Decimal(r["by_cause"]["HELD"]) != T561_M2:
        raise ManifestError("T-561 RETURN HELD is not 23.070")
    rf = return_faces(list(idx.values()), T561_FACES, T561_M2)
    out_ids = sorted(o["line_id"] for o in r["outside"])
    if sorted(h["plaster_line"] for h in rf["held"]) != out_ids:
        raise ManifestError("the HELD plaster returns are not T-561's 'outside' lines")
    # cross-trade: the after state is the candidate + the paint rows only; no other line moves
    after = list(idx.values()) + [dict(r_["paint_row"], line_id="NEW:" + r_["face_id"], held_low=None,
                                       held_high=None, measured_net=None, binding=None, unbound_records=[])
                                  for r_ in rf["valued"] + rf["held"]]
    check_pairs(after)
    for r_ in rf["valued"] + rf["held"]:
        check_status(r_)
    paint_rel = sum((_d(l["measured_net"]) for l in idx.values() if l["item_code"] == "FIN.PAINT" and
                     l["class"] == "RELEASED"), Decimal(0))
    return {"id": "RETURN_PAINT_FACES", "closes": "T-561 ENGINE_OMISSION (register PLASTERED RETURN FACE)",
            "rule": RULE, "rule_text": RULE_TEXT, **rf,
            "fin_paint_released_before_m2": float(paint_rel), "fin_paint_released_after_m2": float(paint_rel),
            "cross_trade": "after-state = candidate + paint rows only; FIN.PLASTER, FIN.SKIRTING, MAS.* lines "
                           "byte-identical (checked by construction and check_pairs)",
            "low_end_cause": "painted part = return face - frame-covered depth (frame detail not printed, T-561); a "
                             "return on a tiled wet-room side carries no paint (owner 2026-11-02): both lie inside "
                             "the 0 low end",
            "v7_delta": "V7 listed the same 30 lines in one list; V8 keys them by face id, splits 26 valued "
                        "(23.070 m2 = T-561 count and sum) from 4 HELD-by-name, and adds the pairing check",
            "source": _src("T-561")}


# ------------------------------------------------------------------------------------------------- 2 dressing class
def _floor_lines(idx, key):
    fl = [l for l in idx.values() if l["element_id"] == f"{key}:floor" and l["item_code"].startswith("FIN.FLOOR.")
          and ".BED." not in l["item_code"]]
    bed = sorted({l["item_code"] for l in idx.values() if l["element_id"] == f"{key}:floor:bed"})
    return fl, bed


def estimated_class(idx, a08, v7_row):
    """A08 ESTIMATED: the dressing's finish class = the neighbour bed room's own released floor finish class."""
    fl, bed = _floor_lines(idx, a08["neighbour"])
    if len(fl) != 1 or fl[0]["class"] != "RELEASED":
        raise ManifestError(f"A08: neighbour {a08['neighbour']} has no single released floor-finish line")
    code = fl[0]["item_code"]
    if code == "FIN.FLOOR.FINISH_HELD":
        raise ManifestError("A08: the neighbour's own finish is HELD: nothing to estimate from")
    others = {}
    for k in a08["other_bed_rooms"]:
        f2, b2 = _floor_lines(idx, k)
        others[k] = {"floor_line": f2[0]["line_id"] if f2 else None, "item_code": f2[0]["item_code"] if f2 else None,
                     "bed": b2}
    add = v7_row["expected_after"]["add"]
    own_bed = sorted({a["item_code"] for a in add if ".BED." in a["item_code"]})
    if own_bed != bed:
        raise ManifestError(f"A08: the dressing bed {own_bed} is not of the neighbour's scope {bed}")
    fin = add[0]
    if fin["value"] is None or Decimal(str(fin["value"])) != Decimal("2.97"):
        raise ManifestError("A08: the dressing floor area is not the V7 2.970 m2")
    same = all(o["item_code"] == code and o["bed"] == bed for o in others.values())
    row = {"id": f"FLOOR_CLASS_A08:{a08['space']}", "closes": "F-C-T564-1", "verdict": "ESTIMATED label (no "
           "quantity change)",
           "physical_element": "the finished floor of the enclosed 1F space beside the bed room (our label 'dressing'; "
                               "the plan prints no name, RFI-A08)",
           "before": {"item_code": fin["item_code"], "m2": fin["value"], "finish_class": "HELD 'unlabelled' (V7)"},
           "expected_after": {"item_code": fin["item_code"], "m2": fin["value"], "m2_change": 0.0,
                              "finish_class": f"{code} (A08 ESTIMATED)", "material_label_source": a08["source"],
                              "neighbour_floor_line": fl[0]["line_id"], "neighbour": a08["neighbour"],
                              "bindings": "T-455 ADH / TILE rows stay HELD blank (no tile size printed; an ESTIMATED "
                                          "class never releases a material quantity)"},
           "basis": "ESTIMATED (A08)", "evidence_status": "area DRAWING-CONFIRMED 2.970 m2; finish class ESTIMATED, "
                                                          "NOT VERIFIED",
           "neighbour_evidence": f"arch {a08['via']} on face 1F-W16 of room 1F-10 = {a08['neighbour']} (T-292 "
                                 "ledger); T-553 pairs the space with this room (his row 23 = 16.340 + 2.970 + 0.150)",
           "other_bed_rooms": others, "label_independent_of_neighbour": same,
           "named_discrepancy": "RFI-A08 text describes the bed room as 4.20 x 4.00; the room the arch and T-553 "
                                "give is printed 3.80 x 4.30 (T-088). Both 1F bed rooms on the candidate carry "
                                f"{code} on {bed}, so the ESTIMATED class is the same either way; the RFI text "
                                "stays for the Lead to correct (no quantity effect)",
           "comparison": "floor tile 387.094 m2 valued + 2.970 m2 ESTIMATED beside (never 390.064 valued) vs "
                         "freelancer 409.58",
           "source": _src("T-564")}
    return check_status(row)


# ------------------------------------------------------------------------------------------------- 3 pier returns
def pier_returns(idx):
    faces = [r for r in csv.DictReader(open(T567_FACES, encoding="utf-8")) if PIER_KEY in r["key"]]
    if len(faces) != 2:
        raise ManifestError(f"T-567: expected 2 pier return faces, found {len(faces)}")
    storey = faces[0]["key"].split("/")[0]
    t = _json(T567_JSON)
    host = [k for k, v in t["candidate_lines"].items() if v["item"] == "FIN.EXT.FINISH" and v["floor"] == storey]
    if len(host) != 1:
        raise ManifestError(f"no single FIN.EXT.FINISH {storey} line for the pier returns")
    hl = idx[host[0]]
    if hl["item_code"] != "FIN.EXT.FINISH" or hl["class"] != "HELD" or hl["measured_net"] is not None:
        raise ManifestError(f"{host[0]} is not the HELD blank FIN.EXT.FINISH line")
    taken = [l["line_id"] for l in idx.values() if "PIER" in l["element_id"].upper() and "RETURN" in
             l["element_id"].upper()]
    if taken:
        raise ManifestError(f"DOUBLE: pier returns already carried by {taken}")
    led = []
    for f in sorted(faces, key=lambda r: r["key"]):
        lo, hi = _d(f["lo"] or None), _d(f["hi"] or None)
        led.append({"face_key": f["key"], "class": f["class"], "status": f["status"],
                    "m2": float(lo) if f["status"] == "DRAWING-CONFIRMED" else None,
                    "bound_m2": None if f["status"] == "DRAWING-CONFIRMED" else [float(lo), float(hi)]})
    conf = sum((Decimal(str(x["m2"])) for x in led if x["m2"] is not None), Decimal(0))
    return {"id": "PIER_RETURNS_EXT", "closes": "T-567 R-T567-6 (register PLASTERED RETURN FACE, external part)",
            "owner_line": host[0], "owner_line_state": "HELD blank (T-314 ENGINE_OMISSION) - unchanged",
            "ledger_entries": led, "drawing_confirmed_m2": float(conf),
            "held_bound_m2": [x["bound_m2"] for x in led if x["bound_m2"]][0],
            "internal_lines_taking_them": 0,
            "evidence_status": "storey face DRAWING-CONFIRMED (length re-measured by the Checker 15:58, height from "
                               "the printed levels); parapet face HELD (pier top not printed)",
            "source": _src("T-567")}


# ------------------------------------------------------------------------------------------------- 4 W17 Q-76 A
def w17(idx):
    h, s = idx[W17["held_line"]], idx[W17["settled_line"]]
    w, ht, bh = Decimal(W17["width"]), Decimal(W17["height"]), Decimal(W17["band_height"])
    q = w * ht
    if h["class"] != "HELD" or (_d(h["held_low"]), _d(h["held_high"])) != (q, (w * bh).quantize(Decimal("0.001"))):
        raise ManifestError(f"{W17['held_line']}: HELD range is not W17 alone ({q} .. {w * bh})")
    if s["class"] != "RELEASED" or h["element_id"].split(":")[2] != s["element_id"].split(":")[2]:
        raise ManifestError("W17: the settled line is not the same storey's released window line")
    cross = sorted((l["line_id"], l["item_code"], l["class"]) for l in idx.values() if "W17" in l["element_id"])
    before = _d(s["measured_net"])
    return {"id": "W17_Q76A", "closes": "F-C-T568-1", "verdict": "OWNER RULE NOT YET WIRED",
            "physical_element": "the curved 1F window over the pool (W17): opening 3.29 x 3.00; the 0.45 m band above "
                                "it is wall",
            "before": {"held_line": W17["held_line"], "held_m2": [float(_d(h["held_low"])), float(_d(h["held_high"]))],
                       "settled_line": W17["settled_line"], "settled_m2": float(before)},
            "expected_after": {"held_line": "RETIRED (no other window in its range)",
                               "settled_m2": float(before + q), "m2_change": float(q)},
            "basis": "OWNER-APPROVED (Q-76 A on the drawing evidence it cites)",
            "evidence_status": "ASSUMED - OWNER-APPROVED, source owner Q-76 A + Q-39 C",
            "cross_trade": {"lines_with_W17": [list(c) for c in cross],
                            "moved_by_this_row": 0,
                            "note": "the W17 reveal lines stay HELD (their own frame / depth detail); blockwork and "
                                    "plaster deduct the masonry opening by their own ledgers: not moved here"},
            "source": _src("T-568") + [{"owner": W17["source"]}]}


# ------------------------------------------------------------------------------------------------- 5 rebar omission
def rebar_omission(idx):
    reb = [l for l in idx.values() if l["item_code"] == "STR.REBAR" and
           any(k in l["element_id"].upper() for k in REBAR_HOSTS)]
    if reb:
        raise ManifestError(f"a dome / lift-pit STR.REBAR line exists ({reb[0]['line_id']}): restate the row")
    hosts = sorted((l for l in idx.values() if l["item_code"] in REBAR_CONC and l["class"] != "EXCLUDED" and
                    any(k in l["element_id"].upper() for k in REBAR_HOSTS)), key=lambda l: l["element_id"])
    rows = [{"concrete_line": l["line_id"], "concrete_item": l["item_code"], "concrete_element": l["element_id"],
             "concrete_class": l["class"], "concrete_m3": l["measured_net"],
             "expected_after": {"item_code": "STR.REBAR", "element_id": l["element_id"] + ":REBAR", "class": "HELD",
                                "value": None, "unit": "kg",
                                "why": "no bar schedule / detail read for this element yet (T-560); never 0"}}
            for l in hosts]
    excl = sorted(l["line_id"] for l in idx.values() if l["item_code"] in REBAR_CONC and l["class"] == "EXCLUDED"
                  and any(k in l["element_id"].upper() for k in REBAR_HOSTS))
    return {"id": "REBAR_OMISSION", "closes": "T-560 ENGINE_OMISSION", "rows": rows, "lines": len(rows),
            "excluded_concrete_not_given_rebar": excl,
            "evidence_status": "HELD blank (no figure, no bound): the omission is of a line, not of a measure",
            "kg_change_valued": 0.0, "source": _src("T-560")}


# ------------------------------------------------------------------------------------------------- assemble
def wiring_rows(rp, dc, pr, wq, rb):
    return [
        {"id": rp["id"], "gate": "B (adds HELD blank FIN.PAINT lines only; FIN.PAINT released unchanged)",
         "steps": [f"1. {rp['valued_faces']} FIN.PAINT return rows on their face ids, HELD blank, bound beside 0 .. "
                   f"the face's plaster m2 (sum {rp['valued_m2']})",
                   f"2. {len(rp['held'])} FIN.PAINT return rows HELD by name on the HELD plaster returns",
                   "3. check_pairs on the package's line index; every other line byte-identical",
                   "4. statement (T-570 F-C-T570-1): restate the RETURN row ENGINE_WRONG 23.07 -> HELD <= 23.07"],
         "order": "any time after T-423 r2 (same B6 family); never folded into a released paint line"},
        {"id": dc["id"], "gate": "B (label only: no line, figure or binding moves)",
         "steps": ["1. in FLOOR_FINISH_COMPLETENESS_WIRING (V7) write the dressing finish class "
                   f"'{dc['expected_after']['finish_class']}' with its source note",
                   "2. statements show 387.094 valued + 2.970 ESTIMATED beside"],
         "order": "inside the V7 FLOOR_FINISH_COMPLETENESS_WIRING package"},
        {"id": pr["id"], "gate": "B (ledger entry on a HELD blank line; no figure released)",
         "steps": [f"1. list {len(pr['ledger_entries'])} pier return faces in the ledger of {pr['owner_line']}",
                   "2. the line stays HELD blank until T-314"],
         "order": "with T-314"},
        {"id": wq["id"], "gate": "B (one HELD line retires, one settled line +9.870 m2)",
         "steps": [f"1. retire {wq['before']['held_line']}", f"2. {wq['before']['settled_line']} "
                   f"{wq['before']['settled_m2']} -> {wq['expected_after']['settled_m2']} m2",
                   "3. the W17 reveal lines stay HELD"],
         "order": "stream F, any time (no dependency)"},
        {"id": rb["id"], "gate": f"B (adds {rb['lines']} HELD blank STR.REBAR lines)",
         "steps": [f"1. one STR.REBAR row per live dome / ring / lift-pit wall concrete line ({rb['lines']})",
                   "2. valued rebar unchanged"],
         "order": "stream S, any time (no dependency)"},
    ]


def packages():
    return {
        "T-498 (S package)": {"v8_changes": [], "why": "no V8 piece moves a MAS line or a glue host"},
        "T-563 PLASTER_HEIGHT_V1_WIRING": {"v8_changes": [], "why": "no V8 piece moves a plaster line"},
        "T-423 r2 (paint / skirting)": {"v8_changes": [], "why": "return paint stays its own row RETURN_PAINT_FACES"},
        "T-509 (B1-04 disposal)": {"v8_changes": [], "why": "T-565 moves no B1 line"},
        "T-314 (FIN.EXT.FINISH)": {"v8_changes": ["PIER_RETURNS_EXT ledger entries"], "why": "T-567 R-T567-6"},
        "FLOOR_FINISH_COMPLETENESS_WIRING (V7)": {"v8_changes": ["FLOOR_CLASS_A08 label"], "why": "F-C-T564-1"},
        "RETURN_PAINT_FACES (supersedes V7 PAINT_RETURN_MISSING)": {"v8_changes": ["face-keyed rows + pairing check",
                                                                                   "T-570 restatement"],
                                                                    "why": "T-561 / T-570"},
        "W17_Q76A (new)": {"v8_changes": ["see wiring_rows"], "why": "F-C-T568-1"},
        "REBAR_OMISSION (new)": {"v8_changes": ["see wiring_rows"], "why": "T-560"},
        "T-363 / T-372 / T-513 / F package": {"v8_changes": [], "why": "no V8 piece moves their lines"},
    }


def build():
    v7 = v7_manifest()
    M2.check_sources(PIECES)
    cov = M4.check_coverage(NEW_PIECES, V7_BASE, V8_BASE)
    if set(NO_WIRING) & set(WIRING_SOURCES):
        raise ManifestError("NO_WIRING and WIRING_SOURCES must be disjoint pieces of this manifest")
    if set(NO_WIRING) | set(WIRING_SOURCES) != set(NEW_PIECES):
        raise ManifestError("every new piece is a wiring source or a declared NO_WIRING piece")
    idx = M1.line_index()
    v7_dress = next(r for r in v7["fix_rows"]["rows"] if r["closes"] == "F-T553-1")
    rp = return_paint(idx)
    dc = estimated_class(idx, A08, v7_dress)
    pr = pier_returns(idx)
    wq = w17(idx)
    rb = rebar_omission(idx)
    man = {
        "schema": SCHEMA, "rule": RULE, "candidate": M1.CANDIDATE, "task": "T-569",
        "supersedes": "T-564 WIRING_MANIFEST_V7.json (every V7 .. V2 statement carried unless listed in v7_to_v8)",
        "coverage_rule": M4.RULE_COVERAGE, "coverage": cov,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V7_JSON, T561, T567_FACES, T567_JSON, M1.INDEX57)},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())}, "no_wiring": NO_WIRING,
        "wiring_sources": WIRING_SOURCES,
        "return_paint": rp, "dressing_class": dc, "pier_returns": pr, "w17": wq, "rebar_omission": rb,
        "wiring_rows": wiring_rows(rp, dc, pr, wq, rb), "packages": packages(),
        "v7_rows_carried": {"FLOOR_FINISH_COMPLETENESS_WIRING": v7["wiring_rows"][0]["id"] ==
                            "FLOOR_FINISH_COMPLETENESS_WIRING"},
        "candidate_lines_moved_v7_to_v8": 0, "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    man["v7_to_v8"] = [
        {"what": "return paint", "v7": f"PAINT_RETURN_MISSING ({v7['return_paint']['lines']} lines, one list)",
         "v8": f"RETURN_PAINT_FACES ({rp['valued_faces']} faces {rp['valued_m2']} m2 + {len(rp['held'])} HELD by "
               "name, pairing check)", "cause": "T-561 / register PLASTERED RETURN FACE / T-570"},
        {"what": "dressing finish class", "v7": "HELD 'unlabelled'", "v8": dc["expected_after"]["finish_class"],
         "cause": "F-C-T564-1 / A08"},
        {"what": "SW pier returns", "v7": "no row", "v8": f"ledger of {pr['owner_line']} (HELD blank)",
         "cause": "T-567 R-T567-6"},
        {"what": "W17", "v7": "no row", "v8": "HELD line retires, 1F settled +9.870 m2", "cause": "F-C-T568-1"},
        {"what": "dome / lift-pit rebar", "v7": "no row", "v8": f"{rb['lines']} HELD blank STR.REBAR rows",
         "cause": "T-560"}]
    man["findings"] = [
        "F-T569-1: the 30 plastered return lines are 26 valued faces (23.070 m2, T-561 count and sum) + 4 HELD by "
        "name (T-561's 'outside' lines); V7's single list hid that split",
        "F-T569-2: RFI-A08 describes the bed room beside the unlabelled space as 4.20 x 4.00, while the arch A-1F-01 "
        "(T-292) and T-553's pairing give the 3.80 x 4.30 room 1F-R0E919A; both 1F bed rooms are PORCELAIN on a DRY "
        "bed, so the A08 ESTIMATED class does not depend on it (Lead: correct the RFI text)",
        "F-T569-3: two Checker-confirmed integration gaps of the newest merges had no wiring row: W17 Q-76 A "
        "(+9.870 m2 settled) and the dome / lift-pit rebar lines (HELD blank)",
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
