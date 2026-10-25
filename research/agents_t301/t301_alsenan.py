"""T-301 on the development villa (P7757): the WP.FOUNDATION scope inventory from the merged, Checker-cited ledgers of the
drawn elements, joined to the waterproofing lines of the candidate of record ARCH_TAKEOFF_V3.0.17. Reads only; writes
counts, statuses, quantities, DXF handles and run / element ids (no coordinate, no name, no drawing content).

    python3 -I research/agents_t301/t301_alsenan.py --extract <run>/t254/v3017     # -> CANDIDATE_V3017_WP.json
    python3 -I research/agents_t301/t301_alsenan.py [--out DIR]                     # inventory + join + T-236 check

<run> is research/agents_t167/v304_run.py then research/agents_t254/v3017_run.py on the Drive copies (Drive "Alsenan
chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip, "ST7757 dxf.dxf").

Element sources (each built from the drawings, merged and Checker-verified; none is the engine's line list):
  footings     research/agents_t233/ALSENAN_FOOTING_INPUT.json: the 26 drawn footing outlines of the foundation plan (DXF
               handle, schedule tag(s), L x W area; T-233 MERGED 2ecb5bf0, Checker 2026-10-23 20:14 re-measured all 26)
  lift pit     outline 1B2B tag FF + the ST7757.pdf p.14 lift detail (base 4.600 x 4.500 x 0.55, screed 0.05, ring 10EB
               2.200 x 2.200, C9 1090 proud 0.050 x 1.000: envelope 4.890 m2; T-219 MERGED de7c1c4c, Verifier 10:40)
  ground beams research/agents_t276/LEDGER_T276.csv: every buried ground-beam face traced once (T-276 r2 MERGED 4d88681b,
               Verifier 2026-10-24 22:54 Gate A PASS); the T-263 run-face ledger is SUPERSEDED for these side faces
  necks        research/agents_t263/LEDGER_T263.csv NECK rows (36 necks; count cross-checked against the T-217 neck census
               research/agents_t217/LEDGER_T217.csv storey FOUNDATION existence DRAWN)
  soffits, boundary, straps, ground slab   research/agents_t263/LEDGER_T263.csv (T-263 MERGED c0ab564d, Verifier 17:59)
The quantity of an inventory element is the drawn measure where the drawing establishes it (outline area, printed
thickness, traced face) and None where it is HELD (never 0).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import t301_wp_inventory as W  # noqa: E402

FAM = "WP.FOUNDATION"
FLOOR = "FDN"
I233 = "research/agents_t233/ALSENAN_FOOTING_INPUT.json"
L276 = "research/agents_t276/LEDGER_T276.csv"
L263 = "research/agents_t263/LEDGER_T263.csv"
L217 = "research/agents_t217/LEDGER_T217.csv"
L219 = "research/agents_t219/LEDGER_T219.csv"
EXTRACT = HERE / "CANDIDATE_V3017_WP.json"
SH = "ST7757 dxf.dxf"
P13 = "ST7757.pdf p.13 typical isolated-footing details"
P14 = "ST7757.pdf p.14 lift detail (with isolated footing, without basement)"
SCREED_T = 0.05                                  # printed '5cm Screed' (p.13, p.14)
LIFT = {"outline": "1B2B", "a": 4.600, "b": 4.500, "base_h": 0.55, "envelope_m2": 4.890}
MEMBRANE = "WP.FOUNDATION.FOOTING_MEMBRANE"
SCREED = "WP.FOUNDATION.FOOTING_SCREED"
SIDES = "WP.FOUNDATION.FOOTING_SIDES"
PIT_M, PIT_B, PIT_S = "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_BOARD", "WP.FOUNDATION.LIFT_PIT_SCREED"
LIQ = "WP.FOUNDATION.BURIED_LIQUID"
PROC = "WP.FOUNDATION.PROCUREMENT"


def _rows(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _el(item, unit, element, face, src, qty=None, na=None, owner=None, ref=None, note=None):
    e = {"family": FAM, "item_code": item, "unit": unit, "element": element, "face": face, "floor": FLOOR,
         "applicability": "NOT_APPLICABLE" if na else "APPLICABLE", "qty": None if na else qty, "source": src,
         "ref": ref, "owner": owner, "note": note}
    if na:
        e["evidence"] = na
    return e


def gb_face(x):
    """the T-276 face id (as the candidate's BURIED_LIQUID components name it)."""
    return x["face"].split(" (")[0]


def footing_elements():
    d = json.loads((ROOT / I233).read_text(encoding="utf-8"))
    out = []
    src = "T-233 footing outlines (MERGED 2ecb5bf0, Checker 2026-10-23 20:14)"
    t263 = {x["element"]: x for x in _rows(L263) if x["member"] == "FOOTING"}
    for o in sorted(d["outlines"], key=lambda o: o["id"]):
        el = f"FTG:{o['id']}"
        ref = f"{SH} outline {o['id']} tag {'+'.join(o['tags'])}"
        if o["tags"] == ["FF"]:                     # the lift footing: the p.14 lift system owns every face of it
            ev = {"sheet": P14, "ref": f"{ref}: the lift footing takes the p.14 sheet membrane / board / screed system "
                                       "(T-219 LIFT:LIFT-01), not the p.13 footing underlay"}
            for item, unit, face in ((MEMBRANE, "m2", "UNDERSIDE"), (SCREED, "m2", "UNDERSIDE"),
                                     (SCREED, "m3", "UNDERSIDE"), (SIDES, "m2", "SIDES")):
                out.append(_el(item, unit, el, face, src, na=ev, owner="WP.FOUNDATION.LIFT_PIT_*", ref=ref))
            tx = t263[el]
            out.append(_el(LIQ, "m2", el, "TOP_OUTSIDE_NECKS", src, ref=ref, owner=PIT_M,
                           na={"sheet": P14, "ref": f"{ref}: {tx['basis'][:160]} (T-263 EXCLUDED)"}))
            continue
        conflict = len(o["tags"]) > 1               # Q-31 C: one outline, two tags: the area is not established
        a = None if conflict else float(o["area"])
        note = "two schedule tags: area HELD (Q-31 C)" if conflict else None
        out.append(_el(MEMBRANE, "m2", el, "UNDERSIDE", src, qty=a, ref=ref, note=note))
        out.append(_el(SCREED, "m2", el, "UNDERSIDE", src, qty=a, ref=ref, note=note))
        out.append(_el(SCREED, "m3", el, "UNDERSIDE", src, qty=None if a is None else round(a * SCREED_T, 6), ref=ref,
                       note=note))
        out.append(_el(SIDES, "m2", el, "SIDES", src, ref=ref, note="governing detail not selected (Q-21 C)"))
        out.append(_el(LIQ, "m2", el, "TOP_OUTSIDE_NECKS", src, ref=ref,
                       note="coating on the right p.13 detail only (Q-21 C)" + ("; " + note if note else "")))
    return out


def lift_elements():
    src = "T-219 lift pit read (MERGED de7c1c4c, Verifier 2026-10-24 10:40) on outline 1B2B FF + p.14"
    el, ref = "LIFT-01", f"{SH} outline {LIFT['outline']} tag FF; ring 10EB; C9 1090"
    base = round(LIFT["a"] * LIFT["b"], 6)                                         # 20.700
    sides = round(2 * (LIFT["a"] + LIFT["b"]) * (LIFT["base_h"] + SCREED_T), 6)     # 18.200 x 0.60 = 10.920
    top = round(base - LIFT["envelope_m2"], 6)                                      # 15.810
    no_board = {"sheet": P14, "ref": f"{ref}: protection board drawn on the sides, the top and the walls, not under "
                                     "the base (T-219 'no board under the base', Verifier 10:40 own read)"}
    return [_el(PIT_M, "m2", el, "BASE_SOFFIT", src, qty=base, ref=ref),
            _el(PIT_M, "m2", el, "BASE_SCREED_SIDES", src, qty=sides, ref=ref),
            _el(PIT_M, "m2", el, "BASE_TOP_OUTSIDE_ENVELOPE", src, qty=top, ref=ref),
            _el(PIT_M, "m2", el, "WALLS_OUTER", src, ref=ref, note="pit depth not printed (D-43)"),
            _el(PIT_B, "m2", el, "BASE_SOFFIT", src, na=no_board, ref=ref),
            _el(PIT_B, "m2", el, "BASE_SCREED_SIDES", src, qty=sides, ref=ref),
            _el(PIT_B, "m2", el, "BASE_TOP_OUTSIDE_ENVELOPE", src, qty=top, ref=ref),
            _el(PIT_B, "m2", el, "WALLS_OUTER", src, ref=ref, note="pit depth not printed (D-43)"),
            _el(PIT_S, "m2", el, "UNDER_BASE", src, qty=base, ref=ref),
            _el(PIT_S, "m3", el, "UNDER_BASE", src, qty=round(base * SCREED_T, 6), ref=ref)]


def buried_elements():
    out = []
    s276 = "T-276 r2 buried-face trace (MERGED 4d88681b, Verifier 2026-10-24 22:54)"
    s263 = "T-263 buried-concrete ledger (MERGED c0ab564d, Verifier 2026-10-24 17:59)"
    for x in _rows(L276):
        if x["member"] == "NECK":
            continue                    # beam-zone neck faces: the deduction from the neck faces, not an element
        el, face = x["element"], gb_face(x)
        if x["status"] == "EXCLUDED":
            lift = x["member"] == "LIFT_PIT"
            out.append(_el(LIQ, "m2", el, face, s276, owner=PIT_M if lift else None, ref=f"{SH} {el}",
                           na={"sheet": P14 if lift else P13 + " note + p.14 N.G. level", "ref": x["basis"][:200]}))
        elif x["status"] == "DRAWING-CONFIRMED":
            out.append(_el(LIQ, "m2", el, face, s276, qty=float(x["qty"]), ref=f"{SH} {el}"))
        else:
            out.append(_el(LIQ, "m2", el, face, s276, ref=f"{SH} {el}", note=x["held_why"][:120]))
    for x in _rows(L263):
        m = x["member"]
        if m == "NECK":
            if x["status"] == "EXCLUDED":
                out.append(_el(LIQ, "m2", x["element"], "SIDES_BELOW_BEAM_ZONE", s263, owner=PIT_M,
                               ref=f"{SH} {x['element']}", na={"sheet": P14, "ref": x["basis"][:200]}))
            else:
                out.append(_el(LIQ, "m2", x["element"], "SIDES_BELOW_BEAM_ZONE", s263, ref=f"{SH} {x['element']}",
                               note="neck height HELD (Q-21 C)"))
        elif m == "GROUND_BEAM" and x["status"] == "EXCLUDED" and x["face"].startswith("soffit"):
            out.append(_el(LIQ, "m2", x["element"], "SOFFIT", s263, ref=f"{SH} {x['element']}",
                           na={"sheet": P13, "ref": x["basis"][:200]}))
        elif m in ("BOUNDARY_GB", "STRAP"):
            out.append(_el(LIQ, "m2", x["element"], x["face"], s263, ref=x["element"], note=x["held_why"][:120]))
        elif m == "GROUND_SLAB":
            out.append(_el(LIQ, "m2", x["element"], "SOFFIT", s263, ref=x["element"],
                           na={"sheet": P13 + " + slab on grade", "ref": x["basis"][:200]}))
        elif m == "LIFT_PIT":
            out.append(_el(LIQ, "m2", x["element"], "OUTER_WALL_FACES", s263, owner=PIT_M, ref=x["element"],
                           na={"sheet": P14, "ref": x["basis"][:200]}))
    out.append(_el(PROC, "item", "FOUNDATION_WP", "SUPPLY", "UP-WP-MAT-001 (product not printed)",
                   note="a supply quantity, not a face: HELD until a product is printed"))
    return out


def inventory():
    els = footing_elements() + lift_elements() + buried_elements()
    W.validate_inventory(els)
    return els


def crosschecks():
    """element presence from a second census: necks (T-263) vs the T-217 neck census; footings (T-233) vs T-219."""
    necks_217 = sum(1 for r in _rows(L217) if r["storey"] == "FOUNDATION" and r["existence"] == "DRAWN")
    necks_263 = sum(1 for r in _rows(L263) if r["member"] == "NECK")
    ftg_233 = len(json.loads((ROOT / I233).read_text(encoding="utf-8"))["outlines"])
    ftg_219 = len({r["outline"] for r in _rows(L219)})
    return {"necks": {"T-217 census DRAWN": necks_217, "T-263 ledger": necks_263, "agree": necks_217 == necks_263},
            "footings": {"T-233 outlines": ftg_233, "T-219 outlines": ftg_219, "agree": ftg_233 == ftg_219}}


# ------------------------------------------------------------------------------------------------ candidate lines
def extract(run_dir):
    """the waterproofing lines of a V3.0.17 run (ids, codes, states, quantities, component ids / values only)."""
    import engine.source.trade_completeness_v1 as TC
    p = Path(run_dir) / "V3_0_17_BOQ_LINES.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    lines = raw["lines"] if isinstance(raw, dict) else raw
    out = []
    for ln in lines:
        if TC.line_trade(ln) != "WATERPROOFING" and "WP" not in (ln.get("item_code") or ""):
            continue
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        f = inp.get("foundation_wp_v3015") or {}
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
                    "evidence_state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
                    "floor": (ln.get("location") or {}).get("floor"),
                    "element_id": (ln.get("location") or {}).get("element_id"), "trade": ln.get("trade"),
                    "subtrade": ln.get("subtrade"), "record_element": f.get("element"),
                    "components": [{"id": c["id"], "value": c.get("value")} for c in f.get("components") or []]})
    out.sort(key=lambda x: (x["item_code"], x["unit"], x["line_id"]))
    return {"source": f"{p.name} (ARCH_TAKEOFF_V3.0.17 run)", "lines": out}


