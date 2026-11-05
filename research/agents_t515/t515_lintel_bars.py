"""T-515: B9-02 LINTEL BAR SPLIT (research rule proposal R-T515-1; research only, nothing in engine/ or tools/ imports it).

Physical element (ERS s.2.1). An RC lintel over an opening carries the masonry above the head and bears on the wall each
side. Its reinforcement, as a lintel schedule + lintel detail print it: n bottom bars and n top bars of a printed
diameter running along the lintel, their ends bent into the bearing (bend DRAWN, length NOT printed), and closed links
at a printed rate per metre (cut length needs the cover and hook length, NOT printed). The concrete length L = clear
span w + 2 x printed minimum bearing (merged V3.0.53 lintel lines).

What is countable (owner 2026-10-29 (B): only drawn / printed bar parts; an undrawn part stays HELD unless physically
certain from the drawings themselves):
  SPAN segment of every main bar     n x w x kg/m      COMPUTED. The bar is drawn continuous across the opening and
                                                       into both bearings, so the clear span w is installed in full.
  IN-BEARING straight segment        n x 2 x (bearing - end cover) x kg/m. End cover NOT printed -> HELD by name; the
                                                       straight part of a bar can never exceed the concrete length L,
                                                       so n x 2 x bearing x kg/m is shown beside as a CEILING within
                                                       the measured L (never a quantity). A printed end cover with its
                                                       source makes it COMPUTED.
  END BENDS                          drawn, not dimensioned -> HELD (a printed bend length with its source computes it).
  LINKS                              count by the printed rate over L (RATE_COUNT = ceil(rate x L), the engine's
                                                       column_rebar policy) and over the span w beside; kg HELD (cut
                                                       length needs cover + hooks; B20 hook edition unverified).
  LAPS                               rebar_lap_rule_v2.bar_with_laps on the straight ceiling L, owner stock 12 m and
                                                       owner class BEAM (60 d): within the stock -> NOT_REQUIRED (a
                                                       genuine 0, not a held 0); a lintel with no printed bearing has
                                                       no ceiling -> laps HELD unless w itself exceeds the stock.
kg/m: engine.source.rebar_unit_mass, the project's method D2_OVER_162 (Urban default R3; owner formula kg = L x d^2 /
162, OWNER_RULE_REBAR_2026-10-24 s.2). kg internally at full precision; t only at the boundary (owner s.1).

The project figure is AT_LEAST (the COMPUTED parts); the HELD parts are named, never summed as 0. Refused: a cover,
bend or hook length without a printed source (a default), a HELD component carrying a number, a bar text that is not
'<n>Ø<d>' / '<n>×<d>', a width that is not metres inside the printed band, a second record for one opening, ledger bar
texts that differ from the printed schedule row.
Project-agnostic functions; the training-villa builder reads only sha-pinned merged files (no private file).

    python3 -I research/agents_t515/t515_lintel_bars.py          # writes research/agents_t515/out/*.json and prints
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import rebar_lap_rule_v2 as LAP  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402

RULE_ID = "R-T515-1"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "Urban project default (R3); owner formula kg = L x d^2 / 162 "
                                                    "(OWNER_RULE_REBAR_2026-10-24 s.2)", "selected_by": "project"}
STOCK_M = 12                      # owner stock bar, OWNER_RULE_REBAR_2026-10-24 s.2 / s.6 item 3
LAP_KIND = "BEAM"                 # the task's owner class for a lintel (60 d beams); never reached within the stock
COMPUTED, HELD, NOT_REQUIRED = "COMPUTED", "HELD", "NOT_REQUIRED"
AT_LEAST, COMPLETE = "AT_LEAST", "COMPLETE"
REQUIRED = "REQUIRED"
BAR = re.compile(r"^\s*(\d+)\s*[Ø×xX]\s*(\d+(?:\.\d+)?)\s*$")
RATE = re.compile(r"^\s*(\d+)\s*[Ø×xX]\s*(\d+(?:\.\d+)?)\s*/\s*[Mm]\s*$")
MAX_W_M = 20.0                    # a width above this is not a lintel opening in metres (mm / cm entry)
DETAIL_KEYS = ("end_cover_m", "bend_m", "hook_m", "cover_m")


class LintelBarError(ValueError):
    pass


def bars(text, where=""):
    """'2Ø12' / '2×12' -> (2, 12.0); anything else refused (never guessed)."""
    m = BAR.match(text or "")
    if not m:
        raise LintelBarError(f"{where}: bar text {text!r} is not '<n>Ø<d>'")
    return int(m.group(1)), float(m.group(2))


def rate(text, where=""):
    """'5Ø8/M' -> (5, 8.0) links per metre."""
    m = RATE.match(text or "")
    if not m:
        raise LintelBarError(f"{where}: link text {text!r} is not '<n>Ø<d>/M'")
    return int(m.group(1)), float(m.group(2))


def _f(x):
    return Fraction(str(x))


def _ceil(q):
    return -((-q.numerator) // q.denominator)


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _printed(rec, key):
    """a detail length (cover / bend / hook) only with a printed source; a bare value is a default -> refused."""
    v = rec.get(key)
    if v is None:
        return None
    src = str(rec.get(key + "_source") or "")
    if not src.upper().startswith("PRINTED"):
        raise LintelBarError(f"{rec.get('opening_id')}: {key} {v} has no printed source: a defaulted detail length is "
                             f"refused (stays HELD)")
    return float(v)


def _comp(role, part, state, kg=None, **kw):
    if state == HELD and kg is not None:
        raise LintelBarError(f"{role} {part}: a HELD component carries a number")
    if state == COMPUTED and (kg is None or kg <= 0):
        raise LintelBarError(f"{role} {part}: a COMPUTED component without a positive kg")
    return dict(role=role, part=part, state=state, kg=kg, **kw)   # full precision (owner s.1)


def lintel_bars(rec, umass=UNIT_MASS):
    """one lintel record {opening_id, decision, width_m, schedule_row, bottom, top, stirrups, bearing_m (None when not
    printed), [band_lo_m, band_hi_m], [end_cover_m / bend_m + *_source PRINTED...]} -> its bar split."""
    oid = rec.get("opening_id")
    out = {"opening_id": oid, "floor": rec.get("floor"), "decision": rec.get("decision"),
           "schedule_row": rec.get("schedule_row"), "rule": RULE_ID}
    if rec.get("decision") != REQUIRED:
        out.update(state=HELD, at_least_kg=None, components=[],
                   why=f"lintel not established ({rec.get('decision')}): {rec.get('why') or 'no reason given'}; "
                       f"its bars stay HELD with it (never 0)")
        w = rec.get("width_m")
        if w and rec.get("bottom") and rec.get("top"):
            nb, db = bars(rec["bottom"], oid)
            nt, dt = bars(rec["top"], oid)
            span = float(_f(w) * (nb * _f(UM.kg_per_m(db, umass)) + nt * _f(UM.kg_per_m(dt, umass))))
            out["if_built_span_kg_beside"] = _r(span)       # beside only: not a bound, never summed
        return out
    for k in DETAIL_KEYS:
        _printed(rec, k)                                    # refuse any defaulted detail length first
    w = rec.get("width_m")
    if w is None or not 0 < float(w) < MAX_W_M:
        raise LintelBarError(f"{oid}: width {w!r} is not an opening width in metres")
    lo, hi = rec.get("band_lo_m"), rec.get("band_hi_m")
    if lo is not None and hi is not None and not (float(lo) - 1e-9 <= float(w) <= float(hi) + 1e-9):
        raise LintelBarError(f"{oid}: width {w} m outside its printed band {rec.get('schedule_row')} {lo}..{hi} m")
    W = _f(w)
    bearing = rec.get("bearing_m")
    Bq = None if bearing is None else _f(bearing)
    L = None if Bq is None else W + 2 * Bq
    cover = _printed(rec, "end_cover_m")
    bend = _printed(rec, "bend_m")
    comps = []
    for role, key in (("BOTTOM", "bottom"), ("TOP", "top")):
        n, d = bars(rec.get(key), f"{oid} {role}")
        kgm = _f(UM.kg_per_m(d, umass))
        base = dict(n=n, dia_mm=d, kg_per_m=_r(float(kgm)))
        comps.append(_comp(role, "SPAN", COMPUTED, float(n * W * kgm), length_each_m=_r(float(W)),
                           basis=f"{n} x clear span {float(W)} m x {_r(float(kgm))} kg/m (bar drawn across the "
                                 f"opening into both bearings)", **base))
        if Bq is None:
            comps.append(_comp(role, "IN_BEARING", HELD, ceiling_kg_beside=None,
                               why="bearing length not printed: the in-bearing straight segment is not known", **base))
        elif cover is not None:
            seg = 2 * (Bq - _f(cover))
            if seg <= 0:
                raise LintelBarError(f"{oid}: printed end cover {cover} m leaves no bar in a {bearing} m bearing")
            comps.append(_comp(role, "IN_BEARING", COMPUTED, float(n * seg * kgm), length_each_m=_r(float(seg)),
                               basis=f"{n} x 2 x (bearing {bearing} - printed end cover {cover}) m", **base))
        else:
            comps.append(_comp(role, "IN_BEARING", HELD, ceiling_kg_beside=float(n * 2 * Bq * kgm),
                               why=f"end cover not printed: straight segment 2 x ({bearing} m bearing - end cover) "
                                   f"per bar; ceiling beside = 2 x {bearing} m (the bar cannot leave the concrete "
                                   f"length L), never a quantity", **base))
        if bend is not None:
            comps.append(_comp(role, "END_BENDS", COMPUTED, float(n * 2 * _f(bend) * kgm),
                               basis=f"{n} x 2 ends x printed bend {bend} m", **base))
        else:
            comps.append(_comp(role, "END_BENDS", HELD, why="end bends drawn into the bearing, no length printed", **base))
        run = L if L is not None else None
        if run is not None:
            lap = LAP.bar_with_laps(str(float(run)), d, LAP_KIND, stock=STOCK_M)
        elif W > STOCK_M:
            lap = LAP.bar_with_laps(str(float(W)), d, LAP_KIND, stock=STOCK_M)
        else:
            lap = {"state": HELD, "laps": None, "basis": "no printed bearing: the run's upper bound is not known"}
        if lap["state"] == NOT_REQUIRED:
            comps.append(dict(role=role, part="LAPS", state=NOT_REQUIRED, kg=0.0, laps=0, n=n, dia_mm=d,
                              basis=f"straight run at most {_r(float(run))} m within the {STOCK_M} m stock: no splice "
                                    f"for any lap length (rebar_lap_rule_v2)"))
        elif lap.get("laps") is not None and lap.get("lap_m") is not None:
            kg = float(n * lap["laps"] * _f(lap["lap_m"]) * kgm)
            comps.append(_comp(role, "LAPS", HELD, laps_per_bar=lap["laps"], lap_m=lap["lap_m"],
                               kg_if_full_run_beside=_r(kg), n=n, dia_mm=d,
                               why="the run exceeds the stock on its ceiling: splice count by rebar_lap_rule_v2; the "
                                   "run itself is HELD with the end cover, so the lap kg is beside"))
        else:
            comps.append(_comp(role, "LAPS", HELD, n=n, dia_mm=d, why=lap.get("basis") or "lap HELD"))
    rn, rd = rate(rec.get("stirrups"), f"{oid} LINKS")
    over_w = _ceil(rn * W)
    over_L = None if L is None else _ceil(rn * L)
    comps.append(_comp("LINKS", "LINKS", HELD, n_over_L=over_L, n_over_span=over_w, dia_mm=rd, rate_per_m=rn,
                       count_method="RATE_COUNT ceil(rate x length) (engine column_rebar policy)",
                       why="link cut length needs the cover and the hook length (not printed; B20 hook edition "
                           "unverified): kg HELD, the count is shown"))
    at_least = sum(c["kg"] for c in comps if c["state"] == COMPUTED)
    held = [f"{c['role']} {c['part']}" for c in comps if c["state"] == HELD]
    out.update(state=AT_LEAST if held else COMPLETE, width_m=_r(float(W)), bearing_m=bearing,
               length_m=None if L is None else _r(float(L)), at_least_kg=at_least, held_parts=held,
               ceiling_straight_kg_beside=None if L is None else (
                   sum(c["kg"] for c in comps if c["part"] == "SPAN") +
                   sum(c.get("ceiling_kg_beside") or 0 for c in comps if c["part"] == "IN_BEARING")),
               links_over_L=over_L, links_over_span=over_w, components=comps)
    return out


def check_row(row):
    """guard: a HELD part never carries a number, a COMPUTED part always does, and the row's at_least is the sum."""
    for c in row.get("components") or []:
        if c["state"] == HELD and c.get("kg") is not None:
            raise LintelBarError(f"{row['opening_id']} {c['role']} {c['part']}: HELD summed as {c['kg']} (refused)")
        if c["state"] == COMPUTED and not c.get("kg"):
            raise LintelBarError(f"{row['opening_id']} {c['role']} {c['part']}: COMPUTED without kg")
    if row["state"] == HELD:
        if row.get("at_least_kg") is not None:
            raise LintelBarError(f"{row['opening_id']}: a HELD lintel carries {row['at_least_kg']} kg (refused)")
        return row
    s = sum(c["kg"] for c in row["components"] if c["state"] == COMPUTED)
    if abs(s - row["at_least_kg"]) > 1e-9:
        raise LintelBarError(f"{row['opening_id']}: at_least {row['at_least_kg']} != computed parts {s}")
    return row


