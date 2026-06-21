"""Generate the raw volume and monthly cost planning test files used during development."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "mock_volume_input.csv"
PRICE_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "mock_price_input.csv"
COST_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "mock_cost_input.csv"
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


def get_plant_for_ship_to(ship_to_id: str) -> str:
    """Resolve a deterministic manufacturing plant supplying a given ship-to location."""
    mapping = {
        "SHIP-001-NL": "PLANT-01",
        "SHIP-001-BE": "PLANT-01",
        "SHIP-014-DE": "PLANT-02",
        "SHIP-014-PL": "PLANT-02",
        "SHIP-027-FR": "PLANT-03",
        "SHIP-027-BE": "PLANT-03",
        "SHIP-038-LT": "PLANT-04",
        "SHIP-038-EE": "PLANT-04",
        "SHIP-052-ES": "PLANT-05",
        "SHIP-052-PT": "PLANT-05",
        "SHIP-073-SE": "PLANT-06",
        "SHIP-073-DK": "PLANT-06",
    }
    return mapping.get(ship_to_id, "PLANT-01")


def month_label(index: int) -> str:
    """Return a YYYY-MM monthly period label within the 2026 planning year."""
    month = index % 12 + 1
    return date(2026, month, 1).strftime("%Y-%m")


def planned_volume_for_row(index: int) -> Decimal:
    """Return the row volume in tons while preserving the exact target total."""
    if index < 2_000:
        return Decimal("25.667")
    return Decimal("25.666")


def generate_rows() -> list[dict[str, str]]:
    """Build deterministic raw input rows for volume planning tests."""
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
                "Plant": get_plant_for_ship_to(ship_to_id),
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


def get_base_price(material_id: str, sold_to_id: str, ship_to_id: str) -> Decimal:
    """Compute a deterministic mock unit price per ton."""
    base_map = {
        "MAT-1001": Decimal("250.00"),
        "MAT-2004": Decimal("315.50"),
        "MAT-3098": Decimal("185.00"),
        "MAT-4120": Decimal("420.25"),
        "MAT-5185": Decimal("95.00"),
    }
    base = base_map.get(material_id, Decimal("100.00"))
    cust_num = int(sold_to_id.split("-")[1])
    ship_num = sum(ord(c) for c in ship_to_id) % 5
    return base + Decimal(f"{cust_num * 3.50 + ship_num * 1.25:.2f}")


def generate_price_rows() -> list[dict[str, str]]:
    """Build deterministic raw price records for the planning year combinations."""
    rows = []
    # Generate one price for every unique combination of material, customer, and ship-to
    for _, material_id in MATERIALS:
        for sold_to_id, _ in CUSTOMERS:
            for ship_to_id, _ in SHIP_TO_BY_CUSTOMER[sold_to_id]:
                price = get_base_price(material_id, sold_to_id, ship_to_id)
                rows.append(
                    {
                        "Sold to ID": sold_to_id,
                        "Ship to ID": ship_to_id,
                        "Material ID": material_id,
                        "Price": f"{price:.2f}",
                    }
                )
    return rows


def write_raw_price_test_file() -> Path:
    """Write the raw pricing CSV file used as input source."""
    PRICE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_price_rows()

    with PRICE_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return PRICE_OUTPUT_PATH


def get_base_cost(plant_id: str, material_id: str, period_str: str) -> Decimal:
    """Compute a deterministic mock unit raw material cost per ton."""
    base_map = {
        "MAT-1001": Decimal("150.00"),
        "MAT-2004": Decimal("180.50"),
        "MAT-3098": Decimal("110.00"),
        "MAT-4120": Decimal("240.25"),
        "MAT-5185": Decimal("55.00"),
    }
    base = base_map.get(material_id, Decimal("60.00"))
    plant_num = int(plant_id.split("-")[1])
    month_num = int(period_str.split("-")[1])
    return base + Decimal(f"{plant_num * 5.75 + month_num * 1.50:.2f}")


def generate_cost_rows() -> list[dict[str, str]]:
    """Build deterministic raw monthly RM cost records for the planning year combinations."""
    rows = []
    # Generate a monthly cost for each Plant, Material ID, and Period combination
    plants = [f"PLANT-{i:02d}" for i in range(1, 7)]
    periods = [f"2026-{m:02d}" for m in range(1, 13)]

    for plant in plants:
        for _, material_id in MATERIALS:
            for period in periods:
                cost = get_base_cost(plant, material_id, period)
                rows.append(
                    {
                        "Plant": plant,
                        "Material ID": material_id,
                        "Period": period,
                        "Cost": f"{cost:.2f}",
                    }
                )
    return rows


def write_raw_cost_test_file() -> Path:
    """Write the raw monthly cost CSV file used as input source."""
    COST_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_cost_rows()

    with COST_OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return COST_OUTPUT_PATH


if __name__ == "__main__":
    vol_path = write_raw_volume_test_file()
    price_path = write_raw_price_test_file()
    cost_path = write_raw_cost_test_file()
    print(f"Generated volume file: {vol_path}")
    print(f"Generated price file: {price_path}")
    print(f"Generated cost file: {cost_path}")
