"""The structured record a quantity becomes once it leaves the workpaper.

Everything upstream of this file is measurement: registers, rules, owner answers, arithmetic.  This is the handover
shape - one flat record per BOQ line, carrying its project, its floor, its room, its trade, its formula, its source,
the rule that governs it, its status and its approval state.  It exists so that approved quantities can one day move
into the Urban Projects Manager without anyone re-typing them.

Two things it deliberately does NOT do.  It does not call anything APPROVED: approval is the owner's act, and every
record leaves here as DRAFT until the owner says otherwise.  And it does not connect to anything - no web app, no
database, no upload.  Raw extraction must never write project financial data; a person stands between.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"

PROJECT_ID = "QORTUBA_Q1_S1_L6"
ZONE = "APARTMENT"

# §J: the fields every record carries.  A record missing any of them is not a handover record.
FIELDS = ("PROJECT_ID", "DRAWING_REVISION", "FLOOR", "ZONE", "ROOM_ID", "ROOM_NAME", "TRADE", "ITEM", "SUBITEM",
          "MEASURED_QUANTITY", "MEASURED_UNIT", "FINAL_BOQ_QUANTITY", "BOQ_UNIT", "FORMULA", "SOURCE", "RULE_ID",
          "STATUS", "APPROVAL_STATUS", "NOTES")

# the engine's own status vocabulary, mapped onto the five the handover shape uses
STATUS_MAP = {
    "FINAL_QUANTITY_AVAILABLE": "FINAL",
    "PARTIALLY_CALCULATED": "PARTIAL",
    "OWNER_INPUT_REQUIRED": "OWNER_INPUT_REQUIRED",
    "PROJECT_RULE_REQUIRED": "SPEC_REQUIRED",
    "SPEC_REQUIRED": "SPEC_REQUIRED",
    "SOURCE_REQUIRED": "DRAWING_REQUIRED",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
    "GEOMETRIC_REFERENCE_ONLY": "NOT_APPLICABLE",
}
APPROVAL_STATES = ("DRAFT", "REVIEWED", "APPROVED")


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def records():
    qs = reg("QORTUBA_RECALCULATED_QUANTITIES_V1")
    fz = reg("FREEZE_URBAN_OWNER_RULES_V1")
    qfz = reg("FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01", QS)
    floor = qfz["STOREY"]
    rev = qfz["DIGEST"][:16]
    out = []
    for x in qs["ROWS"]:
        rooms = x["ROOMS"] or []
        # a trade line is not a room line: the rooms it was built from are named, and the room workpaper stays behind
        # it rather than being flattened into it
        out.append({
            "PROJECT_ID": PROJECT_ID,
            "DRAWING_REVISION": rev,
            "FLOOR": floor,
            "ZONE": ZONE,
            "ROOM_ID": None,
            "ROOM_NAME": ", ".join(sorted(set(rooms))) or None,
            "TRADE": x["TRADE"],
            "ITEM": x["BOQ_ITEM"],
            "SUBITEM": x["QUANTITY_ID"],
            "MEASURED_QUANTITY": x["MEASURED_NET_QUANTITY"],
            "MEASURED_UNIT": x["UNIT"],
            "FINAL_BOQ_QUANTITY": (x["MEASURED_NET_QUANTITY"]
                                   if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE" else None),
            "BOQ_UNIT": x["UNIT"],
            "FORMULA": x["FORMULA"],
            "SOURCE": x["PARAMETER_SOURCE"],
            "RULE_ID": x["RULE_ID"],
            "STATUS": STATUS_MAP[x["STATUS"]],
            "APPROVAL_STATUS": "DRAFT",
            "NOTES": " | ".join(z for z in (
                x["NOTE"],
                (f"{len(x['RESIDUAL_OPENINGS'])} opening(s) still without a height"
                 if x["RESIDUAL_OPENINGS"] else None),
                (x["OWNER_CONFIRMED_PARAMETER_NOTE"] if x["USES_OWNER_CONFIRMED_PARAMETER"] else None),
                (x["TEMPORARY_DEFAULT_WARNING"] if x["USES_TEMPORARY_DEFAULT"] else None),
            ) if z) or None,
            "QUANTITY_ID": x["QUANTITY_ID"],
            "ROOM_WORKPAPER": "QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC",
            "OWNER_RULES_FREEZE": fz["DIGEST"],
        })
    return out


def finish():
    rows = records()
    for r in rows:
        missing = [k for k in FIELDS if k not in r]
        assert not missing, (r["SUBITEM"], missing)
    body = json.dumps(rows, sort_keys=True, ensure_ascii=False, default=str).encode()
    by_status = {}
    for r in rows:
        by_status[r["STATUS"]] = by_status.get(r["STATUS"], 0) + 1
    rec = {
        "ARTIFACT": "QORTUBA_APPROVED_QUANTITIES",
        "SCHEMA_FIELDS": list(FIELDS),
        "STATUSES": sorted(set(STATUS_MAP.values())),
        "APPROVAL_STATES": list(APPROVAL_STATES),
        "PROJECT_ID": PROJECT_ID,
        "ROWS": rows,
        "COUNT": len(rows),
        "BY_STATUS": by_status,
        "BY_APPROVAL": {"DRAFT": len(rows)},
        "APPROVED_COUNT": sum(1 for r in rows if r["APPROVAL_STATUS"] == "APPROVED"),
        "RULE": "§L: only APPROVED records may enter the Urban Projects Manager.  Nothing here is approved: "
                "approval is the owner's act and cannot be performed by the engine that produced the numbers",
        "NOT_CONNECTED_TO_ANYTHING": "this is an export shape, not an integration.  No web app, no database and no "
                                     "upload exists, and raw extraction must never write project financial data",
        "DIGEST": hashlib.sha256(body).hexdigest()[:16],
    }
    (OUT / "APPROVED_QUANTITIES.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['COUNT']} records, digest {r['DIGEST']}")
    print("by status:", r["BY_STATUS"])
    print("approved:", r["APPROVED_COUNT"], "of", r["COUNT"], "- approval is the owner's act")
