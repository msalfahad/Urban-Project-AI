"""Ask the owner in words an owner can answer, and draw the plan that removes the last of the ambiguity.

A question that names OS-77f8fed2eb15 cannot be answered by anybody who was not in the room when the id was minted.
A question that names the opening between the Hall and the Lobby can be answered by whoever owns the flat.  So the
register keeps the id and the question does not: every row here carries a room, an opening type, a width and what the
opening joins, and the id sits in a column marked AUDIT.

Where the words still leave a doubt - a bedroom wall with two identical 1.10 m gaps facing the stair landing - a
numbered plan crop is drawn from the frozen geometry so the owner can point at the thing rather than describe it.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import opening_source_search as OS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
PLAN = OUT / "QORTUBA_OWNER_QUESTION_PLAN.png"


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


# A question number is a name the owner holds.  Once a number has been put in front of them - in a table or on a
# crop - it belongs to that opening for good: if an answered question vacates its slot and the ones still open slide
# up, every crop already sent points at the wrong wall.  So numbers are issued once, recorded here, and never reused.
# New questions take the next free number after the highest ever issued.
ISSUED_NUMBERS = {
    "BE-07": 1, "BE-06": 2, "BE-05": 3, "BE-04": 4, "BE-02": 5, "BE-01": 6,
    "OS-b1e147c89482": 7, "OS-77f8fed2eb15": 8, "OS-85cb2192ebc0": 9,
    "OS-3144b5fbb149": 10, "OS-045efd7810a7": 11,
}


def questions():
    """One numbered row per thing the owner must answer, ranked so the biggest openings come first."""
    rows = [r for r in OS.human_register()
            if r["IS_AN_OPENING_THROUGH_THE_WALL"] and r["INSIDE_APARTMENT"] and r["HEIGHT_M"] is None]
    heights = [r for r in rows if r["TYPE"] not in ("UNRESOLVED", "OPEN_PASSAGE")]
    gaps = [r for r in rows if r["TYPE"] in ("UNRESOLVED", "OPEN_PASSAGE")]
    nxt = iter(range(max(ISSUED_NUMBERS.values()) + 1, 999))

    def num(r):
        return ISSUED_NUMBERS.get(r["OPENING_ID"]) or next(nxt)

    out = []
    for r in sorted(heights, key=lambda z: -z["WIDTH_M"]):
        out.append({"#": num(r), "ROOM": r["ROOM"], "OPENING": r["OPENING"], "WIDTH_M": r["WIDTH_M"],
                    "QUESTION": "Height?", "LOCATION": r["LOCATION"],
                    "ASKS_FOR": "HEIGHT", "TRADE": r["MATERIAL_TRADE"],
                    "WHY_IT_MATTERS": "no area can be released for this opening's trade, and every wall it stands in "
                                      "stays partial, until the height is known",
                    "AUDIT_OPENING_ID": r["OPENING_ID"]})
    for r in sorted(gaps, key=lambda z: -z["WIDTH_M"]):
        passage = r["TYPE"] == "OPEN_PASSAGE"
        # US-16 and US-17: once the type is settled the type question is never asked again.  What is left for a
        # passage is the vertical condition, asked in the words a person standing in it would use.
        out.append({"#": num(r), "ROOM": r["ROOM"],
                    "OPENING": "Open passage" if passage else "Opening of unknown type",
                    "WIDTH_M": r["WIDTH_M"],
                    "QUESTION": (f"Opening {r['LOCATION']}, {r['WIDTH_M']:.2f} m wide: is it open all the way to the "
                                 "ceiling, or is there wall above it?") if passage else
                                "What is this: a door, an open passage, a window, or something else?",
                    "LOCATION": r["LOCATION"],
                    "ASKS_FOR": "PASSAGE_HEIGHT" if passage else "TYPE",
                    "TRADE": r["MATERIAL_TRADE"],
                    "WHY_IT_MATTERS": ("full height means the opening is the full 3.00 m wall height with no top "
                                       "reveal; a head means the owner gives the height and a top reveal applies.  "
                                       "Until then the wall AREAS of the two rooms it joins stay partial - the width "
                                       "deduction from the skirting and profile path is already taken") if passage else
                                      "the type decides whether a height may be defaulted and which trade carries it; "
                                      "until then the walls it stands in cannot be finished",
                    "PLAN_READING": r["PDF_READER"],
                    "AUDIT_OPENING_ID": r["OPENING_ID"]})
    return out


def _bbox(pts, pad=1500):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def marked_plan(qs, width=1800):
    """A plan drawn from the frozen room boxes and wall bands, with each question numbered where it stands."""
    mb = {b["BAND_ID"]: b for b in reg(R1, "PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER")["ROWS"]}
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]
    rooms = [r for r in reg(QS, "QORTUBA_ROOM_REGISTER")["ROWS"] if r["INSIDE_APARTMENT"]]
    blue = {b["BLUE_ELEMENT_ID"]: b for b in reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]}
    floors = {f["ROOM_ID"]: f for f in reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]}

    segs = []
    for w in walls:
        c = mb[w["BAND_ID"]].get("CENTERLINE_IF_DERIVED")
        if not c or c.get("KIND") != "LINE":
            continue
        a = round(c["ANGLE_DEG"], 1); off = c["AXIS_OFFSET_MM"]; e0, e1 = c["EXTENT_MM"]
        if a == 0.0:
            segs.append(((e0, off), (e1, off), w["THICKNESS_MM"]))
        elif a == 90.0:
            segs.append(((-off, e0), (-off, e1), w["THICKNESS_MM"]))
    pts = [p for s in segs for p in s[:2]] + [(r["BBOX_MM"][0], r["BBOX_MM"][1]) for r in rooms] \
        + [(r["BBOX_MM"][2], r["BBOX_MM"][3]) for r in rooms]
    x0, y0, x1, y1 = _bbox(pts)
    sc = width / (x1 - x0)
    height = int((y1 - y0) * sc)

    def P(x, y):
        return (int((x - x0) * sc), int(height - (y - y0) * sc))

    img = Image.new("RGB", (width, height + 30), "white")
    d = ImageDraw.Draw(img)
    for r in rooms:
        b = r["BBOX_MM"]
        d.rectangle([P(b[0], b[3]), P(b[2], b[1])], fill="#F4F7FB")
    for (a, b, t) in segs:
        d.line([P(*a), P(*b)], fill="#1F3A5F", width=max(2, int(t * sc)))
    for r in rooms:
        b = r["BBOX_MM"]
        f = floors.get(r["ROOM_ID"], {})
        lab = OS.friendly(r["CANONICAL_NAME"], f.get("METHOD_A_CAD_POLYGON_AREA_M2"))
        cx, cy = P((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        d.text((cx - 4 * len(lab or ""), cy), lab or "", fill="#33475B")

    sites = {}
    for w in walls:
        c = mb[w["BAND_ID"]].get("CENTERLINE_IF_DERIVED")
        for o in w["OPENINGS"]:
            if c and c.get("KIND") == "LINE":
                a = round(c["ANGLE_DEG"], 1); off = c["AXIS_OFFSET_MM"]; e0, e1 = c["EXTENT_MM"]
                mid = (e0 + e1) / 2
                sites[o["SITE_ID"]] = (mid, off) if a == 0.0 else (-off, mid)
    placed = []
    for q in qs:
        oid = q["AUDIT_OPENING_ID"]
        pos = sites.get(oid) or (tuple(blue[oid]["POSITION_MM"]) if oid in blue else None)
        if not pos:
            continue
        px, py = P(*pos)
        while any(abs(px - a) < 26 and abs(py - b) < 26 for a, b in placed):
            py -= 28
        placed.append((px, py))
        d.ellipse([px - 13, py - 13, px + 13, py + 13], fill="#C0392B", outline="white", width=2)
        d.text((px - (4 if q["#"] < 10 else 8), py - 6), str(q["#"]), fill="white")
    d.text((8, height + 8), "QORTUBA - openings the owner is asked about, numbered as in the question table",
           fill="#33475B")
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(PLAN)
    return PLAN


def finish():
    qs = questions()
    plan = marked_plan(qs)
    out = {
        "ARTIFACT": "QORTUBA_OWNER_QUESTIONS",
        "RULE": "US-12: every question names the room, the opening, the width and what it joins.  The opaque id is "
                "carried in the AUDIT column and is never put to the owner",
        "TABLE_COLUMNS": ["#", "ROOM", "OPENING", "WIDTH_M", "QUESTION"],
        "AUDIT_COLUMNS": ["AUDIT_OPENING_ID"],
        "ROWS": qs, "COUNT": len(qs),
        "ASKING_FOR_A_HEIGHT": sum(1 for q in qs if q["ASKS_FOR"] == "HEIGHT"),
        "ASKING_FOR_A_TYPE": sum(1 for q in qs if q["ASKS_FOR"] == "TYPE"),
        "ASKING_FOR_A_PASSAGE_HEIGHT": sum(1 for q in qs if q["ASKS_FOR"] == "PASSAGE_HEIGHT"),
        "A_NUMBER_IS_ISSUED_ONCE": "a question number belongs to its opening for good.  #8 and #9 were the two open "
                                   "passages and are now answered, so those numbers are retired rather than reused: "
                                   "the crops already in the owner's hands still point at what they always pointed at",
        "RETIRED_NUMBERS": sorted(set(ISSUED_NUMBERS.values()) - {q["#"] for q in qs}),
        "MARKED_PLAN": str(plan),
        "NO_HEIGHT_IS_ASSUMED_FOR_ANY_OF_THEM": True,
        "WINDOWS_ARE_NOT_GROUPED": "each window is asked separately.  None is given another's height unless the owner "
                                   "says they are the same",
        "EVERY_ROW_CHANGES_A_QUANTITY": True,
    }
    (OUT / "QORTUBA_OWNER_QUESTIONS.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str),
                                                      "utf-8")
    return out


if __name__ == "__main__":
    o = finish()
    print(f"{'#':>2}  {'Room':30s} {'Opening':26s} {'Width':>7s}  Question")
    for q in o["ROWS"]:
        print(f"{q['#']:>2}  {str(q['ROOM']):30s} {q['OPENING']:26s} {q['WIDTH_M']:7.3f}  {q['QUESTION']}")
    print()
    print("marked plan:", o["MARKED_PLAN"])
