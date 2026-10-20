"""T-126 route G scope (ROUTE_G_SCOPE_V1): column pieces released only where the storey's roof-slab plan draws them,
blinding per member family. Synthetic villa SV-SCOPE (built below, not a client project): plan frames with their own
origins, mm units, storey heights GF 4.00 / 1F 3.50 / 2F 3.50, blinding 0.075 thick with a 0.15 projection. The same
villa is also checked mirrored, rotated 90 degrees and in metre units; every expected value is a hand calculation
written beside it.

Columns (local mm on the column plan; the foundation plan and the slab plans share the local frame):
  K1 CA  bound outline (2000, 2000); GF and 1F plans draw it; no 2F plan in the set
         GF 0.25 x 0.30 x 4.00 = 0.300 RELEASED, 1F 0.20 x 0.30 x 3.50 = 0.210 RELEASED, 2F 0.210 HELD (no 2F plan)
  K2 CA  mark (9200, 2000) bound to no outline; the foundation plan draws CA at (8000, 2000), 1.20 m away (K1's CA
         outline is claimed by K1); the GF plan draws it there, the 1F plan does not (nearest 6.00 m)
         GF 0.300 RELEASED, 1F 0.210 NOT_PRESENT (its steel item goes too), 2F 0.210 HELD (no 2F plan)
  K3 CB  mark (14000, 6000) unbound; foundation CB outlines at 1.00 and 1.10 m: ambiguous, no anchor; GF plan: one
         outline at a printed CB section (0.25 x 0.60) -> GF 0.25 x 0.60 x 4.00 = 0.600 RELEASED; 1F plan: two
         outlines at the printed 0.20 x 0.50 -> 1F 0.20 x 0.50 x 3.50 = 0.350 HELD
  K4 CD  mark (20000, 6000) unbound, no CD outline on the foundation plan, the GF outline nearby is 0.30 x 0.30 (CD
         prints 0.25 x 0.50) -> GF 0.25 x 0.50 x 4.00 = 0.500 HELD
  K5 CA  bound (2000, 9000): GF 0.300 RELEASED; 1F already not counted by the route (risk record) -> NOT_PRESENT, listed
  K6 CE  bound, the route itself holds it (no height) -> HELD, item unchanged
  planted column on the 1F plan (no column-plan occurrence): untouched
  GF released 0.30 + 0.30 + 0.60 + 0.30 = 1.500, held 0.500; 1F released 0.210, not present 0.210, held 0.350;
  2F held 0.420.

Blinding (t 0.075, p 0.15):
  FA 2.0 x 2.0 at x 1000..3000, y 1000..3000: (2.3)(2.3) = 5.29 m2       FA2 1.0 x 1.0 at x 3200..4200, y 1000..2000:
  (1.3)(1.3) = 1.69; projections overlap x 3050..3150 x y 850..2150 = 0.10 x 1.30 = 0.13
  FB 2.4 x 2.0 at x 6800..9200: (2.7)(2.3) = 6.21                         FC 1.0 x 1.0 at x 11000..12000: 1.69
  released footing layer 5.29 + 1.69 + 6.21 + 1.69 - 0.13 = 14.75 m2 -> 1.10625 m3
  FX/FY one outline, two labels (conflict, owner Q-31 C), route takes the larger 1.5 x 1.0: (1.8)(1.3) = 2.34 m2
  -> HELD 0.1755 (larger alone) .. (2.34 + 1.2 x 1.2 = 3.78) x 0.075 = 0.2835 (each its own pad)
  beam 1 along y 2000 (x 3000..6800, 0.30 wide): strip 3.8 x 0.6 = 2.28 m2; on footing blinding: FA 0.15 x 0.6 = 0.09,
  FA2 1.30 x 0.45 = 0.585, FB 0.15 x 0.6 = 0.09, FA n FA2 0.10 x 0.45 = 0.045 counted once -> 0.72
  beam 2 along x 5000 (y 0..4000): strip 0.6 x 4.0 = 2.40, crossing beam 1 0.6 x 0.6 = 0.36
  ground-beam blinding HELD (Q-21 C): own layer (2.28 + 2.40 - 0.36) = 4.32 m2 -> 0.324; merged 4.32 - 0.72
  = 3.60 -> 0.270
  strap FB..FC (x 9200..11000, 0.40 wide): strip 1.8 x 0.7 = 1.26, on FB 0.105 and FC 0.105 -> 1.05 m2 -> HELD
  0.07875 (merged; a strap at footing level has no own layer)
  total range 1.10625 + 0.1755 + 0.270 + 0.07875 = 1.6305 .. 1.10625 + 0.2835 + 0.324 + 0.07875 = 1.7925
"""

