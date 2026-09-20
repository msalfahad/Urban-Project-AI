"""PA08_QORTUBA_BLIND_01 in order: blind engine run -> inventory -> reading -> takeoff -> consistency -> defects -> freeze."""

from __future__ import annotations

from research.qs_wall_treatment_01.pa08.qortuba import blind, consistency, defects, freeze, inventory, reading, takeoff


def main():
    blind.main(); inventory.main(); reading.main(); takeoff.build(); consistency.main(); defects.main(); freeze.main()


if __name__ == "__main__":
    main()
