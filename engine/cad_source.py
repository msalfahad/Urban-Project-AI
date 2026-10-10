"""Read an authored CAD drawing's census from LibreDWG's JSON decode.

Two decoders, two answers. LibreDWG's DXF writer aborts inside the BLOCKS
section on project 7757's file and emits no ENTITIES section at all; its
JSON writer reports `SUCCESS` and decodes every object. So the census is
taken from the JSON, and the DXF path is not used.

WHAT THIS MODULE IS CAREFUL ABOUT

  1. A DECODER ARTEFACT IS NOT DRAWING CONTENT. The JSON carries 33,388
     AcDbBlockBegin and 33,389 AcDbBlockEnd records for a file whose
     BLOCK_HEADER table has 33 entries and which holds 931 block
     references. Those records are the same defect that broke the DXF
     writer, and counting them as geometry would inflate the drawing
     thirtyfold. They are excluded and the exclusion is reported.

  2. AN UNNAMED ENTITY IS NOT AN UNKNOWN ENTITY. The JSON leaves `entity`
     empty for most records but still carries the numeric DWG type and the
     AcDb subclass, which name it exactly. Reading the empty string as
     "unidentified" would have discarded 10,000 entities that are perfectly
     well identified.

  3. A DECLARED UNIT IS A DECLARATION. `$INSUNITS` is what the author said,
     which is evidence and not a measurement — and `$INSUNITS = 0` means NO
     unit was declared, never millimetres.

Nothing here measures a room, computes an area, or asserts a scale.
"""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# DWG object type codes, for the records whose `entity` name the decoder
# left empty. The subclass in the JSON says the same thing in words; both
# are recorded so a surprise is visible rather than silently mapped.
DWG_TYPE = {
    1: "TEXT", 2: "ATTRIB", 3: "ATTDEF", 4: "BLOCK_BEGIN", 5: "BLOCK_END",
    6: "SEQEND", 7: "INSERT", 8: "MINSERT", 10: "VERTEX_2D",
    11: "VERTEX_3D", 15: "POLYLINE_2D", 16: "POLYLINE_3D", 17: "ARC",
    18: "CIRCLE", 19: "LINE", 20: "DIMENSION_ORDINATE",
    21: "DIMENSION_LINEAR", 22: "DIMENSION_ALIGNED", 23: "DIMENSION_ANG3PT",
    24: "DIMENSION_ANG2LN", 25: "DIMENSION_RADIUS",
    26: "DIMENSION_DIAMETER", 27: "POINT", 31: "3DSOLID", 34: "VIEWPORT",
    35: "ELLIPSE", 36: "SPLINE", 44: "MTEXT", 45: "LEADER",
    77: "LWPOLYLINE", 78: "HATCH", 763: "ARC_DIMENSION",
}

# Block-definition delimiters. Real ones exist — one pair per block — but
# this file's decode emits tens of thousands, so they are never counted as
# drawing content. See note 1 above.
BLOCK_DELIMITERS = (4, 5)

# What an entity contributes, in the engine's own vocabulary. This is a
# CENSUS grouping, not a domain mapping: calling a LINE on the wall layer a
# wall is a decision for the normalisation layer, with evidence, not
# something a counter may do.
GEOMETRY = ("LINE", "LWPOLYLINE", "POLYLINE_2D", "POLYLINE_3D", "ARC",
            "CIRCLE", "ELLIPSE", "SPLINE", "SOLID", "3DFACE", "REGION")
ANNOTATION = ("TEXT", "MTEXT", "ATTRIB", "ATTDEF", "LEADER", "MULTILEADER")
DIMENSIONS = tuple(v for v in DWG_TYPE.values() if v.startswith("DIMENSION")
                   or v == "ARC_DIMENSION")
SYMBOLS = ("INSERT", "MINSERT")

# $INSUNITS. Zero is the trap and is spelled out.
INSUNITS = {
    0: "UNITLESS — the drawing declares NO unit. NOT a declaration of "
       "millimetres and must never be read as one",
    1: "inches", 2: "feet", 3: "miles", 4: "millimetres", 5: "centimetres",
    6: "metres", 7: "kilometres", 10: "yards", 14: "decimetres",
}
MEASUREMENT = {0: "imperial (ANSI) linetype and hatch tables",
               1: "metric (ISO) linetype and hatch tables"}


