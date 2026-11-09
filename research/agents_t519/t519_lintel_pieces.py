"""T-519: B9-02 LINTEL PIECES by system and standard length from the measured jamb bearings (research rule proposal
R-T519-1; research only, nothing in engine/ or tools/ imports it; no candidate line moves).

Physical element (ERS s.2.1). One lintel per opening, over the masonry opening, resting on built masonry at both ends.
What a buyer orders depends on the lintel SYSTEM, so the system is decided first, per opening, from the evidence:

  1. A project LINTEL SCHEDULE / DETAIL is printed (level 1, project document) and its scope covers the host wall's block
     type and its width bands cover the opening width -> PROJECT_RC (cast-in-situ to the printed section; the built
     length is w + the two built bearings; there is NO stock length: it is cast to length). The schedule outranks the
     company precast rule (resolution order: drawings before company rules; owner Q-60 standing directive: "engineering
     office rules override urban project rules"; rulebook UPC-LINTEL-001 scope: "a printed structural lintel schedule
     ... governs instead (never both)").
  2. The schedule's scope covers the wall but the width falls in a band gap / above the last band -> HELD
     (SCHEDULE_SILENT): never the nearest band, never the precast rule by default; designer item.
  3. No schedule covers the wall: WHITE (AAC) wall -> OWNER_PRECAST (UPC-LINTEL-001, owner 2026-11-02; Q-60 atab only
     for white blocks); BLACK wall -> HELD (the company rule says black walls take black precast or RC "as the drawings
     require": the drawings are silent, so the system is not established; never assumed).

Per system:
  PROJECT_RC     ends judged by the merged R-T516-1 end_state against the printed minimum bearing; BEARING_OK -> 1 nr
                 PRODUCED, length in [w + 2 b_min, w + a_s + a_e]; any end FLAGGED_DEFICIT -> the count is HELD by name
                 (the designer may join two openings, dowel into a column or extend through a cross wall), the hard
                 length ceiling beside; any end HELD -> HELD.
  OWNER_PRECAST  bearing b = a project-printed lintel bearing whose scope covers the wall (level 1, when >= the company
                 0.15 m), else the company minimum 0.15 m (level 3); required = w + 2 b; piece = shortest stock length
                 >= required (1.20 / 1.50 / 2.50 / 3.00 / 4.00 m); required > 4.00 m -> FLAGGED (cast-in-situ / design).
                 The piece must then FIT the measured piers: each end's built masonry a >= b and a_s + a_e >= piece - w
                 (the piece may sit off-centre). An end with less than b -> FLAGGED_DEFICIT, never a default bearing; an
                 unmeasured end -> HELD; a pier shared with a REQUIRED neighbour must carry both bearings (else deficit);
                 with a HELD neighbour the fit is CONDITIONAL and the piece is HELD by name.
  Only a PRODUCED piece enters a count; HELD / FLAGGED pieces are listed by name with their reason, never 0.

Beside (never governing): the precast alternative of a PROJECT_RC lintel in a WHITE wall, with the same fit test, so a
substitution request can be answered from measured piers. A BLACK wall has no precast alternative (Q-60).

Refused: a width that is not metres (mm / cm entry), a bearing defaulted for an unmeasured end, a second record for one
opening, an unknown block type or decision.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t516"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import company_rulebook_v1 as C  # noqa: E402
import t516_jamb_bearing as T516  # noqa: E402

RULE_ID = "R-T519-1"
PROJECT_RC, OWNER_PRECAST, SYS_HELD = "PROJECT_RC", "OWNER_PRECAST", "HELD"
PRODUCED, HELD, FLAGGED = "PRODUCED", "HELD", "FLAGGED"
FITS, CONDITIONAL, NO_FIT = "FITS", "CONDITIONAL", "DOES_NOT_FIT"
BLOCKS = ("WHITE", "BLACK")
DECISIONS = ("REQUIRED", "HELD", "FLAGGED")
EPS = 1e-9


class LintelPiecesError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _w(v, oid):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise LintelPiecesError(f"{oid}: width {v!r} is not a number")
    if not 0 < v <= 20.0:
        raise LintelPiecesError(f"{oid}: width {v!r} is not a width in metres (mm / cm entry, or not positive)")
    return float(v)


def band_of(schedule, w):
    """the printed band whose inclusive integer-cm interval holds w, or None (gap / above the last band)."""
    cm = w * 100.0
    for b in schedule["bands"]:
        if b["lo_cm"] - 1e-6 <= cm <= b["hi_cm"] + 1e-6:
            return b
    return None


def system_of(rec, schedule):
    """-> (system, band or None, why)."""
    bt = rec["block_type"]
    if schedule and bt in schedule["scope"]:
        b = band_of(schedule, rec["width_m"])
        if b is None:
            return SYS_HELD, None, (f"the project lintel schedule ({schedule['source']}) covers {bt} walls but prints no "
                                    f"band for w = {rec['width_m']} m: SCHEDULE_SILENT, never the nearest band")
        return PROJECT_RC, b, (f"project LINTEL SCHEDULE row {b['row']} ({schedule['source']}) covers {bt} walls and "
                               f"this width: level 1 governs the company precast rule (Q-60 directive; UPC-LINTEL-001 "
                               f"scope 'never both')")
    if bt == "WHITE":
        return OWNER_PRECAST, None, ("no project lintel schedule covers this WHITE wall: owner precast rule "
                                     "UPC-LINTEL-001 (level 3; Q-60 atab only for white blocks)")
    return SYS_HELD, None, ("BLACK wall and no project lintel schedule covers it: the company rule leaves black walls to "
                            "'black precast or RC as the drawings require'; the drawings are silent: system HELD")


def _precast_bearing(rec, schedule):
    if schedule and schedule.get("bearing_m") is not None and rec["block_type"] in schedule["scope"]:
        return {"m": schedule["bearing_m"], "source": f"project {schedule['bearing_source']}"}
    return None


def precast_piece(rec, schedule, neighbours):
    """the owner precast piece for one opening and its fit on the measured piers."""
    oid, w = rec["opening_id"], rec["width_m"]
    pc = C.lintel(w, bearing=_precast_bearing(rec, schedule))
    out = {"rule": "UPC-LINTEL-001", "bearing_m": pc.get("bearing_m"), "bearing_basis": pc.get("bearing_basis"),
           "bearing_source": pc.get("bearing_source"), "required_m": pc.get("required_m")}
    if pc["status"] != C.OK:
        return dict(out, state=FLAGGED, piece_m=None, fit=None, why=pc.get("why"))
    out["piece_m"] = pc["piece_m"]
    b = pc["bearing_m"]
    av, cond, short = [], [], []
    for e in rec["ends"]:
        a = e.get("available_m")
        if a is None:
            return dict(out, state=HELD, fit=HELD,
                        why=f"{e['side']} end: no masonry measure beside the jamb (never a default bearing, never 0)")
        nb = e.get("shared_with")
        if nb:
            d = neighbours.get(nb)
            if d is None:
                raise LintelPiecesError(f"{oid} {e['side']}: pier shared with {nb}: its lintel decision is needed")
            if d == "REQUIRED":
                a = a - b                       # the neighbour needs its own bearing in the same pier
            elif d in ("HELD", "FLAGGED"):
                cond.append(f"{e['side']} pier {e['available_m']} m shared with {nb} ({d}): if {nb} gets a lintel "
                            f"the pier must carry 2 x {b} m")
        av.append(a)
        if a < b - EPS:
            short.append(f"{e['side']} end {_r(a)} m < bearing {b} m")
    if short:
        return dict(out, state=FLAGGED, fit=NO_FIT, why="FLAGGED_DEFICIT: " + "; ".join(short) + " (never defaulted)")
    if sum(av) < pc["piece_m"] - w - EPS:
        return dict(out, state=FLAGGED, fit=NO_FIT,
                    why=f"piers {_r(sum(av))} m < the piece overhang {_r(pc['piece_m'] - w)} m: the stock piece does "
                        f"not fit between the obstructions")
    if cond:
        two_fit = all(e.get("available_m") is not None and
                      (not e.get("shared_with") or e["available_m"] >= 2 * b - EPS) for e in rec["ends"])
        if not two_fit:
            return dict(out, state=HELD, fit=CONDITIONAL, why="; ".join(cond) + ": it cannot; HELD by name")
    return dict(out, state=PRODUCED, fit=FITS, why="the stock piece fits the measured piers")


def rc_lintel(rec, schedule, neighbours):
    """PROJECT_RC: the end states of the merged R-T516-1 against the printed minimum."""
    b_min = schedule["bearing_m"]
    if b_min is None:
        return {"state": HELD, "count": None, "why": "the schedule prints no minimum bearing: length HELD"}
    ends = []
    for e in rec["ends"]:
        x = {"side": e["side"], "available_m": e.get("available_m"), "own_band_m": e.get("available_m"),
             "stopper": e.get("stopper") or ("OPENING" if e.get("shared_with") else "END_OF_MASONRY"),
             "stopper_id": e.get("shared_with") or "", "beyond_band_end": "", "search_capped": e.get("capped") or "",
             "opening_id": rec["opening_id"]}
        nd = neighbours.get(e.get("shared_with")) if e.get("shared_with") else None
        if e.get("shared_with") and nd is None:
            raise LintelPiecesError(f"{rec['opening_id']} {e['side']}: pier shared with {e['shared_with']}: its lintel "
                                    f"decision is needed")
        ends.append(T516.end_state(x, b_min, nd))
    states = {e["state"] for e in ends}
    W = Fraction(str(rec["width_m"]))
    his = [e.get("bearing_hi_m") for e in ends]
    hi = None if any(h is None for h in his) else _r(W + sum(Fraction(str(h)) for h in his))
    if T516.DEFICIT in states:
        return {"state": HELD, "count": None, "count_at_most": 1, "length_lo_m": None, "length_hi_m": hi,
                "end_states": [e["state"] for e in ends],
                "why": "FLAGGED_BEARING_DEFICIT at " + ", ".join(e["side"] for e in ends if e["state"] == T516.DEFICIT)
                       + ": the printed detail cannot be built as drawn; count and length HELD for the designer"}
    if T516.HELD in states:
        return {"state": HELD, "count": None, "count_at_most": 1, "length_lo_m": None, "length_hi_m": None,
                "end_states": [e["state"] for e in ends], "why": "an end is HELD (masonry not measured)"}
    lo = _r(W + sum(Fraction(str(e["bearing_lo_m"])) for e in ends))
    return {"state": PRODUCED, "count": 1, "length_lo_m": lo, "length_hi_m": hi,
            "end_states": [e["state"] for e in ends],
            "why": "BEARING_OK: cast to length, L in [w + 2 b_min, w + a_s + a_e] (no stock length)"}


def opening(rec, schedule, neighbours):
    oid = rec.get("opening_id")
    if rec.get("block_type") not in BLOCKS:
        raise LintelPiecesError(f"{oid}: block type {rec.get('block_type')!r} not WHITE / BLACK")
    if rec.get("decision") not in DECISIONS:
        raise LintelPiecesError(f"{oid}: decision {rec.get('decision')!r}")
    rec = dict(rec, width_m=_w(rec.get("width_m"), oid))
    out = {"opening_id": oid, "floor": rec.get("floor"), "block_type": rec["block_type"], "width_m": rec["width_m"],
           "decision": rec["decision"], "rule": RULE_ID}
    if rec["width_m"] is None:
        return dict(out, system=SYS_HELD, state=HELD, why="width not established (never 0)")
    system, band, why = system_of(rec, schedule)
    out.update(system=system, system_why=why, schedule_row=band["row"] if band else None)
    if rec["decision"] != "REQUIRED":
        return dict(out, state=HELD, why=f"lintel decision {rec['decision']} (merged T-453): at most 1 piece, HELD by "
                                         f"name, never 0")
    sides = sorted(e.get("side") for e in rec.get("ends") or [])
    if sides != ["END", "START"]:
        raise LintelPiecesError(f"{oid}: needs one START and one END record, got {sides}")
    if system == SYS_HELD:
        return dict(out, state=HELD, why=why)
    if system == PROJECT_RC:
        rc = rc_lintel(rec, schedule, neighbours)
        out.update(state=rc.pop("state"), why=rc.pop("why"), rc=rc, stock_length="NOT_APPLICABLE (cast to length)")
        if rec["block_type"] == "WHITE":
            out["precast_beside"] = precast_piece(rec, schedule, neighbours)
        else:
            out["precast_beside"] = {"state": "NOT_APPLICABLE", "why": "BLACK wall: no precast atab (Q-60)"}
        return out
    pc = precast_piece(rec, schedule, neighbours)
    return dict(out, state=pc["state"], why=pc["why"], precast=pc)


def census(records, schedule):
    seen = set()
    for r in records:
        if r.get("opening_id") in seen:
            raise LintelPiecesError(f"{r.get('opening_id')}: a second record for one opening")
        seen.add(r.get("opening_id"))
    neighbours = {r["opening_id"]: r.get("decision") for r in records}
    for r in records:
        neighbours.update(r.get("neighbour_decisions") or {})
    rows = [opening(r, schedule, neighbours) for r in records]
    return {"rule": RULE_ID, "rows": rows, "summary": summary(rows)}


def _by_length(rows, key):
    out = {}
    for L in sorted(float(x) for x in C.param("UPC-LINTEL-001", "stock_lengths_m")["value"]):
        sel = [r for r in rows if (r.get(key) or {}).get("piece_m") == L]
        out[f"{L:.2f}"] = {"produced_nr": sum(1 for r in sel if r[key]["state"] == PRODUCED),
                           "produced": [r["opening_id"] for r in sel if r[key]["state"] == PRODUCED],
                           "held": [r["opening_id"] for r in sel if r[key]["state"] == HELD],
                           "flagged": [r["opening_id"] for r in sel if r[key]["state"] == FLAGGED]}
    return out


def summary(rows):
    req = [r for r in rows if r["decision"] == "REQUIRED"]
    rc = [r for r in req if r.get("system") == PROJECT_RC]
    pc = [r for r in req if r.get("system") == OWNER_PRECAST]
    s = {"openings": len(rows), "required": len(req),
         "system_count": {k: sum(1 for r in req if r.get("system") == k) for k in (PROJECT_RC, OWNER_PRECAST, SYS_HELD)},
         "rc_produced_nr": sum(1 for r in rc if r["state"] == PRODUCED),
         "rc_produced": [r["opening_id"] for r in rc if r["state"] == PRODUCED],
         "rc_held": [r["opening_id"] for r in rc if r["state"] == HELD],
         "precast_governing_by_length": _by_length(pc, "precast"),
         "precast_governing_flagged_no_piece": [r["opening_id"] for r in pc if r["precast"]["piece_m"] is None],
         "precast_beside_by_length": _by_length(rc, "precast_beside"),
         "system_held": [r["opening_id"] for r in req if r.get("system") == SYS_HELD],
         "not_required_held_by_name": [r["opening_id"] for r in rows if r["decision"] != "REQUIRED"],
         "note": "only PRODUCED pieces are counted; HELD / FLAGGED by name, never 0; RC lintels have no stock length"}
    s["label"] = "COMPLETE" if (not s["rc_held"] and not s["system_held"] and not s["not_required_held_by_name"] and
                                all(not v["held"] and not v["flagged"]
                                    for v in s["precast_governing_by_length"].values())
                                and not s["precast_governing_flagged_no_piece"]) else "PARTIAL (held items named)"
    return s


# ------------------------------------------------------------------------------------- training-villa builder
T516_OUT = ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json"
T453 = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
SCHEDULE = ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
PINS = {T516_OUT: "155ed68bc3f356d3011d342d836205e596ac7127f81bc8f8efc262d69fc5fef3",
        T453: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        SCHEDULE: "5d5baf166700d1d5968c5420f37118ae27836f61a2eeae88ed658f40e25936d7"}


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise LintelPiecesError(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return b.decode("utf-8")


def training_schedule():
    rows = list(csv.DictReader(io.StringIO(_load(SCHEDULE))))
    bands = [{"row": r["ROW_ID"], "lo_cm": int(r["WIDTH_LO_CM"]), "hi_cm": int(r["WIDTH_HI_CM"]),
              "d_cm": int(r["D_CM"])} for r in rows if r["RECORD"] == "SCHEDULE_ROW"]
    mb = [r for r in rows if r["RECORD"] == "DETAIL_READING" and r["ROW_ID"] == "MIN-BEARING"]
    if len(bands) != 5 or len(mb) != 1 or mb[0]["WIDTH_PRINTED"].strip() != "MIN.40cm":
        raise LintelPiecesError("schedule transcription: 5 rows and the MIN.40cm detail expected")
    # scope: the schedule note 'B-WIDTH OF THE BLOCK WALL' names block walls without a block type: every block wall
    return {"source": "ST7757.pdf p.13 LINTEL SCHEDULE (S8.6 transcription)", "scope": ("WHITE", "BLACK"),
            "scope_basis": "printed note 'B-WIDTH OF THE BLOCK WALL': block walls, no block type excluded",
            "bands": bands, "bearing_m": 0.40, "bearing_source": "LINTEL DETAIL 'MIN.40cm' (ST7757 p.13)"}


def training_records():
    t516 = {r["opening_id"]: r for r in json.loads(_load(T516_OUT))["rows"]}
    t453 = json.loads(_load(T453))["lintels"]
    out = []
    for L in t453:
        oid = L["opening_id"]
        rec = {"opening_id": oid, "floor": L["floor"], "block_type": L["block_type"], "width_m": L["width_m"],
               "decision": L["decision"], "t453_schedule_row": L.get("schedule_row")}
        if L["decision"] == "REQUIRED":
            if oid not in t516:
                raise LintelPiecesError(f"{oid}: REQUIRED in T-453 but no T-516 bearing record")
            ends = []
            for e in t516[oid]["ends"]:
                a = None if e["state"] == T516.HELD else e.get("available_trusted_m")
                shared = e["stopper_id"] if e["stopper"] == "OPENING" and e["stopper_id"] in {x["opening_id"]
                                                                                              for x in t453} else None
                capped = "YES" if (e["state"] == T516.BOUNDED and e.get("bearing_hi_m") is None) else ""
                ends.append({"side": e["side"], "available_m": a, "shared_with": shared, "stopper": e["stopper"]
                             if e["stopper"] != "OPENING" or shared else "END_OF_MASONRY", "capped": capped,
                             "t516_state": e["state"]})
            rec["ends"] = ends
        out.append(rec)
    if sorted(k for k in t516) != sorted(r["opening_id"] for r in out if r["decision"] == "REQUIRED"):
        raise LintelPiecesError("T-516 and T-453 REQUIRED sets differ")
    return out


def reconcile(doc):
    """T-453 (precast beside at 0.40, no fit test) and T-516 (precast beside at 0.15 on all 16) against R-T519-1."""
    t453 = {r["opening_id"]: r for r in json.loads(_load(T453))["lintels"]}
    t516 = {r["opening_id"]: r for r in json.loads(_load(T516_OUT))["rows"]}
    rows = []
    for r in doc["rows"]:
        if r["decision"] != "REQUIRED":
            continue
        oid = r["opening_id"]
        a453 = (t453[oid].get("precast_alternative_beside") or {}).get("piece_m")
        a516 = t516[oid]["precast_beside"].get("piece_m")
        mine = (r.get("precast_beside") or {}).get("piece_m")
        cause = []
        if r["block_type"] == "BLACK":
            cause.append("BLACK wall: no precast atab (Q-60); T-516 listed one at the company 0.15 m")
        elif a516 != mine:
            cause.append(f"bearing basis: T-516 used the company minimum 0.15 m, the project detail prints MIN 0.40 m "
                         f"for every block-wall lintel (level 1 > level 3): {a516} -> {mine} m")
        if a453 is not None and a453 != mine:
            cause.append(f"T-453 piece {a453} m differs")
        fit = (r.get("precast_beside") or {}).get("fit")
        rows.append({"opening_id": oid, "block_type": r["block_type"], "t453_rc_nr": 1, "t519_rc_state": r["state"],
                     "t453_precast_beside_m": a453, "t516_precast_beside_m": a516, "t519_precast_beside_m": mine,
                     "t519_precast_fit": fit, "cause": "; ".join(cause) or "same piece"})
    return rows


def build():
    doc = census(training_records(), training_schedule())
    doc["reconciliation"] = reconcile(doc)
    doc["sources"] = {str(p.relative_to(ROOT)): s for p, s in PINS.items()}
    doc["rulebook_digest"] = C.digest()
    return doc
