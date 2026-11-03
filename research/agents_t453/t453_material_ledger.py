"""T-453 part 1: the B1 BLOCKWORK MATERIAL LEDGER beside the candidate (ARCH_TAKEOFF_V3.0.45), NOT in it.

Reader tool (stdlib + engine.source.company_rulebook_v1, COMPANY_RULEBOOK_V1 calculators). It measures nothing: each
material row traces   candidate line id -> wall rows (merged fill) -> net m2 / opening -> rule -> count.
No candidate module, no released (V2.9 + route G) line and no BOQ_FAMILY_MASTER family changes here.

Layers kept apart (owner follow-up 2026-11-02): (1) the source line's net quantity and its label, (2) the theoretical
material from an OWNER CONFIRMED rule or a project document, (3) procurement (waste / breakage, purchasing-group
rounding) only where a sourced value exists. A material row is VERIFIED-NET only when its source line is VERIFIED;
DRAWING-CONFIRMED and ASSUMED - OWNER-APPROVED lines give PROVISIONAL-NET; a HELD line gives HELD (never 0). A material
is never VERIFIED because its area is.

Inputs (all committed, sha256-pinned; no drawing content):
  research/agents_t479/out/LINE_INDEX_V3_0_45.json        candidate V3.0.45 line index (MAS.BLOCK lines and nets)
  research/agents_t279/t279_inputs.py -> research/agents_t333/FILL_T333.csv   the merged per-wall fill (pinned there)
  research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json     per-wall pieces (length x clear height)
  research/agents_t198/OPENINGS_T198.csv                  opening census r3 (widths, heads)
  research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv  the printed structural LINTEL SCHEDULE + detail
  research/agents_t367/MORTAR_BY_LINE_T367.csv            installed black-block joint mortar per part line (T-367)

Rules applied (summary; full provenance in each row):
  R-T453-1 BLOCK COUNT  black 0.20 m: UPC-BLACK-BLOCK-001 12.5 / m2 (40 x 20 module, OWNER CONFIRMED); black 0.15 m:
           HELD (module not stated); white AAC: count HELD (the owner's supplier sheet lists two faces, 62.5 x 25 and
           60 x 20, the project selects none); procurement count HELD while no sourced breakage exists.
  R-T453-2 AAC GLUE     UPC-AAC-GLUE-001 (0.15 m 3.5 kg/m2, 0.20 m 4.5 kg/m2); 25 kg bags rounded once per purchasing
           group; the project group is HELD while any held masonry line remains (known part stated).
  R-T453-3 BLACK MORTAR installed joint m3 from the merged T-367 ledger (B9-04 MASONRY_JOINT_MORTAR_V1: 10 mm joint
           on the 40 x 20 module, owner-provisional) -> cement bags / loose sand by UPC-BLACK-MORTAR-001 (Q-78 1:4,
           8 bags + 1.1 m3 per m3); 0.20 m black only (PROVISIONAL-NET); 0.15 m black HELD (face not stated, T-367
           figure beside); procurement mortar HELD (no sourced waste / dry factor).
  R-T453-4 LINTELS      the project prints a LINTEL SCHEDULE (level 1 PROJECT DOCUMENT: cast-in-situ RC, B = wall
           width, D by opening-width band, MIN 40 cm bearing) which governs the company precast rule (level 3); the
           owner's white precast practice (Q-60 'atab only for white blocks', UPC-LINTEL-001) is reported BESIDE for
           white walls only, never chosen. A lintel is REQUIRED only where masonry is built above the head: the head
           (above FFL) must sit below every candidate piece's clear height (structural top -> soffit) by the band
           depth D plus the owner tile-bed maximum 0.06 m (Q-45); below D the beam serves or conflicts -> FLAGGED;
           unknown head or pieces -> HELD. Concrete m3 = B x D x (w + 2 x 0.40); formwork m2 = 2 x D x L + B x w;
           rebar kg HELD (cover, bends and anchorage not printed). Bearing availability at jambs and RC columns is not
           established here: every lintel row is PROVISIONAL with that check named.

    python3 -I research/agents_t453/t453_material_ledger.py [OUT_DIR]     # writes the ledger (default: ./out)
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, ROOT / "research" / "agents_t279"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.source import company_rulebook_v1 as C  # noqa: E402

SCHEMA = "URBAN_T453_MATERIAL_LEDGER_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.45"
LINE_INDEX = ROOT / "research/agents_t479/out/LINE_INDEX_V3_0_45.json"
REGISTER = ROOT / "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json"
OPENINGS = ROOT / "research/agents_t198/OPENINGS_T198.csv"
SCHEDULE = ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
MORTAR = ROOT / "research/agents_t367/MORTAR_BY_LINE_T367.csv"
PINS = {LINE_INDEX: "16920d3c682399541f8fa84d31f39bca171e3d4e7f362bcb1eb0b05b3f4269f4",
        REGISTER: "4f1c794c4906a49dc796ca8630df7032e8b45afe95dbcaf958d0c502ae877803",
        OPENINGS: "d79e6aa5d23edc0ef26fcce0c94d08ac5bb344a51104bb2b5d7378c08a423e22",
        SCHEDULE: "5d5baf166700d1d5968c5420f37118ae27836f61a2eeae88ed658f40e25936d7",
        MORTAR: "22812178c4e09334c55f5275ddf6b793f5d891b8496a138ca7f93739e9b06b4d"}
CANDIDATE_LINES_SHA = "5972888b659e249bed995992f57f0042571d042b50e761cabcc4221d653451d8"

HELD, FLAGGED = "HELD", "FLAGGED"
VNET, PNET = "VERIFIED-NET", "PROVISIONAL-NET"
TOL = 0.0005                                    # m2: the candidate prints 4 decimals
TILE_BED_MAX_M = 0.06                           # owner Q-45: bathroom bed 4-6 cm (the larger floor bed)
TILE_BED_SRC = "owner Q-45 tile bed 3-4 cm floors / 4-6 cm bathrooms (UPC-TILE-BED-001 thickness_m_wet_floor max)"
MAX_OPENING_M = 10.0                            # a width above this is a unit error (mm passed as m), refused
BASIS_LABEL = {"VERIFIED": VNET, "DRAWING_CONFIRMED": PNET, "ASSUMED___OWNER_APPROVED": PNET}
FILL_STATUS = {"VERIFIED": "VERIFIED", "DRAWING-CONFIRMED": "DRAWING_CONFIRMED",
               "ASSUMED - OWNER-APPROVED": "ASSUMED___OWNER_APPROVED"}


class LedgerError(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _pinned(p):
    h = _sha(p)
    if h != PINS[p]:
        raise LedgerError(f"{Path(p).relative_to(ROOT)}: sha256 {h[:8]} is not the pinned {PINS[p][:8]}")
    return h


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ source lines

EID = re.compile(r"^(?P<floor>\w+)-WALLS:walls t=(?P<t>[0-9.]+)(?:#BLOCKWORK:(?P<basis>[A-Z_]+?)_(?P<mat>BLACK|WHITE))?$")


def mas_lines(index):
    """the MAS.BLOCK lines of a candidate line index -> [{line_id, floor, thickness_m, material, basis, label, net}]"""
    out = []
    for ln in index["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        m = EID.match(ln["element_id"])
        if not m:
            raise LedgerError(f"{ln['line_id']}: element id {ln['element_id']!r} is not a masonry line key")
        basis, mat = m.group("basis"), m.group("mat")
        if ln["class"] == "HELD":
            if ln["measured_net"] is not None:
                raise LedgerError(f"{ln['line_id']}: a HELD line carries a figure")
            label = HELD
        else:
            if basis not in BASIS_LABEL:
                raise LedgerError(f"{ln['line_id']}: basis {basis!r} has no material label")
            if ln["measured_net"] is None:
                raise LedgerError(f"{ln['line_id']}: released line with no net (missing is HELD, never 0)")
            label = BASIS_LABEL[basis]
        out.append({"line_id": ln["line_id"], "element_id": ln["element_id"], "floor": m.group("floor"),
                    "thickness_m": float(m.group("t")), "material": mat, "basis": basis, "label": label,
                    "net_m2": ln["measured_net"], "class": ln["class"], "unit": ln["unit"]})
    return sorted(out, key=lambda x: (x["floor"], x["thickness_m"], x["material"] or "", x["basis"] or "", x["line_id"]))


def fill_walls(fill_doc):
    """t279 inputs -> per MAS.BLOCK wall: floor, t, block type, effective status, carried m2, openings"""
    walls = []
    for ln in fill_doc["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        for w in ln["walls"]:
            st, ps = w["status"], w["part_status"]
            eff = ps if st == "ESTABLISHED PART + HELD" else st
            walls.append({"parent_line": ln["line_id"], "floor": ln["floor"], "thickness_m": float(ln["family"]),
                          "wall_id": w["wall_id"], "block_type": w["block_type"], "status": st, "effective": eff,
                          "carried": w["carried"], "openings": w["openings"]})
    return walls


def reconcile(lines, walls):
    """each released split line = the sum of the carried figures of its walls (same floor / t / block type / basis);
    a released wall figure outside every line, or a line that does not close, stops the ledger."""
    rows, used = [], set()
    for ln in lines:
        if ln["label"] == HELD:
            continue
        mine = [w for w in walls if w["floor"] == ln["floor"] and abs(w["thickness_m"] - ln["thickness_m"]) < 1e-9
                and w["block_type"] == ln["material"] and FILL_STATUS.get(w["effective"]) == ln["basis"]
                and w["carried"] is not None and w["status"] != "HELD ON DROP"]
        s = round(sum(w["carried"] for w in mine), 6)
        diff = round(s - ln["net_m2"], 6)
        if abs(diff) > TOL:
            raise LedgerError(f"{ln['line_id']}: walls sum {s} m2 vs line {ln['net_m2']} m2 (diff {diff})")
        for w in mine:
            used.add((w["floor"], w["wall_id"]))
        rows.append({"line_id": ln["line_id"], "walls": [w["wall_id"] for w in mine], "walls_sum_m2": s,
                     "line_net_m2": ln["net_m2"], "residual_m2": diff,
                     "established_parts": [w["wall_id"] for w in mine if w["status"] == "ESTABLISHED PART + HELD"]})
    stray = [(w["floor"], w["wall_id"]) for w in walls if w["carried"] is not None and w["status"] != "HELD ON DROP"
             and (w["floor"], w["wall_id"]) not in used]
    if stray:
        raise LedgerError(f"released wall figures in no split line: {stray}")
    return rows


# ------------------------------------------------------------------------------------------------ block materials

def _mortar(ln, mortar_rows):
    """installed joint mortar m3 of the line from the merged T-367 ledger (10 mm joint, 40 x 20 module) -> cement /
    sand by UPC-BLACK-MORTAR-001 (Q-78 1:4). The 0.15 m black face is not stated: its joint geometry, hence its
    mortar, is HELD (the T-367 figure beside). Procurement mortar (waste, dry factor) is HELD: no sourced value."""
    rec = C.record("UPC-BLACK-MORTAR-001")["params"]
    out = {"rule": "R-T453-3 / UPC-BLACK-MORTAR-001", "per_m3_of_mortar": {
        "cement_bags_50kg": rec["cement_bags_per_m3"]["value"], "sand_m3_loose": rec["loose_sand_m3_per_m3"]["value"],
        "mix": rec["mix_cement_sand"]["value"]}, "procurement": HELD,
        "procurement_why": "waste / dry-volume factor not sourced: procurement mortar HELD"}
    r = mortar_rows.get(ln["line_id"])
    if r is None or r["mortar_installed_m3"].strip() == "":
        return dict(out, status=HELD, label=HELD, why="no installed joint-mortar volume for this line (T-367): HELD")
    m3 = float(r["mortar_installed_m3"])
    if abs(float(r["area_m2 (established)"]) - ln["net_m2"]) > TOL:
        raise LedgerError(f"{ln['line_id']}: T-367 mortar area {r['area_m2 (established)']} != line {ln['net_m2']}")
    calc = C.black_block_laying_materials(m3)
    beside = {"mortar_installed_m3": _r(m3), "cement_bags": _r(calc["cement_bags"]),
              "sand_m3_loose": _r(calc["sand_m3_loose"])}
    if abs(ln["thickness_m"] - 0.20) > 1e-9:
        return dict(out, status=HELD, label=HELD, beside_t367_40x20=beside,
                    why="the 0.15 m black block face / module is not stated (owner 2026-11-02 data item): its joint "
                        "volume is not established; the T-367 40 x 20 figure is beside only (never 0)")
    return dict(out, status="COMPUTED", label=PNET, unit="m3 / bags / m3", source_t367=r["mortar_or_adhesive_status"],
                mortar_installed_m3=_r(m3), mortar_per_m2=_r(m3 / ln["net_m2"], 8), cement_bags=_r(calc["cement_bags"]),
                sand_m3_loose=_r(calc["sand_m3_loose"]),
                label_why="the 10 mm joint is an owner PROVISIONAL input (T-367, owner 2026-10-29): PROVISIONAL-NET "
                          "even on a VERIFIED area")


def block_materials(ln, mortar_rows=None):
    """one MAS.BLOCK line -> its material rows (theoretical; procurement only with a sourced waste)."""
    mortar_rows = mortar_rows or {}
    area = ln["net_m2"] if ln["label"] != HELD else None
    base = {"line_id": ln["line_id"], "element_id": ln["element_id"], "source_label": ln["label"],
            "net_m2": area, "thickness_m": ln["thickness_m"], "material_type": ln["material"]}
    out = []
    if ln["label"] == HELD:
        why = "source line HELD (parent blank: its held walls / pieces are named in the candidate), never 0"
        for item in ("BLOCK_COUNT", "LAYING_MATERIAL"):
            out.append(dict(base, item=item, status=HELD, label=HELD, why=why))
        return out
    if ln["material"] == "BLACK":
        b = C.black_blocks(area, ln["thickness_m"])
        if b["status"] == C.OK:
            out.append(dict(base, item="BLOCK_COUNT", rule="R-T453-1 / " + b["rule"], status="COMPUTED",
                            label=ln["label"], unit="nr", blocks_per_m2=b["blocks_per_m2"], module_m=b["module_m"],
                            module_basis=b["module_basis"], theoretical_count=_r(b["theoretical_count"]),
                            breakage=HELD, procurement_count=None,
                            procurement_why="no sourced breakage / waste value (UPC-BLACK-BLOCK-001 waste null): "
                                            "procurement HELD, the theoretical count is not rounded or uplifted"))
        else:
            out.append(dict(base, item="BLOCK_COUNT", rule="R-T453-1 / " + b["rule"], status=HELD, label=HELD,
                            why=b["why"], flag="15 cm black block face: data item (owner 2026-11-02)"))
        out.append(dict(base, item="LAYING_MATERIAL", material="black-block mortar 1:4", **_mortar(ln, mortar_rows)))
    elif ln["material"] == "WHITE":
        g = C.aac_bond_bags([{"id": ln["line_id"], "net_area_m2": area, "thickness_m": ln["thickness_m"]}])
        row = g["rows"][0]
        if row["status"] == C.OK:
            out.append(dict(base, item="LAYING_MATERIAL", material="white AAC glue", rule="R-T453-2 / " + g["rule"],
                            status="COMPUTED", label=ln["label"], unit="kg", kg_per_m2=row["kg_per_m2"],
                            consumption_kg=_r(row["consumption"]), bags_25kg_net=_r(row["consumption"] / 25.0),
                            procurement="rounded once per purchasing group (see glue_groups)"))
        else:
            out.append(dict(base, item="LAYING_MATERIAL", material="white AAC glue", status=HELD, label=HELD,
                            why=row["why"]))
        out.append(dict(base, item="BLOCK_COUNT", rule="R-T453-1", status=HELD, label=HELD,
                        why="white AAC block face not selected by the project: the owner's supplier sheet (Q-60) "
                            "lists 62.5 x 25 (6.4 / m2) and 60 x 20 (8.33 / m2); the company rules give no AAC count "
                            "rule: HELD, never the black 12.5 / m2",
                        alternatives_beside={"62.5x25": _r(area * 6.4), "60x20": _r(area / (0.60 * 0.20))}))
    else:
        raise LedgerError(f"{ln['line_id']}: released line with no block type")
    return out


def glue_groups(lines):
    """25 kg glue bags once per purchasing group. The PROJECT group holds every masonry line: a held line (its
    colour not split) holds the group; the known parts per label are stated as fractional bags, never rounded."""
    rows = []
    for ln in lines:
        if ln["label"] == HELD:
            rows.append({"id": ln["line_id"], "net_area_m2": None, "thickness_m": ln["thickness_m"]})
        elif ln["material"] == "WHITE":
            rows.append({"id": ln["line_id"], "net_area_m2": ln["net_m2"], "thickness_m": ln["thickness_m"]})
    g = C.aac_bond_bags(rows)["groups"]["PROJECT"]
    known = {}
    for ln in lines:
        if ln["label"] != HELD and ln["material"] == "WHITE":
            k = known.setdefault(ln["label"], {"m2": 0.0, "kg": 0.0})
            k["m2"] += ln["net_m2"]
            k["kg"] += ln["net_m2"] * float(C.param("UPC-AAC-GLUE-001", "kg_per_m2_by_thickness_m")["value"]
                                            [f"{ln['thickness_m']:.2f}"])
    return {"PROJECT": {"status": g["status"], "bags_to_buy": g.get("bags_to_buy"), "held_lines": g["held_rows"],
                        "known_kg": _r(g["consumption_known"]), "why": g.get("why")},
            "known_part_by_label": {k: {"m2": _r(v["m2"]), "kg": _r(v["kg"]), "bags_25kg_net": _r(v["kg"] / 25.0)}
                                    for k, v in sorted(known.items())}}


def block_totals(mats):
    tot = {}
    for m in mats:
        if m["item"] == "BLOCK_COUNT" and m["status"] == "COMPUTED":
            t = tot.setdefault(m["label"], {"m2": 0.0, "blocks": 0.0, "lines": 0})
            t["m2"] += m["net_m2"]
            t["blocks"] += m["theoretical_count"]
            t["lines"] += 1
    held = [m["line_id"] for m in mats if m["item"] == "BLOCK_COUNT" and m["status"] == HELD]
    return {"black_0_20_by_label": {k: {"m2": _r(v["m2"]), "theoretical_blocks": _r(v["blocks"]),
                                        "lines": v["lines"]} for k, v in sorted(tot.items())},
            "held_count_lines": held, "procurement": HELD,
            "note": "VERIFIED-NET and PROVISIONAL-NET are never summed into one figure; the held lines are not 0"}


# ------------------------------------------------------------------------------------------------ lintels

PIECE = re.compile(r"([0-9.]+) x ([0-9.]+)")


def pieces(formula):
    """'[a x h + b x h2] - [...]' -> [(length, clear height)] of the drawn pieces; None when no piece is drawn."""
    if not formula or not formula.startswith("["):
        return None
    head = formula[1:formula.index("]")]
    out = [(float(a), float(b)) for a, b in PIECE.findall(head)]
    return out or None


def schedule_rows(rows):
    out = []
    for r in rows:
        if r["RECORD"] != "SCHEDULE_ROW":
            continue
        out.append({"row": r["ROW_ID"], "lo_mm": float(r["WIDTH_LO_CM"]) * 10, "hi_mm": float(r["WIDTH_HI_CM"]) * 10,
                    "d_m": float(r["D_CM"]) / 100.0, "bottom": r["BOTTOM_PRINTED"], "top": r["TOP_PRINTED"],
                    "stirrups": r["STIRRUPS_PRINTED"]})
    bearing = [r for r in rows if r["RECORD"] == "DETAIL_READING" and r["ROW_ID"] == "MIN-BEARING"]
    if not out or len(bearing) != 1:
        raise LedgerError("the lintel schedule needs its rows and one MIN-BEARING detail reading")
    m = re.search(r"(\d+(?:\.\d+)?)\s*cm", bearing[0]["WIDTH_PRINTED"])
    return out, float(m.group(1)) / 100.0


def band(width_m, rows):
    mm = round(width_m * 1000.0, 3)
    for r in rows:
        if r["lo_mm"] - 1e-6 <= mm <= r["hi_mm"] + 1e-6:
            return r, None
    if mm > max(r["hi_mm"] for r in rows):
        return None, f"opening {width_m} m is above the last printed band ({max(r['hi_mm'] for r in rows) / 1000} m)"
    return None, f"opening {width_m} m falls in an unprinted interval between two bands (integer-cm bounds)"


OPID = re.compile(r"^([A-Z]+-?[A-Z0-9]*-?\d+|W\d+)\s")


def wall_openings(walls):
    out = []
    for w in walls:
        for part in (w["openings"] or "").split(";"):
            part = part.strip()
            if not part:
                continue
            oid = part.split()[0]
            out.append({"opening_id": oid, "host": w["wall_id"], "floor": w["floor"], "wall_t_m": w["thickness_m"],
                        "block_type": w["block_type"], "wall_status": w["status"], "fill_state": part.split()[-1]})
    return out


def lintel_row(op, census, wall_pieces, rows, bearing_m):
    """one opening in a masonry wall -> one lintel decision and its quantities (theoretical)."""
    rec = dict(op, rule="R-T453-4")
    c = census.get(op["opening_id"])
    if c is None:
        return dict(rec, decision=HELD, why="opening not in the opening census r3 (width unknown)")
    w = None if c["WIDTH_M"].strip() == "" else float(c["WIDTH_M"])
    rec.update(kind=c["KIND"], width_m=w, width_basis=c["WIDTH_BASIS"])
    if w is None:
        return dict(rec, decision=HELD, why="opening width not established (never 0)")
    if not 0 < w < MAX_OPENING_M:
        raise LedgerError(f"{op['opening_id']}: width {w} is not a width in metres")
    bnd, bwhy = band(w, rows)
    if bnd is None:
        return dict(rec, decision=FLAGGED, why=bwhy + ": cast-in-situ design item, never forced into a band")
    rec.update(schedule_row=bnd["row"], section_m=[op["wall_t_m"], bnd["d_m"]], bottom=bnd["bottom"], top=bnd["top"],
               stirrups=bnd["stirrups"])
    h, s = c["HEIGHT_M"].strip(), c["SILL_M"].strip()
    if h == "" or s == "" or c["HEIGHT_STATUS"].strip() == "HELD":
        return dict(rec, decision=HELD, why="opening head not established (height / sill HELD in the census): whether "
                                           "masonry is built above it is not known; at most 1 lintel")
    head = round(float(h) + float(s), 6)
    rec.update(head_above_ffl_m=head, head_basis=c["HEIGHT_STATUS"])
    if op["fill_state"] != "DEDUCTED":
        return dict(rec, decision=HELD, why=f"opening is {op['fill_state']} in the merged fill: the drawn pieces do "
                                           f"not cover it, the clear height above its head is not known; at most 1")
    pcs = wall_pieces.get((op["floor"], op["host"]))
    if not pcs:
        return dict(rec, decision=HELD, why="host wall has no drawn pieces with a printed soffit (wall HELD): the "
                                           "clear height above the head is not known; at most 1 lintel")
    hs = [p[1] for p in pcs]
    need = bnd["d_m"] + TILE_BED_MAX_M
    m_lo, m_hi = round(min(hs) - head, 6), round(max(hs) - head, 6)
    rec.update(clear_heights_m=sorted(set(hs)), margin_min_m=m_lo, margin_max_m=m_hi,
               margin_rule=f"clear height (structural top -> soffit) - head (above FFL) >= D {bnd['d_m']} + "
                           f"{TILE_BED_MAX_M} m ({TILE_BED_SRC})")
    if m_hi < bnd["d_m"]:
        return dict(rec, decision=FLAGGED, why="no piece leaves room for the band depth above the head: the beam / "
                                              "slab serves the opening or the head conflicts with it (designer)")
    if m_lo < need:
        return dict(rec, decision=FLAGGED, why="the head leaves room for the lintel under some pieces only (or only "
                                              "without the floor bed): which piece is over the opening is not read")
    L = round(w + 2 * bearing_m, 6)
    B, D = op["wall_t_m"], bnd["d_m"]
    rec.update(decision="REQUIRED", count=1, label=PNET, type="CAST-IN-SITU RC (project LINTEL SCHEDULE, level 1)",
               bearing_m=bearing_m, length_m=L, concrete_m3=_r(B * D * L), formwork_m2=_r(2 * D * L + B * w),
               rebar_kg=HELD, rebar_why="bar cover, bend / anchorage lengths not printed (detail): kg HELD",
               stirrups_per_m=5, open_checks=["bearing availability (MIN 40 cm) at both jambs not measured",
                                              "jamb against an RC column: connection not approved / not read"])
    if op["block_type"] == "WHITE":
        alt = C.lintel(w, bearing={"m": bearing_m, "source": "project LINTEL DETAIL 'MIN.40cm' (S8.6 transcription)"})
        rec["precast_alternative_beside"] = {k: alt.get(k) for k in ("status", "required_m", "piece_m", "count",
                                                                     "why", "rule")}
        rec["conflict"] = ("F-T453-1: owner practice (Q-60) uses a white precast atab in AAC walls; the project prints "
                           "an RC lintel schedule for block walls; the project document governs (level 1), the "
                           "precast piece is beside only")
    return rec


def lintel_ledger(walls, census, register, rows, bearing_m):
    wall_pieces = {}
    for e in register["entries"]:
        if e.get("item_code") == "MAS.BLOCK":
            p = pieces((e.get("rule_result") or {}).get("formula"))
            if p:
                wall_pieces[(e["floor"], e["element_id"])] = p
    ops = wall_openings(walls)
    seen = {}
    for o in ops:
        if o["opening_id"] in seen:
            raise LedgerError(f"opening {o['opening_id']} hosted twice ({seen[o['opening_id']]} and {o['host']})")
        seen[o["opening_id"]] = o["host"]
    out = [lintel_row(o, census, wall_pieces, rows, bearing_m) for o in sorted(ops, key=lambda x: x["opening_id"])]
    not_hosted = []
    for k in sorted(census):
        if k in seen:
            continue
        above = sorted(w["wall_id"] for w in walls if re.search(rf"(^|\s){re.escape(k)}(\s|$)", w["wall_id"]))
        not_hosted.append({"opening_id": k, "kind": census[k]["KIND"],
                           "why": (f"masonry panel above it ({', '.join(above)}) is in the fill: a lintel or a beam "
                                   f"carries that panel; support type and head HELD (never 0)") if above else
                                  "not hosted by any masonry wall of the merged fill (RC / glazing line / gate / "
                                  "unresolved): no lintel from this ledger"})
    summ = {"openings_in_masonry": len(out)}
    for dec in ("REQUIRED", HELD, FLAGGED):
        summ[dec] = sum(1 for r in out if r["decision"] == dec)
    req = [r for r in out if r["decision"] == "REQUIRED"]
    summ["required_concrete_m3"] = _r(sum(r["concrete_m3"] for r in req))
    summ["required_formwork_m2"] = _r(sum(r["formwork_m2"] for r in req))
    by = {}
    for r in req:
        k = f"{r['floor']} {r['schedule_row']} {r['section_m'][0]:.2f}x{r['section_m'][1]:.2f} L={r['length_m']:.2f}"
        by[k] = by.get(k, 0) + 1
    summ["required_by_type"] = dict(sorted(by.items()))
    summ["label"] = PNET
    summ["held_never_0"] = "HELD and FLAGGED openings carry no count or volume: not 0"
    return out, {"census_openings_not_in_a_masonry_wall": not_hosted, "summary": summ}


# ------------------------------------------------------------------------------------------------ build

def mortar_totals(mats):
    tot, held = {"m3": 0.0, "cement_bags": 0.0, "sand_m3_loose": 0.0, "lines": 0}, []
    for m in mats:
        if m.get("material") != "black-block mortar 1:4":
            continue
        if m["status"] == "COMPUTED":
            tot["m3"] += m["mortar_installed_m3"]
            tot["cement_bags"] += m["cement_bags"]
            tot["sand_m3_loose"] += m["sand_m3_loose"]
            tot["lines"] += 1
        else:
            held.append(m["line_id"])
    return {"black_0_20_provisional_net": {k: (_r(v) if k != "lines" else v) for k, v in tot.items()},
            "held_lines": held, "procurement": HELD, "label": PNET}


def build_from(index, fill_doc, register, census_rows, schedule_csv_rows, mortar_csv_rows=()):
    lines = mas_lines(index)
    walls = fill_walls(fill_doc)
    rec = reconcile(lines, walls)
    mrows = {r["part_line_id_v3026"]: r for r in mortar_csv_rows if r["part_line_id_v3026"].startswith("L-")}
    mats = [m for ln in lines for m in block_materials(ln, mrows)]
    rows, bearing = schedule_rows(schedule_csv_rows)
    census = {r["ID"]: r for r in census_rows}
    lints, lint_extra = lintel_ledger(walls, census, register, rows, bearing)
    return {"schema": SCHEMA, "candidate": index.get("candidate_version"), "rulebook": C.METHOD + " " + C.VERSION,
            "rulebook_digest": C.digest(), "source_lines": lines, "reconciliation": rec, "block_materials": mats,
            "block_totals": block_totals(mats), "glue_groups": glue_groups(lines),
            "mortar": mortar_totals(mats),
            "lintels": lints, "lintel_reconciliation": lint_extra,
            "not_in_part_1": {"mesh_strip_m": "B9-03 (Q-77 optional item) is T-363's integration; no calculator in "
                                              "COMPANY_RULEBOOK_V1", "column_ties_pcs": "same (Q-77)"}}


def build():
    hashes = {str(p.relative_to(ROOT)): _pinned(p) for p in PINS}
    import t279_inputs as L26
    index = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    if index["inputs"]["lines"] != CANDIDATE_LINES_SHA or index["candidate_version"] != CANDIDATE:
        raise LedgerError("the line index is not the candidate of record V3.0.45")
    out = build_from(index, L26.build(), json.loads(REGISTER.read_text(encoding="utf-8")),
                     list(csv.DictReader(OPENINGS.open(encoding="utf-8", newline=""))),
                     list(csv.DictReader(SCHEDULE.open(encoding="utf-8", newline=""))),
                     list(csv.DictReader(MORTAR.open(encoding="utf-8", newline=""))))
    out["inputs"] = dict(hashes, candidate_lines_sha256=CANDIDATE_LINES_SHA, fill="t279_inputs.build() (pinned)")
    return out


def write(ledger, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "MATERIAL_LEDGER_T453.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    cols = ["line_id", "element_id", "item", "material", "source_label", "label", "status", "net_m2", "thickness_m",
            "theoretical_count", "consumption_kg", "bags_25kg_net", "why"]
    with (out_dir / "BLOCK_MATERIALS_T453.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        wr.writeheader()
        for m in ledger["block_materials"]:
            wr.writerow(m)
    cols = ["opening_id", "floor", "host", "block_type", "wall_t_m", "kind", "width_m", "head_above_ffl_m",
            "margin_min_m", "margin_max_m", "schedule_row", "decision", "length_m", "concrete_m3", "formwork_m2",
            "why"]
    with (out_dir / "LINTELS_T453.csv").open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        wr.writeheader()
        for m in ledger["lintels"]:
            wr.writerow(m)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    led = build()
    write(led, argv[0] if argv else HERE / "out")
    print(json.dumps({"block_totals": led["block_totals"], "glue_groups": led["glue_groups"], "mortar": led["mortar"],
                      "lintels": led["lintel_reconciliation"]["summary"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