class CadReadError(RuntimeError):
    """The CAD source could not be decoded, which is not a finding of empty."""


@dataclass(frozen=True)
class CadEntity:
    """One decoded drawing entity, named and placed on its layer."""

    handle: int
    kind: str
    subclass: str
    layer: str
    block: str = ""


@dataclass
class CadCensus:
    """What the drawing is made of. No measurement of anything."""

    source_file: str = ""
    source_sha256_16: str = ""
    format_marker: str = ""
    header: dict = field(default_factory=dict)
    entities: list = field(default_factory=list)
    layers: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    block_inserts: dict = field(default_factory=dict)
    excluded_block_delimiters: int = 0
    decoder: str = ""

    # -- declarations ----------------------------------------------------
    @property
    def declared_unit_code(self):
        return self.header.get("INSUNITS")

    def declared_units(self) -> dict:
        code = self.declared_unit_code
        # Absent and unrecognised are different facts. This decoder's JSON
        # writer omits MEASUREMENT entirely, and reporting that as an
        # unrecognised code would invent a reading the file never gave.
        meas = self.header.get("MEASUREMENT", "ABSENT")
        lfac = self.header.get("DIMLFAC")
        out = {
            "insunits_code": code,
            "insunits_means": (
                "NOT_PRESENT_IN_THIS_DECODE" if code is None
                else INSUNITS.get(code, "unrecognised code")),
            "measurement_code": None if meas == "ABSENT" else meas,
            "measurement_means": (
                "NOT_PRESENT_IN_THIS_DECODE — the variable is absent from "
                "this decoder's output, which is not a reading of it"
                if meas == "ABSENT"
                else MEASUREMENT.get(meas, "unrecognised code")),
            "unit_is_declared": code not in (None, 0),
            "this_is": ("the author's DECLARATION of the drawing unit. It is "
                        "strong evidence and it is not a measurement"),
        }
        # DIMLFAC scales what a dimension PRINTS relative to what it
        # MEASURES. At 0.1 the text is a tenth of the drawing distance, so a
        # 1000 mm wall is annotated "100" — the numbers on the sheet are
        # centimetres while the geometry is millimetres. Comparing printed
        # text to geometry without this is wrong by exactly that factor,
        # which is the kind of error that passes review because both numbers
        # look plausible.
        if lfac not in (None, 1.0):
            out["dimension_text_factor"] = lfac
            out["dimension_text_means"] = (
                f"printed dimension text = drawing distance x {lfac}. The "
                "annotation unit is NOT the drawing unit on this sheet, and "
                "any comparison between the two must apply this factor")
        return out

    # -- census ----------------------------------------------------------
    def by_kind(self) -> dict:
        return dict(Counter(e.kind for e in self.entities).most_common())

    def by_layer(self) -> dict:
        out = {}
        for lay, n in Counter(e.layer for e in self.entities).most_common():
            out[lay] = {"entities": n,
                        "by_kind": dict(Counter(
                            e.kind for e in self.entities
                            if e.layer == lay).most_common(6))}
        return out

    def group_totals(self) -> dict:
        k = Counter(e.kind for e in self.entities)
        return {
            "geometry": sum(k[x] for x in GEOMETRY),
            "annotation": sum(k[x] for x in ANNOTATION),
            "dimensions": sum(k[x] for x in DIMENSIONS),
            "symbol_references": sum(k[x] for x in SYMBOLS),
            "points": k.get("POINT", 0),
            "hatches": k.get("HATCH", 0),
        }

    def record(self) -> dict:
        return {
            "source_file": self.source_file,
            "source_sha256_16": self.source_sha256_16,
            "format_marker": self.format_marker,
            "decoder": self.decoder,
            "declared_units": self.declared_units(),
            "declared_header_variables": dict(self.header),
            "drawing_entities": len(self.entities),
            "entities_by_kind": self.by_kind(),
            "entities_by_layer": self.by_layer(),
            "group_totals": self.group_totals(),
            "layers": sorted(self.layers),
            "blocks": sorted(self.blocks),
            "block_insert_counts": dict(
                sorted(self.block_inserts.items(), key=lambda x: -x[1])),
            "excluded_block_delimiter_records": self.excluded_block_delimiters,
            "why_those_were_excluded": (
                "the decoder emitted one BLOCK_BEGIN/BLOCK_END pair per "
                f"{self.excluded_block_delimiters // 2 or 1} for a file whose "
                f"block table has {len(self.blocks)} entries and which holds "
                f"{sum(self.block_inserts.values())} block references. They "
                "are the same defect that made the DXF writer abort, and "
                "counting them as geometry would inflate the drawing by "
                "orders of magnitude"),
            "contains_no_measurement": True,
            "what_is_not_established_here": (
                "no wall, no opening, no room, no area, no length and no "
                "scale in building millimetres. A LINE on a layer named W is "
                "not yet a wall — that is a decision for the normalisation "
                "layer, made on evidence"),
        }


