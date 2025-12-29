import pandas as pd

SLA_DAYS = 10   # keep configurable


def run_component3a(df_po: pd.DataFrame,
                    df_rcpt: pd.DataFrame,
                    df_lines: pd.DataFrame):
    """
    Component 3A — Vendor On-Time Delivery Performance
    Serverless-safe (Vercel compatible)
    Logic preserved exactly from original version
    """

    # ---------------- CLEAN COLUMN NAMES ----------------
    df_po = df_po.copy()
    df_rcpt = df_rcpt.copy()
    df_lines = df_lines.copy()

    for df in [df_po, df_rcpt, df_lines]:
        df.columns = df.columns.str.strip()

    # ---------------- PURCHASE ORDER ----------------
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Pay-to Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po = df_po[[
        "PO_No",
        "Vendor",
        "Order_Date",
        "Last_Receiving_No"
    ]]

    df_po["Order_Date"] = pd.to_datetime(
        df_po["Order_Date"], errors="coerce"
    )

    # ---------------- PURCHASE LINES (COMPLETION CHECK) ----------------
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["Outstanding_Qty"] = pd.to_numeric(
        df_lines["Outstanding_Qty"], errors="coerce"
    ).fillna(0)

    completed_pos = (
        df_lines
        .groupby("PO_No", as_index=False)["Outstanding_Qty"]
        .sum()
    )

    completed_pos = completed_pos[
        completed_pos["Outstanding_Qty"] == 0
    ]

    # ---------------- RECEIPT DATE ----------------
    df_rcpt = df_rcpt.rename(columns={
        "No.": "Receipt_No",
        "Posting Date": "Posting_Date"
    })

    df_rcpt["Posting_Date"] = pd.to_datetime(
        df_rcpt["Posting_Date"], errors="coerce"
    )

    receipt_dates = df_rcpt[[
        "Receipt_No",
        "Posting_Date"
    ]]

    # ---------------- MERGE ALL ----------------
    df = (
        df_po
        .merge(
            completed_pos[["PO_No"]],
            on="PO_No",
            how="inner"
        )
        .merge(
            receipt_dates,
            left_on="Last_Receiving_No",
            right_on="Receipt_No",
            how="left"
        )
    )

    df = df.dropna(
        subset=["Order_Date", "Posting_Date"]
    )

    # ---------------- DELIVERY DAYS ----------------
    df["Delivery_Days"] = (
        df["Posting_Date"] - df["Order_Date"]
    ).dt.days

    df = df[df["Delivery_Days"] >= 0]

    # ---------------- ON-TIME FLAG ----------------
    df["On_Time"] = df["Delivery_Days"] <= SLA_DAYS

    # ---------------- VENDOR KPI ----------------
    vendor_kpi = (
        df.groupby("Vendor")
        .agg(
            Total_POs=("PO_No", "count"),
            On_Time_POs=("On_Time", "sum")
        )
        .reset_index()
    )

    vendor_kpi["On_Time_Pct"] = round(
        (vendor_kpi["On_Time_POs"] /
         vendor_kpi["Total_POs"]) * 100,
        2
    )

    # ---------------- OVERALL METRICS ----------------
    metrics = {
        "Total_Completed_POs": int(len(df)),
        "Overall_On_Time_Pct": round(
            (df["On_Time"].sum() / len(df)) * 100,
            2
        ) if len(df) else 0,
        "Vendors_Below_95": int(
            (vendor_kpi["On_Time_Pct"] < 95).sum()
        )
    }

    return metrics, vendor_kpi
