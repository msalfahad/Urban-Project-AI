"""Generic ingestion contract (PA05).

SOURCE_DOCUMENT -> SHEET / VIEW -> RAW_ENTITY -> CANONICAL_GEOMETRIC_FEATURE
-> TOPOLOGICAL_SITE / RELATION -> PHYSICAL_SPACE -> FUNCTIONAL_ZONE ->
TRADE_MEASUREMENT_ZONE -> QUANTITY INPUTS.

Nothing in this package may carry a project's coordinates, entity ids, room
names, file paths or dimensions; a project enters only as input data (see
tests/test_pa05_ingest.py::test_no_project_constants_in_engine).
"""

ENGINE_VERSION = "ingest-0.1.0"