from __future__ import annotations

import copy

import pytest

from engine.source import provisional_estimate as PE
from engine.source import route_g_scope_v1 as SC

A = pytest.approx
H = {"GF": 4.0, "1F": 3.5, "2F": 3.5}
ORIG = {"SA": (100000.0, 0.0), "FND": (200000.0, 0.0), "SGF": (300000.0, 0.0), "S1F": (400000.0, 0.0),
        "GB": (500000.0, 0.0)}
ROLE = {"SA": ("COLUMN_PLAN", "ALL"), "FND": ("FOUNDATION_PLAN", "FOUNDATION"), "SGF": ("SLAB_PLAN", "GF"),
        "S1F": ("SLAB_PLAN", "1F"), "GB": ("GROUND_BEAM_PLAN", "GROUND")}
BANDS = {"CA": {"GF": (0.25, 0.30), "1F": (0.20, 0.30), "2F": (0.20, 0.30)},
         "CB": {"GF": (0.25, 0.60), "1F": (0.20, 0.50)}, "CD": {"GF": (0.25, 0.50)}, "CE": {"GF": (0.25, 0.25)}}


def conv(thickness=True):
    def num(i, v):
        return {"id": i, "title": i, "kind": "number", "low": v, "base": v, "high": v, "provenance": "PRINTED_VALUE",
                "source": "SV-SCOPE typical detail", "rationale": "printed"}
    cs = [num("BLINDING_PROJECTION_M", 0.15),
          {"id": "BLINDING_UNDER", "title": "under", "kind": "choice", "base": "FOOTINGS_AND_GROUND_BEAMS",
           "options": ["FOOTINGS_ONLY", "FOOTINGS_AND_GROUND_BEAMS"], "provenance": "PRINTED_VALUE",
           "source": "SV-SCOPE typical detail", "rationale": "printed"}]
    if thickness:
        cs.append(num("BLINDING_THICKNESS_M", 0.075))
    cs += [num(f"STOREY_HEIGHT_{k}", v) for k, v in H.items()]
    return PE.Conventions({"set": "SV-SCOPE", "conventions": cs})


class Frame:
    """world transform of the synthetic villa: scale (mm or m), mirror in x, rotation by 90 degrees"""

    def __init__(self, scale=1.0, mirror=False, rot90=False):
        self.s, self.m, self.r = scale, mirror, rot90

    def p(self, x, y):
        x, y = x * self.s, y * self.s
        if self.m:
            x = -x
        if self.r:
            x, y = -y, x
        return (x, y)

    def vec(self, ux, uy):
        if self.m:
            ux = -ux
        if self.r:
            ux, uy = -uy, ux
        return (ux, uy)

    def box(self, sid, x0, y0, x1, y1):
        o = ORIG[sid]
        a, b = self.p(x0 + o[0], y0 + o[1]), self.p(x1 + o[0], y1 + o[1])
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))

    def cbox(self, sid, cx, cy, w, h):
        return self.box(sid, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

    def at(self, sid, x, y):
        o = ORIG[sid]
        return self.p(x + o[0], y + o[1])

    def band(self, sid, a, b, width):
        """a straight band from local a to local b, `width` mm wide, in route G's frame (u, t0, t1, lo, hi)"""
        pa, pb = self.at(sid, *a), self.at(sid, *b)
        L = ((pb[0] - pa[0]) ** 2 + (pb[1] - pa[1]) ** 2) ** 0.5
        u = ((pb[0] - pa[0]) / L, (pb[1] - pa[1]) / L)
        n = (-u[1], u[0])
        t0, t1 = pa[0] * u[0] + pa[1] * u[1], pb[0] * u[0] + pb[1] * u[1]
        o = pa[0] * n[0] + pa[1] * n[1]
        w = width * self.s / 2
        return {"kind": "STRAIGHT", "u": u, "t0": min(t0, t1), "t1": max(t0, t1), "lo_off": o - w, "hi_off": o + w}


def piece_item(cid, mark, st, category="PROVISIONAL", steel=False):
    B, Hh = BANDS[mark][st]
    v = B * Hh * H[st]
    common = dict(component_id=cid, trade="CONCRETE", family="COLUMNS", storey=st, source="SV-SCOPE column plan",
                  dimensions={"section_m": (B, Hh), "height_m": H[st]})
    if category == "UNRESOLVED":
        out = [PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="STOREY_HEIGHT_NOT_PRINTED", **common)]
    else:
        out = [PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v, formula="B x H x h",
                       assumptions=[f"STOREY_HEIGHT_{st}"], support="CONVENTION_ONLY", confidence="MEDIUM",
                       blocker="NOT_REVIEWED", **common)]
    if steel:
        out.append(PE.item(item_id=f"P-S:{cid}:MAIN:D12", component_id=cid, trade="REINFORCEMENT", family="COLUMNS",
                           storey=st, category="PROVISIONAL", low=10.0, base=10.0, high=10.0, dia_mm=12,
                           source="SV-SCOPE schedule", formula="count x length x d2/162",
                           assumptions=[f"STOREY_HEIGHT_{st}"], support="CONVENTION_ONLY", confidence="MEDIUM",
                           blocker="LAP_ANCHORAGE_RULE"))
    return out


