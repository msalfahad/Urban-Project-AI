"""T-517 project inputs (training villa): the pool-court slab zones and what the documents print for each build-up
layer. Project data only; the rules live in t517_poolcourt_buildup.py.

Drawings by Drive folder ("Alsenan chalet project") and title, entities by handle only; no coordinate, no client name.
The membrane plan, upturn runs and edge runs are CITED from the merged T-494 component rows (sha256-pinned), never
re-derived here. The finish hatch area is read AT RUN TIME from the private decoded drawing
(P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55...); without it the finish area is HELD (never 0).

Evidence read for this table (T-517 run, 2026-11-05):
  * own scan of all 675 TEXT / MTEXT / ATTRIB entities (model space + every block) of the architectural DXF for screed,
    insulation, membrane, protection, tile / ceramic / porcelain / marble, mortar / cement / sand / bed, slope / falls,
    1:n, cm / mm and the Arabic terms: the hits are scale notes ('1:100') and room / sheet titles only; no build-up,
    thickness, mix, slope or finish-type note anywhere (agrees with T-321 s.1 and the T-514 scan of both DXFs);
  * entities within 0.5 m of the pool-court outline: the VOID label block BBF, the level block 124F and its text 1251
    '+5.50'; the designer's finish hatches 1250 and 1253 (layer 3, pattern LINE: the same layer and pattern as the
    TERRACE-550 finish hatches AE0 / D1A / 1252 that carry FIN.ROOF.FINISH in the candidate); hatch 1252 is wholly
    outside the zone (TERRACE-550's), so nothing is counted twice;
  * sanitary-7757.pdf sheet 2 (T-486 / T-494): no rain-water outlet, gully or slope arrow on this slab (-DRAIN-1 RFI);
  * section A-A roof bands: one constant drafting band, refused as a build-up (T-214 / T-221 / T-321).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

T494_ROWS = ROOT / "research/agents_t494/T494_COMPONENT_ROWS.json"
T494_SHA256 = "b87f8325b4bff8c4eb0214a112fb1cf53c7f6810e1a7f2e9c92c83c5f6bd892a"
FINISH_HATCHES = ("1250", "1253")     # layer 3, pattern LINE, inside the POOLCOURT-550 outline
HATCH_EDGE_LAYER2 = ("B31", "CB4", "C7B", "C7C")   # layer-2 entities the hatch's west boundary follows
HATCH_EDGE_CAUSE = ("HATCH_EDGE_ON_LAYER_2: the finish hatch 1250 / 1253 stops on the layer-2 lines B31 / CB4 / C7B / "
                    "C7C (elements drawn below / beyond), 0.25 m short of the 1F wall face B62 and short of the pier "
                    "faces, not on a built edge: the walking finish may run to the faces (face reading) or stop at "
                    "the hatch (designer's extent); not printed which")

Q41 = "Q-41 (owner 2026-10-19 20:45: 'if it is roof or balconies it is screed', its own line)"
SCAN = "T-517 scan of every text of the architectural DXF + T-321 s.1 / T-514 scans: no layer, thickness or mix printed"


def t494_rows(pin=True):
    import t517_poolcourt_buildup as B
    return B.load(T494_ROWS, T494_SHA256 if pin else None)


def zones(hatch_m2=None, pin=True):
    """the two pool-court zones. hatch_m2: the measured finish hatch area inside the open-sky zone (None = drawing
    absent -> finish area HELD)."""
    d = t494_rows(pin)
    rows = d["rows"]

    def one(zone, comp):
        hit = [r for r in rows if r["zone_id"] == zone and r["component"] == comp]
        if len(hit) != 1:
            raise ValueError(f"STALE_INPUT: {zone} {comp} found {len(hit)} times in T-494")
        return hit[0]
    flat = one("POOLCOURT-550", "FLAT_MEMBRANE")
    up = [r for r in rows if r["zone_id"] == "POOLCOURT-550" and r["component"] == "UPTURN" and r["status"] == "MEASURED"]
    up_lm = sum(r["length_lm"] for r in up)
    src = "T-494 component rows (MERGED; T-486 Checker 4.9069 AGREE), cited"
    open_sky = {
        "zone_id": "POOLCOURT-550", "function": flat["function"], "held": "",
        "face_m2": {"value": flat["qty"], "source": f"{src}: FLAT_MEMBRANE {flat['qty']} m2 (to the wall / pier / "
                                                     f"parapet faces, piers and void deducted)"},
        "hatch_m2": None if hatch_m2 is None else {
            "value": hatch_m2, "source": "finish hatches 1250 + 1253 (layer 3), outer paths; label / level islands and "
                                         "symbol frames not edges (T-321 method)", "edge_cause": HATCH_EDGE_CAUSE},
        "upturn_lm": {"value": up_lm, "source": f"{src}: the {len(up)} measured upturn runs (piers, parapet face and "
                                                f"end); the bath-window run 0.500002 lm stays HELD (sill unknown)"},
        "edges_lm": {"slab_edge": {"value": one("POOLCOURT-550", "SLAB_EDGE_TERMINATION")["held_bound"],
                                   "source": f"{src}: C7D + B30 open slab edge"},
                     "void_edge": {"value": one("POOLCOURT-550", "VOID_EDGE_TERMINATION")["held_bound"],
                                   "source": f"{src}: void edge BCF / 2F1C / C7A / 2F1B east part"}},
        "falls": {"slope": None, "outlet_drawn": False, "mean_rise_m": None,
                  "source": "sanitary-7757.pdf sheet 2: no outlet or slope on this slab (T-494 DRAINAGE_FALLS RFI)"},
    }
    ledge_row = one("POOLCOURT-550-LEDGE", "FLAT_MEMBRANE")
    ledge = {"zone_id": "POOLCOURT-550-LEDGE", "function": "ROOF",
             "held": "covered 4.20 m above by the 2F roof slab, open at the void side (R-WP-APPL-EXPOSED-1: HELD with "
                     "the bound shown; register ruling POOL-COURT SLAB)",
             "face_m2": None, "hatch_m2": None, "area_bound_m2": ledge_row["held_bound"],
             "edges_lm": {"void_edge": {"value": one("POOLCOURT-550-LEDGE", "VOID_EDGE_TERMINATION")["held_bound"],
                                        "source": f"{src}: BCF west part"}},
             "falls": None}
    return open_sky, ledge


PRINTS = {
    "FALLS_SCREED": {"scope": "OWNER_RULE", "source": Q41 + "; ELEMENT_REGISTER 'Roof / terrace SCREED TO FALLS' "
                                                            "(one falls volume)",
                     "thickness": None, "mix": None},
    "INSULATION": {"scope": "UNKNOWN", "source": SCAN + "; no owner rule (register: roof insulation UNKNOWN, D-39)",
                   "thickness": None},
    "PROTECTION": {"scope": "UNKNOWN", "source": SCAN + "; Q-41 gives ONE screed line ('falls / protection'), a "
                                                        "separate protection layer is neither printed nor ruled",
                   "thickness": None},
    "FINISH": {"scope": "PRINTED", "source": "designer finish hatch 1250 / 1253 (layer 3, as the terrace finishes)",
               "thickness": None, "material": None},
}


def measure_hatch(dxf=None):
    """{'hatch_m2', 'open_sky_net_m2', 'gap_m2', 'outside_net_m2', 'on_ledge_m2'} from the private drawing, or None."""
    sys.path.insert(0, str(ROOT / "research" / "agents_t486"))
    sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
    import t486_alsenan as A
    path = dxf or A.default_dxf()
    if path is None:
        return None
    import t321_measure as M
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    dw = A.Drawing(path)
    R = A.rings(dw)
    ox, oy = dw.o

    def loc(p):
        return Polygon([((x - ox) / 1000.0, (y - oy) / 1000.0) for x, y in p.exterior.coords]).buffer(0)
    outer = []
    for h in FINISH_HATCHES:
        layer, pat, paths, _islands, _symbols = M._hatch_outer(dw.d, h)
        if layer != "3" or pat != "LINE":
            raise ValueError(f"STALE_INPUT: hatch {h} is {layer} / {pat}")
        outer += [loc(p) for p in paths]
    hatch = unary_union(outer)
    outl = Polygon(R["outline"]).buffer(0)
    piers = unary_union([Polygon(v).buffer(0) for v in R["piers"].values()])
    void = Polygon(R["void"]).buffer(0)
    wx, big = R["wall_x"], 1000.0
    east = Polygon([(wx, -big), (big, -big), (big, big), (wx, big)])
    west = Polygon([(-big, -big), (wx, -big), (wx, big), (-big, big)])
    net = outl.difference(piers).difference(void)
    os_ = net.intersection(east)
    fin = hatch.intersection(os_)
    return {"hatch_m2": round(fin.area, 6), "hatch_outer_m2": round(hatch.area, 6),
            "open_sky_net_m2": round(os_.area, 6), "gap_m2": round(os_.difference(hatch).area, 6),
            "outside_net_m2": round(hatch.difference(os_).area, 6),
            "on_ledge_m2": round(hatch.intersection(net.intersection(west)).area, 6)}