def ledger(records, umass=UNIT_MASS):
    seen = set()
    rows = []
    for r in records:
        if r.get("opening_id") in seen:
            raise LintelBarError(f"{r.get('opening_id')}: a second lintel record for one opening")
        seen.add(r.get("opening_id"))
        rows.append(check_row(lintel_bars(r, umass)))
    return {"rule": RULE_ID, "unit_mass": UM.describe(umass), "rows": rows, "total": total(rows)}


def total(rows):
    """project figure: AT_LEAST the COMPUTED parts, with every HELD part / lintel named; never a full figure."""
    for r in rows:
        check_row(r)
    known = sum(r["at_least_kg"] for r in rows if r["state"] != HELD)
    held_l = [r["opening_id"] for r in rows if r["state"] == HELD]
    held_p = sorted({p for r in rows if r["state"] != HELD for p in r["held_parts"]})
    state = AT_LEAST if (held_l or held_p) else COMPLETE
    return {"state": state, "at_least_kg": _r(known), "at_least_t": _r(known / 1000.0),
            "lintels_computed": sum(1 for r in rows if r["state"] != HELD), "lintels_held": held_l,
            "held_parts": held_p,
            "ceiling_straight_kg_beside": _r(sum(r.get("ceiling_straight_kg_beside") or 0 for r in rows
                                                 if r["state"] != HELD)),
            "links_over_L": sum(r.get("links_over_L") or 0 for r in rows if r["state"] != HELD),
            "links_over_span": sum(r.get("links_over_span") or 0 for r in rows if r["state"] != HELD),
            "rounding": "components and rows at full precision; only these totals rounded (6 dp), after summing",
            "note": "AT_LEAST: straight span parts only; in-bearing segments, end bends, links kg and the held lintels "
                    "are HELD by name, never 0, never summed in"}


