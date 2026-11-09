"""T-554: reconciled-quantities statement adapters for the merged T-543 / T-546 / T-542 reports, plus the Checker class
corrections F-C-T548-1 and F-C-T548-2 / F-C-T543-1 (research, unwired; computes no new quantity).

The T-548 builder (research/agents_t548/statement.py, R-T548-1, MERGED 3f3b580c) is IMPORTED READ-ONLY and is the only
place a section is closed. This module only normalises reports into its section format, applies the owed corrections
from an explicit table, and adds one guarded extension (R-T554-1 below).

R-T554-1 (proposed, every villa): CROSS-FAMILY HOLD. When the physical element of a statement row is held by a
candidate line of ANOTHER item family and unit (the parapet above its RC upstand held as STR.CONC.PARAPET m3 under a
masonry m2 row; a doorway segment of a wet-room upturn held as FIN.WP.DOORWAY_TRANSITION m2 under an lm row), the row
may name that line as its held line, under four conditions:
  (a) the line is HELD (blank) in the candidate line index, its own item code and unit are recorded beside the section,
      and its unit differs from the section unit (a same-unit line belongs in the section's own held lines);
  (b) no quantity of it enters the section: it carries no low and no high into R-T548-1 (f), so it can only make the
      engine bounded high OPEN; its own bounds (in its own unit) are printed beside, never converted;
  (c) it is never a valued line of the section (R-T548-1 (b) refuses the same id twice);
  (d) a row whose element has NO candidate line, own or cross-family, is never HELD: it is UNRESOLVED with engine
      status NONE and its cause named (silent-omission candidate, T-493 F-3), or ENGINE_WRONG with a fix row.
An engine m2 line enters an lm section only through the engine's OWN rule height with its source (R-T546-1 (e)):
lm = m2 / h, checked exact (lm x h == m2), the m2 bound to the index; the freelancer's multiplier is never a height.

CLASS CORRECTIONS (Checker): applied from CORRECTIONS by row signature; a correction whose target row is missing or
has changed is refused, and verify_corrections() refuses a statement in which any owed correction is absent.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T548 = ROOT / "research/agents_t548"
for p in (T548, ROOT / "research/agents_t543", ROOT / "research/agents_t546"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import adapters as A  # noqa: E402  (T-548, read only)
import statement as S  # noqa: E402  (T-548, read only)

INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T543_JSON = ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json"
T543_INPUTS = ROOT / "research/agents_t543/t543_inputs.py"
T546_INPUTS = ROOT / "research/agents_t546/t546_inputs.py"
T542_JSON = ROOT / "research/agents_t542/out/T542_STAIR_BED_CLASSES.json"

D = S.D


class AdapterError(ValueError):
    pass


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_index(path: Path = INDEX) -> dict:
    return A.load_index(path)


# ------------------------------------------------------------------------------------------- R-T554-1 -------------
def bind_cross_family(sec: dict, index: dict) -> None:
    """R-T554-1 (a): every cross-family held line is HELD in the index, of another unit, with its item code."""
    own = {ln["line_id"] for k in ("valued_lines", "held_lines", "excluded_lines") for ln in sec["engine"].get(k, [])}
    for ln in sec["engine"].get("held_cross_family", []):
        lid = ln["line_id"]
        if lid in own:
            raise AdapterError(f"{sec['section_id']}: cross-family line {lid} is also an own line of the section")
        ix = index.get(lid)
        if ix is None or ix["class"] != "HELD":
            raise AdapterError(f"{sec['section_id']}: cross-family line {lid} is not HELD in the index")
        if ix["item_code"] != ln["item_code"] or ix["unit"] != ln["unit"]:
            raise AdapterError(f"{sec['section_id']}: cross-family line {lid} is {ix['item_code']} {ix['unit']} in the "
                               f"index, adapter says {ln['item_code']} {ln['unit']}")
        if ln["unit"] == sec["unit"]:
            raise AdapterError(f"{sec['section_id']}: line {lid} has the section unit {sec['unit']}: an own held line, "
                               "not a cross-family hold")
        if ix["measured_net"] is not None:
            raise AdapterError(f"{sec['section_id']}: cross-family line {lid} carries a quantity")


def bind_derived(sec: dict, index: dict) -> None:
    """Valued lines derived from an engine m2 line through the engine's own rule height (R-T546-1 (e))."""
    for ln in sec["engine"]["valued_lines"]:
        dv = ln.get("derived")
        if not dv:
            raise AdapterError(f"{sec['section_id']}: valued line {ln['line_id']} in {sec['unit']} without derivation")
        ix = index.get(ln["line_id"])
        if ix is None or ix["class"] != "RELEASED" or ix["unit"] != dv["from_unit"]:
            raise AdapterError(f"{sec['section_id']}: {ln['line_id']} is not a RELEASED {dv['from_unit']} line")
        if D(ix["measured_net"]) != D(dv["from_qty"]):
            raise AdapterError(f"{sec['section_id']}: {ln['line_id']} index {ix['measured_net']} != {dv['from_qty']}")
        if not dv.get("height_source"):
            raise AdapterError(f"{sec['section_id']}: {ln['line_id']} rule height without a source")
        if D(ln["qty"]) * D(dv["rule_height"]) != D(dv["from_qty"]):
            raise AdapterError(f"{sec['section_id']}: {ln['line_id']} lm x h != m2 (not exact)")
    for ln in sec["engine"]["held_lines"]:
        ix = index.get(ln["line_id"])
        if ix is None or ix["class"] != "HELD":
            raise AdapterError(f"{sec['section_id']}: held line {ln['line_id']} is not HELD in the index")


