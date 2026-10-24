"""T-267 synthetic stairs (not Alsenan). Every expected value in the tests is a hand calculation written beside it,
never read back from the module."""

MARBLE = {"material": "MARBLE", "source": "synthetic specification sheet"}


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def straight(n, riser, s=30.0, f0=100.0, f1=100.0, going=300.0, width=1200.0, waist=150.0, sides=("LEFT",),
             finish=MARBLE, run_type="FIXED", bottom=0.0, polygons=False):
    """one straight flight floor to floor: n risers, n - 1 drawn treads, the last riser onto the upper floor."""
    surfaces = []
    for i in range(1, n):
        t = {"id": f"T{i}", "kind": "TREAD", "flight": "A", "finish_mm": s, "going_mm": going, "width_mm": width}
        if polygons:
            t["polygon"] = rect((i - 1) * going, 0.0, i * going, width)
        surfaces.append(t)
    return {"stair_id": "S", "ffl_bottom_mm": bottom, "ffl_top_mm": bottom + n * riser,
            "floor_bottom_finish_mm": f0, "floor_top_finish_mm": f1, "surfaces": surfaces,
            "flights": {"A": {"waist_mm": waist, "width_mm": width, "rail_sides": list(sides) if sides else None,
                              "run_mm": (n - 1) * going, "run_type": run_type}},
            "stair_finish": finish, "arrival_nosing_mm": 20.0, "nosing": {"specified": False},
            "bar_detail": None, "building_type": "PRIVATE_HOUSE"}


def dog_leg(n_a, n_b, riser, s_a=30.0, s_land=50.0, s_b=20.0, f0=100.0, f1=100.0, going=300.0, width=1200.0,
            landing_poly=None, top_tread_drawn=False):
    """two flights and a half landing. top_tread_drawn=False: flight A's last riser arrives on the landing (n_a
    risers, n_a - 1 treads); True: flight A's top tread is drawn before the landing at the same level (n_a risers,
    n_a treads). Flight B: n_b risers, n_b - 1 treads, the last onto the upper floor."""
    surf = []
    ta = n_a if top_tread_drawn else n_a - 1
    for i in range(1, ta + 1):
        surf.append({"id": f"A{i}", "kind": "TREAD", "flight": "A", "finish_mm": s_a, "going_mm": going,
                     "width_mm": width})
    surf.append({"id": "L", "kind": "LANDING", "finish_mm": s_land, "rises": not top_tread_drawn,
                 "polygon": landing_poly or rect(0.0, 0.0, 2500.0, 1200.0), "thickness_mm": 160.0, "depth_mm": 1200.0})
    for i in range(1, n_b):
        surf.append({"id": f"B{i}", "kind": "TREAD", "flight": "B", "finish_mm": s_b, "going_mm": going,
                     "width_mm": width})
    n = n_a + n_b
    return {"stair_id": "D", "ffl_bottom_mm": 0.0, "ffl_top_mm": n * riser, "floor_bottom_finish_mm": f0,
            "floor_top_finish_mm": f1, "surfaces": surf,
            "flights": {"A": {"waist_mm": 150.0, "width_mm": width, "rail_sides": ["LEFT", "RIGHT"]},
                        "B": {"waist_mm": 150.0, "width_mm": width, "rail_sides": ["LEFT", "RIGHT"]}},
            "stair_finish": MARBLE, "arrival_nosing_mm": 20.0, "nosing": {"specified": False}, "bar_detail": None,
            "building_type": "PRIVATE_HOUSE"}