def villa(fr=None, thickness=True):
    fr = fr or Frame()
    u = 0.001 / fr.s
    sheets = {sid: {"sheet": {"sheet_id": sid, "role": ROLE[sid][0], "storey": ROLE[sid][1],
                              "origin": fr.p(*ORIG[sid])}} for sid in ORIG}

    def occ(mark, x, y, mx=None, my=None, bound=True, w=300, h=300):
        mx, my = (x - 700, y) if mx is None else (mx, my)
        cid = "COL:SA:{}@{},{}".format(mark, *[round(c) for c in fr.at("SA", mx, my)])
        return {"member_id": cid, "mark": mark, "sheet": "SA", "mark_at": fr.at("SA", mx, my),
                "box": fr.cbox("SA", x, y, w, h) if bound else None, "drawn_m": [0.3, 0.3] if bound else None,
                "outline_binding": "NEAREST" if bound else "NO_OUTLINE",
                "row": {"mark": mark, "by_storey": {s: {"dims_m": {"W": b[0], "H": b[1]}} for s, b in
                                                    BANDS[mark].items()}}}
    K1 = occ("CA", 2000, 2000)
    K2 = occ("CA", 8000, 2000, 9200, 2000, bound=False)
    K3 = occ("CB", 13000, 6000, 14000, 6000, bound=False)
    K4 = occ("CD", 20500, 6000, 20000, 6000, bound=False)
    K5 = occ("CA", 2000, 9000)
    K6 = occ("CE", 26000, 9000)
    sheets["SA"]["columns"] = [K1, K2, K3, K4, K5, K6]

    def fcol(mark, x, y, w=300, h=300):
        return {"member_id": "COL:FND:{}@{},{}".format(mark, *[round(c) for c in fr.at("FND", x, y)]), "mark": mark,
                "box": fr.cbox("FND", x, y, w, h)}
    sheets["FND"]["columns"] = [fcol("CA", 2000, 2000), fcol("CA", 8000, 2000), fcol("CB", 13000, 6000),
                                fcol("CB", 15100, 6000), fcol("CA", 2000, 9000)]

    def ftg(mark, x0, y0, x1, y1):
        b = fr.box("FND", x0, y0, x1, y1)
        L, W = (x1 - x0) / 1000, (y1 - y0) / 1000
        return {"member_id": "FTG:FND:{}@{},{}".format(mark, round(b[0]), round(b[1])), "mark": mark,
                "state": "CONFIRMED", "box": b, "drawn_m": sorted([L, W]), "schedule_m": [max(L, W), min(L, W), 0.4]}
    fts = [ftg("FA", 1000, 1000, 3000, 3000), ftg("FA2", 3200, 1000, 4200, 2000), ftg("FB", 6800, 1000, 9200, 3000),
           ftg("FC", 11000, 1000, 12000, 2000)]
    for f in fts:
        f["drawn_m"] = list(f["schedule_m"][:2])           # the route takes the drawn size equal to the schedule
    conflict = {"member_id": "FTG:FND:FX-FY", "mark": "FX", "state": "LABEL_TYPE_CONFLICT", "box": None,
                "drawn_m": None, "schedule_m": [1.5, 1.0, 0.5],
                "candidates": {"FX": {"schedule_m": [1.5, 1.0, 0.5]}, "FY": {"schedule_m": [0.9, 0.9, 0.3]}}}
    secondary = {"member_id": "FTG:FND:FY", "mark": "FY", "state": "LABEL_TYPE_CONFLICT_SECONDARY", "box": None,
                 "drawn_m": None, "schedule_m": [0.9, 0.9, 0.3]}
    sheets["FND"]["footings"] = fts + [conflict, secondary]
    strap_poly = [fr.at("FND", 9200, 1300), fr.at("FND", 11000, 1300), fr.at("FND", 11000, 1700),
                  fr.at("FND", 9200, 1700)]
    sheets["FND"]["straps"] = {"bands": [{"band_id": "S1", "net_plan_m2": 1.8 * 0.4, "length_m": 1.8,
                                          "polygon": strap_poly, "kind": "STRAIGHT"}]}
    # ground-beam plan: its column outlines at the footing centres (registration), two beams that cross
    sheets["GB"]["column_boxes"] = [fr.cbox("GB", 2000, 2000, 300, 300), fr.cbox("GB", 8000, 2000, 300, 300),
                                    fr.cbox("GB", 3700, 1500, 300, 300)]
    b1, b2 = fr.band("GB", (3000, 2000), (6800, 2000), 300), fr.band("GB", (5000, 0), (5000, 4000), 300)
    sheets["GB"]["bands"] = [dict(b1, band_id="B1"), dict(b2, band_id="B2")]
    sheets["GB"]["beams"] = [{"band_id": "B1", "net_plan_m2": 3.8 * 0.3, "length_m": 3.8, "kind": "STRAIGHT"},
                             {"band_id": "B2", "net_plan_m2": 4.0 * 0.3, "length_m": 4.0, "kind": "STRAIGHT"}]
    # roof-slab plans (column outlines drawn at the storey's section)
    sheets["SGF"]["column_boxes"] = [fr.cbox("SGF", 2000, 2000, 250, 300), fr.cbox("SGF", 8000, 2000, 250, 300),
                                     fr.cbox("SGF", 13000, 6000, 250, 500), fr.cbox("SGF", 15100, 6000, 250, 600),
                                     fr.cbox("SGF", 20500, 6000, 300, 300), fr.cbox("SGF", 2000, 9000, 250, 300),
                                     fr.cbox("SGF", 26000, 9000, 250, 250)]
    sheets["SGF"]["column_presence"] = list(sheets["SGF"]["column_boxes"][:2])     # duplicates: one outline once
    sheets["S1F"]["column_boxes"] = [fr.cbox("S1F", 2000, 2000, 200, 300), fr.cbox("S1F", 13000, 6000, 200, 500),
                                     fr.cbox("S1F", 15100, 6000, 200, 500)]
    D = {"unit_m": u, "sheets": sheets}
    items = []
    for K, sts in ((K1, ("GF", "1F", "2F")), (K2, ("GF", "1F", "2F")), (K3, ("GF", "1F")), (K4, ("GF",)),
                   (K5, ("GF",))):
        for st in sts:
            items += piece_item(f"{K['member_id']}|{st}", K["mark"], st, steel=(K is K2 and st == "1F"))
    items += piece_item(f"{K6['member_id']}|GF", "CE", "GF", category="UNRESOLVED")
    items.append(PE.item(item_id="P-C:COL:S1F:PC@1,1|1F", component_id="COL:S1F:PC@1,1|1F", trade="CONCRETE",
                         family="COLUMNS", storey="1F", category="PROVISIONAL", low=0.2, base=0.2, high=0.2,
                         formula="label", assumptions=["STOREY_HEIGHT_1F"], support="CONVENTION_ONLY",
                         confidence="LOW", blocker="PLANTED_COLUMN_STOREY", source="SV-SCOPE 1F plan label"))
    for f in fts:
        items.append(PE.item(item_id=f"P-C:{f['member_id']}", component_id=f["member_id"], trade="CONCRETE",
                             family="FOOTINGS", storey="FOUNDATION", category="PROVISIONAL", low=1.0, base=1.0,
                             high=1.0, formula="L x W x D", assumptions=["BLINDING_PROJECTION_M"],
                             support="CONVENTION_ONLY", confidence="MEDIUM", blocker="NOT_REVIEWED",
                             source="SV-SCOPE"))
    items.append(PE.item(item_id="P-C:FTG:FND:FX-FY", component_id="FTG:FND:FX-FY", trade="CONCRETE",
                         family="FOOTINGS", storey="FOUNDATION", category="PROVISIONAL", low=0.75, base=0.75,
                         high=0.75, formula="L x W x D", assumptions=["BLINDING_PROJECTION_M"],
                         support="CONVENTION_ONLY", confidence="LOW", blocker="SOURCE_CONFLICT", source="SV-SCOPE"))
    for name, v in (("FOOTINGS", 1.2810), ("GROUND_BEAMS", 0.3471)):
        cid = f"PLAIN_CONCRETE:FOUNDATION:BLINDING_{name}"
        items.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family="PLAIN_CONCRETE",
                             storey="FOUNDATION", category="PROVISIONAL", low=v, base=v, high=v, formula="route",
                             assumptions=(["BLINDING_THICKNESS_M"] if thickness else []) + ["BLINDING_PROJECTION_M"],
                             support="CONVENTION_ONLY", confidence="MEDIUM", blocker="BLINDING_PROJECTION",
                             source="SV-SCOPE"))
    risk = [{"KIND": "COLUMN_ABSENT_ON_STOREY_PLAN", "WHERE": "1F CA",
             "DETAIL": f"{K5['member_id']}|1F: schedule band 1F exists but the 1F roof-slab plan shows no column "
                       f"here; not counted"}]
    R = {"items": items, "conv": conv(thickness), "generic": {"D": D, "risk": risk}}
    return R, {"K1": K1, "K2": K2, "K3": K3, "K4": K4, "K5": K5, "K6": K6}


