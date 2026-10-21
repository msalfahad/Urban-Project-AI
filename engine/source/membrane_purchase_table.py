"""MEMBRANE PURCHASE TABLE (task T-072, opt-in; no released method or quantity changed) - the owner's membrane table
(owner requirement 2026-10-19, his 3 m x 3 m bathroom picture; owner answers Q-24 + addendum, Q-25, Q-30): one row
per waterproofed area with its floor and room name, and at the end the rolls to buy for the project.

Every number is READ from the engine's own waterproofing outputs; nothing is measured or laid out again here:
    waterproofing_system.area_schedule rows   net area A, upturn run and area, doorway continuation, laps, installed
                                              membrane B, consumed membrane, cutting waste, rolls if the area is alone
    the area's layout (membrane_layout)       strip direction, number of floor strips, strip length, last strip width,
                                              band pieces of the separate upstand
    waterproofing_system.cutting_plan          C: the rolls to buy per membrane system, offcuts reused across areas
    wp_install.junction / continuous_fold     the floor-to-wall junction alternatives; CONTINUOUS_FOLD is the owner's
                                              stated method (Q-30: "wall upturn 20 cm, folded from the same membrane,
                                              not a separate strip"); the engine keeps the junction UNRESOLVED (N-11)
                                              and this table selects nothing: both methods are shown side by side

    area_row(row, layout=None, install=None)  -> one table row (state MEASURED)
    held_row(...)                             -> a HELD row: reason shown, quantities None (never 0), no rolls
    fold_cuts(fold, roll_length_m, lap_m)     -> the roll cuts of a continuous-fold plan, checked against the fold's
                                                 own roll count and consumed membrane (refused when they disagree)
    table(rows, systems, ...)                 -> rows, held rows, per-system totals: rolls to buy (shared cutting plan)
                                                 next to the rolls-if-alone sum, for both junction methods
    from_areas(areas, plans, held=())         -> the table of built areas (waterproofing_system.build_area, v26)
    held_from_lines(lines, measured_ids)      -> HELD rows for FIN.WP.FLOOR lines without a quantity
    csv_rows(t) / markdown(t)                 -> the outputs

Quantities (UP-WP-MAT-001): A net horizontal area; B installed membrane (laid: coverage + upturns + doorway pieces +
laps); consumed = the roll length cut x roll width (rips included); C whole rolls of the cutting plan. The owner's
"membrane cut" of his Q-30 example (16.28 m2) is B of the continuous fold; his "gross offcuts" (3.72 m2) is the rolls'
area minus B. Rules: UP-WP-001, -002, -003, -005, UP-WP-LAY-001, UP-WP-MAT-001, UP-WP-ROOF-001, UP-QTY-STATUS-001.
Project-agnostic; stdlib only (membrane_layout.pack_rolls for the shared continuous-fold plan)."""

from __future__ import annotations

import math

from engine.source import membrane_layout as ML

METHOD_ID = "MEMBRANE_PURCHASE_TABLE_V1"
EPS = 1e-6
MEASURED, HELD = "MEASURED", "HELD"
SEPARATE, FOLD = "SEPARATE_UPSTAND", "CONTINUOUS_FOLD"
RULES = ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-005", "UP-WP-LAY-001", "UP-WP-MAT-001", "UP-WP-ROOF-001",
         "UP-QTY-STATUS-001")


class TableError(ValueError):
    pass


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ rows
def held_row(*, floor, room_id, reason, name_en=None, name_ar=None, kind=None, net_m2=None, source=None):
    """a waterproofed area whose wet / dry status, outline or layout is not established: shown with its reason, every
    quantity None (never 0), excluded from the roll totals and counted beside them."""
    if not reason:
        raise TableError(f"a HELD row needs its reason ({floor} {room_id})")
    return {"state": HELD, "floor": floor, "room_id": room_id, "name_en": name_en, "name_ar": name_ar, "kind": kind,
            "reason": reason, "source": source, "net_m2": None if net_m2 is None else _r(net_m2),
            "rolls_if_alone": None, "fold_rolls_if_alone": None}


