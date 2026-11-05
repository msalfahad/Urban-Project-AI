"""T-517 on the training villa: the pool-court build-up layer table (POOLCOURT-550 open sky + the held ledge), the
edge / upstand rows, and the cement : sand census check of the proposed hosts. Research, unwired; values come from
the pinned merged inputs and, for the finish hatch, from the private drawing at run time (absent -> HELD)."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t517_inputs as INP                 # noqa: E402
import t517_poolcourt_buildup as B        # noqa: E402


def build(dxf=None, pin=True, use_drawing=True):
    hm = INP.measure_hatch(dxf) if use_drawing else None
    open_sky, ledge = INP.zones(None if hm is None else hm["hatch_m2"], pin)
    rows = B.ledger(open_sky, INP.PRINTS) + B.ledger(ledge, INP.PRINTS)
    edges = B.edge_rows(open_sky, INP.PRINTS) + B.edge_rows(ledge, INP.PRINTS)
    census = B.census_check(rows, pins=pin)
    screed_area = open_sky["face_m2"]["value"]
    conv = {k: tuple(v) + ([],) for k, v in census["conversions"].items()}
    return {"schema": B.SCHEMA, "guard_class": B.GUARD_CLASS, "rules": list(B.RULES), "hatch": hm,
            "rows": rows, "edge_rows": edges, "census": census,
            "sensitivity_falls_screed": B.sensitivity_per_cm(screed_area, conv),
            "released_quantities_changed": 0}