def by_piece(sc):
    return {(c["occurrence"], c["storey"]): c for c in sc["columns"]}


FRAMES = {"mm": Frame(), "mirror": Frame(mirror=True), "rot90": Frame(rot90=True), "metres": Frame(scale=0.001),
          "mirror_rot_m": Frame(scale=0.001, mirror=True, rot90=True)}


@pytest.fixture(params=sorted(FRAMES))
def case(request):
    R, K = villa(FRAMES[request.param])
    return R, K, SC.measure(R)


def test_column_statuses_by_hand(case):
    R, K, sc = case
    P = by_piece(sc)
    exp = {("K1", "GF"): ("RELEASED", 0.300, "COLUMN_PLAN_OUTLINE"), ("K1", "1F"): ("RELEASED", 0.210, None),
           ("K1", "2F"): ("HELD", 0.210, "NO_STOREY_PLAN"),
           ("K2", "GF"): ("RELEASED", 0.300, "FOUNDATION_PLAN_ANCHOR"),
           ("K2", "1F"): ("NOT_PRESENT", 0.210, "FOUNDATION_PLAN_ANCHOR"), ("K2", "2F"): ("HELD", 0.210, None),
           ("K3", "GF"): ("RELEASED", 0.600, "SECTION_MATCH_ON_STOREY_PLAN"),
           ("K3", "1F"): ("HELD", 0.350, "PRESENCE_UNVERIFIED"), ("K4", "GF"): ("HELD", 0.500, "PRESENCE_UNVERIFIED"),
           ("K5", "GF"): ("RELEASED", 0.300, None), ("K5", "1F"): ("NOT_PRESENT", None, "ROUTE_ABSENT"),
           ("K6", "GF"): ("HELD", None, "ROUTE_HELD")}
    for (k, st), (status, m3, basis) in exp.items():
        c = P[(K[k]["member_id"], st)]
        assert c["status"] == status, (k, st, c)
        if m3 is not None:
            assert c["route_m3"] == A(m3, abs=1e-6), (k, st)
        if basis:
            assert c["basis"] == basis, (k, st, c)
    assert P[(K["K2"]["member_id"], "1F")]["nearest_outline_m"] == A(6.0, abs=0.01)
    assert len(sc["columns"]) == len(exp)               # the planted column is not a column-plan piece


