"""PROFILE TAKEOFF (M1) - the first quantities of a NEW project, from a person-confirmed profile (generic).

A profile (JSON) says what the inventory could only guess: which layers hold footing and column outlines, which text
pattern is a footing / column tag, which sheet is which storey, the printed storey heights, the units, and the schedule
rows typed from the schedule sheet. Nothing in a profile is defaulted: a null leaves that part UNRESOLVED.

Per footing / column sheet:
    outlines   closed axis-aligned rectangles on the family's layers (structural_qto.rectangles)
    binding    each tag to the SMALLEST rectangle containing it (structural_qto.associate); a rectangle with no tag,
               or with two, and a tag inside no rectangle, are exceptions, never resolved by distance
    size       the drawn rectangle against the schedule plan size (structural_qto.size_check, either orientation)
    quantity   footing  L x W x D                      (schedule, size confirmed by the drawing)
               column   B x H x storey height          (schedule section confirmed by the drawing, printed height)
Every quantity is PROVISIONAL with support SOURCE_COMPLETE_UNREVIEWED: all dimensions printed and the outline drawn,
but not taken through the strict release review, so it is a release candidate, not VERIFIED. A size mismatch or a type
missing from the schedule is UNRESOLVED (with the schedule / drawn exposure where both exist). Families with no generic
extractor in M1 (beams, slabs, ground beams, stairs, walls, lintels, all reinforcement) are one UNRESOLVED item each,
with the tag evidence the inventory found.

Stdlib only; the drawing is read by the caller (drawing_inventory.segments / texts) and passed in as plain data.
"""

from __future__ import annotations

import re

from engine.source import provisional_estimate as PE
from engine.source import structural_qto as Q

POLICY_ID = "PROFILE_TAKEOFF_V1"
GENERIC_FAMILIES = ("FOOTINGS", "COLUMNS")
NOT_COVERED = ("BEAMS", "SLABS", "GROUND_BEAMS", "STAIRS", "WALLS", "LINTELS")


class ProfileError(ValueError):
    pass


def conventions(profile):
    """The profile as a convention set: the mapping itself is an assumption a person made; storey heights are
    printed values only when the profile names their source."""
    name = profile.get("profile") or "UNNAMED_PROFILE"
    conv = [{"id": "PROFILE_MAPPING", "title": "Layer, tag and sheet mapping of this drawing set", "kind": "choice",
             "options": [name], "base": name, "provenance": "READING_OF_PRINTED_VALUE",
             "source": profile.get("confirmed_by") or "profile file (not stated who confirmed it)",
             "rationale": "Which layers / tags / sheets hold which members was read off the drawing by a person."}]
    for s in profile.get("sheets", []):
        h, src = s.get("storey_height_m"), s.get("storey_height_source")
        if s.get("storey") and h is not None and src:
            conv.append({"id": f"STOREY_HEIGHT_{s['storey']}", "title": f"Storey height {s['storey']}",
                         "kind": "number", "unit": "m", "base": float(h), "low": float(h), "high": float(h),
                         "provenance": "PRINTED_VALUE", "source": src,
                         "rationale": "Printed floor-to-floor height; the column is measured over it."})
    conv += profile.get("conventions", [])
    return PE.Conventions({"set": name, "conventions": conv})


def _exc(out, kind, family, sheet, detail, where=None):
    out.append({"EXCEPTION_ID": f"EX-{len(out) + 1:04d}", "KIND": kind, "FAMILY": family, "SHEET": sheet,
                "DETAIL": detail, "LOCATION": where})


def _rows(fam_cfg, ttype, storey):
    row = (fam_cfg.get("schedule") or {}).get(ttype)
    if row and storey and "by_storey" in row:
        row = dict(row, **row["by_storey"].get(storey, {}))
    return row


