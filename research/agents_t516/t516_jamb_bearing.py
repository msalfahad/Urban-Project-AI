"""T-516: B9-02 LINTEL JAMB BEARING census (research rule proposal R-T516-1; research only, nothing in engine/ or tools/
imports it).

Physical element (ERS s.2.1). The lintel END that rests on the masonry beside an opening. Its built bearing b is the
length of lintel over masonry beyond the jamb. Three different things bound it, and none of them alone is b:
  - the RC detail prints a MINIMUM ('MIN.40cm'): b >= b_min where the detail can be built (a minimum is not the value);
  - the masonry actually drawn beside the jamb (pier) bounds it from ABOVE: b <= a, where a = the built wall material
    along the wall line, across the full thickness, up to the first column face, next opening or end of masonry
    (research/agents_t516/t516_extract.py reads a from the drawing);
  - a pier shared with a neighbouring lintel is shared: b_this + b_next <= a.
No drawing of this villa prints a per-lintel bearing dimension, so b is never MEASURED here; a printed bearing with a
PRINTED source makes an end MEASURED (fixture).

Per end:
  MEASURED                printed bearing with source (b fixed).
  BOUNDED                 a >= b_min, a trusted: b in [b_min, a_upper]; a_upper = a, or a - b_min when the pier is
                          shared with a REQUIRED neighbour; None (ceiling HELD) when the search hit its limit or only
                          the own-band part is trusted.
  FLAGGED_DEFICIT         a < b_min, a trusted: the printed detail cannot be built at this end as drawn (b <= a < b_min);
                          designer item (RC column connection / wall end / shared pier). Never b_min, never 0.
  HELD                    a not measured, or the junction beyond the band end is not resolved and the own-band part is
                          below b_min.
Per lintel:
  BEARING_OK (both ends BOUNDED / MEASURED): concrete length L in [w + b_s,min + b_e,min, w + a_s + a_e]; the merged
      T-453 L = w + 2 b_min is the LOWER bound (label MIN_BEARING, not exact). Links count in [ceil(r (w + 2 b_min)),
      ceil(r (w + a_s + a_e))] (RATE_COUNT, engine column_rebar policy); straight main-bar ceiling n x (w + a_s + a_e)
      x kg/m (the bar cannot leave the concrete). The T-515 span AT_LEAST stands (span installed in full).
  FLAGGED_BEARING_DEFICIT (any end deficit): the T-453 L = w + 2 b_min is NOT buildable as drawn; L <= w + a_s + a_e
      (hard physical ceiling, beside) and no lower bound beyond w; concrete / formwork / links over L stay HELD for the
      designer; the T-515 span AT_LEAST still stands.
  HELD (any end HELD, none deficit): bounds HELD by name.
Beside only (never the governing figure, register ruling F-T453-1: the project RC schedule governs, level 1): the owner
precast rule (UPC-LINTEL-001, owner 2026-11-02: shortest stock length >= w + 2 x 0.15) and whether its piece fits the
measured piers (each end >= 0.15 and a_s + a_e >= piece - w).

Refused: an available length that is not a number in metres (mm / cm / negative), a bearing defaulted without a printed
source, b_min used as the bearing of a deficit end, a HELD end carrying a bound, a second record for one opening, a
neighbour pier listed on one side only.

    python3 -I research/agents_t516/t516_jamb_bearing.py      # training villa: writes out/JAMB_BEARING_T516.json
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import company_rulebook_v1 as C  # noqa: E402

RULE_ID = "R-T516-1"
MEASURED, BOUNDED, DEFICIT, HELD = "MEASURED", "BOUNDED", "FLAGGED_DEFICIT", "HELD"
OK, FLAGGED, LHELD = "BEARING_OK", "FLAGGED_BEARING_DEFICIT", "HELD"
TRUSTED_JUNCTIONS = ("", "ORTHOGONAL", "DOORWAY_STUB_THEN_ORTHOGONAL")
STOPPERS = ("COLUMN", "OPENING", "END_OF_MASONRY", "SEARCH_LIMIT")
MAX_PIER_M = 20.0


class JambBearingError(ValueError):
    pass


def _f(x):
    return Fraction(str(x))


def _ceil(q):
    return -((-q.numerator) // q.denominator)


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _metres(v, where):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise JambBearingError(f"{where}: {v!r} is not a length")
    x = float(v)
    if math.isnan(x) or x < 0 or x > MAX_PIER_M:
        raise JambBearingError(f"{where}: {v!r} is not a length in metres (mm / cm entry, or negative)")
    return x


def end_state(end, b_min, neighbour_required=None):
    """one lintel end {side, available_m, own_band_m, stopper, stopper_id, beyond_band_end, search_capped,
    [printed_bearing_m + printed_bearing_source]} -> its bearing state."""
    side = end.get("side")
    where = f"{end.get('opening_id')} {side}"
    out = {"side": side, "stopper": end.get("stopper"), "stopper_id": end.get("stopper_id") or "",
           "beyond_band_end": end.get("beyond_band_end") or "", "rule": RULE_ID}
    if end.get("printed_bearing_m") is not None:
        src = str(end.get("printed_bearing_source") or "")
        if not src.upper().startswith("PRINTED"):
            raise JambBearingError(f"{where}: bearing {end['printed_bearing_m']} has no printed source: a defaulted "
                                   f"bearing is refused")
        b = _metres(end["printed_bearing_m"], where)
        a = _metres(end.get("available_m"), where)
        if a is not None and b > a + 1e-9:
            raise JambBearingError(f"{where}: printed bearing {b} m exceeds the {a} m of masonry drawn beside the jamb")
        return dict(out, state=MEASURED if b >= b_min - 1e-9 else DEFICIT, bearing_lo_m=b, bearing_hi_m=b,
                    available_m=a, source=src)
    a = _metres(end.get("available_m"), where)
    if a is None:
        return dict(out, state=HELD, bearing_lo_m=None, bearing_hi_m=None, available_m=None,
                    why="no masonry measure beside this jamb (never the detail minimum, never 0)")
    if end.get("stopper") not in STOPPERS:
        raise JambBearingError(f"{where}: unknown stopper {end.get('stopper')!r}")
    jn = (end.get("beyond_band_end") or "").split(":")[0]
    trusted = jn in TRUSTED_JUNCTIONS
    capped = str(end.get("search_capped") or "").upper() == "YES" or end.get("stopper") == "SEARCH_LIMIT"
    own = _metres(end.get("own_band_m"), where)
    eff = a if trusted else own
    out.update(available_m=a, available_trusted_m=eff, trusted=trusted)
    if eff is None or (not trusted and eff < b_min - 1e-9):
        return dict(out, state=HELD, bearing_lo_m=None, bearing_hi_m=None,
                    why=f"the masonry beyond the band end ({jn}) is not resolved by the run and the own-band part "
                        f"{own} m is below the {b_min} m minimum: bearing HELD (never the minimum, never 0)")
    if eff < b_min - 1e-9:
        why = {"COLUMN": f"only {eff} m of masonry before an RC column face: the lintel abuts the column (connection "
                         f"not drawn / not approved)",
               "OPENING": f"pier of {eff} m to the next opening {end.get('stopper_id')}: shorter than one minimum "
                          f"bearing",
               "END_OF_MASONRY": f"the masonry ends {eff} m beyond the jamb (wall end / far face of the wall met)"}
        return dict(out, state=DEFICIT, bearing_lo_m=None, bearing_hi_m=_r(eff),
                    why=why.get(end.get("stopper"), "masonry shorter than the minimum") +
                        f" < printed MIN {b_min} m: the detail cannot be built as drawn here; designer item")
    hi = None if (capped or not trusted) else eff
    shared = None
    if end.get("stopper") == "OPENING":
        if neighbour_required is None:
            raise JambBearingError(f"{where}: pier shared with {end.get('stopper_id')}: its lintel decision is needed")
        if neighbour_required == "REQUIRED":
            shared = "the neighbour lintel needs its own minimum in the same pier"
            if eff < 2 * b_min - 1e-9:
                return dict(out, state=DEFICIT, bearing_lo_m=None, bearing_hi_m=_r(eff - 0.0),
                            shared_pier_m=_r(eff), why=f"pier {eff} m shared with the REQUIRED lintel "
                                                       f"{end.get('stopper_id')}: < 2 x {b_min} m, both minimums "
                                                       f"cannot be built; designer item (one lintel over both?)")
            hi = None if hi is None else _r(eff - b_min)
        else:
            shared = (f"neighbour {end.get('stopper_id')} lintel {neighbour_required}: "
                      + ("pier < 2 x minimum: IF it gets a lintel both minimums cannot be built (conditional flag)"
                         if eff < 2 * b_min - 1e-9 else "pier >= 2 x minimum: both minimums fit"))
    return dict(out, state=BOUNDED, bearing_lo_m=b_min, bearing_hi_m=_r(hi), shared_pier=shared,
                why=f"masonry {eff} m >= printed MIN {b_min} m: built bearing in [{b_min}, "
                    f"{'HELD' if hi is None else _r(hi)}] m (the minimum is a lower bound, not the value)")


def precast_fit(w, ends):
    """owner precast rule beside (UPC-LINTEL-001): the stock piece and whether the measured piers hold it."""
    pc = C.lintel(w)
    if pc.get("status") != C.OK:
        return {"rule": "UPC-LINTEL-001", "status": pc.get("status"), "why": pc.get("why")}
    minb = pc["bearing_m"]
    av = [e.get("available_trusted_m") if e["state"] != HELD else None for e in ends]
    if any(a is None for a in av):
        fit = HELD
    else:
        fit = "FITS" if all(a >= minb - 1e-9 for a in av) and sum(av) >= pc["piece_m"] - w - 1e-9 else "DOES_NOT_FIT"
    return {"rule": "UPC-LINTEL-001", "status": "BESIDE", "piece_m": pc["piece_m"], "min_bearing_m": minb,
            "fit_on_measured_piers": fit,
            "governs": "no (F-T453-1: the project RC LINTEL SCHEDULE governs, level 1; owner precast practice beside)"}


def lintel(rec, b_min, neighbours=None):
    """rec: {opening_id, decision, width_m, bars [(n, kg_per_m)], links_rate, span_at_least_kg, ends [start, end]}."""
    oid = rec.get("opening_id")
    neighbours = neighbours or {}
    out = {"opening_id": oid, "floor": rec.get("floor"), "rule": RULE_ID, "decision": rec.get("decision")}
    if rec.get("decision") != "REQUIRED":
        return dict(out, state=LHELD, ends=[], why="lintel not established: no bearing census (never 0)")
    w = _metres(rec.get("width_m"), f"{oid} width")
    if not w:
        raise JambBearingError(f"{oid}: width {rec.get('width_m')!r} is not an opening width")
    sides = [e.get("side") for e in rec.get("ends") or []]
    if sorted(sides) != ["END", "START"]:
        raise JambBearingError(f"{oid}: needs exactly one START and one END record, got {sides}")
    ends = [end_state(dict(e, opening_id=oid), b_min, neighbours.get(e.get("stopper_id"))
                      if e.get("stopper") == "OPENING" else None) for e in rec["ends"]]
    for e in ends:
        if e["state"] == HELD and (e.get("bearing_lo_m") is not None or e.get("bearing_hi_m") is not None):
            raise JambBearingError(f"{oid} {e['side']}: a HELD end carries a bound")
        if e["state"] == DEFICIT and e.get("bearing_lo_m") is not None:
            raise JambBearingError(f"{oid} {e['side']}: a deficit end given the minimum as its bearing")
    W = _f(w)
    states = {e["state"] for e in ends}
    rate = rec.get("links_rate")
    bars = rec.get("bars") or []
    kgm = sum(n * _f(k) for n, k in bars)
    his = [e.get("bearing_hi_m") for e in ends]
    ceil_L = None if any(h is None for h in his) else W + sum(_f(h) for h in his)
    res = {"width_m": w, "ends": ends, "span_at_least_kg": rec.get("span_at_least_kg"),
           "precast_beside": precast_fit(w, ends), "t453_length_m": _r(W + 2 * _f(b_min))}
    if DEFICIT in states:
        res.update(state=FLAGGED, length_lo_m=None, length_hi_m=_r(ceil_L),
                   t453_length_label="NOT BUILDABLE AS DRAWN (an end has less masonry than the printed minimum)",
                   links_lo=None, links_hi=None if ceil_L is None else _ceil(rate * ceil_L),
                   straight_ceiling_kg=None if ceil_L is None else float(kgm * ceil_L),
                   why="bearing deficit at " + ", ".join(e["side"] for e in ends if e["state"] == DEFICIT) +
                       ": concrete length, formwork and links over L HELD for the designer; the span AT_LEAST stands")
    elif HELD in states:
        res.update(state=LHELD, length_lo_m=None, length_hi_m=None, t453_length_label="UNVERIFIED (an end HELD)",
                   links_lo=None, links_hi=None, straight_ceiling_kg=None,
                   why="an end is HELD: " + "; ".join(e.get("why", "") for e in ends if e["state"] == HELD))
    else:
        lo = W + sum(_f(e["bearing_lo_m"]) for e in ends)
        res.update(state=OK, length_lo_m=_r(lo), length_hi_m=_r(ceil_L),
                   t453_length_label="LOWER BOUND (minimum bearing both ends), not the exact length",
                   links_lo=_ceil(rate * lo), links_hi=None if ceil_L is None else _ceil(rate * ceil_L),
                   straight_ceiling_kg=None if ceil_L is None else float(kgm * ceil_L),
                   why="both ends have at least the printed minimum of masonry")
    return dict(out, **res)


def census(records, b_min):
    seen = set()
    for r in records:
        if r.get("opening_id") in seen:
            raise JambBearingError(f"{r.get('opening_id')}: a second record for one opening")
        seen.add(r.get("opening_id"))
    dec = {r["opening_id"]: r.get("decision") for r in records}
    dec.update({k: v for r in records for k, v in (r.get("neighbour_decisions") or {}).items()})
    rows = [lintel(r, b_min, dec) for r in records]
    # a pier between two lintels is measured from both sides: the two readings must agree
    by = {(r["opening_id"], e["side"]): e for r in rows for e in r.get("ends") or []}
    for r in rows:
        for e in r.get("ends") or []:
            if e["stopper"] == "OPENING" and dec.get(e["stopper_id"]) == "REQUIRED":
                other = [x for (o, _s), x in by.items() if o == e["stopper_id"] and x["stopper_id"] == r["opening_id"]]
                if len(other) != 1 or abs(other[0]["available_m"] - e["available_m"]) > 0.002:
                    raise JambBearingError(f"{r['opening_id']} {e['side']}: shared pier with {e['stopper_id']} not read "
                                           f"the same from both sides")
    return {"rule": RULE_ID, "min_bearing_m": b_min, "rows": rows, "summary": summary(rows)}


def summary(rows):
    req = [r for r in rows if r["state"] != LHELD or r.get("ends")]
    ends = [e for r in rows for e in r.get("ends") or []]
    cnt = lambda k: sum(1 for e in ends if e["state"] == k)
    ok = [r for r in rows if r["state"] == OK]
    fl = [r for r in rows if r["state"] == FLAGGED]
    hd = [r for r in rows if r["state"] == LHELD and r.get("ends")]
    return {"lintels": len(req), "ends": len(ends), "ends_measured": cnt(MEASURED), "ends_bounded": cnt(BOUNDED),
            "ends_deficit": cnt(DEFICIT), "ends_held": cnt(HELD),
            "lintels_bearing_ok": [r["opening_id"] for r in ok], "lintels_deficit": [r["opening_id"] for r in fl],
            "lintels_held": [r["opening_id"] for r in hd],
            "ok_length_lo_m": _r(sum(r["length_lo_m"] for r in ok)),
            "ok_links_lo": sum(r["links_lo"] for r in ok),
            "note": "figures per lintel; HELD and deficit lintels carry no length / link figure in any total (never 0)"}


# ------------------------------------------------------------------------------------- training-villa builder
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "out" / "JAMB_EVIDENCE_T516.csv"
T515 = ROOT / "research/agents_t515/out/LINTEL_BAR_SPLIT_T515.json"
T453 = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
SCHEDULE = ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
PINS = {T515: "e06725963f9533fb1045e39958cb71c44239ab2cb143f97586ae54b9c6ee64dc",
        T453: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        SCHEDULE: "5d5baf166700d1d5968c5420f37118ae27836f61a2eeae88ed658f40e25936d7"}
EVIDENCE_SHA = "efcc19996a5f4b1613c17cab1e87efb6d0b9f98b6870a73eeda445c2b7fb433c"
OUT = HERE / "out" / "JAMB_BEARING_T516.json"


def _load(p, sha):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != sha:
        raise JambBearingError(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return b.decode("utf-8")


def b_min_printed():
    rows = list(csv.DictReader(io.StringIO(_load(SCHEDULE, PINS[SCHEDULE]))))
    b = [r for r in rows if r["RECORD"] == "DETAIL_READING" and r["ROW_ID"] == "MIN-BEARING"]
    if len(b) != 1 or b[0]["WIDTH_PRINTED"].strip() != "MIN.40cm":
        raise JambBearingError("the lintel detail reading MIN.40cm is not in the schedule transcription")
    return 0.40


def records():
    ev = list(csv.DictReader(io.StringIO(_load(EVIDENCE, EVIDENCE_SHA))))
    t515 = {r["opening_id"]: r for r in json.loads(_load(T515, PINS[T515]))["rows"]}
    t453 = {r["opening_id"]: r for r in json.loads(_load(T453, PINS[T453]))["lintels"]}
    by = {}
    for e in ev:
        by.setdefault(e["opening_id"], []).append(e)
    req = sorted(k for k, r in t453.items() if r["decision"] == "REQUIRED")
    if sorted(by) != req:
        raise JambBearingError(f"evidence covers {sorted(by)}, the REQUIRED lintels are {req}")
    out = []
    for oid in req:
        L = t453[oid]
        b = t515[oid]
        bars = [(c["n"], c["kg_per_m"]) for c in b["components"] if c["part"] == "SPAN"]
        links = [c for c in b["components"] if c["role"] == "LINKS"][0]
        out.append({"opening_id": oid, "floor": L["floor"], "decision": "REQUIRED", "width_m": L["width_m"],
                    "bars": bars, "links_rate": links["rate_per_m"], "span_at_least_kg": b["at_least_kg"],
                    "ends": [{k: e[k] for k in ("side", "available_m", "own_band_m", "stopper", "stopper_id",
                                                "beyond_band_end", "search_capped")} for e in by[oid]],
                    "neighbour_decisions": {e["stopper_id"]: t453[e["stopper_id"]]["decision"]
                                            for e in by[oid] if e["stopper"] == "OPENING" and e["stopper_id"] in t453},
                    "drawn_gap_m": float(by[oid][0]["clear_width_m"])})
        if abs(out[-1]["drawn_gap_m"] - L["width_m"]) > 0.005:
            raise JambBearingError(f"{oid}: drawn gap {out[-1]['drawn_gap_m']} m vs census width {L['width_m']} m")
    for o in out:
        for e in o["ends"]:
            if e["stopper"] == "OPENING" and e["stopper_id"] not in t453:
                # a glazed stretch / bay of the V2 run, not a census opening: no lintel of this ledger shares the pier
                o["neighbour_decisions"][e["stopper_id"]] = "NOT_A_LEDGER_OPENING"
    return out


def build():
    doc = census(records(), b_min_printed())
    t515 = json.loads(_load(T515, PINS[T515]))
    rows = doc["rows"]
    ok = [r for r in rows if r["state"] == OK]
    doc["t515_effect"] = {
        "span_at_least_kg": t515["total"]["at_least_kg"],
        "span_at_least_note": "unchanged: the span part does not depend on the bearing",
        "t515_straight_ceiling_kg_at_exact_0_40": t515["total"]["ceiling_straight_kg_beside"],
        "reading": "the T-515 'ceiling' assumed a bearing of exactly 0.40 m; the detail prints a MINIMUM, so it is a "
                   "ceiling only for that assumption: on BEARING_OK lintels the true straight ceiling is the pier-"
                   "bounded figure below (larger or HELD), on deficit lintels 0.40 m is not buildable",
        "bearing_ok_true_ceiling_kg": _r(sum(r["straight_ceiling_kg"] for r in ok if r["straight_ceiling_kg"])),
        "bearing_ok_ceiling_held": [r["opening_id"] for r in ok if r["straight_ceiling_kg"] is None],
        "deficit_hard_ceiling_kg": _r(sum(r["straight_ceiling_kg"] or 0 for r in rows if r["state"] == FLAGGED)),
        "deficit_ceiling_held": [r["opening_id"] for r in rows if r["state"] == FLAGGED and
                                 r["straight_ceiling_kg"] is None],
        "t515_ceiling_on_deficit_lintels_kg": _r(sum(x["ceiling_straight_kg_beside"] for x in t515["rows"]
                                                      if x["opening_id"] in {r["opening_id"] for r in rows
                                                                             if r["state"] == FLAGGED})),
        "t515_ceiling_on_ok_lintels_kg": _r(sum(x["ceiling_straight_kg_beside"] for x in t515["rows"]
                                                 if x["opening_id"] in {r["opening_id"] for r in ok}))}
    t453 = {r["opening_id"]: r for r in json.loads(_load(T453, PINS[T453]))["lintels"]}
    doc["t453_concrete_effect"] = {
        "bearing_ok_concrete_m3_lower_bound": _r(sum(t453[r["opening_id"]]["concrete_m3"] for r in ok)),
        "bearing_ok_concrete_m3_upper_bound": None if any(r["length_hi_m"] is None for r in ok) else _r(sum(t453[r["opening_id"]]["section_m"][0] *
                                                     t453[r["opening_id"]]["section_m"][1] * r["length_hi_m"]
                                                     for r in ok if r["length_hi_m"] is not None)),
        "bearing_ok_upper_held": [r["opening_id"] for r in ok if r["length_hi_m"] is None],
        "bearing_ok_concrete_m3_upper_without_held_beside": _r(sum(
            t453[r["opening_id"]]["section_m"][0] * t453[r["opening_id"]]["section_m"][1] * r["length_hi_m"]
            for r in ok if r["length_hi_m"] is not None)),
        "deficit_t453_concrete_m3_not_buildable_as_drawn": _r(sum(t453[r["opening_id"]]["concrete_m3"]
                                                                  for r in rows if r["state"] == FLAGGED)),
        "deficit_t453_formwork_m2_not_buildable_as_drawn": _r(sum(t453[r["opening_id"]]["formwork_m2"]
                                                                  for r in rows if r["state"] == FLAGGED)),
        "reading": "merged T-453 lintel concrete = B x D x (w + 2 x 0.40): on BEARING_OK lintels a LOWER bound (label "
                   "MIN_BEARING), on deficit lintels a length the masonry cannot carry as drawn (designer item); "
                   "no candidate line is changed by this research record"}
    doc["sources"] = dict({str(p.relative_to(ROOT)): s for p, s in PINS.items()},
                          **{str(EVIDENCE.relative_to(ROOT)): EVIDENCE_SHA})
    doc["drawing"] = ("Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), read by "
                      "t516_extract.py through the merged MASONRY_CENTRELINE_V2 census (numbers only committed)")
    return doc


if __name__ == "__main__":
    doc = build()
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc["summary"], indent=1))
    for r in doc["rows"]:
        print(r["opening_id"], r["state"], r["width_m"], [(e["side"], e["state"], e.get("available_m"),
                                                           e.get("bearing_hi_m")) for e in r["ends"]],
              r.get("length_lo_m"), r.get("length_hi_m"), r.get("links_lo"), r.get("links_hi"),
              _r(r.get("straight_ceiling_kg")), r["precast_beside"].get("fit_on_measured_piers"))
    print(json.dumps(doc["t515_effect"], indent=1))
    print(json.dumps(doc["t453_concrete_effect"], indent=1))
