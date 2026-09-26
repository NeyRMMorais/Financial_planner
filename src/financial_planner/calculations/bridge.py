"""Margin Bridge (Price-Volume-Mix with FX isolation) calculation engine."""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List, Optional

def get_product_line(material_id: str, material_name: str = "") -> str:
    """Map a material ID and name to its chemical product line."""
    m_id = str(material_id or "").upper().strip()
    m_name = str(material_name or "").upper().strip()
    
    if "MAT-1001" in m_id or "MAT-3098" in m_id or "RESIN" in m_name or "SPECIALTY" in m_name:
        return "Line 1 - Performance Specialties"
    elif "MAT-2004" in m_id or "MAT-4120" in m_id or "ADDITIVE" in m_name or "FILM" in m_name:
        return "Line 2 - Functional Formulations"
    elif "MAT-5185" in m_id or "POLYMER" in m_name or "BASE" in m_name or "INTERMEDIATE" in m_name:
        return "Line 3 - Base Intermediates"
    else:
        # Default assignment based on hash or fallback
        if "1" in m_id or "3" in m_id:
            return "Line 1 - Performance Specialties"
        elif "2" in m_id or "4" in m_id:
            return "Line 2 - Functional Formulations"
        return "Line 3 - Base Intermediates"


def aggregate_scenario_data(df: pd.DataFrame) -> pd.DataFrame:
    groupby_keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]
    
    if df.empty:
        return pd.DataFrame(columns=groupby_keys + ["Product_Line", "Volume", "Price_LC", "Unit_VCM_LC", "VCM_USD", "VCM_LC"])
        
    df_copy = df.copy()
    
    # Pre-populate missing columns for compatibility with tests
    if "Revenue_LC" not in df_copy.columns:
        if "Price_LC" in df_copy.columns:
            df_copy["Revenue_LC"] = df_copy["Price_LC"] * df_copy["Volume"]
        else:
            df_copy["Revenue_LC"] = Decimal("0.00")
            
    if "VCM_LC" not in df_copy.columns:
        if "Unit_VCM_LC" in df_copy.columns:
            df_copy["VCM_LC"] = df_copy["Unit_VCM_LC"] * df_copy["Volume"]
        else:
            df_copy["VCM_LC"] = Decimal("0.00")
            
    for col in ["Revenue_USD", "Total_RM_Cost_LC", "Total_Variable_Cost_LC", "Total_Distribution_Cost_LC"]:
        if col not in df_copy.columns:
            df_copy[col] = Decimal("0.00")
            
    agg = df_copy.groupby(groupby_keys, as_index=False).agg({
        "Volume": "sum",
        "Revenue_LC": "sum",
        "Revenue_USD": "sum",
        "Total_RM_Cost_LC": "sum",
        "Total_Variable_Cost_LC": "sum",
        "Total_Distribution_Cost_LC": "sum",
        "VCM_USD": "sum",
        "VCM_LC": "sum"
    })
    
    def calc_unit_price(row):
        vol = row["Volume"]
        if vol > Decimal("0") or vol > 0:
            return row["Revenue_LC"] / vol
        return Decimal("0.00")
        
    def calc_unit_vcm(row):
        vol = row["Volume"]
        if vol > Decimal("0") or vol > 0:
            return row["VCM_LC"] / vol
        return Decimal("0.00")
        
    agg["Price_LC"] = agg.apply(calc_unit_price, axis=1)
    agg["Unit_VCM_LC"] = agg.apply(calc_unit_vcm, axis=1)
    agg["Product_Line"] = agg.apply(lambda r: get_product_line(r["Material ID"], r["Material"]), axis=1)
    
    return agg

