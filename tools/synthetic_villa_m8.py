"""SYNTHETIC VILLA M8 - the M6 completeness villa with the DESIGN of every scope element it draws, so that the
measured or bounded quantity of each element can be scored against a design truth.

    python3 -I tools/synthetic_villa_m8.py OUT_DIR SEED [SEED ...] [--heldout-vocabulary] [--hard]

tools/synthetic_villa_m6.py draws the elements (pool shell, lift pit, pit in a footing, roof tank, dome ring with or
without ribs, stair flight, sunken outline, boundary wall, unknown outline) and stays unchanged. This generator
re-opens that drawing and, from its own random stream, gives each element the dimensions a plan does not show - the
design the generator author assumes - and in about half of the elements writes them beside the element as a note,
the way a structural plan prints them:

  POOL           wall height 1.10 - 2.10 m, floor 0.20 - 0.35 m          note  "DEPTH 1.65 M, FLOOR 250"
  LIFT_PIT       pit depth 0.90 - 1.70 m, base 0.20 - 0.30 m             note  "DEPTH 1.30 M, BASE 250"
  PIT_IN_FOOTING pit depth 0.90 - 1.70 m (the footing is its base)       note  "DEPTH 1.30 M"
  WATER_TANK     wall height 1.10 - 2.10 m, cover 0.15 - 0.25 m (on the roof slab: no base)
                                                                          note  "HEIGHT 1.60 M, COVER 200"
  DOME           rise 0.40 - 1.00 x the inner radius, shell 0.10 - 0.15 m, ring depth 0.30 - 0.65 m
                                                                          note  "RISE 1.10 M, SHELL 120, RING 450"
  STAIR          riser 0.150 - 0.185 m, waist 0.14 - 0.21 m; n goings drawn = n + 1 risers
                                                                          note  "RISER 165, WAIST 150"
  SUNKEN_SLAB    drop 0.05 - 0.45 m (the edge: perimeter x drop x slab thickness)          never printed
  BOUNDARY_WALL  tie beam depth 0.40 - 0.70 m, half the walls on a strip footing 0.50 - 0.90 x 0.25 m; when the
                 schedule's unread row is 'B.W' and the wall is 0.2 m wide, the row (0.2 x 0.6) is the whole section
  UNKNOWN_OUTLINE a plinth 0.10 - 0.30 m high                                                never printed

The design ranges are the author's, written before any M8 run and deliberately a little wider than the V6
conventions (so that a convention range can miss). Truth formulas (independent of the engine):

  POOL        ring area x wall height + outer area x floor
  LIFT_PIT    ring area x depth + outer area x base;  PIT_IN_FOOTING ring area x depth
  WATER_TANK  ring area x wall height + outer area x cover
  DOME        pi (ri^2 + h^2) x shell + pi (r^2 - ri^2) x ring depth   (ri = r - 0.2, h = rise)
  STAIR       width x (n x going x riser / 2 + waist x hypot(n x going, (n + 1) x riser)) for the flight; the bay
              round it is landing or void (the drawing does not say): truth range flight .. flight + (bay panel -
              flight plan) x the thicker of the slab and the waist (slab or landing)
  SUNKEN      perimeter x drop x the storey's slab thickness
  BOUNDARY    length x (width x beam depth + footing area)
  UNKNOWN     area x plinth height

Synthetic drawings share the generator author's drafting assumptions; the scores test that the measuring rules read
geometry and printed notes correctly and that the convention ranges cover the author's design spread - not
real-drawing accuracy. The truth never reads the engine.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import synthetic_villa as SV              # noqa: E402
from tools import synthetic_villa_m6 as SM6          # noqa: E402

FAMILY = {"POOL": "POOL", "LIFT_PIT": "LIFT", "PIT_IN_FOOTING": "LIFT", "WATER_TANK": "WATER_TANK", "DOME": "DOMES",
          "STAIR": "STAIRS", "SUNKEN_SLAB": "SLAB_STEP", "BOUNDARY_WALL": "BOUNDARY_WALL",
          "UNKNOWN_OUTLINE": "UNKNOWN"}
PRINTABLE = ("POOL", "LIFT_PIT", "PIT_IN_FOOTING", "WATER_TANK", "DOME", "STAIR")


def _ring(el):
    m = el.get("magnitude") or {}
    b = el["box"]
    outer = (b[2] - b[0]) * (b[3] - b[1])
    if el["kind"] == "POOL":
        return m["ring_area_m2"], outer
    if el["kind"] == "PIT_IN_FOOTING":
        return m["outer_area_m2"] - m["inner_area_m2"], m["outer_area_m2"]
    w, h = b[2] - b[0], b[3] - b[1]
    return outer - (w - 0.4) * (h - 0.4), outer                # walls 0.2 m drawn (lift pit, tank)


def design(el, R, slab_t, sched_unread):
    """the hidden design of one drawn element, its truth volume and the note that prints it (or None)."""
    k = el["kind"]
    b = el.get("box")
    out = {"kind": k, "family": FAMILY[k], "id": el["id"], "sheet": el["sheet"], "box": b}
    if k == "POOL":
        H, tf = round(R.uniform(1.10, 2.10), 2), R.choice([0.20, 0.25, 0.30, 0.35])
        ring, outer = _ring(el)
        out.update(design={"wall_height_m": H, "floor_t_m": tf}, truth_m3=ring * H + outer * tf,
                   note=f"DEPTH {H:.2f} M, FLOOR {tf * 1000:.0f}")
    elif k in ("LIFT_PIT", "PIT_IN_FOOTING"):
        d, tb = round(R.uniform(0.90, 1.70), 2), R.choice([0.20, 0.25, 0.30])
        ring, outer = _ring(el)
        base = 0.0 if k == "PIT_IN_FOOTING" else outer * tb
        out.update(design={"depth_m": d, "base_t_m": None if k == "PIT_IN_FOOTING" else tb},
                   truth_m3=ring * d + base,
                   note=f"DEPTH {d:.2f} M" + ("" if k == "PIT_IN_FOOTING" else f", BASE {tb * 1000:.0f}"))
    elif k == "WATER_TANK":
        H, tc = round(R.uniform(1.10, 2.10), 2), R.choice([0.15, 0.20, 0.25])
        ring, outer = _ring(el)
        out.update(design={"wall_height_m": H, "cover_t_m": tc}, truth_m3=ring * H + outer * tc,
                   note=f"HEIGHT {H:.2f} M, COVER {tc * 1000:.0f}")
    elif k == "DOME":
        r = el["magnitude"]["radius_m"]
        ri = r - 0.2
        h = round(R.uniform(0.40, 1.00) * ri, 2)
        t, dr = R.choice([0.10, 0.12, 0.15]), round(R.uniform(0.30, 0.65), 2)
        out.update(design={"r_m": r, "ri_m": ri, "rise_m": h, "shell_t_m": t, "ring_depth_m": dr},
                   truth_m3=math.pi * (ri * ri + h * h) * t + math.pi * (r * r - ri * ri) * dr,
                   note=f"RISE {h:.2f} M, SHELL {t * 1000:.0f}, RING {dr * 1000:.0f}")
    elif k == "STAIR":
        n, go = el["magnitude"]["n_treads"], el["magnitude"]["going_m"]
        wf = b[2] - b[0]
        Rr, w = round(R.uniform(0.150, 0.185), 3), round(R.uniform(0.14, 0.21), 3)
        out.update(design={"risers": n + 1, "riser_m": Rr, "waist_m": w, "going_m": go, "width_m": round(wf, 3),
                           "goings": n},
                   truth_m3=wf * (n * go * Rr / 2.0 + w * math.hypot(n * go, (n + 1) * Rr)),
                   note=f"RISER {Rr * 1000:.0f}, WAIST {w * 1000:.0f}")
    elif k == "SUNKEN_SLAB":
        d = round(R.uniform(0.05, 0.45), 2)
        per = 2 * ((b[2] - b[0]) + (b[3] - b[1]))
        t = slab_t.get(el["sheet"]) or slab_t.get("GF")
        out.update(design={"drop_m": d, "slab_t_m": t}, truth_m3=per * d * t, note=None)
    elif k == "BOUNDARY_WALL":
        m = el["magnitude"]
        L, w = m["strip_length_m"], m["strip_width_m"]
        if sched_unread == "B.W" and abs(w - 0.2) < 1e-9:
            out.update(design={"beam_m": [0.2, 0.6], "footing_m2": 0.0, "printed_by": "schedule row B.W"},
                       truth_m3=L * 0.2 * 0.6, note=None, printed=True)
            return out
        hb = round(R.uniform(0.40, 0.70), 2)
        ft = round(R.uniform(0.50, 0.90), 2) * 0.25 if R.random() < 0.5 else 0.0
        out.update(design={"beam_m": [w, hb], "footing_m2": round(ft, 4)}, truth_m3=L * (w * hb + ft), note=None)
    elif k == "UNKNOWN_OUTLINE":
        h = round(R.uniform(0.10, 0.30), 2)
        out.update(design={"plinth_m": h}, truth_m3=el["magnitude"]["area_m2"] * h, note=None)
    else:
        return None
    out["truth_m3"] = round(out["truth_m3"], 4)
    return out


def _bay_of(D, box_local):
    """the design bay (i, j) a sheet-local box lies in (local = design + 4 m)."""
    xs, ys = D["xs"], D["ys"]
    cx, cy = (box_local[0] + box_local[2]) / 2 - 4.0, (box_local[1] + box_local[3]) / 2 - 4.0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if xs[i] <= cx <= xs[i + 1] and ys[j] <= cy <= ys[j + 1]:
                return i, j
    return None


def generate(out_dir, seed, *, vocabulary="dev", hard=False, m6v2=True, defects=False, print_share=0.5):
    import ezdxf
    out = Path(out_dir)
    src = SM6.generate(out, seed, defects=defects, vocabulary=vocabulary, hard=hard, m6v2=m6v2)
    T = json.loads((out / f"villa_m6_{seed}.truth.json").read_text(encoding="utf-8"))
    D = SV.design(seed)
    R = random.Random(seed * 7919 + 801)                 # M8 stream: never touches the M2 / M6 draws
    s = 1.0 if D["var"]["units"] == "m" else 1000.0
    text_layer = D["var"]["layers"]["text"]
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    els = T["m6"]["elements"]
    sched_unread = next((e.get("token") for e in els if e["kind"] == "SCHEDULE_UNREAD"), None)
    slab_t = dict(D["slab_t"])
    rows = []
    for el in els:
        if el["kind"] not in FAMILY or not el.get("box"):
            continue
        rec = design(el, R, slab_t, sched_unread)
        if rec is None:
            continue
        printed = bool(rec.pop("printed", False))
        note = rec.pop("note", None)
        if note and el["kind"] in PRINTABLE and R.random() < print_share:
            sh = SM6._Sheet(D, el["sheet"])
            b = el["box"]                                   # sheet-local m = design + 4
            x, y = b[0] - 4.0, b[1] - 4.0 - 0.45            # just below the element's box
            t = msp.add_text(note, dxfattribs={"layer": text_layer, "height": 0.15 * s})
            t.set_placement(sh.P(x, y))
            printed = True
            rec["note"] = note
        rec["printed"] = printed
        if el["kind"] == "STAIR":
            # the bay round a drawn flight is landing / slab or a void - the drawing does not say: the truth is the
            # flight .. the flight + the rest of its bay at the storey's slab thickness
            bay = _bay_of(D, el["box"])
            a = sum(q["area"] for q in T["component_list"]["panels"] if q["storey"] == el["sheet"] and
                    (q["i"], q["j"]) == bay)
            plan = rec["design"]["width_m"] * rec["design"]["goings"] * rec["design"]["going_m"]
            t_rest = max(slab_t[el["sheet"]], rec["design"]["waist_m"])
            rec["truth_high_m3"] = round(rec["truth_m3"] + max(a - plan, 0.0) * t_rest, 4)
            rec["truth_rule"] = "flight .. flight + (bay panel - flight plan) x the thicker of slab and waist"
        rows.append(rec)
    path = out / f"villa_m8_{seed}.dxf"
    doc.saveas(str(path))
    T["m8"] = {"seed": seed, "elements": rows, "print_share": print_share,
               "rule": "design values are the generator's; printed ones are written beside the element; the truth "
                       "never reads the engine"}
    (out / f"villa_m8_{seed}.truth.json").write_text(json.dumps(T, indent=1, ensure_ascii=False, default=str),
                                                     encoding="utf-8")
    prof = out / f"villa_m6_{seed}.profile.json"
    (out / f"villa_m8_{seed}.profile.json").write_text(prof.read_text(encoding="utf-8"), encoding="utf-8")
    return path


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for sd in args[1:]:
        print(generate(args[0], int(sd), vocabulary="heldout" if "--heldout-vocabulary" in sys.argv else "dev",
                       hard="--hard" in sys.argv))