def refuse_held_as_zero(sec: dict) -> None:
    """HELD is never 0: a held line (own or cross-family) given a quantity is refused before the builder."""
    for k in ("held_lines", "held_cross_family"):
        for ln in sec["engine"].get(k, []):
            if ln.get("qty") is not None:
                raise AdapterError(f"{sec['section_id']}: held line {ln['line_id']} given qty {ln['qty']!r}: "
                                   "HELD is never a quantity (never 0)")


def for_builder(sec: dict) -> dict:
    """R-T554-1 (b): cross-family lines reach the T-548 builder as held lines with NO bound (they can only open the
    high end); their own unit stays beside in 'held_cross_family'."""
    s2 = copy.deepcopy(sec)
    xf = s2["engine"].pop("held_cross_family", [])
    s2["engine"]["held_lines"] = list(s2["engine"]["held_lines"]) + [
        {"line_id": x["line_id"], "low": None, "high": None, "reason": f"cross-family hold {x['item_code']} {x['unit']}"}
        for x in xf]
    for ln in s2["engine"]["valued_lines"]:
        ln.pop("derived", None)
    return s2


# ------------------------------------------------------------------------------------------- corrections ----------
# (section, row name, expected delta, expected class) -> replacement rows. Source: board T-548 verdict (Verifier
# 2026-11-06T02:22Z): F-C-T548-1, own P7757.dxf re-measure of MS1-LD 1.250 x 1.150 = 1.4375 m2 (handles B16 / BE4 /
# A92 / CE2), T-542 drawing-derived MS1-LD 1.4375 (STAIR_LANDING, Q-53 C scope); the Q-53 / T-086 reference took
# 1.20 x 1.25 = 1.500.
CORRECTIONS = [
    {"id": "F-C-T548-1", "section_id": "T-534/stair-bed", "row": "MS1-LD LANDING SCOPE", "delta": "1.5",
     "class": "ENGINE_WRONG",
     "replace": [
         {"name": "MS1-LD LANDING SCOPE: drawn landing 1.250 x 1.150 with no candidate line", "delta": "1.4375",
          "class": "ENGINE_WRONG", "engine_status": "NONE", "fix_row": "T-502",
          "note": "F-C-T548-1: Checker own P7757.dxf re-measure 1.250 x 1.150 = 1.4375 (T-493 F-3 silent omission); "
                  "T-542 drawing-derived MS1-LD 1.4375 STAIR_LANDING (Q-53 C)"},
         {"name": "MS1-LD LANDING SCOPE: reference size 1.20 x 1.25 vs drawn 1.25 x 1.15", "delta": "0.0625",
          "class": "RULE_DIFFERENCE", "engine_status": "NONE",
          "note": "F-C-T548-1: the Q-53 / T-086 reference figure's own size (1.500 - 1.4375); not an engine error"}]},
    {"id": "F-C-T543-1", "section_id": "T-543/blockwork", "row": "parapets: RC upstand 0.30 m above the slab",
     "delta": "41.0512800", "class": "ENGINE_RIGHT",
     "annotate": {"depends_on": "H1",
                  "note_add": "rests on H1 (F-C-T543-1 / F-C-T548-2): his parapet heights read from the slab top "
                              "(+0.50 / +0.63 over the printed heights above finish); if his base is the finish, only "
                              "(upstand - b_edge) lies inside his face and that share is HELD (b_edge, D-39)"}},
]


