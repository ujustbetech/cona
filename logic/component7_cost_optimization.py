import pandas as pd


def run_component7(
    df_item: pd.DataFrame,
    df_ledger: pd.DataFrame
):
    """
    Component 7 — Cost Optimization / Stock Health
    Serverless-safe (Vercel compatible)
    Logic preserved exactly
    """

    # ---------- COPY & CLEAN ----------
    df_item = df_item.copy()
    df_ledger = df_ledger.copy()

    df_item.columns = df_item.columns.str.strip()
    df_ledger.columns = df_ledger.columns.str.strip()

    # ---------- RENAME ----------
    df_item = df_item.rename(columns={
        "No.": "Item_No",
        "Gen. Prod. Posting Group": "Product_Group"
    })

    df_ledger = df_ledger.rename(columns={
        "Item No.": "Item_No",
        "Remaining Quantity": "Remaining_Qty"
    })

    # ---------- FILTER VALID STOCK ----------
    df_ledger["Remaining_Qty"] = pd.to_numeric(
        df_ledger["Remaining_Qty"],
        errors="coerce"
    ).fillna(0)

    df_ledger = df_ledger[df_ledger["Remaining_Qty"] > 0]

    # ---------- MERGE ----------
    df = df_ledger.merge(
        df_item[["Item_No", "Product_Group"]],
        on="Item_No",
        how="left"
    )

    # ---------- STOCK BUCKET (UNCHANGED LOGIC) ----------
    def stock_bucket(qty):
        if qty <= 50000:
            return "RED"
        elif qty <= 200000:
            return "YELLOW"
        else:
            return "GREEN"

    df["Stock_Status"] = df["Remaining_Qty"].apply(stock_bucket)

    # ---------- LOCATION LEVEL ----------
    location_view = (
        df.groupby(
            ["Item_No", "Location Code", "Stock_Status"],
            as_index=False
        )
        .agg(Total_Qty=("Remaining_Qty", "sum"))
    )

    # ---------- COMPANY LEVEL ----------
    company_view = (
        df.groupby(
            ["Item_No", "Stock_Status"],
            as_index=False
        )
        .agg(Total_Qty=("Remaining_Qty", "sum"))
    )

    return df, location_view, company_view
