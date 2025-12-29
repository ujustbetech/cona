import pandas as pd

ITEM_FILE = "data/Items.xlsx"
LEDGER_FILE = "data/sept_oct_nov_item_ledgers.xlsx"

# --------------------------------------------------
# SHARED LOGIC FOR COMPONENT 7
# --------------------------------------------------
def run_component7():
    # ---------- LOAD FILES ----------
    df_item = pd.read_excel(ITEM_FILE)
    df_ledger = pd.read_excel(LEDGER_FILE)

    # ---------- CLEAN COLUMNS ----------
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
    df_ledger["Remaining_Qty"] = pd.to_numeric(df_ledger["Remaining_Qty"], errors="coerce").fillna(0)
    df_ledger = df_ledger[df_ledger["Remaining_Qty"] > 0]

    # ---------- MERGE ----------
    df = df_ledger.merge(
        df_item[["Item_No", "Product_Group"]],
        on="Item_No",
        how="left"
    )

    # ---------- STOCK BUCKET ----------
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
        df.groupby(["Item_No", "Location Code", "Stock_Status"])
        .agg(Total_Qty=("Remaining_Qty", "sum"))
        .reset_index()
    )

    # ---------- COMPANY LEVEL ----------
    company_view = (
        df.groupby(["Item_No", "Stock_Status"])
        .agg(Total_Qty=("Remaining_Qty", "sum"))
        .reset_index()
    )

    return df, location_view, company_view
