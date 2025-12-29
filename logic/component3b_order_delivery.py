import pandas as pd

PO_FILE = "data/Purchase order - use order date.xlsx"
RECEIPT_FILE = "data/Posted Purchase Receipts - Posting date against document no.xlsx"
LINES_FILE = "data/Purchase Lines -.xlsx"

SLA_DAYS = 15   # same as Excel (≤15 / >15)


def run_component3b():

    # ---------------- LOAD FILES ----------------
    df_po = pd.read_excel(PO_FILE)
    df_rcpt = pd.read_excel(RECEIPT_FILE)
    df_lines = pd.read_excel(LINES_FILE)

    for df in [df_po, df_rcpt, df_lines]:
        df.columns = df.columns.str.strip()

    # ---------------- PURCHASE ORDERS ----------------
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Pay-to Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po = df_po[["PO_No", "Vendor", "Order_Date", "Last_Receiving_No"]]

    df_po["PO_No"] = df_po["PO_No"].astype(str).str.strip().str.upper()
    df_po["Last_Receiving_No"] = df_po["Last_Receiving_No"].astype(str).str.strip().str.upper()
    df_po["Vendor"] = df_po["Vendor"].astype(str).str.strip()
    df_po["Order_Date"] = pd.to_datetime(df_po["Order_Date"], errors="coerce")

    # ---------------- RECEIPTS ----------------
    df_rcpt = df_rcpt.rename(columns={
        "No.": "Last_Receiving_No",
        "Posting Date": "Posting_Date"
    })

    df_rcpt["Last_Receiving_No"] = (
        df_rcpt["Last_Receiving_No"].astype(str).str.strip().str.upper()
    )
    df_rcpt["Posting_Date"] = pd.to_datetime(df_rcpt["Posting_Date"], errors="coerce")

    receipt_map = df_rcpt.set_index("Last_Receiving_No")["Posting_Date"].to_dict()

    # ---------------- PURCHASE LINES (FOR COMPLETION INFO ONLY) ----------------
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["PO_No"] = df_lines["PO_No"].astype(str).str.strip().str.upper()

    po_completion = df_lines.groupby("PO_No")["Outstanding_Qty"].sum()

    # ---------------- MERGE (MATCH EXCEL All_POs_Detail) ----------------
    df = df_po.copy()
    df["Last_Receipt_Date"] = df["Last_Receiving_No"].map(receipt_map)
    df["Outstanding_Qty"] = df["PO_No"].map(po_completion).fillna(0)

    # ---------------- DAYS DIFFERENCE ----------------
    df["Days_Difference"] = (
        df["Last_Receipt_Date"] - df["Order_Date"]
    ).dt.days

    # ---------------- DELIVERY STATUS (EXACT EXCEL LOGIC) ----------------
    df["Delivery_Status"] = "No Receipt"

    df.loc[df["Days_Difference"] > SLA_DAYS, "Delivery_Status"] = ">15 days"
    df.loc[
        (df["Days_Difference"] >= 0) & (df["Days_Difference"] <= SLA_DAYS),
        "Delivery_Status"
    ] = "≤15 days"

    # ---------------- MONTH (FIXES KeyError: 'Month') ----------------
    df["Month"] = df["Last_Receipt_Date"].dt.to_period("M").astype(str)

    # ---------------- METRICS (DASHBOARD SAFE) ----------------
    le_15 = (df["Delivery_Status"] == "≤15 days").sum()
    gt_15 = (df["Delivery_Status"] == ">15 days").sum()

    total_considered = le_15 + gt_15

    metrics = {
        # Excel-aligned
        "≤15_days": int(le_15),
        ">15_days": int(gt_15),

        # Flask dashboard expects these
        "On_Time": int(le_15),
        "Delayed": int(gt_15),

        "On_Time_Pct": round((le_15 / total_considered) * 100, 2)
        if total_considered else 0
    }

    return metrics, df