def _layout_strips(layout):
    lay = (layout or {}).get("layout") or {}
    if not lay:
        return None
    alts = [{k: a.get(k) for k in ("direction", "rolls", "seams", "consumed_m2")} for a in lay.get("alternatives") or ()]
    return {"direction": lay.get("direction"), "floor_strips": lay.get("floor_strips"),
            "direction_alternatives": alts,
            "direction_changes_rolls": len({a["rolls"] for a in alts}) > 1,
            "strip_length_m": _r(lay.get("strip_length_m")), "last_strip_width_m": _r(lay.get("last_strip_width_m")),
            "pieces_per_strip": lay.get("pieces_per_strip"), "band_width_m": _r(lay.get("band_width_m")),
            "band_pieces": len(lay.get("band_pieces_m") or ()),
            "band_pieces_m": round(sum(lay.get("band_pieces_m") or ()), 4)}


def _fold(install):
    jun = (install or {}).get("junction") or {}
    f = jun.get("continuous_fold")
    if not f:
        return {"state": "NOT_COMPUTED", "reason": "no installation layer (ARCH_TAKEOFF_V2.6) for this area"}, None
    if f.get("state") != "COMPUTED":
        return {"state": "BLOCKED", "reason": f.get("reason")}, jun.get("state")
    return {"state": "COMPUTED", "direction": f["direction"], "strips": f["strips"],
            "strip_length_m": f["strip_length_m"], "last_strip_width_m": f["last_strip_width_m"],
            "pieces_per_strip": f["pieces_per_strip"], "developed_m": f.get("developed_m"),
            "required_m2": f["required_m2"], "installed_m2": f["installed_m2"], "consumed_m2": f["consumed_m2"],
            "laps_m2": f["laps_m2"], "corner_excess_m2": f["corner_excess_m2"], "trim_m2": f["trim_m2"],
            "rolls_if_alone": f["rolls"], "seams": f["seams"], "corner_squares": f.get("corner_squares"),
            "jamb_slits": f.get("jamb_slits"),
            "alternatives": f.get("alternatives") or [],
            "direction_changes_rolls": len({a["rolls"] for a in f.get("alternatives") or ()}) > 1}, jun.get("state")


def area_row(row, layout=None, install=None, *, name_ar=None, roll_area_m2=None):
    """one measured area of the waterproofing schedule (waterproofing_system.area_schedule row), with its layout
    (strips of the separate upstand) and its installation record (the continuous-fold alternative)."""
    if row.get("layout_state") == "BLOCKED":
        return held_row(floor=row["floor"], room_id=row["room_id"], name_en=row.get("name_en"), name_ar=name_ar,
                        kind=row.get("scope"), net_m2=row.get("A_net_horizontal_m2"),
                        reason=f"membrane layout BLOCKED: {row.get('blocked_by')}", source="waterproofing schedule")
    up = row["upturn"]
    ps = row.get("proven_subtotal") or {}
    surface = ps.get("total_m2")
    if surface is None and up.get("area_m2") is not None:
        surface = row["A_net_horizontal_m2"] + up["area_m2"] + row["doorway_continuation_m2"]
    rolls = row["rolls_if_installed_alone"]
    gross = row.get("gross_roll_area_if_alone_m2")
    fold, junction_state = _fold(install)
    tr = row["doorway_transitions"]
    out = {"state": MEASURED, "floor": row["floor"], "room_id": row["room_id"], "name_en": row.get("name_en"),
           "name_ar": name_ar, "kind": row.get("scope"), "location_types": row.get("location_types") or [],
           "system_id": row["system_id"],
           "net_m2": _r(row["A_net_horizontal_m2"]), "upturn_lm": _r(up["eligible_lm"]), "upturn_h_m": up["height_m"],
           "upturn_m2": _r(up["area_m2"]), "doorway_continuation_m2": _r(row["doorway_continuation_m2"]),
           "surface_m2": _r(surface),
           "doorway_transitions_open": tr["unresolved"], "doorway_transition_range_m2": tr["range_m2"],
           "strips": _layout_strips(layout),
           "laps_m2": _r(row.get("laps_m2")), "installed_m2": _r(row["B_installed_m2"]),
           "consumed_m2": _r(row["consumed_m2"]), "cutting_waste_m2": _r(row["cutting_waste_m2"]),
           "reusable_offcuts_m2": _r(row.get("reusable_offcuts_m2")),
           "rolls_if_alone": rolls, "gross_roll_area_if_alone_m2": _r(gross),
           "gross_offcuts_if_alone_m2": None if gross is None or row["B_installed_m2"] is None else
           _r(gross - row["B_installed_m2"]),
           "material_state": row.get("final_material_state") or row.get("state"),
           "junction_state": junction_state, "fold": fold,
           "fold_rolls_if_alone": fold.get("rolls_if_alone"),
           "fold_gross_offcuts_if_alone_m2": None if fold["state"] != "COMPUTED" or roll_area_m2 is None else
           _r(fold["rolls_if_alone"] * roll_area_m2 - fold["installed_m2"]),
           "withheld": [w.get("what") for w in row.get("withheld") or ()]}
    return out