def takeoff(profile, extracted, inventory=None):
    """extracted[sheet_id] = {"texts": [...], family: {"segments": [...], "curved": n}}. Returns (items, exceptions,
    conventions)."""
    conv = conventions(profile)
    items, exc = [], []
    u = profile.get("units_to_mm")
    sheets = {s["sheet_id"]: s for s in profile.get("sheets", [])}
    if not u:
        _exc(exc, "UNITS_NOT_CONFIRMED", "ALL", None, "units_to_mm is null: no quantity is computed")
    for fam in GENERIC_FAMILIES:
        cfg = (profile.get("families") or {}).get(fam)
        if not cfg or not cfg.get("layers") or not cfg.get("sheets") or not u:
            items.append(PE.item(item_id=f"U-C:{fam}:NOT_CONFIGURED", component_id=f"{fam}:ALL", trade="CONCRETE",
                                 family=fam, storey="ALL", category="UNRESOLVED", support="NO_GEOMETRY",
                                 confidence="LOW", blocker="PROFILE_INCOMPLETE", source="profile",
                                 expression="layers, sheets and schedule of this family not confirmed in the profile"))
            _exc(exc, "PROFILE_INCOMPLETE", fam, None, "family not configured (layers / sheets / units)")
            continue
        tag_re = re.compile(cfg["tag_regex"])
        eps = 0.5 / u
        for sid in cfg["sheets"]:
            sh = sheets.get(sid)
            if sh is None:
                raise ProfileError(f"{fam}: sheet {sid} is not in the profile")
            storey = sh.get("storey")
            data = extracted.get(sid, {})
            fd = data.get(fam, {"segments": [], "curved": 0})
            if fd.get("curved"):
                _exc(exc, "CURVED_EDGES_IGNORED", fam, sid, f"{fd['curved']} curved edges on the family layers are "
                                                            "not straightened; members drawn with them are not found")
            rects = Q.rectangles(fd["segments"], eps=eps)
            tags = [dict(t, value=t["value"].upper()) for t in data.get("texts", [])
                    if tag_re.match(t["value"].upper())]
            a = Q.associate(rects, tags)
            for o in a["orphans"]:
                _exc(exc, "TAG_OUTSIDE_EVERY_RECTANGLE", fam, sid, f"tag {o['value']} has no outline",
                     [round(o["x"], 1), round(o["y"], 1)])
                items.append(PE.item(item_id=f"U-C:{fam}:{sid}:{o['key']}", component_id=f"{fam}:{sid}:{o['key']}",
                                     trade="CONCRETE", family=fam, storey=storey or "UNKNOWN", category="UNRESOLVED",
                                     support="NO_GEOMETRY", confidence="LOW", blocker="TAG_WITHOUT_OUTLINE",
                                     source=f"{sid} text {o['key']}", expression=f"{o['value']}: outline not found"))
            for iss in a["issues"]:
                if iss["why"] == Q.NO_TAG:
                    _exc(exc, "RECTANGLE_WITHOUT_TAG", fam, sid, "closed outline with no tag (an undetected member, "
                                                                 "a detail or a nested outline)", iss["rectangle"])
            for r in a["rectangles"]:
                if len(r["tags"]) > 1:
                    vals = "/".join(t["value"] for t in r["tags"])
                    _exc(exc, "RECTANGLE_WITH_SEVERAL_TAGS", fam, sid, f"one outline holds {vals}", r["bounds"])
                    for t in r["tags"]:
                        items.append(PE.item(
                            item_id=f"U-C:{fam}:{sid}:{t['key']}", component_id=f"{fam}:{sid}:{t['key']}",
                            trade="CONCRETE", family=fam, storey=storey or "UNKNOWN", category="UNRESOLVED",
                            support="NO_GEOMETRY", confidence="LOW", blocker="COMBINED_OUTLINE",
                            source=f"{sid} text {t['key']}", expression=f"{vals} share one outline"))
                    continue
                if len(r["tags"]) != 1:
                    continue
                t = r["tags"][0]
                items.append(_quantify(fam, cfg, sid, storey, t, r, u, conv, exc))
    found = {t["family_guess"]: t for t in (inventory or {}).get("tag_families", [])}
    for fam in NOT_COVERED:
        ev = found.get(fam)
        items.append(PE.item(item_id=f"U-C:{fam}:NO_GENERIC_EXTRACTOR", component_id=f"{fam}:ALL", trade="CONCRETE",
                             family=fam, storey="ALL", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                             blocker="NO_GENERIC_EXTRACTOR_M1", source="drawing inventory",
                             expression=(f"{ev['count']} '{ev['prefix']}' tags found ({ev['distinct']} types); no "
                                         "generic extractor in M1" if ev else "no generic extractor in M1")))
    items.append(PE.item(item_id="U-S:ALL:NO_GENERIC_EXTRACTOR", component_id="REINFORCEMENT:ALL",
                         trade="REINFORCEMENT", family="ALL", storey="ALL", category="UNRESOLVED",
                         support="NO_GEOMETRY", confidence="LOW", blocker="NO_GENERIC_EXTRACTOR_M1",
                         source="drawing inventory",
                         expression="bar schedules need counts, cut lengths, laps and shapes per member; not extracted"))
    PE.check(items, conv)
    return items, exc, conv


