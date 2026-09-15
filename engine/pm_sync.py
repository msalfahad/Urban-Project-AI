"""E14 — PM Sync.

Writes an approved BOQ into Urban Projects Manager (the Flutter web app). Both
systems run on the same Firestore, so — as the project overview says — this is a
*write*, not an integration.

The web app stores BOQ lines at `projects/{projectId}/boqItems/{itemId}`, each
document carrying a `formulaType` + `measurements` map that the app's own
BoqFormulaEngine turns into a quantity. So this module does two things:

1. Translate our measurement records (as A1/A2 produce them, unit + dimensions)
   into the app's `formulaType` + `measurements` shape, choosing the mapping so
   the app computes exactly the quantity we intended (mirrored in
   `boq_formula.py` and asserted in tests).
2. Emit a document with exactly the fields the app's `BoqItemModel.toMap()`
   expects, and write it through an injectable writer — a plain function in
   tests, `firebase-admin` in production.

Nothing here calls a model, and nothing here invents a number: the rates and
measurements come in already decided; the app does the multiplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .boq_formula import compute_quantity

# The exact keys BoqItemModel.toMap() writes, so a produced document round-trips
# through the app with no surprises. Kept as a constant so a test can assert we
# match the app's model precisely.
BOQ_ITEM_FIELDS = {
    "projectId", "groupId", "packageId", "packageName", "templateId",
    "name", "unit", "formulaType", "measurements", "costRate", "sellingRate",
    "isDeleted", "linkedCostItemId", "notes", "categoryId", "costTypeId",
    "photoUrl", "createdAt", "updatedAt",
}


@dataclass
class ApprovedBoqLine:
    """One approved BOQ line, ready to write into the app.

    `count` and `dimensions_m` are as A1/A2 emit them (dimensions are lengths in
    metres). `unit` is the app-facing unit label (e.g. 'm2', 'm', 'no'). Rates
    are already set by the Rate Library and approved by a human.
    """

    project_id: str
    group_id: str
    package_id: str
    package_name: str
    name: str
    unit: str
    count: float
    dimensions_m: list[float]
    cost_rate: float = 0.0
    selling_rate: float = 0.0
    notes: str | None = None
    category_id: str | None = None
    cost_type_id: str | None = None


def measurement_to_formula(count: float, dimensions_m: list[float]) -> tuple[str, dict]:
    """Map a count + dimensions to the app's (formulaType, measurements).

    Chosen so the app's BoqFormulaEngine reproduces `count * product(dimensions)`:

    - 0 dimensions            -> 'simple', qty = count
    - 2 dims and count == 1   -> 'area', {length, width}   (app: length*width)
    - 3 dims and count == 1   -> 'volume', {length, width, height}
    - anything else           -> 'simple', qty precomputed (count * product)

    The 'simple' fallback is used whenever the app's geometric formulas cannot
    represent the case (a linear run, or several identical instances), because
    'simple' takes the quantity directly and the multiplication we did is plain
    deterministic code — not a model guess.
    """
    dims = list(dimensions_m)
    if not dims:
        return "simple", {"qty": float(count)}
    if count == 1 and len(dims) == 2:
        return "area", {"length": float(dims[0]), "width": float(dims[1])}
    if count == 1 and len(dims) == 3:
        return "volume", {
            "length": float(dims[0]),
            "width": float(dims[1]),
            "height": float(dims[2]),
        }
    qty = float(count)
    for d in dims:
        qty *= float(d)
    return "simple", {"qty": qty}


def to_boq_item_doc(line: ApprovedBoqLine, *, now: datetime | None = None) -> dict[str, Any]:
    """Build a Firestore document matching the app's BoqItemModel.toMap().

    Returns a plain dict; `createdAt`/`updatedAt` are timezone-aware datetimes,
    which firebase-admin stores as Firestore Timestamps.
    """
    now = now or datetime.now(timezone.utc)
    formula_type, measurements = measurement_to_formula(line.count, line.dimensions_m)
    return {
        "projectId": line.project_id,
        "groupId": line.group_id,
        "packageId": line.package_id,
        "packageName": line.package_name,
        "templateId": None,
        "name": line.name,
        "unit": line.unit,
        "formulaType": formula_type,
        "measurements": measurements,
        "costRate": float(line.cost_rate),
        "sellingRate": float(line.selling_rate),
        "isDeleted": False,
        "linkedCostItemId": None,
        "notes": line.notes,
        "categoryId": line.category_id,
        "costTypeId": line.cost_type_id,
        "photoUrl": None,
        "createdAt": now,
        "updatedAt": now,
    }


def expected_quantity(line: ApprovedBoqLine) -> float:
    """The quantity the app will compute for this line — count * product(dims)."""
    formula_type, measurements = measurement_to_formula(line.count, line.dimensions_m)
    return compute_quantity(formula_type, measurements)


# A writer takes (collection_path, document_dict) and persists it, returning the
# new document id. Injected so this module is testable with no Firestore.
Writer = Callable[[str, dict], str]


@dataclass
class SyncResult:
    written: list[str] = field(default_factory=list)  # document ids / paths


def sync_boq(
    lines: list[ApprovedBoqLine],
    writer: Writer,
    *,
    now: datetime | None = None,
) -> SyncResult:
    """Write approved BOQ lines to `projects/{projectId}/boqItems`.

    Each line becomes one document under its project's boqItems subcollection —
    the exact path the web app reads. `writer` is `firestore_writer` in
    production and a capturing stub in tests.
    """
    result = SyncResult()
    for line in lines:
        doc = to_boq_item_doc(line, now=now)
        path = f"projects/{line.project_id}/boqItems"
        doc_id = writer(path, doc)
        result.written.append(doc_id)
    return result


def firestore_writer(db: Any) -> Writer:
    """Build a Writer backed by firebase-admin Firestore.

    Usage (production, once a service account is configured):

        import firebase_admin
        from firebase_admin import credentials, firestore
        firebase_admin.initialize_app(credentials.Certificate("sa.json"))
        writer = firestore_writer(firestore.client())
        sync_boq(lines, writer)

    Kept as a factory so the heavy dependency is never imported in tests.
    """

    def _write(collection_path: str, document: dict) -> str:
        ref = db.collection(collection_path).document()
        ref.set(document)
        return ref.id

    return _write