# ------------------------------------------------------------------------------------- training-villa builder
LEDGER = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
SCHEDULE = ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
PINS = {LEDGER: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        SCHEDULE: "5d5baf166700d1d5968c5420f37118ae27836f61a2eeae88ed658f40e25936d7"}
OUT = ROOT / "research/agents_t515/out/LINTEL_BAR_SPLIT_T515.json"


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise LintelBarError(f"{p.name}: sha256 differs from the pinned merged file (edited input)")
    return b.decode("utf-8")


def schedule():
    rows = list(csv.DictReader(io.StringIO(_load(SCHEDULE))))
    out = {}
    for r in rows:
        if r["RECORD"] == "SCHEDULE_ROW":
            out[r["ROW_ID"]] = {"lo_m": float(r["WIDTH_LO_CM"]) / 100.0, "hi_m": float(r["WIDTH_HI_CM"]) / 100.0,
                                "bottom": (int(r["BOTTOM_N"]), float(r["BOTTOM_DIA_MM"])),
                                "top": (int(r["TOP_N"]), float(r["TOP_DIA_MM"])),
                                "links": (int(r["STIRRUP_RATE_PER_M"]), float(r["STIRRUP_DIA_MM"]))}
    b = [r for r in rows if r["RECORD"] == "DETAIL_READING" and r["ROW_ID"] == "MIN-BEARING"]
    m = re.search(r"(\d+(?:\.\d+)?)\s*cm", b[0]["WIDTH_PRINTED"]) if len(b) == 1 else None
    if not out or not m:
        raise LintelBarError("the printed schedule needs its rows and one MIN-BEARING reading")
    return out, float(m.group(1)) / 100.0


