"""R8.1 §12 — MINSERT under a reflecting parent: build the one-time native AutoCAD oracle.

Research lab only (never imported by engine/). Writes
    MINSERT_REFLECTION_ORACLE.dxf   open in AutoCAD, compare markers
    MINSERT_REFLECTION_ORACLE.json  expected points, ezdxf points, the disagreement

CASE A (the R8.0 F06_MINSERT_MIRRORED_PARENT scene)
    block CELL   : LINE (0,0)-(100,0) + orientation tick (0,0)-(0,30)
    block HOLDER : MINSERT CELL, 3 columns x 2 rows, spacing 1000 (col) x 500 (row)
    model space  : INSERT HOLDER at (0,0), scale (-1, 1)

    Urban hand truth (block-reference semantics: the placed definition is
    rigidly transformed by the parent's matrix):
        cell (c,r) origin = M . (1000c, 500r) = (-1000c, +500r)
    ezdxf 1.4.4 (Insert.virtual_entities -> Insert.transform, which re-encodes
    the nested MINSERT as rotation/scale but never touches row/column spacing):
        cell (c,r) origin = (-1000c, -500r)

CASE B (top-level MINSERT with a negative X scale; tests "spacing is rotated,
    never scaled", the rule both Urban and ezdxf use)
    model space  : MINSERT CELL at (0,-3000), scale (-1,1), 3x2, 1000 x 500
    expected     : cell (c,r) origin = (1000c, -3000 + 500r), each line drawn toward -x
"""

from __future__ import annotations

import json
from pathlib import Path

import ezdxf
from ezdxf.math import Vec3

HERE = Path(__file__).parent
DXF = HERE / "MINSERT_REFLECTION_ORACLE.dxf"
JSON = HERE / "MINSERT_REFLECTION_ORACLE.json"
COLS, ROWS, CS, RS = 3, 2, 1000.0, 500.0
B_AT = (0.0, -3000.0)


def expected_a():
    return {f"[{c},{r}]": (-CS * c, RS * r) for r in range(ROWS) for c in range(COLS)}


def expected_b():
    return {f"[{c},{r}]": (B_AT[0] + CS * c, B_AT[1] + RS * r) for r in range(ROWS) for c in range(COLS)}


def build_doc():
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    for name, color in (("CONTENT", 7), ("URBAN_EXPECTED", 3), ("EZDXF_RESULT", 1), ("NOTES", 2)):
        doc.layers.add(name, color=color)
    cell = doc.blocks.new("CELL")
    cell.add_line((0, 0), (100, 0), dxfattribs={"layer": "CONTENT"})
    cell.add_line((0, 0), (0, 30), dxfattribs={"layer": "CONTENT"})
    holder = doc.blocks.new("HOLDER")
    holder.add_blockref("CELL", (0, 0), dxfattribs={"layer": "CONTENT"}).grid(size=(ROWS, COLS), spacing=(RS, CS))
    msp = doc.modelspace()
    msp.add_blockref("HOLDER", (0, 0), dxfattribs={"layer": "CONTENT", "xscale": -1.0, "yscale": 1.0})
    msp.add_blockref("CELL", B_AT, dxfattribs={"layer": "CONTENT", "xscale": -1.0, "yscale": 1.0}).grid(
        size=(ROWS, COLS), spacing=(RS, CS))
    return doc


def ezdxf_cell_origins(doc):
    """Cell origins as ezdxf realises them (virtual_entities, recursively)."""
    msp = doc.modelspace()
    out = {}
    for case, ref in (("A", msp.query("INSERT")[0]), ("B", msp.query("INSERT")[1])):
        lines = []

        def walk(e):
            if e.dxftype() == "INSERT":
                cells = list(e.multi_insert()) if e.mcount > 1 else [e]
                for cell in cells:
                    for sub in cell.virtual_entities():
                        walk(sub)
            elif e.dxftype() == "LINE":
                lines.append((Vec3(e.dxf.start), Vec3(e.dxf.end)))
        walk(ref)
        # the tick (length 30) starts at each cell origin
        out[case] = sorted(((round(a.x, 6), round(a.y, 6)) for a, b in lines if abs((b - a).magnitude - 30.0) < 1e-6))
    return out


