"""URBAN SOURCE CAPABILITY REGISTER (R8.2) — what each source kind can and cannot support.

Per source kind and route:

    mapping_status              VERIFIED / VERIFIED_BY_FLAG_PATTERN / SOURCE_MAPPING_UNVERIFIED / NOT_MAPPED
    physical_geometry_support   REALISED_EXACT / CARRIED_ANCHOR_ONLY / NOT_REALISED
    source_geometry_exact       the route reproduces the authored geometry exactly (no approximation)
    downstream_measurement_supported
                                the CURRENT Urban geometry stack (cad_adapter primitives:
                                SEGMENT / ARC / CIRCLE / HATCH) can carry and measure it
    identity_support / text_support
    completeness_effect         what an unrealised or unverified instance does to completeness
    known_decoder_limitations
    default_finding             code emitted when the kind is met (None: none)
    impacts                     (domain, severity) of that finding, overriding the code default
    required_validation         what must be shown before the kind may support FINAL
    downstream_allowed_uses     e.g. FINAL_GEOMETRY, PREVIEW, CARRIED_ANNOTATION, REVIEW_ONLY

Rules this register encodes (R8.2 brief §5-§7):
  * no semantic claim from type alone: a POINT is not "noise", a SOLID is not
    "a wall", a HATCH is never wall geometry by being a hatch;
  * an exact source geometry is not a downstream-supported geometry: an
    elliptical arc may PREVIEW but may not silently become FINAL until the
    consumer can preserve / measure it;
  * invisible = retained + HIDDEN, never realised as measurement geometry.

The register is DATA. It never inspects a project; routes consult it by kind.
"""

from __future__ import annotations

from . import findings as F

D1 = "D1_LIBREDWG_JSON"
D2 = "D2_DXF_EZDXF"

FINAL_GEOMETRY = "FINAL_GEOMETRY"
PREVIEW = "PREVIEW"
CARRIED_ANNOTATION = "CARRIED_ANNOTATION"
REVIEW_ONLY = "REVIEW_ONLY"
IDENTITY_CANDIDATE = "IDENTITY_CANDIDATE"
NONE = "NONE"


def _row(kind, *, d1, d2, geometry, exact, downstream, identity="NONE", text="NONE",
         completeness="NONE", limitations=(), finding=None, impacts=None, validation=(), uses=(), note=""):
    return {"source_kind": kind,
            "routes": {D1: d1, D2: d2},
            "physical_geometry_support": geometry,
            "source_geometry_exact": exact,
            "downstream_measurement_supported": downstream,
            "identity_support": identity, "text_support": text,
            "completeness_effect": completeness,
            "known_decoder_limitations": list(limitations),
            "default_finding": finding,
            "impacts": [list(i) for i in (impacts if impacts is not None else (F.IMPACTS[finding] if finding else ()))],
            "required_validation": list(validation),
            "downstream_allowed_uses": list(uses),
            "note": note}


