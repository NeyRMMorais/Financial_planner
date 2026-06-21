"""Generate the raw volume planning test file used during development."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "mock_volume_input.csv"
ROW_COUNT = 3_000
TARGET_VOLUME_TONS = Decimal("77000.000")


MATERIALS = [
    ("Premium Resin A", "MAT-1001"),
    ("Industrial Additive B", "MAT-2004"),
    ("Specialty Compound C", "MAT-3098"),
    ("Packaging Film D", "MAT-4120"),
    ("Base Polymer E", "MAT-5185"),
]

CUSTOMERS = [
    ("CUST-001", "Northstar Manufacturing BV"),
    ("CUST-014", "HelioPack GmbH"),
    ("CUST-027", "Atlas Components SA"),
    ("CUST-038", "Baltic Industrial Group"),
    ("CUST-052", "Iberia Consumer Goods SL"),
    ("CUST-073", "Nordic Materials AB"),
]

SHIP_TO_BY_CUSTOMER = {
    "CUST-001": [
        ("SHIP-001-NL", "Northstar Manufacturing BV - Rotterdam Plant"),
        ("SHIP-001-BE", "Northstar Manufacturing BV - Antwerp DC"),
    ],
    "CUST-014": [
        ("SHIP-014-DE", "HelioPack GmbH - Hamburg Site"),
        ("SHIP-014-PL", "HelioPack GmbH - Poznan Warehouse"),
    ],
    "CUST-027": [
        ("SHIP-027-FR", "Atlas Components SA - Lyon Warehouse"),
        ("SHIP-027-BE", "Atlas Components SA - Antwerp DC"),
    ],
    "CUST-038": [
        ("SHIP-038-LT", "Baltic Industrial Group - Kaunas Plant"),
        ("SHIP-038-EE", "Baltic Industrial Group - Tallinn Hub"),
    ],
    "CUST-052": [
        ("SHIP-052-ES", "Iberia Consumer Goods SL - Valencia Site"),
        ("SHIP-052-PT", "Iberia Consumer Goods SL - Porto DC"),
    ],
    "CUST-073": [
        ("SHIP-073-SE", "Nordic Materials AB - Malmo Plant"),
        ("SHIP-073-DK", "Nordic Materials AB - Aarhus Hub"),
    ],
}


def month_label(index: int) -> str:
    """Return a YYYY-MM monthly period label within the 2026 planning year."""

    month = index % 12 + 1
    return date(2026, month, 1).strftime("%Y-%m")


def planned_volume_for_row(index: int) -> Decimal:
    """Return the row volume in tons while preserving the exact target total.

    Formula:
        2,000 rows use 25.667 tons and 1,000 rows use 25.666 tons.
        This gives ``(2000 * 25.667) + (1000 * 25.666) = 77000.000``.
    """

    if index < 2_000:
        return Decimal("25.667")
    return Decimal("25.666")


def generate_rows() -> list[dict[str, str]]:
    """Build deterministic raw input rows for volume planning tests.

    Business logic:
        Each row is a source-style demand record by material, month, sold-to
        customer, and ship-to receiving entity. Values are emitted as strings so
        CSV readers can convert volume to ``Decimal`` instead of binary floats.
    """

    rows = []
    for index in range(ROW_COUNT):
        material, material_id = MATERIALS[index % len(MATERIALS)]
        sold_to_id, sold_to = CUSTOMERS[(index // len(MATERIALS)) % len(CUSTOMERS)]
        ship_to_id, ship_to = SHIP_TO_BY_CUSTOMER[sold_to_id][
            (index // (len(MATERIALS) * len(CUSTOMERS))) % 2
        ]

        rows.append(
            {
                "Material": material,
                "Material ID": material_id,
                "Date": month_label(index),
                "Sold to ID": sold_to_id,
                "Sold to": sold_to,
                "Ship to ID": ship_to_id,
                "Ship to": ship_to,
                "Volume": f"{planned_volume_for_row(index):.3f}",
            }
        )

    return rows


def write_raw_volume_test_file() -> Path:
    """Write the raw CSV file used as the first development input source."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows()

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total_volume = sum(Decimal(row["Volume"]) for row in rows)
    if len(rows) != ROW_COUNT:
        raise ValueError(f"Generated {len(rows)} rows, expected {ROW_COUNT}.")
    if total_volume != TARGET_VOLUME_TONS:
        raise ValueError(
            f"Generated {total_volume} tons, expected {TARGET_VOLUME_TONS}."
        )

    return OUTPUT_PATH


if __name__ == "__main__":
    output_path = write_raw_volume_test_file()
    print(output_path)
