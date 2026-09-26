"""Pydantic schemas for the FastAPI API layer."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ScenarioCreate(BaseModel):
    name: str = Field(..., description="Unique name of the scenario")
    base_scenario: Optional[str] = Field(None, description="Optional parent scenario to clone from")
    description: str = Field("", description="Optional description/notes for the scenario")


class ScenarioMetadataResponse(BaseModel):
    name: str
    created_at: str
    base_scenario: Optional[str]
    description: str
    change_log: List[str]
    files_status: dict[str, bool]



class PriceOverrideInput(BaseModel):
    material_id: str = Field(..., alias="Material ID")
    sold_to_id: str = Field(..., alias="Sold to ID")
    ship_to_id: str = Field(..., alias="Ship to ID")
    date: str = Field(..., alias="Date", description="Period format, e.g. 2026-01")
    price: Decimal = Field(..., alias="Price")

    model_config = ConfigDict(populate_by_name=True)


class SimulationMetrics(BaseModel):
    total_volume: Decimal
    total_revenue_usd: Decimal
    total_revenue_lc: Decimal
    total_rm_cost_usd: Decimal
    total_rm_cost_lc: Decimal
    total_var_cost_usd: Decimal
    total_var_cost_lc: Decimal
    total_dist_cost_usd: Decimal
    total_dist_cost_lc: Decimal
    total_vcm_usd: Decimal
    total_vcm_lc: Decimal
    weighted_avg_price_usd: Decimal
    weighted_avg_price_lc: Decimal
    weighted_avg_vcm_usd: Decimal
    weighted_avg_vcm_lc: Decimal


class CalculationResponse(BaseModel):
    metrics: SimulationMetrics
    preview: List[dict] = Field(..., description="Preview rows of the calculated dataset")


class CompareRequest(BaseModel):
    scenario_a: str
    scenario_b: str


class CompareMetrics(BaseModel):
    total_volume: Decimal
    total_revenue_usd: Decimal
    total_rm_cost_usd: Decimal
    total_var_cost_usd: Decimal
    total_dist_cost_usd: Decimal
    total_vcm_usd: Decimal
    weighted_avg_price_usd: Decimal
    weighted_avg_vcm_usd: Decimal


class ScenarioDifference(BaseModel):
    absolute_diff: CompareMetrics
    percentage_diff: dict  # string labels, e.g. "total_volume": "10.5%"
    change_log: List[str]
    vcm_variance_by_plant: List[dict]
    vcm_variance_by_material: List[dict]


class BridgeSummary(BaseModel):
    vcm_usd_a: Decimal
    pure_volume_effect: Decimal = Decimal("0.00")
    mix_effect: Decimal = Decimal("0.00")
    volume_effect: Decimal = Decimal("0.00")
    price_effect: Decimal
    cost_effect: Decimal
    fx_effect: Decimal
    vcm_usd_b: Decimal


class BridgeResponse(BaseModel):
    summary: BridgeSummary
    by_product_line: Optional[List[dict]] = None
    by_material: List[dict]
    by_month: List[dict]
    raw_preview: List[dict]
    commentary: List[str]


class DriverAdjustment(BaseModel):
    driver_type: str = Field(..., description="volume, price, raw_cost, var_cost, dist_cost, fx_rate")
    scope_type: str = Field("portfolio", description="portfolio, product_line, material, customer")
    scope_value: Optional[str] = Field(None, description="e.g. 'Line 1 - Performance Specialties' or 'MAT-1001' or 'EUR'")
    adjustment_type: str = Field("pct", description="pct (e.g. 5.0 for +5%), delta (e.g. 10.0 for +$10/MT), or absolute (for FX, e.g. 1.08)")
    value: Decimal = Field(..., description="Numeric value of the adjustment")


class ApplyDriversRequest(BaseModel):
    adjustments: List[DriverAdjustment]
    description: Optional[str] = Field(None, description="Optional custom note describing the change")
    author: Optional[str] = Field("User", description="User name or email")


class ChangeLogItem(BaseModel):
    id: str
    timestamp: str
    author: str
    driver: str
    description: str
    scope: dict
    vcm_before_usd: Decimal
    vcm_after_usd: Decimal
    impact_usd: Decimal
    impact_pct: str


class ApplyDriversResponse(BaseModel):
    scenario: str
    applied_count: int
    change_log_entry: dict
    new_metrics: SimulationMetrics


class LoginLogInput(BaseModel):
    email: str
    name: str
    provider: str


class PPTXExportInput(BaseModel):
    scenario_a: str
    scenario_b: str
    vcm_usd_a: Decimal
    pure_volume_effect: Optional[Decimal] = None
    mix_effect: Optional[Decimal] = None
    volume_effect: Decimal
    price_effect: Decimal
    cost_effect: Decimal
    fx_effect: Decimal
    vcm_usd_b: Decimal
    material_filter: str
    region_filter: str
    theme: str = "dark"
    commentary: Optional[List[str]] = None



