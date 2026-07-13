"""Margin Bridge (Price-Volume-Mix with FX isolation) calculation engine."""

import pandas as pd
from decimal import Decimal
from typing import Dict, Any, List

def aggregate_scenario_data(df: pd.DataFrame) -> pd.DataFrame:
    groupby_keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]
    
    if df.empty:
        return pd.DataFrame(columns=groupby_keys + ["Volume", "Price_LC", "Unit_VCM_LC", "VCM_USD", "VCM_LC"])
        
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
    Cost, and FX effects.

    Args:
        df_a: Fully calculated output dataframe for Scenario A.
        df_b: Fully calculated output dataframe for Scenario B.
        fx_rates_a: Exchange rates for Scenario A.
        fx_rates_b: Exchange rates for Scenario B.

    Returns:
        A DataFrame containing the row-by-row bridge components in USD:
        ['Material ID', 'Sold to ID', 'Ship to ID', 'Date', 'Plant', 'Plant_Currency',
         'Volume_A', 'Volume_B', 'VCM_USD_A', 'VCM_USD_B',
         'Volume_Effect', 'Price_Effect', 'Cost_Effect', 'FX_Effect']
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
    # Merge Rate_A
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

    # Merge Rate_B
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
    keys = ["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"]
    a_subset = a[keys + list(cols_a.values()) + ["Rate_A"]]
    b_subset = b[keys + list(cols_b.values()) + ["Rate_B"]]

    # 4. Outer Join on the keys
    # Merge keys to do outer join
    merged = pd.merge(
        a_subset,
        b_subset,
        on=["Sold to ID", "Ship to ID", "Material ID", "Date", "Plant", "Plant_Currency", "Material"],
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
    Aggregate individual row-by-row bridge effects to produce total sums in USD.
    """
    if bridge_df.empty:
        return {
            "vcm_usd_a": Decimal("0.00"),
            "volume_effect": Decimal("0.00"),
            "price_effect": Decimal("0.00"),
            "cost_effect": Decimal("0.00"),
            "fx_effect": Decimal("0.00"),
            "vcm_usd_b": Decimal("0.00"),
        }

    return {
        "vcm_usd_a": sum(bridge_df["VCM_USD_A"], Decimal("0.00")),
        "volume_effect": sum(bridge_df["Volume_Effect"], Decimal("0.00")),
        "price_effect": sum(bridge_df["Price_Effect"], Decimal("0.00")),
        "cost_effect": sum(bridge_df["Cost_Effect"], Decimal("0.00")),
        "fx_effect": sum(bridge_df["FX_Effect"], Decimal("0.00")),
        "vcm_usd_b": sum(bridge_df["VCM_USD_B"], Decimal("0.00")),
    }


def generate_bridge_commentary(
    summary: Dict[str, Any],
    by_material: List[Dict[str, Any]],
    by_month: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate natural language commentary explaining the key drivers of the VCM bridge.
    Uses Gemini API if GEMINI_API_KEY is available, otherwise falls back to a deterministic rule-based commentary.
    """
    # 1. Parse core metrics
    vcm_a = Decimal(str(summary.get("vcm_usd_a", 0)))
    vcm_b = Decimal(str(summary.get("vcm_usd_b", 0)))
    vol_eff = Decimal(str(summary.get("volume_effect", 0)))
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
        ("Price Effect", price_eff),
        ("Volume Effect", vol_eff),
        ("Cost Effect", cost_eff),
        ("FX Effect", fx_eff)
    ]
    # Sort by absolute value descending
    ranked_effects = sorted(effects, key=lambda x: abs(x[1]), reverse=True)
    primary_name, primary_val = ranked_effects[0]
    secondary_name, secondary_val = ranked_effects[1]

    # Find material details
    # Favorable price driver
    top_price_fav = None
    if by_material:
        price_fav_list = [m for m in by_material if Decimal(str(m.get("Price_Effect", 0))) > 0]
        if price_fav_list:
            top_price_fav = max(price_fav_list, key=lambda x: Decimal(str(x.get("Price_Effect", 0))))
    
    # Unfavorable price driver
    top_price_unfav = None
    if by_material:
        price_unfav_list = [m for m in by_material if Decimal(str(m.get("Price_Effect", 0))) < 0]
        if price_unfav_list:
            top_price_unfav = min(price_unfav_list, key=lambda x: Decimal(str(x.get("Price_Effect", 0))))

    # Favorable/unfavorable cost driver
    top_cost_fav = None
    top_cost_unfav = None
    if by_material:
        cost_fav_list = [m for m in by_material if Decimal(str(m.get("Cost_Effect", 0))) > 0]
        if cost_fav_list:
            top_cost_fav = max(cost_fav_list, key=lambda x: Decimal(str(x.get("Cost_Effect", 0))))
        cost_unfav_list = [m for m in by_material if Decimal(str(m.get("Cost_Effect", 0))) < 0]
        if cost_unfav_list:
            top_cost_unfav = min(cost_unfav_list, key=lambda x: Decimal(str(x.get("Cost_Effect", 0))))

    # Volume/mix driver
    top_vol_fav = None
    top_vol_unfav = None
    if by_material:
        vol_fav_list = [m for m in by_material if Decimal(str(m.get("Volume_Effect", 0))) > 0]
        if vol_fav_list:
            top_vol_fav = max(vol_fav_list, key=lambda x: Decimal(str(x.get("Volume_Effect", 0))))
        vol_unfav_list = [m for m in by_material if Decimal(str(m.get("Volume_Effect", 0))) < 0]
        if vol_unfav_list:
            top_vol_unfav = min(vol_unfav_list, key=lambda x: Decimal(str(x.get("Volume_Effect", 0))))

    # Month anomaly
    top_month = None
    if by_month:
        # Find month with largest absolute variance in VCM (VCM_USD_B - VCM_USD_A)
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

    # Bullet 3: Price effects
    price_comment = f"Pricing adjustments contributed **{fmt_usd(price_eff)}** to the total variance."
    if top_price_fav or top_price_unfav:
        details = []
        if top_price_fav:
            details.append(f"favorable price adjustments in **{top_price_fav.get('Material')}** ({fmt_usd(Decimal(str(top_price_fav.get('Price_Effect', 0))))})")
        if top_price_unfav:
            details.append(f"unfavorable pricing in **{top_price_unfav.get('Material')}** ({fmt_usd(Decimal(str(top_price_unfav.get('Price_Effect', 0))))})")
        price_comment += " Key highlights include " + " and ".join(details) + "."
    bullets.append(price_comment)

    # Bullet 4: Cost effects
    cost_comment = f"Unit cost changes (including raw materials, distribution, and variable production) had a net impact of **{fmt_usd(cost_eff)}**."
    if top_cost_fav or top_cost_unfav:
        details = []
        if top_cost_fav:
            details.append(f"cost improvements in **{top_cost_fav.get('Material')}** ({fmt_usd(Decimal(str(top_cost_fav.get('Cost_Effect', 0))))})")
        if top_cost_unfav:
            details.append(f"cost increases/inflation in **{top_cost_unfav.get('Material')}** ({fmt_usd(Decimal(str(top_cost_unfav.get('Cost_Effect', 0))))})")
        cost_comment += " This was driven by " + " and ".join(details) + "."
    bullets.append(cost_comment)

    # Bullet 5: Volume & Mix
    vol_comment = f"Volume and mix shifts impacted margins by **{fmt_usd(vol_eff)}**."
    if top_vol_fav or top_vol_unfav:
        details = []
        if top_vol_fav:
            details.append(f"volume growth in **{top_vol_fav.get('Material')}** ({fmt_usd(Decimal(str(top_vol_fav.get('Volume_Effect', 0))))})")
        if top_vol_unfav:
            details.append(f"volume contraction in **{top_vol_unfav.get('Material')}** ({fmt_usd(Decimal(str(top_vol_unfav.get('Volume_Effect', 0))))})")
        vol_comment += " Driven by " + " and ".join(details) + "."
    bullets.append(vol_comment)

    # Bullet 6: FX
    bullets.append(
        f"Exchange rate fluctuations had an impact of **{fmt_usd(fx_eff)}**."
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
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Prepare details for prompt
            facts = (
                f"- Starting VCM (Scenario A): {fmt_usd(vcm_a)}\n"
                f"- Ending VCM (Scenario B): {fmt_usd(vcm_b)}\n"
                f"- Net Variance: {fmt_usd(delta)} ({pct_change:+.1f}%)\n"
                f"- Price Effect: {fmt_usd(price_eff)}\n"
                f"- Volume Effect: {fmt_usd(vol_eff)}\n"
                f"- Cost Effect: {fmt_usd(cost_eff)}\n"
                f"- FX Effect: {fmt_usd(fx_eff)}\n"
            )
            
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
                "You are a Senior FP&A Professional and Corporate Finance Director. Below is a structured gross margin bridge analysis.\n"
                "Write a concise, polished executive commentary explaining the variance. Format your output as a list of exactly 4 to 6 bullet points.\n"
                "Follow these rules strictly:\n"
                "1. Maintain strict mathematical consistency. Use the exact numbers provided below.\n"
                "2. Emphasize the primary and secondary drivers clearly.\n"
                "3. Do not invent any names, metrics, or reasons not provided in the facts.\n"
                "4. Keep the style professional, clean, and concise, suitable for a board meeting.\n"
                "5. Do NOT include markdown bold formatting inside the bullet text, keep it clean.\n\n"
                "FACTS:\n"
                f"{facts}\n"
                "COMMENTARY:"
            )

            # Call Gemini
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse text into bullets
            ai_bullets = []
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*") or (line and line[0].isdigit() and line[1] in (".", ")")):
                    # Remove bullet characters
                    content = line.lstrip("-*0123456789. )").strip()
                    if content:
                        ai_bullets.append(content)
                elif line:
                    ai_bullets.append(line)
            
            if len(ai_bullets) >= 3:
                # Prepend the marker
                ai_bullets.insert(0, "[AI-Generated Summary]")
                return ai_bullets
        except Exception as e:
            # Fall back silently to deterministic bullets
            pass

    return bullets