def records():
    sched, bearing = schedule()
    d = json.loads(_load(LEDGER))
    out = []
    for x in d["lintels"]:
        r = {k: x.get(k) for k in ("opening_id", "floor", "decision", "width_m", "schedule_row", "bottom", "top",
                                   "stirrups", "why", "kind")}
        row = sched.get(x.get("schedule_row")) if x.get("schedule_row") else None
        if row is not None:
            got = (bars(x["bottom"]), bars(x["top"]), rate(x["stirrups"]))
            if got != (row["bottom"], row["top"], row["links"]):
                raise LintelBarError(f"{x['opening_id']}: ledger bars {got} differ from the printed row "
                                     f"{x['schedule_row']} {row}")
            r.update(band_lo_m=row["lo_m"], band_hi_m=row["hi_m"])
        if x["decision"] == REQUIRED:
            if abs(x["length_m"] - (x["width_m"] + 2 * bearing)) > 1e-9:
                raise LintelBarError(f"{x['opening_id']}: ledger L {x['length_m']} != w + 2 x {bearing}")
            r["bearing_m"] = bearing
        out.append(r)
    return out


def build():
    doc = ledger(records())
    doc["sources"] = {str(p.relative_to(ROOT)): s for p, s in PINS.items()}
    doc["binding"] = "one row per V3.0.53 STR.CONC.LINTEL line, element_id LINTEL:<opening_id>"
    doc["freelancer"] = {"verdict": "UNRESOLVED",
                         "why": "the freelancer RC workbook keys one project rebar total (RC:ورقة1:25, 44.19 t) and no "
                                "lintel row (tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json): no element figure "
                                "to compare, and whether lintel steel is inside that total is not stated"}
    return doc


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    t = doc["total"]
    print(json.dumps({k: t[k] for k in ("state", "at_least_kg", "at_least_t", "ceiling_straight_kg_beside",
                                        "lintels_computed", "links_over_L", "links_over_span", "held_parts")},
                     ensure_ascii=False, indent=1), "held lintels:", len(t["lintels_held"]))