def apply_corrections(sections: list[dict], corrections: list[dict] = CORRECTIONS) -> list[str]:
    by_id = {x["section_id"]: x for x in sections}
    done = []
    for c in corrections:
        sec = by_id.get(c["section_id"])
        if sec is None:
            raise AdapterError(f"{c['id']}: section {c['section_id']} absent")
        hits = [i for i, r in enumerate(sec["rows"]) if r["name"].startswith(c["row"])]
        if len(hits) != 1:
            raise AdapterError(f"{c['id']}: target row {c['row']!r} found {len(hits)} times")
        i = hits[0]
        r = sec["rows"][i]
        if D(r["delta"]) != D(c["delta"]) or r["class"] != c["class"]:
            raise AdapterError(f"{c['id']}: target row is {r['class']} {r['delta']}, correction expects "
                               f"{c['class']} {c['delta']}: the source changed, re-read before correcting")
        if "replace" in c:
            new = []
            for x in c["replace"]:
                y = {k: v for k, v in r.items() if k not in ("name", "delta", "class", "fix_row", "note",
                                                             "engine_status", "held_line_ids")}
                y.update(x)
                y.setdefault("held_line_ids", [])
                y["correction"] = c["id"]
                new.append(y)
            if sum((D(x["delta"]) for x in new), Decimal(0)) != D(r["delta"]):
                raise AdapterError(f"{c['id']}: replacement rows do not sum to the corrected row")
            sec["rows"][i:i + 1] = new
        else:
            r["depends_on"] = c["annotate"]["depends_on"]
            r["note"] = (r.get("note", "") + "; " if r.get("note") else "") + c["annotate"]["note_add"]
            r["correction"] = c["id"]
        done.append(c["id"])
    return done


def verify_corrections(st: dict, corrections: list[dict] = CORRECTIONS) -> None:
    """Refuse a statement in which an owed correction is missing (adverse: dropped class correction)."""
    secs = {x["section_id"]: x for x in st["sections"]}
    for c in corrections:
        sec = secs.get(c["section_id"])
        if sec is None:
            raise AdapterError(f"{c['id']}: section {c['section_id']} missing from the statement")
        rows = [r for r in sec["rows"] if r["name"].startswith(c["row"])]
        if "replace" in c:
            if any(r["class"] == c["class"] and D(r["delta"]) == D(c["delta"]) for r in rows):
                raise AdapterError(f"{c['id']}: uncorrected row {c['row']} {c['class']} {c['delta']} in the statement")
            want = {(x["class"], D(x["delta"])) for x in c["replace"]}
            got = {(r["class"], D(r["delta"])) for r in rows}
            if not want <= got:
                raise AdapterError(f"{c['id']}: correction rows {sorted(want - got)} missing")
        else:
            if len(rows) != 1 or rows[0].get("depends_on") != c["annotate"]["depends_on"] \
                    or "rests on H1" not in (rows[0].get("note") or ""):
                raise AdapterError(f"{c['id']}: row {c['row']} does not carry its dependency "
                                   f"{c['annotate']['depends_on']}")


# ------------------------------------------------------------------------------------------- T-543 ---------------
T543_TRADE = "B9 blockwork"
PARAPET_RC_LINES = [("L-030538dda6a32c601c4c", "2F_ROOF"), ("L-1d419b64e8ca1af30fb4", "ANNEX_ROOF"),
                    ("L-9a2c81164ec6499cc28c", "1F_ROOF"), ("L-b5ffc172a354375ca107", "GF_TERRACE")]