REGISTER = [
    _row("LINE", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         uses=(FINAL_GEOMETRY,), validation=("K1/K2 reconciliation PASS",)),
    _row("ARC", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         limitations=("cad_adapter: sweep under reflection wrong (MIRRORED_ARC_SWEEP)",),
         uses=(FINAL_GEOMETRY,), validation=("orientation from the full composed map", "K1/K2 reconciliation PASS")),
    _row("CIRCLE", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         uses=(FINAL_GEOMETRY,)),
    _row("LWPOLYLINE", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         limitations=("D1: extrusion/elevation keys present only when their flag bit is set",
                      "project readers that test 'flag & 1' for closure read the DWG extrusion bit, not 'closed' (512)"),
         uses=(FINAL_GEOMETRY,)),
    _row("ELLIPSE", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=False,
         finding=None, validation=("downstream consumer preserves RealisedEllipticalArc", "measurement frame + chord tolerance (R8.3)"),
         uses=(PREVIEW,), note="exact at source; the cad_adapter-based stack has no elliptical primitive"),
    _row("ELLIPTICAL_ARC_FROM_NON_UNIFORM_SCALE", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True,
         downstream=False, finding=F.NON_UNIFORM_SCALE_CURVE, uses=(PREVIEW,),
         validation=("downstream consumer preserves RealisedEllipticalArc",)),
    _row("INSERT", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         identity="BLOCK_NAME_IS_NOT_IDENTITY", uses=(FINAL_GEOMETRY,),
         validation=("block definition present", "block lineage by handle, not name")),
    _row("MINSERT", d1="SOURCE_MAPPING_UNVERIFIED", d2="VERIFIED_WITH_LIBRARY_LIMITATIONS", geometry="NOT_REALISED",
         exact=False, downstream=False, completeness="BLOCKS_REGION", finding=F.SOURCE_MAPPING_UNVERIFIED,
         limitations=("no MINSERT in any real D1 decode", "EZDXF-L01 virtual_entities first cell only",
                      "EZDXF-L02 nested under reflection: rows mis-placed"),
         validation=("real D1 field observation", "native AutoCAD MINSERT_REFLECTION_ORACLE check"),
         uses=(REVIEW_ONLY,)),
    _row("ATTRIB", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         identity="IDENTITY_CANDIDATE_WITH_OWNER_INSERT", text="LITERAL", uses=(CARRIED_ANNOTATION, IDENTITY_CANDIDATE)),
    _row("ATTDEF", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         text="TEMPLATE_ONLY", uses=(CARRIED_ANNOTATION,),
         note="a definition inside a block is a template, not a value; never an identity source"),
    _row("TEXT", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         text="LITERAL", identity="IDENTITY_CANDIDATE", uses=(CARRIED_ANNOTATION, IDENTITY_CANDIDATE),
         limitations=("legacy code-page bytes may be undecodable -> TEXT_UNDECODABLE",)),
    _row("MTEXT", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         text="FORMAT_CODES_NOT_DECODED_R8_2", identity="IDENTITY_CANDIDATE", uses=(CARRIED_ANNOTATION,),
         validation=("CAD_TEXT_PLAIN literal decode (R8.3)",)),
    _row("DIMENSION", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         text="DISPLAY_VALUE", uses=(CARRIED_ANNOTATION,),
         limitations=("its *D graphics block is NOT realised as geometry",
                      "D1: *D headers' entity lists overlap *U lists (LibreDWG 0.13.3)"),
         note="a dimension is evidence about geometry, never geometry"),
    _row("HATCH", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=False, downstream=False,
         uses=(CARRIED_ANNOTATION,), note="never wall geometry because it is a hatch"),
    _row("POINT", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         uses=(CARRIED_ANNOTATION,),
         note="may be survey / setting-out / marker / residue: CARRIED, NOT REGION-FORMING BY DEFAULT, never deleted"),
    _row("SOLID", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         completeness="REVIEW", finding=F.UNVERIFIED_FOR_QTO_USE, uses=(REVIEW_ONLY,),
         note="may be poche / fill or meaningful geometry; not a wall by type, not discarded"),
    _row("WIPEOUT", d1="NOT_MAPPED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         finding=F.CUSTOM_CLASS, impacts=((F.PRESENTATION, F.REVIEW),), uses=(REVIEW_ONLY,),
         note="masks geometry in the plot; the geometry beneath still exists in the source"),
    _row("IMAGE", d1="NOT_MAPPED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         finding=F.CUSTOM_CLASS, impacts=((F.DOCUMENT_CONTENT, F.BLOCKING),), uses=(REVIEW_ONLY,),
         note="raster content is unknown; it is not vector geometry and not proof of absence"),
    _row("OLE2FRAME", d1="VERIFIED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         finding=F.SKIPPED, limitations=("D1 (LibreDWG 0.13.3) labels it type 2, the ATTRIB code",
                                         "cad_adapter drops it silently"),
         uses=(REVIEW_ONLY,)),
    _row("ACAD_PROXY_ENTITY", d1="SOURCE_MAPPING_UNVERIFIED", d2="NOT_MAPPED", geometry="NOT_REALISED",
         exact=False, downstream=False, completeness="BLOCKS_REGION", finding=F.PROXY, uses=(REVIEW_ONLY,)),
    _row("CUSTOM_CLASS", d1="NOT_MAPPED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         completeness="BLOCKS_REGION", finding=F.CUSTOM_CLASS, uses=(REVIEW_ONLY,),
         note="class type codes >= 500 are per-file; identify a class by its name, never by its number"),
    _row("SPLINE", d1="NOT_MAPPED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         completeness="BLOCKS_REGION", finding=F.UNHANDLED, uses=(REVIEW_ONLY,)),
    _row("REGION", d1="NOT_MAPPED", d2="NOT_MAPPED", geometry="NOT_REALISED", exact=False, downstream=False,
         completeness="BLOCKS_REGION", finding=F.UNHANDLED, uses=(REVIEW_ONLY,), note="ACIS body; not decodable here"),
    _row("XREF", d1="SOURCE_MAPPING_UNVERIFIED", d2="VERIFIED_WITH_LIBRARY_LIMITATIONS", geometry="NOT_REALISED",
         exact=False, downstream=False, completeness="BLOCKS_REGION", finding=F.XREF_NOT_RESOLVED,
         limitations=("D1: resolved/unloaded flag semantics unobserved", "EZDXF-L03 xref content absent from virtual_entities"),
         uses=(REVIEW_ONLY,), note="zero children is never proof of absence"),
    _row("ANONYMOUS_BLOCK", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         identity="NOT_FROM_NAME", finding=F.DYNAMIC_BLOCK_UNRESOLVED,
         uses=(FINAL_GEOMETRY,), note="*U geometry is evaluated; identity is not established by the name"),
    _row("DYNAMIC_BLOCK", d1="VERIFIED", d2="VERIFIED", geometry="REALISED_EXACT", exact=True, downstream=True,
         identity="EED_PARENT_REFERENCE_UNVERIFIED", finding=F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED,
         limitations=("parent identity only via application xdata (AcDbBlockRepBTag), mapping unverified",
                      "stretch / flip values appear baked into *U geometry; not proven without one native check"),
         validation=("one native AutoCAD comparison of one dynamic door (evaluated geometry vs properties)",),
         uses=(FINAL_GEOMETRY,), note="geometry usable; opening IDENTITY claims blocked until identity is verified"),
    _row("INVISIBLE_ENTITY", d1="VERIFIED", d2="VERIFIED", geometry="CARRIED_ANCHOR_ONLY", exact=True, downstream=False,
         uses=(NONE,), note="retained, disposition HIDDEN, never realised as measurement geometry"),
    _row("OWNER_UNRESOLVED", d1="VERIFIED", d2="NOT_APPLICABLE", geometry="NOT_REALISED", exact=False, downstream=False,
         completeness="BLOCKS_REGION", finding=F.OWNER_UNRESOLVED, uses=(REVIEW_ONLY,),
         note="UNPLACED: kept with handle, type, layer and raw owner; never realised in model space"),
]

BY_KIND = {r["source_kind"]: r for r in REGISTER}


def row(kind: str) -> dict:
    return BY_KIND[kind]


def impacts_for_kind(kind: str) -> tuple:
    return tuple(tuple(i) for i in BY_KIND[kind]["impacts"])
