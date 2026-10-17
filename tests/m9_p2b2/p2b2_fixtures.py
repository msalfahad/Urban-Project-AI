"""Phase 2B-2 synthetic fixtures (synthetic geometry only; every truth written by hand from the coordinates).

    resolver(*rules)                      a URBAN_PROJECT_RULES_V1 resolver over the knowledge registry 1.1.0
    walls(ring, gaps=())                  the typed boundary features of a room ring (metres): a WALL along every edge
                                          except the gaps, which get their own role (DOOR / PASSAGE / OTHER ...)
    area(ring, ...)                       a waterproofed area through waterproofing_system.make_area / build_area
                                          (agg / agg_glazing: the plan's boundary-role upturn and glazing-edge runs)
    kitchen_plan()                        a small plan (mm): LIVING (dry) | KITCHEN | PANTRY | BATH, three doors,
                                          measured by arch_measure with the owner wet scope
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import door_standards as DSTD              # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import project_rules as PR                 # noqa: E402
from engine.source import robust_geometry as RG               # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402
from engine.source import wp_geometry as WG                   # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

U = 1e-3
ROLES = {"A-WALL": "WALL", "A-DOOR": "DOOR", "A-GLAZ": "WINDOW", "A-COL": "COLUMN"}


def rule(rid, rule_id, parameter, value, scope=None, kind="DETAIL", ref="synthetic detail"):
    return {"id": rid, "rule_id": rule_id, "parameter": parameter, "value": value,
            "scope": scope or {"kind": "PROJECT"}, "source": {"kind": kind, "ref": ref}}


def resolver(*rules):
    with K.using("1.1.0"):
        d = PR.load({"schema": PR.SCHEMA, "project_id": "SYNTHETIC P2B2", "rules": list(rules)})
        return PR.Resolver(d, bindings=PR.bind(d))


def walls(ring, gaps=()):
    """gaps: (edge index, t0, t1, role, id) - t along the edge from its first vertex (metres)."""
    out = []
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        at = lambda t: (a[0] + u[0] * t, a[1] + u[1] * t)            # noqa: E731
        cuts = sorted((t0, t1, role, fid) for e, t0, t1, role, fid in gaps if e == i)
        pos = 0.0
        for t0, t1, role, fid in cuts:
            if t0 > pos:
                out.append({"role": "WALL", "id": f"W{i}.{len(out)}", "a": at(pos), "b": at(t0)})
            if role != "OTHER":
                out.append({"role": role, "id": fid, "a": at(t0), "b": at(t1)})
            pos = t1
        if pos < L:
            out.append({"role": "WALL", "id": f"W{i}.{len(out)}", "a": at(pos), "b": at(L)})
    return out


def area(ring, *, gaps=(), holes=(), codes=("BATHROOM",), scope="WET", pieces=(), doorways=(), beyond=None,
         ents=None, res=None, room_id="GF-A1", floor="GF", extra_feats=(), agg=None, agg_glazing=0.0):
    room = {"room_id": room_id, "floor": floor, "name_en": room_id, "codes": list(codes), "polygon_m": list(ring),
            "hole_polygons_m": [list(h) for h in holes],
            "polygon": [(x / U, y / U) for x, y in ring], "hole_polygons": [[(x / U, y / U) for x, y in h]
                                                                          for h in holes]}
    feats = walls(ring, gaps) + list(extra_feats)
    for h in holes:
        feats += walls(h)
    net = abs(WG.signed_area(ring)) - sum(abs(WG.signed_area(h)) for h in holes)
    with K.using("1.1.0"):
        a = WS.make_area(room, feats, scope=scope, net_m2=net, continuation_pieces=pieces, doorways=doorways,
                         beyond=beyond, ents=ents, unit_m=U, agg_eligible_lm=agg, agg_glazing_lm=agg_glazing)
        return WS.build_area(a, res or resolver())


# ---- the kitchen plan (mm, wall 0.20 m)
K_OUTER = [(0, 0), (8400, 0), (8400, 6400), (0, 6400)]
K_ROOMS = {"LIVING": [(200, 200), (5000, 200), (5000, 6200), (200, 6200)],
           "KITCHEN": [(5200, 200), (8200, 200), (8200, 3800), (5200, 3800)],
           "PANTRY": [(5200, 4000), (6600, 4000), (6600, 6200), (5200, 6200)],
           "BATH": [(6800, 4000), (8200, 4000), (8200, 6200), (6800, 6200)]}
K_OPENINGS = [("DOOR", "x", 5000, 5200, 1000, 1900, None),          # LIVING | KITCHEN 0.90
              ("DOOR", "y", 3800, 4000, 5500, 6300, None),          # KITCHEN | PANTRY 0.80
              ("DOOR", "y", 3800, 4000, 7000, 7800, None)]          # KITCHEN | BATH 0.80
K_SWINGS = (((5200, 1000), 900, 0, 90), ((5500, 4000), 800, 0, 90), ((7000, 4000), 800, 0, 90))
K_WORDS = (("LIVING", (2600, 3200)), ("KITCHEN", (6700, 2000)), ("PANTRY", (5900, 5100)), ("BATH", (7500, 5100)))


def kitchen_plan(*, inserts=()):
    ents = AS._s4_ents(K_ROOMS, K_OUTER, K_OPENINGS, texts=K_WORDS, swings=K_SWINGS)
    ents["inserts"] = list(inserts)
    S = AR.spaces(ents, ROLES, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U), release_safety=True)
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[], owner_scope=True,
                   release_safety=True, door_height=lambda o_: DSTD.door_height(DSTD.INTERNAL, None))
    wp = {ln["location"]["room_id"] for ln in M["lines"] if ln["item_code"] == "FIN.WP.FLOOR"}
    with K.using("1.1.0"):
        areas = WS.areas_from_floor(S, M, ents, ROLES, U, wp_room_ids=wp)
    return S, M, ents, areas


def room_named(M, code):
    return next(r for r in M["rooms"] if code in (r.get("codes") or ()))


# ---- door feasibility plans (mm, wall 0.20 m): room A | room B with a door in their party wall x 4000 .. 4200
def door_plan(*, rooms, outer, openings, swings, words, columns=(), extra=(), inserts=(), facts=None, rules=()):
    ents = AS._s4_ents(rooms, outer, openings, texts=words, swings=swings, columns=columns, extra_segments=extra)
    ents["inserts"] = list(inserts)
    return run_doors(ents, ROLES, facts=facts, rules=rules)


def run_doors(ents, roles, *, facts=None, rules=(), shaft_box=None):
    """the V2.4 door pieces on one synthetic floor: spaces, walls, measure (owner scope), door model (guards), the
    feasibility report through the project rules."""
    from engine.source import arch_walls as AW
    from engine.source import door_feasibility as DF
    from engine.source import door_model as DM
    S = AR.spaces(ents, roles, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U), release_safety=True)
    if shaft_box is not None:
        sys.path.insert(0, str(ROOT / "tests" / "m9_p2b0"))
        import p2b0_fixtures as FX
        FX.mark_stacked_shaft(S, shaft_box)
    S["walls"] = AW.walls(ents, roles, U, S["faces"], S["openings"], columns=S["column_boxes"], geom=RG.Geometry(U))
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[], facts=facts,
                   owner_scope=True, release_safety=True, door_height=lambda o_: DSTD.door_height(DSTD.INTERNAL, facts))
    fm = DM.floor_model(S, M["rooms"], ents, U, "GF", wall_layers=[k for k, v in roles.items() if v == "WALL"],
                        facts=DSTD.door_model_facts(facts), guards=True)
    tx = {t["id"]: t for t in ents["texts"]}
    ft = {f["face_id"]: [tx[i] for i in f.get("label_text_ids") or () if i in tx] for f in S["faces"]}
    model = DM.building_model([("GF", fm)], {"GF": ents["texts"]}, {"GF": ft}, U, entrance_floor="GF", facts=facts,
                              guards=True, not_entrance_codes=("BALCONY", "ROOF"))
    with K.using("1.1.0"):
        res = resolver(*rules)
        ctx = {"GF": DF.floor_context(S, ents, roles, U, M["rooms"], "GF", walls=S["walls"])}
        rep = DF.feasibility(model, ctx, resolver=res, facts=facts)
    return {"S": S, "M": M, "model": model, "rep": rep, "ents": ents}


def two_rooms(*, a_word="BEDROOM", b_word="LIVING", s0=1500, s1=2400, columns=((600, 3400),), a_partition=None,
              b_right=8200, extra_openings=(), extra_swings=(), extra=(), inserts=(), rules=(), facts=None, swing=True):
    """room A (x 200 .. 4000) | room B (x 4200 .. b_right), y 200 .. 4200; a door y s0 .. s1 in the party wall that
    swings into B; a_partition: a 0.20 m wall across A at y a_partition .. +200 (A1 below, A2 above) meeting the
    party wall on the A side (a wall return / T-junction)."""
    top = 4200
    rooms = {"B": [(4200, 200), (b_right, 200), (b_right, top), (4200, top)]}
    words = [(b_word, ((4200 + b_right) / 2, 3000))]
    if a_partition is None:
        rooms["A"] = [(200, 200), (4000, 200), (4000, top), (200, top)]
        words.append((a_word, (2000, 3000)))
    else:
        y0 = a_partition
        rooms["A1"] = [(200, 200), (4000, 200), (4000, y0), (200, y0)]
        rooms["A2"] = [(200, y0 + 200), (4000, y0 + 200), (4000, top), (200, top)]
        words += [("STORE", (2000, (200 + y0) / 2)), (a_word, (2000, (y0 + 200 + top) / 2))]
    outer = [(0, 0), (b_right + 200, 0), (b_right + 200, top + 200), (0, top + 200)]
    openings = [("DOOR", "x", 4000, 4200, s0, s1, None)] + list(extra_openings)
    swings = ((((4200, s0), s1 - s0, 0, 90),) if swing else ()) + tuple(extra_swings)
    return door_plan(rooms=rooms, outer=outer, openings=openings, swings=swings, words=tuple(words),
                     columns=columns, extra=extra, inserts=inserts, facts=facts, rules=rules)


def glazing(x0, x1, y0, y1):
    """two glazing lines inside a window gap of a vertical wall x0 .. x1 between y0 and y1 (the window block)."""
    return tuple((((x0 + (x1 - x0) * f, y0), (x0 + (x1 - x0) * f, y1)), "A-GLAZ", None) for f in (1 / 3, 2 / 3))


def guard_floor(*, rules=(), facts=None):
    """the Phase 2B-0 door-guard floor (tests/m9_p2b0): the main entrance D1 (ENTRANCE HALL, 1.00 m), D3 0.90 m with a
    1.00 m frame (held), ordinary PVC doors; no column is drawn on it."""
    sys.path.insert(0, str(ROOT / "tests" / "m9_p2b0"))
    import p2b0_fixtures as FX
    ents, roles = FX.door_guards()
    return run_doors(ents, roles, facts=facts, rules=rules, shaft_box=(8200, 3200, 9800, 4800))


def party_door(run):
    """the feasibility row of the door in the party wall (x 4000 .. 4200)."""
    for r in run["rep"]["rows"]:
        o = next((x for x in run["S"]["openings"] if x["opening_id"] == r["opening_id"]), None)
        if o is not None and abs(o["centre"][0] - 4100) < 1:
            return r
    raise AssertionError("no party-wall door")