# non-split components: name prefix -> (class, engine status, held/cross-family ids, note). Source: T-543 s.2 / s.4.
T543_SINGLE = {
    "boundary wall": ("RULE_DIFFERENCE", "NONE", [], "family placement: the engine books it as EXT.FENCE.WALL "
                      "(F-STREET 14.84 + F-NORTH 83.1305 valued, F-SEA / F-LOWER HELD); compared under the fence family"),
    "1F 'projections' row": ("UNRESOLVED", "NONE", [], "no masonry element identified (T-543 s.3, T-225); T-550"),
    "his 20 cm openings with no floor": ("UNRESOLVED", "NONE", [], "his deduction with no floor; T-550"),
}
# parapet split rows: name prefix -> (class, engine status, cross-family ids, note)
T543_PARAPET = {
    "parapet face above the RC upstand": ("HELD", "HELD", [x[0] for x in PARAPET_RC_LINES],
                                          "held with its element STR.CONC.PARAPET (material Q-65 C open); R-T554-1"),
    "RC upstand 0.30 m above the slab": ("ENGINE_RIGHT", "NONE", [],
                                         "P1 detail: concrete, never masonry (0 masonry by the detail)"),
    "print rounding of the stored block alternatives": ("TOLERANCE", "NONE", [], ""),
    "RESIDUAL: parapet height below the finished roof": ("UNRESOLVED", "HELD", [],
                                                         "b_edge HELD (D-39); T-550 takes it to its cause"),
}
# F-T554-2: the 2F height row lies wholly on HELD walls (every 2F wall HELD on the roof datum D-39; H_eng is the
# b_r = 0.05 what-if): R-T548-1 (e) refuses RULE_DIFFERENCE on a HELD engine side -> HELD, source cause kept.
T543_RECLASS = {("2F", "height convention"): ("HELD", "F-T554-2: on HELD walls only (D-39 what-if height); "
                                                      "RULE_DIFFERENCE once b_r is printed")}


def _t543_inputs():
    return A._load_module(T543_INPUTS, "t554_t543_inputs")


def t543_section(json_path: Path = T543_JSON) -> dict:
    d = json.loads(json_path.read_text(encoding="utf-8"))
    if d["candidate"] != "ARCH_TAKEOFF_V3.0.58" or d["unit"] != "m2":
        raise AdapterError("T-543: candidate or unit changed")
    inp = _t543_inputs()
    return t543_from(d, inp.engine_lines(), inp.engine_walls())


