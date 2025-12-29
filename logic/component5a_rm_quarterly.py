import pandas as pd

SLA_DAYS = 10   # Change if SLA differs


def run_component5a_rm(
    df_items: pd.DataFrame,
    df_po: pd.DataFrame,
    df_receipts: pd.DataFrame,
    df_lines: pd.DataFrame
):
    """
    Component 5A — RM Purchase Order SLA
    Serverless-safe (Vercel compatible)
    Logic preserved exactly
    """

    # ==================================================
    # COPY & CLEAN
    # ==================================================
    df_items = df_items.copy()
    df_po = df_po.copy()
    df_receipts = df_receipts.copy()
    df_lines = df_lines.copy()

    for df in [df_items, df_po, df_receipts, df_lines]:
        df.columns = df.columns.str.strip()

    # ==================================================
    # 1. GET TRUE RM ITEM CODES
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
    # 2. FIND POs THAT CONTAIN AT LEAST ONE RM ITEM
    # ==================================================
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "No.": "Item_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["PO_No"] = df_lines["PO_No"].astype(str).str.strip()
    df_lines["Item_No"] = df_lines["Item_No"].astype(str).str.strip()
    df_lines["Outstanding_Qty"] = pd.to_numeric(
        df_lines["Outstanding_Qty"], errors="coerce"
    ).fillna(0)

    rm_po_list = (
        df_lines[df_lines["Item_No"].isin(rm_items_set)]["PO_No"]
        .unique()
        .tolist()
    )

    # ==================================================
    # 3. PURCHASE ORDER MASTER (RM ONLY)
    # ==================================================
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Buy-from Vendor Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po["PO_No"] = df_po["PO_No"].astype(str).str.strip()
    df_po["Last_Receiving_No"] = df_po["Last_Receiving_No"].astype(str).str.strip()
    df_po["Order_Date"] = pd.to_datetime(
        df_po["Order_Date"], errors="coerce"
    )

    # 🔴 FILTER TO RM POs ONLY
    df_po = df_po[df_po["PO_No"].isin(rm_po_list)]

    # ==================================================
    # 4. COMPLETION CHECK (Outstanding Qty == 0)
    # ==================================================
    po_completion = (
        df_lines
        .groupby("PO_No", as_index=False)["Outstanding_Qty"]
        .sum()
    )

    completed_pos = po_completion[
        po_completion["Outstanding_Qty"] == 0
    ]["PO_No"]

    df_po = df_po[df_po["PO_No"].isin(completed_pos)]

    # ==================================================
    # 5. RECEIPT DATE
    # ==================================================
    df_receipts = df_receipts.rename(columns={
        "No.": "Receipt_No",
        "Posting Date": "Posting_Date"
    })

    df_receipts["Receipt_No"] = (
        df_receipts["Receipt_No"]
        .astype(str)
        .str.strip()
    )

    df_receipts["Posting_Date"] = pd.to_datetime(
        df_receipts["Posting_Date"], errors="coerce"
    )

    receipt_map = dict(
        zip(df_receipts["Receipt_No"], df_receipts["Posting_Date"])
    )

    df_po["Receipt_Date"] = df_po["Last_Receiving_No"].map(receipt_map)

    # ==================================================
    # 6. DELIVERY DAYS & SLA
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
    # 7. MONTH EXTRACTION
    # ==================================================
    df_po["Month"] = (
        df_po["Order_Date"]
        .dt.to_period("M")
        .astype(str)
    )

    # ==================================================
    # 8. MONTHLY SUMMARY
    # ==================================================
    df_monthly = (
        df_po
        .groupby(["Month", "SLA_Status"])
        .size()
        .reset_index(name="PO_Count")
    )

    # ==================================================
    # 9. METRICS
    # ==================================================
    total_pos = int(len(df_po))
    on_time_pos = int((df_po["SLA_Status"] == "On-Time").sum())

    metrics = {
        "Total_RM_POs": total_pos,
        "On_Time_POs": on_time_pos,
        "Late_POs": int(total_pos - on_time_pos),
        "On_Time_Pct": round(
            (on_time_pos / total_pos) * 100,
            2
        ) if total_pos else 0
    }

    return metrics, df_monthly
