"""CONCRETE COMPLETENESS (M6) - every structural signal of a drawing set ends in one terminal state, and every signal
no measured item explains becomes a located, typed exception (generic, stdlib + engine.source helpers).

    assess(D, intake, items, *, risk=(), heights=None, family_coverage=None, params=None) -> report

The takeoff answers "how much of what I recognised". This pass asks the other question - what does the drawing SHOW
that the takeoff does not hold - without being told what to look for. It reads the route's own detection record (D),
the drawing intake and the items, never a reference quantity.

LEDGERS (each signal gets one terminal state; nothing is dropped)
  GEOMETRY   every line, arc, circle and hatch on a plan sheet that is not annotation is explained by the footprint of
             a detected member (beam band, slab face, column outline, footing, strap) or by an accounted region
             (opening, stair zone, detail, unresolved cell). The rest is clustered by layer and proximity and
             described by its shape (strip, closed area, ring, curve, linework), plan magnitude, position (inside /
             outside the building) and the family its layer name and nearby notes suggest - UNKNOWN when nothing does.
  MEMBERS    a member the route detected but no item holds (a band, a face, a footing) is reported, never lost.
  LABELS     every structural mark ('B12', 'C3', 'F4') or section label ('P.C 20x70', 'GB 30x60') on a plan is consumed
             by a measured member (by reference, or by lying beside a member of its own family) - or reported.
  SCHEDULE   every schedule row is placed on a plan, or reported; a plan mark with no schedule row is reported; the
             schedule reader's own warnings (rows it could not read) are carried.
  STOREYS    every storey a height or a schedule band names has a plan; every plan storey has a height.
  VERTICAL   a column drawn on a storey plan that no column item holds; the route's own column-presence records.
  NOTES      family keywords on any sheet are references; a family referenced but neither measured nor drawn is
             REFERENCED_NOT_DRAWN. Dependency notes ('as per arch', 'see detail', 'by others') are tied to the
             nearest measured member and its items.
  OVERLAP    footprints of measured members that overlap on one plan beyond what the route deducted (double count).
  COVERAGE   slab regions the route excluded or could not resolve (detail, unresolved, stair zone, open boundary).
  UNRESOLVED items the route holds as UNRESOLVED, with their exposure.

V2 (post-discovery; V1 stays frozen at commit 090a470 and its blind run is never overwritten):
  - a hatch is a region marker, not annotation: hatches are read whatever their layer is called; a hatch is the
    member's own fill only when it is the plan's column fill (pattern or layer of the fills found inside columns);
    any other patterned fill lying on measured members is HATCH_ON_MEASURED_MEMBER (that part is marked as something
    the member's item may not be: a cantilever portion, a step, a void, another material), named by the drawing's
    own legend swatch when one is drawn; elsewhere it is a HATCH_REGION group; a fill bounded by another
    unexplained group is that group's fill (evidence, not a second finding); a fill over the whole plan is reported
    LOW as a layer under / round the building (SITE_FILL: blinding, soil, paving).
  - a footing explains only what is drawn on footing / column layers inside it (a pit, a tank or walls drawn inside
    a footing are not the footing).
  - a mark the route saw and could not bind (AMBIGUOUS, TAG_UNBOUND) is consumed by proximity only by a measured
    member that carries the same mark - an unmarked, unresolved band beside it is the question, not the answer.
  - a ring (or a closed outline whose inner faces stop at columns) on a substructure plan, inside the building,
    enclosing a pit-sized area is a pit: lift or tank (candidates beside what the layer / notes say, never decided by
    size alone).

Every finding has a stable id, a location (sheet, storey, box in sheet-local metres), evidence (counts, layer names,
English keywords, structural tokens - never free text), a plan magnitude, a volume only when a printed section or
thickness binds to it (never a ratio), a severity and the action that closes it. The report scores the run: share of
non-annotation linework explained, labels consumed, schedule rows placed, scope population states, unresolved
exposure. A finding is a question for a person, not a quantity: nothing here enters a total.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict

from engine.source import drawing_inventory as DI
from engine.source import drawing_model as DM
from engine.source import member_detection as MD

POLICY_ID = "CONCRETE_COMPLETENESS_V2"

PARAMS = {
    "EXPLAIN_TOL_M": 0.03,          # a line within this distance of a member footprint edge is that member's line
    "EXPLAINED_SHARE": 0.8,         # share of a line's sample points that must be explained
    "CLUSTER_GAP_M": 0.6,           # unexplained entities of one layer closer than this form one group
    "PLAN_MARGIN_M": 8.0,           # the plan area is the members' extent plus this margin (legends / notes outside)
    "SYMBOL_MAX_M": 0.6,            # a group no larger than this next to a text is an annotation symbol
    "SYMBOL_TEXT_M": 1.0,
    "TEXT_NEAR_M": 1.5,             # notes / marks this close to a group describe it
    "MIN_LENGTH_M": 1.0,            # a group shorter than this with no closed area is minor (ledger only)
    "MIN_AREA_M2": 0.25,
    "STRIP_WIDTH_M": (0.08, 0.8),   # a thin closed loop or a parallel pair within this width is a strip
    "LABEL_MEMBER_M": 1.0,          # a mark this close to a member of its own family is that member's mark
    "OVERLAP_MIN_M2": 0.02,         # overlaps smaller than this are drafting noise
    "DEPENDENCY_NEAR_M": 3.0,
    "SLAB_COVERAGE_MIN": 0.6,       # a slab plan whose items hold less than this share of its enclosed area
    "OPENING_SHARE_MAX": 0.25,      # an opening face larger than this share of its plan is reported
    "DEPENDENCY_MEMBER_M": 1.5,     # a dependency note this close to a member is that member's note
    "DEPENDENCY_NOTE_MAX_CHARS": 40,  # longer text is a general note (a signal, not a finding)
    "STAIR_TREAD_M": (0.22, 0.36),  # parallel tread spacing that makes a group of lines a stair flight
    # V2
    "HATCH_ON_MEMBER_SHARE": 0.5,   # a fill this much on measured members is a mark on those members
    "LEGEND_SWATCH_MAX_M2": 1.5,    # a legend swatch is a small fill off the building with its meaning written beside
    "LEGEND_TEXT_M": 3.0,
    "PIT_INNER_M2": (1.0, 9.0),     # a ring on a substructure plan enclosing this much is a pit (lift / tank)
}

PLAN_ROLES = ("FOUNDATION_PLAN", "GROUND_BEAM_PLAN", "SLAB_PLAN", "COLUMN_PLAN")
ANNOTATION_ROLES = MD.ANNOTATION_ROLES
# layer-name tokens of annotation beyond drawing_inventory's roles (generic CAD vocabulary)
ANNOTATION_TOKENS = {"SEC", "SECT", "SECTION", "LEVEL", "LEVELS", "LVL", "ARROW", "NORTH", "SYMB", "SYMBOL", "SYMBOLS",
                     "LEADER", "LEADERS", "CENTER", "CENTRE", "CL", "VIEWPORT", "VPORT", "TITLE", "LOGO", "LEGEND",
                     "CLOUD", "REV", "REVISION", "BUBBLE", "KEY", "KEYPLAN", "NOTE", "NOTES", "TAG", "TAGS", "TABLE",
                     "SCH", "SCHED", "SCHEDULE", "REIN", "REINF", "RFT", "STEEL", "MESH", "BARS", "BAR", "DIM", "DIMS",
                     "TEXT", "TXT", "ANNO", "HATCH", "HAT", "GRID", "AXIS", "AXES", "FRAME", "BORDER", "DEFPOINTS"}
# family vocabulary: layer-name tokens and note words (English; the bilingual note words come from the route's
# SCOPE_WORDS and the drawing model's LABEL_WORDS, read at run time)
FAMILY_TOKENS = {
    "BOUNDARY_WALL": ("BOUN", "BOUND", "BOUNDARY", "FENCE", "COMPOUND", "PLOT"),
    "POOL": ("POOL", "SWIM", "SWIMMING", "JACUZZI"),
    "WATER_TANK": ("TANK", "RESERVOIR", "CISTERN"),
    "LIFT": ("LIFT", "ELEVATOR", "SHAFT"),
    "STAIRS": ("STAIR", "STAIRS", "STAIRCASE", "FLIGHT", "STEPS", "ST"),
    "DOMES": ("DOME", "CUPOLA"),
    "PARAPETS": ("PARAPET", "PARAPETS"),
    "WALLS": ("WALL", "WALLS", "RETAINING", "SHEAR", "CORE", "RW", "BW"),
    "SLAB_STEP": ("SUNK", "SUNKEN", "DROP", "DROPPED", "RECESS", "RECESSED", "DEPRESSED"),
    "CANTILEVER": ("CANTILEVER", "CANT", "OVERHANG", "PROJECTION"),
    "OPENING": ("OPEN", "OPENING", "OPENINGS", "VOID", "VOIDS"),
    "RAMP": ("RAMP",),
    "PLANTER": ("PLANTER", "PLANTERS"),
    "PLANTED_COLUMN": ("PLANTED",),
    "FOOTINGS": ("FOOTING", "FOOTINGS", "FTG", "FDN", "RAFT"),
    "GROUND_BEAMS": ("GROUND", "TIE", "STRAP", "PLINTH"),
    "COLUMNS": ("COLUMN", "COLUMNS", "COL"),
    "BEAMS": ("BEAM", "BEAMS", "LINTEL"),
    "SLABS": ("SLAB", "SLABS", "DECK", "HORDI", "RIBBED"),
}
MEMBER_FAMILIES = ("FOOTINGS", "GROUND_BEAMS", "COLUMNS", "BEAMS", "SLABS")
NOTE_FAMILIES = ("BOUNDARY_WALL", "POOL", "WATER_TANK", "LIFT", "STAIRS", "DOMES", "PARAPETS", "WALLS", "SLAB_STEP",
                 "CANTILEVER", "RAMP", "PLANTER", "PLANTED_COLUMN")
CONCRETE_FAMILIES = ("BOUNDARY_WALL", "POOL", "WATER_TANK", "LIFT", "STAIRS", "DOMES", "PARAPETS", "WALLS",
                     "SLAB_STEP", "CANTILEVER", "RAMP", "PLANTER", "PLANTED_COLUMN", "FOOTINGS", "GROUND_BEAMS",
                     "COLUMNS", "BEAMS", "SLABS")
# item families the route measures -> the family names used here
ITEM_FAMILY = {"FOOTINGS": "FOOTINGS", "GROUND_BEAMS": "GROUND_BEAMS", "GROUND_SLAB": "SLABS", "COLUMNS": "COLUMNS",
               "BEAMS": "BEAMS", "SLABS": "SLABS", "LINTELS": "BEAMS", "STAIRS": "STAIRS", "PLAIN_CONCRETE": None,
               "DOMES": "DOMES", "POOL": "POOL", "LIFT": "LIFT", "WATER_TANK": "WATER_TANK", "PARAPETS": "PARAPETS",
               "WALLS": "WALLS"}
MARK_FAMILY = {"FOOTING": "FOOTINGS", "COLUMN": "COLUMNS", "GROUND_BEAM": "GROUND_BEAMS", "STRAP_BEAM": "GROUND_BEAMS",
               "CONTINUOUS_BEAM": "BEAMS", "BEAM": "BEAMS", "LINTEL": "BEAMS", "SLAB": "SLABS"}
SCHEDULED_FAMILIES = ("FOOTING", "COLUMN", "GROUND_BEAM", "STRAP_BEAM", "CONTINUOUS_BEAM", "BEAM", "LINTEL")

# a member section printed in a label: 'P.C 20x70', 'GB 30X60', 'PLANTED COL. 25 x 50', 'C3 (20x60)'
SECTION_LABEL = re.compile(r"^\s*(?P<prefix>[A-Z][A-Z0-9./ ]{0,20}?)\s*[(\[]?\s*(?P<a>\d{2,4})\s*[X*×]\s*(?P<b>\d{2,4})"
                           r"\s*(?:CM|MM)?\s*[)\]]?\s*$")
SECTION_PREFIX = {"PC": "PLANTED_COLUMN", "PLANTEDCOL": "PLANTED_COLUMN", "PLANTEDCOLUMN": "PLANTED_COLUMN",
                  "C": "COLUMNS", "COL": "COLUMNS", "COLUMN": "COLUMNS", "B": "BEAMS", "BEAM": "BEAMS", "RB": "BEAMS",
                  "GB": "GROUND_BEAMS", "TB": "GROUND_BEAMS", "SB": "GROUND_BEAMS", "L": "BEAMS", "LINTEL": "BEAMS",
                  "W": "WALLS", "WALL": "WALLS", "BW": "BOUNDARY_WALL", "RW": "WALLS"}
DEPENDENCY = re.compile(r"\b(?:AS\s*PER|FOLLOWS?|FOLLOWING|SEE|REFER(?:\s*TO)?|ACC(?:ORDING)?\.?\s*TO)\s*(?:THE\s*)?"
                        r"(?:ARCH(?:ITECT(?:URAL)?)?\.?|DETAILS?|SECTIONS?|DWGS?\.?|DRAWINGS?|SPEC(?:IFICATION)?S?|"
                        r"M\.?\s*E\.?\s*P\.?|SERVICES|SITE)\b|\bBY\s*(?:OTHERS|SPECIALISTS?)\b|"
                        r"\b(?:T\.\s*B\.\s*C\.?|TBC|TO\s*BE\s*CONFIRMED|VARIES|VARIABLE)\b")
THICKNESS = re.compile(r"\bT\s*=\s*(\d{2,3})\b|\b(\d{2,3})\s*(?:CM)\s*TH(?:ICK|K)\b|\b(\d{3})\s*(?:MM)?\s*TH(?:ICK|K)\b")
SHEET_RE = re.compile(r"\b(SH\d{2,3})\b")
COL_ID = re.compile(r"^(?:COL):(SH\d{2,3}):([^@|]*)@(-?\d+),(-?\d+)\|(.+)$")

SEVERITY = ("HIGH", "MEDIUM", "LOW", "INFO")
ACTION = {
    "PLAN_SHEET_NOT_MEASURED": "a plan with structural linework produced no item: check the sheet role / storey and "
                               "the edge layers, measure the storey",
    "DRAWN_NOT_MEASURED": "drawn on a structural plan, held by no item: identify the element (detail / section), "
                          "measure it or confirm it is not concrete",
    "MEMBER_DETECTED_NOT_ITEMIZED": "the route detected this member and no item holds it: bind its section or "
                                    "confirm it is not a member",
    "LABEL_NOT_CONSUMED": "a structural label no measured member uses: find its member (or confirm a duplicate "
                          "label) - a label is never silently dropped",
    "LABEL_MEMBER_CONFLICT": "the label sits on a member measured under another mark: confirm which mark governs",
    "SCHEDULED_NOT_PLACED": "a schedule type found on no plan: confirm the type is unused or locate its members",
    "PLACED_NOT_SCHEDULED": "a plan mark with no schedule row: obtain the section (RFI) - the member is held "
                            "unresolved",
    "SCHEDULE_ROW_UNREAD": "the schedule reader could not read a row: transcribe it or confirm it is not a type",
    "STOREY_PLAN_MISSING": "a storey with a height or a schedule band has no plan: obtain the plan - its members "
                           "are not measured",
    "STOREY_COLUMN_BANDS_MISSING": "a storey plan with columns and no column schedule band for it: obtain the "
                                   "sections of that storey's columns",
    "STOREY_HEIGHT_MISSING": "a plan storey without a height: columns of that storey cannot be measured",
    "COLUMN_PRESENCE_NOT_ITEMIZED": "a column drawn on this storey plan that no column item holds: bind its type "
                                    "and storey",
    "COLUMN_ITEM_WITHOUT_PRESENCE": "a column counted on a storey whose plan shows no column there: confirm the "
                                    "column exists on that storey (else it is over-counted)",
    "STAIR_NOT_MEASURED": "a stair flight / stair zone with no stair item: measure the flight (waist, risers, "
                          "landings) from its section",
    "COLUMN_BAND_NOT_ON_PLAN": "a schedule band names this storey but the plan shows no column there: confirm the "
                               "column stops (or is missing from the plan)",
    "REFERENCED_NOT_DRAWN": "a note names this element and no plan draws it: obtain its drawing or confirm it is "
                            "outside the scope",
    "DEPENDENCY": "the member's geometry depends on another document: obtain it (RFI) before releasing",
    "MEMBER_OVERLAP": "two measured footprints overlap on one plan: the overlap is counted twice unless one of them "
                      "is deducted",
    "OPENING_NOT_DEDUCTED": "an opening drawn inside a measured slab panel that the panel does not deduct: "
                            "confirm the opening and deduct it",
    "REGION_EXCLUDED": "a slab region the route excluded from the slabs: confirm what it is and measure it if it is "
                       "concrete",
    "SLAB_COVERAGE_LOW": "the slab plan's items hold a small share of the area it encloses: a cell may be open, a "
                         "large region taken as opening / detail - check the plan before using the slab total",
    "MEMBER_OUTLINE_SUSPECT": "a column mark bound to an outline far larger than its schedule section: the outline is "
                              "probably another element (pit, footing, detail) - confirm the column and that element",
    "UNRESOLVED_ITEMS": "items the route holds as UNRESOLVED: answer the blocker to release them",
    "HATCH_ON_MEASURED_MEMBER": "a patterned fill on a measured member marks that part as something its item may not "
                                "be (a cantilever portion, a step, a void, another material): read the legend / "
                                "section and confirm the item measures it as that",
}


class CompletenessError(ValueError):
    pass


# ====================================================================== small helpers
def _p(params):
    p = dict(PARAMS)
    p.update(params or {})
    return p


def _tokens(name):
    return [t for t in re.split(r"[^A-Z0-9]+", str(name).upper()) if t]


def _ascii(s, n=60):
    """a value safe to report: ASCII only (non-ASCII runs become '?'), trimmed."""
    s = re.sub(r"[^\x20-\x7E]+", "?", str(s or ""))
    return s[:n]


def annotation_layer(layer):
    if DI.role_guess(layer) in ANNOTATION_ROLES:
        return True
    return any(t in ANNOTATION_TOKENS for t in _tokens(layer))


# V2: a hatch is read on any layer except one that names text, dimensions, frames, grids, rebar or a table
HATCH_ANNOTATION_TOKENS = ANNOTATION_TOKENS - {"HATCH", "HAT"}


def hatch_drawn(layer):
    if DI.role_guess(layer) in ("TEXT", "DIMENSION", "FRAME", "GRID", "REBAR"):
        return False
    return not any(t in HATCH_ANNOTATION_TOKENS for t in _tokens(layer))


def footing_content_layer(layer):
    """V2: what a footing's footprint explains - its own lines and the column / neck drawn on it, nothing else."""
    return DI.role_guess(layer) in ("FOOTING", "COLUMN") or layer_family(layer) in ("FOOTINGS", "COLUMNS")