def t543_from(d: dict, lines: list[dict], walls_list: list[dict], parapet_lines=None) -> dict:
    """Pure adapter: a T-543-format report + the engine masonry lines + the wall register (any villa)."""
    parapet_lines = PARAPET_RC_LINES if parapet_lines is None else parapet_lines
    valued = [{"line_id": x["line_id"], "qty": x["qty"], "unit": "m2"} for x in lines if x["class"] == "RELEASED"]
    held = [x for x in lines if x["class"] == "HELD"]
    if any(x["qty"] is not None for x in held):
        raise AdapterError("T-543: a HELD masonry line carries a quantity (HELD is never 0)")
    walls = {w["wall_id"]: w for w in walls_list}

    def held_ids_for(floor: str, wall_ids: list[str]) -> list[str]:
        ts = set()
        for wid in wall_ids:                       # register ids, e.g. '1F-W14 + 1F-W15' is one register wall
            w = walls.get(wid)
            if w is None or w["floor"] != floor:
                raise AdapterError(f"T-543: wall {wid} not in the {floor} register")
            ts.add(D(w["t_m"]).normalize())
        out = []
        for x in held:
            fl, _, rest = x["element_id"].partition("-WALLS:walls t=")
            if fl != floor or not rest:
                continue
            if not ts or D(rest.split("#")[0]).normalize() in ts:
                out.append(x["line_id"])
        if not out:
            raise AdapterError(f"T-543: no held {floor} masonry line for {wall_ids}")
        return sorted(out)

    rows = []
    for comp in d["rows"]:
        nm = comp["name"]
        if comp["cause"] == "SPLIT" and nm.endswith("storey walls (net of openings)"):
            fl = nm.split()[0]
            all_held = comp["engine_valued_m2"] is None
            for r in comp["decomposition"]["rows"]:
                cls, est, ids, note = r["cause"], "VALUED", [], r.get("basis", "")
                if cls == "HELD":
                    est, ids = "HELD", held_ids_for(fl, r["walls"])
                elif all_held:
                    est = "NONE" if D(r["delta"]) == 0 else "HELD"
                for (f2, pre), (c2, why) in T543_RECLASS.items():
                    if f2 == fl and r["name"].startswith(pre):
                        cls, ids, note = c2, held_ids_for(fl, []), f"{note}; {why}"
                if r["name"].startswith(("height convention", "RESIDUAL: wall-length")):
                    note += "; F-C-T543-2: height (k) and length (m) are one 'height x length' cause: quote together"
                rows.append({"name": f"{fl}: {r['name']}", "delta": r["delta"], "class": cls,
                             "source_cause": r["cause"], "engine_status": est, "held_line_ids": ids,
                             "source": "T-543 s.2 storey-wall split", "note": note,
                             "walls": r["walls"]})
        elif comp["cause"] == "SPLIT" and nm.startswith("parapets"):
            for r in comp["decomposition"]["rows"]:
                k = [v for p, v in T543_PARAPET.items() if r["name"].startswith(p)]
                if len(k) != 1:
                    raise AdapterError(f"T-543 parapet row {r['name']!r} not in the adapter table")
                cls, est, ids, note = k[0]
                if ids:
                    ids = [x[0] for x in parapet_lines]
                if cls != r["cause"]:
                    raise AdapterError(f"T-543 parapet row {r['name']!r}: report class {r['cause']} != table {cls}")
                rows.append({"name": f"parapets: {r['name']}", "delta": r["delta"], "class": cls,
                             "source_cause": r["cause"], "engine_status": est, "held_line_ids": ids,
                             "source": "T-543 s.2 parapet split", "note": f"{r.get('basis', '')}; {note}"})
        else:
            k = [v for p, v in T543_SINGLE.items() if nm.startswith(p)]
            if len(k) != 1 or k[0][0] != comp["cause"]:
                raise AdapterError(f"T-543 component {nm!r} not in the adapter table (or its class changed)")
            cls, est, ids, note = k[0]
            rows.append({"name": nm, "delta": comp["difference_m2"], "class": cls, "source_cause": comp["cause"],
                         "engine_status": est, "held_line_ids": ids, "source": comp["source"], "note": note})
    return {
        "section_id": "T-543/blockwork", "report": "T-543", "trade": T543_TRADE, "item_codes": ["MAS.BLOCK"],
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": d["freelancer_total"], "unit": "m2",
                      "basis": "freelancer masonry workbook, one sheet, exact sum of his row products 1,260.6895 "
                               "(printed 1,260.69; sections 559.80 / 617.25 / 83.64) (T-543 s.1; Drive 'Alsenan "
                               "chalet project')"},
        "engine": {"valued_total": d["engine_valued_total"], "valued_lines": valued,
                   "held_lines": [{"line_id": x["line_id"], "low": None, "high": None,
                                   "reason": f"{x['element_id']} HELD blank"} for x in held],
                   "excluded_lines": [],
                   "held_cross_family": [{"line_id": lid, "item_code": "STR.CONC.PARAPET", "unit": "m3",
                                          "reason": f"{nm} parapet element (RC + material Q-65 C) HELD blank"}
                                         for lid, nm in parapet_lines]},
        "rows": rows,
        "by_cause_source": d["by_cause"],
    }


# ------------------------------------------------------------------------------------------- T-546 ---------------
T546_TRADE = "B8 wet-room waterproofing"
# doorway segments (T-546 HELD, own rows): room -> one entry per segment, in T-546's door order: the HELD
# FIN.WP.DOORWAY_TRANSITION line that holds it (own room, or the shared closure / opening id held in the neighbour
# room), or None (no transition record in the room: R-T554-1 (d) -> UNRESOLVED, F-T554-1). Source: line index V3.0.57
# element ids (room id prefix, opening id, closure id) and FIN.WP.DOORWAY_TRANSITION_NR records.
DOORWAY_HOLD = {
    "GF lobby wash (2 basins)": [("L-19908ce0b9a2bcadff80", "OP-017 shared: held in GF core W.C. 289 (the lobby's own "
                                  "transition count record L-4bf0adee names OP-017)"),
                                 (None, "second doorway: no transition record in this room (GF OP-018 of the core "
                                  "W.C. 245 is a candidate, not bound)")],
    "GF basin space by the stair": [("L-77a630d7e60ca6c404ba", "own closure D2:825|D2:417")],
    "GF master bath": [("L-20400ca6dc38abb30c33", "own closure D2:820")],
    "GF core W.C. 245 x 167 (wedge)": [("L-65194e5d4497f0882024", "own OP-018")],
    "GF core W.C. 289 x 167 (wedge)": [("L-19908ce0b9a2bcadff80", "own OP-017")],
    "GF stair-core W.C. 175 x 135": [("L-77a630d7e60ca6c404ba", "closure D2:825|D2:417 shared: held in the basin "
                                      "space, own transition L-e0c34550 EXCLUDED as the same closure")],
    "GF kitchen": [("L-b46013c737051e5441fe", "own OP-025 (1.00)")],
    "GF driver W.C.": [("L-b4a23dc5fc953bc5a163", "own OP-026")],
    "GF W.C. by the reception room": [("L-1c36054a8cadc0726e65", "own closure D2:495|D2:417")],
    "GF wash by the reception room": [("L-1c36054a8cadc0726e65", "closure D2:495|D2:417 shared: held in the W.C. by "
                                       "the reception room, own transition L-b60811f6 EXCLUDED as the same closure")],
    "1F east bath 210 x 225": [("L-dfc4e74604047cb21407", "own OP-018")],
    "1F bath by the laundry": [("L-19f6405a5e60a99c29f7", "own OP-019")],
    "1F W.C. by the laundry": [(None, "no transition record in this room (the laundry's OP-010 is a candidate, not "
                                "bound)")],
    "1F west bath A 245 x 205": [("L-aed6f48195f99648c3f3", "own OP-004")],
    "1F west bath B 245 x 205": [("L-07b084a5187a64634108", "own closure D2:3118")],
    "1F laundry": [("L-689197a4778b786de143", "own OP-008 (0.90)"), ("L-bec3b3df8ec830a46447", "own OP-010")],
    "2F roof-floor W.C. 300 x 185": [("L-b5a04e7c058346b6f734", "own OP-006")],
}
PANTRY_UPTURN = "L-8090ff20f2b547d1bc96"