# ------------------------------------------------------------------------------------------------ fold cuts
def fold_cuts(fold, roll_length_m, lap_m, roll_width_m):
    """the cuts (lengths along the roll, full roll width) of a continuous-fold plan, rebuilt from its own record
    (strips x pieces per strip, the last piece of a spliced strip shorter by the end laps) and checked against the
    fold's own consumed membrane and roll count; a disagreement is an error, never a silent figure."""
    n, k, Ls = fold["strips"], fold["pieces_per_strip"], fold["strip_length_m"]
    L = roll_length_m
    lens = [L] * (k - 1) + [Ls - (k - 1) * (L - lap_m)] if k > 1 else [Ls]
    cuts = [x for _ in range(n) for x in lens]
    if abs(sum(cuts) * roll_width_m - fold["consumed_m2"]) > 1e-3:
        raise TableError(f"fold cuts {sum(cuts) * roll_width_m:.4f} m2 differ from the fold's consumed "
                         f"{fold['consumed_m2']} m2")
    bins, _ = ML.pack_rolls(cuts, L)
    if len(bins) != fold["rolls_if_alone"]:
        raise TableError(f"fold cuts pack into {len(bins)} rolls, the fold record says {fold['rolls_if_alone']}")
    return cuts


# ------------------------------------------------------------------------------------------------ table
def _system_totals(sys_rec, rows):
    sid, W, L, lap = sys_rec["system_id"], sys_rec["roll_width_m"], sys_rec["roll_length_m"], sys_rec["lap_m"]
    mine = [r for r in rows if r["state"] == MEASURED and r["system_id"] == sid]
    if sorted(r["room_id"] for r in mine) != sorted(sys_rec["areas"]):
        raise TableError(f"system {sid}: the table rows and the cutting plan name different areas")
    alone = sum(r["rolls_if_alone"] for r in mine)
    if alone != sys_rec["rolls_if_each_area_alone"]:
        raise TableError(f"system {sid}: rolls if alone {alone} vs the cutting plan's {sys_rec['rolls_if_each_area_alone']}")
    sep = {"method": SEPARATE, "source": "waterproofing_system.cutting_plan (the engine's procurement plan)",
           "rolls_to_buy": sys_rec["rolls"], "rolls_if_each_area_alone": alone,
           "rolls_saved_by_reusing_offcuts": alone - sys_rec["rolls"],
           "gross_roll_area_m2": _r(sys_rec["gross_roll_area_m2"]), "consumed_m2": _r(sys_rec["consumed_m2"]),
           "installed_m2": _r(sys_rec["installed_m2"]), "net_m2": _r(sys_rec["net_m2"]),
           "untouched_roll_tails_m2": _r(sys_rec["untouched_roll_tails_m2"]),
           "roll_count_state": sys_rec["roll_count_state"], "why_not_confirmed": sys_rec["why_not_confirmed"]}
    folded = [r for r in mine if r["fold"]["state"] == "COMPUTED"]
    not_folded = [r["room_id"] for r in mine if r["fold"]["state"] != "COMPUTED"]
    fold = {"method": FOLD, "areas_computed": len(folded), "areas_not_computed": not_folded,
            "source": "wp_install.continuous_fold cuts, packed together by membrane_layout.pack_rolls"}
    if folded:
        cuts = [c for r in folded for c in fold_cuts(r["fold"], L, lap, W)]
        bins, packing = ML.pack_rolls(cuts, L)
        fa = sum(r["fold"]["rolls_if_alone"] for r in folded)
        inst = sum(r["fold"]["installed_m2"] for r in folded)
        fold.update(rolls_to_buy=len(bins), rolls_if_each_area_alone=fa, rolls_saved_by_reusing_offcuts=fa - len(bins),
                    gross_roll_area_m2=_r(len(bins) * W * L), consumed_m2=_r(sum(cuts) * W),
                    installed_m2=_r(inst), gross_offcuts_m2=_r(len(bins) * W * L - inst),
                    complete=not not_folded,
                    note=None if not not_folded else
                    f"{len(not_folded)} area(s) have no continuous-fold plan (shape or doorway, see each row): the "
                    "fold total covers the computed areas only and is not a project total")
    return {"system_id": sid, "roll_width_m": W, "roll_length_m": L, "lap_m": lap, "areas": len(mine),
            SEPARATE: sep, FOLD: fold}