def layer_family(layer):
    """the family a layer name suggests, by token (exact for short tokens, prefix for long ones) - or None."""
    toks = _tokens(layer)
    best = None
    for fam, words in FAMILY_TOKENS.items():
        for w in words:
            for t in toks:
                if t == w or (len(w) >= 4 and t.startswith(w)):
                    if best is None or len(w) > best[1]:
                        best = (fam, len(w))
    return best[0] if best else None


def _note_words():
    """bilingual note vocabulary per family: the route's SCOPE_WORDS / the model's LABEL_WORDS (read, not copied)."""
    try:
        from engine.source import generic_route as GR
        scope = GR.SCOPE_WORDS
        en = GR.SCOPE_EN
    except Exception:                                     # pragma: no cover - the route is part of the engine
        scope, en = {}, {}
    words = defaultdict(set)
    for fam, ws in FAMILY_TOKENS.items():
        if fam in NOTE_FAMILIES:
            words[fam].update(w for w in ws if len(w) >= 4)
    remap = {"WALLS": "WALLS", "STAIRS": "STAIRS", "LIFT": "LIFT", "POOL": "POOL", "WATER_TANK": "WATER_TANK",
             "DOMES": "DOMES", "PARAPETS": "PARAPETS", "CANTILEVER_PORTIONS": "CANTILEVER"}
    latin = {f: sorted(ws, key=len, reverse=True) for f, ws in words.items()}
    for fam, ws in scope.items():
        f = remap.get(fam)
        if not f:
            continue
        for w in ws:
            if w.isascii():
                words[f].add(w)
                continue
            gloss = note_families(en.get(w, ""), latin) if en.get(w) else []
            words[gloss[0] if gloss else f].add(w)
    return {f: sorted(ws, key=len, reverse=True) for f, ws in words.items()}, en


def note_families(text, words):
    """families a note names (word boundaries for Latin words, substring for other scripts)."""
    u = DM.normalize(text).upper()
    out = []
    for fam, ws in words.items():
        for w in ws:
            wu = w.upper()
            if wu.isascii():
                if re.search(r"(?<![A-Z])" + re.escape(wu) + r"(?![A-Z])", u):
                    out.append(fam)
                    break
            elif wu in u:
                out.append(fam)
                break
    if "BOUNDARY_WALL" in out and "WALLS" in out:
        out.remove("WALLS")
    return out


def section_label(text):
    """('PLANTED_COLUMN', a, b, prefix) for a member-section label, else None."""
    u = DM.normalize(text).upper()
    m = SECTION_LABEL.match(u)
    if not m:
        return None
    pre = re.sub(r"[^A-Z]", "", m.group("prefix"))
    fam = SECTION_PREFIX.get(pre)
    if fam is None:
        mf, _ = DM.mark_family(m.group("prefix").strip())
        fam = MARK_FAMILY.get(mf)
    if fam is None:
        return None
    return fam, int(m.group("a")), int(m.group("b")), pre