def _quantify(fam, cfg, sid, storey, t, r, u, conv, exc):
    ttype = t["value"]
    row = _rows(cfg, ttype, storey)
    cid = f"{fam}:{sid}:{ttype}@{round(r['bounds'][0])},{round(r['bounds'][1])}"
    common = dict(component_id=cid, trade="CONCRETE", family=fam, storey=storey or "UNKNOWN",
                  source=f"sheet {sid}; outline {','.join(r['edge_keys'][:4])}; tag {t['key']}; "
                         f"schedule {cfg.get('schedule_source') or 'typed into the profile'}")
    drawn = sorted((r["width"] * u, r["height"] * u))
    if row is None:
        _exc(exc, "TYPE_NOT_IN_SCHEDULE", fam, sid, f"{ttype} is not a schedule row", r["bounds"])
        return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="TYPE_NOT_IN_SCHEDULE", dimensions={"drawn_mm": drawn},
                       expression=f"{drawn[0]:g} x {drawn[1]:g} mm drawn; depth / height not scheduled", **common)
    if fam == "FOOTINGS":
        L, W, D = row.get("L_mm"), row.get("W_mm"), row.get("D_mm")
        sc = Q.size_check(r, L, W, u, tol_mm=cfg.get("size_tol_mm", 10)) if L and W else None
        if sc is None or D is None:
            _exc(exc, "SCHEDULE_ROW_INCOMPLETE", fam, sid, f"{ttype}: L / W / D missing", r["bounds"])
            return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                           blocker="SCHEDULE_ROW_INCOMPLETE", expression="L x W x D", **common)
        v_s = L * W * D / 1e9
        if sc["state"] != Q.SIZE_CONFIRMED:
            v_d = drawn[0] * drawn[1] * D / 1e9
            _exc(exc, "SIZE_MISMATCH", fam, sid, f"{ttype}: drawn {drawn} mm vs schedule {[L, W]} mm", r["bounds"])
            return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                           blocker="SIZE_MISMATCH", exposure_low=min(v_s, v_d), exposure_high=max(v_s, v_d),
                           dimensions={"schedule_mm": [L, W, D], "drawn_mm": drawn},
                           expression="schedule or drawn plan size x D (they differ)", **common)
        return PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v_s, base=v_s, high=v_s,
                       dimensions={"L_mm": L, "W_mm": W, "D_mm": D, "drawn_mm": drawn},
                       formula="L x W x D (schedule; plan size confirmed by the drawn outline)",
                       assumptions=["PROFILE_MAPPING"], support="SOURCE_COMPLETE_UNREVIEWED", confidence="HIGH",
                       limitations="not reviewed under the strict release rules; overlaps with ground beams and "
                                   "strap ends not deducted", double_count_risk="footing / ground-beam prism at "
                                                                                "strap ends", blocker="NOT_REVIEWED",
                       **common)
    B, H = row.get("B_mm"), row.get("H_mm")
    sc = Q.size_check(r, B, H, u, tol_mm=cfg.get("size_tol_mm", 10)) if B and H else None
    hid = f"STOREY_HEIGHT_{storey}"
    if sc is None:
        _exc(exc, "SCHEDULE_ROW_INCOMPLETE", fam, sid, f"{ttype}: B / H missing", r["bounds"])
        return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="SCHEDULE_ROW_INCOMPLETE", expression="B x H x storey height", **common)
    if sc["state"] != Q.SIZE_CONFIRMED:
        _exc(exc, "SIZE_MISMATCH", fam, sid, f"{ttype}: drawn {drawn} mm vs schedule {[B, H]} mm", r["bounds"])
    if hid not in conv.items:
        _exc(exc, "NO_STOREY_HEIGHT", fam, sid, f"storey {storey}: printed height not in the profile", r["bounds"])
        return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="NO_STOREY_HEIGHT", dimensions={"B_mm": B, "H_mm": H},
                       expression=f"{B / 1000:g} x {H / 1000:g} x storey height (not printed / not in the profile)",
                       **common)
    h = conv.base(hid)
    v_s = B * H / 1e6 * h
    if sc["state"] != Q.SIZE_CONFIRMED:
        v_d = drawn[0] * drawn[1] / 1e6 * h
        return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                       blocker="SIZE_MISMATCH", exposure_low=min(v_s, v_d), exposure_high=max(v_s, v_d),
                       dimensions={"schedule_mm": [B, H], "drawn_mm": drawn, "height_m": h},
                       expression="schedule or drawn section x storey height (they differ)", **common)
    return PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v_s, base=v_s, high=v_s,
                   dimensions={"B_mm": B, "H_mm": H, "height_m": h, "drawn_mm": drawn},
                   formula="B x H (schedule; section confirmed by the drawn outline) x printed storey height",
                   assumptions=["PROFILE_MAPPING", hid], support="SOURCE_COMPLETE_UNREVIEWED", confidence="HIGH",
                   limitations="not reviewed under the strict release rules; floor-to-floor height includes the "
                               "slab / beam zone at the top", double_count_risk="column / slab / beam joint at the "
                                                                                "top of the storey (not deducted)",
                   blocker="NOT_REVIEWED", **common)


def policy_record():
    return {"policy": POLICY_ID, "families": GENERIC_FAMILIES, "not_covered": NOT_COVERED,
            "rule": "a profile is a person's reading; every quantity is a release candidate, never VERIFIED"}