def test_column_totals_by_storey(case):
    _, _, sc = case
    S = sc["columns_by_storey"]
    assert S["GF"]["RELEASED"] == A(1.5) and S["GF"]["HELD"] == A(0.5)
    assert S["1F"]["RELEASED"] == A(0.21) and S["1F"]["NOT_PRESENT"] == A(0.21) and S["1F"]["HELD"] == A(0.35)
    assert S["2F"]["HELD"] == A(0.42) and S["2F"]["RELEASED"] == A(0.0)
    assert len(S["1F"]["not_present"]) == 1             # named, with its m3 (the route-absent piece has none)


def test_blinding_families_by_hand(case):
    _, _, sc = case
    bl = sc["blinding"]
    assert bl["state"] == "MEASURED" and bl["registration"] == "REGISTERED"
    assert bl["released_footing_m3"] == A(14.75 * 0.075, abs=1e-6)
    assert bl["footing_overlap_m2"] == A(0.13, abs=1e-6)
    rec = {r["family"] if r["family"] != "FOOTING" else r["mark"]: r for r in bl["records"]}
    assert rec["FX"]["status"] == "HELD" and rec["FX"]["exposure_m3"] == [A(0.1755), A(0.2835)]
    assert rec["FX"]["route_m3"] == A(0.1755)
    assert "FY" not in rec                                # the secondary label is the same outline
    assert all(rec[m]["status"] == "RELEASED" for m in ("FA", "FA2", "FB", "FC"))
    gb = rec["GROUND_BEAM"]
    assert gb["status"] == "HELD" and gb["m3"] is None and gb["blocker"] == "FOOTING_DETAIL_CHOICE_OPEN"
    assert gb["exposure_m3"] == [A(0.27, abs=1e-6), A(0.324, abs=1e-6)]
    st = rec["STRAP"]
    assert st["status"] == "HELD" and st["exposure_m3"] == [A(0.07875, abs=1e-6), A(0.07875, abs=1e-6)]
    assert bl["released_m3"] == A(1.10625, abs=1e-6)
    assert bl["total_range_m3"] == [A(1.6305, abs=1e-6), A(1.7925, abs=1e-6)]