def thickness_m(text):
    m = THICKNESS.search(DM.normalize(text).upper())
    if not m:
        return None
    if m.group(1):
        return int(m.group(1)) / 100.0
    if m.group(2):
        return int(m.group(2)) / 100.0
    return int(m.group(3)) / 1000.0


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _union_box(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _grow(b, d):
    return (b[0] - d, b[1] - d, b[2] + d, b[3] + d)


def _boxes_touch(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _in_box(b, x, y):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def _seg_dist(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _signed_area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2.0


def _fid(kind, *parts):
    h = hashlib.sha256("|".join([kind] + [str(x) for x in parts]).encode()).hexdigest()[:10]
    return f"CC-{h}"


class _Grid:
    """a uniform grid over boxes (edges or polygons): candidates near a point."""

    def __init__(self, cell):
        self.cell = max(cell, 1e-9)
        self.cells = defaultdict(list)

    def _keys(self, b):
        c = self.cell
        for i in range(int(math.floor(b[0] / c)), int(math.floor(b[2] / c)) + 1):
            for j in range(int(math.floor(b[1] / c)), int(math.floor(b[3] / c)) + 1):
                yield (i, j)

    def add(self, b, obj):
        for k in self._keys(b):
            self.cells[k].append(obj)

    def near(self, x, y, r=0.0):
        seen, out = set(), []
        for k in self._keys((x - r, y - r, x + r, y + r)):
            for o in self.cells.get(k, ()):
                if id(o) not in seen:
                    seen.add(id(o))
                    out.append(o)
        return out


# ====================================================================== context
def _plan_sheets(D):
    return [(sid, rec) for sid, rec in sorted(D["sheets"].items()) if rec["sheet"]["role"] in PLAN_ROLES]


def _sheet_texts(D, sid):
    return [t for t in D["model"]["texts"] if t.get("sheet") == sid]


def _members(D):
    """every detected member with a footprint, per sheet: {sid: [{kind, mid, poly|box, family, mark, ...}]}."""
    out = defaultdict(list)
    for sid, rec in _plan_sheets(D):
        role = rec["sheet"]["role"]
        for b in rec.get("bands", []) or []:
            beam = next((x for x in rec.get("beams", []) if x.get("band_id") == b["band_id"]), {})
            fam = "GROUND_BEAMS" if role == "GROUND_BEAM_PLAN" else "BEAMS"
            out[sid].append({"kind": "BAND", "mid": b["band_id"], "poly": b["polygon"], "family": fam,
                             "mark": beam.get("mark"), "depth_m": beam.get("depth_m"), "parent": b.get("parent"),
                             "state": beam.get("state") or b.get("state")})
        for b in ((rec.get("straps") or {}).get("bands") or []):
            out[sid].append({"kind": "BAND", "mid": b["band_id"], "poly": b["polygon"], "family": "GROUND_BEAMS",
                             "mark": b.get("mark"), "depth_m": b.get("depth_m"), "parent": b.get("parent"),
                             "state": b.get("state"), "strap": True})
        for b in ((rec.get("straps") or {}).get("unbound_candidates") or []):
            out[sid].append({"kind": "STRAP_CANDIDATE", "mid": b["band_id"], "poly": b["polygon"],
                             "family": "GROUND_BEAMS", "mark": None, "state": "UNBOUND_CANDIDATE"})
        for f in ((rec.get("slab") or {}).get("faces") or []):
            out[sid].append({"kind": "FACE", "mid": f["face_id"], "poly": f["polygon"], "holes": f.get("hole_polygons")
                             or [], "family": "SLABS", "cls": f.get("class"), "region": f.get("region"),
                             "area_m2": f.get("area_m2"), "t_m": f.get("t_m"), "volume_m3": f.get("volume_m3")})
        boxes = set()
        for key in ("slab_column_boxes", "column_presence", "column_boxes"):
            for bx in rec.get(key, []) or []:
                boxes.add(tuple(bx))
        for c in rec.get("columns", []) or []:
            if c.get("box"):
                out[sid].append({"kind": "COLUMN", "mid": c["member_id"], "box": tuple(c["box"]),
                                 "poly": MD.box_poly(c["box"]), "family": "COLUMNS", "mark": c.get("mark"),
                                 "suspect": _column_outline_suspect(c)})
                boxes.discard(tuple(c["box"]))
        for bx in sorted(boxes):
            out[sid].append({"kind": "COLUMN_BOX", "mid": "BOX@" + ",".join(f"{v:.0f}" for v in bx), "box": bx,
                             "poly": MD.box_poly(bx), "family": "COLUMNS", "mark": None})
        for ft in rec.get("footings", []) or []:
            poly = ft.get("polygon") or (MD.box_poly(ft["box"]) if ft.get("box") else None)
            approx = False
            if poly is None and ft.get("mark_at") and ft.get("schedule_m"):
                s = max(ft["schedule_m"][0], ft["schedule_m"][1]) * 0.6 / D["unit_m"]
                x, y = ft["mark_at"]
                poly, approx = MD.box_poly((x - s, y - s, x + s, y + s)), True
            if poly is not None:
                out[sid].append({"kind": "FOOTING", "mid": ft["member_id"], "poly": poly, "family": "FOOTINGS",
                                 "mark": ft.get("mark"), "approx": approx, "state": ft.get("state")})
    return out


def _column_outline_suspect(c):
    """the outline a column mark was bound to is more than twice the area of every section its schedule prints
    (a lift pit, a footing or a detail taken for the column): that outline explains nothing."""
    row = c.get("row") or {}
    dr = c.get("drawn_m")
    if not dr:
        return False
    secs = [b["dims_m"] for b in list((row.get("by_storey") or {}).values()) + [{"dims_m": row.get("dims_m") or {}}]
            if (b.get("dims_m") or {}).get("W") and (b.get("dims_m") or {}).get("H")]
    if not secs:
        return False
    return dr[0] * dr[1] > 2.0 * max(d["W"] * d["H"] for d in secs)


def _consumption(D, items, members):
    """which detected member each concrete item holds: {(sid, mid): {"items": [...], "cats": set, "base": x}}."""
    by_sheet_storey = defaultdict(list)
    for sid, rec in _plan_sheets(D):
        by_sheet_storey[rec["sheet"]["storey"]].append(sid)
    ids = {}
    for sid, ms in members.items():
        for m in ms:
            ids.setdefault(m["mid"], []).append((sid, m))
    used = defaultdict(lambda: {"items": [], "cats": set(), "base": 0.0, "exp_high": 0.0})
    for it in items:
        if it["trade"] != "CONCRETE":
            continue
        cid = it["component_id"]
        src_sheets = set(SHEET_RE.findall(it.get("source") or ""))
        cand = set()
        for tok in re.split(r"[:|]", cid):
            for sid, m in ids.get(tok, ()):
                cand.add((sid, m["mid"]))
        for mid, lst in ids.items():                     # footing / column member ids are whole prefixes
            if mid.startswith(("FTG:", "COL:")) and (cid == mid or cid.startswith(mid + "|") or cid.endswith(mid) or
                                                     (":" + mid) in cid):
                for sid, m in lst:
                    cand.add((sid, m["mid"]))
        if len(cand) > 1 and src_sheets:
            cand = {c for c in cand if c[0] in src_sheets} or cand
        if len(cand) > 1:
            st = it.get("storey")
            cand = {c for c in cand if c[0] in by_sheet_storey.get(st, ())} or cand
        for c in cand:
            u = used[c]
            u["items"].append(it["item_id"])
            u["cats"].add(it["category"])
            u["base"] += it.get("base") or 0.0
            u["exp_high"] += it.get("exposure_high") or 0.0
    used["__items__"] = list(items)
    return used


# ====================================================================== GEOMETRY ledger
def _entities(D, intake, sid):
    """the sheet's drawn entities as sample points: segments, arcs, circles, hatch rings."""
    box = D["model"]["sheets"][[s["sheet_id"] for s in D["model"]["sheets"]].index(sid)]["box"]
    inb = lambda p: _in_box(box, p[0], p[1])                         # noqa: E731
    out = []
    for s in intake.get("segments", []):
        if inb(s["a"]) and inb(s["b"]):
            a, b = tuple(s["a"]), tuple(s["b"])
            out.append({"eid": s["id"], "type": "LINE", "layer": s["layer"], "a": a, "b": b,
                        "pts": [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in (0, .25, .5, .75, 1)],
                        "len": math.dist(a, b), "box": _bbox([a, b])})
    for a in intake.get("arcs", []):
        if inb(a["s"]) and inb(a["e"]):
            pts = [tuple(a["s"]), tuple(a["m"]), tuple(a["e"])]
            sweep = _arc_sweep(a)
            out.append({"eid": a["id"], "type": "ARC", "layer": a["layer"], "c": tuple(a["c"]), "r": a["r"],
                        "pts": pts, "len": a["r"] * sweep, "sweep": sweep, "box": _bbox(pts)})
    for c in intake.get("circles", []):
        cx, cy = c["c"][0], c["c"][1]
        if inb((cx, cy)):
            r = c["r"]
            pts = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
            out.append({"eid": c["id"], "type": "CIRCLE", "layer": c["layer"], "c": (cx, cy), "r": r, "pts": pts,
                        "len": 2 * math.pi * r, "box": (cx - r, cy - r, cx + r, cy + r)})
    for h in intake.get("hatches", []):
        ring = [tuple(p[:2]) for p in (h.get("ring") or [])]
        if len(ring) >= 3 and all(inb(p) for p in ring):
            out.append({"eid": h["id"], "type": "HATCH", "layer": h["layer"], "ring": ring, "pts": ring[:8],
                        "len": 0.0, "area": abs(_signed_area(ring)), "box": _bbox(ring),
                        "pattern": _ascii(h.get("pattern"), 20)})
    return out


def _arc_sweep(a):
    """the arc's sweep from start / mid / end (radians, 0 .. 2 pi)."""
    cx, cy = a["c"][0], a["c"][1]
    ang = lambda p: math.atan2(p[1] - cy, p[0] - cx)               # noqa: E731
    s, m, e = ang(a["s"]), ang(a["m"]), ang(a["e"])
    ccw = lambda x, y: (y - x) % (2 * math.pi)                     # noqa: E731
    sw = ccw(s, e)
    if ccw(s, m) > sw:                                               # the mid point is on the other side: clockwise
        sw = 2 * math.pi - sw
    return sw if sw > 1e-9 else 2 * math.pi


def _footprint_index(ms, tol):
    edges, solids = _Grid(max(tol * 30, 1.0)), _Grid(max(tol * 60, 1.0))
    for m in ms:
        if m.get("suspect"):
            continue
        rings = [m["poly"]] + list(m.get("holes") or [])
        for ring in rings:
            for i in range(len(ring)):
                a, b = tuple(ring[i]), tuple(ring[(i + 1) % len(ring)])
                edges.add(_grow(_bbox([a, b]), tol), (a, b, m))
        solid = m["kind"] in ("COLUMN", "COLUMN_BOX", "FOOTING", "BAND", "STRAP_CANDIDATE") or \
            (m["kind"] == "FACE" and (m.get("cls") in ("BEAM", "COLUMN", "DETAIL") or
                                      m.get("region") in ("STAIR_ZONE", "DETAIL")))
        # an UNRESOLVED cell explains none of what is drawn in it: its content (a stair, a pit) is the reason
        if solid:
            solids.add(_bbox(m["poly"]), m)
        for hole in m.get("holes") or []:                 # an opening inside a face: its cross lines are the opening's
            if len(hole) >= 3:
                solids.add(_bbox(hole), {"kind": "HOLE", "mid": m["mid"] + ":HOLE", "poly": hole})
    return edges, solids


def _explained_by(x, y, edges, solids, tol, layer=None):
    for a, b, m in edges.near(x, y, tol):
        if _seg_dist(x, y, a, b) <= tol:
            return m
    for m in solids.near(x, y, 0.0):
        if m["kind"] == "FOOTING" and layer is not None and not footing_content_layer(layer):
            continue                                   # V2: a pit / tank / wall drawn inside a footing is not it
        if MD.point_in_poly(x, y, m["poly"]):
            return m
    return None


def _clusters(ents, gap):
    """union-find of entities of one layer whose boxes come within `gap`."""
    parent = list(range(len(ents)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    g = _Grid(max(gap * 4, 1e-6))
    for i, e in enumerate(ents):
        g.add(_grow(e["box"], gap / 2), i)
    for i, e in enumerate(ents):
        b = _grow(e["box"], gap / 2)
        for j in g.near((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, max(b[2] - b[0], b[3] - b[1]) / 2 + gap):
            if j != i and ents[j]["layer"] == e["layer"] and _boxes_touch(b, _grow(ents[j]["box"], gap / 2)):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    groups = defaultdict(list)
    for i in range(len(ents)):
        groups[find(i)].append(ents[i])
    return list(groups.values())


def _loops(lines, eps):
    """closed loops among straight lines (components whose nodes all have degree 2), as vertex rings."""
    key = lambda p: (round(p[0] / eps), round(p[1] / eps))          # noqa: E731
    adj = defaultdict(list)
    pos = {}
    for k, ln in enumerate(lines):
        a, b = key(ln["a"]), key(ln["b"])
        if a == b:
            continue
        pos[a], pos[b] = ln["a"], ln["b"]
        adj[a].append((b, k))
        adj[b].append((a, k))
    seen, rings = set(), []
    for start in list(adj):
        if start in seen:
            continue
        comp, stack = [], [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            comp.append(n)
            stack.extend(m for m, _ in adj[n] if m not in seen)
        if len(comp) < 3 or any(len(adj[n]) != 2 for n in comp):
            continue
        ring, prev, cur = [comp[0]], None, comp[0]
        while True:
            nxt = [m for m, _ in adj[cur] if m != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == ring[0]:
                break
            ring.append(cur)
            if len(ring) > len(comp):
                break
        if len(ring) == len(comp):
            rings.append([pos[n] for n in ring])
    return rings


def _parallel_pairs(lines, wmin, wmax, min_overlap):
    """[(width, overlap length)] for pairs of parallel straight lines at a strip width."""
    out = []
    used = set()
    for i, a in enumerate(lines):
        if i in used:
            continue
        (ax, ay), (bx, by) = a["a"], a["b"]
        la = math.hypot(bx - ax, by - ay)
        if la <= 0:
            continue
        ux, uy = (bx - ax) / la, (by - ay) / la
        best = None
        for j, b in enumerate(lines):
            if j == i or j in used:
                continue
            (cx, cy), (dx, dy) = b["a"], b["b"]
            lb = math.hypot(dx - cx, dy - cy)
            if lb <= 0 or abs(ux * (dy - cy) / lb - uy * (dx - cx) / lb) > 0.035:
                continue
            w = abs((cx - ax) * uy - (cy - ay) * ux)
            if not (wmin <= w <= wmax):
                continue
            t = sorted([0.0, la])
            s0, s1 = sorted([(cx - ax) * ux + (cy - ay) * uy, (dx - ax) * ux + (dy - ay) * uy])
            ov = min(t[1], s1) - max(t[0], s0)
            if ov >= min_overlap and (best is None or w < best[0]):
                best = (w, ov, j)
        if best:
            used.update((i, best[2]))
            out.append((best[0], best[1]))
    return out


def _treads(lines, lo, hi, min_n=4):
    """a run of >= min_n parallel lines at a stair-tread spacing (the treads of a flight)."""
    if len(lines) < min_n:
        return None
    by_dir = defaultdict(list)
    for ln in lines:
        (ax, ay), (bx, by) = ln["a"], ln["b"]
        L = math.hypot(bx - ax, by - ay)
        if L <= 0:
            continue
        ang = round(math.degrees(math.atan2(by - ay, bx - ax)) % 180.0 / 2.0) * 2.0
        nx, ny = -(by - ay) / L, (bx - ax) / L
        by_dir[ang].append(((ax * nx + ay * ny), L))
    for ang, offs in by_dir.items():
        o = sorted(x for x, _ in offs)
        gaps = [b - a for a, b in zip(o, o[1:]) if b - a > 1e-9]
        good = [g for g in gaps if lo <= g <= hi]
        if len(good) + 1 >= min_n and len(good) >= 0.6 * max(len(gaps), 1):
            return {"n_treads": len(good) + 1, "going_m": sorted(good)[len(good) // 2]}
    return None


SHEET_PRIORITY = ("FOUNDATION_PLAN", "GROUND_BEAM_PLAN", "COLUMN_PLAN", "SLAB_PLAN")


def _sheet_group(role):
    """sheets that repeat each other's context: the substructure plans together, the slab plans together."""
    return "SLABS" if role == "SLAB_PLAN" else "SUBSTRUCTURE"


def _local_index(D, members, consumed, tol_m):
    """every plan sheet's MEASURED member footprints in sheet-local metres (sheets share local coordinates, as the
    route's column-presence check assumes), to recognise context drawn again on another sheet: exact edges of
    measured members (and column outlines), and per family the measured footprints (approximate ones included) for
    a group whose own layer / notes name that member family."""
    u = D["unit_m"]
    out = {}
    for sid, rec in _plan_sheets(D):
        o = rec["sheet"].get("origin") or (0.0, 0.0)
        exact, fam = [], defaultdict(list)
        for m in members.get(sid, []):
            if not (consumed.get((sid, m["mid"])) or m["kind"] == "COLUMN_BOX"):
                continue
            if m["kind"] == "FACE" and m.get("cls") != "PANEL":
                continue
            lm = dict(m, poly=[((x - o[0]) * u, (y - o[1]) * u) for x, y in m["poly"]], holes=[])
            if m["kind"] == "FACE":
                lm["kind"] = "FACE_EDGE"             # its boundary only: never its interior
            if not m.get("approx"):
                exact.append(lm)
            if m["kind"] in ("FOOTING", "COLUMN", "COLUMN_BOX", "BAND"):   # compact footprints only: a slab panel
                fam[m["family"]].append(dict(lm, kind="FAMILY_FOOTPRINT"))  # holds anything drawn inside it
        e_edges, e_sol = _footprint_index(exact, tol_m)
        fidx = {f: _footprint_index(ms, 0.3) for f, ms in fam.items()}
        for f, (ed, so) in fidx.items():
            for m in fam[f]:
                so.add(_bbox(m["poly"]), m)
        out[sid] = {"exact": (e_edges, e_sol), "family": fidx}
    return out


def items_of(consumed):
    return consumed.get("__items__", [])


def geometry_ledger(D, intake, members, consumed, p, notes_words):
    """signals: one row per drawn entity group; findings: unexplained groups, sheets with linework but no member."""
    u = D["unit_m"]
    tol = p["EXPLAIN_TOL_M"] / u
    signals, findings, stats = [], [], defaultdict(float)
    local = _local_index(D, members, consumed, p["EXPLAIN_TOL_M"])
    pending = []
    for sid, rec in _plan_sheets(D):
        sh = rec["sheet"]
        org = sh.get("origin") or (0.0, 0.0)
        ms = members.get(sid, [])
        ents = _entities(D, intake, sid)
        p.setdefault("_ents", {})[sid] = ents
        drawn = [e for e in ents if (hatch_drawn(e["layer"]) if e["type"] == "HATCH" else
                                     not annotation_layer(e["layer"]))]
        stats["entities"] += len(ents)
        stats["annotation_entities"] += len(ents) - len(drawn)
        if not ms:
            ln = sum(e["len"] for e in drawn) * u
            if ln >= 5.0:
                findings.append(_finding(
                    "PLAN_SHEET_NOT_MEASURED", sid, sh, None, "HIGH", family=None, confidence="HIGH",
                    evidence=f"{len(drawn)} non-annotation entities, {ln:.1f} m of linework; no member detected",
                    magnitude={"linework_m": round(ln, 2)}))
            continue
        plan_box = None
        for m in ms:
            plan_box = _union_box(plan_box, _bbox(m["poly"]))
        plan_area = _grow(plan_box, p["PLAN_MARGIN_M"] / u)
        bldg = [m for m in ms if m["kind"] == "FACE"] or ms
        edges, solids = _footprint_index(ms, tol)
        texts = _sheet_texts(D, sid)
        tg = _Grid(max(p["TEXT_NEAR_M"] / u, 1e-6))
        for t in texts:
            tg.add((t["x"], t["y"], t["x"], t["y"]), t)
        unexplained = []
        if not any(i["trade"] == "CONCRETE" and i["family"] == "STAIRS" for i in items_of(consumed)):
            for m in ms:
                if m["kind"] != "FACE" or not (m.get("cls") == "OPENING" or m.get("region") == "OPENING"):
                    continue
                inside = [e for e in drawn if e["type"] == "LINE" and
                          MD.point_in_poly((e["a"][0] + e["b"][0]) / 2, (e["a"][1] + e["b"][1]) / 2, m["poly"])]
                tr = _treads(inside, p["STAIR_TREAD_M"][0] / u, p["STAIR_TREAD_M"][1] / u)
                if tr:
                    findings.append(_finding(
                        "STAIR_NOT_MEASURED", sid, sh, _local_box(_bbox(m["poly"]), org, u), "HIGH", family="STAIRS",
                        confidence="HIGH", evidence=f"{tr['n_treads']} treads at {tr['going_m'] * u:.2f} m drawn "
                                                    f"inside opening {m['mid']} ({m.get('area_m2') or 0:.2f} m2): a "
                                                    "flight in the stair well; no stair item",
                        magnitude={"n_treads": tr["n_treads"], "going_m": round(tr["going_m"] * u, 3),
                                   "opening_m2": round(m.get("area_m2") or 0, 3)}, refs=m["mid"]))
        group_of = {osid: _sheet_group(orec["sheet"]["role"]) for osid, orec in _plan_sheets(D)}
        opening_own = _opening_symbols(ms, drawn, u, p)
        fills = [e for e in drawn if e["type"] == "HATCH"]
        col_fill = _column_fill(fills, solids, p["EXPLAINED_SHARE"])
        legend, swatches = _legend_swatches([e for e in ents if e["type"] == "HATCH"], ms, texts, notes_words, u, p)
        mgrid = _Grid(max(5.0 / u, 1e-6))
        for m in ms:
            mgrid.add(_bbox(m["poly"]), m)
        held = lambda m: bool(consumed.get((sid, m["mid"]))) or m["kind"] == "COLUMN_BOX"     # noqa: E731
        hatched = []
        for e in drawn:
            stats["drawn_entities"] += 1
            stats["drawn_length_m"] += e["len"] * u
            if id(e) in opening_own:
                e["state"] = "EXPLAINED_BY_OPENING"
                stats["explained_length_m"] += e["len"] * u
                continue
            if not any(_in_box(plan_area, x, y) for x, y in e["pts"]):
                e["state"] = "OUTSIDE_PLAN_AREA"
                stats["outside_plan_length_m"] += e["len"] * u
                continue
            if e["type"] == "HATCH":
                stats["fills"] += 1
                if id(e) in swatches:
                    e["state"] = "LEGEND_SWATCH"
                    continue
                pts = _hatch_samples(e)
                lay = e["layer"]
                own = (e["pattern"] in col_fill["patterns"] or lay in col_fill["layers"]) if col_fill else \
                    e["pattern"] in ("SOLID", "")
                sol, _ = _share_in(pts, solids, lambda m: m["kind"] != "FOOTING" or footing_content_layer(lay))
                incol = _share_in(pts, solids, lambda m: m["kind"] in ("COLUMN", "COLUMN_BOX") and
                                  not m.get("suspect"))[0] if col_fill is None else 0.0
                if (own and sol >= p["EXPLAINED_SHARE"]) or incol >= p["EXPLAINED_SHARE"]:
                    e["state"] = "EXPLAINED_BY_MEMBER"
                    stats["fills_explained"] += 1
                    continue
                on, hit = _share_in(pts, mgrid, held)
                if on >= p["HATCH_ON_MEMBER_SHARE"]:
                    e["state"] = "HATCH_ON_MEASURED_MEMBER"
                    hatched.append((e, hit))
                    continue
                e["state"] = "UNEXPLAINED"
                unexplained.append(e)
                continue
            ok = _explained_share(e, edges, solids, tol)
            if ok >= p["EXPLAINED_SHARE"]:
                e["state"] = "EXPLAINED_BY_MEMBER"
                stats["explained_length_m"] += e["len"] * u
                continue
            # context drawn again from another sheet of the same level group (footings on the ground-beam plan, a
            # lower roof outline on the roof plan): exact edges of measured members only, entity by entity
            lp = [((x - org[0]) * u, (y - org[1]) * u) for x, y in e["pts"]]
            for osid, idx in local.items():
                if osid == sid or group_of[osid] != group_of[sid]:
                    continue
                oe, osol = idx["exact"]
                if sum(1 for x, y in lp if _explained_by(x, y, oe, osol, p["EXPLAIN_TOL_M"], e["layer"])) / \
                        len(lp) >= p["EXPLAINED_SHARE"]:
                    e["state"] = "CONTEXT_OF_OTHER_SHEET"
                    e["context_of"] = osid
                    break
            if e.get("state") == "CONTEXT_OF_OTHER_SHEET":
                stats["context_length_m"] += e["len"] * u
                continue
            e["state"] = "UNEXPLAINED"
            unexplained.append(e)
        curves = [e for e in drawn if e["type"] in ("CIRCLE", "ARC")]
        outside = [e for e in drawn if e.get("state") == "OUTSIDE_PLAN_AREA" and e["type"] == "LINE"]
        unexplained = _split_outline_loops(unexplained, plan_box, u, signals, sid, sh, org, outside)
        here = []
        for grp in _clusters(unexplained, p["CLUSTER_GAP_M"] / u):
            lpts = [((x - org[0]) * u, (y - org[1]) * u) for e in grp for x, y in e["pts"]]
            sig, fnd = _describe_group(D, sid, sh, org, grp, ms, bldg, tg, p, notes_words, u, consumed, curves,
                                       plan_box)
            ctx = None
            if sig["FAMILY_GUESS"] in MEMBER_FAMILIES:     # a member family's outline repeated from its own plan
                for osid, idx in local.items():
                    if osid == sid or sig["FAMILY_GUESS"] not in idx["family"]:
                        continue
                    fe, fs = idx["family"][sig["FAMILY_GUESS"]]
                    if sum(1 for x, y in lpts if _explained_by(x, y, fe, fs, 0.3)) / len(lpts) >= \
                            p["EXPLAINED_SHARE"]:
                        ctx = osid
                        break
            if ctx:
                sig["STATE"] = "CONTEXT_OF_OTHER_SHEET"
                sig["CONTEXT_OF"] = ctx
                stats["context_length_m"] += sig["LINEWORK_M"]
                signals.append(sig)
                continue
            here.append((sid, sh, sig, fnd, grp))
        by_mid = {m["mid"]: m for m in ms}
        for e, hit in hatched:
            here.append((sid, sh) + _hatch_on_member(D, sid, sh, org, e, hit, by_mid, consumed, legend, tg, p,
                                                     notes_words, u) + ([e],))
        pending.extend(x[:4] for x in _merge_fills(here, signals, u))
    # the same drawing repeated on several sheets (plot line, boundary wall, a lower roof outline): one finding
    order = {sid: (SHEET_PRIORITY.index(rec["sheet"]["role"]), STOREY_ORDER.index(rec["sheet"]["storey"])
                   if rec["sheet"]["storey"] in STOREY_ORDER else 99, sid) for sid, rec in _plan_sheets(D)}
    pending.sort(key=lambda x: order[x[0]])
    kept = []
    for sid, sh, sig, fnd in pending:
        own = sig["STATE"] == "HATCH_ON_MEASURED_MEMBER" and sh["role"] == "SLAB_PLAN"     # V2: per storey member
        twin = next((k for k in kept if k[2]["LAYER"] == sig["LAYER"] and not (
            own and (k[1]["role"] != "SLAB_PLAN" or k[1].get("storey") != sh.get("storey"))) and (
            (k[2]["SHAPE"] == sig["SHAPE"] and all(abs(a - b) <= 0.3 for a, b in zip(k[2]["BOX_M"], sig["BOX_M"])) and
             abs(k[2]["LINEWORK_M"] - sig["LINEWORK_M"]) <= 0.05 * max(k[2]["LINEWORK_M"], 1e-9)) or
            (k[2]["FAMILY_GUESS"] == sig["FAMILY_GUESS"] != "UNKNOWN" and (
                _iou(k[2]["BOX_M"], sig["BOX_M"]) >= 0.7 or _inside_box(sig["BOX_M"], _grow(k[2]["BOX_M"], 0.3)))))),
                    None)
        if twin:
            sig["STATE"] = "REPEATED_ON_OTHER_SHEET"
            sig["CONTEXT_OF"] = twin[0]
            twin[2].setdefault("REPEATED_ON", []).append(sid)
            if twin[3] is not None:
                twin[3]["EVIDENCE"] += f"; drawn again on {sid}"
            stats["repeated_length_m"] += sig["LINEWORK_M"]
            signals.append(sig)
            continue
        kept.append((sid, sh, sig, fnd))
        signals.append(sig)
        stats[sig["STATE"].lower() + "_groups"] += 1
        if fnd:
            findings.append(fnd)
            stats["unexplained_length_m"] += sig["LINEWORK_M"]
        else:
            stats["minor_length_m"] += sig["LINEWORK_M"]
    for sig in signals:
        if isinstance(sig.get("REPEATED_ON"), list):
            sig["REPEATED_ON"] = ",".join(sig["REPEATED_ON"])
    return signals, findings, dict(stats)


def _inside_box(a, b):
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = max((a[2] - a[0]) * (a[3] - a[1]), 1e-9) + max((b[2] - b[0]) * (b[3] - b[1]), 1e-9) - inter
    if inter == 0.0:                                   # thin boxes (a line): compare the extents instead
        return 1.0 if all(abs(x - y) <= 0.3 for x, y in zip(a, b)) else 0.0
    return inter / ua


def _merge_fills(here, signals, u):
    """V2: a fill bounded by another unexplained group of the same sheet (a pool or pit outline and its hatch, a
    block fill along a wall strip) is that group's fill - evidence on its finding, not a second finding: the fill
    lies in the group's box (at most four times the fill's) and half its boundary runs within 0.3 m of the group's
    lines. A fill round the whole plan is never another group's fill."""
    area = lambda b: max((b[2] - b[0]) * (b[3] - b[1]), 1e-9)                # noqa: E731

    def bounded(fill_grp, grp):
        pts = []
        for h in fill_grp:
            if h["type"] == "HATCH":
                k = len(h["ring"])
                pts += list(h["ring"]) + [((h["ring"][i][0] + h["ring"][(i + 1) % k][0]) / 2,
                                           (h["ring"][i][1] + h["ring"][(i + 1) % k][1]) / 2) for i in range(k)]
        lines = [e for e in grp if e["type"] != "HATCH"]
        return pts and lines and sum(1 for x, y in pts if _dist_to_group(x, y, lines) * u <= 0.3) >= 0.5 * len(pts)
    hosts = [x for x in here if x[2]["SHAPE"] != "HATCH_REGION" and x[3] is not None]
    keep = []
    for x in here:
        sig = x[2]
        if sig["SHAPE"] == "HATCH_REGION" and sig["STATE"] != "SITE_FILL":
            big = next((h for h in hosts if _inside_box(sig["BOX_M"], _grow(h[2]["BOX_M"], 0.3)) and
                        area(h[2]["BOX_M"]) <= 4.0 * area(sig["BOX_M"]) and bounded(x[4], h[4])), None)
            if big:
                mag = sig["MAGNITUDE"]
                pat = ",".join(mag.get("patterns") or [mag.get("pattern") or "fill"])
                sig["STATE"] = "FILL_OF_DRAWN_GROUP"
                sig["CONTEXT_OF"] = big[2]["LAYER"]
                big[3]["EVIDENCE"] += f"; filled ({sig['LAYER']} {pat}, {mag.get('hatch_area_m2', 0):.2f} m2)"
                big[3]["MAGNITUDE"] = dict(big[3]["MAGNITUDE"], fill_m2=mag.get("hatch_area_m2"))
                signals.append(sig)
                continue
        keep.append(x)
    return keep


def _opening_symbols(ms, drawn, u, p):
    """ids of the lines an opening face owns: its X (two diagonals crossing) and the treads of a flight in it."""
    own = set()
    for m in ms:
        if m["kind"] != "FACE" or not (m.get("cls") == "OPENING" or m.get("region") == "OPENING"):
            continue
        inside = [e for e in drawn if e["type"] == "LINE" and
                  MD.point_in_poly((e["a"][0] + e["b"][0]) / 2, (e["a"][1] + e["b"][1]) / 2, m["poly"])]
        box = _bbox(m["poly"])
        diag = math.hypot(box[2] - box[0], box[3] - box[1])
        for e in inside:
            dx, dy = e["b"][0] - e["a"][0], e["b"][1] - e["a"][1]
            ang = abs(math.degrees(math.atan2(dy, dx))) % 90.0
            if e["len"] >= 0.5 * diag and 15.0 <= ang <= 75.0:
                own.add(id(e))
        by_layer = defaultdict(list)
        for e in inside:
            by_layer[e["layer"]].append(e)
        for lay, ls in by_layer.items():
            if _treads(ls, p["STAIR_TREAD_M"][0] / u, p["STAIR_TREAD_M"][1] / u):
                own.update(id(e) for e in ls)
    return own


def _split_outline_loops(ents, plan_box, u, signals, sid, sh, org, outside=()):
    """closed loops of one layer that enclose every measured member of the sheet are the plot / building outline:
    they are recorded once and taken out, so that a wall strip drawn along the plot line is described alone."""
    by_layer = defaultdict(list)
    for e in list(ents) + list(outside):             # a plot line may run beyond the plan area: its loop still closes
        if e["type"] == "LINE":
            by_layer[e["layer"]].append(e)
    drop, extra = set(), []
    corners = ((plan_box[0], plan_box[1]), (plan_box[2], plan_box[1]), (plan_box[2], plan_box[3]),
               (plan_box[0], plan_box[3]))
    for lay, lines in by_layer.items():
        for ring in _loops(lines, 0.002 / u):
            if not all(MD.point_in_poly(x, y, ring) for x, y in corners):
                continue
            ids = set()
            for ln in lines:
                if any(math.dist(ln["a"], q) <= 0.002 / u for q in ring) and \
                        any(math.dist(ln["b"], q) <= 0.002 / u for q in ring):
                    ids.add(id(ln))
            drop |= ids
            keep = []
            for i in range(len(ring)):
                a, b = ring[i], ring[(i + 1) % len(ring)]
                edge = {"a": a, "b": b}
                rest = [ln for ln in lines if id(ln) not in ids]
                if rest and _parallel_pairs([edge] + rest, 0.08 / u, 0.8 / u, 0.5 / u):
                    keep.append({"eid": f"PLOT_EDGE:{i}", "type": "LINE", "layer": lay, "a": a, "b": b,
                                 "pts": [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in
                                         (0, .25, .5, .75, 1)], "len": math.dist(a, b), "box": _bbox([a, b]),
                                 "state": "UNEXPLAINED"})
            extra.extend(keep)
            signals.append({"LEDGER": "GEOMETRY", "SHEET": sid, "STOREY": sh.get("storey"), "LAYER": _ascii(lay, 40),
                            "SHAPE": "CLOSED_AREA", "N_ENTITIES": len(ids), "STATE": "PLOT_OR_OUTLINE",
                            "LINEWORK_M": round(sum(math.dist(q, ring[(i + 1) % len(ring)]) for i, q in
                                                    enumerate(ring)) * u, 3),
                            "BOX_M": _local_box(_bbox(ring), org, u), "POSITION": "AROUND_BUILDING",
                            "FAMILY_GUESS": layer_family(lay) or "UNKNOWN", "CONFIDENCE": "LOW", "KEYWORDS": "",
                            "MARKS_NEAR": "", "MAGNITUDE": {"area_m2": round(abs(_signed_area(ring)) * u * u, 3)},
                            "CANDIDATES": "", "ENTITY_IDS": ""})
    return [e for e in ents if id(e) not in drop] + extra


# ---------------------------------------------------------------------- V2 hatches
def _hatch_samples(e, n=6):
    """sample points of a fill: a grid inside its ring; a thin fill (a strip) adds its vertices and edge midpoints."""
    if "samples" in e:
        return e["samples"]
    ring, b = e["ring"], e["box"]
    pts = []
    for i in range(n):
        for j in range(n):
            x = b[0] + (b[2] - b[0]) * (i + 0.5) / n
            y = b[1] + (b[3] - b[1]) * (j + 0.5) / n
            if MD.point_in_poly(x, y, ring):
                pts.append((x, y))
    if len(pts) < 4:
        k = len(ring)
        pts += list(ring) + [((ring[i][0] + ring[(i + 1) % k][0]) / 2, (ring[i][1] + ring[(i + 1) % k][1]) / 2)
                             for i in range(k)]
    e["samples"] = pts
    return pts


def _share_in(pts, grid, keep):
    """share of the points inside a member of the grid that keep(m) accepts, and the member ids hit."""
    hit = Counter()
    for x, y in pts:
        cand = [m for m in grid.near(x, y, 0.0) if keep(m) and MD.point_in_poly(x, y, m["poly"])]
        if cand:
            cand.sort(key=lambda m: (m["kind"] == "FACE", m["mid"]))      # a band / column / footing before a face
            hit[cand[0]["mid"]] += 1
    return (sum(hit.values()) / len(pts) if pts else 0.0), hit


def _column_fill(hatches, solids, share):
    """the fill this plan uses for its column sections: patterns / layers of fills lying inside column outlines
    (at least two fills and a quarter of them), or None when no fill lies in a column."""
    col = lambda m: m["kind"] in ("COLUMN", "COLUMN_BOX") and not m.get("suspect")        # noqa: E731
    pc, lc, n = Counter(), Counter(), 0
    for h in hatches:
        sh, _ = _share_in(_hatch_samples(h), solids, col)
        if sh >= share:
            n += 1
            pc[h["pattern"]] += 1
            lc[h["layer"]] += 1
    if not n:
        return None
    return {"patterns": {k for k, v in pc.items() if v >= 2 and v >= 0.25 * n},
            "layers": {k for k, v in lc.items() if v >= 2 and v >= 0.25 * n}}


def _legend_swatches(hatches, ms, texts, words, u, p):
    """a legend swatch: a small fill off the building, another fill of the same pattern and layer elsewhere on the
    sheet, and a short note beside it naming one family. -> ({(pattern, layer): (family, note)}, swatch ids)."""
    bb = None
    for m in ms:
        bb = _union_box(bb, _bbox(m["poly"]))
    out, ids = {}, set()
    for h in hatches:
        if h["area"] * u * u > p["LEGEND_SWATCH_MAX_M2"] or bb is None:
            continue
        cx, cy = (h["box"][0] + h["box"][2]) / 2, (h["box"][1] + h["box"][3]) / 2
        if _in_box(bb, cx, cy):
            continue
        if not any(o is not h and o["pattern"] == h["pattern"] and o["layer"] == h["layer"] for o in hatches):
            continue
        votes, note = Counter(), None
        for t in texts:
            if len(t["norm"]) > p["DEPENDENCY_NOTE_MAX_CHARS"] or section_label(t["norm"]):
                continue
            if _dist_to_group(t["x"], t["y"], [h]) * u <= p["LEGEND_TEXT_M"]:
                for f in note_families(t["norm"], words):
                    votes[f] += 1
                    note = note or t
        if votes:
            ranked = votes.most_common()
            if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
                out[(h["pattern"], h["layer"])] = (ranked[0][0], _ascii(note["norm"], 30))
                ids.add(id(h))
    return out, ids


HATCH_CANDIDATES = {"SLABS": ("CANTILEVER", "SLAB_STEP", "OPENING"), "SUBSTRUCTURE": ("LIFT", "WATER_TANK",
                                                                                       "SLAB_STEP")}


def _hatch_on_member(D, sid, sh, org, e, hit, by_mid, consumed, legend, tg, p, words, u):
    """HATCH_ON_MEASURED_MEMBER: a fill that is not the column fill, lying on measured members."""
    hosts = [by_mid[k] for k, _ in hit.most_common() if k in by_mid]
    host = hosts[0]
    a = e["area"] * u * u
    box = _local_box(e["box"], org, u)
    near = []
    r = p["TEXT_NEAR_M"] / u
    gb = _grow(e["box"], r)
    for t in tg.near((gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2, max(gb[2] - gb[0], gb[3] - gb[1]) / 2 + r):
        if len(t["norm"]) <= p["DEPENDENCY_NOTE_MAX_CHARS"] and not section_label(t["norm"]) and \
                _dist_to_group(t["x"], t["y"], [e]) <= r:
            near.append(t)
    kw = sorted({f for t in near for f in note_families(t["norm"], words)})
    leg = legend.get((e["pattern"], e["layer"]))
    group = _sheet_group(sh["role"])
    fam, conf, cands = None, "LOW", ()
    if leg:
        fam, conf = leg[0], "HIGH"
    elif len(kw) == 1:
        fam, conf = kw[0], "MEDIUM"
    else:
        cands = tuple(kw) or HATCH_CANDIDATES.get(group, HATCH_CANDIDATES["SLABS"])
    items = []
    for hm in hosts:
        items += (consumed.get((sid, hm["mid"])) or {}).get("items", [])
    marks = sorted({str(hm.get("mark")) for hm in hosts if hm.get("mark")})
    held = f"{host['kind'].lower()} {host['mid']}" + (f" (measured as {', '.join(marks)})" if marks else "")
    ev = (f"layer {_ascii(e['layer'], 40)}: a {e['pattern'] or 'fill'} fill of {a:.2f} m2 on {held}" +
          (f" and {len(hosts) - 1} more member(s)" if len(hosts) > 1 else "") +
          ("; not the plan's column fill" if host["kind"] in ("COLUMN", "COLUMN_BOX") else "") +
          (f"; legend: {leg[1]}" if leg else "") + (f"; notes: {', '.join(kw)}" if kw else "") +
          (f"; could be {' or '.join(cands)}" if cands else ""))
    mag = {"hatch_area_m2": round(a, 3), "pattern": e["pattern"], "host": host["mid"],
           "host_share": round(sum(hit.values()) / max(len(_hatch_samples(e)), 1), 3)}
    sig = {"LEDGER": "GEOMETRY", "SHEET": sid, "STOREY": sh.get("storey"), "LAYER": _ascii(e["layer"], 40),
           "SHAPE": "HATCH_REGION", "N_ENTITIES": 1, "LINEWORK_M": 0.0, "BOX_M": box, "POSITION": "ON_MEMBER",
           "FAMILY_GUESS": fam or "UNKNOWN", "CONFIDENCE": conf, "KEYWORDS": ",".join(kw),
           "MARKS_NEAR": ",".join(marks)[:80], "MAGNITUDE": mag, "CANDIDATES": "|".join(cands),
           "ENTITY_IDS": e["eid"], "STATE": "HATCH_ON_MEASURED_MEMBER", "MEMBER": host["mid"]}
    fnd = _finding("HATCH_ON_MEASURED_MEMBER", sid, sh, box, "MEDIUM", family=fam, confidence=conf, evidence=ev,
                   magnitude=mag, items=sorted(set(items)), refs=e["eid"], layer=e["layer"])
    return sig, fnd


def _explained_share(e, edges, solids, tol):
    if e["type"] == "CIRCLE":
        hit = next((m for m in solids.near(*e["c"]) if m["kind"] in ("COLUMN", "COLUMN_BOX") and
                    MD.point_in_poly(e["c"][0], e["c"][1], m["poly"])), None)
        return 1.0 if hit else sum(1 for x, y in e["pts"] if _explained_by(x, y, edges, solids, tol, e["layer"])) / 4.0
    return sum(1 for x, y in e["pts"] if _explained_by(x, y, edges, solids, tol, e["layer"])) / len(e["pts"])


def _describe_group(D, sid, sh, org, grp, ms, bldg, tg, p, words, u, consumed=None, curves=(),
                    plan_box=None):
    layer = grp[0]["layer"]
    box = None
    for e in grp:
        box = _union_box(box, e["box"])
    ext = max(box[2] - box[0], box[3] - box[1]) * u
    lines = [e for e in grp if e["type"] == "LINE"]
    arcs = [e for e in grp if e["type"] == "ARC"]
    circles = [e for e in grp if e["type"] == "CIRCLE"]
    hatches = [e for e in grp if e["type"] == "HATCH"]
    linework = sum(e["len"] for e in grp) * u
    loops = _loops(lines, 0.002 / u)
    areas = sorted((abs(_signed_area(r)) * u * u, r) for r in loops)
    shape, mag = "LINEWORK", {"linework_m": round(linework, 3)}
    wmin, wmax = p["STRIP_WIDTH_M"]
    if loops:
        outer = areas[-1]
        per = sum(math.dist(outer[1][i], outer[1][(i + 1) % len(outer[1])]) for i in range(len(outer[1]))) * u
        nested = [a for a, r in areas[:-1] if all(MD.point_in_poly(x, y, outer[1]) for x, y in r)]
        w = 2 * outer[0] / per if per else 0.0
        if wmin <= w <= wmax and not nested:
            shape = "STRIP"
            mag.update(strip_width_m=round(w, 3), strip_length_m=round(outer[0] / w, 3), area_m2=round(outer[0], 3))
        elif nested:
            shape = "RING"
            inner = max(nested)
            mag.update(outer_area_m2=round(outer[0], 3), inner_area_m2=round(inner, 3),
                       ring_area_m2=round(outer[0] - inner, 3))
        else:
            shape = "CLOSED_AREA"
            mag.update(area_m2=round(outer[0], 3), loops=len(loops))
    elif lines:
        pairs = _parallel_pairs(lines, wmin / u, wmax / u, 0.5 / u)
        paired = sum(ov for _, ov in pairs) * u
        if pairs and paired >= 0.5 * (sum(e["len"] for e in lines) * u) / 2:
            ws = sorted(w * u for w, _ in pairs)
            shape = "STRIP"
            mag.update(strip_width_m=round(ws[len(ws) // 2], 3), strip_length_m=round(paired, 3))
    if circles or (arcs and shape == "LINEWORK"):
        if shape == "LINEWORK":
            shape = "CURVED"
        rs = sorted({round(e["r"] * u, 3) for e in circles + arcs})
        mag.update(radii_m=rs[:6], n_circles=len(circles), n_arcs=len(arcs))
    if hatches and shape == "LINEWORK" and not lines and not arcs and not circles:
        shape = "HATCH_REGION"
        mag.update(hatch_area_m2=round(sum(e["area"] for e in hatches) * u * u, 3), patterns=sorted(
            {e["pattern"] for e in hatches})[:4])
    tr = _treads(lines, p["STAIR_TREAD_M"][0] / u, p["STAIR_TREAD_M"][1] / u)
    xcross = _x_cross(lines, box)
    if xcross:
        mag.update(x_cross=True)
    if tr:
        mag.update(n_treads=tr["n_treads"], going_m=round(tr["going_m"] * u, 3))
    # what describes it: notes and marks near, the layer name
    near = []
    r = p["TEXT_NEAR_M"] / u
    gb = _grow(box, r)
    for t in tg.near((gb[0] + gb[2]) / 2, (gb[1] + gb[3]) / 2, max(gb[2] - gb[0], gb[3] - gb[1]) / 2 + r):
        if _in_box(gb, t["x"], t["y"]) and _dist_to_group(t["x"], t["y"], grp) <= r:
            near.append(t)
    cand = circles + arcs + [c for c in curves if c["layer"] != layer and _in_box(_grow(box, 0.05 / u), *c["c"])]
    radial = _radial(lines, cand)
    fam_votes = Counter()
    kw, marks, sections, tks = set(), set(), [], []
    w_note = 3 if ext <= 6.0 else 1
    for t in near:
        if len(t["norm"]) > p["DEPENDENCY_NOTE_MAX_CHARS"]:
            continue                                   # a sentence of general notes names families in prose
        if section_label(t["norm"]):
            continue                                   # a member-section label votes below, as a section
        for f in note_families(t["norm"], words):
            fam_votes[f] += w_note
            kw.add(f)
        if t.get("mark_family"):
            marks.add(t["mark"])
        s = section_label(t["norm"])
        if s:
            sections.append(s)
            fam_votes[s[0]] += 2
        tv = thickness_m(t["norm"])
        if tv:
            tks.append(tv)
    lf = layer_family(layer)
    if lf and not (lf in MEMBER_FAMILIES and radial and radial["spokes"] >= 6):
        fam_votes[lf] += 1 if lf in MEMBER_FAMILIES else 3 if lf == "OPENING" else 2
    if xcross:
        fam_votes["OPENING"] += 3                     # the drafting symbol of a slab opening
    if tr:
        fam_votes["STAIRS"] += 2
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    inside = any(MD.point_in_poly(cx, cy, m["poly"]) for m in bldg if m["kind"] == "FACE") or \
        _in_box(_bbox([pt for m in bldg for pt in m["poly"]]), cx, cy)
    pit_a = mag.get("inner_area_m2") if shape == "RING" else mag.get("area_m2") if shape == "CLOSED_AREA" else None
    pit = pit_a is not None and sh["role"] in ("FOUNDATION_PLAN", "GROUND_BEAM_PLAN") and inside and \
        p["PIT_INNER_M2"][0] <= pit_a <= p["PIT_INNER_M2"][1]
    if pit:                                          # V2: walls round a pit - a lift or a tank, never decided by size
        mag.update(pit=True)
        fam_votes["LIFT"] += 2
        fam_votes["WATER_TANK"] += 2
    if radial and radial["spokes"] >= 6:
        mag.update(radial_spokes=radial["spokes"], radial_r_m=round(radial["r"] * u, 3))
        if shape in ("CURVED", "LINEWORK", "CLOSED_AREA", "STRIP"):
            shape = "RADIAL"
        fam_votes["DOMES"] += 1                        # ribs of a dome or treads of a spiral stair: never decided here
        fam_votes["STAIRS"] += 1
    fam, conf, cands = None, "LOW", []
    if fam_votes:
        ranked = sorted(fam_votes.items(), key=lambda kv: (-kv[1], kv[0]))
        top = [f for f, v in ranked if v == ranked[0][1]]
        if len(top) == 1:
            fam, score = ranked[0]
            conf = "HIGH" if score >= 5 else "MEDIUM" if score >= 2 else "LOW"
        else:
            cands = top
    sig = {"LEDGER": "GEOMETRY", "SHEET": sid, "STOREY": sh.get("storey"), "LAYER": _ascii(layer, 40),
           "SHAPE": shape, "N_ENTITIES": len(grp), "LINEWORK_M": round(linework, 3),
           "BOX_M": _local_box(box, org, u), "POSITION": "INSIDE_BUILDING" if inside else "OUTSIDE_BUILDING",
           "FAMILY_GUESS": fam or "UNKNOWN", "CONFIDENCE": conf, "KEYWORDS": ",".join(sorted(kw)),
           "MARKS_NEAR": ",".join(sorted(marks))[:80], "MAGNITUDE": mag, "CANDIDATES": "|".join(cands),
           "ENTITY_IDS": ",".join(e["eid"] for e in grp[:12]) + ("..." if len(grp) > 12 else "")}
    minor = linework < p["MIN_LENGTH_M"] and max(mag.get("area_m2", 0), mag.get("outer_area_m2", 0),
                                                 mag.get("hatch_area_m2", 0)) < p["MIN_AREA_M2"]
    symbol = ext <= p["SYMBOL_MAX_M"] and any(
        math.dist((t["x"], t["y"]), (cx, cy)) * u <= p["SYMBOL_TEXT_M"] for t in near) and not fam
    if symbol:
        sig["STATE"] = "ANNOTATION_SYMBOL"
        return sig, None
    close = [t for t in near if _dist_to_group(t["x"], t["y"], grp) * u <= 0.6]
    sym = None if loops else _drafting_symbol(lines, circles + arcs, close, u, words)
    if sym:
        sig["STATE"] = sym
        return sig, None
    if plan_box and shape == "CLOSED_AREA" and loops and all(MD.point_in_poly(x, y, areas[-1][1]) for x, y in (
            (plan_box[0], plan_box[1]), (plan_box[2], plan_box[1]), (plan_box[2], plan_box[3]),
            (plan_box[0], plan_box[3]))):
        sig["STATE"] = "PLOT_OR_OUTLINE"
        return sig, None
    pb_area = (plan_box[2] - plan_box[0]) * (plan_box[3] - plan_box[1]) if plan_box else 0.0
    if plan_box and shape == "HATCH_REGION" and (sum(h["area"] for h in hatches) >= 0.5 * pb_area or any(all(
            MD.point_in_poly(x, y, h["ring"]) for x, y in ((plan_box[0], plan_box[1]), (plan_box[2], plan_box[1]),
                                                          (plan_box[2], plan_box[3]), (plan_box[0], plan_box[3])))
            for h in hatches)):
        # V2: a fill round the whole plan is a layer under / round the building (blinding, soil, paving) - LOW
        sig["STATE"] = "SITE_FILL"
        a = mag["hatch_area_m2"]
        return sig, _finding("DRAWN_NOT_MEASURED", sid, sh, _local_box(box, org, u), "LOW", family=None,
                             confidence="LOW", evidence=f"layer {_ascii(layer, 40)}: a {','.join(mag['patterns'])} "
                                                        f"fill of {a:.1f} m2 round the whole plan: a layer under or "
                                                        "round the building (blinding, soil, paving) - confirm "
                                                        "whether it is concrete and whether the takeoff holds it",
                             magnitude=mag, refs=sig["ENTITY_IDS"], layer=layer)
    if minor and not kw:
        sig["STATE"] = "MINOR_UNEXPLAINED"
        return sig, None
    if fam == "OPENING":
        panel = next((m for m in bldg if m["kind"] == "FACE" and m.get("cls") == "PANEL" and
                      (consumed or {}).get((sid, m["mid"])) and MD.point_in_poly(cx, cy, m["poly"])), None)
        if not (panel and shape == "CLOSED_AREA"):
            sig["STATE"] = "OPENING_SYMBOL"
            return sig, None
        a = mag.get("area_m2") or 0.0
        t = panel.get("t_m")
        sig["STATE"] = "OPENING_NOT_DEDUCTED"
        return sig, _finding("OPENING_NOT_DEDUCTED", sid, sh, _local_box(box, org, u), "MEDIUM", family="SLABS",
                             confidence=conf, evidence=f"closed opening outline {a:.2f} m2 on layer "
                                                       f"{_ascii(layer, 40)} inside measured panel {panel['mid']}",
                             magnitude=mag, volume=(a * t, a * t, "opening area x the panel thickness") if t else None,
                             refs=sig["ENTITY_IDS"], layer=layer)
    sig["STATE"] = "DRAWN_NOT_MEASURED"
    vol = None
    if tks and shape in ("CLOSED_AREA", "RING", "HATCH_REGION"):
        a = mag.get("ring_area_m2") or mag.get("area_m2") or mag.get("hatch_area_m2")
        vol = (a * min(tks), a * max(tks), f"plan area x printed thickness {min(tks):g}-{max(tks):g} m")
    elif sections and shape in ("STRIP", "CURVED"):
        L = mag.get("strip_length_m") or linework / 2
        ws = sorted(a * b * 1e-4 for _, a, b, _ in sections)
        vol = (L * ws[0], L * ws[-1], "strip length x printed section")
    big = linework >= 3.0 or max(mag.get("area_m2", 0), mag.get("outer_area_m2", 0),
                                 mag.get("hatch_area_m2", 0)) >= 1.0
    sev = "HIGH" if big or (fam in CONCRETE_FAMILIES and fam not in MEMBER_FAMILIES) else "MEDIUM"
    ev = (f"layer {_ascii(layer, 40)}: {len(grp)} entities ({len(lines)} lines, {len(arcs)} arcs, {len(circles)} "
          f"circles, {len(hatches)} hatches), {linework:.2f} m; shape {shape}; {sig['POSITION'].lower()}" +
          (f"; notes: {', '.join(sorted(kw))}" if kw else "") +
          (f"; marks near: {sig['MARKS_NEAR']}" if marks else "") +
          (f"; layer suggests {lf}" if lf else "") + (f"; could be {' or '.join(cands)}" if cands else ""))
    kind = "STAIR_NOT_MEASURED" if (fam == "STAIRS" and tr and not any(
        i["trade"] == "CONCRETE" and i["family"] == "STAIRS" for i in items_of(consumed or {}))) else \
        "DRAWN_NOT_MEASURED"
    fnd = _finding(kind, sid, sh, _local_box(box, org, u), sev, family=fam, confidence=conf,
                   evidence=ev, magnitude=mag, volume=vol, refs=sig["ENTITY_IDS"], layer=layer)
    return sig, fnd


def _dist_to_group(x, y, grp):
    best = float("inf")
    for e in grp:
        if e["type"] == "LINE":
            d = _seg_dist(x, y, e["a"], e["b"])
        elif e["type"] in ("CIRCLE", "ARC"):
            d = abs(math.dist((x, y), e["c"]) - e["r"]) if e["type"] == "CIRCLE" else \
                min(math.dist((x, y), q) for q in e["pts"])
            if e["type"] == "CIRCLE" and math.dist((x, y), e["c"]) <= e["r"]:
                d = 0.0
        else:
            ring = e["ring"]
            d = 0.0 if MD.point_in_poly(x, y, ring) else min(
                _seg_dist(x, y, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
        best = min(best, d)
        if best == 0.0:
            break
    return best


BAR_NOTE = re.compile(r"(?:Ø|\bT|\bY|\bFI|\bD)\s*\d{1,2}\s*(?:@|/|-|\bAT\b)\s*\d{2,3}|\b\d{1,2}\s*Ø\s*\d{1,2}\b")


def _drafting_symbol(lines, curves, near, u, words):
    """REBAR_SYMBOL: a few bar lines (with hooks) beside a bar notation ('Ø10@200', '5Ø12'); SECTION_MARK: a cut line
    ending in small bubbles that hold single letters / numbers. Drawn on any layer, they are annotation."""
    notes = [DM.normalize(t["norm"]).upper() for t in near]
    if lines and len(lines) <= 8 and not curves and any(BAR_NOTE.search(n) for n in notes):
        return "REBAR_SYMBOL"
    small = [c for c in curves if c["r"] * u <= 0.6]
    if lines and len(lines) <= 4 and small and any(re.fullmatch(r"[A-Z0-9]{1,2}", n.strip()) for n in notes):
        ends = [q for ln in lines for q in (ln["a"], ln["b"])]
        if any(min(math.dist(q, c["c"]) for q in ends) <= c["r"] * 1.6 for c in small):
            return "SECTION_MARK"
    return None


def _x_cross(lines, box):
    """two lines crossing near their middles, each spanning most of the group's diagonal: an opening's X."""
    diag = math.hypot(box[2] - box[0], box[3] - box[1])
    long_ = [ln for ln in lines if ln["len"] >= 0.7 * diag > 0]
    for i, a in enumerate(long_):
        for b in long_[i + 1:]:
            (x1, y1), (x2, y2) = a["a"], a["b"]
            (x3, y3), (x4, y4) = b["a"], b["b"]
            d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(d) < 1e-12:
                continue
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
            v = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / d
            ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1) - math.atan2(y4 - y3, x4 - x3))) % 180.0
            if 0.3 <= t <= 0.7 and 0.3 <= v <= 0.7 and 30.0 <= ang <= 150.0:
                return True
    return False


def _radial(lines, curves):
    """lines radiating from the centre of a circle / arc of the group (dome ribs, spiral treads)."""
    best = None
    for c in curves:
        cx, cy, r = c["c"][0], c["c"][1], c["r"]
        n = 0
        for ln in lines:
            (ax, ay), (bx, by) = ln["a"], ln["b"]
            L = math.hypot(bx - ax, by - ay)
            if L < 0.3 * r:
                continue
            dperp = abs((bx - ax) * (ay - cy) - (by - ay) * (ax - cx)) / L
            if dperp <= 0.05 * r and min(math.dist((ax, ay), (cx, cy)), math.dist((bx, by), (cx, cy))) <= 1.05 * r:
                n += 1
        if n and (best is None or n > best["spokes"]):
            best = {"spokes": n, "r": r, "c": (cx, cy)}
    return best


def _local_box(b, org, u):
    if b is None:
        return None
    return tuple(round(v, 3) for v in ((b[0] - org[0]) * u, (b[1] - org[1]) * u, (b[2] - org[0]) * u,
                                       (b[3] - org[1]) * u))


def _finding(kind, sid, sh, box, severity, *, family=None, confidence="MEDIUM", evidence="", magnitude=None,
             volume=None, refs="", layer="", items=(), storey=None):
    if severity not in SEVERITY:
        raise CompletenessError(f"severity {severity}")
    st = storey or (sh or {}).get("storey")
    return {"FINDING_ID": _fid(kind, sid, st, box, layer, family, refs[:120] if refs else ""), "KIND": kind,
            "SEVERITY": severity, "FAMILY": family or "UNKNOWN", "CONFIDENCE": confidence, "SHEET": sid or "",
            "STOREY": st or "", "BOX_M": box, "EVIDENCE": evidence, "MAGNITUDE": magnitude or {},
            "VOLUME_LOW_M3": None if not volume else round(volume[0], 4),
            "VOLUME_HIGH_M3": None if not volume else round(volume[1], 4),
            "VOLUME_BASIS": "" if not volume else volume[2], "ITEMS": ",".join(items)[:200],
            "REFS": refs, "ACTION": ACTION[kind]}


# ====================================================================== MEMBERS ledger
def member_ledger(D, members, consumed, u):
    signals, findings = [], []
    for sid, rec in _plan_sheets(D):
        sh, org = rec["sheet"], rec["sheet"].get("origin") or (0.0, 0.0)
        for m in members.get(sid, []):
            c = consumed.get((sid, m["mid"]))
            if m["kind"] == "FACE":
                if m.get("cls") != "PANEL" or m.get("region") not in ("STRUCTURAL_SLAB", "GROUND_SLAB"):
                    continue
            elif m["kind"] in ("COLUMN_BOX", "COLUMN"):
                if m.get("suspect"):
                    b = m["box"]
                    findings.append(_finding(
                        "MEMBER_OUTLINE_SUSPECT", sid, sh, _local_box(b, org, u), "MEDIUM", family="COLUMNS",
                        confidence="MEDIUM", evidence=f"column {m['mid']} bound to an outline "
                                                      f"{(b[2] - b[0]) * u:.2f} x {(b[3] - b[1]) * u:.2f} m, more "
                                                      "than twice every section its schedule prints",
                        magnitude={"outline_m": (round((b[2] - b[0]) * u, 3), round((b[3] - b[1]) * u, 3))},
                        refs=m["mid"]))
                continue                                     # columns: the VERTICAL ledger
            state = "HELD_BY_ITEM" if c else "DETECTED_NOT_ITEMIZED"
            signals.append({"LEDGER": "MEMBERS", "SHEET": sid, "STOREY": sh.get("storey"), "KIND": m["kind"],
                            "MEMBER": m["mid"], "FAMILY": m["family"], "STATE": state,
                            "ITEMS": ",".join(c["items"][:4]) if c else ""})
            if not c:
                box = _local_box(_bbox(m["poly"]), org, u)
                area = MD.poly_area(m["poly"]) * u * u
                findings.append(_finding(
                    "MEMBER_DETECTED_NOT_ITEMIZED", sid, sh, box, "MEDIUM" if m["kind"] == "STRAP_CANDIDATE" else
                    "HIGH", family=m["family"], confidence="MEDIUM",
                    evidence=f"{m['kind'].lower()} {m['mid']} ({m.get('state') or ''}) plan {area:.2f} m2; no item",
                    magnitude={"plan_area_m2": round(area, 3)}, refs=m["mid"]))
    return signals, findings


# ====================================================================== LABELS ledger
def _referenced_text_ids(D, items):
    """text ids the route's records name (marks it bound, footing member ids, face tags, strap marks)."""
    out = {}
    for sid, rec in _plan_sheets(D):
        for m in rec.get("marks", []) or []:
            out[m["text_id"]] = m.get("state", "")
        for m in ((rec.get("straps") or {}).get("marks") or []):
            out.setdefault(m["text_id"], m.get("state", "BOUND"))
        for f in ((rec.get("slab") or {}).get("faces") or []):
            for t in (f.get("tag_ids") or []):
                out.setdefault(t, "SLAB_TAG")
            for t in (f.get("opening_labels") or []):
                out.setdefault(t if isinstance(t, str) else str(t), "OPENING_LABEL")
        for ft in rec.get("footings", []) or []:
            tid = ft["member_id"].split(":", 2)[-1]
            out.setdefault(tid, "FOOTING_" + str(ft.get("state")))
    return out


def label_ledger(D, items, members, consumed, p):
    u = D["unit_m"]
    lib = D.get("lib") or {}
    ref = _referenced_text_ids(D, items)
    item_text = " ".join(i.get("source") or "" for i in items)
    planted, col_at = set(), set()
    for i in items:
        if i["trade"] != "CONCRETE":
            continue
        m = re.search(r"PC@(-?\d+),(-?\d+)", i.get("component_id") or "")
        if m:
            planted.add((int(m.group(1)), int(m.group(2))))
        m = re.search(r"COL:(SH\d{2,3}):([^@|:]+)@(-?\d+),(-?\d+)", i.get("component_id") or "")
        if m:
            col_at.add((m.group(1), m.group(2), int(m.group(3)), int(m.group(4))))
    signals, findings = [], []
    near_r = p["LABEL_MEMBER_M"] / u
    for sid, rec in _plan_sheets(D):
        sh, org = rec["sheet"], rec["sheet"].get("origin") or (0.0, 0.0)
        ms = members.get(sid, [])
        mg = _Grid(max(near_r * 4, 1e-6))
        for m in ms:
            mg.add(_grow(_bbox(m["poly"]), near_r), m)
        seen = set()
        bubbles = [e for e in (p.get("_ents") or {}).get(sid, []) if e["type"] == "CIRCLE" and e["r"] * u <= 0.7]
        lib_marks = {k[1] for k in lib}
        for t in _sheet_texts(D, sid):
            sec = section_label(t["norm"])
            fam = MARK_FAMILY.get(t.get("mark_family")) if t.get("mark_family") else None
            if not (fam or sec):
                continue
            if DI.role_guess(t.get("layer") or "") in ("GRID", "DIMENSION", "FRAME"):
                continue                                      # an axis / dimension / title label, not a mark
            if fam and not sec and not re.search(r"\d", t.get("mark") or "") and t.get("mark") not in lib_marks:
                if any(math.dist((t["x"], t["y"]), e["c"]) <= e["r"] for e in bubbles):
                    continue                                  # a letter in a grid bubble
                if not any(k[1] == t.get("mark") for k in lib):
                    continue                                  # a bare letter no schedule names is not a mark
            mark = t.get("mark") if fam else None
            key = (t.get("mark") or t["norm"], round(t["x"] * u, 1), round(t["y"] * u, 1))
            if key in seen:                                   # one label drawn twice (text + block copy)
                continue
            seen.add(key)
            fam = fam or sec[0]
            state, reason, holder = None, "", None
            rs = ref.get(t["id"])
            if rs is not None and (str(rs).startswith("BOUND") or rs in ("SLAB_TAG", "OPENING_LABEL") or
                                   str(rs).startswith("FOOTING_") and "NO_OUTLINE" not in str(rs)):
                state, reason = "CONSUMED_BY_REFERENCE", str(rs)
            elif sec and (round(t["x"]), round(t["y"])) in planted:
                state, reason = "CONSUMED_BY_REFERENCE", "planted column item"
            elif mark and (sid, mark, round(t["x"]), round(t["y"])) in col_at:
                state, reason = "CONSUMED_BY_REFERENCE", "column item at this label"
            if state is None:
                cands = [m for m in mg.near(t["x"], t["y"], near_r) if MD.dist_point_poly(t["x"], t["y"], m["poly"])
                         <= near_r and _family_match(fam, m)]
                held = [m for m in cands if consumed.get((sid, m["mid"])) or m["kind"] in ("COLUMN_BOX",)]
                carries = lambda m: bool(mark and m.get("mark") and (m.get("mark") == mark or      # noqa: E731
                                                                     mark in str(m.get("mark")).split("/")))
                if rs is not None:          # V2: the route saw this mark and could not bind it - only a member that
                    same = [m for m in held if carries(m)]     # carries the same mark consumes it, never a bare band
                else:
                    same = [m for m in held if not m.get("mark") or not mark or carries(m)]
                if same:
                    state, reason, holder = "CONSUMED_BY_PROXIMITY", f"beside {same[0]['kind'].lower()} " \
                                                                     f"{same[0]['mid']}", same[0]
                elif held and (rs is None or any(m.get("mark") for m in held)):
                    hm = next((m for m in held if m.get("mark")), held[0])
                    state, reason, holder = "MEMBER_CONFLICT", (f"route state {rs}; " if rs else "") + \
                        f"on {hm['kind'].lower()} {hm['mid']} measured as {hm.get('mark')}", hm
                else:
                    state = "NOT_CONSUMED"
                    reason = (f"route state {rs}" if rs else "no member of its family within "
                              f"{p['LABEL_MEMBER_M']:g} m")
                    if rs is not None and held:
                        reason += f"; beside unmarked {held[0]['kind'].lower()} {held[0]['mid']} held " + \
                            ("unresolved" if (consumed.get((sid, held[0]["mid"])) or {}).get("cats") == {"UNRESOLVED"}
                             else "without this mark")
                    if fam and mark and t.get("mark_family") in SCHEDULED_FAMILIES and \
                            (t["mark_family"], mark) not in lib and not any(k[1] == mark for k in lib):
                        reason += "; no schedule row"
            tok = _ascii(t["norm"] if sec else mark, 30)
            signals.append({"LEDGER": "LABELS", "SHEET": sid, "STOREY": sh.get("storey"), "TEXT_ID": t["id"],
                            "TOKEN": tok, "FAMILY": fam, "STATE": state, "REASON": reason,
                            "AT_M": (round((t["x"] - org[0]) * u, 3), round((t["y"] - org[1]) * u, 3))})
            if state in ("NOT_CONSUMED", "MEMBER_CONFLICT"):
                bx = _local_box((t["x"], t["y"], t["x"], t["y"]), org, u)
                kind = "LABEL_NOT_CONSUMED" if state == "NOT_CONSUMED" else "LABEL_MEMBER_CONFLICT"
                sev = "HIGH" if (sec or state == "NOT_CONSUMED") else "MEDIUM"
                mag = {"section_cm": (sec[1], sec[2])} if sec else {}
                findings.append(_finding(kind, sid, sh, bx, sev, family=fam, confidence="MEDIUM",
                                         evidence=f"label {tok} ({fam}); {reason}", magnitude=mag, refs=t["id"]))
    _ = item_text
    return signals, findings


def _family_match(fam, m):
    if fam == "PLANTED_COLUMN":                         # consumed only by the column itself, never by its beam
        return m["family"] == "COLUMNS"
    if fam == "COLUMNS":
        return m["family"] == "COLUMNS"
    if fam == "GROUND_BEAMS":
        return m["family"] == "GROUND_BEAMS"
    if fam == "BEAMS":
        return m["family"] in ("BEAMS", "GROUND_BEAMS")
    if fam == "SLABS":
        return m["kind"] == "FACE"
    if fam == "FOOTINGS":
        return m["family"] in ("FOOTINGS", "COLUMNS")
    return False


# ====================================================================== SCHEDULE ledger
def schedule_ledger(D, label_signals, intake=None):
    S = D.get("schedule") or {}
    placed = Counter()
    for s in label_signals:
        if s["TOKEN"] and (s["STATE"].startswith("CONSUMED") or str(s["REASON"]).startswith("route state")):
            placed[s["TOKEN"]] += 1            # V2: a mark drawn on a plan and left unbound is placed (and reported)
    for sid, rec in _plan_sheets(D):
        for b in rec.get("beams", []) or []:
            if b.get("mark"):
                for mk in str(b["mark"]).split("/"):
                    placed[mk] += 1
        for c in rec.get("columns", []) or []:
            placed[c.get("mark")] += 1
        for f in rec.get("footings", []) or []:
            for mk in str(f.get("mark") or "").split("/"):
                placed[mk] += 1
        for ln in rec.get("cb_lines", []) or []:
            placed[ln.get("mark")] += 1
        for m in ((rec.get("straps") or {}).get("marks") or []):
            placed[m.get("mark")] += 1
    signals, findings = [], []
    rows = {}
    for r in S.get("rows", []):
        rows.setdefault((r["family"], r["mark"]), r)
    for (fam, mark), r in sorted(rows.items()):
        n = placed.get(mark, 0)
        st = "PLACED" if n else "NOT_PLACED"
        signals.append({"LEDGER": "SCHEDULE", "SHEET": r.get("sheet") or "", "FAMILY": fam, "TOKEN": mark,
                        "STATE": st, "PLAN_OCCURRENCES": n, "SOURCE": _ascii(r.get("source"), 30)})
        if not n:
            dims = r.get("dims_m") or {}
            findings.append(_finding("SCHEDULED_NOT_PLACED", r.get("sheet") or "", None, None, "MEDIUM",
                                     family=MARK_FAMILY.get(fam, fam), confidence="MEDIUM", storey="ALL",
                                     evidence=f"schedule row {_ascii(mark, 20)} ({fam}) "
                                              f"{_ascii(r.get('source'), 30)}; on no plan",
                                     magnitude={k: v for k, v in dims.items() if isinstance(v, (int, float))},
                                     refs=_ascii(r.get("source"), 40)))
    lib_marks = {m for _, m in rows}
    for s in label_signals:
        if s["STATE"] == "NOT_CONSUMED" and "no schedule row" in s["REASON"] and s["TOKEN"] not in lib_marks:
            findings.append(_finding("PLACED_NOT_SCHEDULED", s["SHEET"], None, (s["AT_M"][0], s["AT_M"][1],
                                                                                s["AT_M"][0], s["AT_M"][1]),
                                     "HIGH", family=s["FAMILY"], confidence="HIGH", storey=s["STOREY"],
                                     evidence=f"plan mark {s['TOKEN']} has no schedule row", refs=s["TEXT_ID"]))
    # attribute-row inserts on a schedule sheet the reader did not turn into a row (a key it cannot read as a mark,
    # e.g. 'B.W'): the type and its printed section are on the drawing and in no takeoff
    srcs = {str(r.get("source")) for r in S.get("rows", [])}
    sched = {sh["sheet_id"] for sh in D["model"]["sheets"] if sh["role"] == "SCHEDULE"}
    sheet_of = D["model"].get("sheet_of")
    for ins in (intake or {}).get("inserts", []) or []:
        at = ins.get("attribs") or {}
        if len(at) < 3 or not sheet_of:
            continue
        sid = sheet_of(ins["x"], ins["y"])
        if sid not in sched:
            continue
        try:
            src = f"INSERT {int(ins['handle_hex'], 16)}"
        except (KeyError, ValueError, TypeError):
            continue
        if src in srcs:
            continue
        vals = [str(v).strip() for v in at.values()]
        nums = [v for v in vals if re.fullmatch(r"\d+(?:\.\d+)?", v)]
        if len(nums) < 2:
            continue                                     # a header row (tag names), not a type
        key = _ascii(vals[0], 16)
        dims = [float(v) for v in nums[:2]]
        signals.append({"LEDGER": "SCHEDULE", "SHEET": sid, "FAMILY": "", "TOKEN": key, "STATE": "ROW_NOT_READ",
                        "PLAN_OCCURRENCES": 0, "SOURCE": src})
        sec = section_label(f"{key} {int(dims[0])}x{int(dims[1])}")
        fam = sec[0] if sec else None
        findings.append(_finding("SCHEDULE_ROW_UNREAD", sid, None, None, "HIGH", family=fam, confidence="MEDIUM",
                                 storey="ALL", evidence=f"schedule row {key} ({src}, {len(at)} fields, first sizes "
                                                        f"{dims[0]:g} / {dims[1]:g}) was not read as a type: no "
                                                        "takeoff can use its section",
                                 magnitude={"sizes": tuple(dims)}, refs=src))
    for w in S.get("warnings", []) or []:
        txt = w if isinstance(w, str) else (w.get("warning") or w.get("reason") or str(w))
        signals.append({"LEDGER": "SCHEDULE", "SHEET": "", "FAMILY": "", "TOKEN": "", "STATE": "READER_WARNING",
                        "PLAN_OCCURRENCES": 0, "SOURCE": _ascii(txt, 80)})
        findings.append(_finding("SCHEDULE_ROW_UNREAD", "", None, None, "LOW", confidence="LOW", storey="ALL",
                                 evidence=f"schedule reader: {_ascii(txt, 120)}", refs=_ascii(txt, 60)))
    return signals, findings


# ====================================================================== STOREYS / VERTICAL ledgers
STOREY_ORDER = ("FOUNDATION", "GROUND", "GF", "1F", "2F", "3F", "4F", "5F", "6F", "ROOF")


def storey_ledger(D, heights, items):
    heights = heights or {}
    plans = defaultdict(list)
    for sid, rec in _plan_sheets(D):
        if rec["sheet"]["role"] == "SLAB_PLAN":
            plans[rec["sheet"]["storey"]].append(sid)
    bands = Counter()
    for r in (D.get("schedule") or {}).get("rows", []):
        for st in (r.get("by_storey") or {}):
            if st not in ("FOUNDATION", "GROUND"):
                bands[st] += 1
    named = set(heights) | set(bands)
    signals, findings = [], []
    for st in sorted(named | set(plans), key=lambda s: STOREY_ORDER.index(s) if s in STOREY_ORDER else 99):
        has_plan, has_h = bool(plans.get(st)), st in heights
        state = "PLAN_AND_HEIGHT" if has_plan and has_h else "PLAN_ONLY" if has_plan else "NAMED_WITHOUT_PLAN"
        signals.append({"LEDGER": "STOREYS", "STOREY": st, "STATE": state, "PLANS": ",".join(plans.get(st, [])),
                        "HEIGHT_M": heights.get(st), "SCHEDULE_BANDS": bands.get(st, 0)})
        if not has_plan:
            findings.append(_finding("STOREY_PLAN_MISSING", "", None, None, "HIGH", confidence="HIGH", storey=st,
                                     evidence=f"storey {st}: height {heights.get(st)} m, {bands.get(st, 0)} schedule "
                                              f"bands; no slab plan of this storey in the set",
                                     magnitude={"schedule_bands": bands.get(st, 0)}))
        elif not has_h and st != "ROOF":
            findings.append(_finding("STOREY_HEIGHT_MISSING", plans[st][0], None, None, "MEDIUM", confidence="HIGH",
                                     storey=st, evidence=f"slab plan {','.join(plans[st])} storey {st}: no height"))
        if has_plan and bands and not bands.get(st) and st != "ROOF":
            n_cols = sum(len([b for b in (D["sheets"][sid].get("column_presence") or [])]) for sid in plans[st])
            if n_cols:
                findings.append(_finding("STOREY_COLUMN_BANDS_MISSING", plans[st][0], None, None, "HIGH",
                                         family="COLUMNS", confidence="HIGH", storey=st,
                                         evidence=f"the {st} plan shows {n_cols} column outlines; the column schedule "
                                                  f"has bands for {', '.join(sorted(bands))} and none for {st}",
                                         magnitude={"column_outlines": n_cols}))
    return signals, findings


def _composites(boxes, gap):
    """touching column outlines (the pieces of an L / T / cross column) as one outline: [(box, [members])]."""
    parent = list(range(len(boxes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _boxes_touch(_grow(boxes[i][0], gap), boxes[j][0]):
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i, bx in enumerate(boxes):
        groups[find(i)].append(bx)
    out = []
    for g in groups.values():
        box = None
        for b, _ in g:
            box = _union_box(box, b)
        out.append((box, [m for _, m in g]))
    return out


def vertical_ledger(D, items, members, risk, heights, u, consumed=None):
    """columns drawn on each storey plan vs the column items of that storey, both in sheet-local metres, one to one.
    A column item stands where its column-plan outline is (the route's own presence rule); an item bound to its label
    only (no outline) is matched to the nearest unmatched outline within 3 m. Unmatched outlines are columns no item
    holds; unmatched items are columns counted on a storey whose plan shows no column near them (a possible
    over-count, reported - never removed)."""
    heights = heights or {}
    origin = {s["sheet_id"]: s.get("origin") or (0.0, 0.0) for s in D["model"]["sheets"]}
    mbox = {}
    for key, c in (consumed or {}).items():
        if not isinstance(key, tuple):
            continue
        sid, mid = key
        m = next((x for x in members.get(sid, []) if x["mid"] == mid and x["kind"] == "COLUMN"), None)
        if m is None:
            continue
        o = origin.get(sid, (0.0, 0.0))
        b = m["box"]
        for iid in c["items"]:
            mbox[iid] = ((b[0] - o[0]) * u, (b[1] - o[1]) * u, (b[2] - o[0]) * u, (b[3] - o[1]) * u)
    col_items = defaultdict(list)                     # storey -> [(local box, boxed?, item)]
    for it in items:
        if it["trade"] != "CONCRETE" or it["family"] != "COLUMNS" or it["storey"] in ("FOUNDATION", "UNKNOWN"):
            continue
        if it["item_id"] in mbox:
            col_items[it["storey"]].append((mbox[it["item_id"]], True, it))
            continue
        m = COL_ID.match(it["component_id"]) or re.match(r"^COL:(SH\d{2,3}):(PC)@(-?\d+),(-?\d+)\|(.+)$",
                                                          it["component_id"])
        if not m:
            continue
        sid, x, y = m.group(1), float(m.group(3)), float(m.group(4))
        o = origin.get(sid, (0.0, 0.0))
        lx, ly = (x - o[0]) * u, (y - o[1]) * u
        col_items[it["storey"]].append(((lx, ly, lx, ly), False, it))
    signals, findings = [], []
    plan_storeys = set()
    for sid, rec in _plan_sheets(D):
        if rec["sheet"]["role"] != "SLAB_PLAN":
            continue
        st, o = rec["sheet"]["storey"], rec["sheet"].get("origin") or (0.0, 0.0)
        plan_storeys.add(st)
        boxes = []
        for m in members.get(sid, []):
            if m["kind"] in ("COLUMN_BOX", "COLUMN"):
                b = m["box"]
                boxes.append((((b[0] - o[0]) * u, (b[1] - o[1]) * u, (b[2] - o[0]) * u, (b[3] - o[1]) * u), m))
        comps = _composites(boxes, 0.05)
        pool = list(col_items.get(st, []))
        matched = {}
        for k, (lb, ms_) in enumerate(comps):             # pass 1: an item whose outline overlaps
            for c in pool:
                if c[1] and _boxes_touch(_grow(lb, 0.15), c[0]):
                    matched.setdefault(k, []).append(c)
        used = {id(c[2]) for v in matched.values() for c in v}
        free = sorted(((math.dist(((lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2), (c[0][0], c[0][1])), k, n)
                       for k, (lb, _) in enumerate(comps) if k not in matched
                       for n, c in enumerate(pool) if not c[1] and id(c[2]) not in used), key=lambda x: x[0])
        for d, k, n in free:                              # pass 2: label-bound items, nearest first, one to one
            c = pool[n]
            if d > 3.0 or k in matched or id(c[2]) in used:
                continue
            matched[k] = [c]
            used.add(id(c[2]))
        for k, (lb, ms_) in enumerate(comps):
            cx, cy = (lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2
            w, d = lb[2] - lb[0], lb[3] - lb[1]
            hit = matched.get(k, [])
            state = "HELD_BY_ITEM" if hit and hit[0][1] else "HELD_BY_LABEL_ITEM" if hit else "NOT_ITEMIZED"
            area = sum((m["box"][2] - m["box"][0]) * (m["box"][3] - m["box"][1]) for m in ms_) * u * u
            signals.append({"LEDGER": "VERTICAL", "SHEET": sid, "STOREY": st, "STATE": state,
                            "AT_M": (round(cx, 3), round(cy, 3)), "SIZE_M": (round(w, 3), round(d, 3)),
                            "PIECES": len(ms_), "ITEMS": ",".join(c[2]["item_id"] for c in hit[:2])})
            if not hit:
                h = heights.get(st)
                vol = (area * h, area * h, "drawn outline area x storey height") if h and area < 4.0 else None
                findings.append(_finding("COLUMN_PRESENCE_NOT_ITEMIZED", sid, rec["sheet"],
                                         tuple(round(v, 3) for v in lb), "HIGH", family="COLUMNS",
                                         confidence="MEDIUM",
                                         evidence=f"column outline {w:.2f} x {d:.2f} m ({len(ms_)} pieces, "
                                                  f"{area:.3f} m2) on the {st} plan; no {st} column item here",
                                         magnitude={"size_m": (round(w, 3), round(d, 3)), "area_m2": round(area, 4)},
                                         volume=vol, refs=",".join(m["mid"] for m in ms_[:4])))
        for c in pool:
            if id(c[2]) in used or "PC@" in c[2]["component_id"]:
                continue
            it = c[2]
            v = it.get("base") or 0.0
            signals.append({"LEDGER": "VERTICAL", "SHEET": sid, "STOREY": st, "STATE": "ITEM_WITHOUT_OUTLINE",
                            "AT_M": (round(c[0][0], 3), round(c[0][1], 3)), "SIZE_M": None, "PIECES": 0,
                            "ITEMS": it["item_id"]})
            findings.append(_finding("COLUMN_ITEM_WITHOUT_PRESENCE", sid, rec["sheet"],
                                     tuple(round(x, 3) for x in c[0]), "MEDIUM", family="COLUMNS",
                                     confidence="MEDIUM",
                                     evidence=f"column item {it['item_id']} ({it['category']}, {v:.3f} m3) on {st}; "
                                              f"the {st} plan shows no column outline within 3 m",
                                     magnitude={"item_m3": round(v, 4)},
                                     volume=(v, v, "the item's own base (possible over-count)") if v else None,
                                     items=[it["item_id"]], refs=it["component_id"]))
    absent = [r for r in risk if r.get("KIND") == "COLUMN_ABSENT_ON_STOREY_PLAN"]
    by_st = defaultdict(list)
    for r in absent:
        by_st[str(r.get("WHERE")).split()[0]].append(r)
    for st, rs in sorted(by_st.items()):
        findings.append(_finding("COLUMN_BAND_NOT_ON_PLAN", "", None, None, "MEDIUM", family="COLUMNS",
                                 confidence="MEDIUM", storey=st,
                                 evidence=f"{len(rs)} column occurrences have a schedule band for {st} and no "
                                          f"outline on the {st} plan (route: not counted)",
                                 magnitude={"occurrences": len(rs)},
                                 refs=";".join(str(r.get("DETAIL", "")).split(":")[0] for r in rs[:6])))
    return signals, findings


# ====================================================================== NOTES ledger
def note_ledger(D, items, members, consumed, geo_findings, words, en, p):
    u = D["unit_m"]
    measured = {ITEM_FAMILY.get(i["family"]) for i in items if i["trade"] == "CONCRETE" and
                i["category"] != "UNRESOLVED"}
    held = {ITEM_FAMILY.get(i["family"]) for i in items if i["trade"] == "CONCRETE"}
    drawn = {f["FAMILY"] for f in geo_findings if f["KIND"] in ("DRAWN_NOT_MEASURED", "STAIR_NOT_MEASURED",
                                                                  "REGION_EXCLUDED", "OPENING_NOT_DEDUCTED")}
    refs = defaultdict(list)
    signals, findings = [], []
    sheets = {s["sheet_id"]: s for s in D["model"]["sheets"]}
    for t in D["model"]["texts"]:
        sid = t.get("sheet")
        if not sid:
            continue
        fams = note_families(t["norm"], words)
        for f in fams:
            refs[f].append((sid, t))
        dep = DEPENDENCY.search(DM.normalize(t["norm"]).upper())
        if dep and sheets.get(sid, {}).get("role") in PLAN_ROLES:
            sh = sheets[sid]
            org = sh.get("origin") or (0.0, 0.0)
            best = None
            r = p["DEPENDENCY_NEAR_M"] / u
            for m in members.get(sid, []):
                if m["kind"] == "FACE" and m.get("cls") != "PANEL":
                    continue
                if m["kind"] == "FACE":                 # a note sits inside a panel: measure to its edge, members
                    poly = m["poly"]                    # win a tie
                    d = min(_seg_dist(t["x"], t["y"], poly[i], poly[(i + 1) % len(poly)])
                            for i in range(len(poly))) + 0.05 / u
                else:
                    d = MD.dist_point_poly(t["x"], t["y"], m["poly"])
                if d <= r and (best is None or d < best[0]):
                    best = (d, m)
            its = consumed.get((sid, best[1]["mid"]), {}).get("items", []) if best else []
            phrase = re.sub(r"\s+", " ", dep.group(0)).strip()
            general = len(DM.normalize(t["norm"])) > p["DEPENDENCY_NOTE_MAX_CHARS"] or best is None or \
                best[0] * u > p["DEPENDENCY_MEMBER_M"]
            signals.append({"LEDGER": "NOTES", "SHEET": sid, "STATE": "GENERAL_NOTE_DEPENDENCY" if general else
                            "DEPENDENCY", "TOKEN": _ascii(phrase, 30),
                            "FAMILY": best[1]["family"] if best else "", "MEMBER": best[1]["mid"] if best else ""})
            if general:
                continue
            findings.append(_finding("DEPENDENCY", sid, sh, _local_box((t["x"], t["y"], t["x"], t["y"]), org, u),
                                     "MEDIUM", family=best[1]["family"] if best else None, confidence="MEDIUM",
                                     evidence=f"note '{_ascii(phrase, 30)}'" + (
                                         f" {best[0] * u:.2f} m from {best[1]['kind'].lower()} {best[1]['mid']}"
                                         if best else "; no measured member within "
                                                      f"{p['DEPENDENCY_NEAR_M']:g} m"),
                                     items=its, refs=t["id"]))
    for fam, lst in sorted(refs.items()):
        state = "MEASURED" if fam in measured else "HELD_UNRESOLVED" if fam in held else \
            "DRAWN" if fam in drawn else "REFERENCED_ONLY"
        sh_ids = sorted({s for s, _ in lst})
        signals.append({"LEDGER": "NOTES", "SHEET": ",".join(sh_ids), "STATE": state, "TOKEN": fam, "FAMILY": fam,
                        "MEMBER": f"{len(lst)} notes"})
        if state == "REFERENCED_ONLY":
            findings.append(_finding("REFERENCED_NOT_DRAWN", ",".join(sh_ids)[:40], None, None, "MEDIUM", family=fam,
                                     confidence="LOW", storey="ALL",
                                     evidence=f"{len(lst)} notes name {fam} on {', '.join(sh_ids)}; no item and no "
                                              "unexplained drawing of it", magnitude={"notes": len(lst)},
                                     refs=",".join(t["id"] for _, t in lst[:6])))
    return signals, findings


# ====================================================================== OVERLAP ledger
def overlap_ledger(D, members, consumed, items, p):
    u = D["unit_m"]
    by_item = {i["item_id"]: i for i in items}
    findings, signals = [], []
    for sid, rec in _plan_sheets(D):
        sh, org = rec["sheet"], rec["sheet"].get("origin") or (0.0, 0.0)
        bands = [m for m in members.get(sid, []) if m["kind"] == "BAND" and consumed.get((sid, m["mid"]))]
        g = _Grid(2.0 / u)
        for m in bands:
            g.add(_bbox(m["poly"]), m)
        seen = set()
        for a in bands:
            ba = _bbox(a["poly"])
            for b in g.near((ba[0] + ba[2]) / 2, (ba[1] + ba[3]) / 2, max(ba[2] - ba[0], ba[3] - ba[1])):
                if b is a or (id(b), id(a)) in seen or not _boxes_touch(ba, _bbox(b["poly"])):
                    continue
                seen.add((id(a), id(b)))
                if a.get("parent") and a.get("parent") == b.get("parent"):
                    continue
                if a["mid"].split(".")[0] == b["mid"].split(".")[0]:
                    continue
                ar = MD.overlap_area(a["poly"], b["poly"]) * u * u
                if ar < p["OVERLAP_MIN_M2"]:
                    continue
                da, db = _depth(consumed[(sid, a["mid"])], by_item), _depth(consumed[(sid, b["mid"])], by_item)
                dep = min(x for x in (da, db) if x) if (da or db) else None
                vol = (ar * dep, ar * dep, "overlap area x the shallower member's depth") if dep else None
                cp = MD.clip_convex(a["poly"], b["poly"])
                box = _local_box(_bbox(cp), org, u) if len(cp) >= 3 else None
                signals.append({"LEDGER": "OVERLAP", "SHEET": sid, "STATE": "OVERLAP", "A": a["mid"], "B": b["mid"],
                                "AREA_M2": round(ar, 4)})
                findings.append(_finding("MEMBER_OVERLAP", sid, sh, box, "HIGH" if (vol and vol[0] >= 0.05) else
                                         "MEDIUM", family=a["family"], confidence="HIGH",
                                         evidence=f"{a['mid']} and {b['mid']} overlap {ar:.3f} m2 on {sid}; both "
                                                  "itemized", magnitude={"overlap_m2": round(ar, 4)}, volume=vol,
                                         items=consumed[(sid, a["mid"])]["items"][:1] +
                                         consumed[(sid, b["mid"])]["items"][:1], refs=f"{a['mid']}|{b['mid']}"))
    return signals, findings


def _depth(c, by_item):
    for iid in c["items"]:
        it = by_item.get(iid) or {}
        d = it.get("dimensions") or {}
        for k in ("depth_m", "H_m", "H", "depth"):
            v = d.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return v
        sec = d.get("section_m") or d.get("schedule_m")
        if isinstance(sec, (list, tuple)) and len(sec) >= 2 and isinstance(sec[1], (int, float)):
            return sec[-1] if len(sec) >= 3 else sec[1]
    return None


# ====================================================================== COVERAGE / UNRESOLVED ledgers
def coverage_ledger(D, items, consumed, p):
    u = D["unit_m"]
    fam_items = Counter(i["family"] for i in items if i["trade"] == "CONCRETE")
    signals, findings = [], []
    for sid, rec in _plan_sheets(D):
        sl = rec.get("slab")
        if not sl:
            continue
        sh, org = rec["sheet"], rec["sheet"].get("origin") or (0.0, 0.0)
        tot = sum(f["area_m2"] for f in sl["faces"])
        reg = Counter()
        for f in sl["faces"]:
            reg[f.get("region") or f.get("class")] += f["area_m2"]
        signals.append({"LEDGER": "COVERAGE", "SHEET": sid, "STOREY": sh.get("storey"), "STATE": "REGIONS",
                        "TOTAL_M2": round(tot, 3), "REGIONS_M2": {k: round(v, 3) for k, v in sorted(reg.items())}})
        panel = sum(f["area_m2"] for f in sl["faces"] if consumed.get((sid, f["face_id"])))
        held = panel + sum(f["area_m2"] for f in sl["faces"] if f.get("class") in ("BEAM", "COLUMN"))
        share = held / tot if tot else 0.0
        signals[-1].update(MEASURED_PANEL_M2=round(panel, 3), HELD_SHARE=round(share, 3))
        if tot >= 10.0 and share < p["SLAB_COVERAGE_MIN"]:
            findings.append(_finding(
                "SLAB_COVERAGE_LOW", sid, sh, _local_box(_bbox([q for f in sl["faces"] for q in f["polygon"]]), org, u),
                "HIGH", family="SLABS", confidence="HIGH",
                evidence=f"the {sh.get('storey')} plan encloses {tot:.1f} m2; panels held by items {panel:.1f} m2 and "
                         f"member strips together hold only {share:.0%} (regions: " +
                         ", ".join(f"{k} {v:.1f}" for k, v in sorted(reg.items()) if v) + ")",
                magnitude={"enclosed_m2": round(tot, 3), "held_m2": round(held, 3), "held_share": round(share, 3)}))
        for f in sl["faces"]:
            region, cls = f.get("region"), f.get("class")
            c = consumed.get((sid, f["face_id"]))
            why = None
            if (cls == "OPENING" or region == "OPENING") and tot and f["area_m2"] >= p["OPENING_SHARE_MAX"] * tot:
                why = "OPENING_DOMINANT"
            elif region in ("DETAIL", "UNRESOLVED") and not c:
                why = region
            elif region == "STAIR_ZONE" and not fam_items.get("STAIRS"):
                why = "STAIR_ZONE"
            elif cls == "OPEN_BOUNDARY" and not c:
                why = "OPEN_BOUNDARY"
            if not why:
                continue
            t = f.get("t_m") or f.get("t_sheet_uniform_m")
            vol = (f["area_m2"] * t, f["area_m2"] * t, f"region area x the sheet's slab thickness {t:g} m") \
                if t and why in ("UNRESOLVED", "OPEN_BOUNDARY") else None
            fam = "STAIRS" if why == "STAIR_ZONE" else "SLABS"
            kind = "STAIR_NOT_MEASURED" if why == "STAIR_ZONE" else "REGION_EXCLUDED"
            mag = {"area_m2": round(f["area_m2"], 3)}
            extra = ""
            if why == "STAIR_ZONE":
                # lines radiating from the centre of a circle drawn in the zone: dome ribs or a spiral stair
                ents = (p.get("_ents") or {}).get(sid, [])
                inside = [e for e in ents if MD.point_in_poly(sum(x for x, _ in e["pts"]) / len(e["pts"]),
                                                              sum(y for _, y in e["pts"]) / len(e["pts"]),
                                                              f["polygon"])]
                rad = _radial([e for e in inside if e["type"] == "LINE"],
                              [e for e in ents if e["type"] in ("CIRCLE", "ARC") and
                               MD.point_in_poly(e["c"][0], e["c"][1], f["polygon"])])
                if rad and rad["spokes"] >= 6:
                    kind, fam = "DRAWN_NOT_MEASURED", None
                    words, _ = _note_words()
                    votes = Counter()
                    for t in [t for t in D["model"]["texts"] if t.get("sheet") == sid and
                              len(t["norm"]) <= p["DEPENDENCY_NOTE_MAX_CHARS"] and
                              MD.point_in_poly(t["x"], t["y"], f["polygon"])]:
                        for nf in note_families(t["norm"], words):
                            votes[nf] += 3
                    for e in inside:
                        lf = layer_family(e["layer"])
                        if lf and lf not in MEMBER_FAMILIES:
                            votes[lf] += 1
                    ranked = votes.most_common(2)
                    if ranked and (len(ranked) == 1 or ranked[0][1] > ranked[1][1]) and ranked[0][0] in ("DOMES",
                                                                                                        "STAIRS"):
                        fam = ranked[0][0]
                        kind = "STAIR_NOT_MEASURED" if fam == "STAIRS" else kind
                    mag.update(radial_spokes=rad["spokes"], radial_r_m=round(rad["r"] * u, 3))
                    extra = (f"; its {rad['spokes']} lines radiate from the centre of a {rad['r'] * u:.2f} m circle: "
                             "dome ribs or a spiral stair (could be DOMES or STAIRS)")
            findings.append(_finding(kind, sid, sh, _local_box(_bbox(f["polygon"]), org, u),
                                     "HIGH" if f["area_m2"] >= 2.0 else "MEDIUM", family=fam, confidence="HIGH" if fam
                                     else "LOW", evidence=f"face {f['face_id']} {f['area_m2']:.2f} m2 region {why} "
                                                          f"({_ascii(f.get('region_reason'), 50)}); no item" + extra,
                                     magnitude=mag, volume=vol, refs=f["face_id"]))
    return signals, findings


def unresolved_ledger(items):
    agg = defaultdict(lambda: {"n": 0, "lo": 0.0, "hi": 0.0, "ids": []})
    for i in items:
        if i["trade"] == "CONCRETE" and i["category"] == "UNRESOLVED":
            a = agg[(i["family"], i["storey"], i.get("blocker") or "")]
            a["n"] += 1
            a["lo"] += i.get("exposure_low") or 0.0
            a["hi"] += i.get("exposure_high") or 0.0
            a["ids"].append(i["item_id"])
    findings = []
    for (fam, st, blk), a in sorted(agg.items()):
        findings.append(_finding("UNRESOLVED_ITEMS", "", None, None, "MEDIUM" if a["hi"] < 1.0 else "HIGH",
                                 family=ITEM_FAMILY.get(fam) or fam, confidence="HIGH", storey=st,
                                 evidence=f"{a['n']} {fam} items on {st} held UNRESOLVED ({_ascii(blk, 40)})",
                                 magnitude={"items": a["n"]}, volume=(a["lo"], a["hi"], "the items' own exposure"),
                                 items=a["ids"][:6], refs=_ascii(blk, 40)))
    return findings


# ====================================================================== SCOPE checklist
POPULATION_OF = {
    "FOOTINGS": "ISOLATED_FOOTING", "GROUND_BEAMS": "GROUND_BEAM", "COLUMNS": "COLUMN", "BEAMS": "SIMPLE_BEAM",
    "SLABS": "SOLID_SLAB", "STAIRS": "STAIR", "LIFT": "LIFT_PIT", "POOL": "POOL", "WATER_TANK": "WATER_TANK",
    "DOMES": "DOME", "BOUNDARY_WALL": "BOUNDARY_WALL", "PARAPETS": "PARAPET", "WALLS": "STRUCTURAL_WALL",
    "PLANTED_COLUMN": "PLANTED_COLUMN", "CANTILEVER": "CANTILEVER", "PLANTER": "PLANTER_STRUCTURAL_ELEMENT",
    "SLAB_STEP": "OTHER_SPECIAL_RC_DETAIL", "RAMP": "OTHER_SPECIAL_RC_DETAIL", "UNKNOWN": "OTHER_SPECIAL_RC_DETAIL",
}


def scope_checklist(items, findings, note_signals):
    from engine.source import structural_population_discovery as SPD
    measured = Counter()
    unresolved = Counter()
    for i in items:
        if i["trade"] != "CONCRETE":
            continue
        f = ITEM_FAMILY.get(i["family"])
        if i["family"] == "COLUMNS" and "PC@" in i["component_id"]:
            f = "PLANTED_COLUMN"
        if i["family"] == "COLUMNS" and i["storey"] == "FOUNDATION":
            measured["NECK"] += 1 if i["category"] != "UNRESOLVED" else 0
        if i["family"] == "GROUND_SLAB":
            (measured if i["category"] != "UNRESOLVED" else unresolved)["GROUND_SLAB"] += 1
        if i["family"] == "LINTELS":
            (measured if i["category"] != "UNRESOLVED" else unresolved)["LINTEL"] += 1
        if "STRAP" in (i.get("source") or "") or ":FOUNDATION:BAND" in i["component_id"]:
            (measured if i["category"] != "UNRESOLVED" else unresolved)["STRAP"] += 1
        if f:
            (measured if i["category"] != "UNRESOLVED" else unresolved)[f] += 1
    open_by = defaultdict(list)
    for f in findings:
        if f["KIND"] in ("DRAWN_NOT_MEASURED", "LABEL_NOT_CONSUMED", "REFERENCED_NOT_DRAWN", "REGION_EXCLUDED",
                         "PLACED_NOT_SCHEDULED", "COLUMN_PRESENCE_NOT_ITEMIZED", "MEMBER_DETECTED_NOT_ITEMIZED",
                         "STAIR_NOT_MEASURED", "STOREY_PLAN_MISSING", "STOREY_COLUMN_BANDS_MISSING"):
            open_by[f["FAMILY"]].append(f)
    noted = {s["FAMILY"] for s in note_signals if s.get("STATE") and s["LEDGER"] == "NOTES" and s["TOKEN"] ==
             s["FAMILY"]}
    rows, ev = [], {}
    fams = ["FOOTINGS", "NECK", "STRAP", "GROUND_BEAMS", "GROUND_SLAB", "COLUMNS", "PLANTED_COLUMN", "BEAMS", "LINTEL",
            "SLABS", "CANTILEVER", "SLAB_STEP", "STAIRS", "LIFT", "POOL", "WATER_TANK", "DOMES", "WALLS",
            "BOUNDARY_WALL", "PARAPETS", "RAMP", "PLANTER", "UNKNOWN"]
    pop_of = dict(POPULATION_OF, NECK="NECK_PEDESTAL", STRAP="STRAP_BEAM", GROUND_SLAB="GROUND_SLAB", LINTEL="LINTEL")
    for fam in fams:
        m, ur, op = measured.get(fam, 0), unresolved.get(fam, 0), open_by.get(fam, [])
        drawn = [f for f in op if f["KIND"] != "REFERENCED_NOT_DRAWN"]
        if m and not (drawn or ur):
            st = "MEASURED"
        elif m:
            st = "PARTLY_MEASURED"
        elif ur:
            st = "HELD_UNRESOLVED"
        elif drawn:
            st = "DRAWN_NOT_MEASURED"
        elif op or fam in noted:
            st = "REFERENCED_NOT_DRAWN"
        else:
            st = "NO_EVIDENCE_CONFIRM_ABSENT"
        if fam == "UNKNOWN" and st == "NO_EVIDENCE_CONFIRM_ABSENT":
            continue
        vlo = sum(f["VOLUME_LOW_M3"] or 0 for f in op)
        vhi = sum(f["VOLUME_HIGH_M3"] or 0 for f in op)
        nov = sum(1 for f in op if f["VOLUME_HIGH_M3"] is None)
        rows.append({"FAMILY": fam, "POPULATION": pop_of.get(fam, "OTHER_SPECIAL_RC_DETAIL"), "STATE": st,
                     "MEASURED_ITEMS": m, "UNRESOLVED_ITEMS": ur, "OPEN_FINDINGS": len(op),
                     "FINDING_VOLUME_LOW_M3": round(vlo, 3), "FINDING_VOLUME_HIGH_M3": round(vhi, 3),
                     "FINDINGS_WITHOUT_VOLUME": nov})
        pop = pop_of.get(fam)
        if pop in SPD.ALL_POPULATIONS:
            prev = ev.get(pop)
            state = SPD.PRESENT if st in ("MEASURED", "PARTLY_MEASURED", "HELD_UNRESOLVED", "DRAWN_NOT_MEASURED") \
                else SPD.BLOCKED if st == "REFERENCED_NOT_DRAWN" else SPD.UNKNOWN
            if prev is None or SPD.STATES.index(state) < SPD.STATES.index(prev["state"]):
                ev[pop] = {"state": state, "refs": [f["FINDING_ID"] for f in op[:4]] or ([f"{m} items"] if m else []),
                           "why": st}
    return rows, SPD.discover(ev)


# ====================================================================== the pass
def assess(D, intake, items, *, risk=(), heights=None, family_coverage=None, params=None):
    """the completeness report of one route-G run. D: generic_route.detect(); intake: tools/urban_intake record;
    items: the run's items; risk: the route's coverage-risk records; heights: {storey: m}."""
    if not D or "sheets" not in D or "model" not in D:
        raise CompletenessError("assess needs the route's detection record D")
    p = _p(params)
    u = D["unit_m"]
    words, en = _note_words()
    members = _members(D)
    consumed = _consumption(D, items, members)
    g_sig, g_fnd, g_stats = geometry_ledger(D, intake or {}, members, consumed, p, words)
    m_sig, m_fnd = member_ledger(D, members, consumed, u)
    l_sig, l_fnd = label_ledger(D, items, members, consumed, p)
    s_sig, s_fnd = schedule_ledger(D, l_sig, intake)
    st_sig, st_fnd = storey_ledger(D, heights, items)
    v_sig, v_fnd = vertical_ledger(D, items, members, risk or (), heights, u, consumed)
    c_sig, c_fnd = coverage_ledger(D, items, consumed, p)
    n_sig, n_fnd = note_ledger(D, items, members, consumed, g_fnd + c_fnd, words, en, p)
    o_sig, o_fnd = overlap_ledger(D, members, consumed, items, p)
    u_fnd = unresolved_ledger(items)
    findings = g_fnd + m_fnd + l_fnd + s_fnd + st_fnd + v_fnd + n_fnd + o_fnd + c_fnd + u_fnd
    seen, uniq = set(), []
    for f in findings:
        if f["FINDING_ID"] in seen:
            continue
        seen.add(f["FINDING_ID"])
        uniq.append(f)
    findings = sorted(uniq, key=lambda f: (SEVERITY.index(f["SEVERITY"]), f["KIND"], f["SHEET"], f["FINDING_ID"]))
    scope, populations = scope_checklist(items, findings, n_sig)
    signals = g_sig + m_sig + l_sig + s_sig + st_sig + v_sig + n_sig + o_sig + c_sig
    scores = _scores(g_stats, l_sig, s_sig, m_sig, v_sig, findings, items, scope)
    return {"policy": POLICY_ID, "params": p, "findings": findings, "signals": signals, "scope": scope,
            "populations": populations, "scores": scores, "geometry_stats": {k: round(v, 3) for k, v in
                                                                              sorted(g_stats.items())},
            "rule": "a finding is a question for a person, never a quantity; no reference quantity is read; volumes "
                    "only from drawn geometry x a printed section / thickness, never a ratio"}


def _pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def _scores(g, labels, sched, mem, vert, findings, items, scope):
    rc = [i for i in items if i["trade"] == "CONCRETE" and i["family"] != "PLAIN_CONCRETE"]
    base = sum(i.get("base") or 0 for i in rc if i["category"] != "UNRESOLVED")
    conf = Counter()
    for i in rc:
        if i["category"] != "UNRESOLVED":
            conf[i.get("confidence")] += i.get("base") or 0
    in_plan = g.get("drawn_length_m", 0) - g.get("outside_plan_length_m", 0)
    lab = Counter(s["STATE"] for s in labels)
    sch = Counter(s["STATE"] for s in sched if s["STATE"] in ("PLACED", "NOT_PLACED"))
    mm = Counter(s["STATE"] for s in mem)
    vv = Counter(s["STATE"] for s in vert)
    fk = Counter(f["KIND"] for f in findings)
    fs = Counter(f["SEVERITY"] for f in findings)
    vlo = sum(f["VOLUME_LOW_M3"] or 0 for f in findings if f["KIND"] != "UNRESOLVED_ITEMS")
    vhi = sum(f["VOLUME_HIGH_M3"] or 0 for f in findings if f["KIND"] != "UNRESOLVED_ITEMS")
    ulo = sum(f["VOLUME_LOW_M3"] or 0 for f in findings if f["KIND"] == "UNRESOLVED_ITEMS")
    uhi = sum(f["VOLUME_HIGH_M3"] or 0 for f in findings if f["KIND"] == "UNRESOLVED_ITEMS")
    return {
        "geometry_explained_pct": _pct(g.get("explained_length_m", 0), in_plan),
        "geometry_unexplained_m": round(g.get("unexplained_length_m", 0), 2),
        "labels": dict(sorted(lab.items())),
        "labels_consumed_pct": _pct(lab.get("CONSUMED_BY_REFERENCE", 0) + lab.get("CONSUMED_BY_PROXIMITY", 0),
                                    sum(lab.values())),
        "schedule_rows_placed_pct": _pct(sch.get("PLACED", 0), sum(sch.values())),
        "members_itemized_pct": _pct(mm.get("HELD_BY_ITEM", 0), sum(mm.values())),
        "column_outlines_itemized_pct": _pct(vv.get("HELD_BY_ITEM", 0), sum(vv.values())),
        "findings_by_kind": dict(sorted(fk.items())), "findings_by_severity": dict(sorted(fs.items())),
        "scope_states": dict(sorted(Counter(r["STATE"] for r in scope).items())),
        "rc_measured_m3": round(base, 3),
        "rc_measured_by_confidence_m3": {k: round(v, 3) for k, v in sorted(conf.items(), key=lambda x: str(x[0]))},
        "unresolved_exposure_m3": (round(ulo, 3), round(uhi, 3)),
        "finding_volume_m3": (round(vlo, 3), round(vhi, 3)),
        "findings_without_volume": sum(1 for f in findings if f["VOLUME_HIGH_M3"] is None),
        "basis": "ratios of the run's own signals and records; finding volumes only where a printed section or "
                 "thickness binds; nothing here is added to any total",
    }


def policy_record():
    return {"policy": POLICY_ID, "params": PARAMS, "kinds": sorted(ACTION), "severity": list(SEVERITY),
            "rule": "every structural signal ends in one terminal state; an unexplained signal is a located finding; "
                    "an absent label is never an absent element (NO_EVIDENCE_CONFIRM_ABSENT)"}
