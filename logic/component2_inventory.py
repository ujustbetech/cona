import pandas as pd
import numpy as np
from datetime import datetime

INPUT_FILE = "data/sept_oct_nov_item_ledgers.xlsx"
OUTPUT_FILE = "outputs/component2_inventory_report.xlsx"


def run_component2():
    """
    Component 2 — Inventory Dormancy Analysis
    Logic aligned 100% with Component 1 (IPYNB)
    """

    # ----------------------------
    # LOAD & CLEAN DATA
    # ----------------------------
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")
    df.columns = df.columns.str.strip()

    required_cols = [
        "Item No.",
        "Location Code",
        "Posting Date",
        "Quantity",
        "Remaining Quantity",
        "Cost Amount (Actual)",
        "Description",
        "Item Category Code",
        "Item Subcategory Code"
    ]

    df = df[required_cols]

    df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Remaining Quantity"] = pd.to_numeric(df["Remaining Quantity"], errors="coerce").fillna(0)
    df["Cost Amount (Actual)"] = pd.to_numeric(df["Cost Amount (Actual)"], errors="coerce").fillna(0)
    df["Location Code"] = df["Location Code"].astype(str).str.strip().replace("nan", "UNKNOWN")

    today = pd.Timestamp(datetime.today().date())

    # ----------------------------
    # LAST OUTWARD DATE
    # ----------------------------
    last_outward = (
        df[df["Quantity"] < 0]
        .groupby(["Item No.", "Location Code"])["Posting Date"]
        .max()
        .reset_index()
        .rename(columns={"Posting Date": "Last Outward Date"})
    )

    # ----------------------------
    # CURRENT STOCK ONLY
    # ----------------------------
    current_stock = (
        df[df["Remaining Quantity"] > 0]
        .groupby(["Item No.", "Location Code"])
        .agg(
            Description=("Description", "first"),
            Category=("Item Category Code", "first"),
            Subcategory=("Item Subcategory Code", "first"),
            On_Hand=("Remaining Quantity", "sum"),
            Stock_Value=("Cost Amount (Actual)", "sum"),
        )
        .reset_index()
    )

    # ----------------------------
    # MERGE & DORMANCY
    # ----------------------------
    result = current_stock.merge(
        last_outward, on=["Item No.", "Location Code"], how="left"
    )

    result["Days Dormant"] = np.where(
        result["Last Outward Date"].notna(),
        (today - pd.to_datetime(result["Last Outward Date"])).dt.days,
        np.nan
    )

    # ----------------------------
    # STATUS CLASSIFICATION (SAME AS IPYNB)
    # ----------------------------
    result["Status"] = "Active"
    result.loc[result["Days Dormant"] > 60, "Status"] = "Slow-Moving"
    result.loc[result["Days Dormant"] > 365, "Status"] = "Dead"
    result.loc[result["Last Outward Date"].isna() & (result["On_Hand"] > 0), "Status"] = "Dead"

    result["Days Dormant Display"] = result["Days Dormant"].fillna("Never Moved")

    # ----------------------------
    # KPI SUMMARY
    # ----------------------------
    total_value = result["Stock_Value"].sum()
    slow_value = result[result["Status"] == "Slow-Moving"]["Stock_Value"].sum()
    dead_value = result[result["Status"] == "Dead"]["Stock_Value"].sum()

    summary = {
        "Total Items": len(result),
        "Active Items": int((result["Status"] == "Active").sum()),
        "Slow-Moving Items": int((result["Status"] == "Slow-Moving").sum()),
        "Dead Items": int((result["Status"] == "Dead").sum()),
        "Total Value": total_value,
        "Slow-Moving Value": slow_value,
        "Dead Value": dead_value,
        "Slow %": (slow_value / total_value * 100) if total_value else 0,
        "Dead %": (dead_value / total_value * 100) if total_value else 0,
    }

    # ----------------------------
    # EXPORT EXCEL
    # ----------------------------
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "KPI": summary.keys(),
                "Value": summary.values(),
            }
        ).to_excel(writer, sheet_name="KPI Summary", index=False)

        result[
            [
                "Item No.",
                "Location Code",
                "Description",
                "Category",
                "Subcategory",
                "On_Hand",
                "Stock_Value",
                "Last Outward Date",
                "Days Dormant Display",
                "Status",
            ]
        ].to_excel(writer, sheet_name="All Items", index=False)

        result[result["Status"] == "Slow-Moving"].to_excel(
            writer, sheet_name="Slow-Moving", index=False
        )

        result[result["Status"] == "Dead"].to_excel(
            writer, sheet_name="Dead", index=False
        )

    return summary, result