def _t546_inputs():
    return A._load_module(T546_INPUTS, "t554_t546_inputs")


def t546_sections() -> list[dict]:
    return t546_from(_t546_inputs(), DOORWAY_HOLD, PANTRY_UPTURN)


def t546_from(inp, doorway_hold: dict, held_upturns) -> list[dict]:
    """Pure adapter: any module / object with T-546's interface (floor_rows, upturn_rows, the freelancer cells, the
    rule height) + the doorway hold table (room -> [(held line id or None, why)] per segment)."""
    held_upturns = {held_upturns} if isinstance(held_upturns, str) else set(held_upturns)
    trade_codes = {"floor": ["FIN.WP.FLOOR"], "upturn": ["FIN.WP.WALL_UPTURN"]}
    # ---- floor, m2 ----
    frows, fvalued = [], []
    for r in inp.floor_rows():
        ln = r["engine_lines"][0]
        fvalued.append({"line_id": ln["line_id"], "qty": ln["qty"], "unit": "m2"})
        his = D(r["freelancer"]) if r["freelancer"] is not None else Decimal(0)
        acc = Decimal(0)
        for c in r["components"]:
            part = D(c["qty"]) * c["sign"]               # engine - his
            acc += part
            frows.append({"name": f"{r['room']}: {c['name']}", "delta": str(-part), "class": c["cause"],
                          "source_cause": c["cause"], "engine_status": "VALUED", "held_line_ids": [],
                          "source": "T-546 s.2 room table", "note": c["basis"]})
        if acc != D(ln["qty"]) - his:
            raise AdapterError(f"T-546 floor {r['room']}: components {acc} != engine - his {D(ln['qty']) - his}")
    floor = {
        "section_id": "T-546/floor", "report": "T-546", "trade": T546_TRADE, "item_codes": trade_codes["floor"],
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": inp.FREELANCER_FLOOR_M2, "unit": "m2",
                      "basis": "freelancer waterproofing sheet H39 = SUM of 17 room floor cells (T-546 F-T546-1; "
                               "Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": inp.engine_floor_total(), "valued_lines": fvalued, "held_lines": [],
                   "excluded_lines": []},
        "rows": frows,
    }
    # ---- upturn, lm ----
    h = inp.UPTURN_H
    urows, uvalued, xf = [], [], {}
    for r in inp.upturn_rows():
        ln = r["engine_lines"][0]
        if ln["qty"] is None:                            # pantry: HELD, not in his list
            if ln["line_id"] not in held_upturns:
                raise AdapterError(f"T-546 upturn: unexpected held line {ln['line_id']}")
            xf[ln["line_id"]] = {"line_id": ln["line_id"], "item_code": "FIN.WP.WALL_UPTURN", "unit": "m2",
                                 "reason": r.get("note") or "upturn HELD; beside, not in his list"}
            continue
        lm = D(ln["qty"]) / D(h)
        uvalued.append({"line_id": ln["line_id"], "qty": S.s(lm), "unit": "lm",
                        "derived": {"from_qty": ln["qty"], "from_unit": "m2", "rule_height": h,
                                    "height_source": ln["height_source"]}})
        holds = list(doorway_hold.get(r["room"], []))
        acc = Decimal(0)
        for c in r["components"]:
            part = D(c["qty"]) * c["sign"]
            acc += part
            row = {"name": f"{r['room']}: {c['name']}", "delta": S.s(-part), "class": c["cause"],
                   "source_cause": c["cause"], "engine_status": "VALUED", "held_line_ids": [],
                   "source": "T-546 s.3 upturn table (lm)", "note": c["basis"]}
            if c["cause"] == "HELD":
                if not holds:
                    raise AdapterError(f"T-546 upturn {r['room']}: more doorway segments than the hold table")
                lid, why = holds.pop(0)
                if lid is None:
                    row.update({"class": "UNRESOLVED", "engine_status": "NONE",
                                "note": f"{c['basis']}; F-T554-1: {why}: no candidate line holds this segment "
                                        "(R-T554-1 (d); silent-omission candidate, T-493 F-3)"})
                else:
                    row.update({"engine_status": "HELD", "held_line_ids": [lid], "note": f"{c['basis']}; {why}"})
                    xf[lid] = {"line_id": lid, "item_code": "FIN.WP.DOORWAY_TRANSITION", "unit": "m2",
                               "reason": "doorway transition HELD (detail not printed, T-310 policy V3)"}
            elif c["cause"] == "RULE_DIFFERENCE" and "no wall" in c["name"]:
                row["engine_status"] = "NONE"           # Q-35 C: a termination, not an upturn
            urows.append(row)
        if holds:
            raise AdapterError(f"T-546 upturn {r['room']}: hold table has unused segments {holds}")
        if acc != lm - D(r["freelancer"]):
            raise AdapterError(f"T-546 upturn {r['room']}: components {acc} != engine - his")
    if S.s(sum((D(x["qty"]) for x in uvalued), Decimal(0))) != S.s(D(inp.engine_upturn_lm_total())):
        raise AdapterError("T-546 upturn: engine lm total differs from t546_inputs")
    upturn = {
        "section_id": "T-546/upturn", "report": "T-546", "trade": T546_TRADE, "item_codes": trade_codes["upturn"],
        "unit": "lm",
        "reference": {"kind": "FREELANCER", "total": inp.FREELANCER_UPTURN_LM, "unit": "lm", "label": "m.l",
                      "basis": "freelancer waterproofing sheet G40 = SUM of room perimeters (G = C x F, F = 1 is a "
                               "multiplier, not a height); his summary row labels the unit 'm.l' (T-546 F-T546-1, "
                               "Checker AGREE): a LENGTH, never m2"},
        "engine": {"valued_lines": uvalued, "held_lines": [], "excluded_lines": [],
                   "held_cross_family": sorted(xf.values(), key=lambda x: x["line_id"])},
        "rows": urows,
        "engine_m2_lines_note": "engine FIN.WP.WALL_UPTURN is m2 in the candidate; lm = m2 / 0.20 (the engine's own "
                                "rule height UP-WP-002 2.0.0 / Q-03); his 1.00 is never adopted",
    }
    return [floor, upturn]


