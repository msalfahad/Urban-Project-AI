"""Qortuba regression for Alsenan Phase A3: the Qortuba RC1 registers rebuilt by the CURRENT engine (rc1_qortuba.py into a
scratch directory) are compared key by key with the frozen tests/rc1/registers (same comparison as Phase A2). Qortuba
files are never edited.

    python3 research/external_engine_lab/alsenan_a3_qortuba_regression.py <rebuilt_register_dir> <a3_register_dir>

Writes QORTUBA_REGRESSION.json into the A3 register directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import alsenan_a2_qortuba_regression as QR2                                       # noqa: E402


def compare(rebuilt: Path) -> dict:
    rec = QR2.compare(Path(rebuilt))
    rec["SCHEMA"] = "URBAN_ALSENAN_A3_QORTUBA_REGRESSION_V1"
    rec["rule"] = ("Qortuba is frozen as RC1_REFERENCE; the A3 additions (STRUCTURAL_SCHEDULE_QTO_V1, the CURVED_GLAZING / "
                   "COUNTER_RUN / WALL_END_CAP / door-frame motifs of entity-role inference) run only where the "
                   "entity-role engine runs, so every Qortuba quantity must stay unchanged; Qortuba files are never "
                   "edited")
    return rec


def main(rebuilt, a3dir):
    rec = compare(Path(rebuilt))
    Path(a3dir, "QORTUBA_REGRESSION.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("state", "registers", "identical", "changed", "extra")}, indent=1))
    return rec


if __name__ == "__main__":
    main(*sys.argv[1:3])
