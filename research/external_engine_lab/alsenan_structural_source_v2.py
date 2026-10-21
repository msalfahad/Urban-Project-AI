"""ALSENAN structural schedule source reader V2 - DEFINITIONS ONLY (control-plane round 2).

ST7757.dxf carries its schedules as attributed blocks (ATTRIB values). This adapter reads every schedule block and
every reinforcement text with full provenance (drawing, block, insert handle, attribute tag, raw value, normalised
value, position) through engine.source.schedule_grammar, and builds typed definitions:

    CONTINUOUS_BEAM  C-BEAM2 / C-BEAM3   B, H, spans, bottom bars per span, support (MID) bars, stirrups / m per span;
                                         T/M-n = design LOAD (t/m), never reinforcement
    SIMPLE_BEAM      SBT (B*, CA, B.W)   B, H, bottom, top, stirrups / m (+ REMARKS side-bar text, tokens only)
    STRAP_BEAM       SBT (SB*)           as simple beams; duplicate keys -> SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY
    FOOTING          FT                  one layer; BOXED raw value kept, interpretation BLOCKED_SEMANTICS
    FOOTING_2_LAYER  FTB                 TOP / BOTTOM x short / long, bars per metre
    COLUMN           CGT                 per storey band B, H, bar count, diameter; LOAD = design load
plus loose texts (planted columns, (T&B), section B-B bars, slab annotations) and the PDF-only typical details
(pp. 8, 14, 15, 16) as accounted BLOCKED_UNREAD objects.

Nothing here feeds a released quantity: every definition carries consumer_state, and the rebar consumers for
CB / straps / per-metre footings are pending (Round 3).
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from engine.source import schedule_grammar as SG

ROOT = Path(__file__).resolve().parents[2]
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DRAWING = "ST7757.dxf"
BLOCK_PAGE = {"FT": 9, "FTB": 9, "CGT": 9, "SBT": 10, "C-BEAM2": 11, "C-BEAM3": 12}
SCHEDULE_BLOCKS = tuple(BLOCK_PAGE)
LOOSE = re.compile(r"%%c|P\.C|T&B|/\d+cm", re.I)
PDF_ONLY = [
    ("PDF:p8:RECOMMENDATIONS", 8, "RECOMMENDATIONS notes 1-24", "raster image; no machine-readable text"),
    ("PDF:p13:LINTEL_SCHEDULE", 13, "lintel detail + schedule", "vector glyphs; consumed by hand transcription "
                                                               "(LINTELS table in alsenan_v3_structure)"),
    ("PDF:p13:GROUND_BEAM_SECTIONS", 13, "ground beam sections", "vector glyphs; hand transcription"),
    ("PDF:p14:LIFT_FOOTING", 14, "lift with isolated footing (FF)", "vector glyphs; no text layer"),
    ("PDF:p14:BOUNDARY_WALL_PARAPETS", 14, "boundary wall + parapets", "vector glyphs; hand transcription"),
    ("PDF:p15:TEMPERATURE_REINFORCEMENT", 15, "temperature reinforcement detail", "vector glyphs; no text layer"),
    ("PDF:p15:PLANTED_COLUMN_DETAIL", 15, "planted column detail", "vector glyphs; no text layer"),
    ("PDF:p15:TYPICAL_DETAILS", 15, "twisted column / beam in casement / slab on beams", "vector glyphs"),
    ("PDF:p16:STAIR_STEEL_LAYOUT", 16, "stair beam + stair steel layout", "vector glyphs; no text layer"),
    ("PDF:p16:OPENING_IN_BEAM_RIBS", 16, "opening in beam, ribs / torsion", "vector glyphs"),
]


def _xy(p):
    return [round(p.x, 1), round(p.y, 1)]


def read(path: Path = DXF) -> dict:
    import ezdxf
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    out = {"drawing": DRAWING, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "blocks": {}, "loose": [],
           "fragments": []}
    for b in SCHEDULE_BLOCKS:
        rows = []
        for i in msp.query(f'INSERT[name=="{b}"]'):
            cells = [SG.cell(b, i.dxf.handle, a.dxf.tag, a.dxf.text, drawing=DRAWING, layer=i.dxf.layer,
                             position=_xy(a.dxf.insert), page=BLOCK_PAGE[b]) for a in i.attribs]
            rows.append({"block": b, "handle": i.dxf.handle, "layer": i.dxf.layer, "insert": _xy(i.dxf.insert),
                         "attribute_y": round(min(a.dxf.insert.y for a in i.attribs), 1),
                         "attributes": {c["tag"]: c["raw"] for c in cells}, "cells": cells})
        out["blocks"][b] = sorted(rows, key=lambda r: (-r["insert"][1], r["insert"][0]))
    for e in msp.query("TEXT MTEXT"):
        t = (e.dxf.text if e.dxftype() == "TEXT" else e.text) or ""
        rec = {"handle": e.dxf.handle, "layer": e.dxf.layer, "raw": t.strip(), "normalised": SG.normalise(t),
               "position": _xy(e.dxf.insert)}
        if SG.normalise(t) == "Ø":
            out["fragments"].append(rec)
        elif LOOSE.search(t):
            out["loose"].append(rec)
    out["loose"].sort(key=lambda r: (r["layer"], r["raw"], r["handle"]))
    out["fragments"].sort(key=lambda r: r["handle"])
    return out


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _bar(row, cb, cd):
    a = row["attributes"]
    r = SG.bar_from_cells(a.get(cb, ""), a.get(cd, ""))
    r["tags"] = [cb, cd]
    return r


def _def(row, element, key, fields, interpretation, notes=None, consumer_state="PENDING_REBAR_CONSUMER_V2"):
    return {"element": element, "type": key, "drawing": DRAWING, "page": BLOCK_PAGE[row["block"]],
            "block": row["block"], "insert_handle": row["handle"], "insert": row["insert"], "fields": fields,
            "raw_attributes": row["attributes"], "interpretation_state": interpretation,
            "consumer_state": consumer_state, "notes": notes or []}


def definitions(src) -> dict:
    """Typed definitions + source conflicts. A definition is INTERPRETED when every reinforcement field parsed,
    PARTIALLY_INTERPRETED when some fields stay BLOCKED_INTERPRETATION, CONFLICT when its key is duplicated."""
    out, conflicts = [], []
    remarks = {}
    sbt = src["blocks"].get("SBT", [])
    xmax = max((r["insert"][0] for r in sbt), default=0.0)
    for t in src["loose"]:
        if t["layer"] == "S-TEXT.SCH" and re.search(r"/\d+cm", t["raw"]) and t["position"][0] > xmax and sbt:
            row = min(sbt, key=lambda r: abs(r["attribute_y"] - t["position"][1]))
            remarks[row["handle"]] = t
    # ---- continuous beams
    for blk in ("C-BEAM2", "C-BEAM3"):
        n = int(blk[-1])
        for row in src["blocks"].get(blk, []):
            a = row["attributes"]
            spans = [_num(a.get(f"L{i}-M")) for i in range(1, n + 1)]
            bottom = [_bar(row, f"BOT{i}-B", f"BOT{i}-D") for i in range(1, n + 1)]
            stir = [_bar(row, f"STR{i}-B", f"STR{i}-D") for i in range(1, n + 1)]
            mids = {}
            for k in (["MID"] if n == 2 else ["MID1", "MID2"]):
                mids[f"support_{k}"] = _bar(row, f"{k}-B", f"{k}-D")
            for s in stir:
                s["semantics"] = "STIRRUPS_PER_METRE (schedule header)"
            fields = {"B_cm": _num(a.get("W")), "H_cm": _num(a.get("H")), "spans_m": spans,
                      "design_load_t_per_m": {k: a[k] for k in a if k.startswith("T/M")},
                      "bottom_bars_per_span": bottom, "support_top_bars": mids, "stirrups_per_span": stir,
                      "continuous_top_bars": {"state": "BLOCKED_INTERPRETATION",
                                              "why": "drawn as split TEXT fragments (count / Ø / diameter) in the "
                                                     "schedule frame; proximity assembly not verified"},
                      "side_bars": {"state": "BLOCKED_INTERPRETATION",
                                    "why": "split text '2Ø12' + '30cm' in the schedule frame; binding to a beam row "
                                           "not verified"}}
            empty = [k for k, v in mids.items() if v["grammar"] == "EMPTY"]
            bad = [b for b in bottom + stir + list(mids.values()) if b["grammar"] == "UNPARSED"]
            notes = ["T/M-n are design loads (t/m), NOT reinforcement"]
            if empty:
                notes.append(f"support bar cell(s) empty in source: {empty}")
            out.append(_def(row, "CONTINUOUS_BEAM", a.get("BEAM-NAME"), fields,
                            "PARTIALLY_INTERPRETED" if not bad else "BLOCKED_INTERPRETATION", notes))
    # ---- simple / strap beams
    for row in sbt:
        row["_key"] = row["attributes"]["BEAM"]
    for c in SG.key_conflicts(sbt, "_key"):
        conflicts.append(dict(c, element="STRAP_BEAM" if c["key"].startswith("SB") else "SIMPLE_BEAM",
                              consequence="every quantity depending on this key's dimensions or bars is BLOCKED; no "
                                          "row is selected (not by geometry, not by order)"))
    ckeys = {c["key"] for c in conflicts}
    for row in sbt:
        a = row["attributes"]
        key = a["BEAM"]
        el = "STRAP_BEAM" if key.startswith("SB") else "SIMPLE_BEAM"
        fields = {"B_cm": _num(a.get("W")), "H_cm": _num(a.get("H")), "bottom": _bar(row, "BOT-B", "BOT-D"),
                  "top": _bar(row, "TOP-B", "TOP-D"), "stirrups_per_m": _bar(row, "STI-B", "D")}
        fields["stirrups_per_m"]["semantics"] = "STIRRUPS_PER_METRE (schedule header)"
        rm = remarks.get(row["handle"])
        if rm:
            p = SG.parse_bar(rm["raw"])
            p.update(text_handle=rm["handle"], position=rm["position"],
                     interpretation="CANDIDATE: side bars, count per level at the printed vertical spacing - the "
                                    "count / face semantics need the typical detail",
                     interpretation_state="TOKENS_PARSED_SEMANTICS_CANDIDATE")
            fields["remarks_side_bars"] = p
        state = "CONFLICT" if key in ckeys else "INTERPRETED"
        out.append(_def(row, el, key, fields, state,
                        consumer_state=("ACTIVE (alsenan_v3_structure.beam_rebar)" if el == "SIMPLE_BEAM" else
                                        "PENDING_REBAR_CONSUMER_V2")))
    # ---- footings
    for row in src["blocks"].get("FT", []):
        a = row["attributes"]
        boxed = a.get("BOXED", "")
        fields = {"L_cm": _num(a.get("W")), "W_cm": _num(a.get("H")), "D_cm": _num(a.get("DEPHT")),
                  "short_bars": _bar(row, "SH-B", "SH-D"), "long_bars": _bar(row, "LO-B", "LO-D"),
                  "boxed": {"raw_boxed_value": boxed, "interpretation": "BLOCKED_SEMANTICS" if boxed else
                            "NOT_PRINTED"}}
        out.append(_def(row, "FOOTING", a["FO-TY"], fields,
                        "PARTIALLY_INTERPRETED" if boxed else "INTERPRETED",
                        ["BOXED value captured raw; its meaning (e.g. starter / box bars) is not established"]
                        if boxed else [], consumer_state="ACTIVE (alsenan_v3_structure.footing_rebar)"))
    for row in src["blocks"].get("FTB", []):
        a = row["attributes"]
        fields = {"L_cm": _num(a.get("W")), "W_cm": _num(a.get("H")), "D_cm": _num(a.get("DEPHT")),
                  "TOP_short": _bar(row, "SH-T-B", "SH-T-D"), "TOP_long": _bar(row, "LO-T-B", "LO-T-D"),
                  "BOTTOM_short": _bar(row, "SH-B-B", "SH-B-D"), "BOTTOM_long": _bar(row, "LO-B-B", "LO-B-D"),
                  "layer_labels": {"BOXED-T": a.get("BOXED-T"), "BOXED-B": a.get("BOXED-B")}}
        notes = ["two-layer footing: all four bar fields are bars PER METRE"]
        if a["FO-TY"] == "FF":
            notes.append("FF = lift footing (REMARKS, legacy Arabic text in the PDF); see p.14")
        out.append(_def(row, "FOOTING_2_LAYER", a["FO-TY"], fields, "INTERPRETED", notes))
    # ---- columns
    for row in src["blocks"].get("CGT", []):
        a = row["attributes"]
        bands = {}
        for band in ("FOU", "GR", "1ST", "2ND"):
            if a.get(f"{band}.W"):
                bands[band] = {"B_cm": _num(a.get(f"{band}.W")), "H_cm": _num(a.get(f"{band}.H")),
                               "bars": _bar(row, f"{band}.R", f"{band}.D")}
        out.append(_def(row, "COLUMN", a["COL-T"], {"bands": bands, "design_load": a.get("LOAD")}, "INTERPRETED",
                        ["LOAD is a design load, not reinforcement"],
                        consumer_state="ACTIVE (alsenan_v3_structure.column_rebar via A3 library)"))
    return {"definitions": out, "conflicts": conflicts, "remarks_bound": len(remarks)}


LOOSE_RULES = [
    # (layer, raw-pattern, object, coverage, interpretation, consumer, population, why)
    ("S-TEXT-SLAB", r"^P\.C 20x70$", "PLANTED_COLUMN 20x70", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "PLANTED_COLUMN", "planted column label captured; its occurrence and bars (10Ø16 nearby) are "
                                      "not bound"),
    ("S-TEXT-SLAB", r"^P\.C 20x50$", "PLANTED_COLUMN 20x50", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "PLANTED_COLUMN", "planted column label captured (x2); bars (8Ø16 nearby) not bound"),
    ("S-TEXT-SLAB", r"^10%%C16$", "PLANTED_COLUMN bars 10Ø16", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "PLANTED_COLUMN", "bar text near P.C 20x70; binding not verified"),
    ("S-TEXT-SLAB", r"^8%%C16$", "PLANTED_COLUMN bars 8Ø16", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "PLANTED_COLUMN", "bar text near P.C 20x50; binding not verified"),
    ("S-TEXT-SLAB", r"^\(T&B\)$", "(T&B) qualifier", "CONSUMED_PARTIAL", "CANDIDATE_TOP_AND_BOTTOM",
     "NO_CONSUMER", "SLAB_2F", "standard notation TOP_AND_BOTTOM; the bar it qualifies is not bound - no multiplication"),
    ("S-TEXT-SLAB", r"^11%%C18$", "SECTION B-B bars 11Ø18", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "SECTION_B_B_MEMBER", "section bar text; member not bound"),
    ("S-TEXT-SLAB", r"^3%%C18$", "SECTION B-B bars 3Ø18", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "NO_CONSUMER", "SECTION_B_B_MEMBER", "section bar text; member not bound"),
    ("S-TEXT.D", r"ST\. OF COLUMN", "column ties 6Ø8/m", "CONSUMED_COMPLETE", "INTERPRETED", "ACTIVE",
     "COLUMN", "column ties (alsenan_v3_structure.column_rebar)"),
    ("S-TEXT.SCH", r"/\d+cm$", "simple-beam REMARKS side bars", "CONSUMED_PARTIAL",
     "TOKENS_PARSED_SEMANTICS_CANDIDATE", "PENDING_REBAR_CONSUMER_V2", "BEAM_SIDE_BARS",
     "captured as typed tokens on the beam definition; not added to quantities"),
    ("S-TEXT.SCH", r"^2%%C12$", "CB schedule side-bar fragment 2Ø12", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "PENDING_REBAR_CONSUMER_V2", "CONTINUOUS_BEAM", "split fragment inside a CB schedule frame"),
    ("S-TEXT-SLAB", r"/m", "slab panel bar annotation", "CONSUMED_PARTIAL", "INTERPRETED", "ACTIVE (V3b slab binding)",
     "SLAB", "per-metre slab bars bound to panels by the V3b slab binder where possible"),
    ("S-TITLE TEXT", r"/m", "slab bar annotation (title layer)", "CONSUMED_PARTIAL", "INTERPRETED",
     "ACTIVE (V3b slab binding)", "SLAB", "per-metre slab bars"),
    ("S-TEXT-SLAB", r"(Top|%%C10$|MM/15cm)", "slab top / section bar text", "CONSUMED_PARTIAL",
     "BLOCKED_INTERPRETATION", "NO_CONSUMER", "SLAB", "local top bars / section text; panel binding not verified"),
    ("S-TEXT-CORNER", r".", "slab corner bars", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION", "NO_CONSUMER", "SLAB",
     "corner reinforcement text; panel binding not verified"),
    ("S-TEXT.D", r".", "section / pool / dome detail bar text", "CONSUMED_PARTIAL", "BLOCKED_INTERPRETATION",
     "PARTIAL (V3b pool / dome lanes)", "DETAIL", "detail bar text; used by hand in the V3b pool / dome lanes"),
]


def _loose_rule(t):
    for layer, pat, obj, cov, interp, cons, pop, why in LOOSE_RULES:
        if t["layer"] == layer and re.search(pat, t["raw"], re.I):
            return {"object": obj, "coverage_state": cov, "interpretation_state": interp, "consumer_state": cons,
                    "population": pop, "reason": why}
    return {"object": "unclassified reinforcement text", "coverage_state": "BLOCKED_UNREAD",
            "interpretation_state": "BLOCKED_INTERPRETATION", "consumer_state": "NO_CONSUMER", "population": None,
            "reason": "no rule for this layer / text"}


def coverage(src, defs) -> list:
    """One terminal coverage row per admitted structural source object."""
    rows = []
    dmap = {(d["block"], d["insert_handle"]): d for d in defs["definitions"]}
    ckeys = {c["key"] for c in defs["conflicts"]}
    for blk, recs in sorted(src["blocks"].items()):
        for r in recs:
            d = dmap.get((blk, r["handle"]))
            key = d["type"] if d else None
            if d is None:
                cov, interp = "BLOCKED_UNREAD", "BLOCKED_INTERPRETATION"
            elif key in ckeys:
                cov, interp = "SOURCE_CONFLICT", "CONFLICT"
            elif d["interpretation_state"] == "INTERPRETED":
                cov, interp = "CONSUMED_COMPLETE", "INTERPRETED"
            else:
                cov, interp = "CONSUMED_PARTIAL", d["interpretation_state"]
            unread = [t for t, v in r["attributes"].items() if t.startswith("BOXED") and v and blk == "FT"]
            rows.append({"object_id": f"{DRAWING}:{blk}:{r['handle']}", "object": f"{d['element'] if d else blk} {key}",
                         "source_file": DRAWING, "page": BLOCK_PAGE[blk], "block": blk, "insert_handle": r["handle"],
                         "bbox_anchor": r["insert"], "row_ids": [key], "parser": "alsenan_structural_source_v2",
                         "coverage_state": cov, "interpretation_state": interp,
                         "consumer_state": d["consumer_state"] if d else "NO_CONSUMER",
                         "fields_read": sorted(r["attributes"]), "fields_blocked_semantics": unread,
                         "reason": "; ".join(d["notes"]) if d else "no definition built"})
    for t in src["loose"]:
        rule = _loose_rule(t)
        rows.append({"object_id": f"{DRAWING}:TEXT:{t['handle']}", "object": rule["object"], "source_file": DRAWING,
                     "page": None, "layer": t["layer"], "text": t["raw"], "position": t["position"],
                     "parser": "schedule_grammar.parse_bar", "grammar": SG.parse_bar(t["raw"])["grammar"],
                     "coverage_state": rule["coverage_state"], "interpretation_state": rule["interpretation_state"],
                     "consumer_state": rule["consumer_state"], "population": rule["population"],
                     "reason": rule["reason"]})
    for f in src["fragments"]:
        rows.append({"object_id": f"{DRAWING}:TEXT:{f['handle']}", "object": "split bar-callout fragment 'Ø'",
                     "source_file": DRAWING, "page": None, "layer": f["layer"], "text": f["raw"],
                     "position": f["position"], "parser": "schedule_grammar.normalise", "grammar": "FRAGMENT",
                     "coverage_state": "CONSUMED_PARTIAL", "interpretation_state": "BLOCKED_INTERPRETATION",
                     "consumer_state": "NO_CONSUMER", "population": "CONTINUOUS_BEAM",
                     "reason": "a diameter sign drawn as its own TEXT (count and diameter are separate entities); "
                               "assembly by proximity not verified"})
    for oid, page, title, why in PDF_ONLY:
        consumed = "hand transcription" in why
        rows.append({"object_id": oid, "object": title, "source_file": "ST7757.pdf", "page": page,
                     "parser": "manual (R1 visual review)" if consumed else None,
                     "coverage_state": "CONSUMED_PARTIAL" if consumed else "BLOCKED_UNREAD",
                     "interpretation_state": "PARTIALLY_INTERPRETED" if consumed else "BLOCKED_INTERPRETATION",
                     "consumer_state": "ACTIVE (hand-transcribed table)" if consumed else "NO_CONSUMER",
                     "reason": why})
    return rows