def _held_keys(els, item, unit, pred):
    return [W.element_key(e) for e in els if e["item_code"] == item and e["unit"] == unit and
            e["applicability"] == "APPLICABLE" and pred(e)]


def links(lines, els):
    """line_id -> inventory keys. A released record names its components (element ids); a held record names its
    element in words, read here per record (each mapping stated, never a fallback)."""
    keys = {W.element_key(e): e for e in els}
    out, unread = {}, []
    face_of = {"base soffit": "BASE_SOFFIT", "base + screed sides": "BASE_SCREED_SIDES",
               "base top outside the pit envelope": "BASE_TOP_OUTSIDE_ENVELOPE", "base": "UNDER_BASE"}
    t276_held = {(x["element"], gb_face(x)) for x in _rows(L276) if x["member"] == "GROUND_BEAM" and
                 x["status"] == "HELD"}
    t276_cid = {f"{x['element']} {gb_face(x)}": (x["element"], gb_face(x)) for x in _rows(L276)
                if x["member"] == "GROUND_BEAM"}
    for ln in lines:
        ic, u, rel = ln["item_code"], ln["unit"], ln.get("record_element") or ""
        ks = []
        if not ic.startswith("WP.FOUNDATION."):
            unread.append(ln["line_id"])            # another family: no inventory yet (named gap)
            continue
        if ln["components"]:
            for c in ln["components"]:
                cid = c["id"]
                if cid.startswith("FTG:"):
                    face = "UNDERSIDE"
                    ks.append(f"{ic}[{u}]/{cid}/{face}")
                elif cid.startswith("LIFT-01 "):
                    ks.append(f"{ic}[{u}]/LIFT-01/{face_of[cid[len('LIFT-01 '):]]}")
                elif cid in t276_cid:                # a T-276 face: '<element> <face>' exactly as the ledger names it
                    ks.append(f"{ic}[{u}]/{t276_cid[cid][0]}/{t276_cid[cid][1]}")
                else:
                    ks.append(f"{ic}[{u}]/?/{cid}")  # names no drawn element: REGISTER_ONLY, never dropped
        elif rel.endswith("_1B1B"):
            ks = [f"{ic}[{u}]/FTG:1B1B/UNDERSIDE"]
        elif rel == "FOOTING_SIDE_FACES":
            ks = _held_keys(els, ic, u, lambda e: e["face"] == "SIDES")
        elif rel in ("LIFT_PIT_MEMBRANE_WALLS", "LIFT_PIT_BOARD_WALLS"):
            ks = [f"{ic}[{u}]/LIFT-01/WALLS_OUTER"]
        elif rel == "BURIED_GROUND_BEAM_FACES_HELD":
            ks = sorted(f"{ic}[{u}]/{el}/{face}" for el, face in t276_held)
        elif rel == "FOOTING_TOPS_OUTSIDE_NECKS":
            ks = _held_keys(els, ic, u, lambda e: e["face"] == "TOP_OUTSIDE_NECKS")
        elif rel == "NECK_FACES":
            ks = _held_keys(els, ic, u, lambda e: e["face"] == "SIDES_BELOW_BEAM_ZONE")
        elif rel == "BOUNDARY_GB_AND_STRAPS":
            ks = _held_keys(els, ic, u, lambda e: e["element"].startswith(("BOUNDARY", "STRAPS")))
        elif rel == "FOUNDATION_WP_PROCUREMENT":
            ks = [f"{ic}[{u}]/FOUNDATION_WP/SUPPLY"]
        else:
            unread.append(ln["line_id"])
            continue
        out[ln["line_id"]] = ks
    missing_keys = sorted({k for ks in out.values() for k in ks} - set(keys))
    return out, unread, missing_keys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", help="a V3.0.17 run directory (writes CANDIDATE_V3017_WP.json)")
    ap.add_argument("--out", help="directory for the inventory csv / report json")
    a = ap.parse_args(argv)
    if a.extract:
        EXTRACT.write_text(json.dumps(extract(a.extract), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("wrote", EXTRACT.relative_to(ROOT))
        return 0
    els = inventory()
    cand = json.loads(EXTRACT.read_text(encoding="utf-8"))["lines"]
    fl = [ln for ln in cand if ln["item_code"].startswith("WP.FOUNDATION.")]
    lk, unread, mk = links(fl, els)
    rep = W.join(els, fl, lk)
    rep["crosschecks"] = crosschecks()
    rep["other_wp_lines"] = dict(Counter(f"{ln['item_code']} {ln['unit']} {ln['evidence_state']}" for ln in cand
                                         if not ln["item_code"].startswith("WP.FOUNDATION.")))
    rep["unread_lines"] = unread
    print("counts", rep["counts"], "register_only", len(rep["register_only"]), "unlinked", rep["unlinked_lines"],
          "unread", unread, "keys not in inventory", mk[:5])
    for f in rep["families"]:
        print(f"{f['item_code']:<34} {f['unit']:<4} el {f['elements']:>3} in {f['in_line']:>3} (q {f['in_line_quantity']:>3}"
              f" h {f['in_line_held']:>3}) na {f['not_applicable']:>3} miss {f['missing']:>2}  inv {f['inventory_qty_in_line']}"
              f"  line {f['line_qty']}  res {f['residual']}")
    print("crosschecks", rep["crosschecks"])
    print("other WP lines (no inventory: named gap)", rep["other_wp_lines"])
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        cols = ("key", "family", "item_code", "unit", "element", "face", "floor", "status", "line_id", "line_state",
                "qty", "owner", "evidence", "source", "note")
        with open(out / "WP_FOUNDATION_INVENTORY_T301.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            for r in rep["elements"]:
                w.writerow({c: (json.dumps(r[c], sort_keys=True) if isinstance(r[c], dict) else
                                ("" if r[c] is None else r[c])) for c in cols})
        (out / "WP_FOUNDATION_REPORT_T301.json").write_text(json.dumps(
            {k: rep[k] for k in ("schema", "rule_id", "counts", "families", "register_only", "unlinked_lines",
                                 "crosschecks", "other_wp_lines", "unread_lines")}, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