def test_detail_choice_releases_one_reading():
    R, _ = villa()
    own = SC.measure(R, beam_detail="OWN_LAYER")["blinding"]
    mer = SC.measure(R, beam_detail="MERGED_WITH_FOOTING", strap_blinding_printed=True)["blinding"]
    g = {r["family"]: r for r in own["records"]}
    assert g["GROUND_BEAM"]["status"] == "RELEASED" and g["GROUND_BEAM"]["m3"] == A(0.324, abs=1e-6)
    g = {r["family"]: r for r in mer["records"]}
    assert g["GROUND_BEAM"]["m3"] == A(0.27, abs=1e-6) and g["STRAP"]["m3"] == A(0.07875, abs=1e-6)
    assert mer["released_m3"] == A(1.10625 + 0.27 + 0.07875, abs=1e-6)
    with pytest.raises(SC.ScopeError):
        SC.measure(R, beam_detail="GUESS")


def test_apply_replaces_items_never_zero(case):
    R, K, sc = case
    out = SC.apply(R, sc)
    ids = {i["item_id"] for i in out}
    k2 = K["K2"]["member_id"]
    assert f"P-C:{k2}|1F" not in ids and f"P-S:{k2}|1F:MAIN:D12" not in ids        # not present: every item goes
    for k, st in (("K3", "1F"), ("K4", "GF"), ("K1", "2F")):
        cid = f"{K[k]['member_id']}|{st}"
        held = [i for i in out if i["component_id"] == cid]
        assert len(held) == 1 and held[0]["category"] == "UNRESOLVED" and held[0]["base"] is None
        assert held[0]["exposure_high"] > 0 and held[0]["blocker"] == "COLUMN_PRESENCE_UNVERIFIED"
    assert f"U-C:{K['K6']['member_id']}|GF" in ids and "P-C:COL:S1F:PC@1,1|1F" in ids
    bl = [i for i in out if i["family"] == "PLAIN_CONCRETE"]
    assert "P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS" not in ids
    rel = [i for i in bl if i["category"] == "PROVISIONAL"]
    assert len(rel) == 1 and rel[0]["base"] == A(1.10625, abs=1e-6)
    held = [i for i in bl if i["category"] == "UNRESOLVED"]
    assert len(held) == 3 and all(i["exposure_low"] > 0 and i["exposure_high"] >= i["exposure_low"] for i in held)
    conc = sum(i["base"] for i in out if i["trade"] == "CONCRETE" and i["family"] == "COLUMNS" and i["base"])
    assert conc == A(1.5 + 0.21 + 0.2, abs=1e-6)        # released pieces + the planted column
    PE.check(out, R["conv"])