def main():
    doc = build_doc()
    ez = ezdxf_cell_origins(doc)
    msp = doc.modelspace()
    for (x, y) in expected_a().values():
        msp.add_circle((x, y), 40, dxfattribs={"layer": "URBAN_EXPECTED"})
    for (x, y) in expected_b().values():
        msp.add_circle((x, y), 40, dxfattribs={"layer": "URBAN_EXPECTED"})
    for (x, y) in ez["A"]:
        msp.add_line((x - 60, y - 60), (x + 60, y + 60), dxfattribs={"layer": "EZDXF_RESULT"})
        msp.add_line((x - 60, y + 60), (x + 60, y - 60), dxfattribs={"layer": "EZDXF_RESULT"})
    notes = ["URBAN R8.1 MINSERT REFLECTION ORACLE",
             "GREEN circles = Urban expected cell origins; RED crosses = ezdxf 1.4.4 result (case A)",
             "Case A: INSERT HOLDER scale(-1,1) containing MINSERT CELL 3x2 @1000x500",
             "Case B (y=-3000): top-level MINSERT CELL scale(-1,1) 3x2 @1000x500",
             "Each cell = 100 line along +x (block frame) + 30 tick at its origin"]
    for i, t in enumerate(notes):
        msp.add_text(t, height=60, dxfattribs={"layer": "NOTES", "insert": (-2600, 1600 - 110 * i)})
    doc.saveas(DXF)
    exp_a = sorted(expected_a().values())
    exp_b = sorted(expected_b().values())
    record = {
        "SCHEMA": "URBAN_R8_1_MINSERT_REFLECTION_ORACLE_V1",
        "status": "MINSERT_REFLECTION_ORACLE_CONFLICT",
        "resolution_by_analysis": "HAND_TRUTH_FAVOURED (native AutoCAD confirmation recommended, not blocking)",
        "dxf": DXF.name,
        "ezdxf_version": ezdxf.__version__,
        "case_A": {"scene": "INSERT HOLDER scale(-1,1) > MINSERT CELL 3x2 spacing col 1000 / row 500",
                   "urban_expected_cell_origins": exp_a, "ezdxf_cell_origins": ez["A"],
                   "agree": exp_a == ez["A"],
                   "disagreement": "rows: Urban +500r, ezdxf -500r; columns agree (-1000c)"},
        "case_B": {"scene": "top-level MINSERT CELL scale(-1,1) at (0,-3000) 3x2 spacing col 1000 / row 500",
                   "urban_expected_cell_origins": exp_b, "ezdxf_cell_origins": ez["B"],
                   "agree": exp_b == ez["B"],
                   "note": "tests the stored-field rule itself: offsets rotated, never scaled"},
        "ezdxf_mechanism": ("Insert.virtual_entities() transforms the nested MINSERT with Insert.transform(m); "
                            "InsertCoordinateSystem absorbs the X reflection as rotation 180 + yscale -1 and the "
                            "spacing attributes row_spacing/column_spacing are left untouched. multi_insert() then "
                            "rotates the unchanged (1000c, 500r) offsets by 180 deg -> (-1000c, -500r). The "
                            "reflected grid is only representable in a flat INSERT encoding with an extrusion flip "
                            "or negated spacing, which ezdxf does not do."),
        "why_hand_truth": ("A block reference places its definition by one affine matrix; nothing in the "
                           "definition is re-encoded. The MINSERT inside HOLDER puts cells at (1000c, 500r) in "
                           "HOLDER's frame, and the parent matrix diag(-1,1) maps them to (-1000c, 500r). This is "
                           "what composing matrices (AutoCAD display, K1) gives."),
        "native_autocad_instructions": [
            "Open MINSERT_REFLECTION_ORACLE.dxf in AutoCAD (any release >= 2018). Do not save changes.",
            "ZOOM EXTENTS. Layers: CONTENT (white) = the real geometry; URBAN_EXPECTED (green circles); "
            "EZDXF_RESULT (red crosses); NOTES.",
            "CASE A: check that each white 30-unit tick of the six cells sits inside a GREEN circle "
            "(upper row at y=+500) and NOT on a red cross (y=-500).",
            "Use ID on two tick origins (e.g. column 0 row 1 and column 2 row 1) and record the coordinates.",
            "CASE B (around y=-3000): check each tick sits inside a green circle at (1000c, -3000+500r); "
            "record ID for column 2 row 1.",
            "Optional: MIRROR a copy of the top-level MINSERT about the Y axis, LIST it, and record the "
            "stored column spacing sign, scale and rotation (tells how AutoCAD re-encodes a mirrored MINSERT).",
            "Report the recorded coordinates; they go into R8.2 as NATIVE_AUTOCAD_OBSERVATION, never into production code.",
        ],
    }
    JSON.write_text(json.dumps(record, indent=1) + "\n")
    return record


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("status",)}, indent=1))
    print("A agree:", r["case_A"]["agree"], r["case_A"]["ezdxf_cell_origins"])
    print("B agree:", r["case_B"]["agree"], r["case_B"]["ezdxf_cell_origins"])
