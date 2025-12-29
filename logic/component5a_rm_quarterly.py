import pandas as pd

# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------
ITEMS_FILE = "data/Items.xlsx"
PO_FILE = "data/Purchase order - use order date.xlsx"
RECEIPT_FILE = "data/Posted Purchase Receipts - Posting date against document no.xlsx"
LINES_FILE = "data/Purchase Lines -.xlsx"

SLA_DAYS = 10   # Change if your SLA differs


def run_component5a_rm():
    # ==================================================
    # 1. LOAD FILES
    # ==================================================
    df_items = pd.read_excel(ITEMS_FILE)
    df_po = pd.read_excel(PO_FILE)
    df_receipts = pd.read_excel(RECEIPT_FILE)
    df_lines = pd.read_excel(LINES_FILE)

    # Clean column names
    for df in [df_items, df_po, df_receipts, df_lines]:
        df.columns = df.columns.str.strip()

    # ==================================================
    # 2. GET TRUE RM ITEM CODES
    # ==================================================
    df_items = df_items.rename(columns={
        "No.": "Item_No",
        "Inventory Posting Group": "Posting_Group"
    })

    rm_items = (
        df_items[df_items["Posting_Group"] == "RM"]["Item_No"]
        .astype(str)
        .str.strip()
        .unique()
    )

    rm_items_set = set(rm_items)

    # ==================================================
    # 3. FIND POs THAT CONTAIN AT LEAST ONE RM ITEM
    # ==================================================
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "No.": "Item_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["PO_No"] = df_lines["PO_No"].astype(str).str.strip()
    df_lines["Item_No"] = df_lines["Item_No"].astype(str).str.strip()

    rm_po_list = (
        df_lines[df_lines["Item_No"].isin(rm_items_set)]["PO_No"]
        .unique()
        .tolist()
    )

    # ==================================================
    # 4. PURCHASE ORDER MASTER
    # ==================================================
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Buy-from Vendor Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po["PO_No"] = df_po["PO_No"].astype(str).str.strip()
    df_po["Last_Receiving_No"] = df_po["Last_Receiving_No"].astype(str).str.strip()
    df_po["Order_Date"] = pd.to_datetime(df_po["Order_Date"], errors="coerce")

    # 🔴 FILTER TO RM POs ONLY
    df_po = df_po[df_po["PO_No"].isin(rm_po_list)]

    # ==================================================
    # 5. COMPLETION CHECK (Outstanding Qty == 0)
    # ==================================================
    po_completion = (
        df_lines.groupby("PO_No", as_index=False)["Outstanding_Qty"]
        .sum()
    )

    completed_pos = po_completion[po_completion["Outstanding_Qty"] == 0]["PO_No"]

    df_po = df_po[df_po["PO_No"].isin(completed_pos)]

    # ==================================================
    # 6. RECEIPT DATE
    # ==================================================
    df_receipts = df_receipts.rename(columns={
        "No.": "Receipt_No",
        "Posting Date": "Posting_Date"
    })

    df_receipts["Receipt_No"] = df_receipts["Receipt_No"].astype(str).str.strip()
    df_receipts["Posting_Date"] = pd.to_datetime(df_receipts["Posting_Date"], errors="coerce")

    receipt_map = dict(
        zip(df_receipts["Receipt_No"], df_receipts["Posting_Date"])
    )

    df_po["Receipt_Date"] = df_po["Last_Receiving_No"].map(receipt_map)

    # ==================================================
    # 7. DELIVERY DAYS & SLA
    # ==================================================
    df_po = df_po.dropna(subset=["Order_Date", "Receipt_Date"])

    df_po["Days_To_Receive"] = (
        df_po["Receipt_Date"] - df_po["Order_Date"]
    ).dt.days

    df_po = df_po[df_po["Days_To_Receive"] >= 0]

    df_po["SLA_Status"] = df_po["Days_To_Receive"].apply(
        lambda x: "On-Time" if x <= SLA_DAYS else "Late"
    )

    # ==================================================
    # 8. MONTH EXTRACTION
    # ==================================================
    df_po["Month"] = df_po["Order_Date"].dt.to_period("M").astype(str)

    # ==================================================
    # 9. MONTHLY SUMMARY
    # ==================================================
    df_monthly = (
        df_po.groupby(["Month", "SLA_Status"])
        .size()
        .reset_index(name="PO_Count")
    )

    # ==================================================
    # 10. METRICS
    # ==================================================
    total_pos = len(df_po)
    on_time_pos = (df_po["SLA_Status"] == "On-Time").sum()

    metrics = {
        "Total_RM_POs": total_pos,
        "On_Time_POs": int(on_time_pos),
        "Late_POs": int(total_pos - on_time_pos),
        "On_Time_Pct": round((on_time_pos / total_pos) * 100, 2) if total_pos else 0
    }

    return metrics, df_monthly