def calculate_margin_bridge(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    fx_rates_a: pd.DataFrame,
    fx_rates_b: pd.DataFrame,
) -> pd.DataFrame:
    """
    Decompose the difference in Variable Contribution Margin (VCM) in USD
    between Scenario A (Base) and Scenario B (Target) into Volume, Price,
    Cost, and FX effects with Product Line metadata.
    """
    # 1. Aggregate and prepare copies
    a = aggregate_scenario_data(df_a)
    b = aggregate_scenario_data(df_b)

    # Clean exchange rates
    fx_a = fx_rates_a.copy()
    fx_a["Currency"] = fx_a["Currency"].astype(str).str.strip()
    fx_b = fx_rates_b.copy()
    fx_b["Currency"] = fx_b["Currency"].astype(str).str.strip()

    # 2. Merge FX rates to get the rate for each row
    a = pd.merge(
        a,
        fx_a[["Date", "Currency", "Rate"]],
        left_on=["Date", "Plant_Currency"],
        right_on=["Date", "Currency"],
        how="left",
    )
    a.rename(columns={"Rate": "Rate_A"}, inplace=True)
    if "Currency" in a.columns:
        a.drop(columns=["Currency"], inplace=True)
    a.loc[a["Plant_Currency"] == "USD", "Rate_A"] = Decimal("1.0")

    b = pd.merge(
        b,
        fx_b[["Date", "Currency", "Rate"]],
        left_on=["Date", "Plant_Currency"],
        right_on=["Date", "Currency"],
        how="left",
    )
    b.rename(columns={"Rate": "Rate_B"}, inplace=True)
    if "Currency" in b.columns:
        b.drop(columns=["Currency"], inplace=True)
    b.loc[b["Plant_Currency"] == "USD", "Rate_B"] = Decimal("1.0")

    # 3. Rename columns to avoid collisions
    cols_a = {
        "Volume": "Vol_A",
        "Price_LC": "Price_LC_A",
        "Unit_VCM_LC": "Unit_VCM_LC_A",
        "VCM_USD": "VCM_USD_A",
    }
    a.rename(columns=cols_a, inplace=True)

    cols_b = {
        "Volume": "Vol_B",
        "Price_LC": "Price_LC_B",
        "Unit_VCM_LC": "Unit_VCM_LC_B",
        "VCM_USD": "VCM_USD_B",
    }
    b.rename(columns=cols_b, inplace=True)

    # Keep necessary columns
    keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material", "Product_Line"]
    a_subset = a[keys + list(cols_a.values()) + ["Rate_A"]]
    b_subset = b[keys + list(cols_b.values()) + ["Rate_B"]]

    # 4. Outer Join on the keys
    merged = pd.merge(
        a_subset,
        b_subset,
        on=keys,
        how="outer",
    )

    # 5. Fill missing values (NaNs) and handle align
    def fill_nan_decimal(series, default=Decimal("0.0")):
        return series.apply(lambda x: default if pd.isna(x) else Decimal(str(x)))

    merged["Vol_A"] = fill_nan_decimal(merged["Vol_A"])
    merged["Vol_B"] = fill_nan_decimal(merged["Vol_B"])
    merged["VCM_USD_A"] = fill_nan_decimal(merged["VCM_USD_A"])
    merged["VCM_USD_B"] = fill_nan_decimal(merged["VCM_USD_B"])

    # Align Price, Unit VCM, and Rate for new/discontinued combinations
    def align_rows(row):
        # A exists but B is missing
        if pd.isna(row["Rate_B"]):
            rate_b = Decimal(str(row["Rate_A"]))
            price_lc_b = Decimal(str(row["Price_LC_A"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_A"]))
            rate_a = Decimal(str(row["Rate_A"]))
            price_lc_a = Decimal(str(row["Price_LC_A"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_A"]))
        # B exists but A is missing
        elif pd.isna(row["Rate_A"]):
            rate_a = Decimal(str(row["Rate_B"]))
            price_lc_a = Decimal(str(row["Price_LC_B"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_B"]))
            rate_b = Decimal(str(row["Rate_B"]))
            price_lc_b = Decimal(str(row["Price_LC_B"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_B"]))
        else:
            rate_a = Decimal(str(row["Rate_A"]))
            rate_b = Decimal(str(row["Rate_B"]))
            price_lc_a = Decimal(str(row["Price_LC_A"]))
            price_lc_b = Decimal(str(row["Price_LC_B"]))
            vcm_lc_a = Decimal(str(row["Unit_VCM_LC_A"]))
            vcm_lc_b = Decimal(str(row["Unit_VCM_LC_B"]))

        return pd.Series([rate_a, rate_b, price_lc_a, price_lc_b, vcm_lc_a, vcm_lc_b])

    aligned_cols = [
        "Rate_A_aligned",
        "Rate_B_aligned",
        "Price_LC_A_aligned",
        "Price_LC_B_aligned",
        "Unit_VCM_LC_A_aligned",
        "Unit_VCM_LC_B_aligned",
    ]
    merged[aligned_cols] = merged.apply(align_rows, axis=1)

    # 6. Compute unit costs in Local Currency (C_LC = Price_LC - Unit_VCM_LC)
    merged["C_LC_A"] = merged["Price_LC_A_aligned"] - merged["Unit_VCM_LC_A_aligned"]
    merged["C_LC_B"] = merged["Price_LC_B_aligned"] - merged["Unit_VCM_LC_B_aligned"]

    # 7. Compute the bridge effects row-by-row
    # Unit VCM in USD for base scenario
    merged["Unit_VCM_USD_A"] = merged["Unit_VCM_LC_A_aligned"] / merged["Rate_A_aligned"]
    merged["Unit_VCM_USD_B"] = merged["Unit_VCM_LC_B_aligned"] / merged["Rate_B_aligned"]

    # Volume Effect = (Vol_B - Vol_A) * Unit_VCM_USD_A
    merged["Volume_Effect"] = (merged["Vol_B"] - merged["Vol_A"]) * merged["Unit_VCM_USD_A"]

    # Price Effect = Vol_B * ((Price_LC_B - Price_LC_A) / Rate_A)
    merged["Price_Effect"] = merged["Vol_B"] * (
        (merged["Price_LC_B_aligned"] - merged["Price_LC_A_aligned"]) / merged["Rate_A_aligned"]
    )

    # Cost Effect = Vol_B * ((C_LC_A - C_LC_B) / Rate_A)
    merged["Cost_Effect"] = merged["Vol_B"] * (
        (merged["C_LC_A"] - merged["C_LC_B"]) / merged["Rate_A_aligned"]
    )

    # FX Effect = Vol_B * Unit_VCM_LC_B * (1/Rate_B - 1/Rate_A)
    merged["FX_Effect"] = merged["Vol_B"] * merged["Unit_VCM_LC_B_aligned"] * (
        (Decimal("1.0") / merged["Rate_B_aligned"]) - (Decimal("1.0") / merged["Rate_A_aligned"])
    )

    # Clean up intermediate aligned columns
    merged.drop(
        columns=[
            "Rate_A_aligned",
            "Rate_B_aligned",
            "Price_LC_A_aligned",
            "Price_LC_B_aligned",
            "Unit_VCM_LC_A_aligned",
            "Unit_VCM_LC_B_aligned",
            "C_LC_A",
            "C_LC_B",
            "Unit_VCM_USD_A",
            "Unit_VCM_USD_B",
            "Rate_A",
            "Rate_B",
        ],
        inplace=True,
    )

    return merged

def summarize_margin_bridge(bridge_df: pd.DataFrame) -> Dict[str, Decimal]:
    """
    Aggregate individual row-by-row bridge effects to produce total sums in USD,
    explicitly separating Pure Volume Effect from Mix Effect.
    """
    if bridge_df.empty:
        return {
            "vcm_usd_a": Decimal("0.00"),
            "pure_volume_effect": Decimal("0.00"),
            "mix_effect": Decimal("0.00"),
            "volume_effect": Decimal("0.00"),
            "price_effect": Decimal("0.00"),
            "cost_effect": Decimal("0.00"),
            "fx_effect": Decimal("0.00"),
            "vcm_usd_b": Decimal("0.00"),
        }

    vcm_usd_a = sum(bridge_df["VCM_USD_A"], Decimal("0.00"))
    vcm_usd_b = sum(bridge_df["VCM_USD_B"], Decimal("0.00"))
    total_vol_a = sum(bridge_df["Vol_A"], Decimal("0.00"))
    total_vol_b = sum(bridge_df["Vol_B"], Decimal("0.00"))
    raw_vol_effect = sum(bridge_df["Volume_Effect"], Decimal("0.00"))

    # Portfolio Baseline Unit Margin in USD
    base_unit_margin_usd = (vcm_usd_a / total_vol_a) if total_vol_a > Decimal("0") else Decimal("0.00")

    # Pure Volume Effect = (Total_Vol_B - Total_Vol_A) * Base_Portfolio_Unit_Margin_USD
    pure_volume_effect = (total_vol_b - total_vol_a) * base_unit_margin_usd

    # Mix Effect = Sum of Row Volume Effects - Pure Volume Effect
    mix_effect = raw_vol_effect - pure_volume_effect

    price_effect = sum(bridge_df["Price_Effect"], Decimal("0.00"))
    cost_effect = sum(bridge_df["Cost_Effect"], Decimal("0.00"))
    fx_effect = sum(bridge_df["FX_Effect"], Decimal("0.00"))

    return {
        "vcm_usd_a": vcm_usd_a,
        "pure_volume_effect": pure_volume_effect,
        "mix_effect": mix_effect,
        "volume_effect": raw_vol_effect,
        "price_effect": price_effect,
        "cost_effect": cost_effect,
        "fx_effect": fx_effect,
        "vcm_usd_b": vcm_usd_b,
    }


def summarize_by_product_line(bridge_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Summarize bridge effects grouped by Product Line.
    """
    if bridge_df.empty:
        return []

    lines = []
    total_vol_a = sum(bridge_df["Vol_A"], Decimal("0.00"))
    vcm_usd_a_tot = sum(bridge_df["VCM_USD_A"], Decimal("0.00"))
    base_unit_margin_usd = (vcm_usd_a_tot / total_vol_a) if total_vol_a > Decimal("0") else Decimal("0.00")

    for p_line, grp in bridge_df.groupby("Product_Line"):
        vol_a = sum(grp["Vol_A"], Decimal("0.00"))
        vol_b = sum(grp["Vol_B"], Decimal("0.00"))
        vcm_a = sum(grp["VCM_USD_A"], Decimal("0.00"))
        vcm_b = sum(grp["VCM_USD_B"], Decimal("0.00"))
        line_raw_vol = sum(grp["Volume_Effect"], Decimal("0.00"))
        
        line_pure_vol = (vol_b - vol_a) * base_unit_margin_usd
        line_mix = line_raw_vol - line_pure_vol
        line_price = sum(grp["Price_Effect"], Decimal("0.00"))
        line_cost = sum(grp["Cost_Effect"], Decimal("0.00"))
        line_fx = sum(grp["FX_Effect"], Decimal("0.00"))
        
        vol_growth_pct = ((vol_b - vol_a) / vol_a * Decimal("100.0")) if vol_a > Decimal("0") else Decimal("0.0")

        lines.append({
            "product_line": str(p_line),
            "volume_a": vol_a,
            "volume_b": vol_b,
            "volume_delta": vol_b - vol_a,
            "volume_growth_pct": vol_growth_pct,
            "vcm_usd_a": vcm_a,
            "vcm_usd_b": vcm_b,
            "vcm_delta_usd": vcm_b - vcm_a,
            "pure_volume_effect": line_pure_vol,
            "mix_effect": line_mix,
            "volume_effect": line_raw_vol,
            "price_effect": line_price,
            "cost_effect": line_cost,
            "fx_effect": line_fx,
            "unit_vcm_usd_a": (vcm_a / vol_a) if vol_a > 0 else Decimal("0.00"),
            "unit_vcm_usd_b": (vcm_b / vol_b) if vol_b > 0 else Decimal("0.00"),
        })

    # Sort lines by vcm_usd_a descending
    lines.sort(key=lambda x: x["vcm_usd_a"], reverse=True)
    return lines


def generate_bridge_commentary(
    summary: Dict[str, Any],
    by_material: List[Dict[str, Any]],
    by_month: List[Dict[str, Any]],
    by_product_line: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """
    Generate natural language commentary explaining the key drivers of the VCM bridge,
    explicitly distinguishing Pure Volume Effect from Mix Effect across chemical product lines.
    Uses Gemini API if GEMINI_API_KEY is available, otherwise falls back to a deterministic rule-based commentary.
    """
    # 1. Parse core metrics
    vcm_a = Decimal(str(summary.get("vcm_usd_a", 0)))
    vcm_b = Decimal(str(summary.get("vcm_usd_b", 0)))
    pure_vol_eff = Decimal(str(summary.get("pure_volume_effect", summary.get("volume_effect", 0))))
    mix_eff = Decimal(str(summary.get("mix_effect", 0)))
    vol_eff = Decimal(str(summary.get("volume_effect", pure_vol_eff + mix_eff)))
    price_eff = Decimal(str(summary.get("price_effect", 0)))
    cost_eff = Decimal(str(summary.get("cost_effect", 0)))
    fx_eff = Decimal(str(summary.get("fx_effect", 0)))

    delta = vcm_b - vcm_a
    pct_change = (delta / vcm_a * 100) if vcm_a != 0 else Decimal("0.0")

    # Helper formatters
    def fmt_usd(val: Decimal) -> str:
        av = abs(val)
        sign = "-" if val < 0 else ""
        if av >= 1_000_000:
            return f"{sign}${av / 1_000_000:,.2f}M"
        elif av >= 1_000:
            return f"{sign}${av / 1_000:,.1f}k"
        return f"{sign}${av:,.2f}"

    # Determine rank of effects
    effects = [
        ("Price Realization", price_eff),
        ("Pure Volume Effect", pure_vol_eff),
        ("Product Mix Effect", mix_eff),
        ("Cost/PPV Effect", cost_eff),
        ("FX Exposure", fx_eff)
    ]
    # Sort by absolute value descending
    ranked_effects = sorted(effects, key=lambda x: abs(x[1]), reverse=True)
    primary_name, primary_val = ranked_effects[0]
    secondary_name, secondary_val = ranked_effects[1]

    # Find material details
    top_price_fav = None
    if by_material:
        price_fav_list = [m for m in by_material if Decimal(str(m.get("Price_Effect", 0))) > 0]
        if price_fav_list:
            top_price_fav = max(price_fav_list, key=lambda x: Decimal(str(x.get("Price_Effect", 0))))
    
    top_price_unfav = None
    if by_material:
        price_unfav_list = [m for m in by_material if Decimal(str(m.get("Price_Effect", 0))) < 0]
        if price_unfav_list:
            top_price_unfav = min(price_unfav_list, key=lambda x: Decimal(str(x.get("Price_Effect", 0))))

    top_cost_fav = None
    top_cost_unfav = None
    if by_material:
        cost_fav_list = [m for m in by_material if Decimal(str(m.get("Cost_Effect", 0))) > 0]
        if cost_fav_list:
            top_cost_fav = max(cost_fav_list, key=lambda x: Decimal(str(x.get("Cost_Effect", 0))))
        cost_unfav_list = [m for m in by_material if Decimal(str(m.get("Cost_Effect", 0))) < 0]
        if cost_unfav_list:
            top_cost_unfav = min(cost_unfav_list, key=lambda x: Decimal(str(x.get("Cost_Effect", 0))))

    # Product Line drivers
    top_line_fav = None
    top_line_unfav = None
    if by_product_line:
        line_fav_list = [l for l in by_product_line if Decimal(str(l.get("vcm_delta_usd", 0))) > 0]
        if line_fav_list:
            top_line_fav = max(line_fav_list, key=lambda x: Decimal(str(x.get("vcm_delta_usd", 0))))
        line_unfav_list = [l for l in by_product_line if Decimal(str(l.get("vcm_delta_usd", 0))) < 0]
        if line_unfav_list:
            top_line_unfav = min(line_unfav_list, key=lambda x: Decimal(str(x.get("vcm_delta_usd", 0))))

    # Month anomaly
    top_month = None
    if by_month:
        def month_var(m):
            v_a = Decimal(str(m.get("VCM_USD_A", 0)))
            v_b = Decimal(str(m.get("VCM_USD_B", 0)))
            return abs(v_b - v_a)
        top_month = max(by_month, key=month_var)

    # 2. Build Deterministic Commentary List
    bullets = []
    
    # Bullet 1: Summary statement
    status_word = "increased" if delta >= 0 else "decreased"
    bullets.append(
        f"Variable Contribution Margin (VCM) {status_word} by **{fmt_usd(delta)}** ({pct_change:+.1f}%), shifting from **{fmt_usd(vcm_a)}** in Scenario A to **{fmt_usd(vcm_b)}** in Scenario B."
    )

    # Bullet 2: Key drivers overview
    primary_word = "favorable" if primary_val >= 0 else "unfavorable"
    secondary_word = "favorable" if secondary_val >= 0 else "unfavorable"
    bullets.append(
        f"The variance was primarily driven by a **{primary_word} {primary_name}** of **{fmt_usd(primary_val)}**, followed by a **{secondary_word} {secondary_name}** of **{fmt_usd(secondary_val)}**."
    )

    # Bullet 3: Volume & Mix isolation
    mix_word = "favorable" if mix_eff >= 0 else "unfavorable"
    vol_word = "growth" if pure_vol_eff >= 0 else "contraction"
    mix_desc = (
        f"Pure volume {vol_word} contributed **{fmt_usd(pure_vol_eff)}**, while portfolio mix shifts between product lines generated a **{mix_word} {fmt_usd(mix_eff)}** impact."
    )
    if top_line_fav:
        mix_desc += f" Performance was supported by strong margin contributions in **{top_line_fav.get('product_line')}** ({fmt_usd(Decimal(str(top_line_fav.get('vcm_delta_usd', 0))))})."
    bullets.append(mix_desc)

    # Bullet 4: Price effects
    price_comment = f"Pricing adjustments contributed **{fmt_usd(price_eff)}** to the total variance."
    if top_price_fav or top_price_unfav:
        details = []
        if top_price_fav:
            details.append(f"favorable price adjustments in **{top_price_fav.get('Material')}** ({fmt_usd(Decimal(str(top_price_fav.get('Price_Effect', 0))))})")
        if top_price_unfav:
            details.append(f"unfavorable pricing in **{top_price_unfav.get('Material')}** ({fmt_usd(Decimal(str(top_price_unfav.get('Price_Effect', 0))))})")
        price_comment += " Key highlights include " + " and ".join(details) + "."
    bullets.append(price_comment)

    # Bullet 5: Cost effects
    cost_comment = f"Unit cost changes (including raw material BOMs, distribution, and variable production) had a net impact of **{fmt_usd(cost_eff)}**."
    if top_cost_fav or top_cost_unfav:
        details = []
        if top_cost_fav:
            details.append(f"cost improvements in **{top_cost_fav.get('Material')}** ({fmt_usd(Decimal(str(top_cost_fav.get('Cost_Effect', 0))))})")
        if top_cost_unfav:
            details.append(f"cost inflation in **{top_cost_unfav.get('Material')}** ({fmt_usd(Decimal(str(top_cost_unfav.get('Cost_Effect', 0))))})")
        cost_comment += " This was driven by " + " and ".join(details) + "."
    bullets.append(cost_comment)

    # Bullet 6: FX
    bullets.append(
        f"Exchange rate fluctuations across plant and billing currencies had an impact of **{fmt_usd(fx_eff)}**."
    )

    # Bullet 7: Monthly anomaly
    if top_month:
        m_date = top_month.get("Date")
        m_vcm_a = Decimal(str(top_month.get("VCM_USD_A", 0)))
        m_vcm_b = Decimal(str(top_month.get("VCM_USD_B", 0)))
        m_delta = m_vcm_b - m_vcm_a
        bullets.append(
            f"The month with the largest absolute variance was **{m_date}** with a shift of **{fmt_usd(m_delta)}**."
        )

    # Add marker to indicate source
    bullets.insert(0, "[Deterministic Summary]")

    # 3. AI Generation check
    import os
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("FP_Gemini_Api")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            # Prepare details for prompt
            facts = (
                f"- Starting VCM (Scenario A): {fmt_usd(vcm_a)}\n"
                f"- Ending VCM (Scenario B): {fmt_usd(vcm_b)}\n"
                f"- Net Variance: {fmt_usd(delta)} ({pct_change:+.1f}%)\n"
                f"- Price Effect: {fmt_usd(price_eff)}\n"
                f"- Pure Volume Effect: {fmt_usd(pure_vol_eff)}\n"
                f"- Product Mix Effect: {fmt_usd(mix_eff)}\n"
                f"- Cost Effect: {fmt_usd(cost_eff)}\n"
                f"- FX Effect: {fmt_usd(fx_eff)}\n"
            )
            
            if top_line_fav:
                facts += f"- Top Performing Product Line: {top_line_fav.get('product_line')} (Delta: {fmt_usd(Decimal(str(top_line_fav.get('vcm_delta_usd', 0))))})\n"
            if top_price_fav:
                facts += f"- Top Favorable Price Driver: {top_price_fav.get('Material')} ({fmt_usd(Decimal(str(top_price_fav.get('Price_Effect', 0))))})\n"
            if top_price_unfav:
                facts += f"- Top Unfavorable Price Driver: {top_price_unfav.get('Material')} ({fmt_usd(Decimal(str(top_price_unfav.get('Price_Effect', 0))))})\n"
            if top_cost_fav:
                facts += f"- Top Cost Saving Driver: {top_cost_fav.get('Material')} ({fmt_usd(Decimal(str(top_cost_fav.get('Cost_Effect', 0))))})\n"
            if top_cost_unfav:
                facts += f"- Top Cost Inflation Drag: {top_cost_unfav.get('Material')} ({fmt_usd(Decimal(str(top_cost_unfav.get('Cost_Effect', 0))))})\n"
            if top_month:
                m_date = top_month.get("Date")
                m_vcm_a = Decimal(str(top_month.get("VCM_USD_A", 0)))
                m_vcm_b = Decimal(str(top_month.get("VCM_USD_B", 0)))
                facts += f"- Month with Largest Variance: {m_date} (Delta: {fmt_usd(m_vcm_b - m_vcm_a)})\n"

            prompt = (
                "You are a Senior FP&A Professional and Corporate Finance Director. Below is a structured chemical manufacturing gross margin bridge analysis.\n"
                "Write a concise, polished executive commentary explaining the variance. Format your output as a list of exactly 4 to 6 bullet points.\n"
                "Follow these rules strictly:\n"
                "1. Maintain strict mathematical consistency. Use the exact numbers provided below.\n"
                "2. Emphasize the primary and secondary drivers clearly, including the distinction between Pure Volume and Product Mix shifts.\n"
                "3. Do not invent any names, metrics, or reasons not provided in the facts.\n"
                "4. Keep the style professional, clean, and concise, suitable for a board meeting.\n"
                "5. Do NOT include markdown bold formatting inside the bullet text, keep it clean.\n\n"
                "FACTS:\n"
                f"{facts}\n"
                "COMMENTARY:"
            )

            model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
            response = client.models.generate_content(
                model=model_name, contents=prompt
            )
            text = response.text.strip()
            
            ai_bullets = []
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*") or (line and line[0].isdigit() and line[1] in (".", ")")):
                    content = line.lstrip("-*0123456789. )").strip()
                    if content:
                        ai_bullets.append(content)
                elif line:
                    ai_bullets.append(line)
            
            if len(ai_bullets) >= 3:
                ai_bullets.insert(0, "[AI-Generated Summary]")
                return ai_bullets
        except Exception as e:
            import logging
            logging.error(f"Gemini commentary generation failed: {e}", exc_info=True)
            pass

    return bullets
