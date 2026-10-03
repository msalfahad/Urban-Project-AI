"""E80 — one table per merged blob: what would divide it, and what is there.

The leak map says where free space crossed. The patch proposer says what
kind of repair each crossing needs. The stroke classifier says what is drawn
at it. Separately those are three reports; together they are a work list.

Ranked by what fixing each separator UNLOCKS — rooms, then a frozen
control, then downstream quantity impact — never by the separator's length.
One separator that divides a 32-label component is worth more than fifty
metres of stroke elsewhere.

Every row carries its CONFIDENCE and its EFFECT WHEN REPAIRED, and the
effect is a measured counterfactual where one has been run and an explicit
NOT_MEASURED where it has not. A predicted effect presented as a measured
one is how a work list becomes a wish list.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# What the drawing has at the separator.
REP_ACCEPTED_BAND = "ACCEPTED_TWO_FACE_BAND"
REP_FRAGMENTED = "FRAGMENTED_MATE_ONLY"
REP_SINGLE_LINE = "SINGLE_LINE_EXISTENCE_SUPPORTED_ONLY"
REP_UNRESOLVED_STROKE = "UNRESOLVED_STROKE_ONLY"
REP_PORTAL = "PORTAL_CANDIDATE"
REP_NOTHING = "NOTHING_DRAWN"

CONF_HIGH = "HIGH"
CONF_MEDIUM = "MEDIUM"
CONF_LOW = "LOW"

NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class SeparatorRow:
    separator_id: str
    space_geometry_id: str
    spaces_divided: tuple[str, ...]
    representation: str
    wall_evidence: tuple[str, ...]
    junction_patch_needed: bool
    junction_patch_id: str
    single_line_involved: bool
    fragmented_mate_involved: bool
    portal_involved: bool
    rooms_in_the_component: int
    controls_unlocked: tuple[str, ...]
    confidence: str
    effect_when_repaired: str
    repair_class: str = ""
    passage_width_mm: float = 0.0
    why: str = ""

    @property
    def rank_key(self) -> tuple:
        # Rooms unlocked, then a frozen control, then quantity impact — and
        # NOT the separator's length.
        return (-self.rooms_in_the_component, -len(self.controls_unlocked),
                -self.passage_width_mm)

    def record(self) -> dict:
        return {
            "separator_id": self.separator_id,
            "space_geometry_id": self.space_geometry_id,
            "spaces_it_would_divide": list(self.spaces_divided),
            "current_representation": self.representation,
            "wall_evidence": list(self.wall_evidence),
            "junction_patch_needed": self.junction_patch_needed,
            "junction_patch_id": self.junction_patch_id,
            "single_line_wall_involved": self.single_line_involved,
            "fragmented_mate_involved": self.fragmented_mate_involved,
            "portal_involved": self.portal_involved,
            "rooms_in_the_merged_component": self.rooms_in_the_component,
            "frozen_controls_unlocked": list(self.controls_unlocked),
            "confidence": self.confidence,
            "effect_when_repaired": self.effect_when_repaired,
            "repair_class": self.repair_class,
            "passage_width_mm": round(self.passage_width_mm, 1),
            "why": self.why,
        }


@dataclass
class Table:
    rows: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        from collections import Counter
        ranked = sorted(self.rows, key=lambda r: r.rank_key)
        return {
            "separators": len(self.rows),
            "by_representation": dict(Counter(
                r.representation for r in self.rows)),
            "by_repair_class": dict(Counter(
                r.repair_class for r in self.rows if r.repair_class)),
            "by_confidence": dict(Counter(r.confidence for r in self.rows)),
            "junction_patches_needed": sum(
                1 for r in self.rows if r.junction_patch_needed),
            "ranked": [r.record() for r in ranked],
            "ranking": ("rooms in the merged component, then frozen "
                        "controls unlocked, then passage width. NOT the "
                        "separator's length"),
            "effect_column": (
                "a measured counterfactual where one has been run, and "
                f"{NOT_MEASURED} where it has not. A predicted effect "
                "presented as a measured one is how a work list becomes a "
                "wish list"),
            "notes": dict(self.notes),
        }


def build(leaks, *, labels_inside, patches=(), strokes=(), controls=(),
          counterfactual=None, min_component_labels: int = 2) -> Table:
    """Join the leak map, the patch proposals and the stroke classes."""
    from engine.unpaired_strokes import (FRAGMENTED_MATE,
                                         SINGLE_LINE_EXISTENCE_SUPPORTED)

    by_leak = {p.provenance.get("leak_id"): p for p in patches
               if p.provenance.get("leak_id")}
    stroke_class = {s.stroke_id: s.stroke_class for s in strokes}
    control_set = set(controls)

    table = Table()
    for lk in leaks:
        ids = tuple(labels_inside.get(lk.space_geometry_id, ()))
        if len(ids) < min_component_labels:
            continue
        patch = by_leak.get(lk.leak_id)
        at_gap = tuple(getattr(lk, "strokes_at_aperture", ())
                       or getattr(lk, "unpaired_strokes_at_frontier", ()))
        classes = {stroke_class.get(i) for i in at_gap}
        single = SINGLE_LINE_EXISTENCE_SUPPORTED in classes
        frag = FRAGMENTED_MATE in classes
        portal = bool(getattr(lk, "portals_at_frontier", ()))

        rep = _representation(lk, single, frag, classes, portal)
        conf, why = _confidence(lk, patch, rep)
        effect = _effect(lk, patch, counterfactual)
        table.rows.append(SeparatorRow(
            separator_id=lk.leak_id,
            space_geometry_id=lk.space_geometry_id,
            spaces_divided=(lk.space_a, lk.space_b),
            representation=rep,
            wall_evidence=tuple(getattr(lk, "bands_at_frontier", ())),
            junction_patch_needed=bool(
                patch is not None and patch.is_validated),
            junction_patch_id=(patch.patch_id if patch is not None else ""),
            single_line_involved=single, fragmented_mate_involved=frag,
            portal_involved=portal,
            rooms_in_the_component=len(ids),
            controls_unlocked=tuple(sorted(
                control_set & {lk.space_a, lk.space_b})),
            confidence=conf, effect_when_repaired=effect,
            repair_class=(patch.gap_repair_class if patch is not None
                          else ""),
            passage_width_mm=getattr(lk, "passage_width_mm", 0.0) or 0.0,
            why=why))
    table.notes["leaks_examined"] = len(list(leaks))
    return table


def _representation(lk, single, frag, classes, portal) -> str:
    if getattr(lk, "bands_at_frontier", ()):
        return REP_ACCEPTED_BAND
    if portal:
        return REP_PORTAL
    if single:
        return REP_SINGLE_LINE
    if frag:
        return REP_FRAGMENTED
    if classes:
        return REP_UNRESOLVED_STROKE
    return REP_NOTHING


def _confidence(lk, patch, rep) -> tuple[str, str]:
    if patch is not None and patch.is_validated:
        return CONF_HIGH, (
            "two independent evidence families support a physical junction "
            "here, and the patch that would close it is named")
    if rep == REP_NOTHING:
        return CONF_LOW, (
            "nothing is drawn at this separator, so there is nothing to "
            "recover. Either the drawing leaves it open or the wall is in a "
            "representation this engine does not read")
    if rep in (REP_FRAGMENTED, REP_SINGLE_LINE):
        return CONF_MEDIUM, (
            "wall-like strokes lie at this separator with raster support, "
            "so something is drawn — but what it is dimensionally is not "
            "established, and a single stroke creates no material geometry")
    if rep == REP_PORTAL:
        return CONF_MEDIUM, (
            "a portal candidate sits here. If its existence is validated "
            "its barrier closes the separator; if not, the wall behind it "
            "was never extracted")
    return CONF_LOW, "nothing available raises this above a guess"


def _effect(lk, patch, counterfactual) -> str:
    if counterfactual is None:
        return NOT_MEASURED
    applied = set(counterfactual.get("repairs_applied", ()))
    if patch is None or patch.patch_id not in applied:
        return NOT_MEASURED
    d = counterfactual.get("delta", {})
    return (f"MEASURED: single-room candidates "
            f"{d.get('single_room_candidates', 0):+d}, largest component "
            f"{d.get('largest_blob_labels', 0):+d} label(s) "
            f"({counterfactual.get('verdict', '')})")