def _abs_handle(h):
    return h[-1] if isinstance(h, list) and h else None


def decode(dwg: str, *, converter: str, out_json: str) -> dict:
    """Run the decoder. Returns its own report; raises if it produced nothing."""
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    cmd = [converter, "-O", "JSON", "-o", out_json, dwg]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    ok = Path(out_json).exists() and Path(out_json).stat().st_size > 0
    if not ok:
        raise CadReadError(
            f"{converter} produced no output for {Path(dwg).name}. The file "
            "was not read, which is NOT a finding that it is empty")
    return {"command": " ".join(cmd), "exit_code": res.returncode,
            "stderr_tail": (res.stderr or "")[-800:],
            "json_bytes": Path(out_json).stat().st_size}


def census(decoded: dict, *, source_file: str = "",
           source_sha256_16: str = "", decoder: str = "") -> CadCensus:
    """Turn a LibreDWG JSON decode into a census. Nothing is measured."""
    objs = decoded.get("OBJECTS") or []
    if not objs:
        raise CadReadError(
            "the decode carries no OBJECTS. Nothing is known about this "
            "drawing, and that is not the same as the drawing being empty")

    layer_name, block_name = {}, {}
    for o in objs:
        kind = o.get("object")
        if kind == "LAYER":
            layer_name[_abs_handle(o.get("handle"))] = o.get("name", "")
        elif kind == "BLOCK_HEADER":
            block_name[_abs_handle(o.get("handle"))] = o.get("name", "")

    hdr_src = decoded.get("HEADER") or {}
    wanted = ("INSUNITS", "MEASUREMENT", "LUNITS", "LUPREC", "AUNITS",
              "EXTMIN", "EXTMAX", "LIMMIN", "LIMMAX", "DIMSCALE", "LTSCALE",
              "TILEMODE", "ACADVER", "DIMLUNIT", "CELTSCALE", "PDSIZE",
              "DIMLFAC", "DIMALT", "DIMALTF", "UNITMODE")
    header = {k: hdr_src.get(k) for k in wanted if k in hdr_src}

    ents, dropped = [], 0
    inserts: Counter = Counter()
    for o in objs:
        if "entity" not in o:
            continue
        t = o.get("type")
        if t in BLOCK_DELIMITERS:
            dropped += 1
            continue
        # The decoder leaves `entity` empty on most records; the numeric type
        # and the subclass still name it, so the name is taken from them.
        kind = o.get("entity") or DWG_TYPE.get(t) or f"DWG_TYPE_{t}"
        blk = block_name.get(_abs_handle(o.get("block_header")), "")
        if kind in SYMBOLS:
            inserts[blk or "UNRESOLVED_BLOCK_REFERENCE"] += 1
        ents.append(CadEntity(
            handle=_abs_handle(o.get("handle")) or -1,
            kind=kind, subclass=str(o.get("_subclass") or ""),
            layer=layer_name.get(_abs_handle(o.get("layer")),
                                 "UNRESOLVED_LAYER_REFERENCE"),
            block=blk))

    return CadCensus(
        source_file=source_file, source_sha256_16=source_sha256_16,
        format_marker=str(decoded.get("FILEHEADER", {}).get("version", "")),
        header=header, entities=ents,
        layers=[v for v in layer_name.values() if v],
        blocks=[v for v in block_name.values()
                if v and not v.startswith("*")],
        block_inserts=dict(inserts), excluded_block_delimiters=dropped,
        decoder=decoder)