def table(rows, systems, *, held=(), project_id=None):
    """the membrane table: measured rows (area_row), held rows, and per membrane system the rolls to buy (the
    engine's shared cutting plan; the continuous-fold cuts packed the same way) next to the rolls-if-alone sum.
    Never a total across systems; held areas are excluded from the rolls and counted beside them."""
    rows = sorted(rows, key=lambda r: (str(r["floor"]), str(r["room_id"])))
    held = sorted([dict(h) for h in held] + [r for r in rows if r["state"] == HELD],
                  key=lambda r: (str(r["floor"]), str(r["room_id"])))
    rows = [r for r in rows if r["state"] == MEASURED]
    seen = set()
    for r in rows + held:
        key = (r["floor"], r["room_id"])
        if key in seen:
            raise TableError(f"area {key} appears twice in the table")
        seen.add(key)
    totals = [_system_totals(s, rows) for s in sorted(systems, key=lambda s: str(s["system_id"]))]
    covered = {r for s in systems for r in s["areas"]}
    orphan = [r["room_id"] for r in rows if r["room_id"] not in covered]
    if orphan:
        raise TableError(f"measured rows outside every cutting plan: {orphan}")
    floors = {}
    for r in rows:
        f = floors.setdefault(r["floor"], {"floor": r["floor"], "areas": 0, "held": 0, "net_m2": 0.0,
                                           "surface_m2": 0.0, "installed_m2": 0.0, "rolls_if_alone": 0})
        f["areas"] += 1
        f["net_m2"] = _r(f["net_m2"] + r["net_m2"])
        f["surface_m2"] = _r(f["surface_m2"] + (r["surface_m2"] or 0.0))
        f["installed_m2"] = _r(f["installed_m2"] + (r["installed_m2"] or 0.0))
        f["rolls_if_alone"] += r["rolls_if_alone"] or 0
    for h in held:
        floors.setdefault(h["floor"], {"floor": h["floor"], "areas": 0, "held": 0, "net_m2": 0.0, "surface_m2": 0.0,
                                       "installed_m2": 0.0, "rolls_if_alone": 0})["held"] += 1
    return {"method": METHOD_ID, "project_id": project_id, "rules": list(RULES), "rows": rows, "held": held,
            "floors": [floors[k] for k in sorted(floors, key=str)], "systems": totals,
            "held_count": len(held),
            "junction": {"engine_state": "UNRESOLVED (N-11): the engine selects no floor-to-wall junction",
                         "owner_words": "Q-30: wall upturn 20 cm folded from the same membrane, not a separate strip",
                         "shown": [SEPARATE, FOLD], "selected": None},
            "never": ["a held area as 0", "a total across membrane systems", "rolls from net area / roll area",
                      "a quantity laid out again outside the engine"]}


