"""S8.3 errata (dated correction layer over the frozen S8.3 package; the frozen files are never written).

    python3 -I research/alsenan_dome_ring_s8_3/errata/build_errata.py

Found by re-auditing the frozen package against the brief's "anchorage and junction bars" item. Reads only the
registered structural and architectural DXFs and the frozen S8.3 outputs; no earlier Urban or third-party figure.

  S8.3-E01  07_REBAR_NOTATION_REGISTER.csv row N-RING-DOTS says the right ring cut draws only part of the labelled
            bars. Both cuts draw all of them (3 bottom + 2 + 2 side + 3 top); the earlier reading used a scan window
            that stopped short of the right cut's outer bars. Graphic only: no family or quantity changes.
  S8.3-E02  each cut also draws one unlabelled small bar inside the bend of the shell bar, under the shell footprint
            just below the springing. It is a bar object the register does not list. One physical family per dome
            (the two cuts are the one ring): UNLABELLED_JUNCTION_BAR, BLOCKED_UNQUANTIFIED (no label, no stated
            diameter, role or length; the detail is N.I.S).
  S8.3-E03  evidence for the mirrored-block test on the real drawings: every dome, ring and detail entity is drawn
            with a +Z extrusion and no dome entity sits in a mirrored insert; the architectural DXF's mirrored inserts
            are door and window blocks away from the domes.
Released quantities are unchanged: the errata add no m3 and no kg.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402

DATE = "2026-10-09"
MANIFEST = PKG / "16_S8_3_FREEZE_MANIFEST.json"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
RING_SECTIONS = ("1A0A", "1A07")
SHELL_BAR_LINE = "1A09"
SHEETS = ("FFRS", "SFRS", "DET")
OUT = ["01_S8_3_ERRATA.csv", "02_ERRATA_SUMMARY.json", "00_ERRATA_README.md"]


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def build():
    import alsenan_structural_s1 as S1
    import ezdxf
    before = DR.verify_frozen(MANIFEST, ROOT)
    frozen = json.loads((PKG / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))
    src = S1.Source()
    E = src.entities()["DET"]
    by = {e["handle"]: e for e in E}
    # ---------------------------------------------------------------- E01 / E02: bars drawn in each ring cut
    cuts = []
    for h in RING_SECTIONS:
        pts = by[h]["pts"]
        x0, y0, x1, y1 = min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)
        dots = [e for e in E if e["type"] == "CIRCLE" and e["layer"] == "S-HAT.BAT" and x0 < e["c"][0] < x1
                and y0 < e["c"][1] < y1]
        big = sorted({round(e["r"], 3) for e in dots})[-1]
        labelled = [e for e in dots if abs(e["r"] - big) < 1e-6]
        small = [e for e in dots if abs(e["r"] - big) >= 1e-6]
        rows_y = Counter(round(e["c"][1]) for e in labelled)
        outer_x = x0 if h == RING_SECTIONS[0] else x1          # the face away from the dome axis
        cuts.append({"cut": h, "labelled": len(labelled), "by_row": [rows_y[k] for k in sorted(rows_y)],
                     "small": [{"handle": e["handle"], "from_outer_face": abs(e["c"][0] - outer_x),
                                "below_ring_top": y1 - e["c"][1], "r_ratio": e["r"] / big} for e in small],
                     "bbox": [x0, y0, x1, y1]})
    bar = by[SHELL_BAR_LINE]
    legs = sorted({round(p[0], 1) for p in bar["pts"]})
    check_all = all(c["labelled"] == 10 and c["by_row"] == [3, 2, 2, 3] and len(c["small"]) == 1 for c in cuts)
    if not check_all:
        raise SystemExit(f"STOP: ring cuts are not as recorded: {cuts}")
    # the small bar sits against the outer leg of the shell bar where it turns down into the ring
    legx = [min(legs), max(legs)]
    touch = []
    for c, lx in zip(cuts, (min(x for x in legx if x < 20000), max(x for x in legx if x > 20000))):
        s = c["small"][0]
        e = by[s["handle"]]
        touch.append(bool(abs(abs(e["c"][0] - lx) - e["r"]) < 1.0))
    # ---------------------------------------------------------------- E03: extrusion / mirror census
    def census(doc, msp, frame_of=None):
        ext, mirrored = Counter(), []
        for e in msp:
            t = e.dxftype()
            if t in ("ARC", "CIRCLE", "LWPOLYLINE", "LINE", "INSERT"):
                z = tuple(round(v, 6) for v in e.dxf.get("extrusion", (0.0, 0.0, 1.0)))
                where = frame_of(e) if frame_of else None
                if frame_of is None or where in SHEETS:
                    ext[(where, z)] += 1
            if t == "INSERT" and (e.dxf.xscale < 0 or e.dxf.yscale < 0):
                mirrored.append({"handle": e.dxf.handle, "block": e.dxf.name,
                                 "sheet": frame_of(e) if frame_of else None,
                                 "at": [round(e.dxf.insert.x), round(e.dxf.insert.y)]})
        return ext, mirrored

    def frame_of(e):
        try:
            p = e.dxf.insert if e.dxftype() == "INSERT" else (e.dxf.center if e.dxftype() in ("ARC", "CIRCLE") else
                                                              (e.dxf.start if e.dxftype() == "LINE" else None))
            if p is None:
                p = next(iter(e.get_points("xy")))
                return src.sheet_of(p[0], p[1])
            return src.sheet_of(p.x, p.y)
        except Exception:
            return None
    st_ext, st_mir = census(src.doc, src.msp, frame_of)
    arch = ezdxf.readfile(BY_SHA / f"{ARCH_SHA}.dxf")
    a_ext, a_mir = census(arch, arch.modelspace())
    dome_centres = [(-236934.1, -799990.1), (-222486.3, -799990.1), (-229250.2, -795134.1)]
    a_near = [m for m in a_mir if min(math.dist(m["at"], c) for c in dome_centres) < 3000]
    st_nonz = sum(n for (w, z), n in st_ext.items() if z != (0.0, 0.0, 1.0))
    a_nonz = sum(n for (w, z), n in a_ext.items() if z != (0.0, 0.0, 1.0))
    st_dome_mir = [m for m in st_mir if m["sheet"] in SHEETS]
    rows = [
        {"ERRATUM_ID": "S8.3-E01", "OUTPUT": "07_REBAR_NOTATION_REGISTER.csv", "ROW": "N-RING-DOTS",
         "KIND": "NOTE_CORRECTION", "WAS": "the right cut draws a part of them",
         "IS": f"both cuts draw all labelled bars: {cuts[0]['by_row']} and {cuts[1]['by_row']} (bottom, side, side, "
               "top) plus one unlabelled small bar each (E02)",
         "QUANTITY_EFFECT": "none (graphic completeness only)", "LANE": "", "EVIDENCE": [c["cut"] for c in cuts]},
        {"ERRATUM_ID": "S8.3-E02", "OUTPUT": "07_REBAR_NOTATION_REGISTER.csv / 08_REBAR_QTO_REGISTER.csv",
         "ROW": "(missing row)", "KIND": "OBJECT_ADDED", "WAS": "not listed",
         "IS": "UNLABELLED_JUNCTION_BAR: one per cut ("
               + ", ".join(f"{s['handle']}: {s['from_outer_face']:.1f} units from the outer face, "
                           f"{s['below_ring_top']:.1f} below the ring top, drawn {s['r_ratio']:.3f} of a labelled bar"
                           for c in cuts for s in c["small"])
               + "); it bears on the outer leg of the shell bar where that bar turns down into the ring; one family "
                 "per dome (the two cuts are the one ring)",
         "QUANTITY_EFFECT": "none: BLOCKED_UNQUANTIFIED for DOME-A and DOME-B (no label, no stated diameter, role or "
                            "length; N.I.S drawing)", "LANE": "BLOCKED_UNQUANTIFIED",
         "EVIDENCE": [s["handle"] for c in cuts for s in c["small"]] + [SHELL_BAR_LINE]},
        {"ERRATUM_ID": "S8.3-E03", "OUTPUT": "evidence (no frozen row changes)", "ROW": "", "KIND": "EVIDENCE_ADDED",
         "WAS": "the mirrored-block test is synthetic only in the package",
         "IS": f"structural sheets {list(SHEETS)}: {sum(st_ext.values())} primitives and inserts, {st_nonz} with a "
               f"non +Z extrusion, {len(st_dome_mir)} mirrored inserts; architectural DXF: {a_nonz} non +Z extrusions, "
               f"{len(a_mir)} mirrored inserts ({', '.join(sorted({m['block'] for m in a_mir}))}), "
               f"{len(a_near)} within 3 m of a dome centre",
         "QUANTITY_EFFECT": "none", "LANE": "", "EVIDENCE": sorted(m["handle"] for m in a_mir)}]
    after = DR.verify_frozen(MANIFEST, ROOT)
    assert before["manifest_sha256"] == after["manifest_sha256"], "the frozen package changed"
    for o in OUT:
        if (HERE / o).exists():
            (HERE / o).unlink()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(v) for k, v in r.items()})
    (HERE / OUT[0]).write_text(buf.getvalue(), encoding="utf-8")
    summary = {"layer": "S8_3_ERRATA", "date": DATE, "corrects": "S8.3 (frozen, unchanged)",
               "frozen_manifest_sha256": after["manifest_sha256"], "errata": [r["ERRATUM_ID"] for r in rows],
               "released_unchanged": frozen["released"], "added_blocked_families": {"DOME-A": ["UNLABELLED_JUNCTION_BAR"],
                                                                                    "DOME-B": ["UNLABELLED_JUNCTION_BAR"]},
               "small_bar_touches_shell_bar_leg": touch, "cuts": [{k: c[k] for k in ("cut", "labelled", "by_row")}
                                                                  for c in cuts],
               "mirror_census": {"structural_non_plus_z": st_nonz, "structural_mirrored_inserts": len(st_dome_mir),
                                 "architectural_non_plus_z": a_nonz, "architectural_mirrored_inserts": len(a_mir),
                                 "architectural_mirrored_near_domes": len(a_near)},
               "post_freeze_comparison_affected": False, "references_read": []}
    if not (all(touch) and st_nonz == 0 and not st_dome_mir and not a_near):
        raise SystemExit(f"STOP: errata evidence not as stated: {summary}")
    (HERE / OUT[1]).write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    L = ["# S8.3 errata (dated correction layer)", "",
         f"S8.3 stays frozen (`{MANIFEST.name}` {after['manifest_sha256'][:12]}…, verified before and after). These "
         "errata change no released quantity: concrete stays "
         f"{frozen['released']['concrete_m3']} m3 and reinforcement {frozen['released']['reinforcement_kg']} kg.", ""]
    L += [f"- **{r['ERRATUM_ID']}** ({r['KIND']}, {r['OUTPUT']}): {r['IS']}. Quantity effect: {r['QUANTITY_EFFECT']}."
          for r in rows]
    L += ["", "Found by re-auditing the frozen package against the brief's 'anchorage and junction bars' item. No "
          "earlier Urban, freelancer or donor figure informed it, and no post-freeze comparison row depends on it."]
    (HERE / OUT[2]).write_text("\n".join(L) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=1, sort_keys=True))
