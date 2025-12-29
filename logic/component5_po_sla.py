import pandas as pd


def run_component5(
    df_po: pd.DataFrame,
    df_rcpt: pd.DataFrame,
    df_lines: pd.DataFrame
):
    """
    Component 5 — Purchase Order SLA (≤90 days vs >90 days)
    Serverless-safe (Vercel compatible)
    Logic preserved exactly
    """

    # ---------------- COPY & CLEAN ----------------
    df_po = df_po.copy()
    df_rcpt = df_rcpt.copy()
    df_lines = df_lines.copy()

    for df in [df_po, df_rcpt, df_lines]:
        df.columns = df.columns.str.strip()

    # ==================================================
    # PURCHASE ORDER (MASTER)
    # ==================================================
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Buy-from Vendor Name": "Vendor",
        "Order Date": "Order_Date"
    })

    df_po = df_po[["PO_No", "Vendor", "Order_Date"]]

    df_po["PO_No"] = df_po["PO_No"].astype(str).str.strip().str.upper()
    df_po["Order_Date"] = pd.to_datetime(
        df_po["Order_Date"], errors="coerce"
    )

    # ==================================================
    # PURCHASE RECEIPT LINES
    # ==================================================
    df_rcpt = df_rcpt.rename(columns={
        "Order No.": "PO_No",
        "Order No": "PO_No",
        "Posting Date": "Posting_Date"
    })

    df_rcpt["PO_No"] = df_rcpt["PO_No"].astype(str).str.strip().str.upper()
    df_rcpt["Posting_Date"] = pd.to_datetime(
        df_rcpt["Posting_Date"], errors="coerce"
    )

    last_receipt = (
        df_rcpt
        .groupby("PO_No", as_index=False)["Posting_Date"]
        .max()
        .rename(columns={"Posting_Date": "Last_Receipt_Date"})
    )

    # ==================================================
    # PURCHASE LINES
    # ==================================================
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "Document No": "PO_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["PO_No"] = df_lines["PO_No"].astype(str).str.strip().str.upper()
    df_lines["Outstanding_Qty"] = pd.to_numeric(
        df_lines["Outstanding_Qty"], errors="coerce"
    ).fillna(0)

    outstanding = (
        df_lines
        .groupby("PO_No", as_index=False)["Outstanding_Qty"]
        .sum()
    )

    # ==================================================
    # MERGE ALL
    # ==================================================
    df = (
        df_po
        .merge(last_receipt, on="PO_No", how="left")
        .merge(outstanding, on="PO_No", how="left")
    )

    df["Outstanding_Qty"] = df["Outstanding_Qty"].fillna(0)

    # ==================================================
    # COMPLETION STATUS
    # ==================================================
    df["PO_Status"] = df["Outstanding_Qty"].apply(
        lambda x: "Completed" if x == 0 else "Open"
    )

    # ==================================================
    # FILTER COMPLETED ONLY
    # ==================================================
    df = df[df["PO_Status"] == "Completed"]
    df = df.dropna(subset=["Order_Date", "Last_Receipt_Date"])

    # ==================================================
    # DAYS TO RECEIVE
    # ==================================================
    df["Days_To_Receive"] = (
        df["Last_Receipt_Date"] - df["Order_Date"]
    ).dt.days

    # ==================================================
    # SLA BUCKET (EXACT LOGIC)
    # ==================================================
    df["SLA_Bucket"] = df["Days_To_Receive"].apply(
        lambda x: "≤ 90 Days" if x <= 90 else "> 90 Days"
    )

    # ==================================================
    # MONTH (FOR TREND CHARTS)
    # ==================================================
    df["Month"] = (
        df["Last_Receipt_Date"]
        .dt.to_period("M")
        .astype(str)
    )

    # ==================================================
    # METRICS
    # ==================================================
    total_pos = int(len(df))
    within_sla = int((df["SLA_Bucket"] == "≤ 90 Days").sum())
    beyond_sla = int((df["SLA_Bucket"] == "> 90 Days").sum())

    metrics = {
        "Total_POs": total_pos,
        "Within_SLA": within_sla,
        "Beyond_SLA": beyond_sla,
        "Within_SLA_Pct": round(
            (within_sla / total_pos) * 100,
            2
        ) if total_pos else 0
    }

    return metrics, df