def from_areas(areas, plans, *, held=(), project_id=None):
    """the table of built areas (waterproofing_system.build_area(..., v26=True)) and their cutting plan."""
    rows = []
    for a in areas:
        W = a["system"]["group"][1]
        L = a["system"]["group"][2]
        rows.append(area_row(a["row"], a.get("layout"), a.get("v26"), name_ar=a.get("name_ar"),
                             roll_area_m2=None if W is None or L is None else W * L))
    return table(rows, plans, held=held, project_id=project_id)


def held_from_lines(lines, measured):
    """HELD rows for the FIN.WP.FLOOR lines of a run that carry no quantity (measured: the (floor, room_id) pairs
    already in the table)."""
    out = []
    for ln in lines:
        if ln.get("item_code") != "FIN.WP.FLOOR" or ln.get("measured_net") is not None:
            continue
        loc = ln.get("location") or {}
        key = (loc.get("floor"), loc.get("room_id"))
        if key in measured:
            continue
        rfi = ln.get("rfi") or {}
        why = rfi.get("question") or ln.get("notes") or ln.get("evidence_state")
        out.append(held_row(floor=key[0], room_id=key[1], name_en=loc.get("room_name_en"),
                            name_ar=loc.get("room_name_ar"), kind="FIN.WP.FLOOR", reason=f"{ln.get('evidence_state')}: "
                            f"{why}", source=f"BOQ line {ln.get('line_id')}"))
    return out


# ------------------------------------------------------------------------------------------------ outputs
CSV_COLUMNS = ("state", "floor", "room_id", "name_en", "name_ar", "kind", "net_m2", "upturn_lm", "upturn_m2",
               "doorway_continuation_m2", "surface_m2", "direction", "floor_strips", "strip_length_m",
               "last_strip_width_m", "band_pieces", "laps_m2", "installed_m2", "consumed_m2", "cutting_waste_m2",
               "rolls_if_alone", "gross_offcuts_if_alone_m2", "fold_state", "fold_direction", "fold_strips",
               "fold_strip_length_m", "fold_last_strip_width_m", "fold_installed_m2", "fold_consumed_m2",
               "fold_rolls_if_alone", "fold_gross_offcuts_if_alone_m2", "material_state", "reason")