# ------------------------------------------------------------------------------------------- T-542 ---------------
def t542_beside(t534_sec: dict, index: dict, json_path: Path = T542_JSON) -> dict:
    return t542_beside_from(json.loads(json_path.read_text(encoding="utf-8")), t534_sec, index)


def t542_beside_from(d: dict, t534_sec: dict, index: dict) -> dict:
    """T-542 has no reference figure (no freelancer stair-bed row; T-542 s.6): it enters the statement as a
    drawing-derived table BESIDE the T-534 stair-bed section, never in its totals or its engine range (R-T548-1 (f)).
    Closures: whole = in the V7 wire + beyond; the wire parts' line ids = the T-534 section's valued lines and their
    drawing area = those lines + the named polygon residual; every beyond part is bound to a HELD line or named as
    having no line (fix row T-502)."""
    stair = [r for r in d["rows"] if r["bed_class"] == "STAIR_BED"]
    whole = sum((D(r["bed_m2"]) for r in stair), Decimal(0))
    wire = [r for r in stair if r["in_v7_wire"]]
    beyond = [r for r in stair if not r["in_v7_wire"]]
    a_wire = sum((D(r["bed_m2"]) for r in wire), Decimal(0))
    a_beyond = sum((D(r["bed_m2"]) for r in beyond), Decimal(0))
    sm = d["summary"]
    if whole != D(sm["whole_stair_bed"]["area_m2"]) or a_wire != D(sm["in_v7_wire"]["area_m2"]) \
            or a_beyond != D(sm["beyond_v7_wire"]["area_m2"]) or whole != a_wire + a_beyond:
        raise AdapterError("T-542: whole != in-wire + beyond (or a summary differs from its rows)")
    sec_valued = {ln["line_id"]: D(ln["qty"]) for ln in t534_sec["engine"]["valued_lines"]}
    if {r["line_id"] for r in wire} != set(sec_valued):
        raise AdapterError("T-542: the wire parts are not the T-534 section's valued lines")
    poly = a_wire - sum(sec_valued.values(), Decimal(0))
    if poly != D(d["v7_wire_candidate_net"]["polygon_residual_m2"]):
        raise AdapterError(f"T-542: wire drawing area - lines = {poly}, report names "
                           f"{d['v7_wire_candidate_net']['polygon_residual_m2']}")
    parts = []
    for r in beyond:
        if r["line_id"] is None:
            state, fix = "NO_CANDIDATE_LINE", "T-502"
        else:
            ix = index.get(r["line_id"])
            if ix is None or ix["class"] != "HELD":
                raise AdapterError(f"T-542: beyond part {r['key']} {r['surface']} line {r['line_id']} is not HELD")
            state, fix = "HELD_LINE", None
        parts.append({"key": r["key"], "surface": r["surface"], "landing_class": r["landing_class"],
                      "drawing_m2": S.s(D(r["bed_m2"])), "line_id": r["line_id"], "state": state, "fix_row": fix})
    held_by_name = [{"key": r["key"], "surface": r["surface"], "beside_m2": r["beside_m2"], "line_id": r["line_id"]}
                    for r in d["rows"] if r["bed_class"] == "HELD"]
    floor_family = [{"key": r["key"], "beside_m2": r["beside_m2"], "floor_bed_line": r["floor_bed_line"]}
                    for r in d["rows"] if r["bed_class"] == "FLOOR_BED_FAMILY"]
    ms1 = [p for p in parts if p["key"] == "MS1-LD"]
    return {"report": "T-542", "attached_to": t534_sec["section_id"], "unit": "m2",
            "kind": "DRAWING_DERIVED_BESIDE (no reference figure; never in a total or an engine range)",
            "whole_at_least": S.s(whole), "in_v7_wire": S.s(a_wire), "candidate_wire_lines": S.s(sum(sec_valued.values(),
                                                                                                  Decimal(0))),
            "polygon_residual": S.s(poly), "beyond_wire": S.s(a_beyond), "beyond_parts": parts,
            "held_by_name": held_by_name, "floor_bed_family_beside": floor_family,
            "cross_check": {"MS1-LD_drawing_m2": ms1[0]["drawing_m2"] if ms1 else None,
                            "note": "equals the F-C-T548-1 ENGINE_WRONG 1.4375 (Checker own re-measure)"}}


# ------------------------------------------------------------------------------------------- assembly ------------
def all_sections(index: dict | None = None) -> tuple[list[dict], dict]:
    index = index if index is not None else load_index()
    secs = A.t541_sections() + A.t534_sections() + [t543_section()] + t546_sections()
    absent = {}
    for x in secs:
        refuse_held_as_zero(x)
        bind_cross_family(x, index)
        if x["section_id"] == "T-546/upturn":
            bind_derived(x, index)
            absent[x["section_id"]] = []
        else:
            absent[x["section_id"]] = A.bind_to_index(for_builder(x), index)
    applied = apply_corrections(secs)
    prov = {"inputs": {str(p.relative_to(ROOT)): sha(p) for p in
                       (A.T541_JSON, A.T541_INPUTS, A.T534_JSON, T543_JSON, T543_INPUTS, T546_INPUTS, T542_JSON,
                        INDEX, T548 / "statement.py", T548 / "adapters.py")},
            "valued_lines_not_in_V3_0_57_index": absent, "corrections_applied": applied}
    return secs, prov