def test_missing_thickness_is_not_a_number():
    R, _ = villa(thickness=False)
    sc = SC.measure(R)
    assert sc["blinding"]["state"] == "NOT_PRINTED" and sc["blinding"]["records"] == []
    out = SC.apply(R, sc)                                  # the route items stay as they were
    assert "P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS" in {i["item_id"] for i in out}


def test_unregistered_plans_add_footings_whole():
    """no ground-beam column outline lands in a footing: the plans are not registered, every outline is added
    whole (no union): footings 5.29 + 1.69 + 6.21 + 1.69 = 14.88 m2 -> 1.116 m3 (the 0.13 m2 overlap counted twice)"""
    R, _ = villa()
    R["generic"]["D"]["sheets"]["GB"]["column_boxes"] = []
    bl = SC.measure(R)["blinding"]
    assert bl["registration"] != "REGISTERED"
    assert bl["released_footing_m3"] == A(14.88 * 0.075, abs=1e-6)


def test_anchor_claimed_by_a_bound_column_is_not_reused():
    """K2's own foundation outline removed: the only CA outline left within reach would be K1's (claimed, and 7.2 m
    away anyway) -> no anchor; the GF plan has an outline at a printed CA section (0.25 x 0.30) near the mark -> GF
    by section; the 1F plan has none near -> HELD, never NOT_PRESENT without a position"""
    R, K = villa()
    fnd = R["generic"]["D"]["sheets"]["FND"]
    fnd["columns"] = [c for c in fnd["columns"] if "8000" not in c["member_id"] and "208000" not in c["member_id"]]
    P = by_piece(SC.measure(R))
    assert P[(K["K2"]["member_id"], "GF")]["basis"] == "SECTION_MATCH_ON_STOREY_PLAN"
    assert P[(K["K2"]["member_id"], "1F")]["status"] == "HELD"


def test_needs_a_route_result():
    with pytest.raises(SC.ScopeError):
        SC.column_scope({"items": [], "generic": {}})
    with pytest.raises(SC.ScopeError):
        SC.blinding_scope({"items": [], "generic": {"D": {"sheets": {}, "unit_m": 0.001}}})


def test_no_project_constants_in_the_module():
    import inspect
    src = inspect.getsource(SC)
    for bad in ("SH0", "SH1", "ST7757", "Alsenan", "F10", "C8"):
        assert bad not in src
    rec = SC.policy_record()
    assert rec["policy"] == "ROUTE_G_SCOPE_V1" and "UP-QTY-STATUS-001" in rec["rules"]


def test_inputs_not_mutated():
    R, _ = villa()
    before = copy.deepcopy(R["items"])
    SC.apply(R, SC.measure(R))
    assert R["items"] == before


def test_without_a_column_plan_the_foundation_occurrences_are_checked():
    """a set with no column plan: route G takes the foundation plan's column occurrences; the scope checks those
    the same way (bound outline CA at (8000, 2000): GF plan draws it, 1F plan does not -> NOT_PRESENT 0.210)"""
    R, _ = villa()
    D = R["generic"]["D"]
    del D["sheets"]["SA"]
    fc = next(c for c in D["sheets"]["FND"]["columns"] if c["member_id"] == "COL:FND:CA@208000,2000")
    fc["mark_at"] = (fc["box"][0] - 700, (fc["box"][1] + fc["box"][3]) / 2)
    fc["row"] = {"mark": "CA", "by_storey": {s: {"dims_m": {"W": b[0], "H": b[1]}} for s, b in BANDS["CA"].items()}}
    R["items"] += piece_item("COL:FND:CA@208000,2000|GF", "CA", "GF") + piece_item("COL:FND:CA@208000,2000|1F", "CA",
                                                                                  "1F")
    P = by_piece(SC.measure(R))
    assert P[("COL:FND:CA@208000,2000", "GF")]["status"] == "RELEASED"
    assert P[("COL:FND:CA@208000,2000", "1F")]["status"] == "NOT_PRESENT"