def csv_rows(t):
    out = []
    for r in t["rows"] + t["held"]:
        s, f = r.get("strips") or {}, r.get("fold") or {}
        out.append({"state": r["state"], "floor": r["floor"], "room_id": r["room_id"], "name_en": r.get("name_en"),
                    "name_ar": r.get("name_ar"), "kind": r.get("kind"), "net_m2": r.get("net_m2"),
                    "upturn_lm": r.get("upturn_lm"), "upturn_m2": r.get("upturn_m2"),
                    "doorway_continuation_m2": r.get("doorway_continuation_m2"), "surface_m2": r.get("surface_m2"),
                    "direction": s.get("direction"), "floor_strips": s.get("floor_strips"),
                    "strip_length_m": s.get("strip_length_m"), "last_strip_width_m": s.get("last_strip_width_m"),
                    "band_pieces": s.get("band_pieces"), "laps_m2": r.get("laps_m2"),
                    "installed_m2": r.get("installed_m2"), "consumed_m2": r.get("consumed_m2"),
                    "cutting_waste_m2": r.get("cutting_waste_m2"), "rolls_if_alone": r.get("rolls_if_alone"),
                    "gross_offcuts_if_alone_m2": r.get("gross_offcuts_if_alone_m2"), "fold_state": f.get("state"),
                    "fold_direction": f.get("direction"), "fold_strips": f.get("strips"),
                    "fold_strip_length_m": f.get("strip_length_m"),
                    "fold_last_strip_width_m": f.get("last_strip_width_m"), "fold_installed_m2": f.get("installed_m2"),
                    "fold_consumed_m2": f.get("consumed_m2"), "fold_rolls_if_alone": f.get("rolls_if_alone"),
                    "fold_gross_offcuts_if_alone_m2": r.get("fold_gross_offcuts_if_alone_m2"),
                    "material_state": r.get("material_state"),
                    "reason": r.get("reason") or (f.get("reason") if f.get("state") != "COMPUTED" else None)})
    return out


def _v(x):
    return "-" if x is None else (f"{x:g}" if isinstance(x, (int, float)) else str(x))


def markdown(t):
    """the table as the owner reads it: one row per area, then the rolls to buy per membrane system."""
    head = ("| Floor | Area | Net m2 | Upturn lm | Surface m2 | Strips (separate upstand) | Installed m2 | Consumed m2 "
            "| Rolls alone | Strips (fold) | Fold installed m2 | Fold rolls alone | State |")
    out = [f"# Membrane table ({t['method']})", "", head, "|" + "---|" * 13]
    for r in t["rows"]:
        s, f = r.get("strips") or {}, r["fold"]
        st = "-" if not s else f"{s['floor_strips']} x {_v(s['strip_length_m'])} m {s['direction']} (last " \
                                f"{_v(s['last_strip_width_m'])} m) + {s['band_pieces']} band pieces"
        ft = f"{f['strips']} x {_v(f['strip_length_m'])} m {f['direction']} (last {_v(f['last_strip_width_m'])} m)" \
            if f["state"] == "COMPUTED" else f"not computed: {f.get('reason')}"
        out.append(f"| {r['floor']} | {r.get('name_en') or r['room_id']} | {_v(r['net_m2'])} | {_v(r['upturn_lm'])} | "
                   f"{_v(r['surface_m2'])} | {st} | {_v(r['installed_m2'])} | {_v(r['consumed_m2'])} | "
                   f"{_v(r['rolls_if_alone'])} | {ft} | {_v(f.get('installed_m2'))} | {_v(f.get('rolls_if_alone'))} | "
                   f"{r['material_state']} |")
    for h in t["held"]:
        out.append(f"| {h['floor']} | {h.get('name_en') or h['room_id']} | HELD | - | - | - | - | - | - | - | - | - | "
                   f"HELD: {h['reason']} |")
    out += ["", "## Rolls to buy (per membrane system; held areas excluded)", ""]
    for s in t["systems"]:
        a, b = s[SEPARATE], s[FOLD]
        out.append(f"- {s['system_id']} (roll {s['roll_width_m']:g} x {s['roll_length_m']:g} m, lap {s['lap_m']:g} m), "
                   f"{s['areas']} areas: separate upstand {a['rolls_to_buy']} rolls (alone {a['rolls_if_each_area_alone']}"
                   f", {a['roll_count_state']}); continuous fold "
                   + (f"{b['rolls_to_buy']} rolls (alone {b['rolls_if_each_area_alone']})" + (
                       "" if b["complete"] else f", {len(b['areas_not_computed'])} area(s) not computed")
                      if "rolls_to_buy" in b else "not computed for any area"))
    out.append(f"- held areas (not in any roll total): {t['held_count']}")
    return "\n".join(out) + "\n"
